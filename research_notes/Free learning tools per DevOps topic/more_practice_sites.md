# More free DevOps practice sites: gaps, 2025–2026 platforms, other ecosystems, deep links (checked 2026-11-09)

How each row was checked (read this first):
- **Opened**: the page was fetched on 2026-11-09 with `curl` or WebFetch and its text read. **JS-only**: the URL returned HTTP 200 but the page is a JavaScript app; the title and status were confirmed and the content came from the vendor's docs or repo. **API**: facts read from a public JSON endpoint. **Repo**: star count, last push and README read through the GitHub API (`gh api`) on 2026-11-09; "pushed" counts any push. **Snippet**: only a search-result snippet was seen.
- Nothing was signed up for, logged into, submitted, downloaded or run. Self-hosted repos are described from their README only.
- **Exclusions applied.** All 132 rows in `research/practice.json` were removed from the results, along with its `excluded_after_research`, `dead_or_renamed` and `paid_only` lists and every host in `known_domains.txt`.
- **Domain interpretation.** `known_domains.txt` lists `github.com`, `killercoda.com`, `grafana.com` and `docs.crowdsec.net`. A GitHub repo is treated as new unless that repo is already in practice.json. A course hosted on Killercoda or Grafana is recorded as a **deep link** under the existing `killercoda` or `grafana-play` id. A creator course may later be promoted to its own row, but it is not counted as a new site. `playground.crowdsec.net` and `academy.crowdsec.net` are new hosts, but `docs.crowdsec.net` is known, so they are flagged as such.
- **Assigned by me.** Levels (L0–L4), roadmap topic ids, ranking and proposed `id`s are my judgement for this reader, not claims made by the sites.
- **Runs:**
  - `browser`: the vendor hosts it.
  - `vendor-account`: a lab account the vendor provisions; it cannot bill you.
  - `throwaway-vm`: you self-host it on a lab VM you delete.
  - `own-cloud-account`: your own cloud account, which can bill you.

## Q1. Which new free practice sites are worth adding, ranked by value for this reader?

### Takeaway
I verified 27 new free sites. Another 3 are partly verified, and 4 are on a watch list. The best finds are:
- **Volunteer-built browser lab courses:**
  - ProLUG's Linux, fail2ban, logging and CKA-troubleshooting labs.
  - Saiyam Pathak's CNPE labs, which give the first free **Flux** and **OpenCost** browser practice.
  - Chad Crowell's CKA scenarios.
- **Public sandboxes that fill named gaps:**
  - MinIO Play (object storage).
  - The Incus online demo (a real 30-minute VM, the closest free thing to Proxmox practice).
  - CrowdSec Playground (grok and parser testing).
  - OpenSearch Playground (the same Dashboards UI as Wazuh).
  - The public Argo CD demo.
- **Datadog Learning Center:** a vendor-provisioned lab account with no card.

Nothing new and free covers Dokploy, Swarm break-fix, macOS, change management, GRUB recovery or SadServers-style cloud break-fix. See Q2.

### Cited Findings

Ranked table. Proposed ids are new; "Topics" are roadmap.json ids.

| # | Proposed id | URL | Practise | Free / limits | Sign-up / card | Runs | Maintained | Level | Topics | Check |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `prolug` | https://professionallinuxusersgroup.github.io/course-books/ (labs: https://killercoda.com/het-tanis) | Linux admin course: 12+ units with worksheets and labs; Killercoda labs for fail2ban+Loki, fail2ban alerting, rsyslog (+TLS), UFW, server startup process, lsof troubleshooting, Alertmanager, Alloy, Vault, Terraform, CKA troubleshooting | Free; certificate only for scheduled Discord runs | Killercoda free account | browser | Labs repo pushed 2026-08-07 (84★) | L1–L3 | systemd-units, journald-logs, kernel-boot, host-firewall, ssh-hardening, crowdsec-fail2ban, logs-loki, prometheus-alertmanager, ansible, secrets, k8s-troubleshooting | Opened + Repo |
| 2 | `cnpe-labs` (or killercoda deep link) | https://killercoda.com/saiyampathak/course/cnpe ; repo https://github.com/saiyam1814/CNPE | 28 exam-style scenarios: ResourceQuota, HPA, NetworkPolicy, **OpenCost rightsizing**, Argo CD, Argo Rollouts canary/blue-green, Tekton, Crossplane, Grafana, PrometheusRule, Jaeger/OTel, **"broken stack remediation"**, RBAC, PSS, Gatekeeper, Kyverno+Cosign, Istio, Linkerd, **Flux HelmRelease** | Free | Killercoda free account; or local kind | browser / throwaway-vm | Created 2026-07-16, pushed 2026-09-21 (4★, new) | L3–L4 | gitops-argocd, deployment-strategies, platform-engineering, k8s-security, prometheus-grafana, alerting, cloud-architecture (FinOps) | Opened + Repo |
| 3 | `crowell-killercoda` (or killercoda deep link) | https://killercoda.com/chadmcrowell ; repo https://github.com/chadmcrowell/killercoda-scenarios | 53 CKA plus 73 CKAD scenario folders. The repo also holds 179 "kubeskills-daily" folders, but their Killercoda pages were not opened. Examples: "Troubleshoot a NotReady Node", kubelet-status, broken-path, pvc-stuck, upgrade-k8s, upgrade-kubelet, prepare-kubeadm, pki-essentials, modify-cluster-dns, linux-services | Free | Killercoda free account | browser | Pushed 2026-05-25 (6★) | L2–L3 | kubeadm-cluster, cka-exam, k8s-troubleshooting, k8s-incidents, k8s-scheduling-storage, k8s-services-dns | Opened + Repo |
| 4 | `datadog-learning-center` | https://learn.datadoghq.com/ | Courses run "on real cloud compute instances" with a provisioned Datadog account: Agent on host and Docker, metrics, monitors, dashboards, APM, logs, Kubernetes | Free; each course enrolment lasts 30 days, then re-enrol | Free account; no card mentioned | vendor-account | Live; new courses listed | L1–L3 | prometheus-grafana, alerting, logs-loki, slo, docker-basics, k8s-architecture | Opened |
| 5 | `incus-demo` | https://linuxcontainers.org/incus/try-it/ | A temporary Linux **VM** on a remote Incus cluster: instances, snapshots, storage, networks, and a real systemd and journald inside a VM | Free; 30-minute sessions; at most 5 per IP; 4 CPU, 8 GiB RAM, 50 GiB disk; very little internet; terms say it is "solely provided to evaluate Incus" | None (accept terms) | browser | API showed `server_status: 0`, 2 of 64 instances in use | L1–L3 | proxmox-ve, systemd-units, journald-logs, start-here | Opened + API |
| 6 | `minio-play` | https://play.min.io (console at :9443) | Public S3-compatible sandbox: buckets, policies, versioning, `mc` CLI (pre-set alias `play`), restic or rclone S3 targets | Free; all data is public and ephemeral | None (docs publish well-known credentials) | browser | Console title "MinIO AIStor Console", live | L1–L2 | object-storage-minio, backups-restore, backup-tools | Opened (JS) + docs snippet |
| 7 | `crowdsec-playground` | https://playground.crowdsec.net/ | In-browser (WASM) CrowdSec grok debugger, grok pattern library and notification-template tester. CrowdSec's own troubleshooting docs say "Test your logs in CrowdSec Playground" | Free | None | browser | Source repo crowdsecurity/crowdsec-wasm-playground pushed 2026-09-23 | L2 | crowdsec-fail2ban, journald-logs, text-tools | JS-only + Repo + docs |
| 8 | `opensearch-playground` | https://playground.opensearch.org/ | Anonymous, read-only OpenSearch Dashboards with sample logs and flights data: Discover, query languages, visualisations. It is the same UI family as the Wazuh dashboard | Free; read-only (cannot save) | None (redirects to /auth/anonymous) | browser | Updated with each OpenSearch release | L1–L2 | wazuh, wazuh-siem, logs-loki, security-response | Opened (redirect) + blog snippet |
| 9 | `argocd-demo` | https://cd.apps.argoproj.io/ | The Argo CD project's own live instance: app list, sync and health status, diffs, history | Free; anonymous read; logging in needs GitHub | None for read | browser | API returned live applications; local logins disabled | L1–L2 | gitops-argocd, deployment-strategies | API |
| 10 | `devops-with-docker-uh` | https://devopswithdocker.com/ (now courses.mooc.fi/org/uh-cs/courses/devops-with-docker-spring-2026) | University of Helsinki MOOC: Dockerfiles, Compose, volumes, networking, security and optimisation. You submit Dockerfiles and compose files | Free; ECTS only for eligible students | mooc.fi account for submissions | throwaway-vm | 2026 edition live (redirect); material repo pushed 2026-02-12 (171★) | L0–L2 | docker-basics, compose-volumes, dockerfile, docker-networking, container-hardening | Opened (JS) + Repo + snippet |
| 11 | `devops-with-kubernetes-uh` | https://devopswithkubernetes.com/ (→ …/devops-with-kubernetes-2026) | Same university: k3d locally, then GKE in part 3, GitOps, monitoring, serverless | Free | mooc.fi account | throwaway-vm, then own-cloud-account (GKE can bill) | 2026 edition live; repo pushed 2026-02-13 (115★) | L2–L3 | k8s-workloads, k8s-networking, helm-kustomize, gitops-argocd, prometheus-grafana | Opened (JS) + Repo |
| 12 | `explain-dalibo` | https://explain.dalibo.com/ | Paste `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` output and read the plan visually; sample plans are included | Free; a standalone single-HTML version exists for private plans | None | browser | Live | L2–L3 | db-incidents, db-basics | Opened |
| 13 | `network-fundamentals-lab` | https://github.com/gnu-gnu/network-fundamentals-lab | Containerlab plus netshoot break-fix labs where the default state is broken. You reproduce, observe with tcpdump, traceroute and ip, then fix with one line. Labs cover routing, NAT, nftables and FRR, and each has a WALKTHROUGH answer key | Free (no licence file) | None | throwaway-vm | Created 2026-07-13, pushed 2026-10-24 (133★). **README is in Korean** | L1–L3 | net-basics, routing-nat, packet-capture, network-problems, host-firewall | Repo |
| 14 | `robusta-k8s-demos` | https://github.com/robusta-dev/kubernetes-demos | One `kubectl apply` per failure: CrashLoopBackOff, OOMKilled, CPU throttling, Pending (nodeSelector), failed Helm release, and more | Free (MIT) | None | throwaway-vm | Pushed 2026-06-30 (37★) | L2 | k8s-troubleshooting, k8s-incidents, memory-oom | Repo |
| 15 | `troubleshoot-k8s-like-a-pro` | https://github.com/vellankikoti/troubleshoot-kubernetes-like-a-pro | 35 scenarios with a runner script; 30 produce visible failure states; 2 need a NetworkPolicy CNI | Free (no licence file) | None | throwaway-vm | Pushed 2026-04-07 (44★) | L1–L3 | k8s-troubleshooting, k8s-networking, k8s-scheduling-storage | Repo |
| 16 | `netdata-demo` | https://app.netdata.cloud/spaces/netdata-demo | Live per-second metrics from real demo nodes (Apache, NGINX, PostgreSQL, Redis and more). Practise reading CPU, disk, network and PSI during the 60-second checklist | Free | None for the demo space (per Netdata); some functions may need sign-in | browser | Live | L1–L2 | slow-system, perf-deep-dive, disk-io, memory-oom | Opened (JS) + snippet |
| 17 | `sans-holiday-hack` | https://www.sans.org/cyber-ranges/holiday-hack-challenge | Free annual browser game with terminal challenges, including "Cloud & Infrastructure" and "Networking & Systems". The 2025 game is playable as a warm-up | Free | Free SANS account | browser | 2026 game not open yet; submissions due 2027-01-05 | L1–L3 | security-response, packet-capture, text-tools | Opened |
| 18 | `missing-semester` | https://missing.csail.mit.edu/2026/ | MIT course, 2026 edition: shell, command-line environment, debugging and profiling, Git, packaging, code quality. Each lecture page has an Exercises section | Free; videos on YouTube | None | throwaway-vm | 2026 edition | L0–L1 | shell-fhs, bash-scripting, git-basics, text-tools | Opened |
| 19 | `40-days-of-kubernetes` | https://github.com/piyushsachdeva/CKA-2024 | Piyush Sachdeva's (The CloudOps Community, India) CKA YouTube series with daily assignments; kubeadm and CKA tasks | Free | None | throwaway-vm | Pushed 2025-07-25 (1,211★); challenge marked completed | L1–L3 | kubeadm-cluster, cka-exam, k8s-workloads | Repo |
| 20 | `azure-monitor-lab` | https://github.com/Azure-Samples/azure-monitor-lab | Microsoft sample: one resource group, Bicep or Terraform, 69 scenarios. "Deploy it, poke around, break it, restore it, and tear it down" | Free code; **Azure costs are yours** | Your Azure subscription | own-cloud-account | Created 2026-05-15, pushed 2026-11-07 (39★, MIT) | L3 | cloud-architecture, alerting, slo, logs-loki | Repo |
| 21 | `controlplane-simulator` | https://github.com/controlplaneio/simulator | Builds a Kubernetes cluster in your AWS account, then runs scenarios that misconfigure it or leave it vulnerable. Walkthroughs are from the 2023 CNCF CTF | Free (Apache-2.0); **AWS costs are yours** | Your AWS account | own-cloud-account | Pushed 2024-09-02 (1,009★); README promotes a hosted waitlist (kubesim.io) | L3–L4 | k8s-security, security-response | Repo |
| 22 | `grafana-quest-world` (or grafana-play deep link) | https://killercoda.com/grafana-labs/course/workshops/adventure ; repo https://github.com/grafana/adventure | "Quest World" text adventure: metrics and logs challenges on the LGTM stack. Each player action is emitted as a trace span | Free (open source) | Killercoda free account, or local Docker Compose plus Python 3.12 | browser / throwaway-vm | Blog 2024-11-21; repo pushed 2026-10-29 (52★) | L0–L1 | prometheus-grafana, logs-loki | Opened + Repo |
| 23 | `database-build` | https://database.build/ | Postgres running in the browser (a Supabase PGlite experiment): create schemas and run SQL | Free | Snippet suggests sign-in for AI features (not verified) | browser | Live | L0–L1 | db-basics | Opened |
| 24 | `k8s-troubleshooting-lab-saif` | https://github.com/Saif-hadd/Kubernetes-Troubleshooting-Lab | 15 scenarios with an RCA template (Minikube, Kind or EKS) | Free (MIT) | None | throwaway-vm (EKS optional, bills) | Created 2026-07-15 (30★, new) | L2–L3 | k8s-troubleshooting, postmortems | Repo |
| 25 | `netbox-demo` | https://demo.netbox.dev/ | Public NetBox (IPAM and DCIM) demo: prefixes, VLANs, racks, devices, cables | Free | Create a user on the demo instance | browser | Live ("demo instance of NetBox for public use") | L1–L2 | net-basics, oss-toolbox | Opened |
| 26 | `backstage-demo` | https://demo.backstage.io/ | Public Backstage developer portal: catalog, templates, TechDocs | Free | None | browser | Live | L2–L3 | platform-engineering | Opened (title) |
| 27 | `ctftime` | https://ctftime.org/event/list/upcoming | Calendar of free online CTFs: 25 events in Nov–Dec 2026. None is labelled DevOps, so check each event page | Free | Per event | browser | Live | L2–L4 | security-response, container-hardening | Opened |

Partly verified (useful, but a key fact is missing):

| Proposed id | URL | What I could confirm | Missing | Topics |
|---|---|---|---|---|
| `elastic-demo-labs` | https://www.elastic.co/demo-gallery/observability-logs | "Observability 101" lessons (15 min) embed `play.instruqt.com/embed/elastic-pmm/invite/...` browser labs | Whether a sign-up is needed; page doesn't say | logs-loki, alerting |
| `crowdsec-academy` | https://academy.crowdsec.net/ | 9 free courses with "no sign-up". "Deploying CrowdSec in Kubernetes" is billed as hands-on | Mostly video, not labs | crowdsec-fail2ban |
| `helsinki-mooc-details` | (rows 10–11) | The 2026 editions exist (both domains redirect) | Deadlines and the exact submission flow: the course page is JS-only | — |

Supporting citations for the table:
- ProLUG Killercoda labs are free in the browser after creating an account; the Big Book of Labs is "used by 10,000+ engineers"; certificates are given only for runs through the ProLUG Discord — [search snippets of ProLUG course books and Leanpub listing](https://professionallinuxusersgroup.github.io/course-books/) (page opened: unit list with Intro/Worksheet/Lab for File Operations, Storage, Firewalls, Package Management, Containerization, Kubernetes, Monitoring, Baselines). Lab list read from [het-tanis/prolug-labs](https://github.com/het-tanis/prolug-labs). Killercoda pages such as [109 fail2ban with log monitoring](https://killercoda.com/het-tanis/course/Linux-Labs/109-fail2ban-with-log-monitoring) returned 200, title "Let's do Linux Configurations | Het-Tanis ProLUG Labs". The 109 lab steps are "Install and configure fail2ban → Loki and Grafana → Promtail → Dashboard". Lab 107 "Server Startup Process" asks for the kernel version, `/proc/cmdline` and systemd startup — [index.json](https://github.com/het-tanis/prolug-labs/tree/HEAD/Linux-Labs/107-server-startup-process).
- CNPE README: "27 chapter labs and a standalone Flux alternative (28 scenarios) … run them free in the browser on Killercoda, or locally on kind"; "All 28 scenarios have passing local runs from 20-21 September 2026" — [saiyam1814/CNPE](https://github.com/saiyam1814/CNPE); course page title "CNPE — Hands-on Exam Scenarios | Saiyam Pathak | Killercoda" — [Killercoda](https://killercoda.com/saiyampathak/course/cnpe).
- Chad Crowell scenario folders (cka/kubelet-status, node-notready, broken-path, pvc-stuck, upgrade-k8s …) — [chadmcrowell/killercoda-scenarios](https://github.com/chadmcrowell/killercoda-scenarios); [Troubleshoot a NotReady Node](https://killercoda.com/chadmcrowell/course/cka/node-notready) returned 200.
- Datadog: "Learn by coding on real cloud compute instances on our free interactive platform"; the Learning Environment course says "Log in to Datadog with the account provisioned for you", "Enroll for free", "your enrollment in this course ends after 30 days. You can re-enroll at any time" — [Datadog Learning Center](https://learn.datadoghq.com/), [The Learning Environment](https://learn.datadoghq.com/courses/the-learning-environment).
- Incus terms: "temporary access to a Linux system running in a virtual-machine", "Session limit of 30 minutes", "Maximum of 5 concurrent sessions per IP", "4 CPU, 8 GiB of RAM and 50 GiB of disk space", "Extremely restricted internet access", "solely provided to evaluate Incus" — [incus-demo /1.0/terms](https://incus-demo.linuxcontainers.org/1.0/terms); status JSON `server_status 0, instance_count 2, instance_max 64` — [incus-demo /1.0](https://incus-demo.linuxcontainers.org/1.0); try-it page — [linuxcontainers.org](https://linuxcontainers.org/incus/try-it/). A search snippet reported the page once showed "down for maintenance", so availability may be intermittent.
- MinIO: "MinIO maintains a sandbox instance of the community server at https://play.min.io", `mc` is "pre-configured with https://play.min.io, aliased as 'play'", files uploaded "should be considered public" — snippets of [MinIO docs mirrors](https://minio.pigsty.io/minio/linux/index.html) and [mc alias import docs](https://docs.min.io/minio/baremetal/reference/minio-mc/mc-alias-import.html). On 2026-11-09 the console at https://play.min.io:9443/ returned 200, title "MinIO AIStor Console". *Snippet-level for the docs.*
- CrowdSec Playground is linked from CrowdSec's troubleshooting doc ("Test your logs in CrowdSec Playground") — [crowdsec-docs issue_lp_no_logs_parsed.md](https://github.com/crowdsecurity/crowdsec-docs/blob/main/crowdsec-docs/unversioned/troubleshooting/issue_lp_no_logs_parsed.md). The source tree has grokDebugger, grokLibrary and notificationTemplate components and a WASM build — [crowdsec-wasm-playground](https://github.com/crowdsecurity/crowdsec-wasm-playground).
- OpenSearch: "anonymous, read-only access … preconfigured sample data"; saving visualisations "is not available … because it is read-only"; it runs on EKS and is updated each release — [OpenSearch blog (snippet)](https://opensearch.org/blog/opensearch-playground/). On 2026-11-09 the root URL returned 302 to `/auth/anonymous` and then 200 at `/app/home`, title "OpenSearch Dashboards".
- Argo CD demo: `/api/v1/settings` returned `userLoginsDisabled: true` with a GitHub Dex connector, and `/api/v1/applications` returned application items without auth — [cd.apps.argoproj.io](https://cd.apps.argoproj.io/).
- Helsinki: devopswithdocker.com redirected to `courses.mooc.fi/org/uh-cs/courses/devops-with-docker-spring-2026` and devopswithkubernetes.com to `…/devops-with-kubernetes-2026` (curl, 2026-11-09). Repo descriptions: "Course material for the DevOps with Kubernetes free MOOC by the University of Helsinki" — [kubernetes-hy](https://github.com/kubernetes-hy/kubernetes-hy.github.io); part 3 files are "introduction-to-gke", "deployment-pipeline", "gke-features" (older material). "Most of the exercises will be focused on a Dockerfile and/or docker-compose.yml" — [course mirror (snippet)](https://hngxapi-v1.onrender.com/getting-started).
- Dalibo: "For best results, use EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)"; a "standalone version … simple all-included .html file" — [explain.dalibo.com](https://explain.dalibo.com/).
- network-fundamentals-lab README: each lab follows "concept → topology → reproduce (broken) → observe with tcpdump/traceroute/ip → cause → one-line fix → lesson"; containerlab plus nicolaka/netshoot; FRR for dynamic routing; "broken is the default". This is my translation from Korean — [gnu-gnu/network-fundamentals-lab](https://github.com/gnu-gnu/network-fundamentals-lab).
- robusta README: "Practice Kubernetes troubleshooting with realistic error scenarios. Each scenario is run with `kubectl apply`" — [robusta-dev/kubernetes-demos](https://github.com/robusta-dev/kubernetes-demos).
- vellankikoti README: "35 real-world Kubernetes issues", "30 scenarios produce clear failure states" — [repo](https://github.com/vellankikoti/troubleshoot-kubernetes-like-a-pro).
- Netdata: "a public area where you can try the platform without signing up"; rooms for Apache, NGINX, PostgreSQL, Redis… — [Netdata blog/docs (snippet)](https://learn.netdata.cloud/docs/getting-started/live-demos). A forum user said some "functions need sign in" — [Cloudron forum (snippet)](https://forum.cloudron.io/topic/1125/netdata-real-time-monitoring/24).
- SANS: "FREE, hands-on cybersecurity challenges for every skill level"; "The game isn't open yet"; submission deadline January 5, 2027; skill areas include "Cloud & Infrastructure" and "Networking & Systems" — [SANS Holiday Hack](https://www.sans.org/cyber-ranges/holiday-hack-challenge).
- Missing Semester 2026 lecture list (shell, command-line environment, debugging and profiling, version control, packaging…); the debugging page has an `<h1 id="exercises">` section — [missing.csail.mit.edu/2026](https://missing.csail.mit.edu/2026/), [debugging-profiling](https://missing.csail.mit.edu/2026/debugging-profiling/).
- 40DaysOfKubernetes: "notes, diagrams, assignments, and resources from the CKA course published on YouTube"; "challenge has been successfully completed" — [piyushsachdeva/CKA-2024](https://github.com/piyushsachdeva/CKA-2024).
- Azure Monitor Lab: "69 demo scenarios", "Deploy it, poke around, break it, restore it, and tear it down" — [Azure-Samples/azure-monitor-lab](https://github.com/Azure-Samples/azure-monitor-lab).
- ControlPlane simulator: "creates a Kubernetes cluster for you in your AWS account; runs scenarios which misconfigure it and/or leave it vulnerable" — [controlplaneio/simulator](https://github.com/controlplaneio/simulator).
- Grafana Quest World: an online Killercoda sandbox with a free account, or local Docker Compose and Python 3.12+; "fully open source" — [Grafana blog 2024-11-21](https://grafana.com/blog/metrics-logs-traces-and-mayhem-introducing-an-observability-adventure-game-powered-by-grafana-alloy-and-otel/); Killercoda link in [grafana/adventure README](https://github.com/grafana/adventure).
- database.build meta: "In-browser Postgres sandbox with AI assistance", "a Supabase experiment" — [database.build](https://database.build/).
- NetBox: "This is a demo instance of NetBox for public use. Click here to create a new user account" — [demo.netbox.dev](https://demo.netbox.dev/login/).
- CTFtime upcoming list: 25 Jeopardy events plus one hack-quest in Nov–Dec 2026; no DevOps-specific labels — [CTFtime](https://ctftime.org/event/list/upcoming).
- Saif-hadd: "15 production-grade scenarios … runnable on Minikube, Kind, or Amazon EKS" with an SRE RCA template — [repo](https://github.com/Saif-hadd/Kubernetes-Troubleshooting-Lab).

### Inferences
- **Practice Arena additions.** Rows 1–9 are the strongest additions because they run in a browser (or a provisioned account) and need no card. Rows 1–3 and 22 are Killercoda courses. If the handbook keeps one row per host, list them as `killercoda` deep links and name the creator in the label.
- **Wazuh link.** OpenSearch Playground is the cheapest way to rehearse the Wazuh dashboard: Wazuh's indexer and dashboard are forks of OpenSearch. This is my inference; the site does not say it.
- **Proxmox stand-in.** Incus is the closest free browser stand-in for Proxmox VE practice: VMs, snapshots, storage pools and bridges. The terms limit use to evaluating Incus, so label it "try virtualisation concepts", not general Linux practice.
- **Throwaway VMs only.** Rows 13–15, 19 and 24 belong in a "run in a throwaway VM" sub-list. Rows 20–21 need the handbook's bill-risk warning (own-cloud-account).

### Gaps
- I could not open the Datadog course catalogue (HTTP 404 on `/collections/current-courses`), so I have no list of troubleshooting-specific courses.
- For the Helsinki courses, MOOC.fi pages are JS-only: 2026 deadlines and whether the course is open-ended were not confirmed.
- database.build sign-in requirements came only from the meta description.

## Q2. What now exists for the gaps the handbook lists as having no free practice?

### Takeaway
- **Partly closed:** object storage, CrowdSec/fail2ban, systemd/journald, cgroups, Postgres slow queries, and Proxmox-style virtualisation (via Incus).
- **Still open (no free hands-on site found):** Dokploy, Docker Swarm break-fix, macOS admin, change management, GRUB/boot recovery and SELinux troubleshooting. The same holds for a free hosted SadServers-style cloud platform.

### Cited Findings
- **Dokploy, Docker Swarm and Traefik.**
  - No dedicated free site. A search found only paid Pluralsight/ACG Swarm labs and a forum walkthrough — [search results incl. Docker forum walkthrough](https://forums.docker.com/t/docker-swarm-series-5th-troubleshooting/136792).
  - Nearest free options are deep links (Q5): SadServers [/labs/traefik/](https://sadservers.com/labs/traefik/) (guide, troubleshooting and cheatsheet pages) and iximiuz Traefik ingress challenges.
  - "Lyon: Migrate Ingress-NGINX to Traefik" is **Paid** on SadServers — [SadServers scenarios list](https://sadservers.com/scenarios).
  - A brand-new repo offers "Offline break/fix labs for DevOps interviews: Linux, Docker Swarm, Kubernetes, Terraform/Terragrunt. Ticket, hints, ./lab verify". It was created 2026-11-07 and has 3★; watch it, do not add yet — [RomanVihovsky/devops-troubleshooting-labs](https://github.com/RomanVihovsky/devops-troubleshooting-labs).
- **Cloud break-fix, SadServers style.**
  - DevOps CTF advertises "Free to play · No setup · Real terminals", "150+ Hands-on Challenges", AWS/GCP/Azure, Terraform and CI/CD. Its creator is Gokul AP — [devops-ctf.com](https://www.devops-ctf.com/).
  - However, its app host `ctf.devops-ctf.com` is a CNAME to an `ap-south-1` ELB that **did not resolve** on 2026-11-09, so the platform is unverified (watch list).
  - SadServers has free AWS-flavoured scenarios: "Istanbul: Delete unattached AWS EBS volumes" and "Auckland: S3 delete & archive old backups" (Email access tier). How they emulate AWS was not checked — [SadServers scenarios](https://sadservers.com/scenarios).
  - Do-it-yourself in your own account: Azure Monitor Lab (Q1 row 20) and small new Azure PaaS troubleshooting repos by yeongseon. These are 0–4★, created April 2026 — [azure-paas-troubleshooting-labs](https://github.com/yeongseon/azure-paas-troubleshooting-labs).
- **macOS.**
  - Jamf 100 is "free and self-paced" but is video and text lessons. Hands-on needs your own Jamf Pro instance — [Jamf 100 (snippet)](https://www.jamf.com/training/100/).
  - HTB Academy "macOS Fundamentals" exists but needs your own Mac and is not confirmed free — [HTB Academy (snippet)](https://academy.hackthebox.com/course/preview/macos-fundamentals).
  - No free macOS practice site found.
- **Databases.**
  - explain.dalibo.com (Q1 row 12) and database.build (row 23) are new.
  - SadServers free scenarios cover Postgres slow queries ("Luxor"), Postgres writes ("Manhattan", public), Mongo replica sets ("Suzhou") and MySQL restore; Redis replication ("Tunis") is paid — [SadServers scenarios](https://sadservers.com/scenarios). See Q5.
  - iximiuz has "Reclaim a Retained PV with a New PVC and Restore a Lost MariaDB Database" — [iximiuz](https://labs.iximiuz.com/challenges/reclaim-retained-pv-with-new-pvc-and-restore-lost-mariadb-database-783fe3ae).
  - No free hosted Postgres replication/failover lab was found beyond SadServers "Helsingør" (already listed). Pluralsight's failover lab is subscription — [Pluralsight (snippet)](https://www.pluralsight.com/labs/aws/postgresql-disaster-recovery-failover).
- **Proxmox and virtualisation.**
  - NDG's browser "Sandbox for Proxmox VE" is paid (75 USD for four months, per snippet) — [NDG (snippet)](https://www.netdevgroup.com/online/courses/open-source/ndg-sandbox-for-proxmox-ve).
  - The Incus demo (Q1 row 5) is the free nearest option.
- **Backups and object storage.**
  - MinIO Play (row 6) and the SadServers backup scenarios: "Alexandria: The Vanishing Backups" (free) and "Montevideo: restore test snapshot would clobber production" (paid) — [SadServers](https://sadservers.com/scenarios).
- **CrowdSec and fail2ban.**
  - CrowdSec Playground (row 7) — [docs reference](https://github.com/crowdsecurity/crowdsec-docs/blob/main/crowdsec-docs/unversioned/troubleshooting/issue_lp_no_logs_parsed.md).
  - ProLUG labs "109-fail2ban-with-log-monitoring" and "110-fail2ban-with-metric-alerting" — [prolug-labs](https://github.com/het-tanis/prolug-labs).
- **Change management.**
  - The only IT-ops simulation found ("ITIL 4 in Action", itSMF UK) was free only to itSMF UK members, and that event had passed — [itSMF UK (snippet)](https://www.itsmf.co.uk/event/masterclass-itil-4-in-action-simulation-oct19/).
  - The Management 3.0 change game is a free printable card game, not IT-specific — [Management 3.0 (snippet)](https://management30.com/blog/gamifying-change-the-change-management-game/).
- **systemd and journald.**
  - New deep links: SadServers "Valladolid" (log-cleaner.service) and "Vienna" (vanishing process); iximiuz "Create a systemd Service", "Start a systemd Service on the First Connection", "Troubleshoot a Worker Service That Keeps Disappearing", "Troubleshoot a Log Shipping Daemon That Refuses to Start". All are listed in Q5.
  - The Incus VM gives a real systemd and journald to experiment on.
- **Linux boot and GRUB.**
  - Nothing free in a browser that lets you break a bootloader.
  - ProLUG lab 107 only *inspects* boot (`/proc/cmdline`, systemd startup) — [index.json](https://github.com/het-tanis/prolug-labs/tree/HEAD/Linux-Labs/107-server-startup-process).
  - LabEx has a "Troubleshoot the RHEL Boot Process" lab, but labex.io is already known and its free status is unconfirmed — [LabEx (snippet)](https://labex.io/tutorials/rhel-troubleshoot-the-rhel-boot-process-589253).
- **SELinux.**
  - Red Hat's RHEL interactive labs list "Secure containers with SELinux (Udica)" (10 min). The page says you must log in to a Red Hat account — [Red Hat RHEL labs](https://www.redhat.com/en/interactive-labs/enterprise-linux).
  - The iximiuz "RHCSA prep … broken" challenges are about man-db, PATH, sudo and scripts, not SELinux — [iximiuz broken-1](https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-1-7a6c4e17).

### Inferences
- The handbook's `gaps` list can drop "object storage", "CrowdSec" and "Proxmox (none at all)". It should keep Dokploy/Swarm, macOS, change management, GRUB and SELinux. For those, the honest recommendation stays "throwaway VM plus the handbook's own drills".
- For change management, the existing `wheel-of-misfortune` and `incident-challenge` rows remain the nearest practice. Nothing new qualifies.

### Gaps
- I could not confirm whether SadServers' AWS scenarios (Istanbul, Auckland) use real AWS or an emulator.
- DevOps CTF could not be verified: the app host does not resolve. Re-check later; if it comes back, it would be the first free SadServers-style cloud platform.
- Red Hat lab deep URLs are `developers.redhat.com/content-gateway/link/<n>` redirectors. I could not map each one to its lab reliably, so only the listing page is cited.

## Q3. Which new or rising 2025–2026 platforms, including creator-promoted ones, are real and free?

### Takeaway
The 2025–2026 movement is not new SaaS. Two other things changed:
- **Creators publish on Killercoda and GitHub:** Saiyam Pathak (CNPE, July 2026), Chad Crowell, ProLUG/Het Tanis, Piyush Sachdeva and Grafana.
- **Established platforms added events and "labs" sections:** SadServers' Advent of Sysadmin 2025 and its /labs pages; iximiuz's Klustered series and RHCSA prep; DevOps Daily's Advent of DevOps.

New SaaS claims (DevOps CTF, Rootly Academy) could not be verified.

### Cited Findings
- **SadServers Advent of Sysadmin 2025.** A 12-day calendar (1–12 December 2025) that drew about 10,000 people. Clues and solutions were later published, and "Karakorum" (Pro) was temporarily opened to all — [sadservers.com/advent](https://sadservers.com/advent), [SadServers 2025 year in review](https://docs.sadservers.com/blog/2025-year-in-review/) (snippets). The tag page lists 12 scenarios — [tag/advent2025](https://sadservers.com/tag/advent2025) (opened).
- **SadServers "Labs by technology".** Pages for systemd, Traefik, Postgres, MySQL, DNS, SSL/TLS, disk volumes, Harbor, Docker, etcd, Redis and others, each with guide, troubleshooting and cheatsheet sub-pages — [sadservers.com/labs](https://sadservers.com/labs) (opened).
- **DevOps Daily "Advent of DevOps".** 25 daily challenges from 1 December 2025, "completely free, open-source, and community-driven" — [dev.to post 2025-11-30](https://dev.to/devopsdaily/advent-of-devops-25-days-to-level-up-your-devops-game-2fb5); https://devops-daily.com/advent-of-devops returned 200.
- **iximiuz "Klustered".** An intro, a 101 series (a–f), Levels 1–4 and "rawkode" rounds. Level One: "The cluster is broken. Fix the plumbing to bring the app to life" — [iximiuz klustered-l1](https://labs.iximiuz.com/challenges/klustered-l1-b71142bd). The original rawkode-academy/klustered repo was last pushed 2022-12-20 — [repo](https://github.com/rawkode-academy/klustered). The live, playable version is on iximiuz.
- **Saiyam Pathak (Kubesimplify) CNPE labs.** Created July 2026 — [saiyam1814/CNPE](https://github.com/saiyam1814/CNPE). Kubesimplify also has an interview-prep repo (20★, pushed 2026-01-13) — [kubesimplify/interview-prep](https://github.com/kubesimplify/interview-prep). Not opened in depth.
- **TrainWithShubham 90DaysOfDevOps.** Pushed 2026-06-07, "starts on the 1st Jan" — [LondheShubham153/90DaysOfDevOps](https://github.com/LondheShubham153/90DaysOfDevOps). Only 68★ on this fork, and it is a reading and task list rather than break-fix, so it is not recommended over the existing `90daysofdevops` row.
- **DevOps CTF.** It claims 150+ challenges in 10 categories and "~10s Environment Spin-up"; copyright "© 2025" — [devops-ctf.com](https://www.devops-ctf.com/). Unverified (Q2).
- **Rootly Academy.** Described as AI-powered incident-response simulations (March 2026) — [Rootly (snippet)](https://rootly.com/sre/top-devops-incident-management-tools-sre-teams-2026-dc0ac). rootly.com/academy returned a 403 bot wall, so it is unverified.
- **Telekom IT DevOps Advent Calendar.** Ran in December 2025 — *snippet only*, no URL confirmed.

### Inferences
- **Creator content, not new SaaS.** For the "promoted by creators" angle, add the creator Killercoda courses as deep links. Treat any new SaaS as unverified until it is reachable and states its free limits.
- **Advent events.** Add an "Advent season" note to the Practice Arena: SadServers Advent of Sysadmin, Advent of DevOps and SANS Holiday Hack all run in December.

### Gaps
- Instagram and YouTube link pages were not mined directly. Creator material was found through GitHub and Killercoda instead.
- I found no evidence of Abhishek Veeramalla or Kunal Kushwaha publishing graded break-fix labs. I did not open their repos.

## Q4. What do other ecosystems offer: non-US, university, vendor sandboxes, events, GitHub break-fix collections?

### Takeaway
- **Universities:** Helsinki (two 2026 DevOps MOOCs) and MIT (Missing Semester 2026) are the useful open courses.
- **Vendors:** Datadog is the only one found with a free provisioned lab account and no card. Elastic embeds Instruqt labs (sign-up unclear). JFrog's practice labs are paid. Red Hat's RHEL labs need a Red Hat login.
- **Non-US:** a Korean containerlab network break-fix series (133★), India-based creators, and French/Indian government platforms that are security-only or simulation-only.

### Cited Findings
- **Non-US / India.**
  - gnu-gnu/network-fundamentals-lab (Korea, Q1 row 13).
  - Piyush Sachdeva's 40DaysOfKubernetes (India, row 19).
  - The DevOps CTF creator (Gokul AP); the app is hosted in `ap-south-1` (Mumbai).
  - India's Virtual Labs (vlab.co.in, Ministry of Education) offers a Computer Networks lab built on "interactive simulations" aligned to B.Tech syllabi. It is academic and simulation-only, so not recommended — [Virtual Labs (snippet)](https://new.vlab.co.in/broad_area.php?ba_id=2).
  - France's Hackropole (ANSSI) has 627 replayable FCSC challenges in crypto, forensics, pwn, reverse and web: security-only — [hackropole.fr](https://hackropole.fr/en/) (opened).
- **University and course labs open to all.** Helsinki (rows 10–11) and MIT (row 18). In ProLUG's syllabus, a Killercoda Ubuntu machine is one option among "a home lab VM or a ProLUG remote lab running Rocky Linux" (snippet) — [ProLUG course books](https://professionallinuxusersgroup.github.io/course-books/).
- **Vendor sandboxes.**
  - **Datadog:** verified (row 4).
  - **Elastic:** Instruqt-embedded "Observability 101" labs, 15 min, sign-up unknown — [Elastic demo gallery](https://www.elastic.co/demo-gallery/observability-logs).
  - **JFrog:** practice labs are "$250" monthly subscriptions — [JFrog practice lab catalog](https://academy.jfrog.com/page/practice-lab-catalog). Excluded.
  - **Octopus/Codefresh GitOps certification:** now at learning.octopus.com; "Login or sign up"; price not stated — [learning.octopus.com](https://learning.octopus.com/). Excluded as unverified free.
  - **Red Hat RHEL labs:** needs a login. Useful titles: "Secure containers with SELinux (Udica)", "Configure a rootless Podman service", "Performance observability in practice with bcc tools", "Upgrade to Red Hat Enterprise Linux 9 in place with Leapp", "Configure firewalls with RHEL system roles", "Configure system storage with Stratis", "Use the web console to monitor performance", "Solve problems with Command Line Assistant" — [Red Hat RHEL interactive labs](https://www.redhat.com/en/interactive-labs/enterprise-linux).
  - **Grafana:** Killercoda sandboxes for the Loki quickstart need a free Killercoda account "to verify you are not a bot" (snippet) — [Grafana Loki quickstart (snippet)](https://grafana.com/docs/loki/v3.7.x/get-started/quick-start/index.xml).
  - **SUSE/Rancher:** university.rancher.com and academy.suse.com did not respond (curl status 000). Not verified.
  - **Canonical:** ubuntu.com/tutorials is live (200) but these are guides, not labs.
- **Free events.**
  - SANS Holiday Hack 2026 (row 17).
  - CTFtime calendar (row 27).
  - SadServers Advent of Sysadmin and DevOps Daily Advent of DevOps (Q3).
- **GitHub break-fix collections:**
  - Q1 rows 13, 14, 15, 19, 20, 21 and 24.
  - mismailzz/Linux-Troubleshooting-Scenarios-with-solutions is a 2022 Q&A list (58★, last push 2022-08-04) — [repo](https://github.com/mismailzz/Linux-Troubleshooting-Scenarios-with-solutions). Stale; not recommended.
  - Omar-268/k8s-cluster-rescue (21★, last push 2025-08-21) — [repo](https://github.com/Omar-268/k8s-cluster-rescue). Weak.
  - k8scenario (6★, last push 2022) — [repo](https://github.com/k8scenario/k8scenario). Stale.

### Inferences
- For "vendor sandboxes with no card", only Datadog qualifies cleanly among the new finds. The others are either already listed (HashiCorp, Docker Labspaces, GitLab, Red Hat) or paid (JFrog).

### Gaps
- SUSE/Rancher academies did not respond.
- I did not check whether Elastic's Instruqt invite labs need an email.
- I did not check whether the Datadog labs are troubleshooting-oriented.

## Q5. Which deep links inside known platforms match the handbook's topics?

### Takeaway
SadServers and iximiuz now have free scenarios for nearly every handbook topic the user named:
- Traefik, systemd, journald-style logs, DNS, TLS, Postgres, cgroups, backups and S3.
- Kubernetes control-plane recovery: etcd restore, broken apiserver static pod, expired certificates, a NotReady kubelet.

Killercoda gains four creator courses. Red Hat gains an SELinux lab title.

### Cited Findings

SadServers access tiers below come from the live list: "Public" = no registration, "Email" = free account, "Paid" = Pro — [SadServers scenarios](https://sadservers.com/scenarios), opened 2026-11-09. Existing deep links (san-juan, salta, helsingor, bilbao, buenos-aires, bengaluru, kilifi, quito, capetown, bangalore, geneva, bucharest, rosario, bergen, cairo, cork) are not repeated. Note: the existing "Cork" label reads "volume not mounted after reboot", but the live title is **"Cork": The catalog won't open**: a Postgres catalog that will not stay up after a host reboot. Please re-label it.

**`sadservers` (new deep links)**

| Label | URL | Tier | Topics |
|---|---|---|---|
| Genova: cgroups problem | https://sadservers.com/scenario/genova | Email | memory-oom, perf-deep-dive, systemd-units |
| Sumé: Tied in a Knot (Knot DNS zone) | https://sadservers.com/scenario/sume | Email | dns-deep |
| Jakarta: it's always DNS | https://sadservers.com/scenario/jakarta | Public | dns-deep, ubuntu-netconfig |
| Salzburg: the TLS key that still matches | https://sadservers.com/scenario/salzburg | Email | tls-certs |
| Lisbon: etcd SSL cert troubles | https://sadservers.com/scenario/lisbon | Email | tls-certs, private-ca |
| Luxor: PostgreSQL analytics queries crawl | https://sadservers.com/scenario/luxor | Email | db-incidents |
| Manhattan: can't write data into database (Postgres) | https://sadservers.com/scenario/manhattan | Public | db-incidents, disk-full |
| Suzhou: MongoDB replicas | https://sadservers.com/scenario/suzhou | Email | db-ha |
| Alexandria: the vanishing backups (cron) | https://sadservers.com/scenario/alexandria | Email | backups-restore, time-scheduling |
| Auckland: S3 delete and archive old backups | https://sadservers.com/scenario/auckland | Email | object-storage-minio, backups-restore |
| Istanbul: delete unattached AWS EBS volumes | https://sadservers.com/scenario/istanbul | Email | aws-iam-ec2, cloud-architecture (FinOps) |
| Valladolid: cleaner not cleaning (systemd service) | https://sadservers.com/scenario/valladolid | Email | systemd-units, journald-logs |
| Vienna: the vanishing process | https://sadservers.com/scenario/vienna | Email | processes-signals, systemd-units |
| Kyoto: the ticket API will not start | https://sadservers.com/scenario/kyoto | Email | linux-problems, site-down-walk |
| Dakar: the half-installed package | https://sadservers.com/scenario/dakar | Email | packages-apt |
| Cordoba: df is lying (or is it du?) | https://sadservers.com/scenario/cordoba | Email | disk-full |
| Verona: Apache portal won't open | https://sadservers.com/scenario/verona | Email | apache-vhosts |
| Bern: Docker web container can't connect to db container | https://sadservers.com/scenario/bern | Email | docker-networking, container-incidents |
| Nairn: Phantom Gitea deploy (CI says success) | https://sadservers.com/scenario/nairn | Email | ci-debugging |
| Parma: debugging Terraform issues | https://sadservers.com/scenario/parma | Email | terraform, terraform-opentofu |
| Tigoni: patch and pray (stateful upgrade) | https://sadservers.com/scenario/tigoni | Email | change-management, availability-dr |
| Bizerte: the slow application | https://sadservers.com/scenario/bizerte | Email | slow-system |
| Philadelphia: htop metrics disagree | https://sadservers.com/scenario/philadelphia | Email | slow-system |
| Amsterdam: cron hijack | https://sadservers.com/scenario/amsterdam | Email | security-response, time-scheduling |
| Porto: port audit without net tools | https://sadservers.com/scenario/porto | Email | port-ownership, sockets-ports |
| Lyon: migrate Ingress-NGINX to Traefik | https://sadservers.com/scenario/lyon | **Paid** | traefik, k8s-onprem-edge |
| Cabedelo: Harbor full of issues | https://sadservers.com/scenario/cabedelo | **Paid** | harbor-ops |
| Montevideo: restore test snapshot would clobber production | https://sadservers.com/scenario/montevideo | **Paid** | backups-restore |
| Tunis: Redis replication problem | https://sadservers.com/scenario/tunis | **Paid** | db-ha |
| Spa: the Compose healthcheck that does not heal | https://sadservers.com/scenario/spa | **Paid** | compose-volumes, docker-problems |
| Banha: intermittent 504 (Nginx + Gunicorn) | https://sadservers.com/scenario/banha | **Paid** | proxy-problems |
| Advent of Sysadmin (event page) | https://sadservers.com/advent | — | start-here |
| Advent 2025 scenarios | https://sadservers.com/tag/advent2025 | mixed | — |
| Labs: systemd guide/troubleshooting/cheatsheet | https://sadservers.com/labs/systemd/ | free pages | systemd-units, journald-logs |
| Labs: Traefik | https://sadservers.com/labs/traefik/ | free pages | traefik, traefik-deep-dive |
| Labs: Postgres | https://sadservers.com/labs/postgres/ | free pages | db-incidents, db-ha |
| Labs: MySQL | https://sadservers.com/labs/mysql/ | free pages | db-incidents |
| Labs: DNS | https://sadservers.com/labs/dns/ | free pages | dns-deep |
| Labs: SSL/TLS | https://sadservers.com/labs/ssl/ | free pages | tls-certs |
| Labs: disk volumes | https://sadservers.com/labs/disk-volumes/ | free pages | disk-full |
| Labs: Harbor | https://sadservers.com/labs/harbor/ | free pages | harbor-ops |

**`iximiuz-labs` (new deep links)**

Free vs premium per challenge was not visible in page metadata; the existing row's free-tier note applies. Some iximiuz pages served mismatched `<title>`/description metadata on 2026-11-09. Where that happened, the label comes from the URL slug and is marked †.

| Label | URL | Topics |
|---|---|---|
| Klustered: Introduction (break-fix K8s series) | https://labs.iximiuz.com/challenges/klustered-101-introduction-57c13ac9 | k8s-troubleshooting, k8s-incidents |
| Klustered: Level One | https://labs.iximiuz.com/challenges/klustered-l1-b71142bd | k8s-troubleshooting |
| Klustered: Level Four | https://labs.iximiuz.com/challenges/klustered-l4-e6611bb2 | k8s-troubleshooting |
| Troubleshoot a worker service that keeps disappearing (systemd) | https://labs.iximiuz.com/challenges/linux-debug-vanishing-worker-service | systemd-units, journald-logs, memory-oom |
| Create a systemd service for a long-running process | https://labs.iximiuz.com/challenges/linux-create-systemd-service | systemd-units |
| Start a systemd service on first connection (socket activation) | https://labs.iximiuz.com/challenges/systemd-socket-activate-listen-stream-inet | systemd-units, sockets-ports |
| Troubleshoot a log-shipping daemon that refuses to start (strace) | https://labs.iximiuz.com/challenges/linux-strace-failing-daemon | packet-capture, linux-problems |
| Troubleshoot an image conversion daemon (missing shared library) | https://labs.iximiuz.com/challenges/linux-missing-shared-library | packages-apt, linux-problems |
| DNS 101: resolve public, internal and local hostnames | https://labs.iximiuz.com/challenges/linux-resolve-hostnames-with-hosts-file-and-dns | dns-deep, ubuntu-netconfig |
| Preserve firewall rules across reboots (nftables) | https://labs.iximiuz.com/challenges/linux-preserve-nftables-rules | host-firewall |
| Restrict access to a Docker-published port with firewall rules | https://labs.iximiuz.com/challenges/docker-networking-prevent-unexpected-access-to-published-port | docker-firewall |
| Bypass a broken VPN with a routing trick to restore SSH | https://labs.iximiuz.com/challenges/networking-restore-emergency-ssh-access | routing-nat, ssh-basics |
| Limit CPU and memory of a Linux process (cgroups) | https://labs.iximiuz.com/challenges/limit-cpu-and-memory-of-linux-process | memory-oom, perf-deep-dive |
| Limit CPU and memory of a Docker Compose application (one cgroup) | https://labs.iximiuz.com/challenges/run-multiple-containers-in-one-cgroup | compose-volumes, docker-engine |
| Make mount points persistent (/etc/fstab) † | https://labs.iximiuz.com/challenges/storage-persistent-mount | disk-full, linux-problems |
| SSH 101: replace password root login with key-based admin | https://labs.iximiuz.com/challenges/ssh-harden-new-server | ssh-hardening |
| Secure a container registry with authentication and TLS | https://labs.iximiuz.com/challenges/run-secure-container-registry | harbor-ops, tls-certs |
| Kubernetes Ingress with Traefik: multiple HTTP backends | https://labs.iximiuz.com/challenges/ingress-traefik-setup-e7396fc3 | traefik, k8s-networking |
| Configure Ingress routing with Traefik for a multi-service shop | https://labs.iximiuz.com/challenges/configure-ingress-routing-with-traefik-for-multi-service-shop-app-3a0ccabe | traefik, k8s-networking |
| Troubleshoot an Ingress that returns 503 † | https://labs.iximiuz.com/challenges/troubleshoot-ingress-returns-503-service-unavailable-8cadc570 | k8s-networking, proxy-problems |
| CKA practice: recover a broken static control-plane pod | https://labs.iximiuz.com/challenges/recover-broken-apiserver-static-pod-b8e1a53b | kubeadm-cluster, k8s-incidents |
| Recover a NotReady node (kubelet config) | https://labs.iximiuz.com/challenges/recover-notready-node-kubelet-config-af6617e0 | k8s-incidents |
| CKA practice: renew expired control-plane certificates † | https://labs.iximiuz.com/challenges/cka-practice-renew-control-plane-certificates-94a449de | kubeadm-cluster, tls-certs |
| Take and restore an etcd snapshot | https://labs.iximiuz.com/challenges/take-and-restore-etcd-snapshot-on-a-kubernetes-cluster-7ae31fbc | kubeadm-cluster, backups-restore |
| CKA kubeadm upgrade | https://labs.iximiuz.com/challenges/cka-kubeadm-upgrade-ecfc7390 | kubeadm-cluster |
| Reclaim a retained PV and restore a lost MariaDB database | https://labs.iximiuz.com/challenges/reclaim-retained-pv-with-new-pvc-and-restore-lost-mariadb-database-783fe3ae | k8s-scheduling-storage, backups-restore |
| Kubernetes observability on-call: six tickets (Prometheus, Loki, Jaeger) | https://labs.iximiuz.com/challenges/kubernetes-observability-on-call-14f1854c | prometheus-grafana, alerting, logs-loki |
| Load and enforce a custom AppArmor profile on a node † | https://labs.iximiuz.com/challenges/load-and-enforce-custom-app-armor-profile-on-node-bdfee9be | k8s-security, container-hardening |
| RHCSA prep: the sudo command isn't what it seems | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-5-6fe249f9 | users-sudo |
| Fix the broken $PATH after login | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-3-dbe16720 | shell-fhs |

**`killercoda` (new deep links; creator courses)**
- ProLUG Linux labs — https://killercoda.com/het-tanis (e.g. https://killercoda.com/het-tanis/course/Linux-Labs/109-fail2ban-with-log-monitoring). Topics: crowdsec-fail2ban, logs-loki.
- CNPE scenarios (Saiyam Pathak) — https://killercoda.com/saiyampathak/course/cnpe. Includes Flux — https://killercoda.com/saiyampathak/course/cnpe/28-flux-gitops-podinfo. Topics: gitops-argocd, platform-engineering.
- Chad M. Crowell CKA exercises — https://killercoda.com/chadmcrowell/course/cka. Includes "Troubleshoot a NotReady Node" — https://killercoda.com/chadmcrowell/course/cka/node-notready. Topics: cka-exam, k8s-incidents.
- Grafana Labs courses (Quest World, Loki quickstart) — https://killercoda.com/grafana-labs. Topics: prometheus-grafana, logs-loki.

**`redhat-interactive-labs` (new deep link)**
- RHEL labs list — https://www.redhat.com/en/interactive-labs/enterprise-linux. Covers "Secure containers with SELinux (Udica)", rootless Podman service, bcc tools performance, Leapp in-place upgrade, firewall system roles and Stratis storage. Red Hat login required. Topics: container-hardening (SELinux), perf-deep-dive, change-management (Leapp upgrade), host-firewall.

**`devops-daily-challenges` (new deep link)**
- Advent of DevOps — https://devops-daily.com/advent-of-devops (2025 edition, 25 challenges).

**`grafana-play` (new deep link, alternative to killercoda)**
- Quest World observability adventure — https://killercoda.com/grafana-labs/course/workshops/adventure (repo https://github.com/grafana/adventure).

**`kodekloud-playgrounds` or `kodekloud-engineer` (new deep link)**
- KodeKloud "Linux Challenges Series" (free) and its solutions repo — https://github.com/kodekloudhub/linux-challenges (62★, pushed 2024-06-13). The README says it is "hosted on KodeKloud platform available for free". Topics: linux-problems.

Sources: [SadServers scenarios](https://sadservers.com/scenarios), [SadServers labs](https://sadservers.com/labs), [iximiuz sitemap and challenge pages](https://labs.iximiuz.com/challenges), [Killercoda pages listed above], [Red Hat RHEL labs](https://www.redhat.com/en/interactive-labs/enterprise-linux), [DevOps Daily dev.to post](https://dev.to/devopsdaily/advent-of-devops-25-days-to-level-up-your-devops-game-2fb5), [kodekloudhub/linux-challenges](https://github.com/kodekloudhub/linux-challenges).

### Inferences
- SadServers' free "Email" tier now covers most of the handbook's Linux, web, DB and backup topics. "Prove it" links can point at these scenarios first; iximiuz is the fallback for systemd, cgroups and Kubernetes control-plane recovery.
- The † iximiuz items need a quick manual check in a browser before publishing. The slugs are reliable but the server-rendered titles were not.

### Gaps
- iximiuz per-challenge free or premium status was not visible without signing in.
- SadServers daily limits on the free tier were not re-checked; the existing row's pricing note applies.

## Q6. What was checked and rejected (so it is not re-proposed)?

### Takeaway
Fourteen candidates were checked and left out:
- 3 because they are paid.
- 4 because they are security-only or simulation-only.
- 4 because they are unverifiable or unreachable.
- 3 because they are shallow or stale.

### Cited Findings
- **JFrog Academy practice labs:** "$250" monthly subscriptions — [JFrog](https://academy.jfrog.com/page/practice-lab-catalog).
- **NDG Proxmox VE sandbox:** paid (snippet) — [NDG](https://www.netdevgroup.com/online/courses/open-source/ndg-sandbox-for-proxmox-ve).
- **Octopus (ex-Codefresh) GitOps certification:** sign-up, price not shown — [learning.octopus.com](https://learning.octopus.com/).
- **Hackropole (ANSSI):** security CTF archive only — [hackropole.fr](https://hackropole.fr/en/).
- **Root-Me:** a bot-check page blocked the fetch; security-focused — https://www.root-me.org/ (not opened).
- **Virtual Labs India:** academic simulations — [vlab (snippet)](https://new.vlab.co.in/broad_area.php?ba_id=2).
- **Jamf 100:** video and text, no lab — [Jamf (snippet)](https://www.jamf.com/training/100/).
- **DevOps CTF:** app host unresolvable on 2026-11-09 — [devops-ctf.com](https://www.devops-ctf.com/).
- **Rootly Academy:** 403 bot wall — rootly.com/academy.
- **SUSE / Rancher academies:** no response (curl 000).
- **Telekom DevOps Advent Calendar:** snippet only.
- **OnlineLinuxTerminal challenges:** only 6 basic challenges (find a file, chmod, grep IPs, tar) — [onlinelinuxterminal.com/challenges](https://onlinelinuxterminal.com/challenges/). Overlaps CMD Challenge.
- **PracticeLinux:** JS-only page; "106+ rooms … many rooms are completely free" (snippet). Not verified — [practicelinux.com](https://www.practicelinux.com/).
- **rawkode-academy/klustered repo:** stale since 2022; use the iximiuz Klustered challenges instead — [repo](https://github.com/rawkode-academy/klustered).
- **SQL games** (SQL Noir, SQL Police Department, Lost at SQL, DB Fiddle) all returned 200. They duplicate SQL Murder Mystery and SQLZoo, which are already listed.
- **Watch list** (too new or too small; re-check in 2027):
  - RomanVihovsky/devops-troubleshooting-labs (3★, Swarm labs) — [repo](https://github.com/RomanVihovsky/devops-troubleshooting-labs).
  - yeongseon Azure troubleshooting labs (0–4★) — [repo](https://github.com/yeongseon/azure-paas-troubleshooting-labs).
  - h-vance/prove-it-labs and monegim/under-the-hood-labs (3★ each). Seen in a GitHub search; not opened.

### Inferences
- Add these to practice.json `excluded_after_research` with `checked_on: 2026-11-09`, so a later pass does not repeat them.

### Gaps
- Root-Me and PracticeLinux could not be read (bot wall or JS), so their free tiers are unconfirmed.
