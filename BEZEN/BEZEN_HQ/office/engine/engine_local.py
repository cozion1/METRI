# BEZEN_HQ/office/engine/engine_local.py
from pathlib import Path
import re, json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]        # .../BEZEN_HQ
INPUT = ROOT / "office" / "inputs" / "teen_sentences.txt"
OUTDIR = ROOT / "runtime" / "logs"
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT = OUTDIR / "engine_output.jsonl"

# חוקים בסיסיים (אפשר להרחיב בלי סוף)
DOMAIN_RULES = [
    ("loneliness", [r"\bלבד\b", r"שקוף", r"לא רוצים אותי", r"לא מבינים אותי", r"אין לי.*עם מי לדבר"]),
    ("self_worth", [r"לא שווה", r"אני אפס", r"כישלון", r"לא מספיק"]),
    ("social_anxiety", [r"יצחקו עליי", r"כולם שופטים", r"עדיף לשתוק", r"אני לא מעז"]),
    ("anger", [r"נמאס לי", r"מתפוצץ", r"בא לי לצעוק", r"להחזיר להם"]),
    ("despair", [r"אין טעם", r"תמיד יהיה ככה", r"בא לי להיעלם"]),
]

BALANCE_MAP = {
    "loneliness": ("נסיגה", "חיבור בטוח"),
    "self_worth": ("השוואה/מחיקת עצמי", "ערך פנימי"),
    "social_anxiety": ("הימנעות", "אומץ רגוע"),
    "anger": ("התפרצות", "ויסות רגשי"),
    "despair": ("ויתור/קיבעון", "תקווה פעילה"),
}

def severity(text: str) -> str:
    # חומרה פשוטה: מילים מוחלטות / קיצוניות
    if any(w in text for w in ["תמיד", "אף פעם", "אף אחד", "אין טעם"]):
        return "גבוהה"
    return "בינונית"

def detect_domain(text: str) -> str:
    for domain, pats in DOMAIN_RULES:
        for pat in pats:
            if re.search(pat, text):
                return domain
    return "unknown"

def bridge_sentence(domain: str) -> str:
    # משפט גשר אמין (לא “חיובי בכוח”)
    bridges = {
        "loneliness": "עכשיו אני מרגיש לבד, אבל זה לא אומר שככה זה תמיד.",
        "self_worth": "עכשיו אני מרגיש פחות, אבל זה לא מגדיר את מי שאני.",
        "social_anxiety": "עכשיו אני מפחד מתגובה, וזה טבעי כשחשוב לי מה יחשבו.",
        "anger": "עכשיו אני מוצף בכעס, ואני יכול לעצור רגע לפני תגובה.",
        "despair": "עכשיו קשה לי לראות מוצא, אבל התחושה הזו יכולה להשתנות.",
        "unknown": "עכשיו קשה לי, ובוא נפרק את זה צעד-צעד."
    }
    return bridges.get(domain, bridges["unknown"])

def helpful_sentence(domain: str) -> str:
    helpful = {
        "loneliness": "אני יכול ליצור חיבור קטן ובטוח, צעד אחד היום.",
        "self_worth": "הערך שלי לא תלוי בלייקים או בהשוואות.",
        "social_anxiety": "אני יכול לדבר בקטן ובבטוח, בלי להוכיח כלום.",
        "anger": "אני בוחר תגובה שמכבדת אותי, גם כשאני כועס.",
        "despair": "צעד קטן אחד עדיף על לוותר — והוא מספיק להיום.",
        "unknown": "אני יכול לבחור צעד קטן שמחזיר לי שליטה."
    }
    return helpful.get(domain, helpful["unknown"])

def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT}")

    lines = [ln.strip("• \t") for ln in INPUT.read_text(encoding="utf-8").splitlines()]
    sentences = [ln for ln in lines if ln and not ln.startswith("שלב") and not ln.startswith("משפטים")]

    with OUT.open("w", encoding="utf-8") as f:
        for s in sentences:
            domain = detect_domain(s)
            sev = severity(s)
            neg, pos = BALANCE_MAP.get(domain, ("לא ידוע", "איזון"))
            rec = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "input": s,
                "domain": domain,
                "severity": sev,
                "pattern": neg,
                "balanced_trait": pos,
                "bridge": bridge_sentence(domain),
                "helpful": helpful_sentence(domain),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"✅ Done. Wrote: {OUT}")

if __name__ == "__main__":
    main()
