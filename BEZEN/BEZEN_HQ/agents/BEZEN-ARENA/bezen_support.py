"""
BEZEN-SUPPORT — Customer service agent with the BEZEN layer.

Architecture note (this differs from bezen_wordsmith on purpose):
wordsmith runs 6 sequential LLM calls, which takes 30-60 seconds. That is fine
for a side-by-side demo page, and unusable for live customer service — a person
waiting on a chat widget leaves after ~10 seconds.

So this agent gets its pattern recognition from pattern_bridge (local keyword
matching over the BEZEN pattern library — instant, no API call) and spends its
single LLM call on the actual reply. Same BEZEN principles, response time in
seconds instead of a minute.

Multi-turn by design: a support conversation is a conversation, not a one-shot.
"""

import os
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv, dotenv_values

import pattern_bridge

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env", override=True)
API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not API_KEY:
    vals = dotenv_values(SCRIPT_DIR / ".env")
    API_KEY = (vals.get("ANTHROPIC_API_KEY") or "").strip()


# Default business config — overridden per deployment by the client's own details.
DEFAULT_BUSINESS = {
    "name": "השירות",
    "domain": "שירות לקוחות כללי",
    "policies": "",
    "escalation": "נציג אנושי יחזור אליך",
}


BEZEN_SUPPORT_PRINCIPLES = """
BEZEN response principles — these shape HOW you reply, on top of your role above:

1. ONE VOICE, NOT A MENU. Never answer with a bulleted or numbered list of options,
   tips, or possible causes. One clear, flowing reply — the way a competent human
   representative actually writes.

2. NAME WHAT'S UNDER THE WORDS FIRST. Before solving, acknowledge the actual
   experience in ONE short sentence — not "I understand your frustration" (empty
   filler), but something specific to what they said. If a customer says "a month
   and nobody answers", the real message is "I've been abandoned", not "I have a
   refund inquiry". Address that first, briefly.

3. RESTORE A SLIVER OF CONTROL. The customer is stuck because things are happening
   TO them. Where possible, give back one concrete piece of agency — a number they
   can hold you to, a specific next moment, one thing they can decide.

4. NO EXTREMES, NO EMPTY PROMISES. Don't say "immediately", "absolutely",
   "definitely" if you can't guarantee it. A calibrated, honest answer builds more
   trust than an enthusiastic one that disappoints. If you don't know — say so
   plainly and say what you're doing about it.

5. ONE CONCRETE NEXT STEP. End with exactly one specific thing that happens next —
   who does what, and when. Not three options for them to choose from.

6. NEVER DEFEND THE COMPANY OVER THE PERSON. Don't explain policy at someone who is
   upset until you have first acknowledged what happened to them.

7. NEVER INVENT SYSTEM DATA. You have NO access to any account, order, ticket, or
   billing system. You must never state or imply that you can see a record, a
   status, an approval, or a history — no "I see your ticket", no "your refund was
   approved", no invented dates or amounts. If the customer gives you a reference
   number, acknowledge receiving it and say what will be done with it. Everything
   you assert as fact must come from the policies given above or from what the
   customer told you. Inventing a status is worse than admitting you cannot see it.

8. KEEP YOUR OWN VOICE CONSISTENT. Stay in one consistent grammatical person and
   gender for yourself throughout the whole conversation. Do not assume the
   customer's gender — if their language does not make it clear, phrase around it.

Match the language of the customer's message exactly. No headers, no labels, no
markdown formatting in your reply — write it as a message a person sends.
"""


class BezenSupport:
    """Customer service agent: pattern recognition + BEZEN-shaped single reply."""

    def __init__(self, client, model, business: dict = None):
        self.client = client
        self.model = model
        self.business = {**DEFAULT_BUSINESS, **(business or {})}

    def _system_prompt(self, message: str, business: dict) -> str:
        matched = pattern_bridge.match(message, top_k=3)
        pattern_context = pattern_bridge.describe(matched)

        policies = business.get("policies") or "(no specific policies provided)"

        return f"""You are a customer service representative for {business['name']}.
Business area: {business['domain']}

Known policies and facts you may rely on:
{policies}

When something genuinely requires a human: {business['escalation']}

Human patterns detected in how this customer wrote their message:
{pattern_context}
Use this to understand what they actually need — do NOT mention the patterns,
do not diagnose them, and never tell the customer what they are feeling.

{BEZEN_SUPPORT_PRINCIPLES}"""

    def respond(self, message: str, history: list = None, business: dict = None) -> dict:
        """Reply to one customer message, in the context of the conversation so far.

        history: list of {"role": "user"|"assistant", "content": str}
        """
        biz = {**self.business, **(business or {})}
        matched = pattern_bridge.match(message, top_k=3)

        messages = []
        for turn in (history or []):
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        try:
            r = self.client.messages.create(
                model=self.model,
                max_tokens=700,
                system=self._system_prompt(message, biz),
                messages=messages,
            )
            reply = r.content[0].text.strip()
        except Exception as e:
            reply = f"[Support error: {e}]"

        return {
            "response": reply,
            "detected_patterns": [
                {"id": p["id"], "label_he": p["label_he"], "label_en": p["label_en"]}
                for p in matched
            ],
        }

    def plain_reply(self, message: str, history: list = None, business: dict = None) -> str:
        """The SAME agent without the BEZEN layer — the control group for comparison."""
        biz = {**self.business, **(business or {})}
        policies = biz.get("policies") or "(no specific policies provided)"

        messages = []
        for turn in (history or []):
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        try:
            r = self.client.messages.create(
                model=self.model,
                max_tokens=700,
                system=(
                    f"You are a customer service representative for {biz['name']}.\n"
                    f"Business area: {biz['domain']}\n\n"
                    f"Known policies and facts you may rely on:\n{policies}\n\n"
                    "Answer politely and helpfully. Match the customer's language."
                ),
                messages=messages,
            )
            return r.content[0].text.strip()
        except Exception as e:
            return f"[Plain error: {e}]"


if __name__ == "__main__":
    client = Anthropic(api_key=API_KEY)
    support = BezenSupport(client, "claude-sonnet-4-5-20250929", {
        "name": "סלקום",
        "domain": "חברת סלולר — חבילות, חשבוניות, תקלות רשת",
        "policies": "זיכוי כספי מטופל תוך 14 ימי עסקים. ניתן לבדוק סטטוס פנייה עם מספר הפנייה.",
        "escalation": "נציג בכיר יחזור אליך תוך יום עסקים אחד",
    })
    test = "אני כבר חודש מחכה שתחזירו לי כסף ואף אחד לא עונה לי!"
    out = support.respond(test)
    print("PATTERNS:", [p["label_he"] for p in out["detected_patterns"]])
    print()
    print(out["response"])
