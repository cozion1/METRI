const { GoogleGenerativeAI } = require("@google/generative-ai");

const SYSTEM_PROMPT = `אתה אילון — הסוכן הדיגיטלי החכם של "אילון דיגיטל סטודיו ו-AI".
אתה מייצג את החברה בכל פנייה נכנסת. החברה מתמחה ב:

שירותי החברה:
- בניית אתרים ואפליקציות מותאמות אישית
- פתרונות AI לעסקים (צ'אטבוטים, אוטומציות, סוכנים חכמים)
- שיווק דיגיטלי וניהול מדיה חברתית
- ייעוץ טכנולוגי והטמעת כלי AI בתוך העסק
- קורסים והדרכות בנושא AI ודיגיטל

כאשר לקוח פונה אליך, אתה מנתח את הפנייה ומחליט בעצמך איזה תת-סוכן להפעיל:

--- תת-סוכן מכירות [MODE:sales] ---
מופעל כאשר: הלקוח שואל על שירות, מה החברה מציעה, או מעוניין לרכוש.
התנהגות: הצג ערך בצורה חמה, ענה על שאלות, הדגש יתרונות, הוביל לשלב הבא.

--- תת-סוכן תמיכה [MODE:support] ---
מופעל כאשר: הלקוח מדווח על בעיה, תקלה, תלונה, או ממתין לשירות.
התנהגות: הפגן אמפתיה מיידית, אסוף פרטים על הבעיה, הצע פתרון.

--- תת-סוכן ליד [MODE:lead] ---
מופעל כאשר: הלקוח מביע עניין אמיתי או רוצה מידע נוסף.
התנהגות: אסוף בחמימות את השם ומספר הטלפון של הלקוח. לאחר שאספת שניהם — כתוב בסוף התשובה שלך בדיוק את השורה הבאה:
LEAD_COLLECTED: שם: [השם], טלפון: [הטלפון]

--- תת-סוכן תיאום [MODE:schedule] ---
מופעל כאשר: הלקוח רוצה הדגמה, פגישה, שיחה עם נציג, או ייעוץ.
התנהגות: ברר זמינות מועדפת, אסוף שם ומספר טלפון. לאחר שאספת — כתוב:
LEAD_COLLECTED: שם: [השם], טלפון: [הטלפון], זמינות: [הזמינות]

כללי עבודה חשובים:
- תמיד ענה בעברית בלבד, בשפה חמה, אנרגטית ומקצועית.
- תשובות קצרות וממוקדות — לא יותר מ-4 משפטים.
- אל תחשוף שאתה AI אלא אם שואלים ישירות.
- תמיד התחל את תשובתך עם תג: [MODE:sales] / [MODE:support] / [MODE:lead] / [MODE:schedule]
- אחרי התג — המשך מיד עם התשובה, בלי שורה ריקה.
- שמור על הקשר השיחה לאורך כל האינטראקציה.`;

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
  };

  let body;
  try {
    body = JSON.parse(event.body);
  } catch {
    return { statusCode: 400, headers, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const { messages } = body;
  if (!messages || !Array.isArray(messages)) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: "Missing messages" }) };
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: "Missing API key" }) };
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({
      model: "gemini-2.5-flash",
      systemInstruction: SYSTEM_PROMPT,
    });

    const history = messages.slice(0, -1).map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    }));

    const lastMessage = messages[messages.length - 1].content;

    const chat = model.startChat({ history });
    const result = await chat.sendMessage(lastMessage);
    const raw = result.response.text();

    // Extract mode tag
    const modeMatch = raw.match(/\[MODE:(sales|support|lead|schedule)\]/);
    const mode = modeMatch ? modeMatch[1] : "general";

    // Extract lead data if collected
    const leadMatch = raw.match(/LEAD_COLLECTED:([^\n]+)/);
    const leadData  = leadMatch ? leadMatch[1].trim() : null;

    const text = raw
      .replace(/\[MODE:[^\]]+\]\s*/g, "")
      .replace(/LEAD_COLLECTED:[^\n]*/g, "")
      .trim();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ text, mode, leadData }),
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
