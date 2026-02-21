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
            systemInstruction = ''
        } = payload;

        if (!userText || !userText.trim()) {
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
            return {
                statusCode: 200,
                body: JSON.stringify({ text: fallbackText || 'אני כאן איתך, וביחד נבחר צעד קטן וטוב.' })
            };
        }

        const model = 'gemini-2.0-flash-001';
        const response = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_instruction: {
                        parts: [{ text: modeKey === 'teacher-impact' ? getTeacherImpactPrompt() : systemInstruction }]
                    },
                    contents: [
                        {
                            parts: [
                                {
                                    text: modeKey === 'teacher-impact'
                                        ? `משפט התלמיד לניתוח: "${userText}"`
                                        : `מצב: ${modeKey}\nחוכמה מתוך Wisdom.md:\n${Array.isArray(wisdomContext) ? wisdomContext.slice(0, 3).join('\n') : ''}\n\nקלט משתמש: ${userText}`
                                }
                            ]
                        }
                    ]
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
    return `אתה סוכן AI למורים בשם BEZEN-TEACHER, מיועד לעזור למורים בבתי ספר יסודיים להפוך משפטים אלימים למשפטים מווסתים.
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
