# 29 — Learn: Web Servers & Reverse Proxies (Apache, Nginx, Traefik, Dokploy)

Everything that sits between a browser and your application: who accepts the
connection, who holds the certificate, who decides which app a request goes to,
and what each hop adds, removes or times out. The module is built around your
real migration: an Ubuntu server where Apache serves several vhosts and owns
443, and Dokploy (Traefik on 80/443, its UI on 3000) needs those ports. When
you finish it you should be able to read any proxy config cold, predict which
backend a request lands on, and move sites from one proxy to another with a
tested rollback.

Command references live in [Web, HTTP & TLS](18-web-http-tls.md) and
[Docker](14-docker-containers.md). The incident walk-throughs live in the
[Apache 443 / Dokploy case study](21-case-apache-443-dokploy.md), the
[port inventory playbook](22-playbook-ports-inventory.md) and the
[site-down playbook](25-playbook-site-down.md). This module is the "why"
underneath them.

**Career stages served:** mainly Mid-level → Senior ([L2 · Mid] → [L3 · Senior]
on the Ops Ladder). Juniors ([L1 · Junior]) get a safe path through Apache
basics, ports and inventory; Leads ([L4 · Lead/SRE]) get the design, cutover and
game-day material in 6.2, section 7 and section 9. Freshers ([L0 · Fresher])
should finish [Learn: Linux](27-learn-linux.md) and
[Learn: Networking](28-learn-networking.md) first. Every topic carries its tag,
and the table in section 0 tells you where to start.

> ⚠️ Every command here is an example to run on **your** servers or a **test VM**.
> Sample outputs are illustrative (Ubuntu 22.04/24.04, Apache 2.4.5x, nginx 1.2x,
> Traefik v3, a recent Dokploy). Exact wording changes between versions.
> Uppercase words (HOST, PORT, CONTAINER, DOMAIN, APPNAME) are placeholders.

---

## 0. How to use this module

> 📚 **Study path (whole module):** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server section (Apache Web Server, IPs and Ports, and their labs) ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · 2) KodeKloud: *Nginx For Beginners* — Intermediate Config ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 3) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress module, Traefik lessons ([course](https://kodekloud.com/courses/kubernetes-networking)) · 4) Docs: [Traefik](https://doc.traefik.io/traefik/) and [Dokploy](https://docs.dokploy.com/) (KodeKloud has no Traefik-on-Docker or Dokploy course) · 5) Practice: the capstone in section 8, then the Ops Ladder L3 drill "Traefik 502 from logs alone". Each area below starts with its own, more precise line.

### Who this module is for

The stage names match the [career ladder](40-career-ladder.md) used across the
handbook. Find your stage, start with its topics, and use section 9 to decide
when to move up.

| Stage | Tag | What you do with this module | Start with |
|---|---|---|---|
| Fresher (0–1 yr) | [L0 · Fresher] | Not yet: finish Linux and networking basics, then read 1.1–1.2 for the vocabulary | [Learn: Linux](27-learn-linux.md), [Learn: Networking](28-learn-networking.md) |
| Junior (1–2 yrs) | [L1 · Junior] | Read and operate Apache safely: roles, ports, vhosts, configtest and reload, logs, inventory | 1.1–1.3, 2.1–2.4, 2.9, 2.11–2.12, 8.1 |
| Mid-level (2–4 yrs) | [L2 · Mid] | Debug any proxy chain with evidence: 404/502/503/504, TLS, headers, timeouts, redirect loops; nginx | Sections 1–3, 4.3–4.4, 4.9, the capstone (8) |
| Senior (4–7 yrs) | [L3 · Senior] | Own the edge: Traefik, Dokploy, certificates, the migration plan and its rollback | Sections 4–7 |
| Senior/Lead/SRE (5+ yrs) | [L4 · Lead/SRE] | Choose and defend the edge design, run the cutover as a change, alert on it, run game days, coach others | 6.2, 7.5–7.6, 9.3 |

You already work at about L2 on-prem: skim the Junior topics, do the capstone,
and put your real hours into sections 4–7.

### Learning path

Work through the topics in this order. The level tags match the Ops Ladder
(L0 Foundations, L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE) and the
career stages above.

| # | Topic | Level · stage | Why at this point |
|---|---|---|---|
| 1 | 1.1–1.3 Roles, Host/SNI, who owns a port | [L1 · Junior] → [L2 · Mid] | The vocabulary for everything else, and the root of your Apache/443 incident |
| 2 | 1.4–1.5 TLS termination, X-Forwarded headers | [L2 · Mid] | Every proxy migration breaks one of these two first |
| 3 | 1.6–1.7 Timeouts, buffering, WebSockets, HTTP/2-3 | [L2 · Mid] | Explains 502 vs 504 and "works for small files only" |
| 4 | 2.1–2.4 Apache processes, layout, vhost matching, docroots | [L1 · Junior] → [L2 · Mid] | You inherited Apache, so learn to read it before you move it |
| 5 | 2.5–2.9 Apache proxy, TLS, rewrite, real IP, logging | [L2 · Mid] | The directives that decide whether the migration is smooth |
| 6 | 2.10–2.13 Apache tuning, toolkit, inventory, AH codes | [L2 · Mid] | Operating, inventorying and "dispatching" Apache safely |
| 7 | 3.1–3.6 Nginx | [L2 · Mid] | The most common proxy you will meet elsewhere, and SadServers nginx scenarios |
| 8 | 4.1–4.9 Traefik | [L3 · Senior] | The proxy Dokploy runs for you; you must debug it without the UI |
| 9 | 5.1–5.8 Dokploy | [L3 · Senior] | Your target platform: where it keeps things and how it breaks |
| 10 | 6.1–6.3 HAProxy, choosing a proxy, Kubernetes ingress | [L3 · Senior] | Choosing tools on purpose, and the bridge to your CKA work |
| 11 | 7.1–7.6 Migration patterns and cutover | [L3 · Senior] → [L4 · Lead/SRE] | The plan for the Apache → Dokploy move, with rollback |
| 12 | 8 Capstone lab, 9 Self-check, 10 Where to go next | [L2 · Mid] / [L3 · Senior] exit | Proof you can do it under time pressure |

Prerequisites: systemd, `ss`, `journalctl` and file permissions from
[Learn: Linux](27-learn-linux.md), and TCP, DNS, the TLS handshake and HTTP
basics from [Learn: Networking](28-learn-networking.md).

### Study method for every topic

For each ### topic below, do these five steps in order:

1. Read the note here: concept, key terms, then "See it on a real system".
2. Do the matching KodeKloud course lesson (pointer in the 📚 line at the top of each area).
3. Optional: a short video on the same topic if something still feels fuzzy.
4. Do the hands-on lab on a **test VM**: build it, break it on purpose, fix it.
5. Read the related playbook so you know what the incident version looks like.

Each topic uses the same layout: **Concept** → **Key terms** → **See it on a
real system** (safe, read-only) → **Hands-on lab (test VM only)** → **How it
breaks** → **Why it matters for troubleshooting** → **Next step**.

### Your lab environment

One disposable VM is enough for almost everything in this module (Dokploy wants
a clean VM of its own, snapshot C below):

| Item | Value used in the labs |
|---|---|
| OS | Ubuntu Server 24.04 LTS (22.04 works; note version differences) |
| Size | 2 vCPU, 4 GB RAM, 30 GB disk (Dokploy's documented minimum is 2 GB RAM / 30 GB disk) |
| IP | 192.168.56.10 on a host-only network (replace with yours) |
| Names | site-a.example.com, site-b.example.com, whoami.example.com |
| Tools | `sudo apt install -y apache2 curl jq tcpdump` plus Docker Engine with the compose plugin |

You do not need DNS for the labs. Use `curl -H 'Host: NAME'` for HTTP and
`curl --resolve NAME:443:IP` for HTTPS, or add the names to `/etc/hosts` on
your laptop (and remove them afterwards).

Two snapshots make the labs painless:

| Snapshot | State | Used by |
|---|---|---|
| A: stock | Ubuntu + `apache2` on port 80 with `000-default` | Labs 1.1, 1.3, 1.6, 1.7, 2.1, 2.2 (they use `http://localhost/`) |
| B: capstone | After steps 8.1–8.2: Apache vhosts on 8080, Traefik on 80/443 | Labs 1.2, 1.4, 1.5, 2.3 onwards, sections 4, 6, 7 and 8 |
| C: fresh | A second VM (or a clean snapshot) with nothing on 80, 443 or 3000 | Dokploy labs 5.1–5.8 |

If you run an "A" lab on snapshot B, replace `http://localhost/` with
`http://127.0.0.1:8080/` and add `-H 'Host: site-a.example.com'`.

> ⚠️ Take a VM snapshot before every lab. "Revert snapshot" is the fastest and
> safest rollback you will ever have. Never practise on the client's server.

---

## 1. Reverse proxy fundamentals

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *IPs and Ports* and its lab ([lesson notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Implement Reverse Proxies and Load Balancers* ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 3) Read: [What is a reverse proxy?](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/) and [Deploying Gunicorn](https://gunicorn.org/deploy/) · 4) Video (for 1.4): ByteByteGo *SSL, TLS, HTTPS Explained* ([YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo), 5 min) · 5) Note: HTTP and TLS refresher in [Learn: Networking](28-learn-networking.md) · 6) Practice: labs 1.1–1.7, plus [everything curl: name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html) for `--resolve`.

### 1.1 Roles: web server, app server, proxy, LB, gateway

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

A browser speaks HTTP over TCP. Several different jobs can sit on the other end
of that connection, and one product often does several of them:

- **Web server**: maps URLs to files on disk and serves them (HTML, CSS,
  images), and hands dynamic requests to something else. Apache and nginx.
- **Application server**: runs your code. gunicorn/uvicorn (Python), php-fpm
  (PHP, speaks FastCGI, not HTTP), Node's built-in server, Tomcat (Java).
  It should never face the internet directly.
- **Reverse proxy**: accepts client connections on behalf of servers behind it,
  picks a backend by Host name and path, forwards the request and relays the
  answer. The client never talks to the backend. Traefik, nginx, Apache
  (mod_proxy), HAProxy.
- **Load balancer**: a reverse proxy whose main job is spreading load over many
  identical backends and taking dead ones out with health checks. Layer 4 (TCP)
  or layer 7 (HTTP).
- **API gateway**: a layer-7 proxy plus API policy: authentication (JWT, API
  keys), per-consumer rate limits, request transformation, versioning.
- **Forward proxy** (the opposite direction): sits in front of *clients*, like a
  corporate Squid on 3128. That is what `http_proxy` points at. Do not confuse
  it with a reverse proxy.

```
             Internet / LAN
                   │  TCP :443 (TLS)
                   ▼
   ┌───────────────────────────────────┐
   │ Reverse proxy (Traefik / Apache)  │  owns :80/:443, holds certificates,
   │ picks a backend by Host and path  │  logs every request, adds X-Forwarded-*
   └───────┬────────────────┬──────────┘
           │ HTTP :8000     │ FastCGI (unix socket or :9000)
           ▼                ▼
    gunicorn (Python)    php-fpm (PHP)       app servers: run code,
           │                │                never face the internet
           ▼                ▼
       PostgreSQL / Redis / files on disk
```

Why app servers sit behind a proxy:

- **Slow clients.** A gunicorn sync worker handles one request at a time. A phone
  on a weak link uploading 10 MB holds that worker for the whole upload. A
  buffering proxy (nginx) receives the full request first, then hands it to the
  app in milliseconds. Gunicorn's deployment docs say exactly this.
- **TLS in one place**: certificates, renewals, protocols and ciphers.
- **Many apps, one IP**: only one process can own IP:443 (topic 1.3).
- **Static files** are served by the proxy without waking the app.
- **Hygiene and safety**: body-size limits, header normalisation, rate limits,
  hiding backend versions.
- **Zero-downtime deploys**: the proxy shifts traffic from old to new backend.
- **php-fpm cannot speak HTTP at all**: something must translate HTTP to FastCGI.

**Key terms**

| Term | Meaning |
|---|---|
| Upstream / backend / origin | The server the proxy forwards to |
| Frontend / entrypoint / listener | The socket the proxy accepts clients on |
| Hop | One TCP connection in the chain; each hop has its own timeouts and logs |
| L4 vs L7 | L4 forwards TCP bytes without reading them; L7 parses HTTP and can route on Host, path and headers |
| Vhost / server block / router | Apache / nginx / Traefik names for "the config for one site" |

**See it on a real system**

```bash
# Who listens on the usual web and app-server ports, and which program is it?
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 or sport = :8000 or sport = :9000 )'
# php-fpm usually listens on a unix socket instead of a TCP port
sudo ss -lxp | grep -i php
# Running services that look like web servers, proxies or app servers
systemctl list-units --type=service --state=running | grep -Ei 'apache|httpd|nginx|php.*fpm|gunicorn|uwsgi|node|tomcat|traefik|haproxy'
# The Server header often (not always) names the program that answered
curl -sI https://app.example.com | grep -i '^server'
```

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      2048       127.0.0.1:8000       0.0.0.0:*     users:(("gunicorn",pid=2210,fd=5),("gunicorn",pid=2209,fd=5))
LISTEN 0      511                *:80               *:*     users:(("apache2",pid=1305,fd=4),("apache2",pid=1304,fd=4),("apache2",pid=1301,fd=4))
LISTEN 0      511                *:443              *:*     users:(("apache2",pid=1305,fd=6),("apache2",pid=1304,fd=6),("apache2",pid=1301,fd=6))
```

- `127.0.0.1:8000` gunicorn → an app server bound to loopback: only a local proxy can reach it. That is correct.
- `*:80` and `*:443` apache2 → Apache holds both web ports on every address (IPv4 and IPv6). It is the front door.
- Several PIDs on one socket → Apache's parent and children share the listening socket (topic 2.1).

**Hands-on lab (test VM only)**

**Step 1.** Start a tiny app server on loopback (any directory with a file in it):

```bash
mkdir -p ~/app && echo 'hello from the app server' > ~/app/index.html
cd ~/app && python3 -m http.server 8000 --bind 127.0.0.1
```

**Step 2.** In a second terminal, make Apache a reverse proxy for `/app/`:

```bash
sudo a2enmod proxy proxy_http
sudo tee /etc/apache2/conf-available/lab-proxy.conf >/dev/null <<'EOF'
ProxyPass        /app/ http://127.0.0.1:8000/
ProxyPassReverse /app/ http://127.0.0.1:8000/
EOF
sudo a2enconf lab-proxy
sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s http://localhost/app/          # hello from the app server
```

**Step 3.** Break it: stop the python server (Ctrl-C) and request again.

```bash
curl -si http://localhost/app/ | head -1        # HTTP/1.1 503 Service Unavailable
sudo tail -n 3 /var/log/apache2/error.log
```

```
[proxy:error] [pid 2412:tid 139...] (111)Connection refused: AH00957: HTTP: attempt to connect to 127.0.0.1:8000 (127.0.0.1) failed
[proxy_http:error] [pid 2412:tid 139...] [client 127.0.0.1:44312] AH01114: HTTP: failed to make connection to backend: 127.0.0.1
```

→ Apache answers **503** when it cannot connect to a backend. nginx and Traefik
answer **502** for the same failure. Knowing which proxy produces which code
tells you which hop is talking.

**Step 4.** Fix it: start the python server again and retry immediately. You may
still get 503 for up to 60 seconds: after a failure Apache puts the backend
"worker" in an error state and does not retry it until `retry` (default 60 s)
expires. Add `retry=0` to the `ProxyPass` line for single-backend sites, reload,
and test again. Clean up with `sudo a2disconf lab-proxy && sudo systemctl reload apache2`.

**How it breaks**

| Symptom | Likely cause | First command | Playbook |
|---|---|---|---|
| 502/503 from the proxy | Backend down, wrong port, bound to the wrong address | `curl -v http://127.0.0.1:BACKEND_PORT/` on the proxy host | [Site down](25-playbook-site-down.md) |
| The wrong site answers | Host name not matched, default vhost served | `sudo apache2ctl -S` | Topic 2.3 |
| Slow only for big uploads | No buffering proxy in front of a sync app server | proxy and app logs side by side | Topic 1.6 |
| Backend reachable from the internet | App bound to `0.0.0.0` and not firewalled | `sudo ss -ltnp` | [Port inventory](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting**

Every web incident becomes "which hop failed?". Knowing the roles tells you
whose log to open: the proxy's access log shows the status code and how long the
upstream took; the app's log shows the exception. The status code itself often
names the hop (Apache 503 vs Traefik 502).

**Next step**

Topic 1.2: how one proxy on one IP knows which of your sites a request is for.

### 1.2 One IP, many sites: Host header and SNI

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Plain version: one IP and one port, many websites. HTTP/1.1 requires every
request to carry a `Host:` header naming the site; the proxy reads it and picks
the matching vhost, server block or router. HTTP/2 carries the same value in the
`:authority` pseudo-header.

HTTPS has a chicken-and-egg problem: the proxy must choose a certificate
**before** it can read any HTTP, because the HTTP is encrypted. So the client
sends the name in clear text inside the TLS ClientHello. That field is **SNI**
(Server Name Indication). The proxy uses SNI to pick the certificate, then the
Host header to pick the site.

```
client                                    proxy on 192.0.2.10:443
  │ TCP SYN → :443 ─────────────────────────►│
  │ TLS ClientHello  SNI=crm.example.com ───►│ choose certificate for crm.example.com
  │◄─────────── ServerHello + certificate ───│
  │ GET / HTTP/1.1                           │
  │ Host: crm.example.com ──────────────────►│ choose vhost/router by Host
  │                                          └──► forward to the crm backend
```

When nothing matches, every product has a default, and it is rarely what you
want:

| Product | No Host match | No SNI match |
|---|---|---|
| Apache | First vhost defined for that IP:port | Certificate of the first `*:443` vhost |
| nginx | `default_server` for that listen socket, else the first server block | Certificate of that default server |
| Traefik | `404 page not found` | Self-signed `TRAEFIK DEFAULT CERT` |

**Key terms**

| Term | Meaning |
|---|---|
| Host header | Site name in the HTTP request, used for vhost/router selection |
| SNI | Site name in the TLS ClientHello, used for certificate selection (and TCP routing) |
| ALPN | Also in the ClientHello: which protocol to speak after TLS (`h2`, `http/1.1`) |
| Default vhost | What answers when no name matches |
| 421 Misdirected Request | The server refuses a request whose Host does not fit the TLS connection it arrived on |

**See it on a real system**

```bash
# Same IP, two sites: only the Host header changes
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' -H 'Host: site-a.example.com' http://192.0.2.10/
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' -H 'Host: site-b.example.com' http://192.0.2.10/
# HTTPS without DNS: --resolve keeps SNI and Host consistent
curl -sv --resolve site-a.example.com:443:192.0.2.10 https://site-a.example.com/ -o /dev/null 2>&1 | grep -E 'Connected|subject:|HTTP/'
# Which certificate does the server send for a known name, and for an unknown one?
openssl s_client -connect 192.0.2.10:443 -servername site-a.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject
openssl s_client -connect 192.0.2.10:443 -servername nothing.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject
# Watch SNI on the wire (needs: sudo apt install tshark)
sudo tshark -i any -f 'tcp port 443' -Y 'tls.handshake.type == 1' -T fields -e ip.src -e tls.handshake.extensions_server_name
```

```
subject=CN = site-a.example.com
subject=CN = TRAEFIK DEFAULT CERT
```

→ The second line is the tell-tale of "no router or certificate matches this
name" on Traefik. On Apache you would instead see the certificate of whichever
443 vhost loads first, which is how a client ends up seeing *another customer's*
certificate.

**Hands-on lab (test VM only)**

**Step 1.** Build the two-vhost Apache from capstone step 8.1 (or any two vhosts; the commands below use 8.1's port 8080, so adjust the port if yours differ).

**Step 2.** Request a name that is not configured:

```bash
curl -s -H 'Host: random.example.com' http://127.0.0.1:8080/
```

→ You get site A, because the first vhost is the default. On a shared server
that means any hostname pointed at your IP shows a real customer site.

**Step 3.** Fix it with an explicit catch-all that loads first (file names load
in alphabetical order, and `000-catchall` sorts before `site-a`):

```bash
sudo tee /etc/apache2/sites-available/000-catchall.conf >/dev/null <<'EOF'
<VirtualHost *:8080>
    ServerName catchall.invalid
    Redirect 404 /
    ErrorLog  ${APACHE_LOG_DIR}/catchall-error.log
    CustomLog ${APACHE_LOG_DIR}/catchall-access.log combined
</VirtualHost>
EOF
sudo a2ensite 000-catchall && sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: random.example.com' http://127.0.0.1:8080/   # 404
curl -s -H 'Host: site-a.example.com' http://127.0.0.1:8080/                                     # still site A
```

**How it breaks**

| Symptom / error text | Cause | First command |
|---|---|---|
| The wrong site's content | Host matched nothing, default vhost answered | `sudo apache2ctl -S`, then `curl -H 'Host: NAME'` |
| `curl: (60) SSL: no alternative certificate subject name matches target host name` | SNI matched no certificate, default certificate served | `openssl s_client -connect IP:443 -servername NAME` |
| Browser shows `TRAEFIK DEFAULT CERT` | No Traefik router with TLS for that name, or ACME failed | Traefik logs, topic 4.7 |
| `421 Misdirected Request` | HTTP/2 connection reused for a name the certificate or vhost does not cover, or SNI and Host differ | `curl -v --http1.1` to compare |
| `https://192.0.2.10/` shows the wrong certificate | No SNI is sent when you connect to an IP | Always test by name with `--resolve` |

**Why it matters for troubleshooting**

Name-based routing happens **inside one process**. That is why Traefik must own
443 for *all* names on the server, and why your Apache vhosts cannot keep 443
"just for their sites" once Dokploy arrives. It is also why `curl https://IP/`
proves nothing: test by name.

**Next step**

Topic 1.3: what "owning a port" means in the kernel, and why two programs cannot share 443.

### 1.3 Who owns IP:443: sockets and binding

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

A listening socket is the tuple (protocol, local IP, port). The kernel delivers
each new connection to exactly one listening socket, and `bind()` fails with
`EADDRINUSE` ("Address already in use") if the tuple is taken. The wildcard
address `0.0.0.0:443` (or `[::]:443`, which on Linux also accepts IPv4 by
default) **overlaps every specific address** on the host. So:

- Apache `Listen 443` (shown as `*:443`) and Docker `-p 443:443` (`0.0.0.0:443`)
  can never coexist.
- Two programs *can* coexist on 443 if **each** binds a **different specific IP**
  (Apache on `192.0.2.10:443`, Traefik on `192.0.2.11:443`). That needs a second
  IP on the host, and neither side may use the wildcard.
- TCP 443 and UDP 443 are different sockets. Dokploy's Traefik publishes both
  (UDP 443 is HTTP/3).
- Ports below 1024 need root or `CAP_NET_BIND_SERVICE`. That is why Apache's
  parent runs as root and its children as `www-data`.
- `SO_REUSEPORT` lets several sockets of the *same* program share a port for
  load spreading. It is not a way for two different products to split 443.

```
          kernel TCP listen table (simplified)
  ┌───────────────────────┬────────────────────────────┐
  │ local address:port    │ owner                      │
  ├───────────────────────┼────────────────────────────┤
  │ *:80                  │ apache2 (parent runs root) │  wildcard: covers 192.0.2.10,
  │ *:443                 │ apache2                    │  127.0.0.1 and every other IP
  │ 127.0.0.1:8000        │ gunicorn                   │
  └───────────────────────┴────────────────────────────┘
  docker-proxy wants 0.0.0.0:443   → EADDRINUSE ✗
  anything wants 192.0.2.11:443    → EADDRINUSE ✗ (the wildcard already covers it)
```

There is a second, sneakier owner: **boot order**. If both Apache and Traefik are
set to start at boot, whichever starts first wins 443 and the other fails or
restart-loops. After a migration, `systemctl stop apache2` is not enough; you
must also `disable` it.

**Key terms**

| Term | Meaning |
|---|---|
| Wildcard bind | `0.0.0.0` / `[::]` / `*`: every address on the host |
| `EADDRINUSE` | errno 98, "Address already in use" |
| docker-proxy | The userland helper Docker starts for each published port (plus iptables/nftables NAT rules) |
| Socket activation | systemd holds the port and starts the service on the first connection (`systemctl list-sockets`) |

**See it on a real system**

```bash
sudo ss -ltnup 'sport = :443'              # TCP and UDP listeners on 443, with process
sudo lsof -nP -iTCP:443 -sTCP:LISTEN       # same question, answered by lsof
systemctl list-sockets --all | grep -E ':(80|443)\b'   # is systemd holding the port?
ip -br addr                                # which IPs does this host own?
ps -o user,pid,ppid,cmd -C apache2         # root parent plus www-data children
systemctl is-enabled apache2 docker        # who will grab ports at the next boot?
```

```
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp   LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1305,fd=6),("apache2",pid=1304,fd=6),("apache2",pid=1301,fd=6))
```

→ `*:443` is the wildcard. Until Apache stops listening there, nothing else on
this host can bind TCP 443 on any address.

**Hands-on lab (test VM only)**

**Step 1.** With Apache running and SSL enabled (`sudo a2enmod ssl && sudo systemctl restart apache2`), try to take 443 with Docker:

```bash
sudo docker run --rm -p 443:80 nginx:alpine
```

```
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint ...:
failed to bind host port for 0.0.0.0:443:172.17.0.2:80/tcp: address already in use
```

That is the wording of Docker Engine 28 and later. Older engines (27 and
before) say `Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use`.

**Step 2.** Coexist with a second IP. Add a temporary address (lost at reboot),
pin Apache to the first IP, and publish Docker on the second:

```bash
ip -br addr                                                  # note your interface name, e.g. enp0s8
sudo ip addr add 192.168.56.11/24 dev enp0s8                 # temporary second IP
sudo sed -i 's/^\(\s*\)Listen 443$/\1Listen 192.168.56.10:443/' /etc/apache2/ports.conf
sudo apache2ctl configtest && sudo systemctl restart apache2 # Listen changes need a restart
sudo ss -ltnp 'sport = :443'                                 # now 192.168.56.10:443, not *:443
sudo docker run -d --name lab443 -p 192.168.56.11:443:80 nginx:alpine
sudo ss -ltnp 'sport = :443'                                 # two owners, two specific IPs
```

**Step 3.** Clean up: `sudo docker rm -f lab443`, restore `Listen 443` in
`ports.conf`, restart Apache, `sudo ip addr del 192.168.56.11/24 dev enp0s8`.

**How it breaks**

| Error text | Meaning | First command |
|---|---|---|
| `(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443` then `AH00451: no listening sockets available, shutting down` | Apache cannot get 443: another program, **or an overlapping `Listen` in Apache's own config** (e.g. `Listen 443` plus `Listen 192.0.2.10:443`; an exact duplicate line is caught earlier by configtest as `Cannot define multiple Listeners on the same IP:port`) | `sudo ss -ltnp 'sport = :443'`, then `grep -Rn '^\s*Listen' /etc/apache2/` |
| `failed to bind host port for 0.0.0.0:443:...: address already in use` (Docker 28+) or `Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use` (older) | A container wants a port a host process holds | `sudo ss -ltnp 'sport = :443'` |
| Dokploy installer: `Error: something is already running on port 443` (or 80, 3000) | Its pre-flight check found a listener | [Case study 21](21-case-apache-443-dokploy.md) |
| Everything worked until a reboot, then Traefik restart-loops | Apache was only stopped, not disabled, and won the boot race | `systemctl is-enabled apache2` |
| `nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)` | Same problem, nginx wording | `sudo ss -ltnp 'sport = :80'` |

**Why it matters for troubleshooting**

This is your incident in one sentence: Dokploy's Traefik needs the wildcard on
80 and 443 and Apache already had it. The decision is never "how do I share
443" but "which single proxy owns 443, and how do the others sit behind it"
(section 7).

**Next step**

Topic 1.4: once one proxy owns 443, where should TLS actually end?

### 1.4 TLS termination, passthrough and re-encryption

**Level:** [L2 · Mid]

**Concept**

The question is *where the TLS session is decrypted*:

```
TERMINATION   client ══TLS══► proxy ──HTTP──► backend      proxy holds cert + key, sees HTTP
PASSTHROUGH   client ══TLS═════════════════► backend      proxy routes TCP by SNI only, sees nothing
RE-ENCRYPT    client ══TLS══► proxy ══TLS═══► backend      proxy decrypts, then opens a new TLS session
```

- **Termination** (most common, Dokploy's default): the proxy holds certificate
  and key, decrypts, and forwards plain HTTP over loopback or a private network.
  Because it can read HTTP, it can route by path, add headers, redirect,
  compress and log URLs.
- **Passthrough**: the proxy never decrypts. It peeks at SNI, picks a backend and
  splices the TCP streams. The backend holds the certificate. The proxy cannot
  see paths or headers, cannot add `X-Forwarded-For` (use PROXY protocol
  instead) and cannot redirect. Use it when the backend *must* own the TLS:
  end-to-end client certificates, compliance, or, in your migration, **keeping
  Apache's existing certificates while Traefik takes over 443**.
- **Re-encryption**: termination plus a second TLS session to the backend. The
  proxy still sees HTTP, and the traffic stays encrypted on the wire. The proxy
  must trust the backend's certificate (private CA) or be told to skip
  verification (lab only).

| | Termination | Passthrough | Re-encryption |
|---|---|---|---|
| Who holds the public certificate | Proxy | Backend | Proxy (backend has its own too) |
| Route by path / add headers / redirect | Yes | No (SNI only) | Yes |
| Client IP at backend | `X-Forwarded-For` | PROXY protocol only | `X-Forwarded-For` |
| Traefik | HTTP router with `tls` | TCP router, `tls.passthrough: true` | HTTP router + service `scheme: https` + serversTransport |
| Apache | `SSLEngine on` in the vhost | Not possible (Apache is L7) | `SSLProxyEngine on` + `ProxyPass / https://...` |
| nginx | `listen 443 ssl` | `stream` module with `ssl_preread` | `proxy_pass https://...` + `proxy_ssl_*` |

**Key terms**

| Term | Meaning |
|---|---|
| Certificate chain | Leaf + intermediates the server must send; the client has the root |
| mTLS | The client also presents a certificate |
| PROXY protocol | A small header the proxy prepends to a TCP stream carrying the client IP; both sides must enable it |
| `insecureSkipVerify` | Traefik's "don't verify the backend certificate"; acceptable only in labs |

**See it on a real system**

```bash
# What does the edge present? (subject, issuer, validity)
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
# On the proxy host: does the backend speak plain HTTP or TLS?
curl -sv  http://127.0.0.1:8443/ -o /dev/null 2>&1 | tail -3
curl -skv https://127.0.0.1:8443/ -o /dev/null 2>&1 | grep -E 'SSL connection|subject:'
```

Recognise the mismatch messages, they are unmistakable:

```
# plain HTTP sent to a TLS port (Apache answers):
Reason: You're speaking plain HTTP to an SSL-enabled server port.
# plain HTTP sent to a TLS port (nginx answers):
400 The plain HTTP request was sent to HTTPS port
# TLS sent to a plain-HTTP port (curl's error):
curl: (35) error:0A00010B:SSL routines::wrong version number
```

**Hands-on lab (test VM only)**

Do this after the capstone setup (8.1–8.2), so Traefik already fronts Apache.

**Step 1.** Re-encryption. Enable `mod_ssl` and the snakeoil site on Apache
(`sudo a2enmod ssl && sudo a2ensite default-ssl`), add `Listen 8443` to
`ports.conf` (the capstone's file holds only `Listen 8080`), change the
`<VirtualHost _default_:443>` line in `default-ssl.conf` to 8443, restart, then point
the Traefik service at `https://host.docker.internal:8443`. Request through
Traefik: you get `500 Internal Server Error`, and Traefik's log (at DEBUG level)
mentions `tls: failed to verify certificate: x509: ...`. With the snakeoil
certificate the reason is usually `certificate is valid for VM-HOSTNAME, not
host.docker.internal` (Go checks the name first); a private-CA certificate with
the right name gives `certificate signed by unknown authority` instead.

**Step 2.** Fix it the lab way: add a serversTransport to the dynamic file and
reference it from the service:

```yaml
http:
  serversTransports:
    lab-skip-verify:
      insecureSkipVerify: true      # LAB ONLY. In production use rootCAs: [/path/ca.crt] (+ serverName if the cert name differs from the URL host)
  services:
    apache:
      loadBalancer:
        serversTransport: lab-skip-verify
        servers:
          - url: "https://host.docker.internal:8443"
```

**Step 3.** Passthrough: replace the HTTP routers for one name with a TCP router
(full example in topic 4.8). Now `openssl s_client -servername site-a.example.com`
shows *Apache's* snakeoil certificate, not Traefik's.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Traefik 500, log says `x509: certificate signed by unknown authority` (or `certificate is valid for X, not Y`) | Re-encrypting to a backend with a private or self-signed certificate, or one whose name differs from the URL host | `rootCAs` (and `serverName`) in a serversTransport (or skip verify in labs) |
| Backend answers 400 "plain HTTP ... SSL-enabled server port" | Proxy speaks HTTP to a TLS backend | Use `https://` in the backend URL |
| Traefik 500 with `tls: first record does not look like a TLS handshake` in its log; nginx 502 with `SSL_do_handshake() failed ... wrong version number` | Proxy speaks TLS to a plain-HTTP backend | Use `http://` |
| Passthrough site: no HTTP→HTTPS redirect, no client IP in logs | Passthrough cannot do L7 work | Redirect on port 80 with an HTTP router; PROXY protocol for IPs |
| Passthrough backend cannot renew Let's Encrypt | HTTP-01 challenges on port 80 never reach it | Route port 80 for that name to the backend too |

**Why it matters for troubleshooting**

During the migration you choose per site: terminate at Traefik with Let's Encrypt
(the end state), pass through to Apache while you move things (fastest cutover,
no certificate work), or re-encrypt when policy demands encrypted hops. Each
choice has its own failure signature, listed above.

**Next step**

Topic 1.5: after termination, the backend no longer sees the real client. How do you get it back?

### 1.5 X-Forwarded headers and real client IPs

**Level:** [L2 · Mid]

**Concept**

Once a proxy sits in front, the backend's TCP peer is the **proxy**, not the
client. Every line in Apache's access log suddenly shows `172.18.0.2`. Proxies
compensate by adding headers:

| Header | Content | Who sets it by default |
|---|---|---|
| `X-Forwarded-For` | `client, proxy1, proxy2`: each proxy appends the address it received the connection from | Traefik, Apache mod_proxy, HAProxy (`option forwardfor`); nginx only if configured |
| `X-Forwarded-Proto` | `http` or `https` as the *client* used it | Traefik; Apache and nginx only if configured |
| `X-Forwarded-Host` / `-Port` | Original Host and port | Traefik; Apache adds `X-Forwarded-Host` |
| `X-Real-IP` | Single client IP (nginx convention) | Traefik; nginx if configured |
| `Forwarded` | RFC 7239 standard form `for=...;proto=https;host=...` | Rarely used |
| PROXY protocol | Same information for raw TCP (passthrough) | Only when enabled on both sides |

```
client 198.51.100.7 ─► LB 192.0.2.5 ─► Traefik 172.18.0.2 ─► Apache :8080
                       XFF: 198.51.100.7     XFF: 198.51.100.7, 192.0.2.5
                                             X-Forwarded-Proto: https
Apache's TCP peer is 172.18.0.2. Only the headers tell it who the client was.
```

**Trust is the whole game.** Any client can send `X-Forwarded-For: 203.0.113.66`.
A backend must use the header *only* when the TCP peer is a proxy it trusts,
and then take the right-most address that is not a trusted proxy. Traefik, by
default, does not trust incoming `X-Forwarded-*` from clients: it strips them and
sets its own, unless the sender is listed in the entryPoint's
`forwardedHeaders.trustedIPs` (needed when a load balancer or CDN sits in front
of Traefik).

What goes wrong when you ignore this:

- Logs, rate limits, geo-blocking and fail2ban all see the proxy IP. fail2ban
  then bans Traefik, which blocks **everyone**.
- **Security hole**: an Apache allow-list like `Require ip 10.0.0.0/8` now
  allows the whole internet, because every request arrives from the proxy's
  private IP.
- The app thinks every request is plain HTTP: it generates `http://` links
  (mixed content), refuses to set `Secure` cookies, breaks OAuth `redirect_uri`
  checks, or redirects to HTTPS forever (capstone break 3).

Fixes, per layer: Apache `mod_remoteip` (topic 2.8), nginx `realip` (3.5),
Traefik `forwardedHeaders.trustedIPs` (4.2), and in the app: gunicorn
`--forwarded-allow-ips`, Django `SECURE_PROXY_SSL_HEADER`, Laravel
`TrustProxies`, Express `app.set('trust proxy', ...)`, PHP via
`SetEnvIf X-Forwarded-Proto ...`.

**Key terms**

| Term | Meaning |
|---|---|
| Trusted proxy | An address allowed to tell you who the client is |
| Spoofing | A client forging `X-Forwarded-For` to look like someone else |
| Hop-by-hop vs end-to-end headers | `Connection`, `Upgrade`, `Keep-Alive` are per hop and stripped; `X-Forwarded-*` travel end-to-end |

**See it on a real system**

The `traefik/whoami` image echoes back exactly what it receives. It is the best
debugging backend there is.

```bash
# Direct: no proxy, so no forwarded headers
sudo docker run -d --name whoami -p 127.0.0.1:18080:80 traefik/whoami
curl -s http://127.0.0.1:18080/
# Which client IPs does Apache log today? (a single private IP = everyone looks like the proxy)
sudo awk '{print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head
```

Through Traefik (after the capstone setup, with a whoami router) it looks like this:

```
Hostname: 6f1c2a9d3b7e
IP: 127.0.0.1
IP: 172.18.0.3
RemoteAddr: 172.18.0.2:50412
GET / HTTP/1.1
Host: whoami.example.com
User-Agent: curl/8.5.0
Accept: */*
Accept-Encoding: gzip
X-Forwarded-For: 192.168.56.1
X-Forwarded-Host: whoami.example.com
X-Forwarded-Port: 80
X-Forwarded-Proto: http
X-Forwarded-Server: 2b8c0d1e4f5a
X-Real-Ip: 192.168.56.1
```

- `RemoteAddr: 172.18.0.2` → the TCP peer is Traefik.
- `X-Forwarded-For: 192.168.56.1` → the real client (your laptop).
- `X-Forwarded-Proto: http` → the client used plain HTTP. Behind HTTPS it reads `https`.

**Hands-on lab (test VM only)**

**Step 1.** Use the capstone Traefik from 8.2: its compose project already runs a whoami container with the router `` Host(`whoami.example.com`) `` (Docker labels). From your laptop: `curl -s -H 'Host: whoami.example.com' http://192.168.56.10/`.

**Step 2.** Spoof: `curl -s -H 'Host: whoami.example.com' -H 'X-Forwarded-For: 203.0.113.66' http://192.168.56.10/ | grep -i forwarded-for`
→ Traefik drops your fake value because your laptop is not a trusted IP.

**Step 3.** Make your laptop "trusted" by adding
`--entrypoints.web.forwardedheaders.trustedips=192.168.56.1/32` to the Traefik
command, `docker compose up -d`, and spoof again: now `203.0.113.66` is kept and
your IP is appended. That is exactly what trusting a CDN or load balancer
does, and why the list must be precise. Remove the flag afterwards.

**How it breaks**

| Symptom | Cause | First check |
|---|---|---|
| All log lines show one private IP | No real-IP module configured | Topic 2.8 / 3.5 |
| fail2ban or rate limit blocks everyone | Bans the proxy IP | `sudo fail2ban-client status JAIL` |
| Real IP correct, but spoofable | Trusting `X-Forwarded-For` from any peer | Test with a forged header from outside |
| Redirect loop, mixed content, OAuth `redirect_uri` mismatch | App ignores `X-Forwarded-Proto` | Capstone break 3 |
| Behind a cloud LB, Traefik logs show the LB IP | LB not in `trustedIPs` | Topic 4.2 |

**Why it matters for troubleshooting**

The day after a migration, the first complaints are "logs show the wrong IP",
"the login redirect loops" and "our IP allow-list stopped working". All three
are this topic.

**Next step**

Topic 1.6: the other thing every hop adds: its own clock.

### 1.6 Timeouts chain and buffering

**Level:** [L2 · Mid]

**Concept**

Every hop has its own timers, and the **first one to expire decides the error
the user sees**:

```
browser ─► LB/CDN ─────► Traefik ──────────► Apache ─────────► gunicorn / php-fpm ─► DB
           idle 60 s      entry readTimeout    Timeout /         --timeout 30 s
           (AWS ALB)      60 s (v3 default)    ProxyTimeout      request_terminate_timeout
                          dialTimeout 30 s     (Ubuntu: 300 s)   max_execution_time 30 s
```

Rule of thumb: **inner timeouts shorter than outer timeouts**. Then the hop
nearest the problem fails first and writes a precise error ("WORKER TIMEOUT" in
gunicorn's log). If an outer proxy gives up first, you get a 504 at the edge and
*nothing* in the app log.

Who produces which code:

| Code | Meaning at a proxy | Typical producer |
|---|---|---|
| 502 Bad Gateway | Backend refused, reset, closed early, or sent garbage | nginx, Traefik (Apache uses 503 for refused) |
| 503 Service Unavailable | No usable backend | Apache (refused / in retry window), Traefik (no healthy server). A Dokploy app scaled to 0 tasks can show 502, 503 or 504 depending on how Traefik reaches it: check with `docker service ps APPNAME` |
| 504 Gateway Timeout | Backend did not answer in time | nginx `proxy_read_timeout`, Apache `ProxyTimeout`, Traefik dial timeout, AWS ALB |
| 499 | Client gave up before nginx answered | nginx access log only |
| 408 / 413 | Client too slow / body too large | Front proxy |

Defaults worth memorising:

| Component | Setting | Default | What you see when it fires |
|---|---|---|---|
| nginx | `proxy_read_timeout` / `proxy_connect_timeout` | 60 s | 504, `upstream timed out (110: Connection timed out)` |
| nginx | `client_max_body_size` | 1m | 413, `client intended to send too large body` |
| Apache | `Timeout` (also `ProxyTimeout` unless set) | 60 s compiled, 300 s in Ubuntu's `apache2.conf` | 504, `AH01102 ... (70007)The timeout specified has expired` |
| Apache | `ProxyPass ... retry=` | 60 s | 503 for a minute after one backend failure |
| Traefik v3 | `entryPoints.X.transport.respondingTimeouts.readTimeout` | 60 s | Slow, large uploads cut off |
| Traefik | `respondingTimeouts.idleTimeout` | 180 s | Idle keep-alive closed |
| Traefik | `serversTransport.forwardingTimeouts.dialTimeout` | 30 s | 504, `dial tcp ...: i/o timeout` |
| Traefik | `forwardingTimeouts.responseHeaderTimeout` | 0 (wait forever) | Slow apps are *not* cut by Traefik |
| gunicorn | `--timeout` | 30 s | `[CRITICAL] WORKER TIMEOUT`, proxy shows 502 |
| php-fpm / PHP | `request_terminate_timeout` / `max_execution_time` | off / 30 s | PHP fatal "Maximum execution time exceeded" |

**Buffering** is the other half. *Request buffering* means the proxy reads the
whole body before contacting the backend (nginx does by default:
`proxy_request_buffering on`), which protects sync app servers from slow uploads.
*Response buffering* means the proxy reads the backend's answer as fast as it
can, frees the backend, then trickles it to a slow client (nginx
`proxy_buffering on`). Buffering must be **off** for Server-Sent Events and
streaming responses. Traefik streams by default and offers a `buffering`
middleware when you want the nginx behaviour.

**Key terms**

| Term | Meaning |
|---|---|
| Connect / dial timeout | How long to wait for TCP to the backend |
| Read / response timeout | How long to wait for the backend's answer (or between two reads) |
| Idle / keep-alive timeout | How long an unused connection stays open |
| Slowloris | Attack that holds connections open by sending very slowly; what read timeouts defend against |

**See it on a real system**

```bash
# Time a slow request: the duration is a fingerprint of WHICH timeout fired
curl -s -o /dev/null -w 'code=%{http_code} connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total}\n' \
  https://app.example.com/reports/export
# Find timeout settings in the chain
grep -RniE '^\s*(Timeout|ProxyTimeout)|timeout=' /etc/apache2/ 2>/dev/null
sudo nginx -T 2>/dev/null | grep -E '_timeout|client_max_body_size'
sudo grep -RniE 'timeout' /etc/dokploy/traefik/traefik.yml 2>/dev/null
```

```
code=504 connect=0.011 ttfb=60.042 total=60.042
```

→ Exactly 60 s: an nginx default, Traefik's readTimeout, or an AWS ALB idle
timeout. 30 s: gunicorn or Traefik's dial timeout. 300 s: Ubuntu's Apache
`Timeout`. Look at the hop whose default matches.

**Hands-on lab (test VM only)**

**Step 1.** A backend that sleeps for as many seconds as the path says:

```bash
cat > ~/slow.py <<'EOF'
import http.server, time
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(int(self.path.strip('/') or 0))
        self.send_response(200); self.end_headers(); self.wfile.write(b'done\n')
http.server.ThreadingHTTPServer(('127.0.0.1', 8001), H).serve_forever()
EOF
python3 ~/slow.py &
```

**Step 2.** Proxy `/slow/` with a 5 second timeout:

```bash
sudo a2enmod proxy proxy_http
echo 'ProxyPass /slow/ http://127.0.0.1:8001/ timeout=5 retry=0' | sudo tee /etc/apache2/conf-available/lab-slow.conf
sudo a2enconf lab-slow && sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' http://localhost/slow/2     # 200 2.0
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' http://localhost/slow/10    # 504 5.0
sudo tail -n 2 /var/log/apache2/error.log
```

```
[proxy_http:error] [pid 3120:tid 140...] (70007)The timeout specified has expired: [client 127.0.0.1:51234] AH01102: error reading status line from remote server 127.0.0.1:8001
[proxy:error] [pid 3120:tid 140...] [client 127.0.0.1:51234] AH00898: Error reading from remote server returned by /slow/10
```

**Step 3.** Fix: either make the endpoint fast (the real fix) or raise
`timeout=` on purpose and write down why. Clean up: `sudo a2disconf lab-slow`,
reload, `kill %1`.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| 504 after exactly N seconds | A proxy timeout fired | `curl -w '%{time_total}'`, then match N to the defaults table |
| 502 after about 30 s with gunicorn | Worker killed by gunicorn's timeout | Search the app log for `WORKER TIMEOUT` (`docker logs CONTAINER`) |
| Uploads over a few MB fail, small ones work | Body size limit (413) or readTimeout on slow links | Proxy error log, topic 3.5 / 4.2 |
| Live log/progress page only updates at the end | Response buffering on | `proxy_buffering off` (nginx) |

**Why it matters for troubleshooting**

"It times out" is not a diagnosis. The exact duration plus the status code
usually names the component, which saves you from reading five logs.

**Next step**

Topic 1.7: connections that are supposed to stay open for hours.

### 1.7 WebSockets, HTTP/2 and HTTP/3

**Level:** [L2 · Mid]

**Concept**

**WebSocket** starts as an ordinary HTTP/1.1 request with `Upgrade: websocket`
and `Connection: Upgrade`. The server answers `101 Switching Protocols`, and
from then on the TCP connection is a two-way pipe that may live for hours.
Three things go wrong at proxies:

1. `Upgrade` and `Connection` are hop-by-hop headers. A proxy drops them unless
   configured to pass them: nginx needs explicit headers, Apache needs
   `upgrade=websocket` (2.4.47+) or `mod_proxy_wstunnel`. Traefik handles it
   automatically.
2. Idle timeouts kill quiet sockets (nginx `proxy_read_timeout` 60 s). The app
   should send pings, or the proxy timeout must be raised for that path.
3. With several replicas, fallbacks like socket.io long-polling need sticky
   sessions.

**HTTP/2** multiplexes many requests over one TLS connection and is negotiated
with ALPN. Proxies usually speak HTTP/2 to clients and HTTP/1.1 to backends.
Browsers reuse one connection for several names covered by the same certificate,
which is where `421 Misdirected Request` comes from.

**HTTP/3** runs over QUIC on **UDP 443**. That is why Dokploy's Traefik
publishes `443/udp`. If a firewall blocks UDP 443, browsers quietly fall back to
TCP. It is harmless, just slower on the first connection. Servers advertise
HTTP/3 with an `Alt-Svc` response header.

**Key terms**

| Term | Meaning |
|---|---|
| 101 Switching Protocols | Successful WebSocket upgrade |
| `Sec-WebSocket-Key` / `-Accept` | Handshake nonce and the server's proof |
| ALPN | TLS extension that picks `h2` or `http/1.1` |
| QUIC | UDP-based transport under HTTP/3 |
| `Alt-Svc` | Header telling the browser "HTTP/3 is available on UDP port N" |

**See it on a real system**

```bash
curl -sI --http2 https://app.example.com | head -1          # HTTP/2 200
curl -sI https://app.example.com | grep -i '^alt-svc'        # alt-svc: h3=":443"; ma=2592000
# WebSocket handshake by hand: a working proxy returns 101
curl -si --http1.1 --max-time 5 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  https://app.example.com/ws/ | head -4
sudo ss -tn state established '( sport = :443 )' | wc -l    # long-lived connections pile up here
```

```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

→ 101 means the upgrade passed through every hop. A 200, 400 or 426 means some
hop dropped the `Upgrade` header or the path is wrong.

**Hands-on lab (test VM only)**

**Step 1.** Run a WebSocket echo backend on loopback (any WebSocket echo server works; this image accepts the upgrade on any path and serves a browser test page on `/.ws`):

```bash
sudo docker run -d --name wsecho -p 127.0.0.1:18081:8080 jmalloc/echo-server
```

**Step 2.** Proxy it through Apache *without* upgrade support and try the handshake against `/ws/.ws`:

```bash
echo 'ProxyPass /ws/ http://127.0.0.1:18081/' | sudo tee /etc/apache2/conf-available/lab-ws.conf
sudo a2enconf lab-ws && sudo systemctl reload apache2
# run the handshake curl from above against http://localhost/ws/.ws → not 101
```

**Step 3.** Fix: change the line to
`ProxyPass /ws/ http://127.0.0.1:18081/ upgrade=websocket` (Apache 2.4.47+;
on older Apache such as RHEL 8's httpd 2.4.37, make sure `mod_proxy_wstunnel`
is loaded, which RHEL does in `conf.modules.d/00-proxy.conf` since it has no
`a2enmod`, and use a `ws://` backend URL), reload, and retry:
`101 Switching Protocols`. Clean up the conf and the container afterwards.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Browser console: `WebSocket connection to 'wss://...' failed`, handshake gets 200/400 | Proxy dropped `Upgrade` | nginx headers (3.5), Apache `upgrade=websocket` |
| Socket drops every 60 s exactly | Idle timeout at a proxy | App pings, or raise `proxy_read_timeout` for that location |
| Works with one replica, breaks with two | No sticky sessions for the polling fallback | Sticky cookie on the LB / Traefik service |
| `421 Misdirected Request` in a browser only | HTTP/2 connection reuse across names | Separate certificates, or make every name valid on that vhost |

**Why it matters for troubleshooting**

Apps with live dashboards, chat or notifications are the ones that "work
except for the live part" after a migration. Check the handshake by hand before
you blame the app.

**Next step**

Section 2: the server you actually inherited. Learn Apache well enough to move it.

---

## 2. Apache httpd in depth

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *Apache Web Server* and *Labs – Apache Web Server* ([course](https://kodekloud.com/courses/devops-pre-requisite-course), [lesson notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)); KodeKloud has no deeper Apache course · 2) Docs: Apache [virtual hosts](https://httpd.apache.org/docs/2.4/vhosts/) and [log files](https://httpd.apache.org/docs/2.4/logs.html) · 3) Note: section 4 of the [Web, HTTP & TLS reference](18-web-http-tls.md) for the command cheat sheet · 4) Video: none verified for Apache, use the docs · 5) Practice: labs 2.1–2.13, then run `apache-inventory.sh` (2.12) read-only on your real server.

Package and names differ by family; keep this table in mind for the whole section.

| | Ubuntu / Debian | RHEL / Rocky / Alma |
|---|---|---|
| Package / service | `apache2` | `httpd` |
| Control tool | `apache2ctl` (also `apachectl`) | `apachectl`, `httpd` |
| Main config | `/etc/apache2/apache2.conf` | `/etc/httpd/conf/httpd.conf` |
| Sites | `sites-available/` + `sites-enabled/` symlinks | `/etc/httpd/conf.d/*.conf` |
| Enable helpers | `a2ensite`, `a2enmod`, `a2enconf`, `a2query` | none: edit files, comment out `LoadModule` |
| Runs as | `www-data` | `apache` |
| Logs | `/var/log/apache2/` | `/var/log/httpd/` |
| Extra gate | UFW / nftables | firewalld and **SELinux** (`httpd_can_network_connect`, `http_port_t`) |

### 2.1 Processes and MPMs: prefork, worker, event

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Apache is one **parent** process running as root (it binds ports 80/443, reads
the config and supervises) plus **children** running as `www-data` that handle
requests. The **MPM** (Multi-Processing Module) decides how children handle
connections, and exactly one MPM is loaded at a time:

| MPM | Model | Use it when |
|---|---|---|
| prefork | Many processes, one connection each, no threads | Only when you must run `mod_php` (PHP extensions are not all thread-safe). Memory-hungry. |
| worker | Few processes × many threads; an idle keep-alive connection still holds a thread | Rarely chosen today |
| event | Like worker, but a listener thread parks idle keep-alive connections, so threads only serve active requests | Default on Ubuntu and RHEL. Pair it with php-fpm. |

```
prefork (mod_php)                         event (+ php-fpm)
root  apache2 (parent, binds :80 :443)    root  apache2 (parent)
├─ www-data apache2  ← 1 conn, PHP inside ├─ www-data apache2 ─ 25 threads + listener
├─ www-data apache2  ← 1 conn, PHP inside ├─ www-data apache2 ─ 25 threads + listener
├─ ... up to MaxRequestWorkers processes  └─ (PHP is NOT inside Apache)
                                                 │ FastCGI over /run/php/php8.3-fpm.sock
                                          root  php-fpm: master
                                          ├─ www-data php-fpm: pool www
                                          └─ ... up to pm.max_children
```

Why php-fpm matters: switching from `mod_php` + prefork to php-fpm + event cuts
memory, lets each site run its own pool (own user, own PHP version), and is the
same shape as a container setup (proxy in front, PHP app server behind). A site
already on php-fpm is much easier to move into Dokploy.

**Key terms**

| Term | Meaning |
|---|---|
| `ThreadsPerChild` | Threads in each child (event/worker; Ubuntu default 25) |
| `ServerLimit` | Maximum number of child processes |
| `MaxRequestWorkers` | Maximum simultaneous requests (prefork: processes; event: threads) |
| `MaxConnectionsPerChild` | Recycle a child after N connections (0 = never) |
| `KeepAlive` / `KeepAliveTimeout` | Reuse a TCP connection for several requests; Ubuntu default 5 s |
| `pm.max_children` | php-fpm's own limit on PHP workers per pool (Ubuntu default 5!) |

**See it on a real system**

```bash
a2query -M                                   # MPM in use (Ubuntu): event / worker / prefork
sudo apache2ctl -V | grep -iA2 'Server MPM'  # same, from the binary (RHEL: httpd -V)
sudo apache2ctl -M 2>/dev/null | grep -E 'mpm|php|fcgi'
ps -o user,pid,ppid,nlwp,rss,cmd -C apache2 --sort=-rss | head   # NLWP = threads per process
systemctl list-units 'php*-fpm*' --no-pager
ls /etc/apache2/mods-enabled/ | grep -E 'mpm|php|fcgi'
```

```
Server MPM:     event
  threaded:     yes (fixed thread count)
    forked:     yes (variable process count)

USER         PID    PPID NLWP   RSS CMD
www-data    1305    1301   27 11896 /usr/sbin/apache2 -k start
www-data    1304    1301   27 11532 /usr/sbin/apache2 -k start
root        1301       1    1  7420 /usr/sbin/apache2 -k start
```

→ Event MPM, two children with 27 threads each (25 workers plus the listener and
housekeeping), one root parent. With prefork you would see many single-threaded
children of 30–80 MB each when `mod_php` is loaded.

**Hands-on lab (test VM only)**

**Step 1.** Install PHP the "old" way and watch the MPM change (Ubuntu 24.04 ships PHP 8.3; 22.04 ships 8.1, adjust names):

```bash
sudo apt install -y libapache2-mod-php php-fpm
a2query -M                         # prefork: installing mod_php switched it
echo '<?php echo php_sapi_name(), PHP_EOL;' | sudo tee /var/www/html/sapi.php
curl -s http://localhost/sapi.php  # apache2handler  (PHP runs inside Apache)
```

**Step 2.** Break it on purpose: enable event while `mod_php` is still loaded.

```bash
sudo a2dismod mpm_prefork && sudo a2enmod mpm_event
sudo apache2ctl configtest
```

```
Apache is running a threaded MPM, but your PHP Module is not compiled to be threadsafe.  You need to recompile PHP.
AH00013: Pre-configuration failed
```

**Step 3.** Fix it properly: move PHP out of Apache into php-fpm.

```bash
sudo a2dismod php8.3                         # remove mod_php
sudo a2enmod mpm_event proxy_fcgi setenvif
sudo a2enconf php8.3-fpm                     # SetHandler to the FPM socket
sudo apache2ctl configtest && sudo systemctl restart apache2   # an MPM change needs a full restart
curl -s http://localhost/sapi.php            # fpm-fcgi
```

**Step 4.** Break the new chain: `sudo systemctl stop php8.3-fpm` and request again.

```
HTTP/1.1 503 Service Unavailable
[proxy:error] (2)No such file or directory: AH02454: FCGI: attempt to connect to Unix domain socket /run/php/php8.3-fpm.sock (localhost) failed
[proxy_fcgi:error] AH01079: failed to make connection to backend: httpd-UDS
```

Start php-fpm again to fix. Remove `/var/www/html/sapi.php` when done.

**How it breaks**

| Error text | Cause | Fix |
|---|---|---|
| `Apache is running a threaded MPM, but your PHP Module is not compiled to be threadsafe` | `mod_php` with event/worker | Prefork, or (better) php-fpm |
| `AH00534: apache2: Configuration error: More than one MPM loaded.` | Two `mpm_*.load` enabled | `a2dismod` one of them |
| `ERROR: Module mpm_prefork is enabled - cannot proceed due to conflicts.` | `a2enmod` refusing a second MPM | Disable the old MPM first |
| 503 + `AH01079 ... httpd-UDS` | php-fpm stopped or socket path wrong | `systemctl status php8.3-fpm`, `ls -l /run/php/` |
| Slow PHP, log: `WARNING: [pool www] server reached pm.max_children setting (5)` | php-fpm pool too small | Raise `pm.max_children` in `/etc/php/8.3/fpm/pool.d/www.conf` with RAM in mind |
| OOM killer kills apache2 children | Prefork + mod_php + too many workers | Topic 2.10 |

**Why it matters for troubleshooting**

"Apache is slow" is often "php-fpm has 5 workers". Knowing which process does the
real work tells you which limit to read. It also tells you how to containerise a
site: a `mod_php` site maps to an image like `php:8.3-apache`; an FPM site maps
to php-fpm plus a web server.

**Next step**

Topic 2.2: where all of this is configured, and how to find the file that matters.

### 2.2 Config layout: Ubuntu vs RHEL

**Level:** [L1 · Junior]

**Concept**

On Ubuntu, Apache reads one main file that includes everything else in a fixed
order. Sites and modules are enabled by **symlinks**, managed by helper scripts.

```
/etc/apache2/
├── apache2.conf        global settings; includes the rest, in this order:
│                         mods-enabled/*.load → mods-enabled/*.conf → ports.conf
│                         → conf-enabled/*.conf → sites-enabled/*.conf
├── ports.conf          Listen directives: WHO OWNS 80/443 starts here
├── envvars             APACHE_RUN_USER, APACHE_LOG_DIR, PID/lock dirs (sourced by apache2ctl)
├── mods-available/     NAME.load (LoadModule) + NAME.conf (its settings)
├── mods-enabled/       symlinks        ← a2enmod / a2dismod
├── conf-available/     global snippets: security.conf, charset.conf, other-vhosts-access-log.conf
├── conf-enabled/       symlinks        ← a2enconf / a2disconf
├── sites-available/    one file per site, must end in .conf
└── sites-enabled/      symlinks        ← a2ensite / a2dissite, loaded ALPHABETICALLY
/var/log/apache2/       access.log, error.log, other_vhosts_access.log, per-site logs
/var/www/html/          default DocumentRoot
```

On RHEL the same ideas are flatter:

```
/etc/httpd/
├── conf/httpd.conf       main file, contains Listen 80, includes the rest
├── conf.d/*.conf         vhosts, ssl.conf (Listen 443 https), welcome.conf
├── conf.modules.d/       00-base.conf, 00-mpm.conf, 00-proxy.conf ... (LoadModule lines)
└── logs → /var/log/httpd
```

`a2query` answers "what is enabled" without reading symlinks: `-s` sites,
`-m` modules, `-c` confs, `-M` the MPM.

**Key terms**

| Term | Meaning |
|---|---|
| `Include` / `IncludeOptional` | Pull in other files; `Optional` does not fail on an empty wildcard |
| `${APACHE_LOG_DIR}` | Variable from `envvars`; only defined when started via `apache2ctl` / systemd |
| `000-default.conf` | Ubuntu's stock site; its name makes it load first, so it is the default vhost |
| Drop-in vhost | A real file (not a symlink) placed in `sites-enabled/` by hand; it still loads but has no source in `sites-available/`, so `ls -l` and `DUMP_INCLUDES` are the reliable way to spot it |

**See it on a real system**

```bash
ls -l /etc/apache2/sites-enabled/            # symlinks = live sites; a plain file here is a hand-made drop-in
a2query -s                                   # enabled sites, nicer output
sudo apache2ctl -t -D DUMP_INCLUDES          # EVERY file Apache reads, in order, with line numbers
grep -RnE '^\s*Listen' /etc/apache2/         # all Listen lines (duplicates = startup failure)
grep -E 'RUN_USER|LOG_DIR' /etc/apache2/envvars
```

```
Included configuration files:
  (*) /etc/apache2/apache2.conf
    (146) /etc/apache2/mods-enabled/access_compat.load
    ...
    (156) /etc/apache2/ports.conf
    (215) /etc/apache2/conf-enabled/charset.conf
    ...
    (225) /etc/apache2/sites-enabled/crm.conf
    (225) /etc/apache2/sites-enabled/crm-le-ssl.conf
    (225) /etc/apache2/sites-enabled/shop.conf
```

→ The number is the line in the parent file that included it. This is the
fastest way to learn an inherited server: it shows the files that are actually
live, not the ones that merely exist.

**Hands-on lab (test VM only)**

**Step 1.** Create a site file **without** the `.conf` suffix and try to enable it:

```bash
echo '<VirtualHost *:80>
    ServerName lab.example.com
</VirtualHost>' | sudo tee /etc/apache2/sites-available/lab
sudo a2ensite lab           # ERROR: Site lab does not exist!
```

**Step 2.** Fix: `sudo mv /etc/apache2/sites-available/lab /etc/apache2/sites-available/lab.conf && sudo a2ensite lab`.

**Step 3.** Break it differently: delete the target, leaving a dangling symlink.

```bash
sudo rm /etc/apache2/sites-available/lab.conf
sudo apache2ctl configtest
```

```
apache2: Syntax error on line 225 of /etc/apache2/apache2.conf: Could not open configuration file /etc/apache2/sites-enabled/lab.conf: No such file or directory
```

**Step 4.** Fix: `sudo a2dissite lab` (removes the dangling symlink), configtest again.

**How it breaks**

| Error text | Cause | First command |
|---|---|---|
| `ERROR: Site NAME does not exist!` | File missing or not ending in `.conf` | `ls /etc/apache2/sites-available/` |
| `Could not open configuration file .../sites-enabled/X.conf` | Dangling symlink | `find /etc/apache2/ -xtype l` |
| `Invalid Mutex directory in argument file:${APACHE_LOCK_DIR}` or `AH00111: Config variable ${APACHE_RUN_DIR} is not defined` | Ran the `apache2` binary directly, without `envvars` | Use `apache2ctl` or `systemctl` |
| A site "is configured" but never answers | It sits in `sites-available` only | `a2query -s` |

**Why it matters for troubleshooting**

On an inherited server the first question is "which of these files are live?".
`DUMP_INCLUDES`, `ls -l sites-enabled/` and `a2query -s` answer it in seconds;
the first two also expose hand-made drop-ins that a quick `ls sites-available`
misses.

**Next step**

Topic 2.3: given the live files, which vhost answers a request?

### 2.3 Listen and VirtualHost matching

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

`Listen` opens sockets. `<VirtualHost>` blocks decide which config serves a
request that arrived on one of those sockets. Matching happens in two steps:

```
connection arrives on 192.0.2.10:443
   │
   ├─ Step 1: IP:port. Collect vhosts whose address matches the connection's LOCAL IP:port.
   │          Exact IP matches (<VirtualHost 192.0.2.10:443>) win. *:443 vhosts are used
   │          only if no exact IP vhost exists for that address. _default_ catches leftovers.
   │
   └─ Step 2: name. Within that set, compare Host (and SNI on TLS) with ServerName,
              then ServerAlias (wildcards allowed), in config order. First match wins.
              No match → the FIRST vhost of that set: the default vhost.
```

Consequences you will meet:

- Because `sites-enabled/` loads alphabetically, the default vhost is whichever
  file sorts first (`000-default.conf` by design).
- One IP-specific vhost "steals" all traffic for that IP from your `*:443`
  vhosts. Mixing `*:443` and `192.0.2.10:443` is a classic surprise.
- A `<VirtualHost *:8080>` without a matching `Listen 8080` is silently
  useless: configtest says `Syntax OK`, nothing listens.
- `NameVirtualHost` is obsolete since 2.4 (`AH00548` warning); delete it.

**Key terms**

| Term | Meaning |
|---|---|
| `ServerName` | The vhost's primary name (one per vhost) |
| `ServerAlias` | Extra names, wildcards like `*.example.com` allowed |
| `_default_` | Vhost address that matches any IP:port not matched by another vhost |
| Name-based vhost | Many names on one IP:port, selected by Host |
| IP-based vhost | Selected by the local IP the connection arrived on |

**See it on a real system**

```bash
sudo apache2ctl -S          # THE command: every vhost, its port, default server, file:line
```

```
VirtualHost configuration:
*:80                   is a NameVirtualHost
         default server crm.example.com (/etc/apache2/sites-enabled/crm.conf:1)
         port 80 namevhost crm.example.com (/etc/apache2/sites-enabled/crm.conf:1)
         port 80 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.conf:1)
                 alias www.shop.example.com
         port 80 namevhost wiki.example.com (/etc/apache2/sites-enabled/wiki.conf:1)
*:443                  is a NameVirtualHost
         default server crm.example.com (/etc/apache2/sites-enabled/crm-le-ssl.conf:2)
         port 443 namevhost crm.example.com (/etc/apache2/sites-enabled/crm-le-ssl.conf:2)
         port 443 namevhost shop.example.com (/etc/apache2/sites-enabled/shop-le-ssl.conf:2)
                 alias www.shop.example.com
         port 443 namevhost wiki.example.com (/etc/apache2/sites-enabled/wiki-le-ssl.conf:2)
ServerRoot: "/etc/apache2"
Main DocumentRoot: "/var/www/html"
Main ErrorLog: "/var/log/apache2/error.log"
Mutex default: dir="/var/run/apache2/" mechanism=default
PidFile: "/var/run/apache2/apache2.pid"
User: name="www-data" id=33
Group: name="www-data" id=33
```

- Three sites on both 80 and 443 → this server hosts three applications.
- `default server crm.example.com` → any unknown name gets the CRM. Fix with a catch-all (topic 1.2).
- `*-le-ssl.conf:2` → certbot `--apache` created these (line 1 is `<IfModule mod_ssl.c>`). Remember certbot when you migrate (topic 2.6).
- `Main DocumentRoot` / `Main ErrorLog` → the main-server values: they serve requests on an address no vhost covers, and any vhost without its own `DocumentRoot` / `ErrorLog` inherits them (startup errors also land in the main ErrorLog).

**Hands-on lab (test VM only)**

Use the capstone vhosts (8.1: site-a and site-b on `*:8080`).

**Step 1.** Add an IP-specific vhost and watch it steal traffic for its IP:

```bash
sudo tee /etc/apache2/sites-available/local-only.conf >/dev/null <<'EOF'
<VirtualHost 127.0.0.1:8080>
    ServerName local-only.example.com
    Redirect 418 /
</VirtualHost>
EOF
sudo a2ensite local-only && sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-a.example.com' http://127.0.0.1:8080/      # 418 !
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-a.example.com' http://192.168.56.10:8080/  # 200
sudo apache2ctl -S | head -8
```

→ For connections to 127.0.0.1, step 1 found an exact-IP vhost, so the `*:8080`
vhosts were never considered, whatever the Host header said.

**Step 2.** Fix: `sudo a2dissite local-only && sudo systemctl reload apache2`.

**Step 3.** Add `ServerAlias *.site-b.example.com` to site-b and test
`-H 'Host: dev.site-b.example.com'`. Then add a `<VirtualHost *:9090>` without
`Listen 9090`: configtest passes, `apache2ctl -S` lists it, and `ss -ltn` shows
nothing on port 9090. Remove it.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| Wrong site for some names | Name not in `ServerName`/`ServerAlias`, default vhost answered | `sudo apache2ctl -S` |
| Works by IP A, wrong site by IP B | IP-specific vhost mixed with `*` vhosts | `sudo apache2ctl -S`, look for numeric addresses |
| New vhost never answers, no errors | No matching `Listen` | `grep -Rn Listen /etc/apache2/`, `sudo ss -ltnp` |
| `AH00072 ... Address already in use` with nothing else on the port | Overlapping `Listen` lines (`Listen 8080` plus `Listen 192.0.2.10:8080`); an exact duplicate fails configtest with `Cannot define multiple Listeners on the same IP:port` | `grep -Rn '^\s*Listen' /etc/apache2/` |
| `[warn] _default_ VirtualHost overlap on port 443, the first has precedence` | Two default-style vhosts on one port | Remove one, or give names |

**Why it matters for troubleshooting**

`apache2ctl -S` is the map of the server. In your incident it answers "which
applications are on this box, on which ports, defined in which file" in one
command. Before any migration, save its output in the change ticket.

**Next step**

Topic 2.4: once a vhost is chosen, how a URL becomes a file, and who may read it.

### 2.4 DocumentRoot, Directory and .htaccess

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

For a static or PHP site, the URL path is appended to `DocumentRoot` to find a
file. Access is controlled per filesystem path with `<Directory>` blocks and per
URL with `<Location>`:

```apache
<VirtualHost *:80>
    ServerName wiki.example.com
    # URL /img/a.png -> /var/www/wiki/public/img/a.png
    DocumentRoot /var/www/wiki/public

    <Directory /var/www/wiki/public>
        # no directory listings; .htaccess may only set rewrites/redirects
        Options -Indexes +FollowSymLinks
        AllowOverride FileInfo
        Require all granted
    </Directory>

    # URL-based rule
    <Location /admin>
        Require ip 10.20.0.0/16
    </Location>
</VirtualHost>
```

Ubuntu's `apache2.conf` denies `/` and grants only `/usr/share` and `/var/www`.
A site under `/srv/site` or `/home/user/site` gets **403** until a
`<Directory>` block grants it.

`.htaccess` files are per-directory config, re-read **on every request**, and
only honoured where `AllowOverride` permits. `AllowOverride None` (Ubuntu's
default for `/var/www`) means every `.htaccess` is silently ignored. That is
why WordPress or Laravel "pretty URLs" return 404 on a fresh server.
`AllowOverride All` lets anyone who can write to the web root change server
config, and costs a filesystem lookup per directory level per request. Prefer
putting the rules in the vhost.

Besides Apache's rules, Unix permissions apply: `www-data` needs `x` on every
parent directory and `r` on the file.

**Key terms**

| Term | Meaning |
|---|---|
| `Require all granted / denied` | 2.4 access syntax (2.2's `Order allow,deny` needs `mod_access_compat`) |
| `Options Indexes` | Directory listing when no index file exists |
| `DirectoryIndex` | Which file serves a directory (`index.html index.php`) |
| `AllowOverride` | Which directive classes `.htaccess` may use: `None`, `All`, `FileInfo`, `AuthConfig`... |
| `Alias` | Map a URL to a directory outside `DocumentRoot` |

**See it on a real system**

```bash
grep -RniE 'DocumentRoot|AllowOverride|<Directory|Require' /etc/apache2/sites-enabled/ /etc/apache2/apache2.conf
sudo find /var/www /srv -name .htaccess -printf '%p (%s bytes)\n' 2>/dev/null
namei -l /var/www/wiki/public/index.php        # permissions of every path component
sudo -u www-data test -r /var/www/wiki/public/index.php && echo readable || echo NOT readable
```

```
f: /var/www/wiki/public/index.php
drwxr-xr-x root     root     /
drwxr-xr-x root     root     var
drwxr-xr-x root     root     www
drwxr-x--- deploy   deploy   wiki          ← no 'x' for others: www-data cannot enter → 403
drwxr-xr-x deploy   deploy   public
-rw-r--r-- deploy   deploy   index.php
```

**Hands-on lab (test VM only)**

**Step 1.** In site-a's directory create `.htaccess` with `Redirect 301 /old /new`.
`curl -sI -H 'Host: site-a.example.com' http://127.0.0.1:8080/old` → 404,
because `AllowOverride None` ignores the file.

**Step 2.** Add a `<Directory /var/www/site-a>` block with `AllowOverride FileInfo`
and `Require all granted` to site-a's vhost, reload: now 301.

**Step 3.** Break it: put the word `Garbage` on its own line in the `.htaccess`.
Every request to site-a now returns **500**, and the error log says:

```
[core:alert] [pid 4410:tid 140...] [client 127.0.0.1:40512] /var/www/site-a/.htaccess: Invalid command 'Garbage', perhaps misspelled or defined by a module not included in the server configuration
```

The same 500 appears when `.htaccess` uses `RewriteEngine On` but `mod_rewrite`
is not enabled. Fix the file, then remove it.

**Step 4.** Break permissions: `sudo chmod 750 /var/www/site-a` with owner root → 403.
Because step 2 allowed overrides, Apache fails first while looking for
`.htaccess`: `AH00529: /var/www/site-a/.htaccess pcfg_openfile: unable to check htaccess file, ensure it is readable and that '/var/www/site-a/' is executable`.
With `AllowOverride None` the same break logs
`AH00035: access to / denied ... because search permissions are missing on a component of the path`.
Restore with `sudo chmod 755 /var/www/site-a`.

**How it breaks**

| Error text | Cause | First command |
|---|---|---|
| 403, `AH01630: client denied by server configuration` | No `Require all granted` for that path | `grep -Rn -B3 -A3 'Directory' /etc/apache2/sites-enabled/X.conf` |
| 403, `AH00035 ... search permissions are missing` or `AH00529 ... unable to check htaccess file` | Unix permissions on a parent dir (AH00529 when overrides are allowed) | `namei -l FILE` |
| 403, `AH01276: Cannot serve directory ... No matching DirectoryIndex` | No index file and `-Indexes` | `ls DIR`, check `DirectoryIndex` |
| 500, `.htaccess: Invalid command ...` | Bad line or module not enabled | Read the named line; `a2enmod rewrite` |
| Pretty URLs 404 on a fresh server | `AllowOverride None` ignoring `.htaccess` | Move rules into the vhost, or allow `FileInfo` |

**Why it matters for troubleshooting**

When you containerise an Apache site, its `.htaccess` must keep working inside
the new image, and the owner of the files changes (UID 33 in Debian-based
images). List every `.htaccess` and every `<Directory>` rule during inventory.

**Next step**

Topic 2.5: vhosts that do not serve files at all, but forward to an app.

### 2.5 Reverse proxy with mod_proxy

**Level:** [L2 · Mid]

**Concept**

`mod_proxy` is the core; protocol modules do the work: `proxy_http` (HTTP and
HTTPS backends), `proxy_fcgi` (php-fpm), `proxy_wstunnel` (WebSockets, the older
way), `proxy_balancer` + `lbmethod_*` (several backends). The directives:

| Directive | What it does | Gotcha |
|---|---|---|
| `ProxyPass /path/ http://127.0.0.1:8000/ [key=value]` | Forward matching requests | First match wins in config order: specific paths (and `!` exclusions) first. Trailing slashes must match on both sides. |
| `ProxyPassReverse /path/ http://127.0.0.1:8000/` | Rewrites `Location`, `Content-Location`, `URI` headers in backend redirects | Does **not** rewrite HTML bodies |
| `ProxyPreserveHost On` | Send the client's Host to the backend | Off by default: the backend sees `Host: 127.0.0.1:8000` |
| `ProxyRequests Off` | Forward-proxy mode off (the default) | **Never** turn it On on an internet-facing server: open proxy |
| `ProxyTimeout` / `timeout=` | Backend read timeout | Defaults to `Timeout` |
| `retry=0` | Retry a failed backend immediately | Default 60 s of 503s after one failure |
| `upgrade=websocket` | Allow WebSocket upgrade (2.4.47+) | Older: `mod_proxy_wstunnel` with `ws://` |
| `RequestHeader set X-Forwarded-Proto "https"` | From `mod_headers` | `mod_proxy_http` adds `X-Forwarded-For/Host/Server` itself, but **not** `-Proto` |
| `SSLProxyEngine on` | Needed for `https://` backends | Plus `SSLProxyVerify`, `SSLProxyCheckPeerName` |

A complete, realistic proxied vhost:

```apache
<VirtualHost *:443>
    ServerName crm.example.com
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/crm.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/crm.example.com/privkey.pem

    ProxyRequests     Off
    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"

    # exclusions first, then specific paths, then the catch-all
    ProxyPass        /server-status !
    ProxyPass        /ws/ http://127.0.0.1:8000/ws/ upgrade=websocket
    ProxyPass        /    http://127.0.0.1:8000/ retry=0 timeout=120
    ProxyPassReverse /    http://127.0.0.1:8000/

    ErrorLog  ${APACHE_LOG_DIR}/crm-error.log
    CustomLog ${APACHE_LOG_DIR}/crm-access.log combined
</VirtualHost>
```

PHP through php-fpm uses the same module family:

```apache
<FilesMatch "\.php$">
    SetHandler "proxy:unix:/run/php/php8.3-fpm.sock|fcgi://localhost"
</FilesMatch>
```

**Key terms**

| Term | Meaning |
|---|---|
| Worker | Apache's connection pool to one backend URL |
| Balancer | `<Proxy balancer://NAME>` with several `BalancerMember` lines |
| `!` | "Do not proxy this path" |

**See it on a real system**

```bash
sudo apache2ctl -M 2>/dev/null | grep -E 'proxy|headers|rewrite|ssl|remoteip'
grep -RnE 'Proxy(Pass|PassReverse|PreserveHost)|SetHandler.*proxy' /etc/apache2/sites-enabled/
# Every backend Apache forwards to. Each one is "an application" to inventory:
grep -RhoE '^\s*ProxyPass\s+\S+\s+\S+' /etc/apache2/sites-enabled/ | awk '{print $3}' | grep -v '^!$' | sort -u
```

```
http://127.0.0.1:8000/
http://127.0.0.1:8069/
http://192.0.2.31:8080/
```

→ Three backends: two local apps (check them with `sudo ss -ltnp 'sport = :8000'`
and `'sport = :8069'` to get the process and its unit) and one on another host.
That is the "which app is which" list from your incident.

**Hands-on lab (test VM only)**

**Step 1.** Start the whoami container from topic 1.5 (`127.0.0.1:18080`) and add a vhost:

```bash
sudo a2enmod proxy proxy_http headers
sudo tee /etc/apache2/sites-available/whoami.conf >/dev/null <<'EOF'
<VirtualHost *:8080>
    ServerName whoami.example.com
    ProxyPass        / http://127.0.0.1:18080/
    ProxyPassReverse / http://127.0.0.1:18080/
</VirtualHost>
EOF
sudo a2ensite whoami && sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s -H 'Host: whoami.example.com' http://127.0.0.1:8080/ | grep -E '^(Host:|X-Forwarded)'
```

```
Host: 127.0.0.1:18080
X-Forwarded-For: 127.0.0.1
X-Forwarded-Host: whoami.example.com
X-Forwarded-Server: whoami.example.com
```

**Step 2.** Add `ProxyPreserveHost On` and `RequestHeader set X-Forwarded-Proto "http"`,
reload, repeat: `Host: whoami.example.com` and an `X-Forwarded-Proto` line appear.
A backend that is itself name-based (another Apache, or Traefik) only works with
`ProxyPreserveHost On`.

**Step 3.** Break it: `sudo a2dismod proxy_http && sudo systemctl reload apache2`.
configtest still passes (`ProxyPass` belongs to `mod_proxy`), but requests now
fail with **500**:

```
AH01144: No protocol handler was valid for the URL / (scheme 'http'). If you are using a DSO version of mod_proxy, make sure the proxy submodules are included in the configuration using LoadModule.
```

Fix with `sudo a2enmod proxy_http` and reload.

**How it breaks**

| Error text | Cause | Fix |
|---|---|---|
| 503 + `AH00957 ... (111)Connection refused` + `AH01114` | Backend down or wrong port | Start it / fix the port; `retry=0` |
| 503 + `(13)Permission denied: AH00957` (RHEL) | SELinux blocks httpd network connects | `sudo setsebool -P httpd_can_network_connect 1` |
| 500 + `AH01144: No protocol handler` | `proxy_http` / `proxy_fcgi` / `proxy_wstunnel` not loaded | `a2enmod` the submodule |
| 502 + `AH01102: error reading status line` | Backend closed the connection or crashed mid-request | Backend logs |
| Redirects go to `http://127.0.0.1:8000/...` | Missing `ProxyPassReverse` | Add it with the same URL as `ProxyPass` |
| Double slashes, 404 on every subpath | Trailing slash mismatch | `/app/` with `http://b/`, or `/app` with `http://b` |

**Why it matters for troubleshooting**

Each `ProxyPass` target is a separate application with its own process, logs and
owner. Collecting them is half of the inventory; the other half is the
`DocumentRoot` sites from topic 2.4.

**Next step**

Topic 2.6: the certificates on those vhosts, and what happens to them when Apache leaves.

### 2.6 TLS with mod_ssl

**Level:** [L2 · Mid]

**Concept**

`a2enmod ssl` loads `mod_ssl`, and `ports.conf` then adds `Listen 443` through
`<IfModule ssl_module>`. Each HTTPS vhost needs three lines:

```apache
SSLEngine on
# fullchain = leaf + intermediates
SSLCertificateFile    /etc/letsencrypt/live/crm.example.com/fullchain.pem
SSLCertificateKeyFile /etc/letsencrypt/live/crm.example.com/privkey.pem
```

Since 2.4.8 the chain goes into `SSLCertificateFile` (the "fullchain");
`SSLCertificateChainFile` is deprecated. Protocols and ciphers are global
(`/etc/apache2/mods-available/ssl.conf`, `SSLProtocol`, `SSLCipherSuite`).

Let's Encrypt with `certbot --apache` writes `*-le-ssl.conf` vhosts, keeps
certificates under `/etc/letsencrypt/live/DOMAIN/`, and renews through
`certbot.timer` (snap installs: `snap.certbot.renew.timer`), which then reloads Apache. During a migration that timer keeps
running: once Apache stops or loses port 80, renewals fail, and a renewal
deploy hook may even try to start Apache again. Inventory it and plan for it.

**Key terms**

| Term | Meaning |
|---|---|
| fullchain.pem / privkey.pem | Leaf + intermediates / private key (certbot layout) |
| `SSLProxyEngine` | Apache as a TLS *client* to `https://` backends |
| OCSP stapling | Server attaches revocation status; `SSLUseStapling` |
| HSTS | `Strict-Transport-Security` header; browsers then refuse plain HTTP for that name |

**See it on a real system**

```bash
grep -RnE 'SSLCertificate(File|KeyFile|ChainFile)' /etc/apache2/sites-enabled/
sudo certbot certificates                                  # every cert, its names, expiry, paths
systemctl list-timers | grep -i certbot
sudo ls /etc/letsencrypt/renewal/ && sudo grep -h authenticator /etc/letsencrypt/renewal/*.conf
# What clients actually receive:
openssl s_client -connect 192.0.2.10:443 -servername crm.example.com </dev/null 2>/dev/null \
  | grep -E '^ *[0-9] s:|i:|Verify return'
```

```
  Certificate Name: crm.example.com
    Serial Number: 4a1f...
    Key Type: ECDSA
    Domains: crm.example.com
    Expiry Date: 2026-12-01 10:15:42+00:00 (VALID: 58 days)
    Certificate Path: /etc/letsencrypt/live/crm.example.com/fullchain.pem
    Private Key Path: /etc/letsencrypt/live/crm.example.com/privkey.pem

authenticator = apache
```

→ `authenticator = apache` means renewal needs a running Apache on port 80. After
cutover to Traefik that renewal will fail; either let Traefik issue new
certificates (the normal end state) or switch the renewal to another method
before you stop Apache.

**Hands-on lab (test VM only)**

**Step 1.** Self-signed certificate and an HTTPS vhost on 8443 (so it does not collide with the capstone's Traefik on 443):

```bash
sudo openssl req -x509 -newkey rsa:2048 -nodes -days 30 \
  -keyout /etc/ssl/private/site-a.key -out /etc/ssl/certs/site-a.crt \
  -subj '/CN=site-a.example.com' -addext 'subjectAltName=DNS:site-a.example.com'
sudo a2enmod ssl
echo 'Listen 8443' | sudo tee -a /etc/apache2/ports.conf
sudo tee /etc/apache2/sites-available/site-a-ssl.conf >/dev/null <<'EOF'
<VirtualHost *:8443>
    ServerName site-a.example.com
    DocumentRoot /var/www/site-a
    SSLEngine on
    SSLCertificateFile    /etc/ssl/certs/site-a.crt
    SSLCertificateKeyFile /etc/ssl/private/site-a.key
</VirtualHost>
EOF
sudo a2ensite site-a-ssl && sudo apache2ctl configtest && sudo systemctl restart apache2
curl -sk --resolve site-a.example.com:8443:127.0.0.1 https://site-a.example.com:8443/
```

**Step 2.** Break it: generate a second key and point `SSLCertificateKeyFile` at it.

```bash
sudo openssl genrsa -out /etc/ssl/private/other.key 2048
sudo sed -i 's#site-a.key#other.key#' /etc/apache2/sites-available/site-a-ssl.conf
sudo apache2ctl configtest; sudo systemctl restart apache2; sudo tail -n 3 /var/log/apache2/error.log
```

```
AH02565: Certificate and private key site-a.example.com:8443:0 from /etc/ssl/certs/site-a.crt and /etc/ssl/private/other.key do not match
AH00016: Configuration Failed
```

→ Depending on version, configtest may still say `Syntax OK`; the mismatch is
caught when the config is actually loaded. That is why configtest alone is not
proof: a `restart` **or** a `reload` (graceful restart) with this error stops
the Apache parent and takes **all** sites down, as the Apache "Stopping and
Restarting" docs warn. Check certificate/key pairs (step 3) before applying,
and read the error log after every change.

**Step 3.** Prove the mismatch the way you would in production (works for RSA and EC keys), then fix the path:

```bash
sudo openssl x509 -in /etc/ssl/certs/site-a.crt -noout -pubkey | sha256sum
sudo openssl pkey -in /etc/ssl/private/other.key -pubout | sha256sum      # different hash = not a pair
sudo sed -i 's#other.key#site-a.key#' /etc/apache2/sites-available/site-a-ssl.conf
sudo apache2ctl configtest && sudo systemctl restart apache2
```

**How it breaks**

| Error text | Cause | First command |
|---|---|---|
| `AH02565: Certificate and private key ... do not match` | Wrong key file, often after a renewal by hand | Compare public-key hashes (step 3) |
| `AH02572: Failed to configure at least one certificate and key for HOST:443` | `SSLEngine on` without certificate lines | Check the vhost |
| `AH01909: ... server certificate does NOT include an ID which matches the server name` | Certificate names differ from `ServerName` | `openssl x509 -noout -ext subjectAltName -in CERT` |
| `curl: (60) SSL certificate problem: unable to get local issuer certificate` | Leaf only, no intermediates | Use `fullchain.pem` |
| `AH02032: Hostname X provided via SNI and hostname Y provided via HTTP have no compatible SSL setup` → 421 | SNI and Host point at vhosts with different TLS setups | Consistent names; test with `--resolve` |
| Renewal fails after the migration | certbot still uses the `apache` authenticator | `sudo certbot renew --dry-run` |

**Why it matters for troubleshooting**

Certificates are the part of a migration that fails **later**: weeks after the
cutover, when a renewal that used to work silently stops. Write every
certificate, its names, expiry and renewal method into the inventory.

**Next step**

Topic 2.7: the other thing inherited Apache servers are full of: rewrite rules.

### 2.7 mod_rewrite essentials

**Level:** [L2 · Mid]

**Concept**

`mod_rewrite` changes or redirects URLs based on conditions. A rule is zero or
more `RewriteCond` lines followed by one `RewriteRule`; all conditions must be
true (AND, unless `[OR]`).

```apache
RewriteEngine On
# condition: test a variable against a regex (! = negate)
RewriteCond %{HTTP_HOST} ^www\.(.+)$ [NC]
# rule: pattern on the URL path → substitution [flags]
RewriteRule ^/?(.*)$ https://%1/$1 [R=301,L]
```

| Piece | Meaning |
|---|---|
| `%{HTTPS}`, `%{HTTP_HOST}`, `%{REQUEST_URI}` | Server variables |
| `%{HTTP:X-Forwarded-Proto}` | Any request header |
| `-f` / `-d` | Condition: "is an existing file / directory" |
| `$1` / `%1` | Capture from the rule pattern / from the last condition |
| `[R=301]`, `[L]`, `[NC]`, `[QSA]`, `[P]`, `[END]` | Redirect, last rule, case-insensitive, keep query string, proxy, stop all processing |

The number one confusion: in a vhost the pattern sees the path **with** a
leading slash (`^/old`); in `.htaccess` the directory prefix is stripped, so the
pattern sees `old` **without** the slash. `^/?old` works in both.

For simple redirects you do not need `mod_rewrite` at all: `Redirect` and
`RedirectMatch` (mod_alias) are clearer.

Recipes you will meet in inherited configs:

```apache
# 1) HTTP → HTTPS when Apache itself terminates TLS (port-80 vhost)
<VirtualHost *:80>
    ServerName site-a.example.com
    Redirect permanent / https://site-a.example.com/
</VirtualHost>

# 2) HTTP → HTTPS that stays correct when a proxy in front terminates TLS
RewriteEngine On
RewriteCond %{HTTP:X-Forwarded-Proto} !=https
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]

# 3) Front controller (WordPress, Laravel): anything that is not a real file goes to index.php
#    .htaccess / <Directory> form; in a vhost REQUEST_FILENAME is not mapped yet,
#    so test %{DOCUMENT_ROOT}%{REQUEST_FILENAME} and rewrite to /index.php instead
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.php [L]
```

Recipe 1 placed behind Traefik is the redirect loop of capstone break 3: Apache
never sees HTTPS, so it redirects forever. Recipe 2 fixes it, but the cleanest
fix is to delete the redirect from Apache and let the edge proxy do it.

**Key terms**

| Term | Meaning |
|---|---|
| Internal rewrite | URL changes inside the server, the browser does not see it |
| External redirect | `[R]`: the browser gets 301/302 and a `Location` header |
| `LogLevel rewrite:trace3` | 2.4's replacement for `RewriteLog`; shows each rule's decision |

**See it on a real system**

```bash
grep -RniE 'Rewrite(Engine|Cond|Rule)|^\s*Redirect' /etc/apache2/sites-enabled/
sudo find /var/www -name .htaccess -exec grep -lE 'Rewrite|Redirect' {} +
# Follow a redirect chain hop by hop (headers only, at most 5 hops)
curl -sIL --max-redirs 5 http://site-a.example.com/ | grep -iE '^(HTTP|location)'
```

```
HTTP/1.1 301 Moved Permanently
Location: https://site-a.example.com/
HTTP/2 200
```

**Hands-on lab (test VM only)**

**Step 1.** Turn on rewrite tracing for one vhost only (add to site-a's vhost, reload):

```apache
LogLevel warn rewrite:trace3
```

**Step 2.** Add recipe 3 inside site-a's vhost in its vhost form (pattern `^/`,
conditions on `%{DOCUMENT_ROOT}%{REQUEST_FILENAME}`, target `/index.php`),
request `/anything`, and read the trace in site-a's error log:

```bash
sudo grep 'rewrite:trace' /var/log/apache2/site-a-error.log | tail -5
```

**Step 3.** Build a loop on purpose. Per-directory rules (in `.htaccess` or a
`<Directory>` block) run again after every internal redirect, so inside a
`<Directory /var/www/site-a>` block of site-a's vhost add `RewriteEngine On` and
`RewriteRule ^(.*)$ /x/$1 [L]`. The URL grows to `/x/x/x/...` until Apache stops
with **500** and
`AH00124: Request exceeded the limit of 10 internal redirects due to probable configuration error`.
(The same rule at vhost level runs only once per request and gives a plain 404.)
Remove the rule and the trace `LogLevel` (trace levels are very noisy).

**How it breaks**

| Symptom / error text | Cause | First command |
|---|---|---|
| Browser: `ERR_TOO_MANY_REDIRECTS`; curl: `(47) Maximum (5) redirects followed` | External redirect loop, usually HTTPS detection behind a proxy | `curl -sIL --max-redirs 5 URL` |
| 500 + `AH00124 ... limit of 10 internal redirects` | Internal rewrite loop | `LogLevel rewrite:trace3` |
| Rule "does nothing" | Pattern written for vhost used in `.htaccess` (or the reverse), or `AllowOverride None` | Trace log |
| 500 + `Invalid command 'RewriteEngine'` | `mod_rewrite` not enabled | `sudo a2enmod rewrite` |

**Why it matters for troubleshooting**

Most "it broke after we put a proxy in front" tickets are rewrite rules written
for a world where Apache saw HTTPS directly. Grep for them during inventory.

**Next step**

Topic 2.8: making Apache see the real client again.

### 2.8 Real client IPs with mod_remoteip

**Level:** [L2 · Mid]

**Concept**

`mod_remoteip` replaces the connection's client IP with the one in
`X-Forwarded-For`, **only when the request came from a proxy you trust**. After
that, `Require ip`, logs (`%a`) and anything reading the client address see the
real client.

```apache
# /etc/apache2/conf-available/remoteip.conf
RemoteIPHeader X-Forwarded-For
# Proxies on private addresses. Docker bridge networks (docker0, compose networks,
# docker_gwbridge) come from 172.17-172.31.x by default, inside 172.16.0.0/12;
# Swarm overlays such as dokploy-network use 10.0.0.0/8. Check yours (command below).
RemoteIPInternalProxy 172.16.0.0/12
# Use RemoteIPTrustedProxy instead for proxies on public addresses
```

And log `%a` (client IP after mod_remoteip) instead of `%h`:

```apache
LogFormat "%a %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\" %D" combined_realip
```

`%D` is the request duration in microseconds. Add it to every access log you own.

For PHP apps that need to know the request was HTTPS (`$_SERVER['HTTPS']`):

```apache
SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on
```

That environment variable is for the application. It does **not** change
`%{HTTPS}` inside `mod_rewrite`, which is why rewrite rules must test
`%{HTTP:X-Forwarded-Proto}` (recipe 2 in topic 2.7).

**Key terms**

| Term | Meaning |
|---|---|
| `%a` / `%{c}a` | Client IP after mod_remoteip / the real TCP peer (the proxy) |
| `RemoteIPInternalProxy` | Trusted proxies with private addresses |
| `RemoteIPProxyProtocol On` | Accept PROXY protocol instead of headers (for TCP passthrough) |

**See it on a real system**

```bash
sudo apache2ctl -M 2>/dev/null | grep remoteip
grep -RnE '^\s*(RemoteIP|LogFormat)' /etc/apache2/
sudo tail -n 3 /var/log/apache2/site-a-access.log | awk '{print $1}'
docker network inspect bridge docker_gwbridge dokploy-network --format '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null
```

→ The last command shows which subnets your proxy containers come from, so you
trust exactly those and nothing wider. On a Dokploy host, Traefik reaches a
service on the host through `docker_gwbridge`, so that subnet (not the overlay)
is the one Apache sees.

**Hands-on lab (test VM only)**

**Step 1.** With the capstone running, request site-a through Traefik and look at
site-a's access log: the first field is a Docker address such as `172.18.0.2`.

**Step 2.** Enable real IPs:

```bash
sudo a2enmod remoteip
printf 'RemoteIPHeader X-Forwarded-For\nRemoteIPInternalProxy 172.16.0.0/12\n' | sudo tee /etc/apache2/conf-available/remoteip.conf
sudo a2enconf remoteip
sudo sed -i 's/combined$/combined_realip/' /etc/apache2/sites-available/site-a.conf
echo 'LogFormat "%a %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\" %D" combined_realip' | sudo tee /etc/apache2/conf-available/logformat-realip.conf
sudo a2enconf logformat-realip && sudo apache2ctl configtest && sudo systemctl reload apache2
```

Request again: the log now shows your laptop's IP (192.168.56.1).

**Step 3.** Spoof test: on the VM, send a forged header directly to Apache (peer
is 127.0.0.1, not trusted): `curl -s -H 'Host: site-a.example.com' -H 'X-Forwarded-For: 203.0.113.66' http://127.0.0.1:8080/`.
The log shows `127.0.0.1`, not the forged address. Trust is working.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Still the proxy IP in logs | Log format still uses `%h`, or proxy not in the trusted range | `%a`; check the Docker subnet |
| Forged IPs appear in logs | Trusted range too wide (`0.0.0.0/0`), or port 8080 reachable from outside | Narrow the range; firewall the backend port |
| `Require ip` stops matching after migration | mod_remoteip missing: every request comes from the proxy | Enable it before cutover |

**Why it matters for troubleshooting**

Do this **before** cutover, or the first day after it you lose every useful
client IP in your logs and your allow-lists quietly open up.

**Next step**

Topic 2.9: logs in general, per vhost, and how to make them answer "is anyone still using this site?".

### 2.9 Logging per vhost and LogLevel

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Two log types, both configurable globally and per vhost:

- **ErrorLog**: problems and diagnostics. Verbosity by `LogLevel`, settable per
  module: `LogLevel warn proxy:info ssl:warn rewrite:trace3`.
- **CustomLog**: one line per request, in a named `LogFormat`. A vhost without
  its own `CustomLog` goes to Ubuntu's `other_vhosts_access.log`, whose first
  field is `vhost:port` so you can still tell sites apart.

Anatomy of an error line:

```
[Sat Oct 03 10:12:01.123456 2026] [proxy_http:error] [pid 2345:tid 140230] (70007)The timeout specified has expired: [client 198.51.100.7:51234] AH01102: error reading status line from remote server 127.0.0.1:8000
 └ time                            └ module:level     └ process/thread      └ OS/APR error (code)                     └ client                    └ AH code + message
```

Useful `LogFormat` fields: `%v` vhost name, `%a` client IP, `%t` time, `%r`
request line, `%>s` final status, `%O` bytes sent, `%D` duration (µs),
`%{Host}i` / `%{X-Forwarded-For}i` request headers. Rotation is done by
`/etc/logrotate.d/apache2` (daily, 14 rotations, compressed, reload afterwards).
Apache on Ubuntu logs to files, not to the journal: `journalctl -u apache2`
only shows start/stop failures.

**Key terms**

| Term | Meaning |
|---|---|
| `combined` / `vhost_combined` | Ubuntu's standard formats (the second starts with `%v:%p`) |
| `LogLevel` per module | Turn up one module (`proxy:debug`) without drowning in the rest |
| Piped log | A `CustomLog` whose target starts with a pipe character: send lines to a program (rotatelogs, logger) |

**See it on a real system**

```bash
grep -RnE 'ErrorLog|CustomLog|LogLevel' /etc/apache2/sites-enabled/ /etc/apache2/apache2.conf
ls -lt /var/log/apache2/ | head -20                    # recently written logs = live sites
sudo tail -F /var/log/apache2/*error.log               # follow all error logs at once
# Hits per vhost from the shared log (field 1 = vhost:port)
sudo awk '{split($1,a,":"); print a[1]}' /var/log/apache2/other_vhosts_access.log | sort | uniq -c | sort -rn
# Last request in each per-site access log
for f in /var/log/apache2/*access.log; do printf '%-55s ' "$f"; sudo tail -n1 "$f" | awk '{print $4, $5}'; done
# Requests per day for one site, including rotated and gzipped logs
sudo zcat -f /var/log/apache2/crm-access.log* | awk '{print substr($4,2,11)}' | sort | uniq -c
# Same, without health checks and bots, so you see humans
sudo zcat -f /var/log/apache2/crm-access.log* | grep -viE 'health|bot|crawler|spider|uptime' | awk '{print substr($4,2,11)}' | sort | uniq -c
```

```
/var/log/apache2/crm-access.log                         [03/Oct/2026:09:58:11 +0000]
/var/log/apache2/shop-access.log                        [03/Oct/2026:10:01:47 +0000]
/var/log/apache2/wiki-access.log                        [14/Mar/2026:16:20:03 +0000]
```

→ The wiki's last request was months ago: a candidate for "is this app still
needed?". Ask its owner before you migrate it; retiring it is cheaper. (The
per-day counts sort as text, not by date; that is fine for counting.)

**Hands-on lab (test VM only)**

**Step 1.** Give the whoami vhost (topic 2.5) its own logs and `LogLevel warn proxy:trace2`,
reload, make one request, and read how much detail mod_proxy writes. Set it back
to `warn`.

**Step 2.** Break it: set `ErrorLog ${APACHE_LOG_DIR}/whoami/error.log` (a directory
that does not exist) and run `sudo apache2ctl configtest`:

```
(2)No such file or directory: AH02291: Cannot access directory '/var/log/apache2/whoami/' for error log of vhost defined at /etc/apache2/sites-enabled/whoami.conf:1
AH00014: Configuration check failed
```

Fix by creating the directory or changing the path.

**How it breaks**

| Symptom / error text | Cause | Fix |
|---|---|---|
| `AH02291: Cannot access directory ... for error log` / `AH00015: Unable to open logs` | Log path missing or not writable | Create it; check permissions/SELinux context |
| A site's requests are "missing" | It has no `CustomLog`; look in `other_vhosts_access.log` | Add per-vhost logs |
| Disk fills with logs | Trace level left on, or logrotate broken | `sudo logrotate -d /etc/logrotate.d/apache2` |
| Logs show only the proxy IP | See topic 2.8 | mod_remoteip + `%a` |

**Why it matters for troubleshooting**

Per-vhost logs with duration (`%D`) answer "which app, how often, how slow"
without any monitoring stack. In your incident, they answer "which apps are
still needed" with evidence instead of guesses.

**Next step**

Topic 2.10: is Apache keeping up? Reading its scoreboard and sizing its workers.

### 2.10 mod_status and MaxRequestWorkers

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

`mod_status` publishes a live **scoreboard** at `/server-status`. On Ubuntu it is
enabled by default and limited to local requests (`Require local` in
`mods-enabled/status.conf`). The `?auto` variant is machine-readable.

Scoreboard letters: `_` waiting, `S` starting, `R` reading request, `W` sending
reply, `K` keep-alive, `D` DNS lookup, `C` closing, `L` logging, `G` graceful
finish, `I` idle cleanup, `.` open slot.

`MaxRequestWorkers` is the maximum number of requests Apache serves at once
(prefork: processes; event: `ServerLimit × ThreadsPerChild`, Ubuntu defaults
16 × 25 = 400 possible, `MaxRequestWorkers 150` set). When it is reached, new
connections wait in the kernel's accept queue: latency climbs, then clients
time out, and the error log says
`server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting`
(the AH number differs per MPM).

Sizing:

- Prefork: `MaxRequestWorkers ≈ RAM you can give Apache / average RSS of a child`.
  With 2 GB for Apache and 60 MB children: about 33, not the default 150.
- Event: workers are threads and cheap; raise `ServerLimit` and
  `MaxRequestWorkers` together, keeping `MaxRequestWorkers ≤ ServerLimit × ThreadsPerChild`.
- Raising Apache's limit is pointless if the real bottleneck is behind it:
  php-fpm's `pm.max_children` (default 5 on Ubuntu) or a slow database. Extra
  Apache workers then just queue at php-fpm.

**Key terms**

| Term | Meaning |
|---|---|
| BusyWorkers / IdleWorkers | Workers serving a request / waiting |
| `ListenBacklog` | Kernel queue length for not-yet-accepted connections (511) |
| `ExtendedStatus` | Per-request detail in the status page (on when mod_status is loaded in 2.4) |

**See it on a real system**

```bash
curl -s 'http://127.0.0.1/server-status?auto' | grep -E 'ServerMPM|BusyWorkers|IdleWorkers|ConnsTotal|ReqPerSec|Scoreboard'
cat /etc/apache2/mods-enabled/mpm_event.conf          # or mpm_prefork.conf
ps -ylC apache2 --sort=rss | awk 'NR>1 {sum+=$8; n++} END {printf "procs=%d avg_rss=%.0f MB\n", n, sum/n/1024}'
sudo grep -h 'MaxRequestWorkers' /var/log/apache2/error.log* 2>/dev/null | tail -3
sudo grep -h 'max_children' /var/log/php*-fpm.log 2>/dev/null | tail -3
```

```
ServerMPM: event
ReqPerSec: .211
BusyWorkers: 3
IdleWorkers: 72
ConnsTotal: 6
Scoreboard: __W_____K_____R______________________________________________________..........
```

→ 3 busy of 75 started workers: Apache is nowhere near its limit. If users
still see slowness, look behind Apache (php-fpm, the app, the database).

If `/server-status` returns the application instead of the scoreboard, the
default vhost proxies `/` to an app. Add `ProxyPass /server-status !` before the
catch-all `ProxyPass`, or query a vhost that does not proxy.

**Hands-on lab (test VM only)**

**Step 1.** Shrink Apache on purpose. Back up `mpm_event.conf`, then set:

```apache
StartServers             1
ServerLimit              2
ThreadsPerChild          2
MinSpareThreads          1
MaxSpareThreads          4
MaxRequestWorkers        4
```

Restart Apache (MPM limits need a restart).

**Step 2.** Load it through the slow backend from topic 1.6 (re-create `/slow/`
with `timeout=30` this time) using `ab` from `apache2-utils`:

```bash
ab -n 40 -c 10 -H 'Host: site-a.example.com' http://127.0.0.1:8080/slow/2 &
watch -n1 "curl -s -H 'Host: site-a.example.com' 'http://127.0.0.1:8080/server-status?auto' | grep -E 'Busy|Idle|Scoreboard'"
```

→ The scoreboard fills with `W`, `ab` reports long waits, and the error log
shows the `MaxRequestWorkers` warning. (While Apache is saturated, the status
request itself may wait in line, which is a lesson too.)

**Step 3.** Restore the backup, restart, and rerun: the same load finishes much faster.

**How it breaks**

| Symptom / error text | Cause | First command |
|---|---|---|
| `server reached MaxRequestWorkers setting` | Too few workers, or slow backends holding them | Scoreboard: mostly `W` = backends slow |
| Mostly `K` in the scoreboard (prefork/worker) | Keep-alive connections hogging workers | Event MPM, lower `KeepAliveTimeout` |
| OOM kills apache2 children | Prefork sized beyond RAM | `ps -ylC apache2`, size by RSS |
| `server reached pm.max_children` in php-fpm log | PHP pool is the bottleneck | Size the pool, not Apache |

**Why it matters for troubleshooting**

"The site is slow" splits into two questions the scoreboard answers in seconds:
is Apache out of workers, and if so, what are they waiting on? It is also a
baseline to compare with after the move to containers.

**Next step**

Topic 2.11: the control commands, and how to stop, move or "dispatch" Apache without surprises.

### 2.11 apache2ctl toolkit: test, inspect, reload, dispatch

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Always drive Apache through `apache2ctl` (or `systemctl`) on Ubuntu, never by
running the `apache2` binary directly: `apache2ctl` sources `envvars`, which
defines `${APACHE_LOG_DIR}` and friends.

| Command | What it does | When |
|---|---|---|
| `sudo apache2ctl configtest` (`-t`) | Syntax check: `Syntax OK` | Before **every** reload or restart |
| `sudo apache2ctl -S` | Vhosts, ports, defaults, main paths | Inventory, wrong-site bugs |
| `sudo apache2ctl -M` | Loaded modules | "Is mod_X on?" |
| `sudo apache2ctl -V` | Build info, MPM, compiled-in paths | Unknown server |
| `sudo apache2ctl -t -D DUMP_INCLUDES` | Every config file read, in order | "Which file is live?" |
| `sudo apache2ctl -t -D DUMP_RUN_CFG` | User, group, PID file, mutexes | Permission puzzles |
| `sudo systemctl reload apache2` (= `apache2ctl graceful`) | Re-read config; in-flight requests finish | Normal changes |
| `sudo systemctl restart apache2` | Stop and start: drops connections | MPM change, `Listen` changes |
| `sudo apache2ctl graceful-stop` | Stop after in-flight requests finish | Planned stop |

Safe change workflow, every time:

```bash
sudo cp -a /etc/apache2 /root/apache2.bak.$(date +%F-%H%M)   # 1. backup
sudoedit /etc/apache2/sites-available/crm.conf               # 2. change ONE thing
sudo apache2ctl configtest                                   # 3. test
sudo systemctl reload apache2                                # 4. apply gracefully
curl -sI -H 'Host: crm.example.com' http://127.0.0.1/        # 5. verify
sudo tail -n 20 /var/log/apache2/error.log                   # 6. watch for new errors
```

**Dispatching Apache** (stopping it for good, or moving it off 80/443) is a
change with three parts. Doing only the first is how Apache comes back after a
reboot and steals 443 again.

```bash
# A) Move Apache to a backend port instead of stopping it (pattern 7.1)
sudoedit /etc/apache2/ports.conf                 # Listen 8080 instead of 80/443
sudo apache2ctl configtest && sudo systemctl restart apache2

# B) Or stop it completely: now AND at boot
sudo systemctl disable --now apache2             # stop + do not start at boot
sudo systemctl mask apache2                      # optional: refuse to start at all, even as a dependency
systemctl is-enabled apache2; systemctl is-active apache2   # masked / inactive

# C) Rollback, written down BEFORE you start
sudo systemctl unmask apache2 && sudo systemctl enable --now apache2
```

Also check what still expects Apache: `certbot` renewals with the `apache`
authenticator, monitoring checks, cron jobs calling `apache2ctl`, and logrotate.

**Key terms**

| Term | Meaning |
|---|---|
| Graceful | Children finish current requests before exiting |
| `disable` vs `mask` | Not started at boot / cannot be started at all |
| `AH00558` | "Could not reliably determine the server's fully qualified domain name" (cosmetic) |

**See it on a real system**

```bash
sudo apache2ctl configtest
systemctl status apache2 --no-pager -l | head -15
systemctl is-enabled apache2
systemctl list-dependencies --reverse apache2.service   # does anything pull Apache in?
```

```
AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message
Syntax OK
```

→ `Syntax OK` is what matters. The `AH00558` line is harmless; silence it with
`echo 'ServerName localhost' | sudo tee /etc/apache2/conf-available/servername.conf && sudo a2enconf servername`.

**Hands-on lab (test VM only)**

**Step 1.** Break a config two classic ways and read what configtest says:
a duplicate `Listen 8080` line in `ports.conf`
(`AH00526: Syntax error on line N of /etc/apache2/ports.conf: Cannot define multiple Listeners on the same IP:port`;
an *overlapping* pair such as `Listen 8080` plus `Listen 192.168.56.10:8080`
passes configtest and fails only at restart with `AH00072 ... Address already in use`),
and an inline comment after a directive, e.g. `DocumentRoot /var/www/site-a # main site`
(`AH00526: Syntax error ... DocumentRoot takes one argument`). Apache only
allows comments on their own line.

**Step 2.** Fix both. Then practise the dispatch: `disable --now`, reboot the VM,
confirm Apache stayed down, then roll back with step C.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| `reload` returned an error and nothing changed | configtest failed inside graceful; old config still running | `sudo apache2ctl configtest` |
| `restart` (or a `reload` that passed configtest) and **all** sites are down | A config error only caught at load time, e.g. a certificate/key mismatch | `journalctl -u apache2 -n 30`, error.log |
| Apache back after reboot | Only stopped, not disabled | `systemctl is-enabled apache2` |
| `AH00526: Syntax error on line N` | Typo, missing module, or inline comment | Open that exact line |

**Why it matters for troubleshooting**

A disciplined change loop (backup, one change, test, graceful apply, verify,
watch) turns most Apache incidents into a one-command rollback.

**Next step**

Topic 2.12: put everything together and inventory an inherited server.

### 2.12 Reading an inherited Apache server

**Level:** [L2 · Mid]

**Concept**

Before you move anything, build a table with one row per site: name and
aliases, ports, what serves it (DocumentRoot or a `ProxyPass` backend, and that
backend's process and unit), logs, certificate and expiry, renewal method,
special rules (`.htaccess`, rewrites, auth), last real request, and owner. That
table *is* the migration plan. The [port inventory playbook](22-playbook-ports-inventory.md)
covers the "who owns this port" side for every service on the host; this topic
is the Apache-specific part.

**Key terms**

| Column | Command that fills it |
|---|---|
| Name, aliases, port, file | `sudo apache2ctl -S` |
| DocumentRoot / backend | `grep` the vhost file (script below) |
| Backend process and unit | `sudo ss -ltnp 'sport = :PORT'`, then `systemctl status PID` |
| Certificate and expiry | `openssl x509 -enddate -noout -in FILE` |
| Last request | Last line of the vhost's access log |

**See it on a real system**

A read-only script that prints the essentials for every enabled vhost (save it
as `apache-inventory.sh`; it changes nothing):

```bash
#!/usr/bin/env bash
# apache-inventory.sh: read-only summary of enabled Apache vhosts (Ubuntu/Debian layout)
shopt -s nullglob
for f in /etc/apache2/sites-enabled/*.conf; do
  echo "=== $f -> $(readlink -f "$f")"
  grep -hiE '^\s*(<VirtualHost|ServerName|ServerAlias|DocumentRoot|ProxyPass(Reverse)?\s|SetHandler|SSLCertificateFile|ErrorLog|CustomLog|Redirect|RewriteRule)' "$f" \
    | sed 's/^\s*/    /'
  for c in $(grep -hiE '^\s*SSLCertificateFile' "$f" | awk '{print $2}'); do
    printf '    cert %s expires: %s\n' "$c" "$(sudo openssl x509 -enddate -noout -in "$c" 2>/dev/null | cut -d= -f2)"
  done
done
echo "=== backends"
grep -RhoE '^\s*ProxyPass\s+\S+\s+\S+' /etc/apache2/sites-enabled/ | awk '{print $3}' | grep -v '^!$' | sort -u
echo "=== last request per access log"
for l in /var/log/apache2/*access.log; do printf '    %-50s %s\n' "$l" "$(sudo tail -n1 "$l" | awk '{print $4}')"; done
```

```
=== /etc/apache2/sites-enabled/crm-le-ssl.conf -> /etc/apache2/sites-available/crm-le-ssl.conf
    <VirtualHost *:443>
    ServerName crm.example.com
    ProxyPass / http://127.0.0.1:8069/
    ProxyPassReverse / http://127.0.0.1:8069/
    SSLCertificateFile /etc/letsencrypt/live/crm.example.com/fullchain.pem
    cert /etc/letsencrypt/live/crm.example.com/fullchain.pem expires: Dec  1 10:15:42 2026 GMT
=== backends
http://127.0.0.1:8069/
=== last request per access log
    /var/log/apache2/crm-access.log                    [03/Oct/2026:09:58:11
```

Then, for each backend port:

```bash
sudo ss -ltnp 'sport = :8069'                      # which process
systemctl status 2210 --no-pager | head -3          # which unit owns that PID
sudo crontab -l -u www-data 2>/dev/null             # jobs that belong to the sites
```

**Hands-on lab (test VM only)**

Run the script on your lab VM after section 8.1, then fill a table for site-a,
site-b and whoami by hand. Compare it with `apache2ctl -S`. Anything in one and
not the other is a finding.

**How it breaks**

| Trap | Why it bites |
|---|---|
| Hand-made files in `sites-enabled/` | `sites-available` does not show them, and `a2query -s` is not a reliable way to spot them; `ls -l sites-enabled/` (plain file, not a symlink) and `DUMP_INCLUDES` are |
| Vhosts defined in `conf-enabled/` or `apache2.conf` | Not where you looked; `DUMP_INCLUDES` finds them |
| A backend on another host | Not in `ss` on this host; the inventory must say so |
| Cron jobs, uploads directories, local mail | Part of the app, but not in Apache config |

**Why it matters for troubleshooting**

This is the list you were missing during the incident. With it, "which app is on
which port, where are its logs, is it still used" takes minutes instead of a
day of searching.

**Next step**

Topic 2.13: the AH error codes you will find in those logs.

### 2.13 Apache error codes decoded

**Level:** [L2 · Mid]

**Concept**

Every Apache 2.4 error message carries an `AHnnnnn` code. Search by the code: it
is stable across versions and languages, unlike the text around it. Start
triage with a histogram:

```bash
sudo grep -ohE 'AH[0-9]{5}' /var/log/apache2/*error.log | sort | uniq -c | sort -rn | head
```

**Key terms**

| Code | Short message | Meaning → fix |
|---|---|---|
| AH00558 | Could not reliably determine the server's FQDN | Cosmetic → global `ServerName` |
| AH00072 | make_sock: could not bind to address | Port taken (other process or overlapping `Listen`) → `ss -ltnp`, grep `Listen` |
| AH00451 | no listening sockets available, shutting down | Follows AH00072 |
| AH00526 | Syntax error on line N of FILE | Open that line |
| AH00015 / AH02291 | Unable to open logs / cannot access log directory | Path or permission |
| AH00534 | More than one MPM loaded | Disable one MPM |
| AH01630 | client denied by server configuration | `Require` rules / `<Directory>` grant |
| AH00035 | access denied ... search permissions are missing | Unix permissions on a parent dir → `namei -l` |
| AH01276 | Cannot serve directory: No matching DirectoryIndex | No index file, listings off |
| AH00124 | Request exceeded the limit of 10 internal redirects | Rewrite loop |
| AH00957 | attempt to connect to IP:PORT failed | Backend down, wrong port, SELinux |
| AH01114 | failed to make connection to backend | Same family → 503 |
| AH01102 / AH00898 | error reading status line / from remote server | Backend closed or timed out → 502/504 |
| AH01144 | No protocol handler was valid for the URL | `proxy_http`/`proxy_fcgi` not loaded |
| AH01079 / AH02454 | failed to make connection to backend: httpd-UDS | php-fpm socket missing |
| AH01071 | Got error 'Primary script unknown' | php-fpm cannot find the script (path mismatch) → "File not found." |
| AH02565 | Certificate and private key do not match | Wrong key file |
| AH02572 | Failed to configure at least one certificate and key | `SSLEngine on` without certificate |
| AH01909 | server certificate does NOT include an ID which matches the server name | Certificate names vs `ServerName` |
| AH02032 | Hostname provided via SNI and via HTTP have no compatible SSL setup | 421 Misdirected Request |
| AH00169 / AH00489 / AH00493 | caught SIGTERM / resuming normal operations / graceful restart | Normal lifecycle: use them to timestamp changes |

**See it on a real system**

```bash
# When did Apache stop, start, or reload? (lifecycle codes give you a change timeline)
sudo grep -hE 'AH00169|AH00489|AH00493' /var/log/apache2/error.log | tail -5
# Errors in the last hour for one vhost
sudo awk -v d="$(date -d '1 hour ago' '+%a %b %d %H')" 'index($0, d)' /var/log/apache2/crm-error.log | tail
```

**Hands-on lab (test VM only)**

Revisit the breaks from 2.1–2.11 and, for each one, write down the AH code you
saw and the one-line fix. That page of notes is your personal Apache runbook.

**How it breaks**

The table above is the "how it breaks". When a code is not listed, search the
[Apache 2.4 documentation](https://httpd.apache.org/docs/2.4/) for the module
named in the `[module:level]` field of the log line.

**Why it matters for troubleshooting**

A histogram of AH codes over the last day tells you in one command whether you
have a config problem, a permission problem or a backend problem.

**Next step**

Section 3: nginx, the proxy you will meet everywhere else (and inside Dokploy's Static build type).

---

## 3. Nginx in depth

> 📚 **Study path:** 1) KodeKloud: *Nginx For Beginners* — Install & Config (*Firewall & Ports*) → Intermediate Config (*Virtual Servers & Multiple Sites*, *Reverse Proxy*) → Security (*HTTPS*) → Performance (*Monitoring & Troubleshooting*) ([course](https://kodekloud.com/courses/nginx-for-beginners), [Reverse Proxy notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) · 2) Video: KodeKloud *NGINX For Beginners | NGINX Tutorial* ([YouTube](https://www.youtube.com/watch?v=Hfg7_y0fGTg), 86 min) · 3) Note: topics 3.1–3.6 here with the [nginx docs](https://nginx.org/en/docs/) open · 4) Practice: SadServers scenarios tagged nginx ([sadservers.com/scenarios](https://sadservers.com/scenarios)).

### 3.1 Architecture and config layout

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

nginx runs one **master** process (root: reads config, binds ports, manages
workers) and a few **worker** processes (`worker_processes auto` = one per CPU
core). Each worker is event-driven and handles thousands of connections, so
there is no "MaxRequestWorkers" cliff like Apache prefork. nginx serves files
and proxies; it never runs PHP itself (always php-fpm behind it).

Config is a tree of **contexts**; directives inherit downward unless redefined:

```
main               user, worker_processes, error_log, pid
├── events         worker_connections (Ubuntu default 768)
└── http           log_format, map, upstream, include conf.d/*.conf, sites-enabled/*
    ├── upstream NAME { server ...; }
    └── server     listen, server_name, ssl_certificate      (≈ an Apache vhost)
        └── location /path/ { proxy_pass ...; root ...; }   (≈ <Location>)
```

Inheritance gotcha: array-type directives such as `proxy_set_header` and
`add_header` are inherited **only if the inner block defines none of its own**.
One `proxy_set_header` inside a `location` silently drops every one set at
`server` level. Use an `include` snippet in each location instead.

| | Ubuntu / Debian | RHEL family |
|---|---|---|
| Main file | `/etc/nginx/nginx.conf` | same |
| Sites | `sites-available/` + symlinks in `sites-enabled/` (no helper script) | `/etc/nginx/conf.d/*.conf` |
| Snippets | `/etc/nginx/snippets/` (`fastcgi-php.conf`, `snakeoil.conf`) | none by default |
| Logs | `/var/log/nginx/access.log`, `error.log` | same |
| User | `www-data` | `nginx` |

**Key terms**

| Term | Meaning |
|---|---|
| Server block | One virtual server (`server { }`) |
| `worker_connections` | Max simultaneous connections per worker (clients + upstreams) |
| `include` | Pull in files; `nginx -T` shows the merged result |
| Reload | `nginx -s reload` / `systemctl reload nginx`: new workers start, old ones finish their requests |

**See it on a real system**

```bash
ps -o user,pid,ppid,cmd -C nginx                 # master (root) + workers (www-data)
nginx -V 2>&1 | tr ' ' '\n' | grep -E 'conf-path|error-log|http-log|with-http_(ssl|realip|stub_status)'
ls -l /etc/nginx/sites-enabled/ /etc/nginx/conf.d/
sudo nginx -T 2>/dev/null | grep -E '^# configuration file'   # every file that is live
```

```
USER         PID    PPID CMD
root        3101       1 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
www-data    3102    3101 nginx: worker process
www-data    3103    3101 nginx: worker process
```

**Hands-on lab (test VM only)**

**Step 1.** On snapshot A (Apache holds port 80), install nginx and watch it fail:

```bash
sudo apt install -y nginx
```

```
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
Job for nginx.service failed because the control process exited with error code.
dpkg: error processing package nginx (--configure):
```

→ Topic 1.3 again: the package's default site wants port 80.

**Step 2.** Fix: change both `listen` lines in `/etc/nginx/sites-available/default`
to `8088` (`listen 8088 default_server;` and `listen [::]:8088 default_server;`), then
`sudo nginx -t && sudo systemctl start nginx && sudo dpkg --configure -a`.
`curl -sI http://localhost:8088/` returns `Server: nginx/1.24.0 (Ubuntu)`.

**How it breaks**

| Error text | Cause | First command |
|---|---|---|
| `bind() to 0.0.0.0:80 failed (98: Address already in use)` | Port owned by another process | `sudo ss -ltnp 'sport = :80'` |
| `worker_connections are not enough` | Connection limit reached | Raise `worker_connections` (and `worker_rlimit_nofile`) |
| Headers missing in one location only | Array directive inheritance | `sudo nginx -T`, check that location |

**Why it matters for troubleshooting**

`nginx -T` gives you the full, merged config in one stream, which is the first
thing to read on any nginx box you did not build.

**Next step**

Topic 3.2: how nginx picks a server block.

### 3.2 Server blocks: listen, server_name, default_server

**Level:** [L2 · Mid]

**Concept**

Selection mirrors Apache's two steps:

1. **listen**: keep the server blocks whose `listen` matches the connection's
   address and port.
2. **server_name**, in this order: exact name → longest wildcard starting with
   `*` (`*.example.com`) → longest wildcard ending with `*` (`mail.*`) → first
   matching regex (`~^api\d+\.example\.com$`) in config order. No match → the
   block marked `default_server` on that listen socket, or else the **first**
   block defined for it.

Write an explicit catch-all so unknown names never see a real site:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    # 444 = close the connection without any response (nginx-specific)
    return 444;
}
server {
    listen 443 ssl default_server;
    server_name _;
    # refuse TLS for unknown SNI instead of showing some site's certificate (nginx 1.19.4+)
    ssl_reject_handshake on;
}
```

**Key terms**

| Term | Meaning |
|---|---|
| `server_name _` | A name that never matches; the convention for catch-alls |
| `default_server` | Flag on `listen`, one per address:port |
| `$host` | Host header (lower-cased, port stripped), or `server_name` if absent |

**See it on a real system**

```bash
sudo nginx -T 2>/dev/null | grep -nE '^\s*(server_name|listen)\b'
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: unknown.example.com' http://127.0.0.1:8088/
```

**Hands-on lab (test VM only)**

**Step 1.** Create two sites on 8088 that return their names:

```bash
sudo tee /etc/nginx/sites-available/lab.conf >/dev/null <<'EOF'
server { listen 8088; server_name site-a.example.com; return 200 "nginx site A\n"; }
server { listen 8088; server_name *.site-b.example.com site-b.example.com; return 200 "nginx site B\n"; }
EOF
sudo ln -s /etc/nginx/sites-available/lab.conf /etc/nginx/sites-enabled/lab.conf
sudo nginx -t && sudo systemctl reload nginx
for h in site-a.example.com dev.site-b.example.com nothing.example.com; do
  printf '%-25s ' "$h"; curl -s -H "Host: $h" http://127.0.0.1:8088/ || echo '(empty reply)'
done
```

→ `nothing.example.com` lands on the stock `default` site, because it holds `default_server` for 8088.

**Step 2.** Break it: add a third block with `server_name site-a.example.com` on 8088.
`nginx -t` warns `conflicting server name "site-a.example.com" on 0.0.0.0:8088, ignored`
and the second definition never answers. Remove it.

**Step 3.** Replace the stock default with the 444 catch-all (port 8088): the unknown
name now gets `curl: (52) Empty reply from server`.

**How it breaks**

| Symptom / error text | Cause | Fix |
|---|---|---|
| Unknown names show a real site | No explicit `default_server` | Catch-all block |
| `conflicting server name ... ignored` | Same name twice on one socket | Remove the duplicate |
| `could not build server_names_hash, you should increase server_names_hash_bucket_size` | Long or many names | `server_names_hash_bucket_size 128;` in `http` |
| Wrong certificate for unknown names | No TLS catch-all | `ssl_reject_handshake on;` |

**Why it matters for troubleshooting**

Same lesson as Apache: always ask "which block matched?" first. The access log
does not tell you by default; add `$server_name` to your `log_format` (topic 3.6).

**Next step**

Topic 3.3: once a server is chosen, which `location` handles the path.

### 3.3 Location matching order

**Level:** [L2 · Mid]

**Concept**

nginx chooses one `location` per request with this algorithm:

```
1. Exact match  location = /path      → if it matches, use it, stop.
2. Find the LONGEST matching prefix   (location /path/ and location ^~ /path/), remember it.
3. If that longest prefix has ^~      → use it, stop (regexes are not checked).
4. Check regex locations ~ (case-sensitive) and ~* (case-insensitive) IN CONFIG ORDER;
   the first that matches wins.
5. No regex matched                   → use the prefix remembered in step 2.
```

Order in the file matters only for regexes. Prefix locations are chosen by
length, not position.

**Key terms**

| Modifier | Type | Note |
|---|---|---|
| `=` | Exact | Fastest; good for `/` or `/health` |
| (none) | Prefix | Longest wins, but a regex can still override it |
| `^~` | Prefix | If it is the longest prefix, regexes are skipped |
| `~` / `~*` | Regex | First match in config order wins |
| `@name` | Named | Only for internal redirects (`try_files ... @app`) |

**See it on a real system**

```bash
sudo nginx -T 2>/dev/null | grep -nE '^\s*location\b'
```

**Hands-on lab (test VM only)**

**Step 1.** A server that tells you which location matched:

```bash
sudo tee /etc/nginx/sites-available/loc.conf >/dev/null <<'EOF'
server {
    listen 8088;
    server_name loc.example.com;
    location = /              { return 200 "1 exact =/\n"; }
    location /                { return 200 "2 prefix /\n"; }
    location /images/         { return 200 "3 prefix /images/\n"; }
    location ^~ /static/      { return 200 "4 prefix ^~ /static/\n"; }
    location ~* \.(png|jpg)$  { return 200 "5 regex png/jpg\n"; }
}
EOF
sudo ln -s /etc/nginx/sites-available/loc.conf /etc/nginx/sites-enabled/loc.conf
sudo nginx -t && sudo systemctl reload nginx
for p in / /index.html /images/a.png /images/a.txt /static/a.png; do
  printf '%-16s ' "$p"; curl -s -H 'Host: loc.example.com' "http://127.0.0.1:8088$p"
done
```

```
/                1 exact =/
/index.html      2 prefix /
/images/a.png    5 regex png/jpg
/images/a.txt    3 prefix /images/
/static/a.png    4 prefix ^~ /static/
```

→ `/images/a.png` went to the regex although `/images/` is a longer prefix:
regexes beat plain prefixes. `^~` is how you stop that.

**Step 2.** Predict, then test, what happens if you remove `^~` from `/static/`.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Static images served by the app (or 404) | A regex location (`~ \.php$`, image regex) caught them | `^~` on the static prefix |
| A new location "is ignored" | An earlier regex matches first | Reorder regexes or use `=`/`^~` |
| 404 for files that exist with `alias` | `alias` replaces the location prefix, `root` appends to it | `location /files/ { alias /srv/files/; }` (both slashes) |

**Why it matters for troubleshooting**

When nginx serves the wrong thing for a path, the answer is almost always in
this algorithm. Make the test server above and you will never guess again.

**Next step**

Topic 3.4: the most common location body of all, `proxy_pass`.

### 3.4 proxy_pass, upstreams and the trailing slash

**Level:** [L2 · Mid]

**Concept**

`proxy_pass` forwards the request. Whether nginx **rewrites the path** depends
on one detail: does the `proxy_pass` URL contain a URI part (anything after
host:port, even just `/`)?

| location | proxy_pass | Request | Backend receives |
|---|---|---|---|
| `/app/` | `http://127.0.0.1:8000` | `/app/x` | `/app/x` (passed unchanged) |
| `/app/` | `http://127.0.0.1:8000/` | `/app/x` | `/x` (prefix replaced by `/`) |
| `/app/` | `http://127.0.0.1:8000/v2/` | `/app/x` | `/v2/x` |
| `/app` | `http://127.0.0.1:8000/` | `/app/x` | `//x` (double slash, a classic bug) |
| `~ ^/app/` (regex) | `http://127.0.0.1:8000/` | n/a | `nginx -t` error: cannot have URI part in a regex location |

`upstream` blocks give a backend pool a name, with health and keep-alive options:

```nginx
upstream crm_backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=10s;
    server 127.0.0.1:8001 backup;
    # reuse connections to the backend; needs HTTP/1.1 and an empty Connection header
    keepalive 32;
}
server {
    listen 80;
    server_name crm.example.com;
    location / {
        proxy_pass http://crm_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
}
```

DNS gotcha: host names in `proxy_pass` and `upstream` are resolved **once**, at
start or reload. A container that gets a new IP is not followed, and a name
that does not resolve at start stops nginx from starting
(`host not found in upstream`). With Docker, use a `resolver 127.0.0.11` plus a
variable in `proxy_pass`, or simply reload nginx after the change. Since nginx
1.27.3 (not the 1.24 in Ubuntu 24.04), open-source nginx can also re-resolve
`upstream` servers with the `resolve` parameter on `server` plus a `resolver`;
check `nginx -v` before relying on it.

**Key terms**

| Term | Meaning |
|---|---|
| `max_fails` / `fail_timeout` | Passive health check: mark a server down after N failures for T seconds |
| `backup` | Used only when the others are down |
| `proxy_next_upstream` | Which errors make nginx try the next server |

**See it on a real system**

```bash
sudo nginx -T 2>/dev/null | grep -nE '^\s*(upstream|server\s+[0-9a-z]|proxy_pass)'
```

**Hands-on lab (test VM only)**

With the whoami container on `127.0.0.1:18080` (topic 1.5), add three locations to
the `loc.example.com` server: `location /a/ { proxy_pass http://127.0.0.1:18080; }`,
`location /b/ { proxy_pass http://127.0.0.1:18080/; }`,
`location /c { proxy_pass http://127.0.0.1:18080/; }`. Reload and request `/a/x`,
`/b/x`, `/c/x`; whoami's request line shows exactly what arrived (`GET /a/x`,
`GET /x`). For `/c/x` whoami received `//x`, and its Go router answers
`301 Moved Permanently` to the cleaned path `/x` instead of echoing; use
`curl -si` to see it. That redirect is the proof of the double slash. Then stop
whoami and request `/a/x`: **502**.

**How it breaks**

| Error text (error.log) | Status | Cause |
|---|---|---|
| `connect() failed (111: Connection refused) while connecting to upstream` | 502 | Backend down or wrong port |
| `upstream prematurely closed connection while reading response header from upstream` | 502 | Backend crashed or was killed mid-request (gunicorn timeout) |
| `no live upstreams while connecting to upstream` | 502 | All servers marked failed |
| `upstream timed out (110: Connection timed out) while reading response header` | 504 | Backend slower than `proxy_read_timeout` |
| `connect() to 127.0.0.1:8000 failed (13: Permission denied)` (RHEL) | 502 | SELinux: `setsebool -P httpd_can_network_connect 1` |
| `host not found in upstream "app:8000"` | nginx will not start | Name does not resolve at start |

**Why it matters for troubleshooting**

The trailing-slash table explains a large share of "works at `/` but every
sub-path is 404" tickets, in nginx and, in a different form, in Apache.

**Next step**

Topic 3.5: the headers, timeouts and limits every proxied location needs.

### 3.5 Proxy headers, timeouts, body size and real IP

**Level:** [L2 · Mid]

**Concept**

By default nginx sends the backend `Host: $proxy_host` (the upstream's own
name), `Connection: close`, and **no** `X-Forwarded-*` headers. Almost every
proxied location needs the same additions, so keep them in one snippet:

```nginx
# /etc/nginx/snippets/proxy-common.conf  (include it inside each proxied location)
proxy_http_version 1.1;
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host  $host;
proxy_set_header Upgrade           $http_upgrade;
proxy_set_header Connection        $connection_upgrade;
proxy_connect_timeout 5s;
proxy_read_timeout    60s;
proxy_send_timeout    60s;
```

The WebSocket `map` goes in the `http` context (for example in `conf.d/websocket-map.conf`):

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    # empty Connection header keeps upstream keepalive working; use close if you do not use keepalive
    ''      '';
}
```

Limits and buffering, per server or location:

```nginx
# default is 1m; larger uploads get 413
client_max_body_size 50m;
# long-lived WebSocket or slow report endpoints only
location /ws/ {
    include snippets/proxy-common.conf;
    proxy_pass http://127.0.0.1:8000;
    proxy_read_timeout 3600s;
}
# Server-Sent Events / streaming: do not buffer the response
location /events/ {
    include snippets/proxy-common.conf;
    proxy_pass http://127.0.0.1:8000;
    proxy_buffering off;
}
```

Real client IP when nginx itself is behind another proxy (Traefik, a load balancer):

```nginx
set_real_ip_from  172.16.0.0/12;
real_ip_header    X-Forwarded-For;
real_ip_recursive on;
```

**Key terms**

| Term | Meaning |
|---|---|
| `$proxy_add_x_forwarded_for` | Incoming `X-Forwarded-For` plus `$remote_addr` |
| `$scheme` | `http` or `https` as nginx received it (behind another proxy it is `http`: forward the upstream's header instead) |
| `proxy_request_buffering` | Read the whole body before contacting the backend (default on) |

**See it on a real system**

```bash
sudo nginx -T 2>/dev/null | grep -nE 'proxy_set_header|client_max_body_size|_timeout|proxy_buffering|real_ip'
```

**Hands-on lab (test VM only)**

**Step 1.** Proxy `/w/` to whoami with **no** headers and look at what arrives
(`Host: 127.0.0.1:18080`, no forwarded headers). Add the snippet and compare.

**Step 2.** Break it: `client_max_body_size 1k;` then
`head -c 5000 /dev/zero | curl -s -o /dev/null -w '%{http_code}\n' --data-binary @- -H 'Host: loc.example.com' http://127.0.0.1:8088/w/`
→ `413`, and error.log says `client intended to send too large body: 5000 bytes`.
Restore a sane value.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| App builds links to `127.0.0.1:8000` | Host not forwarded | `proxy_set_header Host $host;` |
| Redirect loop / mixed content | No `X-Forwarded-Proto` | Snippet above |
| 413 on uploads | `client_max_body_size` 1m default | Raise it where uploads happen |
| WebSocket closes every 60 s | `proxy_read_timeout` | Raise it for that location, or ping from the app |

**Why it matters for troubleshooting**

Most nginx proxy bugs are one missing line from that snippet. Compare a broken
location with the snippet before reading anything else.

**Next step**

Topic 3.6: proving a config is valid and reading what nginx logs.

### 3.6 nginx -t, nginx -T and logs

**Level:** [L2 · Mid]

**Concept**

`nginx -t` checks syntax and that files and certificates load; `nginx -T` does
the same **and prints the full merged config**. Always run `nginx -t` before a
reload: a failed reload leaves the old config running, a failed restart leaves
nothing running.

The default access log does not show which backend answered or how long it
took. Add a format that does:

```nginx
log_format upstream_timing '$remote_addr - $remote_user [$time_local] "$request" '
                           '$status $body_bytes_sent "$http_referer" "$http_user_agent" '
                           'host=$host server=$server_name rt=$request_time '
                           'ua=$upstream_addr us=$upstream_status urt=$upstream_response_time';
access_log /var/log/nginx/access.log upstream_timing;
```

**Key terms**

| Field | Meaning |
|---|---|
| `$request_time` | Total time nginx spent on the request (s) |
| `$upstream_response_time` | Time the backend took; `rt` much bigger than `urt` = slow client or network |
| `$upstream_status` | What the backend returned (vs `$status`, what nginx returned) |

**See it on a real system**

```bash
sudo nginx -t
sudo nginx -T 2>/dev/null | less                 # search with / for a server_name
sudo tail -F /var/log/nginx/error.log
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn   # status histogram (combined format)
```

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

An error-log line, decoded:

```
2026/10/03 10:12:01 [error] 3102#3102: *57 connect() failed (111: Connection refused) while connecting to upstream, client: 198.51.100.7, server: crm.example.com, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:8000/", host: "crm.example.com"
```

→ Connection 57, server block `crm.example.com`, the exact upstream that refused.

**Hands-on lab (test VM only)**

Switch the lab server to the `upstream_timing` format, send requests to `/w/`
with whoami running and stopped, and read `us=` and `urt=` for each. Then run
SadServers scenarios tagged nginx ([sadservers.com/scenarios](https://sadservers.com/scenarios)).

**How it breaks**

| Symptom | First command |
|---|---|
| Reload "did nothing" | `sudo nginx -t` (the reload was refused) |
| `[emerg] unknown directive` | Module not built in: `nginx -V` |
| `SSL_CTX_use_PrivateKey ... key values mismatch` | Key does not belong to the certificate (compare as in topic 2.6) |

**Why it matters for troubleshooting**

With `ua`, `us` and `urt` in the log, nginx tells you which backend failed and
how slow it was, which is most of a 5xx investigation.

**Next step**

Section 4: Traefik, the proxy Dokploy installs and you must be able to debug without its UI.

---

## 4. Traefik in depth

> 📚 **Study path:** 1) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress → *Traefik Overview* → *Demo/Lab: Traefik Installation* → *Demo: Traefik Observability* ([course](https://kodekloud.com/courses/kubernetes-networking), [Traefik Overview notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)); it is Traefik on Kubernetes, but entryPoints, routers, services and access logs carry over · 2) Docs: Traefik [Docker quick start](https://doc.traefik.io/traefik/getting-started/docker/) and [Docker routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/) · 3) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* ([YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI), 32 min, v3 syntax) · 4) Note: topics 4.1–4.9 here · 5) Practice: the capstone (section 8), then the Ops Ladder L3 drill "Traefik 502 from logs alone".

Everything here is Traefik **v3** (what current Dokploy installs). The
[Traefik documentation](https://doc.traefik.io/traefik/) is versioned; make sure
the version selector matches `docker inspect --format '{{.Config.Image}}' dokploy-traefik`.

### 4.1 Static vs dynamic configuration

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

Traefik has two kinds of configuration, and mixing them up is the most common
beginner mistake:

```
STATIC: read once at start; change = restart        DYNAMIC: hot-reloaded from providers
(traefik.yml, OR CLI flags, OR env vars)              (Docker labels, Swarm labels, files, Kubernetes)
 ├─ entryPoints   web :80, websecure :443                    │
 ├─ providers     docker, swarm, file ───────────────────────┘ watched
 ├─ certificatesResolvers  letsencrypt (ACME)
 ├─ api / dashboard, log, accessLog
 └─ serversTransport (global defaults)

REQUEST FLOW
client ─► entryPoint ─► router (rule matches?) ─► middlewares ─► service ─► server (container IP:port)
          websecure     Host(`crm.example.com`)   redirect,auth   crm        http://10.0.1.7:8069
```

- **Static**: how Traefik itself starts: which ports it listens on
  (entryPoints), where it gets routing config (providers), how it gets
  certificates (resolvers), logging, API. Use exactly **one** source (file, CLI
  or env); they are mutually exclusive. Change it, restart Traefik.
- **Dynamic**: the routing itself: routers, services, middlewares, TLS
  certificates and options, serversTransports. Providers deliver it and Traefik
  applies it **without restart**. A semantic error (a router pointing at a
  missing service or middleware) disables only that router. A YAML **syntax**
  error is worse: in current v3 releases the file provider rejects the whole
  reload, logs `Error occurred during watcher callback` with the file name, and
  keeps serving the last good config, so your edit seems to "do nothing". After
  the next restart the file provider cannot load at all and every file-based
  route is gone. Validate YAML before you save it.

In Dokploy: static config is `/etc/dokploy/traefik/traefik.yml`; dynamic config
is every file in `/etc/dokploy/traefik/dynamic/` (file provider) plus the
labels on containers and Swarm services (docker and swarm providers).

**Key terms**

| Term | Meaning |
|---|---|
| Provider | A source of dynamic config: `docker`, `swarm`, `file`, `kubernetesIngress`, `kubernetesCRD`, `kubernetesGateway` |
| `@provider` suffix | Every object is namespaced: `crm@file`, `crm-web@docker`, `api@internal` |
| Hot reload | Dynamic changes applied live, no dropped connections |

**See it on a real system**

```bash
docker ps --filter name=traefik --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker service ls --filter name=traefik          # some Dokploy installs run Traefik as a Swarm service
sudo cat /etc/dokploy/traefik/traefik.yml        # static
sudo ls -l /etc/dokploy/traefik/dynamic/         # dynamic files
docker inspect dokploy-traefik --format '{{json .Args}}'    # CLI flags, if any were used
```

A static file roughly like the one a recent Dokploy writes (read your own; it
changes between versions):

```yaml
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
api:
  insecure: true
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/dokploy/traefik/dynamic/acme.json
      httpChallenge:
        entryPoint: web
```

→ Three providers, two entryPoints, one ACME resolver called `letsencrypt`.
Every label or file you write must use those exact names (`web`, `websecure`,
`letsencrypt`).

**Hands-on lab (test VM only)**

On the capstone Traefik (8.2): change a **dynamic** thing (edit a router rule in
`dynamic/apache.yml`) and test immediately, no restart. Then change a **static**
thing (`--log.level=DEBUG` in `compose.yaml`): nothing happens until
`docker compose up -d` recreates the container. Set it back to INFO.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Edited `traefik.yml`, nothing changed | Static config needs a restart | `docker restart dokploy-traefik` (in a quiet moment) |
| Added CLI flags, the file's settings vanished | Static sources are mutually exclusive | Use one source |
| Edit to a dynamic file has no effect | YAML syntax error: the file provider kept the last good config | `docker logs --tail 50 dokploy-traefik`, look for `watcher callback` and the file name |
| One app 404s after editing a dynamic file | Its router references something missing, or the rule changed | Routers API `error` field (topic 4.3) |
| Every file-based site 404s right after a restart | A YAML syntax error stopped the file provider from loading | Fix the file, `docker restart dokploy-traefik` |
| After restart Traefik will not come up at all | Static YAML error | Logs; restore the backup of `traefik.yml` |

**Why it matters for troubleshooting**

"Do I need a restart?" has a precise answer, and restarting Traefik on a Dokploy
host interrupts **every** site. Know which layer you touched.

**Next step**

Topic 4.2: the ports Traefik listens on.

### 4.2 EntryPoints

**Level:** [L3 · Senior]

**Concept**

An entryPoint is a listening socket **inside** Traefik's container, plus
settings for everything arriving on it. Docker publishing (`-p 443:443`) is what
connects the host port to it. Typical static config:

```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:              # global HTTP → HTTPS for every router on web
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
    http3: {}                    # also needs 443/udp published
    forwardedHeaders:
      trustedIPs:                # only when an LB/CDN in front sends X-Forwarded-*
        - "192.0.2.5/32"
    transport:
      respondingTimeouts:
        readTimeout: 300s        # v3 default 60s: raise for slow, large uploads
        idleTimeout: 180s
```

Notes:

- A router with no `entryPoints` listens on all default entryPoints.
- `proxyProtocol.trustedIPs` on an entryPoint accepts PROXY protocol from a load
  balancer in front (L4 balancers that cannot add headers).
- The ACME HTTP-01 challenge keeps working with a global redirect: Traefik
  answers `/.well-known/acme-challenge/` before redirecting.

**Key terms**

| Term | Meaning |
|---|---|
| `web` / `websecure` | Conventional names; Dokploy uses them |
| `traefik` entryPoint | Port 8080, created when the API/dashboard is enabled insecurely |
| `respondingTimeouts` | Client-side timeouts: read, write, idle |

**See it on a real system**

```bash
docker port dokploy-traefik                     # host ports published to the container
sudo ss -ltnup '( sport = :80 or sport = :443 or sport = :8080 )'
sudo grep -nA12 '^entryPoints' /etc/dokploy/traefik/traefik.yml
```

```
443/tcp -> 0.0.0.0:443
443/udp -> 0.0.0.0:443
80/tcp -> 0.0.0.0:80
```

**Hands-on lab (test VM only)**

Add a third entryPoint `--entrypoints.alt.address=:8444` to the capstone Traefik,
publish `8444:8444`, and attach site-b's router only to `alt`. Request site-b on 80
(404) and on 8444 (works). This is how you can run a second, temporary entry
during a migration. Remove it.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Connection refused on 443 although Traefik runs | Port not published, or published on another IP | `docker port`, `ss -ltnp` |
| Router works on 80, 404 on 443 | Router attached only to `web`, or no `tls` | Topic 4.3 |
| Uploads over a minute fail | v3 `readTimeout` 60 s | Raise it on that entryPoint |
| Client IP is the load balancer's | LB not in `forwardedHeaders.trustedIPs` | Add its exact IP |

**Why it matters for troubleshooting**

A request that never reaches an entryPoint never reaches any router. "Is
Traefik even listening there?" is the first check, just as with Apache's `Listen`.

**Next step**

Topic 4.3: routers, the part that decides which app gets a request.

### 4.3 Routers: rules and priority

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

A router connects an entryPoint to a service when its **rule** matches.

| Matcher (v3) | Example |
|---|---|
| `Host` | ``Host(`crm.example.com`)`` |
| `HostRegexp` | ``HostRegexp(`^[a-z]+\.example\.com$`)`` (Go regex in v3) |
| `PathPrefix` / `Path` / `PathRegexp` | ``PathPrefix(`/api`)`` |
| `Method` | ``Method(`POST`)`` |
| `Header` / `HeaderRegexp` | ``Header(`X-Canary`, `1`)`` |
| `Query` | ``Query(`preview`, `true`)`` |
| `ClientIP` | ``ClientIP(`198.51.100.0/24`)`` |

Combine with `&&`, `||`, `!` and parentheses.

v2 habits that break in v3: ``Host(`a.example.com`, `b.example.com`)`` (several
names in one `Host`) is no longer valid, so join two `Host` matchers with `||`;
and v2's `{name:regex}` style in `HostRegexp` is gone.

**Priority**: when several rules match, the router with the highest priority
wins. By default priority = **length of the rule string**, so the more specific
(longer) rule wins. Set `priority` explicitly when that guess is wrong. This is
also your migration tool: a longer rule such as
``Host(`crm.example.com`) && ClientIP(`198.51.100.0/24`)`` sends only your
testers to the new app (topic 7.4).

**TLS**: a router **with** a `tls` section only matches HTTPS requests; one
without it only matches plain HTTP. That is why Dokploy creates two routers per
domain: one on `web` (usually just redirecting) and one on `websecure` with
`tls.certResolver`.

File provider and Docker labels express the same router:

```yaml
http:
  routers:
    crm:
      entryPoints: [websecure]
      rule: "Host(`crm.example.com`)"
      service: crm
      middlewares: [secure-headers]
      tls:
        certResolver: letsencrypt
```

```
traefik.http.routers.crm.entrypoints=websecure
traefik.http.routers.crm.rule=Host(`crm.example.com`)
traefik.http.routers.crm.service=crm
traefik.http.routers.crm.middlewares=secure-headers@file
traefik.http.routers.crm.tls.certresolver=letsencrypt
```

**Key terms**

| Term | Meaning |
|---|---|
| Rule | Boolean expression over the request |
| Priority | Tie-breaker; default = rule length |
| `tls` | Makes the router HTTPS-only; `certResolver` asks ACME for its names |

**See it on a real system**

```bash
# All HTTP routers, their rule and status (needs the API, see topic 4.9)
curl -s http://127.0.0.1:8080/api/http/routers | jq -r '.[] | [.name, .status, .rule] | @tsv'
# Only the broken ones, with the reason
curl -s http://127.0.0.1:8080/api/http/routers | jq '.[] | select(.status != "enabled") | {name, status, error}'
```

```
site-a@file            enabled  Host(`site-a.example.com`)
site-b@file            enabled  Host(`site-b.example.com`)
crm-websecure@docker   disabled Host(`crm.example.com`)
{
  "name": "crm-websecure@docker",
  "status": "disabled",
  "error": [ "middleware \"secure-headers@file\" does not exist" ]
}
```

→ A disabled router is a 404 for its domain, and the API tells you exactly why.

**Hands-on lab (test VM only)**

**Step 1.** In the capstone dynamic file, add a router
``Host(`site-a.example.com`) && PathPrefix(`/api`)`` pointing to a whoami service
(`http://whoami:80`). Request `/api/x` (whoami answers: longer rule wins) and `/`
(Apache answers).

**Step 2.** Give the plain site-a router `priority: 1000` and request `/api/x`
again: now Apache answers, because explicit priority beats length.

**Step 3.** Remove the priority. Try the v2 form ``Host(`site-a.example.com`, `www.site-a.example.com`)``
and read the router error in the API, then rewrite it with `||`.

**How it breaks**

| Symptom | Cause | First check |
|---|---|---|
| `404 page not found` | No router matched (typo, wrong entryPoint, http vs https) | Routers API, `curl -v` Host |
| 404 only over HTTP | Router has `tls`, nothing on `web` | Add a `web` router (redirect) |
| The wrong app answers a path | Priority by length chose another router | Routers API: compare rules and priority |
| Router `disabled` | Missing middleware/service, bad rule syntax | `error` field in the API |

**Why it matters for troubleshooting**

Traefik's 404 means "no router matched", never "the app said 404". If the app
had answered, the body would be the app's.

**Next step**

Topic 4.4: services, where Traefik actually sends the request.

### 4.4 Services: loadBalancer.server.port and friends

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

A service is a pool of servers. With the **file provider** you list URLs; with
the **Docker/Swarm providers** Traefik builds the URL itself from the
container's IP on a shared network plus a port:

```yaml
http:
  services:
    crm:
      loadBalancer:
        servers:
          - url: "http://10.0.1.7:8069"
        passHostHeader: true          # default: backend sees the client's Host
        healthCheck:
          path: /health
          interval: 10s
          timeout: 3s
        sticky:
          cookie:
            name: crm_lb
```

Port selection for Docker containers:

- Label `traefik.http.services.NAME.loadbalancer.server.port=8069` → used.
- No label, and the container **exposes exactly one** port → that port.
- No label and **several** exposed ports → Traefik silently takes the **lowest**
  one (80 rather than 8080), which is often the wrong one: set the label.
- No label and **zero** exposed ports → you must set the label. In
  **Swarm mode the label is always required**.

Network selection: if the container is on several networks, Traefik may pick an
IP on a network it cannot reach, giving a 504 after the dial timeout. Pin it
with `traefik.docker.network=dokploy-network` (or `providers.docker.network`,
which Dokploy sets).

Two service types matter for migrations (file provider only):

```yaml
http:
  services:
    crm-canary:
      weighted:                       # send 10 % of traffic to the new app
        services:
          - name: crm-legacy
            weight: 9
          - name: crm-new
            weight: 1
    crm-shadow:
      mirroring:                      # copy traffic to the new app, ignore its answers
        service: crm-legacy
        mirrors:
          - name: crm-new
            percent: 10
```

**Key terms**

| Term | Meaning |
|---|---|
| `passHostHeader` | Forward the client's Host (true by default) |
| `serversTransport` | How Traefik talks to backends: TLS trust, timeouts |
| `scheme` | `http` or `https` toward the backend |

**See it on a real system**

```bash
curl -s http://127.0.0.1:8080/api/http/services | jq -r '.[] | [.name, .status, (.loadBalancer.servers // [] | map(.url) | join(","))] | @tsv'
# What Traefik thinks the container's IP and port are vs what the app listens on
docker inspect CONTAINER --format '{{range $n, $c := .NetworkSettings.Networks}}{{$n}}={{$c.IPAddress}} {{end}}'
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
```

```
apache@file        enabled   http://host.docker.internal:8080
crm-web@docker     enabled   http://10.0.1.7:3000
```

→ If `ss -ltn` inside the container shows `127.0.0.1:8069` or only `:8069`,
while Traefik targets `:3000`, you have found your 502.

**Hands-on lab (test VM only)**

**Step 1.** Add a health check to the capstone `apache` service (`path: /`,
`interval: 5s`, `hostname: site-a.example.com`; without `hostname` the check
sends `Host: host.docker.internal:8080`, which lands on Apache's default vhost
and fails if that is the 404 catch-all from 1.2), stop Apache, and request site-a: after the next check you get
`503 Service Unavailable` instead of 502, and the services API shows the server
as down.

**Step 2.** Start Apache; within one interval site-a is back.

**How it breaks**

| Symptom / log text | Cause | Fix |
|---|---|---|
| 502, `dial tcp 10.0.1.7:3000: connect: connection refused` | Wrong port, or app bound to 127.0.0.1 inside the container | Port label = the port the app listens on; bind 0.0.0.0 |
| 504 after 30 s, `dial tcp ...: i/o timeout` | Unreachable network picked, or firewall | `traefik.docker.network`; UFW rules for host backends |
| Router error `port is missing` | No exposed port (or a Swarm service) and no port label | Add the port label |
| 502 although the app runs, container exposes several ports | No port label, Traefik picked the lowest exposed port | Add the port label |
| 503 `no available server` | Every server failed its health check | Fix the app or the health path |

**Why it matters for troubleshooting**

A 502 from Traefik is almost always a service problem, not a routing problem:
the router matched, the backend did not answer.

**Next step**

Topic 4.5: middlewares, the steps between router and service.

### 4.5 Middlewares

**Level:** [L3 · Senior]

**Concept**

Middlewares modify a request or response between router and service. They run
in the order listed on the router. Defined once, used by any router, referenced
across providers with the `@provider` suffix.

| Middleware | Typical use |
|---|---|
| `redirectScheme` | HTTP → HTTPS (`scheme: https`, `permanent: true`) |
| `redirectRegex` | www → apex, old paths |
| `headers` | HSTS (`stsSeconds`), security headers, `customRequestHeaders` (e.g. set `X-Forwarded-Proto`) |
| `basicAuth` | Protect an admin UI (`users: ["admin:HASH"]` or `usersFile`) |
| `ipAllowList` (v2: `ipWhiteList`) | Office-only paths |
| `rateLimit` | `average`, `burst`, `period` per client IP |
| `stripPrefix` / `addPrefix` | App mounted under `/app` but expects `/` |
| `compress`, `buffering`, `retry`, `chain`, `errors` | gzip, nginx-style buffering, retries, grouping, custom error pages |

```yaml
http:
  middlewares:
    to-https:
      redirectScheme:
        scheme: https
        permanent: true
    secure-headers:
      headers:
        stsSeconds: 31536000
        contentTypeNosniff: true
        frameDeny: true
    admin-auth:
      basicAuth:
        users:
          - "admin:$2y$05$EXAMPLEHASHEXAMPLEHASHEXAMPLEHASHEXAMPLEHASHEXAMPL"
    office-only:
      ipAllowList:
        sourceRange: ["198.51.100.0/24"]
    api-limit:
      rateLimit:
        average: 20
        burst: 40
```

The `$` trap with labels: in a Compose file `$` starts a variable, so every `$`
in a bcrypt hash must be doubled in labels (`$$2y$$05$$...`). In a dynamic YAML
file, write it once. Generate a hash with `htpasswd -nB admin` (package
`apache2-utils`; it prompts for the password so it does not land in your shell
history).

**Key terms**

| Term | Meaning |
|---|---|
| Middleware chain | The ordered list on a router |
| `@file` / `@docker` | Which provider defines the middleware |
| `ipStrategy.depth` | For `ipAllowList`/`rateLimit` behind another proxy: which `X-Forwarded-For` entry is the client |

**See it on a real system**

```bash
curl -s http://127.0.0.1:8080/api/http/middlewares | jq -r '.[] | [.name, .type, .status] | @tsv'
sudo cat /etc/dokploy/traefik/dynamic/middlewares.yml
```

**Hands-on lab (test VM only)**

**Step 1.** Add `admin-auth` (with a real hash from `htpasswd -nB admin`) to
site-b's router: `curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-b.example.com' http://127.0.0.1/` → 401;
with `-u admin:PASSWORD` → 200.

**Step 2.** Put the same hash in a **compose label** without doubling the `$`
signs, recreate, and watch every login fail with 401. Double them, recreate, fixed.

**Step 3.** Add `api-limit` with `average: 2, burst: 2` and fire 20 quick requests:
`for i in $(seq 20); do curl -s -o /dev/null -w '%{http_code} ' -H 'Host: site-b.example.com' http://127.0.0.1/; done` → a run of 429s.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| 404 for a whole domain | Router references a middleware that does not exist (`error` in routers API) | Fix the name and `@provider` |
| Basic auth always 401 | `$` not doubled in Compose labels, or wrong hash type | Double `$`; bcrypt from `htpasswd -B` |
| Everyone rate-limited together | Limiting by the address of a proxy in front | `sourceCriterion.ipStrategy.depth` |
| App gets wrong paths under `/app` | Missing `stripPrefix` | Add it, or make the app path-aware |

**Why it matters for troubleshooting**

Middlewares are where "small" security changes break whole domains. After any
middleware edit, check the routers API for `disabled` routers.

**Next step**

Topic 4.6: providers, where all these routers and services come from.

### 4.6 Providers: Docker, Swarm and file

**Level:** [L3 · Senior]

**Concept**

| Provider | Reads | Key settings | Dokploy uses it for |
|---|---|---|---|
| `docker` | Labels on **containers** | `exposedByDefault: false`, `network`, `endpoint` (socket) | Docker Compose deployments |
| `swarm` (v3 has a separate provider) | Labels on **Swarm services** (`deploy.labels` in a stack file) | Port label mandatory | Stack deployments |
| `file` | YAML/TOML files in a directory | `directory`, `watch: true` | Applications' domains, the Dokploy UI, shared middlewares, your own extra routes |
| Kubernetes (`kubernetesIngress`, `kubernetesCRD`, `kubernetesGateway`) | Cluster objects | | Not Dokploy; see topic 6.3 |

Three traps:

- **Swarm labels go under `deploy.labels`**, not top-level `labels`. Top-level
  labels land on the containers and the swarm provider never sees them.
- **`exposedByDefault: false`** (Dokploy's setting) means nothing is routed
  without `traefik.enable=true`.
- **The Docker socket is root.** Mounting `/var/run/docker.sock:ro` does *not*
  make it read-only for the API: anyone who controls Traefik controls the host.
  Keep the dashboard private, keep Traefik updated, and consider a socket proxy
  for exposed setups.

The file provider: mount the **directory**, not a single file. Editors that save
by replacing the file break watches on single-file bind mounts. Dokploy mounts
the whole `dynamic/` directory, which is the right way.

**Key terms**

| Term | Meaning |
|---|---|
| `traefik.enable=true` | Opt a container in when `exposedByDefault` is false |
| `traefik.docker.network` | Which network's IP Traefik uses for the container |
| Constraints | Filter which containers a provider considers |

**See it on a real system**

```bash
docker inspect --format '{{json .Config.Labels}}' CONTAINER | jq 'with_entries(select(.key | startswith("traefik")))'
docker service inspect --format '{{json .Spec.Labels}}' SERVICE | jq        # Swarm service labels
docker network inspect dokploy-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

**Hands-on lab (test VM only)**

**Step 1.** In the capstone compose file (8.2), remove `traefik.enable=true`
from whoami's labels and run `docker compose up -d`: with
`--providers.docker.exposedbydefault=false` the router no longer exists (404).
Put the label back, `docker compose up -d`, and it works again.

**Step 2.** Attach whoami to a second network that Traefik is not on, without
`traefik.docker.network`. Recreate a few times: sometimes Traefik picks the
unreachable IP and requests hang until 504. Add the label to fix.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| 404, container has labels | Missing `traefik.enable=true`, or labels changed but not redeployed | Add; redeploy (labels are read from the running container) |
| Swarm service invisible to Traefik | Labels at top level instead of `deploy.labels`, or no port label | Move them |
| Intermittent 504 | Container on several networks | `traefik.docker.network` |
| Traefik logs `permission denied ... docker.sock` | Socket not mounted or wrong permissions | Check the mount |

**Why it matters for troubleshooting**

When Traefik "doesn't see" an app, the question is always: which provider should
deliver this router, and does that provider see the object at all?

**Next step**

Topic 4.7: certificates, the part that fails at 3 a.m. weeks after go-live.

### 4.7 Certificates: ACME resolvers and the default certificate

**Level:** [L3 · Senior]

**Concept**

A certificate resolver obtains and renews certificates from an ACME CA (Let's
Encrypt) for the names in router rules. Three challenge types:

| Challenge | How the CA verifies | Needs | Good for |
|---|---|---|---|
| HTTP-01 (`httpChallenge`) | Fetches `http://NAME/.well-known/acme-challenge/...` | Port 80 reachable **from the internet** for that name, DNS pointing at you | Public sites (Dokploy default) |
| TLS-ALPN-01 (`tlsChallenge`) | Special TLS handshake on 443 | Port 443 reachable directly (no TLS-terminating CDN in front) | Hosts where port 80 is closed |
| DNS-01 (`dnsChallenge`) | TXT record at `_acme-challenge.NAME` via your DNS provider's API | API token for the DNS provider | **Wildcards**, and **on-prem servers not reachable from the internet** |

For on-prem, DNS-01 is often the only option that works, because the CA cannot
reach your server.

`acme.json` holds account and certificates. It must be mode **600** or Traefik
refuses it. Back it up; losing it means re-issuing everything, and Let's
Encrypt rate limits (for example, a handful of duplicate certificates per week
and a few failed validations per hour) can lock you out mid-migration. Test with
the Let's Encrypt **staging** CA (`caServer`, see the Traefik ACME docs) first.

When no certificate matches the SNI, Traefik serves its self-signed
`TRAEFIK DEFAULT CERT`. You can replace the default, and load your own
certificates (private CA, purchased wildcard) through the file provider:

```yaml
tls:
  certificates:
    - certFile: /etc/dokploy/traefik/dynamic/certs/crm.example.com.crt
      keyFile:  /etc/dokploy/traefik/dynamic/certs/crm.example.com.key
  stores:
    default:
      defaultCertificate:
        certFile: /etc/dokploy/traefik/dynamic/certs/wildcard.example.com.crt
        keyFile:  /etc/dokploy/traefik/dynamic/certs/wildcard.example.com.key
```

Paths are **inside the container**. Anything under Dokploy's `dynamic/`
directory is visible to Traefik at the same path; a host path outside it is not.
Reusing your existing Let's Encrypt files this way gives instant valid TLS at
cutover (topic 7.1).

**Key terms**

| Term | Meaning |
|---|---|
| `certResolver` | Name of the resolver on a router (`letsencrypt` in Dokploy) |
| `acme.json` | Certificate storage; 600 permissions |
| Default certificate | Served when SNI matches nothing |
| `domains` (main/sans) | Ask for explicit names, e.g. a wildcard with DNS-01 |

**See it on a real system**

```bash
sudo ls -l /etc/dokploy/traefik/dynamic/acme.json            # -rw------- expected
sudo jq -r '.letsencrypt.Certificates[]?.domain.main' /etc/dokploy/traefik/dynamic/acme.json
docker logs dokploy-traefik 2>&1 | grep -iE 'acme|certificate|challenge' | tail -20
echo | openssl s_client -connect 127.0.0.1:443 -servername crm.example.com 2>/dev/null | openssl x509 -noout -subject -issuer -enddate
```

Typical ACME failures in the log (wrapped here for reading):

```
ERR Unable to obtain ACME certificate for domains error="unable to generate a certificate for the domains [crm.example.com]:
  acme: error: 400 :: urn:ietf:params:acme:error:connection :: ... Timeout during connect (likely firewall problem)"
ERR ... acme: error: 400 :: urn:ietf:params:acme:error:dns :: DNS problem: NXDOMAIN looking up A for crm.example.com
ERR ... acme: error: 403 :: urn:ietf:params:acme:error:unauthorized :: Invalid response from http://crm.example.com/.well-known/acme-challenge/...
```

→ firewall blocks port 80 from the internet / no DNS record yet / the name points
at another server (or a CDN answers the challenge).

**Hands-on lab (test VM only)**

**Step 1.** Without a public domain, practise the file-provider path: create a
small private CA and a certificate for site-a (or reuse the self-signed one from
topic 2.6), put the files in the capstone `dynamic/certs/` directory, add a
`tls.certificates` entry, and add `tls: {}` to site-a's websecure router.

**Step 2.** `openssl s_client -connect 127.0.0.1:443 -servername site-a.example.com`
now shows your certificate; `-servername nothing.example.com` still shows
`TRAEFIK DEFAULT CERT`. Configure `stores.default.defaultCertificate` and
repeat.

**Step 3.** If you own a domain and a public VPS, repeat with an ACME resolver
pointed at the staging CA, then break it by closing port 80 and read the error.

**How it breaks**

| Symptom | Cause | First check |
|---|---|---|
| Browser shows `TRAEFIK DEFAULT CERT` | ACME failed, or the router has no `tls`/resolver | Traefik logs for `acme` |
| Certificate never issued in Dokploy | Domain added before DNS pointed at the server | Fix DNS, then re-save the domain / restart Traefik |
| `permissions 644 for ... acme.json are too open, please use 600` | Wrong mode after a copy/restore | `sudo chmod 600 acme.json` |
| `too many certificates ... already issued` / `too many failed authorizations` | Rate limit | Use staging; wait; fix the cause first |
| Behind Cloudflare proxy: issuance fails or redirect loops | CDN terminates TLS / answers challenges | DNS-only during issuance, or DNS-01; SSL mode Full (strict) |

**Why it matters for troubleshooting**

Certificate failures are delayed failures. Check issuance right after adding a
domain, and alert on expiry (L4 drills in [Learn: performance & observability](32-learn-performance-observability.md)).

**Next step**

Topic 4.8: when Traefik should not decrypt at all.

### 4.8 TCP routers, HostSNI and passthrough

**Level:** [L3 · Senior]

**Concept**

TCP routers work at layer 4. On a shared entryPoint they are evaluated **before**
HTTP routers; if no TCP router matches, the HTTP routers get the connection.

- With TLS, a TCP router can match on SNI: ``HostSNI(`legacy.example.com`)``.
- `tls.passthrough: true` sends the still-encrypted stream to the backend, which
  must hold the certificate (topic 1.4).
- Without TLS there is no SNI, so the only valid rule is ``HostSNI(`*`)``: one
  service per entryPoint (typical for databases on their own port).

```yaml
tcp:
  routers:
    legacy-passthrough:
      entryPoints: [websecure]
      rule: "HostSNI(`legacy.example.com`)"
      service: legacy-apache-tls
      tls:
        passthrough: true
  services:
    legacy-apache-tls:
      loadBalancer:
        servers:
          - address: "192.0.2.10:8443"
```

The backend sees Traefik's IP. To pass the client IP over raw TCP, enable PROXY
protocol on the Traefik TCP service (see the TCP service docs for your version)
**and** on the backend (Apache: `RemoteIPProxyProtocol On`). Enable it on both
sides or neither: a mismatch breaks every connection.

**Key terms**

| Term | Meaning |
|---|---|
| `HostSNI` | TCP rule on the TLS ClientHello name |
| Passthrough | No decryption at Traefik |
| `address` | TCP services use `host:port`, not URLs |

**See it on a real system**

```bash
curl -s http://127.0.0.1:8080/api/tcp/routers | jq -r '.[] | [.name, .status, .rule] | @tsv'
echo | openssl s_client -connect 127.0.0.1:443 -servername legacy.example.com 2>/dev/null | openssl x509 -noout -issuer
```

**Hands-on lab (test VM only)**

**Step 1.** Use the Apache HTTPS vhost on 8443 from topic 2.6. Add the TCP router
above to the capstone dynamic file with ``HostSNI(`site-a.example.com`)`` and
`address: "host.docker.internal:8443"`.

**Step 2.** `curl -skv --resolve site-a.example.com:443:127.0.0.1 https://site-a.example.com/ 2>&1 | grep subject:`
shows **Apache's** self-signed certificate: Traefik did not decrypt. site-b,
still on HTTP routers, keeps Traefik's certificate.

**Step 3.** Add an HTTP middleware to site-a and notice it has no effect:
passthrough connections never reach HTTP routers. Remove the TCP router.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Passthrough name gets Traefik's certificate | TCP router missing or rule typo; HTTP router took it | TCP routers API |
| `HostSNI(*)` router swallows all TLS on the entryPoint | Catch-all TCP router on a shared entryPoint | Use a dedicated entryPoint for raw TCP |
| Every connection fails after enabling PROXY protocol | Only one side enabled | Both or neither |

**Why it matters for troubleshooting**

Passthrough is the quickest way to move 443 to Traefik while legacy sites keep
their own certificates, and its limits (no headers, no redirects) explain the
odd behaviour of those sites until you move them properly.

**Next step**

Topic 4.9: seeing what Traefik sees: API, dashboard and logs.

### 4.9 Dashboard, API, logs and access logs

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

Traefik explains itself through three channels:

- **API / dashboard**: the live routers, services and middlewares, with their
  status and errors. With `api.insecure: true` it is served on port 8080 inside
  the container (the `traefik` entryPoint). Never publish that to the internet.
  The secure way is a router to `api@internal` with authentication:

```yaml
http:
  routers:
    dashboard:
      entryPoints: [websecure]
      rule: "Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))"
      service: api@internal
      middlewares: [admin-auth, office-only]
      tls:
        certResolver: letsencrypt
```

- **Traefik log** (stdout, `docker logs`): config errors, ACME, provider events.
  `log.level` ERROR by default; DEBUG temporarily shows details such as
  `'502 Bad Gateway' caused by: dial tcp ...: connect: connection refused`.
- **Access log** (`accessLog`, off by default): one line per request, with the
  router and backend chosen. Formats `common` (default) or `json`; filters by
  status code and duration.

```yaml
log:
  level: INFO
accessLog:
  filePath: /var/log/traefik/access.log     # omit to log to stdout
  format: json
  filters:
    statusCodes: ["400-599"]
```

A `common`-format access line ends with request count, router, backend URL and
duration, which is everything you need for a 5xx:

```
192.168.56.1 - - [03/Oct/2026:10:15:02 +0000] "GET / HTTP/1.1" 502 11 "-" "curl/8.5.0" 41 "site-a@file" "http://host.docker.internal:8090" 1ms
```

→ Router `site-a@file` matched (so not a 404 problem), backend
`host.docker.internal:8090` refused (port problem). A request that matched no
router shows no router name (or does not appear at all, depending on version).

**Key terms**

| Term | Meaning |
|---|---|
| `api@internal` | Built-in service behind the dashboard and API |
| `/api/http/routers`, `/api/http/services`, `/api/http/middlewares`, `/api/tcp/routers`, `/api/entrypoints`, `/api/overview` | Most useful API endpoints |
| `OriginStatus` vs `DownstreamStatus` (JSON) | What the backend returned vs what the client got |

**See it on a real system**

```bash
docker logs --tail 100 -f dokploy-traefik
docker logs dokploy-traefik 2>&1 | grep -E ' (ERR|WRN) ' | tail -20
# API without publishing 8080: run curl inside Traefik's network namespace (works when api.insecure is on)
docker run --rm --net container:dokploy-traefik curlimages/curl -s http://127.0.0.1:8080/api/overview
# Private dashboard over SSH instead of an open port (publish 8080 only on 127.0.0.1 first)
ssh -L 8080:127.0.0.1:8080 USER@HOST       # then browse http://localhost:8080/dashboard/
# Access-log triage: 5xx by router and backend
sudo jq -r 'select(.DownstreamStatus >= 500) | [.RouterName, .ServiceURL, .DownstreamStatus] | @tsv' ACCESS_LOG_FILE | sort | uniq -c | sort -rn
```

**Hands-on lab (test VM only)**

The capstone (section 8) is this topic's lab: each break is diagnosed from the
access log and the API alone, before you look at the config. Also do the Ops
Ladder L3 drill: make Traefik return 502 with a wrong port and find it from
Traefik's logs only.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Dashboard reachable from the internet | 8080 published on `0.0.0.0` (and Docker bypasses UFW) | Publish on 127.0.0.1 and use an SSH tunnel, or secure router |
| No access log lines | `accessLog` not enabled | Enable, restart (static) |
| DEBUG left on, disk filling | Forgot to revert | Back to INFO/ERROR, restart |

**Why it matters for troubleshooting**

With the access log you can name the router and backend for any failing request
in one line; with the API you can see why a router is disabled. Together they
replace guessing about labels.

**Next step**

Section 5: Dokploy, which writes most of this Traefik config for you, and where it keeps it.

---

## 5. Dokploy in depth

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm section: *Swarm Services* → *Docker Overlay Network* → *Swarm Service Discovery* → *Docker Stack* ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course), [overlay network notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)), because Dokploy is Swarm underneath · 2) Docs: [Dokploy docs](https://docs.dokploy.com/docs/core) and [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) (KodeKloud has no Dokploy content) · 3) Note: the Swarm area of [Learn: Docker](30-learn-docker.md), then section 7 of the [containers playbook](26-playbook-containers-k8s.md) · 4) Video: none recommended for Dokploy, use the docs · 5) Practice: labs 5.1–5.8 on snapshot C.

Facts in this section were checked against the [Dokploy documentation](https://docs.dokploy.com/)
(installation, manual installation, domains, Docker Compose domains, build
types, backups, and the [troubleshooting pages](https://docs.dokploy.com/docs/core/troubleshooting)).
Dokploy moves fast: confirm paths and names on your version with the
read-only commands given, and read the release notes before every update.

### 5.1 Architecture: Swarm, dokploy-network and core services

**Level:** [L3 · Senior]

**Concept**

Dokploy is a control panel that drives Docker on your server. The installer
needs ports **80, 443 and 3000 free**, installs Docker if missing, initialises
**Docker Swarm** on the server's IP, creates an attachable overlay network
called **dokploy-network**, and starts:

| Component | Runs as | Ports | Role |
|---|---|---|---|
| `dokploy` | Swarm service (`dokploy/dokploy` image) | 3000 (host-mode publish) | Web UI and API; mounts the Docker socket and `/etc/dokploy` |
| `dokploy-postgres` | Swarm service (`postgres:16`), volume `dokploy-postgres` | internal 5432 | Dokploy's own state: projects, domains, env vars |
| `dokploy-traefik` | Standalone container on current installs (some installs: Swarm service) | 80/tcp, 443/tcp, 443/udp (8080 if the dashboard is enabled) | The reverse proxy for everything |
| `dokploy-redis` | Swarm service | internal | Older versions only: the current `install.sh` no longer creates it. An upgraded server may still list it in `docker service ls`; check the release notes before removing it |

```
                         Ubuntu host  (Swarm manager, advertise address 192.0.2.10)
 :80 :443/tcp :443/udp  ┌─────────────────┐  reads labels via /var/run/docker.sock
 ──────────────────────►│ dokploy-traefik │  reads /etc/dokploy/traefik/traefik.yml + dynamic/
                        └────────┬────────┘
                                 │  overlay network: dokploy-network (attachable)
       ┌───────────────┬─────────┴──────────┬──────────────────────┬──────────────────────┐
       ▼               ▼                    ▼                      ▼                      ▼
   dokploy :3000   dokploy-postgres    Application            Compose project        Database
   (UI / API)      (volume)            = Swarm service        = docker compose       services
   host-mode                           crm-x7k2p9             containers APPNAME-*   (optional)
   publish 3000
```

Two consequences people miss:

- Port 3000 and anything you publish are published by Docker, so **UFW rules do
  not protect them** (Ops Ladder blind spot). Once the UI has its own domain
  through Traefik, restrict 3000 in the `DOCKER-USER` chain or at the network
  edge, or reach it through an SSH tunnel.
- Applications are reached by **service name** on dokploy-network
  (`http://crm-x7k2p9:8069`). Swarm resolves that to a virtual IP that depends
  on the kernel's IPVS modules; minimal kernels and some LXC containers lack
  them, which breaks service-to-service traffic (fix: DNS round-robin endpoint
  mode, see 5.8).

**Key terms**

| Term | Meaning |
|---|---|
| Swarm manager | The node that schedules services; Dokploy's server is one |
| Service / task | Swarm's "desired state" object / one running container of it |
| Overlay network | Multi-host Docker network; `attachable` lets plain containers join |
| appName | Dokploy's internal name for an app, e.g. `crm-x7k2p9`; used for service, files and router names |

**See it on a real system**

```bash
docker info --format 'swarm={{.Swarm.LocalNodeState}} manager={{.Swarm.ControlAvailable}}'
docker node ls
docker service ls
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker network inspect dokploy-network --format '{{.Driver}} {{.Scope}} attachable={{.Attachable}}'
sudo ss -ltnup '( sport = :80 or sport = :443 or sport = :3000 )'
```

```
swarm=active manager=true
ID             NAME               MODE         REPLICAS   IMAGE                    PORTS
k3j2h1g0f9e8   dokploy            replicated   1/1        dokploy/dokploy:latest   *:3000->3000/tcp
a1b2c3d4e5f6   dokploy-postgres   replicated   1/1        postgres:16
q9w8e7r6t5y4   crm-x7k2p9         replicated   1/1        crm-x7k2p9:latest
overlay swarm attachable=true
```

→ Dokploy core is healthy (1/1), one Application (`crm-x7k2p9`) runs as a Swarm
service. Traefik does not appear here because it is a plain container on this
install; `docker ps` shows it.

**Hands-on lab (test VM only)**

**Step 1.** On snapshot A (Apache on 80/443), download and **read** the installer
before running it, then run it:

```bash
curl -sSL https://dokploy.com/install.sh -o dokploy-install.sh
less dokploy-install.sh                 # read what it will do: docker, swarm init, network, services
sudo sh dokploy-install.sh
```

→ It stops at its port check with an error that something is already running on
port 80 (or 443): exactly your client incident.

**Step 2.** On a **fresh** VM (snapshot C: no Apache), run it again; it completes and
prints the UI address `http://IP:3000`. If Swarm cannot pick an address
(`must specify a listening address because the address to advertise is not recognized as a system address`),
pass it inline: `sudo ADVERTISE_ADDR=192.168.56.10 sh dokploy-install.sh`.

**Step 3.** Run the "See it" commands and draw the diagram above for your own VM,
with real names and IPs.

**How it breaks**

| Symptom / error text | Cause | First command |
|---|---|---|
| Installer: something is already running on port 80/443/3000 | Apache, nginx or another stack holds the port | `sudo ss -ltnp`, then section 7 / [case study 21](21-case-apache-443-dokploy.md) |
| `must specify a listening address ...` | Several IPs, Swarm cannot choose | `ADVERTISE_ADDR=IP` inline with `sudo` |
| UI down after reboot, log `getaddrinfo ENOTFOUND dokploy-postgres` | Dokploy started before Postgres was ready | `docker service scale dokploy=0 && docker service scale dokploy=1` |
| Apps cannot reach each other by name | IPVS missing for Swarm VIPs | Topic 5.8 |

**Why it matters for troubleshooting**

Dokploy is "just" Docker Swarm + Traefik + Postgres. When the UI is down or
lies, the `docker` CLI still tells the truth.

**Next step**

Topic 5.2: where Dokploy writes things on disk.

### 5.2 Where Dokploy keeps things on disk

**Level:** [L3 · Senior]

**Concept**

Almost everything lives under `/etc/dokploy` (bind-mounted into the `dokploy`
service), plus Docker volumes:

```
/etc/dokploy/
├── traefik/
│   ├── traefik.yml              Traefik STATIC config (entryPoints, providers, letsencrypt resolver)
│   └── dynamic/                 Traefik file provider, hot-reloaded
│       ├── dokploy.yml          router for the Dokploy UI domain (if you set one)
│       ├── middlewares.yml      shared middlewares, e.g. redirect-to-https
│       ├── APPNAME.yml          one file per Application with a domain
│       └── acme.json            Let's Encrypt account + certificates (mode 600, BACK IT UP)
├── applications/APPNAME/code    source cloned for Applications
├── compose/APPNAME/code         source cloned for Compose apps (re-cloned on each deploy)
├── compose/APPNAME/files        File Mounts: persistent, referenced as ../files/ in compose
└── logs/APPNAME/                deployment (build) logs
Docker volumes: dokploy-postgres (Dokploy's DB), dokploy (registry logins, /root/.docker)
```

The `code` directory is wiped and re-cloned on each deployment. Bind-mounting
files from the repository (`./config/app.conf`) works once and then breaks.
Persistent files belong in **File Mounts**, which land in `files/`.

**Key terms**

| Term | Meaning |
|---|---|
| File provider dir | `/etc/dokploy/traefik/dynamic`, same path inside Traefik |
| File Mount | A file whose content you manage in the UI; stored under `files/` |
| Web Server backup | Dokploy's own backup of its Postgres + `/etc/dokploy` |

**See it on a real system**

```bash
sudo ls -la /etc/dokploy /etc/dokploy/traefik /etc/dokploy/traefik/dynamic
sudo ls /etc/dokploy/applications /etc/dokploy/compose 2>/dev/null
sudo ls -t /etc/dokploy/logs/APPNAME/ 2>/dev/null | head -3        # newest deployment logs
docker volume ls --filter name=dokploy
sudo du -sh /etc/dokploy/* 2>/dev/null | sort -h
```

**Hands-on lab (test VM only)**

On the Dokploy VM, create an Application from the `traefik/whoami` Docker image
with a domain `whoami.example.com`, port 80, HTTPS off. Then find, without the
UI: its Swarm service, its dynamic file in `dynamic/`, its router in the
Traefik API, and its deployment log. Write the four commands down.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Compose app loses config files after the 2nd deploy | Bind mounts into `code/`, which is re-cloned | File Mounts + `../files/...` |
| Swarm service never starts, deploy said "done" | Invalid bind mount path | `docker service ps --no-trunc APPNAME` |
| All certificates re-issued after restore | `acme.json` not in the backup or wrong mode | Back it up; `chmod 600` |
| Someone hand-edited `APPNAME.yml`, change vanished | Dokploy rewrites its own files when the app's domains change | Put custom routes in your own file (e.g. `legacy-apache.yml`) |

**Why it matters for troubleshooting**

With the tree above you can debug Dokploy over SSH alone, which is what you
will do when the UI is the thing that is down.

**Next step**

Topic 5.3: the two deployment types, which route traffic differently.

### 5.3 Applications vs Docker Compose

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

| | Application | Docker Compose |
|---|---|---|
| What | One service | A multi-service compose file (or a Swarm stack) |
| Built by | Dokploy (Nixpacks, Railpack, Dockerfile, Buildpacks, Static) or a ready image | Your compose file (images or `build:`) |
| Runs as | Swarm service named after appName | `docker compose` project (or `docker stack` when the type is Stack) |
| Domains become | A **file** in `traefik/dynamic/` | **Labels** injected into the compose file at deploy time |
| Domain change applies | Immediately (hot reload) | **Only after a redeploy** |
| Network | Attached to dokploy-network automatically | Services must be on dokploy-network, or use **Isolated Deployments** |
| Ports | Domain port = container port; Advanced → Ports only for raw IP:port access | Use `expose`, not host `ports: - "3000:3000"` |

A Compose service written the way Dokploy expects (labels shown for when you
manage them yourself instead of using the Domains tab; adjust names to your
`traefik.yml` and `middlewares.yml`):

```yaml
services:
  web:
    image: harbor.example.com/legacy/crm:1.4.2
    restart: unless-stopped
    expose:
      - "80"
    volumes:
      - ../files/crm-uploads:/var/www/html/uploads
    networks:
      - dokploy-network
    labels:
      - traefik.enable=true
      - traefik.docker.network=dokploy-network
      - traefik.http.routers.crm-web.rule=Host(`crm.example.com`)
      - traefik.http.routers.crm-web.entrypoints=web
      - traefik.http.routers.crm-web.middlewares=redirect-to-https@file
      - traefik.http.routers.crm-web.service=crm
      - traefik.http.routers.crm-websecure.rule=Host(`crm.example.com`)
      - traefik.http.routers.crm-websecure.entrypoints=websecure
      - traefik.http.routers.crm-websecure.tls.certresolver=letsencrypt
      - traefik.http.routers.crm-websecure.service=crm
      - traefik.http.services.crm.loadbalancer.server.port=80
networks:
  dokploy-network:
    external: true
```

Also avoid `container_name` in Dokploy compose files: fixed names clash with
redeploys and with how Dokploy finds containers for logs and monitoring.

**Key terms**

| Term | Meaning |
|---|---|
| Preview Compose | UI button showing the final compose file with injected labels |
| Isolated Deployment | Dokploy creates a network per compose app and connects Traefik to it |
| Stack | Compose type deployed with `docker stack deploy` (Swarm semantics, `deploy.labels`) |

**See it on a real system**

```bash
docker compose ls                                           # compose projects (names = appName)
docker ps --filter label=com.docker.compose.project=APPNAME --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker inspect --format '{{json .Config.Labels}}' APPNAME-web-1 | jq 'with_entries(select(.key|startswith("traefik")))'
```

**Hands-on lab (test VM only)**

**Step 1.** Deploy whoami as a **Compose** app with a domain from the Domains tab;
use Preview Compose to read the labels Dokploy injects.

**Step 2.** Change the domain in the UI **without** redeploying and request the
new name: 404. Redeploy: works. Compare with the Application from 5.2, which
changes instantly.

**Step 3.** Replace `expose` with `ports: - "8085:80"` and redeploy. From another
machine, `curl http://192.168.56.10:8085/` works even with `ufw deny 8085`:
the published port bypassed UFW. Revert to `expose`.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Compose domain 404 after a change | Not redeployed; labels are read at deploy | Redeploy |
| 502 for a compose service | Domain port ≠ port the app listens on, or app on 127.0.0.1 | Fix port; bind 0.0.0.0 (Vite: `server.host: true`) |
| Domain never works, health "starting" forever | Failing healthcheck keeps the container out of rotation | Fix or remove the healthcheck |
| Service reachable on a raw port from outside | Host `ports:` publishing | Use `expose` |

**Why it matters for troubleshooting**

"Which type is this app?" is the first question for any Dokploy routing issue,
because it tells you whether to look at a file or at labels, and whether a
redeploy is needed.

**Next step**

Topic 5.4: the exact path from "domain typed in the UI" to "Traefik router".

### 5.4 How a domain becomes a Traefik router

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

```
UI: Domains tab  host=crm.example.com  path=/  container port=8069  HTTPS=on  cert=Let's Encrypt
        │
        ├── Application ─► Dokploy writes /etc/dokploy/traefik/dynamic/crm-x7k2p9.yml
        │                  file provider hot-reloads → routers live in seconds
        │
        └── Compose ────► Dokploy adds traefik.* labels to the service at the NEXT deploy
                          docker provider reads them from the new containers

Either way Traefik ends up with:
  router on web        Host(`crm.example.com`) → middleware redirect-to-https
  router on websecure  Host(`crm.example.com`) → tls.certResolver=letsencrypt → service
  service              http://crm-x7k2p9:8069   (Swarm service name on dokploy-network)
```

An Application's dynamic file typically looks like this (names vary by version;
read yours):

```yaml
http:
  routers:
    crm-x7k2p9-router-1:
      rule: Host(`crm.example.com`)
      service: crm-x7k2p9-service-1
      middlewares:
        - redirect-to-https
      entryPoints:
        - web
    crm-x7k2p9-router-websecure-1:
      rule: Host(`crm.example.com`)
      service: crm-x7k2p9-service-1
      middlewares: []
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
  services:
    crm-x7k2p9-service-1:
      loadBalancer:
        servers:
          - url: http://crm-x7k2p9:8069
        passHostHeader: true
```

Two details from the Dokploy docs that explain most first-day failures:

- **Point DNS at the server before adding the domain.** Otherwise the first ACME
  attempt fails, you get `TRAEFIK DEFAULT CERT`, and you may need to re-save the
  domain or restart Traefik after fixing DNS.
- The domain's **container port** is internal: Traefik connects to it on
  dokploy-network. It does not publish anything to the internet.

**Key terms**

| Term | Meaning |
|---|---|
| Path / Internal Path / Strip Path | Domain options that become `PathPrefix` and prefix middlewares |
| traefik.me | Free wildcard-DNS names Dokploy can generate for testing (HTTP by default) |
| `redirect-to-https` | Middleware from `middlewares.yml` used by the web router |

**See it on a real system**

```bash
sudo grep -l 'crm.example.com' /etc/dokploy/traefik/dynamic/*.yml        # Application? which file?
docker ps -q | xargs -r docker inspect --format '{{.Name}} {{json .Config.Labels}}' | grep -o '^/[^ ]*.*crm\.example\.com' | cut -d' ' -f1   # Compose? which container
docker run --rm --net container:dokploy-traefik curlimages/curl -s http://127.0.0.1:8080/api/http/routers \
  | jq -r '.[] | select(.rule | test("crm.example.com")) | [.name, .status, .service] | @tsv'
curl -sv --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/ -o /dev/null 2>&1 | grep -E 'subject:|issuer:|< HTTP'
```

(The `docker run ... curlimages/curl` line works when the API is enabled, which
is the case with `api.insecure: true` in `traefik.yml`.)

**Hands-on lab (test VM only)**

With the whoami Application from 5.2: change its domain port from 80 to 8080 in
the UI and request it: **502** (whoami listens on 80). Read the new port in its
dynamic file, then fix it. Then delete its DNS entry from your laptop's
`/etc/hosts` and request it by IP over HTTPS: `TRAEFIK DEFAULT CERT`, because
there is no SNI.

**How it breaks**

| Symptom | Layer | First check |
|---|---|---|
| `404 page not found` (Traefik's plain text) | No router: typo, Compose not redeployed, wrong entryPoint | Routers API, `curl -v` Host |
| `502 Bad Gateway` | Router fine, backend refused: port or bind address | Dynamic file / labels port vs `ss -ltn` inside the container |
| `504 Gateway Timeout` after 30 s | Backend unreachable: wrong network, firewall | `traefik.docker.network`; for host backends, UFW rule |
| `TRAEFIK DEFAULT CERT` | ACME failed (DNS, port 80, Cloudflare proxy) | Traefik logs `acme` |
| Works by IP:port, not by domain | You used Advanced → Ports instead of a domain | Remove the port mapping, add a domain |

**Why it matters for troubleshooting**

The three answers (404, 502, certificate) map to three different layers: router,
service and resolver. Name the layer from the symptom first, then open only that
file. The [Dokploy domains troubleshooting page](https://docs.dokploy.com/docs/core/troubleshooting/domains)
lists the same cases.

**Next step**

Topic 5.5: how Dokploy builds and starts your code, and where CI and Harbor fit.

### 5.5 Build types, environment variables and deployments

**Level:** [L3 · Senior]

**Concept**

Sources: GitHub, GitLab, Bitbucket, Gitea, any Git URL, a Docker image, or an
uploaded archive. For Applications, the build types are:

| Build type | What it does | Use it for |
|---|---|---|
| Nixpacks (default) | Detects the language and builds an image; tune with `NIXPACKS_*` env vars | Quick prototypes |
| Railpack | Successor of Nixpacks; `RAILPACK_*` env vars, pin a version | Node, Python, Go, PHP, static |
| Dockerfile | Your Dockerfile, context and target stage; build args and secrets | Production: you control the image |
| Buildpack | Heroku or Paketo buildpacks | Teams already using buildpacks |
| Static | Serves files with an nginx image on **port 80** | Static sites |

Your target pipeline does **not** build on the Dokploy server at all:

```
git push ─► GitLab CI: docker build, tag with $CI_COMMIT_SHORT_SHA ─► push to Harbor (private CA)
                                                                        │
Dokploy Application, source = Docker image harbor.example.com/team/crm:SHA ◄─┘
   trigger: Dokploy deploy webhook / API call from the last CI job
   rollback: deploy the previous SHA tag
```

Requirements for that: Harbor credentials in Dokploy's registry settings, and
Docker on the Dokploy host trusting Harbor's private CA (file
`/etc/docker/certs.d/harbor.example.com/ca.crt`), or pulls fail with
`x509: certificate signed by unknown authority`. Building on the server works
too, but builds compete with production for CPU, RAM and disk; Dokploy supports
separate build servers for that reason.

Environment variables are set per app in the Environment tab (multi-line values
in double quotes). Runtime variables need a **redeploy** to reach the
container; Dockerfile `ARG`s are separate build-time arguments.

**Key terms**

| Term | Meaning |
|---|---|
| Deployment | One build + start; the UI keeps the recent ones with logs |
| Auto deploy / webhook | Deploy on push or on an HTTP call |
| Immutable tag | `crm:3f2a9c1` (commit SHA) instead of `latest`, so rollback is exact |

**See it on a real system**

```bash
docker service inspect crm-x7k2p9 --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
docker service inspect crm-x7k2p9 --format '{{json .Spec.TaskTemplate.ContainerSpec.Env}}' | jq   # contains secrets: do not paste
sudo ls /etc/docker/certs.d/ 2>/dev/null
docker system df                                   # build cache and images growing?
```

**Hands-on lab (test VM only)**

Deploy a tiny app (any repo with a Dockerfile listening on 8000) with the
Dockerfile build type. Break it: set the domain port to 3000 → 502; set an
env var the app needs and do **not** redeploy → old value still in
`docker service inspect`. Redeploy, check again. Then deploy the same app from a
pre-built image tag instead of building.

**How it breaks**

| Symptom / error text | Cause | Fix |
|---|---|---|
| Build log: `Could not resolve host` | Docker's DNS cannot reach upstream (on-prem firewalls block 8.8.8.8) | `"dns": [your internal resolvers]` in `/etc/docker/daemon.json`, restart Docker |
| `x509: certificate signed by unknown authority` pulling from Harbor | Private CA not trusted by Docker | `/etc/docker/certs.d/HARBOR/ca.crt` |
| Server freezes during builds | Builds on a small production box | Build in CI or on a build server |
| New env value not visible | No redeploy | Redeploy |
| Disk full | Build cache and old images | Topic 5.7 cleanup |

**Why it matters for troubleshooting**

When a deploy fails, the deployment log tells you whether it was the build, the
pull or the start. Each has different fixes, and only the start phase involves
Traefik at all.

**Next step**

Topic 5.6: the same logs and metrics from the command line.

### 5.6 Logs, monitoring and the Traefik files

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

The UI shows container logs (Logs tab), build logs (Deployments tab) and
CPU/memory/disk/network graphs (Monitoring). Every one of those has a CLI
equivalent that keeps working when the UI does not:

| You want | Command |
|---|---|
| Is the Application running, and why did tasks fail? | `docker service ps --no-trunc APPNAME` |
| Application stdout/stderr | `docker service logs --tail 100 -f APPNAME` |
| Compose app containers and logs | `docker compose -p APPNAME ps`, `docker logs --tail 100 -f APPNAME-web-1` |
| Build / deploy log | newest file in `/etc/dokploy/logs/APPNAME/` |
| Traefik errors, ACME | `docker logs --tail 200 dokploy-traefik` |
| Dokploy UI/API itself | `docker service logs --tail 100 dokploy` |
| Dokploy database | `docker service logs --tail 50 dokploy-postgres` |
| Live resource use | `docker stats --no-stream` |
| Routers as Traefik sees them | Traefik API (topic 4.9) |

**Key terms**

| Term | Meaning |
|---|---|
| Task error column | Why Swarm could not start a task (`docker service ps --no-trunc`) |
| Worker node logs | Apps scheduled on another node: the UI cannot show their logs (by design) |

**See it on a real system**

```bash
docker service ps --no-trunc crm-x7k2p9 | head -5
```

```
ID       NAME            IMAGE               NODE   DESIRED STATE  CURRENT STATE          ERROR
x1y2z3   crm-x7k2p9.1    crm-x7k2p9:latest   lab1   Running        Running 2 minutes ago
a9b8c7    \_ crm-x7k2p9.1 crm-x7k2p9:latest  lab1   Shutdown       Rejected 3 minutes ago "invalid mount config for type "bind": bind source path does not exist: /folder"
```

→ The first attempt was rejected because of a bad mount, the current one runs.
The UI may only have said "deployment done".

**Hands-on lab (test VM only)**

Break the whoami Application with an invalid bind mount (Advanced → Volumes,
host path `/does-not-exist`), deploy, and find the reason using only
`docker service ps --no-trunc`. Remove the mount, redeploy.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| Logs tab empty | App on a worker node, or slow/full remote server | `docker service ps` (NODE column) |
| Deploy "succeeded" but site 502/503 | Task rejected or crash-looping | `docker service ps --no-trunc APPNAME` |
| Traefik silent about a broken site | Log level ERROR hides details | Temporarily DEBUG, or enable the access log |

**Why it matters for troubleshooting**

Dokploy's UI summarises; Docker's CLI explains. Learn the CLI column of the table
above by heart.

**Next step**

Topic 5.7: protecting the platform itself: backups, updates and recovery.

### 5.7 Backups, updates and recovery

**Level:** [L3 · Senior] → [L4 · Lead/SRE]

**Concept**

Backups (all need an S3-compatible destination configured first):

- **Web Server backup**: Dokploy's own Postgres (`dokploy-postgres`) plus the
  `/etc/dokploy` directory, zipped into one file, optionally on a cron schedule.
  Restore replaces `/etc/dokploy` and the database; if the server's IP changed,
  fix DNS afterwards.
- **Database backups** for databases you run in Dokploy, and **volume backups**
  for app data.
- Your own copy of `acme.json` and of any hand-written dynamic files.

Updates: from the UI, or with the installer's update mode:

```bash
curl -sSL https://dokploy.com/install.sh -o dokploy-install.sh && less dokploy-install.sh
sudo sh dokploy-install.sh update
```

Before every update: take a Web Server backup, read the release notes (Traefik
version and config changes arrive with Dokploy updates), and do it in a quiet
window: Traefik may be recreated, which interrupts every site for a moment.
"Closed network" errors in the logs while Traefik restarts are normal.

Recovery commands from the Dokploy instance troubleshooting page:

```bash
docker ps                                                   # are dokploy, postgres and traefik up?
docker service logs dokploy | tail -50
docker service scale dokploy=0 && docker service scale dokploy=1   # Postgres started after Dokploy
docker restart dokploy-traefik                              # after fixing a broken dynamic YAML file
```

A typical self-inflicted outage: a hand-edited dynamic file with
`passHostHeader` inside the `servers` list. It belongs at the `loadBalancer`
level:

```yaml
# wrong: passHostHeader as a list item
servers:
  - url: http://dokploy:3000
  - passHostHeader: true
# right
servers:
  - url: http://dokploy:3000
passHostHeader: true
```

Disk cleanup, safest first:

```bash
docker system df                                    # what is using space
docker builder prune --filter until=168h            # build cache older than 7 days
docker image prune --filter until=168h              # dangling images older than 7 days
```

> ⚠️ `docker system prune -a` (sometimes suggested for Dokploy) deletes **every**
> image not used by a running container, including the previous release you
> would roll back to, and all stopped containers. Adding `--volumes` also deletes
> unused anonymous volumes (Docker 23 and later; older engines deleted every
> unused volume), which can be **data**. Use the filtered commands above first;
> if you must go further, list what would go (`docker image ls`,
> `docker volume ls -f dangling=true`) and keep rollback tags.

**Key terms**

| Term | Meaning |
|---|---|
| S3 destination | Where Dokploy writes backups (AWS S3, MinIO, others) |
| Canary channel | Pre-release Dokploy builds; not for client servers |

**See it on a real system**

```bash
docker service inspect dokploy --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
docker inspect dokploy-traefik --format '{{.Config.Image}}'
sudo ls -l /etc/dokploy/traefik/dynamic/acme.json
```

**Hands-on lab (test VM only)**

Configure a MinIO container as an S3 destination on the lab VM, take a Web Server
backup, break Dokploy (`docker service rm dokploy` on the **test VM only**),
recreate it using the manual-installation commands from the Dokploy docs, and
restore. Time it: that is your real recovery time.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| All sites briefly down during update | Traefik recreated | Schedule updates; tell users |
| UI loads, data gone after restore | Restored `/etc/dokploy` without the database, or the reverse | Restore both from the same backup |
| Disk full, deploys fail | Images and build cache | Filtered prune; build in CI |

**Why it matters for troubleshooting**

A platform you cannot restore is a single point of failure for every client app
on it. Practise the restore once on a VM before the migration.

**Next step**

Topic 5.8: the checklist of Dokploy failures you will actually meet.

### 5.8 Dokploy pitfalls checklist

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

Collected from the Dokploy troubleshooting pages, the Ops Ladder blind spots and
real migrations. Read it before your first production deploy and again during
any incident.

**Key terms**

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Installer fails: port 80/443/3000 in use | Apache/nginx/another service | Section 7; [case study 21](21-case-apache-443-dokploy.md) |
| 2 | Swarm init: "address to advertise is not recognized" | Multiple IPs | `sudo ADVERTISE_ADDR=IP sh dokploy-install.sh` |
| 3 | Compose domain 404 after editing | No redeploy | Redeploy |
| 4 | 502 Bad Gateway | Domain port wrong, or app listens on 127.0.0.1 | Fix port; listen on 0.0.0.0 |
| 5 | No certificate (`TRAEFIK DEFAULT CERT`) | Domain added before DNS pointed; port 80 blocked; CDN proxy | Fix DNS/port 80, re-save domain or restart Traefik; DNS-01 for on-prem |
| 6 | Builds: `Could not resolve host` | Docker DNS fallback to blocked public resolvers | `"dns"` in `/etc/docker/daemon.json` with internal resolvers |
| 7 | `all predefined address pools have been fully subnetted` | Too many networks | `docker network prune` (removes unused networks only), then `default-address-pools` in `daemon.json` |
| 8 | Services cannot reach each other by name (LXC, minimal kernels) | IPVS modules missing for Swarm VIPs | `ENDPOINT_MODE=dnsrr` on install, or `docker service update --endpoint-mode dnsrr SERVICE`; `tasks.APPNAME:PORT` for apps |
| 9 | Compose config files empty after 2nd deploy | Bind-mounting repo files that get re-cloned | File Mounts + `../files/` |
| 10 | Deploy "done", app not running | Invalid mount or failing healthcheck | `docker service ps --no-trunc` |
| 11 | Raw port reachable despite UFW | Host `ports:` / Advanced → Ports publish around UFW | `expose` + domains; `DOCKER-USER` rules |
| 12 | UI down after reboot | Postgres race | `docker service scale dokploy=0` then `=1` |
| 13 | Everything down after editing a dynamic file | YAML error (e.g. `passHostHeader` placement) | Fix, `docker restart dokploy-traefik` |
| 14 | Apache back on 443 after reboot, Traefik failing | Apache only stopped, not disabled | `systemctl disable --now apache2` (+ `mask`) |
| 15 | Logs/monitoring empty for some apps | App runs on a worker node | Expected; use `docker service logs` |
| 16 | Disk full | Images, build cache, container logs | Filtered prune; log rotation in `daemon.json` |

**See it on a real system**

A two-minute Dokploy health check you can paste into an incident ticket:

```bash
docker service ls; docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | head -20
docker logs --since 15m dokploy-traefik 2>&1 | grep -E ' (ERR|WRN) ' | tail -10
sudo ss -ltnup '( sport = :80 or sport = :443 or sport = :3000 )'
systemctl is-enabled apache2 nginx 2>/dev/null
df -h /var/lib/docker; docker system df
```

**Hands-on lab (test VM only)**

Pick four rows (4, 5, 9, 14), reproduce each on the Dokploy VM, and record:
symptom, the first command that proved the cause, and the fix. Add the notes to
your runbook repo.

**How it breaks**

This topic *is* the "how it breaks" list for Dokploy. For the incident flow
around it, use the [containers and Kubernetes playbook](26-playbook-containers-k8s.md).

**Why it matters for troubleshooting**

Most Dokploy incidents are one of these sixteen rows. Matching the symptom to a
row first saves you from debugging Traefik internals when the answer is "redeploy".

**Next step**

Section 6: HAProxy briefly, and how to choose between the proxies you now know.

---

## 6. HAProxy, choosing a proxy, Kubernetes ingress

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Implement Reverse Proxies and Load Balancers* ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking → *Ingress* and the Gateway API lessons ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator), [Ingress notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page)) · 3) Note: section 8 of [Learn: Kubernetes](31-learn-kubernetes.md) · 4) HAProxy: no KodeKloud course and no verified video; read the configuration manual for the version `haproxy -v` reports · 5) Practice: labs 6.1–6.3.

You now know four proxies. This section adds the one you will meet in front of
load-balanced farms, databases and Kubernetes control planes (HAProxy), puts all
of them side by side so you can choose on purpose, and maps everything onto
Kubernetes, where the same ideas are called Ingress and Gateway API.

### 6.1 HAProxy in brief

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

HAProxy is a dedicated load balancer and proxy. It serves no files, runs no
PHP, and on the versions Ubuntu ships it does not fetch certificates itself
(certbot or files do that). What it does better than the others is balancing:
precise health checks, queueing, stickiness, connection limits, and logs that
tell you in four characters which side ended a session and why. That is why it
sits in front of web farms, database replicas, and the API servers of an HA
kubeadm cluster (often with keepalived holding a floating IP).

Two modes: `mode http` (layer 7: reads Host, path, headers, can add
`X-Forwarded-For`) and `mode tcp` (layer 4: forwards bytes, can still read the
TLS SNI for routing).

The config file `/etc/haproxy/haproxy.cfg` has five kinds of sections:

| Section | Role | Apache / Traefik equivalent |
|---|---|---|
| `global` | Process-wide: logging target, stats socket, user, limits | `apache2.conf` globals / Traefik static config |
| `defaults` | Defaults for every following proxy: mode, timeouts, log format | Global `Timeout`, `LogFormat` |
| `frontend` | The listening side: `bind`, ACLs, which backend to use | `Listen` + vhost matching / entryPoint + router |
| `backend` | A pool of servers, balancing algorithm, health checks | `ProxyPass` target or balancer / Traefik service |
| `listen` | Frontend and backend in one block (stats page, simple TCP) | n/a |

```
frontend fe_http  (bind :80)
   acl host_crm  hdr(host) -i crm.example.com   ──► use_backend be_crm   ──► crm1 127.0.0.1:8000  check
                                                                         └─► crm2 127.0.0.1:8001  check
   acl host_shop hdr(host) -i shop.example.com  ──► use_backend be_shop  ──► shop1 127.0.0.1:8069 check
   nothing matched                              ──► default_backend be_default (deny with 404)
```

A realistic HTTP configuration (Ubuntu 24.04 ships HAProxy 2.8, 22.04 ships 2.4;
both understand everything below):

```
global
    log /dev/log local0
    stats socket /run/haproxy/admin.sock mode 660 level admin

defaults
    mode    http
    log     global
    option  httplog
    option  forwardfor
    timeout connect 5s
    timeout client  60s
    timeout server  60s

frontend fe_http
    bind :80
    acl host_crm  hdr(host) -i crm.example.com
    acl host_shop hdr(host) -i shop.example.com
    use_backend be_crm  if host_crm
    use_backend be_shop if host_shop
    default_backend be_default

backend be_crm
    balance roundrobin
    option httpchk
    http-check send meth GET uri /health ver HTTP/1.1 hdr Host crm.example.com
    http-check expect status 200
    server crm1 127.0.0.1:8000 check inter 5s fall 3 rise 2
    server crm2 127.0.0.1:8001 check inter 5s fall 3 rise 2

backend be_shop
    server shop1 127.0.0.1:8069 check

backend be_default
    http-request deny deny_status 404

listen stats
    bind 127.0.0.1:8404
    stats enable
    stats uri /stats
    stats refresh 10s
```

Health checks decide everything: a server that fails `fall` checks in a row is
marked DOWN and receives no traffic until it passes `rise` checks. When every
server of a backend is DOWN, HAProxy answers **503** with its own page
("No server is available to handle this request.").

HAProxy logs through syslog; on Ubuntu the package configures rsyslog to write
`/var/log/haproxy.log`. Every HTTP log line carries a four-character
**termination state**. The first character says who or what ended the session,
the second in which phase:

| State | Meaning | Status the client saw |
|---|---|---|
| `----` | Normal end | Whatever the backend sent |
| `SC--` | Server refused the connection (or no server was available) | 503 |
| `sH--` | `timeout server` expired while waiting for the response headers | 504 |
| `SH--` | Server aborted before sending complete headers (crash, reset) | 502 |
| `cD--` | Client went quiet during the transfer (`timeout client`) | (transfer cut) |
| `CD--` | Client aborted during the transfer | (transfer cut) |
| `PR--` | The proxy refused the request (`http-request deny`) | 403 or the deny status |

**Key terms**

| Term | Meaning |
|---|---|
| ACL | A named condition (`hdr(host) -i NAME`, `path_beg /api`) used by `use_backend`, `http-request` rules |
| `check`, `inter`, `fall`, `rise` | Active health check on a server: interval, failures to mark DOWN, successes to mark UP |
| `balance` | `roundrobin` (default), `leastconn` (long requests), `source` (crude stickiness) |
| Stats socket / runtime API | `/run/haproxy/admin.sock`: show and change server state without a reload |
| Termination state | The four characters in each log line that say who ended the session and in which phase |
| `option forwardfor` | Add `X-Forwarded-For` (off in Ubuntu's default config) |

**See it on a real system**

```bash
haproxy -v | head -1                                   # 2.8.x on Ubuntu 24.04, 2.4.x on 22.04
sudo haproxy -c -f /etc/haproxy/haproxy.cfg            # validate before EVERY reload
sudo grep -nE '^\s*(frontend|backend|listen|bind|acl|use_backend|default_backend|server)\b' /etc/haproxy/haproxy.cfg
# Live state of every frontend, backend and server (field 18 is the status)
echo 'show stat' | sudo socat stdio /run/haproxy/admin.sock | cut -d, -f1,2,18 | column -s, -t
sudo tail -n 2 /var/log/haproxy.log
```

```
HAProxy version 2.8.5-1ubuntu3 2024/04/01
Configuration file is valid
# pxname  svname    status
fe_http   FRONTEND  OPEN
be_crm    crm1      UP
be_crm    crm2      DOWN
be_crm    BACKEND   UP
be_shop   shop1     UP
be_shop   BACKEND   UP
Oct  3 10:12:01 lb1 haproxy[2101]: 198.51.100.7:51234 [03/Oct/2026:10:12:01.123] fe_http be_crm/crm1 0/0/1/45/46 200 1534 - - ---- 3/3/0/0/0 0/0 "GET / HTTP/1.1"
Oct  3 10:12:09 lb1 haproxy[2101]: 198.51.100.7:51240 [03/Oct/2026:10:12:09.871] fe_http be_shop/shop1 0/0/-1/-1/3002 503 217 - - SC-- 1/1/0/0/3 0/0 "GET / HTTP/1.1"
```

- `crm2 DOWN` → it fails its health check; `be_crm` is still UP because crm1 serves alone.
- `0/0/1/45/46` → timers in ms: request, queue, connect, response, total. The backend needed 45 ms.
- `-1/-1` and `SC--` on the shop line → the connection to 127.0.0.1:8069 was refused; the final `3` in `1/1/0/0/3` is the number of retries, and the 3 s total is HAProxy waiting about a second before each retry. That is a dead or misconfigured backend, not a slow one.

**Hands-on lab (test VM only)**

Run HAProxy on port 8089 next to the capstone (Apache on 8080) and the whoami
container from topic 1.5 (`127.0.0.1:18080`).

**Step 1.** Install it and append a lab frontend:

```bash
sudo apt install -y haproxy socat
sudo cp -a /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.orig
sudo tee -a /etc/haproxy/haproxy.cfg >/dev/null <<'EOF'

frontend fe_lab
    bind :8089
    acl host_whoami hdr(host) -i whoami.example.com
    use_backend be_whoami if host_whoami
    default_backend be_apache

backend be_apache
    server apache1 127.0.0.1:8080 check inter 3s fall 2 rise 2

backend be_whoami
    option httpchk
    http-check send meth GET uri /health
    http-check expect status 200
    server whoami1 127.0.0.1:18080 check inter 3s fall 2 rise 2

listen stats
    bind 127.0.0.1:8404
    stats enable
    stats uri /stats
    stats refresh 5s
EOF
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy
curl -s -H 'Host: site-a.example.com' http://127.0.0.1:8089/
curl -s -H 'Host: whoami.example.com' http://127.0.0.1:8089/ | grep -E '^(Host:|X-Forwarded)'
```

→ site-a answers through HAProxy. The whoami output shows `Host:` but **no**
`X-Forwarded-For`: Ubuntu's default config does not set `option forwardfor`.

**Step 2.** Add `option forwardfor` inside `frontend fe_lab`, validate, reload,
and repeat the whoami request: `X-Forwarded-For: 127.0.0.1` appears.

**Step 3.** Break it: `sudo docker stop whoami`. Within two checks (about 6 s):

```bash
curl -si -H 'Host: whoami.example.com' http://127.0.0.1:8089/ | sed -n '1p;/No server/p'
echo 'show stat' | sudo socat stdio /run/haproxy/admin.sock | cut -d, -f1,2,18 | grep whoami
sudo tail -n 1 /var/log/haproxy.log
```

```
HTTP/1.1 503 Service Unavailable
No server is available to handle this request.
be_whoami,whoami1,DOWN
be_whoami,BACKEND,DOWN
... fe_lab be_whoami/<NOSRV> 0/-1/-1/-1/0 503 217 - - SC-- 1/1/0/0/0 0/0 "GET / HTTP/1.1"
```

→ `<NOSRV>` plus `SC--`: no server was even tried, because the only one is
DOWN. Compare with the shop line above, where a server was tried and refused.

**Step 4.** Fix: `sudo docker start whoami`; after two good checks the server is
UP again (watch `http://127.0.0.1:8404/stats` from the VM or through an SSH
tunnel). Clean up: restore `haproxy.cfg.orig` and `sudo systemctl reload haproxy`,
or `sudo systemctl disable --now haproxy`.

**How it breaks**

| Symptom / log text | Cause | First command |
|---|---|---|
| 503 "No server is available to handle this request." | Every server of the backend is DOWN (health check failing) | Stats socket `show stat`, status column |
| Log state `SC--`, status 503 | Backend refused the connection: down, wrong port | `curl -v` to the server address from the HAProxy host |
| Log state `sH--`, status 504 | `timeout server` shorter than the slow request | Fix the endpoint, or raise the timeout on purpose |
| A server flaps UP/DOWN | Health path slow, or the backend needs a Host header in the check | `http-check send ... hdr Host NAME` |
| `crm.example.com:8089` lands on the default backend | `hdr(host)` includes the port | Match with `hdr_beg(host)` or strip the port before matching |
| `reload` changed nothing | The new config was invalid, so the old process kept running | `sudo haproxy -c -f /etc/haproxy/haproxy.cfg`, `journalctl -u haproxy` |

**Why it matters for troubleshooting**

HAProxy answers the "which hop failed?" question (topic 1.1) in its own log
line: the termination state names the side and the phase, and the timers show
where the time went. You will meet it in front of Kubernetes API servers and
database clusters even if you never use it as a web edge.

**Next step**

Topic 6.2: put all five proxies side by side and choose on purpose.

### 6.2 Choosing a proxy

**Level:** [L3 · Senior] → [L4 · Lead/SRE]

**Concept**

Every proxy in this module does the same six jobs: accept the connection,
handle TLS, pick a route by Host or SNI, forward, add headers, log. They differ
in how configuration arrives, what else they can do, and how they fail. One rule
beats every comparison table: **exactly one process owns 80/443 on an IP**
(topic 1.3). Everything else sits behind it on internal ports.

| | Apache httpd | nginx | Traefik v3 | HAProxy | Caddy |
|---|---|---|---|---|---|
| Main strength | Feature-rich web server: `.htaccess`, mod_php, many modules | Fast static files and reverse proxy, small memory footprint | Discovers routes from Docker, Swarm and Kubernetes; ACME built in | Precise L4/L7 balancing, health checks, detailed logs | HTTPS by default with almost no config |
| Config model | Files and vhosts, graceful reload | Files and server blocks, graceful reload | Static file or flags plus dynamic providers, hot reload | One file, seamless reload, runtime API | Caddyfile or JSON API |
| Certificates | Files (certbot) | Files (certbot) | ACME (HTTP-01, TLS-ALPN-01, DNS-01) or files | Files (certbot) | ACME built in |
| Runs PHP | mod_php or php-fpm | php-fpm only | No | No | php-fpm |
| Follows containers that come and go | No | No (reload after changes) | Yes | Partly (DNS resolution, runtime API) | Limited |
| Where you meet it | Inherited LAMP servers (yours) | Everywhere; Dokploy's Static build type | Dokploy, k3s, Docker hosts | Load-balancer tiers, K8s API HA, database fronts | Small teams and homelabs |
| Choose it when | Inherited apps need `.htaccess` or mod_php as they are | You want a well-known edge or a static server on a VM | Containers come and go, or you run Dokploy | You need serious balancing and health logic, or TCP | You want HTTPS with near-zero config |

A decision guide for your environment:

```
Public web edge of a Docker / Dokploy host?               → Traefik (Dokploy's own), everything else behind it
Apps that need .htaccess or mod_php exactly as they are?  → Apache, but BEHIND the edge on an internal port (7.1)
Plain VM, a few static or proxied sites, no containers?   → nginx (or Apache if that is what the team knows) (7.2)
Many identical backends, TCP services, K8s API HA?        → HAProxy (often with keepalived for a floating IP)
Kubernetes cluster?                                       → an Ingress or Gateway controller (6.3), not a host proxy
```

What a senior adds to the choice: who will operate it (team knowledge beats
benchmarks), how config changes (Git review vs a UI), the blast radius (one edge
for every site means one restart touches every site), who owns certificates, and
how you will see failures (access logs with router and backend names). Write the
choice down as an Architecture Decision Record so the next engineer knows why
(see [Senior architecture](39-learn-senior-architecture.md)).

The anti-pattern to avoid is **two edges**: Apache and Traefik both terminating
TLS, both redirecting HTTP to HTTPS, both adding HSTS and security headers. It
produces redirect loops, duplicated headers and a timeout chain nobody can
reason about.

**Key terms**

| Term | Meaning |
|---|---|
| Edge proxy | The one process that owns 80/443 and faces clients |
| Internal hop | Any proxy or server behind the edge, on a private port |
| Blast radius | What breaks when this component restarts or fails |
| ADR | Architecture Decision Record: context, decision, consequences, in one page |

**See it on a real system**

Each proxy has a recognisable fingerprint. Before you open any config, find out
who answered:

```bash
# The Server header (if not hidden) and Via name the hop that answered
curl -sI https://app.example.com/ | grep -iE '^(server|via|x-powered-by)'
# An unknown name and its status code: which default answered?
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: no-such-site.example.com' http://192.0.2.10/
curl -s -H 'Host: no-such-site.example.com' http://192.0.2.10/ | head -5
```

| Body you get back | Who produced it |
|---|---|
| `404 page not found` (plain text) | Traefik: no router matched |
| `Bad Gateway` or `no available server` (plain text) | Traefik: backend refused, or no healthy server |
| HTML ending in `<center>nginx/1.24.0 (Ubuntu)</center>` | nginx |
| HTML ending in `Apache/2.4.58 (Ubuntu) Server at NAME Port N` | Apache (with `ServerSignature On`) |
| `No server is available to handle this request.` | HAProxy: every server DOWN |
| The application's own styled error page | The request reached the application |

**Hands-on lab (test VM only)**

**Step 1.** On the capstone VM you can run up to four proxies at once: Traefik
on 80/443, Apache on 8080, nginx on 8088 (topic 3.1), HAProxy on 8089 (6.1).
Send each one an unknown Host and a request to a stopped backend, and fill in
your own fingerprint table with the status code and the first line of the body.

**Step 2.** Write a one-page ADR: "Traefik (via Dokploy) is our only edge;
Apache and nginx run only behind it." Context (your incident), decision,
consequences (one restart affects all sites; certificates move to Traefik;
Apache keeps `.htaccess` apps until they are containerised), and the rollback.

**How it breaks**

| Symptom | Design cause | Fix |
|---|---|---|
| Redirect loop, or two redirects in a row | Two layers both redirect HTTP to HTTPS | Redirect only at the edge |
| HSTS or security headers duplicated or contradictory | Both layers add them | Set them only at the edge |
| 504 at the edge, nothing in the app log | Outer timeout shorter than the inner one | Topic 1.6: inner shorter than outer |
| Restarting the edge drops every site | One edge for everything, by design | Prefer hot reloads; schedule restarts; HA pair at L4 for critical sites |
| Nobody knows which proxy owns a name | No inventory, no ADR | Inventory (2.12), PORTS.md, ADR |

**Why it matters for troubleshooting**

Seniors get asked "why Traefik and not nginx?" and must answer with trade-offs,
not taste. And the fingerprint table lets you name the hop that answered from a
single `curl`, which is the first move in every proxy incident.

**Next step**

Topic 6.3: the same ideas inside a Kubernetes cluster.

### 6.3 Kubernetes ingress: the same ideas in a cluster

**Level:** [L3 · Senior]

**Concept**

Kubernetes brings nothing new to this module, only new object names. A
**Service** (ClusterIP) is a stable virtual IP in front of pods, like a Traefik
service pool. An **Ingress** is a list of Host and path rules, like routers. The
**ingress controller** is a reverse proxy (Traefik, HAProxy, NGINX-based) running
as pods that watches Ingress objects and configures itself, exactly as Traefik
watches Docker labels on your Dokploy host. The **Gateway API** splits the same
thing by owner: a GatewayClass says which controller, a Gateway holds the
listeners and certificates (the entryPoints), and HTTPRoutes hold the routing
rules (the routers). Section 8 of [Learn: Kubernetes](31-learn-kubernetes.md)
covers both in CKA depth, including the retirement of the community
ingress-nginx controller.

| Concept | Apache | nginx | Traefik (Dokploy) | Kubernetes Ingress | Gateway API |
|---|---|---|---|---|---|
| Listening socket | `Listen 443` | `listen 443 ssl` | entryPoint `websecure` | Controller's Service, NodePort or hostNetwork | Gateway listener |
| One site's routing | `<VirtualHost>` + `ServerName` | `server` + `server_name` | Router `Host()` rule | Ingress rule `host:` | HTTPRoute `hostnames` |
| Path routing | `ProxyPass /api/` | `location /api/` | `PathPrefix` | `path:` + `pathType` | `matches.path` |
| Backend pool | `ProxyPass` URL or balancer | `upstream` | Service `loadBalancer.servers` | Service → EndpointSlices | `backendRefs` |
| Certificate | `SSLCertificateFile` | `ssl_certificate` | `certResolver` or file certificates | `tls.secretName` (often cert-manager) | Listener `certificateRefs` |
| Unknown name | First vhost | `default_server` | `404 page not found` | Controller's default backend (404) | No route: 404 |

An Ingress for the CRM, served by a Traefik controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: crm
  namespace: crm
spec:
  ingressClassName: traefik
  tls:
  - hosts: ["crm.example.com"]
    secretName: crm-tls
  rules:
  - host: crm.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: crm
            port:
              number: 80
```

**Key terms**

| Term | Meaning |
|---|---|
| IngressClass | Which controller handles an Ingress (`ingressClassName`) |
| `pathType` | `Prefix`, `Exact` or `ImplementationSpecific` |
| EndpointSlice | The live list of ready pod IPs and ports behind a Service |
| Default backend | What the controller serves when no rule matches |
| cert-manager | The usual way to get ACME certificates into TLS Secrets |

**See it on a real system**

```bash
kubectl get ingressclass
kubectl get ingress -A
kubectl -n crm describe ingress crm                       # rules, backends with their endpoints, events
kubectl -n crm get endpointslices -l kubernetes.io/service-name=crm
kubectl get svc -A | grep -iE 'traefik|ingress'           # how the controller is exposed (NodePort / LoadBalancer)
```

```
NAME      CONTROLLER                      PARAMETERS   AGE
traefik   traefik.io/ingress-controller   <none>       12d

NAMESPACE   NAME   CLASS     HOSTS             ADDRESS         PORTS     AGE
crm         crm    traefik   crm.example.com   192.168.56.11   80, 443   3d

Rules:
  Host             Path  Backends
  ----             ----  --------
  crm.example.com
                   /   crm:80 (10.244.2.14:8069)

NAME        ADDRESSTYPE   PORTS   ENDPOINTS     AGE
crm-7xk2q   IPv4          8069    10.244.2.14   3d
```

→ The `Backends` line is the Kubernetes version of "which backend does the router
point at": Service port 80 resolves to pod 10.244.2.14 on port 8069. Empty
parentheses there mean the Service selects no ready pod, and the controller
answers 503.

**Hands-on lab (test VM only)**

Use your kubeadm homelab or a KodeKloud / Killercoda Kubernetes playground that
has an ingress controller (`kubectl get ingressclass` must list one; use its
name instead of `traefik` below).

**Step 1.** Build it with imperative commands (exam speed):

```bash
kubectl create deployment whoami --image=traefik/whoami --port=80
kubectl expose deployment whoami --port=80
kubectl create ingress whoami --class=traefik --rule='whoami.example.com/*=whoami:80'
kubectl get svc -A | grep -iE 'traefik|ingress'          # note the controller's NodePort for port 80
curl -s -H 'Host: whoami.example.com' http://NODE_IP:NODEPORT/ | head -3
```

**Step 2.** Break it like capstone break 1 (wrong port):
`kubectl edit ingress whoami` and set the backend port number to 8080. The
controller now has no valid backend for the name: depending on the controller
you get 404 or 503, and `kubectl describe ingress whoami` shows the backend
without endpoints. Fix it back to 80.

**Step 3.** Break it like capstone break 2 (wrong Host): request
`whoami.exmaple.com` and get the controller's default 404. Then break the
Service selector instead:
`kubectl patch svc whoami -p '{"spec":{"selector":{"app":"nope"}}}'`. The
EndpointSlice empties, the controller answers 503, and `describe ingress` shows
the backend with no endpoints. Fix it with the same patch and `"app":"whoami"`.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| 404 from the controller | No rule matches Host/path, wrong `ingressClassName`, Ingress in a different namespace than its Service | `kubectl describe ingress NAME`, `kubectl get ingressclass` |
| 503 | Service has no ready endpoints (selector mismatch, failing readiness probe) | `kubectl get endpointslices -l kubernetes.io/service-name=SVC` |
| 502 | `targetPort` wrong, or the app does not listen on the pod port | `kubectl port-forward pod/POD 8080:PORT`, then `curl localhost:8080` |
| Controller's default certificate | TLS Secret missing, in another namespace, or not issued yet | `kubectl get secret -n NS`, `kubectl describe certificate` (cert-manager) |
| Ingress never gets an ADDRESS | No controller handles that class | `kubectl get ingressclass`, controller pods and logs |

**Why it matters for troubleshooting**

Services and Networking is a fifth of the CKA exam, and its troubleshooting
questions are this module's questions with new nouns: which proxy answered,
which rule matched, which backend it chose, and whether that backend listens.
Everything in sections 1 and 4 transfers unchanged.

**Next step**

Section 7: using all of this to move real sites from Apache to the new edge without an outage.

---

## 7. Migration patterns and cutover

> 📚 **Study path:** 1) Note: [Case study 21](21-case-apache-443-dokploy.md) phases 3–8 and section 1 of [Deployment patterns](35-deployment-patterns.md) (your 81/444 fix and how to finish it) · 2) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil → *Change Management for Reliability* ([course](https://kodekloud.com/courses/fundamentals-of-sre), [lesson notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 3) Read: [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/) for the change-request format · 4) Video: none needed for this area · 5) Practice: replay the migration on your capstone VM or the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), with a timed rollback.

Your server today is half-way through the first pattern below: Apache moved to
81/444 and Dokploy's Traefik owns 80/443
([Deployment patterns](35-deployment-patterns.md) analyses that fix). This
section is the general theory of moving sites between proxies safely; the case
study is the concrete runbook for one server. The port numbers do not matter:
8080 in this module's labs, 8081 in case study 21, 81 on your real server.

```
START                          7.1 APACHE BEHIND TRAEFIK            7.4 ONE SITE AT A TIME          END (7.6)
Apache :80/:443                Traefik :80/:443                     Traefik :80/:443                Traefik :80/:443
 ├─ shop                         └─► Apache :8080 (internal)          ├─► container crm (Dokploy)      ├─► containers
 ├─ crm                              ├─ shop                          └─► Apache :8080                 └─ Apache disabled,
 └─ wiki                             ├─ crm                               ├─ shop                         masked, backed up
                                     └─ wiki  (apps unchanged)            └─ wiki
```

### 7.1 Apache behind Traefik

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

Keep Apache and every application exactly as they are, move Apache's listener to
an internal port, and let Traefik own 80/443 and forward each hostname to
Apache. No application changes, a one-command rollback, and it unlocks moving
sites one at a time later (7.4).

```
client ══TLS══► Traefik :443   (Let's Encrypt via certResolver, or reused certificate files)
                  │ router Host(`shop.example.com`) → service apache-legacy
                  ▼ plain HTTP on a private hop
               Apache 192.0.2.10:8080   name-based vhosts unchanged
                  │ mod_remoteip trusts the Docker subnet; X-Forwarded-Proto https → HTTPS=on
                  ▼
               php-fpm, app backends, docroots as before
```

The pattern is complete only when all seven parts are done. Your 81/444 change
did part 1; parts 2–7 are what makes it safe:

| # | Part | Detail | Topic |
|---|---|---|---|
| 1 | Listener | Apache on an internal port; every `<VirtualHost>` port changed too; bound to an address the Traefik **container** can reach (the host IP, never 127.0.0.1) | 2.3, 1.3 |
| 2 | Firewall | Allow only the Docker bridge to that port; close it from outside | 7.1 lab |
| 3 | Routes | One router per hostname on `web` (redirect) and `websecure` (TLS), one service pointing at Apache, in your own dynamic file | 4.3, 4.4 |
| 4 | Certificates | Let Traefik issue them (port 80 now reaches Traefik), or reuse the existing files for a gap-free cutover; then stop certbot's `apache` renewals | 4.7, 2.6 |
| 5 | Real client IPs | `mod_remoteip` trusting the Docker subnet, `%a` in log formats | 2.8 |
| 6 | HTTPS awareness | Remove Apache-side HTTPS redirects or make them test `X-Forwarded-Proto`; `SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on` for PHP apps | 2.7, 8.5 |
| 7 | Boot order | Apache stays enabled (it is a backend now) but must never listen on 80/443 again; Traefik owns them at boot | 1.3, 2.11 |

The production route file on a Dokploy host (your own file name, so Dokploy
never rewrites it; check the middleware and resolver names in your
`middlewares.yml` and `traefik.yml` first):

```yaml
# /etc/dokploy/traefik/dynamic/legacy-apache.yml
http:
  routers:
    shop-web:
      entryPoints: [web]
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`)"
      middlewares: [redirect-to-https]
      service: apache-legacy
    shop-websecure:
      entryPoints: [websecure]
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`)"
      service: apache-legacy
      tls:
        certResolver: letsencrypt
  services:
    apache-legacy:
      loadBalancer:
        servers:
          - url: "http://192.0.2.10:8080"
        passHostHeader: true
```

Reusing the existing Let's Encrypt files as a **bridge certificate** (useful for
HSTS sites, which must never see Traefik's default certificate): Dokploy's
Traefik only sees `/etc/dokploy/traefik/dynamic`, and the files in
`/etc/letsencrypt/live/` are symlinks into `../../archive/`, which the container
cannot follow. Copy the real files, keep them private, and remember that certbot
will not update the copies:

```bash
sudo install -d -m 700 /etc/dokploy/traefik/dynamic/certs
sudo install -m 600 "$(sudo readlink -f /etc/letsencrypt/live/shop.example.com/fullchain.pem)" /etc/dokploy/traefik/dynamic/certs/shop.example.com.crt
sudo install -m 600 "$(sudo readlink -f /etc/letsencrypt/live/shop.example.com/privkey.pem)"   /etc/dokploy/traefik/dynamic/certs/shop.example.com.key
```

Then list them under `tls.certificates` (topic 4.7) and, once Traefik has issued
its own certificate for the name, delete the copies. Note the expiry date in the
change ticket: a bridge certificate that outlives its plan becomes an outage.

**Key terms**

| Term | Meaning |
|---|---|
| Internal port | Apache's new, non-public listener (8080, 8081, 81) |
| Legacy route file | Your own dynamic file with the Apache routes, separate from Dokploy's files |
| Bridge certificate | Existing certificate files served by Traefik until its own ACME certificates exist |
| `docker_gwbridge` | The bridge a Swarm-attached container (dokploy-traefik) uses to reach the host |

**See it on a real system**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :8080 )'
grep -RnE '^\s*Listen|<VirtualHost' /etc/apache2/ports.conf /etc/apache2/sites-enabled/
sudo ufw status verbose | grep -E '8080|docker_gwbridge'
# Reach Apache exactly the way Traefik does: from Traefik's network namespace
docker run --rm --net container:dokploy-traefik nicolaka/netshoot \
  curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.10:8080/
sudo ls -l /etc/dokploy/traefik/dynamic/
```

```
LISTEN 0      4096         0.0.0.0:80         0.0.0.0:*    users:(("docker-proxy",pid=2311,fd=4))
LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*    users:(("docker-proxy",pid=2330,fd=4))
LISTEN 0      511                *:8080             *:*    users:(("apache2",pid=1301,fd=3),("apache2",pid=1304,fd=3))
/etc/apache2/ports.conf:5:Listen 8080
/etc/apache2/sites-enabled/shop.conf:1:<VirtualHost *:8080>
8080/tcp on docker_gwbridge  ALLOW IN    Anywhere
200
-rw------- 1 root root 1843 Oct  3 08:10 acme.json
-rw-r--r-- 1 root root  412 Oct  3 08:10 dokploy.yml
-rw-r--r-- 1 root root  733 Oct  3 09:40 legacy-apache.yml
-rw-r--r-- 1 root root  208 Oct  3 08:10 middlewares.yml
```

- `docker-proxy` on 80/443 → the published Traefik ports; Apache holds only 8080.
- The UFW rule admits the Docker bridge, nothing else, to 8080.
- `200` from Traefik's own namespace → the private hop works before any router exists.

**Hands-on lab (test VM only)**

The capstone (section 8) is this pattern on one VM. Then harden it the
production way:

**Step 1.** Allow SSH first (`sudo ufw allow OpenSSH`), then `sudo ufw enable`.
Request site-a through Traefik: after about 30 seconds you get **504**, because
packets from the Traefik container to the host's port 8080 now pass UFW's input
rules and are dropped. ("Docker bypasses UFW" is only true for traffic **to**
published container ports.)

**Step 2.** Fix it narrowly: find the capstone network's subnet with
`docker network inspect capstone_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'`
and allow only that: `sudo ufw allow from 172.18.0.0/16 to any port 8080 proto tcp`.
Site-a works again.

**Step 3.** Prove 8080 is closed from outside: from your laptop,
`nc -vz -w 3 192.168.56.10 8080` must time out, while `curl -H 'Host: site-a.example.com' http://192.168.56.10/` works.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| Traefik 502, log `connect: connection refused` | Apache bound to 127.0.0.1, or wrong port in the service URL | `sudo ss -ltnp 'sport = :8080'` |
| Traefik 504 after 30 s, `i/o timeout` | UFW drops bridge-to-host traffic | Test from Traefik's namespace (netshoot), then the UFW rule |
| Wrong site for a name | `passHostHeader: false`, or a vhost still on `*:80` | `sudo apache2ctl -S`, the whoami test (1.5) |
| Redirect loop | Apache still forces HTTPS | Capstone break 3 (8.5) |
| Every client is 172.18.x in Apache's log, IP allow-lists wide open | `mod_remoteip` missing | Topic 2.8 |
| Certificate errors weeks later | certbot still renews via the `apache` authenticator, or a bridge certificate expired | `sudo certbot renew --dry-run`; switch to `certResolver` |
| Apache's internal port answers from the internet | Wildcard bind without a firewall rule | `nc -vz` from outside |

**Why it matters for troubleshooting**

This is the safest first move of any migration: zero application changes and a
rollback that is one `Listen` line away. Each of the seven parts has its own
failure signature, listed above, so a problem after the move points straight at
the part that was skipped.

**Next step**

Topic 7.2: the same idea on a plain VM without containers, with nginx in front.

### 7.2 Nginx in front of Apache

**Level:** [L2 · Mid]

**Concept**

The classic VM pattern from before containers: nginx owns 80/443, terminates
TLS, serves static files and buffers slow clients; Apache keeps the
`.htaccess` and mod_php applications on `127.0.0.1:8080`. Unlike Traefik in a
container, loopback works here because both run on the host.

Choose it when the box has no Docker or Dokploy, when you want nginx's request
buffering in front of a prefork/mod_php Apache (slow uploads then stop holding
expensive Apache workers, topics 1.1 and 2.10), or when a fleet of VMs is built
by Ansible rather than a platform.

```nginx
# /etc/nginx/sites-available/shop.conf
server {
    listen 80;
    server_name shop.example.com www.shop.example.com;
    return 301 https://$host$request_uri;
}
server {
    # nginx 1.25.1+ prefers "listen 443 ssl;" plus "http2 on;"
    listen 443 ssl http2;
    server_name shop.example.com www.shop.example.com;
    ssl_certificate     /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;
    client_max_body_size 50m;

    # static files straight from disk, without waking Apache
    location /static/ {
        root /var/www/shop/public;
        expires 7d;
    }
    location / {
        include snippets/proxy-common.conf;
        proxy_pass http://127.0.0.1:8080;
    }
}
```

`snippets/proxy-common.conf` is the snippet from topic 3.5; it sends `Host`,
`X-Forwarded-For` and `X-Forwarded-Proto $scheme` (which is `https` here). On the
Apache side: `Listen 127.0.0.1:8080`, vhosts on `*:8080`,
`RemoteIPInternalProxy 127.0.0.1`, and `SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on`.

Certificates: renewals that used certbot's `apache` authenticator must move to
`nginx` (or `webroot`). Run `sudo certbot certonly --nginx --cert-name shop.example.com -d shop.example.com -d www.shop.example.com`
once and answer "Renew & replace" (or add `--force-renewal`): if you choose to keep
the existing certificate, certbot changes nothing and the renewal config still
says `apache`. Then check `sudo grep authenticator /etc/letsencrypt/renewal/shop.example.com.conf`
and run `sudo certbot renew --dry-run`.

**Key terms**

| Term | Meaning |
|---|---|
| Request buffering | nginx reads the whole upload before Apache sees it (default on) |
| `proxy_redirect` | nginx's equivalent of `ProxyPassReverse` (default rewrites redirects from the `proxy_pass` URL) |
| Upstream `Server` header | nginx hides the backend's `Server` header by default and sends its own |

**See it on a real system**

```bash
sudo nginx -T 2>/dev/null | grep -nE '^\s*(server_name|listen|proxy_pass)\b'
sudo ss -ltnp '( sport = :443 or sport = :8080 )'
curl -sI -H 'Host: shop.example.com' http://127.0.0.1:8080/ | grep -iE '^(HTTP|server)'                  # Apache directly
curl -sI --resolve shop.example.com:443:127.0.0.1 https://shop.example.com/ | grep -iE '^(HTTP|server)'  # through nginx
```

```
LISTEN 0      511          0.0.0.0:443        0.0.0.0:*    users:(("nginx",pid=3102,fd=7),("nginx",pid=3101,fd=7))
LISTEN 0      511        127.0.0.1:8080       0.0.0.0:*    users:(("apache2",pid=1301,fd=3),("apache2",pid=1304,fd=3))
HTTP/1.1 200 OK
Server: Apache/2.4.58 (Ubuntu)
HTTP/2 200
server: nginx/1.24.0 (Ubuntu)
```

→ Apache listens on loopback only, so nothing outside the host can bypass nginx.
The same request answers `Server: Apache` directly and `server: nginx` through
the edge.

**Hands-on lab (test VM only)**

**Step 1.** On snapshot A (Apache on 80): change `Listen 80` to
`Listen 127.0.0.1:8080` in `ports.conf` and `<VirtualHost *:80>` to
`<VirtualHost *:8080>` in `000-default.conf`, configtest, restart Apache. Install
nginx (if topic 3.1 left it on 8088, put its default site back on 80), create
the topic 3.5 snippet and its `map` file if you skipped that lab (the snippet
uses `$connection_upgrade`, so `nginx -t` fails without the `map`), and replace
the default site's `location /` with `include snippets/proxy-common.conf;` and
`proxy_pass http://127.0.0.1:8080;`. `nginx -t`, reload, and `curl -sI http://localhost/`
shows `server: nginx` with Apache's page.

**Step 2.** Break it: change the `proxy_pass` port to 8081, reload. You get
**502** and nginx's error log says
`connect() failed (111: Connection refused) while connecting to upstream ... upstream: "http://127.0.0.1:8081/"`.
Fix the port.

**Step 3.** Look at Apache's access log: every line starts with `127.0.0.1`.
Enable `mod_remoteip` with `RemoteIPInternalProxy 127.0.0.1` and a `%a` log
format (topic 2.8) and the real client appears.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| 502, `connect() failed (111: Connection refused)` | Port mismatch, or Apache down | Match `proxy_pass` to Apache's `Listen` |
| App builds links to `http://127.0.0.1:8080` | Host not forwarded | `proxy_set_header Host $host;` (snippet) |
| Redirect loop on HTTPS | Apache rule tests `%{HTTPS}` | Same fix as capstone break 3 |
| Apache logs show only 127.0.0.1 | No `mod_remoteip` | Topic 2.8 |
| 413 on uploads that worked before | nginx's default `client_max_body_size 1m` | Raise it where uploads happen |
| Renewal fails after the move | certbot still uses the `apache` authenticator | Switch to `--nginx` or webroot |

**Why it matters for troubleshooting**

You will find this layout on many inherited VMs. Reading it is the same skill as
7.1 with different names: which process owns 443, where it forwards, and which
headers it adds.

**Next step**

Topic 7.3: how to test any new path before a single user is sent to it.

### 7.3 Testing before DNS: curl --resolve and friends

**Level:** [L2 · Mid]

**Concept**

Never test a migration by changing DNS. Pin the name to the new address for one
request instead, so Host and SNI stay correct while every user still goes the
old way:

| Tool | What it does | Use it for |
|---|---|---|
| `curl -H 'Host: NAME' http://IP:PORT/` | Sets the Host header only, no SNI | Plain-HTTP backends such as Apache on 8080 |
| `curl --resolve NAME:443:IP https://NAME/` | Pins DNS for that name and port; Host and SNI are correct | HTTPS through a new edge |
| `curl --connect-to NAME:443:IP:8443 https://NAME/` | Connects somewhere else but keeps NAME in Host and SNI | A backend's TLS port with the right SNI |
| `openssl s_client -connect IP:443 -servername NAME` | Raw TLS handshake | Which certificate a name gets |
| `/etc/hosts` on your laptop | Pins for a browser | Click-testing; remove the line afterwards |

On the same host (your case), DNS does not change at all: the cutover is the
port swap, and HTTP-01 issuance works as soon as Traefik owns port 80. On a new
server, lower the TTL days ahead and pin names with `--resolve` until every
check is green.

A read-only verification matrix you can run before, during and after the
cutover:

```bash
#!/usr/bin/env bash
# verify-sites.sh: check every name through the NEW edge (read-only). Usage: ./verify-sites.sh EDGE_IP
EDGE=${1:-192.0.2.10}
for name in shop.example.com www.shop.example.com wiki.example.com crm.example.com; do
  https=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$name:443:$EDGE" "https://$name/")
  http=$(curl -s -o /dev/null -w '%{http_code}->%{redirect_url}' --max-time 10 --resolve "$name:80:$EDGE" "http://$name/")
  cert=$(echo | openssl s_client -connect "$EDGE:443" -servername "$name" 2>/dev/null \
         | openssl x509 -noout -issuer -enddate 2>/dev/null | tr '\n' ' ')
  printf '%-22s https=%s  http=%s  %s\n' "$name" "$https" "$http" "$cert"
done
```

```
shop.example.com       https=200  http=301->https://shop.example.com/  issuer=C = US, O = Let's Encrypt, CN = R11 notAfter=Dec 31 23:59:59 2026 GMT
www.shop.example.com   https=200  http=301->https://www.shop.example.com/  issuer=C = US, O = Let's Encrypt, CN = R11 notAfter=Dec 31 23:59:59 2026 GMT
wiki.example.com       https=000  http=301->https://wiki.example.com/  issuer=CN = TRAEFIK DEFAULT CERT notAfter=Oct  3 09:41:12 2027 GMT
crm.example.com        https=502  http=301->https://crm.example.com/  issuer=C = US, O = Let's Encrypt, CN = R10 notAfter=Dec 30 11:02:44 2026 GMT
```

- shop and www → green: valid certificate, 200, HTTP redirects to HTTPS.
- wiki → `https=000` means curl refused the TLS connection, and the issuer shows why: Traefik's default certificate. No certificate for that name yet (topic 4.7).
- crm → TLS is fine but the edge answers 502: a service problem (topic 4.4, capstone break 1).

Do not switch anything until every line is green.

**Key terms**

| Term | Meaning |
|---|---|
| Pinning | Forcing a name to an IP for one tool or one machine |
| `000` from curl | No HTTP response at all: DNS, TCP or TLS failed |
| TTL | How long resolvers may cache a record; lower it days before an IP change |

**See it on a real system**

```bash
curl -sv --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/ -o /dev/null 2>&1 \
  | grep -E 'Connected to|subject:|issuer:|SSL certificate verify|^< HTTP'
```

```
* Connected to crm.example.com (192.0.2.10) port 443
*  subject: CN=crm.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R10
*  SSL certificate verify ok.
< HTTP/2 502
```

→ `Connected to crm.example.com (192.0.2.10)` proves the pin worked; the
certificate is valid; the 502 comes from the edge, not from DNS or TLS.

**Hands-on lab (test VM only)**

**Step 1.** Copy the script to the capstone VM, set the names to site-a, site-b
and whoami, and run `./verify-sites.sh 127.0.0.1`. HTTPS shows `000` because the
capstone serves Traefik's default certificate; add `-k` to the `https=` curl for
the lab and run it again.

**Step 2.** Stop Apache (`sudo systemctl stop apache2`) and run it again: site-a
and site-b turn into 502 while whoami is unchanged (its `http=` column stays
200; its `https=` column shows Traefik's 404 throughout, because the capstone
gives whoami no `websecure` router). Start Apache.

**Step 3.** From your laptop, pin one name in `/etc/hosts` and open it in a
browser. Remove the line afterwards and confirm the browser no longer reaches it.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| `curl https://IP/` shows the wrong certificate | No SNI is sent when you connect to an IP | Use `--resolve` |
| `--resolve` seems ignored | The name or port in `--resolve` differs from the URL (443 vs 8443) | Same name and port in both |
| curl is fine, the browser still shows the old site | Browser or OS DNS cache, HSTS, a forgotten `/etc/hosts` line | Private window, `resolvectl flush-caches`, check `/etc/hosts` |
| `https=000` | TLS failed: default certificate, expired, untrusted private CA | `curl -v` for the exact error |

**Why it matters for troubleshooting**

Testing the new path while users stay on the old one is the difference between a
cutover and a gamble. The same matrix, run after the change, is your
verification evidence for the change ticket.

**Next step**

Topic 7.4: moving sites off Apache one at a time.

### 7.4 Moving vhosts one by one

**Level:** [L3 · Senior]

**Concept**

Once Traefik owns the edge (7.1), each Apache site becomes its own small
migration, the **strangler pattern**: inventory it (2.12), decide (retire, keep
on Apache, or containerise), deploy the new version next to the old one, test it
(7.3), shift traffic in steps, watch, and only then disable the Apache vhost.

Three traffic-shifting tools in a Traefik file-provider config, from safest to
boldest:

**1. Testers only.** A longer rule wins by default (topic 4.3), so a router that
also matches your office range takes precedence for your testers:

```yaml
http:
  routers:
    crm-new-testers:
      entryPoints: [websecure]
      rule: "Host(`crm.example.com`) && ClientIP(`198.51.100.0/24`)"
      service: crm-new
      tls:
        certResolver: letsencrypt
    crm-legacy:
      entryPoints: [websecure]
      rule: "Host(`crm.example.com`)"
      service: apache-legacy
      tls:
        certResolver: letsencrypt
  services:
    crm-new:
      loadBalancer:
        servers:
          - url: "http://crm-x7k2p9:8069"
```

`crm-x7k2p9` is the new app's Swarm service name on dokploy-network. Deploy it
in Dokploy **without** the public domain (or with a temporary name such as
crm-new.example.com); otherwise Dokploy writes its own routers for
crm.example.com and they compete with yours. `ClientIP` matches the TCP peer, so
behind another load balancer use a header rule such as
``Host(`crm.example.com`) && Header(`X-Canary`, `1`)`` instead.

**2. A percentage of everyone.** A weighted service (topic 4.4) with a sticky
cookie, so a logged-in user stays on one version:

```yaml
http:
  services:
    crm-canary:
      weighted:
        services:
          - name: apache-legacy
            weight: 9
          - name: crm-new
            weight: 1
        sticky:
          cookie:
            name: crm_canary
```

**3. Everyone.** Point the `crm-legacy` router's `service:` at `crm-new`. Keep
`apache-legacy` defined, so the rollback is the same one-line change back.

Data decides how far you can go. If old and new versions would write to
different databases or upload directories, a canary splits your data. Share the
store (same schema), or skip the canary and use a short maintenance window
instead. That judgement is the senior part of this topic.

Per-site checklist:

| # | Check | Evidence |
|---|---|---|
| 1 | Inventory row complete: names, backend, certificate, cron jobs, uploads, owner | Table from 2.12 |
| 2 | Decision recorded: retire, keep on Apache, or containerise | Owner's sign-off |
| 3 | New version running without the public domain | `docker service ps APPNAME` |
| 4 | Data path decided: shared database, migrated files, or write freeze | Written in the change |
| 5 | Tested with `--resolve` and the testers-only rule | Matrix output (7.3) |
| 6 | Traffic shifted; 5xx rate and app errors watched | Traefik access log per service |
| 7 | Apache vhost disabled after a quiet period (`a2dissite`), not deleted | `sudo apache2ctl -S` |

**Key terms**

| Term | Meaning |
|---|---|
| Strangler pattern | Replace a system piece by piece behind a stable front door |
| Canary | A small share of real traffic on the new version |
| Sticky cookie | Keeps one client on one backend across requests |

**See it on a real system**

```bash
# Which routers claim crm.example.com, and where do they send it?
curl -s http://127.0.0.1:8080/api/http/routers \
  | jq -r '.[] | select(.rule | test("crm.example.com")) | [.name, .service, .status] | @tsv'
# How much traffic each version really got (JSON access log, topic 4.9)
sudo jq -r 'select(.RequestHost == "crm.example.com") | .ServiceName' ACCESS_LOG_FILE | sort | uniq -c
```

```
crm-new-testers@file   crm-new         enabled
crm-legacy@file        apache-legacy   enabled
    212 apache-legacy@file
     18 crm-new@file
```

→ Both routers are live; your testers' 18 requests reached the new version,
everyone else stayed on Apache.

**Hands-on lab (test VM only)**

**Step 1.** In the capstone, run site-b's files in a container: add a service
`site-b-new` (image `httpd:2.4`, volume `/var/www/site-b:/usr/local/apache2/htdocs:ro`)
to `compose.yaml`, `docker compose up -d`.

**Step 2.** Add a `site-b-new` service (`http://site-b-new:80`) and a testers
router ``Host(`site-b.example.com`) && ClientIP(`192.168.56.1/32`)`` to
`dynamic/apache.yml`. From your laptop you get the container (its `Server`
header says `Apache/2.4.x (Unix)`); from the VM itself (`curl -H 'Host: site-b.example.com' http://127.0.0.1/`)
you still get the host's Apache (`Ubuntu`), because those requests come from the
Docker gateway address.

**Step 3.** Switch the plain site-b router to `site-b-new`, check the access
log, then roll back by switching it again. Time the rollback.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Testers still see the old app | `ClientIP` sees a load balancer's address, or the tester rule is not the longer one | Routers API; use a header rule |
| Users randomly logged out during the canary | Sessions not shared between versions | Sticky cookie, or a shared session store |
| Old and new routers fight over a name | The app was deployed in Dokploy with the public domain | Deploy without it; move the domain into Dokploy only at the final switch, then delete your routers |
| Data written to two places | Canary on a stateful app | Maintenance window instead of a canary |

**Why it matters for troubleshooting**

One site at a time means a small blast radius and an independent rollback for
each move. When something breaks, the access log's service name tells you
immediately whether the old or the new version served the failing request.

**Next step**

Topic 7.5: the one moment that carries real risk, when 80/443 change owner.

### 7.5 Zero-downtime cutover

**Level:** [L3 · Senior]

**Concept**

Everything before and after can be done with no impact. The risky moment is when
80/443 move from Apache to Traefik. Make it short, rehearsed and reversible:

```
T-7d   inventory, decision, change request approved; lower DNS TTL to 300 s if any IP changes
T-3d   Apache ALSO listens on its internal port with the vhosts duplicated → test with -H 'Host:' (no impact)
T-3d   images pulled, legacy route file written, rehearsal + rollback on a VM snapshot
T0     remove Listen 80/443 from Apache, restart          ← sites unreachable from here
T0+1   Traefik binds 80/443 (installer / docker compose up / Traefik already waiting)
T0+2   verify-sites.sh through the real IP; watch ACME issuance in Traefik's log   ← sites back
T0+15  watch 5xx rate, error logs, real client IPs; close the change, or roll back
```

The outage is the gap between Apache releasing 443 and Traefik binding it.
With a Traefik that is ready to start (image pulled, files in place) it lasts
seconds. With Dokploy's installer it lasts minutes, because the installer
refuses to run while 80/443 are taken (case study 21 plans about four minutes);
book a window and say so.

Certificates at the moment of the swap: names that already point at this host
get Let's Encrypt certificates through HTTP-01 as soon as Traefik owns port 80,
usually within a minute. Until then, clients see `TRAEFIK DEFAULT CERT`. For
**HSTS** sites that is a hard browser error with no "continue" button, so give
them a bridge certificate (7.1) or issue with DNS-01 before T0.

On a **new** server (new IP), both edges serve every name, you switch DNS, wait
longer than the old TTL, and watch the old edge's access log drain to zero
before you retire it.

Define the **rollback trigger** before T0, in numbers: for example "any kept
site failing for more than 15 minutes, or partner API calls failing".

**Key terms**

| Term | Meaning |
|---|---|
| Cutover window | The planned minutes when the edge changes owner |
| Rollback trigger | The measurable condition that means "roll back now", agreed in advance |
| Drain | Waiting until the old path receives no more traffic |

**See it on a real system**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 )'          # who owns the doors right now?
docker logs -f --since 5m dokploy-traefik 2>&1 | grep -iE 'acme|certificate|error'
./verify-sites.sh 192.0.2.10                             # 7.3, during and after the swap
sudo tail -f /var/log/apache2/*access.log | awk '{print $1, $7, $9}'   # real client IPs arriving via Traefik?
```

```
# T0-1: Apache owns the doors
LISTEN 0      511                *:80               *:*    users:(("apache2",pid=1301,fd=4),...)
LISTEN 0      511                *:443              *:*    users:(("apache2",pid=1301,fd=6),...)
# T0+1: Traefik owns them, Apache only on 8080
LISTEN 0      4096         0.0.0.0:80         0.0.0.0:*    users:(("docker-proxy",pid=2311,fd=4))
LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*    users:(("docker-proxy",pid=2330,fd=4))
```

**Hands-on lab (test VM only)**

**Step 1.** Prepare the "before" state: snapshot A plus the capstone Apache
vhosts on 8080 **and** the stock site still on 80; capstone `compose.yaml`
written but not started.

**Step 2.** In a second terminal, run a request every 0.2 s and print each
change of status:

```bash
while true; do curl -s -o /dev/null -w '%{http_code}\n' -m 2 -H 'Host: site-a.example.com' http://127.0.0.1/; sleep 0.2; done | uniq -c
```

**Step 3.** Do the swap: remove `Listen 80`, restart Apache, `docker compose up -d`
in `~/capstone`. Count the `000` lines: that is your outage, in requests. Then
do the rollback (7.6) and count again. Write both numbers into your change
template.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Traefik restart-loops at T0+1 | Apache still holds 443: a `Listen` in another file, `[::]:443`, or a socket unit | `sudo ss -ltnp 'sport = :443'`, grep every `Listen` |
| Browser shows a certificate error with no way to continue | Default certificate on an HSTS site during issuance | Bridge certificate or DNS-01 before T0 |
| ACME `too many failed authorizations` | Retried with broken DNS or firewall | Rehearse against the staging CA; fix the cause; wait |
| Some users still reach the old server | Long TTL or cached DNS | Lower TTL days before; keep the old edge serving until drained |
| Rollback takes far longer than planned | It was never rehearsed | Rehearse on a snapshot at T-3d |

**Why it matters for troubleshooting**

A few planned minutes with a tested rollback is professional; an evening of
unplanned 502s is not. The timeline also tells you, during an incident, exactly
which step introduced the failure.

**Next step**

Topic 7.6: rolling back, and finally retiring Apache.

### 7.6 Rollback and retiring Apache

**Level:** [L3 · Senior] → [L4 · Lead/SRE]

**Concept**

There are two different rollbacks, and both must be written before T0:

| Level | What you do | Impact |
|---|---|---|
| Per site | Point that site's router back at `apache-legacy` (hot reload) | Seconds, invisible to users |
| Whole edge | Stop Traefik, give 80/443 back to Apache from the backup | Dokploy apps lose their front door while Traefik is stopped |

Whole-edge rollback on a Dokploy host:

> ⚠️ Stopping `dokploy-traefik` takes **every** Dokploy-hosted site offline until
> it is started again. Prefer per-site rollback; use this only when the edge
> itself is the problem and the rollback trigger has fired.

```bash
# 1. Free 80/443 (on installs where Traefik is a Swarm service: docker service scale dokploy-traefik=0)
docker stop dokploy-traefik
# 2. Restore Apache's listeners and vhosts from the pre-change backup (2.11)
sudo cp -a /root/apache2.bak.2026-10-03-0900/ports.conf /etc/apache2/ports.conf
sudo cp -a /root/apache2.bak.2026-10-03-0900/sites-available/. /etc/apache2/sites-available/
sudo apache2ctl configtest && sudo systemctl restart apache2
# 3. Verify the doors and every site
sudo ss -ltnp '( sport = :80 or sport = :443 )'
./verify-sites.sh 192.0.2.10
```

**Retiring Apache** is a change of its own, done only after the last site has
been off it for an agreed quiet period (for example 14 days with no real
requests in its access logs):

1. Evidence: the last real request per access log (topic 2.9) is older than the quiet period.
2. Stop it now and at boot: `sudo systemctl disable --now apache2`, then `sudo systemctl mask apache2`.
3. Certificates: remove renewals that still use the `apache` authenticator (`sudo grep -l 'authenticator = apache' /etc/letsencrypt/renewal/*.conf`). Back up `/etc/letsencrypt` first; `certbot delete` is irreversible.
4. Firewall: delete the UFW rule for the internal port.
5. Everything that expected Apache: monitoring checks, cron jobs, logrotate, backup scripts.
6. Keep a tar of `/etc/apache2` and the docroots for months. Use `apt remove`, not `apt purge`, until you are sure: purge deletes `/etc/apache2`.
7. Update the inventory and PORTS.md, close the change, write the follow-up note.

**Key terms**

| Term | Meaning |
|---|---|
| Quiet period | Agreed time with zero real traffic before something is retired |
| `mask` | Makes a unit impossible to start, even as a dependency |
| Follow-up | An action item from the change or postmortem, with an owner and a date |

**See it on a real system**

```bash
# Proof that Apache is no longer used: last request per access log
for f in /var/log/apache2/*access.log; do printf '%-45s %s\n' "$f" "$(sudo tail -n1 "$f" | awk '{print $4}')"; done
systemctl is-enabled apache2; systemctl is-active apache2
sudo grep -l 'authenticator = apache' /etc/letsencrypt/renewal/*.conf 2>/dev/null
grep -RlE 'apache2|apache2ctl' /etc/cron* /etc/logrotate.d /etc/systemd/system 2>/dev/null
```

```
/var/log/apache2/shop-access.log              [12/Sep/2026:16:20:03
/var/log/apache2/wiki-access.log              [14/Mar/2026:09:02:51
masked
inactive
/etc/logrotate.d/apache2
```

→ No request for three weeks, Apache masked and stopped, no renewal depends on
it, and only the package's own logrotate file still mentions it.

**Hands-on lab (test VM only)**

**Step 1.** Per-site rollback: with site-b on its container (7.4 lab), switch the
router back to `apache` and time it with the request loop from 7.5. Expect zero
failed requests.

**Step 2.** Whole-edge rollback on the capstone: `docker compose stop traefik`,
put `Listen 80` back, restore the stock `000-default` vhost, restart Apache,
verify. Then reverse it again. Count failed requests both ways.

**Step 3.** Retire: once site-a and site-b both run as containers (repeat the
7.4 lab for site-a), `disable --now`
and `mask` Apache, reboot the VM, and prove that nothing listens on 8080 and
that both sites still answer through Traefik.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Rollback: Apache fails with `AH00072 ... Address already in use` | Traefik or docker-proxy still holds 80/443 (restart policy, Swarm service) | `sudo ss -ltnp`, `docker ps`, `docker service ls`; stop it properly |
| After a reboot Apache is back on 443 and Traefik is down | The retired Apache was only stopped | `disable` and `mask` |
| Certificate expiry emails weeks later | certbot still renews names via Apache | Clean up the renewal configs |
| The rollback restored old config, but data changed meanwhile | Writes happened on the new version | The rollback plan must say which way data flows |
| Config needed for a rollback is gone | `apt purge` ran too early | Restore from the tar; remove, do not purge, until the quiet period ends |

**Why it matters for troubleshooting**

A rehearsed rollback is what lets you move fast, and a finished decommission
closes the security hole of an unpatched Apache nobody watches. At L4 you also
own the paperwork: the change record, the follow-ups and the short postmortem
([CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md)).

**Next step**

Section 8: build the whole thing on a VM and break it three ways.

---

## 8. Capstone lab: Apache behind Traefik

> 📚 **Study path:** 1) Note: re-read topics 1.2, 1.5, 2.7, 4.3 and 4.4 (the three breaks live there) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — *Docker Compose* lesson if Compose feels rusty ([lesson notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)) · 3) Practice environment: your snapshot-A VM or the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) (one hour, extendable) · 4) Then: the Ops Ladder L3 drill "make Traefik return 502 with a wrong port, find and fix it from Traefik's logs alone".

This lab ties sections 1, 2 and 4 together, and it is the environment many
earlier labs call "the capstone" or "snapshot B". Build it once (8.1–8.2, about
45 minutes), take snapshot B, then work through the three breaks (8.3–8.5,
15–20 minutes each). Each break is written as an incident in the handbook's
step format: diagnose from evidence (status, body, access log, API) **before**
you open the config. Test VM only.

```
laptop 192.168.56.1     curl -H 'Host: site-a.example.com' http://192.168.56.10/   (or an /etc/hosts pin)
   │
   ▼
VM 192.168.56.10
 ┌──────────────── docker compose project "capstone" (~/capstone) ─────────────────┐
 │ traefik   publishes :80 :443   API on 127.0.0.1:9080 → container :8080            │
 │   ├─ file provider   dynamic/apache.yml: site-a, site-b routers ─► service apache │
 │   │                                       http://host.docker.internal:8080       │
 │   └─ docker provider whoami labels ─► whoami container :80                        │
 └──────────────────────────────────────────────┬───────────────────────────────────┘
                                                │ host-gateway (docker0, 172.17.0.1)
                                                ▼
 Apache on the host, *:8080     site-a.example.com → /var/www/site-a
                                site-b.example.com → /var/www/site-b
```

### 8.1 Build Apache with two name-based vhosts

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Apache becomes a backend: two name-based vhosts on an internal port, no longer
on 80 or 443. This is your production server in miniature after the
"Apache behind Traefik" move (7.1).

**Key terms**

| Term | Meaning |
|---|---|
| Backend port | Apache's internal listener, here 8080 |
| Default vhost | site-a, because `site-a.conf` sorts first among the vhosts on 8080 |
| Per-vhost logs | `site-a-access.log`, `site-a-error.log`, used by later labs |

**See it on a real system**

What the finished build looks like:

```bash
sudo apache2ctl -S 2>/dev/null | head -5
sudo ss -ltnp 'sport = :8080'
for h in site-a site-b nothing; do printf '%-8s ' "$h"; curl -s -H "Host: $h.example.com" http://127.0.0.1:8080/; done
```

```
VirtualHost configuration:
*:8080                 is a NameVirtualHost
         default server site-a.example.com (/etc/apache2/sites-enabled/site-a.conf:1)
         port 8080 namevhost site-a.example.com (/etc/apache2/sites-enabled/site-a.conf:1)
         port 8080 namevhost site-b.example.com (/etc/apache2/sites-enabled/site-b.conf:1)
LISTEN 0      511                *:8080             *:*    users:(("apache2",pid=5120,fd=4),("apache2",pid=5119,fd=4),("apache2",pid=5117,fd=4))
site-a   <h1>site-a</h1>
site-b   <h1>site-b</h1>
nothing  <h1>site-a</h1>
```

→ Two name-based vhosts on 8080; an unknown name gets site-a, the default vhost
(topic 1.2 fixes that with a catch-all).

**Hands-on lab (test VM only)**

Start from snapshot A (Ubuntu with the stock `apache2` on port 80).

**Step 1.** Back up, then create the two document roots:

```bash
sudo cp -a /etc/apache2 /root/apache2.bak.$(date +%F-%H%M)
for s in site-a site-b; do
  sudo mkdir -p /var/www/$s
  echo "<h1>$s</h1>" | sudo tee /var/www/$s/index.html >/dev/null
done
```

**Step 2.** Create the two vhosts (the unquoted heredoc fills in `$s`; the
backslash keeps `${APACHE_LOG_DIR}` for Apache):

```bash
for s in site-a site-b; do
sudo tee /etc/apache2/sites-available/$s.conf >/dev/null <<EOF
<VirtualHost *:8080>
    ServerName $s.example.com
    DocumentRoot /var/www/$s
    ErrorLog \${APACHE_LOG_DIR}/$s-error.log
    CustomLog \${APACHE_LOG_DIR}/$s-access.log combined
</VirtualHost>
EOF
done
```

**Step 3.** Make Apache a backend: only port 8080, the stock sites off, the new
ones on. `Listen` changes need a restart, not a reload:

```bash
echo 'Listen 8080' | sudo tee /etc/apache2/ports.conf
sudo a2dissite 000-default
sudo a2dissite default-ssl 2>/dev/null || true
sudo a2ensite site-a site-b
sudo apache2ctl configtest && sudo systemctl restart apache2
```

**Step 4.** Run the "See it" commands above and compare.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| `curl: (7) Failed to connect to 127.0.0.1 port 8080` | No `Listen 8080`, or only reloaded | `sudo ss -ltnp 'sport = :8080'` |
| Both names show site-a | Typo in `ServerName`, or both vhosts have the same name | `sudo apache2ctl -S` |
| 403 Forbidden | Document root outside `/var/www`, or permissions | Topic 2.4 |
| configtest: `Could not open configuration file ...` | A dangling symlink left by an earlier lab | `find /etc/apache2/ -xtype l` |

**Why it matters for troubleshooting**

You will compare every later symptom with this known-good state. Save the
`apache2ctl -S` and `ss` output; "what changed?" is much easier against a
baseline.

**Next step**

Topic 8.2: put Traefik in front.

### 8.2 Put Traefik in front with Docker Compose

**Level:** [L2 · Mid] → [L3 · Senior]

**Concept**

A Traefik v3 container owns 80/443. Its static config comes from command-line
flags in `compose.yaml` (so a static change means recreating the container,
topic 4.1). Its dynamic config comes from a watched directory (the legacy
routes to Apache) and from Docker labels (whoami). `host.docker.internal` is
mapped to the host's Docker gateway so the container can reach Apache on the
host. The API listens on `127.0.0.1:9080`, because Apache already owns 8080.

**Key terms**

| Term | Meaning |
|---|---|
| `host-gateway` | Special `extra_hosts` value: the host's address on the default Docker bridge (172.17.0.1) |
| `@file` / `@docker` | Provider suffix on every router and service name |
| `tls: {}` | HTTPS router with no resolver: Traefik serves its default certificate |

**See it on a real system**

What the finished build looks like:

```bash
cd ~/capstone && docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
for h in site-a site-b whoami; do printf '%-7s ' "$h"; curl -s -H "Host: $h.example.com" http://127.0.0.1/ | head -1; done
curl -sk --resolve site-a.example.com:443:127.0.0.1 https://site-a.example.com/
curl -s http://127.0.0.1:9080/api/http/routers | jq -r '.[] | [.name, .status, .rule] | @tsv'
docker compose logs traefik | grep '"site-a@file"' | tail -1    # API calls are access-logged too, so filter
```

```
NAME                 STATUS          PORTS
capstone-traefik-1   Up 2 minutes    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 127.0.0.1:9080->8080/tcp
capstone-whoami-1    Up 2 minutes    80/tcp
site-a  <h1>site-a</h1>
site-b  <h1>site-b</h1>
whoami  Hostname: 3f9c1d2e8a4b
<h1>site-a</h1>
api@internal         enabled  PathPrefix(`/api`)
dashboard@internal   enabled  PathPrefix(`/`)
site-a-secure@file   enabled  Host(`site-a.example.com`)
site-a@file          enabled  Host(`site-a.example.com`)
site-b-secure@file   enabled  Host(`site-b.example.com`)
site-b@file          enabled  Host(`site-b.example.com`)
whoami@docker        enabled  Host(`whoami.example.com`)
traefik-1  | 172.18.0.1 - - [03/Oct/2026:11:02:15 +0000] "GET / HTTP/1.1" 200 16 "-" "curl/8.5.0" 4 "site-a@file" "http://host.docker.internal:8080" 2ms
```

→ Five routers you wrote, plus two internal ones for the API and dashboard. The
access log line already names router and backend: that is what you will read in
every break.

**Hands-on lab (test VM only)**

**Step 1.** Create the project directory and the compose file:

```bash
mkdir -p ~/capstone/dynamic && cd ~/capstone
cat > compose.yaml <<'EOF'
services:
  traefik:
    # pin a v3 minor you have tested. Use v3.6 or newer: older minors' Docker
    # provider fails on Docker Engine 29+ ("client version 1.24 is too old");
    # Dokploy's installer currently pins a v3.6.x release too
    image: traefik:v3.6
    restart: unless-stopped
    command:
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --providers.file.directory=/etc/traefik/dynamic
      - --providers.file.watch=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --api.insecure=true
      - --log.level=INFO
      - --accesslog=true
    ports:
      - "80:80"
      - "443:443"
      - "127.0.0.1:9080:8080"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./dynamic:/etc/traefik/dynamic:ro
  whoami:
    image: traefik/whoami
    labels:
      - traefik.enable=true
      - traefik.http.routers.whoami.rule=Host(`whoami.example.com`)
      - traefik.http.routers.whoami.entrypoints=web
      - traefik.http.services.whoami.loadbalancer.server.port=80
EOF
```

**Step 2.** Create the legacy routes to Apache:

```bash
cat > dynamic/apache.yml <<'EOF'
http:
  routers:
    site-a:
      entryPoints: [web]
      rule: "Host(`site-a.example.com`)"
      service: apache
    site-b:
      entryPoints: [web]
      rule: "Host(`site-b.example.com`)"
      service: apache
    site-a-secure:
      entryPoints: [websecure]
      rule: "Host(`site-a.example.com`)"
      service: apache
      tls: {}
    site-b-secure:
      entryPoints: [websecure]
      rule: "Host(`site-b.example.com`)"
      service: apache
      tls: {}
  services:
    apache:
      loadBalancer:
        servers:
          - url: "http://host.docker.internal:8080"
        passHostHeader: true
EOF
```

**Step 3.** Start it and run the "See it" commands:

```bash
docker compose up -d
```

**Step 4.** Take **snapshot B** now. Notes for the labs that use it:

- Section 4 commands that query `http://127.0.0.1:8080/api/...` were written for a Dokploy host; on this VM use port **9080**.
- Inside the container the dynamic directory is `/etc/traefik/dynamic` (Dokploy's is `/etc/dokploy/traefik/dynamic`); certificate paths in the 4.7 lab must use the container path.
- UFW is inactive on a fresh Ubuntu. If you enable it, allow the compose network to reach 8080 first (7.1 lab), or every legacy site turns into a 504.
- To use a browser, pin site-a, site-b and whoami to 192.168.56.10 in your laptop's `/etc/hosts`.

**How it breaks**

| Symptom | Cause | First command |
|---|---|---|
| `Bind for 0.0.0.0:80 failed: port is already allocated` or `address already in use` | Apache (or nginx) still listens on 80 | `sudo ss -ltnp 'sport = :80'` |
| 404 for site-a and site-b, whoami fine | `apache.yml` not loaded: YAML error or wrong mount path | `docker compose logs traefik`, routers API |
| 504 after about 30 s | UFW blocks container-to-host traffic to 8080 | `sudo ufw status`, topic 7.1 |
| 502 | Apache not on 8080, or `extra_hosts` missing | `docker compose exec traefik wget -qO- -T 3 http://host.docker.internal:8080/` |
| whoami 404 | Missing `traefik.enable=true` or wrong entryPoint label | Topic 4.6 |

**Why it matters for troubleshooting**

This is case study 21's "Option B" on one VM: Traefik owns the doors, Apache
serves behind it unchanged. Every Dokploy routing incident is a variation of
what you can now reproduce here safely.

**Next step**

Topic 8.3: the first break.

### 8.3 Break 1: wrong port gives 502

**Level:** [L2 · Mid]

**Break it (one terminal, then forget what you did):**

```bash
sed -i 's#host.docker.internal:8080#host.docker.internal:8090#' ~/capstone/dynamic/apache.yml
```

The incident: "site-a and site-b return 502 Bad Gateway."

**Step 1 — Reproduce and identify who answered**

**Goal:** confirm the symptom and find out which hop produced it.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-a.example.com' http://127.0.0.1/
curl -s -H 'Host: site-a.example.com' http://127.0.0.1/; echo
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: whoami.example.com' http://127.0.0.1/
```

```
502
Bad Gateway
200
```

**What it means:** the plain-text `Bad Gateway` body is Traefik's own (topic
6.2), so Traefik answered. A router matched, otherwise you would see a 404, so
routing works and the hop between Traefik and the backend fails. whoami answers
200, so Traefik itself is healthy and the problem is specific to the `apache`
service.

**Why this step (now):** the status code plus the body names the failing layer
in seconds and rules out DNS, TLS and routing before you open a single file.
Comparing with a known-good site separates "Traefik is broken" from "one
service is broken".

**Next step:** 502 with Traefik's body → Step 2. If you get a 404 instead → this
is a routing problem, go to 8.4. If the request hangs about 30 s and ends in
504 → network or firewall (7.1 table). If every site fails, whoami included →
Traefik itself: `docker compose ps` and its logs.

**Step 2 — Read the access log line**

**Goal:** get the router and the backend URL Traefik actually used.

```bash
cd ~/capstone && docker compose logs --since 5m traefik | grep ' 502 ' | tail -2
```

```
traefik-1  | 172.18.0.1 - - [03/Oct/2026:11:20:41 +0000] "GET / HTTP/1.1" 502 11 "-" "curl/8.5.0" 57 "site-a@file" "http://host.docker.internal:8090" 0ms
```

**What it means:** router `site-a@file` matched; the backend URL ends in
`:8090`; the request failed after 0 ms, which means an immediate refusal, not a
timeout. (`11` is the size of the `Bad Gateway` body.)

**Why this step (now):** the access log records the decision Traefik made. You
do not need to guess from config files, and it shows the truth even when
somebody else (or Dokploy) changed the config.

**Next step:** if the port in the URL is not the one the backend listens on →
Step 3 to prove it. If the URL looks right → Step 3 anyway, to test reachability
from Traefik's side.

**Step 3 — Test the backend from Traefik's side**

**Goal:** check what listens where, from the same network namespace Traefik uses.

```bash
cd ~/capstone
sudo ss -ltnp '( sport = :8080 or sport = :8090 )'
docker compose exec traefik wget -qO- -T 3 http://host.docker.internal:8090/; echo "exit=$?"
docker compose exec traefik wget -qO- -T 3 http://host.docker.internal:8080/
```

```
LISTEN 0      511                *:8080             *:*    users:(("apache2",pid=5120,fd=4),...)
wget: can't connect to remote host (172.17.0.1): Connection refused
exit=1
<h1>site-a</h1>
```

**What it means:** nothing listens on 8090. Apache is on 8080 and reachable from
inside the Traefik container. The service URL is wrong, Apache is fine.

**Why this step (now):** it proves the hypothesis along the exact path Traefik
uses (container → host-gateway → Apache) and rules out the other causes of a
502 or 504: a firewall, or Apache bound to 127.0.0.1.

**Next step:** wrong port → Step 4. If 8080 is refused too → Apache is down or
bound to 127.0.0.1 (`ss` would show `127.0.0.1:8080`): fix Apache (8.1). If the
test times out → UFW (7.1 lab).

**Step 4 — Fix and verify**

**Goal:** correct the service URL and prove the fix through the whole chain.

```bash
sed -i 's#host.docker.internal:8090#host.docker.internal:8080#' ~/capstone/dynamic/apache.yml
# the file provider reloads within a second or two, no restart
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-a.example.com' http://127.0.0.1/
curl -s http://127.0.0.1:9080/api/http/services | jq -r '.[] | select(.name == "apache@file") | .loadBalancer.servers[].url'
```

```
200
http://host.docker.internal:8080
```

**What it means:** 200 through Traefik, and the API shows the corrected URL: the
hot reload applied without a restart.

**Why this step (now):** you verify through the same entry users use, and you
confirm Traefik's live state through the API rather than trusting the file.

**Next step:** fixed → write the five-line note below, then 8.4. Still 502 →
back to Step 2: another router or service may be involved.

```
502 from Traefik (plain "Bad Gateway")
 ├─ access log has a router name? ── no ──► not a backend problem: treat it as a 404 (8.4)
 └─ yes → read the backend URL in the log line
      └─ test that URL from Traefik's namespace
           ├─ connection refused ──► wrong port, app not listening, or bound to 127.0.0.1
           ├─ timeout (504 after ~30 s) ──► firewall (UFW) or a network Traefik cannot reach
           └─ works from the namespace ──► scheme mismatch (http vs https) or the app crashes mid-request: app logs
```

**Fix & verify:** service URL back to `:8080`; `curl` returns 200 for site-a and
site-b; the services API shows the right URL.

**Rollback:** keep a copy of every dynamic file before you edit it
(`cp apache.yml apache.yml.bak`) or keep the directory in Git; rollback is
restoring the copy, and the file provider applies it within seconds.

**Prevent it next time:** dynamic files in Git with review; a health check on
the service (topic 4.4) so a dead backend shows up in the API as DOWN; run
`verify-sites.sh` (7.3) after every routing change; in Dokploy, the domain's
port must be the port the container listens on.

The five-line incident note for this break:

```
Symptom:            site-a and site-b 502 Bad Gateway; whoami fine
First wrong guess:  Apache is down
Deciding evidence:  Traefik access log showed backend :8090; nothing listens on 8090; :8080 answers from Traefik's namespace
Fix:                service URL back to :8080 in dynamic/apache.yml (hot reload)
Check first next time: the backend URL in the access log line
```

### 8.4 Break 2: wrong Host rule gives 404

**Level:** [L2 · Mid]

**Break it:**

```bash
sed -i 's#site-b.example.com#site-b.exmaple.com#' ~/capstone/dynamic/apache.yml
```

The incident: "site-b shows 404 page not found; site-a is fine."

**Step 1 — Reproduce and compare the body**

**Goal:** find out whether the 404 comes from the proxy or from the site.

```bash
curl -si -H 'Host: site-b.example.com' http://127.0.0.1/ | sed -n '1p;$p'
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: site-b.example.com' http://127.0.0.1:8080/
```

```
HTTP/1.1 404 Not Found
404 page not found
200
```

**What it means:** the plain-text `404 page not found` is Traefik's "no router
matched". Asked directly on 8080, Apache serves site-b with 200, so the site is
fine and the routing in front of it is not.

**Why this step (now):** it separates "the app says 404" (an HTML page with
Apache's signature) from "the proxy found no route", the cheapest split there
is.

**Next step:** Traefik's 404 → Step 2. If the 404 is an HTML page from Apache →
the request reached Apache: a path or DocumentRoot problem (topic 2.4).

**Step 2 — List the routers and their rules**

**Goal:** see the routing table Traefik actually loaded.

```bash
curl -s http://127.0.0.1:9080/api/http/routers \
  | jq -r '.[] | select(.provider == "file") | [.name, .status, (.entryPoints | join(",")), .rule] | @tsv'
```

```
site-a-secure@file   enabled  websecure  Host(`site-a.example.com`)
site-a@file          enabled  web        Host(`site-a.example.com`)
site-b-secure@file   enabled  websecure  Host(`site-b.exmaple.com`)
site-b@file          enabled  web        Host(`site-b.exmaple.com`)
```

**What it means:** the site-b routers exist and are enabled, but their rule says
`exmaple`. A typo is valid syntax, so Traefik reports no error: it simply never
matches.

**Why this step (now):** the API shows what Traefik merged from all providers,
which is the truth. A disabled router would show an `error` field instead,
which is a different cause.

**Next step:** typo found → Step 4. If there is no site-b router at all → the
provider did not deliver it → Step 3. If the router exists with the right rule
but only on `websecure` while you requested plain HTTP → add a `web` router.

**Step 3 — Check that the provider loaded the file**

**Goal:** rule out a file the provider could not load (only needed when a
router is missing entirely).

```bash
cd ~/capstone && docker compose logs --since 10m traefik | grep -iE 'error|file' | tail -5
```

```
traefik-1  | 2026-10-03T11:31:07Z ERR Error occurred during watcher callback error="/etc/traefik/dynamic/apache.yml: yaml: line 7: did not find expected key" providerName=file
```

**What it means:** this example shows what a YAML syntax error looks like. On a
hot reload Traefik keeps the last good config (topic 4.1); after a restart the
file's routers would be missing entirely. In this break the log is clean: the
file loaded, the rule is just wrong.

**Why this step (now):** a missing router has two very different causes (bad
file vs wrong rule), and the provider log separates them in one command.

**Next step:** YAML error → fix the file (validate it with a YAML linter), then
Step 4's verification. No error → back to Step 2 and compare rules character by
character.

**Step 4 — Fix and verify**

**Goal:** correct the rule and prove both entryPoints work.

```bash
sed -i 's#site-b.exmaple.com#site-b.example.com#' ~/capstone/dynamic/apache.yml
curl -s -H 'Host: site-b.example.com' http://127.0.0.1/
curl -sk --resolve site-b.example.com:443:127.0.0.1 https://site-b.example.com/
```

```
<h1>site-b</h1>
<h1>site-b</h1>
```

**What it means:** both the HTTP and the HTTPS router match again.

**Why this step (now):** a rule typo usually exists in both routers of a name
(the `sed` above changed both); verifying only one entryPoint leaves half the
bug in place.

**Next step:** done → 8.5. Still 404 on one entryPoint → Step 2 again for that
router.

```
404 for one name
 ├─ body is plain "404 page not found" ──► Traefik: no router matched
 │    └─ routers API: is there a router for that name?
 │         ├─ no ──► provider did not deliver it: YAML error (logs), labels not redeployed, traefik.enable missing
 │         └─ yes ─► compare the rule with the Host sent: typo, www vs apex, port in Host, http vs https entryPoint, priority
 └─ body is the app's or Apache's HTML ──► the request reached the backend: path, DocumentRoot, app route
```

**Fix & verify:** rule corrected; site-b answers on both entryPoints; the
routers API shows ``Host(`site-b.example.com`)``.

**Rollback:** restore the previous dynamic file from your copy or Git.

**Prevent it next time:** generate routes from the inventory instead of typing
them; run the verification matrix (7.3) after every change; in Dokploy, point
DNS at the server before adding a domain and use Preview Compose to read the
labels it will inject.

### 8.5 Break 3: redirect loop without X-Forwarded-Proto

**Level:** [L2 · Mid] → [L3 · Senior]

**Break it:** give site-a the "force HTTPS" rule written for a server where
Apache itself terminated TLS (a very common inherited config):

```bash
sudo a2enmod rewrite
sudoedit /etc/apache2/sites-available/site-a.conf     # add the three lines below inside <VirtualHost *:8080>
```

```apache
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

```bash
sudo apache2ctl configtest && sudo systemctl restart apache2
```

The incident: "after the move behind Traefik, site-a says ERR_TOO_MANY_REDIRECTS."

**Step 1 — Follow the redirect chain**

**Goal:** see every hop of the redirect and who issues it.

```bash
curl -skIL --max-redirs 5 --resolve site-a.example.com:443:127.0.0.1 https://site-a.example.com/ \
  | grep -iE '^(HTTP|location|server)'
```

```
HTTP/2 301
location: https://site-a.example.com/
server: Apache/2.4.58 (Ubuntu)
HTTP/2 301
location: https://site-a.example.com/
server: Apache/2.4.58 (Ubuntu)
... (the same three lines four more times)
curl: (47) Maximum (5) redirects followed
```

**What it means:** the redirect points at the very URL you requested, so it can
never end. `server: Apache` means Apache issues it, not Traefik (Traefik passes
the backend's `Server` header through).

**Why this step (now):** a loop has one author. Finding it with one `curl`
saves you from reading Traefik's config when the problem is in Apache's, or the
other way round.

**Next step:** Apache is the author → Step 2. If there is no Apache `Server`
header and Traefik's log shows no backend for these requests → a redirect
middleware is attached to the `websecure` router by mistake: check the router's
middlewares in the API.

**Step 2 — Confirm it in both access logs**

**Goal:** see the same requests on both hops.

```bash
sudo tail -n 2 /var/log/apache2/site-a-access.log
cd ~/capstone && docker compose logs --since 2m traefik | grep 'site-a-secure' | tail -2
```

```
172.18.0.2 - - [03/Oct/2026:11:41:07 +0000] "GET / HTTP/1.1" 301 541 "-" "curl/8.5.0"
172.18.0.2 - - [03/Oct/2026:11:41:07 +0000] "GET / HTTP/1.1" 301 541 "-" "curl/8.5.0"
traefik-1  | 172.18.0.1 - - [03/Oct/2026:11:41:07 +0000] "GET / HTTP/2.0" 301 239 "-" "curl/8.5.0" 88 "site-a-secure@file" "http://host.docker.internal:8080" 2ms
traefik-1  | 172.18.0.1 - - [03/Oct/2026:11:41:07 +0000] "GET / HTTP/2.0" 301 239 "-" "curl/8.5.0" 89 "site-a-secure@file" "http://host.docker.internal:8080" 1ms
```

**What it means:** the client spoke HTTP/2 over TLS to Traefik; Apache received
plain `HTTP/1.1` from Traefik (172.18.0.2) and answered 301 every time. Behind a
TLS-terminating proxy, Apache's own `%{HTTPS}` is always off, so the rule fires
on every request.

**Why this step (now):** it proves the private hop is plain HTTP, which is the
design, not a fault. The fault is a rule that tests the wrong thing.

**Next step:** Step 3, to see what Apache does know about the original request.

**Step 3 — See what Apache receives**

**Goal:** prove that the information needed is already in the request.

```bash
echo 'LogFormat "%h \"%r\" %>s xfp=%{X-Forwarded-Proto}i https=%{HTTPS}e" proto_debug' \
  | sudo tee /etc/apache2/conf-available/proto-debug.conf
sudo a2enconf proto-debug
sudoedit /etc/apache2/sites-available/site-a.conf   # add: CustomLog ${APACHE_LOG_DIR}/site-a-proto.log proto_debug
sudo apache2ctl configtest && sudo systemctl reload apache2
curl -sk -o /dev/null --resolve site-a.example.com:443:127.0.0.1 https://site-a.example.com/
sudo tail -n 1 /var/log/apache2/site-a-proto.log
```

```
172.18.0.2 "GET / HTTP/1.1" 301 xfp=https https=-
```

**What it means:** Traefik told Apache the client used HTTPS
(`X-Forwarded-Proto: https`), but Apache's own `HTTPS` variable is unset because
its connection is plain HTTP. The rule tests the variable instead of the header.

**Why this step (now):** you fix the cause (the wrong test), not a symptom such
as switching off HTTPS at Traefik, which would trade a loop for an insecure site.

**Next step:** Step 4: choose the fix.

**Step 4 — Fix it and verify**

**Goal:** one layer owns the redirect, and the loop is gone.

Option A, best: delete the three rewrite lines from Apache (configtest,
reload) and let the edge redirect. Add a middleware to `dynamic/apache.yml` and
attach it to the `web` routers (site-a shown; do the same for site-b):

```yaml
http:
  middlewares:
    to-https:
      redirectScheme:
        scheme: https
        permanent: true
  routers:
    site-a:
      entryPoints: [web]
      rule: "Host(`site-a.example.com`)"
      middlewares: [to-https]
      service: apache
```

Option B, when the rule must stay in Apache (for example in an application's
`.htaccess`): make it proxy-aware (recipe 2 in topic 2.7):

```apache
    RewriteEngine On
    RewriteCond %{HTTP:X-Forwarded-Proto} !=https
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

Only trust that header when port 8080 is reachable from Traefik alone (7.1);
otherwise anyone can send `X-Forwarded-Proto: https` directly.

Option C, for PHP applications that check `$_SERVER['HTTPS']` (WordPress with an
`https://` site URL loops the same way): `SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on`
in the vhost. It fixes the application, not `mod_rewrite`'s `%{HTTPS}`.

Verify:

```bash
curl -skIL --max-redirs 5 --resolve site-a.example.com:443:127.0.0.1 https://site-a.example.com/ | grep -iE '^HTTP'
# GET, not HEAD: Traefik answers a permanent redirect with 301 for GET but 308 for any other method, HEAD included
curl -si -H 'Host: site-a.example.com' http://127.0.0.1/ | grep -iE '^(HTTP|location)'
```

```
HTTP/2 200
HTTP/1.1 301 Moved Permanently
Location: https://site-a.example.com/
```

**What it means:** HTTPS answers 200 at the first hop, and plain HTTP is
redirected once, by Traefik (Option A).

**Why this step (now):** you verify both directions: the loop is gone on HTTPS,
and HTTP still ends up on HTTPS, so you did not trade one bug for another.

**Next step:** remove the debug log (`sudo a2disconf proto-debug`, delete the
`CustomLog` line, reload), write the five-line note, then 8.6.

```
ERR_TOO_MANY_REDIRECTS / curl (47)
 ├─ curl -sIL: is Location the same URL you requested?
 │    ├─ yes ──► the author thinks the request is not HTTPS
 │    │     ├─ Server header is the backend's ──► backend tests %{HTTPS} / $_SERVER['HTTPS']: use X-Forwarded-Proto, or remove its redirect
 │    │     └─ no backend header ──► the proxy redirects on websecure: redirect middleware on the wrong router
 │    └─ no, it alternates (www ↔ apex, /a ↔ /b) ──► two layers disagree on the canonical URL
 └─ only in the browser, curl is fine ──► cached 301, cookies, HSTS: private window, clear site data
```

**Fix & verify:** redirect owned by Traefik (or a proxy-aware Apache rule);
HTTPS answers 200; HTTP gets exactly one 301.

**Rollback:** restore `site-a.conf` from `/root/apache2.bak.*`, configtest,
reload; restore the dynamic file from your copy.

**Prevent it next time:** before any migration, grep every vhost and
`.htaccess` for redirects and rewrites (topic 2.7); decide that one layer, the
edge, owns redirects and HSTS; add `curl -sIL` checks to the verification
matrix.

### 8.6 Debrief and extensions

**Level:** [L2 · Mid] → [L3 · Senior]

The three breaks side by side. Learn the left column as reflexes:

| Break | Symptom | Who answered | Deciding evidence | Layer |
|---|---|---|---|---|
| 1 Wrong port | 502, plain `Bad Gateway` | Traefik | Access log backend URL `:8090`; refused from Traefik's namespace | Service |
| 2 Wrong Host rule | 404, plain `404 page not found` | Traefik | Routers API: rule with a typo | Router |
| 3 Redirect loop | 301 to the same URL | Apache | `server: Apache`; `xfp=https` while `%{HTTPS}` is off | Backend config |

Extensions, each tied to a topic, in rising difficulty:

| Extension | Topic | What you prove |
|---|---|---|
| Real client IPs in Apache's logs | 2.8 | `mod_remoteip` trusting only the compose subnet |
| Health check on the `apache` service | 4.4 | A dead backend becomes 503 `no available server` and shows DOWN in the API |
| TLS passthrough for site-a | 4.8 | Apache's certificate reaches the client; middlewares stop applying |
| Firewall the backend port | 7.1 | UFW on, 504 first, then a narrow rule |
| Move site-b into a container | 7.4 | Testers-only rule, switch, rollback |
| Timed cutover | 7.5 | Your outage in requests, both directions |
| Random break by a partner | 9.3 | Diagnosis from evidence only, under a timer |

Rerun all three breaks a week later with a timer: the target is each one
diagnosed in under ten minutes, using only status, body, access log and API.

Teardown: `cd ~/capstone && docker compose down`, restore Apache from
`/root/apache2.bak.*` (or simply revert to snapshot A).

---

## 9. Self-check and exit test

> 📚 **Study path:** 1) Practice: KodeKloud *Linux Challenges* (free; the scenario challenges include HTTP, database and proxy services) ([course](https://kodekloud.com/courses/linux-challenges)) · 2) Practice: SadServers scenarios tagged nginx or ssl ([sadservers.com/scenarios](https://sadservers.com/scenarios)) · 3) Note: re-read only the topics whose questions you missed (the answer key names them) · 4) Then: the Ops Ladder L3 exit test in 9.2.

Answer the questions for your stage without looking, then check the key in 9.4.
The practical tasks are the real test: do them on a VM, with a timer, and keep
the five-line note for each one in your runbook repo.

### 9.1 Questions by career stage

**[L1 · Junior]**

- **Q1.** What is the difference between a web server, an application server and a reverse proxy? Name one of each on your server.
- **Q2.** `ss -ltnp` shows `*:443` owned by apache2. Why can't a container publish 443, and which two commands prove who owns it?
- **Q3.** Where does Ubuntu's Apache keep its sites, and which command lists the vhosts that are actually live?
- **Q4.** What is the difference between `systemctl reload apache2`, `systemctl restart apache2` and `systemctl disable --now apache2`?
- **Q5.** A site returns 403 after its files moved to `/srv/site`. Name two possible causes and the command that checks each.

**[L2 · Mid]**

- **Q6.** Traefik returns 404 for one name and 502 for another. Which layer is broken in each case, and what do you check first?
- **Q7.** Why does `curl https://192.0.2.10/` prove nothing about a site's certificate? What do you run instead?
- **Q8.** A request fails with 504 after exactly 60 seconds. Which components have a 60 s default, and how do you find out which one fired?
- **Q9.** After Traefik moved in front, Apache logs show only `172.18.0.2`, and `Require ip 10.0.0.0/8` now lets everyone in. Why, and how do you fix both?
- **Q10.** A login page loops with ERR_TOO_MANY_REDIRECTS right after the migration. What is the most likely cause, and what are two fixes?
- **Q11.** nginx: `location /app` with `proxy_pass http://127.0.0.1:8000/`. What path does the backend receive for `/app/x`, and how do you fix it?
- **Q12.** Apache answers 503 for a minute after a backend restart, although the backend is already back. Why?

**[L3 · Senior]**

- **Q13.** Give two examples each of Traefik static and dynamic configuration. Which kind needs a restart?
- **Q14.** When would you choose TLS passthrough over termination during a migration, and what do you lose?
- **Q15.** A Docker Compose app's domain change in Dokploy has no effect, while an Application's change works at once. Why?
- **Q16.** Trace a request for `crm.example.com` to a Dokploy Application container: every hop, and the file or label that configures it.
- **Q17.** HTTP-01 or DNS-01: which one works for an on-prem server that the internet cannot reach, and why?
- **Q18.** Plan the cutover of three Apache vhosts to Traefik on the same host: order of operations, expected downtime, rollback trigger.

**[L4 · Lead/SRE]**

- **Q19.** Write the rollback trigger and both rollback levels for the change in question 18.
- **Q20.** Which alerts would have caught each of the three capstone breaks before a user did?
- **Q21.** A colleague proposes "two edges": Apache keeps 443 for the old sites, Traefik gets 8443 for new ones. Argue for or against it as an ADR.

### 9.2 Timed practical tasks

| Stage | Task | Time | Pass when |
|---|---|---|---|
| [L1 · Junior] | On an Apache server you have never seen, produce the inventory table: names, ports, docroot or backend, log files, certificate expiry, last request (2.12) | 20 min | Every live vhost is listed and matches `apache2ctl -S` |
| [L1 · Junior] | Move the stock Apache from 80 to 8080 and back, with backup, configtest and verification each time (2.11) | 10 min | `ss` proves each state; nothing else changed |
| [L2 · Mid] | Capstone breaks 1–3 applied by a partner in random order; diagnose from status, body, logs and API before opening any config | 10 min each | A five-line note per break with the deciding evidence |
| [L2 · Mid] | Ops Ladder L3 drill: Traefik returns 502 because of a wrong port; find and fix it from Traefik's logs alone | 10 min | Fixed without reading the dynamic file first |
| [L2 · Mid] | Put nginx in front of Apache (7.2) with real client IPs and no redirect loop | 30 min | `verify-sites.sh` green, Apache logs show the client IP |
| [L3 · Senior] | Move one capstone site into a container: testers-only rule, full switch, per-site rollback (7.4, 7.6) | 60 min | Rollback measured in seconds with zero failed requests |
| [L3 · Senior] | Ops Ladder L3 exit test: move one real Apache workload into a container behind Dokploy, built by GitLab CI and pushed to Harbor, with a written rollback you have actually tested | One weekend | Change request, verification evidence and rollback rehearsal all written down |
| [L4 · Lead/SRE] | Game day (9.3) with alerting: learn about the break from an alert, fix it, publish a one-page postmortem | 2 h | Alert fired, fix verified, postmortem with timeline, root cause and follow-ups |

### 9.3 Game day: a random break

A partner runs this on the capstone VM while you are away from the keyboard. It
applies **one** break at random and saves what it needs for the reset. You
diagnose from symptoms, logs and the API only.

> ⚠️ Test VM only. The script edits the capstone files, stops services and
> restarts Traefik. Never run it on a server anyone depends on.

```bash
#!/usr/bin/env bash
# capstone-chaos.sh: apply ONE random capstone break. TEST VM ONLY.
set -euo pipefail
cd ~/capstone
cp dynamic/apache.yml /tmp/apache.yml.before-chaos          # used by the reset below
case $((RANDOM % 5)) in
  0) sed -i 's#host.docker.internal:8080#host.docker.internal:8090#' dynamic/apache.yml ;;  # wrong port -> 502
  1) sed -i 's#site-b.example.com#site-b.exmaple.com#' dynamic/apache.yml ;;                # Host typo -> 404 for site-b
  2) sudo systemctl stop apache2 ;;                                                        # backend down -> 502
  3) docker compose stop whoami >/dev/null ;;                                              # router disappears -> 404 for whoami
  4) printf 'http:\n  broken: [\n' > dynamic/zz-broken.yml
     docker compose restart traefik >/dev/null ;;                                          # file provider fails at start -> 404 for site-a and site-b
esac
echo "One thing is broken. Start the timer."
```

Reset after the debrief:

```bash
cd ~/capstone
cp /tmp/apache.yml.before-chaos dynamic/apache.yml
rm -f dynamic/zz-broken.yml
sudo systemctl start apache2
docker compose up -d && docker compose restart traefik
```

For the L4 version, add a blackbox probe per name (expected status and
redirect) and a 5xx-rate alert per router from the access log, as described in
[Learn: performance & observability](32-learn-performance-observability.md).
You should learn about the break from the alert, not from the partner.

### 9.4 Answer key

- **A1.** A web server serves files and hands dynamic work on (Apache, nginx); an application server runs code (gunicorn, php-fpm, Node); a reverse proxy accepts clients and forwards to backends (Traefik, Apache with mod_proxy). Topic 1.1.
- **A2.** Apache's wildcard `*:443` covers every address, so any other `bind()` to 443 fails with `EADDRINUSE`. `sudo ss -ltnp 'sport = :443'` and `sudo lsof -nP -iTCP:443 -sTCP:LISTEN`. Topic 1.3.
- **A3.** `sites-available/` with symlinks in `sites-enabled/`; `sudo apache2ctl -S` lists the live vhosts, and `apache2ctl -t -D DUMP_INCLUDES` lists the live files. Topics 2.2–2.3.
- **A4.** Reload re-reads the config gracefully; restart drops connections (needed for `Listen` and MPM changes); `disable --now` stops it now and at boot. Topic 2.11.
- **A5.** No `<Directory /srv/site>` block granting access (`AH01630`; grep the vhost and `apache2.conf`), or Unix permissions on a parent directory (`AH00035`; `namei -l FILE`). Topic 2.4.
- **A6.** 404 (plain text): no router matched, so check the routers API and the Host you sent. 502: a router matched but the backend refused, so read the backend URL in the access log and test it from Traefik's namespace. Topics 4.3, 4.4, capstone 8.3–8.4.
- **A7.** Connecting to an IP sends no SNI, so you get the default certificate. Use `curl --resolve NAME:443:IP https://NAME/` or `openssl s_client -servername NAME`. Topics 1.2, 7.3.
- **A8.** nginx `proxy_read_timeout`, Traefik v3's entryPoint `readTimeout`, and an AWS ALB idle timeout (Apache's Ubuntu default is 300 s). Time the request with `curl -w`, then read each hop's log for the matching error. Topic 1.6.
- **A9.** Apache's TCP peer is now Traefik, so every request comes from a private IP inside your allow-list. Enable `mod_remoteip` trusting only the Docker subnet and log `%a`; firewall the backend port so nobody can bypass Traefik. Topics 1.5, 2.8.
- **A10.** The app or Apache tests its own HTTPS state, which is off behind a TLS-terminating proxy. Let the edge own the redirect, or test `X-Forwarded-Proto` (`SetEnvIf` for PHP apps). Topic 2.7, capstone 8.5.
- **A11.** `//x`, because `/app` is replaced by `/`. Use `location /app/` with `proxy_pass http://127.0.0.1:8000/`. Topic 3.4.
- **A12.** After a failure, mod_proxy keeps the worker in error state until `retry` (default 60 s) expires. Use `retry=0` for single-backend sites. Topics 1.1, 2.5.
- **A13.** Static: entryPoints, providers, certificate resolvers, log and access-log settings (restart needed). Dynamic: routers, services, middlewares, TLS certificates (hot reload). Topic 4.1.
- **A14.** When the backend must keep its own certificates or client-certificate authentication, or to move 443 fast without certificate work. You lose path routing, header injection, redirects and `X-Forwarded-For` (PROXY protocol replaces the last one). Topics 1.4, 4.8.
- **A15.** Compose domains become labels injected at deploy time, so they need a redeploy; Application domains are written to a dynamic file that Traefik hot-reloads. Topics 5.3–5.4.
- **A16.** DNS → host:443 → docker-proxy/DNAT → dokploy-traefik entryPoint `websecure` → router from `/etc/dokploy/traefik/dynamic/APPNAME.yml` (tls via `letsencrypt`) → service `http://APPNAME:PORT` on dokploy-network → Swarm VIP → task container. Topic 5.4.
- **A17.** DNS-01: the CA checks a TXT record through your DNS provider's API and never has to reach the server. HTTP-01 and TLS-ALPN-01 need inbound 80 or 443 from the internet. Topic 4.7.
- **A18.** Days before: inventory, internal listener added next to 80/443 and tested, routes written, rehearsal with rollback. In the window: drop `Listen 80/443`, restart Apache, start Traefik, run the matrix, watch ACME. Downtime: seconds with a ready Traefik, minutes with the Dokploy installer. Trigger: an agreed measurable condition. Topics 7.1, 7.3, 7.5.
- **A19.** Trigger, for example "any kept site failing for 15 minutes or partner API errors". Per site: point the router back at `apache-legacy`. Whole edge: stop Traefik, restore `ports.conf` and the vhosts from the backup, restart Apache, verify. Topic 7.6.
- **A20.** Break 1: blackbox probe per name expecting 200, plus a 5xx-rate alert per router. Break 2: the same probe (404). Break 3: a probe with a redirect limit, or one that expects 200 on HTTPS. Topics 4.9, 9.3, module 32.
- **A21.** Against, in most cases: non-standard ports get blocked by corporate networks and leak into URLs, cookies and CORS origins; two certificate systems; two places for redirects and HSTS. For, only as a short, time-boxed step with a written end date. One edge on 443 is the target. Topics 1.3, 6.2, [Deployment patterns](35-deployment-patterns.md).

---

## 10. Where to go next

> 📚 **Study path (after this module):** 1) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress module, Traefik on Kubernetes ([course](https://kodekloud.com/courses/kubernetes-networking)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking section, Ingress and Gateway API ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) KodeKloud: *Fundamentals of SRE* — Incident Management, for the L4 half of section 7 ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Note: the module for your stage in the table below · 5) Practice: the Ops Ladder weekly rhythm.

| If you are | Go next | Why |
|---|---|---|
| [L1 · Junior] | [Port inventory playbook](22-playbook-ports-inventory.md), then [Learn: Linux](27-learn-linux.md) services and logs | Make "which app owns which port, where are its logs" a five-minute task |
| [L2 · Mid] | [Site-down playbook](25-playbook-site-down.md) sections 6–8, then [Web, HTTP & TLS](18-web-http-tls.md) | The incident version of everything in sections 1–4 |
| [L2 · Mid] → [L3 · Senior] | [Case study 21](21-case-apache-443-dokploy.md) end to end, then [Deployment patterns](35-deployment-patterns.md) section 1 | Finish your real migration: from 81/444 to Apache fully behind Traefik |
| [L3 · Senior] | [Learn: Docker](30-learn-docker.md) (networking, Swarm), section 7 of the [containers playbook](26-playbook-containers-k8s.md) | Dokploy is Docker Swarm plus Traefik; debug it below the UI |
| [L3 · Senior] | [Learn: Kubernetes](31-learn-kubernetes.md) section 8 | Ingress and Gateway API for the CKA, with the mapping from 6.3 |
| [L3 · Senior] | [Learn: CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) | GitLab CI → Harbor → Dokploy deploys, and the change-request format for 7.5 |
| [L4 · Lead/SRE] | [Learn: performance & observability](32-learn-performance-observability.md), then [Senior architecture](39-learn-senior-architecture.md) | Alerts for the game day, then an HA edge and ADRs |
| Any stage | [Career ladder](40-career-ladder.md) and [Roadmap](34-roadmap.md) | Where this module sits in your path, and what proves you are ready for the next stage |

Keep doing the weekly rhythm from the Ops Ladder: one SadServers nginx or ssl
scenario on a workday morning, one capstone break on the weekend, and a
five-line note after every real incident. The day you can move a site behind
Traefik, break it, diagnose it from the access log and roll it back without
looking anything up, this module is done.
