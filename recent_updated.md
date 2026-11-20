# Recent updates — your DevOps learning handbook

Updated: 4 October 2026.

This log summarizes the recent source integration, incident expansion and interview
practice work. It does not claim that the entire existing handbook was created in
this update. For the broader project history, see [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md).

This remains your personal learning path under construction. Examples are not your
completed work, and proposed labs have not been executed on your machine.

## 1. Connected sources to the handbook

- Connected the saved research to the relevant problem libraries in modules 41–52,
  Sources & Verification (56), and the course map.
- Added an offline source index with text, domain and source-status filters.
- Kept discovery/search links distinct from actual thread readings, incomplete
  excerpts, historical research checks and narrowly scoped official-documentation checks.
- Fixed filtering so hidden discovery references do not incorrectly match a
  selected source-reading status.
- Preserved the original research catalogs rather than silently relabeling every
  historical source as newly verified.
- Corrected the blanket claim that Reddit, Stack Overflow and Server Fault are
  universally inaccessible. Access limitations are now recorded per reading/run.

The current index contains **488 saved research entries, 1,602 source associations
and 1,423 distinct URLs across 12 topic domains**. Reused links count as multiple
associations; these numbers are not counts of newly verified fixes.

Key files: [source_catalog.py](source_catalog.py), [build_site.py](build_site.py),
[56-sources-and-verification.md](56-sources-and-verification.md),
[research/source-checks.json](research/source-checks.json).

## 2. Added real incident questions and reported solutions

- Added 12 initial case readings: seven Stack Overflow and five Reddit discussions.
- Added another 16 cases: nine community threads, six first-party production
  postmortems and one vendor remediation advisory.
- Total: **28 curated cases**, connected to their relevant problem libraries and
  a new incident directory in module 56.
- The 16 expanded cases include a practical question, environment/version context,
  deciding evidence, reported fix or mitigation, outcome limits, prevention and a
  proposed verification exercise. Their answers are expandable in the website.
- Distinguished author-reported recovery, upstream fixes, workarounds, partial
  improvements and unresolved concerns. For example, the Terraform provider
  correction does not establish that its unexpected destructive plan was resolved.

Topics include Dokploy routing labels, Traefik/Docker compatibility, Apache port
ownership, Docker startup failures, Kubernetes, Wazuh agent connectivity, CI/CD,
Terraform, Loki and database recovery. Historical production accounts include
GitLab, Resend, Cloudflare, Slack and GitHub.

The collection contains 19 retrieved community threads, seven first-party
reports/advisories and two excerpt-only Reddit readings. These are historical
reported incidents, **not a live outage feed or fixes reproduced on your systems**.

Case records: [research/community-threads.json](research/community-threads.json)
and [research/community-incidents.json](research/community-incidents.json).

[Open the incident directory on your existing local server](http://localhost:8173/index.html?v=3#m56-incident-questions-and-documented-resolutions).

## 3. Created a separate module-wise interview folder

Created [interview/](interview/README.md) for you to integrate into the website later.

- **56 module packs**, matching the filenames of handbook modules 01–56.
- **56 scenarios and 112 prompts**: one main question and one harder follow-up per pack.
- Each pack includes answer checkpoints, why the approach makes sense, common
  mistakes, proposed verification and a senior-level risk/rollback extension.
- Added a self-assessment rubric without filling in scores or completion flags.
- Linked Reddit interview discussions, a GitHub practice collection, Stack Overflow
  troubleshooting threads, upstream issues, official documentation and postmortems.
- Labeled provenance honestly: one scenario adapts a Reddit-reported interview
  theme; the other 55 are original practice scenarios. They are not advertised as
  verified questions asked by particular employers.

Start with [interview/README.md](interview/README.md). Source provenance is in
[interview/SOURCES.md](interview/SOURCES.md). Stable filenames, question IDs and
source mappings are in [interview/manifest.json](interview/manifest.json).

**The interview packs are not registered in the website or the course-progress map.**
The Markdown files contain the questions; the manifest is metadata for later integration.

## 4. Rebuilt the local site and verified the additions

Rebuilt [index.html](index.html) and [artifact.html](artifact.html), and updated
[README.md](README.md) and [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md).

Results from the latest implementation verification, before this log was added:

- Site build: 57 modules, 123 map topics, 976 resolved handbook/map links, no build warnings.
- **All 14 automated tests passed**, covering source classifications, incident links,
  expandable answers, internal anchors, offline assets, JavaScript syntax, map
  ordering, interview coverage, unique prompt IDs, local links and provenance.
- Browser checks on port **8173** verified the incident directory, the new Dokploy
  case, its expandable answer and the seven-entry first-party-report filter.
- No browser console errors were observed during that check.
- Publication scan: zero personal/secret findings and zero external resource loads.
  Six historical non-documentation IP literals remained listed by the scanner;
  this is not a claim that the scanner found no items of any kind.
- The map displayed **0/123 done**. No learning-completion action was taken.

Tests: [tests/test_source_integration.py](tests/test_source_integration.py) and
[tests/test_interview_pack.py](tests/test_interview_pack.py).

These checks validate the generated site and content structure. They do not execute
the handbook's server commands, reproduce every incident or verify every external URL.

## 5. What was left unchanged or remains for later

- Your existing server on port 8173 was used; no server restart was needed for these checks.
- Your learning progress was not marked complete or reset.
- The interview website integration is left to you, as requested.
- The previously published remote artifact was **not updated**. Rebuilding the local
  `artifact.html` is not the same as publishing it online.
- This log itself is a standalone project file, not a newly registered website module.

For future updates, append a dated entry describing the change, affected files,
verification performed and any remaining limitations. Do not carry old test results
forward as if they verified new changes.

## 6. Integrated the interview packs into the website (4 October 2026, later)

At your request, the interview packs are now part of the website instead of a standalone folder.

- New sidebar group **Interview practice**, right after "Start here":
  - **Interview Practice: How to Use**: how to practise, the self-assessment rubric, a stage index and the full source ledger.
  - **Interview: Fresher**: the 20 "Foundation" packs (01–20), one entry per topic, e.g. Fresher → SSH & Remote Access, Users & Permissions, Packages, DNS, Processes.
  - **Interview: Junior → Mid-level**: the 24 "Junior → intermediate" packs (playbooks, learn modules, problem libraries).
  - **Interview: Senior**: the 8 "Intermediate → senior" packs.
  - **Interview: Every Stage**: the 4 "All stages" packs (roadmap, career ladder, practice, sources).
- Each pack is placed by its own `Stage:` line; nothing was re-levelled by hand.
- Under each topic: scenario and provenance line, `Mnn-Q01` main question, `Mnn-Q02` interviewer twist, then **answer checkpoints and sources in collapsed blocks**. Checkpoint labels are not sidebar entries, so answers are not spoiled by the index.
- Every handbook module that has a pack ends with a short "Interview practice for this module" pointer to its question.
- `interview/` stays the single source: edit the packs there and run `python3 build_site.py`. The pages are generated by the new `interview_site.py`; no new numbered modules were added.

Affected files: `interview_site.py` (new), `build_site.py` (import, sidebar group, render hook, CSS; backup in `research/build_site.before-interview.py`), `tests/test_interview_pack.py`, `interview/README.md`, `README.md`, `PROJECT-SUMMARY.md`, `index.html`, `artifact.html`.

Verification performed for this change:

- `python3 build_site.py`: 62 modules (57 files + 5 generated interview pages), 123 map topics, 976 map links resolved, no warnings.
- `python3 -m unittest discover -s tests -v`: **15 tests passed**. The old assertion that interview questions must *not* appear in the site was replaced by checks that all 112 prompt IDs appear in both outputs, that there are 56 collapsed answer blocks, and (new test) that every pack sits on the page matching its declared stage and nowhere else.
- In the built page: 112 distinct prompt IDs, 56 answer blocks, 56 source blocks, 56 handbook pointers; no unresolved internal `.md` links (the only `.md` URLs left are four external GitHub links).
- Browser check on the existing 8173 server (no restart): the sidebar shows the new group, the Fresher page lists 20 topics, the SSH entry shows Q01, Q02 and a collapsed answer, and module 09's pointer links to M09-Q01. No console errors. Screenshots from the in-app pane came back blank during this check (a pane capture issue; the DOM checks above passed).

Limits: the question content itself was not rewritten or re-reviewed in this step; it is presented as authored in `interview/`. No progress, scores or completion flags were set. The published artifact was **not** updated by this change.

## 7. Visual refresh of the reading area (4 October 2026, evening)

At your request ("3D looks great but the content UI is looking okay; give it more effect"), the pages now share the 3D map's look. This is presentation only: text, headings, anchors, the sidebar entries, search and the text that **copy** puts on the clipboard are unchanged.

- **Depth and colour:**
  - a soft ambient glow drifts behind the page;
  - the top bar and sidebar are frosted glass, and a light beam travels along the top bar's edge;
  - a thin bar under the top bar shows reading progress through the current module, and the back-to-top button shows the same progress as a ring.
- **One colour tone per sidebar group**, repeated in that group's modules:
  - Start here: blue;
  - Interview practice: violet;
  - Real incidents & playbooks: amber;
  - Real-world problems & OSS toolbox: rose;
  - Learn: teal;
  - Command reference: sky.
- **Module hero:** each module opens with a card holding:
  - a 3D icon tile that floats gently and tilts towards the mouse;
  - a perspective grid like the map's floors;
  - the group name;
  - stats: submodules (topics on the interview pages, families on the decoder page), commands decoded and estimated reading time.
- **Submodule cards:** every `##` section is a glass card that fades in as it scrolls into view. Its heading has a glowing marker, and each step heading (`###`) has a timeline dot.
- **Code as terminal windows (dark in both themes):**
  - ●●● window dots and a language label (BASH, YAML, OUTPUT, TERMINAL …);
  - shell comments are dimmed, `$ command` lines in sample output are bold with a green prompt, and `← notes` in outputs are highlighted;
  - the frame glows on hover.
- **Other elements:**
  - tables have rounded frames, toned headers and row hover;
  - quotes that start with ⚠️ / ✅ / 💡 / 🚨 / ℹ️ become coloured callouts;
  - collapsible blocks have an animated arrow.
- **Home page:** the map banner has a small CSS-3D tower spinning in it, plus a launchpad of six quick-entry cards that tilt and light up under the mouse. The cards link to the Command Decoder, the Apache vs Dokploy case, Who owns this port?, Learn Linux, Interview practice and the Practice Arena.
- **Motion:** all of it stops when the operating system asks for reduced motion, and printing shows everything without effects.

- **Fixed (your report: "when I expand one topic and try to collapse it, it never works"):**
  - **Sidebar:** clicking a module always re-expanded it, and the scroll tracker re-expanded the module being read. Now:
    - clicking a collapsed module expands it and jumps there, as before;
    - clicking an expanded module, or its ▸ arrow, collapses it without moving the page;
    - the arrow alone only toggles, and it has a larger click area;
    - a module you collapsed stays collapsed while you scroll through it, and the sidebar no longer scrolls to a link hidden inside a collapsed module;
    - the button's open/closed state (`aria-expanded`) is announced to screen readers.
  - **3D map:** clicking the open topic again, on the canvas or in the List view, now closes its panel.
  - The collapsible blocks inside pages (answer checkpoints, sources, the decode boxes) already opened and closed correctly; they were checked and left as they were.

Affected files: `site_ui.py` (new: build-time decoration, CSS and script), `build_site.py` (hooks, hero, launchpad, sidebar tones, the collapse fix; backup in `research/build_site.before-ui.py`), `command_decoder.py` (box and card styling), `tests/test_site_ui.py` (new), `index.html`, `artifact.html`.

Verification performed for this change:

- `python3 build_site.py`: 63 modules, no warnings, about 12.9 MB per output (the visual layer adds about 0.2 MB; the artifact limit is 16 MB).
- `python3 -m unittest tests.test_site_ui`: 7 tests passed, including a regression test for the collapse fix. They check that:
  - the code text is identical before and after decoration in four large modules;
  - comments, prompts and notes are marked;
  - each module's `##` sections become balanced cards;
  - every module has a hero and a tone;
  - the artifact contract still holds (title first, no document tags, no external scripts).
- **Built page:** all 63 modules have exactly one card per `##` section (recounted after the decoder page was switched to cards).
- **Browser (8173):**
  - screenshots of the home page in both themes, Network, the Apache case, Interview: Fresher and the Command Decoder;
  - copied code contains no markup;
  - a sidebar jump lands the heading just below the top bar (68 px vs a 54 px bar);
  - the 3D map is unchanged and there are no console errors;
  - collapse fix, checked by clicking in the page:
    - sidebar Network: the name expands it and jumps, the name again collapses it, the arrow expands it and the arrow again collapses it, with the scroll position unchanged on both arrow clicks;
    - map List view: the first click opens a topic, the second closes it, the third opens it again.
- Full suite `python3 -m unittest discover -s tests`: 33 tests, 32 passed. The one failure is the Command Decoder check that all 14 family files exist; their writers are still running.

Limits:
- The in-app browser pane was hidden during the check, so the browser paused the animations (fade-in, progress bar, tilt). They were checked in code and through screenshots, not watched live.
- Performance on the full 63-module page was not profiled.
- The published artifact was **not** updated.

## 8. Independent QA pass and fixes (4 October 2026, night)

At your request ("run one more agent to check all the features ... like I found out 2–3 times"), a separate QA agent tested the site for about 17 minutes in a headless Chrome. It used real mouse and keyboard input and a throwaway browser profile on localhost only, and it changed no project files.

**What it found and what was fixed**

- **Broken (fixed): jumps to a whole module landed in the previous module.**
  - **Where:** clicking a module name in the sidebar, the home launch cards, and in-page links to `#mNN`. The second click landed correctly.
  - **Cause:** modules are drawn lazily (`content-visibility: auto`) at an estimated height. The modules around the target snapped to their real height a frame after the page's single re-align.
  - **Fix:** every jump, and every native `#…` link (via `hashchange`) and deep link on load, now keeps re-aligning until the target has been still for 350 ms, capped at 2.5 s. Any wheel, touch, key or pointer input cancels this at once, so it never fights your own scrolling.
- **Cosmetic (fixed): a `favicon.ico` 404 on every load.** The offline page now carries an inline 🧰 icon; the artifact keeps the icon its host sets.
- **Cosmetic (adjusted): the 3D map's track chips were cut off at 1440 px.**
  - **First attempt:** letting the row wrap made the legend 118 px tall, which is worse.
  - **What it does now:** it stays one scrollable row (47 px), and a fade on the right edge shows more chips are there until you reach the end.
- **Noted, not changed:** one 1.7-second busy period right after load on the 13–14 MB page. It was not profiled further.

**What it verified as working:**

- All 9,071 in-page links resolve, there are no duplicate ids, and all 976 map study links resolve.
- No JavaScript errors in any test.
- **Sidebar:** expand and collapse, including the earlier fix, scroll highlighting, and the drawer at 850 px.
- **Search:** the `/` shortcut, arrow keys, Enter and Escape, and the switch to "Both" for hits hidden by the On-prem/Cloud selector.
- **Theme and selector:** the theme persists, and the On-prem/Cloud selector hides 32 blocks and 10 sidebar entries and filters the map.
- **Small controls:** copy gives plain text; the progress bar and back-to-top work.
- **3D map:**
  - opening and closing restores the scroll position;
  - hovering in 3D and Flat 2D hides no topic or edge, which rules out the earlier bug;
  - clicking an open topic again closes it;
  - Flat 2D, List view, orbit/zoom/keys, guided path, filters and map search work;
  - the map's handbook links land correctly.
- **Decode boxes:** they open, close and reopen cleanly, and "↗ full card" jumps to the card.
- **Layout:** no horizontal scroll at 850, 1024 or 1920 px, and reduced motion works.

**Not covered by the QA pass:** the home tilt cards, the interview collapsibles, the Sources page filters and `artifact.html`. The guided path's ◀ Previous and ✕ End were inconclusive.

**Size housekeeping done at the same time**

The Command Decoder makes the page larger, and claude.ai artifacts have a 16 MB limit:

- **Boxes:** each submodule box now stores only the ids of its command cards. The page script draws the chips and copies the cards in when the box is opened. 448 boxes went from 337 KB to 111 KB.
- **"Used in" lines:** each card's line is now built by the page script from those boxes after load, instead of being stored in the page (about 110 KB saved, more as families are added). It lists at most 15 modules, then "+N more".
- **Result:** the page is 14.07 MB with 187 cards.

Affected files: `build_site.py` (jump settling, hash/load handlers, favicon, map legend; backup in `research/build_site.before-ui.py`), `site_ui.py` (legend fade), `command_decoder.py` (slim boxes, runtime "Used in"; backup of the earlier matcher in `research/command_decoder.before-shlex.py`), `tests/test_site_ui.py`, `tests/test_command_decoder.py`, `index.html`, `artifact.html`.

Verification performed for these fixes:

- **Headless Chrome, real clicks:**
  - sidebar jumps to m05, m12, m02, m40, m55, m30 and m46 all land at 67–68 px with the right module highlighted;
  - the launch card to #m54 and `location.hash = '#m30'` land at 68 px;
  - the QA agent's own original jump test now passes on the first try.
- An earlier run of my test missed m12 and m02. Checking what was under the mouse showed the click had landed on the neighbouring sidebar button while the sidebar was still scrolling, so the miss came from the test, not the page.
- Decode box: 3 chips and 3 cards on open, close and reopen work, and no ids are duplicated.
- "Used in" for `mtr` lists 6 modules with valid links; there are no console errors and no favicon 404.
- `python3 -m unittest discover -s tests`: all tests pass except the Command Decoder check that all 14 family files exist, because families are still being written.

Limits: the 1.7 s post-load task was not investigated. The published artifact was **not** updated.

## 9. Docker instead of the Python server (4 October 2026, night)

At your request ("rather than running python script can you make dockerization"), Docker now both builds the site and serves it on the same address, http://localhost:8173. See `DOCKER.md`.

- **`Dockerfile`, three stages:**
  - **Build** (`python:3.12-slim` + `markdown==3.5.2`, the same as the local build): runs `build_site.py` and the unit tests as a gate, then makes gzip copies.
  - **Serve** (`nginxinc/nginx-unprivileged:stable-alpine`): serves only the two pages.
  - **Export:** `docker build --target export --output type=local,dest=. .` writes `index.html` and `artifact.html` back into the folder.
- **`compose.yaml`:**
  - published on `127.0.0.1:8173` only, restarting `unless-stopped`;
  - non-root on a read-only root filesystem, with a tmpfs for `/tmp`, all capabilities dropped and `no-new-privileges`;
  - health check on `/healthz`.
- **`docker/nginx.conf`:**
  - serves the pre-compressed page: 4.1 MB on the wire instead of 14.5 MB;
  - `Cache-Control: no-cache`, so a rebuild shows on the next refresh;
  - `nosniff`, `no-referrer`, and no nginx version in responses.
- **`.dockerignore`:** only what the build and tests read goes in. Backups, briefs and notes stay out.
- **Server switch:** the in-app preview now runs `docker compose up` (`handbook-docker` in `.claude/launch.json`). The old `python3 -m http.server 8173` was stopped.

Affected files: `Dockerfile`, `compose.yaml`, `docker/nginx.conf`, `.dockerignore`, `DOCKER.md` (all new), `.claude/launch.json`.

Verification performed:

- `docker compose build --build-arg RUN_TESTS=false` succeeded, producing 63 modules with no warnings and a 14,155 KB page, the same as the local build. The test gate was skipped for this first build because 4 Command Decoder families were still being written, and the "all families exist" test fails until then.
- The container is `Up (healthy)` on `127.0.0.1:8173->8080`:
  - `/index.html` with gzip sent 4,077,150 bytes (`Content-Encoding: gzip`, `Cache-Control: no-cache`); without gzip, 14,495,067 bytes;
  - `/healthz` answers `ok`, and project source files return 404;
  - the response headers show `Server: nginx` without a version.
- **In the browser:** 63 modules, 294 decoder cards and 505 decode boxes; the 3D map loads and there are no console errors.
- `docker build --target export` wrote an `index.html` that is byte-identical to the local `python3 build_site.py` output.

Limits:
- The image has not yet been built with the test gate on. That happens after the last decoder families land.
- `stable-alpine` is a moving tag: rebuilds pick up nginx security updates, but they are not bit-for-bit reproducible.
- The container runs in the foreground under the in-app preview. For a service that stays up after reboots, run `docker compose up -d` yourself.

## 10. Command Decoder, handbook corrections and a CHECKPOINT (4 October 2026, 20:50)

Your request: for every module and every submodule, explain each command: what it means, why it is effective, and what weaker command people reach for first (your example: `ping 8.8.8.8` versus `mtr`). This entry also marks a **checkpoint**: the work pauses here and continues later (resume checklist at the end).

**What was built**

- **A new page, 🔍 Command Decoder: What & Why** (sidebar group "Start here"), generated from `commands/` by the new `command_decoder.py`.
- **Each card follows one structure:**
  - in one line;
  - "Read the command": a real handbook invocation, flag by flag;
  - what the output tells you;
  - why it is effective;
  - compared with the command people reach for first, including what that one *does* show;
  - the trap;
  - the next step;
  - plus a safety label (read-only or changes state).

  Example: `ping` does print an end-to-end loss figure but cannot say *where* packets are lost; `mtr` shows the hop where loss starts.
- **A box in every submodule:** each `##` that runs commands opens with a collapsed "🔍 Decode the N commands used here" box. Opening it shows the chips and copies in the full cards; each card also lists the modules that use it.
- **The matcher** reads code blocks like a shell:
  - quotes are respected;
  - `$(…)`, `sh -c '…'`, `ip netns exec`, `docker`/`kubectl exec` and `nsenter` are followed into;
  - wrappers such as `sudo` and `watch` are skipped;
  - subcommands pick their own card, most specific first (`docker compose logs` before `docker`);
  - per-tool rules cover `ip -s`, `systemctl --user`, `iptables -C CHAIN` and `restic -r REPO`;
  - PowerShell aliases (`Sort`, `Select`, `Where`) map to their cmdlets.

  Nothing is executed.

**Status at the checkpoint: 14 of 15 families done, 413 cards**

| Family | Cards |
|---|---|
| Network | 34 |
| DNS, HTTP, TLS & web servers | 25 |
| Firewalls & intrusion blocking | 12 |
| Processes, CPU & memory | 28 |
| Disk, filesystems & storage | 28 |
| systemd, logs, time, kernel & boot | 38 |
| Users, permissions, SSH & hardening | 29 |
| Packages, secrets & supply chain | 20 |
| Reading output: text, files & JSON | 27 |
| Docker, Compose, Swarm & runtimes | 34 |
| Kubernetes & GitOps | 39 |
| Cloud, IaC, Proxmox & CI/CD | 39 |
| Databases, backups & monitoring | 24 |
| Windows & macOS | 36 |
| **Shell building blocks** (echo, cp/mv/install, loops, `set -euo pipefail`, export, `bash -x`, python3) | **in progress** (about 10 cards; started 20:37) |

Every finished family passes its checker: each use of its commands in the handbook is matched by a card. The two exceptions are a bash function called `log` and a few rare commands without a card (for example patronictl, mongosh, sqlite3, rabbitmqctl, nettop and remoting cmdlets).

**Handbook corrections found while writing the cards**

These were verified and fixed; each original is in `research/*.before-*.md`.

| Module | Was | Now |
|---|---|---|
| 46 Kubernetes problems §11.2 | `helm upgrade --dry-run=server` shown failing with "field is immutable" | Helm's dry run never reaches the API server; the page uses `helm template … \| kubectl apply --dry-run=server -f -` |
| 01 Storage & Disk §8 | `mount -o remount,soft,timeo=30` | NFS refuses to change soft/timeo on a remount: unmount and mount again; `soft` can lose writes |
| 25 Site Down (Dependency row) | `pg_isready` showing `too many clients` | pg_isready still says "accepting" on a full server; that error is in the app log (as its Step 16 says) |
| 44 Docker/Swarm problems | Postgres healthcheck without `-h 127.0.0.1` | added: a socket check can pass during first-start init before TCP is open |
| 16 AWS | singular `--instance-id`/`--volume-id` on describe calls; "literal screenshot"; "503 = no healthy targets" | documented plural flags; screenshot decoded from base64; 503 = no *registered* targets (all unhealthy → the ALB fails open) |
| 50 Cloud/IaC/Proxmox | "very old versions only" for `terraform import` / `state mv` | still available; it is the older, unreviewed CLI way |
| 27 Learn Linux | `apt full-upgrade` "for new deps"; "kept back … new deps" | `apt upgrade` installs new dependencies; full-upgrade is for removals; kept back = holds, phasing or removals |
| 17 Windows | `pathping -d`; `sc query` inside PowerShell; `Get-ChildItem $_` | `pathping -n`; `sc.exe` (plain `sc` is Set-Content); `$_.FullName` |

Reported but **not changed**:
- 27 Learn Linux: "1000 or more = allow downgrade" is correct; apt skips older versions only below 1000.

**Still to verify, from the Windows writer:**
- 17 Windows lines 72–78: the success sample shows `PingSucceeded` next to `TcpTestSucceeded`. Test-NetConnection is believed to ping only when the TCP test fails.
- 17 Windows lines 321–329: the `findstr` sample hides extra matching lines.

**Size:** `index.html` is 14.94 MB with 413 cards and 517 boxes; the artifact limit is 16 MB. The boxes store only card ids, and the "Used in" lines are built in the browser.

Affected files:
- `command_decoder.py` (new; earlier versions in `research/command_decoder.*.py`);
- `commands/` (14 family files, `INTRO.md`, `README.md`, `ORDER`);
- `build_site.py` (decoder page and boxes);
- `tests/test_command_decoder.py` (new);
- the handbook modules 01, 16, 17, 25, 27, 44, 46 and 50 (fixes above);
- `research/decoder-briefs/` (briefs and prompts) and `research/fix_code_pipes.py`;
- `index.html`, `artifact.html` (rebuilt with Docker: `docker build --target export`).

Verification performed at the checkpoint:
- Each family was checked with `command_decoder.py --check`; the results are above.
- The Docker image was rebuilt with `RUN_TESTS=false`, because the test that every family file exists fails until shell basics lands.
- The server was restarted on 8173 and serves 63 modules, 14 families, 413 cards and 517 boxes, with no console errors.
- The unit tests were last run before the final families. Re-run them at resume.

**Resume checklist (next session)**

1. Check `commands/shell-basics.md`. If its writer was interrupted, the file may be missing or partial: finish or re-run it from `research/decoder-briefs/prompt-shell-basics.txt`. Then run `python3 research/fix_code_pipes.py commands/shell-basics.md` and the checker.
2. `python3 -m unittest discover -s tests`: everything should pass once shell basics exists.
3. `docker compose up -d --build` with the test gate on (the default), then a browser check of a few boxes and the decoder page. Optionally run the headless-Chrome QA again (scripts in the session scratchpad are temporary).
4. Verify the two open Windows items above.
5. Update `PROJECT-SUMMARY.md`, then decide with you whether to publish the artifact. It is still Version 8 and does not include any of the work from §6 onwards. Run `research/prepublish_scan.py` first.

## 11. Checkpoint closed: all 15 decoder families, test gate on (4 October 2026, about 21:15)

The last writer finished while the checkpoint was being saved, so resume steps 1–3 from §10 are done.

- **Shell building blocks:** 11 cards: echo/printf; cp/mv/install; mkdir/touch/ln/rm; cd/type/which/history; loops; sleep/seq; `set -euo pipefail`/trap/exit; export/printenv/source; bash/sh; python3; script/nano.
  - Every use of its commands is matched, including `echo` (485 uses), `for`/`done` and `mkdir`.
  - **Command Decoder total: 424 cards in 15 families.**
- **Handbook fixes found by this writer** (originals in `research/*.before-*.md`):
  - **35 Deployment Patterns:** the symlink size in a sample now reads `29`, the length of its target path.
  - **39 Senior Architecture:** both node_exporter textfile scripts now create the temp file next to the target (`… .prom.XXXXXX`, ignored by node_exporter until the rename) instead of in `/tmp`. A `/tmp` on tmpfs made the `mv` a copy, so half a file could be read. The explanation is updated.
- **Docker test gate:** the build stage now installs `nodejs`, because one test syntax-checks every inline script with `node --check`. Without it the gated build failed. Node exists only in the build stage; the served nginx image is unchanged.

Verification performed:
- **Docker:** `docker compose build` with the test gate on built 63 modules with no warnings, and all 35 tests passed inside the container. The pages were exported with `docker build --target export`.
- **Local:** `python3 -m unittest discover -s tests` ran 35 tests: OK.
- **Size:** `index.html` is 14.99 MB, with 424 cards and 517 decode boxes.
- **`research/prepublish_scan.py`:** 0 personal or secret findings and 0 external loads. Its six IPv4 notes are all older handbook samples: a real `dig +trace` (root and TLD servers), example.com's address, a subnet quiz value, and version/GitHub numbers in the source catalog.
- **Server:** restarted on 8173 with the tested image. In the browser: 63 modules, 15 families, 424 cards, and no console errors. The Career Ladder "Fresher · L0" box shows 8 chips and fills 8 cards, including the new shell-basics cards.

Still open (from §10 and this writer):
- **17 Windows:** the `Test-NetConnection` success sample (`PingSucceeded` shown next to `TcpTestSucceeded`) and the `findstr` sample.
- **27 Learn Linux, lines 5332/5335:** the exit code bash uses for an unbound variable under `set -u` (the module says 127). Check it on a lab VM.
- The publishing decision: the artifact is still Version 8.

## 12. Long-tail decoder cards + CHECKPOINT (10 October 2026)

Your request: make the remaining decoder cards, then checkpoint and stop before 97% of the session is used. Three parallel writers covered the long tail: about 120 commands that each appear only once or twice in the handbook.

**What was added**

- **New family "More Linux tools"** (`commands/more-linux-tools.md`, 8 cards):
  - tmux/screen/setsid/disown
  - flock/lslocks
  - gdb
  - ldd/ldconfig
  - the BCC tools runqlat/biosnoop/tcpretrans
  - update-grub/grubby/grub-install
  - declare/mapfile/getopts/shopt
  - man
- **New family "More services, runtimes & monitoring"** (`commands/more-apps-and-services.md`, 17 cards):
  - postconf/postmap, multipath, pveversion, buildah/nixpacks, pytest, OpenTelemetry
  - java/jcmd/keytool, node/php, grafana cli/sqlite3
  - mongosh, patronictl, rabbitmqctl, zabbix_get, alloy, sqlcmd, vim, pwgen
- **Windows & macOS, 11 new cards:**
  - Get-HotFix/wusa, bcdedit, PowerShell remoting, mstsc/qwinsta, IIS cmdlets, PowerShell jobs, curl.exe
  - macOS sample/spindump, nettop, open, vmware-toolbox-cmd
- **About 50 near-variants attached to the card they belong with**, each with a one-line "Related:" note. Examples:
  - pidof → pgrep; telnet → nc; getsebool/sestatus → SELinux; ntpdate/chronyd → chronyc; zless → zgrep;
  - whois → dig; fail2ban-regex → fail2ban-client; redis-server → redis-cli;
  - shell builtins (test, true/false, break/continue, shift, local/return) → the loops card.
- **Matcher:** cmdlets with a capital inside the verb (`ForEach-Object`) now match. `--coverage --all` lists every uncovered command.

**Totals: 17 families, 460 cards; 98% of the 18,398 command uses in the handbook match a card.** What is left are mostly not commands: function names defined inside scripts (`run`, `usage`, `check_disk`…), SQL/awk fragments, and a few one-off tools such as smallstep's `step`.

**Handbook corrections in this round** (originals in `research/*.before-*.md`):

| Module | Fix |
|---|---|
| 17 Windows | Test-NetConnection success sample no longer shows `PingSucceeded` (it appears only when the TCP test fails); `systeminfo \| findstr` now uses an exact `/b /i /c:"…"` pattern, with a sample that matches it |
| 27 Learn Linux | the `set -u` exit-status claim (127) is no longer stated as a number: "a non-zero status", plus the `unbound variable` message to look for |
| 20 macOS | `spindump` needs root: `sudo` added |
| 23 Why Is It Slow | jstat/jcmd *find* the JVM through `/tmp/hsperfdata_USER`; jcmd *attaches* over `/tmp/.java_pid<PID>` |

**Open for next time (not verified, not changed):**
- `12-time-ntp.md` line 73: `chronyd -Q '…'` may refuse to run alongside the running chronyd service (pidfile). Check it on a lab VM.
- The `passwd / chage / faillock` card is 430 words, just over the 420 guideline.
- **Size:** the page is now 15.11 MB against the 16 MB artifact limit. Any further growth should be offset (for example by trimming the longest cards).
- **Publishing:** the published artifact is still Version 8; ask before republishing.

Verification performed:
- **Checker:** every touched family passes `--check`, and the escaped-pipe fix is clean on all 17 files.
- **Docker:** `docker compose build` with the test gate on built 63 modules with no warnings; all 35 tests passed inside the build.
- **Local:** `python3 -m unittest discover -s tests` ran 35 tests: OK.
- **Export and scan:** pages exported with `docker build --target export`. `index.html` is 15.11 MB, with 460 cards and 517 boxes. `research/prepublish_scan.py`: 0 personal/secret findings, 0 external loads, and the same 6 older sample IPs as before.
- **Server:** container recreated (`docker compose up -d`, healthy), serving 4.26 MB gzipped.
- **Browser:** 63 modules, 17 families, 460 cards and no console errors. A "Why Is It Slow?" box that contains the new java card opens and fills (32 cards).

## 13. Published artifact updated to Version 9 (10 October 2026)

At your request, https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY now has everything from §6 to §12: interview practice, the visual refresh, the QA fixes, the Command Decoder (460 cards, 17 families) and all handbook corrections. It is still private: only you, and anyone you share it with from the page's Share menu, can open it.

Checks before publishing:
- **`research/prepublish_scan.py`:** 0 personal/secret findings and 0 external loads. Its 6 IPv4 notes are older, legitimate samples.
- **Extra sweep:**
  - No real email addresses: the email-shaped strings are systemd units, SSH algorithm names, `example.internal` placeholders and one mailing-list message ID.
  - No real keys or tokens: the 7 AWS-key-shaped strings are all AWS's documentation key `AKIAIOSFODNN7EXAMPLE`.
  - No personal name.
- **Compared with the live Version 8:** all 56 modules and all 3,193 headings are still present (the new version has 63 modules). Of 30,959 text blocks, only 12 are missing, and every one is an intentional correction or rewrite (home notes, modules 01, 16, 17, 27, 39, 44 and 46).
- **Size:** 15.11 MB, under the 16 MB limit.

## 14. Hands-on labs like devopslabs.dev: in progress (20 October 2026)

Your request: make the handbook more like https://devopslabs.dev without changing the 3D view.
- **Room layout:** each room is split in two. On the left: an incident brief, tasks, answer boxes, hints and points. On the right: a live terminal on a disposable machine.
- **Unlocking:** checks run on that machine. The next task opens only when the current one is verified, and finishing a room opens the next one in its path.

Your answers set the design:
- **Machine:** it must never affect your system. It is destroyed when work is finished, with nothing installed on the host and nothing added to boot.
- **Rooms:** one per L0 roadmap topic, built from real community-reported incidents with solutions, not mainly from your own.
- **Progression:** task by task, then in path order.

**Decided and tested**
- **Lab machine:** an Ubuntu 24.04 container with real systemd, `labs/base/Dockerfile`.
  - **Hardening:** no privileged mode, no host folders, no devices; 768 MB memory, 1 CPU and 512 processes; an internal Docker network only (no internet, no host ports).
  - **The one trade-off:** it adds `SYS_ADMIN` and turns off the container's AppArmor profile, so systemd can remount its own namespaced cgroup read-write.
  - **Tested 20 Oct:** systemd runs, nginx starts and listens, the cgroup is the container's own (`0::/init.scope`), and the test containers were removed.
  - **Why not plain Docker:** without that change, systemd exits ("Failed to create /init.scope control group: Read-only file system").
  - **Rejected:** `--privileged` and mounting the host's cgroups, because both would weaken the host's isolation.
  - **Kept for later:** KVM VMs (this machine supports them) for Kubernetes and reboot rooms.
- **Full design:** `labs/SPEC.md` covers the room format, the controller API, task and path gating, hashed answers, the reaper (30 min idle) and the nginx proxy.

**Being built now**

Two builders are working in parallel:
1. **Platform:** controller, compose profile `labs`, nginx proxy, the "Labs" sidebar page with the split-screen room view, a pilot room, and a live smoke test.
2. **Rooms:** 12 L0 rooms (shell, permissions, users/sudo, SSH, processes, packages, text tools, bash, git, networking, HTTP/curl, Fresher capstone), each from a cited community incident. A test proves every check fails before the fix and passes after it.

The results will be logged in the next entry. Nothing is published yet.

## 15. Hands-on labs finished and tested (7 November 2026)

The labs from entry 14 are built. The **Hands-on labs** page is in the sidebar group *Labs*, with 13 rooms: an orientation room plus the 12 L0 rooms, each adapted from a cited community incident. The 3D map is unchanged.

| You want to | Run |
|---|---|
| Start the labs (the first build of the lab image takes a few minutes) | `docker compose --profile labs up -d --build`, then open http://localhost:8173/#m-labs |
| Stop the labs and the handbook (every lab container and `devlab-net` go too) | `docker compose --profile labs down`, then `docker compose up -d` to bring back only the handbook |
| Stop only the labs | `docker compose --profile labs rm --stop --force labs-controller` |
| Remove everything the labs ever created | `labs/clean.sh` (`--all` also deletes your progress, `--dry-run` only lists) |

**How a room works**
- **Layout:** the brief, tasks, answer boxes, hints and points are on the left; a live terminal on a disposable Ubuntu 24.04 machine with real systemd is on the right.
- **Check:** runs on that machine. The next task opens only when the current one passes, and Finish opens the next room in the path.
- **Without the lab server** (the offline file, the artifact, or the labs stopped), every room opens read-only and shows the start command.

**Fixes made while finishing**
- systemd reported `degraded`, because journald and rsyslog exited with `218/CAPABILITIES`. A drop-in now sets each service's capability bounding set to the lab's 11 capabilities, so `journalctl` keeps working.
- The packaged `ttyd.service` was masked; it had held port 7681.
- Added `acl`, `shellcheck`, `dos2unix` and `ipcalc` for the rooms.
- After Finish, the "Lab machine destroyed" panel stays on screen with a "Start this room again" button.
- The `test_rooms.py` hint now creates `devlab-net` with compose's labels. A plain `docker network create` made compose refuse to start the profile ("incorrect label").

**Verified 7 November 2026**
- **Unit tests:** 59 tests OK.
- **Docker test gate:** 55 tests OK, 1 skipped (the compose checks, because `compose.yaml` is not in the build context).
- **Live smoke test** (`labs/smoke_platform.py`): 74 of 74 checks passed.
  - task and path gating; wrong answers refused; checks fail before the fix and pass after;
  - no internet from a lab, and a lab can't reach the controller or another lab's terminal;
  - cross-site requests and foreign Host headers refused;
  - nothing left after `down`, after removing only the controller, or after `clean.sh --all`.
- **Rooms:** all 13 pass `labs/test_rooms.py` (checks fail → solve → checks pass).
- **End state** (checked again by the lead): no `devlab=1` containers, no `devlab-net`, no lab images, no lab volume. Only `devops-handbook` was rebuilt; handyman-* and portainer were not touched.
- **Page size:** `index.html` is 15,249,895 bytes, under the 16 MB artifact limit. About 0.75 MB of headroom is left, so new features must stay small.

**Limit to know:** a lab is root-capable inside its container (sudo, `CAP_SYS_ADMIN` for systemd, AppArmor unconfined). It is a practice sandbox for the handbook's own rooms, not a barrier against hostile code; see `DOCKER.md`. The next step if that matters is user-namespace remapping or sysbox, and both would change the host's Docker setup.

The artifact has not been republished yet.

## 16. Decision drills, Practice Arena 131 sites, labs security fixes (7 November 2026)

**Decision drills (new page, sidebar group *Labs*)**
- **What a drill is:** a DevOps-Dream-style game played as the on-call engineer.
  - Each drill has 3–5 steps. You pick a move, a "What happened?" panel explains the result and moves four meters (Service, Time, Evidence, Trust), and "Why not the others?" explains the moves you didn't pick.
  - If Service or Trust hits 0, the incident escalates past you and the drill ends early.
  - The end screen shows a score, stars, the real story with its source link, and "Practise this" links to lab rooms, handbook sections and outside sites.
- **Where it works:** offline and in the artifact; it needs no Docker.
- **Code and data:** `drills/SPEC.md`, `drills_site.py`, `drills/*.json` (12 drills, L0–L4, every track) and `tests/test_drills.py`.
- **Sources:** public incidents, each source read on 7 Nov 2026:
  - NADA inodes; Docker json-file logs; Let's Encrypt DST Root expiry; GitLab 2017 backups;
  - GitLab DinD TLS; Zalando CoreDNS OOM; Datadog 2023 systemd-networkd; GitHub RSA host key;
  - Cloudflare WAF regex; Roblox Consul; AWS S3 2017; Atlassian 2022.
- **Extras:** choices are shuffled on each play; keys 1–4/Enter/Esc; focus stays inside the drill; best scores are kept in your browser.

**Practice Arena (module 54): 80 → 131 sites**
- **New research:** from deep research on 7 Nov 2026 (report `reports/New free DevOps practice sites.md`, notes in `research_notes/`).
- **Status fixes:**
  - Microsoft Learn sandboxes are retired; use Applied Skills labs instead;
  - Cloud Quest moved to skillbuilder.aws/cloudquest;
  - the AWS Builder Center has a free sandbox;
  - LocalStack Community is frozen;
  - the Backdoors & Breaches URL changed;
  - EKS Cluster Games and the Big IAM Challenge were unreachable (no DNS) on 7 Nov, so they are marked but not retired;
  - unixgame.io is listed unlinked as "do not use".
- **Catalog:** `research/practice.json` is now the single catalog. Each site has a stable `id`, cost, signup, runs, level, modules, tracks, checked_on and status; it is the base for per-topic practice links.

**Labs: independent review (Opus, xhigh) and fixes**
- **Verdict:** host isolation, answer secrecy and gating held.
- **Fixed:**
  - a lab could forge `X-Lab-Via` while booting;
  - one lab could open another lab's terminal: each ttyd now has a per-session credential that only nginx injects;
  - Finish/Reset/reaper now take the session lock;
  - stopped sessions no longer hold a slot;
  - the clean.sh cache markers are now project-specific;
  - `/api/labs/health` answers `200 {"ok":false}` when the labs are off, so the console stays clean.

**QA (Opus, xhigh): all 12 drills played to the end, 647 checks, plus regressions.** Fixed:
- browser Back leaving the handbook (drills and lab rooms);
- double-clicks picking a move;
- the Tab focus trap;
- read-time estimates counting hidden JSON;
- titles cut off at 360 px;
- four contrast tokens raised to at least 4.5:1;
- two factual slips in the NADA drill, and the Zalando brief wording.

**Verified 7 Nov 2026**
- **Tests:** 101 unit tests OK.
- **Live smoke test:** 84/84 checks, including 401 for lab-to-lab terminal access and 403 for a forged via.
- **Leftovers:** no devlab containers, network, images or volume.
- **Page size:** `index.html` is 15,439,120 bytes, against the 16 MB limit.
- **Artifact:** not republished yet (it is still Version 9).

## 17. Per-topic "Prove it" ladder, then artifact Version 10 (7 November 2026)

**Prove it ladder** (`prove_site.py`, `roadmap.json` field `prove_sites`, `tests/test_prove.py`)
- **Placement:** every 3D-map topic panel shows "Prove it" right after its exit check. The 3D scene itself is unchanged.
- **Three steps, ordered by effort:**
  1. the topic's decision drills, computed from each drill's `topics`, with "✓ played <score>" after you finish one;
  2. its lab rooms, computed from each room's `map_node`;
  3. 0–3 outside sites, chosen by id from `research/practice.json`, the single catalog. Each is badged: in the browser / free account / throwaway VM / can bill YOUR cloud account, plus the date it was checked. Deep links go to exact scenarios, e.g. SadServers "Bergen: port already in use".
- **Coverage:** 117 of 123 topics have sites (77 different sites, none paid); 39 topics have drills and 13 have lab rooms. 53 modules end with a "Prove it" strip (up to 6 cards, plus "Open in the map" chips), rendered at build time.

**Independent QA (Opus, xhigh)**
- **Site picks:** reviewed all 117 topics and fixed 10 mismatched picks (e.g. Vault now links the Vault sandbox; container-hardening now links Kubernetes Goat).
- **Links:** all 124 outside URLs return 200.
- **Bugs fixed:**
  - Back from a strip card dropped you at the top of the module;
  - the root class `lab-open` clashed with a button class;
  - "✓ played" was not refreshed when the map was reopened;
  - the billing badge had no colour;
  - switching On-prem/Cloud with the map closed rewrote the address to `#map`.
- **Map regressions:** 49/49 checks.

**Published:** artifact Version 10 on 7 Nov 2026 at https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY.
- **Before publishing:** 119 unit tests OK; the prepublish scan found 0 personal/secret findings and 0 external loads; every live v9 heading is present in v10 (3,764 → 3,844).
- **Size:** `index.html` is 15,583,876 bytes, about 16 KB under the self-set 15.6 MB budget. New content now needs offsetting cuts.

## 18. Map panel in learning order + Protocol Explorer (9 November 2026)

**Topic panel order.** You asked for this order:
- Old order: why, learn, practice, troubleshoot, commands, exit check, prove it, study path, related, prerequisites, next.
- New order: Prerequisites → Study path → Key commands → Practice drills → Troubleshooting → Exit check → Prove it → Related playbooks → Next step.
- "Why it matters · what you'll learn" is now one collapsed line under the summary.
- `tests/test_prove.py` now asserts this order.

**Protocol Explorer** (https://a2aprotocol.ai/tools/protocol-explorer)
- **What it is:** free, browser-only, no sign-up. You step through 33 protocols packet by packet (HTTP, TCP, DNS, TLS, DHCP, BGP, SSH, WireGuard and more), with each packet explained. It is a teaching simulation, so it belongs in study paths, not in Prove it.
- **Added to:**
  - module 54 §4 (now 132 sites) and `research/practice.json`;
  - the study path of 10 topics: net-basics, http-curl, sockets-ports, dns-deep, tls-certs, reverse-proxy, packet-capture, vpn-mesh, ssh-basics, routing-nat.

119 tests OK; `index.html` is 15,586,543 bytes. Not republished yet; the artifact is still Version 10.

## 19. Learning tools, no-VM ladder and the 9 Nov practice merge (9 November 2026)

- **Learning tools in study paths:** 128 tool links (90 distinct tools) added to the `study` lists of 77 topics, inserted after the first item (after Protocol Explorer where it sits second). Each label carries its data-safety note and the caveats (MetricsQL ≠ PromQL, LogsQL ≠ LogQL, kubectl JSONPath ≠ RFC 9535, Live Jinja has no Ansible filters, browser Helm renderers can differ from `helm template`, jwt.io, A-Packets, WireGuard keys, Terraform plans, crt.sh). Backup: `research/roadmap.before-tools.json`.
- **Module 54 §17 "Learning tools by topic"** (new; "Where to go next" is now §18): four tables, about 125 tools, plus lower-confidence lists. Backup: `research/54-practice-arena.before-tools.md`.
- **No VM? Use these:** a seven-rung ladder in 27-learn-linux.md (Build your lab VM), linked from the start-here study path. WebTerm added to practice.json and module 54 §2.
- **Corrections:** no handbook page linked ssl-config.mozilla.org, so TLSRef is introduced as "formerly the Mozilla SSL Configuration Generator". Play with Docker re-checked (notice still shown): status `retired` in practice.json, §16 row updated, no `prove_sites` used it.
- **Practice merge (more_practice_sites.md + five per-track files):** 32 new sites (165 in all), 245 new deep links, 24 rejected entries in `excluded_after_research`, `prove_sites` re-picked for all 123 topics (354 refs, 240 exact deep links). Premium iximiuz and paid SadServers links were removed. Cork relabelled. Backups: `research/practice.before-more-sites.json`, `research/practice.before-tracks.json`, `research/roadmap.before-more-sites.json`, `research/roadmap.before-tracks.json`, `research/54-practice-arena.before-more-sites.md`, `research/54-practice-arena.before-tracks.md`.
- 134 tests OK. `index.html` is 15,720,446 bytes: +120,223 bytes against the same build scripts (tools +64,391, practice +55,832). Not republished.
- Open: the home-card text in build_site.py still says "132 free-first sites" (module 54 now lists 165). That file belongs to the parallel back-button work, so it was not edited.

## 20. CHECKPOINT (9 November 2026, about 01:45 IST; the machine is shutting down)

**Done since artifact Version 10, built and tested locally (not yet published):**
- §18: the map panel follows the learning order (Prerequisites → Study path → Commands → … → Prove it → Related → Next), plus Protocol Explorer.
- **Job-search unlock:** ai-job-search, with its cautions, unlocks on the 6 milestone topics after "Mark as done" (`tests/test_jobunlock.py`).
- **Universal back navigation** (`backnav_site.py`, `tests/test_backnav.py`): every in-page jump pushes history, and a "← Back to …" pill appears.
- §19: 128 learning-tool links in 77 topics' study paths, with data-safety labels.
  - Practice Arena is now 165 sites, with §17 "Learning tools by topic", WebTerm and the no-VM ladder in 27-learn-linux.md.
  - Play with Docker is retired, and the Killercoda CKA link moved to Sachin's free course.
  - `prove_sites` were re-picked: 354 refs, 240 of them exact deep links.
- The size budget was raised to 15,950,000 at the user's request. `index.html` is 15,720,471 bytes; 134 tests OK; the handbook container is rebuilt.
- **Research notes** (9 Nov) are in `research_notes/Free learning tools per DevOps topic/`: networking, linux, containers/k8s/cicd/iac/obs and cloud/security/data tools, plus more_practice_sites and five per-track practice files.

**In progress at shutdown:** the independent pre-publish QA (Opus xhigh) had started and will not finish. Re-run it next session.

**Next session, in order:**
1. Re-run the pre-publish QA. It covers back navigation (all jump paths, messy use), map regressions, the job unlock, an HTTP check of every outside URL in `#prove-data` and the study items, a spot-check of 15 deep links (title and free, no iximiuz Premium, no SadServers Paid), content fit, layout at 360/768/1366 in both themes, tests, the prepublish scan and size.
2. Republish the artifact as **Version 11** at https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY. First read the live v10 and compare headings, then publish `artifact.html` with `url`.
3. **The user's new request:** find more practice websites for the decision drills, i.e. more public incident sources and post-mortems (k8s.af, danluu/post-mortems, VOID, vendor post-mortems) and per-drill "Practise this" sites, then add more drills. Each drill is about 9.5 KB; the budget now has about 230 KB of headroom.
4. Later: Resume/progress, table readability, and possibly an "unmet prerequisite" hint in the map panel.

**Rules that still apply:**
- Never run the handbook's commands on this machine.
- Never touch the handyman-*, portainer, jenkins or ollama-* containers.
- Labs are ephemeral; `labs/clean.sh` removes everything they create.
- Builders run on Opus high, review and QA on Opus xhigh.
- Practice sites matter most to the user.

**Note for next session:** the QA agent was allowed to fix bugs, so it may have changed files before the shutdown. Check for `research/*.before-qa4.*` backups. Then run `python3 build_site.py` and `python3 -m unittest discover -s tests` before anything else.

## 21. Pre-publish QA4 fixes (10 November 2026)

Independent QA in headless Chrome (real clicks) of the back pill, the map, the job unlock, the links and the layout. Backups are `research/*.before-qa4.*`.

- **Map "Prove it" drills and lab rooms now get their own history entry.** They used to replace the map entry, so Back (and the room's ✕) skipped the map and dropped you in the handbook. Now Back, ✕ and Esc reopen the same topic at the same panel scroll (`openPractice` and `routeFromHash` in build_site.py; test in `tests/test_backnav.py`).
- **Contrast of the unlocked job section:** the teal tint sat on `--bg3`, which put links at 4.3:1 (light) and dim text at 4.47:1 (dark). On `--bg2` the lowest is 4.8:1 (`tests/test_jobunlock.py`).
- **Dead links (404) replaced** in roadmap.json and the modules:
  - KodeKloud kubeadm intro → `Deployment-With-kubeadm-Introduction/page`;
  - KodeKloud kubeadm solution → `Lab-Solution-Install-a-Kubernetes-Cluster-using-kubeadm/page`;
  - Gunicorn deploy docs → `https://gunicorn.org/deploy/`.
- **Prove-it picks:**
  - container-incidents linked an iximiuz challenge labelled "Capture a crashed container's logs", which is really a Kubernetes pod challenge. It now links "Connect a container to a host service", and the catalog label states what that challenge is.
  - The Killercoda Vault/Caddy ACME scenario (letsencrypt-acme) is written in Chinese, and its label now says "(in Chinese)".
- 137 tests OK. `index.html` is 15,720,556 bytes. Not republished.

## 22. Artifact Version 11 published (10 November 2026)

- **Pre-publish QA4:** GO.
  - Fixed: Back from map "Prove it" practice links; 3 dead links (KodeKloud kubeadm ×2, gunicorn); contrast in the job-unlock box; two mislabelled Prove-it picks.
  - 137 tests OK, the prepublish scan clean, `artifact.html` 15,720,120 bytes; every v10 heading is present (3,844 → 3,850).
- **Published as Version 11** (version id 1794306682-857b) at https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY. It includes the panel order, job-search unlock, back pill, 128 learning tools, the 165-site arena and the re-picked Prove-it links.
- **Staged for Version 12** (in `drills_staging/`, not yet merged):
  - 21 new drills (writers A and B still running);
  - the no-IP section (`section_no_ip.md`, which becomes 42 §1.6, with the user's TrueNAS case anonymised).
- **In progress for Version 12:**
  - the senior "troubleshoot without downtime" framework, designed by Fable (`research/senior-troubleshooting-framework.md`), using the user's Pi-hole migration runbook (`research/user-cases/pihole-migration-runbook.md`) as its main case;
  - removing the mobile layout (desktop only, user request).

## 23. Desktop only + slimmer page (10 November 2026)

- Desktop only (user request): removed the phone and small-tablet layouts: the ≤760/640/560/520/360 px rules, the two-row phone topbar, the iOS zoom fix, `hover: none`, the ≤800 px map bottom sheet (plus the map script's `narrow()` branch), safe-area insets, `viewport-fit=cover` and the `--h-m` mobile heights. The ≤900 px drawer sidebar, the lab split stacking, and the ≤1000/1100 px label hiding stay for split-screen laptops.
- New `page_slim.py`, which shrinks the page with no visible change. It strips whitespace between block tags (never inside `<pre>`), writes `&quot;`, `&#x27;`, `&gt;` and safe `&amp;` as plain characters in text, and minifies the template CSS/JS plus the UI, labs, drills and decoder scripts (newlines kept). It also drops `target`/`rel` from the 7,421 plain external links; one line of page script restores them on load, inside `<template>` rooms and debriefs too.
- Also removed: `class="language-*"` on code blocks (nothing read it), and the `nav-h2`/`nav-h3` classes (the CSS now uses `.subnav ul a`). The sidebar template is now one line per module.
- index.html went from 15,720,556 to 15,044,052 bytes (−676,504). Visible text, search index, `<pre>` text and element boxes match the old build exactly; the only DOM change is the viewport meta. Tests: 147 pass, including the new tests/test_page_slim.py. Backups are in research/*.before-slim.*. Not republished.

## 24. Version 12 content merged (10 November 2026)

Merged everything that was staged in `drills_staging/` into the project, then built, tested and checked it in the browser. Backups are `research/*.before-v12.*`. The staging folder is kept, unchanged, in `research/drills_staging-merged-2026-11-10/`.

- **Module 42 §1.6 "A server or NAS gets no IP after a reset or a hardware change"** (Ubuntu netplan, TrueNAS, Proxmox, ESXi; your TrueNAS case anonymised). Module 42 now says "41 problems", the section 1 intro names the renamed-interface case, and the first-minute table has a row for it. Cross-links come from 41 §3.5 (Boot waits two minutes for the network) and 50 §7.2 (Web UI dead after an IP, hostname or NIC change).
- **New module 57 "Method: PROTECT & the Risk Ladder"** (🛟, first in "Real incidents & playbooks", plus a home card "Broken, people waiting?"). It covers the PROTECT loop, six facts for any stack, the eight-rung risk ladder, window or live fix, the before-Enter check, messages for risky steps, and two worked examples: a DNS server move with no downtime, and one box with one way in.
  - **"🖨️ Print the card"** under "The PROTECT card": prints a copy of the card only, black on white, on one A4 page, offline (print rule and script in `site_ui.py`, minified with the rest of the UI).
  - **Course map:** six entries added, no new topic (still 123): study items on outage-basics, deployment-strategies, change-management and incident-command; links on dns-deep and network-problems. A structural diff shows only those six appends.
  - **Interview pack 57**, "The only database is down, and the fast fix could lose data", on the Senior page: 57 packs, 57 scenarios, 114 prompts. The manifest, `interview/README.md`, the home README and the home card were updated to match.
- **24 new decision drills, 36 in all.** L0 5, L1 7, L2 8, L3 9, L4 7. `drills/ORDER` keeps the 12 existing drills in place, and each new drill sits after the existing ones of its level. The new drills come from Pi-hole, Realogs, Healthchecks, Jenkins, Wikimedia (×6), systemd, moby, Ravelin, Proxmox (×2), Traefik, Dokploy, Codecov, Terraform, NRE Labs, Cloudflare 2015, Wazuh, Monzo and GitHub 2018. The three PROTECT drills (Pi-hole DNS move, Monzo, GitHub 43 seconds) also link to module 57 §4.
- **"Safest next step" hints:** 15 one-line hints read at build time from `hints/safest-step.tsv`. Each one sits under its playbook heading in 21, 23, 25, 26, 30, 38, 42, 44, 50 and 52, as "🛟 Safest next step · rung N: …", and "rung N" links to the risk ladder (`#m57-4-the-risk-ladder`). A heading that is missing, or not unique, is a build warning. `tests/test_hints.py` (10 tests) fails on it and also checks the 160-character limit, documentation-only addresses, the Docker build context and the print card.
- **Test change:** the drills page read time is now about 16 minutes, because 36 visible drill cards are about 100 words each. The read-time test now checks that the estimate equals the visible-text estimate, and that it stays under 30 minutes. Counting the JSON would give about 190 minutes.
- **Results:**
  - build: 66 modules, no warnings, 983 map links resolved and 0 fell back to the module top. Every cross-module link fragment resolves; module 57 keeps its one deliberate plain link to module 21.
  - tests: 157 OK.
  - prepublish scan: 0 personal/secret findings and 0 external loads, plus the same six informational IPs as before.
  - size: `index.html` is 15,329,234 bytes and `artifact.html` 15,328,818 bytes (+285 KB; the budget is 15,950,000).
  - the handbook container was rebuilt, and its image gate passed.
  - browser (headless Chrome, 1366 and 1024 px, light and dark): 112 checks pass with no console errors. They cover module 57, the print path, the links into 42 §1.6 from 41, 50 and 57, 36 drills with 3 new ones played to the end, hints under 3 headings landing on the ladder, the outage-basics and dns-deep map items, and the back pill.
- Not republished; the artifact is still Version 11.

## 25. Pre-publish QA5 of Version 12 (10 November 2026)

Independent QA of §23 and §24 in headless Chrome (real clicks; 1366 and 1024 px, light and dark, plus a 900 px pass). Backups are `research/*.before-qa5.*`.

- **Bug fixed: printing the PROTECT card lost your place.** The print layout holds only the card, so the browser came back at the very top of the handbook (scrollY 745,532 → 0 after a real print layout). The print handler now saves the position and restores it on `afterprint` (`site_ui.py`; test in `tests/test_hints.py`).
- **Facts corrected:**
  - live-restore on a Swarm node: dockerd refuses to start with it ("--live-restore daemon configuration is incompatible with swarm mode", see docker/docs#26424). Module 57's tool table said it "skips Swarm services" and §8 said it "will not keep its services up"; both now say dockerd refuses it, so enabling it takes Docker down. The hint under 30's daemon.json section says the same. The docs issue is added to the sources.
  - The PROTECT card's one-box line said "TTL or lease lowered the day before", which is wrong for long leases (Windows DHCP defaults to 8 days). It now says one old TTL ahead and half an old lease ahead, as §5 and §8 do. The card still prints on one A4 page.
  - Drill wikimedia-2022-apache-listen-443: the "add apachectl configtest" choice said it would guard against this; an extra `Listen 443` is valid syntax, so configtest would have passed. The explanation now says so (the verdict stays "good").
  - Interview pack 57: "raise the one exhausted limit" now notes that only works live where the setting can change live (MySQL's `max_connections`; PostgreSQL's needs a restart).
  - New `tests/test_qa5_facts.py` (5 tests) keeps these.
- **Checked and fine:** page_slim regressions (every outside link, template links after drills and labs open, the map panel's 800 runtime links: all `target=_blank rel=noopener`; code blocks match v11 box for box; decoder boxes fill; search 10/10 queries at all four sizes and themes; sidebar; no overflow in long modules; per-module text identical to v11 except the intended changes; tag balance clean). Module 57: 36 links land, the card prints only itself on one A4 page, interview pack 57 renders. 42 §1.6: links in from 41, 50 and 57 and out to 50, 41, 02 and 28 land; Back and the pill restore the scroll. All 24 new drills were played to the end (12 on best moves, 3 stars each); 8 debriefs were checked against their sources. All 15 hints sit under the right headings and land on the ladder. Map: open and close, topic toggle, panel order, Prove it, the job unlock, the six new items.
- 163 tests OK, the prepublish scan clean apart from the known six informational IPs, `artifact.html` 15,329,376 bytes. The handbook container was rebuilt. Not republished.

## 26. Artifact Version 12 published (10 November 2026)

- **Published:** Version 12 (version id 1794314210-eadd) at https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY.
- **Before publishing:** QA5 gave GO.
  - 163 tests OK; the prepublish scan was clean.
  - `artifact.html` was 15,329,376 bytes.
  - Every heading from v10 is still present once HTML entities are decoded (page_slim writes `&` instead of `&amp;`).
- **Contents:** desktop-only + page_slim (−676 KB); 42 §1.6 no-IP; module 57 PROTECT & the Risk Ladder (the user's Pi-hole runbook and TrueNAS case anonymised as worked examples); 36 drills; 15 safest-next-step hints; interview pack 57.
- **Next (research/ideas-2026-11-10.md):** lab rooms for L1–L2 from the incident backlog. Some need the deferred VM tier (Swarm, Harbor, Dokploy, boot, WireGuard, MTU, TrueNAS). Then game-day mode and the review/"Today" page.

## 27. QA6 of lab rooms 13–24 (10 November 2026)

Independent QA of the 12 new rooms (Junior 13–18, Mid 19–24) on the new lab image. All 12 were played in headless Chrome by typing into the ttyd terminal, with one wrong fix per room, then Check, Finish and the walkthrough; every lab container was gone after Finish. Backups are `*.before-qa6.*` next to each changed file.

- **Regression fixed: room 11.** The image now carries apache2, whose package puts `/var/www/html/index.html` there, so nginx's default site served the Apache page instead of "Welcome to nginx!" and `test_rooms.py 11` failed. Room 11's `setup.sh` now removes that file in its lab.
- **Learner bugs fixed:**
  - Room 13: `grep -rn … /etc/apache2/sites-enabled/` skips the symlinks there, so it never showed the `<VirtualHost>` line. It is now `grep -Rn`.
  - Room 14: a bare `dnsmasq --test` reads only `/etc/dnsmasq.conf` and said OK for a broken drop-in. The hint, walkthrough and check now use `--conf-dir=/etc/dnsmasq.d,.dpkg-dist,.dpkg-old,.dpkg-new`, as the unit does. The `man dnsmasq` hints became `dnsmasq --help` (the lab has no man pages).
  - Room 15: the walkthrough now says `sudo cat` for the heartbeat file. "*Why `daemon-reload`:*" rendered with literal asterisks; room 11 had the same problem with a bold link.
  - Room 19: the task explains `generate`'s udevadm "Failed to send reload request" line.
- **Facts corrected:**
  - Room 18: curl, OpenSSL and Python still fall back to the CN when a certificate has no SAN; only browsers and Go ignore it. Also, certbot's `--nginx` plugin reloads nginx itself.
  - Room 20: `nofail` does not shorten a swap wait, because swap units stay ordered before `swap.target`. A failed non-`nofail` swap logs "Dependency failed for swap.target" (not "Reached target"), so the recorded critical chain now jumps to `sysinit.target`.
  - Room 21: the journal tail wording.
  - Room 23: the PG ≤15 reserved-slots message, and that the worker held 15 of the 17 slots.
  - Room 24: only the last X-Forwarded-For entry is trustworthy.
- **DOCKER.md:** rebuilding with `up -d --build` while the labs run fails once with `network devlab-net not found`, because the old controller deletes the network on stop. A new table row says to run `down` first, or to run `up` again.
- **Gates:** smoke 84/84; `test_rooms.py` 25/25 after the fix; 163 tests OK; the build has no warnings; the prepublish scan is clean apart from the 6 known IPs; `artifact.html` is 15,428,235 bytes. Cleanup left no devlab container, network, lab image or progress volume, and only the handbook runs. Not republished.

## 28. Artifact Version 13 published: 12 Junior and Mid lab rooms (10 November 2026)

- **Published:** Version 13 (version id 1794319306-b0c1) at https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY.
- **New rooms:** 25 in total.
  - Junior (13–18): port 80 Apache vs nginx, port 53 dnsmasq vs a stub, restart loop, deleted-but-open log, 502/504 behind nginx, expired certificate.
  - Mid (19–24): netplan lost config (the TrueNAS lesson), boot waits 90 s, logrotate/journald, dig vs the app, Postgres client exhaustion without a restart, proxy client IP and 413.
- **Lab image:** gained apache2, openssl, dnsmasq, systemd-resolved, netplan.io and postgresql, all disabled at boot. systemd-resolved cannot run in the lab (no CAP_SETPCAP), so room 14 uses a labelled stand-in.
- **QA6:** GO.
  - All 12 rooms played in the browser terminal, each with a wrong fix tried first.
  - Smoke test 84/84; test_rooms 25/25; 163 unit tests.
  - Cleanup verified: no devlab containers, network, images or volume left.
- **The QA6 backups** were moved out of labs/rooms (they would have gone into the controller image) to research/labs-qa6-backups/.
- **Open:**
  - ttyd reconnect noise in the console after Finish;
  - no "path complete" message on the last room of a path;
  - the `devlab-net not found` quirk when running `up --build` while the labs run (documented in DOCKER.md; a code fix is still to decide);
  - the VM tier for Swarm/Harbor/Dokploy/boot/WireGuard/MTU/TrueNAS rooms.

## 29. Checkpoint: VM tier plan agreed in principle, not started (10 November 2026)

- **Decision:** don't move everything to VMs. Containers and free sites cover most topics.
- **Proposed order (waiting for the user's "go"):**
  1. **A throwaway verify VM:** it runs the safe module commands and all 25 rooms, produces a checklist, and is destroyed.
  2. **3–4 VM rooms:** boot, NIC/netplan, MTU/WireGuard, Swarm+Dokploy.
  3. **Ollama as a fake learner and hint drafter:** never the judge.
- **Storage:** the user has set aside 25 GB, which is enough.
  - One VM at a time; peak about 10–12 GB, about 1–2 GB at rest.
  - Disks capped at 10 GB; refuse to start below 15 GB free.
  - QEMU runs in Docker with /dev/kvm, so nothing is installed on the host.
- **Full checkpoint:** `.claude/checkpoints/checkpoint-20261110-213000-67548b67.md`.

## 30. Automatic cleanup: the `janitor` service (11 November 2026)

- **Why:** the user asked for automatic, time-based cleanup of only what this project creates, never touching their other containers or images. Before the janitor ran:
  - 34 old handbook builds (untagged) were left on the machine.
  - About 4 GB of this project's build cache had built up.
- **New service** `devops-handbook-janitor` (docker/janitor/, compose service `janitor`):
  - Python stdlib talking to the Engine API over the socket.
  - Hardening: no network, read-only, no capabilities, 128 MB memory and 64-process limits.
  - Restart policy: `unless-stopped`.
  - It looks for running labs every 5 min and runs a full pass every 60 min.
- **What it removes:**
  - our untagged old builds, at once;
  - the tagged lab images after 7 days without labs use, only while the labs are off;
  - our build cache after 48 h unused, by record ID, a parent only together with all its children;
  - orphaned devlab=1 containers.
- **How it recognises ours:**
  - Images: our `devops-handbook.*` labels, or Compose's project and service labels; never an image another compose project built.
  - Build cache: each stage of our Dockerfiles now starts with a no-op `RUN : devops-handbook-<stage>` or `RUN : devlab-<stage>`, and everything built on that record counts as ours.
  - Stage names are not used: BuildKit shares generic steps such as `WORKDIR /src` between projects.
- **Never touched:**
  - other projects' containers and images;
  - all volumes and networks;
  - base-image cache records;
  - the running handbook image and the janitor's own image.
  - Images are never force-removed.
- **Config:** `.env` keys JANITOR_CACHE_KEEP_HOURS, JANITOR_IMAGE_KEEP_DAYS, JANITOR_EVERY_MINUTES and LABS_MAX_SECONDS.
- **Labs controller:** a new hard lifetime limit, `LABS_MAX_SECONDS` (default 3 h), on top of the 30 min idle limit.
- **labs/clean.sh:** build cache now goes through `janitor.py --labs-cache`, which takes only the `: devlab-*` subtrees. Its old text markers are gone.
- **First live run:**
  - removed 35 old builds and 118 + 36 cache records, about 4.2 GB in total;
  - the user's 18 other untagged images and all their containers were untouched.
- **Review:** an independent reviewer (Opus xhigh) went over it twice. Fixes from that review:
  - stage-name marks were unsafe;
  - the legacy patterns were generic;
  - label inheritance;
  - silent prune errors;
  - single-stage builds had no marks;
  - Docker's event log keeps only about 15 min, so it can't track labs use;
  - the LastTagTime documentation was wrong.
- **DOCKER.md:** new section "Automatic cleanup". It also explains why `CREATED` shows the publisher's build date, and that Docker keeps no reliable pull date.
- **Tests:** tests/test_janitor.py added; 174 unit tests pass in total.

## 31. Published on GitHub Pages (12 November 2026)

- **Repo:** https://github.com/sunnymeghnani/DevOpsLearning (public). This folder is now its git working copy.
- **Commit 9e9c290:** pushed as a normal fast-forward on top of the user's own upload, 7dc48d6. That upload was the claude.ai-wrapped copy; it is now replaced by the standalone index.html, which has the same content.
- **Site:** https://sunnymeghnani.github.io/DevOpsLearning/. The path is case-sensitive.
- **Checked in the browser:** the home page loads with no console errors, and the Labs page shows the read-only notice.
- **`.nojekyll`** keeps GitHub Pages from running Jekyll, which would choke on the `{{ }}` in the modules.
- **`.gitignore`** keeps out session files, backups and staging, plus decoder-briefs (local paths) and the owner's raw incident notes.
- **Privacy:**
  - The home path in PROJECT-SUMMARY.md was replaced.
  - Commits use the GitHub noreply email.
  - A staged-file scan found no personal data or secrets.

## 32. Verify VM, focus mode, key commands explained (15–20 November 2026)

- **Verify VM** (`labs/vm/`):
  - QEMU runs inside a capability-free container, and the guest is offline while it is checked.
  - It runs the handbook's commands and all 25 rooms. Report: `reports/verify/verify-2026-11-15.md`.
  - Rooms: 22 PASS, 3 DIFFERS on a real VM.
  - QA: GO. Runner fixes: OOMPolicy=continue, docker restored between blocks, the culprit blamed for BROKE_VM, classifier fixes.
- **Focus mode** (`focus_site.py`):
  - A topic shows only its own sections, with lock cards for topics not reached yet.
  - "Show whole module" shows only that module.
  - "Sources" lists become a "Related incidents" link, and nested sections are de-duplicated.
  - Two QA rounds: 12 bugs fixed.
- **Key commands explained** (`keycmd_site.py`, `keycmd_notes.tsv`):
  - 455 key commands, each with a one-line summary, a safety badge and a Decode › link.
  - Fact-check: 40 summaries and 4 badges corrected.
  - QA: GO.
- **Not yet QA'd:**
  - The whole-module end card now leads with "Next topic".
  - Content fixes from the VM report (14 modules).
  - The VM re-run of the changed modules is still to do. See `PROGRESS-CHECKPOINT.md`.
- **Tests:** 221 pass.
