# 45 — Dokploy Deep Dive & Self-Hosted PaaS Problems (Dokploy, Coolify, CapRover)

This module teaches Dokploy as a tool: how it is built, how to install it, how to run it day to day, and how to learn it from fresher to senior. It then collects 39 problems that people really hit with Dokploy, Coolify and CapRover. They come from GitHub issues sorted by comments and reactions, the official troubleshooting pages and forum threads, and Stack Overflow and Reddit are reachable through search links. Every command is documented for you to run on your own lab VM or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Dokploy sits where most of your daily work happens: Docker, Swarm, Traefik, DNS, TLS and your GitLab → Harbor pipeline. Use the part that matches your stage, then move up.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | sections 1–2, entries 5.1 and 6.2 | you install Dokploy on a lab VM and publish one app on a domain |
| Junior | L1 Operator | sections 2–3 and every L1 entry | you fix a 404, a 502, a missing variable and a full disk without help |
| Mid-level | L2 Troubleshooter | the problem library, sections 6 to 11 | you explain any outage from docker and Traefik evidence alone |
| Senior | L3 Platform | sections 3, 9, 12 and 13 | GitLab CI → Harbor (private CA) → Dokploy runs on two nodes with a tested rollback |
| Senior/Lead | L4 SRE | section 3 and entries 10.3, 10.4, 13.1 | you run DR drills and write the upgrade policy others follow |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** build a lab VM (Ubuntu 24.04, 2 vCPU, 4 GB RAM, 40 GB disk), take a snapshot, install Dokploy, then break one thing at a time on purpose. Fix it using only the entry, and write a five-line note: symptom, evidence, cause, fix, prevention. The Self-check at the end gives ten timed exercises. Never practise on production.

**Placeholders and examples:** UPPERCASE words are placeholders (SERVER_IP, SERVICE, CONTAINER, APP). The examples use 192.0.2.10 for the manager, 192.0.2.20 for a remote server, 10.0.0.0/24 for a private cluster network, 203.0.113.10 for the public address, the user ops, and names under example.com (dokploy.example.com, shop.example.com, harbor.example.com, gitlab.example.com).

**sudo and docker:** `docker` commands are shown without sudo, which assumes your admin user is in the docker group (membership is root-equivalent, so grant it only to admins). Otherwise prefix them with `sudo`. Commands that touch files under /etc or system services already carry sudo.

> 📚 **Study path:** KodeKloud *Docker Training Course for the Absolute Beginner* (Docker Networking, Docker Compose) → *Docker Certified Associate* (Docker Swarm section) → handbook [Docker: Swarm for Dokploy](30-learn-docker.md) and [Docker & K8s incidents: Dokploy, Traefik and Swarm](26-playbook-containers-k8s.md) → [Dokploy troubleshooting docs](https://docs.dokploy.com/docs/core/troubleshooting) → lab: install Dokploy on a scratch VM and work through the Self-check.

---

## 1. Dokploy in 10 minutes

### What Dokploy is

Dokploy is an open-source, self-hosted PaaS: a web UI and API that turn a Git repository or a container image into a running service with a domain and a certificate, on servers you own. Under the hood it is three things you already know: **Docker Swarm** runs the containers, **Traefik v3** routes traffic and gets certificates, and a **Next.js panel** with its own **Postgres** stores your projects, settings and deployment history. Installs from older versions may also run a **dokploy-redis** service, which held the deployment queue; current installers no longer create it (v0.30.0 removed the last Redis code). It also manages databases, S3 backups, remote servers, notifications and one-click templates.

Keep one sentence in mind: *Dokploy is Traefik plus Swarm plus a UI.* When something breaks, the UI rarely tells you why. `docker service ps`, `docker service logs`, `docker logs dokploy-traefik` and the files under `/etc/dokploy` do.

### Architecture at a glance

```text
                    clients (Internet / LAN)
                              |
          80/tcp, 443/tcp+udp |                  3000/tcp (setup only)
                              |                         |
+-----------------------------v-------------------------v---------------+
| Ubuntu host = Swarm manager (192.0.2.10)                              |
|                                                                       |
|  [dokploy-traefik]  plain container, Traefik v3, owns 80/443          |
|     static : /etc/dokploy/traefik/traefik.yml                         |
|     dynamic: /etc/dokploy/traefik/dynamic/*.yml  (watched, live)      |
|     labels : read through docker.sock (Compose services)              |
|          |                                                            |
|  ========|============ overlay network: dokploy-network ============  |
|          |                    |                     |                 |
|   [applications]       [compose projects]     [databases]             |
|   Swarm services       containers or stacks   Swarm services          |
|                                                                       |
|  [dokploy]           Swarm service: UI, API, clones, builds           |
|                      mounts docker.sock and /etc/dokploy              |
|  [dokploy-postgres]  panel state  (older installs: [dokploy-redis])   |
+-----------------------------------------------------------------------+
        | SSH: remote servers (own Docker + own Traefik)
        | swarm join: cluster workers (run replicas, pull from a registry)
```

### The moving parts

| Part | Runs as | Job | First look when it misbehaves |
|---|---|---|---|
| dokploy | Swarm service, 3000/tcp in host mode | UI, API, clones and builds, writes Traefik config | `docker service logs dokploy --since 10m` |
| dokploy-postgres | Swarm service (password in a Docker secret) | projects, services, domains, users, settings | `docker service logs dokploy-postgres --since 10m` |
| dokploy-redis (older installs only) | Swarm service; current installers don't create it | deployment queue in older versions | `docker service ls --filter name=dokploy-redis` |
| dokploy-traefik | plain container (not a service) | 80/443, routing, Let's Encrypt | `docker logs --tail 100 dokploy-traefik` |
| dokploy-network | attachable overlay network | joins Traefik, apps and databases | `docker network inspect dokploy-network` |
| /etc/dokploy | host directory | Traefik files, code checkouts, file mounts, logs | `sudo ls /etc/dokploy` |

### How a request reaches your app

1. DNS resolves shop.example.com to the server (203.0.113.10 from outside, 192.0.2.10 on internal DNS).
2. TCP 443 lands on dokploy-traefik. It is published directly, not through Swarm's ingress mesh, so IPv4 client addresses survive.
3. Traefik matches a router by Host (and optional path). Dokploy generates the routes: as dynamic files for applications (they apply at once), and as container labels for Compose services (they apply at the next deploy). Recent versions can also carry traefik.* labels on an application's Swarm service, so check both places (entry 6.6).
4. The router's service points at the Swarm service name and container port on dokploy-network, for example `http://shop-web-x7k2p:3000`.
5. The container answers and Traefik returns the response.

Each failure has its own signature, and the signature tells you which layer answered:

| You see | Who answered | Meaning | Entry |
|---|---|---|---|
| 404 page not found (plain text) | Traefik | no router matched this host, path or entrypoint | 6.1, 6.6 |
| 502 Bad Gateway | Traefik | router matched, the backend refused the connection | 6.2, 6.7 |
| 503 no available server | Traefik | router matched, no healthy backend | 6.2 |
| 504 Gateway Timeout | Traefik | backend unreachable or too slow | 6.3, 6.8 |
| TRAEFIK DEFAULT CERT | Traefik | no certificate for this name yet | 7.1 |
| connection timed out | network or firewall | the request never reached Traefik | 5.1 |

### How a deploy runs

1. A trigger arrives: the Deploy button, a Git webhook, a registry webhook or an API call.
2. The job waits its turn in the deployment queue (held in dokploy-redis on older versions).
3. Source: Dokploy clones the repository into the service's code directory under /etc/dokploy, fresh on every deploy, or skips this step and pulls an image.
4. Build: Nixpacks, Railpack, Dockerfile, Buildpacks or static, on the target server unless you build in CI.
5. Run: applications become `docker service create/update`. Compose services run as `docker compose up` (or `docker stack deploy` in Stack mode) with Traefik labels and the network added.
6. Route: Traefik picks up the new file or labels.
7. Logs: build-time failures are in the deployment log (Deployments tab), runtime failures in the service logs.

### Applications, Compose and databases

| Aspect | Application | Docker Compose | Database |
|---|---|---|---|
| What it is | one service, built from Git or pulled as an image | your compose file, one or many services | Postgres, MySQL, MariaDB, MongoDB or Redis |
| Runs as | Swarm service | compose project (or a stack in Stack mode) | Swarm service |
| Domains | generated route, live at once | labels added at deploy, redeploy needed | internal host name, optional external port |
| Health, scaling, rollback | Swarm settings in the UI | whatever the compose file says | single instance |
| Persistent data | Mounts: volume, bind or file mount | named volumes or ../files paths | managed volume plus scheduled S3 backups |
| Typical use | your own apps and APIs | third-party stacks, templates, multi-container apps | app databases |

### Build types

| Build type | How it builds | Use it for | Watch out |
|---|---|---|---|
| Nixpacks | detects the language and writes a build plan | quick prototypes | detection surprises; upstream is in maintenance |
| Railpack | Nixpacks' successor (newer Dokploy versions) | the same, with newer runtimes | check that your version has it |
| Dockerfile | your Dockerfile, build path and target | production; the same file builds in CI | nothing beyond normal Docker |
| Buildpacks (Heroku, Paketo) | Cloud Native Buildpacks | teams already on buildpacks | large images, slow builds |
| Static | serves a folder of built files | static sites | build the site first |
| Docker image | no build, pulls from a registry | CI-built images from Harbor (your target setup) | registry login and CA trust (9.3) |

### Where Dokploy fits on your servers

```text
developer --push--> GitLab (gitlab.example.com)
                       |
            GitLab CI runner: test, build, scan
                       |  docker push (robot account, private CA)
                       v
            Harbor (harbor.example.com) <------ pull (CA trusted on every node)
                       |                                    |
   last CI job: POST /api/application.deploy (x-api-key)   |
                       v                                    |
            Dokploy panel ---- docker service update -------+
                       |
            dokploy-traefik :443 ---> app containers on dokploy-network
                       |
            legacy Apache on 81/444 through a dynamic file (entry 6.7)
```

The CI side of this picture lives in [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), the proxy side in [Traefik deep dive](43-traefik-and-reverse-proxies.md), and the security side (Wazuh agent on every host, Traefik access logs, Docker events) in [Wazuh & security tools](48-wazuh-and-security-tools.md). Your own migration story, Apache moved to 81/444 so Traefik could take 80/443, is [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md).

### Dokploy, Coolify and CapRover side by side

| Aspect | Dokploy | Coolify v4 | CapRover |
|---|---|---|---|
| Runs apps on | Swarm services and Compose projects | Docker Compose on each server, driven over SSH | Swarm services |
| Edge proxy | Traefik v3 (dokploy-traefik) | Traefik (coolify-proxy) or Caddy | Nginx (captain-nginx) with Certbot |
| Control plane | Next.js and TypeScript, Postgres (plus Redis in older versions) | Laravel and PHP, Postgres, Redis, a websocket service | Node.js and TypeScript, state in /captain |
| First login | port 3000, then a domain | port 8000, then a domain | port 3000, then captain.ROOT_DOMAIN |
| More servers | remote servers over SSH, Swarm workers | any number of servers over SSH | Swarm workers |
| Builds | Nixpacks, Railpack, Dockerfile, Buildpacks, static, image | Nixpacks, Dockerfile, Compose, static, image | captain-definition, Dockerfile, image |
| Backups | databases, volumes and the panel to S3 | scheduled database backups to S3 | configuration backup; app data is your job |
| CI hooks | API with x-api-key, Git and registry webhooks | API tokens, webhooks | CLI deploys with app tokens, webhooks |
| Typical pain | Swarm networking, routing regressions after upgrades | SSH and server validation, proxy and helper containers | Nginx templates, persistent-data flag, wildcard DNS |
| Choose it when | you want Swarm and Traefik you can debug with plain docker (your setup) | you want Compose-native deploys and a large one-click catalogue | you want a mature, minimal Swarm PaaS with a CLI flow |

All three share the same failure classes, which is why the problem library mixes them: wrong port (502), missing route (404), certificate not issued, Docker networking, disk, upgrades.

### When a PaaS stops being enough

A PaaS on Swarm is a sound choice for a handful of servers and teams. Plan a move to Kubernetes (k3s or kubeadm, with ArgoCD) when you need several of these at once: many teams with quotas and RBAC, autoscaling on metrics, GitOps with drift detection, network policies between tenants, or multi-site failover. Until then, the skills in this module (Swarm, Traefik, registries, backups) transfer directly. See [Kubernetes (CKA)](31-learn-kubernetes.md).

---

## 2. Install and first configuration

This is the homelab-safe path: a VM you can snapshot, an explicit cluster address, the panel reached through an SSH tunnel, then a domain with HTTPS before anything else is exposed.

### Before you install

- Ubuntu 24.04 or 22.04 in a VM, not an unprivileged LXC container (entry 5.4 explains why).
- 2 vCPU, 4 GB RAM (2 GB is the floor), 40 GB disk; /var/lib/docker on its own volume if you can.
- A static address in netplan, and DNS names ready: dokploy.example.com for the panel, one name per app.
- Ports 80, 443 and 3000 free on the host; 80 and 443 reachable from wherever certificates get validated.
- A Docker address range agreed with the network team that overlaps no office, VPN or other Docker host (entry 11.3).

```bash
# Who owns the ports the installer needs?
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'
# Which addresses does the host have? Pick the one other nodes will use.
ip -o -4 addr show scope global
# Docker already here?
docker version --format '{{.Server.Version}}' 2>/dev/null || echo "no docker"
df -h / /var/lib
```

```text
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511          0.0.0.0:80         0.0.0.0:*     users:(("apache2",pid=1123,fd=4))
LISTEN 0      511          0.0.0.0:443        0.0.0.0:*     users:(("apache2",pid=1123,fd=6))
2: ens18    inet 192.0.2.10/24 brd 192.0.2.255 scope global ens18\       valid_lft forever preferred_lft forever
no docker
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        39G  4.1G   33G  12% /
/dev/sda2        39G  4.1G   33G  12% /
```

Apache on 80/443 is exactly the incident from [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md); entry 5.2 shows both ways out.

### Install with an explicit advertise address

```bash
# Download and read the script before running it as root
curl -sSL https://dokploy.com/install.sh -o dokploy-install.sh
less dokploy-install.sh
# Variables go AFTER sudo, because sudo resets the environment
sudo ADVERTISE_ADDR=192.0.2.10 sh dokploy-install.sh
# Decided once, at swarm init: an overlay pool that fits your IP plan
#   sudo ADVERTISE_ADDR=192.0.2.10 DOCKER_SWARM_INIT_ARGS="--default-addr-pool 10.200.0.0/16" sh dokploy-install.sh
# Only inside LXC (prefer a VM): add ENDPOINT_MODE=dnsrr (Proxmox LXC is also auto-detected)
# Pin the panel version instead of "latest stable": add DOKPLOY_VERSION=vX.Y.Z
```

The installer must run as root. It checks the three ports, installs a pinned Docker version if Docker is missing (DOCKER_VERSION at the top of the script, 28.5.0 at the time of writing) and holds the docker-ce packages with apt-mark, initialises Swarm with your address, creates the dokploy-network attachable overlay and /etc/dokploy, stores a generated Postgres password and an auth secret as Docker secrets, starts dokploy-postgres and dokploy as Swarm services, and runs dokploy-traefik as a plain container on dokploy-network, publishing 80/tcp and 443/tcp+udp. The panel image is tagged with the latest stable release it detects on GitHub (for example dokploy/dokploy:v0.30.6), not :latest. Older versions of the script also created a dokploy-redis service. Read your copy of the script to confirm these details for the version you install.

### Verify the install

```bash
docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'
docker ps --filter name=dokploy-traefik --format '{{.Names}}  {{.Status}}  {{.Ports}}'
docker network ls --filter name=dokploy-network
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000
```

```text
NAME               REPLICAS   IMAGE
dokploy            1/1        dokploy/dokploy:v0.30.6
dokploy-postgres   1/1        postgres:16
dokploy-traefik  Up 3 minutes  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp
NETWORK ID     NAME              DRIVER    SCOPE
w3k1p9zq0d2e   dokploy-network   overlay   swarm
200
```

Every service at 1/1, Traefik up on 80/443, the overlay present, and the panel answering locally (200, or a redirect to the sign-up page). If any line differs, start at entry 5.1 or 11.2.

### First login over an SSH tunnel

```bash
# On your laptop: forward local port 3000 to the server's port 3000
ssh -N -L 3000:localhost:3000 ops@192.0.2.10
# Then open http://localhost:3000 and create the admin account
```

Use a long unique password and turn on two-factor authentication in your profile straight away. Invite colleagues as their own users instead of sharing the admin login. The panel controls docker.sock, so treat it like root.

### Give the panel a domain, then close 3000

Create an A record for dokploy.example.com, set it as the panel's domain in the web-server settings with Let's Encrypt (public servers) or your own certificate (internal), and check it from another machine. Only then stop publishing port 3000. Docker-published ports bypass UFW, so unpublishing is the real fix (entry 13.2).

```bash
dig +short dokploy.example.com
curl -sI https://dokploy.example.com | head -1
docker service update --publish-rm "published=3000,target=3000,mode=host" dokploy
# Emergency access later: re-add it, tunnel in, remove it again
#   docker service update --publish-add "published=3000,target=3000,mode=host" dokploy
```

### Connect Harbor and GitLab

**Harbor.** Create a project robot account with pull permission (for example robot$shop+dokploy) and add Harbor in the panel's registry settings: name, URL, username, secret. Every Docker host that will pull, including workers and remote servers, must trust your private CA:

```bash
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp corp-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
sudo cp corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt && sudo update-ca-certificates
docker login harbor.example.com -u 'robot$shop+dokploy'      # prompts for the robot secret
docker pull harbor.example.com/shop/web:1.4.2
```

**GitLab.** You have two options. The GitLab provider is an OAuth application in GitLab whose redirect URL Dokploy shows you; it lets Dokploy list your repositories. The plain Git source with an SSH deploy key works with any self-managed GitLab and avoids HTTPS trust problems (entry 9.3). On-prem, the deploy key is usually the calmer choice.

### Deploy a Harbor image with a domain

1. Create a project (shop), then an Application (web).
2. Provider: Docker. Image harbor.example.com/shop/web:1.4.2, with the Harbor registry selected.
3. Environment: PORT=3000 and the variables the app needs.
4. Domains: shop.example.com, path /, container port 3000, HTTPS on, Let's Encrypt or your certificate.
5. Deploy and read the deployment log to the end.

```bash
docker service ls --filter name=shop-web --format '{{.Name}} {{.Replicas}} {{.Image}}'
sudo ls /etc/dokploy/traefik/dynamic/
sudo cat /etc/dokploy/traefik/dynamic/shop-web-x7k2p.yml
curl -s -o /dev/null -w '%{http_code}\n' https://shop.example.com/healthz
```

A generated route looks roughly like this (simplified; names and details vary by version):

```yaml
http:
  routers:
    shop-web-x7k2p-router-1:
      rule: Host(`shop.example.com`)
      service: shop-web-x7k2p-service-1
      entryPoints: [web]
      middlewares: [redirect-to-https@file]
    shop-web-x7k2p-router-websecure-1:
      rule: Host(`shop.example.com`)
      service: shop-web-x7k2p-service-1
      entryPoints: [websecure]
      tls:
        certResolver: letsencrypt
  services:
    shop-web-x7k2p-service-1:
      loadBalancer:
        servers:
          - url: http://shop-web-x7k2p:3000
        passHostHeader: true
```

Read it like any Traefik config: the Host rule, the entrypoints, the certificate resolver, and a backend URL made of the Swarm service name (with its random suffix) and the container port. Most 404 and 502 investigations end in a file like this or in the container's labels.

### Deploy a Compose stack the Dokploy way

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.2
    env_file: [.env]                      # Dokploy writes the Environment tab to .env
    expose: ["8080"]                      # no ports: Traefik reaches it over dokploy-network
    volumes:
      - ../files/uploads:/app/uploads     # outside the re-cloned code directory
    networks: [dokploy-network]
    restart: unless-stopped
  worker:
    image: harbor.example.com/shop/api:1.4.2
    command: ["node", "worker.js"]
    env_file: [.env]
    networks: [dokploy-network]
networks:
  dokploy-network:
    external: true
```

Then open Domains, pick service api, port 8080, host api.example.com, and deploy. The labels are injected at deploy time, so every domain change needs a redeploy (entry 6.1). Recent versions can attach the network for you, but an explicit external network keeps the design readable. Leave out container_name: it blocks scaling and confuses log views.

---

## 3. Day-2 operations

Installing Dokploy takes ten minutes. Running it for two years is the real job: updates that don't break routing, backups you have restored, alerts from outside the box, and a host that stays patched and closed.

### A weekly health routine

```bash
docker service ls --format 'table {{.Name}}\t{{.Replicas}}'        # every line n/n
docker ps -a --filter status=exited --format '{{.Names}} {{.Status}}' | head
docker logs --since 168h dokploy-traefik 2>&1 | grep -ciE 'error|unable'   # watch the trend
df -h /var/lib/docker ; docker system df                           # below 80 %, reclaimable known
for d in shop.example.com api.example.com; do
  echo | openssl s_client -connect "$d:443" -servername "$d" 2>/dev/null \
    | openssl x509 -noout -enddate | sed "s/^/$d /"
done
```

Ten minutes a week catches most incidents in this module before users do: a task stuck at 0/1, a Traefik error trend, a disk at 85 %, a certificate that stopped renewing.

### Updating Dokploy safely

Updates are the riskiest routine task (entries 6.5, 6.6 and 13.1 are all upgrade stories). Make every update a small change with a rollback.

```bash
# 0. Record what runs now
docker service inspect dokploy --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
docker inspect dokploy-traefik --format '{{.Config.Image}}'
docker version --format 'engine {{.Server.Version}} api {{.Server.APIVersion}}'
# 1. Panel backup (Web Server > Backups) and a VM snapshot
# 2. Update from the UI (Web Server > Updates) or with the install script's update mode
#    (pulls the latest stable release tag and runs docker service update --image on dokploy)
curl -sSL https://dokploy.com/install.sh | sh -s update
# 3. Watch it come back
docker service ps dokploy --no-trunc | head -3
docker service logs dokploy --since 5m | tail -30
# 4. Roll back by pinning a known-good tag from the releases page
docker service update --image dokploy/dokploy:RELEASE_TAG dokploy
# 5. Keep apt from moving Docker under you
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

Before you press the button, read the release notes and the open issues labelled as regressions (#5453 is the kind of thing you are looking for). After it, push one canary app through the full CI path and check it from outside. A rollback by image tag doesn't undo database migrations the newer version already ran on dokploy-postgres, so if the old version won't start on the migrated schema, restore the step 1 panel backup or the VM snapshot. Remember that the Traefik container is versioned separately from the panel: with Docker Engine 29 it must be v3.6.1 or newer.

### Backups you have restored

| Layer | What it holds | How | Restore drill |
|---|---|---|---|
| Panel | dokploy-postgres and /etc/dokploy as one zip | Web Server → Backups to an S3 destination, on a cron schedule | quarterly onto a scratch VM (entry 10.4) |
| Databases | a dump of each database | the database's Backups tab: destination, cron, keep the latest N | monthly into a scratch database (entry 10.3) |
| Volumes and files | named volumes and ../files | volume backups in recent versions, or restic from the host | restore one file every month |
| Images | every released tag | Harbor retention and replication | pull last month's tag |

S3 destinations fail for boring reasons: MinIO's API port is 9000, not the console's 9001; the region must match (us-east-1 when unsure); the bucket must exist; the host clock must be right; and a private CA on the endpoint must be trusted. Give the backup key access to one bucket only, and copy that bucket off-site.

A host-level safety net for file mounts (databases are covered by dumps, not file copies):

```bash
export AWS_ACCESS_KEY_ID=BACKUP_KEY_ID AWS_SECRET_ACCESS_KEY=BACKUP_SECRET
export RESTIC_REPOSITORY=s3:https://minio.example.com:9000/dokploy-files
export RESTIC_PASSWORD_FILE=/root/.restic-pass
sudo -E restic backup /etc/dokploy/compose/*/files
sudo -E restic snapshots --latest 3
```

### Monitoring, logs and notifications

The panel shows per-service CPU and memory, deployment logs and runtime logs, and recent versions add server metrics with alert thresholds. Notifications go to Slack, Discord, Telegram, email and self-hosted push services such as Gotify or ntfy, depending on version, for deploy results, backup results, cleanups and threshold alerts. Turn on at least deploy failures and backup failures.

That isn't enough on its own, because a panel can't page you when its own host is down. Add, from outside the box:

- a probe per domain (blackbox exporter or Uptime Kuma) for HTTP status and certificate expiry;
- node_exporter for disk, memory and OOM kills on every host;
- Traefik's access log in JSON, shipped to Loki or Wazuh.

```yaml
# /etc/dokploy/traefik/traefik.yml - merge with the existing keys, then: docker restart dokploy-traefik
accessLog:
  format: json
```

Without a filePath, Traefik writes the access log to stdout, so `docker logs dokploy-traefik` and any Docker log shipper pick it up. Restarting Traefik drops connections for a second or two, so pick a quiet minute. Metrics and dashboards for the whole stack: [Performance & observability](32-learn-performance-observability.md).

### Cleanup and capacity

- Enable the daily Docker cleanup for each server in the panel, or run `docker builder prune` and `docker image prune` with an `until` filter from a timer (entry 11.1).
- Rotate container logs in daemon.json and keep it under configuration management. One file holds settings from several entries in this module:

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "default-address-pools": [ { "base": "10.200.0.0/16", "size": 24 } ],
  "dns": ["192.0.2.53", "192.0.2.54"]
}
```

Restarting Docker to apply it restarts every container, so schedule it. Builds are the biggest capacity risk: build in CI and deploy images (entry 8.5).

### Hardening checklist

- Reach the panel only through its HTTPS domain, ideally only over VPN or from an allowlist at the firewall; unpublish 3000.
- Two-factor authentication on, one account per person, one API token per pipeline, revoked when people leave.
- The panel mounts docker.sock: whoever controls the panel controls the host.
- No database external ports; admins use SSH plus a throwaway client container (entry 13.2).
- Published ports bypass UFW: scan from outside after every change.
- Keep Dokploy, Traefik and Docker patched, and read security advisories before updates.
- A Wazuh agent on every host watching auth logs, Docker events and Traefik access logs ([Wazuh & security tools](48-wazuh-and-security-tools.md)).

### Remote servers and clusters

| Aspect | Remote server | Cluster node |
|---|---|---|
| What it is | a separate Docker host the panel manages over SSH | a Swarm worker (or manager) joined to the panel's swarm |
| Traefik | its own Traefik; DNS for its apps points at it | shares the manager's Traefik through the overlay |
| Builds | on that server (or in CI) | on the manager; images must be pushed to a registry |
| Logs in the UI | yes, over SSH | not for apps placed on workers (entry 12.3) |
| Needs | SSH key access; setup installs Docker and tools | 2377/tcp, 7946/tcp+udp, 4789/udp between nodes, plus a registry |
| Use it for | separate environments: staging, a client, a site | more capacity and replicas for the same apps |

### Deploying from GitLab CI

The pattern that matches your target setup: CI builds and pushes to Harbor, then the last job asks Dokploy to deploy. The build and push side is in [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md); the deploy job is small.

```yaml
deploy:
  stage: deploy
  image: curlimages/curl:8.10.1
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - >
      curl --fail-with-body -sS -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN"
      -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$DOKPLOY_APP_ID\"}"
    - sleep 30
    - curl --fail -sS -o /dev/null -w '%{http_code}\n' https://shop.example.com/healthz
```

DOKPLOY_TOKEN comes from your Dokploy profile and is stored as a masked, protected variable; DOKPLOY_APP_ID comes from `GET /api/project.all` with the same header. The deploy uses the image tag configured on the application. Two workable patterns: configure a moving tag (for example :main) that CI re-points after each push, and roll back by re-pointing it; or update the application's image to the commit SHA through the API before deploying (endpoint names vary by version, so check your instance's API reference). Compose services have their own deploy endpoint keyed by composeId. Either way, add Harbor as a registry in Dokploy so Swarm pins the image digest (entry 9.4). The webhook alternative, a GitLab push hook pointing at the service's webhook URL, is entry 9.1.

### Templates

One-click templates are Compose services from Dokploy's template catalogue. Treat each one as code you now own: pin the image tags after the first deploy, read its volumes and ports, set domains (then redeploy, entry 6.1), and add it to backups like any other service.

---

## 4. Learning path

KodeKloud has no Dokploy course and no Traefik-on-Docker course, so the path combines the closest courses, this handbook, the official docs and your own lab.

| Stage | Learn | Practise | Exit check |
|---|---|---|---|
| Fresher (L0) | KodeKloud [*DevOps Pre-Requisite Course*](https://kodekloud.com/courses/devops-pre-requisite-course) (Networking Basics, DNS, SSL & TLS Basics); [*Docker Training Course for the Absolute Beginner*](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner) | install Dokploy on a lab VM, deploy a whoami image with a domain | explain what listens on 80, 443 and 3000, and why |
| Junior (L1) | the Docker beginner course's Docker Compose, Docker Networking and Docker Registry lessons; [Docker](30-learn-docker.md) (Compose, Storage) | deploy an app with Postgres and a scheduled backup; break env, port and volume on purpose | fix entries 6.1, 6.2, 8.2 and 10.1 in under 15 minutes each |
| Mid-level (L2) | [*Docker Certified Associate*](https://kodekloud.com/courses/docker-certified-associate-exam-course) (Docker Swarm); [*Kubernetes Networking Deep Dive*](https://kodekloud.com/courses/kubernetes-networking) (Traefik Overview); [Web servers & proxies](29-learn-webservers-proxies.md), [Traefik deep dive](43-traefik-and-reverse-proxies.md), [Site down](25-playbook-site-down.md) | read every file Dokploy writes under /etc/dokploy/traefik; reproduce 6.3, 7.1 and 8.4 | explain any outage from docker and Traefik evidence only |
| Senior (L3) | [*GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*](https://kodekloud.com/courses/gitlab-ci-cd) (Continuous Integration with GitLab, Self-Managed Runners); [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), [Security](37-learn-security-devsecops.md); Harbor docs | GitLab CI → Harbor with your CA → Dokploy API; a two-node cluster; a rollback | the ops-ladder L3 exit test: build, push, deploy, roll back, all written down |
| Senior/Lead (L4) | [*Fundamentals of SRE*](https://kodekloud.com/courses/fundamentals-of-sre) (Incident Management, Change Management for Reliability); [*Prep Course - Prometheus Certified Associate (PCA)*](https://kodekloud.com/courses/prometheus-certified-associate-pca); [Career ladder](40-career-ladder.md) | quarterly DR drill (10.4), upgrade rehearsal (13.1), outside probes and alerts | a written upgrade policy and a DR runbook with a measured restore time |

Free practice: the KodeKloud [Docker playground](https://kodekloud.com/playgrounds/playground-docker) and [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) are enough for single-node exercises; the multi-node entries need two VMs of your own. Keep the [Dokploy docs](https://docs.dokploy.com/docs/core) open while you work, and read the release notes of every version you install: that habit alone prevents most of section 13.

---

The problem library starts here. Sections 5 to 13 run from first-day problems to platform-level ones; each entry stands on its own.

## 5. Install and first access

### 5.1 Panel on port 3000 doesn't open

> **Seen as:** `ERR_CONNECTION_TIMED_OUT`, `ERR_CONNECTION_REFUSED` or `ERR_SSL_PROTOCOL_ERROR` on SERVER_IP:3000 · **Where:** right after the install, server in a cloud VPC or behind an office firewall · **Level:** [L0 · Fresher] · **How common:** CapRover's troubleshooting page opens with it; Dokploy and Coolify both document a "UI not accessible" case

**Why it happens:** the panel speaks plain HTTP on 3000 until it has a domain, so typing https:// gives an SSL error. A timeout means something on the path drops the packets: a security group, an office firewall, NAT. Refused means the packets arrive but nothing listens, because dokploy is still starting, crashed, or waits for dokploy-postgres. UFW is rarely the culprit, since Docker-published ports skip UFW's rules.

**Diagnose:**

```bash
# On the server: does the panel answer locally?
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000
docker service ps dokploy --format '{{.CurrentState}} {{.Error}}' | head -3
sudo ss -ltnp 'sport = :3000'
# From your laptop: open, refused or timed out?
nc -vz -w 5 192.0.2.10 3000
```

```text
200
Running 4 minutes ago
LISTEN 0 4096 0.0.0.0:3000 0.0.0.0:* users:(("docker-proxy",pid=2231,fd=4))
nc: connect to 192.0.2.10 port 3000 (tcp) timed out: Operation now in progress
```

**What the output tells you:** the panel is healthy on the server (200, task Running, port listening), but packets from your laptop never arrive. That is the network path, not Dokploy. A refusal from outside while localhost works means you are hitting a different address (NAT or the wrong IP). If localhost fails too, read `docker service logs dokploy` and go to entry 11.2.

**Fix:**

```bash
# Best: don't expose 3000 at all - tunnel to it
ssh -N -L 3000:localhost:3000 ops@192.0.2.10          # then browse http://localhost:3000
# Must open it briefly? Only your admin IP, at the cloud or office firewall
# Panel not running? Read why, then restart it cleanly
docker service logs dokploy --since 10m | tail -40
docker service scale dokploy=0 && docker service scale dokploy=1
```

**Why this fix works:** the tunnel delivers the traffic to localhost on the server, so no firewall in between matters and nothing new is exposed. Scaling to 0 and back reruns start-up once Postgres is ready. Don't solve it by opening 3000 to the internet: the panel controls docker.sock.

**Prevent it:** use SSH tunnels as your default way into admin panels, give the panel an HTTPS domain on day one and unpublish 3000 (entry 13.2), and record which firewall layers sit in front of each server.

**Next step:** [Who owns this port?](22-playbook-ports-inventory.md) · [Site down](25-playbook-site-down.md) · KodeKloud: *DevOps Pre-Requisite Course* — IPs and Ports · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance)

**Community threads:** [Dokploy docs: Dokploy Instance](https://docs.dokploy.com/docs/core/troubleshooting/instance) · [CapRover: Troubleshooting](https://caprover.com/docs/troubleshooting.html) · [Coolify: Troubleshooting](https://coolify.io/docs/troubleshoot/overview) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+cannot+access+port+3000&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=docker+published+port+not+accessible+from+outside)

### 5.2 Installer stops: port 80, 443 or 3000 in use

> **Seen as:** `Error: something is already running on port 443` (or 80, or 3000) · **Where:** install.sh on a host that already runs Apache, Nginx, Grafana or another proxy · **Level:** [L1 · Junior] · **How common:** a hard-coded check in the official installer; your own production incident

**Why it happens:** the installer stops if anything listens on 80, 443 or 3000, because dokploy-traefik must own 80/443 and the panel needs 3000. Apache and Nginx packages bind 0.0.0.0:80/443, Grafana defaults to 3000, old proxy containers publish 80/443, and a systemd socket unit can keep a port after its service stops.

**Diagnose:**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'
systemctl list-sockets | grep -E ':(80|443|3000)\b'
docker ps --format '{{.Names}} {{.Ports}}' | grep -E ':(80|443|3000)->'
sudo apachectl -S 2>/dev/null | head -8           # vhosts that must keep working
```

```text
LISTEN 0 511       0.0.0.0:443   0.0.0.0:* users:(("apache2",pid=1123,fd=6))
LISTEN 0 511       0.0.0.0:80    0.0.0.0:* users:(("apache2",pid=1123,fd=4))
LISTEN 0 4096            *:3000        *:* users:(("grafana",pid=978,fd=12))
VirtualHost configuration:
*:443                  legacy.example.com (/etc/apache2/sites-enabled/legacy-ssl.conf:2)
*:80                   legacy.example.com (/etc/apache2/sites-enabled/legacy.conf:1)
```

**What the output tells you:** Apache holds 80/443 with live vhosts, and Grafana holds 3000. Decide per owner: retire it, move it, or move it and route it through Traefik later.

**Fix:**

```bash
# Staged (what you did): Apache to 81/444, sites stay up on the new ports
sudo sed -i 's/^Listen 80$/Listen 81/; s/^\(\s*\)Listen 443$/\1Listen 444/' /etc/apache2/ports.conf
sudo sed -i --follow-symlinks 's/:80>/:81>/; s/:443>/:444>/' /etc/apache2/sites-enabled/*.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
# Grafana off 3000
sudo sed -i 's/^;\?http_port = .*/http_port = 3001/' /etc/grafana/grafana.ini
sudo systemctl restart grafana-server
# Check again, then rerun the installer
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'
```

**Why this fix works:** freeing exactly those ports satisfies the installer and lets Traefik bind them, while the legacy sites keep answering on 81/444 until entry 6.7 routes them through Traefik. `--follow-symlinks` matters: without it, `sed -i` replaces the symlinks in sites-enabled with copies and the real files in sites-available stay unchanged. Don't just kill the PIDs: the unit comes back at the next reboot.

**Prevent it:** a port inventory per server, checked before installing anything that wants 80/443, and a change record with a rollback step (restore ports.conf, reload Apache).

**Next step:** [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) · [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *DevOps Pre-Requisite Course* — Apache Web Server, IPs and Ports · [Dokploy install script](https://dokploy.com/install.sh)

**Community threads:** [Dokploy install.sh (port checks)](https://dokploy.com/install.sh) · Search: [Server Fault](https://serverfault.com/search?q=apache+port+443+already+in+use+docker+traefik) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+port+80+already+in+use&restrict_sr=1)

### 5.3 Swarm init fails: advertise address

> **Seen as:** `must specify a listening address because the address to advertise is not recognized as a system address` or `ERROR: We couldn't detect your server IP address.` · **Where:** on-prem servers with several NICs, NAT in front, or no outbound internet · **Level:** [L1 · Junior] · **How common:** first item on Dokploy's Networking & DNS troubleshooting page; a wrong advertised address caused the 502s in Dokploy #3375 (23 comments)

**Why it happens:** without ADVERTISE_ADDR, the current installer takes the first private (RFC 1918) IPv4 address on a non-Docker interface, and only when there is none asks public "what is my IP" services (ifconfig.io, icanhazip.com). On-prem that goes wrong in three ways: with management and production VLANs, bonds or bridges, the first private address may be one other nodes can't reach; a host whose addresses aren't in RFC 1918 ranges gets the public NAT address, which sits on no local interface, so `docker swarm init` refuses it; and an air-gapped host gets no answer at all, so the script stops with the "couldn't detect" error. Exporting ADVERTISE_ADDR before sudo loses it, because sudo resets the environment.

**Diagnose:**

```bash
ip -o -4 addr show scope global
ip route get 192.0.2.1                    # which source address the kernel would use
curl -s --max-time 5 ifconfig.io || echo "no outbound HTTP"
docker info --format '{{.Swarm.LocalNodeState}} {{.Swarm.NodeAddr}}'
```

```text
2: ens18    inet 192.0.2.10/24 brd 192.0.2.255 scope global ens18\       valid_lft forever preferred_lft forever
3: ens19    inet 198.51.100.10/24 brd 198.51.100.255 scope global ens19\       valid_lft forever preferred_lft forever
192.0.2.1 dev ens18 src 192.0.2.10 uid 1000
    cache
203.0.113.77
inactive
```

**What the output tells you:** two global addresses, and the public address 203.0.113.77 sits on no interface. An installer that falls back to it can't initialise the swarm, and one that picks the first private address may pick the wrong VLAN; here the swarm never initialised. Choose the address that other nodes and Traefik backends will use, here 192.0.2.10, and pass it explicitly.

**Fix:**

```bash
# Lab or fresh host only: clean up a half-initialised swarm
docker swarm leave --force 2>/dev/null || true
# Pass the address explicitly, after sudo
sudo ADVERTISE_ADDR=192.0.2.10 sh dokploy-install.sh
docker info --format '{{.Swarm.LocalNodeState}} {{.Swarm.NodeAddr}}'      # expect: active 192.0.2.10
```

**Why this fix works:** Swarm stores the advertise address in its cluster state and hands it to every node; giving it explicitly removes the guessing. `docker swarm leave --force` is fine on a fresh host but destroys the swarm state on a running one. For a live single-node cluster with a wrong address, #3375 used `docker swarm init --force-new-cluster --advertise-addr 192.0.2.10`, after a backup.

**Prevent it:** static addresses in netplan, a documented cluster address per server, and ADVERTISE_ADDR written into your install runbook or Ansible role.

**Next step:** [Docker: Swarm for Dokploy](30-learn-docker.md) · [Networking](28-learn-networking.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Swarm Setup 2 node Cluster) · [Dokploy networking troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/networking)

**Community threads:** [Dokploy docs: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking) · [Dokploy #3375](https://github.com/Dokploy/dokploy/issues/3375) · Search: [Server Fault](https://serverfault.com/search?q=%22must+specify+a+listening+address%22+docker+swarm+init) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+init+advertise-addr+multiple+addresses&restrict_sr=1)

### 5.4 Proxmox LXC: names resolve, connections hang

> **Seen as:** `Migration failed [Error: getaddrinfo ENOTFOUND dokploy-postgres]` or `connect ECONNREFUSED 10.0.1.2:5432` · **Where:** Dokploy inside a Proxmox LXC container or on a stripped kernel · **Level:** [L2 · Mid-level] · **How common:** Dokploy #2583 "Proxmox LXC Installation Issues" (23 comments) and #2331 (19 comments); the installer has a dedicated ENDPOINT_MODE=dnsrr switch

**Why it happens:** a Swarm service name resolves to a virtual IP (VIP), and the kernel's IPVS load-balances that VIP to the tasks. Many LXC containers have no ip_vs module, so the name resolves to an address nobody answers. DNS round-robin (dnsrr) mode returns the task IPs directly and needs no IPVS. Unprivileged containers without nesting and keyctl add more breakage.

**Diagnose:**

```bash
lsmod | grep ip_vs || echo "ip_vs not loaded"
docker service inspect --format '{{.Spec.Name}} {{.Spec.EndpointSpec.Mode}}' dokploy dokploy-postgres
docker exec $(docker ps -q -f name=dokploy.1) getent hosts dokploy-postgres tasks.dokploy-postgres
# On the Proxmox host
pct config 120 | grep -E 'features|unprivileged'
```

```text
ip_vs not loaded
dokploy vip
dokploy-postgres vip
10.0.1.2        dokploy-postgres
10.0.1.3        tasks.dokploy-postgres
features: nesting=1
unprivileged: 1
```

**What the output tells you:** VIP mode without ip_vs. The VIP 10.0.1.2 is a dead end while the task address 10.0.1.3 works: the LXC signature.

**Fix:**

```bash
# Fresh install inside LXC (current installers also switch to dnsrr when they detect Proxmox LXC)
sudo ENDPOINT_MODE=dnsrr sh dokploy-install.sh
# Existing install: switch every service that others call
docker service update --endpoint-mode dnsrr dokploy-postgres
docker service update --endpoint-mode dnsrr dokploy
# Older installs that still run dokploy-redis:
#   docker service update --endpoint-mode dnsrr dokploy-redis
# Proxmox host: allow nesting and keyctl (better: run Docker in a VM)
pct set 120 --features nesting=1,keyctl=1
```

**Why this fix works:** in dnsrr mode the name resolves straight to the task IPs, so IPVS isn't needed. dnsrr can't be combined with ingress-mode published ports; the panel's 3000 is published in host mode, so it is fine. The robust fix is a full VM: an LXC container shares the host's kernel, so modules and sysctls are the host's decision, not yours.

**Prevent it:** run Docker hosts as VMs, and test for ip_vs in your base template.

**Next step:** [Docker: overlay networks and the routing mesh](30-learn-docker.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Docker Overlay Network, Swarm Service Discovery) · [Dokploy networking troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/networking)

**Community threads:** [Dokploy #2583](https://github.com/Dokploy/dokploy/issues/2583) · [Dokploy #2331](https://github.com/Dokploy/dokploy/issues/2331) · [Dokploy docs: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=docker+swarm+lxc+overlay+ipvs&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+lxc+ipvs+dnsrr)

### 5.5 Login fails: invalid origin or other devices

> **Seen as:** `Invalid origin`, or "Invalid email or password" with the right credentials on a second device · **Where:** a panel reached by IP:3000 and by domain, over HTTP and HTTPS, or through an extra proxy or tunnel · **Level:** [L1 · Junior] · **How common:** Dokploy #1924 (35 comments, v0.22.6 over http://LAN-IP:3000), #1455 "invalid origin on login" (25 comments), #151 "400 Oops, something went wrong" (24 comments)

**Why it happens:** web logins check that the request's Origin matches the site they trust, and keep the session in cookies that can be marked Secure (HTTPS only) and tied to one host name. http://IP:3000, https://dokploy.example.com and a tunnel URL are three different origins with three cookie jars. A proxy in front that rewrites Host or drops X-Forwarded-Proto makes the panel see the wrong origin, and a host clock that is far off expires sessions at once. Some versions also had auth bugs, which the threads track.

**Diagnose:**

```bash
curl -sI https://dokploy.example.com | grep -iE '^(HTTP|location)'
timedatectl | grep -E 'System clock synchronized|Local time'
docker service logs dokploy --since 5m 2>&1 | grep -iE 'origin|auth' | tail -5
```

```text
HTTP/2 200
               Local time: Sat 2026-10-03 09:12:44 UTC
System clock synchronized: no
```

In the browser, open devtools, then Network, then the sign-in request: compare its Origin header with the address bar and look at the Set-Cookie flags.

**What the output tells you:** the domain itself works, so the problem is which origin you log in from, plus a clock that isn't synchronised. A Location header pointing at http:// or at an IP would mean a proxy or a setting sends users to a second origin.

**Fix:**

```bash
# One origin only: always https://dokploy.example.com (set as the panel domain, entry "Give the panel a domain")
sudo timedatectl set-ntp true
timedatectl | grep synchronized
# In the browser: clear site data for the old IP:3000 origin, then log in via the domain
```

If a tunnel or another proxy sits in front, it must pass Host and X-Forwarded-Proto through unchanged.

**Why this fix works:** one origin means one cookie jar and a matching Origin header on every device, and a correct clock keeps session expiry sane. Don't run the panel over plain HTTP across the internet to "fix" cookies: the login would travel in clear text.

**Prevent it:** document a single admin URL, reach it over VPN or a tunnel, and monitor NTP ([Time & NTP](12-time-ntp.md)).

**Next step:** [Web, HTTP & TLS](18-web-http-tls.md) · KodeKloud: *DevOps Pre-Requisite Course* — SSL & TLS Basics · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance)

**Community threads:** [Dokploy #1455](https://github.com/Dokploy/dokploy/issues/1455) · [Dokploy #1924](https://github.com/Dokploy/dokploy/issues/1924) · [Dokploy #151](https://github.com/Dokploy/dokploy/issues/151) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+invalid+origin+login&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=%22invalid+origin%22+login+reverse+proxy+cookie)

## 6. Domains, routing and Traefik

### 6.1 Compose or template domain gives 404

> **Seen as:** `404 page not found` in plain text, from Traefik · **Where:** Compose services and one-click templates after adding or editing a domain · **Level:** [L1 · Junior] · **How common:** its own section in Dokploy's Domains & Traefik troubleshooting page; two dozen Dokploy issues and PRs quote the exact string

**Why it happens:** application routes are generated files that Traefik reloads instantly. Compose routes are Traefik labels that Dokploy injects only when it deploys, so a new or edited domain does nothing until the next deploy. Other causes: the wrong service name or port in the domain form, asking for http when the router only listens on https, hand-written labels without traefik.enable=true, a service that isn't on dokploy-network, or two stacks using the same router name.

**Diagnose:**

```bash
# Ask Traefik directly, bypassing DNS: 404 here means no router matched
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: app.example.com' http://192.0.2.10/
curl -sk -o /dev/null -w '%{http_code}\n' --resolve app.example.com:443:192.0.2.10 https://app.example.com/
docker inspect CONTAINER --format '{{json .Config.Labels}}' | jq -c 'with_entries(select(.key|startswith("traefik")))'
```

```text
404
404
{}
```

**What the output tells you:** Traefik has no router for the name on either entrypoint, and the running container carries no traefik labels at all: the domain was saved but never deployed. If labels exist, compare their Host rule, entrypoints and port with what you requested.

**Fix:** in Dokploy, open the Compose service, then Domains: service name, container port and host, then **Deploy**. For hand-written labels, the minimum is:

```yaml
services:
  web:
    image: harbor.example.com/shop/web:1.4.2
    networks: [dokploy-network]
    labels:
      - traefik.enable=true
      - traefik.http.routers.shop-web.rule=Host(`shop.example.com`)
      - traefik.http.routers.shop-web.entrypoints=websecure
      - traefik.http.routers.shop-web.tls.certresolver=letsencrypt
      - traefik.http.services.shop-web.loadbalancer.server.port=3000
networks:
  dokploy-network:
    external: true
```

**Why this fix works:** the deploy writes the labels into the container spec, and Traefik's Docker provider turns them into a router within seconds. Unique router names stop two stacks from overwriting each other. Don't publish ports to "test around" Traefik: you would bypass TLS and the firewall.

**Prevent it:** treat every domain change as a deploy, and add a post-deploy curl in CI that fails on 404.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Site down](25-playbook-site-down.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview · [Dokploy Domains & Traefik troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains)

**Community threads:** [Dokploy docs: Domains & Traefik](https://docs.dokploy.com/docs/core/troubleshooting/domains) · [Dokploy docs: Docker Compose domains](https://docs.dokploy.com/docs/core/docker-compose/domains) · [GitHub: Dokploy issues with this message](https://github.com/Dokploy/dokploy/issues?q=%22404+page+not+found%22) · Search: [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=%22404+page+not+found%22+docker+labels&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=traefik+%22404+page+not+found%22+docker+compose+labels)

### 6.2 502 or 503 right after a successful deploy

> **Seen as:** `Bad Gateway`, or `no available server` (503) · **Where:** first deploy of an app, or after changing its port (Dokploy, Coolify, CapRover) · **Level:** [L1 · Junior] · **How common:** about 54 Dokploy issues and PRs mention Bad Gateway; CapRover calls the wrong container port the most common cause; Coolify documents both errors

**Why it happens:** a router matched, but the backend wasn't usable. 502 means Traefik reached the container's IP and nothing accepted the connection: the domain's port differs from the app's listen port (CapRover's Container HTTP Port defaults to 80), or the app listens on 127.0.0.1 inside the container, as Vite, Astro and many dev servers do. 503 "no available server" means Traefik knows the route but has no healthy server: the container is crash-looping, or its health check fails. Coolify runs health checks inside the container, so an image without curl or wget always fails them.

**Diagnose:**

```bash
docker service ps APP --format '{{.CurrentState}} {{.Error}}' | head -3
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn      # what the app really listens on (no process names: separate PID namespace)
docker inspect CONTAINER --format '{{json .State.Health}}' | jq -c '{Status, Last: .Log[-1].Output}'
docker logs --tail 100 dokploy-traefik 2>&1 | grep -iE 'bad gateway|dial tcp|no available'   # needs DEBUG log level
```

```text
Running 2 minutes ago
LISTEN 0      511        127.0.0.1:4321       0.0.0.0:*
{"Status":null,"Last":null}
2026-10-03T09:30:12Z DBG > 502 Bad Gateway error="dial tcp 10.0.1.7:3000: connect: connection refused"
```

**What the output tells you:** the app listens on 127.0.0.1:4321 while Traefik dials port 3000 on the container's network address: wrong port and loopback binding at once. There is no health check (null), so a 503 wouldn't come from health here.

**Fix:**

```bash
# Make the app listen on all interfaces, on the port you route to:
#   Node:            app.listen(3000, '0.0.0.0')
#   Vite/Astro:      preview --host 0.0.0.0 --port 3000   (or server.host: true)
#   Gunicorn:        gunicorn --bind 0.0.0.0:8000 app:app
# Then set the domain's container port to that port and redeploy.
# 503 with a health check: does the probe tool exist in the image?
docker exec CONTAINER sh -c 'command -v curl || command -v wget || echo "no probe tool"'
```

**Why this fix works:** Traefik connects from outside the container over dokploy-network, so the app must bind an address on that network and the port must match the router's service. A health check that can actually run lets the proxy mark the container healthy. Adding `ports:` so it works from the host proves nothing about the routed path.

**Prevent it:** EXPOSE the real port in every Dockerfile, one port convention per framework, and a /healthz endpoint with a health check that uses a tool present in the image.

**Next step:** [Docker: networking](30-learn-docker.md) · [Site down: proxy errors](25-playbook-site-down.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Dokploy Domains & Traefik troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains)

**Community threads:** [Dokploy docs: Domains & Traefik](https://docs.dokploy.com/docs/core/troubleshooting/domains) · [CapRover: Troubleshooting](https://caprover.com/docs/troubleshooting.html) · [Coolify: Troubleshooting](https://coolify.io/docs/troubleshoot/overview) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+502+bad+gateway+docker+0.0.0.0) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=coolify+%22no+available+server%22&restrict_sr=1)

### 6.3 Intermittent 504 on Compose apps

> **Seen as:** `Gateway Timeout` that comes and goes; Traefik logs `dial tcp 172.18.0.5:3000: i/o timeout` · **Where:** Compose services attached to their project network and to dokploy-network · **Level:** [L2 · Mid-level] · **How common:** Dokploy #821 "Frequent 504s and Poor Uptime on Docker Compose" (28 comments, several confirmations of the fix); Coolify's Gateway Timeout page lists network isolation first

**Why it happens:** a container on two networks has two IPs. Traefik's Docker provider picks one, and if it picks the project network address (a network Traefik isn't attached to), those requests hang until the timeout. The app's logs show nothing, because the requests never arrive.

**Diagnose:**

```bash
docker inspect CONTAINER --format '{{json .NetworkSettings.Networks}}' | jq -c 'map_values(.IPAddress)'
docker network inspect dokploy-network --format '{{range .Containers}}{{.Name}} {{end}}'
docker logs --tail 200 dokploy-traefik 2>&1 | grep -iE 'timeout|dial tcp' | tail -3
```

```text
{"shop_default":"172.18.0.5","dokploy-network":"10.0.1.31"}
dokploy.1.p8x2kq7v0m4n6b1c3z5l7j9h2 dokploy-traefik shop-web-1 dokploy-postgres.1.k3l0aa91c2w4e6r8t1y3u5i7o shop-db-1 dokploy-network-endpoint
... dial tcp 172.18.0.5:3000: i/o timeout
```

**What the output tells you:** Traefik dialled 172.18.0.5 on shop_default, a network it can't reach. The dokploy-network address 10.0.1.31 would have worked.

**Fix:** tell Traefik which network to use, once for all containers (the fix confirmed in #821) or per service. Current Dokploy versions write `network: dokploy-network` into the docker provider of a fresh traefik.yml, but the file is only created when it doesn't exist, so older installs keep whatever they had: check yours with `grep -n -A4 'docker:' /etc/dokploy/traefik/traefik.yml`.

```yaml
# /etc/dokploy/traefik/traefik.yml - keep your other keys, then: docker restart dokploy-traefik
providers:
  docker:
    exposedByDefault: false
    watch: true
    network: dokploy-network
# or per service, in the compose file:
#   labels:
#     - traefik.docker.network=dokploy-network
# Stack mode (Swarm provider) uses the label traefik.swarm.network=dokploy-network
```

**Why this fix works:** the network setting tells Traefik which of the container's addresses to use, so every request takes a reachable path. The swarm provider has the same option (`providers.swarm.network`, label `traefik.swarm.network`) if you route Swarm services by labels. Restarting Traefik is required for static config and drops connections for a second.

**Prevent it:** one proxy-facing network per stack, the traefik.docker.network label on every routed service, and no networks a service doesn't need.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Docker & K8s incidents](26-playbook-containers-k8s.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Dokploy #821](https://github.com/Dokploy/dokploy/issues/821) · [Coolify: Gateway Timeout](https://coolify.io/docs/troubleshoot/applications/gateway-timeout) · Search: [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=traefik.docker.network+gateway+timeout&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=traefik+multiple+networks+gateway+timeout)

### 6.4 Traefik down after a config change

> **Seen as:** `read /etc/traefik/traefik.yml: is a directory`, or `field not found, node: passHostHeader` · **Where:** after manual edits in the panel's Traefik editor, a restore, or cleaning /etc/dokploy · **Level:** [L2 · Mid-level] · **How common:** Dokploy #2018 (18 comments) and #2098 (17 comments, the same trap with config.json); the passHostHeader error is on Dokploy's instance troubleshooting page

**Why it happens:** two different breakages take every site down at once. First, when a bind-mount source file is missing, `docker run -v` creates an empty directory in its place, and Traefik then tries to read a directory as its config. Second, a YAML mistake (passHostHeader next to the server URLs instead of inside loadBalancer, tabs, or v2 syntax in v3) makes Traefik reject the file, so all its routers vanish. The line `accept tcp [::]:443: use of closed network connection` during a restart is normal noise.

**Diagnose:**

```bash
docker logs --tail 30 dokploy-traefik 2>&1 | grep -iE 'error|field not found|is a directory'
ls -ld /etc/dokploy/traefik/traefik.yml            # a leading 'd' is the bind-mount trap
python3 -c 'import sys,yaml; yaml.safe_load(open(sys.argv[1]))' /etc/dokploy/traefik/dynamic/legacy-apache.yml && echo "YAML ok"
```

```text
... ERR error="read /etc/traefik/traefik.yml: is a directory"
drwxr-xr-x 2 root root 4096 Oct  3 08:51 /etc/dokploy/traefik/traefik.yml
YAML ok
```

**What the output tells you:** traefik.yml on the host is a directory: the first mechanism. "field not found" with valid YAML would point to the second: a key in the wrong place.

**Fix:**

```bash
# Directory instead of file: let Dokploy rewrite it, then recreate Traefik
docker service scale dokploy=0
docker stop dokploy-traefik
sudo rm -rf /etc/dokploy/traefik/traefik.yml      # only the wrongly created directory
docker service scale dokploy=1                    # Dokploy writes the file again
# then recreate dokploy-traefik with the command on Dokploy's "Dokploy Instance" troubleshooting page
# Bad key: restore the last good file from git or backup, then
docker restart dokploy-traefik
```

The right place for passHostHeader is inside loadBalancer:

```yaml
http:
  services:
    legacy-apache:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: http://192.0.2.10:81
```

**Why this fix works:** removing the directory and letting Dokploy write the file restores the bind-mount source, and recreating the container binds it again. Traefik validates each dynamic file as a unit, so fixing one key brings back every router in that file. Don't remove anything else under /etc/dokploy: certificates and dynamic files live there.

**Prevent it:** keep /etc/dokploy/traefik in git, lint YAML before saving, change one file at a time while tailing the Traefik log. CapRover users need the same discipline with custom Nginx templates (CapRover documents a fixer script).

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Docker: storage](30-learn-docker.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [Traefik v2 to v3 migration](https://doc.traefik.io/traefik/migrate/v2-to-v3-details/)

**Community threads:** [Dokploy #2018](https://github.com/Dokploy/dokploy/issues/2018) · [Dokploy docs: Dokploy Instance](https://docs.dokploy.com/docs/core/troubleshooting/instance) · [CapRover: Troubleshooting](https://caprover.com/docs/troubleshooting.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+bind+mount+file+%22is+a+directory%22) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=%22field+not+found%22&restrict_sr=1)

### 6.5 Every domain 404 after Docker 29

> **Seen as:** `client version 1.24 is too old. Minimum supported API version is 1.44` in the Traefik log, and 404 on every label-routed domain · **Where:** hosts moved to Docker Engine 29 by a routine `apt upgrade` (or by unattended-upgrades where the Docker repository is in its allowed origins) with an older Traefik image; current Dokploy installers hold the docker-ce packages, older installs and hosts where Docker was already present usually don't · **Level:** [L2 · Mid-level] · **How common:** the Traefik forum's most-viewed thread of the year (about 32k views); Dokploy #4123 and #3053 (22 comments); Coolify #7549 and related issues

**Why it happens:** Docker 29 dropped old API versions. Traefik builds before v3.6.1 spoke API 1.24 by default, so the Docker provider failed, label-based routers disappeared, and the containers kept running behind a proxy that no longer knew them. Updating Dokploy doesn't necessarily replace the Traefik container: one 2026 report ran a current panel with Traefik v3.1.2.

**Diagnose:**

```bash
docker version --format 'engine {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'
docker inspect dokploy-traefik --format '{{.Config.Image}}'
docker logs dokploy-traefik 2>&1 | grep -m1 'too old'
zgrep -h 'docker-ce' $(ls -tr /var/log/apt/history.log*) | tail -1    # oldest file first, so tail is the newest
```

```text
engine 29.0.2 api 1.52 min 1.44
traefik:v3.1.2
... client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version
Upgrade: docker-ce:amd64 (5:28.5.0-1~ubuntu.24.04~noble, 5:29.0.2-1~ubuntu.24.04~noble)
```

**What the output tells you:** a new engine, an old Traefik, and apt did it: the textbook combination.

**Fix:**

```bash
# Preferred: Traefik v3.6.1 or newer. Update Dokploy, check the image, and if it is still old,
# recreate dokploy-traefik with the documented command and a current traefik:v3.6 tag.
# Stopgap: let the daemon accept old clients (merge, don't overwrite daemon.json)
sudo python3 -c 'import json,pathlib; p=pathlib.Path("/etc/docker/daemon.json"); c=json.loads(p.read_text()) if p.exists() else {}; c["min-api-version"]="1.24"; p.write_text(json.dumps(c, indent=2)+"\n")'
sudo systemctl restart docker                      # restarts containers: use a window
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

**Why this fix works:** Traefik 3.6.1 and later negotiate the API version; the daemon setting re-allows API 1.24 for old clients. Merging keeps your dns, pools and log settings, where `echo '{...}' > daemon.json` would wipe them. Holding the packages turns engine upgrades into planned changes.

**Prevent it:** hold Docker packages, upgrade a staging node first, and run outside probes right after every patch window.

**Next step:** [Docker: the daemon and daemon.json](30-learn-docker.md) · [Packages](11-packages.md) · KodeKloud: *Docker Certified Associate* — Docker Engine (Troubleshooting Docker Daemon) · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Docker forum: Docker 29 breaks Traefik](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384) · [Dokploy #4123](https://github.com/Dokploy/dokploy/issues/4123) · [Coolify #7549](https://github.com/coollabsio/coolify/issues/7549) · [Traefik community: top topics](https://community.traefik.io/top?period=yearly) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=traefik+%22client+version+1.24+is+too+old%22&restrict_sr=1)

### 6.6 Image app 404 after a webhook redeploy

> **Seen as:** every domain of a Docker-image app answers `404 page not found` right after a CI, webhook or API redeploy; the traefik.* labels appear only in the service's PreviousSpec · **Where:** Dokploy v0.29.12 to v0.30.6 on Swarm, exactly the GitLab CI → Harbor → API path · **Level:** [L3 · Senior] · **How common:** Dokploy #5453, open in October 2026 and reproduced on v0.30.6; commenters link it to earlier label and domain regeneration bugs (#4243, #5018, #4415)

**Why it happens:** in affected versions the deploy path rebuilds the service spec instead of merging it, so the traefik.* labels the router depends on are lost. The containers stay healthy; Traefik simply has no router any more. Another reporter saw the same with Compose services carrying custom labels after 0.29 → 0.30. Your configuration is fine: this is a regression.

**Diagnose:**

```bash
docker service inspect SERVICE --format '{{json .Spec.Labels}}' | jq -c 'keys'
docker service inspect SERVICE --format '{{json .PreviousSpec.Labels}}' | jq -c 'keys'
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.10/
docker service inspect dokploy --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
```

```text
[]
["traefik.enable","traefik.http.routers.shop-web.entrypoints","traefik.http.routers.shop-web.rule","traefik.http.services.shop-web.loadbalancer.server.port"]
404
dokploy/dokploy:v0.30.6
```

**What the output tells you:** the labels exist only in the previous spec, on an affected version: this bug, not your config.

**Fix:**

```bash
# Fastest: roll the service back (restores the labels AND the previous image)
docker service update --rollback SERVICE
# Or keep the new image: print the lost labels as shell-quoted flags, review them, re-add them
docker service inspect SERVICE --format '{{json .PreviousSpec.Labels}}' \
  | jq -r 'to_entries[] | select(.key|startswith("traefik")) | "--label-add \((.key + "=" + .value) | @sh)"'
# then: docker service update PRINTED_FLAGS SERVICE
```

Then pin Dokploy to the last good release until a fixed one ships, and follow #5453.

**Why this fix works:** a rollback re-applies the whole previous spec, labels included, but also the old image; re-adding the labels keeps the new image. Both are workarounds. One reporter ran a systemd timer that re-added the labels whenever traefik.enable vanished: acceptable for a week, not as a design.

**Prevent it:** after every Dokploy upgrade, push one canary app through the full CI path and assert HTTP 200 from outside; keep a probe per domain; read open regressions before upgrading.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · [Docker: services, tasks and rolling updates](30-learn-docker.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Scaling, Rolling Updates and Rollbacks) · [Dokploy release v0.30.0](https://github.com/Dokploy/dokploy/releases/tag/v0.30.0)

**Community threads:** [Dokploy #5453](https://github.com/Dokploy/dokploy/issues/5453) · [#5453 comments (GitHub API)](https://api.github.com/repos/Dokploy/dokploy/issues/5453/comments?per_page=100) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+404+after+redeploy&restrict_sr=1) · [GitHub issues](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+traefik+labels+redeploy)

### 6.7 Legacy Apache behind Dokploy's Traefik

> **Seen as:** `Bad Gateway` with `dial tcp 127.0.0.1:81: connect: connection refused`, `lookup host.docker.internal: no such host`, or `x509: certificate signed by unknown authority` for the 444 backend · **Where:** your next step after moving Apache to 81/444: a dynamic file routes the old vhosts through Traefik · **Level:** [L3 · Senior] · **How common:** several of the Traefik forum's yearly top threads are this pattern (a LAN host behind a containerised Traefik, file-provider services that won't work)

**Why it happens:** Traefik runs in a container. 127.0.0.1 there is Traefik itself; host.docker.internal doesn't exist on Linux unless the container was started with a host-gateway mapping; Apache may listen only on 127.0.0.1:81; UFW may drop traffic from Docker's bridge subnets to port 81 (traffic to the host's own ports does pass UFW's INPUT rules, unlike published ports); and an HTTPS backend on 444 with a self-signed certificate isn't trusted.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :81'
docker exec dokploy-traefik wget -qS -O /dev/null http://192.0.2.10:81/ 2>&1 | head -2
docker network inspect docker_gwbridge --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
```

```text
LISTEN 0 511 127.0.0.1:81 0.0.0.0:* users:(("apache2",pid=1123,fd=4))
wget: can't connect to remote host (192.0.2.10): Connection refused
172.18.0.0/16
```

**What the output tells you:** Apache listens only on loopback, so Traefik's connection to the host's LAN address is refused. Traffic from Traefik to the host leaves through docker_gwbridge (172.18.0.0/16), which is the source UFW must allow.

**Fix:**

```bash
sudo sed -i 's/^Listen 127.0.0.1:81$/Listen 192.0.2.10:81/' /etc/apache2/ports.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
sudo ufw allow from 172.18.0.0/16 to any port 81 proto tcp
```

```yaml
# /etc/dokploy/traefik/dynamic/legacy-apache.yml  (Traefik watches this folder)
http:
  routers:
    legacy-apache:
      rule: Host(`legacy.example.com`)
      entryPoints: [websecure]
      service: legacy-apache
      tls:
        certResolver: letsencrypt
  services:
    legacy-apache:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: http://192.0.2.10:81
```

On the Apache side, enable mod_remoteip (RemoteIPHeader X-Forwarded-For, RemoteIPInternalProxy 172.18.0.0/16; the Internal variant also accepts private LAN client addresses from the header, which RemoteIPTrustedProxy ignores) and drop Apache's own HTTP-to-HTTPS redirect for proxied vhosts. For the 444 HTTPS backend, use a serversTransport with your CA in rootCAs, not insecureSkipVerify.

**Why this fix works:** the router terminates TLS for legacy.example.com and forwards plain HTTP over a private hop to an address Traefik can reach, and UFW allows exactly that source. Don't open 81 to everyone, and don't point the backend at 127.0.0.1.

**Prevent it:** migrate one vhost at a time with a rollback, keep dynamic files in git, and plan to containerise the legacy apps.

**Next step:** [Case: route the legacy Apache sites](21-case-apache-443-dokploy.md) · [Web servers & proxies](29-learn-webservers-proxies.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · KodeKloud: *Nginx For Beginners* — Reverse Proxy · [Traefik file provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/)

**Community threads:** [Traefik docs: File provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/) · [Traefik community: top topics](https://community.traefik.io/top?period=yearly) · Search: [Server Fault](https://serverfault.com/search?q=traefik+file+provider+apache+backend+502) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=file+provider+external+service+bad+gateway&restrict_sr=1)

### 6.8 Uploads die after 60 seconds

> **Seen as:** uploads or long requests fail at about 60 s with 499, 502 or 504; the Traefik access log shows 499; behind Cloudflare, Error 524 at 100 s · **Where:** Traefik v3 entrypoints (Dokploy, Coolify) in front of file apps or a registry · **Level:** [L3 · Senior] · **How common:** the Traefik forum's yearly top includes registry uploads failing with 499 behind Traefik v3.6 in Swarm; Coolify's 504 page lists large uploads

**Why it happens:** Traefik v3 sets the entrypoint's respondingTimeouts.readTimeout to 60s by default, and it covers reading the whole request, body included. Big uploads on slow links exceed it. App servers add their own limits (Gunicorn's 30 s worker timeout, Nginx's client_max_body_size), and Cloudflare adds a 100 s origin timeout and body-size limits per plan.

**Diagnose:**

```bash
curl -o /dev/null -sS -w '%{http_code} %{time_total}s\n' -T big.bin https://files.example.com/upload
grep -nA6 '^entryPoints' /etc/dokploy/traefik/traefik.yml
docker logs dokploy-traefik 2>&1 | grep '" 499 ' | tail -1    # needs the access log on (common format; section 3 shows JSON)
```

```text
502 60.04s
12:entryPoints:
13-  web:
14-    address: :80
15-  websecure:
16-    address: :443
17-    http3:
18-      advertisedPort: 443
198.51.100.23 - - [03/Oct/2026:10:02:11 +0000] "PUT /upload HTTP/2.0" 499 0 "-" "curl/8.5.0" 1841 "files-router-websecure@file" "http://files-x2c4:8080" 60001ms
```

**What the output tells you:** exactly 60 seconds and a 499: the entrypoint's read timeout cut the upload, and traefik.yml has no respondingTimeouts block, so the default applies.

**Fix:**

```yaml
# /etc/dokploy/traefik/traefik.yml - keep existing keys (http3, http.tls), then: docker restart dokploy-traefik
entryPoints:
  websecure:
    address: :443
    transport:
      respondingTimeouts:
        readTimeout: 600s
```

Raise the app server's limits to match. For a registry, give it its own hostname or entrypoint with long timeouts, or push to Harbor directly instead of through the PaaS proxy.

**Why this fix works:** a longer read window lets slow clients finish sending, and setting it per entrypoint keeps the protection elsewhere. Don't set it to 0 on the public entrypoint: readTimeout is also your defence against slow-client attacks.

**Prevent it:** choose timeouts deliberately per entrypoint, use resumable or chunked uploads for big files, and watch request durations in the access log.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Site down](25-playbook-site-down.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview · [Traefik entryPoints](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/)

**Community threads:** [Traefik docs: EntryPoints](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/) · [Traefik community: top topics](https://community.traefik.io/top?period=yearly) · [Coolify: Gateway Timeout](https://coolify.io/docs/troubleshoot/applications/gateway-timeout) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+v3+upload+timeout+readTimeout) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=readTimeout+upload+499&restrict_sr=1)

### 6.9 Apps log the wrong client IP

> **Seen as:** access logs, rate limits, fail2ban and audit trails show 10.0.x.x, 172.x.0.1 or CDN addresses instead of users · **Where:** Swarm ingress, IPv6 clients on IPv4-only Docker, a CDN or load balancer in front · **Level:** [L3 · Senior] · **How common:** the Traefik forum's yearly top includes "Cannot get real IP address"; a perennial Server Fault and Reddit question

**Why it happens:** each hop can replace the source address. Swarm's ingress mesh SNATs published ports; docker-proxy hands IPv6 clients to the container as the bridge gateway; Traefik ignores X-Forwarded-For from a CDN it doesn't trust (forwardedHeaders.trustedIPs); and the app ignores headers from a proxy it doesn't trust.

**Diagnose:**

```bash
curl -s https://whoami.example.com | grep -iE 'remoteaddr|x-forwarded-for|x-real-ip'   # a traefik/whoami app on the same path
docker service inspect SERVICE --format '{{json .Endpoint.Ports}}'                       # ingress or host mode?
dig +short AAAA app.example.com
```

```text
RemoteAddr: 10.0.1.5:51544
X-Forwarded-For: 198.51.100.77
X-Real-Ip: 198.51.100.77
null
2001:db8::10
```

**What the output tells you:** Traefik received the request from a CDN edge (198.51.100.77) and passed that address on as the client, because the CDN's own X-Forwarded-For wasn't trusted. No published ports on the app is good (Traefik is the only entry). An AAAA record exists, so check Docker's IPv6 too.

**Fix:**

```yaml
# /etc/dokploy/traefik/traefik.yml - trust only your CDN or LB ranges, then restart Traefik
entryPoints:
  web:
    address: :80
    forwardedHeaders:
      trustedIPs: ["198.51.100.0/24"]
  websecure:
    address: :443
    forwardedHeaders:
      trustedIPs: ["198.51.100.0/24"]
```

Then make the app trust only the proxy's subnet (Express trust proxy, Django or Flask proxy fix, Apache mod_remoteip). Use mode=host for any port that must see clients directly, and enable IPv6 in Docker or drop the AAAA record.

**Why this fix works:** Traefik keeps the client address from X-Forwarded-For only when the direct peer is trusted. Dokploy publishes Traefik directly on 80/443 rather than through the ingress mesh, so IPv4 client addresses survive. Never set `insecure: true`: anyone could forge X-Forwarded-For and dodge your rate limits and bans.

**Prevent it:** keep a whoami route in every environment and check it after proxy changes; document the trusted proxy chain.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · KodeKloud: *Nginx For Beginners* — Reverse Proxy · [Traefik entryPoints](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/)

**Community threads:** [Traefik docs: EntryPoints (forwardedHeaders)](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/) · [Traefik community: top topics](https://community.traefik.io/top?period=yearly) · Search: [Server Fault](https://serverfault.com/search?q=traefik+docker+real+client+ip+x-forwarded-for) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=real+ip+cloudflare+trustedIPs&restrict_sr=1)

## 7. Certificates and TLS

### 7.1 Let's Encrypt never issues

> **Seen as:** the browser shows `NET::ERR_CERT_AUTHORITY_INVALID` with issuer `TRAEFIK DEFAULT CERT`; Traefik logs `Unable to obtain ACME certificate` with `Timeout during connect (likely firewall problem)` or `429 rateLimited` · **Where:** Dokploy and Coolify (Traefik ACME), CapRover (Certbot), servers behind NAT or office firewalls · **Level:** [L2 · Mid-level] · **How common:** Dokploy #51 (18 comments), an ACME "403 Unauthorized" discussion and dozens of certificate issues; Coolify keeps a dedicated page

**Why it happens:** HTTP-01 validation needs the name to resolve to your server and port 80 to be reachable from the internet. Traefik tries as soon as you add the domain. If DNS doesn't point there yet, port 80 is blocked, a stale AAAA record sends validation elsewhere, or a WAF or CDN answers the challenge, it fails and keeps serving its built-in self-signed certificate. Retrying in a loop then hits the rate limits (5 failed authorizations per name per hour, 5 certificates per identical name set per week).

**Diagnose:**

```bash
dig +short A app.example.com @1.1.1.1 ; dig +short AAAA app.example.com @1.1.1.1
curl -s --connect-timeout 10 -o /dev/null -w '%{http_code} %{time_total}s\n' http://app.example.com/.well-known/acme-challenge/test   # run from OUTSIDE
docker logs dokploy-traefik 2>&1 | grep -iE 'acme|certificate' | tail -2
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -issuer
```

```text
203.0.113.10
2001:db8:5::20
000 10.01s
... Unable to obtain ACME certificate for domains "app.example.com": ... Timeout during connect (likely firewall problem)
issuer=CN = TRAEFIK DEFAULT CERT
```

**What the output tells you:** the A record is right, but a stale AAAA points somewhere else and port 80 times out from outside, so Let's Encrypt can't reach the challenge and Traefik falls back to its default certificate.

**Fix:**

```bash
# 1. DNS first: correct A, fix or delete the stale AAAA, wait for the TTL
# 2. Open 80 and 443 from the internet at every layer (cloud SG, office firewall, NAT)
# 3. Re-save or redeploy the domain in Dokploy to retrigger issuance, and watch it:
docker logs -f dokploy-traefik 2>&1 | grep -iE 'acme|certificate'
# Rate-limited? Stop retrying, wait out the window, test against the staging CA first
```

Coolify documents a reset by removing /data/coolify/proxy/acme.json and restarting the proxy. In Dokploy, find the store with `grep -n storage /etc/dokploy/traefik/traefik.yml` and back it up before touching it.

**Why this fix works:** issuance succeeds only when the CA's validation request reaches Traefik on port 80 for that exact name, over IPv4 and IPv6. Once it does, Traefik stores the certificate and renews it. Clicking redeploy while DNS is wrong only burns rate limit.

**Prevent it:** DNS first, domain second; an outside probe that alerts when a certificate has less than 14 days left.

**Next step:** [Site down: TLS scenarios](25-playbook-site-down.md) · [Networking, DNS & TLS](28-learn-networking.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security (Cert Manager and Let's Encrypt) · [Let's Encrypt rate limits](https://letsencrypt.org/docs/rate-limits/)

**Community threads:** [Dokploy #51](https://github.com/Dokploy/dokploy/issues/51) · [Coolify: Let's Encrypt not working](https://coolify.io/docs/troubleshoot/dns-and-domains/lets-encrypt-not-working) · [Let's Encrypt: Rate Limits](https://letsencrypt.org/docs/rate-limits/) · Search: [Server Fault](https://serverfault.com/search?q=traefik+%22default+cert%22+lets+encrypt+not+issued) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=traefik+default+cert+letsencrypt&restrict_sr=1)

### 7.2 Cloudflare: redirect loops, 525, 526

> **Seen as:** `ERR_TOO_MANY_REDIRECTS`, Cloudflare `Error 525 SSL handshake failed` or `526 Invalid SSL certificate`, CapRover `Domain Verification Failed - Error 1107` · **Where:** proxied (orange-cloud) records in front of Dokploy or CapRover · **Level:** [L2 · Mid-level] · **How common:** about 174 Dokploy issues and PRs mention Cloudflare; Dokploy #1839 (22 comments); CapRover #775 (45 comments), and CapRover says Cloudflare isn't officially supported

**Why it happens:** Cloudflare terminates TLS and opens its own connection to your origin. In Flexible mode it talks HTTP to the origin while Traefik redirects HTTP to HTTPS: a loop. Full (strict) needs an origin certificate Cloudflare trusts, so Traefik's default certificate gives 526. Proxied records also break HTTP-01 issuance and CapRover's self-check, and the free certificate covers only one subdomain level.

**Diagnose:**

```bash
dig +short app.example.com                                        # CDN addresses = proxied
curl -sSIL -o /dev/null -w '%{num_redirects} redirects\n' https://app.example.com
curl -skv -o /dev/null --resolve app.example.com:443:203.0.113.10 https://app.example.com/ 2>&1 | grep -iE 'subject:|issuer:'   # -k only to inspect the cert: without it curl aborts before printing it
```

```text
198.51.100.80
curl: (47) Maximum (50) redirects followed
50 redirects
*  subject: CN=TRAEFIK DEFAULT CERT
*  issuer: CN=TRAEFIK DEFAULT CERT
```

**What the output tells you:** Flexible mode plus Traefik's redirect produces the loop, and the origin (reached directly with --resolve) serves only the default certificate, so Full (strict) would fail with 526.

**Fix:**

```bash
# Recommended: Cloudflare SSL/TLS mode "Full (strict)" + HTTPS on in Dokploy, with either
#   - a Let's Encrypt certificate (issue it while the record is DNS-only, or via DNS-01), or
#   - a Cloudflare Origin CA certificate pasted into Dokploy as a custom certificate
# Only for non-sensitive sites: Flexible + HTTPS off in Dokploy
# CapRover: turn the proxy off while verifying, or skip the check:
echo '{"skipVerifyingDomains":"true"}' | sudo tee /captain/data/config-override.json
docker service update captain-captain --force
```

**Why this fix works:** Full (strict) gives one encrypted, verified hop from the CDN to Traefik and no redirect fight. Flexible leaves the origin leg in clear text, so never use it for logins. Keep names one level deep under the zone, or bring your own certificates for deeper names.

**Prevent it:** write one TLS design per domain (where TLS ends, which certificate, which CDN mode) and probe both through the CDN and directly at the origin.

**Next step:** [Site down: TLS scenarios](25-playbook-site-down.md) · [Web, HTTP & TLS](18-web-http-tls.md) · KodeKloud: *DevOps Pre-Requisite Course* — SSL & TLS Basics · [Dokploy Cloudflare docs](https://docs.dokploy.com/docs/core/domains/cloudflare)

**Community threads:** [Dokploy docs: Cloudflare](https://docs.dokploy.com/docs/core/domains/cloudflare) · [CapRover: Troubleshooting](https://caprover.com/docs/troubleshooting.html) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=cloudflare+too+many+redirects+traefik&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=cloudflare+526+traefik+origin+certificate)

### 7.3 Internal names: DNS-01 or your private CA

> **Seen as:** `Cannot issue for "app.lan": Domain name does not end with a valid public suffix (TLD)`, `acme: error presenting token`, or Dokploy's traefik.me check failing with `queryA ESERVFAIL` · **Where:** on-prem apps on internal DNS, wildcard needs, homelabs behind DNS-rebinding protection · **Level:** [L3 · Senior] · **How common:** Dokploy #1404 (own wildcard domains, 33 reactions, open) and #3201 (traefik.me ESERVFAIL, 29 comments); CapRover #1310 wildcard SSL (26 comments); several Traefik forum top threads

**Why it happens:** HTTP-01 needs the server reachable from the internet; non-public TLDs can't get public certificates; wildcards always need DNS-01 with a DNS provider token. Magic names like traefik.me resolve to private addresses, which many resolvers (pfSense, OPNsense, Pi-hole, dnsmasq) block as DNS rebinding. And a custom certificate uploaded in Dokploy creates files but isn't used until a domain is set to use it.

**Diagnose:**

```bash
dig +short shop.apps.corp.example @1.1.1.1                        # any public record at all?
dig +short 192-0-2-10.traefik.me @192.0.2.53 ; dig +short 192-0-2-10.traefik.me @1.1.1.1
openssl x509 -in app-fullchain.crt -noout -ext subjectAltName ; openssl verify -CAfile corp-ca.crt app-fullchain.crt
```

```text
192.0.2.10
X509v3 Subject Alternative Name:
    DNS:apps.corp.example, DNS:*.apps.corp.example
app-fullchain.crt: OK
```

**What the output tells you:** no public record exists (first command empty), the local resolver drops traefik.me while 1.1.1.1 answers 192.0.2.10 (rebinding protection), and your private-CA certificate covers the names and verifies.

**Fix:** two routes, depending on whether the name is public.

```yaml
# Route A - a public domain you own: DNS-01 (merge into /etc/dokploy/traefik/traefik.yml,
# give Traefik the provider token, e.g. CF_DNS_API_TOKEN, as an environment variable: a plain
# docker restart doesn't add variables, so set it in the panel's Traefik environment settings if
# your version has them, or recreate dokploy-traefik with -e and the documented command)
certificatesResolvers:
  letsencrypt-dns:
    acme:
      email: ops@example.com
      storage: /etc/dokploy/traefik/dynamic/acme-dns.json   # same folder as your existing store
      dnsChallenge:
        provider: cloudflare
```

Route B, your private CA (the one you already run for Harbor): issue a leaf whose SANs cover the app names, paste the full chain and key into Dokploy's Certificates, set the domain to HTTPS with no ACME provider, and install the CA on clients with `sudo cp corp-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates`. For rebinding, allow the domain in the resolver's rebind settings or use real internal records.

**Why this fix works:** DNS-01 proves control through a TXT record, so the server never has to be reachable; a private CA works because every client you care about trusts it. Don't hand out self-signed leaf certificates without a CA: people learn to click through warnings.

**Prevent it:** a certificate inventory with expiry alerts; for many internal apps an internal ACME CA (for example smallstep step-ca) lets Traefik renew automatically.

**Next step:** [Security & DevSecOps](37-learn-security-devsecops.md) · [Web, HTTP & TLS](18-web-http-tls.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Work With SSL Certificates · [Dokploy certificates docs](https://docs.dokploy.com/docs/core/certificates)

**Community threads:** [Dokploy docs: Certificates](https://docs.dokploy.com/docs/core/certificates) · [Dokploy #3201](https://github.com/Dokploy/dokploy/issues/3201) · [Dokploy #1404](https://github.com/Dokploy/dokploy/issues/1404) · Search: [Server Fault](https://serverfault.com/search?q=traefik+private+ca+certificate+internal+domain) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=traefik+dns+challenge+internal+domain&restrict_sr=1)

## 8. Builds and deployments

### 8.1 Nixpacks can't build the app

> **Seen as:** `Nixpacks was unable to generate a build plan for this app`, `No start command could be found`, or a container exiting with `Error: Cannot find module '/app/server.js'` · **Where:** first deploy of a Git repository with the default Nixpacks build type (Dokploy, Coolify) · **Level:** [L1 · Junior] · **How common:** the classic first-deploy failure on every Nixpacks-based PaaS, and the reason they all offer other build types

**Why it happens:** Nixpacks reads the files at the build path to choose a language provider, install and build commands, and a start command. A monorepo with the wrong build path, a missing lockfile or start script, or a runtime version the project doesn't support yields no plan or the wrong one. Nixpacks is in maintenance mode upstream; Railpack is its successor, and Dockerfile builds are fully deterministic.

**Diagnose:**

```bash
# The plan (providers, install, build, start) is printed at the top of the deploy log.
git ls-files | grep -E '^(package.json|apps/web/package.json|apps/web/pnpm-lock.yaml)$'
nixpacks plan . | head -2                     # same tool, run where the build path points
```

```text
apps/web/package.json
apps/web/pnpm-lock.yaml
{
  "providers": [],
```

**What the output tells you:** there is no package.json at the repository root; the app lives in apps/web, so a build path left at the root gives Nixpacks nothing to detect.

**Fix:**

```bash
# 1. Set the build path to apps/web in the service's build settings, then redeploy
# 2. Or pin the plan in the repository (apps/web/nixpacks.toml):
#      [phases.setup]
#      nixPkgs = ["nodejs_22", "pnpm"]
#      [start]
#      cmd = "pnpm start"
# 3. For production: switch the build type to Dockerfile, the same file your CI builds
```

**Why this fix works:** the right build path gives Nixpacks the files it needs, and nixpacks.toml removes the guessing. A Dockerfile is explicit and identical in CI and Dokploy, so the image you tested is the image you run.

**Prevent it:** Dockerfile builds (built in CI) for anything that matters; Nixpacks for prototypes.

**Next step:** [Docker: Dockerfile mastery](30-learn-docker.md) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Docker Certified Associate* — Docker Image Management (Multi-Stage Builds) · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [GitHub: Dokploy issues mentioning nixpacks](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+nixpacks) · Search: [Stack Overflow](https://stackoverflow.com/search?q=nixpacks+%22unable+to+generate+a+build+plan%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=nixpacks+build+failed+dokploy&restrict_sr=1)

### 8.2 Environment variables don't reach the app

> **Seen as:** `process.env.DATABASE_URL is undefined`, `KeyError: 'SECRET_KEY'`, or a frontend still showing an old NEXT_PUBLIC_ or VITE_ value · **Where:** applications and Compose services after editing the Environment tab · **Level:** [L1 · Junior] · **How common:** Dokploy #385 "Environment variables not being set in container" (25 comments); #507 on Next.js and the database (35 comments, labelled workaround)

**Why it happens:** variables apply at the next deploy, not when you click save. For Compose, Dokploy writes them to a .env file next to the compose file, and Compose uses that file only to substitute ${VAR} in the YAML: a service receives variables only through env_file or environment. Frontend frameworks bake public variables into the bundle at build time, so runtime values don't change them. And the build container isn't on dokploy-network, so code that queries the database during the build fails.

**Diagnose:**

```bash
sudo ls -l /etc/dokploy/compose/shop-api-k2j4/code/.env
docker compose -f /etc/dokploy/compose/shop-api-k2j4/code/docker-compose.yml config | grep -c DATABASE_URL
docker exec CONTAINER printenv | grep -c '^DATABASE_URL='
```

```text
-rw-r--r-- 1 root root 212 Oct  3 09:40 /etc/dokploy/compose/shop-api-k2j4/code/.env
0
0
```

**What the output tells you:** Dokploy wrote .env, but the compose file never hands it to the service, so the container sees nothing.

**Fix:**

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.2
    env_file: [.env]                    # everything Dokploy wrote
    environment:
      DATABASE_URL: ${DATABASE_URL}     # or pick variables one by one
```

Values that frameworks inline at build time must be build arguments (ARG NEXT_PUBLIC_API_URL, then ENV from it before the build step). Shared values can live at project level and be referenced with the `${{project.NAME}}` syntax. Then redeploy.

**Why this fix works:** env_file and environment are the only paths from .env into a Compose container, and build arguments are the only way into a build. Redeploying creates tasks with the new spec. Keep secrets out of build arguments: they stay in the image history.

**Prevent it:** commit an .env.example contract checked in CI, make the app fail fast when a required variable is missing, and run migrations at start-up rather than at build time.

**Next step:** [Docker: Compose](30-learn-docker.md) · [CI/CD: secrets management](33-learn-cicd-iac-sre.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy #385](https://github.com/Dokploy/dokploy/issues/385) · [Dokploy #507](https://github.com/Dokploy/dokploy/issues/507) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+compose+env_file+variables+not+set+container) · [Reddit r/nextjs](https://www.reddit.com/r/nextjs/search/?q=NEXT_PUBLIC+runtime+environment+variables+docker&restrict_sr=1)

### 8.3 Compose ports: port is already allocated

> **Seen as:** `Bind for 0.0.0.0:80 failed: port is already allocated` · **Where:** compose files copied from tutorials that publish 80, 443 or 8080 · **Level:** [L0 · Fresher] · **How common:** one of the most common Docker errors on Stack Overflow; Dokploy's Compose domain docs route through dokploy-network instead

**Why it happens:** tutorials assume there is no proxy, so they publish ports. On Dokploy, dokploy-traefik already owns 80/443, so the deploy fails. Other published ports "work", but they bypass Traefik, TLS and UFW (Docker's NAT runs before UFW).

**Diagnose:**

```bash
grep -nA2 'ports:' /etc/dokploy/compose/shop-web-p3q1/code/docker-compose.yml
docker ps --format '{{.Names}} {{.Ports}}' | grep -E '0.0.0.0:(80|443)->'
```

```text
12:    ports:
13-      - "80:80"
14-      - "8080:8080"
dokploy-traefik 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp
```

**What the output tells you:** the compose file wants port 80, which Traefik holds, and 8080 would be published to the whole network.

**Fix:**

```yaml
services:
  web:
    image: harbor.example.com/shop/web:1.4.2
    expose: ["8080"]               # reachable by Traefik on dokploy-network, not published
    networks: [dokploy-network]
networks:
  dokploy-network:
    external: true
```

Then add the domain (service web, port 8080) and deploy. A non-HTTP service that really must be reachable gets one specific published port, filtered in DOCKER-USER (entry 13.2).

**Why this fix works:** Traefik reaches containers over the overlay network, so HTTP services never need host ports, and nothing can collide with 80/443 or slip past the firewall.

**Prevent it:** a compose review rule: no `ports:` for HTTP services on a PaaS host, and an outside port scan after deploys.

**Next step:** [Deployment patterns: choosing a port](35-deployment-patterns.md) · [Docker & K8s incidents: ports, host and firewall](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate* — Docker Engine (Publishing Ports) · [Dokploy Compose domains](https://docs.dokploy.com/docs/core/docker-compose/domains)

**Community threads:** [Dokploy docs: Docker Compose domains](https://docs.dokploy.com/docs/core/docker-compose/domains) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22port+is+already+allocated%22+docker+compose+traefik) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+port+already+allocated&restrict_sr=1)

### 8.4 Builds fail: could not resolve host

> **Seen as:** `Could not resolve host: github.com`, or `lookup registry-1.docker.io on 127.0.0.11:53: server misbehaving` · **Where:** builds and containers on Ubuntu hosts with systemd-resolved, on networks that block public DNS · **Level:** [L2 · Mid-level] · **How common:** a section of Dokploy's Networking & DNS troubleshooting page; a Stack Overflow classic; also in your ops-ladder library

**Why it happens:** Ubuntu resolves through systemd-resolved's stub at 127.0.0.53, which containers can't use. Docker copies the real upstreams from /run/systemd/resolve/resolv.conf and, when there are none, falls back to 8.8.8.8 and 8.8.4.4, which on-prem firewalls usually block. Guides that set public resolvers in daemon.json break internal names such as harbor.corp.example instead.

**Diagnose:**

```bash
docker run --rm alpine cat /etc/resolv.conf
docker run --rm alpine nslookup github.com
grep -c '^nameserver' /run/systemd/resolve/resolv.conf
```

```text
nameserver 8.8.8.8
nameserver 8.8.4.4
;; connection timed out; no servers could be reached
0
```

**What the output tells you:** the host gives Docker no usable upstream (0 nameservers), so containers fall back to Google's resolvers, and the firewall drops them.

**Fix:**

```bash
# Root fix: give the host real upstreams (netplan nameservers), so resolved and Docker agree.
# Docker-level fix: internal resolvers in daemon.json (merge, don't overwrite)
sudo python3 -c 'import json,pathlib; p=pathlib.Path("/etc/docker/daemon.json"); c=json.loads(p.read_text()) if p.exists() else {}; c["dns"]=["192.0.2.53","192.0.2.54"]; p.write_text(json.dumps(c, indent=2)+"\n")'
sudo systemctl restart docker                      # restarts containers: use a window
docker run --rm alpine nslookup harbor.corp.example
```

**Why this fix works:** Docker hands these servers to every container (through its embedded DNS on user networks), and internal resolvers answer both internal and public names. Overwriting daemon.json with echo would silently drop your log rotation and address pools.

**Prevent it:** manage netplan DNS and daemon.json with Ansible, and add a build smoke test that resolves one internal and one public name.

**Next step:** [Docker & K8s incidents: DNS and container networking](26-playbook-containers-k8s.md) · [DNS](08-dns.md) · KodeKloud: *Demystifying DNS* — Troubleshooting DNS · [Dokploy networking troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/networking)

**Community threads:** [Dokploy docs: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+build+%22could+not+resolve+host%22+systemd-resolved) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=container+dns+8.8.8.8+blocked&restrict_sr=1)

### 8.5 Builds exhaust memory on the server

> **Seen as:** `Killed`, `exit code: 137` or `JavaScript heap out of memory` during builds, and sites slowing or restarting while a deploy runs · **Where:** Dokploy or Coolify building on the same small VPS that serves production · **Level:** [L2 · Mid-level] · **How common:** Dokploy #711 "Custom build server" (50 reactions); exit 137 during docker build is a Stack Overflow classic

**Why it happens:** a frontend build (Next.js, webpack) can need 2–4 GB of RAM. On a 2–4 GB host without swap, the kernel's OOM killer takes the build or, worse, a production container or the panel. Node's heap limit may also be too small for a big build, or bigger than the host can give.

**Diagnose:**

```bash
sudo dmesg -T | grep -iE 'out of memory|killed process' | tail -2
free -h
```

```text
[Sat Oct  3 10:14:02 2026] Out of memory: Killed process 48211 (node) total-vm:4318620kB, anon-rss:1903344kB
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       3.5Gi       112Mi        12Mi       214Mi        98Mi
Swap:             0B          0B          0B
```

**What the output tells you:** the build's node process was OOM-killed on a 4 GB host with no swap and under 100 MB available; production containers are next.

**Fix:**

```bash
# Best: build in GitLab CI, push to Harbor, deploy the image (Docker provider): no builds here.
# If you must build on the host: cap Node's heap (build argument) and add swap as a safety net
#   NODE_OPTIONS=--max-old-space-size=1536
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Set memory limits for app services in their resource settings in Dokploy; a CLI change would be overwritten by the next deploy.

**Why this fix works:** CI runners are sized for builds and disposable, while production hosts only pull images. Swap turns a sudden kill into visible slowness, and limits keep one leaking app from starving the rest.

**Prevent it:** a rule that production hosts never build, an alert on OOM kills, and a build server or runner with enough RAM.

**Next step:** [Memory](04-memory.md) · [Why is it slow?](23-playbook-slow-system.md) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy #711](https://github.com/Dokploy/dokploy/issues/711) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+build+%22exit+code%3A+137%22+killed) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+build+out+of+memory&restrict_sr=1)

### 8.6 A few seconds of 502 on every deploy

> **Seen as:** `Bad Gateway` or `404 page not found` for 10–60 seconds after each deploy · **Where:** Dokploy applications with one replica and no health check · **Level:** [L2 · Mid-level] · **How common:** rollbacks were among Dokploy's most requested features (#319, 69 reactions); #2223 (32 comments) on old containers not being replaced

**Why it happens:** Swarm updates a service stop-first by default: it stops the old task, then starts the new one. Without a health check, the new task counts as running as soon as the process starts, before the app listens. With one replica nothing serves in between, and migrations at start-up stretch the gap.

**Diagnose:**

```bash
docker service inspect SERVICE --format '{{json .Spec.UpdateConfig}} {{json .Spec.TaskTemplate.ContainerSpec.Healthcheck}}'
while true; do printf '%s ' "$(date +%T)"; curl -s -o /dev/null -w '%{http_code}\n' https://shop.example.com/healthz; sleep 1; done
```

```text
{"Parallelism":1,"FailureAction":"pause","Monitor":5000000000,"MaxFailureRatio":0,"Order":"stop-first"} null
10:21:05 200
10:21:06 502
10:21:19 200
```

**What the output tells you:** stop-first and no health check: the 13-second hole is the time between the old task stopping and the new app listening.

**Fix:** in Dokploy's Swarm settings for the application (durations in nanoseconds), set a health check and a start-first update policy:

```json
{
  "HealthCheck":  { "Test": ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/healthz"],
                    "Interval": 10000000000, "Timeout": 3000000000,
                    "StartPeriod": 30000000000, "Retries": 3 },
  "UpdateConfig": { "Parallelism": 1, "Delay": 5000000000,
                    "Order": "start-first", "FailureAction": "rollback" }
}
```

The two objects go into the matching Health Check and Update Config fields. To try it from the CLI first: `docker service update --update-order start-first --update-failure-action rollback --health-cmd 'wget -qO- http://127.0.0.1:3000/healthz || exit 1' SERVICE` (Dokploy re-applies its own settings at the next deploy).

**Why this fix works:** start-first runs the old and new tasks side by side, Swarm only routes to a task once its health check passes, and a failing new version rolls back by itself. Keep /healthz independent of downstream services, or a database blip will roll back every deploy.

**Prevent it:** a health endpoint in every app, start-first as your default, and a probe that runs during each CI deploy.

**Next step:** [CI/CD, IaC & SRE: deployment strategies](33-learn-cicd-iac-sre.md) · [Docker: Swarm services](30-learn-docker.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Scaling, Rolling Updates and Rollbacks) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Dokploy #319](https://github.com/Dokploy/dokploy/issues/319) · [Dokploy #2223](https://github.com/Dokploy/dokploy/issues/2223) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+zero+downtime+start-first+healthcheck) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+rolling+update+downtime+healthcheck&restrict_sr=1)

## 9. CI/CD: GitLab, Harbor, webhooks and the API

### 9.1 Webhook never fires or says Branch Not Match

> **Seen as:** `Branch Not Match`; in GitLab `Hook execution failed: Requests to the local network are not allowed`; or a webhook that returns 200 and deploys nothing · **Where:** push webhooks from GitLab, GitHub or Gitea, and Docker Hub webhooks · **Level:** [L1 · Junior] · **How common:** Dokploy #2149 (27 comments); Dokploy's auto-deploy docs call out the branch and tag rules

**Why it happens:** Dokploy compares the branch in the push event with the branch configured on the service, and deploys a Docker Hub webhook only when the pushed tag equals the configured tag. Auto Deploy must be switched on. A self-managed GitLab also blocks webhooks to private addresses until an admin allows local-network requests, which is exactly the on-prem case where Dokploy sits on the LAN.

**Diagnose:** open GitLab's Project, Settings, Webhooks, Edit, Recent events to see the status and response body, then reproduce the call with the URL copied from the service's Deployments tab:

```bash
curl -sS -X POST https://dokploy.example.com/api/deploy/WEBHOOK_TOKEN \
  -H 'Content-Type: application/json' -H 'X-Gitlab-Event: Push Hook' \
  -d '{"ref":"refs/heads/develop"}'
```

```text
{"message":"Branch Not Match"}
```

**What the output tells you:** the service is set to another branch (main) while the push came from develop. If GitLab's Recent events show the local-network error instead, the request never left GitLab.

**Fix:**

```bash
# 1. Service > General: branch = the branch you push (main); enable Auto Deploy
# 2. GitLab webhook: the URL from the Deployments tab, "Push events", branch filter main
# 3. Self-managed GitLab (admin): Admin > Settings > Network > Outbound requests:
#    allow local-network webhooks only for the panel host via the allowlist (dokploy.example.com)
# 4. GitLab: Test > Push events, then check Recent events for HTTP 200
```

**Why this fix works:** once branch and event match, every push queues a deploy. The allowlist lets GitLab reach one private host without opening webhooks to your whole LAN, so its SSRF protection stays on.

**Prevent it:** in pipelines, prefer an explicit API call as the last CI job (entry 9.2): the deploy appears in the pipeline and fails it visibly.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · [CI/CD, IaC & SRE: GitLab CI/CD](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts · [Dokploy auto-deploy docs](https://docs.dokploy.com/docs/core/auto-deploy)

**Community threads:** [Dokploy docs: Auto Deploy](https://docs.dokploy.com/docs/core/auto-deploy) · [Dokploy #2149](https://github.com/Dokploy/dokploy/issues/2149) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+webhook+%22requests+to+the+local+network+are+not+allowed%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=webhook+local+network+not+allowed&restrict_sr=1)

### 9.2 API deploy from GitLab CI fails

> **Seen as:** `HTTP 401 Unauthorized` or curl exit code 22; `curl: (60) SSL certificate problem: unable to get local issuer certificate`; in v0.25.10 `Webhook Docker Image Name Not Found` · **Where:** the last job of a GitLab pipeline calling Dokploy's API or an image webhook · **Level:** [L2 · Mid-level] · **How common:** Dokploy #3086 (33 comments, 24 reactions); the API flow is documented on the auto-deploy page

**Why it happens:** the documented call is POST /api/application.deploy with an x-api-key header and `{"applicationId": "..."}`; IDs come from GET /api/project.all and tokens from your profile. Typical breakages: the token sent as Authorization: Bearer, a revoked token, an applicationId used for a Compose service, a protected CI variable that doesn't exist on an unprotected branch, a runner image that doesn't trust the panel's private CA, or a release regression. #3086 broke webhook deploys of image-only apps in v0.25.10, and PR #3213 fixed it.

**Diagnose:**

```bash
echo "token length: ${#DOKPLOY_TOKEN}"            # 0 = variable not available on this branch
curl -sS -o /dev/null -w '%{http_code}\n' -H "x-api-key: $DOKPLOY_TOKEN" "$DOKPLOY_URL/api/project.all"
curl -sS -H "x-api-key: $DOKPLOY_TOKEN" "$DOKPLOY_URL/api/project.all" | jq -r '.. | objects | select(has("applicationId") and has("appName")) | "\(.applicationId) \(.name)"'
```

```text
token length: 0
401
```

**What the output tells you:** the job has no token (a protected variable on an unprotected branch), so the API answers 401. With a token you would see the IDs and names to put in DOKPLOY_APP_ID.

**Fix:**

```yaml
deploy:
  stage: deploy
  image: curlimages/curl:8.10.1
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH       # protected branch: protected variables exist
  script:
    - >
      curl --fail-with-body -sS --cacert "$CORP_CA_FILE"
      -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$DOKPLOY_APP_ID\"}"
```

CORP_CA_FILE is a GitLab variable of type File holding your CA, needed only if the panel uses the private CA. Compose services use the compose deploy endpoint with a composeId (check your instance's API reference).

**Why this fix works:** x-api-key is the header the API checks, protected variables reach protected refs only, `--cacert` trusts exactly your CA, and `--fail-with-body` fails the job while showing the server's message. Never use `-k`: it hides interception and expired certificates for good.

**Prevent it:** a smoke test after the deploy (curl the health URL, fail on anything but 200), one token per pipeline, rotated, and the deployed version printed in the job log.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab · [Dokploy auto-deploy docs](https://docs.dokploy.com/docs/core/auto-deploy)

**Community threads:** [Dokploy #3086](https://github.com/Dokploy/dokploy/issues/3086) · [Dokploy docs: Auto Deploy](https://docs.dokploy.com/docs/core/auto-deploy) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+curl+api+deploy+401+x-api-key) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=protected+variable+empty+pipeline&restrict_sr=1)

### 9.3 Private CA: x509 from Harbor or GitLab

> **Seen as:** `tls: failed to verify certificate: x509: certificate signed by unknown authority` on pulls; `SSL certificate problem: unable to get local issuer certificate` on clones · **Where:** Dokploy pulling from Harbor or cloning from self-managed GitLab, on every node and remote server · **Level:** [L2 · Mid-level] · **How common:** the standard on-prem trust problem; Harbor's docs give HTTPS with your own CA a page of its own

**Why it happens:** every client keeps its own trust. dockerd checks /etc/docker/certs.d/HOST/ca.crt and the OS store, on every node that pulls. Git and Node run inside the Dokploy container, which doesn't see the host's store. A server that sends only its leaf certificate, without the intermediate, fails everywhere that doesn't already hold the intermediate.

**Diagnose:**

```bash
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts < /dev/null 2>/dev/null | grep -E '^ *[0-9] s:|^ *i:'
ls /etc/docker/certs.d/harbor.example.com/ 2>/dev/null || echo "no registry CA on $(hostname)"
docker exec $(docker ps -q -f name=dokploy.1) git ls-remote https://gitlab.example.com/web/shop.git 2>&1 | tail -1
```

```text
 0 s:CN = harbor.example.com
   i:CN = Example Corp Issuing CA 1
no registry CA on node-2
fatal: unable to access 'https://gitlab.example.com/web/shop.git/': SSL certificate problem: unable to get local issuer certificate
```

**What the output tells you:** three separate gaps: Harbor sends only its leaf (no "1 s:" line for the intermediate), node-2 has no CA for the registry, and the Dokploy container doesn't trust GitLab.

**Fix:**

```bash
# Every Docker host (manager, workers, remote servers)
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp corp-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
# Git inside the panel: simplest is the plain Git source with an SSH deploy key. Otherwise trust
# the CA for GitLab only (re-check after Dokploy updates):
docker service update \
  --mount-add type=bind,src=/usr/local/share/ca-certificates/corp-ca.crt,dst=/etc/ssl/corp-ca.crt,readonly \
  --env-add NODE_EXTRA_CA_CERTS=/etc/ssl/corp-ca.crt --env-add GIT_CONFIG_COUNT=1 \
  --env-add GIT_CONFIG_KEY_0=http.https://gitlab.example.com/.sslCAInfo \
  --env-add GIT_CONFIG_VALUE_0=/etc/ssl/corp-ca.crt dokploy
```

Also make Harbor and GitLab send the full chain (leaf plus intermediate).

**Why this fix works:** each client now finds the CA where it looks. The per-URL git setting trusts your CA for gitlab.example.com only, so clones from public hosts keep the normal bundle, and NODE_EXTRA_CA_CERTS adds to Node's defaults rather than replacing them. Never use insecure-registries or `http.sslVerify=false`: both accept any certificate at all.

**Prevent it:** distribute the CA with Ansible to every Docker host, bake it into runner images, and alert on certificate expiry.

**Next step:** [Docker: registries and Harbor](30-learn-docker.md) · [Security & DevSecOps](37-learn-security-devsecops.md) · KodeKloud: *Docker Certified Associate* — Docker Image Management (Authenticating to Registries) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [Harbor documentation](https://goharbor.io/docs/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+pull+%22x509%3A+certificate+signed+by+unknown+authority%22+harbor) · [Server Fault](https://serverfault.com/search?q=git+%22unable+to+get+local+issuer+certificate%22+gitlab) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=harbor+private+ca+x509+docker&restrict_sr=1)

### 9.4 Old version still served after a new image

> **Seen as:** CI pushed a new image and Dokploy redeployed, but users get the old code; Swarm warns `image harbor.example.com/shop/web:latest could not be accessed on a registry to record its digest`; workers fail with `No such image` · **Where:** mutable tags such as latest, private registries, multi-node clusters · **Level:** [L2 · Mid-level] · **How common:** Dokploy #1998 "Image not pulled on docker swarm" (22 comments); #2655 "Ability to Pull Updated Docker Images via UI" (39 reactions)

**Why it happens:** Swarm pins a service to an image digest only when the manager can query the registry with credentials. Without registry login (or with an untrusted CA) it warns, and each node runs whatever local image matches the tag, so :latest keeps the old code wherever it is cached. Images that Dokploy builds on the manager exist only there: workers can't pull what was never pushed.

**Diagnose:**

```bash
docker service inspect SERVICE --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
docker service ps SERVICE --format '{{.Node}} {{.CurrentState}} {{.Error}}'
```

```text
harbor.example.com/shop/web:latest
node-1 Running 2 minutes ago
node-2 Rejected 1 minute ago "No such image: harbor.example.com/shop/web:latest"
```

**What the output tells you:** no @sha256 in the spec, so nothing is pinned; node-1 runs whatever it had cached, and node-2 can't get the image at all (no credentials or CA there).

**Fix:**

```bash
# CI: immutable tags (commit SHA); a moving tag is only a convenience
docker build -t harbor.example.com/shop/web:3f9c2ab . && docker push harbor.example.com/shop/web:3f9c2ab
# Dokploy: add Harbor as a registry and select it on the service; for a cluster, set the registry
# Dokploy pushes built images to. The CLI equivalent shows the mechanism:
docker service update --with-registry-auth --image harbor.example.com/shop/web:3f9c2ab SERVICE
docker service inspect SERVICE --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'   # now ...:3f9c2ab@sha256:...
```

**Why this fix works:** with credentials the manager resolves the tag to a digest and every node pulls exactly that image; an immutable tag makes "what is running" answerable and rollbacks exact. Every node still needs the CA (entry 9.3).

**Prevent it:** never deploy :latest to production, print the deployed digest in the pipeline, and keep old tags with Harbor retention for rollbacks.

**Next step:** [Docker: registries and Harbor](30-learn-docker.md) · [Docker & K8s incidents: images, registry and builds](26-playbook-containers-k8s.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Registry · [Docker docs](https://docs.docker.com/)

**Community threads:** [Dokploy #1998](https://github.com/Dokploy/dokploy/issues/1998) · [Dokploy #2655](https://github.com/Dokploy/dokploy/issues/2655) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22could+not+be+accessed+on+a+registry+to+record+its+digest%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+service+update+latest+not+pulling&restrict_sr=1)

## 10. Data: volumes, databases and backups

### 10.1 Data gone after a redeploy

> **Seen as:** a config file from the repository is empty after AutoDeploy, the database starts empty, or the service never starts with `invalid mount config for type "bind": bind source path does not exist` while the deploy log says success · **Where:** Compose services with ./ bind mounts; Swarm services with host paths · **Level:** [L1 · Junior] · **How common:** Dokploy's "Volumes & Mounts" troubleshooting page covers four variants; #1627 (33 reactions)

**Why it happens:** Dokploy clones the repository into a code directory and cleans it on every deploy (AutoDeploy does a fresh clone), so ./data and ./config bind mounts point into a folder that gets wiped. Swarm won't start a task whose bind source is missing on that node, yet the deployment itself "succeeded". CapRover's version of the trap: an app created without "Has Persistent Data" can't keep volumes.

**Diagnose:**

```bash
docker service ps SERVICE --no-trunc --format '{{.Name}} {{.CurrentState}} {{.Error}}' | head -2
docker inspect CONTAINER --format '{{json .Mounts}}' | jq -c '.[] | {Type, Source, Destination}'
sudo ls /etc/dokploy/compose/shop-k2j4/
```

```text
shop-db.1 Rejected 20 seconds ago "invalid mount config for type "bind": bind source path does not exist: /srv/shop/pgdata"
{"Type":"bind","Source":"/etc/dokploy/compose/shop-k2j4/code/data","Destination":"/var/lib/postgresql/data"}
code  files
```

**What the output tells you:** one service points at a host path that doesn't exist on the node it landed on, and a Compose database keeps its data inside code/, which the next deploy wipes. files/ is where persistent bind data belongs.

**Fix:**

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - ../files/pgdata:/var/lib/postgresql/data        # outside code/, survives redeploys
  app:
    volumes:
      - ../files/app-config.yml:/etc/app/config.yml:ro  # created as a File Mount (Advanced > Mounts)
```

Before switching, stop the service and copy the existing data into files/ (`sudo cp -a`). For Swarm host paths, create the directory on every node that may run the task, pin the placement, or use a named volume.

**Why this fix works:** ../files (seen from the compose file) is outside the re-cloned code directory, File Mounts are written by Dokploy before the service starts, and named volumes live under /var/lib/docker/volumes across deploys. Turning off AutoDeploy only hides the problem.

**Prevent it:** a review rule (no ./ bind mounts in Dokploy compose files), volume backups, and a staging redeploy that checks the data is still there.

**Next step:** [Docker: storage](30-learn-docker.md) · [Databases for DevOps](38-learn-databases-ops.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [Dokploy volumes troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/volumes-mounts)

**Community threads:** [Dokploy docs: Volumes & Mounts](https://docs.dokploy.com/docs/core/troubleshooting/volumes-mounts) · [Dokploy #1627](https://github.com/Dokploy/dokploy/issues/1627) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+%22bind+source+path+does+not+exist%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+volume+data+lost+redeploy&restrict_sr=1)

### 10.2 App can't reach its database

> **Seen as:** `getaddrinfo ENOTFOUND shop-db-x1y2z3`, `connect ECONNREFUSED 10.0.1.14:5432`, or `connection to server ... failed: Connection refused` · **Where:** apps talking to Dokploy-managed Postgres, MySQL, MongoDB or Redis · **Level:** [L1 · Junior] · **How common:** Dokploy #507 (35 comments) and #2331 "cannot connect to postgres" (19 comments)

**Why it happens:** Dokploy databases run as Swarm services on dokploy-network and show an internal host and port for apps. Connections fail when the app sits on another network (a Compose project not attached to dokploy-network), when the URL uses localhost or the external port, when the database lives on a different server, when the code runs during the image build, or when VIP mode lacks IPVS (entry 5.4).

**Diagnose:**

```bash
docker inspect CONTAINER --format '{{json .NetworkSettings.Networks}}' | jq -c 'keys'
docker exec CONTAINER printenv DATABASE_URL | sed 's#//[^@]*@#//***@#'
docker run --rm --network dokploy-network nicolaka/netshoot nc -zv -w 3 shop-db-x1y2z3 5432
```

```text
["shop_default"]
postgres://***@localhost:5432/shop
Connection to shop-db-x1y2z3 (10.0.1.14) 5432 port [tcp/postgresql] succeeded!
```

**What the output tells you:** the database is fine and reachable on dokploy-network, but the app sits only on its project network and points at localhost, which inside a container is the container itself.

**Fix:**

```yaml
services:
  app:
    environment:
      DATABASE_URL: postgres://shop:${DB_PASSWORD}@shop-db-x1y2z3:5432/shop   # internal host from the DB page
    networks: [dokploy-network]
networks:
  dokploy-network:
    external: true
```

Keep the app and its database on the same server, or connect across servers over a private network or VPN. Move database access out of the build (run migrations at start-up). If a routed service must stay on two networks, apply entry 6.3 too.

**Why this fix works:** the internal name resolves only on dokploy-network, and the internal port is the container port, not the external one. Exposing the database publicly so the app can connect trades a config bug for a security incident (entry 13.2).

**Prevent it:** a small network diagram per project, and an app that logs which database host it resolved at start-up.

**Next step:** [Databases for DevOps](38-learn-databases-ops.md) · [Docker & K8s incidents: DNS and container networking](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Swarm Service Discovery) · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy #507](https://github.com/Dokploy/dokploy/issues/507) · [Dokploy #2331](https://github.com/Dokploy/dokploy/issues/2331) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+compose+getaddrinfo+ENOTFOUND+postgres+network) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+database+connection+refused&restrict_sr=1)

### 10.3 S3 backups fail or were never restored

> **Seen as:** backup failure notifications with `SignatureDoesNotMatch`, `RequestTimeTooSkewed`, `NoSuchBucket` or `x509: certificate signed by unknown authority`, or a bucket that only grows · **Where:** Dokploy database, volume and panel backups to AWS S3, MinIO or R2 · **Level:** [L2 · Mid-level] · **How common:** Dokploy #416 on destination types (51 comments), #338 "How to restore a database backup" (27 reactions), #709 panel backups (59 reactions)

**Why it happens:** S3 clients sign each request with the key, region, endpoint and current time. A MinIO endpoint on the console port (9001) instead of the API port (9000), a wrong region or bucket, a host clock minutes off, or a private CA on the endpoint makes the request fail. Without retention the bucket grows forever, and nobody knows whether a restore works until the day it is needed.

**Diagnose:**

```bash
aws --endpoint-url https://minio.example.com:9000 --region us-east-1 s3 ls s3://dokploy-backups/shop-db/ | tail -2
timedatectl | grep 'System clock synchronized'
```

```text
2026-10-02 02:00:14   48211934 shop-db-2026-10-02T02-00-00.sql.gz
2026-10-03 02:00:12   48390211 shop-db-2026-10-03T02-00-00.sql.gz
System clock synchronized: no
```

**What the output tells you:** endpoint, region and credentials work from this host, and backups exist; the unsynchronised clock is the likely source of the intermittent signature and time errors.

**Fix:**

```bash
sudo timedatectl set-ntp true                      # signatures need the right time
# Destination in Dokploy: endpoint https://minio.example.com:9000 (API port), region us-east-1,
# an existing bucket, a key limited to that bucket; test it, then set "keep latest N" per schedule
# Monthly restore drill into a scratch database:
aws --endpoint-url https://minio.example.com:9000 s3 cp s3://dokploy-backups/shop-db/shop-db-2026-10-03T02-00-00.sql.gz .
docker exec SCRATCH_PG createdb -U postgres restore_test
gunzip -c shop-db-2026-10-03T02-00-00.sql.gz | docker exec -i SCRATCH_PG pg_restore -U postgres -d restore_test --no-owner --no-acl
docker exec SCRATCH_PG psql -U postgres -d restore_test -c '\dt'      # tables are back
```

Dokploy's Postgres backups are custom-format dumps (`pg_dump -Fc`, then gzip) despite the .sql.gz name, so they go through pg_restore, not psql; use a scratch Postgres of the same or a newer major version. MySQL and MariaDB backups are plain SQL (gunzip into mysql), MongoDB backups are gzipped mongodump archives (mongorestore --archive --gzip). Check the backup command your version uses in its source if a restore complains about the format. Add a lifecycle rule on the bucket as a second retention guard.

**Why this fix works:** requests sign correctly once time, endpoint and region match what the server expects; retention bounds the cost; the drill proves the dump is complete and that you know the steps under pressure.

**Prevent it:** failure notifications for every backup, a monthly restore drill with the time measured, and an off-site copy of the bucket.

**Next step:** [Databases for DevOps](38-learn-databases-ops.md) · [Time & NTP](12-time-ntp.md) · KodeKloud: *Fundamentals of SRE* — Incident Management · [Dokploy backups docs](https://docs.dokploy.com/docs/core/backups)

**Community threads:** [Dokploy docs: Backups](https://docs.dokploy.com/docs/core/backups) · [Dokploy #416](https://github.com/Dokploy/dokploy/issues/416) · [Dokploy #338](https://github.com/Dokploy/dokploy/issues/338) · Search: [Stack Overflow](https://stackoverflow.com/search?q=minio+%22SignatureDoesNotMatch%22+endpoint+region) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+backup+s3+minio&restrict_sr=1)

### 10.4 Restoring Dokploy on a new server

> **Seen as:** the panel is back after a restore, but apps are down, webhooks fail and traefik.me domains point at the old address · **Where:** disaster recovery or a move to new hardware · **Level:** [L4 · Senior/Lead] · **How common:** the post-restore steps are documented on Dokploy's backups page; #709 (59 reactions) asked for panel backups in the first place

**Why it happens:** the panel backup is one zip of dokploy-postgres and /etc/dokploy. Restoring it clears /etc/dokploy and replaces the panel database; it contains no images, no app volumes and no database data. On a new server the stored server IP, DNS, Git provider callbacks and traefik.me names still point at the old host.

**Diagnose:**

```bash
docker service ls --format '{{.Name}} {{.Replicas}}' | grep ' 0/'
dig +short shop.example.com
docker service inspect dokploy --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
```

```text
shop-web-x7k2p 0/1
shop-db-x1y2z3 0/1
203.0.113.10
dokploy/dokploy:v0.30.6
```

**What the output tells you:** the services exist but have no running tasks (their images and data aren't on this host yet), and DNS still points at the old server.

**Fix:**

```bash
# 1. Install the same Dokploy version as the backup (sudo DOKPLOY_VERSION=vX.Y.Z sh dokploy-install.sh),
#    then restore from Web Server > Backups
# 2. Web Server > Server > Update IP; update DNS (TTL lowered in advance); reconnect Git providers;
#    recreate traefik.me domains
# 3. Trust the CA and log in to Harbor on the new host (entry 9.3), then redeploy every service
# 4. Restore database dumps and volume backups (entry 10.3), then check each domain from outside:
for d in shop.example.com api.example.com; do curl -s -o /dev/null -w "$d %{http_code}\n" "https://$d/healthz"; done
```

**Why this fix works:** the panel restore brings back configuration, updating IP, DNS and providers re-points the outside world, redeploys pull images and recreate tasks, and data restores bring back state, in that order, so no app takes traffic before its data is there. Restoring onto a different Dokploy version is a gamble unless the release notes say it is safe.

**Prevent it:** a quarterly DR drill onto a scratch VM with a timed runbook and written recovery time and recovery point targets.

**Next step:** [CI/CD, IaC & SRE: game days](33-learn-cicd-iac-sre.md) · [Senior: architecture](39-learn-senior-architecture.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [Dokploy backups docs](https://docs.dokploy.com/docs/core/backups)

**Community threads:** [Dokploy docs: Backups (restore)](https://docs.dokploy.com/docs/core/backups) · [Dokploy #709](https://github.com/Dokploy/dokploy/issues/709) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+restore+backup+new+server&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+disaster+recovery+restore+new+server)

## 11. Host resources and Docker networking

### 11.1 Disk full: images, build cache, logs

> **Seen as:** `no space left on device` during builds, Postgres `could not write to file "pg_wal/xlogtemp"`, logs that stop loading · **Where:** any PaaS host that builds on itself · **Level:** [L1 · Junior] · **How common:** Dokploy's docs name a full disk as a cause of missing logs and of Postgres starting in recovery mode; the panel ships clean actions and a daily cleanup option

**Why it happens:** every deploy leaves an image behind, BuildKit's cache grows with every build, json-file logs grow without rotation, and volumes of deleted services stay. All of it shares the disk with the panel's own Postgres: builds fail first, then logs, then the panel.

**Diagnose:**

```bash
df -h /var/lib/docker
docker system df
sudo find /var/lib/docker/containers -name '*-json.log' -size +500M -exec ls -lh {} +
```

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        78G   75G  2.9G  97% /
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          143       14        41.2GB    36.8GB (89%)
Containers      19        16        1.1GB     12MB (1%)
Local Volumes   22        9         6.4GB     2.1GB (32%)
Build Cache     612       0         19.7GB    19.7GB
-rw-r----- 1 root root 2.3G Oct  3 10:40 /var/lib/docker/containers/9c1e4b.../9c1e4b...-json.log
```

**What the output tells you:** 37 GB of unused images and 20 GB of build cache can go safely, and one container log has grown to 2.3 GB without rotation.

**Fix:**

```bash
docker builder prune -f --filter until=72h
docker image prune -a -f --filter until=168h       # unused images older than 7 days
# Panel: enable the daily Docker cleanup for each server (or a systemd timer with the two lines above)
# Log rotation for new containers: "log-opts": {"max-size": "10m", "max-file": "3"} in daemon.json
```

**Why this fix works:** both commands remove only what no container uses, and the until filter keeps recent images for rollbacks. Never run `docker system prune -a --volumes` or `docker volume prune -a` on a PaaS host: since Docker 23 the first removes every unused anonymous volume (an image's VOLUME, such as a Compose Postgres without a named volume) and the second every unused named volume too, so a stopped database loses its data. In an emergency `truncate -s 0` on a runaway log is fine; deleting the file isn't, because Docker keeps it open.

**Prevent it:** a disk alert at 80 %, a weekly cleanup timer, log rotation in the server build, builds in CI, and /var/lib/docker on its own volume.

**Next step:** [Storage & disk](01-storage-disk.md) · [Docker & K8s incidents: disk, storage and permissions](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate* — Docker Engine (Logging Driver) · [Dokploy logs & monitoring troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/logs-monitoring)

**Community threads:** [Dokploy docs: Logs & Monitoring](https://docs.dokploy.com/docs/core/troubleshooting/logs-monitoring) · [Dokploy docs: Dokploy Instance](https://docs.dokploy.com/docs/core/troubleshooting/instance) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+%22no+space+left+on+device%22+build+cache+prune) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+disk+full&restrict_sr=1)

### 11.2 Everything down after a reboot

> **Seen as:** the panel logs `Migration failed [Error: getaddrinfo ENOTFOUND dokploy-postgres]`, or every domain stays dead until someone reloads Traefik; Coolify shows `Failed to connect to 127.0.0.1 port 8080` · **Where:** after patching, a power cut or a hypervisor restart · **Level:** [L1 · Junior] · **How common:** Dokploy #1802 "Traefik not working properly upon restart" (54 comments, the second most-commented Dokploy issue); Coolify #5933 (40 comments)

**Why it happens:** nothing orders the start of the Swarm services (dokploy, dokploy-postgres) against the standalone dokploy-traefik container. dokploy can start before Postgres answers and give up on its migrations; Traefik can come up before the networks and services it routes to. A full disk makes Postgres start in recovery mode. Coolify adds Redis failing to save without vm.overcommit_memory=1.

**Diagnose:**

```bash
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'dokploy|traefik'
docker service logs dokploy --since 10m 2>&1 | grep -i migration | tail -2
df -h /var/lib/docker | tail -1
```

```text
dokploy.1.p8x2kq7v0m4n6b1c3z5l7j9h2 Up 2 minutes
dokploy-postgres.1.k3l0aa91c2w4e6r8t1y3u5i7o Up 2 minutes
dokploy-traefik Up 3 minutes
Migration failed [Error: getaddrinfo ENOTFOUND dokploy-postgres]
/dev/sda2        78G   41G   34G  55% /
```

**What the output tells you:** everything runs now, but dokploy started before Postgres was resolvable and gave up; the disk is fine.

**Fix:**

```bash
docker service scale dokploy=0 && docker service scale dokploy=1   # reruns migrations now that Postgres is up
docker restart dokploy-traefik                                       # or reload Traefik from the panel
# Coolify only: Redis overcommit
echo 'vm.overcommit_memory = 1' | sudo tee /etc/sysctl.d/99-redis.conf && sudo sysctl --system
```

If the panel's domain is down as well, reach the UI through an SSH tunnel to 3000 (re-add the 3000 publish first if you removed it).

**Why this fix works:** restarting each component after its dependencies are up gives it the order it needed; it is the documented workaround while start-order races like #1802 exist.

**Prevent it:** reboot test servers on purpose and time the recovery; outside probes per domain so a post-reboot outage pages you; a small post-boot oneshot unit that runs the two restart commands once Docker is up, tested with a planned reboot.

**Next step:** [Services & systemd](07-services-systemd.md) · [Docker & K8s incidents: Dokploy, Traefik and Swarm](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate* — Docker Engine (Restart Policies) · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance)

**Community threads:** [Dokploy #1802](https://github.com/Dokploy/dokploy/issues/1802) · [Coolify #5933](https://github.com/coollabsio/coolify/issues/5933) · [Dokploy docs: Dokploy Instance](https://docs.dokploy.com/docs/core/troubleshooting/instance) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+not+working+after+reboot&restrict_sr=1)

### 11.3 Docker subnets exhausted or overlapping

> **Seen as:** `all predefined address pools have been fully subnetted`, `could not find an available, non-overlapping IPv4 address pool`, or office and VPN users who suddenly can't reach the server · **Where:** hosts with many Compose projects or preview deployments; on-prem networks that use 172.16.0.0/12 or 192.168.0.0/16 · **Level:** [L2 · Mid-level] · **How common:** a section of Dokploy's Networking & DNS page; Dokploy #1004 "network conflict" (18 comments)

**Why it happens:** every Compose project gets its own bridge network, and the default pools allow only about 31 of them. On-prem, the default ranges often overlap office LANs or VPN pools, and a bridge on an overlapping subnet silently steals the route back to those users.

**Diagnose:**

```bash
docker network ls -q | wc -l
docker network inspect $(docker network ls -q) --format '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}' | grep 172.20
ip route get 172.20.14.25                 # a VPN client's address
```

```text
33
shop_default 172.20.0.0/16
172.20.14.25 dev br-5e1c2a7d9f30 src 172.20.0.1 uid 1000
    cache
```

**What the output tells you:** replies to the VPN client leave through a Docker bridge instead of the LAN gateway (the overlap), and 33 networks means the pools are nearly exhausted.

**Fix:**

```bash
docker network prune -f                    # unused networks only
# Permanent: a range nobody else uses (agree it with the network team), merged into daemon.json:
#   "default-address-pools": [{"base": "10.200.0.0/16", "size": 24}]
sudo systemctl restart docker              # existing networks keep their subnets: recreate the affected projects
# Swarm overlay pools are fixed at swarm init (installer: DOCKER_SWARM_INIT_ARGS="--default-addr-pool ...")
```

**Why this fix works:** /24 networks carved from a dedicated /16 give 256 networks that collide with nothing, and recreating a project moves it off the overlapping subnet.

**Prevent it:** reserve a Docker range in your IP plan and bake it into the server build before Dokploy is installed.

**Next step:** [Networking, DNS & TLS](28-learn-networking.md) · [Network speed](24-playbook-network-speed.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Dokploy networking troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/networking)

**Community threads:** [Dokploy docs: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking) · [Dokploy #1004](https://github.com/Dokploy/dokploy/issues/1004) · Search: [Server Fault](https://serverfault.com/search?q=docker+%22pool+overlaps+with+other+one+on+this+address+space%22) · [Stack Overflow](https://stackoverflow.com/search?q=%22all+predefined+address+pools+have+been+fully+subnetted%22)

## 12. Remote servers, clusters and monitoring

### 12.1 Remote server setup fails over SSH

> **Seen as:** `All configured authentication methods failed`, `connect ECONNREFUSED 192.0.2.20:22` or `Timed out while waiting for handshake` · **Where:** adding a remote server in Dokploy (Coolify validates every server the same way) · **Level:** [L2 · Mid-level] · **How common:** Dokploy #1126 "Allow multiserver deployment as non-root user" (28 reactions); "server not reachable" is a recurring Coolify support topic

**Why it happens:** the panel logs in with the private key it stores, then installs Docker, Traefik and build tools during setup, which historically expected root. A hardened sshd (AllowUsers, root login off, another port), fail2ban banning the panel after a few failed tries, a firewall in between, or a key in the wrong user's authorized_keys all stop it.

**Diagnose:**

```bash
# From the panel host, with the same key and user Dokploy uses
ssh -i dokploy_key -o BatchMode=yes -o ConnectTimeout=5 root@192.0.2.20 true
# On the target
sudo sshd -T | grep -E '^(permitrootlogin|allowusers) '
sudo journalctl -u ssh --since '15 min ago' | grep -i 'not allowed' | tail -1
sudo fail2ban-client status sshd | grep 'Banned IP'
```

```text
root@192.0.2.20: Permission denied (publickey).
permitrootlogin prohibit-password
allowusers ops
... sshd[2210]: User root from 192.0.2.10 not allowed because not listed in AllowUsers
   `- Banned IP list:   192.0.2.10
```

**What the output tells you:** AllowUsers admits only ops, so root is refused, and fail2ban then banned the panel's address after its retries.

**Fix:**

```bash
# Root by key only, and only from the panel host; ops keeps working as before
sudo sed -i 's/^AllowUsers .*/AllowUsers ops root@192.0.2.10/' /etc/ssh/sshd_config
sudo sshd -t && sudo systemctl reload ssh
sudo install -d -m 700 /root/.ssh && sudo tee -a /root/.ssh/authorized_keys < dokploy_key.pub
sudo fail2ban-client set sshd unbanip 192.0.2.10   # and add 192.0.2.10 to ignoreip in jail.local
```

Then run the server setup again from the panel. If your Dokploy version supports a non-root user, prefer that, with the sudo and docker rights the setup documents.

**Why this fix works:** AllowUsers accepts USER@HOST patterns, so the panel's key works from the panel's address only, root stays key-only, and ignoreip stops fail2ban from fighting the panel.

**Prevent it:** provision every server with Ansible (users, keys, sshd, UFW, fail2ban) so new servers are panel-ready on day one.

**Next step:** [SSH & remote access](09-ssh-remote-access.md) · [Security & DevSecOps](37-learn-security-devsecops.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy #1126](https://github.com/Dokploy/dokploy/issues/1126) · [Coolify: Troubleshooting](https://coolify.io/docs/troubleshoot/overview) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ssh2+%22All+configured+authentication+methods+failed%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=coolify+server+not+reachable+ssh&restrict_sr=1)

### 12.2 Worker replicas time out

> **Seen as:** `Gateway Timeout` for requests that land on replicas on worker nodes while replicas on the manager answer; Traefik logs `dial tcp 10.0.1.23:3000: i/o timeout` · **Where:** Dokploy clusters (a manager plus workers), cloud or on-prem · **Level:** [L3 · Senior] · **How common:** Dokploy #592 (36 comments; the security groups were wide open and the thread has no single fix); #3375 (23 comments) traced 502s to a wrong advertised address

**Why it happens:** overlay traffic between nodes is VXLAN on UDP 4789, with gossip on 7946 TCP and UDP and management on 2377 TCP. An open cloud security group isn't enough when the host itself filters (some cloud images ship iptables REJECT rules), when nodes advertise public or NAT addresses, when the underlay MTU is below 1500 (VPNs, some clouds) so full-size VXLAN packets drop, or on VMware, where NSX also uses UDP 4789.

**Diagnose:**

```bash
docker node inspect node-2 --format '{{.Status.Addr}}'
sudo tcpdump -ni ens18 -c 5 udp port 4789          # on node-2, while you curl a worker replica
sudo iptables -S INPUT | tail -2
```

```text
203.0.113.21
0 packets captured
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

**What the output tells you:** node-2 advertises a public address, no VXLAN packet arrives, and the host's own iptables rejects everything except SSH: the overlay never had a chance.

**Fix:**

```bash
# On every node: swarm ports from the other nodes' PRIVATE addresses only
for p in 2377/tcp 7946/tcp 7946/udp 4789/udp; do sudo ufw allow from 10.0.0.0/24 to any port ${p%/*} proto ${p#*/}; done
# Cloud images with a REJECT rule: put ACCEPTs before it (or remove it) and persist the change
# Re-join the worker advertising its private address
docker swarm leave                                   # on node-2
docker node rm OLD_NODE_ID                           # on the manager, once the old entry shows Down
docker swarm join --advertise-addr 10.0.0.21 --token SWMTKN-WORKER-TOKEN 10.0.0.11:2377   # on node-2
```

Underlay MTU below 1500: overlays need `--opt com.docker.network.driver.mtu=1400`, which for dokploy-network means a planned rebuild. VMware NSX on 4789: choose another port with `docker swarm init --data-path-port 4790`, which is only possible at swarm creation.

**Why this fix works:** with the ports open between private addresses and the right advertise address, VXLAN packets reach the worker and the replies come back; a smaller overlay MTU keeps encapsulated packets under the underlay's limit.

**Prevent it:** a multi-node checklist (ports, advertise address, MTU, persistent firewall rules) and a probe that reaches every replica.

**Next step:** [Docker: overlay networks and the routing mesh](30-learn-docker.md) · [Network speed](24-playbook-network-speed.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Docker Overlay Network) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Dokploy #592](https://github.com/Dokploy/dokploy/issues/592) · [Dokploy #3375](https://github.com/Dokploy/dokploy/issues/3375) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+overlay+worker+timeout+4789) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+overlay+network+worker+node+timeout&restrict_sr=1)

### 12.3 Logs and graphs empty on other nodes

> **Seen as:** the Logs tab spins or stays empty and monitoring graphs go blank after an app moves to a worker; logs from a remote server fail with SSL handshake errors · **Where:** Dokploy clusters and remote servers · **Level:** [L2 · Mid-level] · **How common:** a dedicated Dokploy troubleshooting page, "Logs & Monitoring"

**Why it happens:** per Dokploy's docs, the UI reads logs and metrics from the node it runs on, so apps placed on worker nodes don't show up. Newer releases are closing parts of this gap (v0.30.0 lists stack containers on worker nodes), so check the release notes of your version before assuming either way. Remote servers that are slow, overloaded or out of disk fail to answer the panel's log requests.

**Diagnose:**

```bash
docker service ps SERVICE --filter desired-state=running --format '{{.Node}} {{.CurrentState}}'
docker service logs --tail 1 SERVICE                 # from a manager: works for tasks on any node
ssh ops@192.0.2.20 'df -h /var/lib/docker | tail -1; uptime'
```

```text
node-2 Running 3 hours ago
shop-web.1.q8r2...@node-2    | GET /healthz 200 2ms
/dev/sdb1       98G   96G  2.0G  98% /var/lib/docker
 10:52:13 up 41 days,  2:13,  1 user,  load average: 7.81, 7.42, 7.10
```

**What the output tells you:** the app runs on node-2, so the UI can't show it, but `docker service logs` from the manager can; the remote server is nearly full and overloaded, the two causes the docs name.

**Fix:**

```bash
docker service logs -f --since 10m SERVICE           # cluster: read logs from a manager
# Centralise logs and metrics: Loki + Alloy (or Wazuh), Prometheus with node_exporter and cAdvisor
# Remote server: free disk (entry 11.1), add CPU and RAM headroom, check panel-to-server connectivity and TLS
```

**Why this fix works:** service logs on a manager aggregate all tasks through the swarm, and a central logs and metrics stack doesn't care which node runs what.

**Prevent it:** treat the panel's log view as a convenience; on multi-node setups your real observability is Prometheus and Loki.

**Next step:** [Performance & observability](32-learn-performance-observability.md) · [Logs & journal](06-logs-journal.md) · KodeKloud: *Grafana Loki* · [Dokploy logs & monitoring troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/logs-monitoring)

**Community threads:** [Dokploy docs: Logs & Monitoring](https://docs.dokploy.com/docs/core/troubleshooting/logs-monitoring) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+service+logs+worker+node) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+logs+not+showing+remote+server&restrict_sr=1)

## 13. Upgrades and security

### 13.1 Panel stuck after an update

> **Seen as:** dokploy never becomes healthy after an update, logging `password authentication failed for user "dokploy"`, `ELIFECYCLE Command failed`, `JavaScript heap out of memory` or `canceling authentication due to timeout` · **Where:** updates from the UI or the script, especially across several minor versions · **Level:** [L3 · Senior] · **How common:** Dokploy #4002 (44 comments, v0.25 to v0.28.6), #3532 "Dokploy is not updating" (28 comments), #3053 (22 comments)

**Why it happens:** in #4002 the comments found several causes stacked on top of each other: a security script changed the Docker secret but not the Postgres user's password; broken notification rows crashed start-up; start-up jobs loaded every backup entry into memory, past Node's default heap; and fast restart loops piled up Postgres authentication timeouts. Big version jumps run many migrations at once.

**Diagnose:**

```bash
docker service ps dokploy --format '{{.CurrentState}} {{.Error}}' | head -2
docker service logs dokploy --since 15m 2>&1 | grep -iE 'password|heap|ELIFECYCLE' | tail -3
docker exec $(docker ps -q -f name=dokploy-postgres) psql -U dokploy -d dokploy -tAc 'SELECT 1;'
```

```text
Starting 4 seconds ago
error: password authentication failed for user "dokploy"
1
```

**What the output tells you:** Postgres itself works over its local socket, but the password dokploy reads from the secret no longer matches the database user: the mismatch from #4002.

**Fix:** take a panel backup or VM snapshot first, then follow what recovered installations in #4002:

```bash
PW=$(docker exec $(docker ps -q -f name=dokploy-postgres) cat /run/secrets/postgres_password)
docker exec -i $(docker ps -q -f name=dokploy-postgres) psql -U dokploy -d dokploy -c "ALTER USER dokploy WITH PASSWORD '$PW';"
docker service update --env-add NODE_OPTIONS=--max-old-space-size=2048 dokploy
docker service scale dokploy=0 dokploy-postgres=0 && sleep 30
docker service scale dokploy-postgres=1 && sleep 20 && docker service scale dokploy=1
```

The same thread also exported and then cleared broken notification rows, and removed a stale DATABASE_URL variable from the service. If nothing works, restore the panel backup on the previous version.

**Why this fix works:** the database accepts the password the app now reads from the secret, enough heap lets the start-up jobs finish, and spacing the restarts lets Postgres clear pending authentication attempts instead of drowning in them.

**Prevent it:** an update policy: panel backup first, a staging instance updated a week earlier, one minor version at a time where possible, release notes and open regressions read, and the previous image tag written down for rollback.

**Next step:** [Senior: architecture & leadership](39-learn-senior-architecture.md) · [Career ladder](40-career-ladder.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance)

**Community threads:** [Dokploy #4002](https://github.com/Dokploy/dokploy/issues/4002) · [#4002 comments (GitHub API)](https://api.github.com/repos/Dokploy/dokploy/issues/4002/comments?per_page=100) · [Dokploy #3532](https://github.com/Dokploy/dokploy/issues/3532) · [Dokploy #3053](https://github.com/Dokploy/dokploy/issues/3053) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+update+broke&restrict_sr=1)

### 13.2 Panel and databases open past UFW

> **Seen as:** no error at all: an outside scan shows 3000/tcp and 5432/tcp open while `ufw status` says deny incoming · **Where:** any Docker host; Dokploy publishes the panel on 3000 and database external ports on all interfaces · **Level:** [L2 · Mid-level] · **How common:** Docker's own docs explain the bypass; "docker bypasses ufw" is one of the most asked Docker security questions; Dokploy #92 "Postgres unencrypted" (30 comments)

**Why it happens:** Docker publishes ports with DNAT rules in its own chains, which run before UFW's INPUT rules, so UFW never sees that traffic. The panel's port 3000 (host mode) and any database external port are therefore open to whoever can reach the server. The panel mounts docker.sock, so getting into it means owning the host.

**Diagnose:**

```bash
nmap -Pn -p 22,80,443,3000,5432 203.0.113.10          # from OUTSIDE your network
sudo ufw status verbose | grep Default
sudo iptables -S DOCKER-USER
```

```text
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
3000/tcp open  ppp
5432/tcp open  postgresql
Default: deny (incoming), allow (outgoing), deny (routed)
-N DOCKER-USER
```

**What the output tells you:** UFW denies by default, yet 3000 and 5432 answer from the internet: both are Docker-published, and DOCKER-USER filters nothing (an empty chain; Docker before 28.2.2 also shows `-A DOCKER-USER -j RETURN`, which means the same).

**Fix:**

```bash
# Panel: once https://dokploy.example.com works, stop publishing 3000
docker service update --publish-rm "published=3000,target=3000,mode=host" dokploy
# Databases: remove the external port; admins use SSH plus a throwaway client on the overlay
ssh -t ops@192.0.2.10 docker run --rm -it --network dokploy-network postgres:16 psql -h shop-db-x1y2z3 -U shop shop
# A port that must stay published: allow known sources only (match the ORIGINAL port, DNAT already ran)
sudo iptables -I DOCKER-USER -p tcp -m conntrack --ctorigdstport 5432 --ctdir ORIGINAL ! -s 198.51.100.0/24 -j DROP
```

Persist DOCKER-USER rules (for example in UFW's after.rules or a small systemd unit), and keep two-factor authentication, one account per admin and one token per pipeline.

**Why this fix works:** unpublishing removes the DNAT rule, so there is nothing to bypass; the throwaway client reaches the database over the overlay through SSH, which is already protected; and DOCKER-USER is the chain Docker guarantees to evaluate before its own rules. Don't set `"iptables": false` in daemon.json: container networking breaks in subtle ways.

**Prevent it:** a weekly outside port scan compared with an allowlist (80 and 443 only), and a Wazuh alert on new listening ports.

**Next step:** [Security & DevSecOps](37-learn-security-devsecops.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · [Who owns this port?](22-playbook-ports-inventory.md) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — System Hardening (UFW Firewall Basics) · [Docker: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

**Community threads:** [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · [Dokploy #92](https://github.com/Dokploy/dokploy/issues/92) · Search: [Server Fault](https://serverfault.com/search?q=docker+bypasses+ufw+published+port) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+ufw+bypass&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises on a lab VM (two VMs for the cluster ones). Snapshot first, break it exactly as described, then fix it using only the entry and write your five-line note.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Open https://VM:3000, then try from outside with the cloud firewall closed | 10 min | 5.1 |
| 2 | Fresher | Deploy traefik/whoami (listens on 80) with the domain's port set to 3000 | 10 min | 6.2 |
| 3 | Junior | Add a domain to a Compose template and don't redeploy | 10 min | 6.1 |
| 4 | Junior | Mount ./data in a Compose Postgres, redeploy, lose the data; redo it with ../files | 20 min | 10.1 |
| 5 | Junior | Fill the disk with old images until a build fails | 20 min | 11.1 |
| 6 | Mid-level | Put a routed Compose service on two networks and catch the intermittent 504 | 20 min | 6.3 |
| 7 | Mid-level | Leave the host without upstream DNS behind a firewall that blocks 8.8.8.8, then build | 20 min | 8.4 |
| 8 | Mid-level | Add a domain before its DNS record exists; read the ACME error and fix it in order | 25 min | 7.1 |
| 9 | Senior | GitLab CI → Harbor (your CA) → Dokploy API on two nodes; remove the CA from node-2 | 45 min | 9.2, 9.3, 9.4 |
| 10 | Senior/Lead | Restore the panel backup onto a fresh VM with a new IP and bring one app back | 60 min | 10.4 |

Quick questions to answer from memory:

1. Which component answers a plain-text 404, and what are the two usual reasons it does?
2. Why does a Compose domain need a redeploy while an application domain doesn't?
3. Why doesn't `ufw deny 3000` protect the panel, and what does?
4. What does `docker service inspect` show when an image is pinned by digest, and why does that matter for :latest?
5. Which three things does a restored panel backup not contain?

---

## Where to go next

- [Traefik deep dive](43-traefik-and-reverse-proxies.md): routers, middlewares, ACME and the access log, which is half of every Dokploy problem.
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md): the GitLab CI → Harbor → Dokploy pipeline end to end, including runners and the private CA.
- [Wazuh & security tools](48-wazuh-and-security-tools.md): agents on your Dokploy hosts, Traefik and Docker logs, alerts on new ports.
- [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md): your own migration, step by step.
- [Site down](25-playbook-site-down.md) and [Docker & K8s incidents](26-playbook-containers-k8s.md): the layer-by-layer method behind every entry here.
- [Docker](30-learn-docker.md) (Swarm for Dokploy) and [Kubernetes (CKA)](31-learn-kubernetes.md): the platforms underneath, and the one you may grow into.
- [Career ladder](40-career-ladder.md): turn the Self-check and a DR drill into evidence of senior-level work.
- Official docs: [Dokploy](https://docs.dokploy.com/docs/core) · [Coolify](https://coolify.io/docs) · [CapRover](https://caprover.com/docs) · [Traefik](https://doc.traefik.io/traefik/) · [Docker](https://docs.docker.com/).
