const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

function stripQuotes(value) {
  const trimmed = value.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseFrontmatter(text) {
  const lines = text.split(/\r?\n/);
  if (lines[0] !== '---') {
    return null;
  }
  let endIndex = -1;
  for (let i = 1; i < lines.length; i += 1) {
    if (lines[i] === '---') {
      endIndex = i;
      break;
    }
  }
  if (endIndex === -1) {
    return null;
  }
  const fmLines = lines.slice(1, endIndex);
  return parseYamlFrontmatter(fmLines);
}

function parseYamlFrontmatter(lines) {
  const data = {};
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }
    const match = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!match) {
      i += 1;
      continue;
    }
    const key = match[1];
    const value = match[2];

    if (value === '') {
      if (key === 'panels' || key === 'choices') {
        const items = [];
        i += 1;
        while (i < lines.length && lines[i].startsWith('  - ')) {
          const itemLine = lines[i];
          const itemMatch = itemLine.match(/^  - ([A-Za-z0-9_]+):\s*(.*)$/);
          const item = {};
          if (itemMatch) {
            item[itemMatch[1]] = stripQuotes(itemMatch[2]);
            i += 1;
            while (i < lines.length && lines[i].startsWith('    ')) {
              const subLine = lines[i].trim();
              const subMatch = subLine.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
              if (subMatch) {
                item[subMatch[1]] = stripQuotes(subMatch[2]);
              }
              i += 1;
            }
          } else {
            i += 1;
          }
          items.push(item);
        }
        data[key] = items;
        continue;
      }
      data[key] = '';
      i += 1;
      continue;
    }

    data[key] = stripQuotes(value);
    i += 1;
  }

  return data;
}

function escapeYaml(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function renderScene(scene) {
  const panels = scene.panels || [];
  const choices = scene.choices || [];

  const lines = [];
  lines.push('---');
  lines.push('bezen_schema: bezen_scene_v1');
  lines.push(`id: "${escapeYaml(scene.id)}"`);
  lines.push(`title_he: "${escapeYaml(scene.title_he)}"`);
  lines.push(`title_en: "${escapeYaml(scene.title_en)}"`);
  lines.push(`trait: "${escapeYaml(scene.trait)}"`);
  lines.push(`variant: "${escapeYaml(scene.variant)}"`);
  lines.push(`feature: "${escapeYaml(scene.feature)}"`);
  lines.push(`hook_sentence: "${escapeYaml(scene.hook_sentence)}"`);
  lines.push('panels:');
  panels.forEach((panel) => {
    lines.push(`  - id: "${escapeYaml(panel.id)}"`);
    lines.push(`    text: "${escapeYaml(panel.text)}"`);
  });
  lines.push('choices:');
  choices.forEach((choice) => {
    lines.push(`  - id: "${escapeYaml(choice.id)}"`);
    lines.push(`    text: "${escapeYaml(choice.text)}"`);
    lines.push(`    result: "${escapeYaml(choice.result)}"`);
  });
  lines.push(`correct_choice_id: "${escapeYaml(scene.correct_choice_id)}"`);
  lines.push(`reflection: "${escapeYaml(scene.reflection)}"`);
  lines.push(`task: "${escapeYaml(scene.task)}"`);
  lines.push(`riddle: "${escapeYaml(scene.riddle)}"`);
  lines.push(`proverb: "${escapeYaml(scene.proverb)}"`);
  lines.push(`closing: "${escapeYaml(scene.closing)}"`);
  lines.push('---');
  lines.push('');
  lines.push(`# ${scene.title_he}`);
  lines.push('');
  lines.push('## פתיח');
  lines.push(scene.hook_sentence);
  lines.push('');
  lines.push('## פנלים');
  panels.forEach((panel, index) => {
    lines.push(`${index + 1}. ${panel.text}`);
  });
  lines.push('');
  lines.push('## בחירות');
  choices.forEach((choice) => {
    lines.push(`- ${choice.id}: ${choice.text}`);
  });
  lines.push('');
  lines.push('## שיקוף');
  lines.push(scene.reflection);
  lines.push('');
  lines.push('## משימה');
  lines.push(scene.task);
  lines.push('');
  lines.push('## חידה');
  lines.push(scene.riddle);
  lines.push('');
  lines.push('## פתגם');
  lines.push(scene.proverb);
  lines.push('');
  lines.push('## סיום');
  lines.push(scene.closing);
  lines.push('');

  return lines.join('\n');
}

const updates = {
  scene_01: {
    panels: {
      p3: 'היד מהססת ואתה מזהה היסוס מעל הדף הריק.'
    },
    reflection: 'תקווה נבנית לפעמים ממעשה זעיר ובאיזון.'
  },
  scene_03B: {
    panels: {
      p1: 'המטרה רחוקה ויש קושי, אך לא נעלמה.'
    },
    reflection: 'תקווה יציבה נשענת על גבול ברור ועל איזון בריא.'
  },
  scene_05: {
    panels: {
      p1: 'לפני הצעד הבא עולה שאלה קשה ואתה מהסס.'
    },
    reflection: 'כשאני מזהה את הספק, אפשר לחזור לאיזון.',
    closing: 'הספק הפך לשותף שקט והצעד הבא אפשרי.'
  },
  scene_09: {
    reflection: 'אני מזהה שדחייה היא מידע, לא זהות.',
    closing: 'מה שנגמר פינה מקום לניסיון חדש ולאיזון אפשרי.'
  },
  scene_10: {
    hook_sentence: 'הקול המבקר חזק ויוצר לחץ, אבל אפשר לענות לו ברוך.',
    panels: {
      p2: 'אתה מתכווץ ומרגיש כיווץ בכתפיים.'
    },
    reflection: 'כשאני מזהה את הקול, אפשר לבחור איזון עדין והוא יכול להיות בן-ברית.',
    closing: 'תמיכה פנימית מחזירה תנועה וצעד יציב.'
  },
  scene_11: {
    reflection: 'אני מזהה שהתמדה חכמה היא שינוי קטן בזמן ובאיזון.'
  },
  scene_13: {
    hook_sentence: 'אמון קטן יוצר שינוי גדול ביחסים גם כשיש פחד.',
    panels: {
      p3: 'אתה מזהה מי יכול לעזור ובוחר אדם אחד.'
    },
    reflection: 'אמון מתחיל בבקשה קטנה ובאיזון.',
    closing: 'בקשה קטנה פתחה דרך חדשה ואפשר צעד יציב.'
  }
};

Object.keys(updates).forEach((sceneId) => {
  const scenePath = path.join(root, 'skills', 'HOPE_CORE', 'scenes', `${sceneId}.md`);
  if (!fs.existsSync(scenePath)) {
    return;
  }
  const content = fs.readFileSync(scenePath, 'utf8');
  const frontmatter = parseFrontmatter(content);
  if (!frontmatter) {
    return;
  }
  const update = updates[sceneId];

  if (update.hook_sentence) frontmatter.hook_sentence = update.hook_sentence;
  if (update.reflection) frontmatter.reflection = update.reflection;
  if (update.closing) frontmatter.closing = update.closing;

  if (update.panels) {
    frontmatter.panels = (frontmatter.panels || []).map((panel) => {
      if (update.panels[panel.id]) {
        return { ...panel, text: update.panels[panel.id] };
      }
      return panel;
    });
  }

  const nextContent = renderScene(frontmatter);
  fs.writeFileSync(scenePath, nextContent, 'utf8');
});
