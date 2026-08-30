"""
Build the closed box: one self-contained HTML file per language, no server, no API.

Why this exists alongside the live agent: a generative agent cannot really be
approved. Approving it means approving an unbounded space of answers nobody has
read yet. The Circle of Friends can read 100% of what this file will ever say,
which is what makes it distributable to 20 branches and 100 countries — including
places with no reliable internet and no way to pay for a service.

What goes in:
  - the movement's own teaching chapters, each shown in full, verbatim, with a
    link to the page it came from. This script selects and arranges; it never
    writes doctrine.
  - full-text search over the official material in that language
  - an index of the presentations with their video links (Hebrew build only —
    the videos are Hebrew)

What stays out, on purpose:
  - the 361 healing testimonials. Unsupervised, reaching someone asking about
    their own illness, they read as a promise of outcome.
  - the video-archive OCR text. It is Cozio's edit, not an authorized text, and
    it carries visible OCR errors.

Run:  python build_closed_box.py            # all languages
      python build_closed_box.py he ru      # only these
Out:  static/groening-closed-box[-<lang>].html
"""

import html
import json
import sys
from pathlib import Path

import groening_corpus
from closed_box_lang import CONTACT_URL, STRINGS

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parents[3] / "data"
OUT_DIR = SCRIPT_DIR / "static"

# Hebrew carries the full site (biography and the MWF page as well); the other
# languages carry the teaching section, which is what has been translated.
SECTIONS = {"he": {"teaching", "biography", "medical"}}
DEFAULT_SECTIONS = {"teaching"}

CONTACTS = [("בלהה", "054-7809195"), ("כרמית", "052-4766334")]
PLAYLIST = "https://www.youtube.com/playlist?list=PLQ93nZFhhcvdHcvsQ7Npd6zKdCRz0pu_j"


def chunks_for(lang: str) -> list:
    allowed = SECTIONS.get(lang, DEFAULT_SECTIONS)
    return [
        c for c in groening_corpus.load()
        if c["authority"] == "official"
        and c.get("lang", "he") == lang
        and c["section"] in allowed
    ]


def chapters(cs: list) -> list:
    """Group the teaching chunks back into their pages, in site order."""
    pages, order = {}, []
    for c in cs:
        if c["section"] != "teaching":
            continue
        key = c["url"] or c["title"]
        if key not in pages:
            pages[key] = {"title": c["title"], "url": c["url"], "parts": []}
            order.append(key)
        pages[key]["parts"].append(c["text"].strip())
    return [
        {"title": pages[k]["title"], "url": pages[k]["url"],
         "text": "\n\n".join(pages[k]["parts"])}
        for k in order
    ]


def videos() -> list:
    try:
        v = json.loads((DATA_DIR / "groening_videos.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    seen, out = set(), []
    for topic, meta in sorted(v.get("topics", {}).items()):
        if meta["url"] in seen:
            continue
        seen.add(meta["url"])
        out.append({"n": meta.get("video_title") or topic, "u": meta["url"]})
    return out


TEMPLATE = """<!DOCTYPE html>
<html lang="__LANG__" dir="__DIR__">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#faf8f5;color:#2c2a28;line-height:1.7;padding:18px}
.wrap{max-width:820px;margin:0 auto}
header{text-align:center;padding:26px 0 20px}
h1{font-size:clamp(28px,6vw,44px);font-weight:600;letter-spacing:.5px;color:#1a1816}
.tagline{color:#8a6d3b;font-size:clamp(14px,2.4vw,17px);margin-top:6px}
.what{background:#fff;border:1px solid #e3ddd3;border-__EDGE__:4px solid #8a6d3b;border-radius:10px;padding:16px 18px;margin:18px 0;font-size:14.5px}
.what h2{font-size:15px;color:#8a6d3b;margin-bottom:8px}
.what p{margin-bottom:9px}
.what p:last-child{margin-bottom:0}
.what b{color:#1a1816}
.draft{background:#fff8e6;border:1px solid #e0c169;border-radius:10px;padding:13px 16px;margin-bottom:18px;font-size:13.5px;color:#6b5316}
.search{margin:22px 0 8px}
input{width:100%;padding:14px 16px;font-size:16px;font-family:inherit;border:1px solid #d9d2c6;border-radius:11px;background:#fff;color:#2c2a28}
input:focus{outline:none;border-color:#8a6d3b}
.count{font-size:12.5px;color:#8c857c;padding:6px 3px 0}
.qa{border:1px solid #e3ddd3;border-radius:11px;margin-bottom:11px;background:#fff;overflow:hidden}
.qa summary{padding:15px 17px;cursor:pointer;font-weight:600;font-size:15.5px;color:#1a1816;list-style:none}
.qa summary::-webkit-details-marker{display:none}
.qa .body{padding:0 17px 16px;font-size:15px;color:#3c3934}
.qa .text{white-space:pre-wrap}
.src{margin-top:12px;padding-top:11px;border-top:1px solid #eee7dc;font-size:12.5px;color:#8c857c}
.src a{color:#8a6d3b}
h2.sec{font-size:16px;color:#8a6d3b;margin:30px 0 12px;padding-bottom:7px;border-bottom:1px solid #e3ddd3}
.hit{border:1px solid #e3ddd3;border-radius:11px;padding:14px 16px;margin-bottom:10px;background:#fff;font-size:14.5px;white-space:pre-wrap;color:#3c3934}
.vid{display:block;padding:9px 13px;border:1px solid #e3ddd3;border-radius:9px;margin-bottom:7px;background:#fff;color:#3c3934;text-decoration:none;font-size:14px}
.vid:hover{border-color:#8a6d3b}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:7px}
.card{background:#fff;border:1px solid #e3ddd3;border-radius:11px;padding:16px 18px;margin-top:14px;font-size:14.5px}
.card h3{font-size:15px;color:#8a6d3b;margin-bottom:9px}
.card a{color:#8a6d3b;font-weight:600;text-decoration:none}
.med{background:#f2f5f8;border:1px solid #ccd8e3;border-radius:11px;padding:15px 17px;margin-top:16px;font-size:13.5px;color:#41556b}
.credit{text-align:center;margin:30px 0 12px;font-size:12px;color:#a9a29a}
.credit b{color:#8c857c;letter-spacing:2px}
.empty{color:#8c857c;font-size:14px;padding:14px 3px}
.listen{background:#f3efe8;border:1px solid #ddd5c8;color:#6b5f4d;border-radius:8px;
  padding:6px 13px;font-size:12.5px;font-family:inherit;cursor:pointer;margin-bottom:12px}
.listen:hover{border-color:#8a6d3b;color:#8a6d3b}
.listen.on{background:#8a6d3b;border-color:#8a6d3b;color:#fff}
.hint{font-size:12.5px;color:#8c857c;margin:-4px 0 12px}
.hit .where{font-size:12.5px;color:#8a6d3b;font-weight:600;margin-bottom:7px;white-space:normal}
.hit mark{background:#fdf0c9;color:#5c4a12;padding:0 2px;border-radius:3px}
.hit .ctx{color:#9a938a}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>__H1__</h1>
  <p class="tagline">__TAGLINE__</p>
</header>

<div class="draft">__DRAFT__</div>

<div class="what">
  <h2>__WHAT_H__</h2>
  __WHAT__
</div>

<h2 class="sec">__QA_H__</h2>
<p class="hint" id="readHint" hidden>__READ_HINT__</p>
<div>__QA__</div>

<h2 class="sec">__SEARCH_H__</h2>
<div class="search">
  <input id="q" placeholder="__SEARCH_PH__" autocomplete="off">
  <div class="count" id="count"></div>
</div>
<div id="hits"></div>

__VIDBLOCK__

<div class="card">
  <h3>__CONTACT_H__</h3>
  __CONTACT__
</div>

<div class="med">__MED__</div>

<p class="credit">__CREDIT__ <b>BEZEN</b></p>
</div>

<script>
const CORPUS = __CORPUS__;
const SYN = __SYN__;
const L = __L__;

const PRE = ["מה","שה","וה","כש","לכ","מ","ב","ל","ה","ש","ו","כ"];
const STOP = new Set(__STOP__);

function words(s){
  const out=new Set();
  for(const raw of (s.match(/[\\u0590-\\u05FF\\u0600-\\u06FF\\u0400-\\u04FFa-zA-Z]{2,}/g)||[])){
    const w=raw.toLowerCase();
    if(STOP.has(w)) continue;
    out.add(w);
    for(const p of PRE) if(w.startsWith(p) && w.length-p.length>=2) out.add(w.slice(p.length));
  }
  return out;
}
const INDEX = CORPUS.map((c,i)=>({...c, i, w: words(c.ti+" "+c.t)}));

// Highlight the words that were searched for. Runs on already-escaped text, so
// there are no tags to collide with.
function mark(escaped, terms){
  if(!terms.length) return escaped;
  try{
    return escaped.replace(new RegExp('('+terms.join('|')+')','gi'),'<mark>$1</mark>');
  }catch(e){ return escaped; }
}

// A passage cut at a chunk boundary can open mid-thought. Borrow the tail of the
// previous piece and the head of the next one from the same page, so the result
// reads as part of something rather than as a fragment.
function withContext(c){
  const before = INDEX[c.i-1], after = INDEX[c.i+1];
  let pre='', post='';
  if(before && before.u===c.u){
    const ss = before.t.trim().split(/(?<=[.!?׃।])\\s+/);
    pre = ss.slice(-2).join(' ').trim();
    if(pre.length>240) pre = '…'+pre.slice(-240);
  }
  if(after && after.u===c.u){
    const ss = after.t.trim().split(/(?<=[.!?׃।])\\s+/);
    post = ss.slice(0,2).join(' ').trim();
    if(post.length>240) post = post.slice(0,240)+'…';
  }
  return {pre, post};
}

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

function search(qs){
  const q=words(qs);
  if(!q.size) return [];
  for(const w of [...q]) if(SYN[w]) for(const x of SYN[w]) q.add(x);
  const scored=[];
  for(const c of INDEX){
    let n=0; for(const t of q) if(c.w.has(t)) n++;
    if(!n) continue;
    const tw=words(c.ti);
    let sc=n; for(const t of q) if(tw.has(t)) sc+=1.5;
    if(c.s==="teaching") sc*=1.6; else if(c.s==="medical") sc*=2.6;
    scored.push([sc,c]);
  }
  scored.sort((a,b)=>b[0]-a[0]);

  // One entry per chapter. Chunking often puts the same page at the top three
  // times over, which fills the list without adding anything.
  const seen=new Set(), out=[];
  for(const [sc,c] of scored){
    if(seen.has(c.u)) continue;
    seen.add(c.u);
    out.push(c);
    if(out.length>=10) break;
  }
  return out;
}

// ── Read aloud, offline ────────────────────────────────────────────────────
// speechSynthesis is built into the browser and needs no network, so a chapter
// can be listened to on a phone with no connection at all — which is the point
// for readers this file has to reach. Chapters run to a few thousand
// characters, and Chrome truncates a long utterance, so the text is queued
// sentence by sentence.
const TTS = window.speechSynthesis;
let playing = null;

if (TTS) {
  document.getElementById('readHint').hidden = false;
  document.querySelectorAll('.listen').forEach(btn => { btn.hidden = false; });
}

function stopAll(){
  if (!TTS) return;
  TTS.cancel();
  if (playing) {
    playing.classList.remove('on');
    playing.textContent = playing.dataset.read;
    playing = null;
  }
}

function listen(btn){
  if (!TTS) return;
  const wasPlaying = (playing === btn);
  stopAll();
  if (wasPlaying) return;

  const text = btn.parentElement.querySelector('.text').textContent;
  const parts = text.split(/(?<=[.!?׃।])\\s+|\\n+/).filter(x => x.trim().length > 1);
  const queue = [];
  let cur = '';
  for (const p of parts) {
    if ((cur + ' ' + p).length > 220) { if (cur) queue.push(cur); cur = p; }
    else cur = cur ? cur + ' ' + p : p;
  }
  if (cur) queue.push(cur);

  playing = btn;
  btn.classList.add('on');
  btn.textContent = L.stop;

  queue.forEach((chunk, i) => {
    const u = new SpeechSynthesisUtterance(chunk);
    u.lang = L.bcp;
    u.rate = 0.95;
    if (i === queue.length - 1) u.onend = () => { if (playing === btn) stopAll(); };
    TTS.speak(u);
  });
}

document.addEventListener('click', e => {
  const b = e.target.closest('.listen');
  if (b) listen(b);
});

const input=document.getElementById('q');
const hits=document.getElementById('hits');
const count=document.getElementById('count');

input.addEventListener('input',()=>{
  const v=input.value.trim();
  hits.innerHTML=''; count.textContent='';
  if(v.length<2) return;
  const r=search(v);
  if(!r.length){ hits.innerHTML='<p class="empty">'+L.empty+'</p>'; return; }
  count.textContent=r.length+' '+L.hits;

  const terms=[...words(v)].filter(w=>w.length>2);
  hits.innerHTML=r.map(c=>{
    const {pre,post}=withContext(c);
    const body =
      (pre  ? '<span class="ctx">'+mark(esc(pre),terms)+' </span>' : '') +
      mark(esc(c.t),terms) +
      (post ? '<span class="ctx"> '+mark(esc(post),terms)+'</span>' : '');
    return '<div class="hit"><div class="where">'+esc(c.ti)+'</div>'+body+
      '<div class="src">'+L.src+' <a href="'+c.u+'" target="_blank" rel="noopener">'+esc(c.ti)+'</a></div></div>';
  }).join('');
});
</script>
</body>
</html>
"""


def build(lang: str) -> Path:
    L = STRINGS[lang]
    cs = chunks_for(lang)
    if not cs:
        raise SystemExit(f"no official chunks for {lang}")

    chs = chapters(cs)
    qa = "\n".join(
        '<details class="qa"><summary>{t}</summary><div class="body">'
        '<button class="listen" data-read="{read}" hidden>{read}</button>'
        '<div class="text">{b}</div>'
        '<div class="src">{src} <a href="{u}" target="_blank" rel="noopener">{t}</a></div>'
        "</div></details>".format(
            t=html.escape(ch["title"]), b=html.escape(ch["text"]),
            u=html.escape(ch["url"]), src=html.escape(L["src"]),
            read=html.escape(L["read"]),
        )
        for ch in chs
    )

    if lang == "he":
        vid = f'<h2 class="sec">{L["vid_h"]}</h2>\n<div class="grid">' + "\n".join(
            '<a class="vid" href="{u}" target="_blank" rel="noopener">{n}</a>'.format(
                u=html.escape(v["u"]), n=html.escape(v["n"]))
            for v in videos()
        ) + f'\n<a class="vid" href="{PLAYLIST}" target="_blank" rel="noopener">{L["vid_all"]}</a></div>'
        contact = L["contact"] + "<br><br>" + "<br>".join(
            f'<b>{n}</b> &nbsp; <a href="tel:{p.replace("-", "")}">{p}</a>' for n, p in CONTACTS
        )
    else:
        vid = ""
        contact = (L["contact"] + f'<br><br><a href="{CONTACT_URL}" target="_blank" '
                   f'rel="noopener">bruno-groening.org</a>')

    corpus = [{"t": c["text"].strip(), "ti": c["title"], "u": c["url"], "s": c["section"]}
              for c in cs]

    page = TEMPLATE
    for key, val in {
        "__LANG__": lang, "__DIR__": L["dir"],
        "__EDGE__": "right" if L["dir"] == "rtl" else "left",
        "__TITLE__": L["title"], "__H1__": L["title"].split("—")[0].strip(),
        "__TAGLINE__": L["tagline"], "__DRAFT__": L["draft"],
        "__WHAT_H__": L["what_h"],
        "__WHAT__": "\n  ".join(f"<p>{p}</p>" for p in L["what"]),
        "__QA_H__": L["qa_h"], "__QA__": qa,
        "__SEARCH_H__": L["search_h"], "__SEARCH_PH__": L["search_ph"],
        "__VIDBLOCK__": vid, "__CONTACT_H__": L["contact_h"], "__CONTACT__": contact,
        "__MED__": L["med"], "__CREDIT__": L["credit"],
        "__CORPUS__": json.dumps(corpus, ensure_ascii=False, separators=(",", ":")),
        "__SYN__": json.dumps(groening_corpus._SYNONYMS, ensure_ascii=False, separators=(",", ":")),
        "__STOP__": json.dumps(sorted(groening_corpus._STOPWORDS), ensure_ascii=False, separators=(",", ":")),
        "__READ_HINT__": L["read_hint"],
        "__L__": json.dumps({k: L[k] for k in ("hits", "empty", "src", "read", "stop", "bcp")},
                            ensure_ascii=False),
    }.items():
        page = page.replace(key, val)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    name = "groening-closed-box.html" if lang == "he" else f"groening-closed-box-{lang}.html"
    out = OUT_DIR / name
    out.write_text(page, encoding="utf-8")
    print(f"  {lang}  {len(chs):2d} chapters · {len(corpus):3d} passages · "
          f"{out.stat().st_size / 1024:5.0f} KB  ->  {name}")
    return out


if __name__ == "__main__":
    for lg in (sys.argv[1:] or list(STRINGS)):
        build(lg)
