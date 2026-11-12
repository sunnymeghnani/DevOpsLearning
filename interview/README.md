# Module-wise DevOps interview practice

Your personal learning path is still under construction. This folder does not claim that you have completed a course, lab or production incident.

**57 module packs, 57 scenarios and 114 prompts:** each pack has one main question and one harder follow-up, plus answer checkpoints, reasoning, common traps and a verification exercise. Files use the same names as handbook modules 01–57. This is a first batch, not an exhaustive interview bank.

The interview content is **integrated into the website** (since 4 October 2026, at your request) under the sidebar group **Interview practice**: a how-to page plus one page per stage (Fresher, Junior → Mid-level, Senior, Every stage), with one entry per topic (for example Fresher → SSH & Remote Access, Users & Permissions). Each handbook module also links to its own question. These Markdown files remain the source; the site pages are rebuilt from them.

## How to use it

1. Pick your current learning module, not every tool at once.
2. Answer the main question aloud before opening the answer.
3. Introduce the twist. State what evidence changes your mind.
4. Compare with the checkpoints; explain why your next check is safe.
5. If useful, do the proposed exercise in a disposable lab and record your actual observations separately.

Foundation: identify the layer, resource or execution context. Intermediate: narrow competing hypotheses with evidence. Senior: handle tradeoffs, blast radius, rollback, data integrity and coordination. The senior extension appears in each pack, but it is not a claim that every role asks the same questions.

## Practice rubric

Score each dimension yourself from 0 (missing), 1 (partly explained), to 2 (clear and supported):

- Establish context and impact before selecting commands.
- Explain at least two plausible causes and a deciding observation.
- Choose a scoped, non-destructive initial check.
- Explain the proposed change, risk and rollback or escalation.
- Verify end-to-end behavior and communicate uncertainty.

A total is only a self-assessment, not a hiring prediction or proof of production readiness. No scores or completion flags have been filled in.

## Sources and attribution

[Source ledger](SOURCES.md) contains Reddit interview discussions, the GitHub practice collection, Stack Overflow/Server Fault troubleshooting threads, upstream issues, official forums, primary documentation and postmortems.

Only module 10 adapts an explicitly reported interview theme; its follow-up is original. The other 56 are original scenario drills. Interview self-reports are unverified, source fixes may be partial or unresolved, and the labs have not been run. Do not present public incidents as your personal work experience.

## Module index

| Module pack | Scenario |
|---|---|
| [01 — storage disk](01-storage-disk.md) | Free bytes, failed writes |
| [02 — network](02-network.md) | Ping works, application times out |
| [03 — cpu performance](03-cpu-performance.md) | High load, mostly idle CPU |
| [04 — memory](04-memory.md) | Exit 137 with free host RAM |
| [05 — processes](05-processes.md) | A process comes back after being killed |
| [06 — logs journal](06-logs-journal.md) | Logs disagree about the incident time |
| [07 — services systemd](07-services-systemd.md) | Works in a terminal, fails as a service |
| [08 — dns](08-dns.md) | DNS succeeds, the client still fails |
| [09 — ssh remote access](09-ssh-remote-access.md) | SSH stopped after a configuration change |
| [10 — users permissions security](10-users-permissions-security.md) | Add one permission without changing the rest |
| [11 — packages](11-packages.md) | A package lock during emergency patching |
| [12 — time ntp](12-time-ntp.md) | Time drift looks like an authentication failure |
| [13 — kernel system](13-kernel-system.md) | Read-only filesystem after I/O errors |
| [14 — docker containers](14-docker-containers.md) | Published port, connection refused |
| [15 — kubernetes](15-kubernetes.md) | Running pods, empty Service backends |
| [16 — aws cloud](16-aws-cloud.md) | Open security group, unreachable EC2 |
| [17 — windows](17-windows.md) | Windows port 443 belongs to PID 4 |
| [18 — web http tls](18-web-http-tls.md) | Correct IP, wrong HTTPS site |
| [19 — cheatsheet](19-cheatsheet.md) | You get only three initial checks |
| [20 — macos](20-macos.md) | macOS resolves differently on VPN |
| [21 — case apache 443 dokploy](21-case-apache-443-dokploy.md) | Apache moved to 81/444: is deployment finished? |
| [22 — playbook ports inventory](22-playbook-ports-inventory.md) | No obvious process owns an exposed port |
| [23 — playbook slow system](23-playbook-slow-system.md) | A slow system with no single hot process |
| [24 — playbook network speed](24-playbook-network-speed.md) | Fast speed test, slow application transfer |
| [25 — playbook site down](25-playbook-site-down.md) | Which layer produced the 502? |
| [26 — playbook containers k8s](26-playbook-containers-k8s.md) | CrashLoopBackOff is a symptom |
| [27 — learn linux](27-learn-linux.md) | A command works for root, not the service account |
| [28 — learn networking](28-learn-networking.md) | Networking explanation without OSI memorization |
| [29 — learn webservers proxies](29-learn-webservers-proxies.md) | A proxy is healthy but users get errors |
| [30 — learn docker](30-learn-docker.md) | The entrypoint file exists, but cannot run |
| [31 — learn kubernetes](31-learn-kubernetes.md) | A slow dependency causes a restart storm |
| [32 — learn performance observability](32-learn-performance-observability.md) | The average looks good while users suffer |
| [33 — learn cicd iac sre](33-learn-cicd-iac-sre.md) | Two green pipelines, one broken environment |
| [34 — roadmap](34-roadmap.md) | Choose a learning dependency, not another tool |
| [35 — deployment patterns](35-deployment-patterns.md) | Pick a deployment pattern under constraints |
| [36 — learn cloud aws](36-learn-cloud-aws.md) | A private cloud workload needs dependencies |
| [37 — learn security devsecops](37-learn-security-devsecops.md) | A secret appears in a successful CI log |
| [38 — learn databases ops](38-learn-databases-ops.md) | More app replicas make database availability worse |
| [39 — learn senior architecture](39-learn-senior-architecture.md) | Design recovery before promising high availability |
| [40 — career ladder](40-career-ladder.md) | Describe experience honestly under interview pressure |
| [41 — problems linux systems](41-problems-linux-systems.md) | Deleted logs did not free space |
| [42 — problems network dns tls vpn](42-problems-network-dns-tls-vpn.md) | Route rollback is itself a coordinated change |
| [43 — traefik and reverse proxies](43-traefik-and-reverse-proxies.md) | Traefik routes disappear after a Docker upgrade |
| [44 — problems docker swarm registry](44-problems-docker-swarm-registry.md) | Runner cleanup targeted the wrong runtime |
| [45 — dokploy and self hosted paas](45-dokploy-and-self-hosted-paas.md) | Dokploy says success, public route is gone |
| [46 — problems kubernetes](46-problems-kubernetes.md) | A historical Kubernetes answer meets a modern cluster |
| [47 — cicd gitlab jenkins actions argocd](47-cicd-gitlab-jenkins-actions-argocd.md) | An unchanged pipeline breaks on a mutable image tag |
| [48 — wazuh and security tools](48-wazuh-and-security-tools.md) | Wazuh enrollment succeeds, events do not arrive |
| [49 — observability stack problems](49-observability-stack-problems.md) | Logging changes make the monitoring stack slow |
| [50 — problems cloud iac proxmox](50-problems-cloud-iac-proxmox.md) | A provider fix reveals a destructive Terraform plan |
| [51 — problems databases storage backup](51-problems-databases-storage-backup.md) | The backup job was green, restore failed |
| [52 — devops day to day](52-devops-day-to-day.md) | Your local command targeted production |
| [53 — oss devops toolbox](53-oss-devops-toolbox.md) | Build an OSS pipeline with clear ownership |
| [54 — practice arena](54-practice-arena.md) | Make a safe incident exercise |
| [55 — paths onprem vs cloud](55-paths-onprem-vs-cloud.md) | Cloud or on-prem is a constraint question |
| [56 — sources and verification](56-sources-and-verification.md) | A highly voted answer is not a verified fix |
| [57 — method protect risk ladder](57-method-protect-risk-ladder.md) | The only database is down, and the fast fix could lose data |

## Website integration

[manifest.json](manifest.json) gives stable module mappings, filenames, question IDs and source IDs. Markdown module files are the authoritative question content; the manifest is a navigation/metadata index, not a second answer copy.

`interview_site.py` (in the project root) generates the website pages at build time: packs are grouped by their own `Stage:` line, answers and sources stay collapsed, provenance and source-limit text is preserved, relative handbook/source links are resolved to site anchors, and nothing marks roadmap completion. Edit the packs here, then run `python3 build_site.py`.

Validation from the project directory:

```sh
python3 -m unittest discover -s tests -v
```

This checks structure and integration contracts; it does not execute the operational exercises or prove every external claim.
