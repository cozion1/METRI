"""
yahoo_finance.py – שליפת מחירי מניות בבורסת ת"א
מניות ת"א מסומנות ב-Yahoo Finance עם סיומת .TA
"""
import yfinance as yf
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

# מיפוי שמות נפוצים לסמלי מסחר ב-Yahoo Finance
COMMON_TASE_TICKERS = {
    "טבע": "TEVA",         # Teva – נסחרת בנאסד"ק, גם ב-ת"א
    "בנק לאומי": "LUMI.TA",
    "בנק הפועלים": "POLI.TA",
    "בנק דיסקונט": "DSCT.TA",
    "בנק מזרחי": "MZTF.TA",
    "כלל ביטוח": "CLIS.TA",
    "מגדל": "MGDL.TA",
    "הראל": "HARL.TA",
    "אבן": "AVEN.TA",
    "נייס": "NICE",
    "אמדוקס": "DOX",
    "גילת": "GILT.TA",
    "אורמת": "ORA",
    "ממן": "MMAN.TA",
}


def get_price_change(ticker: str, period_hours: int = 1) -> Optional[float]:
    """
    מחזיר את אחוז השינוי במחיר המניה ב-N שעות האחרונות.
    מחזיר None אם לא ניתן לקבל נתונים.
    """
    # נסה עם ו-בלי סיומת .TA
    tickers_to_try = _normalize_ticker(ticker)

    for t in tickers_to_try:
        result = _fetch_change(t, period_hours)
        if result is not None:
            return result

    return None


def get_current_price(ticker: str) -> Optional[float]:
    """מחזיר את המחיר הנוכחי של המניה."""
    for t in _normalize_ticker(ticker):
        try:
            info = yf.Ticker(t).fast_info
            price = getattr(info, "last_price", None)
            if price and price > 0:
                return float(price)
        except Exception:
            continue
    return None


def get_price_data(ticker: str, period: str = "1d", interval: str = "5m") -> Optional[Dict]:
    """
    שליפת נתוני מחירים מפורטים.
    מחזיר: {"open", "current", "change_pct", "volume", "ticker"}
    """
    for t in _normalize_ticker(ticker):
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                continue

            open_price = float(hist["Open"].iloc[0])
            current_price = float(hist["Close"].iloc[-1])
            volume = int(hist["Volume"].sum())

            if open_price <= 0:
                continue

            change_pct = ((current_price - open_price) / open_price) * 100

            return {
                "ticker": t,
                "open": open_price,
                "current": current_price,
                "change_pct": round(change_pct, 2),
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"[Yahoo Finance] שגיאה עבור {t}: {e}")
            continue

    return None


def resolve_ticker(company_name: str) -> Optional[str]:
    """
    מנסה לזהות סמל מסחר לפי שם החברה.
    תחילה בטבלה הידועה, אחר-כך חיפוש ב-Yahoo Finance.
    """
    # בדיקה בטבלה הידועה
    for name, ticker in COMMON_TASE_TICKERS.items():
        if name in company_name or company_name in name:
            return ticker

    # ניסיון עם שם החברה כסמל ישירות
    candidates = _normalize_ticker(company_name.upper().replace(" ", ""))
    for t in candidates:
        try:
            stock = yf.Ticker(t)
            info = stock.fast_info
            price = getattr(info, "last_price", None)
            if price and price > 0:
                return t
        except Exception:
            continue

    return None


# ── פונקציות עזר פנימיות ──────────────────────────────────

def _normalize_ticker(ticker: str) -> list:
    """יוצר רשימת גרסאות אפשריות לסמל המסחר."""
    ticker = ticker.strip().upper()
    candidates = []

    if ticker.endswith(".TA"):
        candidates = [ticker, ticker[:-3], ticker[:-3] + ".TLV"]
    elif "." in ticker:
        candidates = [ticker]
    else:
        candidates = [ticker + ".TA", ticker, ticker + ".TLV"]

    return candidates


def _fetch_change(ticker: str, hours: int) -> Optional[float]:
    """שליפה ספציפית של שינוי אחוזי."""
    try:
        stock = yf.Ticker(ticker)
        # 1d עם interval של 5 דקות - מספיק לבדיקת ביצועים יומיים
        hist = stock.history(period="1d", interval="5m")

        if hist.empty or len(hist) < 2:
            return None

        open_price = float(hist["Open"].iloc[0])
        current_price = float(hist["Close"].iloc[-1])

        if open_price <= 0:
            return None

        change_pct = ((current_price - open_price) / open_price) * 100
        return round(change_pct, 2)

    except Exception:
        return None
