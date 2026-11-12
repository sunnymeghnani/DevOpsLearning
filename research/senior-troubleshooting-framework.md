# Senior troubleshooting framework: the PROTECT loop and the risk ladder

Research note, 10 November 2026. It feeds a new handbook module, a printable card, four decision
drills and a "safest next step" hint for the existing playbooks.

- Nothing here was run on this machine. Every command is an example to study: UPPERCASE words are
  placeholders, names use `example.com`, addresses use `OLD_IP` / `NEW_IP` or the documentation ranges.
- Sources were opened on 10 November 2026 and are listed in section 7 with what each one supports.
  Three could not be opened and are named there; nothing below rests on them.
- Text is in my own words. There is one short quotation, in section 2 (step P).

Contents: 1 opinion on the premise · 2 the PROTECT loop · 3 the risk ladder · 4 pre-change
checklists and messages · 5 worked example: moving a DNS server with no downtime (and a review of
that runbook) · 6 handbook implementation proposals · 7 sources.

---

## 1. An honest opinion on the premise

The premise: "every stack and its application comes with an issue", so learn one way of thinking
that works on any stack, and fix things without downtime while many users depend on the system.

### What is right

1. **One method for every stack is the right investment.** Google's SRE book describes
   troubleshooting as a general loop (report, triage, examine, diagnose, test, cure) that does not
   depend on the product, and the Google/O'Reilly article on generic mitigations lists moves that
   work before you understand the outage: roll back, drain, degrade, add capacity, block, quarantine.
   Tools change every two years; these questions do not.
2. **Protecting users first is the senior instinct.** Every serious source says the same thing:
   stop the harm, then find the cause.
3. **You already work this way.** The Pi-hole migration runbook (section 5) is senior thinking:
   it asks why the first import broke before trying again, it distrusts a dashboard number until it
   knows what the number measures, and it gets zero downtime by running old and new side by side.

### What to adjust

1. **Aim for least harm, not zero downtime.** Harm is roughly users affected × minutes, and it
   gets far worse the moment data is at risk. The order of protection is **data, then service, then
   evidence, then speed**. A short, announced window is often the safer choice:
   - GitLab upgraded the PostgreSQL behind GitLab.com in an announced Sunday window, after seven
     rehearsals in staging, with part of the fleet left on the old version as the way back. They
     accepted about two hours of planned downtime rather than attempt it live.
   - GitHub, in October 2018, chose to stay degraded for over 24 hours rather than fail back
     quickly and lose writes.
   - Google's SRE book says 100% is the wrong target, counts scheduled maintenance separately from
     unplanned downtime in one of its examples, and even takes a too-reliable service down on purpose
     so that nobody builds on a promise that was never made.
2. **Zero downtime is built before the change, not won during it.** It comes from a second copy
   (a replica, a parallel instance, a second port), a rollback that has been tried, and a TTL or
   DHCP lease lowered the day before. On one box with no replica, restarting a stateful service
   **is** downtime. The honest choices are: build a temporary second copy and move users across
   (your Pi-hole runbook), or take a short window and say so.
3. **One way of thinking does not replace knowing the stack.** The loop tells you which question
   comes next. You still need six facts about each tool (section 2, "Six facts"). That list is the
   portable part: it is what to learn first about any new stack.
4. **Low rungs are not automatically safe.** Adding capacity took Monzo down in 2019. A one-line
   change on one router halved Cloudflare's traffic in 2020. Even looking can hurt: the SRE book
   warns that active tests have side effects. The ladder in section 3 says where each rung bites.
5. **The loop has a clock.** A senior also knows when to stop: fifteen minutes per idea, then the
   next idea or more people. Google's rule of thumb is to declare an incident when a second team is
   needed, customers can see it, or an hour of focused work has not solved it.
6. **Not everything is an incident.** The same loop runs a planned change; you only start at a
   different step. That is why the migration runbook fits it so well.

**Verdict:** keep the goal, reword it. "Troubleshoot anything, hurt nobody: the least harm to
users and data, and when a risky step cannot be avoided, a short planned window instead of a live
gamble."

---

## 2. The framework: the PROTECT loop

Seven steps. The name is the priority: protect users, protect data, protect evidence.

| | Step | The question a senior asks | Output |
|---|---|---|---|
| **P** | **Protect** | Who is hurt, is it getting worse, and what is the safest thing that stops the harm now? | harm stopped or contained |
| **R** | **Report** | Who needs to know, who leads, and when is the next update? | first message sent, roles named, timeline started |
| **O** | **Observe** | What do I actually see, from where, and what changed just before? | evidence saved, read-only |
| **T** | **Theorise** | What one explanation fits all the evidence, and what cheap, safe test could prove it wrong? | one hypothesis, one prediction, a timebox |
| **E** | **Evaluate** | What is the lowest rung that would help? Can I undo it? How far can it reach? Now, or in a window? | a chosen rung, a written undo, a go/no-go |
| **C** | **Change** | What is the smallest change, how will I know it worked, and what makes me turn back? | one change, checked, widened or reverted |
| **T** | **Teach** | What would have caught this sooner, and what removes the whole class? | five-line note or postmortem, one prevention |

**How it runs.** P and R belong to the first ten minutes. O → T → E → C is the inner loop: each
pass carries one hypothesis and one change, and a failed pass returns to O with the change
reverted. The final T closes it. Two Ts: **Theorise before you touch, Teach after you finish.** For a **planned change** start at O (know the current state); P
then means "what keeps users served while I work" and R is the announcement.

**Where each step comes from, and where the handbook already teaches it.** The new module should
link to these, not repeat them.

| Step | Practice behind it | Already in the handbook |
|---|---|---|
| P | SRE triage and generic mitigations | `25-playbook-site-down.md` §10 "Stabilise before root cause"; `33-learn-cicd-iac-sre.md` "Step 16 — Mitigate first" |
| R | Incident command: one lead, one pair of hands, one voice | `39-learn-senior-architecture.md` "Incident command"; `52-devops-day-to-day.md` §9; `25` §10 |
| O | Start from recent changes; USE and RED | `23-playbook-slow-system.md` §1; `25` §1 (bypass ladder, failure signatures); `39` "Troubleshooting at system level" |
| T | Hypothesis, prediction, test; timeboxing | `33` "Effective troubleshooting method" (Agans' rules) |
| E | One-way and two-way doors, blast radius | `39` "Change management and CAB-lite" (risk score), "Failure domains and blast radius" |
| C | Canary, rolling, blue-green, drain | `33` §3 "Deployment strategies"; `35-deployment-patterns.md` P12; `52` §10 |
| T | Blameless postmortem, contributing factors | `33` "Blameless postmortems"; `39` "Contributing factors", "Eliminating classes of incidents" |

What is **new** here: the single named loop, the risk ladder with its single-box column, the
"window or live fix" rule, and the six facts.

### Six facts to learn about any stack

Before you operate a tool you have never run, find these six things. They are the per-stack part
of the method, and the tables under each step below are these facts filled in.

1. **State:** where does it keep data and config, and how is that backed up and restored?
2. **Look:** how do I see status, logs and the live config without changing anything?
3. **Validate:** how do I test a change before applying it (config test, dry run, diff)?
4. **Apply:** does a change need a reload or a restart, and who feels it?
5. **Undo:** what is the rollback (previous version, saved file, snapshot), and how long does it take?
6. **Reach:** what does it depend on, and what depends on it?

---

### P — Protect (users, data, evidence)

**Question:** who is hurt right now, is it getting worse, and what is the safest thing that stops
the harm?

> "Stopping the bleeding should be your first priority." (Google SRE book, Effective Troubleshooting)

| Do | Do not |
|---|---|
| Spend two minutes sizing up: who, what, since when, spreading or stable | Start root-causing while users are down |
| Pick a mitigation from rungs 1–4 of the ladder: roll back the last change, shift or drain traffic, shed load, switch a feature off, show a maintenance page for the broken part | Restart things "to see if it helps" |
| If data may be getting damaged, stop writes. Freezing is protection too | Mitigate with something you cannot undo |
| Take 60 seconds to save logs and state before a mitigation that destroys them | Change two things at once |

**Low-downtime techniques:** rollback, drain and cordon, failover of a virtual IP, scale out,
rate-limit or block one abusive client, feature flag or kill switch, read-only mode, maintenance
page for one host, switching a route or DNS record back to the known-good target.

| Stack | Protecting moves |
|---|---|
| Linux host | Stop the one runaway unit, not the server. Empty a runaway log in place instead of deleting a file a process still holds open |
| Docker / Swarm | `docker service rollback SERVICE`; `docker service scale SERVICE=N`; `docker node update --availability drain NODE` |
| Kubernetes | `kubectl rollout undo deployment/NAME`; `kubectl cordon NODE`; scale up; take one bad pod out of the Service |
| Reverse proxy | Point the route back at the old upstream; remove one bad backend from the pool; maintenance page for one hostname |
| Database | Stop the one writer or query doing damage; go read-only if data is at risk; fail over only if it has been rehearsed |
| Network / DNS | Put the old record or address back; keep the old resolver answering |
| Storage / NAS | Stop the consumers (apps, VMs) before touching storage; never "repair" a pool to make a warning go away |

**From your cases (Pi-hole):** the migration protects users by design. The old Pi-hole keeps
answering for the whole move, so no step can leave the network without DNS.

---

### R — Report (declare, name roles, first update)

**Question:** who needs to know, who is leading, and when is the next update?

| Do | Do not |
|---|---|
| Say it in the channel within ten minutes: what is affected in user words, since when, what you are doing, next update time | Go silent and type |
| Name one person who decides and one who changes production. Alone? Ask someone to take the updates | Let several people change production at once |
| Start a timeline: time, what you saw, what you changed | Announce a cause you have not proved |
| Declare early: second team needed, users can see it, or an hour without progress | Promise a fix time you cannot keep |
| For a planned change: announce the window and any freeze | Surprise people with a change they could have planned around |

**Low-downtime techniques:** a pinned incident note, `script` to record the terminal, a change
freeze, a default first message written in advance.

| Stack | What "affected" means in user words |
|---|---|
| Linux host | Which sites and jobs live on that server |
| Docker / Swarm | Which services and stacks, on which node |
| Kubernetes | Which app or namespace; one node or the whole cluster |
| Reverse proxy | Which hostnames. Every site behind it shares its fate |
| Database | Which apps write to it; say plainly whether data is at risk |
| Network / DNS | "Names do not resolve for the office." DNS can take your chat and login tools with it, so agree an out-of-band channel first |
| Storage / NAS | Which shares, VM disks and backup jobs; tell the backup owners |

**From your cases (Pi-hole):** the runbook announces a **record-change freeze** for the window.
That is this step in a planned change: with two resolvers live, an edit made on one of them would
give clients two different answers.

---

### O — Observe (read-only first)

**Question:** what do I actually see, from where, and what changed just before?

| Do | Do not |
|---|---|
| Reproduce it with one command you can repeat | Change anything "to see what happens" |
| Read the shape: who and what is **not** affected | Debug the loudest host while the shared cause continues |
| Ask what changed: deploys, config, packages, certificates, dates, hardware someone touched | Trust a number before you know what it measures |
| Resources: utilisation, saturation, errors (USE), errors first. Services: rate, errors, duration (RED) | Run heavy diagnostics on a box that is already struggling |
| Save every output you look at | Rely on memory for the timeline |

**Low-downtime techniques:** all of this is rung 1. The bypass ladder in `25` §1, comparing a
broken member with a healthy one, and testing each pool member directly.

| Stack | Read-only looks |
|---|---|
| Linux host | `uptime`, `journalctl -p err --since "1 hour ago"`, `df -h` and `df -i`, `ss -ltnp`, `ip -br addr`, `systemctl --failed` |
| Docker / Swarm | `docker ps -a`, `docker service ps --no-trunc SERVICE`, `docker logs --since 15m CONTAINER`, `docker events --since 30m` |
| Kubernetes | `kubectl get events --sort-by=.lastTimestamp`, `kubectl describe pod POD`, `kubectl logs --previous POD`, `kubectl rollout history deployment/NAME` |
| Reverse proxy | The log line for one request; `curl -v --resolve`; `nginx -T`; `apachectl -S`; Traefik's dashboard and log |
| Database | Sessions and locks (`pg_stat_activity`), connections against the limit, replication lag, the error log |
| Network / DNS | `dig @SERVER NAME`, `dig +trace NAME`, `ip route get ADDRESS`, `resolvectl status`, a filtered and counted capture: `tcpdump -ni IFACE -c 50 port 53` |
| Storage / NAS | `zpool status -x`, `zfs list -o space`, SMART data, the kernel log, the alerts page |

**From your cases (TrueNAS with no IP after a network adapter was re-seated):** the first move is
at the console and read-only: list the interfaces and compare the name the system now sees with the
name the saved configuration expects. Nothing is changed until those two names are side by side.
**(Pi-hole):** "Load 7, 35% memory" on the dashboard belonged to the host, not to Pi-hole: a
container reads the kernel's host-wide figures.

---

### T — Theorise and test

**Question:** what one explanation fits **all** the evidence, what else would be true if it were
right, and what is the cheapest safe test that could prove it wrong?

| Do | Do not |
|---|---|
| Write one hypothesis and its prediction: "if X, then Y must also be true" | Treat things that happened together as cause and effect |
| Run the cheapest read-only test first; think horses before zebras | Keep the first story because it was first |
| Timebox: 15 minutes, then the next idea or more people | Test with a change you cannot undo |
| Cut the path in half and test the middle | Test two ideas with one change |
| Keep the ideas you ruled out; they save the next person an hour | Throw away a negative result |

**Low-downtime techniques:** a scratch copy with no users on it, a debug container on the same
network, a clone of a snapshot, a replica.

| Stack | Safe ways to test an idea |
|---|---|
| Linux host | Reproduce and time one command; validate a copy of the config (`sshd -t`, `visudo -c`, `systemd-analyze verify UNIT`) |
| Docker / Swarm | Run the same image beside the real one with no published ports; a throwaway container on the same network; curl each task directly |
| Kubernetes | `kubectl debug`, `kubectl port-forward` to one pod, `kubectl auth can-i`, `kubectl diff` against the live object |
| Reverse proxy | Ask the upstream directly, then through the proxy; `--resolve` against each edge in turn |
| Database | `EXPLAIN` before running; try it on a replica or a restored copy |
| Network / DNS | Ask the old and the new server the same name and compare; test from the client's own network |
| Storage / NAS | Clone a snapshot and test on the clone; import read-only on a test machine |

**From your cases (Pi-hole "overload"):** the first story was "too many users". The better
hypothesis predicts something checkable: if clients are being rate-limited, the FTL log has
rate-limit lines and those clients get REFUSED; if shared memory is exhausted, `/dev/shm` is near
100%. Both are read-only checks, and both point away from user count.

---

### E — Evaluate the risk (pick the rung, prepare the way back)

**Question:** what is the lowest rung on the ladder that would fix or prove this? Can I undo it,
and how fast? What is the widest thing it can touch? Is now the right time?

| Do | Do not |
|---|---|
| Ask the three questions: undo? reach? state or data involved? | Fix forward under pressure when a rollback exists |
| Write the undo command **before** the change | Call a change "small" because you typed it on one node |
| Snapshot or back up, and know that it restores | Assume a rollback works because it exists |
| Validate or dry-run with the tool's own check | Skip the window out of pride |
| Decide: live, or a short announced window (rule in section 3) | Start a network change without console access |
| For rung 6 and above, say the plan and ask for strong objections | Seek everyone's agreement while users wait |

**Low-downtime techniques:** prefer two-way doors; shrink the reach (one host, one route, one
client); snapshot first; prepare the fix on the side and switch over; lower TTL or lease ahead.

| Stack | Validate before | Undo after |
|---|---|---|
| Linux host | `sshd -t`, `visudo -c`, `systemd-analyze verify`, `netplan try` (reverts by itself unless confirmed) | a `cp -a` copy of the file, config in Git, a VM snapshot |
| Docker / Swarm | `docker compose config`; an exact image tag | `docker service rollback`; the previous tag, kept on the host |
| Kubernetes | `kubectl diff -f FILE`, `kubectl apply --dry-run=server -f FILE` | `kubectl rollout undo`; revert in Git |
| Reverse proxy | `nginx -t`, `apachectl configtest`; Traefik's file provider documents no validate command, so test the route on a spare hostname with `curl --resolve` | the previous file plus a reload |
| Database | Run the migration on a restored copy; make it backward compatible | restore or point-in-time recovery. Data changes are one-way doors |
| Network / DNS | Lower the TTL or lease at least one old TTL ahead; keep the old answer alive | put the record back; it takes effect within the lowered TTL |
| Storage / NAS | `zfs snapshot POOL/DATASET@before-CHANGE`; export the system config | `zfs rollback` discards everything written since, so prefer a clone when unsure |

**From your cases (Apache holding 443 while Dokploy's Traefik needed it):** stopping Apache was a
door that swung one way for every legacy site. Moving Apache to other ports was a two-way door:
one file, one config test, one reload, and the same steps backwards. The senior refinement is to
prepare the Traefik routes to the moved Apache **on the side** first, so the switch is one short
step instead of a gap. **(Pi-hole):** a full import onto a different machine had already failed
once; running both in parallel made every later step reversible.

---

### C — Change one small thing, check, then continue or revert

**Question:** what is the smallest change that tests my fix, how will I know within N minutes that
it worked, and what makes me turn back?

| Do | Do not |
|---|---|
| Say "doing X now", make **one** change, note the time | Change everywhere at once |
| Start with one node, one route, one stack or one client | Stack a second fix on a first that did not work |
| Prefer a reload to a restart | Declare victory because it "looks fine" |
| Watch the same probe that showed the problem, for a set time | Leave an emergency edit out of Git |
| No improvement: revert at once, back to O | Walk away during the watch window |

**Low-downtime techniques:** canary, rolling update with the new copy started first, drain then
change then return, blue-green switch, a feature flag for a share of users, graceful reload.

| Stack | Applying gently |
|---|---|
| Linux host | `systemctl reload UNIT` where the service supports it; one host first |
| Docker / Swarm | `docker service update --update-parallelism 1 --update-delay 30s --update-order start-first --update-failure-action rollback SERVICE`; Compose stacks one at a time |
| Kubernetes | Rolling update with readiness probes; `kubectl rollout status`; node work as cordon, drain, change, uncordon, one node at a time |
| Reverse proxy | `nginx -s reload` keeps the old config if the new one is invalid and lets old workers finish; `apachectl graceful`; one route or vhost first |
| Database | One replica first, then switch over; schema changes in small compatible steps |
| Network / DNS | One client or one subnet, then DHCP for everyone, the old address last |
| Storage / NAS | One dataset or share first; one disk at a time, and never a second while a resilver runs |

**From your cases (Pi-hole):** the runbook compares old and new answers name by name before any
client moves, then recreates Docker stacks one at a time. **(TrueNAS):** the supported way to
change an interface has a timed test built in: the change reverts by itself unless you confirm it
from a working session.

---

### T — Teach (learn and prevent)

**Question:** what would have caught this sooner or made it a non-event, and what one change
removes the whole class?

| Do | Do not |
|---|---|
| Write the five-line note every time: symptom, first wrong guess, deciding evidence, fix, check first next time | Blame anyone, yourself included |
| For a real outage, a blameless postmortem listing contributing factors | Stop at the first cause |
| Put emergency changes back into Git; fix the runbook that was wrong | Write "be more careful" as an action |
| Add the probe or alert that would have told you first | File twenty actions that nobody owns |
| Pick one prevention with an owner and a date | Keep the lesson in your head |

**Low-downtime techniques for next time:** add the replica or the second resolver, a health check,
a canary in the pipeline, a rollback that is exercised, a restore drill, a game day.

| Stack | Removing the class |
|---|---|
| Linux host | Pin interface names by MAC address; `nofail` on mounts the boot can live without; config in Git |
| Docker / Swarm | Health checks with start-first updates; log rotation; exact image tags |
| Kubernetes | PodDisruptionBudgets, probes, resource requests; an alert on certificate expiry |
| Reverse proxy | Config test in CI; a probe per backend, not only through the front door |
| Database | Restores that are tested on a schedule; a replica; connection limits |
| Network / DNS | A second resolver; settings pinned so an import cannot change them; an inventory of who owns ports 53, 80 and 443 |
| Storage / NAS | Scheduled snapshots and replication; a bridge in front of the NIC so apps do not care about its name |

**From your cases:** each one ends in a class fix. Apache and Traefik: a ports inventory, so a
clash is found before an install. TrueNAS: a name that survives hardware changes. Pi-hole: a second
resolver, so DNS stops being the single point of failure for everything, including image pulls.

---

## 3. The risk ladder

Climb only when the rung below cannot help. Three questions before stepping up:

1. Have I used the rungs below?
2. Can I undo this in under five minutes, and is the undo written down?
3. What is the widest thing this can touch, and is state or data involved?

If one answer is missing, you are not ready for that rung.

| # | Action | Make it reversible | Limit the blast radius | Only one box, no replica | Who decides |
|---|---|---|---|---|---|
| 1 | **Read-only look:** logs, status, queries, a filtered capture | Nothing to undo. Save what you see | Keep it light: filtered and counted captures, no tracing of a hot process, no debug logging, no disk-wide scans on a dying disk | The same, and copy evidence off the box early if the box itself may be failing | Anyone |
| 2 | **Add capacity or shift traffic:** scale out, drain a node, move a VIP, block one client, shed load | Note the old values; scale back, uncordon, unblock | Shift a slice first; check the target has room. **On a stateful cluster, adding a member is a data change: treat it as rung 7** | Nowhere to shift, so shed instead: pause backups and cron, rate-limit, cache or park the heaviest page, raise the one limit that is exhausted. Or build a temporary second instance and move clients to it (section 5) | Any responder; tell the lead |
| 3 | **Restart one replica:** one pod, one task, one worker | Not undoable, but the pool heals it. Save its logs and state first | One of N; confirm the others are healthy and can carry N−1; wait for healthy before the next | **With no replica this is an outage** lasting the service's start time. Reload instead if the service can. Otherwise: validate the config first so it comes back, know the start time, pick a quiet minute, announce it. Swarm on one node can still start the new task before stopping the old | Any responder; tell the lead |
| 4 | **Roll back:** previous image, previous config, `git revert` | Keep the new version so you can roll forward again | Roll back only what changed. **Stop if the data format, schema or protocol changed:** then rollback is rung 8 | Keep the previous image and config **on the box** (the registry may live on the same box). A snapshot from before the change is the rollback for an in-place upgrade | Any responder; tell the lead |
| 5 | **Change config on one node:** one vhost, one route, one host's network, one firewall rule | Copy the old file; write the undo; use the tool's validate and its timed revert where it has one | Take the node out of rotation first; one route or host. **Confirm the setting really is local:** routing policy, cluster objects and shared storage are not | "One node" is everything, so shrink by object: one vhost, one hostname, one container, one client. Keep a console or out-of-band session open. Reload, do not restart | The person at the keyboard plus a second pair of eyes |
| 6 | **Change everywhere:** a fleet-wide run, a daemon or proxy setting, a cluster upgrade, a DHCP option for the whole network | A staged rollout that stops by itself; the revert commit ready | Canary, then one, then half, then all, with a watch time between; one canary at a time; not late on a Friday | You cannot stage by node, so stage by **preparation**: build the new thing beside the old (second port, second container, scratch instance), validate it there, switch over. Daemon, kernel and proxy restarts blip everything: short window, snapshot first | Lead plus reviewer; a change record |
| 7 | **Restart a stateful service:** database, DNS or DHCP server, quorum member, storage, the Docker daemon on a Swarm manager | A restart cannot be undone. Make it safe: a backup you have restored once, a clean shutdown, replication and quorum checked before | One member at a time, wait for resync; stop or park the consumers first; never combine with an upgrade | **A planned window is the honest answer**, or the parallel-run pattern: second instance, both live, clients moved gradually, old one retired last. Lower TTL and lease the day before | The lead, with the service owner |
| 8 | **Data repair:** restore, manual SQL, filesystem or pool repair, replaying events, a failover that drops writes | Usually a one-way door, so **manufacture** the way back: snapshot or copy first, work on the copy, keep the damaged original untouched until the result is verified | Stop writes so the damage stops growing; repair the smallest unit (one table, one dataset); two people; every statement written in a file first | The box holds the only copy: copy it **off** the box before anything else. Restore to the side (new name, second disk) and switch. Accept a longer window | The lead, explicitly and recorded, with the data owner |

**Authority in one line:** rungs 1–4 are two-way doors any responder may use during an incident.
Rungs 5–6 need a second pair of eyes and a written undo. Rungs 7–8 need the lead and normally a
window. If the service is already fully down there is no uptime left to protect, so rung 7 gets
cheaper; rung 8 never does. (This extends the "who decides" table under "Incident command" in `39`.)

### Where each rung bites (public incidents)

| Rung | What went wrong | Lesson |
|---|---|---|
| 1 | The SRE book: a test can change what later tests show (more load, more logging) | Measure lightly; put back anything you changed in order to look |
| 2 | Monzo, 2019: six nodes added to a database cluster to gain capacity began answering for data they did not hold | Capacity for stateful systems is a data change. The undo was done one node at a time |
| 4 | Google's emergency-response chapter: a rollback that had never been tested failed during the incident. AWS: the usual reason a rollback is impossible is a changed protocol or format | Try the rollback before you need it; deploy format changes in two phases (read new first, write new later) |
| 5 | Cloudflare, 2020: one line on one router's policy pulled a large share of backbone traffic to that site for 27 minutes | "One node" is not the reach. Ask what the setting talks to |
| 6 | Google's emergency-response chapter: a global config push judged low-risk got a weaker canary and crash-looped everything | The canary matters most when the change looks harmless |
| 7–8 | GitHub, 2018: a 43-second network break caused an automatic database failover; each side then held writes the other lacked | They chose data over speed and stayed degraded for a day. Automatic failover of state needs fences |

### Window or live fix?

Choose a short, announced window when **any** of these is true:

- the step is rung 7 or 8 on a single instance;
- it is a one-way door: a major-version upgrade, a schema or data-format change, a DHCP server handover;
- the rollback is untested, or takes longer than the window would;
- the live path needs two changes at once;
- a mistake would cut your own access (the only network link, the only DNS, the only login path).

Make the window short with preparation, not speed:

1. Rehearse on a copy. GitLab rehearsed their database upgrade seven times.
2. Prepare everything on the side, so the window holds only the switch.
3. Lower the DNS TTL or DHCP lease ahead. Cloudflare's guidance is 24–48 hours ahead, or at
   least as long as the longest current TTL. DHCP clients renew at half the lease, so lower a
   lease at least half an **old** lease ahead (a full one is safer).
4. Snapshot or back up immediately before; write the undo with its trigger and its duration.
5. A go/no-go check at the start; a stop time after which you roll back instead of pushing on.
6. Leave part of the old world untouched as the way back. GitLab kept nodes on the old version.

A live fix is right when the action is rungs 1–4, or a rung 5–6 that has been shrunk to one
object, validated, and can be undone in minutes.

---

## 4. Pre-change checklists and messages

`52-devops-day-to-day.md` §10 has the seven-question change checklist and `33` has the full change
request. This is the short form for the moment before you press Enter, plus the per-tool facts.

### The ten-line check (rung 5 and above)

1. One sentence: what changes, and why.
2. Snapshot or backup taken now, and I know it restores.
3. The undo command is written in the ticket or channel, with how long it takes.
4. The change is validated with the tool's own check (table below).
5. Console or out-of-band access is open, if this touches network, SSH, DNS or the firewall.
6. One canary first: one node, route, stack or client.
7. The watch: which probe or graph, for how many minutes.
8. The stop condition: "if X by HH:MM, I roll back".
9. People know: what, when, how long, what they will notice, how we go back.
10. One change. Anything else waits for the next pass.

### Validate, apply gently, undo: per tool

| Tool | Validate first | Apply gently | Undo | Limits to know |
|---|---|---|---|---|
| Nginx | `nginx -t` (syntax, and it opens referenced files) | `nginx -s reload` or `systemctl reload nginx` | previous file, reload | A reload with a bad config keeps the old one running; a restart with a bad config does not come back |
| Apache | `apachectl configtest` | `apachectl graceful` or `systemctl reload apache2` | previous file, graceful | Apache's docs say a passing syntax check does not guarantee a clean restart |
| Traefik | No validate command is documented for the file provider | The dynamic file is watched: **saving is deploying** | previous file | Edit a copy, test the route on a spare hostname, watch the log. Mount the directory, not the single file. Static config needs a restart: rung 6 on a single edge |
| Netplan | `netplan try` | confirm within the timeout (120 s by default) | automatic if you do not confirm | The docs say to check that the revert really happened; some virtual devices do not revert cleanly. Console first |
| Docker Compose | `docker compose config` | one stack at a time | previous file and tag | Per-container settings need the container recreated |
| Swarm service | review the planned update flags | `--update-parallelism 1 --update-delay … --update-failure-action rollback` | `docker service rollback SERVICE` | Rollback returns to the previous spec only |
| Docker daemon | check which `daemon.json` keys reload | `systemctl reload docker` for the reloadable keys | previous `daemon.json` | Most keys, `dns` included, need a daemon restart. `live-restore` covers standalone containers only, not Swarm services |
| Kubernetes objects | `kubectl diff -f FILE`; `--dry-run=server` | rolling update; `kubectl rollout status` | `kubectl rollout undo` | `diff` exits 1 when there is a difference, which is not an error |
| Kubernetes node | check PodDisruptionBudgets | `kubectl drain NODE --ignore-daemonsets`, one node at a time | `kubectl uncordon NODE` | Bare pods and local data need explicit flags: read what will be evicted |
| Terraform | `terraform plan -out=tfplan`; read it | `terraform apply tfplan` | revert the code, plan again | Plan files can hold secrets in clear text; `-target` is for exceptions |
| Ansible | `--check --diff --limit CANARY_HOST` | `serial: 1`, then wider | revert the commit, re-run | Check mode cannot predict every task |
| Database | the migration on a restored copy | expand, migrate, contract | restore or point-in-time recovery | Not undoable once new data is written |
| ZFS / NAS | `zfs snapshot POOL/DATASET@before-CHANGE`; config export | one dataset or share first | `zfs rollback`, or better a clone | Rollback discards everything since, and `-r` destroys later snapshots |
| TrueNAS network | the UI's timed test | save only from a working session | reverts by itself when the timer ends | Seen only through search summaries of the vendor docs (the page refused the fetcher): check your version's docs |
| Proxmox network | changes are staged before they apply | Apply Configuration, or `ifreload -a` after a manual edit | previous `/etc/network/interfaces` | Interface names can change with kernel or hardware changes: pin them |
| DNS record | lower the TTL ahead | change one record | put it back | Takes effect only as fast as the **old** TTL allowed |

### Messages

The handbook already has incident updates (`25` §10, `52` §9) and a planned-maintenance notice
(`39` "Stakeholder communication"). Three short forms are missing; all follow the same four facts:
**what is affected, when, what you will notice, how we go back.**

**1. Planned change with a freeze (parallel run).**

```text
[PLANNED] DNS server move, Tue 14:00 to Thu 14:00 UTC. No interruption is expected.
What changes:  a new DNS server runs beside the old one; devices move to it by themselves.
Freeze:        no DNS record changes in this period. Need one urgently? Ask TEAM, we apply it to both.
You notice:    nothing. If names stop resolving, tell CHANNEL or call PHONE.
Way back:      devices are pointed at the old server again; complete within one hour.
Short window:  Thu 13:30 to 14:00 UTC, the old address is retired; a few seconds of delay are possible.
```

**2. A risky step during an incident (rung 6 and above).** Say it, then pause for objections.

```text
[DECISION 10:42 UTC] Next step: restart the database on db01 (single instance).
Why:        connections are exhausted; lower steps (kill idle sessions, raise the limit) did not hold.
Impact:     all apps lose the database for about 90 seconds.
Prepared:   backup from 10:30 verified; config validated; console open.
Turn back:  if it is not accepting connections by 10:47, we restore the 10:30 config and restart again.
Strong objections? Proceeding at 10:45.     Lead: NAME   Keyboard: NAME
```

**3. Done, or rolled back.**

```text
[DONE 14:05 UTC] DNS move complete. The old address was retired at 13:42; the new server has
answered every query since 13:43. The record freeze is lifted. Short write-up by Friday.
```

```text
[ROLLED BACK 13:50 UTC] We returned to the old DNS server at 13:47 after lookups from the
Docker hosts were refused. Nothing is degraded now. We will announce a new date once we know why.
```

Rules that hold for all of them: user words, not component names; times with a zone; always the
next update time; no cause until it is proved; no fix time you cannot keep.

---

## 5. Worked example: moving a DNS server with no downtime

The source is your own Pi-hole migration runbook (`research/user-cases/pihole-migration-runbook.md`),
used with `OLD_IP` / `NEW_IP` only. It is the best single-box, stateful-service case in the
project, because DNS is the service everything else depends on and there was no replica.

### The runbook on the PROTECT loop

| Step | Where the runbook does it |
|---|---|
| **P** Protect | The old Pi-hole answers for the whole move (parallel run). Everything is backed up first. Only one DHCP server at any time |
| **R** Report | A record-change freeze for the window |
| **O** Observe | Pre-flight: version, who serves DHCP, what else runs on the host. The settings loop that prints the risky keys. Records extracted to plain files. Reading the dashboard correctly: load and memory are the host's |
| **T** Theorise | Two stories replaced by tested ones. "The import broke the box" became "the import carried machine-specific settings". "Too many users" became "shared memory or per-client rate limiting" |
| **E** Evaluate | A parallel run chosen over a second in-place import. Settings pinned by environment variable. An exact image tag. A scratch container for the version conversion. The lease lowered a day ahead |
| **C** Change | Old and new answers compared name by name before any client moves. Then DHCP, static hosts, Docker stacks one at a time, stragglers, the old address, and DHCP itself last |
| **T** Teach | A second resolver as the end state; a weekly export kept off the box |

### The runbook on the risk ladder

| Runbook action | Rung | Why it is safe |
|---|---|---|
| Backups, `docker inspect`, the settings loop, `dig` comparisons | 1 | Read-only |
| Build the new Pi-hole beside the old; DHCP hands out both | 2 | Adds a copy. This is how a single box gets a "replica" for the length of the move |
| Recreate Docker stacks one at a time | 3 | One stack; the old resolver is still listed |
| If the new one misbehaves: DHCP back to the old address only | 4 | A rollback bounded by the one-hour lease |
| Static hosts' resolver settings, host by host | 5 | One host; `netplan try` |
| Daemon-wide DNS in `daemon.json` plus a Docker restart | 6 | Every container on that host shares the daemon |
| Retiring the old address; handing over DHCP | 7 | A stateful single service: short window, order fixed, old side kept ready |
| Import the data, not the configuration; leave the query database behind | avoids 8 | Data moves as plain files that can be compared; the old box stays the untouched original |

The pattern to carry to other stacks: **when there is no replica, make one for the duration of the
move.** Old and new both live, clients moved by something with a short timer (lease, TTL, a proxy
route), stragglers found from the old side's log, the old address retired last.

### Review of the runbook

**Excellent:**

- **"Import data, not config."** It names the class: settings that describe the machine (interface,
  listening mode, DHCP, web port, reply address) must not travel to a different machine. Pinning
  them by environment variable is supported by Pi-hole's Docker docs, which say such settings
  become read-only.
- **It checks what the number measures** before believing "overload", and it replaces the story
  with two checkable causes. Pi-hole's config reference confirms the default limit of 1000 queries
  per 60 seconds per client and that limited queries are answered REFUSED. A forum thread confirms
  FTL failing on Docker's default 64 MB shared memory and working after `shm_size` was raised.
- **Parallel run, freeze, stragglers from the query log, old address last, DHCP last.** A Pi-hole
  team member gave the same advice to another user in April 2025: keep both running during the
  cutover, never two DHCP servers, and re-enable DHCP on the old one as the way back.
- **Records are applied with `pihole-FTL --config`, not by trusting the import.** That matches a
  change reported in October 2026: FTL 6.7.1 no longer applies `misc.dnsmasq_lines` from a
  Teleporter archive, for security reasons.
- **"v6 ignores `/etc/dnsmasq.d` by default"** is confirmed by Pi-hole's v5-to-v6 Docker page and
  by the v6 release-fixes post. So is "the last v5 image was 2024.07.0".
- **Validation before any client moves, an exact image tag, the query database left behind.**

**Adjust or double-check:**

| # | Point in the runbook | Finding | Suggested change |
|---|---|---|---|
| 1 | §4: enable `live-restore`, then restart Docker | **Check this first.** Docker's docs say live restore covers standalone containers only, not Swarm services, and the handbook (`30` §12, `26`) records that the daemon rejects the option in Swarm mode. A Dokploy host is a Swarm node | On Swarm or Dokploy hosts do not add it. Change DNS per service (`docker service update --dns-add NEW_IP SERVICE`, which rolls task by task), or treat the daemon restart as a rung 6–7 step in a window |
| 2 | §4: reload dockerd with `kill -HUP` | **Correct.** The docs say a reload is enough to turn on live restore (`systemctl reload docker`, or SIGHUP), and `live-restore` is on the list of reloadable keys. `dns` is not on that list, so it does need the restart | Prefer `systemctl reload docker`. Confirm with `docker info` that live restore is on **before** the restart. Keep the two edits as two steps, as the runbook does |
| 3 | §4: the restart with a changed `dns` | The docs warn that live restore may fail when daemon options have changed between runs; they name bridge addresses and the storage driver, not DNS. It is also only supported across patch releases | Try it once on a host that does not matter. Keep the restart short |
| 4 | §4: "DNS is fixed at container creation" | **Not confirmed either way.** Docker's networking page does not say when the resolver file is written. A per-container `dns:` value is part of the container's definition, so that case does need a recreate. For daemon-level and host-level changes my understanding is that the file is rebuilt at each container start, so a restart may be enough; I could not verify this in the docs | Test on one container: restart it, read its `/etc/resolv.conf`. Recreating is the safe superset. The property the plan relies on is true regardless: a **running** container does not change |
| 5 | §3: DHCP hands out `NEW_IP, OLD_IP` | Order is not priority. Pi-hole's own FAQ says clients may use either listed server at any time. On Docker's user-defined networks the embedded DNS does try upstreams in order; on the default bridge it depends on the container's resolver | The freeze is therefore essential, not optional. Add a phase: DHCP hands out `NEW_IP` only (or new plus the second resolver), wait one lease, **then** read the old box's log as "stragglers". Until then every client still uses the old one sometimes |
| 6 | §0: lower the lease to 1 h "the day before" | Clients renew at half the lease (RFC 2131), and they only learn the shorter lease at that renewal | A day ahead works if the old lease was two days or less. With a seven-day lease, lower it four days ahead. Sleeping devices arrive later; the straggler step covers them |
| 7 | §3 Option A: stop the old container, add `OLD_IP` on the new host | Stopping the container frees port 53, not the address. If `OLD_IP` is the old **host's** own address, adding it elsewhere makes a duplicate address. `ip addr add` is also lost at reboot, and `eth0` is a placeholder | First remove or change the address on the old host, from its console, not over a session that uses that address. Make the extra address permanent with `netplan try`. Use the real interface name. Write the undo (remove on new, restore on old) |
| 8 | §2.2: `listeningMode: all` | Pi-hole's docs warn that this mode can make the server an open resolver and say to firewall it and to consider the other modes first | Keep it only if clients arrive from routed networks or Docker bridges, and confirm port 53 cannot be reached from outside. If every client is on a directly attached subnet, the default local mode is enough |
| 9 | §5: rate limit raised to 6000 | It hides the noisy client as well as relieving it | Keep the raise, and give the "fix the noisy client" line an owner and a date |
| 10 | Whole runbook | The rollback is implied by the design, not written | Per phase: the trigger, the action, the time. For example: "REFUSED or SERVFAIL from the new server for five minutes → DHCP back to the old address only → everyone back within about an hour" |
| 11 | §3 phase 7: DHCP handover | The one step that is nearly a one-way door | Export the static leases first. Order: off on the old, then on on the new. A few seconds with no DHCP server hurts nobody; an overlap does. Announce the window |
| 12 | §0 and §2.3: v5 to v6 on top of a move | Two changes at once | The scratch-container conversion is the right idea (prepare on the side). Spell out its middle steps: the snippet starts the container and then removes it |
| 13 | §2.3: untick Configuration and DHCP leases | I could not open an official page showing those import options (the tutorial in the Sources list refused the fetcher) | Look at the import screen on the scratch container first |
| 14 | Not in the runbook | Devices that never ask DHCP: IPv6 router advertisements, servers and hypervisors with fixed resolvers, VPN configs, the router's own forwarder | List them before the move; the straggler query confirms the list |
| 15 | §1: the backup folder | It holds the password hash, `.env` and client data | Restrict it and delete it after the move |
| 16 | §4: Kubernetes | Fine as written. CoreDNS forwards to the node's resolver file, which kubeadm points at `/run/systemd/resolve/resolv.conf` on hosts using systemd-resolved; glibc reads at most three nameservers | Change the node with `netplan try`, read that file, then do the rolling restart of CoreDNS |

Not verified: the tutorial and the GitHub repository in the runbook's Sources list were not opened.

---

## 6. Proposals for the handbook

The page is 15,720,556 bytes against a budget of 15,950,000, so about **229 KB** is free. The plan
below should cost roughly 90–100 KB and leave over half of the headroom.

| Piece | Rough cost in the page |
|---|---|
| New module (about 26 KB of Markdown) | 40 KB |
| Four drills at about 9 KB | 36 KB |
| About 30 "safest next step" hints | 8–10 KB |
| Card styles and print rule; optional rung picker | 2–5 KB |

### 6.1 New module

- **File and sidebar:** `57-method-protect-risk-ladder.md`, title "Method: PROTECT & the Risk
  Ladder", a ladder icon, **first** in the group "Real incidents & playbooks". The playbooks are
  the stack-specific walks; this page is the method they share.
- **Home page:** one launchpad card, "Something is broken and people are waiting: start here".
- **Course map:** no new topic. The handbook says "123 topics" in many places, so attach the module
  as a study item to four existing topics: `outage-basics` (L2), `deployment-strategies` (L3),
  `change-management` (L4) and `incident-command` (L4).
- **Size target:** 28 KB of Markdown at most. To get there, the seven per-step stack tables above
  collapse into **one** matrix (seven stacks × the six facts), and each step keeps only its
  question, its do / do-not pair and one example.

Outline:

| § | Section | Content | Links out instead of repeating |
|---|---|---|---|
| 0 | How to use | The 30-second version is the card; who reads what by level | `34-roadmap.md` study method |
| 1 | Least harm, not zero downtime | Section 1 above in ten lines | `39` "SLO negotiation", "Availability maths" |
| 2 | PROTECT on one screen | The seven-row table; how the loop runs for an incident and for a planned change | `33` "Effective troubleshooting method" |
| 3 | The seven steps | Question, do / do not, one example each | `25` §1 and §10, `23` §1, `39` "Incident command", "Troubleshooting at system level" |
| 4 | Six facts for any stack | The 7 × 6 matrix | command-reference modules; Command Decoder |
| 5 | The risk ladder | The eight-rung table with the single-box column; "where each rung bites" | `39` "Change management and CAB-lite", "Failure domains and blast radius" |
| 6 | Window or live fix? | The rule and the six ways to shorten a window | `21` §9 "Cutover with minimal downtime", `35` P12, `33` "Example CR" |
| 7 | Before you press Enter | The ten-line check and the per-tool table | `52` §10 "The change checklist" |
| 8 | Messages | The three new templates | `25` §10, `52` §9, `39` "Stakeholder communication" |
| 9 | Case: move a DNS server with no downtime | Section 5, anonymised, with the two mapping tables and the checks worth making | `42` §7.4, `30` §12, `28` (DHCP and DNS) |
| 10 | Practise, self-check, next | The four drills; five self-check questions; lab rooms | drills page, labs, `54-practice-arena.md` |

Self-check questions for §10: name the rung of five given actions; say what makes a restart of a
single database reversible; give two reasons to prefer a window; state the six facts for a tool you
installed this month; rewrite a vague update into the four-fact form.

### 6.2 One-screen printable card

A fenced block in §0 of the module, plus a "Print the card" button. About 25 lines of page script
and one `@media print` rule hide everything except the card. No external requests, works offline.
Both themes print dark-on-white. Text of the card (fits one A4 page and one 1366 × 768 screen):

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
 short announced window → TTL or lease lowered the day before.
```

### 6.3 Four "risk ladder" decision drills

All four follow `drills/SPEC.md` as it stands: no schema change. The rung is named in each
choice's `why` text ("Rung 3: …"). Sources were opened on 10 November 2026 (`read_on`). Decision
points are invented teaching devices; the debrief facts are the sources'. Topic ids exist in
`roadmap.json`; the `practise.handbook` headings were seen in the modules and must pass the usual test.

**Drill A — `pihole-2025-move-dns-no-downtime`: "Move the DNS server without anyone noticing"**

- Level L2 · track `network` · topics `dns-deep`, `docker-networking`, `network-problems` · 8 min.
- Role: you run the only DNS server for an office and its Docker hosts, and it must move to a new machine.
- **A note on the rule.** The SPEC allows community incidents only, never the user's own. So the
  drill takes its **shape** from your runbook and its **facts** from public sources:
  - primary source: Pi-hole forum, "Moving pi-hole to another machine?", 30 April 2025, answered by
    a Pi-hole team member: https://discourse.pi-hole.net/t/moving-pi-hole-to-another-machine/79548
  - supporting, for the debrief text: Pi-hole's v5-to-v6 Docker page (custom dnsmasq files ignored
    by default), the config reference (rate limit and REFUSED; listening modes), the forum thread
    on `/dev/shm`, and the thread where a v6 server warned that interface `eth0` did not exist while
    the machine's interface was `ens18` (a moderator named a Teleporter import as one possible
    origin; the origin was never confirmed).
  - The primary thread is a plan confirmed by a maintainer, not a failure report. The debrief must
    say so, and must not claim that thread shows an import breaking a server.
- Ladder focus: rungs 2, 5 and 7 on a single stateful box; avoiding rung 8.
- Decision points:
  1. *The new server is built. How do the old settings get onto it?* Best: bring lists, records
     and groups; set interface, listening mode, DHCP and web port explicitly on the new machine.
     Bad: full import of everything onto different hardware. Risky: copy the whole config
     directory across. Good: re-enter records from an exported text file and compare.
  2. *Users say DNS "stops" at busy times and the dashboard shows a high load.* Best: read the FTL
     log for rate-limit and shared-memory lines and check `/dev/shm` (rung 1). Bad: conclude "too
     many users" and size up. Risky: restart FTL whenever it happens.
  3. *How do clients move?* Best: both servers live, records frozen, answers compared, DHCP hands
     out both, the old address retired last. Bad: swap addresses in one step at midday. Risky: point
     the router at the new server only, today. Good: a night window with a straight swap; it works,
     but it spends downtime that was not needed.
  4. *The old server also hands out DHCP leases.* Best: move DHCP last, in a short announced
     window: off on the old, then on on the new, old side ready to re-enable. Bad: enable both "for
     overlap". Risky: leave DHCP on the old box indefinitely.
  5. *Everything has moved. What now?* Best: a second resolver, settings pinned, a scheduled export
     kept off the box, the freeze lifted and announced. Bad: wipe the old box the same hour. Risky:
     keep the raised rate limit and never look for the noisy client.
- Practise: `42-problems-network-dns-tls-vpn.md` "7.4 Pi-hole or AdGuard: port 53 busy, clients
  bypass"; `30-learn-docker.md` "daemon.json keys that matter on-prem".

**Drill B — `proxmox-2023-nic-rename-pcie`: "Pull a card, lose the network"**

- Level L2 · track `cloud` · topics `proxmox-ve`, `ubuntu-netconfig`, `network-problems` · 6 min.
- Source: Proxmox forum, "Is there any way to keep the NIC from going down after PCIe change",
  30 November 2023, marked solved (the main answer appears to come from Proxmox staff: confirm the
  label when writing the drill):
  https://forum.proxmox.com/threads/is-there-any-way-to-keep-the-nic-from-going-down-after-pcie-change.137389/
  The Proxmox admin guide (network configuration) supports the debrief: names can change with
  kernel and driver updates, a link file can override a name, a pinning tool exists, and manual
  edits are applied with `ifreload -a`.
- Why this one: it is the public twin of your TrueNAS case (no address after an adapter was
  re-seated), on a single host with one way in.
- Ladder focus: rung 1 at the console before anything else; rung 5 with out-of-band access; the
  low-rung habit of asking "what did I physically touch?".
- Decision points:
  1. *A PCIe card must come out of a single host whose only network port may be renamed.* Best:
     plan it as a window: console or IPMI ready, the port's MAC address and current name written
     down, the name pinned first. Bad: do it remotely and hope. Risky: switch the kernel to old-style
     names (the main answerer warned that these are not stable across hardware changes or even reboots).
  2. *After the change the host has no network.* Best: at the console, list the interfaces and
     compare with the name in the network config (rung 1). Bad: reinstall. Risky: reboot again and again.
  3. *You pin the name with a link file matched on the MAC address, and the port goes down.* Best:
     the config file still used the old name; change both halves together, then reload networking
     (this happened in the thread). Bad: delete the pin and give up. Risky: edit over SSH on that
     same port.
  4. *What stops a repeat?* Best: names pinned by MAC on every host, a note in the hardware-change
     runbook, console access checked before any hardware work. Bad: "never touch the hardware".
- Practise: `42-problems-network-dns-tls-vpn.md` "1.1 netplan apply locks you out";
  `50-problems-cloud-iac-proxmox.md` "7. Proxmox VE: repositories, host network and cluster".

**Drill C — `monzo-2019-cassandra-scale-up`: "More servers, missing data"**

- Level L3 · track `data` · topics `db-ha`, `change-management`, `outage-basics` · 8 min.
- Source: Monzo's public incident report on why the bank was not working on 29 July 2019:
  https://monzo.com/blog/2019/09/08/why-monzo-wasnt-working-on-july-29th
- Facts for the debrief: six servers were added to a production database cluster at 13:10 to gain
  capacity; a setting meant they joined as active members before holding data; card payments began
  failing at 13:14 and customers were logged out of the apps from 13:32; an incident was declared at 13:15; the scale-up was first ruled out; by 14:13 a
  query proved a new server was answering for data it did not have; from 14:18 the new servers were
  removed one at a time over about fifty minutes; missing writes were recovered afterwards from
  events stored elsewhere; follow-ups included fixing and documenting the setting, more metrics,
  and splitting the single shared cluster.
- Ladder focus: rung 2 is not safe by default on stateful systems; the undo of a risky step is
  itself done one member at a time; "what changed?" must stay on the list even when its graphs look fine.
- Decision points:
  1. *Four minutes after capacity was added, payments fail. The new servers' graphs look normal.*
     Best: declare, and keep the scale-up as suspect number one until a test clears it. Bad: rule it
     out because the graphs look normal. Risky: roll back an unrelated recent deploy first.
  2. *Evidence conflicts across services.* Best: one direct read-only query for a key that should
     exist, against a new server (rung 1). Bad: restart the services that report errors.
  3. *The new servers hold no data but answer queries. How do you undo it?* Best: remove them one
     at a time, waiting for each to finish. Bad: switch all six off together. Risky: change the
     setting live and let them fill up.
  4. *Service is back, but some writes landed only on the removed servers.* Best: reconcile from
     the independent record of events before saying "resolved". Bad: announce resolved now.
  5. *Prevention.* Best: document what the setting really does, rehearse with several nodes at
     once, and split the shared cluster to shrink the reach.
- Practise: `38-learn-databases-ops.md` "Failover, fencing and Patroni";
  `39-learn-senior-architecture.md` "Change management and CAB-lite".

**Drill D — `github-2018-43-seconds`: "Fast and wrong, or slow and right"**

- Level L4 · track `data` · topics `db-ha`, `incident-command`, `availability-dr` · 8 min.
- Source: GitHub, "October 21 post-incident analysis", 2018:
  https://github.blog/news-insights/company-news/oct21-post-incident-analysis/
- Facts for the debrief: maintenance on network equipment cut one site off for 43 seconds at 22:52
  UTC; the database failover tool promoted primaries in the other region; each side then held
  writes the other lacked; webhooks and Pages builds were paused at 23:19; the team chose data
  integrity over a fast recovery and restored from backups; a posted recovery estimate proved
  wrong; a backlog of millions of events was worked off; service was degraded for 24 hours and 11
  minutes; follow-ups: no automatic promotion across regions, a richer status page, fault injection.
- Ladder focus: rungs 7 and 8. A deliberate, announced, long degraded period can be the safe choice.
- Decision points:
  1. *Both sites hold writes the other lacks.* Best: stop what makes it worse (pause the jobs that
     write) before deciding anything else. Bad: fail straight back. Risky: let automation continue.
  2. *Fast recovery or complete data?* Best: integrity first: restore, resync, then return. Bad:
     fail back now and drop the newer writes. Risky: serve from the far region despite the latency.
  3. *Users ask how long.* Best: honest status, what works and what does not, the next update
     time, no precise finish time. Bad: a confident estimate. Risky: silence until it is over.
  4. *The backlog is huge and some entries have expired.* Best: pause processing, lengthen the
     expiry, then drain it. Bad: let it run and lose more.
  5. *Prevention.* Best: fence the failover tool to one region; test the assumption with fault injection.
- Practise: `38-learn-databases-ops.md` "Failover, fencing and Patroni";
  `39-learn-senior-architecture.md` "Incident command".

**Reserves** (opened, suitable, not written out):

- Cloudflare, 17 July 2020: one policy line on one router, 27 minutes, about half of traffic.
  Rung 5 that reached everywhere. https://blog.cloudflare.com/cloudflare-outage-on-july-17-2020/
- GitLab, 2020: the PostgreSQL upgrade in a planned window, seven rehearsals, fallback nodes left on
  the old version. A "when a window wins" drill, built from an engineering report rather than a
  post-mortem. https://about.gitlab.com/blog/2020/09/11/gitlab-pg-upgrade/

### 6.4 A "safest next step" hint without rewriting the playbooks

The Markdown modules stay untouched. One small data file and a build step add a single line under
chosen headings.

- **Data:** `hints/safest-step.tsv`, one hint per line: `file`, `heading`, `rung`, `text`.
- **Build:** about 25 lines in `site_ui.py`. After a matching heading it inserts one line:
  "Safest next step · rung N: text", where the rung links to the ladder section of the new module.
  Styling reuses the existing callout class with one modifier.
- **Tests** (the pattern of the `practise.handbook` check): every `file` and `heading` exists; rung
  is 1–8; text is 160 characters at most; no real names or addresses; the whole file stays under 12 KB.
- **Start with about 30 hints**, placed where the temptation to restart is strongest.

Starter set (headings seen in the modules):

| File | Heading | Rung | Hint |
|---|---|---|---|
| `25-playbook-site-down.md` | 7. Proxy error scenarios: 502, 503, 504 | 1 | Read the proxy's log line for one failing request before restarting anything. A deploy just before it? Rung 4. |
| `23-playbook-slow-system.md` | Save a snapshot before you dig | 1 | Looking is free; a restart erases what you came to see. |
| `52-devops-day-to-day.md` | 5.2 Deploy broke production | 4 | Roll back first. Stop if the release changed the data format. |
| `42-problems-network-dns-tls-vpn.md` | 1.1 netplan apply locks you out | 5 | One host, console open, `netplan try` so it reverts by itself. |
| `42-problems-network-dns-tls-vpn.md` | 7.4 Pi-hole or AdGuard: port 53 busy, clients bypass | 1 | Name the owner of port 53 first. Do not stop the host's resolver before it has another one. |
| `44-problems-docker-swarm-registry.md` | 8.5 Rolling update stuck or no rollback | 4 | `docker service rollback`, then find out why the new task was unhealthy. |
| `30-learn-docker.md` | daemon.json keys that matter on-prem | 6 | A daemon restart touches every container on the host. On a Swarm node: a window. |
| `21-case-apache-443-dokploy.md` | 9. Phase 8 — Cutover with minimal downtime | 6 | Prepare the routes on the side; the window holds only the switch. |
| `38-learn-databases-ops.md` | Failover, fencing and Patroni | 7 | The lead decides. Check lag and the backup first; one member at a time. |
| `26-playbook-containers-k8s.md` | 10. Kubernetes: nodes, storage and control plane | 2 | Cordon and drain one node before you change it. |

For **new** text, a matching Markdown convention costs one line in the callout list of
`site_ui.py`: a blockquote that starts with a ladder mark and "Safest next step" renders the same way.

### 6.5 Optional small interactive pieces

- **"Which rung is this?"** Three questions in the module: undo in under five minutes? one object
  or all? state or data involved? The answer names the rung, who decides and the checks from the
  card. About 3 KB, no storage, no network.
- **A rung tag in the Command Decoder** for the twenty commands people reach for under pressure
  (`systemctl restart`, `docker service rollback`, `kubectl drain`, `netplan apply`, `zfs rollback`):
  one extra field per card, shown as "rung N".
- Later, from `research/ideas-2026-11-10.md`: game-day mode can score "lowest rung that fixed it".

### 6.6 Order of work

1. Write the module. It is the content everything else links to.
2. Add the card and its print rule.
3. Drill A, then B (your own world), then C and D.
4. The hint file with ten hints, then grow it to about thirty.
5. The optional pieces, only if the size check still shows more than 100 KB free.

---

## 7. Sources

Opened on 10 November 2026 unless marked otherwise.

**Method, incidents, postmortems**

- Google SRE book, Effective Troubleshooting (the loop, triage first, side effects of tests, starting from recent changes): https://sre.google/sre-book/effective-troubleshooting/
- Google SRE book, Emergency Response (untested rollback, weak canary for a "low-risk" change): https://sre.google/sre-book/emergency-response/
- Google SRE book, Managing Incidents (roles, when to declare): https://sre.google/sre-book/managing-incidents/
- Google SRE workbook, Incident Response (mitigate first, generic mitigations, case studies): https://sre.google/workbook/incident-response/
- Google SRE book, Postmortem Culture (blameless, triggers): https://sre.google/sre-book/postmortem-culture/
- Google SRE book, Embracing Risk (100% is the wrong target; planned and unplanned downtime): https://sre.google/sre-book/embracing-risk/
- Google SRE book, Service Level Objectives (the planned outage of an over-reliable service): https://sre.google/sre-book/service-level-objectives/
- Google SRE workbook, Canarying Releases (definition, one canary at a time): https://sre.google/workbook/canarying-releases/
- Jennifer Mace, Generic mitigations (O'Reilly with Google, 2020): https://www.oreilly.com/content/generic-mitigations/
- PagerDuty Incident Response, Incident Commander training (size up, stabilise, update, verify; timeboxing; strong objections): https://response.pagerduty.com/training/incident_commander/
- PagerDuty, During an Incident; Customer Liaison; Postmortem Process: https://response.pagerduty.com/during/during_an_incident/ · https://response.pagerduty.com/training/customer_liaison/ · https://response.pagerduty.com/after/post_mortem_process/
- Richard Cook, How Complex Systems Fail (several causes, hindsight, change brings new failures): https://how.complexsystems.fail/
- John Allspaw, On Being a Senior Engineer (trade-offs, biases): https://www.kitchensoap.com/2012/10/25/on-being-a-senior-engineer/
- Brendan Gregg, the USE method: https://www.brendangregg.com/usemethod.html
- Grafana Labs, the RED method: https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/

**Reversibility, blast radius, progressive delivery**

- Amazon 2015 shareholder letter (one-way and two-way doors): https://www.sec.gov/Archives/edgar/data/1018724/000119312516530910/d168744dex991.htm
- AWS Builders' Library, Automating safe, hands-off deployments (one box, waves, bake time, time windows); the old aws.amazon.com address redirects here: https://builder.aws.com/content/3ErTKQOTKc5NIw031UePBPxTQ6I/automating-safe-hands-off-deployments
- AWS Builders' Library, Ensuring rollback safety during deployments (two-phase changes): https://builder.aws.com/content/3F04j2yRAAMBuPSPs50xwXZqg01/ensuring-rollback-safety-during-deployments
- Martin Fowler, Blue Green Deployment: https://martinfowler.com/bliki/BlueGreenDeployment.html
- Pete Hodgson, Feature Toggles: https://martinfowler.com/articles/feature-toggles.html

**Tool behaviour**

- Netplan, `netplan try`: https://netplan.readthedocs.io/en/stable/netplan-try/
- Nginx, command-line switches and the beginner's guide (reload behaviour): https://nginx.org/en/docs/switches.html · https://nginx.org/en/docs/beginners_guide.html
- Apache httpd, Stopping and Restarting: https://httpd.apache.org/docs/2.4/stopping.html
- Traefik, file provider: https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/
- Kubernetes, Safely Drain a Node; `kubectl diff`; customising DNS; debugging DNS (known issues): https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/ · https://kubernetes.io/docs/reference/kubectl/generated/kubectl_diff/ · https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/ · https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/
- Docker, live restore; `dockerd` reference (reloadable keys); networking (DNS); Swarm rolling update, drain, `service rollback`: https://docs.docker.com/engine/daemon/live-restore/ · https://docs.docker.com/reference/cli/dockerd/ · https://docs.docker.com/engine/network/ · https://docs.docker.com/engine/swarm/swarm-tutorial/rolling-update/ · https://docs.docker.com/engine/swarm/swarm-tutorial/drain-node/ · https://docs.docker.com/reference/cli/docker/service/rollback/
- Terraform, `terraform plan`: https://developer.hashicorp.com/terraform/cli/commands/plan
- OpenZFS, `zfs rollback`: https://openzfs.github.io/openzfs-docs/man/master/8/zfs-rollback.8.html
- Proxmox VE administration guide, network configuration: https://pve.proxmox.com/pve-docs/chapter-sysadmin.html
- Cloudflare docs, lowering TTLs before a migration: https://developers.cloudflare.com/learning-paths/dns-best-practices/concepts/phase-2
- RFC 2131, DHCP renewal timers (§4.4.5): https://www.rfc-editor.org/rfc/rfc2131

**Pi-hole (for section 5 and Drill A)**

- Docker configuration (environment variables become read-only): https://docs.pi-hole.net/docker/configuration/
- Upgrading the Docker image from v5 to v6: https://docs.pi-hole.net/docker/upgrading/v5-v6/
- Configuration reference (rate limit, listening modes, defaults): https://docs.pi-hole.net/ftldns/configfile/
- Interface binding and the open-resolver warning: https://docs.pi-hole.net/ftldns/interfaces/
- FAQ, why Pi-hole should be the only DNS server: https://discourse.pi-hole.net/t/why-should-pi-hole-be-my-only-dns-server/3376
- Forum threads: moving to another machine (2025) https://discourse.pi-hole.net/t/moving-pi-hole-to-another-machine/79548 · shared memory https://discourse.pi-hole.net/t/shmem-ram-shortage-dev-shm/59004 · v6 release fixes https://discourse.pi-hole.net/t/v6-post-release-fixes-and-findings/76480 · the `eth0` warning https://discourse.pi-hole.net/t/dnsmasq-warn-warning-notification-in-pi-hole-v6/77047 · Teleporter and `misc.dnsmasq_lines` (2026) https://discourse.pi-hole.net/t/misc-etc-dnsmasq-d-and-teleporter-upgrade-settings-6-2-2-to-6-7-1/87876 · installing an older version https://discourse.pi-hole.net/t/migrate-pi-hole-installation-install-older-version/78397

**Public incidents and community threads (drills)**

- Monzo, 29 July 2019: https://monzo.com/blog/2019/09/08/why-monzo-wasnt-working-on-july-29th
- GitHub, 21 October 2018: https://github.blog/news-insights/company-news/oct21-post-incident-analysis/
- Cloudflare, 17 July 2020: https://blog.cloudflare.com/cloudflare-outage-on-july-17-2020/
- GitLab, PostgreSQL upgrade, 2020: https://about.gitlab.com/blog/2020/09/11/gitlab-pg-upgrade/
- Meta, 4 October 2021 (losing your own tools and access with DNS): https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/
- Proxmox forum, NIC name after a PCIe change (2023): https://forum.proxmox.com/threads/is-there-any-way-to-keep-the-nic-from-going-down-after-pcie-change.137389/
- TrueNAS forum, interface renamed after a hardware change (2024; no accepted fix; replies advise the console menu or UI, and a bridge in front of the NIC): https://forums.truenas.com/t/netwwork-interface-changed-name-after-hardware-change/9189

**Could not be opened from this machine, so not relied on**

- Learning From Incidents (learningfromincidents.io): TLS error on both tries. Cook and Allspaw above stand in for that school of thought.
- Etsy Code as Craft, "Blameless PostMortems and a Just Culture": HTTP 403.
- Atlassian's incident-communication page: only navigation text came back.
- TrueNAS documentation pages: HTTP 403 for the fetcher. The 60-second test timer is known only from search-result summaries of those pages and is marked so in section 4.
- The tutorial and the GitHub repository in the runbook's own Sources list (403 and not attempted).
