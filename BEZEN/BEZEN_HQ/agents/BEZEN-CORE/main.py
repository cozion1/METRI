import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# ---------- Paths ----------
BASE = Path(__file__).resolve().parent
BRAIN = BASE / "brain.md"
RULES = BASE / "rules.md"
WORKFLOWS_DIR = BASE / "workflows"
MEMORY_DIR = BASE / "memory"
STATE_FILE = MEMORY_DIR / "state.json"

# ---------- Helpers ----------
def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def load_workflows(dir_path: Path) -> str:
    if not dir_path.exists():
        return ""
    parts = []
    for p in sorted(dir_path.rglob("*.md")):
        parts.append(f"\n\n# WORKFLOW: {p.relative_to(dir_path)}\n{read_text(p)}")
    return "\n".join(parts).strip()

def load_state() -> dict:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

# ---------- Main ----------
def main():
    load_dotenv(BASE / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("BEZEN_MODEL", "gpt-4.1-mini").strip()

    if not api_key or api_key.startswith("PASTE_"):
        print("❌ חסר OPENAI_API_KEY. פתח את agents/BEZEN-CORE/.env והדבק מפתח.")
        return

    client = OpenAI(api_key=api_key)

    brain = read_text(BRAIN)
    rules = read_text(RULES)
    workflows = load_workflows(WORKFLOWS_DIR)

    state = load_state()
    history = state.get("history", [])

    system_prompt = f"""
אתה BEZEN-CORE — סוכן אוטונומי שמטרתו:
1) לזהות "משפט טעון שיפור" מתוך דברי המשתמש
2) לפרק אותו לשכבות (חסם/אמונה/רגש/תחושה/דפוס חשיבה/התנהגות)
3) להציע משפט מעבר
4) להציע משפט מועיל
5) להציע תכונה מועילה מאוזנת + משימה קטנה אחת (10-60 שניות) כדי ליצור "שליטה קטנה"
6) לשמור עקביות עם brain/rules/workflows

עקרונות:
- עברית טבעית, קצרה, בלי חפירות.
- שאלה אחת בכל פעם.
- אם המשתמש כותב משפט טעון שיפור → אתה מתחיל תהליך BEZEN.
- אם המשתמש מבקש "רק להירגע עכשיו" → תן עוגן קצר + נשימה + פעולה אחת.
- תמיד סיים ב"מה הכי נכון עכשיו: (A/B/C)?" עם 3 אפשרויות קצרות.

--- BRAIN ---
{brain}

--- RULES ---
{rules}

--- WORKFLOWS ---
{workflows}
""".strip()

    print("✅ BEZEN-CORE עלה. כתוב הודעה והקש Enter.")
    print("טיפ: כתוב משפט טעון שיפור כמו: 'אם אני לא קיים ברשת – אף אחד לא ירגיש בחסרוני'")

    while True:
        user_text = input("\nאתה: ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit", "q"} or user_text in {"יציאה", "צא"}:
            print("👋 יציאה.")
            break

        history.append({"role": "user", "content": user_text, "ts": now_iso()})

        # Keep last N turns to stay fast & stable
        recent = history[-20:]
        messages = [{"role": "system", "content": system_prompt}]
        for h in recent:
            messages.append({"role": h["role"], "content": h["content"]})

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,
        )

        answer = resp.choices[0].message.content.strip()
        print("\nBEZEN-CORE:", answer)

        history.append({"role": "assistant", "content": answer, "ts": now_iso()})
        state["history"] = history
        save_state(state)

if __name__ == "__main__":
    main()
