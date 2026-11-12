"""Job search unlocks at each milestone: the 3D map panel of the milestone topics shows a locked
section until the learner marks the topic done, then interview, career-ladder and ai-job-search links.

Run after building: python3 -m unittest tests.test_jobunlock -v
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

import build_site  # noqa: E402
from page_slim import minify_css  # noqa: E402

PAGES = ("index.html", "artifact.html")
SIZE_LIMIT = 15_950_000
MILESTONES = {"milestone-fresher": "L0", "milestone-junior": "L1", "milestone-mid": "L2",
              "cka-exam": "L3", "milestone-senior": "L3", "milestone-lead": "L4"}
TOOL = "https://github.com/ai-job-search-dev/ai-job-search"
LOCKED = "🔒 Job search — unlocks when you mark this milestone done"
UNLOCKED = "🔓 You're ready to apply for ${J.r}"
CAUTIONS = ("contact details, job history and salary expectations", "forks are always public",
            "linkedin-search", "guest endpoints", "freehire-search", "/add-portal",
            "Danish job boards", "untrusted input", "never applies for you")


class Page(HTMLParser):
    """ids, <script> bodies (type, id, text)."""

    def __init__(self, text):
        super().__init__()
        self.ids, self.scripts, self._s = set(), [], None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "script":
            self._s = [a.get("type", ""), a.get("id", ""), ""]

    def handle_endtag(self, tag):
        if tag == "script" and self._s is not None:
            self.scripts.append(tuple(self._s))
            self._s = None

    def handle_data(self, data):
        if self._s is not None:
            self._s[2] += data


class JobUnlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {n: (ROOT / n).read_text(encoding="utf-8") for n in PAGES}
        cls.pages = {n: Page(t) for n, t in cls.text.items()}
        cls.roadmap = json.loads((ROOT / "roadmap.json").read_text(encoding="utf-8"))

    def map_script(self, name):
        found = [b for typ, _, b in self.pages[name].scripts if typ != "application/json" and "function jobSection" in b]
        self.assertEqual(len(found), 1, name)
        return found[0]

    def job_data(self, name):
        found = [b for typ, i, b in self.pages[name].scripts if typ == "application/json" and i == "roadmap-data"]
        self.assertEqual(len(found), 1, name)
        return json.loads(found[0])["job"]

    def test_table_names_the_milestones(self):
        nodes = {n["id"]: n for n in self.roadmap["nodes"]}
        levels = {lv["id"]: lv for lv in self.roadmap["levels"]}
        self.assertEqual(set(build_site.JOB_UNLOCK), set(MILESTONES))
        for nid, lv in MILESTONES.items():
            with self.subTest(node=nid):
                self.assertEqual(nodes[nid]["level"], lv)
                self.assertTrue(nodes[nid].get("exit_check"))      # the locked line points at it
                self.assertTrue(levels[lv].get("exit_test"))

    def test_every_link_resolves_to_a_real_anchor(self):
        for name in PAGES:
            data, ids = self.job_data(name), self.pages[name].ids
            self.assertEqual(set(data["n"]), set(MILESTONES), name)
            self.assertEqual([k for _, _, k in data["c"]], ["i", "c"])
            for nid, j in data["n"].items():
                with self.subTest(page=name, node=nid):
                    self.assertIn("roles", j["r"])
                    self.assertEqual([k for _, _, k in j["l"]], ["i", "c"])     # interview pack, career ladder
                    for anchor, label, kind in j["l"] + data["c"]:
                        self.assertIn(anchor, ids)
                        self.assertTrue(anchor.startswith("m-interview-" if kind == "i" else "m40-"), anchor)
                        self.assertTrue(label)

    def test_packs_follow_the_stage(self):
        data = self.job_data("index.html")["n"]
        self.assertEqual(data["milestone-fresher"]["l"][0][0], "m-interview-fresher")
        self.assertEqual(data["milestone-junior"]["l"][0][0], "m-interview-junior-mid")
        self.assertTrue(data["milestone-mid"]["l"][0][0].startswith("m-interview-senior"))
        self.assertTrue(data["milestone-lead"]["l"][0][0].startswith("m-interview-senior"))
        self.assertIn("cka", data["cka-exam"]["l"][0][0])

    def test_panel_code(self):
        for name in PAGES:
            js = self.map_script(name)
            for needle in (LOCKED, UNLOCKED, TOOL, "Pass the exit check above first, then mark it done.",
                           "Nothing is tracked except on your own device.", "run /setup", "private repo",
                           "upstream", 'target: "_blank", rel: "noopener noreferrer"', "🎉 milestone done",
                           "Python 3.10+, Bun and LaTeX", "onclick: () => jumpTo(it.anchor)") + CAUTIONS:
                self.assertIn(needle, js, f"{name}: {needle}")
            # between "Prove it" and "Related playbooks", and toggling redraws the open panel in place
            order = ["kids.push(...proveSection(n))", "kids.push(...jobSection(n, done))", 'section("Related playbooks & notes"']
            pos = [js.index(x) for x in order]
            self.assertEqual(pos, sorted(pos), name)
            toggle = js[js.index("function toggleDone"):js.index("function updateProgress")]
            self.assertIn("renderPanel(G.byId[S.selected])", toggle)

    def test_unlocked_section_keeps_text_contrast(self):
        """QA4: the teal tint over --bg3 put links at 4.3:1 (light) and dim text at 4.47:1 (dark); over
        --bg2 every colour in the section is at least 4.8:1 in both themes."""
        for name, text in self.text.items():
            # the page ships minified CSS (page_slim.minify_css): look for the same rule in that spelling
            self.assertIn(minify_css(".mp-job.is-open { border-left-color: var(--tone); background: color-mix(in srgb, var(--tone) 9%, var(--bg2)); }"), text, name)
            self.assertNotIn("var(--tone) 9%, var(--bg3)", text, name)

    def test_pop_respects_reduced_motion(self):
        for name, text in self.text.items():
            self.assertIn(minify_css("@media (prefers-reduced-motion: reduce) { .jb-pop { animation: none; } }"), text, name)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_map_script_parses(self):
        r = subprocess.run(["node", "--check"], input=self.map_script("index.html"), text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_career_ladder_note(self):
        md = (ROOT / "40-career-ladder.md").read_text(encoding="utf-8")
        note = md.split("### Job search (unlocks at milestones)", 1)[1].split("\n#", 1)[0]
        self.assertIn(TOOL, note)
        for needle in ("forks are always public", "upstream", "linkedin-search", "freehire-search",
                       "Danish job boards", "untrusted input", "Mark as done"):
            self.assertIn(needle, note)
        self.assertLessEqual(len(note.strip().splitlines()), 8)
        for name in PAGES:
            self.assertIn("m40-job-search-unlocks-at-milestones", self.pages[name].ids)
            self.assertTrue(re.search(r'href="' + re.escape(TOOL) + '"', self.text[name]))

    def test_size_limit(self):
        size = (ROOT / "index.html").stat().st_size
        self.assertLess(size, SIZE_LIMIT, f"index.html is {size} bytes")


if __name__ == "__main__":
    unittest.main()
