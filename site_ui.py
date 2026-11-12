"""Visual layer of the handbook page: build-time decoration, CSS and a small script.

Presentation only. The Markdown, heading ids, anchors, the sidebar, the search
index and the text that "copy" puts on the clipboard are unchanged:

  * every top-level "## " section (submodule) is wrapped in <div class="subm">,
    so it renders as a card that fades in when it scrolls into view;
  * code blocks get a terminal frame (data-lang label). Shell comments are wrapped
    in <i>, "$ command" lines of sample output in <b>, and "← note" annotations in
    <em>, so commands, output and explanations read apart;
  * blockquotes that start with ⚠️ / ✅ / 💡 / ℹ️ … become coloured callouts;
  * each module opens with a hero card (icon tile, group, stats) and every sidebar
    group has a colour tone, shared with its modules;
  * the map banner gets a small CSS-3D tower and the home page a launchpad.

Motion respects prefers-reduced-motion; nothing loads from the network.
"""
import html
import re

from page_slim import minify_css, minify_script

GROUP_TONES = {
    "Start here": "blue",
    "Interview practice": "violet",
    "Labs": "teal",
    "Real incidents & playbooks": "amber",
    "Real-world problems & OSS toolbox": "rose",
    "Learn: fresher → senior": "teal",
    "Command reference": "sky",
}


def tone_of(group):
    return GROUP_TONES.get(group, "slate")


# --------------------------------------------------------------------------- #
# submodule cards: wrap each top-level <h2> section
# --------------------------------------------------------------------------- #
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
TAG_RE = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9-]*)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*?(/?)>", re.S)


def top_level_h2(body):
    """Offsets of <h2> tags that are not nested in any element, or None when the
    markup does not balance (then the module is left unwrapped)."""
    depth, pos = 0, []
    for m in TAG_RE.finditer(body):
        if m.group(0).startswith("<!--"):
            continue
        close, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if name in VOID or selfclose:
            continue
        if close:
            depth -= 1
            if depth < 0:
                return None
        else:
            if name == "h2" and depth == 0:
                pos.append(m.start())
            depth += 1
    return pos if depth == 0 else None


def wrap_submodules(body):
    pos = top_level_h2(body)
    if not pos:
        return body
    out = [body[:pos[0]]]
    for i, p in enumerate(pos):
        end = pos[i + 1] if i + 1 < len(pos) else len(body)
        out.append('<div class="subm">' + body[p:end].rstrip() + "</div>\n")
    return "".join(out)


# --------------------------------------------------------------------------- #
# code blocks: terminal frame + light highlighting
# --------------------------------------------------------------------------- #
PRE_RE = re.compile(r'<pre><code(?: class="language-([\w+.-]+)")?>(.*?)</code></pre>', re.S)
HASH_COMMENT_LANGS = {"bash", "sh", "shell", "console", "zsh", "powershell", "ps1", "pwsh",
                      "yaml", "yml", "ini", "toml", "nginx", "apache", "hcl", "dockerfile",
                      "python", "conf", "alloy", "ruby"}
SHELL_LANGS = {"bash", "sh", "shell", "console", "zsh", "powershell", "ps1", "pwsh"}
LABELS = {"bash": "bash", "sh": "sh", "shell": "shell", "console": "console", "zsh": "zsh",
          "powershell": "PowerShell", "ps1": "PowerShell", "pwsh": "PowerShell", "yaml": "YAML",
          "yml": "YAML", "json": "JSON", "ini": "INI", "toml": "TOML", "hcl": "HCL", "nginx": "nginx",
          "apache": "Apache", "dockerfile": "Dockerfile", "sql": "SQL", "python": "Python",
          "text": "output", "xml": "XML", "diff": "diff", "markdown": "Markdown", "js": "JavaScript",
          "javascript": "JavaScript", "php": "PHP", "groovy": "Groovy", "ruby": "Ruby",
          "jinja": "Jinja", "alloy": "Alloy", "cmd": "cmd", "bat": "cmd"}
PROMPT_LINE_RE = re.compile(r"^(\s*(?:\$|PS [^&\n]*?&gt;|[\w.-]+@[\w.-]+:[^$#\n]*[$#])\s)")


def _comment_at(line):
    """Index of a '#' that starts a comment (outside quotes, after whitespace), or -1."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t") and (i + 1 == len(line) or line[i + 1] in " \t!"):
            return i
    return -1


def _hash_comments(line):
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return f"<i>{line}</i>" if stripped.strip("#").strip() else line
    i = _comment_at(line)
    return line if i < 0 else f"{line[:i]}<i>{line[i:]}</i>"


def _annotate(line):
    """'… ← note' -> the note in <em> (sample-output annotations)."""
    i = line.find("←")
    return line if i < 0 else f"{line[:i]}<em>{line[i:]}</em>"


def _decorate_code(lang, code):
    lines = code.split("\n")
    out, prompts = [], 0
    for line in lines:
        pm = PROMPT_LINE_RE.match(line)
        if pm:
            prompts += 1
            rest = line[pm.end():]
            cmt = _comment_at(rest)
            if cmt >= 0:
                rest = f"{rest[:cmt]}<i>{rest[cmt:]}</i>"
            out.append(f"<b><u>{pm.group(1)}</u>{rest}</b>")
            continue
        if lang in HASH_COMMENT_LANGS:
            line = _hash_comments(line)
        out.append(_annotate(line))
    return "\n".join(out), prompts


def decorate_code(body):
    def rep(m):
        lang_raw = m.group(1) or ""
        lang = lang_raw.lower()
        code, prompts = _decorate_code(lang, m.group(2))
        label = LABELS.get(lang, lang) or ("terminal" if prompts else "")
        attr = f' data-lang="{html.escape(label, quote=True)}"' if label else ""
        # no class="language-…" on <code>: nothing reads it, and it repeated ~4,300 times
        return f"<pre{attr}><code>{code}</code></pre>"
    return PRE_RE.sub(rep, body)


# --------------------------------------------------------------------------- #
# callouts
# --------------------------------------------------------------------------- #
CALLOUTS = [("danger", ("🚨", "⛔", "🛑", "❌", "🔥")),
            ("warn", ("⚠️", "⚠", "❗", "❗️")),
            ("ok", ("✅", "✔️", "✔", "🟢")),
            ("tip", ("💡", "🔑", "👉", "🎯", "⭐", "🧠", "🎓")),
            ("info", ("ℹ️", "ℹ", "📌", "📝", "🔎", "🔍", "📚", "🗺️", "🧭"))]


def decorate_quotes(body):
    def rep(m):
        head = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))[:3]
        kind = next((k for k, marks in CALLOUTS if any(head.startswith(x) for x in marks)), "info")
        return f'<blockquote class="callout {kind}">{m.group(1)}{m.group(2)}'
    return re.sub(r"<blockquote>(\s*<p>)((?:<strong>)?[^<]{0,4})", rep, body)


def decorate_body(body, cards=True):
    body = decorate_code(body)
    body = decorate_quotes(body)
    return wrap_submodules(body) if cards else body


# --------------------------------------------------------------------------- #
# "Safest next step" hints: one line under chosen headings, from hints/safest-step.tsv
# --------------------------------------------------------------------------- #
HINTS_FILE = "hints/safest-step.tsv"   # file <TAB> heading <TAB> rung <TAB> text (header row first)
LADDER_ID = "m57-4-the-risk-ladder"    # 57-method-protect-risk-ladder.md "## 4. The risk ladder"


def load_hints(root):
    """{module file: [(heading, rung, text)]}; an absent file means no hints."""
    out = {}
    try:
        with open(f"{root}/{HINTS_FILE}", encoding="utf-8") as f:
            rows = [r.rstrip("\n").split("\t") for r in f if r.strip()][1:]
    except OSError:
        return out
    for fname, heading, rung, text in rows:
        out.setdefault(fname, []).append((heading.strip(), int(rung), text.strip()))
    return out


def insert_hints(body, toc_tokens, hints, prefix):
    """Put each hint right after its heading (exact toc name). Returns (body, headings not found once)."""
    found = {}

    def walk(tokens):
        for t in tokens:
            found.setdefault(html.unescape(t["name"]).strip(), []).append(t["id"])
            walk(t["children"])
    walk(toc_tokens)
    missing = []
    for heading, rung, text in hints:
        ids = found.get(heading, [])
        if len(ids) != 1:
            missing.append(heading)
            continue
        line = (f'<blockquote class="callout ok ssn no-index"><p>🛟 Safest next step · '
                f'<a href="#{LADDER_ID}">rung {rung}</a>: {html.escape(text, quote=False)}</p></blockquote>')
        body = re.sub(rf'(<h([1-6]) id="{re.escape(prefix + ids[0])}"[^>]*>.*?</h\2>)',
                      lambda m: m.group(1) + line, body, count=1, flags=re.S)
    return body, missing


# --------------------------------------------------------------------------- #
# module hero, map tower, home launchpad
# --------------------------------------------------------------------------- #
def _read_time(body):
    # visible text only: embedded data (<script>, e.g. the drills' JSON), <style> and <template> are not read
    body = re.sub(r"<(script|style|template)\b[^>]*>.*?</\1\s*>", " ", body, flags=re.S | re.I)
    words = len(re.findall(r"\w+", html.unescape(re.sub(r"<[^>]+>", " ", body))))
    mins = max(1, round(words / 230))
    if mins < 90:
        return f"≈ {mins} min read"
    return f"≈ {mins / 60:.1f} h read".replace(".0 h", " h")


def module_hero(mod, n_cmds, extra_chip="", unit=("submodule", "submodules")):
    subs = sum(1 for t in mod["toc"] if t["level"] == 2)
    chips = []
    if subs:
        chips.append(f"<span>📑 {subs} {unit[0] if subs == 1 else unit[1]}</span>")
    if n_cmds:
        chips.append(f"<span>🔍 {n_cmds} command{'s' if n_cmds != 1 else ''} decoded</span>")
    if extra_chip:
        chips.append(f"<span>{extra_chip}</span>")
    chips.append(f"<span>⏱ {_read_time(mod['body'])}</span>")
    return (f'<header class="mod-hero tilt">'
            f'<div class="hero-tile" aria-hidden="true"><span>{mod["icon"]}</span></div>'
            f'<div class="hero-text"><div class="hero-kicker">{html.escape(mod["group"])}</div>'
            f'<h1>{html.escape(mod["title"])}</h1>'
            f'<div class="hero-stats">{"".join(chips)}</div></div></header>')


MINI_TOWER = ('<div class="mini-tower" aria-hidden="true"><div class="mt-spin">'
              '<i></i><i></i><i></i><i></i><i></i></div></div>')


def launchpad(links):
    """links: [(href, icon, title, subtitle, tone)] -> the home page quick-entry grid."""
    cards = "".join(
        f'<a class="lcard tilt" data-tone="{tone}" href="{href}"><span class="lc-ico" aria-hidden="true">{icon}</span>'
        f'<b>{html.escape(title)}</b><small>{html.escape(sub)}</small></a>'
        for href, icon, title, sub, tone in links)
    return f'<nav class="launch no-index" aria-label="Quick start">{cards}</nav>'


UI_CSS = r"""
/* ======================= visual layer (site_ui.py) ======================= */
:root {
  --t-blue: #0b6bcb; --t-violet: #7c3aed; --t-amber: #a44c08; --t-rose: #be123c; --t-teal: #0f766e;
  --t-sky: #0369a1; --t-slate: #475569;
  --card: rgba(255, 255, 255, .82); --card-border: #dbe3ec; --card-hi: rgba(255, 255, 255, .9);
  --glow-a: rgba(11, 107, 203, .13); --glow-b: rgba(124, 58, 237, .10); --glow-c: rgba(15, 118, 110, .09);
  --term-bg: #0e1621; --term-bar: #172231; --term-border: #22303f; --term-fg: #d9e4ef;
  --term-dim: #7d8fa3; --term-cmd: #f1f6fb; --term-note: #fbbf24; --term-prompt: #4ade80;
  --tone: var(--t-blue);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --t-blue: #4da3ff; --t-violet: #a78bfa; --t-amber: #fbbf24; --t-rose: #fb7185; --t-teal: #2dd4bf;
    --t-sky: #38bdf8; --t-slate: #94a3b8;
    --card: rgba(22, 29, 38, .74); --card-border: #243142; --card-hi: rgba(255, 255, 255, .045);
    --glow-a: rgba(77, 163, 255, .13); --glow-b: rgba(167, 139, 250, .10); --glow-c: rgba(45, 212, 191, .08);
    --term-bg: #0a1018; --term-bar: #121b26; --term-border: #1f2b3a;
  }
}
:root[data-theme="dark"] {
  --t-blue: #4da3ff; --t-violet: #a78bfa; --t-amber: #fbbf24; --t-rose: #fb7185; --t-teal: #2dd4bf;
  --t-sky: #38bdf8; --t-slate: #94a3b8;
  --card: rgba(22, 29, 38, .74); --card-border: #243142; --card-hi: rgba(255, 255, 255, .045);
  --glow-a: rgba(77, 163, 255, .13); --glow-b: rgba(167, 139, 250, .10); --glow-c: rgba(45, 212, 191, .08);
  --term-bg: #0a1018; --term-bar: #121b26; --term-border: #1f2b3a;
}
[data-tone="blue"] { --tone: var(--t-blue); }     [data-tone="violet"] { --tone: var(--t-violet); }
[data-tone="amber"] { --tone: var(--t-amber); }   [data-tone="rose"] { --tone: var(--t-rose); }
[data-tone="teal"] { --tone: var(--t-teal); }     [data-tone="sky"] { --tone: var(--t-sky); }
[data-tone="slate"] { --tone: var(--t-slate); }

/* ambient light behind everything (one composited layer; drifts slowly) */
body::before { content: ""; position: fixed; inset: -15vh -10vw; z-index: -1; pointer-events: none;
  background:
    radial-gradient(38vw 32vh at 12% 4%, var(--glow-a), transparent 70%),
    radial-gradient(34vw 30vh at 92% 12%, var(--glow-b), transparent 70%),
    radial-gradient(44vw 36vh at 62% 98%, var(--glow-c), transparent 70%);
  animation: ambient 46s ease-in-out infinite alternate; will-change: transform; }
@keyframes ambient { to { transform: translate3d(-3vw, 2.5vh, 0) scale(1.06); } }
::selection { background: color-mix(in srgb, var(--t-blue) 32%, transparent); }
html { scrollbar-color: color-mix(in srgb, var(--fg-dim) 45%, transparent) transparent; }
#sidebar, pre, table, #results { scrollbar-width: thin; }

/* top bar: frosted glass with a light-trail edge, and the reading-progress beam */
#topbar { background: color-mix(in srgb, var(--bg2) 76%, transparent);
  -webkit-backdrop-filter: saturate(1.5) blur(14px); backdrop-filter: saturate(1.5) blur(14px); }
#topbar::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 1px; pointer-events: none;
  background: linear-gradient(90deg, transparent, var(--t-blue) 20%, var(--t-violet) 50%, var(--t-teal) 80%, transparent) 0 0 / 50% 100% repeat-x;
  opacity: .6; animation: beam 14s linear infinite; }
@keyframes beam { to { background-position: 100% 0; } }
#readbar { position: fixed; top: var(--tb-total); left: 0; right: 0; height: 3px; z-index: 31; pointer-events: none;
  transform-origin: 0 50%; transform: scaleX(0); will-change: transform;
  background: linear-gradient(90deg, var(--tone), color-mix(in srgb, var(--tone) 40%, var(--t-violet)));
  box-shadow: 0 0 10px var(--tone); }
.brand-text { background: linear-gradient(92deg, var(--fg) 35%, var(--t-blue) 75%, var(--t-violet));
  -webkit-background-clip: text; background-clip: text; color: transparent; }
#topbar .brand small { -webkit-text-fill-color: var(--fg-dim); }
#map-btn { border: 1px solid transparent; color: var(--fg);
  background: linear-gradient(var(--bg2), var(--bg2)) padding-box,
              linear-gradient(120deg, var(--t-blue), var(--t-violet), var(--t-teal)) border-box;
  transition: box-shadow .2s, transform .2s; }
#map-btn:hover { background: linear-gradient(var(--bg3), var(--bg3)) padding-box,
              linear-gradient(120deg, var(--t-blue), var(--t-violet), var(--t-teal)) border-box;
  box-shadow: 0 0 20px -4px var(--t-violet); transform: translateY(-1px); }
.env-switch { border-radius: 10px; background: color-mix(in srgb, var(--bg) 60%, transparent); }
.env-switch button[aria-pressed="true"] { background: linear-gradient(135deg, color-mix(in srgb, var(--t-blue) 22%, var(--bg3)), var(--bg3)); }

/* sidebar: glass column, group tones, icon tiles */
#sidebar { background: color-mix(in srgb, var(--bg2) 84%, transparent); }
.nav-group { display: flex; align-items: center; gap: 8px; color: var(--tone); }
.nav-group::before { content: ""; flex: none; width: 7px; height: 7px; border-radius: 2px; transform: rotate(45deg);
  background: var(--tone); box-shadow: 0 0 8px var(--tone); }
.nav-group::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, color-mix(in srgb, var(--tone) 45%, transparent), transparent); }
.mod-btn { transition: background .15s, transform .15s; }
.mod-btn:hover { transform: translateX(2px); }
.mod-btn .mod-icon { width: 28px; height: 28px; display: grid; place-items: center; border-radius: 8px; font-size: 15px;
  background: color-mix(in srgb, var(--tone) 13%, transparent); transition: box-shadow .2s, background .2s; }
.module.active > .mod-btn { color: var(--fg);
  background: linear-gradient(90deg, color-mix(in srgb, var(--tone) 20%, transparent), transparent 85%);
  box-shadow: inset 3px 0 0 var(--tone); }
.module.active > .mod-btn .mod-icon { background: color-mix(in srgb, var(--tone) 26%, transparent); box-shadow: 0 0 14px -3px var(--tone); }
.subnav { border-left-color: color-mix(in srgb, var(--tone) 35%, var(--border)); }
.subnav a.current { color: var(--tone); background: color-mix(in srgb, var(--tone) 12%, transparent); box-shadow: inset 2px 0 0 var(--tone); }

/* content column: centred beside the sidebar on wide screens */
#main { max-width: none; }
#main > .mod-section { max-width: 1060px; margin-left: auto; margin-right: auto; }
.mod-section + .mod-section { border-top: 0; padding-top: 34px; }

/* module hero */
.mod-hero { position: relative; isolation: isolate; overflow: hidden; display: flex; align-items: center; gap: 22px;
  margin: 2px 0 22px; padding: 24px 26px; border-radius: 20px;
  border: 1px solid color-mix(in srgb, var(--tone) 32%, var(--card-border));
  background: linear-gradient(135deg, color-mix(in srgb, var(--tone) 17%, var(--bg2)), var(--bg2) 62%);
  box-shadow: 0 24px 60px -36px var(--tone), inset 0 1px 0 var(--card-hi); }
.mod-hero::before { content: ""; position: absolute; z-index: -1; left: -20%; right: -20%; top: 46%; height: 150%;
  background-image:
    linear-gradient(color-mix(in srgb, var(--tone) 34%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--tone) 34%, transparent) 1px, transparent 1px);
  background-size: 30px 30px; transform: perspective(380px) rotateX(62deg); transform-origin: 50% 0;
  -webkit-mask-image: linear-gradient(to bottom, #000 0%, transparent 62%); mask-image: linear-gradient(to bottom, #000 0%, transparent 62%);
  opacity: .55; }
.mod-hero::after { content: ""; position: absolute; z-index: -1; width: 300px; height: 300px; right: -70px; top: -150px; border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--tone) 42%, transparent), transparent 68%); }
.hero-tile { flex: none; width: 76px; height: 76px; border-radius: 20px; display: grid; place-items: center; font-size: 40px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tone) 42%, var(--bg2)), color-mix(in srgb, var(--tone) 10%, var(--bg2)));
  box-shadow: 0 16px 30px -14px var(--tone), inset 0 1px 0 rgba(255, 255, 255, .3), inset 0 -8px 14px rgba(0, 0, 0, .16);
  transform: perspective(520px) rotateX(var(--rx, 12deg)) rotateY(var(--ry, -16deg)); transition: transform .35s cubic-bezier(.2, .7, .2, 1);
  animation: tile-float 7s ease-in-out infinite; }
@keyframes tile-float { 50% { translate: 0 -4px; } }
.hero-tile span { transform: translateZ(18px); filter: drop-shadow(0 6px 8px rgba(0, 0, 0, .28)); }
.hero-text { min-width: 0; }
.hero-kicker { font-size: 11.5px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; color: var(--tone); }
.mod-section .mod-hero h1 { margin: 3px 0 10px; font-size: 30px; line-height: 1.2; letter-spacing: -.012em;
  background: linear-gradient(92deg, var(--fg) 40%, var(--tone)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero-stats { display: flex; flex-wrap: wrap; gap: 6px 8px; }
.hero-stats span { font-size: 12.5px; padding: 3px 11px; border-radius: 999px; color: var(--fg-dim);
  background: color-mix(in srgb, var(--bg) 62%, transparent); border: 1px solid var(--card-border); white-space: nowrap; }

/* submodule cards */
.subm { position: relative; margin: 24px 0; padding: 0 26px 14px; border-radius: 18px;
  background: var(--card); border: 1px solid var(--card-border);
  box-shadow: inset 0 1px 0 var(--card-hi), 0 22px 46px -34px var(--shadow-strong), 0 2px 6px -4px var(--shadow); }
.subm > h2 { margin: 0 -26px 14px; padding: 17px 26px 13px; border-radius: 18px 18px 0 0; font-size: 21px;
  border-bottom: 1px solid var(--card-border);
  background: linear-gradient(90deg, color-mix(in srgb, var(--tone) 15%, transparent), transparent 70%); }
.subm > h2::before { content: ""; display: inline-block; width: 9px; height: 9px; margin: 0 12px 0 2px; vertical-align: 3px;
  border-radius: 2px; transform: rotate(45deg); background: var(--tone); box-shadow: 0 0 10px var(--tone); }
.subm > hr:last-child { display: none; }
.js-anim .subm { opacity: 0; transition: opacity .6s ease; }
.js-anim .subm.in { opacity: 1; }
.js-anim .subm > h2 { background-size: 0% 100%; background-repeat: no-repeat; transition: background-size .9s cubic-bezier(.2, .7, .2, 1) .1s; }
.js-anim .subm.in > h2 { background-size: 100% 100%; }
.js-anim .subm > h2::before { transform: rotate(-135deg) scale(.2); transition: transform .7s cubic-bezier(.3, 1.6, .5, 1) .15s; }
.js-anim .subm.in > h2::before { transform: rotate(45deg); }
.mod-section h3 { color: color-mix(in srgb, var(--tone) 72%, var(--fg)); }
.subm > h3 { position: relative; }
.subm > h3::before { content: ""; position: absolute; left: -18px; top: .5em; width: 8px; height: 8px; border-radius: 50%;
  background: var(--tone); box-shadow: 0 0 0 3px color-mix(in srgb, var(--tone) 22%, transparent), 0 0 10px var(--tone); }
.mod-section > p:first-of-type { font-size: 16px; line-height: 1.68; }
#main pre { transition: border-color .2s ease, box-shadow .2s ease; }
#main pre:hover { border-color: color-mix(in srgb, var(--tone) 50%, var(--term-border));
  box-shadow: 0 18px 38px -24px color-mix(in srgb, var(--tone) 60%, #000), inset 0 1px 0 rgba(255, 255, 255, .05); }
.mod-section ul > li::marker { color: var(--tone); }
.mod-section hr { border: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--border) 15%, var(--border) 85%, transparent); }
.mod-section p a, .mod-section li a, .mod-section td a { text-decoration: none;
  background: linear-gradient(currentColor, currentColor) 0 100% / 0 1px no-repeat; transition: background-size .25s ease; }
.mod-section p a:hover, .mod-section li a:hover, .mod-section td a:hover { background-size: 100% 1px; text-decoration: none; }
:not(pre) > code { background: color-mix(in srgb, var(--tone) 9%, var(--code-bg)); border-color: color-mix(in srgb, var(--tone) 22%, var(--border)); }

/* code: terminal windows (dark in both themes) */
#main pre { padding: 38px 16px 14px; border-radius: 12px; color: var(--term-fg); border: 1px solid var(--term-border);
  background:
    radial-gradient(circle at 17px 13.5px, #ff5f57 0 4.2px, transparent 4.8px),
    radial-gradient(circle at 33px 13.5px, #febc2e 0 4.2px, transparent 4.8px),
    radial-gradient(circle at 49px 13.5px, #28c840 0 4.2px, transparent 4.8px),
    linear-gradient(var(--term-border), var(--term-border)) 0 27px / 100% 1px no-repeat,
    linear-gradient(var(--term-bar), var(--term-bar)) 0 0 / 100% 27px no-repeat,
    var(--term-bg);
  box-shadow: 0 16px 34px -24px rgba(0, 0, 0, .7), inset 0 1px 0 rgba(255, 255, 255, .04); }
#main pre[data-lang]::before { content: attr(data-lang); display: block; position: sticky; left: 0; height: 0; width: 0; overflow: visible;
  transform: translate(48px, -33px); white-space: nowrap; font: 700 10.5px/16px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: .1em; text-transform: uppercase; color: var(--term-dim); pointer-events: none; }
#main pre code { color: inherit; }
#main pre i { font-style: italic; color: var(--term-dim); }
#main pre b { font-weight: 650; color: var(--term-cmd); }
#main pre b u { text-decoration: none; font-weight: 700; color: var(--term-prompt); }
#main pre em { font-style: normal; color: var(--term-note); }
#main .copy-btn { top: 4px; right: 8px; color: #9fb2c6; background: rgba(255, 255, 255, .06); border-color: rgba(255, 255, 255, .12); opacity: .55; }
#main pre:hover .copy-btn { opacity: 1; }
#main .copy-btn:hover { color: #fff; background: rgba(255, 255, 255, .12); }

/* tables */
#main table { width: fit-content; border-collapse: separate; border-spacing: 0; border: 1px solid var(--card-border); border-radius: 12px;
  background: color-mix(in srgb, var(--bg2) 70%, transparent); box-shadow: 0 10px 26px -22px var(--shadow-strong); }
#main th, #main td { border: 0; border-top: 1px solid var(--card-border); }
#main th + th, #main td + td { border-left: 1px solid var(--card-border); }
#main thead tr:first-child th, #main table > tr:first-child > * { border-top: 0; }
#main th { background: linear-gradient(180deg, color-mix(in srgb, var(--tone) 16%, var(--bg3)), color-mix(in srgb, var(--tone) 7%, var(--bg3))); font-weight: 650; }
#main tr:nth-child(even) td { background: color-mix(in srgb, var(--bg3) 45%, transparent); }
#main tbody tr:hover td { background: color-mix(in srgb, var(--tone) 8%, transparent); }

/* callouts */
#main blockquote { color: var(--fg); border: 1px solid color-mix(in srgb, var(--c, var(--tone)) 28%, var(--card-border));
  border-left: 4px solid var(--c, var(--tone)); border-radius: 12px; padding: 10px 16px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--c, var(--tone)) 12%, var(--bg2)), color-mix(in srgb, var(--bg2) 70%, transparent) 85%); }
blockquote.warn { --c: var(--t-amber); } blockquote.danger { --c: var(--t-rose); } blockquote.ok { --c: var(--t-teal); }
blockquote.tip { --c: var(--t-violet); } blockquote.info { --c: var(--t-blue); }
#main blockquote.ssn { padding: 4px 12px; margin: 6px 0 12px; font-size: 13.5px; }
#main blockquote.ssn p { margin: 0; }

/* module 57: "Print the card" prints a copy of the PROTECT card only */
.card-print-btn { margin: .4rem 0 .8rem; padding: 5px 12px; border-radius: 8px; border: 1px solid var(--card-border);
  background: var(--bg2); color: var(--fg); font: inherit; font-size: 13px; cursor: pointer; }
.card-print-btn:hover { border-color: var(--tone); }
#print-card { display: none; }

/* collapsibles */
#main details > summary { list-style: none; }
#main details > summary::-webkit-details-marker { display: none; }
#main details > summary::before { content: "▸"; display: inline-block; width: 1em; margin-right: 4px; color: var(--tone); transition: transform .2s ease; }
#main details[open] > summary::before { transform: rotate(90deg); }
#main details { transition: box-shadow .2s ease, border-color .2s ease; }
#main details:hover { box-shadow: 0 8px 24px -18px var(--tone); }

/* "open the map" banner with a CSS-3D tower */
.map-banner { position: relative; overflow: hidden; isolation: isolate; border-radius: 18px; padding: 16px 20px;
  border: 1px solid color-mix(in srgb, var(--t-violet) 30%, var(--card-border));
  background: linear-gradient(120deg, color-mix(in srgb, var(--t-blue) 16%, var(--bg2)), color-mix(in srgb, var(--t-violet) 12%, var(--bg2)) 55%, color-mix(in srgb, var(--t-teal) 10%, var(--bg2)));
  box-shadow: 0 22px 50px -34px var(--t-violet); }
.map-banner-btn { background: linear-gradient(120deg, var(--t-blue), var(--t-violet)); color: #fff;
  box-shadow: 0 8px 22px -10px var(--t-violet); transition: transform .2s, box-shadow .2s; }
.map-banner-btn:hover { transform: translateY(-1px); box-shadow: 0 12px 28px -10px var(--t-violet); filter: none; }
.mini-tower { flex: none; width: 128px; height: 108px; perspective: 520px; }
.mt-spin { position: relative; width: 92px; height: 92px; margin: 16px auto 0; transform-style: preserve-3d;
  transform: rotateX(66deg) rotateZ(0deg); animation: mt-spin 26s linear infinite; }
.mt-spin i { position: absolute; inset: 0; border-radius: 50%; border: 2px solid var(--c);
  transform: translateZ(calc(var(--n) * 17px)) scale(calc(1 - var(--n) * .09));
  box-shadow: 0 0 12px -2px var(--c), inset 0 0 14px -6px var(--c);
  background:
    radial-gradient(circle at 18% 30%, var(--t-blue) 0 3px, transparent 3.6px),
    radial-gradient(circle at 78% 22%, var(--t-amber) 0 3px, transparent 3.6px),
    radial-gradient(circle at 70% 80%, var(--t-teal) 0 3px, transparent 3.6px),
    radial-gradient(circle at 28% 76%, var(--t-rose) 0 3px, transparent 3.6px),
    radial-gradient(circle, color-mix(in srgb, var(--c) 16%, transparent), transparent 70%); }
.mt-spin i:nth-child(1) { --n: 0; --c: var(--t-teal); }  .mt-spin i:nth-child(2) { --n: 1; --c: var(--t-sky); }
.mt-spin i:nth-child(3) { --n: 2; --c: var(--t-blue); }  .mt-spin i:nth-child(4) { --n: 3; --c: var(--t-violet); }
.mt-spin i:nth-child(5) { --n: 4; --c: var(--t-rose); }
@keyframes mt-spin { to { transform: rotateX(66deg) rotateZ(360deg); } }

/* home launchpad */
.launch { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin: -6px 0 22px; perspective: 900px; }
.lcard { position: relative; overflow: hidden; isolation: isolate; display: flex; flex-direction: column; gap: 3px; padding: 14px 16px 15px;
  border-radius: 16px; color: var(--fg); background: var(--card); border: 1px solid color-mix(in srgb, var(--tone) 26%, var(--card-border));
  box-shadow: inset 0 1px 0 var(--card-hi), 0 18px 34px -28px var(--tone);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)); transition: transform .3s cubic-bezier(.2, .7, .2, 1), box-shadow .3s; }
.lcard::after { content: ""; position: absolute; inset: 0; z-index: -1; opacity: 0; transition: opacity .3s;
  background: radial-gradient(240px circle at var(--mx, 50%) var(--my, 0%), color-mix(in srgb, var(--tone) 22%, transparent), transparent 65%); }
.lcard:hover { text-decoration: none; box-shadow: inset 0 1px 0 var(--card-hi), 0 22px 40px -24px var(--tone); }
.lcard:hover::after { opacity: 1; }
.lc-ico { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 11px; font-size: 21px; margin-bottom: 6px;
  background: linear-gradient(145deg, color-mix(in srgb, var(--tone) 34%, var(--bg2)), color-mix(in srgb, var(--tone) 10%, var(--bg2)));
  box-shadow: 0 8px 18px -10px var(--tone); }
.lcard b { font-size: 15px; }
.lcard small { color: var(--fg-dim); font-size: 12.8px; line-height: 1.45; }

/* back to top: progress ring for the current module */
#totop { border: 0; color: var(--fg);
  background: radial-gradient(closest-side, var(--bg2) 80%, transparent 82%),
              conic-gradient(var(--tone) calc(var(--p, 0) * 1turn), color-mix(in srgb, var(--fg-dim) 22%, transparent) 0);
  box-shadow: 0 8px 24px -8px var(--shadow-strong); }

@media (prefers-reduced-motion: reduce) {
  body::before, .mt-spin, .hero-tile, #topbar::after { animation: none; }
  .js-anim .subm, .js-anim .subm > h2, .js-anim .subm > h2::before { opacity: 1; transition: none; }
  .js-anim .subm > h2 { background-size: 100% 100%; } .js-anim .subm > h2::before { transform: rotate(45deg); }
  .hero-tile, .lcard, .mod-btn { transition: none; }
}
@media print {
  body::before, #readbar { display: none; }
  .js-anim .subm { opacity: 1 !important; }
  body.printing-card > *:not(#print-card) { display: none !important; }
  body.printing-card #print-card { display: block; color: #000; background: #fff; }
  #print-card h2 { font-size: 14pt; margin: 0 0 6pt; }
  #print-card pre, #print-card code { background: #fff !important; color: #000 !important; border: 0; box-shadow: none;
    white-space: pre; font-size: 9pt; line-height: 1.25; }
  #print-card pre::before, #print-card pre::after { display: none !important; }
  @page { size: A4; margin: 12mm; }
}
"""

UI_SCRIPT = r"""<script>
/* visual layer: reveal cards, reading progress, tilt (presentation only) */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var main = document.getElementById("main");
  if (!main) return;

  /* cards fade up as they enter the viewport */
  if (!reduce && typeof IntersectionObserver === "function") {
    var cards = main.querySelectorAll(".subm");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -6% 0px" });
    root.classList.add("js-anim");
    cards.forEach(function (c) { io.observe(c); });
    /* jumps (sidebar, search, links) land on content that must be visible at once */
    var showAround = function (el) {
      var c = el && el.closest ? el.closest(".subm") : null;
      if (c) { c.classList.add("in"); io.unobserve(c); }
    };
    window.addEventListener("hashchange", function () {
      try { showAround(document.getElementById(decodeURIComponent(location.hash.slice(1)))); } catch (_) { /* bad hash */ }
    });
    main.addEventListener("focusin", function (e) { showAround(e.target); });
    if (location.hash) { try { showAround(document.getElementById(decodeURIComponent(location.hash.slice(1)))); } catch (_) { /* ignore */ } }
  }

  /* reading progress through the current module: top beam + ring on the back-to-top button */
  var bar = document.getElementById("readbar"), totop = document.getElementById("totop");
  var secs = Array.prototype.slice.call(main.querySelectorAll(":scope > .mod-section"));
  var tops = [], dirty = true, queued = false, curTone = "";
  function measure() {
    var sy = window.scrollY;
    tops = secs.map(function (s) { return s.getBoundingClientRect().top + sy; });
    dirty = false;
  }
  function update() {
    queued = false;
    if (!secs.length || !bar) return;
    if (dirty) measure();
    var y = window.scrollY + window.innerHeight * 0.3, lo = 0, hi = tops.length - 1, i = 0;
    while (lo <= hi) { var mid = (lo + hi) >> 1; if (tops[mid] <= y) { i = mid; lo = mid + 1; } else hi = mid - 1; }
    var start = tops[i], end = i + 1 < tops.length ? tops[i + 1] : start + secs[i].offsetHeight;
    var p = Math.min(1, Math.max(0, (window.scrollY + window.innerHeight - start) / Math.max(1, end - start)));
    if (window.scrollY < 4 && i === 0) p = 0;
    bar.style.transform = "scaleX(" + p.toFixed(4) + ")";
    if (totop) totop.style.setProperty("--p", p.toFixed(3));
    var tone = secs[i].getAttribute("data-tone") || "blue";
    if (tone !== curTone) { curTone = tone; bar.setAttribute("data-tone", tone); if (totop) totop.setAttribute("data-tone", tone); }
  }
  function queue() { if (!queued) { queued = true; window.requestAnimationFrame(update); } }
  function invalidate() { dirty = true; queue(); }
  window.addEventListener("scroll", queue, { passive: true });
  window.addEventListener("resize", invalidate, { passive: true });
  window.addEventListener("load", invalidate);
  document.addEventListener("handbook-layout", invalidate);
  if (typeof ResizeObserver === "function") new ResizeObserver(invalidate).observe(main);
  queue();

  /* map legend: mark the chip row as scrollable while chips are still hidden on the right */
  var legend = document.querySelector(".map-legend");
  if (legend) {
    var syncLegend = function () {
      legend.classList.toggle("more", legend.scrollLeft + legend.clientWidth < legend.scrollWidth - 2);
    };
    legend.addEventListener("scroll", syncLegend, { passive: true });
    window.addEventListener("resize", syncLegend, { passive: true });
    if (typeof MutationObserver === "function") new MutationObserver(syncLegend).observe(legend, { childList: true, subtree: true });
    if (typeof ResizeObserver === "function") new ResizeObserver(syncLegend).observe(legend);
    syncLegend();
  }

  /* tilt: hero tiles and launchpad cards lean towards the pointer */
  if (!reduce && window.matchMedia && window.matchMedia("(pointer: fine)").matches) {
    main.addEventListener("pointermove", function (e) {
      var t = e.target.closest && e.target.closest(".tilt");
      if (!t) return;
      var r = t.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      var el = t.classList.contains("mod-hero") ? t.querySelector(".hero-tile") : t;
      var k = t.classList.contains("mod-hero") ? 22 : 9;
      if (el) { el.style.setProperty("--ry", ((x - 0.5) * k).toFixed(2) + "deg"); el.style.setProperty("--rx", ((0.5 - y) * k).toFixed(2) + "deg"); }
      t.style.setProperty("--mx", (x * 100).toFixed(1) + "%"); t.style.setProperty("--my", (y * 100).toFixed(1) + "%");
    }, { passive: true });
    main.addEventListener("pointerout", function (e) {
      var t = e.target.closest && e.target.closest(".tilt");
      if (!t || (e.relatedTarget && t.contains(e.relatedTarget))) return;
      var el = t.classList.contains("mod-hero") ? t.querySelector(".hero-tile") : t;
      if (el) { el.style.removeProperty("--rx"); el.style.removeProperty("--ry"); }
    });
  }
})();

/* module 57: "Print the card" button; prints a copy of the card, not the page around it */
(function () {
  var h = document.getElementById("m57-the-protect-card");
  if (!h) return;
  var b = document.createElement("button");
  b.type = "button"; b.className = "card-print-btn"; b.textContent = "🖨️ Print the card";
  h.insertAdjacentElement("afterend", b);
  b.addEventListener("click", function () {
    var old = document.getElementById("print-card");
    if (old) old.remove();
    var box = document.createElement("div");
    var pre = h.parentNode.querySelector("pre");
    box.appendChild(h.cloneNode(true));
    if (pre) box.appendChild(pre.cloneNode(true));
    box.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
    box.querySelectorAll(".copy-btn").forEach(function (e) { e.remove(); });
    box.id = "print-card";
    var y = window.scrollY;     /* the print layout holds only the card, so the browser can lose the scroll position */
    document.body.appendChild(box); document.body.classList.add("printing-card");
    var done = function () {
      window.removeEventListener("afterprint", done);
      document.body.classList.remove("printing-card"); box.remove();
      window.scrollTo(0, y);
    };
    window.addEventListener("afterprint", done);
    try { window.print(); } catch (e) { done(); }
  });
})();
</script>"""


# the page is near the artifact size cap: comments and indentation go (page_slim.py)
UI_CSS = minify_css(UI_CSS) + "\n"
UI_SCRIPT = minify_script(UI_SCRIPT)
