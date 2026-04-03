"""
analyzer.py – ניתוח AI עם Claude
מחלץ ספקים/שותפים נסחרים מתשקיפים ודוחות
"""
import json
import re
import anthropic
from typing import List, Dict, Optional

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def create_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def extract_suppliers_from_text(
    client: anthropic.Anthropic,
    company_name: str,
    announcement_text: str,
    prospectus_text: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> List[Dict]:
    """
    מבקש מ-Claude לזהות ספקים/שותפים שאולי נסחרים בבורסה.
    """
    context_parts = [
        f"הודעת הבורסה:\n{announcement_text[:2000]}"
    ]

    if prospectus_text:
        context_parts.append(
            f"\nקטע רלוונטי מתשקיף/דוח:\n{prospectus_text[:3000]}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""אתה מנתח פיננסי מומחה בשוק ההון הישראלי.

חברה: {company_name}

{context}

משימה: זהה ספקים עיקריים, שותפים אסטרטגיים, או קבלני משנה של {company_name} שעלולים להיות נסחרים בבורסת ת"א (TASE) או בבורסות אחרות.

הנחיות:
1. חפש שמות חברות ספציפיים שמוזכרים כספקים, שותפים, או לקוחות עיקריים
2. נסה לזהות אם הם נסחרים (חברות ציבוריות)
3. אם יש סמל מסחר ידוע – ציין אותו (עם סיומת .TA לבורסת ת"א)
4. הסבר קצר מדוע הם קשורים לחברה הראשית
5. דרג confidence לפי מידת הוודאות שהם באמת ספק/שותף ושהם נסחרים

החזר JSON בלבד (ללא טקסט נוסף) בפורמט הזה:
[
  {{
    "name": "שם החברה הספק",
    "ticker": "SYMB.TA או null אם לא ידוע",
    "reason": "ספק חומרי גלם / שותף אסטרטגי / קבלן משנה",
    "confidence": "high/medium/low"
  }}
]

אם לא נמצאו ספקים נסחרים, החזר: []
"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text = block.text
                break

        json_match = _extract_json(text)
        if json_match:
            suppliers = json.loads(json_match)
            return suppliers if isinstance(suppliers, list) else []

    except anthropic.APIError as e:
        print(f"[Analyzer] שגיאת Claude API: {e}")
    except json.JSONDecodeError as e:
        print(f"[Analyzer] שגיאת JSON parsing: {e}")
    except Exception as e:
        print(f"[Analyzer] שגיאה כללית: {e}")

    return []


def analyze_halt_opportunity(
    client: anthropic.Anthropic,
    company_name: str,
    announcement_text: str,
    main_change_pct: float,
    supplier_data: List[Dict],
    model: str = DEFAULT_MODEL,
) -> str:
    """
    מבקש מ-Claude ניתוח קצר של ההזדמנות הפוטנציאלית.
    """
    suppliers_str = "\n".join([
        f"- {s['name']}: {s.get('change_pct', 'N/A')}% (סמל: {s.get('ticker', '?')})"
        for s in supplier_data
    ])

    prompt = f"""ניתוח הזדמנות קצר (3-4 משפטים בעברית):

חברה ראשית: {company_name} – עלתה {main_change_pct:.1f}% אחרי הודעה מהותית
הודעה: {announcement_text[:500]}

ספקים/שותפים שנבדקו:
{suppliers_str}

האם יש כאן הזדמנות? מה הסיכון? תן המלצה קצרה ופשוטה.
חשוב: זו אינה המלצת השקעה – רק ניתוח ראשוני לבדיקה עצמית.
"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        for block in response.content:
            if block.type == "text":
                return block.text.strip()
    except Exception as e:
        print(f"[Analyzer] שגיאה בניתוח הזדמנות: {e}")

    return "לא ניתן לבצע ניתוח כרגע."


def upload_pdf_for_analysis(
    client: anthropic.Anthropic,
    pdf_bytes: bytes,
    filename: str = "prospectus.pdf",
) -> Optional[str]:
    """מעלה PDF ל-Files API של Anthropic."""
    try:
        uploaded = client.beta.files.upload(
            file=(filename, pdf_bytes, "application/pdf"),
        )
        return uploaded.id
    except Exception as e:
        print(f"[Analyzer] שגיאת העלאת PDF: {e}")
        return None


def extract_suppliers_from_pdf_file(
    client: anthropic.Anthropic,
    company_name: str,
    file_id: str,
    model: str = DEFAULT_MODEL,
) -> List[Dict]:
    """מנתח PDF שהועלה דרך Files API ומחלץ ספקים."""
    prompt = f"""אתה מנתח פיננסי מומחה בשוק ההון הישראלי.

בדוח/תשקיף המצורף של {company_name}, זהה:
1. ספקים עיקריים (ספקי חומרי גלם, יצרנים, קבלני משנה)
2. שותפים אסטרטגיים
3. לקוחות עיקריים

עבור כל גורם שמצאת, בדוק אם הוא חברה ציבורית נסחרת.

החזר JSON בלבד:
[
  {{
    "name": "שם החברה",
    "ticker": "סמל מסחר עם סיומת .TA או null",
    "reason": "תיאור הקשר לחברה",
    "page_reference": "עמוד X (אם ידוע)",
    "confidence": "high/medium/low"
  }}
]
"""

    try:
        response = client.beta.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "file", "file_id": file_id},
                        "title": f"תשקיף {company_name}",
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
            betas=["files-api-2025-04-14"],
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text = block.text
                break

        json_match = _extract_json(text)
        if json_match:
            result = json.loads(json_match)
            return result if isinstance(result, list) else []

    except Exception as e:
        print(f"[Analyzer] שגיאת ניתוח PDF: {e}")

    return []


# ── פונקציות עזר ─────────────────────────────────────────

def _extract_json(text: str) -> Optional[str]:
    """מחלץ JSON מטקסט שעשוי להכיל טקסט נוסף."""
    code_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
    if code_match:
        return code_match.group(1)

    array_match = re.search(r'(\[[\s\S]*\])', text)
    if array_match:
        return array_match.group(1)

    return None
