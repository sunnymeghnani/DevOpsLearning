# 21 — Case Study: Apache Holds 443, Deploy Dokploy & Docker

This is your real incident, written as a runbook you could follow at work tomorrow. A client
wants a new application deployed with Dokploy on a server where Apache already serves several
sites on ports 80 and 443. Dokploy brings Traefik, which needs 80 and 443, and the Dokploy UI
needs 3000. Two programs cannot own the same port, so something has to move.

The module covers the whole job in order: inventory every listener and vhost, prove which apps
are still used, choose an architecture, prepare backups and a change request, move Apache to an
internal port, install Dokploy, route the old sites through Traefik, cut over with a few minutes
of downtime, verify everything, and roll back if something goes wrong.

Every step uses the same format: **Goal**, the commands, a sample output, **What it means**,
**Why this step (now)** and **Next step**. Run the commands on the target server, not on your
laptop. The outputs are illustrative samples from Ubuntu 24.04 (RHEL/Rocky differences are noted)
and use documentation addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and example.com
names. UPPERCASE words such as HOST, PORT, CONTAINER and UNIT are placeholders.

**Who this is for, from fresher to senior.** One real incident touches every stage of the
[career ladder](40-career-ladder.md), so every section below names its level right after its study
path. Read the module the way your stage needs:

| Stage | Level | What to take from this module | Start with |
|---|---|---|---|
| Fresher | [L0 · Fresher] | the story, the before/after diagrams, and Phase 1's read-only commands run on a lab VM | Sections 1–2 |
| Junior | [L1 · Junior] | Phases 1–2 on your own: every port mapped to a process, unit, config file and log | Sections 2, 3, 11 |
| Mid-level | [L2 · Mid] | bind addresses, Host/SNI routing, forwarded headers, the layer walk when a route fails | Sections 6, 8, 11, 12 |
| Senior | [L3 · Senior] | the architecture decision, Dokploy, Traefik routes, a short rehearsed window | Sections 4, 5, 7, 8, 9 |
| Senior/Lead | [L4 · Lead] | change request, rollback trigger, verification matrix, postmortem | Sections 5, 9, 10, 13 |

**How this relates to your real fix.** At work you solved this incident by moving Apache to ports
81 and 444. [Deployment patterns](35-deployment-patterns.md) analyses that fix and shows how to
finish it with Traefik routing. This module is the planned version of the same idea from the start:
Apache moves to an internal port that only Traefik can reach, so only Traefik is exposed on the
public ports.

Each section starts with a 📚 study path in the order to use it: the KodeKloud lesson first for a
new topic, a handbook note first for a quick refresher, then an optional video and a practice task.
The module ends with a self-check and timed exit tasks per level (Section 13).

---

## 1. The situation and the goal

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server: Apache Web Server, then IPs and Ports ([course](https://kodekloud.com/courses/devops-pre-requisite-course), [Apache lesson notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page), [IPs and Ports notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 2) Note: [Learn: web servers and proxies](29-learn-webservers-proxies.md) · 3) Video: *Traefik v3.3 - Secure Everything! Complete Tutorial* (Jim's Garage, 32 min, [YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 4) Practice: KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu): install Apache with two vhosts on 443, then replay this case.

**Level:** [L0 · Fresher] to [L4 · Lead]. Everyone reads this section; it is the map for the rest of
the module.

### The story

Friday afternoon, a ticket: "Deploy our new portal at app.example.com on web01. We use Dokploy
for our other projects, please use it here too." You SSH in, run the Dokploy installer, and get:

```
Error: something is already running on port 80
```

You look around and find Apache, installed years ago by someone who has left, serving three or
four sites. Nobody has a list of them. You don't know which ones are still used, where their logs
are, which certificates they use, or what breaks if Apache stops. You also find a small Node.js
API listening on 127.0.0.1:3000, the third port Dokploy needs.

The panic move is `systemctl stop apache2` and running the installer again. That would take
every existing site down, possibly for hours, while you work out how to bring them back behind
Traefik. This module is the calm version.

### Constraints and success criteria

| Constraint | What it means for the plan |
|---|---|
| Apache serves 3–4 sites on 80 and 443 | They must keep working, at the same URLs, with valid certificates |
| Dokploy needs 80, 443 and 3000, free on every address | The installer checks with `ss -tulnp` and refuses to run otherwise |
| Minimal downtime | Do everything possible before the window; the window only flips ports |
| Same server, same IP | DNS for existing names does not change, so no TTL wait |
| Unknown ownership | Nothing is retired until there is evidence and an owner's OK |
| Reversible | Every change has a tested rollback written down before you start |

The job is done when: every kept site answers through Traefik with a valid certificate, Apache
logs show real client IPs, app.example.com runs in Dokploy with HTTPS, port 3000 is no longer
reachable from outside, the retired sites are documented, and the runbook is in Git.

### Before: Apache owns the front door

```
                      clients (Internet / LAN)
                                |
        DNS: shop, www.shop, api, app (new) -> 192.0.2.10
                                |
 +------------------------------v---------------------------------+
 | web01  192.0.2.10  Ubuntu 24.04                                |
 |                                                                |
 |  apache2 (apache2.service)   *:80   *:443                      |
 |    |- shop.example.com      -> PHP-FPM 8.3 (unix socket)       |
 |    |- api.example.com       -> http://127.0.0.1:3000 (Node)    |
 |    |- docs.example.com      -> /var/www/docs (static)          |
 |    `- intranet.example.com  -> /var/www/intranet (:80 only)    |
 |                                                                |
 |  node   (api-node.service)   127.0.0.1:3000   <- Dokploy UI    |
 |  mysqld (mysql.service)      127.0.0.1:3306      needs 3000 too |
 +----------------------------------------------------------------+
   New: app.example.com via Dokploy -> needs :80 :443 :3000, all taken
```

### After: Traefik owns the front door

```
                      clients (Internet / LAN)
                                |  :80 / :443
 +------------------------------v---------------------------------+
 | web01  192.0.2.10                                              |
 |                                                                |
 |  dokploy-traefik (container, Traefik v3)  publishes 80, 443    |
 |    |- Host(app.example.com)     -> client app (Swarm service)  |
 |    |- Host(dokploy.example.com) -> dokploy:3000                |
 |    `- Host(shop|www.shop|api)   -> http://192.0.2.10:8081      |
 |                                      (file provider route)     |
 |  apache2  192.0.2.10:8081  plain HTTP, firewalled to Docker    |
 |    |- shop.example.com  -> PHP-FPM 8.3                         |
 |    `- api.example.com   -> http://127.0.0.1:3001 (Node moved)  |
 |                                                                |
 |  dokploy UI :3000 -> closed once dokploy.example.com works     |
 +----------------------------------------------------------------+
   Retired: docs.example.com (DNS points elsewhere)
            intranet.example.com (no users in 14 days, owner agreed)
```

Traefik terminates TLS for every name and forwards plain HTTP to Apache on an internal port.
Apache keeps doing what it is good at (PHP, .htaccess, existing vhosts) without owning the
public ports. Later, one app at a time moves into a container and Apache shrinks to nothing.

### The method in eleven moves

1. **Inventory**: every listener, every process, every vhost, every backend, every certificate.
2. **Usage evidence**: logs tell you which sites are alive, who uses them, how much.
3. **Decide**: keep, migrate or retire each site, and pick the architecture.
4. **Prepare**: backups, change request, pre-flight checks, firewall plan, rehearsal.
5. **Move Apache**: add an internal port first, prove it, then remove 80/443.
6. **Deploy**: install Dokploy (Docker, Swarm, Traefik), deploy the client app.
7. **Route**: teach Traefik about the old sites (file provider), with certificates.
8. **Cut over**: the short window where the ports change owner.
9. **Verify**: a matrix per site (status, certificate, client IP, logs, app health).
10. **Rollback plan**: written, rehearsed, with exact commands.
11. **Document**: runbook, 5-line incident note, postmortem if it hurt.

The order matters. Each move produces the evidence the next one needs. Skipping move 2 is how
people delete a site that a partner calls 18,000 times a day.

### Names and addresses used in this runbook

| Item | Value in this runbook | Replace with |
|---|---|---|
| Server | web01, 192.0.2.10 on ens18 | your host and interface |
| Admin network | 198.51.100.0/24 | where your SSH/admin clients sit |
| Apache internal listener | 192.0.2.10:8081 | any free port; 8081 avoids the Traefik dashboard's 8080 |
| docker_gwbridge subnet | 172.18.0.0/16, gateway 172.18.0.1 | check with `docker network inspect docker_gwbridge` |
| Legacy sites | shop (WordPress), api (Node), docs (static), intranet (old PHP) | your vhosts |
| New app | app.example.com, image harbor.example.com/client/app:1.4.2, port 8000 | the client's app |
| Dokploy UI name | dokploy.example.com | your admin name |

### The short version

When you have done this once, this is the skeleton. Every line is explained in the phases below.

```bash
# Phase 1-2: inventory and evidence
sudo ss -ltnup                                   # every listener + process
sudo apache2ctl -S                               # every vhost, file and line
sudo grep -RniE 'ServerName|ServerAlias|ProxyPass|SetHandler|DocumentRoot|CustomLog' /etc/apache2/sites-enabled/
ls -lt --time-style=long-iso /var/log/apache2/ | head -20
# Phase 4: backup
sudo tar -czpf /root/apache-$(date +%F).tgz -C / etc/apache2 etc/letsencrypt var/www
# Phase 5: Apache on an internal port (add first, remove 80/443 later)
sudoedit /etc/apache2/ports.conf                 # add: Listen 192.0.2.10:8081
sudo a2enmod remoteip && sudo a2enconf remoteip  # + internal vhosts written in Steps 30-31:
sudo a2ensite 000-internal-default shop.example.com-internal api.example.com-internal
sudo apache2ctl configtest && sudo systemctl reload apache2
curl -sI -H 'Host: shop.example.com' http://192.0.2.10:8081/
# Phase 6-8: window
sudoedit /etc/apache2/ports.conf                 # remove Listen 80 / 443 (and a2dissite the public vhosts, Step 36)
sudo apache2ctl configtest && sudo systemctl reload apache2
sudo ss -tulnp | grep -E ':(80|443|3000) '       # must print nothing
curl -fsSL https://dokploy.com/install.sh -o ~/case-web01/dokploy-install.sh && sudo ADVERTISE_ADDR=192.0.2.10 bash ~/case-web01/dokploy-install.sh
sudo install -m 600 legacy-apache.yml /etc/dokploy/traefik/legacy-apache.yml.tmp \
  && sudo mv /etc/dokploy/traefik/legacy-apache.yml.tmp /etc/dokploy/traefik/dynamic/legacy-apache.yml
curl -sI --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/
```

---

## 2. Phase 1 — Inventory what is running

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Start, Stop, and Check Status of Network Services ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)), then Operations Deployment: Diagnose and Manage Processes ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page); [course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: [Who owns this port?](22-playbook-ports-inventory.md) and [Processes](05-processes.md) · 3) Video: *Linux for Beginners: systemd start/stop services & journalctl* (Sanjeev Thiyagarajan, 18 min, [YouTube](https://www.youtube.com/watch?v=jZfNVROoF74)) · 4) Practice: run Steps 1–11 read-only on the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) with Apache installed, then try the free [Linux Challenges](https://kodekloud.com/courses/linux-challenges).

**Level:** [L1 · Junior]. This phase is the L1 exit test: given a port, name the process, the unit,
the config file and the log command. Every command here is read-only, so a fresher can run them too.

Goal of the phase: a complete, written picture of what this server does, before you change
anything. Do not trust memory, wikis or the client's description; trust the kernel (which sockets
exist), systemd (which units own them) and Apache's own parser (which vhosts are active). For the
general "who owns this port" method on any service, see
[Who owns this port?](22-playbook-ports-inventory.md).

Start a notes file now and paste every output into it. That file becomes your inventory, your
change request evidence and half of your runbook.

```bash
# keep a timestamped record of everything you look at
mkdir -p ~/case-web01 && cd ~/case-web01
script -q -a inventory-$(date +%F).log     # records the whole terminal session; 'exit' to stop
```

### Step 1 — List every listening socket

**Goal:** see every TCP and UDP port this host listens on, and which process owns each.

```bash
sudo ss -ltnup          # -l listening, -t TCP, -u UDP, -n numeric, -p process (needs root)
# legacy equivalent if ss is missing (net-tools is not installed by default on 22.04+):
sudo netstat -tulpn
```

```
Netid State  Recv-Q Send-Q   Local Address:Port   Peer Address:Port Process
udp   UNCONN 0      0           127.0.0.54:53          0.0.0.0:*     users:(("systemd-resolve",pid=612,fd=16))
udp   UNCONN 0      0        127.0.0.53%lo:53          0.0.0.0:*     users:(("systemd-resolve",pid=612,fd=14))
tcp   LISTEN 0      4096     127.0.0.53%lo:53          0.0.0.0:*     users:(("systemd-resolve",pid=612,fd=15))
tcp   LISTEN 0      4096        127.0.0.54:53          0.0.0.0:*     users:(("systemd-resolve",pid=612,fd=17))
tcp   LISTEN 0      4096           0.0.0.0:22          0.0.0.0:*     users:(("sshd",pid=1021,fd=3),("systemd",pid=1,fd=93))
tcp   LISTEN 0      151          127.0.0.1:3306        0.0.0.0:*     users:(("mysqld",pid=1102,fd=23))
tcp   LISTEN 0      70           127.0.0.1:33060       0.0.0.0:*     users:(("mysqld",pid=1102,fd=21))
tcp   LISTEN 0      511          127.0.0.1:3000        0.0.0.0:*     users:(("node",pid=1377,fd=19))
tcp   LISTEN 0      4096           0.0.0.0:9100        0.0.0.0:*     users:(("node_exporter",pid=988,fd=3))
tcp   LISTEN 0      511                  *:80                *:*     users:(("apache2",pid=2207,fd=4),("apache2",pid=2206,fd=4),("apache2",pid=1234,fd=4))
tcp   LISTEN 0      511                  *:443               *:*     users:(("apache2",pid=2207,fd=6),("apache2",pid=2206,fd=6),("apache2",pid=1234,fd=6))
tcp   LISTEN 0      4096              [::]:22             [::]:*     users:(("sshd",pid=1021,fd=4),("systemd",pid=1,fd=94))
```

**What it means:**

→ `127.0.0.53%lo:53` and `127.0.0.54:53`: systemd-resolved's stub resolver, loopback only. Normal.

→ `0.0.0.0:22` owned by `sshd` and `systemd` pid 1: on Ubuntu 24.04 SSH is socket-activated
(`ssh.socket`), so pid 1 holds the socket too. The same pattern on another port means a systemd
`.socket` unit owns it; `systemctl list-sockets` shows which.

→ `127.0.0.1:3306` mysqld: loopback only, good. A database on 0.0.0.0 would be a finding.

→ `127.0.0.1:3000` node: **the third conflict.** Dokploy's installer checks port 3000 on any
address, including loopback, and the Dokploy service publishes 3000. This app has to move.

→ `*:80` and `*:443` apache2: `*` is a dual-stack wildcard socket (IPv4 and IPv6 at once). Three
PIDs share it: 1234 is the parent (runs as root, opened the socket), 2206/2207 are worker
processes that inherited it. The first PID in the list is not necessarily the parent.

→ Recv-Q/Send-Q on a LISTEN line are the current accept queue and its limit (511 is Apache's
default `ListenBacklog`). A Recv-Q close to Send-Q means the app is not accepting fast enough.

**Why this step (now):** the kernel's socket table is the only source of truth for "who has
port 443". Configs can lie (a file not included, a second Apache instance, a container), but a
socket either exists or it does not. Starting here also catches surprises, like the Node app on
3000, before you plan anything.

**Next step:** if 80/443 belong to `apache2` as here → Step 2 to look closer at the three
ports Dokploy needs. If they belong to `docker-proxy` → a container already publishes them, jump
to Step 9. If they belong to `nginx`, `haproxy` or `caddy`, the method is the same; see
[Who owns this port?](22-playbook-ports-inventory.md) for those configs.

### Step 2 — Zoom in on 80, 443 and 3000

**Goal:** confirm exactly who holds each port Dokploy needs, on every address and protocol.

```bash
# ss filter syntax: the expression must be quoted
sudo ss -ltnup '( sport = :80 or sport = :443 or sport = :3000 )'
# reproduce the Dokploy installer's own check (TCP + UDP, any address)
sudo ss -tulnp | grep -E ':(80|443|3000) '
# same question, different tools (useful when ss output is confusing)
sudo lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(80|443|3000) '
sudo fuser -v 80/tcp 443/tcp 3000/tcp
```

```
$ sudo lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(80|443|3000) '
apache2    1234     root    4u  IPv6  28811      0t0  TCP *:80 (LISTEN)
apache2    1234     root    6u  IPv6  28815      0t0  TCP *:443 (LISTEN)
node       1377  apinode   19u  IPv4  31842      0t0  TCP 127.0.0.1:3000 (LISTEN)
apache2    2206 www-data    4u  IPv6  28811      0t0  TCP *:80 (LISTEN)
apache2    2206 www-data    6u  IPv6  28815      0t0  TCP *:443 (LISTEN)
apache2    2207 www-data    4u  IPv6  28811      0t0  TCP *:80 (LISTEN)
apache2    2207 www-data    6u  IPv6  28815      0t0  TCP *:443 (LISTEN)

$ sudo fuser -v 80/tcp 443/tcp 3000/tcp
                     USER        PID ACCESS COMMAND
80/tcp:              root       1234 F.... apache2
                     www-data   2206 F.... apache2
                     www-data   2207 F.... apache2
443/tcp:             root       1234 F.... apache2
                     www-data   2206 F.... apache2
                     www-data   2207 F.... apache2
3000/tcp:            apinode    1377 F.... node
```

**What it means:**

→ `IPv6 ... *:80`: one IPv6 socket accepting both IPv4 and IPv6 (dual-stack). Moving Apache off
IPv4 alone would not free the port; the socket must go.

→ The same DEVICE number (28811) for 1234 and 2206 proves they share one socket. The `root` PID
is the parent you will reload, never the workers.

→ `F....` in fuser means "open file" (the socket). `fuser -k` would kill them all; do not use it
here (see Step 36 for the safe ways).

→ Nothing on UDP 443 here. If something were (an HTTP/3 server, OpenVPN on 443/udp), the
installer would refuse too, and Traefik publishes 443/udp for HTTP/3.

**Why this step (now):** Step 1 shows everything; this step proves the exact blockers with the
same test the installer uses, so you know the complete list of things that must move: Apache on
80 and 443, Node on 3000.

**Next step:** for each blocking PID → Step 3 to find the systemd unit that starts it (that unit
is what you will reconfigure, not the PID).
If a port is held only by `systemd` (pid 1) → a `.socket` unit owns it: `systemctl list-sockets`,
and plan to stop the socket unit as well as the service.

### Step 3 — Map each PID to its systemd unit

**Goal:** turn PIDs into units, start times, users and command lines.

```bash
systemctl status 1234 --no-pager -n 0        # systemctl accepts a PID and shows its unit
systemctl status 1377 --no-pager -n 0
ps -o pid,ppid,user,lstart,cmd -p 1234,1377   # parent, owner, exact start time, full command
cat /proc/1377/cgroup                         # cgroup path names the unit (or container)
systemctl cat api-node.service                # the unit file + drop-ins: where config comes from
```

```
● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-21 08:14:02 UTC; 1 week 5 days ago
       Docs: https://httpd.apache.org/docs/2.4/
    Process: 1180 ExecStart=/usr/sbin/apachectl start (code=exited, status=0/SUCCESS)
   Main PID: 1234 (apache2)
      Tasks: 55 (limit: 9387)
     Memory: 412.6M (peak: 530.2M)
        CPU: 2h 11min 3.512s
     CGroup: /system.slice/apache2.service
             ├─1234 /usr/sbin/apache2 -k start
             ├─2206 /usr/sbin/apache2 -k start
             └─2207 /usr/sbin/apache2 -k start

    PID    PPID USER     STARTED                  CMD
   1234       1 root     Mon Sep 21 08:14:02 2026 /usr/sbin/apache2 -k start
   1377       1 apinode  Mon Sep 21 08:14:05 2026 /usr/bin/node /opt/api/server.js

0::/system.slice/api-node.service

# /etc/systemd/system/api-node.service
[Unit]
Description=Orders API (Node.js)
After=network.target mysql.service

[Service]
User=apinode
WorkingDirectory=/opt/api
EnvironmentFile=/opt/api/.env
ExecStart=/usr/bin/node /opt/api/server.js
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**What it means:**

→ `Main PID: 1234` + `CGroup: /system.slice/apache2.service`: Apache is managed by systemd as
`apache2.service`, so you control it with `systemctl`, not by hand. On RHEL/Rocky the unit is
`httpd.service` and the binary `/usr/sbin/httpd`.

→ `enabled`: it starts at boot. Remember this when you plan rollback and retirement.

→ PPID 1 and a start time equal to boot: a normal service. A PPID that is a shell, or a start
time from last Tuesday 14:32, would mean someone started it by hand (and it will not survive a
reboot).

→ `/proc/1377/cgroup` = `0::/system.slice/api-node.service`: the unit is `api-node.service`.
If the path were `/system.slice/docker-HEXID.scope`, the process would be inside a container
(go to Step 9). `/user.slice/...` means it was started from someone's login session.

→ `EnvironmentFile=/opt/api/.env`: the port is probably configured there. Check it before you
plan the move (Step 35).

**Why this step (now):** a PID is temporary; the unit is the permanent thing you will edit,
restart, disable or roll back. Knowing the unit also tells you where its logs live
(`journalctl -u UNIT`) and how it starts at boot.

**Next step:** Apache is the big unknown → Step 4 to make Apache itself list its sites. Note
`api-node.service` for Step 7 and Step 35. More on units: [Services & systemd](07-services-systemd.md).
If the cgroup path is `docker-HEXID.scope` → Step 9. If it is under `/user.slice/` → someone started
it by hand: find out who and why before you change anything.

### Step 4 — Dump Apache's vhost map

**Goal:** get Apache's own parsed view of every virtual host, port, name and file.

```bash
sudo apache2ctl -S                      # = apache2ctl -t -D DUMP_VHOSTS -D DUMP_RUN_CFG
sudo apache2ctl -t -D DUMP_VHOSTS       # vhosts only
sudo apache2ctl -M                      # loaded modules (proxy? ssl? php? rewrite?)
apache2 -v                              # version (2.4.58 on 24.04, 2.4.52 on 22.04)
# RHEL/Rocky:
#   sudo httpd -S ; sudo httpd -M ; configs in /etc/httpd/conf/httpd.conf + /etc/httpd/conf.d/*.conf
```

```
AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message
VirtualHost configuration:
*:443                  is a NameVirtualHost
         default server api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 443 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 443 namevhost docs.example.com (/etc/apache2/sites-enabled/docs.example.com-ssl.conf:1)
         port 443 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2)
                 alias www.shop.example.com
*:80                   is a NameVirtualHost
         default server 127.0.1.1 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost 127.0.1.1 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com.conf:1)
         port 80 namevhost docs.example.com (/etc/apache2/sites-enabled/docs.example.com.conf:1)
         port 80 namevhost intranet.example.com (/etc/apache2/sites-enabled/intranet.example.com.conf:1)
         port 80 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com.conf:1)
                 alias www.shop.example.com
ServerRoot: "/etc/apache2"
Main DocumentRoot: "/var/www/html"
Main ErrorLog: "/var/log/apache2/error.log"
Mutex default: dir="/var/run/apache2/" mechanism=default
PidFile: "/var/run/apache2/apache2.pid"
Define: DUMP_VHOSTS
Define: DUMP_RUN_CFG
User: name="www-data" id=33
Group: name="www-data" id=33

$ sudo apache2ctl -M | grep -E 'mpm|ssl|proxy|rewrite|headers|remoteip|status|php'
 headers_module (shared)
 mpm_event_module (shared)
 proxy_module (shared)
 proxy_fcgi_module (shared)
 proxy_http_module (shared)
 proxy_wstunnel_module (shared)
 rewrite_module (shared)
 ssl_module (shared)
 status_module (shared)
```

**What it means:**

→ Four names on 443 and five on 80. intranet.example.com exists only on port 80 (no HTTPS).

→ `default server api.example.com` on 443: any HTTPS request whose SNI/Host matches no vhost
lands on api. The default server is the first vhost loaded for that address:port, and Ubuntu
loads sites-enabled in alphabetical file order, so `api.example.com-le-ssl.conf` wins over docs and
shop. On 80 the default is `000-default.conf` ("It works!" page), which is why it starts with `000-`.

→ Each line gives file and line number: that is your list of files to read in Step 6.

→ `alias www.shop.example.com`: ServerAlias. Aliases are easy to forget when you write
Traefik routes later; copy them now.

→ `mpm_event` + `proxy_fcgi` and no `php8.3_module`: PHP runs as PHP-FPM, a separate service.
`proxy_http` + `proxy_wstunnel`: Apache reverse-proxies something, including websockets.
`remoteip` is not loaded yet; you will need it (Step 31).

→ The AH00558 warning is harmless; it just means no global ServerName.

**Why this step (now):** the files in sites-enabled are not the whole truth (includes,
conf-enabled snippets, `IfModule` blocks that are off). `apache2ctl -S` is Apache's parser telling
you what it actually loaded, with file and line, in seconds.

**Next step:** → Step 5 to list every file Apache reads, because global snippets in conf-enabled
(PHP handler, security headers, redirects) also affect the move.
If `apache2ctl -S` stops with a syntax error → the running Apache was started from an older, valid
config; reload nothing until `apache2ctl configtest` is clean.

### Step 5 — List the config files Apache really loads

**Goal:** know every included file, the listen ports and the enabled sites and snippets.

```bash
sudo apache2ctl -t -D DUMP_INCLUDES                     # every file, in load order
grep -nE '^\s*Listen' /etc/apache2/ports.conf /etc/apache2/sites-enabled/*.conf
ls -l /etc/apache2/sites-enabled/ /etc/apache2/conf-enabled/
find /etc/apache2/sites-enabled -type f                 # real files instead of symlinks = hand edits
```

```
Included configuration files:
  (*) /etc/apache2/apache2.conf
    (146) /etc/apache2/mods-enabled/access_compat.load
    ...
    (150) /etc/apache2/ports.conf
    (222) /etc/apache2/conf-enabled/charset.conf
    (222) /etc/apache2/conf-enabled/other-vhosts-access-log.conf
    (222) /etc/apache2/conf-enabled/php8.3-fpm.conf
    (222) /etc/apache2/conf-enabled/security.conf
    (222) /etc/apache2/conf-enabled/serve-cgi-bin.conf
    (225) /etc/apache2/sites-enabled/000-default.conf
    (225) /etc/apache2/sites-enabled/api.example.com-le-ssl.conf
      (24) /etc/letsencrypt/options-ssl-apache.conf
    ...

/etc/apache2/ports.conf:5:Listen 80
/etc/apache2/ports.conf:8:	Listen 443
/etc/apache2/ports.conf:12:	Listen 443

lrwxrwxrwx 1 root root 35 Mar  3  2024 000-default.conf -> ../sites-available/000-default.conf
lrwxrwxrwx 1 root root 39 Jun 11  2024 api.example.com.conf -> ../sites-available/api.example.com.conf
lrwxrwxrwx 1 root root 46 Jun 11  2024 api.example.com-le-ssl.conf -> ../sites-available/api.example.com-le-ssl.conf
...
lrwxrwxrwx 1 root root 33 Sep 12  2024 php8.3-fpm.conf -> ../conf-available/php8.3-fpm.conf
```

**What it means:**

→ ports.conf has `Listen 80` and `Listen 443` (twice, inside `IfModule ssl_module` and
`IfModule mod_gnutls.c`, Ubuntu's default). This is the file you will edit in Phase 5.

→ No `Listen` inside site files: good. A `Listen` hidden in a vhost file is a classic reason why
"I removed 443 from ports.conf and it still listens".

→ `conf-enabled/php8.3-fpm.conf` sets the PHP handler globally for all vhosts. Any vhost with
PHP files depends on it, including the new internal vhosts you will create.

→ `other-vhosts-access-log.conf`: vhosts without their own CustomLog write to
`/var/log/apache2/other_vhosts_access.log`. You will need that in Step 12.

→ `find -type f` printed nothing: everything in sites-enabled is a symlink, so sites-available
holds the real files. A regular file there means someone edited sites-enabled directly and
`a2dissite` will not behave as you expect.

**Why this step (now):** you are about to change ports. You need every place a port or a global
behaviour is defined, or a forgotten snippet will surprise you during the window.

**Next step:** → Step 6 to read each enabled vhost and extract names, document roots, backends,
logs and certificates.
If a `Listen` line shows up in a site or conf file → note it now, because Step 36 must remove it too
or Apache keeps the port.

### Step 6 — Extract names, docroots and backends

**Goal:** for every vhost, list ServerName/ServerAlias, DocumentRoot, how it serves content
(static, PHP-FPM, reverse proxy, rewrite-proxy) and where it logs.

```bash
sudo grep -RniE '^\s*(<VirtualHost|ServerName|ServerAlias|DocumentRoot|ProxyPass|ProxyPassReverse|RewriteRule|SetHandler|Redirect|Require ip|CustomLog|ErrorLog|SSLCertificate(Key)?File)' \
  /etc/apache2/sites-enabled/ /etc/apache2/conf-enabled/
# one file in full when something is unclear:
sudo cat /etc/apache2/sites-enabled/api.example.com-le-ssl.conf
```

```
sites-enabled/shop.example.com-le-ssl.conf:2:<VirtualHost *:443>
sites-enabled/shop.example.com-le-ssl.conf:3:    ServerName shop.example.com
sites-enabled/shop.example.com-le-ssl.conf:4:    ServerAlias www.shop.example.com
sites-enabled/shop.example.com-le-ssl.conf:5:    DocumentRoot /var/www/shop
sites-enabled/shop.example.com-le-ssl.conf:9:    ErrorLog ${APACHE_LOG_DIR}/shop_error.log
sites-enabled/shop.example.com-le-ssl.conf:10:   CustomLog ${APACHE_LOG_DIR}/shop_access.log combined
sites-enabled/shop.example.com-le-ssl.conf:14:   SSLCertificateFile /etc/letsencrypt/live/shop.example.com/fullchain.pem
sites-enabled/shop.example.com-le-ssl.conf:15:   SSLCertificateKeyFile /etc/letsencrypt/live/shop.example.com/privkey.pem
sites-enabled/shop.example.com.conf:7:    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
sites-enabled/api.example.com-le-ssl.conf:2:<VirtualHost *:443>
sites-enabled/api.example.com-le-ssl.conf:3:    ServerName api.example.com
sites-enabled/api.example.com-le-ssl.conf:6:    ProxyPass /socket.io/ ws://127.0.0.1:3000/socket.io/
sites-enabled/api.example.com-le-ssl.conf:7:    ProxyPass / http://127.0.0.1:3000/
sites-enabled/api.example.com-le-ssl.conf:8:    ProxyPassReverse / http://127.0.0.1:3000/
sites-enabled/api.example.com-le-ssl.conf:12:   ErrorLog ${APACHE_LOG_DIR}/api_error.log
sites-enabled/api.example.com-le-ssl.conf:13:   CustomLog ${APACHE_LOG_DIR}/api_access.log combined
sites-enabled/docs.example.com-ssl.conf:1:<VirtualHost *:443>
sites-enabled/docs.example.com-ssl.conf:2:    ServerName docs.example.com
sites-enabled/docs.example.com-ssl.conf:3:    DocumentRoot /var/www/docs
sites-enabled/docs.example.com-ssl.conf:6:    SSLCertificateFile /etc/ssl/certs/docs.example.com.crt
sites-enabled/docs.example.com-ssl.conf:7:    SSLCertificateKeyFile /etc/ssl/private/docs.example.com.key
sites-enabled/intranet.example.com.conf:1:<VirtualHost *:80>
sites-enabled/intranet.example.com.conf:2:    ServerName intranet.example.com
sites-enabled/intranet.example.com.conf:3:    DocumentRoot /var/www/intranet
sites-enabled/intranet.example.com.conf:6:        Require ip 192.0.2.0/24 198.51.100.0/24
sites-enabled/intranet.example.com.conf:7:    CustomLog ${APACHE_LOG_DIR}/intranet_access.log combined
conf-enabled/php8.3-fpm.conf:5:        SetHandler "proxy:unix:/run/php/php8.3-fpm.sock|fcgi://localhost"
```

**What it means:** read it as four different kinds of site. (The sample is trimmed and the
`/etc/apache2/` prefix of each path is shortened; your output shows full paths and more lines.)

| Pattern in the vhost | Type | Backend to trace in Step 7 |
|---|---|---|
| DocumentRoot + `.php` files + global `SetHandler proxy:unix:...fpm.sock` | PHP app (shop, intranet) | the php8.3-fpm service and its pool |
| `ProxyPass / http://127.0.0.1:3000/` | reverse proxy (api) | whatever listens on 127.0.0.1:3000 |
| `ProxyPass ... ws://` | websockets through Apache | the same backend; Traefik must pass upgrades |
| DocumentRoot only, no handler | static files (docs) | none, just files |
| `RewriteRule ... [P]` | proxy via mod_rewrite (none here) | the URL inside the rule |

→ The port-80 vhosts of shop and api only redirect to HTTPS (certbot's `RewriteRule ... R=permanent`).
Remember that line: if you copy it into an internal vhost you create a redirect loop (Step 32).

→ `Require ip 192.0.2.0/24 198.51.100.0/24` on intranet: an IP allowlist. Behind Traefik every
request would come from Traefik's IP unless you set up mod_remoteip. Allowlists are where proxy
migrations quietly become security holes or lockouts.

→ Two certificate sources: Let's Encrypt (certbot) for shop and api, a manually installed
certificate for docs.

**Why this step (now):** the migration plan depends on the type of each site. Static and PHP
sites can stay on Apache behind Traefik with no change. Proxied apps could even skip Apache. Sites
with IP allowlists or redirects need edits. You cannot plan without this table.

**Next step:** → Step 7 to follow each backend (PHP-FPM socket, 127.0.0.1:3000) to its process
and unit, so you know everything that moves together.
If a vhost proxies to another host (`ProxyPass` or `[P]` to a remote address) → add that host:port
to the backend list; if it uses `SSLVerifyClient` (client certificates) → mark it as an Option C
candidate for Phase 3.

### Step 7 — Trace each backend to a process and unit

**Goal:** know which services Apache depends on, so you don't break them while moving Apache.

```bash
# TCP backends found in ProxyPass lines
sudo ss -ltnp 'sport = :3000'
# unix-socket backends (PHP-FPM)
sudo ss -xlp | grep -E 'php.*fpm'                 # -x unix sockets, -l listening
ls -l /run/php/
systemctl list-units --type=service --no-pager | grep -Ei 'php|fpm|node|api|tomcat|gunicorn|uwsgi'
grep -HE '^\s*(listen|user|group|pm\.max_children)\s*=' /etc/php/8.3/fpm/pool.d/*.conf   # -H: file name even with one pool
sudo grep -n 'PORT' /opt/api/.env                 # env files with secrets are often mode 600
```

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511        127.0.0.1:3000       0.0.0.0:*     users:(("node",pid=1377,fd=19))

u_str LISTEN 0 511 /run/php/php8.3-fpm.sock 30177 * 0 users:(("php-fpm8.3",pid=1110,fd=8),...)

  api-node.service        loaded active running Orders API (Node.js)
  php8.3-fpm.service      loaded active running The PHP 8.3 FastCGI Process Manager

/etc/php/8.3/fpm/pool.d/www.conf:user = www-data
/etc/php/8.3/fpm/pool.d/www.conf:group = www-data
/etc/php/8.3/fpm/pool.d/www.conf:listen = /run/php/php8.3-fpm.sock
/etc/php/8.3/fpm/pool.d/www.conf:pm.max_children = 20

3:PORT=3000
```

**What it means:**

→ api.example.com = Apache → `api-node.service` on 127.0.0.1:3000, port set in `/opt/api/.env`.
Moving it to 3001 is a one-line change plus an Apache ProxyPass change.

→ shop and intranet = Apache → `php8.3-fpm.service` (one shared pool `www`, running as
www-data). Unix-socket backends are unaffected by port changes. They only need the PHP handler
to stay active for the internal vhosts.

→ No Tomcat, Gunicorn or uWSGI. If you had them, they would appear here with their own ports.

**Why this step (now):** a "site" is Apache plus its backends. If you only move Apache and forget
that the Node app occupies 3000, the Dokploy install fails in the middle of your window.

**Next step:** → Step 8 to check every certificate, because certificates decide how TLS moves to
Traefik and whether anything expires during the migration.
If a ProxyPass target has no listener at all → that site is already broken today: record it as
baseline (Phase 2), not as something the migration broke.

### Step 8 — Check every certificate

**Goal:** for each SSL vhost: subject, SANs, issuer, expiry, and how it is renewed.

```bash
# every distinct certificate file referenced by enabled vhosts
for f in $(sudo grep -RhoP '^\s*SSLCertificateFile\s+\K\S+' /etc/apache2/sites-enabled/ | sort -u); do
  echo "== $f"
  sudo openssl x509 -in "$f" -noout -subject -issuer -enddate -ext subjectAltName
done
sudo certbot certificates            # certbot-managed certs, with days left
# what clients actually receive (SNI matters, -servername is required)
echo | openssl s_client -connect 192.0.2.10:443 -servername api.example.com 2>/dev/null \
  | openssl x509 -noout -subject -enddate
```

```
== /etc/letsencrypt/live/api.example.com/fullchain.pem
subject=CN = api.example.com
issuer=C = US, O = Let's Encrypt, CN = R11
notAfter=Nov 28 06:02:41 2026 GMT
X509v3 Subject Alternative Name:
    DNS:api.example.com
== /etc/letsencrypt/live/shop.example.com/fullchain.pem
subject=CN = shop.example.com
issuer=C = US, O = Let's Encrypt, CN = R10
notAfter=Dec  2 09:14:11 2026 GMT
X509v3 Subject Alternative Name:
    DNS:shop.example.com, DNS:www.shop.example.com
== /etc/ssl/certs/docs.example.com.crt
subject=C = US, O = Example Corp, CN = docs.example.com
issuer=C = US, O = Example Corp, CN = Example Corp Issuing CA 1
notAfter=Nov 14 23:59:59 2026 GMT
X509v3 Subject Alternative Name:
    DNS:docs.example.com

Found the following certs:
  Certificate Name: api.example.com
    Domains: api.example.com
    Expiry Date: 2026-11-28 06:02:41+00:00 (VALID: 55 days)
    Certificate Path: /etc/letsencrypt/live/api.example.com/fullchain.pem
  Certificate Name: shop.example.com
    Domains: shop.example.com www.shop.example.com
    Expiry Date: 2026-12-02 09:14:11+00:00 (VALID: 59 days)
```

**What it means:**

→ shop and api use Let's Encrypt, renewed by certbot. After the move, Traefik can issue its own
Let's Encrypt certificates for these names, and certbot's Apache renewal will stop working
(it needs Apache on port 80). Plan to turn certbot off for these names (Gotchas, section 12).

→ docs uses a certificate from a private corporate CA, expiring 14 Nov. Traefik cannot renew
that one; it would be loaded as a file. But check Step 11 first: this site may not even be live.

→ SANs are the names a certificate is valid for. Every Traefik router you write must be covered
by a certificate with matching SANs, or browsers get a name mismatch.

**Why this step (now):** certificates are the part of a proxy migration that breaks loudly
(browser errors, HSTS lockouts). Knowing expiry dates now tells you whether you can migrate with
the existing files or must issue new ones first. More on reading certificates:
[Web, HTTP & TLS](18-web-http-tls.md).

**Next step:** → Step 9 to see whether Docker is already on this host, since Dokploy will
install or reuse it.
If a certificate expires within 30 days → renew it before the migration, or plan Traefik ACME for
that name first. If its SANs miss a ServerAlias → that alias already shows errors today; record it.

### Step 9 — Check for Docker and existing containers

**Goal:** know whether Docker exists, which containers publish which ports, and whether this
host is already part of a Swarm.

```bash
# docker commands need sudo unless your user is in the docker group (root-equivalent)
command -v docker && docker version --format '{{.Server.Version}}'
systemctl is-active docker
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker ps --filter publish=443               # which container publishes a given port
docker info --format '{{.Swarm.LocalNodeState}}'
dpkg -l | grep -E 'docker|containerd' | awk '{print $2, $3}'
```

```
$ command -v docker
$ systemctl is-active docker
inactive
$ dpkg -l | grep -E 'docker|containerd'
$
```

**What it means:**

→ No Docker at all on this host. The Dokploy installer will install Docker CE (via get.docker.com)
and hold the packages with `apt-mark hold`. You can also pre-install it yourself before the
window to shorten the window (Step 26).

→ If Docker were present: containers with `0.0.0.0:443->443/tcp` in the PORTS column also own
ports; on the host they appear in `ss` as `docker-proxy`, not as the app name.

→ `docker info` reporting `active` for Swarm would be a red flag: the installer runs
`docker swarm leave --force` before `docker swarm init`. On a host that is part of someone
else's Swarm, that silently removes it from that cluster.

**Why this step (now):** Dokploy changes the Docker layer of the host (Swarm mode, overlay
networks, iptables rules). You need to know what was there before so you can tell what Dokploy
added, and so you don't break an existing workload.

**Next step:** → Step 10 to read the firewall, because Docker's port publishing interacts with
UFW in a way that surprises almost everyone. More on Docker inspection:
[Docker reference](14-docker-containers.md).
If Docker is present and Swarm is `active` → stop and talk to whoever owns that Swarm before running
the Dokploy installer, which would leave the cluster.

### Step 10 — Read the firewall state

**Goal:** record which ports are open to whom today, and spot rules that will change meaning.

```bash
sudo ufw status verbose
sudo ufw show added                        # rules as the commands that created them
sudo nft list ruleset | grep -nE 'dport (22|80|443|3000|8081)'
sudo iptables -S | head -40                # Ubuntu 22.04/24.04: iptables-nft, same rules
# RHEL/Rocky: sudo firewall-cmd --list-all
```

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    198.51.100.0/24
Apache Full                ALLOW IN    Anywhere
9100/tcp                   ALLOW IN    198.51.100.5
Apache Full (v6)           ALLOW IN    Anywhere (v6)
```

**What it means:**

→ Default deny incoming, SSH only from the admin network, node_exporter only from the monitoring
host 198.51.100.5. Good hygiene to keep.

→ `Apache Full` is a UFW application profile (80/tcp and 443/tcp). After the move Apache will not
use those ports; Traefik will. You might think you need to "allow 80/443 for Docker", but you
won't: Docker's published ports are DNAT-ed in the nat table and forwarded through Docker's own
FORWARD rules before UFW's input rules see them. **Published container ports bypass UFW.** That
includes Dokploy's port 3000.

→ `deny (routed)`: does not stop Docker either, for the same reason.

**Why this step (now):** the firewall is part of the "before" picture you must restore on
rollback, and it changes meaning when Docker arrives. You plan the new rules in Step 25.

**Next step:** → Step 11 to check DNS for every name, the last piece of "what reaches this host".
Firewall basics: [Network reference](02-network.md).
If UFW is inactive and nftables holds hand-written rules → save `nft list ruleset` in full, because
Docker adds its own chains next to them. On RHEL/Rocky record `firewall-cmd --list-all` instead.

### Step 11 — Resolve every ServerName

**Goal:** find out which names actually point at this server, publicly and internally.

```bash
hostname -I                                       # this host's addresses
for h in shop.example.com www.shop.example.com api.example.com docs.example.com intranet.example.com app.example.com; do
  printf '%-24s A=%-15s AAAA=%-6s getent=%s\n' "$h" \
    "$(dig +short A "$h" | tail -n1)" \
    "$(dig +short AAAA "$h" | tail -n1)" \
    "$(getent ahosts "$h" | awk 'NR==1{print $1}')"
done
dig +short A docs.example.com @PUBLIC_RESOLVER    # what the Internet sees, if your resolver is split-horizon
```

```
192.0.2.10
shop.example.com         A=192.0.2.10      AAAA=       getent=192.0.2.10
www.shop.example.com     A=192.0.2.10      AAAA=       getent=192.0.2.10
api.example.com          A=192.0.2.10      AAAA=       getent=192.0.2.10
docs.example.com         A=203.0.113.80    AAAA=       getent=203.0.113.80
intranet.example.com     A=192.0.2.10      AAAA=       getent=192.0.2.10
app.example.com          A=                AAAA=       getent=
```

(After Dokploy is installed, `hostname -I` will also list Docker's bridge addresses such as
172.17.0.1 and 172.18.0.1. Today it shows only the LAN address.)

**What it means:**

→ shop, www.shop, api and intranet point here. They must keep working.

→ **docs.example.com points to 203.0.113.80, another server.** Nobody reaches this vhost by name.
It is dead config (the site was probably moved). Its expiring certificate is irrelevant. Confirm
with the logs in Phase 2, then retire it.

→ No AAAA records: you only need to test IPv4 paths. If there were AAAA records, every test
in this runbook would need an IPv6 twin (`curl -6`), and Let's Encrypt prefers IPv6 when it exists.

→ app.example.com has no record yet. Ask for it to be created early (Step 26) so DNS is ready
before the window.

→ `getent ahosts` follows /etc/hosts and nsswitch like curl and browsers do; `dig` only asks the
DNS server. If they disagree, a hosts-file entry is involved. See [DNS](08-dns.md).

**Why this step (now):** a vhost only matters if traffic can reach it. DNS is the cheapest way
to eliminate dead sites before you spend time migrating them.

**Next step:** → Phase 2, Step 12: the logs tell you which of the reachable sites are actually
used, and by whom.
If `dig` and `getent` disagree → find the hosts-file or split-horizon entry first
([DNS](08-dns.md)). If a name has an AAAA record → add an IPv6 twin to every test in this runbook.

### Phase 1 wrap-up

```
Who holds 80/443/3000?  (Step 1-2: ss / lsof / fuser)
├── apache2      → unit? (Step 3) → vhosts (Step 4-6) → backends (Step 7)
│                   → certs (Step 8) → DNS per name (Step 11)
├── docker-proxy → docker ps --filter publish=PORT (Step 9)
├── systemd pid1 → a .socket unit → systemctl list-sockets
└── other (node, nginx...) → unit (Step 3) → its config → plan its new port
```

**Fix & verify:** nothing changes in Phase 1. "Verified" means your notes contain: every
listener with its unit, every vhost with names/aliases/docroot/backend/log/cert, every backend
unit, the firewall rules and DNS answers for every name.

**Rollback:** not needed; Phase 1 is read-only.

**Prevent it next time:** keep this inventory in Git next to the server's config, and re-run
it quarterly. A host where nobody can list the sites is the root cause of this whole incident.

---

## 3. Phase 2 — Which apps are used and needed

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment: Locate and Analyze System Log Files ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 2) KodeKloud: *Advanced Bash Scripting* — Streams, awk and sed modules ([course](https://kodekloud.com/courses/advanced-bash-scripting)) · 3) Note: [Logs & Journal](06-logs-journal.md) and Apache's [Log Files docs](https://httpd.apache.org/docs/2.4/logs.html) · 4) Practice: on a playground VM, send curl traffic to two vhosts (some with a monitoring User-Agent) and answer Steps 13–15 from the logs.

**Level:** [L1 · Junior] → [L2 · Mid]. Finding the log files is L1; turning them into evidence
(noise filtered out, baselines recorded, owners named) is L2.

Goal of the phase: evidence for each site. Is anyone using it? Who? How much? Is it healthy
today? Who owns it? Retiring a site is the cheapest migration there is, but only with proof.
Migrating a site that has been dead for a year wastes a day; retiring one a partner calls
18,000 times a day is an incident.

All commands here read logs. Ubuntu rotates Apache logs daily and keeps 14 old copies
(`/etc/logrotate.d/apache2`: `daily`, `rotate 14`, `compress`, `delaycompress`, so `.log.1` stays
plain and `.log.2.gz` to `.log.14.gz` are compressed), so you have about two weeks of history.
`zcat -f` reads both compressed and plain files, and `ls -tr` lists them oldest first so the output
is in time order.

`/var/log/apache2` is mode 750 `root:adm`. The `ls` commands and the `*` globs below run as your
own user, so they work only if your account is in the `adm` group (the first user created by the
Ubuntu installer is; check with `id`). Otherwise run this phase from a root shell (`sudo -i`).

### Step 12 — Find each vhost's log files

**Goal:** know which file every vhost writes its access and error logs to.

```bash
sudo grep -RnE '^\s*(CustomLog|ErrorLog)' /etc/apache2/sites-enabled/ /etc/apache2/conf-enabled/ /etc/apache2/apache2.conf
grep APACHE_LOG_DIR /etc/apache2/envvars          # what ${APACHE_LOG_DIR} expands to
ls -lt --time-style=long-iso /var/log/apache2/ | head -20
```

```
sites-enabled/shop.example.com-le-ssl.conf:9:    ErrorLog ${APACHE_LOG_DIR}/shop_error.log
sites-enabled/shop.example.com-le-ssl.conf:10:   CustomLog ${APACHE_LOG_DIR}/shop_access.log combined
sites-enabled/api.example.com-le-ssl.conf:12:    ErrorLog ${APACHE_LOG_DIR}/api_error.log
sites-enabled/api.example.com-le-ssl.conf:13:    CustomLog ${APACHE_LOG_DIR}/api_access.log combined
sites-enabled/intranet.example.com.conf:7:       CustomLog ${APACHE_LOG_DIR}/intranet_access.log combined
sites-enabled/000-default.conf:21:               CustomLog ${APACHE_LOG_DIR}/access.log combined
conf-enabled/other-vhosts-access-log.conf:2:CustomLog ${APACHE_LOG_DIR}/other_vhosts_access.log vhost_combined
apache2.conf:134:ErrorLog ${APACHE_LOG_DIR}/error.log

export APACHE_LOG_DIR=/var/log/apache2$SUFFIX

-rw-r----- 1 root adm 18234112 2026-10-03 09:41 api_access.log
-rw-r----- 1 root adm  6120448 2026-10-03 09:41 shop_access.log
-rw-r----- 1 root adm    91238 2026-10-03 09:40 intranet_access.log
-rw-r----- 1 root adm    40960 2026-10-03 09:12 error.log
-rw-r----- 1 root adm   912384 2026-10-03 08:55 other_vhosts_access.log
-rw-r----- 1 root adm      913 2026-10-03 06:25 access.log
-rw-r----- 1 root adm     2210 2026-10-02 14:03 api_error.log
```

**What it means:** (sample trimmed, `/etc/apache2/` shortened in the grep paths)

→ shop and api have their own access and error logs.

→ intranet has an access log but no ErrorLog line, so its errors go to the main `error.log`.

→ **docs has no CustomLog**, so its requests land in `other_vhosts_access.log` with the
`vhost_combined` format (first field is `vhost:port`).

→ The modification times show every log was written in the last hour, including intranet. A
recent mtime only proves *something* made a request. Monitoring checks do that too, which is
why Step 13 filters them out.

**Why this step (now):** every later question (alive? who? how much? healthy?) is answered
from these files. Finding them first avoids the classic mistake of grepping `access.log` and
concluding a site is dead because it logs somewhere else. Log locations in general:
[Logs & Journal](06-logs-journal.md).

**Next step:** → Step 13 to find the last request from a real user for each site.
If a vhost logs to a pipe (`CustomLog "|..."`) or to syslog → follow that program to the real file
before Step 13.

### Step 13 — Find the last real request per vhost

**Goal:** the timestamp, client and URL of the most recent request that was not a monitor,
crawler or scanner.

```bash
NOISE='zabbix|uptimerobot|nagios|check_http|kube-probe|bot|crawl|spider|zgrab|masscan'
for v in shop api intranet; do
  printf '%-9s ' "$v"
  for f in $(ls -tr /var/log/apache2/${v}_access.log*); do sudo zcat -f "$f"; done \
    | grep -viE "$NOISE" | tail -n1 | awk '{print $4, $1, $7}'
  echo
done
# docs logs to other_vhosts_access.log: filter on the first field
for f in $(ls -tr /var/log/apache2/other_vhosts_access.log*); do sudo zcat -f "$f"; done \
  | awk '$1 ~ /^docs\.example\.com:/' | grep -viE "$NOISE" | tail -n1
# how far back does the evidence go?
ls -l --time-style=long-iso /var/log/apache2/intranet_access.log* | head -n2
ls -ltr --time-style=long-iso /var/log/apache2/intranet_access.log* | head -n1
```

```
shop      [03/Oct/2026:09:41:12 203.0.113.77 /product/blue-mug/

api       [03/Oct/2026:09:41:13 203.0.113.45 /v1/orders?since=1759484400

intranet

-rw-r----- 1 root adm 91238 2026-10-03 09:40 /var/log/apache2/intranet_access.log
-rw-r----- 1 root adm  6150 2026-10-02 23:55 /var/log/apache2/intranet_access.log.1
-rw-r----- 1 root adm  1012 2026-09-19 23:55 /var/log/apache2/intranet_access.log.14.gz
```

**What it means:**

→ shop and api: real requests within the last minute. Alive.

→ intranet: after removing monitoring noise, **no real request in the retained logs**. The
oldest file is from 19 Sep, so the honest statement is "no real user in 14 days", not "never
used". A monthly payroll report would not show up in a 14-day window.

→ docs: the filter printed nothing; every request to docs was noise (Step 15 shows what).

**Why this step (now):** "When was this last used by a human?" is the single strongest signal
for retire versus migrate. It is cheap to compute and kills most debates.

**Next step:** → Step 14 for volume per day, which tells you how careful the cutover of each
live site must be.
If the retained logs cover less than one business cycle (month-end jobs, payroll) → keep the site,
give it its own CustomLog, and decide after a full month.

### Step 14 — Count requests per day, rotated logs included

**Goal:** requests per day for each live site, over the whole retained history.

```bash
# per-day counts for one site, oldest first
for f in $(ls -tr /var/log/apache2/shop_access.log*); do sudo zcat -f "$f"; done \
  | awk '{print substr($4, 2, 11)}' | uniq -c | tail -n 7
# summary for all sites: total, real (noise removed), files, real per day
NOISE='zabbix|uptimerobot|nagios|check_http|kube-probe|bot|crawl|spider|zgrab|masscan'
for v in shop api intranet; do
  all=$(for f in $(ls -tr /var/log/apache2/${v}_access.log*); do sudo zcat -f "$f"; done | wc -l)
  real=$(for f in $(ls -tr /var/log/apache2/${v}_access.log*); do sudo zcat -f "$f"; done | grep -viEc "$NOISE")
  n=$(ls /var/log/apache2/${v}_access.log* | wc -l)
  printf '%-9s total=%-7s real=%-7s files=%-3s real/day=%s\n' "$v" "$all" "$real" "$n" "$((real / n))"
done
```

```
   4381 27/Sep/2026
   4102 28/Sep/2026
   4655 29/Sep/2026
   4490 30/Sep/2026
   4721 01/Oct/2026
   4302 02/Oct/2026
   1688 03/Oct/2026

shop      total=63102   real=58840   files=15  real/day=3922
api       total=270466  real=270310  files=15  real/day=18020
intranet  total=4320    real=0       files=15  real/day=0
```

**What it means:**

→ shop: about 4,000 real requests a day, steady. A WordPress shop with customers.

→ api: about 18,000 a day, nearly all real. Something depends on it heavily (Step 15 shows who).

→ intranet: 4,320 requests in 15 files = 288 a day = one every 5 minutes. That rhythm is a
monitoring check, not a person.

→ Today's count is partial (the day is not over); ignore the last line when you compare.

**Why this step (now):** volume tells you the cost of a mistake. A few minutes of downtime on
the api at 18,000 requests a day is about 60 failed calls per 5 minutes, during business hours
more. That number belongs in the change request and decides the window time (when is the
quietest hour? Run the same pipeline with `substr($4, 14, 2)` and `sort | uniq -c` instead of
`uniq -c` to count per hour across all days).

**Next step:** → Step 15 to learn *who* uses each site and *what* they call.
If a site's volume makes even a few minutes of downtime unacceptable → note it for Phase 3, where
Option F (new host, DNS switch) avoids the window.

### Step 15 — Top clients, URLs and status codes

**Goal:** identify the main consumers, the important URLs (including websockets and uploads),
and the baseline error rate.

```bash
LOGS=$(ls -tr /var/log/apache2/api_access.log*)
# top client IPs
for f in $LOGS; do sudo zcat -f "$f"; done | awk '{print $1}' | sort | uniq -c | sort -rn | head -5
# top method + path (query string stripped)
for f in $LOGS; do sudo zcat -f "$f"; done | awk '{split($7, u, "?"); print $6, u[1]}' | sort | uniq -c | sort -rn | head -6
# status code distribution
for f in $LOGS; do sudo zcat -f "$f"; done | awk '{print $9}' | sort | uniq -c | sort -rn
# who still asks for docs.example.com (vhost_combined: $2 = client, $8 = path)
for f in $(ls -tr /var/log/apache2/other_vhosts_access.log*); do sudo zcat -f "$f"; done \
  | awk '$1 ~ /^docs\.example\.com:/ {print $2, $8}' | sort | uniq -c | sort -rn | head -5
```

```
 201882 203.0.113.45
  52004 198.51.100.23
   3311 203.0.113.77
   1904 203.0.113.81
   1120 198.51.100.40

 188201 "POST /v1/orders
  60112 "GET /v1/orders
  14002 "GET /socket.io/
   4120 "GET /v1/health
   1890 "POST /v1/uploads

 262118 200
   6011 201
   1820 401
    311 502
    206 101

   4320 198.51.100.5 /
     12 203.0.113.150 /robots.txt
```

**What it means:**

→ api: 203.0.113.45 sends 75% of the traffic. That is a partner's server, not a browser. A
partner integration means: a named contact, possibly an IP allowlist on their side, and a
strong reason to keep the URL and TLS behaviour identical.

→ `/socket.io/` and status `101` (Switching Protocols): websockets are in use. The new proxy
chain must pass `Upgrade` headers (Traefik does by default; Apache needs `proxy_wstunnel` or
`upgrade=websocket`, which it already has).

→ `POST /v1/uploads`: request bodies of unknown size. Check upload limits along the new chain
(Gotchas, section 12).

→ `311 502`: the api already returns some 502s today. That is your **baseline**. Write it down
now, or after the cutover someone will blame Traefik for errors that existed before.

→ docs: every request in two weeks comes from 198.51.100.5 (the monitoring host, hitting `/`)
and a crawler. No humans. The monitoring check must be removed when docs is retired, or it
will page someone.

**Why this step (now):** clients and URLs turn "the api" into "partner X's order integration
with websockets and uploads". That changes how you test (you need their critical calls in your
verification matrix) and who you notify.

**Next step:** → Step 16 to record the error baseline per site from the error logs.
If a top client is unknown → identify it (reverse DNS, whois for public IPs, the CMDB for internal
ones) before the window, because it must be notified.

### Step 16 — Check error-log health

**Goal:** know which errors exist before you change anything.

```bash
# errors by module:level (Apache 2.4 format: [time] [module:level] [pid] ...)
sudo awk -F'[][]' '{print $4}' /var/log/apache2/shop_error.log | sort | uniq -c | sort -rn | head
# the most frequent Apache error codes across all error logs
sudo grep -ohE 'AH[0-9]{5}' /var/log/apache2/*error.log | sort | uniq -c | sort -rn | head
sudo tail -n 2 /var/log/apache2/api_error.log
```

```
    212 proxy_fcgi:error
     37 ssl:warn
      9 mpm_event:notice

    311 AH01102
    212 AH01071
     37 AH01909

[Fri Oct 02 14:03:17.204551 2026] [proxy_http:error] [pid 2207:tid 140213] (104)Connection reset by peer: [client 203.0.113.45:50122] AH01102: error reading status line from remote server 127.0.0.1:3000
[Fri Oct 02 14:03:17.204611 2026] [proxy:error] [pid 2207:tid 140213] [client 203.0.113.45:50122] AH00898: Error reading from remote server returned by /v1/orders
```

**What it means:**

→ `AH01102 ... Connection reset by peer ... 127.0.0.1:3000`: the Node app sometimes drops
connections. These are the 311 502s from Step 15. It is an application issue that exists today.

→ `AH01071` under `proxy_fcgi:error`: PHP warnings/errors from WordPress passed through PHP-FPM
(`Got error 'PHP message: ...'`). Usually plugin noise; note the count.

→ `AH01909`: "server certificate does NOT include an ID which matches the server name", typical
for a vhost without ServerName or with a mismatched certificate. Harmless today, and it goes away
when Apache no longer does TLS.

**Why this step (now):** a baseline of known errors lets you prove, after the cutover, that you
did not add new ones. Without it, every pre-existing error looks like your fault.

**Next step:** → Step 17 to read systemd's view of Apache: restarts, reloads and startup warnings.
If one error dominates (hundreds per hour) → fix it or open a ticket now; a noisy baseline hides new
errors during the cutover.

### Step 17 — Read Apache's journal

**Goal:** see when Apache was started, reloaded or restarted, and by what.

```bash
journalctl -u apache2 --since '30 days ago' --no-pager | tail -n 8
journalctl -u apache2 --since '30 days ago' --no-pager | grep -c 'Reloaded'
# not -p warning: an app's stdout/stderr lands in the journal at priority "info" by default
journalctl -u php8.3-fpm -u api-node --since '7 days ago' --no-pager | grep -iE 'error|warn' | tail -n 5
```

```
Sep 21 08:14:01 web01 systemd[1]: Starting apache2.service - The Apache HTTP Server...
Sep 21 08:14:02 web01 apachectl[1180]: AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message
Sep 21 08:14:02 web01 systemd[1]: Started apache2.service - The Apache HTTP Server.
Oct 02 00:00:02 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Oct 02 00:00:02 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.
Oct 02 21:47:31 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Oct 02 21:47:31 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.
Oct 03 00:00:01 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...

14
Oct 02 14:03:17 web01 node[1377]: Error: ECONNRESET at TLSSocket.socketOnEnd ...
```

**What it means:**

→ Reloads at 00:00 every day: logrotate's postrotate hook. It will keep reloading Apache after the
move (harmless) and it explains log file boundaries.

→ The reload at 21:47: not logrotate. Something else reloads Apache (Step 19 finds it: a certbot
deploy hook after a renewal attempt).

→ Note what is *not* here: Apache's own request errors go to its error log files, not to the
journal. The journal shows the service lifecycle and startup messages.

**Why this step (now):** anything that reloads or restarts Apache automatically can undo your
change or fail after it (for example certbot trying to reconfigure port 443 vhosts that no
longer exist).

**Next step:** → Step 18 for a live view of current traffic, per vhost.
If the journal shows restarts you did not expect (`Main process exited`, `Failed with result`) →
find their cause first ([Services & systemd](07-services-systemd.md)); do not stack a migration on
an unstable service.

### Step 18 — Take a live view with server-status

**Goal:** see current load, busy workers and which vhosts are being requested right now.

```bash
# Ubuntu enables mod_status with "Require local" in /etc/apache2/mods-enabled/status.conf
curl -s 'http://127.0.0.1/server-status?auto' | grep -E 'ServerVersion|Uptime:|Total Accesses|ReqPerSec|BusyWorkers|IdleWorkers'
# full page as text: current requests with client, vhost and URL
curl -s 'http://127.0.0.1/server-status' | sed 's/<[^>]*>/ /g' | grep -E 'example\.com' | head
# with a text browser installed: sudo apache2ctl fullstatus
```

```
ServerVersion: Apache/2.4.58 (Ubuntu)
ServerUptime: 12 days 1 hour 10 minutes 8 seconds
Uptime: 1041008
Total Accesses: 3184772
ReqPerSec: 3.05934
BusyWorkers: 4
IdleWorkers: 71

  0-0  2207 0/141/9981 _  ... 203.0.113.45  http/1.1  api.example.com:443  POST /v1/orders HTTP/1.1
  1-0  2206 0/96/8710  W  ... 203.0.113.77  http/1.1  shop.example.com:443  GET /cart/ HTTP/1.1
```

**What it means:**

→ ~3 requests per second on average, 4 busy workers of 75: a lightly loaded server. Traefik in
front will add negligible overhead.

→ The per-request lines show vhost and client live, which confirms Step 15 in real time
(ExtendedStatus is on by default whenever mod_status is loaded in 2.4).

→ After the move, `http://127.0.0.1/server-status` will hit Traefik, not Apache. Monitoring that
scrapes server-status must be pointed at `http://192.0.2.10:8081/server-status`.

**Why this step (now):** it shows the pattern you will compare against during the cutover. It
also reveals a dependency (status monitoring) that breaks when the port changes.

**Next step:** → Step 19 to find automation that touches Apache or calls the sites through
localhost.
If server-status returns 403 or 404 → mod_status is off or restricted to other clients; use the log
counts from Step 15 and do not open it to the network for this.

### Step 19 — Find cron jobs, timers and certbot hooks

**Goal:** list everything scheduled that reloads Apache, renews its certificates, or requests
its sites via localhost or a hard-coded port.

```bash
sudo grep -RnE 'apache|apachectl|a2en|httpd|localhost|127\.0\.0\.1|wp-cron|certbot|:80|:443' \
  /etc/crontab /etc/cron.d/ /var/spool/cron/crontabs/ 2>/dev/null
# jobs that name a site, a docroot or an app directory instead of a URL
sudo grep -RnE 'shop|intranet|docs|/var/www|/opt/api' /etc/crontab /etc/cron.d/ /var/spool/cron/crontabs/ 2>/dev/null
systemctl list-timers --all --no-pager | grep -Ei 'certbot|apache|php|logrotate'
sudo ls -l /etc/letsencrypt/renewal-hooks/{pre,deploy,post}/
sudo grep -HE '^(authenticator|installer)' /etc/letsencrypt/renewal/*.conf
```

```
/var/spool/cron/crontabs/www-data:3:*/5 * * * * curl -s -H 'Host: shop.example.com' http://127.0.0.1/wp-cron.php >/dev/null
/etc/cron.d/intranet-report:1:0 6 1 * * root /usr/local/bin/intranet-report.sh

Sat 2026-10-03 21:47:00 UTC 12h  Sat 2026-10-03 09:47:12 UTC 9min ago snap.certbot.renew.timer snap.certbot.renew.service
Sun 2026-10-04 00:00:00 UTC 14h  Sat 2026-10-03 00:00:01 UTC 9h ago   logrotate.timer          logrotate.service

/etc/letsencrypt/renewal-hooks/deploy/:
-rwxr-xr-x 1 root root 54 Jun 11  2024 reload-apache.sh

/etc/letsencrypt/renewal/api.example.com.conf:authenticator = apache
/etc/letsencrypt/renewal/api.example.com.conf:installer = apache
/etc/letsencrypt/renewal/shop.example.com.conf:authenticator = apache
/etc/letsencrypt/renewal/shop.example.com.conf:installer = apache
```

**What it means:**

→ www-data's crontab runs WordPress cron with `curl http://127.0.0.1/` and a Host header. After
the move, 127.0.0.1:80 is Traefik, which answers with a redirect to HTTPS; `curl -s` without `-L`
silently stops there. **WordPress scheduled jobs would stop running and nobody would notice.**
It must be changed to call Apache's internal port (Phase 5 wrap-up).

→ `intranet-report.sh` runs on the 1st of each month at 06:00. The 14-day log window from Step
13 could not see a monthly job. Read the script before you call intranet "unused".

→ certbot (snap) renews twice a day with the **apache** authenticator and installer. Once Apache
no longer listens on 80/443, those renewals fail; `reload-apache.sh` explains the 21:47 reload.

**Why this step (now):** scheduled jobs are the hidden users of a server. They do not appear as
humans in the logs and they break silently after port changes.

**Next step:** → Step 20 to put an owner's name on every site before deciding anything.
Timers and cron: [Services & systemd](07-services-systemd.md).
If a job reloads or reconfigures Apache (certbot's apache installer, a deploy script) → add it to
the follow-ups so it is disabled or changed right after the move.

### Step 20 — Identify the owner of each app

**Goal:** a person or team who can say "keep", "move" or "retire" for every site.

```bash
stat -c '%U:%G %y %n' /var/www/* /opt/api
# run git as the repo owner: as root, git refuses a repo owned by www-data ("dubious ownership")
sudo -u www-data git -C /var/www/shop log -1 --format='%an <%ae> %ad' 2>/dev/null
sudo head -n 5 /etc/apache2/sites-available/*.conf | grep -E '^==>|#'   # header comments
sudo cat /usr/local/bin/intranet-report.sh | head -n 20
last -n 10 ; sudo grep -E 'sudo: .*COMMAND=.*(apache|a2en|certbot|api)' /var/log/auth.log | tail -n 5
```

```
root:root 2023-02-14 09:02:10.418220511 +0000 /var/www/docs
root:root 2022-06-03 10:12:44.902113745 +0000 /var/www/html
www-data:www-data 2024-01-09 16:41:55.120376004 +0000 /var/www/intranet
www-data:www-data 2026-10-01 11:20:44.731902118 +0000 /var/www/shop
apinode:apinode 2026-09-20 18:05:31.006518337 +0000 /opt/api

==> /etc/apache2/sites-available/intranet.example.com.conf <==
# Intranet v1 - HR team (contact: hr-it@example.com) - legacy, replaced by SaaS 2024?
```

**What it means:**

→ shop's files changed two days ago: actively maintained. api deployed on 20 Sep: actively
maintained.

→ docs untouched since February 2023 and DNS points elsewhere: abandoned on this server.

→ intranet: last change January 2024 and a comment naming the HR team and "replaced by SaaS
2024?". That question mark is exactly what you ask the owner, by email, with your evidence.

→ The rest comes from people: the client, the CMDB, old tickets. Write the answer and its
source into the inventory table.

**Why this step (now):** technical evidence says "probably unused"; only an owner can say
"retire it". The email thread is also your protection if someone complains later.

**Next step:** → fill the inventory table below, then decide with the rules that follow it.
If no owner can be found for a site with real traffic → rule 4 below applies: keep it and migrate it
as-is.

### The inventory table

Template (copy into the change request):

| vhost | domains | type | backend | cert expiry | last real hit | req/day | owner | decision |
|---|---|---|---|---|---|---|---|---|
| NAME | ServerName + aliases | static / PHP / proxy / app | socket, port, unit | date + issuer | timestamp | number | team, contact | keep / migrate / retire |

Filled in for web01:

| vhost | domains | type | backend | cert expiry | last real hit | req/day | owner | decision |
|---|---|---|---|---|---|---|---|---|
| shop | shop, www.shop | PHP (WordPress) | php8.3-fpm socket, mysql | 2 Dec 2026, LE | 03 Oct 09:41 | ~3,900 | client web team | keep on Apache behind Traefik; containerize later |
| api | api | proxy + websockets | api-node.service 127.0.0.1:3000 | 28 Nov 2026, LE | 03 Oct 09:41 | ~18,000 | client backend team; partner 203.0.113.45 | keep behind Apache, move Node to 3001 |
| docs | docs | static | files only | 14 Nov 2026, corp CA | none (DNS elsewhere) | 0 real | nobody (moved 2023) | retire; remove monitor check |
| intranet | intranet | PHP (old) | php8.3-fpm socket | none (HTTP) | none in 14 days; monthly job | 0 real | HR IT | retire after owner OK + scream test |
| 000-default | none | static | files only | none | n/a | scanners | ops | replace with an internal default that returns 404 |
| app (new) | app | container | Dokploy app, port 8000 | Traefik LE | new | new | client | deploy in Dokploy |

### Retire, migrate or keep: the rules

Use evidence in this order and stop at the first rule that applies:

1. **DNS does not point here** (and no hosts-file users in the logs) → nothing can reach it →
   retire the config. Archive the docroot.
2. **Real users or machine clients in the logs** (partner IPs, API keys, cron jobs) → keep it
   working. Never retire traffic you do not understand.
3. **Only monitoring, crawlers and scanners for the whole log window, and the owner agrees** →
   retire with a scream test: disable the vhost, keep every file, serve a short "retired on DATE,
   contact ops" page, wait 2 to 4 weeks, then archive.
4. **No owner can be found but there is real traffic** → migrate as-is, keep looking for the owner.
5. **Has data** (database, uploads) → take and test a backup before any retirement.

"Keep" has two flavours. Keep behind Traefik (Apache serves it on the internal port) is fast and
safe today. Containerize into Dokploy (Option E in Phase 3) is the long-term goal, done one app
at a time later.

### Phase 2 wrap-up

```
For each vhost:
DNS points here? ── no ──► retire config (archive files, remove monitors)
  │ yes
real (non-noise) hits in log window? ── yes ──► keep / migrate (note clients, URLs, websockets)
  │ no
scheduled jobs or monthly users? ── yes ──► keep until owner confirms
  │ no
owner agrees? ── yes ──► scream test → retire after 2-4 weeks
  │ no / unknown
  └──► keep, migrate as-is, chase the owner
```

**Fix & verify:** the table is complete, every "retire" has an owner's written OK, and the
baseline numbers (req/day, error rates, 502 count) are recorded.

**Rollback:** nothing changed yet.

**Prevent it next time:** give every vhost its own `CustomLog`, a header comment with the owner
and a ticket link, and a monitoring check that is documented next to it.

---

## 4. Phase 3 — Choose the architecture

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Implement Reverse Proxies and Load Balancers ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)), then *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page); [course](https://kodekloud.com/courses/kubernetes-networking)) · 2) Note: [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md) for sockets and SNI, and the pattern catalogue in [Deployment patterns](35-deployment-patterns.md) · 3) Video: *Is this the BEST Reverse Proxy for Docker? // Traefik Tutorial* (Christian Lempa, 21 min, v2-era syntax, [YouTube](https://www.youtube.com/watch?v=wLrmmh1eI94)) · 4) Practice: on a test VM, start Apache on 443 and then `docker run -p 443:443` to see `address already in use` from both sides.

**Level:** [L3 · Senior]. Choosing an architecture and defending it in writing is senior work; a
mid-level engineer [L2 · Mid] should be able to explain every option and its trade-off.

Goal of the phase: pick how Apache and Traefik share one server, for reasons you can explain in
the change request. First the two facts that constrain every option, then six options, then the
decision for web01.

### Why two processes cannot share 443

A listening TCP socket is identified by protocol + local address + local port. When a program
calls `bind()` on an address:port that another socket already holds, the kernel refuses with
`EADDRINUSE`. A wildcard socket (`0.0.0.0:443`, `[::]:443`, or the dual-stack socket that `ss`
shows as `*:443`) conflicts with every specific address on that port. Two *specific* addresses (`192.0.2.10:443` and
`192.0.2.11:443`) do not conflict.

This is what the conflict looks like from each side:

```
# Apache starting while something else holds 443
(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443
(98)Address already in use: AH00072: make_sock: could not bind to address 0.0.0.0:443
no listening sockets available, shutting down
AH00015: Unable to open logs

# Docker publishing 443 while Apache holds it (Docker 28 wording)
docker: Error response from daemon: failed to set up container networking: driver failed programming
external connectivity on endpoint dokploy-traefik (4f1c...): failed to bind host port for
0.0.0.0:443:172.18.0.3:443/tcp: address already in use
# (Docker 27 and older: "... Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use")

# The Dokploy installer's pre-check
Error: something is already running on port 443
```

**The SO_REUSEPORT caveat:** Linux lets several sockets bind the same address:port if *all* of
them set `SO_REUSEPORT` and run as the same user. The kernel then spreads new connections across
them at random. That is meant for several workers of the *same* server (Nginx `reuseport`), not
for two different servers: Apache and Traefik sharing 443 that way would send each visitor to a
random one of them. It is not a solution here.

So exactly one program owns the public 443. The real question is which one, and how it hands
requests to the others.

### One IP, many sites: SNI and the Host header

One IP address can serve many HTTPS sites because the client names the site twice:

```
client                                    front proxy (owner of 192.0.2.10:443)
  | TCP connect 192.0.2.10:443  ------->  accept
  | TLS ClientHello, SNI=shop.example.com (sent in clear)
  |                             ------->  pick the certificate for shop.example.com
  | <------- certificate + handshake      (passthrough mode: route on SNI here and stop)
  | HTTP request (encrypted)
  |   GET /cart/  Host: shop.example.com  decrypt, match router/vhost on Host
  |                             ------->  forward to the backend for shop
```

Apache already does this with name-based vhosts (Step 4). Traefik does the same with routers:
`Host(...)` for HTTP routing after TLS termination, `HostSNI(...)` for TCP routing without
decrypting. Whatever owns 443 can therefore front every site, as long as it knows the names and
has (or can pass through to) the right certificates.

### Option A — Apache keeps 443 and proxies the new app

Run the client app as a plain Docker container bound to loopback (`-p 127.0.0.1:18000:8000`) and
add one more Apache vhost with `ProxyPass / http://127.0.0.1:18000/` and a certbot certificate.
Full example in Step 45.

| Pros | Cons |
|---|---|
| Fastest: 30 minutes, zero downtime for existing sites | No Dokploy (no UI, no Git deploys, no previews) |
| Nothing existing changes | Every new app means editing Apache by hand |
| Easy rollback: disable one vhost | Apache stays the centre of everything, the opposite of the goal |

**Choose when:** the client needs the app today and Dokploy is optional, or as a temporary step
while the real migration is planned.

### Option B — Traefik owns 80/443, Apache moves behind it

Move Apache to an internal plain-HTTP port (192.0.2.10:8081 here), install Dokploy so its Traefik
takes 80 and 443, and add a Traefik file-provider config that routes the legacy names to Apache.
Traefik terminates TLS for everything.

| Pros | Cons |
|---|---|
| Dokploy works exactly as designed | A few minutes of downtime for legacy sites in the window |
| One place for certificates (Traefik + Let's Encrypt) | Apache sees Traefik's IP: needs mod_remoteip |
| Old sites move into containers one at a time later | Apps must learn they are behind HTTPS (X-Forwarded-Proto) |
| Apache's vhosts and PHP stay as they are | certbot for Apache stops working; renewals move to Traefik |

**Choose when:** you want Dokploy on this server (our case). This is the recommended option.

Your real fix at work, Apache on 81 and 444, is the first half of this option: Apache left 80 and
443, but onto public ports of its own. [Deployment patterns](35-deployment-patterns.md) shows how to
finish it: Traefik routes every legacy name to Apache, and 81/444 are closed from outside.

### Option C — Traefik passes TLS through to Apache

Same as B, but Traefik does not decrypt legacy traffic. A TCP router with `HostSNI(...)` and
`tls.passthrough: true` forwards the raw TLS stream to Apache on 192.0.2.10:8443, where Apache
keeps its SSL vhosts and certificates. Example in Step 50.

| Pros | Cons |
|---|---|
| Apache's certificates and TLS settings stay untouched | Traefik sees no HTTP: no paths, headers or status codes in its logs |
| Useful for client-certificate (mTLS) apps | Apache sees Traefik's IP unless PROXY protocol is set up on both sides |
| | certbot's HTTP-01 on port 80 needs a special route back to Apache |
| | Two TLS stacks and two renewal systems to maintain |

**Choose when:** an app needs its own TLS (client certificates, pinned certs, a compliance
requirement), or as a short bridge if certificate issuance by Traefik is impossible on day one.

### Option D — A second IP address

Give the server a second address (192.0.2.11), bind Apache to `192.0.2.10:443` and Traefik to
`192.0.2.11:443`, and point the new names at the new IP. Specific addresses do not conflict.

```yaml
# /etc/netplan/50-cloud-init.yaml (fragment) — then: sudo netplan try
network:
  version: 2
  ethernets:
    ens18:
      addresses:
        - 192.0.2.10/24
        - 192.0.2.11/24
```

| Pros | Cons |
|---|---|
| Zero downtime, nothing moves | Needs a free IP (and public NAT for it on-prem) |
| Works well with plain Traefik or Nginx | **The Dokploy installer refuses**: its check matches 443 on any address |
| | Dokploy creates its Traefik with wildcard `-p 80:80 -p 443:443` and may recreate it, losing hand edits |

**Choose when:** you run plain Docker/Traefik (not Dokploy) and can get an extra IP.

### Option E — Containerize every app and retire Apache

Rebuild each site as a container managed by Dokploy: WordPress as a Compose app (WordPress +
MariaDB, uploads in a volume), the Node API from a Dockerfile built by GitLab CI and pushed to
Harbor, the static site as an Nginx image. Apache disappears.

| Pros | Cons |
|---|---|
| The clean end state: one platform, Git-driven deploys | Days of work per app (data, uploads, cron, sessions, mail) |
| Each app isolated, versioned, rollback by image tag | Too slow for "deploy the client's app this week" |

**Choose when:** as the follow-up to B, one app at a time. This is literally the L3 exit test of
your learning plan: move one Apache workload into a container behind Dokploy, built by GitLab CI,
pushed to Harbor, with a tested rollback.

### Option F — A new server, then switch DNS

Build a fresh VM with Dokploy, route the legacy names from its Traefik back to the old Apache over
the private network (or migrate them), test with `curl --resolve`, then change DNS records to the
new IP with a low TTL.

| Pros | Cons |
|---|---|
| No port conflict at all, no window on the old host | Needs another VM and DNS changes for every name |
| Rollback = change DNS back | TTL waits; clients with stale caches see the old server for a while |
| Old server stays untouched as a fallback | Partner allowlists or firewall rules tied to the old IP must change |

**Choose when:** a VM is cheap, the old host is fragile or out of date (old Ubuntu), or the
client will not accept any downtime.

### Decision table

| Option | Legacy downtime | Effort | Risk | Gives Dokploy | Best when |
|---|---|---|---|---|---|
| A Apache proxies new app | none | low | low | no | app needed today, Dokploy optional |
| B Traefik front, Apache behind | minutes | medium | medium | yes | Dokploy on this host (recommended) |
| C TLS passthrough to Apache | minutes | medium-high | medium | yes | apps that must keep their own TLS |
| D second IP | none | medium | low | not with the stock installer | plain Traefik/Nginx, spare IP |
| E containerize all | per app | high | spread out | yes | the long-term end state |
| F new server + DNS | none on old host | high | low | yes | VM available, zero-downtime demand |

### The decision for web01

**B now, E over the following weeks.** Reasons to put in the change request:

- The client asked for Dokploy, so A only delays the real work.
- D is blocked by the Dokploy installer and by how Dokploy manages its Traefik container.
- C keeps two TLS stacks and loses client IPs; nothing on web01 needs its own TLS.
- F is attractive, but needs a VM and DNS changes for four names; keep it as the fallback plan if
  the window rehearsal (Step 27) goes badly.
- B's cost is a few minutes of legacy downtime, which the evidence from Phase 2 (quiet hour,
  partner notified) makes acceptable.

Plus the Phase 2 decisions: retire docs, scream-test intranet, move api-node from 3000 to 3001.

### What you actually did: Apache on 81/444

At work you took a shortcut: you changed Apache's `Listen` lines from 80 and 443 to 81 and 444, so
Dokploy's Traefik could start on 80 and 443. That is port shifting, not yet Option B. It freed the
ports in minutes and is easy to undo, but Apache still serves its sites on public ports of its own.
Users reach them only by typing `https://shop.example.com:444/`, and nothing on 80 and 443 answers
for those names yet. Port shifting is a good first move; on its own it is an unfinished migration.

Four things finish it. First, change every VirtualHost, not only `Listen`: a vhost left on `*:443`
no longer receives traffic, and its requests fall through to whichever vhost answers first on 444,
so users see the wrong site or certificate. Second, give each Apache hostname a Traefik route (plain
HTTP to port 81, or TLS passthrough to 444) and test it with `curl --resolve` before DNS or users
depend on it. Third, fix the certificate renewal path: certbot's HTTP-01 check now lands on Traefik,
not Apache, so renewals fail quietly until a certificate expires; let Traefik issue the
certificates, or route the ACME challenge path back to Apache. Fourth, firewall 81 and 444 so that
only Traefik can reach them. [Deployment Patterns](35-deployment-patterns.md) walks through each
step with commands, sample output and a rollback.

### Phase 3 wrap-up

```
Need Dokploy on this host?
├── no  → Option A (Apache proxies the container) — done today
└── yes → spare VM and DNS changes acceptable?
          ├── yes → Option F (new host, DNS switch)
          └── no  → any app that must keep its own TLS?
                    ├── yes → Option C for those names, B for the rest
                    └── no  → Option B, then E app by app
```

**Fix & verify:** the chosen option and the reasons are written into the change request.

**Rollback:** nothing changed yet.

**Prevent it next time:** decide the "front door" of every new server on day one (one reverse
proxy owns 80/443, everything else listens internally) and write it in the server's README.

---

## 5. Phase 4 — Prepare

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil: Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page); [course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 3) Note: [Learn: Git, CI/CD, IaC, SRE](33-learn-cicd-iac-sre.md) and Docker's [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · 4) Practice: write the change request for your own Apache server before reading Step 22, then rehearse it on a VM with a stopwatch.

**Level:** [L3 · Senior] → [L4 · Lead]. Backups and pre-flight checks are L3 routine; a change
request with a rollback trigger is how leads make changes safe for the whole team.

Goal of the phase: by the time the window starts, every risky thing has already been done
once (on staging), every file you might need is backed up, every command is written down, and
the people affected know. The window itself should be boring.

### Step 21 — Take backups you can restore from

**Goal:** a copy of every config, certificate, docroot and database that the change touches,
plus a written "before" picture to compare against after a rollback.

```bash
TS=$(date +%Y%m%d-%H%M); B=/root/backup-web01-$TS; sudo mkdir -p "$B"
# configs: tar always records modes and owners (-p matters on extract, where root applies it anyway);
# symlinks (letsencrypt/live -> archive) are stored as symlinks
sudo tar -czpf "$B/etc-apache2.tgz"     -C / etc/apache2
sudo tar -czpf "$B/etc-letsencrypt.tgz" -C / etc/letsencrypt
sudo tar -czpf "$B/docs-cert.tgz"       -C / etc/ssl/certs/docs.example.com.crt etc/ssl/private/docs.example.com.key
sudo tar -czpf "$B/etc-php.tgz"         -C / etc/php
sudo tar -czpf "$B/misc.tgz"            -C / etc/systemd/system/api-node.service etc/cron.d var/spool/cron/crontabs etc/ufw opt/api/.env
# content and data
sudo tar -czpf "$B/var-www.tgz" -C / var/www
sudo mysqldump --single-transaction --routines --events --all-databases | gzip | sudo tee "$B/mysql-all.sql.gz" >/dev/null
# the "before" picture
sudo ss -ltnup        | sudo tee "$B/listeners.txt" >/dev/null
sudo apache2ctl -S 2>&1 | sudo tee "$B/vhosts.txt" >/dev/null
sudo iptables-save    | sudo tee "$B/iptables.rules" >/dev/null
# prove the archives are readable, record checksums, then copy them OFF the host
sudo tar -tzf "$B/etc-apache2.tgz" | head -n 3
sudo sh -c "cd $B && sha256sum * > SHA256SUMS" && sudo ls -lh "$B"
```

```
etc/apache2/
etc/apache2/sites-available/
etc/apache2/sites-available/api.example.com-le-ssl.conf

total 1.9G
-rw-r--r-- 1 root root 4.0K Oct  3 10:02 docs-cert.tgz
-rw-r--r-- 1 root root  71K Oct  3 10:02 etc-apache2.tgz
-rw-r--r-- 1 root root  39K Oct  3 10:02 etc-letsencrypt.tgz
-rw-r--r-- 1 root root  93K Oct  3 10:02 etc-php.tgz
-rw-r--r-- 1 root root 6.4K Oct  3 10:02 iptables.rules
-rw-r--r-- 1 root root 3.1K Oct  3 10:02 listeners.txt
-rw-r--r-- 1 root root  12K Oct  3 10:02 misc.tgz
-rw-r--r-- 1 root root 211M Oct  3 10:03 mysql-all.sql.gz
-rw-r--r-- 1 root root  800 Oct  3 10:04 SHA256SUMS
-rw-r--r-- 1 root root 1.7G Oct  3 10:04 var-www.tgz
-rw-r--r-- 1 root root 1.9K Oct  3 10:02 vhosts.txt
```

**What it means:**

→ `tar -tzf` listing files = the archive is readable. A backup you never listed is a hope.

→ The backup holds private keys (letsencrypt, docs key) and database dumps: keep the directory
root-only and copy it to your backup server over SSH, not to a shared drive.

→ `listeners.txt` and `vhosts.txt` are what "rolled back successfully" must look like (Step 58).

→ Take this backup twice: **B0** now (the original state) and **B1** just before the window
(after the no-downtime preparation in Phase 5). Rolling back during the window restores B1;
rolling back the whole project restores B0.

**Why this step (now):** every later step edits these files. If the server is a VM, also take a
hypervisor snapshot right before the window; but a snapshot rollback also throws away orders and
uploads written since, so it is for "the host is broken", not for "one vhost is wrong".

**Next step:** → Step 22 to write the change request that this backup supports.
If `tar -tzf` fails or `mysqldump` reports an error → fix it and take the backup again now; never
start a window without a readable backup.

### Step 22 — Write the change request

**Goal:** one document that a reviewer can approve and that you can follow line by line,
in the format GitLab uses for its own production changes (criticality, steps, verification,
rollback). Their public examples are linked from the
[GitLab change management handbook](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/).

```markdown
# CR: web01 — move Apache behind Traefik, install Dokploy, deploy app.example.com

## Summary
Apache (4 vhosts) holds 80/443; Dokploy needs 80/443/3000. Move Apache to 192.0.2.10:8081
behind Dokploy's Traefik (file-provider routes), move api-node 3000 -> 3001, retire docs,
scream-test intranet, deploy app.example.com in Dokploy.

## Criticality
2 of 4 (1 = highest). Customer-facing (shop ~3.9k req/day, api ~18k req/day incl. partner
203.0.113.45). Planned downtime for legacy sites: <= 10 min. Rollback rehearsed on staging.

## Window
Tue 06:00-07:00 UTC (quietest hour from access logs). Partner + client notified on DATE.

## Pre-change checks (all must pass)
- [ ] Backups B0/B1 exist, listed, copied off-host (Step 21)
- [ ] 192.0.2.10:8081 serves shop and api correctly (Step 34)
- [ ] api-node runs on 3001 (Step 35)
- [ ] DNS app/dokploy.example.com -> 192.0.2.10 (Step 26)
- [ ] Images pre-pulled, installer script read and saved (Step 26, 38)
- [ ] legacy-apache.yml reviewed (Step 48)

## Change steps (expected duration)
1. Remove Listen 80/443, disable public vhosts, configtest, reload (2 min)       [downtime starts]
2. Confirm 80/443/3000 free (1 min)
3. Run Dokploy installer with ADVERTISE_ADDR=192.0.2.10 (3 min)
4. Copy legacy-apache.yml into /etc/dokploy/traefik/dynamic/ (1 min)              [downtime ends]
5. Verification matrix (10 min)
6. Create Dokploy admin, set domain, lock port 3000 (10 min)
7. Deploy app.example.com (15 min)

## Post-change verification
Matrix in Step 54: status, certificate, client IP in Apache log, Traefik log, app health.

## Rollback (trigger: any kept site failing > 15 min, or partner calls failing)
Step 56-58: stop dokploy-traefik + scale dokploy to 0, restore B1 Apache config, restart
Apache, verify against listeners.txt / vhosts.txt. Expected 5 min.

## Monitoring during change
tail Apache access logs, docker logs -f dokploy-traefik, partner contact on call.
```

**What it means:** every step has a duration, every check has an owner and a checkbox, and the
rollback has a *trigger* (when you stop trying to fix forward). The trigger is the most
important line: decided calmly in advance, not at 06:40 under stress.

**Why this step (now):** writing the steps exposes gaps (here: "who calls the partner?",
"what if the installer cannot reach Docker Hub?") while there is still time to fix them.

**Next step:** → Step 23 to run the pre-flight checks that the change request lists.
If a reviewer cannot find the rollback trigger or the expected duration in the document → it is not
ready; add them before scheduling.

### Step 23 — Pre-flight: Docker, Swarm and outbound access

**Goal:** prove that the installer will be able to do its job: supported OS, root, Internet
access to Docker's and Dokploy's sources, no existing Swarm, correct time.

```bash
lsb_release -ds ; uname -m
command -v docker && docker info --format '{{.ServerVersion}} swarm={{.Swarm.LocalNodeState}}'
# what the installer downloads: get.docker.com, Docker Hub images, GitHub release lookup
curl -sSI https://get.docker.com | head -n1
curl -sSI https://registry-1.docker.io/v2/ | head -n1
curl -sSI https://github.com/dokploy/dokploy/releases/latest | head -n1
env | grep -i _proxy                     # a corporate proxy must be set for the shell AND dockerd
timedatectl | grep -E 'synchronized|NTP service'
```

```
Ubuntu 24.04.3 LTS
x86_64
HTTP/2 200
HTTP/2 401
HTTP/2 302
System clock synchronized: yes
NTP service: active
```

**What it means:**

→ Ubuntu 24.04 on x86_64: supported by Dokploy (its docs list Ubuntu 18.04 to 24.04, Debian,
Fedora and CentOS) and by Docker.

→ No docker command: the installer will install Docker. Swarm state cannot be active.

→ `200` from get.docker.com, `401` from the registry (reachable; 401 just means "log in for
details"), `302` from GitHub (the releases redirect used for version detection): outbound
access works. A timeout here means a proxy or firewall; fix it before the window.

→ Behind a proxy, the shell needs `https_proxy` for the installer's curl, and dockerd needs its
own proxy settings (a systemd drop-in with `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`), because image
pulls are done by the daemon, not your shell.

→ Clock synchronized: Let's Encrypt and every TLS check depend on it ([Time & NTP](12-time-ntp.md)).

**Why this step (now):** an installer that fails halfway through a window (no Internet, proxy,
Docker Hub rate limit) is the most common way a 10-minute window becomes a 2-hour outage.

**Next step:** → Step 24 for ports, capacity and address-range conflicts.
If any URL times out → fix the proxy or firewall path for both the shell and dockerd before
scheduling the window. If Swarm is `active` → see Step 9.

### Step 24 — Pre-flight: ports, disk, RAM and subnets

**Goal:** confirm capacity and that Docker's default address ranges do not collide with your
network.

```bash
sudo ss -tulnp | grep -E ':(80|443|3000) '     # today: apache2 and node (expected blockers)
df -h / /var/lib
free -h ; nproc
ip -br addr ; ip route
```

```
tcp   LISTEN 0  511   127.0.0.1:3000  0.0.0.0:*  users:(("node",pid=1377,fd=19))
tcp   LISTEN 0  511           *:80          *:*  users:(("apache2",pid=2207,fd=4),...)
tcp   LISTEN 0  511           *:443         *:*  users:(("apache2",pid=2207,fd=6),...)

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   41G   53G  44% /

               total        used        free      shared  buff/cache   available
Mem:           7.7Gi       2.9Gi       1.1Gi       112Mi       3.9Gi       4.8Gi
4

lo               UNKNOWN        127.0.0.1/8 ::1/128
ens18            UP             192.0.2.10/24
default via 192.0.2.1 dev ens18 proto static
10.0.0.0/16 via 192.0.2.1 dev ens18 proto static
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10
```

**What it means:**

→ The blockers are exactly the ones found in Phase 1. Nothing new appeared since.

→ 53 GB free and 4.8 GiB available memory: above Dokploy's documented minimum (2 GB RAM, 30 GB
disk). Builds inside Dokploy (Nixpacks, Dockerfiles) need more; images and build cache grow.

→ **`10.0.0.0/16 via 192.0.2.1`: your company uses 10.0.x.x.** Docker Swarm assigns overlay
networks from 10.0.0.0/8 by default (the `ingress` network is usually 10.0.0.0/24, the next
overlay 10.0.1.0/24). A container on dokploy-network that tries to reach a company server at
10.0.1.20 would send the packet into the overlay instead: a silent black hole. Pick a free
range now and pass it to the installer, which supports it:

```bash
# Example: give Swarm a range nobody uses. Pass it inline on the sudo command line (Step 39):
# sudo resets the environment, so a plain "export" in your shell never reaches the installer.
#   sudo ADVERTISE_ADDR=192.0.2.10 DOCKER_SWARM_INIT_ARGS="--default-addr-pool 10.250.0.0/16 --default-addr-pool-mask-length 24" bash dokploy-install.sh
# and for local bridges (docker0, docker_gwbridge, Compose networks), in /etc/docker/daemon.json:
#   { "default-address-pools": [ { "base": "172.30.0.0/16", "size": 24 } ] }
```

**Why this step (now):** address overlaps are almost impossible to fix after Swarm is
initialized without re-creating networks, and they only show up later as "the app can't reach the
LDAP server". Checking `ip route` takes ten seconds.

**Next step:** → Step 25 to plan the firewall rules for the new layout.
If RAM or disk is below Dokploy's minimum → add capacity first or choose Option F. If no 10.x routes
exist and nothing else uses 10.0.0.0/8 → the default pools are fine and the export is optional.

### Step 25 — Plan the firewall rules

**Goal:** decide, port by port, who may reach what after the change and which mechanism enforces
it, because UFW does not see Docker's published ports.

| Port | Listener after the change | Who should reach it | Enforced by |
|---|---|---|---|
| 22/tcp | sshd | admin network | UFW (unchanged) |
| 80, 443/tcp, 443/udp | dokploy-traefik (published) | everyone | Docker publishes; UFW not involved |
| 3000/tcp | dokploy (published, host mode) | admin network, then nobody | DOCKER-USER chain, later `--publish-rm` (Step 42) |
| 8081/tcp | Apache on 192.0.2.10 | only the Traefik container | UFW: allow in on docker_gwbridge, default deny |
| 8080/tcp | Traefik dashboard, only if you enable it in Dokploy | admin only, better never | DOCKER-USER or keep it off |
| 2377/tcp, 7946/tcp+udp, 4789/udp | dockerd (Swarm) | other Swarm nodes only (none here) | UFW default deny (dockerd is a host process) |

```bash
# can be added now: iptables accepts an interface that does not exist yet
sudo ufw allow in on docker_gwbridge to 192.0.2.10 port 8081 proto tcp comment 'Traefik -> Apache internal'
sudo ufw status numbered | grep 8081
```

```
[ 5] 192.0.2.10 8081/tcp on docker_gwbridge ALLOW IN    Anywhere                   # Traefik -> Apache internal
```

**What it means:**

→ Traffic from the Traefik container to the host's own IP arrives on the `docker_gwbridge`
interface and goes through the host's INPUT chain, where UFW applies. Without this rule, UFW's
default deny drops it and Traefik reports `502 Bad Gateway` / timeouts for every legacy site.

→ The rule is scoped to that interface, so the rest of the LAN still cannot reach 8081.

→ Docker's published ports (80, 443, 3000) skip UFW entirely: the packet is DNAT-ed to the
container and forwarded through Docker's chains. Filtering for them belongs in the `DOCKER-USER`
chain ([Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)).

**Why this step (now):** two firewall mistakes dominate this kind of migration: Traefik blocked
from reaching Apache (looks like a broken backend), and port 3000 open to the Internet (looks fine
until someone else registers as your Dokploy admin). Both are prevented on paper first.

**Next step:** → Step 26 to prepare DNS, Docker and images so the window is short.
If a row of this table cannot be enforced with the tools you have → change the design (for example
bind to loopback) instead of accepting the exposure.

### Step 26 — Prepare names, Docker and images

**Goal:** everything that does not touch ports 80/443 is done before the window.

```bash
# 1. DNS: request A records app.example.com and dokploy.example.com -> 192.0.2.10 (TTL 300), then:
dig +short app.example.com dokploy.example.com
# 2. Read the installer and note the versions it pins
curl -fsSL https://dokploy.com/install.sh -o ~/case-web01/dokploy-install.sh
grep -nE 'DOCKER_VERSION=|traefik:v|postgres:' ~/case-web01/dokploy-install.sh
# 3. Optional: install Docker now with the same pinned version (binds no web ports)
curl -fsSL https://get.docker.com -o ~/case-web01/get-docker.sh
sudo sh ~/case-web01/get-docker.sh --version 28.5.0
sudo apt-mark hold docker-ce docker-ce-cli docker-ce-rootless-extras
# 4. Pre-pull the images the installer will start
sudo docker pull traefik:v3.6.25 && sudo docker pull postgres:16
sudo docker pull dokploy/dokploy:VERSION     # the release tag the installer will detect (see its releases page)
```

```
192.0.2.10
192.0.2.10

4:DOCKER_VERSION="28.5.0"
290:    postgres:16
341:        traefik:v3.6.25
355:    #     traefik:v3.6.25

docker-ce set on hold.
docker-ce-cli set on hold.
docker-ce-rootless-extras set on hold.
v3.6.25: Pulling from library/traefik
Status: Downloaded newer image for traefik:v3.6.25
```

**What it means:**

→ Both new names resolve: Let's Encrypt will be able to validate them right after the window.

→ The versions shown are what the script pinned when this was written; **read your copy**, they
change with every release. Pull the Dokploy image with the tag your installer will use (it
detects the latest release from GitHub unless `DOKPLOY_VERSION` is set).

→ With Docker pre-installed, the installer prints "Docker already installed" and skips that part,
which is the slowest and most network-dependent piece.

→ Installing Docker starts dockerd and creates docker0 (172.17.0.1) and iptables chains. It does
not bind 80/443, so Apache is unaffected.

**Why this step (now):** the window length is what the client experiences as downtime. Moving
downloads and installs out of it turns 10+ minutes into 2 or 3.

**Next step:** → Step 27 to rehearse the whole window and the rollback on a staging VM.
If the new names do not resolve yet → do not schedule the window, because Let's Encrypt will fail
for them. If `docker pull` hits Docker Hub rate limits → `docker login` with an account first.

### Step 27 — Rehearse on a staging VM

**Goal:** run the exact window procedure and the rollback once, with a stopwatch, on a copy.

```bash
# on a fresh Ubuntu 24.04 VM (staging, 192.0.2.20):
sudo apt-get install -y apache2 php8.3-fpm
sudo tar -xzpf etc-apache2.tgz -C /          # web01's Apache config from backup B0
sudo tar -xzpf etc-letsencrypt.tgz -C /      # certificates, so the SSL vhosts load
sudo tar -xzpf docs-cert.tgz -C /            # the docs vhost references this cert too
sudo a2enmod proxy_fcgi proxy_http proxy_wstunnel rewrite headers ssl && sudo apache2ctl configtest
# then follow Phase 5 -> 8 and Section 10 (rollback) exactly, timing each step:
date +%T                                      # before and after each change step
# test from your laptop without touching DNS:
curl -skI --resolve shop.example.com:443:192.0.2.20 https://shop.example.com/
```

```
Syntax OK
06:00:02  step 1 Apache off 80/443
06:01:10  step 3 installer start
06:03:41  step 3 installer done
06:04:05  step 4 legacy routes loaded
06:09:30  verification done
06:12:02  rollback done, Apache back on 80/443
HTTP/2 200
```

**What it means:**

→ The real downtime (step 1 to step 4) was about 4 minutes; the change request says 10. Good margin.

→ Rollback took under 3 minutes and worked. That is what "tested rollback" means.

→ `-k` is fine on staging: public DNS points at web01, so Traefik on the staging VM cannot pass
Let's Encrypt validation and serves its self-signed default certificate for any name not covered
by the file certificates of Step 49. Never use `-k` on production checks.

**Why this step (now):** rehearsal finds the surprises (a missing module, a vhost that depends on
something not in the backup, an installer prompt) on a machine nobody uses.

**Next step:** → Phase 5, Step 28: start moving Apache, beginning with the changes that cause no
downtime.
If the rehearsal overruns the window or the rollback fails → fix the procedure and rehearse again.
If the gap cannot be made short enough → go back to Phase 3 and consider Option F.

### Maintenance window and communication

Pick the quietest hour from Step 14 (count per hour). Tell the client and the partner (203.0.113.45)
the date, the expected impact ("up to 10 minutes of errors on api.example.com"), and who to call.
During the window, keep one terminal tailing the Apache access logs and later the Traefik log; the
first successful partner request after the cutover is your best health check. Afterwards, send a
short "done, verified" note with the verification matrix attached.

### Phase 4 wrap-up

```
Backups B0 listed + off-host?            ── no ──► stop, fix
Change request reviewed, trigger set?    ── no ──► stop, fix
Outbound access / proxy / time OK?       ── no ──► fix proxy for shell AND dockerd
Docker address ranges collide?           ── yes ─► DOCKER_SWARM_INIT_ARGS + daemon.json pools
Firewall plan for 8081 / 3000 written?   ── no ──► Step 25
Rehearsal done, rollback timed?          ── no ──► Step 27
all yes ──► Phase 5
```

**Fix & verify:** every pre-change checkbox in the change request is ticked.

**Rollback:** if you pre-installed Docker and must back out the project entirely, stop it with
`sudo systemctl disable --now docker.socket docker.service` (Apache does not need it); removing
packages can wait.

**Prevent it next time:** keep the change-request template and the pre-flight commands in a
repo, so the next migration starts from them instead of from a blank page.

---

## 6. Phase 5 — Dispatch Apache off 80 and 443

> 📚 **Study path:** 1) Note: [Learn: web servers and proxies](29-learn-webservers-proxies.md) (vhosts, forwarded headers) and [Services & systemd](07-services-systemd.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD: SYSTEMD Tools ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) · 3) Docs: Apache [virtual host documentation](https://httpd.apache.org/docs/2.4/vhosts/) · 4) Practice: on a playground VM, move a two-vhost Apache to an internal port and back, testing with `curl -H 'Host: ...'` after every reload.

**Level:** [L2 · Mid]. Bind addresses, name-based vhosts, forwarded headers and graceful reloads are
the core reverse-proxy skills of L2. The ladder of stop methods at the end matters at every level.

Goal of the phase: Apache keeps serving every kept site, but on an internal port that only
Traefik can reach, and ports 80, 443 and 3000 end up free. Work up the ladder from the least
invasive change to the most, and verify at every rung:

| Rung | Change | Impact | When |
|---|---|---|---|
| 1 | Add an internal listener and internal vhosts next to 80/443 | none | days before |
| 2 | Move the Node app from 3000 to 3001 | seconds on api | before or in the window |
| 3 | Remove `Listen 80/443`, disable the public vhosts, reload | legacy sites down until Traefik routes them | in the window |
| 4 | `systemctl stop` + `disable` (+ `mask`) Apache | everything Apache served is gone | only when retiring Apache |
| 5 | `kill -TERM` on the parent PID | as 4, without systemd's help | only if systemd cannot stop it |
| 6 | `kill -9` | can leave the port held and shared memory dirty | never as a plan |

### Step 28 — Choose Apache's internal bind address

**Goal:** pick an address the Traefik container can reach, that exists at boot, and that you can
firewall.

The key fact: Traefik runs in a container with its own network namespace. Inside it,
`127.0.0.1` is the container itself, not the host. Apache on 127.0.0.1:8081 is unreachable from
Traefik.

| Apache listens on | Traefik can reach it? | Exists when Apache starts at boot? | Exposure | Verdict |
|---|---|---|---|---|
| 127.0.0.1:8081 | no, container loopback is not host loopback | yes | none | does not work |
| 172.17.0.1:8081 (docker0) | yes | only after Docker starts; otherwise Apache fails with "Cannot assign requested address" | host only | works with `After=docker.service`, fragile |
| 172.18.0.1:8081 (docker_gwbridge) | yes | only after Docker and Swarm init | host only | same, more fragile |
| 192.0.2.10:8081 (host LAN IP) | yes, via the container's default route | yes (wait for network-online) | LAN: must firewall | **recommended** |
| 0.0.0.0:8081 | yes | yes | every interface, firewall required | works, widest exposure |
| host.docker.internal | only if the container was started with `--add-host host.docker.internal:host-gateway` | n/a | n/a | Dokploy creates dokploy-traefik itself, so you cannot rely on adding flags; use it in your own Compose apps |

```bash
ip -br -4 addr                         # the address you will bind
systemctl cat apache2 | grep -E '^(After|Wants)='
# after Dokploy is installed, confirm how Traefik leaves its container:
docker network inspect docker_gwbridge --format '{{range .IPAM.Config}}{{.Subnet}} gw={{.Gateway}}{{end}}'
docker run --rm --net container:dokploy-traefik nicolaka/netshoot ip route
```

```
lo               UNKNOWN        127.0.0.1/8
ens18            UP             192.0.2.10/24

After=network.target remote-fs.target nss-lookup.target

172.18.0.0/16 gw=172.18.0.1

default via 172.18.0.1 dev eth1
10.250.1.0/24 dev eth0 proto kernel scope link src 10.250.1.4
172.18.0.0/16 dev eth1 proto kernel scope link src 172.18.0.3
```

**What it means:**

→ The Traefik container has two interfaces: eth0 on the dokploy-network overlay (10.250.1.0/24
with the custom pool from Step 24) and eth1 on docker_gwbridge (172.18.0.3), with the default
route via 172.18.0.1. A packet to 192.0.2.10:8081 leaves through eth1 and arrives at the host on
the docker_gwbridge interface with source 172.18.0.3. That source subnet is what UFW (Step 25) and
mod_remoteip (Step 31) must trust.

→ This holds because the installer starts dokploy-traefik with `--network dokploy-network` only, so
Docker adds docker_gwbridge for its outside traffic. Dokploy may recreate the container later (Gotchas,
section 12) and its network attachments can differ between versions: if `ip route` inside it ever
shows `default via 172.17.0.1` (the default bridge), the traffic arrives on `docker0` from
172.17.0.0/16, and the UFW rule and `RemoteIPInternalProxy` must name that interface and subnet instead.
Re-run the netshoot check after every Dokploy upgrade.

→ `After=network.target` does not guarantee that 192.0.2.10 is configured when Apache starts. Add
a drop-in so Apache waits for the network to be online:

```bash
sudo systemctl edit apache2
# add in the editor:
#   [Unit]
#   Wants=network-online.target
#   After=network-online.target
```

**Why this step (now):** the bind address decides reachability, boot reliability and exposure at
once. Choosing it before writing any config avoids the most common failure of this migration:
Apache on 127.0.0.1 and Traefik answering 502 Bad Gateway for every legacy site.

**Next step:** → Step 29 to add the listener without touching 80/443.
If you must bind a Docker bridge address instead → add `After=docker.service` to the same drop-in
and accept that Apache then depends on Docker at boot.

### Step 29 — Add the internal listener alongside 80 and 443

**Goal:** Apache listens on 192.0.2.10:8081 in addition to its current ports. No downtime.

```bash
sudo cp -a /etc/apache2/ports.conf /etc/apache2/ports.conf.orig
sudoedit /etc/apache2/ports.conf
```

```apache
# /etc/apache2/ports.conf (transition: public ports + internal port)
Listen 80
Listen 192.0.2.10:8081

<IfModule ssl_module>
	Listen 443
</IfModule>

<IfModule mod_gnutls.c>
	Listen 443
</IfModule>
```

```
$ sudo apache2ctl configtest
Syntax OK
```

**What it means:** `Listen 192.0.2.10:8081` binds only that address, so it neither conflicts with
anything nor appears on other interfaces. Do not reload yet: with no vhost for 8081, requests
there would fall through to the main server config. Create the vhosts first (Step 30), define the
log format (Step 31), then reload once (Step 33).

**Why this step (now):** adding before removing is the core of every low-risk migration. The
public sites keep running exactly as before while you build and test the new path next to them.

**Next step:** → Step 30 to create the internal vhosts.
If configtest fails → the message names the file and line; fix it now, while nothing new is live.

### Step 30 — Create the internal vhosts

**Goal:** one plain-HTTP vhost on 192.0.2.10:8081 per kept site, plus a default vhost that
answers 404 for unknown names.

Build each internal vhost from the site's *SSL* vhost (that is where the real content config
lives), and leave out four things: `SSLEngine`/`SSLCertificate*` lines, the
`Include /etc/letsencrypt/options-ssl-apache.conf` line, any HTTP-to-HTTPS redirect, and any
`RequestHeader set X-Forwarded-Proto` (Traefik now sends the real value).

```apache
# /etc/apache2/sites-available/000-internal-default.conf
# First vhost on 192.0.2.10:8081 = default: unknown Host -> 404, never another site.
<VirtualHost 192.0.2.10:8081>
    ServerName internal-default.invalid
    DocumentRoot /var/www/empty
    <Directory /var/www/empty>
        Options -Indexes
        Require all granted
    </Directory>
    # every path answers 404 (an empty directory with -Indexes alone would answer 403 for /)
    Redirect 404 /
    CustomLog ${APACHE_LOG_DIR}/internal_default_access.log proxied
</VirtualHost>
```

```apache
# /etc/apache2/sites-available/shop.example.com-internal.conf
<VirtualHost 192.0.2.10:8081>
    # The https:// scheme makes Apache build its own redirects (e.g. /wp-admin -> /wp-admin/)
    # with https, because clients reach this site through Traefik over HTTPS.
    ServerName https://shop.example.com
    ServerAlias www.shop.example.com
    DocumentRoot /var/www/shop

    <Directory /var/www/shop>
        AllowOverride All
        Require all granted
    </Directory>

    # TLS ended at Traefik: tell PHP the request was HTTPS (see Step 32)
    SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on

    ErrorLog ${APACHE_LOG_DIR}/shop_error.log
    CustomLog ${APACHE_LOG_DIR}/shop_access.log proxied
</VirtualHost>
```

```apache
# /etc/apache2/sites-available/api.example.com-internal.conf
<VirtualHost 192.0.2.10:8081>
    ServerName https://api.example.com
    ProxyPreserveHost On
    ProxyPass        /socket.io/ ws://127.0.0.1:3000/socket.io/
    ProxyPass        /           http://127.0.0.1:3000/
    ProxyPassReverse /           http://127.0.0.1:3000/
    ErrorLog ${APACHE_LOG_DIR}/api_error.log
    CustomLog ${APACHE_LOG_DIR}/api_access.log proxied
</VirtualHost>
```

```apache
# /etc/apache2/sites-available/intranet-retired.conf  (scream test, enabled in the window)
<VirtualHost 192.0.2.10:8081>
    ServerName intranet.example.com
    Redirect gone /
    ErrorDocument 410 "intranet.example.com was retired on 2026-10-06 (CR-1234). Contact ops@example.com."
    CustomLog ${APACHE_LOG_DIR}/intranet_access.log proxied
</VirtualHost>
```

```bash
sudo mkdir -p /var/www/empty
ls /etc/apache2/sites-available/*internal*.conf /etc/apache2/sites-available/intranet-retired.conf
```

```
/etc/apache2/sites-available/000-internal-default.conf
/etc/apache2/sites-available/api.example.com-internal.conf
/etc/apache2/sites-available/intranet-retired.conf
/etc/apache2/sites-available/shop.example.com-internal.conf
```

**What it means:**

→ The internal vhosts write to the *same* log files as today. Two vhosts logging to one file is
normal (certbot's :80 and :443 copies already do it), and history stays in one place.

→ The file name `000-internal-default.conf` sorts first, so it becomes the default for
192.0.2.10:8081. Without it, an unknown Host would be served by shop.

→ The api vhost still points at 3000; Step 35 moves it to 3001 together with the Node app.

→ docs gets no internal vhost: it is retired outright (DNS points elsewhere).

→ Duplicated config drifts. A tidy alternative is to move the shared body of each site into
`/etc/apache2/snippets/shop.conf` and `Include` it from both vhosts until the public one is gone.

**Why this step (now):** the internal vhosts are the "new path". Building them while the old path
still serves users means you can test them for days, not minutes.

**Next step:** → Step 31 to define the `proxied` log format and teach Apache the real client IP.
If a site has extra directives only in its port-80 vhost (old-path redirects, aliases) → copy them
into the internal vhost too, minus the HTTPS redirect.

### Step 31 — Restore real client IPs with mod_remoteip

**Goal:** Apache logs, `Require ip` rules and PHP see the visitor's IP, not Traefik's.

```apache
# /etc/apache2/conf-available/remoteip.conf
# Only requests coming from Traefik's network may set the client IP via X-Forwarded-For.
RemoteIPHeader X-Forwarded-For
RemoteIPInternalProxy 172.18.0.0/16

# %a = client IP after mod_remoteip (in current 2.4 releases %h follows it too while
# HostnameLookups is Off; %{c}a logs the proxy's own address)
LogFormat "%a %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\" proto=%{X-Forwarded-Proto}i" proxied
```

```bash
sudo a2enmod remoteip
sudo a2enconf remoteip
sudo apache2ctl configtest
```

```
Enabling module remoteip.
To activate the new configuration, you need to run:
  systemctl restart apache2
Enabling conf remoteip.
To activate the new configuration, you need to run:
  systemctl reload apache2
Syntax OK
```

**What it means:**

→ `RemoteIPInternalProxy` versus `RemoteIPTrustedProxy`: both say "trust X-Forwarded-For from
this proxy". The difference is what they accept *inside* the header. TrustedProxy ignores
private addresses in it (10/8, 172.16/12, 192.168/16...), so on-prem clients on private ranges
would still show up as the proxy. InternalProxy accepts them. For an on-prem server with internal
users, InternalProxy is the right one.

→ 172.18.0.0/16 is the docker_gwbridge subnet you expect. Confirm it right after the install
(Step 40) and correct this line if Docker chose another range.

→ Never trust X-Forwarded-For from everyone: any client could then claim to be 192.0.2.5 and pass
an IP allowlist. Here only Traefik can reach 8081 (UFW, Step 25), and Traefik replaces
X-Forwarded-For headers from untrusted clients with the real address.

→ a2enmod says "restart"; a graceful reload also loads new modules. A full restart is only
needed for MPM changes.

**Why this step (now):** without it, every request in Apache's logs comes from 172.18.0.3, every
`Require ip` allowlist either blocks everyone or allows everyone, and fail2ban or rate limits
based on Apache logs stop working.

**Next step:** → Step 32 to fix "am I on HTTPS?" for the apps.
If configtest reports `Invalid command 'RemoteIPHeader'` → the module is not enabled yet: `sudo a2enmod remoteip`.

### Step 32 — Make the apps aware of HTTPS

**Goal:** no redirect loops, correct absolute URLs and secure cookies, now that Apache receives
plain HTTP.

The app used to see HTTPS directly. Now it sees HTTP from Traefik plus a header
`X-Forwarded-Proto: https`. Anything that checks "is this HTTPS?" the old way will think it is
not, and may redirect to HTTPS, which arrives as HTTP again: an infinite loop
(`ERR_TOO_MANY_REDIRECTS`).

```bash
# find HTTPS checks in vhosts and .htaccess files that will now always be "off"
sudo grep -RniE 'RewriteCond\s+%\{(HTTPS|SERVER_PORT)\}' /etc/apache2/sites-available/ /var/www/*/.htaccess
sudo grep -nE "HTTPS|FORCE_SSL|X_FORWARDED_PROTO" /var/www/shop/wp-config.php   # often mode 640/600
```

```
/var/www/shop/.htaccess:3:RewriteCond %{HTTPS} off
/var/www/shop/.htaccess:4:RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
82:define('FORCE_SSL_ADMIN', true);
```

**What it means:**

→ `RewriteCond %{HTTPS} off` uses mod_ssl's own variable, which is now always "off". The
`SetEnvIf ... HTTPS=on` from Step 30 sets an *environment variable* for PHP, not this mod_rewrite
variable. This rule would loop forever. Replace it (Traefik already redirects HTTP to HTTPS, so
the rule could also be removed once the public vhosts are gone):

```apache
# /var/www/shop/.htaccess — redirect only when the request is neither direct HTTPS (the public
# :443 vhost, still live until the window) nor forwarded HTTPS (Traefik -> :8081)
RewriteCond %{HTTPS} off
RewriteCond %{HTTP:X-Forwarded-Proto} !https
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

Keep both conditions while the public vhosts still serve the same docroot: with only the
X-Forwarded-Proto line, direct HTTPS requests to Apache's :443 (which carry no such header) would
be redirected to themselves in a loop until the window.

→ `FORCE_SSL_ADMIN` in WordPress checks `$_SERVER['HTTPS']`. The `SetEnvIf` line makes that
`on` for PHP-FPM requests. On older setups without it, the usual wp-config.php fix is:

```php
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
    $_SERVER['HTTPS'] = 'on';
}
```

→ Other frameworks have their own switch: Laravel's TrustProxies middleware, Django's
`SECURE_PROXY_SSL_HEADER`, Express's `app.set('trust proxy', ...)`. The Node api reads
X-Forwarded-Proto, which Apache passes through unchanged.

→ `ServerName https://...` (Step 30) covers redirects that Apache itself generates, such as the
trailing-slash redirect for directories.

**Why this step (now):** redirect loops and "mixed content" are the most visible failures right
after a proxy cutover. They are easy to prevent and slow to debug under pressure.

**Next step:** → Step 33 to enable the sites and reload Apache once.
If an app stores its own base URL (WordPress `siteurl`/`home`, Laravel `APP_URL`) with `http://` →
change it to `https://` now, or it keeps generating wrong links.

### Step 33 — Configtest and graceful reload

**Goal:** activate the internal listener and vhosts without dropping a single request.

```bash
sudo a2ensite 000-internal-default shop.example.com-internal api.example.com-internal
sudo apache2ctl configtest
sudo apache2ctl -S 2>&1 | grep -A6 '8081'
sudo systemctl reload apache2          # = apachectl graceful on Ubuntu
journalctl -u apache2 -n 2 --no-pager
```

```
Enabling site 000-internal-default.
Enabling site shop.example.com-internal.
Enabling site api.example.com-internal.
To activate the new configuration, you need to run:
  systemctl reload apache2
Syntax OK
192.0.2.10:8081        is a NameVirtualHost
         default server internal-default.invalid (/etc/apache2/sites-enabled/000-internal-default.conf:3)
         port 8081 namevhost internal-default.invalid (/etc/apache2/sites-enabled/000-internal-default.conf:3)
         port 8081 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com-internal.conf:2)
                 alias www.shop.example.com
         port 8081 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com-internal.conf:2)
Oct 03 10:40:11 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Oct 03 10:40:11 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.
```

**What it means:**

→ `Syntax OK` first, always. `apachectl graceful` (what the reload runs) refuses a config that
fails the syntax check, but problems that only appear at runtime, such as a `Listen` address that
cannot be bound, make the parent exit during the reload, and then every site is down. Running
configtest yourself, and reading its warnings, is the cheapest insurance in this whole runbook.

→ The new address:port appears with the internal default first and both kept sites.

→ A graceful reload re-reads the config, opens the new listener, and lets in-flight requests
finish on the old workers. Users notice nothing.

**Why this step (now):** one reload for listener, vhosts, module and log format together is
easier to reason about (and to roll back) than several partial reloads.

**Next step:** → Step 34 to test the internal path the way Traefik will use it.
If configtest fails → do not reload; fix the named file and line. If `apache2ctl -S` does not list
8081 → the Listen line (Step 29) or `a2ensite` is missing.

### Step 34 — Verify the internal listener

**Goal:** prove each kept site works on 192.0.2.10:8081 with the headers Traefik will send.

```bash
sudo ss -ltnp 'sport = :8081'
H='X-Forwarded-Proto: https'
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' -H 'Host: shop.example.com' -H "$H" http://192.0.2.10:8081/
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' -H 'Host: shop.example.com' -H "$H" http://192.0.2.10:8081/wp-admin
curl -s -o /dev/null -w '%{http_code}\n'                 -H 'Host: api.example.com'  -H "$H" http://192.0.2.10:8081/v1/health
curl -s -o /dev/null -w '%{http_code}\n'                 -H 'Host: unknown.example.com'     http://192.0.2.10:8081/
# websocket handshake through Apache (101 = upgraded; --max-time stops curl afterwards)
curl -s -o /dev/null -w '%{http_code}\n' --max-time 3 -H 'Host: api.example.com' \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' 'http://192.0.2.10:8081/socket.io/?EIO=4&transport=websocket'
# spoofing test: from the host itself the XFF header must be IGNORED (we are not a trusted proxy)
curl -s -o /dev/null -H 'Host: shop.example.com' -H 'X-Forwarded-For: 203.0.113.99' http://192.0.2.10:8081/
sudo tail -n1 /var/log/apache2/shop_access.log
```

```
LISTEN 0 511 192.0.2.10:8081 0.0.0.0:* users:(("apache2",pid=24151,fd=8),("apache2",pid=24150,fd=8),("apache2",pid=1234,fd=8))
200
301 https://shop.example.com/wp-admin/
200
404
101
192.0.2.10 - - [03/Oct/2026:10:41:02 +0000] "GET / HTTP/1.1" 200 51234 "-" "curl/8.5.0" proto=-
```

**What it means:**

→ `200` for shop and api: the content path works over plain HTTP.

→ `301 https://shop.example.com/wp-admin/`: Apache's own redirect uses https and no port 8081.
If you saw `http://shop.example.com/...` here, the `ServerName https://` scheme is missing; a
`:8081` in the URL means the request's Host header carried the port or `UseCanonicalName` /
`UseCanonicalPhysicalPort` is On somewhere.

→ `404` for an unknown name: the internal default vhost catches it. A 200 with shop's page would
mean a forgotten default vhost.

→ `101` for the websocket: Apache upgrades the connection to the Node app.

→ The spoofing test logged `192.0.2.10`, not 203.0.113.99: correct, the host is not in
`RemoteIPInternalProxy`. After the install, requests from Traefik (172.18.0.x) will log the real
client.

→ A redirect loop shows up here as `301` pointing at the same URL. Fix Step 32 before continuing.

**Why this step (now):** this proves the new path while the old one still serves users. If
something fails here, you fix it calmly with zero impact. You never want to discover it during
the window.

**Next step:** → Step 35 to move the Node app off port 3000. If anything above failed → back to
Step 30 to 32; [Site down playbook](25-playbook-site-down.md) has the layer-by-layer method.

### Step 35 — Move the app that holds port 3000

**Goal:** api-node listens on 127.0.0.1:3001 and Apache proxies to it; port 3000 becomes free.

```bash
sudo ss -Hltnp 'sport = :3001'                                      # -H: no header; must print nothing
sudo grep -RIn -E '(127\.0\.0\.1|localhost):3000' /etc /opt /var/www 2>/dev/null | grep -v '\.bak:'
sudo sed -i.bak 's/^PORT=3000$/PORT=3001/' /opt/api/.env
sudo sed -i.bak 's#127\.0\.0\.1:3000#127.0.0.1:3001#g' \
  /etc/apache2/sites-available/api.example.com-le-ssl.conf \
  /etc/apache2/sites-available/api.example.com-internal.conf
sudo apache2ctl configtest && sudo systemctl restart api-node && sudo systemctl reload apache2
sudo ss -ltnp '( sport = :3000 or sport = :3001 )'
curl -s -o /dev/null -w '%{http_code}\n' --resolve api.example.com:443:192.0.2.10 https://api.example.com/v1/health
journalctl -u api-node -n 3 --no-pager
```

```
/etc/apache2/sites-available/api.example.com-le-ssl.conf:6:    ProxyPass /socket.io/ ws://127.0.0.1:3000/socket.io/
/etc/apache2/sites-available/api.example.com-le-ssl.conf:7:    ProxyPass / http://127.0.0.1:3000/
...
Syntax OK
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511        127.0.0.1:3001       0.0.0.0:*     users:(("node",pid=24388,fd=19))
200
Oct 03 10:52:07 web01 systemd[1]: Started api-node.service - Orders API (Node.js).
Oct 03 10:52:08 web01 node[24388]: Orders API listening on 127.0.0.1:3001
```

**What it means:**

→ The grep found only Apache's ProxyPass lines: nothing else (cron, other apps) calls 3000
directly. If it had found more, each would need the same edit.

→ Node now listens on 3001, nothing on 3000, and the public api still answers 200 through Apache.

→ The api was unavailable for the second or two between the Node restart and Apache's reload. Do
this at the quiet hour or inside the window, and tell the partner.

**Why this step (now):** it removes the third blocker independently of the others, so the window
only has to deal with 80 and 443. If the app does not read its port from config, you find out now,
not at 06:02 during the window.

**Next step:** → take backup **B1** (Step 21 again) and stop here until the window. In the
window → Step 36.
If the app ignores the new port → find where it really reads it (the unit's `ExecStart`, a default
in the code) and change that. If the api returns 502 afterwards → Apache still points at 3000:
re-run the grep.

### Step 36 — Remove Apache from 80 and 443 (window)

**Goal:** Apache releases the public ports; it keeps serving on 192.0.2.10:8081.

```bash
sudo cp -a /etc/apache2/ports.conf /etc/apache2/ports.conf.pre-window
sudoedit /etc/apache2/ports.conf          # leave only the internal Listen line (below)
sudo a2dissite 000-default shop.example.com shop.example.com-le-ssl api.example.com \
  api.example.com-le-ssl docs.example.com docs.example.com-ssl intranet.example.com
sudo a2ensite intranet-retired
sudo apache2ctl configtest && sudo systemctl reload apache2
```

```apache
# /etc/apache2/ports.conf — Apache sits behind dokploy-traefik since 2026-10-06 (CR-1234)
Listen 192.0.2.10:8081
```

```
Site 000-default disabled.
Site shop.example.com disabled.
Site shop.example.com-le-ssl disabled.
...
Enabling site intranet-retired.
Syntax OK
```

**What it means:** from this moment, nothing answers on 80/443: legacy sites are down until
Traefik routes them (Step 48). The clock is running; follow the window plan without improvising.
The public vhost files stay in sites-available, so rollback is `a2ensite` + the old ports.conf.

**Why this step (now):** it is the first step with user impact, so it comes only after the
internal path is proven (Step 34), the blockers on 3000 are gone (Step 35) and backups exist.

**Next step:** → Step 37 to confirm the ports are really free before running the installer.
If configtest fails here → restore `ports.conf.pre-window`, `a2ensite` the public vhosts and reload
(Phase 5 wrap-up, Rollback) before trying again.

### Step 37 — Confirm 80, 443 and 3000 are free

**Goal:** the exact check the Dokploy installer will run passes.

```bash
sudo ss -tulnp | grep -E ':(80|443|3000) ' || echo "80/443/3000 free"
sudo ss -ltnp 'sport = :8081'
```

```
80/443/3000 free
LISTEN 0 511 192.0.2.10:8081 0.0.0.0:* users:(("apache2",pid=24502,fd=8),("apache2",pid=1234,fd=8))
```

**What it means:** the installer will pass its port check, and Apache still serves the internal
port.

If 443 still shows an `apache2` worker PID after the reload, that worker is finishing a long
request (a download, a websocket) during the graceful reload. Wait 30 seconds and check again; if
it persists, `sudo systemctl restart apache2` forces it (in-flight requests on that worker are cut,
which is acceptable inside the window).

**Why this step (now):** running the installer against a half-free port wastes minutes of your
window on an error message. Ten seconds of checking avoids it.

**Next step:** → Phase 6, Step 38.
If anything other than an apache2 worker still holds 80, 443 or 3000 → identify it with Step 2's
commands; do not start the installer until the check prints nothing.

### Reload, restart and graceful-stop compared

| Command | What happens | In-flight requests | Use when |
|---|---|---|---|
| `systemctl reload apache2` | Ubuntu runs `apachectl graceful`: re-read config, open/close listeners, replace workers | finish normally | config and listener changes (almost always) |
| `systemctl restart apache2` | stop, then start | cut (or waited for, depending on the unit's stop command) | a module/MPM change, or a socket that a graceful reload left behind |
| `apachectl graceful-stop` | stop accepting, let in-flight requests finish, exit | finish (up to `GracefulShutdownTimeout`) | retiring Apache politely |
| `systemctl stop apache2` | runs the unit's ExecStop (on Ubuntu `apachectl graceful-stop`; check `systemctl cat apache2`) | as above, then systemd kills after `TimeoutStopSec` | retiring or rollback prep |
| `apachectl -k stop` / `kill -TERM` parent | immediate stop | cut | systemd unavailable |

The signals behind them, sent to the parent PID from `/run/apache2/apache2.pid`: `TERM` = stop now,
`USR1` = graceful restart, `HUP` = restart, `WINCH` = graceful stop. On RHEL/Rocky the unit is
`httpd` and the PID file is `/run/httpd/httpd.pid`.

### Retiring Apache completely

When the last site has moved into Dokploy (Option E done), stop Apache for good:

```bash
sudo systemctl disable --now apache2      # stop now + do not start at boot
sudo systemctl mask apache2               # nothing can start it (dependencies, package scripts)
systemctl is-enabled apache2              # -> masked
# rollback:  sudo systemctl unmask apache2 && sudo systemctl enable --now apache2
```

Keep the package and its config for a few weeks. Later, `apt remove apache2` keeps the config
files; `apt purge` deletes /etc/apache2 and is the step you only do after the backup is archived.

### Killing Apache: the last resort

> ⚠️ `kill -9` (SIGKILL) on Apache is not a way to free port 443. Use it only on a single hung
> process after everything below has failed.

Prefer, in this order: `systemctl reload` → `systemctl restart` → `systemctl stop` →
`sudo apachectl -k graceful-stop` → `sudo kill -TERM "$(cat /run/apache2/apache2.pid)"` (the parent
only). The `kill` route is only for an Apache that was started by hand outside systemd, or a
unit that hangs in "deactivating".

Why not `kill -9`: the parent gets no chance to stop its children, so orphaned workers can keep
the listening socket open (the port stays busy, which is exactly what you were trying to fix).
It also leaves the scoreboard shared memory and semaphores behind, and the next start can fail
with errors like `AH00023: Couldn't create the ... mutex` / "No space left on device" until they
are cleaned up (`ipcs -s` shows them). See [Processes](05-processes.md) for signals in general.

### Phase 5 wrap-up

```
Internal listener answers? (Step 34: curl -H Host ... http://192.0.2.10:8081/)
├── connection refused  → Listen line / reload / bind address (Step 29, 33)
├── wrong site / 200 for unknown name → default vhost order (Step 30)
├── redirect loop / http:// redirects → X-Forwarded-Proto handling (Step 32)
├── log shows proxy IP for Traefik traffic → mod_remoteip subnet (Step 31)
└── all OK → move 3000 (Step 35) → backup B1 → window: remove 80/443 (Step 36)
             → 80/443/3000 free? (Step 37) ── no → wait / restart apache2
```

**Fix & verify:** besides the steps above, update the two hidden users found in Steps 18 and 19,
because 127.0.0.1:80 will soon be Traefik:

```bash
# www-data's WordPress cron: call Apache's internal port directly
sudo crontab -u www-data -e
#   */5 * * * * curl -s -H 'Host: shop.example.com' -H 'X-Forwarded-Proto: https' http://192.0.2.10:8081/wp-cron.php >/dev/null
# monitoring of server-status: point it at http://192.0.2.10:8081/server-status
```

**Rollback:** restore the ports file and the public vhosts, then reload:

```bash
sudo cp -a /etc/apache2/ports.conf.pre-window /etc/apache2/ports.conf
sudo a2ensite 000-default shop.example.com shop.example.com-le-ssl api.example.com api.example.com-le-ssl
sudo apache2ctl configtest && sudo systemctl reload apache2
```

**Prevent it next time:** on every new server, put application servers on internal addresses from
day one, and keep the public ports for exactly one reverse proxy.

---

## 7. Phase 6 — Install Dokploy and deploy with Docker

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* (free) — Docker Run Commands, Docker Compose, Docker Networking ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner), [networking notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Publishing Ports, then Docker Swarm: Docker Overlay Network ([Publishing Ports notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page), [Overlay Network notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page); [course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Note: [Learn: Docker zero to hero](30-learn-docker.md) and the [Dokploy docs](https://docs.dokploy.com/docs/core) · 4) Video: *How Docker Networking Actually Works* (KodeKloud, 9 min, [YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 5) Practice: on the [Docker playground](https://kodekloud.com/playgrounds/playground-docker), publish one container with `-p 8000:80` and one with `-p 127.0.0.1:8001:80`, then compare `ss -ltnp` and `docker port`.

**Level:** [L3 · Senior]. Docker, Swarm, Dokploy and Docker's firewall behaviour belong to the L3
Platform level. A mid-level engineer can follow the steps; a senior knows why each one is there.

Goal of the phase: Dokploy runs (Docker, Swarm, Traefik, UI), its admin account is yours, port
3000 is not open to the world, and the client's app is deployed with HTTPS. The plain-Docker path
(no Dokploy) is at the end of the phase for when you need Option A. Background:
[Docker zero to hero](30-learn-docker.md) and [Web servers and proxies](29-learn-webservers-proxies.md).

> ⏱️ In the window, the legacy sites are down from Step 36 until Step 48. Run Step 39 and 40, then
> go straight to Step 47 and 48, and come back to Step 41 once the old sites answer again.

### Step 38 — Read what the installer will do

**Goal:** know every change the installer makes before you run it as root.

```bash
grep -nE "ss -tulnp|get.docker.com|swarm (leave|init)|network (rm|create)|chmod|secret create|service create|docker run|--name|-p [0-9]|--publish|traefik:v|postgres:" \
  ~/case-web01/dokploy-install.sh
sha256sum ~/case-web01/dokploy-install.sh
```

```
117:    if ss -tulnp | grep ':80 ' >/dev/null; then
123:    if ss -tulnp | grep ':443 ' >/dev/null; then
129:    if ss -tulnp | grep ':3000 ' >/dev/null; then
142:      curl -sSL https://get.docker.com | sh -s -- --version $DOCKER_VERSION
167:    docker swarm leave --force 2>/dev/null
...
245:        docker swarm init --advertise-addr $advertise_addr $swarm_init_args
247:        docker swarm init --advertise-addr $advertise_addr
257:    docker network rm -f dokploy-network 2>/dev/null
258:    docker network create --driver overlay --attachable dokploy-network
264:    chmod 777 /etc/dokploy
270:    echo "$POSTGRES_PASSWORD" | docker secret create dokploy_postgres_password - 2>/dev/null || true
276:    echo "$AUTH_SECRET" | docker secret create dokploy_auth_secret - 2>/dev/null || true
280:    docker service create \
281:    --name dokploy-postgres \
290:    postgres:16
310:    docker service create \
311:      --name dokploy \
319:      --publish published=3000,target=3000,mode=host \
331:    docker run -d \
332:        --name dokploy-traefik \
338:        -p 80:80/tcp \
339:        -p 443:443/tcp \
340:        -p 443:443/udp \
341:        traefik:v3.6.25
...                                     (lines 344-355: a commented-out "docker service create" variant)
```

**What it means:** the installer, as published at the time of writing (verify your copy; it
changes between releases):

| # | What it does | Why you care |
|---|---|---|
| 1 | Requires root, Linux, not inside a container | run it with sudo on the host |
| 2 | Exits if anything listens on :80, :443 or :3000 (TCP or UDP, any address) | the reason for Phase 5 |
| 3 | Installs Docker CE from get.docker.com if `docker` is missing, pinned version, `apt-mark hold` | Docker upgrades become your manual task |
| 4 | `docker swarm leave --force`, then `docker swarm init --advertise-addr ADDR` | destroys membership in any existing Swarm |
| 5 | Recreates the overlay network `dokploy-network` (attachable) | apps and Traefik meet on it |
| 6 | Creates `/etc/dokploy` with mode 777 | Traefik config lives here; any local user can edit it |
| 7 | Stores the Postgres password and an auth secret as Docker secrets | no plain-text passwords in env |
| 8 | Swarm service `dokploy-postgres` (postgres:16, volume dokploy-postgres) | Dokploy's database: back up this volume |
| 9 | Swarm service `dokploy`, publishes 3000 in host mode, mounts docker.sock and /etc/dokploy | the UI; it controls Docker fully |
| 10 | Container `dokploy-traefik` via `docker run`, `--restart always`, `--network dokploy-network`, publishes 80/tcp, 443/tcp, 443/udp | the new owner of the public ports |

The advertise address is `ADVERTISE_ADDR` if set, otherwise the first private (RFC1918) address on
a real interface, otherwise the public IP from an external lookup. Set it explicitly whenever the
host has more than one address (and in this runbook, because 192.0.2.10 is not an RFC1918 address).

Older installs and many blog posts also show a `dokploy-redis` service and Traefik running as a
Swarm service; the current script creates neither. What you see on a host depends on the version
it was installed with.

**Why this step (now):** you are about to run a script from the Internet as root on a production
server. Reading it is the minimum. Saving it with a checksum records exactly what ran, for the
postmortem and for a rebuild.

**Next step:** → Step 39 to run it.
If your copy of the script differs from this table (other services, other ports) → update the change
request and the firewall plan before the window.

### Step 39 — Run the installer

**Goal:** Dokploy installed with your chosen address and address pool, output logged.

```bash
sudo ADVERTISE_ADDR=192.0.2.10 \
     DOCKER_SWARM_INIT_ARGS="--default-addr-pool 10.250.0.0/16 --default-addr-pool-mask-length 24" \
     bash ~/case-web01/dokploy-install.sh 2>&1 | tee ~/case-web01/dokploy-install.log
```

```
Detecting latest stable version from GitHub...
Latest stable version detected: v0.29.10
Installing Dokploy version: v0.29.10
Docker already installed
Using advertise address: 192.0.2.10
Using custom swarm init arguments: --default-addr-pool 10.250.0.0/16 --default-addr-pool-mask-length 24
Swarm initialized: current node (q3k8w0e2xv7hd1n4pyt6ma9rc) is now a manager.
...                                   (docker swarm join instructions)
Swarm initialized
x1v8c2d9pe7q4m0a3s5k6j2hn
Network created
p0w8x3k5m2n7q9r4t6y1u3v5a
h2j4k6l8z1x3c5v7b9n0m2q4w
Generated secure database credentials and auth secret (stored in Docker Secrets)
verify: Service dokploy-postgres converged
verify: Service dokploy converged
3f9a1c7e5b2d...
Congratulations, Dokploy is installed!
Wait 15 seconds for the server to start
Please go to http://192.0.2.10:3000
```

**What it means:**

→ "Docker already installed": the pre-install from Step 26 saved the slowest part.

→ "converged" for both services: their tasks reached the running state. (The two IDs after
"Network created" are the Docker secrets; each service's ID and progress bars are trimmed here.)

→ The long hex line after "verify" is the dokploy-traefik container ID: Traefik started and bound
80/443.

→ If it stops with `Error: something is already running on port 443` → back to Step 37.
`Failed to initialize Docker Swarm` → usually the advertise address is wrong or not on this host.
Image pull errors → proxy or Docker Hub rate limit (Step 23).

**Why this step (now):** ports are free (Step 37) and every input was prepared, so this is a
mechanical step. The log file goes into the change request.

**Next step:** → Step 40 to verify what was created.
If it failed → use the matching branch in "What it means" above and re-run; if it cannot be fixed
before the rollback trigger → Section 10.

### Step 40 — Verify containers, services, networks and ports

**Goal:** confirm every component runs, find Traefik's source subnet, and see who now owns the
ports.

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker service ls --format 'table {{.Name}}\t{{.Mode}}\t{{.Replicas}}\t{{.Image}}'
docker network ls
docker network inspect docker_gwbridge --format '{{range .IPAM.Config}}{{.Subnet}} gw={{.Gateway}}{{end}}'
sudo ss -tulnp | grep -E ':(80|443|3000|2377|7946) '
docker logs --tail 5 dokploy-traefik
```

```
NAMES                                   IMAGE                       STATUS          PORTS
dokploy-traefik                         traefik:v3.6.25             Up 2 minutes    0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp, [::]:443->443/tcp, [::]:443->443/udp
dokploy.1.m2k7c1x9q0zv8r3d5t6y4wn1b     dokploy/dokploy:v0.29.10    Up 2 minutes    0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
dokploy-postgres.1.h8s1v4n2l5c7x0q9w3e  postgres:16                 Up 2 minutes    5432/tcp

NAME               MODE         REPLICAS   IMAGE
dokploy            replicated   1/1        dokploy/dokploy:v0.29.10
dokploy-postgres   replicated   1/1        postgres:16

NETWORK ID     NAME              DRIVER    SCOPE
5d2c3b1a0f9e   bridge            bridge    local
8a7f6e5d4c3b   docker_gwbridge   bridge    local
x1v8c2d9pe7q   dokploy-network   overlay   swarm
2b1a0f9e8d7c   host              host      local
k4j3h2g1f0e9   ingress           overlay   swarm
9e8d7c6b5a4f   none              null      local

172.18.0.0/16 gw=172.18.0.1

udp   UNCONN 0  0        0.0.0.0:443    0.0.0.0:*  users:(("docker-proxy",pid=31877,fd=7))
udp   UNCONN 0  0           [::]:443       [::]:*  users:(("docker-proxy",pid=31884,fd=7))
udp   UNCONN 0  0              *:7946         *:*  users:(("dockerd",pid=30210,fd=41))
tcp   LISTEN 0  4096     0.0.0.0:80     0.0.0.0:*  users:(("docker-proxy",pid=31851,fd=7))
tcp   LISTEN 0  4096     0.0.0.0:443    0.0.0.0:*  users:(("docker-proxy",pid=31866,fd=7))
tcp   LISTEN 0  4096     0.0.0.0:3000   0.0.0.0:*  users:(("docker-proxy",pid=31710,fd=7))
tcp   LISTEN 0  4096           *:2377         *:*  users:(("dockerd",pid=30210,fd=33))
tcp   LISTEN 0  4096           *:7946         *:*  users:(("dockerd",pid=30210,fd=36))
...
2026-10-06T06:03:41Z INF Traefik version 3.6.25 built on ...
2026-10-06T06:03:41Z INF Starting provider *file.Provider
2026-10-06T06:03:41Z INF Starting provider *docker.Provider
2026-10-06T06:03:41Z INF Starting provider *docker.SwarmProvider
```

**What it means:**

→ Three running pieces: the Traefik container, and one task each for the dokploy and
dokploy-postgres services (task names end in `.1.TASKID`).

→ `docker_gwbridge` is 172.18.0.0/16, the subnet Step 25 (UFW) and Step 31 (mod_remoteip)
assumed. If Docker picked something else, fix both now.

→ 80, 443 and 3000 are now owned by `docker-proxy`. From the host's point of view "who owns
443?" is answered by Docker, not by the process table:
`docker ps --filter publish=443` names the container. This is the case
[Who owns this port?](22-playbook-ports-inventory.md) covers for containers.

→ dockerd listens on 2377 and 7946 (Swarm management and gossip). They are host processes, so
UFW's default deny keeps them closed from outside. Do not open them unless you add Swarm nodes.

→ The Traefik log shows the file, Docker and Swarm providers starting: it is reading
`/etc/dokploy/traefik/dynamic/`, where Step 48 puts the legacy routes.

**Why this step (now):** before adding your own routes you want to know that the platform
itself is healthy; otherwise you cannot tell your mistakes from installation problems.

**Next step:** in the window → Step 47 and 48 now (legacy sites are still down). Then → Step 41.
If a component is not Up or a service shows `0/1` → `docker service ps --no-trunc SERVICE` and
`docker logs` for it ([Containers playbook](26-playbook-containers-k8s.md)) before you add any
routes.

### Step 41 — Claim the admin account and set the domain

**Goal:** you own the Dokploy instance, and its UI is reachable on https://dokploy.example.com.

> ⚠️ A fresh Dokploy shows a registration page, and the first account created becomes the owner.
> Anyone who reaches port 3000 before you can take over your server (the UI controls Docker as
> root). Register immediately, from the admin network, and lock 3000 down (Step 42).

In the UI (labels can differ slightly between versions): register the admin account, then in the
server/web-server settings set the domain `dokploy.example.com`, a real Let's Encrypt email (the
generated traefik.yml starts with a placeholder address) and enable HTTPS.

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.0.2.10:3000/          # from the admin network
sudo grep -nE 'email|storage|entryPoint:|certResolver' /etc/dokploy/traefik/traefik.yml
curl -s -o /dev/null -w '%{http_code}\n' https://dokploy.example.com/
echo | openssl s_client -connect 192.0.2.10:443 -servername dokploy.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -enddate
```

```
200
21:        certResolver: letsencrypt
27:      email: ops@example.com
28:      storage: /etc/dokploy/traefik/dynamic/acme.json
30:        entryPoint: web
200
subject=CN = dokploy.example.com
issuer=C = US, O = Let's Encrypt, CN = R10
notAfter=Jan  4 06:21:09 2027 GMT
```

**What it means:**

→ The UI answers on 3000 and on its domain over HTTPS.

→ traefik.yml shows the resolver name `letsencrypt`, its email, the storage file
`/etc/dokploy/traefik/dynamic/acme.json` and the HTTP-01 challenge on the `web` entry point
(port 80). That resolver name is what your own routes reference in Step 48.

→ The certificate is issued by Let's Encrypt for dokploy.example.com. If you see
`CN = TRAEFIK DEFAULT CERT`, issuance has not happened or failed: read `docker logs dokploy-traefik`
for `acme` errors (Section 9 lists the prerequisites).

**Why this step (now):** an unclaimed Dokploy instance is an open door, and the domain is the
prerequisite for closing port 3000.

**Next step:** → Step 42 to stop exposing 3000.
If the certificate is still `TRAEFIK DEFAULT CERT` → check DNS and port 80 reachability (Section 9
prerequisites) and the `acme` lines in Traefik's log.

### Step 42 — Lock down port 3000

**Goal:** port 3000 is reachable only from the admin network now, and not at all once the
domain works.

Published container ports skip UFW (Step 25), so `ufw deny 3000` does nothing. Filter in the
`DOCKER-USER` chain, matching the *original* destination port, because Docker has already
rewritten the destination (DNAT) when the packet reaches that chain.

```bash
# -I inserts at the top: insert the DROP first, then the ACCEPT above it
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL -j DROP
sudo iptables -I DOCKER-USER -i ens18 -s 198.51.100.0/24 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL -j ACCEPT
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
Chain DOCKER-USER (1 references)
num   pkts bytes target  prot opt in     out  source            destination
1        4   240 ACCEPT  6    --  ens18  *    198.51.100.0/24   0.0.0.0/0    ctorigdstport 3000 ctdir ORIGINAL
2       17  1020 DROP    6    --  ens18  *    0.0.0.0/0         0.0.0.0/0    ctorigdstport 3000 ctdir ORIGINAL
3     9811  4.1M RETURN  0    --  *      *    0.0.0.0/0         0.0.0.0/0
```

**What it means:**

→ The `prot` column is numeric (6 = tcp, 0 = all) because iptables 1.8.9 and 1.8.10 (Ubuntu
24.04) print protocol numbers with `-n`; 22.04's iptables 1.8.7 and 1.8.11+ print `tcp` / `all`.
Whether a final `RETURN` rule is listed also depends on the Docker version.

→ Rule 1 lets the admin network in; rule 2 drops everybody else; the counters prove both match
real traffic (17 dropped packets: scanners found 3000 within minutes).

→ These rules are lost on reboot. Persist them with a small oneshot unit that runs after
docker.service, or in UFW's `/etc/ufw/after.rules` in a `DOCKER-USER` section. Do not
`iptables-save` the whole table into a persistent file: it would freeze Docker's own dynamic rules.

Once https://dokploy.example.com works, remove the published port entirely (the method the Dokploy
community documents):

```bash
docker service update --publish-rm "published=3000,target=3000,mode=host" dokploy
sudo ss -Hltnp 'sport = :3000'                 # -H: no header; expect no output
curl -s -o /dev/null -w '%{http_code}\n' https://dokploy.example.com/
# rollback if you lock yourself out (from the server console/SSH):
#   docker service update --publish-add "published=3000,target=3000,mode=host" dokploy
```

```
dokploy
overall progress: 1 out of 1 tasks
verify: Service dokploy converged
200
```

Also check that the default local route created at install is gone or harmless: the default
dynamic config routes `Host(dokploy.docker.localhost)` to the UI, so
`curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: dokploy.docker.localhost' http://192.0.2.10/`
should not return the Dokploy login once your domain is set. If it does, review
`/etc/dokploy/traefik/dynamic/dokploy.yml`.

**Why this step (now):** an admin UI that controls Docker should never be on the Internet. Doing it
right after the domain works closes the exposure window to minutes.

**Next step:** → Step 43 to deploy the client's app.
If the UI is unreachable after `--publish-rm` → the domain route is broken; re-add the port with the
rollback command above and fix the domain first.

### Step 43 — Deploy the client's app in Dokploy

**Goal:** app.example.com runs as a Dokploy Application from the Harbor image, with HTTPS.

Application or Docker Compose?

| | Application | Docker Compose |
|---|---|---|
| Source | Git repo (build with Dockerfile, Nixpacks, buildpacks) or a ready image | a compose file (repo or pasted) |
| Runs as | one Swarm service | containers or a stack, several services |
| Domains | Domains tab; Dokploy writes the Traefik route as a file in the dynamic directory | Domains tab injects labels and dokploy-network; redeploy after changes |
| Best for | one container app (our case) | app + database + worker together |

Before deploying from Harbor, the host's Docker must trust Harbor's private CA, or pulls fail with
`x509: certificate signed by unknown authority`:

```bash
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp ~/case-web01/harbor-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
sudo docker pull harbor.example.com/client/app:1.4.2     # after: docker login harbor.example.com
```

```
1.4.2: Pulling from client/app
Digest: sha256:5b1e...
Status: Downloaded newer image for harbor.example.com/client/app:1.4.2
```

Then in the UI: add the registry (Harbor URL and a robot account) in the registry settings,
create a project `client`, create an Application `app`, choose the Docker image provider with
`harbor.example.com/client/app:1.4.2` and that registry, add the environment variables in the
Environment tab, add a domain `app.example.com` with path `/`, container port `8000`, HTTPS on and
Let's Encrypt as the certificate provider, then Deploy. Watch the Deployments tab for the deploy
log and the Logs tab for the running container.

**What it means:** the pull proves trust and credentials from the host before Dokploy tries; when
the UI deploy fails, you already know it is not the registry. The container port must be the port
the app listens on *inside* the container (8000), not a host port: nothing is published on the
host, Traefik reaches the service over dokploy-network.

**Why this step (now):** this is the client's actual request. It comes after the platform and the
legacy sites are stable, so a problem here affects only the new app.

**Next step:** → Step 44 to check the app from the shell.
If the deploy fails on pull → registry credentials or CA trust (repeat the pull test above). If it
deploys but the domain returns 404 or 502 → Step 44.

### Step 44 — Check the app's logs and routing

**Goal:** confirm the service runs, find its logs and the route Dokploy wrote.

```bash
docker service ls --format '{{.Name}} {{.Replicas}} {{.Image}}' | grep app
docker service ps --no-trunc --format '{{.Name}} {{.CurrentState}} {{.Error}}' client-app-x7k2qd | head -n3
docker service logs --tail 20 client-app-x7k2qd
sudo ls /etc/dokploy/traefik/dynamic/
sudo cat /etc/dokploy/traefik/dynamic/client-app-x7k2qd.yml
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers \
  | jq -r '.[] | "\(.name)\t\(.status)\t\(.rule)"' | grep -E 'app|legacy'
curl -s -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' https://app.example.com/healthz
```

```
client-app-x7k2qd 1/1 harbor.example.com/client/app:1.4.2
client-app-x7k2qd.1 Running 3 minutes ago

client-app-x7k2qd.1.k2j...@web01 | Listening on 0.0.0.0:8000

acme.json  client-app-x7k2qd.yml  dokploy.yml  legacy-apache.yml  middlewares.yml

http:
  routers:
    client-app-x7k2qd-router-1:
      rule: Host(`app.example.com`)
      service: client-app-x7k2qd-service-1
      middlewares:
        - redirect-to-https
      entryPoints:
        - web
    client-app-x7k2qd-router-websecure-1:
      rule: Host(`app.example.com`)
      service: client-app-x7k2qd-service-1
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
  services:
    client-app-x7k2qd-service-1:
      loadBalancer:
        servers:
          - url: http://client-app-x7k2qd:8000
        passHostHeader: true

client-app-x7k2qd-router-1@file              enabled  Host(`app.example.com`)
client-app-x7k2qd-router-websecure-1@file    enabled  Host(`app.example.com`)
...                                          (the other legacy-* routers from Step 48)
legacy-shop@file                             enabled  Host(`shop.example.com`) || Host(`www.shop.example.com`)
200 0
```

**What it means:**

→ Dokploy names the service `PROJECT-APP-RANDOM` (here client-app-x7k2qd); every Docker command
uses that name.

→ `Listening on 0.0.0.0:8000`: the app binds all interfaces inside its container. If it said
127.0.0.1:8000, Traefik could not reach it and would answer 502.

→ The generated file (exact layout varies by version) shows the pattern you reuse for Apache in
Step 48: an HTTP router that redirects, an HTTPS router with `certResolver: letsencrypt`, and a
service whose URL is the Swarm service name on dokploy-network plus the container port.

→ The Traefik API lists routers with their status: `enabled` is good; `disabled` or `warning`
comes with an error message in the full JSON.

→ `200 0`: HTTP 200 and `ssl_verify_result` 0 (certificate verified).

**Why this step (now):** knowing where Dokploy keeps logs and routes lets you debug from the shell
when the UI is not enough. Wrong container port → 502; missing domain/redeploy → 404; see
[Containers playbook](26-playbook-containers-k8s.md).

**Next step:** the client app is done. If you are running the plain-Docker path instead, see Step
45 and 46. Otherwise → Phase 7 (if you came here from the window, it is already done).

### Without Dokploy: plain Docker

Use this for Option A (Apache keeps 443) or any host where Dokploy is not wanted.

### Step 45 — Run the app with docker run

**Goal:** the app runs as a container reachable only from the host, restarted automatically,
with bounded logs.

```bash
docker login harbor.example.com
docker run -d --name app --restart unless-stopped \
  -p 127.0.0.1:18000:8000 \
  --env-file /opt/app/app.env \
  --log-opt max-size=50m --log-opt max-file=3 \
  harbor.example.com/client/app:1.4.2
docker ps --filter name='^app$' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker port app
docker logs --tail 5 app
docker inspect --format '{{.State.Status}} restarts={{.RestartCount}} ip={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' app
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18000/healthz
```

```
NAMES     STATUS          PORTS
app       Up 12 seconds   127.0.0.1:18000->8000/tcp
8000/tcp -> 127.0.0.1:18000
Listening on 0.0.0.0:8000
running restarts=0 ip=172.17.0.2
200
```

**What it means:**

→ `127.0.0.1:18000->8000/tcp`: published on loopback only. Because published ports bypass UFW, a
plain `-p 18000:8000` would expose the app to the whole network.

→ `--restart unless-stopped`: comes back after a crash or reboot, but not after you stop it on
purpose.

→ `max-size/max-file`: the default json-file log driver never rotates; without these options the
log grows until the disk is full.

Then publish it through Apache (Option A) with one vhost and a certificate:

```apache
# /etc/apache2/sites-available/app.example.com.conf  (then: a2ensite, configtest, reload,
#  and: sudo certbot --apache -d app.example.com)
<VirtualHost *:80>
    ServerName app.example.com
    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:18000/
    ProxyPassReverse / http://127.0.0.1:18000/
    ErrorLog ${APACHE_LOG_DIR}/app_error.log
    CustomLog ${APACHE_LOG_DIR}/app_access.log combined
</VirtualHost>
```

certbot copies this into an SSL vhost on 443 and adds the redirect. In the SSL copy, add
`RequestHeader set X-Forwarded-Proto "https"` so the app knows it is served over HTTPS.

**Why this step (now):** it is the fastest safe way to ship a container next to Apache, and the
basis of Option A.

**Next step:** → Step 46 for the Compose version with a healthcheck and Traefik labels.
If curl gets `connection refused` → the app listens on 127.0.0.1 inside the container or on another
port: read `docker logs app` for its listen address.

### Step 46 — Compose file with healthcheck and Traefik labels

**Goal:** a declarative, reviewable definition of the app that Traefik (Dokploy's or your own)
routes by labels.

```yaml
# /opt/app/docker-compose.yml
services:
  app:
    image: harbor.example.com/client/app:1.4.2
    restart: unless-stopped
    env_file: .env
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8000/healthz"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"
    networks:
      - dokploy-network
    labels:
      - traefik.enable=true
      - traefik.http.routers.client-app.rule=Host(`app.example.com`)
      - traefik.http.routers.client-app.entrypoints=websecure
      - traefik.http.routers.client-app.tls.certresolver=letsencrypt
      - traefik.http.routers.client-app-http.rule=Host(`app.example.com`)
      - traefik.http.routers.client-app-http.entrypoints=web
      - traefik.http.routers.client-app-http.middlewares=redirect-to-https@file
      - traefik.http.services.client-app.loadbalancer.server.port=8000

networks:
  dokploy-network:
    external: true
```

```bash
cd /opt/app
docker compose config --quiet && echo "compose file valid"
docker compose up -d
docker compose ps
docker inspect --format '{{json .State.Health}}' "$(docker compose ps -q app)" | jq '.Status, .Log[-1].Output'
```

```
compose file valid
[+] Running 1/1
 ✔ Container app-app-1  Started
NAME        IMAGE                                 COMMAND                  SERVICE   CREATED          STATUS                    PORTS
app-app-1   harbor.example.com/client/app:1.4.2   "docker-entrypoint.s…"   app       26 seconds ago   Up 25 seconds (healthy)   8000/tcp
"healthy"
"{\"status\":\"ok\"}"
```

**What it means:**

→ No `ports:` at all: Traefik reaches the container over dokploy-network, so nothing is published
on the host and nothing bypasses the firewall.

→ `traefik.enable=true` and the dokploy-network are both required, because Dokploy's Traefik runs
with `exposedByDefault: false` and uses that network to reach containers.

→ `loadbalancer.server.port=8000` pins the port. Without it Traefik guesses from the image's
`EXPOSE`, and a wrong guess is a 502.

→ `(healthy)`: Traefik's Docker provider skips containers whose healthcheck is still starting or
unhealthy, so a broken healthcheck shows up as a 404 from Traefik, not as a 502. The test command
must exist in the image (wget here; use curl or a small binary otherwise).

→ Labels are read when the container is created: after changing them, `docker compose up -d`
again (in Dokploy: redeploy).

**Why this step (now):** Compose is the bridge between "a docker run I typed" and a Dokploy
Compose app or a GitLab CI deployment: the same file works in all three.

**Next step:** → Phase 7 to route the legacy sites.
If the container stays `(health: starting)` or turns `unhealthy` → run the healthcheck command by
hand with `docker exec`; Traefik will not route to it until it is healthy.

### Phase 6 wrap-up

```
Installer ran?
├── "something is already running on port N" → Step 37 (who still holds N)
├── swarm init failed → ADVERTISE_ADDR wrong / not on this host
├── image pull failed → proxy for dockerd, Docker Hub limits (Step 23)
└── OK → docker ps / service ls healthy? (Step 40)
         ├── traefik restarting → docker logs dokploy-traefik (bad traefik.yml?)
         └── OK → admin claimed + domain HTTPS (Step 41) → 3000 locked (Step 42)
                  → app deployed → 404? domain/redeploy/health ; 502? container port / 0.0.0.0 bind
```

**Fix & verify:** `docker ps` shows the three components Up, 3000 is filtered then unpublished,
https://dokploy.example.com and https://app.example.com return 200 with Let's Encrypt
certificates.

**Rollback:** see Section 10 (stop Traefik, scale Dokploy to zero, restore Apache).

**Prevent it next time:** keep the installer copy and its log with the change request; persist
the DOCKER-USER rules; back up `/etc/dokploy` and the `dokploy-postgres` volume like any other
database.

---

## 8. Phase 7 — Route the legacy Apache sites through Traefik

> 📚 **Study path:** 1) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview, then Demo: Traefik Installation ([overview notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page), [installation notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Demo-Traefik-Installation/page)); KodeKloud has no Traefik-on-Docker course, but entry points, routers, services and logs are the same · 2) Docs: Traefik [Docker and Traefik Quick Start](https://doc.traefik.io/traefik/getting-started/docker/) · 3) Note: [Learn: web servers and proxies](29-learn-webservers-proxies.md) · 4) Video: *Traefik v3.3 - Secure Everything! Complete Tutorial* (Jim's Garage, 32 min, [YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 5) Practice: the L3 drill: make Traefik return 502 with a wrong backend port, then fix it from Traefik's logs alone.

**Level:** [L3 · Senior]. Writing Traefik routers and services by hand and debugging them from
Traefik's API and logs is the L3 skill this whole migration depends on.

Goal of the phase: Traefik knows every kept legacy name, terminates TLS for it with a valid
certificate, and forwards it to Apache on 192.0.2.10:8081. Dokploy only writes routes for things
it deploys, so the legacy routes are a file you add to Traefik's file-provider directory. Traefik
docs: [doc.traefik.io](https://doc.traefik.io/traefik/).

### Step 47 — Inspect Traefik's config layout

**Goal:** know where the static and dynamic configuration live, how they reach the container, and
the names (entry points, resolver, middleware) you will reference.

```bash
sudo ls -la /etc/dokploy/traefik /etc/dokploy/traefik/dynamic
sudo cat /etc/dokploy/traefik/traefik.yml
sudo cat /etc/dokploy/traefik/dynamic/middlewares.yml
docker inspect dokploy-traefik --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

```
/etc/dokploy/traefik:
-rw-r--r-- 1 root root  612 Oct  6 06:03 traefik.yml
drwxr-xr-x 2 root root 4096 Oct  6 06:03 dynamic
/etc/dokploy/traefik/dynamic:
-rw------- 1 root root    0 Oct  6 06:03 acme.json
-rw-r--r-- 1 root root  402 Oct  6 06:03 dokploy.yml
-rw-r--r-- 1 root root  135 Oct  6 06:03 middlewares.yml

providers:
  swarm:
    exposedByDefault: false
    watch: true
  docker:
    exposedByDefault: false
    watch: true
    network: dokploy-network
  file:
    directory: /etc/dokploy/traefik/dynamic
    watch: true
entryPoints:
  web:
    address: :80
  websecure:
    address: :443
    http3:
      advertisedPort: 443
    http:
      tls:
        certResolver: letsencrypt
api:
  insecure: true
certificatesResolvers:
  letsencrypt:
    acme:
      email: test@localhost.com
      storage: /etc/dokploy/traefik/dynamic/acme.json
      httpChallenge:
        entryPoint: web

http:
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true

/etc/dokploy/traefik/traefik.yml -> /etc/traefik/traefik.yml
/etc/dokploy/traefik/dynamic -> /etc/dokploy/traefik/dynamic
/var/run/docker.sock -> /var/run/docker.sock
```

**What it means:**

→ **Static config** (`traefik.yml`, mounted as /etc/traefik/traefik.yml): providers, entry points,
resolvers, API, logs. Changes need a Traefik restart.

→ **Dynamic config** (files in `/etc/dokploy/traefik/dynamic`, `watch: true`): routers, services,
middlewares, TLS certificates. Traefik reloads them live within seconds of a file change, no
restart. That is where your legacy routes go.

→ The directory is mounted at the *same path* inside the container, so a path like
`/etc/dokploy/traefik/dynamic/certificates/...` means the same thing on the host and in Traefik.
Files elsewhere on the host (such as /etc/letsencrypt) are invisible to Traefik.

→ Names to reuse: entry points `web` (80) and `websecure` (443), resolver `letsencrypt`,
middleware `redirect-to-https` (from the file provider, so `redirect-to-https@file`).

→ `websecure` has a default `certResolver: letsencrypt`: every router on 443 gets ACME
certificates unless a certificate is provided otherwise.

→ The email is still the placeholder if you have not set it in the UI yet (Step 41).

**Why this step (now):** writing routes against names you assumed instead of names you read is
how a router silently never matches. This takes one minute.

**Next step:** → Step 48 to write the legacy routes.
If traefik.yml has no file provider or a different directory → your Dokploy version differs; adapt
the paths in Step 48 to what you read here.

### Step 48 — Write the legacy routes file

**Goal:** one HTTP router (redirect) and one HTTPS router per kept site, all pointing at one
service: Apache on 192.0.2.10:8081.

```yaml
# ~/case-web01/legacy-apache.yml  ->  /etc/dokploy/traefik/dynamic/legacy-apache.yml
# Legacy Apache sites behind Traefik (CR-1234). Apache: 192.0.2.10:8081, plain HTTP.
http:
  routers:
    legacy-shop-http:
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https@file
      service: legacy-apache
    legacy-shop:
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`)"
      entryPoints:
        - websecure
      service: legacy-apache
      tls:
        certResolver: letsencrypt
    legacy-api-http:
      rule: "Host(`api.example.com`)"
      entryPoints:
        - web
      middlewares:
        - redirect-to-https@file
      service: legacy-apache
    legacy-api:
      rule: "Host(`api.example.com`)"
      entryPoints:
        - websecure
      service: legacy-apache
      tls:
        certResolver: letsencrypt
    # internal-only name, HTTP only today: scream-test page served by Apache (410)
    legacy-intranet:
      rule: "Host(`intranet.example.com`)"
      entryPoints:
        - web
      service: legacy-apache

  services:
    legacy-apache:
      loadBalancer:
        passHostHeader: true
        servers:
          - url: "http://192.0.2.10:8081"
```

```bash
# validate the YAML before Traefik sees it (python3-yaml is present on Ubuntu)
python3 -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1])); print("yaml ok")' ~/case-web01/legacy-apache.yml
# install atomically: write next to the watched dir, then rename into it
sudo install -m 600 ~/case-web01/legacy-apache.yml /etc/dokploy/traefik/legacy-apache.yml.tmp
sudo mv /etc/dokploy/traefik/legacy-apache.yml.tmp /etc/dokploy/traefik/dynamic/legacy-apache.yml
sleep 3; docker logs --since 1m dokploy-traefik 2>&1 | grep -E 'ERR|WRN' || echo "no errors"
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers \
  | jq -r '.[] | select(.name | startswith("legacy")) | "\(.name)\t\(.status)"'
```

```
yaml ok
no errors
legacy-api-http@file      enabled
legacy-api@file           enabled
legacy-intranet@file      enabled
legacy-shop-http@file     enabled
legacy-shop@file          enabled
```

**What it means:**

→ `passHostHeader: true` (the default, written out for clarity) forwards the original Host, so
Apache's name-based vhosts on 8081 pick the right site.

→ Traefik adds `X-Forwarded-For` (client IP), `X-Forwarded-Proto: https`, `X-Forwarded-Host` and
`X-Real-Ip`. Apache's mod_remoteip (Step 31) and `SetEnvIf` (Step 30) use them.

→ The ACME HTTP-01 challenge on port 80 is answered by Traefik itself before routers are
considered, so the redirect routers do not break certificate issuance.

→ Router names are prefixed `legacy-` so they are easy to filter in the API, the dashboard and the
access log, and cannot clash with names Dokploy generates.

→ A YAML error shows as an `ERR ... providerName=file` line, for example
`field not found, node: entrypoint` for a typo of `entryPoints`. While the file is invalid, Traefik
keeps the last valid configuration from that provider.

→ The atomic `mv` matters: an editor saving directly into the watched directory can be read
half-written.

**Why this step (now):** in the window, this is the step that ends the legacy downtime. Writing,
validating and reviewing the file days earlier means the window only needs the `install` + `mv`.

**Next step:** → Step 49 to decide how the legacy names get certificates.
If a router shows `disabled` or the log has `ERR ... providerName=file` → fix the YAML (the error
names the field) and install the file again with the same `install` + `mv`.

### Step 49 — Choose certificates: ACME or files

**Goal:** no visitor sees a certificate error during or after the cutover.

With `certResolver: letsencrypt` (Step 48), Traefik requests new certificates for the legacy names
as soon as the routers load. Until they arrive it serves its self-signed `TRAEFIK DEFAULT CERT`.
With working prerequisites (Section 9) that is seconds; if validation fails, it is an outage with
a certificate error, and with HSTS (Section 12) browsers give users no way to click through.

The zero-gap alternative: give Traefik the certificates Apache already uses (still valid for ~60
days), and switch to ACME later at a calm moment.

```bash
D=/etc/dokploy/traefik/dynamic/certificates/legacy
sudo mkdir -p "$D"
# -L copies the real files: /etc/letsencrypt/live/* are symlinks Traefik could not follow
sudo cp -L /etc/letsencrypt/live/shop.example.com/fullchain.pem "$D/shop.crt"
sudo cp -L /etc/letsencrypt/live/shop.example.com/privkey.pem   "$D/shop.key"
sudo cp -L /etc/letsencrypt/live/api.example.com/fullchain.pem  "$D/api.crt"
sudo cp -L /etc/letsencrypt/live/api.example.com/privkey.pem    "$D/api.key"
sudo chmod 600 "$D"/*.key
sudo ls -l "$D"
```

```yaml
# add to legacy-apache.yml (top level, next to "http:")
tls:
  certificates:
    - certFile: /etc/dokploy/traefik/dynamic/certificates/legacy/shop.crt
      keyFile: /etc/dokploy/traefik/dynamic/certificates/legacy/shop.key
    - certFile: /etc/dokploy/traefik/dynamic/certificates/legacy/api.crt
      keyFile: /etc/dokploy/traefik/dynamic/certificates/legacy/api.key
# and in the two HTTPS routers replace the certResolver block with:  tls: {}
```

```
-rw-r--r-- 1 root root 3749 Oct  6 06:04 api.crt
-rw------- 1 root root 1704 Oct  6 06:04 api.key
-rw-r--r-- 1 root root 3790 Oct  6 06:04 shop.crt
-rw------- 1 root root 1704 Oct  6 06:04 shop.key
```

**What it means:**

→ Traefik picks a certificate from its store by matching the SNI name against each
certificate's SANs, so shop.crt serves both shop and www.shop.

→ The sizes are those of RSA-2048 keys, matching the RSA intermediates (R10/R11) in Step 8. Certbot
2.x creates ECDSA keys by default (a key file of about 240 bytes, issued by an E-series intermediate);
both work the same way here.

→ The entry point still has a default resolver, but Traefik applies the entry point's TLS defaults
only to routers that have no `tls` section of their own, so routers with `tls: {}` do not trigger
ACME. Traefik normally also skips ACME for names a user-provided certificate already covers.
Confirm with
`sudo jq -r '.letsencrypt.Certificates[].domain.main' /etc/dokploy/traefik/dynamic/acme.json`
(the legacy names should not appear) and the Traefik log.

→ These copies never renew. Put the switch to ACME in the calendar well before the earliest
expiry (28 Nov for api): change `tls: {}` back to `certResolver: letsencrypt`, remove the
`tls.certificates` entries, and watch the new certificate arrive.

→ Dokploy's UI also has a certificates section for uploading custom certificates; it stores them
under the same dynamic directory.

| Approach | Gap at cutover | Renewal | Choose when |
|---|---|---|---|
| ACME (`certResolver: letsencrypt`) | seconds if prerequisites hold | automatic | port 80 reachable from the Internet, public DNS |
| Files from Apache | none | manual, until you switch | you want zero risk in the window, or HSTS sites |
| Internal CA files | none | your CA's process | internal-only names (no public validation possible) |

**Why this step (now):** certificates are the visible part of the cutover. Deciding before the
window removes the only failure mode users actually see as "the site is broken".

**Next step:** → Step 51 to test (Step 50 is the passthrough variant, only for Option C).
If a router's names are not covered by any copied certificate's SANs → that name falls back to ACME
or the default certificate; copy the right file or leave that name on ACME.

### Step 50 — Variant: TCP passthrough to Apache

**Goal:** (Option C only) Traefik forwards the encrypted stream for a name to Apache, which keeps
its own certificates and TLS settings.

Apache side: keep the SSL vhost but move it to an internal TLS port.

```apache
# /etc/apache2/ports.conf
Listen 192.0.2.10:8443 https
# in shop.example.com-le-ssl.conf: change  <VirtualHost *:443>  to  <VirtualHost 192.0.2.10:8443>
```

Traefik side: a TCP router matching the SNI name, with passthrough.

```yaml
# /etc/dokploy/traefik/dynamic/legacy-passthrough.yml
tcp:
  routers:
    legacy-shop-tls:
      rule: "HostSNI(`shop.example.com`) || HostSNI(`www.shop.example.com`)"
      entryPoints:
        - websecure
      service: apache-tls
      tls:
        passthrough: true
  services:
    apache-tls:
      loadBalancer:
        servers:
          - address: "192.0.2.10:8443"
```

```bash
echo | openssl s_client -connect 192.0.2.10:443 -servername shop.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -serial
sudo openssl x509 -in /etc/letsencrypt/live/shop.example.com/cert.pem -noout -serial
```

```
subject=CN = shop.example.com
issuer=C = US, O = Let's Encrypt, CN = R10
serial=04A1F3C2D9E8B7A6F5E4D3C2B1A09F8E7D6C
serial=04A1F3C2D9E8B7A6F5E4D3C2B1A09F8E7D6C
```

**What it means:**

→ The serial served on 443 equals Apache's certificate serial: the stream is reaching Apache
untouched.

→ Traefik sees only bytes: no Host header, path or status code in its logs, no middlewares.

→ Apache sees every connection coming from Traefik. To keep client IPs, enable the PROXY protocol
on both sides: on the Traefik TCP service (where exactly depends on the Traefik version; check the
TCP services section of the Traefik docs) and `RemoteIPProxyProtocol On` in the Apache vhost
(Apache 2.4.31+). Once on, that Apache port only accepts connections that start with a PROXY
header, so direct curl tests to 8443 fail by design.

→ Renewal: Traefik's own ACME HTTP challenge handler claims `/.well-known/acme-challenge/` on
port 80 with top priority, so certbot's HTTP-01 through Traefik generally does not work. Use
certbot's DNS-01 method (a plugin for your DNS provider) for passthrough sites.

**Why this step (now):** it is the escape hatch for an app that must keep its own TLS. Everything
else in this runbook assumes TLS terminates at Traefik.

**Next step:** → Step 51.
If the served serial differs from Apache's → the TCP router did not match: check the `HostSNI` names
and that no HTTP router with TLS claims the same name. If Apache refuses connections after enabling
the PROXY protocol → the Traefik side is not sending it.

### Step 51 — Test each route with curl --resolve

**Goal:** every name answers through Traefik with the right status and a verified certificate,
independent of DNS caches.

`--resolve NAME:443:IP` pins the name to an IP for one request while still sending the correct SNI
and Host header. Use it right after loading routes (it bypasses stale caches and split-horizon
DNS), on the staging VM (pin to 192.0.2.20), for names that have no DNS record yet, and for Option F
before switching DNS. More tricks:
[everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html).

```bash
IP=192.0.2.10
while read -r h p; do
  printf '%-22s %-12s ' "$h" "$p"
  curl -s -o /dev/null --max-time 10 --resolve "$h:443:$IP" \
       -w '%{http_code} verify=%{ssl_verify_result} %{time_total}s\n' "https://$h$p"
done <<'LIST'
shop.example.com /
www.shop.example.com /
api.example.com /v1/health
app.example.com /healthz
dokploy.example.com /
LIST
curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' --resolve shop.example.com:80:$IP http://shop.example.com/
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: intranet.example.com' http://$IP/
curl -sv --resolve shop.example.com:443:$IP https://shop.example.com/ -o /dev/null 2>&1 \
  | grep -E 'subject:|expire date:|issuer:|< HTTP|< server'
# websocket through Traefik -> Apache -> Node
curl -s -o /dev/null -w '%{http_code}\n' --max-time 3 --http1.1 --resolve api.example.com:443:$IP \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' 'https://api.example.com/socket.io/?EIO=4&transport=websocket'
```

```
shop.example.com       /            200 verify=0 0.412s
www.shop.example.com   /            200 verify=0 0.398s
api.example.com        /v1/health   200 verify=0 0.061s
app.example.com        /healthz     200 verify=0 0.044s
dokploy.example.com    /            200 verify=0 0.120s
301 -> https://shop.example.com/
410
*  subject: CN=shop.example.com
*  expire date: Dec  2 09:14:11 2026 GMT
*  issuer: C=US; O=Let's Encrypt; CN=R10
< HTTP/2 200
< server: Apache/2.4.58 (Ubuntu)
101
```

**What it means:**

→ Every name: `200` and `verify=0` (certificate chain and name verified).

→ Port 80 redirects to HTTPS (Traefik's `redirect-to-https`).

→ intranet returns `410`: the scream-test page from Apache. Users who still need it will call,
which is the point of a scream test.

→ The certificate expires 2 Dec: these are the file-provided Apache certificates (Step 49). With
ACME you would see a fresh expiry about 90 days out.

→ `HTTP/2 200` from Traefik with `server: Apache/2.4.58`: the client talks HTTP/2 to Traefik and the
response comes from Apache. The full chain works.

→ `101` for the websocket (`--http1.1` because the classic websocket upgrade is an HTTP/1.1
mechanism).

→ If a name shows `000` with curl error 60, or the certificate subject is `TRAEFIK DEFAULT CERT`,
no router matched that SNI or its certificate is not there yet: check the router list (Step 48)
and Step 52.

**Why this step (now):** it tests each layer (TLS, routing, Apache vhost, app) per name in seconds,
and the output pasted into the change request is your proof of success.

**Next step:** all good → Phase 8 verification matrix (Step 54). Anything failing → Step 52.

### Step 52 — Read Traefik's logs, API and dashboard

**Goal:** find why a route fails, from Traefik's point of view.

The samples below come from the later day when the legacy names are switched from file
certificates to ACME (Step 49): shop switched cleanly, api failed validation.

```bash
docker logs --since 10m dokploy-traefik 2>&1 | grep -E ' (ERR|WRN) ' | tail -n 20
docker logs --since 30m dokploy-traefik 2>&1 | grep -i acme | tail -n 5
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers/legacy-shop@file \
  | jq '{status, rule, service, tls, error}'
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/overview | jq '.http'
sudo jq -r '.letsencrypt.Certificates[].domain.main' /etc/dokploy/traefik/dynamic/acme.json
```

```
2026-10-06T06:05:01Z ERR Unable to obtain ACME certificate for domains error="unable to generate a certificate for the domains [api.example.com]: error: one or more domains had a problem:\n[api.example.com] invalid authorization: acme: error: 400 :: urn:ietf:params:acme:error:connection :: 192.0.2.10: Fetching http://api.example.com/.well-known/acme-challenge/X3k...: Timeout during connect (likely firewall problem)\n" ACME CA=https://acme-v02.api.letsencrypt.org/directory acmeCA=https://acme-v02.api.letsencrypt.org/directory domains=["api.example.com"] providerName=letsencrypt.acme routerName=legacy-api@file rule=Host(`api.example.com`)

{
  "status": "enabled",
  "rule": "Host(`shop.example.com`) || Host(`www.shop.example.com`)",
  "service": "legacy-apache",
  "tls": { "certResolver": "letsencrypt" },
  "error": null
}
{
  "routers":     { "total": 11, "warnings": 0, "errors": 0 },
  "services":    { "total": 6,  "warnings": 0, "errors": 0 },
  "middlewares": { "total": 1,  "warnings": 0, "errors": 0 }
}
dokploy.example.com
app.example.com
shop.example.com
```

**What it means:**

→ The ACME error names the exact problem: Let's Encrypt could not connect to port 80 of
192.0.2.10 for api.example.com, "likely firewall problem". The address in that message is the one
Let's Encrypt tried to reach (what public DNS returns for the name), not its own source address. On-prem that is usually the perimeter
firewall or NAT not forwarding port 80. Until it is fixed, api.example.com gets the default
certificate (or keeps the file certificate from Step 49).

→ The router is `enabled` with no error: routing is fine; only the certificate is missing.

→ `/api/overview` counts warnings and errors across all routers: a quick health number to check
after every change.

→ acme.json lists the names that already have Let's Encrypt certificates.

→ Backend failures (Apache unreachable, wrong port) do not appear as ERR lines by default. They show
as `502`/`504` in the access log, and as `dial tcp 192.0.2.10:8081: i/o timeout` (blocked by UFW)
or `connect: connection refused` (Apache not listening there) when you temporarily set the log
level to DEBUG.

To use the dashboard without exposing it, tunnel to the container's address from your laptop and
open `http://localhost:18080/dashboard/`:

```bash
docker run --rm --net container:dokploy-traefik nicolaka/netshoot ip -4 -br addr   # eth1 = docker_gwbridge address
ssh -L 18080:172.18.0.3:8080 ops@web01        # run on your laptop; 172.18.0.3 from the line above
```

To log every request (needed for the verification matrix), add an access log to the static config
and restart Traefik (a few seconds without any site, so do it in the window or at a quiet time).
Recent Dokploy versions can switch this on from the UI; check there first.

```yaml
# append to /etc/dokploy/traefik/traefik.yml, then: docker restart dokploy-traefik
accessLog:
  filePath: /etc/dokploy/traefik/dynamic/access.log
  format: json
  bufferingSize: 100
```

```bash
sudo tail -n 200 /etc/dokploy/traefik/dynamic/access.log \
  | jq -r 'select(.RouterName // "" | startswith("legacy")) | [.StartUTC, .ClientHost, .RequestHost, .RequestPath, .DownstreamStatus, ((.Duration / 1000000 | floor | tostring) + "ms")] | @tsv'
```

```
2026-10-06T06:21:14.118Z  203.0.113.77  shop.example.com  /cart/       200  84ms
2026-10-06T06:21:14.409Z  203.0.113.45  api.example.com   /v1/orders   201  37ms
```

**Why this step (now):** "it doesn't work" from curl tells you *that* a layer failed. Traefik's
log, API and access log tell you *which* router, service or certificate, so you fix the right
thing.

**Next step:** fix what the logs point to, re-run Step 51, then → Phase 8. For the general
Traefik/Dokploy failure catalogue (404, 502, certificate errors) see
[Containers playbook](26-playbook-containers-k8s.md) and the
[Dokploy troubleshooting guide](https://docs.dokploy.com/docs/core/troubleshooting).
If the rollback trigger is reached before the logs lead to a fix → Section 10.

### Phase 7 wrap-up

```
curl --resolve NAME:443:IP https://NAME/
├── TLS error / TRAEFIK DEFAULT CERT
│     ├── router for NAME missing/disabled → API router list, YAML errors (Step 48, 52)
│     └── router OK, no cert → ACME error in log (port 80, DNS, AAAA) or use file certs (Step 49)
├── 404 page not found (from Traefik) → no router matched: Host typo, wrong entryPoint, file not loaded
├── 502 / 504 → Traefik cannot reach 192.0.2.10:8081: UFW rule, Apache bind/port, Apache down
├── 301/302 loop → app HTTPS detection (Step 32)
├── 200 but wrong site → Apache default vhost / missing ServerAlias (Step 30)
└── 200 → check Apache log shows the real client IP (Step 31) → Phase 8
```

**Fix & verify:** Step 51 is all green, the router overview shows 0 errors, and the legacy names
have certificates (file or ACME).

**Rollback:** remove the route file, and Traefik drops the routes within seconds:
`sudo mv /etc/dokploy/traefik/dynamic/legacy-apache.yml /root/legacy-apache.yml.off` (for the full
rollback to Apache on 443, Section 10).

**Prevent it next time:** keep `legacy-apache.yml` in Git with the change request; prefix every
hand-written router; enable the access log on day one.

---

## 9. Phase 8 — Cutover with minimal downtime

> 📚 **Study path:** 1) Note: [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md) (TLS, SNI, DNS TTL) and [Web, HTTP & TLS](18-web-http-tls.md) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)), then *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands: Work With SSL Certificates ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 3) Video: *SSL, TLS, HTTPS Explained* (ByteByteGo, 5 min, [YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo)) · 4) Practice: test a site by name before DNS exists with `curl --resolve` ([everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html)).

**Level:** [L3 · Senior] → [L4 · Lead]. Running a short, timed window from a checklist and proving
success with a verification matrix is how seniors and leads close changes.

Goal of the phase: the short window in which ports 80 and 443 change owner, done from a
checklist, followed by a verification matrix and 30 minutes of watching.

### Why the public ports cannot overlap

The ideal cutover overlaps old and new: Apache keeps 443 while Traefik is installed and tested,
then 443 flips. That overlap works for Apache's *internal* port (Phase 5 ran 443 and 8081 side by
side for days), but not for the public ports:

- The Dokploy installer exits if anything listens on 80, 443 or 3000, on any address.
- Even a manual install could not start Traefik: `docker run -p 443:443` fails with "address
  already in use" while Apache holds `*:443`.

So the legacy downtime runs from Step 36 (Apache releases 80/443) to Step 48 (Traefik routes the
legacy names). Everything in Phases 4 to 7 exists to make that gap short: Docker pre-installed,
images pre-pulled, routes and certificates written in advance, rehearsal timed. A rehearsed gap is
typically 2 to 5 minutes. If even that is unacceptable, the zero-downtime options are F (new host,
DNS switch) or D (second IP, plain Traefik), from Phase 3.

### The timeline

| When | What | Impact |
|---|---|---|
| T-7d | Inventory + evidence (Phases 1-2), decision, change request approved | none |
| T-7d | DNS records for app and dokploy names; UFW rule for 8081 | none |
| T-5d | Apache internal listener + vhosts + mod_remoteip live and tested (Steps 28-34) | none |
| T-5d | Docker pre-installed, images pulled, installer read (Step 26, 38) | none |
| T-3d | Rehearsal + rollback on staging (Step 27) | none |
| T-1d | Notify client and partner; api-node moved to 3001 at a quiet hour (Step 35); backup B1 | seconds on api |
| T0+0 | Step 36: Apache off 80/443 | **legacy down** |
| T0+1 | Step 37: ports free; Step 39: installer | legacy down |
| T0+4 | Step 48 (+49): legacy routes and certificates in place | **legacy back** |
| T0+5 | Step 51 + Step 54 verification matrix | none |
| T0+15 | Step 41-42: admin, domain, port 3000 locked | none |
| T0+25 | Step 43-44: client app deployed | new app live |
| T0+30 to +60 | Step 55: watch; then close the change | none |

### Let's Encrypt prerequisites

Traefik's resolver uses the HTTP-01 challenge on the `web` entry point. For each name:

- **Public DNS** A record (and AAAA, if any) points at an address that reaches this Traefik.
  Let's Encrypt prefers IPv6 when an AAAA exists, so a stale or unreachable AAAA breaks validation.
- **Port 80 is reachable from the Internet** all the way to Traefik: perimeter firewall, NAT/port
  forwarding on-prem, cloud security groups. HTTP-01 always starts on port 80, even for HTTPS-only sites.
- **Internal-only names** (intranet.example.com) cannot pass HTTP-01: use DNS-01 or certificates
  from your internal CA (the same private-CA skills as your Harbor setup).
- **CAA records**, if your domain has them, must allow letsencrypt.org.
- **Clock** in sync (Step 23).
- **Rate limits**: Let's Encrypt limits failed validations per hostname per hour and duplicate
  certificates per week. While experimenting, point the resolver at Let's Encrypt's staging CA
  (`caServer` in the static config; see the ACME section of the Traefik docs).
- A real **email** on the resolver, so expiry warnings reach someone.

### Step 53 — Run the window

**Goal:** execute the change steps in order, timestamped, without improvising.

```bash
cd ~/case-web01 && script -q -a window-$(date +%F).log      # record everything
date +%T; sudo cp -a /etc/apache2/ports.conf /etc/apache2/ports.conf.pre-window
# 1. Apache off 80/443 (Step 36)
sudoedit /etc/apache2/ports.conf                              # only: Listen 192.0.2.10:8081
sudo a2dissite 000-default shop.example.com shop.example.com-le-ssl api.example.com \
  api.example.com-le-ssl docs.example.com docs.example.com-ssl intranet.example.com
sudo a2ensite intranet-retired
sudo apache2ctl configtest && sudo systemctl reload apache2; date +%T
# 2. Ports free (Step 37)
sudo ss -tulnp | grep -E ':(80|443|3000) ' || echo "80/443/3000 free"
# 3. Installer (Step 39)
sudo ADVERTISE_ADDR=192.0.2.10 DOCKER_SWARM_INIT_ARGS="--default-addr-pool 10.250.0.0/16 --default-addr-pool-mask-length 24" \
  bash ~/case-web01/dokploy-install.sh 2>&1 | tee ~/case-web01/dokploy-install.log; date +%T
docker network inspect docker_gwbridge --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'   # expect 172.18.0.0/16
# 4. Legacy routes + certificates (Step 48, 49)
sudo install -m 600 ~/case-web01/legacy-apache.yml /etc/dokploy/traefik/legacy-apache.yml.tmp
sudo mv /etc/dokploy/traefik/legacy-apache.yml.tmp /etc/dokploy/traefik/dynamic/legacy-apache.yml; date +%T
# 5. Quick check (Step 51 loop), then the matrix (Step 54)
```

```
06:00:02
Site 000-default disabled.
...
Syntax OK
06:00:41
80/443/3000 free
...
Congratulations, Dokploy is installed!
06:03:18
172.18.0.0/16
06:03:52
```

**What it means:** legacy downtime ran from 06:00:41 to 06:03:52, a little over three minutes,
matching the rehearsal. The timestamps go into the change request and the incident note.

If the docker_gwbridge subnet is not 172.18.0.0/16, update `RemoteIPInternalProxy` (Step 31) and
the UFW rule (Step 25) right now, before testing: otherwise Apache logs the proxy's IP or UFW drops
Traefik's requests (502).

**Why this step (now):** a window run from a written, rehearsed list is short and boring. A window
run from memory is where people skip the configtest.

**Next step:** → Step 54. If something fails and cannot be fixed before the rollback trigger in
the change request → Section 10.

### Step 54 — Verify every site

**Goal:** a filled-in verification matrix: for each site, status, certificate, real client IP in
Apache, the request in Traefik's log, and the app's own health.

```bash
IP=192.0.2.10
# certificate issuer and expiry as clients see them
for h in shop.example.com www.shop.example.com api.example.com app.example.com dokploy.example.com; do
  printf '%-22s ' "$h"
  echo | openssl s_client -connect $IP:443 -servername "$h" 2>/dev/null \
    | openssl x509 -noout -issuer -enddate | tr '\n' ' '; echo
done
# real client IPs reach Apache (not 172.18.x.x)
sudo tail -n 3 /var/log/apache2/shop_access.log
# the same traffic in Traefik's access log
sudo tail -n 3 /etc/dokploy/traefik/dynamic/access.log | jq -c '{ClientHost, RequestHost, RequestPath, DownstreamStatus, RouterName}'
# partner traffic is flowing again (Ctrl-C after a few lines)
sudo tail -f /var/log/apache2/api_access.log | grep --line-buffered '^203\.0\.113\.45 '
# 5xx since the window started, compare with the baseline from Step 15/16
sudo awk '$4 >= "[06/Oct/2026:06:00" && $9 ~ /^5/' /var/log/apache2/api_access.log | wc -l
```

```
shop.example.com       issuer=C = US, O = Let's Encrypt, CN = R10 notAfter=Dec  2 09:14:11 2026 GMT
www.shop.example.com   issuer=C = US, O = Let's Encrypt, CN = R10 notAfter=Dec  2 09:14:11 2026 GMT
api.example.com        issuer=C = US, O = Let's Encrypt, CN = R11 notAfter=Nov 28 06:02:41 2026 GMT
app.example.com        issuer=C = US, O = Let's Encrypt, CN = R11 notAfter=Jan  4 06:24:30 2027 GMT
dokploy.example.com    issuer=C = US, O = Let's Encrypt, CN = R10 notAfter=Jan  4 06:21:09 2027 GMT

203.0.113.77 - - [06/Oct/2026:06:05:12 +0000] "GET /cart/ HTTP/1.1" 200 48211 "-" "Mozilla/5.0 ..." proto=https
203.0.113.81 - - [06/Oct/2026:06:05:13 +0000] "GET /product/blue-mug/ HTTP/1.1" 200 51023 "-" "Mozilla/5.0 ..." proto=https

{"ClientHost":"203.0.113.77","RequestHost":"shop.example.com","RequestPath":"/cart/","DownstreamStatus":200,"RouterName":"legacy-shop@file"}

203.0.113.45 - - [06/Oct/2026:06:04:03 +0000] "POST /v1/orders HTTP/1.1" 201 312 "-" "PartnerSync/3.2" proto=https

2
```

**What it means:**

→ Every name presents a trusted certificate with a sane expiry (legacy names: the file
certificates, new names: fresh Let's Encrypt ones).

→ Apache logs real client IPs and `proto=https`: mod_remoteip and the forwarded headers work. If
you see `172.18.0.3` instead, the RemoteIPInternalProxy subnet is wrong.

→ Traefik's access log shows the same request on router `legacy-shop@file`: you can now follow a
request through both layers.

→ The partner's first order arrived at 06:04:03, 11 seconds after the routes loaded.

→ Two 5xx since 06:00, against a baseline of about 20 a day: normal. A jump would mean a new
problem (timeouts, upload limits: Section 12).

Fill the matrix (one row per site) and attach it to the change request:

| Site | Status / path | Certificate | Client IP in Apache log | Traefik router | App health |
|---|---|---|---|---|---|
| shop, www.shop | 200 `/`, 301 on http | LE R10, 2 Dec (file) | yes, proto=https | legacy-shop@file | cart + checkout page load, wp-cron ran |
| api | 200 `/v1/health`, 101 websocket | LE R11, 28 Nov (file) | yes | legacy-api@file | partner POSTs 201 |
| intranet | 410 retired page | n/a (HTTP) | yes | legacy-intranet@file | scream test running |
| docs | not routed (DNS elsewhere) | n/a | n/a | none | monitor check removed |
| app | 200 `/healthz` | LE, 90 days | n/a (no Apache) | Dokploy-generated | Dokploy shows running |
| dokploy | 200, port 3000 closed | LE, 90 days | n/a | dokploy | admin login works |

**Why this step (now):** "it works for me in the browser" is not verification. A matrix with
evidence per site is what lets you close the change with confidence and defend it later.

**Next step:** → Step 55, watch for 30 minutes.
If any row is red → Step 52 for that name. If partner traffic does not appear within a few minutes →
call the partner contact; their side may cache DNS or pin the old certificate.

### Step 55 — Watch for 30 minutes

**Goal:** catch the problems that only appear with real traffic: slow endpoints, uploads,
scheduled jobs, certificates still being issued.

```bash
# terminal 1: errors as they happen, both layers
sudo tail -F /var/log/apache2/shop_error.log /var/log/apache2/api_error.log
# terminal 2: Traefik warnings and errors
docker logs -f --since 1m dokploy-traefik 2>&1 | grep --line-buffered -E ' (ERR|WRN) '
# terminal 3: every few minutes
docker ps --format '{{.Names}} {{.Status}}'
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
sudo grep -c 'wp-cron.php' /var/log/apache2/shop_access.log      # increases every 5 min = cron fixed
```

```
dokploy-traefik Up 31 minutes
dokploy.1.m2k7c1x9q0zv8r3d5t6y4wn1b Up 31 minutes
dokploy-postgres.1.h8s1v4n2l5c7x0q9w3e Up 31 minutes
client-app-x7k2qd.1.k2j9x0c3v8b7n6m5l4k3j Up 8 minutes (healthy)

NAME                     CPU %     MEM USAGE / LIMIT
dokploy-traefik          0.31%     38.2MiB / 7.7GiB
dokploy.1.m2k7...        0.84%     312.5MiB / 7.7GiB
dokploy-postgres.1.h8s1  0.05%     61.3MiB / 7.7GiB

17
```

**What it means:** containers stable (no restarts), Traefik uses almost nothing, Dokploy itself is
the biggest consumer (expected), and the wp-cron counter grows: the cron fix from Phase 5 works.

**Why this step (now):** most cutover problems appear within the first half hour, when the team is
still there and the rollback is still cheap.

**Next step:** close the change (send the matrix), then the follow-ups in Section 12 (certbot,
switch legacy names to ACME before 28 Nov) and Section 13.
If errors rise above the baseline or containers restart → Section 11 to find the layer, then Step 52.
If the rollback trigger is met → Section 10.

### Phase 8 wrap-up

```
After Step 36, before Step 48 completes:  sites down — keep moving, follow the list
Installer failed?            → fix fast (Step 39 notes) or roll back (Section 10)
Routes loaded, Step 51 red?  → Step 52 decision tree; rollback trigger reached? → Section 10
Matrix green?                → watch 30 min (Step 55) → close change → follow-ups
```

**Fix & verify:** the matrix is complete and green, no new 5xx above baseline, the client and
partner confirm.

**Rollback:** Section 10.

**Prevent it next time:** the next migration on another server reuses this timeline; only the
names change.

---

## 10. Rollback

> 📚 **Study path:** 1) Note: Step 27 of this module (rehearsal) and [Services & systemd](07-services-systemd.md) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Restart Policies ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)), so you know why a stopped container comes back · 3) KodeKloud: *Fundamentals of SRE* — Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 4) Practice: on your staging VM, roll back from backup B1 with a stopwatch and diff the listeners as in Step 58.

**Level:** [L4 · Lead]. Deciding when to stop fixing forward, rolling back calmly and proving it
worked is a lead's call. Juniors and mid-levels should still run the commands in rehearsals.

Goal: Apache back on 80 and 443 exactly as before the window, in about five minutes, while keeping
Dokploy's data for a later retry. Decide with the trigger written in the change request (for
example: a kept site failing for more than 15 minutes, or partner calls failing), not with hope.

Two restore points exist: **B1** (just before the window: Apache with 80/443 *and* 8081, api-node
on 3001) for a rollback during or soon after the window, and **B0** (the original state) for
abandoning the whole project.

### Step 56 — Free 80, 443 and 3000

**Goal:** stop everything Dokploy publishes, so Apache can bind its ports, without deleting data.

```bash
docker update --restart=no dokploy-traefik    # otherwise a Docker restart or reboot brings it back on 80/443
docker stop dokploy-traefik
docker service scale dokploy=0                # frees 3000 and stops the UI from recreating Traefik
docker service scale client-app-x7k2qd=0      # optional: the new app is unreachable anyway
sudo ss -tulnp | grep -E ':(80|443|3000) ' || echo "80/443/3000 free"
```

```
dokploy-traefik
dokploy-traefik
dokploy scaled to 0
overall progress: 0 out of 0 tasks
verify: Service dokploy converged
client-app-x7k2qd scaled to 0
80/443/3000 free
```

**What it means:** the public ports are free. `dokploy-postgres`, the volumes, `/etc/dokploy` and
the Swarm stay untouched, so retrying later is a `docker service scale dokploy=1`,
`docker update --restart=always dokploy-traefik` (undo the policy change) and
`docker start dokploy-traefik` away.

**Why this step (now):** Apache cannot start on 443 while docker-proxy holds it; this is the
mirror image of Step 37.

**Next step:** → Step 57.
If a port is still held → `docker ps --filter publish=PORT` names the container; a dokploy-traefik
that reappears means the dokploy service is still running.

### Step 57 — Restore Apache

**Goal:** Apache's configuration from backup B1, listening on 80 and 443 again.

```bash
B1=/root/backup-web01-20261006-0545            # the pre-window backup
sudo mv /etc/apache2 /etc/apache2.failed-$(date +%H%M)   # keep the failed config for the postmortem
sudo tar -xzpf "$B1/etc-apache2.tgz" -C /
sudo apache2ctl configtest
sudo systemctl restart apache2                 # clean start after swapping the whole config tree
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :8081 )'
```

```
Syntax OK
State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
LISTEN 0      511        192.0.2.10:8081       0.0.0.0:*     users:(("apache2",pid=40112,fd=8),...)
LISTEN 0      511                 *:80               *:*     users:(("apache2",pid=40112,fd=4),...)
LISTEN 0      511                 *:443              *:*     users:(("apache2",pid=40112,fd=6),...)
```

For a full rollback to **B0** (original state) also put the Node app back on 3000 *before*
restarting Apache, because B0's vhosts proxy to 3000:

```bash
sudo cp -a /opt/api/.env.bak /opt/api/.env && sudo systemctl restart api-node
sudo tar -xzpf /root/backup-web01-20261003-1002/etc-apache2.tgz -C /    # B0, after moving /etc/apache2 aside as above
```

**What it means:** Apache owns 80 and 443 again (plus the harmless internal port from B1). Moving
the current /etc/apache2 aside instead of deleting it keeps the evidence of what went wrong.

**Why this step (now):** with the ports free, the fastest path back to service is the last known
good configuration, restored as a whole rather than edited back by hand under pressure.

**Next step:** → Step 58 to prove the rollback.
If configtest fails on the restored files → a module or certificate path changed since the backup;
read the error and fix it before restarting. If the restart fails with `Address already in use` →
back to Step 56.

### Step 58 — Verify the rollback

**Goal:** the listeners and vhosts match the saved "before" picture, and every site answers.

```bash
B1=/root/backup-web01-20261006-0545
# the backup lives under /root (mode 700): read it with sudo too
diff <(sudo awk 'NR>1 {print $1, $5}' "$B1/listeners.txt" | sort -u) <(sudo ss -ltnup | awk 'NR>1 {print $1, $5}' | sort -u)
diff <(sudo grep -E 'namevhost|alias' "$B1/vhosts.txt") <(sudo apache2ctl -S 2>&1 | grep -E 'namevhost|alias') && echo "vhosts identical"
for h in shop.example.com api.example.com; do
  curl -s -o /dev/null -w "$h %{http_code} verify=%{ssl_verify_result}\n" "https://$h/"
done
```

```
> tcp *:2377
> tcp *:7946
> udp 0.0.0.0:4789
> udp *:7946
vhosts identical
shop.example.com 200 verify=0
api.example.com 200 verify=0
```

**What it means:** the only differences are the Swarm ports (dockerd's 2377 and 7946, and the
kernel's VXLAN socket on 4789/udp for the overlay network that dokploy-postgres still uses), which
exist because Swarm is still initialized (expected and firewalled). Vhosts are identical and both sites answer with valid
certificates. Tell the client and partner, and write down why you rolled back while it is fresh.

**Why this step (now):** a rollback is a change too. It is not done until verified with the same
rigour as the forward change.

**Next step:** postmortem of the attempt (Section 13), fix the cause on staging, schedule a new
window.
If the listeners differ beyond the Swarm ports, or a site fails → compare with B0 and fix it
before you announce the rollback as complete.

### Removing Dokploy completely

Only if the project is abandoned. These commands destroy Dokploy's database and any app data
in its volumes.

> ⚠️ `docker volume rm` and deleting `/etc/dokploy` are irreversible. Back up the
> `dokploy-postgres` volume and `/etc/dokploy` first, and prefer moving directories aside over
> `rm -rf`. Check the uninstall notes in the [Dokploy docs](https://docs.dokploy.com/) for your version.

```bash
docker service rm dokploy dokploy-postgres client-app-x7k2qd
docker rm -f dokploy-traefik
docker swarm leave --force
docker volume ls | grep -i dokploy              # review before deleting anything
# after a backup and an explicit decision only:
#   docker volume rm dokploy-postgres dokploy
#   sudo mv /etc/dokploy /root/etc-dokploy-removed-$(date +%F)
```

### Rollback wrap-up

```
Trigger reached?
├── no  → keep fixing forward, re-check at the next checkpoint
└── yes → Step 56 free ports → Step 57 restore B1 (or B0 + api on 3000)
          → Step 58 diff listeners/vhosts + curl → notify → postmortem
```

**Prevent it next time:** rehearse the rollback, not only the change (Step 27). A rollback you have
never run is a second, untested change.

---

## 11. Logs map for this setup

> 📚 **Study path:** 1) Note: [Logs & Journal](06-logs-journal.md) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Logging Driver ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 3) KodeKloud: *Grafana Loki* ([course](https://kodekloud.com/courses/grafana-loki)), later, to search all these logs in one place · 4) Practice: on staging, follow one request through Traefik, Apache and the backend as shown below.

**Level:** [L2 · Mid]. Starting at the outermost log and following one timestamp inward is the core
L2 troubleshooting habit.

After the migration, one request crosses up to four components. Know where each writes:

| Component | What you find there | Where / command |
|---|---|---|
| Traefik (process) | startup, provider and config errors, ACME results | `docker logs -f --tail 100 dokploy-traefik` |
| Traefik access log | every request: client, host, path, status, router, duration | `/etc/dokploy/traefik/dynamic/access.log` (after enabling, Step 52) |
| Traefik API | routers, services, middlewares and their errors | `docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers` |
| Apache per vhost | access with real client IP (`%a`), errors per site | `/var/log/apache2/shop_access.log`, `shop_error.log`, `api_*.log` |
| Apache other | vhosts without own log, main errors, internal default | `other_vhosts_access.log`, `error.log`, `internal_default_access.log` |
| Apache service | start, stop, reload, startup errors | `journalctl -u apache2` |
| PHP-FPM | pool errors, slow requests, max_children reached | `journalctl -u php8.3-fpm`, `/var/log/php8.3-fpm.log` |
| Node api | app output | `journalctl -u api-node -f` |
| Dokploy UI/server | Dokploy's own errors | `docker service logs -f dokploy` |
| Dokploy app (runtime) | stdout/stderr of the app | Logs tab, or `docker service logs -f client-app-x7k2qd` |
| Dokploy deployments | build and deploy logs | Deployments tab; on disk under `/etc/dokploy/logs/` on recent versions (verify on yours) |
| Swarm tasks | why a task failed or was rescheduled | `docker service ps --no-trunc SERVICE` (Error column) |
| Docker daemon | pulls, network and Swarm errors | `journalctl -u docker` |
| Firewall drops | UFW blocking Traefik to 8081, scanners on 3000 | `journalctl -k -g 'UFW BLOCK'`, `iptables -L DOCKER-USER -n -v` counters |
| Certificates | which names have ACME certs | `sudo jq -r '.letsencrypt.Certificates[].domain.main' /etc/dokploy/traefik/dynamic/acme.json` |

### Follow one request through every layer

```bash
# 1. find it in Traefik's access log (status 502 on the api, for example)
sudo jq -c 'select(.RequestHost=="api.example.com" and .DownstreamStatus==502) | {StartUTC, ClientHost, RequestPath, Duration}' \
  /etc/dokploy/traefik/dynamic/access.log | tail -n 3
# 2. the same second in Apache (client IP + path)
sudo grep '06/Oct/2026:09:12:4' /var/log/apache2/api_access.log | grep '203.0.113.45' | tail -n 3
# 3. Apache's error for it
sudo grep 'Oct 06 09:12:4' /var/log/apache2/api_error.log | tail -n 3
# 4. the backend at that time
journalctl -u api-node --since '2026-10-06 09:12:30' --until '2026-10-06 09:13:00' --no-pager
```

```
{"StartUTC":"2026-10-06T09:12:41.30Z","ClientHost":"203.0.113.45","RequestPath":"/v1/orders","Duration":61204113902}
203.0.113.45 - - [06/Oct/2026:09:12:41 +0000] "POST /v1/orders HTTP/1.1" 502 341 "-" "PartnerSync/3.2" proto=https
[Tue Oct 06 09:12:41.311204 2026] [proxy_http:error] [pid 40211:tid 1402] (104)Connection reset by peer: [client 203.0.113.45:48862] AH01102: error reading status line from remote server 127.0.0.1:3001
Oct 06 09:12:41 web01 node[24388]: Error: ECONNRESET at TLSSocket.socketOnEnd ...
```

→ Traefik saw a 502 that took 61 s; Apache logged the same request with the real client IP and
a 502; Apache's error log says the Node app reset the connection; Node's journal shows its own
upstream connection failing. The fault is in the app, as in the pre-migration baseline (Step 16),
not in Traefik. This is the habit to build: start at the outermost log, follow the timestamp
inward, stop at the first layer that reports the error itself.

---

## 12. Gotchas

> 📚 **Study path:** 1) Note: [Docker, Dokploy/Traefik and Kubernetes incidents](26-playbook-containers-k8s.md) · 2) Docs: Docker [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) (KodeKloud does not cover DOCKER-USER) · 3) KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — System Hardening: UFW Firewall Basics ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) · 4) Practice: on a test VM, `ufw deny 8000`, publish a container on 8000, reach it from another host, then block it in DOCKER-USER.

**Level:** [L2 · Mid] → [L3 · Senior]. Each gotcha is a typical ticket in the week after a
migration. A mid-level engineer fixes them; a senior plans for them before the window.

Each one has bitten real migrations like this. Symptom first, then the cause and the fix.

### UFW does not filter published Docker ports

**Symptom:** `ufw status` shows no rule for 3000 (or a `deny`), yet port 3000 answers from the
Internet. **Cause:** Docker DNATs published ports in the nat table and forwards them through its
own chains before UFW's input rules are consulted. **Fix:** publish only what must be public, bind
test ports to loopback (`-p 127.0.0.1:18000:8000`), and filter container traffic in `DOCKER-USER`
(Step 42). Reference: [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).

### Port 3000 exposed to the Internet

**Symptom:** scanners in the DOCKER-USER counters within minutes; worst case, a stranger registers
the first Dokploy account. **Fix:** claim the admin immediately, filter 3000 to the admin network,
then `docker service update --publish-rm "published=3000,target=3000,mode=host" dokploy` once the
domain works (Steps 41-42). Re-check after every Dokploy upgrade:
`sudo ss -ltnp 'sport = :3000'`.

### Apache still reachable on its internal port

**Symptom:** `nc -zv 192.0.2.10 8081` from another LAN host connects, bypassing Traefik (and its
TLS, logs and future access rules). **Cause:** Apache bound to 0.0.0.0, or the UFW rule allows more
than docker_gwbridge, or UFW is inactive. **Fix:** bind the specific address (Step 28), keep UFW's
default deny with only the interface-scoped allow (Step 25), and test from a second host: the
connection must time out.

```bash
# from another host on the LAN (expected: timeout)
nc -zv -w 3 192.0.2.10 8081
# on web01: what UFW dropped
sudo journalctl -k -g 'UFW BLOCK' --since '10 min ago' | grep 'DPT=8081' | tail -n 2
```

```
nc: connect to 192.0.2.10 port 8081 (tcp) timed out: Operation now in progress
Oct 06 07:02:11 web01 kernel: [UFW BLOCK] IN=ens18 OUT= SRC=198.51.100.40 DST=192.0.2.10 PROTO=TCP SPT=51122 DPT=8081 ...
```

### certbot renewals after Apache leaves 443

**Symptom:** certbot's timer starts failing (`certbot renew --dry-run` reports the Apache plugin
cannot find a vhost on port 80, or the challenge fails), and its deploy hook keeps reloading Apache
for nothing. **Cause:** the `apache` authenticator needs Apache serving port 80 publicly, and
Traefik now answers `/.well-known/acme-challenge/` itself. **Fix:** once Traefik's ACME
certificates serve the legacy names (Step 49 switch), stop certbot renewing them without deleting
anything:

```bash
sudo certbot renew --dry-run 2>&1 | tail -n 5          # see it fail first, for the record
sudo mv /etc/letsencrypt/renewal/shop.example.com.conf /etc/letsencrypt/renewal/shop.example.com.conf.disabled
sudo mv /etc/letsencrypt/renewal/api.example.com.conf  /etc/letsencrypt/renewal/api.example.com.conf.disabled
sudo certbot certificates                               # the disabled names are no longer listed
```

certbot only reads `*.conf` in the renewal directory, so renaming is a reversible "off switch".
Until you switch to ACME, the file certificates from Step 49 do **not** renew: put the earliest
expiry date (28 Nov) in the calendar with a two-week margin.

### HSTS turns a short certificate gap into a hard outage

**Symptom:** browsers show a certificate error with no "proceed anyway" option for shop.example.com.

**Cause:** the site sent `Strict-Transport-Security`; browsers then refuse any invalid certificate
for that name, including Traefik's default certificate during the seconds before ACME succeeds.

**Fix:** check before the window and use file certificates (Step 49) for HSTS names. Also make sure
the header survives: if Apache set it only in the SSL vhost, your internal vhost copy lost it.

```bash
curl -sI https://shop.example.com/ | grep -i strict-transport-security
sudo grep -Rn 'Strict-Transport-Security' /etc/apache2/sites-available/ /etc/apache2/conf-available/
```

```
strict-transport-security: max-age=31536000; includeSubDomains
/etc/apache2/sites-available/shop.example.com-le-ssl.conf:18:    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
```

→ Copy that `Header always set` line into `shop.example.com-internal.conf` (or set it once in a
Traefik headers middleware for the router; not both, or the header is sent twice).

### Websockets

Traefik proxies websocket upgrades without configuration. The middle hop is the risk: Apache must
upgrade too (`proxy_wstunnel` with `ws://` ProxyPass, or `ProxyPass ... upgrade=websocket` on
2.4.47+), as in the api vhost. Idle websockets are cut by the shortest idle timeout in the chain;
socket.io pings keep them alive, other clients may need their own keepalive. Test with the 101 check
in Step 51.

### Big uploads

**Symptom:** uploads that worked before now fail with 413, or die after about a minute. Every hop
has its own limit:

| Hop | Limit | Default to know | Error |
|---|---|---|---|
| Traefik entry point | `transport.respondingTimeouts.readTimeout` in traefik.yml | Traefik v3 sets a read timeout (60 s at the time of writing; check the docs for your version) | upload cut, client sees a reset or 5xx |
| Traefik | body size | no limit unless a Buffering middleware sets one | 413 from Traefik |
| Apache | `LimitRequestBody` | 1 GiB since 2.4.53 | 413 from Apache |
| PHP | `upload_max_filesize`, `post_max_size` | 2M / 8M stock php.ini, often raised | PHP warning, empty `$_FILES` |
| Node / app | framework body limit | app specific | 413 from the app |

Find which hop answered: Traefik's access log status versus Apache's access log status for the same
request (Section 11).

### The timeout chain

Every hop waits for the next one; the shortest timeout wins, and the error appears one hop above
where the time ran out.

```
client ── Traefik ───────────── Apache ────────────── PHP-FPM / Node
          entry point read/write   Timeout 300 (Ubuntu)  max_execution_time 30 (PHP)
          + forwarding timeouts    ProxyTimeout          request_terminate_timeout
          to the backend           (defaults to Timeout) app's own server timeout
```

A slow report page in PHP stops at 30 s (PHP's limit) and Apache returns 500/503. A Node call that
hangs is cut by Apache after `ProxyTimeout` with a 502/504, and Traefik passes that through. Raise a
timeout only on purpose and on every hop at once; usually fix the slow endpoint. See
[Slow system playbook](23-playbook-slow-system.md) for finding where time goes.

### .htaccess rules that change meaning behind a proxy

- `RewriteCond %{HTTPS} off` is now always true → loops (Step 32).
- `%{SERVER_PORT}` is not the socket's port: with `UseCanonicalName Off` (the default) it comes
  from the Host header, and Traefik sends none, so it falls back to the default port of the
  `ServerName` scheme: 443 with `ServerName https://...` (Step 30), 80 without it, in which case
  `%{SERVER_PORT} ^80$` checks loop as well. Keep the scheme in `ServerName` and
  `UseCanonicalName Off`; with `UseCanonicalPhysicalPort On` the value would become 8081.
- `Require ip` and `RewriteCond %{REMOTE_ADDR}` allowlists see Traefik's IP unless mod_remoteip is
  configured, so they either block everyone or (if they allow private ranges) allow everyone.

```bash
sudo grep -RniE '%\{(HTTPS|SERVER_PORT|REMOTE_ADDR)\}|Require (ip|host)|UseCanonical' /var/www/*/.htaccess /etc/apache2/sites-available/
```

### PHP sessions and cookies

Apps that think they run on HTTP may set cookies without the `Secure` flag, or refuse to set
secure cookies and loop on login. The `HTTPS=on` environment variable (Step 30) fixes PHP's view.
Apps that bind a session to the client IP log everyone out once at the cutover (the IP they see
changes) and, without mod_remoteip, would treat all users as one IP. Session files stay where they
were (`/var/lib/php/sessions`), so nobody else is affected.

### Cron jobs, monitoring and anything that calls localhost

After the move, `http://127.0.0.1/` and `http://localhost/` reach Traefik (which redirects to
HTTPS or returns 404), not Apache. Every cron job, health check, `apache2ctl status`/`fullstatus`
and monitoring probe that used them must target `http://192.0.2.10:8081/` with the right Host
header (Step 19, Phase 5 wrap-up). Monitoring that checks a site by IP (`https://192.0.2.10/`) now
gets Traefik's 404 and default certificate: change it to check by name.

### Default vhost surprises

Before: a request with an unknown Host or a bare IP got Apache's first vhost (on 443 that was
api, Step 4). Some clients depend on that without knowing it (a partner calling `https://192.0.2.10/`
with certificate checks disabled). After: Traefik answers 404 for unknown hosts. Find them *before*
the migration by logging the Host header for a few days:

```bash
# /etc/apache2/conf-available/hostcheck.conf (temporary): a2enconf hostcheck + reload
#   LogFormat "%{Host}i %a %>s \"%r\"" hostcheck
#   GlobalLog ${APACHE_LOG_DIR}/hostcheck.log hostcheck
# GlobalLog (2.4.19+) also logs vhosts that have their own CustomLog; a global CustomLog would not.
sudo awk '{print $1}' /var/log/apache2/hostcheck.log | sort | uniq -c | sort -rn
```

```
 182904 api.example.com
  60122 shop.example.com
   1201 www.shop.example.com
     88 192.0.2.10
     12 web01.example.com
```

→ 88 requests by bare IP and 12 by the server's hostname: find the clients (`grep '^192.0.2.10 '`)
and give them a proper name before the cutover, or add a Traefik router for them.

### IPv6 listeners

Apache's `*:443` accepted IPv6 too. Docker also publishes `[::]:443`, but without IPv6 enabled in
Docker those connections pass through docker-proxy, and Traefik sees the proxy's address instead
of the client's. If your names have AAAA records: test with `curl -6`, check the client IPs in the
logs, and remember Let's Encrypt validates over IPv6 first. If they do not, nothing changes.

### Traefik's dashboard port

Dokploy can publish the Traefik dashboard on 8080 from its UI. Had Apache taken 8080 as its
internal port, enabling the dashboard later would fail with "address already in use" (or Apache
would fail at the next restart). That is why this runbook uses 8081. Better: leave the dashboard
unpublished and use the SSH tunnel from Step 52.

### Dokploy recreates its Traefik container

Dokploy manages `dokploy-traefik` itself (for example when you change Traefik settings in the UI or
upgrade). Files under `/etc/dokploy/traefik/` survive because they are bind-mounted; anything you
changed on the container itself (extra `-p` bindings, `--add-host`, a restart policy) does not.
Keep all customisation in the dynamic files or in Dokploy's settings.

### /etc/dokploy is world-writable

The installer sets `chmod 777 /etc/dokploy`. Any local user can then drop a file into Traefik's
dynamic directory and add routes. On a server where several people have shell accounts, limit
shell access and watch that directory (for example with an auditd rule).

### RHEL/Rocky differences

The unit is `httpd`, configs are in `/etc/httpd/conf/httpd.conf` and `/etc/httpd/conf.d/*.conf`
(no a2ensite: rename files or move them), logs in `/var/log/httpd/`, and firewalld instead of UFW
(Docker inserts its rules there too). SELinux adds two checks: Apache may only bind ports labelled
`http_port_t` (8081 is already labelled `transproxy_port_t` in the stock policy, so `-a` fails with
"already defined"; modify it instead: `sudo semanage port -m -t http_port_t -p tcp 8081`, and check
with `sudo semanage port -l | grep -w 8081`), and Apache proxying to a local
port needs `sudo setsebool -P httpd_can_network_connect 1`. Denials show in
`sudo ausearch -m avc -ts recent`.

---

## 13. After the incident

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Incident Management: Blameless Postmortem Culture, then Root Cause Analysis ([postmortem notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page), [RCA notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page)) · 2) Note: [Learn: Git, CI/CD, IaC, SRE](33-learn-cicd-iac-sre.md) and [Career ladder](40-career-ladder.md) · 3) Reading: the postmortem chapters of the [Google SRE book](https://sre.google/sre-book/table-of-contents/) · 4) Practice: write the 5-line note and a one-page postmortem for your real 81/444 change.

**Level:** [L4 · Lead]. Notes, runbooks and postmortems turn one incident into team knowledge, and
into proof of your level when you apply for the next role.

The work is not finished when the sites are green. Three things turn this incident into experience
you (and your team) can reuse: a 5-line note, a runbook, and the follow-ups.

### The 5-line incident note

Your learning plan's habit for every incident, even a small one: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time.

```
Symptom:     Dokploy installer: "something is already running on port 80"; Apache held 80/443
             for 4 undocumented vhosts, a Node API held 3000.
Wrong guess: "Stop Apache and install" — would have taken shop and the partner API down for hours.
Evidence:    ss -ltnup + apache2ctl -S + 14 days of access logs: shop 3.9k/day, api 18k/day
             (partner 203.0.113.45), docs DNS elsewhere, intranet only monitoring.
Fix:         Apache -> 192.0.2.10:8081 behind Dokploy's Traefik (file-provider routes, mod_remoteip),
             Node 3000 -> 3001, docs retired, intranet scream test; 3 min legacy downtime.
Next time:   Run the port inventory (ss + unit + vhosts + logs) BEFORE promising a deploy date.
```

### Runbook and postmortem

- **Runbook:** copy this module's phases into the team's runbook repo, replace the example names with
  placeholders, and keep the real files next to it (`legacy-apache.yml`, internal vhosts, the
  change request, the verification matrix). Your learning plan suggests a public repo of
  sanitized runbooks as proof of skill; documentation addresses and example.com names make that safe.
- **Postmortem:** only needed if something hurt (the window overran, a rollback, a partner outage).
  Use the structure from the Google SRE book: summary, impact, timeline, root cause, what went well,
  what went badly, where you got lucky, action items with owners. Read
  [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) and the
  postmortem chapters from the [SRE book table of contents](https://sre.google/sre-book/table-of-contents/).
- **Change record:** close the change request with the timestamps from Step 53, the matrix from
  Step 54 and the links to both. The format follows
  [GitLab's change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/).

### Follow-ups checklist

| Follow-up | When | Why |
|---|---|---|
| Switch legacy names from file certificates to `certResolver: letsencrypt` | before 14 Nov | file copies expire 28 Nov / 2 Dec |
| Disable certbot renewals for migrated names (rename renewal confs) | right after the switch | stop failing renewals and useless reloads |
| Persist the DOCKER-USER rules (oneshot unit or ufw after.rules) | this week | lost on reboot otherwise |
| Back up `/etc/dokploy` and the `dokploy-postgres` volume | this week | Dokploy's state is now production data |
| Retire intranet after 4 weeks of scream test, archive /var/www/intranet | +4 weeks | owner agreed, no complaints |
| Archive /var/www/docs, remove the docs monitor check, delete its vhost files | +1 week | dead config |
| Containerize api (Dockerfile, GitLab CI to Harbor, Dokploy app) | next sprint | Option E, your L3 exit test |
| Containerize shop (WordPress Compose app, uploads volume, DB) | after api | Apache's last tenant |
| Retire Apache (`disable --now`, `mask`) when the last route leaves it | after shop | end state |
| Update CMDB, monitoring and the server README with the new layout | this week | the next person must not repeat Phase 1 blind |

### Self-check and exit test

Answer without looking, then check the step in brackets. If you miss more than two questions at
your level, re-read those steps before you try the timed tasks.

**Questions**

1. [L1 · Junior] `ss` shows three `apache2` PIDs on `*:443`. Which one is the parent, and how do
   you get from it to the unit, the config and the logs? (Steps 1–3)
2. [L1 · Junior] A vhost has no `CustomLog` line. Where do its requests go on Ubuntu? (Step 12)
3. [L1 · Junior] Why is "no real hits in the last 14 days" not proof that a site is unused? (Steps 13, 19)
4. [L2 · Mid] Why can the Traefik container not reach Apache on 127.0.0.1:8081, and which bind
   address works instead? (Step 28)
5. [L2 · Mid] One IP serves four HTTPS sites. What does the front proxy use to choose the
   certificate, and what to choose the vhost or router? (Phase 3)
6. [L2 · Mid] `RewriteCond %{HTTPS} off` worked for years. Why does it loop behind Traefik, and what
   are two fixes? (Step 32)
7. [L2 · Mid] `ufw deny 3000` is active, yet port 3000 answers from the Internet. Why, and where do
   you filter instead? (Steps 25, 42)
8. [L3 · Senior] When is `RemoteIPInternalProxy` the right choice over `RemoteIPTrustedProxy`? (Step 31)
9. [L3 · Senior] Name four conditions for Traefik to get a Let's Encrypt certificate for a legacy
   name over HTTP-01. (Phase 8)
10. [L3 · Senior] Traefik answers 404 for one name and 502 for another. What does each one tell
    you? (Phase 7 wrap-up)
11. [L3 · Senior] Why does this runbook give Apache port 8081 and not 8080? (Gotchas)
12. [L4 · Lead] What is a rollback trigger, and why is it written before the window? (Step 22)
13. [L4 · Lead] Why are there two backups, B0 and B1, and when do you restore each one? (Steps 21, 57)

**Timed practical tasks (test VM or KodeKloud playground only, never production)**

| Level | Time | Task | Pass when |
|---|---|---|---|
| [L1 · Junior] | 10 min | On a VM where Apache serves two vhosts on 443 and an app listens on 3000, fill the Phase 2 inventory table | every listener has a unit, a config file and a log path |
| [L2 · Mid] | 15 min | From rotated access logs, report the last real hit and real requests per day for each vhost, monitoring excluded | your numbers match a hand count on a small log |
| [L2 · Mid] | 20 min | Move Apache to an internal port with internal vhosts, adding before removing | `curl -H 'Host: ...'` on the internal port returns 200 before 80/443 are removed |
| [L3 · Senior] | 60 min | Put a Traefik v3 container on 80/443 with a file-provider route to that Apache | `curl --resolve` returns 200 with `verify=0` and Apache logs real client IPs |
| [L3 · Senior] | 20 min | Break it three ways: Apache bound to 127.0.0.1, the UFW rule for the internal port removed, a typo in one `Host` rule | from curl and Traefik's logs alone you match 502, 504 (after a long wait) and 404 to the right cause |
| [L4 · Lead] | 15 min | Roll back to Apache on 80/443 from your backup | the listener and vhost diffs show only the expected differences |
| [L4 · Lead] | 30 min | Write the change request (with a rollback trigger) and the 5-line incident note for the exercise | a colleague could run the window from it without asking you |

**Exit criterion:** you have finished this module at your level when you pass every task tagged
with your level and the levels below it, in the time given, using only this handbook.

### What to study next

The layers this incident touched, in the order that would have made it fastest:

- [Who owns this port? Inventory, logs and dispatching](22-playbook-ports-inventory.md): the
  general version of Phases 1-2 for any service, including containers and socket activation.
- [Site down: DNS, routing, TLS, proxy, app](25-playbook-site-down.md): the layer walk you use when
  Step 51 is red.
- [Docker, Dokploy/Traefik and Kubernetes incidents](26-playbook-containers-k8s.md): 404, 502,
  certificate and DNS failures inside Dokploy.
- [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md): sockets, SNI, Host headers and
  certificates from first principles.
- [Learn: Apache, Nginx, Traefik, Dokploy, reverse proxies](29-learn-webservers-proxies.md): vhosts,
  routers, forwarded headers and why proxies buffer.
- [Learn: Docker zero to hero](30-learn-docker.md): published ports, bridge and overlay networks,
  Swarm services, Compose, logs.
- [Deployment patterns: port shifting and beyond](35-deployment-patterns.md): your real 81/444
  fix analysed, how to finish it with Traefik, and the pattern catalogue for the next server.
- [Career ladder](40-career-ladder.md): where each skill in this case sits from fresher to lead,
  and what to learn next for your stage.
- Reference modules for the commands used here: [Network](02-network.md),
  [Services & systemd](07-services-systemd.md), [DNS](08-dns.md),
  [Docker reference](14-docker-containers.md), [Web, HTTP & TLS](18-web-http-tls.md).

Drills from your learning plan that rehearse exactly this case:

- Make Traefik return 502 on purpose with a wrong port (or a missing UFW rule for 8081), then find
  and fix it from Traefik's logs alone ([Traefik docs: Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/)).
- Write the change request for disabling system Apache in GitLab's format before you do it at work.
- L3 exit test: move one Apache workload into a container behind Dokploy, built by a GitLab CI
  pipeline that pushes to Harbor, with a written rollback you have actually tested
  ([GitLab CI quick start](https://docs.gitlab.com/ci/quick_start/),
  [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting)).
- Read why an app server wants a buffering proxy in front of it:
  [Deploying Gunicorn](https://gunicorn.org/deploy/) and
  [What is a reverse proxy?](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/).
