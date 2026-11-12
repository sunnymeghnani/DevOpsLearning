# 53 — Open-Source DevOps Toolbox: What to Use, How It Fits, What Breaks

This module is the map that connects the tool deep dives ([Traefik](43-traefik-and-reverse-proxies.md), [Dokploy](45-dokploy-and-self-hosted-paas.md), [CI/CD](47-cicd-gitlab-jenkins-actions-argocd.md), [Wazuh](48-wazuh-and-security-tools.md), [observability](49-observability-stack-problems.md)) and the problem libraries (41–51). It draws one realistic self-hosted platform built from open-source tools, compares the alternatives in each category, says what to learn at each career stage, and gives twelve integration recipes, each with the failures people report in GitHub issues, official forums and docs. The commands and configuration files are written for your own lab VMs and servers: adapt the UPPERCASE placeholders and test on a snapshot first.

---

## 0. How to use this module

Most on-prem DevOps work happens at the seams between tools, not inside one tool: Traefik passing the header Authentik needs, a GitLab runner trusting Harbor's private CA, Wazuh reading the log Traefik writes, Uptime Kuma noticing that last night's backup never reported. The community threads behind modules 41–51 say the same thing. The most-commented Dokploy issues are about restarts, upgrades and routing regressions rather than features, and the most-viewed Traefik forum topics are basic plumbing such as TCP routing, redirects and the dashboard. Operating the combination is the skill.

### Who reads what

| Stage | Level | Read first | Build in your lab | You are done when |
|---|---|---|---|---|
| Fresher | L0 Foundations | 0, 1.1–1.3, 2.1, 3.1 | one Ubuntu VM with Docker, Traefik or Caddy, Uptime Kuma | you can draw the request path and name every port on it |
| Junior | L1 Operator | 1, 2, 3.2, recipes 4.2, 4.9, 4.11 | Dokploy, a GitLab runner, Prometheus with node_exporter and Grafana, restic | you deploy from a pipeline, see it on a dashboard and restore yesterday's volume |
| Mid-level | L2 Troubleshooter | 2, 3.3, recipes 4.1, 4.6–4.8, 4.10, every "What breaks" | Harbor with the private CA, Loki with Alloy, Wazuh, CrowdSec | you explain any outage on the platform from logs and metrics alone |
| Senior | L3 Platform | 1.11, 3.4, recipes 4.3–4.5, 4.12, section 5 | SSO, OpenBao, k3s with Argo CD, Proxmox Backup Server, an upgrade policy | another engineer rebuilds a component from your runbook without calling you |
| Senior/Lead | L4 SRE | 2 ("Choose when"), 3.5, 5, 6 | a disaster-recovery game day of the whole platform | you can defend every box on the diagram, including the tools you removed |

### Adopt one tool at a time

Every tool in this module goes through the same loop before it touches production:

1. **Lab first.** Install it on a snapshotted VM with a pinned version, and keep its configuration in Git from the first day.
2. **Break it on purpose.** Pick three entries from its problem library (the "Common failure modes" column in section 2 points to them) and reproduce each one.
3. **Back it up and restore it** on a second VM. A backup you have not restored is a hope, not a backup ([51 9.3](51-problems-databases-storage-backup.md#93-no-tested-restore-rto-and-rpo-in-the-disaster)).
4. **Monitor it.** At least "is it up", its disk, its certificate and its backup job (5.6).
5. **Expose it narrowly.** Decide which ports exist and who may reach them before anyone else uses it (1.11, 5.5).
6. **Then production, and only one new tool per month.** Two new tools in the same month means two unknown failure modes at once.

### The tool admission checklist

Before a tool goes live, write the answers in the README of its repository. If one answer is "nobody" or "we will see", the tool is not ready.

| Question | A good answer looks like |
|---|---|
| Who owns it? | a named person and a backup person, both able to restore it |
| Why this tool and not the alternative? | one paragraph that points at the decision table in section 2 |
| Where does its state live? | paths, volumes and databases, plus the backup job that covers them (5.3) |
| Which version runs, and how is it upgraded? | a pinned tag and a link to the release notes you read (5.1) |
| How do we know it is healthy? | a health endpoint, an alert rule and a dashboard (5.6) |
| Which ports does it open, to whom? | a row in the port matrix (1.11) |
| Which secrets does it hold or need? | where they live and who can read them (4.3) |
| How would we remove it? | the exit plan: data export format and the replacement (5.7) |

### Conventions in this module

**Placeholders and examples:** UPPERCASE words are placeholders (PUSH_TOKEN, REPLACE_ME, CROWDSEC). Hosts and addresses follow the plan in 1.2: private VLANs under 10.10.0.0/16, the WireGuard range 10.99.0.0/24, the public address 203.0.113.10, test clients from 192.0.2.0/24 and 198.51.100.0/24, names under example.com, and the users ops and deploy. Your addresses will differ; keep the shape.

**How a recipe is laid out:** each one in section 4 has **Why** (the problem it solves), **Steps** (real configuration), **Verify** (commands with realistic output) and **What breaks** (the failures to expect, linked to the problem entries that fix them). A reference such as "45 6.1" means module 45, entry 6.1.

**Practise and compare:** the [Practice Arena](54-practice-arena.md) lists where to rehearse each tool, and [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) maps every self-hosted tool to its AWS equivalent. Section 2.13 joins the two for each category.

> 📚 **Study path:** KodeKloud [DevOps Pre-Requisite Course](https://kodekloud.com/courses/devops-pre-requisite-course) → [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course) (Swarm) → [GitLab CI/CD](https://kodekloud.com/courses/gitlab-ci-cd) → [Prometheus Certified Associate](https://kodekloud.com/courses/prometheus-certified-associate-pca) → handbook deep dives 43, 45, 47, 48, 49 → this map → the self-check in section 6 on your own lab.

---

## 1. The reference self-hosted platform

The platform below is a realistic target for a team of 5–30 engineers running 10–50 services on three Proxmox nodes. You do not need all of it: section 1.12 shows a one-VM and a three-VM start, and section 3 says in which order to add the rest. What matters is that every tool on the diagram has a reason to be there, a place in the port matrix, and a backup.

### 1.1 The big picture

```text
            Internet users                                   Admins (laptops, phones)
                  |  80/tcp, 443/tcp, 443/udp                       |  51820/udp
                  v                                                 v
+---------------------------------------------------------------------------------------+
| Edge firewall (OPNsense)  public 203.0.113.10                                         |
|   NAT 80/443 --> dokploy-1           WireGuard wg0 10.99.0.0/24 --> internal VLANs    |
|   Unbound DNS: *.example.com --> internal addresses for LAN and VPN clients           |
+---------------------------------------------------------------------------------------+
     | VLAN 10 apps          | VLAN 20 build          | VLAN 30 ops          | VLAN 40 backup
     v                       v                        v                      v
+--------------------+  +---------------------+  +--------------------+  +-------------------+
| dokploy-1 manager  |  | gitlab-1            |  | mon-1              |  | s3-1              |
|  dokploy-traefik   |  |  GitLab CE          |  |  Prometheus        |  |  S3-compatible    |
|   +CrowdSec plugin |  | runner-1            |  |  Alertmanager      |  |  object storage   |
|   +forward-auth    |  |  GitLab Runner      |  |  Grafana, Loki     |  | pbs-1             |
|  Authentik, apps   |  | harbor-1            |  |  blackbox exporter |  |  Proxmox Backup   |
|  CrowdSec agent    |  |  Harbor + Trivy     |  | siem-1             |  |  Server           |
| dokploy-2 worker   |  | bao-1               |  |  Wazuh manager,    |  +-------------------+
| VLAN 50: k3s-1..3  |  |  OpenBao            |  |  indexer,dashboard |
|  + Argo CD         |  +---------------------+  +--------------------+
+--------------------+
 On every VM: node_exporter, Alloy, Wazuh agent, chrony, UFW, restic where there is state
 Underneath:  Proxmox VE cluster pve1-pve3 (mgmt VLAN 10.10.0.0/24), VM backups to pbs-1
 Off site:    kuma-1 (Uptime Kuma, watches from outside) and a copy of every backup
```

Read it in layers. The **edge** (OPNsense, Traefik) decides who gets in. The **apps** layer (Dokploy on Swarm, k3s) runs workloads. The **build** layer (GitLab, runner, Harbor, OpenBao) turns commits into scanned images and hands out short-lived secrets. The **ops** layer (Prometheus stack, Wazuh) watches everything. The **backup** layer (S3 storage, PBS) keeps copies, and the **off-site** pieces see the platform from outside and survive the loss of the site. The flows in 1.3–1.10 connect them.

### 1.2 Hosts and addresses

| VM | VLAN and IP | Runs | Start size (vCPU / RAM / disk) | State to back up |
|---|---|---|---|---|
| pve1–pve3 | mgmt 10.10.0.2–4 | Proxmox VE 9, corosync | bare metal | /etc/pve, every VM through PBS |
| opnsense | mgmt 10.10.0.1, public 203.0.113.10 | firewall, NAT, Unbound DNS, WireGuard | 2 / 4 GB / 32 GB | configuration export (XML) |
| dokploy-1 | apps 10.10.10.11 | Dokploy manager, dokploy-traefik, CrowdSec, Authentik, apps | 4 / 8 GB / 100 GB | dokploy-postgres, /etc/dokploy, app volumes |
| dokploy-2 | apps 10.10.10.12 | Swarm worker for app replicas | 4 / 8 GB / 80 GB | nothing, by design (stateless) |
| k3s-1..3 | k8s 10.10.50.11–13 | k3s servers with embedded etcd, Argo CD, MetalLB | 2 / 4 GB / 50 GB each | etcd snapshots; Git holds the rest |
| gitlab-1 | build 10.10.20.21 | GitLab CE (Omnibus) | 4 / 8 GB / 100 GB | gitlab-backup, gitlab-secrets.json, gitlab.rb |
| runner-1 | build 10.10.20.22 | GitLab Runner, docker executor | 4 / 8 GB / 100 GB | config.toml only |
| harbor-1 | build 10.10.20.23 | Harbor with Trivy, Docker Hub proxy cache | 2 / 4 GB / 40 GB plus images | /data, harbor.yml, certificates |
| bao-1 | build 10.10.20.24 | OpenBao (raft storage) | 2 / 2 GB / 20 GB | raft snapshots; unseal keys kept offline |
| mon-1 | ops 10.10.30.31 | Prometheus, Alertmanager, Grafana, Loki, blackbox | 4 / 8 GB / 200 GB | Grafana database; configuration lives in Git |
| siem-1 | ops 10.10.30.32 | Wazuh all-in-one (manager, indexer, dashboard) | 4 / 8 GB / 50 GB for up to 25 agents | /var/ossec/etc, certificates, indexer snapshots |
| s3-1 | backup 10.10.40.41 | S3-compatible storage | 2 / 4 GB / data disks | it is the target; replicate it off site |
| pbs-1 | backup 10.10.40.42 | Proxmox Backup Server | 4 / 8 GB / large datastore | datastore, synced to an off-site PBS |
| kuma-1 | off site, 198.51.100.20 | Uptime Kuma | 1 / 1 GB / 10 GB | /app/data |

Module 49 runs the monitoring stack on the Dokploy manager to keep the lab small; here it gets its own VM so that a Dokploy outage cannot take the monitoring down with it. The Wazuh sizing comes from the official quickstart (4 vCPU, 8 GiB and 50 GB for 1–25 agents for 90 days of alerts).

### 1.3 Request flow

```text
browser
  | 1 DNS: shop.example.com -> 203.0.113.10 (public) or 10.10.10.11 (internal DNS)
  | 2 TCP 443 -> OPNsense NAT -> dokploy-1:443, published in host mode, so the client IP survives
  v
dokploy-traefik   entryPoint websecure, TLS certificate from acme.json
  | 3 middleware crowdsec@file   -> banned IP? 403 (decisions cached, refreshed every 60 s)
  | 4 middleware authentik@file  -> internal tools only: 302 to the login, or 200 + identity headers
  | 5 router Host(`shop.example.com`) -> service shop-web:3000 on dokploy-network
  v
app container -> response -> one JSON access-log line -> CrowdSec agent, Alloy (Loki), Wazuh agent
```

Only 80/tcp, 443/tcp and 443/udp (HTTP/3) are reachable from the internet. When something fails on this path, first decide who generated the error: a plain-text "404 page not found" is Traefik finding no router, a 502 is the backend refusing the connection, a 504 is Traefik unable to reach it, and a 403 before any app log line is a middleware ([43 1.9](43-traefik-and-reverse-proxies.md#19-who-generated-the-error)).

### 1.4 Deploy flow

```text
git push -> gitlab-1 (443 HTTPS, 22 SSH)
  pipeline -> runner-1 polls gitlab-1:443 (outbound only; nothing connects to the runner)
    build   : docker-in-docker or Buildah, base images through harbor-1/dockerhub-proxy  (4.1)
    scan    : Trivy, fails on fixable CRITICAL findings
    push    : harbor-1:443 shop/web:SHA, then :main on the default branch (robot account, private CA)
    deploy  : POST https://dokploy.example.com/api/application.deploy (x-api-key)       (4.2)
              -> Swarm updates the service -> every node pulls from harbor-1:443
    gitops  : commit the new tag to the shop-deploy repo -> Argo CD on k3s pulls it       (4.4)
```

Two deploy styles live side by side. Swarm apps are **pushed**: the pipeline calls Dokploy's API. Kubernetes apps are **pulled**: Argo CD reconciles about every three minutes by default and applies whatever the deploy repository says. Never let both manage the same app.

### 1.5 Metrics and alerts flow

```text
node_exporter :9100, cAdvisor :8089 on every VM  <-- scrape -- Prometheus mon-1:9090
Traefik metrics :8082 (dokploy-network only)     <-- Alloy on dokploy-1 -- remote_write --> Prometheus
blackbox exporter mon-1:9115 -- probes --> https://shop.example.com/healthz, certificate expiry
Prometheus rules --> Alertmanager :9093 --> email / Teams / Telegram --> on-call
                     Watchdog heartbeat --> Uptime Kuma push monitor on kuma-1 (dead man's switch)
Uptime Kuma (off site) -- HTTP checks --> public URLs; push URLs <-- backup jobs
Grafana :3000 (through Traefik + SSO) -- queries --> Prometheus, Loki
```

Pull is the default: Prometheus scrapes every host on a narrow UFW rule. The one exception is Traefik's metrics entryPoint, which lives on Dokploy's overlay network; a local Alloy scrapes it and forwards the samples (recipe 4.9). Uptime Kuma runs off site on purpose: it is the only component that notices when the whole site, including the monitoring, is gone (4.10).

### 1.6 Log flow

```text
journald, /var/log/*, container json-file logs --> Alloy (every VM) -- push :3100 --> Loki on mon-1
Traefik access.log (JSON) --+--> Alloy ---------------------> Loki            ops questions, dashboards
                            +--> CrowdSec agent ------------> LAPI decisions  blocking at the edge
                            +--> Wazuh agent -- 1514/tcp ---> Wazuh manager   security alerts, retention
```

The same access log goes to three consumers because they answer different questions: Loki answers "which router returns 5xx since the deploy?", CrowdSec answers "is this IP attacking us right now?", and Wazuh answers "show me every denied login to Grafana in the last 90 days". All three are useless without real client IPs ([43 8.3](43-traefik-and-reverse-proxies.md#83-real-client-ip-lost)), and the file needs log rotation or it fills the disk (recipe 4.7).

### 1.7 Security event flow

```text
Wazuh agent (every VM) -- 1515/tcp enrollment, 1514/tcp events --> wazuh-manager on siem-1
  wazuh-manager: decoders + rules --> alerts --> Filebeat --> wazuh-indexer :9200 --> dashboard :443 (VPN only)
  high-level alerts --> email or Slack integration
CrowdSec agent --> LAPI :8080 <-- Traefik bouncer plugin (stream mode)
CrowdSec      <--> CAPI (outbound HTTPS): community blocklist in, your signals out
Trivy in CI, Harbor scan on push --> findings before deploy
```

The tools layer rather than overlap: Trivy stops known-vulnerable images before they run, CrowdSec blocks abusive clients at the edge, Wazuh watches hosts (file integrity, SSH and sudo, Docker events, package vulnerabilities), and on Kubernetes Falco would add runtime detection inside containers. Route their alerts into one place and agree who reads them, or nobody will.

### 1.8 Identity and secrets flow

```text
people   --> Authentik (auth.example.com) --> OIDC login for Grafana, GitLab, Harbor, Argo CD, Proxmox
                                          --> forward auth through Traefik for tools without login (4.5)
CI jobs  --> id_tokens JWT from GitLab --> OpenBao auth/jwt --> 5-minute token --> KV v2 secrets (4.3)
admins   --> OpenBao via OIDC (Authentik) or a personal token, every request in the audit log
runtime  --> Docker secrets (Swarm), Kubernetes Secrets, Dokploy environment variables
```

Apps that speak OIDC should use it directly; forward auth is for tools that have no login of their own. Keep a local break-glass admin for every tool that sits behind SSO, stored offline, because an Authentik outage must not lock you out of the monitoring you need to fix it.

### 1.9 Backup flow

```text
dokploy-1 : Dokploy database and panel backups --> s3-1 bucket dokploy-backups
            restic (systemd timer) ----------------> s3-1 bucket restic-dokploy-1          (4.11)
gitlab-1  : gitlab-backup + gitlab-secrets.json --> s3-1 bucket gitlab
bao-1     : raft snapshot ------------------------> s3-1 bucket openbao
k3s       : etcd snapshots + Velero --------------> s3-1 buckets k3s-etcd, velero
Proxmox   : vzdump of every VM ------------------> pbs-1 (8007/tcp) -- sync job --> off-site PBS
s3-1      : replication or rclone sync ----------> off-site S3 with object lock (immutable copy)
every job : success --> Uptime Kuma push URL + node_exporter textfile metric; silence --> alert
```

This follows 3-2-1 (three copies, two media, one off site) with one immutable copy, so a stolen production credential cannot delete every backup ([51 9.3](51-problems-databases-storage-backup.md#93-no-tested-restore-rto-and-rpo-in-the-disaster)). Two layers are deliberate: PBS restores a whole VM quickly, restic and the application dumps restore one volume or one database without rolling back everything else.

### 1.10 Admin access flow

```text
admin laptop -- 51820/udp --> OPNsense wg0 (10.99.0.1) --> firewall rules per VLAN
   allowed: 22 to every VM, 8006 to pve1-3, 8007 to pbs-1, 443 to siem-1 (Wazuh dashboard),
            443 to gitlab-1 and harbor-1, 6443 to k3s, 8200 to bao-1
   denied:  everything else, and nothing admin-facing is published on 203.0.113.10
out-of-band: IPMI/iDRAC on the mgmt VLAN, reachable only from the VPN, never from the apps VLAN
```

One VPN entry point with one key per person and device replaces a dozen admin ports on the internet (recipe 4.12). Tailscale, Headscale or NetBird do the same job as a mesh when admins roam a lot (2.12).

### 1.11 Port matrix

| Port | Service | Who connects | Exposure |
|---|---|---|---|
| 80/tcp, 443/tcp, 443/udp | dokploy-traefik | internet | **public**, and the only public web ports |
| 51820/udp | WireGuard on OPNsense | admins | **public**; silent to anyone without a key |
| 3000/tcp | Dokploy panel (host mode, bypasses UFW) | admins during setup | never public; close it once the panel has a domain |
| 8080/tcp | Traefik dashboard and API | nobody directly | never published; use the dashboard through a protected router |
| 8082/tcp | Traefik metrics entryPoint | Alloy on dokploy-network | Docker network only |
| 2377/tcp, 7946/tcp+udp, 4789/udp | Docker Swarm control, gossip, VXLAN | Swarm nodes | apps VLAN only |
| 6443/tcp | k3s API server | nodes, admins over VPN | k8s VLAN and VPN |
| 10250/tcp | kubelet | API server, metrics-server | k8s VLAN only |
| 443/tcp, 22/tcp | GitLab web and Git over SSH | users, runners | internal and VPN |
| 443/tcp | Harbor | runners, Docker and k3s nodes | internal |
| 8200/tcp, 8201/tcp | OpenBao API, cluster | runners and admins; OpenBao nodes | internal |
| 9100/tcp, 8089/tcp | node_exporter, cAdvisor | Prometheus on mon-1 | UFW: from 10.10.30.31 only |
| 9090, 9093, 9115/tcp | Prometheus, Alertmanager, blackbox | Grafana, admins through a tunnel | internal |
| 3100/tcp | Loki push and query | Alloy on every VM, Grafana | internal VLANs only |
| 3001/tcp | Uptime Kuma | its own TLS proxy | public status page only, admin UI behind VPN or SSO |
| 1514/tcp, 1515/tcp | Wazuh events, enrollment | agents | internal VLANs only |
| 55000/tcp | Wazuh API | dashboard, admins | internal |
| 9200/tcp | Wazuh indexer (OpenSearch) | manager (Filebeat), dashboard | localhost or internal; never public |
| 443/tcp on siem-1 | Wazuh dashboard | admins | VPN only |
| 8080/tcp, 6060/tcp | CrowdSec LAPI, metrics | bouncer plugin; Prometheus | dokploy-network only |
| 9000/tcp, 9443/tcp | Authentik | Traefik | Docker network; users reach it only through Traefik |
| 8006/tcp, 8007/tcp | Proxmox VE, Proxmox Backup Server | admins, PVE nodes | mgmt and backup VLANs, VPN |
| S3 API port | S3-compatible storage | backup clients | backup VLAN only |
| 22/tcp | SSH | admins over VPN, the automation host | VPN and internal, keys only |

Two rules make this table true in practice. Docker-published ports skip UFW, so bind them to 127.0.0.1 or an internal address and verify from outside ([42 3.1](42-problems-network-dns-tls-vpn.md#31-docker-publishes-ports-past-ufw), [44 4.4](44-problems-docker-swarm-registry.md#44-published-ports-bypass-ufw)). And "internal" still means a firewall rule naming the client subnet, not "anyone on the LAN".

### 1.12 Start smaller

| Size | VMs | What runs where | What you give up |
|---|---|---|---|
| Homelab (Fresher–Junior) | 1 VM, 4 vCPU / 8 GB / 100 GB | Dokploy with its Traefik, apps, Prometheus + Grafana + node_exporter as a Dokploy Compose app, restic to a NAS or USB disk; Uptime Kuma on a second cheap machine | separation: one disk-full or bad upgrade takes everything down |
| Small team (Junior–Mid) | 3 VMs | app VM: Dokploy and apps; build VM: GitLab, runner, Harbor (12–16 GB RAM); ops VM: monitoring and Wazuh (12 GB RAM) | high availability; builds compete with GitLab for memory |
| Platform (Senior) | the 14 VMs above | everything in 1.1 | nothing, but someone must own all of it |

Grow along the adoption calendar in 3.6. The one thing not to postpone is the off-site copy of your backups.

<div class="env" data-env="cloud" markdown="1">

**The same platform on AWS:** the edge becomes an ALB (or NLB) in front of ECS or EKS, Harbor becomes ECR with pull-through cache rules, the runner moves to EC2 or CodeBuild with an IAM role, OpenBao for CI becomes GitLab OIDC into an IAM role plus Secrets Manager, Authentik becomes IAM Identity Center federated with your identity provider, the Prometheus stack becomes CloudWatch or Amazon Managed Service for Prometheus and Managed Grafana, Wazuh agents stay but GuardDuty and Security Hub add managed findings, PBS and restic become AWS Backup with S3 Object Lock, and WireGuard becomes SSM Session Manager. The full table, with what changes when you troubleshoot each pair, is [Equivalents: on-prem and AWS](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws).

</div>

---

## 2. Tool-by-category decision tables

### 2.1 How to read the tables

- **Effort to run:** Low means one container, configuration in one file, and upgrades that rarely break. Medium means several parts or a database, and release notes you must read. High means several stateful components, a required upgrade order and your own sizing work.
- **Resources:** a homelab starting point, not production sizing. Real needs grow with users, series, agents or images.
- **Learning curve:** how long until you can debug it at 3 a.m., not how long until it first starts.
- **Common failure modes:** link to the problem entries that fix them. If a tool has few entries here, it is either very stable or rarely run on-prem; check its issue tracker before you rely on it.
- **Choose when:** the deciding question. Prefer what your team already runs, then what you can operate under pressure, and only then features. Ask "who gets paged when this breaks, and can they debug it?" before you add anything.

### 2.2 PaaS and orchestration

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Dokploy** | Git or image deploys to Docker Swarm behind Traefik v3, databases, S3 backups, a UI over plain Docker | Medium | 2 vCPU, 4 GB, 40 GB for the panel and a few apps | Low to start, Medium to debug (Swarm plus Traefik) | routes lost after a redeploy or upgrade ([45 6.1](45-dokploy-and-self-hosted-paas.md#61-compose-or-template-domain-gives-404), [45 6.6](45-dokploy-and-self-hosted-paas.md#66-image-app-404-after-a-webhook-redeploy)); Docker 29 needs Traefik 3.6.1 or later ([45 6.5](45-dokploy-and-self-hosted-paas.md#65-every-domain-404-after-docker-29)); port 3000 open past UFW ([45 13.2](45-dokploy-and-self-hosted-paas.md#132-panel-and-databases-open-past-ufw)); builds starving the host ([45 8.5](45-dokploy-and-self-hosted-paas.md#85-builds-exhaust-memory-on-the-server)) | your apps are containers, you want Heroku-style deploys, and you debug with `docker service ps` and Traefik's log: the reference platform's choice |
| **Coolify** | Compose-native deploys across many servers driven over SSH, a large one-click catalogue | Medium | 2 vCPU, 2 GB, 30 GB | Low | SSH to every server including itself; Docker 29 broke older pinned proxy images; one bad global proxy edit takes every site down ([troubleshooting docs](https://coolify.io/docs/troubleshoot/overview)) | the team thinks in Compose files and wants many servers without Swarm |
| **CapRover** | a mature, minimal Swarm PaaS with Nginx, Certbot and a CLI deploy flow | Low–Medium | 1 vCPU, 1 GB | Low | container HTTP port mismatch gives 502; "Has Persistent Data" only at creation; domain checks fail behind a proxied CDN ([troubleshooting docs](https://caprover.com/docs/troubleshooting.html)) | you want small and stable, and Nginx is fine as the edge |
| **Portainer CE** | a UI over existing Docker, Swarm or Kubernetes: stacks, logs, consoles | Low | 1 vCPU, 512 MB | Low | five-minute window to create the first admin, environment down ([44 7.1](44-problems-docker-swarm-registry.md#71-portainer-timed-out-lost-password-environment-down)); stack variables and paths ([44 7.2](44-problems-docker-swarm-registry.md#72-portainer-stacks-variables-paths-and-limited-stacks)); the socket mount equals root | you need visibility and stack editing, not builds, domains and certificates; keep it read-only next to Dokploy |
| **k3s** | real Kubernetes on small hardware: one binary with containerd, Flannel, CoreDNS, Traefik, ServiceLB, local-path | Medium–High | 2 vCPU, 4 GB per server; three servers for embedded-etcd HA | High (it is Kubernetes) | bundled Traefik next to another ingress ([46 6.2](46-problems-kubernetes.md#62-ingress-returns-404-class-two-controllers-k3s-traefik)); Harbor CA and registries.yaml ([46 2.4](46-problems-kubernetes.md#24-images-crictl-ctr-and-harbors-private-ca)); etcd snapshot and restore ([46 13.3](46-problems-kubernetes.md#133-etcd-backup-and-restore-kubeadm-and-k3s)) | a workload needs Kubernetes APIs (operators, Helm charts, GitOps), several teams share the platform, or you are on the CKA track |

**Pick this way:** start with Dokploy. Add k3s next to it, not instead of it, when a workload needs Kubernetes features, and move apps one at a time. A PaaS stops being enough when you need per-team RBAC, autoscaling on custom metrics or operators ([45: when a PaaS stops being enough](45-dokploy-and-self-hosted-paas.md#when-a-paas-stops-being-enough)). Whatever you choose, one control plane owns each app.

### 2.3 Reverse proxies

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Traefik v3** | routes discovered from Docker, Swarm and Kubernetes; ACME; middlewares (forward auth, CrowdSec, rate limits) | Low–Medium | 100–200 MB RAM | Medium: routers, services, middlewares and the static/dynamic split | 404 with no router ([43 5.1](43-traefik-and-reverse-proxies.md#51-traefik-answers-404-page-not-found)); 502 and wrong network ([43 5.2](43-traefik-and-reverse-proxies.md#52-traefik-returns-502-bad-gateway), [43 5.3](43-traefik-and-reverse-proxies.md#53-504-or-flapping-container-on-several-networks)); default certificate ([43 6.1](43-traefik-and-reverse-proxies.md#61-traefik-default-cert-instead-of-lets-encrypt)); Docker 29 ([43 7.2](43-traefik-and-reverse-proxies.md#72-docker-29-every-route-vanished)); the 60 s readTimeout cutting uploads ([43 15.1](43-traefik-and-reverse-proxies.md#151-docker-push-and-big-uploads-fail-through-the-proxy)) | containers come and go, and it is already inside Dokploy and k3s |
| **Caddy** | the simplest automatic HTTPS; small sites with a short Caddyfile | Low | about 50 MB | Low | certificate issuance ([43 12.1](43-traefik-and-reverse-proxies.md#121-caddy-cant-get-a-certificate)); DNS providers need a custom build; unpersisted /data re-issues certificates; the subfolder problem ([43 9.4](43-traefik-and-reverse-proxies.md#94-the-subfolder-problem)) | a handful of hosts and no container discovery needed |
| **Nginx / Nginx Proxy Manager** | static files and fast proxying, the most documented proxy; NPM adds a homelab UI | Low (NPM: Low, but the UI hides errors) | tiny | Medium: directive inheritance, buffering, keepalive | 502/504 from the error log ([43 10.1](43-traefik-and-reverse-proxies.md#101-nginx-502-and-504-read-the-errorlog-line)); 413 ([43 10.2](43-traefik-and-reverse-proxies.md#102-413-request-entity-too-large)); NPM certificate errors and admin Bad Gateway ([43 14.1](43-traefik-and-reverse-proxies.md#141-npm-certificate-errors-or-login-bad-gateway)); ingress-nginx retired ([43 8.5](43-traefik-and-reverse-proxies.md#85-kubernetes-ingress-after-ingress-nginx-retired)) | static configuration, or you learn proxies with KodeKloud's Nginx labs; NPM for homelabs only |
| **HAProxy** | TCP and HTTP load balancing: Kubernetes API, databases, PROXY protocol, stick tables | Medium | tiny | Medium–High: ACLs and termination flags | fails to start ([43 13.1](43-traefik-and-reverse-proxies.md#131-haproxy-fails-to-start)); 503/504 from checks ([43 13.2](43-traefik-and-reverse-proxies.md#132-haproxy-503-and-504-checks-and-flags)) | you balance TCP, or front three k3s servers or a keepalived pair |
| **Apache httpd** | legacy PHP vhosts and the mod_* ecosystem | Low | small | Medium | won't start after proxy changes ([43 11.1](43-traefik-and-reverse-proxies.md#111-apache-wont-start-after-proxy-changes)); fighting Traefik for 443 ([21 case](21-case-apache-443-dokploy.md), [45 6.7](45-dokploy-and-self-hosted-paas.md#67-legacy-apache-behind-dokploys-traefik)) | you inherit it: keep it behind Traefik on 81/444, as in your own incident |

**Pick this way:** exactly one proxy owns 80/443 on a host; everything else sits behind it. Learn one proxy deeply and map the others onto it: nginx server blocks, Apache vhosts, Traefik routers, Caddy site blocks and HAProxy frontends all route by Host or SNI to a backend; they differ in discovery, TLS automation and defaults ([29 webservers and proxies](29-learn-webservers-proxies.md)).

### 2.4 CI/CD and GitOps

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **GitLab CI** | Git, CI, registry and environments in one product | High for GitLab itself, Low–Medium for runners | GitLab 4 vCPU, 8 GB; a runner 2–4 vCPU per concurrent build | Medium | job pending, no runner matches ([47 5.1](47-cicd-gitlab-jenkins-actions-argocd.md#51-job-stuck-pending-no-runner-matches)); protected variables empty ([47 5.4](47-cicd-gitlab-jenkins-actions-argocd.md#54-protected-variables-arrive-empty)); dind TLS ([47 6.1](47-cicd-gitlab-jenkins-actions-argocd.md#61-cannot-connect-to-the-docker-daemon-in-dind)); x509 to Harbor ([47 7.2](47-cicd-gitlab-jenkins-actions-argocd.md#72-push-to-harbor-fails-with-x509)); runner disk full ([47 8.1](47-cicd-gitlab-jenkins-actions-argocd.md#81-runner-disk-full)); kaniko archived ([47 6.5](47-cicd-gitlab-jenkins-actions-argocd.md#65-kaniko-is-archived-moving-to-buildah)) | the default on-prem; it is your stack |
| **Jenkins** | complex or legacy pipelines, non-container builds, a huge plugin ecosystem | High | controller 2 vCPU, 4 GB, plus agents | Medium–High (Groovy, plugins) | a plugin update breaks jobs ([47 10.2](47-cicd-gitlab-jenkins-actions-argocd.md#102-a-plugin-update-breaks-jobs-or-login)); crumb errors behind a proxy ([47 10.3](47-cicd-gitlab-jenkins-actions-argocd.md#103-no-valid-crumb-or-403-behind-a-proxy)); builds on the controller ([47 10.4](47-cicd-gitlab-jenkins-actions-argocd.md#104-builds-run-on-the-controller-and-fill-it)); Java 21 or 25 required from LTS 2.555.1 | an employer already runs it; then build the controller with JCasC from day one |
| **GitHub Actions (self-hosted runners)** | code on GitHub that needs your network or hardware | Low–Medium | small runner VM | Low | waiting for a runner ([47 11.1](47-cicd-gitlab-jenkins-actions-argocd.md#111-waiting-for-a-runner-to-pick-up-the-job)); jobs lost mid-run ([47 11.2](47-cicd-gitlab-jenkins-actions-argocd.md#112-self-hosted-job-lost-or-cancelled-mid-run)); never attach self-hosted runners to public repositories | GitHub is the forge |
| **Woodpecker** | lightweight container-native CI for Gitea or Forgejo | Low | about 100 MB for the server | Low | few enterprise features; a smaller community ([docs](https://woodpecker-ci.org/)) | a homelab or small team on Forgejo |

| GitOps tool | Best for | Effort to run | Common failure modes | Choose when |
|---|---|---|---|---|
| **Argo CD** | a UI, app-of-apps, multi-cluster, SSO; renders Helm with `helm template` | Medium | OutOfSync right after a sync ([47 12.1](47-cicd-gitlab-jenkins-actions-argocd.md#121-outofsync-right-after-a-successful-sync)); Progressing forever on-prem ([47 12.2](47-cicd-gitlab-jenkins-actions-argocd.md#122-stuck-in-progressing-on-prem)); cannot reach Git or its CA ([47 12.3](47-cicd-gitlab-jenkins-actions-argocd.md#123-argo-cd-cant-reach-git-helm-or-its-api)); prune deletes too much ([46 12.2](46-problems-kubernetes.md#122-automated-prune-deletes-more-than-intended)) | developers want to see what is deployed; your Kubernetes default |
| **Flux** | a CRD toolkit with no UI by default, image automation, native sops decryption | Medium | reconciliation stuck after retries ([47 12.6](47-cicd-gitlab-jenkins-actions-argocd.md#126-flux-reconciliation-stuck)); path and branch mistakes | a platform team that wants everything as CRDs and a small footprint ([docs](https://fluxcd.io/flux/)) |

**Pick this way:** GitLab CI for building and testing everywhere; push deploys (the pipeline calls Dokploy) for Swarm apps; pull-based GitOps (Argo CD) for Kubernetes. Seniors standardise on one shared CI template, pinned images and runners split by trust level, so a fix lands in one place.

### 2.5 Registries

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Harbor** | projects, robot accounts, Trivy scans, replication, proxy cache, retention | Medium; upgrades only from the previous two minor versions | 2 vCPU, 4 GB, 40 GB plus images | Medium | down after a reboot ([44 9.1](44-problems-docker-swarm-registry.md#91-harbor-down-after-a-reboot-or-upgrade)); disk still full until GC runs ([44 9.2](44-problems-docker-swarm-registry.md#92-disk-still-full-after-deleting-tags)); `robot$` names and 401s ([44 9.3](44-problems-docker-swarm-registry.md#93-robot-accounts-robot-names-and-401s)); behind Traefik ([44 9.4](44-problems-docker-swarm-registry.md#94-harbor-behind-traefik-or-nginx)); x509 from clients ([44 5.3](44-problems-docker-swarm-registry.md#53-x509-unknown-authority-for-a-private-registry)) | several teams, scanning and a Docker Hub cache, and a registry that survives a GitLab outage |
| **GitLab Container Registry** | zero extra services; permissions follow GitLab projects | Low (part of GitLab) | part of GitLab's storage | Low | storage growth without cleanup policies; down whenever GitLab is down or upgrading | a small team that only uses GitLab |
| **Nexus Repository** | many formats: Maven, npm, PyPI, Docker, raw | Medium–High | 4 vCPU, 8 GB | Medium | Docker needs its own connector port; cleanup plus compact tasks; free-space threshold ([47 13.3](47-cicd-gitlab-jenkins-actions-argocd.md#133-nexus-proxy-repositories-fail-from-ci)) | you also need language package proxies |

**Pick this way:** Harbor for the reference platform (recipes 4.1 and 4.2). Whatever you run becomes tier-0: if it is down, nothing builds and no new container starts, so it gets monitoring, backups and a disk alert like a database.

### 2.6 Monitoring

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Prometheus + Alertmanager + Grafana + exporters** | metrics for hosts, containers and Kubernetes; PromQL; alert routing | Medium | 2 vCPU, 4 GB for a small fleet (series count decides) | Medium–High (PromQL, relabeling) | target down ([49 5.1](49-observability-stack-problems.md#51-target-down-refused-or-deadline-exceeded)); relabeling ([49 5.6](49-observability-stack-problems.md#56-relabeling-does-nothing-or-drops-targets)); cardinality OOM ([49 11.4](49-observability-stack-problems.md#114-memory-grows-until-oom-cardinality)); alerts nobody receives ([49 8.1](49-observability-stack-problems.md#81-alerts-fire-but-nobody-is-notified)); Prometheus 2 to 3 ([49 11.2](49-observability-stack-problems.md#112-prometheus-2-to-3-upgrade-breaks-things)) | the default, and the PCA exam path |
| **Zabbix** | classic agent fleets, SNMP and network gear, templates, inventory | Medium–High (database tuning) | 2 vCPU, 4 GB plus the database | Medium | agent unreachable, server not running ([49 7.3](49-observability-stack-problems.md#73-zabbix-agent-unreachable-or-server-not-running)); processes more than 75% busy ([49 7.4](49-observability-stack-problems.md#74-zabbix-processes-more-than-75-busy)) | you inherit a server and network estate, or need SNMP |
| **Netdata** | per-second charts on one host with no configuration | Low | 100–300 MB per node | Low | container IDs instead of names, alert floods ([49 7.2](49-observability-stack-problems.md#72-netdata-container-ids-and-alert-floods)) | you debug one slow host live ([23 slow system](23-playbook-slow-system.md)); not the alerting backbone |
| **Uptime Kuma** | "is it up" checks, certificate expiry, push monitors, status pages | Low | 256–512 MB | Low | false downs and a slow database ([49 7.1](49-observability-stack-problems.md#71-uptime-kuma-false-downs-and-a-slow-database)); /app/data on NFS is unsupported; 2.0 needs Node.js 20.4+ ([migration notes](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2)) | always, as the outside watcher that also watches your monitoring (4.10) |

**Pick this way:** Prometheus for depth, Uptime Kuma for the outside view, Netdata when a single host is slow right now. Zabbix earns its place only when SNMP devices or an existing Zabbix estate are involved; running both Zabbix and Prometheus for the same hosts doubles the pages.

### 2.7 Logging

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Loki + Alloy** | logs indexed by labels, cheap storage, LogQL next to your Grafana dashboards | Medium | 1–2 GB for the single binary | Medium (label design) | Promtail end of life, Alloy ships nothing ([49 9.1](49-observability-stack-problems.md#91-promtail-is-end-of-life-alloy-ships-no-logs)); the Docker driver freezes containers ([49 9.2](49-observability-stack-problems.md#92-the-loki-docker-driver-freezes-containers)); 429 and "too old" ([49 9.3](49-observability-stack-problems.md#93-loki-rejects-pushes-429-and-too-old)); retention needs the compactor ([49 9.4](49-observability-stack-problems.md#94-loki-disk-grows-despite-retention)) | you already run Grafana and mostly ask "what did this service log around 14:05?" |
| **Elasticsearch / OpenSearch** | full-text search over large volumes; Kibana or Dashboards analytics | High (heap, shards, ILM or ISM) | 8 GB RAM and up | High | won't start or refuses clients ([49 10.1](49-observability-stack-problems.md#101-search-cluster-wont-start-or-refuses-clients)); read-only indices and the shard limit ([49 10.4](49-observability-stack-problems.md#104-read-only-indices-yellow-health-shard-limit)); timestamps and grok ([49 10.3](49-observability-stack-problems.md#103-ingest-wrong-timestamps-grok-failures-_type)) | heavy full-text search; remember that the Wazuh indexer is already OpenSearch |
| **Graylog** | a ready log console with streams, pipelines and alerts | Medium–High (MongoDB with AVX, plus OpenSearch) | 8 GB | Medium | won't start or login fails ([49 10.2](49-observability-stack-problems.md#102-graylog-wont-start-or-the-login-fails)); journal utilization too high ([49 10.5](49-observability-stack-problems.md#105-graylog-journal-utilization-too-high)); MongoDB needs an AVX-capable CPU type on Proxmox ([51 4.5](51-problems-databases-storage-backup.md#45-mongodb-exits-with-illegal-instruction)) | a team wants a log UI without building dashboards |

**Pick this way:** Loki for operations, Wazuh's indexer for security events, and no third log store unless someone needs full-text search over gigabytes a day. Never use a client IP, user ID or request ID as a Loki label; filter on them in the query instead.

### 2.8 Security tools

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Wazuh** | host SIEM: log analysis, file integrity, SCA, vulnerability detection, active response | High | 4 vCPU, 8 GB, 50 GB for 1–25 agents | High | agent never connects ([48 5.1](48-wazuh-and-security-tools.md#51-agent-never-connects)); dashboard "not ready yet" ([48 6.1](48-wazuh-and-security-tools.md#61-dashboard-server-is-not-ready-yet)); disk watermark ([48 6.4](48-wazuh-and-security-tools.md#64-disk-watermark-made-indices-read-only)); shard limit ([48 6.5](48-wazuh-and-security-tools.md#65-maximum-shards-open-10001000)); upgrade order ([48 7.9](48-wazuh-and-security-tools.md#79-an-upgrade-breaks-the-stack)); fighting Traefik for 443 ([48 7.8](48-wazuh-and-security-tools.md#78-wazuh-dashboard-and-traefik-fight-for-443)) | you need an audit trail, FIM and security alerts across hosts, or a compliance requirement |
| **CrowdSec** | behaviour detection from logs, a community blocklist, bouncers for Traefik and the firewall | Low–Medium | 100–200 MB | Medium | decisions but no blocking ([48 8.1](48-wazuh-and-security-tools.md#81-decisions-exist-but-nothing-is-blocked)); every client has the same IP ([48 8.2](48-wazuh-and-security-tools.md#82-every-client-shows-the-same-ip)); logs read but not parsed ([48 8.3](48-wazuh-and-security-tools.md#83-logs-read-but-not-parsed)); LAPI port and keys ([48 8.4](48-wazuh-and-security-tools.md#84-lapi-unreachable-port-8080-and-keys)); false positives ([48 8.5](48-wazuh-and-security-tools.md#85-false-positives-ban-real-users)) | public web apps behind Traefik |
| **Fail2ban** | regex on one host's logs, then a firewall ban | Low | tiny | Low | bans don't stop Docker traffic ([48 9.1](48-wazuh-and-security-tools.md#91-bans-do-not-stop-docker-traffic)); fails to start on 24.04 ([48 9.2](48-wazuh-and-security-tools.md#92-fail2ban-fails-to-start-on-ubuntu-2404)); filter matches nothing ([48 9.3](48-wazuh-and-security-tools.md#93-filter-matches-nothing)) | SSH on a single host; use CrowdSec for anything with Docker in front |
| **Falco** | runtime detection inside containers and Kubernetes (syscalls through eBPF): a shell in a container, writes below /etc | Medium | one agent per node | Medium–High | noisy default rules on busy nodes; kernel and driver compatibility after node upgrades ([docs](https://falco.org/docs/)) | Kubernetes workloads that need runtime detection (a CKS topic) |
| **Trivy** | scanning images, filesystems, IaC, secrets and SBOMs in CI and inside Harbor | Low | a CLI plus a cached vulnerability DB | Low | toomanyrequests downloading the DB ([48 10.1](48-wazuh-and-security-tools.md#101-toomanyrequests-downloading-the-db)); x509 scanning Harbor images ([48 10.2](48-wazuh-and-security-tools.md#102-x509-errors-scanning-harbor-images)); pipelines blocked by unfixable CVEs ([48 10.3](48-wazuh-and-security-tools.md#103-pipeline-blocked-by-unfixable-cves)) | always, in every pipeline that builds an image |

**Pick this way:** the tools layer by position. Trivy before deploy, CrowdSec at the edge, Wazuh on every host, Falco inside Kubernetes when you run it. Fail2ban stays useful for SSH on hosts that have no Docker in front.

### 2.9 Secrets

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **OpenBao / HashiCorp Vault** | central, audited, short-lived and dynamic secrets; PKI | High (unsealing, raft HA, audit storage) | 1–2 GB per node; three nodes for HA | High | sealed after every restart ([48 11.1](48-wazuh-and-security-tools.md#111-sealed-after-every-restart)); KV v2 permission denied ([48 11.2](48-wazuh-and-security-tools.md#112-permission-denied-on-kv-v2-secrets)); raft join ([48 11.3](48-wazuh-and-security-tools.md#113-raft-node-cannot-join-the-cluster)); a full audit disk blocks every request ([48 11.4](48-wazuh-and-security-tools.md#114-audit-log-disk-full-blocks-every-request)) | many pipelines and services, audit requirements, rotation. Vault moved to the Business Source License in 2023; OpenBao is the MPL-licensed fork with the same API |
| **sops + age** | encrypted secret files in Git, decrypted at deploy time | Low | a CLI | Low | a lost age key means lost secrets; decrypted files left on disk or printed in CI logs ([repository](https://github.com/getsops/sops)) | GitOps repositories, Flux, Ansible, small teams |
| **Docker and Kubernetes Secrets** | delivering a secret to a running container | Low (built in) | none | Low | Swarm secrets are immutable ([44 8.6](44-problems-docker-swarm-registry.md#86-secrets-and-configs-cant-be-updated)); Kubernetes Secrets are only base64 unless encryption at rest is on | the last hop, never the source of truth |
| **GitLab CI/CD variables** | the first place secrets live | Low | none | Low | protected variables empty ([47 5.4](47-cicd-gitlab-jenkins-actions-argocd.md#54-protected-variables-arrive-empty)); masking and `$` expansion ([47 5.5](47-cicd-gitlab-jenkins-actions-argocd.md#55-masked-values-and-dollar-sign-expansion)); secrets leaking into job logs ([47 13.4](47-cicd-gitlab-jenkins-actions-argocd.md#134-secrets-leak-into-job-logs)) | start here; move to OpenBao when secrets are shared across many projects |

**Pick this way:** GitLab variables first, sops for secrets that belong in a Git repository, OpenBao once you need audit, rotation or short-lived credentials. Plan unsealing and audit storage before production; that is the lesson operators repeat most often.

### 2.10 SSO

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **Authentik** | an identity provider with flows, OIDC, SAML, LDAP and a proxy provider for Traefik forward auth | Medium | 2 vCPU, 2 GB plus PostgreSQL | Medium | outpost path 404 ([48 13.1](48-wazuh-and-security-tools.md#131-forward-auth-returns-404-on-the-outpost-path)); login loops ([48 13.2](48-wazuh-and-security-tools.md#132-login-loops-or-lands-on-authentik)); no workers after an upgrade ([48 13.3](48-wazuh-and-security-tools.md#133-no-workers-connected-after-an-upgrade)); forward-auth 504s ([43 8.2](43-traefik-and-reverse-proxies.md#82-forward-auth-loops-404s-and-504s)) | one UI for SSO and forward auth in a small or medium organisation |
| **Keycloak** | standards-heavy IAM: OIDC, SAML, AD/LDAP federation, many realms | Medium–High | 2 GB plus PostgreSQL | Medium–High | "HTTPS required" and wrong redirects behind Traefik ([48 12.1](48-wazuh-and-security-tools.md#121-https-required-and-wrong-redirects-behind-traefik)); stuck on the database lock ([48 12.2](48-wazuh-and-security-tools.md#122-startup-stuck-on-the-database-lock)); health checks on port 9000 ([48 12.3](48-wazuh-and-security-tools.md#123-health-checks-fail-after-upgrading)) | enterprise integrations and Active Directory federation |
| **Authelia** | a light login portal with 2FA for forward auth, configured in YAML | Low | 50–100 MB | Low | old guides use /api/verify instead of /api/authz/forward-auth; the middleware applied to Authelia's own router; trusting too many proxy IPs ([Traefik integration](https://www.authelia.com/integration/proxies/traefik/)) | you only need a login wall with 2FA in front of a few apps |

**Pick this way:** Authentik for the reference platform. Whatever you choose becomes tier-0 for every protected app, so it gets two replicas or at least a tested restore, and each app keeps a break-glass login.

### 2.11 Backup and object storage

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **restic** | encrypted, deduplicated file and volume backups to S3, SFTP or rest-server | Low | a CLI; RAM grows with repository size | Low | repository locked ([51 5.2](51-problems-databases-storage-backup.md#52-backup-repository-is-already-locked)); check finds errors ([51 5.6](51-problems-databases-storage-backup.md#56-restic-check-repository-contains-errors)); lost password ([51 5.3](51-problems-databases-storage-backup.md#53-encrypted-backup-lost-password-or-key)); jobs that stop silently ([51 5.4](51-problems-databases-storage-backup.md#54-backups-stopped-silently-or-are-empty)) | host-level backups to S3-compatible storage (recipe 4.11) |
| **BorgBackup** | the same idea over SSH, with append-only mode and fast compression | Low | a CLI | Low | the same lock and key entries; append-only needs an SSH forced command ([FAQ](https://borgbackup.readthedocs.io/en/stable/faq.html)) | you back up to an SSH box rather than S3 |
| **Proxmox Backup Server** | incremental, deduplicated VM and container backups, verify jobs, off-site sync | Medium | 4 vCPU, 8 GB plus the datastore | Medium | datastore full after prune and GC ([50 8.2](50-problems-cloud-iac-proxmox.md#82-pbs-datastore-full-and-gc-frees-nothing), [51 5.5](51-problems-databases-storage-backup.md#55-pbs-datastore-full-after-prune-and-gc)); VM locked by a backup ([50 8.1](50-problems-cloud-iac-proxmox.md#81-vm-locked-or-frozen-by-a-backup)) | anything running on Proxmox |
| **Velero** | Kubernetes objects plus volume data to S3 | Medium | in-cluster pods | Medium | "Completed" but the restored database is empty ([51 9.2](51-problems-databases-storage-backup.md#92-velero-completed-restored-database-empty)); S3-compatible endpoints ([51 6.1](51-problems-databases-storage-backup.md#61-s3-targets-fail-style-region-ca-clock), [51 6.3](51-problems-databases-storage-backup.md#63-new-aws-sdk-checksums-break-uploads)) | k3s or Kubernetes workloads; still dump databases at the application level |

**Object storage under the backups:** MinIO Community Edition is archived and no longer ships binaries or images ([51 6.5](51-problems-databases-storage-backup.md#65-minio-community-edition-is-archived)). If you run it, pin the current image digest and plan a move; the usual candidates are Garage (small, geo-distributed), SeaweedFS, RustFS (newer) and Ceph RGW (heavy but mature), compared in [this overview](https://blog.elest.io/rustfs-vs-seaweedfs-vs-garage-which-minio-alternative-should-you-pick/). Keep backups portable (restic repositories and plain S3 objects), so the storage underneath can change without touching the backup tools.

**Pick this way:** PBS for whole VMs, restic for volumes and files, native dumps for databases, Velero for Kubernetes, and an immutable off-site copy for all of them.

### 2.12 VPN and admin access

| Tool | Best for | Effort to run | Resources | Learning curve | Common failure modes | Choose when |
|---|---|---|---|---|---|---|
| **WireGuard** | a fixed hub with static peers; in the Linux kernel and in OPNsense | Low | tiny | Low–Medium (silent by design) | no handshake ([42 8.1](42-problems-network-dns-tls-vpn.md#81-wireguard-no-handshake)); handshake but no traffic ([42 8.2](42-problems-network-dns-tls-vpn.md#82-wireguard-handshake-fine-no-traffic)); MTU ([42 10.2](42-problems-network-dns-tls-vpn.md#102-containers-inside-a-tunnel-or-overlay-hang)) | a handful of admins and one site (recipe 4.12) |
| **Tailscale** | a mesh with NAT traversal, MagicDNS and SSO, run by a SaaS control plane | Very low | tiny | Low | only relayed connections ([42 9.1](42-problems-network-dns-tls-vpn.md#91-tailscale-connects-only-through-a-relay)); subnet routers and 100.64.0.0/10 conflicts ([42 9.2](42-problems-network-dns-tls-vpn.md#92-subnet-router-exit-node-or-10064-conflicts)) | many roaming devices, and a SaaS coordinator is acceptable |
| **Headscale** | a self-hosted Tailscale control server | Medium | small | Medium | behind a reverse proxy ([42 9.3](42-problems-network-dns-tls-vpn.md#93-headscale-behind-a-reverse-proxy)); Cloudflare proxying unsupported; embedded DERP needs UDP 3478 | Tailscale's experience without the SaaS |
| **NetBird** | a self-hostable mesh with management, signal and relay servers, ACL groups and routing peers | Medium | small | Medium | peers relayed or resources unreachable ([42 9.4](42-problems-network-dns-tls-vpn.md#94-netbird-peers-relayed-or-resources-unreachable)) | a self-hosted mesh with a UI and access groups |

**Pick this way:** WireGuard on the firewall for a small team in one place; a mesh (Tailscale, Headscale or NetBird) when people and servers are spread out. Either way, admin UIs are reachable only through it.

### 2.13 Practise and compare with AWS

| Category | Where to practise | AWS equivalent | Compare in |
|---|---|---|---|
| PaaS and containers | [Practice Arena: Docker](54-practice-arena.md#5-docker-and-containers) | ECS on Fargate or EC2 | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| Kubernetes | [Practice Arena: Kubernetes and the CKA](54-practice-arena.md#6-kubernetes-and-the-cka) | EKS | [55 cloud path](55-paths-onprem-vs-cloud.md#5-cloud-path-fresher-to-senior) |
| Reverse proxy, TLS, VPN | [Practice Arena: networking, DNS and TLS](54-practice-arena.md#4-networking-dns-and-tls) | ALB and NLB, ACM, Client VPN, SSM Session Manager | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| CI/CD and IaC | [Practice Arena: IaC and CI/CD](54-practice-arena.md#8-iac-and-cicd) | CodeBuild or runners on EC2, GitLab OIDC roles | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| Registry | [Practice Arena: Docker](54-practice-arena.md#5-docker-and-containers) | ECR with pull-through cache | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| Monitoring and logging | [Practice Arena: observability](54-practice-arena.md#9-observability) | CloudWatch, Managed Prometheus and Grafana, OpenSearch Service | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| Security, secrets, SSO | [Practice Arena: defensive security](54-practice-arena.md#11-defensive-security) | GuardDuty, Security Hub, Inspector, Secrets Manager, IAM Identity Center | [55 equivalents](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) |
| Backups and databases | [Practice Arena: databases](54-practice-arena.md#12-databases-and-sql) | AWS Backup, snapshots, S3 Object Lock | [55: where the data lives](55-paths-onprem-vs-cloud.md#where-the-data-lives) |
| Incidents on the whole platform | [Practice Arena: SRE and incidents](54-practice-arena.md#10-sre-incidents-and-devops-culture) | the same drills, with CloudTrail as the audit log | [55 hybrid](55-paths-onprem-vs-cloud.md#6-hybrid-running-both) |

---

## 3. Adoption order by career stage

Tools are not learned in alphabetical order. Each stage below adds tools that depend on the ones before it, and each ends with an exit check you can run on your own lab. The three columns mean: **install** (you can set it up from the docs), **operate** (you keep it healthy, upgrade it and fix its common failures), **design** (you decide whether it belongs on the platform and how it connects).

| Stage | Install | Operate | Design |
|---|---|---|---|
| Fresher (L0) | Docker, Compose, Traefik or Caddy with one app, Uptime Kuma, restic to a local disk | read container logs, restart a service, renew a certificate on staging | nothing yet: draw what exists |
| Junior (L1) | Dokploy, a GitLab runner, node_exporter, Prometheus and Grafana, a WireGuard peer, Fail2ban for SSH | deploys, domains, environment variables, disk cleanup, a broken pipeline | one app's deploy path |
| Mid-level (L2) | Harbor with the private CA, Loki with Alloy, Alertmanager, Wazuh all-in-one, CrowdSec, Trivy in CI | Traefik 404/502/504 from logs, alert routing, Wazuh agents and indices, registry GC | the logging and alerting flow for a team |
| Senior (L3) | Authentik, OpenBao, k3s with Argo CD, cert-manager and MetalLB, Proxmox Backup Server, Terraform or OpenTofu for Proxmox | upgrades in the right order, restores, capacity, certificates across the platform | the whole reference platform, the port matrix, the upgrade policy |
| Senior/Lead (L4) | whatever the team needs, by delegating | DR game days, on-call health, cost, security reviews | which tools exist at all, their owners, and when to retire them |

### 3.1 Fresher (L0)

**Learn:** Linux basics, Git, the Docker CLI and Compose, one reverse proxy with automatic HTTPS, an uptime check, a file backup and its restore.

**Courses and labs:** KodeKloud [Learning Linux Basics Course & Labs](https://kodekloud.com/courses/the-linux-basics-course), [Docker Training Course for the Absolute Beginner](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner), [GIT for Beginners](https://kodekloud.com/courses/git-for-beginners), and the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) for your experiments.

**Handbook:** [Learn Docker](30-learn-docker.md), [Learn web servers and proxies](29-learn-webservers-proxies.md), [DevOps day to day: a fresher's day](52-devops-day-to-day.md#fresher-l0-a-day), [Practice Arena fresher plan](54-practice-arena.md#fresher-plan-l0).

**Exit check (2 hours, fresh VM):** Docker plus Traefik or Caddy serving a demo app over HTTPS from the Let's Encrypt staging CA; Uptime Kuma checking it every minute; a restic backup of the app's volume restored into another folder and compared with `diff -r`. Then explain, in five sentences, what happens between typing the URL and seeing the page.

### 3.2 Junior (L1)

**Learn:** a PaaS as an operator (Dokploy), Traefik's routers and services, a CI pipeline that builds and deploys, host metrics and one dashboard, SSH hardening, a VPN peer.

**Courses and labs:** KodeKloud [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course) (the Swarm section is how Dokploy runs), [GitLab CI/CD](https://kodekloud.com/courses/gitlab-ci-cd), [Nginx For Beginners](https://kodekloud.com/courses/nginx-for-beginners) (proxy concepts you then map onto Traefik), [Prometheus Certified Associate](https://kodekloud.com/courses/prometheus-certified-associate-pca) (the fundamentals and node_exporter sections), the [CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd).

**Handbook:** [Dokploy in 10 minutes](45-dokploy-and-self-hosted-paas.md#1-dokploy-in-10-minutes), [Traefik in 10 minutes](43-traefik-and-reverse-proxies.md#1-traefik-in-10-minutes), [GitLab CI in 10 minutes](47-cicd-gitlab-jenkins-actions-argocd.md#1-gitlab-ci-in-10-minutes), [observability install](49-observability-stack-problems.md#2-install-and-first-configuration). Recipes 4.2, 4.9, 4.11.

**Exit check (half a day):** a commit on main reaches Dokploy through the pipeline; a Grafana panel shows the host's CPU, memory and disk; an alert fires when you fill the disk past 85% with `fallocate`; you fix a 502 you caused on purpose (wrong container port) using only Traefik's access log.

### 3.3 Mid-level (L2)

**Learn:** a private registry with your own CA, centralised logs, alert routing and inhibition, a SIEM with agents, edge blocking, image scanning, and troubleshooting across tools.

**Courses and labs:** KodeKloud [Grafana Loki](https://kodekloud.com/courses/grafana-loki) (Alloy and LogQL labs), [Prometheus Certified Associate](https://kodekloud.com/courses/prometheus-certified-associate-pca) (alerting), [Demystifying DNS](https://kodekloud.com/courses/demystifying-dns), the [LFCS prep course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs) (certificates, firewalls), the KodeKloud community post on [Harbor](https://kodekloud.com/community/t/setting-up-your-own-container-registry-with-harbor/275367) (there is no Harbor or Wazuh course; use the [Wazuh proof-of-concept guide](https://documentation.wazuh.com/current/proof-of-concept-guide/index.html)).

**Handbook:** [Harbor operations](44-problems-docker-swarm-registry.md#9-harbor-operations), [Wazuh install](48-wazuh-and-security-tools.md#2-install-and-first-configuration), [CrowdSec and the bouncer](48-wazuh-and-security-tools.md#8-crowdsec-and-the-traefik-bouncer), [Loki and Alloy problems](49-observability-stack-problems.md#9-logs-and-traces-loki-alloy-and-tempo). Recipes 4.1, 4.6, 4.7, 4.8, 4.10.

**Exit check (timed drill, 45 minutes):** a colleague breaks one thing (a wrong Traefik port, a stopped Wazuh agent, Loki rejecting pushes, an expired Harbor robot account). You find it from Grafana, Loki and Wazuh alone, fix it, and write the five-line note: symptom, evidence, cause, fix, prevention.

### 3.4 Senior (L3)

**Learn:** identity and secrets for the whole platform, Kubernetes with GitOps, VM-level backups and restores, infrastructure as code for Proxmox, and upgrade policy.

**Courses and labs:** KodeKloud [Certified Kubernetes Administrator (CKA)](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator), [Helm for Beginners](https://kodekloud.com/courses/helm-for-beginners), [Kubernetes Networking Deep Dive](https://kodekloud.com/courses/kubernetes-networking) (it includes Traefik as an ingress), [Terraform Basics](https://kodekloud.com/courses/terraform-basics-training-course), [Ansible for the Absolute Beginners](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course).

**Handbook:** [Vault and short-lived CI tokens](33-learn-cicd-iac-sre.md#hashicorp-vault-and-short-lived-ci-tokens), [Kubernetes problems](46-problems-kubernetes.md), [Proxmox problems](50-problems-cloud-iac-proxmox.md#7-proxmox-ve-repositories-host-network-and-cluster), [deployment patterns](35-deployment-patterns.md), [senior architecture](39-learn-senior-architecture.md). Recipes 4.3, 4.4, 4.5, 4.12 and section 5.

**Exit check (one day):** rebuild one VM of the reference platform (for example harbor-1) from Git plus its backups, while another engineer follows your runbook and you only answer questions. Record the wall-clock time; that is your measured RTO for that component.

### 3.5 Senior/Lead (L4)

**Learn:** choosing and retiring tools, DR for the whole platform, SLOs and on-call design, capacity and cost, security reviews, and teaching others.

**Courses and labs:** KodeKloud [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre), [Certified Kubernetes Security Specialist (CKS)](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks), the [SRE learning path](https://kodekloud.com/learning-path/site-reliability-engineer); the Google SRE book chapters on [toil](https://sre.google/sre-book/eliminating-toil/) and [postmortem culture](https://sre.google/sre-book/postmortem-culture/); one public postmortem a week from [Dan Luu's collection](https://github.com/danluu/post-mortems).

**Handbook:** [career ladder](40-career-ladder.md), [on-call in practice](52-devops-day-to-day.md#9-on-call-and-incident-response-in-practice), [choosing for your career](55-paths-onprem-vs-cloud.md#7-choosing-for-your-career), section 5 of this module.

**Exit check (a game day, then a memo):** declare dokploy-1 lost, restore service from PBS or rebuild it from restic and Git, and measure RTO and RPO against what you promised. Then write one page per tool on the diagram: why it is there, who owns it, and its exit plan. Retire at least one tool that no longer earns its place.

### 3.6 A 12-month adoption calendar

One tool a month, each one through the loop in section 0. The "proved by" column is the evidence that the month is done.

| Month | Add | Proved by |
|---|---|---|
| 1 | Uptime Kuma (off site) and node_exporter on every VM | a test outage is noticed by Kuma within two minutes |
| 2 | Dokploy and its Traefik for the first app | the app survives a redeploy and a host reboot ([45 11.2](45-dokploy-and-self-hosted-paas.md#112-everything-down-after-a-reboot)) |
| 3 | GitLab runner and a build-and-deploy pipeline (4.2) | a commit reaches production with no manual step |
| 4 | Prometheus, Alertmanager and Grafana (4.9) | the Watchdog heartbeat and one real alert both arrive (4.10) |
| 5 | restic and S3-compatible storage (4.11) | a volume restored on another VM, timed |
| 6 | Harbor with the private CA and a Docker Hub proxy cache (4.1) | no runner pulls from Docker Hub directly any more |
| 7 | Loki and Alloy (4.7) | a 5xx spike traced to one router in under five minutes |
| 8 | Wazuh with agents everywhere (4.8) | a FIM alert for a Traefik config change, an SSH brute-force alert |
| 9 | CrowdSec with the Traefik bouncer (4.6) | a manual decision blocks a test client; real client IPs in every log |
| 10 | Authentik for SSO and forward auth (4.5) | internal tools need one login; break-glass accounts tested |
| 11 | OpenBao for CI secrets (4.3) | no long-lived registry password left in GitLab variables |
| 12 | k3s with Argo CD (4.4) and a full DR drill with PBS | one app deployed by GitOps; the drill report with measured RTO |

---

## 4. Integration recipes

Each recipe connects two or more tools of the reference platform. They assume the hosts and addresses from 1.2, Dokploy's paths (`/etc/dokploy/traefik/traefik.yml` for Traefik's static configuration, `/etc/dokploy/traefik/dynamic/` for dynamic files and the access log), and a private CA whose certificate is installed on every host as `/usr/local/share/ca-certificates/corp-ca.crt`. Static Traefik changes need `docker restart dokploy-traefik`, which drops connections for a second, so pick a quiet minute; dynamic files apply live.

### 4.1 Harbor proxy cache for Docker Hub

**Why:** Docker Hub allows 100 anonymous pulls per 6 hours per IPv4 address (or IPv6 /64) and 200 for an authenticated personal account, according to its documentation in October 2026. Every runner, Dokploy node and k3s node behind your NAT shares that budget, and docker-in-docker jobs start with an empty cache every time. A Harbor proxy cache turns a hundred identical pulls into one upstream pull and keeps builds working when the internet link is slow.

**Steps:**

In Harbor, create the upstream and the cache project: **Administration → Registries → New Endpoint**, provider Docker Hub, with a Docker Hub user and a read-only access token, then **Test Connection**. Then **Projects → New Project** named `dockerhub-proxy` with **Proxy Cache** switched on and pointing at that endpoint. Make the project private and give consumers a pull-only robot account.

Reference base images through the proxy. Official images need the `library/` segment:

```dockerfile
# Dockerfile
FROM harbor.example.com/dockerhub-proxy/library/node:22-alpine
```

```yaml
# .gitlab-ci.yml (in the shared CI template every project includes)
variables:
  HUB: harbor.example.com/dockerhub-proxy

.docker:
  image: $HUB/library/docker:28
  services:
    - name: $HUB/library/docker:28-dind
      alias: docker            # the job still reaches the daemon at tcp://docker:2376
```

On k3s nodes, mirror Docker Hub transparently, so manifests that say `nginx:1.27` still go through Harbor:

```yaml
# /etc/rancher/k3s/registries.yaml on every k3s node, then: sudo systemctl restart k3s (k3s-agent on agent nodes)
mirrors:
  docker.io:
    endpoint:
      - "https://harbor.example.com"
    rewrite:
      "^(.*)$": "dockerhub-proxy/$1"
configs:
  "harbor.example.com":
    tls:
      ca_file: /usr/local/share/ca-certificates/corp-ca.crt
```

On plain Docker hosts (Dokploy nodes), `registry-mirrors` in daemon.json accepts only a host, not a path, so it cannot point at a Harbor project. Use the explicit `harbor.example.com/dockerhub-proxy/...` references there, and put the CA in `/etc/docker/certs.d/harbor.example.com/ca.crt`.

**Verify:**

```bash
docker pull harbor.example.com/dockerhub-proxy/library/alpine:3.20
sudo k3s crictl pull docker.io/library/alpine:3.20          # on a k3s node: goes through the mirror
```

```text
3.20: Pulling from dockerhub-proxy/library/alpine
Status: Downloaded newer image for harbor.example.com/dockerhub-proxy/library/alpine:3.20
Image is up to date for sha256:91ef0af61f39...
```

In the Harbor UI, `dockerhub-proxy/library/alpine` now exists; cached repositories appear only after their first pull.

**What breaks:**

- `manifest unknown` for `dockerhub-proxy/nginx`: the `library/` segment is missing ([44 5.1](44-problems-docker-swarm-registry.md#51-docker-hub-rate-limit-and-mirrors-that-dont-mirror)).
- `x509: certificate signed by unknown authority` on a node that never got the CA ([44 5.3](44-problems-docker-swarm-registry.md#53-x509-unknown-authority-for-a-private-registry), [46 2.4](46-problems-kubernetes.md#24-images-crictl-ctr-and-harbors-private-ca)).
- BuildKit `docker-container` builders ignore daemon.json and certs.d ([44 6.2](44-problems-docker-swarm-registry.md#62-buildx-builder-ignores-daemonjson)).
- Harbor is now tier-0: when it is down, nothing builds and no new pod starts. Monitor it (4.9) and run GC, or the cache fills the disk ([44 9.2](44-problems-docker-swarm-registry.md#92-disk-still-full-after-deleting-tags)).

### 4.2 GitLab CI to Harbor to Dokploy

**Why:** builds on the production host are the top cause of "everything is slow during deploys" in Dokploy threads. Building in CI, scanning, storing every image in Harbor and letting Dokploy only pull and run keeps the host quiet, gives every deploy an immutable image, and turns a rollback into re-pointing a tag.

**Steps:**

In Harbor, create the project `shop`, switch on **Automatically scan images on push**, and add a robot account with push and pull on that project. Note its expiry date in the team calendar; robot accounts expire.

In GitLab (**Settings → CI/CD → Variables**): `HARBOR_USER` with **Expand variable reference** unticked (robot names contain `$`), `HARBOR_PASSWORD`, `DOKPLOY_TOKEN` (masked and protected), `DOKPLOY_URL`, `DOKPLOY_APP_ID`, and `CORP_CA` as a variable of type File. The runner's docker-in-docker daemon must trust the CA as well ([47 7.2](47-cicd-gitlab-jenkins-actions-argocd.md#72-push-to-harbor-fails-with-x509)).

In Dokploy, add Harbor under the registry settings and create the application from the image `harbor.example.com/shop/web:main`. With the registry login, Swarm pins each deploy to the image digest and workers can pull ([45 9.4](45-dokploy-and-self-hosted-paas.md#94-old-version-still-served-after-a-new-image)).

```yaml
# .gitlab-ci.yml - build once, scan, promote to :main, deploy
stages: [build, scan, release, deploy]

variables:
  IMAGE: harbor.example.com/shop/web
  HUB: harbor.example.com/dockerhub-proxy

.docker:
  image: $HUB/library/docker:28                 # pin dind to the Docker Engine major your hosts run
  services:
    - name: $HUB/library/docker:28-dind
      alias: docker
  tags: [docker]
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "/certs/client"
  before_script:
    - echo "$HARBOR_PASSWORD" | docker login -u "$HARBOR_USER" --password-stdin harbor.example.com

build:
  extends: .docker
  stage: build
  script:
    - docker build --pull --build-arg GIT_SHA="$CI_COMMIT_SHORT_SHA" -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"

scan:
  stage: scan
  image:
    name: $HUB/aquasec/trivy:TRIVY_VERSION       # pin the release you tested
    entrypoint: [""]
  tags: [docker]
  variables:
    TRIVY_CACHE_DIR: .trivycache
  cache:
    key: trivy-db
    paths: [.trivycache/]
  script:
    - cat /etc/ssl/certs/ca-certificates.crt "$CORP_CA" > /tmp/ca-bundle.crt
    - export SSL_CERT_FILE=/tmp/ca-bundle.crt TRIVY_USERNAME="$HARBOR_USER" TRIVY_PASSWORD="$HARBOR_PASSWORD"
    - trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed "$IMAGE:$CI_COMMIT_SHORT_SHA"

release:
  extends: .docker
  stage: release
  script:
    - docker pull "$IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$IMAGE:$CI_COMMIT_SHORT_SHA" "$IMAGE:main"
    - docker push "$IMAGE:main"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy:
  stage: deploy
  image: $HUB/curlimages/curl:8.10.1
  tags: [docker]
  resource_group: production                    # two pipelines never deploy at the same time
  environment: {name: production, url: "https://shop.example.com"}
  script:
    - >
      curl --fail-with-body -sS --cacert "$CORP_CA"
      -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$DOKPLOY_APP_ID\"}"
    - sleep 45
    - curl --fail -sS https://shop.example.com/version | grep -q "$CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

The scan job builds a CA bundle instead of pointing `SSL_CERT_FILE` at your CA alone: Trivy uses Go's TLS stack, and a bundle with only the private CA would break the download of its vulnerability database. `--cacert` in the deploy job is needed only if the Dokploy panel uses the private CA. Check the endpoint name against your Dokploy instance's API reference before relying on it.

Rolling back is re-pointing `:main` at the last good build and deploying again:

```bash
docker pull harbor.example.com/shop/web:4f2a9c1
docker tag harbor.example.com/shop/web:4f2a9c1 harbor.example.com/shop/web:main
docker push harbor.example.com/shop/web:main
# then re-run the deploy job of that pipeline, or call the same API
```

**Verify:**

```bash
# docker service ls hides the digest, so read the service spec instead
docker service inspect --format '{{.Spec.Name}} {{.Spec.TaskTemplate.ContainerSpec.Image}}' $(docker service ls -q --filter name=shop)
curl -s https://shop.example.com/version
```

```text
shop-web-x7k2p harbor.example.com/shop/web:main@sha256:9c1e4d0b7a52...
4f2a9c1
```

The `@sha256:` suffix proves Swarm resolved the digest through the registry login, and `/version` (the app prints the `GIT_SHA` build argument) proves the new code answers, not just that the API call succeeded.

**What breaks:**

- The job stays pending: the runner lacks one of the job's tags ([47 5.1](47-cicd-gitlab-jenkins-actions-argocd.md#51-job-stuck-pending-no-runner-matches)).
- `DOKPLOY_TOKEN` is empty on feature branches because it is protected ([47 5.4](47-cicd-gitlab-jenkins-actions-argocd.md#54-protected-variables-arrive-empty)); the robot name loses its `$` part ([47 5.5](47-cicd-gitlab-jenkins-actions-argocd.md#55-masked-values-and-dollar-sign-expansion)).
- Large pushes die with 499 or timeouts when Harbor sits behind Traefik's 60-second readTimeout ([47 7.4](47-cicd-gitlab-jenkins-actions-argocd.md#74-large-pushes-die-behind-the-proxy)).
- The API returns 200 but the old version is served ([47 9.1](47-cicd-gitlab-jenkins-actions-argocd.md#91-dokploy-deploy-succeeds-but-nothing-changes)); two pipelines race and the older wins without `resource_group` ([47 9.4](47-cicd-gitlab-jenkins-actions-argocd.md#94-two-deploys-race-and-the-older-wins)).
- Trivy cannot download its database (rate limits or no outbound access) ([48 10.1](48-wazuh-and-security-tools.md#101-toomanyrequests-downloading-the-db)), or blocks on CVEs nobody can fix yet ([48 10.3](48-wazuh-and-security-tools.md#103-pipeline-blocked-by-unfixable-cves)).
- If you also enable Harbor's "prevent vulnerable images from running", a CVE published tonight can block tomorrow's rollback to an older image. Decide that policy before an incident, not during one.

### 4.3 OpenBao secrets into GitLab CI

**Why:** a registry password stored in GitLab variables lives forever, works from any job that can read it, and nobody knows when it was used. With OpenBao, each job proves who it is with a signed ID token (project, branch, protected or not) and gets a token that expires in minutes and can read only its own path, and every read lands in the audit log. Module 33 shows the concept on a dev server; this is the production shape.

**Steps:**

```hcl
# /etc/openbao/openbao.hcl on bao-1 (the file the package's systemd unit reads; check with systemctl cat openbao)
ui            = true
api_addr      = "https://bao.example.com:8200"
cluster_addr  = "https://bao-1.example.com:8201"
disable_mlock = true                     # recommended with integrated (raft) storage

storage "raft" {
  path    = "/var/lib/openbao/data"
  node_id = "bao-1"
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/etc/openbao/tls/bao-1.crt"
  tls_key_file  = "/etc/openbao/tls/bao-1.key"
}

# Audit devices are declared here: since v2.3.2 "bao audit enable" is refused
# unless unsafe_allow_api_audit_creation = true is set
audit "file" "file" {
  description = "audit log; alert on this disk"
  options {
    file_path = "/var/log/openbao/audit.log"
  }
}
```

Initialise once and unseal. With Shamir keys the server starts **sealed after every restart**, so decide now who holds the shares (or configure auto-unseal). The audit device declared above is enabled when the active node starts or reloads its configuration (SIGHUP); watch its disk:

```bash
export BAO_ADDR=https://bao.example.com:8200 BAO_CACERT=/usr/local/share/ca-certificates/corp-ca.crt
bao operator init -key-shares=5 -key-threshold=3     # five shares for five people, kept offline
bao operator unseal                                  # three times, with three different shares
bao login                                            # the initial root token, only for this setup
bao audit list                                       # expect file/ from the configuration file
```

Create the secret, a read-only policy and a JWT role bound to one project's protected refs:

```bash
bao secrets enable -path=secret kv-v2
bao kv put -mount=secret shop/harbor user='robot$shop+gitlab-ci' password='REPLACE_ME'
bao policy write shop-ci - <<'EOF'
path "secret/data/shop/*" { capabilities = ["read"] }
EOF
bao auth enable jwt
bao write auth/jwt/config \
    oidc_discovery_url="https://gitlab.example.com" \
    oidc_discovery_ca_pem=@/usr/local/share/ca-certificates/corp-ca.crt \
    bound_issuer="https://gitlab.example.com"
bao write auth/jwt/role/shop-ci - <<'EOF'
{
  "role_type": "jwt",
  "policies": ["shop-ci"],
  "token_explicit_max_ttl": 300,
  "user_claim": "user_login",
  "bound_audiences": ["https://bao.example.com"],
  "bound_claims": {"project_path": "shop/web", "ref_protected": "true"}
}
EOF
bao token revoke -self                               # stop using the root token
```

The job asks GitLab for an ID token, trades it for a short-lived OpenBao token and reads only what it needs:

```yaml
push-with-openbao:
  image: harbor.example.com/platform/deploy-tools:1.4    # your image: bao CLI, docker CLI, the CA
  id_tokens:
    BAO_ID_TOKEN:
      aud: https://bao.example.com
  variables:
    BAO_ADDR: https://bao.example.com:8200
  script:
    - export BAO_TOKEN="$(bao write -field=token auth/jwt/login role=shop-ci jwt="$BAO_ID_TOKEN")"
    - HARBOR_USER="$(bao kv get -mount=secret -field=user shop/harbor)"
    - bao kv get -mount=secret -field=password shop/harbor | docker login -u "$HARBOR_USER" --password-stdin harbor.example.com
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true"
```

`id_tokens` works on every GitLab tier; the `secrets:` keyword that does the login for you needs GitLab Premium.

**Verify:**

```bash
# inside a job on main (add these lines temporarily)
bao token lookup -format=json | jq -c '{ttl: .data.ttl, policies: .data.policies}'
# the same job on an unprotected feature branch
bao write -field=token auth/jwt/login role=shop-ci jwt="$BAO_ID_TOKEN"
```

```text
{"ttl":298,"policies":["default","shop-ci"]}
Error writing data to auth/jwt/login: Error making API request.
Code: 400. Errors:
* error validating claims: claim "ref_protected" does not match any associated bound claim values
```

The second result is the point: the same job on a branch nobody reviewed gets nothing.

**What breaks:**

- After a reboot every pipeline fails because OpenBao is sealed ([48 11.1](48-wazuh-and-security-tools.md#111-sealed-after-every-restart)). It is now tier-0 for deploys: alert on `/v1/sys/health` (it answers 503 when sealed) and keep a documented break-glass path.
- `permission denied` because the policy says `secret/shop/*` instead of `secret/data/shop/*` ([48 11.2](48-wazuh-and-security-tools.md#112-permission-denied-on-kv-v2-secrets)).
- The audit disk fills and OpenBao refuses every request ([48 11.4](48-wazuh-and-security-tools.md#114-audit-log-disk-full-blocks-every-request)); rotate the audit log and alert on its filesystem.
- `x509` when OpenBao fetches GitLab's discovery document: `oidc_discovery_ca_pem` is missing. Clock skew makes valid tokens look expired; keep chrony healthy ([41 8.1](41-problems-linux-systems.md#81-clock-drift-chrony-wont-correct-it)).
- A raft node cannot join when you grow to three nodes ([48 11.3](48-wazuh-and-security-tools.md#113-raft-node-cannot-join-the-cluster)).
- The secret is safe in OpenBao and then printed by `set -x` in the job log ([47 13.4](47-cicd-gitlab-jenkins-actions-argocd.md#134-secrets-leak-into-job-logs)).

<div class="env" data-env="cloud" markdown="1">

**On AWS:** the same ID token is exchanged directly with AWS STS: your GitLab is registered as an IAM OIDC identity provider, the job's `id_tokens` audience matches the audience registered there, an IAM role trusts that provider with conditions on the `project_path` and `ref_protected` claims, and the job reads Secrets Manager or pushes to ECR with the temporary credentials. There is nothing to unseal, but the role's trust policy is now the thing to review. See [identity for machines](55-paths-onprem-vs-cloud.md#3-equivalents-on-prem-and-aws) and [Learn security and DevSecOps](37-learn-security-devsecops.md).

</div>

### 4.4 Argo CD pulling from GitLab

**Why:** for Kubernetes apps, the deploy repository becomes the single description of what runs. Argo CD pulls it and reconciles, so the pipeline needs no cluster credentials, manual `kubectl edit` changes are undone, and "what is deployed?" has one answer in Git.

**Steps:**

Keep manifests in a separate deploy repository, `platform/shop-deploy`, with a Kustomize `base/` (deployment, service, ingress) and one overlay per environment such as `overlays/prod/`, whose `images:` entry is the only thing CI changes.

Give Argo CD a read-only GitLab deploy token (scope `read_repository`) and your CA, and give the k3s nodes a pull-only Harbor robot account:

```bash
argocd cert add-tls gitlab.example.com --from /usr/local/share/ca-certificates/corp-ca.crt
argocd repo add https://gitlab.example.com/platform/shop-deploy.git --username argocd-read --password "$DEPLOY_TOKEN"
```

```yaml
# /etc/rancher/k3s/registries.yaml on every k3s node (merge with the mirror from 4.1)
configs:
  "harbor.example.com":
    auth:
      username: "robot$shop+k3s-pull"
      password: REPLACE_WITH_ROBOT_SECRET
    tls:
      ca_file: /usr/local/share/ca-certificates/corp-ca.crt
```

```yaml
# shop-prod.yaml - kubectl apply -n argocd -f shop-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: shop-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.example.com/platform/shop-deploy.git
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: shop
  syncPolicy:
    automated:
      prune: false          # switch on once you trust the repository (46 12.2)
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

The application's pipeline changes only the image tag in the deploy repository. It needs a project access token with `write_repository` on that repository ([47 9.2](47-cicd-gitlab-jenkins-actions-argocd.md#92-ci-cant-push-back-to-the-repository)):

```yaml
bump-deploy-repo:
  stage: deploy
  image: harbor.example.com/platform/deploy-tools:1.4    # git, kustomize and the CA
  script:
    - git clone "https://ci-bot:${DEPLOY_REPO_TOKEN}@gitlab.example.com/platform/shop-deploy.git"
    - cd shop-deploy/overlays/prod
    - kustomize edit set image harbor.example.com/shop/web=harbor.example.com/shop/web:$CI_COMMIT_SHORT_SHA
    - git -c user.name=ci-bot -c user.email=ci-bot@example.com commit -am "shop-web $CI_COMMIT_SHORT_SHA"
    - git push origin main
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Argo CD polls about every three minutes; a GitLab webhook to Argo CD's `/api/webhook` makes it react at once.

**Verify:**

```bash
argocd app get shop-prod | grep -E 'Sync Status|Health Status'
kubectl -n shop get deploy shop-web -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

```text
Sync Status:        Synced to main (8d41c2e)
Health Status:      Healthy
harbor.example.com/shop/web:4f2a9c1
```

Then test self-heal: `kubectl -n shop scale deploy shop-web --replicas=5` and watch Argo CD put back the replica count from Git within a few minutes.

**What breaks:**

- Argo CD cannot reach GitLab: missing CA, wrong token, or SSH known hosts ([47 12.3](47-cicd-gitlab-jenkins-actions-argocd.md#123-argo-cd-cant-reach-git-helm-or-its-api)).
- OutOfSync immediately after every sync because a controller mutates a field ([47 12.1](47-cicd-gitlab-jenkins-actions-argocd.md#121-outofsync-right-after-a-successful-sync)).
- Progressing forever on-prem: an Ingress or Service waits for a load-balancer address that only MetalLB or ServiceLB can give ([47 12.2](47-cicd-gitlab-jenkins-actions-argocd.md#122-stuck-in-progressing-on-prem), [46 8.1](46-problems-kubernetes.md#81-loadbalancer-external-ip-stays-pending)).
- A hook waits forever, or a failed sync blocks newer commits ([47 12.4](47-cicd-gitlab-jenkins-actions-argocd.md#124-sync-waits-forever-for-a-hook), [47 12.5](47-cicd-gitlab-jenkins-actions-argocd.md#125-a-failed-sync-blocks-newer-commits)).
- Automated prune deletes more than intended after a path or label mistake ([46 12.2](46-problems-kubernetes.md#122-automated-prune-deletes-more-than-intended)).
- `ImagePullBackOff` with 401 when the Harbor robot account expires ([44 9.3](44-problems-docker-swarm-registry.md#93-robot-accounts-robot-names-and-401s)).

### 4.5 Traefik forward-auth to Authentik

**Why:** many internal tools have no login, or a weak one: Prometheus, Alertmanager, the Traefik dashboard, a log viewer, Uptime Kuma's admin UI. Forward auth puts one SSO login with MFA in front of all of them at the proxy. Apps that speak OIDC themselves (Grafana, GitLab, Harbor, Argo CD, Proxmox) should use Authentik as an OIDC provider directly instead; forward auth is for the rest.

**Steps:**

Deploy Authentik as a Dokploy Compose app from the official compose file for the version you pin: server and worker on the same version, plus PostgreSQL. Route `auth.example.com` to the server's port 9000 and finish the initial setup at `https://auth.example.com/if/flow/initial-setup/`.

In Authentik, for each tool: **Applications → Create With Provider**, provider type **Proxy Provider** in mode **Forward auth (single application)**, external host `https://prometheus.example.com`. Then open **Outposts → authentik Embedded Outpost** and add the application to it; a provider that is not on an outpost answers 404.

Define the middleware once as a dynamic file, so every router can reference it as `authentik@file`:

```yaml
# /etc/dokploy/traefik/dynamic/authentik.yml
http:
  middlewares:
    authentik:
      forwardAuth:
        address: http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
```

`authentik-server` must be the server's name on dokploy-network (check with `docker network inspect dokploy-network`). The browser's callback goes to `/outpost.goauthentik.io/` on the protected host itself, so route that path to Authentik on every protected host with labels on the Authentik server service:

```yaml
# labels on the authentik server service (Dokploy Compose)
- traefik.enable=true
- traefik.http.routers.authentik-outpost.rule=HostRegexp(`^.+\.example\.com$`) && PathPrefix(`/outpost.goauthentik.io/`)
- traefik.http.routers.authentik-outpost.priority=100
- traefik.http.routers.authentik-outpost.entrypoints=websecure
- traefik.http.routers.authentik-outpost.tls.certresolver=letsencrypt
- traefik.http.services.authentik.loadbalancer.server.port=9000
```

Protect a tool by adding the middleware to its router. For a Compose service that is one label; for a Dokploy Application, add it to the application's Traefik router configuration and keep a copy in Git, because panel-generated files can be rewritten:

```yaml
- traefik.http.routers.prometheus.middlewares=authentik@file
```

`trustForwardHeader: true` is safe only because the entryPoint trusts forwarded headers from nobody (clients connect to Traefik directly). If a load balancer or CDN sits in front, list exactly its addresses in the entryPoint's `forwardedHeaders.trustedIPs`.

**Verify:**

```bash
curl -sI https://prometheus.example.com/ | grep -iE '^(HTTP|location)'
curl -sI "https://prometheus.example.com/outpost.goauthentik.io/start?rd=https://prometheus.example.com/" | grep -iE '^(HTTP|location)'
```

```text
HTTP/2 302
location: https://prometheus.example.com/outpost.goauthentik.io/start?rd=https%3A%2F%2Fprometheus.example.com%2F
HTTP/2 302
location: https://auth.example.com/application/o/authorize/?client_id=...
```

The first redirect proves the middleware runs; the second proves the outpost path reaches Authentik. Then log in from a private browser window and confirm the tool opens, and that logging out of Authentik locks it again.

**What breaks:**

- The callback lands on a plain 404: the outpost route or the outpost assignment is missing ([48 13.1](48-wazuh-and-security-tools.md#131-forward-auth-returns-404-on-the-outpost-path)).
- Login loops or lands on Authentik's own page: cookie domain, external host or redirect settings ([48 13.2](48-wazuh-and-security-tools.md#132-login-loops-or-lands-on-authentik)).
- 504 or 404 storms because Traefik cannot reach the server on the shared network ([43 8.2](43-traefik-and-reverse-proxies.md#82-forward-auth-loops-404s-and-504s)); "no workers connected" after upgrading only the server ([48 13.3](48-wazuh-and-security-tools.md#133-no-workers-connected-after-an-upgrade)).
- Scripts, webhooks and API clients receive an HTML redirect: give `/api` its own router with token auth or an IP allow-list instead of SSO.
- Authentik down means every protected tool is down: keep break-glass local accounts and do not put the monitoring you need for fixing Authentik behind Authentik alone.
- With Authelia instead, the endpoint is `/api/authz/forward-auth` on port 9091, and old guides still show `/api/verify` ([Authelia Traefik guide](https://www.authelia.com/integration/proxies/traefik/)).

### 4.6 CrowdSec bouncer in Traefik

**Why:** public web apps attract scanners and credential stuffing all day. CrowdSec reads Traefik's access log, detects behaviour (many 404s for admin paths, login bursts, known CVE probes), shares and receives a community blocklist, and the Traefik plugin enforces the decisions before requests reach any app. Fail2ban's iptables bans miss traffic that Docker forwards ([48 9.1](48-wazuh-and-security-tools.md#91-bans-do-not-stop-docker-traffic)).

**Steps:**

Make sure Traefik writes a JSON access log (static configuration, as in 4.7). Then run CrowdSec as a Dokploy Compose app on dokploy-network. Mount the log **directory**, not the single file: a single-file bind mount keeps pointing at the old inode after log rotation.

```yaml
# crowdsec/docker-compose.yml (Dokploy Compose app)
services:
  crowdsec:
    image: crowdsecurity/crowdsec:CROWDSEC_VERSION       # pin
    environment:
      COLLECTIONS: "crowdsecurity/traefik crowdsecurity/http-cve"
    volumes:
      - ../files/acquis-traefik.yaml:/etc/crowdsec/acquis.d/traefik.yaml:ro
      - /etc/dokploy/traefik/dynamic:/var/log/traefik:ro
      - crowdsec-data:/var/lib/crowdsec/data
      - crowdsec-config:/etc/crowdsec
    networks: [dokploy-network]
    restart: unless-stopped

volumes: {crowdsec-data: {}, crowdsec-config: {}}
networks: {dokploy-network: {external: true}}
```

```yaml
# ../files/acquis-traefik.yaml (a Dokploy file mount, so redeploys keep it)
filenames:
  - /var/log/traefik/access.log
labels:
  type: traefik
```

Create the bouncer key. It is printed once; store it in OpenBao or as a Dokploy secret, never in Git:

```bash
docker exec CROWDSEC cscli bouncers add traefik-bouncer
```

Declare the plugin in Traefik's static configuration and attach the middleware to the whole websecure entryPoint, so every router gets it:

```yaml
# /etc/dokploy/traefik/traefik.yml (static) - add to the existing keys, then restart dokploy-traefik
experimental:
  plugins:
    bouncer:
      moduleName: github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
      version: PLUGIN_VERSION                # pin the release shown in the plugin catalog
entryPoints:
  websecure:
    # keep the existing address and tls settings of this entryPoint
    http:
      middlewares:
        - crowdsec@file
```

```yaml
# /etc/dokploy/traefik/dynamic/crowdsec.yml (dynamic)
http:
  middlewares:
    crowdsec:
      plugin:
        bouncer:
          enabled: true
          crowdsecMode: stream               # decisions refreshed every 60 s, lowest overhead
          crowdsecLapiScheme: http
          crowdsecLapiHost: crowdsec:8080
          crowdsecLapiKey: REPLACE_WITH_BOUNCER_KEY
```

Add `forwardedHeadersTrustedIPs` only if a load balancer or CDN sits in front of Traefik, listing exactly its addresses.

**Verify:**

```bash
docker exec CROWDSEC cscli bouncers list
docker exec CROWDSEC cscli metrics | sed -n '/Acquisition Metrics/,/^$/p'
docker exec CROWDSEC cscli decisions add --ip 192.0.2.50 --duration 5m --reason "bouncer test"
# from the test client 192.0.2.50, within a minute:
curl -s -o /dev/null -w '%{http_code}\n' https://shop.example.com/
docker exec CROWDSEC cscli decisions delete --ip 192.0.2.50
```

```text
 Name              IP Address   Valid  Last API pull          Type
 traefik-bouncer   172.20.0.7   ✔️      2026-10-06T09:14:02Z   crowdsec-bouncer-traefik-plugin
 Source                              Lines read  Lines parsed  Lines unparsed
 file:/var/log/traefik/access.log    18.20k      18.20k        -
403
```

A recent "Last API pull" proves the plugin talks to the LAPI; "Lines parsed" proves the parser understands the log; the 403 proves enforcement. Manual decisions work for private addresses too, but the scenarios never ban them, because private ranges are whitelisted by default, so LAN tests that "attack" the site never trigger a ban.

**What breaks:**

- Decisions exist but nothing is blocked: the middleware is not on the router or entryPoint, or the key is wrong ([48 8.1](48-wazuh-and-security-tools.md#81-decisions-exist-but-nothing-is-blocked), [48 8.4](48-wazuh-and-security-tools.md#84-lapi-unreachable-port-8080-and-keys)).
- Every client has the same IP, so one ban blocks everyone, or nobody: a load balancer, CDN or the Swarm ingress mesh hides client addresses ([48 8.2](48-wazuh-and-security-tools.md#82-every-client-shows-the-same-ip), [43 8.3](43-traefik-and-reverse-proxies.md#83-real-client-ip-lost)).
- Lines read but not parsed: wrong `type` label or a log format the collection does not expect ([48 8.3](48-wazuh-and-security-tools.md#83-logs-read-but-not-parsed)).
- Real users banned: an app that legitimately produces many 404s or 401s needs a whitelist or a scenario tweak ([48 8.5](48-wazuh-and-security-tools.md#85-false-positives-ban-real-users)).
- Traefik downloads plugins at start. Without outbound HTTPS, or with an unpinned version that changed, every router that uses the middleware breaks; on air-gapped hosts use local plugins ([43 1.7](43-traefik-and-reverse-proxies.md#17-middlewares-plugins-and-forward-auth)).

### 4.7 Traefik access logs to Loki and Wazuh

**Why:** one access log answers two different kinds of question. Operations asks "which router returns 5xx since the deploy, and how slow is it?" (Loki, next to the metrics in Grafana). Security asks "who keeps failing to log in to Grafana, and show me 90 days of it" (Wazuh, with rules, alerts and retention). CrowdSec, the third consumer, is recipe 4.6.

**Steps:**

Enable a JSON access log in Traefik's static configuration. Filters are OR-connected: the settings below keep errors, retried requests and slow requests, and drop the healthy bulk. Dokploy's own request graphs read this file too, so decide whether you want everything (no filters) or less volume.

```yaml
# /etc/dokploy/traefik/traefik.yml (static) - then restart dokploy-traefik
accessLog:
  filePath: /etc/dokploy/traefik/dynamic/access.log
  format: json
  bufferingSize: 100
  filters:
    statusCodes: ["400-599"]
    retryAttempts: true
    minDuration: 1s
  fields:
    headers:
      defaultMode: drop        # never log cookies or Authorization headers
```

Rotate it. Traefik never rotates its own log; use the logrotate rule from [43 3.3](43-traefik-and-reverse-proxies.md#33-logs-read-them-ship-them) with this path and a `postrotate` of `docker kill --signal=USR1 dokploy-traefik`, which makes Traefik reopen the file.

Ship it to Loki with the Alloy instance already running on dokploy-1 (module 49 installs it). Mount `/etc/dokploy/traefik/dynamic` read-only at `/var/log/traefik` in the Alloy container and add:

```alloy
local.file_match "traefik" {
  path_targets = [{"__path__" = "/var/log/traefik/access.log", "job" = "traefik", "host" = "dokploy-1"}]
}

loki.source.file "traefik" {
  targets    = local.file_match.traefik.targets
  forward_to = [loki.process.traefik.receiver]
}

loki.process "traefik" {
  stage.json {
    expressions = { router = "RouterName" }
  }
  stage.labels {
    values = { router = "" }     # low cardinality only: never ClientHost or RequestPath
  }
  forward_to = [loki.write.central.receiver]
}

loki.write "central" {
  endpoint {
    url = "http://10.10.30.31:3100/loki/api/v1/push"
  }
}
```

Ship it to Wazuh through the agent (recipe 4.8 adds the `localfile` block), and give the manager rules that turn JSON lines into security alerts:

```xml
<!-- /var/ossec/etc/rules/local_rules.xml on siem-1 -->
<group name="traefik,web,">
  <rule id="100200" level="0">
    <decoded_as>json</decoded_as>
    <field name="DownstreamStatus">\d+</field>
    <field name="entryPointName">\.+</field>
    <description>Traefik access log entry</description>
  </rule>

  <rule id="100201" level="5">
    <if_sid>100200</if_sid>
    <field name="DownstreamStatus">^401$|^403$</field>
    <description>Traefik: denied request to $(RequestHost) from $(ClientHost)</description>
  </rule>

  <rule id="100202" level="10" frequency="20" timeframe="60">
    <if_matched_sid>100201</if_matched_sid>
    <same_field>ClientHost</same_field>
    <description>Traefik: 20 denied requests in 60 s from one client</description>
  </rule>
</group>
```

Restart the manager (`sudo systemctl restart wazuh-manager`) after testing the rules with `wazuh-logtest`.

**Verify:**

In Grafana Explore, against Loki:

```text
sum by (router) (count_over_time({job="traefik", host="dokploy-1"} | json | DownstreamStatus >= 500 [5m]))
```

On siem-1, paste one access-log line into `sudo /var/ossec/bin/wazuh-logtest`:

```text
**Phase 2: Completed decoding.
	name: 'json'
	ClientHost: '198.51.100.23'
	DownstreamStatus: '401'
	RequestHost: 'grafana.example.com'
**Phase 3: Completed filtering (rules).
	id: '100201'
	level: '5'
	description: 'Traefik: denied request to grafana.example.com from 198.51.100.23'
	groups: '['traefik', 'web']'
**Alert to be generated.
```

**What breaks:**

- No file at all: the access log lives in static configuration, which needs a Traefik restart ([43 5.4](43-traefik-and-reverse-proxies.md#54-static-vs-dynamic-configuration-mix-ups)).
- The log grows until the disk is full, because nothing rotates it ([41 1.1](41-problems-linux-systems.md#11-disk-full-find-what-is-eating-the-space), [45 11.1](45-dokploy-and-self-hosted-paas.md#111-disk-full-images-build-cache-logs)).
- Loki answers 429 or "too many streams" after someone labels by client IP or path ([49 9.3](49-observability-stack-problems.md#93-loki-rejects-pushes-429-and-too-old)); Promtail-era configs ship nothing ([49 9.1](49-observability-stack-problems.md#91-promtail-is-end-of-life-alloy-ships-no-logs)).
- Wazuh collects the lines but raises no alerts: no rule matches the decoded fields ([48 7.1](48-wazuh-and-security-tools.md#71-logs-collected-but-no-alerts)), or a noisy rule floods the agent queue ([48 7.2](48-wazuh-and-security-tools.md#72-noisy-rules-and-flooded-agent-queues)).
- Every line shows the same ClientHost: fix real client IPs first ([43 8.3](43-traefik-and-reverse-proxies.md#83-real-client-ip-lost)).
- Access logs contain personal data (IP addresses). Agree retention with whoever owns privacy in your organisation, and apply it in Loki and the Wazuh indexer.

### 4.8 Wazuh agent on Dokploy hosts

**Why:** the Dokploy hosts run the edge and every app. Wazuh on them gives file integrity monitoring of the Traefik configuration, Docker events (a container started privileged, an exec into a container), SSH and sudo activity, package vulnerability detection, and an audit trail that lives on another machine than the one an attacker would clean.

**Steps:**

On the manager, create a group and its shared configuration; every agent in the group receives it:

```bash
sudo /var/ossec/bin/agent_groups -a -g dokploy -q
```

```xml
<!-- /var/ossec/etc/shared/dokploy/agent.conf on siem-1 -->
<agent_config>
  <localfile>
    <log_format>json</log_format>
    <location>/etc/dokploy/traefik/dynamic/access.log</location>
  </localfile>

  <wodle name="docker-listener">
    <disabled>no</disabled>
  </wodle>

  <syscheck>
    <directories realtime="yes" report_changes="yes">/etc/dokploy/traefik</directories>
    <ignore>/etc/dokploy/traefik/dynamic/access.log</ignore>
    <nodiff>/etc/dokploy/traefik/dynamic/acme.json</nodiff>
  </syscheck>
</agent_config>
```

`nodiff` matters: `acme.json` holds the private keys of every certificate, and `report_changes` would otherwise copy its contents into alerts. Watch only `/etc/dokploy/traefik`, not all of `/etc/dokploy`, which also holds code checkouts and logs that change on every deploy.

On dokploy-1 (with the Wazuh apt repository configured), install the agent at exactly the manager's version and hold it, because agents must never be newer than the manager:

```bash
sudo WAZUH_MANAGER='10.10.30.32' WAZUH_AGENT_GROUP='dokploy' WAZUH_AGENT_NAME='dokploy-1' \
  apt-get install -y wazuh-agent=MANAGER_VERSION-1
sudo apt-mark hold wazuh-agent
# The docker-listener wodle needs the Python docker library at the version Wazuh documents (7.1.0 at the
# time of writing): Ubuntu's python3-docker is older and speaks an API version Docker 29 refuses, and
# PEP 668 blocks a system-wide pip install, so use a virtual environment
sudo apt-get install -y python3-venv
sudo python3 -m venv /opt/wazuh-docker-venv
sudo /opt/wazuh-docker-venv/bin/pip install docker==7.1.0 urllib3==1.26.20 requests==2.32.2
# then point the shebang of the listener script under /var/ossec/wodles/docker/ at
# /opt/wazuh-docker-venv/bin/python3, as the Wazuh docker-listener page shows; re-check after agent upgrades
sudo systemctl daemon-reload && sudo systemctl enable --now wazuh-agent
```

On siem-1, open only what agents need, only to the agent subnets:

```bash
sudo ufw allow proto tcp from 10.10.10.0/24 to any port 1514,1515 comment 'wazuh agents: apps VLAN'
```

**Verify:**

```bash
sudo /var/ossec/bin/agent_control -l | grep dokploy        # on siem-1
sudo tail -n 20 /var/ossec/logs/ossec.log | grep -E 'Connected to the server|ERROR'   # on dokploy-1
sudo touch /etc/dokploy/traefik/dynamic/fim-test.yml && sleep 10 && sudo rm /etc/dokploy/traefik/dynamic/fim-test.yml
```

```text
   ID: 004, Name: dokploy-1, IP: any, Active
2026/10/06 09:31:12 wazuh-agentd: INFO: (4102): Connected to the server ([10.10.30.32]:1514/tcp).
```

In the Wazuh dashboard, the file-integrity events for `fim-test.yml` (added, then deleted) appear within seconds because the directory is watched in real time. Removing the test file avoids leaving a stray dynamic configuration file for Traefik to load.

**What breaks:**

- The agent never connects: firewall, wrong manager address, or enrollment on 1515 blocked ([48 5.1](48-wazuh-and-security-tools.md#51-agent-never-connects)); it flaps between active and disconnected ([48 5.2](48-wazuh-and-security-tools.md#52-agents-flap-to-disconnected)).
- A rebuilt host cannot re-enrol with the same name ([48 5.3](48-wazuh-and-security-tools.md#53-duplicate-agent-name-on-re-enrollment)).
- An unattended upgrade makes the agent newer than the manager: that is why it is held ([48 7.9](48-wazuh-and-security-tools.md#79-an-upgrade-breaks-the-stack)).
- Real-time FIM reports nothing on some directories ([48 7.3](48-wazuh-and-security-tools.md#73-fim-real-time-changes-not-reported)); vulnerability detection is empty ([48 7.4](48-wazuh-and-security-tools.md#74-vulnerability-detection-empty-or-wrong)).
- Active response on the edge host bans your own office or monitoring address ([48 7.6](48-wazuh-and-security-tools.md#76-active-response-locks-you-out)); start with alerts only.
- The manager's disk fills with archives ([48 7.5](48-wazuh-and-security-tools.md#75-manager-disk-fills-with-logs-and-archives)).

### 4.9 Prometheus scraping Traefik and Dokploy hosts

**Why:** host metrics (CPU, memory, disk, systemd units), container metrics and Traefik's per-service request rate, errors and latency tell you something is wrong before users do, and show where. On this platform Prometheus runs on mon-1, outside Dokploy, so one detail needs care: Traefik's metrics entryPoint is reachable only on Dokploy's overlay network.

**Steps:**

On every host, run node_exporter (host network, port 9100) and cAdvisor (port 8089) exactly as in [agents on every host](49-observability-stack-problems.md#agents-on-every-host), and allow only mon-1 to scrape them:

```bash
sudo ufw allow proto tcp from 10.10.30.31 to any port 9100,8089 comment 'prometheus on mon-1'
```

Turn on Traefik's metrics on a separate, unpublished entryPoint ([Traefik metrics in Dokploy](49-observability-stack-problems.md#turn-on-traefik-metrics-in-dokploy)):

```yaml
# /etc/dokploy/traefik/traefik.yml (static) - add, keep the rest, then restart dokploy-traefik
entryPoints:
  metrics:
    address: ":8082"
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
    addRoutersLabels: false        # router labels multiply histogram series
```

Attach the Alloy container on dokploy-1 to `dokploy-network` too, let it scrape Traefik there and forward the samples to Prometheus with remote write:

```alloy
prometheus.scrape "traefik" {
  job_name        = "traefik"
  targets         = [{"__address__" = "dokploy-traefik:8082", "host" = "dokploy-1"}]
  scrape_interval = "30s"
  forward_to      = [prometheus.remote_write.central.receiver]
}

prometheus.remote_write "central" {
  endpoint {
    url = "http://10.10.30.31:9090/api/v1/write"
  }
}
```

On mon-1, start Prometheus with `--web.enable-remote-write-receiver`, bind it to the internal address only, and scrape the hosts from file-based targets:

```yaml
# prometheus.yml on mon-1 (excerpt)
scrape_configs:
  - job_name: node
    file_sd_configs:
      - files: ["targets/nodes.yml"]
  - job_name: cadvisor
    file_sd_configs:
      - files: ["targets/cadvisor.yml"]
```

```yaml
# targets/nodes.yml - Prometheus re-reads it by itself
- targets: ["10.10.10.11:9100"]
  labels: {host: dokploy-1, role: dokploy-manager}
- targets: ["10.10.10.12:9100"]
  labels: {host: dokploy-2, role: dokploy-worker}
```

Two rules to start with:

```yaml
# rules/platform.yml
groups:
  - name: platform
    rules:
      - alert: TraefikServiceErrors
        expr: |
          sum by (service) (rate(traefik_service_requests_total{code=~"5.."}[5m]))
            / sum by (service) (rate(traefik_service_requests_total[5m])) > 0.05
        for: 10m
        labels: {severity: page}
        annotations: {summary: "{{ $labels.service }} answers more than 5% errors"}
      - alert: HostDiskFilling
        expr: |
          1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"}
            / node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs"} > 0.85
        for: 15m
        labels: {severity: ticket}
        annotations: {summary: "{{ $labels.host }} {{ $labels.mountpoint }} is over 85% full"}
```

Add `up == 0` for five minutes (TargetDown) and the rest of module 49's [alert rules](49-observability-stack-problems.md#alert-rules), including the Watchdog that recipe 4.10 relies on.

**Verify:**

```bash
# on mon-1 (Prometheus listens on the internal address only, not on localhost)
curl -s http://10.10.30.31:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job, .labels.host, .health] | @tsv'
curl -s 'http://10.10.30.31:9090/api/v1/query?query=sum(rate(traefik_service_requests_total[5m]))' | jq -r '.data.result[0].value[1]'
```

```text
node        dokploy-1   up
node        dokploy-2   up
cadvisor    dokploy-1   up
cadvisor    dokploy-2   down
14.2
```

Traefik does not appear in the targets list, because Alloy scrapes it; the second query returning a rate proves the remote-written series arrive. The `down` line is a real finding: dokploy-2 is missing its UFW rule for 8089.

**What breaks:**

- Targets down with "connection refused" or "context deadline exceeded": UFW, wrong port, or the exporter bound to localhost ([49 5.1](49-observability-stack-problems.md#51-target-down-refused-or-deadline-exceeded)).
- Edits to the configuration are ignored ([49 5.2](49-observability-stack-problems.md#52-prometheus-wont-start-or-ignores-edits)); node_exporter reports the wrong disks or misses systemd units ([49 5.3](49-observability-stack-problems.md#53-node_exporter-wrong-disks-missing-units)).
- cAdvisor is blank after Docker 29 or eats CPU ([49 5.5](49-observability-stack-problems.md#55-cadvisor-blank-after-docker-29-or-eating-cpu)); Dokploy services are not discovered ([49 5.7](49-observability-stack-problems.md#57-dokploy-services-and-traefik-not-discovered)).
- Memory grows until Prometheus is killed, usually after someone enabled router labels or added a high-cardinality label ([49 11.4](49-observability-stack-problems.md#114-memory-grows-until-oom-cardinality)); remote-write samples arrive late or out of order ([49 11.5](49-observability-stack-problems.md#115-remote_write-lag-and-out-of-order-samples)).
- Publishing 8082 on the host leaks your service names and traffic to anyone who finds it; keep it on the Docker network.

### 4.10 Uptime Kuma and Alertmanager notifications

**Why:** two monitoring systems without a plan give double pages for one outage and silence for another. The rule here: **each failure pages once, from the system that sees it best.** Alertmanager owns everything Prometheus measures. Uptime Kuma, off site, owns what only an outsider sees: public reachability, certificate expiry from the internet, the heartbeat of the monitoring stack itself, and backup jobs that never reported.

| Failure | Seen best by | Pages through |
|---|---|---|
| a service returns 5xx, a disk fills, a target is down | Prometheus | Alertmanager |
| the site is unreachable from the internet (ISP, DNS, firewall) | Uptime Kuma off site | Uptime Kuma |
| a public certificate expires soon | Uptime Kuma (and blackbox as a backup) | Uptime Kuma |
| the monitoring stack itself is dead | Uptime Kuma push monitor fed by the Watchdog alert | Uptime Kuma |
| a backup job did not succeed tonight | Uptime Kuma push monitor fed by the job | Uptime Kuma |

**Steps:**

Run Uptime Kuma on kuma-1, outside the site, behind its own TLS proxy that passes WebSockets:

```yaml
# docker-compose.yml on kuma-1
services:
  uptime-kuma:
    image: louislam/uptime-kuma:2          # pin a full 2.x.y tag in production
    volumes:
      - kuma-data:/app/data                # local disk: NFS is not supported
    ports:
      - "127.0.0.1:3001:3001"              # only the local TLS proxy reaches it
    restart: unless-stopped
volumes: {kuma-data: {}}
```

Create the monitors: an **HTTP(s) - Keyword** monitor on `https://shop.example.com/healthz` with retries set to 2 or 3 (one failed check is not an outage) and **Certificate Expiry Notification** on; a **Push** monitor `alertmanager-watchdog` with a heartbeat interval of 120 seconds; a **Push** monitor per backup job with an interval a little longer than the schedule (26 hours for a nightly job). Each push monitor shows its push URL.

Feed the Watchdog to Kuma. Module 49's Alertmanager configuration already routes the always-firing Watchdog alert to a `heartbeat` webhook receiver every minute; put the Kuma push URL in its secret file:

```bash
# on mon-1, in the monitoring stack's secrets directory (module 49)
printf '%s\n' 'https://status.example.com/api/push/PUSH_TOKEN?status=up&msg=watchdog' > files/secrets/heartbeat_url
chmod 600 files/secrets/heartbeat_url
```

Point both systems at the same human channel (one Teams or Telegram channel, one mailbox), and name Kuma's notification "outside view" so the on-call engineer knows which system is talking.

**Verify:**

```bash
curl -fsS -X POST 'https://status.example.com/api/push/PUSH_TOKEN?status=up&msg=manual-test'
amtool alert add alertname=PagingTest severity=page host=dokploy-1 \
  --annotation=summary='routing test, please ignore' --alertmanager.url=http://localhost:9093
```

```text
{"ok":true}
```

The first line proves Kuma accepts the POST that Alertmanager's webhook sends; if your version refuses it, the Watchdog monitor will show down from the first minute. The `amtool` test must arrive exactly once in the paging channel. Finally stop Alertmanager on a lab copy and confirm Kuma raises `alertmanager-watchdog` after about two minutes.

**What breaks:**

- False downs from short timeouts, slow DNS or a struggling SQLite database ([49 7.1](49-observability-stack-problems.md#71-uptime-kuma-false-downs-and-a-slow-database)); the UI breaks behind a proxy that drops WebSocket upgrades ([43 9.5](43-traefik-and-reverse-proxies.md#95-websockets-fail-or-drop-at-60-seconds)).
- Alerts fire but nobody is notified: a receiver typo, SMTP port 25 blocked, or `smtp_require_tls` against a plain server ([49 8.1](49-observability-stack-problems.md#81-alerts-fire-but-nobody-is-notified)).
- Late, repeated or storming notifications from the default timers ([49 8.4](49-observability-stack-problems.md#84-late-repeated-flapping-or-storming-alerts)).
- Kuma running on the same host or site it watches dies with it, and reports nothing.
- Upgrading from 1.x to 2.x migrates the database; back up `/app/data` first and read the [migration notes](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2).

### 4.11 restic backups of Dokploy volumes to S3

**Why:** Dokploy can back up its databases, volumes and panel to S3 ([45 backups](45-dokploy-and-self-hosted-paas.md#backups-you-have-restored)), but a backup that depends on the tool you are trying to recover is a weak second copy. restic gives a host-level, encrypted and deduplicated copy of named volumes, bind-mounted files and `/etc/dokploy` that you can restore with nothing but the restic binary, a password and the bucket.

**Steps:**

On s3-1, create the bucket `restic-dokploy-1` and an access key that can reach only that bucket. On dokploy-1, keep the settings in a root-only environment file:

```bash
# /etc/restic/dokploy-1.env  (owner root, mode 600)
RESTIC_REPOSITORY=s3:https://s3.example.com/restic-dokploy-1
RESTIC_PASSWORD_FILE=/etc/restic/password
RESTIC_CACERT=/usr/local/share/ca-certificates/corp-ca.crt
AWS_ACCESS_KEY_ID=REPLACE_ME
AWS_SECRET_ACCESS_KEY=REPLACE_ME
```

Initialise the repository once with `sudo bash -c 'set -a; . /etc/restic/dokploy-1.env; restic init'`, and store a copy of the password offline: without it the backups cannot be decrypted by anyone ([51 5.3](51-problems-databases-storage-backup.md#53-encrypted-backup-lost-password-or-key)).

The job dumps databases first (copying a live database's files gives a backup that may not start), then backs up files, prunes, samples the data, and reports success only at the very end:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/backup-dokploy.sh
set -euo pipefail
set -a; . /etc/restic/dokploy-1.env; set +a

DB_CONTAINER="$(docker ps -qf name=shop-db)"           # the task of the shop-db service on this node
install -d -m 700 /var/backups/db
docker exec "$DB_CONTAINER" pg_dump -U shop -Fc shop > /var/backups/db/shop.dump

restic backup --tag dokploy-1 \
  /var/lib/docker/volumes/shop-uploads/_data \
  /etc/dokploy \
  /var/backups/db \
  --exclude /etc/dokploy/traefik/dynamic/access.log

restic forget --tag dokploy-1 --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
restic check --read-data-subset=5%

TMP="$(mktemp /var/lib/node_exporter/textfile/backup.prom.XXXX)"
echo "backup_last_success_timestamp_seconds{job=\"restic-dokploy-1\"} $(date +%s)" > "$TMP"
chmod 644 "$TMP" && mv "$TMP" /var/lib/node_exporter/textfile/backup.prom
curl -fsS -m 10 'https://status.example.com/api/push/PUSH_TOKEN?status=up&msg=OK' > /dev/null
```

```ini
# /etc/systemd/system/backup-dokploy.service
[Unit]
Description=restic backup of dokploy-1
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/backup-dokploy.sh
Nice=10
IOSchedulingClass=idle
```

```ini
# /etc/systemd/system/backup-dokploy.timer
[Unit]
Description=Nightly restic backup of dokploy-1

[Timer]
OnCalendar=*-*-* 02:30
RandomizedDelaySec=15m
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it with `sudo systemctl daemon-reload && sudo systemctl enable --now backup-dokploy.timer`. Add an alert on `time() - backup_last_success_timestamp_seconds > 93600` so Prometheus notices too.

**Verify:**

```bash
sudo systemctl start backup-dokploy.service
sudo bash -c 'set -a; . /etc/restic/dokploy-1.env; restic snapshots --tag dokploy-1 --latest 1'
sudo bash -c 'set -a; . /etc/restic/dokploy-1.env; restic restore latest --tag dokploy-1 --target /srv/restore-test --include /var/backups/db'
```

```text
ID        Time                 Host        Tags        Paths
------------------------------------------------------------------------------------------
e90c41f5  2026-10-06 09:52:33  dokploy-1   dokploy-1   /etc/dokploy
                                                       /var/backups/db
                                                       /var/lib/docker/volumes/shop-uploads/_data
------------------------------------------------------------------------------------------
1 snapshots
restoring snapshot e90c41f5 of [/etc/dokploy /var/backups/db /var/lib/docker/volumes/shop-uploads/_data] at 2026-10-06 09:52:33 by root@dokploy-1 to /srv/restore-test
Summary: Restored 3 files/dirs (41.2 MiB) in 0:01
```

Finish the drill: `pg_restore` the dump into a scratch PostgreSQL container, run one application query against it, and write down the time it took. That number is the RTO you can actually promise; the backup interval (nightly here) is the RPO.

**What breaks:**

- "repository is already locked" after a killed run; `restic unlock` only when no other job is running ([51 5.2](51-problems-databases-storage-backup.md#52-backup-repository-is-already-locked)).
- `restic check` reports errors after a disk or network fault ([51 5.6](51-problems-databases-storage-backup.md#56-restic-check-repository-contains-errors)).
- The timer stopped weeks ago and nobody noticed: that is what the push monitor and the timestamp metric are for ([51 5.4](51-problems-databases-storage-backup.md#54-backups-stopped-silently-or-are-empty)).
- S3-compatible quirks: path-style addressing, region, the private CA, clock skew ([51 6.1](51-problems-databases-storage-backup.md#61-s3-targets-fail-style-region-ca-clock)); the storage itself is MinIO Community Edition and unmaintained ([51 6.5](51-problems-databases-storage-backup.md#65-minio-community-edition-is-archived)).
- The key on dokploy-1 can also delete the backups, so ransomware on the host deletes them too. Add an immutable or append-only copy that this host cannot touch ([51 9.3](51-problems-databases-storage-backup.md#93-no-tested-restore-rto-and-rpo-in-the-disaster)).
- `/etc/dokploy` contains acme.json private keys and environment files: the repository password protects them, so treat it like a root password.

### 4.12 WireGuard admin plane

**Why:** the Proxmox UI, the Dokploy panel, the Wazuh dashboard, Harbor, OpenBao and SSH are admin surfaces. Each one on the internet is one more login page for credential stuffing and one more CVE to win a race against. One WireGuard endpoint with a key per person and device replaces all of them, and WireGuard does not answer packets that lack a valid key.

**Steps:**

On OPNsense, create a WireGuard instance on 51820/udp with the tunnel address 10.99.0.1/24 and one peer per person and device. The equivalent on a Linux VM, to show what the GUI builds:

```ini
# /etc/wireguard/wg0.conf on the VPN host
[Interface]
Address    = 10.99.0.1/24
ListenPort = 51820
PrivateKey = SERVER_PRIVATE_KEY

[Peer]
# ops laptop: one peer per person and device, removed when they leave
PublicKey  = OPS_LAPTOP_PUBLIC_KEY
AllowedIPs = 10.99.0.10/32
```

```ini
# the admin's client configuration
[Interface]
Address    = 10.99.0.10/32
PrivateKey = OPS_LAPTOP_PRIVATE_KEY
DNS        = 10.10.0.1

[Peer]
PublicKey           = SERVER_PUBLIC_KEY
Endpoint            = vpn.example.com:51820
AllowedIPs          = 10.10.0.0/16, 10.99.0.0/24
PersistentKeepalive = 25
```

The `DNS` line points at OPNsense's Unbound, which answers `dokploy.example.com` with 10.10.10.11, so admin traffic stays inside the tunnel and keeps its 10.99.0.x source address. Then add firewall rules on the wg0 interface for exactly the ports in 1.10, and on every VM allow SSH only from the VPN and the automation host:

```bash
sudo ufw allow proto tcp from 10.99.0.0/24 to any port 22 comment 'admins via WireGuard'
sudo ufw allow proto tcp from 10.10.20.22 to any port 22 comment 'automation host'
```

Admin web UIs that Traefik serves (the Dokploy panel, Grafana's admin pages) get an allow-list middleware in addition to their own login:

```yaml
# /etc/dokploy/traefik/dynamic/vpn-only.yml - reference it as vpn-only@file on admin routers
http:
  middlewares:
    vpn-only:
      ipAllowList:
        sourceRange: ["10.99.0.0/24", "10.10.0.0/16"]
```

**Verify:**

```bash
sudo wg show wg0 latest-handshakes          # on the VPN host
curl -s -o /dev/null -w '%{http_code}\n' https://dokploy.example.com/      # laptop on the VPN
# from outside (phone hotspot or a cloud VM), never from inside the LAN:
nmap -Pn -p 22,3000,8006,9200 203.0.113.10
```

```text
OPS_LAPTOP_PUBLIC_KEY	1791280321
200
PORT      STATE    SERVICE
22/tcp    filtered ssh
3000/tcp  filtered ppp
8006/tcp  filtered wpl-analytics
9200/tcp  filtered wap-wsp
```

On the VPN the panel answers 200; from the phone hotspot the same URL gets 403 from the allow-list, and every admin port is filtered.

**What breaks:**

- No handshake: UDP 51820 blocked, wrong endpoint, or mismatched keys; WireGuard stays silent by design ([42 8.1](42-problems-network-dns-tls-vpn.md#81-wireguard-no-handshake)).
- Handshake fine but no traffic: forwarding, AllowedIPs or a missing return route ([42 8.2](42-problems-network-dns-tls-vpn.md#82-wireguard-handshake-fine-no-traffic)); large transfers hang on MTU ([42 10.1](42-problems-network-dns-tls-vpn.md#101-small-requests-work-large-ones-hang)).
- Names resolve to the public address and the allow-list says 403 even on the VPN: split DNS ([42 2.3](42-problems-network-dns-tls-vpn.md#23-split-dns-over-a-vpn-breaks-or-leaks), [42 4.1](42-problems-network-dns-tls-vpn.md#41-works-from-outside-not-from-the-office-lan)).
- A UFW change over SSH locks you out: keep the Proxmox console or BMC reachable before you touch SSH rules ([41 5.3](41-problems-linux-systems.md#53-locked-out-recovering-a-server-you-cant-reach), [42 3.2](42-problems-network-dns-tls-vpn.md#32-ufw-locked-you-out-or-a-rule-never-matches)).
- Ports published by Docker ignore UFW; the allow-list at Traefik and binding to internal addresses are the real controls ([42 3.1](42-problems-network-dns-tls-vpn.md#31-docker-publishes-ports-past-ufw)).
- With a mesh instead, Tailscale's 100.64.0.0/10 can collide with existing networks ([42 9.2](42-problems-network-dns-tls-vpn.md#92-subnet-router-exit-node-or-10064-conflicts)).

---

## 5. Running the toolbox safely

### 5.1 Upgrade policy

The practitioners' lesson from 2025–2026 is that defaults change underneath you: Docker 29 broke Traefik's Docker provider overnight, nginx switched on upstream keepalive, Traefik moved to lego v5, and Let's Encrypt stopped sending expiry emails. The policy that survives this:

- **Pin everything** (5.2), and upgrade on purpose, never because a container restarted with `:latest`.
- **Read the release notes and the open issues** of the version you are moving to; the GitHub issue tracker shows version-specific breakage before the docs do.
- **One tool per change window**, on a staging host or a cloned VM first, with a backup taken and a restore tested.
- **Respect the order** where a tool has one, and **never auto-update stateful tools or the edge proxy**. Unattended upgrades are for OS security patches; Docker, Wazuh and other platform packages are held.

| Tool | Trap as of October 2026 | Rule |
|---|---|---|
| Docker Engine 29 | minimum API 1.44 broke Traefik before 3.6.1, older cAdvisor and Portainer | hold docker-ce; upgrade the clients first ([43 7.2](43-traefik-and-reverse-proxies.md#72-docker-29-every-route-vanished), [44 1.3](44-problems-docker-swarm-registry.md#13-docker-29-client-version-is-too-old)) |
| Traefik | v2 is end of life and 3.7 is the only supported line; 3.7.6 moved to lego v5 and a Cloudflare DNS-01 regression was reported | pin 3.7.x and test DNS-01 renewals on staging ([43 3.1](43-traefik-and-reverse-proxies.md#31-upgrades-without-surprises)) |
| Dokploy | the installer pins a Traefik 3.6 image that is out of security support; routing regressions follow some upgrades | snapshot the VM, upgrade, then test every domain ([45 13.1](45-dokploy-and-self-hosted-paas.md#131-panel-stuck-after-an-update)) |
| Wazuh | central components must match; order indexer, server, dashboard, then agents | hold the packages ([48 upgrades](48-wazuh-and-security-tools.md#upgrades-without-drama)) |
| Harbor | upgrades only from the previous two minor versions | step through versions ([44 9.1](44-problems-docker-swarm-registry.md#91-harbor-down-after-a-reboot-or-upgrade)) |
| GitLab Runner | registration tokens disabled by default since 17.0, removal planned for 20.0 | move to `glrt-` authentication tokens ([47 5.2](47-cicd-gitlab-jenkins-actions-argocd.md#52-runner-cant-register-or-authenticate)) |
| Jenkins | Java 21 or 25 required from LTS 2.555.1 | upgrade the JDK image first ([47 10.1](47-cicd-gitlab-jenkins-actions-argocd.md#101-jenkins-wont-install-or-start)) |
| Prometheus | 2 to 3 has breaking changes; only 2.55+ reads a v3 TSDB, which is your rollback path | go through 2.55 ([49 11.2](49-observability-stack-problems.md#112-prometheus-2-to-3-upgrade-breaks-things)) |
| Loki and Promtail | Promtail is end of life since 2 March 2026; new features need schema v13 and tsdb | migrate to Alloy ([49 9.1](49-observability-stack-problems.md#91-promtail-is-end-of-life-alloy-ships-no-logs), [49 9.6](49-observability-stack-problems.md#96-loki-3-upgrade-schema-v13-and-tsdb)) |
| Grafana 12 | AngularJS plugins removed | check panel plugins first ([49 6.7](49-observability-stack-problems.md#67-panel-plugin-not-found-after-grafana-12)) |
| Authentik | server and worker must run the same version | upgrade both together ([48 13.3](48-wazuh-and-security-tools.md#133-no-workers-connected-after-an-upgrade)) |
| Kubernetes | one minor version at a time; ingress-nginx is retired | ([46 13.1](46-problems-kubernetes.md#131-kubeadm-upgrade-skew-package-repos-and-removed-apis), [43 8.5](43-traefik-and-reverse-proxies.md#85-kubernetes-ingress-after-ingress-nginx-retired)) |
| ansible-core 2.19 | templating changes break non-boolean conditionals | pin per fleet ([50 6.4](50-problems-cloud-iac-proxmox.md#64-ansible-core-upgrade-broke-playbooks)) |

### 5.2 Pin versions everywhere

| What | How to pin | How to notice updates |
|---|---|---|
| container images | a full tag, plus the digest for edge and stateful services (`image: traefik:v3.7.X@sha256:...`) | Renovate merge requests, or a monthly review of release pages |
| apt packages (Docker, Wazuh, GitLab, Runner) | `sudo apt-mark hold PACKAGE`; install with `PACKAGE=VERSION` | the vendor's release notes feed |
| Traefik plugins | `version:` in the static configuration | the plugin's releases page |
| Helm charts and Argo CD apps | `targetRevision` and chart `version` | Renovate, `helm search repo --versions` |
| Terraform or OpenTofu providers, Ansible collections | `.terraform.lock.hcl`, `requirements.yml` with versions | Renovate |

Keep one `versions.md` (or the Renovate dashboard) in the platform repository: what runs where, at which version, and when it was last reviewed. If Renovate logs in to Harbor with a robot account, mind the `$` in its name ([Renovate discussion #32194](https://github.com/renovatebot/renovate/discussions/32194)).

### 5.3 Back up each tool's state

| Tool | State lives in | Back up with | Restore test |
|---|---|---|---|
| Dokploy | dokploy-postgres, /etc/dokploy | Dokploy's panel backup to S3, plus restic (4.11) | [restore on a new server](45-dokploy-and-self-hosted-paas.md#104-restoring-dokploy-on-a-new-server) |
| Traefik | acme.json, static and dynamic files | configuration in Git; acme.json in restic | starts on a test VM without ordering new certificates ([43 3.2](43-traefik-and-reverse-proxies.md#32-backups-and-restore)) |
| GitLab | database, repositories, uploads; gitlab-secrets.json and gitlab.rb | `gitlab-backup create`, and the two files copied separately | restore onto the same GitLab version |
| Harbor | /data (blobs and database), harbor.yml, certificates | PBS snapshot with Harbor stopped, or a database dump plus blob storage | pull an image after the restore |
| OpenBao | raft data | `bao operator raft snapshot save`; unseal shares offline | restore into a lab cluster and unseal |
| Grafana, Alertmanager, Prometheus | grafana.db; configuration; TSDB | dashboards and rules as code in Git; Grafana's database file | redeploy from Git; accept losing metric history |
| Loki | chunks and index | usually accept the loss; configuration in Git | — |
| Uptime Kuma | /app/data | stop and copy, or restic | start on another VM |
| Wazuh | /var/ossec/etc (rules, decoders, client.keys), certificates, passwords, indexer data | files in restic, indexer snapshots ([48 backups](48-wazuh-and-security-tools.md#backups-of-wazuh-itself)) | agents reconnect without re-enrolling |
| Authentik, Keycloak | PostgreSQL | `pg_dump` (use `docker compose exec -T`) | log in on a restored copy |
| k3s and Argo CD | etcd; Git holds the manifests | `k3s etcd-snapshot save`, `argocd admin export` | cluster reset from a snapshot ([46 13.3](46-problems-kubernetes.md#133-etcd-backup-and-restore-kubeadm-and-k3s)) |
| Proxmox VMs | PBS datastore | PBS with verify jobs and an off-site sync | a file-level and a full-VM restore each quarter |

### 5.4 Size and capacity

The reference platform in 1.2 adds up to about 42 vCPU and 82 GB of RAM before overcommit. Three Proxmox nodes with 16 cores and 64 GB each run it with room to lose one node (N+1): plan capacity so that the platform still fits when one node is down for maintenance. The things that grow, and need a graph each, are: Prometheus series (memory), Loki and Wazuh daily ingest (disk), Harbor images (disk, until GC), runner concurrency (CPU and disk), and backup repositories (disk on s3-1 and pbs-1). Check them monthly, and size from the graphs rather than from guides.

### 5.5 Exposure rules

**Never public:** the Docker API (2375/2376), the Dokploy panel port 3000, Traefik's dashboard and API (8080) and metrics, Prometheus, Alertmanager, Loki, exporters, the Wazuh indexer (9200), API (55000) and agent ports, OpenBao (8200), the CrowdSec LAPI, databases and Redis, S3 consoles, Proxmox (8006) and PBS (8007), the kubelet and etcd, Swarm ports, Portainer, and Authentik except through Traefik. Public: 80, 443 (tcp and udp) on the edge, and the VPN port.

Docker-published ports skip UFW, so the bind address in the Compose file is the control: `127.0.0.1:PORT` for local tools, an internal address for internal tools, and the `DOCKER-USER` chain for the rest ([44 4.4](44-problems-docker-swarm-registry.md#44-published-ports-bypass-ufw)). Check from both sides:

```bash
# on each host: what listens on every interface?
sudo ss -tulpn | awk 'NR==1 || $5 ~ /^(0\.0\.0\.0|\*|\[::\]):/'
# from an outside vantage point, never from inside the LAN
nmap -Pn -p 22,80,443,2375,3000,5432,6379,8006,8080,8200,9090,9100,9200,55000 203.0.113.10
```

```text
Netid State  Local Address:Port  Process
tcp   LISTEN 0.0.0.0:80          users:(("docker-proxy",pid=1840,fd=7))
tcp   LISTEN 0.0.0.0:443         users:(("docker-proxy",pid=1861,fd=7))
tcp   LISTEN 0.0.0.0:3000        users:(("docker-proxy",pid=2203,fd=7))
PORT     STATE    SERVICE
80/tcp   open     http
443/tcp  open     https
3000/tcp filtered ppp
```

Port 3000 still listens on every interface; the edge firewall filters it today, but one NAT rule change would expose it. Close it in Dokploy once the panel has a domain ([45 13.2](45-dokploy-and-self-hosted-paas.md#132-panel-and-databases-open-past-ufw)). More on closing admin endpoints: [Learn security and DevSecOps](37-learn-security-devsecops.md#closing-admin-endpoints).

<div class="env" data-env="cloud" markdown="1">

**On AWS:** the same list becomes security-group rules. Only the load balancer's security group allows 0.0.0.0/0 on 443; instances accept traffic from the load balancer's security group and nothing else; there is no inbound SSH at all because Session Manager replaces it. AWS Config rules or Security Hub controls flag a security group open to the world, which replaces the outside nmap scan as the routine check. See [55: how things fail](55-paths-onprem-vs-cloud.md#how-things-fail).

</div>

### 5.6 Monitor the toolbox itself

Every tool on the platform gets four checks: is it up, is its disk fine, are its certificates valid, did its backup run. The health endpoints that answer the first question:

| Tool | Health check | Note |
|---|---|---|
| Prometheus, Alertmanager | `/-/healthy`, `/-/ready` | plus the Watchdog heartbeat (4.10) |
| Loki | `/ready` | |
| Grafana | `/api/health` | |
| Harbor | `/api/v2.0/health` | per-component status in the JSON |
| GitLab | `/-/health`, `/-/readiness` | only from IPs in its monitoring allow-list |
| OpenBao | `/v1/sys/health` | 503 when sealed: alert on it |
| Authentik | `/-/health/live/`, `/-/health/ready/` | |
| Keycloak | `/health/ready` on management port 9000 | needs health enabled |
| Argo CD | `/healthz` | |
| Wazuh | indexer `_cluster/health`, `agent_control -l` | yellow is normal on one node |
| Uptime Kuma | watched by mon-1's blackbox exporter | the two watch each other |

### 5.7 Retire tools on purpose

Tools leave as well as arrive, and 2025–2026 forced several exits: MinIO Community Edition was archived, Promtail and Grafana Agent reached end of life, ingress-nginx was retired, kaniko was archived, Traefik v2 reached end of life, and Vault's licence change pushed some teams to OpenBao. Each one followed the same path for the teams that handled it calmly: list everything that depends on the tool; run the replacement next to it; move consumers one at a time with a rollback; switch off the old tool only after a restore test from the new one; then update the diagram in 1.1, the port matrix and the runbooks. The exit plan in the admission checklist (section 0) is what makes this a project instead of an incident.

---

## 6. Self-check

Time yourself, use only this module and the linked entries, and do the practical items on a lab, never on production.

1. **[L0 · 10 min]** Draw the request path for `https://shop.example.com` from 1.3 from memory. Which component generates a plain-text "404 page not found", and which one a 403 that never reaches the app?
2. **[L0 · 5 min]** Which ports of the reference platform may be reachable from the internet, and why is 3000/tcp dangerous even with UFW enabled?
3. **[L1 · 45 min]** Build recipe 4.2 on a lab: a commit reaches Dokploy through Harbor. Then roll back by re-pointing `:main`, and prove with `/version` that the old build answers.
4. **[L1 · 30 min]** Restore one file and one database dump from restic (4.11) onto a different VM, and write down the time it took.
5. **[L2 · 30 min]** Every request in CrowdSec and Wazuh shows the same client IP. Name two causes on this platform and the entry that fixes each.
6. **[L2 · 20 min]** Write a Wazuh rule that alerts on 20 denied requests per minute from one client, and prove it with `wazuh-logtest`.
7. **[L2 · 20 min]** Loki starts answering 429 an hour after a colleague changed the Alloy configuration. What do you look for first?
8. **[L3 · 45 min]** After protecting a new tool with forward auth, the login callback ends in a 404. Find and fix it (4.5).
9. **[L3 · 30 min]** bao-1 rebooted overnight and every deploy job fails. Explain what happened, how you restore service, and what you change so it does not page you again.
10. **[L3 · 30 min]** An Argo CD application stays Progressing forever on k3s. Name the likely cause on-prem and the fix.
11. **[L4 · half a day]** Game day: declare dokploy-1 lost. Restore service once from PBS and once by rebuilding from Git and restic. Compare both times with the RTO you promised.
12. **[L4 · 1 hour]** Write the retirement memo for MinIO Community Edition on this platform: dependents, replacement, migration order, rollback, and the restore test that ends it.

| # | Where the answer is |
|---|---|
| 1 | 1.3 and [43 1.9](43-traefik-and-reverse-proxies.md#19-who-generated-the-error) |
| 2 | 1.11, 5.5 and [45 13.2](45-dokploy-and-self-hosted-paas.md#132-panel-and-databases-open-past-ufw) |
| 3 | 4.2 and [45 9.4](45-dokploy-and-self-hosted-paas.md#94-old-version-still-served-after-a-new-image) |
| 4 | 4.11 and [51 5.1](51-problems-databases-storage-backup.md#51-restore-fails-wrong-tool-roles-objects) |
| 5 | 4.6 and [43 8.3](43-traefik-and-reverse-proxies.md#83-real-client-ip-lost) |
| 6 | 4.7 and [48 7.1](48-wazuh-and-security-tools.md#71-logs-collected-but-no-alerts) |
| 7 | 4.7 and [49 9.3](49-observability-stack-problems.md#93-loki-rejects-pushes-429-and-too-old) |
| 8 | 4.5 and [48 13.1](48-wazuh-and-security-tools.md#131-forward-auth-returns-404-on-the-outpost-path) |
| 9 | 4.3 and [48 11.1](48-wazuh-and-security-tools.md#111-sealed-after-every-restart) |
| 10 | 4.4 and [47 12.2](47-cicd-gitlab-jenkins-actions-argocd.md#122-stuck-in-progressing-on-prem) |
| 11 | 1.9, 5.3 and [51 9.3](51-problems-databases-storage-backup.md#93-no-tested-restore-rto-and-rpo-in-the-disaster) |
| 12 | 2.11, 5.7 and [51 6.5](51-problems-databases-storage-backup.md#65-minio-community-edition-is-archived) |

---

## 7. Where to go next

- **The deep dives behind each layer:** [Traefik](43-traefik-and-reverse-proxies.md), [Dokploy and self-hosted PaaS](45-dokploy-and-self-hosted-paas.md), [CI/CD with GitLab, Jenkins, Actions and Argo CD](47-cicd-gitlab-jenkins-actions-argocd.md), [Wazuh and security tools](48-wazuh-and-security-tools.md), [the observability stack](49-observability-stack-problems.md).
- **The problem libraries:** [Linux](41-problems-linux-systems.md), [network, DNS, TLS and VPN](42-problems-network-dns-tls-vpn.md), [Docker, Swarm and registries](44-problems-docker-swarm-registry.md), [Kubernetes](46-problems-kubernetes.md), [cloud, IaC and Proxmox](50-problems-cloud-iac-proxmox.md), [databases, storage and backups](51-problems-databases-storage-backup.md).
- **How the work feels day to day:** [DevOps day to day](52-devops-day-to-day.md), especially [trying to learn every tool at once](52-devops-day-to-day.md#141-trying-to-learn-every-tool-at-once).
- **Practise and compare:** the [Practice Arena](54-practice-arena.md) for reps on each tool, and [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) for the AWS side of every row in section 2.
- **Plan the years, not the week:** [the roadmap](34-roadmap.md), [the career ladder](40-career-ladder.md), [senior architecture](39-learn-senior-architecture.md).
- **Official documentation roots:** [Traefik](https://doc.traefik.io/traefik/) · [Dokploy](https://docs.dokploy.com/docs/core) · [GitLab](https://docs.gitlab.com/) · [Harbor](https://goharbor.io/docs/) · [Argo CD](https://argo-cd.readthedocs.io/en/stable/) · [k3s](https://docs.k3s.io/) · [Wazuh](https://documentation.wazuh.com/current/) · [CrowdSec](https://docs.crowdsec.net/) · [Trivy](https://trivy.dev/) · [Vault](https://developer.hashicorp.com/vault/docs) · [Authentik](https://docs.goauthentik.io/) · [Keycloak](https://www.keycloak.org/documentation) · [Prometheus](https://prometheus.io/docs/prometheus/latest/storage/) · [Grafana](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/) · [Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/) · [restic](https://restic.readthedocs.io/en/stable/077_troubleshooting.html) · [Proxmox Backup Server](https://pbs.proxmox.com/docs/) · [WireGuard](https://www.wireguard.com/quickstart/).
