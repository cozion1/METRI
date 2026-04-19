"""
BEZEN Arena Server — Unified entry for both agents.

Endpoints:
  GET  /                     → Demo page (HTML)
  GET  /health               → JSON health check
  GET  /agents               → List available agents

  POST /agent                → BEZEN-WORDSMITH (default, for backward compat)
  POST /agent/wordsmith      → BEZEN-WORDSMITH explicitly
  POST /agent/debate         → BEZEN-DEBATE explicitly

  POST /compare/wordsmith    → Plain Claude vs BEZEN-WORDSMITH (same prompt)
  POST /compare/debate       → Plain Claude vs BEZEN-DEBATE (same topic)

  GET  /test/wordsmith       → Quick test
  GET  /test/debate          → Quick test
"""

import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from dotenv import load_dotenv, dotenv_values

from bezen_wordsmith import BezenFlow as BezenWordsmith
from bezen_debate import BezenDebate

# ─────────────────────────────────────────
# Setup
# ─────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env", override=True)

API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not API_KEY:
    vals = dotenv_values(SCRIPT_DIR / ".env")
    API_KEY = (vals.get("ANTHROPIC_API_KEY") or "").strip()

if not API_KEY:
    raise SystemExit("ERROR: ANTHROPIC_API_KEY not configured")

MODEL = os.getenv("BEZEN_MODEL", "claude-sonnet-4-5-20250929")

app = Flask(__name__)
client = Anthropic(api_key=API_KEY)

wordsmith = BezenWordsmith(client, MODEL)
debate = BezenDebate(client, MODEL)


# ─────────────────────────────────────────
# Helper: Plain Claude (no BEZEN) for comparisons
# ─────────────────────────────────────────
def plain_claude(prompt: str, max_tokens: int = 600) -> str:
    """Call Claude directly with no BEZEN wrapper. The control group."""
    try:
        r = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.content[0].text.strip()
    except Exception as e:
        return f"[Plain Claude error: {e}]"


# ─────────────────────────────────────────
# Pages
# ─────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return render_template('demo.html')


@app.route('/compare', methods=['GET'])
def compare_page():
    return render_template('compare.html')


# ─────────────────────────────────────────
# Health & Discovery
# ─────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ready",
        "model": MODEL,
        "agents": ["wordsmith", "debate"],
        "version": "2.0",
    })


@app.route('/agents', methods=['GET'])
def list_agents():
    return jsonify({
        "wordsmith": {
            "category": "wordsmith",
            "description": "BEZEN FLOW for emotional/personal writing — 6-step balanced response engine",
            "endpoint": "/agent/wordsmith",
            "best_for": "Emotional support, personal advice, balanced writing"
        },
        "debate": {
            "category": "debate-lord",
            "description": "BEZEN DEBATE — structured 6-step calibrated argumentation engine",
            "endpoint": "/agent/debate",
            "best_for": "Controversial topics, policy debates, value-based disagreements"
        }
    })


# ─────────────────────────────────────────
# Wordsmith Agent
# ─────────────────────────────────────────
@app.route('/agent', methods=['POST'])
@app.route('/agent/wordsmith', methods=['POST'])
def agent_wordsmith():
    try:
        data = request.json or {}
        text = data.get('input') or data.get('prompt') or data.get('message', '')
        if not text:
            return jsonify({"error": "No input provided"}), 400
        return jsonify(wordsmith.respond(text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test/wordsmith', methods=['GET'])
def test_wordsmith():
    sample = "I'm scared AI will replace me at work. I have no chance. I'm useless."
    return jsonify({"sample_input": sample, "result": wordsmith.respond(sample)})


# ─────────────────────────────────────────
# Debate Agent
# ─────────────────────────────────────────
@app.route('/agent/debate', methods=['POST'])
def agent_debate():
    try:
        data = request.json or {}
        topic = data.get('input') or data.get('topic') or data.get('prompt', '')
        if not topic:
            return jsonify({"error": "No topic provided"}), 400
        return jsonify(debate.respond(topic))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test/debate', methods=['GET'])
def test_debate():
    sample = "Should AI tools be allowed in school exams?"
    return jsonify({"sample_topic": sample, "result": debate.respond(sample)})


# ─────────────────────────────────────────
# Comparison Endpoints (the killer demo)
# ─────────────────────────────────────────
@app.route('/compare/wordsmith', methods=['POST'])
def compare_wordsmith():
    try:
        data = request.json or {}
        text = data.get('input') or data.get('prompt', '')
        if not text:
            return jsonify({"error": "No input provided"}), 400

        plain = plain_claude(text)
        bezen = wordsmith.respond(text)

        return jsonify({
            "input": text,
            "plain_claude": plain,
            "bezen_wordsmith": bezen["response"],
            "bezen_trace": bezen["trace"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/compare/debate', methods=['POST'])
def compare_debate():
    try:
        data = request.json or {}
        topic = data.get('input') or data.get('topic', '')
        if not topic:
            return jsonify({"error": "No topic provided"}), 400

        plain = plain_claude(topic, max_tokens=800)
        bezen = debate.respond(topic)

        return jsonify({
            "topic": topic,
            "plain_claude": plain,
            "bezen_debate": bezen["response"],
            "bezen_trace": bezen["trace"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 7860))
    print("=" * 65)
    print(" BEZEN ARENA SERVER — Unified")
    print("=" * 65)
    print(f"  Demo:        http://localhost:{PORT}/")
    print(f"  Compare:     http://localhost:{PORT}/compare")
    print(f"  Health:      http://localhost:{PORT}/health")
    print(f"  Agents:      http://localhost:{PORT}/agents")
    print()
    print("  Wordsmith:   POST http://localhost:{PORT}/agent/wordsmith")
    print("  Debate:      POST http://localhost:{PORT}/agent/debate")
    print()
    print(f"  Compare WS:  POST http://localhost:{PORT}/compare/wordsmith")
    print(f"  Compare DB:  POST http://localhost:{PORT}/compare/debate")
    print("=" * 65)
    app.run(host='0.0.0.0', port=PORT, debug=False)
