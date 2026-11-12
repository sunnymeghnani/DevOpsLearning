# 35 — Deployment Patterns: Port Shifting & Beyond

This module starts from a fix you made on a real job. A client asked for a new application on a server where Apache already ran three or four sites and owned ports 80 and 443. Dokploy's Traefik needed those same two ports. You changed Apache's configuration to listen on 81 and 444, Traefik got 80 and 443, and the deployment went ahead. You also said that "all the deployment can be done like that and many more". This module takes that seriously. It documents your technique as a proper procedure, analyses honestly what it fixes and what it leaves open, shows how to finish it, and then builds a catalogue of deployment patterns and end-to-end recipes around the same question: **who owns ports 80 and 443 on this machine, and how does traffic reach everything else?**

**Who it serves, fresher to senior.** A **Fresher** [L0] learns why two programs cannot share one IP:port and how to choose a port that is genuinely free. A **Junior** [L1] repeats your 81/444 change safely: backup, every `Listen` and `VirtualHost`, configtest, verify, rollback. A **Mid-level** engineer [L2] finishes it (Traefik routes, certificates, firewall, real client IPs) and deploys apps behind a proxy without new public ports. A **Senior** [L3] picks the right pattern for each workload, says no to "just open port X" with a better design, and runs zero-downtime releases. A **Lead** [L4] turns all of it into a server convention, a PORTS.md standard and a post-deployment checklist that the whole team follows. Every section and pattern carries a tag such as [L2 · Mid]; the table in section 0 tells you where to start.

Placeholders are UPPERCASE: SITE (a hostname such as shop.example.com), HOSTIP (the server's own private address, 192.0.2.10 in the examples), PORT, APP, CONTAINER, IMAGE, TOKEN. Replace them before you run anything.

> ⚠️ Sample outputs are illustrative: Ubuntu 22.04/24.04 (Apache 2.4.52/2.4.58, curl 7.81/8.5), Docker Engine 27 or newer, Traefik v3 as installed by Dokploy. Your versions will print slightly different text. Read before you change, back up before you edit, and change one thing at a time.

The examples use the same lab as [the Apache to Dokploy case study](21-case-apache-443-dokploy.md), so you can move between the two modules without translating names.

| Name in examples | Value | What it is |
|---|---|---|
| Server | web01, 192.0.2.10 on ens18 | the on-prem Ubuntu host (HOSTIP) |
| Second address (pattern P8) | 192.0.2.11 | an extra IP on the same NIC |
| Public address | 203.0.113.10 | NAT on the edge firewall to 192.0.2.10 |
| Office / admin network | 198.51.100.0/24 | where you and the staff sit |
| Apache sites | shop.example.com (+ www), api.example.com, intranet.example.com | the three legacy workloads |
| New Dokploy app | app.example.com | the client's new application |
| Dokploy panel | port 3000 | Dokploy's own web UI |
| docker_gwbridge | 172.18.0.0/16, gateway 172.18.0.1 | the bridge Swarm-attached containers use to reach the host |
| Registry | harbor.example.com | your Harbor |

---

## 0. How to use this module

> 📚 **Study path:** 1) Note: [Case study: Apache holds 443](21-case-apache-443-dokploy.md), then [Who owns this port?](22-playbook-ports-inventory.md), because you already lived this incident and the notes give it names · 2) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *IPs and Ports* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 3) Video: KodeKloud *How Docker Networking Actually Works* (9 min, [YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Practice: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)): install Apache with two vhosts on 80/443, then try to start a Traefik container on the same ports and read the error.

**Level:** the module spans [L0 · Fresher] to [L4 · Lead]. Use the table below to pick your entry point, and skip what is tagged above your stage on a first read.

### Who this is for

You run on-prem Ubuntu servers (netplan, systemd-resolved, UFW) and some AWS, you deploy with Apache, Dokploy (Traefik v3 on Docker Swarm, the `dokploy-network` overlay), GitLab CI and Harbor, and you are working through Kubernetes for the CKA. You can already make things work. This module is about making them work **in a way you can explain, verify, document and undo**, which is the difference between a junior and a senior answer to "deploy this on our server".

| Career stage | Ops Ladder | What to master here | Sections |
|---|---|---|---|
| Fresher (0–1 yr) | [L0 · Fresher] | the four facts below; port ranges; proving a port is free; reading `ss -ltnp` | 0, 2 (ranges, Steps 1–3), 7 (Fresher questions) |
| Junior (1–2 yrs) | [L1 · Junior] | your 81/444 change done completely and reversibly; P1, P2, P10; recipe R1; running the post-deployment checklist | 1 (Steps 1–8), 2, 3 (P1, P2, P10), 4 (R1), 6 |
| Mid-level (2–4 yrs) | [L2 · Mid] | finishing the job behind Traefik; P3–P7; recipes R2–R7; answering "deploy on port X" | 1 (Steps 9–14), 3, 4, 5 |
| Senior (4–7 yrs) | [L3 · Senior] | choosing between patterns; P8, P9, P11, P12; CI/CD to Dokploy (R8); explaining trade-offs to a client | 1 (verdict), 3, 4 (R8), 5 |
| Lead / SRE (5+ yrs) | [L4 · Lead] | the port convention, PORTS.md and the checklist as team standards; reviewing other people's deployments | 2 (convention, template), 6, 7 (Lead tasks) |

### The core idea

Everything in this module follows from four facts. Read them slowly, because every pattern below is just a different answer to the questions they raise.

1. **One listening socket per IP:port.** A TCP listener is identified by protocol, local IP and local port. The kernel refuses a second `bind()` to the same combination with `EADDRINUSE` ("Address already in use"). A socket bound to the wildcard `0.0.0.0:80` (or `[::]:80`) blocks every other bind to port 80 on any IPv4 address of the host. Exceptions such as `SO_REUSEPORT` exist only for several copies of the *same* program sharing load, never for two different servers.
2. **The client picks the port, not the server.** A URL without a port means 80 for `http://` and 443 for `https://`. Browsers, phones, corporate proxies, monitoring tools and Let's Encrypt all assume those two. That is why "all the traffic hits 80 and 443": nobody types `:444`.
3. **So public web traffic needs exactly one owner of 80/443 per IP address.** Two web servers cannot both have them. One of them must own the front door and pass traffic to the other, or they must live on different IP addresses, or one of them must accept a non-standard port that users then have to type.
4. **Everything else is routing.** Once one process owns 80/443, every other application listens somewhere private (a loopback port, a Unix socket, a container port on a Docker network, a Kubernetes Service) and the owner routes to it by hostname, path or SNI.

```
                        ONE IP, ONE OWNER OF 80/443

   clients ──► 203.0.113.10:80/443 ──► [ owner: Traefik / Nginx / Apache / Ingress ]
                                              │ routes by Host, path or SNI
                     ┌────────────────────────┼─────────────────────────┐
                     ▼                        ▼                         ▼
             Apache 192.0.2.10:81     container app:8000         gunicorn 127.0.0.1:8001
             (name-based vhosts)      (dokploy-network,          or unix:/run/APP.sock
                                       no host port at all)
```

### How the module is laid out

| Section | What you get |
|---|---|
| 1 | Your 81/444 fix: why it worked, the complete procedure, what it leaves open, and how to finish it |
| 2 | How to choose a port and prove it is free, plus a PORTS.md inventory template |
| 3 | Twelve deployment patterns, each with steps, pros/cons, verify, rollback and gotchas |
| 4 | Eight end-to-end recipes on a server where Traefik/Dokploy already owns 80/443 |
| 5 | What to do when a client says "deploy it on port X" |
| 6 | The post-deployment checklist |
| 7 | Self-check questions and a practical exit test |
| 8 | Where to go next |

### The step format

Every procedure uses the same shape so you can follow it under pressure: a **Goal**, the commands, a realistic sample output, **What it means**, **Why this step (now)**, and **Next step** with explicit branches. Patterns and recipes end with a pros/cons/when-to-use table, how to **verify**, how to **roll back**, and the **gotchas** that bite people in practice.

### How to study it

Read one pattern or recipe per sitting. For each one, first say in one sentence **who owns 80/443 and how traffic reaches the app**, then do it on a lab VM (never first on a client's server), break it once on purpose (wrong port, wrong bind, firewall in the way), and fix it using only the step's **Next step** branches. Finish by writing the PORTS.md line for what you built. Section 7 has questions and timed tasks for each career stage, so you can check yourself before you rely on it at work.

---

## 1. Your fix: Apache moved to 81 and 444

> 📚 **Study path:** 1) Note: [Case study: Apache holds 443](21-case-apache-443-dokploy.md), phases 5 and 7 (the same server, the same end state) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *Apache Web Server* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · 3) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress → *Traefik Overview* ([lesson](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) for routers, services and entryPoints · 4) Docs: Apache *Virtual Host documentation* ([docs](https://httpd.apache.org/docs/2.4/vhosts/)) and Traefik *Docker and Traefik Quick Start* ([docs](https://doc.traefik.io/traefik/getting-started/docker/)) · 5) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* (32 min, [YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 6) Practice: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)): Apache with two vhosts, move it to 81/444 with Steps 1–8, then put a Traefik container in front with Steps 9–11.

**Level:** Steps 1–8 and the RHEL notes are [L1 · Junior], a careful config change with backup, test and verification · "What it leaves open" and Steps 9–14 are [L2 · Mid], because they cross layers (Docker networking, UFW, certificates, headers) · the rollback plan and the verdict are [L3 · Senior] judgement.

### What happened

The client wanted a new application deployed with Dokploy. Dokploy runs Traefik as its edge proxy, and Traefik must publish ports 80 and 443 on the host. On this server Apache already served three sites on those ports. The Dokploy installer refused to continue, or Traefik could not start, with errors like these:

```
$ sudo bash /root/dokploy-install.sh
Error: something is already running on port 80

$ docker start dokploy-traefik
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint dokploy-traefik: failed to bind host port for 0.0.0.0:80:172.18.0.3:80/tcp: address already in use
Error: failed to start containers: dokploy-traefik
```

That is the Docker Engine 28+ wording. Docker 27 and older say the same thing differently: `... Error starting userland proxy: listen tcp4 0.0.0.0:80: bind: address already in use`. Either way, the important words are `0.0.0.0:80` and `address already in use`.

```
$ sudo ss -ltnp '( sport = :80 or sport = :443 )'
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       511                 *:80               *:*      users:(("apache2",pid=1342,fd=4),("apache2",pid=1341,fd=4),("apache2",pid=1338,fd=4))
LISTEN  0       511                 *:443              *:*      users:(("apache2",pid=1342,fd=6),("apache2",pid=1341,fd=6),("apache2",pid=1338,fd=6))
```

You changed Apache to listen on 81 and 444, Apache released 80 and 443, and Traefik bound them. The new app went live.

### Why it worked

Apache does not "use" a port by magic. Its `Listen` directives (on Ubuntu, in `/etc/apache2/ports.conf`) tell the parent `apache2` process, which starts as root, which sockets to open. `Listen 80` creates a socket on `*:80` (all IPv4 and IPv6 addresses). When you changed the directives to 81 and 444 and reloaded, Apache closed its sockets on 80 and 443 and opened new ones on 81 and 444. With the wildcard sockets gone, Docker could create Traefik's published ports: a `docker-proxy` listener and DNAT rules for `0.0.0.0:80` and `0.0.0.0:443` (plus `[::]` for IPv6, and udp/443 for HTTP/3).

Dokploy needs those two ports specifically because Traefik's `web` entryPoint listens on :80 (plain HTTP, redirects, and Let's Encrypt HTTP-01 challenges, which **must** arrive on port 80) and its `websecure` entryPoint listens on :443 (HTTPS for every app with a domain). Port 3000 is Dokploy's own panel.

| | Before | After your change |
|---|---|---|
| 80/tcp | apache2 (all sites, HTTP) | Traefik (Dokploy) |
| 443/tcp | apache2 (shop, api over HTTPS) | Traefik (Dokploy) |
| 81/tcp | free | apache2 (HTTP vhosts) |
| 444/tcp | free | apache2 (HTTPS vhosts) |
| https://app.example.com | did not exist | works (Traefik → container) |
| https://shop.example.com | Apache | **Traefik answers, but has no route for it** (see "What it leaves open") |

That last row is the part this section is really about. Freeing the port was the right first move and it was fast. It is not yet a finished deployment, and the rest of this section shows the complete procedure and then how to close every gap.

### Step 1 — Back up the Apache config

**Goal:** have a complete, restorable copy of the configuration and of the current vhost map before you touch anything.

```bash
# Copy the whole tree, keeping owners, modes and symlinks (sites-enabled is symlinks)
sudo cp -a /etc/apache2 /etc/apache2.bak-$(date +%F)

# Save what Apache currently believes about its vhosts, for a before/after diff
sudo apache2ctl -S > ~/apache-vhosts-before.txt 2>&1

# Save the current listeners too
sudo ss -ltnp > ~/listeners-before.txt

ls -ld /etc/apache2.bak-*
```

```
drwxr-xr-x 8 root root 4096 Sep 28 10:02 /etc/apache2.bak-2026-09-28
```

**What it means:** the backup sits outside `/etc/apache2`, so Apache will never load it by accident. That matters: Ubuntu's `apache2.conf` includes `sites-enabled/*.conf` and `conf-enabled/*.conf`, so a copy named `shop.bak.conf` inside `sites-enabled/` would be loaded as a second, duplicate vhost. A copy named `shop.conf.bak` would not.

**Why this step (now):** every later step edits several files. If the result is wrong at 2 a.m., `cp -a` back is a ten-second rollback; reconstructing four vhosts from memory is not. If you use etckeeper or keep `/etc` in Git, commit now instead.

**Next step:** if `ls` shows the dated backup and the two `~/…-before.txt` files are not empty → Step 2. If `cp` failed (disk full, typo in the path) → fix that first and never edit without a backup ([Storage](01-storage-disk.md) if the disk is full).

### Step 2 — Find every Listen and VirtualHost

**Goal:** list every place that mentions ports 80 and 443, not just the obvious one.

```bash
# Every Listen directive Apache could load (-R follows the symlinks in *-enabled)
sudo grep -RnE '^\s*Listen\b' /etc/apache2/

# Every VirtualHost opening tag in the files Apache actually loads
sudo grep -RnE '<VirtualHost' /etc/apache2/sites-enabled/ /etc/apache2/conf-enabled/

# Apache's own view: which vhost answers on which address:port
sudo apache2ctl -S
```

```
/etc/apache2/ports.conf:5:Listen 80
/etc/apache2/ports.conf:8:	Listen 443
/etc/apache2/ports.conf:12:	Listen 443

/etc/apache2/sites-enabled/000-default.conf:1:<VirtualHost *:80>
/etc/apache2/sites-enabled/shop.example.com.conf:1:<VirtualHost *:80>
/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2:<VirtualHost *:443>
/etc/apache2/sites-enabled/api.example.com.conf:1:<VirtualHost *:80>
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2:<VirtualHost *:443>
/etc/apache2/sites-enabled/intranet.example.com.conf:1:<VirtualHost *:80>

VirtualHost configuration:
*:80                   is a NameVirtualHost
         default server web01.example.com (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost web01.example.com (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com.conf:1)
         port 80 namevhost intranet.example.com (/etc/apache2/sites-enabled/intranet.example.com.conf:1)
         port 80 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com.conf:1)
                 alias www.shop.example.com
*:443                  is a NameVirtualHost
         default server api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 443 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 443 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2)
                 alias www.shop.example.com
ServerRoot: "/etc/apache2"
Main DocumentRoot: "/var/www/html"
Main ErrorLog: "/var/log/apache2/error.log"
PidFile: "/var/run/apache2/apache2.pid"
User: name="www-data" id=33
Group: name="www-data" id=33
```

**What it means:** port 443 appears **twice** in `ports.conf` (Ubuntu ships one block for `mod_ssl` and one for `mod_gnutls`; only one of them is active, but both must change or the inactive one will bite you the day someone enables the other module). Five vhost files carry a port in their opening tag. The `-le-ssl.conf` files were created by certbot. `intranet` has no HTTPS vhost. The `default server` lines matter: they answer any request whose Host header matches no `ServerName` or `ServerAlias` on that address:port. Also look for IP-based tags such as `<VirtualHost 192.0.2.10:80>` and `<VirtualHost _default_:443>` (Ubuntu's `default-ssl.conf` has used `_default_:443` for years; newer packages may say `*:443`, so check yours with `grep -n VirtualHost /etc/apache2/sites-available/default-ssl.conf`); they need the same change if enabled.

**Why this step (now):** the comment at the top of Ubuntu's own `ports.conf` warns that changing `Listen` usually means changing the `VirtualHost` statements too. People who edit only `ports.conf` get a server that passes `configtest` and serves the wrong site. You need the full list before you edit.

**Next step:** if you found only the expected files → Step 3. If you find `Listen` lines in `sites-enabled` or `conf-enabled` (some vendors put them there), add those files to the edit list in Step 3.

### Step 3 — Change Listen in ports.conf

**Goal:** make Apache open 81 and 444 instead of 80 and 443.

```bash
sudoedit /etc/apache2/ports.conf
diff -u /etc/apache2.bak-$(date +%F)/ports.conf /etc/apache2/ports.conf
```

```
--- /etc/apache2.bak-2026-09-28/ports.conf
+++ /etc/apache2/ports.conf
@@ -2,12 +2,12 @@
 # have to change the VirtualHost statement in
 # /etc/apache2/sites-enabled/000-default.conf

-Listen 80
+Listen 81

 <IfModule ssl_module>
-	Listen 443
+	Listen 444 https
 </IfModule>

 <IfModule mod_gnutls.c>
-	Listen 443
+	Listen 444 https
 </IfModule>
```

**What it means:** `Listen 81` opens `*:81`. The optional second argument `https` on `Listen 444 https` tells Apache which protocol that socket speaks. Apache assumes `https` only for port 443 and `http` for every other port, and the Apache documentation recommends naming the protocol whenever you run HTTPS on a non-standard port. If Traefik will be the only client of Apache (Option B below), you can later drop the 444 listener entirely; keep it for now so nothing breaks during the change.

**Why this step (now):** this is the change that actually frees 80/443. You make it together with Step 4 before any reload, because `Listen` and `VirtualHost` ports must agree at the moment Apache re-reads the config.

**Next step:** → Step 4 (do not reload yet). If Step 2 found `Listen` lines outside `ports.conf`, change them now in the same editing session; if you are unsure whether a module block is active, change it anyway (an inactive block costs nothing).

### Step 4 — Change every VirtualHost port

**Goal:** every vhost that said `*:80` must now say `*:81`, and every `*:443` (or `_default_:443`) must say `*:444`.

```bash
# Edit the REAL files in sites-available. sites-enabled holds symlinks, and
# "sed -i" on a symlink replaces the link with a regular file (the site then
# silently stops tracking sites-available).
cd /etc/apache2/sites-available
sudo sed -i -E 's/(<VirtualHost[^>]*):80>/\1:81>/; s/(<VirtualHost[^>]*):443>/\1:444>/' \
    000-default.conf shop.example.com.conf shop.example.com-le-ssl.conf \
    api.example.com.conf api.example.com-le-ssl.conf intranet.example.com.conf

# Confirm: nothing should still say :80> or :443>
sudo grep -RnE '<VirtualHost[^>]*:(80|443)>' /etc/apache2/sites-enabled/ || echo "no old ports left"
sudo grep -RnE '<VirtualHost' /etc/apache2/sites-enabled/
```

```
no old ports left
/etc/apache2/sites-enabled/000-default.conf:1:<VirtualHost *:81>
/etc/apache2/sites-enabled/shop.example.com.conf:1:<VirtualHost *:81>
/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2:<VirtualHost *:444>
/etc/apache2/sites-enabled/api.example.com.conf:1:<VirtualHost *:81>
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2:<VirtualHost *:444>
/etc/apache2/sites-enabled/intranet.example.com.conf:1:<VirtualHost *:81>
```

**What it means:** listeners and vhosts now agree. Here is what happens if you skip this step, because it is the most common half-done version of your fix: Apache listens on 81 and 444, but no vhost is defined for those ports. A request arriving on 81 matches no `VirtualHost`, so the **main server** configuration answers it (on Ubuntu that is the "Apache2 Ubuntu Default Page" from `/var/www/html`, or nothing useful). A request on 444 also lands on the main server, which has no `SSLEngine on`, so Apache speaks **plain HTTP on the "HTTPS" port** and clients fail with `curl: (35) ... wrong version number`. `apache2ctl configtest` still prints `Syntax OK` in that state, which is why it fools people.

**Why this step (now):** it must happen before the reload in Step 7 so Apache never runs with mismatched ports, not even for a few seconds.

**Next step:** → Step 5. If the grep still finds `:80>` or `:443>`, edit those files by hand; a tag like `<VirtualHost *:80 *:8080>` needs a human, not a regex.

### Step 5 — Fix redirects and rewrites

**Goal:** find every rule that hard-codes a port or forces HTTPS, and decide what it should do in the new layout.

```bash
# Rules in the vhost and conf files
sudo grep -RnE 'Rewrite(Rule|Cond)|Redirect|:80\b|:443\b|ServerName .*:[0-9]|UseCanonical' \
    /etc/apache2/sites-available/ /etc/apache2/conf-available/

# Rules hidden in the applications' .htaccess files
sudo grep -RnE 'SERVER_PORT|HTTPS|https://' /var/www/*/.htaccess /var/www/*/public/.htaccess 2>/dev/null
```

```
/etc/apache2/sites-available/shop.example.com.conf:12:RewriteEngine on
/etc/apache2/sites-available/shop.example.com.conf:13:RewriteCond %{SERVER_NAME} =www.shop.example.com [OR]
/etc/apache2/sites-available/shop.example.com.conf:14:RewriteCond %{SERVER_NAME} =shop.example.com
/etc/apache2/sites-available/shop.example.com.conf:15:RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
/etc/apache2/sites-available/api.example.com.conf:9:Redirect permanent / https://api.example.com/
/var/www/shop/.htaccess:4:RewriteCond %{SERVER_PORT} 80
/var/www/shop/.htaccess:5:RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
```

**What it means:** three kinds of rule, three problems.

- The certbot rules (lines 12–15) redirect every HTTP request to `https://SITE/` with **no port**. After your change that URL lands on Traefik, not on Apache.
- `Redirect permanent / https://api.example.com/` does the same unconditionally.
- The `.htaccess` rule only fires when `SERVER_PORT` is 80, which is now never true, so the old "force HTTPS" logic silently stopped working.

What the rules should do depends on how users will reach the sites (see "What it leaves open"). For the recommended design, where Traefik terminates HTTPS and talks plain HTTP to Apache on 81, Apache should redirect **only when the original client request was HTTP**, which Traefik tells it through the `X-Forwarded-Proto` header:

```apache
# In shop.example.com.conf (the *:81 vhost), replacing certbot's three lines
RewriteEngine on
# Traefik sets X-Forwarded-Proto: https for requests that arrived on 443.
# Redirect only real plain-HTTP requests, otherwise Traefik → Apache → redirect → Traefik loops forever.
RewriteCond %{HTTP:X-Forwarded-Proto} !=https
RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]

# Let PHP and other CGI-style apps know the client used HTTPS
SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on
```

**Why this step (now):** a wrong redirect is invisible in `configtest` and only shows up as `ERR_TOO_MANY_REDIRECTS` in a user's browser. Fixing it while you are already editing vhosts costs a minute. `%{SERVER_NAME}` is used on purpose: it carries no port, while `%{HTTP_HOST}` would carry `:81` for anyone who reached Apache directly.

**Next step:** → Step 6. If an application generates absolute URLs itself (WordPress `siteurl`, Laravel `APP_URL`, Django `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`), note them now; they are covered under "What it leaves open".

### Step 6 — Test the configuration

**Goal:** prove the new config parses and that every vhost sits on the new ports before Apache loads it.

```bash
sudo apache2ctl configtest
sudo apache2ctl -S 2>&1 | head -16
```

```
Syntax OK
VirtualHost configuration:
*:81                   is a NameVirtualHost
         default server web01.example.com (/etc/apache2/sites-enabled/000-default.conf:1)
         port 81 namevhost web01.example.com (/etc/apache2/sites-enabled/000-default.conf:1)
         port 81 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com.conf:1)
         port 81 namevhost intranet.example.com (/etc/apache2/sites-enabled/intranet.example.com.conf:1)
         port 81 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com.conf:1)
                 alias www.shop.example.com
*:444                  is a NameVirtualHost
         default server api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 444 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
         port 444 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2)
                 alias www.shop.example.com
ServerRoot: "/etc/apache2"
```

**What it means:** `Syntax OK` proves the files parse. The `-S` map is the real check: every name you saw in Step 2 now appears under `*:81` or `*:444`, and no `*:80` or `*:443` block remains. Compare it with `~/apache-vhosts-before.txt`; the only differences should be the port numbers.

**Why this step (now):** `systemctl reload` with a broken config leaves the old config running on Ubuntu (the reload fails), but a later reboot or restart would take Apache down completely. Test first, always.

**Next step:** if `Syntax OK` and the map is right → Step 7. If you see `AH00526: Syntax error` → fix the file and line it names, then repeat Step 6.

### Step 7 — Reload Apache

**Goal:** apply the change with the smallest possible interruption.

```bash
sudo systemctl reload apache2
systemctl status apache2 --no-pager | head -12
sudo journalctl -u apache2 --since '5 min ago' --no-pager | tail -5
```

```
● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-28 06:11:02 UTC; 4h 5min ago
       Docs: https://httpd.apache.org/docs/2.4/
    Process: 47088 ExecReload=/usr/sbin/apachectl graceful (code=exited, status=0/SUCCESS)
   Main PID: 1338 (apache2)
      Tasks: 55 (limit: 9387)
     Memory: 21.4M (peak: 38.9M)
        CPU: 4.112s
     CGroup: /system.slice/apache2.service
             ├─ 1338 /usr/sbin/apache2 -k start
             ├─47101 /usr/sbin/apache2 -k start

Sep 28 10:16:44 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Sep 28 10:16:44 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.
```

**What it means:** Ubuntu's reload is `apachectl graceful`: the root parent re-reads the config, opens the new listeners, closes the ones no longer configured, and replaces the workers without dropping requests in flight. If `ss` in Step 8 still shows Apache on 80, do a full `sudo systemctl restart apache2` (a second or two of downtime).

**Why this step (now):** only now are the files consistent and tested. As soon as Apache lets go of 80/443, Dokploy's Traefik can bind them. Do not wait for it to appear by itself: current Dokploy installs run Traefik as a plain container (`docker run --restart always`), and Docker does not retry a container whose **start** failed at port binding, restart policy or not. Check `docker ps -a --filter name=dokploy-traefik`; if it shows `Created` or `Exited`, run `docker start dokploy-traefik`. (Only older installs that ran Traefik as a Swarm service retry on their own.)

**Next step:** → Step 8. If the reload fails, `journalctl -u apache2` shows why; the usual one is `(98)Address already in use: AH00072: make_sock: could not bind to address [::]:81`, meaning something already owns 81 (go to [Who owns this port?](22-playbook-ports-inventory.md) and pick another port).

### Step 8 — Verify sockets and each site

**Goal:** prove who owns which port, and that every Apache site answers on its new port with the right content and certificate.

```bash
# Who owns the four ports now?
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :81 or sport = :444 )'

# Plain HTTP vhost on 81: the Host header picks the vhost
curl -sv -o /dev/null -H 'Host: shop.example.com' http://127.0.0.1:81/

# HTTPS vhost on 444, the quick way (no SNI is sent to an IP literal)
curl -vk -o /dev/null -H 'Host: shop.example.com' https://127.0.0.1:444/

# HTTPS vhost on 444, the correct way: --resolve sends proper SNI AND Host
curl -v -o /dev/null --resolve shop.example.com:444:127.0.0.1 https://shop.example.com:444/
```

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       4096          0.0.0.0:80         0.0.0.0:*      users:(("docker-proxy",pid=48211,fd=7))
LISTEN  0       4096          0.0.0.0:443        0.0.0.0:*      users:(("docker-proxy",pid=48236,fd=7))
LISTEN  0       511                 *:81               *:*      users:(("apache2",pid=47102,fd=3),("apache2",pid=47101,fd=3),("apache2",pid=1338,fd=3))
LISTEN  0       511                 *:444              *:*      users:(("apache2",pid=47102,fd=4),("apache2",pid=47101,fd=4),("apache2",pid=1338,fd=4))
LISTEN  0       4096             [::]:80            [::]:*      users:(("docker-proxy",pid=48218,fd=7))
LISTEN  0       4096             [::]:443           [::]:*      users:(("docker-proxy",pid=48243,fd=7))

*   Trying 127.0.0.1:81...
* Connected to 127.0.0.1 (127.0.0.1) port 81
> GET / HTTP/1.1
> Host: shop.example.com
>
< HTTP/1.1 301 Moved Permanently
< Server: Apache/2.4.58 (Ubuntu)
< Location: https://shop.example.com/

*   Trying 127.0.0.1:444...
* Connected to 127.0.0.1 (127.0.0.1) port 444
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519 / RSASSA-PSS
* Server certificate:
*  subject: CN=api.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
> GET / HTTP/1.1
> Host: shop.example.com
< HTTP/1.1 200 OK
< Server: Apache/2.4.58 (Ubuntu)

* Connected to shop.example.com (127.0.0.1) port 444
*  subject: CN=shop.example.com
*  SSL certificate verify ok.
< HTTP/1.1 200 OK
```

**What it means:**

- `docker-proxy` (Traefik's published ports) owns 80/443, `apache2` owns 81/444. The port swap itself is done.
- The first curl shows the redirect issue from Step 5 in action if you have not fixed it yet: Apache on 81 redirects to `https://shop.example.com/` with no port, which is Traefik.
- The second curl is the quick test from many guides. Notice the certificate is `CN=api.example.com`: curl sends **no SNI** for an IP literal, so Apache used the default `*:444` vhost's certificate for the handshake and only then picked the vhost by Host header. It is fine for "is it alive", misleading for "is the right cert served".
- The third curl uses `--resolve`, which sends the real name in SNI and Host while still connecting to 127.0.0.1. That is the test that matches what a browser does. Use it.

**Why this step (now):** "Apache reloaded" is not proof. The socket table proves ownership; the curls prove each vhost and certificate. You do it from the server first because it removes DNS, firewall and NAT from the picture; from outside comes later.

**Next step:** if all sites answer correctly → read "What it leaves open", then finish with Steps 9–14. If a site shows the Ubuntu default page → its vhost port was missed (back to Step 4). If curl fails with `wrong version number` on 444 → no `*:444` vhost with `SSLEngine on` matched (Step 4). On RHEL or Rocky, read the next section first.

### RHEL and Rocky differences

**Goal:** the same change on a RHEL-family server, where both the file layout and SELinux differ.

```bash
# Where are the Listen lines and vhosts on RHEL/Rocky/Alma?
sudo grep -RnE '^\s*Listen\b' /etc/httpd/conf/httpd.conf /etc/httpd/conf.d/
sudo httpd -S

# Which ports may httpd bind under SELinux?
sudo semanage port -l | grep http_port_t
```

```
/etc/httpd/conf/httpd.conf:47:Listen 80
/etc/httpd/conf.d/ssl.conf:5:Listen 443 https

http_port_t                    tcp      80, 81, 443, 488, 8008, 8009, 8443, 9000
pegasus_http_port_t            tcp      5988
```

**What it means:** on RHEL the HTTP `Listen` is in `/etc/httpd/conf/httpd.conf`, the HTTPS one in `/etc/httpd/conf.d/ssl.conf` (which also holds a `_default_:443` vhost), and your vhosts live in `/etc/httpd/conf.d/*.conf`. SELinux only lets the `httpd_t` domain bind ports labelled `http_port_t`. **81 is already in that list; 444 is not.** Without a label change, httpd fails to start:

```
$ sudo journalctl -u httpd -n 5 --no-pager
httpd[4121]: (13)Permission denied: AH00072: make_sock: could not bind to address [::]:444
httpd[4121]: (13)Permission denied: AH00072: make_sock: could not bind to address 0.0.0.0:444
httpd[4121]: no listening sockets available, shutting down
httpd[4121]: AH00015: Unable to open logs
systemd[1]: httpd.service: Main process exited, code=exited, status=1/FAILURE
```

```bash
# Label 444 for httpd (use -m instead of -a if semanage says the port is already defined)
sudo semanage port -a -t http_port_t -p tcp 444
sudo semanage port -l | grep -w http_port_t

# firewalld instead of UFW; open a port ONLY if clients must reach it directly
sudo firewall-cmd --list-all
```

**Why this step (now):** "Permission denied" on a port above 1023 or on a non-standard low port is almost always SELinux, not file permissions, and `setenforce 0` is the wrong fix (it disables protection for the whole host). Labelling the one port is the narrow, permanent fix. Other differences to remember: service `httpd` (not `apache2`), logs in `/var/log/httpd/`, config test `sudo apachectl configtest`, and no `a2ensite`/`a2enmod` (you include files directly).

**Next step:** → "What it leaves open", same as Ubuntu.

### What it leaves open

Moving Apache freed 80/443 for Dokploy. It did not decide how the three Apache sites are reached now, and a few other things quietly changed with it. Work through this checklist; every row has a fix later in this section.

| # | Open question | What you see if you ignore it | Fix |
|---|---|---|---|
| 1 | How do users reach shop, api and intranet now? | `https://shop.example.com` shows Traefik's `404 page not found` and the `TRAEFIK DEFAULT CERT` warning | Option B: Traefik routes those names to Apache (Steps 9–11) |
| 2 | Certificate renewal for the Apache sites | `certbot renew` fails; certificates expire in ≤ 90 days | Step 12 |
| 3 | Firewall exposure of 81 and 444 | sites reachable on odd ports, bypassing Traefik and its logs | Step 13 |
| 4 | Bind address Traefik can reach | Traefik `502 Bad Gateway` or a timeout to Apache | Step 9 |
| 5 | Real client IPs | every Apache log line shows 172.18.0.x; `Require ip` allow-lists and fail2ban break | Step 14 |
| 6 | Redirect loops | `ERR_TOO_MANY_REDIRECTS` | Step 5 and `X-Forwarded-Proto` |
| 7 | Double TLS between Traefik and Apache | 502 with a TLS verification error in Traefik's log | "Double TLS or plain HTTP inside" |
| 8 | Port choice | a future service collides with 81 or 444 | "Was 81 and 444 a good choice" and section 2 |
| 9 | Documentation | in six months nobody knows why Apache is on 81 | PORTS.md (section 2) |

### Option A: users type port 444

If you do nothing else, the only way to reach the Apache sites is `https://shop.example.com:444/`. That works on your laptop, but it is a poor answer for public websites:

- **Many networks block it.** Corporate firewalls, guest Wi-Fi and some mobile carriers allow only 80 and 443 outbound. Users there get a timeout, not an error page.
- **Every link breaks.** Bookmarks, search results, emails and QR codes point to `https://shop.example.com/`, which is now Traefik.
- **Apps generate URLs without the port.** WordPress redirects to its `siteurl` (no port), Laravel uses `APP_URL`, many apps build links from configuration. Users bounce from :444 to :443 and land on Traefik's 404.
- **Origins include the port.** The browser treats `https://shop.example.com` and `https://shop.example.com:444` as different origins, so CORS, CSP and OAuth redirect URIs registered without the port stop matching.
- **Cookies do not include the port.** The reverse problem: two apps on the same hostname but different ports see each other's cookies, so a session cookie called `session` can collide.
- **HSTS.** If the site ever sent `Strict-Transport-Security`, browsers rewrite `http://shop.example.com:81/` to `https://shop.example.com:81/` and fail, because 81 speaks plain HTTP.
- **Let's Encrypt cannot validate on 81 or 444.** HTTP-01 always connects to port 80 and TLS-ALPN-01 always to port 443.

Option A is acceptable for an internal admin tool used by three people on the LAN (pattern P1). It is not a finish for public sites.

### Option B: Traefik routes to Apache

This is the recommended finish and the same end state as [the case study](21-case-apache-443-dokploy.md): Traefik owns 80/443 for **every** hostname on the server, terminates TLS, and forwards the Apache hostnames to Apache over plain HTTP on the private hop. Apache keeps doing what it is good at (name-based vhosts, `.htaccess`, PHP) without owning the front door.

```
 Internet ──► 203.0.113.10 (edge NAT) ──► 192.0.2.10:80/443  dokploy-traefik
                                              │
                ┌─────────────────────────────┼──────────────────────────────┐
                ▼                             ▼                              ▼
   Host(app.example.com)          Host(shop|www.shop|api)          Host(intranet) + ipAllowList
   → Dokploy app container        → http://192.0.2.10:81           → http://192.0.2.10:81
     on dokploy-network             Apache picks the vhost           (office range only)
                                    by the Host header
```

Why it is better: one place for certificates, one place for access logs and redirects, standard URLs for users, and Apache's ports no longer need to be open to anyone except Traefik. The cost is one dynamic config file and a firewall rule.

A third option exists: keep Apache on 80/443 in front and run Traefik on internal ports behind it. It works, but it fights Dokploy (which expects to manage certificates and the edge), so the case study rejects it; read its analysis before choosing it.

### The certificate trap

Your Apache certificates came from certbot. Renewal needs a challenge, and the challenges are bound to fixed ports: **HTTP-01 always connects to port 80, TLS-ALPN-01 always to port 443.** Both now belong to Traefik. The next renewal (certbot tries when a certificate has fewer than 30 days left) will fail like this:

```
$ sudo certbot renew --dry-run
Saving debug log to /var/log/letsencrypt/letsencrypt.log

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Processing /etc/letsencrypt/renewal/shop.example.com.conf
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Simulating renewal of an existing certificate for shop.example.com and www.shop.example.com
Failed to renew certificate shop.example.com with error: Unable to find a virtual host listening on port 80 which is currently needed for Certbot to prove to the CA that you control your domain. Please add a virtual host for port 80.
```

With certbot's `apache` authenticator (what `certbot --apache` set up) the renewal stops before Let's Encrypt is even asked: the plugin needs a vhost on port 80 and every vhost is now on 81. If you switch the renewal to `--webroot`, or put a port-80 vhost back, the CA does connect to port 80 and you get the other classic failure instead: `Type: unauthorized` with `Detail: 203.0.113.10: Invalid response from http://shop.example.com/.well-known/acme-challenge/...: 404`. That 404 comes from Traefik: Let's Encrypt asked port 80 for a file that only Apache knows about. You have three ways out.

| Option | How | Pros | Cons |
|---|---|---|---|
| 1. Traefik issues the certificates (recommended with Option B) | `tls.certResolver` on each Apache router; Apache serves plain HTTP on 81 | no certbot left for these names, one renewal mechanism, nothing to remember | Apache's own certificates become unused; retire them cleanly (Step 12) |
| 2. Forward the ACME path to Apache | a Traefik router on `web` for the challenge path of those hosts → Apache:81; certbot switched to `--webroot` | Apache keeps its own certificates (needed if you keep direct :444 access or TLS passthrough, pattern P9) | **does not work behind Dokploy's Traefik as installed**: its `letsencrypt` resolver uses HTTP-01 on `web`, and Traefik v3's internal `acme-http@internal` router has the highest possible priority for `/.well-known/acme-challenge/`, so it answers (with 404 for tokens it does not know) before your router is ever consulted (Traefik GitHub issue 10861). Only consider it on a Traefik with no HTTP-01 resolver on that entryPoint; otherwise use option 1 or 3 |
| 3. DNS-01 | a certbot DNS plugin (RFC 2136 for an on-prem BIND, or your DNS provider's plugin) | needs no port at all; works for internal-only names; wildcards possible | DNS API credentials must live on the server; more moving parts |

### Double TLS or plain HTTP inside

If Traefik forwards to `https://192.0.2.10:444`, there are two TLS sessions: client to Traefik and Traefik to Apache. That is allowed, but it adds failure modes. Traefik verifies the backend certificate by default: it connects to an IP address, so the name does not match, and when the Apache certificate expires (see the trap above) every request becomes a 502. If you truly need encryption on the hop (a compliance rule, or Apache on another host across an untrusted network), give Traefik a servers transport that sends the right SNI:

```yaml
# Only if the hop between Traefik and Apache must be encrypted
http:
  serversTransports:
    apache-tls:
      serverName: shop.example.com      # SNI and name check against Apache's cert
      # insecureSkipVerify: true        # last resort for a self-signed backend cert
  services:
    shop-apache-tls:
      loadBalancer:
        serversTransport: apache-tls
        servers:
          - url: "https://192.0.2.10:444"
```

On the same host, the hop never leaves the machine's kernel, so plain HTTP to port 81 is the simpler and more robust choice. The price is that Apache no longer sees HTTPS directly, which is why Step 5 taught it to trust `X-Forwarded-Proto` for redirects and the `HTTPS` variable.

### Was 81 and 444 a good choice

Mostly yes, and it is worth knowing why so you can defend it.

- **81 is a good internal HTTP port.** It is below 1024, so only root (or a process with `CAP_NET_BIND_SERVICE`) can bind it, which means no unprivileged process can grab it while Apache is down. It is already in SELinux's `http_port_t`. It is not assigned to anything common in `/etc/services`.
- **444 is acceptable but usually unnecessary.** It is registered to `snpp` (Simple Network Paging Protocol, practically unused), it needs an SELinux label on RHEL, and with Option B nothing needs HTTPS on Apache at all.
- **8080/8443 are the "conventional" alternatives and collide more often**: Tomcat, Jenkins, many container images and Traefik's own dashboard (which Dokploy can publish on 8080) default to them. The case study uses 8081 bound to the host IP for the same reason you picked 81: it avoids 8080.
- **Never pick a port in the ephemeral range** (`net.ipv4.ip_local_port_range`, 32768–60999 by default on Ubuntu). The kernel hands those out as source ports for outgoing connections, so your service can randomly fail to start with "Address already in use". Section 2 has the full rules.

### Finish the job: overview

Steps 9–14 turn the port swap into a complete, documented deployment using Option B. Do them in order; each one is safe to stop after.

| Step | Result |
|---|---|
| 9 | Apache reachable from the Traefik container, not from the internet |
| 10 | A Traefik dynamic file routes the Apache hostnames to Apache:81 with Let's Encrypt certificates |
| 11 | Tested with `curl --resolve` before anything depends on it |
| 12 | Certificate renewal no longer depends on certbot for those names |
| 13 | 81 and 444 closed from outside |
| 14 | Real client IPs back in Apache's logs |

### Step 9 — Let Traefik reach Apache

**Goal:** Apache's port 81 must be reachable from inside the Traefik container, and nowhere else.

```bash
# Which address does Apache listen on? (*:81 = all addresses, which includes 192.0.2.10)
sudo ss -ltnp 'sport = :81'

# Try Apache from INSIDE Traefik's network namespace (netshoot borrows it; Traefik is untouched)
docker run --rm --net container:dokploy-traefik nicolaka/netshoot \
    curl -sS -m 5 -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.10:81/

# Is UFW active, and does it allow anything on 81?
sudo ufw status verbose | head -8
ip -br addr show docker_gwbridge
```

```
LISTEN 0      511                *:81              *:*    users:(("apache2",pid=47102,fd=3),...)

curl: (28) Connection timed out after 5002 milliseconds

Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

docker_gwbridge  UP  172.18.0.1/16 fe80::42:9cff:fe1a:2b3c/64
```

**What it means:** Apache listens on every address, but the Traefik container cannot reach it. The container is on the `dokploy-network` overlay and reaches the host through `docker_gwbridge`, so its packets arrive at the host's INPUT chain from 172.18.0.x on interface `docker_gwbridge`. UFW's default `deny (incoming)` drops them, hence the timeout. This surprises people because they remember that Docker bypasses UFW; that is only true for traffic **to published container ports**. Traffic **from** a container **to a host process** such as Apache goes through UFW like any other incoming packet.

Your bind-address options:

| Apache listens on | Can Traefik (in a container) reach it? | Verdict |
|---|---|---|
| `127.0.0.1:81` | No. Inside the container 127.0.0.1 is the container itself | wrong for this design |
| `*:81` or `192.0.2.10:81` | Yes, once the firewall allows the Docker bridge | **use this** + UFW rule below |
| `172.18.0.1:81` (the bridge gateway) | Yes | fragile: Apache fails at boot if Docker has not created the bridge yet |
| `host.docker.internal` / `host-gateway` | only if the container was started with that extra host, which Dokploy's Traefik is not | not available without changing Dokploy's container |

```bash
# Allow only the Docker bridge to reach Apache's internal port
sudo ufw allow in on docker_gwbridge to any port 81 proto tcp comment 'Traefik -> Apache'

# Re-test from inside Traefik's namespace
docker run --rm --net container:dokploy-traefik nicolaka/netshoot \
    curl -sS -m 5 -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.10:81/
```

```
Rule added
Rule added (v6)
301
```

**Why this step (now):** a route in Traefik is useless if the packets cannot arrive. Testing from Traefik's own network namespace removes every guess: it is exactly the path Traefik will use. (If the server has no internet access to pull `nicolaka/netshoot`, push it to Harbor once and pull it from there.)

**Next step:** if you get an HTTP code (301 here, because of the redirect from Step 5 that only fires for non-HTTPS requests) → Step 10. If `Connection refused` → Apache is not listening on that address (check `ss`). If it still times out → check that the rule landed on the right interface (`sudo ufw status numbered`) and that no edge firewall sits between them (there should not be on one host).

### Step 10 — Add a Traefik route per Apache site

**Goal:** a dynamic configuration file that tells Traefik "these hostnames go to Apache on 192.0.2.10:81, with Let's Encrypt certificates".

```bash
# Where does Dokploy's Traefik read its config from? (verify on YOUR server)
docker inspect dokploy-traefik --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# The file provider directory and the certificate resolver name
sudo grep -nA3 '^\s*file:' /etc/dokploy/traefik/traefik.yml
sudo grep -nA6 '^certificatesResolvers' /etc/dokploy/traefik/traefik.yml
sudo ls -l /etc/dokploy/traefik/dynamic/
```

```
/etc/dokploy/traefik/traefik.yml -> /etc/traefik/traefik.yml
/etc/dokploy/traefik/dynamic -> /etc/dokploy/traefik/dynamic
/var/run/docker.sock -> /var/run/docker.sock

14:  file:
15-    directory: /etc/dokploy/traefik/dynamic
16-    watch: true

30:certificatesResolvers:
31-  letsencrypt:
32-    acme:
33-      email: ops@example.com
34-      storage: /etc/dokploy/traefik/dynamic/acme.json
35-      httpChallenge:
36-        entryPoint: web

-rw------- 1 root root 48211 Sep 28 10:30 acme.json
-rw-r--r-- 1 root root  1203 Sep 21 14:02 dokploy.yml
-rw-r--r-- 1 root root   148 Sep 21 14:02 middlewares.yml
```

**What it means:** on current Dokploy installs the host directory `/etc/dokploy/traefik/dynamic` is mounted into Traefik at the same path and watched by the file provider, so any valid `.yml` file you drop there is loaded within seconds without a restart. The resolver is called `letsencrypt` and uses HTTP-01 on the `web` entryPoint. Treat these paths and names as **to be verified**: older Dokploy versions differed, which is why you read them from `docker inspect` and the static config instead of trusting this page.

Now write the route file. Write it somewhere harmless first and validate it, because a YAML error in one file can make Traefik reject the update for the whole folder, including Dokploy's own routes.

```yaml
# /etc/dokploy/traefik/dynamic/legacy-apache.yml
# Legacy Apache sites behind Traefik. Apache: http://192.0.2.10:81 (plain HTTP, firewalled to Docker).
# Owner: ops@example.com. See PORTS.md on web01.
http:
  middlewares:
    legacy-apache-https:
      redirectScheme:
        scheme: https
        permanent: true
    legacy-apache-office-only:
      ipAllowList:
        sourceRange:
          - "198.51.100.0/24"

  routers:
    # Port 80: send every legacy hostname to HTTPS (ACME challenges are still answered by Traefik)
    legacy-apache-http:
      entryPoints:
        - web
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`) || Host(`api.example.com`) || Host(`intranet.example.com`)"
      middlewares:
        - legacy-apache-https
      service: legacy-apache

    # Port 443: one router per site, so each gets its own certificate
    shop-apache:
      entryPoints:
        - websecure
      rule: "Host(`shop.example.com`) || Host(`www.shop.example.com`)"
      service: legacy-apache
      tls:
        certResolver: letsencrypt
    api-apache:
      entryPoints:
        - websecure
      rule: "Host(`api.example.com`)"
      service: legacy-apache
      tls:
        certResolver: letsencrypt
    intranet-apache:
      entryPoints:
        - websecure
      rule: "Host(`intranet.example.com`)"
      middlewares:
        - legacy-apache-office-only
      service: legacy-apache
      tls:
        certResolver: letsencrypt

  services:
    legacy-apache:
      loadBalancer:
        passHostHeader: true          # Apache needs the original Host to pick the vhost
        servers:
          - url: "http://192.0.2.10:81"
```

```bash
sudo install -m 600 /dev/null /root/legacy-apache.yml
sudoedit /root/legacy-apache.yml                       # paste the YAML above
sudo python3 -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' /root/legacy-apache.yml && echo "YAML OK"
sudo install -m 644 /root/legacy-apache.yml /etc/dokploy/traefik/dynamic/legacy-apache.yml
sleep 3; docker logs --since 1m dokploy-traefik 2>&1 | tail -20
```

```
YAML OK
```

**What it means:** "YAML OK" and an empty or quiet Traefik log mean the file loaded. A broken file shows up as a line like `ERR Error occurred during watcher callback error="/etc/dokploy/traefik/dynamic/legacy-apache.yml: yaml: line 21: did not find expected key" providerName=file`; fix it at once, since Traefik keeps running on the last good configuration but stops picking up file changes until you do. Design notes: one service for all Apache sites is enough, because Apache itself picks the vhost from the Host header that Traefik passes through. Traefik v3's `Host()` matcher takes exactly one name, so several names are joined with `||`. `ipAllowList` is the v3 name of the old `ipWhiteList`.

**Why this step (now):** with Step 9 done, the path exists; this step gives Traefik the instruction to use it. It touches nothing Dokploy manages: your file is separate, so removing it is a complete rollback.

**Next step:** → Step 11. If `intranet.example.com` has no public DNS record, Let's Encrypt cannot validate it with HTTP-01; give that router a certificate from DNS-01 or your internal CA, or leave intranet out for now.

### Step 11 — Test through Traefik with curl --resolve

**Goal:** prove each hostname reaches the right Apache vhost through Traefik, with a valid certificate, before you rely on it.

```bash
# HTTPS through Traefik, pinned to this server, with correct SNI and Host
curl -sv -o /dev/null --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/ 2>&1 \
    | grep -E '^\* +(subject|issuer)|^< (HTTP|server|location)'

# HTTP on port 80 should redirect to HTTPS
curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' --resolve shop.example.com:80:192.0.2.10 http://shop.example.com/

# Did Traefik get the certificate? (look for errors, not for success lines)
docker logs --since 10m dokploy-traefik 2>&1 | grep -iE 'acme|certificate' | tail -5
```

```
*  subject: CN=shop.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
< HTTP/2 200
< server: Apache/2.4.58 (Ubuntu)

301 -> https://shop.example.com/
```

**What it means:** Traefik terminated TLS with its own Let's Encrypt certificate (issued within a minute of loading the file, because DNS already pointed here), then forwarded to Apache, whose `Server` header proves the response came from the right backend. The HTTP request got a permanent redirect: Traefik's `redirectScheme` with `permanent: true` answers 301 to a GET and 308 to every other method, including the HEAD that `curl -I` sends. If the issuer still says `TRAEFIK DEFAULT CERT`, issuance has not happened or failed: the log lines tell you which (rate limit, DNS not pointing here, port 80 not reachable from the internet).

**Why this step (now):** `--resolve` tests the exact path a browser will take without touching DNS and without waiting for users to report problems. Do it for every hostname: shop, www.shop, api, intranet.

**Next step:** if all names return the expected pages with real certificates → Step 12. If 404 → the Host rule does not match (typo, or the request used an entryPoint the router does not listen on). If 502 → Traefik cannot reach Apache (back to Step 9). If `ERR_TOO_MANY_REDIRECTS` in a browser → Step 5's rule is not proxy-aware yet.

### Step 12 — Fix certificate renewal

**Goal:** stop depending on certbot for names that Traefik now serves, without breaking Apache.

```bash
# What does certbot manage, and when do the certs expire?
sudo certbot certificates

# Which Apache vhosts still reference those files?
sudo grep -RnE 'SSLCertificate(Key)?File' /etc/apache2/sites-enabled/

# Is renewal scheduled by the apt package timer or by the snap?
systemctl list-timers 'certbot*' 'snap.certbot*' --no-pager
```

```
Found the following certs:
  Certificate Name: shop.example.com
    Domains: shop.example.com www.shop.example.com
    Expiry Date: 2026-11-21 08:14:02+00:00 (VALID: 49 days)
    Certificate Path: /etc/letsencrypt/live/shop.example.com/fullchain.pem
  Certificate Name: api.example.com
    Domains: api.example.com
    Expiry Date: 2026-11-30 02:41:19+00:00 (VALID: 58 days)

/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:20:SSLCertificateFile /etc/letsencrypt/live/shop.example.com/fullchain.pem
/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:21:SSLCertificateKeyFile /etc/letsencrypt/live/shop.example.com/privkey.pem
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:18:SSLCertificateFile /etc/letsencrypt/live/api.example.com/fullchain.pem
/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:19:SSLCertificateKeyFile /etc/letsencrypt/live/api.example.com/privkey.pem

NEXT                        LEFT     LAST                        PASSED  UNIT          ACTIVATES
Sat 2026-10-03 21:37:00 UTC 9h left  Sat 2026-10-03 09:12:11 UTC 3h ago  certbot.timer certbot.service
```

**What it means:** Apache's `*:444` vhosts still load these certificate files. Once Traefik serves the sites (Step 11 passed), nobody uses them, but **Apache will refuse to start if a referenced certificate file disappears.** So the order is: first stop Apache from needing the files, then retire the certificates.

```bash
# 1. Disable the HTTPS vhosts (Traefik does HTTPS now) and the 444 listener
sudo a2dissite shop.example.com-le-ssl api.example.com-le-ssl
sudoedit /etc/apache2/ports.conf                      # remove both "Listen 444 https" lines
sudo apache2ctl configtest && sudo systemctl reload apache2

# 2. Keep a backup of all certbot state before removing anything
sudo tar czf /root/letsencrypt-$(date +%F).tgz /etc/letsencrypt

# 3. Retire the certificates so the timer stops trying (and failing) to renew them
sudo certbot delete --cert-name shop.example.com
sudo certbot delete --cert-name api.example.com
```

> ⚠️ `certbot delete` removes the certificate, its key and its renewal configuration. Run it only after `apache2ctl configtest` passes **without** the files being referenced, and only after the tar backup. The safer alternative if you are unsure: leave the certificates in place; renewal will fail noisily but harmlessly and they will simply expire.

**Why this step (now):** a failing renewal is a time bomb only if something still serves the certificate. After this step, nothing does, and Traefik renews its own certificates automatically. If you chose Option A or pattern P9 (Apache keeps its own TLS), switch certbot to DNS-01 instead of deleting anything.

**Next step:** if `configtest` passes with the HTTPS vhosts disabled and the certificates are retired (or switched to DNS-01) → Step 13. If `configtest` fails with `SSLCertificateFile: file '…' does not exist or is empty` → a vhost still points at a deleted file; find it with the `grep` above, restore from the tar backup if needed, and retry.

### Step 13 — Close 81 and 444 from outside

**Goal:** Apache's ports reachable only from the Docker bridge; the internet sees only 80 and 443 (and SSH from the office).

```bash
sudo ufw status numbered
```

```
     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    198.51.100.0/24
[ 2] Apache Full                ALLOW IN    Anywhere
[ 3] 81/tcp                     ALLOW IN    Anywhere
[ 4] 444/tcp                    ALLOW IN    Anywhere
[ 5] 81/tcp on docker_gwbridge  ALLOW IN    Anywhere                   # Traefik -> Apache
[ 6] Apache Full (v6)           ALLOW IN    Anywhere (v6)
[ 7] 81/tcp (v6)                ALLOW IN    Anywhere (v6)
[ 8] 444/tcp (v6)               ALLOW IN    Anywhere (v6)
[ 9] 81/tcp (v6) on docker_gwbridge ALLOW IN    Anywhere (v6)              # Traefik -> Apache
```

```bash
# Remove the broad rules by their spec (safer than by number: numbers shift after each delete)
sudo ufw delete allow 81/tcp
sudo ufw delete allow 444/tcp
sudo ufw status numbered

# From a machine OUTSIDE the server (office laptop, or a cloud VM for the internet view)
nc -vz -w 3 203.0.113.10 81
nc -vz -w 3 203.0.113.10 443
```

```
nc: connect to 203.0.113.10 port 81 (tcp) timed out: Operation now in progress
Connection to 203.0.113.10 443 port [tcp/https] succeeded!
```

**What it means:** Apache's ports are host processes, so UFW **does** filter them, and now only the `docker_gwbridge` rule lets Traefik in. Two notes. First, the `Apache Full` rule (80 and 443) no longer matters: those ports belong to Docker-published Traefik, and published container ports are NAT-ed before UFW's INPUT rules see them, so UFW neither allows nor blocks them. Second, the same bypass applies to Dokploy's panel on port 3000: check it from outside too, and restrict it in the `DOCKER-USER` chain or at the edge firewall (pattern P1 and recipe R7 show how). On AWS, the security group is the equivalent edge control: allow 80/443 from anywhere, SSH from the office, nothing else.

**Why this step (now):** only after Steps 10–11 prove that Traefik serves the sites can you close the direct ports without cutting anyone off. Closing them earlier would leave Option A users stranded with no alternative.

**Next step:** → Step 14. If `nc` to 81 still succeeds from outside, there is another path (UFW inactive, an edge NAT rule for 81, or Apache bound through a different interface): find it before moving on.

### Step 14 — Restore real client IPs in Apache logs

**Goal:** Apache logs and access rules should see the real visitor IP again, not Traefik's.

```bash
sudo tail -n 2 /var/log/apache2/access.log
```

```
172.18.0.3 - - [28/Sep/2026:10:52:11 +0000] "GET / HTTP/1.1" 200 5120 "-" "Mozilla/5.0 ..."
172.18.0.3 - - [28/Sep/2026:10:52:12 +0000] "GET /cart HTTP/1.1" 200 2311 "https://shop.example.com/" "Mozilla/5.0 ..."
```

```apache
# /etc/apache2/conf-available/remoteip.conf
# Trust X-Forwarded-For only when the request comes from a Docker bridge (Traefik).
RemoteIPHeader X-Forwarded-For
RemoteIPInternalProxy 172.16.0.0/12
```

```bash
sudo a2enmod remoteip
sudo a2enconf remoteip
# In /etc/apache2/apache2.conf, change %h to %a in the LogFormat lines ("combined" and "vhost_combined"):
#   %h = the TCP peer (Traefik), %a = the client IP after mod_remoteip
sudoedit /etc/apache2/apache2.conf
sudo apache2ctl configtest && sudo systemctl reload apache2
sudo tail -n 1 /var/log/apache2/access.log
```

```
Syntax OK
198.51.100.23 - - [28/Sep/2026:10:58:40 +0000] "GET / HTTP/1.1" 200 5120 "-" "Mozilla/5.0 ..."
```

**What it means:** mod_remoteip replaces the connection's client address with an address from `X-Forwarded-For`, but only when the request came from a trusted proxy range. It walks the header from the right and stops at the first address that is not a trusted proxy, so a value a client forged at the left end is ignored. `RemoteIPInternalProxy` (rather than `RemoteIPTrustedProxy`) also accepts private client addresses from the header, which you want on-prem where the office users have 198.51.100.x or 10.x addresses. Now `Require ip 198.51.100.0/24` rules, fail2ban jails and log analysis work again. Never trust `X-Forwarded-For` from everywhere: any client could then forge its IP.

**Why this step (now):** it is last because it only affects logging and IP-based rules, not availability, and because it relies on Traefik already being the only way in (Step 13).

**Next step:** update PORTS.md (section 2) and run the post-deployment checklist (section 6). The deployment is now finished.

### Rollback of the whole change

Rollback depends on how far you got. Undo in reverse order, and test after each undo.

```bash
# A. Undo the Traefik routes (Apache sites stop being served through Traefik)
sudo mv /etc/dokploy/traefik/dynamic/legacy-apache.yml /root/

# B. Give 80/443 back to Apache. WARNING: every Dokploy app goes offline at this point.
docker update --restart=no dokploy-traefik     # otherwise it comes back at the next boot and races Apache
docker stop dokploy-traefik

# C. Restore the original Apache config and restart (restart, not reload: listeners change)
sudo cp -a /etc/apache2 /root/apache2-after-change-$(date +%F)    # keep the new state for later
sudo rsync -a --delete /etc/apache2.bak-2026-09-28/ /etc/apache2/
sudo apache2ctl configtest && sudo systemctl restart apache2
sudo ss -ltnp '( sport = :80 or sport = :443 )'
```

> ⚠️ `rsync --delete` makes `/etc/apache2` identical to the backup, deleting anything created since. That is the point of a rollback, but make the second copy first (shown above) so the new work is not lost.

**Partial rollback** is usually what you want: if one Apache site misbehaves behind Traefik, delete only its router from `legacy-apache.yml` and, if it must be reachable meanwhile, publish it temporarily as Option A on :444 with a firewall allow-list.

### Verdict on port shifting

Port shifting is a legitimate, fast technique. It solves **port ownership**. It does not solve **reachability, certificates, security or documentation** by itself.

| Use case | Verdict | Why |
|---|---|---|
| Free 80/443 quickly so the edge proxy can start | ✅ Great | one config change, easy rollback, exactly what you did |
| Internal-only service (admin UI, staging, metrics) on a custom port | ✅ Good | with a firewall allow-list and a PORTS.md entry (pattern P1) |
| A backend behind a reverse proxy (Apache on 81 behind Traefik) | ✅ Good | the port is private; users never see it (Option B) |
| Public website on a non-standard port | ❌ Incomplete | blocked networks, broken links, no Let's Encrypt, origin and HSTS problems |
| Running two front-door web servers side by side for good | ❌ Avoid | two places for certs, logs and rules; pick one owner of 80/443 |
| Fixing "address already in use" without asking who owns the port | ⚠️ Risky | you may be moving the wrong service; find the owner first ([Who owns this port?](22-playbook-ports-inventory.md)) |

---

## 2. Choosing a port: the rules

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *IPs and Ports* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 3) Note: [Who owns this port?](22-playbook-ports-inventory.md) sections 2–4, and the [Network reference](02-network.md) · 4) Video: KodeKloud *Linux Crash Course for Beginners* (141 min) — networking and services parts only ([YouTube](https://www.youtube.com/watch?v=a3ujwK65dgs)) · 5) Practice: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)): run Steps 1–4 below for port 8001 and write your first PORTS.md.

**Level:** port ranges and Step 1 are [L0 · Fresher] · Steps 2–4 (sleeping owners, reserved ranges, recording) are [L1 · Junior] · the server convention and the PORTS.md template are [L3 · Senior] work that a [L4 · Lead] makes a team standard.

Port shifting only works if the new port is genuinely free, stays free, and is written down. This section is the checklist you run **before** you pick a number.

### Port ranges

| Range | Name | Examples | Rule for you |
|---|---|---|---|
| 0–1023 | well-known, "privileged" | 22 SSH, 53 DNS, 80/443 HTTP(S), 81 (no common service uses it) | binding needs root or `CAP_NET_BIND_SERVICE`; good for internal ports of root-started daemons like Apache |
| 1024–49151 | registered (IANA) | 3000 Dokploy and Node defaults, 3306 MySQL, 5432 PostgreSQL, 6379 Redis, 8080 http-alt, 9090 Prometheus, 9100 node_exporter | where most app ports live; check `/etc/services` **and** your own inventory |
| 49152–65535 | dynamic/private (IANA) | client source ports on many OSes | never for servers |
| 32768–60999 | Linux ephemeral range (`net.ipv4.ip_local_port_range`) | source ports of this host's outgoing connections | **never listen here**: a busy outgoing connection can be holding your port when the service starts |
| 30000–32767 | Kubernetes NodePort default | kube-proxy on every node | keep free on cluster nodes |
| 2377/tcp, 7946/tcp+udp, 4789/udp | Docker Swarm | Dokploy initialises Swarm | never reuse on a Dokploy host |

Privileged ports are a Linux rule, not a network rule: a non-root process gets `Permission denied` when it binds below `net.ipv4.ip_unprivileged_port_start` (1024 by default). That is a feature: nobody but root can squat port 81 while Apache restarts. If an unprivileged service genuinely needs a low port, grant only that capability in its unit (`AmbientCapabilities=CAP_NET_BIND_SERVICE`) instead of running it as root. Containers are different: the root Docker daemon binds host ports for them, so an app inside can listen on 8000 and be published anywhere.

### Step 1 — Check nothing listens on the port

**Goal:** prove no process currently owns the port, on any address, for TCP or UDP.

```bash
PORT=8001
# TCP and UDP listeners on that port, with the owning process
sudo ss -ltnup "sport = :$PORT"
# Same question, answered by a different tool (catches odd cases)
sudo lsof -nP -iTCP:$PORT -sTCP:LISTEN
sudo lsof -nP -iUDP:$PORT
```

```
Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
```

**What it means:** only the header line means nothing listens on 8001 right now, on any address and either protocol. A taken port looks like `tcp LISTEN 0 2048 127.0.0.1:8001 0.0.0.0:* users:(("gunicorn",pid=2214,fd=5),...)`. Note that a listener on `127.0.0.1:8001` still blocks a new one on `0.0.0.0:8001`, because the wildcard includes loopback.

**Why this step (now):** it is the cheapest, most direct evidence. Everything after this step looks for owners that are **not running right now** but will claim the port later.

**Next step:** if empty → Step 2. If taken → find the owner's unit and config with [Who owns this port?](22-playbook-ports-inventory.md), then pick another port or move the owner deliberately.

### Step 2 — Check sleeping owners

**Goal:** find services that are not listening at this moment but will grab the port at the next start or boot.

```bash
# systemd socket units listen on behalf of services that are not running yet
systemctl list-sockets --all --no-pager

# Stopped containers with a restart policy come back at boot with their published ports
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Swarm (Dokploy) services with published ports
docker service ls --format 'table {{.Name}}\t{{.Ports}}'

# Installed-but-stopped services that mention the port in their config
sudo grep -RnwE "$PORT" /etc --include='*.conf' --include='*.yml' --include='*.yaml' --include='*.service' --include='*.xml' 2>/dev/null | head
```

```
LISTEN                         UNIT                    ACTIVATES
/run/dbus/system_bus_socket    dbus.socket             dbus.service
/run/systemd/journal/socket    systemd-journald.socket systemd-journald.service
[::]:22                        ssh.socket              ssh.service

NAMES              STATUS                     PORTS
dokploy-traefik    Up 6 days                  0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, ...
old-reports        Exited (0) 3 weeks ago

NAME      PORTS
dokploy   *:3000->3000/tcp

/etc/tomcat10/server.xml:69:    <Connector port="8001" protocol="HTTP/1.1"
```

**What it means:** on Ubuntu 24.04 SSH is socket-activated, so `systemd` (PID 1) owns port 22 even when `sshd` is not running, and `ss` shows `("systemd",pid=1,...)` as the owner. The stopped container `old-reports` publishes nothing now, but check its definition (`docker inspect old-reports --format '{{json .HostConfig.PortBindings}}'`) before reusing its old port. Swarm services with published ports in the default ingress mode are bound by `dockerd` on **every** node of the swarm. The grep found an installed but stopped Tomcat configured for 8001: the next `systemctl start tomcat10` or reboot would fail one of you.

**Why this step (now):** "free right now" is not "free". These sleeping owners cause the classic Monday-morning outage after a weekend reboot.

**Next step:** if nothing claims the port → Step 3. If something does → choose another port, or disable the sleeping owner on purpose and record it.

### Step 3 — Check the reserved ranges

**Goal:** make sure the port is not in a range the kernel or your platform hands out by itself.

```bash
grep -wE "$PORT" /etc/services
sysctl net.ipv4.ip_local_port_range net.ipv4.ip_local_reserved_ports net.ipv4.ip_unprivileged_port_start
```

```
net.ipv4.ip_local_port_range = 32768	60999
net.ipv4.ip_local_reserved_ports =
net.ipv4.ip_unprivileged_port_start = 1024
```

**What it means:** 8001 has no registered name and is below the ephemeral range, so it is safe. If a vendor product insists on a port inside 32768–60999, reserve it so the kernel never uses it as a source port: put `net.ipv4.ip_local_reserved_ports = 50000` in `/etc/sysctl.d/90-reserved-ports.conf` and run `sudo sysctl --system`. On Kubernetes nodes also keep 30000–32767 free.

**Why this step (now):** a port in the ephemeral range works for weeks and then fails at random restarts, which is the hardest kind of bug to trace back to a port choice.

**Next step:** if the port is outside 32768–60999 and 30000–32767 and `/etc/services` names nothing you run → Step 4. If it is inside the ephemeral range → choose another port from your convention, or reserve it as shown, then Step 4.

### Step 4 — Record the port

**Goal:** the port, its owner and its purpose are written where the next person will look.

```bash
# A raw inventory you can paste into PORTS.md and then annotate
sudo ss -ltnupH | awk '{print $1, $5, $7}' | sort -k2 -u
sudoedit /root/PORTS.md
```

```
tcp *:81 users:(("apache2",pid=47102,fd=3),("apache2",pid=47101,fd=3),("apache2",pid=1338,fd=3))
tcp 0.0.0.0:3000 users:(("docker-proxy",pid=2402,fd=7))
tcp 0.0.0.0:443 users:(("docker-proxy",pid=48236,fd=7))
tcp 0.0.0.0:80 users:(("docker-proxy",pid=48211,fd=7))
udp 127.0.0.54:53 users:(("systemd-resolve",pid=612,fd=16))
tcp 192.0.2.10:8001 users:(("gunicorn",pid=2214,fd=5))
```

(Excerpt in `LC_ALL=C` sort order; with a UTF-8 locale `sort` ignores punctuation and the order differs.)

**What it means:** this is the "what is actually there" list. PORTS.md adds what no tool can tell you: why the port exists, who owns it, who may reach it, and where its config lives.

**Why this step (now):** the port you chose today is the mystery listener someone else finds in a year. Writing it down takes two minutes; reverse-engineering it takes an afternoon (module 21 spends a whole phase on exactly that).

**Next step:** deploy using one of the patterns in section 3.

### A port convention for a shared server

Pick a convention once per server (or per fleet) and stick to it. This one fits a Dokploy host that also runs legacy Apache and a few systemd apps:

| Range or port | Reserved for | Bind address | Who may connect |
|---|---|---|---|
| 80, 443 (+ udp/443) | the edge proxy only (Traefik via Dokploy) | all | everyone |
| 81 | Apache legacy vhosts, plain HTTP | all, firewalled | Docker bridge (Traefik) only |
| 22 | SSH | all | office range only |
| 3000 | Dokploy panel | all (Docker-published) | office range only, via `DOCKER-USER` or edge firewall |
| 8001–8099 | app servers run by systemd (gunicorn, node, Tomcat) | 127.0.0.1, or HOSTIP when Traefik must reach them | proxy only |
| 9090–9199 | monitoring (Prometheus 9090, node_exporter 9100) | HOSTIP | monitoring server only |
| 9400–9499 | internal admin UIs on direct ports (pattern P1) | HOSTIP | office range only |
| 18000–18999 | temporary test publishes of containers | 127.0.0.1 only | nobody remote; delete after testing |
| 5432, 3306, 6379, 1883 | databases, caches, brokers | 127.0.0.1 or a private network, never public | apps only (pattern P10) |
| 2377, 7946, 4789 | Docker Swarm | all | other swarm nodes only |
| never | 30000–32767 (NodePorts), 32768–60999 (ephemeral) | | |

### PORTS.md template

Keep this file in `/root/PORTS.md` on the server **and** in your infrastructure Git repository. Update it in the same change as the port.

```markdown
# PORTS.md — web01 (192.0.2.10), Ubuntu 24.04
Last reviewed: 2026-09-28 by ops@example.com · Convention: see "A port convention for a shared server"

| Port/proto | Bind | Owner (unit / container) | Purpose | Who may connect | Enforced by | Config | Contact |
|---|---|---|---|---|---|---|---|
| 22/tcp | [::] | ssh.socket → ssh.service | admin SSH | 198.51.100.0/24 | ufw | /etc/ssh/sshd_config | ops |
| 80,443/tcp 443/udp | 0.0.0.0, [::] | dokploy-traefik | edge proxy, all public sites | anyone | Docker publish (bypasses ufw) | /etc/dokploy/traefik/ | ops |
| 81/tcp | * | apache2.service | legacy vhosts shop, api, intranet | Traefik only | ufw allow in on docker_gwbridge | /etc/apache2/ports.conf | ops |
| 3000/tcp | 0.0.0.0 | dokploy (swarm service) | Dokploy panel | 198.51.100.0/24 | DOCKER-USER rule (docker-user-rules.service) | Dokploy | ops |
| 8001/tcp | 192.0.2.10 | reports.service | reports app (gunicorn) | Traefik only | ufw allow in on docker_gwbridge | /etc/systemd/system/reports.service | team-reports |
| 9100/tcp | 192.0.2.10 | prometheus-node-exporter | metrics | 192.0.2.40 | ufw | /etc/default/prometheus-node-exporter | ops |

## History
- 2026-09-28 Apache moved 80→81, 443→444 for Dokploy; 444 removed after Traefik took over TLS. Change: CHG-0142.
```

---

## 3. Pattern catalogue

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Implement Reverse Proxies and Load Balancers* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 2) KodeKloud: *Nginx For Beginners* — Intermediate Config → *Virtual Servers & Multiple Sites* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Virtual-Servers-Multiple-Sites/page)) and *Reverse Proxy* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) · 3) KodeKloud: *Docker Certified Associate* — Docker Engine → *Publishing Ports* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 4) Note: [Learn: web servers & proxies](29-learn-webservers-proxies.md) and [Learn: Docker](30-learn-docker.md) · 5) Docs: Docker *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)) and Traefik's Docker routing reference ([docs](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/)) · 6) Video: KodeKloud *NGINX For Beginners | NGINX Tutorial* (86 min, [YouTube](https://www.youtube.com/watch?v=Hfg7_y0fGTg)) · 7) Practice: KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)): build P1, P3 and P5 Variant B side by side and compare `ss -ltnp` for each.

**Level:** each pattern starts with its own tag. In short: P1, P2 and P10 are [L1 · Junior]; P3–P7 are [L2 · Mid]; P8, P9, P11 and P12 are [L3 · Senior]. A [L4 · Lead] decides which patterns are allowed on which servers.

Twelve ways to put an application on a server. Most real servers combine several: your web01 is P3 (Traefik in front) + P2 (Apache vhosts behind it) + P6 (Dokploy apps) + P10 (databases not exposed). Read the table, then jump to the pattern you need.

| # | Pattern | Who owns 80/443 | Typical use | Verdict |
|---|---|---|---|---|
| P1 | Port per app | nobody in particular | internal tools, admin UIs | internal only, allow-listed |
| P2 | Name-based virtual hosts | one Apache or Nginx | many simple sites on one server | classic and fine |
| P3 | Reverse proxy by hostname | Traefik, Nginx, Caddy or Apache | public apps of any kind | **the default** |
| P4 | Path-based routing | the proxy | several apps under one hostname | only when the apps support a base path |
| P5 | Docker apps behind the proxy | the proxy | containers | loopback publish, or no publish at all |
| P6 | Dokploy-native domains | Traefik (Dokploy) | anything deployed with Dokploy | **the default on Dokploy hosts** |
| P7 | systemd apps behind a proxy | the proxy | gunicorn, uvicorn, node, Java | solid for non-container apps |
| P8 | Multiple IP addresses | one owner per IP | two independent front doors | only when two edges are truly required |
| P9 | TLS passthrough and SNI routing | a TCP router | apps that must terminate TLS themselves | special cases |
| P10 | Non-HTTP services | nobody | databases, Redis, MQTT, SSH | do not expose |
| P11 | Kubernetes Services and Ingress | the Ingress or Gateway | clusters | port juggling disappears |
| P12 | Blue/green on two ports | the proxy | zero-downtime releases | with health checks and a drain |

### P1 — Port per app

**Level:** [L1 · Junior]; the `DOCKER-USER` part is [L2 · Mid]. **Study:** LFCS Networking → *Configure Packet Filtering (Firewall)* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)).

Each application listens directly on its own port of the host, and clients connect to `HOSTIP:PORT`. No proxy, no hostname routing. Your 81/444 change used this mechanism for Apache. It is the right tool for internal services that a handful of known people or systems use (a monitoring UI, a vendor admin console, a staging build), and the wrong tool for anything public.

```
office 198.51.100.0/24 ──► 192.0.2.10:9401 (admin tool)   ✔ allowed
internet               ──► 192.0.2.10:9401                ✘ dropped by firewall
```

#### Step 1 — Bind the app to a private address

**Goal:** the tool listens on the server's private address (or loopback), not on every interface.

```bash
# After setting the app's bind address (its own config, or -p 192.0.2.10:9401:3001 for a container)
sudo ss -ltnp 'sport = :9401'
```

```
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN  0       4096       192.0.2.10:9401        0.0.0.0:*      users:(("docker-proxy",pid=51022,fd=7))
```

**What it means:** the listener is on 192.0.2.10 only, so a second NIC (a public or DMZ interface) does not expose it. It is still reachable by anything that can route to 192.0.2.10, which is why Step 2 exists.

**Why this step (now):** the bind address is your first filter, and it costs nothing. A server with one NIC gains little from it; a server with a public and a private NIC gains a lot.

**Next step:** if `ss` shows the private address → Step 2. If it shows `0.0.0.0`, `*` or `[::]` → the bind did not apply (wrong config key, or `-p 9401:3001` without an address); fix it and check again before you add any firewall rule.

#### Step 2 — Allow-list the port

**Goal:** only the office range may connect; everybody else is dropped.

```bash
# A host process (systemd service): UFW applies
sudo ufw allow from 198.51.100.0/24 to any port 9401 proto tcp comment 'admin tool, office only'

# A Docker-published port: UFW does NOT apply. Filter in DOCKER-USER, matching the
# ORIGINAL destination port (DNAT has already rewritten it to the container port)
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 9401 --ctdir ORIGINAL \
    ! -s 198.51.100.0/24 -j DROP
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1        0     0 DROP       6    --  ens18  *      !198.51.100.0/24      0.0.0.0/0            ctorigdstport 9401 ctdir ORIGINAL
2     812K  901M RETURN     0    --  *      *       0.0.0.0/0            0.0.0.0/0
```

**What it means:** for a host process, the UFW rule plus the default `deny (incoming)` is enough. For a container, the packet is forwarded, not delivered locally, so UFW's INPUT rules never see it; `DOCKER-USER` is the chain Docker reserves for your filters, evaluated before its own rules. Rules added with `iptables` are lost at reboot; recipe R7 shows how to make them persistent with a small systemd unit. On Docker hosts using the newer nftables firewall backend, `DOCKER-USER` does not exist; check Docker's packet filtering documentation for your version.

**Why this step (now):** the port is useless to an attacker only once the filter exists. Do it before you hand out the URL.

**Next step:** if the rule appears in `ufw status` (host process) or in `DOCKER-USER` (container) → Step 3. If `iptables` answers `No chain/target/match by that name` → Docker is not running or uses the nftables backend; see the note above and Docker's packet filtering docs.

#### Step 3 — Test from inside and outside the allow-list

**Goal:** prove both halves of the rule: allowed clients connect, others time out.

```bash
# From an office machine (198.51.100.x)
nc -vz -w 3 192.0.2.10 9401
# From any machine outside the office range (or the internet view: 203.0.113.10 if NAT-ed)
nc -vz -w 3 192.0.2.10 9401
```

```
Connection to 192.0.2.10 9401 port [tcp/*] succeeded!
nc: connect to 192.0.2.10 port 9401 (tcp) timed out: Operation now in progress
```

**What it means:** "succeeded" from inside and "timed out" from outside means the allow-list works. "Connection refused" from outside would mean a REJECT rule or nothing listening, which is worth understanding (see [Network](02-network.md)).

**Why this step (now):** a firewall rule you have not tested from the wrong side is a hope, not a control.

**Next step:** add the port to PORTS.md. Done.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| simplest possible setup; no proxy to configure | users must know and type the port | internal admin UIs, vendor consoles, staging builds |
| apps are fully independent of each other | no central TLS: each app needs its own certificate or runs plain HTTP | systems talking to systems on a private network |
| easy to firewall per port | many networks block non-standard ports | temporary access during a migration |
| one app's failure cannot break another's routing | every new app means a new firewall rule and a new port to track | never for public websites |

**Verify:** `ss -ltnp` shows the intended bind address; `nc` succeeds from an allowed client and times out from elsewhere; the port is in PORTS.md.

**Rollback:** stop the app or remove its port publish, delete the firewall rule by its spec (`sudo ufw delete allow from 198.51.100.0/24 to any port 9401 proto tcp`, or `sudo iptables -D DOCKER-USER` with the same arguments you inserted), and remove the PORTS.md line.

**Gotchas:**

- Docker-published ports ignore UFW. Use `DOCKER-USER`, the edge firewall, or publish on 127.0.0.1 and use an SSH tunnel.
- IPv6: UFW handles both families, but `iptables` rules do not cover IPv6; use `ip6tables` too, or do not publish on `[::]`.
- Plain HTTP on a custom port sends passwords in clear text across the LAN. Put TLS on the app or front it with the proxy (P3) plus `ipAllowList`.
- People bookmark `http://192.0.2.10:9401`. Changing the port or IP later breaks their muscle memory; choose once, from the convention.

### P2 — Name-based virtual hosts

**Level:** [L1 · Junior]. **Study:** *DevOps Pre-Requisite Course* → *Apache Web Server* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)), then *Nginx For Beginners* → *Virtual Servers & Multiple Sites* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Virtual-Servers-Multiple-Sites/page)).

One web server owns 80/443 and serves many sites. For HTTP the `Host` header selects the site; for HTTPS the TLS SNI extension selects the certificate and then `Host` selects the site. This is what Apache on web01 did before Dokploy arrived, and it is still the right model **behind** a proxy (Apache on 81 behind Traefik is exactly P2 behind P3).

#### Step 1 — Create the vhost

**Goal:** a new site, `blog.example.com`, served by the existing Apache (or Nginx) without disturbing the others.

```apache
# /etc/apache2/sites-available/blog.example.com.conf  (on web01: *:81, behind Traefik)
<VirtualHost *:81>
    ServerName blog.example.com
    ServerAlias www.blog.example.com
    DocumentRoot /var/www/blog/public
    ErrorLog ${APACHE_LOG_DIR}/blog-error.log
    CustomLog ${APACHE_LOG_DIR}/blog-access.log combined
    <Directory /var/www/blog/public>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

```nginx
# Nginx equivalent: /etc/nginx/sites-available/blog.example.com
server {
    listen 80;
    listen [::]:80;
    server_name blog.example.com www.blog.example.com;
    root /var/www/blog/public;
    index index.html;
    access_log /var/log/nginx/blog.access.log;
    error_log  /var/log/nginx/blog.error.log;
    location / {
        try_files $uri $uri/ =404;
    }
}
```

```bash
sudo a2ensite blog.example.com
sudo apache2ctl configtest && sudo systemctl reload apache2
sudo apache2ctl -S 2>&1 | grep -A1 'blog.example.com'
# Nginx: sudo ln -s /etc/nginx/sites-available/blog.example.com /etc/nginx/sites-enabled/
#        sudo nginx -t && sudo systemctl reload nginx
```

```
Syntax OK
         port 81 namevhost blog.example.com (/etc/apache2/sites-enabled/blog.example.com.conf:2)
                 alias www.blog.example.com
```

**What it means:** Apache now knows the name on port 81. It does **not** mean the site is reachable: on web01, Traefik must also route `blog.example.com` to Apache (add a router to `legacy-apache.yml`, as in Step 10 of section 1).

**Why this step (now):** the vhost is the site's identity; everything else (routing, certificate, DNS) points at it.

**Next step:** if `-S` lists the name on port 81 → Step 2. If the name is missing → the site is not enabled (`a2ensite`) or the file name does not end in `.conf`. If `configtest` fails → fix the file and line it names, then repeat.

#### Step 2 — Add a catch-all default

**Goal:** requests for unknown names get a neutral answer, not one of your real sites.

```apache
# /etc/apache2/sites-available/000-default.conf — the first vhost on a port answers unknown names
<VirtualHost *:81>
    ServerName default.invalid
    DocumentRoot /var/www/empty
    <Location />
        Require all denied
    </Location>
</VirtualHost>
```

```nginx
# Nginx: an explicit default_server that closes the connection
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 444;   # Nginx-specific: close the connection without a response (unrelated to TCP port 444)
}
```

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: nonexistent.example.com' http://127.0.0.1:81/
```

```
403
```

**What it means:** unknown names get 403 instead of the shop. Without a catch-all, the first vhost alphabetically answers for every unknown or misspelled name, scanners index your shop under the bare IP, and a DNS mistake silently serves the wrong site. For HTTPS on Nginx, `ssl_reject_handshake on;` in the default server refuses the handshake for unknown names; it needs Nginx 1.19.4 or newer, so on Ubuntu 22.04 (Nginx 1.18) use a self-signed dummy certificate instead.

**Why this step (now):** the default vhost is chosen implicitly. Making it explicit removes a whole class of "why is the wrong site showing?" incidents.

**Next step:** if unknown names get 403 (or a closed connection on Nginx) → Step 3. If they still get a real site → the catch-all is not the first vhost on that port; make sure its file sorts first (`000-…`) and that `apache2ctl -S` shows it as `default server`.

#### Step 3 — Test every name

**Goal:** each name returns its own site; the catch-all handles the rest.

```bash
for h in blog.example.com www.blog.example.com shop.example.com nonexistent.example.com; do
  printf '%-26s ' "$h"
  curl -s -o /dev/null -w '%{http_code} %{size_download}B\n' -H "Host: $h" http://127.0.0.1:81/
done
```

```
blog.example.com           200 18211B
www.blog.example.com       200 18211B
shop.example.com           301 0B
nonexistent.example.com    403 199B
```

**What it means:** each name lands where expected (shop redirects because the request did not carry `X-Forwarded-Proto: https`, as designed in section 1).

**Why this step (now):** `configtest` checks syntax, not routing. Only requests prove routing.

**Next step:** add the Traefik route and certificate (P3), then PORTS.md is unchanged (no new port: that is the beauty of vhosts).

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| unlimited sites on one port pair | one server process: a bad reload or crash takes all sites down | many small PHP or static sites |
| standard URLs, no ports for users | shared modules and PHP version for all sites (php-fpm pools help) | legacy hosting you are not ready to containerise |
| mature tooling (`apache2ctl -S`, `nginx -T`) | tenants are not isolated from each other | behind a proxy, as the backend for several hostnames |

**Verify:** `apache2ctl -S` (or `nginx -T | grep -E 'listen|server_name'`) lists every name on the right port; each name returns its own content with `curl -H 'Host: ...'` or `--resolve`; an unknown name hits the catch-all.

**Rollback:** `sudo a2dissite blog.example.com && sudo systemctl reload apache2` (Nginx: remove the symlink, `nginx -t`, reload). Files in `sites-available` stay for later.

**Gotchas:**

- Apache matches the **IP:port** first, then the name. A single IP-based vhost such as `<VirtualHost 192.0.2.10:81>` shadows every `*:81` name-based vhost for connections to that IP.
- A name that has an HTTP vhost but no HTTPS vhost gets the **default HTTPS vhost's** content and certificate on 443. Every HTTPS name needs its own vhost (or a proxy that terminates TLS for it).
- Forgetting `ServerAlias www...` sends `www` to the catch-all.
- `apache2ctl configtest` says `Syntax OK` for vhosts on ports nobody listens on. Check `-S`.

### P3 — Reverse proxy by hostname

**Level:** [L2 · Mid]. **Study:** LFCS Networking → *Implement Reverse Proxies and Load Balancers* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)), then [Learn: web servers & proxies](29-learn-webservers-proxies.md).

One proxy owns 80/443 and terminates TLS. Every application listens on a private address, and the proxy forwards each hostname to the right backend. This is the default for public applications and the finished form of your fix. Traefik is the proxy on Dokploy hosts; Nginx, Caddy and Apache can play the same role.

```
client ─TLS─► proxy :443 ──(Host: app.example.com)──► http://127.0.0.1:8001   systemd app
                         ├─(Host: shop.example.com)──► http://192.0.2.10:81    Apache vhosts
                         └─(Host: wiki.example.com)──► http://wiki:3000        container on the proxy's network
```

#### Step 1 — Run the app on a private address

**Goal:** the backend listens where the proxy can reach it and the internet cannot.

```bash
# Example: a gunicorn app (pattern P7) on loopback port 8001
sudo ss -ltnp 'sport = :8001'
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8001/health
```

```
LISTEN 0      2048       127.0.0.1:8001      0.0.0.0:*    users:(("gunicorn",pid=2214,fd=5))
200
```

**What it means:** the app is alive and private. Which private address depends on where the proxy runs: a proxy **on the host** (Nginx, Apache, Caddy installed with apt) can use 127.0.0.1; a proxy **in a container** (Dokploy's Traefik) cannot reach the host's loopback and needs HOSTIP plus a firewall rule (section 1, Step 9) or the app on its Docker network (P5).

**Why this step (now):** test the backend alone first. If it fails here, the proxy is not the problem and you saved yourself a confusing 502.

**Next step:** if the backend answers 200 → Step 2. If `Connection refused` → nothing listens there (check the unit, pattern P7). If it answers with an error → fix the app before you touch the proxy ([Site down playbook](25-playbook-site-down.md)).

#### Step 2 — Add the proxy route

**Goal:** one hostname, one route, one certificate. Pick the block for your proxy.

```yaml
# Traefik (Dokploy host): /etc/dokploy/traefik/dynamic/reports.yml
http:
  routers:
    reports:
      entryPoints: [websecure]
      rule: "Host(`reports.example.com`)"
      service: reports
      tls:
        certResolver: letsencrypt
  services:
    reports:
      loadBalancer:
        servers:
          - url: "http://192.0.2.10:8001"     # HOSTIP, not 127.0.0.1: Traefik runs in a container
```

```nginx
# Nginx on the host: /etc/nginx/sites-available/reports.example.com
server {
    listen 443 ssl http2;          # Ubuntu 22.04/24.04 Nginx; "http2 on;" needs 1.25.1+
    listen [::]:443 ssl http2;
    server_name reports.example.com;
    ssl_certificate     /etc/letsencrypt/live/reports.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/reports.example.com/privkey.pem;
    client_max_body_size 20m;      # default is 1m: uploads above it get 413
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;     # WebSockets
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 60s;
    }
}
```

```apache
# Apache as the proxy (a2enmod proxy proxy_http headers ssl)
<VirtualHost *:443>
    ServerName reports.example.com
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/reports.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/reports.example.com/privkey.pem
    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/
    RequestHeader set X-Forwarded-Proto "https"
</VirtualHost>
```

```
# Caddy (/etc/caddy/Caddyfile): automatic HTTPS, headers set for you
reports.example.com {
    reverse_proxy 127.0.0.1:8001
}
```

```bash
# Traefik: drop the file into the watched folder, then look for errors about it
sudo install -m 644 /root/reports.yml /etc/dokploy/traefik/dynamic/reports.yml
sleep 3; docker logs --since 1m dokploy-traefik 2>&1 | grep -iE 'error.*reports' || echo "reports.yml loaded without errors"

# Nginx on the host: enable the site, test, then reload (a failed test changes nothing)
sudo ln -s /etc/nginx/sites-available/reports.example.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

```
reports.yml loaded without errors
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**What it means:** all four say the same thing: "for this name, terminate TLS here and send the request to that private address". Traefik and Caddy obtain certificates themselves; with Nginx or Apache you run certbot, and certbot's HTTP-01 works because that proxy owns port 80.

**Why this step (now):** the backend is proven in Step 1, so whatever fails from now on is the proxy layer.

**Next step:** if the proxy accepts the config (Traefik log quiet, `nginx -t` or `apache2ctl configtest` OK) → Step 3. If it rejects it → fix the line it names; users are unaffected because the old config is still running.

#### Step 3 — Make the app trust the proxy

**Goal:** the app knows the real client IP and that the original request was HTTPS.

```bash
# What does the backend actually receive? Ask it to echo headers (or read its access log)
curl -s --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/debug/headers
```

```
Host: reports.example.com
X-Forwarded-For: 198.51.100.23
X-Forwarded-Host: reports.example.com
X-Forwarded-Port: 443
X-Forwarded-Proto: https
X-Real-Ip: 198.51.100.23
```

**What it means:** Traefik adds these headers automatically; Nginx sends only what you set with `proxy_set_header`; Apache's `mod_proxy` adds `X-Forwarded-For`, `X-Forwarded-Host` and `X-Forwarded-Server` but not `X-Forwarded-Proto`, which is why the Apache example sets it. The app must be told to trust them, or it builds `http://` links and redirect-loops: gunicorn `--forwarded-allow-ips`, Django `SECURE_PROXY_SSL_HEADER`, Express `app.set('trust proxy', 1)`, Tomcat `RemoteIpValve`, Apache `mod_remoteip` (section 1, Step 14).

**Why this step (now):** most "works on the server, broken through the proxy" bugs are header trust bugs: wrong scheme in redirects, all users sharing the proxy's IP in rate limits, CSRF origin failures.

**Next step:** if the headers arrive and the app is set to trust them → Step 4. If `X-Forwarded-Proto` is missing → add it in the proxy (Nginx and Apache need it explicitly). If the headers arrive but the app still builds `http://` links → set its trust option from the list above.

#### Step 4 — Test the route with --resolve

**Goal:** the full path (DNS skipped, TLS, proxy, app) works before you change DNS.

```bash
curl -sv -o /dev/null --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/ 2>&1 \
    | grep -E '^\* +(subject|issuer|SSL certificate verify)|^< HTTP'
```

```
*  subject: CN=reports.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
*  SSL certificate verify ok.
< HTTP/2 200
```

**What it means:** right certificate, trusted chain, 200 from the app. Now point DNS at the server (or it already does) and test once more without `--resolve`.

**Why this step (now):** after DNS changes, mistakes are public and cached for the TTL. Before, they are private.

**Next step:** PORTS.md (the backend port), the post-deployment checklist (section 6).

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| standard URLs for every app; one place for TLS, redirects, logs and access rules | the proxy is a shared dependency: its outage is everyone's outage | every public HTTP application |
| backends stay private, any port, any technology | one more hop to debug (502/504 means "proxy could not get an answer") | many apps on one IP |
| easy to add auth, rate limits, IP allow-lists centrally | header trust must be configured in each app | when you want to swap or scale backends without touching DNS |

**Verify:** `curl --resolve` returns the right certificate and a 200 for each name; the backend port is not reachable from outside (`nc` from another host times out); the app's logs show real client IPs.

**Rollback:** remove the route (delete the Traefik file, or disable the Nginx/Apache site and reload). The backend keeps running privately, so rolling back routing never loses data.

**Gotchas:**

- **502** = the proxy got no valid answer: wrong port, app bound to 127.0.0.1 while the proxy is in a container, firewall between them. **504** = the app was too slow (Nginx gives up after 60 s by default; gunicorn kills workers after 30 s).
- Nginx `client_max_body_size` defaults to 1 MB: uploads fail with 413 until you raise it.
- WebSockets need the `Upgrade` and `Connection` headers in Nginx; Traefik and Caddy handle them automatically.
- In Nginx, `proxy_pass http://127.0.0.1:8001;` and `proxy_pass http://127.0.0.1:8001/;` behave differently inside a `location /prefix/` block (see P4).

### P4 — Path-based routing

**Level:** [L2 · Mid]. **Study:** *Nginx For Beginners* → *Reverse Proxy* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) for the `proxy_pass` trailing-slash rule.

Several apps share one hostname and are told apart by the URL path: `tools.example.com/grafana`, `tools.example.com/reports`. It looks tidy and saves certificates and DNS records, but it only works when each app knows it lives under a prefix. **Prefer a subdomain per app**; use paths when you cannot get more hostnames.

The pitfalls, in the order you will meet them:

| Pitfall | What breaks | Fix |
|---|---|---|
| Absolute asset URLs | the page loads, CSS and JS 404 (`/static/app.css` instead of `/reports/static/app.css`) | tell the app its base path (Django `FORCE_SCRIPT_NAME` or gunicorn `SCRIPT_NAME`, Grafana `root_url`, Vite `base`, React `homepage`) |
| Redirects without the prefix | login redirects to `/login`, which belongs to another app or 404s | same: base path setting, or `X-Forwarded-Prefix` support in the app |
| Strip or keep the prefix | some apps want the prefix removed (most), some want it kept (Grafana with `serve_from_sub_path`) | read the app's docs; StripPrefix only for apps that expect `/` |
| Cookies | all apps on one host share cookies; two apps both using a cookie named `session` log each other out | per-app cookie names, or cookie `Path=/reports` |
| Prefix matching | Traefik's `PathPrefix` is a plain string prefix: `/app` also matches `/application` | match `/app/` (with the slash) or use separate hostnames |
| Single-page apps | client-side routes and `<base href>` assume `/` | build with the base path |

#### Step 1 — Check the app supports a base path

**Goal:** find the setting that tells the app its URL prefix, before you touch the proxy.

```bash
# Run the app with its base-path setting, then ask it for a page and check the links it generates
curl -s http://127.0.0.1:8002/reports/ | grep -oE '(href|src)="[^"]+"' | head -5
```

```
href="/reports/static/css/app.css"
src="/reports/static/js/app.js"
href="/reports/login"
```

**What it means:** every link carries `/reports/`: the app is prefix-aware. If you see `href="/static/..."`, it is not, and path routing will break its assets no matter how clever the proxy rule is.

**Why this step (now):** no proxy rule can fix an app that generates the wrong URLs. Checking the app first decides whether P4 is even possible.

**Next step:** if prefix-aware → Step 2. If not → use a subdomain (P3), or ask the developers for a base-path setting.

#### Step 2 — Route the prefix and strip it if needed

**Goal:** `/reports/...` goes to the reports app, with or without the prefix as the app expects.

```yaml
# Traefik: /etc/dokploy/traefik/dynamic/tools.yml
http:
  middlewares:
    reports-strip:
      stripPrefix:
        prefixes:
          - "/reports"          # Traefik also sends X-Forwarded-Prefix: /reports
  routers:
    tools-reports:
      entryPoints: [websecure]
      rule: "Host(`tools.example.com`) && PathPrefix(`/reports/`)"
      middlewares: [reports-strip]     # omit for apps that expect the prefix to be kept
      service: reports
      tls:
        certResolver: letsencrypt
  services:
    reports:
      loadBalancer:
        servers:
          - url: "http://192.0.2.10:8002"
```

```nginx
# Nginx: the trailing slash on proxy_pass decides whether the prefix is stripped
location /reports/ {
    proxy_pass http://127.0.0.1:8002/;          # /reports/x  ->  /x         (stripped)
    # proxy_pass http://127.0.0.1:8002;         # /reports/x  ->  /reports/x (kept)
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Prefix /reports;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location = /reports { return 301 /reports/; }   # add the slash for people who forget it
```

```bash
# Traefik: install the file and check that it loaded
sudo install -m 644 /root/tools.yml /etc/dokploy/traefik/dynamic/tools.yml
sleep 3; docker logs --since 1m dokploy-traefik 2>&1 | grep -iE 'error.*tools' || echo "tools.yml loaded without errors"

# Nginx variant: test before reload
sudo nginx -t && sudo systemctl reload nginx
```

```
tools.yml loaded without errors
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**What it means:** the two Nginx `proxy_pass` lines differ by one character and route to completely different backend paths. With a URI part (even just `/`), Nginx replaces the matched location prefix with it; without one, Nginx passes the original path unchanged.

**Why this step (now):** the app's behaviour from Step 1 tells you whether to strip; now the proxy matches it.

**Next step:** if the router loads (no error in the Traefik log, or `nginx -t` OK) → Step 3. If `/reports/` returns 404 through the proxy → the rule or the strip setting does not match what the app expects; go back to Step 1's output and compare paths.

#### Step 3 — Test assets, redirects and cookies

**Goal:** prove the three things that usually break.

```bash
B=https://tools.example.com; R='--resolve tools.example.com:443:192.0.2.10'
curl -s $R -o /dev/null -w 'page   %{http_code}\n' $B/reports/
curl -s $R -o /dev/null -w 'asset  %{http_code}\n' $B/reports/static/css/app.css
curl -s $R -o /dev/null -w 'login  %{http_code} -> %{redirect_url}\n' $B/reports/account
curl -s $R -D - -o /dev/null $B/reports/login | grep -i '^set-cookie'
```

```
page   200
asset  200
login  302 -> https://tools.example.com/reports/login
set-cookie: reports_session=8f1c...; Path=/reports; Secure; HttpOnly; SameSite=Lax
```

**What it means:** assets load, redirects keep the prefix, and the session cookie is scoped to `/reports` with a unique name. A redirect to `https://tools.example.com/login` (prefix lost) or `Path=/` with a generic name means the app is not fully prefix-aware.

**Why this step (now):** the home page returning 200 proves very little; these three requests prove the app will actually work for users.

**Next step:** PORTS.md, section 6 checklist.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| one hostname and one certificate for many apps | every app must support a base path | internal tool portals (`tools.example.com/...`) |
| no DNS change for a new app | cookies, CORS origin and CSP are shared between the apps | APIs versioned by path (`/v1`, `/v2`) of the **same** service |
| | subtle, app-specific breakage (assets, redirects, WebSockets) | when new hostnames are genuinely unavailable |

**Verify:** the three requests in Step 3 for every app; a browser session with the developer tools' network tab open shows no 404s.

**Rollback:** remove the router (Traefik file) or the `location` block (Nginx), reload. Then serve the app on its own hostname instead.

**Gotchas:**

- `` PathPrefix(`/app`) `` in Traefik also matches `/application`; include the trailing slash.
- Router priority: Traefik sorts routers by rule length by default, so a long path rule beats a bare `Host` rule for the same hostname. Usually right; set `priority` explicitly when in doubt.
- Health checks and monitoring must use the prefixed path.

### P5 — Docker apps behind the proxy

**Level:** [L2 · Mid]. **Study:** *Docker Training Course for the Absolute Beginner* → *Docker Networking* ([lesson](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page)), then *Docker Certified Associate* → *Publishing Ports* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)).

A containerised app needs no host port at all if the proxy can reach it over a Docker network. There are two clean variants and one dangerous default.

| Variant | Host port | Who can proxy to it | Use on web01? |
|---|---|---|---|
| `ports: "8000:8000"` (the default everyone copies) | `0.0.0.0:8000`, **bypasses UFW** | anyone on the internet | ❌ never for a proxied app |
| A: `ports: "127.0.0.1:18000:8000"` | loopback only | a proxy **on the host** (Nginx/Apache via apt) | ✅ with a host proxy, and for quick tests |
| B: no `ports:`, join the proxy's network + labels | none | a proxy **in a container** (Traefik/Dokploy) | ✅ the default on Dokploy hosts |

#### Step 1 — Variant A: publish on loopback only

**Goal:** the container is reachable from the host itself and nowhere else.

```yaml
# compose.yaml
services:
  web:
    image: harbor.example.com/team/reports:1.4.2
    ports:
      - "127.0.0.1:18000:8000"      # host loopback 18000 -> container 8000
    restart: unless-stopped
```

```bash
docker compose up -d
sudo ss -ltnp 'sport = :18000'
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18000/health
```

```
LISTEN 0      4096       127.0.0.1:18000      0.0.0.0:*    users:(("docker-proxy",pid=53110,fd=7))
200
```

**What it means:** only processes on the host can connect. A host proxy then uses `proxy_pass http://127.0.0.1:18000;` (Nginx) or `ProxyPass / http://127.0.0.1:18000/` (Apache, for example in a vhost on 81 behind Traefik). Dokploy's Traefik **cannot** use this variant: inside its container, 127.0.0.1 is Traefik itself.

**Why this step (now):** it is the smallest safe change from the copy-pasted `"8000:8000"`: one IP prefix closes the UFW bypass.

**Next step:** if your proxy is Traefik in a container → Step 2 instead. Otherwise add the proxy route (P3) and stop here.

#### Step 2 — Variant B: join the proxy network with labels

**Goal:** no host port; Traefik reaches the container by its address on `dokploy-network` and routes by labels.

```yaml
# compose.yaml (deployed with "docker compose up -d" on the Dokploy host)
services:
  web:
    image: harbor.example.com/team/reports:1.4.2
    restart: unless-stopped
    networks:
      - dokploy-network
    labels:
      - traefik.enable=true
      - traefik.http.routers.reports.rule=Host(`reports.example.com`)
      - traefik.http.routers.reports.entrypoints=websecure
      - traefik.http.routers.reports.tls.certresolver=letsencrypt
      - traefik.http.services.reports.loadbalancer.server.port=8000
      - traefik.docker.network=dokploy-network

networks:
  dokploy-network:
    external: true
```

```bash
docker compose up -d
docker ps --filter name=reports --format 'table {{.Names}}\t{{.Ports}}\t{{.Networks}}'
sudo ss -ltnp 'sport = :8000'
curl -s -o /dev/null -w '%{http_code}\n' --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/health
```

```
NAMES             PORTS      NETWORKS
reports-web-1     8000/tcp   dokploy-network
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
200
```

**What it means:** `8000/tcp` without an arrow means the port is only exposed (metadata), not published: no host socket exists, as `ss` confirms. Traefik found the container through the Docker provider, built the router from the labels, and connects to the container's `dokploy-network` address on port 8000. `server.port` pins the port so Traefik never guesses; `traefik.docker.network` tells Traefik which network to use when the container is on several.

**Why this step (now):** with no host port there is nothing to firewall and nothing to collide with: twenty containers can all listen on 8000.

**Next step:** add the app to PORTS.md as "no host port", then the section 6 checklist. For apps deployed through Dokploy itself, use P6 instead of hand-written labels.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| no host port: no collisions, no UFW bypass, nothing to scan | labels are only read when the container is (re)created | every containerised web app on a Traefik host |
| every container can use its natural port | debugging needs tools inside the network (netshoot) | Variant A with a host Nginx/Apache proxy |
| routing config travels with the app (labels) | the container must listen on 0.0.0.0 inside, not 127.0.0.1 | Variant A for short local tests (18000–18999) |

**Verify:** `docker ps` shows no `->` in the Ports column (Variant B) or `127.0.0.1:` (Variant A); `ss` on the host shows no wildcard listener for the app; `curl --resolve` returns 200; from outside, `nc -vz HOSTIP 8000` times out.

**Rollback:** `docker compose down` removes the container and, with it, the labels and therefore the route. Keep the previous image tag so `docker compose up -d` with the old tag is your rollback (P12 and recipe R8).

**Gotchas:**

- Published ports bypass UFW (see the ops ladder's blind spots). Loopback or no publish at all.
- `expose:` restricts nothing; any container on the same network can reach every port the app listens on. Isolation comes from **which networks** a container joins: keep databases on a separate internal network (recipe R6).
- 502 from Traefik usually means the app listens on 127.0.0.1 **inside** the container, or `server.port` is wrong.
- In a Swarm **stack** (`docker stack deploy`), Traefik's Swarm provider reads labels under `deploy.labels`, not container `labels`.
- Do not set `"ip": "127.0.0.1"` in `/etc/docker/daemon.json` on a Dokploy host to make loopback the default: it also applies to Traefik's own `-p 80:80`, and every site goes down.

### P6 — Dokploy-native domains

**Level:** [L1 · Junior] to use the Domains tab, [L2 · Mid] to read and debug what it generates. **Study:** KodeKloud has no Dokploy course, so use the Dokploy docs ([docs](https://docs.dokploy.com/docs/core)) plus *Docker Certified Associate* → *Swarm Service Discovery* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Swarm-Service-Discovery/page)).

When the app is deployed **by Dokploy** (an Application or a Compose service), you never pick a host port. You tell Dokploy the hostname and the port the app listens on **inside the container**; Dokploy writes the Traefik router and service for you. This is the pattern the client's new app used, and it should be your default for anything new on web01.

```
Dokploy UI "Domains":  Host = app.example.com   Path = /   Container Port = 3000   HTTPS = on, Let's Encrypt
                               │                                    │
                               ▼                                    ▼
Traefik router:  Host(`app.example.com`) on websecure  ──►  service url http://APP-SERVICE-NAME:3000
                                                              (Swarm service DNS name on dokploy-network)
```

#### Step 1 — Find the port the app listens on

**Goal:** know the real listening port inside the container before you type it into Dokploy.

```bash
# The image's documented port (a hint, not proof)
docker image inspect harbor.example.com/client/app:2.3.0 --format '{{json .Config.ExposedPorts}}'
# Proof: what actually listens inside the running container (netshoot borrows its namespace)
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
```

```
{"3000/tcp":{}}
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511          0.0.0.0:3000      0.0.0.0:*
```

**What it means:** the app listens on 3000 on all addresses inside its container. That number goes into the **Container Port** field. It does not conflict with Dokploy's own panel on host port 3000, because the container has its own network namespace and nothing is published on the host.

**Why this step (now):** a wrong container port is the number one cause of Dokploy 502s ("Bad Gateway"). `EXPOSE` in a Dockerfile is documentation and can be wrong; the `ss` output cannot.

**Next step:** if the app listens on `127.0.0.1:3000` inside → fix the app's bind address first (an environment variable such as `HOST=0.0.0.0`), otherwise Traefik gets 502. Then → Step 2.

#### Step 2 — Add the domain and deploy

**Goal:** Dokploy generates the route and Traefik obtains the certificate.

| Field in Dokploy (Domains tab) | Value | What it becomes in Traefik |
|---|---|---|
| Host | app.example.com | the router rule's Host |
| Path | / | an extra PathPrefix when not `/` |
| Container Port | 3000 | the service's backend port |
| HTTPS | on | a router on `websecure` with TLS, plus an HTTP→HTTPS redirect on `web` |
| Certificate | Let's Encrypt | `certResolver: letsencrypt` |

Then click **Deploy** (Applications) or **Redeploy** (Compose: domain labels are injected only at deploy time).

```bash
# Applications: Dokploy writes a file-provider config per app (names differ by version)
sudo ls /etc/dokploy/traefik/dynamic/
sudo cat /etc/dokploy/traefik/dynamic/client-app-x1y2z3.yml
```

```
acme.json  client-app-x1y2z3.yml  dokploy.yml  legacy-apache.yml  middlewares.yml

http:
  routers:
    client-app-x1y2z3-router-1:
      rule: Host(`app.example.com`)
      service: client-app-x1y2z3-service-1
      middlewares:
        - redirect-to-https
      entryPoints:
        - web
    client-app-x1y2z3-router-websecure-1:
      rule: Host(`app.example.com`)
      service: client-app-x1y2z3-service-1
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
  services:
    client-app-x1y2z3-service-1:
      loadBalancer:
        servers:
          - url: http://client-app-x1y2z3:3000
        passHostHeader: true
```

**What it means:** this is the same router/service structure you wrote by hand for Apache in section 1, generated for you. The backend URL uses the Swarm service name, which Docker's embedded DNS resolves on `dokploy-network`. For Compose services, the same information lives in container labels instead (`docker inspect CONTAINER --format '{{json .Config.Labels}}'`). Read these files to learn and to debug; **do not edit them**, because Dokploy rewrites them on the next deploy. Your own routes go in your own files (like `legacy-apache.yml`).

**Why this step (now):** seeing the generated config turns Dokploy from a black box into "Traefik config I could have written myself", which is what you need when it breaks.

**Next step:** if the deployment finished and the generated config shows the right Host and port → Step 3. If the deploy failed → read the deployment log in Dokploy first (image pull, build error, registry credentials). If the backend URL carries the wrong port → correct Container Port and redeploy.

#### Step 3 — Verify the route

**Goal:** the app answers through Traefik with a real certificate, and has no host port.

```bash
curl -s -o /dev/null -w '%{http_code}\n' --resolve app.example.com:443:192.0.2.10 https://app.example.com/
docker service inspect client-app-x1y2z3 --format '{{json .Endpoint.Ports}}'
```

```
200
null
```

**What it means:** 200 through Traefik, and `null` published ports: the app exists only on the Docker network. That is the target state.

**Why this step (now):** it confirms the two properties that matter: reachable through the front door, unreachable around it.

**Next step:** section 6 checklist. If 404 → [Traefik 404 scenarios in module 26](26-playbook-containers-k8s.md); if 502 → back to Step 1.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| zero port management; certificates automatic | Dokploy owns the generated config; manual edits are overwritten | everything you deploy on a Dokploy host |
| rollbacks, logs and env in one UI | Compose domains need a redeploy to apply | apps built by GitLab CI and pushed to Harbor (recipe R8) |
| same model scales to more Dokploy servers | the "Ports" setting can still publish host ports if you misuse it | |

**Verify:** `curl --resolve` 200 with a Let's Encrypt issuer; `docker service inspect` shows no published ports; the app's container port matches `ss` inside the container.

**Rollback:** in Dokploy, remove the domain (route disappears) or redeploy a previous deployment from the Deployments list. Keep image tags immutable (commit SHA) so "previous" really means the previous code.

**Gotchas:**

- Do not add the same port under the application's advanced **Ports** settings "to make it work": that publishes it on the host (and, in Swarm's ingress mode, on every node), bypassing UFW. Domains need no published port.
- Two apps claiming the same Host rule: Traefik picks one by priority, silently. Search the dynamic folder and labels before reusing a hostname.
- Let's Encrypt needs public DNS pointing at the server and port 80 reachable from the internet; for internal-only names, use a custom certificate in Dokploy.
- Dokploy documentation: [docs.dokploy.com](https://docs.dokploy.com/).

### P7 — systemd apps behind a proxy

**Level:** [L2 · Mid]; the hardening options are [L3 · Senior]. **Study:** *Learning Linux Basics Course & Labs* → *Creating a SYSTEMD Service* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page)), gunicorn's deployment guide ([docs](https://gunicorn.org/deploy/)) and the [systemd reference](07-services-systemd.md).

Not everything belongs in a container. A Python, Node or Java app run by systemd is perfectly professional if it runs as its own user, listens privately, restarts on failure, logs to the journal and sits behind the proxy. The unit file is the whole deployment descriptor.

#### Step 1 — Create the user and the unit

**Goal:** a hardened service that listens on loopback (host proxy) or HOSTIP (containerised Traefik), or on a Unix socket.

```bash
sudo useradd --system --home-dir /srv/reports --shell /usr/sbin/nologin reports
sudoedit /etc/systemd/system/reports.service
```

```ini
# /etc/systemd/system/reports.service
[Unit]
Description=Reports app (gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
# gunicorn reports readiness to systemd (Type=notify); use Type=simple for servers that cannot
Type=notify
NotifyAccess=main
User=reports
Group=www-data
WorkingDirectory=/srv/reports/app
EnvironmentFile=/etc/reports/env
RuntimeDirectory=reports
# Choose ONE bind:
#   127.0.0.1:8001                    a proxy on the host (Nginx/Apache)
#   192.0.2.10:8001                   Dokploy's Traefik (container) + ufw allow in on docker_gwbridge
#   unix:/run/reports/gunicorn.sock   a proxy on the host, no TCP port at all
ExecStart=/srv/reports/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 \
          --forwarded-allow-ips=127.0.0.1 --access-logfile - reports.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=20
Restart=on-failure
RestartSec=3
# Hardening: the app may write only where it must
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/srv/reports/data

[Install]
WantedBy=multi-user.target
```

**What it means:** the service runs as `reports` with group `www-data` (so a Unix socket it creates can be shared with Nginx), gets a private `/run/reports` directory, restarts on crashes, and can write only to its data directory. Logs go to the journal (`journalctl -u reports`), which rotates them for you.

**Why this step (now):** the unit decides the bind address, the user and the restart behaviour, which are three of the six questions on the post-deployment checklist.

**Next step:** → Step 2, which also checks the unit with `systemd-analyze verify`. If you cannot decide on the bind yet, decide now: a proxy on the host → loopback or a socket; Dokploy's Traefik → HOSTIP plus the bridge firewall rule.

#### Step 2 — Start it and check the listener

**Goal:** the service runs, survives a reboot, and listens exactly where intended.

```bash
sudo systemd-analyze verify /etc/systemd/system/reports.service
sudo systemctl daemon-reload
sudo systemctl enable --now reports.service
systemctl status reports --no-pager | head -6
sudo ss -ltnp 'sport = :8001'
```

```
● reports.service - Reports app (gunicorn)
     Loaded: loaded (/etc/systemd/system/reports.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-28 11:20:04 UTC; 3s ago
   Main PID: 61002 (gunicorn)
      Tasks: 4 (limit: 9387)
LISTEN 0      2048       127.0.0.1:8001      0.0.0.0:*    users:(("gunicorn",pid=61005,fd=5),("gunicorn",pid=61004,fd=5),("gunicorn",pid=61002,fd=5))
```

**What it means:** `enabled` means it starts at boot; `active (running)` with `Type=notify` means gunicorn told systemd it is ready, not just that the process exists. The listener is on loopback only.

**Why this step (now):** you check the listener before adding the proxy so a later 502 cannot be blamed on the wrong layer.

**Next step:** if `active (running)` and the listener matches the bind you chose → Step 3. If the unit is `failed` → `journalctl -u reports -n 50` (missing venv, `Read-only file system` from `ProtectSystem`, port already taken). If it stays `activating` → the server does not send the readiness signal; use `Type=simple`.

#### Step 3 — Put the proxy in front

**Goal:** route the hostname to the app, choosing the snippet for your proxy and bind.

```nginx
# Nginx on the host, TCP
location / { proxy_pass http://127.0.0.1:8001; include proxy_params; }
# Nginx on the host, Unix socket
location / { proxy_pass http://unix:/run/reports/gunicorn.sock; include proxy_params; }
```

```apache
# Apache on the host (e.g. a *:81 vhost behind Traefik), TCP or Unix socket (Apache 2.4.7+)
ProxyPreserveHost On
ProxyPass        / http://127.0.0.1:8001/
# ProxyPass      / "unix:/run/reports/gunicorn.sock|http://localhost/"
ProxyPassReverse / http://127.0.0.1:8001/
```

```bash
# Traefik in a container: bind gunicorn to 192.0.2.10:8001, allow the bridge, then route to it
sudo ufw allow in on docker_gwbridge to any port 8001 proto tcp comment 'Traefik -> reports'
curl -s -o /dev/null -w '%{http_code}\n' --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/health
```

```
Rule added
Rule added (v6)
200
```

**What it means:** Ubuntu's `proxy_params` sets Host, X-Real-IP, X-Forwarded-For and X-Forwarded-Proto. A Unix socket needs no port at all and is invisible to the network, but only proxies on the same host can use it, which excludes Dokploy's Traefik.

**Why this step (now):** the app is proven private and healthy; the proxy is the last link.

**Next step:** PORTS.md (8001 or the socket path), section 6 checklist.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| no container layer; easy to debug with normal tools | dependencies installed on the host (venv, Node, JDK) | apps that are not containerised yet |
| journald logs, restart policy and hardening for free | one version per host unless you use template units (P12) | small internal services |
| Unix sockets avoid ports entirely | Traefik in a container cannot use loopback or sockets | as a migration step towards P6 |

**Verify:** `systemctl is-enabled reports` → `enabled`; `ss` shows the intended bind; `curl` through the proxy returns 200; `sudo systemctl kill -s KILL reports` followed by `systemctl status reports` shows it restarted (do this in a maintenance window).

**Rollback:** `sudo systemctl disable --now reports`, remove the proxy route, reload the proxy. The unit file can stay for later.

**Gotchas:**

- A socket path in `/tmp` breaks with `PrivateTmp=yes` (each side sees a different `/tmp`); use `/run/APP/`.
- Socket permissions: the proxy user (www-data) needs read/write on the socket; `Group=www-data` plus gunicorn's `--umask 007` (or `UMask=0007` in the unit) gives that.
- `ProtectSystem=strict` makes the whole filesystem read-only for the service; add every path it must write to `ReadWritePaths`, or it fails with `Read-only file system`.
- `systemd-analyze security reports.service` scores the unit's exposure and suggests further hardening.

### P8 — Multiple IP addresses

**Level:** [L3 · Senior]. **Study:** *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Configure IPv4/IPv6 Networking and Hostname Resolution* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)), then the [Network reference](02-network.md) for netplan.

If two servers both truly need **ports 80 and 443** (for example, a vendor appliance that must terminate its own HTTPS on the standard port next to Traefik), give the host a second IP address and bind each server to its own address. This is the only pattern where two different programs both own 80/443 on one machine.

```
203.0.113.10 ─NAT─► 192.0.2.10:80/443  Traefik (Dokploy)
203.0.113.11 ─NAT─► 192.0.2.11:80/443  Apache (vendor sites)
```

#### Step 1 — Add the address with netplan

**Goal:** a second address on the same interface, applied with an automatic safety net.

```yaml
# /etc/netplan/50-cloud-init.yaml (your file name may differ: ls /etc/netplan/)
network:
  version: 2
  ethernets:
    ens18:
      addresses:
        - 192.0.2.10/24
        - 192.0.2.11/24
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53]
```

```bash
sudo cp -a /etc/netplan /root/netplan.bak-$(date +%F)
sudo netplan generate                 # syntax check only
sudo netplan try --timeout 120        # applies, reverts automatically unless you confirm
ip -br addr show ens18
```

```
Do you want to keep these settings?

Press ENTER before the timeout to accept the new configuration

Changes will revert in 117 seconds
Configuration accepted.
ens18            UP             192.0.2.10/24 192.0.2.11/24 fe80::be24:11ff:fe4a:91c2/64
```

**What it means:** both addresses are live. `netplan try` is the safe way to change networking over SSH: if the change cuts you off, you cannot press Enter and it rolls back by itself. On AWS the equivalent is a secondary private IP on the ENI plus a second Elastic IP; Ubuntu does not always configure secondary IPs automatically, so add them in netplan too.

**Why this step (now):** without the address, nothing can bind to it (`Cannot assign requested address`).

**Next step:** → Step 2. If `netplan generate` complains about permissions, fix the file mode to 600 (netplan warns about world-readable files). If the file is `50-cloud-init.yaml`, read its header comment first: cloud-init may regenerate it, so either disable cloud-init's network config as that comment explains (`network: {config: disabled}` in `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg`) or check after the next reboot that the second address is still there.

#### Step 2 — Bind each server to its own address

**Goal:** no wildcard listener on 80/443 anywhere; each server owns its own IP:port pair.

```apache
# /etc/apache2/ports.conf
Listen 192.0.2.11:80
<IfModule ssl_module>
    Listen 192.0.2.11:443 https
</IfModule>
```

```bash
# Traefik must publish on 192.0.2.10 only (in Dokploy's container this is NOT a supported
# change: the publish is set when Dokploy creates the container, and updates may recreate it)
sudo ss -ltnp '( sport = :80 or sport = :443 )'
```

```
LISTEN 0      511        192.0.2.11:80        0.0.0.0:*    users:(("apache2",pid=70211,fd=3),...)
LISTEN 0      511        192.0.2.11:443       0.0.0.0:*    users:(("apache2",pid=70211,fd=4),...)
LISTEN 0      4096       192.0.2.10:80        0.0.0.0:*    users:(("docker-proxy",pid=70402,fd=7))
LISTEN 0      4096       192.0.2.10:443       0.0.0.0:*    users:(("docker-proxy",pid=70427,fd=7))
```

**What it means:** four sockets, four different IP:port pairs, no conflict. If **either** side still binds an IPv4 wildcard (`0.0.0.0:80`) or a dual-stack wildcard (`*:80` in `ss`, which is what Apache's plain `Listen 80` creates), the other side's specific IPv4 bind fails with "Address already in use": the wildcard covers every address. An IPv6-only `[::]:80` (docker-proxy's IPv6 listener is one) blocks only IPv6 binds of that port.

**Why this step (now):** binding is where this pattern succeeds or fails; DNS comes after.

**Next step:** if you see four specific listeners and no wildcard → Step 3. If either server fails with `Address already in use` → the other side still binds a wildcard; fix that bind first. If `Cannot assign requested address` → the IP is not on the interface (back to Step 1).

#### Step 3 — Point DNS and NAT at the right address

**Goal:** each hostname resolves to the public address that leads to its server.

```bash
dig +short shop.example.com app.example.com
curl -sI --resolve shop.example.com:443:192.0.2.11 https://shop.example.com/ | head -3
```

```
203.0.113.11
203.0.113.10
HTTP/1.1 200 OK
Server: Apache/2.4.58 (Ubuntu)
```

**What it means:** the vendor sites go to .11 (Apache), the Dokploy apps to .10 (Traefik). Each public IP needs its own NAT rule on the edge firewall.

**Why this step (now):** both servers are now independently reachable on standard ports, which is the whole point of P8.

**Next step:** document both addresses in PORTS.md, then the section 6 checklist.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| both servers keep standard ports and their own certificates | needs a second public IP and NAT rule (cost, paperwork) | an appliance or vendor stack that must own 443 itself |
| complete separation of the two front doors | Dokploy's Traefik publish must be changed, which Dokploy does not manage for you | a long transition where two edges must coexist |
| no proxy chaining | two places for certificates, logs and security rules | rarely: P3 is simpler almost every time |

**Verify:** `ss` shows only specific-address listeners on 80/443; `curl --resolve` against each IP returns the right server; `dig` returns the right public IP for each name.

**Rollback:** restore the netplan backup and `sudo netplan try`; revert `ports.conf` and the Traefik publish; restart both.

**Gotchas:**

- Wildcards break the pattern. docker-proxy's IPv6 `[::]:80` is IPv6-only, so it does not block Apache's IPv4 bind, but if you also serve IPv6, give each server its own IPv6 address and bind that too.
- Outgoing traffic still leaves from the primary address unless you add source-based routing.
- Apache starting before the second address exists fails at boot; netplan addresses are configured early, but check the order after the first reboot.

### P9 — TLS passthrough and SNI routing

**Level:** [L3 · Senior]. **Study:** *DevOps Pre-Requisite Course* → *SSL & TLS Basics* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)), then [Web, HTTP & TLS](18-web-http-tls.md) for SNI and `openssl s_client`.

Sometimes the proxy must **not** terminate TLS: the backend needs mutual TLS with client certificates, holds keys the proxy must not see, or is a legacy appliance with its own certificate. The proxy then reads only the SNI name in the TLS ClientHello (sent in clear text) and forwards the encrypted bytes untouched. This is also a valid finish for your Apache on 444 if you want Apache to keep its own certificates.

#### Step 1 — Add a TCP router with HostSNI

**Goal:** Traefik passes TLS for `legacy.example.com` straight to Apache:444 and terminates TLS itself for every other name.

```yaml
# /etc/dokploy/traefik/dynamic/passthrough.yml
tcp:
  routers:
    legacy-passthrough:
      entryPoints:
        - websecure
      rule: "HostSNI(`legacy.example.com`)"
      service: legacy-tls
      tls:
        passthrough: true
  services:
    legacy-tls:
      loadBalancer:
        servers:
          - address: "192.0.2.10:444"
```

```nginx
# Nginx equivalent (stream module: package libnginx-mod-stream if not loaded), in nginx.conf outside http {}
stream {
    map $ssl_preread_server_name $backend {
        legacy.example.com  192.0.2.10:444;
        default             127.0.0.1:8443;    # Nginx's own https server for everything else
    }
    server {
        listen 443;
        ssl_preread on;
        proxy_pass $backend;
    }
}
```

```bash
# Traefik (web01): install the TCP router and check that it loaded
sudo install -m 644 /root/passthrough.yml /etc/dokploy/traefik/dynamic/passthrough.yml
sleep 3; docker logs --since 1m dokploy-traefik 2>&1 | grep -iE 'error.*passthrough' || echo "passthrough.yml loaded without errors"

# Nginx variant (only on a host where Nginx is the edge): the stream module must be loaded first
ls /etc/nginx/modules-enabled/ | grep stream
sudo nginx -t && sudo systemctl reload nginx
```

```
passthrough.yml loaded without errors
50-mod-stream.conf
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**What it means:** Traefik's TCP routers on an entryPoint are evaluated before its HTTP routers, so this one catches `legacy.example.com` and every other SNI falls through to the normal HTTP routers. In Nginx, `ssl_preread` exposes the SNI as a variable without decrypting anything. HostSNI only works for TLS; for plain TCP the only possible host rule is the catch-all `` HostSNI(`*`) `` (optionally narrowed with `ClientIP`), which takes the whole entryPoint.

**Why this step (now):** the backend must already serve valid TLS on 444 (section 1, Step 8); passthrough only forwards it.

**Next step:** if Traefik's log shows no error for `passthrough.yml` → Step 2. If HTTPS for other names suddenly breaks → the TCP rule is too broad (for example `` HostSNI(`*`) ``); move the file out of the dynamic folder at once, then fix the rule.

#### Step 2 — Test the backend certificate through the proxy

**Goal:** the client sees Apache's certificate, not Traefik's.

```bash
openssl s_client -connect 192.0.2.10:443 -servername legacy.example.com </dev/null 2>/dev/null \
    | openssl x509 -noout -subject -issuer -enddate
```

```
subject=CN = legacy.example.com
issuer=C = US, O = Let's Encrypt, CN = R11
notAfter=Dec  2 07:11:40 2026 GMT
```

**What it means:** the certificate comes from Apache's certbot files, proving passthrough. Renewal is Apache's job again, and port 80 belongs to Traefik, so that certificate must be renewed with DNS-01 (section 1, "The certificate trap").

**Why this step (now):** with passthrough a misroute shows up as the wrong certificate, so the certificate is the test.

**Next step:** PORTS.md, section 6 checklist (renewal path!).

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| the backend keeps its keys, certificates and mTLS | no HTTP features: no headers, redirects, path rules or access logs with URLs for these names | mutual TLS with client certificates |
| end-to-end encryption to the app | the client IP is lost unless you add PROXY protocol on both sides | appliances that must present their own certificate |
| works for any TLS protocol, not only HTTPS | certificate renewal moves back to the backend | compliance rules forbidding TLS termination at the proxy |

**Verify:** `openssl s_client -servername` shows the backend's certificate for passthrough names and Traefik's for the others.

**Rollback:** delete `passthrough.yml`; the name falls back to whatever HTTP router matches (or Traefik's 404).

**Gotchas:**

- Apache sees every connection as coming from the Docker bridge. PROXY protocol fixes that (Apache `RemoteIPProxyProtocol On`; Traefik's PROXY protocol option for TCP services), but both sides must agree or every connection fails.
- An HTTP router and a passthrough TCP router for the same name: the TCP router wins on that entryPoint.
- HTTP/3 (QUIC on udp/443) cannot be passed through by SNI in the same way; clients fall back to TCP.

### P10 — Non-HTTP services

**Level:** [L1 · Junior] for private binds and SSH tunnels, [L3 · Senior] for Traefik TCP entryPoints. **Study:** *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Configure SSH Servers and Clients* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)), then the [SSH reference](09-ssh-remote-access.md).

Databases, caches, message brokers and SSH are not websites. The best port strategy for them is **no exposure**: bind them to loopback or a private network, reach them from apps on the same host or Docker network, and reach them yourself through an SSH tunnel.

#### Step 1 — Find services listening on every interface

**Goal:** a list of non-HTTP listeners that are reachable from the network.

```bash
# TCP listeners NOT bound to loopback
sudo ss -ltnpH | awk '$4 !~ /^(127\.|\[::1\]|\[::ffff:127)/ {print $4, $6}'
```

```
0.0.0.0:5432 users:(("postgres",pid=1022,fd=6))
*:6379 users:(("redis-server",pid=998,fd=6))
0.0.0.0:1883 users:(("mosquitto",pid=1110,fd=5))
*:22 users:(("sshd",pid=801,fd=3),("systemd",pid=1,fd=120))
```

**What it means:** PostgreSQL, Redis and Mosquitto accept connections from anywhere that can route to this host. UFW may block them, but one `ufw disable` during troubleshooting and they are on the internet. Fix the bind, not just the firewall.

**Why this step (now):** you cannot protect what you have not listed.

**Next step:** if only SSH and the edge proxy appear → skip to Step 3. If databases, caches or brokers appear → Step 2.

#### Step 2 — Bind each service privately

**Goal:** every data service listens on loopback or a private address only.

```bash
# PostgreSQL (Ubuntu 24.04 = 16, 22.04 = 14): postgresql.conf and pg_hba.conf
sudo grep -nE "^\s*listen_addresses" /etc/postgresql/16/main/postgresql.conf
#   listen_addresses = 'localhost'                  (or 'localhost,192.0.2.10' for app hosts)
#   pg_hba.conf: host appdb app 192.0.2.0/24 scram-sha-256
sudo systemctl restart postgresql                   # listen_addresses needs a restart, not a reload

# Redis: /etc/redis/redis.conf (Ubuntu's default is already loopback)
sudo grep -nE '^(bind|protected-mode|requirepass)' /etc/redis/redis.conf

# Mosquitto: /etc/mosquitto/conf.d/local.conf
#   listener 1883 127.0.0.1
sudo ss -ltnp '( sport = :5432 or sport = :6379 or sport = :1883 )'
```

```
60:listen_addresses = 'localhost'
75:bind 127.0.0.1 -::1
94:protected-mode yes
LISTEN 0      200        127.0.0.1:5432      0.0.0.0:*    users:(("postgres",pid=8121,fd=6))
LISTEN 0      511        127.0.0.1:6379      0.0.0.0:*    users:(("redis-server",pid=998,fd=6))
LISTEN 0      100        127.0.0.1:1883      0.0.0.0:*    users:(("mosquitto",pid=8302,fd=5))
```

**What it means:** all three are now private. Containerised databases follow the same rule: no `ports:` at all, and a separate internal Docker network shared only with the app (recipe R6).

**Why this step (now):** binding privately removes the risk even if the firewall is disabled or misconfigured.

**Next step:** if every data service now shows a loopback or private bind → Step 3 for human access. If a service fails to start after the change → its log names the bad address; if an app on another host can no longer connect → add that host's private address to the bind and a matching `pg_hba.conf` line.

#### Step 3 — Reach them through an SSH tunnel

**Goal:** you (or a DBA) can use a GUI client without opening the database port.

```bash
# On your laptop: local port 15432 -> the server's loopback 5432, via SSH
ssh -N -L 15432:127.0.0.1:5432 admin@192.0.2.10
# In another terminal on the laptop
psql -h 127.0.0.1 -p 15432 -U app appdb -c 'select current_user, inet_server_addr();'
```

```
 current_user | inet_server_addr
--------------+------------------
 app          | 127.0.0.1
(1 row)
```

**What it means:** the database saw a local connection; the network saw only SSH, which is key-only and allow-listed. For a container database with no published port, tunnel to its container IP, or use `docker exec -it CONTAINER psql`.

**Why this step (now):** it removes the usual excuse for exposing database ports ("the developers need DBeaver").

**Next step:** only if a remote system (not a human) must reach the service → consider a Traefik TCP entryPoint (below) or a VPN; otherwise done.

**Traefik TCP entryPoints.** Traefik can route raw TCP and UDP on extra entryPoints (for example `:5432` with a `` HostSNI(`*`) `` TCP router, or MQTT on 8883 with TLS and real SNI routing). That requires a new entryPoint in the static config and a new published port on the Traefik container, which on a Dokploy host means changing a container Dokploy manages; recent Dokploy versions offer additional Traefik port mappings in their settings. Do it only when a remote system must connect, always with TLS and an allow-list.

**SSH.** Moving SSH from 22 to 2222 is port shifting for log noise, not for security: scanners find it within hours. Key-only authentication and an allow-list are the actual protection. On Ubuntu 24.04 SSH is socket-activated, so after changing `Port` in `sshd_config` you must run `sudo systemctl daemon-reload` and `sudo systemctl restart ssh.socket`; restarting only `ssh.service` keeps listening on the old port. Keep your current session open and test the new port from a second terminal before you log out.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| nothing to attack from the network | humans need a tunnel or VPN | every database, cache and broker by default |
| no firewall rule to forget | apps on other hosts need a private network path | exposure only for system-to-system traffic, with TLS and allow-lists |

**Verify:** the Step 1 command lists only services you intend to be reachable (SSH, the edge proxy); `nc -vz HOSTIP 5432` from another host fails.

**Rollback:** restore the previous `listen_addresses` / `bind` from the config backup and restart the service.

**Gotchas:**

- Docker apps that connect to a database on the host use the bridge gateway or HOSTIP, not 127.0.0.1; the database must then listen on that address and `pg_hba.conf` must allow the bridge subnet.
- Redis `protected-mode` only protects a Redis with no password and no explicit bind; do not rely on it.
- UDP services (DNS, syslog, WireGuard) need `ss -lunp`, not `-ltnp`.

### P11 — Kubernetes Services and Ingress

**Level:** [L3 · Senior], core CKA material. **Study:** *Certified Kubernetes Administrator (CKA)* — Networking → *Ingress* ([lesson](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page)), then [Learn: Kubernetes](31-learn-kubernetes.md).

In Kubernetes the port juggling disappears, because every Pod gets **its own IP address and network namespace**. Ten pods on one node can all listen on 8080 without any conflict, exactly like ten containers on `dokploy-network`. A Service gives a set of pods one stable virtual IP and DNS name, and only the edge (an Ingress controller, a Gateway, or a LoadBalancer) needs ports 80/443 on the outside.

| Service type / mechanism | What it opens | Typical use |
|---|---|---|
| ClusterIP (default) | a virtual IP inside the cluster only | every app; the Ingress/Gateway talks to it |
| NodePort | a port in 30000–32767 on **every** node | bare-metal edge, debugging, external LBs that target nodes |
| LoadBalancer | an external IP from a cloud LB, or from MetalLB on-prem | the Ingress controller's or Gateway's own Service |
| Ingress / Gateway API (HTTPRoute) | hostname and path routing on 80/443 | public HTTP apps: the P3 of Kubernetes |
| hostPort / hostNetwork | the pod binds the node's real ports | ingress controllers as a DaemonSet on bare metal; avoid for apps |

#### Step 1 — Expose the app with a ClusterIP Service

**Goal:** a stable in-cluster address for the pods.

```bash
kubectl create deployment shop --image=harbor.example.com/shop/api:1.4.2 --port=8000 --replicas=2
kubectl expose deployment shop --port=80 --target-port=8000
kubectl get svc shop -o wide
kubectl get endpointslices -l kubernetes.io/service-name=shop
```

```
NAME   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE   SELECTOR
shop   ClusterIP   10.96.142.17    <none>        80/TCP    5s    app=shop
NAME         ADDRESSTYPE   PORTS   ENDPOINTS                 AGE
shop-x7k2p   IPv4          8000    10.244.1.23,10.244.2.31   5s
```

**What it means:** the Service listens on port 80 of its cluster IP and forwards to port 8000 (`targetPort`) on two pod IPs. `port` is what clients use, `targetPort` is what the container listens on, and `containerPort` in the pod spec is documentation; mixing them up is a classic CKA trap and the Kubernetes version of a wrong Dokploy "Container Port".

**Why this step (now):** no endpoints here means the selector or readiness is wrong, and no Ingress can fix that.

**Next step:** if ENDPOINTS is empty → check labels and readiness ([Kubernetes incidents](26-playbook-containers-k8s.md)). Otherwise → Step 2.

#### Step 2 — Route a hostname with Ingress or Gateway API

**Goal:** `shop.example.com` reaches the Service through the cluster's edge.

```yaml
# Ingress (needs an Ingress controller installed)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
spec:
  ingressClassName: nginx
  tls:
    - hosts: [shop.example.com]
      secretName: shop-tls
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: shop
                port:
                  number: 80
---
# Gateway API equivalent (needs a Gateway implementation and a Gateway named "web")
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: shop
spec:
  parentRefs:
    - name: web
  hostnames: ["shop.example.com"]
  rules:
    - backendRefs:
        - name: shop
          port: 80
```

```bash
kubectl apply -f shop-route.yaml
kubectl get ingress shop
curl -s -o /dev/null -w '%{http_code}\n' --resolve shop.example.com:443:192.0.2.50 https://shop.example.com/
```

```
NAME   CLASS   HOSTS              ADDRESS       PORTS     AGE
shop   nginx   shop.example.com   192.0.2.50    80, 443   20s
200
```

**What it means:** the controller (listening on 192.0.2.50) routes by hostname, exactly like Traefik on web01. The community ingress-nginx project is retired: best-effort maintenance ended in March 2026, and there are no further releases or security fixes (existing images and Helm charts stay downloadable, so old clusters keep running). The example above still shows it because so many existing clusters use it; for new clusters choose a Gateway API implementation or another maintained Ingress controller (the Kubernetes blog's "Ingress NGINX Retirement" post, November 2025, explains the options). Gateway API is also part of the CKA curriculum.

**Why this step (now):** the Service works (Step 1), so a failure here is the edge layer.

**Next step:** if the Ingress (or HTTPRoute) has an address and `curl` returns 200 → section 6. If ADDRESS stays empty → Step 3. If 404 → the controller class or the host does not match. If 503 → the Service has no endpoints (back to Step 1).

#### Step 3 — Get traffic into an on-prem cluster

**Goal:** the controller's Service gets a real LAN address that DNS and the edge NAT can point at.

```yaml
# MetalLB (Layer 2 mode): hand out 192.0.2.50-59 to LoadBalancer Services
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: lan-pool
  namespace: metallb-system
spec:
  addresses:
    - 192.0.2.50-192.0.2.59
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: lan-l2
  namespace: metallb-system
spec:
  ipAddressPools: [lan-pool]
```

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller
```

```
NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx-controller   LoadBalancer   10.96.20.110   192.0.2.50    80:31080/TCP,443:31443/TCP   12d
```

**What it means:** MetalLB answered ARP for 192.0.2.50 from one node, so the LAN (and the edge NAT) can reach 80/443 without NodePorts in URLs. The `80:31080` notation shows the NodePort that also exists underneath. Without MetalLB on bare metal, the choices are NodePort (users or an external load balancer use 30000–32767) or running the controller with `hostNetwork`/`hostPort` on chosen nodes.

**Why this step (now):** it is the last hop between the cluster and users, and the one that has no automatic answer on-prem.

**Next step:** DNS for the hostnames → 192.0.2.50 (or its public NAT address), then section 6.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| no port conflicts between apps, ever | a whole platform to run and upgrade | many services, several nodes, need for self-healing and rolling updates |
| declarative routing and rollouts | on-prem needs MetalLB or NodePorts for the edge | teams already on the CKA track |
| the same YAML on any cluster | more layers to debug (pod → Service → Ingress → LB) | |

**Verify:** `kubectl get endpointslices` lists pod IPs; `kubectl get ingress` (or `httproute`) shows the address; `curl --resolve` returns 200.

**Rollback:** `kubectl rollout undo deployment shop` for the app; `kubectl delete -f shop-route.yaml` for the route.

**Gotchas:**

- A node that also runs Apache or Nginx on 80/443 cannot host a `hostNetwork` ingress controller: your Apache-vs-Traefik incident, again, one level down.
- NodePorts (30000–32767) sit just below the Linux ephemeral range (32768–60999). Tuning guides that widen `net.ipv4.ip_local_port_range` (to 1024–65535, for example) make the two overlap, and then a NodePort can be taken by an outgoing connection's source port; keep the ranges apart on nodes.
- `externalTrafficPolicy: Local` keeps the client source IP but only sends traffic to nodes running a pod.

### P12 — Blue/green on two ports

**Level:** [L3 · Senior]. **Study:** *Docker Certified Associate* — Docker Swarm → *Scaling, Rolling Updates and Rollbacks* ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)), the same idea done by an orchestrator, then [Learn: CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

Two copies of the app run side by side on two ports (blue on 8001, green on 8002). The proxy points at one of them. To release, start the new version on the idle port, test it directly, switch the proxy, let the old one drain, then stop it. Rollback is switching back. It is port shifting used on purpose, for zero downtime.

#### Step 1 — Run blue and green from one template unit

**Goal:** one unit file, two instances, the port given by the instance name.

```ini
# /etc/systemd/system/reports@.service  (%i = the port)
[Unit]
Description=Reports app on port %i
After=network-online.target

[Service]
User=reports
Group=www-data
WorkingDirectory=/srv/reports/releases/%i/app
ExecStart=/srv/reports/releases/%i/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:%i reports.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Blue (8001) is live. Deploy the new release into /srv/reports/releases/8002, then:
sudo systemctl daemon-reload
sudo systemctl start reports@8002
curl -s http://127.0.0.1:8002/health; echo
```

```
{"status":"ok","version":"1.5.0"}
```

**What it means:** green runs version 1.5.0 next to blue, invisible to users. Test it as hard as you like now: it has no traffic.

**Why this step (now):** the new version must be proven healthy **before** it receives a single user request.

**Next step:** if healthy → Step 2. If not → `sudo systemctl stop reports@8002`; users never noticed.

#### Step 2 — Switch the proxy upstream

**Goal:** move traffic from 8001 to 8002 with a graceful reload.

```nginx
# /etc/nginx/conf.d/reports-upstream.conf (the only file the switch touches)
upstream reports_backend {
    server 127.0.0.1:8002;     # was 127.0.0.1:8001
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -s --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/health; echo
```

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
{"status":"ok","version":"1.5.0"}
```

**What it means:** Nginx's reload starts new workers with the new upstream and lets old workers finish their requests. With Traefik, change the `url` in the service's file (or use a weighted service to shift traffic gradually, e.g. 90/10 for a canary); the file provider applies it within seconds.

**Why this step (now):** the switch is a single-line, reversible change. That is what makes the release safe.

**Next step:** if the health check through the proxy shows the new version and the proxy log shows 2xx → Step 3. If not, or errors rise → point the upstream back at 8001 and reload; blue never stopped, so this is an instant rollback.

#### Step 3 — Drain and stop blue

**Goal:** stop the old version only after its last request finished.

```bash
# Established connections still on blue (should fall to 0 within the proxy's keepalive time)
sudo ss -Htn state established '( sport = :8001 )' | wc -l
sudo systemctl stop reports@8001
```

```
0
```

**What it means:** no client is still talking to blue, so stopping it drops nothing. Keep its release directory: it is your rollback.

**Why this step (now):** stopping blue immediately after the switch would cut long requests and downloads in the middle.

**Next step:** next release goes to 8001 (the idle port). Record both ports in PORTS.md as one app.

**Pros, cons and when to use**

| Pros | Cons | When to use |
|---|---|---|
| zero downtime; instant rollback (switch back) | two copies use twice the memory during the release | apps that cannot take a maintenance window |
| the new version is tested in production before users see it | database migrations must work for both versions at once | systemd apps (P7) without an orchestrator |
| a trivial, auditable change in the proxy | background jobs and crons can run twice | Traefik weighted services for canaries |

**Verify:** the health endpoint through the proxy shows the new version; the proxy's logs show 2xx; blue has no established connections before you stop it.

**Rollback:** start blue (`sudo systemctl start reports@8001`) if stopped, point the upstream back at 8001, `nginx -t && systemctl reload nginx`.

**Gotchas:**

- Schema changes must be "expand, then contract": add columns in one release, remove old ones in a later release, so both versions work against the same database.
- In-memory sessions are lost on the switch; use a shared session store (Redis, database).
- Dokploy and Kubernetes do the same thing for you with rolling updates (start new, health-check, stop old); this pattern is how it works underneath.

---

## 4. Deployment recipes

> 📚 **Study path:** 1) Note: section 3 of this module, because every recipe names the patterns it combines (a quick refresher before you build) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD → *Creating a SYSTEMD Service* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page)) for R3–R5 · 3) KodeKloud: *Docker Training Course for the Absolute Beginner* — *Docker Compose* ([lesson](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)) for R1 and R6 · 4) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab → *Docker Push* ([lesson](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page)) for R8 · 5) Docs: Dokploy ([docs](https://docs.dokploy.com/docs/core)) · 6) Video: KodeKloud *Docker Compose Tutorial | Docker for Beginners* (44 min, [YouTube](https://www.youtube.com/watch?v=iOGEBj7Ozak)) · 7) Practice: KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)) for R1 and R6, your homelab VM with Traefik for R3–R5 and R7, the CI/CD playground ([link](https://kodekloud.com/playgrounds/playground-ci-cd)) for R8.

**Level:** R1 is [L1 · Junior]; R2–R7 are [L2 · Mid]; R8 is [L3 · Senior]. Each recipe repeats its tag.

End-to-end recipes for web01 as it is now: **Traefik (Dokploy) owns 80/443**, Apache serves legacy vhosts on 81 behind it, UFW is active with `deny (incoming)`. Each recipe names the patterns it combines, so you can look up the reasoning in section 3. Where a recipe has an "Apache-on-81 variant", it means: add a vhost on `*:81` and a router to `legacy-apache.yml`, exactly as in section 1.

| Recipe | Patterns | Host port used |
|---|---|---|
| R1 Static site | P5 (or P2 + P3) | none |
| R2 PHP application | P2 + P3 (or P6) | none new (Apache 81) |
| R3 Python with gunicorn and systemd | P7 + P3 | 8001 on HOSTIP, bridge only |
| R4 Node.js with systemd | P7 + P3 | 8010 on HOSTIP, bridge only |
| R5 Java and Tomcat | P7 + P3 (or P6) | 8020 on HOSTIP, bridge only |
| R6 WordPress with Docker Compose | P5 + P10 | none |
| R7 Internal admin tool on a custom port | P1 | 9401, office only |
| R8 GitLab CI deploy to Dokploy | P6 | none |

### R1 — Static site

**Level:** [L1 · Junior]. A good first recipe: one container, no app server, no database.

A documentation site (`docs.example.com`) built as plain HTML. No app server, so the only question is which web server serves the files.

#### Step 1 — Put the files in a versioned directory

**Goal:** an immutable release directory and a `current` symlink you can flip back.

```bash
sudo mkdir -p /srv/docs/releases/2026-09-28 && sudo chown -R "$USER": /srv/docs
rsync -a ./public/ /srv/docs/releases/2026-09-28/
ln -sfn /srv/docs/releases/2026-09-28 /srv/docs/current
ls -l /srv/docs/
```

```
lrwxrwxrwx 1 deploy deploy   29 Sep 28 12:01 current -> /srv/docs/releases/2026-09-28
drwxr-xr-x 3 deploy deploy 4096 Sep 28 12:01 releases
```

**What it means:** the web server will serve `/srv/docs/current`. A new release is a new directory plus one `ln -sfn`; rollback is pointing the link back.

**Why this step (now):** separating "upload" from "go live" makes both the release and the rollback atomic.

**Next step:** if `current` points at the new release → Step 2. If the files landed in `releases/DATE/public/` → you dropped the trailing slash on `./public/`; fix the copy and re-link.

#### Step 2 — Serve it with an nginx container on dokploy-network

**Goal:** a tiny read-only container, no host port, routed by Traefik.

```yaml
# /srv/docs/compose.yaml
services:
  web:
    image: nginx:stable-alpine          # in production pin the exact current stable tag (hub.docker.com/_/nginx)
    restart: unless-stopped
    read_only: true
    tmpfs: [/var/cache/nginx, /var/run]
    volumes:
      - /srv/docs/current:/usr/share/nginx/html:ro
    networks: [dokploy-network]
    labels:
      - traefik.enable=true
      - traefik.http.routers.docs.rule=Host(`docs.example.com`)
      - traefik.http.routers.docs.entrypoints=websecure
      - traefik.http.routers.docs.tls.certresolver=letsencrypt
      - traefik.http.services.docs.loadbalancer.server.port=80
networks:
  dokploy-network:
    external: true
```

```bash
cd /srv/docs && docker compose up -d
curl -s -o /dev/null -w '%{http_code}\n' --resolve docs.example.com:443:192.0.2.10 https://docs.example.com/
```

```
200
```

**What it means:** Traefik serves the site with its own certificate; the container has no host port and cannot write to its filesystem. The bind mount points at the `current` symlink **as resolved when the container starts**, so after flipping the link run `docker compose restart web`.

**Why this step (now):** it adds a site without touching Apache or any port.

**Next step:** → Step 3. Apache-on-81 variant: a vhost on `*:81` with `DocumentRoot /srv/docs/current` (P2) and a `docs` router in `legacy-apache.yml`; no container needed.

#### Step 3 — Check caching and the 404 page

**Goal:** static assets are cacheable, missing pages return a real 404.

```bash
R='--resolve docs.example.com:443:192.0.2.10'
curl -sI $R https://docs.example.com/assets/site.css | grep -iE '^(HTTP|cache-control|etag|last-modified)'
curl -s $R -o /dev/null -w '%{http_code}\n' https://docs.example.com/no-such-page
```

```
HTTP/2 200
etag: "6aba570a-4b1c"
last-modified: Mon, 28 Sep 2026 12:01:14 GMT
404
```

**What it means:** ETag and Last-Modified let browsers revalidate cheaply; add `Cache-Control` for fingerprinted assets through a small nginx config if the site needs it. Unknown paths return 404, not 200 with the home page.

**Why this step (now):** these two are what users and search engines notice first about a static site.

**Next step:** section 6 checklist.

| Pros | Cons | When to use |
|---|---|---|
| no app server, almost nothing to break | the container must be restarted after a release (symlink resolution) | docs, landing pages, built SPAs |
| releases and rollbacks are a symlink flip | Apache variant shares Apache's fate | |

**Verify:** `curl --resolve` 200 for `/`, 404 for a missing page, correct certificate issuer.

**Rollback:** `ln -sfn /srv/docs/releases/PREVIOUS /srv/docs/current && docker compose restart web`; remove the site entirely with `docker compose down`.

**Gotchas:** a bind mount of a symlink follows the target at start time only; `read_only: true` needs the tmpfs mounts shown, or nginx fails to start; SPAs need `try_files $uri /index.html` in a custom nginx config.

### R2 — PHP application

**Level:** [L2 · Mid]. **Study:** [Learn: web servers & proxies](29-learn-webservers-proxies.md), the Apache in-depth section (php-fpm and `proxy_fcgi`).

A PHP app (`crm.example.com`). On web01, Apache on 81 already runs PHP sites, so the natural home is a new vhost with its own php-fpm pool. The containerised alternative is a Dokploy Application from a `php:8.3-apache` based image with Container Port 80 (P6).

#### Step 1 — Create a dedicated php-fpm pool

**Goal:** the app runs PHP as its own user, isolated from the other sites.

```bash
# Ubuntu 24.04 ships PHP 8.3 (22.04: 8.1; adjust paths)
sudo apt install php8.3-fpm php8.3-mysql php8.3-xml php8.3-mbstring
sudo useradd --system --home-dir /srv/crm --shell /usr/sbin/nologin crm
sudoedit /etc/php/8.3/fpm/pool.d/crm.conf
```

```ini
; /etc/php/8.3/fpm/pool.d/crm.conf
[crm]
user = crm
group = crm
listen = /run/php/php8.3-fpm-crm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 4
php_admin_value[upload_max_filesize] = 20M
php_admin_value[post_max_size] = 22M
```

```bash
sudo php-fpm8.3 -t && sudo systemctl reload php8.3-fpm
ls -l /run/php/php8.3-fpm-crm.sock
```

```
[28-Sep-2026 12:20:01] NOTICE: configuration file /etc/php/8.3/fpm/php-fpm.conf test is successful
srw-rw---- 1 www-data www-data 0 Sep 28 12:20 /run/php/php8.3-fpm-crm.sock
```

**What it means:** a socket that Apache (www-data) can use, and PHP code that runs as `crm`, so a bug in this app cannot write to the shop's files.

**Why this step (now):** the pool is the app's process boundary; the vhost only points at it.

**Next step:** if the test succeeds and the socket exists with group `www-data` → Step 2. If `php-fpm8.3 -t` fails → fix the pool file line it names. If the socket is missing → `journalctl -u php8.3-fpm -n 20`.

#### Step 2 — Add the vhost on 81

**Goal:** Apache passes `.php` requests to the pool and knows the client used HTTPS.

```apache
# /etc/apache2/sites-available/crm.example.com.conf
<VirtualHost *:81>
    ServerName crm.example.com
    DocumentRoot /srv/crm/app/public
    <Directory /srv/crm/app/public>
        AllowOverride All
        Require all granted
    </Directory>
    <FilesMatch "\.php$">
        SetHandler "proxy:unix:/run/php/php8.3-fpm-crm.sock|fcgi://localhost"
    </FilesMatch>
    SetEnvIf X-Forwarded-Proto "^https$" HTTPS=on
    ErrorLog ${APACHE_LOG_DIR}/crm-error.log
    CustomLog ${APACHE_LOG_DIR}/crm-access.log combined
</VirtualHost>
```

```bash
sudo a2enmod proxy_fcgi setenvif
sudo a2ensite crm.example.com
sudo apache2ctl configtest && sudo systemctl reload apache2
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: crm.example.com' -H 'X-Forwarded-Proto: https' http://127.0.0.1:81/
```

```
Syntax OK
200
```

**What it means:** the app answers through Apache on 81. `SetEnvIf ... HTTPS=on` makes PHP's `$_SERVER['HTTPS']` correct behind Traefik, which most frameworks use to build URLs and secure cookies.

**Why this step (now):** test Apache alone before adding Traefik, so each layer is proven separately.

**Next step:** if Apache returns 200 (or the app's own redirect) → Step 3. If 503 → Apache cannot use the socket (path or permissions). If you get PHP source code as plain text → `proxy_fcgi` is not enabled or the `FilesMatch` block is missing.

#### Step 3 — Route it through Traefik

**Goal:** `crm.example.com` works over HTTPS for users.

```bash
# Add a router "crm-apache" (websecure, Host crm.example.com, certResolver letsencrypt,
# service legacy-apache) and add the name to legacy-apache-http's rule in legacy-apache.yml
sudoedit /etc/dokploy/traefik/dynamic/legacy-apache.yml
curl -s -o /dev/null -w '%{http_code}\n' --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/
```

```
200
```

**What it means:** the existing `legacy-apache` service carries the new site; no new port, no new firewall rule.

**Why this step (now):** last link; everything behind it is proven.

**Next step:** section 6 checklist (PHP logs: Apache error log plus `journalctl -u php8.3-fpm`).

| Pros | Cons | When to use |
|---|---|---|
| reuses the running Apache and its firewall rule | PHP version shared by all pools on the host | existing PHP sites, quick additions |
| per-app user isolation with fpm pools | Apache stays a dependency you must keep patched | until the app is containerised (P6) |

**Verify:** `curl --resolve` 200; a page that prints `$_SERVER['HTTPS']` shows `on`; uploads near 20 MB succeed.

**Rollback:** `sudo a2dissite crm.example.com`, reload Apache, remove the router lines; the pool can be removed with its file and a php-fpm reload.

**Gotchas:** `mod_php` and php-fpm cannot both handle the same files (disable `php8.3` module if you switch to fpm and `mpm_event`); a Unix socket in the wrong group gives `Permission denied` and Apache returns 503; framework URL settings (`APP_URL`, `siteurl`) must be the HTTPS name without a port.

### R3 — Python with gunicorn and systemd

**Level:** [L2 · Mid]. **Study:** gunicorn's deployment guide ([docs](https://gunicorn.org/deploy/)) and pattern P7 above.

A Django or Flask app (`reports.example.com`) run by systemd (P7), reached by Dokploy's Traefik in its container. The unit is the one from P7; the differences are the bind address and the firewall rule.

#### Step 1 — Install the release and the unit

**Goal:** a virtualenv-based release and a unit bound to HOSTIP:8001.

```bash
sudo -u reports python3 -m venv /srv/reports/venv
sudo -u reports /srv/reports/venv/bin/pip install -r /srv/reports/app/requirements.txt gunicorn
# Unit from P7 with:  --bind 192.0.2.10:8001 --forwarded-allow-ips=172.18.0.0/16
sudoedit /etc/systemd/system/reports.service
sudo systemctl daemon-reload && sudo systemctl enable --now reports
sudo ss -ltnp 'sport = :8001'
```

```
LISTEN 0      2048      192.0.2.10:8001      0.0.0.0:*    users:(("gunicorn",pid=61005,fd=5),("gunicorn",pid=61002,fd=5))
```

**What it means:** gunicorn listens on the host address Traefik can reach, and trusts `X-Forwarded-*` headers only from the Docker bridge range. (`--forwarded-allow-ips` accepts networks in recent gunicorn versions; on older ones list the exact proxy IP.)

**Why this step (now):** the bind decides whether the container proxy can reach the app at all.

**Next step:** if `ss` shows `192.0.2.10:8001` → Step 2. If the unit failed → `journalctl -u reports -n 50`; the usual causes are a package missing from the venv or a writable path not listed in `ReadWritePaths`.

#### Step 2 — Firewall and route

**Goal:** only Traefik reaches 8001; users reach `reports.example.com`.

```bash
sudo ufw allow in on docker_gwbridge to any port 8001 proto tcp comment 'Traefik -> reports'
# /etc/dokploy/traefik/dynamic/reports.yml: router reports (websecure, certResolver letsencrypt)
# -> service url http://192.0.2.10:8001  (full YAML in P3, Step 2)
sudoedit /etc/dokploy/traefik/dynamic/reports.yml
curl -s -o /dev/null -w '%{http_code}\n' --resolve reports.example.com:443:192.0.2.10 https://reports.example.com/health
```

```
Rule added
Rule added (v6)
200
```

**What it means:** routed and private. Django additionally needs `ALLOWED_HOSTS = ['reports.example.com']`, `CSRF_TRUSTED_ORIGINS = ['https://reports.example.com']` and `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.

**Why this step (now):** firewall before route, so the route never points at an unreachable port.

**Next step:** if `curl` returns 200 → Step 3. If 502 or a timeout → the bind or the UFW rule is wrong; repeat section 1, Step 9's netshoot test against port 8001. If Django answers 400 → `ALLOWED_HOSTS`.

#### Step 3 — Prove restart and timeout behaviour

**Goal:** the app comes back after a crash, and slow requests behave predictably.

```bash
sudo systemctl kill -s KILL reports && sleep 5 && systemctl is-active reports
journalctl -u reports --since '2 min ago' --no-pager | grep -E 'exited|Scheduled restart|Started'
```

```
active
Sep 28 12:41:07 web01 systemd[1]: reports.service: Main process exited, code=killed, status=9/KILL
Sep 28 12:41:10 web01 systemd[1]: reports.service: Scheduled restart job, restart counter is at 1.
Sep 28 12:41:11 web01 systemd[1]: Started reports.service - Reports app (gunicorn).
```

**What it means:** `Restart=on-failure` works. Remember gunicorn's default 30-second worker timeout: a slower endpoint shows `WORKER TIMEOUT` in this journal and a 502 in Traefik; fix the endpoint or raise `--timeout` deliberately.

**Why this step (now):** you want to discover restart behaviour now, not during the first real crash. Do it in a quiet moment; it drops in-flight requests.

**Next step:** section 6 checklist.

| Pros | Cons | When to use |
|---|---|---|
| simple, debuggable, journald logs | Python and system libraries on the host | apps not yet containerised |
| fast deploys (`pip install`, restart) | one firewall rule per app port | small internal apps |

**Verify:** `ss` shows `192.0.2.10:8001`; `nc -vz 192.0.2.10 8001` from an office machine times out; `curl --resolve` 200; Django admin login works over HTTPS (CSRF settings).

**Rollback:** keep the previous release directory and venv; point the unit's `WorkingDirectory`/`ExecStart` back and restart, or use the blue/green layout of P12.

**Gotchas:** binding `0.0.0.0` instead of HOSTIP also works but listens on every interface (including `docker_gwbridge` and any future NIC); `ReadWritePaths` must include media and upload directories.

### R4 — Node.js with systemd

**Level:** [L2 · Mid]. **Study:** *Learning Linux Basics Course & Labs* → *SYSTEMD Tools* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)).

A Node.js API (`api2.example.com`). Two traps on web01: Node apps default to **port 3000, which is Dokploy's panel on this host**, and many tutorials say "run it with pm2 as root".

#### Step 1 — Choose the port and see the trap

**Goal:** understand why the default port fails here, then pick one from the convention.

```bash
sudo ss -ltnp 'sport = :3000'
sudo -u nodeapp node /srv/nodeapp/app/server.js
```

```
LISTEN 0      4096         0.0.0.0:3000       0.0.0.0:*    users:(("docker-proxy",pid=2402,fd=7))
node:events:497
      throw er; // Unhandled 'error' event
      ^

Error: listen EADDRINUSE: address already in use :::3000
```

**What it means:** Dokploy's published panel owns 3000, so the app dies at start. The fix is not to fight for 3000 but to give the app its own port from the 8001–8099 block, through an environment variable.

**Why this step (now):** reproducing the failure once teaches you to read `EADDRINUSE` as "who owns this port?", not as a Node bug.

**Next step:** → Step 2 with a port from the 8001–8099 block (8010 here). If 3000 happens to be free on your host (no Dokploy yet), move the app off it anyway: the next Dokploy install would collide with it.

#### Step 2 — Write the unit

**Goal:** Node supervised by systemd as an unprivileged user, on HOSTIP:8010.

```ini
# /etc/systemd/system/nodeapp.service
[Unit]
Description=Node API (api2.example.com)
After=network-online.target
Wants=network-online.target

[Service]
User=nodeapp
Group=nodeapp
WorkingDirectory=/srv/nodeapp/app
Environment=NODE_ENV=production
Environment=HOST=192.0.2.10
Environment=PORT=8010
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/srv/nodeapp/data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now nodeapp
sudo ss -ltnp 'sport = :8010'
sudo ufw allow in on docker_gwbridge to any port 8010 proto tcp comment 'Traefik -> nodeapp'
```

```
LISTEN 0      511       192.0.2.10:8010      0.0.0.0:*    users:(("node",pid=63110,fd=21))
Rule added
Rule added (v6)
```

**What it means:** the app reads `HOST` and `PORT` (check that your `server.js` does: `app.listen(process.env.PORT, process.env.HOST)`), runs as `nodeapp`, restarts on crashes and logs stdout/stderr to the journal. Express apps behind Traefik also need `app.set('trust proxy', 1)` for correct client IPs and secure cookies.

**Why this step (now):** systemd already is a process supervisor. Running pm2 as root under systemd adds a second supervisor, runs your app as root, keeps logs in `~/.pm2/logs` outside the journal (unrotated unless you add pm2-logrotate) and hides the real process from `systemctl status`. If a team insists on pm2 (cluster mode, its dashboard), run it as the app user (`pm2 startup systemd -u nodeapp --hp /srv/nodeapp`), never as root.

**Next step:** if `ss` shows `node` on `192.0.2.10:8010` → Step 3. If it listens on `:::8010` or `0.0.0.0:8010` → the app ignores `HOST`; fix its `listen()` call. If the unit restarts in a loop → `journalctl -u nodeapp -n 50`.

#### Step 3 — Route the Node app and test

**Goal:** `api2.example.com` reaches the app through Traefik.

```bash
# /etc/dokploy/traefik/dynamic/nodeapp.yml: router api2 -> http://192.0.2.10:8010 (P3 template)
sudoedit /etc/dokploy/traefik/dynamic/nodeapp.yml
curl -s --resolve api2.example.com:443:192.0.2.10 https://api2.example.com/health; echo
```

```
{"status":"ok","uptime":42.7}
```

**What it means:** routed, private, supervised.

**Why this step (now):** last link.

**Next step:** section 6 checklist.

| Pros | Cons | When to use |
|---|---|---|
| one supervisor (systemd), journald logs, hardening | Node version managed on the host | Node services not yet containerised |
| no root anywhere | cluster mode needs several instances or Node's cluster module | |

**Verify:** `systemctl status nodeapp` shows `node` as the main process (not pm2); `ss` shows 192.0.2.10:8010; `curl --resolve` 200.

**Rollback:** `sudo systemctl disable --now nodeapp`, delete `nodeapp.yml`, remove the UFW rule; previous release directories stay for a quick switch back.

**Gotchas:** `/usr/bin/node` from Ubuntu's archive is often older than the app needs; install a specific version (NodeSource or a tarball in `/opt/node-VERSION`) and put that path in `ExecStart`; `npm start` in `ExecStart` adds an extra process layer and swallows signals.

### R5 — Java and Tomcat

**Level:** [L2 · Mid]. **Study:** section 2 of this module (finding sleeping owners), because Tomcat's real problem here is its default ports.

A Java web app (`hr.example.com`) on Tomcat. Tomcat's HTTP connector defaults to **8080**, a port many things on a Dokploy host also want (Traefik's dashboard, Jenkins, other containers' habits), plus 8005 for its shutdown command.

#### Step 1 — Find the collision

**Goal:** see what Tomcat binds before it surprises you.

```bash
sudo apt install tomcat10            # Ubuntu 24.04; starts immediately on 8080
sudo ss -ltnp '( sport = :8080 or sport = :8005 or sport = :8009 )'
```

```
LISTEN 0      100                *:8080             *:*    users:(("java",pid=9120,fd=43))
LISTEN 0      1     [::ffff:127.0.0.1]:8005             *:*    users:(("java",pid=9120,fd=52))
```

**What it means:** the HTTP connector listens on every address on 8080 (reachable by anyone UFW lets through), the shutdown port is loopback-only (good), and AJP on 8009 is off (it is commented out by default since the 2020 "Ghostcat" vulnerability; keep it that way).

**Why this step (now):** Debian-family packages start services at install time; the port is taken before you have configured anything.

**Next step:** if Tomcat holds 8080 (or any port you need) → Step 2. If Tomcat failed to start because 8080 was already taken → `journalctl -u tomcat10` shows the bind error; Step 2 fixes that too.

#### Step 2 — Move the connector and trust the proxy

**Goal:** HTTP on HOSTIP:8020, and Tomcat understanding `X-Forwarded-Proto`.

```xml
<!-- /etc/tomcat10/server.xml (back it up first) -->
<Connector port="8020" address="192.0.2.10" protocol="HTTP/1.1"
           connectionTimeout="20000" />

<!-- inside <Engine> or <Host>: real client IP and scheme from Traefik -->
<Valve className="org.apache.catalina.valves.RemoteIpValve"
       remoteIpHeader="X-Forwarded-For"
       protocolHeader="X-Forwarded-Proto" />
```

```bash
sudo cp -a /etc/tomcat10/server.xml /etc/tomcat10/server.xml.bak-$(date +%F)
sudoedit /etc/tomcat10/server.xml
sudo systemctl restart tomcat10
sudo ss -ltnp 'sport = :8020'
sudo ufw allow in on docker_gwbridge to any port 8020 proto tcp comment 'Traefik -> tomcat'
```

```
LISTEN 0      100       [::ffff:192.0.2.10]:8020         *:*    users:(("java",pid=9488,fd=43))
Rule added
Rule added (v6)
```

**What it means:** Tomcat now listens only on the host address, on a port from the convention. The `RemoteIpValve` makes `request.isSecure()` true for HTTPS requests that arrived at Traefik, so Tomcat stops generating `http://` redirects; its default list of trusted internal proxies already covers private ranges such as the Docker bridges.

**Why this step (now):** both changes need a Tomcat restart, so you make them together.

**Next step:** if `ss` shows only `192.0.2.10:8020` (plus loopback 8005) → Step 3. If Tomcat does not come back → `journalctl -u tomcat10` and `/var/log/tomcat10/catalina.out`; an XML typo in `server.xml` is the usual cause, so restore the backup and edit again.

#### Step 3 — Route Tomcat and test

**Goal:** `hr.example.com` through Traefik.

```bash
# /etc/dokploy/traefik/dynamic/tomcat.yml: router hr -> http://192.0.2.10:8020 (P3 template)
sudoedit /etc/dokploy/traefik/dynamic/tomcat.yml
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --resolve hr.example.com:443:192.0.2.10 https://hr.example.com/hr/
```

```
302 https://hr.example.com/hr/login
```

**What it means:** the redirect stays on `https://` with no port: the valve works. A redirect to `http://hr.example.com:8020/...` would mean it does not.

**Why this step (now):** redirects are where Java apps behind proxies fail first.

**Next step:** section 6 checklist. Containerised alternative: a Dokploy Application from a `tomcat:10.1` based image with Container Port 8080: inside a container, 8080 collides with nothing (P6).

| Pros | Cons | When to use |
|---|---|---|
| standard Tomcat, standard packaging | JVM memory on the host; tune `-Xmx` | Java apps that ship as WARs |
| connector bound to one address, firewalled | 8080 habits everywhere; always check first | when a container is not an option yet |

**Verify:** `ss` shows only `192.0.2.10:8020` and loopback 8005; redirects stay HTTPS; Tomcat's access log (`/var/log/tomcat10/localhost_access_log.*`) shows client IPs, not 172.18.x. The access log only does that if its `AccessLogValve` in `server.xml` has `requestAttributesEnabled="true"`; without it the log keeps showing Traefik's address even though the application sees the real one.

**Rollback:** restore `server.xml.bak-DATE`, restart Tomcat, remove the router file and UFW rule.

**Gotchas:** the context path (`/hr/`) is part of every URL, which is P4's problem in Java form; never expose the manager app (`/manager`) publicly; `systemctl restart tomcat10` takes seconds to tens of seconds, so plan it like a deployment.

### R6 — WordPress with Docker Compose

**Level:** [L2 · Mid]. **Study:** *Docker Training Course for the Absolute Beginner* → *Docker Compose* ([lesson](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)), then [Learn: databases ops](38-learn-databases-ops.md) for backups.

WordPress (`news.example.com`) with MariaDB, the database on an internal network with no port, WordPress joined to `dokploy-network` for Traefik. In Dokploy you can paste the same file into a Compose service and add the domain in the UI instead of writing labels.

#### Step 1 — Write the secrets and the compose file

**Goal:** credentials outside the YAML, database unreachable from anything but WordPress.

```bash
sudo mkdir -p /srv/news && cd /srv/news
sudo install -m 600 /dev/null .env
sudoedit .env          # DB_PASSWORD=...  DB_ROOT_PASSWORD=...  (long random values)
```

```yaml
# /srv/news/compose.yaml
services:
  db:
    image: mariadb:11.4
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wordpress
      MARIADB_PASSWORD: ${DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    networks: [backend]                 # no ports:, not on dokploy-network

  wordpress:
    image: wordpress:6-php8.3-apache
    restart: unless-stopped
    depends_on: [db]
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
    volumes:
      - wp_data:/var/www/html
    networks: [backend, dokploy-network]
    labels:
      - traefik.enable=true
      - traefik.docker.network=dokploy-network
      - traefik.http.routers.news.rule=Host(`news.example.com`)
      - traefik.http.routers.news.entrypoints=websecure
      - traefik.http.routers.news.tls.certresolver=letsencrypt
      - traefik.http.services.news.loadbalancer.server.port=80

volumes:
  db_data:
  wp_data:

networks:
  backend:
    internal: true                      # no route to the outside world at all
  dokploy-network:
    external: true
```

**What it means:** `db` exists only on `backend`, which is `internal`, so it has no host port, no internet access and no path from Traefik. WordPress sits on both networks, so `traefik.docker.network` tells Traefik which one to use. The official image's generated `wp-config.php` already honours `X-Forwarded-Proto`, so WordPress knows it is served over HTTPS.

**Why this step (now):** network membership is the security boundary in Docker; you decide it in the file, before anything runs.

**Next step:** if `docker compose config` renders the file without warnings → Step 2. If it warns that a variable is not set → `.env` is missing, empty or not in the project directory.

#### Step 2 — Start and prove the database is not exposed

**Goal:** the site works; the database is unreachable from the host network.

```bash
docker compose up -d
docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
sudo ss -ltnp 'sport = :3306'
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' --resolve news.example.com:443:192.0.2.10 https://news.example.com/
```

```
SERVICE     STATUS          PORTS
db          Up 20 seconds   3306/tcp
wordpress   Up 18 seconds   80/tcp
302 https://news.example.com/wp-admin/install.php
```

**What it means:** neither service publishes a port (no `->`), nothing listens on 3306 on the host, and WordPress redirects to its installer over HTTPS. Finish the installer immediately: until you do, anyone who finds the URL can claim the site.

**Why this step (now):** you check exposure before you put content in.

**Next step:** if no `->` appears and the installer redirect works → Step 3. If WordPress shows "Error establishing a database connection" → the database is still initialising or the passwords differ; read `docker compose logs db`.

#### Step 3 — Back up the database and files

**Goal:** a restorable backup that does not put the password on the command line.

```bash
cd /srv/news
docker compose exec -T db sh -c 'exec mariadb-dump --single-transaction -uroot -p"$MARIADB_ROOT_PASSWORD" wordpress' \
    | gzip > /root/backup/news-db-$(date +%F).sql.gz
docker run --rm -v news_wp_data:/data:ro -v /root/backup:/backup alpine \
    tar czf /backup/news-files-$(date +%F).tgz -C /data .
ls -lh /root/backup/ | tail -2
```

```
-rw-r--r-- 1 root root 1.9M Sep 28 13:10 news-db-2026-09-28.sql.gz
-rw-r--r-- 1 root root  61M Sep 28 13:11 news-files-2026-09-28.tgz
```

**What it means:** the password stays inside the container's environment; the volume name is the Compose project prefix plus the volume (`news_wp_data`). Test a restore on another machine before you call this a backup.

**Why this step (now):** WordPress gets content and plugins on day one; the backup must exist from day one.

**Next step:** section 6 checklist; schedule the backup with a systemd timer.

| Pros | Cons | When to use |
|---|---|---|
| database has no network exposure at all | WordPress needs regular updates (core, plugins) | WordPress and similar app + DB stacks |
| everything in one file; easy to move to Dokploy | volumes must be backed up separately | |

**Verify:** `docker compose ps` shows no `->`; `ss` shows nothing on 3306; `curl --resolve` 200 after installation; a restore test works.

**Rollback:** `docker compose down` stops the stack but **keeps** the volumes; restore data from the backups if needed.

**Gotchas:** `docker compose down -v` deletes the volumes and with them the database and uploads, so never add `-v` unless that is the goal; `internal: true` also blocks WordPress from reaching the internet if you put it **only** on that network (updates fail), which is why it also joins `dokploy-network`; upload size limits come from PHP inside the image (`upload_max_filesize`), not from Traefik.

### R7 — Internal admin tool on a custom port

**Level:** [L2 · Mid] to build, [L3 · Senior] to keep it safe over time. **Study:** *Certified Kubernetes Security Specialist (CKS)* — System Hardening → *UFW Firewall Basics* ([lesson](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) and Docker *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)).

An uptime dashboard (container listening on 3001) that only the office may use, on port 9401 of web01. This is pattern P1 with Docker, which means the filter must go into `DOCKER-USER` and must survive reboots. If you can, prefer the alternatives in the table at the end (Traefik with `ipAllowList`, or an SSH tunnel); this recipe is for when a direct port is a requirement.

#### Step 1 — Publish on the host address

**Goal:** the tool on 192.0.2.10:9401, not on every interface.

```bash
docker run -d --name uptime --restart unless-stopped \
    -p 192.0.2.10:9401:3001 -v uptime_data:/app/data louislam/uptime-kuma:1
sudo ss -ltnp 'sport = :9401'
```

```
LISTEN 0      4096      192.0.2.10:9401      0.0.0.0:*    users:(("docker-proxy",pid=71204,fd=7))
```

**What it means:** published on the LAN address only. UFW will **not** filter it (published port), so without the next step anyone who can route to 192.0.2.10 can open it.

**Why this step (now):** the bind narrows exposure for free; the filter does the rest.

**Next step:** if the listener shows `192.0.2.10:9401` → Step 2 immediately. If it shows `0.0.0.0:9401` → you omitted the address in `-p`; remove and recreate the container.

#### Step 2 — Write an idempotent DOCKER-USER script

**Goal:** a script that adds the office-only rule (and protects Dokploy's panel on 3000 the same way) without duplicating it.

```bash
sudoedit /usr/local/sbin/docker-user-rules.sh
sudo chmod 755 /usr/local/sbin/docker-user-rules.sh
```

```bash
#!/bin/sh
# /usr/local/sbin/docker-user-rules.sh — office-only access to Docker-published admin ports
set -eu
OFFICE=198.51.100.0/24
EXT_IF=ens18
for PORT in 9401 3000; do
  RULE="-i $EXT_IF -p tcp -m conntrack --ctorigdstport $PORT --ctdir ORIGINAL ! -s $OFFICE -j DROP"
  # -C checks whether the rule exists; insert it only if it does not
  iptables -C DOCKER-USER $RULE 2>/dev/null || iptables -I DOCKER-USER $RULE
done
```

```bash
sudo /usr/local/sbin/docker-user-rules.sh
sudo iptables -L DOCKER-USER -n --line-numbers
```

```
Chain DOCKER-USER (1 references)
num  target     prot opt source               destination
1    DROP       6    --  !198.51.100.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
2    DROP       6    --  !198.51.100.0/24      0.0.0.0/0            ctorigdstport 9401 ctdir ORIGINAL
3    RETURN     0    --  0.0.0.0/0            0.0.0.0/0
```

**What it means:** traffic arriving on `ens18` for ports 9401 or 3000 from outside the office range is dropped before Docker forwards it. `--ctorigdstport` matches the port the client dialled, because by the time `DOCKER-USER` sees the packet, DNAT has rewritten the destination to the container's port (3001). Running the script twice adds nothing the second time.

**Why this step (now):** the tool is live from Step 1; close the gap immediately, then make it permanent.

**Next step:** if each rule appears exactly once → Step 3. If a rule appears twice → an older manual rule exists; delete the duplicate by its spec. If `iptables` reports `No chain` → Docker is not running or uses the nftables backend.

#### Step 3 — Make the rules survive reboots

**Goal:** the rules are re-applied whenever Docker starts.

```ini
# /etc/systemd/system/docker-user-rules.service
[Unit]
Description=Office-only DOCKER-USER rules for admin ports
After=docker.service
Requires=docker.service
PartOf=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/docker-user-rules.sh

[Install]
WantedBy=docker.service
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now docker-user-rules.service
systemctl is-enabled docker-user-rules.service; systemctl is-active docker-user-rules.service
```

```
enabled
active
```

**What it means:** `WantedBy=docker.service` starts the unit whenever Docker starts, `PartOf` restarts it with Docker, and the script's `-C` check keeps it idempotent.

**Why this step (now):** firewall rules that vanish at the next reboot are the most common way a "restricted" admin port ends up public.

**Next step:** if `enabled` and `active` → Step 4. If `failed` → `journalctl -u docker-user-rules` (usually the script is not executable, or has a syntax error: test it with `sh -n`).

#### Step 4 — Test from both sides, and after a reboot

**Goal:** office yes, everyone else no, also after a reboot.

```bash
# From the office (198.51.100.x) and from outside it
nc -vz -w 3 192.0.2.10 9401
# After the next planned reboot of web01
sudo iptables -C DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 9401 --ctdir ORIGINAL ! -s 198.51.100.0/24 -j DROP && echo "rule present"
```

```
Connection to 192.0.2.10 9401 port [tcp/*] succeeded!
nc: connect to 192.0.2.10 port 9401 (tcp) timed out: Operation now in progress
rule present
```

**What it means:** the allow-list works and persists.

**Why this step (now):** you only know a rule persists when you have seen it after a reboot.

**Next step:** PORTS.md (9401 and 3000, "office only, DOCKER-USER"), section 6 checklist.

| Option | Pros | Cons |
|---|---|---|
| Direct port + DOCKER-USER (this recipe) | works for non-HTTP and for tools that dislike proxies | plain HTTP unless the tool does TLS; custom firewall code to maintain |
| Traefik route + `ipAllowList` (+ basic auth middleware) | HTTPS, standard URL, no extra port, one place for access rules | the tool must work behind a proxy (most do) |
| Publish on `127.0.0.1` + SSH tunnel | nothing exposed at all | every user needs SSH access and a tunnel |

**Verify:** Step 4 from both sides; `systemctl is-enabled docker-user-rules` → `enabled`.

**Rollback:** `sudo systemctl disable --now docker-user-rules`, delete the rules with `iptables -D DOCKER-USER` and the same arguments, `docker rm -f uptime` (the `uptime_data` volume keeps its data).

**Gotchas:** IPv6 needs the same rules with `ip6tables` if the port is published on `[::]`; the external interface name must be right (`ip -br link`), or the rule never matches; on AWS, the security group is a simpler and more robust place for this allow-list.

### R8 — GitLab CI deploy to Dokploy

**Level:** [L3 · Senior]; it is the L3 exit test of your ops ladder. **Study:** *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab → *Docker Push* ([lesson](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page)), then the Harbor docs ([docs](https://goharbor.io/docs/)) and [Learn: CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

The client's app (`app.example.com`) is a Dokploy Application of type Docker image. GitLab CI builds the image, pushes it to Harbor with an immutable tag (the commit SHA), moves a `production` tag to that SHA, and asks Dokploy to redeploy. Rollback is moving the tag back.

#### Step 1 — Prepare Dokploy and GitLab

**Goal:** Dokploy pulls from Harbor, and GitLab holds the credentials as masked variables.

| Where | Setting | Value |
|---|---|---|
| Harbor | robot account for project `shop` | pull+push; used by CI as HARBOR_USER / HARBOR_PASSWORD |
| Dokploy, Registry | Harbor registry entry | harbor.example.com with a pull-only robot account |
| Dokploy, Application | Docker image | harbor.example.com/shop/api:production |
| Dokploy, Application | Domain | app.example.com, Container Port 8000, HTTPS, Let's Encrypt |
| Dokploy, profile | API token | stored in GitLab as DOKPLOY_TOKEN (masked, protected) |
| GitLab, CI/CD variables | DOKPLOY_URL, DOKPLOY_APP_ID | https://dokploy.example.com and the application's ID |

```bash
# On the runner host: the CI robot account can log in to Harbor (password from stdin, never in argv)
printf '%s' "$HARBOR_PASSWORD" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin

# Harbor's private CA is trusted (web01 needs the same trust for Dokploy's pulls)
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com </dev/null 2>/dev/null \
    | grep 'Verify return code'

# The Dokploy token works (endpoint name: check your instance's API reference)
curl -s -o /dev/null -w '%{http_code}\n' -H "x-api-key: $DOKPLOY_TOKEN" "$DOKPLOY_URL/api/project.all"
```

```
Login Succeeded
Verify return code: 0 (ok)
200
```

**What it means:** Dokploy always deploys `:production`; CI decides which SHA that tag points to. The application ID and the API endpoint names come from your Dokploy version: its API reference (Swagger UI on your instance) is the authority, not this page.

**Why this step (now):** credentials and identifiers must exist before the pipeline can run, and masked, protected variables keep tokens out of job logs and away from unprotected branches.

**Next step:** if every row of the table exists and a manual deploy of `:production` from Dokploy succeeds → Step 2. If Dokploy cannot pull from Harbor → fix the registry entry or the private CA trust on web01 before you write any pipeline.

#### Step 2 — Write the pipeline

**Goal:** build and push the SHA, promote it to `production`, deploy on a manual click.

```yaml
# .gitlab-ci.yml
stages: [build, release, deploy]

variables:
  IMAGE: harbor.example.com/shop/api
  DOCKER_TLS_CERTDIR: "/certs"

.docker:
  image: docker:27
  services: [docker:27-dind]
  before_script:
    - echo "$HARBOR_PASSWORD" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin

build:
  extends: .docker
  stage: build
  script:
    - docker build --pull -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

release:
  extends: .docker
  stage: release
  script:
    - docker pull "$IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$IMAGE:$CI_COMMIT_SHORT_SHA" "$IMAGE:production"
    - docker push "$IMAGE:production"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual

deploy:
  stage: deploy
  image: curlimages/curl:8.10.1
  needs: [release]
  environment:
    name: production
    url: https://app.example.com
  script:
    - >
      curl --fail-with-body -sS -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$DOKPLOY_APP_ID\"}"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

```bash
# Validate the file before you push it: GitLab's CI Lint API (a token with api scope),
# or open Build > Pipeline editor in the GitLab UI, which validates as you type
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" --header "Content-Type: application/json" \
    --data "$(jq -n --rawfile c .gitlab-ci.yml '{content: $c}')" \
    "https://gitlab.example.com/api/v4/projects/PROJECT_ID/ci/lint" | jq '{valid, errors}'
```

```
{
  "valid": true,
  "errors": []
}
```

**What it means:** every commit on the default branch produces an immutable `:SHA` image. A human clicks `release` to promote it (the manual gate), and `deploy` then calls Dokploy. `--fail-with-body` makes the job fail on an HTTP error while still printing Dokploy's error message. No port appears anywhere: the app is P6, routed by its domain.

**Why this step (now):** the pipeline is the deployment procedure written down, so it gets reviewed like code.

**Next step:** if the pipeline passes on the default branch → Step 3. If `docker login` fails with `x509` → the dind service does not trust Harbor's CA (see Gotchas). If the deploy job gets 401 or 403 → the token or the application ID is wrong.

#### Step 3 — Verify what is actually running

**Goal:** prove the running container uses the digest you just pushed, not a cached old `production`.

```bash
# Digest of the SHA tag in Harbor (from any machine logged in to Harbor)
docker buildx imagetools inspect harbor.example.com/shop/api:4f9c2e1 | grep -m1 Digest
# What the running task's container was created from (on web01)
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=client-app-x1y2z3 | head -1)
docker image inspect "$(docker inspect -f '{{.Image}}' "$CID")" --format '{{join .RepoDigests "\n"}}'
curl -s --resolve app.example.com:443:192.0.2.10 https://app.example.com/version; echo
```

```
Digest:    sha256:7b1e0c9d4f...a12
harbor.example.com/shop/api@sha256:7b1e0c9d4f...a12
{"version":"1.5.0","commit":"4f9c2e1"}
```

`docker service inspect client-app-x1y2z3 --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'` shows a pinned `@sha256:` only when the client that created or updated the service resolved one (the `docker service` CLI does by default; API clients such as Dokploy may store the bare tag), which is why the check above asks the running container instead.

**What it means:** same digest, and the app reports the commit it was built from (bake `CI_COMMIT_SHORT_SHA` into the image as a build argument). If the digests differ, the deploy reused a cached tag; redeploy, and consider deploying the `:SHA` tag directly through Dokploy's API so there is nothing to cache.

**Why this step (now):** "pipeline green" proves the API call worked, not that users see the new code.

**Next step:** section 6 checklist; practise the rollback below once before you need it.

| Pros | Cons | When to use |
|---|---|---|
| immutable SHA images; promotion is explicit | a moving `production` tag must be verified by digest | every app deployed with Dokploy from GitLab |
| rollback = re-run the previous pipeline's release + deploy | the Dokploy token is powerful; scope and rotate it | |

**Verify:** Step 3; the GitLab environment page shows which commit is in production.

**Rollback:** in GitLab, open the previous successful pipeline and re-run its `release` job (moves `production` back to the old SHA), then its `deploy` job. Alternatively use the deployment history in Dokploy's UI. Both work only if the old SHA image still exists in Harbor, so set Harbor's tag retention to keep at least the last ten SHAs.

**Gotchas:** the dind service must trust Harbor's CA, or `docker login` fails with `x509: certificate signed by unknown authority` (mount the CA into the job or configure the runner); Harbor's tag immutability rules must not include `production`, or the release job cannot move it; never echo `$DOKPLOY_TOKEN` in a script line, masked or not.

---

## 5. When a client says: deploy on port X

> 📚 **Study path:** 1) Note: [Who owns this port?](22-playbook-ports-inventory.md), because Step 2 below is that whole module in five lines · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) and *Port Redirection and NAT* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 3) KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil → *Change Management for Reliability* ([lesson](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) for how to write the change down · 4) Practice: timed task 7 in section 7 (the client role-play).

**Level:** Steps 1–3 are [L2 · Mid]: collecting evidence. Steps 4–5 are [L3 · Senior]: choosing a design and explaining the trade-off to someone who is not an engineer.

Clients and vendors often state a requirement as a port number: "it runs on 3000", "open 8443 for our API", "our app needs 443". The number is usually a symptom of a real requirement, not the requirement itself. Your 81/444 fix started exactly here: "Dokploy needs 80/443". This section is the procedure that turns "deploy it on port X" into the right pattern from section 3, with evidence at every step.

| The client says | What it usually means | Usual answer |
|---|---|---|
| "The app runs on port 3000" | the app listens on 3000 inside its container or process | P6 or P5: Container Port 3000, no host port; users get `https://app.example.com/` |
| "It must be on 443" | users must reach it with a normal HTTPS URL | P3 or P6: a new hostname on Traefik; 443 stays Traefik's |
| "Open 8443 for our API" | a partner system calls it, maybe through their own outbound allow-list | a hostname on 443 if they can; otherwise P1 on 8443 allow-listed to their IPs, with TLS |
| "Give us port 5432" | someone wants to reach the database | P10: SSH tunnel or VPN, never a public database port |
| "Our appliance needs 80 and 443" | it terminates its own TLS, maybe runs its own ACME client | P9 passthrough by SNI, or P8 a second IP |
| "Use 8080 like the docs say" | the vendor's default, nothing more | any free port from your convention, or no host port at all (P5, P6) |

### Step 1 — Ask why the app needs port X

**Goal:** turn the port number into a requirement you can design for.

```bash
# What does the app itself say about ports? Run this in the client's repository or release bundle.
grep -RnE '^\s*(EXPOSE|ports:|- "?[0-9]+:[0-9]+|PORT=|LISTEN|server\.port|TLS_)' \
    Dockerfile docker-compose.yml compose.yaml .env.example config/ 2>/dev/null
```

```
Dockerfile:18:EXPOSE 8443
docker-compose.yml:9:    ports:
docker-compose.yml:10:      - "8443:8443"
.env.example:4:PORT=8443
.env.example:5:TLS_CERT=/certs/server.crt
.env.example:6:TLS_KEY=/certs/server.key
```

**What it means:** the app listens on 8443 and terminates TLS itself (`TLS_CERT`, `TLS_KEY`). The compose file publishes 8443 on every host address only because that is how the vendor tested it on a laptop. Now ask the client four questions, and write the answers down:

1. **Who connects?** Browsers on the internet, staff on the LAN or VPN, a partner's server, a mobile app?
2. **Must the URL contain the port?** Is 8443 hard-coded in a partner system, printed on a QR code, or allowed through someone else's outbound firewall?
3. **Must the app terminate TLS itself?** Client certificates (mTLS), a licence bound to its certificate, a compliance rule? Or can it run plain HTTP behind the proxy (most apps have a setting for that)?
4. **What happens if it is down?** This decides monitoring, restart policy and who gets called (section 6).

**Why this step (now):** the port is almost always the vendor's default, and almost never the real requirement. One question here can save you a public port, a firewall exception and a certificate you would have to renew by hand.

**Next step:** if the answer is "browsers, with a normal URL" → Step 2, then go straight to Step 4 (a proxy route, no new public port). If "a partner system has the port hard-coded" or "the app must terminate its own TLS" → Steps 2 and 3. If nobody knows → treat it as a normal web app behind the proxy and say so in writing in Step 5.

### Step 2 — Check whether port X is free

**Goal:** know who owns X on this host now, at the next boot, and in Docker or Swarm.

```bash
X=8443
sudo ss -ltnup "sport = :$X"
docker ps -a --format '{{.Names}}\t{{.Ports}}' | grep -w "$X" || echo "no container publishes $X"
docker service ls --format '{{.Name}}\t{{.Ports}}' | grep -w "$X" || echo "no swarm service publishes $X"
systemctl list-sockets --all --no-pager | grep -w ":$X" || echo "no socket unit on $X"
```

```
Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
no container publishes 8443
no swarm service publishes 8443
no socket unit on 8443
```

**What it means:** nothing owns 8443 right now, no stopped container or Swarm service will claim it, and no socket unit listens for it. If something did own it, the full chain from port to process, unit, config file and logs is in [Who owns this port?](22-playbook-ports-inventory.md), and section 2 here shows how to find owners that are installed but stopped.

**Why this step (now):** you must know this before you promise the client anything. "Free now" also has to mean "free after a reboot", which is why the command checks containers, Swarm services and socket units as well as live listeners.

**Next step:** if X is free → Step 3. If X is owned by something you run and understand → Step 3, then Step 4 decides whether to move it (your 81/444 move) or place the new app elsewhere. If X is owned by something you cannot explain → stop and identify it with module 22 first; never move an owner you do not understand.

### Step 3 — Decide public or internal

**Goal:** know who must reach port X and from where, and what would protect it.

```bash
# From a machine OUTSIDE the server: a cloud VM for the internet view, an office laptop for the LAN view
nc -vz -w 3 203.0.113.10 443
nc -vz -w 3 203.0.113.10 8443

# On web01: the policies a new port would fall under
sudo ufw status verbose | head -4
sudo iptables -L DOCKER-USER -n
```

```
Connection to 203.0.113.10 443 port [tcp/https] succeeded!
nc: connect to 203.0.113.10 port 8443 (tcp) timed out: Operation now in progress

Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

Chain DOCKER-USER (1 references)
target     prot opt source               destination
DROP       6    --  !198.51.100.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
DROP       6    --  !198.51.100.0/24      0.0.0.0/0            ctorigdstport 9401 ctdir ORIGINAL
RETURN     0    --  0.0.0.0/0            0.0.0.0/0
```

**What it means:** today only 80 and 443 (plus SSH from the office) are reachable from outside. Opening 8443 would be a **new** public entry point, and if the app is published by Docker, UFW will not protect it: only a `DOCKER-USER` rule or the edge firewall will (recipe R7). Match the answers from Step 1 to a pattern:

| Who connects | From where | Pattern |
|---|---|---|
| browsers, the public | the internet | P3 or P6: a hostname on Traefik, no new port |
| staff | office LAN or VPN | P3 with `ipAllowList`, or P1 with a firewall allow-list |
| a partner's server | fixed IP addresses | a hostname on 443 if they can use it; otherwise P1 on X allow-listed to their IPs, with TLS |
| a client that needs mTLS, or an appliance with its own TLS | anywhere | P9: SNI passthrough on 443 |
| people who need a database or an admin port | anywhere | P10: SSH tunnel or VPN |

**Why this step (now):** "public or internal" decides everything after it: the certificate, the firewall layer, the monitoring and who gets paged. Testing from outside shows the exposure that really exists, not the one you intended.

**Next step:** public web traffic → Step 4 with P3 or P6. Internal or partner-only on X → Step 4 with P1 (recipe R7 if it is a container). Non-HTTP traffic → pattern P10, then Step 5.

### Step 4 — Move the owner or route the new app

**Goal:** choose between moving the current owner of a port (your 81/444 technique) and putting the new app behind the proxy.

```bash
# If the client asked for a port that is already owned (here 443): who depends on the current owner?
# File-provider routes (Apache sites, Dokploy applications):
sudo grep -RhoE 'Host\(`[^`]+`\)' /etc/dokploy/traefik/dynamic/ | sort -u
# Compose apps keep their Host rules in container labels:
docker ps --format '{{.Labels}}' | grep -oE 'Host\(`[^`]+`\)' | sort -u
```

```
Host(`api.example.com`)
Host(`app.example.com`)
Host(`intranet.example.com`)
Host(`shop.example.com`)
Host(`www.shop.example.com`)
Host(`docs.example.com`)
Host(`news.example.com`)
```

**What it means:** seven hostnames depend on Traefik owning 443. Moving Traefik to give a new app "its" 443 would break all of them, so the only sensible answer is that the new app becomes the eighth hostname. Your 81/444 move was right because the owner you moved (Apache) could become a **backend**; Traefik is the front door and cannot.

| Option | When it is right | What you must also do |
|---|---|---|
| Move the current owner to another port (your 81/444 fix) | the owner can become a backend behind the proxy, or it is internal only | everything in section 1, Steps 1–14: vhosts, redirects, routes, certificates, firewall, PORTS.md |
| New app behind the proxy, no new public port (P3, P5, P6) | the app speaks HTTP(S) and its users can use a hostname | DNS record, route, certificate, then section 6 |
| New app on its own port X (P1) | system-to-system or internal use from known addresses | allow-list (UFW or `DOCKER-USER`), TLS on the app, PORTS.md, a review date |
| New app on a second IP (P8) or with passthrough (P9) | it must own 80/443 or its own TLS | second IP and NAT, or a TCP router; certificate renewal on the app side |

**Why this step (now):** this is where your 81/444 technique belongs in a decision. It is a valid move when the owner can become a backend, and it is not a reason to give every new app its own public port.

**Next step:** decision made → Step 5. If moving an owner would affect clients you cannot reach or reconfigure (partners with hard-coded URLs, devices in the field) → choose the proxy route instead and return to Step 3 for the details.

### Step 5 — Tell the client what you will do

**Goal:** a short written answer: what you will deploy, the URL, what you will not do and why, and what you need from them.

```bash
# Evidence to attach to the ticket or email: the listeners, and the new route working
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :8443 )' > ~/ports-evidence-$(date +%F).txt
curl -s -o /dev/null -w '%{http_code} verify=%{ssl_verify_result}\n' \
    --resolve partner-api.example.com:443:192.0.2.10 https://partner-api.example.com/health
```

```
200 verify=0
```

```
Subject: Deployment of the partner API on web01

Proposal
- URL: https://partner-api.example.com (standard port 443, publicly trusted certificate)
- The application runs privately on the server; port 8443 is not opened to the internet.
- If your system cannot use port 443, we can open 8443 for your fixed IP addresses only.
  Please send those addresses. Nobody else will be able to connect to that port.

Why not a public port 8443
- Port 443 already serves every site on this server through our reverse proxy.
- A separate public port bypasses our central TLS, logging and access rules.

What we need from you
- Your source IP addresses (only if you need 8443)
- A test from your side against https://partner-api.example.com/health

Rollback
- The change is isolated to one new route; removing it restores the current state in minutes.
```

**What it means:** `200 verify=0` proves the route works with a certificate that curl trusts (0 means the chain and name verified). The client gets what they actually need (a working endpoint), a reason they can repeat to their own team, and a cheap, safe option for their real constraint.

**Why this step (now):** the senior skill is translation: a technical constraint becomes a business choice with a recommendation. Writing it down also answers the question someone will ask in a year: "who opened 8443, and why?"

**Next step:** the client agrees → deploy with the chosen pattern (sections 3 and 4), then run section 6. The client insists on a public port X → get the request in writing (ticket or email), deploy P1 with the narrowest allow-list they accept, TLS on the app and monitoring, and put a review date in PORTS.md.

### Decision tree for port requests

```
"Deploy it on port X"
│
├─ Is X only the app's default (EXPOSE, vendor docs, compose file)?
│    └─ yes → ignore X on the host: P6 / P5 (Container Port X, no host port)
│             or P7 on a free port from your convention
│
├─ Is the traffic non-HTTP (database, cache, broker, SSH, custom TCP)?
│    └─ yes → P10: private bind; SSH tunnel or VPN for people;
│             remote systems only: Traefik TCP entryPoint, or P1 + allow-list
│
├─ Can the clients use https://NAME/ on 443?
│    └─ yes → P3 / P6: a hostname route on Traefik          ← the default
│
├─ Must the app terminate TLS itself (mTLS, appliance)?
│    └─ yes → P9: SNI passthrough on 443, or P8: a second IP
│
└─ The clients really need port X (hard-coded, partner firewall):
     ├─ X is free                          → P1 on X + allow-list + TLS, request in writing
     ├─ X is owned by a backend you run    → move it (your 81/444 fix) and route it via the proxy
     └─ X is owned by something unexplained → stop; identify it first (module 22)
```

---

## 6. Post-deployment checklist

> 📚 **Study path:** 1) Note: [systemd](07-services-systemd.md), [Logs & journal](06-logs-journal.md) and [Web, HTTP & TLS](18-web-http-tls.md), as quick refreshers for rows 3–5 · 2) KodeKloud: *Docker Certified Associate* — Docker Engine → *Restart Policies* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)) and *Logging Driver* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 3) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals → *Node Exporter* ([lesson](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page)) for row 7 · 4) Read: Google SRE book, *Effective Troubleshooting* ([chapter](https://sre.google/sre-book/effective-troubleshooting/)) · 5) Practice: run the checklist against the last thing you deployed and fix every failing row.

**Level:** [L1 · Junior] to run it on your own deployments · [L2 · Mid] to fix every failing row · [L4 · Lead] to make it the team's definition of done and to review other people's results against it.

Run this after **every** deployment, whatever the pattern. Each row has a command that proves it, what "pass" looks like, and where the fix lives. A deployment is finished when every row passes or has a written, dated exception.

### The ten checks

| # | Check | Prove it with | Pass when | Fix in |
|---|---|---|---|---|
| 1 | Listening on the intended address | `sudo ss -ltnp 'sport = :PORT'`; for containers `docker ps` (Ports column) or `docker service inspect` | loopback, HOSTIP or no host port, exactly as designed; no surprise `0.0.0.0` | section 2, P5, P7 |
| 2 | Firewall | `sudo ufw status numbered`; `sudo iptables -L DOCKER-USER -n`; `nc -vz` from outside | only the intended ports answer from outside; backend ports time out | section 1 Step 13, P1, R7 |
| 3 | TLS and its renewal path | `curl -sv --resolve NAME:443:HOSTIP https://NAME/`; who renews: Traefik's `acme.json`, `certbot certificates`, timers | right name, trusted chain, 30+ days left, and a renewal method that can reach its challenge | section 1 "The certificate trap" and Step 12 |
| 4 | Logs: location and rotation | `journalctl -u UNIT`; `docker logs CONTAINER`; `/var/log/apache2/`; `/etc/logrotate.d/`; Docker `log-opts` | you can name where every log goes, and each one rotates | [Logs & journal](06-logs-journal.md) |
| 5 | Restart policy and boot | `systemctl is-enabled UNIT`; `docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' CONTAINER` | `enabled`, or `unless-stopped`/`always`; a reboot was survived once | P7, [systemd](07-services-systemd.md) |
| 6 | Health check | `curl -fsS https://NAME/health`; `docker inspect -f '{{.State.Health.Status}}' CONTAINER` | 200 from an endpoint that also touches the app's dependencies | P3 Step 4 |
| 7 | Monitoring and alerts | the uptime or blackbox check and its alert route | an external check exists and a test alert reached a human | [Learn: performance & observability](32-learn-performance-observability.md) |
| 8 | Backup | the backup job's last run, and one restore test | backups exist, live off the host, and a restore worked | R6 Step 3, [Learn: databases ops](38-learn-databases-ops.md) |
| 9 | Documentation | PORTS.md, the change ticket, the app's README | the PORTS.md line was added in the same change, with an owner and a contact | section 2 |
| 10 | Rollback tested | the pattern's or recipe's rollback, executed once | it worked and you know how long it takes | each pattern's **Rollback** |

### Run the checks in one go

**Goal:** prove rows 1–6 and 9 with one read-only script, so the checklist is run every time and not only when you remember.

```bash
sudoedit /usr/local/sbin/postdeploy-check.sh      # paste the script below
sudo chmod 755 /usr/local/sbin/postdeploy-check.sh
sudo /usr/local/sbin/postdeploy-check.sh reports.example.com 8001 reports.service
```

```bash
#!/bin/sh
# /usr/local/sbin/postdeploy-check.sh NAME PORT UNIT_OR_CONTAINER   (read-only: changes nothing)
NAME=$1; PORT=$2; OWNER=$3; HOSTIP=192.0.2.10
echo "== 1 listener"
ss -ltnH "sport = :$PORT" | awk '{print $4}' | sort -u
echo "== 2 firewall"
ufw status | grep -w "$PORT" || echo "no ufw rule mentions $PORT"
echo "== 3 tls"
curl -s -o /dev/null -w 'http=%{http_code} verify=%{ssl_verify_result}\n' \
    --resolve "$NAME:443:$HOSTIP" "https://$NAME/"
echo | openssl s_client -connect "$HOSTIP:443" -servername "$NAME" 2>/dev/null \
    | openssl x509 -noout -enddate
echo "== 4/5 owner"
if systemctl cat "$OWNER" >/dev/null 2>&1; then
    systemctl is-enabled "$OWNER"; systemctl is-active "$OWNER"
    journalctl -u "$OWNER" -p err --since -1h --no-pager -q | tail -3
else
    docker inspect -f 'restart={{.HostConfig.RestartPolicy.Name}} log={{.HostConfig.LogConfig.Type}} {{.HostConfig.LogConfig.Config}}' "$OWNER"
fi
echo "== 6 health"
curl -fsS -o /dev/null -w '%{http_code}\n' --resolve "$NAME:443:$HOSTIP" "https://$NAME/health"
echo "== 9 docs"
grep -n "$PORT/" /root/PORTS.md || echo "MISSING from /root/PORTS.md"
```

```
== 1 listener
192.0.2.10:8001
== 2 firewall
8001/tcp on docker_gwbridge ALLOW       Anywhere                   # Traefik -> reports
8001/tcp (v6) on docker_gwbridge ALLOW       Anywhere (v6)              # Traefik -> reports
== 3 tls
http=200 verify=0
notAfter=Dec 27 09:14:03 2026 GMT
== 4/5 owner
enabled
active
== 6 health
200
== 9 docs
10:| 8001/tcp | 192.0.2.10 | reports.service | reports app (gunicorn) | Traefik only | ufw allow in on docker_gwbridge | /etc/systemd/system/reports.service | team-reports |
```

**What it means:** the app listens only on HOSTIP, only the Docker bridge may reach it, the certificate verifies and has about three months left, the unit starts at boot and logged no errors in the last hour, the health endpoint answers, and PORTS.md knows about it. Rows 7, 8 and 10 cannot be proven from the server alone: tick them by hand with evidence (the name of the uptime check, the backup job's last log line, the date and duration of the rollback test). For a container, row 4/5 prints something like `restart=unless-stopped log=json-file map[max-file:3 max-size:10m]`; an empty `map[]` means its logs never rotate.

**Why this step (now):** the deployment just finished, so every fact is fresh, and any failure is still cheap to fix. A failing row found in three months is an incident; found today it is a five-minute fix.

**Next step:** all rows pass → record the result in the change ticket (template below) and close it. A row fails → fix it using the "Fix in" column before you call the deployment done. A row cannot be fixed now → write a dated exception in PORTS.md's History and in the ticket, with an owner.

### Extra checks per pattern

| Pattern | Also check |
|---|---|
| P5, P6 (containers) | no `->` in the Ports column; the image tag is immutable (a commit SHA); the logging driver has `max-size` |
| P7 (systemd) | `systemd-analyze security UNIT` reviewed; a `kill -9` was followed by an automatic restart |
| P1 (custom port) | a test from an address outside the allow-list times out; the rule is still there after a reboot |
| P9 (passthrough) | the backend's own certificate renewal (DNS-01) and an expiry alert |
| P11 (Kubernetes) | readiness and liveness probes; resource requests; `kubectl rollout history` shows the release |
| P12 (blue/green) | the idle colour is stopped; both ports are in PORTS.md as one app |
| Apache on 81 behind Traefik | `apache2ctl -S` shows only `*:81`; every vhost name has a Traefik router; Apache logs show real client IPs |

### Sign-off record

Paste this into the change ticket. It takes two minutes and turns "I think it is done" into evidence.

```
Deployed:   reports.example.com (P7 + P3) on web01, 2026-09-28, by ops@example.com
Checks:     1-6, 9 pass (postdeploy-check.sh output attached)
            7: uptime check "reports-https", test alert received by on-call
            8: nightly pg_dump to backup01, restore tested 2026-09-28
            10: rollback (disable unit, remove route) timed at 4 minutes
PORTS.md:   8001/tcp added
Exceptions: none
```

---

## 7. Self-check / exit test

> 📚 **Study path:** 1) Practice: answer the questions for your stage without looking, then reread the section in brackets for every miss · 2) KodeKloud: *Linux Challenges* (free, timed) as a warm-up ([course](https://kodekloud.com/courses/linux-challenges)) · 3) Lab: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) or Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)) for the timed tasks, or your homelab VM · 4) Practice: [SadServers](https://sadservers.com/scenarios) "port in use" and "service won't start" scenarios for speed.

**Level:** every question and task carries its stage. Pass your own stage first, then try the next one.

Do the tasks on a lab VM, never first on a client's server. Record your times and repeat the tasks a month later: the goal is a skill you keep.

### Self-check questions

Answer out loud or in writing, without looking. The section in brackets is where to check your answer.

1. [L0 · Fresher] Apache holds `*:443`. Why can Traefik not bind `0.0.0.0:443`, and what error does Docker print? (0, 1)
2. [L0 · Fresher] Which ports does a URL without a port use, and why does nobody type `:444`? (0)
3. [L0 · Fresher] Name the IANA port ranges and the Linux ephemeral range. Which range must a server never listen in, and why? (2)
4. [L0 · Fresher] `ss -ltnp` shows `127.0.0.1:8001`. Can another machine connect? Can a Traefik container on the same host? (2, P3)
5. [L1 · Junior] You changed `Listen 80` to `Listen 81` but no `VirtualHost` tag, and `configtest` says `Syntax OK`. What do clients get on 81, and on 444? (1, Step 4)
6. [L1 · Junior] Why edit the files in `sites-available` and not run `sed -i` on `sites-enabled`? (1, Step 4)
7. [L1 · Junior] Which command shows which vhost answers on which address and port, and why is `configtest` not enough? (1, Step 6)
8. [L1 · Junior] On Rocky Linux, httpd fails with `(13)Permission denied` on 444. What is the narrow fix, and why is `setenforce 0` the wrong one? (1, RHEL)
9. [L1 · Junior] Name two kinds of owner that can claim a port after a reboot even though `ss` shows it free now. (2, Step 2)
10. [L2 · Mid] After the move, `https://shop.example.com` shows Traefik's 404 and the `TRAEFIK DEFAULT CERT`. What is missing, and in which file do you add it? (1, Steps 10–11)
11. [L2 · Mid] The Traefik container times out on `192.0.2.10:81`, but `curl` on the host works. What blocks it, which single rule fixes it, and why does "Docker bypasses UFW" not apply here? (1, Step 9)
12. [L2 · Mid] Why does `certbot renew` fail after the move, and what are the three ways out? (1, "The certificate trap")
13. [L2 · Mid] A browser shows `ERR_TOO_MANY_REDIRECTS` once Traefik fronts Apache. Which header and which rewrite condition fix it? (1, Step 5)
14. [L2 · Mid] `"8000:8000"`, `"127.0.0.1:18000:8000"` and "no ports plus labels": who can reach the app in each case? (P5)
15. [L2 · Mid] A new Dokploy app shows Bad Gateway. Name the two most likely causes and the command that proves each. (P6)
16. [L2 · Mid] An app works on `/` but its CSS returns 404 under `/reports/`. What is wrong, and what can no proxy rule fix? (P4)
17. [L3 · Senior] When is your 81/444 move the right answer, and when is it incomplete? Give one example of each. (1, verdict; 5, Step 4)
18. [L3 · Senior] A vendor appliance must terminate its own TLS on 443 next to Traefik. Give two designs and the main trade-off of each. (P8, P9)
19. [L3 · Senior] Why do Kubernetes pods never fight over ports, and where does the "who owns 80/443" question come back on bare metal? (P11)
20. [L3 · Senior] In a blue/green release, why must database changes be "expand, then contract"? (P12)
21. [L3 · Senior] A client says "open 8443 for our API". Which four questions do you ask, and what does your written answer offer? (5)
22. [L4 · Lead] Write a port convention for a new shared server in five rows, and say who may change it and how. (2)
23. [L4 · Lead] Which checklist rows cannot be proven from the server alone, and how do you make them evidence-based for the whole team? (6)
24. [L4 · Lead] A colleague deployed an internal tool with `ports: "3000:3000"`. What do you ask them to change, and what do you change so it does not happen again? (P1, P5, R7)

### Build the lab

Build this once on an Ubuntu 24.04 VM (a KodeKloud playground resets after its time limit, so script the setup):

1. Install Apache with three name-based vhosts on 80 and 443 (self-signed or internal-CA certificates), and add `/etc/hosts` entries for `shop.example.com`, `api.example.com` and `intranet.example.com` on your workstation.
2. Install Docker and run a Traefik v3 container that publishes 80/443 and watches a file-provider directory, to imitate Dokploy. On a disposable VM you can install Dokploy itself instead.
3. Enable UFW with `deny (incoming)` and allow SSH from your workstation only.
4. Keep a second VM (or your workstation) as the "outside" client for `nc` and `curl --resolve` tests.

### Timed tasks

1. **Port census.** [L0 · Fresher] 10 min. List every listener on the lab VM, mark each one local-only or reachable from outside, and name its owner. Pass: every line of `ss -ltnup` explained correctly.
2. **Your fix, by the book.** [L1 · Junior] 30 min. Move Apache to 81/444 with section 1, Steps 1–8, including every vhost and redirect. Then roll back from the backup and time the rollback. Pass: `apache2ctl -S` shows only 81/444 before the rollback, and the rollback takes under 5 minutes.
3. **Finish the job.** [L2 · Mid] 60 min. Do Steps 9–14 in the lab: the bridge rule, the route file, `curl --resolve` returning 200 for every name, 81/444 closed when tested from the second VM, and the real client IP in Apache's log.
4. **Break it three ways.** [L2 · Mid] 30 min. One at a time: bind Apache to `127.0.0.1:81`, delete the bridge rule, remove the `X-Forwarded-Proto` condition. For each, write down the symptom (502, timeout or redirect loop) and the log line or command output that names the cause.
5. **Three apps, no new public port.** [L2 · Mid] 60 min. Deploy recipes R1, R3 and R6. Pass: from the second VM only 80, 443 and SSH answer, and all three names return 200.
6. **Zero-downtime release.** [L3 · Senior] 45 min. Run P12 while a loop of `curl` requests runs against the health endpoint. Pass: not one failed request during the switch.
7. **Client role-play.** [L3 · Senior] 20 min. Someone plays a client who wants "port 8443, public". Produce the section 5 message and the PORTS.md line for the outcome you agree on.
8. **The CKA link.** [L3 · Senior] 45 min. In your homelab cluster, expose an app with a ClusterIP Service plus an Ingress or HTTPRoute, and give the controller an address with MetalLB. Explain, with command output, who owns 80/443 and on which address.
9. **Make it a standard.** [L4 · Lead] half a day. Write the server's port convention, PORTS.md and the post-deployment checklist as a team document. Have a colleague deploy recipe R7 using only your documents, then review the result with section 6.

### Exit test by career stage

Pass a stage when you can do its tasks alone, within the time, with every claim backed by command output.

| Stage | Tasks and questions | Time | You pass when |
|---|---|---|---|
| Fresher [L0] | task 1; questions 1–4 | 10 min + 10 min | every listener explained; answers match the sections |
| Junior [L1] | task 2; questions 5–9 | 30 min | no `*:80` or `*:443` vhost left; rollback tested and timed |
| Mid-level [L2] | tasks 3, 4 and 5; questions 10–16 | 60 + 30 + 60 min | every name returns 200 with a valid certificate through `--resolve`; each break proven with evidence; only 80, 443 and SSH reachable from outside |
| Senior [L3] | tasks 6, 7 and 8; questions 17–21 | 45 + 20 + 45 min | zero failed requests; the client message offers a safe option for the real constraint; ownership of 80/443 in the cluster explained |
| Lead [L4] | task 9; questions 22–24 | half a day | another engineer deploys from your documents without asking you anything, and section 6 passes |

---

## 8. Where to go next

> 📚 **Study path:** 1) Note: [Case study: Apache holds 443](21-case-apache-443-dokploy.md), the full migration this module generalises · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking → *Ingress* ([lesson](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page)), where the same "one owner of 80/443" idea moves into the cluster · 3) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* ([course](https://kodekloud.com/courses/gitlab-ci-cd)) for recipe R8 done properly · 4) Practice: the ops-ladder L3 drill: make Traefik return 502 with a wrong port, then fix it from Traefik's logs alone.

**Level:** pick the next step for your stage from the second list below.

### Related modules

- The same server as a complete migration, with inventory, change request, cutover and rollback: [21 — Case study: Apache holds 443](21-case-apache-443-dokploy.md)
- Who owns a port, and how to move it safely: [22 — Who owns this port?](22-playbook-ports-inventory.md)
- When a deployed site stops answering (DNS, routing, TLS, proxy, app): [25 — Site down playbook](25-playbook-site-down.md)
- Traefik 404/502, Docker networks and Kubernetes incidents: [26 — Containers & Kubernetes playbook](26-playbook-containers-k8s.md)
- Apache, Nginx, Traefik and Dokploy in depth: [29 — Learn web servers & proxies](29-learn-webservers-proxies.md)
- Publishing, networks, Compose and Swarm: [30 — Learn Docker](30-learn-docker.md)
- Services, Ingress, Gateway API and the CKA: [31 — Learn Kubernetes](31-learn-kubernetes.md)
- Pipelines, infrastructure as code and SRE practice: [33 — Learn CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md)
- Hardening the surface you expose: [37 — Learn security & DevSecOps](37-learn-security-devsecops.md)
- Designing platforms rather than single servers: [39 — Learn senior architecture](39-learn-senior-architecture.md)
- Command references: [Network](02-network.md), [systemd](07-services-systemd.md), [Docker](14-docker-containers.md), [Kubernetes](15-kubernetes.md), [Web, HTTP & TLS](18-web-http-tls.md)
- Where these skills sit in your career: [40 — Career ladder](40-career-ladder.md) and the [34 — Roadmap](34-roadmap.md)

### Next step by stage

1. **[L0 · Fresher]** Repeat section 2 on every server you can log in to, and write PORTS.md for one of them. Then read [22 — Who owns this port?](22-playbook-ports-inventory.md) sections 2–4.
2. **[L1 · Junior]** Pass timed task 2, then do the drills in module 22. Run the section 6 checklist on everything you deploy from now on.
3. **[L2 · Mid]** Pass tasks 3–5, then replay phases 5–8 of [the case study](21-case-apache-443-dokploy.md) in your lab, including its rollback.
4. **[L3 · Senior]** Pass tasks 6–8, move recipe R8 to your real GitLab and Harbor, and use P11 in your CKA homelab until Ingress and Gateway API feel as familiar as Traefik routers.
5. **[L4 · Lead]** Pass task 9 and make the convention, PORTS.md and the checklist part of your team's change process ([40 — Career ladder](40-career-ladder.md), Lead stage).

### Official documentation

- Apache HTTP Server 2.4: [httpd.apache.org/docs/2.4](https://httpd.apache.org/docs/2.4/)
- Traefik: [doc.traefik.io/traefik](https://doc.traefik.io/traefik/)
- Dokploy: [docs.dokploy.com](https://docs.dokploy.com/)
- Docker: [docs.docker.com](https://docs.docker.com/)
- Kubernetes: [kubernetes.io/docs](https://kubernetes.io/docs/)
- Nginx: [nginx.org/en/docs](https://nginx.org/en/docs/)
