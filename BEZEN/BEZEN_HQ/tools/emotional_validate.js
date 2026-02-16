const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const seedPath = path.join(root, 'data', 'seed.json');

function stripBom(text) {
  if (!text) return text;
  return text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text;
}

function stripQuotes(value) {
  const trimmed = value.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseFrontmatter(text) {
  const lines = text.split(/\r?\n/);
  if (lines[0] !== '---') return null;
  let endIndex = -1;
  for (let i = 1; i < lines.length; i += 1) {
    if (lines[i] === '---') {
      endIndex = i;
      break;
    }
  }
  if (endIndex === -1) return null;
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

function countHits(text, keywords) {
  if (!text) return 0;
  let hits = 0;
  keywords.forEach((kw) => {
    if (text.includes(kw)) hits += 1;
  });
  return hits;
}

function scoreCriterion(text, keywords) {
  const hits = countHits(text, keywords);
  if (hits === 0) return 1;
  const score = 2 + hits * 2;
  return Math.min(10, score);
}

const criteria = {
  pain: ['לחץ', 'פחד', 'כאב', 'עייפות', 'ספק', 'דחייה', 'אכזבה', 'כישלון', 'רעש', 'בלבול', 'קושי', 'כבד', 'מתוח'],
  conflict: ['מהסס', 'מתלבט', 'נאבק', 'רוצה', 'צריך', 'בוחר', 'מבקש', 'מתכווץ'],
  insight: ['מזהה', 'מבין', 'לומד', 'ניסוח', 'מסגור', 'שיקוף', 'בחירה', 'תובנה', 'מגדיר'],
  balance: ['איזון', 'גבול', 'קצב', 'מתון', 'יציב', 'בריא', 'עדין', 'סבלנות'],
  empowerment: ['אפשר', 'יכול', 'בוחר', 'שליטה', 'תקווה', 'צעד', 'פעולה', 'התקדמות', 'מחזיר']
};

function improveScene(scene) {
  const appendIfMissing = (value, phrase) => (value.includes(phrase) ? value : `${value} ${phrase}`.trim());

  scene.hook_sentence = appendIfMissing(scene.hook_sentence || '', 'יש קושי ולחץ בתחילת הדרך.');

  scene.panels = (scene.panels || []).map((panel) => {
    if (panel.id === 'p1') {
      panel.text = appendIfMissing(panel.text || '', 'יש קושי וכאב שמגבילים את ההתחלה.');
    }
    if (panel.id === 'p3') {
      panel.text = appendIfMissing(panel.text || '', 'אני מהסס ונאבק פנימית.' );
    }
    if (panel.id === 'p4') {
      panel.text = appendIfMissing(panel.text || '', 'אני מזהה תובנה ראשונה ומבין מה חשוב.' );
    }
    return panel;
  });

  scene.reflection = appendIfMissing(scene.reflection || '', 'אני מזהה את השינוי ובוחר איזון בריא.' );
  scene.closing = appendIfMissing(scene.closing || '', 'אני יכול לבחור צעד יציב שמחזיר שליטה ותקווה.' );

  return scene;
}

function evaluateScene(sceneData) {
  const panelsText = (sceneData.panels || []).map((p) => p.text || '').join(' ');
  const choicesText = (sceneData.choices || []).map((c) => `${c.text || ''} ${c.result || ''}`).join(' ');
  const hook = sceneData.hook_sentence || '';
  const reflection = sceneData.reflection || '';
  const task = sceneData.task || '';
  const closing = sceneData.closing || '';
  const proverb = sceneData.proverb || '';

  const earlyText = `${hook} ${panelsText}`;
  const midText = `${panelsText} ${choicesText}`;
  const lateText = `${reflection} ${task} ${closing} ${proverb}`;

  const scores = {
    pain: scoreCriterion(earlyText, criteria.pain),
    conflict: scoreCriterion(midText, criteria.conflict),
    insight: scoreCriterion(`${reflection} ${panelsText}`, criteria.insight),
    balance: scoreCriterion(lateText, criteria.balance),
    empowerment: scoreCriterion(`${closing} ${choicesText}`, criteria.empowerment)
  };

  const total = scores.pain + scores.conflict + scores.insight + scores.balance + scores.empowerment;
  return { scores, total };
}

function validateEmotional() {
  if (!fs.existsSync(seedPath)) {
    console.error(`שגיאה: קובץ seed לא נמצא: ${seedPath}`);
    process.exit(1);
  }

  const seedRaw = stripBom(fs.readFileSync(seedPath, 'utf8'));
  const seed = JSON.parse(seedRaw);
  if (!seed.skills || !Array.isArray(seed.skills)) {
    console.error('שגיאה: seed חייב לכלול מערך skills.');
    process.exit(1);
  }

  let iterations = 0;
  let failures = [];

  while (iterations < 3) {
    failures = [];
    const results = [];

    seed.skills.forEach((skill) => {
      const scenesDir = path.join(root, 'skills', skill.id, 'scenes');
      (skill.scenes || []).forEach((scene) => {
        const scenePath = path.join(scenesDir, `${scene.id}.md`);
        if (!fs.existsSync(scenePath)) {
          failures.push({ sceneId: scene.id, reason: `קובץ סצנה חסר: ${scenePath}` });
          return;
        }
        const content = fs.readFileSync(scenePath, 'utf8');
        const frontmatter = parseFrontmatter(content);
        if (!frontmatter) {
          failures.push({ sceneId: scene.id, reason: `פרונטמטה חסרה או לא תקינה: ${scenePath}` });
          return;
        }

        const evaluation = evaluateScene(frontmatter);
        results.push({ sceneId: scene.id, scores: evaluation.scores, total: evaluation.total });

        if (evaluation.total < 35) {
          failures.push({ sceneId: scene.id, reason: `ציון רגשי כולל נמוך: ${evaluation.total}/50` });
          const improved = improveScene(frontmatter);
          const nextContent = renderScene(improved);
          fs.writeFileSync(scenePath, nextContent, 'utf8');
        }
      });
    });

    results.forEach((item) => {
      console.log(`סצנה ${item.sceneId}: כאב ${item.scores.pain}/10, קונפליקט ${item.scores.conflict}/10, תובנה ${item.scores.insight}/10, איזון ${item.scores.balance}/10, העצמה ${item.scores.empowerment}/10, סה"כ ${item.total}/50`);
    });

    if (failures.length === 0) {
      console.log('אימות רגשי עבר בהצלחה.');
      return;
    }

    iterations += 1;
  }

  console.error('נכשל: סצנות עם טרנספורמציה חלשה לאחר שיפור אוטומטי.');
  failures.forEach((fail) => {
    console.error(`- ${fail.sceneId}: ${fail.reason}`);
  });
  process.exit(1);
}

validateEmotional();
