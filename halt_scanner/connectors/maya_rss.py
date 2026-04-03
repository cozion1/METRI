"""
maya_rss.py – קונקטור לאתרי בורסת ת"א
סורק RSS של Bizportal ו-Maya לזיהוי הפסקות מסחר
"""
import re
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dateutil import parser as dateutil_parser

# ── URLs לסריקה ───────────────────────────────────────────
RSS_URLS = [
    "https://www.bizportal.co.il/rss/bursamessages",
]

MAYA_API_URL = "https://maya.tase.co.il/api/news"

HALT_KEYWORDS = [
    "הפסקת מסחר",
    "עצירת מסחר",
    "45 דקות",
    "halt",
    "trading suspension",
]

MATERIAL_KEYWORDS = [
    "הודעה מהותית",
    "עסקה מהותית",
    "דוח כספי",
    "הנפקה",
    "רכישה",
    "מיזוג",
    "פיצול",
    "שותפות",
    "חוזה",
    "הסכם",
]


def fetch_announcements(rss_urls: List[str] = None) -> List[Dict]:
    """שולף הודעות מ-RSS ומחזיר רשימה מנורמלת."""
    if rss_urls is None:
        rss_urls = RSS_URLS

    entries = []
    headers = {
        "User-Agent": "HaltScanner/1.0 (trading-halt-monitor)"
    }

    for url in rss_urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                published = _parse_date(entry.get("published", ""))
                entries.append({
                    "id": entry.get("id", entry.get("link", "")),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": published,
                    "source": url,
                })
        except Exception as e:
            print(f"[Maya RSS] שגיאה בשליפה מ-{url}: {e}")

    return entries


def is_halt_announcement(entry: Dict) -> bool:
    """בודק אם ההודעה מציינת הפסקת מסחר."""
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw.lower() in text for kw in HALT_KEYWORDS)


def is_material_announcement(entry: Dict) -> bool:
    """בודק אם ההודעה מהותית (רלוונטית להזדמנות)."""
    text = entry.get("title", "") + " " + entry.get("summary", "")
    return any(kw in text for kw in MATERIAL_KEYWORDS)


def extract_company_name(entry: Dict) -> str:
    """מחלץ שם חברה מכותרת ההודעה."""
    title = entry.get("title", "").strip()

    # דפוסים נפוצים בכותרות Maya
    patterns = [
        r'^(.+?)\s*[-–:]\s*הפסקת מסחר',
        r'^(.+?)\s*[-–:]\s*עצירת',
        r'^(.+?)\s+מפרסמת\s',
        r'^(.+?)\s+הודיעה\s',
        r'^(.+?)\s+מכריזה\s',
        r'^(.+?)\s*:',
    ]

    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            name = match.group(1).strip()
            # נקה מספרים בסוגריים
            name = re.sub(r'\s*\(\d+\)\s*$', '', name)
            return name

    # fallback: שתי המילים הראשונות
    words = title.split()
    return " ".join(words[:3]) if len(words) >= 3 else title


def extract_prospectus_url(entry: Dict) -> Optional[str]:
    """מנסה לחלץ קישור לתשקיף/דוח PDF מההודעה."""
    link = entry.get("link", "")
    summary = entry.get("summary", "")

    # חיפוש קישורי Maya לדוחות
    pdf_patterns = [
        r'https?://[^\s"<>]*\.pdf',
        r'https://maya\.tase\.co\.il/[^\s"<>]*report[^\s"<>]*',
        r'https://maya\.tase\.co\.il/[^\s"<>]*document[^\s"<>]*',
    ]

    for text in [summary, link]:
        for pattern in pdf_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

    return None


def filter_recent(entries: List[Dict], hours: int = 2) -> List[Dict]:
    """מסנן הודעות משעות האחרונות בלבד."""
    cutoff = datetime.now() - timedelta(hours=hours)
    recent = []
    for entry in entries:
        published = entry.get("published")
        if published is None or published >= cutoff:
            recent.append(entry)
    return recent


def _parse_date(date_str: str) -> Optional[datetime]:
    """ממיר מחרוזת תאריך ל-datetime."""
    if not date_str:
        return None
    try:
        return dateutil_parser.parse(date_str, ignoretz=True)
    except Exception:
        return None
