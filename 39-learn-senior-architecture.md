# 39 — Learn: Senior DevOps — Architecture, Reliability & Leadership

This is the module that turns the rest of the handbook into a career. Modules 27 to 38 teach you to
operate systems and fix them when they break. This one covers what a senior engineer adds on top of
that: **designing** systems that fail small, **deciding** between options in writing, and **leading**
people through incidents, migrations and change. It is built around your real platform: on-prem
Ubuntu 22.04/24.04 hosts with netplan, systemd-resolved and UFW/nftables, Apache moved to ports
81/444, Dokploy running Traefik v3 on Docker Swarm with `dokploy-network`, GitLab CI pushing to a
Harbor registry behind a private CA, a kubeadm homelab on the CKA track, and AWS. Every exercise here
is one you could present at work on Monday.

Seniority is not a longer list of tools. A senior engineer and a mid-level engineer often know the
same commands. What differs is the question they ask first. The mid-level engineer asks "which
layer is broken?". The senior engineer asks "why could this layer break the whole platform, why
did we find out from a customer, and what change makes this whole class of failure impossible?".
This module trains that second question, from your first year onward.

> All sample outputs are illustrative: Ubuntu 22.04/24.04, Docker Engine 27–29, Traefik v3,
> PostgreSQL 16, MySQL 8, AWS CLI v2. Public addresses use the documentation ranges (192.0.2.0/24,
> 198.51.100.0/24, 203.0.113.0/24), lab VMs use 192.168.56.0/24, the AWS account is 123456789012
> and names are under example.com. UPPERCASE words in commands are placeholders: HOST, SERVICE,
> PROJECT_ID, NODE, CONTAINER, DATE. Every lab runs on a test VM or a sandbox AWS account, never on
> a work server.

---

## 0. How to use this module

### Who this module is for

The handbook uses one career scale everywhere. Each topic in this module carries a tag such as
**[L2 · Mid]**. The tag marks the stage at which you should **start practising** the topic, not
the stage at which you master it. Seniors still use L1 skills every day, and a fresher who writes a
clean runbook is already doing senior work on a small scale.

| Stage | Experience | Ops Ladder level | Tag | What you take from this module |
|---|---|---|---|---|
| Fresher | 0–1 yr | L0 Foundations | [L0 · Fresher] | The words seniors use (blast radius, SPOF, RPO, SLO) so design meetings make sense; how to be an excellent scribe during an incident |
| Junior | 1–2 yrs | L1 Operator | [L1 · Junior] | Dependency maps of the hosts you run, backups you have actually restored, runbooks someone else can follow |
| Mid-level | 2–4 yrs | L2 Troubleshooter | [L2 · Mid] | Failure domains, availability maths, timeouts and retries, postmortems, change requests, reviewing infra changes |
| Senior | 4–7 yrs | L3 Platform | [L3 · Senior] | Reference architectures, DR, capacity, cost, platform engineering, migrations, ADRs, mentoring |
| Senior / Lead / SRE | 5+ yrs | L4 SRE | [L4 · Lead/SRE] | SLO negotiation, incident command, on-call design, build vs buy, eliminating classes of incidents |

The years are typical, not rules. People move up the ladder by producing the evidence listed in the
last column, not by waiting. [Career ladder](40-career-ladder.md) covers promotion evidence,
interviews and the portfolio. This module covers the technical and leadership content behind them.

### What senior means in one picture

```
 Fresher (L0)     Junior (L1)      Mid-level (L2)      Senior (L3)          Lead / SRE (L4)
 ┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐
 │ one task │ ─▶ │ one host, │ ─▶ │ one incident │ ─▶ │ one system or │ ─▶ │ platform, team, │
 │          │    │ one       │    │ across many  │    │ platform, its │    │ the practices   │
 │          │    │ service   │    │ layers       │    │ whole design  │    │ of the org      │
 └──────────┘    └───────────┘    └──────────────┘    └───────────────┘    └─────────────────┘
 "How do I       "Is it up?       "Which layer is     "How should it       "How do we make
  run this?"      Why not?"        broken, and how     work, and what       this class of
                                   do I prove it?"     happens when it      problem stop
                                                       fails?"              happening?"
 Output:         Output:          Output:             Output:              Output:
 a done ticket   a working host   a fix + evidence    a design + ADR       a practice others
                 + a runbook      + a postmortem      + a migration plan   adopt (SLOs, IC)
```

Read it left to right. Each step widens the **scope** (how much of the system you are responsible
for), the **ambiguity** you can handle (how vague the request can be before you need help) and the
**leverage** of your output (how many people benefit from one piece of your work).

### Learning path

The areas are grouped by subject so the module also works as a reference. To learn it in order,
follow this path. Steps marked with a stage below yours are quick reads; the steps at your stage
are where your real hours go.

| # | Topic | Tag | Section | Why at this point |
|---|---|---|---|---|
| 1 | The stage ladder | [L0 · Fresher] | 1 | Know where you are and what the next stage expects |
| 2 | Single points of failure | [L1 · Junior] | 2 | The first design skill: spot what has no spare |
| 3 | Dependency maps | [L1 · Junior] | 2 | You cannot protect what you have not drawn |
| 4 | Backup strategy | [L1 · Junior] | 5 | A junior who has restored a backup is worth two who have configured one |
| 5 | Runbooks others can follow | [L1 · Junior] | 12 | Your first leverage: work that helps someone at 2am |
| 6 | Failure domains and blast radius | [L2 · Mid] | 2 | The vocabulary of every design review |
| 7 | Availability maths, N+1 | [L2 · Mid] | 3 | Numbers instead of opinions |
| 8 | Health checks, timeouts, retries | [L2 · Mid] | 3 | Most cascading outages start here |
| 9 | RPO and RTO | [L2 · Mid] | 5 | The two numbers every DR plan is built on |
| 10 | Postmortems, change management, infra reviews | [L2 · Mid] | 11, 12 | Mid-level engineers write these; seniors run the process |
| 11 | Today's single Dokploy host | [L2 · Mid] | 4 | Know the baseline before you redesign it |
| 12 | Idempotency, queues, caching, degradation | [L3 · Senior] | 3 | Patterns that let parts fail without the whole failing |
| 13 | On-prem HA and AWS reference architectures | [L3 · Senior] | 4 | Your platform, evolved |
| 14 | DR tiers, capacity, performance budgets | [L3 · Senior] | 5, 6 | Planning ahead instead of reacting |
| 15 | Cost and FinOps | [L3 · Senior] | 7 | Every design is also a bill |
| 16 | Platform engineering and paved-road CI | [L3 · Senior] | 8 | Scale yourself through other teams |
| 17 | Strangler pattern, Apache → Dokploy migration | [L3 · Senior] | 9 | Your real migration, done the senior way |
| 18 | ADRs, design docs, trade-offs | [L3 · Senior] | 10 | Decisions that survive you leaving the room |
| 19 | Mentoring, estimating, saying no, communication | [L3 · Senior] | 12 | Technical leadership without a manager title |
| 20 | Security ownership, DORA metrics | [L3 · Senior] | 13, 14 | Owning outcomes, not tasks |
| 21 | System-level troubleshooting, contributing factors | [L3 · Senior] | 15 | Troubleshooting past the first root cause |
| 22 | SLOs, incident command, on-call design | [L4 · Lead/SRE] | 11 | Reliability as a practice the team runs |
| 23 | Hybrid DR, game days, platform as a product, build vs buy, compliance evidence | [L4 · Lead/SRE] | 4, 5, 8, 10, 13 | Org-level decisions |
| 24 | Eliminating classes of incidents | [L4 · Lead/SRE] | 15 | The senior troubleshooting goal |
| 25 | Senior scenario exercises | [L3 · Senior] to [L4 · Lead/SRE] | 16 | Practise the interview and the real job |
| 26 | Self-check and exit tests | all stages | 17 | Prove the stage, then move up |

### Study method

The other learn modules end every topic with a lab on a VM. Here about half the labs also produce
a **document**: an ADR, a runbook, a postmortem, a design doc, a change request. That is
deliberate. At senior level the written artefact is the work product; the commands are how you
gather the evidence for it.

For each ### topic, follow these steps in order:

1. **Read the handbook note** (15–20 minutes): concept, key terms, the "See it" commands. Write down the two or three ideas you could not explain to someone else yet.
2. **Do the KodeKloud pointer** from the 📚 Study path line at the top of the area, or the official doc named in the topic. For this module the main course is KodeKloud *Fundamentals of SRE* (see the route table below).
3. **Optional video**, only if a concept still feels fuzzy. Stop as soon as it clicks.
4. **Hands-on lab** on the homelab or the sandbox AWS account: build it, break it on purpose, fix it.
5. **Write the artefact** the topic asks for and get it reviewed, by a colleague or by yourself after 48 hours. Rewrite until a junior could act on it without asking you a question.
6. **Teach it.** Explain the topic to a junior, or write a 200-word summary in your public runbook repo. Teaching is the skill this module trains most, because it is the skill that makes a senior.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time.

> Timebox. One topic per morning slot (30–45 minutes) or one evening block. Until your CKA exam,
> CKA sessions come first; this module runs on the morning rep and the Sunday postmortem reading.

### KodeKloud route for this module

KodeKloud has no single "senior DevOps" course. This is the shortest verified route through what
it does have, in order, with the handbook note to read before each one.

| Order | First this (KodeKloud) | Then this | Then this handbook note | Then this lab |
|---|---|---|---|---|
| 1 | [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre): Service Level Objectives and Measurements | Google SRE book chapters from the [table of contents](https://sre.google/sre-book/table-of-contents/) on SLOs | Section 11, SLOs | Write an SLO and burn-rate alert for one Dokploy app |
| 2 | Fundamentals of SRE: Incident Management (IMAG roles, [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page), [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page)) | [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) | Sections 11 and 15 | Ops Ladder L4 game day with a written postmortem |
| 3 | Fundamentals of SRE: Managing Complexity, Risk and Toil ([Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page), capacity planning) | [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/) | Sections 6 and 11 | Change request for disabling system Apache |
| 4 | [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course): Docker Swarm, High Availability/Quorum and Disaster Recovery lessons | [Swarm tutorial](https://docs.docker.com/engine/swarm/swarm-tutorial/) | Section 4 | Three-manager Swarm, kill one node |
| 5 | [Prep Course - Prometheus Certified Associate](https://kodekloud.com/courses/prometheus-certified-associate-pca): Alerting | [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) | Sections 6 and 11 | Disk-fill forecast and SLO alerts |
| 6 | [GitLab CI/CD](https://kodekloud.com/courses/gitlab-ci-cd): Optimization, Security and Monitoring (extends, templates) | [GitLab CI quick start](https://docs.gitlab.com/ci/quick_start/) | Section 8 | A paved-road CI component used by two projects |
| 7 | [AWS Networking Fundamentals](https://kodekloud.com/courses/aws-networking-fundamentals), then [CloudOps Engineer - Associate](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate): Reliability and Cost/Performance domains | [AWS docs](https://docs.aws.amazon.com/): the Well-Architected Framework reliability and cost pillars | Sections 4, 5, 7 | Two-AZ ALB lab in the sandbox account |
| 8 | [Ansible Basics](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course): Playbooks, Handlers and Roles | [Ansible 101](https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN) | Exercise 2 in section 16 | Roll a CA file to all lab nodes with `serial` |

For daily reps, [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) and the
[KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) fill the
morning slot when the homelab is busy.

### Lab environment

Most labs need more than one machine, because high availability cannot be practised on one host.

| VM | Role | IP | Size |
|---|---|---|---|
| dok-01 | Swarm manager, Dokploy, Traefik | 192.168.56.11 | 2 vCPU, 4 GB, 40 GB |
| dok-02 | Swarm manager | 192.168.56.12 | 2 vCPU, 4 GB, 40 GB |
| dok-03 | Swarm manager | 192.168.56.13 | 2 vCPU, 4 GB, 40 GB |
| db-01 | PostgreSQL 16 primary | 192.168.56.21 | 2 vCPU, 2 GB, 30 GB |
| db-02 | PostgreSQL 16 replica | 192.168.56.22 | 2 vCPU, 2 GB, 30 GB |
| mon-01 | Prometheus, Alertmanager, Grafana, blackbox_exporter, backup repo | 192.168.56.30 | 2 vCPU, 4 GB, 60 GB |

The minimum is three VMs (dok-01, dok-02, mon-01): you can still run every two-node lab and put the
database containers on dok-02. Take a snapshot of every VM after the base install, so each "break
it" step can be undone in seconds.

**AWS sandbox.** Use a separate account (or at least a separate region and tag) with a budget
alarm set **before** you create anything, and delete every lab resource the same day.
[Cloud & AWS](36-learn-cloud-aws.md) covers the account set-up and budget alarm.

**Where your real platform appears.** Production examples use 192.0.2.10 for the current Dokploy
host (dok-prod-01), 203.0.113.10 for the public address NATed to it, 192.0.2.53 for the internal
DNS server and harbor.example.com for the registry.

---

## 1. What makes a senior

> 📚 **Study path:** 1) Note: [Career ladder](40-career-ladder.md) section 1 (The career map), so the stages below have a frame · 2) KodeKloud: *Fundamentals of SRE* — its opening lessons on what SRE is and how the role works ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Read: Google SRE book chapter 1, *Introduction*, from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 4) Practice: the evidence-file and three-verbs labs below (no VM needed).

**Who starts here:** everyone, on day one. Freshers read it to see the road; seniors re-read it
when they write a promotion case or mentor someone.

### The stage ladder [L0 · Fresher]

**Concept.** Each career stage is defined by what you can be trusted with **without supervision**,
not by the tools you know. A fresher can be trusted with a well-defined task. A senior can be
trusted with a vague problem ("the platform keeps falling over", "the cloud bill is too high") and
will come back with a framed problem, options, a recommendation, a plan and the people needed to
carry it out.

| Dimension | Fresher [L0] | Junior [L1] | Mid-level [L2] | Senior [L3] | Lead/SRE [L4] |
|---|---|---|---|---|---|
| Typical request | "Restart the service" | "Set up monitoring on this host" | "The site is slow, find out why" | "Make the platform survive a node failure" | "Incidents keep happening, fix how we work" |
| Scope | One task | One host or service | One incident across layers | One system end to end | Several systems and the team's practices |
| Ambiguity handled | None: needs exact steps | Some: needs the goal | A symptom | A business problem | An organisational problem |
| Main output | A done ticket | A working, documented host | A fix with evidence, a postmortem | A design, an ADR, a migration plan | A practice others adopt |
| Failure mode at this stage | Changes things without understanding them | Fixes the symptom, not the cause | Becomes the hero who fixes everything personally | Designs alone, then surprises everyone | Process for its own sake |
| Ready for the next stage when | Asks good questions and writes things down | Others use their runbooks | Their postmortems change how the team works | Their designs are built by others without them | Incidents of a whole class stop |

**Key terms**

| Term | Meaning |
|---|---|
| Scope | How much of the system you are accountable for |
| Leverage | How many people or systems benefit from one piece of your work |
| Ambiguity | How vague a request can be before you need someone to define it for you |
| Artefact | A written output others can use without you: runbook, ADR, design doc, postmortem |
| Bus factor | How many people would have to disappear before a system becomes unmaintainable |

**See it on a real system.** Your Git history is an honest record of your current stage. Count
what you change and what you write down:

```bash
cd ~/work/infra
git shortlog -sn --since="12 months ago" -- ansible/ compose/ traefik/
git log --since="12 months ago" --author="Sam" --oneline -- docs/ runbooks/ adr/ postmortems/ | wc -l
git log --since="12 months ago" --author="Sam" --oneline | wc -l
```

```
   212  Sam
     9  Ravi
     3  Priya
14
231
```

→ Two things jump out. First, one person made 94% of infrastructure changes: the **bus factor is
one**, which is a single point of failure made of people (section 2 treats it like any other SPOF).
Second, only 14 of 231 commits produced something written that others can use. A senior's ratio is
very different: fewer commits, more of them documents and reviews that let others make the changes.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Create a private "evidence file" (some people call it a brag document):
one Markdown file with a section per quarter. For each piece of work, write the problem, what you
did, the outcome in numbers (minutes of downtime avoided, hours saved, euros or rupees saved) and
a link to the artefact.

**Step 2 — Break it.** Read the file as if you were a hiring manager who has never met you. Mark
every line that says what you did but not why it mattered ("configured Traefik" instead of "moved
10 sites behind one proxy, freeing 80/443 for Dokploy with zero downtime").

**Step 3 — Fix it.** Rewrite every marked line as problem → action → measurable outcome, then map
each line to a column of the table above. The column where most lines land is your real stage.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Hero mode | You are paged for everything; nobody else can fix the platform | `git shortlog -sn` on infra repos; count incidents only you resolved | Mentoring and runbooks, section 12 |
| Ticket-taker | You finish tasks but never question whether they are the right tasks | Ask "what problem does this solve?" on the next three tickets | Saying no with alternatives, section 12 |
| Architecture astronaut | Designs nobody asked for, never shipped | Count designs that reached production | Strangler pattern, section 9 |
| Invisible work | Good work nobody knows about | Evidence file empty for a quarter | [Career ladder](40-career-ladder.md) |

**Why it matters for troubleshooting.** Every incident you resolve alone teaches one person. Every
incident you resolve with a runbook, a postmortem and a fixed class of failure teaches the whole
team. The technical skill is the same; the stage is defined by what you leave behind.

**Next step:** learn the three verbs that every senior artefact is built on.

### Designing, deciding, leading [L2 · Mid]

**Concept.** Almost everything in this module falls under one of three verbs:

```
                 ┌──────────────────────────────────────────────┐
                 │                 SENIOR WORK                  │
                 └──────────────────────────────────────────────┘
        ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
        │   DESIGNING    │   │   DECIDING     │   │    LEADING     │
        │ how it should  │   │ which option,  │   │ getting people │
        │ work and fail  │   │ written down,  │   │ to carry it    │
        │                │   │ with trade-offs│   │ out, calmly    │
        └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
   artefacts:   │                    │                    │
        reference diagrams     ADRs, design docs    incident command, postmortems,
        failure-domain maps    trade-off tables     change requests, runbooks,
        DR plans, capacity     build vs buy         mentoring, stakeholder updates
        plans, SLOs            risk registers       migration communication plans
```

**Designing** means deciding how the system behaves on its worst day, not its best one.
**Deciding** means choosing between options that all have costs, and writing down why so the
decision outlives the meeting. **Leading** means other people do the work well because of you:
they know their role in an incident, they can follow your runbook, they understand the migration
plan.

**Key terms:** design review, decision record, stakeholder (anyone affected by the change who is
not doing it), sponsor (the person who can approve the cost), RACI (Responsible, Accountable,
Consulted, Informed).

**See it on a real system.** Look at your last real change, the Apache move to 81/444, and ask
which of the three verbs it contained:

```bash
sudo apachectl -S 2>/dev/null | grep -E 'port (81|444)'
ls ~/work/infra/docs/adr/ ~/work/infra/runbooks/
grep -rl "81\|444" ~/work/infra/docs/ 2>/dev/null | head
```

```
         port 81 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.conf:1)
         port 81 namevhost blog.example.com (/etc/apache2/sites-enabled/blog.conf:1)
         port 444 namevhost shop.example.com (/etc/apache2/sites-enabled/shop-ssl.conf:2)
ls: cannot access '/home/ops/work/infra/docs/adr/': No such file or directory
/home/ops/work/infra/runbooks:
apache-restart.md
```

→ The change was **designed** (ports chosen to avoid a clash) and **executed**, but nothing records
the **decision** (why Traefik becomes the edge, what was rejected) and nobody else could repeat it
from the runbook directory. That gap is exactly what sections 9, 10 and 12 close.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Take one piece of work you did in the last three months. Write one paragraph
for each verb: what you designed, what you decided (and what you rejected), whom you led or
informed.

**Step 2 — Break it.** Hand it to a colleague (or a friend outside IT) and ask them to tell you
back, in their words, *why* the decision was made. If they cannot, the decision lived only in your
head.

**Step 3 — Fix it.** Turn the "deciding" paragraph into a short ADR using the template in
section 10. Keep it; it becomes the first entry in your `docs/adr/` directory.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Design without decision record | "Why is Apache on 81?" asked every few months | Write the ADR now, dated to the original decision | Section 10 |
| Decision without design | Chosen tool fails its first node failure | Draw the failure-domain map before choosing | Section 2 |
| Design and decision without leading | Nobody else can operate it; you get every page | Runbook + handover session | Section 12 |

**Why it matters for troubleshooting.** Half of a hard incident is archaeology: why is it built
like this, what depends on what, who decided. When the design, decision and runbook exist, the
on-call engineer skips the archaeology and goes straight to evidence.

**Next step:** the first design skill, thinking in systems.

---

## 2. Thinking in systems

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil, for the risk vocabulary ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: [Site down](25-playbook-site-down.md), whose layered walk is a dependency map in action, and [DNS](08-dns.md) for the resolver lab · 3) KodeKloud: *Docker Certified Associate* — Docker Swarm ([Section Introduction](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction)) for nodes, managers and services before the three-node lab ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) Read: Google SRE book chapter 22, *Addressing Cascading Failures*, from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 5) Practice: the resolver SPOF lab on dok-01, the dependency map of dok-prod-01, then the failure-domain lab on the three-node Swarm.

**Who starts here:** juniors learn to list single points of failure and draw dependency maps;
mid-level engineers add failure domains and blast radius; seniors use all three in every design
review.

### Single points of failure [L1 · Junior]

**Concept.** A **single point of failure (SPOF)** is any component whose failure, on its own,
stops the service. Beginners look for SPOFs among servers. Seniors look everywhere, and sort them
by **when** they hurt:

| SPOF type | Hurts when | Examples on your platform |
|---|---|---|
| Runtime | Traffic stops right now | The only Dokploy host, the only Traefik, the only internal DNS server 192.0.2.53, the only default gateway, the only database |
| Deploy-time | You cannot change anything, including the fix | Harbor (no pulls, no pushes), GitLab and its runners, the Dokploy UI, the one person with SSH keys |
| Recovery-time | You cannot rebuild after a failure | Backups on the same disk or host, Harbor running on the cluster it must rebuild, the only copy of the private CA key, the credentials in one password manager vault |
| Slow-burn | Breaks on a date, not by accident | A certificate or CA expiring, a domain registration, a licence, a disk filling at 1% a day |

A deploy-time SPOF feels harmless until the day you need to deploy a fix during an outage. A
recovery-time SPOF feels harmless until the day you need to recover. That is why seniors list all
four types, not just the first.

**Key terms**

| Term | Meaning |
|---|---|
| SPOF | One component whose failure alone causes an outage |
| Redundancy | A spare that can take over the work (section 3) |
| Shared fate | Two "redundant" parts that fail together because they share something (section below) |
| Bus factor | The SPOF made of people: knowledge only one person has |

**See it on a real system.** Five read-only checks find most runtime SPOFs on a Dokploy host:

```bash
resolvectl dns                                     # how many DNS servers?
ip route show default                              # how many default routes?
timedatectl timesync-status | grep -E 'Server|Poll'
docker node ls                                     # how many Swarm nodes and managers?
docker service ls --format '{{.Name}}\t{{.Replicas}}'
```

```
Global:
Link 2 (ens18): 192.0.2.53
default via 192.0.2.1 dev ens18 proto static
       Server: 192.0.2.123 (ntp.example.com)
Poll interval: 34min 8s (min: 32s; max 34min 8s)
ID                            HOSTNAME      STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
q1w2e3r4t5y6u7i8o9p0a1s2d *   dok-prod-01   Ready     Active         Leader           28.3.3
shop-web-1a2b3c	1/1
blog-web-4d5e6f	1/1
shop-db-7g8h9i	1/1
```

→ One DNS server, one gateway, one NTP server, one Swarm node, every service with one replica,
and the database living on the same host as the apps. None of this is wrong for a small
platform, but every line is a SPOF and should appear in the risk register (section 9) with a
decision: fix it, or accept it and write down the recovery time.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** On dok-01, run a container that needs DNS at runtime:

```bash
docker run -d --name needs-dns --restart unless-stopped alpine:3.20 \
  sh -c 'while :; do wget -q -T 3 -O /dev/null https://example.com && echo ok || echo FAIL; sleep 5; done'
docker logs --tail 3 needs-dns
```

**Step 2 — Break it.** Point the host's resolver at an address where nothing answers. This is a
runtime change only; `resolvectl revert` undoes it and a reboot clears it. Restart the container
afterwards, because Docker reads the host's resolver list when a container starts:

```bash
resolvectl dns                                       # note the current server first
sudo resolvectl dns ens18 192.168.56.250             # nothing listens here
docker restart needs-dns                             # picks up the new upstream server
sleep 20; docker logs --tail 3 needs-dns
```

```
ok
FAIL
FAIL
```

→ One resolver gone, and every app that calls an external API fails, even though the apps, the
host and the network are healthy. Docker gives each container the host's upstream servers when it
starts (from `/run/systemd/resolve/resolv.conf` when systemd-resolved is in use), and on a
user-defined network the embedded resolver 127.0.0.11 forwards to those same servers, so every
container inherits the host's SPOF.

**Step 3 — Fix it.** Undo the break, then remove the SPOF permanently with two resolvers in
netplan. Use `netplan try`, which rolls back automatically after 120 seconds unless you confirm,
instead of `netplan apply`, which gives no second chance if you cut yourself off:

```bash
sudo resolvectl revert ens18
sudoedit /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    ens18:
      addresses: [192.168.56.11/24]
      routes:
        - to: default
          via: 192.168.56.1
      nameservers:
        addresses: [192.168.56.53, 192.168.56.54]
        search: [lab.example.com]
```

```bash
sudo netplan try
resolvectl dns
```

On VMs built from a cloud image, cloud-init may rewrite `50-cloud-init.yaml` at boot unless its
network configuration is disabled (look in `/etc/cloud/cloud.cfg.d/`); reboot once to confirm
the change survives. Then list the same two servers in `/etc/docker/daemon.json`
(`"dns": ["192.168.56.53", "192.168.56.54"]`, applied by `sudo systemctl restart docker`) so
containers never fall back to 8.8.8.8, and clean up with `docker rm -f needs-dns`.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Only DNS server down | `Could not resolve host` everywhere, apps "randomly" failing | `resolvectl dns`, `sudo tcpdump -ni any port 53` | [Site down](25-playbook-site-down.md), [DNS](08-dns.md) |
| Only Swarm node down | Every app down at once | `docker node ls` from any surviving manager | [Containers & K8s](26-playbook-containers-k8s.md) |
| Harbor down during an outage | Cannot deploy the fix: `manifest unknown` or TLS errors on pull | `docker pull harbor.example.com/PROJECT/IMAGE:TAG` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Bus factor of one | Incident waits for one person to wake up | Count who resolved the last 10 incidents | Section 12 |

**Why it matters for troubleshooting.** When everything fails at once, the cause is almost always
a shared dependency with no spare. Knowing the SPOF list in advance turns "everything is broken"
into a two-minute check of the five commands above.

**By career stage.** A junior keeps the SPOF list for the hosts they run. A mid-level engineer
adds the deploy-time and recovery-time SPOFs. A senior turns the list into decisions with owners
and dates.

**Next step:** a SPOF list tells you *what* is single; a dependency map tells you *who needs it*.

### Dependency maps [L1 · Junior]

**Concept.** A **dependency map** shows, for one service, everything it needs in order to start,
to serve requests and to be recovered. Draw it before every design discussion, every migration
and every incident review. Classify each dependency:

| Kind | Meaning | Example |
|---|---|---|
| Hard | The service fails if the dependency fails | shop needs PostgreSQL |
| Soft | The service degrades but stays up | shop shows "recommendations unavailable" without Redis |
| Start-up only | Needed to start, not to keep running | Harbor (image pull), Vault or env file at boot |
| Recovery | Needed to rebuild after a failure | Backups, Ansible repo, Harbor, DNS, the CA key |

```
                         ┌─────────────────────┐
  users ── DNS ──▶ NAT ──▶ Traefik (dok-prod-01)│  hard, runtime
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐   start-up: harbor.example.com (image)
                         │   shop (Swarm svc)  │   start-up: env/secrets from Dokploy
                         └──┬──────┬──────┬────┘
                hard ───────┘      │      └──────── soft
                 ▼                 ▼ hard            ▼
         ┌────────────┐   ┌──────────────┐   ┌──────────────┐
         │ PostgreSQL │   │ SMTP relay   │   │ Redis cache  │
         │ 192.0.2.31 │   │ 198.51.100.25│   │ 192.0.2.32   │
         └────────────┘   └──────────────┘   └──────────────┘
  recovery: pgBackRest repo on mon-01 · Ansible repo in GitLab · Harbor · private CA key
```

The dangerous pattern is a **dependency loop**: a component needed to recover the platform that
itself runs on the platform. Examples: Harbor deployed as a Dokploy app (to rebuild the Swarm you
need images, which live in Harbor, which needs the Swarm); monitoring hosted on the platform it
monitors (it dies with the thing it should alert about); the internal DNS server running in a
container on a host that needs DNS to pull that container's image.

**Key terms:** upstream (what I call), downstream (who calls me), hard and soft dependency,
dependency loop, critical path.

**See it on a real system.** Connections show real dependencies, not the ones in the wiki. Host
processes (Apache, PHP-FPM) appear in `ss`; containers live in their own network namespace, so
use connection tracking for them:

```bash
sudo ss -tnpH state established '( dport = :5432 or dport = :6379 or dport = :587 or dport = :443 )'
sudo conntrack -L -p tcp --dport 5432 2>/dev/null | head -3      # package: conntrack
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -tn state established
```

```
0      0      192.0.2.10:41822   192.0.2.31:5432    users:(("php-fpm8.3",pid=2710,fd=11))
0      0      192.0.2.10:39012   198.51.100.25:587  users:(("php-fpm8.3",pid=2710,fd=9))
tcp      6 431999 ESTABLISHED src=172.18.0.7 dst=192.0.2.31 sport=48220 dport=5432 src=192.0.2.31 dst=192.0.2.10 sport=5432 dport=48220 [ASSURED] mark=0 use=1
Recv-Q Send-Q Local Address:Port   Peer Address:Port Process
0      0         172.18.0.7:48220   192.0.2.31:5432
0      0         172.18.0.7:52310   192.0.2.32:6379
0      0         172.18.0.7:60244 203.0.113.80:443
```

→ The legacy PHP app on Apache talks to PostgreSQL and an SMTP relay. The containerised app
(172.18.0.7 is its address on `docker_gwbridge`, the bridge Swarm containers use for traffic that
leaves the overlay; inside `dokploy-network` it has a 10.0.1.x address) talks to PostgreSQL,
Redis and an external API at 203.0.113.80:443,
which nobody had written down. That external API is now a hard dependency until proven soft.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** On dok-02, run a small stack with a hard and a soft dependency:

```bash
mkdir -p ~/lab-deps && cd ~/lab-deps
cat > compose.yaml <<'EOF'
services:
  db:
    image: postgres:16
    environment: { POSTGRES_PASSWORD: labonly }
  cache:
    image: redis:7
  app:
    image: nicolaka/netshoot
    command: sh -c 'while :; do nc -zw2 db 5432 && echo "db ok" || echo "db FAIL"; nc -zw2 cache 6379 && echo "cache ok" || echo "cache FAIL"; sleep 5; done'
    depends_on: [db, cache]
EOF
docker compose up -d && sleep 10 && docker compose logs --tail 2 app
```

**Step 2 — Break it.** Stop each dependency in turn and write down what the *user* would
experience, not just what the log says:

```bash
docker compose stop cache; sleep 10; docker compose logs --tail 2 app
docker compose start cache; docker compose stop db; sleep 10; docker compose logs --tail 2 app
```

**Step 3 — Fix it.** Draw the map for this stack and for one real app (start from the `ss` and
`conntrack` output above), mark each edge hard, soft, start-up or recovery, and circle every
dependency loop. Clean up with `docker compose down -v`. Store the real map in the app's runbook.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Undocumented hard dependency | App 500s while "nothing changed" on our side | `ss`/`conntrack` for unexpected peers, app logs | [Site down](25-playbook-site-down.md) |
| Soft dependency that is secretly hard | Cache outage takes the whole site down | Stop the cache in staging and watch | Section 3, graceful degradation |
| Dependency loop | Cannot rebuild after a host loss | Walk the recovery column of the map | Section 5, DR |

**Why it matters for troubleshooting.** During an incident the map tells you which neighbours to
check and in which order. Without it you rediscover the architecture under pressure, which is the
slowest way to learn it.

**By career stage.** A junior draws the map for one app. A mid-level engineer uses it to scope an
incident. A senior uses it to find dependency loops and change the design so recovery never
depends on the thing being recovered.

**Next step:** group the boxes on the map by what they share, which gives you failure domains.

### Failure domains and blast radius [L2 · Mid]

**Concept.** A **failure domain** is a set of components that fail together because they share
something: a host, a hypervisor, a switch, a power feed, a rack, a datacentre, an AWS
Availability Zone, a region. Shared *logical* things are failure domains too: one configuration
file, one certificate, one DNS zone, one Swarm cluster, one CI pipeline, one AWS account, one
person's credentials. The **blast radius** of a failure is how much breaks when one domain fails.

Two rules follow. First, redundant copies must sit in **different** failure domains; two replicas
on the same hypervisor are one replica with extra steps. Second, make every domain as small as you
can afford, so each failure breaks less.

```
┌ Site: on-prem datacentre dc1 ───────────────────────────────────────────────────┐
│ ┌ Power A / switch sw-01 ───────────────────┐ ┌ Power B / switch sw-02 ────────┐ │
│ │ ┌ Hypervisor hv-01 ─────────────────────┐ │ │ ┌ Hypervisor hv-02 ──────────┐ │ │
│ │ │ dok-prod-01   db-01   harbor-01       │ │ │ │ (spare capacity, unused)   │ │ │
│ │ └───────────────────────────────────────┘ │ │ └────────────────────────────┘ │ │
│ └───────────────────────────────────────────┘ └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
 Logical failure domains that cut across everything above:
   traefik.yml + dynamic/*.yml (all 10 sites)   wildcard cert *.example.com
   DNS zone example.com                         one Swarm cluster, one dokploy-network
   GitLab CI (every deploy)                     one AWS account, one root e-mail address
```

→ Today the whole platform is one failure domain (hv-01), and a single bad line in a Traefik
dynamic file is a logical domain covering all 10 sites.

**Ways to shrink the blast radius**

| Technique | What it limits | On your platform |
|---|---|---|
| Spread replicas across domains | Hardware and hypervisor failures | Swarm placement preference on a node label per hypervisor |
| Separate config per site | A typo affecting everyone | One Traefik dynamic file per site, validated before reload |
| Progressive rollout | A bad change hitting every node | Ansible `serial: 1` then `serial: "25%"`; Swarm `--update-parallelism 1 --update-failure-action rollback` |
| Cells or shards | Overload or bad data spreading | Separate Dokploy servers for internal vs customer apps |
| Separate accounts | A leaked key or a bad IAM change | AWS Organizations: prod, non-prod, sandbox, log archive |
| Quotas and limits | One app starving the others | CPU and memory limits per service, rate limits per router |

**Key terms:** failure domain, blast radius, shared fate, correlated failure, cell, progressive
rollout, anti-affinity (Kubernetes) or placement preference (Swarm).

**See it on a real system.** Check whether "redundant" copies really sit in different domains:

```bash
docker node ls --format '{{.Hostname}}\t{{.ManagerStatus}}\t{{.Availability}}'
docker node inspect --format '{{.Description.Hostname}} {{.Spec.Labels}}' $(docker node ls -q)
docker service ps shop-web-1a2b3c --filter desired-state=running --format '{{.Name}}\t{{.Node}}'
aws ec2 describe-instances --filters Name=tag:app,Values=shop \
  --query 'Reservations[].Instances[].[InstanceId,Placement.AvailabilityZone]' --output text
```

```
dok-01	Leader	Active
dok-02	Reachable	Active
dok-03	Reachable	Active
dok-01 map[hv:hv-a]
dok-02 map[hv:hv-a]
dok-03 map[hv:hv-b]
shop-web-1a2b3c.1	dok-02
shop-web-1a2b3c.2	dok-02
i-0a1b2c3d4e5f60718	ap-south-1a
i-0f9e8d7c6b5a40321	ap-south-1a
```

→ Both shop replicas run on dok-02, and dok-01 and dok-02 share hypervisor hv-a anyway. On AWS
both instances sit in ap-south-1a. Each service "has two replicas" and each would still go down
completely with one hypervisor or one AZ.

A common on-prem cause: Swarm does **not** rebalance running tasks when a node comes back. If
dok-03 was drained for patching, its tasks moved to the other nodes and stay there until the next
update of the service.

**Hands-on lab (test VMs only, three-node Swarm)**

**Step 1 — Build it.** Label the nodes by (pretend) hypervisor and deploy two replicas:

```bash
docker node update --label-add hv=hv-a dok-01
docker node update --label-add hv=hv-a dok-02
docker node update --label-add hv=hv-b dok-03
docker service create --name web --replicas 2 -p 8080:80 nginx:1.27
docker service ps web --filter desired-state=running --format '{{.Name}}\t{{.Node}}'
```

**Step 2 — Break it.** Drain dok-03 (as for patching), bring it back, and look where the replicas
ended up. Then simulate the loss of hypervisor hv-a by stopping Docker on dok-01 and dok-02.
⚠ Stopping Docker on a node stops every container on it; do this on lab VMs only.

```bash
docker node update --availability drain dok-03
docker node update --availability active dok-03
docker service ps web --filter desired-state=running --format '{{.Name}}\t{{.Node}}'
# on dok-01 and dok-02:
sudo systemctl stop docker.socket docker.service
# from your workstation:
curl -s -o /dev/null -w '%{http_code}\n' --max-time 3 http://192.168.56.13:8080/
```

→ With dok-01 and dok-02 down, the Swarm also loses its manager quorum (two of three managers
gone), so it cannot even reschedule `web` onto dok-03. Expect `000` from curl until you restart
Docker on one of them. Losing quorum is itself a failure-domain lesson: managers belong in
different domains too.

**Step 3 — Fix it.** Start Docker again on dok-01 and dok-02, then add a placement preference so
replicas spread across hypervisors. Updating the spec reschedules the tasks:

```bash
sudo systemctl start docker                         # on dok-01 and dok-02
docker service update --placement-pref-add 'spread=node.labels.hv' web
docker service ps web --filter desired-state=running --format '{{.Name}}\t{{.Node}}'
docker service rm web
```

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| All replicas in one domain | "We have two replicas" yet a full outage | `docker service ps SERVICE`, AZ query above | [Containers & K8s](26-playbook-containers-k8s.md) |
| Swarm managers in one domain | `The swarm does not have a leader` after one hypervisor fails | `docker node ls` on a surviving manager | [Containers & K8s](26-playbook-containers-k8s.md) |
| Shared logical domain | One config typo, every site returns 404 | `docker logs --tail 50 dokploy-traefik` | [Site down](25-playbook-site-down.md) |
| Change applied everywhere at once | All nodes broken by one bad Ansible run | `git log -1 --stat` in the Ansible repo | Section 11, change management |

**Why it matters for troubleshooting.** When an incident hits several services, ask "what failure
domain do all the broken things share, and do the healthy things *not* share it?". That one
question finds the cause faster than investigating each broken service separately.

**By career stage.** Mid-level engineers learn to name the domain during an incident. Seniors
design so that no single domain holds all copies of anything important, and record the remaining
shared domains as accepted risks.

**Next step:** put numbers on it: how available can a design be, and what does each spare buy?

---

## 3. Designing for availability

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → [Implement Reverse Proxies and Load Balancers](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page) ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: [Learn: Web servers & proxies](29-learn-webservers-proxies.md) for Traefik services and health checks, and [Performance & observability](32-learn-performance-observability.md) section 15 for the availability numbers · 3) KodeKloud: *Docker Certified Associate* — Docker Swarm services, scaling and the High Availability/Quorum lessons ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) Read: Google SRE book chapters 21 (*Handling Overload*) and 22 (*Addressing Cascading Failures*) from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 5) Practice: the load-balancer lab on dok-01, then the timeout, caching and degradation labs that build on it.

**Who starts here:** mid-level engineers learn the maths, health checks and timeouts, because
those explain most cascading outages they will debug. Seniors add the patterns (idempotency,
queues, caching, degradation) that let one part fail without the whole platform failing.

### Availability maths [L2 · Mid]

**Concept.** **Availability** is the fraction of time (or of requests) a service works. People
quote it in "nines". Learn this table by heart, because every SLO and contract discussion starts
from it:

| Availability | Downtime per year | Downtime per 30 days | Realistic for |
|---|---|---|---|
| 99% | 3.65 days | 7.2 hours | One VM, manual recovery |
| 99.5% | 1.83 days | 3.6 hours | One host, good runbooks, backups |
| 99.9% | 8.76 hours | 43.2 minutes | Redundant nodes, automatic failover, on-call |
| 99.95% | 4.38 hours | 21.6 minutes | Multi-AZ, tested failover, mature change management |
| 99.99% | 52.6 minutes | 4.3 minutes | Multi-site, automation everywhere, large team |
| 99.999% | 5.3 minutes | 26 seconds | Telecom-grade; almost never worth it for web apps |

Two formulas do most of the work:

```
Components in SERIES (all must work):      A = A1 × A2 × A3 × ...
Components in PARALLEL (any one is enough): A = 1 − (1 − A1) × (1 − A2) × ...

Example, today's shop path:  DNS 99.95% × Dokploy host 99.5% × app 99.9% × DB 99.9%
                             = 0.9995 × 0.995 × 0.999 × 0.999 ≈ 0.9925  → 99.25% (≈ 5.4 h / month)
Two independent Traefik nodes in parallel: 1 − 0.005 × 0.005 = 0.999975
Same path with that pair:   0.9995 × 0.999975 × 0.999 × 0.999 ≈ 0.9975 → 99.75% (≈ 1.8 h / month)
```

Three lessons hide in those numbers. A chain is weaker than its weakest link, so adding a fourth
nine to one component is wasted while another sits at 99.5%. Parallel maths assumes independent
failures; two nodes on the same hypervisor are not independent, and the real number is much
closer to the single-node figure. And availability also equals **MTBF / (MTBF + MTTR)** (mean
time between failures, mean time to repair): halving the time to repair improves availability as
much as halving how often things break. For a small on-prem team, faster recovery (runbooks,
automation, tested restores) is usually the cheapest nine you can buy.

**Key terms:** availability, nines, MTBF, MTTR, MTTD (mean time to detect), serial and parallel
composition, correlated failure.

**See it on a real system.** Calculate the model, then measure reality. The measurement uses the
Prometheus blackbox_exporter probe for the site (set up in
[Performance & observability](32-learn-performance-observability.md)):

```bash
awk 'BEGIN { a = 0.9995 * 0.995 * 0.999 * 0.999; printf "%.4f  -> %.0f min down per 30 days\n", a, (1-a)*43200 }'
curl -s http://mon-01:9090/api/v1/query \
  --data-urlencode 'query=avg_over_time(probe_success{instance="https://shop.example.com/healthz"}[30d])' \
  | jq -r '.data.result[0].value[1]'
```

```
0.9925  -> 323 min down per 30 days
0.99871
```

→ The model predicts 99.25%; the probe measured 99.871% (about 56 minutes of failed probes in 30
days). Reality beat the model this month because the host did not fail, which is luck, not design.
The model tells you what a bad month looks like; the measurement tells you what this month was.

**Hands-on lab (no VM needed, then mon-01)**

**Step 1 — Build it.** Write the availability model for one real app as a small table: every
component on the request path, its estimated availability, and whether it is serial or parallel.
Use the dependency map from section 2.

**Step 2 — Break it.** Add a "redundant" second Traefik node to the model, but put both on the
same hypervisor. Calculate the parallel figure, then ask: what is the availability of the
hypervisor? Put the hypervisor in series in front of the pair and recalculate. The gain mostly
disappears.

**Step 3 — Fix it.** Pull your last five incidents and compute MTTR from their timelines. Decide
which buys more availability for the money: a second node, or cutting MTTR in half with a tested
runbook. Write the answer as two sentences you could say to a manager.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Promising nines the design cannot deliver | SLA breached in the first bad month | Recompute the serial chain | Section 11, SLOs |
| Correlated "redundancy" | Both copies fail together | Failure-domain map | Section 2 |
| Measuring only uptime of hosts | Hosts up, users see errors | Measure from outside (blackbox probe) or from request success rates | [Performance & observability](32-learn-performance-observability.md) |

**Why it matters for troubleshooting.** When someone says "the site is always down", the measured
number turns an emotional argument into a technical one, and the model points at the component
that contributes most of the downtime.

**Next step:** what a spare costs, and how much headroom the survivors need.

### Redundancy and N+1 [L2 · Mid]

**Concept.** **N** is the number of units needed to carry peak load. **N+1** adds one spare, so
one unit can fail (or be patched) without an outage. **N+2** lets one unit be in maintenance while
another fails. **2N** duplicates everything, typically a second site. Spares can be **active**
(serving traffic all the time, as in active-active) or **standby** (hot, warm or cold, depending on
how ready they are to take over).

Stateless parts (Traefik, app containers) are easy to make redundant: run more copies behind a
load balancer. Stateful parts (databases, Swarm managers, etcd, Harbor's storage) are hard: they
need replication, a way to choose a leader, and **quorum** so that two halves of a split network
never both accept writes (split brain).

```
Quorum: a cluster of 2f+1 voting members survives f failures.
  1 manager  → survives 0     2 managers → survives 0 (worse than 1: either loss stops it)
  3 managers → survives 1     5 managers → survives 2     7 → survives 3 (rarely worth it)
Applies to: Swarm managers (Raft), etcd in Kubernetes, Patroni's DCS, Consul.
```

Headroom is the part people forget. If each of N nodes runs at utilisation u, after one failure
the survivors run at u × N / (N − 1):

| Nodes | Load per node before | Load per node after one failure | Safe? (target ≤ 80%) |
|---|---|---|---|
| 2 | 60% | 120% | No: the survivor collapses |
| 3 | 60% | 90% | No: latency explodes |
| 3 | 50% | 75% | Yes |
| 4 | 60% | 80% | Borderline |
| 4 | 55% | 73% | Yes |

So N+1 is not "add a node"; it is "add a node **and** keep every node below
target × (N − 1) / N".

**Key terms:** N+1, N+2, 2N, active-active, active-passive, hot/warm/cold standby, quorum, split
brain, fencing, headroom.

**See it on a real system.**

```bash
docker info --format '{{.Swarm.Managers}} managers / {{.Swarm.Nodes}} nodes'
curl -s http://mon-01:9090/api/v1/query \
  --data-urlencode 'query=1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle",job="dokploy"}[1h]))' \
  | jq -r '.data.result[] | "\(.metric.instance)  \(.value[1] | tonumber * 100 | floor)%"'
sudo -u postgres psql -x -c "SELECT client_addr, state, sync_state, replay_lag FROM pg_stat_replication;"
```

```
3 managers / 3 nodes
dok-01:9100  58%
dok-02:9100  61%
dok-03:9100  55%
-[ RECORD 1 ]---------------
client_addr | 192.0.2.33
state       | streaming
sync_state  | async
replay_lag  | 00:00:00.001842
```

→ Three managers (quorum survives one loss) and one streaming replica, so the redundancy exists.
But the nodes average 58%: lose one and the other two run near 87%. The cluster is N+1 on paper
and N+0 under peak load. The replica is asynchronous, so a failover can lose the last moments
of writes; that is a recovery-point decision (section 5), not a bug.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** Make a two-manager Swarm on dok-01 and dok-02 (on a fresh lab, or leave and
re-create the lab Swarm):

```bash
docker swarm init --advertise-addr 192.168.56.11            # on dok-01
docker swarm join-token manager                              # copy the join command
# on dok-02: paste the "docker swarm join --token ..." command
docker node ls
```

**Step 2 — Break it.** Stop Docker on dok-02 (lab only), then try to change anything from dok-01:

```bash
sudo systemctl stop docker.socket docker.service             # on dok-02
docker service create --name probe nginx:1.27                # on dok-01
```

```
Error response from daemon: rpc error: code = Unknown desc = The swarm does not have a leader. It's possible that too few managers are online. Make sure more than half of the managers are online.
```

→ Two managers survive zero failures: one manager alone is not a majority of two.

**Step 3 — Fix it.** Start Docker on dok-02, join dok-03 as a third manager and repeat the break.
With three managers, stopping one still leaves a majority and the command succeeds. Then remove
the probe service with `docker service rm probe`.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Even number of managers or members | Cluster freezes after one loss | `docker node ls`, `docker info` | [Containers & K8s](26-playbook-containers-k8s.md) |
| No headroom | Survivors overloaded after a failure, so a single failure becomes a full outage | Per-node CPU and memory in Prometheus | [Slow system](23-playbook-slow-system.md) |
| Async replica promoted | Recent writes missing after failover | `pg_stat_replication`, replay lag before failover | [Databases & ops](38-learn-databases-ops.md) |
| Split brain | Two primaries accept writes | Check which node holds the leader lock or VIP | [Databases & ops](38-learn-databases-ops.md) |

**Why it matters for troubleshooting.** "We have redundancy" is a claim; quorum size, placement and
headroom are the evidence. Checking all three takes a minute and explains why a "redundant"
cluster still went down.

**Next step:** redundancy only helps if traffic stops going to the broken copy, which is the job
of load balancers and health checks.

### Load balancing and health checks [L2 · Mid]

**Concept.** A **load balancer** spreads requests across healthy backends. **Layer 4** balancers
(HAProxy in TCP mode, AWS NLB, keepalived with IPVS) forward connections without reading HTTP.
**Layer 7** balancers (Traefik, Nginx, AWS ALB) read the request and can route by host, path or
header. Common algorithms are round robin, least connections and hashing (for sticky sessions).

A **health check** decides whether a backend should receive traffic. There are two kinds of
question, and mixing them up causes outages:

| Check | Question it answers | Failing it should | Example |
|---|---|---|---|
| Liveness | Is this process stuck beyond repair? | Restart the container | Docker `HEALTHCHECK`, Kubernetes `livenessProbe` |
| Readiness | Can this instance serve requests right now? | Remove it from the load balancer, do not restart | Traefik health check, ALB target health, Kubernetes `readinessProbe` |

```
                       ┌── GET /healthz every 10s, timeout 3s ──▶ app-1  200 ✔  in rotation
 users ─▶ Traefik / ALB┤
                       └── GET /healthz every 10s, timeout 3s ──▶ app-2  timeout ✘ removed
                                                                   (back after it passes again)
```

The classic senior trap is the **deep health check**: `/healthz` also checks the database. When
the database blips for ten seconds, every app instance reports unhealthy at once, the load
balancer removes all of them, and a short database hiccup becomes a full outage with a "no
available server" page. Rule of thumb: a health check should fail only for problems that removing
or restarting **this instance** can fix. Report shared dependencies in a separate status endpoint
and in metrics, not in the check that pulls instances out of rotation.

Graceful shutdown belongs here too: on deploy, an instance should stop receiving new requests,
finish the ones in flight, then exit. Swarm sends SIGTERM and waits `stop_grace_period` (10s by
default) before SIGKILL; the app must handle SIGTERM for this to work.

**Key terms:** L4 and L7 load balancing, round robin, least connections, sticky sessions,
liveness, readiness, shallow and deep checks, draining, graceful shutdown.

**See it on a real system.**

```bash
docker inspect --format '{{json .State.Health}}' CONTAINER | jq '{Status, FailingStreak, last: .Log[-1].Output}'
curl -s http://127.0.0.1:8080/api/http/services | jq '.[] | select(.name|test("shop")) | {name, serverStatus}'
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/shop-tg/6d0ecf831eec9f09 \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]' --output table
```

```
{
  "Status": "unhealthy",
  "FailingStreak": 3,
  "last": "curl: (28) Operation timed out after 3001 milliseconds with 0 bytes received\n"
}
{
  "name": "shop-web-1a2b3c-1-websecure@swarm",
  "serverStatus": {
    "http://10.0.1.7:3000": "UP",
    "http://10.0.1.9:3000": "DOWN"
  }
}
-------------------------------------------------------
|                DescribeTargetHealth                 |
+----------------------+-------------+----------------+
|  i-0a1b2c3d4e5f60718 |  healthy    |  None          |
|  i-0f9e8d7c6b5a40321 |  unhealthy  |  Target.Timeout|
+----------------------+-------------+----------------+
```

→ The Traefik API call only works where the API is enabled (the lab below enables it on
127.0.0.1:8080; Dokploy does not expose it by default). In each view, one backend is out of
rotation and the other carries the load, which is the design working. Your job is to find out why
the second one fails its check before the first one also fails.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** Traefik in front of two `traefik/whoami` instances, with an active health
check. The whoami image lets you change the status its `/health` endpoint returns:

```bash
mkdir -p ~/lab-lb && cd ~/lab-lb
cat > compose.yaml <<'EOF'
services:
  traefik:
    image: traefik:v3.6
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --api.insecure=true
    ports: ["80:80", "127.0.0.1:8080:8080"]
    volumes: ["/var/run/docker.sock:/var/run/docker.sock:ro"]
  whoami:
    image: traefik/whoami
    labels:
      - traefik.enable=true
      - traefik.http.routers.who.rule=Host(`who.lab.example.com`)
      - traefik.http.routers.who.entrypoints=web
      - traefik.http.services.who.loadbalancer.server.port=80
      - traefik.http.services.who.loadbalancer.healthcheck.path=/health
      - traefik.http.services.who.loadbalancer.healthcheck.interval=5s
      - traefik.http.services.who.loadbalancer.healthcheck.timeout=2s
EOF
docker compose up -d --scale whoami=2
for i in 1 2 3 4; do curl -s -H 'Host: who.lab.example.com' http://127.0.0.1/ | grep Hostname; done
```

**Step 2 — Break it.** Make one instance unhealthy, then both:

```bash
W1=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lab-lb-whoami-1)
W2=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lab-lb-whoami-2)
curl -s -X POST -d '500' "http://$W1/health"; sleep 8
for i in 1 2 3 4; do curl -s -H 'Host: who.lab.example.com' http://127.0.0.1/ | grep Hostname; done
curl -s -X POST -d '500' "http://$W2/health"; sleep 8
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: who.lab.example.com' http://127.0.0.1/
```

→ With one instance unhealthy, every response comes from the other. With both unhealthy you get
`503`: this is what a deep health check does to you when the shared database blips.

**Step 3 — Fix it.** Restore both (`curl -s -X POST -d '200' "http://$W1/health"`, same for W2),
watch traffic return to both within one interval, and check
`curl -s http://127.0.0.1:8080/api/http/services | jq` to see `serverStatus` change. Keep this
lab running for the next three topics.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Deep check on a shared dependency | Short DB blip → all backends removed → 503 everywhere | Traefik `serverStatus`, app health endpoint code | [Site down](25-playbook-site-down.md) |
| No readiness check | 502s during every deploy | Traefik access log during a deploy | [Deployment patterns](35-deployment-patterns.md) |
| App ignores SIGTERM | Requests cut off at deploy, 10s pause, exit 137 | `docker service ps SERVICE --no-trunc` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Check too strict or too slow | Flapping in and out of rotation | Health log `FailingStreak`, check timeout vs app latency | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** Many 502/503 incidents are the health system doing exactly
what it was told. Before debugging the app, ask what the checks saw and whether they were checking
the right thing.

**Next step:** what happens to requests stuck waiting on a slow backend.

### Timeouts, retries and circuit breakers [L2 · Mid]

**Concept.** A slow dependency is more dangerous than a dead one. A dead one fails fast; a slow one
holds connections, threads and memory until everything upstream is waiting too. Three tools
contain it:

**Timeouts.** Every network call needs one, and they must **shrink as you go deeper**, so the inner
call gives up before the outer one and can return a clean error:

```
 user / browser                   ─────────────────────────────────────────  (no control)
 Traefik responseHeaderTimeout 30s ───────────────────────────────────
 app server worker timeout 25s     ─────────────────────────────
 app → DB statement_timeout 5s     ─────────
 app → external API timeout 3s     ──────
```

If the inner timeout is longer than the outer one, the proxy returns 504 while the app keeps
working on a request nobody is waiting for any more.

**Retries.** Retry only failures that are likely to be temporary (connection refused, timeouts,
503), only for operations that are safe to repeat (next topic), with **exponential backoff** and
**jitter** (random spread), and with a cap. Retries multiply across layers:

```
 client retries 3×  →  proxy retries 3×  →  app retries 3× to DB
 worst case: the DB receives 3 × 3 × 3 = 27 attempts for one click, exactly when it is struggling
```

Retry at **one** layer, usually the one closest to the user or the one that knows the operation is
idempotent.

**Circuit breakers.** When a dependency keeps failing, stop calling it for a while and fail fast
instead. States: **closed** (normal), **open** (fail immediately), **half-open** (let a few test
requests through, close again if they succeed).

```
   closed ──(error ratio > threshold)──▶ open ──(after fallback duration)──▶ half-open
     ▲                                                                           │
     └──────────────────────(test requests succeed)──────────────────────────────┘
```

Traefik v3 has all three: transport timeouts (`serversTransports.forwardingTimeouts`), a `retry`
middleware (by default it retries only when it cannot reach a backend, not when the backend
answers with a 500; recent v3 releases add a `status` option for chosen response codes, so check
the retry reference for your version), and a `circuitBreaker` middleware with expressions such as `NetworkErrorRatio() > 0.30` or
`LatencyAtQuantileMS(50.0) > 1000`.

**Key terms:** timeout budget, exponential backoff, jitter, retry storm, retry budget, circuit
breaker, fail fast, bulkhead (separate pools so one slow dependency cannot use all workers).

**See it on a real system.** Find every timeout on one request path; most teams discover several
defaults nobody chose:

```bash
sudo grep -rniE 'timeout' /etc/dokploy/traefik/traefik.yml /etc/dokploy/traefik/dynamic/ 2>/dev/null
docker service inspect shop-web-1a2b3c --format '{{json .Spec.TaskTemplate.ContainerSpec.Env}}' \
  | tr ',' '\n' | grep -iE 'timeout|workers'
sudo -u postgres psql -Atc "SHOW statement_timeout;"
curl -s -o /dev/null -w 'connect %{time_connect}s  tls %{time_appconnect}s  first byte %{time_starttransfer}s  total %{time_total}s\n' https://shop.example.com/
```

```
"GUNICORN_CMD_ARGS=--workers 4 --timeout 120"
0
connect 0.004s  tls 0.019s  first byte 0.412s  total 0.415s
```

→ No timeouts configured in Traefik (its responseHeaderTimeout defaults to 0, which means wait
forever), Gunicorn allows 120 seconds, and PostgreSQL's `statement_timeout` is 0 (unlimited). One
slow query can therefore hold a worker for two minutes; four slow queries take the whole app.

**Hands-on lab (test VM only, continues the load-balancer lab)**

**Step 1 — Build it.** whoami can delay its answer with `?wait=`. Measure a slow request with no
timeouts anywhere:

```bash
cd ~/lab-lb
curl -s -X POST -d '200' "http://$W1/health"; curl -s -X POST -d '200' "http://$W2/health"
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' -H 'Host: who.lab.example.com' 'http://127.0.0.1/?wait=40s'
```

```
200 40.012s
```

**Step 2 — Break it.** Simulate a slow dependency under load: 50 concurrent slow requests hold 50
connections for 40 seconds each. With real app workers instead of whoami, the pool would be
exhausted and fast requests would queue behind slow ones:

```bash
sudo apt-get install -y apache2-utils
ab -n 100 -c 50 -H 'Host: who.lab.example.com' 'http://127.0.0.1/?wait=40s' | grep -E 'Time taken|Requests per second'
```

**Step 3 — Fix it.** Add a file provider with a transport timeout and a circuit breaker, then
attach both to the service:

```bash
mkdir -p dyn && cat > dyn/transport.yml <<'EOF'
http:
  serversTransports:
    fast:
      forwardingTimeouts:
        dialTimeout: 2s
        responseHeaderTimeout: 5s
  middlewares:
    who-cb:
      circuitBreaker:
        expression: "LatencyAtQuantileMS(50.0) > 3000"
        checkPeriod: 1s
        fallbackDuration: 10s
        recoveryDuration: 10s
EOF
```

In `compose.yaml`, add `- --providers.file.directory=/dyn` to the Traefik command and
`- ./dyn:/dyn:ro` to its volumes, and add these labels to whoami:

```
      - traefik.http.services.who.loadbalancer.serverstransport=fast@file
      - traefik.http.routers.who.middlewares=who-cb@file
```

```bash
docker compose up -d --scale whoami=2
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' -H 'Host: who.lab.example.com' 'http://127.0.0.1/?wait=40s'
for i in $(seq 1 5); do curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' -H 'Host: who.lab.example.com' 'http://127.0.0.1/?wait=4s'; done
```

```
504 5.004s
200 4.006s
200 4.004s
503 0.002s
503 0.001s
503 0.001s
```

→ The timeout turns a 40-second hang into a 5-second 504. The 4-second requests still succeed,
but once median latency crosses 3 seconds the breaker opens and requests fail in about a
millisecond, which protects the backend and frees connections for everything else. After
`fallbackDuration` it lets test traffic through again. The exact switch-over point depends on how
many requests the breaker has seen in its check period.

For scripts and CI jobs, the same ideas in shell, with exponential backoff, jitter and a cap:

```bash
retry() {
  local max=5 attempt=1 delay
  until "$@"; do
    if (( attempt >= max )); then echo "giving up after $attempt attempts: $*" >&2; return 1; fi
    delay=$(( 2 ** attempt + RANDOM % 3 ))
    echo "attempt $attempt failed, retrying in ${delay}s" >&2
    sleep "$delay"; (( attempt++ ))
  done
}
retry curl -fsS --max-time 5 https://shop.example.com/healthz
```

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| No timeout on a slow dependency | Whole app hangs, CPU idle, workers all busy | `curl -w` timings; app worker status; `pg_stat_activity` long queries | [Slow system](23-playbook-slow-system.md) |
| Inner timeout longer than outer | 504 at the proxy while the app keeps working | Compare timeouts layer by layer | [Site down](25-playbook-site-down.md) |
| Retry storm | A small blip becomes a sustained overload; traffic multiplies during the incident | Request rate at the DB vs at the edge | [Slow system](23-playbook-slow-system.md) |
| Breaker too sensitive | Healthy service returning 503 in bursts | Breaker expression vs normal latency | [Web servers & proxies](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting.** "Everything is slow and the CPU is idle" is very often a
missing timeout: workers are all waiting on one slow thing. The `curl -w` timing line and a list of
timeouts per layer locate it in minutes.

**By career stage.** Mid-level engineers find missing timeouts during incidents. Seniors set the
timeout budget for the whole platform once, put it in the paved-road templates (section 8), and
review new services against it.

**Next step:** retries are only safe if repeating an operation does no harm.

### Idempotency and queues [L3 · Senior]

**Concept.** An operation is **idempotent** if doing it twice has the same effect as doing it once.
`mkdir -p`, an HTTP `PUT`, `CREATE TABLE IF NOT EXISTS` and an Ansible `copy` task are idempotent;
`echo >> file`, an HTTP `POST /orders` and "charge the card" are not. Idempotency is what makes
retries, re-runs of a failed pipeline and re-applying configuration safe. For non-idempotent
business operations, the client sends an **idempotency key** (a unique request ID), and the server
remembers which keys it has already processed.

A **queue** (RabbitMQ, Redis streams, SQS, Kafka) sits between a producer and a consumer. It absorbs
spikes, lets the consumer be down for a while without losing work, and turns synchronous coupling
into asynchronous. The costs: messages are usually delivered **at least once**, so consumers must be
idempotent; a **backlog** can grow silently; a **poison message** that always fails needs a
**dead-letter queue** instead of infinite retries.

```
  web app ──POST──▶ [ queue: emails  ▓▓▓▓▓▓░░░░ backlog 1,240 ] ──▶ worker ×2 ──▶ SMTP relay
     ▲ returns 202 at once               │ failed 5× ▼
     └ user is not kept waiting          [ dead-letter queue: 3 ]  ◀── a human looks at these
```

For your platform, idempotency matters most in three places: Ansible roles and shell scripts (safe
to re-run after a partial failure), database migrations (safe to re-run after a failed deploy), and
CI deploy jobs (safe to retry when the runner dies halfway).

**Key terms:** idempotent, idempotency key, at-least-once and exactly-once delivery, backlog,
consumer lag, dead-letter queue, poison message, back-pressure.

**See it on a real system.**

```bash
ansible-playbook -i inventories/lab site.yml --limit dok-01 --check --diff | tail -3
docker exec rabbitmq rabbitmqctl list_queues name messages messages_unacknowledged consumers
```

```
PLAY RECAP *********************************************************************
dok-01                     : ok=24   changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0

Timeout: 60.0 seconds ...
Listing queues for vhost / ...
name	messages	messages_unacknowledged	consumers
emails	1240	12	2
emails.dlq	3	0	0
```

→ `changed=0` on a second run is the proof that the playbook is idempotent; any task that reports
`changed` on every run is a bug waiting to bite during an incident. The queue shows a backlog of
1,240 with only two consumers and three dead letters; that backlog needs an alert (age of oldest
message is the best signal), not a discovery during a customer complaint.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** A "configuration script" written the way many first scripts are written:

```bash
cat > ~/add-dns.sh <<'EOF'
#!/usr/bin/env bash
echo '{ "dns": ["192.168.56.53", "192.168.56.54"] }' >> /tmp/lab-daemon.json
EOF
chmod +x ~/add-dns.sh && ~/add-dns.sh && python3 -m json.tool /tmp/lab-daemon.json
```

**Step 2 — Break it.** Re-run it, exactly as a retried CI job or a second Ansible `shell` run would:

```bash
~/add-dns.sh && python3 -m json.tool /tmp/lab-daemon.json
```

```
Extra data: line 2 column 1 (char 46)
```

→ On a real host this file is `/etc/docker/daemon.json`, and Docker would refuse to start with an
`invalid character '{' after top-level value` error after the next restart.

**Step 3 — Fix it.** Make the script declare the whole desired state instead of appending to it,
then run it three times:

```bash
cat > ~/add-dns.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
tmp=$(mktemp)
printf '%s\n' '{ "dns": ["192.168.56.53", "192.168.56.54"], "log-opts": { "max-size": "10m", "max-file": "3" } }' > "$tmp"
python3 -m json.tool "$tmp" > /dev/null          # validate before replacing
if ! cmp -s "$tmp" /tmp/lab-daemon.json; then mv "$tmp" /tmp/lab-daemon.json; echo changed; else rm "$tmp"; echo ok; fi
EOF
for i in 1 2 3; do ~/add-dns.sh; done
```

```
changed
ok
ok
```

The Ansible equivalent is a `template` or `copy` task with `validate: python3 -m json.tool %s`,
which reports `changed` once and `ok` afterwards.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Non-idempotent script re-run | Duplicate lines, broken config after a retry | `git diff`, validate the file (`python3 -m json.tool`, `apachectl -t`, `nginx -t`) | [Services & systemd](07-services-systemd.md) |
| Consumer not idempotent | Duplicate e-mails or orders after a worker restart | Count messages by ID in logs | [Databases & ops](38-learn-databases-ops.md) |
| Growing backlog | Work delayed by hours, nobody alerted | `rabbitmqctl list_queues`, oldest-message age | [Performance & observability](32-learn-performance-observability.md) |
| Poison message | Worker crash-loops on the same message | Worker logs, DLQ depth | [Containers & K8s](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** During an incident you will re-run things: pipelines,
playbooks, migrations. Idempotent automation means "run it again" is a safe first move; without it,
the retry becomes a second incident.

**Next step:** another way to protect a slow or fragile dependency is to call it less often.

### Caching layers [L3 · Senior]

**Concept.** A cache keeps a copy of an answer closer to the user so the expensive source is asked
less often. A typical web request can pass through several:

```
 browser cache ─▶ CDN ─▶ reverse proxy cache ─▶ app cache (Redis) ─▶ DB buffer cache ─▶ OS page cache ─▶ disk
 (Cache-Control) (edge)   (Nginx/Varnish)        (your code)          (shared_buffers)   (free -h "cache")
```

Caching is a design decision with failure modes of its own:

| Risk | What happens | Mitigation |
|---|---|---|
| Cold cache | After a restart or flush, every request hits the database at once | Warm up before taking traffic; size the DB for some miss traffic |
| Stampede (thundering herd) | Many keys expire at the same moment and every client recomputes them together | TTL jitter, request coalescing, serve stale while one request refreshes |
| Stale data | Users see old prices or permissions | Short TTL for sensitive data, explicit invalidation on write |
| Hidden capacity gap | The DB is fine only because 95% of reads are cached | Know the hit ratio and what the DB does at 0% |
| Cache becomes a hard dependency | Redis down → site down | Treat cache errors as misses, with a timeout |

The senior question is: "what happens to the next layer down when this cache is empty?".

**Key terms:** hit ratio, TTL, invalidation, cold and warm cache, stampede, stale-while-revalidate,
write-through and cache-aside.

**See it on a real system.**

```bash
curl -sI https://shop.example.com/static/app.css | grep -iE '^(cache-control|age|etag|x-cache)'
docker exec REDIS_CONTAINER redis-cli INFO stats | grep -E 'keyspace_(hits|misses)'
sudo -u postgres psql -Atc "SELECT round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) FROM pg_stat_database;"
```

```
cache-control: public, max-age=31536000, immutable
etag: "65f1c2a8-1b3f2"
keyspace_hits:4823190
keyspace_misses:213044
99.21
```

→ Static files are cacheable for a year (fine, if file names change on each release). Redis hits
about 96% of the time (4,823,190 ÷ 5,036,234), so if Redis empties, the database briefly receives
roughly 24 times its usual read load (5,036,234 ÷ 213,044). PostgreSQL serves 99.2% of block reads from memory. Those
three numbers tell you how much load is hidden behind each cache.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** Fill a Redis cache the way naive code does, with the same TTL for every key.
One `redis-cli` reads all 200 commands from the pipe, so every key is written within milliseconds
(200 separate `docker exec` calls would take many seconds and spread the expiry by themselves):

```bash
docker run -d --name lab-redis redis:7
for i in $(seq 1 200); do echo "SET product:$i cached EX 60"; done | docker exec -i lab-redis redis-cli > /dev/null
docker exec lab-redis redis-cli TTL product:1; docker exec lab-redis redis-cli TTL product:200
```

**Step 2 — Break it.** Every key expires within the same few seconds. In production this is the
moment all clients recompute at once and the database spikes. Watch them vanish together:

```bash
sleep 55; for s in 1 2 3 4 5 6 7; do docker exec lab-redis redis-cli DBSIZE; sleep 1; done
```

**Step 3 — Fix it.** Add jitter so expiry spreads out, then repeat the observation:

```bash
for i in $(seq 1 200); do echo "SET product:$i cached EX $(( 60 + RANDOM % 30 ))"; done | docker exec -i lab-redis redis-cli > /dev/null
sleep 55; for s in $(seq 1 10); do docker exec lab-redis redis-cli DBSIZE; sleep 3; done
docker rm -f lab-redis
```

→ With jitter the key count falls gradually over 30 seconds instead of in one step.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Cold cache after restart | DB CPU spike and slow pages right after a deploy or Redis restart | `redis-cli INFO stats` (misses), DB active connections | [Slow system](23-playbook-slow-system.md) |
| Stampede | Periodic latency spikes at fixed intervals | TTLs of hot keys | [Performance & observability](32-learn-performance-observability.md) |
| Stale content after deploy | Users see old CSS or JS | `curl -sI` cache headers, `age` header | [Web, HTTP & TLS](18-web-http-tls.md) |
| Cache as hard dependency | Redis down → 500s | App logs for Redis connection errors | Section 2, dependency maps |

**Why it matters for troubleshooting.** "It was fine until we restarted Redis" and "it is slow every
hour on the hour" are cache stories. The hit ratio tells you how much load the cache is hiding.

**Next step:** decide in advance what users see when a part fails.

### Graceful degradation [L3 · Senior]

**Concept.** **Graceful degradation** means the system keeps doing the most important thing when
something fails, instead of failing completely. You design the degraded modes in advance, because
nobody designs well at 2am:

| Technique | What users see | Example |
|---|---|---|
| Static fallback | A friendly maintenance page with the right status code | Traefik `errors` middleware serving a page for 502–504 |
| Read-only mode | Can browse, cannot buy or edit | App flag that disables writes when the primary DB is down |
| Feature switch-off | Core works, extras hidden | Recommendations hidden when Redis or an external API fails |
| Serve stale | Slightly old data instead of an error | CDN or proxy `stale-if-error` |
| Load shedding | Some requests rejected fast instead of all served slowly | Traefik `inFlightReq` or `rateLimit` → 429 or 503 |
| Queue writes | "We received your order" now, processing later | Queue between web and worker (previous topic) |

The order of priority comes from the business: for a shop, browsing and checkout matter more than
reviews and recommendations. Write it down per app; it becomes part of the runbook and of the SLO
discussion (section 11).

**Key terms:** degraded mode, load shedding, rate limiting, feature flag (switch), kill switch,
maintenance page, brownout.

**See it on a real system.** Check which protective middlewares a service already has:

```bash
docker service inspect shop-web-1a2b3c --format '{{json .Spec.Labels}}' \
  | jq 'with_entries(select(.key | test("middlewares")))'
curl -s -o /dev/null -w '%{http_code}\n' https://shop.example.com/
```

```
{
  "traefik.http.routers.shop-web-1a2b3c-1-web.middlewares": "redirect-to-https@file"
}
200
```

→ Only an HTTPS redirect, which Dokploy puts on the port-80 router (its routers are named
APP-KEY-web and APP-KEY-websecure). When the app is down, users get Traefik's bare error, and
nothing limits a traffic spike. Both are design gaps you can close with labels.

**Hands-on lab (test VM only, continues the load-balancer lab)**

**Step 1 — Build it.** Add a maintenance page service and an errors middleware, plus a rate limit.
In `compose.yaml` add a service:

```yaml
  maint:
    image: nginx:1.27
    volumes: ["./maint:/usr/share/nginx/html:ro"]
    labels:
      - traefik.enable=true
      - traefik.http.services.maint.loadbalancer.server.port=80
```

and on whoami, replace the middleware label with:

```
      - traefik.http.middlewares.who-errors.errors.status=502-504
      - traefik.http.middlewares.who-errors.errors.service=maint@docker
      - traefik.http.middlewares.who-errors.errors.query=/index.html
      - traefik.http.middlewares.who-rl.ratelimit.average=20
      - traefik.http.middlewares.who-rl.ratelimit.burst=40
      - traefik.http.routers.who.middlewares=who-errors,who-rl
```

```bash
mkdir -p maint && echo '<h1>Shop is under maintenance. Back in a few minutes.</h1>' > maint/index.html
docker compose up -d --scale whoami=2
```

**Step 2 — Break it.** Take every backend out, then send a burst of traffic:

```bash
curl -s -X POST -d '500' "http://$W1/health"; curl -s -X POST -d '500' "http://$W2/health"; sleep 8
curl -s -i -H 'Host: who.lab.example.com' http://127.0.0.1/ | sed -n '1p;$p'
curl -s -X POST -d '200' "http://$W1/health"; curl -s -X POST -d '200' "http://$W2/health"; sleep 8
ab -n 300 -c 30 -H 'Host: who.lab.example.com' http://127.0.0.1/ | grep -E 'Complete|Non-2xx'
```

```
HTTP/1.1 503 Service Unavailable
<h1>Shop is under maintenance. Back in a few minutes.</h1>
Complete requests:      300
Non-2xx responses:      212
```

→ Users see a real page while the status code stays 503 (so monitors and search engines know it
is an outage, not content). The burst above the rate limit gets fast 429 responses instead of
slowing everyone down.

**Step 3 — Fix it.** Tune the limit to real traffic (rate limits that are too low are an outage you
caused yourself), then clean up the lab with `docker compose down`. Write the degraded-mode table
for one real app.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| No degraded mode | Any dependency failure is a full outage | Dependency map: which edges are hard? | Section 2 |
| Maintenance page returns 200 | Monitoring stays green during an outage | `curl -s -o /dev/null -w '%{http_code}'` | [Site down](25-playbook-site-down.md) |
| Rate limit too low | Legitimate users get 429 at peak | Traefik access log, count of 429 by client | [Web servers & proxies](29-learn-webservers-proxies.md) |
| Rate limit behind NAT | Whole office throttled as one client | Check the source IP Traefik sees; configure the client IP strategy | [Web servers & proxies](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting.** A degraded mode buys time: users can still do the important
thing while you debug the broken part calmly, which is the difference between a SEV1 and a SEV3.

**Next step:** assemble all of these patterns into reference architectures for your platform.

---

## 4. Reference architectures

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm ([Section Introduction](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction)) → the High Availability/Quorum and Disaster Recovery lessons → [Docker Overlay Network](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: [Case study: Apache holds 443](21-case-apache-443-dokploy.md) section 4 (Phase 3 — Choose the architecture) and [Learn: Docker](30-learn-docker.md) for Swarm basics · 3) KodeKloud: *AWS Networking Fundamentals* — VPC, subnets, gateways and load balancers ([course](https://kodekloud.com/courses/aws-networking-fundamentals)); video: *AWS Networking Basics: AWS VPC & Subnets for Beginners* (KodeKloud, 18 min, [YouTube](https://www.youtube.com/watch?v=QM63dyA_4Pc)) · 4) Docs: Docker [Swarm tutorial](https://docs.docker.com/engine/swarm/swarm-tutorial/) and Dokploy ([docs](https://docs.dokploy.com/docs/core)) · 5) Practice: the three-manager Swarm lab below on dok-01..03, then the two-AZ lab in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws) or your sandbox account.

**Who starts here:** mid-level engineers draw today's baseline honestly; seniors design the HA
version and defend it in a design review; leads own the hybrid DR picture and its budget.

A **reference architecture** is a drawing plus a set of rules: which components exist, how many
of each, where state lives, how traffic enters, and what happens when any one box disappears.
Every design in this section is built from the patterns of section 3. The value is not the
drawing itself but the table under it that says what each box survives.

### Today's single Dokploy host [L2 · Mid]

**Concept.** Before you redesign anything, draw what exists, including the parts you are not
proud of. This is the **as-is** (baseline) architecture of your production platform, with the
migration about half done: blog and the new shop front end already run in Dokploy; the api, the
legacy shop checkout and a few small sites still run on Apache behind Traefik.

```
                    Internet                          LAN users
                        │ 203.0.113.10 (NAT on the router)  │
                        ▼                                   ▼
 ┌────────────────────────── dok-prod-01  192.0.2.10 ───────────────────────────┐
 │ dokploy-traefik (container, Traefik v3)  publishes :80 :443                  │
 │   ├─ Host(shop.example.com)     → shop-web    (Swarm service, 1 replica)     │
 │   ├─ Host(blog.example.com)     → blog-web    (Swarm service, 1 replica)     │
 │   ├─ Host(dokploy.example.com)  → dokploy:3000  (control plane UI)           │
 │   └─ Host(api|checkout...)      → http://192.0.2.10:81  (file provider)      │
 │ apache2 :81 :444   api, checkout, intranet vhosts (PHP-FPM, legacy)          │
 │ dokploy, dokploy-postgres, dokploy-redis   (Swarm services, one node)        │
 │ shop-db (MySQL 8 container), app databases (PostgreSQL 16 containers)        │
 │ named volumes + /var/backups  ← on the SAME disk as everything above         │
 └───────────────────────────────────────────────────────────────────────────────┘
        ▲ docker pull (private CA)                  ▲ deploy webhook / API
  harbor.example.com (1 VM)                gitlab.example.com + 1 runner (1 VM)
  internal DNS 192.0.2.53 (1 server)       monitoring: nothing outside this host
```

Now write the table that turns the drawing into facts. For every box, ask: if this one thing
fails, what stops, and how long does recovery take **today**, with the people and backups you
actually have?

| Component fails | What stops | Recovery today | Realistic time |
|---|---|---|---|
| dok-prod-01 (hardware, kernel panic) | Every site, every deploy, Dokploy UI | Reboot, or rebuild host and restore | 10 min (reboot) to 1–2 days (rebuild) |
| Its disk | Everything, **including the backups** on `/var/backups` | Nothing to restore from | Unbounded: data loss |
| dokploy-traefik container | All HTTPS; apps still healthy behind it | `docker start dokploy-traefik` | 2–15 min, if someone is awake |
| Docker daemon restart | All containers restart together | Automatic | 1–3 min of errors |
| Harbor VM | Deploys and new pulls; running apps unaffected | Restart or rebuild Harbor | Minutes to a day |
| DNS server 192.0.2.53 | Outbound calls by name, internal names | Restart named/unbound | Minutes, if noticed |
| You (on holiday) | Anything not in a runbook | Wait | Days |

**Key terms:** as-is (baseline) architecture, to-be (target) architecture, measured RTO, rebuild
time, deploy-time dependency, recovery-time dependency.

**See it on a real system.** Six read-only commands describe the baseline more honestly than any
wiki page:

```bash
docker node ls --format '{{.Hostname}}  {{.Status}}  {{.ManagerStatus}}'
docker service ls --format '{{.Name}}\t{{.Replicas}}\t{{.Image}}'
docker ps --filter name=dokploy-traefik --format '{{.Names}}  {{.Status}}'
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :81 or sport = :444 )'
df -h / /var/lib/docker
sudo ls -lh --time-style=long-iso /var/backups/db/ | tail -3
```

```
dok-prod-01  Ready  Leader
dokploy	1/1	dokploy/dokploy:latest
dokploy-postgres	1/1	postgres:16
dokploy-redis	1/1	redis:7
shop-web-1a2b3c	1/1	harbor.example.com/apps/shop-web:3f9c2d1
blog-web-4d5e6f	1/1	harbor.example.com/apps/blog-web:9e1b7a4
shop-db-7g8h9i	1/1	mysql:8.4
dokploy-traefik  Up 3 weeks
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:80        0.0.0.0:*    users:(("docker-proxy",pid=2211,fd=7))
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*    users:(("docker-proxy",pid=2236,fd=7))
LISTEN 0      511                *:81              *:*    users:(("apache2",pid=1187,fd=4))
LISTEN 0      511                *:444             *:*    users:(("apache2",pid=1187,fd=6))
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   61G   33G  65% /
/dev/sda2        98G   61G   33G  65% /
-rw-r----- 1 root root 1.9G 2026-10-01 01:42 shop-db-2026-10-01.sql.gz
-rw-r----- 1 root root 1.9G 2026-10-02 01:41 shop-db-2026-10-02.sql.gz
-rw-r----- 1 root root 1.9G 2026-10-03 01:43 shop-db-2026-10-03.sql.gz
```

→ One node, one replica of everything, and Docker's data and the backups on the same filesystem
as the operating system (`/` and `/var/lib/docker` are the same device). The dumps exist and are
recent, which is good, but they share the fate of the host. None of this is unusual for a young
platform. It becomes a problem only if nobody has written it down and given each line a decision.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** On dok-01, install Dokploy from its documentation (the installer runs a
script as root, so read it before you run it). Deploy two small apps through the UI with the
domains `who.lab.example.com` and `blog.lab.example.com`, plus one PostgreSQL database created by
Dokploy. Take a VM snapshot called `baseline`.

**Step 2 — Break it.** Simulate losing the host, not just a reboot. Note the time, then destroy the
VM state by reverting dok-01 to the **pre-Dokploy** snapshot from section 0 (a fresh Ubuntu). This
is what a dead disk looks like from the outside.

**Step 3 — Fix it.** Rebuild with only what you would have at 2am: your notes and whatever backups
exist outside the VM. Write down the clock time at the end of each phase:

| Phase | Started | Finished | What slowed you down |
|---|---|---|---|
| Notice and decide to rebuild | | | |
| Reinstall Ubuntu settings, Docker, Dokploy | | | |
| Recreate apps, domains, environment variables | | | |
| Restore database data | | | |
| Verify both sites | | | |

The total is your **measured RTO** for "host lost". Most people discover two things here: the
environment variables and secrets were only in the Dokploy UI, and there was no copy of the
database outside the VM. Both go into the risk register (section 9) and the backup plan (section
5). Finish by reverting to the `baseline` snapshot.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Host down | Every site down at once, Dokploy UI unreachable | `ping -c3 192.0.2.10`, then the hypervisor console | [Site down](25-playbook-site-down.md) |
| Disk full | Deploys fail with `no space left on device`, databases crash | `df -h /var/lib/docker`, `docker system df` | [Storage & disk](01-storage-disk.md) |
| Docker daemon restart | All containers restart together, 1–3 minutes of 502s | `journalctl -u docker --since "-15min"` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Traefik container stopped | All HTTPS down, apps healthy | `docker ps -a --filter name=dokploy-traefik` | [Learn: Web servers & proxies](29-learn-webservers-proxies.md) |
| Apache down | Only the legacy sites return 502 | `systemctl status apache2`, `curl -sI http://127.0.0.1:81/` | [Case study](21-case-apache-443-dokploy.md) |

**Why it matters for troubleshooting.** When you know the baseline, "everything is down" stops
being a mystery: there are only a handful of boxes that can take everything down, and the table
above lists them in order of likelihood.

**Next step:** redesign the platform so that losing any one of those boxes stops only a part of
it, for a short time.

### On-prem HA platform [L3 · Senior]

**Concept.** The target (**to-be**) design keeps your tools (Dokploy, Traefik, Swarm, Harbor,
GitLab) and changes the counts, the placement of state and the path of traffic. It applies the
patterns of section 3 layer by layer:

```
                              Internet / LAN
                                    │
                     VIP 192.0.2.100 (keepalived, VRRP)    ← public NAT and DNS point here
                 ┌──────────────────┴──────────────────┐
          ┌──────▼───────┐                      ┌──────▼───────┐                ┌──────────────┐
          │ dok-prod-01  │                      │ dok-prod-02  │                │ dok-prod-03  │
          │ manager      │                      │ manager      │                │ manager      │
          │ Traefik      │                      │ Traefik      │                │ app tasks    │
          │ Dokploy UI   │                      │ (standby edge│                │              │
          │ app tasks    │                      │  + app tasks)│                │              │
          └──────┬───────┘                      └──────┬───────┘                └──────┬───────┘
                 └──────────────── dokploy-network (overlay) ───────────────────────────┘
                                    │                                  │
                 ┌──────────────────▼──────────┐     streaming    ┌────▼──────────────────┐
                 │ db-01 PostgreSQL 16 primary │ ───────────────▶ │ db-02 hot standby     │
                 │ (db VIP 192.0.2.110)        │   replication    │ (promote on failure)  │
                 └──────────────────┬──────────┘                  └───────────────────────┘
                                    │ WAL archive + nightly full (pgBackRest)
                 ┌──────────────────▼──────────────────┐        ┌──────────────────────────┐
                 │ object storage off the app hosts    │ ─────▶ │ off-site copy: S3 bucket │
                 │ (MinIO VM or NAS): backups, uploads │        │ with Object Lock         │
                 └─────────────────────────────────────┘        └──────────────────────────┘
   harbor.example.com (replicates to a 2nd registry)      mon-01: Prometheus, Alertmanager, Grafana,
   gitlab.example.com + 2 runners                          blackbox exporter, plus 1 probe outside
```

| Layer | Single host today | HA design | Why |
|---|---|---|---|
| Edge | One Traefik | Traefik on two nodes behind a VRRP virtual IP | The VIP moves in seconds when a node or Traefik dies |
| Orchestration | One-node Swarm | Three managers (Raft tolerates one loss) | Two managers is worse than one: losing either loses quorum |
| Apps | One replica | Two or more replicas, at most one per node, health checks | A node loss leaves a running copy |
| Images | Built on the host | Built in CI, pushed to Harbor, pulled by any node | An image that exists on one node cannot start on another |
| State | Volumes beside the apps | Databases on dedicated VMs with a replica; uploads in object storage | Tasks may move between nodes; data must not move with them |
| Backups | Same disk | Off-host, off-site, one immutable copy, restore tested monthly | Section 5 |
| Monitoring | Nothing off-host | Separate VM plus one probe from outside your network | A dead host cannot send its own alert |
| Control plane | Dokploy on the host | Still one Dokploy, pinned to dok-prod-01, backed up, restore runbook | A deploy-time SPOF you accept in writing (ADR) |

Raft, the consensus algorithm behind Swarm managers, needs a **majority** of managers to agree
before any change to the cluster state:

| Managers | Majority needed | Failures tolerated |
|---|---|---|
| 1 | 1 | 0 |
| 2 | 2 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Docker recommends no more than seven managers. Three is right for this platform; five makes sense
once you have more than about ten nodes or spread nodes over two rooms.

Four details decide whether this design works in practice. They are exactly the details a design
review should ask about:

**Dokploy's own services can move.** Dokploy creates `dokploy`, `dokploy-postgres` and, on
installs from older releases, `dokploy-redis` with a manager-only placement constraint (recent
installers no longer create `dokploy-redis`; `docker service ls` shows which you have, and the
inspect command below shows the constraint). On a three-manager cluster, Swarm may reschedule them to another manager after a failure,
where their local volumes are empty, so the UI comes back with no projects. Pin them to the node
that holds their data (`node.hostname==dok-prod-01`) and restore from backup instead of letting
them float. Re-check the constraint after every Dokploy upgrade.

**Images must come from a registry.** Dokploy's cluster feature needs a registry so that every
node can pull what Dokploy built. With Harbor behind your private CA, every new node must trust
that CA before it joins (exercise 2 in section 16 shows how to roll trust out to many nodes).

**Certificates on two edges.** Traefik keeps ACME certificates in a local `acme.json`; two
instances do not share it. With the HTTP-01 challenge, the validation request can land on the
other node and fail. Either use the DNS-01 challenge on both instances, or let only the active
node issue certificates and copy `acme.json` (mode 600) to the standby. Record the choice in an
ADR, because it changes how certificates fail.

**Dokploy manages one Traefik, not two.** The standby Traefik on dok-prod-02 is yours: same image
tag, same static file, same dynamic folder, deployed by Ansible from Git. If you skip this, the
standby drifts and fails exactly when it is needed.

**Key terms:** virtual IP (VIP), VRRP, keepalived, quorum, Raft, leader election, placement
constraint, active/passive, active/active, stateless tier, stateful tier.

**See it on a real system.** On the lab cluster, after Step 1 of the lab below:

```bash
docker node ls
docker info --format 'managers={{.Swarm.Managers}} nodes={{.Swarm.Nodes}}'
docker service ps who --filter desired-state=running --format '{{.Name}}\t{{.Node}}\t{{.CurrentState}}'
docker service inspect dokploy-postgres --format '{{json .Spec.TaskTemplate.Placement.Constraints}}'
ip -br addr show ens18
```

```
ID                            HOSTNAME   STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
k2x8d0v9q3j1m5n7b4c6z8a0s *   dok-01     Ready     Active         Leader           28.3.3
p9o8i7u6y5t4r3e2w1q0a9s8d     dok-02     Ready     Active         Reachable        28.3.3
z1x2c3v4b5n6m7l8k9j0h1g2f     dok-03     Ready     Active         Reachable        28.3.3
managers=3 nodes=3
who.1	dok-01	Running 2 hours ago
who.2	dok-02	Running 2 hours ago
who.3	dok-03	Running 2 hours ago
["node.role==manager","node.hostname==dok-01"]
ens18            UP             192.168.56.11/24 192.168.56.100/24 fe80::be24:11ff:fe4a:1b2c/64
```

→ Three managers, one leader, replicas spread one per node, and the VIP (192.168.56.100) currently
on dok-01. The placement line shows Dokploy's own `node.role==manager` plus the pin you added.
Without the pin, the first constraint alone would let Dokploy's database move to dok-02 or dok-03
and start there with an empty volume.

**Hands-on lab (test VMs dok-01..03 only)**

**Step 1 — Build it.** Open the Swarm ports between the three VMs (TCP 2377, TCP and UDP 7946,
UDP 4789), then join dok-02 and dok-03 as managers and run a service with one replica per node:

```bash
# on dok-01, the existing manager created by the Dokploy install
docker swarm join-token manager
# on dok-02 and dok-03, paste the printed command, for example:
docker swarm join --token SWMTKN-1-TOKEN 192.168.56.11:2377
# on dok-01 again
docker service create --name who --replicas 3 --replicas-max-per-node 1 \
  --network dokploy-network \
  --label traefik.enable=true \
  --label 'traefik.http.routers.who.rule=Host(`who.lab.example.com`)' \
  --label traefik.http.routers.who.entrypoints=web \
  --label traefik.http.services.who.loadbalancer.server.port=80 \
  traefik/whoami:v1.10
```

Pin Dokploy's own services to dok-01 so they never start empty elsewhere:

```bash
for s in $(docker service ls --format '{{.Name}}' | grep -E '^dokploy(-postgres|-redis)?$'); do
  docker service update --constraint-add 'node.hostname==dok-01' "$s"
done
```

Add the standby edge on dok-02. Copy Dokploy's Traefik folder from dok-01 (in production this is
an Ansible role, not a manual copy) and start Traefik with the same image Dokploy uses:

```bash
# on dok-01
docker inspect dokploy-traefik --format '{{.Config.Image}}'
sudo tar -C /etc/dokploy -czf /tmp/traefik-conf.tgz traefik
scp /tmp/traefik-conf.tgz 192.168.56.12:/tmp/
# on dok-02
sudo mkdir -p /etc/dokploy && sudo tar -C /etc/dokploy -xzf /tmp/traefik-conf.tgz
docker run -d --name edge-traefik --restart unless-stopped --network dokploy-network \
  -p 80:80 -p 443:443 \
  -v /etc/dokploy/traefik/traefik.yml:/etc/traefik/traefik.yml:ro \
  -v /etc/dokploy/traefik/dynamic:/etc/dokploy/traefik/dynamic \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  TRAEFIK_IMAGE
```

Install keepalived on dok-01 and dok-02 (`sudo apt install -y keepalived`), create the script user
(`sudo useradd -r -s /usr/sbin/nologin keepalived_script`) and write
`/etc/keepalived/keepalived.conf`. This is dok-01; on dok-02 use `priority 100` and swap the two
addresses:

```
global_defs {
    enable_script_security
    script_user keepalived_script
}

vrrp_script chk_edge {
    script "/usr/bin/curl -s -o /dev/null --max-time 2 http://127.0.0.1/"
    interval 2
    fall 2
    rise 2
}

vrrp_instance EDGE {
    state BACKUP
    interface ens18
    virtual_router_id 51
    priority 150
    advert_int 1
    nopreempt
    unicast_src_ip 192.168.56.11
    unicast_peer {
        192.168.56.12
    }
    virtual_ipaddress {
        192.168.56.100/24 dev ens18
    }
    track_script {
        chk_edge
    }
}
```

The check succeeds whenever Traefik answers at all (a 404 is still an answer), and fails when
nothing listens. `nopreempt` stops the VIP from bouncing back the moment dok-01 returns, which
avoids a second interruption. Unicast avoids the multicast problems of many virtual switches.

```bash
sudo systemctl enable --now keepalived
for i in $(seq 1 5); do curl -s -H 'Host: who.lab.example.com' http://192.168.56.100/ | grep Hostname; done
```

**Step 2 — Break it.** Power off dok-01 from the hypervisor (a hard stop, not a clean shutdown)
while a loop requests the site through the VIP from your workstation:

```bash
while :; do printf '%s ' "$(date +%T)"; curl -s -m 2 -o /dev/null -w '%{http_code}\n' \
  -H 'Host: who.lab.example.com' http://192.168.56.100/; sleep 0.5; done
```

```
14:02:10 200
14:02:11 200
14:02:11 000
14:02:13 000
14:02:16 200
14:02:16 200
```

Each `000` line is a request that waited the full 2-second `-m` timeout, which is why they are
about 2.5 seconds apart: the VIP was gone for roughly four seconds.

On dok-02, `ip -br addr show ens18` now lists the VIP and `docker node ls` shows dok-01 as `Down`
and `Unreachable`, with a new leader. Now power off dok-02 as well, leaving one manager of three:

```bash
docker node ls          # on dok-03
```

```
Error response from daemon: rpc error: code = Unknown desc = The swarm does not have a leader. It's possible that too few managers are online. Make sure more than half of the managers are online.
```

→ Running containers on dok-03 keep running, but the cluster cannot change anything: no deploys,
no rescheduling, no scaling. This is quorum loss, and it is why a third manager matters.

**Step 3 — Fix it.** Start dok-02: quorum returns (two of three) and `docker node ls` works again.
Start dok-01: it rejoins as a manager, but Swarm does **not** move tasks back by itself, so spread
them again:

```bash
docker service ps who --format '{{.Name}}\t{{.Node}}' --filter desired-state=running
docker service update --force who
```

If two managers were lost for good (disks destroyed), the last-resort recovery on the survivor is
`docker swarm init --force-new-cluster --advertise-addr 192.168.56.13`. It turns the survivor into
a single-manager cluster that keeps the services, after which you join new managers. Use it only
when the other managers can never return; running it while they can return creates two clusters.

Finish with `docker service rm who`, `docker rm -f edge-traefik` on dok-02, and stop keepalived if
you need the VMs for other labs.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Split brain: VIP on both nodes | Random resets, ARP flapping, half the requests fail | `ip -br addr` on both nodes, `journalctl -u keepalived` | [Learn: Networking](28-learn-networking.md) |
| Quorum lost | `The swarm does not have a leader` on every change | `docker node ls` on each manager | [Containers & K8s](26-playbook-containers-k8s.md) |
| Image only on one node | New tasks elsewhere stuck in `Preparing` or rejected with `No such image` | `docker service ps --no-trunc SERVICE` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Node-local volume | Data "disappears" after a task moves | `docker service inspect SERVICE --format '{{json .Spec.TaskTemplate.ContainerSpec.Mounts}}'` | [Learn: Databases](38-learn-databases-ops.md) |
| Dokploy database moved | UI shows no projects after a failover | `docker service ps dokploy-postgres` | This topic, pinning |
| Standby Traefik refuses `acme.json` | Standby logs `permissions 644 for acme.json are too open` | `ls -l /etc/dokploy/traefik/dynamic/acme.json` | [Learn: Web servers & proxies](29-learn-webservers-proxies.md) |
| Tasks not rebalanced | All replicas on one node after a failover | `docker service ps SERVICE` | `docker service update --force SERVICE` |

**Why it matters for troubleshooting.** In an HA platform the symptoms change shape. "Everything
down" becomes "every third request fails" or "only new deploys fail". Knowing the design tells you
which component can produce which partial symptom.

**Next step:** the same design in AWS, where the provider runs some of these boxes for you.

### AWS reference architecture [L3 · Senior]

**Concept.** On AWS the same layers exist, but several are managed services. A typical design for
the shop, if it ran in a region such as eu-west-1:

```
                              Route 53 (shop.example.com, alias record)
                                              │
                               CloudFront + WAF (optional: static files, edge)
                                              │
 ┌───────────────────────────────── VPC 10.20.0.0/16 ────────────────────────────────────┐
 │          Availability Zone a                              Availability Zone b          │
 │  ┌───────────────────────────┐   Application Load   ┌───────────────────────────┐      │
 │  │ public 10.20.0.0/24       │◀── Balancer (nodes ─▶│ public 10.20.1.0/24       │      │
 │  │ ALB node, NAT gateway a   │    in both AZs)      │ ALB node, NAT gateway b   │      │
 │  └─────────────┬─────────────┘                      └─────────────┬─────────────┘      │
 │  ┌─────────────▼─────────────┐                      ┌─────────────▼─────────────┐      │
 │  │ private app 10.20.10.0/24 │  ECS service or EC2  │ private app 10.20.11.0/24 │      │
 │  │ tasks / instances         │  Auto Scaling group, │ tasks / instances         │      │
 │  │                           │  min 2, both AZs     │                           │      │
 │  └─────────────┬─────────────┘                      └─────────────┬─────────────┘      │
 │  ┌─────────────▼─────────────┐   synchronous        ┌─────────────▼─────────────┐      │
 │  │ RDS PostgreSQL 16 primary │ ───replication─────▶ │ RDS standby (Multi-AZ)    │      │
 │  └───────────────────────────┘                      └───────────────────────────┘      │
 │   S3 gateway endpoint (uploads, backups)   interface endpoints: ECR, Secrets Manager   │
 └────────────────────────────────────────────────────────────────────────────────────────┘
   AWS Backup with a cross-region copy · ECR (Harbor can replicate into it)
   CloudWatch alarms → SNS → on-call · IAM roles everywhere, no long-lived access keys
```

| On-prem component | AWS equivalent | What AWS runs for you | What you still own |
|---|---|---|---|
| Traefik + keepalived VIP | ALB with ACM certificates | Load balancer nodes in each AZ, certificate renewal | Listener rules, health checks, idle timeouts, WAF rules |
| Swarm managers + Dokploy | ECS (or EKS) control plane | Scheduling, control-plane availability | Task definitions, deployment settings, capacity |
| Three VMs | Auto Scaling group or Fargate across two or three AZs | Replacing failed instances | Images/AMIs, scaling policy, patching (EC2) |
| PostgreSQL primary, replica, pgBackRest | RDS Multi-AZ, automated backups with PITR (up to 35 days) | Failover (typically 60–120 s for a Multi-AZ instance), backups | Parameters, connections, restore drills |
| MinIO or NAS | S3 | Durability and availability of objects | Bucket policies, lifecycle, Object Lock, encryption |
| Harbor | ECR | Registry availability, scanning | Lifecycle policies, pull permissions |
| Prometheus, Alertmanager | CloudWatch + SNS (or managed Prometheus and Grafana) | Storage and availability of metrics | Alarm design, dashboards, runbooks |

Three design choices in that drawing are worth defending in a review:

**One NAT gateway per AZ.** A NAT gateway lives in one AZ. If both private subnets route through
the gateway in AZ a and AZ a fails, AZ b loses outbound access too, so your "two-AZ" design has a
one-AZ egress. Two gateways cost more per hour; the ADR should say which you chose and why.

**Health checks that test the app, not the instance.** The ALB health check path must exercise
the application (for example `/healthz`), and the Auto Scaling group should use the ELB health
check type, or a dead app on a live instance is never replaced.

**Multi-AZ is not a backup.** The RDS standby receives every mistake synchronously, including a
`DROP TABLE`. Point-in-time restore and AWS Backup copies in another region are what protect you
from those.

**Key terms:** region, Availability Zone, Multi-AZ, Auto Scaling group, target group, health check
type, NAT gateway, gateway endpoint, interface endpoint.

**See it on a real system (sandbox account).**

```bash
aws elbv2 describe-target-health --target-group-arn TG_ARN \
  --query 'TargetHealthDescriptions[].[Target.Id,Target.Port,TargetHealth.State,TargetHealth.Reason]' --output text
aws rds describe-db-instances --db-instance-identifier shop-db \
  --query 'DBInstances[0].[MultiAZ,AvailabilityZone,SecondaryAvailabilityZone,BackupRetentionPeriod]' --output text
aws ec2 describe-nat-gateways --query 'NatGateways[].[NatGatewayId,SubnetId,State]' --output text
```

```
i-0a1b2c3d4e5f60718	80	healthy	None
i-0f9e8d7c6b5a40312	80	unhealthy	Target.ResponseCodeMismatch
True	eu-west-1a	eu-west-1b	7
nat-0123456789abcdef0	subnet-0aaa1111bbbb2222c	available
```

→ One target fails its health check with the wrong status code: typically the app answers the
health check path with a 301/302 redirect, and the target group only accepts 200 by default. RDS
is Multi-AZ with seven days of backups. There is only **one** NAT gateway, the zonal SPOF
described above.

**Hands-on lab (sandbox account only, budget alarm set first)**

**Step 1 — Build it.** Repeat the load-balancer lab from [Cloud & AWS](36-learn-cloud-aws.md)
section 6, but put the instances in an Auto Scaling group `lab-asg` (min 2, max 4) spread over two
subnets in different AZs, with health check type `ELB`.

**Step 2 — Break it.** Kill one instance and watch the platform heal, then simulate an AZ loss by
removing a subnet from the group:

```bash
aws ec2 terminate-instances --instance-ids i-0a1b2c3d4e5f60718
aws autoscaling describe-scaling-activities --auto-scaling-group-name lab-asg --max-items 3 \
  --query 'Activities[].[StartTime,StatusCode,Description]' --output text
aws autoscaling update-auto-scaling-group --auto-scaling-group-name lab-asg \
  --vpc-zone-identifier "subnet-0bbb2222cccc3333d"
```

Keep a `curl` loop against the ALB DNS name running in another terminal. Expect a few errors at
most, while the ALB stops sending traffic to the terminated target.

**Step 3 — Fix it.** Restore both subnets in `--vpc-zone-identifier`, wait for two healthy targets,
then delete everything the same day (Auto Scaling group with `--force-delete`, load balancer,
target group, launch template). Write down how long the replacement took from termination to
`healthy`; that number goes into the RTO column of your design.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Health check gets a redirect | Targets `unhealthy`, `Target.ResponseCodeMismatch` | `aws elbv2 describe-target-health` | [Cloud & AWS](36-learn-cloud-aws.md) section 6 |
| Security group blocks the ALB | Targets `unhealthy`, `Target.Timeout` | `aws ec2 describe-security-groups --group-ids SG_ID` | [Cloud & AWS](36-learn-cloud-aws.md) section 3 |
| Single NAT gateway, AZ outage | Private instances in the healthy AZ cannot reach the internet | Route tables per subnet | [Cloud & AWS](36-learn-cloud-aws.md) section 3 |
| App caches the DB address | Errors for minutes after an RDS failover | App connection pool settings, DNS TTL | [Learn: Databases](38-learn-databases-ops.md) |
| ASG uses EC2 health checks only | Dead app never replaced | `aws autoscaling describe-auto-scaling-groups --query 'AutoScalingGroups[].HealthCheckType'` | [AWS reference](16-aws-cloud.md) |

**Why it matters for troubleshooting.** Managed services move the failure modes rather than remove
them: you stop debugging keepalived and start debugging health check codes, security groups and
route tables. The mapping table tells you which on-prem instinct applies to which AWS component.

**Next step:** combine both worlds, so that AWS protects the on-prem platform.

### Hybrid DR with AWS [L4 · Lead/SRE]

**Concept.** A small on-prem team rarely needs a second data centre. It needs a place to recover
to. AWS can be that place, at low cost, if the data is already there and the environment can be
created on demand. This is the **pilot light** tier from section 5:

```
 ON-PREM (primary)                                            AWS eu-west-1 (DR, pilot light)
 ┌───────────────────────────────┐   Site-to-Site VPN    ┌────────────────────────────────────┐
 │ Traefik VIP → Swarm apps      │ ═════════════════════ │ VPC, subnets, security groups:     │
 │ db-01 PostgreSQL 16 primary   │ ── WAL archive ─────▶ │   always deployed (Terraform)      │
 │                               │    over HTTPS         │ S3: pgBackRest repo2, versioned,   │
 │ Harbor                        │ ── replication ─────▶ │   Object Lock                      │
 │ GitLab                        │ ── nightly backup ──▶ │ ECR: same images, same tags        │
 └───────────────────────────────┘                       │ OFF until declared: ASG at 0,      │
               ▲                                         │   PostgreSQL EC2 restored from S3  │
               │  Route 53 failover records (TTL 60)     │ ACM certificate already issued     │
               └─────────────────────────────────────────┴────────────────────────────────────┘
```

Two variants, chosen per app by its RPO and RTO:

| Variant | Data path | RPO | RTO | Running cost |
|---|---|---|---|---|
| Pilot light | pgBackRest repo in S3 (WAL archive, `archive_timeout` 60 s); restore into an EC2 PostgreSQL when declared | About 1 minute | 1–3 hours (restore time grows with database size) | S3 storage, the VPN, ECR |
| Warm standby | A PostgreSQL streaming replica on a small EC2 instance over the VPN; one app instance running | Seconds | 15–30 minutes | The above plus two small instances |

Physical pgBackRest backups cannot be restored into RDS (RDS gives no access to the data
directory), so the DR database is PostgreSQL on EC2, or you accept a logical-dump path with a
worse RPO. That is the kind of constraint that belongs in the design doc before anyone promises
an RPO.

The design rule that matters most is **independence**: the DR side must not need anything that
died with the primary. Walk the dependency map from section 2 and check each edge:

| Dependency | If it lives only on-prem | DR-ready version |
|---|---|---|
| DNS zone | Cannot change records during the disaster | Public zone in Route 53 (or a provider with an API), TTL 60 on failover records |
| Container images | Harbor is down, nothing to pull | Harbor replicates to ECR on every push |
| Secrets | Vault or password manager on-prem | Copies in AWS Secrets Manager, or a sealed break-glass copy |
| Certificates | Let's Encrypt HTTP-01 needs the old edge | ACM certificate issued in advance |
| Partner allowlists | Partners only allow 203.0.113.10 | DR egress IPs (Elastic IPs) registered with partners in advance |
| People and access | SSO or VPN that runs on-prem | Break-glass IAM access with MFA, tested twice a year |

**Key terms:** pilot light, warm standby, failover routing, failback, break-glass access,
independence of the recovery site.

**See it on a real system.** Prove that the DR data is fresh and that DNS can move quickly:

```bash
sudo -u postgres pgbackrest --stanza=main info
dig +noall +answer shop.example.com
aws route53 get-health-check-status --health-check-id HEALTH_CHECK_ID \
  --query 'HealthCheckObservations[0].StatusReport.Status' --output text
```

```
stanza: main
    status: ok
    cipher: aes-256-cbc

    db (current)
        wal archive min/max (16): 000000010000002A00000012/000000010000002B0000004F

        full backup: 20260928-010002F
            timestamp start/stop: 2026-09-28 01:00:02+00 / 2026-09-28 01:21:47+00
            wal start/stop: 000000010000002A00000012 / 000000010000002A00000013
            database size: 18.2GB, database backup size: 18.2GB
            repo1: backup set size: 4.1GB, backup size: 4.1GB

        full backup: 20260928-020001F
            timestamp start/stop: 2026-09-28 02:00:01+00 / 2026-09-28 02:26:30+00
            wal start/stop: 000000010000002A00000016 / 000000010000002A00000017
            database size: 18.2GB, database backup size: 18.2GB
            repo2: backup set size: 4.1GB, backup size: 4.1GB
shop.example.com.	60	IN	A	203.0.113.10
Success: HTTP Status Code 200, OK. Resolved IP: 203.0.113.10.
```

→ Each repository (local repo1 and S3 repo2) holds a recent full backup; pgBackRest writes each
backup to one repository, so repo2 gets its own backup run (`--repo=2`), while WAL is archived to
both. The WAL archive is moving, so the S3 copy can restore to within about a minute of now. The record's TTL is 60 seconds and the
Route 53 health check sees the on-prem site as healthy. Each of these lines is a precondition for
the DR plan; if any one is missing, the RTO in the plan is fiction.

**Hands-on lab (sandbox account only)**

**Step 1 — Build it.** Upload last night's dump of the lab database to a versioned S3 bucket in the
sandbox account (`aws s3 cp appdb.dump s3://BUCKET/dr/appdb.dump`).

**Step 2 — Break it.** Declare the lab "primary" lost: from now on you may not touch dok-01 or
db-01. Start a timer.

**Step 3 — Fix it.** In the sandbox, start one small EC2 instance with Docker, run `postgres:16`,
download the dump and restore it with `pg_restore`, then run one smoke query that a real app
would run. Stop the timer and delete the instance and the bucket. The time you measured, scaled by
the size of your real database, is the honest RTO of pilot light for your team.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| DR depends on the primary | Failover blocked: no DNS changes, no images, no secrets | Walk the independence table above | Section 2, dependency maps |
| WAL shipping silently stopped | Restore ends hours earlier than expected | `pgbackrest info`, `pg_stat_archiver` | [Learn: Databases](38-learn-databases-ops.md) |
| Long DNS TTL | Clients keep going to the dead site for hours | `dig +noall +answer NAME` | [DNS](08-dns.md) |
| DR Terraform never applied | `terraform apply` fails on the day | A quarterly apply into a test account | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| No failback plan | Stuck in DR for weeks, data diverging | The failback section of the DR plan | Section 5 |

**Why it matters for troubleshooting.** During a real disaster you have no time to discover
missing dependencies. A Lead's job is to discover them on a calm Tuesday, which is what the
independence table and the drills in the next section are for.

**Next step:** disaster recovery as a discipline: backups, RPO/RTO, DR tiers and drills.

---

## 5. Disaster recovery

> 📚 **Study path:** 1) Note: [Learn: Databases for DevOps](38-learn-databases-ops.md) for dumps, physical backups, WAL and replication, because every DR plan is a data plan first · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance → [Backup and Restore Methods](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods) for etcd on your homelab ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) KodeKloud: *Docker Certified Associate* — the Swarm High Availability/Quorum and Disaster Recovery lessons ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) KodeKloud: *Fundamentals of SRE* — Chaos Engineering, for game days ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 5) Read: Google SRE book chapter 26, *Data Integrity: What You Read Is What You Wrote*, from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 6) Practice: the restore drill below; the RTO you measure is the only one that counts.

**Who starts here:** juniors own backups and prove them with restores; mid-level engineers turn
business needs into RPO and RTO numbers; seniors choose DR tiers per app and write the plan; leads
run game days and make the organisation fund what the plan needs.

**Disaster recovery (DR)** is everything that gets the service and its data back after an event
the HA design did not absorb: a lost site, a destroyed disk, ransomware, a bad migration, a
deleted volume. HA handles the expected failures automatically. DR handles the rest, mostly with
people following a plan.

### Backup strategy [L1 · Junior]

**Concept.** A backup is a restore you have not tried yet. The rule most teams use is **3-2-1-1-0**:

| Rule | Meaning | On your platform |
|---|---|---|
| 3 copies | Production data plus two backups | Live DB, backup repo on mon-01, off-site copy |
| 2 media | Not all on the same kind of storage or system | Local disk plus object storage |
| 1 off-site | Survives losing the building | S3 bucket or a second site |
| 1 immutable or offline | Survives ransomware and a mistaken `rm` with admin rights | S3 Object Lock, or an append-only backup server |
| 0 errors | Restores are tested and verified, not assumed | Monthly automated restore test |

Backups, replication and snapshots protect against different things. Teams that confuse them find
out during the incident:

| Mechanism | Protects against | Does not protect against |
|---|---|---|
| Replication (streaming replica, RDS Multi-AZ) | Losing a server | Mistakes: a `DROP TABLE` replicates in milliseconds |
| Snapshots on the same storage (LVM, ZFS, hypervisor) | Bad upgrades, quick rollback | Losing that storage or that host |
| Backups off-host with retention | Mistakes, corruption, lost hosts | Nothing, if they are tested and the keys are safe |
| Immutable backups | An attacker or script deleting backups | Slow discovery: retention must be longer than detection time |

What needs a backup on this platform, and how:

| What | Where it lives | Method | How often | Watch out |
|---|---|---|---|---|
| App PostgreSQL 16 databases | db-01, or Dokploy DB containers | pgBackRest (full + WAL) and `pg_dump -Fc` for single-table restores | Continuous WAL, nightly backup | A copied data directory of a running server is not a backup |
| App MySQL 8 databases | shop-db container | `mysqldump --single-transaction --routines --triggers --events` or MySQL Shell dump utilities | Nightly, plus binary logs for point-in-time | `--single-transaction` is consistent for InnoDB tables only |
| Dokploy's own state | `dokploy-postgres` and `/etc/dokploy` | Dokploy's backup feature to an S3 destination where your version offers it, or `pg_dump` plus `tar` | Nightly and before every Dokploy upgrade | `/etc/dokploy` holds `acme.json` and the Traefik dynamic files |
| Uploads in named volumes | `/var/lib/docker/volumes/...` | restic | Nightly | Move uploads to object storage in the HA design |
| Harbor | Harbor's database, `/data`, `harbor.yml` | Harbor's documented backup procedure | Nightly | Images can be rebuilt; robot accounts, tags and signatures cannot |
| GitLab | GitLab server | `sudo gitlab-backup create`, plus `/etc/gitlab/gitlab-secrets.json` and `gitlab.rb` | Nightly | The secrets file is not inside the backup archive |
| Private CA key | Offline | Encrypted copy in two separate places | On every change | Losing it means re-issuing and re-distributing every certificate |
| Host configuration | `/etc/apache2`, netplan, keepalived, Traefik | Git + Ansible | Every change | Rebuild from code; back up only what code cannot recreate |
| Secrets | Password manager or Vault | Its export procedure, sealed break-glass copy | On change | Test that the break-glass copy opens |

**Key terms:** 3-2-1-1-0, retention, immutability, Object Lock, append-only, restore test,
consistency (crash-consistent versus application-consistent), dead man's switch.

**See it on a real system.**

```bash
systemctl list-timers --all | grep -Ei 'backup|restic|pgbackrest'
restic -r sftp:backup@192.168.56.30:/srv/restic snapshots --latest 3
cat /var/lib/prometheus/node-exporter/backup.prom
```

```
Sun 2026-10-04 01:37:12 UTC 15h left  Sat 2026-10-03 01:41:55 UTC 8h ago  platform-backup.timer  platform-backup.service
repository 3f7a91c2 opened (version 2, compression level auto)
ID        Time                 Host        Tags        Paths
------------------------------------------------------------------------
9c1e4f2a  2026-10-01 01:43:10  dok-01      nightly     /var/backups/stage
71b2d0e8  2026-10-02 01:42:51  dok-01      nightly     /var/backups/stage
e40a6c19  2026-10-03 01:44:02  dok-01      nightly     /var/backups/stage
------------------------------------------------------------------------
3 snapshots
# HELP platform_backup_last_success_timestamp_seconds Unix time of the last successful backup.
# TYPE platform_backup_last_success_timestamp_seconds gauge
platform_backup_last_success_timestamp_seconds 1790991842
```

→ The timer ran 8 hours ago, the repository holds one snapshot per night, and the host exports
the time of the last **successful** run as a metric. That last line is the important one: you
alert when success is missing, not when failure is reported, because a backup job that never
starts reports nothing.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** On dok-01, create a small lab database with a table worth losing:

```bash
docker run -d --name lab-pg -e POSTGRES_PASSWORD=lab-only-password postgres:16
sleep 5; docker exec lab-pg createdb -U postgres appdb
docker exec lab-pg psql -U postgres -d appdb -c \
  "CREATE TABLE orders AS SELECT g AS id, now() - g * interval '1 minute' AS created FROM generate_series(1,5000) g;"
```

On mon-01 create a `backup` user and the directory `/srv/restic` (SFTP access only), and put
dok-01's root SSH public key in that user's `authorized_keys`. Run `sudo sftp backup@192.168.56.30`
once from dok-01 so root accepts mon-01's host key (restic cannot answer that prompt). On dok-01, install restic (`sudo apt install -y restic`), write the repository
password to `/etc/restic/password` (mode 600) and an environment file:

```bash
sudo install -d -m 700 /etc/restic
sudoedit /etc/restic/env
```

```
RESTIC_REPOSITORY=sftp:backup@192.168.56.30:/srv/restic
RESTIC_PASSWORD_FILE=/etc/restic/password
```

```bash
sudo bash -c 'set -a; . /etc/restic/env; restic init'
```

The backup script dumps the lab database and Dokploy's configuration, sends them to the
repository, applies retention and records success:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/platform-backup.sh
set -euo pipefail
STAGE=/var/backups/stage
STAMP=$(date +%F)
mkdir -p "$STAGE"
docker exec lab-pg pg_dump -U postgres -Fc appdb > "$STAGE/appdb-$STAMP.dump"
tar -C /etc -czf "$STAGE/dokploy-etc-$STAMP.tgz" dokploy
restic backup "$STAGE" --tag nightly
restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
rm -f "$STAGE"/*
# temp file in the target directory: node_exporter reads only *.prom, and mv is then an atomic rename
TMP=$(mktemp /var/lib/prometheus/node-exporter/backup.prom.XXXXXX)
printf '# HELP platform_backup_last_success_timestamp_seconds Unix time of the last successful backup.\n# TYPE platform_backup_last_success_timestamp_seconds gauge\nplatform_backup_last_success_timestamp_seconds %s\n' "$(date +%s)" > "$TMP"
chmod 644 "$TMP"
mv "$TMP" /var/lib/prometheus/node-exporter/backup.prom
```

`docker exec` runs without `-t` on purpose: a TTY would corrupt the binary dump. The metric file is
written to a temporary file in the same directory and renamed, so node_exporter never reads half a
file (a temporary file in `/tmp` would be copied, not renamed, when `/tmp` is a separate tmpfs). `set -e` means
the success metric is only updated when every step worked.

Schedule it with a systemd service and timer:

```ini
# /etc/systemd/system/platform-backup.service
[Unit]
Description=Nightly platform backup to restic
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
EnvironmentFile=/etc/restic/env
ExecStart=/usr/local/sbin/platform-backup.sh
Nice=10
IOSchedulingClass=idle
```

```ini
# /etc/systemd/system/platform-backup.timer
[Unit]
Description=Run the platform backup every night

[Timer]
OnCalendar=*-*-* 01:30:00
RandomizedDelaySec=15m
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo chmod 750 /usr/local/sbin/platform-backup.sh
sudo systemctl daemon-reload && sudo systemctl enable --now platform-backup.timer
sudo systemctl start platform-backup.service && journalctl -u platform-backup.service -n 20 --no-pager
```

Add the alert on mon-01. It fires when the last success is older than 26 hours or the metric is
missing entirely:

```yaml
groups:
  - name: backups
    rules:
      - alert: BackupNotSucceededRecently
        expr: time() - platform_backup_last_success_timestamp_seconds > 26 * 3600
        for: 15m
        labels:
          severity: ticket
        annotations:
          summary: "No successful platform backup on {{ $labels.instance }} for over 26 hours"
      - alert: BackupMetricMissing
        expr: absent(platform_backup_last_success_timestamp_seconds)
        for: 1h
        labels:
          severity: ticket
```

**Step 2 — Break it.** Make a realistic mistake in the lab database: drop a table that matters:

```bash
docker exec lab-pg psql -U postgres -d appdb -c 'DROP TABLE orders;'
```

**Step 3 — Fix it.** Restore into a **scratch** location first, never straight over production,
then copy back only what was lost:

```bash
sudo bash -c 'set -a; . /etc/restic/env; restic restore latest --target /tmp/restore'
ls /tmp/restore/var/backups/stage/
docker exec lab-pg createdb -U postgres appdb_restore
docker exec -i lab-pg pg_restore -U postgres -d appdb_restore < /tmp/restore/var/backups/stage/appdb-2026-10-03.dump
docker exec lab-pg psql -U postgres -d appdb_restore -Atc 'SELECT count(*) FROM orders;'
docker exec lab-pg bash -c 'pg_dump -U postgres -d appdb_restore -t orders | psql -U postgres -d appdb'
```

Time the whole restore, then make it routine: a monthly job that restores the newest dump into a
scratch database, runs a row-count check and records a `platform_restore_test_last_success_timestamp_seconds`
metric the same way. Run `restic check --read-data-subset=5%` weekly to catch repository damage
early. Clean up with `docker exec lab-pg dropdb -U postgres appdb_restore` and
`sudo rm -rf /tmp/restore`.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Timer disabled or job failing | No new snapshots; nobody notices for weeks | `systemctl list-timers`, `journalctl -u platform-backup` | [systemd](07-services-systemd.md) |
| Backup of live database files | Restore starts but PostgreSQL reports corruption | Check the method: file copy instead of dump or pgBackRest | [Learn: Databases](38-learn-databases-ops.md) |
| Repository password lost with the host | Backups exist but cannot be decrypted | Is the password in the break-glass vault? | Section 5, this topic |
| Backups in the same failure domain | Host lost, backups lost with it | `df -h` on the backup path; where is the copy? | Section 2, failure domains |
| Retention shorter than detection | Ransomware or silent corruption older than the oldest backup | `restic snapshots` oldest date | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Staging disk fills | Backup fails with `no space left on device` | `df -h /var/backups` | [Storage & disk](01-storage-disk.md) |

**Why it matters for troubleshooting.** The first question in any data incident is "what is the
newest good copy, and how long does it take to get it back?". If you answer that from a metric and
a tested runbook, the incident is a procedure, not a crisis.

**Next step:** put numbers on "how much data can we lose" and "how long can we be down".

### RPO and RTO [L2 · Mid]

**Concept.** Two numbers drive every DR decision:

```
       last good copy           disaster                          service restored
             │                     │                                     │
 ────────────●─────────────────────✖─────────────────────────────────────●──────▶ time
             │◀─────── RPO ───────▶│◀──────────────── RTO ──────────────▶│
               data you can lose      detect → decide → rebuild → restore → verify → DNS
```

**RPO (Recovery Point Objective)** is the maximum acceptable data loss, measured in time. **RTO
(Recovery Time Objective)** is the maximum acceptable time until the service works again. Both are
**business** decisions: you supply the cost of each option, the app owner chooses. A first set for
your platform might look like this:

| App or service | RPO | RTO | Why |
|---|---|---|---|
| shop | 5 min | 1 h | Revenue; orders cannot be re-created |
| api | 15 min | 2 h | Partners retry, but not for long |
| blog | 24 h | 1 day | Content changes weekly |
| intranet | 24 h | 2 days | Few users, workarounds exist |
| Dokploy control plane | 24 h | 4 h | Running apps keep serving; only deploys stop |
| Harbor | 24 h | 4 h | Running apps keep serving; deploys and scaling stop |
| GitLab | 24 h | 1 day | Code also lives on laptops; pipelines stop |

What the backup method makes possible, at best:

| Method | Achievable RPO | Note |
|---|---|---|
| Nightly dump | Up to 24 h, plus the dump duration | Worse if a night fails and nobody notices |
| Hourly snapshots | 1 h | Only if the snapshot leaves the host |
| WAL archiving (pgBackRest), `archive_timeout = 60s` | About 1 min | Each forced switch still archives a 16 MB segment (compressed by pgBackRest) |
| Asynchronous streaming replica | Seconds | Not a backup: replicates mistakes |
| Synchronous replica | Zero for committed transactions | Every commit waits for the replica; the primary stalls if the only sync replica dies |

The RTO is a sum of phases, and the slowest phase is usually not the technical one:

| Phase | Typical on this platform | How to shorten it |
|---|---|---|
| Detect | 5 min with alerts, hours without | Outside probe, alert routing (section 11) |
| Decide | 10–30 min | Decision authority written in the DR plan |
| Provision | 15 min to days | Spare capacity, IaC, a pre-built VM template |
| Restore data | 18 GB at 150 MB/s ≈ 2 min, plus WAL replay | Test it: replaying a day of WAL can take longer than the base restore |
| Verify | 10–20 min | A scripted smoke test per app |
| DNS | Up to the old TTL | TTL 300 or less on records that may move |

Restoring from off-site storage is bounded by bandwidth: 100 GB over a 100 Mbit/s link is about
800 Gbit ÷ 0.1 Gbit/s = 8,000 s, or 2.2 hours, before any database work starts.

**Key terms:** RPO, RTO, MTTD (mean time to detect), MTTR (mean time to restore), recovery
point, data loss window, decision authority.

**See it on a real system.** Measure the RPO you have right now, not the one in the wiki:

```bash
sudo -u postgres psql -Atc "SELECT now() - last_archived_time, failed_count, last_failed_time FROM pg_stat_archiver;"
sudo -u postgres psql -h 192.168.56.22 -Atc "SELECT now() - pg_last_xact_replay_timestamp();"
```

```
00:00:41.208311|0|
00:00:00.532781
```

→ The last WAL segment reached the archive 41 seconds ago and archiving has never failed, so the
backup RPO is about a minute. The replica (db-02) is half a second behind. On a quiet primary the
replica value grows even though nothing is lost (no new transactions to replay), so read it
together with write activity.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** Write target RPO and RTO for the two lab apps (who and the lab database) in
a table like the one above, with a one-line reason for each.

**Step 2 — Break it.** Power off dok-01 at a moment you do not choose (ask someone, or use
`sleep $((RANDOM % 3600))` before a `virsh destroy` on the hypervisor). Recover using only the
runbook and backups.

**Step 3 — Fix it.** Fill the phase table with measured minutes. Compare to your targets. For each
phase that blew the target, write one concrete action (an alert, a template VM, a script, a lower
TTL) with an owner and a date. That list is the input for the DR tier choice in the next topic.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| `archive_command` failing | WAL piles up in `pg_wal` until the disk fills and PostgreSQL stops | `SELECT * FROM pg_stat_archiver;`, `du -sh $PGDATA/pg_wal` | [Learn: Databases](38-learn-databases-ops.md) |
| RPO promised from the backup start time | Real loss includes the dump duration and failed nights | Newest successful backup timestamp | This topic |
| RTO assumes the expert is awake | 2am restore takes four times longer | Run the drill with someone else | Section 5, game days |
| TTL 86400 on a record you will move | Clients reach the dead site for a day | `dig +noall +answer NAME` | [DNS](08-dns.md) |
| Off-site restore over a slow link | Restore takes hours just to download | Link speed × data size | [Network speed](24-playbook-network-speed.md) |

**Why it matters for troubleshooting.** During a data incident, RPO and RTO are the decision
frame: restore now and lose 40 seconds of orders, or spend an hour on repair and lose none. With
agreed numbers, the IC can make that call in minutes instead of arguing about it.

**Next step:** choose how much DR each app gets.

### DR tiers [L3 · Senior]

**Concept.** Not every app deserves the same protection. The four standard strategies (also used
in AWS's own DR guidance) trade cost against RPO and RTO:

| Tier | How it works | RPO | RTO | Cost | On-prem example | AWS example |
|---|---|---|---|---|---|---|
| Backup and restore | Backups off-site; rebuild everything on demand | Hours | Hours to days | $ | restic and pgBackRest to object storage | AWS Backup, S3 cross-region copy |
| Pilot light | Data replicated continuously; core infrastructure defined but compute off | Minutes | Tens of minutes to hours | $$ | WAL archive in S3, Terraform ready (section 4) | Cross-region read replica, ASG at 0 |
| Warm standby | A scaled-down, fully working copy always running | Seconds to minutes | Minutes | $$$ | Second room with a replica and a one-node Swarm | Smaller ASG running, replica promoted on failover |
| Multi-site active/active | Both sites serve traffic all the time | Near zero | Near zero | $$$$ | Rarely sensible for a small on-prem team | Multi-region with Route 53 and global databases |

Two senior habits make tiers work:

**Tier by business impact, then by dependency.** Put each app in a tier (Tier 0: foundations such
as DNS, identity, the edge; Tier 1: revenue; Tier 2: important internal; Tier 3: can wait). A Tier 1
app cannot recover faster than its slowest Tier 0 dependency, so the restore order follows the
dependency map from section 2: DNS, network and VPN, secrets, registry, databases, apps.

**Cost the gap in money.** "Warm standby for the shop costs about 250 dollars a month and
removes most of a 2-hour outage risk; an hour of shop downtime costs about 4,000 dollars in lost
orders" is a sentence a manager can decide on. "We need more DR" is not.

The DR plan is a short document that someone else can execute. A template:

```markdown
# DR plan: platform (dok-prod)   Version 3 · Owner: ops lead · Reviewed: 2026-09-15

## 1. Scope and tiers
| App | Tier | RPO | RTO | Strategy | Runbook |
|---|---|---|---|---|---|
| shop | 1 | 5 min | 1 h | Warm standby (AWS) | runbooks/dr-shop.md |
| api | 1 | 15 min | 2 h | Pilot light | runbooks/dr-api.md |
| blog, intranet | 3 | 24 h | 2 days | Backup and restore | runbooks/dr-restore-generic.md |

## 2. Who declares a disaster
Primary: ops lead. Deputy: IT manager. Declare when: the primary site cannot be restored
within half of the shortest RTO in scope, or data integrity is in doubt.

## 3. Contacts and access
On-call rota link, vendor and ISP contacts, break-glass access location (sealed envelope 2).

## 4. Recovery order
1 DNS and VPN · 2 secrets · 3 registry (ECR) · 4 databases · 5 Tier 1 apps · 6 the rest

## 5. Communication
Status page owner, customer template (section 12), update interval 30 min.

## 6. Failback
Criteria to return, data resync direction, planned window, who approves.

## 7. Test history
| Date | Test type | Measured RTO | Gaps found | Actions |
|---|---|---|---|---|
```

The plan must live where the disaster cannot reach it: in Git **and** as a printed or offline
copy, not only on the wiki hosted on the platform it describes.

**Key terms:** DR tier, application tier, recovery order, declaration criteria, failback, plan
owner.

**See it on a real system.** Check the plan against reality. For each Tier 1 app, three facts must
match what the plan claims:

```bash
dig +noall +answer shop.example.com api.example.com
aws s3api get-bucket-versioning --bucket example-dr-backups --query Status --output text
aws s3api get-object-lock-configuration --bucket example-dr-backups \
  --query 'ObjectLockConfiguration.Rule.DefaultRetention' --output text
```

```
shop.example.com.	60	IN	A	203.0.113.10
api.example.com.	3600	IN	A	203.0.113.10
Enabled
30	COMPLIANCE
```

→ The shop record can move within a minute, but the api record has a one-hour TTL, so a 2-hour RTO
is already half spent waiting for caches. The bucket is versioned and locked in compliance mode
for 30 days, which means even an administrator cannot delete backups younger than that: exactly
what you want against ransomware, and exactly what you must budget for in storage.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write the DR plan for your real platform with the template above: every app
tiered, every tier with a strategy, and a recovery order taken from your dependency map.

**Step 2 — Break it.** Give the plan to a colleague and ask them to find one dependency that would
block the recovery (the classic answer: "the plan is on the wiki, the wiki is on dok-prod-01").

**Step 3 — Fix it.** Fix every gap they find, add the monthly cost of each tier, and get the app
owners to sign off on their RPO and RTO in the MR that adds the plan.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Everything is Tier 1 | Budget never approved, nothing improves | Ask for the cost of one hour of downtime per app | Section 7, cost |
| DR side drifts | Failover fails on config differences | Same IaC and pipeline for both sides | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| Plan stored on the platform | Nobody can read the plan during the disaster | Keep a copy in Git and offline | This topic |
| No declaration criteria | Team debugs for hours instead of failing over | Write the criteria in section 2 of the plan | Section 11, incident command |
| No failback plan | Weeks in DR, data diverging between sites | Write failback before the first drill | [Cloud & AWS](36-learn-cloud-aws.md) section 13 |

**Why it matters for troubleshooting.** In a large incident the hardest decision is when to stop
troubleshooting and start recovering. Declaration criteria and tiers make that a rule instead of a
judgement made by tired people at 3am.

**Next step:** prove the plan works before you need it.

### DR drills and game days [L4 · Lead/SRE]

**Concept.** An untested DR plan is a hypothesis. Drills test it in steps of increasing realism:

| Level | What happens | How often | Risk |
|---|---|---|---|
| 1. Tabletop | The team talks through a scenario with the plan open, no systems touched | Quarterly | None |
| 2. Component restore | Restore one database or volume into a scratch environment and verify it | Monthly (automate it) | None |
| 3. Functional failover | Fail over one app in the lab or staging, end to end, with a timer | Quarterly | Low |
| 4. Production game day | Planned failure in production with abort criteria and everyone ready | Once or twice a year | Controlled |

A **game day** borrows from chaos engineering: state a hypothesis about steady state ("the shop
keeps serving with dok-prod-01 powered off"), inject a real failure, observe, and stop immediately
if the abort criteria are met. The point is to find surprises while everyone is awake, rested and
watching, instead of at 2am.

A game day plan, short enough to read in five minutes:

```markdown
# Game day 2026-11: lose the edge node

Hypothesis: with dok-prod-01 powered off, all Tier 1 sites keep answering 200 within 30 s
(VIP moves to dok-prod-02), Tier 3 sites may return the maintenance page, no data is lost.
Scope: dok-prod-01 only. Not in scope: databases, Harbor.
When: Tuesday 10:00–12:00 (low traffic, everyone in office). Change: CR-2026-058.
Roles: facilitator (Ravi), IC (Sam), operator (Priya), scribe (Anil), observer (IT manager).
Steady-state signals: blackbox probe success, Traefik 5xx rate, shop checkout synthetic test.
Abort criteria: any Tier 1 site non-200 for more than 2 minutes, or 5xx above 5 % for 5 minutes,
or any data inconsistency. Abort action: power dok-prod-01 back on, restore VIP priority.
Injection: hypervisor hard power-off of dok-prod-01 at a time chosen by the facilitator.
Measure: time to detect, time to VIP move, time to all green, pages sent, runbook gaps.
After: postmortem within 5 days, actions in the tracker with owners and dates.
```

**Key terms:** tabletop exercise, game day, hypothesis, steady state, blast radius, abort
criteria, facilitator, injection.

**See it on a real system.** The evidence of a drill is a timeline. During the drill, the scribe
can pull exact times instead of guessing:

```bash
journalctl -u keepalived --since "2026-11-10 10:00" --until "2026-11-10 10:30" | grep -E 'Entering (MASTER|BACKUP)'
curl -sG http://mon-01:9090/api/v1/query_range \
  --data-urlencode 'query=min(probe_success{job="blackbox"})' \
  --data-urlencode 'start=2026-11-10T10:05:00Z' --data-urlencode 'end=2026-11-10T10:15:00Z' \
  --data-urlencode 'step=15s' | jq -r '.data.result[0].values[] | "\(.[0] | todate) \(.[1])"' | uniq -f1
```

```
Nov 10 10:07:42 dok-prod-02 Keepalived_vrrp[912]: (EDGE) Entering MASTER STATE
2026-11-10T10:05:00Z 1
2026-11-10T10:07:30Z 0
2026-11-10T10:07:45Z 1
```

→ The power-off happened just before 10:07:30, the VIP moved at 10:07:42, and every probe was
green again by 10:07:45. That is measured evidence for the hypothesis, and the numbers go straight
into the DR plan's test history.

**Hands-on lab (homelab, with a second person)**

**Step 1 — Build it.** Write a game day plan for the lab using the template, with real abort
criteria. Ask a friend or colleague to act as facilitator and keep the injection time secret.

**Step 2 — Break it.** The facilitator powers off dok-01 at a random moment within a two-hour
window. You respond only from the runbooks and the DR plan, as if paged at 2am.

**Step 3 — Fix it.** Recover, then hold a 30-minute review the same day: what surprised you, which
runbook step was wrong or missing, what took longest. Turn each finding into an action with an
owner and a date, and update the DR plan's test history.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Drill always run by the expert | "Passed", yet nobody else can do it | Rotate the operator role; experts only observe | Section 12, mentoring |
| Same scenario every time | Only one failure path is ever tested | Rotate scenarios: disk, DB, DNS, registry, people | Section 2 |
| No abort criteria | The drill turns into a real outage | Write abort criteria and the abort action first | This topic |
| Findings never fixed | The same gaps appear in every drill | Track actions like postmortem actions | Section 11, postmortems |
| Failback skipped | Return to normal becomes the real outage | Make failback part of the drill | Section 5, DR tiers |

**Why it matters for troubleshooting.** People troubleshoot the way they have practised. A team
that has failed over three times in daylight fails over calmly at night; a team that never has
will improvise, and improvisation under pressure is where most data loss happens.

**Next step:** the slow-moving risks: running out of capacity and blowing the latency budget.

---

## 6. Capacity planning and performance budgets

> 📚 **Study path:** 1) Note: [Performance & observability](32-learn-performance-observability.md) section 16 (Capacity planning) and section 15 (SLIs, SLOs and error budgets), because this section adds the senior layer on top of them · 2) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals → [Node Exporter](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page), then the PromQL lessons ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 3) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil (capacity planning) and Observability and Monitoring → [Performance Monitoring Deep Dive](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0)), only if PromQL still feels abstract · 5) Practice: the disk-fill forecast and latency-budget labs below on mon-01, dok-01 and db-01.

**Who starts here:** mid-level engineers already read saturation from dashboards (module 32);
seniors turn those numbers into dates ("we must add a node by March") and into budgets that each
layer has to respect.

Capacity incidents are the most preventable ones: the data predicting them existed for weeks. The
senior skill is not running the query, it is making the forecast part of the routine and turning
it into a purchase, a change or a design decision **before** the lead time runs out.

### Capacity planning [L3 · Senior]

**Concept.** Capacity planning answers one question: will we have enough of every resource, with
one node down, by the time we could get more? It needs five inputs:

| Input | Meaning | Where it comes from |
|---|---|---|
| Peak demand | The busy-hour value, not the average | p95 or max over 30 days in Prometheus |
| Growth rate | How fast peak demand rises | Month-over-month change of that peak |
| Lead time | How long it takes to add capacity | Weeks or months for hardware, minutes in the cloud |
| Target utilisation | How full you allow a resource to get | About 60–70% for CPU, less for latency-critical paths |
| Failure headroom | Survive the loss of the biggest node (N+1) | The HA design in section 4 |

```
needed  = peak_now × (1 + monthly_growth) ^ (lead_time + horizon, in months) ÷ target_utilisation
check   = capacity of (all nodes − the biggest one) ≥ needed        ← N+1
```

**Worked example.** Three nodes with 8 vCPU each (24 vCPU). The p95 of total CPU use over 30 days
is 9.5 vCPU. Peak demand grows 4% a month. New hardware takes three months to arrive and you plan
three months beyond that, so six months in total:

| Step | Calculation | Result |
|---|---|---|
| Peak in six months | 9.5 × 1.04⁶ = 9.5 × 1.265 | 12.0 vCPU |
| At 70% target utilisation | 12.0 ÷ 0.70 | 17.2 vCPU needed |
| Capacity with one node down | 2 × 8 | 16 vCPU |
| Verdict | 16 < 17.2 | Order now; in six months a node failure at peak would saturate the rest |

Without the N+1 line the platform looks fine (24 vCPU against 17.2), which is exactly how
"redundant" clusters fall over: the survivors cannot carry the load of the dead node.

CPU is rarely the first thing to run out. Seniors keep a checklist of every finite resource:

| Resource | First symptom when it runs out | How to watch it |
|---|---|---|
| Disk space (logs, images, DB growth, build cache) | `no space left on device`, crashed databases | `predict_linear` on `node_filesystem_avail_bytes` |
| Memory | OOM kills, swap storms | `node_memory_MemAvailable_bytes`, `dmesg` OOM lines |
| Disk IOPS and latency | Slow everything, high `iowait` | `rate(node_disk_io_time_seconds_total[5m])` |
| conntrack table | `nf_conntrack: table full, dropping packet` | `node_nf_conntrack_entries` against `node_nf_conntrack_entries_limit` |
| Overlay network addresses | New tasks fail: `node is missing network attachments, ip addresses may be exhausted` | Subnet size versus tasks + services + nodes |
| Database connections | `too many connections` / `remaining connection slots are reserved` | `pg_stat_activity` count versus `max_connections` |
| Harbor and backup storage | Pushes or backups fail | Repository size trend, retention policies |
| Prometheus TSDB | Scrapes dropped, disk full on mon-01 | `prometheus_tsdb_storage_blocks_bytes` |
| Certificate issuance | ACME orders rejected | Let's Encrypt limits, such as 50 new certificates per registered domain per week |
| People | Toil crowds out planned work | On-call load (section 11) |

The overlay line surprises many Dokploy users. `dokploy-network` gets a /24 from Swarm's default
address pool unless it was created otherwise: about 250 usable addresses shared by every task
replica, every service VIP and one load-balancer address per node. Two replicas per app across 60
apps already needs 120 + 60 + 3 addresses.

**Key terms:** peak versus average, growth rate, lead time, target utilisation, headroom, N+1,
saturation, forecast, capacity review.

**See it on a real system.** From mon-01 and a manager node:

```bash
PROM=http://mon-01:9090/api/v1/query
curl -sG "$PROM" --data-urlencode \
  'query=quantile_over_time(0.95, sum(rate(node_cpu_seconds_total{mode!="idle"}[5m]))[30d:5m])' \
  | jq -r '.data.result[0].value[1]'
curl -sG "$PROM" --data-urlencode \
  'query=(node_filesystem_avail_bytes{mountpoint="/"} / -deriv(node_filesystem_avail_bytes{mountpoint="/"}[7d]) / 86400) > 0' \
  | jq -r '.data.result[] | "\(.metric.instance) \(.value[1] | tonumber | floor) days until full"'
docker network inspect dokploy-network --format '{{json .IPAM.Config}}'
docker service ls --format '{{.Replicas}}' | awk -F/ '{t+=$2; s++} END {print s" services, "t" tasks"}'
docker system df
```

```
9.48
dok-prod-01:9100 23 days until full
db-01:9100 141 days until full
[{"Subnet":"10.0.1.0/24","Gateway":"10.0.1.1"}]
41 services, 88 tasks
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          64        19        23.4GB    16.8GB (71%)
Containers      27        23        1.21GB    96.3MB (7%)
Local Volumes   18        14        19.7GB    2.1GB (10%)
Build Cache     212       0         7.9GB     7.9GB
```

→ Peak CPU is 9.5 vCPU (the input of the worked example). The root filesystem of dok-prod-01 fills
in 23 days at last week's rate, and the last command shows why: 16.8 GB of old images and 7.9 GB of
build cache, because Dokploy builds on the host. The overlay network uses about 88 + 41 + 3 = 132
of roughly 250 addresses. None of this is urgent today; all of it has a date.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** On mon-01 add a forecast alert. In production use a 7-day window and a
14-day horizon; for the lab, use one hour and one day so it fires quickly:

```yaml
groups:
  - name: capacity
    rules:
      - alert: DiskWillFillSoon
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 24 * 3600) < 0
        for: 10m
        labels:
          severity: ticket
        annotations:
          summary: "{{ $labels.instance }}: / predicted to fill within 24 h at the current rate"
          runbook_url: "https://gitlab.example.com/ops/runbooks/-/blob/main/disk-full.md"
```

**Step 2 — Break it.** Reproduce the most common real cause: a chatty container with Docker's
default `json-file` log driver, which never rotates logs unless told to:

```bash
docker run -d --name chatty alpine:3.20 sh -c 'while :; do echo "$(date) order-sync retry for id=$RANDOM failed: upstream timeout"; done'
sleep 300; sudo du -sh /var/lib/docker/containers/$(docker inspect -f '{{.Id}}' chatty)
```

Within the hour the forecast alert fires, long before the disk is actually full. That gap between
"alert" and "outage" is the whole point of forecasting.

**Step 3 — Fix it.** Remove the container, then set log rotation defaults in
`/etc/docker/daemon.json` (they apply to containers created afterwards):

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
```

```bash
docker rm -f chatty
sudo systemctl restart docker
docker run -d --name chatty2 alpine:3.20 sh -c 'echo hello; sleep 3600'
docker inspect -f '{{.HostConfig.LogConfig}}' chatty2 && docker rm -f chatty2
```

Restarting Docker interrupts the containers on that node; live-restore covers standalone
containers, not Swarm services. On production, drain the node first
(`docker node update --availability drain NODE`), restart, set it back to `active`, one node at a
time in a change window. Then add `docker image prune -a -f --filter until=168h` and
`docker builder prune -f --filter until=168h` to a weekly timer (`-f` skips the confirmation
prompt, which would otherwise abort the job when no terminal is attached), and write a one-page **capacity
review** for the lab: each resource from the checklist, today's use, forecast date, action.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Planning on averages | Fine all month, saturated every busy hour | Compare p95 or max with avg over 30 days | [Performance & observability](32-learn-performance-observability.md) |
| No N+1 check | Cluster survives on paper, falls over when a node dies | Capacity of nodes minus the biggest | This topic |
| Logs without rotation | Disk fills from `/var/lib/docker/containers` | `sudo du -sh /var/lib/docker/containers/*` | [Storage & disk](01-storage-disk.md) |
| Overlay addresses exhausted | New tasks stuck, `ip addresses may be exhausted` | `docker network inspect dokploy-network` | [Containers & K8s](26-playbook-containers-k8s.md) |
| conntrack full | Random connection drops under load, `table full` in `dmesg` | `sudo sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max` | [Network speed](24-playbook-network-speed.md) |
| Lead time ignored | Forecast right, hardware arrives after the outage | Lead time column in the capacity review | This topic |

**Why it matters for troubleshooting.** Many "sudden" outages are capacity curves that crossed a
line. When you troubleshoot, ask "has this been growing?" and look at 30 days, not 30 minutes.

**Next step:** budgets for latency and resources, so that each layer knows its share.

### Performance budgets [L3 · Senior]

**Concept.** An SLO says "95% of shop requests complete in under 800 ms". A **performance budget**
splits that number across the layers a request passes through, so every owner knows their share
and a regression is caught in the layer that caused it:

| Layer | Budget (p95) | Measured by |
|---|---|---|
| Traefik routing and middlewares | 10 ms | Traefik entry point versus service duration |
| Application code (excluding DB and external calls) | 400 ms | App metrics or traces |
| Database queries, total per request | 150 ms | `pg_stat_statements`, slow query log |
| External APIs (with timeout and fallback) | 150 ms | Client-side metrics |
| Headroom for variance | 90 ms | — |
| Server-side total | 800 ms | `traefik_service_request_duration_seconds` |

Network setup (DNS, TCP and TLS for a new visitor) comes on top and is measured from the client
side. The budget also tells you where timeouts belong: each inner timeout must be shorter than the
budget of the layer that calls it (section 3, timeouts).

Budgets are not only for latency. **Resource budgets** give each app reservations and limits so a
single app cannot starve the node:

| Setting | Effect | Without it |
|---|---|---|
| Memory reservation | Scheduler only places the task where that much memory is free | Tasks packed onto a node until it swaps |
| Memory limit | The container is OOM-killed instead of the host | One leak takes down every app on the node |
| CPU limit | Caps a runaway process | One busy loop slows every neighbour |

In Dokploy, set these in the application's resource settings rather than with
`docker service update`, because Dokploy re-applies its own service definition on the next deploy
and would silently remove a manual change.

**Key terms:** latency budget, performance budget, resource budget, reservation, limit, noisy
neighbour, N+1 query pattern.

**See it on a real system.** Measure the client-side phases, then the server-side p95 per service:

```bash
curl -s -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://shop.example.com/
curl -sG http://mon-01:9090/api/v1/query --data-urlencode \
  'query=histogram_quantile(0.95, sum by (le, service) (rate(traefik_service_request_duration_seconds_bucket[5m])))' \
  | jq -r '.data.result[] | "\(.metric.service)\t\(.value[1])"'
```

```
dns=0.012 tcp=0.031 tls=0.087 ttfb=0.612 total=0.640
shop-web-1a2b3c-1-websecure@swarm	0.734
blog-web-4d5e6f-1-websecure@swarm	0.181
legacy-apache@file	1.920
```

→ For this visitor, connection setup took 87 ms and the server about 525 ms (TTFB minus TLS). At
p95 the shop uses 734 of its 800 ms, so the headroom is almost gone; the legacy Apache service is
at 1.9 s and has no budget at all. These histograms exist when Prometheus metrics are enabled in
Traefik's static configuration; [Performance & observability](32-learn-performance-observability.md)
section 11 covers scraping.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** On db-01 create a benchmark database, then measure the baseline round trip
from dok-01 with `pgbench` from the official image (select-only, four clients, 30 seconds). This
assumes db-01 already accepts password logins from 192.168.56.0/24 (`listen_addresses`, a
`pg_hba.conf` line, and the lab password set on the `postgres` role):

```bash
# on db-01
sudo -u postgres createdb bench && sudo -u postgres pgbench -i bench
# on dok-01
docker run --rm -e PGPASSWORD=lab-only-password postgres:16 \
  pgbench -h 192.168.56.21 -U postgres -S -c 4 -T 30 bench | grep -E 'latency average|tps'
```

```
latency average = 1.221 ms
tps = 3273.961422 (without initial connection time)
```

**Step 2 — Break it.** Add 20 ms of latency to everything db-01 sends. This also slows SSH, so
run it from the hypervisor console, and remove it afterwards:

```bash
sudo tc qdisc add dev ens18 root netem delay 20ms
```

```
latency average = 21.304 ms
tps = 187.752090 (without initial connection time)
```

→ Each query now costs 20 ms more. A page that runs 12 queries one after another (the N+1
pattern) gains 240 ms, which consumes more than the whole 150 ms database budget. The database is
not slower; the distance to it is. That is why the budget table is per request, not per query.

**Step 3 — Fix it.** Remove the delay (`sudo tc qdisc del dev ens18 root`) and rerun the baseline.
Then make the budget enforceable: add an alert when a service's p95 exceeds its budget for 15
minutes (severity `ticket`), list the budgets in the app's design doc, and ask developers to
batch queries (one query returning 12 rows instead of 12 queries) wherever the database sits on
another host.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Budget not owned by anyone | p95 creeps up release after release | p95 per service over 90 days | [Performance & observability](32-learn-performance-observability.md) |
| N+1 queries across hosts | Fast in dev (DB on localhost), slow in production | `pg_stat_statements` calls per request | [Slow system](23-playbook-slow-system.md) |
| No memory limit | One leaking app triggers the host OOM killer, many apps die | `sudo dmesg -T`, look for `Killed process` | [Memory](04-memory.md) |
| Limit too tight | Task restarts in a loop, `OOMKilled` | `docker inspect -f '{{.State.OOMKilled}}' CONTAINER` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Manual limits overwritten | Limits vanish after the next Dokploy deploy | `docker service inspect SERVICE --format '{{json .Spec.TaskTemplate.Resources}}'` | This topic |

**Why it matters for troubleshooting.** "The site is slow" becomes "the shop spends 600 ms in the
database against a 150 ms budget", which names the layer and the owner in one sentence.

**Next step:** every resource in this section costs money; make the cost visible.

---

## 7. Cost and FinOps

> 📚 **Study path:** 1) Note: [Cloud & AWS](36-learn-cloud-aws.md) section 12 (Cost and FinOps): reading the bill, common bill surprises, rightsizing and commitments, the AWS mechanics this section assumes · 2) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Cost and Performance Optimization domain ([course](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 3) KodeKloud: *AWS Certified Cloud Practitioner (CLF-C02)* — billing and pricing, only if the vocabulary is new ([course](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02)) · 4) Docs: the cost optimization pillar of the AWS Well-Architected Framework in the [AWS documentation](https://docs.aws.amazon.com/) · 5) Practice: the cost-per-app worksheet for your on-prem platform, then the monthly sandbox bill review below.

**Who starts here:** juniors learn that every resource has an owner and a price; mid-level
engineers clean up waste they created; seniors build the cost model, attach a cost to every
design option and make trade-offs between money and reliability explicit.

Every architecture is also a bill. A design review that ends without "what does it cost per month,
and what do we get for it?" is not finished. The senior contribution is rarely the clever saving;
it is making cost **visible**, **owned** and **compared with value**, so the organisation stops
cutting the wrong things.

### On-prem cost model [L3 · Senior]

**Concept.** On-prem infrastructure is not free; its costs are spread over budgets that nobody
adds up. **Total cost of ownership (TCO)** puts them on one page. An illustrative monthly model for
a three-node platform (replace the numbers with your own currency and prices):

| Cost item | Basis | Per month |
|---|---|---|
| Servers | 3 × 9,000 over 48 months | 563 |
| Backup NAS and disks | 3,000 over 48 months | 63 |
| Power and cooling | 3 × 350 W × 730 h = 767 kWh × PUE 1.6 × 0.15 per kWh | 184 |
| Rack space or server room share | Facilities estimate | 300 |
| Internet links (two ISPs) | Contracts | 400 |
| Licences and support | Hypervisor support, hardware warranty | 200 |
| Off-site backup storage | 2 TB in object storage | 50 |
| People | 0.5 FTE of a loaded 5,000 per month | 2,500 |
| **Total** | | **4,260** |

With 12 apps on the platform that is about 355 per app per month. Two lessons fall out of almost
every model like this:

**People time dominates.** Half an engineer costs more than all the hardware together, so
automation, runbooks and toil reduction (section 11) are cost work, not just quality work. A
change that saves two hours of manual work a week saves more than retiring a server.

**Consolidation trades money for blast radius.** Moving 12 apps onto fewer, bigger hosts lowers
the hardware line and raises the failure domain from "some apps" to "all apps". Both numbers belong
in the same ADR.

**Unit costs** make the model useful in conversations: cost per app, per deploy, per GB of backup,
per 1,000 orders. "The shop costs 410 a month to run and earns 60,000" settles arguments that
"the platform is expensive" cannot.

**Key terms:** TCO, CapEx, OpEx, amortisation, PUE (power usage effectiveness), loaded cost,
utilisation, unit cost, showback, chargeback.

**See it on a real system.** Utilisation tells you whether you paid for capacity you use:

```bash
PROM=http://mon-01:9090/api/v1/query
curl -sG "$PROM" --data-urlencode \
  'query=avg_over_time((1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))[30d:1h])' \
  | jq -r '.data.result[] | "\(.metric.instance)\tcpu \(.value[1] | tonumber * 100 | floor)%"'
curl -sG "$PROM" --data-urlencode \
  'query=1 - avg_over_time(node_memory_MemAvailable_bytes[30d]) / node_memory_MemTotal_bytes' \
  | jq -r '.data.result[] | "\(.metric.instance)\tmem \(.value[1] | tonumber * 100 | floor)%"'
docker ps --format '{{.Names}}' | grep -vE '^dokploy' | wc -l
```

```
dok-prod-01:9100	cpu 31%
db-01:9100	cpu 6%
harbor:9100	cpu 3%
dok-prod-01:9100	mem 71%
db-01:9100	mem 38%
harbor:9100	mem 22%
23
```

→ The app host averages 31% CPU (fine, peaks are higher) and 71% memory, which is the real limit.
db-01 and the Harbor VM are nearly idle: candidates for smaller VMs on the hypervisor, as long as
the smaller size still covers their peaks and the N+1 rule.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Fill the TCO table for your real platform. Ask facilities or finance for
the numbers you do not know; an estimate with a stated basis beats a blank.

**Step 2 — Break it.** Ask "what is missing?" with a colleague. Typical gaps: people time,
on-call compensation, the second ISP, backup storage growth, the cost of the last outage.

**Step 3 — Fix it.** Compute cost per app, list the three biggest cost lines, and propose two
savings, each with its reliability trade-off written next to it ("shrink db-01 from 8 to 4 vCPU:
saves 30 a month, peak CPU still under 50%, no change to failure domains").

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Hidden people cost | "On-prem is free" in every discussion | Add the FTE line to the model | This topic |
| Zombie VMs and containers | Resources nobody can name | Owner labels on VMs, Dokploy projects and containers | Section 8, golden paths |
| Unbounded retention | Backup, log and metric storage grow every month | Retention settings per store | Section 6, capacity |
| Harbor never cleaned | Registry disk grows without limit | Tag retention rules plus scheduled garbage collection in Harbor | [Learn: Docker](30-learn-docker.md) |
| Savings that move risk | Cheaper platform, bigger outages | Write the trade-off in an ADR | Section 10 |

**Why it matters for troubleshooting.** Cost data is operational data. An unexpected jump in
egress, storage or CPU-hours is often the first sign of a runaway job, a leak or a compromised
host, and it shows up in the bill before anyone looks at a dashboard.

**Next step:** the cloud version, where every resource has a price per hour.

### Cloud FinOps [L3 · Senior]

**Concept.** **FinOps** is the practice of engineering, finance and product sharing
responsibility for cloud spend. It runs as a loop of three phases:

| Phase | Question | Typical work |
|---|---|---|
| Inform | Who spends what, on what? | Tags, cost allocation, dashboards, showback per team or app |
| Optimize | Are we paying for value? | Rightsizing, commitments, cleanup, architecture changes |
| Operate | Does it stay optimised? | Budgets, anomaly alerts, monthly reviews, tagging policies |

The levers, roughly in the order a senior applies them (cleanup and rightsizing first, so you
never commit to waste):

| Lever | Typical saving | Risk or trade-off |
|---|---|---|
| Delete idle: unattached EBS volumes, old snapshots, idle load balancers, unused public IPv4 addresses | Small to medium, low risk once confirmed | Deleting DR or evidence resources; tag before deleting |
| Rightsize instances and databases (Compute Optimizer, CloudWatch p95) | Often 20–40% of the resized items | Too small fails at peak; memory needs the CloudWatch agent to be visible |
| Schedule non-production (12 hours × 5 days) | About 64% of those instances (60 of 168 hours running) | Broken mornings if start-up is not automated |
| gp2 → gp3 volumes | About 20% of EBS cost | Rarely any; gp3 includes 3,000 IOPS and 125 MB/s baseline |
| Graviton (arm64) instances | Often around 20% lower hourly price | Images must be multi-arch (`docker buildx`) |
| Savings Plans or Reserved Instances for the steady baseline | Up to roughly 66–72% against on-demand | One- or three-year commitment; over-committing is pure waste |
| Spot for stateless workers and CI runners | Up to about 90% | Two-minute interruption notice |
| S3 lifecycle rules, Intelligent-Tiering | Large for cold data | Retrieval fees and minimum storage durations |
| VPC gateway endpoints for S3 and DynamoDB | Removes NAT data processing for that traffic; the endpoint itself is free | Interface endpoints (ECR, Secrets Manager) cost per hour per AZ |
| Log retention (CloudWatch Logs defaults to never expire) | Storage that grows forever | Compliance retention needs |
| Data transfer design (cross-AZ chatter, egress) | Depends | Cross-AZ costs per GB each way, but single-AZ costs resilience |

All percentages are typical list-price figures at the time of writing; check the current pricing
pages for your region before you put a number in a proposal.

**Unit cost** is the FinOps number that matters to the business: "cost per 1,000 orders went from
3.10 to 2.40" proves an optimisation without the noise of a growing business, where the total bill
may rise even while efficiency improves.

**Key terms:** FinOps, showback, chargeback, cost allocation tags, rightsizing, Savings Plans,
Spot, unit cost, anomaly detection.

**See it on a real system (sandbox or a read-only billing role).** Each Cost Explorer API request
is billed (about one cent), so run these monthly, not in a loop:

```bash
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text \
  | sort -t$'\t' -k2 -rn | head -6
aws ec2 describe-volumes --filters Name=status,Values=available \
  --query 'Volumes[].[VolumeId,Size,CreateTime]' --output text
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].PublicIp' --output text
aws logs describe-log-groups --query 'logGroups[?!retentionInDays].logGroupName' --output text
```

```
Amazon Elastic Compute Cloud - Compute	1843.27
Amazon Relational Database Service	612.40
EC2 - Other	544.91
Amazon Elastic Load Balancing	187.30
AmazonCloudWatch	142.66
Amazon Simple Storage Service	96.12
vol-0c1d2e3f4a5b6c7d8	200	2025-11-14T09:12:44.000Z
vol-0a9b8c7d6e5f4a3b2	50	2026-02-02T16:40:03.000Z
198.51.100.44
/aws/lambda/old-thumbnailer	/ecs/shop-web	/ecs/shop-worker
```

→ "EC2 - Other" is the line people misread: it holds EBS volumes and snapshots, NAT gateways and
data transfer, not instances. Two unattached volumes (250 GB) have been paid for since last year,
one Elastic IP is not attached to anything, and three log groups keep everything forever. Each is
a ticket with an owner, not a midnight `delete` spree: confirm the owner first, snapshot or export
if in doubt, then delete.

**Hands-on lab (sandbox account only)**

**Step 1 — Build it.** Define a tagging policy with four mandatory tags (`app`, `env`, `owner`,
`cost-center`), apply it to everything in the sandbox, and activate `app` and `env` as cost
allocation tags in the Billing console. Check that the budget alarm from
[Cloud & AWS](36-learn-cloud-aws.md) section 0 still exists.

**Step 2 — Break it.** Create two untagged resources on purpose (a 1 GB gp2 volume and an
unattached Elastic IP), then find them with the commands above and with the Tag Editor in the
console (search all resource types where the `owner` tag is "(not tagged)").

**Step 3 — Fix it.** Delete both, then write the agenda of a 30-minute monthly cost review: top
five services and their change versus last month, untagged spend, idle resources found, one
optimisation to try, and the unit cost trend. Run it once on the sandbox bill.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Savings that remove redundancy | Bill down, an outage later (single NAT, single-AZ database) | Write the trade-off in an ADR before the change | Section 10 |
| Commitments before rightsizing | Savings Plan covers instances you later shrink | Rightsize first, commit to the remaining baseline | This topic |
| Untagged spend | Nobody owns a third of the bill | Tag policy plus a monthly untagged report | This topic |
| "Unused" DR resources deleted | DR fails at the next drill | Tag DR resources with `purpose=dr` and exclude them | Section 5 |
| Chasing cents | Hours spent on a 5-dollar resource | Work top-down from the largest service lines | This topic |

**Why it matters for troubleshooting.** A cost anomaly is an incident signal: egress tripling
overnight can mean a misconfigured backup, a crawler, or exfiltration. Treat a budget alert like
any other alert: who changed what, when.

**Next step:** reduce the cost of every new app by giving developers one paved way to ship it.

---

## 8. Platform engineering

> 📚 **Study path:** 1) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Optimization, Security and Monitoring (includes, templates, `extends`), then Continuous Deployment ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 2) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 2 (GitLab CI/CD) and [Deployment patterns](35-deployment-patterns.md) section 4 (Deployment recipes) · 3) Docs: Dokploy ([docs](https://docs.dokploy.com/docs/core)) and GitLab's [CI quick start](https://docs.gitlab.com/ci/quick_start/) · 4) Practice: the KodeKloud [CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd) for the pipeline mechanics, then the paved-road component lab below, used by two projects.

**Who starts here:** mid-level engineers write the first shared CI template; seniors design the
golden path and keep it working; leads run the platform as a product with users, metrics and a
roadmap.

**Platform engineering** is building the internal tools and defaults that let developers ship
safely without asking the ops team for every step. It is how a senior engineer scales: instead of
deploying 20 apps, you make deploying an app something 20 teams can do the same, correct way.

### Golden paths [L3 · Senior]

**Concept.** A **golden path** (or paved road) is the supported, documented and automated way to do
a common task: create a service, deploy it, add a domain, get a database, get alerts. It is not
mandatory; it is simply so much easier than the alternatives that most teams choose it. On your
platform the path for a new service could look like this:

```
 developer ──▶ "new-service" template repo ──▶ git push ──▶ paved-road CI component
                                                             (lint, test, build, scan, push)
                                                                        │
                         Harbor: signed, scanned image  ◀──────────────┘
                                   │  deploy job calls the Dokploy API (token in a masked variable)
                                   ▼
               Dokploy app: replicas, health check, limits, domain ──▶ Traefik route + TLS
                                   │
           defaults from day one: blackbox probe, dashboard, alert → on-call, runbook stub, SLO
```

The template repository is where the defaults live, so every new service starts with them instead
of adding them after the first incident:

| Default in the template | Why it is there |
|---|---|
| Dockerfile: pinned base image, non-root user, `HEALTHCHECK` | Security and correct health checks (section 3) |
| `/healthz` endpoint and `/metrics` | The probe and the dashboard work on the first deploy |
| `.gitlab-ci.yml` that only includes the platform components | Every pipeline gets fixes centrally |
| `README.md` with owner, SLO, dependencies | Section 2 dependency map, section 11 SLOs |
| `runbook.md` stub with the standard sections | Section 12 runbooks |
| Resource reservations and limits | Section 6 resource budgets |

Dokploy can already be a small internal developer platform: projects and environments, apps from
Git or from a registry image, generated Traefik routes with certificates, managed databases with
scheduled backups, and an API for pipelines. A senior also knows where it stops:

| Need | Dokploy on Swarm | Kubernetes (kubeadm, k3s, EKS) |
|---|---|---|
| Team size and skills | One to three ops people | Needs Kubernetes skills (CKA level) |
| Self-service UI | Built in | Needs a portal or GitOps (Argo CD, Backstage) |
| Multi-team isolation and RBAC | Coarse (projects, users) | Namespaces, RBAC, quotas, NetworkPolicies |
| Autoscaling | Manual replica counts | HPA, cluster autoscaler |
| GitOps | Webhooks and API | Argo CD or Flux, native |
| Control-plane HA | One Dokploy instance | Three control-plane nodes with etcd quorum |
| Ecosystem | Small | Large: cert-manager, Kyverno, CloudNativePG, operators |
| Running cost in people | Low | Medium to high |

Move to Kubernetes when you need what its column offers (several teams with isolation,
autoscaling, policy, GitOps at scale), not because it is popular. Exercise 6 in section 16 is
exactly this decision.

**Key terms:** golden path, paved road, internal developer platform (IDP), self-service, template
repository, thinnest viable platform, platform team.

**See it on a real system.** How many services are actually on the path? Ask GitLab:

```bash
for p in $(glab api "groups/apps/projects?per_page=100" | jq -r '.[].path_with_namespace'); do
  if glab api "projects/${p//\//%2F}/repository/files/.gitlab-ci.yml/raw?ref=main" 2>/dev/null \
       | grep -q 'platform/ci-components'; then echo "on-path  $p"; else echo "off-path $p"; fi
done | sort | uniq -c -w8
```

```
      9 off-path apps/blog-web
     14 on-path  apps/api
```

→ 14 of 23 projects use the platform components; 9 still carry their own pipelines. The off-path
list is your adoption backlog, and each one is a conversation ("what does the path lack that you
need?"), not an order.

**Hands-on lab (lab GitLab or GitLab.com sandbox group)**

**Step 1 — Build it.** Create a `templates/new-service` repository with the defaults from the table
above: a Dockerfile with a non-root user and `HEALTHCHECK`, a `/healthz` route, a `README.md` with
owner and SLO fields, a `runbook.md` stub, and a `.gitlab-ci.yml` that only includes the platform
components (next topic). Mark it as a template project.

**Step 2 — Break it.** Create a new service from the template and time how long it takes a
colleague, who has never done it, to get it deployed on the lab Dokploy with a domain. Note every
question they ask.

**Step 3 — Fix it.** Every question is a missing default or a missing line of documentation. Fix
them in the template, then measure again. "Time to first deploy" is the headline metric of a
golden path; under an hour is a good first target.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Path harder than the shortcut | Teams copy old pipelines instead | Ask the off-path teams what is missing | This topic |
| Template copied, never updated | 23 slightly different pipelines | Include components; do not copy files | Next topic |
| Mandated, not adopted | Shadow pipelines, hidden servers | Make the path the easiest option, then measure adoption | Section 8, platform as a product |
| Defaults missing in old services | Only new services have probes and limits | Backfill as a tracked project | Section 15, classes of incidents |

**Why it matters for troubleshooting.** When every service has the same health endpoint, log
format, dashboard and runbook layout, the on-call engineer debugs the 23rd service as fast as the
first. Uniformity is a troubleshooting tool.

**Next step:** the mechanism that keeps pipelines uniform: versioned CI components.

### Paved-road CI templates [L3 · Senior]

**Concept.** A shared CI template only helps if it is **included** (so fixes reach every project)
and **versioned** (so a fix in one place cannot break 23 pipelines at once). GitLab's CI/CD
components do both: a component lives in its own project, takes typed inputs and is referenced at
a released version. They need a recent GitLab (17.0 or later is the safe line for self-managed);
on older versions, `include: project:` with `ref:` set to a tag gives the same pinning without
inputs.

The component project `platform/ci-components` holds one file per component:

```yaml
# templates/docker-build.yml
spec:
  inputs:
    image:
      description: "Harbor path without registry or tag, for example apps/shop-web"
    context:
      default: "."
    stage:
      default: build
---
"build-and-push":
  stage: $[[ inputs.stage ]]
  image: docker:28
  services:
    - name: docker:28-dind
      alias: docker
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE: "harbor.example.com/$[[ inputs.image ]]"
  before_script:
    - echo "$HARBOR_ROBOT_TOKEN" | docker login harbor.example.com -u "$HARBOR_ROBOT_USER" --password-stdin
  script:
    - docker build --pull -t "$IMAGE:$CI_COMMIT_SHORT_SHA" "$[[ inputs.context ]]"
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

```yaml
# templates/deploy-dokploy.yml
spec:
  inputs:
    image:
      description: "Same Harbor path as the build component"
    dokploy_app_id:
      description: "Application ID shown in the Dokploy UI"
    domain:
      description: "Public hostname, used for the GitLab environment URL"
---
"deploy-production":
  stage: deploy
  image: docker:28
  services:
    - name: docker:28-dind
      alias: docker
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE: "harbor.example.com/$[[ inputs.image ]]"
  script:
    - echo "$HARBOR_ROBOT_TOKEN" | docker login harbor.example.com -u "$HARBOR_ROBOT_USER" --password-stdin
    - docker pull "$IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$IMAGE:$CI_COMMIT_SHORT_SHA" "$IMAGE:production"
    - docker push "$IMAGE:production"
    - apk add --no-cache curl
    - >
      curl -fsS -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_API_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$[[ inputs.dokploy_app_id ]]\"}"
  environment:
    name: production
    url: https://$[[ inputs.domain ]]
  resource_group: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

A consuming project's whole pipeline is now a few lines:

```yaml
# apps/shop-web/.gitlab-ci.yml
stages: [test, build, deploy]

include:
  - component: $CI_SERVER_FQDN/platform/ci-components/docker-build@1.4.0
    inputs:
      image: apps/shop-web
  - component: $CI_SERVER_FQDN/platform/ci-components/deploy-dokploy@1.4.0
    inputs:
      image: apps/shop-web
      dokploy_app_id: "APP_ID"
      domain: shop.example.com

unit-tests:
  stage: test
  image: node:22-alpine
  script:
    - npm ci
    - npm test
```

Design decisions worth explaining in the component's README:

**Two tags per image.** The commit tag (`:3f9c2d1`) is immutable and is what you roll back to and
audit. `:production` is the moving tag the Dokploy app is configured to pull, so the deploy job
only has to move it and trigger a deploy. If you enable tag immutability in Harbor, exclude the
`production` tag from the rule. Check the endpoint and header against the API reference of your
Dokploy version; at the time of writing a deploy is `POST /api/application.deploy` with an
`x-api-key` header.

**`resource_group: production`.** Two pipelines can never deploy at the same time; the second
waits. This removes a whole class of race conditions.

**`environment:`.** GitLab records every deployment, which is the raw data for DORA metrics
(section 14).

**Private CA.** The dind daemon must trust Harbor's CA; bake the CA into an internal dind image or
mount it through the runner configuration, never switch TLS verification off.

Versioning rules for the component project: semantic versions as Git tags, a changelog, a
pipeline that tests every change by including the component at `$CI_COMMIT_SHA` in a sample
project, and a deprecation window (announce, keep the old major version working for a defined
time, then remove).

**Key terms:** CI/CD component, inputs, interpolation, semantic versioning, pinning,
`resource_group`, environment, moving tag versus immutable tag.

**See it on a real system.** Which versions are in use, and who is still on an old major?

```bash
glab api "projects/platform%2Fci-components/releases" | jq -r '.[0:3][] | "\(.tag_name)\t\(.released_at[0:10])"'
grep -rhoE 'ci-components/[a-z-]+@[0-9.]+' ~/work/apps/*/.gitlab-ci.yml | sort | uniq -c | sort -rn
```

```
1.4.0	2026-09-22
1.3.2	2026-08-30
1.3.1	2026-08-11
     12 ci-components/docker-build@1.4.0
     12 ci-components/deploy-dokploy@1.4.0
      2 ci-components/docker-build@1.2.0
      2 ci-components/deploy-dokploy@1.2.0
```

→ Two projects lag two minor versions behind. That is normal; a major version behind would mean a
breaking change is waiting for them, and that needs an owner and a date.

**Hands-on lab (lab GitLab)**

**Step 1 — Build it.** Create `platform/ci-components` with the build component, tag `1.0.0`, and
use it from two projects pinned to `@1.0.0`. Both pipelines push to Harbor.

**Step 2 — Break it.** On `main` of the component project, rename the input `image` to
`image_path` without a new major version, and change one consuming project to reference
`@main` instead of a tag. Push a commit to that project: pipeline creation fails with an input
error, while the project pinned to `@1.0.0` keeps working. That difference is the entire argument
for pinning.

**Step 3 — Fix it.** Revert the rename on `main`, release the rename properly as `2.0.0` with a
changelog entry, migrate one project at a time through MRs, and add the self-test pipeline to the
component project so a breaking change fails there first.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Consumers track `@main` | One commit breaks every pipeline | `grep -r 'ci-components' */.gitlab-ci.yml` | This topic |
| Concurrent deploys | Two pipelines deploy different commits, last one wins at random | Check for `resource_group` | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| dind does not trust the CA | `x509: certificate signed by unknown authority` on push | Job log, CA in the dind image | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Deploy token in plain text | Token visible in job logs | Masked and protected CI variables | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| Moving tag blocked by Harbor | Push of `:production` rejected by an immutability rule | Harbor project tag immutability rules | [Learn: Docker](30-learn-docker.md) |

**Why it matters for troubleshooting.** When a pipeline breaks, the first question becomes "did
the component change, or did the project?", answerable from one version string. Without
components, every broken pipeline is its own archaeology project.

**Next step:** treat the whole platform as a product with users.

### Platform as a product [L4 · Lead/SRE]

**Concept.** A platform team's customers are developers. Treating the platform as a product means
it has users you talk to, a roadmap driven by their pain, documentation, support and measurable
outcomes, instead of being "whatever ops happened to build". The opposite, a ticket queue where
developers wait for ops to click buttons, does not scale and makes the platform team the
bottleneck.

| Product practice | On your platform |
|---|---|
| Know the users | Quarterly 30-minute interview with each team lead: what slows you down? |
| Thinnest viable platform | Start with Dokploy, components and docs; add tools only for proven needs |
| Self-service first | New app, domain, database, secret without a ticket |
| Documentation as a feature | One "getting started" page that a new developer finishes in an hour |
| Support model | Office hours twice a week, a chat channel, a response-time promise |
| Deprecation policy | Announce, migrate with help, then remove; never break users silently |
| Platform SLOs | The deploy pipeline and Dokploy API have their own availability targets |

Measure outcomes, not activity:

| Metric | Good direction | Source |
|---|---|---|
| Time to first deploy of a new service | Down | Template lab measurement |
| Share of services on the golden path | Up | Adoption script above |
| Deployment frequency and lead time | Up and down | DORA metrics (section 14) |
| Tickets to the platform team per month | Down | Issue tracker label |
| Developer satisfaction (quarterly 5-question survey) | Up | Survey |

**Key terms:** platform as a product, internal customers, self-service, thinnest viable platform,
platform SLO, deprecation policy, adoption.

**See it on a real system.** Your ticket queue tells you what to automate next:

```bash
glab api "projects/ops%2Fplatform/issues?labels=platform-request&state=closed&created_after=2026-07-01T00:00:00Z&per_page=100" \
  | jq -r '.[].labels[] | select(startswith("type::"))' | sort | uniq -c | sort -rn | head -5
```

```
     17 type::domain
     11 type::database
      8 type::resources
      5 type::ci-variable
      3 type::restart
```

→ The request templates set a scoped `type::` label, so the queue sorts itself. Seventeen tickets
in one quarter just to add a domain: that is a missing self-service feature
(teams could add domains in their own Dokploy project, with a naming rule and an automatic
certificate). The top line of this list is always your next roadmap item.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write a one-page platform charter: who the users are, what the platform
offers today, what it does not do, the support model and three outcome metrics with today's
values.

**Step 2 — Break it.** Show it to two developers and ask: "what would make you stop using this
platform?" Write the answers down verbatim.

**Step 3 — Fix it.** Turn the answers and the ticket analysis into a three-item quarterly roadmap,
each item with the metric it should move.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Building what nobody asked for | Features unused, real pain ignored | Interviews and ticket analysis first | This topic |
| Ticket ops | Developers wait days for routine changes | Automate the top ticket category | Section 15, classes of incidents |
| Platform without an SLO | Pipeline outages treated as low priority | Define and publish platform SLOs | Section 11 |
| Breaking changes without notice | Trust collapses, teams build their own | Deprecation policy, versioned components | Previous topic |

**Why it matters for troubleshooting.** Many incidents start with a workaround someone built
because the platform could not do what they needed. A platform that listens removes the
workarounds, and with them a class of hard-to-debug snowflakes.

**Next step:** migrations: the Apache to Dokploy move, planned the senior way.

---

## 9. Migration strategy

> 📚 **Study path:** 1) Note: [Case study: Apache holds 443](21-case-apache-443-dokploy.md), the technical cutover phase by phase, and its section 10 (Rollback) · 2) Note: [Deployment patterns](35-deployment-patterns.md) section 1 (Your fix: Apache moved to 81 and 444) · 3) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil → [Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress → [Traefik Overview](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page), for routers and services · 5) Read: [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/) · 6) Practice: the strangler lab below, then the migration plan for one real site, reviewed by a colleague.

**Who starts here:** mid-level engineers execute migration steps from a plan; seniors write the
plan, the risk register and the rollback criteria, and decide go or no-go; leads make sure the
organisation (support, customers, management) moves with the system.

Moving Apache to 81/444 was the **tactical** fix: it got Dokploy running the same day. Finishing
the migration so that Apache disappears without anyone noticing is the **strategic** work, and it
is where seniors earn their title. The technical steps are in module 21; this section is about
running the migration as a project.

### Strangler pattern [L3 · Senior]

**Concept.** The **strangler fig pattern** replaces a legacy system gradually. You put a routing
layer (the façade) in front of the old system, then move one route at a time to the new system,
until the old one serves nothing and can be removed. You already built the façade: Traefik on
80/443, with Apache behind it on 81/444.

```
 Phase 0 (before)        Phase 1 (façade)              Phase 2..n (move routes)        Last phase
 ┌────────────┐          ┌──────────────┐              ┌──────────────┐                ┌──────────────┐
 │  Apache    │          │  Traefik     │              │  Traefik     │                │  Traefik     │
 │  :80 :443  │   ──▶    │  :80 :443    │      ──▶     │  :80 :443    │       ──▶      │  :80 :443    │
 │  all sites │          └──────┬───────┘              └──┬────────┬──┘                └──────┬───────┘
 └────────────┘                 │ every route             │ moved  │ the rest               │ every route
                         ┌──────▼───────┐          ┌──────▼──┐  ┌──▼───────────┐     ┌──────▼───────┐
                         │ Apache :81   │          │ Dokploy │  │ Apache :81   │     │ Dokploy apps │
                         │ all sites    │          │ apps    │  │ fewer sites  │     │ Apache gone  │
                         └──────────────┘          └─────────┘  └──────────────┘     └──────────────┘
```

Why seniors prefer it over a "big bang" cutover:

| Property | Strangler | Big bang |
|---|---|---|
| Blast radius of a mistake | One route | Every site |
| Rollback | Change one route back, seconds | Restore the whole old system |
| Progress | Visible and measurable (routes moved, Apache traffic falling) | All or nothing |
| Learning | Lessons from site 1 improve site 2 | One shot |
| Risk | The façade becomes a new SPOF; must be HA (section 4) | Long freeze, high-stakes weekend |

Traefik can also move a route **gradually**: a weighted service sends a small share of requests
to the new backend, with a sticky cookie so each user stays on one side. That turns each route
move into a canary (section 3 of [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) covers canary
releases).

**Key terms:** strangler fig, façade, route, weighted service, canary, sticky session, point of no
return, decommissioning.

**See it on a real system.** Which routes still go to Apache, and how much traffic does each
legacy site still get?

```bash
sudo grep -nE 'url:|rule:' /etc/dokploy/traefik/dynamic/legacy-apache.yml
for f in /var/log/apache2/*access.log; do printf '%8d %s\n' "$(sudo grep -c "$(date +%d/%b/%Y)" "$f")" "$f"; done | sort -rn
```

```
18:      rule: "Host(`api.example.com`)"
26:      rule: "Host(`checkout.example.com`)"
33:      rule: "Host(`intranet.example.com`)"
44:          - url: "http://192.0.2.10:81"
   31877 /var/log/apache2/api-access.log
    9112 /var/log/apache2/checkout-access.log
     212 /var/log/apache2/intranet-access.log
       0 /var/log/apache2/access.log
```

→ Three routes left on Apache, and the request counts per log file are your migration burndown:
when a line reaches zero and stays there for two weeks, that site is ready for removal.

**Hands-on lab (dok-01, test VM only)**

**Step 1 — Build it.** Install Apache on dok-01 next to Dokploy. The first start fails because
Traefik already owns port 80: the original incident of module 21 in miniature. Move Apache to 81
and add one legacy site:

```bash
sudo apt install -y apache2            # apt reports that apache2 failed to start: port 80 is taken
echo 'Listen 81' | sudo tee /etc/apache2/ports.conf
sudo dpkg --configure -a               # finishes the package set-up, now on port 81
sudo mkdir -p /var/www/old && echo '<h1>old site (Apache)</h1>' | sudo tee /var/www/old/index.html
sudoedit /etc/apache2/sites-available/old.conf
```

```
<VirtualHost *:81>
    ServerName old.lab.example.com
    DocumentRoot /var/www/old
</VirtualHost>
```

```bash
sudo a2ensite old && sudo a2dissite 000-default && sudo a2enmod rewrite && sudo systemctl restart apache2
docker service create --name old-site-new --network dokploy-network traefik/whoami:v1.10
```

Then the façade with a 90/10 canary. Traefik's default self-signed certificate is enough for the
lab:

```yaml
# /etc/dokploy/traefik/dynamic/old-site.yml
http:
  routers:
    old-site:
      entryPoints: [websecure]
      rule: "Host(`old.lab.example.com`)"
      service: old-site-canary
      tls: {}
  services:
    old-site-canary:
      weighted:
        services:
          - name: old-site-apache
            weight: 9
          - name: old-site-new
            weight: 1
        sticky:
          cookie:
            name: old_site_backend
    old-site-apache:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: "http://192.168.56.11:81"
    old-site-new:
      loadBalancer:
        servers:
          - url: "http://old-site-new:80"
```

```bash
for i in $(seq 1 20); do curl -sk --resolve old.lab.example.com:443:127.0.0.1 https://old.lab.example.com/ | head -1; done | sort | uniq -c
```

```
     18 <h1>old site (Apache)</h1>
      2 Hostname: 4f2a9c1d7e3b
```

**Step 2 — Break it.** Someone "hardens" the legacy vhost with the classic HTTPS redirect, which
Apache sites carried for years when they owned 443. Add inside the `VirtualHost`:

```
    RewriteEngine On
    RewriteCond %{HTTPS} !=on
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

```bash
sudo systemctl reload apache2
curl -sSkL -o /dev/null --resolve old.lab.example.com:443:127.0.0.1 -b /dev/null https://old.lab.example.com/
```

```
curl: (47) Maximum (50) redirects followed
```

→ Traefik terminates TLS and talks plain HTTP to port 81, so Apache always sees `HTTPS=off`,
always redirects to `https://`, and the browser comes back through Traefik to the same place:
an infinite loop (browsers show "too many redirects"). Requests that the canary sends to the new
container are fine, which makes the bug look random to users.

**Step 3 — Fix it.** Trust the header Traefik sets instead of the connection Apache sees, then
reload and repeat the test with `-w '%{http_code}\n'` added (expect `200`):

```
    RewriteEngine On
    RewriteCond %{HTTP:X-Forwarded-Proto} !=https
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

Better still, delete the redirect from Apache and let Traefik own it with a redirect middleware
on the port-80 router (module 35 shows `legacy-apache-https`): one layer, one rule. Then move the weight to 50/50 and 0/100, watching the
error rate at each step, and finally remove the Apache server from the weighted service. Clean up
with `docker service rm old-site-new`, the YAML file, `sudo a2dissite old` and
`sudo systemctl disable --now apache2`.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Redirect loop behind the façade | `ERR_TOO_MANY_REDIRECTS`, curl error 47 | `curl -skI` through Traefik, read the `Location` header | [Learn: Web servers & proxies](29-learn-webservers-proxies.md) |
| Real client IP lost | Apache logs and fail2ban see only Traefik's address | Apache log source addresses; configure `mod_remoteip` | [Deployment patterns](35-deployment-patterns.md) |
| Forgotten consumer | A cron job or partner still calls `:444` or the old IP directly | Apache logs by source address after the move | [Who owns this port?](22-playbook-ports-inventory.md) |
| Sessions break at the weight change | Users logged out, carts emptied | Session store shared? sticky cookie set? | This topic |
| Façade is a new SPOF | Traefik down = every site down, old and new | Section 4 HA design | [Site down](25-playbook-site-down.md) |

**Why it matters for troubleshooting.** During a strangler migration two systems serve one domain.
The first question for any bug report becomes "which backend served this request?", so make it
answerable: log the Traefik service name, or add a response header per backend.

**Next step:** plan the whole Apache to Dokploy migration as a project.

### Apache to Dokploy, the senior way [L3 · Senior]

**Concept.** A senior migration plan has seven parts. Each answers a question someone will ask,
usually at the worst moment if the plan does not answer it first.

| Part | Question it answers |
|---|---|
| 1. Inventory | What exactly are we moving, and who owns it? |
| 2. Classification | What happens to each item: move, rebuild, keep, retire? |
| 3. Risk register | What can go wrong, how likely, how bad, and what do we do about it? |
| 4. Phased cutover | In what order, with what entry and exit criteria? |
| 5. Success metrics | How do we know it worked? |
| 6. Rollback | How do we undo each phase, and until when is undo possible? |
| 7. Communication plan | Who needs to know what, and when? |

**1. Inventory.** Collect it from the system, not from memory (module 21 phase 1 has the full
method). The short version:

```bash
sudo apachectl -S 2>/dev/null | grep -E 'namevhost|alias'
sudo grep -rhoE '(ProxyPass|SSLCertificateFile|AuthType|Require ip) .*' /etc/apache2/sites-enabled/ | sort | uniq -c
sudo grep -rlE 'example\.com|curl|wget' /etc/cron.d /etc/cron.daily /var/spool/cron/crontabs 2>/dev/null
sudo certbot certificates 2>/dev/null | grep -E 'Certificate Name|Expiry Date'
```

```
         port 81 namevhost api.example.com (/etc/apache2/sites-enabled/api.conf:1)
         port 81 namevhost checkout.example.com (/etc/apache2/sites-enabled/checkout.conf:1)
         port 81 namevhost intranet.example.com (/etc/apache2/sites-enabled/intranet.conf:1)
         port 444 namevhost checkout.example.com (/etc/apache2/sites-enabled/checkout-ssl.conf:2)
      1 AuthType Basic
      2 ProxyPass / http://127.0.0.1:3001/
      1 Require ip 198.51.100.0/24
      1 SSLCertificateFile /etc/letsencrypt/live/checkout.example.com/fullchain.pem
/var/spool/cron/crontabs/www-data
  Certificate Name: checkout.example.com
    Expiry Date: 2026-11-21 08:14:02+00:00 (VALID: 49 days)
```

→ Three vhosts, one still with its own TLS on 444 and a certbot certificate (a second renewal
mechanism to retire), one with Basic auth, one with an office IP allowlist, and a `www-data`
crontab that calls something by URL. Each line becomes a row in the inventory table:

| Site | Owner | Requests/day | Stack and special config | Data |
|---|---|---|---|---|
| api.example.com | Dev team (Ravi) | 31,900 | Node 20 via `ProxyPass` to 127.0.0.1:3001 | Shared MySQL 8 schema `api` |
| checkout.example.com | Sales (Priya) | 9,100 | PHP 8.3, sessions in files, TLS on 444, certbot | MySQL 8 schema `shop` |
| intranet.example.com | HR | 212 | Static, Basic auth, office IP allowlist | None |
| www-data cron job | Nobody known | Every 5 min | `curl https://api.example.com/sync` | — |

**2. Classification.** Decide per item with the "R" vocabulary of migrations:

| Decision | Meaning | Applied to |
|---|---|---|
| Retire | Switch off; nobody needs it | intranet (owner agrees, replaced by the HR tool) |
| Retain | Keep as it is, for now | — |
| Rehost | Same software, new home (container as-is) | The `www-data` cron job, as a scheduled task next to the api once an owner is found |
| Replatform | Small changes to run well on the platform | api (has a Dockerfile; logs to stdout), checkout (PHP-FPM image, sessions to Redis) |
| Refactor | Re-architect | Not in this project; out of scope by decision |
| Repurchase | Replace with a SaaS | — |

**3. Risk register.** Likelihood (L) and impact (I) from 1 to 3; the score is L × I, and anything
scoring 6 or more needs a mitigation before its phase starts:

| ID | Risk | L | I | Score | Mitigation | Owner | Trigger and response |
|---|---|---|---|---|---|---|---|
| R1 | Redirect loop when a site moves behind Traefik | 2 | 3 | 6 | Test every site through Traefik in staging; header-based redirect rule | Sam | Error 47 or `too many redirects` → route back |
| R2 | Checkout sessions lost at the switch | 2 | 3 | 6 | Sessions in Redis shared by old and new; switch at low traffic | Ravi | Logout reports → weight back to Apache |
| R3 | Certificate not issued at cutover | 2 | 3 | 6 | Issue on a temporary hostname first; Let's Encrypt staging for tests | Sam | No cert in `acme.json` → keep the old route |
| R4 | Hidden consumers (cron, partners, hard-coded :444) | 3 | 2 | 6 | 14 days of log analysis per source address; partner list | Priya | Unknown client in logs → contact before removal |
| R5 | Data drift during the checkout DB move | 1 | 3 | 3 | 10-minute read-only window; row counts and checksums | Ravi | Mismatch → abort, stay on old DB |
| R6 | After migration, one host carries every site | 3 | 3 | 9 | Section 4 HA work and off-host backups are **preconditions** for phase 4 | Sam | Phase 4 blocked until done |
| R7 | Rollback impossible after Apache removal | 1 | 3 | 3 | Keep apache2 installed and disabled for 30 days | Sam | — |

R6 is the risk most migration plans miss: success concentrates every site onto the new platform,
so the platform's own SPOFs must be fixed first or the migration itself raises the risk.

**4. Phased cutover.** Order by risk, lowest first, so the team learns on cheap mistakes:

| Phase | Scope | Entry criteria | Exit criteria | Rollback | Time |
|---|---|---|---|---|---|
| 0. Prepare | ADR, inventory, probes per site, backups off-host | ADR accepted (section 10) | Every site probed; restore tested | — | 1 week |
| 1. Façade | Traefik on 80/443, Apache on 81/444 | — | Done; 14 days without related errors | Apache back to 80/443 (module 21 section 10) | Done |
| 2. Retire | intranet | Owner sign-off; zero requests from outside the office for 14 days | DNS record removed, vhost disabled | Re-enable vhost | 1 day |
| 3. Low-risk move | api | Phase 2 done; container passes tests | 7 days, 5xx rate and p95 at or below baseline | Route back to Apache, seconds | 1 week |
| 4. Critical move | checkout via canary 10 % → 50 % → 100 % | R6 mitigated; sessions in Redis | 14 days meeting the SLO | Weight back to Apache | 3 weeks |
| 5. Switch off | Disable Apache, close 81/444 | Apache requests at zero for 14 days | Change request executed (CR-2026-031 in module 33) | `systemctl enable --now apache2` | 1 day |
| 6. Decommission | Remove packages, certbot, firewall rules, docs | 30 days after phase 5 | Nothing references Apache | Reinstall from Ansible | 1 day |

**5. Success metrics.** Agree them before phase 2, so nobody redefines success afterwards:

| Metric | Baseline | Target |
|---|---|---|
| 5xx rate per site | Today's value from Traefik metrics | Not higher than baseline |
| p95 latency per site | Today's value | Not more than 10 % higher |
| Unplanned downtime during the migration | — | 0 minutes |
| Certificate renewal mechanisms | 2 (certbot + Traefik ACME) | 1 |
| Deploy lead time for api and checkout | About 1 day (manual) | Under 30 minutes (pipeline) |
| Apache requests per day | 41,200 | 0 |

**6. Rollback.** Every phase has a rollback, a trigger and a **point of no return**. For a route
move, rollback is editing one Traefik route, effective in seconds. For checkout, the point of no
return is the first order written to the new database: after that, rolling back means copying new
orders back to the old schema. The plan must say this explicitly and set a decision deadline
("rollback by traffic weight is possible until day 3 of phase 4; after that we fix forward").

**7. Communication plan.**

| Audience | What they need | Channel | When |
|---|---|---|---|
| Site owners | Dates, what to test, rollback criteria, their sign-off | MR mention + email | 2 weeks before, the day before, after each phase |
| Support desk | What may change, how to recognise migration issues, whom to call | Chat + knowledge-base note | 1 week before, start and end of each window |
| Customers (checkout) | Maintenance window, if any | Status page and site banner | 72 hours before |
| Management | Status (red, amber, green), risks, decisions needed | Weekly status report (section 12) | Weekly |
| On-call engineers | New topology, runbooks, how to roll back | Handover session | Before phase 3 |

Before each phase, hold a five-minute **go/no-go** check and record the answers in the change
request:

1. Entry criteria of the phase met, with evidence linked.
2. Rollback tested in staging, and the person who will execute it is present.
3. Monitoring for the affected sites green for 24 hours, probes in place.
4. Owners and support informed; no conflicting change in the calendar.
5. A named person has authority to call rollback without a meeting.

**Key terms:** inventory, migration R's, risk register, likelihood and impact, entry and exit
criteria, point of no return, go/no-go, burndown.

**See it on a real system.** Progress is visible from three numbers you can check daily:

```bash
sudo grep -c 'url: "http://192.0.2.10:81"' /etc/dokploy/traefik/dynamic/legacy-apache.yml
sudo ss -ltnp '( sport = :81 or sport = :444 )' | tail -n +2 | wc -l
curl -sG http://mon-01:9090/api/v1/query --data-urlencode \
  'query=sum(increase(traefik_service_requests_total{service="legacy-apache@file"}[1d]))' | jq -r '.data.result[0].value[1]'
```

```
1
2
41207.23
```

→ The legacy service is still referenced, Apache still listens on both ports, and it served
about 41,200 requests in the last day. All three numbers must reach zero by the end of phase 5:
traffic first, then the route, then the listeners.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write this plan for your real platform: inventory from the commands above,
classification, a risk register with at least six risks, the phase table, metrics, rollback with
a point of no return per phase, and the communication table.

**Step 2 — Break it.** Hold a 30-minute pre-mortem with a colleague: "It is three months from
now and the migration failed badly. What happened?" Write down every cause they invent.

**Step 3 — Fix it.** Each invented cause that is not in the risk register becomes a new row with a
mitigation. Then have one site owner review and sign the plan in an MR. The signed plan, plus the
ADR from section 10, is senior-level evidence for your [career ladder](40-career-ladder.md).

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| No inventory | A forgotten site or cron job breaks after switch-off | Log-based inventory before the plan | [Case study](21-case-apache-443-dokploy.md) |
| Big bang under time pressure | All sites move in one night, several break | Phase by risk; one site per window | This topic |
| Success metrics defined afterwards | Endless debate about whether it worked | Agree metrics before phase 2 | This topic |
| Point of no return unknown | Rollback attempted after new writes, data lost | Write it per phase | This topic |
| Platform risk ignored | The migration succeeds, then one host failure takes every site down | Make HA and backups a precondition | Section 4 |
| Silent stakeholders | Support learns about the migration from customers | Communication table with dates | Section 12 |

**Why it matters for troubleshooting.** Most migration incidents are not technical surprises;
they are known risks nobody wrote down, or rollbacks nobody tested. A risk register with triggers
turns "something is wrong after the switch" into a lookup: which risk, which trigger, which
response.

**Next step:** record the decisions behind the plan so they outlive the project.

---

## 10. Decision making

> 📚 **Study path:** 1) Note: this section first, because KodeKloud has no course on ADRs or design docs; then reread "Designing, deciding, leading" in section 1 · 2) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil, for the risk vocabulary that design reviews use ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Read: Google SRE book chapters 3 (*Embracing Risk*) and 9 (*Simplicity*) from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 4) Practice: write ADR-0003 below for your own platform, then a design doc for the HA project of section 4, each reviewed by one person.

**Who starts here:** mid-level engineers write their first ADR about a decision they already
made; seniors write design docs and run design reviews; leads decide build versus buy and own the
consequences in budgets and headcount.

A decision that lives only in a meeting is lost the day the people who were in the room leave.
Written decisions are how a team keeps its memory, how newcomers understand why things are the way
they are, and how you avoid relitigating the same question every six months ("why is Apache on
81 again?").

### Architecture decision records [L3 · Senior]

**Concept.** An **ADR** is a short document (one or two pages) that records one significant
decision: the context, the options, the choice and its consequences. ADRs live in Git next to the
code or configuration they explain (`docs/adr/0003-...md`), are numbered, and are **immutable once
accepted**: when a decision changes, you write a new ADR that supersedes the old one, so the
history stays readable. The lifecycle is Proposed → Accepted → (Deprecated or Superseded).

Write an ADR when a decision is hard to reverse, affects other people, or will make someone ask
"why?" later. This is the full ADR for the decision your platform is built on:

```markdown
# ADR-0003: Traefik via Dokploy replaces Apache as edge proxy

- Status: Accepted
- Date: 2026-06-12 (written down 2026-10-03; decided during the June port-conflict incident)
- Deciders: Sam (DevOps, author), Ravi (development lead), Priya (IT manager, sponsor)
- Consulted: owners of api, checkout and intranet; support desk
- Informed: all developers, the on-call rota
- Related: ADR-0002 "Apache listens on 81/444", CR-2026-031 "Disable system Apache",
  migration plan "Apache to Dokploy", design doc DD-0004 "Platform HA"

## Context

dok-prod-01 (192.0.2.10, public 203.0.113.10) served our sites from Apache 2.4 on ports 80 and
443 for six years: api (Node behind ProxyPass), checkout (PHP 8.3), intranet (static) and docs.
New applications are to be delivered as containers through Dokploy, whose Traefik v3 edge must
own 80 and 443 to route by hostname and to obtain Let's Encrypt certificates automatically.
In June the Dokploy installer stopped with "Error: something is already running on port 80",
because Apache held 80 and 443. We unblocked the install the same day by moving Apache to 81/444
(ADR-0002). This ADR decides which component is
the long-term edge.

Constraints:
- One public IPv4 address; no budget for a second host or address this quarter.
- No URL changes for existing sites; at most 5 minutes of downtime per site per change.
- One operations engineer; the result must be operable by the on-call rota from runbooks.
- Certificates must renew without manual steps.

## Decision drivers

1. Self-service: developers add apps and domains without an ops ticket.
2. One certificate mechanism instead of certbot plus ACME.
3. Reversibility: every step can be undone in under 15 minutes.
4. Operational simplicity for a one-person ops team.
5. A path to retire Apache completely.

## Considered options

A. Apache stays the edge on 80/443 and reverse-proxies to Traefik on 8080/8443.
B. Traefik, managed by Dokploy, becomes the only edge on 80/443. Apache moves behind it on
   81/444 and is routed through Traefik's file provider; sites move into Dokploy one by one.
C. A second public IP address or host dedicated to Dokploy.
D. HAProxy on 80/443 in front of both, routing by SNI with TLS passthrough.

## Decision

Option B. Traefik via Dokploy is the only edge proxy on 80 and 443. Apache remains a backend on
81/444 for legacy sites until each site is migrated or retired, then Apache is disabled
(CR-2026-031) and removed. The comparison of options is attached below this record.

## Consequences

Positive:
- New apps get a domain and certificate from the Dokploy UI in minutes, without a ticket.
- One renewal mechanism (Traefik ACME) once the last certbot certificate is retired.
- Every site move is reversible by changing one route (strangler migration).

Negative:
- dok-prod-01 becomes the single edge for every site. A Traefik or host failure is a full
  outage until DD-0004 (Platform HA) is delivered. Accepted for at most two quarters.
- Apache sees Traefik's address instead of clients; mod_remoteip is required on every vhost.
- Legacy vhosts that force HTTPS themselves loop behind Traefik; each must be checked.
- Dokploy upgrades can change Traefik's configuration; they become normal changes with a
  rollback plan.

Follow-ups:
- Risk R6 (single edge): owner Sam, review date 2027-01-15.
- Runbooks: "Traefik down", "Route a site back to Apache", "Certificate not issued".
- Monitoring: blackbox probe per hostname; alert when a certificate expires within 14 days.

## Validation

We will know this decision worked when, by 2027-01-31: no ops tickets are needed for new
domains, certbot is removed, Apache serves zero requests, and no incident was caused by the
edge change. Revisit this ADR if a second public address becomes available, if Dokploy is
replaced, or if one host can no longer carry the edge traffic.
```

The options comparison attached to the ADR. Scoring the options against the **drivers** keeps the
discussion about what the team said it needs, not about favourite tools:

| Driver | A: Apache edge | B: Traefik edge (chosen) | C: Second IP or host | D: HAProxy SNI |
|---|---|---|---|---|
| Self-service domains and certificates | No: every app needs an Apache vhost and challenge forwarding | Yes | Yes, for new apps | Partly: HAProxy config per new name |
| One certificate mechanism | No | Yes, after migration | No: two edges | No: certbot behind passthrough plus ACME |
| Reversible in under 15 minutes | Yes | Yes, route by route | Yes | Yes |
| Operational simplicity | Medium: two proxies chained | High: one proxy | Medium: two edges to run | Low: three proxies |
| Path to retire Apache | No | Yes | Yes, slowly | Yes |
| Cost this quarter | None | None | New IP or host: not in budget | None |
| Verdict | Rejected: blocks self-service | **Chosen** | Rejected: budget | Rejected: complexity |

Notice what the ADR does **not** hide: the biggest negative consequence (a single edge for every
site) is written in plain words, with an owner and a deadline. An ADR that lists only benefits is
marketing, and reviewers learn to distrust it.

**Key terms:** ADR, status (proposed, accepted, superseded), context, decision drivers, considered
options, consequences, deciders, consulted, informed.

**See it on a real system.** A healthy ADR directory is short, numbered and has statuses:

```bash
ls ~/work/infra/docs/adr/
grep -H -m1 '^- Status:' ~/work/infra/docs/adr/0*.md | sed 's#.*/adr/##'
```

```
0001-record-architecture-decisions.md
0002-apache-listens-on-81-444.md
0003-traefik-via-dokploy-is-the-edge.md
0004-postgresql-streaming-replication.md
README.md
0001-record-architecture-decisions.md:- Status: Accepted
0002-apache-listens-on-81-444.md:- Status: Accepted
0003-traefik-via-dokploy-is-the-edge.md:- Status: Accepted
0004-postgresql-streaming-replication.md:- Status: Proposed
```

→ Four decisions, one still open for review. ADR-0001 is the conventional first record: "we will
record architecture decisions, in this format, here". The README lists them with one-line
summaries so a newcomer can read the platform's history in ten minutes.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Create `docs/adr/` in your infra repository with ADR-0001 (the decision to
use ADRs), ADR-0002 (Apache on 81/444, the tactical fix) and ADR-0003 adapted from the example
above to your real facts.

**Step 2 — Break it.** Ask a colleague who was not involved to read ADR-0003 and answer three
questions without asking you: why not option A, what is the biggest risk we accepted, and when
must we revisit the decision. Every question they cannot answer is a gap.

**Step 3 — Fix it.** Fill the gaps, open an MR, and request review from the deciders. Merging the
MR is the acceptance. Link the ADR from the Traefik configuration file with a comment
(`# Why Traefik is the edge: docs/adr/0003-...`), so the next person who opens the config finds the
reason.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| ADR written to justify, not decide | Only the chosen option is described | Require at least two real alternatives | Trade-off tables, this section |
| Too long | Nobody reads it | Two pages maximum; move detail to a design doc | Next topic |
| Not linked from the system | The same "why?" keeps coming back | Comment in the config, link in the README | This topic |
| Edited after acceptance | History rewritten, trust lost | Supersede with a new ADR instead | This topic |
| Negative consequences missing | Surprises in production, reviewers distrust ADRs | A mandatory "Negative" list | This topic |

**Why it matters for troubleshooting.** Half of a hard incident is archaeology (section 1). An ADR
answers "is this behaviour a bug or a decision?" in one minute, for example why Apache logs show
Traefik's address, or why every site fails together when dok-prod-01 is down.

**Next step:** the longer document that comes before big decisions.

### Design docs and RFCs [L3 · Senior]

**Concept.** A **design doc** describes how a new system or a significant change will work,
before it is built, so that reviewers can find problems while they are still cheap. An **RFC**
(request for comments) is the same idea for practices that affect many people, such as an on-call
policy or an SLO framework, with an explicit comment period. Design docs usually produce one or
more ADRs as their decisions settle.

| Situation | Write |
|---|---|
| Small, reversible change | A clear MR description |
| Production change with risk | A change request (section 11) |
| A choice others will live with | An ADR |
| A new system, a project of more than about two weeks, or work that affects other teams | A design doc, then ADRs |
| A practice for the whole organisation | An RFC with a comment period |

A template that works for infrastructure:

```markdown
# DD-0004: Platform HA for dok-prod   Author: Sam · Reviewers: Ravi, Priya · Status: In review

## 1. Summary
Three sentences: what we will build, why now, what it costs.

## 2. Context and problem
Today's architecture (diagram), incidents and risks that motivate the change (link R6).

## 3. Goals and non-goals
Goals: survive the loss of any one node with < 1 minute of disruption for Tier 1 sites.
Non-goals: multi-site, Kubernetes, changing the CI system.

## 4. Requirements
Availability target and SLOs · RPO/RTO per tier · security and compliance · capacity for
18 months (section 6) · budget ceiling.

## 5. Proposed design
Diagram, components, data flows, placement of state, failure modes table
(component fails → what happens → how we detect it → how we recover).

## 6. Alternatives considered
Each with a paragraph and the weighted trade-off table.

## 7. Risks and mitigations
Risk register rows with owners.

## 8. Operational readiness
Monitoring and alerts, runbooks, on-call training, backups and restore tests, DR plan update.

## 9. Security
Threat model summary, new ports and firewall rules, secrets, access.

## 10. Cost
One-off and monthly, in money and in people time.

## 11. Rollout and rollback
Phases with entry/exit criteria, point of no return, communication.

## 12. Open questions
Numbered, each with an owner.

## 13. Decision log
Date, decision, ADR link.
```

Three habits make reviews effective. Share the document a week ahead and ask for written
comments. Start the review meeting with ten minutes of silent reading, so everyone discusses the
same text. End it with a recorded outcome: approved, approved with changes (listed), or not
approved (with the reason and the next step).

**Key terms:** design doc, RFC, goals and non-goals, failure modes table, operational readiness,
design review, open questions.

**See it on a real system.** The most useful section of any design doc is the failure modes
table; a reviewer can check it against the real system in minutes. For DD-0004:

| Component fails | Effect | Detected by | Recovery |
|---|---|---|---|
| dok-prod-01 | VIP moves; Dokploy UI unavailable; apps keep serving | Blackbox probe, keepalived log, node-down alert | Automatic for traffic; UI restored from backup per runbook |
| Traefik on the active node | Check script fails, VIP moves | keepalived state change alert | Automatic |
| db-01 | Writes fail | Replication and DB-down alerts | Manual promotion of db-02 (runbook, 15 min) |
| Harbor | No new deploys or scaling | Registry probe | Rebuild Harbor; pulls from the replica registry meanwhile |
| Two managers at once | Cluster read-only; apps keep running | Swarm manager alert | Restore quorum; last resort `--force-new-cluster` |

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write DD-0004 for your platform using the template and the section 4
design. Keep it under eight pages.

**Step 2 — Break it.** Run a review with two people and ten minutes of silent reading. Ask each
reviewer for the one failure the document does not handle.

**Step 3 — Fix it.** Add those failures to the failure modes table, record the outcome in the
decision log, and turn each settled choice (for example "keepalived VIP, not an external load
balancer") into its own ADR.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| No non-goals | Scope grows every review | Write non-goals first | This topic |
| Design after building | Review becomes a rubber stamp | Review at 20 % done, not 90 % | This topic |
| Failure modes missing | Surprises in the first incident | Mandatory failure modes table | Section 2 |
| No decision recorded | Same debate in every meeting | Outcome and ADR links at the end | Previous topic |
| Operational readiness skipped | System launched without alerts or runbooks | Readiness section as a launch gate | Section 12 |

**Why it matters for troubleshooting.** The failure modes table is a pre-written triage guide:
when the system misbehaves, the on-call engineer looks up which component failure produces the
symptom they see.

**Next step:** how to compare options honestly.

### Trade-off tables [L3 · Senior]

**Concept.** Every real option has costs. A **weighted decision matrix** makes the comparison
explicit: list must-have requirements first (options that fail one are out), then weight the
remaining criteria by importance, score each option from 1 (poor) to 5 (excellent), and multiply.
For "make the platform survive a node loss":

| Criterion | Weight | A: Three-node Swarm with Dokploy | B: Kubernetes with Argo CD | C: Two independent Dokploy servers behind a VIP | D: Move to AWS ECS |
|---|---|---|---|---|---|
| Time to deliver | 25 | 4 → 100 | 2 → 50 | 4 → 100 | 3 → 75 |
| Operational simplicity | 20 | 4 → 80 | 2 → 40 | 3 → 60 | 4 → 80 |
| Team skills today | 15 | 4 → 60 | 3 → 45 | 5 → 75 | 2 → 30 |
| Three-year cost | 15 | 4 → 60 | 3 → 45 | 4 → 60 | 2 → 30 |
| Availability gained | 15 | 4 → 60 | 5 → 75 | 3 → 45 | 5 → 75 |
| Reversibility | 10 | 4 → 40 | 2 → 20 | 4 → 40 | 3 → 30 |
| **Total (max 500)** | 100 | **400** | 275 | 380 | 320 |

Two more steps separate a senior from someone filling in a spreadsheet:

**Check the must-haves before scoring.** If "data must stay on-prem" were a must-have, D would be
out before any scoring, and showing its score would only confuse the discussion.

**Test the sensitivity.** Change the weights the way a sceptic would. Raise availability to 25 and
lower time to deliver to 15: A scores 400, C 370, D 340, B 305. A still wins, so the decision is
robust. If a small change in weights flips the winner, the options are effectively equal and the
decision should rest on reversibility and team preference, stated openly.

Also classify the decision by how reversible it is. Amazon's terms are useful here:

| Type | Example on your platform | How to decide |
|---|---|---|
| Two-way door (easy to undo) | Traefik middleware settings, alert thresholds, a Dokploy app's replica count | Decide fast, at the lowest level, measure, adjust |
| One-way door (expensive to undo) | Moving to Kubernetes, choosing a database engine, a three-year Savings Plan, deleting Apache's configuration | Design doc, trade-off table, review, ADR |

**Key terms:** weighted decision matrix, must-have (deal-breaker), sensitivity analysis,
reversibility, one-way and two-way doors, cost of delay.

**See it on a real system.** Scores must come from evidence, not opinion. For "operational
simplicity", count what each option adds to the on-call engineer's world:

| Option | New components to operate | New failure modes to learn | New runbooks |
|---|---|---|---|
| A | keepalived, second Traefik | Quorum, split brain, image distribution | 4 |
| B | etcd, control plane, CNI, ingress controller, Argo CD | All of Kubernetes | 10+ |
| C | keepalived, a second Dokploy | Config drift between two Dokploy instances, data sync | 5 |
| D | ECS, ALB, VPN, IAM | AWS networking and IAM | 6 |

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Build the matrix for "Swarm (Dokploy) or Kubernetes for the next two
years" with your own criteria and weights, after listing the must-haves.

**Step 2 — Break it.** Ask a colleague to set the weights independently, without seeing yours.
Compare.

**Step 3 — Fix it.** Where the weights differ, discuss the criterion, not the total. Agree on
weights, rerun, add a sensitivity line, and attach the table to an ADR.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Weights chosen after scoring | The favourite always wins | Fix weights before scoring | This topic |
| Scores without evidence | Endless argument about a 3 versus a 4 | Evidence column per score | This topic |
| No must-haves | Impossible options discussed for hours | Filter before scoring | This topic |
| One-way door decided fast | Expensive reversal later | Classify the door first | This topic |

**Why it matters for troubleshooting.** When a design fails in production, the trade-off table
shows whether the failure was a known, accepted cost or a surprise. Known costs need a better
mitigation; surprises need a better review.

**Next step:** the biggest recurring trade-off: build, run or buy.

### Build vs buy [L4 · Lead/SRE]

**Concept.** For every capability (monitoring, registry, CI, secrets, PaaS, status page) you can
**build** it, **run** an open-source product yourself, or **buy** a service. The real comparison
is total cost of ownership over several years plus the factors money does not capture:

| Question | Points towards build or self-host | Points towards buy |
|---|---|---|
| Is it what makes us different? | Yes | No, it is a commodity |
| Do we have the skills and time to run it for years? | Yes | No |
| Must the data stay on-prem? | Yes | No |
| Is time to value critical? | No | Yes |
| Is there a mature open-source product? | Yes, run it | — |
| How expensive is leaving later? | Low with open formats | Check export options and contract terms |
| Who is paged when it breaks? | Us | The vendor, under an SLA |

An illustrative three-year comparison for monitoring and logging (replace the numbers with real
quotes; the method is the point):

| Cost line | Self-hosted Prometheus, Grafana, Loki | SaaS observability |
|---|---|---|
| Infrastructure per month | 2 VMs and 1 TB storage: 100 | — |
| Subscription per month | — | 15 hosts, metrics and 100 GB logs: 450 |
| People per month | 0.1 FTE: 500 | 0.03 FTE: 150 |
| Set-up (one-off) | 3 weeks: 3,750 | 1 week: 1,250 |
| **Three-year total** | 600 × 36 + 3,750 = **25,350** | 600 × 36 + 1,250 = **22,850** |

The money is nearly a tie, which is common. The decision is then made by the other rows: whether
metrics and logs may leave the network, whether the team wants Prometheus skills (it is on your
PCA path), and what happens to dashboards and alerts if you leave the vendor.

For your platform, a defensible set of answers:

| Capability | Choice | Why |
|---|---|---|
| PaaS | Run Dokploy (open source) | Fits team size; Kubernetes when the triggers in section 8 appear |
| Registry | Run Harbor on-prem, replicate to ECR | On-prem pulls, private CA, scanning; ECR for AWS DR |
| Monitoring | Run Prometheus and Grafana | Data stays inside; skills match the PCA path |
| Status page | Buy | It must not live on the platform it reports on |
| Public DNS | Buy a managed DNS service | API for failover, anycast, no on-prem dependency |
| Off-site backup storage | Buy object storage | Durability you cannot build cheaply |
| Secrets | Run sops with age, or Vault when needs grow | Start simple; see [Security & DevSecOps](37-learn-security-devsecops.md) |

**Key terms:** build, buy, run (self-host), TCO, lock-in, exit cost, core versus context,
time to value.

**See it on a real system.** The hidden cost of "run" is time. Measure it from your issue tracker
before claiming self-hosting is free:

```bash
glab api "projects/ops%2Fplatform/issues?labels=monitoring&state=closed&created_after=2026-04-01T00:00:00Z&per_page=100" \
  | jq '[.[] | .time_stats.total_time_spent] | add / 3600'
```

```
41.5
```

→ 41.5 logged hours in six months on the monitoring stack: about 7 hours a month, or 0.04 FTE.
That number belongs in the "people per month" row, and it only exists if the team logs time
(`/spend` in GitLab) on platform work.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Pick one capability you run today (Harbor, monitoring or GitLab runners)
and fill the three-year TCO table with real numbers.

**Step 2 — Break it.** Write down your exit plan for the "buy" option: how would you get your data
and configuration out in a month? If you cannot answer, that is lock-in, and it belongs in the
comparison.

**Step 3 — Fix it.** Write the recommendation as an ADR with both columns, the non-money factors
and the exit plan.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| "Free" open source with no owner | Outdated, unpatched, nobody on call for it | Name an owner and log the time | This topic |
| Buying a tool to fix a process | New tool, same incidents | Fix the process first; then decide | Section 11 |
| Lock-in without an exit plan | Price rises, no way out | Exit plan in the ADR | This topic |
| Building a commodity | Team maintains a home-made status page or CI | Buy or run something standard | This topic |

**Why it matters for troubleshooting.** Every component you run is a component you debug at 2am.
Build vs buy is, in the end, a decision about which failures your team wants to own.

**Next step:** reliability leadership: SLOs, incident command, postmortems, change and on-call.

---

## 11. Reliability leadership

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements → Incident Management (Preparing for Incidents, Designing Effective Alerts, IMAG roles, [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page), [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page)) → Managing Complexity, Risk and Toil ([Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: [Performance & observability](32-learn-performance-observability.md) section 15 (SLIs, SLOs and error budgets) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7 (SRE practice: incident roles, postmortem template, a full change request) · 3) Read: Google SRE book chapters 4 (*Service Level Objectives*), 11 (*Being On-Call*), 14 (*Managing Incidents*) and 15 (*Postmortem Culture*) from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 4) Practice: the postmortem review, the SLO negotiation role-play and the incident-command tabletop below.

**Who starts here:** mid-level engineers write postmortems and change requests; seniors run those
processes for the team; leads negotiate SLOs with the business, command major incidents and design
on-call so that people stay healthy.

Module 33 teaches the **artefacts** of SRE practice: the postmortem template, the change request,
the incident roles. This section is about **running the practice**: making the meeting work, the
actions happen, the numbers matter to the business and the pager bearable.

### Running blameless postmortems [L2 · Mid]

**Concept.** A **blameless postmortem** studies how a failure became possible, on the assumption
that everyone acted reasonably given what they knew at the time. Blame makes people hide details;
without details nothing is learned and the incident repeats. Blameless does not mean
consequence-free for negligence; it means the default question is "how did the system let this
happen?", not "who did it?".

When to hold one:

| Trigger | Why |
|---|---|
| Any SEV1 or SEV2 | User impact always deserves learning |
| Any data loss, even recovered | The next one may not be recoverable |
| A production change that had to be rolled back | Change safety is a leading indicator |
| A near miss that could have been a SEV1 | Free lessons, no customer paid for them |
| A failed DR drill or game day | Section 5 |
| On request from the on-call engineer | If it felt bad, it is worth 30 minutes |

The process, with times that keep it from fading:

| When | What | Who |
|---|---|---|
| During the incident | Timeline with UTC times, commands, decisions | Scribe |
| Within 2 working days | Draft with the module 33 template: impact, timeline, contributing factors, what went well, where we got lucky | Usually the IC |
| Within 5 working days | 45-minute review meeting | Facilitator plus everyone involved |
| At the review | Action items created in the tracker, each with owner, due date and priority | Facilitator |
| Weekly | Open actions reviewed in the ops meeting | Team lead |
| After 30 days | Follow-up: were the actions done, did they work? | Facilitator |

**Facilitating the review.** The facilitator is ideally not the person most involved. Open with
the purpose ("we are here to learn how our systems and processes made this possible"). Walk the
timeline and, at each decision point, ask questions that reveal context rather than judgement:

1. What did you know at that moment, and where did that information come from?
2. What made that action look like the right one?
3. What would have helped you notice sooner?
4. Where did the tools, dashboards or runbook mislead or slow you?
5. What went well, and is it luck or design?

Avoid counterfactuals ("should have", "failed to", "simply"); they describe a world that did not
exist and hide the real constraints. Language matters:

| Blameful | Blameless |
|---|---|
| "Ravi deleted the database volume" | "A cleanup command removed a named volume while its service was mid-redeploy; nothing prevented a volume prune on production" |
| "Should have checked the certificate" | "Certificate expiry was not monitored; the only signal was a browser warning reported by a customer" |
| "Root cause: human error" | "The runbook step had two readings and both hosts showed the same prompt" |

**Action items** are where postmortems succeed or fail. Each needs an owner, a due date, a
priority and a type (prevent, detect, mitigate, process):

| Weak action | Strong action |
|---|---|
| "Be more careful with cleanup" | "Remove `docker volume prune` from the disk-full runbook and add a protected-label filter to the cleanup timer (Sam, 2026-10-17, P1, prevent)" |
| "Improve monitoring" | "Alert when any certificate in the inventory expires within 21 days (Priya, 2026-10-24, P1, detect)" |
| "Document the process" | "Write and test the 'route a site back to Apache' runbook with a junior executing it (Anil, 2026-10-31, P2, mitigate)" |

**Key terms:** blameless, counterfactual, contributing factor, near miss, facilitator, action item
types (prevent, detect, mitigate, process), follow-up review.

**See it on a real system.** Open postmortem actions, oldest due date first:

```bash
glab api "projects/ops%2Fplatform/issues?labels=postmortem-action&state=opened&per_page=100" \
  | jq -r '.[] | "\(.due_date // "no-date")\t#\(.iid)\t\(.title)"' | sort
```

```
2026-09-12	#142	Alert on Harbor CA expiry 30 days ahead
2026-10-10	#151	Add mod_remoteip to the checkout vhost
2026-10-24	#155	Monthly restore test for the Dokploy database backup
no-date	#137	Improve monitoring
```

→ #142 is three weeks overdue, and it is the action that would have prevented exercise 2 in
section 16. #137 has no date and no definition of done; it should be rewritten as a strong action
or closed. The share of actions closed by their due date is the honest measure of whether your
postmortems change anything.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write a blameless postmortem of your real June incident (Apache holding
80 and 443, the Dokploy installer refusing to run) with the module 33 template. Use your shell history and logs for
the timeline.

**Step 2 — Break it.** Read it back and highlight every sentence that names a person as the cause,
uses "should have", or ends at "human error".

**Step 3 — Fix it.** Rewrite each highlighted sentence as a system condition. Run a 30-minute
review with one colleague using the five questions, and create three to five strong actions in
the tracker with the `postmortem-action` label.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Actions never done | Same incident class every quarter | Weekly review of open actions; escalate overdue P1s | Section 15 |
| Blame language | People stop volunteering details | Facilitator rewrites; the lead models it | This topic |
| Only big outages reviewed | Near misses repeat until one becomes big | Add near misses to the triggers | This topic |
| "Human error" as root cause | Fix is "training", nothing changes | Ask what made the error easy and the impact large | Section 15, contributing factors |
| Postmortem not shared | Other teams repeat the incident | Publish internally; monthly "postmortem of the month" | Section 12 |

**Why it matters for troubleshooting.** A library of honest postmortems is the best troubleshooting
reference a team can own: it records what the symptoms looked like on **your** systems, which
first guesses were wrong, and which evidence settled the question.

**Next step:** most incidents start with a change, so make changes safe without making them slow.

### Change management and CAB-lite [L2 · Mid]

**Concept.** In most incident histories, a large share of outages begin with a change: a deploy,
a configuration edit, an upgrade, a firewall rule. **Change management** exists to make changes
safe and visible, not to slow them down. Heavy processes (a weekly Change Advisory Board that
approves everything) push teams to batch changes, which makes each change bigger and riskier.
A **CAB-lite** process classifies changes so that most flow freely and only risky ones get extra
eyes:

| Type | Definition | Examples on your platform | Approval | Record |
|---|---|---|---|---|
| Standard | Pre-approved, low risk, repeatable, automated | App deploy through the paved-road pipeline; new Traefik route via MR with tests | None beyond the MR | Pipeline and MR |
| Normal | Everything else | Ansible role change on all nodes, Dokploy upgrade, firewall change, disabling Apache | Peer review plus a change request (module 33 has a full example, CR-2026-031) | CR linked to MR |
| Emergency | Needed now to restore service | Rolling back, failing over, a hotfix during an incident | The IC | CR written within 24 hours |

A simple risk score decides how much ceremony a normal change needs. Score each factor from 1 to
3 and add them:

| Factor | 1 | 2 | 3 |
|---|---|---|---|
| Blast radius | One app or host | Several apps | Every site or the whole platform |
| Reversibility | Instant (route, flag, redeploy previous) | Minutes to an hour | Hard or impossible (data migrations, deletions) |
| Novelty | Done before with a runbook | Done before without a runbook | First time |

| Total | What it needs |
|---|---|
| 3–4 | Can become a standard change once automated |
| 5–6 | Peer review, CR with rollback, normal hours |
| 7–9 | CR with rehearsed rollback, senior review, change window, communication (section 12) |

**Progressive rollout** applies to infrastructure as much as to apps. Change one canary host,
watch it, then widen:

```yaml
# site.yml (excerpt): roll a role across the Swarm nodes safely
- hosts: swarm_nodes
  become: true
  serial:
    - 1          # canary: one node first
    - "50%"
    - "100%"
  max_fail_percentage: 0
  pre_tasks:
    - name: Drain the node before changing it
      ansible.builtin.command: docker node update --availability drain {{ ansible_facts['hostname'] }}
      delegate_to: "{{ groups['swarm_managers'][0] }}"
  roles:
    - docker_engine
  post_tasks:
    - name: Put the node back into service
      ansible.builtin.command: docker node update --availability active {{ ansible_facts['hostname'] }}
      delegate_to: "{{ groups['swarm_managers'][0] }}"
```

The node is addressed by its own hostname (`ansible_facts['hostname']`), because that is the
name Swarm knows it by, while the command runs on a manager. For Swarm services, the equivalent is
`--update-parallelism 1 --update-delay 30s --update-failure-action rollback`, which replaces one task at a time and rolls back if new tasks
fail. Always run Ansible with `--check --diff --limit CANARY_HOST` first and paste the diff into
the change request.

**Make changes visible.** "What changed?" is the first question of every incident (module 33,
"Incident: the first fifteen minutes"). Answer it in seconds by annotating dashboards from the
deploy pipeline:

```bash
curl -fsS -X POST https://grafana.example.com/api/annotations \
  -H "Authorization: Bearer $GRAFANA_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"tags\": [\"deploy\", \"shop-web\"], \"text\": \"shop-web $CI_COMMIT_SHORT_SHA by $GITLAB_USER_LOGIN\"}"
```

**Key terms:** standard, normal and emergency change, CAB, change calendar, freeze window, canary
host, progressive rollout, change correlation.

**See it on a real system.** An incident started at 09:20. What changed in the hour before?

```bash
git -C ~/work/infra log --since="2026-10-03 08:00" --until="2026-10-03 09:20" --pretty='%h %ad %an %s' --date=format:%H:%M
zgrep -h -A1 '^Start-Date: 2026-10-03' /var/log/apt/history.log* | grep -E 'Start-Date|Commandline'
docker service inspect shop-web-1a2b3c --format '{{.UpdatedAt}} {{.Spec.TaskTemplate.ContainerSpec.Image}}'
```

```
d41c9e2 09:12 Sam traefik: add rate limit middleware to checkout
7a03b18 08:47 Ravi ansible: bump docker to 28.3.3 on dok-prod-*
Start-Date: 2026-10-03  06:25:11
Commandline: /usr/bin/unattended-upgrade
2026-10-03 09:15:42.118223421 +0000 UTC harbor.example.com/apps/shop-web:3f9c2d1@sha256:9b0e4c1d2a7f...
```

→ Three changes in the hour before the incident: a Traefik middleware at 09:12, a shop deploy at
09:15 and a Docker upgrade at 08:47 (plus the morning's unattended upgrades). The rate limit eight
minutes before the 429 complaints is the first suspect. Without the history, the same answer takes
an hour of guessing.

**Hands-on lab (no VM needed, then the lab VMs)**

**Step 1 — Build it.** Write a one-page change policy for your team: the three types with your own
examples, the risk score, and who approves what.

**Step 2 — Break it.** Classify your last 20 changes with it. Note which "normal" changes had no
rollback plan, and which "standard" ones caused an incident.

**Step 3 — Fix it.** Turn the most frequent safe change into a standard change by automating it,
and add the Grafana annotation call to the deploy component from section 8. On the lab, roll a
harmless role across dok-01..03 with the `serial` play above and watch the canary go first.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| CAB as bottleneck | Changes batched weekly, each one bigger | Classify; automate standard changes | This topic |
| Rubber-stamp approvals | CRs approved unread, incidents unchanged | Reviewer must name the rollback trigger | Section 12, review checklists |
| Changes outside the process | "Quick fix" on the server, nobody knows | Drift detection: nightly `ansible-playbook --check` | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| No change correlation | Every incident starts with an hour of "what changed?" | Deploy annotations, a change log channel | This topic |
| All nodes changed at once | One bad role breaks the whole cluster | `serial` with a canary host | This topic |

**Why it matters for troubleshooting.** The fastest diagnosis is "it broke at 09:15 and the shop
was deployed at 09:15". Visible, small, progressive changes turn many incidents into a one-step
rollback.

**Next step:** agree with the business how reliable each service must be.

### SLO negotiation [L4 · Lead/SRE]

**Concept.** Module 32 teaches the mechanics: SLIs, SLO targets, error budgets, burn rates. The
Lead's job is the **agreement**: a target the business chose knowingly, and an **error budget
policy** that says what happens when the budget is spent. Without the policy an SLO is a number on
a dashboard that changes nothing.

Start every negotiation from what each target costs on **your** platform. A 30-day month has 43,200
minutes:

| SLO | Error budget per 30 days | What it takes on this platform |
|---|---|---|
| 99 % | 7.2 hours | Today's single host, tested backups, business-hours response |
| 99.5 % | 3.6 hours | Monitoring from outside, restore drills, best-effort evening response |
| 99.9 % | 43.2 minutes | The section 4 HA design, canary deploys, 24×7 on-call with 15-minute response |
| 99.95 % | 21.6 minutes | Plus automatic database failover, two edges, strict change windows |
| 99.99 % | 4.3 minutes | Multi-site active/active and automation for every recovery; humans are too slow |

An **SLA** is a contract with penalties and should be looser than the internal SLO (for example
SLA 99.5 %, SLO 99.9 %), so that you act long before you owe anyone money.

A negotiation that works follows the same steps every time:

1. Start from users: which journeys matter (browse, log in, check out), and what "broken" looks like to a customer.
2. Show today's numbers for each journey over the last 90 days, including the incidents behind them.
3. Show the table above: the cost of each target in money and in people.
4. Ask the business for the cost of downtime: revenue per hour, contractual penalties, reputation.
5. Propose targets near today's performance where users are content, not aspirational ones.
6. Negotiate the error budget policy: this, not the number, is the real agreement.
7. Write it down, get the product owner's signature in the MR, review it quarterly.

A policy that a product owner can sign:

```markdown
# Error budget policy: shop   Agreed: Priya (product owner), Sam (ops lead) · Review: quarterly

SLO: 99.9 % of checkout requests succeed (HTTP status below 500 and faster than 2 s),
measured at Traefik over a rolling 30 days. Budget: 43.2 minutes of full outage equivalent.

Budget remaining   What happens
> 50 %             Normal: features ship, planned risky changes allowed.
25–50 %            Risky changes need senior review; top reliability actions get priority.
< 25 %             Only low-risk changes and reliability fixes; daily budget check.
Exhausted          Feature freeze for the shop (security fixes excepted) until the budget is
                   back above 10 % or the actions for the top two causes are done.

Any single incident that consumes more than 20 % of the budget requires a postmortem.
Planned maintenance counts against the budget.
Disagreements go to the IT manager; the decision is recorded in this file.
```

The paging side of the agreement is a burn-rate alert. Module 32 has the full multi-window set,
and the latency half of the SLI from the duration histogram; the fast-burn pair for errors pages
when 2 % of the 30-day budget burns in one hour (a burn rate of 14.4):

```yaml
groups:
  - name: slo-shop
    rules:
      - record: shop:request_error_ratio:rate5m
        expr: |
          sum(rate(traefik_service_requests_total{service=~"shop-web.*",code=~"5.."}[5m]))
          / sum(rate(traefik_service_requests_total{service=~"shop-web.*"}[5m]))
      - record: shop:request_error_ratio:rate1h
        expr: |
          sum(rate(traefik_service_requests_total{service=~"shop-web.*",code=~"5.."}[1h]))
          / sum(rate(traefik_service_requests_total{service=~"shop-web.*"}[1h]))
      - alert: ShopErrorBudgetFastBurn
        expr: shop:request_error_ratio:rate1h > (14.4 * 0.001) and shop:request_error_ratio:rate5m > (14.4 * 0.001)
        labels:
          severity: page
        annotations:
          summary: "shop: 2 % of the 30-day error budget burned in the last hour"
          runbook_url: "https://gitlab.example.com/ops/runbooks/-/blob/main/shop-errors.md"
```

**Key terms:** SLI, SLO, SLA, error budget, error budget policy, burn rate, user journey, feature
freeze.

**See it on a real system.** Where does the shop stand against a 99.9 % SLO this month?

```bash
curl -sG http://mon-01:9090/api/v1/query --data-urlencode \
  'query=1 - sum(increase(traefik_service_requests_total{service=~"shop-web.*",code=~"5.."}[30d])) / sum(increase(traefik_service_requests_total{service=~"shop-web.*"}[30d]))' \
  | jq -r '.data.result[0].value[1]'
```

```
0.99862
```

→ 99.862 % success, so 0.138 % of requests failed against a budget of 0.1 %: 138 % of the budget is
spent. Under the policy above the shop is in feature freeze. That sentence is the point of the
whole exercise: the number triggers an agreed behaviour, without a new argument.

**Hands-on lab (no VM needed, with a colleague)**

**Step 1 — Build it.** Prepare a one-page proposal for the shop: journeys, 90 days of real
numbers, the cost table, a proposed SLO and the error budget policy.

**Step 2 — Break it.** Role-play: your colleague plays a product owner who insists on "100 %
uptime" and "no feature freezes, ever". Keep the conversation on cost and consequences, not on
technology.

**Step 3 — Fix it.** Write down where you ended up, including the concessions (for example 99.9 %
with a freeze only for the checkout journey). Put the agreed policy in Git and have it signed in
the MR.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| SLO set by engineers alone | Breaches change nothing; the business ignores them | Product owner signs the policy | This topic |
| 100 % target | Every incident is a failure; no budget for change | Show the cost table | This topic |
| SLO on what is easy to measure | CPU-based SLO green while checkout fails | SLI at the user boundary (Traefik, synthetic checks) | [Performance & observability](32-learn-performance-observability.md) |
| No policy | Budget exhausted, features keep shipping | Agree the policy first | This topic |
| SLA tighter than the SLO | Penalties before the team even notices | SLA looser than the SLO | This topic |

**Why it matters for troubleshooting.** The error budget tells the on-call engineer how urgent an
issue is: a slow burn at 1× is a ticket for Monday, a 14× burn is a page now. It also tells the
team, after the incident, whether reliability work beats feature work this sprint.

**Next step:** when the budget burns fast, someone must take command.

### Incident command [L4 · Lead/SRE]

**Concept.** Module 33 introduces the roles (incident commander, operations, communications,
scribe) and the first fifteen minutes. Commanding a real SEV1 is a separate skill: the **incident
commander (IC)** does not debug. The IC keeps the picture, sets priorities, makes decisions, assigns
work and protects the people doing it. The most common failure of a strong engineer acting as IC
is disappearing into a terminal while nobody coordinates.

| SEV | Definition on this platform | Examples | Response |
|---|---|---|---|
| SEV1 | Revenue or most users affected, no workaround, or data at risk | All sites down (dok-prod-01 dead); checkout failing; data loss | Page now; IC declared; updates every 30 min; postmortem required |
| SEV2 | Important function degraded, workaround exists | api 5xx at 20 %; Harbor down while a fix must ship | Page; updates hourly; postmortem required |
| SEV3 | Minor or partial impact | Blog slow; one replica down; certificate expires in 7 days | Business hours; ticket |
| SEV4 | No user impact | Backup failed once and the retry succeeded; near miss | Ticket; weekly review |

When in doubt, declare the higher severity and downgrade later; nobody was ever harmed by an IC
who took an incident too seriously for ten minutes.

**The IC checklist.**

1. Declare: "This is a SEV1. I am the incident commander." Open the incident issue and the channel or bridge.
2. Assign roles by name: operations lead, communications lead, scribe. Subject experts join when asked.
3. Establish the facts: what is broken, for whom, since when (UTC), what changed recently.
4. Set the priority: **stop the bleeding first**. Mitigate (roll back, fail over, degrade, shed load) before looking for the root cause.
5. Timebox hypotheses: each line of investigation gets an owner and 15 minutes, then reports back.
6. Decide out loud and record every decision with its time and reason ("10:42 roll back shop-web to 9e1b7a4, owner Ravi").
7. Keep the update rhythm: internal and external updates at the promised interval, even when nothing changed.
8. Protect the responders: one channel for work, another for questions; the IC answers managers so engineers do not have to.
9. Hand over explicitly at shift changes or after about three hours, using the handover format below.
10. Resolve with criteria: the user-facing signals green for an agreed time, then announce, keep evidence, schedule the postmortem.

The first five minutes in the incident channel sound like this:

```
10:31 IC (Sam): Declaring SEV1: all sites returning 502 since ~10:24 UTC. I am IC.
10:31 IC: Ravi = operations lead. Priya = comms. Anil = scribe. Bridge: link in the issue.
10:32 IC: Known so far: blackbox probes red for every hostname, dok-prod-01 answers ping.
         Last changes: Dokploy upgrade 10:20 (Ravi). Hypothesis 1: upgrade replaced Traefik config.
10:32 IC: Ravi, check dokploy-traefik status and logs, 10 minutes, report at 10:42.
10:33 IC: Priya, status page "investigating" now, next update 11:00.
```

Some actions are **two-way doors** any responder may take at once (section 10); others are one-way
doors that only the IC may approve:

| Action | Who decides |
|---|---|
| Roll back a deploy, revert a route, restart a stateless service, fail over the VIP | Any responder; tell the IC |
| Scale up, enable a maintenance page, shed load | Operations lead; tell the IC |
| Restore a database from backup (loses data after the RPO point), declare a disaster, fail over to AWS | IC, with the app owner when possible |
| Anything that deletes data or cannot be undone | IC, explicitly, recorded |

A handover is a short structured message, not a chat scroll:

```
HANDOVER 13:30 UTC  SEV1 #162 "All sites 502"
State: mitigated at 11:05 (Traefik config restored from backup); root cause not confirmed.
Current risk: Dokploy upgrade still half applied; do NOT re-run the upgrade.
Open threads: (1) diff Traefik static config old/new — Ravi; (2) customer refunds list — Priya.
Next update due: 14:00 internal, 14:30 status page.
New IC: Anil, acknowledged 13:31.
```

**Key terms:** incident commander, operations lead, communications lead, scribe, declaring,
mitigation, timeboxing, decision log, handover, resolution criteria.

**See it on a real system.** Make declaring cheap: one command that opens the incident issue from
a template, so nobody hesitates because of paperwork:

```bash
glab issue create --repo ops/platform --title "SEV1: all sites return 502" \
  --label "incident,sev1" --description "$(cat ~/work/ops/templates/incident.md)"
```

```
Creating issue in ops/platform
#162 SEV1: all sites return 502 (less than a minute ago)
 https://gitlab.example.com/ops/platform/-/issues/162
```

→ The issue becomes the single source of truth: the template has sections for roles, timeline,
decisions and links, and the scribe fills it during the incident instead of reconstructing it
afterwards.

**Hands-on lab (tabletop, three people, 60 minutes)**

**Step 1 — Build it.** Prepare three scenario cards with injects every ten minutes. For example:
"10:24 all sites 502" → "10:34 Traefik logs show `no such file` for the dynamic config" → "10:44
the CEO asks in the channel for an ETA" → "10:54 the restore of `/etc/dokploy` from backup is one
day old".

**Step 2 — Break it.** Run the first card with yourself as IC. The facilitator interrupts you with
injects and side questions, exactly as real incidents do.

**Step 3 — Fix it.** Review the scribe's log: were roles assigned in the first five minutes, did
updates go out on time, was every decision recorded, did the IC stay out of the terminal? Swap
roles and run the next card.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| IC debugging | Nobody coordinates; updates stop | Hand the keyboard to someone else | This topic |
| Too many people in the channel | Noise, duplicate work, conflicting changes | Separate work and question channels | This topic |
| No updates | Managers message engineers directly | Fixed update interval, even with no news | Section 12, templates |
| Late declaration | 40 minutes of quiet debugging before anyone is told | Declare on any SEV1 signal; downgrade later | This topic |
| Uncoordinated fixes | Two people change the same thing; the timeline is lost | Every change announced to the IC first | This topic |

**Why it matters for troubleshooting.** Incident command is troubleshooting at the level of the
team: parallel hypotheses with owners and timeboxes, evidence in one place, and decisions made
deliberately. It turns five people debugging into one coordinated investigation.

**Next step:** design the on-call system that feeds incidents to people.

### On-call design [L4 · Lead/SRE]

**Concept.** On-call is a system with a capacity, like any other. Too few people, too many pages
or pages without a clear action, and the system fails: people burn out and quality drops. The
Google SRE book gives useful upper bounds: at most about **25 % of an engineer's time** on call,
at most **two incidents per 12-hour shift** (an incident with its follow-up takes hours), and for a
single-site 24×7 rotation a minimum of about **eight engineers** (six per site for two sites).

A team of four cannot staff a healthy 24×7 rotation on those numbers, and pretending it can is how
teams burn out. Honest options:

| Option | How it works | Fits when |
|---|---|---|
| Business hours plus best effort | Primary on call 08:00–20:00 on working days; nights and weekends only for SEV1, best effort, no guaranteed response | SLOs at 99.5 % or lower; written in the SLO doc |
| Weekly 24×7 with compensation | One week in four on call, a secondary as backup, time off after night pages | 99.9 % needed and the team agrees to the load |
| Follow-the-sun or partner | Another region or a managed service partner covers nights | Global teams or a budget for a partner |
| Fewer pages | Make most alerts tickets; fix the noisy ones | Always, first |

Every page must pass four tests, or it becomes a ticket:

| Test | Question |
|---|---|
| Urgent | Will users be hurt if nobody acts in the next 30 minutes? |
| Actionable | Is there something the on-call engineer can do now? |
| Symptom-based | Does it describe user impact (SLO burn, probe failure) rather than a cause (CPU 90 %)? |
| Documented | Does it link to a runbook with the first steps? |

Route by severity in Alertmanager, so tickets never wake anyone. The top-level `time_intervals`
and `active_time_intervals` need Alertmanager 0.24 or newer, and the `location` (time zone) field
0.25 or newer; check `alertmanager --version`, because older distribution packages (Ubuntu
22.04's, for example) lack them:

```yaml
route:
  receiver: ticket-queue
  group_by: [alertname, service]
  routes:
    - matchers: ['severity="page"']
      receiver: pager
      group_wait: 30s
      repeat_interval: 1h
    - matchers: ['severity="ticket"']
      receiver: ticket-queue
      repeat_interval: 24h
      active_time_intervals: [business-hours]
time_intervals:
  - name: business-hours
    time_intervals:
      - weekdays: ['monday:friday']
        times:
          - start_time: '09:00'
            end_time: '18:00'
        location: 'Asia/Kolkata'
```

New people join the rotation in stages: **shadow** (receives pages, an experienced engineer
responds), **reverse shadow** (responds, with the experienced engineer watching) and then
**primary** with a named secondary. Each stage lasts at least one full rotation.

Measure the rotation every week, and act when a number crosses its line:

| Metric | Healthy | Action when crossed |
|---|---|---|
| Pages per week | Under 10, and at most 2 per 12-hour shift | Page review; convert or fix the top three |
| Share of actionable pages | Above 90 % | Delete or demote the rest |
| After-hours pages | Under 2 per week | Fix the causes, or move the alert to business hours |
| Time to acknowledge (MTTA) | Under 5 minutes for pages | Check routing, phones, escalation |
| Toil share | Under 50 % of the team's time | Automate the biggest toil (section 15) |

**Key terms:** rotation, primary and secondary, escalation policy, page versus ticket, alert
fatigue, MTTA, shadowing, compensation, toil.

**See it on a real system.** Alertmanager counts the notifications it sends per integration.
Compare this week with the healthy line:

```bash
curl -sG http://mon-01:9090/api/v1/query --data-urlencode \
  'query=sum by (integration) (increase(alertmanager_notifications_total[7d]))' \
  | jq -r '.data.result[] | "\(.metric.integration)\t\(.value[1] | tonumber | floor)"'
```

```
webhook	61
email	214
```

→ 61 pager notifications in a week (the pager is behind the webhook integration), six times the
healthy line and before counting repeats. The next step is a page review: export the week from
the pager app, group by alert name, and for each of the top three decide: fix the cause, make it a
ticket, or delete it. Exercise 5 in section 16 works through exactly this situation.

**Hands-on lab (no VM needed, then mon-01)**

**Step 1 — Build it.** Design the rotation for a four-person team: which option from the table,
hours, primary and secondary, escalation, compensation, and how a new joiner moves from shadow to
primary. Write it as a one-page on-call policy.

**Step 2 — Break it.** Take last month's alerts from your monitoring (or the lab's), and apply the
four tests to each alert rule. Count how many rules fail at least one test.

**Step 3 — Fix it.** On mon-01, change the severity of every failing rule to `ticket` or delete
it, add `runbook_url` to every remaining page, and load the routing tree above. Check with
`amtool check-config /etc/prometheus/alertmanager.yml` before reloading.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Too few people | Exhaustion, sick days, resignations | Change the option, not the people | This topic |
| Alert fatigue | Pages acknowledged and ignored; a real one missed | Page review; four tests | [Performance & observability](32-learn-performance-observability.md) |
| Pages without runbooks | Every page needs the expert | `runbook_url` mandatory for `severity="page"` | Section 12, runbooks |
| Juniors thrown in | Panic, slow response, people quit the rotation | Shadow and reverse shadow first | Section 12, mentoring |
| On-call as punishment | Nobody volunteers; knowledge stays with one person | Compensation, fair rotation, visible thanks | [Career ladder](40-career-ladder.md) |

**Why it matters for troubleshooting.** A tired engineer troubleshoots badly. The quality of
on-call design shows up directly in time to resolve, in the number of mistakes made during
incidents, and in whether anyone is still willing to be paged next year.

**Next step:** technical leadership: runbooks, reviews, mentoring, estimating and communication.

---

## 12. Technical leadership

> 📚 **Study path:** 1) Note: this section first, because leadership is practised rather than watched and KodeKloud has no course for it · 2) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7 (Runbooks, On-call hygiene) and [Career ladder](40-career-ladder.md) section 11 (Soft skills) · 3) KodeKloud: *Fundamentals of SRE* — Incident Management → Preparing for Incidents, for runbook habits ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Read: Google SRE book chapter 28, *Accelerating SREs to On-Call and Beyond*, from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 5) Practice: one runbook that a junior follows without your help, and one infrastructure MR reviewed with the checklist below.

**Who starts here:** juniors write runbooks; mid-level engineers review infrastructure changes;
seniors mentor, estimate, say no with alternatives and keep stakeholders informed. None of this
needs a manager title. It is what makes other people effective because of you.

Technical leadership is measured by what happens when you are **not** there: the runbook that
someone else follows at 2am, the review comment that prevents an outage you never see, the junior
who handles an incident alone for the first time.

### Runbooks others can follow [L1 · Junior]

**Concept.** A **runbook** is a step-by-step procedure for one situation, usually one alert. Its
quality test is the **2am test**: could a colleague who has never seen this problem follow it
half-awake, without calling you? That requires every step to say what to run, what you should see,
and what to do if you see something else.

| Check | Why |
|---|---|
| Linked from the alert (`runbook_url`) | Found in seconds, not searched for |
| Impact and severity at the top | The reader knows whether to declare an incident |
| Every step: command, expected output, branch if different | No guessing |
| Safety notes before dangerous steps | Prevents a second incident |
| Escalation with names or a rota link | Nobody stays stuck alone |
| "Last tested" date and tester | Trust, and a reminder to retest |
| Under two screens, links for depth | Readable at 2am |

An example that passes the test. Commands are indented because the whole runbook is shown as one
block:

```markdown
# Runbook: all sites return 502 or 504 on dok-prod-01

Alert: AllSitesDown (probe_success == 0 for every hostname for 2 min)
Impact: SEV1, every site on the platform. Declare an incident before step 3.
Owner: ops team · Last tested: 2026-09-20 by Anil (game day) · Next review: 2027-03
Access: SSH to dok-prod-01 with sudo; Dokploy admin login

## Safety
- Do not run docker system prune or delete volumes during this runbook.
- Do not restart Docker before step 4: it restarts every container on the host.

## 1. Is the host alive? (1 min)
    ping -c3 192.0.2.10
    ssh dok-prod-01 uptime
Expected: replies and an uptime. No reply: follow the runbook "dok-prod-01 down".

## 2. Is Traefik running? (1 min)
    docker ps -a --filter name=dokploy-traefik --format '{{.Names}} {{.Status}}'
Expected: "dokploy-traefik Up ...". If it says Exited: go to step 5.

## 3. What does Traefik say? (3 min)
    docker logs --since 15m dokploy-traefik 2>&1 | grep -i error | tail -20
Expected: no errors. Common findings:
- "yaml:" or "field not found": a broken file in /etc/dokploy/traefik/dynamic, go to step 6.
- "connection refused" for every service: the apps are down, go to step 4.

## 4. Are the apps running? (2 min)
    docker service ls --format '{{.Name}} {{.Replicas}}'
Expected: every service n/n. Many at 0/1: check docker node ls and df -h /.

## 5. Start Traefik (1 min)
    docker start dokploy-traefik
Verify: curl -sI https://shop.example.com | head -1 shows "HTTP/2 200" within 30 s.

## 6. Remove the last dynamic config change (3 min)
    sudo ls -lt /etc/dokploy/traefik/dynamic/ | head -5
    sudo mkdir -p /root/traefik-quarantine
    sudo mv /etc/dokploy/traefik/dynamic/NEWEST_FILE.yml /root/traefik-quarantine/
Traefik reloads by itself within seconds. Verify as in step 5. Never move acme.json.

## Escalation
Not fixed after 20 minutes, or data at risk: call the secondary (rota link) and the ops lead.

## After
Add the timeline to the incident issue. If a step was wrong or missing, fix this runbook today.
```

**Key terms:** runbook, playbook, 2am test, expected output, branch, escalation, last tested.

**See it on a real system.** Audit the runbook directory and the alert rules together:

```bash
grep -L 'Last tested' ~/work/ops/runbooks/*.md
grep -ho 'Last tested: [0-9-]*' ~/work/ops/runbooks/*.md | sort | head -3
grep -c 'runbook_url' /etc/prometheus/rules/*.yml
grep -c 'alert:' /etc/prometheus/rules/*.yml
```

```
/home/ops/work/ops/runbooks/harbor-down.md
/home/ops/work/ops/runbooks/postgres-replica-lag.md
Last tested: 2025-11-02
Last tested: 2026-03-14
Last tested: 2026-09-20
/etc/prometheus/rules/capacity.yml:1
/etc/prometheus/rules/node.yml:3
/etc/prometheus/rules/slo.yml:4
/etc/prometheus/rules/capacity.yml:3
/etc/prometheus/rules/node.yml:9
/etc/prometheus/rules/slo.yml:4
```

→ Two runbooks were never tested, one was last tested eleven months ago, and only 8 of 16 alert
rules point to a runbook. That is a concrete, measurable backlog for a junior to own.

**Hands-on lab (lab VMs, with a junior or a friend)**

**Step 1 — Build it.** Write the runbook above for the lab (dok-01 instead of dok-prod-01).

**Step 2 — Break it.** Without saying what you did, put a broken YAML file into
`/etc/dokploy/traefik/dynamic/` on dok-01, then ask your junior to fix the outage using only the
runbook. Sit behind them, silent, and write down every question they ask and every place they
hesitate.

**Step 3 — Fix it.** Each question is a defect in the runbook: a missing expected output, an
ambiguous step, a missing branch. Fix them, have someone else run it, and record the date in
"Last tested".

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Stale runbook | Commands for old versions fail at 2am | "Last tested" older than 6 months → retest | This topic |
| "Check the logs" steps | Reader does not know which logs or what to look for | Command plus expected output in every step | This topic |
| No safety notes | Runbook step causes a second incident | Safety section before the steps | Section 11, change management |
| Runbook in one head | Every page goes to the same person | Write it after every incident that had no runbook | Section 11, postmortems |

**Why it matters for troubleshooting.** A runbook is troubleshooting knowledge in executable form.
Every incident without one costs an expert's time; every incident with a good one is a chance for
someone new to learn.

**Next step:** prevent incidents before they ship, in review.

### Infra review checklists [L2 · Mid]

**Concept.** Reviewing an infrastructure change is different from reviewing application code:
the blast radius is bigger, tests are thinner and many changes are hard to undo. A checklist keeps
reviews consistent and stops the most expensive mistakes:

| Area | Question | Red flag |
|---|---|---|
| Scope | What does it touch: hosts, apps, users? | "All hosts" without `serial` or a canary |
| Rollback | How do we undo it, and how long does that take? | No rollback, or "restore from backup" |
| Evidence | Where is the `--check --diff`, `terraform plan` or staging result? | "Works on my machine" |
| Idempotency | Can it run twice safely? | `shell:` or `command:` without `creates`/`changed_when` |
| Secrets | Any secret in the diff or in the logs? | Tokens in YAML, `set -x` around credentials |
| Network | New ports, firewall rules, exposure? | `0.0.0.0` binds, ports opened "temporarily" |
| TLS | Certificates, CAs, expiry, trust stores affected? | Self-signed or CA changes without a rollout plan |
| Observability | Alerts, dashboards and runbooks updated? | New service with no probe |
| Versions | Pinned images, packages, modules? | `:latest`, unpinned roles |
| Size | Can it be reviewed in 15 minutes? | Five unrelated changes in one MR |

Write comments that say what kind of comment they are, so the author knows what must change:
**blocking:** (must change before merge), **question:**, **suggestion:**, **nit:** (style, optional).
Explain the risk, not only the rule: "blocking: this runs `dist-upgrade` and reboots every
production host in parallel, which would take all three Swarm managers down at once and lose
quorum. Please add `serial: 1` and a drain step."

For Terraform, read the plan for destruction before anything else:

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -r '.resource_changes[] | select(.change.actions | contains(["delete"])) | "\(.change.actions | join(",")) \(.address)"'
```

```
delete,create aws_db_instance.shop
delete aws_security_group_rule.office_ssh
```

→ The first line is a **replacement** of the production database (destroy, then create), usually
caused by changing an attribute that forces a new resource. One line like that is a reason to
stop the review and talk.

**Key terms:** blast radius, rollback plan, evidence, idempotency, conventional comment labels,
replacement in a Terraform plan.

**See it on a real system.** Practise on a realistic MR. This diff contains five problems:

```diff
--- a/ansible/roles/platform/tasks/main.yml
+++ b/ansible/roles/platform/tasks/main.yml
@@ -12,0 +13,8 @@
+- name: Upgrade all packages
+  ansible.builtin.shell: apt-get update && apt-get -y dist-upgrade && reboot
+
+- name: Open the Dokploy UI for the new contractor
+  community.general.ufw:
+    rule: allow
+    port: "3000"
+    proto: tcp
--- a/ansible/group_vars/prod.yml
+++ b/ansible/group_vars/prod.yml
@@ -4,1 +4,2 @@
 harbor_url: harbor.example.com
+harbor_robot_token: "EXAMPLE-robot-secret-0123456789abcdef"
--- a/compose/monitoring/compose.yaml
+++ b/compose/monitoring/compose.yaml
@@ -8,2 +8,2 @@
   grafana:
-    image: grafana/grafana:11.2.2
+    image: grafana/grafana:latest
```

The answer key, with the comment a senior would write:

| # | Problem | Comment |
|---|---|---|
| 1 | `dist-upgrade` and `reboot` on every production host at once, through `shell` | blocking: no `serial`, no drain, not idempotent, no check mode. Use `ansible.builtin.apt` and `ansible.builtin.reboot` in a play with `serial: 1` and a drain step |
| 2 | Port 3000 opened with UFW | blocking: it is meant to expose the Dokploy admin UI, and it reveals a bigger problem: ports published by Docker bypass UFW, so 3000 may already be reachable from anywhere. Scan it from outside, filter it in the `DOCKER-USER` chain, and give the contractor access through `dokploy.example.com` with an IP allowlist ([Security & DevSecOps](37-learn-security-devsecops.md), Docker bypasses UFW) |
| 3 | Robot token committed in plain text | blocking: move it to Ansible Vault or a CI variable, and **rotate the token now**, because it is in Git history whatever happens to this MR |
| 4 | `grafana:latest` | blocking: unpinned image, the next restart may bring a major version; pin a version or a digest |
| 5 | Three unrelated changes in one MR | suggestion: split them, so each can be reviewed, tested and rolled back on its own |

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Turn the checklist into a GitLab MR description template
(`.gitlab/merge_request_templates/infra.md`) with the questions as headings the author must fill.

**Step 2 — Break it.** Review the last five merged infrastructure MRs of your team against the
checklist, as if they were still open. Count the red flags that went through.

**Step 3 — Fix it.** Share the count (not names) in the next team meeting, propose the template,
and agree on two rules, for example "every infra MR shows its check or plan output" and "every
blocking comment explains the risk".

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| "LGTM" reviews | Incidents traced to reviewed MRs | Reviewer names the rollback trigger | This topic |
| Syntax-only review | Valid YAML that takes production down | Review the blast radius first | Section 2 |
| Giant MRs | Nobody really reads them | Ask to split; review time limit | This topic |
| Review as gatekeeping | Authors avoid reviewers, changes go around the process | Explain risks; approve quickly when safe | Section 11, change management |

**Why it matters for troubleshooting.** Every red flag caught in review is an incident that never
needs troubleshooting. And when something does break, a reviewed MR with plan output is the best
evidence of what changed and why.

**Next step:** raise the people who will write and review these changes next.

### Mentoring juniors [L3 · Senior]

**Concept.** Mentoring is deliberately growing someone else's ability, and it is how a senior
removes the biggest SPOF on most small platforms: themselves. The aim is not to make juniors
depend on you for answers, but to make them able to find answers the way you do.

| Mentee stage | What to delegate | How you support | Ready for more when |
|---|---|---|---|
| Fresher (L0) | Well-defined tasks with a runbook; scribe during incidents | Daily pairing; explain the why behind each step; review everything | Asks precise questions and writes things down |
| Junior (L1) | One host or service end to end; writing runbooks; on-call shadow | Weekly 1:1; they drive, you navigate; review their runbooks | Others use their runbooks without asking them |
| Mid-level (L2) | Operations lead in incidents; infra MRs; postmortem author | Socratic questions; light review of designs | Their postmortems change how the team works |

Techniques that work in operations:

**I do, we do, you do.** First they watch you (narrating your reasoning, not just your commands),
then you do it together, then they do it while you watch silently.

**Driver and navigator.** In pairing and in real incidents, the junior types and you suggest
direction. It is slower the first time and much faster the tenth.

**Socratic questions.** During an incident, ask instead of telling: "What would you check next,
and what result would rule that layer out?" The question teaches the method; the answer only
teaches the fix.

**Safe failure.** Let them break and fix things in the lab (every lab in this handbook has a
"Break it" step for this reason), and let them own a real postmortem with you as a reviewer.

**Feedback with SBI.** Situation, behaviour, impact: "In yesterday's incident (situation) you
posted the timeline every 15 minutes without being asked (behaviour); the IC never had to chase
anyone and the postmortem took half the usual time (impact)." Use the same structure for
corrective feedback, in private, soon after the event.

A 1:1 every week or two keeps the plan honest:

```
1:1 Anil · 2026-10-07 · 30 min
1. Wins since last time (theirs first)
2. What is blocking you or confusing you?
3. Learning plan: progress on the current module and KodeKloud course, next lab
4. Feedback both ways (one thing each)
5. Next two weeks: one stretch task, one thing to stop doing
```

A first 90 days for a fresher, built from this handbook:

| Days | Learn | Do | Evidence |
|---|---|---|---|
| 1–30 | [Learn: Linux](27-learn-linux.md), [Learn: Networking](28-learn-networking.md), [Cheatsheet](19-cheatsheet.md); KodeKloud *Learning Linux Basics Course & Labs* ([course](https://kodekloud.com/courses/the-linux-basics-course)) | Scribe in two incidents; one lab a day | Notes repository with five-line lab notes |
| 31–60 | [Learn: Docker](30-learn-docker.md), [Site down](25-playbook-site-down.md), [Who owns this port?](22-playbook-ports-inventory.md) | Write one runbook; fix three alerts without `runbook_url` | A runbook a colleague followed |
| 61–90 | [Learn: Web servers & proxies](29-learn-webservers-proxies.md), this module's section 2 | On-call shadow for one rotation; author a postmortem with review | A published postmortem and a shadow rotation completed |

**Key terms:** mentoring, delegation, pairing, driver and navigator, Socratic questioning, SBI
feedback, 1:1, shadowing, bus factor.

**See it on a real system.** Is knowledge spreading? Count who closed the last ten incidents:

```bash
glab api "projects/ops%2Fplatform/issues?labels=incident&state=closed&order_by=updated_at&per_page=10" \
  | jq -r '.[].closed_by.username' | sort | uniq -c | sort -rn
```

```
      8 ops
      2 ravi
```

→ Eight of the last ten incidents ended with you. That is a bus factor of one, the same SPOF as in
section 1, and the mentoring goal writes itself: within six months, at least three people close
incidents, with you as reviewer rather than resolver.

**Hands-on lab (with a junior colleague or a friend)**

**Step 1 — Build it.** Write a 90-day plan for one person using the table above, adjusted to their
current stage, and agree it with them in a first 1:1.

**Step 2 — Break it.** Run three pairing sessions where you are only allowed to ask questions,
never to type or give answers. Notice how often you want to take the keyboard.

**Step 3 — Fix it.** After a month, ask for feedback on your mentoring with the same SBI structure,
and adjust: more autonomy where they are ready, more pairing where they are stuck.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Doing it for them | Fast today, dependent forever | Questions instead of answers | This topic |
| Information dumping | Long explanations, nothing retained | One concept, then a lab | This topic |
| No feedback | Mentee guesses what good looks like | SBI after each notable event | This topic |
| Only praise | Growth stalls on known weaknesses | One improvement point per 1:1 | This topic |
| Mentoring without time | 1:1s cancelled every week | Put it in the plan and the estimate | Next topic |

**Why it matters for troubleshooting.** A team where three people can troubleshoot the platform
resolves incidents faster, sleeps better and loses less when someone leaves. Your best incident
response improvement may be a junior who no longer needs to call you.

**Next step:** plan work honestly, and protect the plan.

### Estimating and saying no [L3 · Senior]

**Concept.** An estimate is a statement about uncertainty, not a promise. Seniors estimate in
ranges, include the work nobody sees, convert effort into calendar time, and re-estimate at
milestones. A useful method is the **three-point estimate**: for each task, an optimistic (O), a
most likely (M) and a pessimistic (P) value, combined as E = (O + 4M + P) ÷ 6 with a spread of
(P − O) ÷ 6.

The section 4 HA project, broken into tasks of two days or less where possible (days of effort):

| Task | O | M | P | E |
|---|---|---|---|---|
| Add dok-prod-02 and dok-prod-03, join Swarm, firewall rules | 1 | 2 | 4 | 2.2 |
| Harbor as Dokploy registry; CA trust on new nodes | 1 | 2 | 5 | 2.3 |
| Move app state to the database VMs and object storage | 3 | 5 | 10 | 5.5 |
| PostgreSQL replica, pgBackRest, first restore test | 2 | 4 | 8 | 4.3 |
| keepalived edge, second Traefik, DNS-01 certificates | 2 | 3 | 6 | 3.3 |
| Monitoring, alerts, runbooks, one game day | 2 | 3 | 5 | 3.2 |
| Reviews, change requests, communication, waiting for windows | 1 | 2 | 4 | 2.2 |
| **Total** | | | | **23.0** |

The spreads combine as the square root of the sum of squares: about ±2 days, so 85 % confidence
is roughly 25 days of effort. Then the step most estimates forget: you will not spend every day on
this project. With on-call, reviews and interruptions, a **focus factor** of 0.6 is realistic, so
the expected 23 days of effort take about 38 working days of calendar time, and the 85 % figure
about 42. The honest answer to "when will it be done?" is "about eight weeks; I commit to nine and
will report progress every Friday".

Hidden work that belongs in every infrastructure estimate: reviews and their rework, change
requests and waiting for windows, documentation and runbooks, testing rollback, communication,
monitoring, and the first week of support after launch.

**Saying no with alternatives.** Seniors rarely say a bare "no". They say one of three things:
"yes, if…" (conditions), "not now, because…, the earliest is…" (priority), or "not this way; here
is a way that gets you what you need" (alternative):

| Request | Weak answer | Senior answer |
|---|---|---|
| "Open port 8443 on dok-prod-01 for client X's app" | "No, policy." Or doing it silently | "Not this way: their app can run on 443 behind Traefik with its own hostname and certificate today; if they need their own TLS, Traefik can pass it through (exercise 4). What does the client need exactly?" |
| "Give the developers SSH to production" | "No." | "Not this way: logs are in Grafana, deploys go through the pipeline, and for debugging we have time-limited break-glass access with an audit trail. Which of these is missing for you?" |
| "Skip the restore test, the migration must happen Friday" | "OK." | "Yes, if we accept losing up to 24 hours of orders if it fails. I recommend Tuesday with the test. It is your call; please confirm in the change request." |
| "Can you also migrate the mail server this sprint?" | Accept and miss both deadlines | "Not now: it would delay the HA project by three weeks. The earliest is November. Which one matters more?" |

**Key terms:** three-point estimate, effort versus duration, focus factor, confidence level,
spike (time-boxed research), scope, trade-off, alternatives.

**See it on a real system.** Learn your own estimation bias from data. GitLab stores estimates
(`/estimate`) and time spent (`/spend`) per issue:

```bash
glab api "projects/ops%2Fplatform/issues?labels=project-ha&state=closed&per_page=100" \
  | jq -r '.[] | select(.time_stats.time_estimate > 0) | "\(.time_stats.total_time_spent / .time_stats.time_estimate * 100 | floor)%\t\(.title)"'
```

```
150%	Add dok-prod-02 and dok-prod-03 to the Swarm
93%	keepalived edge and second Traefik
210%	Move app state to the database VMs
```

→ The state migration took twice the estimate, which is typical for data work, and the ratio
across your closed tasks is your personal correction factor for the next plan.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Estimate a real project of yours with the three-point table, the spread,
the focus factor and a calendar date. Record the estimates in the issues.

**Step 2 — Break it.** Ask a colleague to list everything your task list forgot. Add it.

**Step 3 — Fix it.** At the end of the project, compare estimate and actuals per task with the
command above, and write down your correction factor and the kinds of tasks you underestimate.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Single-number estimates | Every project "late" | Ranges and confidence | This topic |
| Effort reported as calendar time | Deadlines missed by the focus factor | Convert with a measured focus factor | This topic |
| Hidden work missing | Reviews, change windows and docs eat the buffer | Standard hidden-work checklist | This topic |
| Yes to everything | Many projects half done | "Not now, because…" with a date | This topic |
| No without an alternative | Requester goes around you | Offer the path that meets the need | This topic |

**Why it matters for troubleshooting.** Unrealistic plans produce rushed changes, skipped tests
and tired people, the raw material of incidents. Honest estimates are a reliability practice.

**Next step:** keep everyone informed, especially when things go wrong.

### Stakeholder communication [L3 · Senior]

**Concept.** During outages and migrations, people who cannot see your terminal need to make
decisions: support must answer customers, managers must decide whether to escalate. Good
communication follows a few rules:

| Rule | Meaning |
|---|---|
| Bottom line up front (BLUF) | First sentence: what is affected and what users should do |
| Write for the audience | Customers need impact and timing; managers need risk and decisions; engineers need detail |
| Known and unknown | Say what you know, what you do not know yet, and what you are doing |
| Next update time | Always promise the next update, and keep the promise |
| No jargon, no blame | "Checkout is unavailable", not "the PHP-FPM pool is saturated" |
| One source of truth | A status page or incident issue that every message links to |

Templates save time when you have none. Customer-facing outage messages:

```
INVESTIGATING · 10:35 UTC
Checkout is currently unavailable; browsing the shop still works. We are investigating
and will post the next update by 11:00 UTC. Orders placed before 10:24 UTC are safe.

UPDATE · 11:00 UTC
We have found the cause in our web routing layer and are applying a fix. Checkout is
still unavailable. Next update by 11:30 UTC or as soon as service is restored.

RESOLVED · 11:12 UTC
Checkout has been working normally since 11:05 UTC. Between 10:24 and 11:05 UTC orders
could not be placed. No order or payment data was lost. We will publish a summary of
what happened and what we are changing within five working days.
```

Planned work and migrations:

```
PLANNED MAINTENANCE · checkout.example.com
When: Tuesday 13 October, 06:00–06:30 UTC (low-traffic window)
Impact: checkout may be unavailable for up to 5 minutes during this window. Browsing,
accounts and existing orders are not affected.
Why: we are moving checkout to our new hosting platform for faster, safer updates.
If something goes wrong: we return to the current setup within 15 minutes.
Questions: support@example.com
```

```
TO: checkout owners, support · SUBJECT: checkout migration, phase 4 starts 13 Oct
What changes: checkout moves from Apache to Dokploy, 10 % of traffic first, 100 % by 28 Oct.
What you need to do: run the test plan (link) on staging by 9 Oct and sign off in the MR.
How you will know it works: error rate and response time on the dashboard (link).
Rollback: one route change, under 1 minute; criteria in the plan (link).
Contact during the windows: #ops-migration, on-call phone (rota link).
```

For managers after a major incident, an executive summary of five lines:

```
SEV1 2026-10-03 · Checkout unavailable for 41 minutes (10:24–11:05 UTC)
Impact: about 120 orders delayed or lost (estimated 6,000 in revenue), no data loss.
Cause: a platform upgrade replaced our web routing configuration; our checks did not catch it.
Fixed: configuration restored from backup at 11:05; upgrade procedure now tested on staging first.
Next: three actions owned by the ops team, due by 31 October (postmortem link). No decision needed.
```

And the weekly status report for a project, with a red/amber/green status that means something:

```
Platform HA · week 6 of 9 · Status: AMBER
Done: dok-prod-02/03 joined, Harbor trusted on all nodes, replica running.
Next: keepalived edge (Tue), game day (Thu).
Risk: state migration took 2× estimate; one week of buffer left.
Decision needed: approve the Thursday 10:00 game day window (CR-2026-058) by Tuesday.
```

**Key terms:** BLUF, stakeholder, status page, update cadence, executive summary, RAG status,
single source of truth.

**See it on a real system.** The status page must survive the outage it reports. Check that it
does not depend on your platform:

```bash
dig +noall +answer status.example.com
dig +short shop.example.com status.example.com
```

```
status.example.com.	300	IN	CNAME	status-provider.example.net.
203.0.113.10
status-provider.example.net.
198.51.100.80
```

→ The status page is hosted by a provider outside your network, on a different address from the
shop. If it resolved to 203.0.113.10, a dok-prod-01 outage would take the status page down with
everything else.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write the three customer messages, the executive summary and one weekly
status report for the scenario "checkout down for 40 minutes after a Dokploy upgrade".

**Step 2 — Break it.** Give them to someone non-technical. Ask them to tell you, in their words,
what happened, whether their data is safe and when the next update comes.

**Step 3 — Fix it.** Rewrite every sentence they misunderstood. Save the final versions as
templates in your ops repository, next to the runbooks.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Silence during an outage | Customers and managers flood engineers with questions | Comms role with a fixed update interval | Section 11, incident command |
| Jargon | Support cannot explain the outage to customers | Non-technical reader test | This topic |
| Promising times you cannot keep | Trust lost on the second missed estimate | Promise the next update, not the fix | This topic |
| Status page on the platform | Status page down with everything else | Host it elsewhere | This topic |
| Green status until the deadline | "Everything was fine" until the project is late | Amber early, with the decision needed | This topic |

**Why it matters for troubleshooting.** Good communication buys the engineers quiet time to work.
Every unanswered manager becomes an interruption in the incident channel.

**Next step:** security and compliance, owned at senior level.

---

## 13. Security and compliance ownership

> 📚 **Study path:** 1) Note: [Security & DevSecOps](37-learn-security-devsecops.md) for all the technical controls (hardening, network security, TLS and PKI, secrets, scanning); this section only adds what changes when you **own** the outcome · 2) KodeKloud: *DevOps Pre-Requisite Course* — Security → [SSL & TLS Basics](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page) as a PKI refresher ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · 3) KodeKloud: *Certified Kubernetes Security Specialist (CKS)*, after the CKA ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Docs: the [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) and [OWASP](https://owasp.org/) · 5) Practice: the certificate inventory lab and the evidence map below.

**Who starts here:** juniors apply hardening steps; mid-level engineers fix findings; seniors own
the security posture of the platform (threat model, patch and access processes, certificate and
secret lifecycle); leads turn good operations into the evidence that audits and customers ask
for.

Security at senior level is less about knowing more attacks and more about **ownership**: every
control has an owner, a frequency and evidence that it actually ran. Most breaches of small
platforms do not use clever exploits; they use an expired process, such as a contractor account
nobody removed, a token in Git, or an unpatched service everybody assumed someone else patched.

### Owning security outcomes [L3 · Senior]

**Concept.** Start with a lightweight **threat model** of the platform's most exposed part, the
edge. STRIDE gives six questions; answer each for Traefik and Dokploy:

| STRIDE | Question | On your edge | Control |
|---|---|---|---|
| Spoofing | Can someone pretend to be someone else? | Forged `X-Forwarded-For` defeating IP allowlists; brute force on the Dokploy login | Trusted-proxy settings, allowlist on the Dokploy router, strong admin authentication |
| Tampering | Can someone change what they should not? | Anyone who can write `/etc/dokploy/traefik/dynamic` can re-route any site | Root-only permissions, config from Git, change alerts |
| Repudiation | Can someone act without a trace? | UI changes in Dokploy, manual edits on hosts | Config in Git, auditd on config paths, central logs |
| Information disclosure | Can data leak? | Traefik dashboard or port 3000 reachable; `acme.json` holds private keys | Dashboard off or protected, firewall in `DOCKER-USER`, file mode 600 |
| Denial of service | Can someone take it down? | No rate limits; one edge node | Rate limits (section 3), the HA edge (section 4) |
| Elevation of privilege | Can someone become root? | Membership of the `docker` group, and containers that mount `docker.sock` (Traefik and Dokploy do) are root-equivalent | Minimal `docker` group, read-only socket where possible, keep those images patched |

Then own the recurring processes. Each needs an owner, a frequency and evidence:

| Process | Target | Owner | Evidence | Frequency |
|---|---|---|---|---|
| Patching | Critical CVEs fixed within 7 days, high within 30 | Ops | unattended-upgrades logs; Harbor scan trend | Weekly review |
| Vulnerability triage | Scanner findings triaged by severity **and** exploitability | Ops | Triage notes on Harbor findings | Weekly |
| Access review | Who has sudo, `docker`, Dokploy admin, Harbor admin, GitLab maintainer | Ops lead | Review issue with the lists and removals | Quarterly |
| Offboarding | Access removed on the last day | IT + ops | Checklist issue per leaver | Per event |
| Certificate and secret inventory | Every CA, certificate and token with expiry and owner | Ops | Inventory file plus expiry alerts | Continuous |
| Backup immutability | Ransomware cannot delete backups | Ops | Object Lock configuration (section 5) | Monthly check |
| Security incident readiness | Runbooks for leaked credentials and a compromised host | Lead | Tabletop records | Twice a year |

**Key terms:** threat model, STRIDE, attack surface, root-equivalent, patch SLA, exploitability,
access review, certificate inventory, security debt.

**See it on a real system.** Three ownership checks on dok-prod-01:

```bash
getent group sudo docker
sudo jq -r '.letsencrypt.Certificates[] | "\(.domain.main) \(.certificate)"' /etc/dokploy/traefik/dynamic/acme.json \
  | while read -r name cert; do printf '%-28s ' "$name"; echo "$cert" | base64 -d | openssl x509 -noout -enddate; done
openssl x509 -noout -subject -enddate -in /usr/local/share/ca-certificates/harbor-ca.crt
```

```
sudo:x:27:ops,ravi
docker:x:998:ops,ravi,anil,deploy-old
app.example.com              notAfter=Dec 18 07:12:44 2026 GMT
shop.example.com             notAfter=Dec  2 10:31:09 2026 GMT
dokploy.example.com          notAfter=Nov 29 22:05:51 2026 GMT
subject=CN = Example Internal Root CA
notAfter=Oct 13 09:00:00 2026 GMT
```

→ Four accounts are root-equivalent through the `docker` group, including `deploy-old`, which
nobody can explain: an access review finding. The Let's Encrypt certificates renew automatically.
The internal CA that Harbor's certificate chains to expires in **ten days**, and nothing alerted:
this is exactly exercise 2 in section 16, found by a check instead of by an outage.

**Hands-on lab (test VMs only)**

**Step 1 — Build it.** On every lab node, export the expiry of every local CA and certificate
file as a metric, using the same textfile pattern as the backup metric in section 5:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/cert-expiry-metrics.sh
set -euo pipefail
OUT=/var/lib/prometheus/node-exporter/cert_expiry.prom
TMP=$(mktemp "$OUT.XXXXXX")      # same directory, not *.prom: ignored until the rename
echo '# TYPE cert_not_after_timestamp_seconds gauge' > "$TMP"
for f in /usr/local/share/ca-certificates/*.crt /etc/docker/certs.d/*/ca.crt; do
  [ -f "$f" ] || continue
  end=$(date -d "$(openssl x509 -noout -enddate -in "$f" | cut -d= -f2)" +%s)
  echo "cert_not_after_timestamp_seconds{file=\"$f\"} $end" >> "$TMP"
done
chmod 644 "$TMP"
mv "$TMP" "$OUT"
```

Run it daily from a systemd timer, and add the alert on mon-01:

```yaml
groups:
  - name: certificates
    rules:
      - alert: CertificateFileExpiresSoon
        expr: (cert_not_after_timestamp_seconds - time()) / 86400 < 30
        labels:
          severity: ticket
        annotations:
          summary: "{{ $labels.file }} on {{ $labels.instance }} expires in {{ $value | humanize }} days"
      - alert: CertificateFileExpiresVerySoon
        expr: (cert_not_after_timestamp_seconds - time()) / 86400 < 7
        labels:
          severity: page
```

**Step 2 — Break it.** Create a short-lived lab CA and install it as if it were real:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 5 -subj "/CN=Lab Short-Lived CA" \
  -keyout /tmp/lab-ca.key -out /tmp/lab-ca.crt
sudo cp /tmp/lab-ca.crt /usr/local/share/ca-certificates/lab-short-lived.crt
sudo /usr/local/sbin/cert-expiry-metrics.sh
```

Within a scrape interval both alerts fire, weeks or days before any pull would fail.

**Step 3 — Fix it.** Remove the lab CA (`sudo rm /usr/local/share/ca-certificates/lab-short-lived.crt`
and `sudo update-ca-certificates --fresh`), rerun the script, watch the alerts resolve, and add
every certificate and CA you own to an inventory file with owner and renewal procedure.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| CA expiry unmonitored | `x509: certificate has expired` on every pull, on every node at once | `openssl x509 -noout -enddate -in CA_FILE` | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Forgotten accounts | Ex-colleagues or old deploy users still root-equivalent | `getent group sudo docker` | [Users & permissions](10-users-permissions-security.md) |
| Patch backlog | Known-exploited CVEs open for months | Harbor scan results, `apt list --upgradable` | [Packages](11-packages.md) |
| Exposed admin surfaces | Dokploy UI or Traefik dashboard reachable from the internet | `nmap -Pn -p 3000,8080 203.0.113.10` from outside | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Secrets in Git | Tokens found in history after a leak | gitleaks on the repository | [Security & DevSecOps](37-learn-security-devsecops.md) |

**Why it matters for troubleshooting.** Many "random" outages are security processes that lapsed:
an expired certificate, a revoked token, a disk full of an attacker's files. Knowing the inventory
turns those into lookups.

**Next step:** turn these processes into evidence for audits and customers.

### Compliance as evidence [L4 · Lead/SRE]

**Concept.** Frameworks such as **ISO 27001** and **SOC 2** ask an organisation to define controls
and prove that they operate. Engineers do not need to become auditors, but a Lead should know that
good operations already produce most of the evidence, if it is kept:

| Control area | What you already do in this handbook | Evidence an auditor accepts |
|---|---|---|
| Change management | MRs, reviews, change requests (section 11) | MR approval history, CR issues linked to deploys |
| Access control | Quarterly access review (previous topic) | Review issues with exported group lists and removals |
| Backup and recovery | Restore tests, DR drills (section 5) | Restore-test metrics, DR plan test history |
| Incident management | Incident issues and postmortems (section 11) | Incident timeline, postmortem, closed actions |
| Vulnerability management | Harbor and Trivy scans, patch targets | Scan reports, triage notes, patch logs |
| Logging and monitoring | Central logs, alert rules in Git | Retention settings, rule history |
| Asset inventory | Ansible inventory, Dokploy projects, AWS tags | Inventory files, tag reports (section 7) |
| Supplier management | Build vs buy decisions (section 10) | Vendor list with contracts (legal owns the contracts) |

Two Lead-level habits make audits cheap. **Automate evidence**: a monthly pipeline that exports
group memberships, scan summaries and restore-test results to a dated folder. **Policy as code**:
rules enforced by tools (a CI check that blocks unpinned images, Harbor policies that block
critical vulnerabilities, Kubernetes admission policies later) are controls that operate every
time, and their configuration in Git is the evidence.

**Key terms:** control, evidence, ISO 27001, SOC 2, policy as code, continuous compliance,
segregation of duties.

**See it on a real system.** One control, tested with data: were any production infrastructure
changes merged by their own author without another approval?

```bash
glab api "projects/ops%2Finfra/merge_requests?state=merged&updated_after=2026-07-01T00:00:00Z&per_page=100" \
  | jq -r '.[] | select(.merge_user.username == .author.username) | "!\(.iid)\t\(.merged_at[0:10])\t\(.title)"'
```

```
!412	2026-08-14	hotfix: raise checkout memory limit
!431	2026-09-02	traefik: temporary allowlist for vendor
```

→ Two self-merged changes in a quarter. The first was an incident hotfix (allowed as an emergency
change, if a CR was written within 24 hours); the second was not. The fix is a process one:
protected branches that require one approval, with a documented emergency path.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Fill the evidence table for your real team: for each control area, the
artefact that exists today and where it lives.

**Step 2 — Break it.** Pick three rows and try to produce the evidence for the last quarter in
under 15 minutes each. Note which ones you cannot produce.

**Step 3 — Fix it.** Automate the hardest one (for example a scheduled pipeline that exports group
memberships and restore-test results to a dated folder in a private repository).

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Evidence assembled by hand before audits | Weeks of screenshots every year | Automated monthly exports | This topic |
| Controls on paper only | Policy says "reviewed", history shows self-merges | Enforce with protected branches and tools | This topic |
| Compliance as a separate project | Engineers see it as overhead and avoid it | Map it to work already done | This topic |
| No emergency path | People bypass controls during incidents and hide it | Documented emergency change type | Section 11 |

**Why it matters for troubleshooting.** The same evidence that satisfies an auditor answers the
first incident questions: who changed what, when, approved by whom, and which backup can we trust.

**Next step:** measure how well the team delivers change: the DORA metrics.

---

## 14. DORA metrics

> 📚 **Study path:** 1) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) sections 2 and 3 (GitLab CI/CD, deployment strategies), the delivery system these metrics measure · 2) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Deployment (environments and deployments) ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 3) KodeKloud: *Fundamentals of SRE* — Release Engineering ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Practice: compute the metrics for one project with the script below every Monday for a month, and pick one improvement.

**Who starts here:** mid-level engineers learn what the metrics mean; seniors measure them for
their platform and use them to choose improvements; leads use them to discuss delivery with
management without turning them into targets for individuals.

The DORA research programme (DevOps Research and Assessment, now part of Google Cloud) found that
a handful of delivery metrics predict both software delivery performance and organisational
outcomes, and that speed and stability improve **together** rather than trading off. That
finding is the most useful argument a senior has against "we deploy rarely so we are safer".

### The four key metrics [L3 · Senior]

**Concept.** In the classic four-key model, two metrics measure throughput and two measure
stability:

| Metric | Question | Measured on your platform as | What improves it |
|---|---|---|---|
| Deployment frequency | How often do we deploy to production? | Successful production deployments per day or week (GitLab environments) | Small MRs, automated pipelines, standard changes |
| Lead time for changes | How long from commit to production? | Commit time to the deployment that shipped it | Fast pipelines, small batches, fewer manual gates |
| Change failure rate | What share of deployments cause a failure? | Deployments that caused an incident, rollback or hotfix, divided by all deployments | Tests, canary releases, review checklists |
| Time to restore service | How fast do we recover from a failure? | Incident start to service restored | Fast rollback, good alerts, runbooks, observability |

Recent DORA reports and the [dora.dev](https://dora.dev/) metrics guide replace the fourth metric
with **failed deployment recovery time** (recovery from a deployment that needed immediate
intervention, not from every incident) and add a fifth, **deployment rework rate** (the share of
deployments that are unplanned and happen because of a production incident). They also regroup
the five: change lead time, deployment frequency and failed deployment recovery time count as
throughput; change fail rate and rework rate as instability. The idea is unchanged: measure how
fast you deliver and how often delivery hurts.

The research groups teams into performance clusters that shift from year to year, so do not
memorise thresholds. As a direction: the best-performing teams deploy on demand, often several
times a day, with lead times under a day, low change failure rates and recovery within an hour.
Your useful comparison is with your own team last quarter.

Three rules keep the metrics honest:

**Measure the team and the system, never individuals.** Ranking people by deployments produces
tiny meaningless deployments and kills collaboration.

**Use trends, not targets.** Once a metric becomes a target it stops measuring anything
(Goodhart's law): deployment frequency rises when people split one change into five.

**Read throughput and stability together, and next to the SLOs.** Faster deployments with a rising
change failure rate and a burning error budget is not progress.

**Key terms:** deployment frequency, lead time for changes, change failure rate, time to restore
(failed deployment recovery time), rework rate, throughput, stability, Goodhart's law.

**See it on a real system.** Before measuring, check that the raw data exists. Every production
deployment must go through a GitLab job with an `environment:` (the deploy component in section 8
does this), and incidents must be issues with labels:

```bash
glab api "projects/apps%2Fshop-web/deployments?environment=production&order_by=updated_at&sort=desc&per_page=2" \
  | jq -r '.[] | "\(.environment.name)\t\(.updated_at)\t\(.status)\t\(.sha[0:7])"'
glab api "projects/ops%2Fplatform/issues?labels=incident&per_page=5" | jq -r '.[] | "#\(.iid)\t\(.labels | join(","))"'
```

```
production	2026-10-02T16:41:09.512Z	success	3f9c2d1
production	2026-10-02T11:03:47.880Z	success	9e1b7a4
#162	incident,sev1,app::shop-web,caused-by-deploy
#158	incident,sev3,app::blog-web
#151	incident,sev2,app::api,caused-by-deploy
#149	incident,sev3,app::shop-web
#147	incident,sev2,app::shop-web
```

→ Production deployments are recorded, and incidents carry an app label and, when a deployment
triggered them, `caused-by-deploy`. Those two habits are all the change failure rate needs. The
label is decided in the postmortem, not during the incident.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Agree the definitions for your team in writing: what counts as a
production deployment, where lead time starts (first commit, MR merge or pipeline start), what
counts as a failure, and when restore ends (mitigated, not root-caused).

**Step 2 — Break it.** Find two ways each metric could be gamed or miscounted on your platform
(for example deployments of unchanged images, or incidents never labelled `caused-by-deploy`).

**Step 3 — Fix it.** Add a rule or an automatic check against each, and write the definitions into
the README of the ops repository so the numbers mean the same thing every month.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Metrics used to rank people | Gaming, smaller and meaningless changes | Team-level dashboards only | This topic |
| Definitions drift | Numbers jump without any real change | Written definitions in the repository | This topic |
| Failures not labelled | Change failure rate looks perfect | Labelling decided in every postmortem | Section 11 |
| Throughput only | Faster deployments, more incidents | Show all four with the SLOs | Section 11, SLOs |

**Why it matters for troubleshooting.** A rising change failure rate tells you where incidents come
from before you study any single one of them, and a long time to restore points at missing
rollback paths, alerts or runbooks.

**Next step:** compute the numbers from GitLab.

### Measuring DORA on GitLab [L3 · Senior]

**Concept.** GitLab's built-in DORA dashboards need the Ultimate tier. On other tiers you can
compute the same metrics from the API: deployments of the `production` environment for frequency
and lead time, and incident issues for failure rate and time to restore. The script below is
small enough to read in full, which matters: a metric nobody can explain is a metric nobody
trusts.

```bash
#!/usr/bin/env bash
# dora.sh GROUP/PROJECT [DAYS] - DORA metrics for one project's production environment
set -euo pipefail
PROJECT=${1:?usage: dora.sh group/project [days]}
DAYS=${2:-30}
SINCE=$(date -u -d "-$DAYS days" +%Y-%m-%dT%H:%M:%SZ)
P=${PROJECT//\//%2F}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

glab api --paginate "projects/$P/deployments?environment=production&status=success&updated_after=$SINCE&order_by=updated_at&per_page=100" \
  | jq -s 'add // []' > "$TMP/deploys.json"
glab api --paginate "projects/ops%2Fplatform/issues?labels=incident,app::${PROJECT##*/}&created_after=$SINCE&per_page=100" \
  | jq -s 'add // []' > "$TMP/incidents.json"

DEPLOYS=$(jq length "$TMP/deploys.json")
FAILED=$(jq '[.[] | select(.labels | any(. == "caused-by-deploy"))] | length' "$TMP/incidents.json")
awk -v d="$DEPLOYS" -v n="$DAYS" 'BEGIN {printf "deployments:            %d in %d days (%.1f per day)\n", d, n, d/n}'

jq -r '.[] | [.deployable.commit.committed_date, .updated_at] | @tsv' "$TMP/deploys.json" \
  | while IFS=$'\t' read -r c d; do echo $(( ($(date -d "$d" +%s) - $(date -d "$c" +%s)) / 3600 )); done \
  | sort -n | awk '{a[NR]=$1} END {if (NR) print "median lead time:       " a[int((NR+1)/2)] " h"}'

if [ "$DEPLOYS" -gt 0 ]; then
  echo "change failure rate:    $FAILED of $DEPLOYS ($(( 100 * FAILED / DEPLOYS )) %)"
fi

jq -r '.[] | select(.closed_at != null) | [.created_at, .closed_at] | @tsv' "$TMP/incidents.json" \
  | while IFS=$'\t' read -r o c; do echo $(( ($(date -d "$c" +%s) - $(date -d "$o" +%s)) / 60 )); done \
  | sort -n | awk '{a[NR]=$1} END {if (NR) print "median time to restore: " a[int((NR+1)/2)] " min"}'
```

Limits you should state whenever you show the numbers: lead time starts at the commit date of the
deployed commit (with merge commits that is the merge time, not the first commit); time to restore
uses issue creation and closing, so incidents must be closed when service is restored and the
follow-up work tracked in separate issues; incidents are attributed to an app by label.

**Key terms:** environment, deployment record, `--paginate`, median versus mean, attribution,
data quality.

**See it on a real system.**

```bash
GITLAB_HOST=gitlab.example.com ./dora.sh apps/shop-web 30
```

```
deployments:            42 in 30 days (1.4 per day)
median lead time:       19 h
change failure rate:    3 of 42 (7 %)
median time to restore: 38 min
```

→ A healthy picture with one obvious lever: 19 hours from commit to production is mostly MRs
waiting for review overnight. Medians are used on purpose: one incident that lasted a day would
dominate a mean and hide the typical case.

**Hands-on lab (lab GitLab or a sandbox group)**

**Step 1 — Build it.** Make sure two lab projects deploy through a job with
`environment: production`, label incidents as above, and run the script for each.

**Step 2 — Break it.** Redeploy the same commit five times without a change and rerun: deployment
frequency jumps and lead time falls, although nothing was delivered.

**Step 3 — Fix it.** Count only deployments whose commit differs from the previous deployment's
commit (compare `.sha` with the previous element after sorting by time), note the definition in
the README, and from now on run the script every Monday and plot the four lines.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Deploys outside the pipeline | Frequency too low, lead time missing | Compare `docker service inspect` update times with GitLab deployments | Section 11, change management |
| Redeploys counted | Frequency inflated | Distinct commit SHAs per period | This topic |
| Incidents left open for follow-up work | Time to restore in days | Close at restore; track follow-ups separately | Section 11, postmortems |
| Token with too many rights | Script token could change projects | Use a `read_api` token, stored outside the script | [Security & DevSecOps](37-learn-security-devsecops.md) |

**Why it matters for troubleshooting.** When the change failure rate of one app rises, the next
incident there is likely deploy-related: check "what changed?" first, and invest in that app's
tests and canary before the next release.

**Next step:** troubleshooting at senior level, beyond the single root cause.

---

## 15. Senior-level troubleshooting

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Incident Management → [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page) and [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Read: Google SRE book, [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 3) Note: [Site down](25-playbook-site-down.md) and [Slow system](23-playbook-slow-system.md), the layered walks this section assumes you already run fluently · 4) Practice: the one-bad-backend lab below, then classify your last ten incidents (or the 30 Ops Ladder cases) and choose one class to eliminate.

**Who starts here:** mid-level engineers find the broken layer and prove it; seniors read the
shape of a failure across the whole platform, and keep asking after the first root cause; leads
make whole classes of incidents disappear.

The playbooks in modules 21–26 teach a reliable method for one incident. Senior troubleshooting
adds three things: reading the **pattern** of a failure before touching any single host, refusing
to stop at the **first** cause, and turning the answer into a change that prevents the **class**,
not just the instance.

### Troubleshooting at system level [L3 · Senior]

**Concept.** Before opening a terminal, look at the shape of the failure. Which part of the
platform is affected, and which is not, usually narrows the cause to a layer in a minute:

| Pattern | Likely shared cause | First check |
|---|---|---|
| Every site, every node, at once | Something everything shares: edge, DNS, network, a CA or certificate, the upstream provider | Probes from outside, edge logs, certificate dates, provider status |
| Every app on one node | The node: disk, memory, Docker daemon, kernel, NIC | Node dashboard, `df -h`, `dmesg -T`, `docker info` |
| One app, every replica | The app's release or its dependency (database, external API) | Deploy history, app logs, dependency health |
| One replica of an app | That task or the node under it | `docker service ps`, logs of that task |
| A fixed share of requests fails (1 in 2, 1 in 3) | One bad member of a pool: a backend, an edge node, one of two DNS servers | Test each member directly |
| At fixed times | Scheduled work: backups, cron, cache expiry, log rotation, renewals | Timers and cron at those times |
| Slowly getting worse | Growth, leak, saturation | 30-day trend, not the last hour |
| Only some users | Network path, resolver, IPv6 versus IPv4, client version, region | Test from several vantage points |
| Right after a change | The change | "What changed?" (section 11) |

Then apply the habits that separate a senior from a fast mid-level engineer:

**Ask "why now?".** The system worked yesterday. Something changed: a deploy, a date, traffic, a
dependency, a certificate. The answer to "why now?" is often the root cause, or at least its
trigger.

**Make predictions.** For each hypothesis, say what else would be broken if it were true, and
check that first. "If Traefik's config is broken, every site on that node fails, including the
static ones" can be confirmed or ruled out in seconds.

**Mitigate before you understand.** If rolling back, failing over or removing a bad backend
restores service, do it, then investigate with the pressure off (section 11, incident command).

**Keep a hypothesis list.** Write hypotheses, evidence for and against, and owners in the incident
issue. It stops the team from testing the same idea twice and shows the IC where the
investigation stands.

**Key terms:** failure pattern, blast radius pattern, vantage point, "why now?", prediction,
hypothesis list, mitigation.

**See it on a real system.** "One request in two fails" for the shop behind the HA edge. Test
each edge node directly instead of the VIP:

```bash
for n in 192.0.2.10 192.0.2.11; do
  printf '%-12s ' "$n"
  curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' --resolve shop.example.com:443:$n https://shop.example.com/healthz
done
```

```
192.0.2.10   200 0.084s
192.0.2.11   502 0.012s
```

→ The VIP is on dok-prod-01 and works, but the standby edge on dok-prod-02 returns 502: its
Traefik configuration has drifted. Today nobody notices; on the day the VIP moves, everything
breaks. A probe per edge node (not only through the VIP) would have shown this weeks ago.

**Hands-on lab (lab VMs, continues the section 4 cluster)**

**Step 1 — Build it.** Run `who` with three replicas behind Traefik on dok-01 (section 4 lab), then
test it through Traefik on the `/health` path:

```bash
for i in $(seq 1 9); do curl -s -o /dev/null -w '%{http_code} ' -H 'Host: who.lab.example.com' http://192.168.56.11/health; done; echo
```

**Step 2 — Break it.** Make one replica unhealthy. From a debug container on `dokploy-network`,
find the task addresses with Swarm's `tasks.` DNS name and set the first one's health status
to 500:

```bash
docker run --rm -it --network dokploy-network alpine:3.20 sh
apk add --no-cache curl bind-tools
dig +short tasks.who
curl -s -X POST -d 500 http://FIRST_TASK_IP/health
exit
```

Repeat the test from Step 1:

```
200 500 200 200 500 200 200 500 200
```

→ Exactly one request in three fails: the shape that says "one bad member of a pool". Restarting
everything would hide it for a while; finding the member fixes it.

**Step 3 — Fix it.** Test each member directly from the debug container
(`for ip in $(dig +short tasks.who); do echo "$ip $(curl -s -o /dev/null -w '%{http_code}' http://$ip/health)"; done`),
which names the bad task. Then fix the class, not the instance: give Traefik a health check so it
removes bad members by itself:

```bash
docker service update \
  --label-add traefik.http.services.who.loadbalancer.healthcheck.path=/health \
  --label-add traefik.http.services.who.loadbalancer.healthcheck.interval=5s \
  who
```

Changing only service labels does not replace the tasks (Swarm redeploys only when the task
template changes), so the broken task is still running. Rerun the Step 1 loop: within about 20
seconds (Traefik's Swarm provider re-reads services every 15 seconds by default, then the first
check runs) the failures stop without any action from you, while the bad task stays out of
rotation for you to inspect. For a Dokploy-managed app, set the same health check in the app's settings so the
next deploy keeps it.

**How it breaks**

| Failure | Symptom | First command | Playbook |
|---|---|---|---|
| Testing only through the VIP or load balancer | Intermittent errors nobody can reproduce | Test each member directly | [Site down](25-playbook-site-down.md) |
| Debugging the loudest host | Hours on a symptom while the shared cause continues | Draw the pattern table first | This topic |
| Restart as diagnosis | Problem disappears, comes back next week | Collect evidence before restarting | [Containers & K8s](26-playbook-containers-k8s.md) |
| No "why now?" | Fix the effect, the trigger repeats | Timeline of changes and dates | Section 11, change management |
| Standby never tested | Failover lands on a broken node | Probe every member, not just the active one | Section 4 |

**Why it matters for troubleshooting.** Pattern reading is what makes seniors look fast: they
skip the layers the pattern has already ruled out.

**Next step:** once service is back, keep asking past the first cause.

### Contributing factors [L3 · Senior]

**Concept.** Complex systems rarely fail for one reason. An incident happens when several
conditions line up, like holes in slices of Swiss cheese: a trigger meets latent conditions that
were there for months, detection is late and the response is slower than it should be. "The root
cause" is usually just the last hole. A senior lists **contributing factors** in categories:

| Category | Question |
|---|---|
| Trigger | What event started it? |
| Latent conditions | What was already wrong and waiting? |
| Detection | Why did we not notice sooner, or why did a customer notice first? |
| Response | What slowed diagnosis or recovery? |
| Process and organisation | Which pressures, gaps or incentives made the conditions likely? |
| What limited the impact | What went right, and was it design or luck? |

Your June incident, analysed this way:

| Category | Contributing factor |
|---|---|
| Trigger | The Dokploy installer was run on a host where Apache held 80 and 443; its pre-check stopped with `Error: something is already running on port 80` |
| Latent condition | Apache had bound 0.0.0.0:80 and 443 for six years; no port inventory existed |
| Latent condition | No decision record said who owns the edge, so nobody checked before installing |
| Latent condition | Production was the first host the installer ever ran on; there was no staging host |
| Detection | The failure was visible only in the installer's terminal output; nothing alerted |
| Response | No runbook for a port conflict; diagnosis started from scratch |
| Process | The ticket asked to deploy on web01 by Friday; new platforms had no design review |
| What limited the impact | The installer's own port check refused to continue instead of taking the ports, so Apache kept serving: the vendor's design, luck for us |

Every row is a place to act, and most of them are not technical. A "5 whys" chain would probably
have stopped at "Apache was using ports 80 and 443", which explains the error but prevents nothing.

**Key terms:** contributing factor, trigger, latent condition, Swiss cheese model, detection gap,
response gap, 5 whys (and its limits), fishbone diagram.

**See it on a real system.** If postmortems record their factors in a small front matter block
(`contributing: no-inventory, no-staging, alert-gap`), the whole history becomes queryable:

```bash
grep -h '^contributing:' ~/work/ops/postmortems/*.md | cut -d: -f2 | tr ',' '\n' | sed 's/^ *//' \
  | sort | uniq -c | sort -rn | head -6
```

```
      6 alert-gap
      5 no-runbook
      4 no-staging
      4 manual-change
      3 no-inventory
      2 single-person-knowledge
```

→ Detection gaps appear in six postmortems, missing runbooks in five. Those are not six and five
separate problems; they are two systemic weaknesses, and fixing them improves every future
incident at once.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Write the contributing-factor table for one of your own incidents (or for
exercise 2 of section 16, as if it had happened), using all six categories.

**Step 2 — Break it.** Do a "5 whys" on the same incident and compare: which factors does the
single chain miss?

**Step 3 — Fix it.** Add a `contributing:` line with short tags to your postmortem template, and
backfill it for your last five postmortems so the query above starts producing data.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Stopping at the trigger | The fix is "do not do that again" | Ask for latent conditions | This topic |
| Only technical factors | Process gaps repeat in every incident | Fill the process row every time | This topic |
| Luck counted as design | "It went well" until luck runs out | Mark luck explicitly | Section 11, postmortems |
| Factors in prose only | Patterns invisible across incidents | Short tags in front matter | This topic |

**Why it matters for troubleshooting.** Latent conditions are tomorrow's incidents. Each one you
list and fix is an outage you never troubleshoot.

**Next step:** use the patterns to remove whole classes of incidents.

### Eliminating classes of incidents [L4 · Lead/SRE]

**Concept.** An **instance fix** repairs this incident: renew the certificate, delete the logs,
stop the process holding the port. A **class fix** makes the whole category impossible or
harmless. Class fixes follow a hierarchy, strongest first:

| Level | Meaning | Example |
|---|---|---|
| 1. Eliminate | The failure can no longer happen | Only Traefik binds 80/443; apps never publish host ports |
| 2. Automate | A machine does the error-prone step | ACME renews certificates; Ansible applies config from Git |
| 3. Guardrail | Mistakes are blocked or contained | CI rejects compose files with host ports; volumes protected by label filters |
| 4. Detect early | You learn days before users do | Expiry metrics, `predict_linear` disk alerts, drift reports |
| 5. Document and train | People know what to do | Runbooks, game days |

Level 5 alone is not a class fix; "more training" after every incident is a sign the team has run
out of better ideas. Applied to the classes that keep appearing on platforms like yours:

| Incident class | Instance fix | Class fix |
|---|---|---|
| Certificate or CA expiry | Renew the certificate | Automated renewal, an inventory with expiry metrics and alerts at 30 and 7 days (section 13) |
| Disk full | Delete files | Log rotation defaults, retention per store, prune timers, `predict_linear` alerts (section 6) |
| Port conflicts | Stop the other process | One edge for all HTTP, a port registry, a CI check for host ports ([Who owns this port?](22-playbook-ports-inventory.md)) |
| Configuration drift | Fix the server by hand | Config from Git through Ansible, a nightly `--check --diff` drift report |
| Bad deploys | Roll back | Canary releases, automatic rollback on burn rate, smaller MRs (section 14) |
| Leaked credentials | Rotate the secret | Secret scanning in CI, short-lived credentials (OIDC), no long-lived keys |
| Single dependency outage | Restart it | Redundancy (two resolvers, replicated registry), graceful degradation (section 3) |

**Choosing the class.** Rank classes by impact, not by count: a class that happens five times for
ten minutes matters less than one that happens three times and takes every site down.

**Key terms:** instance fix, class fix, hierarchy of controls, guardrail, recurrence rate,
incident taxonomy.

**See it on a real system.** With `class:`, `minutes:` and `sev:` lines (in that order) in each
postmortem's front matter, rank the classes by impact (minutes weighted by severity, SEV1 = 4 down
to SEV4 = 1):

```bash
awk -F': *' 'FNR==1 {c=""; m=0}
  /^class:/ {c=$2} /^minutes:/ {m=$2}
  /^sev:/ {n[c]++; impact[c] += m * (5 - $2)}
  END {for (k in n) printf "%-16s %3d %7d\n", k, n[k], impact[k]}' ~/work/ops/postmortems/*.md \
  | sort -k3 -rn
```

```
cert-expiry        3    1080
disk-full          5     700
port-conflict      2     330
bad-deploy         4     310
config-drift       2     120
```

→ Disk full happens most often, but certificate expiry costs the most, because when a CA expires
everything fails at once. The first class to eliminate is certificate expiry, with the section 13
inventory and automation; disk full comes second.

**Hands-on lab (no VM needed)**

**Step 1 — Build it.** Classify your last ten incidents (or the 30 Ops Ladder cases if your
history is short) with one class each, plus severity and minutes.

**Step 2 — Break it.** For the top class by impact, write down the instance fixes applied so far.
If every one is level 5 or an instance fix, the class will recur.

**Step 3 — Fix it.** Write an ADR and a small project for a level 1–3 fix of that class, sliced
so the first useful part ships within two weeks. Define the success metric as recurrence: zero
incidents of that class in the next two quarters.

**How it breaks**

| Failure | Symptom | First move | Read next |
|---|---|---|---|
| Class fix too big | Planned for months, never shipped | Slice it; ship detection first | Section 12, estimating |
| Training as the only control | Same class every quarter | Move up the hierarchy | This topic |
| No recurrence metric | Nobody knows whether the fix worked | Count the class per quarter | This topic |
| Ranking by count only | Effort goes to frequent, cheap incidents | Weight by severity and duration | This topic |

**Why it matters for troubleshooting.** The best incident is the one that cannot happen anymore.
Eliminating a class removes a whole branch from every future troubleshooting tree.

**Next step:** put everything together in senior scenario exercises.

---

## 16. Senior scenario exercises

> 📚 **Study path:** 1) Note: reread the sections each exercise names before you start; the exercises assume them · 2) KodeKloud: *Fundamentals of SRE* for the incident, SLO and change vocabulary ([course](https://kodekloud.com/courses/fundamentals-of-sre)), and *Ansible Basics Course* — Playbooks, Handlers and Roles for exercise 2 ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · 3) Video: Jeff Geerling *Ansible 101* ([playlist](https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN)) if `serial` and handlers are new · 4) Practice: timebox each exercise to 60–90 minutes, write your answer first, then compare it with the model outline.

**Who starts here:** mid-level engineers attempt the immediate-response half of each exercise;
seniors answer in full and produce the artefacts; leads add the people, budget and policy parts.
These are also the questions senior interviews ask, in the form "tell me how you would…"
([Career ladder](40-career-ladder.md) section 8 has the interview side).

Each exercise is open-ended on purpose: there is no single right answer, only better and worse
reasoning. Work in this order:

1. Write your own answer first, without looking at the outline: immediate actions, design or plan, artefacts, communication.
2. Compare with the model outline and mark what you missed. Missed items show you which section to reread.
3. Produce at least one real artefact per exercise (ADR, runbook, change request, design doc, message) and keep it in your portfolio.

### Exercise 1: host died at 2am [L3 · Senior]

**Scenario.** At 02:07 the monitoring on mon-01 pages: every site is down. dok-prod-01 does not
answer ping, and the hypervisor console shows the RAID controller has failed; the disk contents
may be unrecoverable. This is today's single-host platform (section 4). You are on call.

**Your task.** Part A: get service back tonight. Part B: on Monday, present a design in which the
loss of one host never takes all apps down again. Budget: two more VMs on the hypervisor cluster
and four weeks of your time; no new public IP.

**Model answer outline, part A (tonight).**

- Declare a SEV1 in the incident issue and act as IC and operator; call the secondary from the rota if it is not fixed within 20 minutes. Post "investigating" on the status page, which is hosted off the platform (section 12).
- Decide early, using the DR plan's declaration criteria (section 5): with a failed RAID controller, waiting for hardware is a gamble. Rebuild on spare capacity in parallel with the vendor call.
- Follow the recovery order from the DR plan: new VM from the template; Docker and the pinned Dokploy version; restore Dokploy's database and `/etc/dokploy` (Traefik config and `acme.json`) from the off-host backup; restore the app databases; deploy the apps from Harbor images (not from source); give the new VM 192.0.2.10 or move the NAT for 203.0.113.10; run the smoke test per site.
- Compute and report data loss against each app's RPO (newest backup time versus 02:07), and inform the app owners before customers ask.
- If no off-host backup exists, say so immediately to the manager: this becomes a business decision about data loss, not a technical problem.
- Resolve with criteria (probes green for 30 minutes), post the resolution message, keep the evidence, schedule the postmortem.

**Model answer outline, part B (the design).**

- The section 4 on-prem HA design: three Swarm managers, apps with two or more replicas and at most one per node, Harbor as Dokploy's registry, state moved to database VMs with a streaming replica and to object storage, a keepalived VIP with a second Traefik, Dokploy's own services pinned and backed up (an accepted deploy-time SPOF, written in an ADR), backups off-host and off-site with an immutable copy, monitoring and one probe outside the network.
- The senior catch: three VMs on **one** physical hypervisor host share fate. Use anti-affinity so the three nodes run on three physical hosts, ideally on different power circuits and switches, and verify it in the hypervisor's placement view.
- Prove it: a game day (section 5) that powers off dok-prod-01 at 10:00 on a Tuesday, with abort criteria.
- Artefacts: design doc DD-0004 with the failure modes table, ADRs (edge VIP, database replication), updated risk register, runbooks ("VIP failover", "promote db-02", "restore the Dokploy control plane"), DR plan update, cost and an estimate with a focus factor (section 12).

**What separates the stages.** A mid-level answer restores service with help and writes the
postmortem. A senior answer leads the recovery, notices the shared hypervisor failure domain and
delivers the design with ADRs. A lead answer also renegotiates the SLO and its budget, and makes
the game day a twice-yearly practice.

**Reread:** sections 2, 4, 5 and 11.

### Exercise 2: Harbor CA expires in 10 days [L3 · Senior]

**Scenario.** The section 13 check shows that the internal root CA that signed
`harbor.example.com`'s certificate expires on 13 October at 09:00 UTC, ten days from now. Forty
nodes trust it: 3 Dokploy/Swarm nodes, 12 Kubernetes nodes (containerd), 6 GitLab runners
(Docker, plus dind images with the CA baked in) and 19 Docker hosts owned by other teams. After
expiry, every pull and push to Harbor fails with `x509: certificate has expired or is not yet
valid`: no deploys, no scaling, and any rescheduled pod whose image is not cached fails.

**Your task.** A plan that finishes with three days of margin, executed safely, plus the class fix.

**Model answer outline.**

- Treat it as a slow incident: a SEV3 today that becomes a SEV1 on day 10. One owner, a daily check-in, a status message to every node owner today.
- Inventory before action: every place that trusts the CA. Find it by fingerprint, not by file name: system trust stores, `/etc/docker/certs.d`, `/etc/containerd/certs.d`, dind and other CI images, Harbor replication endpoints, Kubernetes workloads that call Harbor's API, the blackbox exporter's `ca_file`, developer laptops.
- Choose the strategy. **Option A, renew the same CA**: issue a new CA certificate with the same subject and the same key, with a longer validity. Existing leaf certificates (Harbor's) keep validating because issuer name and key are unchanged, so Harbor needs no change. It requires the CA private key; this is the moment you find out whether its offline copy exists. **Option B, new CA**: distribute a bundle with old and new CA, re-issue Harbor's certificate from the new CA, switch Harbor, then remove the old CA after every node is verified. More work, but the right moment to fix key size and custody. With ten days and 40 nodes, A is the safe choice now, and B can be planned calmly afterwards.
- Roll out with Ansible: one canary node of each type first, then batches with `serial`, and a real pull as the verification step on every node. Remember how each consumer reads trust: Docker reads `certs.d` at pull time, but the daemon loads the system store at start; containerd reads `certs.d/hosts.toml` at pull time, if `config_path` is set in its registry configuration; dind images must be rebuilt and the CI component version bumped.
- Verify globally with the expiry metric from section 13: the count of nodes still reporting the old date must reach zero, and the 19 nodes of other teams need a named confirmation each.
- Afterwards: a postmortem (why only ten days of notice? The overdue action #142 from section 11 is a contributing factor), expiry alerts at 90, 30 and 7 days for every CA, a tested runbook "renew the internal CA", key custody rules, and a decision on a private ACME CA (for example step-ca) with short-lived, automatically renewed certificates ([Security & DevSecOps](37-learn-security-devsecops.md), TLS and PKI).

Option A on the offline machine that holds the CA key; `-signkey` keeps the subject and the
extensions (including the Subject Key Identifier) and resets the dates:

```bash
openssl x509 -in ca.crt -noout -subject -enddate -ext subjectKeyIdentifier
openssl x509 -in ca.crt -signkey ca.key -days 3650 -set_serial 0x$(openssl rand -hex 16) -out ca-renewed.crt
openssl x509 -in ca-renewed.crt -noout -subject -enddate -ext subjectKeyIdentifier,basicConstraints
openssl verify -CAfile ca-renewed.crt harbor.crt
```

```
subject=CN = Example Internal Root CA
notAfter=Oct 13 09:00:00 2026 GMT
X509v3 Subject Key Identifier:
    3A:9F:1C:...:D2
subject=CN = Example Internal Root CA
notAfter=Sep 30 11:02:17 2036 GMT
X509v3 Subject Key Identifier:
    3A:9F:1C:...:D2
X509v3 Basic Constraints: critical
    CA:TRUE
harbor.crt: OK
```

The rollout play (the canary is the first batch of `serial`):

```yaml
- name: Roll out the renewed internal CA
  hosts: harbor_clients
  become: true
  serial: [1, "25%", "100%"]
  max_fail_percentage: 0
  vars:
    ca_src: files/example-internal-root-ca.crt
  tasks:
    - name: System trust store
      ansible.builtin.copy:
        src: "{{ ca_src }}"
        dest: /usr/local/share/ca-certificates/example-internal-root-ca.crt
        mode: "0644"
      notify: Update CA trust

    - name: Docker registry trust directory
      ansible.builtin.file:
        path: /etc/docker/certs.d/harbor.example.com
        state: directory
        mode: "0755"
      when: "'docker_hosts' in group_names"

    - name: Docker registry trust (read at pull time)
      ansible.builtin.copy:
        src: "{{ ca_src }}"
        dest: /etc/docker/certs.d/harbor.example.com/ca.crt
        mode: "0644"
      when: "'docker_hosts' in group_names"

    - name: containerd registry trust directory
      ansible.builtin.file:
        path: /etc/containerd/certs.d/harbor.example.com
        state: directory
        mode: "0755"
      when: "'k8s_nodes' in group_names"

    - name: containerd CA file
      ansible.builtin.copy:
        src: "{{ ca_src }}"
        dest: /etc/containerd/certs.d/harbor.example.com/ca.crt
        mode: "0644"
      when: "'k8s_nodes' in group_names"

    - name: containerd hosts.toml (needs config_path = /etc/containerd/certs.d)
      ansible.builtin.copy:
        dest: /etc/containerd/certs.d/harbor.example.com/hosts.toml
        mode: "0644"
        content: |
          server = "https://harbor.example.com"

          [host."https://harbor.example.com"]
            capabilities = ["pull", "resolve", "push"]
            ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
      when: "'k8s_nodes' in group_names"

    - name: Flush handlers before testing
      ansible.builtin.meta: flush_handlers

    - name: Prove a pull works (Docker hosts)
      ansible.builtin.command: docker pull harbor.example.com/library/healthcheck:1.0
      changed_when: false
      when: "'docker_hosts' in group_names"

    - name: Prove a pull works (Kubernetes nodes)
      ansible.builtin.command: crictl pull harbor.example.com/library/healthcheck:1.0
      changed_when: false
      when: "'k8s_nodes' in group_names"

  handlers:
    - name: Update CA trust
      ansible.builtin.command: update-ca-certificates
```

**What separates the stages.** A mid-level answer copies the file to every node by hand. A senior
answer inventories by fingerprint, chooses between renewing and replacing with a reason, rolls out
with a canary and a verification on every node, and fixes the class. A lead answer also asks why
the overdue postmortem action did not trigger an escalation, and changes how overdue actions are
reviewed.

**Reread:** sections 11 (postmortems, change management), 13 and 15.

### Exercise 3: cut the cloud bill by 30% [L3 · Senior]

**Scenario.** The AWS bill has been about 12,000 a month for six months: the shop's warm standby,
staging, CI runners and an analytics stack. The CFO asks for 30 % less within one quarter.
Reliability must not get worse.

**Your task.** A plan with numbers, the order of work, the risks, and how you will report results.

**Model answer outline.**

- Inform before cutting: cost by service, account, tag and usage type (section 7), the untagged share, an owner per line, and the unit cost (per 1,000 orders) as the headline metric, so growth does not hide efficiency.
- Order matters: clean up and rightsize **before** committing, or the Savings Plan pays for waste.
- Protect reliability explicitly: production Multi-AZ and the DR tier stay unless the app owner signs a changed RPO/RTO in an ADR. Cost decisions that change RPO or RTO are business decisions.
- Add guardrails so the savings last: budgets with alerts, anomaly detection, a tagging policy, a monthly 30-minute review.

A plan that reaches the target:

| Step | Weeks | Saving per month |
|---|---|---|
| Delete idle: unattached volumes, old snapshots, idle load balancers, unused public IPv4 | 1–2 | 420 |
| gp2 → gp3, CloudWatch Logs retention 30 days, old backups to colder S3 classes | 1–3 | 400 |
| Schedule staging and analytics to run 12 hours on working days | 2–4 | 1,050 |
| Rightsize from p95 metrics (Compute Optimizer plus the CloudWatch agent for memory) | 3–8 | 780 |
| NAT data processing → S3 gateway endpoint and ECR interface endpoints | 4–6 | 310 |
| Compute Savings Plan (one year) on the remaining steady baseline | 9–12 | 900 |
| **Total** | | **3,860 (32 %)** |

**What separates the stages.** A mid-level answer lists cleanup ideas. A senior answer sequences
the work, protects the reliability decisions and measures unit cost. A lead answer also sets up
ownership and the monthly review so the bill does not drift back.

**Reread:** sections 5 (DR tiers) and 7; [Cloud & AWS](36-learn-cloud-aws.md) section 12.

### Exercise 4: client demands port 443 [L3 · Senior]

**Scenario.** A client's vendor writes: "Our application must run on port 443 on your server."
dok-prod-01 already serves ten sites on 443 through Traefik. The vendor insists on "a dedicated
443".

**Your task.** The questions you ask, the options, your recommendation, and the reply.

**Model answer outline.**

- Clarify the real requirement before choosing anything: Do they mean "reachable at `https://client.example.com`" without a port in the URL (almost always)? Does their app terminate TLS itself (their own certificate, client certificates, mTLS)? Is the protocol HTTP at all? Do their clients send SNI? Do partners allowlist a dedicated IP? What availability do they expect?
- **Option 1, the standard (most cases):** a Dokploy app on an internal port and a Traefik router `Host(client.example.com)` on the `websecure` entry point, with an ACME certificate or their own certificate loaded through the file provider. Port 443 is shared by name, exactly like the other ten sites. No new port, no new risk.
- **Option 2, TLS passthrough:** if they must terminate TLS themselves, a Traefik TCP router with `HostSNI` and `passthrough: true` on the same 443. Traefik routes by the SNI name without decrypting.
- **Option 3, a dedicated address:** only for protocols without SNI or a hard IP requirement. Do not try to bind a second address on dok-prod-01, because Dokploy's Traefik publishes `0.0.0.0:443`; use a separate VM with its own address and its own NAT rule.
- Also cover isolation (all Dokploy apps share `dokploy-network`, so a client app can reach other apps' internal ports; consider a separate host for untrusted code), capacity (section 6), the SLA they expect versus your SLO, a change request, and an ADR if TCP passthrough is a new pattern on the platform. [Deployment patterns](35-deployment-patterns.md) section 5 walks through the conversation.
- Reply with "not this way; here is a way that gets you what you need" (section 12): "Your application will be reachable at https://client.example.com on port 443 from tomorrow. If you need to terminate TLS with your own certificate, we can pass the encrypted connection straight to your container. Could you confirm which of the two you need?"

Option 2 as a file provider route:

```yaml
# /etc/dokploy/traefik/dynamic/client-passthrough.yml
tcp:
  routers:
    client-passthrough:
      entryPoints: [websecure]
      rule: "HostSNI(`client.example.com`)"
      service: client-tls
      tls:
        passthrough: true
  services:
    client-tls:
      loadBalancer:
        servers:
          - address: "client-app:8443"
```

```bash
openssl s_client -connect 203.0.113.10:443 -servername client.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer
openssl s_client -connect 203.0.113.10:443 -servername shop.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer
```

```
subject=CN = client.example.com
issuer=C = US, O = Client Corp, CN = Client Corp Issuing CA
subject=CN = shop.example.com
issuer=C = US, O = Let's Encrypt, CN = R11
```

→ The same address and port present the client's own certificate for their name and Traefik's
Let's Encrypt certificate for the shop: one port 443, two TLS owners.

**What separates the stages.** A junior opens a new port. A mid-level engineer routes by host name.
A senior asks what the client actually needs, offers passthrough or a separate host only when it is
required, and covers isolation and the SLA. A lead turns the answer into a documented pattern so
the next request takes a day, not a debate.

**Reread:** section 12 (saying no); [Deployment patterns](35-deployment-patterns.md) sections 2 and
5; [Case study](21-case-apache-443-dokploy.md).

### Exercise 5: on-call burnout [L4 · Lead/SRE]

**Scenario.** Three engineers share a 24×7 rotation. The pager sent about 60 notifications last
week (the section 11 query), a third of them at night. One engineer has resigned and named on-call
as the reason. Your manager asks you to fix on-call within six weeks.

**Your task.** A data-driven plan, the rotation you propose, and how you will show progress.

**Model answer outline.**

- Start with data, not opinions: export four weeks of pages and tag each with alert name, time of day, whether it needed action, and what the action was.
- Typical findings, and what to do with them: a few alerts produce most pages (a disk alert at 80 % on a host whose usage is flat, an HTTP probe without `for:` that flaps, a CPU alert on the batch host every night at 02:00). Delete or demote anything that fails the four tests of section 11, add `for:` and grouping, fix the top causes (log rotation, the batch schedule, the flapping probe), and move tickets to business hours with Alertmanager routing.
- Replace cause-based pages with symptom-based ones: SLO burn-rate alerts for user-facing services (section 11).
- Redesign the rotation honestly: three people cannot sustain 24×7 within the SRE book's bounds. Propose business-hours primary plus SEV1-only best-effort nights with compensation, or a partner for nights, and align the SLO document with the coverage you actually have. This needs the manager's signature, because it changes what the business is promised.
- Protect people: time off after night pages, shadowing to grow the rotation (section 12, mentoring), and a hiring case built from the data.
- Measure weekly and publish: pages per week (target under 10), after-hours pages (under 2), actionable share (over 90 %), time to acknowledge.

**What separates the stages.** A senior answer cleans up alerts and fixes the noisiest causes. A
lead answer also changes the rotation policy, renegotiates the SLO to match the coverage, and makes
the case for headcount with numbers.

**Reread:** section 11 (on-call design, SLO negotiation) and section 15 (classes of incidents).

### Exercise 6: Kubernetes or not [L4 · Lead/SRE]

**Scenario.** The CTO says: "Everyone runs Kubernetes. Should we move off Dokploy? I want a
recommendation in two weeks." Context: 23 services, three development teams growing to five, one
operations engineer (you, CKA in progress), on-prem platform with AWS for DR.

**Your task.** The recommendation document and how you reach it.

**Model answer outline.**

- Frame the problem first: which pains would Kubernetes solve? Collect them from the teams: isolation between teams, autoscaling, GitOps, policy enforcement, ecosystem, hiring. List the costs as precisely: skills, upgrades (Kubernetes ships about three minor versions a year, each with roughly 14 months of patch support, so upgrades are a permanent chore), a highly available control plane and etcd, storage, ingress, certificates, observability, RBAC, Pod Security Admission and NetworkPolicies.
- Options: A, stay on Dokploy and finish the HA project; B, Kubernetes on-prem (kubeadm or k3s) with Argo CD; C, managed EKS for new workloads with Dokploy on-prem for the rest; D, build skills on a staging cluster now and move when defined triggers are met.
- Must-haves first, then the weighted matrix with a sensitivity check (section 10).
- A two-week proof of concept with one real service on a three-node cluster (Argo CD, Traefik ingress, cert-manager), measuring deploy time, the operational work it created, and behaviour when a node is killed.
- A typical recommendation for this context: "Not yet for production. Finish the Dokploy HA project; run a staging Kubernetes cluster to build skills; move production when two of these triggers are true: more than five teams needing isolation, a real autoscaling need, a second operations engineer hired, a compliance requirement for policy enforcement." A different context can justify the opposite answer; what matters is that the triggers are explicit.
- Deliver a design doc with the matrix and the PoC results, plus an ADR. Present costs in people as well as money.

**What separates the stages.** A senior answer compares the technologies honestly and runs the
PoC. A lead answer frames it as a business decision with triggers, people costs and a reversible
path, so the CTO can decide and revisit.

**Reread:** sections 8 (golden paths, Dokploy versus Kubernetes) and 10; [Learn: Kubernetes](31-learn-kubernetes.md).

### Exercise 7: production volumes deleted [L3 · Senior]

**Scenario.** At 14:10 the disk of dok-prod-01 is at 97 %. Following an old wiki snippet, a junior
runs `docker volume prune --all --force`. At that moment the `shop-db` service was being
redeployed, so its named volume counted as unused and was deleted, with six other volumes. The new
task started with an empty volume; MySQL initialised an empty database, and the shop is showing
errors and empty pages.

**Your task.** The response in the first hour, the recovery, and the changes afterwards.

**Model answer outline.**

- Declare a SEV1 and **stop new writes first**: put the shop into maintenance (the errors middleware from section 3, or scale the web service to zero), so no new orders land in the empty database and complicate the restore.
- Freeze the scene: no further cleanup, keep the shell history, and capture the daemon's recent events before they are gone.
- Assess what is lost: the list of destroyed volumes, the owner of each, and the newest backup of each.
- Restore the shop database from the newest dump into a fresh volume, verify row counts, then reopen. The painful lesson: if MySQL's binary logs lived in the same volume, point-in-time recovery is impossible and the RPO is the last dump (about 13 hours of orders). With the section 4 and 5 design (database on db-01, binary logs or WAL shipped off-host), it would have been about a minute.
- Reconcile the lost orders with the payment provider's records and order e-mails; decide with the business how to contact affected customers.
- Restore or rebuild the other six volumes once their owners are found.
- Blameless postmortem: the junior followed the documentation; the system allowed the deletion. Contributing factors: disk alert too late and no forecast, no log rotation, a dangerous wiki snippet, everyone in the `docker` group, the database on the app host with a node-local volume, binary logs next to the data, no maintenance-mode runbook.
- Class fixes: remove volume pruning from every runbook and wiki page, and use image and builder pruning with time filters instead; disk forecasts (section 6); databases off the app hosts with off-host log shipping; least privilege for the `docker` group; a tested "disk full on a Docker host" runbook.

The first commands, in order (read-only except the maintenance switch):

```bash
docker service scale shop-web-1a2b3c=0
docker events --since 2026-10-03T14:00:00 --until 2026-10-03T14:20:00 --filter type=volume --filter event=destroy
sudo tail -20 /home/USERNAME/.bash_history     # saved when that shell exits; also copy the open terminal
docker volume ls --format '{{.Name}}' | sort
sudo bash -c 'set -a; . /etc/restic/env; restic snapshots --latest 3'
```

```
shop-web-1a2b3c scaled to 0
2026-10-03T14:10:31.552871210Z volume destroy shop-db-data (driver=local)
2026-10-03T14:10:31.601440875Z volume destroy blog-uploads (driver=local)
2026-10-03T14:10:31.640118007Z volume destroy 3f1e9a0c7b... (driver=local)
```

→ The events confirm what was destroyed and when (14:10:31), which fixes the start of the data
loss window. In a Dokploy-managed app, scale through the Dokploy UI if you can, so its state
matches what you did.

**What separates the stages.** A mid-level answer restores the database. A senior answer stops the
writes first, measures the data loss honestly, runs a blameless postmortem and removes the class.
A lead answer also changes who is in the `docker` group and how wiki snippets are reviewed.

**Reread:** sections 4, 5 and 15; [Learn: Databases](38-learn-databases-ops.md).

### Exercise 8: building power off for 8 hours [L4 · Lead/SRE]

**Scenario.** Facilities announce power maintenance from Saturday 22:00 to Sunday 06:00, five weeks
from now: the server room will be fully powered off. The shop must stay up; the api should; the
rest may be down. You have the AWS account and five weeks.

**Your task.** The plan, the cutover and failback runbooks, the rehearsal and the communication.

**Model answer outline.**

- Tier the services: shop (must stay up), api (should), blog and intranet (static maintenance page), internal tools (down), Harbor and GitLab (deploy freeze for the weekend).
- Build a temporary warm standby in AWS for shop and api from the section 4 AWS reference architecture at minimum size: images replicated to ECR, secrets copied, ACM certificates issued, partner allowlists updated with the AWS addresses a week ahead.
- Data: replicate the databases to AWS over the site-to-site VPN days before (a replica on EC2, or a managed service that supports your engine version), and check the initial sync time against the VPN bandwidth.
- DNS: lower the TTL of the affected records to 60 seconds at least a week before, and host the maintenance pages for Tier 3 sites as static files in S3 behind CloudFront.
- Cutover runbook (Saturday 21:00): change freeze, checkout read-only for a few minutes, final sync check, promote the AWS database, switch DNS, smoke tests, then the on-prem shutdown checklist before 22:00.
- The senior catches: scheduled jobs must run on one side only (disable cron and timers on the passive side, or orders get processed twice); e-mail sending addresses must be allowed by SPF; payment provider webhooks may be allowlisted by IP; sessions must survive or users must log in again.
- Failback (Sunday): power-on order (network, DNS, storage, databases, Swarm managers, apps), checks for hardware that does not come back after a cold start, reverse sync of the data written in AWS, a second short read-only window, DNS back, then tear down or keep the standby as the new DR tier.
- A full dress rehearsal a week before with a test hostname, with abort criteria; communication: customer notice 72 hours before, an internal plan, two people on shift with a named IC.
- Cost: a few days of temporary infrastructure, small compared with eight hours of lost shop revenue; say so in the proposal.

**What separates the stages.** A senior answer designs the cutover and the failback. A lead answer
also negotiates which services may be down, staffs the night, owns the communication, and uses the
event to decide whether the temporary standby should become the permanent DR tier.

**Reread:** sections 4 (AWS reference architecture, hybrid DR), 5 and 12;
[Cloud & AWS](36-learn-cloud-aws.md) sections 6 and 11.

---

## 17. Self-check and exit test

> 📚 **Study path:** 1) Practice: answer the questions for your stage without notes, then reread the section in brackets for every miss · 2) KodeKloud: *Fundamentals of SRE* — revisit the lessons behind any missed SLO, incident or change question ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Practice: the timed tasks on your lab VMs, or in the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) and [Docker playground](https://kodekloud.com/playgrounds/playground-docker) when the homelab is busy · 4) Note: [Career ladder](40-career-ladder.md) section 12 (Self-check and exit tests) to place your result on the ladder.

**Who starts here:** everyone, at their own stage. Answer all questions of your stage and the
stage below without notes, then do the timed tasks with a timer and only the runbooks and
reference modules open, as in a real incident. You pass a stage when you answer at least 80 % of
its questions correctly and complete its timed tasks within the time and the pass criteria.

### Fresher and Junior checks

| # | Question | Answer outline |
|---|---|---|
| 1 | What is a SPOF? Name four on today's platform and give each its type. | One component whose failure alone stops the service; for example the single host (runtime), Harbor (deploy-time), backups on the same disk (recovery-time), the internal CA (slow-burn) (section 2) |
| 2 | How do a backup, a replica and a snapshot differ? | Only an off-host backup with retention protects against mistakes and lost hosts; a replica copies mistakes; a snapshot on the same storage dies with it (section 5) |
| 3 | What does 3-2-1-1-0 mean? | Three copies, two media, one off-site, one immutable or offline, zero errors in tested restores (section 5) |
| 4 | Why alert on the time of the last **successful** backup? | A job that never starts reports no failure; absence of success catches every case (section 5) |
| 5 | What must every runbook step contain? | Command, expected output, and what to do if the output differs (section 12) |
| 6 | What is the blast radius of restarting Docker on dok-prod-01? | Every container on that host restarts, so every site there has errors for a few minutes (sections 4 and 6) |
| 7 | What are RPO and RTO? | Maximum acceptable data loss in time; maximum acceptable time to restore service (section 5) |
| 8 | What does the scribe do during an incident? | Keeps the timeline with UTC times, commands and decisions, so nobody reconstructs it later (section 11) |

| Timed task | Time | Pass criteria |
|---|---|---|
| Restore yesterday's lab database dump into a scratch database and verify a row count | 20 min | Correct count; the production database untouched |
| Write the runbook "Traefik container stopped" and have a colleague follow it | 30 min | Colleague restores service without asking you anything |
| List every SPOF of dok-01 with its type and one mitigation each | 15 min | At least one SPOF of each of the four types |

### Mid-level checks

| # | Question | Answer outline |
|---|---|---|
| 1 | Edge 99.9 %, app 99.9 %, database 99.95 % in series: what availability can users get at most? | 0.999 × 0.999 × 0.9995 ≈ 99.75 % (section 3) |
| 2 | Why is a two-manager Swarm worse than one manager? | Raft needs a majority; with two managers, losing either loses quorum, so you doubled the failure chance (section 4) |
| 3 | The replica lag query shows 30 seconds on a quiet primary. Is data at risk? | Not necessarily: with no new transactions the timestamp ages; compare with write activity (section 5) |
| 4 | What happens when `archive_command` keeps failing? | WAL is retained in `pg_wal` until the disk fills and PostgreSQL stops (section 5) |
| 5 | Name the three change types with an example of each on this platform. | Standard (pipeline deploy), normal (Dokploy upgrade), emergency (rollback during an incident) (section 11) |
| 6 | What makes a postmortem action item strong? | Specific, owner, due date, priority and type (prevent, detect, mitigate, process) (section 11) |
| 7 | What do you look for first in a Terraform plan? | Deletions and replacements (`delete,create`) (section 12) |
| 8 | Why does a legacy Apache site loop behind Traefik, and what are the two fixes? | Apache sees plain HTTP and redirects to HTTPS forever; trust `X-Forwarded-Proto` or remove the redirect from Apache (section 9) |

| Timed task | Time | Pass criteria |
|---|---|---|
| Write the change request to disable Apache, with rollback and a go/no-go list | 30 min | A reviewer can execute and roll back from it alone |
| Make `who` on the lab survive the loss of dok-01 (three managers, VIP) and prove it with a curl loop | 60 min | Under 5 seconds of errors when dok-01 is powered off |
| Review the five-problem MR from section 12 without notes | 15 min | All five problems found, each with the risk explained |

### Senior checks

| # | Question | Answer outline |
|---|---|---|
| 1 | Which four details decide whether the on-prem HA design works? | Dokploy's services can move to empty volumes; images must come from a registry; ACME certificates on two edges; the second Traefik is yours to manage (section 4) |
| 2 | Choose a DR tier for shop, api and blog, and justify one with money. | For example warm standby, pilot light, backup and restore; compare the standby's monthly cost with the cost of an hour of downtime (section 5) |
| 3 | 3 × 8 vCPU, peak 9.5 vCPU, growth 4 % a month, lead time 3 months plus 3 of horizon, 70 % target: order now? | Yes: 12.0 ÷ 0.7 = 17.2 vCPU needed against 16 with one node down (section 6) |
| 4 | What is in "EC2 - Other" on an AWS bill? | EBS volumes and snapshots, NAT gateways, data transfer (section 7) |
| 5 | Why pin CI component versions, and what does `resource_group` prevent? | One commit cannot break every pipeline; two pipelines cannot deploy at the same time (section 8) |
| 6 | What is the point of no return in a migration, and where is it for checkout? | After it, rollback means losing or copying back data; for checkout, the first order written to the new database (section 9) |
| 7 | What do weak ADRs leave out? | Real alternatives, negative consequences with owners, and a validation and revisit condition (section 10) |
| 8 | Name the six categories of contributing factors. | Trigger, latent conditions, detection, response, process and organisation, what limited the impact (section 15) |
| 9 | Name the four DORA metrics and one way to game each. | Frequency (redeploys), lead time (definition drift), change failure rate (unlabelled incidents), time to restore (incidents closed late or early) (section 14) |

| Timed task | Time | Pass criteria |
|---|---|---|
| Write ADR-0003 for your platform and get one review | 90 min | Reviewer can explain why not option A, the biggest accepted risk, and when to revisit |
| Risk register (six or more risks) and phased cutover table for the Apache migration | 90 min | Every risk scoring 6 or more has a mitigation, owner and trigger; every phase has entry and exit criteria and a rollback |
| Exercise 2 (Harbor CA) in writing, including the rollout play | 60 min | Inventory by fingerprint, a justified strategy, canary and per-node verification, the class fix |

### Lead and SRE checks

| # | Question | Answer outline |
|---|---|---|
| 1 | Write an error budget policy in five lines. | SLO and window; actions at more than 50 %, 25–50 %, under 25 % and exhausted; postmortem trigger; who settles disputes (section 11) |
| 2 | What do you do in your first five minutes as IC of a SEV1? | Declare, assign roles by name, state the known facts, set the first mitigation with an owner and a timebox, post the first update with the next update time (section 11) |
| 3 | Why can four people not staff a healthy 24×7 rotation, and what do you offer instead? | The SRE book's bounds (about eight people for one site, at most two incidents a shift); business hours plus SEV1 best effort, a partner, and fewer pages (section 11) |
| 4 | When the three-year cost of build and buy is a tie, what decides? | Data location, skills and their value, exit cost, who is paged (section 10) |
| 5 | What is the hierarchy of controls for eliminating a class of incidents? | Eliminate, automate, guardrail, detect early, document and train (section 15) |
| 6 | What evidence shows an auditor that change management works? | MR approval history, CRs linked to deploys, the emergency path with CRs written within 24 hours (section 13) |

| Timed task | Time | Pass criteria |
|---|---|---|
| Command a 60-minute tabletop with injects (section 11) | 60 min | Roles assigned within 5 minutes, every update on time, every decision in the log, IC never at a terminal |
| Run a lab game day with a written plan and abort criteria (section 5) | 2 h + postmortem | Hypothesis tested with measured times; postmortem published within 5 days |
| Exercise 6 (Kubernetes or not) as a three-page recommendation | 2 h | Must-haves, weighted matrix with sensitivity, PoC plan, explicit triggers |

**Before you move up a stage,** your portfolio should hold the evidence, not just the knowledge:

| Stage reached | Evidence in your portfolio |
|---|---|
| Junior | A restore you performed and timed; two runbooks others have followed |
| Mid-level | A postmortem that changed something; a change request you executed; a reviewed MR with plan output |
| Senior | A design doc and ADRs that others built from; a migration plan with a risk register; a DR plan with test history |
| Lead / SRE | An agreed SLO with an error budget policy; a game day you ran; a class of incidents that stopped recurring |

---

## 18. Where to go next

> 📚 **Study path:** 1) KodeKloud: keep *Certified Kubernetes Administrator (CKA)* first until you pass it ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)); this module runs on the morning rep and the Sunday postmortem reading · 2) Note: [Roadmap](34-roadmap.md) and [Career ladder](40-career-ladder.md) section 13 (Your personal next steps) · 3) Read: the Google SRE books ([sre.google/books](https://sre.google/books/)) · 4) Practice: one senior exercise from section 16 each month, kept in your portfolio.

**Who starts here:** everyone who finished their stage's exit test.

This module is the top of the handbook's learning path, but it points back down constantly:
senior work is mostly the earlier modules applied with a wider scope. Where to go next depends on
your stage:

| Your stage | Next in this handbook | Next with KodeKloud | Artefact to produce next |
|---|---|---|---|
| Fresher, Junior | [Learn: Linux](27-learn-linux.md), [Learn: Networking](28-learn-networking.md), [Site down](25-playbook-site-down.md) | *Learning Linux Basics Course & Labs* ([course](https://kodekloud.com/courses/the-linux-basics-course)), then *Prep Course - Linux Foundation Certified System Administrator (LFCS)* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) | A timed restore and two runbooks |
| Mid-level | [Performance & observability](32-learn-performance-observability.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Deployment patterns](35-deployment-patterns.md) | *Certified Kubernetes Administrator (CKA)* ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)), *Fundamentals of SRE* ([course](https://kodekloud.com/courses/fundamentals-of-sre)) | A postmortem and a change request |
| Senior | [Cloud & AWS](36-learn-cloud-aws.md), [Security & DevSecOps](37-learn-security-devsecops.md), [Databases for DevOps](38-learn-databases-ops.md) | *AWS Certified CloudOps Engineer - Associate* ([course](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)), *HashiCorp Certified: Terraform Associate 004* ([course](https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004)) | The HA design doc, ADR-0003, the migration plan |
| Lead / SRE | [Career ladder](40-career-ladder.md) sections 6 and 11; this module's sections 11 and 15 again, applied to your team | *Certified Kubernetes Security Specialist (CKS)* ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)), *Prep Course - Prometheus Certified Associate (PCA)* ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) | An SLO with a policy, a game day, one class of incidents eliminated |

For your situation today (Junior moving to Mid-level, CKA in progress, the Apache to Dokploy
migration half done), the highest-value next steps are concrete:

1. Finish the CKA; keep this module to the morning slot until the exam is behind you.
2. Write ADR-0002 and ADR-0003 for the decisions you already made (section 10). It takes an evening and turns past work into senior evidence.
3. Move the backups off dok-prod-01 and run one timed restore (section 5). It removes the biggest risk on your platform.
4. Write the Apache migration plan with its risk register (section 9), then move one low-risk site with the strangler pattern.
5. Draft DD-0004, the HA design doc (sections 4 and 10), and show it to your manager with an estimate (section 12).

Books worth their time once the CKA is done: *Site Reliability Engineering* and *The Site
Reliability Workbook* (free to read at [sre.google/books](https://sre.google/books/)), *Accelerate*
by Forsgren, Humble and Kim (the research behind DORA), *Team Topologies* by Skelton and Pais
(platform teams), *Thinking in Systems* by Donella Meadows, and *The Field Guide to Understanding
'Human Error'* by Sidney Dekker (blameless thinking).

Every senior skill in this module grows the same way the troubleshooting skills did: one real
problem, one lab, one written artefact, one person taught, every week.
