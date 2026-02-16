const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const seedPath = path.join(root, 'data', 'seed.json');

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

function validateScene(scene, scenePath, errors) {
  const content = fs.readFileSync(scenePath, 'utf8');
  const frontmatter = parseFrontmatter(content);

  if (!frontmatter) {
    errors.push(`Missing or invalid frontmatter: ${scenePath}`);
    return;
  }

  const requiredFields = [
    'bezen_schema',
    'id',
    'title_he',
    'title_en',
    'trait',
    'variant',
    'feature',
    'hook_sentence',
    'panels',
    'choices',
    'correct_choice_id',
    'reflection',
    'task',
    'riddle',
    'proverb',
    'closing'
  ];

  requiredFields.forEach((field) => {
    if (frontmatter[field] === undefined || frontmatter[field] === '') {
      errors.push(`Missing required field '${field}' in ${scenePath}`);
    }
  });

  if (frontmatter.bezen_schema !== 'bezen_scene_v1') {
    errors.push(`Invalid bezen_schema in ${scenePath}`);
  }

  if (frontmatter.id !== scene.id) {
    errors.push(`Scene id mismatch in ${scenePath} (expected ${scene.id})`);
  }

  if (!Array.isArray(frontmatter.panels) || frontmatter.panels.length !== 6) {
    errors.push(`Panels must have exactly 6 items in ${scenePath}`);
  }

  if (!Array.isArray(frontmatter.choices) || frontmatter.choices.length !== 4) {
    errors.push(`Choices must have exactly 4 items in ${scenePath}`);
  }

  const choiceIds = Array.isArray(frontmatter.choices) ? frontmatter.choices.map((c) => c.id) : [];
  const correctId = frontmatter.correct_choice_id;
  const correctCount = choiceIds.filter((id) => id === correctId).length;
  if (correctCount !== 1) {
    errors.push(`correct_choice_id must match exactly one choice in ${scenePath}`);
  }

  if (Array.isArray(frontmatter.panels)) {
    frontmatter.panels.forEach((panel, index) => {
      if (!panel.id || !panel.text) {
        errors.push(`Panel ${index + 1} must include id and text in ${scenePath}`);
      }
    });
  }

  if (Array.isArray(frontmatter.choices)) {
    frontmatter.choices.forEach((choice, index) => {
      if (!choice.id || !choice.text || !choice.result) {
        errors.push(`Choice ${index + 1} must include id, text, and result in ${scenePath}`);
      }
    });
  }
}

function validateFlow(skill, errors) {
  const flowPath = path.join(root, 'skills', skill.id, 'FLOW.md');
  if (!fs.existsSync(flowPath)) {
    errors.push(`Missing FLOW.md: ${flowPath}`);
    return;
  }
  const flowContent = fs.readFileSync(flowPath, 'utf8');
  let cursor = 0;
  (skill.scenes || []).forEach((scene) => {
    const link = `scenes/${scene.id}.md`;
    const index = flowContent.indexOf(link, cursor);
    if (index === -1) {
      errors.push(`FLOW.md missing link for ${scene.id} in ${flowPath}`);
    } else {
      cursor = index + link.length;
    }
  });
}

function validate() {
  if (!fs.existsSync(seedPath)) {
    console.error(`Seed file not found: ${seedPath}`);
    process.exit(1);
  }

  const seed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  if (!seed.skills || !Array.isArray(seed.skills)) {
    console.error('Seed file must include a skills array.');
    process.exit(1);
  }

  const errors = [];

  seed.skills.forEach((skill) => {
    const skillDir = path.join(root, 'skills', skill.id);
    const scenesDir = path.join(skillDir, 'scenes');

    if (!fs.existsSync(scenesDir)) {
      errors.push(`Missing scenes directory: ${scenesDir}`);
      return;
    }

    (skill.scenes || []).forEach((scene) => {
      const scenePath = path.join(scenesDir, `${scene.id}.md`);
      if (!fs.existsSync(scenePath)) {
        errors.push(`Missing scene file: ${scenePath}`);
        return;
      }
      validateScene(scene, scenePath, errors);
    });

    validateFlow(skill, errors);
  });

  if (errors.length > 0) {
    errors.forEach((error) => {
      console.error(`ERROR: ${error}`);
    });
    process.exit(1);
  }

  console.log('Validation passed.');
}

validate();
