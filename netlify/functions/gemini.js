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
                        parts: [{ text: systemInstruction }]
                    },
                    contents: [
                        {
                            parts: [
                                {
                                    text: `מצב: ${modeKey}\nחוכמה מתוך Wisdom.md:\n${Array.isArray(wisdomContext) ? wisdomContext.slice(0, 3).join('\n') : ''}\n\nקלט משתמש: ${userText}`
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
