import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]  # BEZEN_HQ
TEMPLATE_DIR = ROOT / "skills_HOPE_CORE" / "skills_TEMPLATE"
SKILLS_ROOT = ROOT  / "skills_HOPE_CORE"   # נשארים באותו Skill-root כמו שעשית

def slug(name: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in "_-") else "_" for ch in name.strip()).upper()

def render(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text

def main():
    cfg_path = ROOT / "tools" / "skill_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    skill_name = slug(cfg["skill_name"])
    emotion = cfg["emotion"].strip()
    negative_sentence = cfg["negative_sentence"].strip()

    # יעד
    out_dir = SKILLS_ROOT / f"skills_{skill_name}"
    scenes_dir = out_dir / "scenes"

    # הקשר לתבניות
    ctx = {
        "SKILL_NAME": skill_name,
        "EMOTION": emotion,
        "NEGATIVE_SENTENCE": negative_sentence,
        "GENERATED_AT": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # צור תיקיות
    scenes_dir.mkdir(parents=True, exist_ok=True)

    # העתק/צור תבניות בסיס (אם קיימות)
    # 1) scene_template.md -> מייצר 3 סצנות בסיס לדוגמה
    scene_template = (TEMPLATE_DIR / "scene_template.md").read_text(encoding="utf-8")
    flow_template  = (TEMPLATE_DIR / "flow_template.md").read_text(encoding="utf-8")
    scoring_template = (TEMPLATE_DIR / "scoring_template.md").read_text(encoding="utf-8")

    # סצנות בסיס (אפשר להרחיב אחר כך)
    (scenes_dir / "scene_01_trigger.md").write_text(
        render(scene_template, {**ctx, "SCENE_ID": "01", "SCENE_TITLE": "Trigger"}), encoding="utf-8"
    )
    (scenes_dir / "scene_02_crack.md").write_text(
        render(scene_template, {**ctx, "SCENE_ID": "02", "SCENE_TITLE": "Crack"}), encoding="utf-8"
    )
    (scenes_dir / "scene_03_bridge.md").write_text(
        render(scene_template, {**ctx, "SCENE_ID": "03", "SCENE_TITLE": "Bridge"}), encoding="utf-8"
    )

    # קבצי מערכת
    (out_dir / "flow.md").write_text(render(flow_template, ctx), encoding="utf-8")
    (out_dir / "scoring.md").write_text(render(scoring_template, ctx), encoding="utf-8")

    # extras
    (out_dir / "triggers.md").write_text(
        f"# Triggers — {skill_name}\n\n- Emotion: {emotion}\n- Negative Sentence: {negative_sentence}\n",
        encoding="utf-8"
    )
    (out_dir / "overview.md").write_text(
        f"# Overview — {skill_name}\n\nנוצר אוטומטית ב־{{GENERATED_AT}}.\n\n"
        f"## ליבה\n- Emotion: {emotion}\n- Negative Sentence: {negative_sentence}\n",
        encoding="utf-8"
    )

    print("✅ GENERATED:", out_dir)

if __name__ == "__main__":
    main()
