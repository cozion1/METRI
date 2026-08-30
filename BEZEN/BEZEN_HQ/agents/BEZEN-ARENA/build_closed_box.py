"""
Build the closed box: one self-contained HTML file, no server, no API.

Why this exists alongside the live agent: a generative agent cannot really be
approved. Approving it means approving an unbounded space of answers nobody has
read yet. The Circle of Friends can read 100% of what this file will ever say,
which is what makes it distributable to 20 branches and 100 countries.

What goes in:
  - curated question -> answer pairs, where every answer is text copied VERBATIM
    from the movement's own site (this script selects passages, it never writes
    them), each with its source URL
  - full-text search over the official teaching, biography and medical pages
  - an index of the 52 presentations with their video links

What stays out, on purpose:
  - the 361 healing testimonials. Unsupervised, delivered to someone asking about
    their own illness, they read as a promise of outcome.
  - the video-archive OCR text. It is Cozio's edit, not an authorized text, and
    it carries visible OCR errors.

Run:  python build_closed_box.py
Out:  static/groening-closed-box.html
"""

import html
import json
import re
from pathlib import Path

import groening_corpus

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parents[3] / "data"
OUT = SCRIPT_DIR / "static" / "groening-closed-box.html"

# Sections allowed into the box. See module docstring for what is excluded.
ALLOWED = {"teaching", "biography", "medical"}

CONTACTS = [("בלהה", "054-7809195"), ("כרמית", "052-4766334")]
PLAYLIST = "https://www.youtube.com/playlist?list=PLQ93nZFhhcvdHcvsQ7Npd6zKdCRz0pu_j"

# Curated entries. The `find` string locates a passage in the corpus; the answer
# shown to the reader is that passage, verbatim. Nothing here is composed.
SEEDS = [
    ("מהי ההתכווננות, ואיך עושים אותה?", "לשבת עם ידיים פתוחות, כשהכפות מופנות כלפי מעלה"),
    ("התחלתי להתכוונן והכאב דווקא החמיר. מה זה אומר?", "כאבי ה- Regelungen, קבלו אותם בסבלנות רבה"),
    ("מהו הזרם המרפא (Heilstrom)?", "כוח רוחני המביא בעקבותיו את ההחלמה"),
    ("מה לפי ברונו גרונינג הסיבה למחלה?", "ככל שהאדם נסוג מפני האל"),
    ("האם השיטה באה במקום טיפול רפואי?", "תוספת יעילה לידע הרפואי הקונבנציונלי"),
    ("האם אפשר לכפות החלמה על מישהו?", "אינני יכול לגנוב אותם מכם"),
    ("למה מחשבות נחשבות לכוח?", "מחשבה חיובית היא כוח בונה"),
    ("ברונו גרונינג הועמד לדין. מה קרה שם?", "הריגה מתוך רשלנות"),
    ("מה המשמעות של הרצון החופשי בשיטה?", "אי אפשר לכפות על אדם את ההחלמה"),
]


def pick(find: str) -> dict:
    """Return the official passage containing `find`, verbatim."""
    for c in groening_corpus.load():
        if c["section"] in ALLOWED and c["authority"] == "official" and find in c["text"]:
            return {"text": c["text"].strip(), "title": c["title"], "url": c["url"]}
    return {}


def build_entries() -> list:
    out = []
    for question, find in SEEDS:
        p = pick(find)
        if not p:
            print(f"  !! no passage found for: {question}")
            continue
        out.append({"q": question, **p})
    return out


def build_corpus() -> list:
    return [
        {"t": c["text"].strip(), "ti": c["title"], "u": c["url"], "s": c["section"]}
        for c in groening_corpus.load()
        if c["section"] in ALLOWED and c["authority"] == "official"
    ]


def build_videos() -> list:
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
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ברונו גרונינג — שאלות ותשובות</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#faf8f5;color:#2c2a28;line-height:1.7;padding:18px}
.wrap{max-width:820px;margin:0 auto}
header{text-align:center;padding:26px 0 20px}
h1{font-size:clamp(28px,6vw,44px);font-weight:600;letter-spacing:.5px;color:#1a1816}
.tagline{color:#8a6d3b;font-size:clamp(14px,2.4vw,17px);margin-top:6px}
.what{background:#fff;border:1px solid #e3ddd3;border-right:4px solid #8a6d3b;border-radius:10px;padding:16px 18px;margin:18px 0;font-size:14.5px}
.what h2{font-size:15px;color:#8a6d3b;margin-bottom:8px}
.what p{margin-bottom:9px}
.what p:last-child{margin-bottom:0}
.what b{color:#1a1816}
.draft{background:#fff8e6;border:1px solid #e0c169;border-radius:10px;padding:13px 16px;margin-bottom:18px;font-size:13.5px;color:#6b5316}
.search{position:relative;margin:22px 0 8px}
input{width:100%;padding:14px 16px;font-size:16px;font-family:inherit;border:1px solid #d9d2c6;border-radius:11px;background:#fff;color:#2c2a28}
input:focus{outline:none;border-color:#8a6d3b}
.count{font-size:12.5px;color:#8c857c;padding:6px 3px 0}
.qa{border:1px solid #e3ddd3;border-radius:11px;margin-bottom:11px;background:#fff;overflow:hidden}
.qa summary{padding:15px 17px;cursor:pointer;font-weight:600;font-size:15.5px;color:#1a1816;list-style:none}
.qa summary::-webkit-details-marker{display:none}
.qa summary:before{content:'‹';float:left;color:#8a6d3b;font-size:19px;line-height:1.2;transform:rotate(-90deg);transition:transform .15s}
.qa[open] summary:before{transform:rotate(90deg)}
.qa .body{padding:0 17px 16px;font-size:15px;white-space:pre-wrap;color:#3c3934}
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
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>ברונו גרונינג</h1>
  <p class="tagline">עזרה והחלמה בדרך הרוחנית</p>
</header>

<div class="draft">
  <b>גרסה לבדיקה — טרם אושרה.</b> החומר הועבר לעופר לייבה ולדוב לבדיקה ואישור.
  אין לראות בתוכן שכאן עמדה רשמית של התנועה עד לאישור.
</div>

<div class="what">
  <h2>מה זה הדף הזה — ומה הוא איננו</h2>
  <p>זהו <b>אוסף סגור של שאלות מובנות עם תשובות מובנות.</b> כל תשובה כאן היא קטע שהועתק
  מילה במילה מהאתר הרשמי של חוג ידידי ברונו גרונינג, עם קישור לעמוד המקורי. שום דבר כאן
  לא נכתב מחדש ולא נוסח מחדש.</p>
  <p>הדף עובד <b>בלי אינטרנט, בלי שרת ובלי עלות.</b> אפשר לשמור אותו, לשלוח אותו
  בוואטסאפ או במייל, ולפתוח אותו בכל מחשב או טלפון.</p>
  <p>המשמעות המעשית: אפשר לקרוא כאן <b>מאה אחוז ממה שהדף הזה אי פעם יגיד.</b> אין הפתעות.</p>
  <p><b>סוכן חי הוא דבר אחר לגמרי.</b> סוכן מבין שאלה שנוסחה בדרך שלא צפינו, מנהל שיחה
  שנמשכת לאורך כמה תשובות, ומתאים את דבריו לאדם שמולו. הדף הזה לא עושה אף אחד מהשלושה —
  הוא עונה רק על מה שהוכן מראש, ומחפש בטקסט המקורי. זה ההבדל בין ספר מסודר היטב לבין שיחה.</p>
</div>

<h2 class="sec">שאלות ותשובות</h2>
<div id="qa">__QA__</div>

<div class="search">
  <input id="q" placeholder="חיפוש בכל החומר הרשמי…" autocomplete="off">
  <div class="count" id="count"></div>
</div>
<div id="hits"></div>

<h2 class="sec">מצגות לצפייה</h2>
<div class="grid">__VIDS__</div>

<div class="card">
  <h3>לשאול על חוג</h3>
  לשאלות על חוגים, מפגשים וחוגים מרחוק — הכי טוב לדבר עם אחת משתי הנציגות הוותיקות.
  הן יסבירו ויפנו למנחה בעיר שלך.<br><br>
  __CONTACTS__
</div>

<div class="med">
  הדף אינו רופא ואינו מאבחן. הקבוצה הרפואית-מדעית של התנועה (MWF) מתארת את השיטה
  כ<b>תוספת</b> לידע הרפואי הקונבנציונלי או האלטרנטיבי — לא כתחליף לו.
  אין להפסיק, לשנות או לדחות טיפול רפואי על סמך מה שכתוב כאן.
  במצב חירום רפואי — פנו מיד לעזרה דחופה.
</div>

<p class="credit">בליווי טכנולוגי של <b>BEZEN</b></p>
</div>

<script>
const CORPUS = __CORPUS__;

// Same Hebrew handling as the server-side retrieval: strip the prefix letters
// that glue onto a word, so "והכאב" still matches "כאב".
const PRE = ["מה","שה","וה","כש","לכ","מ","ב","ל","ה","ש","ו","כ"];
const SYN = __SYN__;
const STOP = new Set(["של","את","עם","על","לא","כן","זה","זו","הוא","היא","אני","אתה","יש","אין","כל","גם","רק","אבל","או","כי","אם","מה","מי","איך","למה","כמו","יותר","כך","אז","עוד","כדי","היה","היו","להיות","בין","אחרי","לפני"]);

function words(s){
  const out=new Set();
  for(const raw of (s.match(/[\\u0590-\\u05FFa-zA-Z]{2,}/g)||[])){
    const w=raw.toLowerCase();
    if(STOP.has(w)) continue;
    out.add(w);
    for(const p of PRE) if(w.startsWith(p) && w.length-p.length>=2) out.add(w.slice(p.length));
  }
  return out;
}
const INDEX = CORPUS.map(c=>({...c, w: words(c.ti+" "+c.t)}));

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
  return scored.slice(0,8).map(x=>x[1]);
}

const input=document.getElementById('q');
const hits=document.getElementById('hits');
const count=document.getElementById('count');

input.addEventListener('input',()=>{
  const v=input.value.trim();
  hits.innerHTML=''; count.textContent='';
  if(v.length<2) return;
  const r=search(v);
  if(!r.length){
    hits.innerHTML='<p class="empty">לא נמצא קטע מתאים. נסה מילה אחרת, או פנה לאחת הנציגות.</p>';
    return;
  }
  count.textContent=r.length+' קטעים מהחומר הרשמי';
  hits.innerHTML=r.map(c=>
    '<div class="hit">'+esc(c.t)+
    '<div class="src">מקור: <a href="'+c.u+'" target="_blank" rel="noopener">'+esc(c.ti)+'</a></div></div>'
  ).join('');
});
</script>
</body>
</html>
"""


def main():
    entries = build_entries()
    corpus = build_corpus()
    videos = build_videos()

    qa = "\n".join(
        '<details class="qa"><summary>{q}</summary><div class="body">{t}'
        '<div class="src">מקור: <a href="{u}" target="_blank" rel="noopener">{ti}</a></div>'
        "</div></details>".format(
            q=html.escape(e["q"]), t=html.escape(e["text"]),
            u=html.escape(e["url"]), ti=html.escape(e["title"]),
        )
        for e in entries
    )
    vids = "\n".join(
        '<a class="vid" href="{u}" target="_blank" rel="noopener">{n}</a>'.format(
            u=html.escape(v["u"]), n=html.escape(v["n"])
        )
        for v in videos
    )
    vids += '\n<a class="vid" href="{}" target="_blank" rel="noopener">— כל המצגות —</a>'.format(PLAYLIST)
    contacts = "<br>".join(
        f'<b>{n}</b> &nbsp; <a href="tel:{p.replace("-", "")}">{p}</a>' for n, p in CONTACTS
    )

    page = (TEMPLATE
            .replace("__QA__", qa)
            .replace("__VIDS__", vids)
            .replace("__CONTACTS__", contacts)
            .replace("__SYN__", json.dumps(groening_corpus._SYNONYMS, ensure_ascii=False, separators=(",", ":")))
            .replace("__CORPUS__", json.dumps(corpus, ensure_ascii=False, separators=(",", ":"))))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")

    kb = OUT.stat().st_size / 1024
    print(f"{OUT}")
    print(f"  {len(entries)} שאלות מובנות · {len(corpus)} קטעים לחיפוש · {len(videos)} מצגות")
    print(f"  {kb:.0f} KB")


if __name__ == "__main__":
    main()
