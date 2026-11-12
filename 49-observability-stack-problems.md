# 49 — Observability Toolbox & Problems: Prometheus, Grafana, Loki, Alertmanager, Zabbix, Uptime Kuma, ELK

This module teaches the Prometheus + Alertmanager + Grafana + Loki/Alloy stack as a toolbox for your Dokploy and Traefik hosts: how it is built, how to install it, how to run it day to day and how to learn it from fresher to senior, with Uptime Kuma, Zabbix, Netdata and ELK/OpenSearch/Graylog compared along the way. It then collects 40 problems that engineers really hit with all of these tools. They come from GitHub issues sorted by reactions and comments, the official forums (community.grafana.com, discuss.elastic.co, the Zabbix and Graylog forums) and the docs' troubleshooting pages; Stack Overflow and Reddit are reachable through search links. Every command is documented for you to run on your own lab VM or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Monitoring is how you hear about a problem before your users do. It is also where many first-year DevOps engineers lose a week: a target that stays DOWN for no visible reason, an alert that never arrives, a Loki volume that quietly fills the disk. Use the part that matches your stage, then move up.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | sections 1–2, entries 6.1, 6.2 and 7.1 | you can name what each container in the stack does and open a dashboard with real data from your own host |
| Junior | L1 Operator | section 2 and the L1 entries: 5.1–5.3, 6.3, 6.4, 7.2, 7.3, 9.1, 10.1, 10.2 | you bring a DOWN target back, add a host and a probe, and explain a "No data" panel without help |
| Mid-level | L2 Troubleshooter | sections 5, 8 and 9 | alerts reach the right people on time, every host's logs land in Loki, and you can prove from evidence why a notification was late |
| Senior | L3 Platform | section 3 and entries 5.7, 6.8, 9.6, 10.4, 11.2, 11.3 | the stack lives in GitLab with CI checks, upgrades are rehearsed, and Dokploy apps are scraped by label, not by IP list |
| Senior/Lead | L4 SRE | section 3, entries 8.4, 11.4, 11.5 and the Self-check | you own the alert review, a cardinality budget and a tested dead man's switch, and others follow your runbooks |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** use two lab VMs with Ubuntu 24.04: dokploy-1 with Dokploy installed (4 vCPU, 8 GB RAM, 60 GB disk) for the stack in section 2, and a small dokploy-2 (2 vCPU, 2 GB RAM) as a second host. Take snapshots, break one thing at a time on purpose, and fix it using only the entry. ELK, OpenSearch, Graylog and Zabbix get their own throwaway VM with 8 GB RAM, because they are heavy. After each fix, write a five-line note: symptom, evidence, cause, fix, prevention. Never practise on production.

**Placeholders and examples:** UPPERCASE words are placeholders (HOST, TARGET, CONTAINER, SERVICE, APP_NAME). The examples use dokploy-1 (192.0.2.10, private 10.10.0.10) as the Dokploy manager that also runs the monitoring stack, dokploy-2 (192.0.2.20, private 10.10.0.20) as a second server, 203.0.113.10 as the public address of shop.example.com, 172.30.0.0/24 for the Docker network "monitoring", 10.0.1.0/24 for dokploy-network, 198.51.100.25 for the SMTP relay smtp.example.com, the user ops, and names under example.com (grafana.example.com, status.example.com, plus harbor.example.com and gitlab.example.com, which use your private CA).

> 📚 **Study path:** KodeKloud [*Prep Course - Prometheus Certified Associate (PCA)*](https://kodekloud.com/courses/prometheus-certified-associate-pca) (Prometheus Fundamentals → PromQL → Alerting) → [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) (Grafana Loki Essentials) → handbook [Performance & observability](32-learn-performance-observability.md) (§10–14 and the §17 homelab lab) → [Prometheus docs](https://prometheus.io/docs/) and the [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) tutorial → lab: build section 2 on a Dokploy test VM, then work through the Self-check.

---

## 1. Prometheus, Grafana and Loki in 10 minutes

### What the stack is

Prometheus pulls numbers from HTTP endpoints every 15 to 30 seconds and stores them as time series, each named by a metric and a set of labels. It evaluates alert rules against them and sends firing alerts to Alertmanager, which groups, silences and routes them to email, Teams or Telegram. Grafana draws dashboards and lets you explore metrics and logs side by side. Loki stores logs indexed only by a few labels (a stream), and Grafana Alloy is the agent on each host that tails Docker and journald logs and pushes them to Loki. Exporters translate the world into Prometheus format: node_exporter for the host, cAdvisor for containers, blackbox_exporter for probes, and Traefik's built-in /metrics for requests.

Keep one sentence in mind: *Prometheus asks, Alloy tells.* Metrics are pulled, so Prometheus must reach every target; networks and firewalls cause most metric problems (section 5). Logs are pushed, so Loki must accept and store whatever arrives; labels, limits and retention cause most log problems (section 9).

### Architecture at a glance

```text
+----------------------- dokploy-1  192.0.2.10 / 10.10.0.10 -----------------------+
|                                                                                  |
|  [dokploy-traefik] :80 :443 --- grafana.example.com ---> [grafana]               |
|       | :8082 /metrics (internal entryPoint)              |  PromQL   | LogQL    |
|       v                                                   v           v          |
|  [prometheus] 127.0.0.1:9090 <----------------------------+     [loki] :3100     |
|     | scrapes: traefik, blackbox, loki, grafana, agents   (10.10.0.10 only) ^    |
|     | alerts                                                               |     |
|     v                                                                      |     |
|  [alertmanager] 127.0.0.1:9093 ---> email, Teams, heartbeat URL            |     |
|                                                                            |     |
|  [blackbox] ---> https://shop.example.com, harbor, gitlab (private CA)     |     |
|                                                                            |     |
|  agents (host network): node_exporter :9100, cAdvisor :8089, Alloy --push--+     |
+----------------------------------------------------------------------------------+
     v Prometheus scrapes :9100 :8089 (UFW: from 10.10.0.10 only)    ^ Alloy pushes logs
+----------------------- dokploy-2  192.0.2.20 / 10.10.0.20 -----------------------+
|  agents: node_exporter :9100, cAdvisor :8089, Alloy                              |
+----------------------------------------------------------------------------------+
```

### The moving parts

| Part | Runs as | Job | Listens on | First look when it misbehaves |
|---|---|---|---|---|
| Prometheus | container with a named volume | scrapes targets, keeps 30 days, evaluates rules | 9090 on 127.0.0.1 | Status > Targets, `docker logs` |
| Alertmanager | container | groups, inhibits, silences, routes and sends | 9093 on 127.0.0.1 | `amtool config routes test`, "Notify for alerts failed" in its log |
| Grafana | container behind dokploy-traefik | dashboards, Explore, optional alerting | 3000, served as grafana.example.com | panel Inspect > Query, `docker logs` |
| Loki | container with a named volume | stores log streams, answers LogQL | 3100 on the private IP | /ready, `loki_discarded_samples_total` |
| Alloy | container on every host | tails Docker and journald, pushes to Loki | 12345 (UI) on 127.0.0.1 | its UI component graph, `docker logs` |
| node_exporter | container on every host, host network | CPU, memory, disks, network, systemd units | 9100 | `curl -s localhost:9100/metrics` |
| cAdvisor | container on every host, host network | per-container CPU, memory, network | 8089 | `docker logs` (API version errors) |
| blackbox_exporter | container | HTTP, TCP, ICMP and TLS probes | 9115, internal | /probe with debug=true |
| Traefik metrics | inside dokploy-traefik | requests, 5xx, latency, certificates | 8082, internal | `wget -qO- http://dokploy-traefik:8082/metrics` from Prometheus |

### Three ideas behind most problems

1. **Pull needs a path.** Inside a container, localhost is the container itself, and UFW drops traffic from Docker bridges to host ports unless you allow it. The reverse also holds: ports published with -p skip UFW, so a published exporter is open to the world (entries 5.1, 6.4, 7.1).
2. **Labels are the bill.** Every new combination of label values is a new series in Prometheus and a new stream in Loki. IDs, raw URLs and container names in labels end as out-of-memory kills and 429 errors (entries 9.3, 11.4).
3. **An alert passes four gates.** The rule (expression plus `for`) fires, Prometheus sends it, Alertmanager routes, groups, inhibits or silences it, and the receiver delivers it over SMTP, a webhook and TLS. "No alert" means one gate is closed; check them in that order (entries 8.1, 8.4).

### Where it fits with Dokploy, Traefik and GitLab

The stack is one more Compose app in Dokploy, deployed from a GitLab repository. Only Grafana gets a domain, grafana.example.com, routed by dokploy-traefik with a certificate. Prometheus, Alertmanager and the Alloy UI listen on 127.0.0.1 and you reach them through an SSH tunnel. Prometheus joins dokploy-network to scrape Traefik's internal metrics entryPoint and, if you label them, your apps (entry 5.7). Configuration changes follow your normal pipeline: merge request, GitLab CI runs promtool and amtool, merge, Dokploy redeploys. blackbox_exporter probes Harbor and GitLab with your private CA, so an expiring certificate pages you before a pipeline fails ([CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md)).

Two neighbours keep their own jobs. The Dokploy panel shows per-service CPU, memory and logs, but it cannot page you when its own host is down ([Dokploy deep dive](45-dokploy-and-self-hosted-paas.md)). Wazuh reads the same journald for security events ([Wazuh & security tools](48-wazuh-and-security-tools.md)): Loki is for operations, Wazuh for detection.

### The other tools side by side

| Tool | Best at | Weak at | Pick it when | Entries |
|---|---|---|---|---|
| Uptime Kuma | uptime checks and status pages in five minutes, dozens of notification channels | no metrics depth; SQLite strain as monitors grow | you need "is it up?" for a few hundred URLs today, or a watcher outside the main stack | 7.1 |
| Netdata | per-second host and container charts with zero configuration | long retention and fleet-wide alert design; noisy defaults | you debug one slow host live ([Slow system](23-playbook-slow-system.md)) | 7.2 |
| Zabbix | agent-based fleets, SNMP and network gear, templates, inventory | short-lived containers, the PromQL ecosystem | you inherit a classic server and network estate, or need SNMP | 7.3, 7.4 |
| ELK / OpenSearch | full-text search over large log volumes, SIEM storage (the Wazuh indexer is OpenSearch) | JVM heap, disk and shard planning | you search many GB of logs a day or already run Wazuh | 10.1, 10.3, 10.4 |
| Graylog | a ready log console with streams, pipelines and alerts | needs MongoDB plus OpenSearch | a team wants a log UI without building Kibana views | 10.2, 10.5 |
| Prometheus + Grafana + Loki | metrics and logs for Docker, Swarm and Kubernetes; PromQL; alert routing | you design labels, retention and HA yourself | your default for Dokploy and the CKA/PCA path | 5–9, 11 |

### What to watch first on a Dokploy host

Start with these signals before any dashboard polish; section 2 turns each one into a rule.

- **Host (USE: utilisation, saturation, errors):** disk above 85% and "full within 24 hours", memory available under 10%, OOM kills, failed systemd units, load compared with the CPU count.
- **Containers:** memory near the limit, restart loops (Dokploy's deploy notifications), CPU throttling on busy apps.
- **Traefik (RED: rate, errors, duration):** 5xx ratio per service, p95 latency, certificate expiry.
- **From outside:** one HTTP probe per public domain plus Harbor and GitLab, ideally also from a second site.
- **The stack itself:** an always-firing Watchdog heartbeat, failed config reloads, failed notifications, Loki rejecting logs.

The methods behind this list are in [Performance & observability](32-learn-performance-observability.md#2-methodologies); the playbook that uses these signals during an incident is [Slow system](23-playbook-slow-system.md).

---

## 2. Install and first configuration

This builds the stack the way you run it on a Dokploy host: a Git repository in GitLab, deployed by Dokploy as a Compose app, with agents on every server. The generic single-VM version without Dokploy is the lab in [32 §17](32-learn-performance-observability.md#17-homelab-lab-full-monitoring-stack); do that one first if you have never run Prometheus.

### Before you install

- **Where it runs.** A separate small VM (2 vCPU, 4 GB RAM, 50 GB SSD) is best, because monitoring should survive the host it watches. With a single Dokploy host, run it there and add an outside watcher (entry 7.1).
- **Disk.** Prometheus needs 1 to 2 bytes per sample. Five hosts plus Traefik make about 10,000 series; at a 30 s interval that is 333 samples per second, or about 1.7 GB for 30 days. Loki compresses well: 2 GB of raw logs a day becomes roughly 10 GB for 31 days. A dedicated 50 GB volume covers both, with headroom for compaction.
- **Ports.** Nothing new is public. Only grafana.example.com goes through Traefik; 9100 and 8089 are open to the Prometheus host only (UFW), Loki's 3100 is bound to the private IP, and every UI binds 127.0.0.1.
- **No ./ bind mounts.** Dokploy re-clones the code directory on every deploy, so a config file bind-mounted from ./ can turn up empty or stale ([Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 10.1). Here each config directory is baked into a small image at deploy time, and secrets live under ../files, outside the clone.
- **Versions.** Pin every image. The `.env.example` below lists the versions that were current in October 2026. Check first that the ports are free: `sudo ss -ltnp | grep -E ':(3100|8082|8089|9090|9093|9100|12345)\b'` should print nothing.

### The repository layout

```text
observability/                        # GitLab repo; Dokploy deploys it as a Compose app
├── docker-compose.yml                # central stack (dokploy-1 only)
├── agents/docker-compose.yml         # node_exporter, cAdvisor, Alloy (every host)
├── .env.example                      # pinned versions; real values go in Dokploy's Environment tab
├── prometheus/Dockerfile             # FROM prom/prometheus + COPY . /etc/prometheus/
├── prometheus/prometheus.yml
├── prometheus/rules/host.yml
├── prometheus/rules/platform.yml
├── prometheus/targets/nodes.yml      # file_sd: one entry per server, re-read without a reload
├── prometheus/targets/cadvisor.yml
├── alertmanager/Dockerfile + alertmanager.yml
├── blackbox/Dockerfile + blackbox.yml + internal-ca.crt   # a CA certificate is public, safe in Git
├── loki/Dockerfile + loki.yml
├── alloy/Dockerfile + config.alloy
├── grafana/Dockerfile
├── grafana/provisioning/datasources/datasources.yml
├── grafana/provisioning/dashboards/dashboards.yml
├── grafana/dashboards/Infra/*.json   # the folder name becomes the Grafana folder
├── tests/host_test.yml               # promtool unit tests for the rules
└── .gitlab-ci.yml
```

```bash
# .env.example - versions checked on 3 October 2026; bump them in a merge request, never use latest
PROMETHEUS_TAG=v3.13.4      # 3.13 is the LTS line; 3.15.0 is the newest feature release
ALERTMANAGER_TAG=v0.34.1
BLACKBOX_TAG=v0.28.0
NODE_EXPORTER_TAG=v1.12.1
GRAFANA_TAG=13.2.0          # Grafana 13 since April 2026
LOKI_TAG=3.7.8
ALLOY_TAG=v1.20.0
CADVISOR_IMAGE=CADVISOR_IMAGE_AND_TAG   # copy it from the cAdvisor releases page; 0.49.x cannot talk to Docker 29 (5.5)
HOST_LABEL=dokploy-1        # agents only: the host label for this server
GRAFANA_ADMIN_PASSWORD=CHANGE_ME        # used on Grafana's first start only (6.1); set the real one in Dokploy
```

Every config directory carries the same short image recipe, so a deploy that changes a rule builds a new image and recreates only that container:

```dockerfile
# prometheus/Dockerfile (alertmanager/, blackbox/, loki/ and alloy/ follow the same pattern)
ARG PROMETHEUS_TAG
FROM prom/prometheus:${PROMETHEUS_TAG}
COPY . /etc/prometheus/
```

```dockerfile
# grafana/Dockerfile
ARG GRAFANA_TAG
FROM grafana/grafana:${GRAFANA_TAG}
COPY provisioning/ /etc/grafana/provisioning/
COPY dashboards/ /etc/grafana/dashboards/
```

### Agents on every host

```yaml
# agents/docker-compose.yml - one Dokploy Compose app per server (compose path ./agents/docker-compose.yml)
services:
  node-exporter:
    image: prom/node-exporter:${NODE_EXPORTER_TAG}
    command:
      - --path.rootfs=/host
      - --collector.systemd
      - --collector.systemd.unit-include=(docker|containerd|ssh|ufw|chrony|systemd-resolved)\.service
      - --collector.textfile.directory=/host/var/lib/node_exporter/textfile
    network_mode: host                # the host's real interfaces; listens on :9100 and UFW applies
    pid: host
    volumes:
      - /:/host:ro,rslave
      - /run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket:ro   # the systemd collector asks D-Bus
    restart: unless-stopped

  cadvisor:
    image: ${CADVISOR_IMAGE}
    command:
      - --port=8089                   # 8080 is often taken on Dokploy hosts
      - --docker_only=true
      - --housekeeping_interval=30s
      - --store_container_labels=false
      - --whitelisted_container_labels=com.docker.swarm.service.name,com.docker.compose.project,com.docker.compose.service
      - --disable_metrics=percpu,sched,tcp,udp,disk,process,hugetlb,referenced_memory,cpu_topology,resctrl
    network_mode: host
    privileged: true
    devices: ["/dev/kmsg"]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    restart: unless-stopped

  alloy:
    build:
      context: ../alloy               # config.alloy is baked in at deploy time
      args: {ALLOY_TAG: "${ALLOY_TAG}"}
    command:
      - run
      - --server.http.listen-addr=0.0.0.0:12345
      - --storage.path=/var/lib/alloy/data
      - /etc/alloy/config.alloy
    environment:
      HOST_LABEL: ${HOST_LABEL}
      LOKI_URL: http://10.10.0.10:3100/loki/api/v1/push
    ports: ["127.0.0.1:12345:12345"]  # UI through an SSH tunnel only
    volumes:
      - alloy-data:/var/lib/alloy/data                 # read positions survive restarts (9.1)
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log/journal:/var/log/journal:ro
      - /etc/machine-id:/etc/machine-id:ro
    restart: unless-stopped

volumes:
  alloy-data:
```

Create the textfile directory once on each host (`sudo install -d -m 0755 /var/lib/node_exporter/textfile`). Scripts such as a backup job write `*.prom` files there, for example a `backup_last_success_timestamp_seconds` line, and node_exporter publishes them.

### Open the firewall narrowly

```bash
# dokploy-1: Prometheus sits on network "monitoring" and reaches the local agents via host.docker.internal
sudo ufw allow proto tcp from 172.30.0.0/24 to any port 9100,8089 comment 'prometheus -> local agents'
# every other host: only the monitoring server may scrape
sudo ufw allow proto tcp from 10.10.0.10 to any port 9100,8089 comment 'prometheus scrape'
sudo ufw status numbered | grep -E '9100'
```

```text
[ 7] 9100,8089/tcp              ALLOW IN    172.30.0.0/24              # prometheus -> local agents
```

Loki needs no UFW rule: Docker-published ports skip UFW, so the bind address in the Compose file (10.10.0.10:3100) is the control. On a network you do not trust, route Loki through Traefik with basic auth instead.

### Turn on Traefik metrics in Dokploy

```yaml
# /etc/dokploy/traefik/traefik.yml - add these keys and keep everything else; then: docker restart dokploy-traefik
entryPoints:
  # web and websecure stay exactly as they are
  metrics:
    address: ":8082"            # never published: Prometheus reaches it over dokploy-network
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
    addRoutersLabels: false     # per-router histograms multiply series (11.4)
```

Restarting Traefik drops connections for a second, so pick a quiet minute. Keep a copy of this block in the repository and check it after Dokploy updates. The metrics themselves and ready-made Traefik alerts are in the [Traefik deep dive](43-traefik-and-reverse-proxies.md), section 3.4.

### The central stack

```yaml
# docker-compose.yml - central stack on dokploy-1 (Dokploy Compose app, type Docker Compose)
services:
  prometheus:
    build: {context: ./prometheus, args: {PROMETHEUS_TAG: "${PROMETHEUS_TAG}"}}
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --storage.tsdb.retention.size=20GB          # a safety cap well below the volume size (11.1)
    ports: ["127.0.0.1:9090:9090"]                   # SSH tunnel only
    extra_hosts: ["host.docker.internal:host-gateway"]
    volumes: ["prometheus-data:/prometheus"]
    networks: [monitoring, dokploy-network]
    restart: unless-stopped

  alertmanager:
    build: {context: ./alertmanager, args: {ALERTMANAGER_TAG: "${ALERTMANAGER_TAG}"}}
    command:
      - --config.file=/etc/alertmanager/alertmanager.yml
      - --storage.path=/alertmanager
      - --cluster.listen-address=                    # a single instance needs no gossip (8.1)
    ports: ["127.0.0.1:9093:9093"]
    volumes:
      - ../files/secrets:/etc/alertmanager/secrets:ro   # smtp_password, teams_url, heartbeat_url
      - alertmanager-data:/alertmanager
    networks: [monitoring]
    restart: unless-stopped

  blackbox:
    build: {context: ./blackbox, args: {BLACKBOX_TAG: "${BLACKBOX_TAG}"}}
    command: ["--config.file=/etc/blackbox/blackbox.yml"]
    cap_add: [NET_RAW]                               # ICMP probes (5.4)
    networks: [monitoring]
    restart: unless-stopped

  loki:
    build: {context: ./loki, args: {LOKI_TAG: "${LOKI_TAG}"}}
    command: ["-config.file=/etc/loki/loki.yml"]
    ports: ["10.10.0.10:3100:3100"]                   # private interface only: Alloy pushes here
    volumes: ["loki-data:/loki"]
    networks: [monitoring]
    restart: unless-stopped

  grafana:
    build: {context: ./grafana, args: {GRAFANA_TAG: "${GRAFANA_TAG}"}}
    environment:
      GF_SERVER_ROOT_URL: https://grafana.example.com/
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_DATABASE_WAL: "true"                        # SQLite under load (6.8)
    volumes: ["grafana-data:/var/lib/grafana"]
    labels:
      - traefik.docker.network=dokploy-network       # two networks: tell Traefik which one to use
    networks: [monitoring, dokploy-network]
    restart: unless-stopped

volumes:
  prometheus-data:
  alertmanager-data:
  loki-data:
  grafana-data:

networks:
  monitoring:
    name: monitoring
    ipam:
      config:
        - subnet: 172.30.0.0/24
  dokploy-network:
    external: true
```

The traefik.docker.network label matters: a routed container on two networks gives Traefik two addresses, and picking the wrong one causes intermittent 504s ([Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 6.3).

### Prometheus configuration

```yaml
# prometheus/prometheus.yml - relative paths resolve next to this file, in the container and in CI
global:
  scrape_interval: 30s
  scrape_timeout: 10s
  evaluation_interval: 30s
  external_labels:
    site: onprem-1

rule_files:
  - rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
        labels: {host: dokploy-1}

  - job_name: node
    file_sd_configs:
      - files: ["targets/nodes.yml"]

  - job_name: cadvisor
    file_sd_configs:
      - files: ["targets/cadvisor.yml"]

  - job_name: traefik
    static_configs:
      - targets: ["dokploy-traefik:8082"]
        labels: {host: dokploy-1}

  - job_name: stack
    static_configs:
      - targets: ["alertmanager:9093", "loki:3100", "grafana:3000", "blackbox:9115"]
        labels: {host: dokploy-1}

  - job_name: probe-public
    metrics_path: /probe
    params: {module: [http_2xx]}
    static_configs:
      - targets: ["https://shop.example.com/healthz", "https://grafana.example.com/api/health"]
        labels: {host: dokploy-1}                # the host that serves them, for inhibition (8.4)
    relabel_configs: &blackbox_relabel           # YAML anchor: reused by probe-internal
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox:9115

  - job_name: probe-internal
    metrics_path: /probe
    params: {module: [http_internal]}
    static_configs:
      - targets: ["https://harbor.example.com"]
        labels: {host: harbor-1}
      - targets: ["https://gitlab.example.com/-/health"]
        labels: {host: gitlab-1}
    relabel_configs: *blackbox_relabel
```

```yaml
# prometheus/targets/nodes.yml - Prometheus notices edits by itself; no reload needed
- targets: ["host.docker.internal:9100"]
  labels: {host: dokploy-1, role: manager}
- targets: ["10.10.0.20:9100"]
  labels: {host: dokploy-2, role: worker}
# prometheus/targets/cadvisor.yml is the same list with port 8089
```

Every job carries a `host` label naming the machine that serves it, probes included. Inhibition (entry 8.4) and per-host dashboards depend on it, so add it to every new job.

### Alert rules

```yaml
# prometheus/rules/host.yml
groups:
  - name: host
    rules:
      - alert: TargetDown
        expr: up == 0
        for: 5m
        labels: {severity: page}
        annotations:
          summary: "{{ $labels.job }} on {{ $labels.host }} ({{ $labels.instance }}) is down"
          runbook_url: https://wiki.example.com/runbooks/target-down
      - alert: DiskAbove85Percent
        expr: |
          (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|squashfs|overlay|ramfs"}
             / node_filesystem_size_bytes) * 100 > 85
        for: 10m
        labels: {severity: ticket}
        annotations: {summary: "{{ $labels.host }} {{ $labels.mountpoint }} is {{ $value | humanize }}% full"}
      - alert: DiskFullIn24h
        expr: predict_linear(node_filesystem_avail_bytes{fstype=~"ext4|xfs"}[6h], 24 * 3600) < 0
        for: 30m
        labels: {severity: page}
        annotations: {summary: "{{ $labels.host }} {{ $labels.mountpoint }} will be full within 24 hours"}
      - alert: SystemdUnitFailed
        expr: node_systemd_unit_state{state="failed"} == 1
        for: 5m
        labels: {severity: ticket}
        annotations: {summary: "{{ $labels.name }} failed on {{ $labels.host }}"}
      - alert: HostMemoryLow
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.10
        for: 10m
        labels: {severity: ticket}
        annotations: {summary: "{{ $labels.host }} has less than 10% memory available"}
      - alert: HostOomKill
        expr: increase(node_vmstat_oom_kill[10m]) > 0
        labels: {severity: ticket}
        annotations: {summary: "The kernel OOM killer fired on {{ $labels.host }}"}
      - alert: ContainerNearMemoryLimit
        expr: |
          container_memory_working_set_bytes{name!=""}
            / (container_spec_memory_limit_bytes{name!=""} > 0) > 0.9
        for: 10m
        labels: {severity: ticket}
        annotations: {summary: "{{ $labels.name }} on {{ $labels.host }} uses over 90% of its memory limit"}
```

```yaml
# prometheus/rules/platform.yml
groups:
  - name: platform
    rules:
      - alert: ProbeFailed
        expr: probe_success == 0
        for: 2m
        labels: {severity: page}
        annotations: {summary: "{{ $labels.instance }} fails its {{ $labels.job }} probe"}
      - alert: CertificateExpiresSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 14 * 86400
        for: 1h
        labels: {severity: ticket}
        annotations: {summary: "The certificate of {{ $labels.instance }} expires in {{ $value | humanizeDuration }}"}
      - alert: TraefikServiceHigh5xx
        expr: |
          sum by (service) (rate(traefik_service_requests_total{code=~"5.."}[5m]))
            / sum by (service) (rate(traefik_service_requests_total[5m])) > 0.05
        for: 10m
        labels: {severity: page}
        annotations: {summary: "{{ $labels.service }} answers more than 5% errors"}
  - name: meta
    rules:
      - alert: Watchdog
        expr: vector(1)
        labels: {severity: heartbeat}
        annotations: {summary: "Always firing: proves rules, Alertmanager and the receiver work end to end"}
      - alert: PrometheusConfigReloadFailed
        expr: prometheus_config_last_reload_successful == 0
        for: 5m
        labels: {severity: ticket}
      - alert: AlertmanagerNotificationsFailing
        expr: rate(alertmanager_notifications_failed_total[10m]) > 0
        for: 10m
        labels: {severity: ticket}
        annotations: {summary: "Alertmanager cannot deliver to {{ $labels.integration }}"}
      - alert: LokiDiscardingLogs
        expr: sum by (reason) (rate(loki_discarded_samples_total[10m])) > 0
        for: 15m
        labels: {severity: ticket}
        annotations: {summary: "Loki rejects log lines: {{ $labels.reason }}"}
      - alert: ScrapeNearTimeout
        expr: scrape_duration_seconds > 8              # scrape_timeout is 10s
        for: 15m
        labels: {severity: ticket}
```

The disk and systemd rules are the ops-ladder L4 drill; the [32 §12](32-learn-performance-observability.md#12-alertmanager-and-alert-rules) chapter explains how `for`, pending and firing work.

### Alertmanager configuration

```yaml
# alertmanager/alertmanager.yml - secrets are files under ../files/secrets, never in Git
global:
  resolve_timeout: 5m
  smtp_smarthost: smtp.example.com:587
  smtp_from: alertmanager@example.com
  smtp_auth_username: alertmanager@example.com
  smtp_auth_password_file: /etc/alertmanager/secrets/smtp_password
  smtp_require_tls: true

route:
  receiver: ops-email                    # tickets: grouped email
  group_by: ["alertname", "host"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - matchers: ['severity="heartbeat"']
      receiver: heartbeat
      group_wait: 0s
      group_interval: 1m
      repeat_interval: 1m
    - matchers: ['severity="page"']
      receiver: ops-teams
      group_wait: 10s
      repeat_interval: 1h

inhibit_rules:
  - source_matchers: ['alertname="TargetDown"', 'job="node"']   # a dead host explains its other alerts
    target_matchers: ['severity=~"page|ticket"']
    equal: ["host"]

receivers:
  - name: ops-email
    email_configs:
      - to: ops@example.com
        send_resolved: true
  - name: ops-teams
    msteamsv2_configs:
      - webhook_url_file: /etc/alertmanager/secrets/teams_url   # a Teams Workflows webhook (8.1)
        send_resolved: true
  - name: heartbeat
    webhook_configs:
      - url_file: /etc/alertmanager/secrets/heartbeat_url       # a dead man's switch on another host
```

### Probes, Loki and Alloy

```yaml
# blackbox/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      preferred_ip_protocol: ip4        # the default prefers IPv6 (5.4)
  http_internal:
    prober: http
    timeout: 10s
    http:
      preferred_ip_protocol: ip4
      valid_status_codes: [200, 301, 302, 401]
      tls_config:
        ca_file: /etc/blackbox/internal-ca.crt
  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: ip4
```

```yaml
# loki/loki.yml - single binary, filesystem storage, retention on from day one
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  instance_addr: 127.0.0.1
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules

schema_config:
  configs:
    - from: 2026-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 744h               # 31 days
  ingestion_rate_mb: 8
  ingestion_burst_size_mb: 16
  max_global_streams_per_user: 10000
  reject_old_samples: true
  reject_old_samples_max_age: 168h

compactor:
  working_directory: /loki/compactor
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  delete_request_store: filesystem

ruler:
  alertmanager_url: http://alertmanager:9093

analytics:
  reporting_enabled: false
```

```text
// alloy/config.alloy - Docker and journald logs to Loki with a few bounded labels
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

discovery.relabel "containers" {
  targets = []
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_swarm_service_name"]
    regex         = "(.+)"
    target_label  = "service"
  }
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
    regex         = "(.+)"
    target_label  = "service"
  }
}

loki.source.docker "containers" {
  host          = "unix:///var/run/docker.sock"
  targets       = discovery.docker.containers.targets
  relabel_rules = discovery.relabel.containers.rules
  labels        = {host = sys.env("HOST_LABEL"), source = "docker"}
  forward_to    = [loki.process.drop_debug.receiver]
}

loki.process "drop_debug" {
  stage.drop {
    expression = "(?i)level=debug"
  }
  forward_to = [loki.write.default.receiver]
}

loki.relabel "journal" {
  forward_to = []
  rule {
    source_labels = ["__journal__systemd_unit"]
    target_label  = "unit"
  }
}

loki.source.journal "system" {
  path          = "/var/log/journal"
  max_age       = "12h"
  relabel_rules = loki.relabel.journal.rules
  labels        = {host = sys.env("HOST_LABEL"), source = "journal"}
  forward_to    = [loki.write.default.receiver]
}

loki.write "default" {
  endpoint {
    url = sys.env("LOKI_URL")
  }
}
```

The labels are host, source, service and unit, all with bounded values. Container IDs and Swarm task names change on every deploy, so they stay out of labels (entry 9.3).

### Grafana provisioning

```yaml
# grafana/provisioning/datasources/datasources.yml - fixed uids keep dashboards portable (6.6)
apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: 30s              # equal to scrape_interval, so $__rate_interval is right (6.2)
  - name: Loki
    uid: loki
    type: loki
    access: proxy
    url: http://loki:3100
  - name: Alertmanager
    uid: alertmanager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    jsonData:
      implementation: prometheus
```

```yaml
# grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1
providers:
  - name: infra
    type: file
    allowUiUpdates: false            # Git is the source of truth; edit, export, commit
    updateIntervalSeconds: 60
    options:
      path: /etc/grafana/dashboards
      foldersFromFilesStructure: true
```

Start with the community "Node Exporter Full" dashboard (grafana.com ID 1860): import it once in the UI, export it as JSON with the switch for use in another instance turned off ("Export for sharing externally" in older versions), and commit the JSON under grafana/dashboards/Infra/ (entry 6.6 explains why).

### Deploy with Dokploy and verify

1. Create the secret files once on dokploy-1 (the first block below). Dokploy keeps each Compose app under /etc/dokploy/compose/APP_NAME, with code/ (re-cloned) and files/ (kept).
2. In Dokploy, create a project "observability", add a Compose service from the GitLab repository (branch main, compose path ./docker-compose.yml), paste the `.env.example` values into the Environment tab with real secrets, and deploy.
3. Under Domains, add grafana.example.com for service grafana, port 3000, HTTPS with your certificate resolver, then redeploy (Compose domains need a redeploy).
4. Add the agents as a second Compose app per server (compose path ./agents/docker-compose.yml, HOST_LABEL set per server), then add Traefik metrics as shown above.

```bash
APP=/etc/dokploy/compose/APP_NAME                       # Dokploy's folder for the stack
sudo install -d -m 0750 -o 65534 -g 65534 "$APP/files/secrets"
sudo touch "$APP"/files/secrets/{smtp_password,teams_url,heartbeat_url}
sudoedit "$APP/files/secrets/smtp_password"             # one line each, no trailing spaces
sudo chown 65534:65534 "$APP"/files/secrets/* && sudo chmod 0400 "$APP"/files/secrets/*
```

```bash
# From your laptop: tunnel to the UIs, then check every target and the Watchdog
ssh -N -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 ops@192.0.2.10 &
curl -s localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job, .scrapeUrl, .health, .lastError] | @tsv'
curl -s localhost:9093/api/v2/alerts | jq -r '.[].labels.alertname'
curl -s -o /dev/null -w '%{http_code}\n' https://grafana.example.com/api/health
```

```text
prometheus      http://localhost:9090/metrics                     up
node            http://host.docker.internal:9100/metrics          up
node            http://10.10.0.20:9100/metrics                    up
cadvisor        http://host.docker.internal:8089/metrics          up
cadvisor        http://10.10.0.20:8089/metrics                    down   Get "http://10.10.0.20:8089/metrics": context deadline exceeded
traefik         http://dokploy-traefik:8082/metrics               up
stack           http://loki:3100/metrics                          up
probe-public    http://blackbox:9115/probe?module=http_2xx&target=https%3A%2F%2Fshop.example.com%2Fhealthz   up
probe-internal  http://blackbox:9115/probe?module=http_internal&target=https%3A%2F%2Fharbor.example.com     up
Watchdog
200
```

Read it like an incident: one target times out, and only on dokploy-2's port 8089, so dokploy-2 is missing its UFW rule for 8089 (entry 5.1). Watchdog firing is good news: it is the heartbeat that proves the alert path works. Finally send one test alert through the whole chain and confirm a human received it:

```bash
docker exec "$(docker ps -qf name=alertmanager)" amtool --alertmanager.url=http://localhost:9093 \
  alert add DeployTest severity=ticket host=dokploy-1 --annotation=summary="test from the install runbook"
```

---

## 3. Day-2 operations

Installing the stack takes an afternoon; keeping it trustworthy is the real job. A monitoring system that is silently broken is worse than none, because people stop checking by hand.

### A weekly health routine

Ten minutes every Monday, with the SSH tunnel from section 2 open:

```bash
q() { curl -s localhost:9090/api/v1/query --data-urlencode "query=$1" | jq -r '.data.result[] | "\(.metric|tostring) \(.value[1])"'; }
q 'count(up == 0)'                                                   # DOWN targets; no output means none
q 'sum by (job) (scrape_samples_scraped)'                            # series per job: compare with last week
q 'sum by (reason) (increase(loki_discarded_samples_total[7d]))'     # logs Loki refused
q 'sum by (integration) (increase(alertmanager_notifications_failed_total[7d]))'
curl -s localhost:9093/api/v2/silences | jq -r '.[] | select(.status.state=="active") | "\(.endsAt) \(.createdBy) \(.comment)"'
ssh ops@192.0.2.10 'df -h /var/lib/docker | tail -1'
```

```text
{"job":"cadvisor"} 6120
{"job":"node"} 2910
{"integration":"msteamsv2"} 3
2026-12-31T23:00:00.000Z ops mute dokploy-2 during kernel update
/dev/sdb1        59G   21G   36G  37% /var/lib/docker
```

**Act on it:** a DOWN target goes to entry 5.1; a job that grew more than 30% in a week goes to 11.4; failed notifications go to 8.1 (three failed Teams deliveries here deserve a look today); a silence that ends in three months for a one-hour maintenance must be expired now; the Docker disk above 70% goes to 11.1 and 9.4.

### Upgrades without surprises

| Component | Read before upgrading | Typical trap | Entry |
|---|---|---|---|
| Prometheus 2 to 3 | the migration guide | strict scrape Content-Type, le="1.0", Alertmanager API v2 only | 11.2 |
| Grafana 11, 12, 13 | What's new, plus a plugin inventory | AngularJS plugins gone since 12; back up grafana.db first | 6.7 |
| Loki 2 to 3 and 3.x minors | the upgrade guide | schema v13 and tsdb; no shell in images from 3.5.8 | 9.6 |
| Promtail or Grafana Agent to Alloy | Alloy's migration guide | positions re-read, permissions on docker.sock and journald | 9.1 |
| Docker Engine on monitored hosts | Docker's release notes | cAdvisor's API version refused after Docker 29 | 5.5 |
| Uptime Kuma 1 to 2 | the wiki migration page | a long database migration; back up first | 7.1 |
| Elasticsearch, OpenSearch, Graylog | the compatibility matrix | Kibana and Elasticsearch versions must match; MongoDB needs AVX | 10.1, 10.2 |

The routine is the same for all of them: bump one pinned version in a merge request, let CI validate it, deploy it to a staging VM (or run the new version beside the old one on another port against the same targets), watch it for a day, then deploy to production. Write the rollback down before you start: for Prometheus it is the previous tag, and only 2.55 or later can read a TSDB written by 3.x.

### Backups and restores

| What | How | Why it matters |
|---|---|---|
| The Git repository | GitLab and its own backups | the real backup: config, rules and dashboards rebuild the stack in 20 minutes |
| Grafana database | nightly `sqlite3 .backup`, or dumps once it runs on PostgreSQL | users, teams, service accounts and anything not provisioned |
| Secrets in ../files/secrets | your password manager or Vault ([Wazuh & security tools](48-wazuh-and-security-tools.md)) | they are not in Git by design |
| Alertmanager data | optional | silences and the notification log; losing them re-sends a few notifications |
| Prometheus TSDB | a snapshot in a backup window, or accept the loss | history helps capacity planning, but metrics are rarely evidence |
| Loki chunks | object storage with versioning if logs must be kept | compliance logs belong in an archive or Wazuh, not only in Loki |
| Uptime Kuma /app/data | a volume archive with the container stopped | monitors, history and status pages |

For Grafana, `sqlite3 grafana.db ".backup '/backup/grafana.db'"` takes a consistent copy while it runs (entry 6.8); a Prometheus snapshot is a POST to /api/v1/admin/tsdb/snapshot and needs `--web.enable-admin-api`, so enable that flag only for the backup window. Once a quarter, rebuild the whole stack on a scratch VM from Git plus the latest Grafana backup, and time it. That number belongs in your DR plan ([Senior architecture](39-learn-senior-architecture.md), [Databases, storage & backups](51-problems-databases-storage-backup.md)).

### Capacity, retention and cardinality

- **Prometheus disk:** retention seconds × samples per second × 2 bytes, plus 20 to 30% for the WAL and compaction. Keep both limits: `retention.time` for intent, `retention.size` as the safety net (entry 11.1).
- **Cardinality budget:** check every new exporter before production. `curl -s TARGET:PORT/metrics | grep -vc '^#'` counts its series; anything above a few thousand per target needs a reason (entry 11.4).
- **Loki labels:** at most about ten labels, each with a bounded set of values. `logcli series --analyze-labels '{host=~".+"}'` shows which label explodes (entry 9.3).
- **Longer history:** a second system (Thanos, Mimir or VictoriaMetrics) only when you need more than about 90 days or several Prometheus servers in one view (entry 11.5). Most single-site Dokploy estates never do.

The method behind these numbers is in [Capacity planning](32-learn-performance-observability.md#16-capacity-planning).

### Security hardening

- **Publish nothing you do not need.** Only Grafana goes through Traefik. Prometheus, Alertmanager and Alloy bind 127.0.0.1, Loki binds the private IP. Docker-published ports skip UFW, so the bind address is the control ([Who owns this port?](22-playbook-ports-inventory.md)).
- **Prometheus and Alertmanager have no login.** If they must be reachable, put them behind Traefik with forward auth or basic auth, or use `--web.config.file` with TLS and basic auth users. This stack avoids the lifecycle API (/-/reload, /-/quit) and reloads by restart or SIGHUP.
- **Grafana:** change the bootstrap password, give everyone a personal account or SSO (Keycloak or Authentik, see [Wazuh & security tools](48-wazuh-and-security-tools.md)), keep sign-up off, and use service accounts for API tokens.
- **The Docker socket is root.** Alloy and cAdvisor read it; Prometheus service discovery should go through a read-only socket proxy (entry 5.7).
- **Secrets are files** outside Git (smtp_password, teams_url, heartbeat_url). The private CA certificate is public and can live in Git.
- **Logs carry secrets.** Tokens and passwords end up in log lines. Mask them in Alloy (a `stage.replace` in loki.process) before they reach Loki, and never put user data in labels.

### Monitoring the monitoring

- **The Watchdog heartbeat** fires forever and goes to a heartbeat URL on another machine: an Uptime Kuma push monitor on dokploy-2, or a hosted dead man's switch. When the heartbeats stop, the outside system raises the alarm that your stack can no longer raise.
- **The meta rules** in rules/platform.yml catch failed reloads, failed notifications, Loki refusing logs and scrapes close to their timeout.
- **An outside probe** of https://grafana.example.com/api/health from a second site, so you learn when the monitoring host itself is unreachable.

### Alert hygiene

Every alert carries a severity, a summary and a runbook_url, and has an owner who would act on it. Page only on what users feel (a failed probe, a 5xx ratio, a disk that fills within 24 hours); send causes such as CPU or memory as tickets. Once a month, list the alerts that fired, and delete or fix the ones nobody acted on. Entry 8.4 covers the mechanics; [SLIs, SLOs and error budgets](32-learn-performance-observability.md#15-slis-slos-and-error-budgets) covers what to alert on.

### Config as code with GitLab CI

```yaml
# .gitlab-ci.yml - nothing reaches Dokploy unless these pass
stages: [validate]

prometheus:
  stage: validate
  image: {name: "prom/prometheus:v3.13.4", entrypoint: [""]}
  script:
    - promtool check config prometheus/prometheus.yml
    - promtool check rules prometheus/rules/*.yml
    - promtool test rules tests/*.yml

alertmanager:
  stage: validate
  image: {name: "prom/alertmanager:v0.34.1", entrypoint: [""]}
  script:
    - amtool check-config alertmanager/alertmanager.yml
    - amtool config routes test --config.file=alertmanager/alertmanager.yml --verify.receivers=ops-teams severity=page alertname=TargetDown host=dokploy-1

alloy:
  stage: validate
  image: {name: "grafana/alloy:v1.20.0", entrypoint: [""]}
  script:
    - alloy fmt alloy/config.alloy > /dev/null
```

```yaml
# tests/host_test.yml - a broken rule fails the pipeline instead of staying silent in production
rule_files: [../prometheus/rules/host.yml]
evaluation_interval: 30s
tests:
  - interval: 30s
    input_series:
      - series: 'node_filesystem_avail_bytes{host="dokploy-1",mountpoint="/",fstype="ext4"}'
        values: '10x30'
      - series: 'node_filesystem_size_bytes{host="dokploy-1",mountpoint="/",fstype="ext4"}'
        values: '100x30'
    alert_rule_test:
      - eval_time: 12m
        alertname: DiskAbove85Percent
        exp_alerts:
          - exp_labels: {severity: ticket, host: dokploy-1, mountpoint: /, fstype: ext4}
            exp_annotations: {summary: "dokploy-1 / is 90% full"}
```

Loki images from 3.5.8 have no shell, so a GitLab job cannot run a script inside them. Validate the Loki file on a Docker host before merging instead: `docker run --rm -v "$PWD/loki:/etc/loki:ro" grafana/loki:3.7.8 -config.file=/etc/loki/loki.yml -verify-config`. The pipeline patterns themselves are in the [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

## 4. Learning path

KodeKloud covers Prometheus and Alertmanager in depth (PCA), Loki with Alloy (Grafana Loki) and Elasticsearch with Fluent Bit (EFK). It has nothing on Zabbix, Uptime Kuma, Netdata or Graylog, so for those the path is the official docs plus the entries here.

| Stage | Learn | Practise | Exit check |
|---|---|---|---|
| Fresher (L0) | [*DevOps Pre-Requisite Course*](https://kodekloud.com/courses/devops-pre-requisite-course) (Networking Basics, DNS); [*Docker Training Course for the Absolute Beginner*](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner) (Docker Networking, Docker Compose); LFCS lesson [*Locate and Analyze System Log Files*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page) | Uptime Kuma checking five URLs; the [32 §17](32-learn-performance-observability.md#17-homelab-lab-full-monitoring-stack) homelab lab | explain what each container does and why localhost inside Grafana is not the host |
| Junior (L1) | PCA *Prometheus Fundamentals* (notes: [Prometheus Basics](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Prometheus-Basics), [Node Exporter](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page), [Monitoring Containers](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Monitoring-Containers/page)); the [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) tutorial | build section 2 on a test VM; add dokploy-2 as a target | fix entries 5.1, 5.3, 6.2 and 6.4 in under 15 minutes each |
| Mid-level (L2) | PCA *PromQL* and *Alerting*; [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) (Grafana Loki Essentials, the LogQL labs); DCA [*Logging Driver*](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page) | write the rules and routes yourself; send pages and tickets to different receivers; ship journald and Docker logs | prove with timestamps why a notification arrived late (8.4); a week with zero discarded Loki samples |
| Senior (L3) | PCA *Service Discovery and relabeling* and *Monitoring Kubernetes*; [*Certified Kubernetes Administrator (CKA)*](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator) (Logging & Monitoring); [*Helm for Beginners*](https://kodekloud.com/courses/helm-for-beginners); optional [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) | the CI checks in section 3; dockerswarm_sd for Dokploy apps (5.7); kube-prometheus-stack on a kubeadm lab (11.3) | upgrade Prometheus, Grafana and Loki on staging with a written rollback |
| Senior/Lead (L4) | [*Fundamentals of SRE*](https://kodekloud.com/courses/fundamentals-of-sre) (Service Level Objectives and Measurements, Incident Management, [Performance Monitoring Deep Dive](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page)); [Career ladder](40-career-ladder.md) | the ops-ladder L4 game day; a monthly alert review; a cardinality budget per team | an SLO with a burn-rate alert, a tested dead man's switch, and a timed rebuild of the stack from Git |

Free practice: the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), [Docker playground](https://kodekloud.com/playgrounds/playground-docker), [Kubernetes multi-cluster playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster) and [Helm playground](https://kodekloud.com/playgrounds/playground-helm), plus the monitoring tasks in [100 Days of DevOps](https://kodekloud.com/100-days-of-devops). For Kubernetes, watch KodeKloud's [*Kubernetes Monitoring Made Easy with Prometheus*](https://www.youtube.com/watch?v=6xmWr7p5TE0) (68 minutes) before entry 11.3. The PCA course is also the best preparation for the Prometheus Certified Associate exam if you want the certificate on your CV.

---

The problem library starts here. Sections 5 to 11 run from first-week problems to platform-level ones; each entry stands on its own.

## 5. Targets and exporters

### 5.1 Target DOWN: refused or deadline exceeded

> **Seen as:** `connect: connection refused`, `context deadline exceeded` or `server returned HTTP status 401 Unauthorized` in the Error column of Status > Targets · **Where:** Prometheus in a container (Compose or Dokploy) scraping node_exporter on the host, Docker's metrics on :9323 or exporters on other servers · **Level:** [L1 · Junior] · **How common:** the classic first-week problem; a Prometheus GitHub discussion, a dev.to write-up and a Cloudron forum thread all describe the same UFW-on-the-Docker-bridge trap, and "context deadline exceeded" is one of the most searched target errors

**Why it happens:** the error word tells you the layer. *Refused* means the packet arrived and nothing listened: inside a container, localhost is the container itself, or the exporter listens on 127.0.0.1 only (`--web.listen-address=127.0.0.1:9100`, or `"metrics-addr": "127.0.0.1:9323"` for Docker). *Deadline exceeded* means no answer in time: UFW's default deny drops packets that arrive from a Docker bridge (docker0, a br-xxxx network, docker_gwbridge for Swarm services) at a host port, because Docker's NAT rules bypass UFW only for published container ports. A scrape slower than scrape_timeout (huge /metrics, a slow textfile script, a hung NFS mount) looks the same. A 4xx status means the scheme, path or credentials are wrong.

**Diagnose:**

```bash
# 1. The same path the scrape takes, from inside the Prometheus container
docker exec "$(docker ps -qf name=prometheus)" wget -qO- -T 5 http://host.docker.internal:9100/metrics | head -2
# 2. On the target: who listens, on which address?
sudo ss -Hltnp 'sport = :9100'
# 3. Did UFW drop it? SRC is the address you must allow
sudo journalctl -k --since '10 min ago' | grep 'UFW BLOCK' | grep 'DPT=9100' | tail -1
# 4. Slow rather than blocked?
curl -s -o /dev/null -w '%{time_total}s\n' http://localhost:9100/metrics
```

```text
wget: download timed out
LISTEN 0 4096 *:9100 *:* users:(("node_exporter",pid=1187,fd=3))
Oct 03 09:14:02 dokploy-1 kernel: [UFW BLOCK] IN=br-5f2c1a9e7b31 OUT= SRC=172.30.0.2 DST=172.17.0.1 LEN=60 TTL=64 PROTO=TCP SPT=48122 DPT=9100 SYN
0.041s
```

**What the output tells you:** node_exporter listens on all addresses and answers locally in 41 ms, so it is neither down nor slow. The kernel log shows UFW dropping SYN packets from 172.30.0.2, the Prometheus container on network "monitoring", which is why the scrape times out instead of being refused. A *refused* error with a LISTEN line on 127.0.0.1:9100 would point at the listen address instead.

**Fix:**

```bash
# Allow exactly the source the log printed: one Docker network, one port
sudo ufw allow proto tcp from 172.30.0.0/24 to any port 9100 comment 'prometheus -> node_exporter'
# Prometheus side: never localhost for host services; host.docker.internal needs
#   extra_hosts: ["host.docker.internal:host-gateway"] on the Prometheus service
# A slow exporter: give that job more time, keeping the timeout below the interval
#   scrape_interval: 30s
#   scrape_timeout: 25s
# HTTPS or protected exporters: scheme: https, tls_config.ca_file, and basic_auth or authorization
```

**Why this fix works:** the rule opens one port to one subnet, so Prometheus gets through and everyone else still meets the default deny. host.docker.internal resolves to the host's bridge address, which is the host as seen from a container. Don't "fix" it by publishing the exporter with `-p 9100:9100`: published ports skip UFW and the exporter becomes public. Don't disable UFW either.

**Prevent it:** the TargetDown and ScrapeNearTimeout alerts from section 2, commented UFW rules kept in Git or Ansible, and a rule that exporters are never published with -p.

**Next step:** [Who owns this port?](22-playbook-ports-inventory.md) · [Docker networking](30-learn-docker.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals · LFCS [*Configure Packet Filtering (Firewall)*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall) · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [prometheus/prometheus discussion #9678](https://github.com/prometheus/prometheus/discussions/9678) · [dev.to: the Docker networking gotcha in a self-hosted monitoring stack](https://dev.to/muhammadkamrankabeeross/the-docker-networking-gotcha-nobody-warns-you-about-when-building-a-self-hosted-monitoring-stack-54c5) · [Cloudron forum: Prometheus can't reach node exporter](https://forum.cloudron.io/topic/13280/prometheus-can-t-reach-node-exporter-blocked-traffic) · Search: [Stack Overflow](https://stackoverflow.com/search?q=prometheus+docker+node_exporter+%22context+deadline+exceeded%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=ufw+docker+node_exporter&restrict_sr=1)

### 5.2 Prometheus won't start or ignores edits

> **Seen as:** `open /prometheus/queries.active: permission denied`, `opening storage failed: lock DB directory: resource temporarily unavailable`, `yaml: unmarshal errors`, or a rule you changed that still fires the old way · **Where:** a fresh Prometheus container with a bind-mounted data directory, or a running one after edits to prometheus.yml or the rules, in Compose or Dokploy · **Level:** [L1 · Junior] · **How common:** #5976 (queries.active permission denied) and #3441 (the image running as nobody) are on the first page of Prometheus issues sorted by reactions

**Why it happens:** the image runs as nobody (UID 65534), so a root-owned host directory is not writable. Two Prometheus processes on one data directory fight over the lock: an old container still running, a second Compose project on the same volume, or a Swarm update with order start-first. YAML mistakes (tabs, indentation, a key under the wrong parent) stop the start. Edits that "do nothing" have three usual causes: no reload was sent (POST /-/reload needs `--web.enable-lifecycle`; otherwise SIGHUP or a restart); a single-file bind mount kept the old inode after vim or `sed -i` wrote a new file; or, on Dokploy, the code directory was re-cloned under a running container that now reads a stale or empty copy.

**Diagnose:**

```bash
docker ps -a --filter volume=observability_prometheus-data --format '{{.Names}} {{.Status}}'
docker logs --tail 20 prom-test-prometheus-1 2>&1 | grep 'level=ERROR'      # the one that restarts
docker run --rm -v "$PWD/prometheus:/cfg:ro" --entrypoint promtool prom/prometheus:v3.13.4 check config /cfg/prometheus.yml
curl -s localhost:9090/api/v1/query --data-urlencode 'query=prometheus_config_last_reload_successful' | jq -r '.data.result[0].value[1]'
```

```text
observability-prometheus-1 Up 3 hours
prom-test-prometheus-1 Restarting (1) 10 seconds ago
time=2026-10-03T09:20:11.402Z level=ERROR source=main.go msg="Fatal error" err="opening storage failed: lock DB directory: resource temporarily unavailable"
Checking /cfg/prometheus.yml
  SUCCESS: 2 rule files found
 SUCCESS: /cfg/prometheus.yml is valid prometheus config file syntax
1
```

**What the output tells you:** the config is valid and the running instance reloaded fine (1), but a second container from another Compose project mounts the same volume. It cannot take the TSDB lock and restarts in a loop. With a bind-mounted directory, `ls -ln` would show whether the owner is 65534; anything else explains the permission error.

**Fix:**

```bash
docker rm -f prom-test-prometheus-1                         # one Prometheus per data directory, ever
sudo chown -R 65534:65534 /srv/prometheus/data              # bind-mounted data only
docker kill --signal=HUP observability-prometheus-1    # reload without the lifecycle API
```

```yaml
# Swarm or Dokploy stack services that own a data directory: stop the old task first
deploy:
  update_config:
    order: stop-first
# Config files: mount a directory, never a single file; on Dokploy bake them into the image (section 2)
```

**Why this fix works:** the lock exists so that two writers cannot corrupt the same blocks, so the only real fix is one writer. SIGHUP makes Prometheus re-read the files it can see, which is why those files must be current: directory mounts follow an editor's rename-and-replace, and an image rebuilt on every deploy cannot go stale. Never delete the lock file to force a second instance in.

**Prevent it:** `promtool check config` and `promtool check rules` in CI (section 3), the PrometheusConfigReloadFailed alert, and stop-first updates for every stateful service.

**Next step:** [Docker storage and bind mounts](30-learn-docker.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 10.1 · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals ([Prometheus Basics notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Prometheus-Basics)) · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [Prometheus issues sorted by reactions (#5976, #3441)](https://github.com/prometheus/prometheus/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow: queries.active](https://stackoverflow.com/search?q=%22queries.active%22+permission+denied+prometheus) · [Stack Overflow: lock DB directory](https://stackoverflow.com/search?q=prometheus+%22lock+DB+directory%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=prometheus+config+reload+not+applied&restrict_sr=1)

### 5.3 node_exporter: wrong disks, missing units

> **Seen as:** the only filesystems are /etc/hostname, /etc/hosts and /etc/resolv.conf; DiskAbove85Percent fires for a snap or tmpfs mount nobody can clean; `node_systemd_unit_state` is missing, so SystemdUnitFailed can never fire · **Where:** Ubuntu hosts monitored for disk above 85% and failed units (the ops-ladder L4 drill), node_exporter in Docker or from the Ubuntu package · **Level:** [L1 · Junior] · **How common:** "Does not work so great inside a docker container" (#66, 47 comments) and "Systemd service metrics missing" (#1082, 42 comments) are among node_exporter's most-commented issues

**Why it happens:** in a container without the host's PID namespace, network and root filesystem, node_exporter reports the container's own view, and the only "disks" it sees are the files Docker bind-mounts into every container. The systemd collector (like the processes collector) is off by default, and in a container it also needs the D-Bus socket. Snap packages mount squashfs images that are always 100% full, and tmpfs or overlay mounts show up unless filtered; the older node_exporter in Ubuntu's package excludes fewer filesystem types than upstream. A hung NFS mount makes the filesystem collector time out the whole scrape.

**Diagnose:**

```bash
docker inspect -f '{{.HostConfig.NetworkMode}} pid={{.HostConfig.PidMode}} args={{join .Args " "}}' node-exporter
curl -s localhost:9100/metrics | grep '^node_filesystem_avail_bytes' | grep -o 'mountpoint="[^"]*"'
curl -s localhost:9100/metrics | grep -c '^node_systemd_unit_state'
docker logs node-exporter 2>&1 | grep -m1 'name=systemd'
```

```text
bridge pid= args=--collector.systemd
mountpoint="/etc/hostname"
mountpoint="/etc/hosts"
mountpoint="/etc/resolv.conf"
0
time=2026-10-03T09:31:40.118Z level=ERROR source=collector.go msg="collector failed" name=systemd err="couldn't get dbus connection: dial unix /var/run/dbus/system_bus_socket: connect: no such file or directory"
```

**What the output tells you:** the exporter runs on a bridge network without the host's PID namespace or root filesystem, so the real / and /var/lib/docker are invisible and a full disk would never alert. The systemd collector is enabled but cannot reach D-Bus, so the failed-unit alert can never fire. And since `curl localhost:9100` works from the host, it was published with -p, which also made it public.

**Fix:**

```yaml
# The lines that make node_exporter see the host (the full service is in section 2)
network_mode: host
pid: host
command: ["--path.rootfs=/host", "--collector.systemd"]
volumes:
  - /:/host:ro,rslave
  - /run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket:ro
# remove any ports: entry - with host networking it listens on the host, behind UFW
```

```bash
# Ubuntu package instead of a container: set one line in /etc/default/prometheus-node-exporter
#   ARGS="--collector.systemd --collector.filesystem.fs-types-exclude=^(tmpfs|squashfs|overlay|nsfs|ramfs|autofs)$"
#   (the flag replaces the built-in exclude list, so also keep the types that list already had,
#    as printed by "prometheus-node-exporter --help", for example iso9660 and the other pseudo filesystems)
sudo systemctl restart prometheus-node-exporter
curl -s localhost:9100/metrics | grep -c '^node_systemd_unit_state'     # no longer 0
```

**Why this fix works:** `--path.rootfs` makes the collectors read the host's mount table and /proc, host networking gives it the real interfaces, and the D-Bus socket lets the systemd collector list units. Filtering pseudo filesystems, in the rule as in section 2 or at the source, removes alerts nobody can act on. Don't silence the disk alert instead, or the real / fills up unseen; and keep a unit-include list, because the full systemd collector adds many series.

**Prevent it:** one shared host rule file in Git, tested the way the ops-ladder drill does: fill a test VM's disk with fallocate, stop a unit, and watch both alerts fire.

**Next step:** [Disk & storage](01-storage-disk.md) · [Services & systemd](07-services-systemd.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals ([Node Exporter notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page)) · [node_exporter README](https://github.com/prometheus/node_exporter)

**Community threads:** [node_exporter issues sorted by comments (#66 Docker, #1082 systemd)](https://github.com/prometheus/node_exporter/issues?q=is%3Aissue+sort%3Acomments-desc) · [node_exporter README: Docker flags](https://github.com/prometheus/node_exporter) · Search: [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=node_exporter+snap+squashfs&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=node_exporter+docker+path.rootfs+filesystem)

### 5.4 blackbox: probe fails, site works

> **Seen as:** ProbeFailed (`probe_success 0`) for https://harbor.example.com while the site opens fine in a browser; the debug log shows `connect: network is unreachable` to an IPv6 address, `x509: certificate signed by unknown authority`, or ICMP `socket: operation not permitted` · **Where:** blackbox_exporter in a container probing internal sites behind Traefik (Harbor, GitLab, Grafana) and pinging hosts · **Level:** [L2 · Mid-level] · **How common:** a classic Stack Overflow and Reddit question; the blackbox README documents debug=true and the ICMP permissions because they come up constantly

**Why it happens:** the HTTP prober prefers IPv6 by default, so a name with an AAAA record fails on a host without an IPv6 route. The exporter does not trust your private CA. ICMP needs CAP_NET_RAW, root or a wide `net.ipv4.ping_group_range`. Or the relabel pattern is missing (entry 5.6), or the app answers 302 or 401 while the module expects 2xx.

**Diagnose:**

```bash
# Ask blackbox directly; debug=true prints every step of the probe
docker exec "$(docker ps -qf name=prometheus)" wget -qO- \
  'http://blackbox:9115/probe?target=https://harbor.example.com&module=http_2xx&debug=true' \
  | grep -E 'msg=|^probe_success|^probe_ip_protocol'
```

```text
time=2026-10-03T09:40:11.102Z level=INFO source=utils.go msg="Resolving target address" target=harbor.example.com ip_protocol=ip6
time=2026-10-03T09:40:11.104Z level=INFO source=utils.go msg="Resolved target address" target=harbor.example.com ip=2001:db8:10::25
time=2026-10-03T09:40:11.105Z level=ERROR source=http.go msg="Error for HTTP request" err="Get \"https://[2001:db8:10::25]\": dial tcp [2001:db8:10::25]:443: connect: network is unreachable"
probe_ip_protocol 6
probe_success 0
```

**What the output tells you:** the name resolves to an IPv6 address first and this host has no IPv6 route, so every probe dies before TLS starts. With IPv4 preferred, the next run reaches TLS; an x509 error at that point would mean the module lacks your CA file.

**Fix:**

```yaml
# blackbox.yml (excerpt from section 2) - and send internal targets to this module, not http_2xx
  http_internal:
    prober: http
    http:
      preferred_ip_protocol: ip4
      valid_status_codes: [200, 301, 302, 401]   # Harbor and GitLab answer 401 or 302 without a login
      tls_config:
        ca_file: /etc/blackbox/internal-ca.crt
```

```bash
# ICMP: cap_add: [NET_RAW] on the container (section 2), or for a host binary:
sudo setcap cap_net_raw+ep /usr/local/bin/blackbox_exporter
```

**Why this fix works:** preferring IPv4 matches what the network can route, the CA file lets the probe verify the chain the way a browser with your CA installed does, and NET_RAW is the one capability ICMP sockets need. Never set `insecure_skip_verify: true` to turn a probe green: the chain and expiry checks are half the reason you probe.

**Prevent it:** test every new module with debug=true before adding targets, keep the ProbeFailed and CertificateExpiresSoon rules, and probe the important sites from a second location too (entry 7.1).

**Next step:** [Web, HTTP & TLS](18-web-http-tls.md) · [Site down](25-playbook-site-down.md) · KodeKloud: *DevOps Pre-Requisite Course* — SSL & TLS Basics · [blackbox_exporter README](https://github.com/prometheus/blackbox_exporter)

**Community threads:** [blackbox_exporter README: debug, ICMP permissions, relabel pattern](https://github.com/prometheus/blackbox_exporter) · Search: [Stack Overflow](https://stackoverflow.com/search?q=blackbox+exporter+probe_success+0) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=blackbox+exporter+icmp+docker&restrict_sr=1)

### 5.5 cAdvisor blank after Docker 29, or eating CPU

> **Seen as:** container dashboards empty after an `apt upgrade`; cAdvisor logs `client version 1.41 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version`; or cAdvisor itself uses 5 to 15% CPU · **Where:** Ubuntu Docker hosts upgraded to Docker Engine 29 (November 2025) with cAdvisor pinned to an older release such as 0.49.1, or busy hosts scraped every few seconds · **Level:** [L2 · Mid-level] · **How common:** cAdvisor #3749 "Failure to get data in Prometheus on latest Docker" (November 2025) is among its most-reacted issues; #2523 on high CPU usage has more than 50 reactions

**Why it happens:** Docker Engine 29 refuses API versions older than 1.44, and cAdvisor 0.49.1 asks for 1.41, so it loses container names and labels. Docker 29 also makes the containerd image store the default on fresh installs, which older cAdvisor builds read less well. High CPU comes from the defaults: frequent housekeeping, every metric family, disk-usage scans of every container layer, and every Docker label exported as a Prometheus label.

**Diagnose:**

```bash
docker version --format 'server {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'
docker logs --tail 50 cadvisor 2>&1 | grep -m1 'too old'
curl -s localhost:8089/metrics | grep -c 'container_last_seen{.*name="[^"]'
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}}' cadvisor
```

```text
server 29.0.4 api 1.52 min 1.44
W1003 09:52:10.441120       1 manager.go:1116] Failed to create existing container: ... Error response from daemon: client version 1.41 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version
0
cadvisor 11.62%
```

**What the output tells you:** the engine's minimum API is 1.44 and cAdvisor still asks for 1.41, so not one container series carries a name any more. The CPU figure is a second, separate problem: default settings on a host with many containers.

**Fix:**

```bash
# 1. Hold the engine while you upgrade cAdvisor
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
# 2. Set CADVISOR_IMAGE to a current release from the cAdvisor releases page and redeploy the agents app
# 3. Keep the cost down: the section 2 flags (--docker_only, --housekeeping_interval=30s,
#    --disable_metrics=..., --store_container_labels=false) and a 30s scrape interval
# 4. Once names are back, release the hold so security updates flow again
sudo apt-mark unhold docker-ce docker-ce-cli containerd.io
```

**Why this fix works:** a newer cAdvisor negotiates an API version the engine accepts, so names and labels return. Fewer metric families, slower housekeeping and a whitelist of three labels cut its CPU and your series count; the reporter of #2523 roughly halved CPU by scraping less often. Don't downgrade Docker to keep an old cAdvisor alive: engine security fixes matter more than a dashboard.

**Prevent it:** read Docker's release notes before upgrading monitored hosts, pin both versions, and alert when names vanish: `absent(container_last_seen{job="cadvisor", name!=""})`. If you built the [32 §17](32-learn-performance-observability.md#17-homelab-lab-full-monitoring-stack) lab with cAdvisor 0.49.1, this is the entry that bites it on Docker 29.

**Next step:** [Docker](30-learn-docker.md) · [Slow system](23-playbook-slow-system.md) (container slow, host fast) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals ([Monitoring Containers notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Monitoring-Containers/page)) · [cAdvisor README](https://github.com/google/cadvisor)

**Community threads:** [google/cadvisor #3749](https://github.com/google/cadvisor/issues/3749) · [Docker Engine 29 release notes](https://docs.docker.com/engine/release-notes/29/) · [google/cadvisor #2523](https://github.com/google/cadvisor/issues/2523) · Search: [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=cadvisor+%22client+version%22+too+old&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=cadvisor+%22client+version+1.41+is+too+old%22)

### 5.6 Relabeling does nothing or drops targets

> **Seen as:** no error at all: three probe targets configured but one shown, every target labelled `instance="blackbox:9115"`, a job with 0/0 up, or a label you added that never appears · **Where:** adding service discovery (file_sd, docker, dockerswarm, kubernetes) or the blackbox pattern, and shaping labels · **Level:** [L2 · Mid-level] · **How common:** a staple Stack Overflow topic; the blackbox README and the Docker Swarm guide exist largely to show correct relabel patterns

**Why it happens:** `relabel_configs` runs before the scrape, on target labels (`__address__`, `__meta_*`), and decides which targets exist. `metric_relabel_configs` runs after the scrape, on every sample, and cannot see `__meta_*`. Rules run top to bottom over one label set. Labels starting with `__` are dropped after target relabeling unless copied, regexes are fully anchored, several source labels are joined with `;`, `action: keep` drops everything that does not match, and a scraped label that clashes with a target label is renamed to `exported_` plus its name unless honor_labels is set.

**Diagnose:**

```bash
curl -s 'localhost:9090/api/v1/targets?state=active' \
  | jq -r '.data.activeTargets[] | select(.labels.job=="probe-public") | "\(.scrapeUrl) \(.labels.instance)"'
grep -A9 'job_name: probe-public' prometheus/prometheus.yml | grep -E 'source_labels|target_label|replacement'
```

```text
http://blackbox:9115/probe?module=http_2xx&target=blackbox%3A9115 blackbox:9115
      - target_label: __address__
        replacement: blackbox:9115
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
```

**What the output tells you:** the first rule already replaced `__address__` with the exporter's address, so every target copied "blackbox:9115" into `__param_target`. Three targets collapsed into one identical label set, and blackbox now probes itself, successfully, which is why nothing turns red.

**Fix:**

```yaml
relabel_configs:
  - source_labels: [__address__]       # 1. remember the real target
    target_label: __param_target
  - source_labels: [__param_target]    # 2. keep it visible as instance
    target_label: instance
  - target_label: __address__          # 3. only now point the scrape at blackbox
    replacement: blackbox:9115
# Discovery metadata disappears after relabeling: copy what you need into real labels
#  - action: labelmap
#    regex: __meta_docker_container_label_com_docker_compose_(service|project)
```

**Why this fix works:** relabeling is an ordered pipeline, so the real address must be saved before it is overwritten, and labelmap copies metadata into permanent labels while it still exists. Filter targets only in relabel_configs and drop metrics only in metric_relabel_configs; change one rule at a time and re-check Status > Service discovery, which shows discovered labels next to the final ones.

**Prevent it:** a comment on each rule stating its intent, the dropped-target count (`/api/v1/targets?state=dropped`) after every discovery change, and `count by (job) (up)` compared with the number of targets you expect.

**Next step:** [Performance & observability: Prometheus](32-learn-performance-observability.md#11-prometheus) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Service Discovery and relabeling · [Prometheus guide: Docker Swarm](https://prometheus.io/docs/guides/dockerswarm/)

**Community threads:** [blackbox_exporter README: the multi-target pattern](https://github.com/prometheus/blackbox_exporter) · [Prometheus guide: Docker Swarm relabel examples](https://prometheus.io/docs/guides/dockerswarm/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=relabel_configs+metric_relabel_configs+difference) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=relabel_configs+blackbox+instance&restrict_sr=1)

### 5.7 Dokploy services and Traefik not discovered

> **Seen as:** a `dockerswarm_sd_configs` job finds 0 targets; half the targets are 10.0.0.x addresses that time out; `http://dokploy-traefik:8082/metrics` answers 404 · **Where:** Dokploy applications run as Swarm services on dokploy-network behind Traefik, and you want per-app and Traefik metrics without hard-coded IPs · **Level:** [L3 · Senior] · **How common:** Swarm discovery was a long-standing top request (#1766) until Prometheus 2.20 shipped it; Dokploy users meet this as soon as they want per-app metrics

**Why it happens:** dockerswarm_sd needs a manager's Docker API. A task yields one target per attached network, including the ingress network (10.0.0.0/24 by default) that Prometheus cannot reach, so without a network filter half the targets time out. The port Swarm reports is not necessarily the app's metrics port. Only Dokploy *applications* and Compose apps of type Stack are Swarm services; plain Compose containers need docker_sd_configs instead. For Traefik, /metrics exists only on the entryPoint metrics are bound to, so with metrics off or bound elsewhere you get 404.

**Diagnose:**

```bash
docker node ls --format '{{.Hostname}} {{.ManagerStatus}}'
curl -s 'localhost:9090/api/v1/targets?state=active' | jq -r '.data.activeTargets[]
  | select(.labels.job=="shop-web") | "\(.discoveredLabels.__meta_dockerswarm_network_name) \(.scrapeUrl) \(.health)"'
docker exec "$(docker ps -qf name=prometheus)" wget -qO- -T 5 http://dokploy-traefik:8082/metrics | head -1
```

```text
dokploy-1 Leader
dokploy-2
ingress http://10.0.0.14:3000/metrics down
dokploy-network http://10.0.1.23:3000/metrics up
wget: server returned error: HTTP/1.1 404 Not Found
```

**What the output tells you:** dokploy-2 is a worker, so discovery must use dokploy-1's API. Each task appears twice, once per network; the ingress copy can never be reached, the dokploy-network copy works. Traefik answers 404 on 8082 because metrics are not yet enabled on that entryPoint.

**Fix:**

```yaml
# prometheus.yml - Dokploy applications that carry service labels prometheus-job and prometheus-port
  - job_name: swarm-tasks
    dockerswarm_sd_configs:
      - host: tcp://socket-proxy:2375            # read-only proxy in front of the manager's socket
        role: tasks
    relabel_configs:
      - source_labels: [__meta_dockerswarm_task_desired_state]
        regex: running
        action: keep
      - source_labels: [__meta_dockerswarm_service_label_prometheus_job]
        regex: .+
        action: keep
      - source_labels: [__meta_dockerswarm_network_name]
        regex: dokploy-network                   # exactly one reachable target per task
        action: keep
      - source_labels: [__address__, __meta_dockerswarm_service_label_prometheus_port]
        regex: '([^:]+)(?::\d+)?;(\d+)'
        target_label: __address__
        replacement: $1:$2
      - source_labels: [__meta_dockerswarm_service_label_prometheus_job]
        target_label: job
      - source_labels: [__meta_dockerswarm_service_name]
        target_label: service
```

```yaml
# docker-compose.yml (central stack) - Prometheus may only read services, tasks, nodes and networks
  socket-proxy:
    image: tecnativa/docker-socket-proxy:VERSION   # pin a release tag
    environment: {SERVICES: 1, TASKS: 1, NODES: 1, NETWORKS: 1}
    volumes: ["/var/run/docker.sock:/var/run/docker.sock:ro"]
    networks: [monitoring]
```

Give each app the service labels prometheus-job=APP and prometheus-port=PORT (in a stack file under `deploy.labels`, not top-level `labels`, which land on containers). Then enable Traefik's metrics entryPoint as in section 2 and restart dokploy-traefik.

**Why this fix works:** discovery reads the live task list from a manager, the network filter keeps one reachable address per task, and the port label tells Prometheus where /metrics lives, so new replicas and nodes are scraped without editing a file. The socket proxy limits Prometheus to read-only calls, whereas a raw docker.sock mount is root on the host. Never publish 8082, and never use container names or task IDs as labels: they change on every deploy.

**Prevent it:** put the two labels on every Dokploy app's checklist, alert on `up == 0` per job, and graph the target count per job so a missing app is visible.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) (3.4 Metrics and alerts) · KodeKloud: *Docker Certified Associate* — Docker Swarm · *Prep Course - Prometheus Certified Associate (PCA)* — Service Discovery and relabeling · [Prometheus guide: Docker Swarm](https://prometheus.io/docs/guides/dockerswarm/)

**Community threads:** [Prometheus guide: Monitoring Docker Swarm](https://prometheus.io/docs/guides/dockerswarm/) · [Traefik v3 metrics reference](https://doc.traefik.io/traefik/reference/install-configuration/observability/metrics/) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+prometheus+grafana&restrict_sr=1) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=prometheus+metrics+entrypoint&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=prometheus+dockerswarm_sd_configs+ingress+network)

## 6. Grafana: access, data sources and dashboards

### 6.1 Grafana won't start or the password is lost

> **Seen as:** `GF_PATHS_DATA='/var/lib/grafana' is not writable.` and `mkdir: can't create directory '/var/lib/grafana/plugins': Permission denied`, or `Invalid username or password` with the password from the Compose file · **Where:** a new Grafana container with a bind-mounted data directory, or an old one whose admin password nobody remembers · **Level:** [L0 · Fresher] · **How common:** "Admin password reset" is the most-viewed topic on community.grafana.com (about 233k views); "New Docker Install with persistent storage, Permission problem" has about 121k

**Why it happens:** the image runs as UID 472 (group 0), so a host directory owned by root or by your user is not writable. `GF_SECURITY_ADMIN_PASSWORD` is applied only on the very first start, when the database is created; after that the database holds the password and changing the variable does nothing. Repeated failed logins also trigger brute-force protection for a few minutes.

**Diagnose:**

```bash
docker logs grafana 2>&1 | grep -E 'not writable|Permission denied' | head -2
ls -lnd /srv/grafana
```

```text
GF_PATHS_DATA='/var/lib/grafana' is not writable.
mkdir: can't create directory '/var/lib/grafana/plugins': Permission denied
drwxr-xr-x 2 0 0 4096 Oct  3 10:02 /srv/grafana
```

**What the output tells you:** the data directory belongs to root (UID 0) and Grafana runs as 472, so it cannot even create its plugins folder. A login failure on a healthy container is the other case: the database already holds an older password.

**Fix:**

```bash
sudo chown -R 472:0 /srv/grafana            # or use a named volume, as in section 2
# Lost admin password: reset it in the container ("grafana cli" replaces the deprecated grafana-cli)
read -rsp 'New admin password: ' PW && docker exec grafana grafana cli admin reset-admin-password "$PW"; unset PW
# Package install on a host: name the real config and data path, or the CLI can update a different grafana.db
sudo grafana cli --homepath /usr/share/grafana --config /etc/grafana/grafana.ini \
  --configOverrides cfg:default.paths.data=/var/lib/grafana admin reset-admin-password 'NEW_PASSWORD'
```

**Why this fix works:** ownership 472:0 matches the user the image runs as, and the CLI writes the new password hash straight into the database the login checks. Never `chmod 777` the data directory, and don't delete grafana.db to "reset" the password unless you mean to lose every user, dashboard and alert stored in it.

**Prevent it:** named volumes, personal accounts or SSO instead of a shared admin, and the bootstrap password kept in your secret store.

**Next step:** [Users, permissions & security](10-users-permissions-security.md) · [Docker](30-learn-docker.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [Grafana server CLI](https://grafana.com/docs/grafana/latest/administration/cli/)

**Community threads:** [Grafana community: Admin password reset](https://community.grafana.com/t/admin-password-reset/19455) · [Grafana community: Docker install with persistent storage, permission problem](https://community.grafana.com/t/new-docker-install-with-persistent-storage-permission-problem/10896) · [Grafana configuration docs](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+docker+%22GF_PATHS_DATA%22+not+writable) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=reset+admin+password+docker&restrict_sr=1)

### 6.2 Panels show No data, gaps or odd zeros

> **Seen as:** a panel says No data, a stat shows No data instead of 0, a time series has gaps, or values change when you zoom · **Where:** new dashboards, and community dashboards imported onto your own Prometheus and Loki · **Level:** [L0–L1 · Fresher/Junior] · **How common:** "How to get NO DATA to 0 when there is no data value" (about 87k views) and "How can I turn no data to zero in Loki" (about 14k) on community.grafana.com; Grafana #4470 "Hide empty / no data panels" has 146 comments

**Why it happens:** the query returns no series: a counter that never incremented, a label typo, the wrong data source, a renamed job, or an imported dashboard that expects labels your setup does not have. Gaps come from rate windows shorter than two scrapes, or `$__interval` below the scrape interval. A Loki `count_over_time` returns nothing at all when no line matched.

**Diagnose:**

```bash
# Grafana first: panel menu > Inspect > Query shows the exact request and response.
# Then check the pieces with the q() helper from section 3, from the outside in
q 'up{job="node"}'
q 'count by (__name__) ({__name__=~"node_network_receive_bytes_total|http_requests_total"})'
```

```text
{"__name__":"up","host":"dokploy-1","instance":"host.docker.internal:9100","job":"node"} 1
{"__name__":"node_network_receive_bytes_total"} 12
```

**What the output tells you:** the target is up and the node metrics exist, but `http_requests_total` does not exist at all, so a panel built on it can only say No data. For an imported dashboard, compare its variables (job, instance, nodename) with your real label names.

**Fix:**

```text
# PromQL: an explicit zero when nothing matched, and a window that follows the zoom level
sum(rate(http_requests_total[$__rate_interval])) or vector(0)
# LogQL: the same idea for log counts
sum(count_over_time({service="shop-web"} |= "error" [5m])) or vector(0)
# Cosmetic only: panel > Standard options > No value = 0
```

**Why this fix works:** `or vector(0)` returns zero when the left side is empty, and `$__rate_interval` is at least four scrape intervals once the data source knows the scrape interval (timeInterval in section 2), which removes the gaps. Don't paper over a missing metric with "No value = 0" on a panel people use for decisions: a missing series is information.

**Prevent it:** alert on missing data with `absent()`, never on a panel that can be empty, and adapt the variables of imported dashboards before trusting them.

**Next step:** [Performance & observability: Grafana](32-learn-performance-observability.md#13-grafana) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — PromQL · [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/)

**Community threads:** [community.grafana.com top topics (No data to 0)](https://community.grafana.com/top?period=all) · [Grafana issues sorted by comments (#4470)](https://github.com/grafana/grafana/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+%22no+data%22+instead+of+0+prometheus) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=no+data+show+0&restrict_sr=1)

### 6.3 Grafana behind a proxy: Origin not allowed

> **Seen as:** `Origin not allowed` on save or login, "If you're seeing this Grafana has failed to load its application files", websocket errors on /api/live/ws, or a redirect to http://localhost:3000 · **Where:** Grafana published through Apache (your legacy proxy), Nginx, or Traefik in Dokploy, on a subdomain or a sub-path · **Level:** [L1 · Junior] · **How common:** "After update to 8.3.5: Origin not allowed behind proxy" (about 46k views), a 39k-view sibling thread and "How to set up Grafana HTTPS" (about 150k views) on community.grafana.com; Grafana #45261 for IIS

**Why it happens:** since 8.3.5 Grafana checks that the browser's Origin matches the Host it receives, so a proxy that does not forward the original Host header gets "Origin not allowed"; Apache needs ProxyPreserveHost On. A root_url or serve_from_sub_path that does not match the public URL breaks asset loading and redirects. Grafana Live needs the Upgrade and Connection headers on /api/live/, and TLS terminated at the proxy while root_url still says http gives mixed redirects.

**Diagnose:**

```bash
grep -nE 'ProxyPreserveHost|ProxyPass' /etc/apache2/sites-enabled/grafana.conf
docker exec grafana printenv GF_SERVER_ROOT_URL
curl -s -o /dev/null -D - https://grafana.example.com/ | grep -iE '^(HTTP|location)'
```

```text
12:    ProxyPass / http://127.0.0.1:3000/
13:    ProxyPassReverse / http://127.0.0.1:3000/
http://localhost:3000/
HTTP/1.1 302 Found
Location: /login
```

**What the output tells you:** Apache passes Host 127.0.0.1:3000 instead of grafana.example.com (no ProxyPreserveHost), so the origin check fails on every save and login. The login redirect itself is relative and works, but root_url still says http://localhost:3000, so every absolute URL Grafana builds (OAuth callbacks, share links, links in alert notifications and emails) points at an address only the server can reach.

**Fix:**

```apache
# /etc/apache2/sites-enabled/grafana.conf - needs mod_proxy, mod_proxy_http and mod_proxy_wstunnel
ProxyPreserveHost On
ProxyPass        /api/live/ ws://127.0.0.1:3000/api/live/
ProxyPassReverse /api/live/ ws://127.0.0.1:3000/api/live/
ProxyPass        / http://127.0.0.1:3000/
ProxyPassReverse / http://127.0.0.1:3000/
# Grafana: GF_SERVER_ROOT_URL=https://grafana.example.com/
# Sub-path: GF_SERVER_ROOT_URL=https://example.com/grafana/ and GF_SERVER_SERVE_FROM_SUB_PATH=true, no prefix stripping
# Nginx: proxy_set_header Host $host, plus a location /api/live/ with the Upgrade and Connection headers
```

**Why this fix works:** with the original Host forwarded, Origin and Host match again, and root_url tells Grafana which public URL to use in redirects and asset links. Traefik keeps the Host header by default, which is why the section 2 setup needs only GF_SERVER_ROOT_URL. Don't work around the error by adding origins to csrf_trusted_origins until it goes away; fix the header.

**Prevent it:** a dedicated subdomain rather than a sub-path, TLS terminated in one place, and proxy snippets kept in Git.

**Next step:** [Web servers & proxies](29-learn-webservers-proxies.md) · [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) · KodeKloud: LFCS [*Implement Reverse Proxies and Load Balancers*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page) · [Run Grafana behind a reverse proxy](https://grafana.com/tutorials/run-grafana-behind-a-proxy/)

**Community threads:** [Grafana community: Origin not allowed behind proxy after 8.3.5](https://community.grafana.com/t/after-update-to-8-3-5-origin-not-allowed-behind-proxy/60598) · [grafana/grafana #45261](https://github.com/grafana/grafana/issues/45261) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+%22origin+not+allowed%22) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=origin+not+allowed+reverse+proxy&restrict_sr=1)

### 6.4 Data source fails or Loki has no labels

> **Seen as:** `dial tcp 127.0.0.1:9090: connect: connection refused`, `lookup prometheus on 127.0.0.11:53: no such host`, `Bad Gateway`, `no org id`, or a Loki data source that connects but lists no labels · **Where:** adding Prometheus, Loki or Elasticsearch data sources in a Grafana container (Compose or Dokploy) · **Level:** [L1 · Junior] · **How common:** a daily question on r/grafana and Stack Overflow; it shares its root cause with entry 5.1

**Why it happens:** in the default (server) access mode the Grafana backend sends the query, so the URL is resolved inside the Grafana container, where localhost is Grafana itself. Containers from different Compose projects share no network unless both join one (dokploy-network or a named network). Loki with `auth_enabled: true` needs an X-Scope-OrgID header ("no org id"). A reachable Loki with no labels simply has nothing shipping logs yet, and HTTPS back ends need your private CA.

**Diagnose:**

```bash
docker exec grafana wget -qO- -T 5 http://prometheus:9090/-/ready
docker inspect grafana --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}'
docker exec grafana wget -qO- -T 5 http://loki:3100/loki/api/v1/labels    # after fixing the network
```

```text
wget: bad address 'prometheus:9090'
dokploy-network
{"status":"success","data":[]}
```

**What the output tells you:** Grafana is attached to dokploy-network only, so the name prometheus does not resolve. Once it joins "monitoring", Loki answers but has no labels: the data source is fine, and the real gap is that no agent ships logs yet (entry 9.1).

**Fix:**

```yaml
# The same network as the back ends, and service names instead of localhost
grafana:
  networks: [monitoring, dokploy-network]
# Data source URLs (provisioned in section 2): http://prometheus:9090 and http://loki:3100
# Multi-tenant Loki: add the HTTP header X-Scope-OrgID: TENANT to the data source
# HTTPS back ends: enable "With CA Cert" and paste your private CA (tlsCACert when provisioning)
```

**Why this fix works:** a shared user-defined network gives Docker's embedded DNS (127.0.0.11) a record for each service name, so the backend's request reaches the right container, and the tenant header tells a multi-tenant Loki whose data to return. Don't switch the data source to browser access to dodge the problem: then every user's browser must reach Prometheus directly, which means publishing it.

**Prevent it:** data sources provisioned from Git with fixed uids, and each data source's health endpoint probed by blackbox or Uptime Kuma.

**Next step:** [Docker networking](30-learn-docker.md) · [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Grafana docs](https://grafana.com/docs/grafana/latest/)

**Community threads:** [prometheus/prometheus discussion #9678 (container networking)](https://github.com/prometheus/prometheus/discussions/9678) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+docker+%22dial+tcp+127.0.0.1%3A9090%22+connection+refused) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=%22no+labels+were+received%22&restrict_sr=1)

### 6.5 PromQL joins and rates that mislead

> **Seen as:** `many-to-many matching not allowed: matching labels must be unique on one side`, `found duplicate series for the match group`, `vector cannot contain metrics with the same labelset`, or rates that look wrong · **Where:** dashboards and rules that join node_uname_info for host names, compute per-second rates or percentages · **Level:** [L2 · Mid-level] · **How common:** "Extract labels values from prometheus metrics" is the most-viewed Prometheus topic on community.grafana.com (about 206k views); rate and increase extrapolation (#3746, #3806) and joining different labels (#2204) are top-reacted Prometheus issues

**Why it happens:** binary operators match series on all labels, so a join needs `on()` or `ignoring()` plus `group_left` or `group_right`. The same target scraped twice (two jobs, or two file_sd files) creates duplicates that break joins. rate() needs at least two samples in its window, so windows under about four scrape intervals give gaps. Rate on a gauge, rate(sum()) instead of sum(rate()), and expecting increase() to return whole numbers (it extrapolates) all give plausible but wrong graphs.

**Diagnose:**

```bash
q 'count by (instance) (up{job=~"node.*"}) > 1'            # the same target in two jobs?
q 'count by (instance) (node_uname_info) > 1'
```

```text
{"instance":"10.10.0.20:9100"} 2
{"instance":"10.10.0.20:9100"} 2
```

**What the output tells you:** dokploy-2 is scraped by two jobs, so node_uname_info has two series for one instance and a join on instance finds two partners: that is the many-to-many error.

**Fix:**

```text
# Remove the duplicate job first, then join explicitly and copy only the label you need
rate(node_network_receive_bytes_total[5m]) * on (instance) group_left (nodename) node_uname_info
# Aggregate after rate, never before
sum by (job) (rate(http_requests_total[5m]))
# In Grafana, let the window follow the zoom level
sum by (host) (rate(node_cpu_seconds_total{mode!="idle"}[$__rate_interval]))
```

**Why this fix works:** `on (instance)` names the matching labels and `group_left (nodename)` declares the right side as the "one" side and copies nodename across, which works only once each instance exists once. rate() must see raw counter resets, which a sum would hide, so it comes first. Don't silence a join error by aggregating both sides away; you lose the dimension you wanted.

**Prevent it:** one job per target, and heavy or shared expressions turned into recording rules with promtool unit tests (section 3).

**Next step:** [Performance & observability: Prometheus](32-learn-performance-observability.md#11-prometheus) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — PromQL · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [community.grafana.com top topics](https://community.grafana.com/top?period=all) · [Prometheus issues sorted by reactions (#3746, #3806, #2204)](https://github.com/prometheus/prometheus/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22many-to-many+matching+not+allowed%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=group_left+many-to-many&restrict_sr=1)

### 6.6 Provisioning: DS_PROMETHEUS not found

> **Seen as:** `Failed to upgrade legacy queries Datasource ${DS_PROMETHEUS} was not found`, `Cannot save provisioned dashboard`, or "The dashboard has been changed by someone else" · **Where:** dashboards kept as JSON in Git and provisioned by file, Ansible, Helm or ConfigMaps · **Level:** [L2 · Mid-level] · **How common:** Grafana #10786 (dashboard variables in provisioning) and #36040, plus community threads on importing with a data source variable and on loading dashboards through Helm (about 60k views)

**Why it happens:** JSON exported for use in another instance (the "Export for sharing externally" switch in older versions) contains `__inputs` placeholders such as `${DS_PROMETHEUS}` that only the UI import dialog resolves; file provisioning loads them as they are. Provisioned dashboards are read-only unless allowUiUpdates is true, and UI edits are overwritten on the next load anyway. Data source UIDs differ between environments, two files can carry the same dashboard UID, and on Kubernetes the sidecar only loads ConfigMaps with the right label in a namespace it searches.

**Diagnose:**

```bash
docker logs grafana 2>&1 | grep 'logger=provisioning' | tail -1
grep -rln 'DS_PROMETHEUS' grafana/dashboards/
grep -rho '"uid": *"[^"]*"' grafana/dashboards/ | sort | uniq -d
```

```text
logger=provisioning.dashboard t=2026-10-03T10:12:04.511364172Z level=warn msg="the same UID is used more than once" orgId=1 uid=rYdddlPWk times=2 providers=[infra]
grafana/dashboards/Infra/traefik.json
"uid": "rYdddlPWk"
```

**What the output tells you:** traefik.json was exported for sharing and still holds the `${DS_PROMETHEUS}` placeholder, and two files carry the same dashboard UID; while that duplicate exists, Grafana stops writing dashboards from that provider, so even unrelated edits never land.

**Fix:**

```bash
# Point the placeholder at the data source uid provisioned in section 2
sed -i 's/\${DS_PROMETHEUS}/prometheus/g' grafana/dashboards/Infra/traefik.json
# Give the copied dashboard its own "uid" in its JSON, commit, deploy
# From now on: edit in the UI, export as JSON with the "another instance" / "sharing externally" switch off, commit, deploy
# Kubernetes: ConfigMaps labelled grafana_dashboard: "1" in a namespace the sidecar searches
```

**Why this fix works:** provisioning loads the JSON as written, so every reference must already point at a real data source, and a fixed uid makes the same file work in every environment. Unique dashboard UIDs let Grafana tell the files apart. Don't set allowUiUpdates to true as a workaround: the UI and Git drift apart, and the next deploy silently discards someone's edits.

**Prevent it:** Git as the source of truth, and a CI step that fails on invalid JSON, duplicate UIDs or `${DS_` placeholders. Grafana 13 also offers Git Sync, a two-way GitOps alternative to file provisioning.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · [Performance & observability: Grafana](32-learn-performance-observability.md#13-grafana) · KodeKloud: *Helm for Beginners* · [What's new in Grafana v13.0](https://grafana.com/docs/grafana/latest/whatsnew/whats-new-in-v13-0/)

**Community threads:** [grafana/grafana #10786](https://github.com/grafana/grafana/issues/10786) · [grafana/grafana #36040](https://github.com/grafana/grafana/issues/36040) · [Grafana community: dashboard import with a data source variable](https://community.grafana.com/t/dashboard-import-with-datasource-variable/4896) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+provisioning+DS_PROMETHEUS+not+found) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=provisioning+DS_PROMETHEUS&restrict_sr=1)

### 6.7 Panel plugin not found after Grafana 12

> **Seen as:** `Panel plugin not found: PLUGIN_ID`, `Error loading: PLUGIN_ID`, or a data source type missing after the upgrade · **Where:** long-lived dashboards, often imported years ago, that use AngularJS community plugins, upgraded from 10 or 11 to 12 or 13 · **Level:** [L2 · Mid-level] · **How common:** Grafana's blog post and EPIC #95822 on removing Angular, plus community threads urging migrations of plugins such as Flowcharting

**Why it happens:** AngularJS was deprecated in Grafana 9, disabled by default in 11 and removed in 12, and the `angular_support_enabled` setting no longer does anything. Core Angular panels (the old Graph, Singlestat and Table) migrate automatically, but third-party Angular plugins simply fail to load.

**Diagnose:**

```bash
docker exec grafana grafana cli plugins ls
# Before upgrading, on 11.x: Administration > Plugins marks Angular plugins as deprecated,
# and dashboards that use them show a warning icon
```

```text
installed plugins:
agenty-flowcharting-panel @ 0.9.1
grafana-piechart-panel @ 1.6.4
```

**What the output tells you:** two Angular plugins are still installed, and every panel that uses them breaks on 12 and later.

**Fix:**

```text
grafana-piechart-panel      -> core "Pie chart" panel
agenty-flowcharting-panel   -> core "Canvas" panel, or a React-based diagram plugin
old Graph and Singlestat    -> open once on 11, let them migrate to Time series and Stat, save
Rehearsal: restore last night's grafana.db into a staging Grafana 13 and open every dashboard
```

**Why this fix works:** core panels and React plugins are the only ones the current frontend loads, and a rehearsal on a copy of the database shows every broken panel before users do. Don't hold Grafana at 11 forever for one plugin: you would miss security fixes.

**Prevent it:** dashboards as code, a plugin inventory in every upgrade change request, staging first, and the major version pinned in Compose.

**Next step:** section 3, Upgrades without surprises · [Performance & observability: Grafana](32-learn-performance-observability.md#13-grafana) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [What's new in Grafana v12.0](https://grafana.com/docs/grafana/latest/whatsnew/whats-new-in-v12-0/)

**Community threads:** [Grafana blog: AngularJS support removed in Grafana 12](https://grafana.com/blog/angularjs-support-will-be-removed-in-grafana-12-what-you-need-to-know/) · [grafana/grafana #95822](https://github.com/grafana/grafana/issues/95822) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+12+%22panel+plugin+not+found%22) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=angular+plugin+grafana+12&restrict_sr=1)

### 6.8 Database is locked, or two Grafana replicas

> **Seen as:** `"failed to look up user based on cookie" logger=context error="database is locked"`, a slow UI, alert states that fail to save · **Where:** Grafana on its default SQLite database with many users and alert rules, on NFS, or scaled to two replicas in Swarm or Kubernetes · **Level:** [L3–L4 · Senior to Senior/Lead] · **How common:** grafana/grafana #16638 "Grafana Logs database is locked" is open with about 123 comments

**Why it happens:** SQLite allows one writer at a time, and alerting and sessions write constantly. A grafana.db on NFS or CIFS makes locking slow and unreliable. Two replicas sharing one SQLite file is never supported.

**Diagnose:**

```bash
docker logs grafana --since 24h 2>&1 | grep -c 'database is locked'
findmnt -T "$(docker volume inspect -f '{{.Mountpoint}}' PROJECT_grafana-data)" -o SOURCE,FSTYPE
docker service ls --filter name=grafana --format '{{.Name}} {{.Replicas}}'
```

```text
412
SOURCE                 FSTYPE
nas01:/export/docker   nfs4
observability_grafana 2/2
```

**What the output tells you:** hundreds of lock errors a day, the database on NFS, and two replicas writing to it: all three causes at once.

**Fix:**

```bash
# 1. Back up first
sudo sqlite3 /path/to/grafana.db ".backup '/backup/grafana-before-change.db'"
# 2. Short term: one replica on local disk, with WAL and retries
#    GF_DATABASE_WAL=true  GF_DATABASE_QUERY_RETRIES=3    (transaction_retries defaults to 5)
# 3. Real HA: PostgreSQL plus the unified alerting peers
#    GF_DATABASE_TYPE=postgres GF_DATABASE_HOST=postgres:5432 GF_DATABASE_NAME=grafana GF_DATABASE_USER=grafana
#    GF_DATABASE_PASSWORD__FILE=/run/secrets/grafana_db GF_UNIFIED_ALERTING_HA_PEERS=grafana-1:9094,grafana-2:9094
```

**Why this fix works:** WAL stops readers and the writer from blocking each other, and retries absorb short locks. PostgreSQL removes the single-writer limit and is the supported way to run several replicas, with HA peers so alert notifications are not sent twice. Grafana has no built-in SQLite-to-PostgreSQL migration; with dashboards and alerts provisioned from Git, a fresh PostgreSQL database plus provisioning is the clean path. Never keep grafana.db on NFS.

**Prevent it:** dashboards, data sources and alert rules as code so the database is disposable, nightly backups, and an HA decision before anyone scales replicas.

**Next step:** [Databases for DevOps](38-learn-databases-ops.md) · [Senior architecture](39-learn-senior-architecture.md) · KodeKloud: *Fundamentals of SRE* · [Grafana configuration docs](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)

**Community threads:** [grafana/grafana #16638](https://github.com/grafana/grafana/issues/16638) · [Grafana configuration: database settings](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=grafana+%22database+is+locked%22) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=database+is+locked+sqlite&restrict_sr=1)

## 7. Uptime Kuma, Netdata and Zabbix

### 7.1 Uptime Kuma: false downs and a slow database

> **Seen as:** monitors flap to DOWN with `timeout of 48000ms exceeded`, `getaddrinfo EAI_AGAIN shop.example.com`, `connect ECONNREFUSED 127.0.0.1:8080` or `unable to verify the first certificate` while the sites work; or the UI slows down with `SQLITE_BUSY` and `KnexTimeoutError: Knex: Timeout acquiring a connection. The pool is probably full.` · **Where:** Uptime Kuma in Docker or Dokploy on an on-prem Ubuntu host checking internal and public sites; long-running instances; the 1.x to 2.x upgrade · **Level:** [L0–L2 · Fresher to Mid-level] · **How common:** #275 "Lots of timeout of 48000ms exceeded during the day, but the site is still up?" is Uptime Kuma's most-commented bug (105 comments); #114 (EAI_AGAIN), #2346 (Knex timeout), #2344 (monitors slow down over time), #7338 (SQLITE_BUSY) and #6264 (v2 migration failing) follow

**Why it happens:** the default timeout is about 80% of the 60-second interval, so 48 s means the check never got an answer: slow DNS inside Docker, IPv6 trouble, CPU starvation, or a SQLite database too slow to record results. Docker's embedded DNS forwards to the host's resolvers or falls back to public ones that an on-prem firewall blocks (EAI_AGAIN). localhost is the Uptime Kuma container, and public names resolve to a public IP that the LAN router may not hairpin back. Node.js does not trust your private CA. On the database side, SQLite on NFS is unsupported, a huge heartbeat history makes kuma.db slow, and the v2 migration rewrites data and can take a long time; there is no official SQLite-to-MariaDB migration.

**Diagnose:**

```bash
docker run --rm --net container:uptime-kuma nicolaka/netshoot sh -c \
  'dig +short shop.example.com; curl -s -o /dev/null -m 10 -w "%{http_code} %{time_total}s\n" https://shop.example.com'
docker exec uptime-kuma du -h /app/data/kuma.db
docker logs uptime-kuma --since 1h 2>&1 | grep -cE 'SQLITE_BUSY|KnexTimeoutError'
```

```text
203.0.113.10
000 10.004s
1.9G	/app/data/kuma.db
37
```

**What the output tells you:** DNS works and returns the public 203.0.113.10, but the HTTPS request from inside the LAN never completes: the router does not hairpin traffic back to its own public address. Separately, a 1.9 GB database and 37 lock errors an hour mean the history slows every check down.

**Fix:**

```bash
# Inside the LAN, check internal paths: split-horizon DNS, or http://shop-web:3000 over dokploy-network
# Containers cannot resolve at all? Give Docker real resolvers in /etc/docker/daemon.json:
#   {"dns": ["192.0.2.53", "192.0.2.54"]}            then: sudo systemctl restart docker
# Private CA: mount it and set NODE_EXTRA_CA_CERTS=/app/data/internal-ca.pem
# Database: Settings > Monitor History = 30 days, then "Shrink Database"; keep /app/data on a local volume
# Before the 2.x upgrade: stop, back up, switch to louislam/uptime-kuma:2, and let the migration finish
docker stop uptime-kuma
docker run --rm -v uptime-kuma:/data -v "$PWD":/backup alpine tar czf /backup/kuma-data.tgz -C /data .
```

**Why this fix works:** checks from inside the LAN must use paths that exist inside the LAN; real resolvers and the CA remove the DNS and TLS failures; and a smaller database records results on time, which removes most "timeouts" that were really the app waiting on SQLite. Two or three retries per monitor stop one slow answer from paging anyone. Don't put /app/data on NFS, and don't restart the container during the v2 migration.

**Prevent it:** retries before notifications, history retention set on day one, a backup before every upgrade, the major tag pinned, and a second watcher outside your network for the sites that matter most.

**Next step:** [DNS](08-dns.md) · [Site down](25-playbook-site-down.md) · KodeKloud: *DevOps Pre-Requisite Course* — DNS · [Uptime Kuma README](https://github.com/louislam/uptime-kuma)

**Community threads:** [louislam/uptime-kuma #275](https://github.com/louislam/uptime-kuma/issues/275) · [Uptime Kuma bugs sorted by comments](https://github.com/louislam/uptime-kuma/issues?q=is%3Aissue+label%3Abug+sort%3Acomments-desc) · [Wiki: Migration from v1 to v2](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2) · [louislam/uptime-kuma #6264](https://github.com/louislam/uptime-kuma/issues/6264) · [heise: Uptime Kuma 2.0 with MariaDB support](https://www.heise.de/en/news/Uptime-Kuma-2-0-Monitoring-tool-now-with-MariaDB-support-10793657.html) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=uptime+kuma+timeout+48000ms&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=uptime+kuma+EAI_AGAIN+docker)

### 7.2 Netdata: container IDs and alert floods

> **Seen as:** charts named `cgroup_` plus a hash or a container ID instead of the container name; host CPU and disk charts that show the container's view; a stream of warnings such as `system.softnet_stat` · **Where:** Netdata as a container on Docker or Dokploy hosts for quick per-second dashboards · **Level:** [L1 · Junior] · **How common:** #3972 "docker container names not resolved" (72 comments) and #1076 "Alarm system.softnet_stat is very strict" (71 comments) are among Netdata's most-commented issues

**Why it happens:** Netdata resolves container names through docker.sock; if the socket is not mounted, or the netdata user cannot read it (the docker group's GID differs from host to host), it shows IDs. Without `pid: host`, host networking and the host's /proc, /sys, /etc/passwd, /etc/group and os-release mounts, it charts the container instead of the host. The default health alerts are tuned for generic hosts and fire often on busy ones.

**Diagnose:**

```bash
stat -c '%g %n' /var/run/docker.sock
docker exec netdata sh -c 'id netdata; ls -ln /var/run/docker.sock'
docker inspect -f 'pid={{.HostConfig.PidMode}} net={{.HostConfig.NetworkMode}}' netdata
```

```text
988 /var/run/docker.sock
uid=201(netdata) gid=201(netdata) groups=201(netdata),999(docker)
srw-rw---- 1 0 988 0 Oct  3 08:01 /var/run/docker.sock
pid= net=bridge
```

**What the output tells you:** the socket belongs to group 988 on this host, but inside the image the netdata user is in group 999, so it cannot ask Docker for names; and the container runs without the host's PID namespace or network, so its "host" charts describe the container.

**Fix:**

```yaml
# Start from Netdata's documented Compose file; the parts that matter here
services:
  netdata:
    pid: host
    network_mode: host
    cap_add: [SYS_PTRACE, SYS_ADMIN]
    security_opt: [apparmor:unconfined]
    environment:
      PGID: "988"                       # docker.sock group on THIS host; check Netdata's Docker docs for your version
    volumes:
      - /:/host/root:ro,rslave
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /etc/passwd:/host/etc/passwd:ro
      - /etc/group:/host/etc/group:ro
      - /etc/os-release:/host/etc/os-release:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
# Noisy alert: docker exec -it netdata /etc/netdata/edit-config health.d/net.conf
#   set "to: silent" or a new threshold, then: docker exec netdata netdatacli reload-health
```

**Why this fix works:** the host mounts and namespaces let Netdata read the host's own counters, and the right group on docker.sock lets it turn cgroup IDs into names. Tuning health.d keeps the agent's alerts meaningful. Decide which tool pages people: if Alertmanager does, set Netdata's notifications to silent instead of paging twice.

**Prevent it:** start from Netdata's documented Compose file, keep health.d overrides in Git, and use Netdata for live per-second debugging rather than as a second paging system.

**Next step:** [Slow system](23-playbook-slow-system.md) · [CPU performance](03-cpu-performance.md) · KodeKloud: *Fundamentals of SRE* — [Performance Monitoring Deep Dive](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page) · [Netdata: install with Docker](https://learn.netdata.cloud/docs/netdata-agent/installation/docker)

**Community threads:** [netdata/netdata #3972](https://github.com/netdata/netdata/issues/3972) · [Netdata community: debugging container name resolution](https://community.netdata.cloud/t/how-to-debug-container-name-resolution-for-the-netdata-agent/1399) · [Netdata issues sorted by comments (#1076)](https://github.com/netdata/netdata/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=netdata+docker+container+names&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=netdata+docker+container+names+not+resolved)

### 7.3 Zabbix: agent unreachable or server not running

> **Seen as:** `cannot connect to [[192.0.2.30]:10050]: [111] Connection refused` or `[113] No route to host`; `Received empty response from Zabbix Agent ... Assuming that agent dropped connection because of access permissions.`; `host [Web01] not found` in the agent log; or the frontend banner `Zabbix server is not running: the information displayed may not be current.` · **Where:** adding Ubuntu hosts to Zabbix, often with the Zabbix server in Docker; fresh installs, reboots and upgrades · **Level:** [L1 · Junior] · **How common:** dozens of Zabbix forum threads carry these exact titles, and the "server is not running" banner is one of the most asked Zabbix questions on forums, Stack Overflow and Server Fault

**Why it happens:** the agent is stopped or listens on localhost only, or UFW blocks 10050 on the agent (passive checks) or 10051 on the server (active checks). `Server=` in the agent config is an allow-list checked against the poller's real source address; a Zabbix server in Docker polling an agent on the same host connects from its bridge address, not from 127.0.0.1, so the agent drops it. For active checks, `Hostname=` must match the frontend's host name exactly, case included. PSK or TLS set on one side only breaks the handshake. The banner usually means zabbix_server itself is down (wrong DB password, database down or not upgraded, CacheSize too small) or the frontend points at the wrong server address or port.

**Diagnose:**

```bash
zabbix_get -s 192.0.2.30 -k agent.ping              # package zabbix-get, run on the Zabbix host
sudo grep -E '^(Server|ServerActive|Hostname)=' /etc/zabbix/zabbix_agent2.conf
sudo tail -n 2 /var/log/zabbix/zabbix_agent2.log
```

```text
zabbix_get [212]: Check access restrictions in Zabbix agent configuration
Server=127.0.0.1
ServerActive=127.0.0.1
Hostname=Web01
2026/10/03 10:51:12.004441 failed to accept an incoming connection: connection from "172.18.0.4" rejected, allowed hosts: "127.0.0.1"
2026/10/03 10:51:40.512090 [101] active check configuration update from [127.0.0.1:10051] started to fail (host [Web01] not found)
```

**What the output tells you:** the agent still has the package defaults, so it only accepts 127.0.0.1, while the Dockerised server polls from 172.18.0.4; and the frontend calls the host web01 while the agent says Web01, so active checks fail too.

**Fix:**

```bash
# /etc/zabbix/zabbix_agent2.conf - IPs, CIDRs and DNS names are allowed
#   Server=192.0.2.30,172.18.0.0/16
#   ServerActive=192.0.2.30
#   Hostname=web01                      # exactly as in the frontend
sudo systemctl restart zabbix-agent2
sudo ufw allow proto tcp from 192.0.2.30 to any port 10050 comment 'zabbix passive checks'
# Agent on the same host as a Dockerised server: the polls come from the bridge, so allow 172.18.0.0/16 instead (5.1)
# Agent container: set ZBX_HOSTNAME and ZBX_SERVER_HOST instead of editing the file
# Banner "server is not running": the server log names the cause
docker logs --tail 50 zabbix-server 2>&1 | grep -iE 'database is down|access denied|CacheSize'
```

**Why this fix works:** the allow-list now contains the address the poller really uses, the host name matches the key the server uses to find active checks, and the UFW rule opens the agent port to the poller only. For the banner, the server log names the failure (`database is down: reconnecting in 10 seconds`, `Access denied for user 'zabbix'`, or a request to increase CacheSize); fix that, then check that the frontend points at the right server and port. Don't set Server=0.0.0.0/0 to make it work: any host could then query the agent.

**Prevent it:** template the agent config with Ansible, use auto-registration with HostMetadata so hosts arrive with the right name, and monitor the Zabbix server with its own health template plus an outside probe.

**Next step:** [Who owns this port?](22-playbook-ports-inventory.md) · [Services & systemd](07-services-systemd.md) · KodeKloud: LFCS [*Configure Packet Filtering (Firewall)*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall) · [Zabbix documentation](https://www.zabbix.com/documentation)

**Community threads:** [Zabbix forum: Received empty response from Zabbix Agent](https://www.zabbix.com/forum/zabbix-troubleshooting-and-problems/404690-server-agent-cannot-communicate-serverreceived-empty-response-from-zabbix-agent) · [Zabbix forum: cannot connect to 10050, connection refused](https://www.zabbix.com/forum/zabbix-troubleshooting-and-problems/10105-cannot-connect-to-10-0-2-66-10050-connection-refused) · [Zabbix common errors (blog)](https://dobrinin.dev/posts/zabbix-common-errors/) · Search: [Server Fault](https://serverfault.com/search?q=zabbix+agent+10050+connection+refused) · [Stack Overflow](https://stackoverflow.com/search?q=%22Zabbix+server+is+not+running%22) · [Reddit r/zabbix](https://www.reddit.com/r/zabbix/search/?q=%22server+is+not+running%22&restrict_sr=1)

### 7.4 Zabbix processes more than 75% busy

> **Seen as:** `Zabbix poller processes more than 75% busy`, `Zabbix unreachable poller processes more than 75% busy`, `Zabbix history syncer processes more than 75% busy`, `More than 75% used in the history cache` or `Zabbix housekeeper processes more than 75% busy` (newer versions say "Utilization of ... processes over 75%"), with gaps in graphs and a growing queue · **Where:** a Zabbix that grew to hundreds of hosts or short item intervals · **Level:** [L3 · Senior] · **How common:** many Zabbix forum threads with these exact titles for pollers, unreachable pollers, history syncers and the housekeeper

**Why it happens:** too few pollers for many passive checks, or unreachable hosts tying pollers up until Timeout. History syncers wait on a slow database (disk I/O, no partitioning, untuned MySQL or PostgreSQL). The housekeeper deletes millions of rows from large history tables and is 100% busy while it runs. CacheSize, HistoryCacheSize or ValueCacheSize are too small, intervals too short, and many items unsupported.

**Diagnose:**

```bash
# Frontend first: the "Zabbix server health" dashboard and Administration > Queue
sudo grep -c 'slow query' /var/log/zabbix/zabbix_server.log
sudo grep 'slow query' /var/log/zabbix/zabbix_server.log | tail -1 | cut -c1-100
iostat -xz 5 2 | grep -E 'Device|sda'          # on the database host (columns trimmed)
```

```text
2841
  1187:20261003:110201.552 slow query: 4.812376 sec, "insert into history_uint (itemid,clock,ns,va
Device      r/s      w/s    wkB/s  w_await  aqu-sz  %util
sda        12.0   1480.0  42110.0    38.20   56.10   99.8
```

**What the output tells you:** thousands of slow inserts and a database disk at 99.8% utilisation with 38 ms write waits: the history syncers are busy because the database cannot keep up, so adding syncers would only add more waiting writers.

**Fix:**

```bash
# Database first: faster disks, a tuned MySQL/PostgreSQL, partitioned history and trends tables
#   (or TimescaleDB), and housekeeping turned off for the tables the partitions now expire
# Then size zabbix_server.conf from the internal graphs, aiming at 30-40% average busy:
#   StartPollers=40  StartPollersUnreachable=5  StartDBSyncers=8  Timeout=5
#   CacheSize=256M  HistoryCacheSize=128M  ValueCacheSize=256M
# Less load: active agent checks, Zabbix proxies for remote sites (7.0+ adds asynchronous pollers),
#   longer intervals, and unsupported items disabled
sudo systemctl restart zabbix-server
```

**Why this fix works:** each busy alarm names the queue that waits, and the slow-query log shows what it waits for. Fixing the database removes the bottleneck behind the syncers and the housekeeper, while proxies and active checks spread the polling. Partitions drop a whole day at once instead of deleting rows one by one. Don't just raise every Start value: more processes against a saturated database make it slower.

**Prevent it:** plan capacity in new values per second (Reports > System information shows the required server performance), start large installs on partitioning or TimescaleDB, and look at the busy graphs every week. 7.0 is the LTS most installs run; 8.0 LTS was due around October 2026, so read the roadmap before planning an upgrade.

**Next step:** [Databases for DevOps](38-learn-databases-ops.md) · [Slow system: disk I/O](23-playbook-slow-system.md) · KodeKloud: LFCS [*Monitor Storage Performance*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page) · [Zabbix roadmap](https://www.zabbix.com/roadmap)

**Community threads:** [Zabbix forum: history syncer more than 75% busy](https://www.zabbix.com/forum/zabbix-help/40202-zabbix-history-syncer-processes-more-than-75-busy) · [Zabbix forum: housekeeper more than 75% busy](https://www.zabbix.com/forum/zabbix-help/448045-optimizing-and-troubleshoting-zabbix-housekeeper-processes-more-than-75-busy) · [Zabbix forum: poller more than 75% busy](https://www.zabbix.com/forum/zabbix-troubleshooting-and-problems/50469-zabbix-poller-processes-more-than-75-busy) · Search: [Reddit r/zabbix](https://www.reddit.com/r/zabbix/search/?q=history+syncer+busy&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=zabbix+history+syncer+75%25+busy)

## 8. Alerting: Alertmanager and Grafana

### 8.1 Alerts fire but nobody is notified

> **Seen as:** a rule is Firing on Prometheus's Alerts page but no email, Teams or Telegram message arrives; Alertmanager logs `Notify for alerts failed ... notify retry canceled after 4 attempts`, `535 5.7.8 Username and Password not accepted` or `x509: certificate signed by unknown authority`; Prometheus logs `Error sending alert ... no such host` · **Where:** Alertmanager in Docker or Kubernetes · **Level:** [L2 · Mid-level] · **How common:** among the most common Alertmanager questions; Microsoft's retirement of Office 365 connectors for Teams produced alertmanager #3920 (55 comments)

**Why it happens:** walk the four gates. The rule may still be Pending because of `for:`. Prometheus may have no `alerting:` block, or an Alertmanager address it cannot resolve. The route tree may send the alert elsewhere (a label typo, a missing `continue: true`, a stricter matcher than you think), or a silence or inhibition mutes it. Finally the receiver fails: outbound 25 or 587 blocked by the on-prem firewall (AWS restricts port 25 too), `smtp_require_tls` defaulting to true, Gmail wanting an app password, an internal relay or webhook signed by your private CA, or a Teams URL from the retired Office 365 connectors instead of a Workflows webhook. In some container networks gossip cannot pick an address and Alertmanager will not start: `Failed to get final advertise address`.

**Diagnose:**

```bash
curl -s localhost:9090/api/v1/alertmanagers | jq -r '.data.activeAlertmanagers[].url'
docker exec alertmanager amtool config routes test --config.file=/etc/alertmanager/alertmanager.yml severity=ticket alertname=DiskAbove85Percent
docker exec alertmanager amtool --alertmanager.url=http://localhost:9093 silence query
docker logs alertmanager --since 1h 2>&1 | grep -m1 'Notify for alerts failed'
```

```text
http://alertmanager:9093/api/v2/alerts
ops-email
ID  Matchers  Ends At  Created By  Comment
time=2026-10-03T11:02:13.902Z level=ERROR source=dispatch.go msg="Notify for alerts failed" num_alerts=2 err="ops-email/email[0]: notify retry canceled after 4 attempts: establish connection to server: dial tcp 198.51.100.25:587: i/o timeout"
```

**What the output tells you:** Prometheus knows the Alertmanager, the route sends the alert to ops-email, and nothing is silenced. The last gate fails: the SMTP relay never answers on 587, so something between this host and the relay drops outbound SMTP.

**Fix:**

```bash
nc -vz -w 5 smtp.example.com 587       # the same timeout from the host means a firewall, not Alertmanager
# Then: open dokploy-1 -> smtp.example.com:587, or use the internal relay your network team provides.
# An internal relay signed by your CA (alertmanager.yml):
#   email_configs:
#     - to: ops@example.com
#       smarthost: relay.example.com:587
#       tls_config: {ca_file: /etc/alertmanager/internal-ca.crt}
# Teams: create a Workflows webhook, use msteamsv2_configs, keep the old receiver until the new one works
# A single Alertmanager without HA: --cluster.listen-address= (empty) turns gossip off
docker exec alertmanager amtool --alertmanager.url=http://localhost:9093 alert add NotifyTest severity=ticket host=dokploy-1
```

**Why this fix works:** each gate has its own check, so you repair the closed one instead of rewriting the config: the route test proves the routing, the silence list proves nothing is muted, and a raw TCP test separates a blocked network from bad credentials (a 535 reply) or an untrusted certificate (x509). The test alert then proves the whole chain. Don't set `insecure_skip_verify` on the email TLS settings; give Alertmanager your CA.

**Prevent it:** the Watchdog heartbeat to an outside dead man's switch, the AlertmanagerNotificationsFailing rule, and `amtool config routes test` in CI (section 3).

**Next step:** [Performance & observability: Alertmanager](32-learn-performance-observability.md#12-alertmanager-and-alert-rules) · [Network](02-network.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/)

**Community threads:** [Alertmanager configuration docs (routes, email, msteamsv2)](https://prometheus.io/docs/alerting/latest/configuration/) · [prometheus/alertmanager #3920](https://github.com/prometheus/alertmanager/issues/3920) · Search: [Stack Overflow](https://stackoverflow.com/search?q=alertmanager+%22notify+retry+canceled%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=alertmanager+email+not+sending&restrict_sr=1)

### 8.2 Grafana alerting: NoData and Error floods

> **Seen as:** a flood of alerts named DatasourceNoData or DatasourceError; `Template variables are not supported in alert queries`; `Failed to evaluate queries and expressions: input data must be a wide series but got type long` · **Where:** alert rules built in Grafana (unified alerting) on Prometheus, Loki or SQL data sources · **Level:** [L2 · Mid-level] · **How common:** "Template variables are not supported in alert queries" (about 123k views), "input data must be a wide series but got type long" (about 36k) and alert export and import (about 53k) on community.grafana.com; Grafana #6557 has 142 comments

**Why it happens:** alert rules cannot use dashboard variables, so a query copied from a panel with `$host` fails. SQL data sources return long-format frames that need a Reduce expression or the time-series format. When a query returns nothing or errors, Grafana raises separate DatasourceNoData or DatasourceError alert instances with different labels, so the silences and routes written for the original alert miss them. Legacy dashboard alerting was removed in Grafana 11, so old blog examples no longer apply.

**Diagnose:**

```bash
# Firing Grafana-managed alerts by name (a service account token in GRAFANA_TOKEN)
curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" https://grafana.example.com/api/prometheus/grafana/api/v1/alerts \
  | jq -r '.data.alerts[] | .labels.alertname + " " + (.labels.datasource_uid // "-")' | sort | uniq -c
```

```text
     38 DatasourceNoData loki
      2 ShopErrorLogs -
```

**What the output tells you:** 38 of 40 firing instances are DatasourceNoData from Loki-based rules: their queries matched no log lines, and by default Grafana treats "no data" as a problem. The two real alerts drown in it.

**Fix:**

```text
Rule > Configure no data and error handling:
  If no data:         Normal (or Keep Last State) for queries that are empty by design, such as error counts
  If execution error: Error, routed by datasource_uid to the platform team instead of the app owners
Queries: explicit matchers instead of $host; one multi-dimensional rule gives one instance per series
SQL: add a Reduce expression (Last or Mean), or return a time column so the frame is wide
Keep rules as code: Alerting > Export, then provision them from files in Git
```

**Why this fix works:** a query for error lines is supposed to be empty most of the time, so No data must mean Normal there, while real data-source failures still surface as errors and go to whoever runs the data source. Explicit matchers and wide frames are what the rule evaluator accepts. Don't silence DatasourceNoData globally: then a broken data source looks like a healthy service.

**Prevent it:** one source of truth per alert (Prometheus rules for infrastructure, Grafana rules only for cross-data-source cases), pending periods on every rule, and rules provisioned from Git.

**Next step:** [Performance & observability: Grafana](32-learn-performance-observability.md#13-grafana) · KodeKloud: *Fundamentals of SRE* — Incident Management · [Grafana: No Data and Error states](https://grafana.com/docs/grafana/latest/alerting/fundamentals/alert-rule-evaluation/nodata-and-error-states/)

**Community threads:** [Grafana docs: No Data and Error states](https://grafana.com/docs/grafana/latest/alerting/fundamentals/alert-rule-evaluation/nodata-and-error-states/) · [community.grafana.com top topics (alerting)](https://community.grafana.com/top?period=all) · Search: [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=DatasourceNoData&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=grafana+%22template+variables+are+not+supported+in+alert+queries%22)

### 8.3 Templates print no value or break messages

> **Seen as:** messages that show `<no value>`, an empty Slack title, Telegram's `Bad Request: can't parse entities`, or a Grafana contact point test that fails with a template error · **Where:** custom email, Slack, Telegram or Teams messages copied from blogs, in Alertmanager and in Grafana alerting · **Level:** [L2–L3 · Mid-level/Senior] · **How common:** "How To Use Alert Message Templates in Grafana" (144 replies, about 86k views) and "Documentation of Alert Templating in Serious Need of Improvement!" (121 replies) are top community.grafana.com topics; alertmanager #2923 tracks Telegram parse errors

**Why it happens:** there are two template layers. Rule annotations use `{{ $labels.instance }}` and `{{ $value }}`; Alertmanager notification templates use `.CommonLabels`, `.GroupLabels` and `range .Alerts`. Go templates print `<no value>` for a label that only some alerts in the group have. Grafana's template data (`.Alerts`, `.Labels`, `.Annotations`, `.Values`) differs from Alertmanager examples, and Telegram's HTML or Markdown parse modes reject unescaped or truncated markup.

**Diagnose:**

```bash
grep -n 'custom.title' /etc/alertmanager/templates/custom.tmpl
docker exec alertmanager amtool --alertmanager.url=http://localhost:9093 alert query alertname=DiskAbove85Percent
```

```text
1:{{ define "custom.title" }}[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }} on {{ .CommonLabels.host }}{{ end }}
Alertname           Starts At                Summary
DiskAbove85Percent  2026-10-03 11:20:00 UTC  dokploy-2 / is 91% full
DiskAbove85Percent  2026-10-03 11:21:30 UTC  dokploy-1 /var is 88% full
```

**What the output tells you:** the group holds alerts from two hosts, so host is not a common label and `.CommonLabels.host` prints `<no value>`. Per-alert details belong in a loop over `.Alerts`.

**Fix:**

```text
{{ define "custom.title" }}[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}{{ if .CommonLabels.host }} on {{ .CommonLabels.host }}{{ end }}{{ end }}
{{ define "custom.text" }}{{ range .Alerts }}- {{ .Annotations.summary }}{{ if .Labels.service }} (service {{ .Labels.service }}){{ end }}
{{ end }}{{ end }}
# Telegram receivers: parse_mode: '' (plain text), or escape markup in annotations
# Grafana: start from a working notification template, change one field at a time, use the preview
```

**Why this fix works:** human text lives in the rule annotations (summary, description, runbook_url), where every alert has its own labels, and the notification template only loops over alerts and guards optional labels with `if`. Plain-text Telegram messages cannot fail markup parsing.

**Prevent it:** templates in Git, rendered with `amtool template render` in CI, and the same annotation names in Prometheus and Grafana rules.

**Next step:** [Performance & observability: Alertmanager](32-learn-performance-observability.md#12-alertmanager-and-alert-rules) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/)

**Community threads:** [community.grafana.com top topics (templating)](https://community.grafana.com/top?period=all) · [Alertmanager issues sorted by reactions (#2923)](https://github.com/prometheus/alertmanager/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=alertmanager+template+range+.Alerts) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=alertmanager+template+no+value&restrict_sr=1)

### 8.4 Late, repeated, flapping or storming alerts

> **Seen as:** the first notification minutes after the problem, "resolved" 5 minutes late, the same alert every 4 hours, alerts flapping between firing and resolved, one dead host sending a dozen notifications, a silence that does not mute, a Watchdog that "never stops" · **Where:** any Alertmanager or Grafana alerting setup that grew without a design · **Level:** [L2–L4 · Mid-level to Senior/Lead] · **How common:** a perennial question on Stack Overflow and r/PrometheusMonitoring; alertmanager #2995 (inhibit rules documentation), #226 (resolved notifications for silenced alerts, 71 comments) and #1860 (acknowledging alerts) show how often teams fight these features

**Why it happens:** the timers work as designed: group_wait (30 s) delays the first notification of a new group, group_interval (5 m) delays every change to a group including resolutions, and repeat_interval (4 h) re-sends an unchanged group. The rule's `for:` and the scrape and evaluation intervals add more. Thresholds on raw, noisy series flap. Storms come from group_by being too fine (or `'...'`, which turns grouping off) and from missing inhibition for cascades. Inhibition's `equal` needs the same value on both alerts, so differently formatted labels never match, and it also applies when the listed label is missing on both. Silence matchers are anchored and case-sensitive. Watchdog is meant to fire forever.

**Diagnose:**

```bash
q 'ALERTS_FOR_STATE{alertname="TargetDown"}'     # value = when the condition became true (Unix time)
docker exec alertmanager amtool config routes show --config.file=/etc/alertmanager/alertmanager.yml
AM=localhost:9093/api/v2/alerts
curl -s "$AM?filter=host%3D%22dokploy-2%22" | jq length                              # all alerts for the host
curl -s "$AM?active=false&silenced=false&filter=host%3D%22dokploy-2%22" | jq length   # of those, inhibited
```

```text
{"__name__":"ALERTS_FOR_STATE","alertname":"TargetDown","host":"dokploy-2","instance":"10.10.0.20:9100","job":"node","severity":"page"} 1791025320
Routing tree:
└── default-route  receiver: ops-email
    ├── {severity="heartbeat"}  receiver: heartbeat
    └── {severity="page"}  receiver: ops-teams
6
0
```

**What the output tells you:** the condition began at 11:02:00 UTC; with `for: 5m` the alert fired at 11:07 and the page route waited its 10 s group_wait, so a page at about 11:07 is the design, not a bug. But six alerts concern dokploy-2 and none is inhibited, so its TargetDown for cAdvisor, its disk alerts and its probes arrive as separate notifications: the inhibit rule is missing or its `equal` label does not match.

**Fix:**

```yaml
# alertmanager.yml - timers per route, coarser grouping, inhibition for cascades
route:
  group_by: ["alertname", "host"]          # never '...' unless every alert must be its own message
  routes:
    - matchers: ['severity="page"']
      receiver: ops-teams
      group_wait: 10s
      group_interval: 1m
      repeat_interval: 1h                  # keep it a multiple of group_interval
inhibit_rules:
  - source_matchers: ['alertname="TargetDown"', 'job="node"']
    target_matchers: ['severity=~"page|ticket"']
    equal: ["host"]                        # every job, probes included, must carry the same host label
```

```yaml
# Prometheus rule: smooth a noisy signal instead of paging on every wobble
- alert: ShopHigh5xx
  expr: |
    sum by (service) (rate(traefik_service_requests_total{service="shop-web@docker", code=~"5.."}[10m]))
      / sum by (service) (rate(traefik_service_requests_total{service="shop-web@docker"}[10m])) > 0.05
  for: 5m
  keep_firing_for: 10m                     # Prometheus 2.42+: a short dip does not send "resolved"
```

**Why this fix works:** knowing the three timers turns "late" into a timeline you can write into the runbook; grouping by alert and host sends one message per problem; inhibition removes symptoms of a cause that is already paging; and a longer window plus keep_firing_for stops a noisy series from flapping. Route Watchdog to a heartbeat receiver with a one-minute repeat, never silence it. Page on symptoms users feel and send causes as tickets.

**Prevent it:** the expected notification timeline in each runbook, a monthly alert review that deletes alerts nobody acted on, and a shared host label on every job, including the probe jobs.

**Next step:** [SLIs, SLOs and error budgets](32-learn-performance-observability.md#15-slis-slos-and-error-budgets) · [Career ladder](40-career-ladder.md) · KodeKloud: *Fundamentals of SRE* — Incident Management (Designing Effective Alerts) · [Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/)

**Community threads:** [Alertmanager configuration docs (timers, inhibit_rules)](https://prometheus.io/docs/alerting/latest/configuration/) · [Alertmanager issues sorted by reactions (#2995, #226, #1860)](https://github.com/prometheus/alertmanager/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=alertmanager+group_wait+group_interval+repeat_interval) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=alert+fatigue&restrict_sr=1)

## 9. Logs and traces: Loki, Alloy and Tempo

### 9.1 Promtail is end-of-life: Alloy ships no logs

> **Seen as:** after replacing Promtail or Grafana Agent with Alloy, Explore shows no labels; Alloy logs `permission denied` on /var/run/docker.sock or cannot open /var/log/journal; its UI on :12345 is unreachable; old logs are re-sent and rejected as too old · **Where:** Ubuntu and Docker hosts moving to Alloy · **Level:** [L1–L2 · Junior/Mid-level] · **How common:** every Promtail user must migrate: Grafana Agent reached end of life on 1 November 2025 and Promtail on 2 March 2026

**Why it happens:** Promtail and Grafana Agent no longer get fixes, and Alloy is the supported successor. A converted config stores read positions in a new place, so files and journals can be read again from the start. Alloy needs read access to docker.sock, /var/log/journal and /etc/machine-id, and its UI binds 127.0.0.1:12345 by default, which nobody outside the container can reach. Promtail's command-line flags and environment variables are not converted at all.

**Diagnose:**

```bash
docker logs alloy --since 10m 2>&1 | grep -E 'level=(error|warn)' | cut -c1-150
curl -s http://10.10.0.10:3100/loki/api/v1/labels
```

```text
ts=2026-10-03T11:40:02.118Z level=error msg="failed to start component" component_id=loki.source.journal.system err="... /var/log/journal: no such file or directory"
ts=2026-10-03T11:40:02.341Z level=error msg="could not list containers" component_id=loki.source.docker.containers err="permission denied while trying to connect to the Docker daemon socket"
{"status":"success","data":[]}
```

**What the output tells you:** both sources fail at the start: the journal directory is not mounted into the container, and Alloy may not read docker.sock, so nothing reaches Loki and it has no labels.

**Fix:**

```bash
# Convert once and read the report; Promtail's flags and env vars must be moved by hand
alloy convert --source-format=promtail --report=report.txt --output=config.alloy promtail.yaml
# Bridge during the migration: run the old file unchanged with "alloy run --config.format=promtail promtail.yaml"
# Agents Compose service (section 2): docker.sock, /var/log/journal and /etc/machine-id mounted read-only,
#   --storage.path on a named volume, --server.http.listen-addr=0.0.0.0:12345 published on 127.0.0.1 only
# Still "permission denied" on the socket? Add the socket's group: group_add: ["988"]   (stat -c %g /var/run/docker.sock)
# Keep max_age on loki.source.journal (12h in section 2) so a first start does not replay weeks of journal
```

**Why this fix works:** Alloy reads exactly what is mounted and permitted, and a persistent storage path keeps its positions across restarts, so it neither misses logs nor re-sends them. Roll out host by host and watch `loki_discarded_samples_total` while you do; don't delete the old agent's positions file until Alloy is confirmed.

**Prevent it:** pin the Alloy version, keep its storage path on a volume, and validate the config with `alloy fmt` in CI (section 3).

**Next step:** [Logs & journal](06-logs-journal.md) · KodeKloud: [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) — Grafana Loki Essentials (Grafana Alloy agent) · [Alloy: migrate from Promtail](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/)

**Community threads:** [Loki docs: Promtail end of life](https://grafana.com/docs/loki/latest/send-data/promtail/) · [Alloy docs: migrate from Promtail](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/) · [Alloy docs: loki.source.docker](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/) · [Grafana Agent docs (EOL notice)](https://grafana.com/docs/agent/latest/) · Search: [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=promtail+to+alloy+migration&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=grafana+alloy+loki.source.docker+permission+denied)

### 9.2 The Loki Docker driver freezes containers

> **Seen as:** `docker stop` hangs, `docker logs` stops updating, and containers cannot be killed while Loki is down or restarting · **Where:** hosts whose /etc/docker/daemon.json sets `"log-driver": "loki"` for every container, Dokploy hosts included · **Level:** [L2 · Mid-level] · **How common:** grafana/loki #2361 is among Loki's most-reacted issues and is still open

**Why it happens:** the Loki logging-driver plugin blocks a container's output when it cannot deliver to Loki and keeps retrying, so the availability of every app on the host becomes tied to the logging back end. A Loki restart or a network blip stalls every container that writes logs.

**Diagnose:**

```bash
docker info --format '{{.LoggingDriver}}'; docker plugin ls --format '{{.Name}} {{.Enabled}}'
sudo journalctl -u docker --since '10 min ago' | grep -i loki | tail -1 | cut -c1-160
curl -s -m 3 http://10.10.0.10:3100/ready || echo "loki unreachable"
```

```text
loki
loki:latest true
... level=error msg="error sending batch, will retry" error="Post \"http://10.10.0.10:3100/loki/api/v1/push\": dial tcp 10.10.0.10:3100: connect: connection refused"
loki unreachable
```

**What the output tells you:** every container logs through the Loki driver and Loki is unreachable, so the driver retries while container output backs up behind it.

**Fix:**

```json
{
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "3"}
}
```

Put this in /etc/docker/daemon.json and restart Docker in a maintenance window. The default driver applies only to containers created afterwards, so redeploy the apps (in Dokploy, a redeploy per app), then ship the files with Alloy as in section 2. If you must keep the driver for a while, set `"mode": "non-blocking"`, `"max-buffer-size": "4m"`, `"loki-retries": "2"` and `"loki-timeout": "2s"` in its log-opts.

**Why this fix works:** json-file never depends on the network, rotation caps its disk use, and Alloy reads the files and retries on its own without blocking any app. Non-blocking mode drops log lines when its buffer fills instead of stalling, a trade you make knowingly.

**Prevent it:** never let app availability depend on the log back end, and prove it in staging by stopping Loki on purpose.

**Next step:** [Docker](30-learn-docker.md) · [Logs & journal](06-logs-journal.md) · KodeKloud: *Docker Certified Associate* — Docker Engine ([Logging Driver notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · [Loki docs](https://grafana.com/docs/loki/latest/)

**Community threads:** [grafana/loki #2361](https://github.com/grafana/loki/issues/2361) · [Loki issues sorted by reactions](https://github.com/grafana/loki/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=loki+logging+driver+hang&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=loki+docker+driver+container+hangs)

### 9.3 Loki rejects pushes: 429 and too old

> **Seen as:** `429 Too Many Requests: Ingestion rate limit exceeded for user fake (limit: 4194304 bytes/sec)`, `Per stream rate limit exceeded`, `Maximum active stream limit exceeded, reduce the number of active streams (reduce labels or reduce label values)`, `entry too far behind`, `timestamp too old` · **Where:** shipping Docker, Swarm or Kubernetes logs; the first start of an agent on old files; noisy debug logging · **Level:** [L2 · Mid-level] · **How common:** Loki's docs give these validation reasons a page of their own; "High cardinality labels" (#91) and "Allow out of order log submission" (#1544) are top-reacted Loki issues

**Why it happens:** high-cardinality labels (container IDs, Swarm task names, pod names, request IDs, users) create too many streams. Volume above the tenant limits trips the rate limits; per_stream_rate_limit defaults to 3 MB/s with a 15 MB burst. Agents that ship old files on first start hit reject_old_samples, which is on by default, and so does clock skew. Losing the positions file re-reads everything.

**Diagnose:**

```bash
q 'sum by (reason) (rate(loki_discarded_samples_total[5m]))'
logcli --addr=http://10.10.0.10:3100 series --analyze-labels '{host=~".+"}' | head -6
```

```text
{"reason":"stream_limit"} 812.4
Total Streams:  41211
Unique Labels:  4

Label Name  Unique Values  Found In Streams
container   40987          41211
```

**What the output tells you:** a container label with almost 41,000 values: every Swarm task and every deploy created new streams until the stream limit was reached, and now Loki refuses about 800 lines a second.

**Fix:**

```yaml
# 1. In Alloy, labels only with bounded values (host, source, service, unit as in section 2);
#    container names and IDs go into the log line or structured metadata, never into labels
# 2. Drop debug lines at the agent (stage.drop) before raising any limit
# 3. Then size limits to the real volume (loki.yml)
limits_config:
  ingestion_rate_mb: 8
  ingestion_burst_size_mb: 16
  per_stream_rate_limit: 5MB
  per_stream_rate_limit_burst: 20MB
  max_global_streams_per_user: 10000
  reject_old_samples: true
  reject_old_samples_max_age: 168h      # raise it only for a planned backfill; fix NTP for "too far in the future"
```

**Why this fix works:** a stream is the unit Loki indexes and limits, so fewer, bounded labels reduce memory, the index and the limit hits all at once, and queries by host or service stay fast. Raising limits without fixing labels only postpones the next 429 and makes Loki slower.

**Prevent it:** a label review before onboarding a service, and the LokiDiscardingLogs alert (section 2) by reason.

**Next step:** [Observability pillars and cardinality](32-learn-performance-observability.md#10-observability-pillars-and-cardinality) · KodeKloud: [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) — Grafana Loki Essentials · [Loki: request validation and rate limits](https://grafana.com/docs/loki/latest/operations/request-validation-rate-limits/)

**Community threads:** [Loki docs: request validation and rate-limit errors](https://grafana.com/docs/loki/latest/operations/request-validation-rate-limits/) · [Loki issues sorted by reactions (#91, #1544)](https://github.com/grafana/loki/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=loki+%22ingestion+rate+limit+exceeded%22) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=loki+stream+limit+exceeded&restrict_sr=1)

### 9.4 Loki disk grows despite retention

> **Seen as:** the Loki volume grows forever although retention_period is set; `no space left on device`; Loki restart-loops replaying its WAL; on 3.x a config error asking for `delete_request_store` once retention is enabled · **Where:** single-binary Loki on filesystem storage in Docker or Dokploy · **Level:** [L2 · Mid-level] · **How common:** the retention docs state that without retention enabled, logs sent to Loki live forever; "WAL corruption leads to endless restarts" (#12583) is on Loki's most-reacted list

**Why it happens:** retention is applied only by the compactor and is off by default, so retention_period alone deletes nothing. Loki 3.x requires delete_request_store when retention is on, and retention needs a 24h index period with tsdb (or boltdb-shipper). In simple-scalable or microservices mode the compactor may not run at all. And the WAL and chunks often sit on a small root disk.

**Diagnose:**

```bash
curl -s http://10.10.0.10:3100/config | grep -E 'retention_enabled|retention_period|delete_request_store'
sudo du -sh /var/lib/docker/volumes/PROJECT_loki-data/_data/{chunks,wal}
```

```text
  retention_enabled: false
  delete_request_store: ""
  retention_period: 31d
38G	/var/lib/docker/volumes/PROJECT_loki-data/_data/chunks
1.2G	/var/lib/docker/volumes/PROJECT_loki-data/_data/wal
```

**What the output tells you:** retention_period says 31 days, but the compactor's retention is off, so it compacts and never deletes; 38 GB of chunks for a small estate confirms it.

**Fix:**

```yaml
# loki.yml - the compactor applies retention (as in section 2)
compactor:
  working_directory: /loki/compactor
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  delete_request_store: filesystem
limits_config:
  retention_period: 744h
# Crash loop after a full disk: free space first; only as a last resort move the wal/ directory aside
# (logs not yet flushed are lost). Production: object storage (MinIO or S3) and a dedicated volume.
```

**Why this fix works:** with retention enabled, the compactor marks chunks older than the period and deletes them after the delay, so disk use levels off at roughly 31 days of logs. Freeing disk before touching the WAL keeps the unflushed data; moving the WAL trades it for a working Loki.

**Prevent it:** retention configured on day one, a disk alert on the Loki volume (DiskFullIn24h covers it when the volume is its own filesystem), and logs that must be kept for years archived elsewhere.

**Next step:** [Disk & storage](01-storage-disk.md) · [Databases, storage & backups](51-problems-databases-storage-backup.md) · KodeKloud: [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) · [Loki: log retention](https://grafana.com/docs/loki/latest/operations/storage/retention/)

**Community threads:** [Loki docs: log retention](https://grafana.com/docs/loki/latest/operations/storage/retention/) · [Loki docs: upgrade guide](https://grafana.com/docs/loki/latest/setup/upgrade/) · [Loki issues sorted by reactions (#12583)](https://github.com/grafana/loki/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=loki+retention+not+working+compactor) · [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=loki+retention+disk+full&restrict_sr=1)

### 9.5 Loki queries fail: limits and timeouts

> **Seen as:** `too many outstanding requests`, `maximum of series (500) reached for a single query`, `max entries limit per query exceeded, limit > max_entries_limit (5001 > 5000)`, `the query time range exceeds the limit`, or `504 Gateway Timeout` · **Where:** dashboards with many Loki panels, long time ranges, or metric queries grouped by high-cardinality labels · **Level:** [L2–L3 · Mid-level/Senior] · **How common:** grafana/loki #5123 (too many outstanding requests after 2.4.2) and #3045 (maximum of series 500) are top-reacted Loki issues

**Why it happens:** the per-tenant queue in the query frontend or scheduler is too small for dashboards that fire many parallel queries (a 2.4.2 regression made this common). A `sum by` over a high-cardinality label exceeds max_query_series (500). Line limits (max_entries_limit_per_query, 5000) and the maximum query length (721h) cap what one query may return, and proxy or Grafana data-source timeouts are shorter than the query.

**Diagnose:**

```bash
logcli --addr=http://10.10.0.10:3100 query --stats --since=24h --limit=10 '{service="shop-web"} |= "error"' 2>&1 | grep -E 'TotalBytesProcessed|ExecTime'
docker logs loki --since 1h 2>&1 | grep -ciE 'outstanding|context deadline'
```

```text
Summary.TotalBytesProcessed   41 GB
Summary.ExecTime              58.1s
126
```

**What the output tells you:** one 24-hour error search reads 41 GB and takes almost a minute, so a dashboard with a dozen such panels overflows the queue and hits the 60-second proxy timeout.

**Fix:**

```yaml
# loki.yml - commonly used settings for a single-binary Loki serving dashboards
query_scheduler:
  max_outstanding_requests_per_tenant: 4096
frontend:
  max_outstanding_per_tenant: 4096
limits_config:
  split_queries_by_interval: 1h
  max_query_series: 1000
  query_timeout: 5m
server:
  http_server_read_timeout: 5m
  http_server_write_timeout: 5m
# Queries: narrow stream selectors first, line filters before parsers, topk, shorter ranges;
# raise the Grafana data source timeout; move heavy metric queries into ruler recording rules
```

**Why this fix works:** a bigger queue absorbs dashboard bursts, splitting by hour lets one query run in parallel pieces, and longer timeouts on Loki, Grafana and the proxy stop healthy queries from being cut off. The query rewrite matters most: a selector that names the service reads a fraction of the data a line filter over everything would.

**Prevent it:** a panel budget per dashboard, recording rules for the dashboards everyone opens, and no `sum by` over unbounded labels.

**Next step:** [Performance & observability: logs and tracing](32-learn-performance-observability.md#14-logs-and-tracing) · KodeKloud: [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) — Grafana Loki on Kubernetes (LogQL labs) · [Loki docs](https://grafana.com/docs/loki/latest/)

**Community threads:** [grafana/loki #5123](https://github.com/grafana/loki/issues/5123) · [grafana/loki #3045](https://github.com/grafana/loki/issues/3045) · Search: [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=loki+%22too+many+outstanding+requests%22&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=loki+%22maximum+of+series%22+reached)

### 9.6 Loki 3 upgrade: schema v13 and tsdb

> **Seen as:** Loki refuses to start after an upgrade: `schema v13 is required to store Structured Metadata`, `tsdb index type is required`; labels dropped after the upgrade; `docker exec loki sh` fails with `executable file not found` · **Where:** upgrading a 2.x config (boltdb-shipper, schema v11 or v12) to 3.x, or debugging a 3.5.8+ container · **Level:** [L3 · Senior] · **How common:** spelled out in the Loki upgrade guide; "failed to get token ranges for ingester err=zone not set" (#13414) is another upgrade issue on the most-reacted list

**Why it happens:** structured metadata and OTLP ingestion are on by default in 3.x and need schema v13 with the tsdb index. 3.0 also lowered the limits to 15 label names per series and a 256 KB maximum line size, and removed shared_store. From 3.5.8 the images contain no shell. Later minors changed more (3.6.0 moved to the AWS SDK v2), so every minor upgrade needs its notes read.

**Diagnose:**

```bash
docker run --rm -v "$PWD/loki:/etc/loki:ro" grafana/loki:3.7.8 -config.file=/etc/loki/loki.yml -verify-config
grep -B2 -A6 'schema:' loki/loki.yml
```

```text
level=error msg="validating config" err="schema v13 is required to store Structured Metadata and use native OTLP ingestion, your schema version is v12. Set allow_structured_metadata: false in the limits_config section or set the command line argument -validation.allow-structured-metadata=false and restart Loki. Then proceed to update to schema v13 or newer before re-enabling this config, search for 'Storage Schema' in the docs for the schema update procedure"
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v12
```

**What the output tells you:** the only schema period is v12 on boltdb-shipper, so 3.x refuses to start with structured metadata enabled; the message itself names the stop-gap and the real fix.

**Fix:**

```yaml
# Add a new period with a FUTURE date (UTC); never edit or delete old periods
schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v12
      index: {prefix: index_, period: 24h}
    - from: 2026-10-10
      store: tsdb
      object_store: filesystem
      schema: v13
      index: {prefix: index_, period: 24h}
limits_config:
  allow_structured_metadata: false     # only until 2026-10-10 has passed; then remove this line
# No shell in the image: debug from a sidecar, e.g. docker run --rm -it --net container:loki nicolaka/netshoot
```

**Why this fix works:** Loki reads each period with its own schema, so old data stays readable while new data is written with v13 and tsdb from the cut-over date. Editing an existing period would make old chunks unreadable. The netshoot container shares Loki's network namespace and brings its own tools.

**Prevent it:** `-verify-config` before every merge, pinned versions, and the upgrade guide read for every minor release.

**Next step:** section 3, Upgrades without surprises · KodeKloud: [*Grafana Loki*](https://kodekloud.com/courses/grafana-loki) · [Loki upgrade guide](https://grafana.com/docs/loki/latest/setup/upgrade/)

**Community threads:** [Loki docs: upgrade guide (3.0 schema and tsdb, 3.5.8 shell removal, 3.6.0 AWS SDK v2)](https://grafana.com/docs/loki/latest/setup/upgrade/) · [Loki issues sorted by reactions (#13414)](https://github.com/grafana/loki/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=loki+3.0+schema+v13&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=loki+%22schema+v13+is+required%22)

### 9.7 Tempo: traces never show up

> **Seen as:** Grafana Explore says `trace not found`; Tempo logs `pusher failed to consume trace data` or `Too many jobs in the queue`; queries fail with "response larger than the max"; the app's exporter logs `connection refused` to tempo:4317 · **Where:** apps instrumented with OpenTelemetry sending OTLP to Tempo in Docker or Kubernetes · **Level:** [L3 · Senior] · **How common:** Tempo's troubleshooting docs cover each of these; trace-to-logs setup is a recurring r/grafana topic

**Why it happens:** the OTLP receivers are not enabled, or bound to localhost inside the container. gRPC (4317) and HTTP/protobuf (4318, path /v1/traces) get mixed up. Ingestion and per-trace limits drop spans (rate limited, trace too large, live traces exceeded). Head sampling drops traces before they leave the app, very recent traces are still in the ingesters, and querier queues or response-size limits cut queries off.

**Diagnose:**

```bash
curl -s http://tempo:3200/ready
curl -s http://tempo:3200/metrics | grep -E '^tempo_(distributor_spans_received_total|discarded_spans_total)'
docker run --rm --net container:tempo nicolaka/netshoot ss -ltn | grep -E ':(4317|4318)'
docker exec shop-web printenv | grep '^OTEL_EXPORTER_OTLP'
```

```text
ready
tempo_distributor_spans_received_total{tenant="single-tenant"} 0
LISTEN 0 4096 127.0.0.1:4317 0.0.0.0:*
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
```

**What the output tells you:** Tempo is ready but has received zero spans: its gRPC receiver listens on 127.0.0.1 only, and the app sends gRPC to the HTTP port 4318, so the two never meet.

**Fix:**

```yaml
# tempo.yaml - listen on all interfaces inside the container
distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"
# App: OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318 with OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf,
#      or http://tempo:4317 with grpc - the protocol and the port must match
# Raise ingestion and per-trace limits only after reading tempo_discarded_spans_total by reason
```

**Why this fix works:** a receiver bound to 0.0.0.0 accepts connections from other containers, and a matching protocol and port pair lets the exporter's requests parse. Putting Alloy or an OpenTelemetry Collector in front adds batching, retries and tail sampling, so app restarts and Tempo restarts lose fewer spans.

**Prevent it:** alert on discarded spans, and put trace IDs into log lines so Loki and Tempo link in both directions.

**Next step:** [Performance & observability: logs and tracing](32-learn-performance-observability.md#14-logs-and-tracing) · [Senior architecture](39-learn-senior-architecture.md) · KodeKloud: *Fundamentals of SRE* — Observability and Monitoring · [Tempo troubleshooting](https://grafana.com/docs/tempo/latest/troubleshooting/)

**Community threads:** [Tempo docs: troubleshooting](https://grafana.com/docs/tempo/latest/troubleshooting/) · Search: [Reddit r/grafana](https://www.reddit.com/r/grafana/search/?q=tempo+trace+not+found&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=opentelemetry+tempo+4317+connection+refused)

## 10. ELK, OpenSearch and Graylog

### 10.1 Search cluster won't start or refuses clients

> **Seen as:** `bootstrap check failure [1] of [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]`, `master not discovered yet`, exit code 78 or 137; once it runs, `received plaintext http traffic on an https channel`, `missing authentication credentials for REST request`, `Kibana server is not ready yet` or `unable to find valid certification path to requested target` · **Where:** Docker or package installs on Ubuntu of Elasticsearch 8+, OpenSearch 2.12+ or the Wazuh indexer · **Level:** [L1 · Junior] · **How common:** on discuss.elastic.co "Kibana server is not ready yet" (about 257k views), "Missing Authentication for REST request" (about 125k) and "Master not discovered yet" (about 102k); on forum.opensearch.org the single-node Docker start error and the default dashboard password

**Why it happens:** vm.max_map_count defaults to 65530 on Ubuntu 22.04 and RHEL (Ubuntu 24.04 ships 1048576, so the check rarely fires there unless something lowered it), and it is a host kernel setting, not a container one; binding to a non-loopback address turns the production bootstrap checks on. A node without discovery settings, or with a data directory from another cluster, waits for a master forever. A heap larger than the container's memory limit gets it killed (137), and a data directory not writable by UID 1000 stops it. Once running, Elasticsearch 8 has TLS and authentication on by default, so http:// clients without credentials fail; Kibana 8 refuses the elastic superuser and needs kibana_system or a service token; Kibana and Elasticsearch versions must match; and OpenSearch 2.12+ requires a strong OPENSEARCH_INITIAL_ADMIN_PASSWORD.

**Diagnose:**

```bash
sysctl vm.max_map_count                      # this host is Ubuntu 22.04; 24.04 prints 1048576
docker logs --tail 20 es01 2>&1 | grep -m2 -E 'bootstrap check|master not discovered'
docker inspect -f '{{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}' es01
```

```text
vm.max_map_count = 65530
bootstrap check failure [1] of [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
78 OOMKilled=false
```

**What the output tells you:** exit code 78 is a failed bootstrap check, not a crash, and the check names the cause: the host's map count. Memory is fine (not OOM-killed).

**Fix:**

```bash
echo 'vm.max_map_count=1048576' | sudo tee /etc/sysctl.d/99-search.conf && sudo sysctl --system
# Elastic now recommends 1048576; OpenSearch and the Wazuh indexer ask for at least 262144
# One node: discovery.type=single-node. A new cluster: discovery.seed_hosts plus cluster.initial_master_nodes,
#   the latter only for the very first bootstrap. Heap within the limit: ES_JAVA_OPTS=-Xms2g -Xmx2g in a 4 GB container
sudo chown -R 1000:0 /srv/es/data
# Elasticsearch 8 clients: https, the cluster CA and a real user
docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .
curl --cacert http_ca.crt -u elastic https://localhost:9200/_cluster/health
docker exec -it es01 /usr/share/elasticsearch/bin/elasticsearch-reset-password -u kibana_system   # then into kibana.yml
```

**Why this fix works:** the bootstrap checks protect production nodes from settings that fail later under load, so meeting them is the fix, not disabling them. Clients that use https, trust the cluster CA and authenticate as a proper user are what a secure-by-default cluster expects; Logstash, Fluent Bit and Grafana each need the CA configured too. Don't turn security off (`xpack.security.enabled: false`) to make the errors go away.

**Prevent it:** sysctls set by Ansible on every log or SIEM host, data directories never reused across clusters, Kibana pinned to the Elasticsearch version, and the cluster CA distributed to clients like your Harbor CA.

**Next step:** [Wazuh & security tools](48-wazuh-and-security-tools.md), entries 6.1 and 6.6 · [Kernel & system](13-kernel-system.md) · KodeKloud: [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) · [Elastic: vm.max_map_count](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/vm-max-map-count)

**Community threads:** [discuss.elastic.co: plaintext HTTP traffic on an HTTPS channel](https://discuss.elastic.co/t/i-got-received-plaintext-http-traffic-on-an-https-channel-closing-connection-netty4httpchannel/302973) · [discuss.elastic.co: Kibana server is not ready yet on 8.0](https://discuss.elastic.co/t/kibana-server-is-not-ready-yet-on-elastic-8-0/297418) · [discuss.elastic.co top topics](https://discuss.elastic.co/top?period=all) · [forum.opensearch.org top topics](https://forum.opensearch.org/top?period=all) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22vm.max_map_count%22+65530+docker) · [Reddit r/elasticsearch](https://www.reddit.com/r/elasticsearch/search/?q=kibana+server+is+not+ready+yet&restrict_sr=1)

### 10.2 Graylog won't start or the login fails

> **Seen as:** `WARNING: MongoDB 5.0+ requires a CPU with AVX support, and your current system does not appear to have that!` followed by `Illegal instruction`; `Could not connect to http://127.0.0.1:9200`; the admin login is rejected; the web interface never appears · **Where:** a new Graylog stack in Docker or from packages, often inside a Proxmox VM · **Level:** [L1 · Junior] · **How common:** on the Graylog forum's top list: "default username and password not working" (about 62k views), "Could not connect to http://127.0.0.1:9200" (about 32k) and "web-interface not showing up" (about 29k); Graylog #13950 and graylog-docker #241 on AVX

**Why it happens:** MongoDB 5 and later need AVX, and Proxmox's default virtual CPU types do not pass it through. root_password_sha2 generated with plain `echo` hashes a trailing newline, so the password you type never matches; password_secret must be set and long (16 characters or more). Inside Docker, 127.0.0.1 is the Graylog container itself, not OpenSearch. And http_bind_address on 127.0.0.1, or a wrong http_external_uri behind a proxy, hides the web interface.

**Diagnose:**

```bash
grep -o -m1 -w avx /proc/cpuinfo || echo "no AVX"            # inside the VM
docker logs mongodb --tail 2
echo -n 'NEW_PASSWORD' | sha256sum | cut -d' ' -f1; grep '^GRAYLOG_ROOT_PASSWORD_SHA2' .env
```

```text
no AVX
WARNING: MongoDB 5.0+ requires a CPU with AVX support, and your current system does not appear to have that!
Illegal instruction (core dumped)
004e8bb555eb57bb2acfa52d6bd0c2fca13610cfd4979be826f8f331ad31fd15
GRAYLOG_ROOT_PASSWORD_SHA2=6a2d1251c68bb7c2215510e732854b44165bdc47691f426d8cad6c8ff963eec2
```

**What the output tells you:** the VM's CPU hides AVX, so MongoDB dies on its first instruction and Graylog has no configuration store; and the stored hash differs from the hash of the password, so it was made with a newline.

**Fix:**

```bash
# Proxmox: VM > Hardware > Processors > Type "host" (or an AVX-capable model such as x86-64-v3), then stop and start the VM
# Graylog's .env: a long secret and a hash made WITHOUT a newline
GRAYLOG_PASSWORD_SECRET=$(pwgen -N 1 -s 96)
GRAYLOG_ROOT_PASSWORD_SHA2=$(echo -n 'NEW_PASSWORD' | sha256sum | cut -d' ' -f1)
# Reachable settings in containers
#   GRAYLOG_HTTP_BIND_ADDRESS=0.0.0.0:9000
#   GRAYLOG_HTTP_EXTERNAL_URI=https://graylog.example.com/
#   GRAYLOG_ELASTICSEARCH_HOSTS=http://opensearch:9200
```

**Why this fix works:** the "host" CPU type exposes the physical CPU's instruction sets, AVX included, which MongoDB is compiled for; a reboot inside the guest is not enough, the VM must be stopped and started. `echo -n` hashes exactly the password, and service names replace a localhost that points at the wrong container. Pinning MongoDB 4.4 to avoid AVX is a last resort, since it is end-of-life.

**Prevent it:** check CPU flags before choosing VM CPU types, start from Graylog's official Compose files, and keep the secrets in your secret store.

**Next step:** [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Docker networking](30-learn-docker.md) · KodeKloud: [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) · [Graylog community](https://community.graylog.org/top?period=all)

**Community threads:** [Graylog2/graylog2-server #13950](https://github.com/Graylog2/graylog2-server/issues/13950) · [Graylog2/graylog-docker #241](https://github.com/Graylog2/graylog-docker/issues/241) · [community.graylog.org top topics](https://community.graylog.org/top?period=all) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=mongodb+avx&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=graylog+root_password_sha2+login+not+working)

### 10.3 Ingest: wrong timestamps, grok failures, _type

> **Seen as:** events shifted by your UTC offset; tags `_grokparsefailure` and `_dateparsefailure`; `mapper_parsing_exception failed to parse field [@timestamp]`; Fluent Bit's `Action/metadata line [1] contains an unknown parameter [_type]`; `[input] tail.0 paused (mem buf overlimit)` · **Where:** shipping Apache, Traefik, syslog and container logs into Elasticsearch, OpenSearch or Graylog · **Level:** [L2 · Mid-level] · **How common:** "How to set @timestamp timezone?" (about 115k views) and "Replace @timestamp with actual timestamp from log file" (about 97k) on discuss.elastic.co; "Timezone Graylog Server" (about 50k) on the Graylog forum; Fluent Bit #4155 (98 comments) and #5217 (64) on stuck or skipped logs

**Why it happens:** stores keep UTC and UIs show browser time, and timestamps without a zone are parsed as UTC. Grok patterns that do not match the real line tag events instead of dropping them. The same field name arrives with different types from different sources. Elasticsearch 8 and OpenSearch 2.x removed mapping types, so the old `_type` parameter is rejected. When the output is slower than the input, the memory buffer limit pauses tail inputs and retries pile up.

**Diagnose:**

```bash
docker logs fluent-bit 2>&1 | grep -m1 -o 'unknown parameter \[_type\]'
curl -s http://127.0.0.1:2020/api/v1/metrics | jq -c '.output'      # needs HTTP_Server On
head -1 /var/log/apache2/access.log
```

```text
unknown parameter [_type]
{"es.0":{"proc_records":0,"proc_bytes":0,"errors":412,"retries":1236,"retries_failed":412}}
198.51.100.7 - - [03/Oct/2026:17:02:11 +0530] "GET /healthz HTTP/1.1" 200 312 "-" "kube-probe/1.35"
```

**What the output tells you:** every bulk request is rejected because of `_type`, so nothing is indexed and retries fill the buffer. The Apache line carries its own offset (+0530), so a date filter that reads it gets the right time without any timezone setting.

**Fix:**

```text
# Fluent Bit es output for Elasticsearch 8+ and OpenSearch 2.x (comments must sit on their own lines)
[OUTPUT]
    Name               es
    Match              *
    Host               es01
    Port               9200
    tls                On
    tls.ca_file        /etc/fluent-bit/http_ca.crt
    # security is on by default in Elasticsearch 8 (10.1): a dedicated writer user, password from the environment
    HTTP_User          fluent-bit
    HTTP_Passwd        ${FLUENT_ES_PASSWORD}
    Suppress_Type_Name On
    # Trace_Error On while debugging; storage.type filesystem on inputs to buffer on disk

# Logstash: parse the line, then take @timestamp from the line itself
filter {
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  date { match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"] target => "@timestamp" }
}
# Lines without a zone: add timezone => "Asia/Kolkata" (your zone) to the date filter
# Graylog: root_timezone in server.conf, each user's time zone, and the input's zone for senders without one
```

**Why this fix works:** Suppress_Type_Name stops sending the field modern clusters reject, a filesystem buffer lets inputs keep reading while the output catches up, and a date filter that reads the line's own offset makes @timestamp the time the event happened. Fix grok patterns against real lines in the Grok Debugger rather than loosening them until everything "matches".

**Prevent it:** applications log in UTC with ISO 8601 offsets or as JSON, explicit index templates for known fields, and an alert on output errors and retries.

**Next step:** [Logs & journal](06-logs-journal.md) · [Time & NTP](12-time-ntp.md) · KodeKloud: [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) · [Fluent Bit: Elasticsearch output](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch)

**Community threads:** [discuss.elastic.co top topics (timestamps and time zones)](https://discuss.elastic.co/top?period=all) · [Fluent Bit docs: Elasticsearch output](https://docs.fluentbit.io/manual/data-pipeline/outputs/elasticsearch) · [Fluent Bit issues sorted by comments (#4155, #5217)](https://github.com/fluent/fluent-bit/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=logstash+%40timestamp+timezone) · [Reddit r/elasticsearch](https://www.reddit.com/r/elasticsearch/search/?q=grokparsefailure&restrict_sr=1)

### 10.4 Read-only indices, yellow health, shard limit

> **Seen as:** `flood stage disk watermark [95%] exceeded on ... all indices on this node will be marked read-only`, `cluster_block_exception ... FORBIDDEN/12/index read-only / allow delete (api)`, health yellow or red with unassigned shards; months later `this action would add [2] total shards, but this cluster currently has [1000]/[1000] maximum shards open`, `CircuitBreakingException: [parent] Data too large` or `Limit of total fields [1000] has been exceeded` · **Where:** log and SIEM clusters (Elasticsearch, OpenSearch, the Wazuh indexer, Graylog's back end) running out of disk or shards, and single nodes with replicas · **Level:** [L2–L3 · Mid-level/Senior] · **How common:** "FORBIDDEN/12/index read-only / allow delete (api)" (about 59k views) and "CircuitBreakingException: [parent] Data too large" (about 88k) on discuss.elastic.co, Wazuh Google Group threads on the shard limit, and dedicated Elastic troubleshooting pages

**Why it happens:** the disk watermarks act in steps: at 85% no new shards go to the node, at 90% shards move away, and at 95% every index on the node becomes read-only-allow-delete. Log indices without a retention policy (ILM in Elastic, ISM in OpenSearch and Wazuh) fill the disk. A replica is never placed on the node holding its primary, so a single node with replicas stays yellow forever. Daily indices times shards times replicas reach the default 1000 shards per node, a small heap trips circuit breakers, and dynamic mapping of arbitrary JSON keys explodes the field count.

**Diagnose:**

```bash
ES='curl -s --cacert http_ca.crt -u elastic:PASSWORD https://localhost:9200'
$ES'/_cluster/health?filter_path=status,active_shards,unassigned_shards'; echo
$ES'/_cat/allocation?v&h=shards,disk.percent,disk.avail,node'
$ES'/_cat/indices/wazuh-alerts-*?h=index,pri,rep,store.size&s=index' | tail -2
```

```text
{"status":"yellow","active_shards":499,"unassigned_shards":499}
shards disk.percent disk.avail node
   499           95      9.8gb es01
wazuh-alerts-4.x-2026.10.02 3 1 2.3gb
wazuh-alerts-4.x-2026.10.03 3 1 1.2gb
```

**What the output tells you:** one node at 95% disk, so every index is now read-only; 499 primaries plus one replica each that can never be placed on a single node, which is why health stays yellow with 499 unassigned shards. The shard limit counts those unassigned replicas too, so daily indices with three primaries each already use 998 of the 1000 shards allowed.

**Fix:**

```bash
# 1. Free disk: delete the oldest indices you no longer need, by explicit name
#    (wildcard deletes are refused by default on recent versions)
$ES'/wazuh-alerts-4.x-2026.07.01' -X DELETE
# 2. A single node needs no replicas: set 0 now, and in the index template for new indices
$ES'/_all/_settings' -X PUT -H 'Content-Type: application/json' -d '{"index.number_of_replicas": 0}'
# 3. Current versions lift the read-only block once usage drops below the high watermark; older ones need:
$ES'/_all/_settings' -X PUT -H 'Content-Type: application/json' -d '{"index.blocks.read_only_allow_delete": null}'
# 4. Retention: an ILM or ISM policy that deletes after N days, and 1 primary shard for small daily indices
#    (raising cluster.max_shards_per_node to 1500 is a stop-gap, not a plan)
```

**Why this fix works:** freeing disk clears the flood stage, zero replicas match what one node can hold, and a delete policy keeps both disk and shard count flat. Heap of at most half the RAM (and under about 31 GB) and explicit mappings (or `dynamic: false`) address the breaker and field-limit errors. Don't raise the watermarks to 99%: a node with a full disk can corrupt indices.

**Prevent it:** a retention policy from day one, a disk alert at 75%, and alerts on shard count and heap usage.

**Next step:** [Wazuh & security tools](48-wazuh-and-security-tools.md), entries 6.3 to 6.5 · [Disk & storage](01-storage-disk.md) · KodeKloud: [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) · [Elastic: fix watermark errors](https://www.elastic.co/docs/troubleshoot/elasticsearch/fix-watermark-errors)

**Community threads:** [Elastic docs: fix watermark errors](https://www.elastic.co/docs/troubleshoot/elasticsearch/fix-watermark-errors) · [Elastic docs: red or yellow cluster health](https://www.elastic.co/docs/troubleshoot/elasticsearch/red-yellow-cluster-status) · [Wazuh Google Group: maximum shards open](https://groups.google.com/g/wazuh/c/AungE5r1llI) · [Wazuh FAQ: shards limit by node](https://desvelao.github.io/wazuh-faqs/faqs/elasticsearch-reached-shards-limit-by-node/) · Search: [Server Fault](https://serverfault.com/search?q=elasticsearch+yellow+unassigned+shards+single+node) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=maximum+shards+open&restrict_sr=1)

### 10.5 Graylog journal utilization too high

> **Seen as:** `Journal utilization is too high and may go over the limit soon. Please verify that your OpenSearch cluster is healthy and fast enough.`, `Uncommited messages deleted from journal`, the process buffer at 100%, failed indexing attempts · **Where:** a Graylog that has run for a while, at peak hours or after an OpenSearch problem · **Level:** [L2–L3 · Mid-level/Senior] · **How common:** the Graylog forum's top list has several such threads: "Graylog high journal utilization is too high" (42 replies), "Journal Utilization is too high" (about 19k views), "Process Buffer filling very fast during peak hours" and "Buffer process 100%" (about 17k)

**Why it happens:** the journal is Graylog's on-disk queue between inputs and OpenSearch. It fills when OpenSearch is slow, red or read-only (entry 10.4), when expensive extractors or pipeline rules (greedy regexes) saturate the process buffer, or when there are too few processors for the CPU count, too little heap, or a journal on a small disk (the default maximum is 5 GB).

**Diagnose:**

```bash
# UI first: System > Nodes > node details shows buffers and journal; System > Overview shows indexer failures
curl -s --cacert http_ca.crt -u admin:PASSWORD 'https://opensearch:9200/_cluster/health?filter_path=status'; echo
sudo tail -n 200 /var/log/graylog-server/server.log | grep -cE 'FORBIDDEN/12|read-only'
```

```text
{"status":"red"}
57
```

**What the output tells you:** the back end is red and refusing writes (the read-only block from entry 10.4), so the output buffer cannot drain and the journal grows; Graylog itself is healthy.

**Fix:**

```bash
# 1. Fix the back end first: disk, read-only blocks and health (entry 10.4)
# 2. Then make processing cheap: anchored regexes, fewer extractors, pipeline rules that stop early
# 3. Then size the node (server.conf): processbuffer_processors and outputbuffer_processors to the cores,
#    a larger Graylog heap, and message_journal_max_size with a disk to match
sudo systemctl restart graylog-server
```

**Why this fix works:** the journal only drains as fast as OpenSearch accepts writes, so a healthy back end is the real fix and the journal size only buys time. Cheaper processing and matching processor counts keep the buffers from becoming the bottleneck once the back end is healthy. Don't just enlarge the journal while the cluster is read-only: it delays the outage and the data loss.

**Prevent it:** alerts on journal utilisation, buffer usage and indexer failures, and a load test before onboarding a big log source.

**Next step:** [Slow system](23-playbook-slow-system.md) · [Databases, storage & backups](51-problems-databases-storage-backup.md) · KodeKloud: [*EFK Stack: Enterprise-Grade Logging and Monitoring*](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring) · [Graylog community](https://community.graylog.org/top?period=all)

**Community threads:** [community.graylog.org top topics (journal and buffers)](https://community.graylog.org/top?period=all) · Search: [Stack Overflow](https://stackoverflow.com/search?q=graylog+%22journal+utilization+is+too+high%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=graylog+journal+utilization&restrict_sr=1)

## 11. Prometheus at scale

### 11.1 Prometheus fills its disk or fails after a crash

> **Seen as:** `write /prometheus/wal/00000123: no space left on device`; after a crash `opening storage failed: block dir: ... open .../meta.json: no such file or directory` or `Encountered WAL read error, attempting repair`; retention that seems ignored · **Where:** a single Prometheus on a VM or Docker volume, months after the install or after the disk filled · **Level:** [L2 · Mid-level] · **How common:** storage sizing recurs in the top-reacted Prometheus issues (#6934 memory spikes during WAL replay, #1381 per-series retention), and the storage docs carry explicit warnings about NFS and compaction headroom

**Why it happens:** without a retention flag Prometheus keeps 15 days, and disks are sized by guess. retention.size counts the WAL and head chunks but deletes only whole blocks, and compaction briefly needs room for old and new blocks at once. A TSDB on NFS, EFS or other non-POSIX storage is unsupported and can corrupt. A crash or a full disk during compaction leaves a block directory without meta.json, or a damaged WAL segment.

**Diagnose:**

```bash
df -h /var/lib/docker | tail -1
VOL=$(docker volume inspect -f '{{.Mountpoint}}' PROJECT_prometheus-data); sudo du -sh "$VOL/wal"
curl -s localhost:9090/api/v1/status/flags | jq -r '.data | with_entries(select(.key | test("retention")))'
q 'increase(prometheus_tsdb_compactions_failed_total[6h])'
```

```text
/dev/sdb1        59G   57G  1.6G  98% /var/lib/docker
9.8G	/var/lib/docker/volumes/PROJECT_prometheus-data/_data/wal
{
  "storage.tsdb.retention.size": "0B",
  "storage.tsdb.retention.time": "90d"
}
{"host":"dokploy-1","instance":"localhost:9090","job":"prometheus"} 3
```

**What the output tells you:** 90 days with no size cap on a volume Docker images also use; compactions fail for lack of space, so the WAL keeps growing (9.8 GB) and the disk is nearly full.

**Fix:**

```bash
# Size it: retention seconds x samples per second x 2 bytes, plus 20-30% for the WAL and compaction
#   30 days x 333 samples/s x 2 B is about 1.7 GB; give Prometheus its own volume and both limits:
#   --storage.tsdb.retention.time=30d --storage.tsdb.retention.size=40GB   (at most ~80% of the volume)
# A corrupt block after a crash: stop, back up, move ONLY the block named in the error, start
docker stop PROMETHEUS_CONTAINER
sudo mkdir -p /root/prom-quarantine && sudo mv "$VOL/BLOCK_ULID" /root/prom-quarantine/
docker start PROMETHEUS_CONTAINER
# A WAL that will not repair: move wal/ aside as a last resort (the newest ~2 hours are lost)
```

**Why this fix works:** a size cap deletes the oldest blocks before the disk fills, and a dedicated volume stops image pulls and logs from competing with the TSDB. Moving only the named block keeps the rest of the history readable. Don't delete the whole data directory as a first move, and keep the TSDB on local ext4 or XFS, never NFS; for history beyond a few months, use remote_write to a long-term store (entry 11.5).

**Prevent it:** the DiskFullIn24h rule on the Prometheus volume, and alerts on `prometheus_tsdb_compactions_failed_total` and `prometheus_tsdb_wal_corruptions_total`.

**Next step:** [Capacity planning](32-learn-performance-observability.md#16-capacity-planning) · [Disk & storage](01-storage-disk.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals · [Prometheus storage](https://prometheus.io/docs/prometheus/latest/storage/)

**Community threads:** [Prometheus docs: storage (retention, sizing, NFS, recovery)](https://prometheus.io/docs/prometheus/latest/storage/) · [Prometheus issues sorted by reactions (#6934, #1381)](https://github.com/prometheus/prometheus/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=prometheus+%22opening+storage+failed%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=prometheus+disk+full+retention&restrict_sr=1)

### 11.2 Prometheus 2 to 3 upgrade breaks things

> **Seen as:** targets DOWN with `received unsupported Content-Type "text/html" and no fallback_scrape_protocol specified for target` or `non-compliant scrape target sending blank Content-Type`; panels filtering on `le="5"` suddenly empty; alerts no longer reaching an old Alertmanager · **Where:** an image tag bumped from v2 to v3, often through `:latest` · **Level:** [L3 · Senior] · **How common:** the official migration guide lists about ten breaking changes; strict Content-Type checks and le/quantile normalisation silently break home-grown exporters and dashboards

**Why it happens:** v3 validates the scrape Content-Type strictly where v2 fell back to text. The Alertmanager API v1 is gone, so `api_version: v2` (Alertmanager 0.16 or later) is required. le and quantile values are normalised to floats (le="5" becomes le="5.0"). Range selectors are left-open, `.` in regexes matches newlines, remote_write's enable_http2 defaults to false, `--enable-feature=agent` became `--agent`, and holt_winters was renamed. Only 2.55 or later can read a TSDB written by v3.

**Diagnose:**

```bash
# Run v3 beside v2 (another port, a copy of the config, its own data volume) and compare
q 'count by (job) (up == 0)'                                      # against the v3 instance
grep -rnE 'le=\\?"[0-9]+\\?"|holt_winters' grafana/dashboards/ prometheus/rules/ | head -2
grep -n 'api_version' prometheus/prometheus.yml
```

```text
{"job":"backup-exporter"} 1
grafana/dashboards/Infra/traefik.json:212:  "expr": "sum(rate(traefik_service_request_duration_seconds_bucket{le=\"5\"}[5m]))",
prometheus/prometheus.yml:14:      api_version: v1
```

**What the output tells you:** a home-grown exporter (a script serving text with the wrong Content-Type) fails the strict check, a dashboard filters on an integer le, and Prometheus still points at the removed Alertmanager API v1.

**Fix:**

```yaml
# A job you cannot fix yet: tell Prometheus how to parse it
  - job_name: backup-exporter
    fallback_scrape_protocol: PrometheusText0.0.4
    static_configs: [{targets: ["10.10.0.20:9469"]}]
alerting:
  alertmanagers:
    - api_version: v2                       # needs Alertmanager 0.16 or later
      static_configs: [{targets: ["alertmanager:9093"]}]
# Queries and rules: le="5" -> le="5.0"; holt_winters -> double_exponential_smoothing
#   (with --enable-feature=promql-experimental-functions); --enable-feature=agent -> --agent
```

**Why this fix works:** each change matches one documented breaking change, so the v3 instance scrapes, alerts and graphs like v2 did. Upgrading through 2.55 first gives you a rollback floor, because only 2.55 or later can read the new TSDB format. Fix the exporter properly afterwards (the right Content-Type header) instead of leaving the fallback forever.

**Prevent it:** pin `prom/prometheus:v3.x.y` and never use latest, upgrade a staging instance first, and attach the migration guide to the change request.

**Next step:** section 3, Upgrades without surprises · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* · [Prometheus 3 migration guide](https://prometheus.io/docs/prometheus/latest/migration/)

**Community threads:** [Prometheus docs: 3.0 migration guide](https://prometheus.io/docs/prometheus/latest/migration/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=fallback_scrape_protocol) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=prometheus+3+upgrade&restrict_sr=1)

### 11.3 kube-prometheus-stack on kubeadm

> **Seen as:** KubeControllerManagerDown, KubeSchedulerDown and etcd targets with `dial tcp NODE_IP:10257: connect: connection refused`; a ServiceMonitor that exists but never becomes a target; a chart upgrade failing with `metadata.annotations: Too long: must have at most 262144 bytes` · **Where:** a fresh Helm install on a kubeadm homelab or CKA-style cluster, or a major chart upgrade · **Level:** [L3 · Senior] · **How common:** prometheus-community/helm-charts #1500 (CRD annotations too long, 91 comments) and #1041 (admission webhooks during upgrades, 65) top the chart's issues; #1236 and kube-prometheus #718 document the kubeadm bind addresses

**Why it happens:** kubeadm binds kube-controller-manager (10257) and kube-scheduler (10259) to 127.0.0.1 and etcd metrics to 127.0.0.1:2381, and kube-proxy metrics default to 127.0.0.1:10249, so Prometheus in a pod is refused. With serviceMonitorSelectorNilUsesHelmValues true (the default), Prometheus only selects ServiceMonitors labelled with the Helm release. Helm installs CRDs once and never upgrades them, and client-side apply of the large CRDs exceeds the 256 KiB annotation limit.

**Diagnose:**

```bash
sudo ss -ltnp | grep -E ':(10257|10259|2381) '                     # on a control-plane node
kubectl -n monitoring get prometheus -o jsonpath='{.items[0].spec.serviceMonitorSelector}'; echo
kubectl get servicemonitor -A --show-labels | grep shop
```

```text
LISTEN 0 4096 127.0.0.1:10257 0.0.0.0:* users:(("kube-controller",pid=2210,fd=3))
LISTEN 0 4096 127.0.0.1:10259 0.0.0.0:* users:(("kube-scheduler",pid=2187,fd=3))
LISTEN 0 4096 127.0.0.1:2381  0.0.0.0:* users:(("etcd",pid=2055,fd=12))
{"matchLabels":{"release":"kps"}}
shop   shop-web   12d   app=shop-web
```

**What the output tells you:** the control-plane components listen on localhost only, so the scrapes are refused; and Prometheus selects ServiceMonitors labelled release=kps, which shop-web's is not.

**Fix:**

```bash
# Control plane: listen where Prometheus can reach, and keep it through kubeadm upgrades
#   kube-controller-manager.yaml and kube-scheduler.yaml: --bind-address=0.0.0.0
#   etcd.yaml: --listen-metrics-urls=http://127.0.0.1:2381,http://NODE_IP:2381
#   kube-proxy ConfigMap: metricsBindAddress: 0.0.0.0:10249
#   then the same values in the kubeadm ClusterConfiguration extraArgs, and firewall the ports to the cluster
# values.yaml: select every ServiceMonitor, not only the release's
#   prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues: false   (the same for podMonitor and rule)
# Major chart upgrades: apply the CRDs server-side first
helm pull prometheus-community/kube-prometheus-stack --version X.Y.Z --untar
kubectl apply --server-side --force-conflicts -f kube-prometheus-stack/charts/crds/crds/
```

**Why this fix works:** the components now listen on an address the Prometheus pod can reach, and writing the flags into the kubeadm configuration stops the next `kubeadm upgrade` from reverting the static pod manifests. A nil selector selects every ServiceMonitor; server-side apply stores no last-applied annotation, so the size limit no longer applies. Don't open these ports beyond the cluster network.

**Prevent it:** read the chart's upgrade notes for every major version, use ServerSideApply for CRDs in Argo CD, and keep a list of expected targets with an alert on TargetDown.

**Next step:** [Kubernetes (CKA)](31-learn-kubernetes.md) · [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Monitoring Kubernetes · *Helm for Beginners* · [*Kubernetes Monitoring Made Easy with Prometheus*](https://www.youtube.com/watch?v=6xmWr7p5TE0)

**Community threads:** [helm-charts #1236](https://github.com/prometheus-community/helm-charts/issues/1236) · [kube-prometheus #718](https://github.com/prometheus-operator/kube-prometheus/issues/718) · [helm-charts #1513](https://github.com/prometheus-community/helm-charts/issues/1513) · [helm-charts issues sorted by reactions (#1500, #1041)](https://github.com/prometheus-community/helm-charts/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kube-prometheus-stack+KubeControllerManagerDown+kubeadm) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=kube-prometheus-stack+controller+manager+down&restrict_sr=1)

### 11.4 Memory grows until OOM: cardinality

> **Seen as:** a Prometheus that was fine for months uses several GB, restarts slowly or dies with exit 137 (`OOMKilled: true`); `query processing would load too many samples into memory in query execution`; `sample limit exceeded`; `prometheus_tsdb_head_series` climbing every day · **Where:** after new exporters, apps or labels were added · **Level:** [L3–L4 · Senior to Senior/Lead] · **How common:** #5469 "Document memory planning guidelines" and #6934 "Memory usage spikes during WAL replay" are top-reacted Prometheus issues, and the official naming guide warns that every label combination is a new series

**Why it happens:** memory follows the number of active series, and series multiply with unbounded label values: user IDs, raw URL paths, request IDs, container IDs, full Docker label sets. Churn adds more, because every Swarm task or pod restart creates new series. Histograms multiply buckets by label values (Traefik with router labels on is a classic), and WAL replay at restart plus long-range dashboard queries add peaks.

**Diagnose:**

```bash
# Status > TSDB Status shows the same lists in the UI
curl -s localhost:9090/api/v1/status/tsdb | jq -r '.data.seriesCountByMetricName[:2][] | "\(.name) \(.value)"'
curl -s localhost:9090/api/v1/status/tsdb | jq -r '.data.labelValueCountByLabelName[:2][] | "\(.name) \(.value)"'
q 'topk(2, sum by (job) (scrape_series_added))'                    # churn per job
```

```text
http_server_request_duration_seconds_bucket 412880
traefik_router_request_duration_seconds_bucket 61440
path 51327
container_label_com_docker_swarm_task_id 2990
{"job":"shop-web"} 1840
{"job":"cadvisor"} 220
```

**What the output tells you:** one app histogram has 412,880 series because it labels requests with the raw path (51,327 distinct paths, with IDs inside the URLs); Traefik's router labels are on; and Swarm task IDs leak in as labels, so every deploy adds new series.

**Fix:**

```yaml
# prometheus.yml, per job - stop the flood at ingestion while the source is being fixed
    sample_limit: 20000                     # the scrape fails loudly instead of filling the TSDB
    label_limit: 30
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: http_server_request_duration_seconds_bucket
        action: drop
      - regex: container_label_com_docker_swarm_task_id
        action: labeldrop
# At the source: route templates (/users/:id) instead of raw paths, IDs in logs and traces only,
# Traefik addRoutersLabels: false, cAdvisor --store_container_labels=false with a short whitelist
```

**Why this fix works:** removing the label that explodes cuts series by orders of magnitude, and the limits turn a silent memory leak into a failing target that pages someone. Only after the series count is under control do more memory and recording rules for heavy queries make sense; adding RAM first just delays the next OOM.

**Prevent it:** a graph of head series and churn per job, an alert when series jump, for example `prometheus_tsdb_head_series > 1.3 * (prometheus_tsdb_head_series offset 1d)`, and a series count for every new exporter in staging (section 3).

**Next step:** [Observability pillars and cardinality](32-learn-performance-observability.md#10-observability-pillars-and-cardinality) · [Memory](04-memory.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Instrumentation · [Prometheus naming practices](https://prometheus.io/docs/practices/naming/)

**Community threads:** [Prometheus docs: metric and label naming](https://prometheus.io/docs/practices/naming/) · [Prometheus issues sorted by reactions (#5469, #6934)](https://github.com/prometheus/prometheus/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=cardinality+OOM&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=prometheus+high+cardinality+memory)

### 11.5 remote_write lag and out-of-order samples

> **Seen as:** `Failed to send batch, retrying ... server returned HTTP status 429 Too Many Requests`, `server returned HTTP status 400 Bad Request: out of order sample`, `Skipping resharding, last successful send was beyond threshold`, `Error on ingesting out-of-order samples` · **Where:** Prometheus pairs shipping to a central long-term store (Mimir, Thanos receive, VictoriaMetrics), or rules and exporters with explicit timestamps · **Level:** [L4 · Senior/Lead] · **How common:** kube-prometheus-stack #1177 (out-of-order results from rule evaluation) and #5483 (out-of-order samples only when scraping cAdvisor) are among the chart's most-reacted issues

**Why it happens:** the receiver throttles the tenant or is slow, so the shards back up and the WAL grows. HA replicas send identical series without a replica label, or the receiver does not deduplicate. Exporters with explicit timestamps (cAdvisor, federation, Pushgateway), duplicate jobs or rule groups produce the same series twice. And clocks drift when outbound NTP is blocked on-prem.

**Diagnose:**

```bash
q 'prometheus_remote_storage_highest_timestamp_in_seconds - ignoring(remote_name, url) group_right prometheus_remote_storage_queue_highest_sent_timestamp_seconds'
q 'rate(prometheus_remote_storage_samples_failed_total[5m])'
timedatectl | grep -E 'synchronized|NTP service'; chronyc tracking | grep 'System time'
```

```text
{"host":"dokploy-1","instance":"localhost:9090","job":"prometheus","remote_name":"mimir","url":"https://mimir.example.com/api/v1/push"} 1835.2
{"host":"dokploy-1","instance":"localhost:9090","job":"prometheus","remote_name":"mimir","url":"https://mimir.example.com/api/v1/push"} 412.7
System clock synchronized: no
              NTP service: active
System time     : 41.208734193 seconds slow of NTP time
```

**What the output tells you:** this Prometheus is half an hour behind (1835 s) and about 400 samples a second are rejected; its clock is 41 seconds slow and unsynchronised, so its samples land out of order next to its HA twin's.

**Fix:**

```yaml
global:
  external_labels:
    cluster: onprem-1
    __replica__: prometheus-a             # Mimir's default HA labels are cluster and __replica__
remote_write:
  - url: https://mimir.example.com/api/v1/push
    queue_config:
      capacity: 10000
      max_shards: 50
      max_samples_per_send: 2000
    write_relabel_configs:                # ship only what the central store needs
      - source_labels: [__name__]
        regex: 'go_.*|process_.*'
        action: drop
# Fix NTP first (allow outbound UDP 123, or use an internal NTP server); honor_timestamps: false on misbehaving
# exporters; remove duplicate jobs and rule groups; a receiver-side out-of-order window only for genuinely late data
```

**Why this fix works:** with a correct clock and a replica label, the receiver keeps one sample per series and timestamp and drops the twin's copy; a larger queue drains the backlog once the receiver accepts the rate, and write relabeling cuts what must be sent at all. Raising receiver limits blindly only moves the bottleneck.

**Prevent it:** alerts on remote-write lag above a few minutes, on any failed samples and on `node_timex_sync_status == 0`, and meta-monitoring of the receiver itself.

**Next step:** [Time & NTP](12-time-ntp.md) · [Senior architecture](39-learn-senior-architecture.md) · [Cloud & AWS](36-learn-cloud-aws.md) · KodeKloud: *Fundamentals of SRE* · [Prometheus storage](https://prometheus.io/docs/prometheus/latest/storage/)

**Community threads:** [Prometheus docs: storage (out-of-order window, remote storage)](https://prometheus.io/docs/prometheus/latest/storage/) · [helm-charts issues sorted by reactions (#1177, #5483)](https://github.com/prometheus-community/helm-charts/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Error+on+ingesting+out-of-order+samples%22) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=remote_write+429&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises on the two lab VMs, plus a third VM for exercises 9 and 10. Snapshot first, break it exactly as described, fix it using only the entry, and write your five-line note.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Start Grafana on a root-owned bind-mounted data directory, then change GF_SECURITY_ADMIN_PASSWORD and log in | 10 min | 6.1 |
| 2 | Fresher | Point Uptime Kuma at https://shop.example.com from inside the LAN and at localhost:3000 | 10 min | 7.1 |
| 3 | Junior | Delete dokploy-2's UFW rule for 9100 and explain the exact target error | 10 min | 5.1 |
| 4 | Junior | Run node_exporter as a plain container with -p 9100:9100 and no host mounts; make the disk and systemd alerts work | 15 min | 5.3 |
| 5 | Junior | Attach Grafana to dokploy-network only, then fix both data sources | 10 min | 6.4 |
| 6 | Mid-level | Block outbound 587 on dokploy-1 and find which alert gate is closed | 20 min | 8.1 |
| 7 | Mid-level | Add a container label in Alloy, redeploy an app five times, and read Loki's discard reasons | 20 min | 9.3 |
| 8 | Mid-level | Set retention_period without the compactor's retention and fill the Loki volume with a log generator | 25 min | 9.4 |
| 9 | Senior | Install kube-prometheus-stack on a kubeadm lab and bring every control-plane target UP | 45 min | 11.3 |
| 10 | Senior/Lead | Push a single-node OpenSearch past the flood stage, recover it, and add a delete policy | 45 min | 10.4 |

Quick questions to answer from memory:

1. Why does a scrape from a Prometheus container to a host port behind UFW time out instead of being refused?
2. Which three Alertmanager timers decide when a notification goes out, and what are their defaults?
3. Why does retention_period alone never shrink Loki's disk?
4. What makes a label high-cardinality, and where do you look for it in Prometheus and in Loki?
5. Why must probe jobs carry the same host label as the node job?

---

## Where to go next

- [Performance & observability](32-learn-performance-observability.md): the theory behind this module, from USE and RED to SLOs, plus the homelab lab in §17.
- [Slow system](23-playbook-slow-system.md): the incident playbook that turns these metrics into a diagnosis.
- [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) and [Traefik deep dive](43-traefik-and-reverse-proxies.md): the platform this stack watches, including Traefik's metrics and access log.
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md): the GitLab pipeline that validates and deploys the monitoring repository.
- [Wazuh & security tools](48-wazuh-and-security-tools.md): the OpenSearch-based indexer behind entries 10.1 and 10.4, and security monitoring next to operations monitoring.
- [Databases for DevOps](38-learn-databases-ops.md) and [Databases, storage & backups](51-problems-databases-storage-backup.md): exporters and alerts for PostgreSQL and Redis, and the backups this module only touches.
- [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) and [Cloud & AWS](36-learn-cloud-aws.md): monitoring hosts on Proxmox and in AWS, where CloudWatch joins the picture.
- [Senior architecture](39-learn-senior-architecture.md) and [Career ladder](40-career-ladder.md): turn the alert review, the cardinality budget and a tested dead man's switch into senior-level evidence.
- Official docs: [Prometheus](https://prometheus.io/docs/) · [Grafana](https://grafana.com/docs/grafana/latest/) · [Loki](https://grafana.com/docs/loki/latest/) · [Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/) · [Zabbix](https://www.zabbix.com/documentation) · [Uptime Kuma](https://github.com/louislam/uptime-kuma) · [Netdata](https://learn.netdata.cloud/docs/netdata-agent/installation/docker) · [Elastic](https://www.elastic.co/docs/troubleshoot/elasticsearch/fix-common-cluster-issues).
