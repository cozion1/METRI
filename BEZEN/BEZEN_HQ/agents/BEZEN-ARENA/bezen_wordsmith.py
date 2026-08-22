"""
BEZEN-WORDSMITH Agent — Arena #1
Category: wordsmith (writing)
Strategy: FLOW 0-6 produces structured, balanced, actionable text
"""

import os
import json
from pathlib import Path
from anthropic import Anthropic
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Load .env from script directory explicitly
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env", override=True)

# Force reload from file directly if env var loading failed
API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not API_KEY:
    from dotenv import dotenv_values
    vals = dotenv_values(SCRIPT_DIR / ".env")
    API_KEY = (vals.get("ANTHROPIC_API_KEY") or "").strip()
if not API_KEY:
    raise SystemExit(f"ERROR: ANTHROPIC_API_KEY not found in {SCRIPT_DIR}/.env")

# ─────────────────────────────────────────
# Setup
# ─────────────────────────────────────────
app = Flask(__name__)
client = Anthropic(api_key=API_KEY)
MODEL = "claude-sonnet-4-5-20250929"  # Using stable, high-quality model


# ─────────────────────────────────────────
# BEZEN FLOW Engine
# ─────────────────────────────────────────
class BezenFlow:
    """Structured 6-step pipeline that wraps any LLM."""

    def __init__(self, client, model):
        self.client = client
        self.model = model

    def _call(self, system: str, user: str, max_tokens: int = 500) -> str:
        """Single LLM call with strict system prompt."""
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            return resp.content[0].text.strip()
        except Exception as e:
            return f"[FLOW error: {str(e)}]"

    def flow_0_opening(self, user_input: str) -> str:
        sys = """You are BEZEN FLOW Step 0: Quiet Opening.
Acknowledge the user in ONE short sentence (max 12 words).
DO NOT solve. DO NOT advise. DO NOT explain.
Examples: "I hear you." | "Let's pause here together." | "Noted — let's go slow."
Return ONLY the acknowledgment sentence."""
        return self._call(sys, user_input, max_tokens=100)

    def flow_1_pain(self, user_input: str) -> str:
        sys = """You are BEZEN FLOW Step 1: Pain Detection.
Identify the SINGLE most important issue in the user's message.
Return it as ONE crystallized sentence in quotes.
If no clear emotional/pain content, summarize the topic in one sentence."""
        return self._call(sys, user_input, max_tokens=200)

    def flow_2_bridge(self, pain: str) -> str:
        sys = f"""You are BEZEN FLOW Step 2: Bridge (1% Control).
The core issue: {pain}

Ask ONE question that restores 1% of the user's agency.
NOT a solution. NOT a big question. A tiny anchor.

Examples:
- "What is one thing you noticed today that others missed?"
- "Where in this situation do you still have a small choice?"
- "What is the smallest part of this you can name precisely?"

Return ONLY the question (max 20 words)."""
        return self._call(sys, pain, max_tokens=150)

    def flow_3_transform(self, pain: str) -> str:
        sys = f"""You are BEZEN FLOW Step 3: Transform Extreme to Balanced.
Take this statement: {pain}

Rewrite it as a BALANCED, realistic alternative.
NOT a positive lie. NOT denial. A truthful middle ground.

Examples:
"I am useless" → "I do not yet know my new role"
"Nothing works" → "This particular path is currently blocked"
"I'm a failure" → "This attempt did not give the result I hoped"

Return ONLY the rewritten sentence."""
        return self._call(sys, pain, max_tokens=150)

    def flow_4_trait(self, balanced: str) -> str:
        sys = f"""You are BEZEN FLOW Step 4: Name the Self-Regulatory Trait.
Based on this balanced statement: {balanced}

Name ONE trait the person is exercising right now.
Examples: "honest self-assessment", "patience", "boundary awareness", "intellectual humility"

Format your response EXACTLY like this (no headers, no markdown):
**TraitName** — One sentence explanation.

Example: **Adaptive awareness** — Recognizing change while staying engaged with it.

Keep total response under 20 words. Use the language of the input."""
        return self._call(sys, balanced, max_tokens=120)

    def flow_5_action(self, trait: str, balanced: str) -> str:
        sys = f"""You are BEZEN FLOW Step 5: Micro-Action.
Trait: {trait}
Reality: {balanced}

Suggest ONE micro-action taking 2-10 minutes maximum.
NOT a plan. NOT multiple steps. ONE concrete thing.

Bad: "Build a portfolio over the next month"
Good: "Open ChatGPT for 5 minutes, ask one question about your field"

Return ONLY the action (max 25 words)."""
        return self._call(sys, balanced, max_tokens=150)

    def respond(self, user_input: str) -> dict:
        """Run full 6-step pipeline and compose final response."""
        f0 = self.flow_0_opening(user_input)
        f1 = self.flow_1_pain(user_input)
        f2 = self.flow_2_bridge(f1)
        f3 = self.flow_3_transform(f1)
        f4 = self.flow_4_trait(f3)
        f5 = self.flow_5_action(f4, f3)

        # Compose final wordsmith-quality response, labels matched to input language
        hebrew_chars = sum(1 for ch in user_input if '֐' <= ch <= '׿')
        if hebrew_chars > len(user_input) / 4:
            labels = {
                "core": "הליבה",
                "question": "כיוון למחשבה (חלק מההדגמה, לא שאלה שצריך לענות עליה כאן)",
                "balanced": "ניסוח מאוזן יותר",
                "trait": "מה זה מראה עליך",
                "action": "צעד קטן אחד (2-10 דקות)",
            }
        else:
            labels = {
                "core": "The core",
                "question": "A direction to consider (part of the demo, not a question to answer here)",
                "balanced": "A more balanced framing",
                "trait": "What this shows about you",
                "action": "One small step (2-10 minutes)",
            }

        composed = f"""{f0}

{labels['core']}: {f1}

{labels['question']}: {f2}

{labels['balanced']}: {f3}

{labels['trait']}: {f4}

{labels['action']}: {f5}
"""

        return {
            "response": composed.strip(),
            "trace": {
                "flow_0_opening": f0,
                "flow_1_pain": f1,
                "flow_2_bridge": f2,
                "flow_3_transform": f3,
                "flow_4_trait": f4,
                "flow_5_action": f5,
            }
        }


# ─────────────────────────────────────────
# Initialize
# ─────────────────────────────────────────
bezen = BezenFlow(client, MODEL)


# ─────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    """Landing page - serves the demo."""
    return render_template('demo.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "agent": "BEZEN-WORDSMITH",
        "version": "1.0",
        "category": "wordsmith",
        "model": MODEL,
        "status": "ready",
        "engine": "BEZEN FLOW 0-6"
    })


@app.route('/agent', methods=['POST'])
def agent():
    """Main endpoint for arena calls."""
    try:
        data = request.json or {}
        user_input = data.get('input') or data.get('prompt') or data.get('message', '')

        if not user_input:
            return jsonify({"error": "No input provided"}), 400

        result = bezen.respond(user_input)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test', methods=['GET'])
def test():
    """Quick test endpoint."""
    sample = "I'm scared AI will replace me at work. I have no chance. I'm useless."
    result = bezen.respond(sample)
    return jsonify({
        "test_input": sample,
        "result": result
    })


# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("BEZEN-WORDSMITH Agent")
    print("=" * 60)
    print(f"Model: {MODEL}")
    PORT = int(os.getenv("PORT", 7860))
    print(f"Demo:     http://localhost:{PORT}/")
    print(f"API:      http://localhost:{PORT}/agent")
    print(f"Health:   http://localhost:{PORT}/health")
    print(f"Test:     http://localhost:{PORT}/test")
    print("=" * 60)
    app.run(host='0.0.0.0', port=PORT, debug=False)
