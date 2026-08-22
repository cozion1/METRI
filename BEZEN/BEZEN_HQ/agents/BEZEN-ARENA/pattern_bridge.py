"""
Pattern Bridge — connects the 499 human-pattern library to agent-to-agent interaction.

Given one agent's text (an argument, a stance, a rebuttal), finds which human
patterns it exhibits (defensiveness, comparison, self-doubt, a named strength, etc.)
so another agent can respond to the pattern, not just the literal words.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PATTERNS_PATH = SCRIPT_DIR.parents[3] / "data" / "bezen_patterns.json"

_CACHE = None


def load_patterns() -> list:
    global _CACHE
    if _CACHE is None:
        with open(PATTERNS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _CACHE = data["patterns"]
    return _CACHE


def _tokens(pattern: dict) -> list:
    """Words to match against, pulled from tags + both labels."""
    words = []
    words += pattern.get("tags", [])
    words += pattern.get("label_he", "").split()
    words += pattern.get("label_en", "").lower().split()
    return [w.strip(",.!?\"'") for w in words if len(w.strip(",.!?\"'")) > 2]


def match(text: str, top_k: int = 3) -> list:
    """Score every pattern by keyword overlap with `text`. Cheap, dependency-free.

    Not semantic search — a real integration would embed patterns once and use
    vector similarity. This is enough to prove the concept: agents can recognize
    a human pattern in another agent's output instead of treating it as bare text.
    """
    text_low = text.lower()
    scored = []
    for p in load_patterns():
        score = sum(1 for w in _tokens(p) if w.lower() in text_low)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda sp: sp[0], reverse=True)
    return [p for _, p in scored[:top_k]]


def describe(patterns: list) -> str:
    """Render matched patterns as compact context for an LLM prompt."""
    if not patterns:
        return "No specific human pattern detected — respond on content alone."
    lines = []
    for p in patterns:
        lines.append(
            f"- {p['label_he']} ({p['label_en']}): {p['short_description']} "
            f"| balanced trait: {p.get('balanced_trait_id', '-')} "
            f"| bridge: {p['bridge_sentences'][0] if p.get('bridge_sentences') else '-'}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    sample = "אני חושב שהעמדה שלך פשוט מגוחכת, כל אחד שמבין בזה יודע שאתה טועה."
    hits = match(sample)
    print(describe(hits))
