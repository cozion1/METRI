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

import json
import os
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from dotenv import load_dotenv, dotenv_values

from bezen_wordsmith import BezenFlow as BezenWordsmith
from bezen_debate import BezenDebate
from bezen_support import BezenSupport
from bezen_sales import BezenSales
from bezen_groening import BezenGroening

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
support = BezenSupport(client, MODEL)
sales = BezenSales(client, MODEL)
groening = BezenGroening(client, MODEL)


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


def agent_reply(system: str, message: str, max_tokens: int = 600) -> str:
    """Call Claude with an arbitrary system prompt — used to run a visitor's
    OWN agent persona, with and without the BEZEN layer added on top."""
    try:
        r = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": message}]
        )
        return r.content[0].text.strip()
    except Exception as e:
        return f"[Agent error: {e}]"


# The generalized BEZEN response layer — added on top of ANY existing agent
# persona, so a visitor can test the effect on their own agent's system
# prompt instead of only BEZEN's built-in demo personas.
BEZEN_LAYER = """
In addition to the role described above, apply these BEZEN response principles:
1. Before any advice, include ONE small question that gives the person back a sliver of agency — a tiny anchor, not a big open question.
2. If the user states something in extreme or absolute terms ("no one", "always", "useless"), gently reframe it as a balanced, honest middle ground. Not toxic positivity, not denial.
3. End with exactly ONE small concrete action (2-10 minutes) — never a list, never a multi-step plan.
4. Never produce a bulleted list of tips or options. One clear, calibrated voice, not a menu.
5. Keep your original persona and expertise intact — these are response-shaping principles layered on top of it, not a replacement for who you are.
Match the language of the user's message. No headers or labels in your reply.
"""


# ─────────────────────────────────────────
# Pages
# ─────────────────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return render_template('demo.html')


@app.route('/compare', methods=['GET'])
def compare_page():
    return render_template('compare.html')


@app.route('/support', methods=['GET'])
def support_page():
    return render_template('support.html')


@app.route('/sales', methods=['GET'])
def sales_page():
    return render_template('sales.html')


CONFIG_DIR = SCRIPT_DIR / "configs"
_SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@app.route('/groening', methods=['GET'])
def groening_page():
    """Bruno Gröning teaching agent — under review by the Circle of Friends."""
    return render_template('groening.html')


# Five plain links are easier to hand out than language codes — nobody has to be
# told what /de means, and nobody mistypes it. /groening/box/<lang> still works.
BOX_BY_NUMBER = {2: 'en', 3: 'de', 4: 'ru', 5: 'ar'}


@app.route('/groening/box<int:num>', methods=['GET'])
def groening_box_numbered(num):
    from flask import abort
    if num not in BOX_BY_NUMBER:
        abort(404, 'no box with that number')
    return groening_box(BOX_BY_NUMBER[num])


@app.route('/groening/box', methods=['GET'])
@app.route('/groening/box/<lang>', methods=['GET'])
def groening_box(lang='he'):
    """The closed box: one self-contained file per language, needing no server and
    no API once downloaded — which is the point, since it is meant to reach places
    with neither reliable internet nor a way to pay. Built by build_closed_box.py."""
    from flask import send_file, abort
    if lang not in ('he', 'en', 'de', 'ru', 'ar'):
        abort(404, 'no box in that language yet')
    name = 'groening-closed-box.html' if lang == 'he' else f'groening-closed-box-{lang}.html'
    f = SCRIPT_DIR / 'static' / name
    if not f.exists():
        abort(404, 'not built yet — run build_closed_box.py')
    return send_file(f, mimetype='text/html')


@app.route('/config/<slug>', methods=['GET'])
def get_config(slug):
    """Load a named client config so a prospect gets /support?c=almaya rather
    than their entire business config base64'd into a 1,800-character URL."""
    if not _SLUG_OK.match(slug or ""):
        return jsonify({"error": "bad config name"}), 400

    path = (CONFIG_DIR / f"{slug}.json").resolve()
    try:
        path.relative_to(CONFIG_DIR.resolve())
    except ValueError:
        return jsonify({"error": "bad config name"}), 400

    if not path.is_file():
        return jsonify({"error": "not found"}), 404

    try:
        with open(path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
# Agent-to-Agent Pattern Recognition (POC)
# ─────────────────────────────────────────
@app.route('/agent/debate/vs_agent', methods=['POST'])
def agent_debate_vs_agent():
    try:
        data = request.json or {}
        topic = data.get('topic', '')
        opponent_text = data.get('opponent_text', '')
        if not opponent_text:
            return jsonify({"error": "No opponent_text provided"}), 400
        return jsonify(debate.respond_to_agent(topic, opponent_text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test/debate/vs_agent', methods=['GET'])
def test_debate_vs_agent():
    sample_topic = "Should AI tools be allowed in school exams?"
    sample_opponent = "Obviously banning AI is the only serious position — anyone who disagrees just doesn't understand how exams work."
    return jsonify({
        "sample_topic": sample_topic,
        "sample_opponent_text": sample_opponent,
        "result": debate.respond_to_agent(sample_topic, sample_opponent),
    })


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

        with ThreadPoolExecutor(max_workers=2) as pool:
            plain_future = pool.submit(plain_claude, text)
            bezen_future = pool.submit(wordsmith.respond, text)
            plain = plain_future.result()
            bezen = bezen_future.result()

        return jsonify({
            "input": text,
            "plain_claude": plain,
            "bezen_wordsmith": bezen["response"],
            "bezen_trace": bezen["trace"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/agent/support', methods=['POST'])
def agent_support():
    """Live multi-turn customer service agent with the BEZEN layer.

    Body: {message, history: [{role, content}], business: {name, domain, policies, escalation}}
    Unlike the one-shot compare demo, this holds a real conversation.
    """
    try:
        data = request.json or {}
        message = (data.get('message') or data.get('input') or '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        history = data.get('history') or []
        business = data.get('business') or {}

        result = support.respond(message, history=history, business=business)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/agent/groening', methods=['POST'])
def agent_groening():
    """Q&A on the teaching of Bruno Gröning, grounded in the movement's own site.

    Body: {message, history: [{role, content}]}
    Returns the reply plus the official sources it drew on and one presentation
    to watch next — the sources are shown to the user so any quote can be checked
    against the page it came from.
    """
    try:
        data = request.json or {}
        message = (data.get('message') or data.get('input') or '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400
        result = groening.respond(message, history=data.get('history') or [])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/groening/stats', methods=['GET'])
def groening_stats():
    import groening_corpus
    return jsonify(groening_corpus.stats())


@app.route('/sales/brief', methods=['POST'])
def sales_brief():
    """Pre-call briefing on a customer, with and without the pattern read."""
    try:
        data = request.json or {}
        deal = data.get('deal') or {}
        if not any((deal.get('customer_name'), deal.get('situation'), deal.get('history'))):
            return jsonify({"error": "No customer details provided"}), 400

        if data.get('compare'):
            with ThreadPoolExecutor(max_workers=2) as pool:
                plain_future = pool.submit(sales.brief, deal, False)
                bezen_future = pool.submit(sales.brief, deal, True)
                plain = plain_future.result()
                bezen = bezen_future.result()
            return jsonify({
                "plain": plain["response"],
                "bezen": bezen["response"],
                "detected_patterns": bezen["detected_patterns"],
            })

        out = sales.brief(deal, use_bezen=True)
        return jsonify({"bezen": out["response"], "detected_patterns": out["detected_patterns"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/sales/roleplay', methods=['POST'])
def sales_roleplay():
    """One turn of the simulated customer the rep practises against."""
    try:
        data = request.json or {}
        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        deal = data.get('deal') or {}
        history = data.get('history') or []

        if data.get('compare'):
            with ThreadPoolExecutor(max_workers=2) as pool:
                plain_future = pool.submit(sales.roleplay, message, history, deal, False)
                bezen_future = pool.submit(sales.roleplay, message, history, deal, True)
                plain = plain_future.result()
                bezen = bezen_future.result()
            return jsonify({"plain": plain, "bezen": bezen})

        return jsonify({"bezen": sales.roleplay(message, history, deal, True)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/sales/debrief', methods=['POST'])
def sales_debrief():
    """Coach the rep on the practice call they just had."""
    try:
        data = request.json or {}
        out = sales.debrief(data.get('transcript') or [], data.get('deal') or {})
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/sales/instructions', methods=['POST'])
def sales_instructions():
    """Export the simulated-customer prompt for an existing voice agent."""
    try:
        data = request.json or {}
        return jsonify(sales.realtime_instructions(data.get('deal') or {}))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/compare/support', methods=['POST'])
def compare_support():
    """Same customer-service agent, with and without the BEZEN layer."""
    try:
        data = request.json or {}
        message = (data.get('message') or data.get('input') or '').strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        history = data.get('history') or []
        business = data.get('business') or {}

        with ThreadPoolExecutor(max_workers=2) as pool:
            plain_future = pool.submit(support.plain_reply, message, history, business)
            bezen_future = pool.submit(support.respond, message, history, business)
            plain = plain_future.result()
            bezen = bezen_future.result()

        return jsonify({
            "message": message,
            "plain_claude": plain,
            "bezen_support": bezen["response"],
            "detected_patterns": bezen["detected_patterns"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/compare/custom', methods=['POST'])
def compare_custom():
    """Run a VISITOR's OWN agent persona — with and without the BEZEN layer —
    on the same test message, so a prospect can see the effect on their own
    agent instead of only BEZEN's built-in demo personas."""
    try:
        data = request.json or {}
        persona = (data.get('persona') or '').strip()
        message = (data.get('message') or data.get('input') or '').strip()
        if not persona:
            return jsonify({"error": "No agent persona/prompt provided"}), 400
        if not message:
            return jsonify({"error": "No test message provided"}), 400

        with ThreadPoolExecutor(max_workers=2) as pool:
            plain_future = pool.submit(agent_reply, persona, message)
            bezen_future = pool.submit(agent_reply, persona + "\n\n" + BEZEN_LAYER, message)
            plain = plain_future.result()
            bezen = bezen_future.result()

        return jsonify({
            "persona": persona,
            "message": message,
            "plain_claude": plain,
            "bezen_custom": bezen,
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

        with ThreadPoolExecutor(max_workers=2) as pool:
            plain_future = pool.submit(plain_claude, topic, 800)
            bezen_future = pool.submit(debate.respond, topic)
            plain = plain_future.result()
            bezen = bezen_future.result()

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
