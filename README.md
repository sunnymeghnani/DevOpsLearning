# DevOps Troubleshooting Handbook (Offline)

An offline handbook for a DevOps engineer who runs on-prem Ubuntu servers (plus some AWS) and is
growing from fresher to senior. It has four parts: real incidents and playbooks, real-world problem
libraries for the Linux hosts, networks and open-source tools you run (Dokploy, Traefik, Docker, Swarm
and Harbor, Kubernetes, GitLab CI, Wazuh, the Prometheus and Grafana stack, Terraform, Ansible,
Proxmox, databases and backups, Let's Encrypt, WireGuard and Tailscale) plus a map of how those tools
fit together and the day-to-day reality of the job, a learning track
from fresher to senior, and a command reference for Linux, containers, Kubernetes, AWS, Windows and
macOS.

> ⚠️ All examples are illustrative. Sample outputs are representative — actual output varies by
> distro and version. Commands are documented for you to run on your own test VM or servers, not
> to paste onto a production host. Addresses come from the documentation ranges (192.0.2.0/24,
> 198.51.100.0/24, 203.0.113.0/24) or private ranges, names use example.com, and UPPERCASE words
> are placeholders. Nothing here needs internet access except where noted.

> ✅ **Prior review.** The original 56 modules were reported to have passed an independent technical review:
> a second reviewer checked each command, flag, path, config snippet, error string and sample
> output against Ubuntu 22.04/24.04 and the tool versions current in October 2026, and fixed what
> was wrong in place (about 900 corrections across the handbook).
> The [Sources & Verification](56-sources-and-verification.md) page distinguishes historical
> research reports from fresh, claim-specific checks and from unverified discovery links.

## How to use this handbook

Pick the entry point that matches why you opened it.

| You want to | Start with | Then |
|---|---|---|
| Fix something that is broken now | the [triage method](#universal-triage-method) below, then the matching playbook (21–26, 35) | the problem library for that tool (41–51): search the exact error text, or start from the [top community problems](19-cheatsheet.md#top-community-problems-first-command) table; for requests and on-call, [DevOps day to day](52-devops-day-to-day.md) |
| Grow from fresher to senior | the [Career Ladder](40-career-ladder.md) to place yourself, then the [Roadmap](34-roadmap.md) and its [3D course map](#map) | the Learn module for your level (27–33, 36–39), one topic at a time |
| Find a command | the [Cheat Sheet](19-cheatsheet.md) and the command reference (01–20) | the search box at the top: press / and type a command, an error message or a port |
| Practise before it breaks for real | the [Practice Arena](54-practice-arena.md): free sites first (SadServers, Killercoda, devops.games and more), paid ones labelled | the [practice plan for your stage](54-practice-arena.md#14-practice-plans-by-career-stage) |
| Focus on on-prem or on AWS | the 🏢/☁️ selector in the top bar, then [On-prem or cloud path](55-paths-onprem-vs-cloud.md) | the [on-prem ↔ AWS equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) table |
| Trace a problem to its sources | [Sources & Verification](56-sources-and-verification.md) | Filter by tool, domain or source status; compare the source's version and environment before applying a fix |

**Study method.** Every topic uses the same loop: the KodeKloud lesson for a new topic → the
handbook note → a lab where you break something on purpose → the matching playbook drill under a
timer → the exit check and a five-line note (symptom, first wrong guess, deciding evidence, fix,
what to check first next time). Details: [Study method](34-roadmap.md#study-method) and
[Learning with KodeKloud](40-career-ladder.md#9-learning-with-kodekloud).

**Levels.** Career stages and levels are one scale: Fresher L0 Foundations, Junior L1 Operator,
Mid-level L2 Troubleshooter, Senior L3 Platform, Senior/Lead L4 SRE. Playbook steps and problem
entries carry tags such as [L2 · Mid]: work through the ones at or below your level first, and read
one level up to see what is coming.

## Universal triage method

When a system is "slow" or "broken", check resources in this order (the USE method:
**U**tilization, **S**aturation, **E**rrors — for every resource):

```
1. uptime          → load average: is the box overloaded?
2. dmesg -T | tail → kernel errors: OOM kills, disk errors, NIC resets?
3. df -h ; df -i   → disk full? inodes full?
4. free -h         → memory pressure? swap thrashing?
5. top / htop      → which process? CPU-bound or I/O-wait (wa%)?
6. ss -tulpn       → is the service actually listening?
7. journalctl -xe  → what do the logs say?
```

Golden rule: **check the logs before restarting anything** — a restart destroys evidence.

## Sections

The sidebar uses the same five groups.

### Start here

> 🏢/☁️ **On-prem or cloud?** Use the selector in the top bar (Both · 🏢 On-prem · ☁️ Cloud). It switches every block marked 🏢 On-premise or ☁️ Cloud (AWS): the two paths on [page 55](55-paths-onprem-vs-cloud.md) and the environment-specific entries in the problem libraries ([41](41-problems-linux-systems.md), [42](42-problems-network-dns-tls-vpn.md), [44](44-problems-docker-swarm-registry.md), [46](46-problems-kubernetes.md)), [DevOps day to day](52-devops-day-to-day.md) and the [toolbox map](53-oss-devops-toolbox.md). It also hides the other environment's entries in the sidebar and filters the 3D map and its guided path. Your choice is remembered.

| Module | What it covers |
|---|---|
| [Home / Triage](README.md) | This page: how to use the handbook, the triage method, cloud vs on-premise notes |
| [Command Decoder: What & Why](command-decoder.md) | What each command and its flags mean, how to read the output, why it works better than the command people reach for first (for example `ping` versus `mtr`), the trap and the next step. Every submodule opens with a collapsed box that decodes the commands it uses |
| [34 — Zero-to-Hero Roadmap](34-roadmap.md) | All 123 topics on five levels in study order, the weekly rhythm and your first 30 days; the text version of the 3D course map |
| [40 — Career Ladder](40-career-ladder.md) | What each stage is trusted with, skills matrix and checklists, interview preparation, learning with KodeKloud, building proof |
| [55 — On-prem or cloud path](55-paths-onprem-vs-cloud.md) | Choose your environment: who owns what on-prem vs AWS, the same symptom with different first moves, an on-prem ↔ AWS equivalents table, and the on-prem and cloud paths from fresher to senior |
| [54 — Practice Arena](54-practice-arena.md) | 80 checked practice sites and games (SadServers, Killercoda, OverTheWire, Learn Git Branching, Mess With DNS, devops.games…), free first with paid options labelled, plus weekly practice plans per stage |
| [56 — Sources & Verification](56-sources-and-verification.md) | Offline source index for the saved community-problem research, source status filters, scoped checks and a process for refreshing one domain at a time |

### Interview practice

Generated from the [interview pack](interview-guide.md): 57 scenarios, 114 prompts, grouped by the stage each pack declares. Answer aloud, add the twist, then open the collapsed checkpoints. Practice scenarios, not verified employer questions; nothing records completion.

| Page | What it covers |
|---|---|
| [Interview Practice: How to Use](interview-guide.md) | How to practise, the self-assessment rubric, the stage index and the source ledger |
| [Interview: Fresher](interview-fresher.md) | Foundation questions for modules 01–20: storage, network, processes, systemd, DNS, SSH, users & permissions, packages, Docker and Kubernetes basics, AWS, Windows, macOS… |
| [Interview: Junior → Mid-level](interview-junior-mid.md) | The playbooks, learn modules and problem libraries: ports, slow systems, site down, Docker, Kubernetes, Traefik, Dokploy, CI/CD, Wazuh, observability… |
| [Interview: Senior](interview-senior.md) | Decision-making under constraints: deployment patterns, AWS, security, databases, architecture, networking and on-prem vs cloud trade-offs |
| [Interview: Every Stage](interview-every-stage.md) | Explaining your learning path, roadmap, practice and sources honestly |

### Real incidents & playbooks

| Module | What it covers |
|---|---|
| [57 — Method: PROTECT & the Risk Ladder](57-method-protect-risk-ladder.md) | Something is broken and people are waiting: the PROTECT loop, the eight-rung risk ladder, window or live fix, messages for risky steps, two worked examples and a printable card |
| [21 — Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) | Your real incident end to end: inventory, architecture choice, moving Apache off 80/443, Dokploy, Traefik routes, cutover, rollback, postmortem |
| [22 — Who owns this port?](22-playbook-ports-inventory.md) | Port → PID → unit → config → logs on Linux, Docker, Swarm, Kubernetes, Windows and macOS; dispatching a service safely |
| [23 — Why is it slow?](23-playbook-slow-system.md) | The 60-second checklist, then CPU, memory, disk I/O, network and application slowness, scenarios, Windows and macOS quick playbooks, and a decision tree |
| [24 — Network speed](24-playbook-network-speed.md) | Path and latency, iperf3 throughput, NIC, TCP and MTU, safe tuning, AWS, containers, Wi-Fi and VPN, Windows and macOS tools, six scenarios |
| [25 — Site down: DNS · TLS · proxy](25-playbook-site-down.md) | The layered walk from DNS to the app, which layer sent each status code, 502/503/504, communicating during an outage |
| [26 — Docker & K8s incidents](26-playbook-containers-k8s.md) | Containers that will not stay up, ports and firewall, DNS, disk and registries; Dokploy, Traefik and Swarm; Kubernetes pods, Services, nodes and rollouts |
| [35 — Deployment patterns](35-deployment-patterns.md) | Your 81/444 port shift and how to finish it, choosing ports, twelve deployment patterns, recipes and a post-deployment checklist |

### Real-world problems & OSS toolbox

Start with 52, the day-to-day view: the tickets, requests, changes and on-call situations that fill
a real week, and how to learn from them. The tool modules (45, 43, 47, 48 and 49) teach the tool
first (the tool in 10 minutes, install, day-2 operations, a learning path); 51, 50, 44, 46, 41 and
42 build on the Learn modules and go straight to the problems; 53 maps how the tools fit together.
Every library lists the problems DevOps engineers hit most, each with diagnosis, sample output, fix
and prevention.

| Module | What it covers |
|---|---|
| [52 — DevOps day to day](52-devops-day-to-day.md) | A realistic day and week by career stage; the ticket and request taxonomy; access, port, domain, deploy, certificate, disk and restore requests; on-call and incidents in practice; changes that go wrong; toil; working with developers; runbooks; how engineers learn on the job, burnout, and a 90-day "learn from your own tickets" plan |
| [45 — Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md) | Dokploy architecture, install, updates and backups; problems with Dokploy, Coolify and CapRover: domains, certificates, builds, webhooks, data and Swarm nodes |
| [43 — Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) | Traefik v3 in depth and its day-2 operations; problems with Traefik, nginx, Apache, Caddy, HAProxy and Nginx Proxy Manager |
| [47 — CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) | GitLab CI runners, Docker-in-Docker, Harbor and the private CA, caches and deploys; Jenkins, GitHub Actions runners, Argo CD and Flux, SonarQube and Nexus |
| [48 — Wazuh & security tools](48-wazuh-and-security-tools.md) | Wazuh install, agents, indexer and rules; CrowdSec with the Traefik bouncer, Fail2ban, Trivy, Vault and OpenBao, Keycloak and Authentik |
| [49 — Observability stack](49-observability-stack-problems.md) | Prometheus, Alertmanager, Grafana and Loki with Alloy on your Dokploy hosts: install, alert rules and day-2 operations; problems with exporters, dashboards, alerts and Loki, plus Uptime Kuma, Netdata, Zabbix, Tempo, ELK, OpenSearch and Graylog |
| [51 — Databases & backups: problems](51-problems-databases-storage-backup.md) | PostgreSQL, MySQL and MariaDB, Redis and MongoDB in Docker and Dokploy, PgBouncer, backups with restic, borg, pgBackRest and Proxmox Backup Server, MinIO and S3, schema migrations in CI/CD, WAL and upgrades, Velero and restore drills |
| [50 — Cloud, IaC & Proxmox: problems](50-problems-cloud-iac-proxmox.md) | AWS access, networking and surprise bills; Terraform and OpenTofu state, drift and refactoring; Ansible connections, idempotency and safe rollouts; Proxmox VE networking, quorum, storage and backups; cloud-init templates and Packer |
| [44 — Docker, Swarm & Harbor: problems](44-problems-docker-swarm-registry.md) | Docker daemon access and the Docker 29 upgrade, full disks and logs, Compose v2, container networking, Docker Hub limits and private-CA registries, BuildKit, Portainer, Swarm services, overlay and quorum, and Harbor operations (robots, GC, replication) |
| [46 — Kubernetes: problems](46-problems-kubernetes.md) | kubectl access and RBAC, kubeadm, k3s and containerd, NotReady nodes, CNI and CoreDNS, ingress-nginx and Traefik, cert-manager, MetalLB, storage, metrics-server, Helm, Argo CD and Flux, upgrades, certificates and etcd, Rancher and EKS; every entry names its CKA domain |
| [41 — Linux & systemd: problems](41-problems-linux-systems.md) | Disk full and filesystems, packages and upgrades, systemd services and timers, users and sudo, SSH lockouts, memory and OOM, load and kernel limits, time, LVM and boot failures, NFS, RAID and SMART |
| [42 — Network, DNS & TLS: problems](42-problems-network-dns-tls-vpn.md) | Interfaces, routes and netplan, host name resolution, UFW, firewalld and nftables, NAT and port forwarding, Let's Encrypt and ACME, certificate chains and private CAs, BIND, Unbound, Pi-hole and AdGuard, WireGuard, OpenVPN, Tailscale, Headscale and NetBird, MTU and IPv6 |
| [53 — OSS DevOps toolbox map](53-oss-devops-toolbox.md) | The reference self-hosted platform (request, deploy, metrics, log, security, identity, backup and admin flows, and a port matrix), tool-by-category decision tables for PaaS, proxies, CI/CD, registries, monitoring, logging, security, secrets, SSO, backups and VPN, the adoption order by career stage, twelve integration recipes that wire the tools together (each with what breaks), and how to run the toolbox safely: upgrades, pinned versions, backups and exposure |

### Learn: fresher → senior

| Module | What it covers |
|---|---|
| [27 — Linux](27-learn-linux.md) | Shell, files, users, processes, packages, systemd, boot, storage, SSH, scheduling, bash, logs and kernel basics |
| [28 — Networking, DNS & TLS](28-learn-networking.md) | Layers, subnetting, routing, NAT, TCP and UDP, firewalls, DNS, HTTP, TLS, load balancing, VPN and MTU, IPv6, packet capture |
| [29 — Web servers & proxies](29-learn-webservers-proxies.md) | Apache, nginx, Traefik and Dokploy in depth, HAProxy, migration patterns, and a capstone: Apache behind Traefik |
| [30 — Docker](30-learn-docker.md) | Images, Dockerfiles, networking, storage, Compose, Harbor, daemon.json, security and Swarm for Dokploy |
| [31 — Kubernetes (CKA)](31-learn-kubernetes.md) | A kubeadm homelab, workloads, Services, Ingress and Gateway API, storage, scheduling, RBAC, Helm, troubleshooting, CKA strategy and drills |
| [32 — Performance & observability](32-learn-performance-observability.md) | CPU, memory, disk and network deep dives, Prometheus, Alertmanager, Grafana, logs and tracing, SLOs and capacity |
| [33 — CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) | Git, GitLab CI/CD, deployment strategies, Ansible, Terraform, secrets, SRE practice and the L4 game day |
| [36 — Cloud & AWS](36-learn-cloud-aws.md) | IAM, VPC, EC2, S3 and KMS, load balancing and Route 53, RDS, containers, observability, IaC, hybrid links and FinOps |
| [37 — Security & DevSecOps](37-learn-security-devsecops.md) | Hardening, network security, PKI, secrets, container and Kubernetes security, supply chain, detection and incident response |
| [38 — Databases for DevOps](38-learn-databases-ops.md) | PostgreSQL, MySQL/MariaDB and Redis operations, backups that restore, replication, databases in containers, incident playbooks |
| [39 — Senior: architecture & leadership](39-learn-senior-architecture.md) | Availability, disaster recovery, capacity, cost, platform engineering, migrations, decisions, reliability and technical leadership, DORA |

### Command reference

| Module | What it covers |
|---|---|
| [01 — Storage & disk](01-storage-disk.md) | df, du, lsblk, iostat, LVM, RAID, inode/space issues, fsck, smartctl |
| [02 — Network](02-network.md) | ping, mtr, traceroute, ss, ip, tcpdump, nc, nmap, ethtool, firewall |
| [03 — CPU & performance](03-cpu-performance.md) | top, htop, uptime, mpstat, pidstat, vmstat, sar, perf, load average |
| [04 — Memory](04-memory.md) | free, vmstat, /proc/meminfo, OOM killer, swap, slab, smem |
| [05 — Processes](05-processes.md) | ps, pstree, kill, nice, strace, ltrace, lsof, zombies |
| [06 — Logs & journal](06-logs-journal.md) | journalctl, dmesg, /var/log, tail, grep, logrotate |
| [07 — Services & systemd](07-services-systemd.md) | systemctl, failed units, boot analysis, targets, timers |
| [08 — DNS](08-dns.md) | dig, nslookup, host, resolv.conf, systemd-resolved, common failures |
| [09 — SSH & remote access](09-ssh-remote-access.md) | ssh -v, keys, scp/rsync, tunnels, common auth failures |
| [10 — Users, permissions & security](10-users-permissions-security.md) | id, sudo, chmod/chown, ACLs, SELinux, auditd, login history |
| [11 — Package management](11-packages.md) | apt, yum/dnf, rpm, dpkg, broken deps, held/locked packages |
| [12 — Time & NTP](12-time-ntp.md) | timedatectl, chrony, ntpq, clock drift (critical for TLS/Kerberos/AWS) |
| [13 — Kernel, boot & hardware](13-kernel-system.md) | uname, sysctl, ulimit, dmesg, dmidecode, lspci, modules |
| [14 — Docker & containers](14-docker-containers.md) | docker ps/logs/inspect/stats/exec, image and network debugging |
| [15 — Kubernetes](15-kubernetes.md) | kubectl get/describe/logs/exec, CrashLoopBackOff, Pending pods, nodes |
| [16 — AWS](16-aws-cloud.md) | EC2, EBS, metadata (IMDS), SSM, security groups vs NACLs, CloudWatch, ELB |
| [17 — Windows](17-windows.md) | pathping, ipconfig, tracert, netstat, tasklist, event logs, AD/domain, PowerShell |
| [20 — macOS](20-macos.md) | diskutil, launchctl, unified log, scutil, Gatekeeper, tmutil, memory_pressure |
| [18 — Web, HTTP & TLS](18-web-http-tls.md) | curl -v, openssl s_client, cert expiry, latency breakdown, 5xx debugging |
| [19 — Cheat sheet](19-cheatsheet.md) | First 5 minutes on a broken box, the one-liners you always forget, the top community problems with their first command, port ownership, freeing a port, slowness and network speed on one page |

## Cloud vs on-premise notes

- Everything in sections 01–13 applies to **both** AWS EC2 and on-premise Linux.
- On AWS, also check the **hypervisor layer**: instance status checks, EBS volume
  status, security groups, NACLs — see [16-aws-cloud.md](16-aws-cloud.md).
- On-premise, also check the **physical layer**: RAID controller, SMART, cabling,
  switch port — see [01](01-storage-disk.md) and [13](13-kernel-system.md).

## Where the real-world problems come from

The playbooks and problem libraries go beyond one person's incidents. They are built from what
engineers report in public discussions: GitHub issues of the tools themselves,
the official forums (the Traefik community, Docker forums, the GitLab forum, the Wazuh Google Group,
the Grafana community, HashiCorp Discuss, the Let's Encrypt community, Ubuntu Discourse, the OPNsense,
Proxmox and restic forums, the DigitalOcean community and others), official
documentation and troubleshooting pages, and public postmortems. New **Community case reading**
sections in modules 41–52 now contain 28 curated cases, including Reddit, Stack Overflow,
Server Fault, GitHub, official forums and six historical production postmortems.
The 16 expanded incident questions add deciding evidence, reported recovery, prevention and
proposed verification exercises. They do not record completed learning or form a live outage feed.
Two original Reddit discussions remain explicitly excerpt-only. The earlier research run's access limitation
does not apply universally. Search links remain discovery aids, not read threads.
The saved catalogs distinguish references reported
checked from unverified links. [Sources & Verification](56-sources-and-verification.md) exposes
those records, with separate labels for thread readings, incomplete excerpts, discovery links
and fresh checks of specific claims. This is your personal learning path under construction;
the integration does not change your map progress or treat scenarios as work you have done.
Tools move fast, so compare the source with the release notes of the version you run.
