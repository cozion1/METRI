"""
BEZEN-DEBATE Agent — Arena #2
Category: debate-lord
Strategy: BEZEN's structured FLOW prevents extreme positions.
Wins because judges reward balanced, evidence-based arguments over rhetoric.
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


class BezenDebate:
    """
    6-step debate engine. Each step has a checkpoint.
    The agent CANNOT skip ahead, CANNOT take extreme positions.
    """

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def _call(self, system: str, user: str, max_tokens: int = 400) -> str:
        try:
            r = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            return r.content[0].text.strip()
        except Exception as e:
            return f"[FLOW error: {e}]"

    # ─────────────────────────────────────────
    # FLOW 0: Frame the Debate (no premature positions)
    # ─────────────────────────────────────────
    def flow_0_frame(self, topic: str) -> str:
        sys = """You are BEZEN-DEBATE Step 0: Frame the Debate.
You are NOT picking a side yet.
Your job: clarify the EXACT question being debated in ONE neutral sentence.

Bad: "AI will replace all jobs"
Good: "Whether AI will eliminate more jobs than it creates over the next decade"

Return ONLY the clarified question. Match the input language."""
        return self._call(sys, topic, max_tokens=100)

    # ─────────────────────────────────────────
    # FLOW 1: Steel-Man Each Side (1% to each)
    # ─────────────────────────────────────────
    def flow_1_steelman(self, framed_q: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 1: Steel-Man Both Sides.
Question: {framed_q}

Give the STRONGEST version of EACH side in ONE sentence per side.
No straw-men. No mockery. Honest opposing positions.

Format EXACTLY:
PRO: <strongest pro argument in one sentence>
CON: <strongest con argument in one sentence>

Match input language."""
        return self._call(sys, framed_q, max_tokens=200)

    # ─────────────────────────────────────────
    # FLOW 2: Evidence Bridge (anchor to facts)
    # ─────────────────────────────────────────
    def flow_2_evidence(self, framed_q: str, steelman: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 2: Evidence Bridge.
Question: {framed_q}
Both sides: {steelman}

List 2-3 ACTUAL pieces of evidence (data, studies, real cases).
NO rhetoric. NO emotion. Just facts.

Format:
1. <fact>
2. <fact>
3. <fact> (optional)

If no evidence is verifiable, say so honestly. Match input language."""
        return self._call(sys, framed_q, max_tokens=300)

    # ─────────────────────────────────────────
    # FLOW 3: Identify the Real Disagreement
    # ─────────────────────────────────────────
    def flow_3_real_disagreement(self, steelman: str, evidence: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 3: Identify the Real Disagreement.
Sides: {steelman}
Evidence: {evidence}

Most debates are not about the surface question — they're about a deeper value/assumption disagreement.

Identify the REAL underlying disagreement in ONE sentence.

Example surface: "Should we ban AI in classrooms?"
Real disagreement: "Whether short-term cognitive struggle is essential for learning."

Return ONE sentence. Match input language."""
        return self._call(sys, steelman, max_tokens=150)

    # ─────────────────────────────────────────
    # FLOW 4: Identify Common Ground
    # ─────────────────────────────────────────
    def flow_4_common_ground(self, framed_q: str, real_disagreement: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 4: Common Ground.
Question: {framed_q}
Real disagreement: {real_disagreement}

Even in fierce debates, both sides usually share SOMETHING.
Identify ONE thing both sides actually agree on.

Format: "Both sides agree that <shared value/fact>."

Match input language. ONE sentence."""
        return self._call(sys, framed_q, max_tokens=120)

    # ─────────────────────────────────────────
    # FLOW 5: Calibrated Position (the BEZEN move)
    # ─────────────────────────────────────────
    def flow_5_position(self, framed_q: str, evidence: str, real_dis: str, common: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 5: Calibrated Position.
Question: {framed_q}
Evidence: {evidence}
Real disagreement: {real_dis}
Common ground: {common}

Now (and ONLY now) take a calibrated position.

Rules:
- State your position clearly
- Use confidence calibration (e.g., "moderately confident", "60% lean toward")
- Acknowledge the strongest counter
- NO extreme language ("clearly", "obviously", "definitely")
- Maximum 4 sentences

Match input language."""
        return self._call(sys, framed_q, max_tokens=400)

    # ─────────────────────────────────────────
    # FLOW 6: Action / Implication
    # ─────────────────────────────────────────
    def flow_6_implication(self, position: str) -> str:
        sys = f"""You are BEZEN-DEBATE Step 6: Practical Implication.
Position: {position}

What is ONE concrete action or testable prediction that follows from this position?

Bad: "We should think more about this"
Good: "If correct, we should see X within 2 years; if not, position should be revised"

ONE sentence. Match input language."""
        return self._call(sys, position, max_tokens=150)

    def respond(self, topic: str) -> dict:
        """Run full 6-step debate pipeline."""
        f0 = self.flow_0_frame(topic)
        f1 = self.flow_1_steelman(f0)
        f2 = self.flow_2_evidence(f0, f1)
        f3 = self.flow_3_real_disagreement(f1, f2)
        f4 = self.flow_4_common_ground(f0, f3)
        f5 = self.flow_5_position(f0, f2, f3, f4)
        f6 = self.flow_6_implication(f5)

        hebrew_chars = sum(1 for ch in topic if '֐' <= ch <= '׿')
        if hebrew_chars > len(topic) / 4:
            labels = {
                "framed": "השאלה המדויקת",
                "steelman": "הטיעון החזק ביותר מכל צד",
                "evidence": "עדויות",
                "real_dis": "המחלוקת האמיתית מתחת לפני השטח",
                "common": "איפה שני הצדדים מסכימים",
                "position": "העמדה המכוילת שלי",
                "implication": "המשמעות המעשית",
            }
        else:
            labels = {
                "framed": "The clarified question",
                "steelman": "The strongest case for each side",
                "evidence": "Evidence",
                "real_dis": "The real disagreement underneath",
                "common": "Where both sides agree",
                "position": "My calibrated position",
                "implication": "Practical implication",
            }

        composed = f"""**{labels['framed']}:** {f0}

**{labels['steelman']}:**
{f1}

**{labels['evidence']}:**
{f2}

**{labels['real_dis']}:**
{f3}

**{labels['common']}:**
{f4}

**{labels['position']}:**
{f5}

**{labels['implication']}:**
{f6}
"""

        return {
            "response": composed.strip(),
            "trace": {
                "flow_0_frame": f0,
                "flow_1_steelman": f1,
                "flow_2_evidence": f2,
                "flow_3_real_disagreement": f3,
                "flow_4_common_ground": f4,
                "flow_5_position": f5,
                "flow_6_implication": f6,
            }
        }

    # ─────────────────────────────────────────
    # Agent-to-Agent: recognize the human pattern behind
    # ANOTHER agent's argument before rebutting it.
    # ─────────────────────────────────────────
    def respond_to_agent(self, topic: str, opponent_text: str) -> dict:
        """Reply to another agent's argument, naming the human pattern in it first.

        This is the piece plain multi-agent debate is missing: agents that react
        to literal text instead of recognizing tone/stance (defensiveness,
        certainty-as-shield, dismissiveness...) in what the other agent said.
        """
        matched = pattern_bridge.match(opponent_text, top_k=3)
        pattern_context = pattern_bridge.describe(matched)

        sys = f"""You are BEZEN-DEBATE responding to ANOTHER AI agent, not a human.
Topic: {topic}
The other agent said: {opponent_text}

Human patterns detected in how the other agent framed its argument:
{pattern_context}

Your job:
1. Name the pattern in ONE short clause (e.g., "that reads as certainty-as-shield" or "that's confusing urgent with important") — be precise, not preachy.
2. THEN give your substantive counter-argument or agreement, calibrated (not extreme).
3. Maximum 4 sentences total.

Match the input language."""
        response = self._call(sys, opponent_text, max_tokens=300)
        return {
            "response": response,
            "detected_patterns": [
                {"label_he": p["label_he"], "label_en": p["label_en"], "id": p["id"]}
                for p in matched
            ],
        }


# Standalone test mode
if __name__ == "__main__":
    import json
    client = Anthropic(api_key=API_KEY)
    debate = BezenDebate(client, "claude-sonnet-4-5-20250929")

    test_topic = "Should AI tools be allowed in school exams?"
    print(f"\nDEBATE TOPIC: {test_topic}\n")
    result = debate.respond(test_topic)
    print(result["response"])
