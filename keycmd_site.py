"""Key commands explained: every command in a map topic's "Key commands" list gets a one-line
"what this exact invocation does", a safety badge and "Decode ›" links to its Command Decoder cards.

The lines live in keycmd_notes.tsv (command <TAB> safety <TAB> summary), keyed by the exact command
string from roadmap.json, so they can be reviewed on their own. The cards come from
command_decoder's own matcher (the same one that fills the submodule decode boxes), so nothing is
executed. annotate() stores per topic

    node["cmdx"] = [[summary, safety, "card-id card-id"], ...]     # parallel to node["commands"]

(card ids without their "cmd-" prefix, the main command first). The map's cmdList() renders them in
the topic panel and, through window.__map.cmdList, on focus_site.py's end card.

    python3 keycmd_site.py            # lists key commands without a line, and lines nobody uses
"""
import os
import sys

import command_decoder as cd
from page_slim import minify_css

NOTES_FILE = "keycmd_notes.tsv"
LEVELS = ("ro", "load", "ch", "dg")
MAX_SUMMARY = 110
# cards that only shape another command's output (or wrap it): the Decode link prefers the command they serve
HELPER_CARDS = {"cmd-head", "cmd-tail", "cmd-grep", "cmd-sort-uniq", "cmd-jq-yq", "cmd-echo-printf",
                "cmd-cd-pwd-type-which-history", "cmd-for-while-read-case", "cmd-bash-sh",
                "cmd-select-object-where-object-sort-object"}


def load_notes(here):
    """{command: (safety, summary)}; ValueError on a malformed, duplicate or over-long line."""
    notes = {}
    path = os.path.join(here, NOTES_FILE)
    with open(path, encoding="utf-8") as f:
        for no, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3 or not all(p.strip() for p in parts):
                raise ValueError(f"{NOTES_FILE}:{no}: expected 'command<TAB>safety<TAB>summary'")
            cmd, level, summary = parts
            if level not in LEVELS:
                raise ValueError(f"{NOTES_FILE}:{no}: safety {level!r} is not one of {', '.join(LEVELS)}")
            if len(summary) > MAX_SUMMARY:
                raise ValueError(f"{NOTES_FILE}:{no}: summary is {len(summary)} characters (at most {MAX_SUMMARY})")
            if cmd in notes:
                raise ValueError(f"{NOTES_FILE}:{no}: duplicate command {cmd!r}")
            notes[cmd] = (level, summary)
    return notes


def command_cards(cmd, index, sub_tools):
    """The decoder cards a key command uses, the main command first."""
    cards = cd.match_text("```bash\n" + cmd + "\n```", index, sub_tools)
    main = [c for c in cards if c["id"] not in HELPER_CARDS]
    return main + [c for c in cards if c["id"] in HELPER_CARDS]


def annotate(roadmap, here):
    """Add node["cmdx"] to every topic with key commands. Returns (missing commands, unused note lines)."""
    notes = load_notes(here)
    _, cards = cd.load_cards(here)
    index, sub_tools = cd.key_index(cards)
    missing, used = [], set()
    for n in roadmap.get("nodes") or []:
        cmds = n.get("commands") or []
        if not cmds:
            continue
        rows = []
        for c in cmds:
            c = str(c)
            note = notes.get(c)
            if not note:
                missing.append((n.get("id"), c))
                continue
            used.add(c)
            ids = " ".join(x["id"][len("cmd-"):] for x in command_cards(c, index, sub_tools))
            rows.append([note[1], note[0], ids])
        if len(rows) == len(cmds):
            n["cmdx"] = rows
    return missing, sorted(set(notes) - used)


KEYCMD_CSS = """
/* key commands explained (keycmd_site.py): command, then what it does, a safety badge and Decode links */
.kc { margin: 0 0 9px; }
.kc .mp-cmd { margin: 0; }
.kc-meta { margin: 3px 2px 0 6px; font-size: 12.8px; line-height: 1.45; color: var(--fg); }
.kc-b { display: inline-block; margin: 0 6px 0 4px; padding: 0 7px; border-radius: 999px; font-size: 11px; font-weight: 600;
  line-height: 17px; white-space: nowrap; border: 1px solid var(--border); color: var(--fg-dim); background: var(--bg3); vertical-align: 1px; }
.kc-ro { color: var(--accent2); border-color: color-mix(in srgb, var(--accent2) 45%, transparent); background: color-mix(in srgb, var(--accent2) 10%, transparent); }
.kc-ch { color: var(--fg); background: var(--mark); border-color: transparent; }
.kc-dg { color: var(--danger); border-color: color-mix(in srgb, var(--danger) 55%, transparent); background: color-mix(in srgb, var(--danger) 10%, transparent); }
.kc-load { border-style: dashed; }
.kc-d { font-size: 12px; white-space: nowrap; margin-right: 6px; }
.kc-d + .kc-d { color: var(--fg-dim); }
@media print { .kc-d { display: none; } }
"""
KEYCMD_CSS = minify_css(KEYCMD_CSS)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    import json
    with open(os.path.join(here, "roadmap.json"), encoding="utf-8-sig") as f:
        roadmap = json.load(f)
    missing, unused = annotate(roadmap, here)
    for topic, cmd in missing:
        print(f"missing: {topic}: {cmd}")
    for cmd in unused:
        print(f"unused line: {cmd}")
    print(f"{len(missing)} missing, {len(unused)} unused")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
