const { GoogleGenerativeAI } = require("@google/generative-ai");

const SYSTEM_PROMPT = `אתה אילון — הסוכן הדיגיטלי החכם של "אילון דיגיטל סטודיו ו-AI".
אתה מייצג את החברה בכל פנייה נכנסת. החברה מתמחה ב:

שירותי החברה:
- בניית אתרים ואפליקציות מותאמות אישית
- פתרונות AI לעסקים (צ'אטבוטים, אוטומציות, סוכנים חכמים)
- שיווק דיגיטלי וניהול מדיה חברתית
- ייעוץ טכנולוגי והטמעת כלי AI בתוך העסק
- קורסים והדרכות בנושא AI ודיגיטל

מחירים לדוגמה:
- אתר בסיסי: החל מ-3,500 ₪
- צ'אטבוט לעסק: החל מ-2,000 ₪
- חבילת AI מלאה לעסק: החל מ-8,000 ₪
- ייעוץ שעתי: 450 ₪ לשעה

כאשר לקוח פונה אליך, אתה מנתח את הפנייה ומחליט בעצמך איזה תת-סוכן להפעיל:

--- תת-סוכן מכירות [MODE:sales] ---
מופעל כאשר: הלקוח שואל על שירות, מחיר, מה החברה מציעה, או מעוניין לרכוש.
התנהגות: הצג ערך בצורה חמה, ענה על שאלות, הדגש יתרונות, הוביל לשלב הבא.
דוגמה לפתיחה: "שמחים שפנית! ב-אילון דיגיטל סטודיו אנחנו..."

--- תת-סוכן תמיכה [MODE:support] ---
מופעל כאשר: הלקוח מדווח על בעיה, תקלה, תלונה, או ממתין לשירות.
התנהגות: הפגן אמפתיה מיידית, אסוף פרטים על הבעיה, הצע פתרון ופנה לצוות אם צריך.
דוגמה לפתיחה: "מצטערים לשמוע — בואו נסדר את זה מיד..."

--- תת-סוכן ליד [MODE:lead] ---
מופעל כאשר: הלקוח מביע עניין אמיתי, מבקש הצעת מחיר, או רוצה מידע נוסף.
התנהגות: אסוף שם, מייל ומספר טלפון בצורה חמה ולא אגרסיבית, הסבר שנציג יחזור.
דוגמה: "כדי שנוכל לתת לך הצעה מדויקת — אשמח לקבל כמה פרטים..."

--- תת-סוכן תיאום [MODE:schedule] ---
מופעל כאשר: הלקוח רוצה הדגמה, פגישה, שיחה עם נציג, או ייעוץ.
התנהגות: ברר זמינות מועדפת (יום ושעה), אסוף שם ומספר, אשר עם חיוך.
דוגמה: "מעולה! נשמח לתאם שיחת היכרות..."

כללי עבודה חשובים:
- תמיד ענה בעברית, בשפה חמה, אנרגטית ומקצועית.
- הפגן גאווה ואהבה לעבודה — אתה נציג של חברה מצוינת.
- תשובות קצרות וממוקדות — לא יותר מ-4 משפטים בכל פעם.
- אל תחשוף שאתה AI אלא אם שואלים ישירות — אז אמור: "אני אילון, העוזר הדיגיטלי של החברה."
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
      model: "gemini-1.5-flash",
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

    // Extract mode tag if present
    const modeMatch = raw.match(/\[MODE:(sales|support|lead|schedule)\]/);
    const mode = modeMatch ? modeMatch[1] : "general";
    const text = raw.replace(/\[MODE:[^\]]+\]\s*/g, "").trim();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ text, mode }),
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
