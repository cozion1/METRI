exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'שיטת בקשה לא נתמכת' })
        };
    }

    try {
        const payload = JSON.parse(event.body || '{}');
        const {
            modeKey = 'personal',
            userText = '',
            fallbackText = '',
            wisdomContext = [],
            chatHistory = [],
            systemInstruction = ''
        } = payload;

        if ((!userText || !userText.trim()) && modeKey !== 'experiential-break') {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'חסר טקסט משתמש' })
            };
        }

        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            if (modeKey === 'teacher-impact') {
                return {
                    statusCode: 200,
                    body: JSON.stringify({
                        text: JSON.stringify({
                            agent: "HEART",
                            helpfulSentence: "אני מרגיש כל כך כועס עכשיו, אני צריך רגע להירגע לפני שאני עונה.",
                            explanation: "(סימולציה ללא API Key) - התלמיד מציג רגש מציף של כעס ופגיעות שמפורש כהתפוצצות."
                        })
                    })
                };
            }
            if (modeKey === 'personal') {
                const historyLength = chatHistory ? chatHistory.length : 0;
                let simulatedResponse = "";
                if (historyLength === 0 || historyLength === 1) { // Just the user's first message
                    simulatedResponse = "(סימולציה) אני מבין שזה מה שאתה מרגיש עכשיו. זה בטח ממש מציף. מאיפה לדעתך הגיעה ההרגשה הזאת?";
                } else if (historyLength === 2 || historyLength === 3) {
                    simulatedResponse = "(סימולציה) זה טבעי להרגיש ככה כשדברים כאלה קורים. בוא נחשוב ביחד – מה לדעתך היה גורם לך להרגיש אפילו קצת יותר טוב עכשיו?";
                } else if (historyLength === 4 || historyLength === 5) {
                    simulatedResponse = "(סימולציה) אני מבין. ואיך אתה חושב שהצד השני רואה את הדברים? האם יכול להיות שהם התכוונו למשהו אחר?";
                } else {
                    simulatedResponse = "(סימולציה) אנחנו עושים כאן עבודה תודעתית יפה. בוא נתקדם לאט ונמשיך לחקור את זה יחד. מה הצעד הבא שהיית רוצה לעשות?";
                }
                return {
                    statusCode: 200,
                    body: JSON.stringify({ text: simulatedResponse })
                };
            }
            if (modeKey === 'experiential-break') {
                return {
                    statusCode: 200,
                    body: JSON.stringify({ text: "הנה קטע חשיבה קצר (סימולציה): לפעמים הדברים נראים גדולים יותר ממה שהם. ניקח נשימה עמוקה ונחשוב מה באמת חשוב." })
                };
            }
            return {
                statusCode: 200,
                body: JSON.stringify({ text: fallbackText || 'אני כאן איתך, וביחד נבחר צעד קטן וטוב.' })
            };
        }

        let contents = [];

        if (modeKey === 'teacher-impact') {
            contents = [{ parts: [{ text: `משפט התלמיד לניתוח: "${userText}"` }] }];
        } else if (modeKey === 'personal' && chatHistory && chatHistory.length > 0) {
            // Personal Mode with Chat History
            contents = [...chatHistory];
        } else if (modeKey === 'experiential-break' && chatHistory && chatHistory.length > 0) {
            // Experiential Break takes chat history to generate contextual content
            contents = [...chatHistory];
        } else {
            contents = [
                {
                    parts: [
                        { text: `מצב: ${modeKey}\nחוכמה מתוך Wisdom.md:\n${Array.isArray(wisdomContext) ? wisdomContext.slice(0, 3).join('\n') : ''}\n\nקלט משתמש: ${userText}` }
                    ]
                }
            ];
        }

        const model = 'gemini-flash-latest';
        const response = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_instruction: {
                        parts: [{ text: modeKey === 'teacher-impact' ? getTeacherImpactPrompt() : (modeKey === 'personal' ? getPersonalProgressivePrompt() : (modeKey === 'experiential-break' ? getExperientialPrompt() : systemInstruction)) }]
                    },
                    contents: contents
                })
            }
        );

        if (!response.ok) {
            return {
                statusCode: 200,
                body: JSON.stringify({ text: fallbackText || 'אני כאן איתך, וביחד נבחר צעד קטן וטוב.' })
            };
        }

        const data = await response.json();
        const apiText = data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || '';

        // If it's the new mode, return the JSON string directly
        if (modeKey === 'teacher-impact') {
            return {
                statusCode: 200,
                body: JSON.stringify({ text: apiText }) // Keep wrapper for client parsing
            };
        }

        // If it's the personal chat mode or experiential break, return the full text
        if (modeKey === 'personal' || modeKey === 'experiential-break') {
            return {
                statusCode: 200,
                body: JSON.stringify({ text: apiText }) // Keep full progressive response
            };
        }

        const concise = apiText.split('\n').map((line) => line.trim()).filter(Boolean).slice(0, 2).join(' ');

        return {
            statusCode: 200,
            body: JSON.stringify({ text: concise || fallbackText || 'אני כאן איתך, וביחד נבחר צעד קטן וטוב.' })
        };
    } catch (error) {
        return {
            statusCode: 200,
            body: JSON.stringify({ text: 'אני כאן איתך, וביחד נבחר צעד קטן וטוב.' })
        };
    }
};

function getTeacherImpactPrompt() {
    return `אתה סוכן AI למורים בשם BEZEN-TEACHER, מיועד לעזור למורים בבתי ספר יסודיים להפוך משפטים טעוני שיפור (שנשמעים תוקפניים או פוגעניים) למשפטים מווסתים ומועילים.
המשתמש (המורה) יזין משפט ששמע מתלמיד.

עליך לבצע 3 פעולות בלבד:
1. זהה את מניע השורש (הסוכן הפנימי) של המשפט. בחר אחד מתוך 5 בלבד: MIND (מחשבה פרנואידית/האשמה), HEART (רגש מציף/עלבון/שנאה), BODY (תחושת פיצוץ/חום בגוף), ACTION (איום במעשה/אלימות פיזית או מילולית ישירה), SOUL (אמונת עומק קשה - "אני כלום", "חייב להחזיר").
2. חבר "משפט מועיל" (כלומר - מה התלמיד יכול להגיד במקום, כדי להביע את המצוקה בלי לתקוף). המשפט צריך להיות מנוסח בגוף ראשון ("אני מרגיש ש...").
3. כתוב כלי הרגעה קצר למורה - הסבר למורה למה הסוכן הזה נבחר.

עליך להחזיר את התשובה *אך ורק* כפורמט JSON תקין (אל תוסיף טקסט מעבר), במבנה הבא בדיוק גימור:
{
  "agent": "MIND | HEART | BODY | ACTION | SOUL",
  "helpfulSentence": "המשפט שהתלמיד יכול להגיד במקום",
  "explanation": "הסבר קצר למורה (עד 2 משפטים)."
}
`;
}

function getPersonalProgressivePrompt() {
    return `אתה מנטור רוחני, איש חכם ומספר סיפורים לילדים בבית ספר יסודי.
המטרה שלך היא להוביל את התלמיד מהמשפט הקשה והטעון שלו דרך מסע עמוק ומרתק אל "שביל הזהב" - משפט מאוזן, חיובי ובונה.
במקום "לחפור" עם שאלות ישירות או פסיכולוגיה יבשה שמשעממת ילדים, תפקידך *לייצר חוויה* עשירה בדמיון!

חוקי ברזל:
1. אל תקפוץ לעולם לפתרון מהיר. זהו מסע ארוך שנועד להדהד שינוי פנימי דרך חוויה תודעתית רצופה. ענה תמיד בקצרה, פסקה אחת או שתיים לכל היותר.
2. **חובת שימוש בחוויה:** לעולם, בשום אופן, אל תענה רק בשאלות יבשות! בכל תגובה שלך לילד, פתח באחד ורק אחד מהכלים הבאים (גוון ביניהם):
   - **סיפור מוסר השכל קצרצר:** על חכמי קדם, בעלי חיים או כוחות טבע (למשל, סיפור על שני זאבים או על נהר זועם).
   - **משחק דמיון מסקרן:** "דמיין שהכעס שדיברת עליו נראה כמו כדור של אש בידייך. תשחק איתו רגע במחשבה. איזה צבע יש לו עכשיו כשהוא מתקרר מעט?"
   - **חידה מטאפורית:** קצרצרה שצריך לפתור, הקשורה לכוח פנימי, לכעס או לויתור, ומשאירה את הילד סקרן.
   - **פתגם עתיק:** כלי קסום מהפסיכולוגיה החיובית שמוגש בצורה מלהיבה כ"סוד" או כספר עתיק.
3. דבר בשפה ציורית, חמה ומרתקת של מספר סיפורים, בגובה העיניים של ילד. צור עבורו חוויה שבה הוא "הגיבור".
4. סיים כל הודעה בשאלה אחת קטנה הקשורה לחוויה/לסיפור הדימיוני שיצרת, במטרה שיוביל אוטומטית למחשבה פנימית וקידום הדיאלוג אל שביל הזהב. לעולם אל תשאל "למה אתה מרגיש ככה?".
זכור: המטרה היא להשאיר את התלמיד מרותק לדיאלוג (לשחק, להאזין לסיפור, לפתור את החידון) כדי שההטמעה תהיה חווייתית ולא דידקטית!`;
}

function getExperientialPrompt() {
    return `אתה מדריך נשימה מומחה בוויסות רגשי לילדים.
עליך לייצר *אך ורק* תרגיל נשימה פעיל של 30 שניות, בלי שאלות, בלי שיח, רק הנחיות פעולה לזמן ההמתנה.

מצורפת היסטוריית השיחה כדי שתשלב מסר הרגעה שרומז אל "המשפט המועיל" (הכיוון החיובי) במקום המשפט השלילי או ההתפרצות.

חוקי ברזל:
1. איסור מוחלט על שאלות: לעולם אל תשאל "מה אתה מרגיש?" או "מה תבחר עכשיו?". סיים את הטקסט בנקודה ומשפט הרגעה.
2. אל תחזור על משפט המצוקה השלילי של הילד!
3. חובה לגוון תמיד: תן לילד בכל פעם תרגיל נשימה שונה ממש (נשימת בלון מתנפח, כיבוי נר, נשימת ריבוע, ספירה 4-7-8, הדחת ריח של פרח).
4. חובה להנחות את הילד לנשוף ולשאוף בהתאמה לאנימציה מולו: "שאף כשהעיגול מולך גדל / נשוף כשהוא קטן".

תבנית חובה לתשובה שלך (ענה בדיוק לפי המבנה הזה, בגוף שני יחיד - אתה):
[פסקה 1: משפט נעים שמרמז בעדינות על "המשפט המועיל" ולמה כדאי לנוח רגע.]
[פסקה 2: הנחיות נשימה מדויקות ופעילות (למשל: "כשהעיגול שעל המסך גדל, קח שאיפה עמוקה פנימה... 1, 2, 3... וכשהוא קטן, הוצא את האוויר בנשיפה ארוכה ממש כמו לכבות מסביבך נרות...")]
[פסקה 3: משפט סיום קצר, בטוח ומרגיע. חובה עליך להוסיף בסופו בדיוק את המילים: "המשך הדיאלוג."!]

החזר רק את טקסט התרגיל, ללא כל הקדמה.`;
}
