""""Safest next step" hints (hints/safest-step.tsv) and the module 57 print card (Version 12).

Every hint names a (file, heading) pair; the build puts one line under that heading linking to the
risk ladder in module 57. A heading that is missing, or that is not unique, is a build warning and a
failure here.
"""
import ipaddress
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_site  # noqa: E402
from page_slim import minify_css  # noqa: E402
from site_ui import HINTS_FILE, LADDER_ID, UI_CSS, UI_SCRIPT, insert_hints, load_hints  # noqa: E402

TSV = ROOT / HINTS_FILE
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]


def rows():
    lines = [l for l in TSV.read_text(encoding="utf-8").splitlines() if l.strip()]
    return lines[0], [l.split("\t") for l in lines[1:]]


class HintFile(unittest.TestCase):
    def test_format_and_limits(self):
        self.assertLess(TSV.stat().st_size, 12 * 1024)
        header, body = rows()
        self.assertEqual(header.split("\t"), ["file", "heading", "rung", "text"])
        self.assertGreaterEqual(len(body), 15)
        seen = set()
        for r in body:
            self.assertEqual(len(r), 4, r)
            fname, heading, rung, text = r
            self.assertRegex(fname, r"^\d\d-[\w.-]+\.md$")
            self.assertTrue((ROOT / fname).is_file(), fname)
            self.assertIn(int(rung), range(1, 9), r)
            self.assertLessEqual(len(text), 160, r)
            self.assertNotIn((fname, heading), seen, "duplicate hint")
            seen.add((fname, heading))

    def test_no_real_names_or_addresses(self):
        text = TSV.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"/home/|/Users/|sunny")
        for ip in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text):
            self.assertTrue(any(ipaddress.ip_address(ip) in n for n in DOC_NETS), ip)

    def test_every_heading_exists_exactly_once(self):
        hints = load_hints(str(ROOT))
        titles = {f: (t, i, g) for f, t, i, g in build_site.MODULES}
        for fname in hints:
            self.assertIn(fname, titles, f"{fname} is not in MODULES")
            mod = build_site.render_module(fname, *titles[fname])
            self.assertEqual(mod["hint_missing"], [], f"{fname}: headings not found once")


class HintBuildStep(unittest.TestCase):
    TOC = [{"name": "1. Alpha", "id": "1-alpha", "children": [{"name": "Beta &amp; gamma", "id": "beta-gamma", "children": []}]},
           {"name": "Twice", "id": "twice", "children": []}, {"name": "Twice", "id": "twice_1", "children": []}]
    BODY = '<h2 id="m99-1-alpha">1. Alpha</h2><p>a</p><h3 id="m99-beta-gamma">Beta &amp; gamma</h3><p>b</p>'

    def test_line_goes_right_under_its_heading(self):
        body, missing = insert_hints(self.BODY, self.TOC, [("Beta & gamma", 3, "Restart <one> replica")], "m99-")
        self.assertEqual(missing, [])
        self.assertIn('Beta &amp; gamma</h3><blockquote class="callout ok ssn no-index"><p>🛟 Safest next step · '
                      f'<a href="#{LADDER_ID}">rung 3</a>: Restart &lt;one&gt; replica</p></blockquote><p>b</p>', body)

    def test_missing_or_ambiguous_heading_is_reported(self):
        body, missing = insert_hints(self.BODY, self.TOC, [("Nope", 1, "x"), ("Twice", 1, "y")], "m99-")
        self.assertEqual(missing, ["Nope", "Twice"])
        self.assertEqual(body, self.BODY)

    def test_build_warns(self):
        warnings = []
        mods = [{"file": "99-x.md", "hint_missing": ["Nope"], "ids": set()}]
        by_file = {m["file"]: m for m in mods}
        build_site.hint_warnings({"99-x.md": [("Nope", 1, "x")], "98-gone.md": [("A", 1, "y")]}, mods, by_file, warnings.append)
        self.assertEqual(len(warnings), 3, warnings)
        self.assertTrue(any("'Nope'" in w for w in warnings))
        self.assertTrue(any("98-gone.md" in w for w in warnings))
        self.assertTrue(any(LADDER_ID in w for w in warnings))

    def test_docker_build_context_keeps_the_tsv(self):
        ignore = ROOT / ".dockerignore"
        if not ignore.is_file():          # inside the image build: .dockerignore is not copied, the TSV must be
            self.assertTrue(TSV.is_file())
            return
        lines = [l.strip() for l in ignore.read_text().splitlines() if l.strip() and not l.startswith("#")]
        top = HINTS_FILE.split("/")[0]
        for pat in lines:
            self.assertFalse(pat.startswith(top) or pat in ("*.tsv", "**/*.tsv"), pat)


class BuiltPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_one_line_under_each_heading(self):
        _, body = rows()
        found = re.findall(r'</h[1-6]><blockquote class="callout ok ssn no-index"><p>🛟 Safest next step · '
                           rf'<a href="#{LADDER_ID}">rung \d</a>', self.page)
        self.assertEqual(len(found), len(body))
        self.assertEqual(self.page.count('class="callout ok ssn'), len(body))
        self.assertEqual(self.page.count(f'id="{LADDER_ID}"'), 1)

    def test_print_card(self):
        self.assertEqual(self.page.count('id="m57-the-protect-card"'), 1)
        self.assertIn('getElementById("m57-the-protect-card")', UI_SCRIPT)
        self.assertIn("window.print()", UI_SCRIPT)
        self.assertIn(minify_css("body.printing-card > *:not(#print-card) { display: none !important; }"), UI_CSS)
        self.assertIn(minify_css("#print-card { display: none; }"), UI_CSS)

    def test_print_card_keeps_the_reading_position(self):
        # QA5: the print layout holds only the card, so Chrome came back at the top of the page
        # (scrollY 745,532 -> 0). The handler saves the position and restores it on afterprint.
        start = UI_SCRIPT.index('getElementById("m57-the-protect-card")')
        handler = UI_SCRIPT[start:UI_SCRIPT.index("window.print()", start)]
        self.assertRegex(handler, r"var y\s*=\s*window\.scrollY")
        done = handler[handler.index("var done"):]
        self.assertRegex(done, r"window\.scrollTo\(0,\s*y\)")

    def test_module_57_is_first_in_its_group(self):
        group = [f for f, _, _, g in build_site.MODULES if g == "Real incidents & playbooks"]
        self.assertEqual(group[0], "57-method-protect-risk-ladder.md")


if __name__ == "__main__":
    unittest.main()
