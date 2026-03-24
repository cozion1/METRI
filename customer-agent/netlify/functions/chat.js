const { GoogleGenerativeAI } = require("@google/generative-ai");
const path = require("path");
const fs   = require("fs");

// ══ טעינת דפוסי BEZEN ══
let BEZEN_PATTERNS = [];
try {
  const p = path.join(__dirname, "pattern_map.json");
  BEZEN_PATTERNS = JSON.parse(fs.readFileSync(p, "utf8"));
} catch (e) {
  console.warn("BEZEN patterns not loaded:", e.message);
}

// ══ מילות מפתח רגשיות — ממפות ביטויים נפוצים לדפוסי BEZEN ══
const EMOTION_KEYWORDS = {
  "לא בטוח":      ["doubt","fear","comparison"],
  "לא הצלחתי":    ["stuck_progress","failure_fear","self_criticism"],
  "לא הצליח":     ["stuck_progress","failure_fear"],
  "ניסיתי":       ["stuck_progress","giving_up"],
  "לא מתאים":     ["doubt","avoidance"],
  "כבר ניסיתי":   ["stuck_progress","giving_up","avoidance"],
  "לא יודע":      ["doubt","confusion"],
  "מפחד":         ["fear_rejection","fear_failure"],
  "דואג":         ["anxiety","control"],
  "עייף":         ["burnout","avoidance"],
  "תסכול":        ["stuck_progress","comparison_trap"],
  "לבד":          ["loneliness","no_value"],
  "לא שווה":      ["no_value","self_criticism"],
  "ביקורת":       ["self_criticism","perfectionism"],
  "השוואה":       ["comparison_trap","comparison_social_media"],
  "אחרים":        ["comparison_trap","comparison_social_media"],
  "לוותר":        ["giving_up","avoidance"],
  "לדחות":        ["procrastination","avoidance"],
};

// ══ ניתוח BEZEN — שורש עברי + מילות מפתח ══
function analyzeWithBezen(text) {
  if (!BEZEN_PATTERNS.length) return null;

  const clean = text.replace(/[",'.!?״׳]/g, " ").toLowerCase();
  const words = clean.split(/\s+/).filter((w) => w.length > 2);

  // שורשים: 3 אותיות ראשונות
  const stems = words.map((w) => w.slice(0, 3));

  // IDs שזוהו דרך מילות מפתח
  const keywordHits = new Set();
  Object.entries(EMOTION_KEYWORDS).forEach(([phrase, ids]) => {
    if (clean.includes(phrase)) ids.forEach((id) => keywordHits.add(id));
  });

  const scored = BEZEN_PATTERNS.map((p) => {
    const fields = [
      p.primary_feature, p.emotion, p.behavior,
      p.limiting_belief, p.pattern_family
    ].join(" ").toLowerCase();

    let score = 0;

    // התאמת מילת מפתח מלאה — ניקוד גבוה
    if (keywordHits.has(p.pattern_id)) score += 5;

    // התאמת מילה מלאה
    words.forEach((w) => { if (fields.includes(w)) score += 2; });

    // התאמת שורש (3 אותיות)
    stems.forEach((s) => { if (fields.includes(s)) score += 1; });

    return { ...p, score };
  }).filter((p) => p.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 2);

  if (!scored.length) return null;

  return {
    top_patterns: scored.map((p) => ({
      pattern_id:      p.pattern_id,
      emotion:         p.emotion,
      behavior:        p.behavior,
      limiting_belief: p.limiting_belief,
      helpful_trait:   p.helpful_trait,
      bridge_sentence: p.bridge_sentence,
    })),
  };
}

// ══ System Prompt ══
const BASE_PROMPT = `אתה אילון — הסוכן הדיגיטלי החכם של "אילון דיגיטל סטודיו ו-AI".
אתה מייצג את החברה בכל פנייה נכנסת. החברה מתמחה ב:
- בניית אתרים ואפליקציות מותאמות אישית
- פתרונות AI לעסקים (צ'אטבוטים, אוטומציות, סוכנים חכמים)
- שיווק דיגיטלי וניהול מדיה חברתית
- ייעוץ טכנולוגי והטמעת כלי AI בתוך העסק
- קורסים והדרכות בנושא AI ודיגיטל

כאשר לקוח פונה אליך, בחר תת-סוכן:

--- [MODE:sales] --- שאלות על שירות / עניין לרכוש
--- [MODE:support] --- בעיה / תלונה / תקלה
--- [MODE:lead] --- עניין אמיתי — אסוף שם + טלפון בחמימות. לאחר שאספת: LEAD_COLLECTED: שם: X, טלפון: Y
--- [MODE:schedule] --- בקשת פגישה/הדגמה — אסוף שם + טלפון + זמינות. לאחר שאספת: LEAD_COLLECTED: שם: X, טלפון: Y, זמינות: Z

כללים:
- עברית בלבד, חמה ומקצועית.
- עד 4 משפטים בתשובה.
- התחל תמיד עם תג [MODE:...]`;

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
      },
      body: "",
    };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
  };

  let body;
  try { body = JSON.parse(event.body); }
  catch { return { statusCode: 400, headers, body: JSON.stringify({ error: "Invalid JSON" }) }; }

  const { messages } = body;
  if (!messages || !Array.isArray(messages)) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: "Missing messages" }) };
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: "Missing API key" }) };
  }

  // ══ ניתוח BEZEN ══
  const lastUserMsg = messages[messages.length - 1].content;
  const bezenResult = analyzeWithBezen(lastUserMsg);

  // בנה System Prompt עם הקשר BEZEN אם נמצא
  let systemPrompt = BASE_PROMPT;
  if (bezenResult) {
    const ctx = bezenResult.top_patterns.map((p) =>
      `• דפוס: ${p.pattern_id} | רגש: ${p.emotion} | התנהגות: ${p.behavior} | גשר: ${p.bridge_sentence} | תכונה מועילה: ${p.helpful_trait}`
    ).join("\n");

    systemPrompt += `\n\n══ ניתוח BEZEN (השתמש כהקשר, לא להציג ללקוח) ══\n${ctx}\nהתאם את תגובתך לדפוסים אלו בצורה עדינה וחמה.`;
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.5-flash",
      systemInstruction: systemPrompt,
    });

    const history = messages.slice(0, -1).map((m) => ({
      role:  m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    }));

    const chat   = model.startChat({ history });
    const result = await chat.sendMessage(lastUserMsg);
    const raw    = result.response.text();

    // מצא mode
    const modeMatch = raw.match(/\[MODE:(sales|support|lead|schedule)\]/);
    const mode = modeMatch ? modeMatch[1] : "general";

    // מצא ליד
    const leadMatch = raw.match(/LEAD_COLLECTED:([^\n]+)/);
    const leadData  = leadMatch ? leadMatch[1].trim() : null;

    const text = raw
      .replace(/\[MODE:[^\]]+\]\s*/g, "")
      .replace(/LEAD_COLLECTED:[^\n]*/g, "")
      .trim();

    // ══ ספירת טוקנים ══
    const usage = result.response.usageMetadata || {};
    const tokens = {
      prompt:    usage.promptTokenCount    || 0,
      response:  usage.candidatesTokenCount || 0,
      total:     usage.totalTokenCount      || 0,
      bezen_hit: bezenResult ? bezenResult.top_patterns.length : 0,
    };

    console.log(`[BEZEN] patterns hit: ${tokens.bezen_hit} | tokens: ${JSON.stringify(tokens)}`);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ text, mode, leadData, tokens, bezenAnalysis: bezenResult }),
    };

  } catch (err) {
    console.error(err);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: "AI error", details: err.message }),
    };
  }
};
