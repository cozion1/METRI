"""
Retrieval over the Bruno Gröning corpus.

Local keyword retrieval, no embeddings and no API call — same reasoning as
pattern_bridge: this runs on every turn of a live conversation, so it has to be
instant. A semantic version behind the same search() signature is the upgrade.

Two sources, deliberately kept apart because they carry different authority:

  data/groening_official/  — scraped from bruno-groening.org (the movement's own
                             site). Every chunk keeps its URL. This is what the
                             agent is allowed to quote.
  data/groening_corpus/    — Cozio's own 49-video archive, 52 topics of slides.
                             Useful for finding the right topic, but it is his
                             edit, not an authorized text. Marked as such, ranked
                             below official, and never presented as a quotation.

That distinction is the whole point: an agent that misattributes a sentence to
Bruno Gröning and then repeats it in 100 countries does damage that cannot be
walked back.
"""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parents[3] / "data"
OFFICIAL_DIR = DATA_DIR / "groening_official"
ARCHIVE_DIR = DATA_DIR / "groening_corpus"

MIN_SCORE = 1.5
MAX_CHUNK = 1100          # characters — roughly one idea
MIN_CHUNK = 120

_CHUNKS = None

# Hebrew prefix letters that glue onto a word and break naive matching.
_HE_PREFIXES = ("מה", "שה", "וה", "כש", "לכ", "מ", "ב", "ל", "ה", "ש", "ו", "כ")

_LEAD_NOISE = {
    "", "Facebook", "Youtube", "חיפוש", "Skip to content", "בית",
    "ברונו גרונינג", "שיטתו של ברונו גרונינג", "ביוגרפיה", "החלמות",
}

_STOPWORDS = {
    "של", "את", "עם", "על", "לא", "כן", "זה", "זו", "הוא", "היא", "אני", "אתה",
    "אנחנו", "הם", "יש", "אין", "כל", "גם", "רק", "אבל", "או", "כי", "אם", "מה",
    "מי", "איך", "למה", "כמו", "יותר", "כך", "אז", "עוד", "כדי", "היה", "היו",
    "להיות", "אשר", "בין", "אחרי", "לפני", "תוך", "ואת", "וגם", "וכן",
}


# The movement's Hebrew translation keeps the German terms in Latin letters —
# across the 12 teaching pages, "Einstellen" appears 16 times and "התכווננות"
# zero. Israelis type the Hebrew, which is also the vocabulary of Cozio's videos.
# Without this bridge a search in the words people actually use returns nothing.
_SYNONYMS = {
    "התכווננות": ["einstellen"], "התכוונות": ["einstellen"],
    "להתכוונן": ["einstellen"], "מתכוונן": ["einstellen"],
    "התכוונן": ["einstellen"], "כיוונון": ["einstellen"],
    "רגלונג": ["regelungen"], "ויסות": ["regelungen"], "הוויסות": ["regelungen"],
    "מרפא": ["heilstrom", "regelungen"], "טיהור": ["regelungen"],
    "זרם": ["heilstrom"], "הזרם": ["heilstrom"],
    "כאב": ["regelungen"], "כאבים": ["regelungen"], "החמרה": ["regelungen"],
    "רפואי": ["רופא", "רופאים"], "רפואה": ["רופא", "רופאים"],
    "טיפול": ["רופא", "רופאים"],
    "משפט": ["אישום", "תביעה"], "תביעה": ["אישום"], "דין": ["אישום", "משפט"],
}


def _forms(word: str) -> set:
    """A word plus its plausible un-prefixed forms, so 'והכאב' matches 'כאב'."""
    out = {word}
    for p in _HE_PREFIXES:
        if word.startswith(p) and len(word) - len(p) >= 2:
            out.add(word[len(p):])
    return out


def _words(text: str) -> set:
    raw = re.findall(r"[֐-׿a-zA-Z]{2,}", text)
    out = set()
    for w in raw:
        w = w.lower()
        if w in _STOPWORDS:
            continue
        out |= _forms(w)
    return out - _STOPWORDS


def _split(body: str) -> list:
    """Break a page into chunks of at most MAX_CHUNK characters.

    Prefers blank lines, then single lines, then sentence ends. The scraped
    pages put whole articles on consecutive single-newline lines, so splitting
    on blank lines alone would keep only the first 1100 characters of a page and
    silently drop the rest — which is exactly what it did before this handled
    oversized blocks.
    """
    def by_sentence(text: str) -> list:
        out, cur = [], ""
        for s in re.split(r"(?<=[.!?।׃])\s+|\n", text):
            s = s.strip()
            if not s:
                continue
            if len(cur) + len(s) + 1 <= MAX_CHUNK:
                cur = f"{cur} {s}" if cur else s
            else:
                if cur:
                    out.append(cur)
                # A single sentence longer than the cap: hard-wrap it.
                while len(s) > MAX_CHUNK:
                    out.append(s[:MAX_CHUNK])
                    s = s[MAX_CHUNK:]
                cur = s
        if cur:
            out.append(cur)
        return out

    chunks, cur = [], ""
    for p in [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]:
        if len(p) > MAX_CHUNK:
            if len(cur) >= MIN_CHUNK:
                chunks.append(cur)
            cur = ""
            chunks.extend(by_sentence(p))
        elif len(cur) + len(p) + 2 <= MAX_CHUNK:
            cur = f"{cur}\n\n{p}" if cur else p
        else:
            if len(cur) >= MIN_CHUNK:
                chunks.append(cur)
            cur = p
    if len(cur) >= MIN_CHUNK:
        chunks.append(cur)
    return [c for c in chunks if len(c) >= MIN_CHUNK]


def _read(path: Path) -> tuple:
    """Return (title, source_url, body) for one corpus markdown file."""
    text = path.read_text(encoding="utf-8")
    title = ""
    m = re.match(r"#\s*(.+)", text)
    if m:
        title = re.split(r"\s*::\s*|\s+-\s+חוג ידידי", m.group(1))[0].strip()
    url = ""
    m = re.search(r"מקור:\s*(https?://\S+)", text)
    if m:
        url = m.group(1)
    body = text.split("---", 1)[-1] if "---" in text else text
    body = re.sub(r"^#.*$", "", body, flags=re.M)
    body = re.sub(r"^###\s*שקופית\s*\d+\s*$", "", body, flags=re.M)
    # Breadcrumb / social / search leftovers the scraper couldn't strip by tag.
    lines = body.split("\n")
    while lines and (lines[0].strip() in _LEAD_NOISE or "›" in lines[0]):
        lines.pop(0)
    return title or path.stem, url, "\n".join(lines)


def load() -> list:
    """Build the chunk index once per process."""
    global _CHUNKS
    if _CHUNKS is not None:
        return _CHUNKS

    chunks = []
    for directory, authority in ((OFFICIAL_DIR, "official"), (ARCHIVE_DIR, "archive")):
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            if path.name.lower() in ("index.md", "manifest.json"):
                continue
            try:
                title, url, body = _read(path)
            except Exception:
                continue
            section = path.parent.name if authority == "official" else "topics"
            for piece in _split(body):
                chunks.append({
                    "text": piece,
                    "title": title,
                    "url": url,
                    "section": section,
                    "authority": authority,
                    "words": _words(f"{title} {piece}"),
                })
    _CHUNKS = chunks
    return _CHUNKS


# The teaching pages are the doctrine itself; healing testimonials are the
# largest section by volume and would otherwise drown everything else out.
_SECTION_WEIGHT = {
    "teaching": 1.6,
    "medical": 2.6,
    "biography": 1.1,
    "topics": 1.0,
    "healings": 0.7,
}


def search(query: str, top_k: int = 6, min_score: float = MIN_SCORE) -> list:
    """Top passages for a question, official material ranked first."""
    q = _words(query)
    if not q:
        return []
    for w in list(q):
        q.update(_SYNONYMS.get(w, ()))
    scored = []
    for c in load():
        hits = q & c["words"]
        if not hits:
            continue
        score = len(hits)
        # A term in the page title is worth more than one buried in the body.
        title_words = _words(c["title"])
        score += 1.5 * len(q & title_words)
        score *= _SECTION_WEIGHT.get(c["section"], 1.0)
        if c["authority"] == "official":
            score *= 1.35
        if score >= min_score:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])

    out, seen = [], set()
    for score, c in scored:
        key = (c["title"], c["text"][:60])
        if key in seen:
            continue
        seen.add(key)
        out.append({**{k: v for k, v in c.items() if k != "words"}, "score": round(score, 2)})
        if len(out) >= top_k:
            break
    return out


def as_context(passages: list) -> str:
    """Render passages for the model, labelled so it can cite them correctly."""
    if not passages:
        return "(לא נמצאו קטעים רלוונטיים בקורפוס.)"
    parts = []
    for i, p in enumerate(passages, 1):
        if p["authority"] == "official":
            src = f'האתר הרשמי — {p["title"]}'
            if p["url"]:
                src += f' | {p["url"]}'
            tag = "מקור רשמי — מותר לצטט"
        else:
            src = f'ארכיון הסרטונים — {p["title"]}'
            tag = "ארכיון פנימי — לא מאושר, אסור לצטט כלשון גרונינג"
        parts.append(f"[קטע {i}] ({tag})\nמקור: {src}\n\n{p['text']}")
    return "\n\n---\n\n".join(parts)


def stats() -> dict:
    chunks = load()
    by = {}
    for c in chunks:
        by[c["section"]] = by.get(c["section"], 0) + 1
    return {
        "chunks": len(chunks),
        "by_section": by,
        "chars": sum(len(c["text"]) for c in chunks),
    }


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    q = " ".join(sys.argv[1:]) or "מה עושים כשהכאב מחמיר אחרי ההתכווננות"
    print(f"\n--- {q} ---")
    for p in search(q):
        print(f'{p["score"]:6.2f}  [{p["authority"]}/{p["section"]}]  {p["title"][:50]}')
        print(f'        {p["text"][:130]}...')
