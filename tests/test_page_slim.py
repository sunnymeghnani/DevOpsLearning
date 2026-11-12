"""page_slim.py byte savers + the desktop-only page (user, 10 Nov 2026).

The savers must never change what the reader sees, copies or searches: <pre> text stays byte for
byte, inline whitespace stays, attributes keep their entities, JS keeps every token and newline.
"""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from page_slim import EXTERNAL_LINKS_JS, compact_html, minify_css, minify_js, minify_script  # noqa: E402


class CompactHtml(unittest.TestCase):
    def test_block_whitespace_goes_inline_whitespace_stays(self):
        src = "<table>\n<tr>\n<td>a</td>\n<td><code>x</code> <strong>y</strong></td>\n</tr>\n</table>\n<p>one</p>\n<p>two</p>"
        self.assertEqual(compact_html(src),
                         "<table><tr><td>a</td><td><code>x</code> <strong>y</strong></td></tr></table><p>one</p><p>two</p>")
        # text next to an inline tag, a <br>, or an element that only holds whitespace keeps its space
        for keep in ("<p>a <br>\nb</p>", "<li><code>a</code>\n<code>b</code></li>", "<div>\n</div>", "<span>\n</span>"):
            self.assertEqual(compact_html(keep), keep)

    def test_pre_script_style_are_left_alone(self):
        pre = '<pre data-lang="bash"><code><b><u>$ </u>echo "a  b" &gt; f &amp;&amp; cat f</b>\n\n  done\n</code></pre>'
        out = compact_html("<p>x</p>\n" + pre + "\n<p>y</p>")
        self.assertIn('<pre data-lang="bash"><code><b><u>$ </u>echo "a  b" > f && cat f</b>\n\n  done\n</code></pre>', out)
        for raw in ('<script type="application/json" id="d">{"a": "&quot; &gt;\\n  x"}</script>',
                    "<style>\n.a  >  .b { color: red; }\n</style>"):
            self.assertIn(raw, compact_html("<div>\n" + raw + "\n</div>"))

    def test_entities_only_in_text_and_only_when_safe(self):
        src = '<p title="say &quot;hi&quot; &amp; &gt;">&quot;q&quot; it&#x27;s a &gt; b &amp;&amp; c &amp;lt; d &amp;copy &amp;#39;</p>'
        self.assertEqual(compact_html(src),
                         '<p title="say &quot;hi&quot; &amp; &gt;">"q" it\'s a > b && c &amp;lt; d &amp;copy &amp;#39;</p>')
        self.assertEqual(compact_html("<p>&lt;none&gt;</p>"), "<p>&lt;none></p>")   # '<' must stay escaped

    def test_external_link_boilerplate(self):
        plain = '<a href="https://example.com/a?b=1&amp;c=2" target="_blank" rel="noopener">x</a>'
        self.assertEqual(compact_html(plain), '<a href="https://example.com/a?b=1&amp;c=2">x</a>')
        for keep in ('<a class="lcard" href="https://e.com" target="_blank" rel="noopener">x</a>',
                     '<a href="https://e.com" target="_blank" rel="noopener noreferrer">x</a>',
                     '<a href="#m27">x</a>'):
            self.assertEqual(compact_html(keep), keep)
        # the page script puts target/rel back, in the module HTML and inside <template> rooms/debriefs
        self.assertIn('a[href^="http"]:not([target])', EXTERNAL_LINKS_JS)
        self.assertIn('a.target = "_blank"; a.rel = "noopener";', EXTERNAL_LINKS_JS)
        self.assertIn("t.content", EXTERNAL_LINKS_JS)


class MinifyCssJs(unittest.TestCase):
    def test_css(self):
        css = ('/* c */\n.a :hover, .b > .c {\n  content: " : ; } ";  color: var(--x);\n}\n'
               '@media (max-width: 900px) { .d { width: calc(100% - 2px); } }')
        self.assertEqual(minify_css(css), '.a :hover,.b > .c{content:" : ; } ";color:var(--x)}'
                                          '@media (max-width:900px){.d{width:calc(100% - 2px)}}')

    def test_js_keeps_literals_and_newlines(self):
        js = ('  // line comment\n  const re = /\\/\\*not a comment*\\//g, s = "// no", t = `a\n    ${ {k: 1}.k } // kept`;\n'
              '  /* block\n  comment */\n  let x = 1 / 2 / 3; return_(x)\n  a = b\n  (c)\n')
        out = minify_js(js)
        self.assertEqual(out, 'const re = /\\/\\*not a comment*\\//g, s = "// no", t = `a\n    ${ {k: 1}.k } // kept`;\n'
                              'let x = 1 / 2 / 3; return_(x)\na = b\n(c)')
        self.assertEqual(minify_script("<script>\n  a();\n</script>"), "<script>\na();\n</script>")

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_every_page_script_parses(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        bodies = [m.group(2) for m in re.finditer(r"<script([^>]*)>(.*?)</script>", page, re.S) if "json" not in m.group(1)]
        self.assertGreater(len(bodies), 8)
        for i, body in enumerate(bodies):
            r = subprocess.run(["node", "--check"], input=body, text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, f"script {i}: {r.stderr}")


class DesktopOnlyPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {n: (ROOT / n).read_text(encoding="utf-8") for n in ("index.html", "artifact.html")}

    def test_no_phone_layouts(self):
        for name, page in self.pages.items():
            with self.subTest(page=name):
                widths = {int(w) for w in re.findall(r"@media ?\(max-width: ?(\d+)px\)", page)}
                self.assertTrue(widths, name)
                self.assertGreaterEqual(min(widths), 900, sorted(widths))       # nothing for phones / small tablets
                self.assertNotIn("min-width: 641px", page)
                self.assertNotIn("safe-area-inset", page)
                self.assertNotIn("viewport-fit", page)
                self.assertNotIn("--h-m", page)
                self.assertNotIn("text-size-adjust", page)
                self.assertNotIn("hover:none", page.replace(" ", ""))
                self.assertNotIn("S.vw <= 800", page)                           # map bottom-sheet branch gone

    def test_narrow_laptop_layout_kept(self):
        for name, page in self.pages.items():
            with self.subTest(page=name):
                self.assertIn('drawerMQ = mq("(max-width: 900px)")', page)       # collapsible sidebar
                self.assertRegex(page, r"@media \(max-width:900px\)\{#sidebar\{")
                self.assertRegex(page, r"@media \(max-width:900px\)\{\.lab-split\{grid-template-columns:1fr")
                self.assertRegex(page, r"\.cv > \.mod-section\{content-visibility:auto;contain-intrinsic-size:auto var\(--h-d,4000px\)\}")
                self.assertRegex(page, r'<section class="mod-section" id="m27"[^>]* style="--h-d:\d+px">')

    def test_slim_markup(self):
        page = self.pages["index.html"]
        self.assertIn(EXTERNAL_LINKS_JS, page)
        self.assertNotIn('class="language-', page)
        self.assertNotIn("nav-h2", page)
        self.assertNotIn("nav-h3", page)
        self.assertIn(".subnav ul a{font-size:12.8px}", page)
        main = page[page.index('<main id="main"'):page.index("</main>")]
        main = re.sub(r"<(pre|script|style)\b.*?</\1>", "", main, flags=re.S)
        self.assertNotIn("&quot;", re.sub(r"<[^>]+>", "", main))
        self.assertLess(len(re.findall(r"</td>\n<td>|</p>\n<p>|<tr>\n<td>", main)), 10)


if __name__ == "__main__":
    unittest.main()
