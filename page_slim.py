"""Byte savers for the generated page (build_site.py and the *_site.py generators).

The handbook ships as ONE html file that must stay under the claude.ai artifact page cap
(about 16 MB, of which claude.ai's own wrapping takes about 600 KB). Everything here keeps
the page's behaviour, anchors, search results and visible content identical:

  minify_css(css)    drop comments and the whitespace CSS ignores (strings and url() kept as-is)
  minify_js(js)      drop comments, indentation, trailing spaces and blank lines. Newlines stay,
                     so automatic semicolon insertion never changes; strings, template literals
                     and regex literals are copied byte for byte. No renaming, no rewriting.
  compact_html(s)    for generated module HTML: drop whitespace-only text between two block-level
                     tags (outside <pre>, <script>, <style>), write &quot; &#x27; &gt; (and &amp;
                     where no entity can follow) as plain characters in text, '<hr />' -> '<hr>',
                     and drop the target/rel boilerplate of plain external links; the page script
                     puts it back on load (EXTERNAL_LINKS_JS), so every link still opens in a new tab.
"""
import re

__all__ = ["minify_css", "minify_js", "minify_script", "compact_html", "EXTERNAL_LINKS_JS"]


# --------------------------------------------------------------------------- CSS
_CSS_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|url\([^)]*\)|/\*.*?\*/', re.S)


def _css_plain(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r" ?([{};,]) ?", r"\1", s)
    s = s.replace(": ", ":")                 # only AFTER ':' -- ' :hover' (descendant) keeps its space
    return s.replace(";}", "}")


def minify_css(css):
    """Strings and url(...) are copied as they are; comments become nothing."""
    out, buf, pos = [], [], 0
    for m in _CSS_TOKEN.finditer(css):
        buf.append(css[pos:m.start()])
        tok = m.group(0)
        if tok.startswith("/*"):
            buf.append(" ")
        else:
            out.append(_css_plain("".join(buf))); buf = []
            out.append(tok)
        pos = m.end()
    buf.append(css[pos:])
    out.append(_css_plain("".join(buf)))
    return "".join(out).strip()


# --------------------------------------------------------------------------- JS
_JS_KEYWORDS_BEFORE_REGEX = {"return", "typeof", "instanceof", "in", "of", "new", "delete", "void",
                             "throw", "case", "do", "else", "yield", "await"}
_REGEX_AFTER = set("(,=:[!&|?{};+-*%<>~^")


def minify_js(js):
    """Comment and indentation stripper. A tiny lexer tracks strings, template literals
    (with nested ${...}), regex literals and comments, so nothing inside them changes."""
    out = []                  # output chars
    i, n = 0, len(js)
    stack = []                # template-literal nesting: brace depth at each '${'
    depth = 0                 # current brace depth (code)
    last = ""                 # last significant code character / word, for the regex test

    def at_line_start():
        return not out or out[-1] == "\n"

    def newline():
        while out and out[-1] in " \t":
            out.pop()
        if out and out[-1] != "\n":
            out.append("\n")

    def template(j):
        """Copy a template literal starting after its backtick; return index after the
        closing backtick, or after '${' (pushing state)."""
        while j < n:
            c = js[j]
            if c == "\\":
                out.append(js[j:j + 2]); j += 2; continue
            if c == "`":
                out.append(c); return j + 1, False
            if c == "$" and j + 1 < n and js[j + 1] == "{":
                out.append("${"); return j + 2, True
            out.append(c); j += 1
        raise ValueError("unterminated template literal")

    while i < n:
        c = js[i]
        if c in " \t":
            if at_line_start():
                i += 1; continue
            out.append(c); i += 1; continue
        if c in "\r\n":
            newline(); i += 1; continue
        if c == "/" and i + 1 < n and js[i + 1] == "/":
            j = js.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "/" and i + 1 < n and js[i + 1] == "*":
            j = js.find("*/", i + 2)
            if j < 0:
                raise ValueError("unterminated block comment")
            if "\n" in js[i:j]:
                newline()
            elif out and out[-1] not in " \t\n":
                out.append(" ")
            i = j + 2
            continue
        if c in "'\"":
            j = i + 1
            while j < n and js[j] != c:
                if js[j] == "\\":
                    j += 1
                elif js[j] == "\n":
                    raise ValueError("newline in string literal")
                j += 1
            out.append(js[i:j + 1]); i = j + 1; last = c
            continue
        if c == "`":
            out.append(c)
            i, opened = template(i + 1)
            if opened:
                stack.append(depth); depth += 1
            last = "`"
            continue
        if c == "/" and (last == "" or last in _REGEX_AFTER or last in _JS_KEYWORDS_BEFORE_REGEX):
            j, in_class = i + 1, False
            while j < n:
                d = js[j]
                if d == "\\":
                    j += 2; continue
                if d == "\n":
                    raise ValueError("newline in regex literal near: " + js[i:i + 40])
                if in_class:
                    in_class = d != "]"
                elif d == "[":
                    in_class = True
                elif d == "/":
                    break
                j += 1
            j += 1
            while j < n and (js[j].isalnum() or js[j] == "_"):
                j += 1
            out.append(js[i:j]); i = j; last = "/re/"
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if stack and depth == stack[-1]:
                stack.pop()
                out.append("}")
                i, opened = template(i + 1)
                if opened:
                    stack.append(depth); depth += 1
                last = "`"
                continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (js[j].isalnum() or js[j] in "_$"):
                j += 1
            word = js[i:j]
            out.append(word); i = j; last = word
            continue
        out.append(c); i += 1; last = c
    if stack:
        raise ValueError("unterminated ${ in template literal")
    newline()
    return "".join(out).strip("\n")


def minify_script(tag):
    """'<script>…</script>' (as the generators keep their page scripts) -> same tag, minified body."""
    m = re.fullmatch(r"(\s*<script>)(.*)(</script>\s*)", tag, re.S)
    if not m:
        raise ValueError("expected one <script>…</script> block")
    return "<script>\n" + minify_js(m.group(2)) + "\n</script>"


# --------------------------------------------------------------------------- HTML
BLOCK_TAGS = frozenset("""p div li ul ol dl dt dd table thead tbody tfoot tr td th caption colgroup col
    h1 h2 h3 h4 h5 h6 blockquote details summary section header footer nav aside main article figure
    figcaption hr pre script style form fieldset legend""".split())
_RAW = re.compile(r"<(pre|script|style|textarea)\b[^>]*>.*?</\1>", re.S)
_TAG = re.compile(r"<[^>]+>")
_TAG_NAME = re.compile(r"</?([a-zA-Z][\w-]*)")
_EXT_LINK = re.compile(r'<a href="(https?://[^"]+)" target="_blank" rel="noopener">')
_AMP = re.compile(r"&amp;(?![A-Za-z0-9#])")

# put back on load what compact_html dropped from plain external links: in the module HTML and in
# the <template> rooms/debriefs the labs and drills clone from. It runs first in the page script,
# before anything reads or clones the module HTML; links that already carry a target keep theirs.
EXTERNAL_LINKS_JS = ('(() => { const fix = r => r.querySelectorAll(\'a[href^="http"]:not([target])\')'
                     '.forEach(a => { a.target = "_blank"; a.rel = "noopener"; }); '
                     'const m = document.getElementById("main"); if (!m) return; fix(m); '
                     'm.querySelectorAll("template").forEach(t => fix(t.content)); })();')


def _text(t):
    """Entity spellings that mean the same character in HTML text (never in attributes)."""
    if "&" not in t:
        return t
    t = t.replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'").replace("&gt;", ">")
    return _AMP.sub("&", t)


def _pre(block):
    """Inside <pre>: same entity rewrite on the text between tags; whitespace is content."""
    parts = _TAG.split(block)
    tags = _TAG.findall(block)
    out = [_text(parts[0])]
    for tag, txt in zip(tags, parts[1:]):
        out.append(tag); out.append(_text(txt))
    return "".join(out)


def _name(tag):
    m = _TAG_NAME.match(tag)
    return (m.group(1).lower(), tag.startswith("</")) if m else ("", False)


def compact_html(s):
    # tokens: ("raw", text) for <pre>/<script>/<style> blocks, ("tag", text), ("text", text)
    toks = []
    pos = 0
    for m in _RAW.finditer(s):
        _split(s[pos:m.start()], toks)
        blk = m.group(0)
        toks.append(("raw", _pre(blk) if m.group(1) == "pre" else blk, m.group(1), False))
        pos = m.end()
    _split(s[pos:], toks)
    out = []
    for k, (kind, val, _name_, _closing) in enumerate(toks):
        if kind == "text":
            if not val.strip():
                prev = toks[k - 1] if k else None
                nxt = toks[k + 1] if k + 1 < len(toks) else None
                if prev and nxt and prev[0] != "text" and nxt[0] != "text" \
                        and prev[2] in BLOCK_TAGS and nxt[2] in BLOCK_TAGS:
                    # never between <x> and its own </x>: an element that only holds whitespace
                    # is not :empty, and must not become so
                    same = prev[0] == "tag" and nxt[0] == "tag" and not prev[3] and nxt[3] and prev[2] == nxt[2]
                    if not same:
                        continue
                out.append(val)
            else:
                out.append(_text(val))
        else:
            out.append(val)
    return "".join(out)


def _split(seg, toks):
    pos = 0
    for m in _TAG.finditer(seg):
        if m.start() > pos:
            toks.append(("text", seg[pos:m.start()], "", False))
        tag = m.group(0)
        if tag.startswith("<!--"):
            toks.append(("tag", tag, "", False))
        else:
            name, closing = _name(tag)
            if name == "hr" and tag == "<hr />":
                tag = "<hr>"
            elif name == "a":
                tag = _EXT_LINK.sub(r'<a href="\1">', tag)
            toks.append(("tag", tag, name, closing))
        pos = m.end()
    if pos < len(seg):
        toks.append(("text", seg[pos:], "", False))
