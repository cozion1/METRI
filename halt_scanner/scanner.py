"""
scanner.py – לוגיקת הסריקה הראשית
מחבר בין כל הרכיבים: RSS → AI → Yahoo Finance → התראה
כולל: caching, rate limiting, daily summary, safety checks
"""
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from connectors import maya_rss, yahoo_finance, pdf_parser
import analyzer
from alerts import telegram_alert, email_alert

logger = logging.getLogger("HaltScanner")

DATA_DIR = Path(__file__).parent / "data"
PROCESSED_FILE = DATA_DIR / "processed_halts.json"
DAILY_LOG_FILE = DATA_DIR / "daily_log.json"
BUDGET_FILE = DATA_DIR / "budget_tracker.json"


class HaltScanner:
    def __init__(self, config: Dict):
        self.config = config
        model = config.get("anthropic", {}).get("model", "claude-sonnet-4-20250514")
        self.claude = analyzer.create_client(
            config["anthropic"]["api_key"]
        )
        self.model = model
        self.processed_ids: Set[str] = self._load_processed()
        self._api_calls_this_hour = 0
        self._hour_start = datetime.now()
        self._last_alert_time = None
        self._daily_alerts: List[Dict] = self._load_daily_log()

    # ── סריקה ראשית ──────────────────────────────────────

    def scan(self) -> int:
        """מבצע סריקה אחת. מחזיר מספר ההתראות."""
        logger.info(f"מתחיל סריקה...")

        alerts_sent = 0
        cfg_scan = self.config.get("scanning", {})
        cfg_alerts = self.config.get("alerts", {})
        min_change = cfg_alerts.get("min_price_change_pct", 1.0)
        lookback_hours = cfg_scan.get("lookback_hours", 2)

        # 1. שליפת הודעות
        rss_urls = self.config.get("maya", {}).get("rss_urls", maya_rss.RSS_URLS)
        entries = maya_rss.fetch_announcements(rss_urls)
        entries = maya_rss.filter_recent(entries, hours=lookback_hours)
        logger.info(f"נמצאו {len(entries)} הודעות")

        # 2. סינון הפסקות מסחר
        halts = [
            e for e in entries
            if maya_rss.is_halt_announcement(e) and e["id"] not in self.processed_ids
        ]
        logger.info(f"מתוכן {len(halts)} הפסקות חדשות")

        for halt in halts:
            try:
                if not self._check_rate_limit():
                    logger.warning("חריגה ממגבלת API - עוצר סריקה")
                    break

                if not self._check_cooldown():
                    logger.debug("cooldown פעיל - ממתין")
                    continue

                sent = self._process_halt(halt, min_change)
                if sent:
                    alerts_sent += 1
                    self._last_alert_time = datetime.now()
                self.processed_ids.add(halt["id"])
            except Exception as e:
                logger.error(f"שגיאה בעיבוד הפסקה: {e}")

        self._save_processed()
        logger.info(f"סריקה הסתיימה – {alerts_sent} התראות נשלחו")
        return alerts_sent

    # ── עיבוד הפסקה בודדת ────────────────────────────────

    def _process_halt(self, entry: Dict, min_change: float) -> bool:
        company_name = maya_rss.extract_company_name(entry)
        if not company_name:
            return False

        logger.info(f"מעבד הפסקה: {company_name}")

        # מחיר מניה ראשית
        main_ticker = yahoo_finance.resolve_ticker(company_name)
        main_data = None
        if main_ticker:
            main_data = yahoo_finance.get_price_data(main_ticker)

        main_change = main_data["change_pct"] if main_data else None

        if main_change is not None and main_change < min_change:
            logger.info(f"{company_name} – שינוי {main_change:.1f}% < סף {min_change}%, מדלג")
            return False

        # AI: זיהוי ספקים
        prospectus_text = self._fetch_prospectus_text(entry, company_name)
        announcement_text = entry.get("title", "") + "\n" + entry.get("summary", "")

        self._track_api_call()
        suppliers_raw = analyzer.extract_suppliers_from_text(
            self.claude,
            company_name,
            announcement_text,
            prospectus_text,
            model=self.model,
        )

        if not suppliers_raw:
            logger.info(f"{company_name} – לא נמצאו ספקים נסחרים")
            return False

        # סינון לפי confidence
        min_conf = self.config.get("safety", {}).get("min_confidence", "medium")
        if min_conf == "high":
            suppliers_raw = [s for s in suppliers_raw if s.get("confidence") == "high"]

        # בדיקת מחירי ספקים
        cfg_scan = self.config.get("scanning", {})
        max_suppliers = cfg_scan.get("max_suppliers_to_check", 5)
        lag_threshold = cfg_scan.get("price_lag_threshold", 0.6)

        suppliers_with_prices = []
        opportunities = []

        for s in suppliers_raw[:max_suppliers]:
            ticker = s.get("ticker")
            if not ticker or ticker == "null":
                ticker = yahoo_finance.resolve_ticker(s.get("name", ""))
                if ticker:
                    s["ticker"] = ticker

            price_data = None
            if s.get("ticker"):
                price_data = yahoo_finance.get_price_data(s["ticker"])

            s["change_pct"] = price_data["change_pct"] if price_data else None
            suppliers_with_prices.append(s)

            if (main_change is not None
                    and s["change_pct"] is not None
                    and s["change_pct"] < main_change * lag_threshold):
                opportunities.append(s)

        if not opportunities and main_change is not None:
            logger.info(f"{company_name} – כל הספקים זזו מספיק, אין הזדמנות")
            return False

        # ניתוח AI
        analysis = None
        if opportunities or suppliers_with_prices:
            self._track_api_call()
            analysis = analyzer.analyze_halt_opportunity(
                self.claude,
                company_name,
                announcement_text,
                main_change or 0,
                suppliers_with_prices,
                model=self.model,
            )

        halt_info = {
            "company": company_name,
            "ticker": main_ticker or "?",
            "change_pct": main_change,
            "announcement": announcement_text,
            "link": entry.get("link", ""),
            "time": datetime.now().isoformat(),
        }

        # שמירה ללוג יומי
        self._log_daily(halt_info, suppliers_with_prices, opportunities, analysis)

        return self._send_alerts(halt_info, suppliers_with_prices, analysis)

    # ── סיכום יומי ────────────────────────────────────────

    def send_daily_summary(self):
        """שולח סיכום יומי של כל ההתראות שנשלחו."""
        daily = self._load_daily_log()
        today = datetime.now().strftime("%Y-%m-%d")
        today_alerts = [a for a in daily if a.get("date", "").startswith(today)]

        tg = self.config.get("telegram", {})
        em = self.config.get("email", {})

        if not today_alerts:
            summary = (
                f"*סיכום יומי – {today}*\n\n"
                f"לא זוהו הזדמנויות היום.\n"
                f"המערכת פעילה ומנטרת.\n\n"
                f"_HaltScanner Pro_"
            )
        else:
            lines = [f"*סיכום יומי – {today}*\n"]
            lines.append(f"זוהו {len(today_alerts)} הפסקות עם הזדמנויות:\n")

            for i, alert in enumerate(today_alerts, 1):
                company = alert.get("company", "?")
                change = alert.get("main_change")
                opps = alert.get("opportunities", 0)
                change_str = f"+{change:.1f}%" if change else "N/A"
                lines.append(f"{i}. *{company}* ({change_str}) – {opps} ספקים מעניינים")

            budget = self._get_budget_today()
            lines.append(f"\nעלות API היום: ~${budget:.2f}")
            lines.append(f"\n_HaltScanner Pro – שמירה על שקט נפשי_")
            summary = "\n".join(lines)

        if self.config.get("alerts", {}).get("enable_telegram", True):
            telegram_alert.send_simple_message(
                tg["bot_token"], tg["chat_id"], summary
            )

        if (self.config.get("alerts", {}).get("enable_email", False)
                and em.get("enabled", False)):
            email_alert.send_summary(
                em["smtp_server"], em["smtp_port"],
                em["username"], em["password"],
                em["recipients"], summary
            )

        logger.info("סיכום יומי נשלח")

    # ── שליפת תשקיף ──────────────────────────────────────

    def _fetch_prospectus_text(self, entry: Dict, company_name: str) -> Optional[str]:
        pdf_url = maya_rss.extract_prospectus_url(entry)
        if pdf_url:
            text = pdf_parser.extract_text_from_url(pdf_url)
            if text:
                return pdf_parser.extract_supplier_section(text)

        pdf_url = pdf_parser.get_maya_prospectus_url(company_name)
        if pdf_url:
            text = pdf_parser.extract_text_from_url(pdf_url)
            if text:
                return pdf_parser.extract_supplier_section(text)

        return None

    # ── שליחת התראות ──────────────────────────────────────

    def _send_alerts(
        self, halt_info: Dict, suppliers: List[Dict], analysis: Optional[str],
    ) -> bool:
        cfg = self.config.get("alerts", {})
        tg_cfg = self.config.get("telegram", {})
        em_cfg = self.config.get("email", {})
        sent = False

        if cfg.get("enable_telegram", True):
            ok = telegram_alert.send_alert(
                bot_token=tg_cfg["bot_token"],
                chat_id=tg_cfg["chat_id"],
                halt_info=halt_info,
                suppliers=suppliers,
                analysis=analysis,
            )
            if ok:
                sent = True

        if cfg.get("enable_email", False) and em_cfg.get("enabled", False):
            email_alert.send_alert(
                smtp_server=em_cfg["smtp_server"],
                smtp_port=em_cfg["smtp_port"],
                username=em_cfg["username"],
                password=em_cfg["password"],
                recipients=em_cfg["recipients"],
                halt_info=halt_info,
                suppliers=suppliers,
                analysis=analysis,
            )
            sent = True

        return sent

    # ── בטיחות: rate limiting ─────────────────────────────

    def _check_rate_limit(self) -> bool:
        now = datetime.now()
        if (now - self._hour_start).total_seconds() > 3600:
            self._api_calls_this_hour = 0
            self._hour_start = now

        max_calls = self.config.get("safety", {}).get("max_api_calls_per_hour", 20)
        return self._api_calls_this_hour < max_calls

    def _check_cooldown(self) -> bool:
        if self._last_alert_time is None:
            return True
        cooldown = self.config.get("safety", {}).get("cooldown_minutes", 2)
        elapsed = (datetime.now() - self._last_alert_time).total_seconds()
        return elapsed >= cooldown * 60

    def _track_api_call(self):
        self._api_calls_this_hour += 1
        self._track_budget()

    # ── בטיחות: budget tracking ───────────────────────────

    def _track_budget(self):
        today = datetime.now().strftime("%Y-%m-%d")
        budget_data = self._load_budget()
        if budget_data.get("date") != today:
            budget_data = {"date": today, "calls": 0, "est_cost": 0.0}

        budget_data["calls"] += 1
        # הערכה: ~$0.01 per Sonnet call average
        budget_data["est_cost"] += 0.01

        max_budget = self.config.get("anthropic", {}).get("max_daily_budget_usd", 5.0)
        if budget_data["est_cost"] > max_budget:
            logger.warning(f"חריגה מתקציב יומי! ${budget_data['est_cost']:.2f} > ${max_budget}")

        try:
            DATA_DIR.mkdir(exist_ok=True)
            BUDGET_FILE.write_text(
                json.dumps(budget_data, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    def _load_budget(self) -> Dict:
        try:
            if BUDGET_FILE.exists():
                return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"date": "", "calls": 0, "est_cost": 0.0}

    def _get_budget_today(self) -> float:
        data = self._load_budget()
        today = datetime.now().strftime("%Y-%m-%d")
        return data.get("est_cost", 0.0) if data.get("date") == today else 0.0

    # ── לוג יומי ──────────────────────────────────────────

    def _log_daily(self, halt_info, suppliers, opportunities, analysis):
        entry = {
            "date": datetime.now().isoformat(),
            "company": halt_info.get("company"),
            "ticker": halt_info.get("ticker"),
            "main_change": halt_info.get("change_pct"),
            "suppliers_checked": len(suppliers),
            "opportunities": len(opportunities),
            "analysis_snippet": (analysis or "")[:100],
        }
        self._daily_alerts.append(entry)
        self._save_daily_log()

    def _load_daily_log(self) -> List[Dict]:
        try:
            if DAILY_LOG_FILE.exists():
                data = json.loads(DAILY_LOG_FILE.read_text(encoding="utf-8"))
                # שמור רק 7 ימים אחרונים
                cutoff = (datetime.now() - timedelta(days=7)).isoformat()
                return [d for d in data if d.get("date", "") > cutoff]
        except Exception:
            pass
        return []

    def _save_daily_log(self):
        try:
            DATA_DIR.mkdir(exist_ok=True)
            DAILY_LOG_FILE.write_text(
                json.dumps(self._daily_alerts, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"שגיאה בשמירת לוג יומי: {e}")

    # ── שמירת מצב ─────────────────────────────────────────

    def _load_processed(self) -> Set[str]:
        DATA_DIR.mkdir(exist_ok=True)
        if PROCESSED_FILE.exists():
            try:
                data = json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))
                return set(data[-500:]) if isinstance(data, list) else set()
            except Exception:
                pass
        return set()

    def _save_processed(self):
        try:
            DATA_DIR.mkdir(exist_ok=True)
            ids_list = list(self.processed_ids)[-500:]
            PROCESSED_FILE.write_text(
                json.dumps(ids_list, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"שגיאה בשמירת מצב: {e}")
