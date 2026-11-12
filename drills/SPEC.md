# Decision drills: spec (7 November 2026)

A drill is an incident you play in the browser, the way DevOps Dream plays a CIO's year, but at
the on-call engineer's level. You get the symptom and the evidence, pick one of 3–4 moves, and a
"What happened?" panel explains the result and moves four meters. After the last step comes the
real story: what the engineers in the public post-mortem found and fixed, with a link to it.

It needs no Docker and no network, so drills work in the offline `index.html` and in the published
artifact (unlike the labs, which need the lab server).

## Rules

- **Community incidents only.** Every drill is adapted from a public post-mortem, incident report,
  GitHub issue or forum thread with a solution, never from the user's own incidents. The source is
  opened and read; the debrief must match it. Reddit, Stack Overflow and Server Fault are blocked
  here: never reach them by any workaround.
- **Decision points may be invented; the facts may not.** The choices are a teaching device; the
  "What really happened" debrief, dates, numbers and the fix come from the source.
- **Safe samples.** Generic names (ops, deploy, Sam, Priya), `example.com`, documentation addresses
  (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32). Never the real username or home
  path from this machine. Commands are shown, never run on this machine.
- **Own words.** Summaries are written fresh; at most one quote under 15 words per drill, in
  quotation marks with attribution.
- **Size.** The whole page is near the 16 MB artifact limit: keep each drill file under 9 KB and
  the player (CSS + JS) under 28 KB.

## Files

- `drills/<id>.json`: one drill per file (schema below). `<id>` matches `^[a-z0-9][a-z0-9-]{2,62}$`.
- `drills/ORDER`: one id per line, in the order shown on the page (unlisted files follow by level).
- `drills_site.py`: builds the virtual page `drills.md` (sidebar group "Labs", title
  "Decision drills", icon 🎯), exports `DRILLS_FILE, DRILLS_CSS, DRILLS_SCRIPT, drills_markdown,
  drill_count`, wired into `build_site.py` the same way as `labs_site.py`. Also a launchpad card on
  the home page.
- `tests/test_drills.py`: schema and safety checks (below).

## Drill schema

```json
{
  "id": "gitlab-2017-backup-restore",
  "title": "The backups that were never tested",
  "level": "L1",
  "track": "data",
  "topics": ["<roadmap.json node id>", "..."],
  "minutes": 6,
  "role": "You are the on-call database engineer for a busy Git hosting site.",
  "source": {
    "label": "GitLab.com database incident, 31 January 2017 (post-mortem)",
    "url": "https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/",
    "org": "GitLab",
    "date": "2017-01-31",
    "read_on": "2026-11-07"
  },
  "brief": "Markdown: the opening situation in 2-4 sentences.",
  "steps": [
    {
      "situation": "Markdown: what you see now (alert text, a user report, a graph described).",
      "evidence": "Optional plain text shown in a terminal frame: command + output, or a log excerpt.",
      "evidence_cmd": "Optional: the command that produced the evidence, e.g. df -h /var/opt",
      "choices": [
        {
          "text": "Short action, as the player would say it.",
          "verdict": "best",
          "effect": {"service": 10, "time": -5, "evidence": 15, "trust": 0},
          "why": "Markdown, 1-3 sentences: what this move does and why it helps or hurts here."
        }
      ]
    }
  ],
  "debrief": {
    "what_happened": "Markdown, 3-6 sentences: the real timeline, root cause and fix, from the source.",
    "lessons": ["2-4 one-line lessons, each something you would check or change at work"],
    "commands": ["0-6 commands the lesson relies on (the Command Decoder links them if it knows them)"]
  },
  "practise": {
    "labs": ["optional labs/rooms ids, e.g. 05-processes-signals"],
    "handbook": [{"file": "51-problems-databases-storage-backup.md", "heading": "an existing heading"}],
    "sites": [{"label": "SadServers: a broken-disk scenario", "url": "https://sadservers.com/scenarios"}]
  }
}
```

Constraints the tests enforce:

- `level` is one of `L0`…`L4`; `track` is one of the `roadmap.json` tracks; every `topics` id exists
  in `roadmap.json` (1–4 ids); `minutes` 3–15.
- 3–5 steps; each step has 3–4 choices; exactly one `best`, and verdicts are from
  `best | good | risky | bad`; every choice has `why`.
- `effect` keys are exactly `service`, `time`, `evidence`, `trust`, integers from -30 to 30. The
  `best` choice of a step has the highest total of that step.
- `source.url` is https, and `read_on` is a date. `practise.handbook` entries point at existing
  headings in existing modules; `practise.labs` ids exist in `labs/rooms/`.
- No real username or home path, no non-documentation IPv4 addresses, no secrets-looking strings.
- Every file is under 9 KB.

## The four meters

All start at 50 and are clamped to 0–100.

| Meter | Means | Goes up when you | Goes down when you |
|---|---|---|---|
| **Service** | users can work | restore service safely, roll back, fail over | make a change that widens the outage |
| **Time** | time to restore | take the shortest path that is still safe | wander, wait, or redo work |
| **Evidence** | you know why | read logs/metrics before acting, keep a timeline | guess, restart to "see if it helps", destroy evidence |
| **Trust** | team and users | communicate, escalate early, stay blameless | blame, hide, go silent, act alone on prod |

If **Service** or **Trust** reaches 0, the drill ends early ("The incident escalated past you")
and offers a retry, as DevOps Dream does when the board fires you.

## Player (page script)

- **Drill list:** grouped by level (L0 Fresher … L4 Senior/Lead). Each card shows title, track,
  minutes, source org and year, and your best result. Linkable as `#drill.<id>`.
- **Brief screen:** role, brief, the four meters, then "Start".
- **Each step:** situation, the evidence in the handbook's terminal frame, then the choices as
  buttons.
  - **After a pick:** the buttons lock, and the picked one shows its verdict colour (best green,
    good teal, risky amber, bad red). A "What happened?" panel shows the `why` and the deltas, and
    the meters animate.
  - **"Why not the others?"** is a collapsible panel listing every other choice's verdict and `why`.
  - **Next** stays disabled until a choice is made.
- **End screen:** the four meters, an overall score (average of the meters), a 1–3 star rating
  (3 = every step best), then the debrief:
  - what really happened, with the source link and date;
  - the lessons;
  - the commands;
  - "Practise this": the lab rooms, handbook sections and outside sites.
  - Buttons: "Play again", plus the next drill in the list.
- **Progress:** the best score per drill is kept in `localStorage`, every access wrapped in
  try/catch. The page works the same without it.
- **Design:**
  - uses the handbook's existing tokens, cards and terminal frame, in both the dark and the light
    theme;
  - keyboard: 1–4 pick a choice, Enter goes Next;
  - respects reduced motion;
  - works from 360 px wide.
- **No external requests, no `alert()`/`confirm()`.** Drill data is embedded once, as a JSON
  script tag.

## Not in scope here

Per-topic practice links in the map panel and module pages (a later step), and changes to the 3D
map scene.
