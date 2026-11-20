"""Focused topic reading and learning-mode locks (focus_site.py): a handbook item opened from a map
topic shows only that section, with a bar (Previous / Next / Show whole module / Back to topic) and an
end card; "Show whole module" locks sections of topics whose prerequisites are not done; the sidebar
and search stay unlocked reference reading.

Run after building: python3 -m unittest tests.test_focus -v
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import backnav_site  # noqa: E402
import focus_site  # noqa: E402

PAGES = ("index.html", "artifact.html")
SIZE_LIMIT = 15_950_000
BUDGET = 22_000          # bytes of focus CSS + script in the page


def roadmap_of(text):
    m = re.search(r'<script type="application/json" id="roadmap-data">(.*?)</script>', text, re.S)
    return json.loads(m.group(1))


class Focus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {n: (ROOT / n).read_text(encoding="utf-8") for n in PAGES}
        cls.src = (ROOT / "build_site.py").read_text(encoding="utf-8")
        cls.js = focus_site.FOCUS_SCRIPT
        cls.rm = roadmap_of(cls.text["index.html"])

    def test_pages_carry_css_and_script_once(self):
        for name, t in self.text.items():
            with self.subTest(page=name):
                self.assertEqual(t.count(self.js), 1)
                self.assertIn(focus_site.FOCUS_CSS, t)
                # after the map (it reads window.__map), before backnav (its click handler must run first)
                self.assertLess(t.index('<script id="map-ui">'), t.index(self.js))
                self.assertLess(t.index(self.js), t.index(backnav_site.BACKNAV_SCRIPT))

    def test_strings_and_behaviour_hooks(self):
        js = self.js
        for needle in ('"📘 Reading for: "', '" · section "', '" of "', '"‹ Previous"', '"Next ›"', '"Show whole module"',
                       '"← Back to topic"', '"End of this section"', '"Next section for this topic: "', '"✓ Mark ‘"',
                       '"Next topic: "', '"🔒 Part of topic "', '". Unlocks when you finish: "', '"Open anyway"',
                       '"✕ Leave learning mode"', '"aria-label": "Focused reading"', '"aria-live": "polite"',
                       '"#read."', '".module"', "M.toggleDone(t)", "roadmap-done", "B.jump(el, hash, from)",
                       "s.bo.m === t", "H.back()", "#sidebar a,#sidebar button", '"popstate"', '"hashchange"',
                       "data-fx-off", "handbook-layout", "W.__focus = {"):
            self.assertIn(needle, js, needle)
        self.assertEqual(js.count("pushState"), 1)            # only the no-backnav fallback; backnav pushes the entry
        css = focus_site.FOCUS_CSS
        for needle in ("[data-fx-off]{display:none !important}", "position:sticky", "var(--tb-total)", ".fx-on .backnav",
                       "@media print", ":focus-visible"):
            self.assertIn(needle, css, needle)
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,6}\b")        # theme tokens only: both themes

    def test_qa_fixes(self):
        """Regressions found in QA: each needle guards one fix."""
        js = self.js
        for needle in ("cur.pre.has(id)",                      # the reading topic's own prerequisites never lock
                       't.matches(".mod-btn")',                # folding a module in the sidebar tree stays in focus
                       'exit(t.tagName === "A")',              # a sidebar link keeps "#read…" behind it: Back returns
                       'a.classList.contains("skip-link")',    # the skip link does not end focused reading
                       "if (b && !b.disabled) b.focus(",       # Enter, Enter on Next never turns into Previous
                       "if (S.open) stale = 1",                # locks recompute after the map closes, spot kept
                       "if (r.top > line) break"):             # keep() anchors on the block under the reading line
            self.assertIn(needle, js, needle)

    def test_followups(self):
        """QA follow-ups (15 Nov 2026): whole module = that module only, ending in Next module / Back to topic;
        area-wide source sections leave the sequence for an end-card link; nested sections show once; a moved
        anchor opens the topic's first section with a note; locked sections do not print."""
        js, css = self.js, focus_site.FOCUS_CSS
        for needle in ('if (c !== cur.mod && c !== bar) hide(c, "f", hid)',   # whole module hides every other module
                       '"End of module “"', "go(cur.i, true, nm)",
                       '" locked"',                                          # the next module's locks, counted
                       "!it.area && !seen[it.anchor]",                       # area sections are not in the sequence
                       "var a = it && !it.area && it.anchor",                # ... and never lock
                       '"Related incidents in this area"', '".source-entry"',
                       "y !== x && within(y.r, x.el)",                       # a section inside a listed one is dropped
                       "if (within(L[i].r, el)) return i",                   # ... and its anchor opens the outer one
                       '"That section moved, starting at the beginning of this topic"', "moved: i < 0",
                       "if (p.moved || p.named && !cur.alt) rs(url())",      # the URL is corrected (also a stale module id)
                       '".module" + (mid ? "." + mid : "")',                 # #read.T.A.module.MODULE
                       "M.cmdList(n)", '"⌨️ Key commands for this topic ("'):
            self.assertIn(needle, js, needle)
        self.assertNotIn('[data-fx-off="l"]', css)            # print no longer reveals locked sections
        # QA7 (15 Nov 2026): Next module lands on the module's hero (its h1 has no id, so no scroll margin: it sat
        # behind the top bar); "#read.T.INNER" scrolls to the nested anchor, and open() puts it in the URL; the key
        # commands box stays open when the end card is drawn again (Back from a Decode link)
        for needle in ('cur.alt ? (f && cur.mod.querySelector("h1")) || cur.mod : cur.at || cur.L[cur.i].el', "focusEl(spot(1))",
                       "at: i >= 0 && L[i].a !== a ? a : null", "apply(t, i, false, null, false, a);", "hash = enc(t, a);",
                       "open: !!kcOpen[t]", "kcOpen[t] = kc.open",
                       # an "Open anyway" no longer leaks into another topic's locks (the count changed on reload)
                       "if (openedFor !== t) { opened.clear(); openedFor = t; }"):
            self.assertIn(needle, js, needle)
        self.assertIn("[data-fx-off]{display:none !important}", css)
        self.assertIn(r"RX = /^#read\.([^.]+)\.([^.]+)(\.module(?:\.([^.]+))?)?$/", js)
        # the build marks the area-wide items, and every topic's area items point at a 56 "Sources:" card
        n_area = 0
        for node in self.rm["nodes"]:
            for it in node.get("links", []):
                if it.get("file") == "56-sources-and-verification.md" and it["label"].startswith("Sources & verification"):
                    self.assertEqual(it.get("area"), 1, node["id"])
                    n_area += 1
            for it in node.get("study", []) + node.get("links", []):
                if it.get("area"):
                    self.assertTrue(it["anchor"].startswith("m56-sources-"), it["anchor"])
        self.assertGreater(n_area, 90)

    def test_module_end_leads_with_the_next_topic(self):
        """17 Nov 2026: the whole-module end card leads with the map's next step (nextTopic, as on the last section's
        card); handbook order is a smaller "Next module in the book: X (🔒 N locked) ›", shown only while that module
        has a section this reader can open. Book order jumped areas (cloud-concepts: Cloud → Security, 26 locked)."""
        js, css = self.js, focus_site.FOCUS_CSS
        card = js[js.index("function endCard()"):]
        whole = card[card.index("if (cur.whole) {"):card.index("kc = M.cmdList")]
        # the lead: same choice (nt = nextTopic(t)) and the same action as the section card, primary
        self.assertIn('if (nt) b.push(btn("nt", "Next topic: " + G.byId[nt].title + " →", function () { toMap(nt); }, null, 1));', whole)
        self.assertIn("nt = nextTopic(t)", js)
        self.assertNotIn('"Next module: "', js)
        # the book's order: after Back to topic, smaller, the count before the ›
        self.assertLess(whole.index('"← Back to topic"'), whole.index('"Next module in the book: "'))
        self.assertIn('"Next module in the book: " + nm.getAttribute("data-title") + (k.length ? " (🔒 " + k.length + " locked)" : "") + " ›"', whole)
        self.assertIn('nb.classList.add("fx-sm")', whole)
        self.assertNotRegex(whole[whole.index('"Next module in the book: "'):], r'\}, null, 1\)')   # never the primary
        self.assertIn(".fx-btn.fx-sm{", css)
        # shown only when a section of it is open to this reader, or nothing in it locks
        self.assertIn("(nm = nextMod(cur.mod)) && ((k = plan(nm)).free || !k.length)", whole)
        self.assertIn("out.free = okR.length;", js)
        # URLs and history unchanged: the book's module still opens through go() (replaceState), "#read.T.A.module.MOD"
        self.assertIn("function () { go(cur.i, true, nm); }", whole)
        self.assertIn("function url() { return enc(cur.t, cur.L[cur.i].a, cur.whole, cur.alt && cur.mod.id); }", js)
        # a lock change (roadmap-done) redraws the card: the next topic, the count and the visibility follow
        self.assertIn("if (old && old.isConnected) { old.replaceWith(endCard()); refocus(end, k); }", js)

    def test_nested_sections_in_the_page(self):
        """Topics that list a section and a subsection inside it exist (the de-duplication has work to do), and
        every module id is a bare word, so "#read.T.A.module.MODULE" stays unambiguous."""
        t = self.text["index.html"]
        mods = re.findall(r'<section class="mod-section" id="([^"]+)"', t)
        self.assertGreater(len(mods), 50)
        for m in mods:
            self.assertNotIn(".", m)
        cards = {}
        for m in re.finditer(r'<div class="subm"><h2 id="([^"]+)">(.*?)(?=<div class="subm"><h2 |</section>)', t, re.S):
            cards[m.group(1)] = set(re.findall(r'<h[3-6] id="([^"]+)"', m.group(2)))
        nested = 0
        for node in self.rm["nodes"]:
            anchors = [it["anchor"] for it in node.get("study", []) + node.get("links", []) if it.get("anchor")]
            nested += any(a in cards.get(b, ()) for a in anchors for b in anchors if a != b)
        self.assertGreater(nested, 20)

    def test_build_site_hooks(self):
        src = self.src
        self.assertIn("if (window.__focus && S.selected && window.__focus.open(S.selected, anchor)) return;", src)
        self.assertIn('document.dispatchEvent(new CustomEvent("roadmap-done", { detail: id }));', src)
        self.assertIn("if (window.__focus) window.__focus.exit();", src)              # search = reference reading
        self.assertIn("!h.closest('[hidden],[data-fx-off]')", src)                    # scrollspy skips hidden headings
        self.assertIn('s.hasAttribute("data-fx-off") ? null', src)                      # ... and hidden modules
        self.assertIn(":scope > .mod-section:not([data-fx-off])", backnav_site.BACKNAV_SCRIPT)
        # the map's study links still go through backnav when focus does not take them
        self.assertIn('if (el && window.__backnav) { window.__backnav.jump(el, "#" + anchor); return; }', src)
        # any other map link (a decoder card, an area's sources) leaves focused reading first
        self.assertLess(src.index("if (window.__focus) window.__focus.exit(1);"),
                        src.index('if (el && window.__backnav) { window.__backnav.jump(el, "#" + anchor); return; }'))
        self.assertIn('"area": 1,', src)

    def test_every_handbook_item_resolves(self):
        """Every roadmap item that names a handbook file resolves to a heading that exists in both pages."""
        n = 0
        for node in self.rm["nodes"]:
            for it in node.get("study", []) + node.get("links", []):
                if not it.get("file"):
                    continue
                n += 1
                with self.subTest(topic=node["id"], heading=it.get("heading")):
                    self.assertIn("anchor", it)
                    for name, t in self.text.items():
                        self.assertRegex(t, r'<h[23] id="%s">' % re.escape(it["anchor"]), name)
        self.assertGreater(n, 800)

    def test_hash_format_is_unambiguous(self):
        """"#read.TOPIC.ANCHOR[.module]" relies on topic ids and anchors without dots; h2 targets open as a whole card."""
        t = self.text["index.html"]
        for node in self.rm["nodes"]:
            self.assertNotIn(".", node["id"])
            for it in node.get("study", []) + node.get("links", []):
                a = it.get("anchor")
                if not a:
                    continue
                self.assertNotIn(".", a)
                if f'<h2 id="{a}">' in t:
                    self.assertIn(f'<div class="subm"><h2 id="{a}">', t, a)

    def test_size_budget(self):
        self.assertLessEqual(len((focus_site.FOCUS_CSS + self.js).encode("utf-8")), BUDGET)
        self.assertLessEqual(len((backnav_site.BACKNAV_CSS + backnav_site.BACKNAV_SCRIPT).encode("utf-8")), 6_500)
        for name in PAGES:
            with self.subTest(page=name):
                self.assertLess((ROOT / name).stat().st_size, SIZE_LIMIT)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_node_check(self):
        page = self.text["index.html"]
        bodies = [s for s in re.findall(r"<script(?: id=\"[\w-]+\")?>(.*?)</script>", page, re.S) if "W.__focus = {" in s]
        self.assertEqual(len(bodies), 1)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "focus.js"
            f.write_text(bodies[0], encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
