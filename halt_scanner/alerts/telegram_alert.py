"""
telegram_alert.py – שליחת התראות לטלגרם
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime


def send_alert(
    bot_token: str,
    chat_id: str,
    halt_info: Dict,
    suppliers: List[Dict],
    analysis: Optional[str] = None,
) -> bool:
    """
    שולח התראת הפסקת מסחר + ספקים לטלגרם.
    מחזיר True אם נשלח בהצלחה.
    """
    message = _build_message(halt_info, suppliers, analysis)
    return _send_message(bot_token, chat_id, message)


def send_simple_message(bot_token: str, chat_id: str, text: str) -> bool:
    """שליחת הודעת טקסט פשוטה."""
    return _send_message(bot_token, chat_id, text)


def send_test_alert(bot_token: str, chat_id: str) -> bool:
    """שולח התראת בדיקה לוידוא שהחיבור עובד."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = (
        f"✅ *HaltScanner – בדיקת מערכת*\n\n"
        f"המערכת פעילה ומחוברת!\n"
        f"זמן: {now}\n\n"
        f"_דוגמה להתראה:_\n"
        f"🚨 *הפסקת מסחר: TEVA*\n"
        f"📄 סיבה: עסקה מהותית\n\n"
        f"*ספקים שלא זזו:*\n"
        f"• ABC Chemicals (ABCC.TA): +1.2% לעומת TEVA +8.5%\n"
        f"  → שמא הזדמנות לבדיקה?\n\n"
        f"✅ מערכת HaltScanner פעילה"
    )
    return _send_message(bot_token, chat_id, message)


# ── בניית הודעה ────────────────────────────────────────────

def _build_message(
    halt_info: Dict,
    suppliers: List[Dict],
    analysis: Optional[str],
) -> str:
    company = halt_info.get("company", "לא ידוע")
    main_ticker = halt_info.get("ticker", "?")
    main_change = halt_info.get("change_pct")
    announcement = halt_info.get("announcement", "")
    link = halt_info.get("link", "")
    time_str = datetime.now().strftime("%H:%M")

    # כותרת
    change_str = f"+{main_change:.1f}%" if main_change and main_change > 0 else "N/A"
    lines = [
        f"🚨 *הפסקת מסחר: {company}* ({main_ticker})",
        f"⏰ {time_str} | מניה ראשית: {change_str}",
        "",
    ]

    # הודעה
    if announcement:
        short_ann = announcement[:200] + "..." if len(announcement) > 200 else announcement
        lines.append(f"📄 {short_ann}")
        lines.append("")

    # ספקים
    if suppliers:
        lines.append("*ספקים/שותפים שנבדקו:*")
        for s in suppliers:
            name = s.get("name", "?")
            ticker = s.get("ticker") or "לא ידוע"
            s_change = s.get("change_pct")
            reason = s.get("reason", "")

            if s_change is not None:
                s_change_str = f"+{s_change:.1f}%" if s_change >= 0 else f"{s_change:.1f}%"
                arrow = "⚠️" if (main_change and s_change < main_change * 0.6) else "ℹ️"
                lines.append(f"{arrow} *{name}* ({ticker}): {s_change_str}")
            else:
                lines.append(f"❓ *{name}* ({ticker}): מחיר לא זמין")

            if reason:
                lines.append(f"   _{reason}_")

        lines.append("")

    # ניתוח AI
    if analysis:
        lines.append("🤖 *ניתוח:*")
        # קיצור הניתוח אם ארוך מדי
        short_analysis = analysis[:400] + "..." if len(analysis) > 400 else analysis
        lines.append(short_analysis)
        lines.append("")

    # קישור
    if link:
        lines.append(f"🔗 [לקריאת ההודעה המלאה]({link})")

    lines.append("\n_HaltScanner – שמירה על שקט נפשי_ 🧘")

    return "\n".join(lines)


def _send_message(bot_token: str, chat_id: str, text: str) -> bool:
    """שליחה בפועל ל-Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.ok:
            print(f"[Telegram] הודעה נשלחה בהצלחה")
            return True
        else:
            print(f"[Telegram] שגיאה: {response.status_code} – {response.text[:200]}")
            return False
    except requests.RequestException as e:
        print(f"[Telegram] שגיאת רשת: {e}")
        return False
