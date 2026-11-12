"""The "Prove it" practice ladder: where a reader proves they can troubleshoot a topic.

Three steps per roadmap topic, ordered by effort:
  1. Decision drills  - computed from drills/*.json "topics" (roadmap node ids)
  2. Lab rooms        - computed from labs/rooms/*/room.json "map_node"
  3. Outside sites    - curated per node in roadmap.json "prove_sites": ["site-id" | {"id", "deep"}]
                        ids from research/practice.json (the one source of truth for outside sites;
                        "deep" names one of that site's deep_links by its label)

The build attaches node["prove"] = {"d": [drill ids], "l": [room ids], "s": [refs]} to the embedded
roadmap (the 3D map panel renders it after the exit check) and embeds one compact catalog,
<script type="application/json" id="prove-data">, with only the sites, deep links, drills and rooms
actually referenced. Each module page also gets a build-time "Prove it" strip (works without JS)
for the topics whose study/links point at that module.

Sites whose status is not "ok", and anything flagged do_not_link in the catalog, are never linked.
"""
import html
import json
import os

from drills_site import load_drills
from labs_site import load_rooms

PRACTICE_FILE = os.path.join("research", "practice.json")
MAX_SITES = 3          # per topic
STRIP_MAX = 6          # items in a module strip
STRIP_TOPICS = 4       # map-topic chips in a module strip

# badges: where it runs / what you need (research/practice.json runs_legend and signup)
RUNS_BADGE = {"browser": "in the browser", "vendor-account": "in the browser",
              "throwaway-vm": "throwaway VM", "own-cloud-account": "can bill YOUR cloud account"}
RUNS_TIP = {"browser": "The vendor hosts everything; you need a browser, sometimes an SSH client.",
            "vendor-account": "A lab account the vendor creates and deletes; it cannot bill you.",
            "throwaway-vm": "Run it on a lab VM or Codespace you delete afterwards, never on a work laptop or real server.",
            "own-cloud-account": "You deploy into your own cloud account and pay for what it uses: set a budget alarm first."}
SIGNUP_BADGE = {"free-account": "free account", "card": "card needed"}


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load_practice(here):
    """(linkable sites by id, ids that must never be linked) from research/practice.json."""
    path = os.path.join(here, PRACTICE_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}, set()
    blocked = set()
    for group in ("sites", "dead_or_renamed", "paid_only", "excluded_after_research"):
        for row in data.get(group) or []:
            if isinstance(row, dict) and row.get("do_not_link"):
                blocked.add(row.get("id") or row.get("site"))
    sites = {s["id"]: s for s in data.get("sites") or []
             if isinstance(s, dict) and s.get("id") and s.get("status") == "ok" and s["id"] not in blocked
             and str(s.get("url", "")).startswith(("https://", "http://"))}
    return sites, blocked


def site_ref(ref):
    """'id' or {"id", "deep"} -> (id, deep label or None)."""
    if isinstance(ref, str):
        return ref, None
    if isinstance(ref, dict) and isinstance(ref.get("id"), str):
        deep = ref.get("deep")
        return ref["id"], deep if isinstance(deep, str) and deep else None
    return None, None


def deep_url(site, label):
    for d in site.get("deep_links") or []:
        if d.get("label") == label and str(d.get("url", "")).startswith(("https://", "http://")):
            return d["url"]
    return None


def topic_ladders(roadmap, here, warn):
    """Attach node["prove"] (and drop the raw prove_sites) on the embedded roadmap.
    Returns the compact catalog for #prove-data."""
    sites, blocked = load_practice(here)
    drills = load_drills(here)
    rooms = load_rooms(here)
    ids = {n["id"] for n in roadmap["nodes"]}
    by_topic_d, by_topic_l = {}, {}
    for d in drills:
        for t in d.get("topics") or []:
            if t in ids and d["id"] not in by_topic_d.setdefault(t, []):
                by_topic_d[t].append(d["id"])
    for r in rooms:
        t = r.get("map_node")
        if t in ids:
            by_topic_l.setdefault(t, []).append(r["id"])
    used, used_d, used_l = {}, set(), set()
    for n in roadmap["nodes"]:
        refs = n.pop("prove_sites", None) or []
        if not isinstance(refs, list):
            warn(f"roadmap node '{n['id']}': 'prove_sites' must be a list")
            refs = []
        clean, seen = [], set()
        for ref in refs:
            sid, deep = site_ref(ref)
            if sid in blocked:
                warn(f"roadmap node '{n['id']}': prove site '{sid}' is flagged do_not_link — dropped")
                continue
            site = sites.get(sid)
            if not site:
                warn(f"roadmap node '{n['id']}': prove site {sid!r} is not an 'ok' site in {PRACTICE_FILE} — dropped")
                continue
            if sid in seen:
                continue
            if deep and not deep_url(site, deep):
                warn(f"roadmap node '{n['id']}': {sid} has no deep link labelled {deep!r} — linking the main page")
                deep = None
            seen.add(sid)
            clean.append({"id": sid, "deep": deep} if deep else sid)
            entry = used.setdefault(sid, {k: site.get(k) for k in
                                          ("name", "url", "cost", "signup", "runs", "checked_on")})
            if deep:
                entry.setdefault("deep", {})[deep] = deep_url(site, deep)
        if len(clean) > MAX_SITES:
            warn(f"roadmap node '{n['id']}': {len(clean)} prove sites, only the first {MAX_SITES} are shown")
            clean = clean[:MAX_SITES]
        p = {}
        if by_topic_d.get(n["id"]):
            p["d"] = by_topic_d[n["id"]]
            used_d.update(p["d"])
        if by_topic_l.get(n["id"]):
            p["l"] = by_topic_l[n["id"]]
            used_l.update(p["l"])
        if clean:
            p["s"] = clean
        if p:
            n["prove"] = p
    return {
        "sites": used,
        "drills": {d["id"]: {"t": d["title"], "m": d.get("minutes")} for d in drills if d["id"] in used_d},
        "labs": {r["id"]: {"t": r["title"], "m": r.get("minutes")} for r in rooms if r["id"] in used_l},
    }


def module_topics(raw_nodes):
    """module file -> topic ids whose own study/links point at it (study first, then links, in node order).
    Uses the roadmap as written (not the build's added 'Sources & verification' links)."""
    out = {}
    for kind in ("study", "links"):
        for n in raw_nodes:
            for item in n.get(kind) or []:
                f = item.get("file") if isinstance(item, dict) else None
                if f and n["id"] not in out.setdefault(f, []):
                    out[f].append(n["id"])
    return out


def site_badges(site):
    """[(text, extra class, title)] for one catalog site."""
    out = []
    runs = site.get("runs")
    if runs in RUNS_BADGE:
        out.append((RUNS_BADGE[runs], " badge-warn" if runs == "own-cloud-account" else "", RUNS_TIP[runs]))
    if site.get("signup") in SIGNUP_BADGE:
        out.append((SIGNUP_BADGE[site["signup"]], "", "The least you need to start"))
    if site.get("cost") == "freemium":
        out.append(("free tier", "", "Real practice works on the free tier; a paid plan adds more"))
    if site.get("checked_on"):
        out.append((f"checked {site['checked_on']}", "", "Date these facts were last checked"))
    return out


def short_title(title):
    """'Traefik v3: entryPoints, routers, services' -> 'Traefik v3' (the part before the first colon)."""
    head = str(title).split(": ", 1)[0].strip()
    return head if len(head) >= 4 else str(title)


def strip_html(fname, topics, nodes_by_id, catalog, map_href):
    """Build-time 'Prove it' strip for the end of one module page ('' when there is nothing to show)."""
    drills, labs, sites = [], [], []
    for t in topics:
        p = (nodes_by_id.get(t) or {}).get("prove") or {}
        drills += [d for d in p.get("d", []) if d not in drills]
        labs += [r for r in p.get("l", []) if r not in labs]
        for ref in p.get("s", []):
            sid, deep = site_ref(ref)
            if sid not in [s for s, _ in sites]:
                sites.append((sid, deep))
    drills, labs = drills[:2], labs[:2]
    sites = sites[:max(0, STRIP_MAX - len(drills) - len(labs))]
    if not (drills or labs or sites):
        return ""
    cards = []
    for d in drills:
        info = catalog["drills"].get(d, {})
        mins = f" · {_esc(info['m'])} min" if info.get("m") else ""
        cards.append(f'<a class="lcard" data-tone="teal" href="#drill.{_esc(d)}"><small>🎯 Decision drill{mins}</small>'
                     f'<b>{_esc(info.get("t", d))}</b></a>')
    for r in labs:
        info = catalog["labs"].get(r, {})
        mins = f" · {_esc(info['m'])} min" if info.get("m") else ""
        cards.append(f'<a class="lcard" data-tone="violet" href="#lab.{_esc(r)}"><small>🧪 Lab room{mins}</small>'
                     f'<b>{_esc(info.get("t", r))}</b></a>')
    for sid, deep in sites:
        s = catalog["sites"][sid]
        url = (s.get("deep") or {}).get(deep) if deep else None
        label = s["name"] + (f": {deep}" if url else "")
        # titles only on the billing warning: the strips repeat on every module page, so they stay lean
        badges = "".join(f'<span class="badge{cls}"' + (f' title="{_esc(tip)}"' if cls else "") + f'>{_esc(txt)}</span>'
                         for txt, cls, tip in site_badges(s))
        cards.append(f'<a class="lcard" data-tone="sky" href="{_esc(url or s["url"])}" target="_blank" rel="noopener">'
                     f'<small>↗ Outside practice</small><b>{_esc(label)}</b><span class="ps-b">{badges}</span></a>')
    shown = [t for t in topics if t in nodes_by_id][:STRIP_TOPICS]
    chips = "".join(f'<a class="chip" href="{_esc(map_href(t))}">🧭 {_esc(short_title(nodes_by_id[t].get("title", t)))}</a>'
                    for t in shown)
    more = len([t for t in topics if t in nodes_by_id]) - len(shown)
    if more > 0:
        chips += f'<a class="chip" href="{_esc(map_href(""))}">+{more} more on the map</a>'
    return (f'<aside class="prove-strip no-index" aria-label="Prove it">'
            '<p class="ps-head"><strong>🎯 Prove it</strong> You\'ve got it when you can fix it on a broken system. '
            'Easiest first; nothing is tracked, you decide.</p>'
            f'<div class="ps-grid">{"".join(cards)}</div>'
            + (f'<div class="ps-map"><span>Open in the map:</span>{chips}</div>' if chips else "")
            + "</aside>")


PROVE_CSS = r"""
/* ===== "Prove it" ladder (prove_site.py): 3D map panel + module strips ===== */
.mp-prove { list-style: none; padding-left: 0 !important; counter-reset: pv; }
.mp-prove > li { margin: 0; padding: 7px 0; border-bottom: 1px dashed var(--border); }
.mp-prove > li:last-child { border-bottom: 0; }
.pv-step { display: block; font-weight: 700; font-size: 13px; }
.pv-step::before { counter-increment: pv; content: counter(pv) " · "; color: var(--accent); }
.pv-step small { font-weight: 400; color: var(--fg-dim); }
.map-panel .pv-list { list-style: none; padding-left: 0; margin: 3px 0 0; }
.pv-list li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 7px; margin: 4px 0; }
.pv-list a { overflow-wrap: anywhere; }
.badge.badge-warn { color: var(--danger); border-color: var(--danger); }
.badge.badge-done { color: var(--accent2); border-color: var(--accent2); }
.prove-strip { margin: 30px 0 6px; padding: 14px 16px 12px; border-radius: 16px; background: var(--card);
  border: 1px solid color-mix(in srgb, var(--tone) 24%, var(--card-border)); }
.prove-strip .ps-head { margin: 0 0 10px; font-size: 14px; color: var(--fg-dim); }
.prove-strip .ps-head strong { color: var(--fg); margin-right: 4px; }
.ps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 10px; }
.ps-grid .lcard { padding: 10px 13px 11px; gap: 2px; border-radius: 13px; }
.ps-grid .lcard b { font-size: 14px; line-height: 1.35; overflow-wrap: anywhere; }
.ps-grid .lcard small { font-size: 11.5px; font-weight: 600; letter-spacing: .03em; color: var(--tone); }
.ps-b { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.ps-map { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 12px; font-size: 13px; color: var(--fg-dim); }
.ps-map .chip { color: var(--accent); }
.ps-map .chip:hover { border-color: var(--accent); text-decoration: none; }
"""
