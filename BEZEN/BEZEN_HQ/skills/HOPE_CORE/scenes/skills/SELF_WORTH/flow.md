# SELF_WORTH — FLOW
# SELF_WORTH — Flow

START -> scene_01_trigger

scene_01_trigger:
  next: scene_02_conflict

scene_02_conflict:
  choices:
    A: loop_comparison
    B: scene_03_choice

loop_comparison:
  description: חזרה לדפוס ההשוואה וההקטנה
  next: scene_01_trigger

scene_03_choice:
  choices:
    A: loop_comparison
    B: reinforce_self_worth

reinforce_self_worth:
  description: חיזוק כבוד עצמי רגוע
  effect:
    - הפחתת עוצמת הקול הביקורתי
    - הגברת ויסות רגשי
  next: scene_01_trigger
