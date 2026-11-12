# 54 — Practice Arena: Sites and Games to Train DevOps Skills

Reading gives you the map. Practice gives you the reflexes you need when a real server breaks and
nobody is there to ask. This module collects 165 places where you can practise DevOps work with your
hands: servers that are already broken, games for the command line and Git, DNS and TLS
playgrounds, Docker, Kubernetes and cloud labs, incident drills, defensive security ranges, SQL
puzzles and project challenges. It also includes the kind of site that started the list:
[devops.games](https://devops.games/), a strategy game about software delivery for tech leaders.

The first 80 sites were opened, or seen at their exact address in search results, on 3 October
2026. A second sweep on 7 November 2026 added 51 more and re-tested about 40 of the first 80; a third
on 9 November added 34, for 165 in all, plus about 240 checked deep links into SadServers, iximiuz and Killercoda that the map's "Prove it" ladders use. Every row added or changed by those sweeps says "checked
7 Nov 2026" or "checked 9 Nov 2026" in its Cost column; every other row still reflects 3 October. Nothing was signed up for in that sweep, so its
"free" labels describe each site as it looks before you log in. Free comes first. Every table runs from Free to
Freemium to Paid, each section opens with its best free option and closes with a **Free-only
path**, and paid options show the price model the site displayed that day. Free tiers change
often, so look again before you rely on one. Section 16 lists what has already closed, moved or
gone paid-only, what to use instead, and what no free site covers yet. Section 17 adds the other
half: free learning tools (visualisers, explainers, validators) grouped by topic.

---

## 0. How to use this module

Use this module next to the rest of the handbook, not instead of it. The handbook explains the
system and the playbooks give the method. The sites below give you broken systems to practise on,
so that the first time you meet a problem is not at work.

### The practice loop

Every practice rep follows the same four steps. It is the handbook's
[Study method](34-roadmap.md#study-method) applied to practice sites.

1. **Learn the concept first.** Read the handbook note, then the KodeKloud lesson for it, in the order given in [Learning with KodeKloud](40-career-ladder.md#9-learning-with-kodekloud). A practice site teaches you little if you cannot name what you are looking at.
2. **Practise on a site with a timer.** Give an easy scenario 30 minutes and a medium one 45. Take no hints until the timer runs out, then read the solution and find the exact step you missed.
3. **Reproduce it on your own homelab VM.** Snapshot an Ubuntu VM, break the same thing on purpose and fix it again using only the matching playbook. The practice VM is deleted after the session, but your own servers, Dokploy hosts and kubeadm cluster are where the skill has to work.
4. **Write a five-line note.** Symptom, first wrong guess, the evidence that settled it, the fix, and what you will check first next time. A folder of these notes is the best interview preparation you can have.

A note from one morning rep looks like this:

```text
date:        2026-10-06 · SadServers, easy, tag nginx · 28 min · no hints
symptom:     the site returns 502 Bad Gateway
first guess: the app process had crashed
evidence:    ss -ltnp shows the app on 127.0.0.1:8081, but nginx proxies to :8080
fix:         corrected the proxy_pass port, nginx -t, systemctl reload nginx
check first: compare the proxy target with ss -ltnp before reading app logs
```

The timer matters more than it looks. Without it you drift into reading documentation for an hour
and remember none of it. With it you learn to collect evidence in a fixed order, which is the habit
the playbooks in [Site down](25-playbook-site-down.md) and [Why is it slow?](23-playbook-slow-system.md)
are built on.

### Choose by career stage

Start in the row for your stage. Move to the right-hand column when the left one feels easy.

| Stage | Level | Start with | Add when that feels easy |
|---|---|---|---|
| Fresher | L0 Foundations | Linux Journey, OverTheWire Bandit, Learn Git Branching, Subnetting Practice, SQL Murder Mystery | Linux Upskill Challenge on a small VM, Mess With DNS, the Docker workshop |
| Junior | L1 Operator | KodeKloud Engineer's 100 Days of DevOps, SadServers easy scenarios, badssl.com, KodeKloud playgrounds, Linuxzoo | iximiuz Docker roadmap, GitLab CI tutorials on your own GitLab, the Harbor demo, Grafana Play, AWS Educate |
| Mid-level | L2 Troubleshooter | SadServers medium scenarios, iximiuz challenges, Killercoda CKA scenarios, flAWS, the Isovalent Cilium lab | Kubernetes Goat, Wheel of Misfortune as the on-call engineer, the PromQL cheat sheet, Pwned Labs and Cybr free labs |
| Senior | L3 Platform | Kubernetes the Hard Way, Containerlab, CloudGoat, the OpenTelemetry demo | running Wheel of Misfortune as game master, Coding Challenges, the Wiz Cloud Security Championship |
| Senior/Lead | L4 SRE | DevOps Dream on devops.games, DORA Quick Check, your own game days, postmortem reading | CodeCrafters, coaching juniors through SadServers, PagerDuty's incident roles, The Incident Challenge |

Work at your level and read one level up. If a site starts to feel like reading rather than doing,
move on. The goal is reps on broken systems, not badges.

### Free, freemium and paid

The Cost column describes what that row asks you to use, with one of three labels.

- **Free**: what the row describes costs nothing. Some sites need a free account (KodeKloud, GitHub, Red Hat, Cisco NetAcad).
- **Freemium**: you can practise for real on the free tier, and a paid plan adds scenarios, time or courses. The price model is quoted as the site showed it on 3 October 2026.
- **Paid**: you pay to use it, sometimes after a free trial or a few free levels.

Every section has a free-only path, so you never need to pay to cover a skill. Three paid items
do earn their price for you. killer.sh comes with two sessions when you buy the CKA exam, so you
only pay if you want more. A KodeKloud subscription already includes the CKA course with its
Lightning Labs and mock exams. SadServers Pro is cheap and adds the most realistic break-and-fix
practice once you have finished the free scenarios.

Watch for the hidden cost. Labs that run in your own cloud account bill you like any other
resources: CloudGoat and the other own-account "goats" in sections 7 and 11, AWS Workshops outside
the free Builder Center sandbox, the Cloud Resume Challenge, and a Linux Upskill Challenge server
in the cloud. Set a budget alarm before you start and tear everything down the same day. If you
need your own AWS account, the AWS Free plan is the safest kind: up to $200 of credits, it closes
after six months or when the credits run out, and AWS says nothing is charged unless you upgrade
or turn on paid-only services.

### Where it runs

The rows added on 7 November 2026 also say where the lab runs, because who owns the machine or
account decides the risk.

- **Browser**: the vendor hosts everything. You need a browser, sometimes an SSH client.
- **Vendor-owned account**: a real cloud account or lab VM that the vendor creates and deletes. It cannot bill you.
- **Throwaway VM or Codespace**: you run it yourself on a lab VM or a GitHub Codespace and delete it afterwards, never on your work laptop or a real server. A free personal GitHub account gets 120 core-hours and 15 GB-month of Codespaces a month with no payment method, and usage stops at the quota instead of being billed. That is about 60 hours on the smallest 2-core machine.
- **YOUR cloud account (can bill you)**: you deploy it into your own AWS, Azure or GCP account and pay for what it uses.

### Practise safely

These rules apply to every site in this module.

- Practise only on platforms built for it, or on VMs and accounts you own. Never scan, attack or "test" a system without written permission, and that includes your employer's production.
- Run vulnerable-by-design labs (Kubernetes Goat, CloudGoat, OWASP Juice Shop) in isolation: a throwaway VM, a kind or k3s cluster, or a separate AWS account. Keep them off the network that holds Wazuh, Harbor, GitLab or anything real, and destroy them when you finish.
- Never paste real hostnames, addresses, logs, keys or customer data into a practice site or its AI assistant. Use example.com and the documentation address ranges, as the rest of the handbook does.
- An internet-facing practice server is attacked within minutes of going online. Use key-only SSH, a firewall and updates from the first hour, and delete the server when you are done.
- When you test a public site of your own on SSL Labs, tick the option that keeps the result off its public boards.
- Treat downloaded capture files and security datasets as untrusted. Open them inside a lab VM, never on your work laptop.
- Some practice services are public. Anyone can see what you push to the Harbor demo, your pull requests to the DevOps-Daily challenges and the HTTP Observatory scan history. Use throwaway images and sanitised code.

### How to read the tables

Each section has one table. **Site** links to the page to start from. **What you practise** says
what your hands will do there. **Cost** uses the labels above. **Level / stage** uses the handbook
scale: L0 Fresher, L1 Junior, L2 Mid-level, L3 Senior, L4 Senior/Lead. **Use it with this
handbook** names the module to read before or after. Rows added on 7 November 2026 put sign-up,
where it runs and the check date in the Cost column. Under each table, the **Free-only path**
gives a no-cost route through the section and **Best picks** explains the strongest sites and
exactly what to do first.

---

## 1. Broken-server troubleshooting

These sites hand you a machine that is already broken, a short symptom and a clock. That is the
skill the job pays for and the one courses rarely train: finding evidence on a system you did not
build. Use them for the 30-minute morning rep, one scenario per workday.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [KodeKloud Engineer](https://engineer.kodekloud.com/) | Ticket-style tasks on the servers of a simulated company, graded automatically: Linux administration, Git, Docker, Kubernetes, Jenkins, Ansible, Terraform | **Free** · 100 Days of DevOps and 100 Days of Cloud are in KodeKloud's free tier (one task a day) | L0–L2 · Fresher–Mid | [Linux](27-learn-linux.md), [Docker](30-learn-docker.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [Killercoda](https://killercoda.com/) | Browser VMs with guided scenarios, plus empty Ubuntu and Kubernetes playgrounds to break on purpose | **Free** · free scenarios and playgrounds; the PLUS plan (4-hour sessions) and COURSE plan (CKA, CKAD and CNPE courses) are paid | L0–L3 · Fresher–Senior | [Linux](27-learn-linux.md), [Kubernetes](31-learn-kubernetes.md) |
| [iximiuz USE Practice](https://labs.iximiuz.com/playgrounds/use-practice-4ce4816f) | A VM that starts a random CPU, memory, disk or network load; you find which resource is saturated | **Free** · runs on iximiuz's free Basic plan (one hour of playtime a day) | L1–L2 · Junior–Mid | [Why is it slow?](23-playbook-slow-system.md), [Performance](32-learn-performance-observability.md) |
| [Linuxzoo](https://linuxzoo.net/) | Your own Linux VM with root, run by Edinburgh Napier University since 2004, with tutorials on administration, networking, firewalls, SELinux, DNS, Apache, logs and diagnostics | **Free** · register and join a queue; no card mentioned · runs on their VM through a browser SSH client or your terminal · checked 7 Nov 2026 | L0–L2 · Fresher–Mid | [Linux](27-learn-linux.md), [Linux problems](41-problems-linux-systems.md) |
| Killercoda community break-fix series: [The Dev Bench](https://killercoda.com/barrymister), [Devopsify](https://killercoda.com/devopsify/course/en), [KubeDojo](https://killercoda.com/kubedojo) and [EgyKode](https://killercoda.com/egykode) | Short, ticket-sized breaks on a real Ubuntu VM: sudo broken by a bad drop-in, a full LVM volume, a bad fstab line, a service that won't start, a proxy 502, a TLS chain. Community-written, so quality varies; these four are in English and were checked | **Free** · free Killercoda account, one-hour sessions · checked 9 Nov 2026 | L0–L3 · Fresher–Senior | [Linux problems](41-problems-linux-systems.md), [Site down](25-playbook-site-down.md) |
| [SadServers](https://sadservers.com/scenarios) | Real Linux VMs with something broken (web servers, disk, DNS, Docker, databases, Kubernetes), a time limit and a solution to read afterwards | **Freemium** · free plan with "a selection of scenarios with daily limits" (at least 57 of the 96 listed; the limit is not published); [Pro](https://sadservers.com/pricing) $9 a month or $72 a year; Pro+ $11 a month, $88 a year or $249 once · runs in the browser on their VM · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Site down](25-playbook-site-down.md), [Why is it slow?](23-playbook-slow-system.md), [Who owns this port?](22-playbook-ports-inventory.md) |
| [iximiuz Labs challenges](https://labs.iximiuz.com/challenges) | Short challenges on real VMs with hints and automatic checks: Linux, networking, containers, Kubernetes, CI/CD, security | **Freemium** · free Basic plan (one playground at a time, one hour a day, part of the content); [Complete Bundle](https://labs.iximiuz.com/pricing) billed yearly ($48 shown) or $144 once | L1–L3 · Junior–Senior | [Docker & K8s incidents](26-playbook-containers-k8s.md), [Networking](28-learn-networking.md) |
| [SysAdmin Simulator](https://sys-admin-simulator.com/) | A live on-call shift: alerts arrive, an SLA clock runs, and you triage and fix in a real terminal | **Freemium** · a free account starts a shift; team training is offered, with no public price list | L1–L3 · Junior–Senior | [Site down](25-playbook-site-down.md), [Network speed](24-playbook-network-speed.md) |

**Free-only path:** alternate a KodeKloud Engineer task and a free SadServers scenario on workday
mornings, make one rep a week a USE Practice run or a Linuxzoo tutorial, and rebuild every failure
on your own homelab VM at the weekend.

### Best picks for broken servers

**KodeKloud Engineer, 100 Days of DevOps (free).** You already study with KodeKloud, and this
challenge turns that into a daily graded task on the servers of a simulated company. The tasks read
like tickets, so you practise the shape of the job: find the right host, change it and prove that
it works. First: sign in, start 100 Days of DevOps and do day 1 against a 30-minute timer. Then do
one task per working day; the free plan allows one a day anyway.

**iximiuz Labs (free and freemium).** Each challenge targets one mechanism, such as a Ready node
that schedules nothing or a readiness probe that holds a pod at 0/1, so you learn why a fix works
rather than which command to type. The USE Practice playground starts a random load and you find
the saturated resource, which is the 60-second checklist from
[Why is it slow?](23-playbook-slow-system.md) against a live target. First: one USE Practice run
with `uptime`, `vmstat 1`, `mpstat -P ALL 1`, `iostat -xz 1` and `free -m`, then the Kubernetes
challenge about a node that is Ready but schedules nothing.

**SadServers (freemium).** This is the closest you can get to a real outage without being on call:
an SSH session on a VM where something is wrong, a one-paragraph symptom, a check button and a time
limit. First: open the scenario list, filter by the nginx, dns and docker tags, take an easy one
and start a 30-minute timer. When time runs out, read the solution and write the five-line note.
Pro doubles the time limit and opens more than 125 scenarios, which matters once the free set is
done.

These free scenarios (free with an email sign-up, checked 7 Nov 2026) match your stack:
[San Juan](https://sadservers.com/scenario/san-juan) ("mucho Traefik", a Traefik load balancer in
Docker Compose, the nearest thing to a Dokploy drill), [Salta](https://sadservers.com/scenario/salta)
(a Docker container that will not start), [Helsingør](https://sadservers.com/scenario/helsingor)
(Postgres replication in Compose), [Bilbao](https://sadservers.com/scenario/bilbao),
[Buenos Aires](https://sadservers.com/scenario/buenos-aires) and
[Bengaluru](https://sadservers.com/scenario/bengaluru) (Kubernetes), and
[Kilifi](https://sadservers.com/scenario/kilifi) (Helm). "Lyon", which migrates Ingress-NGINX to
Traefik, is Pro-only. Free VMs have no internet access and are destroyed when you finish.

**Linuxzoo (free).** A real VM where you are root, with no install and no bill. The tutorials
cover the server side of the job (Apache, DNS, firewall rules, SELinux, logs). First: register,
join the queue and switch your machine on, then do the diagnostics tutorial and the Apache one, and
compare what you did with [Linux problems](41-problems-linux-systems.md).

**SysAdmin Simulator (freemium).** Use it to practise incident flow rather than single fixes:
several alerts at once, a clock, and the choice of what to mitigate first. First: play one free
shift, then write the timeline as if you were posting it in the incident channel.

---

## 2. Linux command line and shell

L0 and L1 live here. The goal is not to memorise flags but to read a system: files, permissions,
processes, pipes and logs. Pick one game for fun and one structured track, and do both in the same
week.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Linux Upskill Challenge](https://linuxupskillchallenge.org/) | A month of daily lessons (21 in total, one or two hours each) running your own internet-facing Linux server: SSH, users, packages, logs, firewall, scheduling | **Free** · open source; you provide the server | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md), [SSH](09-ssh-remote-access.md) |
| [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) | Log in over SSH and find each level's password behind odd file names, permissions, search, compression and pipes | **Free** | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md), [SSH](09-ssh-remote-access.md) |
| [pwn.college Linux Luminarium](https://pwn.college/linux-luminarium/) | 15 modules and about 128 checked challenges in an in-browser workspace: paths, commands, globbing, pipes, variables, processes, permissions, users | **Free** | L0 · Fresher | [Linux](27-learn-linux.md) |
| [CMD Challenge](https://cmdchallenge.com/) | One-line shell puzzles in a browser terminal: `find`, `grep`, `sort`, `uniq`, `awk`, `sed` and pipes | **Free** | L0–L2 · Fresher–Mid | [Logs & journal](06-logs-journal.md), [Linux](27-learn-linux.md) |
| [The Command Line Murders](https://github.com/veltman/clmystery) | Clone a repository and solve a murder mystery with `grep`, `head`, `cat` and pipes over text files | **Free** | L0 · Fresher | [Linux](27-learn-linux.md) |
| [Linux Journey on LabEx](https://labex.io/linuxjourney) | The classic Linux Journey lessons, from the command line to networking and the kernel, now with a browser terminal | **Free** · no sign-up for the lessons | L0 · Fresher | [Linux](27-learn-linux.md) |
| [WebTerm free play](https://webterm.app/en/free-play) | A simulated shell for the first hour: `ls`, `cd`, `chmod`, pipes and files in a virtual file system with canned output. The site claims 100+ commands; about 70 worked when tested, and `sudo`, `apt`, `ip`, `ss` and `journalctl` are missing, so move on to a real VM by day two | **Free** · no sign-up · runs in your browser tab only · checked 9 Nov 2026 | L0 · Fresher | [Linux](27-learn-linux.md#no-vm-use-these) |
| [Terminus](https://web.mit.edu/mprat/Public/web/Terminus/Web/main.html) | A browser text adventure that teaches moving around and handling files; ten minutes for absolute beginners | **Free** | L0 · Fresher | [Linux](27-learn-linux.md) |
| [Exercism Bash track](https://exercism.org/tracks/bash) | 97 scripting exercises with automatic analysis and optional feedback from volunteer mentors | **Free** | L1–L2 · Junior–Mid | [Linux](27-learn-linux.md) |
| [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) | A clean Ubuntu 24.04 VM in the browser for an hour, extendable, to break and fix anything from the handbook | **Free** · KodeKloud account | L0–L3 · all stages | [Linux](27-learn-linux.md), [Case: Apache vs Dokploy](21-case-apache-443-dokploy.md) |
| [Killercoda Linux](https://killercoda.com/linux) | Community scenarios and courses on a real Linux VM, guided step by step | **Free** · PLUS adds longer sessions | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md) |
| [systemd by example](https://systemd-by-example.com/) | A shell in a sandbox where you write, edit and remove unit files, then watch dependencies and targets behave; a five-part article series explains each step | **Free** · no login or price mentioned · runs in the browser on their container, 10 minutes a run, no network · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Services & systemd](07-services-systemd.md), [Linux problems](41-problems-linux-systems.md) |
| [Webminal](https://www.webminal.org/) | A browser terminal with lessons from navigation to shell scripting, "Linux Command Golf" challenges and MySQL access; free since 2011 | **Free** · free account · runs in the browser · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md) |
| [WebVM](https://webvm.io/) and [Linux Dungeon](https://jfoxuk.github.io/webvm/) | A full Linux system compiled to WebAssembly; Linux Dungeon is an escape-room game of directories, clues and config edits built on it | **Free** · open source, no sign-up · runs in your browser tab only · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md) |
| [learnbyexample TUI apps](https://github.com/learnbyexample/TUI-apps) | Terminal apps with 70+ text-processing, 50+ grep, 50+ sed and 80+ awk exercises | **Free** · open source · runs in a throwaway VM or Codespace · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Logs & journal](06-logs-journal.md), [Linux](27-learn-linux.md) |
| [Under The Wire](https://underthewire.tech/) | PowerShell wargames over SSH in the style of Bandit (Century, Cyborg, Groot, Oracle, Trebek); Oracle covers the registry and DNS zone records | **Free** per player write-ups; a 2021 blog says the first credentials come from the project's Slack · runs on their Windows hosts over SSH · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Windows](17-windows.md) |
| [ProLUG Linux course and labs](https://professionallinuxusersgroup.github.io/course-books/) | Volunteer course books with worksheets, and free [Killercoda labs](https://killercoda.com/het-tanis) on fail2ban with Loki, rsyslog over TLS, UFW, the startup process and `lsof` troubleshooting | **Free** · free Killercoda account · runs in the browser · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Linux](27-learn-linux.md), [Linux problems](41-problems-linux-systems.md), [Wazuh & security tools](48-wazuh-and-security-tools.md) |
| [The Missing Semester (MIT, 2026)](https://missing.csail.mit.edu/2026/) | Lectures on the shell, the command-line environment, debugging, Git and packaging, each with exercises | **Free** · no sign-up · exercises on your lab VM · checked 9 Nov 2026 | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md) |
| [Incus online demo](https://linuxcontainers.org/incus/try-it/) | A real VM for 30 minutes with a guided tour of instances, snapshots, storage and networks; the nearest free stand-in for Proxmox VE concepts | **Free** · accept the terms, no sign-up · 5 sessions per IP, almost no internet, for evaluating Incus only; down for maintenance on one visit · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Linux](27-learn-linux.md), [Cloud, IaC & Proxmox](50-problems-cloud-iac-proxmox.md) |
| [Vim Adventures](https://vim-adventures.com/) | A puzzle game that drills Vim motions and commands | **Paid** · first levels free; a licence costs $35 for six months, or $40 with the timed challenges | L0–L1 · Fresher–Junior | [Linux](27-learn-linux.md) |

**Free-only path:** Linux Journey for the concepts, Bandit levels 0 to 15, the Linux Luminarium,
ten CMD Challenge puzzles a week for pipelines, then the Linux Upskill Challenge on a small server
and the Exercism Bash track for scripts. Add systemd by example once you write your own units, and
Under The Wire's Century game for the Windows hosts you look after. `vimtutor`, which ships with
Vim, replaces Vim Adventures.

### Best picks for Linux

**Linux Upskill Challenge (free).** It is the most job-shaped option on this list: for a month you
look after a real server that is exposed to the internet, which is what you do on your on-prem
Ubuntu hosts. First: create a small Ubuntu server. A cloud VM with a budget alarm is safer than
opening a port on your home network. Switch SSH to keys only, then start day 1 and keep the daily
notes in a Git repository.

**OverTheWire Bandit (free).** Every level starts with an SSH login and ends with a password hidden
somewhere awkward, so `ssh`, man pages, `find`, `file` and pipes become reflexes. First: levels 0 to
10 in one sitting. For each level, write down the one command that found the password.

**pwn.college Linux Luminarium (free).** The gentlest structured start, run by a team at Arizona
State University: a workspace in the browser and short challenges that check themselves. First: the
first three modules, then the permissions and users modules, which match the ownership and sudo
sections of [Linux](27-learn-linux.md).

**CMD Challenge (free).** Log triage is pipeline building. Ten minutes on these one-liners before
work trains the `grep`, `sort`, `uniq -c` and `awk` chain you run on access logs in
[Site down](25-playbook-site-down.md). First: the first ten puzzles, then the variant sets linked
from its home page.

**systemd by example (free).** Units that start in the wrong order, or a service that never comes
back after a reboot, are hard to practise on a real host. Here each run builds a small system from
your units. First: write a service that depends on another, break the `After=` and `Wants=` lines
on purpose, and predict what `systemctl status` will show before you run it.

---

## 3. Git

Git mistakes are the most common self-inflicted outage for juniors: a force-push over a colleague's
work, a lost commit, a merge that drops a fix. Practise the scary commands (rebase, reset, reflog)
where nothing can break, then use them calmly on real repositories.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Learn Git Branching](https://learngitbranching.js.org/) | Visual levels that redraw the commit graph after each command: commits, branches, merge, rebase, cherry-pick, remotes; plus a free sandbox | **Free** | L0–L1 · Fresher–Junior | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [Git Exercises](https://gitexercises.fracz.com/) | Exercises solved in a real local repository and verified when you push your answer | **Free** | L0–L2 · Fresher–Mid | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [Oh My Git!](https://ohmygit.org/) | An open-source game that draws your repository as you play, with cards for beginners and a real Git terminal | **Free** · download for Linux, macOS or Windows | L0 · Fresher | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [GitHub Skills](https://learn.github.com/skills) | Courses that run inside your own copy of a repository, guided by issues and pull requests; several cover GitHub Actions | **Free** · GitHub account | L0–L2 · Fresher–Mid | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [KodeKloud Git playground](https://kodekloud.com/playgrounds/playground-git) | `git` plus a Gitea server for an hour: remotes, merge conflicts, reset and reflog | **Free** · KodeKloud account | L0–L2 · Fresher–Mid | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |

**Free-only path:** Learn Git Branching (the main levels, then the remote ones), Git Exercises, and
a reflog rescue in the KodeKloud Git playground: commit, `git reset --hard HEAD~2`, then get the
commits back.

### Best picks for Git

**Learn Git Branching (free).** The fastest way to see what rebase and cherry-pick do, because the
tree redraws after every command. First: the introduction levels, then the remote levels, which
explain fetch, pull and push the way GitLab merge requests use them.

**Git Exercises (free).** Once the graph makes sense, do the same moves in a real repository on
your laptop. First: clone it, solve the first few exercises and push each answer to see whether it
passes. The exercises on conflicts and on fixing old commits are the ones that pay off at work.

**GitHub Skills (free).** Each course is a repository that teaches you by opening issues and
checking your commits. First: [Hello GitHub Actions](https://github.com/skills/hello-github-actions),
which takes under 30 minutes, then
[Publish Docker images](https://github.com/skills/publish-docker-images). The pipeline ideas carry
straight over to GitLab CI in [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md).

---

## 4. Networking, DNS and TLS

Many of the incidents in this handbook are DNS- or TLS-shaped: a name that resolves differently for
curl and dig, a certificate served on the wrong port, a proxy that answers before the app does.
These sites let you break DNS and TLS safely and read real packets without touching production.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Mess With DNS](https://messwithdns.net/) | A real subdomain on a real authoritative DNS server: create A, CNAME, MX and TXT records and watch every query arrive live | **Free** | L0–L2 · Fresher–Mid | [DNS](08-dns.md), [Networking](28-learn-networking.md), [Site down](25-playbook-site-down.md) |
| [Protocol Explorer](https://a2aprotocol.ai/tools/protocol-explorer) | Step through 33 protocols packet by packet (HTTP, TCP, DNS, TLS, DHCP, BGP, SSH, WireGuard, QUIC and more) in a network diagram and packet table, with each packet explained. A teaching simulation, not real traffic: learn what a healthy exchange looks like before you read `tcpdump`. Runs in the browser, no sign-up; checked 9 Nov 2026 | **Free** | L0–L2 · Fresher–Mid | [Networking](28-learn-networking.md), [DNS](08-dns.md), [Web, HTTP & TLS](18-web-http-tls.md) |
| [badssl.com](https://badssl.com/) | Subdomains with deliberately broken TLS: expired, wrong host, self-signed, untrusted root, weak ciphers, old protocols | **Free** | L1–L2 · Junior–Mid | [Web, HTTP & TLS](18-web-http-tls.md), [Site down](25-playbook-site-down.md) |
| [nginx playground](https://nginx-playground.wizardzines.com/) | Paste an nginx config, run curl against it in a sandbox and read the response; its sibling [DNS lookup](https://dns-lookup.jvns.ca/) shows every record type in the browser | **Free** | L1–L2 · Junior–Mid | [Web servers & proxies](29-learn-webservers-proxies.md), [Traefik](43-traefik-and-reverse-proxies.md) |
| [SSL Labs Server Test](https://www.ssllabs.com/ssltest/) | A graded report on a public HTTPS site's certificate chain, protocols and ciphers | **Free** | L1–L3 · Junior–Senior | [Traefik](43-traefik-and-reverse-proxies.md), [Security](37-learn-security-devsecops.md) |
| [Subnetting Practice](https://subnettingpractice.com/) | Random subnetting, IPv6 and binary questions with answers, plus calculators | **Free** | L0–L1 · Fresher–Junior | [Networking](28-learn-networking.md) |
| [Wireshark sample captures](https://wiki.wireshark.org/SampleCaptures) | Real capture files by protocol (DNS, HTTP, TCP, TLS and many more) to open in Wireshark or `tcpdump -r` | **Free** | L1–L3 · Junior–Senior | [Network speed](24-playbook-network-speed.md), [Networking](28-learn-networking.md) |
| [Cisco Packet Tracer](https://www.netacad.com/cisco-packet-tracer) | A network simulator: build LANs, VLANs, routing and DHCP from virtual devices | **Free** · free Cisco Networking Academy account | L0–L1 · Fresher–Junior | [Networking](28-learn-networking.md) |
| [Containerlab](https://containerlab.dev/) | Network labs written in YAML and started as containers on your Linux VM, wired together with virtual links | **Free** · open source; needs Docker | L2–L4 · Mid–Lead | [Networking](28-learn-networking.md), [Network speed](24-playbook-network-speed.md) |
| [GNS3](https://www.gns3.com/) | An open-source emulator that runs real router and Linux images in topologies you draw | **Free** · open source | L1–L3 · Junior–Senior | [Networking](28-learn-networking.md) |
| [Wizard Zines debugging mysteries](https://mysteries.wizardzines.com/) | Five branching stories (a slow website, a [connection timeout](https://mysteries.wizardzines.com/connection-timeout.html), a DNS update that did not work, a 50 ms request, a failed Docker connection) where you choose the next `curl`, `tcpdump` or `iptables` check | **Free** · no sign-up · runs in the browser, no real terminal · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Site down](25-playbook-site-down.md), [Network, DNS & TLS problems](42-problems-network-dns-tls-vpn.md) |
| [Wizard Zines questions](https://questions.wizardzines.com/) | Ten-minute question sets on TLS certificates, HTTP headers and status codes, CORS, CDNs, TCP, UDP, DNS records, Unix permissions and signals | **Free** · no sign-up · runs in the browser · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Networking](28-learn-networking.md), [Linux](27-learn-linux.md) |
| [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/) | Every byte of a real TLS 1.3 session explained, with the commands to reproduce it; sibling pages cover TLS 1.2, DTLS and QUIC | **Free** · no sign-up · runs in the browser; reproduce it on a lab VM · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Web, HTTP & TLS](18-web-http-tls.md), [Network, DNS & TLS problems](42-problems-network-dns-tls-vpn.md) |
| [RouterJockey trainers](https://routerjockey.com/training-tools/) | IPv4 and nibble-level IPv6 subnetting drills, plus binary and hex trainers | **Free** · no account · runs in the browser · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Networking](28-learn-networking.md) |
| [Nginx location match tester](https://nginx.viraptor.info/) | Paste `location` blocks and a URL and see which block nginx picks | **Free** · no sign-up · runs in the browser; no nested locations or listen ports · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Web servers & proxies](29-learn-webservers-proxies.md) |
| [htaccess tester](https://htaccess.madewithlove.com/) | See how Apache rewrite rules transform a URL before you deploy them | **Free** · no account · runs in the browser · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Web servers & proxies](29-learn-webservers-proxies.md), [Case: Apache vs Dokploy](21-case-apache-443-dokploy.md) |
| [MDN HTTP Observatory](https://developer.mozilla.org/en-US/observatory) | A graded report on the security headers and HTTP-to-HTTPS redirect of a public site of your own | **Free** · no sign-up · runs in the browser; scan history is public and the TLS tests were removed · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Traefik](43-traefik-and-reverse-proxies.md), [Security](37-learn-security-devsecops.md) |
| [Cisco DevNet Sandboxes](https://developer.cisco.com/site/sandbox/) | Real Cisco gear, always-on or reserved for up to seven days, for routing, switching and network automation | **Free** · sign-up terms not stated · runs in a vendor-owned lab · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Networking](28-learn-networking.md) |
| [network-fundamentals-lab](https://github.com/gnu-gnu/network-fundamentals-lab) | Containerlab labs that start broken: find the routing, NAT, nftables or FRR fault with `tcpdump`, `traceroute` and `ip`, then fix it in one line; walkthroughs included (README in Korean) | **Free** · open source · runs on a throwaway VM · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Networking](28-learn-networking.md), [Network problems](42-problems-network-dns-tls-vpn.md) |
| [NetBox demo](https://demo.netbox.dev/) | A public NetBox: model prefixes, VLANs, racks, devices and cables as you would document your own network | **Free** · create a user on the demo · runs in the browser · checked 9 Nov 2026 | L1–L2 · Junior–Mid | [Networking](28-learn-networking.md), [OSS toolbox](53-oss-devops-toolbox.md) |
| [httpbin](https://httpbin.org/) | A real HTTP service to hit with `curl`: methods, headers, status codes, redirects, auth and an `/anything` echo | **Free** · no sign-up · checked 9 Nov 2026 | L0–L1 · Fresher–Junior | [Web, HTTP & TLS](18-web-http-tls.md) |
| [Let's Encrypt staging environment](https://letsencrypt.org/docs/staging-environment/) | The real ACME staging CA: point certbot, Traefik or Caddy at it, fail HTTP-01 and DNS-01 on purpose, and never hit a production rate limit | **Free** · no sign-up · your ACME client runs on a lab host; staging certificates are not trusted · checked 9 Nov 2026 | L2 · Mid | [Network problems](42-problems-network-dns-tls-vpn.md), [Traefik](43-traefik-and-reverse-proxies.md) |
| [iximiuz networking playgrounds](https://labs.iximiuz.com/playgrounds?category=networking) | Small networks of real VMs: MiniLAN, a dual-network router lab, a three-node Docker Swarm | **Freemium** · free tier with daily limits | L1–L3 · Junior–Senior | [Networking](28-learn-networking.md), [Dokploy](45-dokploy-and-self-hosted-paas.md) |

**Free-only path:** ten minutes of Subnetting Practice a day for a week, the Mess With DNS
experiments, every badssl.com error reproduced with `openssl s_client`, one DNS and one TLS capture
from the Wireshark samples, one Wizard Zines mystery a week, then one Containerlab topology on your
homelab VM. Check your own public sites with SSL Labs and the HTTP Observatory after every proxy
change.

### Best picks for networking

**Mess With DNS (free).** Julia Evans and a collaborator built it as a wizard zines project. It
gives you a subdomain on a real authoritative server and shows each query as it arrives, so caching
and TTLs stop being theory. First: create an A record and query it with `dig` through two different
resolvers. Then change the record and watch which resolver keeps answering with the old value until
the TTL runs out. Finally compare what `dig`, `getent ahosts` and `curl -v` see, which is the gap
behind the DNS case in [Site down](25-playbook-site-down.md).

**badssl.com (free).** Each subdomain fails in a different, named way. First: run the loop below on
a lab VM and write down the exact verify code and message for each host. Those strings are what you
will be searching for when Harbor, a GitLab runner or Traefik reports a certificate problem.

```bash
# On your lab VM: one line of evidence per broken host
for h in expired wrong.host self-signed untrusted-root; do
  echo "== $h.badssl.com"
  openssl s_client -connect "$h.badssl.com:443" -servername "$h.badssl.com" </dev/null 2>/dev/null \
    | grep -E 'Verify return code|subject=|issuer='
done
```

**nginx playground (free).** See why a proxy answers 404, 502 or a redirect loop before you touch
Traefik. First: make each of those three failures happen on purpose, fix them, then translate the
working server block into Traefik router and service labels with
[Traefik](43-traefik-and-reverse-proxies.md). After any certificate change on a public domain of
your own, check it on SSL Labs.

**Wizard Zines debugging mysteries (free).** Of the new networking finds, only these and Under The
Wire are true "something is broken, find out why" exercises. Each step offers a check, such as `curl -v`, `tcpdump` or the
firewall rules, and shows what it would reveal. First: the connection-timeout mystery. Before each
choice, write the check you would run at work, then compare it with the order in
[Site down](25-playbook-site-down.md).

**Containerlab (free).** When you are ready for routing, MTU and multi-host problems, describe a lab
of Linux nodes in a YAML file and let Containerlab wire them together on your homelab VM. First: two
Linux nodes and one link, capture the traffic between them with `tcpdump`, then lower the MTU on
one side and watch large transfers stall while pings still work. That is the symptom chased in
[Network speed](24-playbook-network-speed.md).

---

## 5. Docker and containers

Play with Docker, the old default for practising Docker in a browser, shut down on 1 March 2026
(section 16; its page still showed the notice on 9 Nov 2026). Docker now points learners to iximiuz Labs, its own Labspaces and the workshop on
their own machine. Because Dokploy runs on Docker Swarm, also practise on a real Swarm.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Docker workshop](https://docs.docker.com/get-started/workshop/) | Docker's official hands-on guide: containerise an app, update it, share the image, persist data, bind mounts, multi-container apps, Compose | **Free** · runs on your own Docker host | L0–L1 · Fresher–Junior | [Docker](30-learn-docker.md) |
| [Docker Labspaces](https://github.com/dockersamples/labspace-infra) | Docker's replacement for browser labs: an interactive lab with a code editor that you start with one `docker compose` command and open on localhost | **Free** · runs locally | L0–L2 · Fresher–Mid | [Docker](30-learn-docker.md) |
| [KodeKloud Docker playground](https://kodekloud.com/playgrounds/playground-docker) | A Docker host with Compose for an hour, extendable | **Free** · KodeKloud account | L0–L2 · Fresher–Mid | [Docker](30-learn-docker.md), [Docker commands](14-docker-containers.md) |
| [DockerLabs by Collabnix](https://dockerlabs.collabnix.com/) | A large community collection of Docker and Kubernetes labs, from first containers to security and supply chain | **Free** | L0–L2 · Fresher–Mid | [Docker](30-learn-docker.md) |
| [Harbor demo server](https://demo.goharbor.io) | The registry you run at work, in public: create a project, `docker login`, push and pull, with normal user functions only (no admin) | **Free** · self-register; images under 100 MB; [reset every two days](https://goharbor.io/docs/main/install-config/demo-server/); never push anything sensitive · runs in the browser, plus a Docker client in a Codespace or throwaway VM · checked 7 Nov 2026 | L1 · Junior | [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md), [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [Dockerlings](https://github.com/furkan/dockerlings) | Bite-sized Docker exercises in the terminal | **Free** · open source · runs in a Codespace or throwaway VM · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Docker](30-learn-docker.md) |
| [Docker katas](https://github.com/eficode-academy/docker-katas) | Docker step by step, from hello-world to deploying a web app | **Free** · open source · runs in a Codespace or throwaway VM · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Docker](30-learn-docker.md) |
| [DevOps with Docker (University of Helsinki)](https://devopswithdocker.com/) | A graded MOOC: Dockerfiles, Compose, volumes, networks, security and image size, submitted as files you built | **Free** · mooc.fi account for submissions · runs on your throwaway VM · checked 9 Nov 2026 | L0–L2 · Fresher–Mid | [Docker](30-learn-docker.md) |
| [iximiuz Docker roadmap](https://labs.iximiuz.com/roadmaps/docker) | Checked challenges in five modules: running containers, building images, pulling and pushing, container networking, storage | **Freemium** · the free Basic plan covers part of it | L1–L3 · Junior–Senior | [Docker](30-learn-docker.md), [Docker & K8s incidents](26-playbook-containers-k8s.md) |
| [iximiuz Docker Swarm playground](https://labs.iximiuz.com/playgrounds/docker-swarm) | A three-node Swarm on real VMs with its own registry: services, overlay networks, rolling updates, draining nodes | **Freemium** · free tier with daily limits | L1–L3 · Junior–Senior | [Dokploy](45-dokploy-and-self-hosted-paas.md), [Deployment patterns](35-deployment-patterns.md) |

**Free-only path:** the Docker workshop on your homelab VM, the free iximiuz Docker challenges and
the [container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch)
tutorial, the KodeKloud Docker playground for quick experiments away from home, the free SadServers
Docker scenarios (Salta, San Juan, Helsingør; see section 1), a push to the Harbor demo, and one
Swarm session that mirrors your Dokploy setup.

### Best picks for Docker

**Docker workshop (free).** Do it on your homelab VM rather than in a playground, so that volumes,
networks and images are still there tomorrow and you can break them. First: work through the parts
in order, then delete the app's volume on purpose and watch what happens to its data. That one
experiment explains a whole family of "my data disappeared after a redeploy" questions about
Dokploy.

**Docker Labspaces (free).** Docker's own successor to browser labs runs as containers on your
machine. First: start the container-supported development labspace, then open port 3030 on
localhost in a browser.

```bash
docker compose -f oci://dockersamples/labspace-container-supported-development up
```

**iximiuz Labs (freemium).** The best structured container practice: every challenge runs on a real
VM and checks your result, and the networking module shows what Docker does with namespaces,
bridges and iptables. First: the free container networking tutorial linked above, which is the
background for "published ports bypass UFW" in [Docker](30-learn-docker.md). Then one Swarm
session: deploy a stack with two replicas, drain a node and watch the tasks move. Those are the
mechanics Dokploy relies on (see [Dokploy](45-dokploy-and-self-hosted-paas.md)).

**Harbor demo server (free).** The most stack-specific find of the November sweep: Harbor itself,
public and wiped every two days, so you can rehearse project and push workflows with no risk to
your production registry. First: self-register, create a project, then from a Codespace tag a
small image, `docker login demo.goharbor.io`, push it and pull it back. Then push to a project
that does not exist and read the error, the way a GitLab job would see it.

---

## 6. Kubernetes and the CKA

Until you pass the CKA, this section is your main practice. Troubleshooting is the heaviest exam
domain, so every break-and-fix rep here counts twice. The order of the table is also a sensible
order for the weeks before the exam.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Killercoda CKA scenarios](https://killercoda.com/cka) | Free community scenario sets for CKA topics, on real clusters that start in the browser | **Free** · community sets; Killercoda's own CKA Scenario Course needs the paid COURSE plan | L1–L3 · Junior–Senior | [Kubernetes](31-learn-kubernetes.md) |
| [KodeKloud Kubernetes playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster) | Ready-made clusters for an hour (a three-node 1.30 cluster plus older versions) to break and fix | **Free** · KodeKloud account | L1–L3 · Junior–Senior | [Kubernetes](31-learn-kubernetes.md), [Docker & K8s incidents](26-playbook-containers-k8s.md) |
| [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way) | Build a cluster by hand: certificates, etcd, control plane, workers, pod routes | **Free** · needs four ARM64 or AMD64 machines or VMs | L2–L3 · Mid–Senior | [Kubernetes](31-learn-kubernetes.md) |
| [CKAD exercises](https://github.com/dgkanatsios/CKAD-exercises) | Short `kubectl` tasks grouped by exam domain, with hidden solutions, for imperative speed | **Free** | L1–L2 · Junior–Mid | [Kubernetes](31-learn-kubernetes.md) |
| [Network Policy Editor](https://editor.networkpolicy.io/) | Draw which pods may talk to which and read the NetworkPolicy YAML it produces | **Free** | L2 · Mid | [Kubernetes](31-learn-kubernetes.md) |
| [KubeInvaders](https://github.com/lucky-sideburn/kubeinvaders) | Space Invaders where every alien is a pod or a node: shoot them and watch the cluster recover | **Free** · open source; run it on a lab cluster | L2–L3 · Mid–Senior | [Docker & K8s incidents](26-playbook-containers-k8s.md) |
| [Kubernetes Goat](https://madhuakula.com/kubernetes-goat/) | An intentionally vulnerable cluster: learn each misconfiguration, then how to detect and prevent it | **Free** · open source; lab cluster only | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md) |
| [EKS Cluster Games](https://eksclustergames.com/) | A browser CTF that starts inside a low-privileged EKS pod and walks through Kubernetes and AWS misconfigurations | **Free** · **unreachable on 7 Nov 2026**: the domain has no DNS address records, though Wiz still links it and no retirement notice was found; re-check before relying on it, and use the Wiz Cloud Security Championship meanwhile | L2–L3 · Mid–Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Security](37-learn-security-devsecops.md) |
| [K8s Games](https://k8sgames.com/) | A 3D cluster simulator: a 20-level campaign, Chaos Mode, ten timed outage challenges, a scored sandbox and a `kubectl` bar | **Free** · open source, no sign-up · runs in the browser (a simulated cluster) · checked 7 Nov 2026 | L0–L2 · Fresher–Mid | [Kubernetes](31-learn-kubernetes.md), [Docker & K8s incidents](26-playbook-containers-k8s.md) |
| [Isovalent labs](https://isovalent.com/resource-library/labs/) | Cilium on a real cluster: [install it where no CNI exists](https://isovalent.com/labs/cilium-getting-started/), move from L3 to L7 policy, publish a path with the Gateway API and pass an exam that asks you to fix an HTTPRoute; also Tetragon, LB IPAM and packet capture | **Free** · two labs are Enterprise-only; a name and email form is likely · runs in the browser (an Instruqt environment for 30–60 minutes) · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Kubernetes problems](46-problems-kubernetes.md), [Traefik](43-traefik-and-reverse-proxies.md) |
| [Meshery Playground](https://play.meshery.io) | Live Kubernetes clusters with CNCF projects installed, for traffic splitting and circuit breaking | **Free** · named account · runs in the browser on clusters that reset daily · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Kubernetes](31-learn-kubernetes.md) |
| [Helm Playground](https://helm-playground.com/) | Render Helm templates against values to debug template errors before `helm install` | **Free** · no sign-up · runs in the browser; the Helm version is not stated · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Kubernetes problems](46-problems-kubernetes.md) |
| [Wiz Cloud Security Championship](https://www.cloudsecuritychampionship.com/) | Twelve expert-level challenges from 2025–26, 11 still open: Kubernetes privilege escalation ("Game of Pods"), container escape ("Contain Me If You Can"), Terraform automation ("State of Affairs"), restricted Kubernetes networking, S3 and Azure AD | **Free** as far as shown: no price appears; hints cost points · log in or register · runs in a vendor-provided environment · checked 7 Nov 2026 | L3–L4 · Senior–Lead | [Kubernetes problems](46-problems-kubernetes.md), [Security](37-learn-security-devsecops.md) |
| [Chad Crowell's CKA and CKAD scenarios](https://killercoda.com/chadmcrowell) | About 120 scenarios on a real cluster, such as [Troubleshoot a NotReady Node](https://killercoda.com/chadmcrowell/course/cka/node-notready), kubelet status, a stuck PVC, kubeadm upgrades and PKI | **Free** · free Killercoda account · runs in the browser · checked 9 Nov 2026 | L2–L3 · Mid–Senior | [Kubernetes](31-learn-kubernetes.md), [Kubernetes problems](46-problems-kubernetes.md) |
| [CNPE exam scenarios (Saiyam Pathak)](https://killercoda.com/saiyampathak/course/cnpe) | 28 platform scenarios: Argo CD and Rollouts, OpenCost rightsizing, Kyverno with Cosign, Gatekeeper, a broken stack to repair and a [Flux HelmRelease](https://killercoda.com/saiyampathak/course/cnpe/28-flux-gitops-podinfo), the first free browser Flux practice | **Free** · free Killercoda account, or kind locally · checked 9 Nov 2026 | L3–L4 · Senior–Lead | [Kubernetes](31-learn-kubernetes.md), [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [DevOps with Kubernetes (University of Helsinki)](https://devopswithkubernetes.com/) | A graded MOOC: k3d on your machine, then GKE, GitOps and monitoring | **Free** · mooc.fi account · throwaway VM; the GKE part uses your own Google Cloud account, which can bill you · checked 9 Nov 2026 | L2–L3 · Mid–Senior | [Kubernetes](31-learn-kubernetes.md) |
| [40 Days of Kubernetes](https://github.com/piyushsachdeva/CKA-2024) | Piyush Sachdeva's CKA video series with a daily assignment, from Pods to kubeadm | **Free** · YouTube and a throwaway cluster · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Kubernetes](31-learn-kubernetes.md) |
| [Robusta Kubernetes demos](https://github.com/robusta-dev/kubernetes-demos), [Troubleshoot Kubernetes like a pro](https://github.com/vellankikoti/troubleshoot-kubernetes-like-a-pro) and [Kubernetes Troubleshooting Lab](https://github.com/Saif-hadd/Kubernetes-Troubleshooting-Lab) | Break-fix collections for your own throwaway cluster: one `kubectl apply` per failure (OOMKilled, CrashLoopBackOff, Pending), 35 scripted scenarios, and 15 scenarios with an RCA template | **Free** · open source · kind or Minikube on a throwaway VM · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Kubernetes problems](46-problems-kubernetes.md) |
| [Sachin's free CKA mock course](https://killercoda.com/sachin/course/CKA) | About 80 exam-style tasks on real clusters, a quarter of them troubleshooting: NotReady nodes, a broken kubelet, etcd backup and restore, upgrades, PV and PVC, NetworkPolicy, CoreDNS. The free replacement for the Killer Shell CKA set, which moved to a paid course | **Free** · free Killercoda account · checked 9 Nov 2026 | L2–L3 · Mid–Senior | [Kubernetes](31-learn-kubernetes.md), [Kubernetes problems](46-problems-kubernetes.md) |
| [iximiuz Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes) | Ticket-like problems: pods that will not schedule, a readiness probe stuck at 0/1, a NotReady node after a kubelet config error, a Traefik Ingress moved to the Gateway API; plus a [K3s playground](https://labs.iximiuz.com/playgrounds/k3s) | **Freemium** · many challenges run on the free plan | L1–L3 · Junior–Senior | [Kubernetes](31-learn-kubernetes.md), [Traefik](43-traefik-and-reverse-proxies.md) |
| [killer.sh](https://killer.sh/) | Exam simulators for CKA, CKAD, CKS, LFCS and CNPE: two environments of scenarios with detailed solutions | **Paid** · two sessions come with a CKA, CKAD or CKS exam purchase; otherwise $39.99 for two ([pricing](https://killer.sh/pricing)) | L2–L3 · Mid–Senior | [Kubernetes](31-learn-kubernetes.md) |

**Free-only path:** Killercoda's free CKA scenarios and the free iximiuz challenges for daily reps,
the CKAD exercises for `kubectl` speed, your kubeadm homelab for the
[twenty timed drills](31-learn-kubernetes.md#22-twenty-timed-break-and-fix-drills), and Kubernetes
the Hard Way once before the exam. KubeInvaders and Kubernetes Goat add self-healing and security
on top, both on a throwaway cluster. The free SadServers Kubernetes scenarios (section 1), the
Isovalent Cilium lab and K8s Games' Chaos Mode add variety without a cluster of your own.

### Best picks for Kubernetes

**Killercoda CKA scenarios (free).** Real clusters in the browser that start in seconds, with free
scenario sets from several community authors that cover the CKA topics. First: pick one set and do
one scenario each weekday against the clock, alternating with your homelab drills. Killercoda's own
CKA Scenario Course sits in the paid COURSE plan; skip it if you already use KodeKloud's CKA course.

**Kubernetes the Hard Way (free).** Do it once, slowly, on four homelab VMs. Every certificate and
systemd unit you write by hand is something you will recognise later when kubelet or etcd breaks in
a kubeadm cluster. First: read the prerequisites and build the four machines, and plan a whole
weekend for it.

**iximiuz Labs (freemium).** The Kubernetes challenges look like real tickets, including CKA-style
ones and one that moves a Traefik Ingress to the Gateway API, which matters for your Traefik work.
First: the challenge about recovering a NotReady node after a kubelet configuration error, with a
20-minute timer, then compare your steps with
[The troubleshooting method](31-learn-kubernetes.md#20-the-troubleshooting-method).

**Isovalent "Getting Started with Cilium" (free).** The bridge from Traefik labels and a kubeadm
cluster to cloud-native networking. You install a CNI on a cluster that has none, which is the
"node NotReady, network plugin not ready" state from the CKA, then write policy and Gateway API
routes. First: the getting-started lab and its exam, where you diagnose and fix an HTTPRoute that
does not match the expected request.

**K8s Games (free).** A simulation, not a real cluster, so treat it as L0–L2 warm-up. First: the
campaign to learn the objects, then one Chaos Mode run a week, naming the failing object before
you fix it.

**Wiz Cloud Security Championship (free, as far as shown).** The L3–L4 stretch, and the stand-in
for EKS Cluster Games while that domain is unreachable. Wiz's K8s LAN Party had the same DNS
outage on 7 Nov 2026. First: "Game of Pods", then write down which RBAC rule would have stopped
each step.

**killer.sh (paid, but included with the exam).** Harder than the real exam on purpose. First: do
nothing yet. Use the first included session two to three weeks before the exam, review every
solution even for questions you got right, and keep the second session for the final week. The
[CKA exam strategy](31-learn-kubernetes.md#21-cka-exam-strategy) section explains how to use the
time.

---

## 7. Cloud and AWS

You work on AWS next to on-prem, so the cloud practice here is mostly AWS. The focus is IAM and
security mistakes, because those are what hurt in production. Two rules: practise in a separate
account with a budget alarm, and delete everything the same day. Better still, start in accounts
the vendor owns, which cannot bill you: the Cost column says where each lab runs.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [flAWS](http://flaws.cloud/) | Six levels of classic AWS mistakes: open S3 buckets, leaked keys, the instance metadata service | **Free** | L1–L2 · Junior–Mid | [Cloud & AWS](36-learn-cloud-aws.md), [AWS commands](16-aws-cloud.md) |
| [flAWS2](http://flaws2.cloud/) | An attacker path and a defender path; the defender path is incident response on real CloudTrail logs | **Free** | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md), [Cloud & AWS](36-learn-cloud-aws.md) |
| [The Big IAM Challenge](https://bigiamchallenge.com/) | Browser puzzles about IAM and resource policies that allow more than their authors meant | **Free** · **unreachable on 7 Nov 2026**: no DNS address records and no retirement notice; re-check before relying on it, and meanwhile read policies in the Pwned Labs free labs or try the Wiz Cloud Security Championship (section 6) | L2–L3 · Mid–Senior | [Cloud & AWS](36-learn-cloud-aws.md) |
| [AWS Educate](https://aws.amazon.com/education/awseducate/) | Console labs on IAM, VPC, EC2, S3, RDS and a static S3 website, with unlimited attempts inside a time window (lab list from a 2022 AWS post) | **Free** · email sign-up, age 13+, no Amazon account, "no credit card needed" · runs in a vendor-owned AWS sandbox · checked 7 Nov 2026 | L0 · Fresher | [Cloud & AWS](36-learn-cloud-aws.md), [AWS commands](16-aws-cloud.md) |
| [Microsoft Applied Skills](https://learn.microsoft.com/en-us/credentials/applied-skills/) | Timed 30- or 45-minute tasks in a real Azure portal for Azure administration, networking, Windows Server hybrid, security and DevOps; no save and resume, and some labs were reported unavailable | **Free** according to community write-ups only; Microsoft's pages do not say so · Microsoft Learn profile · runs in a lab VM connected to an [Azure environment the lab supplies](https://learn.microsoft.com/en-us/credentials/support/assessment-lab-frequently-asked-questions) · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [On-prem vs cloud](55-paths-onprem-vs-cloud.md), [Cloud & AWS](36-learn-cloud-aws.md) |
| [Cloud Resume Challenge](https://cloudresumechallenge.dev/) | A 16-step project: a resume site with DNS, HTTPS, a serverless visitor counter, infrastructure as code and CI/CD | **Free** challenge · the guidebook is sold separately; AWS usage is billed | L1–L2 · Junior–Mid | [Cloud & AWS](36-learn-cloud-aws.md), [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [AWS Workshops](https://builder.aws.com/build/workshops) | AWS's catalogue of step-by-step workshops, now part of AWS Builder Center | **Free** content · since 8 July 2026 a [free Builder Center sandbox](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/) runs selected workshops in a vendor-owned account: no AWS account or card, 8 hours, once a week, resets on Sunday; every other workshop runs in YOUR AWS account and is billed · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Cloud & AWS](36-learn-cloud-aws.md) |
| [CloudGoat](https://github.com/RhinoSecurityLabs/cloudgoat) | Vulnerable-by-design AWS scenarios, deployed with Terraform, to learn misconfigurations and their fixes | **Free** · open source; AWS usage is billed; separate account only | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md), [Cloud & IaC problems](50-problems-cloud-iac-proxmox.md) |
| [CloudFoxable](https://cloudfoxable.bishopfox.com/) | 18 gamified AWS attack-path flags deployed with Terraform; the README separates "always on" low-cost flags from ones that cost money | **Free** · open source · runs in YOUR AWS account (can bill you); never a production, shared or work account · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md), [Cloud & AWS](36-learn-cloud-aws.md) |
| [IAM Vulnerable](https://github.com/BishopFox/iam-vulnerable) | 31 IAM privilege-escalation paths to find and then close | **Free** · open source; the default set costs nothing, optional modules about $4.50 a month (EC2) or about $4 an hour (Glue) · runs in YOUR AWS account (can bill you) · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Security](37-learn-security-devsecops.md) |
| [Azure Monitor Lab](https://github.com/Azure-Samples/azure-monitor-lab) | A Microsoft sample: deploy one resource group with Bicep or Terraform, then break and restore 69 monitoring scenarios | **Free** code · your Azure subscription pays for what it deploys: budget alarm first, delete the same day · checked 9 Nov 2026 | L3 · Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Observability toolbox](49-observability-stack-problems.md) |
| [Pwned Labs](https://pwnedlabs.io/explore) | AWS, Azure, GCP, Kubernetes, CI/CD and hybrid attack-and-defence scenarios in real cloud accounts | **Freemium** · over 30 of 90 scenarios free with a free account; paid prices not readable · runs in a vendor-owned cloud account · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Security](37-learn-security-devsecops.md) |
| [Cybr hands-on labs](https://cybr.com/hands-on-labs/) | AWS and Azure red- and blue-team labs, cleaned up automatically to prevent surprise bills | **Freemium** · 33 of 123 labs free; free account, no credit card · runs in a vendor-owned AWS or Azure account · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Security](37-learn-security-devsecops.md) |
| [AWS Cloud Quest](https://skillbuilder.aws/cloudquest) | A role-playing game with an AI "customer" and builds in live AWS environments, rebuilt and moved into Skill Builder on 11 August 2026 | **Freemium** · AWS's [Cloud Quest page](https://aws.amazon.com/training/digital/aws-cloud-quest/) says free accounts get "limited access" and every role needs an Individual or Team subscription; the two free roles listed on 3 Oct 2026 now appear only in a search snippet, so check while signed in · runs in a vendor-owned account · checked 7 Nov 2026 | L0–L1 · Fresher–Junior | [Cloud & AWS](36-learn-cloud-aws.md) |
| [AWS Skill Builder](https://skillbuilder.aws/) | Free digital courses; the subscription adds hands-on labs and full Cloud Quest | **Freemium** · free courses; Individual subscription billed monthly or yearly · checked 7 Nov 2026 | L0–L3 · Fresher–Senior | [Cloud & AWS](36-learn-cloud-aws.md) |
| [Google Skills](https://www.skills.google/) | Google Cloud labs in temporary projects, skill badges and the Arcade programme (formerly Cloud Skills Boost) | **Freemium** · a free monthly allowance of credits (35 shown); paid credits or Innovators Plus at $299 a year; the Arcade continues, but [since April 2026](https://discuss.google.dev/t/what-s-changing-in-the-google-skills-arcade-from-april-2026/345557) Arcade Sprints and the Certification Zone are gone, games have fewer labs and every game is worth one point · checked 7 Nov 2026 | L0–L2 · Fresher–Mid | [Cloud & AWS](36-learn-cloud-aws.md) |
| [LocalStack](https://www.localstack.cloud/pricing) | AWS services emulated on your own machine, for CLI and Terraform practice without a bill | **Freemium** · the Hobby plan is free for non-commercial use only and needs an account and auth token; the free Community edition no longer receives updates; paid plans from $39 a month billed yearly · runs in a throwaway VM or Codespace · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Cloud & IaC problems](50-problems-cloud-iac-proxmox.md) |

**Free-only path:** AWS Educate's console labs, flAWS and then the flAWS2 defender path, the free
Pwned Labs and Cybr labs, one Builder Center sandbox workshop a week, and the HashiCorp Terraform
sandbox (section 8) or LocalStack for Terraform practice. The Big IAM Challenge belongs here again
once its domain answers. Touch your own account only for the Cloud Resume Challenge and the
own-account goats, and only after the budget alarm is in place.

### Best picks for cloud

**AWS Educate, then the Builder Center sandbox (free).** Both run in accounts AWS owns, so nothing
can bill you. Educate gives a fresher guided console labs on IAM, VPC, EC2 and S3. The Builder
Center sandbox gives you a ready-made account for 8 hours once a week, enough for one real
workshop. First: the Educate VPC and IAM labs, then one sandbox workshop on a Saturday, writing
down every resource it creates so you could delete it by hand. Cloud Quest's free access is now
limited, so use it only if you already pay for Skill Builder.

**Pwned Labs and Cybr (free labs).** Real cloud accounts that the vendor provisions and, at Cybr,
cleans up, which makes them the safest real-cloud practice found. First: one free Pwned Labs AWS
lab and one free Cybr blue-team lab. For each, write the IAM change that would have stopped the
attack.

**Microsoft Applied Skills (free per community reports).** Now that Learn sandboxes are retired,
this was the only no-card way into a real Azure portal the November sweep found for
non-students. Students can add Azure for Students: $100 of credit for 12 months, "no credit card
required". First: one timed Azure administrator task, which maps onto
[On-prem vs cloud](55-paths-onprem-vs-cloud.md).

**flAWS and flAWS2 (free).** Created by Scott Piper of Summit Route, they teach the AWS mistakes
that end up in the news. Do flAWS first, then the flAWS2 defender path, where you are the incident
responder working through CloudTrail logs from an attack with `jq` and Athena. First: flAWS level 1.
For every level, write down which IAM or bucket setting would have prevented it.

**The Big IAM Challenge (free; unreachable on 7 Nov 2026).** Reading IAM policies is a senior
skill that looks like a junior one. The domain had no DNS address records on 7 November 2026, so
re-check it first; until it answers, use the Pwned Labs free labs or the Wiz Cloud Security
Championship. First: solve one policy a day and explain in one sentence why it grants too much.
Then read your own account's policies with the same eye, using [Cloud & AWS](36-learn-cloud-aws.md).

**LocalStack (freemium).** Terraform practice without a bill or a risk to a real account. The free
Hobby plan now needs an account and an auth token and is for non-commercial use only, and the old
Community image no longer gets updates; the HashiCorp Terraform sandbox (section 8) has LocalStack
ready in the browser. First: point the AWS CLI and a Terraform provider at it, create and destroy
an S3 bucket and a queue, then repeat the Terraform exercise from
[CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) against it.

---

## 8. IaC and CI/CD

Your stack is GitLab CI with Harbor, with Ansible and Terraform next to it. Practise pipelines on
your own GitLab first, because that is where free practice is closest to your job, then borrow
structured courses from HashiCorp, Red Hat and GitHub.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [GitLab CI/CD tutorials](https://docs.gitlab.com/ci/quick_start/) | Official step-by-step tutorials, starting with your first pipeline; the [tutorials index](https://docs.gitlab.com/tutorials/) has more | **Free** · on your own GitLab or GitLab.com | L0–L2 · Fresher–Mid | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [GitLab University](https://university.gitlab.com/) | Free self-paced GitLab courses and learning paths, including a [CI/CD course](https://university.gitlab.com/courses/gitlab-cicd) | **Free** courses · certification exams are paid | L0–L2 · Fresher–Mid | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [HashiCorp Terraform tutorials](https://developer.hashicorp.com/terraform/tutorials) | Get-started tracks per provider (AWS, Docker, Azure, GCP and more), state, modules and certification prep | **Free** | L1–L3 · Junior–Senior | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Cloud & IaC problems](50-problems-cloud-iac-proxmox.md) |
| [Red Hat interactive labs](https://www.redhat.com/en/interactive-labs) | Browser labs for Ansible Automation Platform, RHEL and OpenShift, about an hour each | **Free** · Red Hat account | L1–L2 · Junior–Mid | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [Hello GitHub Actions](https://github.com/skills/hello-github-actions) | A first workflow in under 30 minutes inside your own repository; [Publish Docker images](https://github.com/skills/publish-docker-images) builds and pushes an image | **Free** · GitHub account | L0–L1 · Fresher–Junior | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |
| [KodeKloud CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd) | Jenkins, Gitea, Docker and a one-node Kubernetes cluster for an hour; the [Ansible playground](https://kodekloud.com/playgrounds/playground-ansible) gives you Ansible and two target servers | **Free** · KodeKloud account | L1–L2 · Junior–Mid | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [KodeKloud free challenges](https://kodekloud.com/free-courses) | Timed Terraform, Linux, Kubernetes and CKS challenges that grade a finished build | **Free** · KodeKloud account | L1–L3 · Junior–Senior | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [HashiCorp sandboxes](https://developer.hashicorp.com/terraform/sandbox) | Terraform with Docker, LocalStack and `awslocal` already installed; sibling sandboxes for Vault, Consul, Nomad and Boundary | **Free** as far as shown (no price stated) · runs in the browser for up to an hour, nothing saved; never point it at a real AWS account, because the timer does not clean that up · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Cloud & IaC problems](50-problems-cloud-iac-proxmox.md) |
| [GitHub Actions Goat](https://github.com/step-security/github-actions-goat) | CI supply-chain hardening: egress filtering, tamper detection, audit logs, long-lived credentials, untrusted actions and self-hosted runners | **Free** · open source; fork it with a GitHub account · runs on GitHub-hosted runners in your fork, no cloud bill · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), [Security](37-learn-security-devsecops.md) |
| [CI/CD Goat](https://github.com/cider-security-research/cicd-goat) | 11 challenges on the OWASP Top 10 CI/CD risks across Gitea, Jenkins, GitLab with a runner, LocalStack and a "prod" box, started with `docker compose` | **Free** · open source, but not updated since July 2024, so expect to fix things before it starts · runs in a throwaway VM; a 2-core Codespace may lack the memory for GitLab · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), [Security](37-learn-security-devsecops.md) |
| [Argo CD public demo](https://cd.apps.argoproj.io/) | The project's own live Argo CD: read sync and health status, diffs and history on apps that are Degraded, Missing or OutOfSync | **Free** · read-only, no sign-up · runs in the browser · checked 9 Nov 2026 | L1–L2 · Junior–Mid | [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) |

**Free-only path:** the GitLab tutorials on your own GitLab with a runner and Harbor, the HashiCorp
get-started track for Docker and then AWS (or the HashiCorp sandbox with LocalStack), one Red Hat
Ansible lab followed by the same playbook in the KodeKloud Ansible playground, and the KodeKloud
Terraform Challenges as the exit check. GitHub Actions Goat and CI/CD Goat add pipeline security.

### Best picks for IaC and CI/CD

**GitLab CI/CD tutorials (free).** Nothing beats practising on the GitLab you actually run. First:
"Create and run your first GitLab CI/CD pipeline" on a test project, then add a job that builds an
image and pushes it to Harbor, as in [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md).
Then break it on purpose: remove your private CA from the runner and read the x509 error it
produces, so that you recognise it at once next time.

**HashiCorp Terraform tutorials (free).** The official tracks are short and current. First: the
Docker get-started collection, which needs no cloud account, then the AWS one with a budget alarm.
Run `terraform plan` before every apply and read it like a change request.

**Red Hat interactive labs (free).** A browser lab with Ansible already installed and a guided
script, about an hour each. First: one Ansible lab, then write the same playbook against the two
target servers in the KodeKloud Ansible playground, and finally against two homelab VMs.

**KodeKloud free challenges (free).** Use the Terraform Challenges as a test, not a lesson: you get
a diagram and must build it. First: try one after the HashiCorp track; if you need hints, go back
to the tutorial for that part.

**CI/CD Goat (free, stale).** The closest free match to a GitLab-plus-runner setup under attack.
Its age is part of the exercise: getting it to start on a throwaway VM is break-fix practice in
itself. First: the first two challenges, then check whether your own GitLab runners allow the same
poisoned pipeline, using [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md).

---

## 9. Observability

Dashboards are easy to look at and hard to read. Practise on public demos with real data first,
then on your own stack from [Observability toolbox](49-observability-stack-problems.md).

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Grafana Play](https://play.grafana.org/) | A public Grafana with many example dashboards and live data sources; explore and edit panels without signing in | **Free** | L0–L2 · Fresher–Mid | [Performance](32-learn-performance-observability.md), [Observability toolbox](49-observability-stack-problems.md) |
| [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) | The official tutorial: explore metrics and logs, build a dashboard, add annotations and alert rules, with a sample app in Docker Compose or a Killercoda sandbox | **Free** | L1 · Junior | [Observability toolbox](49-observability-stack-problems.md) |
| [PromQL cheat sheet](https://promlabs.com/promql-cheat-sheet/) | Common PromQL patterns, each with a link that opens it in [PromLens](https://demo.promlens.com/) to run and explain the query | **Free** | L1–L2 · Junior–Mid | [Performance](32-learn-performance-observability.md) |
| [PromLabs demo Prometheus](https://demo.promlabs.com/) | A public Prometheus server to run your own queries against | **Free** | L1–L2 · Junior–Mid | [Performance](32-learn-performance-observability.md) |
| [OpenTelemetry demo](https://opentelemetry.io/docs/demo/) | The Astronomy Shop microservices with traces, metrics and logs, plus feature flags that switch on failure scenarios | **Free** · run it on your Docker or Kubernetes lab | L2–L3 · Mid–Senior | [Performance](32-learn-performance-observability.md), [Observability toolbox](49-observability-stack-problems.md) |
| [KodeKloud Prometheus & Grafana playground](https://kodekloud.com/playgrounds/playground-prometheus-grafana) | Prometheus and Grafana already running, with sample dashboards, for an hour | **Free** · KodeKloud account | L1–L2 · Junior–Mid | [Performance](32-learn-performance-observability.md) |
| [Prometheus demo site](https://demo.prometheus.io) | A live Prometheus run by the Prometheus project, with Alertmanager, node_exporter and Grafana beside it | **Free** · no sign-up · runs in the browser · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Performance](32-learn-performance-observability.md), [Observability toolbox](49-observability-stack-problems.md) |
| [Grafana LogQL simulator](https://grafana.com/docs/loki/latest/query/analyzer/) | LogQL line filters, logfmt, json, pattern and regex parsers, label filters and `line_format` on sample or pasted log lines | **Free** · no sign-up · runs in the browser; the stream selector is fixed and metric queries are not supported · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Observability toolbox](49-observability-stack-problems.md) |
| [VRL Playground](https://playground.vrl.dev/) | Vector Remap Language programs run against sample events, with shareable links | **Free** · no sign-up · runs in the browser · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Observability toolbox](49-observability-stack-problems.md) |
| [OTTL Playground](https://ottl.run) | OpenTelemetry Collector transformation statements tested on sample telemetry | **Free** · no sign-up · runs in the browser; use the bare domain, because the `www.` host failed · checked 7 Nov 2026 | L2 · Mid | [Observability toolbox](49-observability-stack-problems.md) |
| [Getting Started with OpenTelemetry (LFS148)](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/) | The Linux Foundation's 11-chapter course, 8–10 hours, with OpenTelemetry labs and a badge | **Free** · Linux Foundation account; 90 days of access · runs in a GitHub Codespace (or a Dev Container on a lab VM) · checked 7 Nov 2026 | L1 · Junior | [Performance](32-learn-performance-observability.md), [Observability toolbox](49-observability-stack-problems.md) |
| [Grafana Quest World](https://killercoda.com/grafana-labs/course/workshops/adventure) | A text adventure on the Grafana stack: every move becomes metrics, logs and a trace, and the quests are solved with queries | **Free** · free Killercoda account, or Docker Compose locally · checked 9 Nov 2026 | L0–L1 · Fresher–Junior | [Performance & observability](32-learn-performance-observability.md) |
| [Netdata demo space](https://app.netdata.cloud/spaces/netdata-demo) | Per-second metrics from live demo nodes (Apache, NGINX, PostgreSQL, Redis): read CPU, disk, network and pressure like the 60-second checklist | **Free** · no sign-up for the demo; some functions ask you to sign in · checked 9 Nov 2026 | L1–L2 · Junior–Mid | [Why is it slow?](23-playbook-slow-system.md), [Performance & observability](32-learn-performance-observability.md) |
| [Datadog Learning Center](https://learn.datadoghq.com/) | Courses on real cloud instances with a Datadog account made for you: the Agent, monitors, dashboards, APM, logs and Kubernetes | **Free** · free account, no card mentioned · 30-day enrolment, renewable · vendor account · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Observability toolbox](49-observability-stack-problems.md) |
| [Uptime Kuma public demo](https://demo.kuma.pet/start-demo) | A throwaway Uptime Kuma per visitor: HTTP, TCP and DNS monitors, notifications and a status page | **Free** · no sign-up · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Observability toolbox](49-observability-stack-problems.md) |
| [Alertmanager routing tree editor](https://prometheus.io/webtools/alerting/routing-tree-editor/) | Paste an `alertmanager.yml`, see the route tree and test which receiver a label set reaches | **Free** · official tool · runs in your browser · checked 9 Nov 2026 | L3–L4 · Senior–Lead | [Performance & observability](32-learn-performance-observability.md) |
| [PromLabs PromQL training](https://promlabs.com/promql-training/) | Live training by Prometheus co-founder Julius Volz: two three-hour sessions with exercises | **Paid** · €500 per participant, booked for a group | L2–L3 · Mid–Senior | [Observability toolbox](49-observability-stack-problems.md) |

**Free-only path:** Grafana Play for reading dashboards, the PromQL cheat sheet against the PromLabs
demo server, alerts on the Prometheus demo's Alertmanager, the Grafana fundamentals tutorial, the
LogQL simulator for Loki queries, then the OpenTelemetry demo on your lab with one failure flag at
a time.

### Best picks for observability

**Grafana Play (free).** You can open any panel and see how it was built. First: pick a dashboard,
open one panel in edit mode and read its query. Change the time range or the aggregation, predict
the new graph, then apply and check whether you were right.

**PromQL cheat sheet with PromLens (free).** The fastest way to learn PromQL by running it. First:
open the `rate`, `sum by` and `histogram_quantile` examples in PromLens and read its explanation of
each step. Then write the same three queries against `node_exporter` on your own Prometheus, using
[Performance](32-learn-performance-observability.md).

**OpenTelemetry demo (free).** A whole shop of instrumented services that you can break on purpose.
First: run it with Docker Compose on a lab VM, ask a friend (or a script) to switch on one failure
flag, and find the cause from traces and metrics before you look at which flag was set.

**Prometheus demo and the pipeline playgrounds (free).** The Prometheus project's own demo adds a
live Alertmanager and node_exporter to what PromLabs offers, so you can read real alert states.
The LogQL, VRL and OTTL playgrounds cover the log and telemetry transforms that are hardest to try
on a production stack. First: open the demo's alerts page, pick one rule and say when it would
fire, then
parse one of your own (sanitised) access-log lines in the LogQL simulator.

---

## 10. SRE, incidents and DevOps culture

From mid-level up, the hard part of an incident is coordination more than commands: who leads, what
you say, what you mitigate first and what you learn afterwards. These games and drills train that,
and the reading lists show how other teams failed.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Wheel of Misfortune](https://dastergon.github.io/wheel-of-misfortune/) | Disaster role-playing: a game master replays an outage and the on-call engineer talks through the response; this web tool picks scenarios and loads your own ([repository](https://github.com/dastergon/wheel-of-misfortune)) | **Free** · open source · the github.io tool works; the repository's homepage link now returns 404, so use this one · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Site down](25-playbook-site-down.md) |
| [DevOps Dream](https://devops.games/) | A browser strategy game: you play the CIO, pick initiatives and react to events while four delivery metrics based on DORA research move | **Free** | L3–L4 · Senior–Lead | [Senior architecture](39-learn-senior-architecture.md), [Career ladder](40-career-ladder.md) |
| [DORA Quick Check](https://dora.dev/quickcheck/) | Five questions that place your team's delivery performance against DORA benchmarks | **Free** · answers are not stored | L3–L4 · Senior–Lead | [Senior architecture](39-learn-senior-architecture.md) |
| [Backdoors & Breaches](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/) | An incident-response card game for tabletop exercises with your security colleagues | **Free** to play online · physical decks are sold · the old /projects/ address now redirects here · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Wazuh](48-wazuh-and-security-tools.md), [Security](37-learn-security-devsecops.md) |
| [Dan Luu's post-mortems](https://github.com/danluu/post-mortems) | Short summaries of public postmortems grouped by cause: config errors, hardware, conflicts, time, databases | **Free** | L1–L4 · Junior–Lead | [Senior architecture](39-learn-senior-architecture.md) |
| [Kubernetes Failure Stories](https://k8s.af/) | Public Kubernetes incident write-ups and conference talks | **Free** | L2–L4 · Mid–Lead | [Docker & K8s incidents](26-playbook-containers-k8s.md) |
| [DevOps Daily games](https://devops-daily.com/games) | 62 simulators: Kubernetes RBAC, CNI, scheduler and terminal; a Docker terminal; GitOps and deployment strategies; Terraform state puzzles; Incident Commander; a daily on-call incident; PromQL; DNS, TCP/UDP, TLS and AWS VPC | **Free** · no sign-up seen; an unexplained "Pro" area exists · runs in the browser (simulations, not real systems) · checked 7 Nov 2026 | L0–L2 · Fresher–Mid | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Kubernetes](31-learn-kubernetes.md) |
| [Server Survival](https://pshenok.github.io/server-survival/) | A cloud-architecture tower defence: place WAFs, load balancers, queues, caches, replicas and GeoDNS against traffic and DDoS waves on a budget | **Free** · open source, no account; use this original, not the copies · runs in the browser · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Senior architecture](39-learn-senior-architecture.md), [Why is it slow?](23-playbook-slow-system.md) |
| [SDPD](https://sdpd.live/) | Diagnose 33 distributed-system failures, such as split brain, stale reads, a thundering herd and hot partitions, plus a chaos simulator | **Free** · open source, no sign-up · runs in the browser · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Senior architecture](39-learn-senior-architecture.md) |
| [System Design Sim](https://systemdesignsim.com/playground) | Build on real AWS, Azure or GCP instance sizes while p99 latency, errors and the monthly bill update; flash-sale challenges up to 20,000 requests a second | **Free** · no account · runs in the browser · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Senior architecture](39-learn-senior-architecture.md), [On-prem vs cloud](55-paths-onprem-vs-cloud.md) |
| [The Incident Challenge](https://theincidentchallenge.com/) | Live rounds every other Monday with a 24-hour window: compare staging with production logs, requests, services and config to find the cause, ranked by solve time | **Free** as far as shown (no price) · Google or LinkedIn sign-in, even for the demo · runs in the browser · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Site down](25-playbook-site-down.md), [Why is it slow?](23-playbook-slow-system.md) |
| [PagerDuty Incident Response](https://response.pagerduty.com/) | Role guides for incident commander, deputy, scribe, subject-matter expert and liaisons, severity levels, a postmortem template and an open [training course](https://response.pagerduty.com/training/courses/incident_response/) | **Free** · no sign-up · documentation to read and adapt · checked 7 Nov 2026 | L1–L4 · Junior–Lead | [DevOps day to day](52-devops-day-to-day.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [The VOID](https://www.thevoid.community/) | Search over 10,000 public incident reports by impact type in its [database](https://www.thevoid.community/database) | **Free** to browse · no sign-up · runs in the browser · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Senior architecture](39-learn-senior-architecture.md) |
| [Defensomania](https://karneades.github.io/Defensomania/play/) | An incident-response card game with a free online dealer, for security tabletop sessions | **Free** · open source, no sign-up · runs in the browser · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Wazuh](48-wazuh-and-security-tools.md), [Security](37-learn-security-devsecops.md) |
| [Backstage demo](https://demo.backstage.io/) | A public developer portal: find a service's owner, docs and templates in the catalog | **Free** · no sign-up · runs in the browser · checked 9 Nov 2026 | L2–L3 · Mid–Senior | [Senior: architecture & leadership](39-learn-senior-architecture.md) |
| [The Art of SLOs (Google)](https://sre.google/resources/practices-and-processes/art-of-slos/) | Google's workshop handbook: define SLIs and SLOs for an example service, then error budgets and burn-rate alerts | **Free** · run it with your team · checked 9 Nov 2026 | L4 · Lead | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [SysAdmin Simulator](https://sys-admin-simulator.com/practice/incident-response) | Live on-call practice with alerts, SLA timers and a real terminal (also in section 1) | **Freemium** · free account to start | L1–L3 · Junior–Senior | [Site down](25-playbook-site-down.md) |
| [Uptime Labs](https://uptimelabs.io/) | Incident simulations for teams that run on the vendor's systems, with time pressure and performance analytics | **Paid** · per-user team pricing; a free drill to try | L3–L4 · Senior–Lead | [Senior architecture](39-learn-senior-architecture.md) |

**Free-only path:** one Wheel of Misfortune session a month with a colleague (or alone, talking
out loud), one postmortem from Dan Luu's list, k8s.af or The VOID every Sunday, a round of The
Incident Challenge when one is live, and one game of DevOps Dream before you next argue for a
platform investment.

New in 2026, may change: three on-call games appeared in the autumn, weeks old when checked, with
few or no stars. [ON-CALL](https://oncall-simulator.vercel.app/) runs six incidents in one night
and grades your postmortem, [Pit Wall On-Call](https://pitwall.rafifdzaky.com/) gives a daily
incident with alerts, metrics and logs (it needs a 1024 px screen), and
[non-call](https://serum.sh/non-call/) is a terminal-style night of competing alerts. Try them,
but do not build a plan on them yet.

### Best picks for SRE and culture

**Wheel of Misfortune (free).** Google's SRE book describes it as
[disaster role-playing](https://sre.google/sre-book/accelerating-sre-on-call/): a game master
replays a real outage, the on-call engineer explains each step, and the team watches and learns.
First: write three scenarios from your own five-line notes (the Apache-on-443 case is a good one),
load them into the tool and run one in 30 minutes with a colleague. Google Cloud's
[write-up on mitigating incidents](https://cloud.google.com/blog/products/management-tools/shrinking-the-time-to-mitigate-production-incidents)
links a template for preparing sessions.

**DevOps Dream (free).** The game that started this module. It trains the L3 and L4 mindset: the
trade-offs between speed, stability and investment, scored on four delivery metrics drawn from the
2019 State of DevOps research. First: play one company size to the end. Then write down which
decisions moved deployment frequency and which moved the change failure rate, and take the DORA
Quick Check for your real team.

**Postmortem reading (free).** Every Sunday, read one postmortem and name the failing layer before
you reach the root-cause section. First: a config-error entry from Dan Luu's list, then a k8s.af
story about DNS or the CNI, and compare it with
[Docker & K8s incidents](26-playbook-containers-k8s.md).

**The Incident Challenge (free, as far as shown).** The only new game built as a real
investigation: you compare staging and production evidence until the difference explains the
outage. First: the demo, then one live round, and write the five-line note before reading how
others solved it.

**DevOps Daily games, Server Survival and SDPD (free).** DevOps Daily is a large set of
simulations, so place it at L0–L2 next to SysAdmin Simulator, not next to SadServers. Server
Survival and SDPD train architecture judgement rather than commands. First: one DevOps Daily
Kubernetes simulator, one Server Survival game to the end, and one SDPD failure whose name you did
not know.

**PagerDuty Incident Response (free).** The incident roles that the L3 and L4 exit tests assume,
written down and maintained. First: read the incident commander and scribe guides, then assign
those two roles at your next Wheel of Misfortune session.

**Uptime Labs (paid).** Worth it only when you lead a team that drills regularly. First: their free
drill, to see the format and borrow ideas for your own game days.

### Run a Wheel of Misfortune session

You can run this with two people and no budget. It is also the best preparation for the L4 game
day in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md#8-l4-exit-test-the-game-day).

1. **Pick a past incident with a known cause.** Strip names and real addresses, and write down the evidence in the order it appeared: alert, dashboards, logs, the change that caused it.
2. **Assign roles.** One game master who knows the story, one on-call engineer who does not, and optionally a scribe and observers.
3. **Play for 30 to 45 minutes.** The on-call engineer says what they would check; the game master answers only what that check would really show. No "you just know it" shortcuts.
4. **Debrief for 15 minutes.** What helped, what was missing (a runbook, an alert, access, a dashboard), and one action item with an owner.
5. **Save the scenario.** Add it to your Wheel of Misfortune list so the next person can play it.

---

## 11. Defensive security

Security practice here is defensive: detect, investigate and harden. You run Wazuh, CrowdSec and
Trivy, so the best free practice is to trigger events in your own lab and check that your tools
notice. Kubernetes Goat (section 6) and CloudGoat and the flAWS2 defender path (section 7) belong
here too.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [Wazuh proof-of-concept guide](https://documentation.wazuh.com/current/proof-of-concept-guide/index.html) | Official lab scenarios to trigger and detect: file integrity monitoring, brute force, Docker events, vulnerability detection, malicious commands and more | **Free** · your own lab | L1–L3 · Junior–Senior | [Wazuh](48-wazuh-and-security-tools.md) |
| [CyLab Security Academy](https://cylabacademy.org/) | Carnegie Mellon's free security practice, formerly picoCTF.org; the general-skills problems cover Linux and scripting | **Free** | L0–L1 · Fresher–Junior | [Security](37-learn-security-devsecops.md) |
| [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) | An intentionally insecure web shop to run in Docker behind your lab proxy and check what a WAF or CrowdSec catches | **Free** · open source; lab only | L2–L3 · Mid–Senior | [Traefik](43-traefik-and-reverse-proxies.md), [Security](37-learn-security-devsecops.md) |
| [OWASP WrongSecrets](https://wrongsecrets.herokuapp.com/) | 76 challenges on secrets that leak through code, configuration, container images and cloud setups | **Free** · open source, no sign-up; the hosted demo is "not always up" · the Docker challenges run in the browser on the hosted instance; the Kubernetes and Vault ones need a throwaway cluster, the cloud ones YOUR cloud account (can bill you) · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Security](37-learn-security-devsecops.md), [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | Browser labs in 31 web topics, including request smuggling, cache poisoning, Host-header attacks, SSRF, CORS, OAuth and JWT: the attacks your reverse proxy should stop | **Free** · account to save progress; Burp Community is enough · runs in the browser; run Burp in a throwaway VM · checked 7 Nov 2026 | L1–L3 · Junior–Senior | [Traefik](43-traefik-and-reverse-proxies.md), [Security](37-learn-security-devsecops.md) |
| [Wiz Cloud Hunting Games](https://www.cloudhuntinggames.com/) | An incident-response investigation of a fictional data-extortion case in the cloud | **Free** as far as shown (no price stated); sign-up terms not stated · runs in the browser · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md), [Wazuh](48-wazuh-and-security-tools.md) |
| [Stratus Red Team](https://github.com/DataDog/stratus-red-team) | Emulate real cloud attack techniques one at a time and check that your detections fire | **Free** · open source · runs in YOUR cloud account (can bill you); use a dedicated account · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Wazuh](48-wazuh-and-security-tools.md), [Security](37-learn-security-devsecops.md) |
| [CrowdSec Playground](https://playground.crowdsec.net/) | CrowdSec's grok debugger and pattern library: make a parser match your log line before you deploy it | **Free** · no sign-up · runs in your browser · checked 9 Nov 2026 | L2 · Mid | [Wazuh & security tools](48-wazuh-and-security-tools.md) |
| [OpenSearch Playground](https://playground.opensearch.org/) | Read-only OpenSearch Dashboards with sample logs: Discover, queries and visualisations, the same screens the Wazuh dashboard is built on | **Free** · anonymous, cannot save · checked 9 Nov 2026 | L1–L2 · Junior–Mid | [Wazuh & security tools](48-wazuh-and-security-tools.md) |
| [SANS Holiday Hack Challenge](https://www.sans.org/cyber-ranges/holiday-hack-challenge) | A yearly browser game with terminal challenges, including cloud and networking tracks; the 2025 game stays playable until the 2026 one opens in December | **Free** · free SANS account · checked 9 Nov 2026 | L1–L3 · Junior–Senior | [Security & DevSecOps](37-learn-security-devsecops.md) |
| [CTFtime upcoming events](https://ctftime.org/event/list/upcoming) | A calendar of free online CTFs; none is labelled DevOps, so pick ones with Linux, web or cloud categories | **Free** · each event has its own sign-up · checked 9 Nov 2026 | L2–L4 · Mid–Lead | [Security & DevSecOps](37-learn-security-devsecops.md) |
| [ControlPlane Kubernetes simulator](https://github.com/controlplaneio/simulator) | Builds a cluster in your AWS account and runs CTF scenarios that misconfigure it | **Free** code · your AWS account pays: dedicated account, budget alarm, destroy after each run · checked 9 Nov 2026 | L3–L4 · Senior–Lead | [Security & DevSecOps](37-learn-security-devsecops.md), [Kubernetes problems](46-problems-kubernetes.md) |
| [LetsDefend](https://letsdefend.io/) | A simulated SOC: alerts arrive in a SIEM and you investigate and close them | **Freemium** · free basic access; VIP plans are paid | L1–L2 · Junior–Mid | [Wazuh](48-wazuh-and-security-tools.md) |
| [Blue Team Labs Online](https://blueteamlabs.online/) | Defensive challenges with downloadable evidence (logs, captures, memory images, phishing mail) and hosted investigations | **Freemium** · free challenges; PRO £15 a month or £144 a year | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md) |
| [TryHackMe SOC Level 1](https://tryhackme.com/path/outline/soclevel1) | A guided SOC analyst path: alert triage, SIEM investigations, network and endpoint telemetry, reporting | **Paid** · TryHackMe has free rooms, but this path needs [Premium](https://tryhackme.com/pricing), billed monthly or yearly | L1–L2 · Junior–Mid | [Security](37-learn-security-devsecops.md), [Wazuh](48-wazuh-and-security-tools.md) |
| [HTB Academy SOC Analyst path](https://academy.hackthebox.com/path/preview/soc-analyst) | 15 modules: incident handling, SIEM, Splunk and Elastic hunting, Windows event logs, traffic analysis, IDS, YARA and Sigma | **Paid** · a few [HTB Academy](https://academy.hackthebox.com/) modules are free; the path needs a subscription, with [new prices](https://www.hackthebox.com/blog/new-academy-pricing) from 12 October 2026 | L2–L3 · Mid–Senior | [Security](37-learn-security-devsecops.md), [Wazuh](48-wazuh-and-security-tools.md) |

**Free-only path:** the Wazuh proof-of-concept scenarios in your own lab, Juice Shop behind Traefik
and CrowdSec on a throwaway VM, the flAWS2 defender path, Kubernetes Goat, the WrongSecrets Docker
challenges, the Wiz Cloud Hunting Games, and the free challenges on LetsDefend and Blue Team Labs
Online.

### Best picks for defensive security

**Wazuh proof-of-concept guide (free).** The best match for your stack: each scenario tells you how
to trigger an event on a lab endpoint and which alert Wazuh should raise. First: file integrity
monitoring and brute-force detection on a lab Ubuntu agent. If the alert does not appear, you have
a real troubleshooting exercise for [Wazuh](48-wazuh-and-security-tools.md).

**OWASP Juice Shop (free).** Run it in Docker on an isolated lab VM behind Traefik, then check what
CrowdSec and Wazuh see while you work through a few beginner challenges. First: start the
container, find the hidden score board (finding it is a challenge in itself), and solve one
challenge while you watch the Traefik access log.

**OWASP WrongSecrets (free).** Secrets baked into images and configs are exactly what Trivy and
your Harbor scans should catch. First: the Docker challenges on the hosted instance, then scan the
project's public container image with Trivy on a lab VM and see which secrets it reports and which
it misses.

**LetsDefend and Blue Team Labs Online (freemium).** Investigations on evidence you could not
safely create yourself. First: one free LetsDefend alert from triage to closure, then one free BTLO
challenge with a packet capture. Write each up in the incident note format from
[Security](37-learn-security-devsecops.md).

**TryHackMe SOC Level 1 or HTB Academy SOC Analyst (paid).** Choose one only if you want a long,
structured SOC path after the free options. TryHackMe is gentler and cheaper; HTB Academy goes
deeper. Buying both is a waste.

---

## 12. Databases and SQL

Database work in operations is mostly reading: which query is slow, which row changed, whether a
backup really restored. Learn SQL with puzzles, then practise operations on PostgreSQL itself.

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [PostgreSQL Exercises](https://pgexercises.com/) | Graded queries on one small PostgreSQL dataset: joins, aggregates, window functions, recursive queries, modifying data | **Free** | L1–L2 · Junior–Mid | [Databases](38-learn-databases-ops.md), [Databases & backups problems](51-problems-databases-storage-backup.md) |
| [SQL Murder Mystery](https://mystery.knightlab.com/) | Solve a crime in SQL City by querying reports, witness statements and suspects; a walkthrough for beginners | **Free** | L0 · Fresher | [Databases](38-learn-databases-ops.md) |
| [Select Star SQL](https://selectstarsql.com/) | An interactive book that teaches SQL on a real dataset, with no sign-up | **Free** | L0–L1 · Fresher–Junior | [Databases](38-learn-databases-ops.md) |
| [SQLZoo](https://sqlzoo.net/) | Step-by-step SQL tutorials with quizzes and assessments | **Free** | L0–L1 · Fresher–Junior | [Databases](38-learn-databases-ops.md) |
| [Postgres Playground](https://www.crunchydata.com/developers/tutorials) | PostgreSQL running in the browser, with tutorials on performance analysis, indexes, partitioning and query analytics | **Free** | L2–L3 · Mid–Senior | [Databases](38-learn-databases-ops.md), [Databases & backups problems](51-problems-databases-storage-backup.md) |
| [Use The Index, Luke: 3-minute test](https://use-the-index-luke.com/3-minute-test) | Five questions on how indexes really behave, for your database engine | **Free** | L2–L3 · Mid–Senior | [Databases](38-learn-databases-ops.md) |
| [explain.dalibo.com](https://explain.dalibo.com/) | Paste `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` and read the plan as a tree; sample plans included | **Free** · no sign-up · plans are stored on its server, so use lab plans or the offline single-file version · checked 9 Nov 2026 | L2–L3 · Mid–Senior | [Databases](38-learn-databases-ops.md) |
| [database.build](https://database.build/) | Postgres running in your browser tab: make tables and run SQL with nothing installed | **Free** · AI features may ask you to sign in · checked 9 Nov 2026 | L0–L1 · Fresher–Junior | [Databases](38-learn-databases-ops.md) |
| [MinIO Play](https://play.min.io:9443/) | MinIO's public S3-compatible server: buckets, policies, versioning, and `mc`'s preset `play` alias as a restic or rclone target | **Free** · public demo credentials; everything you upload is public and deleted · checked 9 Nov 2026 | L1–L2 · Junior–Mid | [Databases, storage & backups](51-problems-databases-storage-backup.md) |

**Free-only path:** SQL Murder Mystery if SQL is new, then PostgreSQL Exercises, the Postgres
Playground performance tutorials, the 3-minute test, and a restore test of your own backup on a lab
VM, as in [Databases](38-learn-databases-ops.md).

### Best picks for databases

**PostgreSQL Exercises (free).** Plain, graded SQL on PostgreSQL, one of the databases you are
likely to run under Dokploy. First: the joins and aggregates sections. When you finish, load a
similar dataset into your lab Postgres and run the same queries with `EXPLAIN ANALYZE`.

**SQL Murder Mystery (free).** The friendliest start if SQL is new: the story makes you chain
queries the way you will when you dig through an application's tables during an incident. First:
the walkthrough if SQL is new, otherwise solve it straight away and count your queries.

**Postgres Playground (free).** Operations-flavoured tutorials in a browser database. First: the
performance analysis tutorial, then compare what it shows with `pg_stat_statements` on your own lab
database. Finish with the Use The Index, Luke test and read the chapters behind any question you
missed.

---

## 13. Project-based challenges

Projects turn separate skills into proof. Pick ones that mirror your stack, publish the sanitised
result, and follow the advice in [Building proof](40-career-ladder.md#10-building-proof).

| Site | What you practise | Cost | Level / stage | Use it with this handbook |
|---|---|---|---|---|
| [roadmap.sh DevOps projects](https://roadmap.sh/devops/projects) | About 28 project ideas from beginner to advanced: server stats script, log archive tool, nginx log analyser, SSH setup, static site server, DNS setup, containers, monitoring | **Free** | L0–L3 · Fresher–Senior | [Roadmap](34-roadmap.md) |
| [KodeKloud Engineer](https://engineer.kodekloud.com/) | 100 Days of DevOps as a three-month project with visible progress (see section 1) | **Free** | L0–L2 · Fresher–Mid | [Career ladder](40-career-ladder.md) |
| [DevOps exercises](https://github.com/bregman-arie/devops-exercises) | Over 2,600 questions and exercises across Linux, networking, cloud, Kubernetes, Terraform and more | **Free** | L0–L3 · Fresher–Senior | [Career ladder](40-career-ladder.md) |
| [90DaysOfDevOps](https://github.com/MichaelCade/90DaysOfDevOps) | A learning-in-public journey in three editions: 2022 foundations, 2023 DevSecOps, 2024 community sessions | **Free** | L0–L2 · Fresher–Mid | [Roadmap](34-roadmap.md) |
| [Coding Challenges](https://codingchallenges.fyi/challenges/intro) | Build your own tools: a load balancer, DNS resolver, Redis server, rate limiter, uptime monitor, NTP client, curl | **Free** | L2–L4 · Mid–Lead | [Networking](28-learn-networking.md), [Senior architecture](39-learn-senior-architecture.md) |
| [Advent of Code](https://adventofcode.com/) | Daily programming puzzles each December, in any language; good for Bash or Python speed | **Free** | L1–L3 · Junior–Senior | [Linux](27-learn-linux.md) |
| [DevOps-Daily challenges](https://github.com/The-DevOps-Daily/challenges) | Six graded fixes: shrink a Docker image, summarise an access log in Bash, fix a Kubernetes deployment, write Prometheus alerts, speed up PostgreSQL, build a Terraform network module | **Free** · open source; GitHub account, and your pull requests are public, so sanitise them · graded by GitHub Actions on your pull request · checked 7 Nov 2026 | L1–L2 · Junior–Mid | [Docker](30-learn-docker.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| [Hackattic](https://hackattic.com/challenges) | 17 hard tasks: produce a TLS certificate to spec, write a DNS server, "be the registry", restore a database dump, host Git | **Free** · optional account, and an API token to submit · your code runs in a throwaway VM; some tasks need a server reachable from the internet · checked 7 Nov 2026 | L2–L3 · Mid–Senior | [Network, DNS & TLS problems](42-problems-network-dns-tls-vpn.md), [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) |
| [Protohackers](https://protohackers.com/problems) | 12 TCP and UDP server problems, ending with a man-in-the-middle proxy and a reliable protocol over UDP | **Free** · no price stated; anonymous checks allowed; unconfirmed whether new submissions are accepted · runs on a short-lived cloud VM with a public port (YOUR cloud account, small bill) · checked 7 Nov 2026 | L2–L4 · Mid–Lead | [Networking](28-learn-networking.md) |
| [CodeCrafters](https://codecrafters.io/) | Rebuild Redis, Git, SQLite, Kafka, a DNS server or an HTTP server in your language, tested stage by stage | **Freemium** · limited free content; [membership](https://codecrafters.io/pricing) for 3 months, a year or lifetime | L3–L4 · Senior–Lead | [Senior architecture](39-learn-senior-architecture.md) |

**Free-only path:** one roadmap.sh project a month built on your own stack (Ubuntu, Docker, GitLab
CI), the six DevOps-Daily challenges as graded pull requests, the matching DevOps exercises
questions before interviews, and from L2 one Coding Challenge or Hackattic task per quarter. Run
any server that Hackattic or Protohackers must reach on a short-lived cloud VM with key-only SSH,
and delete it the same day.

### Best picks for projects

**roadmap.sh DevOps projects (free).** Small, concrete and graded by difficulty. First: "Server
Performance Stats" as a Bash script, then "Nginx Log Analyser". Both reuse commands from
[Why is it slow?](23-playbook-slow-system.md) and [Site down](25-playbook-site-down.md). Push each
one to a public repository with a short README.

**DevOps exercises (free).** A huge question bank for interview preparation. First: before an
interview, answer one topic out loud without notes, then check yourself and add the misses to the
plan in [Interview preparation](40-career-ladder.md#8-interview-preparation).

**Coding Challenges (free).** For L2 and up, building a load balancer or a DNS resolver teaches a
protocol more deeply than any course. First: "Build your own load balancer" in Go or Python, then
put two copies of a small app behind it, kill one, and compare its behaviour with Traefik's health
checks.

**CodeCrafters (freemium).** The same idea with automatic tests for each stage. First: try a free
challenge; pay only if you finish it and want the rest of the catalogue.

---

## 14. Practice plans by career stage

Each plan is one week that you repeat until the exit check for your stage in
[Self-check and exit tests](40-career-ladder.md#12-self-check-and-exit-tests) feels easy. The free
plan is complete on its own; the paid column is optional. The rhythm follows the KodeKloud study
method: lessons in the evenings, a timed rep in the mornings, homelab work at the weekend, and a
short review on Sunday.

Until you pass the CKA, the CKA track below takes the weekend slot, and the rest of your plan runs
on the 30-minute morning rep alone.

### Fresher plan (L0)

Goal: be comfortable in a shell, with Git and with basic networking, and write your first five-line
notes.

| When | Free-only plan | Optional paid add-on |
|---|---|---|
| Workday mornings, 30 min | Monday and Wednesday: Bandit levels. Tuesday and Thursday: a Linux Luminarium module. Friday: Learn Git Branching | Vim Adventures levels instead of one Bandit day |
| Two evenings, 60 min | A KodeKloud free crash course (Linux, then Docker) and the matching section of [Linux](27-learn-linux.md) | KodeKloud subscription: Learning Linux Basics Course & Labs |
| Weekend, 2 hours | One or two Linux Upskill Challenge days on your small server; SQL Murder Mystery once | none needed |
| Sunday, 20 min | Ten Subnetting Practice questions; reread the week's notes | none needed |

**What to log:** a five-line note for every level that stopped you for more than ten minutes, and
each new command in your own runbook with one line on when to use it.

### Junior plan (L1)

Goal: fix common breakages on Ubuntu, Docker, DNS and TLS without help, and run your first real
pipeline.

| When | Free-only plan | Optional paid add-on |
|---|---|---|
| Workday mornings, 30 min | Monday, Wednesday and Friday: a KodeKloud Engineer task. Tuesday and Thursday: a SadServers easy scenario tagged dns, nginx or docker | SadServers Pro once the free easy scenarios run out |
| Two evenings, 60 min | The KodeKloud lesson and handbook note for your current topic; one Mess With DNS or badssl.com experiment | KodeKloud subscription courses for Docker, Git and Nginx |
| Weekend, 2 to 3 hours | The Docker workshop or the free iximiuz Docker challenges; a GitLab CI pipeline on your GitLab that pushes to Harbor (or to the public Harbor demo); one AWS Educate lab | iximiuz Complete Bundle for the full Docker roadmap |
| Sunday, 30 min | One postmortem from Dan Luu's list; 15 minutes on Grafana Play | none needed |

**What to log:** a note for every scenario, and a running list of error strings (x509, 502,
NXDOMAIN, permission denied) with the layer each one points to.

### Mid-level plan (L2)

Goal: pass the CKA and find the failing layer of an incident quickly.

| When | Free-only plan | Optional paid add-on |
|---|---|---|
| Workday mornings, 30 min | Monday and Wednesday: a Killercoda CKA scenario or an iximiuz Kubernetes challenge. Tuesday and Thursday: a SadServers medium scenario. Friday: a USE Practice run | KodeKloud CKA Lightning Labs on one morning a week |
| Two evenings, 60 min | A section of the KodeKloud CKA course or of [Kubernetes](31-learn-kubernetes.md); one PromQL cheat sheet exercise | KodeKloud CKA course (subscription) |
| Weekend, 3 hours | Homelab break-and-fix from the twenty drills; one flAWS level or free Pwned Labs lab; one Wazuh proof-of-concept scenario; the Isovalent Cilium lab once | killer.sh sessions in the last three weeks before the exam |
| Once a month | Play the on-call engineer in a Wheel of Misfortune session | none needed |

**What to log:** for every Kubernetes rep, the time to the first useful piece of evidence as well
as the total time. That first number is what drops as you improve.

### Senior plan (L3)

Goal: solve platform-level problems and build labs for other people.

| When | Free-only plan | Optional paid add-on |
|---|---|---|
| Workday mornings, 30 min | Two days: a harder SadServers or iximiuz challenge. One day: a Big IAM Challenge policy (unreachable on 7 Nov 2026; use a free Pwned Labs or Cybr lab until it answers). One day: a Kubernetes Failure Stories write-up | SadServers Pro+ or the iximiuz Complete Bundle |
| Two evenings, 60 min | A chapter of Kubernetes the Hard Way; a Containerlab topology for MTU and routing; the OpenTelemetry demo with one failure flag | Blue Team Labs Online PRO for deeper investigations |
| Weekend, 3 hours | A CloudGoat scenario in a sandbox AWS account; Kubernetes Goat; Juice Shop behind Traefik and CrowdSec; one Wiz Cloud Security Championship challenge | HTB Academy or TryHackMe SOC path, one of them |
| Once a month | Run a Wheel of Misfortune session as game master for a junior | none needed |

**What to log:** each lab you build for others (what it breaks, how to reset it), and every
detection you add to Wazuh or Prometheus because of a practice session.

### Lead plan (L4)

Goal: make the team ready for incidents, measure delivery, and teach.

| When | Free-only plan | Optional paid add-on |
|---|---|---|
| Weekly, 60 min | One Coding Challenge stage (load balancer, rate limiter, DNS resolver); one postmortem discussed with the team | CodeCrafters membership |
| Monthly | A game day from [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md#8-l4-exit-test-the-game-day) with PagerDuty's incident roles; a Backdoors & Breaches tabletop with security | Uptime Labs for regular team drills |
| Quarterly | DORA Quick Check for each team; one session of DevOps Dream with the other leads, followed by a talk about your real metrics | none needed |
| Coaching | Assign SadServers scenarios to juniors and review their five-line notes with them | SadServers Business if you use it for hiring |

**What to log:** team-level results: time to mitigate in drills, action items closed from game
days, and the DORA Quick Check result over time.

### The CKA track

This runs inside the Junior and Mid-level plans and takes the weekend slot until the exam.

| Period | Free-only practice | Optional paid add-on |
|---|---|---|
| Weeks 1 to 4 | KodeKloud Kubernetes playground and your kubeadm homelab for the course labs; CKAD exercises for `kubectl` speed | KodeKloud CKA course sections in order |
| Weeks 5 to 8 | Killercoda CKA scenarios and iximiuz Kubernetes challenges on weekdays; the [twenty timed drills](31-learn-kubernetes.md#22-twenty-timed-break-and-fix-drills) at weekends | KodeKloud Lightning Labs and the first mock exam |
| Last 3 weeks | Kubernetes the Hard Way once (if you have not done it); repeat the drills you failed | killer.sh session 1, three weeks out; remaining mock exams; killer.sh session 2 in the final week |

Killercoda's COURSE plan is an alternative to the KodeKloud course, not an addition to it. Pick one.

### Your practice log

Keep one line per rep in a plain file in your notes repository. It turns practice into evidence
for reviews and interviews.

```text
2026-10-07 | SadServers     | easy, tag dns       | 30 min | 1 hint | notes/2026-10-07-dns.md
2026-10-08 | KodeKloud Eng. | 100 Days, day 12    | 25 min | 0      | notes/2026-10-08-cron.md
2026-10-10 | iximiuz        | k8s NotReady node   | 18 min | 0      | notes/2026-10-10-kubelet.md
```

Review the log every Sunday. Anything that took more than twice its timer goes back on next week's
list. Three solves in a row inside the timer means it is time to move up a level.

---

## 15. Practice map

Each playbook, learn and toolbox module from 21 to 51, with the one to three sites that train it
best. Finish the reading, then do the first site in the row.

| Module | Practise on | Why these |
|---|---|---|
| [21 — Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) | [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), [iximiuz Docker playground](https://labs.iximiuz.com/playgrounds/docker), [SadServers](https://sadservers.com/scenarios) | Rebuild Apache holding 443, free the port and put Traefik in front, then practise port conflicts under a timer |
| [22 — Who owns this port?](22-playbook-ports-inventory.md) | [SadServers](https://sadservers.com/scenarios), [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), [CMD Challenge](https://cmdchallenge.com/) | `ss`, `lsof` and `systemctl` against a clock, plus the pipelines to read their output |
| [23 — Why is it slow?](23-playbook-slow-system.md) | [iximiuz USE Practice](https://labs.iximiuz.com/playgrounds/use-practice-4ce4816f), [SadServers](https://sadservers.com/scenarios) | The USE method against random load, then slow-service scenarios |
| [24 — Network speed](24-playbook-network-speed.md) | [Containerlab](https://containerlab.dev/), [Wireshark sample captures](https://wiki.wireshark.org/SampleCaptures), [iximiuz networking playgrounds](https://labs.iximiuz.com/playgrounds?category=networking) | MTU, loss and routing in a lab you control, and real captures to read |
| [25 — Site down](25-playbook-site-down.md) | [Mess With DNS](https://messwithdns.net/), [badssl.com](https://badssl.com/), [nginx playground](https://nginx-playground.wizardzines.com/) | Break DNS, TLS and the proxy layer one at a time |
| [26 — Docker & K8s incidents](26-playbook-containers-k8s.md) | [iximiuz Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes), [Killercoda CKA scenarios](https://killercoda.com/cka), [KubeInvaders](https://github.com/lucky-sideburn/kubeinvaders) | Realistic pod, node and Ingress failures, plus self-healing you can watch |
| [27 — Linux](27-learn-linux.md) | [Linux Upskill Challenge](https://linuxupskillchallenge.org/), [OverTheWire Bandit](https://overthewire.org/wargames/bandit/), [pwn.college Linux Luminarium](https://pwn.college/linux-luminarium/) | A real server to run, SSH reflexes and checked basics |
| [28 — Networking](28-learn-networking.md) | [Subnetting Practice](https://subnettingpractice.com/), [Mess With DNS](https://messwithdns.net/), [Cisco Packet Tracer](https://www.netacad.com/cisco-packet-tracer) | Addressing drills, live DNS and simulated LANs |
| [29 — Web servers & proxies](29-learn-webservers-proxies.md) | [nginx playground](https://nginx-playground.wizardzines.com/), [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), [SSL Labs](https://www.ssllabs.com/ssltest/) | Config experiments, a full Apache or nginx install, and a TLS report |
| [30 — Docker](30-learn-docker.md) | [iximiuz Docker roadmap](https://labs.iximiuz.com/roadmaps/docker), [Docker workshop](https://docs.docker.com/get-started/workshop/), [Docker Labspaces](https://github.com/dockersamples/labspace-infra) | Checked challenges, the official path and local labs |
| [31 — Kubernetes](31-learn-kubernetes.md) | [Killercoda CKA scenarios](https://killercoda.com/cka), [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way), [killer.sh](https://killer.sh/) | Daily reps, deep understanding, and the exam simulator at the end |
| [32 — Performance & observability](32-learn-performance-observability.md) | [Grafana Play](https://play.grafana.org/), [PromQL cheat sheet](https://promlabs.com/promql-cheat-sheet/), [OpenTelemetry demo](https://opentelemetry.io/docs/demo/) | Reading dashboards, writing queries, chasing failures in traces |
| [33 — CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) | [GitLab CI/CD tutorials](https://docs.gitlab.com/ci/quick_start/), [HashiCorp Terraform tutorials](https://developer.hashicorp.com/terraform/tutorials), [Wheel of Misfortune](https://dastergon.github.io/wheel-of-misfortune/) | Pipelines on your own GitLab, Terraform basics and incident drills |
| [34 — Roadmap](34-roadmap.md) | [roadmap.sh DevOps projects](https://roadmap.sh/devops/projects), [KodeKloud Engineer](https://engineer.kodekloud.com/), [90DaysOfDevOps](https://github.com/MichaelCade/90DaysOfDevOps) | Projects and a daily task that follow the same order of topics |
| [35 — Deployment patterns](35-deployment-patterns.md) | [iximiuz Docker Swarm playground](https://labs.iximiuz.com/playgrounds/docker-swarm), [KodeKloud Docker playground](https://kodekloud.com/playgrounds/playground-docker), [GitLab CI/CD tutorials](https://docs.gitlab.com/ci/quick_start/) | Rolling updates and rollbacks on a real Swarm, driven by a pipeline |
| [36 — Cloud & AWS](36-learn-cloud-aws.md) | [AWS Educate](https://aws.amazon.com/education/awseducate/), [flAWS](http://flaws.cloud/), [The Big IAM Challenge](https://bigiamchallenge.com/) (unreachable on 7 Nov 2026; use [Pwned Labs](https://pwnedlabs.io/explore) meanwhile) | Guided console labs in a vendor-owned sandbox, classic mistakes and policy reading |
| [37 — Security & DevSecOps](37-learn-security-devsecops.md) | [Kubernetes Goat](https://madhuakula.com/kubernetes-goat/), [flAWS2](http://flaws2.cloud/), [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) | Misconfigurations in a cluster, a cloud incident from logs, web attacks your tools should catch |
| [38 — Databases](38-learn-databases-ops.md) | [PostgreSQL Exercises](https://pgexercises.com/), [Postgres Playground](https://www.crunchydata.com/developers/tutorials), [SQL Murder Mystery](https://mystery.knightlab.com/) | SQL fluency first, then performance work |
| [39 — Senior: architecture & leadership](39-learn-senior-architecture.md) | [DevOps Dream](https://devops.games/), [DORA Quick Check](https://dora.dev/quickcheck/), [Coding Challenges](https://codingchallenges.fyi/challenges/intro) | Delivery trade-offs, real metrics and systems built from scratch |
| [40 — Career ladder](40-career-ladder.md) | [DevOps exercises](https://github.com/bregman-arie/devops-exercises), [roadmap.sh DevOps projects](https://roadmap.sh/devops/projects), [Cloud Resume Challenge](https://cloudresumechallenge.dev/) | Interview answers and public proof |
| [41 — Linux & systems problems](41-problems-linux-systems.md) | [Linuxzoo](https://linuxzoo.net/), [systemd by example](https://systemd-by-example.com/), [SadServers](https://sadservers.com/scenarios) | A root VM with server-side tutorials, unit-file behaviour, then timed break-and-fix |
| [42 — Network, DNS, TLS & VPN problems](42-problems-network-dns-tls-vpn.md) | [Wizard Zines debugging mysteries](https://mysteries.wizardzines.com/), [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/), [badssl.com](https://badssl.com/) | Choosing the next check, reading a handshake byte by byte, naming each TLS failure |
| [43 — Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) | [SadServers "San Juan"](https://sadservers.com/scenario/san-juan), [nginx playground](https://nginx-playground.wizardzines.com/), [iximiuz Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes), [SSL Labs](https://www.ssllabs.com/ssltest/) | A broken Traefik in Docker Compose, routing logic, the Traefik Ingress to Gateway API challenge, and TLS checks |
| [44 — Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) | [Harbor demo server](https://demo.goharbor.io), [SadServers "Salta"](https://sadservers.com/scenario/salta), [iximiuz Docker Swarm playground](https://labs.iximiuz.com/playgrounds/docker-swarm) | Push and pull on real Harbor, a container that will not start, and Swarm mechanics |
| [45 — Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md) | [SadServers "San Juan"](https://sadservers.com/scenario/san-juan), [iximiuz Docker Swarm playground](https://labs.iximiuz.com/playgrounds/docker-swarm), [KodeKloud Docker playground](https://kodekloud.com/playgrounds/playground-docker) | The nearest free Dokploy-style drill (Traefik plus Compose), then the Swarm and Docker mechanics Dokploy is built on |
| [46 — Kubernetes problems](46-problems-kubernetes.md) | [SadServers "Bilbao"](https://sadservers.com/scenario/bilbao), [Isovalent labs](https://isovalent.com/resource-library/labs/), [Helm Playground](https://helm-playground.com/) | Broken deployments, a cluster with no CNI and a broken HTTPRoute, and template errors |
| [47 — CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) | [GitLab CI/CD tutorials](https://docs.gitlab.com/ci/quick_start/), [Hello GitHub Actions](https://github.com/skills/hello-github-actions), [KodeKloud CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd) | GitLab first, then Actions and Jenkins side by side |
| [48 — Wazuh & security tools](48-wazuh-and-security-tools.md) | [Wazuh proof-of-concept guide](https://documentation.wazuh.com/current/proof-of-concept-guide/index.html), [LetsDefend](https://letsdefend.io/), [Backdoors & Breaches](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/) | Trigger and detect in your lab, triage alerts, rehearse a breach |
| [49 — Observability toolbox](49-observability-stack-problems.md) | [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/), [KodeKloud Prometheus & Grafana playground](https://kodekloud.com/playgrounds/playground-prometheus-grafana), [OpenTelemetry demo](https://opentelemetry.io/docs/demo/) | Build the stack, then debug it with real signals |
| [50 — Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) | [LocalStack](https://www.localstack.cloud/pricing), [CloudGoat](https://github.com/RhinoSecurityLabs/cloudgoat), [HashiCorp Terraform tutorials](https://developer.hashicorp.com/terraform/tutorials) | Terraform without a bill, real misconfigurations, then clean state work |
| [51 — Databases, storage & backups problems](51-problems-databases-storage-backup.md) | [Postgres Playground](https://www.crunchydata.com/developers/tutorials), [PostgreSQL Exercises](https://pgexercises.com/), [Use The Index, Luke](https://use-the-index-luke.com/3-minute-test) | Query and index behaviour behind most database tickets |

The command reference (modules 01 to 20) pairs best with CMD Challenge, the KodeKloud Ubuntu
playground and SadServers: look up a command, then use it under a timer. For
[Windows](17-windows.md), use Under The Wire. For
[On-prem vs cloud](55-paths-onprem-vs-cloud.md), start with the vendor-owned accounts in section 7
(AWS Educate, the Builder Center sandbox, Pwned Labs, Cybr, Applied Skills), then System Design
Sim for cost intuition. Nothing free covers [macOS](20-macos.md) yet.

---

## 16. Dead, renamed or paid-only

Checked on 3 October 2026; rows that mention 7 Nov 2026 were added or re-checked on 7 November
2026. If an older guide, video or forum post sends you to one of these, use the replacement in the
last column. EKS Cluster Games and The Big IAM Challenge are not listed here: they were unreachable
on 7 Nov 2026, but no retirement notice was found, so they stay in sections 6 and 7 with that
label.

| What you may see mentioned | What changed | Use instead |
|---|---|---|
| [Katacoda](https://www.katacoda.com/) | Closed to the public in 2022; the page now points to O'Reilly | [Killercoda](https://killercoda.com/), iximiuz Labs, KodeKloud playgrounds |
| [Play with Docker](https://labs.play-with-docker.com/) | Retired on 1 March 2026 (the page still shows the notice and no working start button, 9 Nov 2026); Docker [announced it](https://forums.docker.com/t/play-with-docker-is-deprecated-and-will-be-unavailable-starting-march-1-2026-learn-about-alternatives/151177) on 22 February 2026 and named alternatives | [iximiuz Docker playground](https://labs.iximiuz.com/playgrounds/docker), [Killercoda](https://killercoda.com/), the [KodeKloud Docker playground](https://kodekloud.com/playgrounds/playground-docker), [Docker Labspaces](https://github.com/dockersamples/labspace-infra) |
| [Play with Kubernetes](https://labs.play-with-k8s.com/) | Same end date, 1 March 2026 | Killercoda, the [iximiuz K3s playground](https://labs.iximiuz.com/playgrounds/k3s), the KodeKloud Kubernetes playground |
| [Play with Docker classroom](https://training.play-with-docker.com/) | The lesson pages are still online, but their in-browser terminals depended on Play with Docker, so expect them to fail | The [Docker workshop](https://docs.docker.com/get-started/workshop/) on your own Docker host |
| [Linux Journey](https://linuxjourney.com/) | Moved: the old address redirects permanently to LabEx, with the lessons kept | [Linux Journey on LabEx](https://labex.io/linuxjourney) |
| [GitHub Skills](https://skills.github.com/) | Now part of GitHub Learn; the old address redirects. Before that, GitHub Learning Lab closed in 2022 | [GitHub Skills on GitHub Learn](https://learn.github.com/skills) |
| [Google Cloud Skills Boost](https://www.cloudskillsboost.google/) | Renamed Google Skills; the old address redirects permanently. The Arcade continues, but since April 2026 Arcade Sprints and the Certification Zone are gone, games have fewer labs and every game is worth one point (7 Nov 2026) | [Google Skills](https://www.skills.google/) |
| [AWS Skill Builder, old address](https://explore.skillbuilder.aws/) | Redirects to the new site, where Cloud Quest was rebuilt and relaunched on 11 August 2026 | [AWS Skill Builder](https://skillbuilder.aws/) |
| [AWS Cloud Quest docs page](https://docs.cloudquest.skillbuilder.aws/coming-soon/index.html) | Now says only that Cloud Quest has moved to Skill Builder; AWS's product page says free accounts get limited access and every role needs a subscription (7 Nov 2026) | [AWS Cloud Quest](https://skillbuilder.aws/cloudquest); AWS Educate for free console labs |
| [Microsoft Learn sandboxes](https://learn.microsoft.com/en-us/answers/questions/5772915/microsoft-sandbox-is-no-longer-available) | Retired: exercises in [Microsoft Learn](https://learn.microsoft.com/en-us/training/) modules now need your own Azure subscription; the modules stay free. The [Learn FAQ](https://learn.microsoft.com/en-us/training/support/faq?pivots=sandbox), updated 29 July 2026, confirms it (7 Nov 2026) | [Microsoft Applied Skills](https://learn.microsoft.com/en-us/credentials/applied-skills/) labs for a real Azure portal; Azure for Students ($100 of credit, no card) if you are a student; LocalStack or the HashiCorp sandbox for AWS-style practice; Google Skills free credits; or an Azure free account with a budget alarm |
| LocalStack Community edition | Frozen: LocalStack says the Community emulator will no longer receive product updates; the free Hobby plan is non-commercial and needs an account and auth token (7 Nov 2026) | [LocalStack Hobby](https://www.localstack.cloud/pricing), or the [HashiCorp Terraform sandbox](https://developer.hashicorp.com/terraform/sandbox) in the browser |
| [Backdoors & Breaches, old address](https://www.blackhillsinfosec.com/projects/backdoorsandbreaches/) | Redirects to /tools/backdoorsandbreaches/ (7 Nov 2026) | [Backdoors & Breaches](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/) |
| [picoCTF.org](https://picoctf.org/) | Became CyLab Security Academy; picoCTF logins created before 8 May 2026 keep their progress | [CyLab Security Academy](https://cylabacademy.org/) |
| [Killer Shell CKA on Killercoda](https://killercoda.com/killer-shell-cka) | Marked as moved: replaced by the CKA Scenario Course in the paid COURSE plan | [Sachin's free CKA mock course](https://killercoda.com/sachin/course/CKA) (re-checked 9 Nov 2026), the free community sets on [Killercoda CKA](https://killercoda.com/cka), iximiuz Kubernetes challenges |
| [YouBrokeProd](https://youbrokeprod.com/) | An incident-simulator game, offline on 3 October 2026 with a "back online soon" notice while it migrates | SadServers, [SysAdmin Simulator](https://sys-admin-simulator.com/) |
| [DNSViz](https://dnsviz.net/) | In maintenance mode: new DNSSEC analyses work, older analyses cannot be loaded | Mess With DNS for experiments, `dig +dnssec` on your lab |
| GitLab's public hands-on lab guides | The CI/CD lab guide pages in the GitLab handbook now redirect to a GitLab sign-in | [GitLab CI/CD tutorials](https://docs.gitlab.com/ci/quick_start/), [GitLab University](https://university.gitlab.com/) |
| [HTB Academy pricing](https://www.hackthebox.com/blog/new-academy-pricing) | Monthly plans move from cubes to tier-based access, at higher prices, on 12 October 2026 | The free options in section 11 first |
| [LetsDefend](https://letsdefend.io/) | Announces an agreement to be acquired by Hack The Box; plans may change | [Blue Team Labs Online](https://blueteamlabs.online/), the Wazuh proof-of-concept guide |
| The Unix Game (`unixgame.io`) | Redirects to an unrelated gambling site — do not use (7 Nov 2026) | OverTheWire Bandit, CMD Challenge, the Linux Luminarium |
| `contained.af` | The old container-escape game no longer resolves (NXDOMAIN, 7 Nov 2026) | "Contain Me If You Can" in the Wiz Cloud Security Championship |
| [LF Introduction to GitOps (LFS169)](https://training.linuxfoundation.org/training/introduction-to-gitops-lfs169/) | "No longer available" (7 Nov 2026) | The GitOps simulators in the DevOps Daily games |
| [WrongSecrets Render mirror](https://wrongsecrets.onrender.com/) | Suspended by its owner (HTTP 503, 7 Nov 2026) | The [Heroku instance](https://wrongsecrets.herokuapp.com/) |

Paid-only or effectively paid, each with a free route:

| Paid option | What you pay for | Free route to the same skill |
|---|---|---|
| [killer.sh](https://killer.sh/) | Exam simulator sessions | Two sessions come with the CKA exam; before that, Killercoda CKA scenarios and the homelab drills |
| [TryHackMe SOC Level 1](https://tryhackme.com/path/outline/soclevel1) | Premium subscription | Wazuh proof-of-concept guide, LetsDefend and BTLO free challenges |
| [HTB Academy SOC Analyst path](https://academy.hackthebox.com/path/preview/soc-analyst) | Academy subscription | The same free route as above |
| [Uptime Labs](https://uptimelabs.io/) | Team incident simulations | Wheel of Misfortune sessions and the free SysAdmin Simulator shift |
| [PromLabs PromQL training](https://promlabs.com/promql-training/) | Live group training | The PromQL cheat sheet, PromLens and the demo Prometheus |
| [Vim Adventures](https://vim-adventures.com/) | A six-month game licence | `vimtutor`, which ships with Vim |
| [AWS Jam](https://aws.amazon.com/training/digital/aws-jam/) | Free accounts get limited access; Jam events need a Team subscription (7 Nov 2026) | AWS Educate, the Builder Center sandbox, and the Pwned Labs and Cybr free labs |

### What no free site covers yet

The 7 November 2026 sweep found nothing free for these. Build your own labs for them, which is the
L4 skill in section 18.

- **Dokploy and Docker Swarm break-fix.** No free lab breaks either for you. The nearest stand-ins are SadServers "San Juan" (Traefik with Docker Compose), the iximiuz Swarm playground and the Harbor demo.
- **Cloud break-fix in the style of SadServers.** AWS Jam is the best one and sits behind a subscription. The do-it-yourself routes need your own account: break a VPC or IAM setup on purpose in a dedicated, credit-capped account, never one near production.
- **macOS.** Nothing for [macOS](20-macos.md).
- **Partly closed on 9 Nov 2026.** Object storage (MinIO Play), CrowdSec parsers (CrowdSec Playground), Proxmox-style virtualisation (the Incus demo), Flux (the CNPE scenarios) and nftables (an iximiuz challenge and network-fundamentals-lab) now have a free option. Still nothing for Dokploy, GRUB or boot recovery, SELinux troubleshooting without a Red Hat login, or change management.
- **Smaller gaps.** No free browser playground for OpenTofu or Jenkins, no free iptables or nftables sandbox in the browser, no FinOps game with verified availability, and no standalone chaos-engineering game.

---

## 17. Learning tools by topic

**Learning tools show you how a healthy system works; the practice sites in sections 1 to 13 give
you broken systems to fix.** See the normal case in a tool first, then go and break it.

These are free visualisers, explainers, calculators and validators, in the same family as
Protocol Explorer in section 4. Each was opened on 8 or 9 November 2026: the page was live and
said what is listed here. Interactive behaviour was mostly not exercised. The best one to three
per topic also appear in that topic's study path on the 3D map. **Topics** are map topic ids.

**Data safety:** *Browser* means the site says, or its code shows, that your input stays in the
tab. *Server* means what you paste goes to its server, so use lab data only. *Public* means you
enter a public domain, URL or image that its server checks. *No input* means there is nothing to
paste. *Not stated* means treat it as *Server*. A Share, Save or permalink button publishes what
you typed, even on a *Browser* tool. ◇ marks a tool whose features came from its docs, or whose
page did not fully load.

### Networking, DNS, TLS and HTTP

| Tool | What it shows you | Data safety | Level | Topics |
|---|---|---|---|---|
| [TLSRef Configurator](https://configurator.tlsref.org/) (formerly the Mozilla SSL Configuration Generator) | Modern, Intermediate or Old TLS settings for nginx, Apache, HAProxy, Traefik, Caddy, AWS ALB/ELB, Postfix and more | No secrets entered | L2 | tls-certs, apache-vhosts, traefik |
| [Visual Subnet Calculator](https://visualsubnetcalc.com/) | Split and join subnets; AWS, Azure and OCI modes subtract each cloud's reserved addresses | Browser; a share link encodes your whole plan | L1–L2 | net-basics, aws-vpc-alb |
| [cidr.xyz](https://cidr.xyz/) | A CIDR as a bit map: mask, base, broadcast, usable range | Browser | L1 | net-basics |
| [jodies ipcalc](https://jodies.de/ipcalc) | Address, mask, wildcard and broadcast in binary; supernets | Server, harmless input | L1 | net-basics |
| [Kurose & Ross interactive problems](https://gaia.cs.umass.edu/kurose_ross/interactive/) | Fresh exercises with answers: TCP sequence/ACK, congestion window, RTT and timeout, DNS, subnets, NAT, routing | No input | L1–L2 | net-basics, sockets-ports, routing-nat, network-speed |
| [Explained from First Principles: The Internet](https://explained-from-first-principles.com/internet/) | A long explainer with built-in DNS, DNSSEC and HTTP tools | DNS tools use Google's API; IP lookup uses IPinfo | L1–L3 | net-basics, dns-deep, tls-certs |
| [DNSViz](https://dnsviz.net/) | A zone's delegation and DNSSEC chain as a graph, with errors (new analyses only, see section 16) | Public | L2–L3 | dns-deep |
| [Verisign DNSSEC Debugger](https://dnssec-analyzer.verisignlabs.com/) | The DNSSEC chain checked step by step | Public | L3 | dns-deep |
| [Google Admin Toolbox Dig](https://toolbox.googleapps.com/apps/dig/) | A web `dig` with the raw answer | Public | L1 | dns-deep, network-problems |
| [Globalping](https://globalping.io/) | ping, traceroute, mtr, dig and HTTP from probes picked by country, ASN or cloud region | Public | L1–L2 | dns-deep, site-down-walk, uptime-checks |
| [unboundtest](https://unboundtest.com/) | A fresh resolver configured like Let's Encrypt's, with its full log | Public | L3 | letsencrypt-acme |
| [Let's Debug](https://letsdebug.net/) | Why a certificate will not issue: DNS, CAA, rate limits, HTTP-01, DNS-01, TLS-ALPN-01 | Public | L2 | letsencrypt-acme |
| [crt.sh](https://crt.sh/) | Every logged certificate for a name | Public; CT logs expose every hostname you put in a certificate | L2 | tls-certs, letsencrypt-acme |
| [The Illustrated QUIC Connection](https://quic.xargs.org/) and [TLS 1.2](https://tls12.xargs.org/) | Every byte of a handshake, reproduced with command-line tools | No input | L3–L4 | tls-certs |
| [REDbot](https://redbot.org/) | HTTP lint: Cache-Control, Vary, ETag, content negotiation | Public | L2–L3 | http-curl, reverse-proxy, site-down-walk |
| [HTTP/3 Check](https://http3check.net/) | Alt-Svc, QUIC versions, 0-RTT and handshake timings | Public | L2 | reverse-proxy, traefik-deep-dive |
| [HTTP/3 explained](https://http3-explained.haxx.se/) | A free book on HTTP/3 and QUIC | No input | L2 | http-curl |
| [Will It CORS?](https://httptoolkit.com/will-it-cors/) | Describe a cross-origin request; see what the server must answer | Not stated | L1–L2 | proxy-problems |
| [curlconverter](https://curlconverter.com/) | A curl command as Python, Go, Node, Ansible, HTTPie or PowerShell | Browser; strip tokens and cookies first | L1 | http-curl |
| [Toolsbase Traefik validator](https://toolsbase.dev/en/developer/traefik-config-validator) | 24 checks on Traefik v3 YAML and labels: missing services, typos, v2-to-v3 breaks | Browser | L2 | traefik, traefik-legacy-routes |
| [Traceroute Visualizer](https://kriztalz.sh/traceroute-visualizer/) | traceroute or mtr output as a hop map and loss/RTT heatmap | Browser, but hop IPs go to IPinfo and PeeringDB; geolocation is often wrong | L1 | network-speed |
| [CloudPing.info](https://www.cloudping.info/) | Latency from your browser to about 170 cloud regions (no Azure) | Your browser pings providers | L1 | network-speed |
| [Encapsulation calculator](https://baturin.org/tools/encapcalc/) | Overhead and the MTU left for WireGuard, VXLAN, GRE, VLAN or MPLS | No secrets entered | L2–L3 | vpn-mesh, network-speed |
| [AllowedIPs calculator](https://www.procustodibus.com/blog/2021/03/wireguard-allowedips-calculator/) | WireGuard allowed minus disallowed ranges, as a CIDR list | CIDRs only | L2 | vpn-mesh |
| [DevToolLab WireGuard generator](https://devtoollab.com/tools/wireguard-config-generator) | Server and peer configs with PSKs and QR codes | Browser (stated); never give any generator a real private key | L1–L2 | vpn-mesh |
| [Is BGP safe yet?](https://isbgpsafeyet.com/) | BGP hijacks and RPKI, animated, plus a test of your ISP | The test loads a probe site | L0–L1 | routing-nat |
| [BGPlay](https://bgplay.massimocandela.com/) | A prefix's route changes over time from RIPE RIS data | Query only | L3 | routing-nat |
| [bgp.tools](https://bgp.tools/) | ASN and prefix search with a looking glass | Query only | L2–L3 | routing-nat |
| [Hurricane Electric looking glass](https://lg.he.net/) | BGP routes, ping and traceroute from HE routers | Query only | L3 | routing-nat |
| [PCAP Triage Lite](https://dfir-toolkit.andreafortuna.org/tools/pcap-triage-lite/) | HTTP, DNS and TLS SNI pulled from a capture | Browser | L2 | packet-capture |
| [A-Packets](https://apackets.com/) | A capture turned into an interactive report | Free uploads are public: sample captures only | L2 | packet-capture |

Lower confidence (live, quality not established): the [Toolkit TCP simulators](https://toolkit-1m9.pages.dev/tools/simulators/tcp-congestion), [McCreary networking MicroSims](https://dmccreary.github.io/networking/sims/) (some unfinished), the [SSLShopper certificate decoder](https://www.sslshopper.com/certificate-decoder.html) (never paste a key), [curlbuilder](https://curlbuilder.com/) and [Wireview](https://wireview.github.io/).

### Linux

| Tool | What it shows you | Data safety | Level | Topics |
|---|---|---|---|---|
| [explainshell](https://explainshell.com/) | Each part of a command matched to its man page, with Ubuntu 26.04 pages | Server: the command is in the URL | L0–L1 | shell-fhs |
| [ManKier explain](https://www.mankier.com/explain) | The same idea on ManKier's man pages | Server | L0–L1 | shell-fhs |
| [tldr pages web app](https://tldr.inbrowser.app/) | Short examples per command, by platform | Search term only | L0 | shell-fhs, packages-apt, windows-macos |
| [cheat.sh](https://cheat.sh/) | Community cheat sheets, also `curl cht.sh/tar` | Query only | L0–L1 | shell-fhs |
| [chmod and umask calculator](https://hidekazu-konishi.com/tools/chmod_permission_calculator_tool.html) | Octal, symbolic and `ls -l` forms, setuid/setgid/sticky, a umask tab | Browser | L0–L1 | files-permissions |
| [chmod-calculator.com](https://chmod-calculator.com/) | Checkboxes to octal and rwx | Not stated, harmless | L0 | files-permissions |
| [What is a filesystem?](https://aneeshdurg.me/what_is_a_filesystem/) | Inodes, links, permissions, mounts and disk latency, animated | No input | L1–L2 | disk-full, files-permissions |
| [Linux Handbook SSH config generator](https://linuxhandbook.com/tools/ssh-config-generator/) | One `~/.ssh/config` Host block from a form | Not stated: host names and key paths only, never key contents | L0–L1 | ssh-basics |
| [ssh-audit.com](https://www.ssh-audit.com/) | Your SSH server's algorithms against hardened policies | Its server connects to the host: internet-reachable hosts you own | L2–L3 | ssh-hardening |
| [Linuxize systemd generator](https://linuxize.com/tools/systemd-service-file-generator/) | A unit file as you type, with `systemd-analyze verify` and a root warning | Browser | L1–L2 | systemd-units |
| [Systemd Timer Builder](https://tools.incoherency.co.uk/systemd-timer-builder) | A `.service` and `.timer` pair: OnCalendar, Persistent, delays | Not stated | L1–L2 | time-scheduling |
| [crontab.guru](https://crontab.guru/) | A cron line in plain English | Expression only | L0–L1 | time-scheduling |
| [Cronuru](https://cronuru.com/) | Cron converted between Unix, Kubernetes CronJob, EventBridge and GitHub Actions | Expression only | L1–L2 | time-scheduling |
| [regex101](https://regex101.com/) | Test, debug and explain a regex in POSIX BRE/ERE, PCRE2, Python or Go | Save and Library store it: no real log lines | L1–L2 | text-tools, crowdsec-fail2ban |
| [regexper](https://regexper.com/) | A regex drawn as a railroad diagram | Permalink holds the regex | L1 | text-tools |
| [Regex Vis](https://regex-vis.com/) | A regex graph you can edit node by node | Not stated | L1–L2 | text-tools |
| [RegExr](https://regexr.com/) | Live tester and reference | Save makes a public link | L1 | text-tools |
| [RegexLearn](https://regexlearn.com/) | Step-by-step regex lessons | Not stated | L0–L1 | text-tools |
| [iHateRegex](https://ihateregex.io/) | 29 ready patterns with diagrams | Not stated | L1 | text-tools |
| [jq playground](https://play.jqlang.org/) (official) | A jq filter, its input and output | Browser until you share | L1–L2 | text-tools, k8s-troubleshooting |
| [JMESPath](https://jmespath.org/) | The language behind `aws --query`, with a live box | Not stated | L1–L2 | text-tools |
| [linuxatemyram](https://www.linuxatemyram.com/) | Why `free` looks full, and when to worry | No input | L0–L1 | memory-oom |
| [WintelGuy RAID calculator](https://wintelguy.com/raidcalc.pl) | Usable space, fault tolerance and write penalty for RAID and RAID-Z | Numbers only | L1–L2 | disk-io |
| [JSLinux](https://bellard.org/jslinux/) | Alpine 3.23 and other Linux images emulated in your tab | Browser | L0–L2 | start-here, kernel-boot |
| [v86](https://copy.sh/v86/) | x86 emulator: Arch, Buildroot and more, with network capture | Browser | L1–L3 | start-here, kernel-boot |
| [Interactive kernel map](https://makelinux.github.io/kernel/map/) | A clickable map of kernel 7.0 subsystems | No input | L3–L4 | kernel-boot |
| [Linux syscall tables](https://syscalls.mebeim.net/) | Syscall numbers, signatures and sources per arch and version | No input | L3–L4 | kernel-boot |
| [kernelconfig.io](https://www.kernelconfig.io/) | Kconfig options by kernel version and arch | Search only | L3–L4 | kernel-boot |
| [speedscope](https://www.speedscope.app/) | A profile as a flame graph: time order, left heavy, sandwich | Browser | L3 | perf-deep-dive |
| [Firefox Profiler](https://profiler.firefox.com/) | Imports Linux perf; compares two recordings | Browser until you upload | L3 | perf-deep-dive |
| [Perfetto UI](https://ui.perfetto.dev/) | perf and ftrace traces on a timeline | Browser | L3–L4 | perf-deep-dive |
| [eBPF.party](https://ebpf.party/) | eBPF exercises run on a real kernel in a throwaway VM | Server: exercise code only | L3–L4 | perf-deep-dive |

Lower confidence, so not on the map: [Sysctl Explorer](https://sysctl-explorer.net/) (stale, 2018), the [container2wasm demo](https://ktock.github.io/container2wasm-demo/), the [inet-ip CLI playground](https://inet-ip.info/playground), [WebAWK](https://agordon.github.io/webawk/), [DistroSea](https://distrosea.com/) (desktop distros only), [Incus Try it](https://linuxcontainers.org/incus/try-it/) (down for maintenance when visited) and the [Vectree OOM explainer](https://vectree.io/c/scoring-algorithms-oomscoreadj-and-heuristics-of-the-linux-oom-killer) (no sources cited). For plain-English sudoers, read [Understanding sudoers(5) syntax](https://toroid.org/sudoers-syntax).

### Containers, Kubernetes, CI/CD, IaC and observability

| Tool | What it shows you | Data safety | Level | Topics |
|---|---|---|---|---|
| [Kubernetes, explained](https://kubernetes-explained.vercel.app/) (Kubesimplify) | Step-through: kubectl to running pod, scheduler phases, Service to EndpointSlice, kube-proxy modes, ingress | No input | L1–L3 | k8s-architecture, k8s-services-dns, k8s-networking |
| [Kubernetes Visual Handbook](https://k8s-info.pages.dev/docs/intro) | 65+ visualisers from Pod lifecycle to NetworkPolicies; author unknown | No input | L0–L3 | k8s-architecture |
| [Webernetes](https://webernetes-demo.ngrok.app/) (ngrok) | A small Kubernetes running in your tab; not real images | Browser | L1–L3 | k8s-architecture |
| [Phippy books](https://www.cncf.io/phippy/) (CNCF) | The illustrated guide to Kubernetes | No input | L0 | k8s-architecture |
| [kube-score](https://kube-score.com/) | Reliability and security advice for a manifest | Browser | L2 | k8s-workloads |
| [Kubernetes YAML Generator](https://k8syaml.com/) (Octopus) | A Deployment from a form: probes, affinity, tolerations, volumes | Not stated | L1–L2 | k8s-workloads, k8s-scheduling-storage |
| [ValidKube](https://validkube.com/) (Komodor) | kubeconform, kubectl-neat, Trivy, Polaris and Kubescape on pasted YAML; stale since 2022 | Server: never a real Secret | L2 | k8s-workloads |
| [NetworkPolicy viewer](https://artturik.github.io/network-policy-viewer/) | A policy drawn as pods, namespaces and ports; last updated 2024 | Probably browser | L2 | k8s-networking |
| [JSONPath evaluator](https://jsonpath.com/) | RFC 9535 paths on JSON; kubectl JSONPath differs (`{}` templates, `range`/`end`) | Not stated | L1–L2 | cka-exam |
| [YAML multiline strings](https://yaml-multiline.info/) | `|` vs `>` and chomping, live | No input | L1 | helm-kustomize, gitlab-ci-advanced, ansible |
| [Helm Playground](https://paulvollmer.net/helm-playground/) | A template rendered by Helm's engine in WASM; may differ from `helm template` | Browser | L2 | helm-kustomize |
| [Hadolint online](https://hadolint.github.io/hadolint/) | Dockerfile lint, ShellCheck on RUN lines | Browser | L1–L2 | dockerfile |
| [Registry Explorer](https://explore.ggcr.dev/) | A public image's manifest, layers and files | Public images only | L2–L3 | dockerfile, harbor-ops |
| [Composerize](https://www.composerize.com/) | `docker run` to Compose; links Decomposerize and Composeverter | Not stated | L1 | docker-basics |
| [Docker2Kube](https://docker2kube.app.enting.org/) | Compose or `docker run` to Kubernetes manifests | Not stated | L1–L2 | compose-volumes |
| [Kompose](https://kompose.io/) | The official Compose-to-Kubernetes converter (install) | Local | L2 | compose-volumes |
| [OpsGraph](https://opsgraph.pages.dev/) | Draws CI pipelines (GitLab, Actions, Jenkins), Kubernetes manifests, Compose and Terraform | Browser; share links encode the file | L1–L2 | ci-debugging, jenkins, compose-volumes |
| [actionlint playground](https://rhysd.github.io/actionlint/) | GitHub Actions workflow errors | Browser | L1–L2 | gitops-argocd |
| [Argo CD demo](https://cd.apps.argoproj.io/) | A live Argo CD with Healthy, Degraded and OutOfSync apps | Read-only, no login | L1–L2 | gitops-argocd, deployment-strategies |
| [Terraform Visual](https://hieven.github.io/terraform-visual/) | A plan JSON as a graph | Read in the browser, but real plans hold resolved secrets: lab plans only | L2 | terraform |
| [HCL Playground](https://hcl-playground.com/) | Terraform and OpenTofu expressions evaluated | Server | L2 | terraform-opentofu |
| [Live Jinja](https://keshav-madhav.github.io/live_jinja/) | Jinja2 in your tab; no Ansible filters | Browser | L1–L2 | ansible |
| [Ansible Template Tester](https://ansible.sivel.net/test/) | Renders with Ansible's own templating; stuck on "Loading" when checked | Server | L2 | ansible-practice |
| [OTelBin](https://www.otelbin.io/) | OpenTelemetry Collector config validated and drawn as a pipeline | Browser-only mode by default; Share publishes | L2–L3 | logs-loki |
| [VictoriaMetrics playground](https://play.victoriametrics.com/) | MetricsQL over a live cluster, with query trace and relabel tools; MetricsQL ≠ PromQL | Their data, your queries | L2–L3 | prometheus-grafana |
| [VictoriaLogs playground](https://play-vmlogs.victoriametrics.com/) | LogsQL over live Kubernetes logs; LogsQL ≠ LogQL | Their data, your queries | L2 | logs-loki |
| [Kubesec](https://kubesec.io/) | Manifest security scoring; use the CLI, the hosted API receives your file | Local CLI | L2 | k8s-workloads |

The jq playground and crontab.guru are in the Linux table.

### Cloud, security, data and design

| Tool | What it shows you | Data safety | Level | Topics |
|---|---|---|---|---|
| [AWS Pricing Calculator](https://calculator.aws/) ◇ | Official cost estimates, exportable; no account | Saved estimates go to AWS public servers | L1–L4 | cloud-concepts, cloud-architecture |
| [instances.vantage.sh](https://instances.vantage.sh/) | Every EC2 type with specs and prices; RDS, Azure and GCP tabs | No input | L1–L4 | aws-iam-ec2, cloud-architecture |
| [aws.permissions.cloud](https://aws.permissions.cloud/) | Every IAM action, its resources and conditions; risky managed policies | Not stated | L2–L3 | aws-iam-ec2 |
| [gcp.permissions.cloud](https://gcp.permissions.cloud/) ◇ | The same for Google Cloud roles (data did not render when checked) | Not stated | L2–L3 | cloud-concepts |
| [OpenReplay IAM policy explainer](https://openreplay.com/tools/iam-policy-explainer/) | A policy or trust policy in plain English, wildcards flagged | Browser | L1–L2 | aws-iam-ec2, object-storage-minio |
| [AWS Policy Generator](https://awspolicygen.s3.amazonaws.com/policygen.html) ◇ | IAM, S3, SNS, SQS and VPC endpoint policies from a form | No account | L1 | aws-iam-ec2 |
| [Azure Charts](https://azurecharts.com/) | Azure services, regions, latency and retirements | No input | L1–L3 | cloud-concepts |
| [CloudPing.co](https://www.cloudping.co/) | Latency between AWS regions, p10 to p99 | No input | L3–L4 | availability-dr |
| [diagrams.net](https://app.diagrams.net/) | Diagrams with AWS and Azure shape libraries | Saved where you choose | L1–L4 | cloud-architecture, postmortems |
| [samwho.dev Load Balancing](https://samwho.dev/load-balancing/) | Round robin, least connections and PEWMA, with drops and p99 | No input | L2–L3 | aws-vpc-alb, availability-dr |
| [Interactive latency numbers](https://colin-scott.github.io/personal_website/research/interactive_latency.html) | Cache, RAM, SSD, disk and network by year; extrapolated after about 2014 | No input | L1–L2 | slow-system |
| [The Secret Lives of Data: Raft](https://thesecretlivesofdata.com/raft/) ◇ | Leader election and log replication, guided | No input | L2 | db-ha, kubeadm-cluster |
| [RaftScope](https://raft.github.io/) | A five-server Raft cluster you can poke | No input | L3 | db-ha |
| [Consistent hash ring demo](https://gallery.selfboot.cn/en/algorithms/hashring) | Nodes and virtual nodes on a ring; which keys move | No input | L3 | object-storage-minio |
| [Aiven Kafka visualization](https://aiven.io/tools/kafka-visualization) | Partitions, replicas and consumer groups in motion | No input | L2–L3 | oss-toolbox |
| [db<>fiddle](https://dbfiddle.uk/) | SQL on PostgreSQL 8.4–19, MySQL, MariaDB, SQL Server, Redis, Valkey and more | Server: lab data only | L1–L3 | db-basics |
| [SQL Fiddle](https://sqlfiddle.com/) | A smaller SQL playground; prefer db<>fiddle | Server | L1 | db-basics |
| [Redis Sandbox](https://redis.io/try/sandbox/) | Redis commands on sample data, no account | Server | L1–L2 | db-basics |
| [explain.dalibo.com](https://explain.dalibo.com/) | A PostgreSQL EXPLAIN plan as a tree | Server stores it (delete offered; offline pev2 file exists) | L2–L3 | db-incidents |
| [explain.depesz.com](https://explain.depesz.com/) | EXPLAIN ANALYZE with slow nodes highlighted | Server stores it; obfuscate option | L2–L3 | db-incidents |
| [MySQL EXPLAIN visualiser](https://mysqlexplain.com/) | A visual MySQL plan | Not stated | L2–L3 | db-incidents |
| [PGTune](https://pgtune.leopard.in.ua/) | Starting postgresql.conf memory, parallelism and WAL settings | Not stated, harmless | L2 | db-incidents |
| [CyberChef](https://gchq.github.io/CyberChef/) | Chained decoding: base64, hex, hashes, PEM | Browser | L1–L3 | secrets, private-ca, security-response |
| [jwt.ms](https://jwt.ms/) | A JWT decoded with its claims explained | Browser; test or expired tokens only | L2–L3 | vault-sso |
| [jwt.io](https://www.jwt.io/) | Decode, verify and generate JWTs | Not stated: never paste real JWTs into jwt.io | L2 | vault-sso |
| [FIRST EPSS](https://www.first.org/epss/) | The daily chance each CVE is exploited within 30 days | API and CSV | L2–L4 | container-hardening |
| [Vulnerability-Lookup](https://vulnerability.circl.lu/) (CIRCL) | CVEs with advisories, sightings and KEV lists | No input | L2–L4 | security-response, wazuh-siem |
| [OSV.dev](https://osv.dev/) | Vulnerabilities by package and ecosystem | Query only | L2 | container-hardening |
| [CycloneDX Sunshine](https://cyclonedx.github.io/Sunshine/) | An SBOM's components and CVEs, with EPSS and KEV | Browser | L2–L3 | container-hardening |
| [Rekor Search](https://search.sigstore.dev/) (Sigstore) | Entries in the public signing log | Public: keyless signing publishes the signer's email | L3 | aws-platform |
| [CSP Evaluator](https://csp-evaluator.withgoogle.com/) (Google) | Weaknesses and bypasses in a Content-Security-Policy | Not stated | L2–L3 | milestone-senior |
| [OWASP Threat Dragon](https://www.threatdragon.com/docs/) ◇ | Data-flow threat models with STRIDE and LINDDUN (desktop app or self-hosted) | Local | L3–L4 | security-response |
| [ByteByteGo guides](https://bytebytego.com/guides/) | About 400 illustrated system-design explainers; not interactive | No input | L2–L4 | cloud-architecture |

Left out: Cloudcraft (now needs a Datadog account). Reachable but not confirmed: the Rego Playground (its Publish makes a public link), the Azure Pricing Calculator, DB Fiddle and the CVSS 4.0 calculator.

---

## 18. Where to go next

- Place yourself on the [Career ladder](40-career-ladder.md), then follow the [Roadmap](34-roadmap.md) for the order of topics. Section 14 above tells you what to practise each week at that level.
- Use [Learning with KodeKloud](40-career-ladder.md#9-learning-with-kodekloud) for the lessons behind each practice block, and come back here for the reps.
- Turn the practice log into proof with [Building proof](40-career-ladder.md#10-building-proof): a public repository of sanitised notes, scripts and small projects.
- Feed your own incidents back into practice. Every real outage becomes a Wheel of Misfortune scenario, and every five-line note can become a lab that breaks the same thing on a VM.
- When the sites get easy, build scenarios for others. Writing a script that breaks a VM in a realistic way, and a hint list for it, is the L4 skill behind the game day in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md#8-l4-exit-test-the-game-day).
- Mark December: SadServers' [Advent of Sysadmin](https://sadservers.com/advent), DevOps Daily's [Advent of DevOps](https://devops-daily.com/advent-of-devops) and the SANS Holiday Hack all run then.
- Check this list every quarter. Free tiers shrink, prices change and playgrounds close, as section 16 shows. When a link dies, look for the replacement the site itself recommends before you trust a random alternative.
- Check more than the HTTP status. On 7 November 2026 two Wiz CTF domains had gone dark while Wiz's own hub still advertised them, and Play with Docker still answered HTTP 200 eight months after it shut down. Test DNS, read the page, and record a dated "unreachable, re-check" label before you move anything to section 16.

### Catalogs to find more

Short, focused lists beat the giant awesome-lists for finding practice sites. Even good lists keep
dead entries, so treat every entry as a lead to verify. Stars and last push as of 7 Nov 2026.

| Catalog | What to mine | Verdict |
|---|---|---|
| [wargame-nexus](https://github.com/zardus/wargame-nexus) · 1,360 stars · pushed 25 Oct 2026 | The Cloud, Blue Team/DFIR and "Not Security" sections (CMD Challenge, SadServers, Under The Wire, Protohackers), with badges for offline and dead sites | The best liveness tracker; leans towards security |
| [Awesome-CloudSec-Labs](https://github.com/iknowjason/Awesome-CloudSec-Labs) · 2,210 stars · pushed 1 Oct 2025 | AWS, Azure, GCP, Kubernetes, container, Terraform, CI/CD and PaaS labs, each tagged hosted or self-hosted | The best cloud-security catalog, but no push in 13 months |
| [awesome-docker, "Where to Start"](https://github.com/veggiemonk/awesome-docker) · 37,190 stars · pushed 4 Nov 2026 | Docker katas, DevOps Daily's Docker simulator, Dockerlings | Good; still lists Play with Docker |
| [awesome-kubernetes, interactive environments](https://github.com/ramitsurana/awesome-kubernetes/blob/master/docs/learning-resources/interactive-environments.md) · 16,139 stars · pushed 31 Oct 2026 | Meshery Playground and other hosted clusters | Good; still lists dead and offline sites |
| [awesome-k8s-security](https://github.com/magnologan/awesome-k8s-security) · 2,008 stars · pushed 6 Nov 2026 | The Trainings and Learning sections | Active; links some dead brands |
| [awesome-cyber-skills](https://github.com/joe-shenouda/awesome-cyber-skills) · 4,781 stars · pushed 17 Sep 2026 | 120 entries with a category column (Cloud, System/Network, Blue Team) | Useful; many old VMs |
| [resilience-engineering](https://github.com/lorin/resilience-engineering) · pushed 31 Oct 2026 | Lorin Hochstein's reading list on resilience engineering | L4 reading, not practice |
| [DevOpsCube: websites to practise DevOps](https://devopscube.com/websites-to-practice-devops/) · 15 Feb 2026 | Free-tier limits for Killercoda, iximiuz, SadServers and others | The best roundup outside GitHub |

free-for-dev and awesome-sysadmin are maintained but catalogue free infrastructure and software,
not practice sites, so they are not worth mining for this module.
