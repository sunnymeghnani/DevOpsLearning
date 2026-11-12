"""Back navigation after in-page jumps: every jump the reader starts pushes a history entry (Back
returns to the map topic or the scroll position they left) and a floating "← Back" pill names the
origin. Automatic hash corrections keep using replaceState.

Run after building: python3 -m unittest tests.test_backnav -v
"""
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
import build_site  # noqa: E402

PAGES = ("index.html", "artifact.html")
SIZE_LIMIT = 15_950_000
BUDGET = 6_500          # bytes of pill CSS + script in the page ("about 6 KB")


def scripts(text):
    return re.findall(r"<script(?: id=\"[\w-]+\")?>(.*?)</script>", text, re.S)


class BackNav(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {n: (ROOT / n).read_text(encoding="utf-8") for n in PAGES}
        cls.src = (ROOT / "build_site.py").read_text(encoding="utf-8")
        cls.js = backnav_site.BACKNAV_SCRIPT

    def test_pages_carry_pill_css_and_script(self):
        for name, t in self.text.items():
            with self.subTest(page=name):
                self.assertEqual(t.count(backnav_site.BACKNAV_HTML), 1)
                self.assertIn(backnav_site.BACKNAV_CSS, t)
                self.assertIn(self.js, t)
                self.assertEqual(t.count('id="backnav"'), 1)

    def test_pill_markup_and_strings(self):
        h = backnav_site.BACKNAV_HTML
        self.assertIn('class="backnav"', h)
        self.assertIn(" hidden>", h)                      # never shown on a cold load
        self.assertIn('<button type="button" class="bn-go">← Back</button>', h)
        self.assertIn('aria-label="Hide the back button"', h)
        self.assertIn("✕", h)
        for needle in ('"Back to " + c.t.trim()', '"map" + (n ? ": " + n.title : "")', '"drill: "', '"lab: "',
                       'getAttribute("data-title")', 'btn.setAttribute("aria-label", s)', 'e.key === "Escape"',
                       "dialog[open],#sidebar.open", "1.5 * innerHeight", "setTimeout(later, 12000)"):
            self.assertIn(needle, self.js, needle)

    def test_pill_css(self):
        css = backnav_site.BACKNAV_CSS
        for needle in ("position: fixed", "var(--bg2)", "var(--accent)", "var(--shadow)", "border-radius: 999px",
                       ".map-open .backnav, .drill-open .backnav, .lab-on .backnav { display: none; }",
                       "@media (max-width: 900px)", "max-width: calc(100vw - 90px)", "prefers-reduced-motion: reduce",
                       ":focus-visible"):
            self.assertIn(needle, css, needle)
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,6}\b")     # theme tokens only: both themes for free

    def test_jumps_push_history(self):
        js = self.js
        self.assertIn('H.pushState({ bn: from.k, bo: from }, "", hash || location.href)', js)
        self.assertIn("rs({ bnK: from.k, bnPt: from.pt }); W.__map.close({ keepHistory: true })", js)  # topic + panel scroll
        self.assertIn("rs({ bnK: from.k, bnY: from.y, bnA: from.a, bnO: from.o })", js)    # scrollY + heading anchor
        self.assertIn("back = was && s.bnK && was.bn === s.bnK", js)                      # only from its own landing
        self.assertIn('if (st().bn === c.k) return H.back();', js)                        # pill = browser Back
        self.assertIn('addEventListener("popstate"', js)
        self.assertIn('D.addEventListener("click", function (e) { pre = link(e) ? here() : null; }, true)', js)
        self.assertIn("e.defaultPrevented || e.button || e.metaKey", js)                 # new-tab clicks stay native
        self.assertIn(r"/^(map([./]|$)|drill\.|lab\.)/", js)                             # their own history
        # map study / job-unlock links and search results go through it
        self.assertIn('if (el && window.__backnav) { window.__backnav.jump(el, "#" + anchor); return; }', self.src)
        self.assertIn('if (B) { B.jump(d.el, d.el.id ? "#" + d.el.id : "", from, 1); return; }', self.src)

    def test_corrections_keep_replace_state(self):
        src = self.src
        self.assertIn('history.replaceState(history.state, "", hsh)', src)                # map topic hash
        self.assertIn('history.replaceState(null, "", "#" + LEGACY[lm[1]])', src)         # old bookmarks
        self.assertIn('history.state && history.state.bnY != null', src)                  # Back: no snap to the hash
        self.assertIn("jumpTo.stop = () => { settleToken++; };", src)
        self.assertIn("H.replaceState(Object.assign({}, st(), o), \"\")", self.js)        # origin note: same URL
        self.assertEqual(self.js.count("pushState"), 1)
        # drills and labs keep their own entries
        self.assertIn('history.pushState({ drill: 1 }, "", "#drill." + id)', build_site.DRILLS_SCRIPT)
        self.assertIn('history.pushState({ lab: 1 }, "", "#lab." + id)', build_site.LABS_SCRIPT)

    def test_map_practice_links_get_their_own_entry(self):
        """QA4: a drill or lab room opened from a map topic's "Prove it" used to replace the map entry, so
        Back skipped the map. Now it keeps the topic and panel scroll on the map entry and pushes its own."""
        src = self.src
        body = src[src.index("function openPractice"):src.index("function practiceLink")]
        self.assertIn("history.replaceState(Object.assign({}, history.state, { mapSel: S.selected, mapPt: panel.scrollTop }), \"\")", body)
        self.assertNotIn('history.replaceState(null, "", "#" + kind + "." + id)', body)
        self.assertIn("fn(id);", body)
        self.assertNotIn("fn(id, true)", body)              # fromHash would skip the drill's / room's pushState
        self.assertLess(body.index("mapPt: panel.scrollTop"), body.index("closeMap({ keepHistory: true })"))
        route = src[src.index("function routeFromHash"):src.index('addEventListener("hashchange", routeFromHash)')]
        self.assertIn("hs.mapSel === id && hs.mapPt != null", route)
        for name, t in self.text.items():
            with self.subTest(page=name):
                self.assertIn("mapSel: S.selected, mapPt: panel.scrollTop", t)

    def test_size_budget(self):
        self.assertLessEqual(len((backnav_site.BACKNAV_CSS + self.js).encode("utf-8")), BUDGET)
        for name in PAGES:
            with self.subTest(page=name):
                self.assertLess((ROOT / name).stat().st_size, SIZE_LIMIT)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_node_check(self):
        page = self.text["index.html"]
        bodies = [s for s in scripts(page) if "__backnav" in s]
        self.assertTrue(bodies)
        with tempfile.TemporaryDirectory() as d:
            for i, body in enumerate(bodies):
                f = Path(d) / f"s{i}.js"
                f.write_text(body, encoding="utf-8")
                r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
