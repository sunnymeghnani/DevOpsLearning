# Project Summary — DevOps Field Handbook

What was built, how it was built, where everything lives, and what is worth knowing
before you extend it. Last updated: 10 November 2026 — **checkpoint** (Version 13 published; VM-tier plan waiting, see `recent_updated.md` §29).

**Checkpoint state (10 Oct):** Command Decoder complete — 17 families, 460 cards, 98% of handbook command uses decoded (`recent_updated.md` §12), visual refresh (`site_ui.py`), QA fixes, Docker build/serve (`DOCKER.md`), and eight handbook corrections found while writing cards (ten modules corrected in total). Test gate on in Docker (35 tests pass). Published as artifact Version 9 on 10 Oct (`recent_updated.md` §13).

**Local update:** Sources & Verification (56) now connects the saved research to the
problem libraries and course map. `index.html` and `artifact.html` have been rebuilt;
the existing published artifact has not been updated by this integration.

**Personal scope:** this is the user's learning path under construction. Examples and proposed
labs are not completed user work. Do not mark progress or imply the user performed them.
The latest request is substantive Reddit/Stack Overflow case integration, not merely search links.
`research/community-threads.json` records 12 curated discussions (7 Stack Overflow, 5 Reddit).
`research/community-incidents.json` adds 16 questions/cases, including six production
postmortems, nine community threads and one vendor advisory: 28 curated cases total.
The build adds them to modules 41–52 and a case directory in 56 without rewriting historical
catalogs. Solutions distinguish confirmed recovery, workaround, partial improvement and limits.

**Standalone interview pack:** `interview/README.md` indexes 56 module-matched files with
56 scenarios and 112 prompts (main question plus twist), answer checkpoints, reasoning,
traps and proposed verification exercises. `interview/SOURCES.md` separates Reddit interview
self-reports, the GitHub practice collection, incident threads and technical references.
One scenario adapts a reported interview theme; 55 are original practice. `manifest.json`
supports the integration. On 4 Oct (later) the user asked for it in the website: `interview_site.py` now
generates an **Interview practice** sidebar group (how-to page + Fresher, Junior → Mid-level, Senior, Every stage)
from `interview/`, and each handbook module links to its question. See `recent_updated.md` §6.

- **Published (private):** https://claude.ai/artifact/QtxCGPQLVM2TmYGzNizSpY
- **Offline copy:** `index.html` in this folder: double-click it, no internet needed
- **Local site:** http://localhost:8173 — served by Docker (`docker compose up -d --build`, see `DOCKER.md`); the old `python3 -m http.server` is retired.

---

## 1. At a glance

| Item | Value |
|---|---|
| Modules | 57 markdown modules + 5 interview pages generated from `interview/` + the Command Decoder page (63 sidebar pages) |
| Command Decoder | 460 cards in 17 families (98% of 18,398 command uses matched); a collapsed decode box in 517 submodules |
| Total content | ~155,000 lines of markdown |
| 3D course map | 123 topics on 5 levels (Fresher → Senior/Lead), 11 tracks |
| Handbook links inside the map | 976, all resolving; includes 120 links to source-domain sections |
| Internal page links | Validated in both generated outputs by `tests/test_source_integration.py` |
| Problem-library entries | ~470 real-world problems across modules 41–52 (about 40 per module) |
| Practice sites | 80, checked live, free first |
| Independent technical reviews | Every module, roughly 900 corrections in total |
| Source index | 488 saved research entries, 1,602 source associations, 1,423 distinct URLs across 12 domains; includes 28 curated cases |
| Output size | `index.html` / `artifact.html` ≈ 15.1 MB each (14.4 MiB), close to the 16 MB artifact limit; served gzipped at ≈ 4.3 MB |
| Build status | `docker compose up -d --build` (or `python3 build_site.py`) → 63 modules, 3D map on, no warnings |
| Pre-publish scan | 0 personal-data or secret findings, 0 external resource loads |

---

## 2. What was asked, and what was done

| # | Your request | What was built |
|---|---|---|
| 1 | Troubleshooting commands for every area, with purpose, examples and sample output; offline; AWS and on-prem | Command reference 01–20 (storage, network, CPU, memory, processes, logs, systemd, DNS, SSH, permissions, packages, time, kernel, Docker, Kubernetes, AWS, web/TLS, cheat sheet) |
| 2 | A web UI with clickable indexing per module and sub-topic | `build_site.py` → one offline `index.html`: grouped sidebar, 2-level index from `##`/`###`, full-text search, scrollspy, copy buttons, dark/light theme |
| 3 | Windows and macOS in more detail, show the output and what it means | Windows (17) rewritten in depth, new macOS module (20), sample outputs with explanations across modules |
| 4 | Your real case: Apache running 3–4 apps on 443 while Dokploy needed it | Module 21: a full runbook — inventory, which apps are used and needed (logs), dispatching Apache, Docker + Dokploy deploy, routing legacy sites through Traefik, cutover, rollback |
| 5 | How to find what runs on which port, and how to "dispatch" it | Module 22: port → PID → unit → config → logs on Linux, Docker, Swarm, Kubernetes, Windows, macOS; safe stop/disable/mask ladder |
| 6 | Learn each topic, then troubleshoot it; why each step, and what the next step is | Learn modules 27–33 and 36–39; playbooks 21–26 use Goal / commands / sample output / What it means / Why this step / Next step |
| 7 | Why the system is slow; network speed | Playbooks 23 (60-second checklist, USE method) and 24 (iperf3, mtr, MTU, retransmits) |
| 8 | A 3D map of the courses | Offline canvas 3D map: floors = levels, sectors = tracks, prerequisite edges, guided path, filters, flat 2D view, list view, progress tracking |
| 9 | "I use KodeKloud — tell me which course, video or note first" | Verified KodeKloud catalog (`research/kodekloud-map.md`); study paths in modules and on every map topic, in order: course → note → video → lab |
| 10 | Your fix was moving Apache to 81/444 — answer that, plus many more deployment patterns | Module 35: your fix analysed and how to finish it, 12 deployment patterns, recipes, "client says deploy on port X" procedure |
| 11 | Make it fresher → senior | Career ladder (40), stage tags on every topic, map floors labelled with career stages, senior architecture and leadership (39) |
| 12 | Publish it as an artifact (desktop is enough) | `artifact.html` built to the artifact rules, published and updated in place (Versions 1–8) |
| 13 | Go beyond your own incidents: real community problems and your open-source tools | Problem libraries 41–51, tool deep dives (Traefik, Dokploy, CI/CD, Wazuh, observability), day-to-day module (52), toolbox map (53) |
| 14 | Practice sites like devops.games, free first, paid with links | Practice Arena (54): 80 sites, free → freemium → paid, weekly practice plans per stage |
| 15 | Use more space in the 3D map; flat 2D must keep working | Wider, centred, de-cluttered 3D view; label collision handling; hover/selection bug fixed; flat 2D unchanged |
| 16 | An on-premise / cloud selection | 🏢 On-prem · ☁️ Cloud · Both selector in the top bar and the map; page 55 with both paths |
| 17 | Put the interview questions into their module → submodule (fresher → SSH, permissions…) | Interview practice group: how-to page + Fresher, Junior → Mid, Senior, Every stage pages, generated from `interview/` (`interview_site.py`) |
| 18 | What each command means and why it is effective (ping vs mtr), for every module and submodule | Command Decoder page (`commands/`, `command_decoder.py`) + a decode box under every submodule heading |
| 19 | A content UI with more effect, like the 3D map | `site_ui.py`: module heroes, glass submodule cards, terminal code frames, group colour tones, reading progress, launchpad with a CSS-3D tower |
| 20 | Check every feature for issues ("I found 2–3 bugs myself") | Headless-Chrome QA pass; fixed module jumps, map legend, favicon, sidebar collapse, map topic toggle |
| 21 | Docker instead of running the Python script | `Dockerfile` (build → nginx-unprivileged → export), `compose.yaml`, `docker/nginx.conf`, `DOCKER.md` |

---

## 3. Every module, by sidebar group

### Start here

| File | Title | Lines |
|---|---|---|
| README.md | Home / Triage | 175 |
| 34-roadmap.md | Zero-to-Hero Roadmap | 441 |
| 40-career-ladder.md | Career Ladder: Fresher → Senior | 2,366 |
| 55-paths-onprem-vs-cloud.md | On-Prem or Cloud Path | 628 |
| 54-practice-arena.md | Practice Arena | 887 |
| 56-sources-and-verification.md | Sources & Verification | Narrative plus generated source index |

### Real incidents & playbooks

| File | Title | Lines |
|---|---|---|
| 21-case-apache-443-dokploy.md | Case: Apache vs Dokploy on 443 | 4,776 |
| 22-playbook-ports-inventory.md | Who Owns This Port? | 3,578 |
| 23-playbook-slow-system.md | Why Is It Slow? | 5,822 |
| 24-playbook-network-speed.md | Network Speed | 4,166 |
| 25-playbook-site-down.md | Site Down: DNS·TLS·Proxy | 4,793 |
| 26-playbook-containers-k8s.md | Docker & K8s Incidents | 6,854 |
| 35-deployment-patterns.md | Deployment Patterns | 4,157 |

### Real-world problems & OSS toolbox

| File | Title | Lines |
|---|---|---|
| 52-devops-day-to-day.md | DevOps Day to Day | 2,363 |
| 45-dokploy-and-self-hosted-paas.md | Dokploy & Self-Hosted PaaS | 2,332 |
| 43-traefik-and-reverse-proxies.md | Traefik & Reverse Proxies | 2,787 |
| 47-cicd-gitlab-jenkins-actions-argocd.md | CI/CD Toolbox | 2,198 |
| 48-wazuh-and-security-tools.md | Wazuh & Security Tools | 2,653 |
| 49-observability-stack-problems.md | Observability Stack | 2,899 |
| 51-problems-databases-storage-backup.md | Databases & Backups: Problems | 2,161 |
| 50-problems-cloud-iac-proxmox.md | Cloud, IaC & Proxmox: Problems | 2,539 |
| 44-problems-docker-swarm-registry.md | Docker, Swarm & Harbor: Problems | 2,219 |
| 46-problems-kubernetes.md | Kubernetes: Problems | 2,338 |
| 41-problems-linux-systems.md | Linux & systemd: Problems | 2,341 |
| 42-problems-network-dns-tls-vpn.md | Network, DNS & TLS: Problems | 2,296 |
| 53-oss-devops-toolbox.md | OSS DevOps Toolbox Map | 1,816 |

### Learn: fresher → senior

| File | Title | Lines |
|---|---|---|
| 27-learn-linux.md | Linux | 8,542 |
| 28-learn-networking.md | Networking, DNS & TLS | 5,945 |
| 29-learn-webservers-proxies.md | Web Servers & Proxies | 6,965 |
| 30-learn-docker.md | Docker | 7,201 |
| 31-learn-kubernetes.md | Kubernetes (CKA) | 7,422 |
| 32-learn-performance-observability.md | Performance & Observability | 7,454 |
| 33-learn-cicd-iac-sre.md | CI/CD, IaC & SRE | 7,026 |
| 36-learn-cloud-aws.md | Cloud & AWS | 6,449 |
| 37-learn-security-devsecops.md | Security & DevSecOps | 11,088 |
| 38-learn-databases-ops.md | Databases for DevOps | 7,264 |
| 39-learn-senior-architecture.md | Senior: Architecture & Leadership | 6,839 |

### Command reference

| File | Title | Lines |
|---|---|---|
| 01-storage-disk.md | Storage & Disk | 309 |
| 02-network.md | Network | 295 |
| 03-cpu-performance.md | CPU & Performance | 168 |
| 04-memory.md | Memory | 142 |
| 05-processes.md | Processes | 163 |
| 06-logs-journal.md | Logs & Journal | 113 |
| 07-services-systemd.md | Services & systemd | 115 |
| 08-dns.md | DNS | 125 |
| 09-ssh-remote-access.md | SSH & Remote Access | 152 |
| 10-users-permissions-security.md | Users & Permissions | 155 |
| 11-packages.md | Packages | 119 |
| 12-time-ntp.md | Time & NTP | 93 |
| 13-kernel-system.md | Kernel & Hardware | 125 |
| 14-docker-containers.md | Docker & Containers | 165 |
| 15-kubernetes.md | Kubernetes | 206 |
| 16-aws-cloud.md | AWS | 253 |
| 17-windows.md | Windows | 469 |
| 20-macos.md | macOS | 311 |
| 18-web-http-tls.md | Web, HTTP & TLS | 168 |
| 19-cheatsheet.md | Cheat Sheet | 162 |

---

## 4. Timeline

| When | Stage | Result |
|---|---|---|
| 9 Aug 2026 | First session | Command reference 01–20, the offline web UI, Windows/macOS detail, sidebar highlight fix |
| 3 Oct, night | Phase A (parallel writers) | Playbooks, learn modules, KodeKloud research, first 3D map code — cut off by the usage limit at ~3:40 am |
| 3 Oct, morning | Recovery run | Truncated modules finished, 3D map completed, `artifact.html` build added; reviews of 22, 24, 28 |
| 3 Oct, evening | Batch 1 | Security (37) finished, roadmap (103 topics), Traefik (43), Dokploy (45), CI/CD (47), Wazuh (48) → **Version 1 published** |
| 3 Oct, night | Batch 2 + extras | Observability (49), Cloud/IaC/Proxmox (50), Databases & backups (51), Practice Arena (54), On-prem vs Cloud page (55) and selector, 3D map spacing → **Version 2** |
| 4 Oct, after 11 pm | Batches 3 and 4 | Docker/Swarm/Harbor (44), Kubernetes (46), Day to day (52), Linux (41), Networking (42), Toolbox map (53), practice labs on map topics → **Version 3** |
| 4 Oct, overnight | Reviews 5a–5c | 115 + 103 + 149 corrections; username scrub → **Versions 4, 5, 6** |
| 4 Oct, morning | Reviews 5d–5e | 176 + 260 corrections → **Version 7** |
| 4 Oct, morning | Batch 6 (final pass) | Completeness check against all 16 requests above, consistency fixes, scan clean → **Version 8** |

### Review corrections by batch

| Review batch | Modules | Corrections |
|---|---|---|
| Recovery run | 22, 24, 28 | (part of the recovery run) |
| 5a | 21, 35, 45, 43 | 115 |
| 5b | 47, 48, 25, 26 | 103 |
| 5c | 30, 31, 29, 23 | 149 |
| 5d | 27, 32, 33, 36 | 176 |
| 5e | 37, 38, 39, 40, 49, 50, 51 + targeted checks of 41, 42, 44, 46, 52–55 | 260 |

Examples of what the reviews caught:

- Current Dokploy installs no longer create a Redis service.
- The example Traefik Compose file had no `container_name`, so every `docker logs traefik` command would have failed.
- Wazuh is now on 4.14.8 (4.14.0 has known crashes); Filebeat certificate names and an error code were wrong.
- The GitLab runner must be pinned together with the matching `gitlab-runner-helper-images` package.
- Jenkins rotated its apt signing key in 2026.
- `docker volume prune` and `docker system prune --volumes` no longer remove named volumes on Engine 23+.
- The March 2026 Trivy supply-chain compromise (CVE-2026-33634) is now covered in the Security module.
- 38 commands inside tables had a stray `\` before `|`, which made copied commands wrong.

---

## 5. How the handbook is built

| Piece | What it does |
|---|---|
| `NN-*.md` modules | The content. `##` headings become first-level sidebar entries, `###` the second level |
| `build_site.py` | Converts every module with python-markdown (`fenced_code`, `tables`, `toc`, `md_in_html`), builds the sidebar, search, map and selector, writes `index.html` and `artifact.html` |
| `roadmap.json` | The 3D map data: levels (with career stages), tracks, 123 topics, prerequisites, study paths, links, guided-path order, `env` tag per topic |
| `index.html` | The offline handbook (a complete HTML page) |
| `artifact.html` | The same content shaped for claude.ai artifacts (starts with `<title>`, no html/head/body tags) |
| `research/` | Research catalogs (`*.json`), the KodeKloud map, the Ops Ladder text, practice-site research, roadmap backups, `prepublish_scan.py` |
| `source_catalog.py` | Builds the offline source index from the 12 saved problem catalogs, with explicit source status, filters and links to modules |
| `research/source-checks.json` | Three official URLs with a date and the exact claim checked during this integration; historical `verified` flags remain distinct |
| `tests/test_source_integration.py` | Checks source classification, URLs, generated IDs and links, embedded JavaScript syntax, roadmap links and prerequisite order |

### Updating the handbook

```bash
cd DevOpsLearning                                      # this folder
python3 build_site.py                                  # must end with "no warnings"
python3 -m unittest discover -s tests -v               # build integrity and source semantics
python3 research/prepublish_scan.py artifact.html      # personal data / secrets / external loads
```

Then republish `artifact.html` to the same artifact URL (ask Claude to "republish the handbook to the existing link").

### Writing conventions used everywhere

- First line `# NN — Title`; `## N. Section` and `### ` sub-entries; short, unique headings without links.
- Playbook steps: **Goal** → commands → sample output → **What it means** → **Why this step (now)** → **Next step**.
- Problem entries: **Seen as** (exact error) → **Why it happens** → **Diagnose** → **What the output tells you** → **Fix** → **Why this fix works** → **Prevent it** → **Next step** → community links and search links.
- Sample data uses documentation IPs (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24), example.com and generic users (`ops`, `deploy`, "Sam").
- On-prem/cloud content: a `<div class="env" data-env="onprem" markdown="1">` (or `cloud`) block with a blank line after the opening tag and before `</div>`; never nested; no `##` heading inside.
- Roadmap topics: every topic has `env` (`both`, `onprem`, `cloud`); study items are ordered course/note → video → lab; `heading` values must match a real `##`/`###` heading.

---

## 6. Worth knowing

### Keeping it current

- **Versions go stale.** Dokploy, Traefik, Wazuh, Kubernetes and Docker change quickly. Plan a refresh pass every 3–6 months; the `research/` catalogs keep every source link, so a refresh can start from them.
- **KodeKloud's catalog changes.** Course names and URLs were verified on 3 October 2026 (`research/kodekloud-map.md`). Re-check before buying or scheduling a course.
- **Practice sites come and go.** Play with Docker and Play with Kubernetes shut down in March 2026; Katacoda became Killercoda. The Practice Arena (54) lists what changed — re-check it occasionally.
- **Sample outputs are illustrative.** They were reviewed for realism, but exact columns and wording vary with distro and tool versions. Always compare with your own system.

### Sources and limits

- **Prior access limitation:** the earlier research run could not retrieve Stack Overflow, Server Fault or Reddit. Do not repeat the unsupported blanket explanation that these sites universally opted out or block all tools. The current selection contains 19 retrieved community threads (including Server Fault), seven first-party reports/advisories, and two excerpt-only Reddit cases (Wazuh and Terraform). Search links remain discovery aids.
- **Source status is visible:** 994 associations are marked reported checked in the original research, 573 are discovery links, 2 are unverified, and 5 associations refer to the three official URLs checked for specific claims on 4 October. Related readings account for 19 threads, seven reports and two excerpts. Two newly read URLs replace prior recorded labels rather than creating duplicate associations. Counts come from historical catalogs plus both community JSON files, not a fresh review of every source.
- **Offline integration:** use Sources & Verification in Start here, the source notice above each problem library, or the related source link on a course-map topic. Filter by domain, source status or text. Global search also finds the collapsed source entries and opens them.
- **Accessible sources** that were used: GitHub issues and discussions of each tool, official forums (Traefik, Docker, GitLab, Kubernetes, Grafana, HashiCorp, Jenkins, Let's Encrypt, Proxmox, Elastic, CrowdSec), the Wazuh community group, official documentation and public postmortems.
- **Handbook troubleshooting/deployment commands were not executed on this machine.** Build, source validation and browser checks are separate from reproducing the documented operational incidents.
- **Integration checks:** `python3 -m unittest discover -s tests -v` checks both HTML outputs: source classifications, domain coverage, exact case links, solution disclosures, unique IDs, internal anchors, offline assets, JavaScript syntax and map ordering/links. Interview checks cover all 56 modules, 112 unique prompt IDs, teaching sections, local links, provenance and exclusion from the site. Browser checks use the existing port 8173 server. No map-completion action is authorized. These checks do not verify every external URL or run the proposed labs.
- **Latest verification (4 October):** all 14 automated checks passed. The browser on 8173 displayed the 28-case directory, navigated to the new Dokploy label-loss case, expanded its scoped workaround/verification answer, and filtered exactly seven research entries with first-party reports. No browser console errors were observed in that check. The publication scan found zero personal/secret findings and zero external resource loads; six historical non-documentation IP literals remain listed by the scanner. The externally published artifact was not updated.

### Using the site

- **The artifact is private.** Only you can open the link until you share it from the page's Share menu.
- **Progress ticks on the map are stored in each browser.** They do not sync between computers or between the offline file and the artifact.
- **The on-prem/cloud choice is remembered per browser too.** "Both" shows everything.
- **Local preview availability depends on the process serving it.** The user's active preview is port 8173; the offline `index.html` can also be opened directly.
- **A hidden browser tab pauses the 3D map's animation.** That is normal browser behaviour; it redraws as soon as the tab is visible.
- **The page is large (≈ 12.0 MiB).** The first search takes a moment while it builds its index.

### Working with Claude on this project

- **Usage limits:** big parallel runs used up a 5-hour usage window in under an hour three times. Batches of 4–5 agents, with a republish after each, worked reliably.
- **Generic names only:** writer agents once picked up your username from the folder path; it was scrubbed, and `research/prepublish_scan.py` now flags it. Always run the scan before publishing.
- **The scratchpad is temporary.** Anything worth keeping (research, scripts, backups) lives in `research/`.
- **Adding a tool:** ask for a new module in the problem-library or toolbox format; it then needs a sidebar entry in `build_site.py`, a few topics in `roadmap.json` (with `env` and ordered study items), a row in `README.md`, a rebuild with zero warnings, the scan, and a republish.

### Ideas for next steps

- A refresh pass in early 2027 (versions, KodeKloud catalog, practice sites).
- New modules for tools you adopt next (for example Ceph, Vault in production, or a service mesh).
- Your own incident notes: the day-to-day module (52) has a 90-day "learn from your own tickets" plan — your notes could become new playbook entries.

## Checkpoint 2026-11-09 01:45 IST
See recent_updated.md §20. Built locally but not yet published: map panel in learning order, job-search unlock at milestones, universal back-nav pill, 128 learning tools in study paths, Practice Arena 165 sites, 240 exact practice deep links. Next: pre-publish QA, then artifact Version 11, then more incident sources and practice sites for decision drills.
