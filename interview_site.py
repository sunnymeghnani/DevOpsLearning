"""Interview practice pages for the website, generated from the interview/ folder.

interview/ stays the single source of truth (57 packs, README.md, SOURCES.md,
manifest.json). At build time this module turns it into five virtual handbook
pages, grouped by the stage each pack declares on its "Stage:" line:

    interview-guide.md        how to practise, the rubric, stage index, source ledger
    interview-fresher.md      "Foundation"              packs (01-20)
    interview-junior-mid.md   "Junior -> intermediate"  packs
    interview-senior.md       "Intermediate -> senior"  packs
    interview-every-stage.md  "All stages"              packs (career / learning honesty)

Inside a stage page: "## <handbook module title>" per topic (e.g. SSH & Remote
Access), "### Mnn-Q01" (main question) and "### Mnn-Q02" (twist) under it, answer
checkpoints and sources in collapsed <details> blocks. Every handbook module that
has a pack also gets a short "Interview practice" pointer appended.

Nothing here records completed work or scores; it only re-presents the pack.
"""
import json
import os
import re

PACK_DIR = "interview"

# (virtual file, sidebar title, icon, stage key or None for the guide)
INTERVIEW_PAGES = [
    ("interview-guide.md", "Interview Practice: How to Use", "🎤", None),
    ("interview-fresher.md", "Interview: Fresher", "🌱", "fresher"),
    ("interview-junior-mid.md", "Interview: Junior → Mid-level", "🌿", "junior-mid"),
    ("interview-senior.md", "Interview: Senior", "🌳", "senior"),
    ("interview-every-stage.md", "Interview: Every Stage", "🪜", "every"),
]
INTERVIEW_FILES = {f for f, *_ in INTERVIEW_PAGES}
GUIDE = "interview-guide.md"
STAGE_PAGE = {stage: f for f, _, _, stage in INTERVIEW_PAGES if stage}
STAGE_TITLE = {stage: t for _, t, _, stage in INTERVIEW_PAGES if stage}
STAGE_INTRO = {
    "fresher": "Foundation questions: name the layer, the resource or the execution context "
               "before reaching for a fix. Each pack then adds an intermediate follow-up.",
    "junior-mid": "Junior to mid-level questions: narrow competing hypotheses with evidence, "
                  "then extend the answer with risk and verification the way a senior would.",
    "senior": "Intermediate to senior decision-making: trade-offs, blast radius, rollback, "
              "data integrity and coordination under constraints.",
    "every": "Questions for every stage: explaining your learning path and experience honestly, "
             "then deepening the evidence behind each claim.",
}

INTERVIEW_CSS = """
.iv-answer,.iv-sources { border:1px solid var(--border); border-radius:8px; margin:10px 0; padding:10px 14px; }
.iv-answer summary,.iv-sources summary { cursor:pointer; font-weight:600; }
.iv-answer[open] { background:var(--bg2); }
.iv-meta { font-size:13.5px; color:var(--fg-dim); }
.iv-pointer { border-left:3px solid var(--accent); padding:8px 12px; background:var(--bg2); }
"""


def stage_of(stage_line):
    """Map a pack's own "Stage:" line to a site page."""
    s = (stage_line or "").strip().lower()
    if s.startswith("foundation"):
        return "fresher"
    if s.startswith("junior"):
        return "junior-mid"
    if s.startswith("intermediate"):
        return "senior"
    return "every"


def _fix_links(text):
    """Pack-relative links -> links the site builder can resolve to in-page anchors."""
    text = re.sub(r"\]\(\.\./(\d\d-[\w.-]+\.md)", r"](\1", text)           # handbook modules
    text = re.sub(r"\]\(SOURCES\.md#", f"]({GUIDE}#", text)                  # ledger entries
    text = re.sub(r"\]\(SOURCES\.md\)", f"]({GUIDE}#source-ledger)", text)
    text = re.sub(r"\]\(README\.md#", f"]({GUIDE}#", text)                   # rubric etc.
    text = re.sub(r"\]\(README\.md\)", f"]({GUIDE})", text)
    # research files are not part of the published page: name them instead of linking
    text = re.sub(r"\[([^\]]+)\]\(\.\./(research/[\w.-]+)\)", r"\1 (`\2` in the project folder)", text)
    return text


def _section(text, start_pat, end_pat=None):
    m = re.search(start_pat, text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    if end_pat:
        e = re.search(end_pat, rest, re.M)
        if e:
            rest = rest[:e.start()]
    return rest.strip("\n")


def parse_pack(path):
    """One interview/NN-*.md file -> dict of its parts (text kept verbatim)."""
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    fname = os.path.basename(path)
    head = re.match(r"#\s+(\d+)\s+—\s+Interview practice:\s+(.+)", text)
    ids = re.findall(r"^## (M\d{2}-Q\d{2}) ", text, re.M)
    stage_line = (re.search(r"^Stage:\s*(.+)$", text, re.M) or [None, ""])[1]
    prov_line = (re.search(r"^Provenance:\s*(.+)$", text, re.M) or [None, ""])[1]
    q1 = _section(text, r"^## " + re.escape(ids[0]) + r" .*$", r"^## |^<details>")
    q2 = _section(text, r"^## " + re.escape(ids[1]) + r" .*$", r"^## |^<details>")
    details = _section(text, r"^<details>\s*$", r"^</details>\s*$")
    sources = _section(text, r"^## Sources and limits\s*$")
    return {
        "file": fname, "num": head.group(1) if head else fname[:2],
        "scenario": head.group(2).strip() if head else fname,
        "ids": ids, "stage_line": stage_line.strip(), "stage": stage_of(stage_line),
        "provenance": prov_line.strip(), "q1": q1, "q2": q2,
        "details": details, "sources": sources,
    }


def load_packs(here):
    pack_dir = os.path.join(here, PACK_DIR)
    if not os.path.isdir(pack_dir):
        return []
    packs = [parse_pack(os.path.join(pack_dir, f))
             for f in sorted(os.listdir(pack_dir)) if re.fullmatch(r"\d\d-[\w.-]+\.md", f)]
    return [p for p in packs if len(p["ids"]) == 2]


def _answer_block(details):
    """<details> body: keep the <summary>, turn its ### labels into bold labels so the
    checkpoints stay hidden from the sidebar index."""
    body = re.sub(r"^### (.+)$", r"**\1**", details, flags=re.M)
    return f'<details class="iv-answer" markdown="1">\n{body.strip()}\n\n</details>'


def _stage_page(stage, packs, titles):
    out = [f"# {STAGE_TITLE[stage]}", "",
           STAGE_INTRO[stage], "",
           "Answer the main question aloud first, then the twist, and only then open the "
           f"answer checkpoints. Score yourself with the [practice rubric]({GUIDE}#practice-rubric). "
           "These are practice scenarios, not verified employer questions (only M10 adapts a "
           f"reported interview theme); see [how to use]({GUIDE}) for provenance. Nothing on this "
           "page records completed work, and the proposed labs have not been run.", "", "---", ""]
    for p in packs:
        topic = titles.get(p["file"], p["scenario"])
        out += [f"## {topic}", "",
                f'<p class="iv-meta">Scenario: <strong>{p["scenario"]}</strong> · '
                f'Stage: {p["stage_line"]}</p>', "",
                f"Handbook module: [{topic}]({p['file']}) · Provenance: {p['provenance']}", "",
                f"### {p['ids'][0]} — {p['scenario']}", "", _fix_links(p["q1"]), "",
                f"### {p['ids'][1]} — Interviewer twist", "", _fix_links(p["q2"]), "",
                _fix_links(_answer_block(p["details"])), "",
                '<details class="iv-sources" markdown="1">',
                "<summary>Sources and limits</summary>", "",
                _fix_links(p["sources"]), "", "</details>", ""]
    return "\n".join(out)


def _readme_section(here, name):
    with open(os.path.join(here, PACK_DIR, "README.md"), encoding="utf-8-sig") as f:
        text = f.read()
    return _section(text, r"^## " + re.escape(name) + r"\s*$", r"^## ")


def _guide_page(here, packs, titles):
    by_stage = {s: [p for p in packs if p["stage"] == s] for s in STAGE_PAGE}
    total_q = sum(len(p["ids"]) for p in packs)
    out = ["# Interview Practice: How to Use", "",
           f"**{len(packs)} module packs, {len(packs)} scenarios and {total_q} prompts**, one pack per "
           "handbook module, grouped here by the stage each pack declares. Every pack has a main "
           "question and a harder interviewer twist, then answer checkpoints, the reasoning behind "
           "the order, a common trap, a proposed verification exercise and a senior extension.", "",
           "Your learning path is still under construction: nothing here claims you completed a "
           "course, lab or production incident, and no scores or completion flags are recorded. "
           "The source files live in the `interview/` folder of the project.", "", "---", "",
           "## How to use it", "", _fix_links(_readme_section(here, "How to use it")), "",
           "## Practice rubric", "", _fix_links(_readme_section(here, "Practice rubric")), "",
           "## Stage index", ""]
    for stage, page in STAGE_PAGE.items():
        items = by_stage[stage]
        if not items:
            continue
        out += [f"### {STAGE_TITLE[stage]}", "", STAGE_INTRO[stage], "",
                "| Topic | Scenario | Questions |", "|---|---|---|"]
        for p in items:
            topic = titles.get(p["file"], p["scenario"])
            out.append(f"| [{topic}]({page}#{p['ids'][0].lower()}) | {p['scenario']} | "
                       f"{p['ids'][0]}, {p['ids'][1]} |")
        out.append("")
    out += ["## Sources and attribution", "", _fix_links(_readme_section(here, "Sources and attribution")), ""]
    # the source ledger: its intro + "Interview context" kept, entries as h4 (anchors, no sidebar noise)
    with open(os.path.join(here, PACK_DIR, "SOURCES.md"), encoding="utf-8-sig") as f:
        ledger = f.read()
    ledger = re.sub(r"\A\s*# .*\n", "", ledger, count=1)
    ledger = re.sub(r"^## Interview context\s*$", "### Interview context", ledger, flags=re.M)
    ledger = re.sub(r"^## ([A-Z]\d{2})\s*$", r"#### \1", ledger, flags=re.M)
    out += ["## Source ledger", "", _fix_links(ledger.strip()), ""]
    return "\n".join(out)


def interview_markdown(fname, here, titles):
    """Markdown text for one virtual interview page."""
    packs = load_packs(here)
    if fname == GUIDE:
        return _guide_page(here, packs, titles)
    stage = next(s for f, _, _, s in INTERVIEW_PAGES if f == fname)
    return _stage_page(stage, [p for p in packs if p["stage"] == stage], titles)


_PACK_CACHE = {}


def backlink_markdown(fname, here):
    """Short pointer appended to a handbook module that has an interview pack."""
    key = os.path.abspath(here)
    if key not in _PACK_CACHE:
        _PACK_CACHE[key] = {p["file"]: p for p in load_packs(here)}
    p = _PACK_CACHE[key].get(fname)
    if not p:
        return ""
    page, stage = STAGE_PAGE[p["stage"]], STAGE_TITLE[p["stage"]]
    return ("\n\n---\n\n"
            f'<p class="iv-pointer">🎤 <strong>Interview practice for this module</strong> '
            f"({stage.replace('Interview: ', '')}): "
            f'<a href="{page}#{p["ids"][0].lower()}">{p["ids"][0]} — {p["scenario"]}</a> '
            f"and its interviewer twist.</p>\n")


def section_id_for(fname):
    """Same rule as build_site.section_id for non-numbered files: 'interview-fresher.md' -> 'm-interview-fresher'."""
    stem = os.path.splitext(fname)[0].lower()
    return "m-" + (re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "x")


def manifest_summary(here):
    """(scenario_count, prompt_count) from interview/manifest.json, for checks."""
    with open(os.path.join(here, PACK_DIR, "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    return m.get("scenario_count"), m.get("prompt_count")
