# PERSISTENCE — SMART FLOW

START -> scene_01_trigger.md
scene_01_trigger.md -> scene_02_conflict.md

# אם בקונפליקט יש הצפה — נכנסים ללופ וויסות
scene_02_conflict.md -> loop_overwhelm.md

# לופ הצפה:
# A = חיזוק קטן → ממשיכים קדימה
# B = עדיין כבד → חוזרים לקונפליקט
loop_overwhelm.md:A -> scene_03_choice.md
loop_overwhelm.md:B -> scene_02_conflict.md

# אם בבחירה יש ספק — לופ ספק
scene_03_choice.md -> loop_doubt.md

# לופ ספק:
# A = בוחר צעד קטן → הצלחה
# B = חוזר לבדוק את עצמו בקונפליקט
loop_doubt.md:A -> SUCCESS
loop_doubt.md:B -> scene_02_conflict.md

SUCCESS -> END
# --- Demo: Multi-Day Proof (Persistence) ---

scene_03_choice.md -> day_01.md

day_01.md -> day_02.md
day_02.md -> day_03.md

# Day 03 has 2 emotional endings:
day_03.md:A -> SUCCESS
day_03.md:B -> scene_02_conflict.md

