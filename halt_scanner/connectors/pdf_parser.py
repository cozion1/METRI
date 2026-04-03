"""
pdf_parser.py – חילוץ טקסט מתשקיפים ודוחות PDF
"""
import re
import io
import requests
import pdfplumber
from typing import Optional, Dict, List

SUPPLIER_KEYWORDS = [
    "ספקים עיקריים",
    "ספק עיקרי",
    "ספקים",
    "שותפים אסטרטגיים",
    "שותפים עסקיים",
    "לקוחות עיקריים",
    "יצרנים",
    "קבלני משנה",
    "ספקי חומרי גלם",
    "תלות בספקים",
    "suppliers",
    "key suppliers",
    "strategic partners",
]


def extract_text_from_url(url: str, max_pages: int = 30) -> Optional[str]:
    """
    מוריד PDF מ-URL ומחלץ ממנו טקסט.
    מוגבל ל-max_pages עמודים ראשונים כדי לחסוך בזמן.
    """
    try:
        headers = {"User-Agent": "HaltScanner/1.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        pdf_bytes = io.BytesIO(response.content)
        return extract_text_from_bytes(pdf_bytes, max_pages)

    except requests.RequestException as e:
        print(f"[PDF Parser] שגיאת הורדה: {e}")
        return None
    except Exception as e:
        print(f"[PDF Parser] שגיאה כללית: {e}")
        return None


def extract_text_from_file(file_path: str, max_pages: int = 30) -> Optional[str]:
    """מחלץ טקסט מקובץ PDF מקומי."""
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = pdf.pages[:max_pages]
            text = "\n".join(
                page.extract_text() or "" for page in pages
            )
        return text if text.strip() else None
    except Exception as e:
        print(f"[PDF Parser] שגיאה בקריאת קובץ: {e}")
        return None


def extract_text_from_bytes(pdf_bytes: io.BytesIO, max_pages: int = 30) -> Optional[str]:
    """מחלץ טקסט מ-BytesIO של PDF."""
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            pages = pdf.pages[:max_pages]
            text = "\n".join(
                page.extract_text() or "" for page in pages
            )
        return text if text.strip() else None
    except Exception as e:
        print(f"[PDF Parser] שגיאת pdfplumber: {e}")
        return None


def extract_supplier_section(full_text: str) -> Optional[str]:
    """
    מחלץ את הקטע הרלוונטי לספקים מתוך הטקסט המלא.
    מחזיר עד 3,000 תווים סביב הקטע הרלוונטי.
    """
    if not full_text:
        return None

    best_pos = -1
    for keyword in SUPPLIER_KEYWORDS:
        pos = full_text.lower().find(keyword.lower())
        if pos != -1:
            if best_pos == -1 or pos < best_pos:
                best_pos = pos

    if best_pos == -1:
        return None

    start = max(0, best_pos - 200)
    end = min(len(full_text), best_pos + 2800)
    return full_text[start:end]


def get_maya_prospectus_url(company_name: str) -> Optional[str]:
    """
    מנסה לחלץ קישור לתשקיף/דוח אחרון מ-Maya.
    מחזיר URL של PDF אם נמצא.
    """
    # חיפוש בסיסי ב-Maya (ללא API key)
    search_url = (
        f"https://maya.tase.co.il/api/search?q={requests.utils.quote(company_name)}"
        f"&type=prospectus&limit=1"
    )
    try:
        headers = {"User-Agent": "HaltScanner/1.0"}
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.ok:
            data = response.json()
            items = data.get("results", data.get("items", []))
            if items:
                first = items[0]
                return first.get("url") or first.get("link")
    except Exception:
        pass

    return None
