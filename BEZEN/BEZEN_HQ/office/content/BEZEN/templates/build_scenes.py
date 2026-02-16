import json
from pathlib import Path

# ---------- הגדרות ----------
TRAITS_ROOT = Path("../traits")   # תיקיית התכונות
SCENES_PER_TRAIT = 15             # כמה סצנות לייצר

def scene_template(trait_name, index):
    return {
        "scene_id": f"{trait_name}_{index:02d}",
        "loaded_sentence": "",
        "bridge_ladder": [
            "אני מזהה את הקושי",
            "אני עוצר רגע לנשימה",
            "אני בוחר תגובה אחרת",
            "אני מתקדם צעד קטן",
            "אני מחזק את עצמי",
            "אני ממשיך קדימה"
        ],
        "user_choice_prompt": "מה תבחר לעשות עכשיו?",
        "choice_A": "להתקדם",
        "choice_B": "להישאר במקום",
        "micro_task": "בצע פעולה קטנה",
        "implicit_trait_hint": trait_name,
        "optional_trait_label": trait_name,
        "next_scene_hint": f"{trait_name}_{index+1:02d}"
    }

def build_scenes():
    if not TRAITS_ROOT.exists():
        print(f"❌ לא מצאתי את התיקיה: {TRAITS_ROOT.resolve()}")
        print("בדוק שאתה מריץ מתוך templates (cd templates).")
        return

    trait_folders = [p for p in TRAITS_ROOT.iterdir() if p.is_dir()]
    if not trait_folders:
        print(f"❌ אין תיקיות תכונה בתוך: {TRAITS_ROOT.resolve()}")
        return

    for trait_folder in trait_folders:
        trait_name = trait_folder.name
        print(f"🔹 בונה סצנות ל: {trait_name}")

        for i in range(1, SCENES_PER_TRAIT + 1):
            scene_data = scene_template(trait_name, i)
            file_path = trait_folder / f"scene_{i:02d}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(scene_data, f, ensure_ascii=False, indent=2)

        print(f"✅ נוצרו {SCENES_PER_TRAIT} קבצים עבור {trait_name}\n")

if __name__ == "__main__":
    build_scenes()
