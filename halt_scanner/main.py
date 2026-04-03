"""
main.py – נקודת כניסה ראשית ל-HaltScanner Pro
הפעל: python main.py
אפשרויות:
  python main.py          – מריץ ברקע כל N דקות
  python main.py --once   – סריקה אחת ויציאה
  python main.py --test   – בדיקת חיבורים ושליחת התראת דמה
  python main.py --demo TEVA  – סימולציה עם חברה ספציפית
  python main.py --summary    – שלח סיכום יומי עכשיו
"""
import sys
import time
import yaml
import schedule
import logging
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"
LOG_DIR = Path(__file__).parent / "logs"

# ── הגדרת logging ────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            LOG_DIR / f"halt_scanner_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("HaltScanner")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    required = [
        ("anthropic", "api_key"),
        ("telegram", "bot_token"),
        ("telegram", "chat_id"),
    ]
    missing = []
    for section, key in required:
        val = cfg.get(section, {}).get(key, "")
        if not val or val.startswith("YOUR_"):
            missing.append(f"{section}.{key}")

    if missing:
        logger.warning(f"config.yaml: חסרים: {', '.join(missing)}")
        logger.info("הרץ: python setup_scanner.py להגדרה אוטומטית")

    return cfg


def is_trading_hours(config: dict) -> bool:
    """בודק אם נמצאים בשעות מסחר (א-ה, 09:45-17:30)."""
    if not config.get("scanning", {}).get("trading_hours_only", True):
        return True

    now = datetime.now()
    day = now.isoweekday()  # 1=Mon ... 7=Sun
    if day == 6:  # Saturday
        return False

    hour_min = now.hour * 100 + now.minute
    return 945 <= hour_min <= 1730


def run_scan(scanner, config: dict):
    """מפעיל סריקה אחת עם retry."""
    if not is_trading_hours(config):
        return

    retry_count = config.get("scanning", {}).get("retry_on_error", 3)
    for attempt in range(retry_count):
        try:
            alerts = scanner.scan()
            if alerts > 0:
                logger.info(f"נשלחו {alerts} התראות")
            return
        except Exception as e:
            logger.error(f"שגיאה בסריקה (ניסיון {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(10 * (attempt + 1))


def run_daily_summary(scanner, config: dict):
    """שולח סיכום יומי."""
    try:
        scanner.send_daily_summary()
    except Exception as e:
        logger.error(f"שגיאה בסיכום יומי: {e}")


def cmd_test(config: dict):
    """בדיקת חיבורים."""
    from alerts import telegram_alert
    from connectors import maya_rss, yahoo_finance

    print("\n" + "=" * 50)
    print("  HaltScanner Pro – בדיקת מערכת")
    print("=" * 50 + "\n")

    results = {}

    # 1. Telegram
    print("1. בדיקת Telegram...")
    tg = config.get("telegram", {})
    if tg.get("bot_token", "").startswith("YOUR_"):
        print("   * טוקן לא הוגדר - דלג")
        results["telegram"] = False
    else:
        ok = telegram_alert.send_test_alert(tg["bot_token"], tg["chat_id"])
        print(f"   {'OK' if ok else 'נכשל'}")
        results["telegram"] = ok

    # 2. RSS
    print("2. בדיקת RSS (Bizportal)...")
    try:
        entries = maya_rss.fetch_announcements()
        halts = [e for e in entries if maya_rss.is_halt_announcement(e)]
        print(f"   OK - {len(entries)} הודעות, {len(halts)} הפסקות")
        results["rss"] = True
    except Exception as e:
        print(f"   נכשל: {e}")
        results["rss"] = False

    # 3. Yahoo Finance
    print("3. בדיקת Yahoo Finance...")
    data = yahoo_finance.get_price_data("TEVA")
    if data:
        print(f"   OK - TEVA: {data['change_pct']:+.2f}%")
        results["yahoo"] = True
    else:
        data = yahoo_finance.get_price_data("LUMI.TA")
        if data:
            print(f"   OK - LUMI.TA: {data['change_pct']:+.2f}%")
            results["yahoo"] = True
        else:
            print("   לא ניתן לשלוף מחיר (ייתכן לאחר שעות מסחר)")
            results["yahoo"] = None

    # 4. Anthropic
    print("4. בדיקת Anthropic API...")
    api_key = config.get("anthropic", {}).get("api_key", "")
    if api_key.startswith("YOUR_"):
        print("   * API Key לא הוגדר - דלג")
        results["anthropic"] = False
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            model = config.get("anthropic", {}).get("model", "claude-sonnet-4-20250514")
            client.messages.create(
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": "בדיקה. אמור: OK"}],
            )
            print(f"   OK - מודל {model} פעיל")
            results["anthropic"] = True
        except Exception as e:
            print(f"   נכשל: {e}")
            results["anthropic"] = False

    # 5. Email
    print("5. בדיקת Email...")
    em = config.get("email", {})
    if not em.get("enabled") or em.get("password", "").startswith("YOUR_"):
        print("   * אימייל לא הוגדר - דלג")
        results["email"] = None
    else:
        from alerts import email_alert
        try:
            ok = email_alert.send_test(
                em["smtp_server"], em["smtp_port"],
                em["username"], em["password"],
                em["recipients"],
            )
            print(f"   {'OK' if ok else 'נכשל'}")
            results["email"] = ok
        except Exception as e:
            print(f"   נכשל: {e}")
            results["email"] = False

    # סיכום
    print("\n" + "=" * 50)
    passed = sum(1 for v in results.values() if v is True)
    total = len(results)
    print(f"  תוצאה: {passed}/{total} רכיבים פעילים")

    if all(v is not False for v in results.values()):
        print("  המערכת מוכנה להפעלה!")
    else:
        failed = [k for k, v in results.items() if v is False]
        print(f"  צריך לתקן: {', '.join(failed)}")
        print("  הרץ: python setup_scanner.py")

    print("=" * 50 + "\n")


def cmd_demo(config: dict, company: str):
    """סימולציה עם חברה ספציפית."""
    from scanner import HaltScanner

    print(f"\n=== דמו: {company} ===")
    scanner = HaltScanner(config)

    fake_entry = {
        "id": f"demo_{company}_{time.time()}",
        "title": f"{company} - הפסקת מסחר 45 דקות בעקבות הודעה מהותית",
        "summary": "עסקה מהותית לרכישת חברה בת. ההודעה מהותית לפי תקנות ניירות ערך.",
        "link": "https://maya.tase.co.il/",
        "published": None,
        "source": "demo",
    }

    scanner._process_halt(fake_entry, min_change=0.0)
    print("=== דמו הסתיים ===")


def main():
    config = load_config()
    args = sys.argv[1:]

    if "--test" in args:
        cmd_test(config)
        return

    if "--demo" in args:
        idx = args.index("--demo")
        company = args[idx + 1] if idx + 1 < len(args) else "טבע"
        cmd_demo(config, company)
        return

    if "--summary" in args:
        from scanner import HaltScanner
        scanner = HaltScanner(config)
        scanner.send_daily_summary()
        return

    from scanner import HaltScanner
    scanner = HaltScanner(config)

    if "--once" in args:
        scanner.scan()
        return

    # מצב רגיל – לולאה תמידית
    interval = config.get("scanning", {}).get("interval_minutes", 5)
    logger.info(f"HaltScanner Pro מתחיל – סריקה כל {interval} דקות")
    logger.info("שעות מסחר: א-ה 09:45-17:30 | Ctrl+C לעצירה")

    # סריקה ראשונה
    run_scan(scanner, config)

    # תזמון
    schedule.every(interval).minutes.do(run_scan, scanner, config)

    # סיכום יומי
    alerts_cfg = config.get("alerts", {})
    if alerts_cfg.get("daily_summary", False):
        summary_time = alerts_cfg.get("daily_summary_time", "17:45")
        schedule.every().day.at(summary_time).do(
            run_daily_summary, scanner, config
        )
        logger.info(f"סיכום יומי מתוזמן ל-{summary_time}")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
