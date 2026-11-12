"""Visual layer: decoration must never change what the reader copies or reads (parses files only)."""
import html
import re
import unittest
from pathlib import Path

import markdown

from site_ui import decorate_body, decorate_code, top_level_h2, wrap_submodules

ROOT = Path(__file__).resolve().parents[1]


def render(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    return markdown.Markdown(extensions=["fenced_code", "tables", "toc", "md_in_html"]).convert(text)


def code_texts(body):
    return [html.unescape(re.sub(r"<[^>]+>", "", m)) for m in re.findall(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", body, re.S)]


class Decoration(unittest.TestCase):
    def test_code_text_is_unchanged(self):
        for name in ("02-network.md", "21-case-apache-443-dokploy.md", "17-windows.md", "33-learn-cicd-iac-sre.md"):
            body = render(name)
            self.assertEqual(code_texts(body), code_texts(decorate_code(body)), name)

    def test_comments_prompts_and_notes(self):
        body = ('<pre><code class="language-bash">ss -tlnp   # who listens\n# whole line\necho "#not" # yes\n</code></pre>'
                '<pre><code>$ mtr -rwc 50 example.com\n  3.|-- 198.51.100.9  80.0%   ← ignore!\n</code></pre>')
        out = decorate_code(body)
        self.assertIn('<pre data-lang="bash">', out)
        self.assertIn("ss -tlnp   <i># who listens</i>", out)
        self.assertIn("<i># whole line</i>", out)
        self.assertIn('echo "#not" <i># yes</i>', out)
        self.assertIn('<pre data-lang="terminal">', out)
        self.assertIn("<b><u>$ </u>mtr -rwc 50 example.com</b>", out)
        self.assertIn("<em>← ignore!</em>", out)

    def test_cards_wrap_each_top_level_section_and_stay_balanced(self):
        for name in ("02-network.md", "27-learn-linux.md", "55-paths-onprem-vs-cloud.md"):
            body = render(name)
            n = len(top_level_h2(body))
            wrapped = wrap_submodules(body)
            self.assertEqual(wrapped.count('<div class="subm">'), n, name)
            self.assertEqual(top_level_h2(wrapped), [], name)      # balanced, every h2 now inside a card
            self.assertEqual(re.sub(r'<div class="subm">|</div>\n?', "", wrapped).replace("\n", ""),
                             re.sub(r"</div>\n?", "", body).replace("\n", ""), name)

    def test_unbalanced_markup_is_left_alone(self):
        body = "<h2>a</h2><div><p>x</p><h2>b</h2>"
        self.assertEqual(wrap_submodules(body), body)

    def test_read_time_counts_only_visible_text(self):
        # QA 2026-11-07: the drills page said "≈ 63 min read" because its embedded JSON counted as words
        from site_ui import _read_time
        visible = "<p>" + "word " * 460 + "</p>"                       # 460 words = 2 min
        hidden = ('<script type="application/json" id="drill-data">' + '{"k":"v"},' * 20000 + "</script>"
                  '<div hidden><template data-drill="x"><p>' + "debrief " * 9000 + "</p></template></div>"
                  "<style>.a{color:red}</style>")
        self.assertEqual(_read_time(visible), "≈ 2 min read")
        self.assertEqual(_read_time(visible + hidden), "≈ 2 min read")


class BuiltPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.art = (ROOT / "artifact.html").read_text(encoding="utf-8")

    def test_every_module_has_a_hero_and_a_tone(self):
        sections = re.findall(r'<section class="mod-section" id="([^"]+)"[^>]*data-tone="(\w+)"', self.html)
        self.assertGreater(len(sections), 50)
        self.assertEqual(self.html.count('<header class="mod-hero tilt">'), len(sections))
        self.assertEqual(self.html.count("<h1>"), len(sections))
        self.assertIn('<div id="readbar" aria-hidden="true"></div>', self.html)

    def test_sidebar_modules_can_collapse(self):
        # regression (user report, 2026-10-04): an expanded module could never be collapsed again
        buttons = re.findall(r'<button class="mod-btn" data-target="#[^"]+"( aria-expanded="false")?>', self.html)
        with_sub = self.html.count('<ul class="subnav">')
        self.assertEqual(sum(1 for b in buttons if b), with_sub)
        self.assertIn("if (hasSub && (open || e.target.closest(\".chev\")))", self.html)
        self.assertIn("if (!userCollapsed.has(li)) setExpanded(li, true);", self.html)
        self.assertIn("if (id && id === S.selected) deselect();", self.html)      # map: second click closes a topic

    def test_jumps_settle_and_page_has_an_icon(self):
        # regression (QA pass, 2026-10-04): module jumps landed in the previous module because
        # neighbours rendered at their real height after the single re-align
        self.assertIn("function settleOn(el, opt)", self.html)
        self.assertIn("settleOn(el, opt);", self.html)                       # every jumpTo
        self.assertIn('addEventListener("hashchange", () => {', self.html)  # native #mNN links too
        self.assertIn('<link rel="icon" href="data:image/svg+xml', self.html[:3000])   # no favicon.ico 404
        self.assertNotIn('<link rel="icon"', self.art[:3000])               # the artifact host sets its own

    def test_artifact_contract_still_holds(self):
        self.assertTrue(self.art.startswith("<title>"))
        for tag in ("<!DOCTYPE", "<html", "<head", "<body"):
            self.assertNotIn(tag, self.art[:5000])
        self.assertNotRegex(self.art, r'<(?:script|link)[^>]+(?:src|href)="https?://')
        self.assertIn("prefers-reduced-motion", self.art)


if __name__ == "__main__":
    unittest.main()
