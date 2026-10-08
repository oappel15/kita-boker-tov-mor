#!/usr/bin/env python3
"""בוקר טוב עולמי – static site generator.
Reads content/topics.json + every content/editions/YYYY-MM-DD.json and rebuilds ALL pages.
Usage:  python3 build.py          (validate + build)
        python3 build.py --check  (validate only)
Standard library only (Pillow optional, used just to read image sizes)."""
import json, os, re, sys, glob, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_NAME = "בוקר טוב עולמי"
FOOTER_CREDIT = "האתר נוצר ע״י מור לנגר אפל"
MAX_WORDS = 150
MONTHS = ["ינואר","פברואר","מרץ","אפריל","מאי","יוני","יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"]
DAYS = ["יום שני","יום שלישי","יום רביעי","יום חמישי","יום שישי","שבת","יום ראשון"]
try:
    from PIL import Image
except Exception:
    Image = None

def e(s): return html.escape(str(s), quote=True)
def d_obj(s): return datetime.date.fromisoformat(s)
def heb_date(s, weekday=False):
    d = d_obj(s); t = f"{d.day} ב{MONTHS[d.month-1]} {d.year}"
    return f"{DAYS[d.weekday()]}, {t}" if weekday else t
def words(txt): return len([w for w in re.split(r"\s+", txt) if re.search(r"\w", w)])

# ---------------- load + validate ----------------
def load():
    topics = json.load(open(os.path.join(ROOT, "content/topics.json"), encoding="utf-8"))
    tmap = {t["key"]: t for t in topics}
    eds = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content/editions/*.json"))):
        ed = json.load(open(f, encoding="utf-8"))
        ed["_file"] = os.path.relpath(f, ROOT)
        eds.append(ed)
    eds.sort(key=lambda x: x["date"], reverse=True)
    return topics, tmap, eds

def validate(tmap, eds):
    errs = []; seen_dates = set()
    contact = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|(?:\+?972|0)[- ]?5\d[- ]?\d{3}[- ]?\d{4}")
    for ed in eds:
        w = ed["_file"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ed.get("date", "")): errs.append(f"{w}: bad date"); continue
        if os.path.basename(w) != ed["date"] + ".json": errs.append(f"{w}: file name must equal date")
        if ed["date"] in seen_dates: errs.append(f"{w}: duplicate edition date")
        seen_dates.add(ed["date"])
        for k in ("number", "title", "intro", "items"):
            if k not in ed: errs.append(f"{w}: missing '{k}'")
        ids = set()
        for it in ed.get("items", []):
            p = f"{w} [{it.get('id','?')}]"
            for k in ("id", "topic", "date", "title", "body", "image", "sources", "think"):
                if not it.get(k): errs.append(f"{p}: missing '{k}'")
            if not re.fullmatch(r"[a-z0-9-]+", it.get("id", "")): errs.append(f"{p}: id must be a-z0-9-")
            if it.get("id") in ids: errs.append(f"{p}: duplicate id")
            ids.add(it.get("id"))
            if it.get("topic") not in tmap: errs.append(f"{p}: unknown topic '{it.get('topic')}'")
            body = " ".join(it.get("body", [])) if isinstance(it.get("body"), list) else str(it.get("body", ""))
            n = words(body)
            if n > MAX_WORDS: errs.append(f"{p}: body has {n} words (max {MAX_WORDS})")
            if it.get("topic") == "experiments":
                for k in ("materials", "steps", "why", "safety"):
                    if not it.get(k): errs.append(f"{p}: experiment missing '{k}'")
                if words(it.get("why", "")) > MAX_WORDS: errs.append(f"{p}: 'why' over {MAX_WORDS} words")
            img = it.get("image") or {}
            for k in ("src", "alt", "caption", "credit", "license"):
                if not img.get(k): errs.append(f"{p}: image missing '{k}'")
            if img.get("src", "").startswith("http"): errs.append(f"{p}: image must be stored locally under assets/img (no hotlinking)")
            elif img.get("src") and not os.path.exists(os.path.join(ROOT, img["src"])): errs.append(f"{p}: image file not found {img['src']}")
            if img.get("src", "").lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not img.get("source_url"):
                errs.append(f"{p}: photo needs image.source_url (licence page)")
            for s in it.get("sources", []) + it.get("more", []):
                if not s.get("url", "").startswith("https://"): errs.append(f"{p}: link must be https: {s.get('url')}")
                if not s.get("name") or not s.get("title"): errs.append(f"{p}: link needs name + title")
            v = it.get("video")
            if v:
                if not v.get("url", "").startswith("https://"): errs.append(f"{p}: bad video url")
                if not v.get("channel"): errs.append(f"{p}: video needs channel (credit)")
            if contact.search(json.dumps(it, ensure_ascii=False)): errs.append(f"{p}: looks like an email/phone – remove contact details")
    return errs

# ---------------- html pieces ----------------
def head(title, desc):
    return f"""<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E☀️%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Varela+Round&family=Assistant:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css"></head>
<body class="nav-open">
<a class="skip" href="#main">דילוג לתוכן</a>
<script>try{{if(localStorage.getItem("kitaBoker:nav")==="0"||(localStorage.getItem("kitaBoker:nav")===null&&innerWidth<760))document.body.classList.remove("nav-open")}}catch(e){{}}</script>
"""

def nav(topics, active):
    links = [("index.html", "☀️ המהדורה החדשה", "home")]
    links += [(f"topic-{t['key']}.html", f"{t['emoji']} {t['name']}", t["key"]) for t in topics]
    links += [("archive.html", "🗂️ ארכיון", "archive"), ("about.html", "💛 על האתר", "about")]
    li = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if k == active else ""}>{e(n)}</a></li>' for h, n, k in links)
    return f"""<div class="navwrap" id="navbar"><button type="button" id="nav-toggle" class="nav-toggle" aria-controls="site-nav" aria-expanded="true">✕ סגירה</button>
<nav id="site-nav" aria-label="ניווט ראשי"><ul>{li}</ul></nav></div>"""

def masthead(sub):
    return f"""<header class="mast"><div class="sky" aria-hidden="true"><span class="sun"></span><span class="cloud c1"></span><span class="cloud c2"></span><span class="cloud c3"></span></div>
<div class="mast-in"><p class="kicker">ידיעות טובות לכל המשפחה, מכיתה ד׳ ועד מבוגרים ומבוגרות</p>
<h1><a href="index.html">בוקר טוב עולמי</a></h1><p class="sub">{sub}</p></div></header>"""

def footer(latest):
    return f"""<footer class="sitefoot" role="contentinfo"><span>☀️ {FOOTER_CREDIT}</span><span class="sep">·</span><span>מתעדכן פעם בשבוע<span class="fdate"> · מהדורה אחרונה: {e(heb_date(latest))}</span></span><span class="sep">·</span><a href="about.html">על האתר והקרדיטים</a></footer>
<script src="assets/app.js"></script></body></html>"""

def img_tag(img):
    w = h = None
    p = os.path.join(ROOT, img["src"])
    if img["src"].endswith(".svg"): w, h = 800, 500
    elif Image:
        try: w, h = Image.open(p).size
        except Exception: pass
    wh = f' width="{w}" height="{h}"' if w else ""
    tall = " tall" if (w and h and h > w) else ""
    return f'<img class="pic{tall}" src="{e(img["src"])}" alt="{e(img["alt"])}"{wh} loading="lazy" decoding="async">'

def img_credit(img):
    lic = e(img["license"])
    if img.get("license_url"): lic = f'<a href="{e(img["license_url"])}" rel="noopener license" target="_blank">{lic}</a>'
    src = f' · <a href="{e(img["source_url"])}" rel="noopener" target="_blank">מקור התמונה</a>' if img.get("source_url") else ""
    return f'תמונה: {e(img["credit"])} · רישיון: {lic}{src}'

def link_li(s):
    date = f' ({e(heb_date(s["date"]))})' if s.get("date") else ""
    return f'<li><a href="{e(s["url"])}" rel="noopener" target="_blank">{e(s["title"])}</a> · <span class="src">{e(s["name"])}</span>{date}</li>'

def article(it, ed, tmap, show_edition=False):
    t = tmap[it["topic"]]; aid = f'{ed["date"]}-{it["id"]}'
    body = it["body"] if isinstance(it["body"], list) else [it["body"]]
    paras = "".join(f"<p>{e(x)}</p>" for x in body)
    extra = ""
    if it["topic"] == "experiments":
        extra = ('<div class="exp"><div><h4>🧺 מה צריך?</h4><ul>' + "".join(f"<li>{e(m)}</li>" for m in it["materials"]) + '</ul></div>'
                 '<div><h4>👣 איך עושים?</h4><ol>' + "".join(f"<li>{e(s)}</li>" for s in it["steps"]) + '</ol></div></div>'
                 f'<h4>🤔 למה זה קורה?</h4><p>{e(it["why"])}</p><p class="safety">⚠️ <b>בטיחות:</b> {e(it["safety"])}</p>')
    vid = ""
    if it.get("video"):
        v = it["video"]; meta = " · ".join(x for x in (v.get("lang"), v.get("duration")) if x)
        vid = f'<p class="video"><a class="btn vbtn" href="{e(v["url"])}" rel="noopener" target="_blank">▶ לצפייה בסרטון</a> <span>״{e(v["title"])}״ · ערוץ: {e(v["channel"])}{" · " + e(meta) if meta else ""}</span></p>'
    edl = f'<a class="edlink" href="edition-{ed["date"]}.html#{aid}">ממהדורה {e(ed["number"])} · {e(heb_date(ed["date"]))}</a>' if show_edition else ""
    more = ""
    if it.get("more"):
        more = '<h5>📖 להעמיק ולקרוא עוד</h5><ul>' + "".join(link_li(s) for s in it["more"]) + "</ul>"
    return f"""<article class="item" id="{aid}" style="--tc:{t['color']};--ti:{t['ink']}" data-topic="{t['key']}">
<figure>{img_tag(it['image'])}<figcaption>{e(it['image']['caption'])}</figcaption></figure>
<div class="item-in"><p class="tag">{t['emoji']} בוקר טוב {e(t['name'])}</p>
<h3 class="tts-src">{e(it['title'])}</h3><p class="when">{e(heb_date(it['date']))} {edl}</p>
<div class="tts-src body">{paras}</div>{extra}{vid}
<p class="think"><b>💬 לחשוב ולשוחח:</b> {e(it['think'])}</p>
<div class="tts"><button type="button" class="btn sm" data-tts="@item">🔊 הקראה</button><button type="button" class="btn sm ghost" data-tts="@item" data-slow>🐢 לאט</button><button type="button" class="btn sm ghost" data-tts-stop>⏹ עצירה</button><span class="tts-note" aria-live="polite"></span></div>
<details class="credits" open><summary>מקורות וקרדיטים</summary><h5>📰 מקורות המידע</h5><ul>{"".join(link_li(s) for s in it['sources'])}</ul>{more}<p class="imgcred">{img_credit(it['image'])}</p><p class="note">הידיעה נכתבה במילים שלנו על סמך המקורות.</p></details>
</div></article>"""

def edition_body(ed, topics, tmap, eds):
    chips = []; secs = []; exps = []
    for t in topics:
        its = [i for i in ed["items"] if i["topic"] == t["key"]]
        if not its: continue
        sid = f"sec-{t['key']}"
        chips.append(f'<a class="chip" style="--tc:{t["color"]};--ti:{t["ink"]}" href="#{sid}">{t["emoji"]} {e(t["name"])}</a>')
        (exps if t["key"] == "experiments" else secs).append(f"""<section class="topic" id="{sid}" style="--tc:{t['color']};--ti:{t['ink']}"><div class="topic-h"><h2>{t['emoji']} בוקר טוב {e(t['name'])}</h2><a href="topic-{t['key']}.html">כל הידיעות של בוקר טוב {e(t['name'])} ←</a></div>
<div class="grid">{"".join(article(i, ed, tmap) for i in its)}</div></section>""")
    i = [x["date"] for x in eds].index(ed["date"])
    newer = eds[i-1] if i > 0 else None; older = eds[i+1] if i + 1 < len(eds) else None
    pn = '<nav class="pn" aria-label="מהדורות">' + (f'<a href="edition-{older["date"]}.html">→ המהדורה הקודמת ({e(heb_date(older["date"]))})</a>' if older else "<span></span>") + \
         (f'<a href="edition-{newer["date"]}.html">המהדורה הבאה ({e(heb_date(newer["date"]))}) ←</a>' if newer else '<a href="archive.html">לכל המהדורות בארכיון ←</a>') + "</nav>"
    return f"""<div class="edhead"><p class="ribbon">מהדורה {e(ed['number'])} · {e(heb_date(ed['date'], True))}</p><h2 class="edtitle">{e(ed['title'])}</h2>
<p class="intro tts-src" id="intro">{e(ed['intro'])}</p>
<div class="tts center"><button type="button" class="btn sm" data-tts=".item h3">🔊 להקריא את כל הכותרות</button><button type="button" class="btn sm ghost" data-tts="#intro">🔊 הקראת הפתיח</button><button type="button" class="btn sm ghost" data-tts-stop>⏹ עצירה</button><span class="tts-note" aria-live="polite"></span></div>
<nav class="chips" aria-label="נושאים במהדורה">{"".join(chips)}</nav></div><div class="topics-grid">{"".join(secs)}</div>{"".join(exps)}{pn}"""

def write(name, html_text):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f: f.write(html_text)

def build():
    topics, tmap, eds = load()
    errs = validate(tmap, eds)
    if errs:
        print("❌ validation failed:"); [print("  -", x) for x in errs]; sys.exit(1)
    print(f"✓ valid: {len(eds)} editions, {sum(len(x['items']) for x in eds)} items")
    if "--check" in sys.argv: return
    latest = eds[0]["date"]; F = footer(latest); out = []
    # home = newest edition
    write("index.html", head(f"{SITE_NAME} · ידיעות טובות מכל העולם", "אתר ידיעות אופטימיות לילדים, לילדות ולכל המשפחה: חלל, מדע, חינוך, רפואה, ספורט, כלכלה, מוסיקה, אירועים מיוחדים וניסויים.")
          + nav(topics, "home") + masthead("כל שבוע: ידיעות טובות ומעודדות מכל העולם, וגם ניסויים לבית ולכיתה") + '<main id="main">' + edition_body(eds[0], topics, tmap, eds) + "</main>" + F); out.append("index.html")
    for ed in eds:
        n = f"edition-{ed['date']}.html"
        write(n, head(f"מהדורה {ed['number']} · {heb_date(ed['date'])} · {SITE_NAME}", ed["intro"][:150]) + nav(topics, "") + masthead(f"מהדורה {ed['number']} · {heb_date(ed['date'])}")
              + '<main id="main">' + edition_body(ed, topics, tmap, eds) + "</main>" + F); out.append(n)
    for t in topics:
        rows = [(ed, it) for ed in eds for it in ed["items"] if it["topic"] == t["key"]]
        rows.sort(key=lambda r: (r[0]["date"], r[1]["date"]), reverse=True)
        body = "".join(article(it, ed, tmap, True) for ed, it in rows) or '<p class="empty">עוד אין כאן ידיעות. בקרוב!</p>'
        n = f"topic-{t['key']}.html"
        write(n, head(f"בוקר טוב {t['name']} · {SITE_NAME}", f"כל הידיעות הטובות בנושא {t['name']}, מהחדשה לישנה.") + nav(topics, t["key"]) + masthead(f"{t['emoji']} בוקר טוב {t['name']}")
              + f'<main id="main" class="topicpage" style="--tc:{t["color"]};--ti:{t["ink"]}"><div class="edhead"><h2 class="edtitle">{t["emoji"]} בוקר טוב {e(t["name"])}</h2><p class="intro">כל הידיעות בנושא {e(t["name"])} מכל המהדורות, מהחדשה לישנה ({len(rows)}).</p></div><div class="grid">{body}</div></main>' + F); out.append(n)
    # archive
    blocks = []
    for ed in eds:
        lis = "".join(f'<li data-q="{e((it["title"] + " " + tmap[it["topic"]]["name"]).lower())}"><span class="mini" style="--tc:{tmap[it["topic"]]["color"]}">{tmap[it["topic"]]["emoji"]} {e(tmap[it["topic"]]["name"])}</span> <a href="edition-{ed["date"]}.html#{ed["date"]}-{it["id"]}">{e(it["title"])}</a></li>' for it in ed["items"])
        blocks.append(f'<section class="arch"><h2><a href="edition-{ed["date"]}.html">מהדורה {e(ed["number"])} · {e(heb_date(ed["date"], True))}</a></h2><p>{e(ed["title"])}</p><ul>{lis}</ul></section>')
    write("archive.html", head(f"ארכיון · {SITE_NAME}", "כל המהדורות וכל הידיעות של בוקר טוב עולמי.") + nav(topics, "archive") + masthead("🗂️ הארכיון: שום ידיעה לא נמחקת")
          + f'<main id="main"><div class="edhead"><h2 class="edtitle">כל המהדורות</h2><p class="intro">{len(eds)} מהדורות, {sum(len(x["items"]) for x in eds)} ידיעות וניסויים. אפשר לחפש לפי מילה או נושא.</p>'
          + '<p class="searchrow"><label for="q">🔎 חיפוש בארכיון</label> <input id="q" type="search" placeholder="למשל: ירח, שיא, תזמורת"></p><p id="q-none" class="empty" hidden>לא מצאנו. נסו מילה אחרת.</p></div>'
          + "".join(blocks) + "</main>" + F); out.append("archive.html")
    # about + image credits
    creds = []
    for ed in eds:
        for it in ed["items"]:
            creds.append(f'<li><a href="edition-{ed["date"]}.html#{ed["date"]}-{it["id"]}">{e(it["title"])}</a>: {img_credit(it["image"])}</li>')
    chips = "".join(f'<a class="chip" style="--tc:{t["color"]};--ti:{t["ink"]}" href="topic-{t["key"]}.html">{t["emoji"]} בוקר טוב {e(t["name"])}</a>' for t in topics)
    write("about.html", head(f"על האתר · {SITE_NAME}", "על בוקר טוב עולמי, איך משתמשים בו בכיתה, וקרדיטים.") + nav(topics, "about") + masthead("💛 על האתר")
          + f"""<main id="main" class="prose"><section class="card"><h2>מה זה ״בוקר טוב עולמי״?</h2><p class="tts-src" id="about-1">אתר של ידיעות טובות, מעניינות ומעודדות מכל העולם, לילדים וילדות מכיתה ד׳ ועד מבוגרים ומבוגרות. כל ידיעה קצרה (עד 150 מילים), נכתבת במילים שלנו על סמך מקורות אמינים, ומלווה בתמונה, ולפעמים גם בסרטון. בתחתית כל ידיעה יש קרדיט למקורות וקישורים להעמקה.</p>
<p class="tts-src" id="about-2">האתר מתעדכן פעם בשבוע במהדורה חדשה. שום ידיעה לא נמחקת: כל המהדורות נשמרות בארכיון ובעמודי הנושאים, וכך נבנה לאט לאט מאגר של ידיעות טובות.</p>
<div class="tts"><button type="button" class="btn sm" data-tts="#about-1, #about-2">🔊 הקראה</button><button type="button" class="btn sm ghost" data-tts-stop>⏹ עצירה</button><span class="tts-note" aria-live="polite"></span></div>
<nav class="chips" aria-label="נושאים">{chips}</nav></section>
<section class="card"><h2>👩‍🏫👨‍🏫 רעיונות למורים ולמורות</h2><ul>
<li><b>פתיחת בוקר:</b> בוחרים ידיעה אחת, מקריאים (או לוחצים על ״הקראה״) ושואלים את שאלת ״לחשוב ולשוחח״.</li>
<li><b>כתבים וכתבות צעירים:</b> כל קבוצה מקבלת נושא, קוראת את הידיעה ומציגה אותה לכיתה בדקה אחת, בציור או בקומיקס.</li>
<li><b>מחפשים את המקור:</b> פותחים יחד את אחד המקורות שבתחתית הידיעה ובודקים: מי כתב? מתי? איך יודעים שזה אמין?</li>
<li><b>ניסוי השבוע:</b> מבצעים את אחד הניסויים בכיתה, מנחשים מראש מה יקרה, ובסוף מסבירים ״למה זה קורה?״.</li>
<li><b>הקראה:</b> ההקראה משתמשת בקול העברי של המכשיר. אם לא שומעים, אפשר להוסיף קול עברית בהגדרות או לנסות דפדפן Chrome או Edge.</li></ul></section>
<section class="card"><h2>📷 קרדיטים לתמונות</h2><p>אנחנו משתמשים רק בתמונות חופשיות לשימוש (נחלת הכלל, Creative Commons, תמונות של סוכנויות חלל ומוסדות ציבוריים) או באיורים מקוריים. לכל תמונה מצוינים היוצר או היוצרת, הרישיון והמקור.</p><ul class="small">{"".join(creds)}</ul></section>
<section class="card"><h2>🙏 תודות</h2><p>{FOOTER_CREDIT}. הבנייה והעדכון השבועי: צוות Kita. סרטונים מקושרים ליוטיוב ושייכים לערוצים שמצוינים לידם.</p></section></main>""" + F); out.append("about.html")
    # 404
    write("404.html", head(f"לא נמצא · {SITE_NAME}", "העמוד לא נמצא") + nav(topics, "") + masthead("אופס! העמוד לא נמצא") + '<main id="main" class="prose"><section class="card"><p>אולי הקישור השתנה. אפשר לחזור ל<a href="index.html">מהדורה החדשה</a> או ל<a href="archive.html">ארכיון</a>.</p></section></main>' + F)
    print("✓ built:", len(out) + 1, "pages")

if __name__ == "__main__":
    build()
