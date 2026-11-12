"""Hands-on labs page for the website, generated from labs/rooms/ (like interview_site.py).

One virtual page, "labs.md" (sidebar group "Labs", title "Hands-on labs"):

  * a status card that the page script fills in: lab server running or not;
  * "How the labs work" (indexed by the site search);
  * one "## <path>" section per path with a card per room (level, minutes, points, source link);
    the script marks each card open, locked or completed from the labs controller;
  * per room, a <template> with the brief, the tasks, the question boxes, the checks (their
    one-line descriptions only) and the hints, rendered at build time. The script clones it into
    the split-screen room view (left: brief and tasks, right: the ttyd terminal at /lab-term/<sid>/).

Without the controller (offline file, published artifact, labs not started) the same view is
read-only and says how to start the lab server.

Never in the page: answer hashes, plaintext answers, solve.sh, answers.test.json, check scripts
and walkthroughs (the controller returns the walkthrough after Finish). Nothing here touches Docker.
"""
import html
import json
import os
import re

import markdown

from page_slim import minify_css, minify_script

LABS_FILE = "labs.md"
LABS_TITLE = "Hands-on labs"
ROOMS_DIR = os.path.join("labs", "rooms")
START_CMD = "docker compose --profile labs up -d --build"
STOP_CMD = "docker compose --profile labs down"
CLEAN_CMD = "labs/clean.sh"
PATHS = [  # (path key, section title); unknown paths follow in name order
    ("fresher", "Fresher path (L0)"),
    ("junior", "Junior path (L1)"),
    ("mid", "Mid-level path (L2)"),
    ("senior", "Senior path (L3)"),
    ("lead", "Lead path (L4)"),
]
ROOM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def _md(text):
    return markdown.markdown(str(text or ""), extensions=["fenced_code", "tables"])


def _md_inline(text):
    out = _md(text).strip()
    m = re.fullmatch(r"<p>(.*)</p>", out, re.S)
    return m.group(1) if m else out


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load_rooms(here):
    """Public room data from labs/rooms/*/room.json, sorted by path then order."""
    root = os.path.join(here, ROOMS_DIR)
    rooms = []
    if not os.path.isdir(root):
        return rooms
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name, "room.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                r = json.load(f)
        except (OSError, ValueError):
            continue
        if not ROOM_ID_RE.match(str(r.get("id", ""))) or not r.get("tasks") or not r.get("title"):
            continue
        r["_dir"] = name
        rooms.append(r)
    order = {k: i for i, (k, _) in enumerate(PATHS)}
    rooms.sort(key=lambda r: (order.get(r.get("path"), len(order)), str(r.get("path")), r.get("order", 0), r["id"]))
    return rooms


def path_title(key):
    return dict(PATHS).get(key) or (str(key).replace("-", " ").capitalize() + " path")


def _summary(brief):
    """First sentence or two of the brief as plain text, for the card."""
    text = re.sub(r"<[^>]+>", "", _md(brief))
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    text = re.sub(r"^#oncall,?\s*[\d:.]+\s*", "", text)
    cut = text[:190]
    if len(text) > 190:
        cut = cut.rsplit(" ", 1)[0] + " …"
    return cut


def _card(r):
    total = sum(int(t.get("points", 0)) for t in r["tasks"])
    src = r.get("source") or {}
    chips = [f'<span class="chip chip-level">{_esc(r.get("level", ""))}</span>']
    if r.get("minutes"):
        chips.append(f'<span class="chip">⏱ {_esc(r["minutes"])} min</span>')
    if r.get("difficulty"):
        chips.append(f'<span class="chip">{_esc(r["difficulty"])}</span>')
    chips.append(f'<span class="chip">{len(r["tasks"])} tasks · {total} pts</span>')
    url = str(src.get("url", ""))
    link = (f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(src.get("title", url))}</a>'
            if url.startswith("https://") else _esc(src.get("title", "")))
    return (f'<article class="lab-card" data-room="{_esc(r["id"])}" data-title="{_esc(r["title"])}" '
            f'data-path="{_esc(r.get("path", ""))}" data-order="{_esc(r.get("order", 0))}" data-points="{total}" '
            f'id="lab.{_esc(r["id"])}">'
            f'<div class="lab-card-top"><span class="lab-num">{int(r.get("order", 0)):02d}</span>{"".join(chips)}'
            f'<span class="lab-badge" data-badge></span></div>'
            f'<h3>{_esc(r["title"])}</h3>'
            f'<p class="lab-sum">{_esc(_summary(r.get("brief", "")))}</p>'
            f'<p class="lab-src">Source ({_esc(src.get("note", "adapted"))}): {link}</p>'
            f'<div class="lab-card-foot"><button type="button" class="lab-open" data-room="{_esc(r["id"])}">Read the room</button>'
            f'<span class="lab-lock" data-lock></span></div></article>')


def _task(i, t):
    qs = "".join(
        f'<label class="lab-q" data-q="{_esc(q["id"])}"><span class="lab-q-prompt">{_md_inline(q.get("prompt", ""))}</span>'
        f'<span class="lab-q-row"><input type="text" autocomplete="off" spellcheck="false" autocapitalize="off" '
        f'placeholder="{_esc(q.get("format", ""))}" aria-label="{_esc(q.get("prompt", ""))}"><span class="lab-mark" aria-hidden="true"></span></span>'
        f'<small class="lab-q-msg" role="status"></small></label>'
        for q in t.get("questions", []))
    checks = "".join(
        f'<li data-check="{_esc(c["id"])}"><span class="lab-mark" aria-hidden="true"></span><span>{_md_inline(c.get("describe", ""))}</span>'
        f'<small class="lab-c-reason"></small></li>' for c in t.get("checks", []))
    hints = "".join(f'<details class="lab-hint"><summary>Hint {n}</summary><div>{_md(h)}</div></details>'
                    for n, h in enumerate(t.get("hints", []), 1))
    return (f'<li class="lab-task" data-task="{_esc(t["id"])}" data-points="{int(t.get("points", 0))}">'
            f'<div class="lab-task-head"><span class="lab-task-n">{i}</span><h3>{_esc(t.get("title", ""))}</h3>'
            f'<span class="lab-task-pts">{int(t.get("points", 0))} pts</span></div>'
            f'<div class="lab-task-lock">🔒 Pass task {i - 1} to unlock this one.</div>'
            f'<div class="lab-task-body"><div class="lab-task-text">{_md(t.get("text", ""))}</div>'
            + (f'<div class="lab-qs">{qs}</div>' if qs else "")
            + (f'<ul class="lab-checks" aria-label="Checked on the lab machine">{checks}</ul>' if checks else "")
            + '<div class="lab-task-actions"><button type="button" class="lab-check-btn">Check</button>'
              '<span class="lab-task-msg" role="status"></span></div>'
            + hints + "</div></li>")


def _template(r):
    src = r.get("source") or {}
    url = str(src.get("url", ""))
    link = (f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(src.get("title", url))}</a>'
            if url.startswith("https://") else _esc(src.get("title", "")))
    tasks = "".join(_task(i, t) for i, t in enumerate(r["tasks"], 1))
    return (f'<template data-room="{_esc(r["id"])}"><div class="lab-brief">{_md(r.get("brief", ""))}</div>'
            f'<p class="lab-src">Real-world source ({_esc(src.get("note", "adapted"))}): {link}</p>'
            f'<ol class="lab-tasks">{tasks}</ol></template>')


def labs_markdown(here):
    """Markdown (with raw HTML blocks) for the virtual page labs.md."""
    rooms = load_rooms(here)
    paths = []
    for r in rooms:
        if not paths or paths[-1][0] != r.get("path"):
            paths.append((r.get("path"), []))
        paths[-1][1].append(r)
    total = sum(int(t.get("points", 0)) for r in rooms for t in r["tasks"])
    out = [
        f"# {LABS_TITLE}", "",
        f'<p class="lab-lead">Fix real incidents on a real (disposable) Ubuntu server: {len(rooms)} rooms, '
        f'{total} points. Each room is adapted from an incident engineers reported online, with the '
        'source linked. Read the brief, work in the terminal next to it, answer the questions and press '
        '<strong>Check</strong>: the checks run on the lab machine itself.</p>', "",
        '<div id="lab-app" class="lab-app no-index" data-state="checking">'
        '<div class="lab-status" role="status"><span class="lab-dot" aria-hidden="true"></span>'
        '<div class="lab-status-text"><strong data-status-title>Looking for the lab server…</strong>'
        '<span data-status-detail></span></div>'
        '<div class="lab-status-cmd" data-status-cmd><code>' + html.escape(START_CMD) + '</code>'
        '<button type="button" class="mbtn lab-copy" data-copy="' + html.escape(START_CMD, quote=True) + '">Copy</button>'
        '<button type="button" class="mbtn lab-retry" hidden>Check again</button></div></div></div>', "",
        "## How the labs work", "",
        "- **One disposable server per room.** Starting a room boots a fresh Ubuntu 24.04 container with "
        "real systemd in about five seconds. You work as `lab` with passwordless `sudo` in the terminal on the right.",
        "- **Checked on the machine.** *Check* runs the room's check scripts inside the lab as root. They "
        "test the real state (is the service active *and* enabled?), not the commands you typed.",
        "- **Unlocks.** The next task opens when every question and check of the current one passes. The "
        "next room of a path opens when you finish the previous room with all tasks passed.",
        "- **Nothing touches your computer.** Labs run on the internal Docker network `devlab-net` (no "
        "internet, no published ports) with memory, CPU and process limits. They are destroyed on *Finish*, "
        "on *Reset*, after 30 minutes idle and when the lab server stops. At most two run at once.",
        f"- **Start and stop.** Start the lab server with `{START_CMD}`. Stop it with `{STOP_CMD}`. "
        f"`{CLEAN_CMD}` removes everything the labs created (add `--all` to also forget your progress).",
        "- **Offline copy.** Without the lab server, every room still opens read-only, so you can study the "
        "brief and the tasks.", "",
    ]
    for key, items in paths:
        pts = sum(int(t.get("points", 0)) for r in items for t in r["tasks"])
        out += [f"## {path_title(key)}", "",
                f'<p class="lab-path-meta">{len(items)} rooms · {pts} points · rooms open in order.</p>', "",
                '<div class="lab-grid">' + "".join(_card(r) for r in items) + "</div>", ""]
    if not rooms:
        out += ["## Rooms", "", "No rooms are built yet (`labs/rooms/` is empty).", ""]
    out += ['<div class="lab-store" hidden>' + "".join(_template(r) for r in rooms) + "</div>", ""]
    return "\n".join(out)


def room_count(here):
    return len(load_rooms(here))


LABS_CSS = r"""
/* ===== hands-on labs (labs_site.py) ===== */
.lab-lead { font-size: 16px; }
.lab-status { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; margin: 14px 0 6px; padding: 14px 18px;
  border-radius: 16px; border: 1px solid color-mix(in srgb, var(--tone) 30%, var(--card-border));
  background: linear-gradient(120deg, color-mix(in srgb, var(--tone) 12%, var(--bg2)), var(--bg2) 70%);
  box-shadow: 0 18px 40px -32px var(--tone); }
.lab-dot { flex: none; width: 12px; height: 12px; border-radius: 50%; background: var(--fg-dim); }
.lab-app[data-state="online"] .lab-dot { background: var(--t-teal); box-shadow: 0 0 0 4px color-mix(in srgb, var(--t-teal) 25%, transparent), 0 0 12px var(--t-teal); }
.lab-app[data-state="offline"] .lab-dot { background: var(--t-amber); }
.lab-app[data-state="checking"] .lab-dot { animation: lab-pulse 1.2s ease-in-out infinite; }
@keyframes lab-pulse { 50% { opacity: .3; } }
.lab-status-text { flex: 1 1 260px; min-width: 0; display: flex; flex-direction: column; }
.lab-status-text span { color: var(--fg-dim); font-size: 13.5px; }
.lab-status-cmd { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.lab-status-cmd code, .lab-cmd code { font-size: 13px; }
.lab-app[data-state="online"] [data-status-cmd] { display: none; }
.lab-path-meta { color: var(--fg-dim); font-size: 13.5px; margin: -2px 0 10px; }
.lab-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 14px; margin: 8px 0 26px; }
.lab-card { position: relative; display: flex; flex-direction: column; gap: 6px; padding: 14px 16px 14px; border-radius: 16px;
  background: var(--card); border: 1px solid color-mix(in srgb, var(--tone) 22%, var(--card-border));
  box-shadow: inset 0 1px 0 var(--card-hi), 0 18px 34px -30px var(--tone); transition: box-shadow .2s, transform .2s; }
.lab-card:hover { box-shadow: inset 0 1px 0 var(--card-hi), 0 22px 40px -24px var(--tone); transform: translateY(-1px); }
.lab-card-top { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; }
.lab-card .chip { font-size: 11.5px; padding: 1px 8px; }
.lab-num { font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; color: var(--tone); margin-right: 2px; }
.lab-badge:empty, .lab-lock:empty { display: none; }
.lab-badge { margin-left: auto; font-size: 11.5px; font-weight: 700; border-radius: 999px; padding: 1px 9px;
  color: var(--on-accent); background: var(--accent2); }
.lab-card.is-running .lab-badge { background: var(--t-teal); }
.mod-section .lab-card h3 { margin: 2px 0 0; font-size: 16px; color: var(--fg); }
.lab-sum { margin: 0; font-size: 13.5px; color: var(--fg-dim); line-height: 1.5; }
.lab-src { margin: 0; font-size: 12.5px; color: var(--fg-dim); overflow-wrap: anywhere; }
.lab-card-foot { margin-top: auto; padding-top: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.lab-open, .lab-check-btn, .lab-big { font: inherit; font-size: 13.5px; font-weight: 650; cursor: pointer; border-radius: 9px; padding: 6px 14px;
  border: 1px solid var(--accent); color: var(--on-accent); background: var(--accent); }
.lab-open:hover, .lab-check-btn:hover, .lab-big:hover { filter: brightness(1.08); }
.lab-open:focus-visible, .lab-check-btn:focus-visible, .lab-big:focus-visible, .lab-view button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.lab-card.is-locked .lab-open { background: none; color: var(--accent); }
.lab-lock { font-size: 12.5px; color: var(--fg-dim); }
.lab-card.is-locked { opacity: .78; }
.lab-card.is-done { border-color: color-mix(in srgb, var(--accent2) 50%, var(--card-border)); }

/* room view: split screen above the page */
html.lab-on, html.lab-on body { overflow: hidden; }
.lab-view { position: fixed; inset: 0; z-index: 95; display: flex; flex-direction: column; background: var(--bg); color: var(--fg); }
.lab-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; padding: 8px 12px; background: var(--bg2); border-bottom: 1px solid var(--border); }
.lab-v-head { flex: 1 1 240px; min-width: 0; }
.lab-v-kicker { font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--t-teal); }
.lab-view h2#lab-v-title { margin: 0; padding: 0; border: 0; font-size: 18px; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lab-v-score { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 650; white-space: nowrap; }
.lab-meter { width: 110px; height: 8px; border-radius: 99px; background: var(--bg3); overflow: hidden; border: 1px solid var(--border); }
.lab-meter i { display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--t-teal), var(--accent2)); transition: width .4s ease; }
.lab-v-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.lab-view .mbtn.is-hot { background: var(--accent2); color: var(--on-accent); border-color: transparent; font-weight: 700; }
.lab-split { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(340px, 44%) 1fr; }
.lab-left { min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 18px 22px 40px; border-right: 1px solid var(--border); }
.lab-right { min-height: 0; display: flex; flex-direction: column; background: var(--term-bg); }
.lab-term-bar { display: flex; align-items: center; gap: 10px; padding: 7px 12px; background: var(--term-bar); color: var(--term-dim);
  border-bottom: 1px solid var(--term-border); font: 600 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.lab-term-dots { width: 46px; height: 11px; flex: none; background:
  radial-gradient(circle at 5px 5.5px, #ff5f57 0 4.2px, transparent 4.8px), radial-gradient(circle at 21px 5.5px, #febc2e 0 4.2px, transparent 4.8px),
  radial-gradient(circle at 37px 5.5px, #28c840 0 4.2px, transparent 4.8px); }
.lab-term-state { margin-left: auto; }
.lab-term-body { flex: 1; min-height: 0; position: relative; }
.lab-term-body iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; background: var(--term-bg); }
.lab-panel { max-width: 520px; margin: 9vh auto 0; padding: 22px 24px; color: var(--term-fg); line-height: 1.6; }
.lab-panel h3 { margin: 0 0 8px; color: var(--term-cmd); font-size: 18px; }
.lab-panel p { margin: 8px 0; color: var(--term-fg); }
.lab-panel small { color: var(--term-dim); }
.lab-panel code { background: rgba(255, 255, 255, .06); border: 1px solid var(--term-border); color: var(--term-cmd); border-radius: 5px; padding: 1px 5px; }
.lab-cmd { display: flex; align-items: center; gap: 8px; margin: 12px 0; padding: 9px 12px; border-radius: 10px; background: rgba(0, 0, 0, .25); border: 1px solid var(--term-border); }
.lab-cmd code { flex: 1; border: 0 !important; background: none !important; overflow-x: auto; white-space: nowrap; }
.lab-spin { width: 26px; height: 26px; border-radius: 50%; border: 3px solid var(--term-border); border-top-color: var(--term-prompt); animation: lab-rot .9s linear infinite; margin-bottom: 10px; }
@keyframes lab-rot { to { transform: rotate(360deg); } }
.lab-brief { padding: 12px 16px; border-radius: 14px; border: 1px solid var(--card-border); border-left: 4px solid var(--t-amber);
  background: linear-gradient(90deg, color-mix(in srgb, var(--t-amber) 10%, var(--bg2)), var(--bg2) 80%); }
.lab-brief p { margin: 6px 0; }
.lab-left .lab-src { margin: 8px 0 4px; }
.lab-tasks { list-style: none; margin: 14px 0 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.lab-task { border-radius: 14px; border: 1px solid var(--card-border); background: var(--card); padding: 12px 16px; }
.lab-task-head { display: flex; align-items: center; gap: 10px; }
.lab-task-head h3 { margin: 0; font-size: 16px; flex: 1; min-width: 0; color: var(--fg); }
.lab-task-n { flex: none; width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-size: 13px; font-weight: 800;
  background: color-mix(in srgb, var(--t-teal) 18%, var(--bg3)); color: var(--t-teal); }
.lab-task-pts { font-size: 12.5px; font-weight: 700; color: var(--fg-dim); white-space: nowrap; }
.lab-task-lock { display: none; margin: 8px 0 0 36px; font-size: 13px; color: var(--fg-dim); }
.lab-task.is-locked { opacity: .62; }
.lab-task.is-locked .lab-task-body { display: none; }
.lab-task.is-locked .lab-task-lock { display: block; }
.lab-task.is-passed { border-color: color-mix(in srgb, var(--accent2) 55%, var(--card-border)); }
.lab-task.is-passed .lab-task-n { background: var(--accent2); color: var(--on-accent); }
.lab-task.is-passed .lab-task-pts { color: var(--accent2); }
.lab-task.is-current { border-color: color-mix(in srgb, var(--t-teal) 55%, var(--card-border)); box-shadow: 0 14px 30px -24px var(--t-teal); }
.lab-task-body { margin-left: 36px; }
.lab-task-text p { margin: 6px 0; font-size: 14.5px; }
.lab-qs { display: flex; flex-direction: column; gap: 10px; margin: 10px 0; }
.lab-q { display: flex; flex-direction: column; gap: 4px; font-size: 14px; }
.lab-q-prompt { font-weight: 600; }
.lab-q-row { display: flex; align-items: center; gap: 8px; }
.lab-q input { flex: 1; min-width: 0; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--fg);
  font: 14px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.lab-q input:focus { outline: 2px solid var(--accent); border-color: transparent; }
.lab-q input:disabled { opacity: .7; }
.lab-q.is-ok input { border-color: var(--accent2); }
.lab-q.is-bad input { border-color: var(--danger); }
.lab-q-msg, .lab-c-reason { font-size: 12.5px; color: var(--fg-dim); }
.lab-q.is-bad .lab-q-msg, .lab-checks li.is-bad .lab-c-reason { color: var(--danger); }
.lab-mark { flex: none; width: 18px; text-align: center; font-weight: 800; }
.lab-q.is-ok .lab-mark::before, .lab-checks li.is-ok .lab-mark::before { content: "✓"; color: var(--accent2); }
.lab-q.is-bad .lab-mark::before, .lab-checks li.is-bad .lab-mark::before { content: "✗"; color: var(--danger); }
.lab-checks { list-style: none; margin: 8px 0; padding: 8px 10px; border-radius: 10px; background: var(--bg3); font-size: 13.5px; }
.lab-checks li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 6px; padding: 2px 0; }
.lab-checks li > span:nth-child(2) { flex: 1 1 0; min-width: 0; }
.lab-checks li .lab-mark::before { content: "○"; color: var(--fg-dim); }
.lab-c-reason { flex-basis: 100%; padding-left: 24px; }
.lab-task-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin: 8px 0; }
.lab-check-btn:disabled, .lab-big:disabled { opacity: .5; cursor: default; filter: none; }
.lab-task-msg { font-size: 13px; color: var(--fg-dim); }
.lab-task-msg.is-ok { color: var(--accent2); font-weight: 650; }
.lab-task-msg.is-bad { color: var(--danger); }
.lab-hint { margin: 6px 0; border: 1px dashed var(--border); border-radius: 9px; padding: 5px 10px; font-size: 13.5px; }
.lab-hint summary { cursor: pointer; color: var(--fg-dim); font-weight: 600; }
.lab-hint p { margin: 4px 0; }
.lab-result { margin-top: 16px; padding: 14px 18px; border-radius: 14px; border: 1px solid color-mix(in srgb, var(--accent2) 45%, var(--card-border));
  background: linear-gradient(120deg, color-mix(in srgb, var(--accent2) 12%, var(--bg2)), var(--bg2) 70%); }
.lab-result h3 { margin: 0 0 6px; font-size: 18px; color: var(--fg); }
.lab-result h4, .lab-result h5 { margin: 14px 0 4px; color: var(--t-teal); }
.lab-result pre { background: var(--term-bg); color: var(--term-fg); border-color: var(--term-border); }
.lab-toast { position: fixed; left: 50%; bottom: 26px; transform: translateX(-50%); z-index: 96; padding: 8px 16px; border-radius: 999px;
  background: var(--accent2); color: var(--on-accent); font-weight: 700; box-shadow: 0 10px 30px var(--shadow-strong); }
.lab-view .lab-readonly-note { margin: 10px 0 0; font-size: 13px; color: var(--fg-dim); }
@media (max-width: 900px) {
  .lab-split { grid-template-columns: 1fr; grid-template-rows: minmax(0, 1fr) minmax(300px, 46%); }
  .lab-left { border-right: 0; border-bottom: 1px solid var(--border); padding: 14px 16px 30px; }
  .lab-meter { display: none; }
}
@media (prefers-reduced-motion: reduce) { .lab-app[data-state="checking"] .lab-dot, .lab-spin { animation: none; } .lab-card { transition: none; } }
"""


LABS_SCRIPT = r"""<script>
/* hands-on labs (labs_site.py): room list state, split-screen room view, talks to /api/labs/ */
(function () {
  "use strict";
  var app = document.getElementById("lab-app");
  if (!app) return;
  var API = "/api/labs/";
  var START_CMD = "__START_CMD__";
  var root = document.documentElement;
  var cards = Array.prototype.slice.call(document.querySelectorAll(".lab-card"));
  var titleEl = app.querySelector("[data-status-title]"), detailEl = app.querySelector("[data-status-detail]");
  var retryBtn = app.querySelector(".lab-retry");
  var S = { online: false, rooms: {}, room: null, sid: null, session: null, busy: false, finished: false, lastAct: Date.now(), view: null, opener: null };
  var host = location.hostname;
  var canProbe = /^https?:$/.test(location.protocol) &&
    (host === "localhost" || host === "127.0.0.1" || host === "[::1]" || host === "::1" || /\.localhost$/.test(host));

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function card(id) { for (var i = 0; i < cards.length; i++) if (cards[i].getAttribute("data-room") === id) return cards[i]; return null; }
  function roomTitle(id) { var c = card(id); return c ? c.getAttribute("data-title") : id; }
  function copy(text, btn) { if (window.__handbookCopy) window.__handbookCopy(text, null, btn); }

  function api(path, body, ms) {
    var ctl = typeof AbortController === "function" ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, ms || 20000) : 0;
    var opt = { method: body === undefined ? "GET" : "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Accept": "application/json" } };
    if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    if (ctl) opt.signal = ctl.signal;
    return fetch(API + path, opt).then(function (r) {
      return r.text().then(function (txt) {
        var data = null;
        try { data = JSON.parse(txt); } catch (_) { data = null; }
        clearTimeout(timer);
        if (!r.ok || !data) {
          var e = new Error((data && data.message) || (r.status === 502 || r.status === 504 ? "The lab server is not running." : "The lab server answered " + r.status + "."));
          e.status = r.status; e.code = data && data.error; throw e;
        }
        return data;
      });
    }, function (err) { clearTimeout(timer); var e = new Error(err && err.name === "AbortError" ? "The lab server did not answer in time." : "The lab server is not reachable."); e.status = 0; throw e; });
  }

  /* ---------- status card and room list ---------- */
  function setState(state, title, detail) {
    app.setAttribute("data-state", state);
    titleEl.textContent = title; detailEl.textContent = detail || "";
    if (retryBtn) retryBtn.hidden = state !== "offline" || !canProbe;
  }
  function setOffline(why) {
    S.online = false; S.rooms = {};
    if (why === "file") setState("offline", "Read-only: the lab server only runs next to a local copy",
      "Rooms open read-only here. On your machine, start the lab server from the project folder, then open http://localhost:8173 and come back to this page.");
    else setState("offline", "The lab server is not running",
      "Rooms open read-only. Start it from the project folder (it builds the lab image the first time), then press Check again.");
    paintCards();
  }
  function paintCards() {
    cards.forEach(function (c) {
      var id = c.getAttribute("data-room"), r = S.rooms[id], btn = c.querySelector(".lab-open");
      var lock = c.querySelector("[data-lock]"), badge = c.querySelector("[data-badge]");
      c.classList.remove("is-locked", "is-done", "is-running");
      lock.textContent = ""; badge.textContent = "";
      if (!S.online) { btn.textContent = "Read the room"; return; }
      if (!r) { btn.textContent = "Read the room"; lock.textContent = "Not on this lab server yet: rebuild it."; return; }
      if (r.completed) { c.classList.add("is-done"); badge.textContent = "✓ " + r.best_points + "/" + r.total_points + " pts"; }
      if (r.session) { c.classList.add("is-running"); badge.textContent = "● running"; }
      if (r.locked) { c.classList.add("is-locked"); btn.textContent = "Preview"; lock.textContent = "🔒 Finish “" + roomTitle(r.requires) + "” first"; }
      else btn.textContent = r.session ? "Resume lab" : r.completed ? "Open again" : "Open room";
    });
  }
  function refreshRooms() {
    return api("rooms").then(function (d) {
      S.rooms = {};
      d.rooms.forEach(function (r) { S.rooms[r.id] = r; });
      var done = d.rooms.filter(function (r) { return r.completed; }).length;
      var pts = d.rooms.reduce(function (a, r) { return a + (r.best_points || 0); }, 0);
      var running = d.rooms.filter(function (r) { return r.session; }).length;
      setState("online", "Lab server running", done + " of " + d.rooms.length + " rooms finished · " + pts + " points · " +
        running + " of " + d.max_labs + " labs running");
      paintCards();
      if (S.view && !S.view.hidden && !S.sid && S.room && !S.finished) paintIdle();
    });
  }
  function probe() {
    if (!canProbe) { setOffline("file"); return Promise.resolve(); }
    setState("checking", "Looking for the lab server…", "");
    return api("health", undefined, 4000).then(function (h) {
      if (!h || !h.ok) throw new Error("bad health");
      S.online = true;
      if (!h.image_present) setState("online", "Lab server running", "The lab image is missing: run " + START_CMD + ".");
      return refreshRooms();
    }).catch(function () { setOffline("down"); });
  }

  /* ---------- the room view ---------- */
  function buildView() {
    var v = document.createElement("div");
    v.id = "lab-view"; v.className = "lab-view"; v.hidden = true;
    v.setAttribute("role", "dialog"); v.setAttribute("aria-modal", "true"); v.setAttribute("aria-labelledby", "lab-v-title");
    v.innerHTML =
      '<header class="lab-bar"><button type="button" class="mbtn" data-act="close">← Rooms</button>' +
      '<div class="lab-v-head"><div class="lab-v-kicker"></div><h2 id="lab-v-title" tabindex="-1"></h2></div>' +
      '<div class="lab-v-score"><span class="lab-pts"></span><span class="lab-meter" aria-hidden="true"><i></i></span></div>' +
      '<div class="lab-v-actions"><button type="button" class="mbtn" data-act="reset" title="Destroy this lab machine and start a fresh one">⟲ Reset</button>' +
      '<button type="button" class="mbtn mbtn-accent" data-act="finish" title="Destroy the lab machine and record the room">⚑ Finish</button>' +
      '<button type="button" class="mbtn" data-act="theme" title="Toggle light / dark theme" aria-label="Toggle theme">🌓</button>' +
      '<button type="button" class="mbtn" data-act="close" title="Close (the lab keeps running)" aria-label="Close">✕</button></div></header>' +
      '<div class="lab-split"><section class="lab-left" aria-label="Brief and tasks"></section>' +
      '<section class="lab-right" aria-label="Terminal"><div class="lab-term-bar"><span class="lab-term-dots" aria-hidden="true"></span>' +
      '<span>lab@lab — terminal</span><span class="lab-term-state"></span></div><div class="lab-term-body"></div></section></div>';
    document.body.appendChild(v);
    v.addEventListener("click", function (e) {
      if (e.target.closest("a[href^='#']")) { closeView(1); return; }   /* in-page link: leave the room, follow it */
      if (e.detail > 1) return;                 /* a double-click's second click does not repeat the action */
      var b = e.target.closest("[data-act]");
      if (b) { act(b.getAttribute("data-act")); return; }
      var chk = e.target.closest(".lab-check-btn");
      if (chk) { checkTask(chk.closest(".lab-task")); return; }
      var cp = e.target.closest("[data-copy]");
      if (cp) copy(cp.getAttribute("data-copy"), cp);
      var st = e.target.closest("[data-start]");
      if (st) startLab();
      if (e.target.closest("[data-again]")) openRoom(S.room, true);
      var nx = e.target.closest("[data-next]");
      if (nx) openRoom(nx.getAttribute("data-next"));
      if (e.target.closest("[data-reprobe]")) probe().then(function () { if (S.online && S.room) openRoom(S.room, true); });
    });
    v.addEventListener("keydown", function (e) {
      e.stopPropagation();                      /* the page's own shortcuts ("/", Esc) stay out of the room view */
      if (e.key === "Escape") closeView();
      else if (e.key === "Tab") {               /* focus stays in the room; the terminal iframe keeps its own keys */
        var f = [].filter.call(v.querySelectorAll("button,a[href],summary,input,iframe"), function (x) { return !x.disabled && x.getClientRects().length; }), a = document.activeElement;
        if (f.length && (e.shiftKey ? a === f[0] : a === f[f.length - 1])) { e.preventDefault(); f[e.shiftKey ? f.length - 1 : 0].focus(); }
      }
      else if (e.key === "Enter" && e.target.matches && e.target.matches(".lab-q input")) { e.preventDefault(); checkTask(e.target.closest(".lab-task")); }
    });
    ["keydown", "pointerdown"].forEach(function (t) { v.addEventListener(t, markActive, { passive: true }); });
    S.view = v;
    return v;
  }
  function markActive() { S.lastAct = Date.now(); }
  function el(sel) { return S.view.querySelector(sel); }
  function term() { return el(".lab-term-body"); }
  function termState(t) { el(".lab-term-state").textContent = t || ""; }

  function openRoom(id, fromHash) {
    if (!/^[a-z0-9][a-z0-9-]{1,62}$/.test(id || "")) return;
    var tpl = document.querySelector('template[data-room="' + id + '"]');
    if (!tpl) return;
    var v = S.view || buildView();
    if (S.room !== id) { S.sid = null; S.session = null; }
    S.room = id; S.finished = false; S.opener = S.opener || document.activeElement;
    var c = card(id);
    el(".lab-v-kicker").textContent = "Hands-on lab · " + (c ? c.querySelector(".chip-level").textContent : "");
    el("#lab-v-title").textContent = roomTitle(id);
    var left = el(".lab-left");
    left.innerHTML = "";
    left.appendChild(tpl.content.cloneNode(true));
    var res = document.createElement("div"); res.className = "lab-result"; res.hidden = true; left.appendChild(res);
    /* opened from a card: a history entry of its own, so Back closes the room */
    if (!fromHash) { try { if (v.hidden) history.pushState({ lab: 1 }, "", "#lab." + id); else history.replaceState(history.state, "", "#lab." + id); } catch (_) { /* ignore */ } }
    v.hidden = false; root.classList.add("lab-on");
    el("#lab-v-title").focus({ preventScroll: true });
    left.scrollTop = 0;
    var r = S.rooms[id];
    if (S.online && r && r.session) { S.sid = r.session; resume(); }
    else if (S.sid) resume();
    else paintIdle();
  }
  function closeView(keep) {                  /* keep: 1 = following a link, 2 = Back / Forward */
    if (!S.view || S.view.hidden) return;
    S.view.hidden = true; root.classList.remove("lab-on");
    term().innerHTML = "";
    var o = S.opener, c = card(S.room), J = window.__handbookJump, oc = o && o.closest && o.closest(".lab-card, .prove-strip");
    S.opener = null;
    if (S.online) refreshRooms().catch(function () { /* the list keeps its last state */ });
    function land(back) {                     /* back to the card it was opened from (or the room's card) */
      if (J && (back || !oc) && (oc || c)) J(oc || c, "center");
      if (oc) o.focus({ preventScroll: true });
    }
    if (keep) { if (keep > 1 && oc) land(1); return; }
    /* Close / Esc: pop the entry openRoom pushed (fromHash then lands), else just tidy the address */
    try { if (history.state && history.state.lab) { S.land = land; history.back(); return; } history.replaceState(null, "", "#m-labs"); } catch (_) { /* ignore */ }
    land();
  }

  /* left pane state */
  function paintTasks() {
    var st = S.session, tasks = Array.prototype.slice.call(el(".lab-left").querySelectorAll(".lab-task"));
    var readOnly = !S.online || !st || st.state !== "ready";
    var total = 0, got = 0, firstOpen = null;
    tasks.forEach(function (li, i) {
      var tid = li.getAttribute("data-task"), pts = +li.getAttribute("data-points") || 0;
      var ts = st && st.tasks[tid];
      total += pts;
      var passed = !!(ts && ts.passed), open = ts ? ts.open : (!S.online || i === 0);
      if (passed) got += pts;
      li.classList.toggle("is-passed", passed);
      li.classList.toggle("is-locked", S.online && !open);
      li.classList.toggle("is-current", !!(ts && open && !passed));
      if (ts && open && !passed && !firstOpen) firstOpen = li;
      li.querySelectorAll(".lab-q").forEach(function (q) {
        var ok = !!(ts && ts.answers[q.getAttribute("data-q")]), inp = q.querySelector("input");
        if (ok) { q.classList.add("is-ok"); q.classList.remove("is-bad"); }
        inp.disabled = readOnly || ok || passed;
      });
      li.querySelectorAll(".lab-checks li").forEach(function (c) {
        var r = ts && ts.checks[c.getAttribute("data-check")];
        c.classList.toggle("is-ok", !!(r && r.pass)); c.classList.toggle("is-bad", !!(r && !r.pass));
        c.querySelector(".lab-c-reason").textContent = r ? r.reason : "";
      });
      var btn = li.querySelector(".lab-check-btn");
      btn.disabled = readOnly || passed || S.busy;
      btn.title = !S.online ? "Start the lab server to check your work" : readOnly ? "Start the lab first" : "";
      var msg = li.querySelector(".lab-task-msg");
      if (passed) { msg.textContent = "Passed · +" + pts + " points"; msg.className = "lab-task-msg is-ok"; }
    });
    if (st) { got = st.points; total = st.total_points; }
    el(".lab-pts").textContent = got + " / " + total + " pts";
    el(".lab-meter i").style.width = (total ? Math.round(got * 100 / total) : 0) + "%";
    var fin = el('[data-act="finish"]'), rst = el('[data-act="reset"]');
    fin.disabled = !S.sid; rst.disabled = !S.sid;
    fin.classList.toggle("is-hot", !!(st && st.complete));
    return firstOpen;
  }
  function panel(html) { term().innerHTML = '<div class="lab-panel">' + html + "</div>"; }
  function cmdBox(cmd) { return '<div class="lab-cmd"><code>' + esc(cmd) + '</code><button type="button" class="mbtn" data-copy="' + esc(cmd) + '">Copy</button></div>'; }
  function paintIdle() {
    S.session = null; S.sid = null;
    paintTasks();
    termState("");
    if (!S.online) {
      panel("<h3>Start the lab server</h3>" + (canProbe
        ? "<p>The lab server is not running, so the room is read-only. From the project folder, run:</p>" + cmdBox(START_CMD) +
          "<p>Then press <button type=\"button\" class=\"mbtn\" data-reprobe>Check again</button> and <strong>Start the lab</strong>.</p>"
        : "<p>This copy of the handbook has no lab server, so the room is read-only. From the project folder on your machine, run:</p>" +
          cmdBox(START_CMD) + "<p>Then open <code>http://localhost:8173</code>, come back to this room and press <strong>Start the lab</strong>.</p>") +
        "<p><small>Labs are disposable containers on an internal Docker network: no internet, no published ports, " +
        "destroyed on Finish, Reset, 30 minutes idle and when you stop the lab server " +
        "(<code>docker compose --profile labs down</code>). Nothing is installed on your computer.</small></p>");
      return;
    }
    var r = S.rooms[S.room];
    if (r && r.locked) {
      panel("<h3>🔒 Locked</h3><p>Finish <strong>" + esc(roomTitle(r.requires)) + "</strong> with all tasks passed to open this room. " +
        "You can read it already.</p><p><button type=\"button\" class=\"lab-big\" data-next=\"" + esc(r.requires) + "\">Go to that room</button></p>");
      return;
    }
    panel("<h3>Ready when you are</h3><p>Starting the room boots a fresh Ubuntu server with real systemd and sets up the incident " +
      "(a few seconds). You are <code>lab</code> with passwordless <code>sudo</code>.</p>" +
      "<p><button type=\"button\" class=\"lab-big\" data-start>▶ Start the lab</button></p>" +
      "<p><small>No internet inside. Finish or Reset destroys the machine; so does 30 minutes without activity.</small></p>");
  }
  function showTerminal() {
    var src = S.session.terminal;
    var f = term().querySelector("iframe");
    if (f && f.getAttribute("src") === src) return;
    term().innerHTML = "";
    f = document.createElement("iframe");
    f.title = "Lab terminal"; f.src = src;
    f.addEventListener("load", function () {
      try { ["keydown", "pointerdown"].forEach(function (t) { f.contentWindow.document.addEventListener(t, markActive, { passive: true }); }); } catch (_) { /* not same-origin */ }
      try { f.contentWindow.focus(); } catch (_) { /* ignore */ }
    });
    term().appendChild(f);
  }
  function setSession(view) {
    S.session = view; S.sid = view.session;
    if (view.state === "ready") { showTerminal(); termState("● running"); }
    else if (view.state === "starting") { panel('<div class="lab-spin"></div><h3>Booting the lab machine…</h3><p>systemd, then the room setup, then your terminal.</p>'); termState("starting"); setTimeout(pollStart, 1200); }
    else { panel("<h3>The lab machine stopped</h3><p>It was shut down from inside. Press <strong>Reset</strong> for a fresh one.</p>"); termState("stopped"); }
    var first = paintTasks();
    return first;
  }
  function pollStart() {
    if (!S.sid || !S.session || S.session.state !== "starting") return;
    api("sessions/" + S.sid).then(setSession).catch(gone);
  }
  function gone(err) {
    if (err && err.status === 404) {
      S.sid = null; S.session = null;
      panel("<h3>This lab is gone</h3><p>" + esc(err.message) + "</p><p><button type=\"button\" class=\"lab-big\" data-start>▶ Start a fresh lab</button></p>");
      termState(""); paintTasks();
    } else toast(err ? err.message : "The lab server is not reachable.", true);
  }
  function resume() { api("sessions/" + S.sid).then(setSession).catch(gone); }
  function startLab() {
    if (S.busy || !S.room) return;
    S.busy = true; S.finished = false;
    panel('<div class="lab-spin"></div><h3>Booting the lab machine…</h3><p>systemd, then the room setup, then your terminal. About 5–15 seconds.</p>');
    termState("starting");
    api("rooms/" + S.room + "/start", {}, 200000).then(function (v) { S.busy = false; setSession(v); refreshRooms().catch(function () {}); })
      .catch(function (e) {
        S.busy = false;
        panel("<h3>The lab did not start</h3><p>" + esc(e.message) + "</p><p><button type=\"button\" class=\"lab-big\" data-start>Try again</button></p>");
        termState("");
      });
  }
  function qMark(q, ok, text) {
    q.classList.toggle("is-ok", ok === true); q.classList.toggle("is-bad", ok === false);
    q.querySelector(".lab-q-msg").textContent = text || "";
  }
  function checkTask(li) {
    if (!li || S.busy || !S.sid || !S.session || S.session.state !== "ready") return;
    var tid = li.getAttribute("data-task"), msg = li.querySelector(".lab-task-msg");
    var ts = S.session.tasks[tid];
    if (!ts || !ts.open || ts.passed) return;
    S.busy = true; paintTasks();
    msg.className = "lab-task-msg"; msg.textContent = "Checking on the lab machine…";
    var chain = Promise.resolve(), missing = 0;
    li.querySelectorAll(".lab-q").forEach(function (q) {
      var qid = q.getAttribute("data-q"), val = q.querySelector("input").value.trim();
      if (ts.answers[qid]) return;
      if (!val) { missing++; qMark(q, false, "Answer this question."); return; }
      chain = chain.then(function () {
        return api("sessions/" + S.sid + "/answer", { question: qid, answer: val }).then(function (r) {
          S.session = r.state; qMark(q, r.correct, r.correct ? "" : r.message);
        });
      });
    });
    var hasChecks = !!li.querySelector(".lab-checks li");
    chain.then(function () { return hasChecks ? api("sessions/" + S.sid + "/check", { task: tid }, 60000) : null; })
      .then(function (r) {
        if (r) S.session = r.state;
        S.busy = false;
        var next = paintTasks(), now = S.session.tasks[tid];
        if (now.passed) {
          toast("Task passed · +" + li.getAttribute("data-points") + " points");
          if (S.session.complete) { msg.textContent = "All tasks passed. Press Finish to record the room."; msg.className = "lab-task-msg is-ok"; }
          if (next) next.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
          msg.className = "lab-task-msg is-bad";
          msg.textContent = missing ? "Answer every question, then check again." : "Not yet: see the marks above.";
        }
      })
      .catch(function (e) { S.busy = false; paintTasks(); msg.className = "lab-task-msg is-bad"; msg.textContent = e.message; if (e.status === 404) gone(e); });
  }
  function finish() {
    if (!S.sid || S.busy) return;
    var complete = S.session && S.session.complete;
    if (!complete && !window.confirm("Finish now? The lab machine is destroyed, unfinished tasks earn no points and the next room stays locked.")) return;
    S.busy = true;
    api("sessions/" + S.sid + "/finish", {}, 60000).then(function (r) {
      S.busy = false; S.sid = null; S.session = null; S.finished = true;
      term().innerHTML = ""; termState("destroyed");
      panel("<h3>Lab machine destroyed</h3><p>Nothing of it is left. Your result is saved by the lab server.</p>" +
        "<p><button type=\"button\" class=\"lab-big\" data-again>Start this room again</button></p>");
      var res = el(".lab-result");
      res.hidden = false;
      res.innerHTML = "<h3>" + (r.complete ? "Room complete" : "Room finished") + " · " + r.points + " / " + r.total_points + " points</h3>" +
        (r.next_room ? (r.next_open ? '<p><button type="button" class="lab-big" data-next="' + esc(r.next_room) + '">Next room: ' + esc(roomTitle(r.next_room)) + " →</button></p>"
          : "<p>Pass every task to open the next room.</p>") : "") +
        "<h4>Walkthrough</h4>" + (r.walkthrough_html || "<p>No walkthrough for this room.</p>");
      res.querySelectorAll('a[href^="http"]').forEach(function (a) { a.target = "_blank"; a.rel = "noopener"; });
      el(".lab-pts").textContent = r.points + " / " + r.total_points + " pts";
      el('[data-act="finish"]').disabled = true; el('[data-act="reset"]').disabled = true;
      el(".lab-left").querySelectorAll(".lab-task input, .lab-check-btn").forEach(function (x) { x.disabled = true; });
      res.scrollIntoView({ behavior: "smooth", block: "start" });
      refreshRooms().catch(function () {});
    }).catch(function (e) { S.busy = false; toast(e.message, true); });
  }
  function reset() {
    if (!S.sid || S.busy) return;
    if (!window.confirm("Reset? This lab machine is destroyed and a fresh one starts; the tasks start over.")) return;
    S.busy = true;
    el(".lab-left").querySelectorAll(".lab-q").forEach(function (q) { qMark(q, null, ""); q.querySelector("input").value = ""; });
    el(".lab-left").querySelectorAll(".lab-task-msg").forEach(function (m) { m.textContent = ""; m.className = "lab-task-msg"; });
    panel('<div class="lab-spin"></div><h3>Resetting…</h3><p>Destroying the old machine and booting a fresh one.</p>');
    termState("starting");
    api("sessions/" + S.sid + "/reset", {}, 200000).then(function (v) { S.busy = false; setSession(v); })
      .catch(function (e) { S.busy = false; gone(e.status ? e : { status: 0, message: e.message }); });
  }
  function act(a) {
    if (a === "close") closeView();
    else if (a === "finish") finish();
    else if (a === "reset") reset();
    else if (a === "theme" && window.__handbookToggleTheme) window.__handbookToggleTheme();
  }
  var toastT = 0;
  function toast(text, bad) {
    var t = document.querySelector(".lab-toast");
    if (!t) { t = document.createElement("div"); t.className = "lab-toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = text; t.style.background = bad ? "var(--danger)" : ""; t.hidden = false;
    clearTimeout(toastT); toastT = setTimeout(function () { t.hidden = true; }, bad ? 5000 : 2600);
  }

  /* keep an active lab alive while the learner works (the reaper removes labs idle for 30 min) */
  setInterval(function () {
    if (!S.sid || !S.view || S.view.hidden || !S.session || S.session.state !== "ready") return;
    if (Date.now() - S.lastAct > 120000) return;
    api("sessions/" + S.sid + "/ping", {}).catch(function (e) { if (e.status === 404) gone(e); });
  }, 60000);

  /* wiring */
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".lab-open");
    if (b) { if (e.detail < 2) { S.opener = b; openRoom(b.getAttribute("data-room")); } return; }
    var cp = e.target.closest && e.target.closest(".lab-copy");
    if (cp) copy(cp.getAttribute("data-copy"), cp);
  });
  if (retryBtn) retryBtn.addEventListener("click", function () { probe(); });
  function fromHash() {
    var m = /^#lab\.([a-z0-9-]+)$/.exec(location.hash), l = S.land;
    S.land = null;
    if (m) openRoom(m[1], true);
    else if (S.view && !S.view.hidden) closeView(2);   /* Back / Forward out of a room */
    else if (l) l(1);
  }
  window.addEventListener("hashchange", fromHash);
  probe().then(fromHash);
  window.__labs = { state: S, probe: probe, openRoom: openRoom, closeView: closeView };
})();
</script>""".replace("__START_CMD__", START_CMD)


# the page is near the artifact size cap: comments and indentation go (page_slim.py)
LABS_CSS = minify_css(LABS_CSS) + "\n"
LABS_SCRIPT = minify_script(LABS_SCRIPT)
