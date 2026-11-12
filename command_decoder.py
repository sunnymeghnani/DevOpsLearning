"""Command Decoder: what each command means and why it works, for every submodule.

commands/ holds the decoder cards, one Markdown file per command family
(network.md, docker-and-containers.md, ...), plus INTRO.md (the page intro) and
README.md (how to write a card; not published). A card is a "### " heading, a
metadata block, then the explanation:

    ### mtr — where along the path packets are lost
    Match: mtr
    Instead of: ping, traceroute
    Safety: read-only

    **In one line:** ...

At build time this module
  * renders the cards as one page, "Command Decoder" (family = "##", card = "###");
  * scans every "## " section (submodule) of every handbook module for the commands
    its code blocks run and puts a collapsed "commands in this submodule, decoded"
    box right under that section's heading. The box holds links to the cards; the
    page script copies the full cards into the box the first time it is opened, so
    each card exists once in the HTML however many submodules use it;
  * adds a "Used in" line to each card, linking back to the modules that use it.

Matching is textual only: nothing is executed. A code line counts as a command
when it sits in a bash/sh/console/powershell block, or behind a "$ " / "PS>" prompt
in an untagged block. Each pipeline segment is reduced to its command words
("sudo -u postgres psql -c ..." -> "psql"), nested commands are followed
("ip netns exec ns1 ping ..." -> also "ping"; "kubectl exec pod -- ss -tlnp" ->
also "ss"), and the words are matched most-specific-first against the cards'
Match keys ("docker compose logs", then "docker compose", then "docker").

    python3 command_decoder.py --check commands/network.md --heads "ping mtr ip ss"
    python3 command_decoder.py --coverage
"""
import argparse
import html
import os
import re
import shlex
import sys

from page_slim import minify_script

CARD_DIR = "commands"
DECODER_FILE = "command-decoder.md"
NOT_FAMILIES = {"README.md", "INTRO.md"}
REQUIRED_PARTS = ("**In one line:**", "**Read the command:**", "**Why it is effective:**",
                  "**Trap:**", "**Next step:**")

CMD_LANGS = {"bash", "sh", "shell", "console", "zsh", "powershell", "ps1", "pwsh", "cmd", "bat"}
# "$ cmd" and "PS C:\> cmd" are prompts; "# cmd" is NOT (it is a comment far more often)
PROMPT_RE = re.compile(r"^\s*(?:\$|PS [^>\n]*>|PS>|C:\\[^>\n]*>|[\w.-]+@[\w.-]+:[^$#\n]*[$#])\s+(.*)$")
SPLIT_TOKENS = {"|", "||", "&&", ";", "&", "(", ")", "|&", ";;", ";&", "&>"}
SUBST_RE = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
LEAD_KEYWORDS = {"do", "then", "else", "elif", "if", "while", "until", "{", "}", "!"}
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S*$")
WORD_RE = re.compile(r"[A-Za-z][\w.+-]*$")
POWERSHELL_RE = re.compile(r"[A-Z][A-Za-z]+-[A-Z][A-Za-z]+$")   # Get-Process, ForEach-Object
# PowerShell's capitalised short aliases name their cmdlet's card ("Sort CPU" is Sort-Object,
# not the Unix sort)
PS_ALIASES = {"Select": "select-object", "Where": "where-object", "Sort": "sort-object",
              "ForEach": "foreach-object", "Measure": "measure-object", "Group": "group-object"}


def normalize_head(head):
    """The match form of a command's first word: lower-case for ordinary commands and
    PowerShell cmdlets; a capitalised word such as "Host" (pasted ssh_config) stays as is."""
    if head in PS_ALIASES:
        return PS_ALIASES[head]
    return head.lower() if (head[:1].islower() or POWERSHELL_RE.match(head)) else head
WRAPPERS = {"sudo", "doas", "time", "nohup", "exec", "env", "watch", "timeout", "nice", "ionice",
            "stdbuf", "!", "command", "builtin", "xargs", "chroot"}
WRAPPER_VALUE_FLAGS = {
    "sudo": {"-u", "-g", "-h", "-C", "-D", "-p", "-r", "-t", "-U"},
    "watch": {"-n", "-d"}, "timeout": {"-s", "-k"}, "nice": {"-n"}, "ionice": {"-c", "-n", "-p"},
    "stdbuf": {"-o", "-e", "-i"}, "xargs": {"-I", "-n", "-P", "-d", "-L", "-a", "-E", "-s"},
    "env": {"-u", "-C", "-S"},
}
# global flags of multi-tools that consume the next word ("kubectl -n prod get pods")
TOOL_VALUE_FLAGS = {"-n", "--namespace", "--context", "-H", "--host", "-f", "--file", "-p",
                    "--project-name", "--profile", "--region", "--kubeconfig", "-C", "--log-level",
                    "--cluster", "--server", "-s", "--env-file", "--project-directory"}
# per-tool exceptions: "--user" names a kubeconfig user for kubectl, but is a plain switch
# for systemctl ("systemctl --user daemon-reload")
TOOL_VALUE_FLAGS_BY_TOOL = {
    "kubectl": TOOL_VALUE_FLAGS | {"--user", "--as", "--as-group", "--request-timeout"},
    "systemctl": {"-H", "--host", "-M", "--machine", "-t", "--type", "--state", "-n", "--lines",
                  "-o", "--output", "--root", "-s", "--signal", "--kill-whom"},
    # ip: -s is "statistics" (ip -s link show eth0); only these options take a value
    "ip": {"-n", "-netns", "-f", "-family", "-b", "-batch", "-l", "-loops", "-rc", "-rcvbuf"},
    # iptables: the word after -t/-I/-A/-C/-D/-L/-S is the table or chain, which picks the card
    "iptables": set(), "ip6tables": set(),
    # restic: "restic -r REPO check" -> the repository is a value, "check" picks the card
    "restic": {"-r", "--repo", "--repository-file", "-p", "--password-file", "--password-command",
               "-o", "--option", "--cache-dir", "--cacert", "--limit-upload", "--limit-download"},
}


def command_words(words):
    """['sudo', '-u', 'pg', 'psql', '-c', 'x'] -> ['psql', '-c', 'x']: shell keywords, wrappers
    and VAR=x assignments stripped. A string is split on whitespace first."""
    if isinstance(words, str):
        words = words.split()
    i = 0
    while i < len(words):
        w = words[i]
        if w in LEAD_KEYWORDS or ENV_ASSIGN_RE.match(w):
            i += 1
            continue
        if w == "command" and i + 1 < len(words) and words[i + 1] in ("-v", "-V"):
            return []                                # "command -v wget" only looks wget up
        if w in WRAPPERS:
            vf = WRAPPER_VALUE_FLAGS.get(w, set())
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in vf else 1
            if w in ("timeout", "chroot"):          # timeout [-s SIG] DURATION cmd / chroot DIR cmd
                i += 1
            continue
        break
    return words[i:]


def _nested(words):
    """Commands run *inside* another command: sh -c '...', ip netns exec NS cmd, nsenter ... cmd,
    docker/podman exec [opts] CTR cmd, kubectl exec/debug ... -- cmd."""
    head = words[0].lower()
    if head in ("sh", "bash", "zsh") and len(words) > 2 and words[1] == "-c":
        return [words[2]]                            # the quoted script, parsed again by segments()
    if "--" in words and head in ("kubectl", "docker", "podman", "nerdctl", "crictl", "oc"):
        return words[words.index("--") + 1:]
    if head == "ip" and words[1:3] == ["netns", "exec"] and len(words) > 4:
        return words[4:]
    if head == "nsenter":
        i = 1
        while i < len(words) and words[i].startswith("-"):
            i += 2 if words[i] in ("-t", "--target") else 1
        return words[i:]
    if head in ("docker", "podman", "nerdctl") and len(words) > 2:
        j = 2 if words[1] == "compose" else 1
        if j < len(words) and words[j] == "exec":
            i = j + 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in ("-u", "--user", "-e", "--env", "-w", "--workdir") else 1
            return words[i + 1:]                     # skip the container/service name
    return []


def command_lines(md_text):
    """Command lines (prompt stripped, continuations joined) from the fenced code blocks."""
    for m in re.finditer(r"^```([^\n]*)\n(.*?)^```", md_text, re.S | re.M):
        lang = (m.group(1).strip().split() or [""])[0].lower()
        yield from _block_lines(lang, m.group(2))


def _block_lines(lang, body):
    is_cmd = lang in CMD_LANGS
    heredoc_end, pending = None, ""
    for raw in body.splitlines():
        if heredoc_end is not None:                  # here-document bodies are data, not commands
            if raw.strip() == heredoc_end:
                heredoc_end = None
            continue
        line = raw
        pm = PROMPT_RE.match(line)
        if pm:
            line = pm.group(1)
        elif not is_cmd and not pending:
            continue
        line = pending + line
        if line.rstrip().endswith("\\"):
            pending = line.rstrip()[:-1] + " "
            continue
        pending = ""
        hd = re.search(r"<<-?\s*['\"]?([A-Za-z_]+)['\"]?", line)
        if hd:
            heredoc_end = hd.group(1)
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        yield re.sub(r"\s+#\s.*$", "", stripped)     # drop a trailing "  # comment"


def _shell_words(line):
    """Shell-like tokens of one line, as lists split at unquoted | || && ; & ( ) — quotes are
    respected, so `grep -E 'apache|httpd'` stays one command. Unbalanced quotes fall back to a
    plain split on the same operators."""
    try:
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ""
        tokens = list(lex)
    except ValueError:
        return [part.split() for part in re.split(r"\|\||&&|\||;|&|\(|\)", line)]
    out, cur = [], []
    for t in tokens:
        if t in SPLIT_TOKENS:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    out.append(cur)
    return out


def segments(line, _depth=0):
    """Command word lists in a line: one per pipeline/list segment, plus commands run inside
    $(...), backticks, sh -c '...' and exec-style wrappers."""
    if _depth > 4:
        return
    inner = []

    def grab(m):
        inner.append(m.group(1) if m.group(1) is not None else m.group(2))
        return " _ "

    flat = SUBST_RE.sub(grab, line)                  # $(cmd) runs cmd, even inside double quotes
    for raw in _shell_words(flat):
        words = command_words(raw)
        while words:
            if " " in words[0]:                      # a quoted script: watch 'ss -s', sh -c "..."
                yield from segments(" ".join(words), _depth + 1)
                break
            if not WORD_RE.match(words[0]):
                break
            yield words
            words = command_words(_nested(words))
    for sub in inner:
        yield from segments(sub, _depth + 1)


def candidate_keys(words, sub_tools):
    """Most specific first: ['docker compose logs', 'docker compose', 'docker']."""
    low = normalize_head(words[0])
    if low not in sub_tools:
        return [low]
    value_flags = TOOL_VALUE_FLAGS_BY_TOOL.get(low, TOOL_VALUE_FLAGS)
    subs, i = [], 1
    while i < len(words) and len(subs) < 2:
        w = words[i]
        if w.startswith("-"):
            i += 2 if (w in value_flags and "=" not in w) else 1
            continue
        if not WORD_RE.match(w):
            break
        subs.append(w.lower())
        i += 1
    return [" ".join([low] + subs[:n]) for n in range(len(subs), 0, -1)] + [low]


# --------------------------------------------------------------------------- #
# cards
# --------------------------------------------------------------------------- #
META_RE = re.compile(r"^(Match|Instead of|Safety):\s*(.*)$")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def family_files(here):
    d = os.path.join(here, CARD_DIR)
    if not os.path.isdir(d):
        return []
    files = sorted(f for f in os.listdir(d) if f.endswith(".md") and f not in NOT_FAMILIES)
    order = os.path.join(d, "ORDER")
    if os.path.isfile(order):
        with open(order, encoding="utf-8") as f:
            wanted = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        files = [f for f in wanted if f in files] + [f for f in files if f not in wanted]
    return files


def parse_family(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    title_m = re.match(r"\s*#\s+(.+)", text)
    fam = {"file": os.path.basename(path), "title": title_m.group(1).strip() if title_m else path,
           "cards": []}
    parts = re.split(r"^### ", text, flags=re.M)
    fam["intro"] = re.sub(r"\A\s*#\s+.*\n", "", parts[0]).strip()
    for part in parts[1:]:
        head, _, rest = part.partition("\n")
        name, _, tagline = head.partition(" — ")
        meta, lines, body_start = {}, rest.split("\n"), 0
        for i, l in enumerate(lines):
            mm = META_RE.match(l.strip())
            if mm:
                meta[mm.group(1)] = mm.group(2).strip()
                body_start = i + 1
            elif l.strip():
                break
        name = name.strip().strip("`").strip()
        fam["cards"].append({
            "id": "cmd-" + slug(name), "name": name, "tagline": tagline.strip(),
            "family": fam["title"], "file": fam["file"],
            "keys": [k.strip().lower() for k in meta.get("Match", "").split(",") if k.strip()],
            "instead": meta.get("Instead of", "").strip(), "safety": meta.get("Safety", "").strip(),
            "body_md": "\n".join(lines[body_start:]).strip(),
        })
    return fam


def load_cards(here):
    families = [parse_family(os.path.join(here, CARD_DIR, f)) for f in family_files(here)]
    return families, [c for fam in families for c in fam["cards"]]


def key_index(cards):
    """match key -> card, and the tools that have subcommand-specific keys."""
    index, sub_tools = {}, set()
    for c in cards:
        for k in c["keys"]:
            index.setdefault(k, c)
            if " " in k:
                sub_tools.add(k.split()[0])
    return index, sub_tools


def match_text(md_text, index, sub_tools):
    """Cards used by the code blocks of a Markdown fragment, in first-use order."""
    seen, out = set(), []
    for line in command_lines(md_text):
        for words in segments(line):
            for k in candidate_keys(words, sub_tools):
                c = index.get(k)
                if c:
                    if c["id"] not in seen:
                        seen.add(c["id"])
                        out.append(c)
                    break
    return out


# --------------------------------------------------------------------------- #
# per-submodule boxes
# --------------------------------------------------------------------------- #
def _norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def _md_heading_text(s):
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return _norm(re.sub(r"[`*_]", "", s))


def h2_sections(md_text):
    """[(normalised heading text, section markdown)] for every '## ' heading outside fences."""
    out, cur_head, cur, fence = [], None, [], None
    for line in md_text.split("\n"):
        st = line.lstrip()
        if fence is None and st.startswith(("```", "~~~")):
            fence = st[:3]
        elif fence and st.startswith(fence):
            fence = None
        if fence is None and line.startswith("## "):
            if cur_head is not None:
                out.append((cur_head, "\n".join(cur)))
            cur_head, cur = _md_heading_text(line[3:].strip()), []
        elif cur_head is not None:
            cur.append(line)
    if cur_head is not None:
        out.append((cur_head, "\n".join(cur)))
    return out


def section_box(cards):
    """Collapsed box under a submodule heading. Only the card ids are stored (without the
    "cmd-" prefix); the page script draws the chips and copies the cards in when it opens,
    which keeps several hundred boxes small."""
    n = len(cards)
    ids = " ".join(c["id"][len("cmd-"):] for c in cards)
    return (f'<details class="cmd-sec no-index" data-cmds="{ids}">'
            f'<summary>🔍 Decode the {n} command{"s" if n != 1 else ""} used here: '
            f'what each one means and why it works</summary></details>')


def inject_boxes(body_html, md_text, index, sub_tools):
    """Put a box under each <h2> whose section runs decoded commands.
    Returns (html, [(card_id, h2_anchor_id)])."""
    queue = [(head, match_text(sec, index, sub_tools)) for head, sec in h2_sections(md_text)]
    uses = []

    def add(m):
        text = _norm(html.unescape(re.sub(r"<[^>]+>", "", m.group(2))))
        for i, (head, cards) in enumerate(queue):
            if head == text:
                del queue[:i + 1]
                if not cards:
                    return m.group(0)
                uses.extend((c["id"], m.group(1)) for c in cards)
                return m.group(0) + section_box(cards)
        return m.group(0)

    out = re.sub(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', add, body_html, flags=re.S)
    return out, uses


# --------------------------------------------------------------------------- #
# the Command Decoder page
# --------------------------------------------------------------------------- #
def decoder_markdown(here):
    families, cards = load_cards(here)
    intro_path = os.path.join(here, CARD_DIR, "INTRO.md")
    intro = ""
    if os.path.isfile(intro_path):
        with open(intro_path, encoding="utf-8-sig") as f:
            intro = re.sub(r"\A\s*#\s+.*\n", "", f.read()).strip()
    out = ["# Command Decoder", "",
           f'<p class="cmd-count"><strong>{len(cards)} command{"s" if len(cards) != 1 else ""} decoded in '
           f'{len(families)} famil{"ies" if len(families) != 1 else "y"}.</strong> '
           "Every submodule of the handbook opens with a collapsed <em>🔍 Decode the commands used in "
           "this submodule</em> box; opening it shows the cards below in place.</p>", "",
           intro, ""]
    for fam in families:
        out += [f"## {fam['title']}", "", fam["intro"], ""]
        for c in fam["cards"]:
            meta = []
            if c["instead"] and c["instead"] not in ("—", "-"):
                meta.append(f"<b>Use instead of:</b> {html.escape(c['instead'])}")
            if c["safety"]:
                meta.append(f"<b>Safety:</b> {html.escape(c['safety'])}")
            out += [f'<div class="cmd-card" id="{c["id"]}" markdown="1">', "",
                    f"### {c['name']} — {c['tagline']}" if c["tagline"] else f"### {c['name']}", ""]
            if meta:
                out += [f'<p class="cmd-meta">{" · ".join(meta)}</p>', ""]
            out += [c["body_md"], "", f'<p class="cmd-used" data-card="{c["id"]}"></p>', "", "</div>", ""]
    return "\n".join(out)


USED_IN_MAX = 15


def fill_used_in(body_html, used_in):
    """used_in: card id -> [(label, anchor)]; fills the empty <p class="cmd-used"> slots
    (at most USED_IN_MAX links, then "+N more", to bound the page size)."""
    def fill(m):
        links = used_in.get(m.group(1))
        if not links:
            return ""
        items = " · ".join(f'<a href="#{a}">{html.escape(t)}</a>' for t, a in links[:USED_IN_MAX])
        more = f" · +{len(links) - USED_IN_MAX} more" if len(links) > USED_IN_MAX else ""
        return f'<p class="cmd-used">Used in {len(links)} module{"s" if len(links) != 1 else ""}: {items}{more}</p>'
    return re.sub(r'<p class="cmd-used" data-card="([^"]+)"></p>', fill, body_html)


DECODER_CSS = """
.cmd-sec { position:relative; margin:4px 0 18px; padding:9px 14px; border-radius:12px; border:1px solid transparent;
  background: linear-gradient(var(--bg2), var(--bg2)) padding-box,
              linear-gradient(115deg, var(--tone, var(--accent)), color-mix(in srgb, var(--t-violet, #8b5cf6) 70%, transparent) 40%, var(--border) 75%) border-box; }
.cmd-sec > summary { cursor:pointer; font-weight:650; font-size:14px; }
.cmd-sec[open] { box-shadow:0 16px 40px -26px var(--tone, var(--accent)); }
.cmd-sec .cmd-chips { margin:8px 0 2px; display:flex; flex-wrap:wrap; gap:6px; font-size:0; }
.cmd-sec .cmd-chips a { text-decoration:none; background:none; font-size:13px; }
.cmd-sec .cmd-chips a code { display:inline-block; padding:2px 10px; border-radius:999px; font-size:12.8px; transition:transform .15s, box-shadow .15s;
  color:var(--fg); background:color-mix(in srgb, var(--tone, var(--accent)) 12%, var(--bg)); border:1px solid color-mix(in srgb, var(--tone, var(--accent)) 35%, var(--border)); }
.cmd-sec .cmd-chips a:hover code { transform:translateY(-1px); box-shadow:0 6px 14px -8px var(--tone, var(--accent)); }
.cmd-fill .cmd-card, .subm .cmd-card { margin:12px 0; background:color-mix(in srgb, var(--bg) 70%, transparent); }
.cmd-fill .cmd-card h4 { margin:12px 0 6px; font-size:16px; color:color-mix(in srgb, var(--tone, var(--accent)) 72%, var(--fg)); }
.cmd-fill .cmd-full { font-size:12.5px; font-weight:500; text-decoration:none; margin-left:8px; padding:1px 8px; border-radius:999px;
  border:1px solid var(--border); color:var(--fg-dim); }
.cmd-fill .cmd-full:hover { color:var(--fg); border-color:var(--tone, var(--accent)); }
.cmd-card { position:relative; overflow:hidden; scroll-margin-top:70px; margin:18px 0; padding:2px 20px 10px 22px; border-radius:14px;
  background:var(--card, var(--bg2)); border:1px solid var(--card-border, var(--border));
  box-shadow: inset 0 1px 0 var(--card-hi, transparent), 0 16px 34px -28px var(--shadow-strong); }
.cmd-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px;
  background:linear-gradient(var(--tone, var(--accent)), var(--t-violet, #8b5cf6)); }
.cmd-card > h3, .cmd-card > h4 { margin-top:14px; }
.cmd-card table { font-size:13.5px; }
.cmd-meta { font-size:13px; color:var(--fg-dim); margin:-4px 0 10px; display:flex; flex-wrap:wrap; gap:4px 14px; }
.cmd-meta b { color:var(--fg); font-weight:600; }
.cmd-used { font-size:12.8px; color:var(--fg-dim); border-top:1px dashed var(--border); padding-top:7px; margin-bottom:4px; }
.cmd-count { font-size:15px; }
"""

DECODER_SCRIPT = r"""<script>
/* Command Decoder: fill a submodule's box with the full cards the first time it is opened */
(function () {
  function fill(box) {
    if (box.querySelector('.cmd-fill')) return;
    var chips = document.createElement('p'), slot = document.createElement('div');
    chips.className = 'cmd-chips'; slot.className = 'cmd-fill';
    box.appendChild(chips); box.appendChild(slot);
    (box.getAttribute('data-cmds') || '').split(' ').forEach(function (key) {
      var id = key && 'cmd-' + key, card = key && document.getElementById(id);
      if (!card) return;
      var h = card.querySelector('h3'), a = document.createElement('a'), code = document.createElement('code');
      a.href = '#' + id;
      code.textContent = h ? h.textContent.split(' \u2014 ')[0] : key;
      a.appendChild(code); chips.appendChild(a);
      var copy = card.cloneNode(true);
      copy.removeAttribute('id');
      copy.querySelectorAll('[id]').forEach(function (n) { n.removeAttribute('id'); });
      copy.querySelectorAll('.cmd-used').forEach(function (n) { n.remove(); });
      var h3 = copy.querySelector('h3');
      if (h3) {                      /* an h4 inside the box keeps the page outline and search clean */
        var h4 = document.createElement('h4');
        h4.innerHTML = h3.innerHTML;
        var full = document.createElement('a');
        full.className = 'cmd-full'; full.href = '#' + id; full.title = 'Open this card in the Command Decoder';
        full.textContent = '↗ full card';
        h4.appendChild(full);
        h3.parentNode.replaceChild(h4, h3);
      }
      slot.appendChild(copy);
    });
  }
  document.addEventListener('toggle', function (e) {
    var t = e.target;
    if (t && t.classList && t.classList.contains('cmd-sec') && t.open) fill(t);
  }, true);

  /* "Used in" on each card, rebuilt from the boxes' id lists (keeps it out of the page source) */
  var MAX = 15;
  function usedIn() {
    var map = {};
    document.querySelectorAll('details.cmd-sec[data-cmds]').forEach(function (box) {
      var h2 = box.previousElementSibling, sec = box.closest('.mod-section');
      if (!sec || !h2 || h2.tagName !== 'H2' || !h2.id) return;
      var title = sec.getAttribute('data-title') || '';
      box.getAttribute('data-cmds').split(' ').forEach(function (k) {
        var list = map[k] || (map[k] = []);
        if (!list.some(function (x) { return x[0] === title; })) list.push([title, h2.id]);
      });
    });
    document.querySelectorAll('.cmd-used[data-card]').forEach(function (p) {
      var list = map[p.getAttribute('data-card').replace(/^cmd-/, '')];
      if (!list || !list.length) { p.remove(); return; }
      p.textContent = 'Used in ' + list.length + (list.length === 1 ? ' module: ' : ' modules: ');
      list.slice(0, MAX).forEach(function (x, i) {
        if (i) p.appendChild(document.createTextNode(' · '));
        var a = document.createElement('a'); a.href = '#' + x[1]; a.textContent = x[0]; p.appendChild(a);
      });
      if (list.length > MAX) p.appendChild(document.createTextNode(' · +' + (list.length - MAX) + ' more'));
      p.removeAttribute('data-card');
    });
  }
  var idle = window.requestIdleCallback || function (cb) { return setTimeout(cb, 200); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { idle(usedIn); });
  else idle(usedIn);
})();
</script>"""
DECODER_SCRIPT = minify_script(DECODER_SCRIPT)   # comments and indentation go (page_slim.py)


# --------------------------------------------------------------------------- #
# checks for card writers (read-only: parses Markdown, runs nothing)
# --------------------------------------------------------------------------- #
def handbook_texts(here):
    for f in sorted(os.listdir(here)):
        if re.fullmatch(r"\d\d-[\w.-]+\.md", f) or f == "README.md":
            with open(os.path.join(here, f), encoding="utf-8-sig") as fh:
                yield f, fh.read()


def coverage(here, cards, heads=None):
    """{head: [matched uses, unmatched uses, example unmatched line]} over all handbook modules."""
    index, sub_tools = key_index(cards)
    res = {}
    for _, text in handbook_texts(here):
        for line in command_lines(text):
            for words in segments(line):
                h = normalize_head(words[0])
                if heads is not None and h not in heads:
                    continue
                r = res.setdefault(h, [0, 0, ""])
                if any(k in index for k in candidate_keys(words, sub_tools)):
                    r[0] += 1
                else:
                    r[1] += 1
                    r[2] = r[2] or " ".join(words)[:120]
    return res


def check_family(here, path, heads):
    fam = parse_family(path)
    _, all_cards = load_cards(here)
    problems = []
    names = {}
    for c in all_cards:
        names.setdefault(c["id"], []).append(c["file"])
    keys = {}
    for c in all_cards:
        for k in c["keys"]:
            keys.setdefault(k, []).append(f'{c["file"]}:{c["name"]}')
    for c in fam["cards"]:
        if not c["keys"]:
            problems.append(f'{c["name"]}: no Match: keys')
        if not c["tagline"]:
            problems.append(f'{c["name"]}: heading has no " — tagline"')
        for part in REQUIRED_PARTS:
            if part not in c["body_md"]:
                problems.append(f'{c["name"]}: missing {part}')
        if len(names.get(c["id"], [])) > 1:
            problems.append(f'{c["name"]}: card name used more than once: {names[c["id"]]}')
        for k in c["keys"]:
            if len(keys[k]) > 1:
                problems.append(f'Match key "{k}" is claimed by several cards: {keys[k]}')
            if heads and k.split()[0] not in heads:
                problems.append(f'{c["name"]}: key "{k}" starts with "{k.split()[0]}", which this family does not own')
    words = sum(len(c["body_md"].split()) for c in fam["cards"])
    print(f'{fam["file"]}: "{fam["title"]}", {len(fam["cards"])} cards, {words} words, '
          f'{os.path.getsize(path) // 1024} KB')
    cov = coverage(here, all_cards, set(heads) if heads else None)
    missing = {h: r for h, r in cov.items() if r[1]}
    for h in heads or []:
        r = cov.get(h)
        if not r:
            continue
        print(f'  {h:28s} matched {r[0]:4d}  unmatched {r[1]:4d}' + (f'   e.g. {r[2]}' if r[1] else ""))
    for p in sorted(set(problems)):
        print("  PROBLEM: " + p)
    if not problems and not missing:
        print("  OK: every card is complete and every use of the owned commands is matched")
    return 1 if problems else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", help="a family file under commands/")
    ap.add_argument("--heads", default="", help="space-separated command words the family owns")
    ap.add_argument("--coverage", action="store_true", help="commands with unmatched uses (3+ unless --all)")
    ap.add_argument("--all", action="store_true", help="with --coverage: also list commands used once or twice")
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    if a.check:
        return check_family(here, a.check, [h.lower() for h in a.heads.split()])
    if a.coverage:
        _, cards = load_cards(here)
        cov = coverage(here, cards)
        for h, (ok, bad, ex) in sorted(cov.items(), key=lambda kv: -kv[1][1]):
            if bad and (ok or bad >= (1 if a.all else 3)):
                print(f"{h:28s} matched {ok:5d}  unmatched {bad:5d}  e.g. {ex}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

