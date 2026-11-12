#!/usr/bin/env python3
"""Build a single self-contained offline web UI (index.html) from the
troubleshooting markdown files. Re-run after editing any .md file or
roadmap.json:

    python3 build_site.py
    python3 build_site.py --out /tmp/test.html --artifact-out /tmp/test-artifact.html \
                          --roadmap /tmp/other-roadmap.json
    python3 build_site.py --artifact-out ''      # skip artifact.html

What it does
  * renders every module listed in MODULES (missing .md files are skipped with
    a WARNING, so the build never breaks while modules are still being written)
  * builds the grouped sidebar (group label -> module -> ## -> ###)
  * rewrites links between modules ("02-network.md", "08-dns.md#decision-tree")
    to in-page anchors
  * reads roadmap.json (if present), resolves every study/link item that names
    a handbook file + heading to an in-page anchor at BUILD time, and embeds it
    as <script type="application/json" id="roadmap-data"> for the offline
    3D course map (pure canvas-2D renderer, no libraries, no CDN)
  * writes the SAME page twice from one template:
      index.html     standalone offline file (doctype/html/head/body, meta tags)
      artifact.html  claude.ai artifact body: no doctype/html/head/body tags,
                     <title> on the very first line, then <style> and content
    Both use one theme-token structure (light on :root, dark via
    prefers-color-scheme or data-theme="dark"), bare-hash deep links
    (#m21-..., #map, #map.NODE_ID) and no external resources at all.
"""
import argparse
import html
import json
import os
import re
import sys

import markdown
from source_catalog import BY_MODULE, SOURCE_HEADINGS, SOURCE_CSS, SOURCE_SCRIPT, catalog_markdown, community_directory, community_markdown, source_anchor
from interview_site import (INTERVIEW_PAGES, INTERVIEW_FILES, INTERVIEW_CSS,
                            interview_markdown, backlink_markdown)
from command_decoder import (DECODER_FILE, DECODER_CSS, DECODER_SCRIPT, decoder_markdown,
                             inject_boxes, key_index, load_cards)
from site_ui import (LADDER_ID, MINI_TOWER, UI_CSS, UI_SCRIPT, decorate_body, insert_hints, launchpad,
                     load_hints, module_hero, tone_of)
from labs_site import LABS_FILE, LABS_CSS, LABS_SCRIPT, labs_markdown, room_count
from drills_site import DRILLS_FILE, DRILLS_CSS, DRILLS_SCRIPT, drills_markdown, drill_count
from prove_site import PROVE_CSS, module_topics, strip_html, topic_ladders
from backnav_site import BACKNAV_CSS, BACKNAV_HTML, BACKNAV_SCRIPT
from page_slim import EXTERNAL_LINKS_JS, compact_html, minify_css, minify_js

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "index.html")
ARTIFACT_OUT = os.path.join(HERE, "artifact.html")
ROADMAP = os.path.join(HERE, "roadmap.json")
HINTS = load_hints(HERE)  # "Safest next step" lines under chosen headings (hints/safest-step.tsv)
LADDER_FILE = "57-method-protect-risk-ladder.md"

# (file, sidebar title, icon, sidebar group) -- this order is the sidebar AND page order
MODULES = [
    ("README.md", "Home / Triage", "🏠", "Start here"),
    # generated at build time from commands/ (see command_decoder.py)
    ("command-decoder.md", "Command Decoder: What & Why", "🔍", "Start here"),
    ("34-roadmap.md", "Zero-to-Hero Roadmap", "🗺️", "Start here"),
    ("40-career-ladder.md", "Career Ladder: Fresher → Senior", "🎓", "Start here"),
    ("55-paths-onprem-vs-cloud.md", "On-Prem or Cloud Path", "⚖️", "Start here"),
    ("54-practice-arena.md", "Practice Arena", "🎮", "Start here"),
    ("56-sources-and-verification.md", "Sources & Verification", "📚", "Start here"),

    # hands-on labs: generated at build time from labs/rooms/ (see labs_site.py)
    ("labs.md", "Hands-on labs", "🧪", "Labs"),
    # decision drills: generated at build time from drills/*.json (see drills_site.py)
    ("drills.md", "Decision drills", "🎯", "Labs"),

    # interview practice: generated at build time from interview/ (see interview_site.py)
    ("interview-guide.md", "Interview Practice: How to Use", "🎤", "Interview practice"),
    ("interview-fresher.md", "Interview: Fresher", "🌱", "Interview practice"),
    ("interview-junior-mid.md", "Interview: Junior → Mid-level", "🌿", "Interview practice"),
    ("interview-senior.md", "Interview: Senior", "🌳", "Interview practice"),
    ("interview-every-stage.md", "Interview: Every Stage", "🪜", "Interview practice"),

    ("57-method-protect-risk-ladder.md", "Method: PROTECT & the Risk Ladder", "🛟", "Real incidents & playbooks"),
    ("21-case-apache-443-dokploy.md", "Case: Apache vs Dokploy on 443", "🧩", "Real incidents & playbooks"),
    ("22-playbook-ports-inventory.md", "Who Owns This Port?", "🔌", "Real incidents & playbooks"),
    ("23-playbook-slow-system.md", "Why Is It Slow?", "🐢", "Real incidents & playbooks"),
    ("24-playbook-network-speed.md", "Network Speed", "📶", "Real incidents & playbooks"),
    ("25-playbook-site-down.md", "Site Down: DNS·TLS·Proxy", "🚨", "Real incidents & playbooks"),
    ("26-playbook-containers-k8s.md", "Docker & K8s Incidents", "🧯", "Real incidents & playbooks"),
    ("35-deployment-patterns.md", "Deployment Patterns", "🚀", "Real incidents & playbooks"),

    # tool deep dives + problem libraries collected from GitHub issues, forums and docs
    ("52-devops-day-to-day.md", "DevOps Day to Day", "☕", "Real-world problems & OSS toolbox"),
    ("45-dokploy-and-self-hosted-paas.md", "Dokploy & Self-Hosted PaaS", "🏗️", "Real-world problems & OSS toolbox"),
    ("43-traefik-and-reverse-proxies.md", "Traefik & Reverse Proxies", "🚦", "Real-world problems & OSS toolbox"),
    ("47-cicd-gitlab-jenkins-actions-argocd.md", "CI/CD Toolbox", "🏭", "Real-world problems & OSS toolbox"),
    ("48-wazuh-and-security-tools.md", "Wazuh & Security Tools", "🕵️", "Real-world problems & OSS toolbox"),
    ("49-observability-stack-problems.md", "Observability Stack", "🔭", "Real-world problems & OSS toolbox"),
    ("51-problems-databases-storage-backup.md", "Databases & Backups: Problems", "🗃️", "Real-world problems & OSS toolbox"),
    ("50-problems-cloud-iac-proxmox.md", "Cloud, IaC & Proxmox: Problems", "🧱", "Real-world problems & OSS toolbox"),
    ("44-problems-docker-swarm-registry.md", "Docker, Swarm & Harbor: Problems", "⚓", "Real-world problems & OSS toolbox"),
    ("46-problems-kubernetes.md", "Kubernetes: Problems", "⛵", "Real-world problems & OSS toolbox"),
    # 41, 42 and 53 were written by parallel batches; listed here so the build stays warning-free
    ("41-problems-linux-systems.md", "Linux & systemd: Problems", "🔧", "Real-world problems & OSS toolbox"),
    ("42-problems-network-dns-tls-vpn.md", "Network, DNS & TLS: Problems", "🕸️", "Real-world problems & OSS toolbox"),
    ("53-oss-devops-toolbox.md", "OSS DevOps Toolbox Map", "🛠️", "Real-world problems & OSS toolbox"),

    ("27-learn-linux.md", "Linux", "🐧", "Learn: fresher → senior"),
    ("28-learn-networking.md", "Networking, DNS & TLS", "🛰️", "Learn: fresher → senior"),
    ("29-learn-webservers-proxies.md", "Web Servers & Proxies", "🔀", "Learn: fresher → senior"),
    ("30-learn-docker.md", "Docker", "🚢", "Learn: fresher → senior"),
    ("31-learn-kubernetes.md", "Kubernetes (CKA)", "🎡", "Learn: fresher → senior"),
    ("32-learn-performance-observability.md", "Performance & Observability", "📈", "Learn: fresher → senior"),
    ("33-learn-cicd-iac-sre.md", "CI/CD, IaC & SRE", "🔁", "Learn: fresher → senior"),
    ("36-learn-cloud-aws.md", "Cloud & AWS", "🌥️", "Learn: fresher → senior"),
    ("37-learn-security-devsecops.md", "Security & DevSecOps", "🔐", "Learn: fresher → senior"),
    ("38-learn-databases-ops.md", "Databases for DevOps", "🗄️", "Learn: fresher → senior"),
    ("39-learn-senior-architecture.md", "Senior: Architecture & Leadership", "🏛️", "Learn: fresher → senior"),

    ("01-storage-disk.md", "Storage & Disk", "💾", "Command reference"),
    ("02-network.md", "Network", "🌐", "Command reference"),
    ("03-cpu-performance.md", "CPU & Performance", "⚡", "Command reference"),
    ("04-memory.md", "Memory", "🧠", "Command reference"),
    ("05-processes.md", "Processes", "🔄", "Command reference"),
    ("06-logs-journal.md", "Logs & Journal", "📜", "Command reference"),
    ("07-services-systemd.md", "Services & systemd", "⚙️", "Command reference"),
    ("08-dns.md", "DNS", "📡", "Command reference"),
    ("09-ssh-remote-access.md", "SSH & Remote Access", "🔑", "Command reference"),
    ("10-users-permissions-security.md", "Users & Permissions", "🛡️", "Command reference"),
    ("11-packages.md", "Packages", "📦", "Command reference"),
    ("12-time-ntp.md", "Time & NTP", "🕐", "Command reference"),
    ("13-kernel-system.md", "Kernel & Hardware", "🖥️", "Command reference"),
    ("14-docker-containers.md", "Docker & Containers", "🐳", "Command reference"),
    ("15-kubernetes.md", "Kubernetes", "☸️", "Command reference"),
    ("16-aws-cloud.md", "AWS", "☁️", "Command reference"),
    ("17-windows.md", "Windows", "🪟", "Command reference"),
    ("20-macos.md", "macOS", "🍎", "Command reference"),
    ("18-web-http-tls.md", "Web, HTTP & TLS", "🔒", "Command reference"),
    # was 🚀 — that icon now belongs to 35 Deployment Patterns, so every module keeps a unique icon
    ("19-cheatsheet.md", "Cheat Sheet", "📋", "Command reference"),
]

# Modules that get the "Open the 3D course map" banner (when roadmap.json exists)
MAP_HOST_FILES = ("README.md", "34-roadmap.md")

# The previous builds used positional ids (#mod0 .. #mod20) in this order.
# They are mapped to the new stable ids so old bookmarks keep working.
LEGACY_ORDER = [
    "README.md", "01-storage-disk.md", "02-network.md", "03-cpu-performance.md",
    "04-memory.md", "05-processes.md", "06-logs-journal.md", "07-services-systemd.md",
    "08-dns.md", "09-ssh-remote-access.md", "10-users-permissions-security.md",
    "11-packages.md", "12-time-ntp.md", "13-kernel-system.md", "14-docker-containers.md",
    "15-kubernetes.md", "16-aws-cloud.md", "17-windows.md", "20-macos.md",
    "18-web-http-tls.md", "19-cheatsheet.md",
]

STUDY_TYPES = {"note", "kodekloud", "video", "lab", "read", "doc", "book", "course", "playbook", "link"}


# --------------------------------------------------------------------------- #
# Markdown modules
# --------------------------------------------------------------------------- #
def section_id(fname):
    """Stable section id: '02-network.md' -> 'm02', 'README.md' -> 'm-readme'."""
    m = re.match(r"(\d+)-", fname)
    if m:
        return "m" + m.group(1)
    stem = os.path.splitext(fname)[0].lower()
    return "m-" + (re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "x")


def _norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def resolve_heading(mod, query):
    """First h2/h3 (document order) whose text contains `query` (case-insensitive).
    Falls back to a punctuation-insensitive match and then to the slug id."""
    q = (query or "").strip().lower()
    if not q:
        return None
    for h in mod["heads"]:
        if q in h["name"].lower():
            return h["id"]
    nq = _norm(q)
    if nq:
        for h in mod["heads"]:
            if nq in _norm(h["name"]):
                return h["id"]
    for h in mod["heads"]:
        if q in h["id"]:
            return h["id"]
    return None


GENERATED_FILES = INTERVIEW_FILES | {DECODER_FILE, LABS_FILE, DRILLS_FILE}
_CARD_INDEX = []


def card_index():
    """(match-key index, tools with subcommand keys) for the Command Decoder, loaded once."""
    if not _CARD_INDEX:
        _CARD_INDEX.append(key_index(load_cards(HERE)[1]))
    return _CARD_INDEX[0]


def render_module(fname, title, icon, group):
    """Convert one markdown file into a module dict (body html + toc + heading index)."""
    if fname in INTERVIEW_FILES:
        text = interview_markdown(fname, HERE, {f: t for f, t, *_ in MODULES})
    elif fname == DECODER_FILE:
        text = decoder_markdown(HERE)
    elif fname == LABS_FILE:
        text = labs_markdown(HERE)
    elif fname == DRILLS_FILE:
        text = drills_markdown(HERE)
    else:
        with open(os.path.join(HERE, fname), encoding="utf-8-sig") as f:
            text = f.read()
        text += backlink_markdown(fname, HERE)
    if fname == "56-sources-and-verification.md":
        text += community_directory(HERE) + catalog_markdown(HERE)
    if fname in BY_MODULE:
        text += community_markdown(HERE, fname)
    # drop the top-level "# NN — Title" heading; the section header replaces it
    text = re.sub(r"\A\s*# .*\n", "", text, count=1)
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "md_in_html"])  # md_in_html: on-prem/cloud env blocks
    body = md.convert(text)
    sec = section_id(fname)
    prefix = sec + "-"
    # every heading id gets the module prefix -> unique across the whole page
    body = re.sub(r'(<h[1-6]) id="', rf'\1 id="{prefix}', body)
    cmd_uses = []
    if fname not in GENERATED_FILES:
        # "Decode the commands used in this submodule" box under every ## heading that runs commands
        body, cmd_uses = inject_boxes(body, text, *card_index())
    hint_missing = []
    if fname in HINTS and fname not in GENERATED_FILES:
        body, hint_missing = insert_hints(body, md.toc_tokens, HINTS[fname], prefix)
    # presentation: submodule cards, terminal-framed code, callouts (see site_ui.py)
    body = decorate_body(body)

    def prefix_tokens(tokens):
        return [{
            "id": prefix + t["id"],
            "name": html.unescape(t["name"]),
            "level": t["level"],
            "children": prefix_tokens(t.get("children", [])),
        } for t in tokens]

    toc = prefix_tokens(md.toc_tokens)
    heads, ids = [], set()

    def walk(tokens):
        for t in tokens:
            ids.add(t["id"])
            if t["level"] in (2, 3):
                heads.append({"level": t["level"], "name": t["name"], "id": t["id"]})
            walk(t["children"])

    walk(toc)
    return {"file": fname, "title": title, "icon": icon, "group": group, "sec": sec,
            "body": body, "toc": toc, "heads": heads, "ids": ids, "est": estimate_height(body),
            "cmd_uses": cmd_uses, "hint_missing": hint_missing}


def estimate_height(body):
    """Rough rendered height (px) of a module on a desktop/laptop screen (the page is desktop-only).
    Used as contain-intrinsic-size for content-visibility:auto, so the page can
    skip laying out off-screen modules; the browser remembers the real size
    once a module has been rendered, so this only needs to be in the right range."""
    pres = re.findall(r"<pre[^>]*>(.*?)</pre>", body, re.S)
    pre_lines = sum(p.count("\n") + 1 for p in pres)
    rest = re.sub(r"<pre[^>]*>.*?</pre>", " ", body, flags=re.S)
    chars = len(html.unescape(re.sub(r"<[^>]+>", "", rest)))
    blocks = len(re.findall(r"<(?:p|li|tr|blockquote|table)\b", rest))
    heads = len(re.findall(r"<h[234]\b", rest))
    fixed = pre_lines * 19.5 + len(pres) * 46 + blocks * 9 + heads * 46 + 160
    return int(fixed + chars / 105 * 24)


MAP_HASH_RE = re.compile(r"map(?:[/.](.*))?")


def map_href(node_id):
    """Deep link into the 3D map. Bare-hash form only ('#map', '#map.NODE_ID');
    the old '#map/NODE_ID' form is still accepted by the page for back-compat."""
    return "#map." + node_id if node_id else "#map"


def rewrite_links(mod, by_file, known_files, missing_links):
    """Same-module '#frag' links and cross-module 'file.md#frag' links -> in-page anchors;
    '#map' / '#map/ID' -> '#map' / '#map.ID'; external links open in a new tab."""
    prefix = mod["sec"] + "-"

    def fix_local(m):
        frag = m.group(1)
        mm = MAP_HASH_RE.fullmatch(frag)
        if mm:                                   # link into the 3D course map
            return f'href="{map_href(html.unescape(mm.group(1) or ""))}"'
        if prefix + frag in mod["ids"]:
            return f'href="#{prefix}{frag}"'
        return m.group(0)

    body = re.sub(r'href="#([^"]+)"', fix_local, mod["body"])

    def fix_md(m):
        target, frag = m.group(1), m.group(2)
        t = by_file.get(target)
        if t:
            anchor = t["sec"]
            if frag:
                frag = html.unescape(frag)
                if t["sec"] + "-" + frag in t["ids"]:
                    anchor = t["sec"] + "-" + frag
                else:
                    anchor = resolve_heading(t, frag.replace("-", " ")) or t["sec"]
            return f'href="#{anchor}"'
        key = (mod["file"], target, target in known_files)
        missing_links[key] = missing_links.get(key, 0) + 1
        esc = html.escape(target, quote=True)
        # no href at all: an inert placeholder link (a bare "#" would jump to the top)
        return f'data-missing="{esc}" title="{esc} is not part of this build yet"'

    body = re.sub(r'href="(?:\./)?([\w.-]+\.md)(?:#([^"]*))?"', fix_md, body)
    # external links: real <a target="_blank" rel="noopener"> (needed inside the artifact frame too)
    body = re.sub(r'<a href="(https?://[^"]+)"(?![^>]*\btarget=)', r'<a href="\1" target="_blank" rel="noopener"', body)
    mod["body"] = body


def title_from_file(fname):
    """'# 35 — Deployment patterns' -> 'Deployment patterns' (fallback: file stem)."""
    try:
        with open(os.path.join(HERE, fname), encoding="utf-8-sig") as f:
            first = f.readline().strip()
    except OSError:
        first = ""
    m = re.match(r"#\s+(?:\d+\s*[—–-]\s*)?(.+)", first)
    return m.group(1).strip() if m else os.path.splitext(fname)[0]


def load_modules(warn):
    mods = []
    for fname, title, icon, group in MODULES:
        if fname not in GENERATED_FILES and not os.path.isfile(os.path.join(HERE, fname)):
            warn(f"{fname} not found — skipped (not written yet?)")
            continue
        mods.append(render_module(fname, title, icon, group))
    # numbered modules that exist on disk but are not in MODULES are still published (group "More")
    listed = {f for f, *_ in MODULES}
    for fname in sorted(os.listdir(HERE)):
        if re.fullmatch(r"\d+-[\w.-]+\.md", fname) and fname not in listed:
            warn(f"{fname} is not listed in MODULES — appended under 'More'; "
                 "add it to MODULES in build_site.py to set its title, icon and position")
            mods.append(render_module(fname, title_from_file(fname), "📄", "More"))
    by_file = {m["file"]: m for m in mods}
    known = listed | set(by_file)
    missing_links = {}
    for m in mods:
        rewrite_links(m, by_file, known, missing_links)
    for (src, dst, is_known), n in sorted(missing_links.items()):
        why = "is not built yet" if is_known else "is not listed in MODULES"
        warn(f"{src}: {n} link(s) to {dst}, which {why} — rendered as an inactive link")
    hint_warnings(HINTS, mods, by_file, warn)
    # Command Decoder: the "Used in" line of each card is built by the page script from the
    # submodule boxes (command_decoder.DECODER_SCRIPT), so it costs nothing in the page source
    return mods, by_file



def hint_warnings(hints, mods, by_file, warn):
    """Safest-next-step hints whose module or heading is missing, or whose ladder link would be dead."""
    for fname, rows in hints.items():
        if fname not in by_file:
            warn(f"hints: {fname} is not in this build — {len(rows)} safest-next-step hint(s) skipped")
    for m in mods:
        for heading in m.get("hint_missing", ()):
            warn(f"hints: heading '{heading}' is not exactly one heading of {m['file']} — hint skipped")
    if hints and LADDER_ID not in by_file.get(LADDER_FILE, {}).get("ids", ()):
        warn(f"hints: the risk ladder anchor #{LADDER_ID} is missing from {LADDER_FILE} — hint links are dead")


# --------------------------------------------------------------------------- #
# roadmap.json -> embedded, anchor-resolved data for the 3D map
# --------------------------------------------------------------------------- #
ID_RE = re.compile(r"[A-Za-z0-9._~-]+")

# "Job search unlocks at each milestone" (3D map panel): milestone node -> (roles you can now apply
# for, interview pack (file, heading or None), career-ladder heading). JOB_COMMON goes with every one.
JOB_UNLOCK = {
    "milestone-fresher": ("junior roles", ("interview-fresher.md", None), "Junior questions"),
    "milestone-junior": ("mid-level roles", ("interview-junior-mid.md", None), "Mid-level questions"),
    "milestone-mid": ("senior roles", ("interview-senior.md", None), "Senior questions"),
    "cka-exam": ("roles that ask for the CKA", ("interview-junior-mid.md", "Kubernetes (CKA)"), "Certifications versus projects"),
    "milestone-senior": ("senior and platform roles", ("interview-senior.md", "Deployment Patterns"), "Senior questions"),
    "milestone-lead": ("lead and SRE roles", ("interview-senior.md", "Architecture & Leadership"), "Lead and SRE questions"),
}
JOB_COMMON = (("interview-every-stage.md", None), "Your CV and LinkedIn")
LADDER = "40-career-ladder.md"


def job_links(by_file, ids, warn):
    """JOB_UNLOCK -> {"c": common links, "n": {node id: {"r": roles, "l": links}}}; a link is
    [anchor, label, kind] with kind "i" (interview pack) or "c" (career ladder)."""
    def link(fname, heading, kind):
        mod = by_file.get(fname)
        if not mod:
            warn(f"job unlock: {fname} is not in this build — link skipped")
            return None
        if not heading:
            return [mod["sec"], mod["title"], kind]
        anchor = resolve_heading(mod, heading)
        if not anchor:
            warn(f"job unlock: heading '{heading}' not found in {fname} — link skipped")
            return None
        name = next(h["name"] for h in mod["heads"] if h["id"] == anchor)
        return [anchor, ("Career ladder" if kind == "c" else mod["title"]) + " › " + name, kind]

    def pair(pack, ladder):
        return [x for x in (link(*pack, "i"), link(LADDER, ladder, "c")) if x]
    out = {"c": pair(*JOB_COMMON), "n": {}}
    for nid, (roles, pack, ladder) in JOB_UNLOCK.items():
        if nid not in ids:
            warn(f"job unlock: roadmap node '{nid}' not found — skipped")
            continue
        out["n"][nid] = {"r": roles, "l": pair(pack, ladder)}
    return out


def process_roadmap(path, by_file, warn):
    """Validate roadmap.json and resolve handbook links for the 3D map.

    Data contract (ROADMAP_SCHEMA in the workflow script, plus the optional extras below):
      levels[]  {id, name, goal?, exit_test?, stage?}
                "stage" is OPTIONAL: the career stage for that level, e.g.
                {"id": "L2", "name": "Troubleshooter", "stage": "Mid-level"}. When present
                the map shows "L2 · Mid-level · Troubleshooter" on floors, chips, tooltips
                and in the list view; when absent it falls back to "L2 · Troubleshooter".
      tracks[]  {id, name, color "#rgb"/"#rrggbb"}
      nodes[]   {id (letters, digits, . _ ~ - so it can live in a #map.ID deep link),
                 title, level, track, summary, why, learn[], practice[], troubleshoot[],
                 commands[], exit_check, prereqs[], study[], links[]}
                study/links items: {type, label, file+heading | url, note?}; for file items
                the build adds "anchor" (resolved in-page id), "module_title", or
                "pending": true when the file is not part of this build.
                prove_sites[] (optional): research/practice.json site ids ("id" or {id, deep}),
                at most 3; prove_site.topic_ladders() turns them, plus the drills and lab rooms
                that name the node, into node["prove"] for the map's "Prove it" section.
      path[]    recommended order (node ids); derived topologically when missing.
    """
    if not os.path.isfile(path):
        print(f"info: {os.path.basename(path)} not found — 3D course map disabled")
        return None
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        warn(f"{path} could not be parsed ({e}) — 3D course map disabled")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        warn(f"{path}: expected an object with a 'nodes' array — 3D course map disabled")
        return None

    levels = [lv for lv in data.get("levels") or [] if isinstance(lv, dict) and lv.get("id")]
    tracks = [t for t in data.get("tracks") or [] if isinstance(t, dict) and t.get("id")]
    data["levels"], data["tracks"] = levels, tracks
    for lv in levels:
        st = lv.get("stage")
        if st is not None and not (isinstance(st, str) and st.strip()):
            warn(f"roadmap level '{lv['id']}': 'stage' should be a non-empty string like \"Mid-level\" — ignored")
            lv.pop("stage", None)
    level_ids = {lv["id"] for lv in levels}
    track_ids = set()
    for t in tracks:
        track_ids.add(t["id"])
        col = t.get("color", "")
        if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", str(col)):
            warn(f"roadmap track '{t['id']}': color {col!r} is not #rgb/#rrggbb — a grey fallback is used")

    nodes, seen = [], set()
    for n in data["nodes"]:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or not n["id"]:
            warn(f"roadmap: skipped a node without a string 'id': {str(n)[:60]}")
            continue
        if n["id"] in seen:
            warn(f"roadmap: duplicate node id '{n['id']}' — later copy ignored")
            continue
        seen.add(n["id"])
        if not ID_RE.fullmatch(n["id"]):
            warn(f"roadmap: node id '{n['id']}' has characters outside letters, digits, . _ ~ - "
                 "(its #map.ID deep link will be percent-encoded)")
        nodes.append(n)
    data["nodes"] = nodes
    ids = {n["id"] for n in nodes}

    resolved = fallback = 0
    for n in nodes:
        nid = n["id"]
        # Tie existing learning topics to their saved research without modifying
        # the prerequisite graph or claiming source coverage for unrelated modules.
        domains = sorted({BY_MODULE[item["file"]]
                          for kind in ("study", "links")
                          for item in (n.get(kind) or [])
                          if isinstance(item, dict) and item.get("file") in BY_MODULE})
        if "56-sources-and-verification.md" in by_file:
            for domain in domains:
                n.setdefault("links", []).append({
                    "type": "read", "label": f"Sources & verification: {domain}",
                    "file": "56-sources-and-verification.md", "heading": SOURCE_HEADINGS[domain],
                })
        if n.get("level") not in level_ids:
            warn(f"roadmap node '{nid}': level {n.get('level')!r} is not defined in 'levels'")
        if n.get("track") not in track_ids:
            warn(f"roadmap node '{nid}': track {n.get('track')!r} is not defined in 'tracks'")
        prereqs = n.get("prereqs") or []
        if not isinstance(prereqs, list):
            warn(f"roadmap node '{nid}': 'prereqs' must be a list of node ids")
            n["prereqs"] = prereqs = []
        for p in prereqs:
            if p not in ids:
                warn(f"roadmap node '{nid}': unknown prereq '{p}' (ignored on the map)")
            elif p == nid:
                warn(f"roadmap node '{nid}': lists itself as a prereq (ignored)")
        for kind in ("study", "links"):
            items = n.get(kind) or []
            if not isinstance(items, list):
                warn(f"roadmap node '{nid}': '{kind}' must be a list")
                n[kind] = []
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                typ = item.get("type")
                if typ and typ not in STUDY_TYPES:
                    warn(f"roadmap node '{nid}': unknown {kind} type {typ!r} (shown with a generic icon)")
                url = item.get("url")
                if url and not re.match(r"https?://", str(url)):
                    warn(f"roadmap node '{nid}': {kind} url {url!r} is not http(s) — it will not be clickable")
                fname = item.get("file")
                if not fname:
                    continue
                mod = by_file.get(fname)
                if not mod:
                    item["pending"] = True
                    warn(f"roadmap node '{nid}': {kind} file {fname} is not in this build — shown as 'coming soon'")
                    continue
                item["module_title"] = mod["title"]
                heading = item.get("heading")
                anchor = resolve_heading(mod, heading) if heading else None
                if heading and not anchor:
                    fallback += 1
                    warn(f"roadmap node '{nid}': heading '{heading}' not found in {fname} — linking to the module top")
                else:
                    resolved += 1
                item["anchor"] = anchor or mod["sec"]

    # cycles in the prerequisite graph
    parents = {n["id"]: [p for p in (n.get("prereqs") or []) if isinstance(p, str) and p in ids and p != n["id"]]
               for n in nodes}
    state = {}

    def dfs(u, stack):
        state[u] = 1
        stack.append(u)
        for p in parents[u]:
            if state.get(p) == 1:
                cyc = stack[stack.index(p):] + [p]
                warn("roadmap: prerequisite cycle " + " → ".join(cyc))
            elif not state.get(p):
                dfs(p, stack)
        stack.pop()
        state[u] = 2

    for n in nodes:
        if not state.get(n["id"]):
            dfs(n["id"], [])

    # guided path
    path = data.get("path") or []
    if not isinstance(path, list):
        warn("roadmap: 'path' must be a list of node ids")
        path = []
    clean, pos = [], {}
    for pid in path:
        if pid not in ids:
            warn(f"roadmap path: unknown node '{pid}' (skipped)")
            continue
        if pid in pos:
            warn(f"roadmap path: '{pid}' listed twice (second ignored)")
            continue
        pos[pid] = len(clean)
        clean.append(pid)
    for pid in clean:
        for p in parents[pid]:
            if p not in pos:
                warn(f"roadmap path: '{pid}' needs '{p}', which is not on the path")
            elif pos[p] > pos[pid]:
                warn(f"roadmap path: '{pid}' comes before its prerequisite '{p}'")
    not_on_path = [n["id"] for n in nodes if n["id"] not in pos]
    if clean and not_on_path:
        warn(f"roadmap path: {len(not_on_path)} node(s) not on the guided path: {', '.join(not_on_path[:8])}"
             + (" …" if len(not_on_path) > 8 else ""))
    data["path"] = clean
    data["job"] = job_links(by_file, ids, warn)
    print(f"roadmap: {len(nodes)} nodes, {len(levels)} levels, {len(tracks)} tracks, "
          f"{len(clean)} path steps, {resolved} handbook links resolved, {fallback} fell back to module top")
    return data


def json_for_script(obj):
    """JSON that is safe inside <script type="application/json">."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


# --------------------------------------------------------------------------- #
# HTML assembly
# --------------------------------------------------------------------------- #
def nav_module(mod):
    sub = []
    for t in mod["toc"]:
        if t["level"] != 2:
            continue
        sub.append(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a>')
        kids = [k for k in t["children"] if k["level"] == 3]
        if kids:
            sub.append("<ul>")
            for k in kids:
                sub.append(f'<li><a href="#{k["id"]}">{html.escape(k["name"])}</a></li>')
            sub.append("</ul>")
        sub.append("</li>")
    sub_html = f'<ul class="subnav">{"".join(sub)}</ul>' if sub else ""
    chev = ('<span class="chev" title="Show or hide the sections of this module">▸</span>'
            if sub_html else "")
    expanded = ' aria-expanded="false"' if sub_html else ""
    # one line per module: the sidebar is ~3,400 links, so every byte of template repeats
    return (f'\n<li class="module" data-mod="{mod["sec"]}" data-tone="{tone_of(mod["group"])}">'
            f'<button class="mod-btn" data-target="#{mod["sec"]}"{expanded}>'
            f'<span class="mod-icon">{mod["icon"]}</span><span class="mod-name">{html.escape(mod["title"])}</span>'
            f'{chev}</button>{sub_html}</li>')


MAP_NAV = ('\n<li class="nav-extra"><a class="map-nav" href="#map">'
           '<span class="mod-icon">🧭</span><span class="mod-name">3D course map</span></a></li>')


def build_nav(mods, has_map):
    parts, groups = [], []
    for m in mods:
        if not groups or groups[-1][0] != m["group"]:
            groups.append((m["group"], []))
        groups[-1][1].append(m)
    for gname, gmods in groups:
        parts.append(f'\n<li class="nav-group" data-tone="{tone_of(gname)}">{html.escape(gname)}</li>')
        parts.extend(nav_module(m) for m in gmods)
        if has_map and gname == "Start here":
            parts.append(MAP_NAV)
    if has_map and not any(g == "Start here" for g, _ in groups):
        parts.insert(0, MAP_NAV)
    return compact_html("".join(parts))


def map_banner(roadmap):
    n, lvs = len(roadmap["nodes"]), roadmap["levels"]
    stages = [str(lv.get("stage")).strip() for lv in lvs if lv.get("stage")]
    span = f" — {html.escape(stages[0])} to {html.escape(stages[-1])}" if len(stages) >= 2 else ""
    return (f'<div class="map-banner no-index">{MINI_TOWER}'
            f'<div class="mb-text"><strong>🗺️ Open the 3D course map</strong>'
            f'<span>{n} topics on {len(lvs)} levels{span}. Click any topic to see why it matters, what to study '
            f'(handbook, KodeKloud, videos, labs), how to troubleshoot it and what comes next — '
            f'or start the guided path.</span></div>'
            f'<a class="map-banner-btn" href="{map_href("")}">Open the 3D map →</a></div>')


HOME_LINKS = [  # (file, icon, title, subtitle) for the home page launchpad
    (DECODER_FILE, "🔍", "Command Decoder", "What each command means and why it works: ping vs mtr, netstat vs ss…"),
    ("57-method-protect-risk-ladder.md", "🛟", "Broken, people waiting?", "Start here: the PROTECT loop, the risk ladder and a printable card"),
    ("21-case-apache-443-dokploy.md", "🧩", "Apache vs Dokploy on 443", "Your real incident as a step-by-step runbook"),
    ("22-playbook-ports-inventory.md", "🔌", "Who owns this port?", "Every listener mapped to a process, unit and config"),
    ("27-learn-linux.md", "🐧", "Learn path: Linux first", "Fresher → senior, each step with why and what next"),
    ("interview-guide.md", "🎤", "Interview practice", "114 prompts by stage, answers collapsed"),
    (LABS_FILE, "🧪", "Hands-on labs", "Fix a real incident on a disposable server, checked live"),
    (DRILLS_FILE, "🎯", "Decision drills", "Play a real outage move by move, then read the post-mortem"),
    ("54-practice-arena.md", "🎮", "Practice Arena", "165 free-first sites and games to practise safely"),
]


def build_content(mods, roadmap, prove=None):
    """prove: (catalog, module file -> topic ids) for the end-of-module "Prove it" strips."""
    parts = []
    nodes_by_id = {n["id"]: n for n in roadmap["nodes"]} if roadmap else {}
    by_file = {m["file"]: m for m in mods}
    for m in mods:
        banner = map_banner(roadmap) if roadmap and m["file"] in MAP_HOST_FILES else ""
        if m["file"] == "README.md":
            banner += launchpad([(f'#{by_file[f]["sec"]}', ic, t, sub, tone_of(by_file[f]["group"]))
                                 for f, ic, t, sub in HOME_LINKS if f in by_file])
        domain = BY_MODULE.get(m["file"])
        if domain:
            banner += (f'<p class="source-notice"><a href="#{source_anchor(domain)}">Browse saved sources for this library</a>'
                       ' · Source labels distinguish recorded checks, unverified references and discovery links.</p>')
        n_cmds = len({c for c, _ in m.get("cmd_uses", [])})
        extra, unit = "", ("submodule", "submodules")
        if m["file"] == DECODER_FILE:
            extra = f'🧩 {m["body"].count(chr(60) + "div class=" + chr(34) + "cmd-card" + chr(34))} command cards'
            unit = ("family", "families")
        elif m["file"] in INTERVIEW_FILES:
            unit = ("topic", "topics")
        elif m["file"] == LABS_FILE:
            extra, unit = f"🧪 {room_count(HERE)} rooms", ("section", "sections")
        elif m["file"] == DRILLS_FILE:
            n = drill_count(HERE)
            extra, unit = f"🎯 {n} drill{'s' if n != 1 else ''}", ("section", "sections")
        strip = ""
        if prove and m["file"] in prove[1]:
            strip = strip_html(m["file"], prove[1][m["file"]], nodes_by_id, prove[0], map_href)
        parts.append(f'''
<section class="mod-section" id="{m["sec"]}" data-title="{html.escape(m["title"])}" data-tone="{tone_of(m["group"])}" style="--h-d:{m["est"]}px">
  {module_hero(m, n_cmds, extra, unit)}
  {banner}
  {m["body"]}{strip}
</section>''')
    # whitespace between block tags, entity spellings, link boilerplate (page_slim.compact_html)
    return compact_html("".join(parts))


MAP_OVERLAY = r"""
<div id="map" class="map-overlay" role="dialog" aria-modal="true" aria-labelledby="map-heading" hidden>
  <div class="map-toolbar">
    <div class="map-title" id="map-heading">🗺️<span> Course map: fresher → senior</span></div>
    <div class="map-search">
      <input id="map-q" type="search" placeholder="Find a topic… (/)" aria-label="Find a topic" autocomplete="off" spellcheck="false" aria-controls="map-q-results">
      <div id="map-q-results" class="map-q-results" role="listbox" aria-label="Matching topics" hidden></div>
    </div>
    <div class="map-actions">
      <button type="button" class="mbtn mbtn-accent" id="map-path-btn" aria-pressed="false" title="Walk the recommended study order step by step">▶<span class="lbl"> Guided path</span></button>
      <button type="button" class="mbtn" id="map-flat-btn" aria-pressed="false" title="Flat 2D grid: levels as rows, tracks as columns">◫<span class="lbl"> Flat 2D</span></button>
      <button type="button" class="mbtn" id="map-list-btn" aria-pressed="false" title="Accessible list of every topic, grouped by level">☰<span class="lbl"> List</span></button>
      <button type="button" class="mbtn" id="map-reset-btn" title="Reset the camera">⟲<span class="lbl"> Reset view</span></button>
      <div class="env-switch" data-env-switch role="group" aria-label="On-premise or cloud"></div>
      <button type="button" class="mbtn" id="map-theme-btn" title="Toggle light/dark theme" aria-label="Toggle theme">🌓</button>
      <button type="button" class="mbtn" id="map-close-btn" title="Close the map (Esc)" aria-label="Close the map">✕</button>
    </div>
  </div>
  <div class="map-legend" aria-label="Filters">
    <span class="lg-label">Tracks</span><div id="map-legend-tracks" class="lg-group"></div>
    <span class="lg-label">Levels</span><div id="map-legend-levels" class="lg-group"></div>
    <span id="map-progress" class="lg-progress"></span>
  </div>
  <div id="map-stage" class="map-stage">
    <canvas id="map-canvas" tabindex="0" role="img" aria-label="3D course map. Levels are floors stacked bottom to top (L0 Fresher at the bottom), tracks are coloured sectors around the tower, lines are prerequisites. Use the List button for a keyboard-friendly list of all topics."></canvas>
    <div id="map-pathbar" class="map-pathbar" role="toolbar" aria-label="Guided path" hidden></div>
    <div id="map-tip" class="map-tip" hidden></div>
    <aside id="map-list" class="map-list" aria-label="All topics by level" hidden></aside>
    <aside id="map-panel" class="map-panel" aria-labelledby="map-panel-title" hidden></aside>
    <div class="map-hint" aria-hidden="true">Drag to orbit · scroll / pinch to zoom · click a topic · ← → ↑ ↓ rotate · + − zoom · Esc closes</div>
    <div id="map-toast" class="map-toast" role="status" hidden></div>
    <div id="map-live" class="sr-only" aria-live="polite"></div>
  </div>
</div>
"""


TEMPLATE = r"""__DOC_START__
<style>
__SOURCE_CSS__
/* ===== theme tokens =====================================================
   Light palette on bare :root; dark palette when the OS prefers dark (unless
   the reader picked light) and again when the reader picked dark. The theme
   toggle only sets data-theme on the root element; every colour comes from here.
   ======================================================================== */
:root {
  color-scheme: light;
  --bg: #f7f9fb; --bg2: #ffffff; --bg3: #eef2f6; --fg: #1c2733; --fg-dim: #576775;
  --accent: #0b69c7; --accent2: #157347; --border: #d7dfe7; --code-bg: #f0f3f7;
  --mark: #ffe58f; --danger: #b42318; --on-accent: #ffffff;
  --accent-soft: rgba(11, 107, 203, .10); --banner-a: rgba(11, 107, 203, .10); --banner-b: rgba(21, 115, 71, .08);
  --shadow: rgba(16, 32, 52, .16); --shadow-strong: rgba(16, 32, 52, .28); --scrim: rgba(16, 26, 38, .38);
  --node-hi: #ffffff; --check-ink: #0b1a10;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0f141a; --bg2: #161d26; --bg3: #1d2733; --fg: #d8e1ea; --fg-dim: #8e9cab;
    --accent: #4da3ff; --accent2: #7ee0a3; --border: #263241; --code-bg: #10171f;
    --mark: #6b5300; --danger: #ff7b72; --on-accent: #0f141a;
    --accent-soft: rgba(77, 163, 255, .13); --banner-a: rgba(77, 163, 255, .14); --banner-b: rgba(126, 224, 163, .10);
    --shadow: rgba(0, 0, 0, .45); --shadow-strong: rgba(0, 0, 0, .55); --scrim: rgba(0, 0, 0, .5);
    --node-hi: #ffffff; --check-ink: #0b1a10;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0f141a; --bg2: #161d26; --bg3: #1d2733; --fg: #d8e1ea; --fg-dim: #8e9cab;
  --accent: #4da3ff; --accent2: #7ee0a3; --border: #263241; --code-bg: #10171f;
  --mark: #6b5300; --danger: #ff7b72; --on-accent: #0f141a;
  --accent-soft: rgba(77, 163, 255, .13); --banner-a: rgba(77, 163, 255, .14); --banner-b: rgba(126, 224, 163, .10);
  --shadow: rgba(0, 0, 0, .45); --shadow-strong: rgba(0, 0, 0, .55); --scrim: rgba(0, 0, 0, .5);
  --node-hi: #ffffff; --check-ink: #0b1a10;
}
/* layout tokens: --tb is the topbar height without the notch inset */
:root { --tb: 54px; --gutter: 16px; --tb-total: var(--tb); }

* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; font: 15px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg); color: var(--fg); overflow-x: hidden; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
a[data-missing] { color: var(--fg-dim); text-decoration: underline dotted; cursor: help; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
.skip-link { position: fixed; left: 16px; top: -60px; z-index: 50; padding: 8px 14px; border-radius: 8px;
  background: var(--accent); color: var(--on-accent); font-weight: 700; }
.skip-link:focus { top: 8px; }

/* ---------- layout ---------- */
#topbar { position: fixed; top: 0; left: 0; right: 0; z-index: 30; height: var(--tb-total);
  display: flex; flex-wrap: wrap; align-items: center; align-content: center; gap: 8px 10px;
  padding: 8px 16px;
  background: var(--bg2); border-bottom: 1px solid var(--border); }
#topbar .brand { flex: none; display: flex; align-items: center; gap: 4px; min-width: 0; font-weight: 700; white-space: nowrap; }
.brand-text { overflow: hidden; text-overflow: ellipsis; }
#topbar .brand small { color: var(--fg-dim); font-weight: 400; margin-left: 6px; }
.tb-btn { flex: none; display: inline-flex; align-items: center; justify-content: center; gap: 4px;
  height: 38px; min-width: 38px; padding: 0 10px; border-radius: 8px; border: 1px solid var(--border);
  background: none; color: var(--fg); font: inherit; font-size: 15px; cursor: pointer; white-space: nowrap; }
.tb-btn:hover { background: var(--bg3); }
.tb-btn:focus-visible, #q:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
#hamburger { display: none; font-size: 18px; }
#map-btn { border-color: var(--accent); color: var(--accent); font-size: 14px; font-weight: 600; }
#sidebar { position: fixed; top: var(--tb-total); bottom: 0; left: 0; width: 300px; z-index: 20;
  overflow-y: auto; overscroll-behavior: contain; background: var(--bg2); border-right: 1px solid var(--border);
  padding: 10px 8px 40px; }
#scrim { position: fixed; top: var(--tb-total); left: 0; right: 0; bottom: 0; z-index: 19; background: var(--scrim); }
#main { margin-left: 300px; padding: calc(var(--tb-total) + 20px) 34px 60px; max-width: 1000px; min-width: 0;
  overflow-wrap: break-word; }
#main:focus { outline: none; }
@media (max-width: 1000px) { #topbar .brand small { display: none; } }
@media (max-width: 900px) {
  #sidebar { width: min(320px, 86vw); transform: translateX(-104%); visibility: hidden;
    transition: transform .2s ease, visibility 0s linear .2s; }
  #sidebar.open { transform: none; visibility: visible; transition: transform .2s ease;
    box-shadow: 0 0 30px var(--shadow-strong); }
  #main { margin-left: 0; padding: calc(var(--tb-total) + 16px) var(--gutter) 60px; }
  #hamburger { display: inline-flex; }
}

/* ---------- sidebar ---------- */
#navlist { list-style: none; margin: 0; padding: 0; }
.nav-group { margin: 16px 10px 4px; font-size: 11px; font-weight: 700; letter-spacing: .09em;
  text-transform: uppercase; color: var(--fg-dim); }
.nav-group:first-child { margin-top: 4px; }
.module { margin: 1px 0; }
.mod-btn { display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;
  background: none; border: 0; color: var(--fg); font: inherit; padding: 7px 10px;
  border-radius: 8px; cursor: pointer; }
.mod-btn:hover { background: var(--bg3); }
.module.active > .mod-btn { background: var(--bg3); color: var(--accent); font-weight: 600;
  box-shadow: inset 3px 0 0 var(--accent); }
.mod-icon { width: 1.4em; text-align: center; flex: none; }
.mod-name { flex: 1; min-width: 0; }
.chev { color: var(--fg-dim); transition: transform .15s, background .15s; font-size: 12px;
  padding: 4px 7px; margin: -4px -6px -4px 0; border-radius: 6px; line-height: 1; }
.chev:hover { background: var(--bg3); color: var(--fg); }
.module.expanded .chev { transform: rotate(90deg); }
.subnav { list-style: none; margin: 0 0 4px; padding: 0 0 0 20px; display: none;
  border-left: 1px solid var(--border); margin-left: 19px; }
.module.expanded .subnav { display: block; }
.subnav ul { list-style: none; padding-left: 14px; }
.subnav a { display: block; padding: 3px 8px; border-radius: 6px; color: var(--fg-dim);
  font-size: 13.5px; }
.subnav ul a { font-size: 12.8px; }
.subnav a:hover { color: var(--fg); background: var(--bg3); text-decoration: none; }
.subnav a.current { color: var(--accent); font-weight: 600; background: var(--accent-soft);
  box-shadow: inset 2px 0 0 var(--accent); border-radius: 0 6px 6px 0; }
.nav-extra { margin: 1px 0; }
.map-nav { display: flex; align-items: center; gap: 9px; padding: 7px 10px; border-radius: 8px;
  color: var(--accent); font-weight: 600; }
.map-nav:hover { background: var(--bg3); text-decoration: none; }

/* ---------- search ---------- */
#search { flex: 1 1 200px; max-width: 520px; position: relative; min-width: 0; }
#q { width: 100%; height: 38px; padding: 0 12px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg); color: var(--fg); font: inherit; }
#q:focus { outline: 2px solid var(--accent); border-color: transparent; }
#results { position: absolute; top: 44px; left: 0; right: 0; max-height: min(70vh, 560px);
  overflow-y: auto; overscroll-behavior: contain; background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; display: none; box-shadow: 0 10px 40px var(--shadow); }
#results.show { display: block; }
.result { display: block; padding: 9px 13px; border-bottom: 1px solid var(--border);
  cursor: pointer; color: var(--fg); }
.result:last-child { border-bottom: 0; }
.result:hover, .result.sel { background: var(--bg3); text-decoration: none; }
.result .path { font-size: 12px; color: var(--fg-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.result .snippet { font-size: 13px; color: var(--fg); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.result mark { background: var(--mark); color: inherit; border-radius: 3px; padding: 0 1px; }
.result .nores { color: var(--fg-dim); }

/* ---------- content ---------- */
.mod-section { padding-top: 6px; margin-bottom: 26px; scroll-margin-top: calc(var(--tb-total) + 4px); }
.mod-section + .mod-section { border-top: 1px solid var(--border); padding-top: 26px; }
/* render off-screen modules lazily; the build estimates their height */
.cv > .mod-section { content-visibility: auto; contain-intrinsic-size: auto var(--h-d, 4000px); }
.mod-section h1 { font-size: 26px; line-height: 1.3; margin: 6px 0 14px; overflow-wrap: anywhere; }
.mod-section h2 { font-size: 20px; line-height: 1.35; margin: 30px 0 10px; padding-bottom: 6px;
  border-bottom: 1px solid var(--border); }
.mod-section h3 { font-size: 16.5px; line-height: 1.4; margin: 22px 0 8px; color: var(--accent2); }
.mod-section h2, .mod-section h3, .mod-section h4 { overflow-wrap: anywhere; }
#main [id] { scroll-margin-top: calc(var(--tb-total) + 14px); }
pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 10px; max-width: 100%;
  padding: 12px 14px; overflow-x: auto; position: relative; font-size: 13px; line-height: 1.5; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
:not(pre) > code { background: var(--code-bg); border: 1px solid var(--border);
  border-radius: 5px; padding: 1px 5px; font-size: 13px; overflow-wrap: anywhere; }
blockquote { margin: 12px 0; padding: 8px 14px; border-left: 3px solid var(--accent);
  background: var(--bg3); border-radius: 0 8px 8px 0; color: var(--fg-dim); }
table { border-collapse: collapse; width: 100%; max-width: 100%; margin: 12px 0; font-size: 14px;
  display: block; overflow-x: auto; }
th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left;
  vertical-align: top; }
th { background: var(--bg3); }
tr:nth-child(even) td { background: var(--bg2); }
img, video, canvas, svg { max-width: 100%; }
.copy-btn { position: absolute; top: 6px; right: 6px; font-size: 11px; padding: 3px 8px;
  border-radius: 6px; border: 1px solid var(--border); background: var(--bg2);
  color: var(--fg-dim); cursor: pointer; opacity: 0; transition: opacity .15s; font-family: inherit; }
pre:hover .copy-btn, .copy-btn:focus-visible { opacity: 1; }
.copy-btn:hover { color: var(--fg); }
.flash { animation: flash 1.6s ease-out; }
@keyframes flash { 0% { background: var(--mark); } 100% { background: transparent; } }
#totop { position: fixed; right: 16px; bottom: 18px;
  z-index: 25; display: none; background: var(--bg3); color: var(--fg); border: 1px solid var(--border);
  border-radius: 50%; width: 42px; height: 42px; font-size: 18px; cursor: pointer; box-shadow: 0 4px 16px var(--shadow); }
#totop.show { display: block; }

/* ---------- "open the map" banner ---------- */
.map-banner { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 12px 18px; margin: 4px 0 20px; padding: 14px 16px; border: 1px solid var(--border);
  border-radius: 12px; background: linear-gradient(135deg, var(--banner-a), var(--banner-b)); }
.map-banner .mb-text { flex: 1 1 260px; min-width: 0; }
.map-banner strong { display: block; font-size: 16.5px; margin-bottom: 2px; }
.map-banner span { color: var(--fg-dim); font-size: 14px; }
.map-banner-btn { flex: none; background: var(--accent); color: var(--on-accent); font-weight: 700;
  padding: 8px 16px; border-radius: 999px; white-space: nowrap; }
.map-banner-btn:hover { text-decoration: none; filter: brightness(1.08); }

/* ---------- 3D course map overlay ---------- */
html.map-open, html.map-open body { overflow: hidden; }
.map-overlay { position: fixed; inset: 0; z-index: 100; display: flex; flex-direction: column;
  background: var(--bg); color: var(--fg); }
.map-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 10px;
  padding: 8px 12px;
  background: var(--bg2); border-bottom: 1px solid var(--border); }
.map-title { font-weight: 700; white-space: nowrap; }
.map-search { position: relative; flex: 1 1 180px; max-width: 360px; min-width: 120px; }
.map-search input { width: 100%; padding: 6px 11px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg); color: var(--fg); font: inherit; font-size: 14px; }
.map-search input:focus { outline: 2px solid var(--accent); border-color: transparent; }
.map-q-results { position: absolute; top: 40px; left: 0; right: 0; z-index: 6; max-height: 55vh;
  overflow-y: auto; background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
  box-shadow: 0 10px 40px var(--shadow); }
.map-q-results button { display: block; width: 100%; text-align: left; border: 0;
  border-bottom: 1px solid var(--border); background: none; color: var(--fg); font: inherit;
  font-size: 14px; padding: 7px 12px; cursor: pointer; }
.map-q-results button:last-child { border-bottom: 0; }
.map-q-results button:hover, .map-q-results button.sel { background: var(--bg3); }
.map-q-results small { display: block; color: var(--fg-dim); font-size: 12px; }
.map-q-results .nores { padding: 8px 12px; color: var(--fg-dim); font-size: 13.5px; }
.map-actions { display: flex; flex-wrap: wrap; gap: 6px; margin-left: auto; }
.mbtn { background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 8px;
  padding: 5px 10px; font: inherit; font-size: 13.5px; line-height: 1.4; cursor: pointer; white-space: nowrap; }
.mbtn:hover { background: var(--bg3); }
.mbtn:disabled { opacity: .45; cursor: default; background: var(--bg); }
.mbtn-accent { border-color: var(--accent); color: var(--accent); }
.mbtn[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: transparent; }
.map-overlay button:focus-visible, .map-overlay a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.map-legend { display: flex; align-items: center; gap: 6px 8px; padding: 6px 12px; white-space: nowrap;
  overflow-x: auto; scrollbar-width: thin; background: var(--bg2); border-bottom: 1px solid var(--border); }
/* one scrollable row; a fade on the right edge says "more chips this way" until the end is reached */
.map-legend.more { -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 64px), transparent);
  mask-image: linear-gradient(90deg, #000 calc(100% - 64px), transparent); }
.lg-group { display: flex; gap: 5px; }
.lg-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: var(--fg-dim); margin-left: 4px; }
.lg-chip { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--border);
  background: var(--bg); color: var(--fg); border-radius: 999px; padding: 1px 10px; font: inherit;
  font-size: 12.5px; cursor: pointer; }
.lg-chip:hover { border-color: var(--c, var(--accent)); }
.lg-chip[aria-pressed="false"] { opacity: .45; text-decoration: line-through; }
.lg-name { color: var(--fg-dim); }
@media (max-width: 1100px) { .lg-name { display: none; } }
.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; flex: none;
  background: var(--c, var(--accent)); }
.lg-progress { margin-left: auto; padding-left: 12px; font-size: 12.5px; font-weight: 600; color: var(--accent2); }
.map-stage { position: relative; flex: 1; min-height: 0; overflow: hidden; }
#map-canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block;
  touch-action: none; cursor: grab; outline: none; }
#map-canvas.dragging { cursor: grabbing; }
#map-canvas:focus-visible { box-shadow: inset 0 0 0 2px var(--accent); }
.map-tip { position: absolute; left: 0; top: 0; z-index: 4; max-width: 280px; pointer-events: none;
  background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 6px 10px;
  font-size: 13px; line-height: 1.4; box-shadow: 0 6px 24px var(--shadow); }
.map-tip strong { display: block; }
.tip-meta { color: var(--fg-dim); font-size: 12px; }
.map-hint { position: absolute; left: 12px; bottom: 10px; z-index: 1; font-size: 12px;
  color: var(--fg-dim); pointer-events: none; }
.map-toast { position: absolute; left: 50%; bottom: 40px; transform: translateX(-50%); z-index: 7;
  max-width: calc(100% - 32px); background: var(--bg2); border: 1px solid var(--border); overflow-wrap: anywhere;
  border-radius: 10px; padding: 8px 14px; font-size: 14px; box-shadow: 0 8px 30px var(--shadow); }
.map-pathbar { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); z-index: 4;
  display: flex; align-items: center; gap: 6px; max-width: calc(100% - 24px); padding: 5px 6px 5px 14px;
  background: var(--bg2); border: 1px solid var(--accent); border-radius: 999px;
  box-shadow: 0 8px 30px var(--shadow); }
.pb-label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; }
.pb-label strong { color: var(--accent); }
.map-panel, .map-list { position: absolute; top: 12px; bottom: 12px; z-index: 3; overflow-y: auto;
  overscroll-behavior: contain; background: var(--bg2); border: 1px solid var(--border);
  border-radius: 14px; box-shadow: 0 12px 40px var(--shadow); overflow-wrap: break-word; }
.map-panel { right: 12px; width: min(440px, 44vw); padding: 14px 18px 24px; }
.map-list { left: 12px; width: min(340px, 36vw); padding: 12px 14px 20px; }
.map-overlay.panel-open .map-pathbar { left: calc((100% - min(440px, 44vw) - 24px) / 2); }
/* details panel */
.mp-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
/* on-prem / cloud selector + switchable content blocks */
.env-switch { display: inline-flex; flex: none; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.env-switch button { background: none; border: 0; color: var(--fg-dim); font: inherit; font-size: 12.5px; line-height: 1.2; padding: 6px 9px; cursor: pointer; white-space: nowrap; }
.env-switch button + button { border-left: 1px solid var(--border); }
.env-switch button:hover { color: var(--fg); background: var(--bg3); }
.env-switch button[aria-pressed="true"] { background: var(--bg3); color: var(--accent); font-weight: 700; }
.env { border-left: 3px solid var(--border); padding: 2px 0 2px 14px; margin: 16px 0; }
.env::before { display: inline-block; font-size: 11.5px; font-weight: 700; letter-spacing: .04em; color: var(--accent); background: var(--bg3); border-radius: 999px; padding: 2px 10px; margin-bottom: 4px; }
.env[data-env="onprem"]::before { content: "🏢 On-premise"; }
.env[data-env="cloud"]::before { content: "☁️ Cloud (AWS)"; }
html[data-env="onprem"] .env[data-env="cloud"], html[data-env="cloud"] .env[data-env="onprem"] { display: none; }
.subnav li.env-off { display: none; }
.mp-chips, .mp-chipset, .mp-actions { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--border);
  background: var(--bg3); color: var(--fg); border-radius: 999px; padding: 2px 10px; font-size: 12.5px; }
.chip-level { color: var(--accent); font-weight: 600; }
.chip-node { font: inherit; font-size: 13px; padding: 4px 11px; cursor: pointer; text-align: left; }
.chip-node:hover { border-color: var(--c, var(--accent)); background: var(--bg); }
.chip-node.is-done { border-color: var(--accent2); }
.mp-close { flex: none; width: 32px; height: 32px; border: 1px solid var(--border); border-radius: 8px;
  background: none; color: var(--fg); cursor: pointer; font-size: 14px; }
.mp-close:hover { background: var(--bg3); }
.mp-title { font-size: 21px; line-height: 1.3; margin: 10px 0 4px; }
.mp-summary { margin: 4px 0 10px; }
.mp-done.is-done { background: var(--accent2); color: var(--on-accent); border-color: transparent; font-weight: 600; }
.mp-pathinfo { margin: 8px 0 0; font-size: 13px; color: var(--accent); font-weight: 600; }
.mp-h { margin: 18px 0 6px; font-size: 11.5px; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: var(--fg-dim); }
.map-panel p, .map-panel li { font-size: 14px; }
.map-panel ul, .map-panel ol { margin: 4px 0; padding-left: 20px; }
.map-panel li { margin: 3px 0; }
.mp-ts { list-style: none; padding-left: 0 !important; }
.mp-ts li { padding: 6px 0; border-bottom: 1px dashed var(--border); }
.mp-ts li:last-child { border-bottom: 0; }
.ts-arrow { color: var(--accent); margin: 0 6px; }
.mp-ts code { word-break: break-word; }
.mp-cmd { display: flex; align-items: center; gap: 8px; margin: 5px 0; padding: 4px 5px 4px 10px;
  background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; }
.mp-cmd code { flex: 1; min-width: 0; overflow-x: auto; white-space: pre; font-size: 12.8px;
  background: none !important; border: 0 !important; padding: 2px 0 !important; overflow-wrap: normal; }
.mp-copy { flex: none; font-size: 11px; padding: 2px 8px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--bg2); color: var(--fg-dim); cursor: pointer; }
.mp-copy:hover { color: var(--fg); }
.mp-about { margin: 10px 0 0; }
.mp-about > summary { cursor: pointer; margin: 0; }
.mp-about[open] > summary { margin-bottom: 6px; }
.mp-exit { margin: 0; padding: 8px 12px; background: var(--bg3); border-left: 3px solid var(--accent2);
  border-radius: 0 8px 8px 0; }
.mp-study { list-style: none; padding-left: 0 !important; counter-reset: st; }
.mp-study li { display: flex; align-items: flex-start; gap: 9px; margin: 0; padding: 7px 0;
  border-bottom: 1px solid var(--border); }
.mp-study li:last-child { border-bottom: 0; }
ol.mp-study li::before { counter-increment: st; content: counter(st); flex: none; width: 20px; height: 20px;
  margin-top: 1px; border-radius: 50%; background: var(--bg3); color: var(--fg-dim); font-size: 11.5px;
  font-weight: 700; text-align: center; line-height: 20px; }
.si-icon { flex: none; width: 1.3em; text-align: center; }
.si-body { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; min-width: 0; }
.si-note { flex-basis: 100%; color: var(--fg-dim); font-size: 12.5px; }
.mp-jump { background: none; border: 0; padding: 0; font: inherit; font-size: 14px; color: var(--accent);
  cursor: pointer; text-align: left; }
.mp-jump:hover { text-decoration: underline; }
.mp-pending { color: var(--fg-dim); }
.badge { font-size: 10.5px; font-weight: 600; letter-spacing: .05em; text-transform: uppercase; white-space: nowrap;
  color: var(--fg-dim); border: 1px solid var(--border); border-radius: 999px; padding: 0 7px; }
.badge-online { color: var(--accent); border-color: var(--accent); }
.badge-local { color: var(--accent2); border-color: var(--accent2); }
.mp-empty { margin: 0; color: var(--fg-dim); font-style: italic; }
.mp-key { margin: 6px 0 0; color: var(--fg-dim); font-size: 12.5px; }
/* job search, unlocked per milestone */
.mp-job { padding: 6px 12px 10px; background: var(--bg3); border-left: 3px solid var(--border); border-radius: 0 8px 8px 0; }
.mp-job.is-open { border-left-color: var(--tone); background: color-mix(in srgb, var(--tone) 9%, var(--bg2)); }
.mp-job p { margin: 6px 0; }
.map-panel .jb-warn { list-style: none; padding-left: 0; }
.jb-pop { display: inline-block; animation: jbpop .5s ease-out; }
@keyframes jbpop { 0% { transform: scale(.6); opacity: 0; } 70% { transform: scale(1.12); } 100% { transform: none; opacity: 1; } }
@media (prefers-reduced-motion: reduce) { .jb-pop { animation: none; } }
/* list view */
.ml-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ml-head h2 { margin: 0; font-size: 17px; }
.ml-hint { margin: 4px 0 6px; color: var(--fg-dim); font-size: 13px; }
.ml-level h3 { margin: 16px 0 4px; font-size: 14px; color: var(--accent2); }
.ml-count { color: var(--fg-dim); font-weight: 400; font-size: 12.5px; }
.ml-goal, .ml-exit { margin: 2px 0 6px; color: var(--fg-dim); font-size: 12.5px; }
.ml-level ul { list-style: none; margin: 0; padding: 0; }
.ml-node { display: flex; align-items: center; gap: 8px; width: 100%; padding: 6px 8px; border: 0;
  border-radius: 8px; background: none; color: var(--fg); font: inherit; font-size: 14px;
  text-align: left; cursor: pointer; }
.ml-node:hover, .ml-node.is-sel { background: var(--bg3); }
.ml-node.is-sel { box-shadow: inset 3px 0 0 var(--accent); }
.ml-title { flex: 1; min-width: 0; }
.ml-meta { color: var(--fg-dim); font-size: 12px; white-space: nowrap; }
__UI_CSS__
</style>
<script>
/* apply the saved theme before first paint (storage may be unavailable) */
(function () { try { var t = window.localStorage.getItem("theme"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); } catch (e) { /* no storage */ } })();
(function () { try { var v = window.localStorage.getItem("handbook-env"); if (v === "onprem" || v === "cloud") document.documentElement.setAttribute("data-env", v); } catch (e) { /* no storage */ } })();
</script>
__BODY_OPEN__
<a class="skip-link" href="#main">Skip to content</a>
<header id="topbar">
  <button id="hamburger" class="tb-btn" type="button" title="Table of contents" aria-label="Table of contents" aria-controls="sidebar" aria-expanded="false">☰</button>
  <div class="brand"><span aria-hidden="true">🧰</span><span class="brand-text">DevOps Troubleshooting<small>__BRAND_SMALL__</small></span></div>
  <div id="search" role="search">
    <input id="q" type="search" placeholder="Search commands & topics… (/)" autocomplete="off" spellcheck="false" aria-label="Search the handbook" aria-controls="results">
    <div id="results" role="listbox" aria-label="Search results"></div>
  </div>
  <button id="map-btn" class="tb-btn" type="button" title="Open the 3D course map"__MAPBTN_HIDDEN__><span aria-hidden="true">🗺️</span><span class="lbl"> 3D Map</span></button>
  <div class="env-switch" data-env-switch role="group" aria-label="On-premise or cloud"></div>
  <button id="theme-btn" class="tb-btn" type="button" title="Toggle light / dark theme" aria-label="Toggle light / dark theme">🌓</button>
</header>
<div id="readbar" aria-hidden="true"></div>
<div id="scrim" hidden></div>
<nav id="sidebar" aria-label="Table of contents"><ul id="navlist">__NAV__</ul></nav>

<main id="main" class="cv" tabindex="-1">__CONTENT__</main>
<button id="totop" type="button" title="Back to top" aria-label="Back to top">↑</button>
__BACKNAV_HTML__
__MAP_OVERLAY__
__ROADMAP_DATA__
<script>
__EXTERNAL_LINKS_JS__
(function () {
  "use strict";
  const $ = s => document.querySelector(s);
  const $$ = s => Array.prototype.slice.call(document.querySelectorAll(s));
  const root = document.documentElement;
  if (!root.getAttribute("lang")) root.setAttribute("lang", "en");
  const raf = window.requestAnimationFrame ? cb => window.requestAnimationFrame(cb) : cb => setTimeout(cb, 16);
  const idle = window.requestIdleCallback ? cb => window.requestIdleCallback(cb, { timeout: 80 }) : cb => setTimeout(cb, 1);
  const mq = q => (window.matchMedia ? window.matchMedia(q) : null);
  const onMQ = (m, fn) => { if (!m) return; if (m.addEventListener) m.addEventListener("change", fn); else if (m.addListener) m.addListener(fn); };

  /* ---------- storage: may be unavailable (private mode, sandboxed frames) ---------- */
  const store = {
    get(k) { try { return window.localStorage.getItem(k); } catch (_) { return null; } },
    set(k, v) { try { window.localStorage.setItem(k, v); } catch (_) { /* storage unavailable: keep it for this visit */ } },
  };
  window.__handbookStore = store;

  /* ---------- theme: tokens on :root; the toggle only sets data-theme on the root element ---------- */
  const darkMQ = mq("(prefers-color-scheme: dark)");
  const savedTheme = store.get("theme");
  if (savedTheme === "light" || savedTheme === "dark") root.setAttribute("data-theme", savedTheme);
  function effectiveTheme() {
    const t = root.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : (darkMQ && darkMQ.matches ? "dark" : "light");
  }
  function toggleTheme() {
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    store.set("theme", next);
  }
  window.__handbookToggleTheme = toggleTheme;
  $("#theme-btn").addEventListener("click", toggleTheme);

  /* ---------- copy: clipboard API, else select the text so the reader can copy it ---------- */
  function selectContents(el) {
    try {
      const r = document.createRange(); r.selectNodeContents(el);
      const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      return true;
    } catch (_) { return false; }
  }
  function copyText(text, el, btn) {
    const label = btn ? (btn.dataset.label || (btn.dataset.label = btn.textContent)) : "";
    const report = ok => {
      if (!btn) return;
      btn.textContent = ok ? "copied!" : "selected – copy it";
      clearTimeout(btn._copyT);
      btn._copyT = setTimeout(() => { btn.textContent = label; }, ok ? 1200 : 2600);
    };
    const fallback = () => {
      let ok = false;
      if (el && selectContents(el)) { try { ok = document.execCommand("copy"); } catch (_) { ok = false; } }
      report(ok);
    };
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === "function")
        navigator.clipboard.writeText(String(text)).then(() => report(true), fallback);
      else fallback();
    } catch (_) { fallback(); }
  }
  window.__handbookCopy = copyText;

  /* ---------- jumping: instant scroll, then re-align once lazily rendered sections settle ---------- */
  function jumpTo(el, block) {
    if (!el) return;
    if (window.__sourcesReveal) window.__sourcesReveal(el);
    for (let parent = el; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS") parent.open = true;
    }
    const opt = { block: block || "start" };
    el.scrollIntoView(opt);
    settleOn(el, opt);
  }
  /* Modules use content-visibility:auto with an estimated height. After a jump, the modules
     around the target render at their real height some frames later and push the target away;
     keep re-aligning until it has held still for 350 ms (max 2.5 s). Any wheel, touch, key or
     pointer input from the reader cancels the correction at once. */
  let settleToken = 0;
  function settleOn(el, opt) {
    const token = ++settleToken, now = () => (window.performance ? performance.now() : Date.now());
    const t0 = now();
    let last = el.getBoundingClientRect().top, stillSince = t0;
    const step = () => {
      if (token !== settleToken || !el.isConnected) return;
      const t = now(), top = el.getBoundingClientRect().top;
      if (Math.abs(top - last) >= 0.5) { el.scrollIntoView(opt); stillSince = t; }
      last = el.getBoundingClientRect().top;
      if (t - stillSince < 350 && t - t0 < 2500) raf(step);
    };
    raf(step);
  }
  ["wheel", "touchstart", "keydown", "pointerdown"].forEach(t =>
    addEventListener(t, () => { settleToken++; }, { capture: true, passive: true }));
  /* native in-page links (<a href="#m30">, cards, cross-references) get the same correction */
  addEventListener("hashchange", () => {
    let id = "";
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id || /^map(?:[./]|$)/.test(id) || (history.state && history.state.bnY != null)) return;   // Back onto a saved spot: backnav (or the browser) restores it
    const el = document.getElementById(id);
    if (el && main.contains(el)) settleOn(el, { block: "start" });
  });
  addEventListener("load", () => {
    let id = "";
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const el = id && !/^map(?:[./]|$)/.test(id) ? document.getElementById(id) : null;
    if (el && main.contains(el)) settleOn(el, { block: "start" });
  });
  window.__handbookJump = jumpTo;
  jumpTo.stop = () => { settleToken++; };
  document.addEventListener("click", e => {   /* strip drill/lab: open in place, Back returns here */
    const a = e.target.closest && e.target.closest(".prove-strip a[href^='#drill.'],.prove-strip a[href^='#lab.']"), h = a && a.hash, l = h && h[1] === "l",
      f = h && (l ? (window.__labs || {}).openRoom : (window.__drills || {}).open);
    if (f && !(e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey)) { e.preventDefault(); f(h.slice(l ? 5 : 7)); }
  });
  function flash(el) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }

  /* ---------- old bookmarks (#mod0 … #mod20) -> stable ids ---------- */
  const LEGACY = __LEGACY_JSON__;
  const lm = /^#mod(\d+)$/.exec(location.hash);
  if (lm && LEGACY[lm[1]]) {
    try { history.replaceState(null, "", "#" + LEGACY[lm[1]]); } catch (_) { /* ignore */ }
    raf(() => jumpTo(document.getElementById(LEGACY[lm[1]])));
  }

  /* ---------- sidebar: fixed column on desktop, off-canvas drawer on phones ---------- */
  const topbar = $("#topbar"), sidebar = $("#sidebar"), burger = $("#hamburger"), scrim = $("#scrim");
  const main = $("#main"), navlist = $("#navlist");
  const drawerMQ = mq("(max-width: 900px)");
  const isDrawer = () => !!(drawerMQ && drawerMQ.matches);
  const sidebarVisible = () => !isDrawer() || sidebar.classList.contains("open");
  function setDrawer(open) {
    open = !!open && isDrawer();
    sidebar.classList.toggle("open", open);
    scrim.hidden = !open;
    burger.setAttribute("aria-expanded", String(open));
    if (open) revealInSidebar(curLink || (curModLi && curModLi.querySelector(".mod-btn")), true);
  }
  window.__handbookCloseDrawer = () => setDrawer(false);
  burger.addEventListener("click", () => setDrawer(!sidebar.classList.contains("open")));
  scrim.addEventListener("click", () => setDrawer(false));
  onMQ(drawerMQ, () => { if (!isDrawer()) setDrawer(false); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && sidebar.classList.contains("open")) { setDrawer(false); burger.focus(); }
  });
  /* a module the reader collapsed stays collapsed: scrolling never re-opens it */
  const userCollapsed = new Set();
  function setExpanded(li, on) {
    if (!li) return;
    li.classList.toggle("expanded", !!on);
    const b = li.querySelector(":scope > .mod-btn");
    if (b && b.hasAttribute("aria-expanded")) b.setAttribute("aria-expanded", String(!!on));
  }
  navlist.addEventListener("click", e => {
    const btn = e.target.closest(".mod-btn");
    if (btn) {
      const li = btn.parentElement;
      const hasSub = !!li.querySelector(":scope > .subnav");
      const open = li.classList.contains("expanded");
      if (hasSub && (open || e.target.closest(".chev"))) {
        /* collapse an open module, or toggle from the arrow without leaving the page position */
        setExpanded(li, !open);
        if (open) userCollapsed.add(li); else userCollapsed.delete(li);
        return;
      }
      $$("#navlist .module.expanded").forEach(m => { if (m !== li) setExpanded(m, false); });
      userCollapsed.delete(li);
      setExpanded(li, true);
      jumpTo(document.getElementById(btn.dataset.target.slice(1)));
      setDrawer(false);
      return;
    }
    if (e.target.closest("a")) setDrawer(false);   // native #anchor navigation does the scrolling
  });
  function revealInSidebar(el, instant) {
    if (el && !el.offsetParent) el = curModLi && curModLi.querySelector(".mod-btn");   // hidden in a collapsed module
    if (!el || !sidebarVisible()) return;
    const st = sidebar.scrollTop, h = sidebar.clientHeight, r = el.offsetTop;
    if (r < st + 60 || r > st + h - 80) {
      const top = Math.max(0, r - h / 2);
      if (instant || !sidebar.scrollTo) sidebar.scrollTop = top; else sidebar.scrollTo({ top, behavior: "smooth" });
    }
  }

  /* ---------- scrollspy: cached offsets + binary search; DOM touched only on change ---------- */
  const sections = $$("#main > .mod-section");
  const modLi = new Map(), linkById = new Map();
  $$("#navlist .module").forEach(li => modLi.set(li.dataset.mod, li));
  $$("#navlist .subnav a").forEach(a => linkById.set(a.getAttribute("href").slice(1), a));
  let secTops = [], headCache = new Map(), readOffset = 90, dirty = true, spyQueued = false;
  let curSec = -1, curModLi = null, curLink = null, totopOn = false;
  const totop = $("#totop");
  function measure() {
    const sy = window.scrollY;
    readOffset = topbar.getBoundingClientRect().bottom + 24;
    secTops = sections.map(s => s.getBoundingClientRect().top + sy);
    headCache.clear();
    dirty = false;
  }
  function headsOf(i) {
    let c = headCache.get(i);
    if (!c) {
      const sy = window.scrollY;
      const els = Array.prototype.filter.call(sections[i].querySelectorAll("h2[id], h3[id]"), h => linkById.has(h.id) && !envHidden(h) && !h.closest('[hidden]'));
      c = { els, tops: els.map(h => h.getBoundingClientRect().top + sy) };
      headCache.set(i, c);
    }
    return c;
  }
  function lastAtOrBefore(a, y) {
    let lo = 0, hi = a.length - 1, ans = -1;
    while (lo <= hi) { const mid = (lo + hi) >> 1; if (a[mid] <= y) { ans = mid; lo = mid + 1; } else hi = mid - 1; }
    return ans;
  }
  function spy() {
    spyQueued = false;
    const sy = window.scrollY;
    const on = sy > 600;
    if (on !== totopOn) { totopOn = on; totop.classList.toggle("show", on); }
    if (!sections.length) return;
    if (dirty) measure();
    const y = sy + readOffset;
    const si = Math.max(0, lastAtOrBefore(secTops, y));
    const hc = headsOf(si);
    const hi = lastAtOrBefore(hc.tops, y);
    const link = hi >= 0 ? linkById.get(hc.els[hi].id) || null : null;
    let changed = false;
    if (si !== curSec) {
      curSec = si;
      const li = modLi.get(sections[si].id) || null;
      if (li !== curModLi) {
        if (curModLi) { curModLi.classList.remove("active"); setExpanded(curModLi, false); }
        if (li) { li.classList.add("active"); if (!userCollapsed.has(li)) setExpanded(li, true); }
        curModLi = li; changed = true;
      }
    }
    if (link !== curLink) {
      if (curLink) curLink.classList.remove("current");
      if (link) link.classList.add("current");
      curLink = link; changed = true;
    }
    if (changed) revealInSidebar(curLink || (curModLi && curModLi.querySelector(".mod-btn")));
  }
  function queueSpy() { if (!spyQueued) { spyQueued = true; raf(spy); } }
  function invalidate() { dirty = true; queueSpy(); }
  document.addEventListener("handbook-layout", invalidate);

  /* ---------- on-prem / cloud selector ----------
     "Both" shows everything; "On-prem" / "Cloud" hide the other environment's
     <div class="env" data-env="…"> blocks, their sidebar entries, and (via the
     handbook-env event) the other environment's topics in the 3D map. */
  function curEnv() { const v = document.documentElement.getAttribute("data-env"); return v === "onprem" || v === "cloud" ? v : "both"; }
  function envHidden(el) {
    const blk = el && el.closest ? el.closest(".env") : null, e = curEnv();
    return !!blk && e !== "both" && blk.getAttribute("data-env") !== e;
  }
  function syncEnvUi() {
    const e = curEnv();
    document.querySelectorAll("[data-env-switch] button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.env === e)));
    document.querySelectorAll(".subnav a[href^='#']").forEach(a => {
      const t = document.getElementById(a.getAttribute("href").slice(1)), li = a.closest("li");
      if (li && t) li.classList.toggle("env-off", envHidden(t));
    });
  }
  function setEnv(v) {
    if (v !== "onprem" && v !== "cloud") v = "both";
    if (v === "both") document.documentElement.removeAttribute("data-env"); else document.documentElement.setAttribute("data-env", v);
    try { localStorage.setItem("handbook-env", v); } catch (_) { /* no storage: the choice lasts for this visit */ }
    syncEnvUi(); invalidate();
    document.dispatchEvent(new CustomEvent("handbook-env", { detail: v }));
  }
  window.__setHandbookEnv = setEnv;
  document.querySelectorAll("[data-env-switch]").forEach(box => {
    [["both", "Both", "Show on-premise and cloud content"],
     ["onprem", "🏢 On-prem", "On-premise path: hide cloud-only content and map topics"],
     ["cloud", "☁️ Cloud", "Cloud path: hide on-premise-only content and map topics"]].forEach(([v, label, tip]) => {
      const b = document.createElement("button");
      b.type = "button"; b.dataset.env = v; b.textContent = label; b.title = tip;
      b.addEventListener("click", () => setEnv(v));
      box.appendChild(b);
    });
  });
  syncEnvUi();
  addEventListener("scroll", queueSpy, { passive: true });
  addEventListener("resize", invalidate, { passive: true });
  addEventListener("load", invalidate);
  if (typeof ResizeObserver === "function") {
    const ro = new ResizeObserver(invalidate);
    sections.forEach(s => ro.observe(s));
    ro.observe(topbar);
  }
  queueSpy();
  totop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  /* ---------- copy buttons: added as code blocks come near the viewport ---------- */
  function addCopyBtn(pre) {
    if (pre.querySelector(":scope > .copy-btn")) return;
    const b = document.createElement("button");
    b.type = "button"; b.className = "copy-btn"; b.textContent = "copy";
    b.setAttribute("aria-label", "Copy this code block");
    pre.appendChild(b);
  }
  const pres = main.querySelectorAll("pre");
  if (typeof IntersectionObserver === "function") {
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (en.isIntersecting) { addCopyBtn(en.target); io.unobserve(en.target); }
    }), { rootMargin: "800px 0px" });
    pres.forEach(p => io.observe(p));
  } else pres.forEach(addCopyBtn);
  main.addEventListener("click", e => {
    const b = e.target.closest(".copy-btn");
    if (!b) return;
    const pre = b.parentElement, code = pre.querySelector("code") || pre;
    copyText(code.textContent, code, b);
  });

  /* ---------- full-text search: index built lazily, in idle chunks, on first use ---------- */
  const input = $("#q"), box = $("#results");
  let docs = null, building = false, progress = 0, selIdx = -1, qTimer = 0;
  const BLOCKS = { P: 1, UL: 1, OL: 1, PRE: 1, TABLE: 1, BLOCKQUOTE: 1, DIV: 1 };
  function textOf(el) {
    let t;
    if (el.tagName === "PRE") t = (el.querySelector("code") || el).textContent;
    else if (el.tagName === "LI") {            // own text only: nested lists / paragraphs are indexed separately
      t = "";
      for (let c = el.firstChild; c; c = c.nextSibling) if (!(c.nodeType === 1 && BLOCKS[c.tagName])) t += c.textContent;
    } else t = el.textContent;
    return t.replace(/\s+/g, " ").trim();
  }
  function buildIndex() {
    if (docs || building) return;
    building = true;
    const skip = new Set(main.querySelectorAll(".no-index, .no-index *"));
    const list = main.querySelectorAll("section.mod-section, h2, h3, summary, p, li, pre, td, th");
    const out = [], N = list.length;
    let i = 0, mod = "", ctx = "";
    function step() {
      const t0 = Date.now();
      while (i < N && Date.now() - t0 < 12) {
        const el = list[i++];
        if (skip.has(el)) continue;
        if (el.tagName === "SECTION") { mod = el.getAttribute("data-title") || ""; ctx = ""; continue; }
        const text = textOf(el);
        if (!text) continue;
        const isHead = el.tagName === "H2" || el.tagName === "H3" || el.tagName === "SUMMARY";
        if (isHead) ctx = text;
        out.push({ mod, ctx: isHead ? "" : ctx, lc: text.toLowerCase(), el, isHead });
      }
      progress = N ? i / N : 1;
      if (i < N) {
        if (input.value.trim().length >= 2) showStatus(`Indexing the handbook… ${Math.round(progress * 100)}%`);
        idle(step);
      } else { docs = out; building = false; if (input.value.trim().length >= 2) search(); }
    }
    idle(step);
  }
  function esc(s) { return s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function hl(text, q) {
    const i = text.toLowerCase().indexOf(q);
    if (i < 0) return esc(text.slice(0, 120));
    const start = Math.max(0, i - 40);
    const seg = text.slice(start, start + 130);
    const j = seg.toLowerCase().indexOf(q);
    return (start ? "…" : "") + esc(seg.slice(0, j)) + "<mark>" +
      esc(seg.slice(j, j + q.length)) + "</mark>" + esc(seg.slice(j + q.length));
  }
  function showStatus(msg) {
    box.innerHTML = `<div class="result"><span class="nores">${esc(msg)}</span></div>`;
    box.classList.add("show");
  }
  function hideResults() { box.classList.remove("show"); selIdx = -1; }
  let hits = [];
  function search() {
    const q = input.value.trim().toLowerCase().replace(/\s+/g, " ");
    selIdx = -1;
    if (q.length < 2) { hideResults(); box.innerHTML = ""; return; }
    if (!docs) { buildIndex(); showStatus(`Indexing the handbook… ${Math.round(progress * 100)}%`); return; }
    const heads = [], rest = [];
    for (const d of docs) {
      if (d.lc.indexOf(q) < 0) continue;
      (d.isHead ? heads : rest).push(d);
      if (heads.length >= 40 || heads.length + rest.length > 400) break;
    }
    hits = heads.concat(rest).slice(0, 40);
    box.innerHTML = hits.length
      ? hits.map((d, i) => `<a class="result" role="option" data-i="${i}">
           <div class="path">${esc(d.mod)}${d.ctx ? " › " + esc(d.ctx) : ""}</div>
           <div class="snippet">${hl(textOf(d.el), q)}</div></a>`).join("")
      : '<div class="result"><span class="nores">No matches</span></div>';
    box.classList.add("show");
  }
  function go(d) {
    const B = window.__backnav, from = B && B.here();   // where the reader was, before the env switch moves it
    if (envHidden(d.el)) setEnv("both");
    hideResults();
    if (isDrawer()) input.blur();
    if (B) { B.jump(d.el, d.el.id ? "#" + d.el.id : "", from, 1); return; }   // pushes an entry: Back returns here
    jumpTo(d.el, "center");
    flash(d.el);
  }
  box.addEventListener("click", e => {
    const a = e.target.closest("a.result");
    if (a && hits[+a.dataset.i]) go(hits[+a.dataset.i]);
  });
  input.addEventListener("focus", buildIndex);
  input.addEventListener("input", () => { buildIndex(); clearTimeout(qTimer); qTimer = setTimeout(search, 110); });
  input.addEventListener("keydown", e => {
    if (e.key === "Escape") { hideResults(); input.blur(); return; }
    const items = box.querySelectorAll("a.result");
    if (e.key === "Enter") {
      e.preventDefault();
      clearTimeout(qTimer);
      if (!items.length) { search(); return; }
      const d = hits[Math.max(selIdx, 0)];
      if (d) go(d);
      return;
    }
    if (!items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); selIdx = (selIdx + 1) % items.length; }
    else if (e.key === "ArrowUp") { e.preventDefault(); selIdx = (selIdx - 1 + items.length) % items.length; }
    else return;
    items.forEach((it, i) => it.classList.toggle("sel", i === selIdx));
    if (items[selIdx]) items[selIdx].scrollIntoView({ block: "nearest" });
  });
  document.addEventListener("keydown", e => {
    if (e.key !== "/" || root.classList.contains("map-open") || e.ctrlKey || e.metaKey || e.altKey) return;
    const a = document.activeElement;
    if (a && (a.tagName === "INPUT" || a.tagName === "TEXTAREA" || a.isContentEditable)) return;
    e.preventDefault(); input.focus();
  });
  document.addEventListener("click", e => { if (!e.target.closest("#search")) hideResults(); });
})();
</script>

<script id="map-core">
/* =====================================================================
   3D course map — pure, DOM-free core (graph, layout, camera, projection,
   hit-testing). Exposed as window.__mapCore; unit-tested with node.
   World: y is up. Levels are floors (y), tracks are angular sectors.
   ===================================================================== */
(function (root) {
  "use strict";
  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  function easeInOutCubic(t) { t = clamp(t, 0, 1); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function angleDiff(a, b) { let d = (b - a) % TAU; if (d > Math.PI) d -= TAU; else if (d < -Math.PI) d += TAU; return d; }
  function lerpAngle(a, b, t) { return a + angleDiff(a, b) * t; }
  const V = (x, y, z) => ({ x, y, z });
  const sub = (a, b) => V(a.x - b.x, a.y - b.y, a.z - b.z);
  const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
  const cross = (a, b) => V(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
  function norm(a) { const l = Math.hypot(a.x, a.y, a.z); return l > 1e-9 ? V(a.x / l, a.y / l, a.z / l) : V(0, 0, 0); }
  const arr = v => (Array.isArray(v) ? v : []);

  /* ---------- graph ---------- */
  function buildGraph(data) {
    data = data && typeof data === "object" ? data : {};
    const levels = [], tracks = [], levelIndex = Object.create(null), trackIndex = Object.create(null);
    arr(data.levels).forEach(l => {
      if (l && l.id != null && !(String(l.id) in levelIndex)) {
        levelIndex[String(l.id)] = levels.length;
        levels.push(Object.assign({ name: String(l.id) }, l, { id: String(l.id) }));
      }
    });
    arr(data.tracks).forEach(t => {
      if (t && t.id != null && !(String(t.id) in trackIndex)) {
        trackIndex[String(t.id)] = tracks.length;
        tracks.push(Object.assign({ name: String(t.id), color: null }, t, { id: String(t.id) }));   // null colour -> theme token
      }
    });
    const nodes = [], byId = Object.create(null);
    arr(data.nodes).forEach(raw => {
      if (!raw || typeof raw.id !== "string" || !raw.id || byId[raw.id]) return;
      const n = Object.assign({}, raw);
      n.title = n.title ? String(n.title) : n.id;
      const lv = n.level != null ? String(n.level) : "?";
      if (!(lv in levelIndex)) { levelIndex[lv] = levels.length; levels.push({ id: lv, name: lv === "?" ? "Unlevelled" : lv }); }
      const tr = n.track != null ? String(n.track) : "other";
      if (!(tr in trackIndex)) { trackIndex[tr] = tracks.length; tracks.push({ id: tr, name: tr === "other" ? "Other" : tr, color: null }); }
      n.level = lv; n.track = tr; n.li = levelIndex[lv]; n.ti = trackIndex[tr]; n.index = nodes.length;
      nodes.push(n); byId[n.id] = n;
    });
    nodes.forEach(n => {
      n.parents = arr(n.prereqs).filter((p, i, a) => typeof p === "string" && byId[p] && p !== n.id && a.indexOf(p) === i);
      n.children = [];
    });
    nodes.forEach(n => n.parents.forEach(p => byId[p].children.push(n.id)));
    const edges = [];
    nodes.forEach(n => n.parents.forEach(p => edges.push({ from: p, to: n.id })));
    const g = { levels, tracks, nodes, byId, edges, levelIndex, trackIndex, path: [], pathPos: Object.create(null) };
    let path = arr(data.path).filter((id, i, a) => typeof id === "string" && byId[id] && a.indexOf(id) === i);
    if (!path.length) path = topoOrder(g);
    g.path = path;
    path.forEach((id, i) => { g.pathPos[id] = i; });
    const rank = id => (id in g.pathPos ? g.pathPos[id] : 1e6 + byId[id].index);
    nodes.forEach(n => { n.children.sort((a, b) => rank(a) - rank(b)); n.parents.sort((a, b) => rank(a) - rank(b)); });
    return g;
  }

  /* Kahn's algorithm; ties broken by level then data order; cycle members appended. */
  function topoOrder(g) {
    const indeg = Object.create(null);
    g.nodes.forEach(n => { indeg[n.id] = n.parents.length; });
    const ready = g.nodes.filter(n => !indeg[n.id]);
    const out = [], seen = new Set();
    while (ready.length) {
      ready.sort((a, b) => a.li - b.li || a.index - b.index);
      const n = ready.shift();
      out.push(n.id); seen.add(n.id);
      n.children.forEach(c => { if (--indeg[c] === 0) ready.push(g.byId[c]); });
    }
    g.nodes.forEach(n => { if (!seen.has(n.id)) out.push(n.id); });
    return out;
  }

  function walk(g, id, key) {
    const seen = new Set(), stack = [id];
    while (stack.length) {
      const cur = g.byId[stack.pop()];
      if (!cur) continue;
      for (const nx of cur[key]) if (nx !== id && !seen.has(nx)) { seen.add(nx); stack.push(nx); }
    }
    return seen;
  }
  const ancestors = (g, id) => walk(g, id, "parents");     // full prerequisite chain
  const descendants = (g, id) => walk(g, id, "children");  // everything that builds on it
  const nextSteps = (g, id) => (g.byId[id] ? g.byId[id].children.slice() : []);

  /* path entries whose prerequisites are not earlier on the path */
  function pathProblems(g, path) {
    const pos = Object.create(null), out = [];
    path.forEach((id, i) => { pos[id] = i; });
    path.forEach((id, i) => {
      const n = g.byId[id];
      if (!n) { out.push({ id, problem: "unknown" }); return; }
      n.parents.forEach(p => { if (!(p in pos) || pos[p] > i) out.push({ id, prereq: p, problem: p in pos ? "order" : "missing" }); });
    });
    return out;
  }

  function levelProgress(g, done) {
    const out = g.levels.map(l => ({ id: l.id, name: l.name, done: 0, total: 0 }));
    g.nodes.forEach(n => { out[n.li].total++; if (done && done.has(n.id)) out[n.li].done++; });
    return out;
  }

  function searchNodes(g, q, limit) {
    q = String(q || "").trim().toLowerCase();
    if (!q) return [];
    const scored = [];
    g.nodes.forEach(n => {
      const t = n.title.toLowerCase();
      let s = -1;
      if (t.startsWith(q)) s = 0;
      else if (t.includes(q)) s = 1;
      else if (n.id.includes(q)) s = 2;
      else {
        const hay = [n.summary, n.why].concat(arr(n.learn), arr(n.commands), arr(n.troubleshoot)).join(" ").toLowerCase();
        if (hay.includes(q)) s = 3;
      }
      if (s >= 0) scored.push({ n, s });
    });
    scored.sort((a, b) => a.s - b.s || a.n.li - b.n.li || a.n.index - b.n.index);
    return scored.slice(0, limit || 8).map(x => x.n.id);
  }

  /* ---------- layouts ---------- */
  function cellsOf(g) {
    const cells = Object.create(null);
    const rank = n => (n.id in g.pathPos ? g.pathPos[n.id] : 1e6 + n.index);
    g.nodes.forEach(n => { const k = n.li + "|" + n.ti; (cells[k] = cells[k] || []).push(n); });
    Object.keys(cells).forEach(k => cells[k].sort((a, b) => rank(a) - rank(b)));
    return cells;
  }
  const floorY = (g, li, gap) => (li - (g.levels.length - 1) / 2) * gap;
  const trackAngle = (g, ti) => ti * TAU / Math.max(1, g.tracks.length);

  /* Tower: floor per level, sector per track; nodes sharing a cell are spread
     over up to 3 radial rows and an angular fan inside the sector. */
  function layoutCylinder(g, o) {
    o = Object.assign({ radius: 10, gap: 4.2, spacing: 2.1 }, o);
    const R = o.radius, sector = TAU / Math.max(1, g.tracks.length), pos = Object.create(null), cells = cellsOf(g);
    Object.keys(cells).forEach(k => {
      const list = cells[k], cnt = list.length;
      const rows = cnt <= 3 ? 1 : cnt <= 8 ? 2 : 3, per = Math.ceil(cnt / rows);
      list.forEach((n, i) => {
        const row = Math.floor(i / per), col = i % per, inRow = Math.min(per, cnt - row * per);
        const r = rows === 1 ? R * 0.74 : R * (0.46 + 0.5 * row / (rows - 1));
        const spread = Math.min(sector * 0.72, (inRow - 1) * o.spacing / r);
        const a = trackAngle(g, n.ti) + (inRow > 1 ? (col / (inRow - 1) - 0.5) * spread : 0);
        pos[n.id] = { x: r * Math.cos(a), y: floorY(g, n.li, o.gap), z: r * Math.sin(a), angle: a, radius: r };
      });
    });
    return pos;
  }

  /* Flat 2D grid in the x/y plane (z = 0): rows = levels (L0 at the bottom), columns = tracks. */
  function layoutFlat(g, o) {
    o = Object.assign({ colW: 7, rowStep: 1.25, pad: 1.5 }, o);
    const T = Math.max(1, g.tracks.length), L = g.levels.length, cells = cellsOf(g);
    const maxCell = new Array(L).fill(1);
    Object.keys(cells).forEach(k => { const li = +k.split("|")[0]; maxCell[li] = Math.max(maxCell[li], cells[k].length); });
    const rowH = maxCell.map(m => m * o.rowStep + o.pad);
    const height = rowH.reduce((s, h) => s + h, 0), width = T * o.colW;
    const rows = [], cols = [];
    let y = -height / 2;
    for (let li = 0; li < L; li++) { rows.push({ bottom: y, top: y + rowH[li] }); y += rowH[li]; }
    for (let t = 0; t < T; t++) { const x0 = -width / 2 + t * o.colW; cols.push({ x0, x1: x0 + o.colW, cx: x0 + o.colW / 2 }); }
    const pos = Object.create(null);
    Object.keys(cells).forEach(k => cells[k].forEach((n, i) => {
      const row = rows[n.li], col = cols[n.ti];
      pos[n.id] = { x: col.x0 + 0.8, y: row.top - o.pad / 2 - o.rowStep * (i + 0.5), z: 0 };
    }));
    return { pos, rows, cols, width, height, colW: o.colW };
  }

  function bezier(a, c, b, t) {
    const u = 1 - t;
    return V(u * u * a.x + 2 * u * t * c.x + t * t * b.x, u * u * a.y + 2 * u * t * c.y + t * t * b.y, u * u * a.z + 2 * u * t * c.z + t * t * b.z);
  }
  /* control point of a prerequisite curve: bulges outward in 3D, sideways/up in 2D */
  function edgeControl(a, b, flat) {
    const m = V((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2);
    if (flat) {
      if (Math.abs(a.x - b.x) < 0.5) return V(m.x - 1.6, m.y, m.z);
      return V(m.x, m.y + Math.min(1.6, Math.abs(a.x - b.x) * 0.06), m.z);
    }
    const r = Math.hypot(m.x, m.z), same = Math.abs(a.y - b.y) < 0.01;
    if (r < 1) return V(m.x, m.y + 2.2, m.z);
    const f = (r + 2) / r;
    return V(m.x * f, m.y + (same ? 1.3 : 0), m.z * f);
  }

  /* ---------- camera & projection ---------- */
  /* c = {yaw, pitch, dist, target:{x,y,z}, fov}; orbit camera looking at target */
  function makeCamera(c) {
    const cp = Math.cos(c.pitch), t = c.target;
    const eye = V(t.x + c.dist * cp * Math.sin(c.yaw), t.y + c.dist * Math.sin(c.pitch), t.z + c.dist * cp * Math.cos(c.yaw));
    const f = norm(sub(t, eye));
    let r = norm(cross(f, V(0, 1, 0)));
    if (!r.x && !r.y && !r.z) r = V(Math.cos(c.yaw), 0, -Math.sin(c.yaw));
    const u = cross(r, f);
    return { eye, f, r, u, fov: c.fov || 0.9, near: 0.3 };
  }
  const focalLength = (cam, vh) => (vh / 2) / Math.tan(cam.fov / 2);
  /* perspective projection -> {x, y, depth, scale} in CSS px, or null behind the camera */
  function project(cam, p, vw, vh, cx, cy) {
    const d = sub(p, cam.eye), z = dot(d, cam.f);
    if (!(z > cam.near)) return null;
    const s = focalLength(cam, vh) / z;
    return { x: (cx == null ? vw / 2 : cx) + dot(d, cam.r) * s, y: (cy == null ? vh / 2 : cy) - dot(d, cam.u) * s, depth: z, scale: s };
  }
  /* camera distance at which a box of half-size (halfW, halfH) around the target fits */
  function fitDistance(halfW, halfH, vw, vh, fov) {
    const tv = Math.tan(fov / 2), th = tv * Math.max(0.2, vw / Math.max(1, vh));
    return Math.max(halfH / tv, halfW / th);
  }
  /* smallest camera distance at which every point projects inside region {x0,x1,y0,y1}
     (projection centred in the region); binary search, exact under perspective */
  function fitPoints(view, pts, region, vw, vh) {
    const cx = (region.x0 + region.x1) / 2, cy = (region.y0 + region.y1) / 2;
    const fits = d => {
      const cam = makeCamera({ yaw: view.yaw, pitch: view.pitch, dist: d, target: view.target, fov: view.fov });
      for (const p of pts) {
        const q = project(cam, p, vw, vh, cx, cy);
        if (!q || q.x < region.x0 || q.x > region.x1 || q.y < region.y0 || q.y > region.y1) return false;
      }
      return true;
    };
    let lo = 1, hi = 800;
    if (!fits(hi)) return hi;
    for (let i = 0; i < 40; i++) { const mid = (lo + hi) / 2; if (fits(mid)) hi = mid; else lo = mid; }
    return hi;
  }
  /* drag in px -> new yaw/pitch ("grab the tower": dragging right turns it right) */
  function orbit(yaw0, pitch0, dx, dy, pmin, pmax) {
    return { yaw: yaw0 - dx * 0.0065, pitch: clamp(pitch0 + dy * 0.005, pmin == null ? -0.35 : pmin, pmax == null ? 1.5 : pmax) };
  }
  /* drag in px -> world-space move of the target so the scene follows the pointer */
  function panDelta(cam, dx, dy, dist, vh) {
    const k = dist / focalLength(cam, vh);
    return V((-cam.r.x * dx + cam.u.x * dy) * k, (-cam.r.y * dx + cam.u.y * dy) * k, (-cam.r.z * dx + cam.u.z * dy) * k);
  }
  /* camera that frames one node: node faces the viewer (3D) or sits left of centre (2D) */
  function focusCamera(p, flat, baseDist) {
    if (flat) return { yaw: 0, pitch: 0, target: V(p.x + 2.2, p.y, 0), dist: baseDist * 0.55 };
    const a = Math.atan2(p.z, p.x);
    return { yaw: Math.PI / 2 - a, pitch: 0.3, target: V(p.x * 0.5, p.y, p.z * 0.5), dist: baseDist * 0.62 };
  }

  /* items: [{id, x, y, r, depth}] in screen px -> id of the front-most node under (x, y) */
  function hitTest(items, x, y, pad) {
    pad = pad == null ? 4 : pad;
    let best = null;
    for (const it of items) {
      const d = Math.hypot(it.x - x, it.y - y);
      if (d > it.r + pad) continue;
      if (!best || it.depth < best.depth - 1e-6 || (Math.abs(it.depth - best.depth) <= 1e-6 && d < best.d)) best = { id: it.id, depth: it.depth, d };
    }
    return best ? best.id : null;
  }

  /* axis-aligned rectangles {x, y, w, h} overlap (with padding) — label collision test */
  function rectsOverlap(a, b, pad) {
    pad = pad || 0;
    return a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;
  }

  /* cut r0 px off the start and r1 px off the end of a screen polyline (edges stop at node rims) */
  function trimPolyline(pts, r0, r1) {
    if (!pts || pts.length < 2) return null;
    const cut = (list, r) => {
      const o = list[0];
      let i = 1;
      while (i < list.length && Math.hypot(list[i].x - o.x, list[i].y - o.y) <= r) i++;
      if (i >= list.length) return null;
      const a = list[i - 1], b = list[i];
      let lo = 0, hi = 1;
      for (let k = 0; k < 18; k++) {
        const mid = (lo + hi) / 2;
        if (Math.hypot(a.x + (b.x - a.x) * mid - o.x, a.y + (b.y - a.y) * mid - o.y) < r) lo = mid; else hi = mid;
      }
      return [{ x: a.x + (b.x - a.x) * hi, y: a.y + (b.y - a.y) * hi }].concat(list.slice(i));
    };
    let s = cut(pts.map(p => ({ x: p.x, y: p.y })), r0);
    if (!s) return null;
    s = cut(s.reverse(), r1);
    if (!s) return null;
    s.reverse();
    return s.length >= 2 ? s : null;
  }

  /* ---------- deep links & labels ---------- */
  /* "#map" -> {id: null}; "#map.NODE" (and the legacy "#map/NODE") -> {id: "NODE"}; anything else -> null.
     Only bare hashes are produced (letters, digits, . _ ~ -), which survive any host frame. */
  function parseHash(hash) {
    const m = /^#?map(?:[./](.*))?$/.exec(String(hash || ""));
    if (!m) return null;
    let id = m[1] || null;
    if (id) { try { id = decodeURIComponent(id); } catch (_) { /* keep raw */ } }
    return { id };
  }
  function mapHash(id) {
    if (!id) return "#map";
    return "#map." + String(id).replace(/[^A-Za-z0-9._~-]/g, c => encodeURIComponent(c));
  }
  /* "L2 · Mid-level · Troubleshooter"; the career stage is optional */
  function levelLabel(lv, withName) {
    if (!lv) return "";
    const parts = [lv.id, lv.stage, withName === false ? "" : lv.name].map(x => (x == null ? "" : String(x).trim()));
    return parts.filter((x, i) => x && parts.indexOf(x) === i).join(" · ");
  }

  root.__mapCore = {
    TAU, clamp, lerp, easeInOutCubic, angleDiff, lerpAngle,
    buildGraph, topoOrder, ancestors, descendants, nextSteps, pathProblems, levelProgress, searchNodes,
    cellsOf, floorY, trackAngle, layoutCylinder, layoutFlat, bezier, edgeControl,
    makeCamera, focalLength, project, fitDistance, fitPoints, orbit, panDelta, focusCamera, hitTest, trimPolyline, rectsOverlap,
    parseHash, mapHash, levelLabel,
  };
})(typeof window !== "undefined" ? window : globalThis);
</script>

<script id="map-ui">
/* =====================================================================
   3D course map — UI: canvas-2D renderer, interaction, details panel,
   guided path, filters, list view, progress. Runs only if roadmap data
   was embedded at build time. Test hooks: window.__map.
   ===================================================================== */
(function () {
  "use strict";
  const core = window.__mapCore;
  const dataEl = document.getElementById("roadmap-data");
  const overlay = document.getElementById("map");
  if (!core || !dataEl || !overlay) return;
  let raw;
  try { raw = JSON.parse(dataEl.textContent); } catch (e) { console.warn("3D map: roadmap-data is not valid JSON", e); return; }
  const G = core.buildGraph(raw);
  /* on-prem / cloud: topics tagged env "onprem" or "cloud" show only for that choice (or Both);
     the guided path is rebuilt from the topics that are shown */
  const envNow = () => { const v = document.documentElement.getAttribute("data-env"); return v === "onprem" || v === "cloud" ? v : "both"; };
  const envOk = n => { const e = envNow(); return e === "both" || !n.env || n.env === "both" || n.env === e; };
  const FULL_PATH = G.path.slice();
  function applyEnvPath() {
    G.path = FULL_PATH.filter(id => envOk(G.byId[id]));
    G.pathPos = Object.create(null);
    G.path.forEach((id, i) => { G.pathPos[id] = i; });
  }
  applyEnvPath();
  document.addEventListener("handbook-env", () => {
    applyEnvPath();
    if (S.selected && G.byId[S.selected] && !envOk(G.byId[S.selected])) deselect();
    if (S.pathMode) endPath();
    if (S.listOpen) renderList();
    if (S.selected) renderPanel(G.byId[S.selected]);
    requestRender();
  });
  if (!G.nodes.length) return;

  const $id = id => document.getElementById(id);
  const stage = $id("map-stage"), canvas = $id("map-canvas"), ctx = canvas.getContext("2d");
  const panel = $id("map-panel"), tip = $id("map-tip"), listEl = $id("map-list"), pathBar = $id("map-pathbar");
  const qIn = $id("map-q"), qRes = $id("map-q-results"), toastEl = $id("map-toast"), live = $id("map-live");
  const mapBtn = $id("map-btn");
  if (mapBtn) mapBtn.hidden = false;

  const { clamp, lerp, TAU } = core;
  // roomy tower: floors far enough apart (and a flat enough default pitch) that
  // their ellipses don't overlap on screen; GROUND = drop from L0 to the track ring
  const R = 12, GAP = 7.2, NODE_R = 0.55, GROUND = 3.2, PITCH0 = 0.32, PMIN = -0.35, PMAX = 1.5, DMIN = 7, DMAX = 200;
  const FOV = 50 * Math.PI / 180;
  const LS_KEY = "ops-handbook.roadmap.done.v1";
  const FONT = (getComputedStyle(document.body).fontFamily || "system-ui, sans-serif");
  const reduceMQ = matchMedia("(prefers-reduced-motion: reduce)");
  let reduced = reduceMQ.matches;

  const pos3 = core.layoutCylinder(G, { radius: R, gap: GAP, spacing: 2.6 });
  const flatL = core.layoutFlat(G, {});
  const posF = flatL.pos;
  const edgeCtl = G.edges.map(e => ({ c3: core.edgeControl(pos3[e.from], pos3[e.to], false),
                                      cF: core.edgeControl(posF[e.from], posF[e.to], true) }));

  /* ---------- colours: theme tokens from CSS (re-read on theme change); track colours from the data ---------- */
  const isHex = c => /^#(?:[0-9a-f]{3}|[0-9a-f]{6})$/i.test(String(c || "").trim());
  function hexRgb(c) {
    c = String(c).trim().slice(1);
    if (c.length === 3) c = c.split("").map(x => x + x).join("");
    return [parseInt(c.slice(0, 2), 16), parseInt(c.slice(2, 4), 16), parseInt(c.slice(4, 6), 16)];
  }
  function mix(c, w, k) {
    if (!isHex(c) || !isHex(w)) return c;
    const a = hexRgb(c), b = hexRgb(w);
    return "rgb(" + a.map((v, i) => Math.round(v + (b[i] - v) * k)).join(",") + ")";
  }
  let COL = null;
  function colors() {
    if (COL) return COL;
    const cs = getComputedStyle(document.documentElement);
    const v = n => (cs.getPropertyValue(n) || "").trim() || "gray";
    COL = { bg: v("--bg"), bg2: v("--bg2"), bg3: v("--bg3"), fg: v("--fg"), dim: v("--fg-dim"), accent: v("--accent"),
            accent2: v("--accent2"), border: v("--border"), nodeHi: v("--node-hi"), checkInk: v("--check-ink") };
    G.tracks.forEach(t => { t.col = isHex(t.color) ? String(t.color).trim() : COL.dim; t.light = mix(t.col, COL.nodeHi, 0.5); });
    return COL;
  }
  colors();
  const themeChanged = () => { COL = null; colors(); requestRender(); };
  new MutationObserver(themeChanged).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  const schemeMQ = matchMedia("(prefers-color-scheme: dark)");
  if (schemeMQ.addEventListener) schemeMQ.addEventListener("change", themeChanged); else if (schemeMQ.addListener) schemeMQ.addListener(themeChanged);
  const LV = (lv, withName) => core.levelLabel(lv, withName);

  /* ---------- state ---------- */
  const S = {
    open: false, viewInit: false, yaw: 0.6, pitch: PITCH0, dist: 40, target: { x: 0, y: 0, z: 0 }, fov: FOV,
    flat: false, morph: 0, selected: null, hover: null, hiddenTracks: new Set(), hiddenLevels: new Set(),
    done: new Set(), pathMode: false, pathIdx: 0, autoRotate: false, tween: null, listOpen: false,
    vw: 1, vh: 1, dpr: 1, hits: [], proj: Object.create(null),
  };
  function loadDone() {
    try { const v = JSON.parse(localStorage.getItem(LS_KEY) || "[]"); return Array.isArray(v) ? v.filter(id => G.byId[id]) : []; }
    catch (_) { return []; }
  }
  function saveDone() { try { localStorage.setItem(LS_KEY, JSON.stringify([...S.done])); } catch (_) { /* no storage: progress lives for this visit only */ } }
  S.done = new Set(loadDone());

  /* ---------- small DOM helper ---------- */
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k === "style") el.style.cssText = v;
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : String(v));
    }
    for (const c of kids.flat(3)) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(String(c)));
    return el;
  }
  const arr = v => (Array.isArray(v) ? v : []);
  const lvOf = n => G.levels[n.li], trOf = n => G.tracks[n.ti];
  const isVisible = n => envOk(n) && !S.hiddenTracks.has(n.track) && !S.hiddenLevels.has(n.level);

  /* ---------- sizing & camera ---------- */
  function resize() {
    const r = stage.getBoundingClientRect();
    S.vw = Math.max(1, r.width); S.vh = Math.max(1, r.height);
    S.dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    canvas.width = Math.round(S.vw * S.dpr); canvas.height = Math.round(S.vh * S.dpr);
    requestRender();
  }
  /* outline of the tower used for fitting: top-floor rim (+ room for labels) and the ground ring */
  function towerFitPoints() {
    const L = G.levels.length, yTop = core.floorY(G, L - 1, GAP), yBot = core.floorY(G, 0, GAP) - GROUND, pts = [];
    for (let i = 0; i < 32; i++) {
      const t = i / 32 * TAU, c = Math.cos(t), s = Math.sin(t);
      pts.push({ x: R * 1.08 * c, y: yTop + 1.4, z: R * 1.08 * s });
      pts.push({ x: R * 1.52 * c, y: yBot, z: R * 1.52 * s });
    }
    return pts;
  }
  /* wide screens: the home fit is limited by height, leaving the sides empty. Stretch the
     projected x around the centre (up to 1.8x) so floors widen and same-floor topics spread
     apart; circles and labels are drawn unstretched. Cached per stage size / free area. */
  let stretchKey = "", stretchVal = 1;
  function stretchFor(vp) {
    const key = `${S.vw}x${S.vh}|${Math.round(vp.cx)}|${Math.round(vp.w)}|${Math.round(vp.h)}`;
    if (key === stretchKey) return stretchVal;
    stretchKey = key;
    const v = homeView(false), cam = core.makeCamera(Object.assign({}, v, { fov: FOV }));
    let xmax = 0;
    for (const p of towerFitPoints()) {
      const q = core.project(cam, p, S.vw, S.vh, vp.cx, vp.cy);
      if (q) xmax = Math.max(xmax, Math.abs(q.x - vp.cx));
    }
    stretchVal = clamp((vp.w / 2 - 12) / Math.max(1, xmax), 1, 1.8);
    return stretchVal;
  }
  /* projection centre: the part of the stage not covered by the panel / list.
     In 3D the floor labels ("L2 · Mid-level · Troubleshooter 0/14") sit left of the
     tower, so the tower is centred in what remains after reserving room for them. */
  const labelRoom = w => clamp(w * 0.24, 110, 250);
  function viewport() {
    let left = 0, right = 0, bottom = 0;
    if (!panel.hidden) right = panel.offsetWidth + 24;
    if (S.listOpen) left = listEl.offsetWidth + 24;
    const w = Math.max(160, S.vw - left - right), hh = Math.max(140, S.vh - bottom);
    const lab = labelRoom(w) * (1 - core.easeInOutCubic(S.morph));
    return { cx: left + lab + (w - lab) / 2, cy: hh / 2, w: w - lab, h: hh };
  }
  function homeView(flat) {
    const vp = viewport();
    if (flat) {
      const d = core.fitDistance(flatL.width / 2 + 3.5, flatL.height / 2 + 2.2, vp.w, vp.h, FOV);
      return { yaw: 0, pitch: 0, dist: clamp(d, DMIN, DMAX), target: { x: -1.6, y: 0.4, z: 0 } };
    }
    // fit the whole tower (top floor + labels above it, ground ring + track labels below)
    // inside the free area, so nothing is cut off at any yaw
    const L = G.levels.length, yTop = core.floorY(G, L - 1, GAP), yBot = core.floorY(G, 0, GAP) - GROUND;
    const pts = towerFitPoints();
    const view = { yaw: 0.6, pitch: PITCH0, target: { x: 0, y: (yTop + yBot) / 2, z: 0 }, fov: FOV };
    const m = 18;
    const region = { x0: vp.cx - vp.w / 2 + 12, x1: vp.cx + vp.w / 2 - 12, y0: vp.cy - vp.h / 2 + m, y1: vp.cy + vp.h / 2 - m };
    const rcx = (region.x0 + region.x1) / 2, rcy = (region.y0 + region.y1) / 2;
    // the near (lower) side of the tower projects larger than the far top, so a
    // symmetric fit leaves empty space above it: re-centre the target vertically
    // on the projected bounds a few times, refitting the distance each time
    let d = core.fitPoints(view, pts, region, S.vw, S.vh);
    for (let k = 0; k < 4; k++) {
      const cam = core.makeCamera(Object.assign({}, view, { dist: d }));
      let y0 = Infinity, y1 = -Infinity;
      for (const p of pts) { const q = core.project(cam, p, S.vw, S.vh, rcx, rcy); if (q) { y0 = Math.min(y0, q.y); y1 = Math.max(y1, q.y); } }
      const off = (y0 + y1) / 2 - rcy;                       // > 0: content sits low on screen
      if (Math.abs(off) < 2) break;
      const px2world = d * Math.tan(FOV / 2) / (S.vh / 2);    // world units per px at the target
      view.target = { x: 0, y: view.target.y - off * px2world / Math.cos(PITCH0), z: 0 };
      d = core.fitPoints(view, pts, region, S.vw, S.vh);
    }
    return Object.assign(view, { dist: clamp(d, DMIN, DMAX) });
  }
  function flyTo(view, ms) {
    const dur = reduced ? 0 : (ms == null ? 900 : ms);
    if (!dur) {
      S.yaw = view.yaw; S.pitch = view.pitch; S.dist = view.dist; S.target = Object.assign({}, view.target);
      S.tween = null; requestRender(); return;
    }
    S.tween = { from: { yaw: S.yaw, pitch: S.pitch, dist: S.dist, target: Object.assign({}, S.target) },
                to: view, t0: performance.now(), dur };
    requestRender();
  }
  function stepTween(now) {
    const tw = S.tween;
    if (!tw) return false;
    const k = core.easeInOutCubic((now - tw.t0) / tw.dur);
    S.yaw = core.lerpAngle(tw.from.yaw, tw.to.yaw, k);
    S.pitch = lerp(tw.from.pitch, tw.to.pitch, k);
    S.dist = lerp(tw.from.dist, tw.to.dist, k);
    S.target = { x: lerp(tw.from.target.x, tw.to.target.x, k), y: lerp(tw.from.target.y, tw.to.target.y, k),
                 z: lerp(tw.from.target.z, tw.to.target.z, k) };
    if (k >= 1) { S.tween = null; return false; }
    return true;
  }
  function focusNode(id) {
    const p = (S.flat ? posF : pos3)[id];
    if (!p) return;
    const v = core.focusCamera(p, S.flat, homeView(S.flat).dist);
    v.dist = clamp(v.dist, DMIN, DMAX);
    flyTo(v);
  }

  /* ---------- render loop (runs only while open and something changes) ---------- */
  let raf = 0, lastT = 0, idleTimer = 0;
  function requestRender() { if (S.open && !raf) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0;
    const dt = lastT ? Math.min(50, now - lastT) : 16;
    let more = stepTween(now);
    const goal = S.flat ? 1 : 0;
    if (S.morph !== goal) {
      const step = reduced ? 1 : dt / 650;
      S.morph = goal > S.morph ? Math.min(goal, S.morph + step) : Math.max(goal, S.morph - step);
      more = true;
    }
    if (S.autoRotate && !S.flat && !S.selected && !drag && !S.tween) { S.yaw += dt * 0.00009; more = true; }
    draw();
    if (more && S.open) { lastT = now; raf = requestAnimationFrame(frame); } else lastT = 0;
  }
  function interact() {
    S.autoRotate = false;
    clearTimeout(idleTimer);
    if (!reduced) idleTimer = setTimeout(() => {
      if (S.open && !S.selected && !S.flat && !S.pathMode && !drag) { S.autoRotate = true; requestRender(); }
    }, 30000);
  }

  /* ---------- drawing ---------- */
  function text(str, x, y, opt) {
    const C = colors();
    ctx.font = opt.font; ctx.textAlign = opt.align || "center"; ctx.textBaseline = opt.base || "alphabetic";
    ctx.globalAlpha = opt.alpha == null ? 1 : opt.alpha;
    ctx.lineJoin = "round"; ctx.lineWidth = opt.halo == null ? 3.5 : opt.halo; ctx.strokeStyle = C.bg;
    if (ctx.lineWidth > 0) ctx.strokeText(str, x, y);
    ctx.fillStyle = opt.color || C.fg; ctx.fillText(str, x, y);
  }
  function fitText(str, maxW) {
    if (ctx.measureText(str).width <= maxW) return str;
    let lo = 0, hi = str.length;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (ctx.measureText(str.slice(0, mid) + "…").width <= maxW) lo = mid; else hi = mid - 1; }
    return lo > 0 ? str.slice(0, lo).trimEnd() + "…" : "…";
  }
  function polyline(pts, close) {
    ctx.beginPath();
    pts.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
    if (close) ctx.closePath();
  }

  function drawTower(P, cam, a, prog, selLi) {
    const C = colors(), T = G.tracks.length, sector = TAU / Math.max(1, T), SEG = 72;
    const floors = G.levels.map((lv, li) => {
      const y = core.floorY(G, li, GAP), p = P({ x: 0, y, z: 0 });
      return { li, y, depth: p ? p.depth : 0 };
    }).sort((p, q) => q.depth - p.depth);
    ctx.save();
    for (const f of floors) {
      const off = S.hiddenLevels.has(G.levels[f.li].id), pts = [];
      for (let i = 0; i < SEG; i++) {
        const t = i / SEG * TAU, p = P({ x: R * 1.06 * Math.cos(t), y: f.y, z: R * 1.06 * Math.sin(t) });
        if (!p) { pts.length = 0; break; }
        pts.push(p);
      }
      if (pts.length) {
        polyline(pts, true);
        ctx.fillStyle = selLi === f.li ? C.accent : C.fg;
        ctx.globalAlpha = a * (off ? 0.01 : selLi === f.li ? 0.07 : 0.035); ctx.fill();
        ctx.strokeStyle = selLi === f.li ? C.accent : C.dim; ctx.lineWidth = selLi === f.li ? 1.6 : 1;
        ctx.globalAlpha = a * (off ? 0.12 : 0.45); ctx.stroke();
      }
      for (let t = 0; t < T; t++) {   // track spokes on every floor
        const ang = t * sector, c = Math.cos(ang), s = Math.sin(ang);
        const p0 = P({ x: R * 0.2 * c, y: f.y, z: R * 0.2 * s }), p1 = P({ x: R * 1.06 * c, y: f.y, z: R * 1.06 * s });
        if (!p0 || !p1) continue;
        ctx.strokeStyle = G.tracks[t].col; ctx.lineWidth = 1.2;
        ctx.globalAlpha = a * 0.3 * (off || S.hiddenTracks.has(G.tracks[t].id) ? 0.25 : 1);
        polyline([p0, p1]); ctx.stroke();
      }
    }
    // central axis
    const yTop = core.floorY(G, G.levels.length - 1, GAP) + 2.6, yBot = core.floorY(G, 0, GAP) - GROUND;
    const ax0 = P({ x: 0, y: yBot, z: 0 }), ax1 = P({ x: 0, y: yTop, z: 0 });
    if (ax0 && ax1) { ctx.strokeStyle = C.dim; ctx.globalAlpha = a * 0.35; ctx.lineWidth = 1; ctx.setLineDash([3, 5]); polyline([ax0, ax1]); ctx.stroke(); ctx.setLineDash([]); }
    // ground ring: coloured track sectors + labels
    for (let t = 0; t < T; t++) {
      const tr = G.tracks[t], off = S.hiddenTracks.has(tr.id);
      const a0 = t * sector - sector / 2 + 0.05, a1 = t * sector + sector / 2 - 0.05, pts = [];
      for (let i = 0; i <= 16; i++) {
        const ang = a0 + (a1 - a0) * i / 16, p = P({ x: R * 1.16 * Math.cos(ang), y: yBot, z: R * 1.16 * Math.sin(ang) });
        if (p) pts.push(p);
      }
      if (pts.length > 1) { ctx.strokeStyle = tr.col; ctx.lineWidth = 4; ctx.lineCap = "round"; ctx.globalAlpha = a * (off ? 0.2 : 0.9); polyline(pts); ctx.stroke(); }
      const lp = P({ x: R * 1.4 * Math.cos(t * sector), y: yBot, z: R * 1.4 * Math.sin(t * sector) });
      if (lp) {
        ctx.font = `600 12.5px ${FONT}`;
        const w = ctx.measureText(tr.name).width;
        // step the track name down if it would collide with a floor label ("L0 · Fresher …")
        let ly = lp.y;
        for (let k = 0; k < 4; k++) {
          const bx = { x0: lp.x - w / 2 - 14, x1: lp.x + w / 2 + 5, y0: ly - 13, y1: ly + 5 };
          if (!floorBoxes.some(b => bx.x0 < b.x1 && bx.x1 > b.x0 && bx.y0 < b.y1 && bx.y1 > b.y0)) break;
          ly += 16;
        }
        reserved.push({ x0: lp.x - w / 2 - 14, x1: lp.x + w / 2 + 5, y0: ly - 13, y1: ly + 5 });
        ctx.globalAlpha = a * (off ? 0.3 : 1);
        ctx.fillStyle = tr.col; ctx.beginPath(); ctx.arc(lp.x - w / 2 - 8, ly - 4, 4, 0, TAU); ctx.fill();
        text(tr.name, lp.x + 2, ly, { font: `600 12.5px ${FONT}`, alpha: a * (off ? 0.35 : 0.95), color: C.fg });
      }
    }
    ctx.restore();
  }
  /* screen boxes of the floor labels, computed before the tower is drawn so the
     track names on the ground ring can keep clear of them */
  let floorBoxes = [];
  function floorLabelBoxes(P, cam, prog) {
    const out = [];
    G.levels.forEach((lv, li) => {
      const p = P({ x: -cam.r.x * R * 1.12, y: core.floorY(G, li, GAP), z: -cam.r.z * R * 1.12 });
      if (!p) return;
      const rest = [lv.stage, lv.name].filter(Boolean).join(" · ");
      const head = lv.id + (rest ? " · " : " "), tail = rest + "  " + prog[li].done + "/" + prog[li].total;
      ctx.font = `600 13px ${FONT}`; const wt = ctx.measureText(tail).width;
      ctx.font = `800 13px ${FONT}`; const wh = ctx.measureText(head).width;
      const x = p.x - 8;
      out.push({ x0: x - wt - wh - 3, x1: x + 3, y0: p.y - 10, y1: p.y + 8 });
    });
    return out;
  }
  function drawFloorLabels(P, cam, a, prog, selLi) {
    const C = colors();
    G.levels.forEach((lv, li) => {
      const y = core.floorY(G, li, GAP);
      const p = P({ x: -cam.r.x * R * 1.12, y, z: -cam.r.z * R * 1.12 });
      if (!p) return;
      const off = S.hiddenLevels.has(lv.id);
      const rest = [lv.stage, lv.name].filter(Boolean).join(" · ");
      const head = lv.id + (rest ? " · " : " "), tail = rest + "  " + prog[li].done + "/" + prog[li].total;
      ctx.font = `600 13px ${FONT}`;
      const wt = ctx.measureText(tail).width;
      const x = p.x - 8;
      ctx.font = `800 13px ${FONT}`;
      reserved.push({ x0: x - wt - ctx.measureText(head).width - 3, x1: x + 3, y0: p.y - 10, y1: p.y + 8 });
      text(tail, x, p.y + 4, { font: `600 13px ${FONT}`, align: "right", alpha: a * (off ? 0.35 : 1), color: selLi === li ? C.accent : C.dim });
      text(head, x - wt, p.y + 4, { font: `800 13px ${FONT}`, align: "right", alpha: a * (off ? 0.35 : 1), color: C.accent });
    });
  }
  function drawGrid(P, a, prog, selLi) {
    const C = colors(), x0 = -flatL.width / 2, x1 = flatL.width / 2;
    const top = flatL.rows.length ? flatL.rows[flatL.rows.length - 1].top : 0, bot = flatL.rows.length ? flatL.rows[0].bottom : 0;
    ctx.save();
    flatL.rows.forEach((row, li) => {
      const q = [P({ x: x0, y: row.bottom, z: 0 }), P({ x: x1, y: row.bottom, z: 0 }), P({ x: x1, y: row.top, z: 0 }), P({ x: x0, y: row.top, z: 0 })];
      if (q.some(p => !p)) return;
      polyline(q, true);
      ctx.fillStyle = selLi === li ? C.accent : C.fg;
      ctx.globalAlpha = a * (selLi === li ? 0.07 : li % 2 ? 0.045 : 0.02); ctx.fill();
      ctx.strokeStyle = C.border; ctx.globalAlpha = a * 0.9; ctx.lineWidth = 1; ctx.stroke();
      const lp = P({ x: x0 - 0.4, y: (row.bottom + row.top) / 2, z: 0 });
      if (lp) {
        const lv = G.levels[li], off = S.hiddenLevels.has(lv.id), al = a * (off ? 0.35 : 1);
        const tail = (lv.name || "") + " " + prog[li].done + "/" + prog[li].total;
        if (lv.stage) {
          text(lv.id, lp.x, lp.y - 11, { font: `800 13px ${FONT}`, align: "right", alpha: al, color: C.accent });
          text(String(lv.stage), lp.x, lp.y + 4, { font: `700 12px ${FONT}`, align: "right", alpha: al, color: C.fg });
          text(tail, lp.x, lp.y + 19, { font: `500 12px ${FONT}`, align: "right", alpha: al, color: C.dim });
        } else {
          text(lv.id, lp.x, lp.y - 3, { font: `800 13px ${FONT}`, align: "right", alpha: al, color: C.accent });
          text(tail, lp.x, lp.y + 13, { font: `500 12px ${FONT}`, align: "right", alpha: al, color: C.dim });
        }
      }
    });
    flatL.cols.forEach((col, t) => {
      const tr = G.tracks[t], off = S.hiddenTracks.has(tr.id);
      if (t > 0) {
        const p0 = P({ x: col.x0, y: bot, z: 0 }), p1 = P({ x: col.x0, y: top, z: 0 });
        if (p0 && p1) { ctx.strokeStyle = C.border; ctx.globalAlpha = a; ctx.lineWidth = 1; polyline([p0, p1]); ctx.stroke(); }
      }
      const hp = P({ x: col.cx, y: top + 0.7, z: 0 });
      if (hp) {
        ctx.font = `700 12.5px ${FONT}`;
        const maxW = Math.max(30, (col.x1 - col.x0) * hp.scale - 20);
        const label = fitText(tr.name, maxW), w = ctx.measureText(label).width;
        ctx.globalAlpha = a * (off ? 0.3 : 1); ctx.fillStyle = tr.col;
        ctx.beginPath(); ctx.arc(hp.x - w / 2 - 8, hp.y - 4, 4, 0, TAU); ctx.fill();
        text(label, hp.x + 2, hp.y, { font: `700 12.5px ${FONT}`, alpha: a * (off ? 0.35 : 1), color: C.fg });
      }
    });
    ctx.restore();
  }
  function drawEdge(i, pos, P, pa, pb, kind, alpha, m) {
    const C = colors(), e = G.edges[i], A = pos[e.from], B = pos[e.to], ec = edgeCtl[i];
    const c = { x: lerp(ec.c3.x, ec.cF.x, m), y: lerp(ec.c3.y, ec.cF.y, m), z: lerp(ec.c3.z, ec.cF.z, m) };
    const pts = [];
    for (let k = 0; k <= 14; k++) { const p = P(core.bezier(A, c, B, k / 14)); if (!p) return; pts.push(p); }
    const rA = clamp(NODE_R * pa.scale, 3.5, 24) + 2, rB = clamp(NODE_R * pb.scale, 3.5, 24) + 3;
    const tr = core.trimPolyline(pts, rA, rB);
    if (!tr) return;
    const st = {
      base: [C.dim, (0.24 + 0.18 * m) * alpha, 1.2], /* faint in 3D, as before in flat 2D */ hover: [C.fg, 0.9, 1.8], chain: [C.accent, 0.95, 2.6],
      next: [C.accent2, 0.95, 2.4], later: [C.accent2, 0.38, 1.3], dim: [C.dim, 0.07, 1],
    }[kind];
    ctx.strokeStyle = st[0]; ctx.globalAlpha = st[1]; ctx.lineWidth = st[2]; ctx.lineCap = "round";
    if (kind === "next" || kind === "later") ctx.setLineDash(kind === "next" ? [7, 5] : [3, 5]);
    polyline(tr); ctx.stroke(); ctx.setLineDash([]);
    if (kind === "dim" || kind === "later") return;
    const q = tr[tr.length - 1], p = tr[tr.length - 2], ang = Math.atan2(q.y - p.y, q.x - p.x), s = 4 + st[2] * 1.6;
    ctx.fillStyle = st[0]; ctx.beginPath(); ctx.moveTo(q.x, q.y);
    ctx.lineTo(q.x - s * Math.cos(ang - 0.45), q.y - s * Math.sin(ang - 0.45));
    ctx.lineTo(q.x - s * Math.cos(ang + 0.45), q.y - s * Math.sin(ang + 0.45));
    ctx.closePath(); ctx.fill();
  }
  function drawNode(n, p, r, state, alpha, m, front, near) {
    const C = colors(), tr = trOf(n), done = S.done.has(n.id), hov = S.hover === n.id;
    const pathCur = S.pathMode && G.path[S.pathIdx] === n.id;
    const al = state === "dim" ? 0.16 : state === "later" ? 0.5 * alpha : alpha;
    if (state === "sel") { ctx.globalAlpha = 0.2; ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(p.x, p.y, r + 9, 0, TAU); ctx.fill(); }
    ctx.globalAlpha = al;
    const g = ctx.createRadialGradient(p.x - r * 0.35, p.y - r * 0.4, r * 0.1, p.x, p.y, r);
    g.addColorStop(0, tr.light); g.addColorStop(1, tr.col);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, TAU); ctx.fill();
    ctx.lineWidth = Math.max(1.2, r * 0.14); ctx.strokeStyle = C.bg; ctx.stroke();
    if (done) {
      ctx.strokeStyle = C.accent2; ctx.lineWidth = 2.2; ctx.beginPath(); ctx.arc(p.x, p.y, r + 3.2, 0, TAU); ctx.stroke();
      if (r >= 6) {
        ctx.strokeStyle = C.checkInk; ctx.lineWidth = Math.max(1.6, r * 0.2); ctx.lineCap = "round"; ctx.lineJoin = "round";
        ctx.beginPath(); ctx.moveTo(p.x - r * 0.4, p.y + 0.02 * r); ctx.lineTo(p.x - r * 0.1, p.y + r * 0.32); ctx.lineTo(p.x + r * 0.42, p.y - r * 0.3); ctx.stroke();
      }
    }
    const ringR = r + (done ? 6.5 : 4);
    if (state === "sel" || hov || pathCur) {
      ctx.globalAlpha = state === "dim" ? 0.5 : 1; ctx.strokeStyle = state === "sel" ? C.accent : pathCur ? C.accent : C.fg; ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.arc(p.x, p.y, ringR, 0, TAU); ctx.stroke();
    } else if (state === "chain" || state === "next") {
      ctx.globalAlpha = 0.9; ctx.strokeStyle = state === "chain" ? C.accent : C.accent2; ctx.lineWidth = 1.6;
      if (state === "next") ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.arc(p.x, p.y, ringR, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
    }
    // label: queued, then placed after all nodes are drawn (placeLabels) so labels never overlap
    const flat = m > 0.5;
    const show = flat || state === "sel" || state === "chain" || state === "next" || hov || pathCur || (!S.selected && front && r >= 7);
    if (!show) return;
    const pri = state === "sel" ? 1000 : hov ? 900 : pathCur ? 800 : state === "chain" ? 500 + near * 100
      : state === "next" ? 400 + near * 100 : flat ? 300 : near * 100 + r;
    if (flat) {
      const fs = 12.5, font = `${state === "sel" ? 700 : 600} ${fs}px ${FONT}`;
      ctx.font = font;
      const label = fitText(n.title, Math.max(40, (flatL.colW - 1.3) * p.scale - r));
      labelQ.push({ str: label, x: p.x + r + 6, y: p.y + 0.5, fs, pri, opt: { font, align: "left", base: "middle", alpha: state === "dim" ? 0.35 : 1 } });
    } else if ((state !== "dim" && state !== "later") || hov) {
      const fs = clamp(r * 0.9 + 5, 11, 15), font = `${state === "sel" ? 700 : 600} ${fs}px ${FONT}`;
      labelQ.push({ str: n.title, x: p.x, y: p.y + r + fs + (done ? 4 : 1), fs, pri, opt: { font, alpha: Math.max(0.55, al) } });
    }
  }
  /* greedy label placement: highest priority first (selected, hovered, guided-path step,
     prerequisite chain, next steps, then nearest/largest); a label whose box would overlap
     an already placed one is skipped, except the always-shown top three kinds */
  let labelQ = [], reserved = [];   // reserved: boxes of track / floor labels drawn by the tower
  function placeLabels() {
    const placed = reserved.slice(), PAD = 3;
    labelQ.sort((a, b) => b.pri - a.pri);
    for (const L of labelQ) {
      ctx.font = L.opt.font;
      const w = ctx.measureText(L.str).width, left = L.opt.align === "left";
      const box = left   // flat-grid labels: rows are already spaced for them, so use the glyph height only
        ? { x0: L.x - 2, x1: L.x + w + 2, y0: L.y - L.fs * 0.45, y1: L.y + L.fs * 0.45 }
        : { x0: L.x - w / 2 - PAD, x1: L.x + w / 2 + PAD, y0: L.y - L.fs * 0.85 - PAD, y1: L.y + L.fs * 0.3 + PAD };
      const clash = placed.some(b => box.x0 < b.x1 && box.x1 > b.x0 && box.y0 < b.y1 && box.y1 > b.y0);
      if (clash && L.pri < 800) continue;
      placed.push(box);
      text(L.str, L.x, L.y, L.opt);
    }
    labelQ = [];
  }

  function draw() {
    const W = S.vw, H = S.vh, C = colors();
    reserved = [];
    ctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
    ctx.globalAlpha = 1;
    const bgG = ctx.createRadialGradient(W / 2, H * 0.45, 0, W / 2, H * 0.45, Math.max(W, H) * 0.75);
    bgG.addColorStop(0, C.bg3); bgG.addColorStop(1, C.bg);
    ctx.fillStyle = bgG; ctx.fillRect(0, 0, W, H);
    const cam = core.makeCamera(S), vp = viewport();
    const xs = lerp(stretchFor(vp), 1, core.easeInOutCubic(S.morph));   // no stretch in flat 2D
    const P = p => {
      const q = core.project(cam, p, W, H, vp.cx, vp.cy);
      if (q && xs !== 1) q.x = vp.cx + (q.x - vp.cx) * xs;
      return q;
    };
    const m = core.easeInOutCubic(S.morph);
    const pos = Object.create(null);
    for (const n of G.nodes) {
      const a = pos3[n.id], b = posF[n.id];
      pos[n.id] = { x: lerp(a.x, b.x, m), y: lerp(a.y, b.y, m), z: lerp(a.z, b.z, m) };
    }
    const prog = core.levelProgress({ levels: G.levels, nodes: G.nodes.filter(envOk) }, S.done);
    const sel = S.selected && G.byId[S.selected] ? S.selected : null;
    const selLi = sel ? G.byId[sel].li : -1;
    floorBoxes = m < 0.999 ? floorLabelBoxes(P, cam, prog) : [];
    if (m < 0.999) drawTower(P, cam, 1 - m, prog, selLi);
    if (m > 0.001) drawGrid(P, m, prog, selLi);

    let chain = null, next = null, later = null;
    if (sel) {
      chain = core.ancestors(G, sel); chain.add(sel);
      next = new Set(G.byId[sel].children);
      later = core.descendants(G, sel);            // everything further downstream, shown faintly
    }
    const proj = Object.create(null);
    let dMin = Infinity, dMax = -Infinity;
    for (const n of G.nodes) {
      if (!isVisible(n)) continue;
      const p = P(pos[n.id]);
      if (!p) continue;
      proj[n.id] = p; dMin = Math.min(dMin, p.depth); dMax = Math.max(dMax, p.depth);
    }
    const span = Math.max(1e-6, dMax - dMin);
    const rel = d => (d - dMin) / span;
    const fade = d => 1 - (1 - m) * 0.55 * rel(d);       // depth cue (none in flat mode)
    const items = [];
    G.edges.forEach((e, i) => {
      const pa = proj[e.from], pb = proj[e.to];
      if (!pa || !pb) return;
      let kind = "base";
      if (sel) kind = chain.has(e.to) ? "chain" : e.from === sel ? "next" : later.has(e.from) && later.has(e.to) ? "later" : "dim";
      else if (S.hover && (e.from === S.hover || e.to === S.hover)) kind = "hover";
      const depth = (pa.depth + pb.depth) / 2;
      items.push({ depth: depth + 0.01, draw: () => drawEdge(i, pos, P, pa, pb, kind, fade(depth), m) });
    });
    const hits = [];
    for (const n of G.nodes) {
      const p = proj[n.id];
      if (!p) continue;
      const r = clamp(NODE_R * p.scale, 3.5, 24);
      const state = !sel ? "normal" : n.id === sel ? "sel" : chain.has(n.id) ? "chain" : next.has(n.id) ? "next" : later.has(n.id) ? "later" : "dim";
      hits.push({ id: n.id, x: p.x, y: p.y, r, depth: p.depth });
      items.push({ depth: p.depth, draw: () => drawNode(n, p, r, state, fade(p.depth), m, rel(p.depth) < 0.55, 1 - rel(p.depth)) });
    }
    items.sort((a, b) => b.depth - a.depth);          // painter's algorithm: far -> near
    labelQ = [];
    ctx.save();
    for (const it of items) it.draw();
    ctx.restore();
    if (m < 0.999) { ctx.save(); drawFloorLabels(P, cam, 1 - m, prog, selLi); ctx.restore(); }
    ctx.save(); placeLabels(); ctx.restore();         // node labels last, on top, without overlaps
    ctx.globalAlpha = 1;
    S.hits = hits; S.proj = proj;
  }

  /* ---------- tooltip ---------- */
  function hideTip() { tip.hidden = true; }
  function showTip(id, x, y) {
    const n = G.byId[id], lv = lvOf(n), tr = trOf(n);
    tip.replaceChildren(h("strong", null, n.title),
      h("span", { class: "tip-meta" }, `${LV(lv)} · ${tr.name}${S.done.has(id) ? " · ✓ done" : ""}`));
    tip.hidden = false;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = x + 14, top = y + 14;
    if (left + tw > S.vw - 8) left = x - tw - 14;
    if (top + th > S.vh - 8) top = y - th - 14;
    tip.style.transform = `translate(${Math.max(4, left)}px, ${Math.max(4, top)}px)`;
  }

  /* ---------- pointer / wheel / keyboard ---------- */
  const pointers = new Map();
  let drag = null, pinch = null;
  const localXY = e => { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
  const startDrag = (p, moved) => ({ sx: p.x, sy: p.y, yaw: S.yaw, pitch: S.pitch, target: Object.assign({}, S.target), moved: moved || 0 });
  canvas.addEventListener("pointerdown", e => {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    try { canvas.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ }
    const p = localXY(e);
    pointers.set(e.pointerId, p);
    interact(); S.tween = null; hideTip();
    if (pointers.size === 1) drag = startDrag(p);
    else if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      pinch = { d0: Math.hypot(a.x - b.x, a.y - b.y) || 1, dist0: S.dist };
      drag = null;
    }
  });
  canvas.addEventListener("pointermove", e => {
    const p = localXY(e);
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, p);
    if (pinch && pointers.size >= 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y) || 1;
      S.dist = clamp(pinch.dist0 * pinch.d0 / d, DMIN, DMAX);
      requestRender(); return;
    }
    if (drag && pointers.has(e.pointerId)) {
      const dx = p.x - drag.sx, dy = p.y - drag.sy;
      drag.moved = Math.max(drag.moved, Math.hypot(dx, dy));
      if (drag.moved < 4) return;
      if (S.flat) {
        const cam = core.makeCamera(Object.assign({}, S, { target: drag.target }));
        const d = core.panDelta(cam, dx, dy, S.dist, S.vh);
        S.target = { x: drag.target.x + d.x, y: drag.target.y + d.y, z: drag.target.z + d.z };
      } else {
        const o = core.orbit(drag.yaw, drag.pitch, dx, dy, PMIN, PMAX);
        S.yaw = o.yaw; S.pitch = o.pitch;
      }
      canvas.classList.add("dragging"); requestRender(); return;
    }
    if (e.pointerType === "mouse" && !pointers.size) {
      interact();   // a mouse over the map pauses the idle spin, so topics hold still to be clicked
      const id = core.hitTest(S.hits, p.x, p.y, 3);
      if (id !== S.hover) { S.hover = id; canvas.style.cursor = id ? "pointer" : ""; requestRender(); }
      if (id) showTip(id, p.x, p.y); else hideTip();
    }
  });
  function endPointer(e, cancelled) {
    if (!pointers.has(e.pointerId)) return;
    pointers.delete(e.pointerId);
    canvas.classList.remove("dragging");
    if (pinch) {
      if (pointers.size < 2) { pinch = null; drag = pointers.size === 1 ? startDrag([...pointers.values()][0], 99) : null; }
      return;
    }
    const d = drag; drag = null;
    if (!d || cancelled || d.moved >= 6) { requestRender(); return; }
    const p = localXY(e);
    const id = core.hitTest(S.hits, p.x, p.y, e.pointerType === "mouse" ? 3 : 10);
    if (id && id === S.selected) deselect();          // clicking the open topic again closes it
    else if (id) select(id); else if (S.selected) deselect();
  }
  canvas.addEventListener("pointerup", e => endPointer(e, false));
  canvas.addEventListener("pointercancel", e => endPointer(e, true));
  canvas.addEventListener("pointerleave", () => { if (!drag && S.hover) { S.hover = null; canvas.style.cursor = ""; requestRender(); } hideTip(); });
  canvas.addEventListener("wheel", e => {
    e.preventDefault(); interact(); S.tween = null;
    const k = e.deltaMode === 1 ? 0.05 : e.deltaMode === 2 ? 0.5 : 0.0015;
    S.dist = clamp(S.dist * Math.exp(clamp(e.deltaY, -300, 300) * k), DMIN, DMAX);
    requestRender();
  }, { passive: false });

  function nudge(dx, dy) {
    interact(); S.tween = null;
    if (S.flat) {
      const cam = core.makeCamera(S), d = core.panDelta(cam, -dx * 60, -dy * 60, S.dist, S.vh);
      S.target = { x: S.target.x + d.x, y: S.target.y + d.y, z: S.target.z + d.z };
    } else {
      const o = core.orbit(S.yaw, S.pitch, -dx * 40, -dy * 40, PMIN, PMAX);
      S.yaw = o.yaw; S.pitch = o.pitch;
    }
    requestRender();
  }
  function zoomBy(f) { interact(); S.tween = null; S.dist = clamp(S.dist * f, DMIN, DMAX); requestRender(); }
  document.addEventListener("keydown", e => {
    if (!S.open) return;
    const t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
    if (e.key === "Escape") {
      e.preventDefault(); e.stopPropagation();
      if (t === qIn && !qRes.hidden) { closeResults(); return; }
      closeMap(); return;
    }
    if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
    let handled = true;
    switch (e.key) {
      case "ArrowLeft": nudge(-1, 0); break;
      case "ArrowRight": nudge(1, 0); break;
      case "ArrowUp": nudge(0, -1); break;
      case "ArrowDown": nudge(0, 1); break;
      case "+": case "=": zoomBy(1 / 1.15); break;
      case "-": case "_": zoomBy(1.15); break;
      case "/": qIn.focus(); break;
      default: handled = false;
    }
    if (handled) { e.preventDefault(); e.stopPropagation(); }
  }, true);

  /* ---------- details panel ---------- */
  const ICON = { note: "📘", playbook: "🧯", kodekloud: "🎓", course: "🎓", video: "▶️", lab: "🧪", read: "📖", doc: "📄", book: "📚", link: "🔗", interview: "🎤" };
  /* copy via the page's shared helper: clipboard API, else the text in `el` is selected for a manual copy */
  function copyText(str, el, btn) {
    if (window.__handbookCopy) { window.__handbookCopy(str, el, btn); return; }
    try { navigator.clipboard.writeText(String(str)).catch(() => {}); } catch (_) { /* no clipboard */ }
  }
  function section(title, ...kids) { return [h("h3", { class: "mp-h" }, title), ...kids]; }
  function bullets(items) { return h("ul", null, arr(items).map(x => h("li", null, String(x)))); }
  function tsItem(s) {
    s = String(s);
    const m = /\s*(?:→|->)\s*/.exec(s);
    if (!m) return h("li", null, s);
    return h("li", null, h("span", { class: "ts-sym" }, s.slice(0, m.index)), h("span", { class: "ts-arrow", "aria-hidden": "true" }, "→"),
      h("code", null, s.slice(m.index + m[0].length)));
  }
  function cmdRow(c) {
    const b = h("button", { type: "button", class: "mp-copy", "aria-label": "Copy command" }, "copy");
    const code = h("code", null, String(c));
    b.addEventListener("click", () => copyText(String(c), code, b));
    return h("div", { class: "mp-cmd" }, code, b);
  }
  const isHttp = u => /^https?:\/\//i.test(String(u || ""));
  function studyItem(it) {
    if (!it || typeof it !== "object") return h("li", null, h("span", { class: "si-body" }, String(it)));
    const type = String(it.type || (it.file ? "note" : "link")).toLowerCase();
    const label = it.label || it.heading || it.file || it.url || "untitled";
    let main, badge = null;
    if (it.anchor) {
      main = h("button", { type: "button", class: "mp-jump", title: (it.module_title ? "Handbook › " + it.module_title : "Open in the handbook"),
        onclick: () => jumpTo(it.anchor) }, label);
      badge = h("span", { class: "badge badge-local" }, "handbook");
    } else if (it.file) {
      main = h("span", { class: "mp-pending" }, label);
      badge = h("span", { class: "badge" }, "coming soon");
    } else if (isHttp(it.url)) {
      main = h("a", { href: it.url, target: "_blank", rel: "noopener noreferrer" }, label);
      badge = h("span", { class: "badge badge-online", title: "Needs internet" }, "online ↗");
    } else {
      main = h("span", null, label);
      if (type === "kodekloud") badge = h("span", { class: "badge", title: "Find it in your KodeKloud library" }, "in KodeKloud");
    }
    return h("li", null, h("span", { class: "si-icon", "aria-hidden": "true", title: type }, ICON[type] || "🔗"),
      h("span", { class: "si-body" }, main, badge, it.note ? h("span", { class: "si-note" }, String(it.note)) : null));
  }
  function chips(ids, empty) {
    if (!ids.length) return h("p", { class: "mp-empty" }, empty);
    return h("div", { class: "mp-chipset" }, ids.map(id => {
      const n = G.byId[id], tr = trOf(n), done = S.done.has(id);
      return h("button", { type: "button", class: "chip chip-node" + (done ? " is-done" : ""), style: `--c:${tr.col}`,
        title: `${LV(lvOf(n))} · ${tr.name}`, onclick: () => select(id, { fly: true }) },
        h("span", { class: "dot" }), (done ? "✓ " : "") + n.title);
    }));
  }
  /* "Prove it" ladder (prove_site.py): decision drills, lab rooms, then outside practice sites */
  const PROVE = (() => {
    const el = document.getElementById("prove-data");
    try { return el ? JSON.parse(el.textContent) : null; } catch (_) { return null; }
  })();
  const RUNS = { browser: "in the browser", "vendor-account": "in the browser", "throwaway-vm": "throwaway VM", "own-cloud-account": "can bill YOUR cloud account" };
  const RUNS_TIP = { browser: "The vendor hosts everything; you need a browser, sometimes an SSH client.",
    "vendor-account": "A lab account the vendor creates and deletes; it cannot bill you.",
    "throwaway-vm": "Run it on a lab VM or Codespace you delete afterwards, never on a work laptop or real server.",
    "own-cloud-account": "You deploy into your own cloud account and pay for what it uses: set a budget alarm first." };
  const SIGNUP = { "free-account": "free account", card: "card needed" };
  function drillBest(id) {                         // drills_site.py keeps {id: {s: best score, r: stars}} under "drills.best"
    try { const b = JSON.parse(window.localStorage.getItem("drills.best") || "{}"), o = b && b[id]; return o && o.s >= 0 ? o.s : null; }
    catch (_) { return null; }
  }
  /* like the handbook links: close the map and open the drill or lab room on an entry of its own, so Back
     (or the room's ✕) reopens this topic at the same panel scroll (QA4: it used to replace the map entry) */
  function openPractice(kind, id) {
    const api = kind === "drill" ? window.__drills : window.__labs, fn = api && (kind === "drill" ? api.open : api.openRoom);
    try { history.replaceState(Object.assign({}, history.state, { mapSel: S.selected, mapPt: panel.scrollTop }), ""); } catch (_) { /* ignore */ }
    closeMap({ keepHistory: true });
    if (typeof fn !== "function") { location.hash = "#" + kind + "." + id; return; }
    fn(id);
  }
  function practiceLink(kind, id, info) {
    return h("a", { href: `#${kind}.${id}`, class: "pv-local",
      onclick: e => { if (e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; e.preventDefault(); openPractice(kind, id); } },
      (kind === "drill" ? "🎯 " : "🧪 ") + (info && info.t ? info.t : id));
  }
  function proveSection(n) {
    const P = n.prove;
    if (!P || !PROVE) return [];
    const steps = [], mins = info => (info && info.m ? h("span", { class: "badge" }, `${info.m} min`) : null);
    if (arr(P.d).length) steps.push(h("li", null, h("span", { class: "pv-step" }, "Decision drill ", h("small", null, "· pick each move in a real outage")),
      h("ul", { class: "pv-list" }, P.d.map(id => {
        const info = PROVE.drills[id], best = drillBest(id);
        return h("li", null, practiceLink("drill", id, info), mins(info),
          best == null ? null : h("span", { class: "badge badge-done", title: "Your best score on this device" }, `✓ played ${best}`));
      }))));
    if (arr(P.l).length) steps.push(h("li", null, h("span", { class: "pv-step" }, "Lab room ", h("small", null, "· fix it on a disposable server")),
      h("ul", { class: "pv-list" }, P.l.map(id => h("li", null, practiceLink("lab", id, PROVE.labs[id]), mins(PROVE.labs[id]),
        h("span", { class: "badge", title: "Checked live with the local lab server; read-only without it" }, "local lab"))))));
    const sites = arr(P.s).map(ref => {
      const id = typeof ref === "string" ? ref : ref && ref.id, s = PROVE.sites[id];
      if (!s) return null;
      const deep = ref && ref.deep && s.deep && s.deep[ref.deep] ? ref.deep : null;
      const badges = [];
      if (RUNS[s.runs]) badges.push(h("span", { class: "badge" + (s.runs === "own-cloud-account" ? " badge-warn" : ""), title: RUNS_TIP[s.runs] }, RUNS[s.runs]));
      if (SIGNUP[s.signup]) badges.push(h("span", { class: "badge", title: "The least you need to start" }, SIGNUP[s.signup]));
      if (s.cost === "freemium") badges.push(h("span", { class: "badge", title: "Real practice works on the free tier; a paid plan adds more" }, "free tier"));
      if (s.checked_on) badges.push(h("span", { class: "badge", title: "Date these facts were last checked" }, `checked ${s.checked_on}`));
      return h("li", null, h("a", { href: deep ? s.deep[deep] : s.url, target: "_blank", rel: "noopener noreferrer", class: "pv-site" },
        s.name + (deep ? `: ${deep}` : "") + " ↗"), ...badges);
    }).filter(Boolean);
    if (sites.length) steps.push(h("li", null, h("span", { class: "pv-step" }, "Outside practice ", h("small", null, "· needs internet, opens in a new tab")),
      h("ul", { class: "pv-list" }, sites)));
    if (!steps.length) return [];
    return section("Prove it: you've got it when you can do this on a broken system",
      h("ol", { class: "mp-prove" }, steps),
      h("p", { class: "mp-key" }, "Easiest first. Nothing is tracked: you decide when you're ready."));
  }
  /* job search unlocks at each milestone: links resolved at build time (job_links in build_site.py) */
  const JOB = raw.job && raw.job.n ? raw.job : null, AJS = "https://github.com/ai-job-search-dev/ai-job-search";
  let jobPop = null;                               // milestone just marked done: its badge pops once
  function jobSection(n, done) {
    const J = JOB && JOB.n[n.id];
    if (!J) return [];
    const btn = h("button", { type: "button", class: "mbtn" + (done ? "" : " mbtn-accent"), onclick: () => toggleDone(n.id) },
      done ? "↺ Not ready yet? Lock it again" : "☐ Mark as done");
    const local = "Nothing is tracked except on your own device.";
    if (!done) return section("🔒 Job search — unlocks when you mark this milestone done", h("div", { class: "mp-job" },
      h("p", null, "Pass the exit check above first, then mark it done. " + local), btn));
    const pop = jobPop === n.id;
    const li = (b, t, warn) => h("li", null, h("span", { class: "badge" + (warn ? " badge-warn" : "") }, b), " ", t);
    return section(`🔓 You're ready to apply for ${J.r}`, h("div", { class: "mp-job is-open", "data-tone": "teal" },
      h("p", null, h("span", { class: "badge badge-done" + (pop ? " jb-pop" : "") }, "🎉 milestone done"),
        " Prepare the stage you apply for and the one below it."),
      h("ul", { class: "mp-study" }, [J.l[0], JOB.c[0], J.l[1], JOB.c[1]].filter(Boolean)
        .map(([anchor, label, k]) => studyItem({ anchor, label, type: k === "i" ? "interview" : "note" }))),
      h("p", null, h("a", { href: AJS, target: "_blank", rel: "noopener noreferrer" }, "🧰 ai-job-search ↗"), " ",
        h("span", { class: "badge" }, "MIT"), " ", h("span", { class: "badge" }, "~70k ★"), " ",
        h("span", { class: "badge badge-online", title: "Needs internet" }, "online ↗")),
      h("p", { class: "mp-key" }, "Commands and skills that run inside Claude Code (a paid Claude plan or API credits): score job posts, " +
        "tailor your CV, draft cover letters, prepare interviews and track applications. Needs Python 3.10+, Bun and LaTeX."),
      h("ol", null, h("li", null, "Make a private repo and add this one as upstream (don't fork: forks are always public)."),
        h("li", null, "Open it in Claude Code and run /setup."),
        h("li", null, "Search with freehire-search (software, DevOps, remote roles) or add your own board with /add-portal.")),
      h("ul", { class: "jb-warn" },
        li("private", "Setup writes your contact details, job history and salary expectations into tracked files.", 1),
        li("ToS", "Skip linkedin-search: it uses LinkedIn's guest endpoints, which its own README says breaks LinkedIn's terms.", 1),
        li("Danish", "Most bundled portal skills are Danish job boards."),
        li("you submit", "It drafts and tracks, never applies for you. Job posts are untrusted input: review what it fetches.")),
      btn, h("p", { class: "mp-key" }, local)));
  }
  function renderPanel(n) {
    const lv = lvOf(n), tr = trOf(n), done = S.done.has(n.id);
    const kids = [];
    kids.push(h("div", { class: "mp-top" },
      h("div", { class: "mp-chips" },
        h("span", { class: "chip chip-level" }, LV(lv)),
        h("span", { class: "chip", style: `--c:${tr.col}` }, h("span", { class: "dot" }), tr.name),
        n.env === "onprem" || n.env === "cloud" ? h("span", { class: "chip" }, n.env === "onprem" ? "🏢 On-prem" : "☁️ Cloud") : null),
      h("button", { type: "button", class: "mp-close", "aria-label": "Close details", title: "Close details", onclick: deselect }, "✕")));
    kids.push(h("h2", { class: "mp-title", id: "map-panel-title" }, n.title));
    if (n.summary) kids.push(h("p", { class: "mp-summary" }, String(n.summary)));
    const linkBtn = h("button", { type: "button", class: "mbtn", title: "Copy a link that opens the map on this topic" }, "🔗 Link");
    linkBtn.addEventListener("click", () => {
      const url = location.href.split("#")[0] + core.mapHash(n.id);
      toast(url, 6000);                             // visible + selectable if the clipboard is unavailable
      copyText(url, toastEl, linkBtn);
    });
    kids.push(h("div", { class: "mp-actions" },
      h("button", { type: "button", class: "mbtn mp-done" + (done ? " is-done" : ""), "aria-pressed": String(done),
        onclick: () => toggleDone(n.id) }, done ? "✓ Done" : "☐ Mark as done"),
      h("button", { type: "button", class: "mbtn", onclick: () => focusNode(n.id), title: "Fly the camera to this topic" }, "◎ Focus"),
      linkBtn));
    if (S.pathMode && n.id in G.pathPos) kids.push(h("p", { class: "mp-pathinfo" }, `Guided path · step ${G.pathPos[n.id] + 1} of ${G.path.length}`));
    // learning order (user, 9 Nov 2026): prerequisites → study path → commands → prove it → related → next step
    if (n.why || arr(n.learn).length) kids.push(h("details", { class: "mp-about" },
      h("summary", { class: "mp-h" }, "Why it matters · what you'll learn"),
      n.why ? h("p", null, String(n.why)) : null, arr(n.learn).length ? bullets(n.learn) : null));
    kids.push(...section("Prerequisites", chips(n.parents, "None — this is a starting point.")));
    if (arr(n.study).length) kids.push(...section("Study path (in this order)", h("ol", { class: "mp-study" }, n.study.map(studyItem))));
    if (arr(n.commands).length) kids.push(...section("Key commands", h("div", { class: "mp-cmds" }, n.commands.map(cmdRow))));
    if (arr(n.practice).length) kids.push(...section("Practice drills (on a test VM)", bullets(n.practice)));
    if (arr(n.troubleshoot).length) kids.push(...section("Troubleshooting: symptom → first command", h("ul", { class: "mp-ts" }, n.troubleshoot.map(tsItem))));
    if (n.exit_check) kids.push(...section("Exit check — you've got it when…", h("p", { class: "mp-exit" }, String(n.exit_check))));
    kids.push(...proveSection(n));
    kids.push(...jobSection(n, done));
    if (arr(n.links).length) kids.push(...section("Related playbooks & notes", h("ul", { class: "mp-study" }, n.links.map(studyItem))));
    kids.push(...section("Next step →", chips(n.children, "Nothing builds on this yet. Continue with the guided path.")));
    const later = core.descendants(G, n.id).size - n.children.length;
    if (later > 0) kids.push(h("p", { class: "mp-key" }, `On the map: prerequisites glow blue, next steps green (dashed); ${later} further topic${later === 1 ? "" : "s"} downstream stay faintly lit.`));
    if (S.pathMode && n.id in G.pathPos && G.pathPos[n.id] < G.path.length - 1) {
      const nx = G.byId[G.path[G.pathPos[n.id] + 1]];
      kids.push(h("p", { class: "mp-pathinfo" }, h("button", { type: "button", class: "mbtn mbtn-accent", onclick: () => goPath(G.pathPos[n.id] + 1) }, `Next on the path: ${nx.title} ▶`)));
    }
    panel.replaceChildren(...kids);
    panel.hidden = false;
    overlay.classList.add("panel-open");
    panel.scrollTop = 0;
  }

  /* ---------- selection, progress, path ---------- */
  function setHash(hsh) {
    if (location.hash === hsh) return;
    try { history.replaceState(history.state, "", hsh); } catch (_) { /* file:// quirks */ }
  }
  function select(id, opts) {
    opts = opts || {};
    const n = G.byId[id];
    if (!n) return;
    if (!envOk(n) && window.__setHandbookEnv) window.__setHandbookEnv("both");   // opening an other-environment topic shows Both
    if (!isVisible(n)) { S.hiddenTracks.delete(n.track); S.hiddenLevels.delete(n.level); syncLegend(); }
    S.selected = id; S.hover = null; hideTip(); interact();
    if (S.pathMode && id in G.pathPos) { S.pathIdx = G.pathPos[id]; renderPathBar(); }
    renderPanel(n);
    setHash(core.mapHash(id));
    live.textContent = `Selected ${n.title}, ${LV(lvOf(n))}, ${trOf(n).name}. ${n.parents.length} prerequisites, ${n.children.length} next steps.`;
    if (S.listOpen) renderList();
    if (opts.fly) focusNode(id);
    requestRender();
  }
  function deselect() {
    S.selected = null; panel.hidden = true; overlay.classList.remove("panel-open");
    if (S.open) setHash("#map");
    if (S.listOpen) renderList();
    requestRender();
  }
  function toggleDone(id) {
    if (S.done.has(id)) S.done.delete(id); else { S.done.add(id); jobPop = id; }
    saveDone(); updateProgress();
    if (S.selected) { const y = panel.scrollTop; renderPanel(G.byId[S.selected]); panel.scrollTop = y; }   // stay put: the job section sits low
    jobPop = null;
    if (S.listOpen) renderList();
    if (S.pathMode) renderPathBar();
    requestRender();
  }
  function updateProgress() { $id("map-progress").textContent = `✓ ${S.done.size}/${G.nodes.length} done`; }
  const pathBtn = $id("map-path-btn");
  function startPath() {
    if (!G.path.length) return;
    S.pathMode = true;
    pathBtn.setAttribute("aria-pressed", "true");
    let i = G.path.findIndex(id => !S.done.has(id));
    if (i < 0) i = 0;
    goPath(i);
  }
  function goPath(i) {
    if (!G.path.length) return;
    if (!S.pathMode) { S.pathMode = true; pathBtn.setAttribute("aria-pressed", "true"); }
    S.pathIdx = clamp(i, 0, G.path.length - 1);
    renderPathBar();
    select(G.path[S.pathIdx], { fly: true });
  }
  function endPath() {
    S.pathMode = false; pathBar.hidden = true; pathBtn.setAttribute("aria-pressed", "false");
    if (S.selected) renderPanel(G.byId[S.selected]);
    requestRender();
  }
  function renderPathBar() {
    const id = G.path[S.pathIdx], n = G.byId[id];
    pathBar.replaceChildren(
      h("span", { class: "pb-label" }, h("strong", null, `Step ${S.pathIdx + 1}/${G.path.length}`), " ", n.title),
      h("button", { type: "button", class: "mbtn", disabled: S.pathIdx === 0, onclick: () => goPath(S.pathIdx - 1), "aria-label": "Previous step" }, "◀"),
      h("button", { type: "button", class: "mbtn mbtn-accent", disabled: S.pathIdx >= G.path.length - 1, onclick: () => goPath(S.pathIdx + 1) }, "Next ▶"),
      h("button", { type: "button", class: "mbtn", title: "Mark this step done and continue",
        onclick: () => { if (!S.done.has(id)) toggleDone(id); if (S.pathIdx < G.path.length - 1) goPath(S.pathIdx + 1); } },
        S.done.has(id) ? "✓ Next" : "✓ Done"),
      h("button", { type: "button", class: "mbtn", "aria-label": "End guided path", title: "End guided path", onclick: endPath }, "✕"));
    pathBar.hidden = false;
  }

  /* ---------- legend filters ---------- */
  function syncLegend() {
    overlay.querySelectorAll("[data-track]").forEach(b => b.setAttribute("aria-pressed", String(!S.hiddenTracks.has(b.dataset.track))));
    overlay.querySelectorAll("[data-level]").forEach(b => b.setAttribute("aria-pressed", String(!S.hiddenLevels.has(b.dataset.level))));
  }
  function toggleFilter(set, key) {
    if (set.has(key)) set.delete(key); else set.add(key);
    if (S.selected && !isVisible(G.byId[S.selected])) deselect();
    syncLegend(); interact(); requestRender();
  }
  G.tracks.forEach(tr => $id("map-legend-tracks").append(
    h("button", { type: "button", class: "lg-chip", "aria-pressed": "true", "data-track": tr.id, style: `--c:${tr.col}`,
      title: `Show / hide the ${tr.name} track`, onclick: () => toggleFilter(S.hiddenTracks, tr.id) }, h("span", { class: "dot" }), tr.name)));
  G.levels.forEach(lv => $id("map-legend-levels").append(
    h("button", { type: "button", class: "lg-chip", "aria-pressed": "true", "data-level": lv.id,
      title: `Show / hide ${LV(lv)}`, onclick: () => toggleFilter(S.hiddenLevels, lv.id) }, lv.id, h("span", { class: "lg-name" }, " " + LV(lv).slice(String(lv.id).length + 3)))));

  /* ---------- accessible list view ---------- */
  const listBtn = $id("map-list-btn");
  function renderList() {
    const prog = core.levelProgress({ levels: G.levels, nodes: G.nodes.filter(envOk) }, S.done);
    const rank = n => (n.id in G.pathPos ? G.pathPos[n.id] : 1e6 + n.index);
    const parts = [
      h("div", { class: "ml-head" }, h("h2", null, "All topics by level"),
        h("button", { type: "button", class: "mp-close", "aria-label": "Close list", onclick: () => toggleList(false) }, "✕")),
      h("p", { class: "ml-hint" }, "Bottom floor first, in guided-path order. Each button opens the topic."),
    ];
    G.levels.forEach((lv, li) => {
      const nodes = G.nodes.filter(n => n.li === li && envOk(n)).sort((a, b) => rank(a) - rank(b));
      if (!nodes.length) return;
      parts.push(h("section", { class: "ml-level" },
        h("h3", null, `${LV(lv)} `, h("span", { class: "ml-count" }, `${prog[li].done}/${prog[li].total} done`)),
        lv.goal ? h("p", { class: "ml-goal" }, String(lv.goal)) : null,
        h("ul", null, nodes.map(n => h("li", null, h("button", {
          type: "button", class: "ml-node" + (S.selected === n.id ? " is-sel" : ""), "aria-current": S.selected === n.id ? "true" : null,
          onclick: () => (S.selected === n.id ? deselect() : select(n.id, { fly: true, fromList: true })) },
          h("span", { class: "dot", style: `--c:${trOf(n).col}` }), h("span", { class: "ml-title" }, n.title),
          h("span", { class: "ml-meta" }, trOf(n).name + (S.done.has(n.id) ? " · ✓" : "")))))),
        lv.exit_test ? h("p", { class: "ml-exit" }, h("strong", null, "Exit test: "), String(lv.exit_test)) : null));
    });
    const keep = listEl.scrollTop;
    listEl.replaceChildren(...parts);
    listEl.scrollTop = keep;
  }
  function toggleList(force) {
    S.listOpen = force == null ? !S.listOpen : !!force;
    listEl.hidden = !S.listOpen;
    listBtn.setAttribute("aria-pressed", String(S.listOpen));
    if (S.listOpen) {
      renderList();
      const first = listEl.querySelector(".ml-node.is-sel") || listEl.querySelector(".ml-node");
      if (first) first.focus({ preventScroll: false });
    } else if (overlay.contains(document.activeElement) === false || listEl.contains(document.activeElement)) {
      listBtn.focus();
    }
    requestRender();
  }

  /* ---------- search ---------- */
  let qHits = [], qSel = -1;
  function closeResults() { qRes.hidden = true; qHits = []; qSel = -1; }
  function renderResults() {
    if (!qIn.value.trim()) { closeResults(); return; }
    qRes.replaceChildren(...(qHits.length ? qHits.map((id, i) => {
      const n = G.byId[id];
      const b = h("button", { type: "button", role: "option", class: i === qSel ? "sel" : "", "aria-selected": String(i === qSel) },
        n.title, h("small", null, `${LV(lvOf(n))} · ${trOf(n).name}`));
      b.addEventListener("pointerdown", ev => ev.preventDefault());
      b.addEventListener("click", () => pickResult(id));
      return b;
    }) : [h("div", { class: "nores" }, "No topic matches — try a tool name like dig or tcpdump.")]));
    qRes.hidden = false;
  }
  function pickResult(id) { closeResults(); qIn.value = ""; select(id, { fly: true }); canvas.focus({ preventScroll: true }); }
  qIn.addEventListener("input", () => { qHits = core.searchNodes(G, qIn.value, 8); qSel = qHits.length ? 0 : -1; renderResults(); });
  qIn.addEventListener("keydown", e => {
    if (e.key === "ArrowDown" && qHits.length) { e.preventDefault(); qSel = (qSel + 1) % qHits.length; renderResults(); }
    else if (e.key === "ArrowUp" && qHits.length) { e.preventDefault(); qSel = (qSel - 1 + qHits.length) % qHits.length; renderResults(); }
    else if (e.key === "Enter") { e.preventDefault(); if (qHits.length) pickResult(qHits[Math.max(0, qSel)]); }
  });
  qIn.addEventListener("blur", () => setTimeout(closeResults, 120));

  /* ---------- toast ---------- */
  let toastT = 0;
  function toast(msg, ms) { toastEl.textContent = msg; toastEl.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { toastEl.hidden = true; }, ms || 4000); }

  /* ---------- open / close / routing ---------- */
  let lastFocus = null;
  function setInert(on) {
    ["topbar", "sidebar", "scrim", "main", "totop"].forEach(id => {
      const el = $id(id);
      if (!el) return;
      if ("inert" in el) el.inert = on; else if (on) el.setAttribute("aria-hidden", "true"); else el.removeAttribute("aria-hidden");
    });
  }
  function openMap(opts) {
    opts = opts || {};
    if (opts.push) { try { history.pushState({ handbookMap: 1 }, "", opts.push); } catch (_) { /* ignore */ } }
    if (S.open) return;
    lastFocus = document.activeElement;
    S.open = true;
    overlay.hidden = false;
    document.documentElement.classList.add("map-open");
    setInert(true);
    if (window.__handbookCloseDrawer) window.__handbookCloseDrawer();
    resize();
    if (!S.viewInit) { Object.assign(S, homeView(S.flat)); S.viewInit = true; }
    S.autoRotate = !reduced && !S.selected && !S.flat && !S.pathMode;
    /* keep the open topic in the address, unless the link that opened the map names another topic */
    const target = opts.push ? core.parseHash(opts.push) : null;
    if (S.selected && !(target && target.id)) setHash(core.mapHash(S.selected));
    if (S.selected) { const y = panel.scrollTop; renderPanel(G.byId[S.selected]); panel.scrollTop = y; }
    updateProgress();
    try { canvas.focus({ preventScroll: true }); } catch (_) { canvas.focus(); }
    requestRender();
  }
  function closeMap(opts) {
    opts = opts || {};
    if (!S.open) return;
    S.open = false;
    overlay.hidden = true;
    document.documentElement.classList.remove("map-open");
    setInert(false);
    if (raf) cancelAnimationFrame(raf);
    raf = 0; lastT = 0; drag = null; pinch = null; pointers.clear();
    clearTimeout(idleTimer); hideTip(); closeResults();
    if (!opts.fromHash && !opts.keepHistory) {
      if (history.state && history.state.handbookMap) history.back();
      else if (core.parseHash(location.hash)) { try { history.replaceState(null, "", location.href.split("#")[0]); } catch (_) { /* ignore */ } }
    }
    if (!opts.keepHistory && lastFocus && document.contains(lastFocus) && lastFocus !== document.body) {
      try { lastFocus.focus({ preventScroll: true }); } catch (_) { /* ignore */ }
    }
  }
  /* internal study links: close the map and jump to the handbook heading */
  function jumpTo(anchor) {
    const el = document.getElementById(anchor);
    if (el && window.__backnav) { window.__backnav.jump(el, "#" + anchor); return; }   // pushes an entry: Back reopens this topic
    closeMap({ keepHistory: true });
    try { history.replaceState(null, "", "#" + anchor); } catch (_) { /* ignore */ }
    if (el) {
      if (window.__handbookJump) window.__handbookJump(el); else el.scrollIntoView({ block: "start" });
      el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
    }
  }
  function routeFromHash() {
    const m = core.parseHash(location.hash);      // "#map", "#map.ID" or legacy "#map/ID"
    if (!m) { if (S.open) closeMap({ fromHash: true }); return; }
    if (/^#map\//.test(location.hash)) setHash(core.mapHash(m.id));   // upgrade old links in place
    openMap();
    const id = m.id;
    if (id) {
      if (G.byId[id]) { if (S.selected !== id) select(id, { fly: true }); }
      else toast(`No topic called “${id}” — showing the whole map.`);
    } else if (S.selected) deselect();
    const hs = history.state;                      // back from a drill or lab room opened in this panel
    if (id && hs && hs.mapSel === id && hs.mapPt != null) { panel.scrollTop = hs.mapPt; requestAnimationFrame(() => { panel.scrollTop = hs.mapPt; }); }
  }
  addEventListener("hashchange", routeFromHash);
  addEventListener("popstate", routeFromHash);
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest("a[href^='#map']");
    if (!a) return;
    const href = a.getAttribute("href"), m = core.parseHash(href);
    if (!m) return;
    e.preventDefault();
    openMap({ push: core.mapHash(m.id) });
    if (m.id) routeFromHash();                     // "#map.NODE_ID" -> focus that node
  });
  if (mapBtn) mapBtn.addEventListener("click", () => { openMap({ push: "#map" }); });
  $id("map-close-btn").addEventListener("click", () => closeMap());
  $id("map-reset-btn").addEventListener("click", () => { interact(); flyTo(homeView(S.flat), 700); });
  $id("map-theme-btn").addEventListener("click", () => { if (window.__handbookToggleTheme) window.__handbookToggleTheme(); });
  const flatBtn = $id("map-flat-btn");
  function setFlat(on) {
    S.flat = !!on; flatBtn.setAttribute("aria-pressed", String(S.flat));
    interact(); S.autoRotate = false;
    if (S.selected) focusNode(S.selected); else flyTo(homeView(S.flat), 800);
    requestRender();
  }
  flatBtn.addEventListener("click", () => setFlat(!S.flat));
  listBtn.addEventListener("click", () => toggleList());
  pathBtn.addEventListener("click", () => (S.pathMode ? endPath() : startPath()));

  if (typeof ResizeObserver === "function") new ResizeObserver(() => { if (S.open) resize(); }).observe(stage);
  addEventListener("resize", () => { if (S.open) resize(); });
  const onMotion = e => { reduced = e.matches; if (reduced) S.autoRotate = false; };
  if (reduceMQ.addEventListener) reduceMQ.addEventListener("change", onMotion); else if (reduceMQ.addListener) reduceMQ.addListener(onMotion);

  window.__map = {
    core, graph: G, state: S, pos3, posF, open: openMap, close: closeMap, select, deselect,
    startPath, goPath, endPath, setFlat, toggleList, toggleDone, draw, homeView,
    projected: id => S.proj[id] || null, hits: () => S.hits.slice(),
  };
  if (core.parseHash(location.hash)) routeFromHash();
})();
</script>
__SOURCE_SCRIPT__
__UI_SCRIPT__
__DOC_END__"""


# The two outputs differ only in the document wrapper around the shared template.
VARIANTS = {
    "index": {
        "doc_start": ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                      '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                      '<meta name="color-scheme" content="light dark">\n'
                      '<title>DevOps Troubleshooting Handbook</title>\n'
                      '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 '
                      'viewBox=%270 0 100 100%27%3E%3Ctext y=%27.9em%27 font-size=%2790%27%3E%F0%9F%A7%B0'
                      '%3C/text%3E%3C/svg%3E">'),
        "body_open": "</head>\n<body>",
        "doc_end": "</body>\n</html>\n",
        "brand_small": "offline handbook",
    },
    # claude.ai artifact: the host wraps the page, so no doctype/html/head/body;
    # <title> must be the very first line, then <style> and the content.
    "artifact": {
        "doc_start": "<title>DevOps Field Handbook</title>",
        "body_open": "",
        "doc_end": "",
        "brand_small": "field handbook",
    },
}


def slim_template(t):
    """Minify the template's own <style> and <script> blocks (placeholders survive: they are
    plain identifiers on their own lines). JSON data blocks are not in the template."""
    t = re.sub(r"(<style>)(.*?)(</style>)", lambda m: m.group(1) + minify_css(m.group(2)) + m.group(3), t, flags=re.S)
    return re.sub(r"(<script(?: id=\"[\w-]+\")?>)(.*?)(</script>)",
                  lambda m: m.group(1) + minify_js(m.group(2)) + m.group(3), t, flags=re.S)


_SLIM_TEMPLATE = []


def render_page(variant, nav, content, legacy, roadmap, has_map, prove_data=None):
    v = VARIANTS[variant]
    if not _SLIM_TEMPLATE:
        _SLIM_TEMPLATE.append(slim_template(TEMPLATE))
    page = _SLIM_TEMPLATE[0]
    for key, val in (
        ("__DOC_START__", v["doc_start"]),
        ("__BODY_OPEN__", v["body_open"]),
        ("__DOC_END__", v["doc_end"]),
        ("__SOURCE_CSS__", SOURCE_CSS + INTERVIEW_CSS + DECODER_CSS + LABS_CSS + DRILLS_CSS + PROVE_CSS + BACKNAV_CSS),
        ("__SOURCE_SCRIPT__", SOURCE_SCRIPT + DECODER_SCRIPT + LABS_SCRIPT + DRILLS_SCRIPT + BACKNAV_SCRIPT),
        ("__BACKNAV_HTML__", BACKNAV_HTML),
        ("__EXTERNAL_LINKS_JS__", EXTERNAL_LINKS_JS),
        ("__UI_CSS__", UI_CSS),
        ("__UI_SCRIPT__", UI_SCRIPT),
        ("__BRAND_SMALL__", v["brand_small"]),
        ("__MAPBTN_HIDDEN__", "" if has_map else " hidden"),
        ("__MAP_OVERLAY__", MAP_OVERLAY if has_map else ""),
        ("__LEGACY_JSON__", json.dumps(legacy)),
        ("__ROADMAP_DATA__", f'<script type="application/json" id="roadmap-data">{json_for_script(roadmap)}</script>'
                             + (f'<script type="application/json" id="prove-data">{json_for_script(prove_data)}</script>'
                                if prove_data else "")
                             if has_map else ""),
        ("__NAV__", nav),
    ):
        page = page.replace(key, val)
    # content last: module text must never be scanned for placeholders
    return page.replace("__CONTENT__", content, 1)


def write(path, page):
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return os.path.getsize(path) / 1024


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the offline handbook (index.html) and its artifact twin (artifact.html).")
    ap.add_argument("--out", default=OUT, help="standalone offline html (default: index.html next to this script)")
    ap.add_argument("--artifact-out", default=ARTIFACT_OUT,
                    help="claude.ai artifact html (default: artifact.html next to this script; '' to skip)")
    ap.add_argument("--roadmap", default=ROADMAP, help="roadmap json for the 3D map (default: roadmap.json)")
    args = ap.parse_args(argv)

    warnings = []

    def warn(msg):
        warnings.append(msg)
        print("WARNING: " + msg)

    mods, by_file = load_modules(warn)
    if not mods:
        print("ERROR: no markdown modules found — nothing to build")
        return 1
    roadmap = process_roadmap(args.roadmap, by_file, warn)
    has_map = roadmap is not None and len(roadmap["nodes"]) > 0
    if roadmap is not None and not has_map:
        warn("roadmap has no nodes — 3D course map disabled")

    legacy = {str(i): by_file[f]["sec"] for i, f in enumerate(LEGACY_ORDER) if f in by_file}
    nav = build_nav(mods, has_map)
    prove = None
    if has_map:
        # "Prove it" ladder: drills/labs computed from their own data, sites from roadmap prove_sites
        with open(args.roadmap, encoding="utf-8-sig") as f:
            raw_nodes = [n for n in (json.load(f).get("nodes") or []) if isinstance(n, dict) and n.get("id")]
        prove = (topic_ladders(roadmap, HERE, warn), module_topics(raw_nodes))
    content = build_content(mods, roadmap if has_map else None, prove)

    outputs = [("index", args.out)]
    if args.artifact_out:
        outputs.append(("artifact", args.artifact_out))
    missing = sum(1 for f, *_ in MODULES if f not in by_file)
    extra = sum(1 for m in mods if m["group"] == "More")
    for variant, path in outputs:
        size = write(path, render_page(variant, nav, content, legacy, roadmap, has_map, prove and prove[0]))
        if size > 15.5 * 1024:
            warn(f"{os.path.basename(path)} is {size / 1024:.1f} MB — close to the 16 MB artifact limit")
        print(f"wrote {path} ({size:.0f} KB)")
    print(f"built {len(mods)} modules"
          + (f" ({missing} listed module(s) missing, skipped)" if missing else "")
          + (f" (+{extra} unlisted under 'More')" if extra else "")
          + (", 3D map on" if has_map else ", 3D map off")
          + (f", {len(warnings)} warning(s)" if warnings else ", no warnings"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
