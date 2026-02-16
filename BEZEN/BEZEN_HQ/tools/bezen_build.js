const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const seedPath = path.join(root, 'data', 'seed.json');
const templatePath = path.join(root, 'templates', 'scene.template.md');

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
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

function build() {
  if (!fs.existsSync(seedPath)) {
    console.error(`Seed file not found: ${seedPath}`);
    process.exit(1);
  }

  const seed = JSON.parse(fs.readFileSync(seedPath, 'utf8'));
  if (!seed.skills || !Array.isArray(seed.skills)) {
    console.error('Seed file must include a skills array.');
    process.exit(1);
  }

  seed.skills.forEach((skill) => {
    const skillId = skill.id;
    const skillScenesDir = path.join(root, 'skills', skillId, 'scenes');
    const flowPath = path.join(root, 'skills', skillId, 'FLOW.md');

    ensureDir(skillScenesDir);

    (skill.scenes || []).forEach((scene) => {
      const scenePath = path.join(skillScenesDir, `${scene.id}.md`);
      if (fs.existsSync(scenePath)) {
        return;
      }
      const content = renderScene(scene);
      fs.writeFileSync(scenePath, content, 'utf8');
    });

    const flowLines = [];
    flowLines.push('<!-- BEZEN_FLOW_LINKS_START -->');
    flowLines.push(`# BEZEN Flow Links — ${skillId}`);
    flowLines.push('');
    (skill.scenes || []).forEach((scene, index) => {
      const order = index + 1;
      flowLines.push(`${order}. [${scene.id}](scenes/${scene.id}.md)`);
    });
    flowLines.push('');
    flowLines.push('<!-- BEZEN_FLOW_LINKS_END -->');
    const flowBlock = flowLines.join('\n');

    if (!fs.existsSync(flowPath)) {
      const newFlow = [`# FLOW — ${skillId}`, '', flowBlock, ''].join('\n');
      fs.writeFileSync(flowPath, newFlow, 'utf8');
      return;
    }

    const existingFlow = fs.readFileSync(flowPath, 'utf8');
    const startToken = '<!-- BEZEN_FLOW_LINKS_START -->';
    const endToken = '<!-- BEZEN_FLOW_LINKS_END -->';
    const startIndex = existingFlow.indexOf(startToken);
    const endIndex = existingFlow.indexOf(endToken);

    if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
      const before = existingFlow.slice(0, startIndex).trimEnd();
      const after = existingFlow.slice(endIndex + endToken.length).trimStart();
      const merged = [before, flowBlock, after].filter(Boolean).join('\n\n') + '\n';
      fs.writeFileSync(flowPath, merged, 'utf8');
    } else {
      const appended = existingFlow.trimEnd() + '\n\n' + flowBlock + '\n';
      fs.writeFileSync(flowPath, appended, 'utf8');
    }
  });
}

build();
