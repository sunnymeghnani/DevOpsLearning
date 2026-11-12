"""Decision drills (drills/SPEC.md): schema and safety checks for every drill file, the page
generator (on tests/fixtures/drills/), and the built pages.

Every drills/*.json (files starting with "_" are drafts and are skipped) must pass the
"Constraints the tests enforce" of drills/SPEC.md. Run: python3 -m unittest tests.test_drills -v
"""
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import drills_site  # noqa: E402

DRILLS = ROOT / "drills"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "drills"
ROOMS = ROOT / "labs" / "rooms"
METERS = {"service", "time", "evidence", "trust"}
VERDICTS = {"best", "good", "risky", "bad"}
REQUIRED = ("id", "title", "level", "track", "topics", "minutes", "role", "source", "brief", "steps",
            "debrief", "practise")
MAX_FILE = 9 * 1024          # "every file is under 9 KB"
MAX_PLAYER = 28 * 1000       # "the player (CSS + JS) under 28 KB"
DOC_NETS = ((192, 0, 2), (198, 51, 100), (203, 0, 113))
GENERIC_USERS = {"root", "user", "ubuntu", "runner", "app", "build", "nobody", "ops", "deploy", "lab"}
SECRET_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key id
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),                       # GitHub tokens
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}"),                         # GitLab personal tokens
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),                     # Slack tokens
    re.compile(r"\bsk_live_[A-Za-z0-9]{16,}"),                         # Stripe live keys
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}"),     # JWTs
    re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\b[\"']?\s*[:=]\s*[\"']?"
               r"(?![<$*{(%]|x{3,}|example|changeme|redacted)[A-Za-z0-9+/_.-]{12,}"),
]


def drill_files(folder=DRILLS):
    return sorted(p for p in folder.glob("*.json") if not p.name.startswith("_")) if folder.is_dir() else []


def roadmap():
    return json.loads((ROOT / "roadmap.json").read_text(encoding="utf-8"))


def lab_ids():
    ids = set()
    for d in ROOMS.iterdir() if ROOMS.is_dir() else []:
        f = d / "room.json"
        if f.is_file():
            ids.add(d.name)
            ids.add(json.loads(f.read_text(encoding="utf-8")).get("id", d.name))
    return ids


def strings(obj):
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in strings(v)]
    return []


def is_date(s):
    try:
        datetime.date.fromisoformat(str(s))
        return re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s)) is not None
    except ValueError:
        return False


def bad_ipv4(text):
    """IPv4 addresses outside the documentation ranges (loopback, 0.0.0.0, link-local such as the
    cloud metadata address, and netmasks are not addresses of anyone's machine, so they pass)."""
    out = []
    for m in re.finditer(r"(?<![\d.])(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?![\d.]*\d)", text):
        o = tuple(int(x) for x in m.groups())
        if any(x > 255 for x in o):
            continue
        if o[:3] in DOC_NETS or o[0] in (0, 127, 255) or o[:2] == (169, 254):
            continue
        out.append(m.group(0))
    return out


def private_names():
    """The real username and home path of this machine (never generic ones such as root in a container)."""
    home = Path.home()
    names = {home.name} | {os.environ.get(k, "") for k in ("USER", "LOGNAME")}
    names = {n for n in names if len(n) >= 3 and n.lower() not in GENERIC_USERS}
    paths = {str(home)} if home.name.lower() not in GENERIC_USERS else set()
    return names, paths


def check_drill(path, tracks, nodes, labs):
    """List of problems with one drill file (empty if it passes)."""
    raw = path.read_bytes()
    errs = []
    if len(raw) >= MAX_FILE:
        errs.append(f"file is {len(raw)} bytes (must be under {MAX_FILE})")
    try:
        d = json.loads(raw.decode("utf-8"))
    except ValueError as e:
        return errs + [f"not valid JSON: {e}"]
    if not isinstance(d, dict):
        return errs + ["not a JSON object"]
    errs += [f"missing key {k!r}" for k in REQUIRED if k not in d]
    did = str(d.get("id", ""))
    if not drills_site.DRILL_ID_RE.match(did):
        errs.append(f"id {did!r} does not match {drills_site.DRILL_ID_RE.pattern}")
    if did != path.stem:
        errs.append(f"id {did!r} differs from the file name")
    for k in ("title", "role", "brief"):
        if not isinstance(d.get(k), str) or not d.get(k, "").strip():
            errs.append(f"{k} is empty")
    if d.get("level") not in {f"L{i}" for i in range(5)}:
        errs.append(f"level {d.get('level')!r} is not L0…L4")
    if d.get("track") not in tracks:
        errs.append(f"track {d.get('track')!r} is not a roadmap.json track")
    topics = d.get("topics")
    if not isinstance(topics, list) or not 1 <= len(topics) <= 4:
        errs.append("topics must list 1-4 roadmap node ids")
    else:
        errs += [f"topic {t!r} is not a roadmap.json node" for t in topics if t not in nodes]
    m = d.get("minutes")
    if isinstance(m, bool) or not isinstance(m, int) or not 3 <= m <= 15:
        errs.append(f"minutes {m!r} is not an integer 3-15")

    src = d.get("source") if isinstance(d.get("source"), dict) else {}
    if not str(src.get("url", "")).startswith("https://"):
        errs.append("source.url is not https")
    if not is_date(src.get("read_on")):
        errs.append(f"source.read_on {src.get('read_on')!r} is not a date (YYYY-MM-DD)")
    if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(src.get("date", ""))):
        errs.append(f"source.date {src.get('date')!r} is not a date")
    for k in ("label", "org"):
        if not str(src.get(k, "")).strip():
            errs.append(f"source.{k} is empty")

    steps = d.get("steps")
    if not isinstance(steps, list) or not 3 <= len(steps) <= 5:
        errs.append("steps: need 3-5 steps")
        steps = steps if isinstance(steps, list) else []
    for i, s in enumerate(steps, 1):
        if not isinstance(s, dict):
            errs.append(f"step {i} is not an object")
            continue
        if not str(s.get("situation", "")).strip():
            errs.append(f"step {i}: situation is empty")
        ch = s.get("choices")
        if not isinstance(ch, list) or not 3 <= len(ch) <= 4:
            errs.append(f"step {i}: need 3-4 choices")
            continue
        totals = []
        for j, c in enumerate(ch, 1):
            where = f"step {i} choice {j}"
            if not isinstance(c, dict):
                errs.append(f"{where} is not an object")
                totals.append(None)
                continue
            if c.get("verdict") not in VERDICTS:
                errs.append(f"{where}: verdict {c.get('verdict')!r} is not best|good|risky|bad")
            for k in ("text", "why"):
                if not str(c.get(k, "")).strip():
                    errs.append(f"{where}: {k} is empty")
            eff = c.get("effect")
            if not isinstance(eff, dict) or set(eff) != METERS:
                errs.append(f"{where}: effect keys must be exactly {sorted(METERS)}")
                totals.append(None)
                continue
            for k, v in eff.items():
                if isinstance(v, bool) or not isinstance(v, int) or not -30 <= v <= 30:
                    errs.append(f"{where}: effect.{k} = {v!r} is not an integer -30..30")
            totals.append(sum(v for v in eff.values() if isinstance(v, int)))
        best = [j for j, c in enumerate(ch) if isinstance(c, dict) and c.get("verdict") == "best"]
        if len(best) != 1:
            errs.append(f"step {i}: {len(best)} 'best' choices (need exactly one)")
        elif None not in totals:
            b = totals[best[0]]
            others = [t for j, t in enumerate(totals) if j != best[0]]
            if others and b <= max(others):
                errs.append(f"step {i}: the best choice totals {b}, not more than the others {others}")

    deb = d.get("debrief") if isinstance(d.get("debrief"), dict) else {}
    if not str(deb.get("what_happened", "")).strip():
        errs.append("debrief.what_happened is empty")
    if not isinstance(deb.get("lessons"), list) or not 2 <= len(deb["lessons"]) <= 4:
        errs.append("debrief.lessons: need 2-4 lessons")
    if not isinstance(deb.get("commands", []), list) or len(deb.get("commands", [])) > 6:
        errs.append("debrief.commands: at most 6 commands")

    pr = d.get("practise") if isinstance(d.get("practise"), dict) else {}
    for lab in pr.get("labs") or []:
        if lab not in labs:
            errs.append(f"practise.labs: {lab!r} is not a room in labs/rooms/")
    for h in pr.get("handbook") or []:
        f, head = str((h or {}).get("file", "")), str((h or {}).get("heading", ""))
        if not re.fullmatch(r"[\w.-]+\.md", f) or not (ROOT / f).is_file():
            errs.append(f"practise.handbook: module {f!r} does not exist")
        elif not drills_site.find_heading(str(ROOT), f, head):
            errs.append(f"practise.handbook: no heading {head!r} in {f}")
    for s in pr.get("sites") or []:
        if not str((s or {}).get("url", "")).startswith("https://") or not str((s or {}).get("label", "")).strip():
            errs.append(f"practise.sites: {s!r} needs a label and an https url")

    text = raw.decode("utf-8", "replace")
    names, paths = private_names()
    for p in paths:
        if p in text:
            errs.append("contains this machine's home path")
    for n in names:
        if re.search(rf"(?i)(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", text):
            errs.append("contains this machine's username")
    if re.search(r"/home/[^/\s\"]+/(?:external|programming)\b", text):
        errs.append("contains a real-looking home path")
    for ip in bad_ipv4(text):
        errs.append(f"IPv4 address {ip} is not in a documentation range (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24)")
    for s in strings(d):
        for rx in SECRET_RES:
            hit = rx.search(s)
            if hit:
                errs.append(f"secret-looking string: {hit.group(0)[:24]}…")
    return errs


class DrillFiles(unittest.TestCase):
    """drills/*.json: the writer's gate."""

    @classmethod
    def setUpClass(cls):
        rm = roadmap()
        cls.tracks = {t["id"] for t in rm["tracks"]}
        cls.nodes = {n["id"] for n in rm["nodes"]}
        cls.labs = lab_ids()

    def test_every_drill_passes_the_spec(self):
        files = drill_files()
        for f in files:
            with self.subTest(drill=f.name):
                self.assertEqual(check_drill(f, self.tracks, self.nodes, self.labs), [])

    def test_ids_unique_and_order_file_known(self):
        ids = [f.stem for f in drill_files()]
        self.assertEqual(len(ids), len(set(ids)))
        order = drills_site.read_order(str(DRILLS))
        self.assertEqual([x for x in order if x not in ids], [], "drills/ORDER lists ids without a drill file")
        self.assertEqual(len(order), len(set(order)), "drills/ORDER lists an id twice")

    def test_every_valid_file_is_loaded(self):
        """A file that passes the schema must also be picked up by the page generator."""
        loaded = {d["id"] for d in drills_site.load_drills(str(ROOT))}
        for f in drill_files():
            if not check_drill(f, self.tracks, self.nodes, self.labs):
                self.assertIn(f.stem, loaded)

    def test_fixtures_pass_the_same_checks(self):
        for f in drill_files(FIXTURES):
            with self.subTest(fixture=f.name):
                self.assertEqual(check_drill(f, self.tracks, self.nodes, self.labs), [])

    def test_checker_catches_bad_drills(self):
        """The gate itself: a broken copy of a fixture must fail on each rule."""
        import tempfile
        base = json.loads((FIXTURES / "fixture-full-log-volume.json").read_text(encoding="utf-8"))
        cases = {
            "level": lambda d: d.update(level="L5"),
            "track": lambda d: d.update(track="nope"),
            "topic": lambda d: d.update(topics=["no-such-node"]),
            "minutes": lambda d: d.update(minutes=30),
            "steps": lambda d: d.update(steps=d["steps"][:2]),
            "choices": lambda d: d["steps"][0].update(choices=d["steps"][0]["choices"][:2]),
            "two best": lambda d: d["steps"][1]["choices"][1].update(verdict="best"),
            "verdict": lambda d: d["steps"][0]["choices"][1].update(verdict="ok"),
            "why": lambda d: d["steps"][0]["choices"][1].update(why=""),
            "effect keys": lambda d: d["steps"][0]["choices"][0]["effect"].update(speed=1),
            "effect range": lambda d: d["steps"][0]["choices"][1]["effect"].update(trust=-40),
            "best not highest": lambda d: d["steps"][0]["choices"][3]["effect"].update(service=30),
            "http source": lambda d: d["source"].update(url="http://example.com/"),
            "read_on": lambda d: d["source"].update(read_on="last week"),
            "heading": lambda d: d["practise"]["handbook"].append({"file": "01-storage-disk.md", "heading": "No such heading here"}),
            "module": lambda d: d["practise"]["handbook"].append({"file": "99-nope.md", "heading": "x"}),
            "lab": lambda d: d["practise"]["labs"].append("99-no-such-room"),
            "ipv4": lambda d: d.update(brief=d["brief"] + " The host is 8.8.4.4."),
            "secret": lambda d: d.update(brief=d["brief"] + " AKIAABCDEFGHIJKLMNOP"),
            "size": lambda d: d.update(brief="x" * MAX_FILE),
        }
        names, paths = private_names()
        if names:
            cases["username"] = lambda d: d.update(role=d["role"] + " " + sorted(names)[0])
        with tempfile.TemporaryDirectory() as tmp:
            for name, mutate in cases.items():
                d = json.loads(json.dumps(base))
                mutate(d)
                p = Path(tmp) / (d["id"] + ".json")
                p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                with self.subTest(case=name):
                    self.assertNotEqual(check_drill(p, self.tracks, self.nodes, self.labs), [])

    def test_ipv4_rule(self):
        self.assertEqual(bad_ipv4("192.0.2.10 198.51.100.7 203.0.113.250 127.0.0.53 0.0.0.0 255.255.255.0 169.254.169.254"), [])
        self.assertEqual(bad_ipv4("10.0.0.5 and 8.8.8.8"), ["10.0.0.5", "8.8.8.8"])
        self.assertEqual(bad_ipv4("version 1.2.3.4.5 or 300.1.1.1"), [])


class Generator(unittest.TestCase):
    """drills_site.py on tests/fixtures/drills/."""

    @classmethod
    def setUpClass(cls):
        cls.md = drills_site.drills_markdown(str(ROOT), str(FIXTURES))
        m = re.search(r'<script type="application/json" id="drill-data">(.*?)</script>', cls.md, re.S)
        cls.raw_json = m.group(1) if m else ""
        cls.data = json.loads(cls.raw_json) if m else None

    def test_order_skip_and_count(self):
        ids = [d["id"] for d in drills_site.load_drills(str(ROOT), str(FIXTURES))]
        # L0 first; inside L1 the ORDER file wins; "_draft…" files are skipped
        self.assertEqual(ids, ["fixture-second-drill", "fixture-third-drill", "fixture-full-log-volume"])
        self.assertEqual(drills_site.drill_count(str(ROOT), str(FIXTURES)), 3)
        self.assertNotIn("draft-skipped", self.md)
        self.assertEqual([d["id"] for d in self.data], ids)

    def test_list_is_server_side_grouped_by_level(self):
        self.assertIn("## L0 · Fresher", self.md)
        self.assertIn("## L1 · Junior", self.md)
        self.assertLess(self.md.index("## L0 · Fresher"), self.md.index("## L1 · Junior"))
        for d in self.data:
            self.assertIn(f'<article class="drill-card" id="drill.{d["id"]}"', self.md)
            self.assertIn(f'<template data-drill="{d["id"]}">', self.md)
        card = re.search(r'<article class="drill-card" id="drill.fixture-full-log-volume".*?</article>', self.md, re.S).group(0)
        self.assertIn("<h3>Fixture: the log volume that filled up</h3>", card)
        self.assertIn('<div class="drill-brief"><p>The disk alert for <code>web1.example.com</code>', card)   # the brief, without JS
        self.assertIn('href="https://example.com/postmortems/log-volume?team=ops&amp;year=2026" target="_blank" rel="noopener"', card)
        self.assertIn("Example Ops 2026", card)
        self.assertIn('<span class="chip">Linux</span>', card)                     # the track by its roadmap name
        self.assertIn("⏱ 4 min", card)

    def test_data_is_embedded_once_and_safely(self):
        self.assertEqual(self.md.count('id="drill-data"'), 1)
        self.assertNotIn("<", self.raw_json)                     # no "</script", "<!--" or "<tag" for the HTML rewriters
        self.assertIn("\\u003c/p>", self.raw_json)
        # the brief's literal "</script>" stays text in the card
        self.assertIn("&lt;/script&gt;&lt;b&gt;not bold&lt;/b&gt; &amp; more", self.md)
        self.assertEqual(self.md.count("</script>"), 1)

    def test_steps_are_rendered_for_the_player(self):
        d = next(x for x in self.data if x["id"] == "fixture-full-log-volume")
        self.assertEqual(set(d), {"id", "steps"})              # title, brief and role come from the card
        self.assertEqual(len(d["steps"]), 3)
        s0 = d["steps"][0]
        self.assertEqual(s0["choices"][0]["effect"], [0, 5, 20, 5])          # service, time, evidence, trust
        self.assertEqual([c["verdict"] for c in s0["choices"]], ["best", "bad", "risky", "good"])
        self.assertEqual(s0["choices"][0]["text"], "Measure with <code>du</code> before deleting anything")
        # the evidence has its own "$ " line, so evidence_cmd is not repeated
        self.assertEqual(s0["evidence"].count("<u>$</u>"), 1)
        self.assertTrue(s0["evidence"].startswith("<u>$</u> <b>df -h /var</b>\n"))
        # evidence without a prompt line gets evidence_cmd as its first line
        self.assertTrue(d["steps"][1]["evidence"].startswith("<u>$</u> <b>ls -lh /var/log/app/</b>\n-rw-r"))
        self.assertEqual(d["steps"][2]["evidence"], "")
        # links to modules cannot be rewritten inside the JSON: they become plain text
        self.assertNotIn(".md", json.dumps(d))

    def test_debrief_template(self):
        tpl = re.search(r'<template data-drill="fixture-full-log-volume">.*?</template>', self.md, re.S).group(0)
        self.assertIn("<h4>What really happened</h4>", tpl)
        self.assertIn("(Example Ops, 15 January 2026) · read on 2026-11-07", tpl)
        self.assertIn('href="01-storage-disk.md#deleted-but-open-files-classic-trap"', tpl)
        self.assertIn('href="01-storage-disk.md#df-filesystem-free-space"', tpl)
        self.assertIn('href="01-storage-disk.md"', tpl)                       # the module link in what_happened
        self.assertIn('<a class="drill-lab" data-lab="l0-text-tools">', tpl)   # the script adds href="#lab.<id>"
        self.assertNotIn('href="#lab.', tpl)
        self.assertIn('href="https://sadservers.com/scenarios" target="_blank" rel="noopener"', tpl)
        self.assertRegex(tpl, r'<code>df -h /var</code> <a class="drill-dec" href="#cmd-[a-z0-9-]+">')
        for h in ("Lessons", "Commands", "Practise this"):
            self.assertIn(f"<h4>{h}</h4>", tpl)
        self.assertNotIn(" id=", tpl)                                         # templates add no ids to the page

    def test_handbook_links_resolve_through_build_site(self):
        """The same pipeline as the real build: drills.md + a module, then rewrite_links."""
        import build_site
        orig = build_site.drills_markdown
        build_site.drills_markdown = lambda here: drills_site.drills_markdown(here, str(FIXTURES))
        try:
            mods = [build_site.render_module(f, t, i, g) for f, t, i, g in build_site.MODULES
                    if f in (drills_site.DRILLS_FILE, "01-storage-disk.md")]
        finally:
            build_site.drills_markdown = orig
        by_file = {m["file"]: m for m in mods}
        missing = {}
        for m in mods:
            build_site.rewrite_links(m, by_file, set(by_file), missing)
        body, disk = by_file[drills_site.DRILLS_FILE]["body"], by_file["01-storage-disk.md"]
        self.assertEqual({k: v for k, v in missing.items() if k[0] == drills_site.DRILLS_FILE}, {})
        tpl = re.search(r'<template data-drill="fixture-full-log-volume">.*?</template>', body, re.S).group(0)
        links = re.findall(r'href="#(m01[^"]*)"', tpl)
        self.assertIn("m01-deleted-but-open-files-classic-trap", links)
        self.assertIn("m01-df-filesystem-free-space", links)
        for a in links:
            self.assertTrue(a == "m01" or a in disk["ids"], a)
        self.assertIn('<div class="drill-grid">', body)
        self.assertIn("drill-data", body)
        json.loads(re.search(r'id="drill-data">(.*?)</script>', body, re.S).group(1))   # markdown left it intact

    def test_dates(self):
        self.assertEqual(drills_site._date("2017-01-31"), "31 January 2017")
        self.assertEqual(drills_site._date("2017"), "2017")


class Player(unittest.TestCase):
    """DRILLS_CSS + DRILLS_SCRIPT: size, syntax and the SPEC's page rules."""

    @classmethod
    def setUpClass(cls):
        cls.js = re.fullmatch(r"<script>(.*)</script>", drills_site.DRILLS_SCRIPT, re.S).group(1)
        cls.css = drills_site.DRILLS_CSS

    def test_size_budget(self):
        size = len(self.css.encode("utf-8")) + len(drills_site.DRILLS_SCRIPT.encode("utf-8"))
        self.assertLess(size, MAX_PLAYER, f"player is {size} bytes")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_script_parses(self):
        r = subprocess.run(["node", "--check"], input=self.js, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_external_requests_or_dialogs(self):
        for bad in ("alert(", "confirm(", "prompt(", "fetch(", "XMLHttpRequest", "http://", "https://", "import(", "eval("):
            self.assertNotIn(bad, self.js)
        for bad in ("url(http", "@import", "https://", "http://"):
            self.assertNotIn(bad, self.css)

    def test_storage_is_guarded(self):
        lines = self.js.split("\n")
        uses = [i for i, ln in enumerate(lines) if "localStorage" in ln]
        self.assertTrue(uses)
        for i in uses:
            self.assertTrue(any("try {" in lines[j] for j in range(max(0, i - 3), i + 1)), lines[i])

    def test_spec_behaviour_is_wired(self):
        js = self.js
        self.assertIn('getElementById("drill-data")', js)
        self.assertIn("[50, 50, 50, 50]", js)                                  # meters start at 50
        self.assertIn("Math.max(0, Math.min(100,", js)                         # and are clamped
        self.assertIn("S.m[0] <= 0 || S.m[3] <= 0", js)                        # Service or Trust at 0 ends early
        self.assertIn("The incident escalated past you", js)
        self.assertIn("Why not the others?", js)
        self.assertIn("What happened?", js)
        self.assertIn('data-act="next" data-enter disabled', js)               # Next is gated
        self.assertIn("#drill\\.", js)                                          # deep links
        self.assertIn('"#lab." +', js)
        self.assertIn("prefers-reduced-motion", js)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn("Play again", js)
        self.assertIn("Next drill:", js)
        self.assertRegex(js, r"/\^\[1-4\]\$/")                                  # keys 1-4
        self.assertIn('e.key === "Enter"', js)

    def test_qa_fixes_2026_11_07(self):
        js, css = self.js, self.css
        # a double-click on Start / Next / Play again must not also pick a move on the screen that replaces it
        self.assertIn("e.detail > 1", js)
        # opening from a card pushes a history entry, so browser Back closes the drill instead of leaving the page;
        # closing pops that entry again (switching drills replaces it)
        self.assertIn('history.pushState({ drill: 1 }, "", "#drill." + id)', js)
        self.assertIn("history.state && history.state.drill) { S.land = land; return history.back(); }", js)
        self.assertIn("else if (l) l(1);", js)     # after the pop: back to the card and its Play button
        # aria-modal dialog: Tab and Shift+Tab wrap inside the view instead of reaching the page behind it
        self.assertIn('e.key === "Tab"', js)
        self.assertRegex(js, r"e\.shiftKey \? a === f\[0\] \|\| a === S\.view : a === f\[f\.length - 1\]")
        # desktop only (user, 10 Nov 2026): the 360 px phone rules (title clamp, 2x2 meters) are gone;
        # the title is checked at 1024 and 1366 px in the browser QA instead
        self.assertNotRegex(css, r"@media \(max-width:\s*(?:360|520|560|640)px\)")

    def test_qa2_back_lands_and_end_screen_survives(self):
        js = self.js
        # browser Back with a drill open (close(2)) lands on the card it was opened from, not the list top
        self.assertIn("else if (S.view && !S.view.hidden) close(2);", js)
        self.assertIn("if (keep) { if (keep > 1 && oc) land(1); return; }", js)
        # following a link out of the debrief keeps the end screen in that history entry, and Back restores it
        self.assertIn('history.replaceState({ drill: st && st.drill, end: en ?', js)
        self.assertIn("var e = fromHash && history.state && history.state.end;", js)
        self.assertIn("if (e && e.id === id) {", js)

    def test_uses_the_handbook_tokens(self):
        for tok in ("var(--card)", "var(--card-border)", "var(--term-bg)", "var(--accent2)", "var(--danger)",
                    "var(--t-teal)", "var(--t-amber)", "var(--fg-dim)"):
            self.assertIn(tok, self.css)
        # no colours of its own: the only literal colours are the terminal frame's three window dots
        self.assertEqual(set(re.findall(r"#[0-9a-fA-F]{6}\b", self.css)), {"#ff5f57", "#febc2e", "#28c840"})
        self.assertNotRegex(self.css, r"\brgba?\(")


class BuiltPages(unittest.TestCase):
    """index.html and artifact.html (run python3 build_site.py first)."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for n in ("index.html", "artifact.html"):
            p = ROOT / n
            if p.is_file():
                cls.pages[n] = p.read_text(encoding="utf-8")
        if not cls.pages:
            raise unittest.SkipTest("the pages are not built")
        cls.ids = [d["id"] for d in drills_site.load_drills(str(ROOT))]

    @staticmethod
    def section(page):
        start = page.index('id="m-drills"')
        end = page.find("<section", start + 1)
        return page[start:end if end > 0 else None]

    def test_wired_like_the_labs(self):
        import build_site
        self.assertIn(("drills.md", "Decision drills", "🎯", "Labs"), build_site.MODULES)
        self.assertIn(drills_site.DRILLS_FILE, build_site.GENERATED_FILES)
        self.assertTrue(any(f == drills_site.DRILLS_FILE for f, *_ in build_site.HOME_LINKS))
        for name, page in self.pages.items():
            self.assertTrue(drills_site.DRILLS_CSS in page, name)
            self.assertTrue(drills_site.DRILLS_SCRIPT in page, name)
            self.assertEqual(page.count('id="drill-data"'), 1, name)
            self.assertTrue('href="#m-drills"' in page, name)                    # launchpad card and sidebar
            self.assertTrue(f"🎯 {len(self.ids)} drill" in page, name)
            self.assertTrue('id="map-canvas"' in page, name)                     # the 3D map is still there

    def test_every_drill_is_on_the_page(self):
        for name, page in self.pages.items():
            sec = self.section(page)
            data = json.loads(re.search(r'id="drill-data">(.*?)</script>', sec, re.S).group(1))
            self.assertEqual([d["id"] for d in data], self.ids, name)
            for did in self.ids:
                self.assertTrue(f'id="drill.{did}"' in sec, (name, did))
                self.assertTrue(f'<template data-drill="{did}">' in sec, (name, did))

    def test_debrief_links_resolve_to_headings(self):
        for name, page in self.pages.items():
            ids = set(re.findall(r'\sid="([^"]+)"', page))
            sections = set(re.findall(r'<section class="mod-section" id="([^"]+)"', page))
            sec = self.section(page)
            for did in self.ids:
                tpl = re.search(rf'<template data-drill="{re.escape(did)}">.*?</template>', sec, re.S).group(0)
                self.assertNotRegex(tpl, r'href="[\w.-]+\.md', (name, did))
                for a, head in re.findall(r'href="#([^"]+)" data-heading="([^"]*)"', tpl):
                    self.assertIn(a, ids, (name, did, head))
                    self.assertNotIn(a, sections, (name, did, f"{head!r} fell back to the module top"))
                for a in re.findall(r'class="drill-dec" href="#([^"]+)"', tpl):
                    self.assertIn(a, ids, (name, did))

    def test_nothing_private_in_the_drills_section(self):
        names, paths = private_names()
        for name, page in self.pages.items():
            sec = html.unescape(self.section(page))
            for p in paths:
                self.assertFalse(p in sec, name)
            for n in names:
                self.assertIsNone(re.search(rf"(?i)(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", sec), name)

    def test_page_size(self):
        self.assertLess(len(self.pages.get("index.html", "").encode("utf-8")), 15_950_000)

    def test_read_time_counts_only_visible_text(self):
        # the hero estimate must not count the embedded drill JSON and debrief templates (was "≈ 63 min read"
        # with 12 drills). The visible drill cards are about 100 words each: 36 drills read in about 16 min,
        # while counting the JSON would give about 190 min. So: equal to the visible-text estimate, and small.
        for name, page in self.pages.items():
            sec = self.section(page)
            hero = re.search(r'<header class="mod-hero.*?</header>', sec, re.S).group(0)
            mins = int(re.search(r"≈ (\d+) min read", hero).group(1))
            visible = re.sub(r"<(script|style|template)\b[^>]*>.*?</\1\s*>", " ", sec.replace(hero, ""), flags=re.S | re.I)
            words = len(re.findall(r"\w+", html.unescape(re.sub(r"<[^>]+>", " ", visible))))
            self.assertLessEqual(abs(mins - round(words / 230)), 1, name)
            self.assertLess(mins, 30, name)


class DrillFacts(unittest.TestCase):
    """Technical statements QA found wrong (2026-11-07); keep them from coming back."""

    def test_nada_drill(self):
        d = json.loads((DRILLS / "nada-2024-inodes-sessions.json").read_text(encoding="utf-8"))
        text = json.dumps(d, ensure_ascii=False)
        # growing ext4 adds inodes in proportion (new block groups bring inode tables); only the ratio is fixed
        self.assertNotIn("inode count is fixed", text)
        # find -mtime +1 matches files at least two full days old, not "older than a day"
        for st in d["steps"]:
            for c in st["choices"]:
                if "-mtime +1" in c["text"]:
                    self.assertNotIn("older than a day", c["text"])
                    self.assertIn("two full days", c["why"])


if __name__ == "__main__":
    unittest.main()
