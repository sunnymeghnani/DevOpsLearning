"""Decision drills page for the website, generated from drills/*.json (see drills/SPEC.md).

One virtual page, "drills.md" (sidebar group "Labs", title "Decision drills"):

  * "How the drills work" and the four meters (indexed by the site search);
  * one "## <level>" section per level with a card per drill: title, track, minutes, source org
    and year, the role, the brief and the source link. Each card has the id "drill.<id>", so a
    "#drill.<id>" link works with or without the script;
  * per drill, a <template> with the debrief (what really happened, lessons, commands, "Practise
    this"). It is part of the module body, so build_site.rewrite_links turns its handbook links
    ("file.md#slug") into in-page anchors. Lab links carry data-lab and get their "#lab.<id>"
    href from the script (the lab rooms are views, not elements);
  * the steps and choices, rendered to HTML at build time, embedded once as
    <script type="application/json" id="drill-data">. The page script plays them in a
    full-screen view (meters, choices, "What happened?", end screen).

Nothing here needs Docker or the network: drills work in index.html and in the artifact.
"""
import html
import json
import os
import re

import markdown
from markdown.extensions.toc import slugify as _toc_slugify, unique as _toc_unique

from page_slim import minify_script

DRILLS_FILE = "drills.md"
DRILLS_TITLE = "Decision drills"
DRILLS_DIR = "drills"
ROOMS_DIR = os.path.join("labs", "rooms")
LEVELS = [("L0", "Fresher"), ("L1", "Junior"), ("L2", "Mid-level"), ("L3", "Senior"), ("L4", "Senior / Lead")]
METERS = ("service", "time", "evidence", "trust")
VERDICTS = ("best", "good", "risky", "bad")
DRILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")
PROMPT_RE = re.compile(r"(\$|[\w.-]+@[\w.-]+:[^$#\s]*[$#]) (.*)")      # "$ cmd" or "ops@db1:~$ cmd"
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December")


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def _ext(out):
    """External links open in a new tab (needed inside the artifact frame too)."""
    return re.sub(r'<a href="(https?://[^"]+)"(?![^>]*\btarget=)', r'<a href="\1" target="_blank" rel="noopener"', out)


def _links(out):
    """For the JSON data: as _ext, and links to .md files (which build_site cannot rewrite there) become text."""
    out = _ext(out)
    return re.sub(r'<a href="(?:\./)?[\w.-]+\.md(?:#[^"]*)?"[^>]*>(.*?)</a>', r"\1", out, flags=re.S)


def _md(text):
    """Markdown without raw HTML: "<id>" or "</script>" in a drill stays text."""
    md = markdown.Markdown(extensions=["fenced_code", "tables"])
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    return md.convert(str(text or "")).strip()


def _md_inline(text):
    out = _md(text)
    m = re.fullmatch(r"<p>(.*)</p>", out, re.S)
    return m.group(1) if m else out


def _date(iso):
    """'2017-01-31' -> '31 January 2017' (anything else is returned as it is)."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    if not m or not 1 <= int(m.group(2)) <= 12:
        return str(iso or "")
    return f"{int(m.group(3))} {MONTHS[int(m.group(2)) - 1]} {m.group(1)}"


def json_for_script(obj):
    """JSON that is safe inside <script type="application/json">: every "<" is escaped, so there is no
    "</script", no "<!--" and nothing build_site's HTML rewriting (which keys on "<tag") could touch.
    ">" and "&" need no escape in script data and stay as they are (the page is near its size limit)."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def drills_dir(here, folder=None):
    return folder or os.path.join(here, DRILLS_DIR)


def read_order(folder):
    try:
        with open(os.path.join(folder, "ORDER"), encoding="utf-8") as f:
            lines = [ln.split("#", 1)[0].strip() for ln in f]
    except OSError:
        return []
    return [ln for ln in lines if ln]


def load_drills(here, folder=None):
    """Drills from <folder>/*.json (files starting with "_" are skipped), in page order:
    by level, then by drills/ORDER, then by id. Files that do not parse or lack the basics are skipped
    (tests/test_drills.py reports them)."""
    folder = drills_dir(here, folder)
    if not os.path.isdir(folder):
        return []
    drills = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        if (not isinstance(d, dict) or not DRILL_ID_RE.match(str(d.get("id", ""))) or not d.get("title")
                or not isinstance(d.get("steps"), list) or not d["steps"]
                or not all(isinstance(s, dict) and s.get("choices") for s in d["steps"])):
            continue
        drills.append(d)
    order = {k: i for i, k in enumerate(read_order(folder))}
    levels = {k: i for i, (k, _) in enumerate(LEVELS)}
    drills.sort(key=lambda d: (levels.get(d.get("level"), len(levels)), order.get(d["id"], len(order)), d["id"]))
    return drills


def drill_count(here, folder=None):
    return len(load_drills(here, folder))


def level_title(key):
    name = dict(LEVELS).get(key)
    return f"{key} · {name}" if name else (str(key) or "Other")


def _tracks(here):
    try:
        with open(os.path.join(here, "roadmap.json"), encoding="utf-8") as f:
            return {t["id"]: t["name"] for t in json.load(f).get("tracks", [])}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def _rooms(here):
    """lab directory name or room id -> (room id, title)."""
    root, out = os.path.join(here, ROOMS_DIR), {}
    if not os.path.isdir(root):
        return out
    for name in sorted(os.listdir(root)):
        try:
            with open(os.path.join(root, name, "room.json"), encoding="utf-8") as f:
                r = json.load(f)
        except (OSError, ValueError):
            continue
        if r.get("id"):
            out[name] = out[str(r["id"])] = (str(r["id"]), str(r.get("title", r["id"])))
    return out


# --------------------------------------------------------------------------- #
# handbook headings: the same ids the site gives them (markdown toc slugs, made unique per module)
# --------------------------------------------------------------------------- #
def _norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", str(s).lower()))


def _plain(md_text):
    return html.unescape(re.sub(r"<[^>]+>", "", _md_inline(md_text))).strip()


_HEADS = {}


def module_headings(here, fname):
    """(module title, [(heading text, slug)]) for a handbook module; ([], "") if it is missing.
    The first "# " line is the module title (build_site drops it before rendering)."""
    key = (here, fname)
    if key in _HEADS:
        return _HEADS[key]
    path = os.path.join(here, fname)
    if not re.fullmatch(r"[\w.-]+\.md", fname) or not os.path.isfile(path):
        _HEADS[key] = ("", [])
        return _HEADS[key]
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().split("\n")
    title, heads, used, fence, first = "", [], set(), None, True
    for line in lines:
        st = line.lstrip()
        if fence is None and st.startswith(("```", "~~~")):
            fence = st[:3]
            continue
        if fence:
            if st.startswith(fence):
                fence = None
            continue
        m = re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        text = _plain(m.group(2))
        if first and len(m.group(1)) == 1:
            first = False
            title = re.sub(r"^\d+\s*[—–-]\s*", "", text)
            continue
        first = False
        heads.append((text, _toc_unique(_toc_slugify(text, "-"), used)))
    _HEADS[key] = (title or os.path.splitext(fname)[0], heads)
    return _HEADS[key]


def find_heading(here, fname, heading):
    """(heading text, slug) for the heading of `fname` named `heading`: an exact match of the
    normalised text first, then the first heading that contains it. None if there is none."""
    _, heads = module_headings(here, fname)
    want = _norm(_plain(heading))
    if not want:
        return None
    for text, slug in heads:
        if _norm(text) == want:
            return text, slug
    for text, slug in heads:
        if want in _norm(text):
            return text, slug
    return None


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
def _source_link(src):
    url = str(src.get("url", ""))
    label = src.get("label") or url
    return (f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(label)}</a>'
            if url.startswith("https://") else _esc(label))


def _card(d, tracks):
    src = d.get("source") or {}
    track = tracks.get(d.get("track"), d.get("track", ""))
    year = str(src.get("date", ""))[:4]
    org = " ".join(x for x in (_esc(src.get("org", "")), _esc(year)) if x)
    chips = [f'<span class="chip chip-level">{_esc(d.get("level", ""))}</span>']
    if track:
        chips.append(f'<span class="chip">{_esc(track)}</span>')
    if d.get("minutes"):
        chips.append(f'<span class="chip">⏱ {_esc(d["minutes"])} min</span>')
    chips.append(f'<span class="chip">{len(d["steps"])} steps</span>')
    return (f'<article class="drill-card" id="drill.{_esc(d["id"])}" data-drill="{_esc(d["id"])}" '
            f'data-title="{_esc(d["title"])}" data-level="{_esc(d.get("level", ""))}" data-track="{_esc(track)}" '
            f'data-minutes="{_esc(d.get("minutes", ""))}">'
            f'<div class="drill-card-top">{"".join(chips)}<span class="drill-best" data-best></span></div>'
            f'<h3>{_esc(d["title"])}</h3>'
            + (f'<p class="drill-role">{_md_inline(d["role"])}</p>' if d.get("role") else "")
            + f'<div class="drill-brief">{_ext(_md(d.get("brief", "")))}</div>'
            f'<p class="drill-src">Source: {_source_link(src)}' + (f" · {org}" if org else "") + "</p>"
            f'<div class="drill-card-foot"><button type="button" class="drill-play" data-drill="{_esc(d["id"])}" hidden>'
            "▶ Play the drill</button></div></article>")


def _command_cards(commands, here):
    """command -> Command Decoder card id ("cmd-…"), for the commands the decoder knows."""
    try:
        from command_decoder import key_index, load_cards, match_text
        index, sub_tools = key_index(load_cards(here)[1])
    except Exception:   # the decoder is optional for the drills page
        return {}
    out = {}
    for cmd in commands:
        hits = match_text("```bash\n" + str(cmd) + "\n```\n", index, sub_tools)
        if hits:
            out[cmd] = hits[0]["id"]
    return out


def _template(d, here, rooms, cmd_cards):
    src, deb, pr = d.get("source") or {}, d.get("debrief") or {}, d.get("practise") or {}
    when = _date(src.get("date"))
    meta = ", ".join(x for x in (_esc(src.get("org", "")), _esc(when)) if x)
    out = [f'<template data-drill="{_esc(d["id"])}"><div class="drill-deb">',
           "<h4>What really happened</h4>", _ext(_md(deb.get("what_happened", ""))),
           f'<p class="drill-src">Source: {_source_link(src)}' + (f" ({meta})" if meta else "")
           + (f' · read on {_esc(src["read_on"])}' if src.get("read_on") else "") + "</p>"]
    if deb.get("lessons"):
        out.append("<h4>Lessons</h4><ul>" + "".join(f"<li>{_ext(_md_inline(x))}</li>" for x in deb["lessons"]) + "</ul>")
    if deb.get("commands"):
        items = []
        for c in deb["commands"]:
            card = cmd_cards.get(c)
            dec = f' <a class="drill-dec" href="#{_esc(card)}">🔍 decode</a>' if card else ""
            items.append(f"<li><code>{_esc(c)}</code>{dec}</li>")
        out.append('<h4>Commands</h4><ul class="drill-cmds">' + "".join(items) + "</ul>")
    prac = []
    for lab in pr.get("labs") or []:
        rid, title = rooms.get(str(lab), (str(lab), str(lab)))
        prac.append(f'<li>🧪 Lab: <a class="drill-lab" data-lab="{_esc(rid)}">{_esc(title)}</a></li>')
    for h in pr.get("handbook") or []:
        fname, heading = str(h.get("file", "")), str(h.get("heading", ""))
        mod_title, _ = module_headings(here, fname)
        hit = find_heading(here, fname, heading)
        href = f"{fname}#{hit[1]}" if hit else fname
        label = f"{mod_title} › {hit[0] if hit else heading}"
        prac.append(f'<li>📖 Handbook: <a href="{_esc(href)}" data-heading="{_esc(heading)}">{_esc(label)}</a></li>')
    for s in pr.get("sites") or []:
        url = str(s.get("url", ""))
        if url.startswith("https://"):
            prac.append(f'<li>🌐 <a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(s.get("label", url))}</a></li>')
    if prac:
        out.append('<h4>Practise this</h4><ul class="drill-prac">' + "".join(prac) + "</ul>")
    out.append("</div></template>")
    return "".join(out)


def _evidence(text, cmd):
    """Terminal-frame HTML: "$ " lines as prompt + command. evidence_cmd is shown as the first prompt
    line unless the evidence already has its own prompt lines."""
    text, cmd = str(text or "").rstrip("\n"), str(cmd or "").strip()
    lines = text.split("\n") if text else []
    if cmd and not any(PROMPT_RE.match(ln) for ln in lines):
        lines.insert(0, "$ " + cmd)
    out = []
    for ln in lines:
        m = PROMPT_RE.match(ln)
        out.append(f"<u>{html.escape(m.group(1), quote=False)}</u> <b>{html.escape(m.group(2), quote=False)}</b>" if m
                   else html.escape(ln, quote=False))
    return "\n".join(out)


def _data(d):
    """What the player needs that is not on the card: the steps, rendered."""
    steps = []
    for s in d["steps"]:
        steps.append({
            "situation": _links(_md(s.get("situation", ""))),
            "evidence": _evidence(s.get("evidence"), s.get("evidence_cmd")),
            "choices": [{
                "text": _links(_md_inline(c.get("text", ""))),
                "verdict": c.get("verdict") if c.get("verdict") in VERDICTS else "risky",
                "effect": [int((c.get("effect") or {}).get(k, 0) or 0) for k in METERS],
                "why": _links(_md(c.get("why", ""))),
            } for c in s["choices"]],
        })
    return {"id": d["id"], "steps": steps}


def drills_markdown(here, folder=None):
    """Markdown (with raw HTML blocks) for the virtual page drills.md."""
    drills = load_drills(here, folder)
    tracks, rooms = _tracks(here), _rooms(here)
    cmd_cards = _command_cards([c for d in drills for c in (d.get("debrief") or {}).get("commands") or []], here)
    out = [
        f"# {DRILLS_TITLE}", "",
        f'<p class="drill-lead">Play a real outage at the on-call engineer\'s level: {len(drills)} '
        f'drill{"s" if len(drills) != 1 else ""}, each adapted from a public post-mortem, incident report or '
        'solved issue, with the source linked. Read the evidence, pick a move, see what it did, and at the end '
        'read what the engineers really found and fixed. No Docker and no network needed.</p>', "",
        "## How the drills work", "",
        "- **One incident, 3–5 decisions.** Each step shows what you see now (an alert, a user report, a "
        "log or command output) and 3–4 moves. Pick one: the moves lock, the verdict shows "
        "(best, good, risky or bad) and **What happened?** explains it. **Why not the others?** "
        "explains the moves you did not pick.",
        "- **Four meters, all starting at 50.** *Service*: users can work. *Time*: time to restore. "
        "*Evidence*: you know why it broke. *Trust*: your team and your users. If **Service** or **Trust** "
        "drops to 0, the incident escalates past you and the drill ends early: try again.",
        "- **Score and stars.** The score is the average of the four meters at the end. Three stars: the best "
        "move at every step. Two: only best or good moves. Your best score per drill stays in this browser.",
        "- **Then the real story.** The debrief tells what really happened, with the source and its date, the "
        "lessons, the commands, and where to practise next: a lab room, a handbook section or an outside site.",
        "- **Keys.** 1–4 pick a move, Enter goes on, Esc closes the drill. Link a drill with `#drill.<id>`.",
        "",
    ]
    groups = []
    for d in drills:
        if not groups or groups[-1][0] != d.get("level"):
            groups.append((d.get("level"), []))
        groups[-1][1].append(d)
    for key, items in groups:
        mins = sum(int(d.get("minutes") or 0) for d in items)
        out += [f"## {level_title(key)}", "",
                f'<p class="drill-meta">{len(items)} drill{"s" if len(items) != 1 else ""} · about {mins} min.</p>', "",
                '<div class="drill-grid">' + "".join(_card(d, tracks) for d in items) + "</div>", ""]
    if not drills:
        out += ["## Drills", "", "No drills are built yet (`drills/` has no drill files).", ""]
    out += ['<div class="drill-store" hidden>' + "".join(_template(d, here, rooms, cmd_cards) for d in drills) + "</div>", "",
            '<script type="application/json" id="drill-data">' + json_for_script([_data(d) for d in drills]) + "</script>", ""]
    return "\n".join(out)


DRILLS_CSS = r"""
/* ===== decision drills (drills_site.py) ===== */
.drill-lead { font-size: 16px; }
.drill-meta { color: var(--fg-dim); font-size: 13.5px; margin: -2px 0 10px; }
.drill-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 14px; margin: 8px 0 26px; }
.drill-card { display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; border-radius: 16px; background: var(--card);
  border: 1px solid color-mix(in srgb, var(--tone) 22%, var(--card-border));
  box-shadow: inset 0 1px 0 var(--card-hi), 0 18px 34px -30px var(--tone); transition: box-shadow .2s, transform .2s; }
.drill-card:hover { box-shadow: inset 0 1px 0 var(--card-hi), 0 22px 40px -24px var(--tone); transform: translateY(-1px); }
.drill-card-top { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; }
.drill-card .chip { font-size: 11.5px; padding: 1px 8px; }
.drill-best:empty { display: none; }
.drill-best { margin-left: auto; font-size: 11.5px; font-weight: 700; border-radius: 999px; padding: 1px 9px; color: var(--on-accent); background: var(--accent2); }
.mod-section .drill-card h3 { margin: 2px 0 0; font-size: 16px; color: var(--fg); }
.drill-role { margin: 0; font-size: 13.5px; font-weight: 600; color: var(--tone); }
.drill-card .drill-brief p { margin: 0 0 4px; font-size: 13.5px; line-height: 1.5; color: var(--fg-dim); }
.drill-src { margin: 0; font-size: 12.5px; color: var(--fg-dim); overflow-wrap: anywhere; }
.drill-card-foot { margin-top: auto; padding-top: 6px; }
.drill-play, .drill-big { font: inherit; font-size: 14px; font-weight: 650; cursor: pointer; border-radius: 9px; padding: 7px 16px;
  border: 1px solid var(--accent); color: var(--on-accent); background: var(--accent); }
.drill-play:hover, .drill-big:hover { filter: brightness(1.08); }
.drill-big:disabled { opacity: .45; cursor: default; filter: none; }
.drill-big.is-over { background: var(--danger); border-color: var(--danger); }
.drill-view button:focus-visible, .drill-play:focus-visible, .drill-view a:focus-visible, .drill-view summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* the player: full screen above the page */
html.drill-open, html.drill-open body { overflow: hidden; }
.drill-view { position: fixed; inset: 0; z-index: 95; display: flex; flex-direction: column; background: var(--bg); color: var(--fg); outline: 0; }
.drill-bar { display: flex; align-items: center; gap: 8px 12px; padding: 8px 12px; background: var(--bg2); border-bottom: 1px solid var(--border); }
.drill-v-head { flex: 1; min-width: 0; }
.drill-v-kicker { font-size: 11px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--t-teal); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.drill-view h2 { margin: 0; padding: 0; border: 0; font-size: 18px; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; outline: 0; }
.drill-meters { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px 18px; padding: 10px max(16px, calc(50% - 380px)); background: var(--bg2); border-bottom: 1px solid var(--border); }
.drill-m { position: relative; display: grid; grid-template-columns: 1fr auto; align-items: baseline; font-size: 12.5px; font-weight: 700; }
.drill-m b { font: 800 14px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.drill-m-bar { grid-column: 1 / -1; height: 8px; margin-top: 4px; border-radius: 99px; background: var(--bg3); border: 1px solid var(--border); overflow: hidden; }
.drill-m-bar i { display: block; height: 100%; width: 50%; border-radius: inherit; background: linear-gradient(90deg, var(--t-teal), var(--accent2)); transition: width .6s cubic-bezier(.2, .7, .2, 1), background .3s; }
.drill-m.is-low .drill-m-bar i { background: linear-gradient(90deg, var(--danger), var(--t-amber)); }
.drill-m.is-low b { color: var(--danger); }
.drill-d { position: absolute; right: 0; top: -15px; font-size: 11.5px; font-weight: 800; opacity: 0; pointer-events: none; }
.drill-d.up { color: var(--accent2); } .drill-d.down { color: var(--danger); }
.drill-d.show { animation: drill-pop 1.6s ease-out; }
@keyframes drill-pop { 0% { opacity: 0; transform: translateY(6px); } 15%, 70% { opacity: 1; transform: none; } 100% { opacity: 0; } }
.drill-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; }
.drill-inner { max-width: 760px; margin: 0 auto; padding: 18px 16px 60px; }
.drill-k { margin: 0 0 6px; font-size: 12px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--fg-dim); outline: 0; }
.drill-inner .drill-role { font-size: 15px; margin-bottom: 10px; }
.drill-sit, .drill-inner .drill-brief { padding: 12px 16px; border-radius: 14px; border: 1px solid var(--card-border); border-left: 4px solid var(--t-amber);
  background: linear-gradient(90deg, color-mix(in srgb, var(--t-amber) 10%, var(--bg2)), var(--bg2) 80%); }
.drill-sit p, .drill-inner .drill-brief p { margin: 6px 0; }
.drill-view pre { margin: 12px 0; padding: 38px 16px 14px; border-radius: 12px; color: var(--term-fg); border: 1px solid var(--term-border); font-size: 13px;
  background: radial-gradient(circle at 17px 13.5px, #ff5f57 0 4.2px, transparent 4.8px), radial-gradient(circle at 33px 13.5px, #febc2e 0 4.2px, transparent 4.8px),
    radial-gradient(circle at 49px 13.5px, #28c840 0 4.2px, transparent 4.8px), linear-gradient(var(--term-border), var(--term-border)) 0 27px / 100% 1px no-repeat,
    linear-gradient(var(--term-bar), var(--term-bar)) 0 0 / 100% 27px no-repeat, var(--term-bg); }
.drill-view pre code { background: none; border: 0; padding: 0; color: inherit; font-size: inherit; }
.drill-view pre b { color: var(--term-cmd); } .drill-view pre u { text-decoration: none; color: var(--term-prompt); }
.drill-choices { list-style: none; margin: 14px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.drill-c { width: 100%; display: flex; align-items: flex-start; gap: 10px; text-align: left; font: inherit; font-size: 14.5px; line-height: 1.45; cursor: pointer;
  padding: 10px 12px; border-radius: 12px; color: var(--fg); background: var(--card); border: 1px solid var(--card-border); transition: border-color .15s, background .15s, opacity .2s; }
.drill-c:hover:not(:disabled) { border-color: var(--accent); background: var(--accent-soft); }
.drill-c:disabled { cursor: default; opacity: .55; }
.drill-n { flex: none; width: 24px; height: 24px; border-radius: 7px; display: grid; place-items: center; font-size: 12.5px; font-weight: 800; background: var(--bg3); color: var(--fg-dim); }
.drill-ct { flex: 1; min-width: 0; }
.drill-c.is-picked { opacity: 1; border-width: 2px; padding: 9px 11px; border-color: var(--v); background: color-mix(in srgb, var(--v) 12%, var(--card)); }
.drill-c.is-picked .drill-n { background: var(--v); color: var(--bg); }
.drill-tag { display: inline-block; font-size: 11.5px; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; border-radius: 999px; padding: 1px 9px;
  color: var(--v); border: 1px solid color-mix(in srgb, var(--v) 45%, transparent); background: color-mix(in srgb, var(--v) 12%, transparent); white-space: nowrap; }
.v-best { --v: var(--accent2); } .v-good { --v: var(--t-teal); } .v-risky { --v: var(--t-amber); } .v-bad { --v: var(--danger); }
.drill-res { margin-top: 14px; padding: 12px 16px; border-radius: 14px; border: 1px solid color-mix(in srgb, var(--v) 45%, var(--card-border));
  background: linear-gradient(120deg, color-mix(in srgb, var(--v) 11%, var(--bg2)), var(--bg2) 70%); }
.drill-view h4 { margin: 4px 0 6px; font-size: 16px; color: var(--fg); }
.drill-res p { margin: 6px 0; }
.drill-deltas { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 4px; padding: 0; font-size: 12.5px; font-weight: 700; }
.drill-deltas li { padding: 1px 8px; border-radius: 999px; background: var(--bg3); color: var(--fg-dim); }
.drill-deltas .up { color: var(--accent2); } .drill-deltas .down { color: var(--danger); }
.drill-others { margin-top: 8px; border: 1px dashed var(--border); border-radius: 10px; padding: 6px 12px; font-size: 14px; }
.drill-others summary { cursor: pointer; font-weight: 650; color: var(--fg-dim); }
.drill-others ul { margin: 6px 0 2px; padding-left: 18px; }
.drill-others li { margin: 8px 0; } .drill-others li p { margin: 3px 0; }
.drill-nav { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; margin-top: 16px; }
.drill-nav .mbtn { white-space: normal; text-align: left; }
.drill-gate { font-size: 13px; color: var(--fg-dim); }
.drill-end { padding: 16px 18px; border-radius: 16px; border: 1px solid color-mix(in srgb, var(--accent2) 45%, var(--card-border));
  background: linear-gradient(120deg, color-mix(in srgb, var(--accent2) 12%, var(--bg2)), var(--bg2) 70%); }
.drill-end.is-over { border-color: color-mix(in srgb, var(--danger) 50%, var(--card-border)); background: linear-gradient(120deg, color-mix(in srgb, var(--danger) 12%, var(--bg2)), var(--bg2) 70%); }
.drill-end h3 { margin: 0 0 4px; font-size: 22px; color: var(--fg); outline: 0; }
.drill-stars { font-size: 28px; letter-spacing: 4px; color: var(--t-amber); }
.drill-stars s { text-decoration: none; color: var(--fg-dim); opacity: .35; }
.drill-trail { margin: 10px 0 0; padding-left: 22px; font-size: 14px; } .drill-trail li { margin: 4px 0; }
.drill-deb { margin-top: 18px; }
.drill-deb h4 { margin: 18px 0 6px; color: var(--t-teal); }
.drill-deb p { margin: 6px 0; }
.drill-cmds { padding-left: 18px; } .drill-cmds li { margin: 4px 0; }
.drill-dec { font-size: 12.5px; white-space: nowrap; }
.drill-prac { list-style: none; padding: 0; } .drill-prac li { margin: 6px 0; }
@media (prefers-reduced-motion: reduce) {
  .drill-card, .drill-c, .drill-m-bar i { transition: none; } .drill-d.show { animation: none; opacity: 1; }
}
"""


DRILLS_SCRIPT = r"""<script>
/* decision drills (drills_site.py): plays the drills embedded in #drill-data in a full-screen view */
(function () {
  "use strict";
  var dataEl = document.getElementById("drill-data");
  if (!dataEl) return;
  var D;
  try { D = JSON.parse(dataEl.textContent); } catch (_) { return; }
  var byId = {}, root = document.documentElement;
  D.forEach(function (d, i) { d.n = i; byId[d.id] = d; });
  var NAMES = ["Service", "Time", "Evidence", "Trust"];
  var VERD = { best: "Best move", good: "Good move", risky: "Risky move", bad: "Bad move" };
  var KEY = "drills.best";
  var S = { d: null, i: 0, m: null, picks: [], order: null, over: false, view: null, opener: null, raf: 0 };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function calm() { try { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (_) { return false; } }
  function card(id) { return document.getElementById("drill." + id); }
  function attr(id, a) { var c = card(id); return c ? c.getAttribute("data-" + a) || "" : ""; }
  function bests() { try { var b = JSON.parse(window.localStorage.getItem(KEY) || "{}"); return b && typeof b === "object" ? b : {}; } catch (_) { return {}; } }
  function keep(id, score, stars) {
    try {
      var b = bests(), o = b[id] || { s: -1, r: 0 };
      b[id] = { s: Math.max(o.s, score), r: Math.max(o.r || 0, stars) };
      window.localStorage.setItem(KEY, JSON.stringify(b));
      return score > o.s && o.s >= 0;
    } catch (_) { return false; }
  }
  function starText(n) { return "★★★".slice(0, n) + "☆☆☆".slice(0, 3 - n); }
  function paintCards() {
    var b = bests();
    document.querySelectorAll(".drill-card").forEach(function (c) {
      var o = b[c.getAttribute("data-drill")], el = c.querySelector("[data-best]");
      if (el) el.textContent = o && o.s >= 0 ? "Best " + o.s + " · " + starText(o.r || 0) : "";
      var p = c.querySelector(".drill-play");
      if (p) { p.hidden = false; p.textContent = o ? "▶ Play again" : "▶ Play the drill"; }
    });
  }

  /* ---------- the view ---------- */
  function build() {
    var v = document.createElement("div");
    v.className = "drill-view"; v.hidden = true; v.tabIndex = -1;
    v.setAttribute("role", "dialog"); v.setAttribute("aria-modal", "true"); v.setAttribute("aria-labelledby", "drill-v-title");
    v.setAttribute("data-tone", "teal");
    var m = "";
    NAMES.forEach(function (n, k) {
      m += '<div class="drill-m" data-k="' + k + '"><span>' + n + '</span><b>50</b><span class="drill-m-bar" role="meter" aria-label="' + n +
        '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="50"><i></i></span><span class="drill-d" aria-hidden="true"></span></div>';
    });
    v.innerHTML = '<header class="drill-bar"><button type="button" class="mbtn" data-act="close">← Drills</button>' +
      '<div class="drill-v-head"><div class="drill-v-kicker"></div><h2 id="drill-v-title" tabindex="-1"></h2></div>' +
      '<button type="button" class="mbtn" data-act="theme" title="Toggle light / dark theme" aria-label="Toggle theme">🌓</button>' +
      '<button type="button" class="mbtn" data-act="close" title="Close (Esc)" aria-label="Close">✕</button></header>' +
      '<div class="drill-meters">' + m + '</div><div class="drill-body"><div class="drill-inner"></div></div>';
    document.body.appendChild(v);
    v.addEventListener("click", onClick);
    v.addEventListener("keydown", onKey);
    S.view = v;
    return v;
  }
  function $(sel) { return S.view.querySelector(sel); }
  function inner() { return $(".drill-inner"); }

  function meters(deltas) {
    var from = S.shown || [50, 50, 50, 50], to = S.m.slice(), t0 = 0, dur = calm() ? 0 : 600;
    S.shown = to;
    cancelAnimationFrame(S.raf);
    S.view.querySelectorAll(".drill-m").forEach(function (el, k) {
      el.querySelector("i").style.width = to[k] + "%";
      var bar = el.querySelector(".drill-m-bar");
      bar.setAttribute("aria-valuenow", to[k]);
      el.classList.toggle("is-low", to[k] <= 20);
      var d = el.querySelector(".drill-d"), x = deltas ? deltas[k] : 0;
      d.className = "drill-d";
      if (x) { void d.offsetWidth; d.textContent = (x > 0 ? "+" : "−") + Math.abs(x); d.className = "drill-d show " + (x > 0 ? "up" : "down"); }
    });
    var bs = S.view.querySelectorAll(".drill-m b");
    function frame(t) {
      if (!t0) t0 = t;
      var p = dur ? Math.min(1, (t - t0) / dur) : 1;
      bs.forEach(function (b, k) { b.textContent = Math.round(from[k] + (to[k] - from[k]) * p); });
      if (p < 1) S.raf = requestAnimationFrame(frame);
    }
    if (dur) S.raf = requestAnimationFrame(frame); else frame(1);
  }
  function screen(html, focusSel) {
    var el = inner();
    el.innerHTML = html;
    $(".drill-body").scrollTop = 0;
    var f = focusSel && el.querySelector(focusSel);
    if (f) f.focus({ preventScroll: true });
    return el;
  }

  function open(id, fromHash) {
    var d = byId[id];
    if (!d) return;
    var v = S.view || build();
    /* Back closes it */
    if (!fromHash) { try { if (v.hidden) history.pushState({ drill: 1 }, "", "#drill." + id); else history.replaceState(history.state, "", "#drill." + id); } catch (_) { /* ignore */ } }
    S.opener = S.opener || document.activeElement;
    S.d = d;
    $(".drill-v-kicker").textContent = ["Decision drill", attr(id, "level"), attr(id, "track"), attr(id, "minutes") ? "⏱ " + attr(id, "minutes") + " min" : ""].filter(Boolean).join(" · ");
    $("#drill-v-title").textContent = attr(id, "title") || id;
    v.hidden = false; root.classList.add("drill-open");
    var e = fromHash && history.state && history.state.end; /* Back from a debrief link: the same end screen */
    if (e && e.id === id) { reset(); S.m = e.m; S.picks = e.p; S.i = e.i; meters(); screen(e.html, ".drill-k"); }
    else brief();
  }
  function reset() { S.i = 0; S.m = [50, 50, 50, 50]; S.picks = []; S.over = false; S.shown = null; meters(); }
  function brief() {
    reset();
    var c = card(S.d.id), role = c && c.querySelector(".drill-role"), br = c && c.querySelector(".drill-brief");
    var best = bests()[S.d.id];
    screen('<p class="drill-k" tabindex="-1">The brief · ' + S.d.steps.length + ' decisions</p>' +
      (role ? '<p class="drill-role">' + role.innerHTML + "</p>" : "") +
      '<div class="drill-brief">' + (br ? br.innerHTML : "") + "</div>" +
      "<p>The four meters above all start at 50. Each move you make changes them. If <strong>Service</strong> or " +
      "<strong>Trust</strong> drops to 0, the incident escalates past you. Keys: <kbd>1</kbd>–<kbd>4</kbd> pick a move, <kbd>Enter</kbd> goes on.</p>" +
      (best && best.s >= 0 ? '<p class="drill-gate">Your best so far: ' + best.s + " / 100 · " + starText(best.r || 0) + "</p>" : "") +
      '<div class="drill-nav"><button type="button" class="drill-big" data-act="start" data-enter>Start the drill →</button></div>', ".drill-k");
  }
  function shuffle(n) {
    var a = [], i, j, t;
    for (i = 0; i < n; i++) a.push(i);
    for (i = n - 1; i > 0; i--) { j = Math.floor(Math.random() * (i + 1)); t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function step() {
    var st = S.d.steps[S.i], n = S.d.steps.length, ev = "";
    S.order = shuffle(st.choices.length);
    if (st.evidence) ev = '<pre data-lang="terminal"><code>' + st.evidence + "</code></pre>";
    var ch = S.order.map(function (ci, k) {
      return '<li><button type="button" class="drill-c" data-c="' + ci + '"><span class="drill-n">' + (k + 1) + '</span><span class="drill-ct">' +
        st.choices[ci].text + '</span></button></li>';
    }).join("");
    screen('<p class="drill-k" tabindex="-1">Step ' + (S.i + 1) + " of " + n + "</p>" +
      '<div class="drill-sit">' + st.situation + "</div>" + ev +
      '<h4>Your move</h4><ol class="drill-choices" aria-label="Your move">' + ch + "</ol>" +
      '<div class="drill-slot" aria-live="polite"></div>' +
      '<div class="drill-nav"><button type="button" class="drill-big" data-act="next" data-enter disabled>' +
      (S.i + 1 < n ? "Next step →" : "Close the incident →") + '</button><span class="drill-gate">Pick a move to go on.</span></div>', ".drill-k");
  }
  function pick(ci) {
    var st = S.d.steps[S.i];
    if (S.picks.length > S.i || !st || !st.choices[ci]) return;
    var c = st.choices[ci], deltas = [];
    S.picks.push(ci);
    c.effect.forEach(function (x, k) {
      var before = S.m[k];
      S.m[k] = Math.max(0, Math.min(100, before + x));
      deltas.push(S.m[k] - before);
    });
    S.over = S.m[0] <= 0 || S.m[3] <= 0;
    inner().querySelectorAll(".drill-c").forEach(function (b) {
      b.disabled = true;
      if (+b.getAttribute("data-c") === ci) {
        b.classList.add("is-picked", "v-" + c.verdict);
        b.setAttribute("aria-pressed", "true");
        b.querySelector(".drill-ct").insertAdjacentHTML("beforeend", ' <span class="drill-tag">' + VERD[c.verdict] + "</span>");
      }
    });
    var chips = c.effect.map(function (x, k) {
      return '<li class="' + (x > 0 ? "up" : x < 0 ? "down" : "") + '">' + NAMES[k] + " " + (x > 0 ? "+" : x < 0 ? "−" : "±") + Math.abs(x) + "</li>";
    }).join("");
    var others = S.order.filter(function (k) { return k !== ci; }).map(function (k) {
      var o = st.choices[k];
      return '<li><span class="drill-tag v-' + o.verdict + '">' + VERD[o.verdict] + "</span> <strong>" + o.text + "</strong>" + o.why + "</li>";
    }).join("");
    var slot = inner().querySelector(".drill-slot");
    slot.innerHTML = '<div class="drill-res v-' + c.verdict + '"><h4>What happened? <span class="drill-tag">' + VERD[c.verdict] + "</span></h4>" + c.why +
      '<ul class="drill-deltas" aria-label="Meter changes">' + chips + "</ul>" +
      (others ? '<details class="drill-others"><summary>Why not the others?</summary><ul>' + others + "</ul></details>" : "") + "</div>";
    meters(deltas);
    var nx = inner().querySelector('[data-act="next"]');
    nx.disabled = false;
    if (S.over) { nx.textContent = "The incident escalated →"; nx.classList.add("is-over"); }
    inner().querySelector(".drill-gate").textContent = S.over
      ? (S.m[0] <= 0 ? "Service" : "Trust") + " reached 0." : "Read what happened, then go on.";
    nx.focus({ preventScroll: true });
    slot.scrollIntoView({ block: "nearest", behavior: calm() ? "auto" : "smooth" });
  }
  function next() {
    if (S.picks.length <= S.i) return;
    if (S.over) return escalated();
    S.i++;
    if (S.i < S.d.steps.length) step(); else end(false);
  }
  function escalated() {
    var which = S.m[0] <= 0 ? "Service" : "Trust";
    screen('<div class="drill-end is-over"><p class="drill-k" tabindex="-1">Drill over · step ' + (S.i + 1) + " of " + S.d.steps.length + "</p>" +
      "<h3>The incident escalated past you</h3><p><strong>" + which + "</strong> reached 0. " +
      (which === "Service" ? "The outage widened faster than you could contain it, " : "The team and the users stopped trusting the response, ") +
      "so the incident commander handed it to someone else. Start again and try a different move.</p>" + trail() +
      '<div class="drill-nav"><button type="button" class="drill-big" data-act="again" data-enter>↻ Retry the drill</button>' +
      '<button type="button" class="mbtn" data-act="story">Read the real story anyway</button>' +
      '<button type="button" class="mbtn" data-act="close">All drills</button></div></div>', ".drill-k");
  }
  function trail() {
    return '<ol class="drill-trail">' + S.picks.map(function (ci, i) {
      var c = S.d.steps[i].choices[ci];
      return '<li><span class="drill-tag v-' + c.verdict + '">' + VERD[c.verdict] + "</span> " + c.text + "</li>";
    }).join("") + "</ol>";
  }
  function end(story) {
    var score = Math.round((S.m[0] + S.m[1] + S.m[2] + S.m[3]) / 4);
    var all = function (ok) { return S.picks.every(function (ci, i) { return ok.indexOf(S.d.steps[i].choices[ci].verdict) >= 0; }); };
    var stars = all(["best"]) ? 3 : all(["best", "good"]) ? 2 : 1;
    var nb = "", nd = D.length > 1 ? D[(S.d.n + 1) % D.length] : null;
    if (!story) {
      var prev = bests()[S.d.id];
      nb = keep(S.d.id, score, stars) ? " · new best!" : prev && prev.s > score ? " · your best: " + prev.s : "";
      paintCards();
    }
    var counts = {};
    S.picks.forEach(function (ci, i) { var v = S.d.steps[i].choices[ci].verdict; counts[v] = (counts[v] || 0) + 1; });
    var sum = ["best", "good", "risky", "bad"].filter(function (v) { return counts[v]; }).map(function (v) {
      return counts[v] + " " + v + " move" + (counts[v] > 1 ? "s" : "");
    }).join(", ");
    var head = story
      ? '<div class="drill-end is-over"><p class="drill-k" tabindex="-1">Escalated · not scored</p><h3>The real story</h3>'
      : '<div class="drill-end"><p class="drill-k" tabindex="-1">Incident closed</p><h3>Score ' + score + " / 100" + esc(nb) + "</h3>" +
        '<div class="drill-stars" role="img" aria-label="' + stars + ' of 3 stars">' + "★★★".slice(0, stars) + "<s>" + "★★★".slice(0, 3 - stars) + "</s></div>" +
        "<p>" + sum + ". The score is the average of the four meters; three stars means the best move at every step.</p>";
    var tpl = document.querySelector('template[data-drill="' + S.d.id + '"]');
    var el = screen(head + trail() + "</div>", ".drill-k");
    if (tpl) {
      el.appendChild(tpl.content.cloneNode(true));
      el.querySelectorAll("a[data-lab]").forEach(function (a) { a.href = "#lab." + a.getAttribute("data-lab"); });
    }
    el.insertAdjacentHTML("beforeend", '<div class="drill-nav"><button type="button" class="drill-big" data-act="again">↻ Play again</button>' +
      (nd ? '<button type="button" class="mbtn" data-act="go" data-id="' + esc(nd.id) + '">Next drill: ' + esc(attr(nd.id, "title") || nd.id) + " →</button>" : "") +
      '<button type="button" class="mbtn" data-act="close">All drills</button></div>');
  }
  function close(keep) { /* keep: 1 = following a link, 2 = Back / Forward */
    if (!S.view || S.view.hidden) return;
    cancelAnimationFrame(S.raf);
    S.view.hidden = true; root.classList.remove("drill-open");
    var o = S.opener, c = S.d && card(S.d.id), J = window.__handbookJump;
    S.opener = null;
    var oc = o && o.closest && o.closest(".drill-card, .prove-strip");
    function land(back) {
      if (J && (back || !oc) && (oc || c)) J(oc || c, "center");
      if (oc) o.focus({ preventScroll: true });
    }
    if (keep) { if (keep > 1 && oc) land(1); return; } /* Back lands on the card */
    /* pop our entry */
    try { if (history.state && history.state.drill) { S.land = land; return history.back(); } history.replaceState(null, "", "#m-drills"); } catch (_) { /* ignore */ }
    land();
  }

  function onClick(e) {
    var a = e.target.closest("a[href^='#']");
    if (a) { /* in-page link (handbook, decoder, lab): leave the drill, keep its end screen for Back */
      var en = inner().querySelector(".drill-end"), st = history.state;
      try { history.replaceState({ drill: st && st.drill, end: en ? { id: S.d.id, html: inner().innerHTML, m: S.m, p: S.picks, i: S.i } : null }, ""); } catch (_) { /* ignore */ }
      close(1); return;
    }
    var b = e.target.closest("[data-act], .drill-c");
    if (!b || b.disabled || e.detail > 1) return; /* not a double-click's 2nd click */
    if (b.classList.contains("drill-c")) return pick(+b.getAttribute("data-c"));
    var act = b.getAttribute("data-act");
    if (act === "close") close();
    else if (act === "theme") { if (window.__handbookToggleTheme) window.__handbookToggleTheme(); }
    else if (act === "start") { reset(); step(); }
    else if (act === "next") next();
    else if (act === "again") { reset(); step(); }
    else if (act === "story") end(true);
    else if (act === "go") open(b.getAttribute("data-id"));
  }
  function onKey(e) {
    e.stopPropagation(); /* the page's shortcuts ("/", Esc) stay out of the drill */
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key === "Tab") { /* focus stays in the dialog */
      var f = [].filter.call(S.view.querySelectorAll("button,a[href],summary"), function (x) { return !x.disabled && x.getClientRects().length; }), a = document.activeElement;
      if (e.shiftKey ? a === f[0] || a === S.view : a === f[f.length - 1]) { e.preventDefault(); f[e.shiftKey ? f.length - 1 : 0].focus(); }
      return;
    }
    var t = e.target, tag = t && t.tagName;
    if (/^[1-4]$/.test(e.key)) {
      var btn = inner().querySelectorAll(".drill-c")[+e.key - 1];
      if (btn && !btn.disabled) { e.preventDefault(); pick(+btn.getAttribute("data-c")); }
    } else if (e.key === "Enter" && !/^(BUTTON|A|SUMMARY|INPUT|TEXTAREA|SELECT)$/.test(tag || "")) {
      var go = inner().querySelector("[data-enter]:not(:disabled)");
      if (go) { e.preventDefault(); go.click(); }
    }
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".drill-play");
    if (b) { S.opener = b; open(b.getAttribute("data-drill")); }
  });
  function fromHash() {
    var m = /^#drill\.([a-z0-9][a-z0-9-]{2,62})$/.exec(location.hash), l = S.land;
    S.land = null;
    if (m && byId[m[1]]) open(m[1], true);
    else if (S.view && !S.view.hidden) close(2);
    else if (l) l(1);
  }
  window.addEventListener("hashchange", fromHash);
  paintCards();
  if (document.readyState === "complete") fromHash(); else window.addEventListener("load", function () { setTimeout(fromHash, 0); });
  window.__drills = { state: S, open: open, close: close, pick: pick, next: next };
})();
</script>"""


def _squeeze_css(css):
    """Drop comments and the whitespace the browser ignores (the page is near the artifact size limit)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    return re.sub(r":\s+", ":", css).replace(";}", "}").strip() + "\n"


DRILLS_CSS = "\n/* ===== decision drills (drills_site.py) ===== */\n" + _squeeze_css(DRILLS_CSS)
# comments and indentation go; every statement keeps its own line (page_slim.minify_js)
DRILLS_SCRIPT = minify_script(DRILLS_SCRIPT)
