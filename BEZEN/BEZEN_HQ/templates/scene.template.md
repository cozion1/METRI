---
bezen_schema: bezen_scene_v1
id: "{{id}}"
title_he: "{{title_he}}"
title_en: "{{title_en}}"
trait: "{{trait}}"
variant: "{{variant}}"
feature: "{{feature}}"
hook_sentence: "{{hook_sentence}}"
panels:
  - id: "p1"
    text: "{{panel_1}}"
  - id: "p2"
    text: "{{panel_2}}"
  - id: "p3"
    text: "{{panel_3}}"
  - id: "p4"
    text: "{{panel_4}}"
  - id: "p5"
    text: "{{panel_5}}"
  - id: "p6"
    text: "{{panel_6}}"
choices:
  - id: "A"
    text: "{{choice_a}}"
    result: "{{choice_a_result}}"
  - id: "B"
    text: "{{choice_b}}"
    result: "{{choice_b_result}}"
  - id: "C"
    text: "{{choice_c}}"
    result: "{{choice_c_result}}"
  - id: "D"
    text: "{{choice_d}}"
    result: "{{choice_d_result}}"
correct_choice_id: "{{correct_choice_id}}"
reflection: "{{reflection}}"
task: "{{task}}"
riddle: "{{riddle}}"
proverb: "{{proverb}}"
closing: "{{closing}}"
---

# {{title_he}}

## פתיח
{{hook_sentence}}

## פנלים
1. {{panel_1}}
2. {{panel_2}}
3. {{panel_3}}
4. {{panel_4}}
5. {{panel_5}}
6. {{panel_6}}

## בחירות
- A: {{choice_a}}
- B: {{choice_b}}
- C: {{choice_c}}
- D: {{choice_d}}

## שיקוף
{{reflection}}

## משימה
{{task}}

## חידה
{{riddle}}

## פתגם
{{proverb}}

## סיום
{{closing}}
