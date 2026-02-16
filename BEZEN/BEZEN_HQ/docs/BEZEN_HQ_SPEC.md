# BEZEN HQ Spec

## Folder Conventions
- `skills/<SKILL>/scenes/<SCENE_ID>.md` for scene files.
- `skills/<SKILL>/FLOW.md` for ordered scene flow per skill.
- `scenarios/*.md` reserved for scenario orchestration (do not change path structure).

## Naming
- `<SKILL>` is uppercase with underscores (example: `HOPE_CORE`).
- `<SCENE_ID>` is an exact identifier from `data/seed.json` (example: `scene_01`, `scene_03B`).
- File names must match `<SCENE_ID>.md` exactly.

## Scene Frontmatter (Required)
Frontmatter is strict YAML. All fields are required and must be non-empty.

```yaml
---
bezen_schema: bezen_scene_v1
id: "scene_01"
title_he: "כותרת בעברית"
title_en: "English Title"
trait: "trait_name"
variant: "variant_name"
feature: "feature_name"
hook_sentence: "משפט פתיחה בעברית"
panels:
  - id: "p1"
    text: "טקסט פנל 1 בעברית"
  - id: "p2"
    text: "טקסט פנל 2 בעברית"
  - id: "p3"
    text: "טקסט פנל 3 בעברית"
  - id: "p4"
    text: "טקסט פנל 4 בעברית"
  - id: "p5"
    text: "טקסט פנל 5 בעברית"
  - id: "p6"
    text: "טקסט פנל 6 בעברית"
choices:
  - id: "A"
    text: "בחירה A בעברית"
    result: "תוצאה קצרה בעברית"
  - id: "B"
    text: "בחירה B בעברית"
    result: "תוצאה קצרה בעברית"
  - id: "C"
    text: "בחירה C בעברית"
    result: "תוצאה קצרה בעברית"
  - id: "D"
    text: "בחירה D בעברית"
    result: "תוצאה קצרה בעברית"
correct_choice_id: "B"
reflection: "משפט שיקוף בעברית"
task: "משימה קצרה בעברית"
riddle: "חידה קצרה בעברית"
proverb: "פתגם בעברית"
closing: "משפט סיום בעברית"
---
```

## Flow.md Rule
- `skills/<SKILL>/FLOW.md` must exist and list scenes in order.
- Each entry must link to `scenes/<SCENE_ID>.md`.

## Scene Schema (Strict)
- `id`: string, exact scene identifier (matches filename).
- `title_he`: string, Hebrew title (RTL UI text).
- `title_en`: string, English title.
- `trait`: string, trait label.
- `variant`: string, variant label.
- `feature`: string, feature label.
- `hook_sentence`: string, Hebrew hook sentence.
- `panels`: array of 6 objects, each has `id` and `text` (Hebrew).
- `choices`: array of 4 objects, each has `id`, `text` (Hebrew), `result` (Hebrew).
- `correct_choice_id`: string, must match one of the choice `id` values.
- `reflection`: string, Hebrew reflection.
- `task`: string, Hebrew task.
- `riddle`: string, Hebrew riddle.
- `proverb`: string, Hebrew proverb.
- `closing`: string, Hebrew closing line.

## How to Add New Scenes
1) Append the new scene object to `data/seed.json` under the correct skill.
2) Run `node tools/bezen_build.js` to generate new files.
3) Run `node tools/bezen_validate.js` and fix any reported issues.
