"""The "Prove it" practice ladder (prove_site.py): curated sites per roadmap topic, the computed drill
and lab links, the 3D map panel code and the end-of-module strips in the built pages.

Run after building: python3 -m unittest tests.test_prove -v
"""
import json
import re
import shutil
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import prove_site  # noqa: E402
from drills_site import load_drills  # noqa: E402
from labs_site import load_rooms  # noqa: E402

PAGES = ("index.html", "artifact.html")
SIZE_LIMIT = 15_950_000          # index.html budget (raised 9 Nov 2026; the artifact page limit is 16 MB)
SITE_FIELDS = {"name", "url", "cost", "signup", "runs", "checked_on", "deep"}
PANEL_TITLE = "Prove it: you've got it when you can do this on a broken system"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Page(HTMLParser):
    """ids, <script> bodies by type, and every <a> inside a .prove-strip."""

    def __init__(self, text):
        super().__init__()
        self.ids, self.scripts, self.strips, self.hrefs = set(), [], [], []
        self._script = None
        self._depth = 0          # > 0 while inside a prove-strip <aside>
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if a.get("href"):
            self.hrefs.append(a["href"])
        if tag == "script":
            self._script = [a.get("type", ""), a.get("id", ""), ""]
        if tag == "aside" and "prove-strip" in a.get("class", "").split():
            self.strips.append({"links": [], "cards": 0})
            self._depth = 1
        elif tag == "aside" and self._depth:
            self._depth += 1
        if self._depth and tag == "a":
            self.strips[-1]["links"].append(a)
            if "lcard" in a.get("class", "").split():
                self.strips[-1]["cards"] += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append(tuple(self._script))
            self._script = None
        if tag == "aside" and self._depth:
            self._depth -= 1

    def handle_data(self, data):
        if self._script is not None:
            self._script[2] += data


class Curation(unittest.TestCase):
    """roadmap.json prove_sites against research/practice.json."""

    @classmethod
    def setUpClass(cls):
        cls.roadmap = load("roadmap.json")
        cls.practice = load("research/practice.json")
        cls.sites = {s["id"]: s for s in cls.practice["sites"]}
        cls.blocked = {r.get("id") for g in ("sites", "dead_or_renamed", "paid_only", "excluded_after_research")
                       for r in cls.practice.get(g, []) if isinstance(r, dict) and r.get("do_not_link")}

    def test_every_node_has_the_field(self):
        for n in self.roadmap["nodes"]:
            self.assertIsInstance(n.get("prove_sites"), list, n["id"])

    def test_ids_exist_are_ok_and_linkable(self):
        for n in self.roadmap["nodes"]:
            with self.subTest(node=n["id"]):
                refs = [prove_site.site_ref(r) for r in n["prove_sites"]]
                self.assertLessEqual(len(refs), 3)
                ids = [sid for sid, _ in refs]
                self.assertEqual(len(ids), len(set(ids)), "a site is listed twice")
                for sid, deep in refs:
                    self.assertIn(sid, self.sites, f"{sid} is not in practice.json sites")
                    self.assertEqual(self.sites[sid]["status"], "ok", sid)
                    self.assertNotIn(sid, self.blocked)
                    self.assertFalse(self.sites[sid].get("do_not_link"), sid)
                    if deep is not None:
                        labels = [d["label"] for d in self.sites[sid].get("deep_links", [])]
                        self.assertIn(deep, labels, f"{sid}: no deep link labelled {deep!r}")
                for r in n["prove_sites"]:
                    if isinstance(r, dict):
                        self.assertLessEqual(set(r), {"id", "deep"}, n["id"])

    def test_safety_order(self):
        """Own-cloud sites only on cloud topics and never alone; paid-only sites are not used."""
        for n in self.roadmap["nodes"]:
            runs = [self.sites[prove_site.site_ref(r)[0]]["runs"] for r in n["prove_sites"]]
            costs = [self.sites[prove_site.site_ref(r)[0]]["cost"] for r in n["prove_sites"]]
            with self.subTest(node=n["id"]):
                if "own-cloud-account" in runs:
                    self.assertTrue(n["track"] == "cloud" or n.get("env") == "cloud", "own-cloud site on a non-cloud topic")
                    self.assertTrue(any(r != "own-cloud-account" for r in runs), "own-cloud site is the only option")
                self.assertNotIn("paid", costs)

    def test_deep_links_are_unique_web_urls(self):
        for s in self.practice["sites"]:
            labels = [d["label"] for d in s.get("deep_links", [])]
            self.assertEqual(len(labels), len(set(labels)), s["id"])
            for d in s.get("deep_links", []):
                self.assertRegex(d["url"], r"^https?://[^\s]+$", s["id"])

    def test_qa4_dead_links_are_replaced(self):
        """QA4 (10 Nov 2026): these returned 404; the replacements returned 200 with the matching title."""
        dead = ("notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Introduction-to-Deployment-with-kubeadm/page",
                "notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Install-Kubernetes-the-kubeadm-way/Solution-Install-a-Kubernetes-Cluster-using-kubeadm/page",
                "docs.gunicorn.org/en/stable/deploy.html")
        texts = {p.name: p.read_text(encoding="utf-8") for p in [ROOT / "roadmap.json", *sorted(ROOT.glob("[0-9][0-9]-*.md"))]}
        for name, text in texts.items():
            for url in dead:
                self.assertNotIn(url, text, f"{name}: {url}")
        study = [it.get("url", "") for n in self.roadmap["nodes"] for it in n.get("study", [])]
        self.assertIn("https://gunicorn.org/deploy/", study)
        self.assertIn("https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Deployment-With-kubeadm-Introduction/page", study)
        # the iximiuz "crashed container" challenge is really a Kubernetes pod challenge: relabelled, and the
        # Docker incidents topic links a Docker one instead
        ix = [d["label"] for d in self.sites["iximiuz-labs"]["deep_links"]]
        self.assertIn("Debug a restarting pod from its previous logs (Kubernetes)", ix)
        self.assertNotIn("Capture a crashed container's logs and fix it", ix)
        node = next(n for n in self.roadmap["nodes"] if n["id"] == "container-incidents")
        self.assertIn({"id": "iximiuz-labs", "deep": "Connect a container to a host service"}, node["prove_sites"])
        # the Vault-tutorial ACME scenario on Killercoda is written in Chinese: the label says so
        kc = {d["url"]: d["label"] for d in self.sites["killercoda"]["deep_links"]}
        self.assertTrue(kc["https://killercoda.com/vault-tutorial/course/vault-tutorial/ch9-acme-caddy"].endswith("(in Chinese)"))

    def test_no_unixgame_in_sources(self):
        self.assertNotIn("unixgame", (ROOT / "roadmap.json").read_text(encoding="utf-8").lower())
        blocked = [r for r in self.practice["dead_or_renamed"] if r.get("id") == "unixgame"]
        self.assertTrue(blocked and blocked[0].get("do_not_link"))
        self.assertNotIn("unixgame", self.sites)


class Computed(unittest.TestCase):
    """Drill and lab links come from drills/*.json topics and labs/rooms/*/room.json map_node."""

    @classmethod
    def setUpClass(cls):
        cls.roadmap = load("roadmap.json")
        cls.warnings = []
        cls.catalog = prove_site.topic_ladders(cls.roadmap, str(ROOT), cls.warnings.append)
        cls.drill_ids = {json.loads(p.read_text(encoding="utf-8"))["id"] for p in (ROOT / "drills").glob("*.json")
                         if not p.name.startswith("_")}
        cls.room_ids = {json.loads(p.read_text(encoding="utf-8"))["id"] for p in (ROOT / "labs" / "rooms").glob("*/room.json")}

    def test_resolves_without_warnings(self):
        self.assertEqual(self.warnings, [])

    def test_links_point_at_real_drills_and_rooms(self):
        drills = {d["id"]: d for d in load_drills(str(ROOT))}
        rooms = {r["id"]: r for r in load_rooms(str(ROOT))}
        n_d = n_l = 0
        for n in self.roadmap["nodes"]:
            p = n.get("prove") or {}
            for d in p.get("d", []):
                n_d += 1
                self.assertIn(d, self.drill_ids)
                self.assertIn(n["id"], drills[d]["topics"])
            for r in p.get("l", []):
                n_l += 1
                self.assertIn(r, self.room_ids)
                self.assertEqual(rooms[r]["map_node"], n["id"])
        # every drill topic and every room's map_node shows up on its topic
        self.assertEqual(n_d, sum(len(d["topics"]) for d in drills.values()))
        self.assertEqual(n_l, len(rooms))

    def test_catalog_is_minimal(self):
        used = {prove_site.site_ref(r)[0] for n in self.roadmap["nodes"] for r in (n.get("prove") or {}).get("s", [])}
        self.assertEqual(set(self.catalog["sites"]), used)
        for sid, s in self.catalog["sites"].items():
            self.assertLessEqual(set(s), SITE_FIELDS, sid)
        self.assertNotIn("path", self.catalog)   # test_source_integration treats a 'path' key as the roadmap


class BuiltPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {name: (ROOT / name).read_text(encoding="utf-8") for name in PAGES}
        cls.pages = {name: Page(t) for name, t in cls.text.items()}
        cls.nodes = {n["id"]: n for n in load("roadmap.json")["nodes"]}

    def json_script(self, name, sid):
        found = [body for typ, i, body in self.pages[name].scripts if typ == "application/json" and i == sid]
        self.assertEqual(len(found), 1, f"{name}: #{sid}")
        return json.loads(found[0])

    def test_prove_data_is_embedded_once_and_compact(self):
        for name, text in self.text.items():
            with self.subTest(page=name):
                self.assertEqual(text.count('id="prove-data"'), 1)
                data = self.json_script(name, "prove-data")
                self.assertNotIn("path", data)
                self.assertEqual(set(data), {"sites", "drills", "labs"})
                for sid, s in data["sites"].items():
                    self.assertLessEqual(set(s), SITE_FIELDS, sid)
                body = re.search(r'id="prove-data">(.*?)</script>', text, re.S).group(1)
                self.assertNotIn("</", body)
                self.assertNotIn("<", body)

    def test_panel_targets_exist(self):
        for name in PAGES:
            with self.subTest(page=name):
                data, ids = self.json_script(name, "prove-data"), self.pages[name].ids
                graph = self.json_script(name, "roadmap-data")
                with_ladder = 0
                for n in graph["nodes"]:
                    self.assertNotIn("prove_sites", n)    # replaced by the resolved "prove"
                    p = n.get("prove")
                    if not p:
                        continue
                    with_ladder += 1
                    for d in p.get("d", []):
                        self.assertIn("drill." + d, ids)
                        self.assertIn(d, data["drills"])
                    for r in p.get("l", []):
                        self.assertIn("lab." + r, ids)
                        self.assertIn(r, data["labs"])
                    for ref in p.get("s", []):
                        sid, deep = prove_site.site_ref(ref)
                        self.assertIn(sid, data["sites"])
                        if deep:
                            self.assertTrue(data["sites"][sid]["deep"][deep].startswith(("https://", "http://")))
                self.assertGreater(with_ladder, 100)

    def map_script(self, name):
        found = [body for typ, _, body in self.pages[name].scripts if typ != "application/json" and "function proveSection" in body]
        self.assertEqual(len(found), 1)
        return found[0]

    def test_panel_code_is_in_the_map_script(self):
        for name in PAGES:
            js = self.map_script(name)
            for needle in (PANEL_TITLE, "kids.push(...proveSection(n))", '"drills.best"', "closeMap({ keepHistory: true })",
                           'target: "_blank", rel: "noopener noreferrer"', "can bill YOUR cloud account", "✓ played"):
                self.assertIn(needle, js, f"{name}: {needle}")
            # QA3: re-opening the map redraws the still-selected panel ("✓ played" after a drill), and a
            # deselect while the map is closed (top-bar env switch) leaves the address alone
            for needle in ("renderPanel(G.byId[S.selected]); panel.scrollTop = y;", 'if (S.open) setHash("#map");'):
                self.assertIn(needle, js, f"{name}: {needle}")
            # learning order (user, 9 Nov 2026): prerequisites → study path → commands → exit check →
            # prove it → related playbooks → next step
            order = ['section("Prerequisites"', 'section("Study path (in this order)"', 'section("Key commands"',
                     "Exit check — you've got it when", "kids.push(...proveSection(n))",
                     'section("Related playbooks & notes"', 'section("Next step →"']
            pos = [js.index(x) for x in order]
            self.assertEqual(pos, sorted(pos), f"{name}: panel sections out of order")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_map_script_parses(self):
        r = subprocess.run(["node", "--check"], input=self.map_script("index.html"), text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_module_strips_resolve(self):
        urls = set()
        for s in load("research/practice.json")["sites"]:
            if s["status"] == "ok":
                urls.add(s["url"])
                urls.update(d["url"] for d in s.get("deep_links", []))
        for name in PAGES:
            page = self.pages[name]
            with self.subTest(page=name):
                self.assertGreater(len(page.strips), 30)
                for strip in page.strips:
                    self.assertGreater(strip["cards"], 0)
                    self.assertLessEqual(strip["cards"], prove_site.STRIP_MAX)
                    for a in strip["links"]:
                        href = a.get("href", "")
                        if href.startswith(("https://", "http://")):
                            self.assertIn(href, urls)
                            self.assertEqual(a.get("target"), "_blank")
                            self.assertIn("noopener", a.get("rel", "").split())
                        elif href == "#map":
                            continue
                        elif href.startswith("#map."):
                            self.assertIn(href[5:], self.nodes)
                        else:
                            self.assertTrue(href.startswith("#") and href[1:] in page.ids, f"{name}: {href}")

    def test_strip_drills_and_labs_open_in_place(self):
        """QA3: a strip's drill/lab card opens without the native jump to the drills/labs page, and closing
        lands back on the strip, so Back and Close return the reader to the module they were reading."""
        for name, text in self.text.items():
            with self.subTest(page=name):
                self.assertIn(""".closest(".prove-strip a[href^='#drill.'],.prove-strip a[href^='#lab.']")""", text)
                self.assertIn('o.closest(".drill-card, .prove-strip")', text)
                self.assertIn('o.closest(".lab-card, .prove-strip")', text)
                # the open-room flag on <html> must not reuse the "Read the room" button class (.lab-open):
                # html.lab-open picked up the button styles and every click set the room's opener to <html>
                self.assertIn('root.classList.add("lab-on")', text)
                self.assertNotIn('classList.add("lab-open")', text)

    def test_warning_badges_beat_the_plain_badge_rule(self):
        """QA3: the page's later `.badge` rule overrode `.badge-warn`/`.badge-done`, so the billing warning and
        "✓ played" looked like any other badge; two-class selectors win regardless of order."""
        for name, text in self.text.items():
            with self.subTest(page=name):
                self.assertIn(".badge.badge-warn { color: var(--danger)", text)
                self.assertIn(".badge.badge-done { color: var(--accent2)", text)

    def test_strips_sit_at_the_end_of_their_module(self):
        text = self.text["index.html"]
        for m in re.finditer(r'<aside class="prove-strip', text):
            tail = text[m.start():text.index("</section>", m.start())]
            self.assertEqual(tail.count("<aside"), 1, "strip is not the last thing in its module")

    def test_no_unixgame_link_anywhere(self):
        """Module 54 names unixgame.io only as a warning in plain text; nothing may link to it."""
        for name, page in self.pages.items():
            with self.subTest(page=name):
                self.assertFalse([h for h in page.hrefs if "unixgame" in h.lower()])
                for sid in ("prove-data", "roadmap-data"):
                    self.assertNotIn("unixgame", json.dumps(self.json_script(name, sid)).lower())
                self.assertIsNone(re.search(r"""(?:href|src)\s*=\s*["'][^"']*unixgame""", self.text[name], re.I))

    def test_size_limit(self):
        size = (ROOT / "index.html").stat().st_size
        self.assertLess(size, SIZE_LIMIT, f"index.html is {size} bytes")


if __name__ == "__main__":
    unittest.main()
