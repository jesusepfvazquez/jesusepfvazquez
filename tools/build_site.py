#!/usr/bin/env python3
"""Build the personal website (site/) from the LaTeX CV files.

Usage, from the site root:   python3 tools/build_site.py

Source of truth (edit these in Overleaf, then paste the changed files here):
    Jesus_Vazquez_CV/cv.tex          section order (\\input lines)
    Jesus_Vazquez_CV/cv/*.tex        one file per CV section
    tools/abstracts.json             optional abstracts, keyed by paper slug
    content/cv/VAZQUEZ-CV.pdf        the compiled CV (copied to site/cv/)

Generated pages:  site/index.html, site/research/, site/publications/, site/cv/
Static files that this script does not touch:  site/assets/  (style.css, site.js, images)
"""
import datetime
import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CV_DIR = ROOT / "Jesus_Vazquez_CV"
SECTIONS_DIR = CV_DIR / "cv"
ABSTRACTS = ROOT / "tools" / "abstracts.json"
PDF_SRC = ROOT / "content" / "cv" / "VAZQUEZ-CV.pdf"
OUT = ROOT / "site"

BUILD_ID = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # busts browser caches
NAME = "Jesus E. Vazquez"
EMAIL_USER, EMAIL_DOMAIN = "jvazqu18", "jh.edu"
LINKS = [
    ("Google Scholar", "https://scholar.google.com/citations?user=QywOz04AAAAJ"),
    ("ORCID", "https://orcid.org/0000-0002-3166-1632"),
    ("GitHub", "https://github.com/jesusepfvazquez"),
    ("LinkedIn", "https://www.linkedin.com/in/jesusepfvazquez/"),
]
SKIP_SECTIONS = {"references"}  # kept off the public page; the PDF still has them

# ------------------------------------------------------------------ research areas
AREAS = [
    {
        "title": "Right-Censored Covariate Regression",
        "blurb": "Estimators for regression when a time-to-event covariate is only partly observed.",
        "keywords": ["censored covariate", "missing covariate", "outcome dependent right",
                     "conditional mean imputation"],
        "text": (
            "In many cohort studies, a covariate is a time-to-event variable that is only partly "
            "observed. In Huntington disease studies, for example, age at clinical diagnosis is "
            "unknown for participants who have not yet been diagnosed at their last visit. I develop "
            "robust and efficient estimators for regression models with right-censored covariates, "
            "study the links between right-censored and missing covariates, and apply the estimators "
            "to Huntington disease progression data."
        ),
    },
    {
        "title": "Causal Inference with Right-Censored Confounders",
        "blurb": "Identification and estimation when a confounder, or its proxy, is right-censored.",
        "keywords": ["target trial", "right-censored confounder"],
        "text": (
            "Observational studies of treatment effects are limited when an important confounder, "
            "such as disease aggressiveness, is not measured, and in slowly progressive diseases the "
            "available proxies of the confounder are often right-censored. I formalize identification "
            "conditions for this setting and develop weighted estimators, with applications to "
            "antidepressant use in Huntington disease."
        ),
    },
    {
        "title": "Federated Learning with Incomplete Data",
        "blurb": "Joint inference across clinical sites without sharing individual-level data.",
        "keywords": ["federated"],
        "text": (
            "Clinical sites often cannot share individual-level data, and each site can have its own "
            "missingness patterns. I develop federated inverse probability weighting estimators that "
            "combine site-level summaries into valid joint inference, together with a variance "
            "correction that accounts for the estimated weights."
        ),
    },
    {
        "title": "Huntington Disease Applications",
        "blurb": "Methods motivated by, and applied to, Huntington disease cohorts.",
        "keywords": ["huntington"],
        "text": (
            "The methods above are motivated by studies of Huntington disease. Applied projects with "
            "clinical collaborators cover disease progression, family-level outcomes, and clinical "
            "characteristics of patients across cohorts."
        ),
    },
    {
        "title": "Applied Collaborations",
        "blurb": "Statistical design and analysis with clinical and public health collaborators.",
        "keywords": [],
        "text": (
            "I collaborate with clinical and public health researchers on statistical design and "
            "analysis. Recent projects cover cardiovascular and kidney health after preterm birth, "
            "pulmonary infection, dermatology, physical activity measurement, neuroimaging, and "
            "environmental health."
        ),
    },
]

# ================================================================== LaTeX -> HTML
_unknown = set()
ACCENT = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303"}
SYMBOLS = {"&": "&amp;", "%": "%", "$": "$", "#": "#", "_": "_", "{": "{", "}": "}",
           " ": " ", ",": " ", ";": " ", ":": " ", "!": ""}
IGNORE_CMDS = {"footnotesize", "small", "large", "Large", "scriptsize", "normalsize", "noindent",
               "centering", "par", "relax", "hfill", "medskip", "smallskip", "bigskip"}
SPACE_CMDS = {"enskip", "quad", "qquad", "thinspace"}


def strip_comments(s):
    return re.sub(r"(?<!\\)%[^\n]*", "", s)


def read_group(s, i):
    """s[i] == '{'. Return (raw inside, index after the matching '}')."""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif c == "}" and (j == 0 or s[j - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces near: " + s[i:i + 80])


def read_arg(s, i):
    while i < len(s) and s[i].isspace():
        i += 1
    if i < len(s) and s[i] == "{":
        return read_group(s, i)
    return (s[i] if i < len(s) else ""), i + 1


def _math(m):
    m = m.replace(" ", "")
    if m in ("^*", "^{*}"):
        return "*"
    if m in ("^{\\dagger}", "^\\dagger"):
        return "†"
    return html.escape(re.sub(r"[\\{}^]", "", m))


def _accent(mark, s, i):
    if i < len(s) and s[i] == "{":
        arg, i = read_group(s, i)
    else:
        arg, i = (s[i] if i < len(s) else ""), i + 1
    arg = arg.strip()
    if arg in ("\\i", "i"):
        arg = "i"
    ch = arg[:1]
    return unicodedata.normalize("NFC", ch + ACCENT[mark]) + arg[1:], i


def _conv(s, i, in_group):
    out = []
    n = len(s)
    while i < n:
        c = s[i]
        if c == "}":
            i += 1
            if in_group:
                return "".join(out), i
            continue
        if c == "{":
            body, i = _conv(s, i + 1, True)
            out.append(body)
            continue
        if c == "~":
            out.append("\u00a0")
            i += 1
            continue
        if c == "$":
            j = s.find("$", i + 1)
            if j < 0:
                i += 1
                continue
            out.append(_math(s[i + 1:j]))
            i = j + 1
            continue
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+)\*?[ \t]*", s[i:])
            if m:
                name, i = m.group(1), i + m.end()
                if name in ("bf", "bfseries", "it", "itshape", "em", "sl"):
                    body, i = _conv(s, i, in_group)
                    tag = "strong" if name in ("bf", "bfseries") else "em"
                    out.append(f"<{tag}>{body}</{tag}>")
                    return "".join(out), i
                if name in ("textbf", "textit", "emph", "underline", "textsc", "text", "mbox",
                            "textsubscript", "textsuperscript", "textrm", "textsf"):
                    arg, i = read_arg(s, i)
                    body = _conv(arg, 0, False)[0]
                    tag = {"textbf": "strong", "textit": "em", "emph": "em",
                           "textsubscript": "sub", "textsuperscript": "sup"}.get(name)
                    out.append(f"<{tag}>{body}</{tag}>" if tag else body)
                elif name == "href":
                    url, i = read_arg(s, i)
                    text, i = read_arg(s, i)
                    url = re.sub(r"\\([_%&#])", r"\1", url.strip())
                    body = _conv(text, 0, False)[0] or html.escape(url)
                    out.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" '
                               f'rel="noopener">{body}</a>')
                elif name in ("newline", "linebreak"):
                    out.append(" ")
                elif name == "cdotp":
                    out.append("·")
                elif name in SPACE_CMDS:
                    out.append(" ")
                elif name == "i":
                    out.append("i")
                elif name in ("hspace", "vspace", "color"):
                    _, i = read_arg(s, i)
                elif name in IGNORE_CMDS:
                    pass
                else:
                    _unknown.add(name)
                continue
            nxt = s[i + 1:i + 2]
            if nxt == "\\":
                out.append(" ")
                i += 2
            elif nxt in ACCENT:
                text, i = _accent(nxt, s, i + 2)
                out.append(html.escape(text))
            elif nxt in SYMBOLS:
                out.append(SYMBOLS[nxt])
                i += 2
            else:
                i += 2
            continue
        if s.startswith("---", i):
            out.append("—")
            i += 3
        elif s.startswith("--", i):
            out.append("–")
            i += 2
        elif s.startswith("``", i):
            out.append("“")
            i += 2
        elif s.startswith("''", i):
            out.append("”")
            i += 2
        else:
            out.append(html.escape(c, quote=False))
            i += 1
    return "".join(out), i


def conv(s):
    s = strip_comments(s)
    s = re.sub(r"\\vskip\s*-?[\d.]+\s*(?:em|ex|pt|cm|mm)", "", s)
    out = re.sub(r"\s+", " ", _conv(s, 0, False)[0]).strip()
    return re.sub(r"\s*\(GPA:[^)]*\)", "", out)  # GPA stays in the PDF but is left off the website


def plain(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", plain(s).lower()).strip("-")


# ================================================================== CV parser
def split_items(raw):
    return [x for x in re.split(r"\\item\b", raw)[1:] if x.strip()]


def honors_in(raw):
    """All \\cvhonor{a}{b}{c}{d} groups inside raw text."""
    res = []
    for m in re.finditer(r"\\cvhonor\b", raw):
        i, args = m.end(), []
        for _ in range(4):
            a, i = read_arg(raw, i)
            args.append(a)
        res.append(args)
    return res


def parse_section(body):
    """Return a list of blocks: sub, entry, list, honor."""
    blocks = []
    pos = 0
    pat = re.compile(r"\\(cvsubsection|cventry|cvparagraph|cvhonor)\b")
    while True:
        m = pat.search(body, pos)
        if not m:
            break
        kind, i = m.group(1), m.end()
        if kind == "cvsubsection":
            arg, i = read_arg(body, i)
            blocks.append(("sub", conv(arg)))
        elif kind == "cventry":
            args = []
            for _ in range(5):
                a, i = read_arg(body, i)
                args.append(a)
            blocks.append(("entry", args))
        elif kind == "cvparagraph":
            arg, i = read_arg(body, i)
            e = re.search(r"\\begin\{etaremune\}(.*)\\end\{etaremune\}", arg, re.S)
            items = []
            for it in split_items(e.group(1) if e else arg):
                sub = []
                hm = re.search(r"\\begin\{cvhonors_smaller\}(.*?)\\end\{cvhonors_smaller\}", it, re.S)
                if hm:
                    sub = honors_in(hm.group(1))
                    it = it[:hm.start()] + it[hm.end():]
                items.append((it, sub))
            blocks.append(("list", items))
        else:  # cvhonor
            args = []
            for _ in range(4):
                a, i = read_arg(body, i)
                args.append(a)
            blocks.append(("honor", args))
        pos = i
    return blocks


def parse_cv():
    order = re.findall(r"^\s*\\input\{cv/([^}]+?)(?:\.tex)?\}", (CV_DIR / "cv.tex").read_text(
        encoding="utf-8"), re.M)
    sections = []
    for name in order:
        if name in SKIP_SECTIONS:
            continue
        text = strip_comments((SECTIONS_DIR / f"{name}.tex").read_text(encoding="utf-8"))
        m = re.search(r"\\cvsection\{", text)
        title, end = read_group(text, m.end() - 1)
        sections.append({"file": name, "title": conv(title), "blocks": parse_section(text[end:])})
    return sections


# ------------------------------------------------------------------ CV rendering
def desc_html(raw):
    raw = raw.strip()
    if not raw:
        return ""
    m = re.search(r"\\begin\{cvitems\}(.*?)\\end\{cvitems\}", raw, re.S)
    lead = conv(raw[:m.start()]) if m else conv(raw)
    parts = f"<p>{lead}</p>" if lead else ""
    if m:
        items = "".join(f"<li>{conv(x)}</li>" for x in split_items(m.group(1)))
        parts += f"<ul>{items}</ul>"
    return parts


def date_html(d):
    return conv(d).replace(" - ", " – ")


def render_entry(a, bold_sub=False):
    role, org, loc, date, desc = a
    role_h, org_h, loc_h, date_h = conv(role), conv(org), conv(loc), date_html(date)
    head = org_h or role_h
    sub = role_h if org_h else ""
    sub_h = (f'<span class="deg">{sub}</span>' if bold_sub else f"<em>{sub}</em>") if sub else ""
    meta = " · ".join(x for x in (sub_h, loc_h) if x)
    return {
        "date": date_h,
        "html": f'<h4>{head}</h4>' + (f'<p class="meta">{meta}</p>' if meta else "") + desc_html(desc),
    }


def render_blocks(blocks, bold_sub=False):
    out, entries, honors = [], [], []

    def flush_entries():
        nonlocal entries
        if entries:
            out.append('<div class="entries">' + "".join(
                f'<article class="entry"><div class="entry-date">{e["date"]}</div>'
                f'<div class="entry-body">{e["html"]}</div></article>' for e in entries) + "</div>")
            entries = []

    def flush_honors():
        nonlocal honors
        if honors:
            rows = "".join(
                f'<article class="entry"><div class="entry-date">{date_html(h[3])}</div><div class="entry-body">'
                f'<h4>{conv(h[0])}</h4><p class="meta">{conv(h[1])}'
                + (f" · {conv(h[2])}" if conv(h[2]) else "") + "</p></div></article>" for h in honors)
            out.append(f'<div class="entries">{rows}</div>')
            honors = []

    for kind, val in blocks:
        if kind != "entry":
            flush_entries()
        if kind != "honor":
            flush_honors()
        if kind == "sub":
            if val.startswith("†") or val.startswith("<sup"):
                out.append(f'<p class="note">{val}</p>')
            else:
                out.append(f'<h3 class="subhead">{val}</h3>')
        elif kind == "entry":
            role, org, loc, date, desc = val
            has_desc = bool(strip_comments(desc).strip())
            if not (conv(org) or conv(loc) or conv(date) or has_desc):
                flush_entries()
                out.append(f'<p class="note">{conv(role)}</p>')  # legend row
            elif not (conv(org) or conv(loc) or conv(date)) and entries:
                # continuation row (e.g. a second degree printed under the first)
                entries[-1]["html"] += f'<h5>{conv(role)}</h5>' + desc_html(desc)
            else:
                entries.append(render_entry(val, bold_sub))
        elif kind == "list":
            lis = []
            for raw, sub in val:
                extra = ""
                if sub:
                    extra = "<ul class=\"venues\">" + "".join(
                        f"<li>{conv(h[0])}, {conv(h[1])}, {conv(h[2])}, {conv(h[3])}</li>"
                        for h in sub) + "</ul>"
                lis.append(f"<li>{conv(raw)}{extra}</li>")
            out.append(f'<ol class="cv-list" reversed>{"".join(lis)}</ol>')
        elif kind == "honor":
            honors.append(val)
    flush_entries()
    flush_honors()
    return "".join(out)


# ================================================================== papers
STATUS = {"Under Review": "review", "Published Peer-Reviewed": "published",
          "In Progress": "progress", "Published Abstracts": "abstract"}
TYPE_LABEL = {"published": "Journal article", "review": "Preprint", "abstract": "Conference abstract"}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def parse_papers():
    text = strip_comments((SECTIONS_DIR / "papers.tex").read_text(encoding="utf-8"))
    papers = []
    for sec in re.split(r"\\cvsubsection\{", text)[1:]:
        sec = "{" + sec
        name, end = read_group(sec, 0)
        status = STATUS.get(plain(conv(name)))
        if not status:
            continue
        body = re.search(r"\\begin\{etaremune\}(.*?)\\end\{etaremune\}", sec[end:], re.S)
        for item in split_items(body.group(1)):
            papers.append(parse_paper(item, status))
    return papers


def parse_paper(raw, status):
    raw = raw.strip()
    idx = raw.index("\\textbf{")
    authors_raw = raw[:idx].strip()
    title, end = read_group(raw, idx + len("\\textbf"))
    rest = raw[end:]
    venue = ""
    m = re.search(r"\\textit\{", rest)
    if m:
        venue = plain(conv(read_group(rest, m.end() - 1)[0])).rstrip(".")
    url = label = ""
    m = re.search(r"\\href\{", rest)
    if m:
        url, j = read_group(rest, m.end() - 1)
        label = plain(conv(read_group(rest, j)[0]))
    date = ""
    m = re.search(r"([A-Za-z]{3})[a-z]* (\d{1,2}), (20\d\d)", rest)
    if m and m.group(1).lower() in MONTHS:
        date = f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    else:
        y = re.search(r"\b(20\d\d)\b", rest)
        if y:
            date = f"{y.group(1)}-01-01"
    authors = [a.strip() for a in authors_raw.split(";") if a.strip()]
    p = {"title": plain(conv(title)).rstrip("."), "title_html": conv(title).rstrip("."), "authors": authors, "venue": venue,
         "url": url.strip(), "label": label, "date": date, "year": date[:4], "status": status}
    first = re.sub(r"[^a-z]", "", plain(conv(authors[0])).split(",")[0].lower())
    words = [w for w in re.findall(r"[a-z0-9]+", p["title"].lower())
             if w not in {"a", "an", "the", "of", "in", "for", "and", "with", "to", "from", "on"}]
    p["slug"] = "-".join([first, p["year"] or "nd"] + words[:4])
    return p


def authors_html(p):
    parts = []
    for a in p["authors"]:
        h = conv(a)
        parts.append(f'<span class="me">{h}</span>' if "vazquez" in plain(h).lower()[:8] else h)
    text = "; ".join(parts)
    return text if plain(text).endswith((".", "†")) else text + "."


def link_html(p):
    if not p["url"]:
        return ""
    return f' <a class="plink" href="{html.escape(p["url"], quote=True)}" target="_blank" rel="noopener">{html.escape(p["label"] or "Link")}</a>'


def status_chip(p):
    label = {"published": "Published", "review": "Under review", "progress": "In preparation",
             "abstract": "Abstract"}[p["status"]]
    return f'<span class="chip {p["status"]}">{label}</span>'


def venue_year(p):
    if p["status"] in ("published", "abstract"):
        return f'<em>{html.escape(p["venue"])}</em>, {p["year"]}' if p["venue"] else p["year"]
    if p["status"] == "review":
        return f'<em>{html.escape(p["venue"])}</em>' if p["venue"] else ""
    return ""


def paper_li(p, abstracts=None, with_type=False):
    ab = (abstracts or {}).get(p["slug"], "")
    ab_html = ""
    if ab:
        ab_html = ('<details class="abs"><summary>Abstract</summary><p>'
                   + html.escape(ab).replace("\\n", "<br>").replace("\n", "<br>") + "</p></details>")
    title = p["title_html"]
    return (f'<li class="paper"><div class="paper-title">{title}</div>'
            f'<div class="paper-authors">{authors_html(p)}</div>'
            f'<div class="paper-venue">{status_chip(p)} {venue_year(p)}{link_html(p)}</div>{ab_html}</li>')


# ================================================================== page shell
def shell(title, path, body, description):
    nav = [("Home", "/"), ("Research", "/research/"), ("Publications", "/publications/"),
           ("CV", "/cv/")]
    cur = ' class="active" aria-current="page"'
    links = "".join(f'<a href="{u}"{cur if u == path else ""}>{t}</a>' for t, u in nav)
    today = datetime.date.today().strftime("%B %d, %Y").replace(" 0", " ")
    ext = " · ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in LINKS)
    full_title = NAME if path == "/" else f"{title} · {NAME}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="icon" href="/assets/icon.png">
<link rel="stylesheet" href="/assets/style.css?v={BUILD_ID}">
</head>
<body>
<header class="site-header"><div class="wrap bar">
  <a class="brand" href="/">{NAME}</a>
  <nav class="nav" aria-label="Main">{links}</nav>
</div></header>
<main>
{body}
</main>
<footer class="site-footer"><div class="wrap foot">
  <div>
    <div class="foot-name">{NAME}</div>
    <div>Department of Biostatistics, Johns Hopkins Bloomberg School of Public Health</div>
    <div><a class="mail" data-u="{EMAIL_USER}" data-d="{EMAIL_DOMAIN}" href="#">{EMAIL_USER} [at] {EMAIL_DOMAIN}</a></div>
  </div>
  <div class="foot-right">
    <div>{ext}</div>
    <div class="muted">Updated {today}</div>
  </div>
</div></footer>
<script src="/assets/site.js?v={BUILD_ID}"></script>
</body>
</html>
"""


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ================================================================== pages
def assign_areas(papers):
    buckets = [[] for _ in AREAS]
    for p in papers:
        if p["status"] == "abstract":
            continue
        t = p["title"].lower()
        for i, area in enumerate(AREAS):
            if any(k in t for k in area["keywords"]) or i == len(AREAS) - 1:
                buckets[i].append(p)
                break
    order = {"published": 0, "review": 1, "progress": 2}
    for b in buckets:
        b.sort(key=lambda p: (order[p["status"]], -int(p["year"] or 0)))
    return buckets


def page_home(papers, abstracts):
    buckets = assign_areas(papers)
    rows = ""
    for n, (area, items) in enumerate(zip(AREAS, buckets), 1):
        rows += (f'<a class="area-row" href="/research/#{slug(area["title"])}">'
                 f'<span class="num">{n:02d}</span><span class="area-title">{area["title"]}</span>'
                 f'<span class="area-text">{html.escape(area["blurb"])}</span></a>')
    recent = sorted([p for p in papers if p["status"] in ("published", "review")],
                    key=lambda p: (p["date"], p["status"] == "published"), reverse=True)[:5]
    recent_html = "".join(paper_li(p) for p in recent)
    link_row = " ".join(f'<a href="{u}" target="_blank" rel="noopener">{t}</a>' for t, u in LINKS)
    body = f"""
<section class="wrap hero">
  <div class="hero-text">
    <p class="overline">Postdoctoral Fellow · Biostatistics · Johns Hopkins</p>
    <h1>{NAME}</h1>
    <p class="lead">I develop statistical methods for incomplete and distributed data, with applications across neurological, pulmonary, and cardiovascular health.</p>
    <p class="cta">
      <a class="btn" href="/research/">Research</a>
      <a class="btn ghost" href="/cv/">CV</a>
    </p>
    <p class="links">{link_row} <a class="mail" data-u="{EMAIL_USER}" data-d="{EMAIL_DOMAIN}" href="#">Email</a></p>
  </div>
  <figure class="portrait"><img src="/assets/avatar.jpg" alt="Portrait of {NAME}" width="900" height="1094"></figure>
</section>

<section class="wrap section" id="about">
  <div class="cols">
    <h2>About</h2>
    <div class="prose">
      <p>I am a Postdoctoral Fellow in the Department of Biostatistics at the <a href="https://publichealth.jhu.edu" target="_blank" rel="noopener">Johns Hopkins Bloomberg School of Public Health</a>, where I hold the <a href="https://facultyaffairs.jhu.edu/initiatives/deia/ppdf/" target="_blank" rel="noopener">Johns Hopkins Provost Postdoctoral Fellowship</a>. I work with <a href="https://www.elizabethstuart.org" target="_blank" rel="noopener">Dr. Elizabeth A. Stuart</a>. I completed my Ph.D. in Biostatistics at the University of North Carolina at Chapel Hill under <a href="https://tpgarcia.github.io" target="_blank" rel="noopener">Dr. Tanya P. Garcia</a>. My dissertation developed robust and efficient estimators for regression models with right-censored covariates, with applications to Huntington disease progression.</p>
      <p>My research focuses on settings where data are incomplete or distributed: censoring, missingness, and data that cannot leave the institutions that collect them. Currently, I am working on federated learning frameworks that let multiple clinical sites draw joint inferences without sharing individual-level data. I collaborate across health domains, including neurological disease, pulmonary health, preterm kidney health, cardiovascular outcomes, and physical activity.</p>
    </div>
  </div>
</section>

<section class="wrap section" id="contact">
  <div class="cols">
    <h2>Get in touch</h2>
    <div class="callout">
      <h3>Open to new collaborations</h3>
      <p>Students: please send a brief email with your research interests, your resume, and your CV. Researchers from other fields are welcome to write about a project.</p>
      <a class="btn mail" data-u="{EMAIL_USER}" data-d="{EMAIL_DOMAIN}" href="#">Email me</a>
    </div>
  </div>
</section>

<section class="wrap section" id="areas">
  <div class="section-head"><h2>Research areas</h2><a class="more" href="/research/">All papers by area</a></div>
  <div class="area-rows">{rows}</div>
</section>

<section class="wrap section" id="recent">
  <div class="section-head"><h2>Recent papers</h2><a class="more" href="/publications/">Full publication list</a></div>
  <ul class="papers">{recent_html}</ul>
</section>
"""
    write("index.html", shell("Home", "/", body,
          "Jesus E. Vazquez, Postdoctoral Fellow in Biostatistics at Johns Hopkins. Statistical methods for incomplete and distributed data."))


def page_research(papers, abstracts):
    buckets = assign_areas(papers)
    nav = "".join(f'<a href="#{slug(a["title"])}">{a["title"]}</a>' for a, b in zip(AREAS, buckets) if b)
    secs = ""
    n = 0
    for area, items in zip(AREAS, buckets):
        if not items:
            continue
        n += 1
        lis = "".join(paper_li(p, abstracts) for p in items)
        secs += (f'<section class="area-block" id="{slug(area["title"])}">'
                 f'<div class="area-head"><span class="num">{n:02d}</span><h2>{area["title"]}</h2></div>'
                 f'<p class="area-desc">{html.escape(area["text"])}</p><ul class="papers">{lis}</ul></section>')
    body = f"""
<section class="wrap page-head">
  <p class="overline">Research</p>
  <h1>Statistical methods for incomplete and distributed data</h1>
  <p class="lead">The work sits under a partial observation framework and is motivated by studies of Huntington disease, pulmonary health, and cardiovascular outcomes. Each area lists its papers: published, under review, and in preparation. † marks senior authorship.</p>
  <nav class="jump" aria-label="Research areas">{nav}</nav>
</section>
<div class="wrap">{secs}</div>
"""
    write("research/index.html", shell("Research", "/research/", body,
          "Research areas and papers: right-censored covariates, causal inference, federated learning, and Huntington disease applications."))


def page_publications(papers, abstracts):
    pubs = [p for p in papers if p["status"] in ("published", "review", "abstract")]
    counts = {k: sum(1 for p in pubs if p["status"] == k) for k in ("published", "review", "abstract")}
    groups = []
    rev = [p for p in pubs if p["status"] == "review"]
    if rev:
        groups.append(("Under review", rev))
    years = sorted({p["year"] for p in pubs if p["status"] != "review"}, reverse=True)
    for y in years:
        items = [p for p in pubs if p["status"] != "review" and p["year"] == y]
        items.sort(key=lambda p: (p["date"], p["status"] == "published"), reverse=True)
        groups.append((y, items))
    key = {"published": "journal", "review": "preprint", "abstract": "abstract"}
    html_groups = ""
    for label, items in groups:
        lis = ""
        for p in items:
            text = html.escape(plain(" ".join([p["title"], " ".join(conv(a) for a in p["authors"]), p["venue"]])).lower(), quote=True)
            ab = abstracts.get(p["slug"], "")
            li = paper_li(p, abstracts)
            li = li.replace('<li class="paper">', f'<li class="paper" data-type="{key[p["status"]]}" data-text="{text}">', 1)
            lis += li
        html_groups += f'<section class="pub-group"><h2 class="year">{label}</h2><ul class="papers">{lis}</ul></section>'
    body = f"""
<section class="wrap page-head">
  <p class="overline">Publications</p>
  <h1>Papers and abstracts</h1>
  <p class="lead">Journal articles, preprints and papers under review, and conference abstracts. Papers still in preparation are listed on the <a href="/research/">research page</a>. A current list is also on <a href="{LINKS[0][1]}" target="_blank" rel="noopener">Google Scholar</a>.</p>
  <div class="filters" role="group" aria-label="Filter publications">
    <button class="pill active" data-filter="all">All <span>{len(pubs)}</span></button>
    <button class="pill" data-filter="journal">Journal articles <span>{counts["published"]}</span></button>
    <button class="pill" data-filter="preprint">Preprints <span>{counts["review"]}</span></button>
    <button class="pill" data-filter="abstract">Conference abstracts <span>{counts["abstract"]}</span></button>
    <input class="search" type="search" placeholder="Search title, author, journal" aria-label="Search publications">
  </div>
  <p class="empty" hidden>No matching publications.</p>
</section>
<div class="wrap pubs">{html_groups}</div>
"""
    write("publications/index.html", shell("Publications", "/publications/", body,
          "Journal articles, preprints, and conference abstracts by Jesus E. Vazquez."))


def page_cv(sections):
    toc = "".join(f'<a href="#{slug(s["title"])}">{s["title"]}</a>' for s in sections)
    secs = "".join(
        f'<section class="cv-section" id="{slug(s["title"])}"><h2>{s["title"]}</h2>{render_blocks(s["blocks"], s["file"] == "education")}</section>'
        for s in sections)
    body = f"""
<section class="wrap page-head">
  <p class="overline">Curriculum vitae</p>
  <h1>{NAME}</h1>
  <p class="lead">The page below is generated from the same LaTeX files as the PDF, so the two stay in step.</p>
  <p class="cta"><a class="btn" href="/cv/VAZQUEZ-CV.pdf">Download PDF</a></p>
</section>
<div class="wrap cv-layout">
  <nav class="cv-toc" aria-label="CV sections">{toc}</nav>
  <div class="cv-main">{secs}</div>
</div>
"""
    write("cv/index.html", shell("CV", "/cv/", body, "Curriculum vitae of Jesus E. Vazquez."))
    if PDF_SRC.exists():
        shutil.copy(PDF_SRC, OUT / "cv" / "VAZQUEZ-CV.pdf")


def page_extras():
    body = """
<section class="wrap page-head">
  <p class="overline">Page not found</p>
  <h1>That page does not exist</h1>
  <p class="lead">Try the <a href="/">home page</a>, the <a href="/research/">research page</a>, or the <a href="/publications/">publications</a>.</p>
</section>
"""
    write("404.html", shell("Not found", "/404", body, "Page not found."))
    # Old Hugo URLs that may still be linked somewhere.
    write("_redirects", "/resume/VAZQUEZ-CV.pdf /cv/VAZQUEZ-CV.pdf 301\n"
          "/publication/* /publications/ 301\n/publication-type/* /publications/ 301\n"
          "/event/* / 301\n/talk/* / 301\n/authors/* / 301\n/tag/* / 301\n/category/* / 301\n")


def main():
    abstracts = json.loads(ABSTRACTS.read_text(encoding="utf-8")) if ABSTRACTS.exists() else {}
    papers = parse_papers()
    sections = parse_cv()
    page_home(papers, abstracts)
    page_research(papers, abstracts)
    page_publications(papers, abstracts)
    page_cv(sections)
    page_extras()
    print(f"{len(papers)} papers, {len(sections)} CV sections written to {OUT}")
    if _unknown:
        print("Unhandled LaTeX commands (ignored):", ", ".join(sorted(_unknown)), file=sys.stderr)


if __name__ == "__main__":
    main()
