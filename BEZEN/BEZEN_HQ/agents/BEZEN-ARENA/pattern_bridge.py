"""
Pattern Bridge — connects the human-pattern library to agent interaction.

Given a person's (or another agent's) text, finds which human patterns it
exhibits — defensiveness, comparison, self-doubt, a named strength — so the
responding agent can answer the pattern, not just the literal words.

Matching is lexical, not semantic. That is a deliberate tradeoff: it runs in
microseconds with no API call and no model, which is what makes it usable in a
live support loop. It is also why precision matters more than recall here —
a wrong pattern actively misleads the agent, while no pattern just means it
answers on content alone. So this scores conservatively and returns nothing
rather than guessing.

A semantic version (embed every pattern once, cosine-match at runtime) would
recall far more; it belongs behind the same match() signature when it is worth
the added dependency.
"""

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PATTERNS_PATH = SCRIPT_DIR.parents[3] / "data" / "bezen_patterns.json"

_CACHE = None
_INDEX = None

# Minimum score before a pattern is considered a real hit rather than noise.
MIN_SCORE = 2.0

# Hebrew glues prefixes onto words (ב/ל/מ/ה/ש/ו/כ), so "מהבית" and "בית" are
# the same lexical item. Stripping them raises recall, but on its own it also
# raises false positives — which is why single generic words score low and a
# hit needs corroboration to clear MIN_SCORE.
_HE_PREFIXES = ("מה", "שה", "וה", "כש", "לכ", "מ", "ב", "ל", "ה", "ש", "ו", "כ")

# Words too common to carry signal on their own.
_STOPWORDS = {
    "את", "של", "לא", "אני", "אתה", "היא", "הוא", "זה", "זו", "יש", "אין",
    "עם", "על", "כל", "רק", "גם", "אבל", "כי", "מה", "מי", "איך", "למה",
    "the", "and", "for", "with", "that", "this", "you", "not", "are", "was",
    "have", "has", "but", "all", "can", "will", "would", "about", "from",
}


def load_patterns() -> list:
    global _CACHE
    if _CACHE is None:
        with open(PATTERNS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _CACHE = [p for p in data["patterns"] if p.get("active", True)]
    return _CACHE


def _forms(word: str) -> set:
    """The word itself plus its prefix-stripped variant, if plausible.

    Both are kept, never just the stripped one: those prefix letters are also
    ordinary root letters, so blind stripping mangles real words — הורס→ורס,
    שייכות→ייכות, בסיס→סיס. Keeping both means a genuine match still lands
    while the word survives intact.
    """
    w = word.lower().strip(",.!?\"'()[]{}:;־–—…")
    if len(w) < 3 or w in _STOPWORDS:
        return set()

    out = {w}
    for pref in _HE_PREFIXES:
        if w.startswith(pref) and len(w) - len(pref) >= 3:
            stripped = w[len(pref):]
            if stripped not in _STOPWORDS:
                out.add(stripped)
            break
    return out


def _words(text: str) -> set:
    """Content-word forms in `text`. Punctuation and stopwords dropped."""
    raw = re.split(r"[\s,.!?\"'()\[\]{}:;־–—]+", text.lower())
    out = set()
    for w in raw:
        out |= _forms(w)
    return out


def _build_index() -> list:
    """Precompute the matchable signals for every pattern, once."""
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    _INDEX = []
    for p in load_patterns():
        tags = [t for t in p.get("tags", []) if t]
        # Multi-word tags are strong signal; single words are weak on their own.
        phrase_tags = [t.lower() for t in tags if len(t.split()) > 1]
        word_tags = set()
        for t in tags:
            if len(t.split()) == 1:
                word_tags |= _forms(t)

        examples = [_words(ex) for ex in p.get("example_inputs", []) if ex]
        label_words = _words(p.get("label_he", "")) | _words(p.get("label_en", ""))

        _INDEX.append({
            "pattern": p,
            "phrase_tags": phrase_tags,
            "word_tags": word_tags,
            "examples": [e for e in examples if e],
            "label_words": label_words,
        })
    return _INDEX


def _score(entry: dict, text_low: str, text_words: set) -> float:
    """Weighted score. Phrases and example overlap dominate; labels barely count."""
    score = 0.0

    # A multi-word tag appearing verbatim is the strongest available signal.
    for phrase in entry["phrase_tags"]:
        if phrase in text_low:
            score += 3.0

    # Single-word tag hits: real signal, but one alone stays under MIN_SCORE.
    score += 1.0 * len(entry["word_tags"] & text_words)

    # Overlap with a known real phrasing of this pattern, scaled by how much of
    # that example is present — catches paraphrases the tags miss. Examples of
    # one or two words are excluded: sharing their only word scores a perfect
    # ratio on what is really a single generic word ("בית" alone matched
    # "working from home"), which is exactly the false positive to avoid.
    best_example = 0.0
    for ex in entry["examples"]:
        if len(ex) < 3:
            continue
        shared = len(ex & text_words)
        if shared >= 2:
            best_example = max(best_example, 3.0 * (shared / len(ex)))
    score += best_example

    # Label words are the weakest evidence — they are naming vocabulary, not
    # how a person actually writes.
    score += 0.4 * len(entry["label_words"] & text_words)

    return score


def match(text: str, top_k: int = 3, min_score: float = MIN_SCORE) -> list:
    """Return up to `top_k` patterns present in `text`, best first.

    Returns [] when nothing clears `min_score` — an empty result means "answer
    on content alone", which is correct far more often than a wrong pattern.
    """
    if not text or not text.strip():
        return []

    text_low = text.lower()
    text_words = _words(text)
    if not text_words:
        return []

    scored = []
    for entry in _build_index():
        s = _score(entry, text_low, text_words)
        if s >= min_score:
            scored.append((s, entry["pattern"]))

    scored.sort(key=lambda sp: sp[0], reverse=True)
    return [p for _, p in scored[:top_k]]


def match_scored(text: str, top_k: int = 3, min_score: float = MIN_SCORE) -> list:
    """Same as match(), but returns (score, pattern) — useful for tuning."""
    if not text or not text.strip():
        return []
    text_low = text.lower()
    text_words = _words(text)
    if not text_words:
        return []
    scored = [
        (s, e["pattern"])
        for e in _build_index()
        if (s := _score(e, text_low, text_words)) >= min_score
    ]
    scored.sort(key=lambda sp: sp[0], reverse=True)
    return scored[:top_k]


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
    samples = [
        "אני חושב שהעמדה שלך פשוט מגוחכת, כל אחד שמבין בזה יודע שאתה טועה.",
        "האינטרנט נופל כל ערב ואני עובד מהבית, זה הורס לי את הפרנסה",
        "אני רוצה לבטל, נמאס לי מכם",
        "כולם מסביבי מצליחים ואני נשאר מאחור",
    ]
    for s in samples:
        print(f"\n> {s}")
        for score, p in match_scored(s):
            print(f"   {score:.1f}  {p['label_he']}")
        if not match_scored(s):
            print("   (no pattern — answer on content)")
