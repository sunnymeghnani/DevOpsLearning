# 57 — Method: PROTECT & the Risk Ladder

Every stack breaks in its own way, but the questions a senior asks are always the same: who is
hurt, who needs to know, what do I actually see, what one idea explains it, how risky is the next
step, how small can I make it, and what stops it next time. This module turns those questions into
one loop, **PROTECT**, and one scale for the risk of each action, the **risk ladder**: eight rungs
from "look" to "repair data", with a column for the case every self-hoster knows, one box and no
replica. The playbooks in this group are the stack-specific walks; this page is the method they share.

How to use it:

- **Something is broken and people are waiting:** open [the PROTECT card](#the-protect-card), do P and R in the first ten minutes, then run the inner loop.
- **You are about to change something risky:** read section 4 (the ladder), 5 (window or live fix?) and 6 (before you press Enter).
- **You are learning:** read sections 1–3 once, walk the worked examples (8 and 9), then play the three decision drills. L0–L1 start with rungs 1–4 and the "Do not" column; L3–L4 own the single-box column, the authority line and the decision message.

Sections link to the modules that teach the detail; study them as the [roadmap](34-roadmap.md#study-method) suggests.

> ⚠️ Commands are documentation to study, not to paste. UPPERCASE words are placeholders
> (SERVICE, NODE, FILE, OLD_IP, NEW_IP); addresses use the documentation ranges and names use example.com.

---

## The PROTECT card

> 🖨️ The printable card: one A4 page or one laptop screen. The module's print button prints only this card.

```text
PROTECT: troubleshoot anything, hurt nobody

P Protect    Who is hurt? Getting worse? Safest way to stop the harm NOW?
             roll back · shift or drain · shed load · maintenance page · stop writes
             Save 60 s of evidence before anything that destroys it.
R Report     What is affected (user words) · since when · what we are doing ·
             next update at HH:MM · who leads, who types.
O Observe    Read-only. Reproduce with one command. What changed? What still works?
             Resources: utilisation, saturation, errors. Services: rate, errors, duration.
T Theorise   ONE explanation for ALL the evidence. "If true, then ___ is also true."
             Cheapest safe test first. 15 minutes, then the next idea or more people.
E Evaluate   Lowest rung that helps? Undo in under 5 min, written down? Widest reach?
             State or data involved? Live, or a short window?
C Change     One change. One node, route or client. Validate, apply gently, watch the
             same probe N minutes, then widen or revert. Never stack fixes.
T Teach      Five-line note. What would have caught it sooner? Remove the class.

RISK LADDER  (climb only when the rung below cannot help)
 1 look, read-only            anyone
 2 add capacity / shift       anyone, tell the lead    stateful? treat as 7
 3 restart ONE replica        anyone, tell the lead    no replica? it is an outage
 4 roll back                  anyone, tell the lead    data or format changed? stop
 5 change config, one node    second pair of eyes; undo written
 6 change everywhere          canary, one, half, all; a window on a single box
 7 restart a stateful service lead decides; backup restored once; window
 8 repair data                lead + owner; copy first; never the only copy in place

BEFORE ANY CHANGE (rung 5 and above)
 [ ] snapshot or backup taken, and I know it restores
 [ ] undo command written where others can see it
 [ ] validated: nginx -t · apachectl configtest · netplan try · kubectl diff ·
     terraform plan · docker compose config
 [ ] console or out-of-band access open (network, SSH, DNS, firewall)
 [ ] one canary first · watch ___ min · roll back if ____________ by __:__
 [ ] people told: what, when, how long, how we go back

ONE BOX, NO REPLICA?  snapshot → prepare the fix on the side → switch over →
 short announced window → TTL lowered one old TTL ahead, lease half an old lease.
```

---

## 1. Why one method across stacks

Tools change every two years; the questions do not. Google's SRE book describes troubleshooting
as one loop (triage, examine, diagnose, test, treat) whatever the product, and the "generic
mitigations" article lists moves that work **before** you understand an outage: roll back, drain,
degrade, add capacity, block, quarantine. Two adjustments make the goal honest:

1. **Least harm, not zero downtime.** Harm is roughly users affected times minutes, and far worse
   once data is at risk. Protect **data, then service, then evidence, then speed**. A short
   announced window is often the safer choice: GitLab upgraded GitLab.com's database in a planned
   window after rehearsals, and GitHub in 2018 chose a day of degradation over losing writes. See
   [SLO negotiation](39-learn-senior-architecture.md#slo-negotiation-l4-leadsre).
2. **Zero downtime is built before the change, not won during it:** a second copy (replica,
   parallel instance, second port), a rollback that has been tried, a TTL or lease lowered ahead.
   On one box with no replica, restarting a stateful service **is** downtime: build a temporary
   second copy, or take a short window and say so.

> 💡 Low rungs are not automatically safe: section 4 shows where each rung bites.

---

## 2. The PROTECT loop

The name is the priority: protect users, protect data, protect evidence.

| | Step | The question a senior asks | Output |
|---|---|---|---|
| **P** | **Protect** | Who is hurt, is it getting worse, what safest thing stops the harm now? | harm contained |
| **R** | **Report** | Who needs to know, who leads, when is the next update? | first message, roles, timeline |
| **O** | **Observe** | What do I actually see, from where, and what changed just before? | evidence saved, read-only |
| **T** | **Theorise** | What one explanation fits all the evidence, and what cheap safe test could prove it wrong? | one hypothesis, a timebox |
| **E** | **Evaluate** | Lowest rung that helps? Undo? Reach? Now, or in a window? | a rung, a written undo |
| **C** | **Change** | Smallest change, how will I know in N minutes, what makes me turn back? | one change, checked |
| **T** | **Teach** | What would have caught this sooner, and what removes the whole class? | five-line note, one prevention |

**How it runs.** P and R fill the first ten minutes. O, T, E, C is the inner loop: one hypothesis
and one change per pass; a failed pass returns to O with the change reverted. **Theorise before
you touch, Teach after you finish.** For a **planned change** start at O; P then means "what keeps
users served while I work" and R is the announcement.

### Do, do not, techniques

| Step | Do | Do not | Low-downtime techniques · read more |
|---|---|---|---|
| **P** | Size up in two minutes; mitigate from rungs 1–4; stop writes if data is at risk; save 60 s of evidence first | root-cause while users are down; restart "to see"; mitigate with something you cannot undo | rollback, drain, VIP failover, block one client, kill switch, read-only mode · [Stabilise before root cause](25-playbook-site-down.md#stabilise-before-root-cause), [Mitigate first](33-learn-cicd-iac-sre.md#step-16-mitigate-first) |
| **R** | Within ten minutes: impact in user words, since when, next update; one person decides, one types; declare early | go silent; several people changing production; announce an unproved cause | an out-of-band channel if DNS or chat may be down · [Communicating during an outage](25-playbook-site-down.md#10-communicating-during-an-outage), [Incident command](39-learn-senior-architecture.md#incident-command-l4-leadsre) |
| **O** | Reproduce with one command; read who is **not** affected; ask what changed; USE for resources, RED for services | change things "to see what happens"; trust a number before you know what it measures | all rung 1 · [the bypass ladder](25-playbook-site-down.md#where-to-stand-the-bypass-ladder), [find what changed](23-playbook-slow-system.md#find-what-changed-in-the-last-24-hours) |
| **T** | One hypothesis and its prediction; cheapest read-only test; 15-minute timebox; keep ruled-out ideas | keep the first story because it was first; test two ideas with one change | a scratch copy, a debug container, a snapshot clone · [Effective troubleshooting method](33-learn-cicd-iac-sre.md#effective-troubleshooting-method) |
| **E** | Undo, reach, state? Write the undo **first**; snapshot and know it restores; choose live or window | fix forward when a rollback exists; call it "small" because it is one node | two-way doors, shrink the reach, lower TTL ahead · [CAB-lite](39-learn-senior-architecture.md#change-management-and-cab-lite-l2-mid), [blast radius](39-learn-senior-architecture.md#failure-domains-and-blast-radius-l2-mid) |
| **C** | Say "doing X now"; one change on one node or client; reload over restart; watch the same probe; no better, revert | change everywhere at once; stack fixes; leave an emergency edit out of Git | canary, start-first rolling, blue-green · [Deployment strategies](33-learn-cicd-iac-sre.md#3-deployment-strategies), [P12 blue/green](35-deployment-patterns.md#p12-bluegreen-on-two-ports) |
| **T** | Five-line note: symptom, wrong guess, deciding evidence, fix, check first; one prevention with an owner | blame anyone; write "be more careful" | a replica, a probe, an exercised rollback · [Blameless postmortems](33-learn-cicd-iac-sre.md#blameless-postmortems), [classes of incidents](39-learn-senior-architecture.md#eliminating-classes-of-incidents-l4-leadsre) |

### The loop by stack

| Stack | P: protecting move | O: read-only look | T: safe test | T: remove the class |
|---|---|---|---|---|
| Linux host | stop the runaway unit, not the server | `journalctl -p err --since "1 hour ago"`, `ss -ltnp` | `sshd -t`, `visudo -c` | NIC names pinned by MAC |
| Docker / Swarm | `docker service rollback SERVICE`; drain | `docker service ps --no-trunc SERVICE` | same image beside it, no ports | health checks, start-first, exact tags |
| Kubernetes | `kubectl rollout undo deployment/NAME` | `kubectl get events --sort-by=.lastTimestamp` | `kubectl debug`, `kubectl diff` | PDBs, probes, requests |
| Reverse proxy | route back to the old upstream | one request's log line; `curl -v --resolve` | upstream direct, then via proxy | config test in CI |
| Database | stop the damaging writer; read-only | locks, connections, replication lag | `EXPLAIN`; a restored copy | scheduled restore drills |
| Network / DNS | put the old record or address back | `dig @SERVER NAME`, `ip route get ADDRESS` | ask old and new the same name | a second resolver |
| Storage / NAS | stop the consumers first | `zpool status -x`, SMART, kernel log | test on a snapshot clone | snapshots plus replication |

---

## 3. Six facts for any new stack

Before you operate a tool you have never run, find these six. They are the per-stack part of the method.

1. **State:** where are data and config, and how are they backed up and restored?
2. **Look:** how do I see status, logs and live config without changing anything?
3. **Validate:** how do I test a change first (config test, dry run, diff)?
4. **Apply:** reload or restart, and who feels it?
5. **Undo:** what is the rollback, and how long does it take?
6. **Reach:** what does it depend on, and what depends on it?

For Pi-hole, fact 6 is the one that matters: image pulls, logins and monitoring all need DNS.

---

## 4. The risk ladder

Climb only when the rung below cannot help. Before stepping up: have I used the rungs below? Can I
undo this in under five minutes, and is the undo written down? What is the widest thing it can
touch, and is state or data involved? One missing answer means you are not ready.

| # | Action | Make it reversible | Limit the blast radius | Only one box, no replica | Who decides |
|---|---|---|---|---|---|
| 1 | **Look:** logs, status, queries, a filtered capture | save what you see | filtered, counted captures; no debug logging on a hot box | copy evidence off early if the box may be failing | anyone |
| 2 | **Add capacity or shift:** scale out, drain, move a VIP, block a client, shed load | note old values; scale back, uncordon | a slice first. **Adding a member to a stateful cluster is a data change: rung 7** | nowhere to shift, so shed: pause backups and cron, rate-limit; or build a temporary second instance (section 8) | any responder; tell the lead |
| 3 | **Restart one replica** | the pool heals it; save its logs | one of N; the rest carry N−1; wait for healthy | **with no replica this is an outage:** reload if possible, validate config, know the start time, announce | any responder; tell the lead |
| 4 | **Roll back:** previous image, config, `git revert` | keep the new version to roll forward | only what changed. **Data format or schema changed? Rung 8** | keep the previous image and config **on the box**; a snapshot for in-place upgrades | any responder; tell the lead |
| 5 | **Config on one node:** vhost, route, host network, firewall rule | copy the old file; timed revert where one exists | node out of rotation. **Is it really local?** Routing policy and cluster objects are not | shrink by object: one vhost, one container, one client; console open; reload | keyboard plus second pair of eyes |
| 6 | **Change everywhere:** fleet run, daemon or proxy setting, upgrade, network-wide DHCP option | staged rollout that stops by itself | canary, one, half, all, with watch time | stage by **preparation**: build beside the old, validate, switch; daemon restarts need a window | lead plus reviewer; change record |
| 7 | **Restart a stateful service:** database, DNS or DHCP server, quorum member, Docker on a Swarm manager | not undoable: a backup restored once, clean shutdown, quorum checked | one member at a time; park consumers; never with an upgrade | **a planned window**, or the parallel run: both live, clients moved, old retired last | the lead, with the owner |
| 8 | **Repair data:** restore, manual SQL, pool repair, a failover that drops writes | one-way: copy first, work on the copy | stop writes; smallest unit; two people; statements in a file | copy **off** the box first; restore to the side and switch | the lead, recorded, with the data owner |

**Authority in one line:** rungs 1–4 are two-way doors any responder may use; rungs 5–6 need a
second pair of eyes and a written undo; rungs 7–8 need the lead and normally a window. If the
service is already fully down, rung 7 gets cheaper; rung 8 never does.

### Where each rung bites

| Rung | Public incident | Lesson |
|---|---|---|
| 1 | SRE book: a test can change what later tests show | measure lightly |
| 2 | Monzo 2019: six servers added for capacity answered for data they did not hold | capacity for state is a data change |
| 4 | SRE book: a rollback never tested failed mid-incident | try the rollback before you need it |
| 5 | Cloudflare 2020: one policy line on one router pulled backbone traffic to one site for 27 minutes | ask what the setting talks to |
| 6 | SRE book: a global push judged low-risk got a weak canary | canary the harmless-looking change |
| 7–8 | GitHub 2018: 43 seconds of network loss caused a cross-region database failover | data over speed; fence automatic failover |

---

## 5. Window or live fix?

Choose a short, announced window when **any** of these is true:

- the step is rung 7 or 8 on a single instance;
- it is a one-way door: major upgrade, schema or format change, DHCP server handover;
- the rollback is untested, or slower than the window;
- the live path needs two changes at once;
- a mistake would cut your own access (the only link, DNS or login path).

Make it short with preparation, not speed: rehearse on a copy; prepare on the side so the window
holds only the switch; lower the DNS TTL at least one old TTL ahead (Cloudflare
suggests 24–48 hours); lower a DHCP lease at least half an **old** lease ahead, since clients renew
at half the lease (RFC 2131); snapshot right before; set a stop time after which you roll back;
leave part of the old world untouched. A live fix is right for rungs 1–4, or a rung 5–6 shrunk to
one object, validated and undoable in minutes. Example: the
[Apache case cutover](21-case-apache-443-dokploy.md#9-phase-8-cutover-with-minimal-downtime).

---

## 6. Before you press Enter

[The change checklist](52-devops-day-to-day.md#the-change-checklist) plans the change; this is the
ten-line check for the moment before the command (rung 5 and above):

1. One sentence: what changes, and why.
2. Snapshot or backup taken now, and I know it restores.
3. The undo is written in the ticket or channel, with its duration.
4. Validated with the tool's own check (table below).
5. Console or out-of-band access open for network, SSH, DNS or firewall work.
6. One canary first: one node, route, stack or client.
7. The watch: which probe, for how many minutes.
8. The stop condition: "if X by HH:MM, I roll back".
9. People know: what, when, how long, what they will notice, how we go back.
10. One change. Anything else waits for the next pass.

| Tool | Validate first | Apply gently | Undo | Limit to know |
|---|---|---|---|---|
| Nginx | `nginx -t` | `nginx -s reload` | previous file, reload | bad config on reload keeps the old one; on restart it stays down |
| Apache | `apachectl configtest` | `apachectl graceful` | previous file, graceful | a clean syntax check does not promise a clean restart |
| Traefik | none for the file provider | the file is watched: **saving is deploying** | previous file | edit a copy; test a spare hostname with `curl --resolve` |
| Netplan | `netplan try` | confirm within 120 s | reverts by itself | check the revert happened; console first |
| Compose | `docker compose config` | one stack at a time | previous file and tag | per-container settings need a recreate |
| Swarm | read the update flags | `--update-parallelism 1 --update-order start-first --update-failure-action rollback` | `docker service rollback SERVICE` | previous spec only |
| Docker daemon | which keys reload | `systemctl reload docker` | previous `daemon.json` | `dns` needs a restart; on a Swarm node dockerd refuses live-restore |
| Kubernetes | `kubectl diff -f FILE` | rolling; `kubectl rollout status` | `kubectl rollout undo` | `diff` exits 1 on a difference |
| ZFS | `zfs snapshot POOL/DATASET@before` | one dataset first | a clone, or `zfs rollback` | rollback discards everything since |
| DNS record | lower the TTL ahead | one record | put it back | as fast as the **old** TTL allows |

---

## 7. Messages

Incident updates live in [Site down §10](25-playbook-site-down.md#10-communicating-during-an-outage)
and [DevOps day to day §9](52-devops-day-to-day.md#9-on-call-and-incident-response-in-practice); the
maintenance notice in [Stakeholder communication](39-learn-senior-architecture.md#stakeholder-communication-l3-senior).
Three forms were missing. All carry four facts: **what is affected, when, what you will notice, how we go back.**

**1. Planned change with a freeze (parallel run).**

```text
[PLANNED] DNS server move, Tue 14:00 to Thu 14:00 UTC. No interruption is expected.
What changes:  a new DNS server runs beside the old one; devices move to it by themselves.
Freeze:        no DNS record changes. Need one urgently? Ask TEAM, we apply it to both.
You notice:    nothing. If names stop resolving, tell CHANNEL or call PHONE.
Way back:      devices are pointed at the old server again; complete within one hour.
Short window:  Thu 13:30-14:00 UTC the old address is retired; a few seconds of delay possible.
```

**2. A risky step during an incident (rung 6 and above).** Say it, then pause for objections.

```text
[DECISION 10:42 UTC] Next step: restart the database on db01 (single instance).
Why:        connections exhausted; lower steps (kill idle sessions, raise the limit) did not hold.
Impact:     all apps lose the database for about 90 seconds.
Prepared:   backup from 10:30 verified; config validated; console open.
Turn back:  not accepting connections by 10:47 -> restore the 10:30 config and restart again.
Strong objections? Proceeding at 10:45.     Lead: NAME   Keyboard: NAME
```

**3. Done, or rolled back.**

```text
[DONE 14:05 UTC] DNS move complete. The old address was retired at 13:42; the new server has
answered every query since. The record freeze is lifted. Short write-up by Friday.

[ROLLED BACK 13:50 UTC] We returned to the old DNS server at 13:47 after lookups from the
Docker hosts were refused. Nothing is degraded now. A new date follows once we know why.
```

Always user words, times with a zone, the next update; no unproved cause, no fix time you cannot keep.

---

## 8. Worked example 1: move a DNS server with no downtime

**The situation:** a self-hosted Pi-hole serving a whole network (office clients, servers, Docker
hosts, a small Kubernetes cluster) must move to a new machine. It is the only resolver, may also
serve DHCP, and has no replica. The plan follows a real migration runbook, anonymised; the Pi-hole
facts come from Pi-hole's docs and forum. Pi-hole basics:
[port 53 busy, clients bypass](42-problems-network-dns-tls-vpn.md#74-pi-hole-or-adguard-port-53-busy-clients-bypass).

| Step | What the plan does | Rung |
|---|---|---|
| **P** | The old Pi-hole answers for the whole move (parallel run); backups first; never two DHCP servers | 2 |
| **R** | A record-change freeze (message 1): with two resolvers live, an edit on one gives two answers | – |
| **O** | Version, DHCP owner, other services; records exported to files. Dashboard "load 7" is the **host's** figure | 1 |
| **T** | "The import broke it" became "the import carried machine settings" (interface, listening mode, DHCP, web port). "Too many users" became "`/dev/shm` full, or per-client rate limiting", both in the FTL log | 1 |
| **E** | Parallel run, not a second full import; machine settings pinned by `FTLCONF_*` (they become read-only); an exact image tag; lease lowered ahead | – |
| **C** | Answers compared name by name; then DHCP, static hosts (`netplan try`, rung 5), Docker stacks one at a time (3), stragglers, the old address and DHCP last (7) | 3–7 |
| **T** | A second resolver as the end state; a scheduled export off the box | – |

Import the data (lists, records, groups), not the configuration, and leave the query database
behind: that **avoids rung 8**, because the old box stays the untouched original. The pattern to
carry: **with no replica, make one for the length of the move**, move clients with something on a
short timer (lease, TTL, proxy route), find stragglers in the old side's log, retire the old last.

### Checks worth making before you copy it

1. **Swarm services are not covered by live-restore.** Docker's docs say live restore applies to
   standalone containers only, and on a Swarm node dockerd refuses to start with it
   (`--live-restore daemon configuration is incompatible with swarm mode`;
   [daemon.json keys](30-learn-docker.md#daemonjson-keys-that-matter-on-prem)). A Dokploy host is
   a Swarm node, so "enable live-restore, restart Docker" takes Docker down instead of keeping its
   services up. There, set
   DNS **per service** (`docker service update --dns-add NEW_IP SERVICE` rolls task by task), or
   do the daemon restart in a window. On plain Docker hosts, enable it with `systemctl reload docker`
   and confirm it in `docker info` **before** the restart that changes `dns`.
2. **`NEW_IP,OLD_IP` is not a priority order.** Pi-hole's FAQ says clients may use either server.
   So the freeze is essential, and DHCP must hand out `NEW_IP` only (or new plus a second resolver)
   for one full lease **before** the old log counts as a list of stragglers.
3. **Lease halving.** Clients renew at half the lease and only then learn a shorter one: a one-day
   lease lowered the day before works; a seven-day lease needs four days.
4. **IP takeover can duplicate an address.** Stopping the old container frees port 53, not
   `OLD_IP`. If it is the old **host's** address, remove it there first, from the console; add it
   on the new host with `netplan try` on the real interface name; write the undo.
5. **`listeningMode: all`** can make an open resolver (Pi-hole's config reference): keep it only for
   routed or Docker-bridge clients, and firewall port 53.
6. **Clients that never ask DHCP:** fixed resolvers on servers and hypervisors, VPN configs, the
   router's forwarder, IPv6 router advertisements. List them first.

| Phase | Roll back when | Action | Back within |
|---|---|---|---|
| New server built | any DIFF on a local record | fix on the new server; no client moved | nothing to undo |
| DHCP hands out new | REFUSED or SERVFAIL from it for 5 minutes | DHCP back to `OLD_IP` only | one short lease |
| Static hosts, stacks | a host or stack cannot resolve | `netplan try` reverts; previous compose file | minutes per host |
| Old address retired | queries to `OLD_IP` time out | address off the new host, back on the old, old container started | minutes |
| DHCP handover (window) | no lease, or two offers | off on the new, on again on the old (static leases exported first) | one renewal |

---

## 9. Worked example 2: one box, one way in

**No IP after a hardware change.** A NAS loses its network after an adapter is re-seated. **O** at
the console: the interface name the system sees now against the name the saved config expects.
**E**: one way in, so every edit is rung 5, console open. **C**: the vendor's timed test reverts
unless confirmed. **T**: pin names. Full walk:
[No IP after a reset or a hardware change](42-problems-network-dns-tls-vpn.md#16-a-server-or-nas-gets-no-ip-after-a-reset-or-a-hardware-change)
and [netplan apply locks you out](42-problems-network-dns-tls-vpn.md#11-netplan-apply-locks-you-out).

**One port, two owners.** Apache held 443 while Dokploy's Traefik needed it. Stopping Apache was a
one-way door for every legacy site; moving it to other ports was two-way (one file, one config
test, one reload, the same steps back: rung 5). The senior refinement: prepare Traefik's routes to
the moved Apache **on the side**, so the switch is one short step, then keep a ports inventory.
Full case: the [Apache vs Dokploy runbook](21-case-apache-443-dokploy.md) and its
[rollback](21-case-apache-443-dokploy.md#10-rollback).

---

## 10. Practise and self-check

**Decision drills** (Labs): the Pi-hole move, Monzo 2019 (adding capacity caused
the outage) and GitHub 2018 (a long degradation chosen over a risky fast path). Every choice names its rung.

1. Name the rung: `kubectl cordon NODE`; `zfs rollback`; restarting the only PostgreSQL; a new DHCP option for the office.
2. What makes restarting a single database safe enough, given it cannot be undone?
3. Two reasons to take a window for a DHCP server move.
4. Rewrite "DB issues, looking into it" with the four facts and a next update time.

More: the [game day](33-learn-cicd-iac-sre.md#8-l4-exit-test-the-game-day).

---

## 11. Sources

Opened in November 2026; summaries in our own words.

- Google SRE book: [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/), [Emergency Response](https://sre.google/sre-book/emergency-response/), [Managing Incidents](https://sre.google/sre-book/managing-incidents/); workbook [Incident Response](https://sre.google/workbook/incident-response/); J. Mace, [Generic mitigations](https://www.oreilly.com/content/generic-mitigations/)
- Docker [live restore](https://docs.docker.com/engine/daemon/live-restore/) and [docs issue 26424](https://github.com/docker/docs/issues/26424) (the Swarm refusal); [netplan try](https://netplan.readthedocs.io/en/stable/netplan-try/); Apache [Stopping and Restarting](https://httpd.apache.org/docs/2.4/stopping.html); Cloudflare [lowering TTLs](https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-2); [RFC 2131](https://www.rfc-editor.org/rfc/rfc2131) §4.4.5
- Pi-hole [Docker configuration](https://docs.pi-hole.net/docker/configuration/), [v5 to v6](https://docs.pi-hole.net/docker/upgrading/v5-v6/), [config reference](https://docs.pi-hole.net/ftldns/configfile/), [FAQ: the only DNS server](https://discourse.pi-hole.net/t/why-should-pi-hole-be-my-only-dns-server/3376), [moving to another machine](https://discourse.pi-hole.net/t/moving-pi-hole-to-another-machine/79548)
- Incidents: [Monzo 2019](https://monzo.com/blog/2019/09/08/why-monzo-wasnt-working-on-july-29th), [GitHub 2018](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/), [Cloudflare 2020](https://blog.cloudflare.com/cloudflare-outage-on-july-17-2020/), [GitLab 2020](https://about.gitlab.com/blog/2020/09/11/gitlab-pg-upgrade/)
