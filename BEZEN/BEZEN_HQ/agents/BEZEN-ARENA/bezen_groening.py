"""
BEZEN-GROENING — an agent on the teaching of Bruno Gröning, with the BEZEN layer.

Built for the Circle of Friends (20+ branches in Israel, 100+ countries). Ofer
Leiba and Dov review it before it goes anywhere.

Retrieval is local (groening_corpus), so one LLM call per turn — the same latency
reasoning as bezen_support.

Three hard constraints, each of them there because of a specific failure:

1. QUOTES. The agent may only quote text that appears verbatim in the retrieved
   passages, and only from the movement's own site. Cozio's video archive is
   retrieved for topic-finding but is never quotable — it is his edit, and parts
   of it came through OCR with visible errors. A fabricated Gröning quote that
   spreads to 100 countries cannot be recalled.

2. MEDICINE. The Circle's own medical group (MWF) describes the method as a
   "תוספת" — a supplement to conventional or alternative medical knowledge, not a
   replacement. The agent says that, in their words, and never advises anyone to
   start, stop or change treatment, and never diagnoses.

3. THE CONTROVERSY. The movement's own biography documents the trials, the
   healing ban and the negligent-homicide charge. So the agent answers those
   questions straight from that material. Evasion would read far worse than the
   facts, which are already public on their site.
"""

import json
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv, dotenv_values

import groening_corpus

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parents[3] / "data"
load_dotenv(SCRIPT_DIR / ".env", override=True)

API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not API_KEY:
    vals = dotenv_values(SCRIPT_DIR / ".env")
    API_KEY = (vals.get("ANTHROPIC_API_KEY") or "").strip()


# Two experienced representatives. Every question about joining a circle, a local
# group, or a remote group goes to them — they explain and route to the
# facilitator in the right city. The agent never tries to answer this itself.
CONTACTS = [
    {"name": "בלהה", "phone": "054-7809195"},
    {"name": "כרמית", "phone": "052-4766334"},
]

PLAYLIST = "https://www.youtube.com/playlist?list=PLQ93nZFhhcvdHcvsQ7Npd6zKdCRz0pu_j"


def _load_videos() -> dict:
    try:
        return json.loads((DATA_DIR / "groening_videos.json").read_text(encoding="utf-8"))
    except Exception:
        return {"playlist": PLAYLIST, "topics": {}}


VIDEOS = _load_videos()

_LANG_NAMES = {"he": "Hebrew", "en": "English", "de": "German",
               "ru": "Russian", "ar": "Arabic"}


SYSTEM = """אתה סוכן מלווה של חוג ידידי ברונו גרונינג. אתה עונה על שאלות אודות שיטתו של ברונו גרונינג מתוך החומר הרשמי של התנועה בלבד.

# חוקים מוחלטים — אין מהם חריגה

## ציטוטים
- מותר לך לצטט **אך ורק** טקסט שמופיע מילה במילה בקטעים שסומנו "מקור רשמי — מותר לצטט".
- קטעים שסומנו "ארכיון פנימי" משמשים אותך רק כדי להבין באיזה נושא מדובר. **אסור לצטט מהם, ואסור לייחס מהם דבר לברונו גרונינג.**
- אסור לך לנסח מחדש משפט ולהציג אותו כאילו הוא ציטוט. ציטוט = העתקה מדויקת.
- אם נושא השאלה אינו מכוסה בקטעים שקיבלת — תגיד את זה במפורש, ואל תשלים מהידע הכללי שלך.
- כשאתה מצטט, ציין בגוף המשפט מאיזה עמוד באתר הרשמי זה בא — בשם העמוד בלבד. **אל תדביק כתובות URL ואל תוסיף שורת "מקור:" בסוף.** הממשק כבר מציג למשתמש את הקישורים לעמודים.

## רפואה
- אתה לא רופא ולא מאבחן. אסור לך לומר לאדם להתחיל, להפסיק, לשנות או לדחות טיפול רפואי כלשהו.
- העמדה הרשמית של הקבוצה הרפואית-מדעית (MWF) של התנועה: שיטתו של ברונו גרונינג היא **תוספת** לידע הרפואי הקונבנציונלי או האלטרנטיבי — לא תחליף לו. כשעולה שאלה רפואית, זו העמדה שאתה מוסר.
- **חובה:** בכל פעם שאדם מזכיר מחלה ממשית שיש לו, כאב גופני שהוא חווה, החמרה במצבו, או מצוקה נפשית — עליך לכלול בתשובה, במשפט אחד טבעי ולא מנוסח כאזהרה משפטית, את העובדה שהשיטה היא תוספת ולא תחליף לטיפול רפואי, ושכדאי שרופא יבדוק את מה שהוא מתאר. זה לא אופציונלי ואינו תלוי בהקשר.
- אל תאמר לאדם שכאב שהוא חווה הוא "בוודאי" Regelungen או "לא החמרה של המחלה". אינך יודע זאת, ואינך יכול לדעת. תאר מה השיטה אומרת על התופעה — ואל תאבחן מה קורה אצלו בפועל.
- אם עולה סכנה מיידית לחיים, אמור זאת ישירות והפנה לעזרה דחופה. אל תרכך.

## השנוי במחלוקת
- אם שואלים על המשפטים, האיסור לעסוק בריפוי, כתב האישום או הביקורת — **ענה ישירות מהביוגרפיה הרשמית של התנועה.** אל תתחמק ואל תתגונן. העובדות האלה מפורסמות באתר שלהם עצמם, והתחמקות פוגעת באמון הרבה יותר מהעובדות.

## חוגים ומפגשים
- שאלות על הצטרפות לחוג, מפגשים, חוג באזור מסוים או חוג מרחוק — **אתה לא עונה עליהן מהחומר.** אתה מפנה לשתי נציגות ותיקות שמסבירות ומפנות למנחה בעיר המתאימה:
  בלהה 054-7809195 · כרמית 052-4766334

# איך אתה עונה — שכבת BEZEN

1. **קול אחד, לא תפריט.** אף פעם לא רשימת טיפים או נקודות. תשובה אחת זורמת, כמו אדם שמכיר את החומר ומדבר.
2. **קודם לזהות מה מתחת למילים.** לפני התוכן — משפט אחד קצר שמכיר במה שהאדם באמת אמר. לא "אני מבין אותך", אלא משהו ספציפי לדבריו.
3. **להחזיר פיסת שליטה.** אל תיתן פתרון שלם. תן דבר אחד קטן שהאדם עצמו יכול לעשות או להחליט.
4. **בלי הבטחות ובלי סופרלטיבים.** אל תבטיח החלמה, תוצאה או ישועה. תשובה מכוילת בונה אמון יותר מתשובה נלהבת.
5. **צעד אחד קונקרטי בסוף**, לא שלושה.
6. **בלי הצפה.** אל תפרוס את כל התורה בתשובה אחת. נושא אחד, לעומק.
7. ענה בשפת השואל.

## שפות — כלל קריטי
- ענה תמיד בשפה שבה פנו אליך.
- **אסור לך להציג תרגום משלך כציטוט של ברונו גרונינג.** תרגום שלך אינו המקור.
- ברשותך התרגומים הרשמיים של סעיף המשנה ב**עברית, גרמנית, אנגלית, רוסית וערבית**. אם הקטע שקיבלת הוא כבר בשפת השואל — צטט אותו כלשונו, זה הנוסח המאושר של התנועה.
- אם הקטע בשפה אחרת מזו שבה אתה עונה: הבא את הציטוט **בשפת המקור כלשונו**, ולידו הסבר בשפת השואל — או הסבר במילים שלך תוך שאתה אומר במפורש שזה תיאור ולא ציטוט.
- ציין שהאתר הרשמי של התנועה קיים ב-33 שפות, ושכדאי לקרוא שם את הנוסח המאושר בשפתו.

אל תשתמש בכותרות, בתוויות, בכוכביות, בהדגשות markdown או ברשימות. טקסט רץ בלבד."""


class BezenGroening:
    def __init__(self, client: Anthropic, model: str):
        self.client = client
        self.model = model

    # ── suggestion of a presentation to watch after the answer ──
    def suggest_video(self, passages: list, question: str) -> dict:
        """Pick the presentation closest to what was actually discussed.

        Preference goes to a topic that came back from retrieval, so the
        suggestion follows the conversation instead of being random.
        """
        topics = VIDEOS.get("topics", {})
        for p in passages:
            if p.get("section") == "topics" and p["title"] in topics:
                return {"topic": p["title"], **topics[p["title"]]}
        # Nothing from the video archive was retrieved, so no single presentation
        # genuinely matches — biography and trial questions land here. Offering a
        # loosely-related one would look like the agent wasn't listening; the
        # playlist is the honest answer.
        return {"topic": "", "video_title": "כל המצגות", "url": VIDEOS.get("playlist", PLAYLIST)}

    def respond(self, message: str, history: list = None, max_tokens: int = 1100) -> dict:
        history = history or []
        passages = groening_corpus.search(message, top_k=6)
        context = groening_corpus.as_context(passages)

        msgs = []
        for h in history[-8:]:
            role = h.get("role")
            content = (h.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                msgs.append({"role": role, "content": content})

        # The whole system prompt is Hebrew, which pulled replies into Hebrew even
        # when the question was English — the "answer in the user's language" rule
        # was buried under it. This directive goes last, where it carries the most
        # weight, and names the language when the script tells us which it is.
        named = _LANG_NAMES.get(groening_corpus.detect_lang(message))
        directive = (
            "IMPORTANT: Write your ENTIRE reply in the same language the user "
            "wrote their question in — every sentence, not only the quotations."
        )
        if named and re.search(r"[Ѐ-ӿ֐-׿؀-ۿA-Za-z]", message):
            directive += f" That language is {named}."

        msgs.append({
            "role": "user",
            "content": (
                f"קטעים מהקורפוס שאותרו עבור השאלה הזו:\n\n{context}\n\n"
                f"---\n\nהשאלה של המשתמש:\n{message}\n\n---\n{directive}"
            ),
        })

        try:
            r = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=SYSTEM,
                messages=msgs,
            )
            reply = r.content[0].text.strip()
            # Strip stray markdown the model sometimes emits despite the
            # rule above — keep the words, drop the markup.
            reply = re.sub(r"\*\*(.+?)\*\*", r"\1", reply)
            reply = re.sub(r"^#+\s*", "", reply, flags=re.M)
        except Exception as e:
            return {"error": str(e), "reply": "", "sources": [], "video": None}

        # A pure routing answer ("call Bilha / Carmit") isn't grounded in the
        # corpus, so sources and a presentation under it would be misleading.
        # But a substantive answer that merely mentions the contacts at the end
        # is still grounded — length is what separates the two.
        has_contact = any(c["phone"].replace("-", "") in reply.replace("-", "") for c in CONTACTS)
        routed = has_contact and len(reply) < 500

        # Drop weak retrieval hits so the source line reflects what was actually
        # used, not whatever happened to share a word with the question.
        strong = [p for p in passages if p["authority"] == "official" and p["score"] >= 2.0]

        return {
            "reply": reply,
            "routed": routed,
            "sources": [] if routed else [
                {"title": p["title"], "url": p["url"], "section": p["section"],
                 "authority": p["authority"], "score": p["score"]}
                for p in strong
            ],
            "video": None if routed else self.suggest_video(passages, message),
            "contacts": CONTACTS,
            "retrieved": len(passages),
        }
