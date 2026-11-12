# 48 — Wazuh Deep Dive & Security Tool Problems (Wazuh, CrowdSec, Fail2ban, Trivy, Vault, Keycloak, Authentik)

This module has two halves. The toolbox half teaches **Wazuh** as a defensive monitoring platform: what each component does, how to install it next to your Dokploy, Traefik, GitLab and Harbor stack, and how to run it for years without the indexer filling up. The problem library then works through 40 problems that engineers really hit with Wazuh and with the security tools that usually sit beside it: CrowdSec with the Traefik bouncer, Fail2ban, Trivy, Vault/OpenBao, Keycloak and Authentik.
The problems come from GitHub issues, the Wazuh Google Group, official forums and vendor troubleshooting pages. Stack Overflow, Server Fault and Reddit block AI tools, so they appear as search links you can open yourself. Every command is written for you to run on your own servers, and none of them was run on this machine. The scope is defensive throughout: detect, block, harden, recover.

---

## 0. How to use this module

### Who this module serves

| Stage | Level | Start with | You know it when |
|---|---|---|---|
| Fresher | L0 Foundations | §1, the all-in-one install in §2, entries 5.1 and 6.1 | you installed Wazuh in a VM, enrolled one agent and found your own failed SSH login as an alert |
| Junior | L1 Operator | §2 log collection, 5.x, 7.5, 7.7, 8.1, 8.3, 9.2 | agents stay connected, Traefik, Docker and Apache logs arrive, and SSH brute force gets banned |
| Mid-level | L2 Troubleshooter | §3, 6.x, 7.1–7.4, 7.6, 7.8, 8.x, 9.x, 10.x | you can read indexer health, write and test a rule, tune noise, and fix certificate and parser problems |
| Senior | L3 Platform | §3 upgrades, sizing and backups, 7.9, 11.x, 12.x, 13.x | you run Wazuh on its own VM with retention and upgrade it in order with a rollback, and you put SSO and secrets management in front of the platform |
| Senior/Lead | L4 SRE | §3 "Monitoring Wazuh itself", §4, the Self-check | security monitoring runs as a service, with ingestion alerts, an alert budget, runbooks and game days |

### How each entry is laid out

Every problem entry uses the same order, so you can scan it in the middle of an incident:

- **Seen as / Where / Level / How common**: the exact message or symptom, the context, the level and career stage, and how often the community reports it.
- **Why it happens**: the cause in plain words first, then the precise mechanism.
- **Diagnose**: read-only commands, a realistic sample output, then **What the output tells you**.
- **Fix** and **Why this fix works**: the change, why it works, its trade-offs, and what you should not do.
- **Prevent it**, then **Next step** (handbook, KodeKloud, docs), then **Community threads** (verified links plus search links).

Lab conventions used everywhere below: the Wazuh server is `wazuh01` at 192.0.2.10, agents live in 10.0.10.0/24, the admin VPN is 10.0.99.0/24, outside clients and attackers come from 203.0.113.0/24 or 198.51.100.0/24, and every domain is under example.com. Commands that query the indexer or the API use `-u admin` without a password, so curl prompts for it and the password stays out of your shell history.

### How to practise

1. Build a two-VM lab: `wazuh01` (4 vCPU, 8 GB RAM, 60 GB disk, Ubuntu 24.04) and `dokploy01` (Ubuntu 24.04 with Docker and Dokploy). Snapshot both.
2. Pick an entry and cause its symptom on purpose: block 1514/tcp, fill a disk with `fallocate`, change the server IP, delete a bouncer key. Then fix it using only the entry.
3. Write a five-line note: the symptom, your first wrong guess, the evidence that decided it, the fix, and what you will check first next time.
4. Never practise active response or firewall bans on a production host unless you have console access to it.

> 📚 **Study path:** 1) Note: §1 and §2 of this module, then the security mindset and Linux hardening areas of [Learn Security & DevSecOps](37-learn-security-devsecops.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Locate and Analyze System Log Files ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) and Configure Packet Filtering (Firewall) ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 3) KodeKloud: *EFK Stack: Enterprise-Grade Logging and Monitoring* for the index, shard and replica ideas the Wazuh indexer shares ([course](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring)) · 4) Docs: [Wazuh documentation](https://documentation.wazuh.com/current/) — the verified KodeKloud map lists no Wazuh, CrowdSec, Vault or Keycloak course, so the official docs and your lab do most of the teaching here · 5) Practice: the two-VM lab above, or the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) for the agent side.

---

## 1. Wazuh in 10 minutes

### What Wazuh is and is not

Wazuh is an open-source (GPLv2) security monitoring platform, usually described as SIEM plus XDR. An **agent** on every host collects log lines, file-integrity changes, the package and process inventory, and configuration-assessment results. The **server**, also called the manager, decodes those events and matches them against rules. A match at or above a threshold becomes an **alert**. The **indexer**, a fork of OpenSearch, stores the alerts. The **dashboard**, which is OpenSearch Dashboards with the Wazuh plugin, lets you search and visualise them.

What Wazuh is not:

- **Not a firewall or an inline IPS.** It sees events after they happen. Active response can add a local firewall rule, but fast blocking at the edge is CrowdSec's or Traefik's job.
- **Not a patching tool.** Vulnerability detection tells you which packages have known CVEs. Patching them is still your job.
- **Not an uptime monitor or a backup.** "Is the site up?" belongs to your monitoring stack, and restores belong to your backup tool.

Version note for October 2026: the Wazuh documentation shows 4.14 as the current line (patch 4.14.8 when this module was checked; run `apt-cache policy wazuh-manager` or read the release notes for the latest), and a 5.0 release is being prepared on GitHub. The indexer, server and dashboard must all run the same version, and agents must never be newer than the server (entry 7.9).

### Components and ports

```
 AGENTS: wazuh-agent on every host                      WAZUH SERVER (manager)  wazuh01 192.0.2.10
 dokploy01 · web01 · gitlab-runner01 · harbor01        ┌───────────────────────────────────────────┐
┌─────────────────────────────────┐  1515/tcp enroll   │ wazuh-authd      enrollment, agent keys   │
│ logcollector: files, journald,  │ ─────────────────▶ │ wazuh-remoted    agent channel (encrypted)│
│   Docker json-file logs         │  1514/tcp events   │ wazuh-analysisd  decoders → rules         │
│ syscheckd: file integrity (FIM) │ ─────────────────▶ │   → /var/ossec/logs/alerts/alerts.json    │
│ modulesd: SCA, inventory        │ ◀───────────────── │ wazuh-modulesd   vulnerability detection  │
│ execd: active response          │  config, AR orders │ wazuh-apid       REST API 55000/tcp       │
└─────────────────────────────────┘                    │ Filebeat ─────┐   indexer connector ──┐   │
                                                       └───────────────┼───────────────────────┼───┘
                                                                       │ 9200/tcp (TLS)        │
                                                       ┌───────────────▼───────────────────────▼───┐
                                                       │ WAZUH INDEXER (OpenSearch fork)           │
                                                       │ wazuh-alerts-4.x-YYYY.MM.DD (daily)       │
                                                       │ wazuh-archives-4.x-* (only if enabled)    │
                                                       │ wazuh-states-vulnerabilities-*            │
                                                       │ 9300-9400/tcp between indexer nodes       │
                                                       └───────────────▲───────────────────────────┘
                                                                       │ 9200/tcp
                                                       ┌───────────────┴───────────────────────────┐
 Admin browser (VPN or LAN only) ── 443/tcp ─────────▶ │ WAZUH DASHBOARD (OpenSearch Dashboards    │
                                                       │ + Wazuh plugin) ── calls the API on 55000 │
                                                       └───────────────────────────────────────────┘
```

| Port | Component | Who connects | Who may reach it |
|---|---|---|---|
| 1514/tcp | server, wazuh-remoted | agents, for every event | agent networks only |
| 1515/tcp | server, wazuh-authd | agents, once, to enroll | agent networks only, and protect it with an enrollment password |
| 514/udp or tcp | server, syslog input (optional) | switches, firewalls, appliances | their management subnet only |
| 55000/tcp | server, REST API | dashboard, admins, automation | localhost, the dashboard host and the admin VPN |
| 1516/tcp | server cluster | worker and master nodes | cluster nodes only |
| 9200/tcp | indexer REST API | Filebeat, dashboard, indexer connector | Wazuh nodes only, never the internet |
| 9300–9400/tcp | indexer transport | other indexer nodes | indexer nodes only |
| 443/tcp | dashboard | admins' browsers | admin VPN or office LAN only |

### The event pipeline

1. An agent's logcollector reads a new line, for example a failed SSH login, and sends it to the server over 1514/tcp, encrypted with the agent's key.
2. `wazuh-remoted` receives it and hands it to `wazuh-analysisd`. Pre-decoding splits off the syslog header, a decoder extracts fields such as `srcip` and `user`, and the ruleset assigns a rule ID and a level from 0 to 15.
3. If the level is at or above `log_alert_level` (3 by default), the alert is written to `/var/ossec/logs/alerts/alerts.json`. Everything else is dropped, or kept in the archives if you enabled them.
4. Filebeat on the server ships `alerts.json` to the indexer, which stores it in the daily `wazuh-alerts-4.x-*` index.
5. The dashboard reads alerts from the indexer, and agent status and configuration from the API on 55000.

The one idea to keep: **`alerts.json` on the server is the dividing line.** If an alert is in `alerts.json` but not in the dashboard, the problem is in Filebeat, the indexer or the dashboard (§6). If the alert is not in `alerts.json`, the problem is the agent, the decoder or the rule (§5 and §7). Almost every entry in the problem library is a break in one of these five hops.

### Where Wazuh fits in your stack

- **Give Wazuh its own VM.** It needs about 8 GB of RAM, its dashboard wants port 443 (entry 7.8), and the thing that watches your platform should not share a failure with it.
- **Put agents on everything you run:** the Dokploy hosts (Traefik access logs, Docker events, SSH and sudo logs, file-integrity checks on `/etc/dokploy/traefik` and `/etc/ssh`), the GitLab server and runners, the Harbor host, the legacy Apache host on 81/444, and the Kubernetes nodes.
- **Pair it with fast local blockers.** CrowdSec or Fail2ban block within seconds on the host that sees the attack. Wazuh gives you the central view, correlation across hosts, and the audit trail.
- **Shift left with Trivy**, keep secrets in **Vault or OpenBao**, and put **Keycloak or Authentik** SSO in front of admin UIs. The library below covers each of them.

| Need | Tool | Where it runs |
|---|---|---|
| See what happened on every host, file integrity, compliance checks | Wazuh | agents everywhere, server on its own VM |
| Block abusive IPs at the HTTP edge within seconds | CrowdSec with the Traefik bouncer | Dokploy host, next to Traefik |
| Ban SSH brute force on a single host with no extra services | Fail2ban | each host |
| Find known CVEs in images before they deploy | Trivy (CLI in CI, adapter in Harbor) | GitLab runners, Harbor |
| Store, issue and rotate secrets | Vault or OpenBao | its own VM or small cluster |
| SSO and MFA in front of web apps | Keycloak (full IAM) or Authentik (forward auth friendly) | containers behind Traefik |

---

## 2. Install and first configuration

### Choose a deployment model

| Method | Good for | Watch out for |
|---|---|---|
| Install assistant, all-in-one (`wazuh-install.sh -a`) | labs and fleets up to about 100 agents on one VM | one VM is a single point of failure; size it from the table below |
| Install assistant, distributed (`--generate-config-files`, then `--wazuh-indexer`, `--start-cluster`, `--wazuh-server`, `--wazuh-dashboard` on each node) | separate indexer nodes, bigger fleets | `config.yml` must list every node, because the certificates are built from it |
| Docker single-node or multi-node (the `wazuh-docker` repository) | teams that run everything in containers | `vm.max_map_count` on the host, the certificate generator, published ports that bypass UFW, and a special password-change procedure |
| OVA or cloud image | a 30-minute evaluation | change the documented default credentials on first boot and grow the disk |
| Kubernetes manifests | L3 and later | a stateful indexer on Kubernetes is a project of its own |

The quickstart sizes an all-in-one server for 90 days of searchable alerts like this:

| Agents | CPU | RAM | Storage for 90 days |
|---|---|---|---|
| 1–25 | 4 vCPU | 8 GiB | 50 GB |
| 26–50 | 8 vCPU | 8 GiB | 100 GB |
| 51–100 | 8 vCPU | 8 GiB | 200 GB |

### All-in-one with the install assistant

```bash
# Fresh Ubuntu 24.04 VM: wazuh01, 192.0.2.10, 4 vCPU, 8 GB RAM, 60 GB disk, static IP (entry 6.7 explains why)
curl -sO https://packages.wazuh.com/4.14/wazuh-install.sh
less wazuh-install.sh                    # read what you are about to run as root
sudo bash ./wazuh-install.sh -a          # indexer + server + dashboard + certificates on this host
```

```
INFO: Starting Wazuh installation assistant. Wazuh version: 4.14.8
INFO: --- Configuration files ---
INFO: Generating configuration files.
INFO: --- Wazuh indexer ---
INFO: Wazuh indexer cluster initialized.
INFO: --- Wazuh server ---
INFO: Wazuh manager installation finished.
INFO: --- Wazuh dashboard ---
INFO: Wazuh dashboard web application initialized.
INFO: --- Summary ---
INFO: You can access the web interface https://192.0.2.10:443
    User: admin
    Password: (printed once; store it in your password manager)
INFO: Installation finished.
```

```bash
# Every internal password (admin, kibanaserver, wazuh, wazuh-wui, ...) is in the install archive
sudo tar -O -xvf wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt
# The archive also holds the root CA key: move it off the working directory and lock it down
sudo mv wazuh-install-files.tar /root/ && sudo chmod 600 /root/wazuh-install-files.tar
# Stop apt from upgrading Wazuh by surprise; you will upgrade deliberately and in order (§3)
sudo sed -i "s/^deb /#deb /" /etc/apt/sources.list.d/wazuh.list && sudo apt-get update
# Firewall: agents may reach 1514-1515, admins may reach 443, nothing else from outside
sudo ufw allow from 10.0.10.0/24 to any port 1514,1515 proto tcp comment 'wazuh agents'
sudo ufw allow from 10.0.99.0/24 to any port 443 proto tcp comment 'wazuh dashboard via admin VPN'
sudo systemctl is-active wazuh-indexer wazuh-manager wazuh-dashboard filebeat
```

Open `https://192.0.2.10` from the admin VPN. The browser warns about the certificate because the installer signs everything with its own root CA. That is expected. Import `root-ca.pem` into your admin machines, or put the dashboard behind a proxy with a trusted certificate.

### Docker single-node deployment

```bash
# On a Docker host dedicated to Wazuh (not the Dokploy edge host)
sysctl vm.max_map_count                          # the indexer needs at least 262144
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-wazuh.conf && sudo sysctl --system   # only if it was lower
git clone https://github.com/wazuh/wazuh-docker.git -b v4.14.8     # the latest 4.14 patch tag; 4.14.0 has known remoted crashes (entry 7.9)
cd wazuh-docker/single-node
docker compose -f generate-indexer-certs.yml run --rm generator    # writes config/wazuh_indexer_ssl_certs/
# Change the default passwords now, before the first start (entry 6.2), then:
docker compose up -d && docker compose ps --format 'table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

```
NAME                            IMAGE                          STATUS         PORTS
single-node-wazuh.dashboard-1   wazuh/wazuh-dashboard:4.14.8   Up 2 minutes   0.0.0.0:443->5601/tcp
single-node-wazuh.indexer-1     wazuh/wazuh-indexer:4.14.8     Up 2 minutes   0.0.0.0:9200->9200/tcp
single-node-wazuh.manager-1     wazuh/wazuh-manager:4.14.8     Up 2 minutes   0.0.0.0:514->514/udp, 0.0.0.0:1514-1515->1514-1515/tcp, 0.0.0.0:55000->55000/tcp
```

Read the PORTS column as a security finding. Ports published by Docker skip UFW's INPUT rules, so 9200 and 55000 are now reachable from every network that can reach this host. The dashboard talks to the indexer over the Compose network and does not need a published 9200. In `docker-compose.yml`, change `"9200:9200"` to `"127.0.0.1:9200:9200"` (or delete it) and `"55000:55000"` to `"127.0.0.1:55000:55000"`, then run `docker compose up -d` again. The background is in [Docker bypasses UFW](37-learn-security-devsecops.md#docker-bypasses-ufw).

### Enroll the first agents

```bash
# On each Ubuntu host, for example dokploy01 (10.0.10.21); the server is 192.0.2.10
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import
sudo chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
sudo apt-get update
# Add WAZUH_AGENT_GROUP="dokploy" only once that group exists on the server (next section): enrollment into a missing group is refused
sudo WAZUH_MANAGER="192.0.2.10" WAZUH_AGENT_NAME="dokploy01" apt-get install -y wazuh-agent
sudo systemctl daemon-reload && sudo systemctl enable --now wazuh-agent
sudo apt-mark hold wazuh-agent           # an agent must never be newer than the server (entry 7.9)
```

```bash
# On the server: list agents and their state
sudo /var/ossec/bin/agent_control -l
```

```
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh01 (server), IP: 127.0.0.1, Active/Local
   ID: 001, Name: dokploy01, IP: any, Active
   ID: 002, Name: web01, IP: any, Never connected
```

Agent 002 is the start of entry 5.1. Agent states mean: **Active** (keepalives arriving), **Disconnected** (no keepalive for longer than the server's disconnection time), **Pending** (handshake started but never completed), **Never connected** (a key exists but no event ever arrived).

Anyone who can reach 1515/tcp can enroll an agent unless you require a password. Turn that on before the first real host:

```bash
# Server: require a shared secret for enrollment (set use_password to yes inside the existing auth block of ossec.conf)
sudo grep -n 'use_password' /var/ossec/etc/ossec.conf
echo 'ENROLLMENT_PASSWORD' | sudo tee /var/ossec/etc/authd.pass >/dev/null
sudo chown root:wazuh /var/ossec/etc/authd.pass && sudo chmod 640 /var/ossec/etc/authd.pass
sudo systemctl restart wazuh-manager
# Agents then install with WAZUH_REGISTRATION_PASSWORD='ENROLLMENT_PASSWORD' added to the apt-get line
```

### Agent groups and shared configuration

Groups let the server push one `agent.conf` to many agents, so you edit log collection for every Dokploy host in one place.

```bash
# Server: create a group, put agent 001 in it, edit the shared config, validate it
sudo /var/ossec/bin/agent_groups -a -g dokploy -q
sudo /var/ossec/bin/agent_groups -a -i 001 -g dokploy -q
sudoedit /var/ossec/etc/shared/dokploy/agent.conf
sudo /var/ossec/bin/verify-agent-conf -f /var/ossec/etc/shared/dokploy/agent.conf
```

```xml
<agent_config>
  <!-- Traefik access log in JSON (path = accessLog.filePath in your traefik.yml) -->
  <localfile>
    <log_format>json</log_format>
    <location>/etc/dokploy/traefik/dynamic/access.log</location>
  </localfile>
  <!-- stdout/stderr of every container, as written by the json-file logging driver -->
  <localfile>
    <log_format>json</log_format>
    <location>/var/lib/docker/containers/*/*-json.log</location>
  </localfile>
  <!-- Docker events: container start/stop/exec, image pulls -->
  <wodle name="docker-listener">
    <disabled>no</disabled>
  </wodle>
  <!-- File integrity on files that change routing and access, not on data or logs -->
  <syscheck>
    <directories realtime="yes">/etc/dokploy/traefik</directories>
    <directories realtime="yes">/etc/ssh,/etc/sudoers.d</directories>
    <ignore type="sregex">.log$</ignore>
  </syscheck>
</agent_config>
```

Agents poll for the merged group file and restart their modules when it changes. If `verify-agent-conf` complains, fix the XML before agents pick it up: a broken `agent.conf` can leave every agent in the group on stale settings. Do not set `report_changes` on files that hold secrets, such as middleware files with basic-auth hashes, because the diff travels inside the alert.

### Collect Traefik, Docker, Apache and journald logs

| Source | Where the lines are | `log_format` | Notes |
|---|---|---|---|
| Traefik on Dokploy | `accessLog.filePath` in `/etc/dokploy/traefik/traefik.yml` | `json` | JSON gives Wazuh named fields such as `ClientHost` and `DownstreamStatus` |
| Containers | `/var/lib/docker/containers/*/*-json.log` | `json` | only with the json-file logging driver; each line wraps the app line as `log`, `stream`, `time` |
| Docker events | `docker-listener` wodle | none | needs the Python Docker module on the agent; on Ubuntu 24.04 install `python3-docker` with apt, because a system-wide `pip install` is blocked by PEP 668 |
| Apache on 81/444 | `/var/log/apache2/access.log` and `error.log` | `apache` | the built-in web rules fire on scans and error bursts |
| SSH and sudo on journald-only hosts | the systemd journal | `journald` | filter on the unit to keep the volume down |
| Switches, firewalls, appliances | syslog sent to the server on 514 | `remote` block on the server | restrict `allowed-ips` to their subnet |

```yaml
# /etc/dokploy/traefik/traefik.yml (static config: restart the dokploy-traefik container after editing)
accessLog:
  filePath: /etc/dokploy/traefik/dynamic/access.log
  format: json
  filters:
    statusCodes:
      - "400-599"        # keep only errors and denials; drop this filter if you also want successful logins
```

```xml
<!-- Apache (agent ossec.conf or a group agent.conf) -->
<localfile>
  <log_format>apache</log_format>
  <location>/var/log/apache2/access.log</location>
</localfile>
<localfile>
  <log_format>apache</log_format>
  <location>/var/log/apache2/error.log</location>
</localfile>
<!-- SSH from the journal on hosts without /var/log/auth.log -->
<localfile>
  <location>journald</location>
  <log_format>journald</log_format>
  <filter field="_SYSTEMD_UNIT">^ssh.service$</filter>
</localfile>
<!-- Server ossec.conf: accept syslog from the network-device subnet only -->
<remote>
  <connection>syslog</connection>
  <port>514</port>
  <protocol>udp</protocol>
  <allowed-ips>10.0.20.0/24</allowed-ips>
</remote>
```

Traefik never rotates its own access log. Add a logrotate rule whose `postrotate` runs `docker kill --signal=USR1 dokploy-traefik`, which makes Traefik reopen the file. Without it, the log grows until the disk fills (see [Docker: disk, storage and permissions](26-playbook-containers-k8s.md#5-docker-disk-storage-and-permissions)).

### FIM, SCA and vulnerability detection

- **File integrity monitoring (syscheck)** scans `/etc`, `/usr/bin`, `/usr/sbin`, `/bin`, `/sbin` and `/boot` every 12 hours by default. `realtime="yes"` uses inotify for instant alerts on small directories, and `whodata="yes"` uses the Linux audit system to record who made the change (entry 7.3).
- **Security configuration assessment (SCA)** runs a CIS-based policy for the agent's OS on a schedule and shows pass/fail per check under Configuration Assessment. Aim for a documented baseline with written exceptions, not 100%.
- **Vulnerability detection** (4.8 and later) matches each agent's package inventory against Wazuh's threat-intelligence feed and writes the results into `wazuh-states-vulnerabilities-*` through the indexer connector. It needs HTTPS egress from the server (or the documented offline update) and indexer credentials stored with `wazuh-keystore` (entry 7.4).

```xml
<!-- Server ossec.conf (the installer writes these blocks; check them after any change) -->
<vulnerability-detection>
  <enabled>yes</enabled>
  <index-status>yes</index-status>
  <feed-update-interval>60m</feed-update-interval>
</vulnerability-detection>
<indexer>
  <enabled>yes</enabled>
  <hosts>
    <host>https://127.0.0.1:9200</host>
  </hosts>
  <ssl>
    <certificate_authorities>
      <ca>/etc/filebeat/certs/root-ca.pem</ca>
    </certificate_authorities>
    <certificate>/etc/filebeat/certs/filebeat.pem</certificate>
    <key>/etc/filebeat/certs/filebeat-key.pem</key>
  </ssl>
</indexer>
```

```bash
# Credentials the indexer connector uses (repeat after every admin password change)
sudo /var/ossec/bin/wazuh-keystore -f indexer -k username -v admin
sudo /var/ossec/bin/wazuh-keystore -f indexer -k password -v 'ADMIN_PASSWORD'    # prefix the line with a space to keep it out of history
```

### Your first custom rule

Custom rules go in `/var/ossec/etc/rules/local_rules.xml` and custom decoders in `/var/ossec/etc/decoders/local_decoder.xml`. Upgrades never overwrite these two files. Use rule IDs from 100000 to 120000. This example turns Traefik's JSON access log into an alert when one client collects ten authentication failures in a minute:

```xml
<group name="local,traefik,web,">
  <!-- Base rule: any Traefik JSON access-log line; level 0 = classify, do not alert -->
  <rule id="100200" level="0">
    <decoded_as>json</decoded_as>
    <field name="RequestHost">\.+</field>
    <field name="DownstreamStatus">\d+</field>
    <description>Traefik access log</description>
  </rule>
  <rule id="100201" level="5">
    <if_sid>100200</if_sid>
    <field name="DownstreamStatus">^401$</field>
    <description>Traefik: 401 for $(RequestHost)$(RequestPath) from $(ClientHost)</description>
  </rule>
  <rule id="100202" level="10" frequency="10" timeframe="60">
    <if_matched_sid>100201</if_matched_sid>
    <same_field>ClientHost</same_field>
    <description>Traefik: 10 or more authentication failures in 60 s from $(ClientHost)</description>
    <mitre>
      <id>T1110</id>
    </mitre>
  </rule>
</group>
```

```bash
# Test without restarting anything: paste one real log line at the prompt
sudo /var/ossec/bin/wazuh-logtest
```

```
{"ClientHost":"203.0.113.50","DownstreamStatus":401,"RequestHost":"admin.example.com","RequestMethod":"POST","RequestPath":"/login","time":"2026-10-03T09:12:44Z"}

**Phase 1: Completed pre-decoding.
	full event: '{"ClientHost":"203.0.113.50","DownstreamStatus":401,...}'

**Phase 2: Completed decoding.
	name: 'json'
	ClientHost: '203.0.113.50'
	DownstreamStatus: '401'
	RequestHost: 'admin.example.com'
	RequestPath: '/login'

**Phase 3: Completed filtering (rules).
	id: '100201'
	level: '5'
	description: 'Traefik: 401 for admin.example.com/login from 203.0.113.50'
	groups: '['local', 'traefik', 'web']'
	firedtimes: '1'
**Alert to be generated.
```

`wazuh-logtest` reads the saved rule files, so you can iterate without a restart. Live alerting picks up the new rules only after `sudo systemctl restart wazuh-manager`. Put `local_rules.xml` and `local_decoder.xml` in Git and deploy them like any other config (entry 7.1).

### Active response, safely

Active response runs a script on the agent or the server when a rule fires. The classic use is `firewall-drop` for SSH brute force (rule 5763). It is also the classic way to lock yourself out, so start with a whitelist, one rule, a timeout and a lab host:

```xml
<!-- Server ossec.conf: add the white_list lines inside the existing global block -->
<global>
  <white_list>10.0.99.0/24</white_list>     <!-- admin VPN -->
  <white_list>198.51.100.23</white_list>    <!-- office NAT address -->
</global>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>                <!-- block on the agent that saw the attack -->
  <rules_id>5763</rules_id>                 <!-- sshd brute force -->
  <timeout>600</timeout>                    <!-- unblock after 10 minutes -->
</active-response>
```

Every add and delete is logged in `/var/ossec/logs/active-responses.log` on the agent. Entry 7.6 covers lockouts and Docker traffic. For HTTP abuse, CrowdSec at the Traefik edge (§8) is the better tool, because it blocks at layer 7 regardless of iptables chain order.

### Alerts to Slack and email

```xml
<!-- Server ossec.conf -->
<integration>
  <name>slack</name>
  <hook_url>https://hooks.slack.com/services/SLACK_WEBHOOK_PATH</hook_url>
  <level>10</level>
  <alert_format>json</alert_format>
</integration>

<global>
  <email_notification>yes</email_notification>
  <smtp_server>localhost</smtp_server>        <!-- a local Postfix relay, see entry 7.7 -->
  <email_from>wazuh@example.com</email_from>
  <email_to>ops@example.com</email_to>
  <email_maxperhour>12</email_maxperhour>
</global>
<alerts>
  <log_alert_level>3</log_alert_level>
  <email_alert_level>12</email_alert_level>
</alerts>
```

Wazuh's mail daemon does not authenticate to SMTP servers, so point it at a local relay that does (entry 7.7). Choose notification levels deliberately: a channel that pings for every level-5 event gets muted within a week.

---

## 3. Day-2 operations

### Weekly health checks

```bash
# 1. Services
sudo systemctl is-active wazuh-indexer wazuh-manager wazuh-dashboard filebeat
# 2. Agents: active, disconnected, never connected (curl prompts for the wazuh-wui password)
TOKEN=$(curl -sk -u wazuh-wui -X POST "https://127.0.0.1:55000/security/user/authenticate?raw=true")
curl -sk -H "Authorization: Bearer $TOKEN" "https://127.0.0.1:55000/agents/summary/status?pretty=true"
# 3. Indexer: health, disk per node, shard count
curl -sk -u admin "https://127.0.0.1:9200/_cluster/health?filter_path=status,number_of_nodes,active_shards,unassigned_shards"
curl -sk -u admin "https://127.0.0.1:9200/_cat/allocation?v"
# 4. Filebeat still shipping alerts to the indexer?
sudo filebeat test output | tail -n 2
# 5. Server errors since the last check
sudo grep -E "ERROR|CRITICAL" /var/ossec/logs/ossec.log | tail -n 20
```

```
active
active
active
active
{
    "data": {
        "connection": {"active": 41, "disconnected": 2, "never_connected": 1, "pending": 0, "total": 44},
        "configuration": {"synced": 43, "not_synced": 1, "total": 44}
    },
    "error": 0
}
{"status":"green","number_of_nodes":1,"active_shards":187,"unassigned_shards":0}
shards disk.indices disk.used disk.avail disk.total disk.percent host      ip        node
   187       38.1gb    46.2gb     51.8gb     98.0gb           47 127.0.0.1 127.0.0.1 node-1
  talk to server... OK
  version: 7.10.2
```

| Check | Healthy | Act when |
|---|---|---|
| Services | all four `active` | anything else: entries 6.1 and 6.6 |
| Agents | `disconnected` and `never_connected` close to 0 | non-zero for more than an hour: entries 5.1 and 5.2 |
| Indexer status | `green` | `yellow` or `red`: entry 6.3 |
| `disk.percent` | below 75 | above 75: entry 6.4 and the retention policy below |
| `active_shards` | far below 1000 per node | above 800: entry 6.5 |
| `filebeat test output` | `talk to server... OK` | an error: entries 6.2 and 6.7 |

Filebeat reports version 7.10.2 for the indexer on purpose. The Wazuh indexer answers with that compatibility version so the bundled Filebeat OSS keeps working, so do not "fix" it.

### Index retention and disk budget

Wazuh creates a new `wazuh-alerts-4.x-YYYY.MM.DD` index every day, and nothing deletes old ones until you add an Index State Management (ISM) policy. Measure first, then budget:

```bash
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/wazuh-alerts-*?v&h=index,docs.count,store.size&s=index:desc" | head -n 4
```

```
index                         docs.count store.size
wazuh-alerts-4.x-2026.10.02       405311      1.2gb
wazuh-alerts-4.x-2026.10.01       412977      1.2gb
wazuh-alerts-4.x-2026.09.30       391204      1.1gb
```

Budget: 1.2 GB per day × 90 days × (1 + replicas) × 1.25 headroom is about 135 GB for a single node. Keep the disk under 75%, so give it a 200 GB volume. Then enforce the 90 days:

```json
{
  "policy": {
    "description": "Delete Wazuh alert and archive indices after 90 days",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [],
        "transitions": [{ "state_name": "delete", "conditions": { "min_index_age": "90d" } }]
      },
      {
        "name": "delete",
        "actions": [{ "delete": {} }],
        "transitions": []
      }
    ],
    "ism_template": [{ "index_patterns": ["wazuh-alerts-*", "wazuh-archives-*"], "priority": 1 }]
  }
}
```

```bash
# Save the JSON above as wazuh-retention.json, create the policy, then attach it to the indices that already exist
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_plugins/_ism/policies/wazuh-retention" -H 'Content-Type: application/json' -d @wazuh-retention.json
curl -sk -u admin -X POST "https://127.0.0.1:9200/_plugins/_ism/add/wazuh-alerts-*" -H 'Content-Type: application/json' -d '{"policy_id":"wazuh-retention"}'
```

`ism_template` only catches indices created after the policy exists, which is why the second call attaches it to the old ones. The server keeps its own compressed copies under `/var/ossec/logs/alerts` and never deletes them either. Entry 7.5 adds a cron job for that.

### Certificates and passwords

| Component | Certificate files | Password copies it keeps |
|---|---|---|
| Indexer | `/etc/wazuh-indexer/certs/` (`indexer.pem`, `indexer-key.pem`, `admin.pem`, `root-ca.pem`) | internal users in the security plugin (`admin`, `kibanaserver`, ...) |
| Server | `/etc/filebeat/certs/` (`filebeat.pem`, `filebeat-key.pem`, `root-ca.pem`) | Filebeat keystore (`username`, `password`), `wazuh-keystore` for the indexer connector |
| Dashboard | `/etc/wazuh-dashboard/certs/` (`dashboard.pem`, `dashboard-key.pem`, `root-ca.pem`) | dashboard keystore (`opensearch.password`), API user in `/usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml` |

```bash
# Expiry of every node certificate, and a 30-day early warning you can cron
for c in /etc/wazuh-indexer/certs/indexer.pem /etc/filebeat/certs/filebeat.pem /etc/wazuh-dashboard/certs/dashboard.pem; do
  printf '%s  ' "$c"; sudo openssl x509 -in "$c" -noout -enddate
done
sudo openssl x509 -in /etc/wazuh-indexer/certs/indexer.pem -noout -checkend $((30*24*3600)) || echo "RENEW SOON"
# Change passwords only with the bundled tool; it updates the copies together on an all-in-one host
sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -h
```

Changing a password in one place and not the others is the root of entry 6.2. Keep the table above in your runbook.

### Upgrades without drama

1. Read the release notes and the open GitHub issues for the target version. In 2025–2026 that meant threads such as the 4.12 → 4.13 indexer breakage and the remoted crashes on 4.13.1/4.14.0 (entry 7.9).
2. Snapshot the VM or take the backups below. Upgrade a lab copy first.
3. Upgrade in this order, all to the same version: **indexer → server (then refresh the Filebeat template) → dashboard → agents**.
4. Keep your config files when dpkg asks, then diff them against the new `*.dpkg-dist` files.
5. Hold the packages again when you are done.

```bash
# Re-enable the repo for this change only
sudo sed -i "s/^#deb /deb /" /etc/apt/sources.list.d/wazuh.list && sudo apt-get update
# Target: the latest patch of the line (4.14.8 when this was written); copy the exact steps from the upgrade guide of that version
# Stop the writers first: Filebeat, the dashboard, and (single-node indexer) the manager, whose indexer connector also writes
sudo systemctl stop filebeat wazuh-dashboard wazuh-manager
# Indexer: back up its security config, let only primaries allocate, flush, upgrade, restore the security config, allow everything again
sudo /usr/share/wazuh-indexer/bin/indexer-security-init.sh --options "-backup /etc/wazuh-indexer/opensearch-security -icl -nhnv"
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{"persistent":{"cluster.routing.allocation.enable":"primaries"}}'
curl -sk -u admin -X POST "https://127.0.0.1:9200/_flush"
sudo cp /etc/wazuh-indexer/jvm.options /root/jvm.options.bak
sudo apt-get install -y wazuh-indexer=4.14.8-1 && sudo systemctl daemon-reload && sudo systemctl restart wazuh-indexer
sudo /usr/share/wazuh-indexer/bin/indexer-security-init.sh     # re-applies the backed-up security config (see the guide for your version)
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{"persistent":{"cluster.routing.allocation.enable":"all"}}'
# Server, then the Filebeat module, alerts template and pipelines that match it, then the dashboard
sudo apt-get install -y wazuh-manager=4.14.8-1 && sudo systemctl daemon-reload && sudo systemctl start wazuh-manager
curl -s https://packages.wazuh.com/4.x/filebeat/wazuh-filebeat-0.5.tar.gz | sudo tar -xvz -C /usr/share/filebeat/module
sudo curl -so /etc/filebeat/wazuh-template.json https://raw.githubusercontent.com/wazuh/wazuh/v4.14.8/extensions/elasticsearch/7.x/wazuh-template.json
sudo chmod go+r /etc/filebeat/wazuh-template.json
sudo systemctl start filebeat
sudo filebeat setup --pipelines
sudo filebeat setup --index-management -E output.logstash.enabled=false
sudo apt-get install -y wazuh-dashboard=4.14.8-1 && sudo systemctl restart wazuh-dashboard
# Freeze again
sudo sed -i "s/^deb /#deb /" /etc/apt/sources.list.d/wazuh.list && sudo apt-get update
```

Upgrade agents last, either with apt on each host or centrally with WPK packages (`/var/ossec/bin/agent_upgrade -a 001`, or the API). Never let an agent pass the server's version.

### Backups of Wazuh itself

```bash
# Configuration, keys, rules, groups, certificates (contains secrets: encrypt it and store it off the host)
sudo tar -czf /backup/wazuh01-config-$(date +%F).tgz \
  /var/ossec/etc /var/ossec/api/configuration \
  /etc/wazuh-indexer/opensearch.yml /etc/wazuh-indexer/jvm.options /etc/wazuh-indexer/certs \
  /etc/filebeat/filebeat.yml /etc/filebeat/certs \
  /etc/wazuh-dashboard/opensearch_dashboards.yml /etc/wazuh-dashboard/certs \
  /usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml /root/wazuh-install-files.tar
# Alert data: indexer snapshots (needs path.repo: ["/mnt/wazuh-snapshots"] in opensearch.yml and a restart)
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_snapshot/nightly" -H 'Content-Type: application/json' -d '{"type":"fs","settings":{"location":"/mnt/wazuh-snapshots"}}'
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_snapshot/nightly/wazuh-$(date +%F)" -H 'Content-Type: application/json' -d '{"indices":"wazuh-alerts-*","include_global_state":false}'
```

`/var/ossec/etc/client.keys` holds every agent's key. Lose it and every agent must re-enroll. A backup you have never restored is a hope, not a backup, so restore one on a scratch VM every quarter.

### Sizing and scaling

- **Heap:** the indexer heap (`-Xms`/`-Xmx` in `/etc/wazuh-indexer/jvm.options`) should be about half of the RAM the indexer can use and never above about 31 GB. The rest goes to the page cache, which search depends on. On an 8 GB all-in-one, the indexer shares RAM with the server and dashboard, so do not go above 4 GB.
- **When to split:** move the indexer to its own nodes when the all-in-one swaps or the heap stays above 75%. Add server worker nodes when `wazuh-remoted` or `wazuh-analysisd` saturate a CPU, and put a TCP load balancer in front of 1514 for the agents.
- **Dropped events:** `events_dropped` in `/var/ossec/var/run/wazuh-analysisd.state` should stay at 0. If it climbs, the server cannot keep up with the event rate.
- **Archives:** `logall_json` stores every event, not only alerts. It can multiply storage several times over. Enable it while you debug a decoder, then disable it.

### Hardening and exposure

- 9200, 9300–9400, 55000 and 1516 are never reachable from user networks or the internet. The dashboard is reachable only from the admin VPN or the office LAN.
- 1514 and 1515 are open only to agent networks. Enrollment requires a password, and agents on untrusted networks can also be verified with certificates.
- Change every default and installer password, and give each person their own dashboard account with a role (read-only for most people) instead of sharing `admin`.
- Patch the OS of the Wazuh VM normally, but keep the Wazuh packages held and upgrade them on purpose (see "Upgrades without drama").
- SSO for the dashboard (SAML or OpenID Connect through the indexer's security plugin, with Keycloak or Authentik) is a good L3 project once the basics are stable.

### Monitoring Wazuh itself

A security monitor that silently stops is worse than none, because everyone assumes it is watching. Alert on these four signals: indexer health is not green, indexer disk is above 75%, more than N agents are disconnected, and **no new alert in the last 15 minutes** (a dead-man's switch for the whole pipeline).

```bash
#!/usr/bin/env bash
# /usr/local/bin/wazuh-ingest-check: prints a metric and exits 1 when nothing was indexed for 15 minutes.
# Uses a dedicated read-only indexer user "monitor"; MONITOR_PASSWORD comes from a root-only env file.
set -euo pipefail
COUNT=$(curl -sk -u "monitor:${MONITOR_PASSWORD}" -H 'Content-Type: application/json' \
  "https://127.0.0.1:9200/wazuh-alerts-*/_count" \
  -d '{"query":{"range":{"timestamp":{"gte":"now-15m"}}}}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["count"])')
echo "wazuh_alerts_last_15m ${COUNT}"
[ "${COUNT}" -gt 0 ]
```

Run it from cron and send the exit code to whatever already pages you: an Uptime Kuma push monitor, a Prometheus textfile collector, or Alertmanager. The alerting principles are in [Alertmanager and alert rules](32-learn-performance-observability.md#12-alertmanager-and-alert-rules).

---

## 4. Learning path

| Stage | Learn | Do in the lab | KodeKloud, handbook and docs | Exit check |
|---|---|---|---|---|
| Fresher · L0 | Linux logs, journald, UFW, TLS basics; what an agent, server, indexer and dashboard do | Install the all-in-one, enroll one agent, cause failed SSH logins, find the alerts | LFCS *Locate and Analyze System Log Files* and *Configure Packet Filtering (Firewall)*; DevOps Pre-Requisite *SSL & TLS Basics* ([note](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)); [Logs & journal](06-logs-journal.md) | Explain the five hops of the event pipeline from memory |
| Junior · L1 | Groups and `agent.conf`, log formats, the Docker logging driver, Fail2ban basics | A `dokploy` group with the Traefik JSON log and Docker events; an sshd jail; CrowdSec with the Traefik bouncer | DCA *Logging Driver* ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)); *Learning Linux Basics Course & Labs* — IPTABLES Introduction ([note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)); [Docker logging](30-learn-docker.md#6-logging) | Onboard a new host (agent, logs, jail) in 30 minutes from your own runbook |
| Mid-level · L2 | Decoders and rules, `wazuh-logtest`, noise tuning, shards and ISM, certificate chains, Trivy in CI | Three custom rules; the retention policy; break and fix the certificates; a cached Trivy job | *EFK Stack: Enterprise-Grade Logging and Monitoring* ([course](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring)); *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)); LFCS *Work With SSL Certificates* ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) | Self-check exercises 1–6 within their time limits |
| Senior · L3 | Distributed design, upgrades with rollback, snapshots, Vault/OpenBao with raft and auto-unseal, SSO with forward auth | Upgrade a lab from N-1 to N and roll back from a snapshot; a three-node Vault/OpenBao; Authentik in front of admin UIs | *Certified Kubernetes Security Specialist (CKS)* — System Hardening, Supply Chain Security, Runtime Security ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)); free *CKS – Challenges* ([course](https://kodekloud.com/courses/cks-challenges)); [Secrets management](33-learn-cicd-iac-sre.md#6-secrets-management) | A written upgrade runbook, executed twice without data loss |
| Senior/Lead · L4 | Detection engineering as a process, alert budgets, ingestion SLOs, incident response | A weekly noise review, the ingestion dead-man's switch, a tabletop incident exercise | *Fundamentals of SRE* — Incident Management, Designing Effective Alerts ([course](https://kodekloud.com/courses/fundamentals-of-sre)); [Career ladder skills matrix](40-career-ladder.md#7-skills-matrix) | A quarterly report covering agent coverage, top rules and time to acknowledge level-12 alerts |

How practitioners say they really learned this:

- They ran the all-in-one in a VM, attacked their own lab host with failed logins and port scans from a second VM, and read the raw alert JSON, not only the dashboard.
- They lived in `wazuh-logtest` until decoders and rules made sense.
- They learned OpenSearch basics (shards, replicas, watermarks, ISM), because most "Wazuh is broken" threads are indexer operations problems.
- They read the Wazuh Google Group and the GitHub issues for their version before every upgrade.
- For CrowdSec and Fail2ban, they learned iptables chain order the hard way, with Docker.

---

## 5. Wazuh agents and enrollment

The problem library starts here. Sections 5–7 cover Wazuh, ordered from the agent to the indexer to the ruleset. Sections 8–13 cover the tools around it.

### 5.1 Agent never connects

> **Seen as:** the agent is listed as **Never connected** or **Pending**, and its log says `WARNING: (4101): Waiting for server reply (not started). Tried: '192.0.2.10'.` · **Where:** a new agent on a Dokploy or web host, with the server on its own VM · **Level:** [L1 · Junior] · **How common:** the most asked Wazuh question; the docs have separate troubleshooting pages for enrollment and for connection

**Why it happens:** enrolling and connecting are two different conversations. Enrollment over 1515/tcp (`wazuh-authd`) gives the agent its key. After that, every event travels over 1514/tcp to `wazuh-remoted`. "Never connected" means a key exists but no event has ever arrived. The usual causes are that 1514 is blocked while 1515 was opened (UFW on the server, a cloud security group, a corporate firewall), or that the agent's `address` points to an old IP or to a name that resolves somewhere else. A third cause is a key mismatch after the agent was reinstalled or deleted on the server, in which case the server logs `(1408): Invalid ID ... for the source ip`.

**Diagnose:**

```bash
# Agent side
sudo tail -n 5 /var/ossec/logs/ossec.log
sudo grep -E '^status|^last_ack' /var/ossec/var/run/wazuh-agentd.state
nc -vz 192.0.2.10 1515; nc -vz 192.0.2.10 1514
# Server side: listening? allowed? key mismatch?
sudo ss -ltnp | grep -E ':151[45]'; sudo ufw status | grep -E '151[45]'
sudo grep -F '(1408)' /var/ossec/logs/ossec.log | tail -n 3
```

```
wazuh-agentd: INFO: Trying to connect to server ([192.0.2.10]:1514/tcp).
wazuh-agentd: ERROR: (1216): Unable to connect to '[192.0.2.10]:1514/tcp': 'Connection timed out'.
status='pending'
Connection to 192.0.2.10 1515 port [tcp/*] succeeded!
nc: connect to 192.0.2.10 port 1514 (tcp) failed: Connection timed out
1515/tcp                   ALLOW       10.0.10.0/24               # wazuh enrollment
```

**What the output tells you:** 1515 answers, 1514 times out, and UFW only lists 1515. The firewall allows enrollment but not events. "Connection refused" instead of a timeout would mean nothing listens, because the server is stopped or remoted uses another port or protocol. A `(1408)` line on the server would mean the agent presents a key the server does not have, so you would re-enroll (entry 5.3).

**Fix:**

```bash
# Server: allow the event port from agent networks only
sudo ufw allow from 10.0.10.0/24 to any port 1514 proto tcp comment 'wazuh agent events'
# Agent: wrong server address? correct it and restart
sudo sed -i 's#<address>.*</address>#<address>192.0.2.10</address>#' /var/ossec/etc/ossec.conf && sudo systemctl restart wazuh-agent
# Key mismatch: delete the stale entry on the server, then the agent enrolls again when restarted without a key
sudo /var/ossec/bin/manage_agents -r 002                                               # server
sudo truncate -s 0 /var/ossec/etc/client.keys && sudo systemctl restart wazuh-agent    # agent
```

**Why this fix works:** an agent needs both ports for its whole life, and a key only works if the server holds the same one. Do not open 1514 and 1515 to 0.0.0.0/0 on a server that the internet can reach. Do not switch the agent to UDP "to see if it helps" either: that changes the protocol on one side only.

**Prevent it:** keep both ports in your firewall-as-code, make the agent install script run `nc -vz` against 1514 and 1515 before it installs anything, and alert when `never_connected` stays above 0 for an hour.

**Next step:** [Listening but unreachable from outside](22-playbook-ports-inventory.md#14-scenario-listening-but-unreachable-from-outside) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure Packet Filtering (Firewall) · [Wazuh docs: enrollment troubleshooting](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html)

**Community threads:** [Wazuh docs: agent connection](https://documentation.wazuh.com/current/user-manual/agent/agent-management/agent-connection.html) · [Google Group: Agent registration issue](https://groups.google.com/g/wazuh/c/KIoGg4Ux2xc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+agent+never+connected) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=never+connected&restrict_sr=1)

### 5.2 Agents flap to Disconnected

> **Seen as:** agents switch between Active and Disconnected; the agent logs `wazuh-agentd: WARNING: Server unavailable. Setting lock.`, and the server logs `(1404): Authentication error. Wrong key or corrupt payload.` · **Where:** fleets built from VM templates, sites behind NAT or stateful firewalls, the days after an upgrade · **Level:** [L2 · Mid] · **How common:** a steady stream of group threads, plus GitHub #33038 (remoted crashing on 4.13.1/4.14.0)

**Why it happens:** four patterns cover most cases.

1. **Cloned VMs.** A golden image already contained `/var/ossec/etc/client.keys`, so several hosts present the same agent ID and key. The server keeps rejecting one of them, and they take turns looking connected.
2. **Idle timeouts.** A NAT device or firewall drops the long-lived TCP session.
3. **Server crashes.** When `wazuh-remoted` restarts, every agent drops at once, so check whether the flapping is fleet-wide.
4. **Suspended VMs and laptops** miss keepalives for longer than the server's disconnection time.

**Diagnose:**

```bash
# Server: one agent or all of them? did a daemon crash?
sudo /var/ossec/bin/agent_control -l | grep -c Disconnected
sudo grep -F '(1404)' /var/ossec/logs/ossec.log | tail -n 2
sudo journalctl -u wazuh-manager --since "-6h" --no-pager | grep -iE 'core dumped|segfault|exited' | tail -n 3
# On each of the two suspect agents (here web07 and web08): same ID and name?
sudo cut -d' ' -f1,2 /var/ossec/etc/client.keys
```

```
17
2026/10/03 10:41:07 wazuh-remoted: WARNING: (1404): Authentication error. Wrong key or corrupt payload. Message received from agent '014' at 'any'.
web07$ 014 web-template
web08$ 014 web-template
```

**What the output tells you:** web07 and web08 both carry ID 014 under the name `web-template`, so they were cloned from an image with a key inside. If the journal had instead shown `wazuh-remoted` exiting at the moment all agents dropped, you would be looking at a server bug: find the issue for your version and upgrade or roll back.

**Fix:**

```bash
# On each clone: drop the inherited key; the agent enrolls again under its own hostname
sudo systemctl stop wazuh-agent
sudo truncate -s 0 /var/ossec/etc/client.keys
sudo systemctl start wazuh-agent
# On the server, once every clone has its own ID: remove the shared entry
sudo /var/ossec/bin/manage_agents -r 014
```

**Why this fix works:** an agent ID plus its key is an identity, and two machines cannot share one. Fresh enrollment gives each host its own. For NAT timeouts, keep the agent keepalive (`notify_time`, 10 seconds by default) far below the firewall's idle timeout, or raise that timeout for 1514/tcp.

**Prevent it:** never bake `client.keys` into a template. Enroll on first boot with cloud-init or Ansible. Alert on the disconnected count, and read the open issues before every upgrade ([Upgrades without drama](48-wazuh-and-security-tools.md#upgrades-without-drama)).

**Next step:** [Ansible](33-learn-cicd-iac-sre.md#4-ansible) for first-boot enrollment · KodeKloud: *Ansible Basics Course* — Playbooks ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · [Wazuh docs: agent connection](https://documentation.wazuh.com/current/user-manual/agent/agent-management/agent-connection.html)

**Community threads:** [GitHub #33038: remoted crashing on 4.13.1/4.14.0](https://github.com/wazuh/wazuh/issues/33038) · [GitHub #17928: many agent disconnections](https://github.com/wazuh/wazuh/issues/17928) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+agent+disconnected) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=agents+disconnected&restrict_sr=1)

### 5.3 Duplicate agent name on re-enrollment

> **Seen as:** the agent logs `ERROR: Duplicate agent name: web01 (from manager)`, and the server logs `Duplicate name 'web01', rejecting enrollment` · **Where:** a host that was rebuilt or reinstalled under the same hostname · **Level:** [L1 · Junior] · **How common:** several group threads plus GitHub #13580 and discussion #26268; one thread reports it across a whole fleet after an upgrade to 4.13.1

**Why it happens:** agent names are unique on the server. The rebuilt host lost its key, so it asks for a new one under its old name, but the old entry is still registered. The `force` options in the server's `auth` block decide when an existing agent may be replaced. By default that only happens once the old agent has been disconnected for longer than `disconnected_time` (1 hour) and was registered more than `after_registration_time` ago. A host you rebuilt 20 minutes ago is therefore refused until the hour has passed.

**Diagnose:**

```bash
sudo /var/ossec/bin/agent_control -l | grep -w web01
sudo grep -i 'duplicate' /var/ossec/logs/ossec.log | tail -n 2
sudo grep -A6 '<force>' /var/ossec/etc/ossec.conf
```

```
   ID: 007, Name: web01, IP: any, Disconnected
2026/10/03 11:02:19 wazuh-authd: WARNING: Duplicate name 'web01', rejecting enrollment. Agent '007' key already exists on the manager.
      <force>
        <enabled>yes</enabled>
        <key_mismatch>yes</key_mismatch>
        <disconnected_time enabled="yes">1h</disconnected_time>
        <after_registration_time>1h</after_registration_time>
```

**What the output tells you:** the old ID 007 is disconnected, but not for an hour yet, so the policy is protecting it. Either wait it out or remove it on purpose.

**Fix:**

```bash
# Server: remove the old registration (scripts can call DELETE /agents?agents_list=007&status=all&older_than=0s on the API)
sudo /var/ossec/bin/manage_agents -r 007
# Agent: restart; it enrolls again and receives a new ID
sudo systemctl restart wazuh-agent
```

**Why this fix works:** removing the stale identity frees the name. The force policy exists to stop a second machine from silently taking over a live agent's identity, so do not set `disconnected_time` to zero in production just to make this message go away.

**Prevent it:** write a decommission and rebuild runbook that deletes the agent first, and run a weekly API job that removes agents disconnected for more than 30 days.

**Next step:** [Ansible](33-learn-cicd-iac-sre.md#4-ansible) · KodeKloud: *Ansible Basics Course* — Handlers, Roles and Collections ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · [Wazuh docs: enrollment troubleshooting](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html)

**Community threads:** [GitHub #13580: Duplicate name, rejecting enrollment](https://github.com/wazuh/wazuh/issues/13580) · [GitHub discussion #26268](https://github.com/wazuh/wazuh/discussions/26268) · [Google Group: Duplicate name, enrollment rejected](https://groups.google.com/g/wazuh/c/Fuuzs1abBTI) · [Google Group: agents duplicated after 4.13.1](https://groups.google.com/g/wazuh/c/DYzAh9h6ZhI) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+%22duplicate+agent+name%22) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=duplicate+agent+name&restrict_sr=1)

---

## 6. Wazuh indexer and dashboard

### 6.1 Dashboard server is not ready yet

> **Seen as:** the browser shows `Wazuh dashboard server is not ready yet`; the dashboard logs `[ConnectionError]: connect ECONNREFUSED 127.0.0.1:9200` or `Another OpenSearch Dashboards instance appears to be migrating the index` · **Where:** after a reboot, an upgrade or an IP change, or on a VM with too little RAM · **Level:** [L1 · Junior] · **How common:** wazuh-docker #771 has 30 comments, and the Google Group has a thread for nearly every release (4.3 OVA, 4.9, 4.10, 4.12)

**Why it happens:** the message comes from the dashboard and only means "I cannot use the indexer yet". The usual real causes are:

- the indexer is down or still starting, very often after being OOM-killed (entry 6.6);
- `opensearch.hosts` still points to an old IP;
- TLS between the dashboard and the indexer fails (entry 6.7);
- the `kibanaserver` password was changed without updating the dashboard keystore (entry 6.2);
- an upgrade was interrupted while the dashboard migrated its saved-objects index, leaving a half-built `.kibana_N`.

**Diagnose:**

```bash
sudo systemctl is-active wazuh-indexer wazuh-dashboard
sudo journalctl -u wazuh-dashboard -n 40 --no-pager | grep -iE '"error"|migrat' | tail -n 2
sudo grep -E '^opensearch.hosts' /etc/wazuh-dashboard/opensearch_dashboards.yml
curl -sk -u admin "https://127.0.0.1:9200/_cluster/health?filter_path=status"
```

```
failed
active
Oct 03 09:14:02 wazuh01 opensearch-dashboards[912]: {"type":"log","@timestamp":"2026-10-03T09:14:02Z","tags":["error","opensearch","data"],"pid":912,"message":"[ConnectionError]: connect ECONNREFUSED 127.0.0.1:9200"}
opensearch.hosts: https://127.0.0.1:9200
curl: (7) Failed to connect to 127.0.0.1 port 9200 after 0 ms: Couldn't connect to server
```

**What the output tells you:** the dashboard is running and correctly configured, but the indexer is `failed`, so go to entry 6.6 to find out why. If the indexer were healthy and the log said `migrating the index`, you would clean up the migration as shown below. If it said `self signed certificate` or `altnames`, entry 6.7 applies.

**Fix:**

```bash
# Indexer down: start it and watch it come up (1-3 minutes is normal)
sudo systemctl restart wazuh-indexer && sudo journalctl -u wazuh-indexer -f
# Indexer address changed: point the dashboard at it
sudo sed -i 's#^opensearch.hosts:.*#opensearch.hosts: https://192.0.2.10:9200#' /etc/wazuh-dashboard/opensearch_dashboards.yml
# Interrupted migration: list the saved-object indices, delete ONLY the half-built one the log names, restart
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/.kibana*?v&h=index,docs.count"
curl -sk -u admin -X DELETE "https://127.0.0.1:9200/.kibana_2"
sudo systemctl restart wazuh-dashboard
```

**Why this fix works:** the dashboard holds no data of its own. As soon as the indexer answers over TLS with valid credentials, the dashboard becomes ready. Deleting the half-built migration target lets the next start redo the migration from the intact previous index. Take a snapshot first (§3), and never delete `.kibana` indices blindly, because your saved searches and visualisations live there.

**Prevent it:** give the VM the RAM from the sizing table, alert on the `wazuh-indexer` service state, and follow the IP-change checklist in entry 6.7.

**Next step:** [Weekly health checks](48-wazuh-and-security-tools.md#weekly-health-checks) · KodeKloud: *EFK Stack: Enterprise-Grade Logging and Monitoring* (Kibana depends on Elasticsearch exactly the way this dashboard depends on the indexer) · [Wazuh docs: dashboard troubleshooting](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/troubleshooting.html)

**Community threads:** [wazuh-docker #771](https://github.com/wazuh/wazuh-docker/issues/771) · [Google Group: not ready yet](https://groups.google.com/g/wazuh/c/CSCIP8NQymY) · [Google Group: after upgrade 4.12](https://groups.google.com/g/wazuh/c/oDjE7uIa6D8) · [Google Group: OVA 4.3.8](https://groups.google.com/g/wazuh/c/DN5SlzUg9zk) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22wazuh+dashboard+server+is+not+ready+yet%22) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=dashboard+not+ready+yet&restrict_sr=1)

### 6.2 API down or credentials rejected

> **Seen as:** `Wazuh API seems to be down` or `No API available to connect` in the dashboard; after a password change, Filebeat logs `Unable to authenticate user [admin] for REST request` · **Where:** after changing passwords (especially in Docker) or after a server crash · **Level:** [L2 · Mid] · **How common:** wazuh-docker #838 ("the documented way to change admin/wazuh-wui passwords do not work", 21 comments) and #712

**Why it happens:** first rule out the trivial case: `wazuh-manager` is stopped, so nothing listens on 55000. Otherwise it is a credential-copy problem. Every component keeps its own copy of a password (see the §3 table): the indexer's internal users, the Filebeat keystore, the dashboard keystore, `wazuh-keystore` for the vulnerability connector, and the API user in `wazuh.yml`. If you change one copy and not the others, whichever component holds the stale copy breaks. In Docker, the environment variables only seed the first start. Changing them later does nothing until the indexer's `internal_users.yml` hash is updated and applied with `securityadmin`.

**Diagnose:**

```bash
sudo systemctl is-active wazuh-manager && sudo ss -ltnp | grep 55000
curl -sk -u wazuh-wui -X POST "https://127.0.0.1:55000/security/user/authenticate?raw=true"; echo
sudo grep -E 'url|port|username' /usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml
sudo filebeat test output 2>&1 | tail -n 1
```

```
active
LISTEN 0 128 0.0.0.0:55000 0.0.0.0:* users:(("python3",pid=1422,fd=33))
{"title": "Unauthorized", "detail": "Invalid credentials"}
      url: https://127.0.0.1
      port: 55000
      username: wazuh-wui
  talk to server... ERROR 401 Unauthorized: {"error":{"root_cause":[{"type":"security_exception","reason":"Unable to authenticate user [admin] for REST request [/]"}]}}
```

**What the output tells you:** the API is up but rejects the password you believe is current, and Filebeat's stored `admin` password is stale as well. Someone changed passwords in one place only.

**Fix:**

```bash
# Set the new admin password with the bundled tool (on an all-in-one it also refreshes the local copies)
sudo /usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh -u admin -p 'NEW_ADMIN_PASSWORD'
# Make sure every copy matches: Filebeat, the vulnerability connector, and (for kibanaserver) the dashboard
echo 'NEW_ADMIN_PASSWORD' | sudo filebeat keystore add password --stdin --force
sudo /var/ossec/bin/wazuh-keystore -f indexer -k password -v 'NEW_ADMIN_PASSWORD'
echo 'NEW_KIBANASERVER_PASSWORD' | sudo /usr/share/wazuh-dashboard/bin/opensearch-dashboards-keystore --allow-root add -f --stdin opensearch.password
# API user wazuh-wui: change it with the tool's API options (see -h), then put the same value in wazuh.yml
sudoedit /usr/share/wazuh-dashboard/data/wazuh/config/wazuh.yml
sudo systemctl restart wazuh-manager filebeat wazuh-dashboard
```

On Docker, generate the bcrypt hash with the indexer image's `hash.sh`, put it in `config/wazuh_indexer/internal_users.yml`, update the matching variables in `docker-compose.yml`, recreate the stack, and run `securityadmin.sh` inside the indexer container as the Wazuh Docker documentation describes.

**Why this fix works:** a credential works only when the side that checks it and the side that presents it agree. The tool changes the checking side, and the keystore and `wazuh.yml` edits update every presenting side. Do not "solve" it by giving Filebeat or the dashboard a different, more powerful user, or by disabling the security plugin.

**Prevent it:** change passwords only with the tool or the documented Docker procedure, keep the five-copies table in your runbook, and store each password in a password manager instead of in shell history.

**Next step:** [Certificates and passwords](48-wazuh-and-security-tools.md#certificates-and-passwords) · KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions ([course](https://kodekloud.com/courses/the-linux-basics-course)) · [Wazuh docs: dashboard troubleshooting](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/troubleshooting.html)

**Community threads:** [wazuh-docker #838](https://github.com/wazuh/wazuh-docker/issues/838) · [wazuh-docker #712](https://github.com/wazuh/wazuh-docker/issues/712) · [Google Group: No API available to connect](https://groups.google.com/g/wazuh/c/-7gjBdnst50) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22wazuh+api+seems+to+be+down%22) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=api+seems+to+be+down&restrict_sr=1)

### 6.3 Indexer cluster yellow or red

> **Seen as:** `"status" : "yellow"` with `unassigned_shards` above 0, or `red` with searches failing on `all shards failed` · **Where:** single-node installs, a node that left a multi-node cluster, the hours after a disk-full event · **Level:** [L2 · Mid] · **How common:** recurring in the Google Group ("Wazuh-indexer doesn't work"), and standard OpenSearch operations

**Why it happens:** yellow means every primary shard is assigned but some replicas are not. Red means at least one primary is missing. On a single node, any index with `number_of_replicas` of 1 or more stays yellow forever, because a replica is never placed on the node that holds its primary. Other causes are a node that left the cluster, a disk above the low watermark (85% by default), which blocks new shards on that node, and allocation that gave up after five failed retries following a disk-full event. Red usually means a lost node without replicas, or a shard corrupted by a crash or a full disk.

**Diagnose:**

```bash
curl -sk -u admin "https://127.0.0.1:9200/_cluster/health?filter_path=status,number_of_nodes,unassigned_shards"
curl -sk -u admin "https://127.0.0.1:9200/_cat/shards?h=index,shard,prirep,state,unassigned.reason" | grep -v STARTED | head -n 2
curl -sk -u admin "https://127.0.0.1:9200/_cluster/allocation/explain?filter_path=index,allocate_explanation,node_allocation_decisions.deciders.explanation"
```

```
{"status":"yellow","number_of_nodes":1,"unassigned_shards":9}
wazuh-alerts-4.x-2026.10.01  0 r UNASSIGNED INDEX_CREATED
wazuh-alerts-4.x-2026.10.02  0 r UNASSIGNED INDEX_CREATED
{"index":"wazuh-alerts-4.x-2026.10.01","allocate_explanation":"cannot allocate because allocation is not permitted to any of the nodes","node_allocation_decisions":[{"deciders":[{"explanation":"a copy of this shard is already allocated to this node [[wazuh-alerts-4.x-2026.10.01][0], node[aG3k...], [P], s[STARTED]]"}]}]}
```

**What the output tells you:** only replicas (`r`) are unassigned, the reason is `INDEX_CREATED`, and the explanation says the copy would land next to its own primary. This is the single-node case: harmless for the data, but it hides real problems behind a permanent yellow. Reasons such as `NODE_LEFT` or `ALLOCATION_FAILED` point instead to a lost node or a disk event.

**Fix:**

```bash
# Single node: replicas can never be placed, so set them to 0 on the existing Wazuh indices
curl -sk -u admin -X PUT "https://127.0.0.1:9200/wazuh-*/_settings" -H 'Content-Type: application/json' -d '{"index":{"number_of_replicas":0}}'
# Allocation gave up after a disk-full event: retry it once the disk is fixed
curl -sk -u admin -X POST "https://127.0.0.1:9200/_cluster/reroute?retry_failed=true"
```

For a red index with a corrupted primary and no replica, restore that index from a snapshot. If there is no snapshot and you can afford to lose that day, delete the index. Forcing an empty or stale primary with the reroute API accepts data loss explicitly, so only do it after reading the OpenSearch documentation and writing down what you lose.

**Why this fix works:** health reflects shard placement rules. Removing replicas that can never be placed returns a single node to green, so a future yellow or red means something again. Real redundancy needs at least three indexer nodes with replicas set to 1.

**Prevent it:** run single-node installs with replicas set to 0 plus nightly snapshots, run production with three or more nodes, and alert whenever health is not green.

**Next step:** [Weekly health checks](48-wazuh-and-security-tools.md#weekly-health-checks) · KodeKloud: *EFK Stack: Enterprise-Grade Logging and Monitoring* ([course](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring)) · [Wazuh docs: cluster management](https://documentation.wazuh.com/current/user-manual/wazuh-indexer-cluster/cluster-management.html)

**Community threads:** [Google Group: Wazuh-indexer doesn't work](https://groups.google.com/g/wazuh/c/nwTRrcV8Y40) · [Wazuh docs: indexer indices](https://documentation.wazuh.com/current/user-manual/wazuh-indexer/wazuh-indexer-indices.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=opensearch+yellow+unassigned+replica+single+node) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=indexer+yellow&restrict_sr=1)

### 6.4 Disk watermark made indices read-only

> **Seen as:** Filebeat logs `blocked by: [TOO_MANY_REQUESTS/12/disk usage exceeded flood-stage watermark, index has read-only-allow-delete block]`; alerts stop at one moment while `alerts.json` keeps growing · **Where:** installs without a retention policy, with archives enabled, or with a disk shared with the server · **Level:** [L2 · Mid] · **How common:** several group threads ("Wazuh read-only", "TOO_MANY_REQUESTS ... disk usage exceeded") and GitHub discussion #33799 about single-node disk pressure

**Why it happens:** OpenSearch protects itself in three steps. Above 85% disk use (low watermark), it stops placing new shards on the node. Above 90% (high watermark), it moves shards away if it can. Above 95% (flood stage), it puts a `read_only_allow_delete` block on the node's indices, so Filebeat's writes fail with a 429. On a single-node Wazuh install that means alerts stop being indexed. The disk fills because there is no ISM retention policy, because `logall_json` archives were left on, or because the server's own logs share the filesystem.

**Diagnose:**

```bash
df -h /var/lib/wazuh-indexer
curl -sk -u admin "https://127.0.0.1:9200/_cat/allocation?v&h=disk.percent,disk.used,disk.avail"
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/wazuh-*?h=index,store.size&s=store.size:desc" | head -n 3
sudo grep -h 'flood-stage' /var/log/filebeat/filebeat* | tail -n 1
```

```
Filesystem                         Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   94G  4.1G  96% /
disk.percent disk.used disk.avail
          96    94.1gb      4.1gb
wazuh-archives-4.x-2026.10.02  14.8gb
wazuh-archives-4.x-2026.10.01  14.6gb
wazuh-alerts-4.x-2026.10.02     1.2gb
2026-10-03T06:02:11.512Z  WARN  [elasticsearch]  ... blocked by: [TOO_MANY_REQUESTS/12/disk usage exceeded flood-stage watermark, index has read-only-allow-delete block];
```

**What the output tells you:** 96% used, and the daily archives indices are more than ten times the size of the alerts. Someone enabled archives for debugging and never turned them off.

**Fix:**

```bash
# 1. Free space: list what a pattern matches, then delete the oldest indices you can afford to lose
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/wazuh-archives-4.x-2026.09.*?h=index"
curl -sk -u admin -X DELETE "https://127.0.0.1:9200/wazuh-archives-4.x-2026.09.*"
# 2. The block is lifted automatically once usage falls below the high watermark; clear it if someone set it by hand
curl -sk -u admin -X PUT "https://127.0.0.1:9200/wazuh-*/_settings" -H 'Content-Type: application/json' -d '{"index.blocks.read_only_allow_delete": null}'
# 3. Stop the growth: archives off (entry 7.5) and the ISM retention policy from §3
sudo grep -nE 'logall' /var/ossec/etc/ossec.conf
```

**Why this fix works:** the watermarks are a safety brake, not the fault. Free the space and the brake releases. Do not raise the watermarks to 99%: a full data disk can corrupt shards and turn yellow into red (entry 6.3). Events rejected during the block are still in the compressed files under `/var/ossec/logs/alerts/` on the server if you need to investigate that window.

**Prevent it:** add the ISM retention policy, alert at 75% disk, give the indexer data its own volume, and enable archives only for a short debugging window.

**Next step:** [Index retention and disk budget](48-wazuh-and-security-tools.md#index-retention-and-disk-budget) · [Disk space usage](01-storage-disk.md#1-disk-space-usage) · KodeKloud: *EFK Stack: Enterprise-Grade Logging and Monitoring* · [Wazuh docs: index lifecycle management](https://documentation.wazuh.com/current/user-manual/wazuh-indexer-cluster/index-lifecycle-management.html)

**Community threads:** [Google Group: TOO_MANY_REQUESTS disk usage exceeded](https://groups.google.com/g/wazuh/c/9mazw9zCz0w) · [Google Group: Wazuh read-only](https://groups.google.com/g/wazuh/c/ST6OVgBrBm4) · [GitHub discussion #33799: events lost over time on a single node](https://github.com/wazuh/wazuh/discussions/33799) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22flood-stage+watermark%22+read-only-allow-delete) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=read-only-allow-delete&restrict_sr=1)

### 6.5 Maximum shards open (1000/1000)

> **Seen as:** Filebeat logs `Validation Failed: 1: this action would add [3] total shards, but this cluster currently has [1000]/[1000] maximum shards open;` and no alerts appear after midnight · **Where:** single-node installs that have run for six to twelve months without retention · **Level:** [L2 · Mid] · **How common:** a classic Google Group thread ("maximum shards open limit - looking for clues") and a regular question every year

**Why it happens:** OpenSearch limits each data node to 1000 open shards by default (`cluster.max_shards_per_node`). Wazuh creates a new alerts index every day with three primary shards, plus monitoring and statistics indices. One node therefore reaches the limit after roughly 300 days. At midnight the new daily index cannot be created, and every alert for that day is rejected.

**Diagnose:**

```bash
curl -sk -u admin "https://127.0.0.1:9200/_cluster/health?filter_path=active_shards,number_of_nodes"
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices?h=index" | sed -E 's/-[^-]+$//' | sort | uniq -c | sort -rn | head -n 4
sudo grep -h 'maximum shards open' /var/log/filebeat/filebeat* | tail -n 1
```

```
{"active_shards":1000,"number_of_nodes":1}
    301 wazuh-alerts-4.x
     43 wazuh-monitoring
     43 wazuh-statistics
      2 wazuh-states-vulnerabilities
```

**What the output tells you:** 301 daily alert indices at three shards each use about 900 of the 1000 slots. Retention was never set up.

**Fix:**

```bash
# Delete what your retention period no longer requires (list first, then delete)
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/wazuh-alerts-4.x-2025.*?h=index" | wc -l
curl -sk -u admin -X DELETE "https://127.0.0.1:9200/wazuh-alerts-4.x-2025.*"
# Single node: one primary shard per daily index is plenty; edit the template Filebeat loads, then reload it
sudo sed -i 's/"index.number_of_shards": "3"/"index.number_of_shards": "1"/' /etc/filebeat/wazuh-template.json
sudo filebeat setup --index-management -E output.logstash.enabled=false
# Emergency only, for a few days while you clean up
curl -sk -u admin -X PUT "https://127.0.0.1:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{"persistent":{"cluster.max_shards_per_node":1200}}'
```

**Why this fix works:** every shard costs heap and file handles whether you search it or not. Fewer, larger shards plus retention keep the count stable. Raising the limit treats the symptom: memory pressure grows until the indexer falls over (entry 6.6). If you raised it as an emergency step, lower it again once you have cleaned up.

**Prevent it:** add the ISM retention policy from §3, use one shard per daily index on single-node installs, and alert when `active_shards` passes 800.

**Next step:** [Index retention and disk budget](48-wazuh-and-security-tools.md#index-retention-and-disk-budget) · KodeKloud: *EFK Stack: Enterprise-Grade Logging and Monitoring* · [Wazuh docs: indexer indices](https://documentation.wazuh.com/current/user-manual/wazuh-indexer/wazuh-indexer-indices.html)

**Community threads:** [Google Group: maximum shards open limit](https://groups.google.com/g/wazuh/c/AungE5r1llI) · [Google Group: Wazuh stopped displaying new logs](https://groups.google.com/g/wazuh/c/TwAMgqcjXH8) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22maximum+shards+open%22+opensearch) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=maximum+shards+open&restrict_sr=1)

### 6.6 Indexer will not start

> **Seen as:** `wazuh-indexer.service` failed with `Result: oom-kill`; or the log says `max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]`; or `java.nio.file.AccessDeniedException: /etc/wazuh-indexer/certs/indexer-key.pem`; in Docker, the indexer container restarts in a loop · **Where:** undersized all-in-one VMs, Docker and LXC hosts, certificates copied by hand · **Level:** [L2 · Mid] · **How common:** wazuh-docker #1076 (containers keep rebooting, 23 comments), #903 (rlimits), and many group threads

**Why it happens:** the indexer is a Java service that needs memory, kernel settings and readable certificates before it serves anything. On a 4 GB all-in-one VM, the indexer heap plus the server plus the dashboard do not fit, and the kernel kills the biggest process. Inside Docker or LXC, the host's `vm.max_map_count` applies, and older defaults (65530) are too low. Recent Ubuntu releases ship a much higher default, so you see this mostly on older hosts and containers. After a manual certificate copy, files owned by root with the wrong mode cannot be read by the `wazuh-indexer` user.

**Diagnose:**

```bash
sudo systemctl status wazuh-indexer --no-pager | sed -n 3p
sudo journalctl -k --since "-1d" --no-pager | grep -iE 'out of memory|killed process' | tail -n 1
sudo grep -hiE 'max_map_count|AccessDenied|OutOfMemory' /var/log/wazuh-indexer/wazuh-cluster.log | tail -n 2
free -h | head -n 2; sysctl vm.max_map_count; sudo grep -E '^-Xm[sx]' /etc/wazuh-indexer/jvm.options
sudo ls -l /etc/wazuh-indexer/certs/indexer-key.pem
```

```
     Active: failed (Result: oom-kill) since Sat 2026-10-03 03:12:55 UTC; 6h ago
Oct 03 03:12:55 wazuh01 kernel: Out of memory: Killed process 1187 (java) total-vm:7912344kB, anon-rss:2650112kB
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       3.5Gi       112Mi        12Mi       210Mi        96Mi
vm.max_map_count = 1048576
-Xms2g
-Xmx2g
-r-------- 1 root root 1704 Oct  1 10:02 /etc/wazuh-indexer/certs/indexer-key.pem
```

**What the output tells you:** a 3.8 GiB VM with a 2 GB heap was OOM-killed: the VM is below the minimum. `vm.max_map_count` is already high, so leave it alone. The key file belongs to root, so even with enough memory the next start would fail with `AccessDeniedException`.

**Fix:**

```bash
# Memory: give the VM 8 GB (all-in-one minimum), then keep the heap at about half of what the indexer can use
sudo sed -i -E 's/^-Xms.*/-Xms4g/; s/^-Xmx.*/-Xmx4g/' /etc/wazuh-indexer/jvm.options
# Kernel setting: raise it only if sysctl showed a value below 262144
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.d/99-wazuh-indexer.conf && sudo sysctl --system
# Certificates: owned by the indexer user, directory 500, files 400
sudo chown -R wazuh-indexer:wazuh-indexer /etc/wazuh-indexer/certs
sudo chmod 500 /etc/wazuh-indexer/certs && sudo chmod 400 /etc/wazuh-indexer/certs/*
sudo systemctl restart wazuh-indexer
```

**Why this fix works:** the heap is only part of the indexer's memory. The operating system's page cache does most of the search work, which is why the heap should stay near half of the available RAM and never above about 31 GB. Do not "fix" an OOM kill by shrinking the heap to 512 MB on a 4 GB VM: it will start, then crash under the first real query. Do not lower `vm.max_map_count` below what your distribution ships either.

**Prevent it:** size the VM from the quickstart table, alert on memory and swap use, keep other heavy services off the Wazuh VM, and always copy certificates with the ownership and modes shown above.

**Next step:** [Memory](04-memory.md) · [Sizing and scaling](48-wazuh-and-security-tools.md#sizing-and-scaling) · KodeKloud: *Docker Certified Associate* — Docker Engine – Security (resource limits) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [Wazuh quickstart (requirements)](https://documentation.wazuh.com/current/quickstart.html)

**Community threads:** [wazuh-docker #1076: containers keep rebooting](https://github.com/wazuh/wazuh-docker/issues/1076) · [wazuh-docker #903: rlimits error](https://github.com/wazuh/wazuh-docker/issues/903) · [Google Group: Wazuh-indexer doesn't work](https://groups.google.com/g/wazuh/c/nwTRrcV8Y40) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh-indexer+failed+to+start) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=indexer+oom&restrict_sr=1)

### 6.7 Certificate errors after an IP change

> **Seen as:** `filebeat test output` says `x509: certificate is valid for 192.0.2.10, not 10.0.5.20`; the dashboard logs `Hostname/IP does not match certificate's altnames` · **Where:** a DHCP lease change, an OVA imported into a new network, a cloned or migrated VM · **Level:** [L2 · Mid] · **How common:** wazuh-docker #2063 ("SSL Cert errors", 17 comments), #733 and #1142 on certificate generation

**Why it happens:** the installer builds every node certificate from `config.yml`, and it writes each node's IP (and name) into the certificate's Subject Alternative Name. TLS clients check that the address they dialled appears in the SAN. Change the server's IP and every client now dials an address the certificate does not list. Two related mistakes are regenerating one component's certificate from a new root CA (the chain no longer matches) and letting certificates expire.

**Diagnose:**

```bash
sudo openssl x509 -in /etc/wazuh-indexer/certs/indexer.pem -noout -subject -enddate -ext subjectAltName
for f in /etc/wazuh-indexer/certs/root-ca.pem /etc/filebeat/certs/root-ca.pem /etc/wazuh-dashboard/certs/root-ca.pem; do sudo openssl x509 -in "$f" -noout -fingerprint -sha256; done
ip -br -4 addr show scope global
sudo filebeat test output 2>&1 | grep -iE 'x509|handshake'
```

```
subject=C = US, L = California, O = Wazuh, OU = Wazuh, CN = node-1
notAfter=Sep 28 10:02:11 2035 GMT
X509v3 Subject Alternative Name:
    DNS:node-1, IP Address:192.0.2.10
sha256 Fingerprint=4F:1A:...:9C
sha256 Fingerprint=4F:1A:...:9C
sha256 Fingerprint=4F:1A:...:9C
ens18            UP             10.0.5.20/24
    handshake... ERROR x509: certificate is valid for 192.0.2.10, not 10.0.5.20
```

**What the output tells you:** the certificate is far from expiry, all three components trust the same root CA, and only the SAN is wrong. Either give the server its old IP back, or reissue the node certificates from the same CA.

**Fix:**

```bash
# Option 1 (simplest): give wazuh01 its old address back with a static IP or a DHCP reservation.
# Option 2: reissue node certificates for the new address, signed by the SAME root CA
mkdir -p ~/wazuh-certs && cd ~/wazuh-certs
sudo tar -xf /root/wazuh-install-files.tar wazuh-install-files/root-ca.pem wazuh-install-files/root-ca.key
curl -sO https://packages.wazuh.com/4.14/wazuh-certs-tool.sh
printf 'nodes:\n  indexer:\n    - name: node-1\n      ip: "10.0.5.20"\n  server:\n    - name: wazuh-1\n      ip: "10.0.5.20"\n  dashboard:\n    - name: dashboard\n      ip: "10.0.5.20"\n' > config.yml
sudo bash wazuh-certs-tool.sh -h       # use the option that signs with an existing root CA (root-ca.pem + root-ca.key)
```

Then copy each new certificate and key into its component's `certs` directory under the expected file name, with the ownership and modes from entry 6.6. Replace the old IP in `opensearch.yml` (`network.host`), `opensearch_dashboards.yml` (`opensearch.hosts`), `filebeat.yml` (`hosts`), the `indexer` block of `ossec.conf`, and the API URL in `wazuh.yml`, and restart the indexer, server, Filebeat and dashboard in that order.

**Why this fix works:** reusing the root CA means every trust store stays valid and only the leaf certificates change. Do not set `ssl.verification_mode: none` in Filebeat or `opensearch.ssl.verificationMode: none` in the dashboard. That turns a loud, fixable error into silent exposure to anyone who can intercept the traffic.

**Prevent it:** give the Wazuh VM a static address, put DNS names in the SAN and use them in every config, monitor expiry with `openssl x509 -checkend`, and keep `wazuh-install-files.tar` (with the root CA key) safe and offline.

**Next step:** [Scenario: x509 unknown authority](37-learn-security-devsecops.md#scenario-x509-unknown-authority) · [TLS and certificates](18-web-http-tls.md#3-tls-certificates-openssl) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Work With SSL Certificates ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · [Wazuh documentation](https://documentation.wazuh.com/current/)

**Community threads:** [wazuh-docker #2063: SSL Cert errors](https://github.com/wazuh/wazuh-docker/issues/2063) · [wazuh-docker #733: generate-indexer-certs error](https://github.com/wazuh/wazuh-docker/issues/733) · [wazuh-docker #1142: certificate tool missing](https://github.com/wazuh/wazuh-docker/issues/1142) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+x509+certificate+is+valid+for) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=certificate+ip+change&restrict_sr=1)

---

## 7. Wazuh rules, modules and operations

### 7.1 Logs collected but no alerts

> **Seen as:** a new source (Traefik JSON log, an app log, Docker container logs) shows nothing in the dashboard, and `wazuh-logtest` prints `No decoder matched.` · **Where:** every time you add a log source · **Level:** [L2 · Mid] · **How common:** group threads such as "Wazuh cannot capture log" and "Not showing alerts or archives"; the docs have a whole page on testing decoders and rules

**Why it happens:** an event becomes an alert only when four things are true: the agent reads the file, the line reaches the server, a decoder understands it, and a rule with level 3 or higher matches it. The usual breaks are a wrong path or glob, or a `localfile` block in a group the agent is not part of. Another is testing with old lines, because the logcollector only reads lines written after it started. Custom formats have no decoder, and sometimes the only rule that matches has level 0. For Docker events, the `docker-listener` wodle fails if the Python Docker module is missing.

**Diagnose:**

```bash
# Agent: is the file being read at all?
sudo grep -E 'logcollector.*(Analyzing file|Could not open)' /var/ossec/logs/ossec.log | tail -n 2
# Server: what does the ruleset do with one real line? (paste the line at the prompt)
sudo /var/ossec/bin/wazuh-logtest
```

```
wazuh-logcollector: INFO: (1950): Analyzing file: '/var/log/shopapi/app.log'.
**Phase 1: Completed pre-decoding.
	full event: '[shopapi] WARN login failed user=bob ip=203.0.113.50'
**Phase 2: Completed decoding.
	No decoder matched.
```

**What the output tells you:** the agent reads the file and the line reaches the analysis engine, but nothing knows how to parse it. You need a decoder and a rule, or the app should log JSON. If Phase 1 had shown a `hostname` or `program_name`, the line would have a syslog header, and the decoder should match on `program_name` instead.

**Fix:**

```xml
<!-- /var/ossec/etc/decoders/local_decoder.xml -->
<decoder name="shopapi">
  <prematch>^[shopapi] </prematch>
</decoder>
<decoder name="shopapi-login">
  <parent>shopapi</parent>
  <regex>login failed user=(\S+) ip=(\S+)</regex>
  <order>user, srcip</order>
</decoder>
<!-- /var/ossec/etc/rules/local_rules.xml -->
<group name="local,shopapi,">
  <rule id="100300" level="5">
    <decoded_as>shopapi</decoded_as>
    <match>login failed</match>
    <description>shopapi: failed login for $(user) from $(srcip)</description>
  </rule>
</group>
```

Run `wazuh-logtest` again until Phase 3 shows rule 100300, then run `sudo systemctl restart wazuh-manager`. To prove that events arrive at all, enable `logall_json` for a few minutes and watch `/var/ossec/logs/archives/archives.json`, then turn it off again (entry 7.5).

**Why this fix works:** decoders turn text into fields and rules decide what matters. Extracting `srcip` also lets frequency rules and active response use the address. JSON logs skip the decoder work entirely, because the built-in JSON decoder names every field.

**Prevent it:** test every new source with `wazuh-logtest` before rollout, and keep `local_decoder.xml` and `local_rules.xml` in Git with a CI step that runs sample lines through the API's logtest endpoint.

**Next step:** [Your first custom rule](48-wazuh-and-security-tools.md#your-first-custom-rule) · KodeKloud: *Advanced Bash Scripting* — awk and sed, for slicing sample lines ([course](https://kodekloud.com/courses/advanced-bash-scripting)) · [Wazuh docs: testing decoders and rules](https://documentation.wazuh.com/current/user-manual/ruleset/testing.html)

**Community threads:** [Wazuh docs: custom decoders](https://documentation.wazuh.com/current/user-manual/ruleset/decoders/custom.html) · [Wazuh docs: custom rules](https://documentation.wazuh.com/current/user-manual/ruleset/rules/custom.html) · [Google Group: Wazuh cannot capture log](https://groups.google.com/g/wazuh/c/gGoWhgbXSO0) · [Google Group: Not showing alerts or archives](https://groups.google.com/g/wazuh/c/WCFSnM8uOZg) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+custom+decoder+no+decoder+matched) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=custom+decoder&restrict_sr=1)

### 7.2 Noisy rules and flooded agent queues

> **Seen as:** thousands of alerts a day from a handful of rules (5710 invalid SSH users, 31101 web 400s, 550 and 554 file changes after `apt upgrade`, 510 `Trojaned version of file '/bin/diff' detected`); agents raise `Agent event queue is full. Events may be lost.` · **Where:** internet-facing hosts, busy Traefik access logs, after patch nights · **Level:** [L2 · Mid] · **How common:** GitHub #19346 (Trojaned /bin/diff, 61 comments), #19792 (SCA false positive, 74 comments), #25456 (sync omitted due to abuse control)

**Why it happens:** the default ruleset is broad on purpose, and an internet-facing SSH port collects scanner noise all day. Full access logs from a busy site exceed the agent's buffer, which defaults to 5000 queued events at 500 events per second. File integrity checks fire on every package upgrade, and rootcheck and SCA heuristics produce known false positives. The result is alert fatigue: people stop reading, and the one alert that matters scrolls past.

**Diagnose:**

```bash
# Top 10 rules of the last 24 hours, straight from the indexer
curl -sk -u admin -H 'Content-Type: application/json' "https://127.0.0.1:9200/wazuh-alerts-*/_search?size=0" \
  -d '{"query":{"range":{"timestamp":{"gte":"now-24h"}}},"aggs":{"top":{"terms":{"field":"rule.id","size":10}}}}' \
  | python3 -c 'import sys,json; [print(b["key"], b["doc_count"]) for b in json.load(sys.stdin)["aggregations"]["top"]["buckets"]]'
```

```
5710 48211
31101 20456
550 3120
510 1688
100201 912
```

**What the output tells you:** two rules produce most of the volume. 5710 is SSH user enumeration from the internet on a host that only accepts keys, and 31101 is every 4xx from a busy site. Neither needs a human.

**Fix:**

```xml
<!-- /var/ossec/etc/rules/local_rules.xml: level-0 children silence one precise condition, the parent stays intact -->
<group name="local,tuning,">
  <rule id="100100" level="0">
    <if_sid>5710</if_sid>
    <srcip>!10.0.0.0/8</srcip>
    <description>Tuned: invalid SSH user from outside (key-only SSH); keep internal attempts</description>
  </rule>
</group>
```

Cut volume at the source too: Traefik's `accessLog.filters.statusCodes` (§2) keeps 200s out of Wazuh entirely. Only after filtering, raise `queue_size` and `events_per_second` in the agent's `client_buffer` block.

**Why this fix works:** a level-0 child rule stops alerts only for the condition you name, survives upgrades (it lives in `local_rules.xml`), and leaves the original rule working for everything else, including internal sources that could signal lateral movement. Do not delete rules from the shipped ruleset, and do not raise `log_alert_level` globally: both hide real signals.

**Prevent it:** review the top 10 rules every week, record each suppression with a reason, owner and date, and set an alert budget (for example, no more than 20 alerts a day that need a human).

**Next step:** [Alertmanager and alert rules](32-learn-performance-observability.md#12-alertmanager-and-alert-rules) · KodeKloud: *Fundamentals of SRE* — Incident Management, Designing Effective Alerts ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · [Wazuh docs: custom rules](https://documentation.wazuh.com/current/user-manual/ruleset/rules/custom.html)

**Community threads:** [GitHub #19346: Trojaned /bin/diff](https://github.com/wazuh/wazuh/issues/19346) · [GitHub #19792: SCA guest account false positive](https://github.com/wazuh/wazuh/issues/19792) · [GitHub #25456: sync omitted due to abuse control](https://github.com/wazuh/wazuh/issues/25456) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+reduce+noise+rule+level+0) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=too+many+alerts&restrict_sr=1)

### 7.3 FIM real-time changes not reported

> **Seen as:** you edit `/etc/ssh/sshd_config` and the alert arrives hours later or never; the agent logs `Unable to add inotify watch to real time monitoring` · **Where:** hosts with large monitored trees, Docker hosts, NFS mounts · **Level:** [L2 · Mid] · **How common:** a recurring configuration question; inotify limits are a Linux classic

**Why it happens:** without `realtime="yes"`, a directory is checked only by the scheduled scan, every 12 hours by default. Real-time mode needs one inotify watch per directory. Pointing it at huge trees such as `/var/lib/docker` uses up the per-user watch limit, after which new watches fail silently except for that log line. Network filesystems do not deliver inotify events at all. `whodata` mode depends on auditd and conflicts with locked audit configurations (`-e 2`).

**Diagnose:**

```bash
sudo grep -iE 'inotify|real time|whodata' /var/ossec/logs/ossec.log | tail -n 2
sudo grep -E '<directories|<frequency' /var/ossec/etc/ossec.conf
sysctl fs.inotify.max_user_watches
```

```
wazuh-syscheckd: WARNING: Unable to add inotify watch to real time monitoring: '/var/lib/docker/overlay2/9b1c.../merged'. '-1' '28': The maximum limit of inotify watches has been reached.
    <frequency>43200</frequency>
    <directories realtime="yes">/etc,/usr/bin,/usr/sbin,/var/lib/docker</directories>
fs.inotify.max_user_watches = 65536
```

**What the output tells you:** `/var/lib/docker` holds tens of thousands of directories, used up every watch, and left no room for `/etc`. The scope is the problem, not Wazuh.

**Fix:**

```xml
<syscheck>
  <frequency>43200</frequency>
  <directories realtime="yes" check_all="yes">/etc/ssh,/etc/sudoers.d,/etc/dokploy/traefik</directories>
  <directories whodata="yes">/etc/passwd,/etc/shadow,/etc/group</directories>
  <directories>/etc,/usr/bin,/usr/sbin</directories>
  <ignore type="sregex">.log$|.swp$</ignore>
</syscheck>
```

If you still need more watches, raise the limit with `echo 'fs.inotify.max_user_watches=524288' | sudo tee /etc/sysctl.d/99-inotify.conf && sudo sysctl --system`.

**Why this fix works:** real-time monitoring belongs on small, high-value directories. Everything else is covered by the scheduled scan, and `whodata` adds the user who made the change for credential files. Container layers are not configuration. Image scanning (Trivy) and runtime tools cover them better.

**Prevent it:** define FIM scope as configuration, binaries and credentials, and after each change `touch` a test file and expect the alert within a minute.

**Next step:** [auditd basics](37-learn-security-devsecops.md#auditd-basics) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — Runtime Security (audit logs) ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · [Wazuh documentation](https://documentation.wazuh.com/current/)

**Community threads:** [GitHub search: inotify realtime](https://github.com/wazuh/wazuh/issues?q=inotify+realtime) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+syscheck+realtime+not+working) · [Server Fault](https://serverfault.com/search?q=inotify+max_user_watches+reached) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=fim+realtime&restrict_sr=1)

### 7.4 Vulnerability detection empty or wrong

> **Seen as:** the Vulnerability Detection page shows no results, and the server logs `IndexerConnector initialization failed for index 'wazuh-states-vulnerabilities-wazuh01', retrying until the connection is successful.`; or it lists CVEs for snap or ESM packages that are already patched · **Where:** 4.8 and later, after a password change, on servers without internet egress · **Level:** [L2 · Mid] · **How common:** many 4.8+ issues: #24113, #24171 and #28563 (false positives), #24151 (RocksDB errors), #27260 (memory)

**Why it happens:** since 4.8 the server matches every agent's package inventory (syscollector) against Wazuh's threat-intelligence feed, then writes the results to the indexer through the indexer connector. Results are empty when that connector cannot authenticate (the `wazuh-keystore` copy of the password is stale), when the server cannot download the feed (no egress or a missing proxy), or when syscollector is disabled on the agents so there is nothing to match. False positives come from the hard problem of translating version strings for backported, ESM and snap packages, and many have been fixed in later patch releases.

**Diagnose:**

```bash
sudo grep -iE 'indexer-connector|vulnerability' /var/ossec/logs/ossec.log | tail -n 3
curl -sk -u admin "https://127.0.0.1:9200/_cat/indices/wazuh-states-vuln*?h=index,docs.count"
curl -sk -H "Authorization: Bearer $TOKEN" "https://127.0.0.1:55000/syscollector/001/packages?limit=1&select=name,version" | head -c 300; echo
```

```
2026/10/03 08:00:12 indexer-connector: WARNING: IndexerConnector initialization failed for index 'wazuh-states-vulnerabilities-wazuh01', retrying until the connection is successful.
{"data": {"affected_items": [{"name": "openssl", "version": "3.0.13-0ubuntu3.5"}], "total_affected_items": 712, ...
```

**What the output tells you:** inventory exists (712 packages on agent 001), but the states index does not even exist, because the connector cannot log in. Scanning may well be working while nothing is ever stored.

**Fix:**

```bash
# Give the connector the current indexer credentials (after every admin password change)
sudo /var/ossec/bin/wazuh-keystore -f indexer -k username -v admin
sudo /var/ossec/bin/wazuh-keystore -f indexer -k password -v 'ADMIN_PASSWORD'
sudo systemctl restart wazuh-manager
# No egress? allow HTTPS from the server to the Wazuh feed, set the proxy, or use the documented offline update
```

For false positives, check the package against your distribution's security tracker, look for a fix in newer Wazuh patch releases, and record accepted findings with a reason instead of muting the module.

**Why this fix works:** the dashboard only shows what is in `wazuh-states-vulnerabilities-*`. Once the connector can write, the next scan cycle fills the index. Treat the module as triage input that points you at hosts to patch, not as the final word.

**Prevent it:** add `wazuh-keystore` to the password checklist (entry 6.2), alert when the states index has zero documents, and keep the server's egress to the feed in the firewall documentation.

**Next step:** [Image scanning with Trivy](37-learn-security-devsecops.md#image-scanning-with-trivy) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — Supply Chain Security · [Wazuh docs: indexer integration](https://documentation.wazuh.com/current/user-manual/manager/indexer-integration.html)

**Community threads:** [GitHub #24113: snap package false positives](https://github.com/wazuh/wazuh/issues/24113) · [GitHub #24171: 4.8 false positives](https://github.com/wazuh/wazuh/issues/24171) · [GitHub #24151: RocksDB errors](https://github.com/wazuh/wazuh/issues/24151) · [Google Group: vulnerability module stuck](https://groups.google.com/g/wazuh/c/BmHALiKqvZs) · Search: [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=vulnerability+detection+empty&restrict_sr=1)

### 7.5 Manager disk fills with logs and archives

> **Seen as:** `No space left on device` on the server, daemons crashing, and `/var/ossec` using tens of GB · **Where:** long-running servers, all-in-one installs where the indexer shares the disk · **Level:** [L1 · Junior] · **How common:** common on installs older than a year; GitHub discussion #33799 shows the single-node variant

**Why it happens:** the server compresses `alerts.json` and `alerts.log` (and archives, if enabled) into dated folders every night under `/var/ossec/logs/`, and it never deletes them. With `logall` or `logall_json` turned on, every event is stored, not only alerts, so that folder grows many times faster than the alerts.

**Diagnose:**

```bash
df -h /var/ossec
sudo du -xh --max-depth=2 /var/ossec | sort -rh | head -n 4
sudo grep -nE '<logall>|<logall_json>' /var/ossec/etc/ossec.conf
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   97G  1.0G  99% /
66G   /var/ossec
62G   /var/ossec/logs
61G   /var/ossec/logs/archives
4.1G  /var/ossec/logs/alerts
14:    <logall>yes</logall>
15:    <logall_json>yes</logall_json>
```

**What the output tells you:** the archives use 61 GB and both archive switches are on. That is the whole problem.

**Fix:**

```bash
# 1. Turn archives off unless you are actively debugging a decoder
sudo sed -i -E 's#<logall>yes#<logall>no#; s#<logall_json>yes#<logall_json>no#' /var/ossec/etc/ossec.conf && sudo systemctl restart wazuh-manager
# 2. Keep 30 days of local copies; the indexer holds the searchable copy
printf '#!/bin/sh\nfind /var/ossec/logs/alerts /var/ossec/logs/archives -type f -mtime +30 \\( -name "*.gz" -o -name "*.sum" \\) -delete\n' | sudo tee /etc/cron.daily/wazuh-log-retention >/dev/null
sudo chmod 755 /etc/cron.daily/wazuh-log-retention
```

**Why this fix works:** the local files are a buffer and an audit copy, not the place you search. If compliance needs longer retention, archive them to object storage before deleting, instead of keeping them on the server's root disk.

**Prevent it:** put `/var/ossec` on its own logical volume, alert at 75% disk, and write the retention period (and who decided it) into the runbook.

**Next step:** [Disk space usage](01-storage-disk.md#1-disk-space-usage) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Locate and Analyze System Log Files · [Wazuh docs: event logging](https://documentation.wazuh.com/current/user-manual/manager/wazuh-archives.html)

**Community threads:** [GitHub discussion #33799](https://github.com/wazuh/wazuh/discussions/33799) · Search: [Server Fault](https://serverfault.com/search?q=wazuh+disk+full+archives) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=disk+full+archives&restrict_sr=1)

### 7.6 Active response locks you out

> **Seen as:** right after enabling `firewall-drop`, your SSH session freezes, the CI runner cannot deploy, or the whole office loses access; `/var/ossec/logs/active-responses.log` shows an `add` for your own address · **Where:** the first week of active response · **Level:** [L2 · Mid] · **How common:** the classic active-response mistake; the docs ship a dedicated use case for SSH brute force

**Why it happens:** active response turns a log line into a firewall rule with nobody checking. An office behind one NAT address, a CI runner that retries with a stale key, or a monitoring probe can look exactly like a brute-force source. Without a `white_list`, a timeout and a narrow rule list, the block hits people you need. On hosts that run Docker, check where the drop rule sits: rules that only land in INPUT do not protect published container ports.

**Diagnose:**

```bash
sudo tail -n 2 /var/ossec/logs/active-responses.log                          # on the agent that blocked
sudo iptables -S INPUT | grep DROP; sudo iptables -S FORWARD | grep DROP
sudo grep -nE 'white_list|<rules_id>|<timeout>' /var/ossec/etc/ossec.conf   # on the server
```

```
2026/10/03 11:20:03 active-response/bin/firewall-drop: {"version":1,"origin":{"name":"node01","module":"wazuh-execd"},"command":"add","parameters":{"alert":{"rule":{"id":"5763","level":10},"data":{"srcip":"198.51.100.23"}}}}
-A INPUT -s 198.51.100.23/32 -j DROP
-A FORWARD -s 198.51.100.23/32 -j DROP
318:    <rules_id>5763</rules_id>
```

**What the output tells you:** rule 5763 (SSH brute force) fired for 198.51.100.23, which is the office NAT address, and there is no `white_list` and no `timeout`. The block is permanent.

**Fix:**

```bash
# From the console or another admin path: remove the block now
sudo iptables -D INPUT -s 198.51.100.23/32 -j DROP; sudo iptables -D FORWARD -s 198.51.100.23/32 -j DROP
# Then on the server: add white_list entries (admin VPN, office NAT, CI runners) and a timeout, as in §2, and restart
sudo systemctl restart wazuh-manager
```

**Why this fix works:** the server checks `white_list` before it sends any block order, and `timeout` makes every block expire. Together they turn a mistake into a 10-minute annoyance instead of an outage. Find out why the office address failed logins in the first place (stale keys, a password spray from a compromised laptop) before you whitelist it forever.

**Prevent it:** before enabling active response, confirm console access (IPMI, the Proxmox console, a cloud serial console). Start with one rule, one host and a short timeout, review `active-responses.log` weekly, and prefer CrowdSec at the Traefik edge for HTTP.

**Next step:** [SSH hardening](37-learn-security-devsecops.md#ssh-hardening) · [SSH & remote access](09-ssh-remote-access.md) · KodeKloud: *Learning Linux Basics Course & Labs* — IPTABLES Introduction ([note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)) · [Wazuh docs: configuring active response](https://documentation.wazuh.com/current/user-manual/capabilities/active-response/how-to-configure.html)

**Community threads:** [Wazuh docs: blocking SSH brute force](https://documentation.wazuh.com/current/user-manual/capabilities/active-response/ar-use-cases/blocking-ssh-brute-force.html) · [Wazuh docs: active-response reference](https://documentation.wazuh.com/current/user-manual/reference/ossec-conf/active-response.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+active+response+firewall-drop+whitelist) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=active+response+blocked&restrict_sr=1)

### 7.7 Email or Slack alerts never arrive

> **Seen as:** no email ever, with `wazuh-maild: ERROR: (1223): Error Sending email to 'smtp.example.com' (smtp server)` in the server log; or Slack stays silent and `/var/ossec/logs/integrations.log` is empty · **Where:** the first notification setup · **Level:** [L1 · Junior] · **How common:** a long-standing FAQ, because maild cannot log in to SMTP servers

**Why it happens:** Wazuh's mail daemon speaks plain SMTP without authentication, so pointing it straight at a provider that requires login and TLS fails. Other causes are `email_notification` left at `no`, an `email_alert_level` (12 by default) above anything that fires, the hourly cap (`email_maxperhour`), a Slack integration whose `level` is higher than your alerts, a revoked webhook, or a server without HTTPS egress.

**Diagnose:**

```bash
sudo grep -E 'maild|integratord' /var/ossec/logs/ossec.log | tail -n 2
sudo grep -E 'email_notification|smtp_server|email_alert_level|<level>' /var/ossec/etc/ossec.conf
nc -vz 127.0.0.1 25; sudo tail -n 3 /var/ossec/logs/integrations.log
```

```
2026/10/03 12:01:44 wazuh-maild: ERROR: (1223): Error Sending email to 'smtp.example.com' (smtp server)
    <email_notification>yes</email_notification>
    <smtp_server>smtp.example.com</smtp_server>
    <email_alert_level>12</email_alert_level>
nc: connect to 127.0.0.1 port 25 (tcp) failed: Connection refused
```

**What the output tells you:** maild talks directly to an external server that requires authentication, and no local relay exists.

**Fix:**

```bash
# Local Postfix relay that authenticates upstream (choose "Satellite system" in the installer)
sudo apt-get install -y postfix libsasl2-modules
sudo postconf -e 'relayhost = [smtp.example.com]:587' 'smtp_sasl_auth_enable = yes' 'smtp_tls_security_level = encrypt' 'smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd' 'smtp_sasl_security_options = noanonymous'
echo '[smtp.example.com]:587 RELAY_USER:RELAY_PASSWORD' | sudo tee /etc/postfix/sasl_passwd >/dev/null && sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd && sudo systemctl restart postfix
sudo sed -i 's#<smtp_server>.*</smtp_server>#<smtp_server>localhost</smtp_server>#' /var/ossec/etc/ossec.conf && sudo systemctl restart wazuh-manager
# Slack: prove the webhook works from the server itself
curl -s -X POST -H 'Content-Type: application/json' -d '{"text":"wazuh01 webhook test"}' "https://hooks.slack.com/services/SLACK_WEBHOOK_PATH"
```

**Why this fix works:** Postfix handles authentication, TLS, queueing and retries, and maild only needs a local port 25. The webhook test separates "Slack rejects it" from "Wazuh never sends it". Add `integrator.debug=2` to `/var/ossec/etc/local_internal_options.conf` while you debug integrations, then remove it.

**Prevent it:** send a synthetic notification every month, alert when the Postfix queue (`mailq`) grows, and keep webhook URLs in your secret store, because anyone holding one can post to the channel.

**Next step:** [Alertmanager and alert rules](32-learn-performance-observability.md#12-alertmanager-and-alert-rules) · KodeKloud: *Fundamentals of SRE* — Designing Effective Alerts · [Wazuh documentation](https://documentation.wazuh.com/current/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+email+alerts+not+working+smtp) · [Server Fault](https://serverfault.com/search?q=postfix+relayhost+sasl+587) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=email+alerts&restrict_sr=1) · [GitHub search: wazuh maild](https://github.com/wazuh/wazuh/issues?q=maild+smtp)

### 7.8 Wazuh dashboard and Traefik fight for 443

> **Seen as:** after installing Wazuh all-in-one on the Dokploy host, Traefik restarts with `listen tcp :443: bind: address already in use` and every site goes down, or the dashboard fails with `EADDRINUSE` · **Where:** co-locating Wazuh with Dokploy, Apache or any other proxy · **Level:** [L2 · Mid] · **How common:** the same pattern as the Apache-vs-Dokploy incident in [module 21](21-case-apache-443-dokploy.md); port conflicts are a top community question

**Why it happens:** only one process can own 0.0.0.0:443, and the Wazuh dashboard listens there by default, just like Traefik. Whichever starts first wins. After the next reboot the winner can change, so the outage looks random.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :443'
docker ps -a --filter name=dokploy-traefik --format '{{.Names}}  {{.Status}}'
sudo grep -E '^server\.(host|port)' /etc/wazuh-dashboard/opensearch_dashboards.yml
```

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511          0.0.0.0:443        0.0.0.0:*     users:(("node",pid=2211,fd=19))
dokploy-traefik  Restarting (1) 12 seconds ago
server.host: 0.0.0.0
server.port: 443
```

**What the output tells you:** `node` (the dashboard) owns 443, so Traefik loops on its failed bind.

**Fix:**

```bash
# Best: move Wazuh to its own VM. In a lab, move the dashboard off 443 and let Traefik own the edge:
sudo sed -i -E 's/^server.port:.*/server.port: 8443/' /etc/wazuh-dashboard/opensearch_dashboards.yml
sudo systemctl restart wazuh-dashboard && docker restart dokploy-traefik
sudo ufw allow from 172.16.0.0/12 to any port 8443 proto tcp comment 'traefik to wazuh dashboard'
```

```yaml
# /etc/dokploy/traefik/dynamic/wazuh.yml: route wazuh.example.com to the dashboard, admin VPN only
http:
  routers:
    wazuh:
      rule: Host(`wazuh.example.com`)
      entryPoints: [websecure]
      service: wazuh
      middlewares: [admin-only]
      tls:
        certResolver: letsencrypt
  middlewares:
    admin-only:
      ipAllowList:
        sourceRange: ["10.0.99.0/24"]
  services:
    wazuh:
      loadBalancer:
        serversTransport: wazuh-ca
        servers:
          - url: "https://10.0.10.21:8443"    # dokploy01's own address: the dashboard now shares this host with Traefik
  serversTransports:
    wazuh-ca:
      rootCAs: ["/etc/dokploy/traefik/dynamic/wazuh-root-ca.pem"]
```

**Why this fix works:** one port has one owner. The edge proxy owns 443 and routes by host name, and everything else moves to an internal port. `rootCAs` makes Traefik verify the dashboard's certificate against the Wazuh root CA. Do not use `insecureSkipVerify: true`, which hides a man-in-the-middle. The allow-list keeps the dashboard off the public internet even though it shares the edge.

**Prevent it:** check `ss -ltnp` before every install, keep a port plan per host, and run the security monitor on its own VM.

**Next step:** [Choosing a port: the rules](35-deployment-patterns.md#2-choosing-a-port-the-rules) · [bind: Address already in use](22-playbook-ports-inventory.md#13-scenario-bind-address-already-in-use) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview ([course](https://kodekloud.com/courses/kubernetes-networking))

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=wazuh+dashboard+change+port+443) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=change+dashboard+port&restrict_sr=1) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=wazuh+traefik&restrict_sr=1)

### 7.9 An upgrade breaks the stack

> **Seen as:** after an upgrade the dashboard is "not ready yet", the indexer connector logs HTTP 404, or `wazuh-remoted` keeps crashing; agents refuse to enroll with `Agent version must be lower or equal to manager version` · **Where:** an `apt upgrade` or patch playbook that touched some Wazuh packages, agents upgraded before the server · **Level:** [L3 · Senior] · **How common:** GitHub #32044 (indexer breaks from 4.12 to 4.13, 84 comments), #33038 and #32820 (crashes on 4.13.1/4.14.0), group threads after 4.9, 4.12 and 4.13.1

**Why it happens:** Wazuh's central components are released and tested as a set, and the dashboard plugin, the Filebeat template and the server must match. Partial upgrades happen when the repository was left enabled and a routine `apt upgrade` or patch playbook took whatever was newest. dpkg conffile prompts can replace tuned configs, and new releases sometimes ship regressions. Agents newer than the server are rejected by design.

**Diagnose:**

```bash
apt list --installed 2>/dev/null | grep -E '^(wazuh-|filebeat)'
grep -E ' (upgrade|install) (wazuh|filebeat)' /var/log/dpkg.log | tail -n 3
ls /etc/wazuh-indexer/*.dpkg-* /etc/wazuh-dashboard/*.dpkg-* 2>/dev/null
```

```
filebeat/now 7.10.2-1 amd64 [installed,local]
wazuh-dashboard/now 4.13.1-1 amd64 [installed,local]
wazuh-indexer/now 4.14.0-1 amd64 [installed,local]
wazuh-manager/now 4.14.0-1 amd64 [installed,local]
2026-10-02 03:14:22 upgrade wazuh-indexer:amd64 4.13.1-1 4.14.0-1
2026-10-02 03:14:51 upgrade wazuh-manager:amd64 4.13.1-1 4.14.0-1
/etc/wazuh-dashboard/opensearch_dashboards.yml.dpkg-dist
```

**What the output tells you:** a 03:14 job upgraded the indexer and server but not the dashboard, so the versions are mixed. The `.dpkg-dist` file shows dpkg offered a new config that was not installed, which is good, because your tuned file was kept.

**Fix:**

```bash
# Finish the upgrade so every central component runs the same version, in order (full steps in §3)
sudo apt-get install -y wazuh-dashboard=4.14.0-1 && sudo systemctl restart wazuh-dashboard
sudo apt-mark hold wazuh-indexer wazuh-manager wazuh-dashboard filebeat
# Agent newer than the server: pin it back until the server is upgraded
sudo apt-get install -y --allow-downgrades wazuh-agent=4.13.1-1 && sudo apt-mark hold wazuh-agent
```

If the new release itself is broken (a crash loop in an open issue), roll back to the VM snapshot and wait for the patch release. Also refresh the Filebeat template after the server upgrade, as §3 shows.

**Why this fix works:** a consistent version set is what Wazuh tests. Holds stop unattended or bulk upgrades from creating a mixed set again. Do not "fix" a mixed set by downgrading only the indexer: indexer data written by a newer version may not be readable by an older one, which is why you roll back from a snapshot instead.

**Prevent it:** hold the packages, upgrade in a change window after a lab rehearsal and a snapshot, read the open issues for the target version, and upgrade agents last.

**Next step:** [Upgrades without drama](48-wazuh-and-security-tools.md#upgrades-without-drama) · [Change management in SRE practice](33-learn-cicd-iac-sre.md#7-sre-practice) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability ([note](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page))

**Community threads:** [GitHub #32044: indexer breaks 4.12 → 4.13](https://github.com/wazuh/wazuh/issues/32044) · [GitHub #33038: remoted crashing](https://github.com/wazuh/wazuh/issues/33038) · [GitHub #32820: modulesd crashing](https://github.com/wazuh/wazuh/issues/32820) · [Google Group: not ready after 4.9 update](https://groups.google.com/g/wazuh/c/z4glUiL-hHs) · Search: [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=upgrade+broke&restrict_sr=1)

---

## 8. CrowdSec and the Traefik bouncer

CrowdSec separates deciding from enforcing. The security engine reads logs (acquisition), parses them, and runs leaky-bucket scenarios. When a scenario overflows, it stores a decision such as "ban 203.0.113.50 for 4 hours" in the Local API (LAPI, `127.0.0.1:8080` by default). Bouncers, also called remediation components, pull those decisions and enforce them: the firewall bouncer on the host, or the Traefik plugin in front of your apps. Most "CrowdSec does nothing" threads end at one of those arrows.

### 8.1 Decisions exist but nothing is blocked

> **Seen as:** `cscli decisions list` shows the attacker's IP with action `ban`, but its requests still reach the app, or nothing is ever banned · **Where:** Traefik on Dokploy with the CrowdSec plugin, or the host firewall bouncer in front of Docker · **Level:** [L1 · Junior] · **How common:** forum topics "Ban not working at all" (about 3,000 views) and "ban only local" (26 replies); plugin issues #120 and #248

**Why it happens:** CrowdSec only decides, and a bouncer must enforce. The common gaps are: no bouncer is registered, or the Traefik middleware is defined but attached to no router; the bouncer cannot reach LAPI, so it never pulls decisions (entry 8.4); simulation mode is on; you are testing from your LAN, and the default `crowdsecurity/whitelists` parser never bans private addresses; or the host firewall bouncer only filters INPUT, while Docker-published ports go through FORWARD.

**Diagnose:**

```bash
sudo cscli decisions list -o raw | head -n 2
sudo cscli bouncers list -o raw
sudo cscli simulation status
sudo grep -n -A3 'middlewares' /etc/dokploy/traefik/traefik.yml || echo "no entrypoint middlewares"
```

```
id,source,ip,reason,action,country,as,events_count,expiration,simulated,alert_id
41237,crowdsec,203.0.113.50,crowdsecurity/http-probing,ban,NL,64500 EXAMPLE-NET,11,3h51m12s,false,812
name,ip,revoked,last_pull,type,version,auth_type
traefik-bouncer,10.0.1.14,false,2026-09-30T08:12:40Z,Crowdsec-Bouncer-Traefik-Plugin,1.x,api-key
global simulation: disabled
no entrypoint middlewares
```

**What the output tells you:** the decision is real and not simulated, but the bouncer last pulled three days ago (go to entry 8.4), and no middleware is attached to the entry point, so routers created by Dokploy never pass through CrowdSec.

**Fix:**

```yaml
# /etc/dokploy/traefik/traefik.yml (static): load the plugin, then add http.middlewares under your EXISTING websecure entry point
experimental:
  plugins:
    crowdsec-bouncer-traefik-plugin:
      moduleName: github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
      version: PLUGIN_VERSION            # pin the latest release tag
entryPoints:
  websecure:
    http:
      middlewares:
        - crowdsec@file
```

```yaml
# /etc/dokploy/traefik/dynamic/crowdsec.yml (dynamic): CrowdSec runs as a container on dokploy-network
http:
  middlewares:
    crowdsec:
      plugin:
        crowdsec-bouncer-traefik-plugin:
          enabled: true
          crowdsecMode: stream
          crowdsecLapiScheme: http
          crowdsecLapiHost: crowdsec:8080
          crowdsecLapiKey: BOUNCER_API_KEY
```

Restart Traefik, then test end to end from a VM outside your network (here 203.0.113.99): `sudo cscli decisions add --ip 203.0.113.99 --duration 10m --reason "bouncer test"`, wait for the next stream refresh (60 seconds by default), then `curl -sI https://app.example.com` from that VM must return 403. Remove the test with `sudo cscli decisions delete --ip 203.0.113.99`. For the host firewall bouncer in front of Docker, set `iptables_chains` to include `DOCKER-USER` in `/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml`.

**Why this fix works:** a middleware on the entry point applies to every router, including the ones Dokploy generates from labels, so no app is forgotten. Stream mode keeps a local copy of decisions in Traefik and refreshes it periodically, so each request does not wait for LAPI. Do not test bans from a private address and conclude CrowdSec is broken: private ranges are whitelisted on purpose.

**Prevent it:** run the synthetic ban test monthly, and alert when a bouncer's `last_pull` is older than five minutes.

**Next step:** [Rate limits, allowlists and WAF](37-learn-security-devsecops.md#rate-limits-allowlists-and-waf) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview · [CrowdSec documentation](https://docs.crowdsec.net/)

**Community threads:** [Forum: Ban not working at all](https://discourse.crowdsec.net/t/ban-not-working-at-all/1311) · [Forum: NPM + CrowdSec (Docker) ban only local](https://discourse.crowdsec.net/t/nginx-proxy-manager-crowdsec-docker-ban-only-local/1638) · [Plugin #120: not blocking banned IPs](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/120) · [Plugin #248: not pulling from the API](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/248) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=crowdsec+traefik+bouncer+not+blocking&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=crowdsec+traefik+bouncer)

### 8.2 Every client shows the same IP

> **Seen as:** Traefik's access log, CrowdSec, Wazuh and Fail2ban all see `10.0.0.2` or `172.18.0.1` as the client for every request; CrowdSec bans that address and everyone is locked out · **Where:** Traefik as a Swarm service with ports in ingress mode, IPv6 clients reaching IPv4-only containers, a CDN or load balancer in front · **Level:** [L2 · Mid] · **How common:** plugin #41 ("clientTrustedIPs seems to block every IP") and #28; a classic Traefik-on-Swarm question

**Why it happens:** Swarm's ingress routing mesh source-NATs incoming connections, so the container sees the mesh address instead of the client's. Docker's userland proxy, used for example when an IPv6 client reaches an IPv4-only container, shows the bridge gateway instead. Behind a CDN or load balancer, the real address is only in `X-Forwarded-For`, and Traefik ignores that header unless the sender is listed in `forwardedHeaders.trustedIPs`. Every security tool downstream inherits the wrong address.

**Diagnose:**

```bash
sudo tail -n 3 /etc/dokploy/traefik/dynamic/access.log | python3 -c 'import sys,json; [print(json.loads(l)["ClientHost"]) for l in sys.stdin]'
docker service inspect dokploy-traefik --format '{{json .Endpoint.Ports}}' 2>/dev/null || docker port dokploy-traefik
```

```
10.0.0.2
10.0.0.2
10.0.0.2
[{"Protocol":"tcp","TargetPort":443,"PublishedPort":443,"PublishMode":"ingress"}]
```

**What the output tells you:** `PublishMode: ingress` means the routing mesh rewrites the source. Every client becomes 10.0.0.2.

**Fix:**

```bash
# Publish 80/443 in host mode so Traefik sees real client addresses (one Traefik per node)
docker service update --publish-rm 443 --publish-add mode=host,published=443,target=443 \
  --publish-rm 80 --publish-add mode=host,published=80,target=80 dokploy-traefik
```

Behind a CDN or load balancer, trust forwarded headers only from it: list its ranges in `entryPoints.websecure.forwardedHeaders.trustedIPs` and in the plugin's `forwardedHeadersTrustedIPs`.

**Why this fix works:** host-mode publishing bypasses the mesh, so packets arrive with their original source. The trade-off is that you lose mesh load balancing and must run Traefik on each node that receives traffic. Trusting `X-Forwarded-For` from everyone would let an attacker pick their own address, dodge bans, or get innocent addresses banned.

**Prevent it:** after every proxy or network change, request a page from a known external address and confirm `ClientHost` in the access log shows it.

**Next step:** [Dokploy, Traefik and Swarm](26-playbook-containers-k8s.md#7-dokploy-traefik-and-swarm) · [Docker Swarm for Dokploy](30-learn-docker.md#14-docker-swarm-for-dokploy) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Swarm Services, Docker Overlay Network) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course))

**Community threads:** [Plugin #41: clientTrustedIPs blocks every IP](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/41) · [Plugin #28: bypassing CrowdSec for local IPs](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/28) · Search: [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=real+ip+swarm&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=traefik+swarm+real+client+ip+ingress)

### 8.3 Logs read but not parsed

> **Seen as:** `cscli metrics` shows thousands of lines read and zero parsed, so no alert ever fires · **Where:** a new acquisition file, CrowdSec in a container, a custom Traefik log path · **Level:** [L1 · Junior] · **How common:** forum topics on parser failures, "Not a standard directory for logs", and how to read the metrics

**Why it happens:** each acquisition source carries a `type` label that selects the parser. If the label says `nginx` for a Traefik log, or the `crowdsecurity/traefik` collection is not installed, every line is unparsed. In Docker, a common cause is that the log file exists on the host but was never mounted into the CrowdSec container, so the path stays empty. An unexpected log format, such as a custom Traefik format, also defeats the parser.

**Diagnose:**

```bash
sudo cscli metrics show acquisition 2>/dev/null || sudo cscli metrics
sudo cscli collections list | grep -iE 'traefik|http'
sudo cscli explain --file /var/log/traefik/access.log --type traefik | tail -n 6
```

```
 Source                             Lines read  Lines parsed  Lines unparsed
 file:/var/log/traefik/access.log   18204       -             18204
 crowdsecurity/http-cve        enabled  ...
```

**What the output tells you:** lines arrive but no Traefik collection is installed (only `http-cve` is listed), so nothing can parse them.

**Fix:**

```bash
sudo cscli collections install crowdsecurity/traefik
printf 'filenames:\n  - /var/log/traefik/access.log\nlabels:\n  type: traefik\n' | sudo tee /etc/crowdsec/acquis.d/traefik.yaml
sudo systemctl reload crowdsec
# Containerised CrowdSec: mount the host log directory read-only, e.g. /etc/dokploy/traefik/dynamic:/var/log/traefik:ro
```

**Why this fix works:** the collection brings the parser and the HTTP scenarios, and the `type` label routes each line to the right parser. `cscli explain` shows every parser stage, so you can see exactly where a line falls out.

**Prevent it:** scrape CrowdSec's Prometheus metrics (port 6060) and alert when the parsed rate of a source drops to zero.

**Next step:** [Docker logging](30-learn-docker.md#6-logging) · KodeKloud: *Docker Certified Associate* — Logging Driver ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · [CrowdSec documentation](https://docs.crowdsec.net/)

**Community threads:** [Forum: parser failures for Caddy logs](https://discourse.crowdsec.net/t/help-with-parser-failures-for-caddy-logs/1361) · [Forum: not a standard directory for logs](https://discourse.crowdsec.net/t/not-a-standard-directory-for-logs/152) · [Forum: how to read the metrics](https://discourse.crowdsec.net/t/question-about-how-to-read-the-metrics/49) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=crowdsec+unparsed+traefik&restrict_sr=1)

### 8.4 LAPI unreachable: port 8080 and keys

> **Seen as:** CrowdSec will not start with `listen tcp 127.0.0.1:8080: bind: address already in use`; `cscli` says `could not get jwt token`; the Traefik plugin logs `crowdsecQuery:unreachable` or returns 403 for everyone · **Where:** busy hosts, CrowdSec installed with apt next to containers, reinstalls · **Level:** [L2 · Mid] · **How common:** forum topics "Could not get jwt token after apt install", "Failed to start the firewall bouncer", "Unable to get crowdsec to start"; plugin #251 and #245

**Why it happens:** LAPI listens on 8080 by default, a port that many other things want (the Traefik dashboard in insecure mode, application containers). Bound to `127.0.0.1`, LAPI is unreachable for a Traefik container, whose `127.0.0.1` is its own loopback. API keys are shown once and change when you reinstall, so bouncers keep presenting the old key and get 403. Multi-server setups add TLS between agents and LAPI, which fails on certificate mismatches.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :8080'
sudo grep -E 'listen_uri' /etc/crowdsec/config.yaml; sudo grep -E '^url' /etc/crowdsec/local_api_credentials.yaml
sudo cscli lapi status
docker logs dokploy-traefik 2>&1 | grep -i crowdsec | tail -n 1
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:(("docker-proxy",pid=3302,fd=4))
    listen_uri: 127.0.0.1:8080
url: http://127.0.0.1:8080/
level=error msg="failed to authenticate to Local API (LAPI): ... connect: connection refused"
... level=error ... crowdsecQuery:unreachable ... plugin=crowdsec-bouncer-traefik-plugin
```

**What the output tells you:** a container already publishes 8080, so LAPI cannot bind it, and even if it could, Traefik could not reach it on loopback.

**Fix:**

```bash
# Move LAPI to a free port and keep every client in sync (config, machine credentials, firewall bouncer)
sudo sed -i 's#listen_uri: 127.0.0.1:8080#listen_uri: 127.0.0.1:8081#' /etc/crowdsec/config.yaml
sudo sed -i 's#^url: .*#url: http://127.0.0.1:8081/#' /etc/crowdsec/local_api_credentials.yaml
sudo sed -i 's#^api_url: .*#api_url: http://127.0.0.1:8081/#' /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml
sudo systemctl restart crowdsec crowdsec-firewall-bouncer && sudo cscli lapi status
# Traefik in Docker: run CrowdSec as a container on dokploy-network (crowdsec:8080), then issue a fresh key
sudo cscli bouncers delete traefik-bouncer; sudo cscli bouncers add traefik-bouncer     # prints the new key once
```

**Why this fix works:** LAPI is the hub that every agent and bouncer authenticates to, so its address and keys must match everywhere. Running CrowdSec on the same Docker network as Traefik avoids exposing LAPI on a host interface at all. Do not bind LAPI to `0.0.0.0` without a firewall rule, because the API would then be exposed to anything that can reach the host, and a leaked bouncer key or machine password would work from anywhere.

**Prevent it:** keep CrowdSec's port in the host's port inventory, store the bouncer key in your secret store (or the container's `BOUNCER_KEY_traefik` variable), and alert on stale bouncer pulls.

**Next step:** [bind: Address already in use](22-playbook-ports-inventory.md#13-scenario-bind-address-already-in-use) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Start, Stop, and Check Status of Network Services ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · [CrowdSec documentation](https://docs.crowdsec.net/)

**Community threads:** [Forum: could not get jwt token after apt install](https://discourse.crowdsec.net/t/could-not-get-jwt-token-after-apt-install/166) · [Forum: failed to start the firewall bouncer](https://discourse.crowdsec.net/t/failed-to-start-the-firewall-bouncer/973) · [Forum: multi-server TLS handshake error](https://discourse.crowdsec.net/t/multi-server-tls-handshake-error/1302) · [Plugin #251: crowdsecQuery unreachable](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/251) · [Plugin #245: 403 Forbidden](https://github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/issues/245)

### 8.5 False positives ban real users

> **Seen as:** users from one office or mobile network get a 403 or the ban page; decisions show `crowdsecurity/http-probing` or a crawl scenario against Nextcloud, Matrix or a sync client · **Where:** apps that legitimately produce many 404 or 403 responses, uptime monitors, CGNAT · **Level:** [L2 · Mid] · **How common:** forum topics on Nextcloud and Kavita false positives, Synapse bans, and exceptions for allowed 404s

**Why it happens:** scenarios are leaky buckets keyed by IP. A WebDAV or sync client probing for files, a single-page app requesting missing assets, or 300 phones behind one carrier NAT can overflow a bucket the same way a scanner does. App-specific collections ship whitelists for these patterns, but only if you install them.

**Diagnose:**

```bash
sudo cscli decisions list --ip 198.51.100.23 -o raw
sudo cscli alerts list --ip 198.51.100.23 -o raw | head -n 3
sudo cscli alerts inspect 812 -d | grep -E 'http_path|http_status' | head -n 5
```

```
id,source,ip,reason,action,country,as,events_count,expiration,simulated,alert_id
41301,crowdsec,198.51.100.23,crowdsecurity/http-probing,ban,...,3h12m4s,false,812
│ http_path   │ /remote.php/dav/files/alice/Photos/2026 │
│ http_status │ 404                                     │
```

**What the output tells you:** the "probing" was a Nextcloud sync client asking WebDAV for folders that do not exist yet.

**Fix:**

```bash
sudo cscli decisions delete --ip 198.51.100.23
sudo cscli collections install crowdsecurity/nextcloud     # app collections include their own whitelists
```

```yaml
# /etc/crowdsec/parsers/s02-enrich/local-whitelist.yaml: narrow exceptions, each with a reason
name: local/office-and-monitoring
description: "Office NAT and uptime monitor are never banned"
whitelist:
  reason: "office NAT (owner: ops) and uptime monitor"
  ip:
    - "198.51.100.23"
  cidr:
    - "10.0.99.0/24"
```

**Why this fix works:** whitelisted events are dropped before they reach a bucket, so they cannot trigger a decision. Prefer the app collection over a broad path whitelist: a path exception such as "anything under /remote.php" is also an exception for attackers. Reload CrowdSec after adding parsers (`sudo systemctl reload crowdsec`).

**Prevent it:** run new or noisy scenarios in simulation first (`sudo cscli simulation enable crowdsecurity/http-probing`), and review the top decisions every week.

**Next step:** [Rate limits, allowlists and WAF](37-learn-security-devsecops.md#rate-limits-allowlists-and-waf) · KodeKloud: *Fundamentals of SRE* — Designing Effective Alerts (the same false-positive budget thinking) · [CrowdSec documentation](https://docs.crowdsec.net/)

**Community threads:** [Forum: false positives with Nextcloud and Kavita](https://discourse.crowdsec.net/t/false-positives-occuring-with-nextcloud-and-ebook-reader-kavita/339) · [Forum: bans from Synapse Matrix requests](https://discourse.crowdsec.net/t/frequent-ip-bans-by-crowdsec-due-to-synapse-matrix-requests-seeking-help-and-solutions/1472) · [Forum: exceptions for allowed 404s](https://discourse.crowdsec.net/t/adding-exceptions-for-allowed-404-errors/764) · [Forum: whitelist by URL portion](https://discourse.crowdsec.net/t/help-with-whitelist-rules-expression-with-portion-of-url/41) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=crowdsec+false+positive&restrict_sr=1)

---

## 9. Fail2ban

Fail2ban is the simplest banning tool: a jail combines a filter (regular expressions), a log source (a file or the systemd journal) and an action (a firewall rule). When an address matches `maxretry` times within `findtime`, it is banned for `bantime`. Put your settings in `/etc/fail2ban/jail.local`, never in `jail.conf`, which package upgrades overwrite. On a Dokploy host, keep Fail2ban for SSH and let CrowdSec handle HTTP at Traefik.

### 9.1 Bans do not stop Docker traffic

> **Seen as:** `fail2ban-client status traefik-auth` lists the attacker as banned, but its requests still reach the site · **Where:** any service published by Docker, including Traefik on Dokploy · **Level:** [L2 · Mid] · **How common:** the official wiki page "Fail2Ban and Docker", fail2ban #3894, and many container-image issues

**Why it happens:** Fail2ban's default chain is INPUT. Traffic to a Docker-published port is DNAT-ed and travels through the FORWARD chain to the container, so it never meets an INPUT rule. On Ubuntu 24.04 the packaged `/etc/fail2ban/jail.d/defaults-debian.conf` sets `banaction = nftables` (and `backend = systemd`), so bans land in the nftables table `inet f2b-table` on the input hook instead of in iptables chains; list them with `sudo nft list table inet f2b-table`. The result for Docker traffic is the same. Running Fail2ban itself in a container adds a second trap: its `iptables` binary may use a different backend (legacy or nft) from the host, which gives `iptables: No chain/target/match by that name`.

**Diagnose:**

```bash
sudo fail2ban-client status traefik-auth | tail -n 3
sudo iptables -S | grep -E 'f2b|DOCKER-USER' | head -n 5
```

```
   |- Currently banned: 3
   |- Total banned:     9
   `- Banned IP list:   203.0.113.50 203.0.113.61 198.51.100.9
-N DOCKER-USER
-N f2b-traefik-auth
-A INPUT -p tcp -m multiport --dports 80,443 -j f2b-traefik-auth
-A FORWARD -j DOCKER-USER
-A DOCKER-USER -j RETURN
```

**What the output tells you:** the ban chain hangs off INPUT, and DOCKER-USER, the chain Docker reserves for your own rules and jumps to from FORWARD, holds no ban rule.

**Fix:**

```ini
# /etc/fail2ban/jail.local
[traefik-auth]
enabled   = true
filter    = traefik-auth
# a file-based jail: override the systemd backend that Ubuntu 24.04 sets in [DEFAULT], or logpath is ignored
backend   = auto
logpath   = /etc/dokploy/traefik/dynamic/access.log
chain     = DOCKER-USER
banaction = iptables-allports
maxretry  = 5
findtime  = 10m
bantime   = 1h
ignoreip  = 127.0.0.1/8 ::1 10.0.99.0/24
```

Apply it with `sudo fail2ban-client reload traefik-auth`. The shipped `traefik-auth` filter expects Traefik's default common log format. If your access log is JSON (for Wazuh and CrowdSec), use the JSON filter from entry 9.3.

**Why this fix works:** DOCKER-USER is evaluated before Docker's own accept rules for forwarded traffic, so a drop there reaches container ports. All-ports banning avoids a subtle trap: after DNAT, the destination port in FORWARD is the container's port, which can differ from the published one. Do not flush Docker's chains or disable Docker's iptables management to make Fail2ban work.

**Prevent it:** test every ban from a real external address. For HTTP, prefer the CrowdSec bouncer inside Traefik, which works at layer 7 whatever the iptables layout.

**Next step:** [Docker bypasses UFW](37-learn-security-devsecops.md#docker-bypasses-ufw) · [Docker: ports, host and firewall](26-playbook-containers-k8s.md#3-docker-ports-host-and-firewall) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — UFW Firewall Basics ([note](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) · [Fail2ban wiki](https://github.com/fail2ban/fail2ban/wiki)

**Community threads:** [Fail2ban wiki: Fail2Ban and Docker](https://github.com/fail2ban/fail2ban/wiki/Fail2Ban-and-Docker) · [fail2ban #3894: DOCKER-USER action not working](https://github.com/fail2ban/fail2ban/issues/3894) · [fail2ban discussion #3600: host Fail2ban for containers](https://github.com/fail2ban/fail2ban/discussions/3600) · [docker-fail2ban #112: failure to add ban rule](https://github.com/crazy-max/docker-fail2ban/issues/112) · Search: [Server Fault](https://serverfault.com/search?q=fail2ban+docker+DOCKER-USER) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=fail2ban+docker+not+banning&restrict_sr=1)

### 9.2 Fail2ban fails to start on Ubuntu 24.04

> **Seen as:** `systemctl status fail2ban` shows `failed`, with `ERROR Failed during configuration: Have not found any log file for sshd jail`, or on early 24.04 installs `ModuleNotFoundError: No module named 'asynchat'` · **Where:** fresh or upgraded Ubuntu 24.04 servers, minimal and cloud images · **Level:** [L1 · Junior] · **How common:** a very common report after 24.04 upgrades (see the search links)

**Why it happens:** with a file backend (the upstream default, the default on Ubuntu 22.04, and what many copied `jail.local` files set with `backend = auto` or `polling`), the sshd jail looks for `/var/log/auth.log`, but minimal and cloud images often log only to the systemd journal, so the file does not exist and the whole service refuses to start. Ubuntu 24.04's own `/etc/fail2ban/jail.d/defaults-debian.conf` already sets `backend = systemd`, so on 24.04 this error almost always means a `jail.local` overrides it. Separately, the Fail2ban package first shipped with 24.04 imported `asynchat`, a module Python 3.12 removed. Updated noble packages fixed that.

**Diagnose:**

```bash
sudo journalctl -u fail2ban -n 20 --no-pager | grep -iE 'error|module' | tail -n 2
ls -l /var/log/auth.log
apt-cache policy fail2ban | sed -n 2,3p
sudo grep -rn '^backend' /etc/fail2ban/jail.d/ /etc/fail2ban/jail.local
```

```
fail2ban-server[1290]: ERROR   Failed during configuration: Have not found any log file for sshd jail
ls: cannot access '/var/log/auth.log': No such file or directory
  Installed: 1.0.2-3ubuntu0.1
  Candidate: 1.0.2-3ubuntu0.1
/etc/fail2ban/jail.d/defaults-debian.conf:4:backend = systemd
/etc/fail2ban/jail.local:3:backend = auto
```

**What the output tells you:** the package is current, so this is the journald case: no auth.log, and a `jail.local` copied from an older server switches the packaged `systemd` backend back to `auto`, so the jail still expects the file.

**Fix:**

```ini
# /etc/fail2ban/jail.local (delete any backend = auto or polling line from [DEFAULT])
[DEFAULT]
ignoreip          = 127.0.0.1/8 ::1 10.0.99.0/24
bantime.increment = true

[sshd]
enabled = true
backend = systemd
```

Then run `sudo apt-get install -y python3-systemd && sudo apt-get install --only-upgrade -y fail2ban`, followed by `sudo systemctl restart fail2ban && sudo fail2ban-client status sshd`.

**Why this fix works:** the systemd backend reads sshd's messages straight from the journal, so no log file is needed. Setting it on the `[sshd]` jail rather than in `[DEFAULT]` keeps file-based jails such as `traefik-auth` (entry 9.1) reading their `logpath`. The package update removes the Python 3.12 incompatibility. `bantime.increment` makes repeat offenders' bans grow each time.

**Prevent it:** manage `jail.local` with configuration management, and monitor `fail2ban-client status`. A Fail2ban that died silently looks exactly like one that is working.

**Next step:** [fail2ban](37-learn-security-devsecops.md#fail2ban) · [journalctl](06-logs-journal.md#1-journalctl-systemd-journal) · KodeKloud: *Learning Linux Basics Course & Labs* — SYSTEMD Tools ([note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) · [Fail2ban wiki](https://github.com/fail2ban/fail2ban/wiki)

**Community threads:** [Fail2ban wiki: Troubleshooting](https://github.com/fail2ban/fail2ban/wiki/Troubleshooting) · [docker-fail2ban #25: stopped working without me knowing](https://github.com/linuxserver/docker-fail2ban/issues/25) · Search: [Stack Overflow](https://stackoverflow.com/search?q=fail2ban+ubuntu+24.04+asynchat) · [Server Fault](https://serverfault.com/search?q=fail2ban+%22Have+not+found+any+log+file+for+sshd+jail%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=fail2ban+24.04&restrict_sr=1)

### 9.3 Filter matches nothing

> **Seen as:** the jail runs, attacks are visible in the log, but `Total failed: 0`; `fail2ban-regex` reports `0 matched` · **Where:** a JSON access log, a custom nginx or app format, logs in UTC with a server in another time zone · **Level:** [L2 · Mid] · **How common:** a classic filter and date mismatch (linuxserver/docker-swag #384, many search results)

**Why it happens:** a failure counts only when the `failregex` matches and the line's timestamp falls within `findtime`. A filter written for the common log format never matches JSON. A date that Fail2ban cannot find, or reads in the wrong time zone, makes the line look old, so it is ignored. A `logpath` inside a container instead of on the host, or a proxy's address instead of the client's in the log, fails just as quietly.

**Diagnose:**

```bash
sudo fail2ban-regex /etc/dokploy/traefik/dynamic/access.log /etc/fail2ban/filter.d/traefik-auth.conf | grep -E '^Lines'
sudo tail -n 1 /etc/dokploy/traefik/dynamic/access.log
```

```
Lines: 5214 lines, 0 ignored, 0 matched, 5214 missed
{"ClientHost":"203.0.113.50","DownstreamStatus":401,"RequestHost":"admin.example.com","RequestMethod":"POST","RequestPath":"/login","StartUTC":"2026-10-03T09:12:44.118Z","time":"2026-10-03T09:12:44Z"}
```

**What the output tells you:** the log is JSON and the filter expects common log format, so 0 of 5214 lines match.

**Fix:**

```ini
# /etc/fail2ban/filter.d/traefik-json-auth.conf
# Traefik writes JSON keys in alphabetical order, so ClientHost comes before DownstreamStatus
[Definition]
failregex   = ^\{.*"ClientHost":"<HOST>".*"DownstreamStatus":40[13],
ignoreregex =
datepattern = "time":"%%Y-%%m-%%dT%%H:%%M:%%S
```

Test it with `sudo fail2ban-regex /etc/dokploy/traefik/dynamic/access.log /etc/fail2ban/filter.d/traefik-json-auth.conf`, which should now report some matched lines. Then set `filter = traefik-json-auth` and `logtimezone = UTC` in the jail and reload it.

**Why this fix works:** the regex now matches the real line shape, and the date pattern plus `logtimezone` place each event at the right moment. `fail2ban-regex` is the only honest test, because a jail that matches nothing raises no error.

**Prevent it:** keep filters, together with a few real sample lines, in Git, and run `fail2ban-regex` against the samples in CI whenever the proxy's log format changes.

**Next step:** [fail2ban](37-learn-security-devsecops.md#fail2ban) · KodeKloud: *Advanced Bash Scripting* — Streams, awk and sed ([course](https://kodekloud.com/courses/advanced-bash-scripting)) · [Fail2ban wiki](https://github.com/fail2ban/fail2ban/wiki)

**Community threads:** [Fail2ban wiki: Troubleshooting](https://github.com/fail2ban/fail2ban/wiki/Troubleshooting) · [docker-swag #384: fail2ban not banning](https://github.com/linuxserver/docker-swag/issues/384) · Search: [Stack Overflow](https://stackoverflow.com/search?q=fail2ban-regex+0+matched+json) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=fail2ban+traefik+json&restrict_sr=1)

---

## 10. Trivy and image scanning

Trivy scans container images, filesystems, Git repositories and Kubernetes clusters for known vulnerabilities, misconfigurations and leaked secrets. It downloads a vulnerability database (an OCI artifact) and scans locally. You meet it in two places: as a job in GitLab CI, and as the scanner built into Harbor. Most of its problems come from the database download, from trust in your private registry, and from turning findings into a sensible pipeline gate.

### 10.1 TOOMANYREQUESTS downloading the DB

> **Seen as:** `FATAL ... failed to download vulnerability DB: ... TOOMANYREQUESTS: retry-after: ..., allowed: 44000/minute`; Harbor scans fail in bursts · **Where:** CI runners behind one NAT address, Harbor's Trivy adapter, many parallel jobs · **Level:** [L2 · Mid] · **How common:** Trivy discussion #7668 ("Solve once for all the TOOMANYREQUESTS issues") plus several related threads and Harbor issues #21163 and #20961

**Why it happens:** every job without a cache downloads the database again from the registry, and all your runners share one public address. When the registry rate-limits that address, every scan fails at once. The Java database (for JAR scanning) is a second download with the same problem.

**Diagnose:**

```bash
trivy image --debug alpine:3.20 2>&1 | grep -iE 'vulndb|toomanyrequests' | head -n 3
```

```
2026-10-03T07:12:01Z INFO  [vulndb] Need to update DB
2026-10-03T07:12:01Z INFO  [vulndb] Downloading vulnerability DB...
2026-10-03T07:12:02Z FATAL Fatal error  run error: init error: DB error: failed to download vulnerability DB: ... TOOMANYREQUESTS: retry-after: 412.1µs, allowed: 44000/minute
```

**What the output tells you:** the scan never started. The download was refused, and the cause is shared egress plus no cache, not your image.

**Fix:**

```bash
# Use mirrors in order of preference, so Trivy falls back when one is rate-limited
trivy image --db-repository mirror.gcr.io/aquasec/trivy-db:2,ghcr.io/aquasecurity/trivy-db:2,public.ecr.aws/aquasecurity/trivy-db:2 \
  --java-db-repository mirror.gcr.io/aquasec/trivy-java-db:1,ghcr.io/aquasecurity/trivy-java-db:1 \
  harbor.example.com/shop/api:1.4.2
```

```yaml
# .gitlab-ci.yml: cache the DB between jobs
trivy-scan:
  image:
    name: aquasec/trivy:TRIVY_VERSION
    entrypoint: [""]
  variables:
    TRIVY_CACHE_DIR: .trivycache/
    TRIVY_NO_PROGRESS: "true"
  cache:
    key: trivy-db
    paths: [.trivycache/]
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Why this fix works:** caching turns N downloads per day into roughly one, and the mirror list removes the single point of rate-limiting. Recent Trivy releases already prefer `mirror.gcr.io`, so upgrading Trivy alone often solves it. For air-gapped sites, mirror the database artifact into Harbor and point `--db-repository` at it.

**Prevent it:** pin and regularly update the Trivy version, cache the database in every pipeline, and run one scheduled job that refreshes it.

**Next step:** [Image scanning with Trivy](37-learn-security-devsecops.md#image-scanning-with-trivy) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [Trivy documentation](https://trivy.dev/)

**Community threads:** [Trivy discussion #7668: TOOMANYREQUESTS](https://github.com/aquasecurity/trivy/discussions/7668) · [Trivy discussion #7641: blocked by rate limiter](https://github.com/aquasecurity/trivy/discussions/7641) · [trivy-action #389](https://github.com/aquasecurity/trivy-action/issues/389) · [Harbor #21163: overriding DB repositories](https://github.com/goharbor/harbor/issues/21163) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=trivy+toomanyrequests&restrict_sr=1)

### 10.2 x509 errors scanning Harbor images

> **Seen as:** `tls: failed to verify certificate: x509: certificate signed by unknown authority` when scanning `harbor.example.com/...`, even though `docker pull` works on the same host · **Where:** GitLab jobs and admin laptops scanning images in a Harbor that uses your private CA · **Level:** [L2 · Mid] · **How common:** the private-CA registry problem is one of the most common CI failures (see handbook 37)

**Why it happens:** Trivy talks to the registry itself, using Go's TLS stack, which trusts the operating system bundle or whatever `SSL_CERT_FILE` and `SSL_CERT_DIR` point to. `/etc/docker/certs.d/` is read only by the Docker daemon, so `docker pull` works while Trivy fails. In CI, the job image (`aquasec/trivy`) contains none of your CAs. A second trap: pointing `SSL_CERT_FILE` at a file holding only your private CA fixes Harbor and breaks every public registry.

**Diagnose:**

```bash
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer
trivy image --debug harbor.example.com/shop/api:1.4.2 2>&1 | grep -iE 'x509|unauthorized' | head -n 1
```

```
issuer=CN = Example Internal Root CA 2026
... Get "https://harbor.example.com/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
```

**What the output tells you:** the certificate comes from your internal CA, and Trivy's trust store does not contain it.

**Fix:**

```bash
# Host or runner: add the CA to the system bundle (Go reads it)
sudo cp example-root-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates
# CI job: give Trivy a FULL bundle (public CAs + yours) and a Harbor robot account with pull rights only
export SSL_CERT_FILE="$CA_BUNDLE_FILE"            # GitLab "File" variable: system bundle with your root CA appended
export TRIVY_USERNAME='robot$shop+scanner'
export TRIVY_PASSWORD="$HARBOR_ROBOT_TOKEN"
trivy image harbor.example.com/shop/api:1.4.2
```

**Why this fix works:** Trivy now verifies Harbor's chain like any other public site, and a robot account limits what a leaked CI token can do. Do not add `--insecure`: it disables certificate checks for the registry, which is exactly what an attacker on the path needs.

**Prevent it:** build CI base images with the company CA already installed, and follow one CA distribution runbook for hosts, Docker, containerd and CI.

**Next step:** [Distributing trust: hosts, Docker, containerd](37-learn-security-devsecops.md#distributing-trust-hosts-docker-containerd) · [Harbor scanning and policies](37-learn-security-devsecops.md#harbor-scanning-and-policies) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Work With SSL Certificates · [Harbor documentation](https://goharbor.io/docs/)

**Community threads:** [GitHub search: trivy x509 unknown authority](https://github.com/aquasecurity/trivy/issues?q=x509+unknown+authority) · Search: [Stack Overflow](https://stackoverflow.com/search?q=trivy+x509+certificate+signed+by+unknown+authority) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=trivy+private+registry+certificate&restrict_sr=1)

### 10.3 Pipeline blocked by unfixable CVEs

> **Seen as:** `Total: 23 (HIGH: 19, CRITICAL: 4)` and exit code 1 on a commit that changed nothing; developers ask to remove the scan · **Where:** GitLab CI gates that fail on every finding · **Level:** [L2 · Mid] · **How common:** a recurring DevSecOps argument on every forum (see the search links)

**Why it happens:** new CVEs are published every day, so an unchanged image can fail tomorrow. Many findings have no fixed package yet, so neither developers nor ops can act on them. A gate that fails on everything trains people to ignore it or to bypass it.

**Diagnose:**

```bash
trivy image --severity HIGH,CRITICAL --quiet harbor.example.com/shop/api:1.4.2 | grep -E '^Total'
trivy image --severity HIGH,CRITICAL --ignore-unfixed --quiet harbor.example.com/shop/api:1.4.2 | grep -E '^Total'
```

```
Total: 23 (HIGH: 19, CRITICAL: 4)
Total: 3 (HIGH: 2, CRITICAL: 1)
```

**What the output tells you:** only three findings can be fixed today, and those three are what the gate should stop on.

**Fix:**

```yaml
# .trivyignore.yaml: every exception has a reason, an owner and an expiry date
vulnerabilities:
  - id: CVE_ID
    statement: "Not reachable: the service never parses untrusted archives (owner: ops, ticket OPS-412)"
    expired_at: 2026-12-31
```

Gate with `trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed --ignorefile .trivyignore.yaml "$IMAGE"`, and rebuild images on fresh base images every week so fixed packages actually arrive.

**Why this fix works:** the gate now fails only on findings someone can fix, and accepted risks expire instead of hiding forever. Unfixed findings still appear in the full report and in Harbor's scan results, so they are visible without blocking delivery.

**Prevent it:** schedule weekly base-image rebuilds (for example with Renovate), review the exception file monthly, and track the number of open fixable findings per service.

**Next step:** [Pipeline: scan, sign, deploy](37-learn-security-devsecops.md#pipeline-scan-sign-deploy) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — Supply Chain Security ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · [Trivy documentation](https://trivy.dev/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=trivy+ignore-unfixed+exit-code+gitlab) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=trivy+gate+unfixed+cve&restrict_sr=1) · [GitHub search: trivyignore expired_at](https://github.com/aquasecurity/trivy/issues?q=trivyignore+expired_at)

---

## 11. Vault and OpenBao

Vault and its open-source fork OpenBao (CLI `bao`, same concepts and mostly the same commands) serve secrets over an API on 8200/tcp, while cluster nodes talk on 8201/tcp. Data is encrypted at rest, and the key that unlocks it is protected by a **seal**. Integrated **raft** storage replicates data between nodes, and **audit devices** log every request. Each of those three pieces has a classic failure.

### 11.1 Sealed after every restart

> **Seen as:** apps fail with `Code: 503. Errors: * Vault is sealed` after a reboot or a container update; in Docker, startup can also fail with `Failed to lock memory: cannot allocate memory` · **Where:** Vault or OpenBao with the default Shamir seal, often single-node in Docker · **Level:** [L2 · Mid] · **How common:** several HashiCorp Discuss threads ("Vault is sealed and unable to unseal it", "sealed after post-unseal setup failed") and GitHub #5593

**Why it happens:** with the Shamir seal, the key that decrypts Vault's data exists only in memory. Every restart (a reboot, a recreated container, an OOM kill) seals Vault until enough key holders run `vault operator unseal`. That is the design, not a bug, but without auto-unseal a 3 a.m. restart means an outage until people wake up. In containers, Vault also tries to lock its memory, which fails without the `IPC_LOCK` capability unless `disable_mlock = true` is set. HashiCorp recommends that setting with integrated storage.

**Diagnose:**

```bash
export VAULT_ADDR=https://vault.example.com:8200
vault status; echo "exit=$?"
docker inspect vault --format 'started={{.State.StartedAt}} restarts={{.RestartCount}}'
```

```
Seal Type          shamir
Sealed             true
Threshold          3
Unseal Progress    0/3
Storage Type       raft
exit=2
started=2026-10-03T03:12:44Z restarts=1
```

**What the output tells you:** Vault restarted at 03:12 and has been sealed ever since. Exit code 2 means "sealed", which makes it easy to monitor.

**Fix:**

```bash
# Now: three key holders each run this and paste their own share at the prompt
vault operator unseal
```

```hcl
# Afterwards: auto-unseal through a small separate Vault (transit), then run the documented seal migration once
seal "transit" {
  address     = "https://vault-unsealer.example.com:8200"
  key_name    = "autounseal"
  mount_path  = "transit/"
  tls_ca_cert = "/vault/config/ca.pem"
}
disable_mlock = true    # with integrated storage; otherwise run the container with --cap-add IPC_LOCK
```

**Why this fix works:** auto-unseal moves the root of trust to another system (a second Vault, a cloud KMS or an HSM), so a restarted node unseals itself and no unseal key ever sits in a config file. The transit token comes from the environment, not the file. OpenBao uses the same seal stanzas.

**Prevent it:** keep an unseal runbook with named key holders, alert when `vault status` exits with 2, and never store unseal keys on the Vault host.

**Next step:** [HashiCorp Vault](37-learn-security-devsecops.md#hashicorp-vault) · [Secrets management](33-learn-cicd-iac-sre.md#6-secrets-management) · KodeKloud: the verified map has no Vault course, so use the [Vault documentation](https://developer.hashicorp.com/vault/docs) and the [OpenBao documentation](https://openbao.org/docs/)

**Community threads:** [Discuss: Vault is sealed and unable to unseal it](https://discuss.hashicorp.com/t/vault-is-sealed-and-unable-to-unseal-it/71604) · [Discuss: sealed after post-unseal setup failed](https://discuss.hashicorp.com/t/vault-is-sealed-after-post-unseal-setup-failed/32236) · [Discuss: Vault is sealed for API call](https://discuss.hashicorp.com/t/vault-is-sealed-for-api-call/24990) · [GitHub #5593: sealed randomly](https://github.com/hashicorp/vault/issues/5593) · [Vault docs: status command](https://developer.hashicorp.com/vault/docs/commands/status)

### 11.2 Permission denied on KV v2 secrets

> **Seen as:** `vault kv get secret/app/db` returns `Code: 403. Errors: * permission denied`, although the policy says `path "secret/app/*"` · **Where:** the first policies anyone writes for a KV version 2 engine · **Level:** [L2 · Mid] · **How common:** a classic first-week Vault question (see the search links)

**Why it happens:** KV version 2 keeps versions and metadata, so its API paths gain a segment. The CLI command `vault kv get secret/app/db` really reads `secret/data/app/db`, and listing uses `secret/metadata/app/`. A policy written for `secret/app/*` matches neither path.

**Diagnose:**

```bash
vault token lookup -format=json | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"]["policies"])'
vault kv get -output-curl-string secret/app/db
vault token capabilities secret/data/app/db
```

```
['default', 'app-read']
curl -H "X-Vault-Request: true" -H "X-Vault-Token: $(vault print token)" https://vault.example.com:8200/v1/secret/data/app/db
deny
```

**What the output tells you:** the token holds `app-read`, the real path contains `data/`, and capabilities on that path are `deny`.

**Fix:**

```hcl
# app-read.hcl, then: vault policy write app-read app-read.hcl
path "secret/data/app/*" {
  capabilities = ["read"]
}
path "secret/metadata/app/*" {
  capabilities = ["read", "list"]
}
```

**Why this fix works:** policies match API paths, not CLI shorthand. Policy changes apply to existing tokens immediately, because Vault evaluates policies on every request. Do not "fix" it by attaching the `root` policy or a `secret/*` wildcard to an application token.

**Prevent it:** write policies as code and test each one with `vault token capabilities PATH` in CI before applying it.

**Next step:** [Secrets never in Git](37-learn-security-devsecops.md#secrets-never-in-git) · [GitLab CI variables](37-learn-security-devsecops.md#gitlab-ci-variables) · KodeKloud: the verified map has no Vault course · [Vault documentation](https://developer.hashicorp.com/vault/docs)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=vault+kv+v2+permission+denied+policy+data) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=vault+kv2+permission+denied&restrict_sr=1) · [GitHub search: kv v2 permission denied](https://github.com/hashicorp/vault/issues?q=kv+v2+permission+denied)

### 11.3 Raft node cannot join the cluster

> **Seen as:** `vault operator raft join` fails with `failed to join raft cluster`, or the node joins but stays sealed; logs show `x509: certificate is valid for vault-1.example.com, not 10.0.30.11` · **Where:** building a three-node Vault or OpenBao cluster · **Level:** [L3 · Senior] · **How common:** GitHub #25360 ("nodes join, but cant unseal") and #9618

**Why it happens:** a joining node calls the leader's API over TLS (8200), then replicates over the cluster port (8201). It fails when the leader's certificate does not list the address the joiner used, when the joiner does not trust the leader's CA, when 8201 is blocked, or when `api_addr` and `cluster_addr` advertise an address other nodes cannot reach, such as `0.0.0.0` or a container IP. With Shamir, a joined node must still be unsealed on its own.

**Diagnose:**

```bash
vault operator raft list-peers
nc -vz vault-1.example.com 8201
sudo grep -E 'api_addr|cluster_addr|leader_api_addr|leader_ca_cert' /etc/vault.d/vault.hcl
```

```
Node       Address             State     Voter
----       -------             -----     -----
vault-1    10.0.30.11:8201     leader    true
vault-2    10.0.30.12:8201     follower  true
nc: connect to vault-1.example.com port 8201 (tcp) failed: Connection timed out
api_addr = "https://0.0.0.0:8200"
```

**What the output tells you:** the cluster port is blocked from this node, and the node advertises `0.0.0.0`, which nobody can connect to.

**Fix:**

```hcl
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "vault-3"
  retry_join {
    leader_api_addr     = "https://vault-1.example.com:8200"
    leader_ca_cert_file = "/etc/vault.d/tls/ca.pem"
  }
}
api_addr     = "https://vault-3.example.com:8200"
cluster_addr = "https://vault-3.example.com:8201"
```

Open 8201/tcp between the Vault nodes only, issue certificates whose SANs contain the names you use, restart, and unseal the new node.

**Why this fix works:** `retry_join` keeps trying with a CA it trusts, and the advertised addresses are now reachable names that appear in the certificates. Three or five voters keep a quorum through one or two node losses.

**Prevent it:** take regular `vault operator raft snapshot save` backups, monitor the peer list, and rehearse replacing a node.

**Next step:** [mTLS](37-learn-security-devsecops.md#mtls) · [Certificates, chains and trust](37-learn-security-devsecops.md#certificates-chains-and-trust) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — TLS Basics ([note](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) · [Vault documentation](https://developer.hashicorp.com/vault/docs)

**Community threads:** [GitHub #25360: nodes join, but cannot unseal](https://github.com/hashicorp/vault/issues/25360) · [GitHub #9618: not initialized but is initialized](https://github.com/hashicorp/vault/issues/9618) · Search: [Stack Overflow](https://stackoverflow.com/search?q=vault+raft+join+failed+x509)

### 11.4 Audit log disk full blocks every request

> **Seen as:** every Vault request suddenly fails with a 500, and the server log shows `failed to audit request` with `no space left on device` · **Where:** a file audit device on a small disk, logrotate without a reload · **Level:** [L3 · Senior] · **How common:** a well-known operational trap (see the search links)

**Why it happens:** Vault refuses to answer a request it cannot audit. If every enabled audit device fails, nothing is served. That is deliberate: no unaudited access to secrets. A full disk, or a logrotate rule that renames the file without telling Vault (so Vault keeps writing to the deleted file and the space is never freed), turns this into an outage.

**Diagnose:**

```bash
vault audit list -detailed
df -h /var/log/vault
sudo lsof +L1 2>/dev/null | grep -i vault | head -n 2
```

```
Path      Type    Description    Replication    Options
file/     file    n/a            replicated     file_path=/var/log/vault/audit.log
Filesystem  Size  Used Avail Use% Mounted on
/dev/sdb1   20G   20G     0 100% /var/log/vault
vault  912 vault  7w  REG  8,17  9663676416  0  131 /var/log/vault/audit.log.1 (deleted)
```

**What the output tells you:** one file device only, the disk is full, and 9 GB are held by a deleted file that Vault still has open.

**Fix:**

```bash
sudo systemctl reload vault                       # SIGHUP: Vault reopens its audit file and the deleted one is released
vault audit enable -path=syslog-audit syslog tag="vault" facility="AUTH"   # a second device, so one failure is survivable
```

Add `postrotate` with `systemctl reload vault` to the logrotate rule for `/var/log/vault/audit.log`.

**Why this fix works:** with two devices, Vault answers as long as at least one of them can write. The reload makes rotation actually free space. Ship the JSON audit log to Wazuh with a `localfile` block, because who read which secret is exactly what you want in your SIEM.

**Prevent it:** give the audit log its own volume, alert at 75% disk, and rotate it with a reload.

**Next step:** [Disk space usage](01-storage-disk.md#1-disk-space-usage) · [Log rotation issues](06-logs-journal.md#5-log-rotation-issues) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Locate and Analyze System Log Files · [Vault documentation](https://developer.hashicorp.com/vault/docs)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=vault+audit+log+disk+full+requests+fail) · [Server Fault](https://serverfault.com/search?q=vault+audit+device+blocked) · [GitHub search: failed to audit request](https://github.com/hashicorp/vault/issues?q=%22failed+to+audit+request%22)

---

## 12. Keycloak

Keycloak (26.x, built on Quarkus) is a full identity and access management server: OIDC and SAML, user federation, MFA, fine-grained clients. In production it runs with `kc.sh start` (never `start-dev`) against PostgreSQL. It serves HTTP on 8080 behind a TLS-terminating proxy, and exposes health and metrics on a separate management port, 9000. Almost every problem below comes from the proxy, the database or that management port.

### 12.1 HTTPS required and wrong redirects behind Traefik

> **Seen as:** `We are sorry... HTTPS required` on the admin login; redirects to `http://auth.example.com:8080/...`; `Invalid parameter: redirect_uri`; the admin console stuck on "Loading the Admin UI" · **Where:** Keycloak in Docker behind Traefik or Dokploy · **Level:** [L2 · Mid] · **How common:** keycloak discussion #13459 ("Cannot access admin console behind traefik proxy"), issue #14452, and a forum thread on reverse-proxying with Traefik

**Why it happens:** Keycloak builds every URL it hands out (issuer, redirects, admin console assets) from what it believes its public address is. Behind Traefik it sees plain HTTP from a container IP unless you tell it to trust the `X-Forwarded-*` headers (`KC_PROXY_HEADERS=xforwarded`) and give it its public URL (`KC_HOSTNAME`). With TLS terminated at Traefik, Keycloak's HTTP listener must also be enabled. The master realm refuses plain HTTP from non-local addresses, hence "HTTPS required". Clients whose redirect URIs do not exactly match the real HTTPS URL produce `Invalid parameter: redirect_uri`.

**Diagnose:**

```bash
curl -s https://auth.example.com/realms/master/.well-known/openid-configuration | python3 -m json.tool | grep -E '"issuer"'
docker exec keycloak env | grep -E '^KC_(HOSTNAME|PROXY|HTTP)'
```

```
    "issuer": "http://auth.example.com/realms/master",
KC_HTTP_ENABLED=true
```

**What the output tells you:** the issuer is `http://`, so Keycloak does not know it is served over HTTPS, and neither `KC_HOSTNAME` nor `KC_PROXY_HEADERS` is set.

**Fix:**

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:KEYCLOAK_VERSION    # pin a 26.x (or newer) tag
    command: start
    environment:
      KC_HOSTNAME: https://auth.example.com
      KC_PROXY_HEADERS: xforwarded
      KC_HTTP_ENABLED: "true"
      KC_HEALTH_ENABLED: "true"
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: ${KC_DB_PASSWORD}
    labels:
      - traefik.enable=true
      - traefik.http.routers.keycloak.rule=Host(`auth.example.com`)
      - traefik.http.routers.keycloak.entrypoints=websecure
      - traefik.http.routers.keycloak.tls.certresolver=letsencrypt
      - traefik.http.services.keycloak.loadbalancer.server.port=8080
```

**Why this fix works:** Keycloak now derives HTTPS URLs from the trusted headers and its configured hostname, so the issuer, redirects and admin console assets all agree. Traefik sets `X-Forwarded-Proto` and `X-Forwarded-Host` itself and ignores those headers from untrusted clients. Do not set the master realm's "Require SSL" to `none`. It makes the error disappear by sending admin passwords in clear text.

**Prevent it:** check the discovery document's `issuer` after every proxy change, and register exact HTTPS redirect URIs per client instead of wildcards.

**Next step:** [Traefik in depth](29-learn-webservers-proxies.md#4-traefik-in-depth) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · KodeKloud: *Nginx For Beginners* — Security, HTTPS ([note](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Security/HTTPS/page)) · [Keycloak documentation](https://www.keycloak.org/documentation)

**Community threads:** [Discussion #13459: admin console behind Traefik](https://github.com/keycloak/keycloak/discussions/13459) · [Issue #14452: hostname-admin broken behind a reverse proxy](https://github.com/keycloak/keycloak/issues/14452) · [Forum: reverse proxy Keycloak with Traefik](https://forum.keycloak.org/t/struggling-to-reverse-proxy-keycloak-with-traefik/30197) · [Keycloak guide: Traefik with TLS passthrough](https://www.keycloak.org/server/traefik-passthrough) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=keycloak+traefik+https+required&restrict_sr=1)

### 12.2 Startup stuck on the database lock

> **Seen as:** Keycloak hangs at start with `Waiting for changelog lock....`, then fails with `Could not acquire change log lock. Currently locked by ...` · **Where:** right after an upgrade, or after the container was killed during its first start on a new version · **Level:** [L3 · Senior] · **How common:** a classic upgrade problem (see the search links); keycloak discussion #24655 asks for smoother upgrades

**Why it happens:** on a new version, Keycloak migrates the database schema on start and holds a row lock in the `databasechangeloglock` table while it does. If the container is killed mid-migration (an OOM kill, a healthcheck that restarts it too early, two replicas starting at once), the lock row stays "locked" and every later start waits for an owner that no longer exists.

**Diagnose:**

```bash
docker logs keycloak 2>&1 | grep -iE 'changelog lock|liquibase' | tail -n 2
docker exec keycloak-db psql -U keycloak -d keycloak -c 'SELECT id, locked, lockgranted, lockedby FROM databasechangeloglock;'
```

```
 id | locked |       lockgranted       |        lockedby
----+--------+-------------------------+--------------------------
  1 | t      | 2026-10-03 03:12:41.512 | 7c1e9d0a2b44 (10.0.40.7)
```

**What the output tells you:** a container that no longer exists took the lock at 03:12.

**Fix:**

```bash
docker compose stop keycloak                                       # 1. make sure NO instance runs
docker exec keycloak-db pg_dump -U keycloak -Fc keycloak > keycloak-$(date +%F).dump    # 2. backup
docker exec keycloak-db psql -U keycloak -d keycloak -c "UPDATE databasechangeloglock SET locked=false, lockgranted=NULL, lockedby=NULL WHERE id=1;"
docker compose up -d keycloak && docker logs -f keycloak           # 3. ONE instance migrates
```

**Why this fix works:** the lock protects the schema from two migrations running at once. Releasing it is safe only when you are certain no instance is running. A long healthcheck start period lets the migration finish instead of being killed again.

**Prevent it:** back up the database before every upgrade, run a single replica while migrating, and give the healthcheck a `start_period` of several minutes.

**Next step:** [Databases ops](38-learn-databases-ops.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [Keycloak documentation](https://www.keycloak.org/documentation)

**Community threads:** [Discussion #24655: future of seamless upgrades](https://github.com/keycloak/keycloak/discussions/24655) · [Discussion #25750: PostgreSQL database privileges](https://github.com/keycloak/keycloak/discussions/25750) · Search: [Stack Overflow](https://stackoverflow.com/search?q=keycloak+%22could+not+acquire+change+log+lock%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=keycloak+changelog+lock&restrict_sr=1)

### 12.3 Health checks fail after upgrading

> **Seen as:** after an upgrade the container is marked unhealthy and restarted in a loop; `GET /health/ready` on 8080 returns 404; the healthcheck output says `exec: "curl": executable file not found` · **Where:** compose or Swarm healthchecks written for older Keycloak versions · **Level:** [L2 · Mid] · **How common:** common after the management-interface change (see the search links)

**Why it happens:** recent Keycloak versions serve `/health` and `/metrics` on the management port 9000, not on 8080, and only when `KC_HEALTH_ENABLED=true`. The official image is minimal and contains no `curl` or `wget`, so a copied `curl` healthcheck fails even on the right port. A restart loop during a migration can then also cause entry 12.2.

**Diagnose:**

```bash
docker inspect keycloak --format '{{json .State.Health.Log}}' | python3 -c 'import sys,json; print(json.load(sys.stdin)[-1]["Output"][:120])'
docker exec keycloak bash -c 'exec 3<>/dev/tcp/127.0.0.1/9000; printf "GET /health/ready HTTP/1.0\r\n\r\n" >&3; head -n 1 <&3'
```

```
OCI runtime exec failed: exec failed: unable to start container process: exec: "curl": executable file not found
HTTP/1.0 200 OK
```

**What the output tells you:** Keycloak is healthy on 9000. Only the healthcheck command is broken.

**Fix:**

```yaml
    healthcheck:
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/127.0.0.1/9000 && printf 'GET /health/ready HTTP/1.0\\r\\n\\r\\n' >&3 && head -n 1 <&3 | grep -q ' 200'"]
      interval: 15s
      timeout: 5s
      retries: 10
      start_period: 180s
```

**Why this fix works:** bash's `/dev/tcp` needs no extra binary, port 9000 is where the readiness endpoint lives, and the start period covers migrations. Do not publish 9000 through Traefik: metrics and health belong on the internal network only.

**Prevent it:** read the upgrade notes for every Keycloak release you skip, and test the healthcheck in staging before production.

**Next step:** [Containers that will not stay up](26-playbook-containers-k8s.md#2-docker-containers-that-will-not-stay-up) · KodeKloud: *Docker Certified Associate* — Restart Policies ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)) · [Keycloak documentation](https://www.keycloak.org/documentation)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=keycloak+health+ready+9000+404) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=keycloak+healthcheck+curl&restrict_sr=1) · [GitHub search: healthcheck curl](https://github.com/keycloak/keycloak/issues?q=healthcheck+curl)

---

## 13. Authentik

Authentik runs as a **server** (web UI, API and the embedded outpost on 9000/9443), a **worker** (background tasks such as blueprints, outpost updates and email), and PostgreSQL. For apps without SSO support, Traefik's `forwardAuth` middleware asks the outpost whether each request is allowed, and the browser completes the login through `/outpost.goauthentik.io/` on the app's own host name. Releases use calendar versions (2025.x, 2026.x), and server and worker must always run the same one.

### 13.1 Forward auth returns 404 on the outpost path

> **Seen as:** after logging in, the browser lands on `https://app.example.com/outpost.goauthentik.io/callback?...` and gets `404 page not found` · **Where:** a new app protected by Traefik forward auth · **Level:** [L2 · Mid] · **How common:** authentik #8956 ("path /outpost.goauthentik.io not found", 54 comments), #9122, #2180 and #4510

**Why it happens:** forward auth uses two separate paths. The middleware's check (Traefik to the outpost) works as soon as the address is right. The browser's callback, though, goes to `/outpost.goauthentik.io/` on the app's host, and Traefik routes that only if a router sends that path to authentik. The other classic gap is a provider that was never added to the embedded outpost, so the outpost answers 404 for that host.

**Diagnose:**

```bash
curl -sI https://app.example.com/ | grep -iE '^(HTTP|location)'
curl -sI "https://app.example.com/outpost.goauthentik.io/start?rd=https://app.example.com/" | head -n 1
```

```
HTTP/2 302
location: https://app.example.com/outpost.goauthentik.io/start?rd=https%3A%2F%2Fapp.example.com%2F
HTTP/2 404
```

**What the output tells you:** the middleware works (it redirects to the outpost path), but nothing on `app.example.com` routes that path to authentik.

**Fix:**

```yaml
# Labels on the authentik server container: send the outpost path of every protected host to authentik
- traefik.enable=true
- traefik.http.routers.authentik-outpost.rule=HostRegexp(`^.+\.example\.com$`) && PathPrefix(`/outpost.goauthentik.io/`)
- traefik.http.routers.authentik-outpost.priority=100
- traefik.http.routers.authentik-outpost.entrypoints=websecure
- traefik.http.routers.authentik-outpost.tls.certresolver=letsencrypt
- traefik.http.services.authentik.loadbalancer.server.port=9000
```

```yaml
# /etc/dokploy/traefik/dynamic/authentik.yml: the shared middleware your app routers reference as authentik@file
http:
  middlewares:
    authentik:
      forwardAuth:
        address: http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders: [X-authentik-username, X-authentik-groups, X-authentik-email, X-authentik-uid]
```

In the authentik admin UI, add the application's proxy provider to the **authentik Embedded Outpost**.

**Why this fix works:** the high-priority router catches the callback path on every protected host before the app's own router does, and the outpost then knows the provider for that host. The Traefik v3 rule syntax uses plain regular expressions in `HostRegexp`; v2-style `{name:...}` placeholders no longer work.

**Prevent it:** after protecting each new app, run the two `curl` checks above as a smoke test.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Closing admin endpoints](37-learn-security-devsecops.md#closing-admin-endpoints) · KodeKloud: *Kubernetes Networking Deep Dive* — Ingress (Traefik) · [authentik documentation](https://docs.goauthentik.io/)

**Community threads:** [authentik #8956: outpost path not found](https://github.com/goauthentik/authentik/issues/8956) · [authentik #9122: embedded outpost 404](https://github.com/goauthentik/authentik/issues/9122) · [authentik #2180: forward auth in Traefik/Docker](https://github.com/goauthentik/authentik/issues/2180) · [authentik #4510: proxy provider not working](https://github.com/goauthentik/authentik/issues/4510) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=authentik+outpost+404+traefik&restrict_sr=1)

### 13.2 Login loops or lands on authentik

> **Seen as:** after a successful login the browser bounces between the app and authentik, or ends on authentik's own user page instead of the app; the admin UI shows `CSRF Failed: Origin checking failed`; some users see "Request has been denied" · **Where:** forward auth in domain mode, authentik behind more than one proxy, hosts with clock drift · **Level:** [L2 · Mid] · **How common:** authentik #1997 ("forward auth redirecting to authentik instead of app", 43 comments), #8127 and #2023

**Why it happens:** the redirect back to the app is built from the provider's external host and the forwarded headers. An external host with `http` instead of `https`, or a different host name, sends the browser somewhere else. Domain-mode forward auth needs a cookie domain that covers every app. When authentik sits behind a proxy whose headers it does not trust, it sees the wrong scheme and origin, which causes the CSRF failure. Clock drift invalidates sessions straight away. "Request has been denied" is not a loop at all: a policy bound to the application rejected the user.

**Diagnose:**

```bash
curl -sI "https://app.example.com/outpost.goauthentik.io/start?rd=https://app.example.com/" | grep -i '^location'
docker logs authentik-server 2>&1 | grep -iE 'csrf|origin' | tail -n 2
timedatectl | grep -E 'synchronized'
```

```
location: https://auth.example.com/application/o/authorize/?client_id=...&redirect_uri=http%3A%2F%2Fapp.example.com%2Foutpost.goauthentik.io%2Fcallback...
System clock synchronized: yes
```

**What the output tells you:** the callback URL uses `http://`, so the provider's external host is wrong. The clock is fine.

**Fix:** set the provider's external host to exactly `https://app.example.com`, and in domain mode set the cookie domain to `example.com`. Then tell authentik which proxies it may trust and recreate the containers:

```yaml
    environment:
      AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS: "10.0.1.0/24,172.16.0.0/12"   # your Docker/Traefik networks only
```

**Why this fix works:** with the right external host, the callback lands on the app's HTTPS origin, and trusted proxy ranges let authentik believe the scheme and host Traefik reports, and only from Traefik. Do not trust forwarded headers from everywhere: any client could then claim any origin.

**Prevent it:** document each protected app's provider settings (external host, mode, cookie domain) next to its Traefik labels, and keep NTP healthy on every host.

**Next step:** [HTTP behaviour scenarios](25-playbook-site-down.md#8-http-behaviour-scenarios) · [Time & NTP](12-time-ntp.md) · KodeKloud: *DevOps Pre-Requisite Course* — SSL & TLS Basics ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · [authentik documentation](https://docs.goauthentik.io/)

**Community threads:** [authentik #1997: forward auth redirects to authentik](https://github.com/goauthentik/authentik/issues/1997) · [authentik #8127: request has been denied](https://github.com/goauthentik/authentik/issues/8127) · [authentik #2023: logout and proxied sessions](https://github.com/goauthentik/authentik/issues/2023) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=authentik+redirect+loop&restrict_sr=1)

### 13.3 No workers connected after an upgrade

> **Seen as:** the admin UI warns `No workers connected`; outposts stop updating; on a fresh install `/if/flow/initial-setup/` returns Not Found; an upgrade hangs in a migration · **Where:** upgrades across several releases, a compose file reused from an older release · **Level:** [L3 · Senior] · **How common:** authentik #16780 (2025.8.2), #18292 (2025.10.2, 50 comments), #17740, #20667 and #11046

**Why it happens:** server and worker share the database schema and the task system, so they must run the same release. Recent releases reworked how background tasks run, so a compose file from an older release can start a worker that never connects. The worker can also crash on permissions or database access, or still be applying migrations and blueprints. The initial-setup flow is created by the worker, which is why a fresh install shows Not Found until the worker has finished.

**Diagnose:**

```bash
docker compose ps --format '{{.Name}}  {{.Image}}  {{.Status}}'
docker compose logs --tail 20 worker | grep -iE 'error|migrat|connect' | tail -n 3
```

```
authentik-server-1   ghcr.io/goauthentik/server:2026.5.4   Up 2 hours (healthy)
authentik-worker-1   ghcr.io/goauthentik/server:2025.12.1  Restarting (1) 20 seconds ago
```

**What the output tells you:** the worker runs an older tag than the server, typically because only one service's image was updated.

**Fix:**

```bash
docker compose exec -T postgresql pg_dump -U authentik -Fc authentik > authentik-$(date +%F).dump   # -T: no TTY, or the dump is corrupted
sed -i 's/^AUTHENTIK_TAG=.*/AUTHENTIK_TAG=2026.5.4/' .env      # one tag for server AND worker
docker compose pull && docker compose up -d && docker compose logs -f worker
```

Use the compose file published for your target release (see the authentik docs), upgrade one release at a time, and let migrations finish before you judge the result. A PostgreSQL major-version change needs a dump and restore, not just a new image tag.

**Why this fix works:** a single tag guarantees matching code on both services, and the backup makes a failed migration recoverable. Watching the worker log shows when blueprints and migrations are done.

**Prevent it:** pin `AUTHENTIK_TAG` in `.env`, read the release notes of every release you cross, and upgrade in a change window with a fresh database dump.

**Next step:** [Databases ops](38-learn-databases-ops.md) · [Docker Compose](30-learn-docker.md#9-docker-compose) · KodeKloud: *Docker Certified Associate* — Docker Compose ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [authentik documentation](https://docs.goauthentik.io/)

**Community threads:** [authentik #16780: no workers after 2025.8.2](https://github.com/goauthentik/authentik/issues/16780) · [authentik #18292: no workers 2025.10.2](https://github.com/goauthentik/authentik/issues/18292) · [authentik #17740: outposts after 2025.10.0](https://github.com/goauthentik/authentik/issues/17740) · [authentik #20667: migration hangs](https://github.com/goauthentik/authentik/issues/20667) · [authentik #11046: initial-setup Not Found](https://github.com/goauthentik/authentik/issues/11046)

---

## Self-check

Ten timed break-and-fix exercises from this module. Run each on the two-VM lab after taking a snapshot. Break it as described, then fix it using only the entry named.

| # | Stage | Break it | Expected fix (entry) | Time |
|---|---|---|---|---|
| 1 | Fresher | `sudo ufw deny 1514/tcp` on wazuh01, restart an agent | the agent turns Active again (5.1) | 15 min |
| 2 | Fresher | stop `wazuh-indexer`, open the dashboard | name the failing hop and restore it (6.1) | 10 min |
| 3 | Junior | rebuild `web01` and enroll it again immediately | the agent is enrolled without waiting an hour (5.3) | 15 min |
| 4 | Junior | point acquisition at the Traefik log with `type: nginx` | `cscli metrics` shows parsed lines (8.3) | 20 min |
| 5 | Junior | set `backend = auto` for the sshd jail on a journald-only host | Fail2ban runs and bans a test IP (9.2) | 15 min |
| 6 | Mid-level | `fallocate` the indexer disk to 96% | alerts flow again and retention is in place (6.4) | 30 min |
| 7 | Mid-level | add an app log line format with no decoder | a level-5 alert with `srcip` (7.1) | 30 min |
| 8 | Mid-level | change the indexer `admin` password in one place only | Filebeat, dashboard and vulnerability connector work (6.2) | 30 min |
| 9 | Senior | change wazuh01's IP | TLS works with certificates from the same root CA (6.7) | 45 min |
| 10 | Senior/Lead | restart Vault at "3 a.m." with Shamir, then design the fix | unsealed now, plus a written auto-unseal and alerting plan (11.1) | 45 min |

After each exercise, write the five-line note from §0. When you can do all ten within the time limits, you have the Wazuh and security-tooling skills the [career ladder](40-career-ladder.md) expects at L2–L3.

## Where to go next

- **Harden what Wazuh watches:** [Learn Security & DevSecOps](37-learn-security-devsecops.md): SSH hardening, Docker and UFW, private CA, secrets, supply chain.
- **The edge in front of everything:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) and [Traefik in depth](29-learn-webservers-proxies.md#4-traefik-in-depth), where CrowdSec, forward auth and access logs live.
- **The platform Wazuh agents run on:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) and [Dokploy in depth](29-learn-webservers-proxies.md#5-dokploy-in-depth).
- **Scanning in the pipeline:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) and [GitLab CI/CD](33-learn-cicd-iac-sre.md#2-gitlab-cicd).
- **When a security change breaks a site:** [Site down playbook](25-playbook-site-down.md) and [Containers and Kubernetes playbook](26-playbook-containers-k8s.md).
- **Port conflicts like 7.8:** [Ports inventory](22-playbook-ports-inventory.md), the [Apache 443 case](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md).
- **Kubernetes next:** [Learn Kubernetes](31-learn-kubernetes.md), then CKS on KodeKloud for runtime security and audit logs.
- **Career framing:** [Career ladder](40-career-ladder.md), where detection engineering and secrets management are L3–L4 skills.
- **Official docs:** [Wazuh](https://documentation.wazuh.com/current/) · [CrowdSec](https://docs.crowdsec.net/) · [Fail2ban wiki](https://github.com/fail2ban/fail2ban/wiki) · [Trivy](https://trivy.dev/) · [Vault](https://developer.hashicorp.com/vault/docs) · [OpenBao](https://openbao.org/docs/) · [Keycloak](https://www.keycloak.org/documentation) · [authentik](https://docs.goauthentik.io/)
