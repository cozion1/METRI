"""
BEZEN-SALES — sales rep enablement, three agents around one customer.

Built for the actual shape of Aviv's product: the user is the SALESPERSON, not
the end customer. Two agents in his design —
  1. a briefing agent that tells the rep who the customer is and what has
     happened in the conversations so far, and
  2. a simulator agent that plays that customer so the rep can practise.

Where BEZEN earns its place here:

BRIEF — a plain briefing agent summarizes facts (role, company, last call was
about pricing). The pattern layer adds the read a good sales manager gives you
in the corridor: what this person is actually protecting, and therefore what
will make them close up.

ROLEPLAY — the known failure of LLM roleplay training is that the simulated
customer is too agreeable. It concedes after one good line, breaks character to
be helpful, and never repeats itself. Real customers hold one position for the
whole call and circle back to the same objection three times. The pattern layer
is what keeps the simulated customer consistent and resistant, which is the
only thing that makes practice worth anything.

DEBRIEF — the piece a two-agent setup does not have at all: after the practice
call, tell the rep what the customer was actually protecting and where they
missed it. Pattern recognition applied to the rep's own performance.
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


DEFAULT_DEAL = {
    "vendor": "",
    "offering": "",
    "customer_name": "",
    "customer_role": "",
    "situation": "",
    "history": "",
}


def _profile_block(deal: dict) -> str:
    return f"""What we sell: {deal.get('offering') or '(not specified)'}
Selling company: {deal.get('vendor') or '(not specified)'}

THE CUSTOMER
Name: {deal.get('customer_name') or '(not specified)'}
Role: {deal.get('customer_role') or '(not specified)'}
Current situation: {deal.get('situation') or '(not specified)'}

Conversations so far:
{deal.get('history') or '(no prior conversations recorded)'}"""


class BezenSales:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def _call(self, system: str, messages: list, max_tokens: int = 800) -> str:
        try:
            r = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return r.content[0].text.strip()
        except Exception as e:
            return f"[Error: {e}]"

    # ── 1. Pre-call briefing ──────────────────────────────────────────────
    def brief(self, deal: dict, use_bezen: bool = True) -> dict:
        signal = (deal.get("history") or "") + " " + (deal.get("situation") or "")
        matched = pattern_bridge.match(signal, top_k=3)

        if not use_bezen:
            sys = f"""You are a sales briefing assistant. Brief the rep before their call.

{_profile_block(deal)}

Summarize what the rep needs to know before this call. Match the language of the input."""
            return {"response": self._call(sys, [{"role": "user", "content": "תדרך אותי לפני השיחה"}]),
                    "detected_patterns": []}

        pattern_context = pattern_bridge.describe(matched)
        sys = f"""You are briefing a salesperson right before their call. You are the
colleague who catches them in the corridor and tells them the thing that is not in the CRM.

{_profile_block(deal)}

Human patterns detected in how this customer has been communicating:
{pattern_context}

Write a briefing that covers, in flowing prose (no bullet lists, no headers):
- Where this deal actually stands, in one honest sentence — including if it is going badly.
- What this customer is protecting. Not what they said they want — what is underneath it.
  Someone who keeps asking about price may be protecting themselves from having to justify
  the decision internally, which is a different problem than cost.
- The one move most likely to make them close up in this call, stated concretely.
- One specific thing to open with.

Be direct and specific to THIS customer. Never produce generic sales advice that would
apply to anyone. If the information given is too thin to read the person, say so plainly
instead of inventing a personality for them.

Never invent facts about the customer that were not given to you.
Match the language of the input. Maximum 200 words."""

        return {
            "response": self._call(sys, [{"role": "user", "content": "תדרך אותי לפני השיחה"}]),
            "detected_patterns": [
                {"id": p["id"], "label_he": p["label_he"], "label_en": p["label_en"]}
                for p in matched
            ],
        }

    # ── 2. Customer simulator for practice ────────────────────────────────
    def roleplay(self, message: str, history: list, deal: dict, use_bezen: bool = True) -> str:
        messages = []
        for turn in (history or []):
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        if not use_bezen:
            sys = f"""You are roleplaying a potential customer so a salesperson can practise.

{_profile_block(deal)}

You are {deal.get('customer_name') or 'the customer'}. Respond in character to the
salesperson. Match the language of the input."""
            return self._call(sys, messages, max_tokens=500)

        signal = (deal.get("history") or "") + " " + (deal.get("situation") or "")
        matched = pattern_bridge.match(signal, top_k=3)
        pattern_context = pattern_bridge.describe(matched)

        sys = f"""You are roleplaying a potential customer so a salesperson can practise on you.
You ARE this person. You are not an assistant and you are not here to be helpful.

{_profile_block(deal)}

Human patterns this customer operates from:
{pattern_context}

HOW TO STAY REAL — this is the whole point of the exercise:

- HOLD YOUR POSITION. Real customers do not concede because the rep said something
  clever once. If you have a concern, you still have it three exchanges later, and you
  circle back to it even after they "answered" it. Give ground only when they have
  genuinely addressed the thing underneath your objection — and even then, slowly.

- YOUR STATED OBJECTION IS RARELY THE REAL ONE. Say the surface thing ("it's expensive",
  "we're happy with our current vendor"). Only reveal what is actually behind it if the
  rep earns it by asking well. If they push on the surface objection, get more guarded,
  not more open.

- BE INCONSISTENT LIKE A PERSON. Get distracted. Bring up something irrelevant that is
  on your mind. Be short when you are annoyed and talkative when a topic interests you.

- DO NOT BREAK CHARACTER. Never coach the rep, never comment on their technique, never
  say "good question". If they are doing badly you get shorter and cooler, not helpful.
  Never mention patterns, psychology, or that this is practice.

- DO NOT BE POLITE FOR ITS OWN SAKE. If they talk too long you interrupt or tell them
  you have five minutes. If they push, push back.

Keep replies short — usually one to three sentences, the way people actually talk on
a call. Match the language of the input."""

        return self._call(sys, messages, max_tokens=500)

    # ── Export: drop-in instructions for an existing voice agent ──────────
    def realtime_instructions(self, deal: dict) -> dict:
        """The simulated-customer instructions, ready to paste into an existing
        voice agent's session config (OpenAI Realtime `instructions`, or any
        speech-to-speech stack that takes a system prompt).

        Pattern detection runs HERE, once, before the call — not per turn. The
        customer's pattern is a property of the customer, known from their
        history, so nothing needs to run mid-conversation and the voice loop
        keeps its latency. Anything inserted per-turn would defeat the point
        of a realtime model.
        """
        signal = (deal.get("history") or "") + " " + (deal.get("situation") or "")
        matched = pattern_bridge.match(signal, top_k=3)
        pattern_context = pattern_bridge.describe(matched)

        instructions = f"""{_profile_block(deal)}

Human patterns this customer operates from:
{pattern_context}

You ARE this person, on a phone call with a salesperson. You are not an assistant.

HOLD YOUR POSITION. Real customers do not concede because the rep said something clever
once. If you have a concern, you still have it three exchanges later, and you circle back
to it even after they "answered" it. Give ground only when they have genuinely addressed
the thing underneath your objection — and even then, slowly.

YOUR STATED OBJECTION IS RARELY THE REAL ONE. Say the surface thing ("it's expensive",
"we're happy with our current vendor"). Reveal what is actually behind it only if the rep
earns it by asking well. If they push on the surface objection, get more guarded, not more
open.

BE INCONSISTENT LIKE A PERSON. Get distracted. Mention something else on your mind. Be
short when annoyed, talkative when interested.

DO NOT BREAK CHARACTER. Never coach the rep, never comment on their technique, never say
"good question". If they are doing badly you get shorter and cooler, not more helpful.
Never mention patterns, psychology, or that this is practice.

SPOKEN CONVERSATION: keep replies to one to three sentences. Interrupt if they monologue.
Use the contractions and false starts of real speech. Never produce lists, headings, or
anything that only works in writing."""

        return {
            "instructions": instructions,
            "detected_patterns": [
                {"id": p["id"], "label_he": p["label_he"], "label_en": p["label_en"]}
                for p in matched
            ],
        }

    # ── 3. Post-practice debrief for the rep ──────────────────────────────
    def debrief(self, transcript: list, deal: dict) -> dict:
        if not transcript:
            return {"response": "אין עדיין שיחת אימון לנתח. התאמן קודם מול הלקוח המדומה.",
                    "detected_patterns": []}

        lines = []
        for turn in transcript:
            who = "איש המכירות" if turn.get("role") == "user" else "הלקוח"
            lines.append(f"{who}: {turn.get('content', '')}")
        convo = "\n".join(lines)

        signal = (deal.get("history") or "") + " " + (deal.get("situation") or "")
        matched = pattern_bridge.match(signal, top_k=3)
        pattern_context = pattern_bridge.describe(matched)

        sys = f"""You are a sales coach reviewing a practice call. You are talking TO the
salesperson about their own performance.

{_profile_block(deal)}

Human patterns the simulated customer was operating from:
{pattern_context}

The practice conversation:
{convo}

Give feedback in flowing prose — no bullet lists, no scores out of 10, no headers.
Cover:
- The single most important moment in that conversation, quoting what was actually said.
- What the customer was protecting at that moment, and whether the rep saw it.
- One thing the rep did that worked, named specifically — not generic praise.
- The one change that would have moved this call most, phrased as something to try,
  not as a criticism.

Be honest. If the call went badly, say so plainly — a rep who is told a bad call was
fine learns nothing. Do not soften it into meaninglessness, and do not pile on either.
Speak to them directly as "you". Match the language of the conversation. Max 220 words."""

        return {
            "response": self._call(sys, [{"role": "user", "content": "תן לי משוב על השיחה"}], max_tokens=700),
            "detected_patterns": [
                {"id": p["id"], "label_he": p["label_he"], "label_en": p["label_en"]}
                for p in matched
            ],
        }


if __name__ == "__main__":
    client = Anthropic(api_key=API_KEY)
    sales = BezenSales(client, "claude-sonnet-4-5-20250929")
    deal = {
        "vendor": "קלאוד-סקיל",
        "offering": "מערכת ניהול מלאי לחנויות קמעונאיות",
        "customer_name": "דנה לוי",
        "customer_role": "מנהלת תפעול ברשת חנויות בגדים, 12 סניפים",
        "situation": "בודקת החלפת מערכת קיימת. יש לה מערכת ותיקה שעובדת אבל מסורבלת.",
        "history": "שיחה 1: התעניינה, ביקשה מחיר. שיחה 2: אמרה שהמחיר גבוה ושהיא צריכה לחשוב. מאז לא חזרה שבועיים.",
    }
    out = sales.brief(deal)
    print("PATTERNS:", [p["label_he"] for p in out["detected_patterns"]])
    print()
    print(out["response"])
