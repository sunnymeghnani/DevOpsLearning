# 40 — Career Ladder: Fresher to Senior DevOps

This module is the map that ties the handbook together. The reference modules (01–20) tell
you which command to run. The playbooks (21–26 and 35) tell you what to do when something
breaks. The learn modules (27–33 and 36–39) explain why things work. None of them says what
to learn first, what an employer expects from you at each step, or how to prove you are ready
for the next one. That is this module's job.

It describes five career stages, from your first ops job to lead and SRE roles. Each stage gets
the same treatment: what good work looks like, a skills checklist, the incidents you should
handle without help, portfolio projects, a 90-day plan, the signs that you are ready to move up,
and the mistakes that hold people back at that stage. After the stages come a skills matrix,
interview preparation with model answers, a study method for KodeKloud, how to build public proof
of your skills, the soft skills that decide promotions, a self-check, and finally your own next
steps.

**Who it serves:** every stage. **[L0 · Fresher]** and **[L1 · Junior]** readers use it as a
study plan. **[L2 · Mid]** readers use it as a promotion checklist and for interview preparation.
**[L3 · Senior]** and **[L4 · Lead]** readers use it to mentor others and to build onboarding paths.
If you are a Junior moving to Mid (on the CKA track and finishing an Apache → Dokploy migration),
read sections 0, 3, 4, 8 and 13 first, then come back for the rest.

> Tags combine the Ops Ladder level and the career stage, for example **[L2 · Mid]**. Years of
> experience are typical ranges, not rules. Evidence moves you up a stage, not the calendar.
> Commands in this module are examples to study and run on a **test VM**, never on servers people
> depend on. Sample outputs are illustrative (Ubuntu 22.04/24.04) and use documentation addresses
> (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and example.com names. UPPERCASE words are
> placeholders. KodeKloud course titles, contents and free/paid status were checked on
> 3 October 2026 and can change, so re-check a course page before you buy or schedule anything.

---

## 0. How to use this module

> 📚 **Study path:** 1) Note: [README](README.md) triage and [34 — Roadmap](34-roadmap.md) (a quick refresher, so the handbook comes first) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics and Web Server, only if you are a Fresher ([link](https://kodekloud.com/courses/devops-pre-requisite-course)) · 3) Video: KodeKloud *Linux Crash Course for Beginners* ([YouTube](https://www.youtube.com/watch?v=a3ujwK65dgs)), Freshers only · 4) Practice: the ten-minute placement checks below, then one timed [SadServers scenario](https://sadservers.com/scenarios) to calibrate.

### Stages at a glance

| Stage | Typical experience | Ops Ladder level | Tag | You are trusted to | Exit test (from your Ops Ladder) |
|---|---|---|---|---|---|
| Fresher | 0–1 year | L0 Foundations | [L0 · Fresher] | do a defined task correctly on one server, with review | 30 min, no notes: sudo user with key-only SSH, five largest files under `/var`, every field of `ls -l`, revert a bad Git commit |
| Junior | 1–2 years | L1 Operator | [L1 · Junior] | keep a service running day to day from runbooks | 5 min: given only a port number, name the process, its unit, its config file and the command that shows its logs |
| Mid-level | 2–4 years | L2 Troubleshooter | [L2 · Mid] | own a system end to end and find the broken layer | 15 min: "the site is down", walk DNS, route, firewall, TLS, proxy and app, and name the broken layer with evidence |
| Senior | 4–7 years | L3 Platform | [L3 · Senior] | build and run the platform other people deploy to | one weekend: move an Apache workload into a container behind Dokploy, built by GitLab CI, pushed to Harbor, with a tested rollback |
| Lead / Staff / SRE | 5+ years | L4 SRE | [L4 · Lead] | make reliability a property of the organisation | game day: a random fault, found by an alert, fixed, and a published one-page postmortem |

```
  Fresher          Junior            Mid-level            Senior               Lead / Staff / SRE
  0-1 yr           1-2 yrs           2-4 yrs              4-7 yrs              5+ yrs
  L0 Foundations   L1 Operator       L2 Troubleshooter    L3 Platform          L4 SRE
 ──────────────► ───────────────► ──────────────────► ──────────────────► ─────────────────────►
  "How do I do     "How do I keep    "Why did it break,   "How do we make      "How does the whole
   this task?"      this running?"    and in which         this class of        organisation get
                                      layer?"              failure impossible?" reliably better?"

  unit of work:    a task            a service            a system             a platform        an organisation
  blast radius:    a test VM         one service          one product          many teams        the business
```

The question in the middle row is the real difference between stages. Commands are learned in
a few months. Moving from "how do I do this" to "why did it break" to "how do we stop it from
ever happening again" is what takes years, and it is what interviewers and promotion panels
listen for.

### Place yourself in ten minutes

Answer **yes** only if you have done the thing without help in the last six months and could
show evidence (a ticket, a commit, a note, a lab log). "I could probably do it" counts as no.

**L0 · Fresher checks**

- **1.** On a fresh VM and without notes, create a sudo user who can log in with an SSH key only.
- **2.** Explain every field of an `ls -l` line, including the number after the permissions.
- **3.** Undo a bad commit on a shared branch without rewriting history.

**L1 · Junior checks**

- **4.** Given port 8443, name the process, its systemd unit, its config file and its log command in under five minutes.
- **5.** Fix a "No space left on device" incident, including the cases where `df -h` shows free space.
- **6.** Write a systemd unit with a restart policy, kill the process and find the restart in the journal.

**L2 · Mid checks**

- **7.** Prove which layer broke in a "site is down" incident with a packet capture, a log line or `curl -v` output.
- **8.** Explain why `ufw deny` does not protect a published Docker port, and fix it properly.
- **9.** Diagnose `CrashLoopBackOff` and `ImagePullBackOff` from a registry with a private CA, without searching the web.

**L3 · Senior checks**

- **10.** Build commit → image tagged with the commit SHA → Harbor → deploy → tested rollback, end to end.
- **11.** Upgrade a kubeadm cluster by one minor version and restore etcd from a snapshot.
- **12.** Write a design document that other people reviewed, approved and built.

**L4 · Lead checks**

- **13.** Define an SLO for a real service and alert on how fast its error budget burns.
- **14.** Act as incident commander for an incident that involved more than one team.
- **15.** Change a process (on-call, change management, postmortems) across teams and keep it changed.

**Reading the result:** go down the list. The first group where you answer "no" to two or more
questions is your working stage. Read that stage's section and the one above it. If you answer
"yes" to most of a higher group but "no" in a lower one, you have a gap at the lower level. Fix
it first, because higher-level skills rest on it. A senior who can't read `ss` output gets found
out in the first incident.

### How to work through it

1. **Place yourself** with the checks above and write the date and your answers in your notes repo.
2. **Read your stage section fully**, then skim the next stage so you know where you are heading.
3. **Run the 90-day plan** for your stage. It names handbook modules, KodeKloud courses and an output for every two weeks.
4. **Turn every real incident into a five-line note**: the symptom, your first wrong guess, the evidence that settled it, the fix, and what you will check first next time.
5. **Re-score the skills matrix** (section 7) every quarter. Change a score only when you have new evidence.
6. **Move up when the "ready for the next stage" signs are true**, not when a number of years has passed.

### How the handbook fits together

| Handbook part | Modules | When it matters most | How to use it at each stage |
|---|---|---|---|
| Triage and cheat sheet | [README](README.md), [19 — Cheat sheet](19-cheatsheet.md) | Fresher onward | Fresher: memorise the seven-step triage. Senior: teach it |
| Reference | [01](01-storage-disk.md)–[18](18-web-http-tls.md), [20](20-macos.md) | every stage | Look up commands. Junior: know where everything is. Mid: know the gotchas |
| Case study | [21 — Apache 443 and Dokploy](21-case-apache-443-dokploy.md) | Junior → Mid | Your own incident as a runbook. Re-read it at each stage and notice what you now see |
| Playbooks | [22](22-playbook-ports-inventory.md), [23](23-playbook-slow-system.md), [24](24-playbook-network-speed.md), [25](25-playbook-site-down.md), [26](26-playbook-containers-k8s.md), [35](35-deployment-patterns.md) | Junior onward | Junior: run 22 and 23 alone. Mid: run all of them alone. Senior: improve them |
| Learn | [27](27-learn-linux.md), [28](28-learn-networking.md), [29](29-learn-webservers-proxies.md), [30](30-learn-docker.md), [31](31-learn-kubernetes.md), [32](32-learn-performance-observability.md), [33](33-learn-cicd-iac-sre.md), [36](36-learn-cloud-aws.md), [37](37-learn-security-devsecops.md), [38](38-learn-databases-ops.md), [39](39-learn-senior-architecture.md) | in stage order | The theory behind the playbooks, with labs |
| Roadmap | [34 — Roadmap](34-roadmap.md) | every stage | The topic-by-topic order of study. This module adds the career view on top |

---

## 1. The career map

> 📚 **Study path:** 1) Note: [34 — Roadmap](34-roadmap.md) for the topic order behind this map · 2) KodeKloud: the *Free Courses* page ([link](https://kodekloud.com/free-courses)) and the CKA learning path ([link](https://kodekloud.com/learning-path/cka)), to see what each stage costs · 3) Read: [roadmap.sh DevOps](https://roadmap.sh/devops) as a topic checklist only, not as a study plan · 4) Practice: score yourself in section 7 before you pick a stage plan.

**[All stages].** Read this once now, and again each time you move up a stage. It shows the
whole ladder, the courses and certificates in order, and what changes at each step.

### Scope, autonomy and trust

| Stage | Scope | Autonomy | Typical tasks | On-call role | Trusted with |
|---|---|---|---|---|---|
| **Fresher** [L0] | One task on one server | Follows runbooks. Every production change is reviewed or paired | User accounts, package installs, log checks, ticket triage, documentation fixes, small bash scripts | Shadows on-call. Never holds the pager alone | Read-only production access, test VMs, staging changes after review |
| **Junior** [L1] | One service or a handful of servers | Does routine work alone. Asks before non-routine changes | systemd units and timers, disk clean-ups, certificate renewals, SSH keys, deploys through existing pipelines, small CI fixes | Secondary on-call. Escalates early, with evidence | Standard (pre-approved) production changes, restarts, runbook execution |
| **Mid-level** [L2] | A whole system: host, proxy, app, DNS, TLS, pipeline | Owns tickets end to end. Asks for design review, not for help with steps | Multi-layer incident diagnosis, reverse proxy configuration, pipelines, migrations like Apache → Dokploy, Kubernetes workloads, Terraform modules | Primary on-call. Leads small incidents | Normal changes with a change request, migrations with a written rollback |
| **Senior** [L3] | A platform used by several teams | Sets technical direction for their area and unblocks others | Designs CI → registry → deploy platforms, builds and upgrades clusters, sets IaC standards, plans capacity, hardens hosts, reviews designs | Escalation point. Incident commander for medium-severity incidents | Architecture decisions, high-risk changes, tool choices, mentoring juniors |
| **Lead / Staff / SRE** [L4] | The organisation's reliability | Defines strategy and decides what not to do | SLOs and error budgets, incident process, postmortem culture, platform roadmap, cost, hiring | Incident commander for major incidents. Owns on-call health | Organisation-wide standards, budgets, hiring decisions, saying no |

### Levels, titles and years

**Titles vary between companies.** A "Senior DevOps Engineer" at a ten-person startup may do
the work this module calls Mid-level, and a "DevOps Engineer II" at a large company may do
Senior work. Judge a role by its scope (a task, a service, a system, a platform, an
organisation) and by what you are trusted with, not by the title.

**Years are averages.** Someone who handles two real incidents a week and writes them up
moves faster than someone who spends five years running the same playbook. Someone who changes
jobs every year may collect titles without depth. Promotion panels look for **sustained
behaviour at the next level**: you get promoted for already doing the next job, consistently,
for a few months.

**Skill levels and job stages are different things.** The Ops Ladder levels (L0–L4) measure
skill in an area. Career stages measure the job. Being uneven is normal: you can be L2 at
troubleshooting, L1 at containers and L0 at Terraform all at once. The stage you are at is
roughly the level you reach in **most** areas, plus the level of your judgement and
communication. The skills matrix in section 7 makes this visible.

**The three paths after Senior:**

| Path | Focus | You spend your week on | Measured by |
|---|---|---|---|
| Lead / manager | The team | Planning, hiring, unblocking, 1:1s, some hands-on work | The team's output and health |
| Staff / principal engineer | Technical direction across teams, still hands-on | Design docs, reviews, the hardest problems, prototypes | Decisions that hold up for years, other engineers' growth |
| SRE | Reliability as an engineering discipline | SLOs, automation that removes toil, incident process, capacity | Error budgets kept, toil removed, incidents that don't recur |

In this handbook all three sit at **[L4 · Lead]**, because the Ops Ladder L4 skills (metrics,
alerts, incident response, postmortems, change management) are what they share.

### Handbook modules by stage

| Stage | Start with | Master | Playbooks you must run alone | Learn modules |
|---|---|---|---|---|
| Fresher [L0] | [README](README.md) triage, [19](19-cheatsheet.md), [34](34-roadmap.md) | [01](01-storage-disk.md), [05](05-processes.md), [06](06-logs-journal.md), [07](07-services-systemd.md), [09](09-ssh-remote-access.md), [10](10-users-permissions-security.md), [11](11-packages.md) | none alone; read [22](22-playbook-ports-inventory.md) and [23](23-playbook-slow-system.md) so you know they exist | [27](27-learn-linux.md), [28](28-learn-networking.md) sections 1–3 |
| Junior [L1] | [21](21-case-apache-443-dokploy.md) phases 1–2 (inventory) | [02](02-network.md), [03](03-cpu-performance.md), [04](04-memory.md), [08](08-dns.md), [12](12-time-ntp.md), [13](13-kernel-system.md), [14](14-docker-containers.md) | [22 — Ports inventory](22-playbook-ports-inventory.md), [23 — Slow system](23-playbook-slow-system.md) first 60 seconds | [27](27-learn-linux.md) complete, [28](28-learn-networking.md) TCP, ports, NAT and firewalls, [30](30-learn-docker.md) |
| Mid-level [L2] | [25 — Site down](25-playbook-site-down.md) | [15](15-kubernetes.md), [16](16-aws-cloud.md), [18](18-web-http-tls.md) | [21](21-case-apache-443-dokploy.md), [23](23-playbook-slow-system.md), [24](24-playbook-network-speed.md), [25](25-playbook-site-down.md), [26](26-playbook-containers-k8s.md) | [28](28-learn-networking.md) DNS, HTTP, TLS and capture, [29](29-learn-webservers-proxies.md), [31](31-learn-kubernetes.md), [33](33-learn-cicd-iac-sre.md) CI and IaC parts, [36](36-learn-cloud-aws.md), [38](38-learn-databases-ops.md) |
| Senior [L3] | [35 — Deployment patterns](35-deployment-patterns.md) | everything above, well enough to teach it | all playbooks, plus improving them after each incident | [32](32-learn-performance-observability.md), [33](33-learn-cicd-iac-sre.md), [37](37-learn-security-devsecops.md), [39](39-learn-senior-architecture.md) |
| Lead / SRE [L4] | [39 — Senior architecture](39-learn-senior-architecture.md) | [32](32-learn-performance-observability.md) SLOs and alerting, [33](33-learn-cicd-iac-sre.md) SRE part | running incidents across teams with these playbooks as shared language | [34](34-roadmap.md) and this module, used to onboard and mentor others |

### KodeKloud courses by stage

All titles below are from the verified KodeKloud map (checked 3 October 2026). Do them in the
order listed. "Free" means listed on KodeKloud's
[Free Courses](https://kodekloud.com/free-courses) page on that date.

| Stage | Courses, in this order | Why this order |
|---|---|---|
| Fresher [L0] | [DevOps Pre-Requisite Course](https://kodekloud.com/courses/devops-pre-requisite-course) (Networking Basics, Web Server, SSL & TLS Basics) → [Learning Linux Basics Course & Labs](https://kodekloud.com/courses/the-linux-basics-course) → [Shell Scripts for Beginners](https://kodekloud.com/courses/shell-scripts-for-beginners) → [GIT for Beginners](https://kodekloud.com/courses/git-for-beginners) → [Docker Training Course for the Absolute Beginner](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner) (free) → [Crash Course: AWS Basics](https://kodekloud.com/courses/crash-course-aws-basics) (free) | Networking and web servers first, because every later topic sits on top of them. Linux next, then scripting and Git, because the L0 exit test needs both. Docker and AWS only as tasters |
| Junior [L1] | [Prep Course - Linux Foundation Certified System Administrator (LFCS)](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs) (Operations Deployment and Networking first) → [Linux Challenges](https://kodekloud.com/courses/linux-challenges) (free) → [Advanced Bash Scripting](https://kodekloud.com/courses/advanced-bash-scripting) (Streams, Good Practices, awk, sed) → [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course) (Engine, Networking, Image Management, Swarm; skip the Enterprise sections) → [Ansible Basics Course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course) → [Nginx For Beginners](https://kodekloud.com/courses/nginx-for-beginners) | LFCS Operations and Networking are exactly the L1 exit test. The Docker course's Engine sections (daemon troubleshooting, logging driver, publishing ports) are what a Dokploy server needs. Ansible makes your fixes repeatable |
| Mid-level [L2] | [Kubernetes for the Absolute Beginners – Hands-on Tutorial](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial) (fast) → [Certified Kubernetes Administrator (CKA)](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator) → [Kubernetes Challenges](https://kodekloud.com/courses/kubernetes-challenges) (free) → [Kubernetes Troubleshooting for Application Developers](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers) → [Demystifying DNS](https://kodekloud.com/courses/demystifying-dns) → [GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines](https://kodekloud.com/courses/gitlab-ci-cd) → [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-basics-training-course) → [AWS Networking Fundamentals](https://kodekloud.com/courses/aws-networking-fundamentals) | CKA first because it is your current track and troubleshooting is its largest domain. DNS and GitLab CI close the L2 and L3 gaps from your Apache/Dokploy work. Terraform before AWS so every AWS lab is code you can destroy |
| Senior [L3] | [Kubernetes Networking Deep Dive](https://kodekloud.com/courses/kubernetes-networking) → [Helm for Beginners](https://kodekloud.com/courses/helm-for-beginners) → [Prep Course - Prometheus Certified Associate (PCA)](https://kodekloud.com/courses/prometheus-certified-associate-pca) → [Grafana Loki](https://kodekloud.com/courses/grafana-loki) → [Certified Kubernetes Security Specialist (CKS)](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks) → [HashiCorp Certified: Terraform Associate 004](https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004) → [AWS Certified CloudOps Engineer - Associate](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate) | Platform depth: how traffic really flows in a cluster, how it is packaged, how it is observed and how it is secured. Then the IaC and cloud certificates that senior job adverts ask for |
| Lead / SRE [L4] | [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre) → [Certified Kubernetes Application Developer (CKAD)](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad) if your platform serves developers | SLOs, incident management, blameless postmortems and change management. Leadership itself is not a KodeKloud topic, so pair this with the [Google SRE books](https://sre.google/books/) |

KodeKloud has nothing on Traefik with Docker labels, Dokploy, Harbor, tcpdump, strace or the
Linux performance method. For those, use the handbook modules ([21](21-case-apache-443-dokploy.md),
[26](26-playbook-containers-k8s.md), [28](28-learn-networking.md), [23](23-playbook-slow-system.md))
and the free resources in your Ops Ladder.

### Certifications in order

| # | Certification | Format | Stage | Why at this point | Skip or swap when |
|---|---|---|---|---|---|
| 1 | LFCS (Linux Foundation Certified System Administrator) | Performance-based, in a terminal | Fresher → Junior | Proves you can operate Linux under time pressure, which is the whole of L0 and L1 | You already run Linux daily (you do). Take the KodeKloud course for the content and skip the exam fee |
| 2 | Docker: no certificate | — | Junior | No hiring manager filters on a Docker certificate. The skill is proved by the CI → Harbor → Dokploy project | Never. Spend the money on the CKA instead |
| 3 | **CKA** (Certified Kubernetes Administrator) | Performance-based, 2 hours, live clusters | Junior → Mid | The certificate most asked for in on-prem and Kubernetes roles. Hands-on, so it is hard to fake. Troubleshooting is its largest domain (30% in the current curriculum) | Don't swap it. It is your current track |
| 4 | HashiCorp Terraform Associate | Multiple choice | Mid | Short to prepare. Once you know Terraform, every AWS lab becomes code you can apply in the evening and destroy before bed, so cloud study stays cheap | Swap with 5 if your job turns AWS-first |
| 5 | AWS Solutions Architect – Associate, **or** AWS CloudOps Engineer – Associate | Multiple choice | Mid → Senior | Solutions Architect is the AWS keyword recruiters search for. CloudOps (formerly SysOps Administrator) is closer to day-to-day operations and has a verified KodeKloud course | Take only one associate exam. Skip Cloud Practitioner: the associate exam covers it |
| 6 | CKS (Certified Kubernetes Security Specialist) | Performance-based, 2 hours, requires a passed CKA (check the exam page for whether it must still be valid when you book) | Senior | Security becomes your scope at Senior. Its System Hardening part (SSH, open ports, UFW, AppArmor, seccomp) applies directly to your Ubuntu hosts | Skip if Kubernetes is not your platform at that point |
| 7 | Prometheus Certified Associate (PCA), or AWS DevOps Engineer – Professional | Multiple choice | Senior / Lead | Optional. PCA if observability is your area, the AWS professional exam if your platform lives on AWS | Skip both if your projects already show the skill |

**Why this order:** each certificate builds on the one before. Linux is under everything.
Containers are the unit you deploy. Kubernetes runs containers at scale and its exam tests Linux,
networking and troubleshooting under time pressure. Terraform makes cloud work reproducible and
cheap. The cloud certificate then shows breadth. Security and observability certificates come
last because they only make sense once you own a platform.

**Skip these for now:** KCNA and KCSA (multiple-choice exams below the CKA), AWS Cloud
Practitioner (covered by any associate exam), LPIC-1 and RHCSA (unless your servers move to RHEL,
in which case RHCSA replaces LFCS), and the Docker Certified Associate exam itself (the course is
useful, the badge is not).

**The rule from your Ops Ladder:** collect no more certificates until the CKA is done. After
that, have at most one certificate in progress at a time, and pair every certificate with a
project that uses it. One certificate plus a public trail of fixed problems says more than five
badges.

### What changes at each step

| Moving from → to | What you stop doing | What you start doing | The proof people look for |
|---|---|---|---|
| Fresher → Junior | Asking how to do routine tasks | Owning routine tasks end to end, writing them down | Tickets closed and not reopened, runbooks others use |
| Junior → Mid | Escalating every incident that crosses a layer | Walking every layer yourself and naming the broken one with evidence | Incidents you led, notes with captures and log lines |
| Mid → Senior | Fixing the same class of incident again | Designing so it cannot recur, and building what other teams use | Design docs, platforms other teams depend on, juniors you grew |
| Senior → Lead / Staff / SRE | Being the person who fixes everything | Making the organisation able to fix things without you | SLOs, processes, roadmaps, people promoted on your watch |

---

## 2. Fresher · L0 Foundations

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics, Web Server, SSL & TLS Basics ([link](https://kodekloud.com/courses/devops-pre-requisite-course)) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Working with Shell I through Service Management with SYSTEMD ([link](https://kodekloud.com/courses/the-linux-basics-course)) · 3) Note: [27 — Learn Linux](27-learn-linux.md) sections 1–6 and the [README](README.md) triage · 4) Video: KodeKloud *Linux Crash Course for Beginners* ([YouTube](https://www.youtube.com/watch?v=a3ujwK65dgs)) · 5) Practice: [Linux Upskill Challenge](https://linuxupskillchallenge.org/) days 1–10, then the L0 exit test.

**[L0 · Fresher], 0–1 year.** Your first ops, support or DevOps job, or the first year after
switching from development or helpdesk. Nobody expects you to fix production alone. People do
expect you to be careful, to learn fast and to leave a written trail of what you did.

### Good fresher work

- **You finish the task you were given and show it is done.** "Done" comes with evidence: the command output, a link to the merge request, a screenshot of the dashboard.
- **You never change production silently.** Before you run something you don't fully understand, you ask. Before you change a file, you take a backup copy.
- **You read the logs before you restart anything.** A restart destroys the evidence, which is the golden rule in the [README](README.md).
- **Your questions carry context**: what you were trying to do, what you ran, the exact error text, and what you already checked (section 11 has a template).
- **You take notes and reuse them**, so you never ask the same question twice.
- **You learn the map of your environment**: which servers exist, what runs on each, how you reach them (VPN, bastion, SSH config), and where the monitoring and documentation live.
- **Your scripts are small, quoted and ShellCheck-clean**, and they fail loudly instead of carrying on after an error.

### Fresher skills checklist

| Area | Can do alone | With help | Not yet (that's fine) |
|---|---|---|---|
| Linux | Navigate the filesystem, read and change permissions, manage users and groups, `apt install`, `systemctl status`, `journalctl -u UNIT` | Write a systemd unit, edit `/etc/fstab`, extend an LVM volume | Kernel parameters, boot failures, performance tuning |
| Networking | `ip a`, `ip route`, `ping`, `dig`, `curl -I`; explain IP, subnet, gateway, port, DNS | Add a UFW rule, change a netplan file | tcpdump analysis, NAT, routing problems |
| Scripting | Bash with variables, loops, `if`, exit codes, zero ShellCheck warnings | Argument parsing, `trap`, `set -euo pipefail` pitfalls | Python tooling |
| Git | Clone, branch, commit, push, open a merge request, `git revert` | Rebase, resolve conflicts | Rewriting shared history (and you shouldn't) |
| Containers | `docker run`, `ps`, `logs`, `exec`, `pull` | Write a Dockerfile, a Compose file | Docker networking internals |
| Kubernetes | `kubectl get`, `describe`, `logs` in a lab | — | Anything in production |
| Cloud | Launch an EC2 instance in a sandbox and SSH in with a key | Security groups, IAM roles | VPC design |
| IaC | Read an Ansible playbook or Terraform file and explain what it changes | Run an Ansible ad-hoc command in a lab | Write roles or modules |
| CI/CD | Find the failing job in a GitLab pipeline and read its log | Fix a simple job | Design a pipeline |
| Observability | Read a Grafana dashboard; `df`, `free`, `top` | Create a simple alert | PromQL |
| Security | Key-based SSH, `sudo`, least privilege, never commit secrets | UFW, certificate renewal | Hardening baselines |
| Databases | Connect with `psql` or `mysql`, run a `SELECT`, check the service is running | Take a backup | Replication, tuning |
| Troubleshooting | Follow the seven-step triage in the [README](README.md) and collect evidence | Anything beyond a runbook | Leading an incident |
| Communication | Clear ticket updates, questions with context | Writing a runbook | Talking to stakeholders during an incident |

### Fresher incidents

At this stage, "handle alone" means **diagnose and report with evidence**. Fix things yourself
only on non-production servers, or in production when a runbook says exactly what to do.

| Incident | What you do alone | First moves | Open |
|---|---|---|---|
| A user gets `Permission denied (publickey)` | Collect the client-side debug output and check key file permissions | `ssh -vvv USER@HOST`, then on the server `sudo ls -ld /home/USER /home/USER/.ssh /home/USER/.ssh/authorized_keys` | [09](09-ssh-remote-access.md) |
| A non-production disk is at 90% | Find what is large, report it, delete nothing without approval | `df -h`, `df -i`, `sudo du -xh --max-depth=1 /var` | [01](01-storage-disk.md) |
| A test service is down and a runbook exists | Read the logs first, then follow the runbook | `systemctl status UNIT`, `journalctl -u UNIT -n 50 --no-pager` | [07](07-services-systemd.md), [06](06-logs-journal.md) |
| "Is the site up?" | Check the status code and certificate dates | `curl -sI https://HOST/`, `curl -vI https://HOST/` | [18](18-web-http-tls.md) |
| `apt` says the dpkg lock is held | Find who holds it (usually unattended-upgrades) and wait. Never delete the lock file | `sudo lsof /var/lib/dpkg/lock-frontend`, `systemctl status apt-daily.service apt-daily-upgrade.service` (the `unattended-upgrades` unit is only the shutdown hook and always looks active) | [11](11-packages.md) |
| A cron job did not run | Check whether cron started it and what it printed | `journalctl -u cron --since today` (`crond` on RHEL), `sudo crontab -l -u USER` | [07](07-services-systemd.md) |

### Fresher portfolio

Pick three of these. Each lives in its own folder of one Git repository, with a README that says
what it is, how to run it, and what you learned.

**1. Hardened Ubuntu VM baseline [L0 · Fresher].** Build an Ubuntu 24.04 VM with a sudo user,
key-only SSH, UFW allowing only SSH, unattended security upgrades and correct time sync. Write
down every command and why. *Done when* you can rebuild it from your README in 30 minutes, which
is your L0 exit test. Modules: [09](09-ssh-remote-access.md), [10](10-users-permissions-security.md),
[11](11-packages.md), [12](12-time-ntp.md).

**2. `sysreport.sh` with a systemd timer [L0 · Fresher].** A script that reports disk use, inode
use, memory and failed systemd units, with zero ShellCheck warnings, run daily by a systemd timer
that writes to the journal. *Done when* it runs on a fresh VM with no edits and its output shows
up under `journalctl -u sysreport`. Modules: [27](27-learn-linux.md), [07](07-services-systemd.md).

**3. Your notes repository [L0 · Fresher].** A Git repo of everything you learn: one file per
topic, every command with one line on when to use it. Use it to practise Git: branches, merge
requests to yourself, and a deliberate bad commit that you then `git revert`. This repo later
becomes your public runbooks repo (section 10).

**4. A static site behind Apache with HTTPS [L0 · Fresher].** Two name-based virtual hosts on
one Apache server, each with its own log files and a certificate (self-signed is fine in a lab).
Save the output of `sudo apache2ctl -S` and explain every line. This is the setup from your own
Apache → Dokploy incident in miniature. Modules: [18](18-web-http-tls.md),
[29](29-learn-webservers-proxies.md), [21](21-case-apache-443-dokploy.md).

**5. Your first container [L0 · Fresher].** Write a Dockerfile for a tiny Python HTTP app, run it
with a published port, read its logs, `exec` into it and explain what `docker ps` shows. Module:
[30](30-learn-docker.md).

A starting point for project 2 that already follows good habits:

```bash
#!/usr/bin/env bash
# sysreport.sh - daily health report: disk, inodes, memory, failed units.
# Exit code: 0 = all good, 1 = at least one warning (so a timer or monitor can alert on it).
set -euo pipefail

warn=0
threshold=85

echo "== disk (warn at ${threshold}%) =="
while read -r use mount; do
  pct=${use%\%}
  if (( pct >= threshold )); then echo "WARN ${mount} at ${use}"; warn=1; fi
done < <(df --output=pcent,target -x tmpfs -x devtmpfs -x overlay -x squashfs | tail -n +2)

echo "== inodes =="
df -x tmpfs -x devtmpfs -x overlay -x squashfs --output=ipcent,target | tail -n +2

echo "== memory =="
free -h

echo "== failed units =="
if systemctl --failed --no-legend | grep -q .; then
  systemctl --failed --no-legend
  warn=1
else
  echo "none"
fi

exit "$warn"
```

```
$ ./sysreport.sh; echo "exit=$?"
== disk (warn at 85%) ==
WARN /var at 91%
== inodes ==
  12% /
  34% /var
== memory ==
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       1.1Gi       1.2Gi        12Mi       1.5Gi       2.4Gi
Swap:          2.0Gi          0B       2.0Gi
== failed units ==
none
exit=1
```

**Why it is written this way:** `set -euo pipefail` stops the script at the first failing
command instead of printing a misleading report. The exit code makes it usable by a timer or a
monitor. Excluding `tmpfs` and `overlay` avoids false alarms from RAM-backed mounts and Docker's
layered filesystems, and excluding `squashfs` skips snap packages (certbot, lxd), whose read-only
loop mounts always show 100%.

**Next:** wrap it in a `.service` plus `.timer` pair, as shown in [07](07-services-systemd.md),
and check it with `systemctl list-timers`.

### Fresher 90-day plan

| Days | Focus | Handbook | KodeKloud | Output you keep |
|---|---|---|---|---|
| 1–15 | Shell, files, permissions, users | [27](27-learn-linux.md), [10](10-users-permissions-security.md), [19](19-cheatsheet.md) | *Learning Linux Basics Course & Labs*: Working with Shell I, Linux Core Concepts, Security and File Permissions | Notes repo with your first 20 commands, each explained |
| 16–30 | Packages, processes, services, logs | [11](11-packages.md), [05](05-processes.md), [07](07-services-systemd.md), [06](06-logs-journal.md) | *Learning Linux Basics*: Package Management, Service Management with SYSTEMD | `sysreport.sh` version 1 |
| 31–45 | Networking, DNS, ports, SSH, web servers | [28](28-learn-networking.md) sections 1–3, [02](02-network.md), [08](08-dns.md), [09](09-ssh-remote-access.md) | *DevOps Pre-Requisite Course*: Networking Basics, DNS, Web Server (Apache Web Server, IPs and Ports), SSL & TLS Basics | Apache with two HTTPS vhosts (project 4) |
| 46–60 | Bash and Git properly | [27](27-learn-linux.md) scripting part | *Shell Scripts for Beginners* (Exit Codes, ShellCheck), *GIT for Beginners* (Resetting and Reverting, reflog) | ShellCheck-clean `sysreport.sh` with a timer, a practised `git revert` |
| 61–75 | First steps with Docker | [30](30-learn-docker.md) sections 1–2, [14](14-docker-containers.md) | *Docker Training Course for the Absolute Beginner*: Docker Run Commands, Docker Images | Containerised Python app (project 5) |
| 76–90 | Consolidate and test yourself | [README](README.md) triage, [16](16-aws-cloud.md) section 1 | *Crash Course: AWS Basics* (free), first attempt at *Linux Challenges* (free) | L0 exit test passed in under 30 minutes, Linux Upskill Challenge days 1–10 done |

Free resources from your Ops Ladder for this stage:
[Linux Journey](https://labex.io/linuxjourney),
[Linux Upskill Challenge](https://linuxupskillchallenge.org/),
[Pro Git, chapters 1–3](https://git-scm.com/book/en/v2),
the [Bash Guide](https://mywiki.wooledge.org/BashGuide) and
[ShellCheck](https://www.shellcheck.net/).

### Ready for Junior

You are ready when all of these are true:

- You passed the L0 exit test twice, on different days, without notes.
- Routine tickets assigned to you come back closed, not reopened.
- You read the logs before you ask, and your questions include the exact error text.
- You can say what a command will do before you run it, including what could go wrong.
- Your notes repo has at least 30 entries and you actually search it.
- Someone more senior has started giving you tasks without step-by-step instructions.

### Fresher mistakes

- **Running internet commands as root without reading them.** `curl ... | sudo bash` executes whatever the server sends. Download to a file, read it, then run it.
- **`chmod -R 777` to make an error go away.** It hides the real problem (wrong owner, wrong user) and opens the files to everyone. Find which user needs which access; [10](10-users-permissions-security.md) shows how.
- **Restarting before reading logs.** The restart works, the cause is lost, and the problem comes back at 3 a.m.
- **Editing config without a backup.** Make `sudo cp -a FILE FILE.bak.$(date +%F)` a reflex, or better, keep the config in Git.
- **Hiding a mistake.** A mistake reported in two minutes is a small story. The same mistake found by someone else an hour later is a trust problem. Section 11 shows how to report one.
- **Tutorial hell.** Watching courses without doing the labs and breaking things. Every hour of video needs at least an hour at a terminal.
- **Pasting AI-generated commands you don't understand.** Check each command against its man page or the handbook before you run it, and never paste secrets, hostnames or customer data into an AI tool.
- **Collecting badges.** KCNA or Cloud Practitioner before you can pass the L0 exit test proves very little.

---

## 3. Junior · L1 Operator

> 📚 **Study path:** 1) Note: [22 — Ports inventory](22-playbook-ports-inventory.md) section 4 (you already do most of this, so refresh first) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment, then Networking ([link](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: *Linux for Beginners: systemd start/stop services & journalctl* by KodeKloud instructor Sanjeev Thiyagarajan ([YouTube](https://www.youtube.com/watch?v=jZfNVROoF74)) · 4) Practice: *Linux Challenges* (free, [link](https://kodekloud.com/courses/linux-challenges)) and five [SadServers](https://sadservers.com/scenarios) easy scenarios, then the L1 exit test.

**[L1 · Junior], 1–2 years.** You run services day to day. You know where things are, you can
follow and write runbooks, and you can go from a port number to the process, unit, config and
logs in minutes, which is the Ops Ladder L1 goal and the skill you built during the Apache
investigation.

### Good junior work

- **You own routine operations end to end**: patching, certificate renewals, user and key management, disk clean-ups, deploys through existing pipelines.
- **You find the owner of any port in minutes** and you know which unit, config file and log belong to it ([22](22-playbook-ports-inventory.md)).
- **You write a runbook for every task you do twice**, and other people use your runbooks.
- **You escalate early and with evidence.** You timebox (30 minutes stuck, or immediately when users are affected) and your escalation says what you checked and what you saw.
- **You automate the second time.** If a fix needs five commands, the second occurrence gets a script or an Ansible task.
- **You are a useful secondary on-call**: you acknowledge fast, collect evidence, and hand over a clean summary.

### Junior skills checklist

| Area | Can do alone | With help | Not yet |
|---|---|---|---|
| Linux | systemd units, drop-ins and timers; journald filters; disk, inode and deleted-open-file problems; logrotate; extending LVM | Kernel parameters, boot failures, OOM analysis | Performance profiling |
| Networking | `ss -ltnp`, port → process → unit, UFW, static netplan config, `resolvectl`, `curl -v`, refused vs timed out | tcpdump, Docker NAT and firewall interaction | Designing networks |
| Scripting | Robust bash (`set -euo pipefail`, `trap`, logging), small Python scripts that call an API | Testing scripts, packaging tools | Building internal tools for others |
| Git | Rebase on main, resolve conflicts, respond to review comments | `git bisect` | Choosing a branching strategy for a team |
| Containers | Multi-stage Dockerfiles, Compose stacks, volumes, log rotation, `docker system df` and safe pruning | Docker DNS and networking problems, Swarm services | Runtime internals |
| Kubernetes | Deployments, Services, ConfigMaps in a homelab; `kubectl describe` and `logs --previous` | Ingress, PersistentVolumes | Cluster upgrades in production |
| Cloud | EC2, EBS, security groups, instance IAM roles, S3 basics, CLI profiles | VPC routing, NAT gateways | Multi-account setups |
| IaC | Ansible playbooks and roles for packages, users and config; `terraform plan` and `apply` in a sandbox | Terraform state, `import` | Module design |
| CI/CD | A build-and-push pipeline to Harbor, masked and protected variables | Runners, caching, environments | Pipeline templates for many teams |
| Observability | node_exporter, Prometheus, Grafana dashboards, a disk alert | PromQL `rate()`, alert routing | SLOs |
| Security | Key-only SSH, UFW, certificate renewal, adding a private CA to the trust store | CIS-style hardening, secrets management | Threat modelling |
| Databases | `pg_dump` and `mysqldump` backups, restore to a test server, check connections | Users and grants, slow query logs | Replication and failover |
| Troubleshooting | The incidents in the next table, alone | "Site is down" across several layers | Performance mysteries |
| Communication | Five-line incident notes, runbooks | Change requests | Stakeholder updates during a major incident |

### Junior incidents

| Incident | First moves | Open |
|---|---|---|
| `bind: Address already in use` | `sudo ss -ltnp 'sport = :PORT'`, `sudo lsof -nP -iTCP:PORT -sTCP:LISTEN`, `systemctl list-sockets` | [22](22-playbook-ports-inventory.md), [21](21-case-apache-443-dokploy.md) |
| `No space left on device` (including inodes and deleted files still held open) | `df -h`, `df -i`, `sudo lsof -nP +L1` | [01](01-storage-disk.md), [23](23-playbook-slow-system.md) |
| Docker filled the disk | `docker system df`, `sudo du -xh --max-depth=1 /var/lib/docker` | [26](26-playbook-containers-k8s.md) section 5, [14](14-docker-containers.md) |
| A service won't start or keeps restarting (`start request repeated too quickly`) | `systemctl status UNIT -l --no-pager`, `journalctl -u UNIT -b -n 100 --no-pager`, `systemd-analyze verify /etc/systemd/system/UNIT.service` | [07](07-services-systemd.md) |
| `Permission denied (publickey)` | `ssh -vvv USER@HOST`, `sudo journalctl -u ssh -n 50 --no-pager` (`sshd` on RHEL) | [09](09-ssh-remote-access.md) |
| A container exits immediately or restart-loops | `docker ps -a`, `docker logs --tail 50 CONTAINER`, exit codes 126, 127, 137 | [26](26-playbook-containers-k8s.md) section 2 |
| Works on localhost, not from other machines | `sudo ss -ltnp` (bound to 127.0.0.1?), `sudo ufw status verbose` | [22](22-playbook-ports-inventory.md), [02](02-network.md) |
| Certificate expired, or "not yet valid" on a certificate you know is fine | `openssl s_client -connect HOST:443 -servername HOST`, `timedatectl` | [18](18-web-http-tls.md), [12](12-time-ntp.md) |
| "The server is slow" | Run the first 60 seconds of the checklist and hand over the output | [23](23-playbook-slow-system.md), [03](03-cpu-performance.md) |

**Why these:** they are the most common single-layer failures on Ubuntu servers. A junior who
handles them alone frees the rest of the team for the multi-layer incidents.

### Junior portfolio

**1. A supervised service [L1 · Junior].** A systemd unit for a small Python HTTP server with
`Restart=on-failure`, a dedicated user and an environment file. Kill it with `kill -9`, find the
restart in the journal, and add the evidence to the README. This is an Ops Ladder L1 drill.

**2. Ports inventory script [L1 · Junior].** A script that, for every listening TCP port, prints
the process, the systemd unit that owns it, its main config file and the command that shows its
logs. Run it on a VM with Apache, a Node app and Docker. It is the L1 exit test as a tool, and the
first move of [21](21-case-apache-443-dokploy.md). Module: [22](22-playbook-ports-inventory.md).

**3. A Compose stack you can restore [L1 · Junior].** A reverse proxy (Nginx or Traefik), an app
and PostgreSQL 16 with health checks, log rotation, a nightly `pg_dump` and a **tested restore**
into a fresh container. Modules: [30](30-learn-docker.md), [38](38-learn-databases-ops.md).

**4. An Ansible playbook for a fresh VM [L1 · Junior].** Users and keys, SSH hardening, UFW,
Docker with your `/etc/docker/daemon.json` (internal DNS servers and log rotation). Run it twice:
the second run must report no changes. This is an Ops Ladder L3 drill, and starting it now gives
you a head start. Module: [33](33-learn-cicd-iac-sre.md).

**5. Monitoring, first version [L1 · Junior].** node_exporter, Prometheus and Grafana on the
homelab, with alerts for disk above 85% and for failed systemd units (turn on node_exporter's
systemd collector). Module: [32](32-learn-performance-observability.md).

The `daemon.json` for project 4, as an Ansible template would render it:

```
{
  "dns": ["192.0.2.53", "192.0.2.54"],
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
```

**Why these two settings:** without `dns`, containers inherit the host's upstream resolvers
(Docker reads `/run/systemd/resolve/resolv.conf` when `/etc/resolv.conf` only lists
127.0.0.53). When Docker finds no usable upstream, for example because the host resolves through
a local dnsmasq or unbound on 127.0.0.1, it falls back to 8.8.8.8 and 8.8.4.4, which on-prem
firewalls usually block. Pinning the internal resolvers removes both surprises. Without
`log-opts`, the default json-file driver never rotates and container logs fill the disk. Both
are cases in your Ops Ladder library. New settings apply to containers created after the
Docker restart, not to running ones.

### Junior 90-day plan

| Weeks | Focus | Handbook | KodeKloud | Output you keep |
|---|---|---|---|---|
| 1–2 | Ports, processes, services, logs | [22](22-playbook-ports-inventory.md), [05](05-processes.md), [06](06-logs-journal.md), [07](07-services-systemd.md) | *LFCS prep*: Operations Deployment (Create systemd Services, Diagnose and Manage Processes, Locate and Analyze System Log Files) | L1 exit test under 5 minutes; portfolio project 1 |
| 3–4 | Networking on the host | [02](02-network.md), [08](08-dns.md), [28](28-learn-networking.md) TCP, NAT and firewall sections | *LFCS prep*: Networking (Start/Stop/Check Network Services, Configure Packet Filtering, Port Redirection and NAT, Reverse Proxies) | Ports inventory script (project 2) |
| 5–6 | Disks, memory, slow hosts | [01](01-storage-disk.md), [04](04-memory.md), [23](23-playbook-slow-system.md) | *LFCS prep*: Storage (Monitor Storage Performance, LVM); *Linux Challenges* | Fill `/var` on a test VM and find the failing service with journalctl, df and du only |
| 7–8 | Docker for operators | [30](30-learn-docker.md), [26](26-playbook-containers-k8s.md) sections 2–3 | *Docker Certified Associate*: Docker Engine (Publishing Ports, Restart Policies, Troubleshooting Docker Daemon, Logging Driver) | Compose stack with tested restore (project 3) |
| 9–10 | Automation | [33](33-learn-cicd-iac-sre.md) Ansible part | *Ansible Basics Course* (Playbooks, Handlers, Roles, Templates); *Advanced Bash Scripting* (Streams, Good Practices, awk, sed) | Ansible playbook (project 4) |
| 11–13 | Proxies and monitoring | [29](29-learn-webservers-proxies.md), [21](21-case-apache-443-dokploy.md) phases 1–2, [32](32-learn-performance-observability.md) | *Nginx For Beginners* (Reverse Proxy, Monitoring & Troubleshooting) | Monitoring version 1 (project 5); five SadServers easy scenarios inside their time limits |

### Ready for Mid

- You pass the L1 exit test in under five minutes, every time.
- You have handled every incident in the Junior table at least once, alone, and have the notes to show it.
- People ask you how a service is set up, because your runbooks are the best description of it.
- You have started to see patterns: "this is the third disk-full on hosts without log rotation".
- You reach for `ss`, `journalctl` and `curl -v` before you form an opinion.
- You have started on multi-layer problems, even if you still need help to finish them.

### Junior mistakes

- **`kill -9` on whatever holds the port.** If a systemd unit owns the process, it starts again, or you take down a service people use. Find the owner and unit first ([22](22-playbook-ports-inventory.md)), then stop it through systemd, after agreement.
- **`docker system prune -a --volumes` to free space.** It deletes unused volumes (on Docker Engine 23.0 and later only anonymous ones, such as the volume the postgres image creates when you forget to name one; on older releases named ones too), and volumes hold databases. Safer first moves: `docker system df` to see what is using space, then `docker builder prune` and `docker image prune`. Remove volumes only one by one, by name, after checking what they contain.
- **Changing production without a record.** Even a standard change gets a ticket or a line in the change log, so the next person can connect "it broke at 14:05" to "I reloaded Apache at 14:04".
- **Fixing the symptom forever.** A cron job that restarts a leaking service every night is a workaround. Keep it if you must, but open a ticket for the root cause.
- **Backups that were never restored.** A backup you have not restored is a hope, not a backup.
- **Escalating too late, or too early.** Use a timebox and escalate with evidence either way.
- **Treating course labs as experience.** Labs teach you to build things. Your job is fixing them, so break your homelab on purpose every week.

---

## 4. Mid-level · L2 Troubleshooter

> 📚 **Study path:** 1) Note: [25 — Site down](25-playbook-site-down.md) sections 1–2 and [21 — Apache 443 and Dokploy](21-case-apache-443-dokploy.md) (your own method, so refresh it first) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts, kubeadm, Networking, Troubleshooting ([link](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)), with *Demystifying DNS* — DNS as a System, Troubleshooting DNS ([link](https://kodekloud.com/courses/demystifying-dns)) · 3) Video: KodeKloud *How Docker Networking Actually Works* ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Practice: the "break DNS three ways" drill, the Traefik 502 drill, then the L2 exit test.

**[L2 · Mid], 2–4 years.** You own a system end to end: host, firewall, DNS, TLS, reverse proxy,
app, pipeline. When it breaks, you walk the layers and name the broken one with evidence instead
of guessing. Your Ops Ladder marks L2 as "start here", because the gaps in your notes (packet
captures, resolver logs, container DNS, Docker and UFW) live at this level.

### Good mid-level work

- **You diagnose across layers with evidence.** Every conclusion comes with a packet capture, a log line or `curl -v` output that proves it ([25](25-playbook-site-down.md)).
- **You lead small incidents** as primary on-call: you stabilise first (roll back the change), then investigate, and you post updates without being asked.
- **You plan changes with a written rollback** and you test that rollback before the window. Your Apache → Dokploy move is exactly this kind of work.
- **You turn repeat incidents into root-cause work**: a ticket, a fix, and a postmortem for anything users noticed.
- **You review other people's work** and answer juniors' questions by showing the method, not just the answer.
- **You know why each tool works**, so when the usual command fails you know which one to try next.

### Mid-level skills checklist

| Area | Can do alone | With help | Not yet |
|---|---|---|---|
| Linux | The 60-second performance checklist and the USE method, `strace`, `lsof`, OOM analysis, boot problems from the console | Kernel tuning for a specific workload | Kernel debugging |
| Networking | The layered walk (DNS, route, firewall, TLS, proxy, app), tcpdump, resolver debug logs, Docker NAT and `DOCKER-USER`, MTU problems | Routing between sites, VPN design | Network architecture for a whole company |
| Scripting | Python tools with error handling, arguments and tests; reading Go | Designing a shared library | — |
| Git | `git bisect`, protected branches, a sensible branching model for one repo | Monorepo or GitOps repository design | — |
| Containers | Docker networking and DNS, Traefik routing, Dokploy, Swarm services and overlays, Harbor with a private CA | Rootless containers, seccomp profiles | Container runtime internals |
| Kubernetes | CKA level: build with kubeadm, upgrade, back up and restore etcd, debug nodes, pods, Services and DNS | CNI internals, operators | Multi-cluster platforms |
| Cloud | VPC with public and private subnets, ALB, Auto Scaling, RDS, IAM policies, CloudWatch alarms | AWS Organizations and SCPs, cost optimisation | Multi-region design |
| IaC | Terraform modules, remote state with locking, Ansible roles | State surgery (`terraform state mv`, `import`) | Organisation-wide IaC standards |
| CI/CD | Multi-stage pipelines: test, scan, build, push, deploy, verify, roll back | Runner fleets, autoscaling runners | Platform-wide templates |
| Observability | PromQL, alert rules, log aggregation, a dashboard per service (USE and RED) | SLOs and burn-rate alerts | Organisation-wide strategy |
| Security | Image scanning, secrets out of Git, sane TLS settings, least-privilege IAM | CIS benchmark roll-out, audits | Running a security programme |
| Databases | Tested restores, replication status, connection exhaustion, migrations inside deploys | Failover, major version upgrades | Internals and tuning |
| Troubleshooting | Every incident in the next table, alone | Latency across many services | — |
| Communication | Change requests, postmortems, status updates | Negotiating across teams | Executive briefings |

### Mid-level incidents

| Incident | First moves | Open |
|---|---|---|
| "The site is down" | Walk the layers in order and stop at the first one that fails: `getent ahosts HOST`, `ip route get IP`, `nc -vz HOST 443`, `openssl s_client`, `curl -v --resolve` | [25](25-playbook-site-down.md) |
| Port conflict during a migration (Apache vs Traefik, the Dokploy installer refuses to run) | Inventory listeners and vhosts, prove which sites are used, move Apache to an internal port, test, cut over | [21](21-case-apache-443-dokploy.md), [22](22-playbook-ports-inventory.md) |
| Traefik or Dokploy returns 502 or 404 | Traefik logs, container labels, the port the app really listens on, the network it is attached to | [25](25-playbook-site-down.md) section 3, [26](26-playbook-containers-k8s.md), [29](29-learn-webservers-proxies.md) |
| Resolves on the host, fails inside a container | `docker exec CONTAINER cat /etc/resolv.conf`, netshoot in the container's network namespace, `sudo tcpdump -ni any port 53` | [26](26-playbook-containers-k8s.md) section 4, [08](08-dns.md) |
| `x509: certificate signed by unknown authority` pulling from Harbor | `openssl s_client -connect HARBOR:443 -showcerts`, then `/etc/docker/certs.d/HARBOR/` and `/etc/containerd/certs.d/HARBOR/` | [18](18-web-http-tls.md), [26](26-playbook-containers-k8s.md) |
| High load average with idle CPU, OOM kills | `vmstat 1`, `iostat -xz 1`, D-state processes, `journalctl -k -b` | [23](23-playbook-slow-system.md), [03](03-cpu-performance.md), [04](04-memory.md) |
| Slow transfers on a fast link | Latency, then raw throughput with iperf3, then this host's link, TCP and MTU | [24](24-playbook-network-speed.md) |
| `CrashLoopBackOff`, `ImagePullBackOff`, `Pending`, node `NotReady` | `kubectl describe pod POD`, `kubectl logs POD --previous`, events, `sudo crictl pull IMAGE` on the node, `sudo journalctl -u kubelet` | [26](26-playbook-containers-k8s.md), [31](31-learn-kubernetes.md), [15](15-kubernetes.md) |
| An EC2 instance is unreachable, or a private subnet has no internet | Security group, NACL (both directions), route table, NAT gateway, status checks | [16](16-aws-cloud.md), [36](36-learn-cloud-aws.md) |
| `too many connections` from PostgreSQL or MySQL | Who holds the connections, pool sizes, leaks after a deploy | [38](38-learn-databases-ops.md) |
| Everything broke right after a change | Roll back first, diagnose second | [35](35-deployment-patterns.md), [33](33-learn-cicd-iac-sre.md) |

**Why these:** every one of them crosses at least two layers. Being able to name the broken layer
quickly, with proof, is the skill that makes people call you first.

### Mid-level portfolio

**1. GitLab CI → Harbor → Dokploy pipeline [L2 · Mid → L3 · Senior].** This is your Ops Ladder
L3 exit test and the strongest single project you can show. It should have these stages:

| Stage | What the job does | Why it matters |
|---|---|---|
| test | Unit tests, ShellCheck, a Dockerfile linter | Fail in seconds, before anything is built |
| build | Build the image and tag it with the commit SHA (`$CI_COMMIT_SHORT_SHA`) | Every running container traces back to one commit |
| scan | Scan the image (Harbor can scan on push with Trivy) and fail on critical findings | Supply-chain hygiene, a CKS topic later |
| push | Push to `harbor.example.com/PROJECT/APP:SHA` with a Harbor robot account | Least privilege: the pipeline can push to one project only |
| deploy | Tell Dokploy to deploy that exact tag (webhook or API, see the [Dokploy docs](https://docs.dokploy.com/docs/core)) | Deploys are repeatable and logged |
| verify | `curl -fsS https://app.example.com/healthz` from outside | A deploy is not done until it is proven |
| rollback | A manual job that redeploys the previous SHA | Rehearsed, so it works during an incident |

The private-CA trap: the job that runs `docker push` **and** the Docker daemon it talks to (for
example a `docker:dind` service) both need Harbor's CA. Modules: [33](33-learn-cicd-iac-sre.md),
[35](35-deployment-patterns.md), [30](30-learn-docker.md), [18](18-web-http-tls.md).

**2. A kubeadm homelab cluster with a break-and-fix log [L2 · Mid].** One control plane and two
workers on Ubuntu 24.04 with containerd, a CNI, an ingress controller and metrics-server, pulling
images from Harbor through `/etc/containerd/certs.d/HARBOR/hosts.toml`. Keep a log of every fault
you inject and how you found it: CoreDNS loop, a stopped kubelet, a wrong image tag, a
NetworkPolicy that blocks DNS, an expired certificate. This is your CKA preparation and your proof
in one. Module: [31](31-learn-kubernetes.md).

**3. The Apache → Dokploy case, written up [L2 · Mid].** The change request, the inventory, the
rollback plan, what went wrong (the DNS detour included), and a postmortem in the SRE book's
format. Sanitise it (section 10). It becomes the STAR story in section 8. Module:
[21](21-case-apache-443-dokploy.md).

**4. A Terraform repository for AWS [L2 · Mid].** A VPC with public and private subnets, an ALB
in front of an Auto Scaling group, remote state in S3 with locking, and `terraform plan` running
on every merge request. Destroy it every evening so it costs almost nothing. Modules:
[36](36-learn-cloud-aws.md), [33](33-learn-cicd-iac-sre.md).

**5. A public runbooks and postmortems repository [L2 · Mid].** Ten sanitised runbooks from real
incidents and three postmortems. Section 10 describes the layout.

### Mid-level 90-day plan

This plan puts the CKA in the middle because it is your current track. Until the exam, the CKA
blocks come first and everything else runs on the 30-minute morning rep.

| Weeks | Focus | Handbook | KodeKloud | Output you keep |
|---|---|---|---|---|
| 1–2 | DNS, TLS, HTTP and looking at packets | [28](28-learn-networking.md) DNS, HTTP, TLS and capture sections, [08](08-dns.md), [18](18-web-http-tls.md) | *Demystifying DNS*: DNS as a System, Troubleshooting DNS | Break DNS three ways on a test VM (bad netplan upstream, systemd-resolved stopped, wrong `/etc/hosts`), diagnose each with tcpdump, getent and resolvectl |
| 3–4 | The site-down walk and proxies | [25](25-playbook-site-down.md), [29](29-learn-webservers-proxies.md), [21](21-case-apache-443-dokploy.md), [26](26-playbook-containers-k8s.md) sections 3–4 | *Kubernetes Networking Deep Dive*: Kubernetes Ingress module (Traefik Overview, Traefik Installation) | Traefik 502 drill fixed from Traefik's logs alone; L2 exit test in 15 minutes |
| 5–10 | CKA course | [31](31-learn-kubernetes.md), [15](15-kubernetes.md), [26](26-playbook-containers-k8s.md) | *Kubernetes for the Absolute Beginners* (fast), then *CKA* in this order: Core Concepts, kubeadm install, Networking, Troubleshooting, Cluster Maintenance, Security, the rest; *Kubernetes Troubleshooting for Application Developers* | Homelab cluster with a break-and-fix log (project 2) |
| 11–12 | CKA exam | [31](31-learn-kubernetes.md) exam strategy area | *CKA* Lightning Labs and mock exams, *Ultimate Certified Kubernetes Administrator (CKA) Mock Exam Series*, then the killer.sh sessions | CKA passed |
| 13 | Start the L3 exit test | [33](33-learn-cicd-iac-sre.md), [35](35-deployment-patterns.md) | *GitLab CI/CD*: Continuous Integration with GitLab, Self-Managed Runners | Pipeline skeleton pushing SHA-tagged images to Harbor (project 1) |

Free resources from your Ops Ladder for this stage:
[Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/),
[Spying on your programs with strace](https://wizardzines.com/zines/strace/),
[Mess With DNS](https://messwithdns.net/),
[everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html),
[badssl.com](https://badssl.com/),
[Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/)
and [learnkube: Troubleshooting deployments](https://learnkube.com/troubleshooting-deployments).

### Ready for Senior

- You pass the L2 exit test in 15 minutes and can teach the walk to a junior.
- You have led several incidents and written postmortems whose action items actually got done.
- You have run at least one migration with a change request and a tested rollback, and it is written up.
- You think about prevention without being asked: "how do we make sure this never happens again?"
- Engineers bring you their designs to review before they build.
- You hold the CKA, and the L3 exit test project (GitLab CI → Harbor → Dokploy with rollback) is done.
- You can explain a technical trade-off in terms of cost, risk and time, for example why Dokploy is the right size for twelve apps and when Kubernetes would be.

### Mid-level mistakes

- **Changing several things at once.** When it starts working you don't know which change fixed it, and the others stay in place as silent risk. Change one thing, test, then the next (*Debugging: The 9 Indispensable Rules* calls this "change one thing at a time").
- **Hero mode.** Fixing everything yourself at 2 a.m. without telling anyone feels good and teaches the organisation nothing. Post updates, write it down, and hand over.
- **Starting a change without a written rollback.** If you can't write the rollback, you don't understand the change yet.
- **Kubernetes for everything.** For a handful of apps on two servers, Dokploy or Compose may be the better answer. Choose by operational cost, not by what looks good on a CV.
- **Skipping the postmortem because "it was small".** Small incidents are cheap lessons. The big one usually started as a small one that nobody wrote down.
- **Leaving temporary doors open after a migration.** Test ports, old listener ports and debug dashboards stay reachable for months. Close them and verify from outside the host, remembering that UFW does not filter published Docker ports.
- **Ignoring cloud and IaC because your job is on-prem.** Senior roles expect both. Terraform and one AWS associate exam keep your options open.
- **Being right rudely.** A correct review comment written as an attack still loses the argument. Section 11 covers this.

---

## 5. Senior · L3 Platform

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals, PromQL, Alerting ([link](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — System Hardening, Supply Chain Security ([link](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 3) Note: [35 — Deployment patterns](35-deployment-patterns.md) and [39 — Senior architecture](39-learn-senior-architecture.md) · 4) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0)) · 5) Practice: the L3 exit test, then a DR drill with a stopwatch (Senior portfolio project 3).

**[L3 · Senior], 4–7 years.** You build and run the platform other people deploy to: CI
templates, registries, clusters, base images, ingress, observability. You design so a class of
failure cannot happen again, and you make the people around you better. Seniority shows in
judgement and scope, not in knowing more commands.

### Good senior work

- **You prevent classes of failure.** The Mid-level fix for a port clash is moving Apache. The Senior fix is a rule that one ingress owns 80 and 443 on every host, enforced by config management and checked before every install.
- **You build things other teams use without needing you**: pipeline templates, base images, Harbor projects with robot accounts, cluster standards, with documentation good enough that people don't have to ask.
- **You write decisions down.** Design docs and architecture decision records (ADRs) state the options, the trade-offs and why you chose one.
- **You lead medium incidents and run blameless postmortems** that end in systemic fixes, not "be more careful".
- **You multiply others**: reviews that teach, pairing, mentoring a junior through their exit tests.
- **You balance risk, cost and speed**, and you can say no with reasons and an alternative.
- **You know what the business needs from each system**: which outage costs money, which costs reputation, which nobody would notice.

### Senior skills checklist

| Area | Can do alone | With help | Not yet |
|---|---|---|---|
| Linux | Fleet standards: base images, patch cadence, hardening, performance tuning backed by measurements | Kernel bugs, unusual hardware | — |
| Networking | Platform network design: subnets and VLANs, ingress architecture, internal DNS, overlay MTU, load balancing, VPNs | Large-scale routing, with the network team | — |
| Scripting | Tools in Python or Go, with tests, that other teams use | Writing Kubernetes operators | — |
| Git | Release and branching strategy, GitOps repository layout, approval rules | — | — |
| Containers | Base image standards, image signing, registry design (projects, robot accounts, replication, retention) | Custom runtime security profiles | — |
| Kubernetes | Cluster design (HA control plane, etcd, CNI choice, ingress), upgrades, multi-tenancy, RBAC, NetworkPolicies, PodDisruptionBudgets | Multi-cluster, service mesh | — |
| Cloud | Multi-AZ architecture, VPC design, IAM strategy, cost awareness | Multi-account organisations, landing zones | Multi-region active-active |
| IaC | Module design, state layout, drift detection, policy checks in CI | — | — |
| CI/CD | Templates for many teams, promotion by image digest, progressive delivery, supply-chain controls | — | — |
| Observability | SLOs, symptom-based alerts, dashboards per service, log pipeline, tracing basics | Organisation-wide observability strategy | — |
| Security | Hardening baselines (for example from the [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)), secrets management, scanning gates, audit logging | Compliance audits, security programme design | — |
| Databases | HA design, backups with point-in-time recovery, major upgrades, capacity planning | Deep engine tuning | — |
| Troubleshooting | Any incident; coordinating investigation across teams; coaching others while it happens | — | — |
| Communication | Design docs, ADRs, incident command for medium incidents, cross-team negotiation | Executive communication | — |

### Senior incidents

At Senior, the question is no longer "can you fix it?" but "will it happen again?". Each row
shows the Mid-level fix and the Senior fix for the same class of incident.

| Incident class | Mid-level fix | Senior fix: make it unable to recur | Modules |
|---|---|---|---|
| Two programs want 80/443 (Apache vs Traefik) | Move Apache to 81/444 or an internal port | One ingress owns 80/443 on every host; a port registry in Git; config management controls `Listen` lines; a pre-install check in the pipeline | [21](21-case-apache-443-dokploy.md), [22](22-playbook-ports-inventory.md), [39](39-learn-senior-architecture.md) |
| Disk filled by container logs | Prune, add log rotation on that host | `daemon.json` log options rolled out by Ansible to every host; disk alerts that predict the fill time | [01](01-storage-disk.md), [32](32-learn-performance-observability.md) |
| Expired certificate | Renew it | ACME automation everywhere it is possible; expiry probes that alert weeks ahead for the rest | [18](18-web-http-tls.md), [32](32-learn-performance-observability.md) |
| `x509: unknown authority` from Harbor | Copy `ca.crt` to the failing host | An Ansible role that installs the CA in the OS trust store, Docker's `certs.d` and containerd's `certs.d`; CI images built with the CA | [37](37-learn-security-devsecops.md), [30](30-learn-docker.md) |
| Bad deploy took the site down | Manual rollback | Health-gated progressive deploys, automatic rollback, deploys by image digest | [35](35-deployment-patterns.md) |
| Containers can't resolve internal names | Add `dns` to one host's `daemon.json` | Resolver standard for every host; a probe that resolves from inside a container and alerts | [08](08-dns.md), [28](28-learn-networking.md) |
| A node failure took an app down | Fix the node | PodDisruptionBudgets, anti-affinity, N+1 capacity, tested etcd restores | [31](31-learn-kubernetes.md), [39](39-learn-senior-architecture.md) |
| A security group change exposed a port | Revert the rule | Changes only through IaC, with policy checks on every merge request | [36](36-learn-cloud-aws.md), [37](37-learn-security-devsecops.md) |
| Database ran out of connections | Restart the app | Connection pooling, per-app limits, alerts on connection use as a percentage of the maximum | [38](38-learn-databases-ops.md) |

You also become the person who runs the incident rather than the person typing the fix. That
means the incident commander role from the SRE book: coordinate, keep a timeline, decide when to
roll back, and keep stakeholders informed (section 11).

### Senior portfolio

**1. A GitOps platform on the homelab cluster [L3 · Senior].** Argo CD or Flux, a repository per
environment (or folders), Helm charts, promotion from staging to production by image digest, and
a written rollback. Modules: [33](33-learn-cicd-iac-sre.md), [35](35-deployment-patterns.md).

**2. Observability with SLOs [L3 · Senior].** Prometheus, Alertmanager, Grafana and Loki. One
service gets an SLO, an error budget and burn-rate alerts, plus a dashboard that answers "are
users OK right now?" in five seconds. Module: [32](32-learn-performance-observability.md).

**3. A disaster-recovery drill with measured numbers [L3 · Senior].** Restore etcd from a
snapshot and PostgreSQL 16 to a point in time, on fresh machines, with a stopwatch. Publish the
measured recovery time (RTO) and data loss (RPO) next to the targets. Modules:
[31](31-learn-kubernetes.md), [38](38-learn-databases-ops.md).

**4. A hardening baseline [L3 · Senior].** An Ansible role based on the CIS Benchmark for Ubuntu
24.04, with a before-and-after report and a list of the controls you skipped and why. Module:
[37](37-learn-security-devsecops.md).

**5. A design doc and ADRs [L3 · Senior].** For example "One ingress per host" or "Dokploy or
Kubernetes for our twelve apps": context, options, trade-offs, decision, consequences. Module:
[39](39-learn-senior-architecture.md).

### Senior 90-day plan

| Weeks | Focus | Handbook | KodeKloud | Output you keep |
|---|---|---|---|---|
| 1–2 | Map what exists | [39](39-learn-senior-architecture.md), [22](22-playbook-ports-inventory.md) | — | Architecture doc of your environment (hosts, ports, proxies, registry, pipelines, owners) and its top five risks |
| 3–4 | Observability with SLOs | [32](32-learn-performance-observability.md) | *Prep Course - PCA*: Prometheus Fundamentals, PromQL, Alerting; *Grafana Loki* | Portfolio project 2 |
| 5–6 | Safe deploys | [35](35-deployment-patterns.md), [33](33-learn-cicd-iac-sre.md) | *Helm for Beginners*; *Kubernetes Networking Deep Dive* (Services, Ingress) | Health-gated deploys with automatic rollback in your pipeline |
| 7–8 | Security baseline | [37](37-learn-security-devsecops.md) | *CKS*: System Hardening, Supply Chain Security | Hardening role and Harbor scanning gate (project 4) |
| 9–10 | Recovery | [31](31-learn-kubernetes.md) cluster maintenance, [38](38-learn-databases-ops.md) | *CKA* Cluster Maintenance (Backup and Restore Methods) as a refresher | DR drill with measured RTO and RPO (project 3) |
| 11–13 | Decide and teach | [39](39-learn-senior-architecture.md), this module | *HashiCorp Certified: Terraform Associate 004* or *AWS Certified CloudOps Engineer - Associate* | Design doc and ADRs (project 5); one junior mentored through the L1 exit test |

### Ready for Lead, Staff or SRE

- Teams other than yours depend on what you built, and it runs without you.
- You run incidents calmly, and your postmortems lead to changes in systems and processes, not just tickets.
- Your design docs get adopted, and people ask for your view before they decide.
- You have helped at least one person reach the next stage.
- You think in error budgets, cost and risk, and you can explain them to someone who isn't an engineer.
- You have chosen **not** to build something, and that decision held up.

### Senior mistakes

- **CV-driven development.** A service mesh for five services, a new cluster because Kubernetes is interesting. Every component is something the on-call engineer has to understand at 3 a.m.
- **Becoming the bottleneck.** If every decision or fix needs you, the team cannot grow and you cannot go on holiday. Write it down, delegate, review.
- **Building platforms nobody asked for.** Talk to the teams who will use it before you build it, and measure whether they do.
- **Ignoring cost and operability.** A design is not done until you know what it costs per month and who runs it.
- **Arguing from taste.** "I prefer X" loses to data. Bring numbers, a prototype or a precedent.
- **Saying yes to everything.** Senior engineers protect focus, theirs and the team's.

---

## 6. Lead, Staff and SRE · L4

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements, Incident Management, Change Management for Reliability ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Read: the [Google SRE books](https://sre.google/books/), chapters 12, 14 and 15 of the SRE book · 3) Note: [32 — Performance and observability](32-learn-performance-observability.md) sections 12 and 15 (alert rules, SLOs and error budgets) and [39 — Senior architecture](39-learn-senior-architecture.md) · 4) Video: none recommended; read real postmortems on [k8s.af](https://k8s.af/) instead · 5) Practice: the L4 game day with a published one-page postmortem.

**[L4 · Lead], 5+ years.** Whether the title is Lead, Staff, Principal or SRE, the job is the
same at its core: make reliability a property of the organisation instead of a property of a few
heroic people. The Ops Ladder L4 skills (metrics, logs and alerts, performance analysis, incident
response, postmortems and change management) are the toolkit.

### Good lead and SRE work

- **You define what "reliable enough" means**, with SLOs agreed with product owners, and you use error budgets to decide between feature work and reliability work.
- **You run major incidents** as incident commander and make the process work for everyone else: clear roles, regular updates, a blameless review.
- **You remove toil.** You measure where on-call time goes and automate or delete the biggest items.
- **You fix the system that produces incidents**: change management, review culture, on-call load, alert quality.
- **You grow people.** Juniors move up faster because of the paths, reviews and feedback you set up. This handbook is one such tool.
- **You make the roadmap**: what the platform does next year, what it stops doing, and what it costs.

### Lead skills checklist

| Area | Can do alone | With help | Not yet |
|---|---|---|---|
| Reliability | SLOs, error budget policies, burn-rate alerting, capacity planning | Company-wide reliability targets | — |
| Incidents | Incident command for major incidents, incident process design, postmortem reviews | Legal or regulatory reporting after incidents | — |
| Architecture | Platform strategy, build vs buy, on-prem vs cloud decisions with cost models | Company-wide architecture governance | — |
| Security | Security requirements in platform design, coordinating incident response with the security team | Security programme ownership | — |
| People | Mentoring, interviewing, onboarding paths, feedback | Performance management (if you take the manager path) | — |
| Communication | Writing for executives, roadmaps, negotiation between teams | Board-level reporting | — |

The technical areas from the earlier checklists don't go away. You keep at least Senior depth in
two or three of them, so your decisions stay grounded and engineers trust them.

### Lead incidents

| Situation | What L4 looks like | Read |
|---|---|---|
| A major incident across several teams | You take incident command, assign operations and communications roles, set the update rhythm, decide on rollback or failover, and call the all-clear | [Google SRE book](https://sre.google/books/) chapter 14, section 11 here |
| The same class of incident keeps coming back | You find the shared cause (missing standard, process gap, overloaded team) and fix that, not the next instance | [33](33-learn-cicd-iac-sre.md) |
| A provider or cloud outage | You executed the failover plan you wrote and rehearsed months before | [36](36-learn-cloud-aws.md), [39](39-learn-senior-architecture.md) |
| A security incident | You coordinate with the security team: contain, preserve evidence, rotate credentials, communicate | [37](37-learn-security-devsecops.md) |
| On-call burnout | You measure pages per shift, cut noisy alerts, and staff the rotation properly | [32](32-learn-performance-observability.md) |

The arithmetic behind error budgets, which you should be able to do on a whiteboard:

```
SLO               99.9% of requests to app.example.com succeed (non-5xx) over 30 days
Error budget      0.1% of requests  (as time: 30 d x 24 h x 60 min x 0.001 = 43.2 minutes)
Fast-burn page    burn rate 14.4 for 1 hour (confirmed over 5 min)  -> 2% of the budget in 1 hour
Slow-burn ticket  burn rate 6 for 6 hours (confirmed over 30 min)   -> 5% of the budget in 6 hours
Budget spent?     freeze risky releases, spend the sprint on reliability, as the policy says
```

**Why burn rates:** an alert on "error rate above 1%" pages for short blips and misses slow
leaks. An alert on how fast the budget burns pages only when users will feel it. The SRE
workbook, in the [Google SRE books](https://sre.google/books/), explains the method.

### Lead portfolio

**1. A game-day programme [L4 · Lead].** A script breaks one random thing in the homelab. You
find out from an alert, fix it, and publish a one-page postmortem with a timeline, root cause and
follow-ups. This is the Ops Ladder L4 exit test. Run it monthly and keep the postmortems public.

**2. An incident management process [L4 · Lead].** Severity levels, roles, update templates and a
postmortem template, written for your organisation and used at least once.

**3. An SLO and error-budget policy [L4 · Lead].** SLOs for three services, the policy for what
happens when a budget runs out, and three months of data.

**4. An onboarding path built from this handbook [L4 · Lead].** A fresher-to-junior path for your
team, with exit tests, and evidence that someone used it.

**5. Talks and writing [L4 · Lead].** A meetup talk or a blog series about a real incident or
migration. Writing is how a Lead's influence reaches people they never meet.

### Lead 90-day plan

For your first 90 days in a Lead or SRE role:

| Days | Focus | What you do | Output |
|---|---|---|---|
| 1–30 | Listen | Read the last ten postmortems, shadow on-call, interview each team about what hurts, map the systems | A one-page "state of reliability" with the top five problems |
| 31–60 | Stabilise | Fix the noisiest alerts, set up incident roles and templates, agree SLOs for the two most important services | Pages per week down; incident process in use |
| 61–90 | Improve | Error-budget policy, a reliability roadmap, the first game day, an onboarding path | Roadmap agreed by product and engineering |

KodeKloud's *Fundamentals of SRE* (SLOs, Incident Management, Change Management for
Reliability) is a good refresher during days 1–30. The real material is the
[Google SRE books](https://sre.google/books/), GitLab's
[change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/)
handbook page and real postmortems from [k8s.af](https://k8s.af/) and
[Dan Luu's list](https://github.com/danluu/post-mortems).

### Beyond L4

There is no exit test after L4. Growth from here is principal or distinguished engineer, head
of platform, or engineering manager of several teams. The signs you are growing: decisions you
made years ago still hold, people you mentored now mentor others, and the organisation handles
incidents well when you are not in the room.

### Lead mistakes

- **Staying the best firefighter.** If you still fix every major incident yourself, nobody else learns to, and you have no time for the work that prevents them.
- **Process for its own sake.** A change advisory board that meets weekly and approves everything slows teams without reducing risk. Automate the checks, keep human review for real risk.
- **SLOs nobody uses.** An SLO that doesn't change a decision is just a dashboard.
- **Losing technical depth.** Keep hands-on time every week, or your judgement drifts away from how systems really behave.
- **Blame dressed up as "accountability".** One blameful postmortem teaches everyone to hide information in the next incident.

---

## 7. Skills matrix

> 📚 **Study path:** 1) Note: [34 — Roadmap](34-roadmap.md), to turn each low score into topics · 2) KodeKloud: the course for your lowest-scoring area from the table in section 1, for example *Terraform Basics Training Course* — Terraform State, Remote State for IaC ([link](https://kodekloud.com/courses/terraform-basics-training-course)) · 3) Practice: [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) tasks in your weakest area as the morning rep · 4) Re-score in 90 days, with evidence for every change.

**[All stages].** The per-stage checklists above tell you what to do now. This matrix shows each area across all
five stages, so you can see where each skill is heading and spot the areas where you are behind
or ahead.

### The matrix

| Area | Fresher [L0] | Junior [L1] | Mid [L2] | Senior [L3] | Lead / SRE [L4] |
|---|---|---|---|---|---|
| Linux | Shell, files, permissions, packages | Runs services: systemd, journald, disks, timers | Diagnoses performance, OOM, boot problems; `strace` | Sets fleet standards and baselines | Owns the fleet lifecycle strategy |
| Networking | IP, ports, DNS basics | Port → process, UFW, netplan, resolvectl | Layered walk, tcpdump, NAT, Docker and firewalls, TLS | Designs platform networks and ingress | Network strategy with the network and security teams |
| Scripting | Small bash, ShellCheck-clean | Robust bash, small Python | Python tools with tests | Tools other teams use | Decides where automation pays off |
| Git | Commit, branch, revert | Rebase, conflicts, reviews | Bisect, repository conventions | Release and GitOps strategy | Engineering-wide conventions |
| Containers | `run`, `logs`, `exec` | Dockerfiles, Compose, log rotation | Docker networking and DNS, Traefik, Swarm, Harbor with a private CA | Base images, registry design, supply chain | Container platform strategy |
| Kubernetes | `get` and `describe` in a lab | Deploys manifests in a homelab | CKA: build, upgrade, restore, debug | Cluster design, multi-tenancy | Platform build-vs-buy decisions |
| Cloud (AWS) | Sandbox EC2 | EC2, security groups, IAM roles, S3 | VPC, ALB, Auto Scaling, RDS, CloudWatch | Multi-AZ architecture, IAM strategy, cost | Cloud strategy and cost governance |
| IaC | Reads it | Ansible playbooks, `terraform plan` and `apply` | Modules, remote state, imports | Standards, drift detection, policy checks | Organisation-wide adoption |
| CI/CD | Reads job logs | Build-and-push pipeline | Test, scan, push, deploy, verify, roll back | Templates, promotion by digest, progressive delivery | Delivery performance (deploy frequency, lead time, change failure rate, time to restore) |
| Observability | Reads dashboards | Exporters, dashboards, simple alerts | PromQL, logs, USE and RED dashboards | SLOs and burn-rate alerts | SLO programme and on-call health |
| Security | Keys, sudo, no secrets in Git | UFW, certificate renewal, private CA trust | Image scanning, secrets management, least-privilege IAM | Hardening baselines, scanning gates | Security requirements across the platform |
| Databases | Connect and query | Backup, restore to a test host | Connections, replication status, migrations in deploys | HA, point-in-time recovery, major upgrades | Data reliability strategy |
| Troubleshooting | Follows triage, collects evidence | Single-layer incidents alone | Multi-layer incidents alone | Prevents classes of incidents | Fixes the system that produces incidents |
| Communication | Clear tickets and questions | Runbooks, five-line incident notes | Change requests, postmortems, status updates | Design docs, ADRs, incident command | Roadmaps, executive updates, mentoring programmes |

### Score yourself

Score each area from 0 to 4 against the matrix. Each score needs a piece of evidence you could
show someone: a ticket, a commit, a lab log, a write-up. No evidence, no score.

| Score | Meaning |
|---|---|
| 0 | Not yet: you have read about it at most |
| 1 | With help: you can do it with a runbook or someone beside you (Fresher column) |
| 2 | Alone on routine work (Junior column) |
| 3 | Alone on non-routine work, and you can teach it (Mid column) |
| 4 | You set the standard others follow (Senior column and above) |

Copy this into your notes repository and fill it in every quarter:

```
| Area            | Score | Evidence (link or note)                      | Target in 90 days | Next action                          |
|-----------------|-------|----------------------------------------------|-------------------|--------------------------------------|
| Linux           |       |                                              |                   |                                      |
| Networking      |       |                                              |                   |                                      |
| Scripting       |       |                                              |                   |                                      |
| Git             |       |                                              |                   |                                      |
| Containers      |       |                                              |                   |                                      |
| Kubernetes      |       |                                              |                   |                                      |
| Cloud (AWS)     |       |                                              |                   |                                      |
| IaC             |       |                                              |                   |                                      |
| CI/CD           |       |                                              |                   |                                      |
| Observability   |       |                                              |                   |                                      |
| Security        |       |                                              |                   |                                      |
| Databases       |       |                                              |                   |                                      |
| Troubleshooting |       |                                              |                   |                                      |
| Communication   |       |                                              |                   |                                      |
```

### Reading your profile

**A T-shape is the goal.** Breadth at Junior level across all fourteen areas, plus depth (3 or
4) in two or three. A profile with one area at 4 and the rest at 0 struggles in incidents,
because incidents cross areas.

**Your estimated profile today** (from your Ops Ladder notes and the Apache → Dokploy work;
replace it with your own evidence-based scores):

| Area | Estimate | Why | The move that raises it |
|---|---|---|---|
| Linux | 2 | L1 is "mostly in place" per your notes | Ops Ladder L1 exit test under 5 minutes, then the slow-system drills in [23](23-playbook-slow-system.md) |
| Networking | 2 | Good layered method, but no packet captures or resolver logs yet | The four blind-spot tools: tcpdump, `getent ahosts`, resolver debug logs, `curl --resolve` |
| Containers | 2 | Dokploy, Docker and Harbor in daily use | Container DNS, `DOCKER-USER`, the Traefik 502 drill |
| Kubernetes | 1 | CKA track in progress, homelab | CKA, plus the break-and-fix log |
| CI/CD | 1–2 | GitLab CI in use | The L3 exit test pipeline |
| IaC | 0–1 | Not in your notes yet | Ansible playbook for Docker and `daemon.json`, then Terraform |
| Observability | 1 | Not in your notes yet | node_exporter, Prometheus and Grafana with the two Ops Ladder alerts |
| Communication | 2–3 | Your incident write-up is already the kind of proof teams hire on | Change requests in GitLab's format, public postmortems |

That profile is a **Junior moving into Mid**: L1 is mostly solid, L2 is in progress, and the
missing pieces are known and specific.

---

## 8. Interview preparation

> 📚 **Study path:** 1) Note: [21 — Apache 443 and Dokploy](21-case-apache-443-dokploy.md) for your STAR story and [25 — Site down](25-playbook-site-down.md) for the layered walk (refreshers, so they come first) · 2) KodeKloud: *DevOps Interview Questions and Answers: Scenario-Based Prep* (free, listed on the [Free Courses](https://kodekloud.com/free-courses) page) · 3) Read: [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 4) Practice: [SadServers](https://sadservers.com/scenarios), *Linux Challenges* and *Kubernetes Challenges* ([link](https://kodekloud.com/courses/kubernetes-challenges)) with a timer, thinking aloud.

**[L0 · Fresher] to [L4 · Lead].** The questions below are grouped by stage. Prepare the stage
you are applying for and the one below it, because interviewers start one level down to find
your floor before they test your ceiling.

### How DevOps interviews run

| Round | What they test | How to prepare | Stage where it appears |
|---|---|---|---|
| Recruiter screen | Do your stage, salary range and story fit the role? | A 60-second version of your story; know your numbers | All |
| Technical screen | Concepts: Linux, networking, containers, CI/CD, cloud | The concept questions below, answered aloud | All |
| Live troubleshooting | A broken VM or cluster, with a timer, while you think aloud | SadServers and KodeKloud challenges under a timer, narrating as you go | Junior and up |
| System design | Design a pipeline, a platform or an HA deployment on a whiteboard | The Senior questions below; [35](35-deployment-patterns.md) and [39](39-learn-senior-architecture.md) | Mid and up |
| Behavioural | Past incidents, conflict, mistakes, influence (STAR format) | Three stories written down: an incident, a migration, a mistake | All, deeper for Senior and up |
| Take-home | A pipeline, a Terraform module or a Dockerfile to build and explain | Your portfolio projects are rehearsals for this | Sometimes |

KodeKloud's free *DevOps Interview Questions and Answers: Scenario-Based Prep* (listed on the
[Free Courses](https://kodekloud.com/free-courses) page) is good extra practice for the
scenario rounds.

### Answering scenario questions

Interviewers care more about **how** you approach a scenario than about the final answer. Use the
same structure every time, out loud:

1. **Clarify.** Who is affected, since when, what changed recently? Is it all users or some?
2. **Stabilise.** If a change happened just before, say you would consider rolling it back first and investigating afterwards.
3. **Evidence first.** Name the command and what each possible output would mean: "I'd run `ss -ltnp 'sport = :443'`. If it shows apache2, then…".
4. **One layer at a time.** Form a hypothesis, test it, and move to the next layer only when this one is proven fine.
5. **Fix, then verify.** Say how you would prove the fix worked, from the user's side.
6. **Prevent and communicate.** What stops it happening again, and who you would tell.

When you don't know something, say so and say how you would find out: "I haven't used that
flag. I'd check the man page, try it on a test VM, and look at what the error text says." That
answer beats a confident guess every time.

### Fresher questions

**Q1. What happens when you type https://app.example.com into a browser?** [L0 · Fresher]

Outline: the name is resolved (browser cache, `/etc/hosts` through nsswitch, then the DNS
resolver), a TCP connection is opened to port 443 (SYN, SYN-ACK, ACK), a TLS handshake checks
that the certificate matches the name and chains to a trusted CA, an HTTP request is sent with a
Host header, a proxy or web server routes it to the app, and the response comes back. Strong
answers name the tool that tests each step: `getent ahosts`, `nc -vz`, `openssl s_client`,
`curl -v`. Handbook: [28](28-learn-networking.md) section 1, [25](25-playbook-site-down.md).

**Q2. Explain every field of an `ls -l` line.** [L0 · Fresher]

Outline: for `-rw-r----- 1 www-data adm 48211 Oct  3 09:12 access.log`, the file type (`-` file,
`d` directory, `l` symlink), permission bits for owner, group and others, the hard link count,
the owner, the group, the size in bytes, the modification time and the name. Bonus: on a
directory, `x` means you may enter it, and `r` means you may list it. Handbook:
[10](10-users-permissions-security.md), [27](27-learn-linux.md).

**Q3. What does `chmod 640` mean, and why is `chmod 777` a bad fix?** [L0 · Fresher]

Outline: 6 = read and write for the owner, 4 = read for the group, 0 = nothing for others. 777
lets any user change the file's contents (renaming or deleting it depends on the directory's
permissions), and if root later runs it, anyone can get root. The
real fix is the right owner and group. Handbook: [10](10-users-permissions-security.md).

**Q4. How do you check whether a service is running, and why it failed?** [L0 · Fresher]

Outline: `systemctl status UNIT` (active or failed, main PID, last log lines),
`journalctl -u UNIT -b --no-pager` for the full log since boot, and `systemctl is-enabled UNIT`
for whether it starts at boot. "Active" and "enabled" are different questions. Handbook:
[07](07-services-systemd.md), [06](06-logs-journal.md).

**Q5. The disk is full. How do you find what is using it?** [L0 · Fresher]

Outline: `df -h` to find the filesystem, `df -i` in case inodes ran out, then
`sudo du -xh --max-depth=1 /var | sort -h` and drill down. Mention that a deleted file still held
open by a process keeps using space (`sudo lsof -nP +L1`), and that you don't delete things you
don't understand. Handbook: [01](01-storage-disk.md).

**Q6. What is a port, and how do you see what is listening?** [L0 · Fresher]

Outline: a port number identifies which program on a host receives a connection. `sudo ss -ltnp`
lists listening TCP sockets with the owning process. `127.0.0.1:3000` is reachable only from the
host itself, `0.0.0.0:443` on every IPv4 address of the host, so from any network the firewall
lets through (`[::]:443` is the IPv6 equivalent). Handbook: [22](22-playbook-ports-inventory.md),
[02](02-network.md).

**Q7. What is the difference between TCP and UDP?** [L0 · Fresher]

Outline: TCP is connection-oriented, ordered and retransmits lost data (HTTP, SSH, databases).
UDP sends independent datagrams with no delivery guarantee (DNS queries, NTP, VXLAN overlays,
streaming). DNS falls back to TCP for large answers, so firewalls must allow both on port 53.
Handbook: [28](28-learn-networking.md).

**Q8. What is DNS, and what is `/etc/hosts` for?** [L0 · Fresher]

Outline: DNS turns names into addresses through resolvers and authoritative servers, with caching
controlled by TTLs. `/etc/hosts` is a local override consulted through `/etc/nsswitch.conf`.
Strong answer: `dig` asks the DNS server directly and skips `/etc/hosts`, while `curl` and
`getent ahosts` follow nsswitch, which is why `dig` and `curl` can disagree. Handbook:
[08](08-dns.md), [28](28-learn-networking.md).

**Q9. How do you set up key-only SSH safely?** [L0 · Fresher]

Outline: `ssh-keygen -t ed25519`, `ssh-copy-id USER@HOST`, then log in with the key **in a second
terminal** while the first session stays open. Only then set `PasswordAuthentication no` (in a
drop-in under `/etc/ssh/sshd_config.d/` whose name sorts before any file already there, such as
cloud-init's `50-cloud-init.conf`, because sshd keeps the first value it reads), check the syntax
with `sudo sshd -t`, confirm the effective value with `sudo sshd -T | grep -i passwordauthentication`,
and reload the SSH service (`sudo systemctl reload ssh`, `sshd` on RHEL). Keeping the first session open is what saves you if you lock yourself out. Handbook:
[09](09-ssh-remote-access.md).

**Q10. What is the difference between `git revert` and `git reset`?** [L0 · Fresher]

Outline: `revert` adds a new commit that undoes an old one, so history stays intact and it is
safe on shared branches. `reset` moves the branch pointer back and rewrites history, which breaks
everyone else's copy if the commits were already pushed. Use `reset` only on local work. Handbook:
[33](33-learn-cicd-iac-sre.md).

**Q11. How is a container different from a virtual machine?** [L0 · Fresher]

Outline: a VM runs its own kernel on virtual hardware. A container is a set of processes on the
host's kernel, isolated by namespaces (what they can see) and limited by cgroups (what they can
use). Containers start faster and are lighter, but share the kernel, so isolation is weaker.
Handbook: [30](30-learn-docker.md) section 2.

**Q12. What is the difference between `CMD` and `ENTRYPOINT` in a Dockerfile?** [L0 · Fresher]

Outline: `ENTRYPOINT` is the executable that always runs. `CMD` provides default arguments, or
the default command when there is no `ENTRYPOINT`. Arguments to `docker run IMAGE ...` replace
`CMD`, not `ENTRYPOINT`; `--entrypoint` replaces the entrypoint. Prefer the exec (JSON array)
form so the process is PID 1 and receives signals. Handbook: [30](30-learn-docker.md).

**Q13. A website doesn't open. What do you check first?** [L0 · Fresher]

Outline: is it only me (another network, another machine)? What exactly happens: a DNS error, a
timeout, a certificate warning, an HTTP error code? `curl -I https://HOST/` shows which. Then
check that the name resolves and the port answers, collect the output, and escalate with it.
Handbook: [25](25-playbook-site-down.md) section 1, [README](README.md).

**Q14. Running a script gives "Permission denied". Why?** [L0 · Fresher]

Outline: the execute bit is missing (`chmod +x`), the filesystem is mounted `noexec` (check with
`findmnt -no OPTIONS --target FILE`), the shebang points to a missing interpreter (that one gives
"bad interpreter"), or you can't enter a directory on the path. `ls -l` and `namei -l PATH` show
which. Handbook: [10](10-users-permissions-security.md).

### Junior questions

**Q1. Port 443 is already in use. What do you do?** [L1 · Junior]

Outline: kill nothing yet. `sudo ss -ltnp 'sport = :443'` shows the process and PID,
`systemctl status PID` shows the unit that owns it, and its config shows why it listens there
(`sudo apache2ctl -S` for Apache). Check socket activation (`systemctl list-sockets`) and IPv6
(`[::]:443`). Then decide: should it be there? If two programs both need 443, one becomes the
front door and the other moves to an internal port behind it. That is exactly your Apache →
Dokploy case. Handbook: [22](22-playbook-ports-inventory.md), [21](21-case-apache-443-dokploy.md).

**Q2. `/var` is full on a production server. Walk me through it.** [L1 · Junior]

Outline: `df -h` and `df -i`, then `sudo du -xh --max-depth=1` down the tree. Check deleted-but-open
files with `sudo lsof -nP +L1` (space returns only when the process restarts or the file is
truncated). Usual suspects: the journal (`journalctl --disk-usage`, then `--vacuum-size`),
unrotated app logs, Docker (`docker system df`). Before deleting anything, know what it is and who
owns it. Afterwards, add rotation and an alert. Handbook: [01](01-storage-disk.md),
[23](23-playbook-slow-system.md).

**Q3. A systemd service won't start. How do you debug it?** [L1 · Junior]

Outline: `systemctl status UNIT -l`, then `journalctl -u UNIT -b -n 100`. Common causes: wrong
`ExecStart` path, missing `EnvironmentFile`, permissions for the service user, the port already
taken, and "start request repeated too quickly" after too many restarts (fix the cause, then
`systemctl reset-failed UNIT`). `systemd-analyze verify /etc/systemd/system/UNIT.service`
catches unit-file mistakes. Handbook:
[07](07-services-systemd.md).

**Q4. Write a systemd unit for an app. What matters, and why not just use `nohup`?** [L1 · Junior]

Outline: `User=` (not root), an absolute `ExecStart`, `Restart=on-failure` with `RestartSec`,
`EnvironmentFile`, `WorkingDirectory`, `After=network-online.target` plus `Wants=` if it needs the
network, `WantedBy=multi-user.target`; then `daemon-reload` and `enable --now`. `nohup` gives you
no restart, no boot start, no journal and no resource limits. Handbook:
[07](07-services-systemd.md).

**Q5. The load average is 12 on a 4-core server, but the CPU is mostly idle. Why?** [L1 · Junior]

Outline: Linux counts tasks in uninterruptible sleep (state D) in the load average, and they are
usually waiting for disk or NFS. `vmstat 1` shows a high `b` column and `wa`, `iostat -xz 1`
shows the busy device, and `ps -eo state,pid,cmd` filtered on `D` names the waiting processes.
Handbook: [23](23-playbook-slow-system.md), [03](03-cpu-performance.md).

**Q6. What is the difference between "connection refused" and "connection timed out"?** [L1 · Junior]

Outline: refused means the host answered with a reset: nothing listens on that address and port
(often the app is bound to 127.0.0.1 only), or a firewall rule actively rejects. Timed out means
packets vanish: a firewall drop, a wrong route or a host that is down. `tcpdump` shows whether an
RST comes back. Handbook: [28](28-learn-networking.md), [02](02-network.md).

**Q7. Why doesn't `ufw deny` block a published Docker port?** [L1 · Junior]

Outline: Docker's NAT rule rewrites the destination in PREROUTING, so the packet is forwarded to
the container and passes through the FORWARD chain, never the INPUT rules UFW manages. Fixes:
don't publish ports for apps behind Traefik (attach them to the proxy network instead), bind
temporary ports to 127.0.0.1, or filter in the `DOCKER-USER` chain. Handbook:
[26](26-playbook-containers-k8s.md) section 3, [28](28-learn-networking.md).

**Q8. A container exits as soon as it starts. How do you debug it?** [L1 · Junior]

Outline: `docker ps -a` for the exit code and `docker logs CONTAINER` for the output. Exit 126 =
not executable, 127 = command not found, 137 = SIGKILL (often out of memory), 143 = SIGTERM. The
main process must stay in the foreground. To look inside, start a shell instead of the app:
`docker run --rm -it --entrypoint sh IMAGE`. Handbook: [26](26-playbook-containers-k8s.md)
section 2.

**Q9. How do you stop Docker container logs from filling the disk?** [L1 · Junior]

Outline: set `log-opts` (`max-size`, `max-file`) in `/etc/docker/daemon.json` and restart Docker.
It applies only to containers created afterwards, so recreate the existing ones. Per service, use
the `logging:` key in Compose. Handbook: [14](14-docker-containers.md),
[26](26-playbook-containers-k8s.md).

**Q10. Cron or a systemd timer?** [L1 · Junior]

Outline: timers log to the journal, can depend on other units, catch up on missed runs with
`Persistent=true`, spread load with `RandomizedDelaySec`, and show up in `systemctl list-timers`.
Cron is simpler and exists everywhere. For anything you need to debug later, choose the timer.
Handbook: [07](07-services-systemd.md).

**Q11. What is a reverse proxy, and why put one in front of an app?** [L1 · Junior]

Outline: it accepts client connections and forwards them to backends. It terminates TLS, routes
by Host header or SNI, gives one program ownership of 80 and 443, buffers slow clients so app
workers aren't tied up, balances load and adds headers. In Dokploy that program is Traefik.
Handbook: [29](29-learn-webservers-proxies.md).

**Q12. A GitLab CI job fails. How do you debug it?** [L1 · Junior]

Outline: read the job log from the **first** error, not the last line. Check which runner and
executor ran it and which image. Check variables: protected variables are only available on
protected branches and tags, a common surprise. Reproduce locally with the same image.
`CI_DEBUG_TRACE` prints everything, including secret values, so use it only in a private project
and delete the job log afterwards. Handbook: [33](33-learn-cicd-iac-sre.md).

**Q13. How do you make Docker trust Harbor's private CA?** [L1 · Junior]

Outline: put the CA certificate at `/etc/docker/certs.d/harbor.example.com/ca.crt` for Docker,
add it to the OS trust store (`/usr/local/share/ca-certificates/`, then
`sudo update-ca-certificates`) for curl and other tools, and configure containerd's
`/etc/containerd/certs.d/harbor.example.com/hosts.toml` on Kubernetes nodes. Every host that pulls
needs it. Marking the registry as insecure is not a fix. Handbook: [18](18-web-http-tls.md),
[26](26-playbook-containers-k8s.md).

**Q14. A user gets `Permission denied (publickey)`. Where do you look?** [L1 · Junior]

Outline: `ssh -vvv` shows which keys the client offers. On the server, `journalctl -u ssh`
(`sshd` on RHEL) often says why, and permissions must be strict: `~/.ssh` 700,
`authorized_keys` 600, and a home directory that is not group-writable. Also check `AllowUsers`
or `AllowGroups` and whether they use the right username. Handbook: [09](09-ssh-remote-access.md).

### Mid-level questions

**Q1. "The site is down." Walk me through it.** [L2 · Mid]

Outline: clarify scope (everyone or some users, since when, any change). If a change just went
out, consider rolling it back first. Then walk the layers in order and stop at the first that
fails: DNS from the client's point of view (`getent ahosts`, then `dig` against each resolver),
route (`ip route get`), port and firewall (`nc -vz`, tcpdump), TLS
(`openssl s_client -servername`), proxy (`curl -v --resolve` to bypass DNS, Traefik logs; the
status code says which layer answered), app (logs, health endpoint) and its dependencies. Prove
the broken layer with output before fixing. Handbook: [25](25-playbook-site-down.md).

**Q2. "The server is slow." Walk me through it.** [L2 · Mid]

Outline: the 60-second checklist (`uptime`, `dmesg -T`, `vmstat 1`, `mpstat -P ALL 1`,
`pidstat 1`, `iostat -xz 1`, `free -m`, `sar -n DEV 1`, `sar -n TCP,ETCP 1`, `top`) and the USE
method: utilisation, saturation and errors for CPU, memory, disk and network. Name the saturated
resource first, then find the process. Handbook: [23](23-playbook-slow-system.md),
[03](03-cpu-performance.md), [32](32-learn-performance-observability.md).

**Q3. A pod is in `CrashLoopBackOff`. What do you do?** [L2 · Mid]

Outline: `kubectl logs POD --previous` for the crashed container's output,
`kubectl describe pod POD` for Last State, exit code and reason (for example `OOMKilled` with
137), and events. Usual causes: the app fails at startup (bad config, unreachable dependency), a
liveness probe kills it before it is ready, memory limits, a wrong command. Fix based on the
evidence and verify that the restart count stops rising. Handbook:
[26](26-playbook-containers-k8s.md), [31](31-learn-kubernetes.md).

**Q4. Pods can't pull images from Harbor: `ImagePullBackOff`. Diagnose it.** [L2 · Mid]

Outline: the event text in `kubectl describe pod` says which of three problems it is:
`x509: certificate signed by unknown authority` (the node doesn't trust the CA: containerd's
`hosts.toml`), `unauthorized` (missing or wrong `imagePullSecret`, robot account permissions), or
`not found` (wrong name or tag). On the node, `sudo crictl pull IMAGE` shows the raw error.
Handbook: [26](26-playbook-containers-k8s.md), [31](31-learn-kubernetes.md).

**Q5. Traefik returns 404 for one app and 502 for another. What does each tell you?** [L2 · Mid]

Outline: 404 means no router matched: a typo in the Host rule, the wrong entrypoint, or labels
not re-read because the app was not redeployed. 502 means a router matched but the backend
refused the connection: wrong port, or an app listening on 127.0.0.1 inside its container. 504
means Traefik timed out: either the backend was too slow, or the dial itself timed out after 30
seconds (`dial tcp IP:PORT: i/o timeout` in the log), typically a container that is not on
`dokploy-network`. Check Traefik's logs and
the container's labels, and run `ss -ltn` inside the container's network namespace with
netshoot. Handbook: [25](25-playbook-site-down.md) section 3, [26](26-playbook-containers-k8s.md).

**Q6. A name resolves on the host but not inside a container. Why?** [L2 · Mid]

Outline: on user-defined networks, containers ask Docker's embedded DNS at 127.0.0.11, which
forwards to the host's upstream servers. If Docker finds no usable upstream it falls back to
8.8.8.8 and 8.8.4.4, which on-prem firewalls usually block. Or the target service is not on the
same network. Prove it with `docker exec CONTAINER cat /etc/resolv.conf` and tcpdump on port 53,
and fix with a `dns` list in `daemon.json`. Handbook: [26](26-playbook-containers-k8s.md)
section 4, [08](08-dns.md).

**Q7. Design a CI/CD pipeline from commit to production.** [L2 · Mid]

Outline: test and lint → build an image tagged with the commit SHA → scan → push to Harbor with
a robot account → deploy to staging → smoke tests → promote **the same digest** to production →
verify from outside → a rehearsed rollback job. Secrets live in masked, protected CI variables or
a secrets manager, never in the repository. Handbook: [33](33-learn-cicd-iac-sre.md),
[35](35-deployment-patterns.md).

**Q8. How does a Kubernetes Service send traffic to pods?** [L2 · Mid]

Outline: the Service's selector picks pods. Ready pods appear in EndpointSlices. kube-proxy on
every node programs rules (iptables, IPVS or nftables) that send traffic for the ClusterIP to
those endpoints, and CoreDNS answers `SVC.NS.svc.cluster.local`. No ready pods means no
endpoints, and the Service fails. Debug with
`kubectl get endpointslices -l kubernetes.io/service-name=SVC` and by comparing labels with the
selector. Handbook: [31](31-learn-kubernetes.md), [15](15-kubernetes.md).

**Q9. What is Terraform state, and what happens if two people apply at once?** [L2 · Mid]

Outline: state maps each resource in code to a real object ID. A remote backend (S3, with locking
through a lock file in recent Terraform or a DynamoDB table in older setups) stops two applies
from running at once. Without a lock you get a corrupted or diverged state. Never edit state by
hand; use `terraform state` and `import`, and run `plan` in CI. Handbook:
[33](33-learn-cicd-iac-sre.md), [36](36-learn-cloud-aws.md).

**Q10. An EC2 instance in a private subnet can't reach the internet.** [L2 · Mid]

Outline: the subnet's route table needs `0.0.0.0/0` via a NAT gateway; the NAT gateway sits in a
public subnet whose route table points to an internet gateway. The security group must allow
outbound traffic, and the NACL must allow both directions, including the return traffic on
ephemeral ports 1024–65535. Check DNS resolution in the VPC too. Handbook:
[16](16-aws-cloud.md), [36](36-learn-cloud-aws.md).

**Q11. curl says `unable to get local issuer certificate`. Fix it.** [L2 · Mid]

Outline: either the server sends its certificate without the intermediate (fix the server: serve
the full chain), or the issuing CA is private and missing from the client's trust store (add it
and run `update-ca-certificates`). `openssl s_client -connect HOST:443 -servername HOST -showcerts`
shows which. Never "fix" it with `curl -k` in a script. Handbook: [18](18-web-http-tls.md).

**Q12. Tell me about a migration you led.** [L2 · Mid]

Outline: use your Apache → Dokploy story in STAR format, later in this section.

**Q13. How do you know your backups work?** [L2 · Mid]

Outline: scheduled restore tests to a fresh host, timed, with a data check (row counts or an
application-level check). Alert when a backup job fails and when the newest backup is too old.
For PostgreSQL, WAL archiving gives point-in-time recovery. A backup that has never been restored
doesn't count. Handbook: [38](38-learn-databases-ops.md).

**Q14. Rolling, blue/green or canary: when do you use each?** [L2 · Mid]

Outline: rolling is the cheap default but runs two versions side by side during the rollout.
Blue/green switches all traffic at once and rolls back instantly, at the cost of double capacity
and a schema that works for both versions. Canary sends a small share of traffic first and
promotes based on metrics, so it needs good observability. Handbook:
[35](35-deployment-patterns.md).

**Q15. A pod stays `Pending`. Why?** [L2 · Mid]

Outline: the events at the bottom of `kubectl describe pod` usually say: requests larger than any
node's free capacity, a taint without a toleration, a PVC that never bound, or a nodeSelector or
affinity that nothing satisfies. `kubectl describe node NODE` shows allocated resources.
Handbook: [26](26-playbook-containers-k8s.md), [31](31-learn-kubernetes.md).

### Senior questions

**Q1. Design zero-downtime deploys for a web app with a database.** [L3 · Senior]

Outline: readiness probes so traffic only reaches ready instances; surge before removing old
instances (`maxUnavailable: 0`, or `order: start-first` in Swarm); graceful shutdown (handle
SIGTERM, drain connections, a `preStop` delay so the load balancer stops sending first); database
changes in expand/contract steps so old and new code both work (add a nullable column, deploy
code that writes both, backfill, switch reads, drop the old column in a later release); deploy by
digest; health-gated automatic rollback. Handbook: [35](35-deployment-patterns.md),
[39](39-learn-senior-architecture.md), [38](38-learn-databases-ops.md).

**Q2. Design a delivery platform for twenty teams.** [L3 · Senior]

Outline: shared GitLab CI templates teams `include`, Harbor projects per team with robot
accounts, scanning and retention policies, promotion by digest between environments, GitOps for
deploys, a golden path that is easier than doing it yourself, and guardrails rather than gates.
Measure it with adoption and delivery metrics (deploy frequency, lead time, change failure rate,
time to restore). Handbook: [33](33-learn-cicd-iac-sre.md), [37](37-learn-security-devsecops.md).

**Q3. How would you make sure the Apache-on-443 incident can never happen again?** [L3 · Senior]

Outline: one ingress owns 80 and 443 on every host; a port registry in Git; config management
controls listener configuration; a pre-install check that fails the pipeline if a required port
is taken; an alert when a host starts listening on a port not in its baseline; and the runbook
from the migration published so the next engineer starts from it. Handbook:
[21](21-case-apache-443-dokploy.md), [22](22-playbook-ports-inventory.md),
[39](39-learn-senior-architecture.md).

**Q4. How do you upgrade a production Kubernetes cluster?** [L3 · Senior]

Outline: read the release notes and check for removed APIs, take and verify an etcd snapshot,
rehearse on staging, upgrade the control plane one minor version at a time (`kubeadm upgrade plan`,
then `apply`), then drain and upgrade nodes one by one while PodDisruptionBudgets keep apps
available, and verify after each step. Rolling back means restoring etcd onto a rebuilt control
plane, which is exactly why you rehearse first. Handbook: [31](31-learn-kubernetes.md).

**Q5. How do you set resource requests and limits?** [L3 · Senior]

Outline: measure real usage (p95 and p99 over weeks), set requests near typical use so scheduling
is honest, set memory limits close to requests so OOM behaviour is predictable, be careful with
CPU limits because they throttle, keep N+1 headroom, and review capacity regularly. Handbook:
[32](32-learn-performance-observability.md), [31](31-learn-kubernetes.md).

**Q6. Design secrets management for the platform.** [L3 · Senior]

Outline: no secrets in Git or images. Options: a secrets manager (Vault, AWS Secrets Manager)
synced into clusters, or encrypted files in Git (SOPS). Kubernetes Secrets are only base64, so
enable encryption at rest and restrict RBAC. Rotation, audit logs and least privilege matter more
than the tool. Handbook: [37](37-learn-security-devsecops.md).

**Q7. Design a highly available web app on AWS.** [L3 · Senior]

Outline: an ALB across two or three Availability Zones, an Auto Scaling group spread across the
same zones, RDS Multi-AZ with automated backups and point-in-time recovery, static assets on S3,
health checks everywhere, and everything in Terraform. The RTO and RPO targets decide how far to
go, because each step costs money. Mention the on-prem equivalent for contrast. Handbook:
[36](36-learn-cloud-aws.md), [39](39-learn-senior-architecture.md).

**Q8. What should page a human, and what shouldn't?** [L3 · Senior]

Outline: page on symptoms users feel (SLO burn rate, error rate, latency), not on causes like
"CPU at 80%". Causes go to dashboards and tickets. Every page must be actionable and link to a
runbook. Delete or downgrade alerts nobody acts on. Handbook:
[32](32-learn-performance-observability.md).

**Q9. A team wants to skip code review to ship faster. What do you do?** [L3 · Senior]

Outline: find out what is actually slow (review wait time, large merge requests, unclear
owners). Offer a faster path: smaller changes, automated checks, a "standard change" category for
low-risk work, pairing as review. Keep human review for risky changes, write the agreement down,
and escalate only if needed. Handbook: [33](33-learn-cicd-iac-sre.md), section 11 here.

**Q10. Tell me about a postmortem you led.** [L3 · Senior]

Outline: blameless format, a timeline, contributing factors rather than one "root cause",
action items with owners and dates, and what happened to those actions afterwards. Interviewers
listen for systemic fixes and for the follow-through. Handbook: [33](33-learn-cicd-iac-sre.md),
[Google SRE books](https://sre.google/books/).

**Q11. On-prem or cloud for a new workload?** [L3 · Senior]

Outline: compare steady versus spiky load, data location and egress costs, compliance, the team's
skills, hardware lead times, the value of managed services and the cost of leaving later. Write it
as an ADR with numbers. Your Dokploy-on-prem setup versus a managed AWS service is a good example.
Handbook: [39](39-learn-senior-architecture.md), [36](36-learn-cloud-aws.md).

**Q12. How do you harden a fleet of Ubuntu servers?** [L3 · Senior]

Outline: a baseline derived from the CIS Benchmark, applied by Ansible, with documented
exceptions; key-only SSH and no root login; automatic security updates; default-deny firewalls
(remembering Docker's published ports); auditd; minimal packages; time sync; regular scans that
measure compliance. Handbook: [37](37-learn-security-devsecops.md),
[10](10-users-permissions-security.md).

**Q13. Plan a PostgreSQL major upgrade, for example 14 to 16, with minimal downtime.** [L3 · Senior]

Outline: three options. `pg_upgrade --link` (minutes of downtime; once the new cluster has
started, the old one can no longer be used safely, so take a backup first), logical replication
to a new 16 cluster followed by a switch-over (near-zero downtime, but sequences and DDL need
care), or dump and restore (simple, long downtime). Rehearse on a copy, check extensions, run
`vacuumdb --all --analyze-in-stages` afterwards, and keep a rollback path. Handbook:
[38](38-learn-databases-ops.md).

### Lead and SRE questions

**Q1. How do you define an SLO for a service?** [L4 · Lead]

Outline: start from a user journey, pick SLIs that users feel (availability, latency) measured
as close to them as possible (load balancer logs rather than app metrics), set a target slightly
below current performance and agree it with the product owner, use a 28- or 30-day window, and
write the error-budget policy. Handbook: [32](32-learn-performance-observability.md).

**Q2. Walk me through running a major incident.** [L4 · Lead]

Outline: declare it, take incident command (or hand it over), assign an operations lead and a
communications lead, open one channel, set an update rhythm (for example every 30 minutes),
stabilise before root-causing, keep a decision log, hand over if it runs long, call the
all-clear, and schedule the postmortem within days. Handbook: [Google SRE
books](https://sre.google/books/) (Managing Incidents), section 11 here.

**Q3. How do you reduce toil?** [L4 · Lead]

Outline: measure it (on-call logs, tickets by category), use the SRE definition (manual,
repetitive, automatable, no lasting value, grows with the service), fix the biggest items first,
and cap the share of time spent on toil. Handbook: [33](33-learn-cicd-iac-sre.md).

**Q4. On-call is burning people out. What do you do?** [L4 · Lead]

Outline: measure pages per shift and out-of-hours pages, delete or downgrade non-actionable
alerts, fix the top recurring causes, enlarge the rotation, write runbooks, and make sure people
are compensated. Report progress monthly. Handbook: [32](32-learn-performance-observability.md).

**Q5. Build or buy: Dokploy, Kubernetes or a managed service?** [L4 · Lead]

Outline: total cost of ownership including people, the skills you have, time to value, support,
lock-in and the exit plan. Write it as an ADR and revisit it when the number of apps or teams
changes. Handbook: [39](39-learn-senior-architecture.md).

**Q6. How do you balance reliability work against features?** [L4 · Lead]

Outline: error budgets make it a rule instead of an argument: while the budget is healthy,
ship; when it's spent, reliability work comes first. Put reliability items on the same roadmap as
features and express risk in money or hours of downtime.

**Q7. How do you measure a platform team's success?** [L4 · Lead]

Outline: delivery metrics (deploy frequency, lead time, change failure rate, time to restore),
SLO attainment, adoption of the platform, developer satisfaction, toil hours, cost per service.

**Q8. How do you grow junior engineers?** [L4 · Lead]

Outline: a clear ladder with exit tests (like this module), pairing on real incidents, real
ownership with a safety net, regular specific feedback, and making their work visible to people
who decide promotions.

**Q9. What does good change management look like?** [L4 · Lead]

Outline: risk classes (standard, normal, emergency), automated checks for the common risks, peer
review, a mandatory rollback plan, windows only for high-risk changes, and every incident linked
back to the change that caused it. GitLab's public
[change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/)
page is a good model.

**Q10. How would you interview a DevOps engineer?** [L4 · Lead]

Outline: a live troubleshooting exercise on a broken VM, a design discussion at their level, a
written postmortem or runbook they bring, and behavioural questions. No trivia: nobody remembers
every flag, and that isn't the job.

**Q11. Design disaster recovery for the business.** [L4 · Lead]

Outline: classify services into tiers, set RTO and RPO per tier, keep backups off-site and
immutable, rehearse restores and failovers on a schedule, run game days, and publish the measured
numbers. Handbook: [39](39-learn-senior-architecture.md), [38](38-learn-databases-ops.md).

**Q12. The same kind of incident happens every month. What do you do?** [L4 · Lead]

Outline: read the postmortems together, find the shared contributing factor (a missing standard,
a process gap, an overloaded team), fix it at that level, and track the recurrence rate to prove
it worked.

**Q13. How would you cut the AWS bill by 30%?** [L4 · Lead]

Outline: visibility first (tags, Cost Explorer by service and team), then rightsizing, Savings
Plans for steady load, Spot for interruptible work, storage lifecycle rules, deleting idle
resources, watching NAT gateway and data transfer charges, and switching non-production off
outside working hours. Handbook: [36](36-learn-cloud-aws.md).

### Your STAR story

Every interview from Junior up asks for a real story. Yours is the Apache → Dokploy migration,
and it is a strong one because it has a constraint, a risk, a method and a result. Fill in the
bracketed parts with your real numbers and keep the hostnames generic.

**Situation.** "An on-prem Ubuntu server ran Apache with [four] virtual hosts on ports 80
and 443. We needed to deploy a new application with Dokploy, which runs Traefik v3 on Docker Swarm
and needs 80 and 443 for itself. The installer refused to run because Apache held the ports, and
there was no inventory of the existing sites or their owners."

**Task.** "My job was to free 80 and 443 for Traefik without breaking the existing sites, with at
most a few minutes of downtime and a rollback I had tested before the change window."

**Action.** "First I built an inventory: every listener with `ss -ltnp`, every virtual host with
`apache2ctl -S`, and the access logs to see which sites still had traffic. I wrote a change
request with steps, verification and rollback. Before the window, I added `Listen 81` and
`Listen 444` alongside the old ports, moved the virtual hosts to them, ran `configtest`, reloaded,
and tested every site on the new ports with `curl --resolve` before touching 80 and 443. In the
window I removed the old `Listen` lines, confirmed with `ss` that 80 and 443 were free, installed
Dokploy, deployed the app and ran the verification list. When a check failed with a DNS error, I
tested the proxy separately from DNS with `curl --resolve` to find which layer was at fault
[describe what you found]. Afterwards I made sure 81 and 444 were not reachable from places they
shouldn't be."

**Result.** "The new app went live behind Traefik with a valid certificate. [All four] existing
sites kept working with [N minutes] of downtime. The rollback was written and rehearsed but not
needed. The runbook is in Git, and the next step, routing the legacy sites through Traefik and
moving one of them into a container built by GitLab CI and pushed to Harbor, is planned."

**What I'd do differently** (interviewers love this part, and it shows Senior thinking): "I'd do
the inventory before the deploy request, not after the installer failed. And instead of keeping
Apache on non-standard public ports, I'd put Apache on an internal port behind Traefik, so one
proxy owns TLS for every name and no port bypasses it. That's the pattern I'd now make a
standard for every host."

**Length:** practise a 60-second version (one sentence per letter) for screens and a five-minute
version for technical rounds. Expect follow-ups such as "why not just stop Apache?", "how did you
know which sites were used?", "what was the rollback?" and "what would you monitor afterwards?".
The answers are all in [21](21-case-apache-443-dokploy.md).

### Questions to ask them

Interviews go both ways. These questions tell you what the job will really be like:

- "What did your last major incident look like, and what changed afterwards?" (Do they run blameless postmortems?)
- "How does a change get to production, and how long does it take?" (Delivery maturity.)
- "What does on-call look like: how many pages a week, and how is it compensated?"
- "What would you expect from me in the first 90 days?"
- "How do people here move from Mid to Senior? Can you give an example from the last year?"
- "What is on-prem and what is in the cloud, and is that changing?"
- "What's the biggest source of toil for the team right now?"

### Live troubleshooting rounds

- **Narrate.** Silence looks like being stuck. "I'm checking whether anything listens on 443, because the error was connection refused" shows your method even if you're slow.
- **Read the error message, all of it.** Half of all live rounds are won by the person who actually reads the text.
- **Check the obvious first**: is the service running, is the disk full, is the clock right, is it DNS.
- **Prefer reversible moves** and say what you would do differently on production ("here I'd take a backup copy first").
- **Keep a timeline** in a scratch file. It helps you, and you can show it at the end.
- **Practise under the same conditions**: SadServers scenarios and KodeKloud's *Linux Challenges* and *Kubernetes Challenges* with a timer, talking aloud.

---

## 9. Learning with KodeKloud

> 📚 **Study path:** 1) Note: [34 — Roadmap](34-roadmap.md) to choose the topic, then the matching handbook module · 2) KodeKloud: *Crash Course: Linux For Absolute Beginners* (free, 21 minutes), only to learn how the graded labs work ([link](https://kodekloud.com/courses/crash-course-linux-for-absolute-beginners)) · 3) Notes: [KodeKloud Notes](https://notes.kodekloud.com/), the free text of each lesson · 4) Practice: the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) for break-and-fix sessions.

**[All stages], most useful from [L0 · Fresher] to [L3 · Senior].** KodeKloud is your main course
provider. Used well, it gives you hours of graded terminal time. Used badly, it becomes hours of
video that never transfer to a broken server. This section is the method that makes the
difference. The course choices per stage are in section 1 and in each stage's 90-day plan.

### The five-step loop

Every topic, at every stage, goes through the same five steps. The order matters: the handbook
gives the problem, KodeKloud gives the model and graded practice, and the break-and-fix step
proves that the skill transferred.

| Step | Time | What you do | Why this step | Next step |
|---|---|---|---|---|
| 1. Handbook note first | 10 min | Read the matching module (for example [22](22-playbook-ports-inventory.md) for ports). Write down the two or three commands or ideas you don't understand yet | The lesson then has a real problem to attach to | Step 2 with those questions in mind |
| 2. Lesson and lab | 30–60 min | Only the sections the stage plan names, in that order. Do the lab right after the lecture | Graded typing in a real terminal beats watching | If the lab beats you, read the lesson's KodeKloud Notes page and retry once before you open the solution |
| 3. Review in notes | 5 min | Find the lesson on KodeKloud Notes. Copy each new command into your own notes repo with one line on when to use it | Your notes are searchable at 3 a.m.; a video is not | Step 4 |
| 4. Break it on purpose | 20–30 min | In a playground or the homelab, recreate a failure from the handbook (for example the Apache vs Traefik clash from [21](21-case-apache-443-dokploy.md)) | Course labs teach building; your job is fixing | Fix it using only the playbooks [23](23-playbook-slow-system.md)–[26](26-playbook-containers-k8s.md) |
| 5. Timed drill | 15–30 min | The exit test or drill for your level, with a timer | Proves the skill works outside the course | Write the five-line note, tick the drill, pick the next topic |

### Labs first, video second

- **Skip lectures for things you already do daily** and go straight to the lab. If you pass it first time, move on. If not, watch the lecture and retry.
- **Timebox each lab question**: ten minutes stuck, then read the lesson note, then ten more minutes, then the hint or solution. Redo the whole lab the next day without help. A lab you passed after reading the solution does not count as done.
- **Type every command.** Never paste from the solution, because the typing is how the syntax gets into your fingers.
- **Read each question twice.** The graders check exact names, namespaces, paths and ports, and so does the CKA.
- **Use the tools the exam allows.** Practise with `man`, `--help` and `kubectl explain` instead of a search engine, because the CKA only lets you open the official documentation.
- **Do only the named sections.** Whole courses front to back waste weeks, for example the Docker Enterprise sections of the Docker Certified Associate course.

### Notes you will actually use

Keep one Git repository with one file per topic. It is your study aid now and the seed of your
public proof later (section 10).

```
notes/
├── linux/systemd.md
├── networking/dns.md
├── docker/networking.md
├── kubernetes/troubleshooting.md
├── incidents/2026-10-01-traefik-502.md
└── flashcards.md
```

One entry per command or idea, always in the same shape:

```
## sudo ss -ltnp 'sport = :443'
When:    "address already in use", or "who owns this port?"
Reads:   State, Recv-Q, Send-Q, Local Address:Port, Peer Address:Port, Process
Gotcha:  without sudo, the Process column is empty for other users' sockets
Source:  KodeKloud LFCS > Networking > Start, Stop and Check Status of Network Services;
         handbook 22, section 3
```

**Why this shape:** "When" is what you will search for during an incident, because you remember
the symptom, not the command. "Gotcha" stops you from trusting misleading output. "Source" lets
you go back to the full lesson.

### Spaced repetition

You forget most of a lesson within a few days unless you pull it back out of memory. Reviewing at
growing intervals keeps it for months at a fraction of the effort of re-watching.

| Review | When | How |
|---|---|---|
| 1 | The next day | Redo the lab from memory, or answer its questions aloud |
| 2 | Three days later | Five flashcards: symptom on the front, first command and what its output means on the back |
| 3 | One week later | A break-and-fix in the playground, without notes |
| 4 | Three weeks later | A timed challenge or drill: *Linux Challenges*, *Kubernetes Challenges*, a SadServers scenario |
| 5 | Two months later | Explain it to someone, or write the runbook or blog post about it |

Flashcards work best as symptom → first move, because that is the direction you need in an
incident. A plain file or any flashcard app will do:

```
Q: docker pull from Harbor fails with "x509: certificate signed by unknown authority"
A: The host doesn't trust Harbor's CA. Docker reads /etc/docker/certs.d/HARBOR/ca.crt,
   containerd reads /etc/containerd/certs.d/HARBOR/hosts.toml, curl uses the OS store
   (update-ca-certificates). Check with: openssl s_client -connect HARBOR:443 -showcerts

Q: Load average 12 on 4 cores, CPU mostly idle
A: Tasks in D state (waiting on disk or NFS) count towards load. vmstat 1 (b and wa columns),
   iostat -xz 1, ps -eo state,pid,cmd filtered on D.
```

### Your weekly rhythm

Adapted from your Ops Ladder. Each habit hangs on something that already happens, so the reps
don't depend on finding free time. It adds up to about eight hours a week.

| When | Time | What | Output |
|---|---|---|---|
| Workday mornings | 30 min | One KodeKloud Engineer or [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) task, **or** one [SadServers](https://sadservers.com/scenarios) scenario. Alternate between them | One line on what you missed |
| Two evenings | 60 min each | Loop steps 1–3 for the current topic. Until the CKA, that topic is the next CKA section | Notes entries |
| Weekend homelab block | 2–3 h | Loop steps 4–5, then a CKA break-and-fix session (Lightning Labs and mock exams in the last two weeks) | A break-and-fix log entry |
| Sunday evening | 30 min | One real postmortem from [k8s.af](https://k8s.af/) or [Dan Luu's list](https://github.com/danluu/post-mortems): name the failing layer before you read the root cause. Then your flashcards | One line in your notes |
| Any incident at work | 10 min | The five-line note: symptom, first wrong guess, deciding evidence, fix, what to check first next time | An `incidents/` entry |
| Last Sunday of the month | 30 min | Re-score your two weakest areas in the skills matrix and plan next month | Updated matrix |

**The rule that overrides the table:** until you pass the CKA, the CKA course comes first and
everything else runs on the 30-minute morning rep.

### Free versus paid

On 3 October 2026 the [Free Courses](https://kodekloud.com/free-courses) page listed, among
others: *Docker Training Course for the Absolute Beginner*, the *Crash Course* series (Linux,
Docker, Kubernetes, AWS), *Linux Challenges*, *Kubernetes Challenges*, *Terraform Challenges*,
*CKS – Challenges* and *DevOps Interview Questions and Answers: Scenario-Based Prep*. Lesson text on
[KodeKloud Notes](https://notes.kodekloud.com/), the playgrounds and the 100 Days of DevOps tasks
(one a day on the free plan) are free too. Everything else needs a subscription.

**How to spend the money:** do the free material first, then buy the subscription for the months
you are actively working through a paid course (the CKA months, for you). A subscription you are
not using every week is the most expensive way to feel productive. Prices and free status change,
so check the page before you pay.

### Where KodeKloud stops

KodeKloud has no course on several things your stack depends on. Use these instead:

| Topic | Use instead | Handbook |
|---|---|---|
| Traefik with Docker labels | Traefik's [Docker quick start](https://doc.traefik.io/traefik/getting-started/docker/) and [Docker routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/) | [29](29-learn-webservers-proxies.md) section 4 |
| Dokploy | [Dokploy docs](https://docs.dokploy.com/docs/core) and [troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) | [29](29-learn-webservers-proxies.md) section 5, [21](21-case-apache-443-dokploy.md) |
| Harbor with a private CA | [Harbor docs](https://goharbor.io/docs/) | [30](30-learn-docker.md) section 11 |
| Published ports bypassing UFW | Docker docs: [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) | [26](26-playbook-containers-k8s.md) section 3 |
| tcpdump and strace | [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/), [Spying on your programs with strace](https://wizardzines.com/zines/strace/) | [28](28-learn-networking.md) section 14 |
| The Linux performance method | [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) | [23](23-playbook-slow-system.md) section 2 |
| Real broken servers, timed | [SadServers](https://sadservers.com/scenarios), [Killercoda](https://killercoda.com/linux), [iximiuz Labs](https://labs.iximiuz.com/roadmaps/docker) | every playbook's practice section |

### KodeKloud mistakes

- **Watching at double speed without doing the labs.** It feels fast and leaves nothing behind. The lab is the course; the video is the introduction.
- **Opening the solution at the first difficulty.** Struggling for ten minutes is where the learning happens. Use the timebox above.
- **Studying five topics in parallel.** One main topic plus the morning reps. Finish, drill, then switch.
- **Treating completion certificates as certifications.** A KodeKloud completion certificate shows you finished a course. Only the exams in section 1 count as certifications, and projects count more than both.
- **Never leaving the lab environment.** Labs are pre-built and pre-configured. Rebuild the same thing on your homelab from nothing at least once per topic, because that is where the real gaps show.
- **Skipping step 5.** Without the timed drill you don't know whether you learned the topic or just recognised it.

---

## 10. Building proof

> 📚 **Study path:** 1) Note: [21 — Apache 443 and Dokploy](21-case-apache-443-dokploy.md) section 5 (a full change request) and section 13 (after the incident) · 2) KodeKloud: *Fundamentals of SRE* — Blameless Postmortem Culture ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page)) · 3) Read: GitLab's [change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/) page and the Postmortem Culture chapter in the [Google SRE books](https://sre.google/books/) · 4) Practice: publish your first sanitised runbook this week.

**[All stages], most valuable from [L1 · Junior] up.** Remote teams hire on written evidence.
A certificate shows that you studied. Public work shows that you can do the job, explain it, and
handle sensitive material responsibly. Your Apache → Dokploy write-up is already this kind of
document; this section is about producing more of it, on purpose.

### What counts as proof

| Proof | What it shows | Cost to you | Weight with hiring managers | From stage |
|---|---|---|---|---|
| Certification (for example the CKA) | You studied a curriculum and can work under time pressure | Exam fee and 6–10 weeks | Gets you past CV filters; required by some partners and consultancies | Junior |
| Portfolio repository with working code | You can build things that run | Evenings | High, if it runs and has a clear README | Fresher |
| Public runbooks | You can operate systems and write for others | Low: you write them anyway | High for operations roles | Junior |
| Postmortems | You learn from failure and think in systems | Low | Very high from Mid up | Mid |
| Blog posts | You can explain, and people can find you | Medium | Medium to high; they stay searchable for years | Mid |
| Talks and mentoring | Influence beyond your own work | High | High for Senior and Lead roles | Senior |
| Fixes to the docs of tools you use | You can work with strangers in public | Variable | Medium | any |

### Certifications versus projects

Certificates open doors and projects win offers. A certificate gets your CV read and gives you a
structured curriculum. In the interview, nobody asks about the certificate; they ask what you
built, what broke and what you did about it. The best combination is one certificate plus a
project that uses it, so every exam leaves something you can show:

| Certificate | The project that goes with it |
|---|---|
| CKA | The kubeadm homelab cluster with its break-and-fix log (Mid portfolio project 2) |
| HashiCorp Terraform Associate | The Terraform AWS repository with `plan` in CI (Mid portfolio project 4) |
| AWS associate exam | The same repository extended to a highly available app with a written cost estimate |
| CKS | The hardening baseline role with before-and-after scans (Senior portfolio project 4) |
| PCA | Observability with SLOs and burn-rate alerts (Senior portfolio project 2) |

### The public repository

One repository, organised so a reviewer finds the best material in under a minute:

```
ops-proof/
├── README.md                  # who you are, what is here, where to start (five lines)
├── runbooks/
│   ├── port-already-in-use.md
│   ├── disk-full.md
│   ├── traefik-502.md
│   └── harbor-x509-unknown-authority.md
├── postmortems/
│   ├── apache-443-dokploy-migration.md
│   └── homelab-gameday-coredns-loop.md
├── change-requests/
│   └── move-apache-off-80-443.md
├── labs/
│   ├── k8s-break-and-fix-log.md
│   └── sysreport/
├── pipelines/
│   └── gitlab-ci-harbor-dokploy/
└── infra/
    ├── ansible-docker-host/
    └── terraform-aws-vpc/
```

**Why this layout:** reviewers skim. Runbooks and postmortems at the top show operations
judgement in two clicks; code folders show you can build. Put the strongest three items in the
README by name.

### Sanitising before you publish

Work documents belong to your employer. Publish only what you are allowed to, and when in doubt,
reproduce the incident in your homelab and publish that version instead.

- **Addresses:** replace public IPs with the documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and internal ranges with one consistent fake range, so the story still makes sense.
- **Names:** domains become example.com, hostnames become roles (web-01, harbor-01), people become roles (on-call engineer, finance team).
- **Secrets and identifiers:** remove tokens, passwords, robot account names, customer names, ticket numbers, internal URLs and screenshots of internal tools.
- **Time:** use relative times (T+0, T+12 min) if the date would identify the incident.
- **Scan before every push**, because one forgotten token in Git history is a real incident of its own.

A pre-push check you can keep in the repository (run it on your own machine, in your repo):

```bash
# 1. Secrets in the whole Git history (gitleaks 8.19 or later; older versions use "gitleaks detect")
gitleaks git --no-banner -v .

# 2. Anything that looks like an IPv4 address, minus the documentation and loopback ranges
grep -rnoE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' --include='*.md' . \
  | grep -vE '192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|127\.0\.0\.|0\.0\.0\.0'

# 3. Your real company name or domain must not appear anywhere (REALCOMPANY is a placeholder)
grep -rniF 'REALCOMPANY' . || echo "clean"
```

```
$ gitleaks git --no-banner -v .
9:14AM INF 41 commits scanned.
9:14AM INF scanned ~186204 bytes (186.20 KB) in 380ms
9:14AM INF no leaks found

$ grep -rnoE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' --include='*.md' . | grep -vE '...'
./runbooks/traefik-502.md:42:172.18.0.5
./postmortems/apache-443-dokploy-migration.md:88:10.20.30.41

$ grep -rniF 'REALCOMPANY' . || echo "clean"
clean
```

**What it means:** gitleaks found nothing (the exact wording varies by version). `172.18.0.5` is
an address from Docker's default address pool (172.18.0.0/16 is usually the first user-defined
network, after the default bridge's 172.17.0.0/16), the same on millions of hosts, so it can stay.
`10.20.30.41` looks like a real internal address: replace it before you push.

**Why this step:** you sanitise by hand, and hand-editing misses things. The scan is the second
pair of eyes.

**Next step:** if gitleaks ever reports a leak that is already in history, deleting the file in a
new commit does not help. Rotate the secret first, then rewrite the history or publish a fresh
repository. [37](37-learn-security-devsecops.md) covers secret scanning in CI.

### Templates

**Runbook.** Written for a tired person at 3 a.m. who has never seen the system:

```
# RUNBOOK: Traefik returns 502 for one app          [L2 · Mid]
Last tested: 2026-10-01, homelab (Ubuntu 24.04, Dokploy, Traefik v3)
Symptom:     curl -sI https://app.example.com/ shows HTTP/2 502; other apps are fine
Safe to run: every command under "Diagnose" is read-only

Diagnose
1. Traefik's own view:   docker logs --since 10m dokploy-traefik 2>&1 | grep -i app
2. The app's real port:  docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
3. Its networks:         docker inspect -f '{{json .NetworkSettings.Networks}}' CONTAINER

Fix          (the port in the domain settings must match what the app listens on)
Verify       curl -sI https://app.example.com/ shows 200 from another machine
Rollback     redeploy the previous image tag from the Dokploy UI
Why          a router matched, but the backend could not be reached (handbook 25, section 7)
```

**Postmortem**, in the structure of the SRE book:

```
Title, date, authors, status (draft / reviewed / closed)
Summary          two sentences: what broke, for how long, for whom
Impact           users affected, requests failed, money or SLO budget spent
Trigger          the event that started it (often a change)
Contributing     every factor that made it possible or worse; no single "root cause", no names
Detection        how we found out, and how long that took
Resolution       what stopped the impact
Action items     | action | type (prevent / detect / mitigate) | owner | due | ticket |
Lessons          what went well, what went badly, where we got lucky
Timeline         UTC timestamps, facts only
```

**Change request**, in GitLab's format (criticality, steps with expected duration, verification,
rollback with a trigger). [21](21-case-apache-443-dokploy.md) section 5 has a complete one for the
Apache move; copy its headings for every change you make.

### Blog posts that get read

Write about problems you actually solved, with the exact error text in the title, because that is
what people paste into a search engine. Structure: symptom with the exact error → what you
guessed first and why it was wrong → the evidence that settled it → the fix → how you made sure it
won't come back. Aim for one post a month, 800–1,500 words.

Titles from your own work, ready to write:

- "Apache owned 443 and Dokploy needed it: freeing the port without breaking four sites"
- "Why `ufw deny` did not protect my published Docker port"
- "Containers couldn't resolve internal names: Docker's 8.8.8.8 fallback"
- "Making Docker, containerd and GitLab runners trust a private Harbor CA"
- "Traefik 404 versus 502: what each one tells you"
- "My CKA break-and-fix log: twenty faults and how I found them"

### Proof by stage

| Moving to | The minimum proof that makes the case |
|---|---|
| Junior | Notes repository with 30+ entries, `sysreport.sh` with a timer, the hardened VM README, the L0 exit test passed twice |
| Mid-level | Ten runbooks, the ports inventory script, a Compose stack with a tested restore, an Ansible playbook, the L1 exit test log |
| Senior | CKA, the GitLab CI → Harbor → Dokploy pipeline with a tested rollback, three postmortems, the Apache → Dokploy write-up, a Terraform repository, a blog series |
| Lead / Staff / SRE | Design docs and ADRs other teams adopted, a DR drill with measured numbers, a mentee who moved up, a talk |

### Your CV and LinkedIn

Each line is an action, a scope and a measured result. Put brackets around numbers you still need
to fill in from your own records, and never inflate them: interviewers ask follow-up questions.

| Before | After |
|---|---|
| Responsible for Apache and Docker servers | Moved [four] Apache sites off ports 80/443 to make room for Dokploy (Traefik v3) with [N] minutes of downtime and a rehearsed rollback; the runbook is now the team's standard |
| Worked with Kubernetes | Built a three-node kubeadm cluster (containerd, private Harbor registry with an internal CA); documented [20] injected faults and their fixes; passed the CKA |
| Did monitoring | Added Prometheus and Grafana alerting for disk use and failed systemd units across [N] hosts; caught [3] disk-full incidents before users noticed |
| Wrote CI pipelines | Built a GitLab CI pipeline that tags images with the commit SHA, scans them, pushes to Harbor and deploys through Dokploy with a one-click rollback |

### Job search (unlocks at milestones)

On the 3D course map, each stage milestone (and the CKA) unlocks a job-search kit once you pass its exit check and press **Mark as done** (saved only in your browser): the matching interview pack, the questions above and [ai-job-search](https://github.com/ai-job-search-dev/ai-job-search) (MIT). That tool is a set of Claude Code commands and skills (Claude Code needs a paid Claude plan or API credits) that score job posts, tailor your CV, draft cover letters, prepare interviews and track applications. It needs Python 3.10+, Bun and LaTeX.

- Setup writes your contact details, job history and salary expectations into tracked files, and GitHub forks are always public: use a private repo with the tool as `upstream`.
- Skip `linkedin-search`: it uses LinkedIn's guest endpoints, which its own README says breaks LinkedIn's terms. Use `freehire-search` (software, DevOps, remote) or add a board with `/add-portal`.
- Most bundled portal skills are Danish job boards.
- It drafts and tracks; it never submits an application. Job posts are untrusted input: review what it fetches.

---

## 11. Soft skills

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Incident Management (IMAG roles, Blameless Postmortem Culture) ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: [25 — Site down](25-playbook-site-down.md) section 10 (communicating during an outage) and [39 — Senior architecture](39-learn-senior-architecture.md) · 3) Read: the Managing Incidents chapter in the [Google SRE books](https://sre.google/books/) · 4) Practice: rewrite your last three tickets or chat questions with the templates below.

**[All stages].** Up to Mid-level, people are promoted mostly for what they can fix. From Mid to
Senior and beyond, they are promoted mostly for how they communicate, decide and work with others.
Each part below is tagged with the stage where it starts to matter; none of them stops mattering
later.

### Asking good questions

**[L0 · Fresher] onward.** A good question gets a fast answer and shows that you did your part.
Send it as one message, not "hi" followed by waiting:

```
Goal:      Free port 443 on web-01 so the Dokploy installer can run.
Problem:   The installer stops with "Port 443 is already in use".
Tried:     sudo ss -ltnp 'sport = :443' -> apache2 (pid 1234)
           sudo apache2ctl -S -> 4 name-based vhosts on *:443 (output attached)
I think:   Two vhosts are unused (no access-log lines in 30 days), two are live.
Question:  Who owns shop.example.com and intranet.example.com, and may they move to an
           internal port behind Traefik?
Urgency:   Not urgent; the change is planned for Thursday.
```

- **Timebox first:** about 30 minutes stuck, or straight away when users are affected.
- **Exact error text**, never "it doesn't work". Copy it, don't retype it.
- **Say what you ruled out**, so nobody sends you back to step one.
- **Ask in the team channel rather than a private message**, so the answer helps the next person.
- **Close the loop:** when it's solved, post what fixed it and add it to your notes.

### Writing that people read

**[L1 · Junior] onward.** Runbooks, tickets, change requests and design docs are how your work
reaches people who never meet you.

- **Bottom line first.** The first sentence says what happened or what you need. Detail comes after.
- **Write runbooks for a tired stranger**: someone at 3 a.m. who has never seen the system. Test every runbook by watching someone else follow it, silently.
- **Commands in code blocks, exact versions, absolute times with a timezone** (14:05 UTC, not "this afternoon").
- **One name per thing.** If it is "web-01" in one paragraph, it is not "the Apache box" in the next.
- **Cut a third.** Most first drafts are a third too long. Shorter documents get read.

### Status updates during incidents

**[L1 · Junior] to [L4 · Lead].** Juniors post facts into the incident channel; Mid-level
engineers write the updates for small incidents; Seniors and Leads own them for big ones.

The internal update, for engineers:

```
[INCIDENT] app.example.com returning 502 for ~40% of requests      SEV2   Update 3, 14:30 UTC
Impact:      Checkout fails for some users since 14:05 UTC.
Status:      Cause narrowed to the Traefik -> app hop. DNS, TLS and the host are fine.
Doing now:   Rolling back the 14:02 deploy (on-call engineer).
Next update: 15:00 UTC, or sooner if anything changes.
```

The stakeholder version, for people who don't need the layers:

```
Some customers cannot complete checkout since 14:05 UTC. We have found the likely cause,
a software change made at 14:02, and are undoing it now. We expect checkout to work again
by 14:45 UTC and will update you at 15:00 UTC at the latest.
```

**Why it is written this way:** a fixed cadence stops people asking "any news?" every five
minutes, which steals time from the fix. Saying what you know and what you don't builds trust.
Never promise a resolution time you can't keep; promise the next update time instead. The
outage communication part of [25](25-playbook-site-down.md) (section 10) has more templates.

### Incident commander checklist

**[L3 · Senior] and [L4 · Lead].** The incident commander coordinates and decides; they do not
type the fix. Work through the list in order:

1. **Declare** the incident: name the severity, open one channel, post the first update within 15 minutes.
2. **Assign roles**: incident commander (you, hands off the keyboard), operations lead (makes the changes), communications lead (writes the updates), scribe (keeps the timeline).
3. **Set the cadence** for updates and say it out loud.
4. **Stabilise before you investigate**: roll back, fail over, disable the feature. Decide with evidence and timebox each hypothesis.
5. **Keep a decision log** with timestamps: what was decided, by whom, on what evidence.
6. **Protect the responders**: one person changes production at a time, and every change is announced before it is made.
7. **Hand over** before people are exhausted. Nobody works an incident for twelve hours straight.
8. **Call the all-clear on criteria**: verified from the user's side, monitoring normal for an agreed time.
9. **Schedule the postmortem** within a few working days, with a named owner.

### Owning mistakes

**[All stages].** Everyone breaks production eventually. What people remember is how fast you
said so and what you did next. Report within minutes, facts first, with the fix and the
prevention:

```
Heads-up: I broke intranet.example.com at 10:12 UTC. It is fixed now.
What happened: during the port clean-up I disabled the intranet vhost (a2dissite) because its
               access log looked empty. Its traffic was logged to a different file.
Impact:        Finance could not open the monthly report page for 25 minutes. No data lost.
Fixed:         Re-enabled the vhost and reloaded Apache at 10:37 UTC. Verified with curl and
               with a user from Finance.
Prevention:    The inventory step now checks every CustomLog path in the vhost's own config,
               not just the default access.log. Runbook updated (link).
```

- **No excuses and no self-punishment.** Both make the message about you instead of the system.
- **Blameless does not mean silent.** A blameless culture fixes the system rather than the person, but you still own telling people quickly.
- **Bring the prevention**, even a small one. It turns "they broke it" into "they made it safer".

### Estimating work

**[L1 · Junior] to [L3 · Senior].** Estimates go wrong because work is not broken down and
unknowns are not named. A method that works:

1. Break the work into tasks of half a day or less.
2. Give each task three numbers: best case, likely, worst case.
3. Combine them per task as (best + 4 × likely + worst) / 6, a three-point (PERT) estimate.
4. Add waiting time for anything that depends on another team (reviews, change windows, DNS changes).
5. State your confidence and assumptions. Re-estimate when you learn something, and say early when it slips.

Example: finishing your Apache → Dokploy migration with steps 9–14 from
[35](35-deployment-patterns.md) section 1.

| Task | Best | Likely | Worst | Three-point |
|---|---|---|---|---|
| Step 9: Traefik can reach Apache on 81 | 0.5 h | 1 h | 3 h | 1.3 h |
| Step 10: a Traefik route per Apache site | 1 h | 2 h | 4 h | 2.2 h |
| Step 11: test with `curl --resolve` | 0.5 h | 1 h | 2 h | 1.1 h |
| Step 12: certificates issued by Traefik | 1 h | 2 h | 6 h | 2.5 h |
| Step 13: close 81 and 444 from outside | 0.5 h | 1 h | 2 h | 1.1 h |
| Step 14: real client IPs in Apache's logs | 1 h | 2 h | 4 h | 2.2 h |
| Change request, review and window | 2 h | 4 h | 8 h | 4.3 h |
| **Total** | **6.5 h** | **13 h** | **29 h** | **about 15 h** |

**How to say it:** "About two days of hands-on work, done within a week because the review and
the change window depend on other people. Worst case four days, if certificate issuance fights
Dokploy's own HTTP-01 handler, which [35](35-deployment-patterns.md) warns about."

### Review comments that help

**[L2 · Mid] onward.** A correct comment written as an attack still loses the argument and makes
the next review worse.

| Instead of | Write |
|---|---|
| "This will lose data." | "blocking: what happens to this volume when the service is recreated? If it's anonymous, the data goes with it. A named volume fixes it (handbook 30, section 8)." |
| "Why would you publish this port?" | "question: does this need a published port? Behind Traefik it only needs `dokploy-network`, and published ports bypass UFW." |
| "Wrong." | "suggestion: `systemctl reload` keeps connections open here; `restart` drops them." |
| (nothing about what was good) | "Nice: the rollback job is tested. I'll copy that pattern." |

- **Label the weight** of every comment: blocking, question, suggestion, nit. Approve with nits rather than blocking over style.
- **Explain why and link the source**, so the author learns the rule, not just the fix.
- **Receiving reviews:** thank, ask when something is unclear, disagree with evidence, and move long debates to a call, then write the outcome back into the review.

### Saying no with an alternative

**[L3 · Senior] onward.** Seniors protect the team's focus and the platform's safety. A bare "no"
starts a fight; a "no, but" starts a decision. The pattern: acknowledge the goal → state the risk
or cost with numbers → offer two options → let them choose.

Example: a client demands their new app "on port 443" on a server that already serves ten sites.

> "You'll get it on 443 at https://client.example.com, the same as the other ten sites. What we
> can't do is give the app the port itself, because the proxy needs 443 to serve all eleven.
> Option one: the app goes behind the proxy this week. Option two: if it truly needs raw TLS on
> its own IP, that's a second address and about two days of work. Which fits better?"

[35](35-deployment-patterns.md) section 5 covers the technical side of that conversation.

### Handover notes

**[L2 · Mid] onward.** Every on-call handover, end of shift and holiday gets a short written
note, so nothing lives only in your head:

```
HANDOVER 18:00 UTC, from on-call A to on-call B
Open:     SEV3 disk at 88% on web-02 (/var/lib/docker). Build cache pruned at 17:40; still
          growing about 1%/h from the "reports" app's logs. Ticket OPS-412.
Watch:    above 95%, follow runbooks/disk-full.md step 4 (rotate the app log).
          Do NOT prune volumes.
Done:     Harbor robot token rotated; CI green again.
Pending:  intranet.example.com certificate renews tonight through Traefik; check at 09:00.
```

---

## 12. Self-check and exit tests

> 📚 **Study path:** 1) Note: the "Ready for" lists in sections 2–6 and the placement checks in section 0 · 2) KodeKloud: Lightning Labs and Mock Exams in *Certified Kubernetes Administrator (CKA)* ([link](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Note: the module exit tests in [22](22-playbook-ports-inventory.md) section 19, [25](25-playbook-site-down.md) section 14 and [26](26-playbook-containers-k8s.md) section 13 · 4) Practice: the timed tasks below, once a quarter.

**[All stages].** Re-run this section every quarter. Answer the questions aloud before you look
anything up, then check yourself against the section named in brackets.

### Which stage am I

Your working stage is the stage of the **first exit test you fail**. The exit tests measure
skill; the "Ready for" signs in each stage section measure judgement and trust. You need both to
move up.

```
Pass the L0 exit test (30 min, no notes)?
 ├─ no ──► Fresher [L0]. Section 2. Next: Linux Basics, DevOps Pre-Requisite, sysreport.sh
 └─ yes ─► Pass the L1 exit test (port -> process, unit, config, logs in 5 min)?
            ├─ no ──► Junior [L1]. Section 3, weeks 1-4. Next: LFCS Operations and Networking
            └─ yes ─► Pass the L2 exit test (site down, broken layer with evidence, 15 min)?
                       ├─ no ──► Junior moving to Mid [L1 -> L2]. Section 4, weeks 1-4.
                       │         Next: DNS, tcpdump, the 25-playbook walk, the Traefik 502 drill
                       └─ yes ─► Pass the L3 exit test (CI -> Harbor -> Dokploy, tested rollback)?
                                  ├─ no ──► Mid-level [L2]. Section 4. Next: CKA, the pipeline
                                  └─ yes ─► Pass the L4 game day (alert, fix, published postmortem)?
                                             ├─ no ──► Senior [L3]. Section 5. Next: SLOs, DR drill
                                             └─ yes ─► Lead / Staff / SRE [L4]. Section 6.
                                                       Next: teach this ladder to someone else
```

### Questions by stage

**[L0 · Fresher]**

1. Why do you read the logs before you restart a service? (section 2, Good fresher work)
2. What does `set -euo pipefail` change in a script, and when can it surprise you? (section 2, Fresher portfolio; [27](27-learn-linux.md) section 12)
3. Why is piping a downloaded script into `sudo bash` risky, and what do you do instead? (section 2, Fresher mistakes)
4. What evidence turns "done" into done for a ticket? (section 2)
5. What do you do in the first two minutes after you realise you broke something? (section 11, Owning mistakes)

**[L1 · Junior]**

1. Name the commands that take you from a port number to the process, unit, config file and logs. (section 3, Junior incidents)
2. How can `df -h` show free space while writes fail with "No space left on device"? (section 8, Junior Q2)
3. Why does `kill -9` on whatever holds a port often fail to free it for long? (section 3, Junior mistakes)
4. What makes an escalation good, and when do you escalate? (section 3, Good junior work)
5. Why doesn't a backup count until you have restored it? (section 3, Junior mistakes)

**[L2 · Mid]**

1. List the layers of the site-down walk in order, with one command for each. (section 8, Mid Q1)
2. What does each of Traefik's 404, 502 and 504 tell you? (section 8, Mid Q5)
3. Why doesn't UFW protect a published Docker port, and what are three correct fixes? (section 8, Junior Q7)
4. What must a change request contain before you start? (section 10, Templates)
5. When is Kubernetes the wrong answer for a set of apps? (section 4, Mid-level mistakes)

**[L3 · Senior]**

1. What is the Mid-level fix and the Senior fix for the Apache vs Traefik port clash? (section 5, Senior incidents)
2. What goes into an ADR, and why write one at all? (section 5, Senior portfolio)
3. How would you know whether the platform you built is actually used? (section 5, Senior mistakes)
4. Explain a risk, cost and speed trade-off from your work in two sentences a manager would understand. (section 11, Saying no)

**[L4 · Lead]**

1. Work out the error budget of a 99.9% SLO over 30 days, in minutes. (section 6, Lead incidents)
2. What does an incident commander deliberately not do? (section 11, Incident commander checklist)
3. Name two signs of unhealthy on-call and the fix for each. (section 8, Lead Q4)
4. Why does one blameful postmortem damage the next incident? (section 6, Lead mistakes)

### Timed practical tasks

| Stage | Task | Time limit | You pass when |
|---|---|---|---|
| Fresher | The L0 exit test on a fresh VM | 30 min | All four parts done without notes |
| Junior | The L1 exit test, then fill `/var` on a test VM until a service fails | 5 min, then 20 min | Process, unit, config and log command named; the failing service found with journalctl, df and du only |
| Mid-level | The L2 exit test, then the Traefik 502 drill | 15 min, then 20 min | The broken layer named with a capture, a log line or `curl -v` output; the 502 fixed from Traefik's logs alone |
| Senior | The L3 exit test | One weekend | Pipeline runs end to end, rollback tested, write-up published |
| Lead / SRE | The L4 game day | Half a day, postmortem within 48 h | The alert found it, it was fixed, a one-page postmortem with follow-ups is published |
| Any | A mock interview with a friend, using the questions for your target stage in section 8 | 45 min | You narrated your method on every scenario and said "I don't know, here's how I'd find out" at least once without panic |

Write the date and your time for each task in your notes repository. Times that go down from one
quarter to the next are the best evidence you have that you are moving up.

---

## 13. Your personal next steps

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — in the order of the Mid-level 90-day plan in section 4 ([link](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [35 — Deployment patterns](35-deployment-patterns.md) section 1, "Finish the job" (steps 9–14) · 3) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* ([YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) for current Traefik v3 syntax · 4) Practice: the Traefik 502 drill on a test copy of your Dokploy host, then the CKA break-and-fix log.

This section is written for you as of October 2026: a DevOps engineer on on-prem Ubuntu (plus
AWS), studying with KodeKloud, on the CKA track, who just solved a real port conflict by moving
Apache to 81 and 444 so Dokploy's Traefik could own 80 and 443.

### Where you are today

**Estimate: Junior moving into Mid, [L1 · Junior] → [L2 · Mid].** The evidence:

- **L1 is mostly in place.** Your notes and the Apache investigation show you can go from a port to its process, unit, config and logs.
- **You already work like a Mid-level engineer in places.** You solved a cross-layer problem (Apache, Traefik, Docker, DNS) on a live server without losing the existing sites, and you wrote it up.
- **The L2 gaps are known and specific:** packet captures, resolver debug logs, `getent` versus `dig`, container DNS, and published ports bypassing UFW.
- **Kubernetes is in progress** (CKA track, homelab). Observability and IaC are not in your notes yet.

Confirm or correct this estimate with the placement checks in section 0 and the skills matrix in
section 7. Evidence beats this paragraph.

### Your priorities, in order

1. **The CKA.** It is your current track, the certificate most asked for in on-prem Kubernetes roles, and its troubleshooting domain is exactly L2 work. Keep at least one CKA evening a week from today, and from week 5 of the 90-day plan it gets every evening and weekend block until the exam.
2. **Finish the Apache → Dokploy migration.** It is live work, it closes real risks, and turning a workaround into a design is the clearest Mid-level proof you can produce.
3. **The L2 blind-spot tools**: tcpdump, `getent ahosts`, resolver debug logs, `curl --resolve`, netshoot. They fit the 30-minute morning reps.
4. **The L3 exit test pipeline**: GitLab CI → Harbor → Dokploy with a tested rollback, after the CKA.
5. **Observability version 1**: node_exporter, Prometheus and Grafana with the two Ops Ladder alerts.
6. **Write it up in public**: the migration postmortem, then a runbook a month.

### Finish the Dokploy migration

Moving Apache to 81 and 444 freed 80 and 443, but [35](35-deployment-patterns.md) section 1
("What it leaves open") lists what it did not finish: users reaching the legacy sites on `:444`,
certbot renewals that will fail because HTTP-01 needs port 80, ports 81 and 444 reachable around
Traefik, Apache logs full of Traefik's address instead of client IPs, and missing documentation.
Finish it in this order:

1. **Re-check which Apache sites are still used** with the method in [21](21-case-apache-443-dokploy.md) section 3. Every site you can retire is one less route to maintain.
2. **Write the change request first**, in GitLab's format, with a rollback and its trigger. [21](21-case-apache-443-dokploy.md) section 5 has a complete example.
3. **Rehearse steps 9–14 of [35](35-deployment-patterns.md) section 1 on a test VM**: Traefik reaches Apache on 81 and nothing else does, one Traefik route per Apache hostname, testing with `curl --resolve`, certificates issued by Traefik, 81 and 444 closed from outside, real client IPs back in Apache's logs.
4. **Run the change in a window**, then verify from **another machine**, because a check from the host itself proves nothing about the firewall.
5. **Then the L3 exit test:** move one of the Apache apps into a container, built by GitLab CI, pushed to Harbor and deployed by Dokploy, with a rollback you have tested ([30](30-learn-docker.md) section 11, [33](33-learn-cicd-iac-sre.md) section 2).
6. **Then think like a Senior:** write the ADR "One ingress owns 80 and 443 on every host" ([39](39-learn-senior-architecture.md)) and keep a port registry in Git (PORTS.md, [35](35-deployment-patterns.md) section 2).

The outside check for step 4, run from your laptop or another server, never from web-01 itself:

```bash
nc -vz -w 3 web-01.example.com 81
nc -vz -w 3 web-01.example.com 444
curl -sI https://shop.example.com/ | head -n 1
```

```
nc: connect to web-01.example.com (192.0.2.10) port 81 (tcp) timed out: Operation now in progress
nc: connect to web-01.example.com (192.0.2.10) port 444 (tcp) timed out: Operation now in progress
HTTP/2 200
```

**What it means:** "timed out" on 81 and 444 means the firewall drops the packets, so from
outside the legacy ports are closed. `HTTP/2 200` on the normal URL means Traefik now serves the
legacy site on 443. "Connection refused" would also be acceptable (nothing answers on that
address), but `succeeded!` means the port is still open to the world.

**Why this step:** the whole point of the migration is that Traefik is the only way in. A port
that answers from outside bypasses Traefik's TLS, logs and access rules.

**Next step:** if either port says `succeeded!`, go to step 13 of
[35](35-deployment-patterns.md) section 1 and fix the firewall or the bind address, then repeat
this check. If both are closed and every site returns 200 through Traefik, write the postmortem
and publish its sanitised version (section 10).

### Your next 14 days

| Days | What | Output |
|---|---|---|
| Day 1 | Score the skills matrix (section 7) with evidence; run the placement checks (section 0) | Matrix in your notes repository |
| Every workday morning | SadServers scenarios tagged dns, nginx or docker, alternating with 100 Days of DevOps tasks | One line per session on what you missed |
| Evening 1 each week | CKA: Core Concepts, then Install Kubernetes the kubeadm way (rebuild the homelab with containerd and `SystemdCgroup = true`), so the course never goes cold | A working homelab cluster, notes entries |
| Evening 2 each week | *Demystifying DNS*: DNS as a System, then Troubleshooting DNS (weeks 1–2 of the Mid-level plan) | Notes entries, flashcards |
| Weekend 1 | Replay your DNS case on a test VM with tcpdump, `getent ahosts`, resolver debug logs and `curl --resolve` | A five-line note and your first public runbook |
| Weekend 2 | Write the change request for steps 9–14 and rehearse steps 9–11 on a test VM | The change request in Git |
| Sunday evenings | Read the tcpdump and strace zines, then one postmortem from k8s.af | Flashcards |

### Your next 90 days

Run the Mid-level 90-day plan in section 4 with one change: the weekly CKA evening from the
14-day plan continues through weeks 1–4. The plan puts the site-down walk and proxies in weeks 3–4
(where the migration fits) and the full CKA push in weeks 5–12. The milestones to check against:

| By day | Milestone |
|---|---|
| 30 | L2 exit test passed in 15 minutes; Dokploy migration finished (steps 9–14 live, 81 and 444 closed from outside); first public runbook |
| 60 | CKA course done; homelab break-and-fix log with at least ten faults; Traefik 502 drill passed |
| 90 | CKA passed; pipeline skeleton pushing SHA-tagged images to Harbor; the Apache → Dokploy postmortem published; skills matrix re-scored |

### Your next twelve months

| Quarter | Focus | You can show at the end |
|---|---|---|
| Oct–Dec 2026 | CKA (exam in weeks 11–12 of the 90-day plan), the finished migration, the L2 tools | CKA passed or booked; the migration write-up; the L2 exit test log. You are working at Mid-level |
| Jan–Mar 2027 | L3 exit test, Ansible for Docker hosts, monitoring version 1 | One Apache app running in Dokploy from CI and Harbor with a tested rollback; an idempotent Ansible playbook; disk and failed-unit alerts |
| Apr–Jun 2027 | Terraform and one AWS associate exam, each with its project | The Terraform AWS repository; one certificate; three public postmortems |
| Jul–Sep 2027 | Observability with SLOs, the first game day, the ADR, mentoring | An SLO with burn-rate alerts; a game-day postmortem; the "one ingress per host" ADR; a junior you helped through L1. First Senior behaviours are visible |

### What not to do this year

- **No new certificates before the CKA.** Your Ops Ladder is explicit about this, and it is right.
- **Don't move the Dokploy apps to Kubernetes** just because you are learning Kubernetes. Choose by operational cost (section 4, Mid-level mistakes).
- **No long video bootcamps.** They re-explain tools you already use and never hand you a broken server.
- **Don't leave 81 and 444 open "for now".** Temporary doors become permanent ones.

### Where to go next

- **This week:** [21 — Apache 443 and Dokploy](21-case-apache-443-dokploy.md) section 8 (route the legacy Apache sites through Traefik) and [35 — Deployment patterns](35-deployment-patterns.md) section 1.
- **For the CKA:** [31 — Learn Kubernetes](31-learn-kubernetes.md) sections 20–22 and [26 — Containers and Kubernetes](26-playbook-containers-k8s.md) sections 8–10.
- **For the L2 tools:** [28 — Learn networking](28-learn-networking.md) sections 8 and 14, then [25 — Site down](25-playbook-site-down.md).
- **For the L3 exit test:** [30 — Learn Docker](30-learn-docker.md) sections 11 and 14, [33 — CI/CD, IaC and SRE](33-learn-cicd-iac-sre.md) section 2.
- **For what comes after Mid:** [39 — Senior architecture](39-learn-senior-architecture.md), [37 — Security and DevSecOps](37-learn-security-devsecops.md), [36 — Cloud and AWS](36-learn-cloud-aws.md), [38 — Databases](38-learn-databases-ops.md).
- **For the topic order across the whole handbook:** [34 — Roadmap](34-roadmap.md).
- **Every quarter:** come back here, re-score section 7, re-run section 12 and rewrite this section with your new evidence.
