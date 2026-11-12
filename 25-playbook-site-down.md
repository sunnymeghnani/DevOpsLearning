# 25 — Site Down: DNS → Route → Firewall → TLS → Proxy → App

"The site is down" is a report, not a diagnosis. Between the user's browser and
your database sit at least eight layers, and each one fails in its own
recognisable way. This playbook is the **L2 Troubleshooter exit test** from the
ops ladder turned into a procedure: walk the request path from the client
outwards, stop at the first layer that fails, and **name that layer with
evidence**: a packet capture, a log line, or a piece of `curl -v` output. A
hunch does not count.

How to use it:

- **You have an exact error message** (`curl: (60)`, `502 Bad Gateway`, `AH00072`): find it in the error-text table in Section 1 and jump straight to that scenario.
- **You only know "it's down"**: start at Section 2, Step 0, and walk the steps in order. Each step tells you where to go next.
- **You are mid-incident with people waiting**: read Section 10 first (two minutes), send the first update, stabilise, then come back here.

**Who this module serves, stage by stage:**

| Stage | What to take from this module |
|---|---|
| [L0 · Fresher] | Section 1 (the request path and the failure-signature table) and Steps 0, 5 and 11. Run them on a test VM until each curl exit code means something to you. |
| [L1 · Junior] | The scenarios tagged L1 (§4.1, §5.1, §5.3, §6.3, §8.3, §9.1) on your own; the rest of Section 2 with a senior next to you. |
| [L2 · Mid] | **Your exit test.** Walk every layer in 15 minutes and name the broken one with evidence (Sections 12 and 14). Handle every scenario alone. |
| [L3 · Senior] | The "Prevent it next time" lists: monitoring, explicit defaults and configuration management, so the same outage cannot happen twice. §7.4 and capacity sizing in §7.2. |
| [L4 · Lead] | Section 10: lead the incident, keep the timeline, write the postmortem, and turn Section 12 into a team game day. |

Each section and scenario starts with a numbered 📚 study path (KodeKloud
lesson, handbook note, video, practice), and every scenario carries a level
tag such as [L2 · Mid].
The KodeKloud lesson comes first when the topic is new to most readers; the
handbook note comes first when it is a quick refresher.

**Your own server after the 81/444 move.** You freed 80/443 for Dokploy by
moving Apache to ports 81 and 444. Since then Traefik answers first for
**every** name on the box, so an Apache site that is "down" usually shows up
here as the Traefik default certificate (§6.4), a Traefik `404 page not found`
(§8.1) or a 502 from Traefik to Apache (§7.1), and certificate renewal for the
Apache names breaks (§6.3). [Deployment patterns](35-deployment-patterns.md)
analyses that fix and shows how to finish it with Traefik routing.

> 📚 **Study path:** 1) Note: [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md), area "One request, every layer" · 2) KodeKloud: *DevOps Pre-Requisite Course*: Networking Basics → Web Server → Security (SSL & TLS Basics), with their labs ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) · 3) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* ([YouTube](https://www.youtube.com/watch?v=9nCIjLlLVzY), 14 min) · 4) Practice: the break-it table in Section 12 on the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)).

Command reference lives elsewhere, so this module links instead of repeating:
[DNS](08-dns.md), [Network](02-network.md), [Web, HTTP & TLS](18-web-http-tls.md),
[Time & NTP](12-time-ntp.md), [Docker](14-docker-containers.md), [AWS](16-aws-cloud.md).
The theory behind each layer is in [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md)
and [Learn: web servers and reverse proxies](29-learn-webservers-proxies.md). The
real incident that started this handbook (Apache holding 443 while Dokploy needed it)
is in [Case study: Apache 443 and Dokploy](21-case-apache-443-dokploy.md).

> ⚠️ Every command and output here is illustrative and is meant to be run on **your**
> servers during **your** incident. Addresses use documentation ranges
> (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and example.com names. UPPERCASE
> words (HOST, PORT, CONTAINER, UNIT, DOMAIN) are placeholders. Outputs match
> Ubuntu 22.04/24.04 (curl 7.81/8.5, OpenSSL 3.0, Apache 2.4.52/2.4.58,
> Nginx 1.18/1.24, Traefik v3); wording differs slightly between versions.

---

## 1. The method: walk the request path

> 📚 **Study path:** 1) KodeKloud: *Networks and Communications*, Network Troubleshooting module, only if layers and routing still feel shaky ([course](https://kodekloud.com/courses/networks-and-communications)) · 2) Note: [Learn: networking](28-learn-networking.md), area "Layers and the tools that test them" · 3) Read: [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) · 4) Practice: learn the failure-signature table below by heart, then solve three [SadServers scenarios](https://sadservers.com/scenarios) using only this section.

**Level:** [L0 · Fresher] reads it; [L2 · Mid] applies it under time pressure.

### The request path

Every HTTP request crosses these layers in this order. A failure at one layer
hides every layer after it, so you never debug the app while DNS is broken.

```
  CLIENT  browser / curl / monitoring probe / another service
    │
    │ ① name → IP          /etc/hosts → systemd-resolved (127.0.0.53) → upstream resolver
    │                       → authoritative nameserver          getent ahosts, dig, resolvectl
    ▼
  NETWORK  client LAN → gateway → WAN / VPN → edge router / NAT  ip route get, mtr, tracepath
    │
    │ ② packets reach the server's IP
    ▼
  FILTERS  corporate firewall → cloud SG / NACL → host firewall (ufw / nftables / firewalld)
    │                                                            tcpdump, ufw status, nft list
    │ ③ TCP handshake on PORT                                    nc -vz, ss -ltnp
    ▼
  FRONT PROXY  Traefik (Dokploy) / Apache / Nginx / AWS ALB
    │   ④ TLS terminates here (certificate, chain, SNI)         openssl s_client
    │   ⑤ routing by Host header / SNI → picks an upstream      proxy access + error logs
    ▼
  APP SERVER  gunicorn / uvicorn / php-fpm / node / a container  systemctl, journalctl, docker logs
    │   ⑥ the app's own code and config                         curl 127.0.0.1:APP_PORT
    ▼
  DEPENDENCIES  PostgreSQL / MySQL / Redis / object storage / external APIs
                                                                 nc -vz, pg_isready, redis-cli ping
```

On your Dokploy hosts the front proxy is the `dokploy-traefik` container, the
upstream is a Swarm service on the `dokploy-network` overlay, and step ⑤ is a
Traefik router. On the old Apache hosts, step ⑤ is a `<VirtualHost>` with
`ProxyPass`, or PHP via `php-fpm`. On a host where Apache was moved to 81/444
(your fix), Apache becomes one more upstream behind Traefik: Traefik's router
for `shop.example.com` forwards to `http://192.0.2.10:81`, and step ⑤ happens
twice (Traefik picks Apache, then Apache picks the vhost). The layers are the
same in all three.

### Name the broken layer with evidence

The exit test is "name the broken layer **with evidence**". That rules out
"I think it's the firewall" and asks for something you can paste into the
incident channel:

| Layer | Evidence that names it |
|---|---|
| DNS | `getent ahosts` returns nothing or the wrong IP; `tcpdump port 53` shows queries leaving and no answer coming back |
| Route | `ip route get` picks the wrong interface; `mtr` loss that starts at one hop and continues to the last hop |
| Firewall / SG | `tcpdump` on the server shows the SYN arriving and no SYN-ACK leaving, plus a `UFW BLOCK` kernel log line; or no SYN at all while the client is sending |
| Listener | `ss -ltnp` shows nothing on the port, or `127.0.0.1:PORT` only |
| TLS | `openssl s_client` shows `Verify return code: 21`, an expired `notAfter`, or a SAN list without the name |
| Proxy | a log line: `AH01114`, `connect() failed (111)`, Traefik `502 ... connection refused` |
| App | `WORKER TIMEOUT` in gunicorn's log, a traceback, `curl 127.0.0.1:8000` failing on the box |
| Dependency | `FATAL: sorry, too many clients already`, `redis-cli ping` timing out |

Five habits that make the walk fast:

1. **One layer, one hypothesis, one test.** Each step below tests exactly one layer.
2. **Bisect with bypasses.** Each `curl` variant in Section 2 skips one more layer. When a variant suddenly works, the broken layer is the one it just skipped.
3. **Capture before you change.** A restart wipes the evidence. Spend 60 seconds copying logs first (Section 10 explains when stabilising comes first).
4. **Change one thing at a time**, and write the time down when you do.
5. **Ask "what changed?" early.** Most outages follow a deploy, a certificate renewal, a DNS edit, a package upgrade or a firewall change. See Section 9.2.

### Read the failure signature

How a connection fails tells you which layer stopped it before you run any
other command. Learn this table by heart:

| What curl says | Exit | On the wire | What it means | Go to |
|---|---|---|---|---|
| `Could not resolve host` | 6 | no TCP at all; maybe DNS queries with no answer | name → IP failed on **this** client | Step 1, §4.1 |
| `Connection refused` (curl 8: `Couldn't connect to server`) | 7 | SYN → RST | host reached; nothing listens on that IP:PORT, or a REJECT rule answered | Step 5, §5.1 |
| `Connection timed out` / `Timeout was reached` | 28 | SYN → silence, SYN retransmits | packets dropped: firewall, SG, wrong IP, routing, host down | Step 4, §5.2 |
| `No route to host` | 7 | ICMP host-unreachable | no ARP reply on the local subnet, **or** a firewalld/iptables REJECT with `icmp-host-prohibited` (`admin-prohibited` with the nftables backend) | Step 4, Step 8 |
| `Connection reset by peer` | 56 / 35 | handshake OK, then RST | something killed an open connection: app crash, docker-proxy with nothing behind it, IPS, keep-alive race | Step 13, §7.4 |
| `Empty reply from server` | 52 | connected, then FIN with no bytes | process accepted and closed: crashed worker, or a container app bound to 127.0.0.1 | Step 15, §5.3 |
| `SSL ... wrong version number` | 35 | TLS hello answered by plain HTTP | you spoke HTTPS to an HTTP port | Step 12 |
| `SSL certificate problem: ...` | 60 | handshake completes, verification fails | certificate, chain, name or clock | Step 10, §6 |
| `HTTP/1.1 4xx` or `5xx` | 0 | full HTTP exchange | an HTTP server answered; now find **which one** | Step 11, Section 3 |

> Refused is good news: the network path works and a host answered. Timeout is
> harder, because a packet disappeared somewhere and you have to find where.

### Where to stand: the bypass ladder

You can only see some layers from certain places. Walk down this ladder: each
rung skips one more layer. The first rung that **works** tells you the broken
layer is the one that rung just skipped:

| Rung | Run it from | Command | Layers it skips |
|---|---|---|---|
| 1 | your laptop | `curl -v https://app.example.com/` | none (full path) |
| 2 | your laptop | `curl -v --resolve app.example.com:443:192.0.2.10 https://app.example.com/` | DNS |
| 3 | the server | `curl -v --resolve app.example.com:443:127.0.0.1 https://app.example.com/` | DNS, network, firewall |
| 4 | the server | `curl -v -H 'Host: app.example.com' http://127.0.0.1/` | also TLS |
| 5 | the server | `curl -v http://127.0.0.1:8000/health` | also the proxy (talks to the app) |
| 6 | app's network namespace | `nc -vz db01.example.com 5432` | everything except the dependency |

Read it in both directions: if rung 1 fails and rung 2 works, DNS is guilty. If
rung 3 works and rung 2 fails, the problem is between your laptop and the
server (network, firewall, SG). If rung 5 works and rung 4 fails, the proxy is
guilty. On rung 4, a 301 or 308 redirect to `https://` counts as a pass: it
proves the proxy matched the host (Dokploy domains with HTTPS redirect plain
HTTP), so judge by "did the proxy route it", not by "was it 200".

### From a Windows or macOS client

The person reporting the outage is often on Windows or a Mac. Same layers,
different commands:

| Layer | Windows (PowerShell) | macOS |
|---|---|---|
| Resolve like apps do | `Resolve-DnsName app.example.com` | `dscacheutil -q host -a name app.example.com` |
| Flush DNS cache | `ipconfig /flushdns` | `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` |
| Route / path | `tracert -d 192.0.2.10`, `pathping 192.0.2.10` | `traceroute -n 192.0.2.10`, `mtr` (Homebrew) |
| TCP port test | `Test-NetConnection 192.0.2.10 -Port 443` | `nc -vz -G 3 192.0.2.10 443` |
| HTTP / TLS | `curl.exe -v https://app.example.com/` | `curl -v https://app.example.com/` |
| hosts file | `C:\Windows\System32\drivers\etc\hosts` | `/etc/hosts` |

In PowerShell, plain `curl` is an alias for `Invoke-WebRequest`. Type
`curl.exe`. Details are in [Windows](17-windows.md) and [macOS](20-macos.md).

### Find your scenario by error text

| You see | Scenario |
|---|---|
| `curl: (6) Could not resolve host` | §4.1 |
| `dig` answers, `curl` / app says it cannot resolve, or gets a different IP | §4.2 |
| Changed a DNS record, clients still go to the old IP | §4.3 |
| Lookups slow or failing intermittently, need resolver internals | §4.4 |
| `Connection refused` / `Couldn't connect to server` | §5.1 |
| `Connection timed out` / `Timeout was reached` | §5.2 |
| Works with `curl localhost` on the server, not from other machines | §5.3 |
| `curl: (60) ... unable to get local issuer certificate` | §6.1 |
| `no alternative certificate subject name matches target host name` | §6.2 |
| `certificate has expired` / `certificate is not yet valid` | §6.3 |
| Browser shows `TRAEFIK DEFAULT CERT` | §6.4 |
| `502 Bad Gateway`, `AH01102`, `connect() failed (111`, `upstream prematurely closed`, or Apache `503` with `AH01114` (backend refused) | §7.1 |
| `503 Service Unavailable`, `no available server`, `AH00484`, `AH01079` | §7.2 |
| `504 Gateway Timeout`, requests dying at about 30 s or 60 s, `WORKER TIMEOUT` | §7.3 (a Traefik 504 with `dial tcp ... i/o timeout`: §7.1) |
| Some requests fail, some succeed | §7.4 |
| `404 page not found` (plain text) vs an app-styled 404 | §8.1 |
| `ERR_TOO_MANY_REDIRECTS`, `curl: (47) Maximum (50) redirects followed` | §8.2 |
| `413 Request Entity Too Large`, `client intended to send too large body` | §8.3 |
| WebSocket connection failed, `400` / `426` on upgrade, drops after 60 s | §8.4 |
| Apache will not start, `AH00072 make_sock: could not bind`, `AH00526` | §9.1 |
| Everything broke right after a change | §9.2 |

---

## 2. The layered walk, step by step

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), area "One request, every layer" (a refresher of the theory behind every step) · 2) KodeKloud: *Learning Linux Basics Course & Labs*: Networking → DNS, Networking Basics, Troubleshooting ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 3) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) before Steps 3 and 7 (KodeKloud has no tcpdump lesson) · 4) Practice: walk Steps 0–16 against a fault you planted yourself (Section 12) on the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)).

**Level:** [L2 · Mid]: this walk is the Mid-level exit test. [L1 · Junior] engineers should run Steps 0, 5, 6, 11 and 14 alone.

This is the full walk for when you know nothing yet. Steps 0–3 are DNS, 4–9
are the network and filters, 10–12 are TLS and HTTP, 13–16 are proxy, app and
dependencies. In the example, `app.example.com` should resolve to `web01` at
192.0.2.10; your workstation is 192.0.2.50; the internal resolvers are
192.0.2.53 and 192.0.2.54.

### Step 0 — Pin down the symptom

**Goal:** turn "the site is down" into one precise, reproducible sentence.

```bash
# Reproduce from a terminal, not a browser (browsers cache DNS, redirects and HSTS)
curl -sS -o /dev/null --connect-timeout 5 --max-time 20 \
  -w 'code=%{http_code} ip=%{remote_ip} dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' \
  https://app.example.com/

# Is it one site or every site on the box? (shared layer vs one vhost)
for h in app.example.com shop.example.com legacy.example.com; do
  printf '%-22s ' "$h"; curl -sS -o /dev/null -m 10 -w '%{http_code}\n' "https://$h/" 2>&1
done

# Is a proxy variable silently in the path? (then curl talks to the proxy, not to you)
env | grep -i _proxy
```

```
code=502 ip=192.0.2.10 dns=0.012 connect=0.013 tls=0.041 ttfb=0.044 total=0.044
app.example.com        502
shop.example.com       200
legacy.example.com     200
```

**What it means:**

- `code=502` with `ip=192.0.2.10`: DNS resolved to the expected address, TCP and TLS completed (`tls` is non-zero), and an HTTP server answered with an error. Everything below HTTP works.
- `code=000` would mean no HTTP response at all; `curl` prints the reason on stderr (`(6)`, `(7)`, `(28)`, `(35)`, `(60)`), which tells you the layer straight away.
- Only `app` fails while its neighbours on the same proxy return 200: the shared layers (network, firewall, proxy process, wildcard cert) are fine. Focus on what is unique to `app`: its DNS record, its router or vhost, its backend.
- The timings show where the time went; a `ttfb` far above `tls` means the backend is slow, not the network.

Ask the reporter four questions while you type: **since when** (exact time),
**who** (everyone, one office, VPN users, IPv6 users), **what exactly** (URL,
error text, screenshot), and **what changed** (deploys, DNS edits, certificate
renewals, `apt` upgrades in `/var/log/apt/history.log`, firewall tickets).

**Why this step (now):** it costs 30 seconds and often skips half the walk.
"Down" turns out to be one path, one user behind a corporate proxy, or one
vhost. The curl exit code and the `%{remote_ip}` value tell you which layer to
start at, and the one-vs-all comparison separates shared infrastructure from a
single application.

**Next step:** `(6) Could not resolve` → Step 1. `(7)` refused or `(28)` timeout → Step 4.
`(35)` or `(60)` TLS errors → Step 10. Any HTTP status → Step 11 and Section 3.
Works for you but not for the reporter → repeat Step 0 and Step 1 **from their
machine or network**, because the difference is on their side.

### Step 1 — Compare what apps see with what DNS says

**Goal:** find out whether name resolution is involved, and which path is lying.

```bash
getent ahosts app.example.com      # resolves through glibc + /etc/nsswitch.conf: what curl/python/php get
dig +short app.example.com         # asks the nameserver in /etc/resolv.conf directly, skips /etc/hosts
dig +short AAAA app.example.com    # is there an IPv6 answer too? clients prefer it
grep -E '^hosts:' /etc/nsswitch.conf
grep -vE '^\s*(#|$)' /etc/hosts    # any static override for this name?
```

```
$ getent ahosts app.example.com
192.0.2.10      STREAM app.example.com
192.0.2.10      DGRAM
192.0.2.10      RAW
$ dig +short app.example.com
192.0.2.10
$ dig +short AAAA app.example.com
$ grep -E '^hosts:' /etc/nsswitch.conf
hosts:          files dns
```

**What it means:**

- Both return the expected IP: DNS works **for this machine**. Move on.
- `getent` prints nothing and exits with code 2: the name does not resolve on the path applications use. That is `curl: (6)`.
- `getent` and `dig` disagree: something before DNS in the `hosts:` line answered first. Usually a stale `/etc/hosts` line, or `mdns4_minimal [NOTFOUND=return]` swallowing a `.local` name. See §4.2.
- An unexpected AAAA answer: dual-stack clients try IPv6 first. If the IPv6 path is broken, some users see slowness or failures while your IPv4 tests pass. Test with `curl -6` and `curl -4`.

**Why this step (now):** DNS is the first layer, and these two commands take
two seconds. `curl` resolves through `getaddrinfo()`, which follows
`/etc/nsswitch.conf` (`files` = `/etc/hosts` first, then `dns`); `dig` skips all
of that and asks a nameserver directly. Comparing the two tells you both
whether DNS is involved and which source is wrong, before you touch a resolver.

**Next step:** both correct → Step 4 (DNS is cleared). `getent` fails → Step 2.
The two disagree → §4.2. Both return the same **wrong** IP → §4.3.

### Step 2 — Ask the resolver, then the authority

**Goal:** find which resolver this host uses and whether it, its upstream, or the
authoritative server is failing.

```bash
ls -l /etc/resolv.conf               # should be a symlink to the systemd stub on Ubuntu
resolvectl status                    # which upstream DNS servers each interface uses
resolvectl query app.example.com     # resolve through systemd-resolved, with source and timing
dig @192.0.2.53 app.example.com      # ask the upstream directly, skipping the 127.0.0.53 stub
dig +trace app.example.com           # walk delegation from the root (public names only)
```

```
$ ls -l /etc/resolv.conf
lrwxrwxrwx 1 root root 39 Mar 12  2026 /etc/resolv.conf -> ../run/systemd/resolve/stub-resolv.conf

$ resolvectl status
Global
         Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
  resolv.conf mode: stub

Link 2 (ens18)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53 192.0.2.54
        DNS Domain: corp.example.com

$ resolvectl query app.example.com
app.example.com: resolve call failed: All attempts to contact name servers or networks failed

$ dig @192.0.2.53 app.example.com
;; communications error to 192.0.2.53#53: timed out
;; communications error to 192.0.2.53#53: timed out
;; communications error to 192.0.2.53#53: timed out

; <<>> DiG 9.18.28-0ubuntu0.24.04.1-Ubuntu <<>> @192.0.2.53 app.example.com
; (1 server found)
;; global options: +cmd
;; no servers could be reached
```

**What it means:**

- `resolv.conf mode: stub` and the symlink are normal on Ubuntu: apps ask 127.0.0.53, and systemd-resolved forwards to the `DNS Servers` listed per link. If `/etc/resolv.conf` is a plain file pointing at a dead IP, someone or something replaced it.
- `All attempts to contact name servers or networks failed`: the upstreams did not answer at all. That points at the resolver hosts, or a firewall in between, not at the record.
- `resolve call failed: 'app.example.com' not found` would mean an NXDOMAIN answer: the resolvers work and say the name does not exist (typo, missing record, wrong zone).
- `dig @192.0.2.53` timing out confirms it independently of systemd-resolved. Repeat with `@192.0.2.54`: if one works, you have one dead resolver.
- In `dig +trace`, the last section, answered by the zone's own nameserver, is the truth. If the trace answer differs from your resolver's, your resolver's cache is stale (§4.3).

**Why this step (now):** Step 1 showed resolution fails. The next question is
**which hop** in the resolver chain fails: the local stub, the configured
upstream, or the authoritative data. Asking each one directly with `dig @SERVER`
isolates them one at a time. `dig +trace` only works for publicly delegated
names and needs outbound DNS to the internet, which many on-prem networks block.
For internal zones, ask the internal servers directly instead.

**Next step:** upstream unreachable → Step 3 (prove it on the wire). NXDOMAIN
from every server → the record is missing; fix it in the zone. Stub fails, upstream works
→ §4.4 (debug systemd-resolved). Answers fine here but `getent` still fails → §4.2.

### Step 3 — Watch DNS on the wire

**Goal:** see with your own eyes whether queries leave the host, which server
they go to, and whether answers come back.

```bash
# Terminal 1: capture DNS on all interfaces (UDP and TCP 53)
sudo tcpdump -ni any port 53

# Terminal 2: repeat the failing lookup
getent ahosts app.example.com
```

```
listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144 bytes
10:20:01.101234 lo    In  IP 127.0.0.1.53412 > 127.0.0.53.53: 4521+ [1au] A? app.example.com. (44)
10:20:01.101301 lo    In  IP 127.0.0.1.53412 > 127.0.0.53.53: 7731+ [1au] AAAA? app.example.com. (44)
10:20:01.101890 ens18 Out IP 192.0.2.21.41877 > 192.0.2.53.53: 31337+ [1au] A? app.example.com. (44)
10:20:01.101950 ens18 Out IP 192.0.2.21.39012 > 192.0.2.53.53: 1822+ [1au] AAAA? app.example.com. (44)
10:20:06.103112 ens18 Out IP 192.0.2.21.41877 > 192.0.2.54.53: 31337+ [1au] A? app.example.com. (44)
10:20:06.103170 ens18 Out IP 192.0.2.21.39012 > 192.0.2.54.53: 1822+ [1au] AAAA? app.example.com. (44)
```

**What it means:**

- The `lo` lines are your app asking the local stub. The `ens18 Out` lines are systemd-resolved forwarding to the real upstream.
- Queries go **out** to 192.0.2.53, nothing comes **in**, and five seconds later the resolver retries against 192.0.2.54, which also stays silent. That is proof the query leaves this host and dies on the way to or at the resolvers.
- A healthy exchange has a matching `In` line: `192.0.2.53.53 > 192.0.2.21.41877: 31337 1/0/1 A 192.0.2.10 (60)`, where `1/0/1` means one answer record.
- `NXDomain` in the reply means the resolver answered "no such name". Look for names like `app.example.com.corp.example.com` too: that is search-domain expansion at work (§4.2).
- No `ens18 Out` lines at all: the stub answered from cache, or never forwarded (check `resolvectl status` for a link with no DNS servers).

**Why this step (now):** a capture turns "I think DNS is broken" into "queries
leave on ens18 to 192.0.2.53 and no reply arrives within 5 s". That is enough
to hand to the network or DNS team. It also separates a local resolver problem
(queries never leave) from an upstream or firewall problem (queries leave,
silence) in one look, which no amount of reading config files can do.

**Next step:** queries leave, no replies → test the path to the resolver with
Step 4 and `dig +tcp @192.0.2.53` (firewalls sometimes block UDP 53 only), then
escalate with the capture. Replies come back but the app still fails → §4.2.
Queries never leave → §4.4.

### Step 4 — Check the route

**Goal:** confirm the client has a sane route to the server IP and find where
packets stop if they do.

```bash
ip route get 192.0.2.10            # which interface, gateway and source IP the kernel will use
ip -br addr                        # is that interface UP with the expected address?
ping -c 3 -W 1 192.0.2.10          # ICMP reachability (may be blocked: not proof of failure)
mtr -rwn -c 50 192.0.2.10          # per-hop loss and latency, 50 probes
tracepath -n 192.0.2.10            # path + path MTU, no root needed
ip neigh show 192.0.2.10           # same subnet only: did ARP resolve the MAC?
```

```
$ ip route get 192.0.2.10
192.0.2.10 dev ens18 src 192.0.2.50 uid 1000
    cache

$ mtr -rwn -c 50 203.0.113.10
Start: 2026-10-03T10:24:11+0000
HOST: ops01                 Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 192.0.2.1            0.0%    50    0.5   0.5   0.3   1.2   0.1
  2.|-- 198.51.100.1         0.0%    50    3.1   3.3   2.9   6.0   0.4
  3.|-- 198.51.100.9        62.0%    50    9.8   9.9   9.5  11.2   0.3
  4.|-- 203.0.113.10         0.0%    50   12.4  12.6  12.1  14.9   0.4

$ ip neigh show 192.0.2.10
192.0.2.10 dev ens18 FAILED
```

**What it means:**

- `ip route get` with `dev ens18` and no `via`: the server is on the same subnet, so delivery depends on ARP. With `via 192.0.2.1`, it goes through the gateway. A surprising `dev` (a VPN `tun0`, a Docker bridge `br-…`, a second NIC) is a finding on its own.
- In the mtr report, hop 3 shows 62 % loss but the final hop shows 0 %: hop 3 just rate-limits ICMP replies to itself. **Only loss that persists to the last hop is real.**
- `ip neigh ... FAILED`: on the same subnet, nobody answered ARP for 192.0.2.10. The host is down, its interface is down, it is in a different VLAN, or there is an IP conflict. That is also what produces `No route to host`.
- `ping` failing alone proves nothing. Many networks drop ICMP. The TCP test in Step 5 is the one that counts.

**Why this step (now):** DNS gave you an IP; now check the client can get packets
to it before testing ports. Route problems (wrong interface after a VPN connects,
two default routes after a netplan change, a Docker bridge subnet that overlaps a
real office subnet such as 172.17.0.0/16) produce timeouts that look exactly
like firewall drops. `ip route get` answers "which way will the packet go" in
one line.

**Next step:** route looks right → Step 5. Wrong interface or overlapping subnet
→ fix routing (see [Network](02-network.md) section 8, use `sudo netplan try` for
safe changes). Loss persisting to the last hop → path problem, escalate with the
mtr report (see [Network speed playbook](24-playbook-network-speed.md)).
`FAILED` ARP → the server or its NIC is down; get console access.

### Step 5 — Test the TCP port from the client

**Goal:** find out whether a TCP handshake on the service port succeeds, is
refused, or times out.

```bash
nc -vz -w 3 app.example.com 443    # -z: just connect; -w 3: give up after 3 s
nc -vz -w 3 app.example.com 80
nc -vz -w 3 192.0.2.10 443         # by IP: takes DNS out of the picture
```

```
Connection to app.example.com (192.0.2.10) 443 port [tcp/https] succeeded!
nc: connect to app.example.com (192.0.2.10) port 80 (tcp) failed: Connection refused
nc: connect to 192.0.2.10 port 443 (tcp) timed out: Operation now in progress
```

**What it means:**

- `succeeded!`: DNS, route, every firewall and the listener are fine for this port. The problem is TLS or above. Go up the stack.
- `Connection refused`: the packet **reached** a host that answered with RST. Nothing listens on that IP:PORT, or a firewall rule REJECTs. The network path is fine.
- `timed out`: the SYN, or the SYN-ACK coming back, vanished. Suspect a firewall DROP, a security group, a NACL, NAT, the wrong IP, or a host that is down.
- A name with several A/AAAA records: `nc` tries each in turn, so you may see one refused followed by one success. Note which IP fails.

**Why this step (now):** it is the cheapest test that clears four layers at
once: route, every firewall on the path, and the listener. It also produces the
refused / timeout split that decides whether you look at the server's
**process** (refused) or at the **path** (timeout). It works without TLS or HTTP
knowledge, so it also works for databases, Redis and SSH.

**Next step:** succeeded → Step 10 (TLS). Refused → Step 6 on the server, then
§5.1. Timed out → Step 7 on the server (do SYNs arrive?), then §5.2.

### Step 6 — Confirm the listener on the server

**Goal:** see exactly which process listens on the port, and on which address.

```bash
sudo ss -ltnp 'sport = :443'                  # -l listening, -t TCP, -n numeric, -p process (needs root)
sudo ss -ltnp                                 # everything listening, to spot "wrong port" mistakes
sudo lsof -nP -iTCP:443 -sTCP:LISTEN          # same answer, different view
systemctl list-sockets --no-pager             # systemd socket units can hold ports too
```

```
$ sudo ss -ltnp 'sport = :443'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*     users:(("docker-proxy",pid=2817,fd=7))
LISTEN 0      4096            [::]:443          [::]:*     users:(("docker-proxy",pid=2824,fd=7))

$ sudo ss -ltnp | grep -E ':(80|443|3000|8000|8080)\b'
LISTEN 0      4096         0.0.0.0:80        0.0.0.0:*     users:(("docker-proxy",pid=2803,fd=7))
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*     users:(("docker-proxy",pid=2817,fd=7))
LISTEN 0      4096         0.0.0.0:3000      0.0.0.0:*     users:(("docker-proxy",pid=2790,fd=7))
LISTEN 0      511       192.0.2.10:8080      0.0.0.0:*     users:(("apache2",pid=1342,fd=4),("apache2",pid=1341,fd=4))
LISTEN 0      2048       127.0.0.1:8000      0.0.0.0:*     users:(("gunicorn",pid=1550,fd=5),("gunicorn",pid=1549,fd=5))
```

**What it means:**

- `Local Address` is the most important column. `0.0.0.0:443` / `[::]:443` / `*:443` = all interfaces. `127.0.0.1:8000` = **this host only**: correct for an app behind a local proxy, and the reason remote clients get refused (§5.3). A specific IP means only connections to that IP are accepted.
- `docker-proxy` on 80/443 means a container published those ports (here Traefik from Dokploy). `docker-proxy` on 3000 is the Dokploy UI: the installer publishes the `dokploy` Swarm service with `mode=host`, which maps the port like a plain container (check with `docker service inspect dokploy --format '{{json .Endpoint.Ports}}'`: `"PublishMode":"host"`). A port held by `dockerd` itself is a Swarm **ingress** (routing-mesh) published port. To see which container is behind it, use `docker ps --format '{{.Names}}\t{{.Ports}}'` (full method in [Ports inventory](22-playbook-ports-inventory.md)).
- Apache has been moved to `192.0.2.10:8080`: off 80/443 so Traefik can own them, on an address the Traefik container can reach, with ufw allowing 8080 only from the Docker bridge range. That is the migration pattern from [the case study](21-case-apache-443-dokploy.md): Traefik forwards the remaining Apache sites to it. A `127.0.0.1` bind would not work for that, because inside the Traefik container `127.0.0.1` is Traefik itself. The port number is a choice: the case study uses 8081, your own fix used 81 and 444 (see [Deployment patterns](35-deployment-patterns.md)). What matters is the bind address and a firewall that keeps the port internal.
- `Recv-Q` on a LISTEN line is the number of connections waiting to be accepted; `Send-Q` is the backlog limit. If `Recv-Q` sits close to `Send-Q`, the app is not accepting fast enough and new clients time out (§7.2).
- Nothing listed for the port: the service is down or listens elsewhere. That explains a "refused".

**Why this step (now):** Step 5 told you how the connection failed; this tells
you why from the server's side. It also catches the most common mistakes,
such as the wrong port, a loopback-only bind, or the port taken by a different
service than you assumed (Apache vs Traefik: the incident that started this
handbook), in one command and without touching anything.

**Next step:** nothing listening → Step 14 (why is the service not running?).
Listening on 127.0.0.1 only → §5.3. Listening correctly but the client times out
→ Step 7. Listening and the client connects → Step 10.

### Step 7 — Watch the SYNs arrive

**Goal:** prove whether the client's packets reach the server, and whether the
server answers.

```bash
# On the server. Only SYN and RST packets for port 443 from the test client:
sudo tcpdump -ni any 'tcp port 443 and host 192.0.2.50 and (tcp[tcpflags] & (tcp-syn|tcp-rst) != 0)'

# Meanwhile, on the client:
nc -vz -w 3 192.0.2.10 443
```

```
10:31:02.118201 ens18 In  IP 192.0.2.50.53122 > 192.0.2.10.443: Flags [S], seq 1849023114, win 64240, options [mss 1460,sackOK,TS val 3011 ecr 0,nop,wscale 7], length 0
10:31:03.141882 ens18 In  IP 192.0.2.50.53122 > 192.0.2.10.443: Flags [S], seq 1849023114, win 64240, options [mss 1460,sackOK,TS val 4034 ecr 0,nop,wscale 7], length 0
10:31:05.157913 ens18 In  IP 192.0.2.50.53122 > 192.0.2.10.443: Flags [S], seq 1849023114, win 64240, options [mss 1460,sackOK,TS val 6050 ecr 0,nop,wscale 7], length 0
```

**What it means:** read the flags column.

- `[S]` in, `[S.]` (SYN-ACK) out: the server accepts. If the client still times out, the SYN-ACK is lost on the way back (asymmetric routing, a stateful firewall seeing only half the flow).
- `[S]` in, `[R.]` out: the kernel answered "nothing here". That is a refused connection, seen from the server (§5.1).
- `[S]` in, **nothing out**, the same `seq` retransmitted after 1 s, 2 s, 4 s: the SYN arrived and the host dropped it. tcpdump sees incoming packets **before** the host firewall, so this pattern almost always means your own ufw / nftables / iptables (Step 8), or reverse-path filtering on a multi-homed host.
- **No lines at all** while the client is sending: the packet never reached this host. The drop is upstream (cloud SG, NACL, corporate firewall, NAT port-forward), or DNS sends clients somewhere else (compare with `%{remote_ip}` from Step 0).

**Why this step (now):** a timeout has many possible causes spread across
several teams' equipment. One capture on the server cuts the search space in
half: either the problem is on this host (packets arrive) or it is not (packets
never arrive). That decides whether you open the host firewall or call the
network team, and the capture is the evidence you bring them.

**Next step:** SYN in, nothing out → Step 8. Nothing arrives → Step 9. SYN in,
RST out → Step 6 and §5.1. SYN-ACK out but the client never completes → check the
return route with `ip route get 192.0.2.50 from 192.0.2.10` (§5.2).

### Step 8 — Check the host firewall

**Goal:** find the rule on the server that drops or rejects the traffic.

```bash
sudo ufw status verbose                                      # Ubuntu's front end
sudo journalctl -k --since '15 min ago' | grep -E 'UFW (BLOCK|AUDIT)'   # needs ufw logging on
sudo nft list ruleset | less                                 # the real ruleset (ufw, Docker and others)
sudo iptables -L INPUT -n -v --line-numbers                  # per-rule packet counters (iptables-nft view)
sudo firewall-cmd --list-all                                 # RHEL/Rocky: firewalld instead of ufw
```

```
$ sudo ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    192.0.2.0/24
80/tcp                     ALLOW IN    Anywhere

$ sudo journalctl -k --since '15 min ago' | grep 'UFW BLOCK'
Oct 03 10:31:02 web01 kernel: [UFW BLOCK] IN=ens18 OUT= MAC=52:54:00:3a:91:0c:52:54:00:8e:12:44:08:00 SRC=192.0.2.50 DST=192.0.2.10 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=40211 DF PROTO=TCP SPT=53122 DPT=443 WINDOW=64240 RES=0x00 SYN URGP=0
```

**What it means:**

- Default `deny (incoming)` and no rule for 443: the SYNs from Step 7 are dropped by design. The `UFW BLOCK` line with `DPT=443 ... SYN` is the evidence: source, destination, port and timestamp in one line.
- Rules exist but traffic is still blocked: read the `-v` counters in `iptables -L -n -v`. The rule whose packet counter grows while you retry is the one matching. Order matters; the first match wins.
- RHEL/Rocky firewalld rejects with an ICMP "prohibited" message by default (`icmp-host-prohibited` with the iptables backend, `admin-prohibited` with the nftables backend that RHEL 8 and later use), so clients see `No route to host` instead of a timeout. That is a firewall message, not a routing problem.
- `Status: inactive` and an empty ruleset: the host firewall is cleared. Go to Step 9.

> ⚠️ **Never "test" by flushing the firewall** (`iptables -F`, `nft flush ruleset`).
> With a default-drop policy it can lock you out of SSH, and it deletes Docker's
> NAT and forwarding chains, so every container loses networking until Docker is
> restarted. The safe test is to add one narrow, temporary allow rule for your
> source and port, check it, and remove it:
> `sudo ufw allow from 192.0.2.50 to any port 443 proto tcp`, then later
> `sudo ufw delete allow from 192.0.2.50 to any port 443 proto tcp`.

**Why this step (now):** Step 7 proved the packet reaches the host and dies
there. The host firewall is the only thing on the host that drops a SYN without
answering, so it is the one place left to look. Reading the logs and counters
is read-only and names the exact rule, which is far safer than "turn the
firewall off and see".

**Next step:** a blocking rule found → fix it (§5.2 Fix & verify). No rule
matches but SYNs still vanish → check reverse-path filtering
(`sysctl net.ipv4.conf.all.rp_filter`) and the return route (§5.2).
Packets never arrived in Step 7 → Step 9.

### Step 9 — Check cloud filters and the Docker bypass

**Goal:** find the filter **outside** the host that eats the packets, or explain
why a port is reachable even though ufw says deny.

```bash
# AWS: which security groups sit on the instance, and do they allow 443?
aws ec2 describe-instances --instance-ids i-0abc1234567890def \
  --query 'Reservations[].Instances[].SecurityGroups[]'
aws ec2 describe-security-groups --group-ids sg-0abc1234567890def \
  --query 'SecurityGroups[].IpPermissions[?ToPort==`443`]'
# NACLs are stateless: they must allow 443 in AND the ephemeral return ports out
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-0abc1234567890def \
  --query 'NetworkAcls[].Entries[]'

# Docker: ufw says one thing, Docker's NAT table says another
sudo ufw status | grep 8081
sudo iptables -t nat -L DOCKER -n
sudo iptables -L DOCKER-USER -n -v     # the chain Docker reserves for YOUR filtering rules
```

```
$ sudo ufw status | grep 8081
8081                       DENY        Anywhere

$ sudo iptables -t nat -L DOCKER -n
Chain DOCKER (2 references)
target     prot opt source               destination
DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:80 to:172.18.0.3:80
DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:443 to:172.18.0.3:443
DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8081 to:172.17.0.5:8080
```

**What it means:**

- **Cloud side:** a missing inbound rule for 443 in the SG, or a NACL without the return range `1024-65535`, gives exactly the "nothing arrives" pattern from Step 7. VPC Flow Logs show `REJECT` for that flow. The full checklist and Reachability Analyzer are in [AWS](16-aws-cloud.md) section 5.
- **On-prem:** you rarely see the edge firewall or the NAT port-forward yourself. Hand the network team the Step 7 capture: "SYNs from 198.51.100.77 to 203.0.113.10:443 at 10:31 UTC never reach web01 (192.0.2.10)". That is a request they can act on.
- **Docker:** `ufw deny 8081` lives in the INPUT chain. A published port is rewritten by the DNAT rule in PREROUTING **before** INPUT, and the packet then travels through FORWARD to the container, so ufw's rule never sees it. Port 8081 is open to the world even though ufw lists DENY. The reverse also happens: an `ALLOW` you add in ufw does nothing for a container port.

**Why this step (now):** Step 7 showed the packets never reach the host (or
the port is reachable when it should not be). Everything left is outside the
host's own INPUT rules, and you need either cloud API reads or another team.
Docker's NAT is in this step because it is the one host-level filter path that
ufw does not show you.

**Next step:** missing SG/NACL rule → add it (least privilege: the source CIDR
you need, not `0.0.0.0/0` unless it is a public site), retest with Step 5.
On-prem drop → escalate with the capture. Docker port that should not be public
→ publish it on loopback (`127.0.0.1:18000:8000`), better still do not publish it
at all and route through Traefik on `dokploy-network`, or filter in DOCKER-USER:

```bash
# Allow container port 8081 only from the office subnet (match the ORIGINAL dport: DNAT changed it).
# --ctdir ORIGINAL limits the match to client-to-container packets, so replies to the
# containers' own outbound connections to some remote port 8081 are not dropped.
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctdir ORIGINAL --ctorigdstport 8081 ! -s 192.0.2.0/24 -j DROP
# Rollback: delete the exact same rule
sudo iptables -D DOCKER-USER -i ens18 -p tcp -m conntrack --ctdir ORIGINAL --ctorigdstport 8081 ! -s 192.0.2.0/24 -j DROP
```

Rules added with `iptables -I` are lost on reboot. Persist them with your
configuration management, not by hand. Background:
[Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/),
and its iptables page with the `DOCKER-USER` and conntrack examples
([Docker docs: iptables](https://docs.docker.com/engine/network/firewall-iptables/)).

### Step 10 — Inspect the TLS handshake

**Goal:** see the certificate and chain the server actually sends for this
name, and whether this client trusts them.

```bash
# Full handshake with SNI, showing every certificate the server sends
openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null

# The leaf only: subject, issuer, validity, names
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName

# Also check the host name (s_client does NOT check it unless asked)
openssl s_client -connect app.example.com:443 -servername app.example.com \
  -verify_hostname app.example.com </dev/null 2>/dev/null | grep 'Verify return code'

# Compare with the file on disk: a renewed cert is not served until the proxy reloads
sudo openssl x509 -noout -enddate -in /etc/letsencrypt/live/app.example.com/fullchain.pem
```

```
$ openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null
CONNECTED(00000003)
depth=2 C = US, O = Example Corp, CN = Example Corp Root CA
verify return:1
depth=1 C = US, O = Example Corp, CN = Example Corp Issuing CA 1
verify return:1
depth=0 CN = app.example.com
verify return:1
---
Certificate chain
 0 s:CN = app.example.com
   i:C = US, O = Example Corp, CN = Example Corp Issuing CA 1
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Sep  1 08:12:44 2026 GMT; NotAfter: Nov 30 08:12:43 2026 GMT
-----BEGIN CERTIFICATE-----
MIIF...
-----END CERTIFICATE-----
 1 s:C = US, O = Example Corp, CN = Example Corp Issuing CA 1
   i:C = US, O = Example Corp, CN = Example Corp Root CA
   a:PKEY: rsaEncryption, 4096 (bit); sigalg: RSA-SHA256
   v:NotBefore: Jan 10 00:00:00 2025 GMT; NotAfter: Jan 10 00:00:00 2030 GMT
-----BEGIN CERTIFICATE-----
MIIG...
-----END CERTIFICATE-----
---
Server certificate
subject=CN = app.example.com
issuer=C = US, O = Example Corp, CN = Example Corp Issuing CA 1
---
SSL handshake has read 3412 bytes and written 393 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
    Verify return code: 0 (ok)

$ openssl s_client ... | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN = app.example.com
issuer=C = US, O = Example Corp, CN = Example Corp Issuing CA 1
notBefore=Sep  1 08:12:44 2026 GMT
notAfter=Nov 30 08:12:43 2026 GMT
X509v3 Subject Alternative Name:
    DNS:app.example.com, DNS:www.app.example.com
```

**What it means:**

- `Certificate chain` lists what the **server sends**: `0` is the leaf, `1` the intermediate. A healthy server sends leaf + intermediate(s); the root comes from the client's trust store. Only a `0` entry means the intermediate is missing.
- `depth=` lines are the client's verification walk. `Verify return code: 0 (ok)` means the chain is trusted **by this machine**. This machine has the private Example Corp root installed; a laptop without it fails with code 19 or 20.
- The `v:` line and `notAfter` show the validity window. Compare it with `date -u` on **both** client and server.
- `X509v3 Subject Alternative Name` is the list of names the certificate covers. Browsers ignore the CN completely; curl and most libraries fall back to it only when the certificate has no DNS or IP SAN at all. Treat the SAN list as the truth: the name must be in it.
- The return codes you will meet:

| Verify return code | Meaning | Scenario |
|---|---|---|
| 0 (ok) | chain trusted (host name not checked unless you add `-verify_hostname`) | Step 11 |
| 9 certificate is not yet valid | notBefore is in the future for this clock | §6.3 |
| 10 certificate has expired | notAfter passed, or the clock is wrong | §6.3 |
| 18 self-signed certificate | leaf signed by itself, for example TRAEFIK DEFAULT CERT | §6.4 |
| 19 self-signed certificate in certificate chain | chain ends in a root this machine does not trust (private CA) | §6.1 |
| 20 unable to get local issuer certificate | issuer of the last cert sent is unknown here | §6.1 |
| 21 unable to verify the first certificate | usually: the server sent the leaf without its intermediate | §6.1 |
| 62 hostname mismatch | with `-verify_hostname`: name not in SAN | §6.2 |

**Why this step (now):** the TCP port answers (Step 5), so TLS is the next
layer. Certificate problems are a top cause of "site down" reports because
browsers block the page completely. `openssl s_client` shows the raw chain and
dates even when verification fails, while curl stops at the first error and
hides the rest. Always pass `-servername`: without SNI, a proxy hosting many
names hands back its **default** certificate and you debug the wrong one.

**Next step:** code 0 and the name is in the SAN → Step 11. Code 19/20/21 → §6.1.
Name missing → §6.2. Dates wrong → §6.3. Subject `TRAEFIK DEFAULT CERT` → §6.4.
Served cert older than the file on disk → reload the proxy (§6.3). Handshake
error `wrong version number` → the port speaks plain HTTP (Step 12).

### Step 11 — Read curl -v end to end

**Goal:** see the whole exchange in one place and identify **who** produced the
HTTP response.

```bash
curl -v -o /dev/null https://app.example.com/            # verbose, discard the body
curl -sv https://app.example.com/ 2>&1 | grep -E '^(\* +(Connected|Server cert|subject|expire|SSL)|< |> GET)'
curl -sI https://app.example.com/                        # response headers only (HEAD)
curl -s -D - -o /dev/null https://app.example.com/        # headers of a real GET
```

```
$ curl -v https://app.example.com/          # without -o, so the short error body is visible too
* Host app.example.com:443 was resolved.
* IPv6: (none)
* IPv4: 192.0.2.10
*   Trying 192.0.2.10:443...
* Connected to app.example.com (192.0.2.10) port 443
* ALPN: curl offers h2,http/1.1
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
*  CAfile: /etc/ssl/certs/ca-certificates.crt
*  CApath: /etc/ssl/certs
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256 / X25519 / RSASSA-PSS
* ALPN: server accepted h2
* Server certificate:
*  subject: CN=app.example.com
*  start date: Sep  1 08:12:44 2026 GMT
*  expire date: Nov 30 08:12:43 2026 GMT
*  subjectAltName: host "app.example.com" matched cert's "app.example.com"
*  issuer: C=US; O=Example Corp; CN=Example Corp Issuing CA 1
*  SSL certificate verify ok.
> GET / HTTP/2
> Host: app.example.com
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/2 502
< content-type: text/plain; charset=utf-8
< content-length: 11
< date: Sat, 03 Oct 2026 10:40:12 GMT
<
Bad Gateway
```

**What it means:** read it top to bottom; every `*` line is a layer that passed.

- `IPv4: 192.0.2.10`: DNS gave the expected address (from the client's point of view).
- `Connected to ... port 443`: route, firewalls and listener passed.
- `SSL certificate verify ok` and `matched cert's "app.example.com"`: TLS passed, with the right certificate.
- `> GET / HTTP/2`: the request went out. `<` lines are what came back.
- `HTTP/2 502`, `text/plain`, an 11-byte body `Bad Gateway`, **no `server:` header**: that is Traefik's own error page. Traefik received the request, matched a router (otherwise it would be a 404), and failed to get an answer from the backend. Apache would add `server: Apache/2.4.58 (Ubuntu)` and an HTML page, Nginx `server: nginx/1.24.0 (Ubuntu)`.

**Why this step (now):** curl is the one tool that walks every layer the way a
real client does, and its verbose output records which layers passed. At the
HTTP layer, the question changes from "does it connect" to "who answered".
A 502 from Traefik, from Apache behind Traefik, or from the app itself are three
different problems with three different log files. The headers and body
format tell you which (Section 3).

**Next step:** 5xx or 4xx from the proxy → Step 13 and the matching scenario
(§7, §8). Response from the app itself (framework error page, JSON error, an
`x-powered-by` header) → Step 14. Unexpected redirect → §8.2. Works from here but
not for users → compare their `%{remote_ip}` and Step 12.

### Step 12 — Bypass DNS and the front proxy

**Goal:** test one layer in isolation by pinning the name, the target, or the
Host header.

```bash
# 1. Skip DNS but keep TLS, SNI and Host correct: pin the name to an IP for one request
curl -v --resolve app.example.com:443:192.0.2.10 https://app.example.com/

# 2. Pin name:port to a DIFFERENT host and port (Traefik on 8443 during a migration,
#    or one specific node behind a load balancer). SNI, Host and cert check stay correct.
curl -v --connect-to app.example.com:443:192.0.2.11:8443 https://app.example.com/

# 3. Plain HTTP: the Host header alone selects the vhost or Traefik router
curl -v -H 'Host: app.example.com' http://192.0.2.10/

# 4. On the server itself: skip network and firewall, still go through TLS and the proxy
curl -v --resolve app.example.com:443:127.0.0.1 https://app.example.com/
```

```
$ curl -v --resolve app.example.com:443:192.0.2.10 https://app.example.com/
* Added app.example.com:443:192.0.2.10 to DNS cache
* Hostname app.example.com was found in DNS cache
*   Trying 192.0.2.10:443...
* Connected to app.example.com (192.0.2.10) port 443
...
< HTTP/2 200

$ curl -v --connect-to app.example.com:443:192.0.2.11:8443 https://app.example.com/
* Connecting to hostname: 192.0.2.11
* Connecting to port: 8443
*   Trying 192.0.2.11:8443...
...

$ curl -v https://app.example.com:8080/
*   Trying 192.0.2.10:8080...
* Connected to app.example.com (192.0.2.10) port 8080
* ALPN: curl offers h2,http/1.1
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
* OpenSSL/3.0.13: error:0A00010B:SSL routines::wrong version number
curl: (35) OpenSSL/3.0.13: error:0A00010B:SSL routines::wrong version number
```

**What it means:**

- With `--resolve` the request gets a 200, while the normal request fails: the server and proxy are fine, and **DNS** (or what DNS points to) is the broken layer for this client. Compare with `getent ahosts`.
- `--connect-to` is the migration tool: you can test the new Traefik on a temporary port, with the real hostname and certificate, before moving DNS or freeing 443.
- `-H 'Host: ...'` works for plain HTTP only. With `https://192.0.2.10/`, curl sends **no SNI at all** (an IP address is never sent as SNI, RFC 6066), so the proxy picks its default certificate and maybe a default router, and curl checks the certificate against the IP. That is why `--resolve` exists.
- `wrong version number` means you spoke TLS to a port that answered in plain HTTP. The opposite (HTTP to a TLS port) gets a 400 page saying "plain HTTP request was sent to HTTPS port" (Nginx) or "speaking plain HTTP to an SSL-enabled server port" (Apache).

**Why this step (now):** after Step 11 you know which layer fails for the full
path; this proves it by removing layers one at a time without changing any
config. It is the bypass ladder from Section 1 in practice, and the only safe
way to test a server while DNS is broken or still points at the old box.
Details: [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html).

**Next step:** works with `--resolve` but not without → §4.3 or §4.2. Works on the
server (variant 4) but not from outside → Steps 7–9. Fails even on the server →
Step 13.

### Step 13 — Read the proxy logs

**Goal:** get the proxy's own explanation for the error: which upstream it
tried, and what went wrong.

```bash
# --- Apache ---
sudo apache2ctl -S                                                     # which vhost serves which name, and its file
grep -RniE 'ErrorLog|CustomLog|ProxyPass |SSLCertificateFile' /etc/apache2/sites-enabled/
sudo tail -n 50 /var/log/apache2/error.log                             # plus each vhost's own ErrorLog
sudo tail -n 2000 /var/log/apache2/access.log | awk '{print $9}' | sort | uniq -c | sort -rn   # status histogram

# --- Nginx ---
sudo nginx -T 2>/dev/null | grep -nE 'server_name|listen|proxy_pass|fastcgi_pass|error_log|access_log'
sudo tail -n 50 /var/log/nginx/error.log

# --- Traefik (Dokploy) ---
docker ps --filter name=traefik --format '{{.Names}}\t{{.Status}}'
docker logs --since 15m dokploy-traefik 2>&1 | tail -n 50
sudo grep -nA3 -E '^(log|accessLog):' /etc/dokploy/traefik/traefik.yml   # log level, access log path
sudo ls -l /etc/dokploy/traefik/dynamic/                                  # per-app routers written by Dokploy
```

```
$ sudo tail -n 3 /var/log/apache2/error.log
[Sat Oct 03 10:40:12.551203 2026] [proxy:error] [pid 1342:tid 140233] (111)Connection refused: AH00957: HTTP: attempt to connect to 127.0.0.1:8000 (127.0.0.1:8000) failed
[Sat Oct 03 10:40:12.551260 2026] [proxy_http:error] [pid 1342:tid 140233] [client 192.0.2.50:53122] AH01114: HTTP: failed to make connection to backend: 127.0.0.1
[Sat Oct 03 10:40:12.551301 2026] [proxy:error] [pid 1342:tid 140233] AH00959: ap_proxy_connect_backend disabling worker for (127.0.0.1:8000) for 60s

$ sudo tail -n 1 /var/log/nginx/error.log
2026/10/03 10:40:12 [error] 2211#2211: *118 connect() failed (111: Connection refused) while connecting to upstream, client: 192.0.2.50, server: app.example.com, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:8000/", host: "app.example.com"

$ docker logs --since 15m dokploy-traefik 2>&1 | tail -n 1
2026-10-03T10:40:12Z DBG github.com/traefik/traefik/v3/pkg/proxy/httputil/proxy.go:121 > 502 Bad Gateway error="dial tcp 10.0.1.15:3000: connect: connection refused"
```

**What it means:**

- All three say the same thing in their own dialect: the proxy tried the upstream address (`127.0.0.1:8000`, `10.0.1.15:3000`) and got **connection refused**. The proxy is healthy; the app behind it is not listening there.
- The status code the client sees differs per proxy. Nginx and Traefik answer **502** for a refused connect. Apache answers **503 Service Unavailable** when it cannot even connect (`AH01114`), and keeps `502 Proxy Error` for a backend that accepted and then failed (`AH01102`). Traefik answers **504** when the dial itself times out (`dial tcp ...: i/o timeout`, after its 30 s `dialTimeout`).
- The errno in brackets is the key: `(111) Connection refused` = nothing listening; `(110) Connection timed out` / `i/o timeout` = upstream unreachable (wrong network, firewall); `(104) Connection reset by peer` or `prematurely closed` = the upstream accepted and then died; `(13) Permission denied` on a socket = file permissions, or SELinux on RHEL.
- Apache's `AH00959 ... disabling worker for 60s`: after one failed connect, Apache stops trying that backend for 60 seconds and answers **503** in the meantime, even once the app is back. Do not mistake that for "the fix didn't work" (§7.2).
- Traefik logs per-request errors at DEBUG level only. At the default ERROR level you may see nothing; enable the access log, which records status, router and backend URL for every request.
- `apache2ctl -S` and `nginx -T` show which vhost **actually** answers a name. With several vhosts on one IP, a missing `ServerName` / `server_name` sends traffic to the default (first) one.

**Why this step (now):** a proxy that returns 5xx always knows why, and writes
it down. Reading the log turns "502" into "refused on 127.0.0.1:8000", which
points straight at one process and one port. It is faster and more precise than
guessing from the outside, and it costs nothing.

**Next step:** refused / reset / timeout to the upstream → Step 14 and Step 15.
No log line at all for your request → the request never reached this proxy
(another proxy in front, wrong vhost, DNS pointing elsewhere: re-check Step 11's IP).
Specific errors → §7.1 (502), §7.2 (503), §7.3 (504), §8.1 (404).

### Step 14 — Check the app process and its logs

**Goal:** find out whether the application is running, crash-looping, or
running but failing.

```bash
# systemd-managed app server (gunicorn, node, php-fpm)
systemctl status gunicorn-app.service --no-pager -l
journalctl -u gunicorn-app.service --since '30 min ago' --no-pager | tail -n 50
systemctl status php8.3-fpm --no-pager            # Ubuntu 22.04: php8.1-fpm
sudo tail -n 50 /var/log/php8.3-fpm.log

# Plain Docker / Compose containers
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs --since 15m --tail 100 CONTAINER

# Dokploy applications run as Docker Swarm services
docker service ls
docker service ps APP_SERVICE --no-trunc
docker service logs --since 15m --tail 100 APP_SERVICE
```

```
$ docker service ps app-web-3k2j1 --no-trunc
ID          NAME                  IMAGE                                   NODE   DESIRED STATE  CURRENT STATE           ERROR
x3k1q8...   app-web-3k2j1.1       harbor.example.com/apps/web:4f2c9e1     web01  Running        Starting 4 seconds ago
p9q2w1...    \_ app-web-3k2j1.1   harbor.example.com/apps/web:4f2c9e1     web01  Shutdown       Failed 21 seconds ago   "task: non-zero exit (1)"
m7d4e2...    \_ app-web-3k2j1.1   harbor.example.com/apps/web:4f2c9e1     web01  Shutdown       Failed 48 seconds ago   "task: non-zero exit (1)"

$ docker service logs --tail 5 app-web-3k2j1
app-web-3k2j1.1.p9q2w1@web01 | [2026-10-03 10:39:51 +0000] [1] [INFO] Starting gunicorn 22.0.0
app-web-3k2j1.1.p9q2w1@web01 | django.core.exceptions.ImproperlyConfigured: Set the DATABASE_URL environment variable
app-web-3k2j1.1.p9q2w1@web01 | [2026-10-03 10:39:52 +0000] [1] [INFO] Shutting down: Master
```

**What it means:**

- The task history shows a restart loop: each task starts, exits with code 1, and Swarm starts a new one. While no task is up, Traefik has nothing to send traffic to (502 or 503).
- The log names the cause: a missing `DATABASE_URL`, so a configuration problem, not code or infrastructure. Typical after a redeploy that lost an environment variable.
- For systemd services, `activating (auto-restart)` in `systemctl status` is the same crash loop; `status=203/EXEC` means a bad `ExecStart` path ([Services](07-services-systemd.md)).
- Exit code 137 means SIGKILL, often the OOM killer (`docker inspect -f '{{.State.OOMKilled}}' CONTAINER`, `journalctl -k | grep -i 'killed process'`).

**Why this step (now):** the proxy says the upstream refuses or dies; the
only question left is why the app is not answering, and the app's own log is
the only thing that knows. Check status and logs **before** restarting:
a restart can make a crash loop look healthy for 30 seconds and wipes the
container's previous output.

**Next step:** crash loop with a clear error → fix the config, redeploy, verify.
Running but the proxy still fails → Step 15 (does the app answer locally, on the
port the proxy uses?). Errors about the database or Redis → Step 16. Container
specifics → [Containers & Kubernetes playbook](26-playbook-containers-k8s.md).

### Step 15 — Hit the app directly, bypassing the proxy

**Goal:** prove whether the app itself answers correctly on the address and
port the proxy is configured to use.

```bash
# App on the host's loopback (systemd-managed gunicorn / node)
curl -sv -m 10 http://127.0.0.1:8000/health

# App in a container with no published port: borrow the container's network namespace
docker run --rm --net container:CONTAINER nicolaka/netshoot curl -sv -m 10 http://127.0.0.1:8000/health

# Exactly what Traefik sees: Traefik's own namespace, the Swarm service name, the configured port
docker run --rm --net container:dokploy-traefik nicolaka/netshoot curl -sv -m 10 http://APP_SERVICE:3000/health

# What the app is really listening on, inside its namespace
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn

# php-fpm over its socket (package libfcgi-bin; needs ping.path = /ping in the pool file)
sudo env SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
  cgi-fcgi -bind -connect /run/php/php8.3-fpm.sock
```

```
$ docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511        127.0.0.1:8000       0.0.0.0:*

$ docker run --rm --net container:dokploy-traefik nicolaka/netshoot curl -sv -m 10 http://app-web-3k2j1:3000/health
*   Trying 10.0.1.14:3000...
* connect to 10.0.1.14 port 3000 from 10.0.1.4 port 43122 failed: Connection refused
curl: (7) Failed to connect to app-web-3k2j1 port 3000 after 1 ms: Couldn't connect to server
```

**What it means:**

- Inside the container the app listens on **8000** and only on **127.0.0.1**. Traefik is configured for port 3000 and connects from another container. Two bugs: the wrong port in the Dokploy domain settings, and a loopback bind inside the container (start the app with `--bind 0.0.0.0:8000` or `HOST=0.0.0.0`).
- The service name resolved (`10.0.1.14`), so both containers share `dokploy-network`. If the name did not resolve, or the connect timed out, the app would be on a different network than Traefik (§7.1).
- `curl 127.0.0.1:8000/health` returning 200 on the host while the proxy reports errors: the proxy points at the wrong address, port or socket. Compare its config line by line.
- The php-fpm ping prints `pong`; `Connection refused` or `No such file or directory` on the socket means php-fpm is down or the socket path in the vhost is wrong (version mismatch such as `php8.1-fpm.sock` after an upgrade to 8.3).

**Why this step (now):** it is the last bypass on the ladder. If the app answers
here, the bug is in the proxy's view of it (port, network, socket path, Host
header). If it fails here too, the proxy is innocent and you can stop reading
proxy configs. Borrowing the namespace (`--net container:`) tests from the
exact vantage point of the proxy or the app, without installing tools in
production images.

**Next step:** app answers locally but not via the proxy → fix the proxy target
(§7.1). App fails or hangs locally → Step 16 (often a dependency), then the app's
own logs. Health endpoint slow → §7.3.

### Step 16 — Check dependencies

**Goal:** check that the app can reach and use its database, cache and any
APIs it calls, from the app's own network position.

```bash
# From the app's network namespace (what the app sees, which may differ from the host)
docker run --rm --net container:CONTAINER nicolaka/netshoot nc -vz -w 3 db01.example.com 5432
docker run --rm --net container:CONTAINER nicolaka/netshoot nc -vz -w 3 redis01.example.com 6379

# Protocol-level checks from the host (client packages: postgresql-client, mysql-client, redis-tools)
pg_isready -h db01.example.com -p 5432
mysqladmin -h db01.example.com -u monitor -p ping
redis-cli -h redis01.example.com -p 6379 ping

# Dependency errors in the app's log
journalctl -u gunicorn-app.service --since '30 min ago' --no-pager \
  | grep -iE 'OperationalError|could not connect|too many|timeout|redis|refused' | tail -n 20
```

```
$ pg_isready -h db01.example.com -p 5432
db01.example.com:5432 - accepting connections

$ redis-cli -h redis01.example.com -p 6379 ping
PONG

$ journalctl -u gunicorn-app.service --since '30 min ago' --no-pager | grep -i OperationalError | tail -n 1
Oct 03 10:41:07 web01 gunicorn[1550]: psycopg2.OperationalError: connection to server at "db01.example.com" (192.0.2.30), port 5432 failed: FATAL:  sorry, too many clients already
```

**What it means:**

- `accepting connections` and `PONG`: the services are up and reachable **from this host**. That does not prove the app can use them: credentials, connection limits and the container's own DNS still matter.
- `sorry, too many clients already`: PostgreSQL hit `max_connections`. The app is fine, the database is fine, and together they fail. Usually a connection leak, too many workers each holding a pool, or a stuck batch job. Check `SELECT count(*), state FROM pg_stat_activity GROUP BY state;` on the database.
- `nc` from the container times out while the host connects fine: a container-specific path problem (Docker DNS, a firewall rule on the DB allowing only the host IP, or `dokploy-network` subnet overlapping a real subnet).

**Why this step (now):** you reach this step after the app itself is shown to be
running but failing. A down dependency makes a healthy app return 500, 502 or
504, and makes health checks that touch the DB fail, which pulls backends out
of the pool (503). Checking from the app's namespace prevents the classic false
negative: "the DB is reachable from my shell" while the container cannot reach it.

**Next step:** dependency down or saturated → that service's own runbook
(stabilise: kill the runaway job, raise limits temporarily, fail over). All
dependencies fine → the bug is in the app (recent deploy? → §9.2). Slow
dependency → [Slow system playbook](23-playbook-slow-system.md).

---

## 3. Status codes: which layer said it

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), area "HTTP", and [Web, HTTP & TLS](18-web-http-tls.md) (quick refresher) · 2) KodeKloud: *Nginx For Beginners*: Performance → Monitoring & Troubleshooting ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Performance/Monitoring-Troubleshooting/page)) · 3) Practice: fingerprint the responder with `curl -s -D -` on three of your own sites, one behind each proxy.

**Level:** [L1 · Junior].

A status code only tells you something once you know **who** generated it.
The same 502 means different things from Traefik, from Apache behind Traefik,
or from an app that proxies to another API.

### Fingerprint the responder

| Responder | Headers | Its own error pages look like | Where it logs |
|---|---|---|---|
| Traefik (Dokploy) | no `Server` header by default | short plain text: `Bad Gateway`, `404 page not found`, `no available server`, `Gateway Timeout` | `docker logs dokploy-traefik`, access log if enabled |
| Apache | `Server: Apache/2.4.58 (Ubuntu)` | HTML, titles like `502 Proxy Error`, `503 Service Unavailable` | `/var/log/apache2/error.log` + each vhost's `ErrorLog` |
| Nginx | `Server: nginx/1.24.0 (Ubuntu)` | HTML with a centred `nginx/1.24.0 (Ubuntu)` footer | `/var/log/nginx/error.log` |
| AWS ALB | `Server: awselb/2.0` | minimal HTML with `awselb/2.0` | ALB access logs (S3), target health |
| CDN in front | `server:` and request-id headers from the CDN, 52x codes | CDN-branded pages | CDN dashboard |
| The app | `X-Powered-By: PHP/8.3.6`, framework cookies, JSON bodies | app-styled pages, JSON `{"detail": ...}` | app log, `journalctl -u UNIT`, `docker logs` |

```bash
# Headers + first bytes of the body, to fingerprint the responder
curl -s -D - https://app.example.com/ | head -n 20
# Through each rung of the ladder: does the code change between layers?
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: app.example.com' http://192.0.2.10:8080/  # Apache behind Traefik
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/                             # the app
```

Read it from the bottom up: the guilty layer is the innermost one that still
fails. If the app returns 200 and Apache returns 502, the link between Apache
and the app is broken; if Apache returns 200 and the full path fails, look at
Traefik, TLS or the network in front of it.

### Status code meaning per layer

| Code | When a proxy generates it | When the app generates it | Go to |
|---|---|---|---|
| 400 | plain HTTP sent to the HTTPS port; request headers or cookies too large | validation error | Step 12 |
| 401 / 403 | auth middleware (Traefik `basicAuth`), IP allowlist, Apache `AH01630: client denied by server configuration` | app login / permissions | proxy config, app log |
| 404 | Traefik: **no router matched** the Host / path; Apache / Nginx: default vhost has no such path | the route does not exist in the app | §8.1 |
| 408 | client too slow to send the request (Apache `mod_reqtimeout`) | rare | client network |
| 413 | body larger than the proxy limit (`client_max_body_size`, `LimitRequestBody`) | framework upload limit | §8.3 |
| 421 | Misdirected Request: Apache when the SNI name and the Host header select vhosts with different TLS settings (`AH02032`) | — | Step 12 (`--resolve`, not `-H` with https) |
| 429 | rate-limit middleware | app throttling | proxy / app config |
| 499 | log only (Nginx, Traefik): **client** closed the connection before the answer | — | something upstream of you timed out first |
| 500 | rare from the proxy: broken `.htaccess`, `AH00124` rewrite loop | unhandled exception | app log |
| 502 | upstream refused, reset, closed early, or sent garbage | the app proxies to another API that failed | §7.1 |
| 503 | no healthy / available backend; Apache could not connect to the backend (`AH01114`, `AH01079`) or the worker is in its retry window; php-fpm full; Nginx `limit_req` (default reject code) | maintenance mode, health failing | §7.2 (connect refused: §7.1) |
| 504 | upstream did not answer within the proxy timeout (Nginx, Traefik, ALB); Traefik also when the **dial** times out (backend unreachable). Apache's mod_proxy_http answers a backend read timeout with 502 instead | — | §7.3 |

### Time-to-failure fingerprints

When requests always die after the **same** number of seconds, the number
tells you which component's timeout fired:

| Dies after | Status / error | Usually |
|---|---|---|
| ~5 s or ~10 s pause, then works | slow, not failing | first DNS server dead, resolver retries the next one (§4.4) |
| ~30 s | 502 (Nginx `upstream prematurely closed`, Apache `AH01102`, Traefik `EOF`) | gunicorn kills the worker: default `--timeout 30` (§7.3) |
| ~30 s | 500 with `Maximum execution time of 30 seconds exceeded` | PHP `max_execution_time` |
| ~30 s | 504 from Traefik, its log says `dial tcp IP:PORT: i/o timeout` | Traefik's `forwardingTimeouts.dialTimeout` (30 s): the backend is unreachable, not slow (§7.1 Step 3) |
| 60 s | 504 | Nginx `proxy_read_timeout` 60 s; AWS ALB idle timeout 60 s |
| 60 s, uploads only | connection closed | Traefik v3 entrypoint `respondingTimeouts.readTimeout` (60 s default) |
| 100 s | 524 | a CDN's origin timeout |
| 300 s | 502 `Proxy Error` with `AH01102` and `(70007)The timeout specified has expired` | Apache on Ubuntu: `Timeout 300` in `apache2.conf`, inherited by `ProxyTimeout`. Apache's mod_proxy_http reports a backend read timeout as 502, not 504 |
| ~130 s | `curl: (28)` on connect | the kernel gave up retrying the SYN (`net.ipv4.tcp_syn_retries = 6`): nothing answers at all |

---

## 4. DNS scenarios

> 📚 **Study path:** 1) KodeKloud: *Demystifying DNS*: DNS as a System (resolvers, walking the tree, TTL), then Miscellaneous → Troubleshooting DNS ([course](https://kodekloud.com/courses/demystifying-dns)) · 2) Note: [DNS](08-dns.md) and [Learn: networking](28-learn-networking.md), area "DNS in depth" · 3) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* ([YouTube](https://www.youtube.com/watch?v=9nCIjLlLVzY)) · 4) Practice: the ops ladder drill "break DNS three ways" (Section 12 #1 and #2, plus systemd-resolved stopped).

Each scenario repeats only the commands that matter for it. For the general
tools, see Steps 1–3 above and [DNS](08-dns.md).

### 4.1 curl (6) Could not resolve host

> 📚 **Study path:** 1) Note: [DNS](08-dns.md) (quick refresher) · 2) KodeKloud: *DevOps Pre-Requisite Course*: Networking Basics → DNS, then Labs – DNS ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/DNS/page)) · 3) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* ([YouTube](https://www.youtube.com/watch?v=9nCIjLlLVzY)) · 4) Practice: Section 12 #1 (dead resolver) on the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)).

**Level:** [L1 · Junior].

**Symptom:** `curl: (6) Could not resolve host: app.example.com` on a server,
CI runner or cron job, often right after a netplan change, a VPN change or a
fresh install. No TCP connection is ever attempted.

**Step 1 — Resolve the way curl does**

**Goal:** confirm the failure is on the glibc path and learn what kind of failure it is.

```bash
getent ahosts app.example.com; echo "exit=$?"
resolvectl query app.example.com
env | grep -i _proxy          # curl (5) "Could not resolve proxy" is a different problem
```

```
exit=2
app.example.com: resolve call failed: No appropriate name servers or networks for name found
```

**What it means:** `exit=2` means no source in `/etc/nsswitch.conf` could
resolve the name. The resolvectl message classifies the failure:

- `No appropriate name servers or networks for name found` = no DNS server is configured on any link → Step 2.
- `All attempts to contact name servers or networks failed` = servers configured, none answered → Step 3.
- `'app.example.com' not found` = a server answered NXDOMAIN → Step 4.

**Why this step (now):** the three resolvectl messages correspond to three
different fixes (config, network, zone data). Spending ten seconds here stops
you from editing a DNS zone when the server simply has no resolver configured.

**Next step:** as listed above.

**Step 2 — Check the resolver configuration**

**Goal:** find out why this host has no usable DNS server.

```bash
ls -l /etc/resolv.conf
resolvectl status
sudo cat /etc/netplan/*.yaml
```

```
Link 2 (ens18)
    Current Scopes: none
         Protocols: -DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported

network:
  version: 2
  ethernets:
    ens18:
      addresses: [192.0.2.21/24]
      routes:
        - to: default
          via: 192.0.2.1
```

**What it means:** `Current Scopes: none` = systemd-resolved has no DNS server
for this link. The netplan file has a static address but no `nameservers:`
block. That typically happens when someone switches from DHCP (which supplied
DNS servers) to a static address. If `/etc/resolv.conf` is a regular file
rather than the stub symlink, something overwrote it; look for the culprit
(an old script, cloud-init, a VPN client).

**Why this step (now):** Step 1 said there is no server to ask, so the
question is configuration, not the network. Netplan is where the server list
should come from on Ubuntu.

**Next step:** missing `nameservers:` → Fix & verify below. Servers configured
but silent → Step 3.

**Step 3 — Prove where the queries die**

**Goal:** get evidence that the configured resolvers do not answer, and which protocol fails.

```bash
sudo tcpdump -ni any port 53 &            # or in a second terminal
dig @192.0.2.53 app.example.com +time=2 +tries=1
dig @192.0.2.54 app.example.com +time=2 +tries=1
dig @192.0.2.53 app.example.com +tcp +time=2 +tries=1    # TCP 53 too: some firewalls only allow UDP
nc -vz -w 2 192.0.2.53 53
```

```
;; communications error to 192.0.2.53#53: timed out
;; communications error to 192.0.2.54#53: timed out
;; communications error to 192.0.2.53#53: timed out
nc: connect to 192.0.2.53 port 53 (tcp) timed out: Operation now in progress
```

**What it means:** both resolvers time out over UDP and TCP, and the capture
shows queries leaving with no replies. Either the resolvers are down, or
something in between drops port 53 from this host. Run the same `dig` from a
host in another subnet: if it works there, the problem is the path from this
subnet (firewall rule, ACL on the DNS server allowing only known subnets).

**Why this step (now):** "DNS is down" and "this host may not reach DNS" have
different owners. The capture plus a comparison from a second host tells you
which team to call, with evidence.

**Next step:** one resolver works → remove or deprioritise the dead one, and
report it. None work from anywhere → DNS service outage: escalate, and in the
meantime use `curl --resolve` for checks. Only this subnet fails → firewall or
ACL (Steps 8–9).

**Step 4 — NXDOMAIN: check the record and search domains**

**Goal:** find out whether the record is really missing, missing only
internally, or the name was typed short.

```bash
dig app.example.com | grep -E 'status:|SERVER:'
dig +short NS example.com
dig @ns1.example.net app.example.com +norecurse +noall +answer   # the authority's view
resolvectl domain                                                # search domains per link
```

```
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 18822
;; SERVER: 127.0.0.53#53(127.0.0.53) (UDP)
ns1.example.net.
ns2.example.net.
app.example.com.	3600	IN	A	192.0.2.10
Link 2 (ens18): corp.example.com
```

**What it means:** the authoritative server has the record, but the internal
resolver says NXDOMAIN. That is **split-horizon DNS**: the internal DNS (often
Active Directory DNS) hosts its own copy of `example.com`, which lacks the new
record. If the authority also said NXDOMAIN, the record really does not exist
(typo, wrong zone, never created). If only a short name like `app` fails, the
search domain is missing or wrong (§4.2 Step 4).

**Why this step (now):** NXDOMAIN is an answer, not a failure to answer. The
question becomes "which copy of the zone is wrong", and asking the authority
with `+norecurse` answers it without any cache in between.

**Next step:** add the record to the zone copy that lacks it. Old IP instead
of NXDOMAIN → §4.3.

**Decision tree**

```
curl: (6) Could not resolve host
├── env has http(s)_proxy? ── yes → curl (5)/(6) via proxy: test with --noproxy '*'
├── getent ahosts NAME works? ── yes → curl uses something else (proxy, container, app cache) → §4.2
└── resolvectl query NAME says...
    ├── "No appropriate name servers"  → no DNS on any link → fix netplan nameservers
    ├── "All attempts ... failed"     → tcpdump port 53 + dig @each server
    │       ├── fails only from this subnet → firewall/ACL to resolvers
    │       └── fails everywhere           → resolver outage → escalate, use --resolve meanwhile
    └── "not found" (NXDOMAIN)        → dig @authority +norecurse
            ├── authority has it  → internal split-horizon zone missing record
            └── authority lacks it → create/fix the record (typo? wrong zone?)
```

**Fix & verify**

Add the resolvers to netplan, then apply with the automatic rollback timer:

```bash
sudo cp /etc/netplan/50-cloud-init.yaml /root/50-cloud-init.yaml.bak   # your file name may differ
sudoedit /etc/netplan/50-cloud-init.yaml
```

```
network:
  version: 2
  ethernets:
    ens18:
      addresses: [192.0.2.21/24]
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53, 192.0.2.54]
        search: [corp.example.com]
```

```bash
sudo netplan try                      # applies, reverts after 120 s unless you press Enter
resolvectl status ens18               # DNS Servers: 192.0.2.53 192.0.2.54
getent ahosts app.example.com         # expected IP
curl -sS -o /dev/null -w '%{http_code}\n' https://app.example.com/
```

**Rollback**

`netplan try` reverts on its own if you lose access. To undo afterwards:
`sudo cp /root/50-cloud-init.yaml.bak /etc/netplan/50-cloud-init.yaml && sudo netplan apply`.

**Prevent it next time**

- Manage netplan files with configuration management, including `nameservers:`. Never rely on DHCP options you are about to remove.
- Monitor resolution from each server (a blackbox DNS probe, or a cron `getent` check that alerts).
- Keep at least two resolvers, in different failure domains.
- On Docker hosts, set `"dns": ["192.0.2.53", "192.0.2.54"]` in `/etc/docker/daemon.json` so containers do not fall back to public resolvers that the firewall blocks (see [Containers playbook](26-playbook-containers-k8s.md)).

### 4.2 dig resolves, curl does not

> 📚 **Study path:** 1) Note: Step 1 above and [DNS](08-dns.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs*: Networking → DNS ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)) · 3) Read: [Some things about getaddrinfo that surprised me](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/) (KodeKloud has no getent-vs-dig lesson) · 4) Practice: Section 12 #2 (stale `/etc/hosts` line), then the same with a `.local` name.

**Level:** [L2 · Mid].

**Symptom:** `dig +short app.example.com` returns the right IP, but curl or the
application cannot resolve the name, or connects to a **different** IP.

**Step 1 — Put the two answers side by side**

**Goal:** confirm the disagreement and see the two answers.

```bash
dig +short app.example.com
getent ahosts app.example.com | head -n 1
```

```
192.0.2.10
192.0.2.99      STREAM app.example.com
```

**What it means:** DNS says 192.0.2.10, the application path says 192.0.2.99.
Some source listed **before** `dns` in nsswitch is answering. In a "cannot
resolve" variant, `getent` would print nothing while `dig` succeeds: a source
returned "not found" and nsswitch stopped before asking DNS.

**Why this step (now):** it proves the disagreement is real and on this host,
so you stop looking at DNS servers and start looking at local configuration.

**Next step:** Step 2.

**Step 2 — Ask each nsswitch source separately**

**Goal:** find which source produced the wrong answer.

```bash
grep -E '^hosts:' /etc/nsswitch.conf
getent -s files hosts app.example.com        # /etc/hosts only
getent -s dns hosts app.example.com          # DNS only, as glibc does it
grep -n 'app.example.com' /etc/hosts
```

```
hosts:          files mdns4_minimal [NOTFOUND=return] dns
192.0.2.99      app.example.com
192.0.2.10      app.example.com
14:192.0.2.99   app.example.com   # temp test before migration
```

**What it means:** line 14 of `/etc/hosts` pins the name to the old server.
`files` comes first in the `hosts:` line, so DNS is never asked. The comment
shows it was a temporary test that nobody removed. Classic after a migration.

**Why this step (now):** `getent -s` queries one nsswitch source at a time,
the most direct way to see which source answers. Opening `/etc/hosts`
alone would miss the other sources (mdns, myhostname, libvirt, nss plugins).

**Next step:** a stale hosts line → Fix & verify. `.local` names failing → Step 3.
Short names failing → Step 4.

**Step 3 — Names ending in .local**

**Goal:** check whether mDNS is intercepting your internal domain.

```bash
getent ahosts db01.corp.local; echo "exit=$?"
getent -s dns hosts db01.corp.local
```

```
exit=2
192.0.2.30      db01.corp.local
```

**What it means:** `mdns4_minimal [NOTFOUND=return]` hands every `.local`
name to multicast DNS (Avahi). When mDNS finds nothing, `[NOTFOUND=return]`
stops the lookup **before** `dns` is tried. `dig` asks DNS directly and works;
every application fails. Common on desktop-derived images joined to an Active
Directory domain named `corp.local`.

**Why this step (now):** it is the most common "dig works, nothing else
does" trap on Ubuntu, and the `hosts:` line from Step 2 already showed the
suspect.

**Next step:** fix by removing `mdns4_minimal [NOTFOUND=return]` from the
`hosts:` line on servers (they do not need mDNS), or by moving `dns` before it.

**Step 4 — Short names and search domains**

**Goal:** check whether the app uses a short name that only works with a search domain.

```bash
dig +short app                       # dig does NOT apply search domains by default
dig +short +search app               # now it does
resolvectl domain
grep -E '^(search|options)' /etc/resolv.conf
```

```
(empty)
192.0.2.10
Link 2 (ens18): corp.example.com
search corp.example.com
```

**What it means:** `app` resolves only as `app.corp.example.com`, through the
search list. A host or container without that search domain (a new server, a
Docker container, a Kubernetes pod with its own search list and `ndots:5`)
fails. In Kubernetes, `ndots:5` makes external names try every search domain
first, which multiplies queries and slows them down.

**Why this step (now):** short names hide a dependency on per-host
configuration. Proving it with `dig +search` explains why the same config file
works on one host and not on another.

**Next step:** use FQDNs in application config. If you need the short name,
set the search domain in netplan (`nameservers.search`) or the container's
`dns_search`.

**Decision tree**

```
dig OK, app/curl not OK
├── getent ahosts NAME = wrong IP
│     └── getent -s files hosts NAME → match? → stale /etc/hosts line
├── getent ahosts NAME = empty
│     ├── name ends in .local and hosts: has mdns4_minimal [NOTFOUND=return] → mDNS swallow
│     ├── short name? dig +search NAME works → search domain missing on this host/container
│     └── hosts: line lacks dns / has odd module → fix nsswitch.conf
└── getent OK but the APP is wrong
      ├── app runs in a container → its own /etc/resolv.conf (Containers playbook)
      ├── http_proxy set → the proxy resolves, not you
      └── app caches DNS (JVM, Nginx proxy_pass hostname resolved at start) → restart/reload it
```

**Fix & verify**

```bash
sudo cp /etc/hosts /etc/hosts.bak.$(date +%F)
sudo sed -i '/^192\.0\.2\.99[[:space:]]\+app\.example\.com/s/^/# removed during incident: /' /etc/hosts
getent ahosts app.example.com | head -n 1      # now 192.0.2.10
curl -sS -o /dev/null -w '%{remote_ip} %{http_code}\n' https://app.example.com/
```

Commenting the line out, not deleting it, keeps a record of what was there.

**Rollback**

`sudo cp /etc/hosts.bak.YYYY-MM-DD /etc/hosts` (the file you saved).

**Prevent it next time**

- Treat `/etc/hosts` entries for production names as temporary. Add a dated comment and a ticket, and remove them when the test ends.
- Do not name internal domains `.local`. If you inherit one, fix nsswitch on servers through configuration management.
- Use fully qualified names in all application configs and connection strings.

### 4.3 Changed a DNS record, still old IP

> 📚 **Study path:** 1) KodeKloud: *Demystifying DNS*: DNS as a System → Time to Live (TTL) ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/DNS-as-a-System/Time-to-Live-TTL/page)) · 2) Note: [Learn: networking](28-learn-networking.md), area "DNS in depth" · 3) Practice: the negative-caching experiment on [Mess With DNS](https://messwithdns.net/) · 4) Apply: plan your next DNS cutover with [Deployment patterns](35-deployment-patterns.md).

**Level:** [L2 · Mid].

**Symptom:** you moved `app.example.com` from 192.0.2.99 (old Apache server)
to 192.0.2.10 (new Dokploy server). Some clients reach the new server, others
still hit the old one, and your own laptop keeps getting the old IP.

**Step 1 — Compare the cache with the authority**

**Goal:** find out whether the authoritative data is correct and how long caches will keep the old answer.

```bash
dig +noall +answer app.example.com                                   # via your resolver (cached)
sleep 5; dig +noall +answer app.example.com                           # TTL should count down
dig +short NS example.com
dig @ns1.example.net app.example.com +norecurse +noall +answer        # the source of truth
dig @ns1.example.net example.com SOA +noall +answer                   # serial: did the change publish?
```

```
app.example.com.	2873	IN	A	192.0.2.99
app.example.com.	2868	IN	A	192.0.2.99
ns1.example.net.
ns2.example.net.
app.example.com.	3600	IN	A	192.0.2.10
example.com.	3600	IN	SOA	ns1.example.net. hostmaster.example.com. 2026100302 7200 3600 1209600 3600
```

**What it means:** the authority already serves the new IP. Your resolver
holds the old answer with a TTL counting down from 3600: it expires in about
48 minutes (2868 s). Nothing is broken; you are waiting for caches. If the
authority still showed the old IP, the change was not published (wrong zone,
serial not incremented on a BIND primary, change made in the wrong DNS
provider account).

**Why this step (now):** it separates the two possible problems, "the change
never happened" and "the change happened but caches remember", in one
comparison. Only the first one is yours to fix in the zone.

**Next step:** authority correct → Step 2 (find every cache). Authority wrong → fix the zone and recheck.

**Step 2 — Find every cache between the client and the authority**

**Goal:** list the caches, from closest to the client to furthest away, and decide which you can flush.

```bash
resolvectl query app.example.com          # "-- Data from: cache" means systemd-resolved cached it
dig @192.0.2.53 app.example.com +noall +answer      # each internal resolver separately
dig @192.0.2.54 app.example.com +noall +answer
```

```
app.example.com: 192.0.2.99                    -- link: ens18
-- Data from: cache
app.example.com.	2850	IN	A	192.0.2.99
app.example.com.	3600	IN	A	192.0.2.10
```

**What it means:** the caches in order, from the client outwards:

| Cache | How to flush |
|---|---|
| browser | Chrome: `chrome://net-internals/#dns` → Clear host cache; or restart the browser |
| application | JVM caches lookups (`networkaddress.cache.ttl`); Nginx resolves a `proxy_pass` hostname **once at start**: reload or restart the app/proxy |
| OS stub | Linux `sudo resolvectl flush-caches`; Windows `ipconfig /flushdns`; macOS `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` |
| internal resolvers | BIND `sudo rndc flushname app.example.com`; Unbound `sudo unbound-control flush app.example.com`; Windows DNS `Clear-DnsServerCache` |
| ISP / public resolvers | you cannot flush them; wait for the TTL |

Here 192.0.2.53 still caches the old answer and 192.0.2.54 already has the new
one, which explains why clients disagree.

The `-- Data from:` line is printed by newer systemd (Ubuntu 24.04). Older
releases such as 22.04's systemd 249 may show only the `-- Information acquired
via protocol DNS in ...` timing line; there, compare with
`resolvectl query --cache=no app.example.com`, which skips the local cache.

**Why this step (now):** "still old IP" is always a cache somewhere. Walking the
caches in order shows which ones you control, which ones you only need to
wait for, and gives you an honest ETA for everyone else.

**Next step:** flush what you control, then Step 3 if a name that did not exist before is still "not found".

**Step 3 — Negative caching for brand-new names**

**Goal:** explain why a **new** record still returns NXDOMAIN after you created it.

```bash
dig @ns1.example.net example.com SOA +noall +answer     # the last field is the negative-cache TTL
```

```
example.com.	3600	IN	SOA	ns1.example.net. hostmaster.example.com. 2026100302 7200 3600 1209600 3600
```

**What it means:** if anyone looked up `new.example.com` **before** you created
it, resolvers cached the NXDOMAIN answer for up to the SOA's last field
(3600 s here, bounded by the SOA record's own TTL). Testing a name before
the record exists, a monitoring probe, or a typo in a browser is enough to
trigger it.

**Why this step (now):** it explains the most confusing variant, "the record
exists at the authority, yet my resolver insists it does not", and why
flushing the resolver fixes it while waiting a few minutes does not.

**Next step:** flush the resolvers you control (table above), or wait out the negative TTL.

**Decision tree**

```
DNS change not visible
├── dig @authority +norecurse shows OLD/none → change not published → fix zone (serial, right provider)
└── authority shows NEW
    ├── your resolver shows OLD with TTL counting down → cache: flush or wait TTL
    ├── one internal resolver OLD, other NEW → flush that resolver
    ├── NXDOMAIN for a new name → negative cache (SOA minimum) → flush / wait
    ├── dig NEW but app still hits OLD → app-level cache (Nginx/JVM) → reload app
    └── browser only → browser cache / HSTS / cached 301 → clear, test with curl
```

**Fix & verify**

```bash
sudo resolvectl flush-caches
resolvectl query app.example.com           # "Data from: network", new IP
curl -sS -o /dev/null -w '%{remote_ip} %{http_code}\n' https://app.example.com/
```

While caches expire, keep the **old** server useful: make Apache on 192.0.2.99
proxy `app.example.com` to the new server, so stale clients still get the right
content instead of an outage.

**Rollback**

Reverting a DNS change is also subject to TTL. The rollback you have is the
old server staying up (and proxying) until the TTL window has passed.

**Prevent it next time**

- Lower the record's TTL (to 300 s) at least one old-TTL period **before** the change; raise it again afterwards.
- Verify every change at the authority with `dig @NS +norecurse`, and note the SOA serial.
- Do not look up names before they exist. If you did, flush.
- Keep the old server running and proxying for at least the old TTL after a migration.

### 4.4 Debugging the resolver itself

> 📚 **Study path:** 1) KodeKloud: *Demystifying DNS*: Miscellaneous → Troubleshooting DNS ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page)) · 2) Read: [Arch Wiki: systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved) (KodeKloud does not cover resolved's debug log) · 3) Note: [DNS](08-dns.md) · 4) Practice: Section 12 #1 with `resolvectl log-level debug` on, then read the log line by line.

**Level:** [L2 · Mid].

**Symptom:** lookups are slow (5–10 s pauses), fail intermittently, or fail
only for some domains, and `dig @UPSTREAM` works fine. The problem is inside
systemd-resolved: which server it picked, which link, which feature level.

**Step 1 — Turn on debug logging and reproduce**

**Goal:** see every decision systemd-resolved makes for one failing lookup.

```bash
sudo resolvectl log-level debug
journalctl -fu systemd-resolved                  # terminal 1: follow the resolver
resolvectl query app.example.com                 # terminal 2: reproduce
```

```
Oct 03 10:20:01 web01 systemd-resolved[612]: Looking up RR for app.example.com IN A.
Oct 03 10:20:01 web01 systemd-resolved[612]: Switching to DNS server 192.0.2.53 for interface ens18.
Oct 03 10:20:01 web01 systemd-resolved[612]: Transaction 41234 for <app.example.com IN A> scope dns on ens18/*.
Oct 03 10:20:01 web01 systemd-resolved[612]: Using feature level UDP+EDNS0 for transaction 41234.
Oct 03 10:20:01 web01 systemd-resolved[612]: Sending query packet with id 41234 on interface 2/AF_INET of size 44.
Oct 03 10:20:06 web01 systemd-resolved[612]: Timeout reached on transaction 41234.
Oct 03 10:20:06 web01 systemd-resolved[612]: Retrying transaction 41234, after switching servers.
Oct 03 10:20:06 web01 systemd-resolved[612]: Switching to DNS server 192.0.2.54 for interface ens18.
Oct 03 10:20:06 web01 systemd-resolved[612]: Using degraded feature set UDP instead of UDP+EDNS0 for DNS server 192.0.2.54.
Oct 03 10:20:06 web01 systemd-resolved[612]: Processing incoming packet of size 60 on transaction 41234 (rcode=SUCCESS).
Oct 03 10:20:06 web01 systemd-resolved[612]: Transaction 41234 for <app.example.com IN A> scope dns on ens18/* now complete with <success> from network (unsigned; non-confidential).
```

**What it means:** line by line:

- `Switching to DNS server 192.0.2.53`: the first server tried.
- `Timeout reached` after 5 s: 192.0.2.53 did not answer. **This is your 5-second pause.**
- `Switching to DNS server 192.0.2.54` then `rcode=SUCCESS`: the second server answered.
- `Using degraded feature set UDP instead of UDP+EDNS0`: a device on the path (often an old firewall doing DNS inspection) breaks EDNS0, so resolved falls back. It works, but more slowly; worth reporting.
- Other lines to look for: `DNSSEC validation failed` (upstream or zone broken for DNSSEC), and queries sent on the **wrong link** (a VPN interface winning because it has `~.` as a routing domain).

**Why this step (now):** systemd-resolved hides a lot of logic: per-link
servers, server switching, feature-level fallbacks, routing domains. `dig`
bypasses all of it, which is why `dig` works while apps stall. The debug log
is the only place where those decisions are written down.

**Next step:** Step 2 to read the per-link picture, then turn logging off (Step 3).

**Step 2 — Read per-link servers, routing domains and counters**

**Goal:** check which link should answer which domain, and how often lookups fail.

```bash
resolvectl status
resolvectl domain
resolvectl statistics
resolvectl monitor          # Ubuntu 24.04 (systemd 255): live view of every lookup and its answer
```

```
Link 3 (tun0)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
       DNS Servers: 10.8.0.1
        DNS Domain: ~.

Transactions
Current Transactions: 0
  Total Transactions: 18233
Cache
  Current Cache Size: 211
          Cache Hits: 9921
        Cache Misses: 8312
Failure Transactions
      Total Timeouts: 412
```

**What it means:** the VPN link `tun0` claims `~.`, the routing domain for
**every** name, with `+DefaultRoute`. All lookups, including internal
`corp.example.com` names, go to the VPN's DNS, which does not know them.
`Total Timeouts: 412` confirms a recurring failure, not a one-off.

**Why this step (now):** the debug log showed which server was used. This
shows **why** that server was chosen, which is what you need to change.

**Next step:** fix the link configuration (Fix & verify), then Step 3.

**Step 3 — Turn debug logging off again**

**Goal:** restore normal logging so the journal does not fill up.

```bash
sudo resolvectl log-level info
```

**What it means:** no output. Debug logging is very verbose and can fill a small `/var/log/journal`.

**Why this step (now):** you have the evidence. Leaving debug on is a slow-burning incident of its own.

**Next step:** apply the fix.

**Decision tree**

```
resolver slow / flaky, dig @upstream fine
├── 5 s pauses → first server dead → debug log shows "Timeout reached" → fix server order/remove it
├── "degraded feature set" → middlebox breaks EDNS0 → report; works but slower
├── "DNSSEC validation failed" → upstream/zone DNSSEC broken → fix upstream, or DNSSEC=no drop-in (deliberate)
├── wrong link answers (VPN ~.) → per-link domains → route ~corp.example.com to the right link
└── /etc/resolv.conf not the stub symlink → something overwrote it → restore symlink
```

**Fix & verify**

```bash
# Send internal names to the LAN resolvers at runtime (until reboot / reconnect):
sudo resolvectl dns ens18 192.0.2.53 192.0.2.54
sudo resolvectl domain ens18 '~corp.example.com' corp.example.com
# Restore the stub symlink if something replaced resolv.conf:
sudo ln -sf ../run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
resolvectl query db01.corp.example.com        # answered via ens18
```

Make it permanent in netplan (`nameservers:` and `search:`) or in the VPN
client's settings. Runtime `resolvectl` changes do not survive a reboot.

**Rollback**

`sudo resolvectl revert ens18` drops the runtime per-link settings. Restore
`/etc/resolv.conf` from your backup if you replaced it.

**Prevent it next time**

- Keep `/etc/resolv.conf` as the stub symlink; configure servers in netplan only.
- Order resolvers by health, and monitor each one directly (`dig @each`).
- For VPNs, use split DNS (`~corp.example.com`) rather than `~.` when the VPN DNS cannot resolve everything.
- Reference: [Arch Wiki: systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved).

---

## 5. Connection scenarios

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), areas "Transport" and "Firewalls and connection tracking" · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Configure Packet Filtering (Firewall) and Port Redirection and NAT ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 3) Read: [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) (KodeKloud does not cover the UFW bypass) · 4) Practice: Section 12 #3, #4 and #5.

### 5.1 Connection refused

> 📚 **Study path:** 1) Note: [Ports inventory](22-playbook-ports-inventory.md) (quick refresher) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Start, Stop, and Check Status of Network Services ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) Video: *Linux for Beginners: systemd start/stop services & journalctl* ([YouTube](https://www.youtube.com/watch?v=jZfNVROoF74)) · 4) Practice: Section 12 #4 (stopped Nginx), watch the RST in tcpdump.

**Level:** [L1 · Junior].

**Symptom:** `curl: (7) Failed to connect to app.example.com port 443 after 2 ms:
Couldn't connect to server` (curl 7.x says `Connection refused`), or
`nc ... failed: Connection refused`. It fails **fast**, in milliseconds.

**Step 1 — Confirm the exact IP and port being refused**

**Goal:** make sure you are debugging the right host.

```bash
curl -v --connect-timeout 5 https://app.example.com/ 2>&1 | grep -E 'Trying|connect to|Failed'
```

```
*   Trying 192.0.2.99:443...
* connect to 192.0.2.99 port 443 from 192.0.2.50 port 51234 failed: Connection refused
* Failed to connect to app.example.com port 443 after 2 ms: Couldn't connect to server
```

**What it means:** curl went to 192.0.2.99, the **old** Apache server that you
already stopped, not to the new server 192.0.2.10. The refusal is real, but the
problem is DNS or a cache (§4.3). If the IP is the expected one, go on.

**Why this step (now):** a refusal proves a host answered, but not that it was
the right one. One grep of `curl -v` prevents an hour on the wrong box.

**Next step:** wrong IP → §4.2 / §4.3. Right IP → Step 2 on that server.

**Step 2 — See what listens on the server**

**Goal:** find out whether anything listens on that port, on which address.

```bash
sudo ss -ltnp 'sport = :443'
sudo ss -ltnp | grep -E 'apache2|nginx|docker-proxy|traefik'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
(no lines for :443)
LISTEN 0      511          0.0.0.0:80        0.0.0.0:*     users:(("apache2",pid=1342,fd=4))
```

**What it means:** Apache listens on 80 only. Nothing listens on 443: the SSL
module or the 443 vhost is not enabled, `Listen 443` is missing from
`ports.conf`, or the service that should own 443 (Traefik) is not running.
Other common answers: the service listens on `127.0.0.1:443` (§5.3), on `[::]`
only with IPv6-only binding, or on a different port than the client uses.

**Why this step (now):** "refused" means the kernel found no listening socket
for that IP and port. `ss` lists the sockets, so it confirms or kills that
explanation directly.

**Next step:** nothing listens → Step 4. Listener exists and still refused → Step 3.

**Step 3 — Find out who sends the RST**

**Goal:** check whether the server itself refuses, or something in the middle does.

```bash
sudo tcpdump -ni any 'tcp port 443 and host 192.0.2.50 and (tcp[tcpflags] & (tcp-syn|tcp-rst) != 0)'
sudo nft list ruleset | grep -n -i reject
```

```
10:52:10.101120 ens18 In  IP 192.0.2.50.51234 > 192.0.2.10.443: Flags [S], seq 77120931, win 64240, length 0
10:52:10.101161 ens18 Out IP 192.0.2.10.443 > 192.0.2.50.51234: Flags [R.], seq 0, ack 77120932, win 0, length 0
```

**What it means:** the server's kernel answered the SYN with RST. Either no
socket matched (Step 2) or a local `reject with tcp reset` rule matched (the
nft grep shows it). If the capture shows **no SYN** while the client gets
refused, the RST comes from a device in between (a firewall configured to
reject, a load balancer with no listener) or from another host with the same IP.

**Why this step (now):** the listener looks right but the client is refused,
so the RST must be generated somewhere other than where you expect. A
capture is the only way to see who sends it.

**Next step:** the local kernel sends RST with a correct listener → firewall
REJECT rule (Step 8). No SYN arrives → the device in between (Step 9).

**Step 4 — Find out why the service is not listening**

**Goal:** get the reason from the service manager and the service's own log.

```bash
systemctl status apache2 --no-pager -l
sudo apache2ctl -M 2>/dev/null | grep -i ssl          # is mod_ssl loaded?
ls -l /etc/apache2/sites-enabled/
grep -n Listen /etc/apache2/ports.conf
docker ps -a --filter name=traefik --format '{{.Names}}\t{{.Status}}'
```

```
● apache2.service - The Apache HTTP Server
     Active: active (running) since Sat 2026-10-03 09:12:44 UTC; 1h 39min ago
lrwxrwxrwx 1 root root 27 Oct  3 09:10 app.conf -> ../sites-available/app.conf
5:Listen 80
dokploy-traefik	Exited (1) 12 minutes ago
```

**What it means:** Apache is running but has no SSL module or 443 vhost (no
`ssl` output, no `-ssl.conf` site), because 443 was deliberately handed to
Traefik. Traefik, the new owner of 443, has **exited**. The refusal is
Traefik's absence. Read `docker logs dokploy-traefik` for why (for example a
broken dynamic config file, or 443 grabbed by Apache again at boot, see §9.1).

**Why this step (now):** you know nothing listens; the service manager and
container runtime know **why**, and their logs record the last error.

**Next step:** start or fix the owning service, then verify. Port clash at
start → §9.1.

**Decision tree**

```
Connection refused (fast failure)
├── curl -v shows an unexpected IP → DNS/cache problem → §4.2 / §4.3
└── right IP → on server: ss -ltnp 'sport = :PORT'
    ├── nothing listening
    │     ├── service stopped/crashed → systemctl status / docker ps -a → logs → fix, start
    │     └── service up, wrong port/vhost → config (Listen, ports:, Dokploy domain port)
    ├── listening on 127.0.0.1 only → §5.3
    └── listening on 0.0.0.0 / * and still refused
          ├── tcpdump: SYN in, RST out → local REJECT rule → ufw/nft
          └── tcpdump: no SYN → RST from a device in between / IP conflict
```

**Fix & verify**

```bash
docker logs --tail 30 dokploy-traefik          # read the reason first
docker start dokploy-traefik                   # after fixing the cause
sudo ss -ltnp 'sport = :443'                   # docker-proxy listening again
curl -sS -o /dev/null -w '%{http_code}\n' https://app.example.com/
```

**Rollback**

If the fix was a config change (a Traefik dynamic file, an Apache `Listen`
line), restore the previous file from your backup and start the service again.

**Prevent it next time**

- Monitor with a TCP or HTTPS check from **outside** the server, not only "is the process running".
- Set restart policies (`Restart=on-failure` for systemd units; Dokploy's Traefik runs with a Docker restart policy, check it with `docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' dokploy-traefik`).
- Keep a port inventory per server (who should own which port) and compare with `ss -ltnp` after every change. See [Ports inventory](22-playbook-ports-inventory.md).

### 5.2 Connection timed out

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 2) Note: [Learn: networking](28-learn-networking.md), areas "Routing" and "Firewalls and connection tracking" · 3) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) · 4) Practice: Section 12 #3 (ufw deny 443); for the AWS version, *AWS Networking Fundamentals* ([course](https://kodekloud.com/courses/aws-networking-fundamentals)).

**Level:** [L2 · Mid].

**Symptom:** `curl: (28) Failed to connect to app.example.com port 443 after
5002 ms: Timeout was reached` (older curl: `Connection timed out after 5001
milliseconds`). Without `--connect-timeout`, it hangs for about 130 seconds.

**Step 1 — Fail fast and try a second vantage point**

**Goal:** confirm the timeout quickly, and check whether it is specific to your network position.

```bash
# From your laptop, connected through the company VPN (172.17.20.50):
curl -sv --connect-timeout 5 -o /dev/null https://app.example.com/ 2>&1 | grep -E 'Trying|timed out|Timeout'
nc -vz -w 3 192.0.2.10 443
# From another host on the SERVER's own subnet:
ssh admin@192.0.2.11 'nc -vz -w 3 192.0.2.10 443'
```

```
*   Trying 192.0.2.10:443...
* Failed to connect to app.example.com port 443 after 5002 ms: Timeout was reached
nc: connect to 192.0.2.10 port 443 (tcp) timed out: Operation now in progress
Connection to 192.0.2.10 443 port [tcp/https] succeeded!
```

**What it means:** from the VPN, the connection disappears. From the server's
own subnet, it connects. The service is up; something drops the traffic
between the VPN and the server (a routed firewall, an ACL, a security group),
or the server's replies go back a different way. Office users reporting "it
works for me" while VPN users report "down" is the same signal.

**Why this step (now):** a second vantage point splits "the server is
unreachable" from "the server is unreachable **from here**" in one command, which
tells you whether to look at the host or at the network.

**Next step:** Step 2 on the server, to see whether your SYNs arrive.

**Step 2 — Capture on the server**

**Goal:** prove whether the packets from your client reach the server, and
which way the answer leaves.

```bash
sudo tcpdump -ni any 'tcp port 443 and host 172.17.20.50'
```

```
10:58:01.220114 ens18 In  IP 172.17.20.50.40112 > 192.0.2.10.443: Flags [S], seq 3011822, win 64240, length 0
10:58:01.220171 docker0 Out IP 192.0.2.10.443 > 172.17.20.50.40112: Flags [S.], seq 99120, ack 3011823, win 65160, length 0
10:58:02.244310 ens18 In  IP 172.17.20.50.40112 > 192.0.2.10.443: Flags [S], seq 3011822, win 64240, length 0
```

**What it means:** the SYN arrives on `ens18`, but the SYN-ACK leaves on
**`docker0`**, the Docker bridge. The reply never reaches the client, which
retransmits its SYN. Other patterns: SYN in, nothing out → host firewall
(Step 8). No SYN at all → an upstream drop (Step 9). SYN-ACK out on the right
interface but the client never sees it → a stateful device on the return path.

**Why this step (now):** the capture separates "dropped before the host",
"dropped by the host" and "answered the wrong way", and each has a different
fix.

**Next step:** wrong reply interface → Step 3. Nothing out → Step 8. Nothing in → Step 9.

**Step 3 — Check the return route**

**Goal:** find out why replies to this client use the wrong interface.

```bash
ip route get 172.17.20.50 from 192.0.2.10
ip route | grep -E 'docker0|br-'
docker network inspect bridge --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
```

```
172.17.20.50 from 192.0.2.10 dev docker0 uid 0
    cache
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev br-3f9c2a1d7e44 proto kernel scope link src 172.18.0.1
172.17.0.0/16
```

**What it means:** Docker's default bridge uses `172.17.0.0/16`, which
contains the VPN pool `172.17.20.0/24`. The kernel believes VPN clients live
behind `docker0`, so replies to them go into the bridge and vanish. Every
client outside 172.17.0.0/16 works, which is why the outage looks partial.
Compose and Swarm networks (`172.18.0.0/16`, `172.19.0.0/16`, ...) can collide
the same way with office ranges in 172.16.0.0/12. On multi-homed servers, the
same symptom appears when the reply route uses a different NIC than the one
the request arrived on.

**Why this step (now):** the capture showed the reply leaving the wrong way;
`ip route get ... from ...` asks the kernel which route it uses for the reply,
which is exactly the decision that went wrong.

**Next step:** overlap → move Docker's address pools (Fix & verify).
Multi-homed → add policy routing (`ip rule`, or `routing-policy` in netplan) so
replies leave via the interface the request came in on.

**Decision tree**

```
Connection timed out
├── works from server's own subnet, not from yours → path between subnets
├── tcpdump on server:
│     ├── no SYN arrives          → upstream drop: SG/NACL/edge FW/NAT/wrong IP (Step 9)
│     ├── SYN in, nothing out      → host firewall (ufw/nft) or SYN backlog full (ss Recv-Q, nstat -az TcpExtListenOverflows)
│     ├── SYN in, SYN-ACK out wrong iface → route overlap (docker0/br-*) or multi-homed return path
│     └── SYN in, SYN-ACK out right iface → stateful device on the return path drops it
└── ip neigh FAILED (same subnet) → host/NIC down, VLAN, IP conflict
```

**Fix & verify**

Move Docker's networks out of real address space (by default they come from
172.17.0.0/16 upwards). Pick a range your IP plan reserves for Docker:

```bash
sudo cp /etc/docker/daemon.json /root/daemon.json.bak 2>/dev/null || true
sudoedit /etc/docker/daemon.json
```

```
{
  "bip": "10.200.0.1/24",
  "default-address-pools": [ { "base": "10.201.0.0/16", "size": 24 } ],
  "dns": ["192.0.2.53", "192.0.2.54"]
}
```

```bash
sudo systemctl restart docker           # restarts containers: schedule it, Swarm services move/restart
ip route get 172.17.20.50 from 192.0.2.10   # now: via 192.0.2.1 dev ens18
nc -vz -w 3 192.0.2.10 443                  # from the VPN client: succeeded
```

Existing user-defined networks keep their old subnets until you recreate them.
Swarm overlay networks (`ingress`, `dokploy-network`) come from the swarm's own
pool (`docker swarm init --default-addr-pool`), and `docker_gwbridge` must be
recreated to change its subnet: plan the ranges before installing Dokploy, not
during an incident.
For a host firewall drop, the fix is a narrow allow rule such as
`sudo ufw allow proto tcp from 192.0.2.0/24 to any port 443`.

**Rollback**

Restore `/root/daemon.json.bak` and restart Docker. For a ufw rule:
`sudo ufw delete allow proto tcp from 192.0.2.0/24 to any port 443`.

**Prevent it next time**

- Set `bip` and `default-address-pools` in `daemon.json` **before** the first container on every new Docker host, from a range reserved for Docker in your IP plan.
- Keep a capture-first habit: never change firewall rules on a timeout until you know where the packet dies.
- Monitor from more than one network position (inside the LAN, through the VPN, from outside).

### 5.3 Works on localhost, not from other machines

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), area "Transport: TCP, UDP, ports and sockets" (quick refresher) · 2) KodeKloud: *DevOps Pre-Requisite Course*: Web Server → IPs and Ports ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 3) Containers: *Docker Certified Associate*: Docker Engine → Publishing Ports ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 4) Practice: Section 12 #5 (gunicorn without `--bind`) between two playground VMs.

**Level:** [L1 · Junior].

**Symptom:** on the server, `curl http://127.0.0.1:8000/` works. From any other
machine, `http://192.0.2.10:8000/` is refused (or times out with a firewall).

**Step 1 — Read the bind address**

**Goal:** see which address the service accepts connections on.

```bash
sudo ss -ltnp 'sport = :8000'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      2048       127.0.0.1:8000      0.0.0.0:*     users:(("gunicorn",pid=1550,fd=5))
```

**What it means:** the socket is bound to `127.0.0.1`, so only connections to
the loopback address are accepted. A connection to 192.0.2.10:8000 finds no
socket and is refused. This is not a firewall issue; opening ufw changes
nothing.

**Why this step (now):** it is the single most common cause of this symptom,
and `ss` proves or rules it out in one line.

**Next step:** loopback bind → Step 2. Bound to `0.0.0.0` → firewall (Step 8) or Docker (Step 4).

**Step 2 — Find where the bind address comes from**

**Goal:** locate the setting that chose 127.0.0.1.

```bash
systemctl cat gunicorn-app.service | grep -E 'ExecStart|bind'
grep -RnE 'bind|listen|host' /etc/gunicorn-app/ 2>/dev/null | head
```

```
ExecStart=/srv/app/venv/bin/gunicorn app.wsgi:application --workers 4
```

**What it means:** no `--bind`, so gunicorn uses its default
`127.0.0.1:8000`. Defaults that bind to loopback:

| Software | Default / setting |
|---|---|
| gunicorn | `127.0.0.1:8000` unless `--bind` (or `0.0.0.0:$PORT` when the `PORT` environment variable is set) |
| Flask / Django dev servers | `127.0.0.1` |
| Node `app.listen(3000, 'localhost')` | loopback (and `localhost` may mean `::1` only) |
| PostgreSQL | `listen_addresses = 'localhost'` |
| Redis | `bind 127.0.0.1 -::1`, plus `protected-mode yes` |
| MySQL / MariaDB on Ubuntu | `bind-address = 127.0.0.1` |
| Docker | `-p 127.0.0.1:18000:8000` publishes on loopback only |
| Apache after a migration | `Listen 127.0.0.1:8080` (fine for a proxy on the same host; a containerised Traefik cannot reach it) |

**Why this step (now):** you need to change the setting at its source, not
work around it. Knowing the default explains why it "suddenly" binds to
loopback: often nobody set it at all.

**Next step:** Step 3 before you change anything.

**Step 3 — Decide whether it should be reachable at all**

**Goal:** decide on the right fix rather than the quickest.

```bash
# Is a proxy on this host already configured to reach the app on loopback?
grep -RnE '127\.0\.0\.1:8000|localhost:8000' /etc/apache2/sites-enabled/ /etc/nginx/sites-enabled/ 2>/dev/null
# Who talks to the app today: only the local proxy, or other hosts too?
sudo ss -tn state established '( sport = :8000 )'
```

```
/etc/apache2/sites-enabled/app-ssl.conf:12:    ProxyPass / http://127.0.0.1:8000/
Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
0      0          127.0.0.1:8000     127.0.0.1:51822
0      0          127.0.0.1:8000     127.0.0.1:51830
```

**What it means:** Apache already proxies `app.example.com` to
`127.0.0.1:8000`, and every live connection to the app comes from the local
proxy. The person who reported "port 8000 refused" was bypassing the proxy.
A loopback bind is often **correct**. An app server behind
Apache, Nginx or Traefik should listen on loopback (or only on a Docker
network) so that nobody bypasses the proxy's TLS, headers and limits. If other
machines need the app, route them **through the proxy**: add a vhost or a
Dokploy domain instead of opening port 8000. Databases and Redis should only
be opened to the specific app hosts, with a firewall rule, and Redis never
without authentication.

**Why this step (now):** "make it listen on 0.0.0.0" is easy and frequently
wrong. It exposes an unauthenticated port, and with Docker published ports
ufw will not protect it (Step 9).

**Next step:** should go through the proxy → configure the proxy (§7.1 shows
the target settings). Should be reachable directly → change the bind, add a
narrow firewall rule.

**Step 4 — The container variant: reset or empty reply**

**Goal:** recognise the Docker form of the same mistake.

```bash
# On the Docker host, through the loopback address (docker-proxy handles this one)
curl -sv http://127.0.0.1:18000/ 2>&1 | tail -n 2
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
```

```
* Recv failure: Connection reset by peer
curl: (56) Recv failure: Connection reset by peer
LISTEN 0      511        127.0.0.1:8000       0.0.0.0:*
```

**What it means:** the port is published (`docker-proxy` accepts the
connection on the host's loopback), but inside the container the app listens
on `127.0.0.1`. docker-proxy's onward connection to the container's `eth0`
address finds nothing, so it drops the client. On the host the client sees
`(56) Connection reset by peer` or `(52) Empty reply from server`, not
"refused". From **another machine** the same mistake looks like a plain
`(7)` refused: there the iptables DNAT rule forwards the SYN straight to the
container, whose kernel answers RST. Behind Traefik it shows up as a 502
(§7.1).

**Why this step (now):** in containers the symptom changes shape, so it does
not look like the same bug. Checking the listener inside the namespace shows
that it is.

**Next step:** make the app bind `0.0.0.0` **inside** the container (it is
still isolated by Docker networking), and control exposure with how you
publish the port.

**Decision tree**

```
Works on localhost, not remotely
├── ss: 127.0.0.1:PORT / [::1]:PORT → loopback bind
│     ├── should be behind a proxy → keep it, route through Apache/Nginx/Traefik
│     └── must be reachable → change bind (gunicorn --bind, listen_addresses...) + narrow firewall rule
├── ss: 0.0.0.0:PORT → host firewall (ufw/nft) or cloud SG
└── container: reset / empty reply → app binds 127.0.0.1 INSIDE the container → bind 0.0.0.0 there
```

**Fix & verify**

For an app that must be reachable directly from one other host:

```bash
sudo systemctl edit gunicorn-app.service
```

```
[Service]
ExecStart=
ExecStart=/srv/app/venv/bin/gunicorn app.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

```bash
sudo systemctl restart gunicorn-app.service
sudo ufw allow proto tcp from 192.0.2.11 to any port 8000
sudo ss -ltnp 'sport = :8000'                     # 0.0.0.0:8000
ssh admin@192.0.2.11 'curl -s -o /dev/null -w "%{http_code}\n" http://192.0.2.10:8000/health'
```

The empty `ExecStart=` line is required: it clears the original before setting
the new one.

**Rollback**

`sudo systemctl revert gunicorn-app.service && sudo systemctl restart gunicorn-app.service`,
then `sudo ufw delete allow proto tcp from 192.0.2.11 to any port 8000`.

**Prevent it next time**

- Write the bind address explicitly in every unit, compose file and config. Do not rely on defaults.
- For anything behind Traefik, publish nothing: attach to `dokploy-network` and let Traefik route.
- Use `127.0.0.1:HOSTPORT:CONTAINERPORT` for temporary test ports on Docker hosts.

---

## 6. TLS scenarios

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course*: Security → SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)), then *Certified Kubernetes Administrator (CKA)*: Security → TLS Basics ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) · 2) Note: [Learn: networking](28-learn-networking.md), area "TLS and certificates" · 3) Video: ByteByteGo *SSL, TLS, HTTPS Explained* ([YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo)) · 4) Practice: every failure host on [badssl.com](https://badssl.com/); write down the exact curl error for each.

For the general certificate commands, see Step 10 and
[Web, HTTP & TLS](18-web-http-tls.md) section 3. To see each failure on
purpose, use the matching hosts on [badssl.com](https://badssl.com/).

### 6.1 curl (60) unable to get local issuer certificate

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course*: Security → SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)), then *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Essential Commands → Work With SSL Certificates ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 2) Note: [Web, HTTP & TLS](18-web-http-tls.md), then [Security & DevSecOps](37-learn-security-devsecops.md) for running a private CA · 3) Video: ByteByteGo *SSL, TLS, HTTPS Explained* ([YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo)) · 4) Practice: `curl -v` against the untrusted-root and incomplete-chain hosts on [badssl.com](https://badssl.com/), then Section 12 #9.

**Level:** [L2 · Mid].

**Symptom:** `curl: (60) SSL certificate problem: unable to get local issuer
certificate`. Often "works in the browser, fails in curl, Python, Java, Docker
or the CI runner". In Docker pulls from Harbor the same problem reads
`x509: certificate signed by unknown authority`.

**Step 1 — Count the certificates the server sends**

**Goal:** decide whether this is a server problem (incomplete chain) or a client problem (unknown CA).

```bash
openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null 2>/dev/null \
  | grep -E '^ *[0-9]+ s:|^ +i:|Verify return code'
```

```
 0 s:CN = app.example.com
   i:C = US, O = Example Corp, CN = Example Corp Issuing CA 1
    Verify return code: 21 (unable to verify the first certificate)
```

**What it means:** the server sends **only the leaf** (`0 s:`), issued by an
intermediate it does not send. A client that does not already have that
intermediate cannot build a path to a root. Browsers often hide this because
they cache intermediates or download them, which is why "the browser works".
A healthy server shows a `1 s:` line for the intermediate. If the chain is
complete and the code is **19** (`self-signed certificate in certificate
chain`) or **20**, the server is fine and this client simply does not trust
your root.

**Why this step (now):** the same error message has two causes on opposite
ends of the connection. Counting the certificates decides which end to fix,
so you do not install CAs on a hundred clients to cover a server that is
missing one file.

**Next step:** only the leaf → fix the server (Fix & verify, server side).
Chain complete, code 19 or 20 → Step 2.

**Step 2 — Check whether this client trusts your root**

**Goal:** confirm the private root is missing from this machine's trust store.

```bash
# Which root does the chain end at?
openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null 2>/dev/null \
  | grep -E '^ +i:' | tail -n 1
# Is that root in the system bundle? (prints every subject in the bundle, then filters)
awk -v cmd='openssl x509 -noout -subject' '/BEGIN/{close(cmd)}; {print | cmd}' \
  /etc/ssl/certs/ca-certificates.crt | grep -i 'Example Corp'
```

```
   i:C = US, O = Example Corp, CN = Example Corp Root CA
(no output from the second command)
```

**What it means:** the chain ends at `Example Corp Root CA`, a private root,
and the system bundle does not contain it. Every client of this service needs
the root installed, including containers and CI runners.

**Why this step (now):** it proves the client side is missing the root before
you change anything, and it names the exact root to distribute.

**Next step:** install the root (Fix & verify, client side), then Step 3 if one
particular program still fails.

**Step 3 — Find the trust store the failing program really uses**

**Goal:** stop "I installed the CA and it still fails".

```bash
# Example: a Python app in a virtualenv still fails after update-ca-certificates
/srv/app/venv/bin/python -c "import requests; requests.get('https://app.example.com/')" 2>&1 | tail -n 1
/srv/app/venv/bin/python -c "import certifi; print(certifi.where())"      # which bundle requests really reads
# Same request, forced onto the system bundle you just updated
REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
  /srv/app/venv/bin/python -c "import requests; print(requests.get('https://app.example.com/').status_code)"
```

```
requests.exceptions.SSLError: HTTPSConnectionPool(host='app.example.com', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)')))
/srv/app/venv/lib/python3.12/site-packages/certifi/cacert.pem
200
```

**What it means:** the virtualenv's `requests` verifies against its own
pip-installed `certifi` bundle, which knows nothing about your private root.
Forced onto the system bundle, the same request returns 200, so the CA is
installed correctly and this program simply looks elsewhere. Not every
program reads the system bundle:

| Client | Trust store | How to add your CA |
|---|---|---|
| curl, wget, apt, most of Ubuntu | `/etc/ssl/certs/ca-certificates.crt` | `/usr/local/share/ca-certificates/NAME.crt` + `sudo update-ca-certificates` |
| RHEL / Rocky | `/etc/pki/tls/certs/ca-bundle.crt` | `/etc/pki/ca-trust/source/anchors/` + `sudo update-ca-trust` |
| Python `requests` | its own `certifi` bundle | `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` |
| Node.js | built-in Mozilla list | `NODE_EXTRA_CA_CERTS=/path/to/root.crt` |
| Java | `cacerts` keystore | `keytool -importcert -cacerts -alias example-corp -file root.crt` |
| Docker daemon (Harbor pulls) | per registry | `/etc/docker/certs.d/harbor.example.com/ca.crt` |
| containerd (Kubernetes nodes) | per registry | `/etc/containerd/certs.d/harbor.example.com/hosts.toml` |
| a container image | the image's own bundle | add the CA in the Dockerfile and run `update-ca-certificates` at build time |

**Why this step (now):** after a correct system-level fix, the remaining
failures are almost always a program with its own trust store.

**Next step:** add the CA where that program looks; verify with that program, not with curl.

**Decision tree**

```
curl (60) unable to get local issuer certificate
└── openssl s_client -showcerts: how many certs sent?
    ├── leaf only (code 21) → server misconfig: serve fullchain (leaf + intermediate)
    └── leaf + intermediate(s)
        ├── code 19/20, root is PRIVATE → install root on the client
        │     └── still fails in one program → that program's own trust store (table)
        └── code 20, root is PUBLIC → client CA bundle outdated → update ca-certificates
```

**Fix & verify**

Server side: serve the full chain, leaf first, then the intermediate(s):

```bash
cat app.example.com.crt example-corp-issuing-ca-1.crt | sudo tee /etc/ssl/certs/app.example.com-fullchain.crt >/dev/null
# Apache: SSLCertificateFile /etc/ssl/certs/app.example.com-fullchain.crt
# Nginx:  ssl_certificate     /etc/ssl/certs/app.example.com-fullchain.crt;
# Traefik file provider: certFile pointing at the fullchain file
sudo apache2ctl configtest && sudo systemctl reload apache2
openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null 2>/dev/null \
  | grep -cE '^ *[0-9]+ s:'          # expect 2 or more
```

Client side: install the private root:

```bash
sudo cp example-corp-root.crt /usr/local/share/ca-certificates/example-corp-root.crt   # must end in .crt, PEM format
sudo update-ca-certificates
curl -sS -o /dev/null -w '%{http_code}\n' https://app.example.com/
```

```
Updating certificates in /etc/ssl/certs...
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
200
```

> ⚠️ `curl -k`, `verify=False` and `insecure-registries` are diagnostic tools only.
> In production they turn every TLS problem, including a real attack, into
> "working".

**Rollback**

Server: point the config back at the previous certificate file and reload.
Client: `sudo rm /usr/local/share/ca-certificates/example-corp-root.crt && sudo update-ca-certificates --fresh`.

**Prevent it next time**

- Always deploy `fullchain` files. Check with `-showcerts` from a clean client after every certificate change.
- Distribute the private root to every host, runner and image with configuration management (the ops ladder's Ansible drill), not by hand.
- Monitor TLS from a machine that has **only** the trust stores your users have.

### 6.2 No alternative certificate subject name matches

> 📚 **Study path:** 1) Note: [Web, HTTP & TLS](18-web-http-tls.md) (quick refresher) · 2) KodeKloud: *Nginx For Beginners*: Intermediate Config → Virtual Servers & Multiple Sites ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Virtual-Servers-Multiple-Sites/page)) and Security → HTTPS ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Security/HTTPS/page)) · 3) Apache side: *DevOps Pre-Requisite Course*: Web Server → Apache Web Server ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) and the [Apache virtual host docs](https://httpd.apache.org/docs/2.4/vhosts/) · 4) Practice: the wrong.host host on [badssl.com](https://badssl.com/).

**Level:** [L2 · Mid].

**Symptom:** `curl: (60) SSL: no alternative certificate subject name matches
target host name 'shop.example.com'`; browsers show `NET::ERR_CERT_COMMON_NAME_INVALID`.

**Step 1 — Read the names in the certificate actually served**

**Goal:** see which certificate the server picks for this name.

```bash
openssl s_client -connect shop.example.com:443 -servername shop.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName
```

```
subject=CN = legacy.example.com
X509v3 Subject Alternative Name:
    DNS:legacy.example.com
```

**What it means:** asked for `shop.example.com`, the server answered with the
certificate for `legacy.example.com`. Either the right certificate exists but a
different vhost or router answered, or the certificate for the right vhost does
not include the name. If the subject is `TRAEFIK DEFAULT CERT`, go to §6.4.

**Why this step (now):** the error names the **requested** host, not the
certificate you got. Seeing the served certificate tells you whether the
wrong vhost answered or the right one has an incomplete certificate.

**Next step:** a different site's certificate → Step 2. The right site's
certificate missing this name → reissue it with the name added (Fix & verify).

**Step 2 — See which vhost answers on 443**

**Goal:** find out why the server chose that certificate.

```bash
sudo apache2ctl -S 2>/dev/null | sed -n '/\*:443/,/\*:80/p'
sudo apache2ctl -S 2>/dev/null | grep -n 'shop'
```

```
*:443                  is a NameVirtualHost
         default server legacy.example.com (/etc/apache2/sites-enabled/000-legacy-ssl.conf:2)
         port 443 namevhost legacy.example.com (/etc/apache2/sites-enabled/000-legacy-ssl.conf:2)
         port 443 namevhost app.example.com (/etc/apache2/sites-enabled/app-ssl.conf:2)
*:80                   is a NameVirtualHost
6:         port 80 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.conf:1)
```

**What it means:** `shop.example.com` has a vhost on **port 80 only**. On 443
no vhost matches the SNI name, so Apache uses the **default server** for
`*:443`, the first one loaded (`000-legacy-ssl.conf`), and its certificate.
Nginx behaves the same with its `default_server` (or the first `server` block
for that `listen`). Traefik serves its default certificate instead.

**Why this step (now):** the served certificate came from the fallback. `-S`
shows the fallback and every name the server knows, which pinpoints the missing
vhost, `ServerName` or `ServerAlias`.

**Next step:** create the 443 vhost (or add `ServerAlias`) and make sure its
certificate covers the name.

**Step 3 — Check how clients address the server**

**Goal:** rule out client-side naming problems.

```bash
# The same server, addressed three ways
curl -sS -o /dev/null -w '%{http_code}\n' https://shop.example.com/   # the FQDN
curl -sS -o /dev/null -w '%{http_code}\n' https://192.0.2.10/         # by IP, as a misconfigured client or probe does
curl -sS -o /dev/null -w '%{http_code}\n' https://web01/              # short host name via the search domain
```

```
200
curl: (60) SSL: no alternative certificate subject name matches target host name '192.0.2.10'
000
curl: (60) SSL: no alternative certificate subject name matches target host name 'web01'
000
```

**What it means:** the server is correct for its FQDN. The same server fails
when addressed by IP or short name, because no certificate lists those names.
(curl 8.5 says `target host name '192.0.2.10'` even for an IP; newer curl
releases say `target IPv4 address '192.0.2.10'`, and `target hostname '...'`
for names.)
These also produce the error, even with a perfect server:

- Connecting by IP (`https://192.0.2.10/`) or short name (`https://web01/`): no certificate lists them.
- Wildcard depth: `*.example.com` covers `app.example.com`, but **not** `example.com` and **not** `api.app.example.com`.
- `curl -H 'Host: shop.example.com' https://192.0.2.10/` sends no SNI at all (an IP is never sent as SNI), so the server falls back to its default certificate and curl checks it against the IP: use `--resolve` instead (Step 12).

**Why this step (now):** if the server answers correctly for the FQDN (Step 1
run against the right name passes), the remaining cause is how the client asks.

**Next step:** use the FQDN in client config, or add the needed SAN.

**Decision tree**

```
no alternative certificate subject name matches
├── served cert subject = TRAEFIK DEFAULT CERT → §6.4
├── served cert = another site's cert → no 443 vhost/router for this name → apache2ctl -S / nginx -T
├── served cert = right site, name missing in SAN → reissue with the name
└── client uses IP / short name / deeper subdomain than the wildcard → use FQDN or add SAN
```

**Fix & verify**

```bash
# Option A: give shop its own 443 vhost (copy app-ssl.conf, set ServerName and its certificate)
sudo cp /etc/apache2/sites-available/app-ssl.conf /etc/apache2/sites-available/shop-ssl.conf
sudoedit /etc/apache2/sites-available/shop-ssl.conf     # ServerName shop.example.com + its cert/key
sudo a2ensite shop-ssl
# Option B (Let's Encrypt): one certificate with both names
sudo certbot --apache --cert-name app.example.com -d app.example.com -d shop.example.com
sudo apache2ctl configtest && sudo systemctl reload apache2
openssl s_client -connect shop.example.com:443 -servername shop.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -ext subjectAltName
```

**Rollback**

`sudo a2dissite shop-ssl && sudo systemctl reload apache2`. Certbot keeps the
previous certificate versions under `/etc/letsencrypt/archive/`.

**Prevent it next time**

- Every name that has a port-80 vhost needs a 443 vhost (or a redirect plus a covering certificate). Check `apache2ctl -S` after every site change.
- Make the default 443 vhost a deliberate "catch-all" with a neutral certificate and a 421/404 page, not a real customer site.
- Keep an inventory of names per certificate; add the SAN **before** adding the alias.

### 6.3 Certificate expired or not yet valid

> 📚 **Study path:** 1) Note: [Time & NTP](12-time-ntp.md) (quick refresher) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Set and Synchronize System Time ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Essential Commands → Work With SSL Certificates, for `openssl x509 -dates` ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 4) Practice: Section 12 #10 and the expired host on [badssl.com](https://badssl.com/).

**Level:** [L1 · Junior] for the clock and the reload; [L3 · Senior] for renewal paths that cannot fail silently.

**Symptom:** `curl: (60) SSL certificate problem: certificate has expired`, or
`certificate is not yet valid`, sometimes for a certificate you know is fine.

**Step 1 — Compare the served dates with the real time**

**Goal:** decide between "the certificate is wrong" and "the clock is wrong".

```bash
date -u                      # on the failing CLIENT
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -dates
```

```
Mon Jun  2 03:11:09 UTC 2025
notBefore=Sep  1 08:12:44 2026 GMT
notAfter=Nov 30 08:12:43 2026 GMT
```

**What it means:** the certificate is valid from 1 September 2026, but this
client thinks it is June 2025, so the certificate is "not yet valid". The
**client's** clock is wrong. If `date -u` were correct and `notAfter` in the
past, the certificate really expired (Step 3).

**Why this step (now):** both errors are comparisons between two dates.
Checking both dates first keeps you from renewing a perfectly good certificate
because a VM's clock drifted.

**Next step:** clock wrong → Step 2. Certificate expired → Step 3.

**Step 2 — Check time synchronisation**

**Goal:** find out why the clock is wrong and whether NTP can reach a server.

```bash
timedatectl
timedatectl timesync-status                     # systemd-timesyncd (Ubuntu 22.04/24.04 default)
journalctl -u systemd-timesyncd --since today --no-pager | tail -n 5
chronyc tracking; chronyc sources -v            # if chrony is used (RHEL/Rocky, many servers)
```

```
               Local time: Mon 2025-06-02 03:11:09 UTC
           Universal time: Mon 2025-06-02 03:11:09 UTC
System clock synchronized: no
              NTP service: active
Jun 02 03:05:44 web07 systemd-timesyncd[588]: Timed out waiting for reply from 203.0.113.123:123 (ntp.ubuntu.com).
```

**What it means:** NTP is enabled but has never synchronised: outbound UDP 123
to the public pool is blocked, which is common on-prem. A VM restored from an
old snapshot or a host with a dead RTC battery then keeps the wrong time
indefinitely. With chrony, `Reach 0` and `^?` in `chronyc sources` mean the same.

**Why this step (now):** fixing the clock fixes this error and a list of others
(Kerberos, AWS signatures, TOTP, log correlation). See [Time & NTP](12-time-ntp.md).

**Next step:** point the host at an internal NTP server (Fix & verify).

**Step 3 — Certificate really expired: find out why renewal failed**

**Goal:** find the broken renewal path, not only renew once.

```bash
sudo certbot certificates                                    # expiry per certificate
systemctl list-timers --all | grep -i certbot                # is the renewal timer there and firing?
sudo tail -n 30 /var/log/letsencrypt/letsencrypt.log
sudo certbot renew --dry-run                                 # does renewal work right now?
docker logs dokploy-traefik 2>&1 | grep -i acme | tail -n 5  # Traefik/Dokploy: ACME errors (§6.4)
```

```
  Certificate Name: app.example.com
    Expiry Date: 2026-09-30 08:12:43+00:00 (INVALID: EXPIRED)
Sat 2026-10-03 12:00:00 UTC  ...  certbot.timer  certbot.service
Certbot failed to authenticate some domains (authenticator: apache). The Certificate Authority reported these problems:
  Domain: app.example.com
  Type:   connection
  Detail: 203.0.113.10: Fetching http://app.example.com/.well-known/acme-challenge/...: Timeout during connect (likely firewall problem)
```

**What it means:** the timer runs, but the HTTP-01 challenge cannot reach
port 80: `Timeout during connect` means nothing answers there, typically a
firewall change that closed it. If port 80 now belongs to Traefik (your 81/444
setup), the same log says `Type: unauthorized` and `Invalid response from
http://app.example.com/.well-known/acme-challenge/...: 404` instead: Traefik
answers, but has no router sending the challenge path to Apache. Either way,
renewal has been failing silently for weeks until the certificate expired.

**Why this step (now):** renewing by hand without fixing the challenge path
gives you another outage in 60–90 days.

**Next step:** fix the challenge path (open 80, or move the site to Traefik's
ACME, or switch to DNS-01), renew, then Step 4.

**Step 4 — Renewed on disk, old certificate still served**

**Goal:** confirm the running server loaded the new certificate.

```bash
sudo openssl x509 -noout -enddate -in /etc/letsencrypt/live/app.example.com/fullchain.pem
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -enddate
```

```
notAfter=Dec 29 07:40:11 2026 GMT
notAfter=Sep 30 08:12:43 2026 GMT
```

**What it means:** the file on disk is renewed, but the process still serves
the old certificate from memory. Apache, Nginx and HAProxy read certificates
at start or reload only. Traefik renews and swaps its own ACME certificates by
itself, but it does not watch certificate files referenced by the file
provider: it re-reads them only when a file in its watched dynamic directory
changes. After replacing such a certificate, `touch` the dynamic YAML that
references it (or restart Traefik).

**Why this step (now):** "I renewed it and it is still expired" is almost
always this. The two `notAfter` dates prove it in two lines.

**Next step:** reload the server (Fix & verify).

**Decision tree**

```
certificate has expired / is not yet valid
├── date -u on client wrong? ── yes → NTP: timedatectl / chronyc → internal NTP server
└── clock right
    ├── notAfter past on SERVED cert
    │     ├── file on disk newer → reload proxy (deploy hook missing)
    │     └── file on disk also old → renewal broken → certbot dry-run / ACME logs → fix challenge path
    ├── intermediate in the served chain expired → re-download the current chain, serve fullchain
    └── notBefore future on server side → cert issued by a CA with a wrong clock (internal CA) → fix CA clock, reissue
```

**Fix & verify**

Clock (systemd-timesyncd):

```bash
sudo mkdir -p /etc/systemd/timesyncd.conf.d
printf '[Time]\nNTP=ntp1.corp.example.com ntp2.corp.example.com\n' | sudo tee /etc/systemd/timesyncd.conf.d/local.conf
sudo systemctl restart systemd-timesyncd
timedatectl | grep synchronized          # System clock synchronized: yes
```

With chrony: add `server ntp1.corp.example.com iburst` to
`/etc/chrony/chrony.conf` (RHEL: `/etc/chrony.conf`), restart `chrony`
(RHEL: `chronyd`), then `sudo chronyc makestep` to correct a large offset at once.

> ⚠️ Stepping a clock by months under a running database or message queue can
> confuse it (timeouts, TTLs, replication). On such hosts, coordinate the step
> or do it in a maintenance window.

Certificate: renew and reload:

```bash
sudo certbot renew --cert-name app.example.com
sudo apache2ctl configtest && sudo systemctl reload apache2
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -enddate
```

**Rollback**

Remove `/etc/systemd/timesyncd.conf.d/local.conf` and restart timesyncd. Certbot
keeps old certificate versions in `/etc/letsencrypt/archive/` (but an expired
one is no rollback target).

**Prevent it next time**

- Add a reload hook: `sudo certbot reconfigure --cert-name app.example.com --deploy-hook 'systemctl reload apache2'` (`reconfigure` needs certbot 2.3+, so Ubuntu 24.04's package or the snap; on 22.04's apt certbot 1.21, put a script in `/etc/letsencrypt/renewal-hooks/deploy/`). Certificates obtained with the `--apache` or `--nginx` installer are reloaded by certbot itself; the hook matters for `--webroot` / `--standalone` certificates and for other consumers of the files (HAProxy, a Traefik file provider, a mail server).
- Alert on certificates expiring within 14 days, checked from **outside**: `openssl x509 -noout -checkend 1209600` returns non-zero when less than 14 days remain.
- Provide an internal NTP service and point every host at it; alert on `System clock synchronized: no`.

### 6.4 TRAEFIK DEFAULT CERT served

> 📚 **Study path:** 1) KodeKloud: *Kubernetes Networking Deep Dive*: Kubernetes Ingress → Traefik Overview ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)), then Network Security → Cert Manager and Let's Encrypt (Traefik on Kubernetes, but routers, resolvers and ACME work the same on Docker) · 2) Note: [Web servers & proxies](29-learn-webservers-proxies.md), areas "Traefik in depth" and "Dokploy in depth" · 3) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* ([YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 4) Practice: Section 12 #11, with [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) open.

**Level:** [L2 · Mid].

**Symptom:** the browser warns about an untrusted certificate; the certificate
viewer shows `TRAEFIK DEFAULT CERT`. curl says `SSL certificate problem:
self-signed certificate`.

**Step 1 — Confirm, and check whether a router matches**

**Goal:** distinguish "no router for this name" from "router without a certificate".

```bash
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName
curl -sk -o /dev/null -w '%{http_code}\n' https://app.example.com/     # -k only for this diagnosis
```

```
subject=CN = TRAEFIK DEFAULT CERT
X509v3 Subject Alternative Name:
    DNS:6c1e9f3b0a7d42e1b5f0a1c2d3e4f5a6.0b7e2c9d8f1a3b4c5d6e7f8a9b0c1d2e.traefik.default
200
```

**What it means:** Traefik generates this self-signed certificate at start and
uses it whenever it has no better certificate for the SNI name. With `-k` the
request returns **200**, so a router matches and the app works; only the
certificate is missing. A **404** instead means no HTTPS router matches this
host at all (§8.1), which also produces the default certificate.

**Why this step (now):** the two cases need opposite fixes (router
configuration vs certificate acquisition), and one curl tells them apart.

**Next step:** 200 → Step 2 (why no certificate). 404 → §8.1.

**Step 2 — Read the ACME errors**

**Goal:** find out why Traefik could not obtain a certificate.

```bash
docker logs dokploy-traefik 2>&1 | grep -iE 'acme|certificate' | tail -n 5
sudo ls -l /etc/dokploy/traefik/dynamic/acme.json
```

```
2026-10-03T09:02:11Z ERR Unable to obtain ACME certificate for domains error="unable to generate a certificate for the domains [app.example.com]: error: one or more domains had a problem:\n[app.example.com] acme: error: 400 :: urn:ietf:params:acme:error:connection :: 203.0.113.10: Timeout during connect (likely firewall problem)\n" ACME CA=https://acme-v02.api.letsencrypt.org/directory acmeCA=https://acme-v02.api.letsencrypt.org/directory domains=["app.example.com"] providerName=letsencrypt.acme routerName=app-web-router-websecure-2@file rule=Host(`app.example.com`)
-rw------- 1 root root 14211 Oct  3 09:02 /etc/dokploy/traefik/dynamic/acme.json
```

**What it means:** Let's Encrypt tried the HTTP-01 challenge on port 80 of the
public IP and could not connect. Typical causes, in order:

- port 80 not forwarded or not allowed from the internet (on-prem edge firewall, SG);
- the name exists only in internal DNS: a public CA can **never** validate it with HTTP-01;
- public DNS still points at the old server, so the challenge lands on Apache;
- `acme.json` permissions other than `600`: Traefik refuses it with `permissions 644 for ... acme.json are too open, please use 600`;
- rate limits after many failed attempts (`too many failed authorizations`).

**Why this step (now):** Traefik always says why ACME failed; reading it beats
toggling HTTPS in the UI and hoping.

**Next step:** public site → fix port 80 reachability or DNS, Traefik retries.
Internal-only name → Step 3 (use your private CA certificate or DNS-01).

**Step 3 — Check the router's TLS configuration**

**Goal:** confirm what certificate source the router is told to use.

```bash
sudo grep -rn -B2 -A12 'app.example.com' /etc/dokploy/traefik/dynamic/*.yml
```

```
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-2-  routers:
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-3-    app-web-router-websecure-2:
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml:4:      rule: Host(`app.example.com`)
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-5-      service: app-web-service-2
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-6-      entryPoints:
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-7-        - websecure
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-8-      tls:
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-9-        certResolver: letsencrypt
```

grep marks the matching line with `:` and the context lines around it with `-`.

**What it means:** the router asks the `letsencrypt` resolver for a
certificate. For an internal name that cannot work, so the router must instead
use a certificate you provide: `tls: {}` with no resolver, plus your
certificate in Traefik's TLS store. Compose apps carry the same information as
labels (`traefik.http.routers.NAME.tls.certresolver=letsencrypt`); inspect them
with `docker inspect --format '{{json .Config.Labels}}' CONTAINER`.

**Why this step (now):** you now know why ACME failed; the configuration
shows whether ACME should be involved at all.

**Next step:** Fix & verify.

**Decision tree**

```
TRAEFIK DEFAULT CERT served
├── curl -k → 404 → no HTTPS router for this Host → §8.1 (rule, entrypoint, redeploy)
└── curl -k → 200 → router OK, no certificate
    ├── docker logs: ACME "Timeout during connect" → port 80 unreachable from internet / DNS points elsewhere
    ├── name is internal-only → HTTP-01 impossible → private CA cert (file provider) or DNS-01
    ├── acme.json "too open" → chmod 600, restart Traefik
    └── rate limited → fix cause, wait, test against the staging CA first
```

**Fix & verify**

For an internal name signed by your private CA, give Traefik the certificate
through a dynamic file, and make your wildcard the default instead of the
self-signed one. Dokploy's certificate settings write this kind of file for
you; if you write it by hand, the paths must be paths **inside** the Traefik
container.

```
# /etc/dokploy/traefik/dynamic/certs-internal.yml
tls:
  certificates:
    - certFile: /etc/dokploy/traefik/dynamic/certificates/wildcard-corp/fullchain.pem
      keyFile: /etc/dokploy/traefik/dynamic/certificates/wildcard-corp/privkey.pem
  stores:
    default:
      defaultCertificate:
        certFile: /etc/dokploy/traefik/dynamic/certificates/wildcard-corp/fullchain.pem
        keyFile: /etc/dokploy/traefik/dynamic/certificates/wildcard-corp/privkey.pem
```

Then set the router's `tls:` to `{}`, with no `certResolver`. In Dokploy, keep
HTTPS on for the domain and pick the certificate option that adds no Let's
Encrypt resolver (the option names differ between Dokploy versions), then
confirm the result in the generated file under `/etc/dokploy/traefik/dynamic/`
with the Step 3 grep. The file provider watches the directory, so Traefik picks
up the change without a restart.

```bash
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer
curl -sS -o /dev/null -w '%{http_code}\n' https://app.example.com/      # without -k
```

**Rollback**

Move `certs-internal.yml` out of the dynamic directory; Traefik drops it within
seconds. Restore the router's previous `tls:` block.

**Prevent it next time**

- Decide per domain **before** deploying: public name → ACME (HTTP-01 needs port 80 open; DNS-01 works without it); internal name → private CA.
- Set a default certificate (your wildcard) so a forgotten router shows a trusted certificate and a 404, not a scary warning.
- Alert on `Unable to obtain ACME certificate` in Traefik's logs.
- Practise: [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) and the Traefik docs at [doc.traefik.io](https://doc.traefik.io/traefik/).

---

## 7. Proxy error scenarios: 502, 503, 504

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Implement Reverse Proxies and Load Balancers ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)), then *Nginx For Beginners*: Reverse Proxy, Load Balancer and Monitoring & Troubleshooting ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 3) Video: KodeKloud *NGINX For Beginners | NGINX Tutorial* ([YouTube](https://www.youtube.com/watch?v=Hfg7_y0fGTg)) · 4) Practice: Section 12 #6, #7 and #8.

All four start the same way: find out **which** proxy produced the code
(Section 3), then read **that** proxy's error log (Step 13). The log line
nearly always names the upstream address and the error.

### 7.1 502 Bad Gateway

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Reverse proxy fundamentals" · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*: Networking → Implement Reverse Proxies and Load Balancers ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 3) Docker side: *Docker Certified Associate*: Docker Swarm → Docker Overlay Network ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) · 4) Video: KodeKloud *How Docker Networking Actually Works* ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY), 9 min) · 5) Practice: Section 12 #6, the ops ladder's "Traefik 502 with a wrong port" drill, on the KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)).

**Level:** [L2 · Mid].

**Symptom:** `502 Bad Gateway` (Traefik, Nginx) or `502 Proxy Error` (Apache).
The proxy is alive and matched a route, but did not get a valid HTTP response
from the upstream. Two cousins belong here too, because the cause is the same
broken upstream: Apache answers **503** when it cannot connect to the backend
at all (`AH01114`), and Traefik answers **504** after 30 s when the dial times
out (`dial tcp ...: i/o timeout`).

**Step 1 — Read the proxy's error line and classify it**

**Goal:** turn "502" into one specific upstream failure.

```bash
sudo grep -E 'AH01114|AH00957|AH01102' /var/log/apache2/error.log | tail -n 5     # Apache
sudo grep -E 'upstream|connect\(\)' /var/log/nginx/error.log | tail -n 5          # Nginx
docker logs --since 15m dokploy-traefik 2>&1 | grep -iE '502|dial tcp|EOF' | tail -n 5   # Traefik (DEBUG level)
```

```
2026-10-03T11:02:41Z DBG github.com/traefik/traefik/v3/pkg/proxy/httputil/proxy.go:121 > 502 Bad Gateway error="dial tcp 10.0.1.14:3000: connect: connection refused"
```

**What it means:** use this table to read the line:

| Log line | Proxy | Meaning |
|---|---|---|
| `(111)Connection refused: AH00957` then `AH01114: HTTP: failed to make connection to backend` | Apache | nothing listens on the `ProxyPass` target (the client gets a **503**, not a 502) |
| `AH01102: error reading status line from remote server` | Apache | the upstream accepted, then closed without answering (crash, worker killed, keep-alive race) |
| `(13)Permission denied: AH00957` | Apache on RHEL | SELinux blocks httpd from connecting (`setsebool -P httpd_can_network_connect 1`); the client gets a 503 |
| `connect() failed (111: Connection refused) while connecting to upstream` | Nginx | nothing listens on the `proxy_pass` target |
| `upstream prematurely closed connection while reading response header` | Nginx | the upstream closed early (worker killed at a timeout, crash) |
| `recv() failed (104: Connection reset by peer)` | Nginx | the upstream reset the connection |
| `connect() to unix:/run/php/php8.3-fpm.sock failed (2: No such file or directory)` | Nginx | php-fpm down, or the socket path names the wrong PHP version |
| `upstream sent too big header while reading response header` | Nginx | large cookies / headers: raise `proxy_buffer_size` |
| `no live upstreams while connecting to upstream` | Nginx | every server in the upstream block was marked failed |
| `dial tcp IP:PORT: connect: connection refused` | Traefik | same network, nothing listening on that port |
| `dial tcp IP:PORT: i/o timeout` | Traefik | IP unreachable: the container is not on a network Traefik shares, Traefik picked the wrong network, or a firewall drops it. The client gets a **504** after the 30 s `dialTimeout` |
| `lookup NAME on 127.0.0.11:53: no such host` | Traefik | the service name does not resolve from Traefik (not on `dokploy-network`, or no running task) |
| `EOF` | Traefik | the upstream closed the connection without a response |

Here: Traefik reached the container's IP on `dokploy-network`, and nothing
listens on port 3000.

On your own server, where Traefik forwards the Apache sites to
`http://192.0.2.10:81`, the same two lines read differently: `dial tcp
192.0.2.10:81: connect: connection refused` means Apache is not listening on
that address (stopped, or bound to `127.0.0.1:81` only; users get a 502), and
`i/o timeout` means ufw drops the traffic from the Docker bridge to port 81
(users wait 30 s and get a **504**, not a 502). Both are
covered in [Deployment patterns](35-deployment-patterns.md), Steps 9 and 13.

**Why this step (now):** the errno separates the four real causes (nothing
listening, unreachable, crashed mid-request, permission) that all look
identical from the browser. It costs one grep.

**Next step:** refused → Step 2. Timeout / no such host → Step 3. Closed early
/ EOF → §7.3 (a timeout killed the worker) or §7.4 (keep-alive race).

**Step 2 — Ask the app what it listens on**

**Goal:** compare the port and address the proxy uses with what the app really listens on.

```bash
docker ps --filter name=app-web --format '{{.Names}}'
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
sudo grep -rn -A4 'app-web-service' /etc/dokploy/traefik/dynamic/*.yml | grep -i url
```

```
app-web-3k2j1.1.x3k1q8ab9c0d
LISTEN 0      2048         0.0.0.0:8000       0.0.0.0:*
/etc/dokploy/traefik/dynamic/app-web-3k2j1.yml-22-          - url: http://app-web-3k2j1:3000
```

**What it means:** the app listens on 8000 on all interfaces, which is fine.
The Dokploy domain says port 3000, so the routing is wrong, not the app. The
same check catches `127.0.0.1:8000` inside the container (fix the bind, §5.3),
and Apache `ProxyPass` lines pointing at an old port.

**Why this step (now):** "connection refused" means the target address and
port are wrong or empty. Comparing both sides settles which side to change.

**Next step:** change the port in the Dokploy domain settings (or the
`loadbalancer.server.port` label), redeploy, verify.

**Step 3 — Check that Traefik and the app share a network**

**Goal:** explain `i/o timeout` and `no such host` errors.

```bash
docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{$v.IPAddress}}{{"\n"}}{{end}}' CONTAINER
docker network inspect dokploy-network -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
docker inspect --format '{{json .Config.Labels}}' CONTAINER | tr ',' '\n' | grep -E 'server.port|docker.network|rule'
```

```
shop_default 172.20.0.3
dokploy-traefik 10.0.1.4/24
app-web-3k2j1.1.x3k1q8ab9c0d 10.0.1.14/24
"traefik.http.routers.shop.rule":"Host(`shop.example.com`)"
```

**What it means:** the Compose app `shop` is only on its project network
`shop_default`. Traefik is not on that network, so the container's IP is
unreachable for it (`i/o timeout`, which users see as a 504 after 30 s).
Containers on several networks give the same error when Traefik picks the
wrong IP; pin it with the label `traefik.docker.network=dokploy-network`. For a
Compose app that Dokploy deploys as a Swarm **stack**, Traefik v3 reads it
through the Swarm provider, whose label is `traefik.swarm.network` instead.

**Why this step (now):** with Docker, "reachable" means "on a shared network".
Listing networks on both sides proves or disproves it in two commands.

**Next step:** attach the service to `dokploy-network` (Fix & verify), redeploy.

**Decision tree**

```
502 Bad Gateway
├── who? (Section 3) → read THAT proxy's error log
├── refused (111)
│     ├── app listens on another port → fix ProxyPass / Dokploy port / server.port label
│     ├── app listens on 127.0.0.1 inside container → bind 0.0.0.0 (§5.3)
│     └── app not running → Step 14 (crash loop, OOM, config)
├── timeout / i/o timeout (Traefik 504) / no such host → not on a shared network → dokploy-network + traefik.docker.network
├── closed early / EOF / AH01102
│     ├── at a fixed time (30 s) → worker timeout → §7.3
│     └── random, low traffic → keep-alive race → §7.4
└── permission denied → socket perms / SELinux (RHEL)
```

**Fix & verify**

For a Compose app in Dokploy, join the external network and name the port:

```
services:
  web:
    image: harbor.example.com/apps/shop:4f2c9e1
    expose:
      - "8000"
    networks:
      - dokploy-network
    labels:
      - traefik.enable=true
      - traefik.http.routers.shop.rule=Host(`shop.example.com`)
      - traefik.http.routers.shop.entrypoints=websecure
      - traefik.http.routers.shop.tls=true
      - traefik.http.routers.shop.tls.certresolver=letsencrypt   # public names only; internal names: §6.4
      - traefik.http.services.shop.loadbalancer.server.port=8000
      - traefik.docker.network=dokploy-network
networks:
  dokploy-network:
    external: true
```

When you add the domain in Dokploy's UI it injects equivalent labels. Labels
are read at deploy, so **redeploy** after any change. If the compose type is
"Stack" (deployed with `docker stack deploy`), the labels go under
`deploy: labels:` and the network label is `traefik.swarm.network`.

```bash
for i in $(seq 1 20); do curl -s -o /dev/null -w '%{http_code}\n' https://shop.example.com/; done | sort | uniq -c
```

```
     20 200
```

**Rollback**

Redeploy the previous compose file (Dokploy keeps deployment history; the
compose file should be in Git).

**Prevent it next time**

- Pin the port with `loadbalancer.server.port`; never rely on Traefik guessing from `expose`.
- Pin the network with `traefik.docker.network` for multi-network containers (`traefik.swarm.network` for Swarm stacks).
- Add a Docker `HEALTHCHECK` (or Dokploy health check) so a dead app is visible before users see 502s.
- Lab: the ops ladder's "make Traefik return 502 on purpose with a wrong port" drill.

### 7.2 503 Service Unavailable

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Apache httpd in depth" · 2) KodeKloud: *Nginx For Beginners*: Performance → Monitoring & Troubleshooting ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Performance/Monitoring-Troubleshooting/page)) · 3) KodeKloud: *Fundamentals of SRE*: Observability and Monitoring → Performance Monitoring Deep Dive ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page)) · 4) Practice: Section 12 #8 (`pm.max_children = 1` under load).

**Level:** [L2 · Mid] to diagnose; [L3 · Senior] to size the pools from measured memory.

**Symptom:** `503 Service Unavailable`. Unlike a 502, the proxy usually did
not even try the upstream: it decided nothing was available, or it was out of
capacity.

**Step 1 — Identify the flavour of 503**

**Goal:** find which component decided "unavailable", and why.

```bash
curl -s -D - https://app.example.com/ | head -n 12
sudo grep -E 'AH00940|AH01079|AH02454|AH01170' /var/log/apache2/error.log | tail -n 5
sudo grep -E 'limiting requests|no live upstreams' /var/log/nginx/error.log | tail -n 3
```

```
HTTP/1.1 503 Service Unavailable
Server: Apache/2.4.58 (Ubuntu)
Content-Type: text/html; charset=iso-8859-1

[Sat Oct 03 11:14:09.120443 2026] [proxy:error] [pid 1342:tid 140233] (11)Resource temporarily unavailable: AH02454: FCGI: attempt to connect to Unix domain socket /run/php/php8.3-fpm.sock (localhost) failed
[Sat Oct 03 11:14:09.120501 2026] [proxy_fcgi:error] [pid 1342:tid 140233] [client 192.0.2.50:50122] AH01079: failed to make connection to backend: httpd-UDS
```

**What it means:** match it against the flavours:

| Evidence | From | Meaning |
|---|---|---|
| body `no available server` | Traefik | the service has no healthy server left (all failed health checks, no running task) |
| `AH00940: HTTP: disabled connection for (127.0.0.1:8000)` | Apache | backend in its retry window after an earlier failure (`AH00959 ... for 60s`) |
| `AH02454 (11)Resource temporarily unavailable` + `AH01079` | Apache + php-fpm | every php-fpm child is busy **and** the socket's queue (`listen.backlog`, 511 by default on Linux) is full |
| `(111)Connection refused: AH00957` + `AH01114` | Apache | the backend refused the connect (nothing listening): Apache reports that as 503, see §7.1 |
| `AH01170: ... All workers are in error state` | Apache balancer | every pool member failed |
| `limiting requests, excess: ... by zone` | Nginx | `limit_req` rejected the request; its default status is 503 |
| `Server: awselb/2.0` | AWS ALB | no healthy targets (`aws elbv2 describe-target-health`, see [AWS](16-aws-cloud.md)) |
| app-styled maintenance page | the app | maintenance mode (for example Laravel `php artisan down`) |

Here php-fpm is saturated.

**Why this step (now):** a 503 has very different causes (capacity, health,
retry state, rate limits, maintenance mode). The headers and one grep tell you
which one before you restart anything, and a restart would hide a capacity
problem only until the next peak.

**Next step:** capacity (php-fpm, Apache workers) → Step 2. Apache retry
window → Step 3. Traefik `no available server` → Step 14 and the health check.

**Step 2 — Measure the capacity limit and the memory behind it**

**Goal:** confirm saturation and work out a safe new limit.

```bash
sudo grep -E 'max_children' /var/log/php8.3-fpm.log | tail -n 2
grep -E '^pm(\.max_children|\.start_servers|\.max_spare_servers)? *=' /etc/php/8.3/fpm/pool.d/www.conf
ps --no-headers -o rss -C php-fpm8.3 | awk '{s+=$1; n++} END {printf "%d processes, average %.0f MB\n", n, s/n/1024}'
free -m
sudo grep -E 'AH00484|AH00161' /var/log/apache2/error.log | tail -n 2    # Apache itself full?
curl -s 'http://127.0.0.1/server-status?auto' | grep -E 'BusyWorkers|IdleWorkers'
```

```
[03-Oct-2026 11:14:02] WARNING: [pool www] server reached pm.max_children setting (5), consider raising it
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.max_spare_servers = 3
6 processes, average 58 MB
               total        used        free      shared  buff/cache   available
Mem:            7940        2210         820          64        4910        5420
```

**What it means:** the pool allows 5 children (Ubuntu's default) at about 58 MB
each. With about 5.4 GB available, you could afford far more:
`(available memory you give PHP) / average RSS`, for example 3000 / 58 ≈ 50.
Leave headroom for the database and the page cache. If instead `AH00484`
(event MPM) or `AH00161` (prefork) appears, **Apache itself** is at
`MaxRequestWorkers`. Apache does not answer 503 then: new connections wait in
the listen backlog, users see slowness and timeouts, and the 503 comes from
whatever health-checks Apache from the front (Traefik, an ALB).

**Why this step (now):** raising limits without the memory math trades a 503
for swapping or an OOM kill, which is a worse outage. Measured RSS makes the
new number defensible.

**Next step:** raise the limit (Fix & verify), and find out **why** requests
pile up (slow DB? one slow endpoint? a crawler? see [Slow system playbook](23-playbook-slow-system.md)).

**Step 3 — Apache still answers 503 after the backend is back**

**Goal:** recognise the retry window.

```bash
sudo grep -E 'AH00959|AH00940' /var/log/apache2/error.log | tail -n 3
```

```
[Sat Oct 03 11:20:02.551301 2026] [proxy:error] [pid 1342:tid 140233] AH00959: ap_proxy_connect_backend disabling worker for (127.0.0.1:8000) for 60s
[Sat Oct 03 11:20:30.004112 2026] [proxy:error] [pid 1342:tid 140240] AH00940: HTTP: disabled connection for (127.0.0.1:8000)
```

**What it means:** one failed connection put the backend in an error state for
60 seconds (`retry=60`, the default). Requests during that window get an
immediate 503 without Apache even trying, even though the app is back.

**Why this step (now):** without this, you would conclude your fix failed and
start changing things that are already correct.

**Next step:** wait 60 seconds, or `sudo systemctl reload apache2` to reset the
workers. For single-backend `ProxyPass` lines, set `retry=0` (Fix & verify).

**Decision tree**

```
503 Service Unavailable
├── Traefik "no available server" → no healthy task/server → Step 14 + health check
├── Apache AH00940 after AH00959 → retry window → wait / reload / retry=0
├── Apache AH01114 / AH00957 (111) → backend refused the connect → §7.1 (Apache says 503, the cause is a 502-type fault)
├── Apache AH01079 + AH02454 (11) → php-fpm full → pm.max_children (memory math) + why slow
├── Apache AH00484/AH00161 → MaxRequestWorkers → front proxy/LB health fails → raise (memory math) + why slow
├── Nginx "limiting requests" → limit_req → tune zone/burst, or it's an attack/crawler
├── ALB awselb → describe-target-health → health check path / SG
└── app maintenance page → someone ran maintenance mode → ask / bring it up
```

**Fix & verify**

```bash
sudo cp /etc/php/8.3/fpm/pool.d/www.conf /root/www.conf.bak
sudo sed -i 's/^pm.max_children = .*/pm.max_children = 40/' /etc/php/8.3/fpm/pool.d/www.conf
sudo php-fpm8.3 -t                                   # config test
sudo systemctl reload php8.3-fpm
# Apache, single backend: do not blacklist it for 60 s after one failure
#   ProxyPass "/" "http://127.0.0.1:8000/" retry=0
sudo apache2ctl configtest && sudo systemctl reload apache2
for i in $(seq 1 50); do curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/; done | sort | uniq -c
```

**Rollback**

`sudo cp /root/www.conf.bak /etc/php/8.3/fpm/pool.d/www.conf && sudo systemctl reload php8.3-fpm`.

**Prevent it next time**

- Size worker pools from measured memory, write the calculation in the config file as a comment.
- Monitor saturation, not just up/down: php-fpm status page (`pm.status_path`), Apache `server-status`, and alert on `max_children` warnings.
- Health checks should test what users need (a page that touches the DB), with a timeout shorter than the proxy's.

### 7.3 504 and requests dying at 30 or 60 seconds

> 📚 **Study path:** 1) Note: the time-to-failure table in Section 3 and [Slow system playbook](23-playbook-slow-system.md) · 2) Read: [Deploying Gunicorn](https://gunicorn.org/deploy/) (KodeKloud has no lesson on the timeout chain) · 3) KodeKloud: *Nginx For Beginners*: Intermediate Config → Reverse Proxy ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) · 4) Note: [Databases for DevOps](38-learn-databases-ops.md) for the slow query behind the timeout · 5) Practice: Section 12 #7 (`time.sleep(40)` in one view).

**Level:** [L2 · Mid].

**Symptom:** some requests (an export, a report, an upload) always fail after
the same number of seconds: a 502 at about 30 s or a 504 at 60 s, while quick
pages work.

**Step 1 — Time the request through the proxy and directly**

**Goal:** measure exactly when and where it dies.

```bash
curl -sS -o /dev/null -w '%{http_code} %{time_total}s\n' https://app.example.com/reports/export
curl -sS -o /dev/null -w '%{http_code} %{time_total}s\n' http://127.0.0.1:8000/reports/export   # on the server, no proxy
```

```
502 30.041s
curl: (52) Empty reply from server
000 30.012s
```

**What it means:** even **without** the proxy, the connection dies at 30.0 s
with no response. The app server kills the request; the proxy only reports
it (as 502, because the upstream closed early). A 504 at exactly 60 s through
the proxy, with the direct request finishing in 75 s, would instead point at
the proxy's read timeout.

**Why this step (now):** the time-to-failure fingerprint (Section 3) names the
component whose timeout fires. Running the same request with and without the
proxy tells you which side of the proxy it is on.

**Next step:** dies at about 30 s directly → Step 2 (gunicorn). Dies only
through the proxy → proxy timeout (Fix & verify table).

**Step 2 — Confirm the app server's timeout**

**Goal:** find the log line that proves which component killed it.

```bash
journalctl -u gunicorn-app.service --since '10 min ago' --no-pager | grep -E 'WORKER TIMEOUT|Booting worker'
sudo grep 'upstream timed out' /var/log/nginx/error.log | tail -n 2      # Nginx variant
```

```
Oct 03 11:31:12 web01 gunicorn[1550]: [2026-10-03 11:31:12 +0000] [1550] [CRITICAL] WORKER TIMEOUT (pid:1612)
Oct 03 11:31:13 web01 gunicorn[1550]: [2026-10-03 11:31:13 +0000] [1701] [INFO] Booting worker with pid: 1701
```

**What it means:** gunicorn's master killed worker 1612 because it had not
reported back for 30 seconds (`--timeout`, default 30), then started a
replacement. Every request handled by that worker died with it. The Nginx
variant reads `upstream timed out (110: Connection timed out) while reading
response header from upstream`, which produces a 504.

**Why this step (now):** it is direct evidence; you are no longer guessing from
the number 30.

**Next step:** Step 3. Only raise timeouts after you know why the request is slow.

**Step 3 — Find out why the request takes that long**

**Goal:** fix the slowness rather than hide it.

```bash
# Python: what is the stuck worker doing right now? (pip install py-spy)
sudo py-spy dump --pid 1701
# PostgreSQL: long-running queries
sudo -u postgres psql -c "SELECT pid, now()-query_start AS runtime, left(query,80) FROM pg_stat_activity WHERE state='active' ORDER BY runtime DESC LIMIT 5;"
# PHP: log slow requests with a stack trace (pool config): request_slowlog_timeout = 5s, slowlog = /var/log/php-fpm-slow.log
```

```
 pid  |    runtime      |                          left
------+-----------------+--------------------------------------------------------------
 4412 | 00:00:41.20311  | SELECT o.*, c.* FROM orders o JOIN customers c ON ... WHERE
```

**What it means:** the export runs a 41-second query (missing index, no
pagination). Raising timeouts would make this request "work" and let each one
hold a worker for 40+ seconds; a handful of users clicking export would then
exhaust the pool (§7.2).

**Why this step (now):** the timeout is the symptom; the slow work is the
cause. Fixing the cause (index, background job, pagination) removes the
outage and the capacity risk at once.

**Next step:** fix the query or move the work to a background job (return 202
and poll). If the long request is legitimate, raise timeouts as below.

**Decision tree**

```
request dies at a fixed time
├── ~30 s, also when calling the app directly → app server timeout (gunicorn WORKER TIMEOUT, PHP max_execution_time)
├── 60 s only through Nginx → proxy_read_timeout (504)
├── 60 s through an ALB → idle timeout (504 from awselb)
├── 60 s, uploads through Traefik v3 → entrypoint readTimeout
├── 300 s through Apache (Ubuntu) → Timeout/ProxyTimeout 300
└── in all cases: WHY is it slow? → DB query / external API / CPU → fix or background job first
```

**Fix & verify**

If a long request is legitimate, raise the timeouts **together**, outermost
largest, so the innermost layer gives up first and logs why:

| Layer | Setting | Default |
|---|---|---|
| AWS ALB | idle timeout attribute | 60 s |
| Traefik | `serversTransports` `forwardingTimeouts.responseHeaderTimeout` (and `dialTimeout`); entrypoint `respondingTimeouts.readTimeout` / `writeTimeout` | 0 (none) for response headers; dialTimeout 30 s; readTimeout 60 s in v3 |
| Nginx | `proxy_read_timeout`, `proxy_send_timeout` | 60 s |
| Apache | `ProxyTimeout`, or `timeout=` on `ProxyPass` | `Timeout` (300 s in Ubuntu's apache2.conf) |
| gunicorn | `--timeout` | 30 s |
| PHP | `max_execution_time`, php-fpm `request_terminate_timeout` | 30 s, 0 (off) |

```bash
sudo systemctl edit gunicorn-app.service        # ExecStart= ... --timeout 120
sudo systemctl restart gunicorn-app.service
# Nginx: proxy_read_timeout 130s;  →  sudo nginx -t && sudo systemctl reload nginx
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://app.example.com/reports/export
```

**Rollback**

`sudo systemctl revert gunicorn-app.service && sudo systemctl restart gunicorn-app.service`;
restore the proxy file from its backup and reload.

**Prevent it next time**

- Write the timeout chain down once per stack (a table like the one above, with your values).
- Long work belongs in a queue (Celery, RQ, Laravel queues), not in a request.
- Alert on `WORKER TIMEOUT` and on p99 latency approaching the smallest timeout. Reference: [Deploying Gunicorn](https://gunicorn.org/deploy/).

### 7.4 Intermittent 5xx from one backend in a pool

> 📚 **Study path:** 1) KodeKloud: *Nginx For Beginners*: Intermediate Config → Load Balancer ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 2) Note: [Learn: networking](28-learn-networking.md), area "Load balancing and health checks" · 3) Swarm: *Docker Certified Associate*: Docker Swarm → Swarm Service Discovery ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Swarm-Service-Discovery/page)) · 4) Practice: on the KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)), put Nginx in front of three small backends, make one return 500, then find it with the 100-request loop and `$upstream_addr`.

**Level:** [L3 · Senior].

**Symptom:** "every few requests fail", "refresh and it works". Typically one
replica, node or pool member out of several is bad, or a keep-alive race
between proxy and backend.

**Step 1 — Quantify the failure rate**

**Goal:** turn "sometimes" into a number you can watch while you fix it.

```bash
for i in $(seq 1 100); do curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/health; done | sort | uniq -c
```

```
     67 200
     33 502
```

**What it means:** about one in three requests fails. With three replicas
behind round-robin, that is exactly the pattern of **one** broken replica.
Rare, random failures (1–2 %) under low traffic suggest a keep-alive race
instead (Step 4).

**Why this step (now):** you need a baseline to know whether a change helped,
and the ratio itself is a hint (1/N of N backends).

**Next step:** Step 2.

**Step 2 — Find which backend the failures come from**

**Goal:** tie each failure to a backend address.

```bash
# Nginx: add $upstream_addr to the log, for example:
#   log_format upstreamlog '$remote_addr [$time_local] "$request" $status $request_time $upstream_status $upstream_addr';
#   access_log /var/log/nginx/upstream.log upstreamlog;
sudo awk '$7 >= 500 {print $10}' /var/log/nginx/upstream.log | sort | uniq -c
# Traefik JSON access log (path = accessLog.filePath in traefik.yml): which backend served the 5xx?
sudo jq -r 'select(.DownstreamStatus >= 500) | .ServiceAddr' /etc/dokploy/traefik/dynamic/access.log | sort | uniq -c
# Swarm: where do the replicas run?
docker service ps app-web-3k2j1 --filter desired-state=running --format '{{.Name}} {{.Node}} {{.Image}} {{.CurrentState}}'
```

```
     33 10.0.1.17:8000
app-web-3k2j1.1 web01 harbor.example.com/apps/web:4f2c9e1 Running 2 hours ago
app-web-3k2j1.2 web02 harbor.example.com/apps/web:4f2c9e1 Running 2 hours ago
app-web-3k2j1.3 web03 harbor.example.com/apps/web:4f2c9e1 Running 2 hours ago
```

**What it means:** every failure came from `10.0.1.17`. Map that IP to a task
(`docker network inspect dokploy-network`) and you have the bad replica and its
node, here `web03`.

**Why this step (now):** aggregated logs hide a single bad member; grouping by
upstream address exposes it.

**Next step:** Step 3 on that node.

**Step 3 — Compare the bad backend with a good one**

**Goal:** find what is different about it.

```bash
# On web03 vs web01: same image digest? same config? healthy host?
docker inspect --format '{{.Image}}' $(docker ps -q --filter name=app-web-3k2j1)
df -h /var/lib/docker; timedatectl | grep synchronized
docker run --rm --net container:$(docker ps -q --filter name=app-web-3k2j1) nicolaka/netshoot nc -vz -w 3 db01.example.com 5432
```

```
sha256:9b1f0c...
/dev/sda2        40G   40G     0 100% /
nc: connect to db01.example.com (192.0.2.30) port 5432 (tcp) timed out: Operation now in progress
```

**What it means:** `web03`'s disk is full, and from its containers the
database is unreachable (a DB-side firewall rule allows only `web01` and
`web02`). Typical differences: disk, clock, DNS, firewall rules on dependencies,
an image that did not update, a node-local `.env` or volume.

**Why this step (now):** the replica is identical on paper; the difference is
in its environment. Comparing side by side is faster than reading code.

**Next step:** take it out of rotation (Fix & verify), then fix the node.

**Step 4 — The keep-alive race (no single bad backend)**

**Goal:** recognise intermittent 502s caused by idle connection reuse.

```bash
# Do the failures spread over ALL backends? (one bad backend → Step 2 instead)
sudo grep 'prematurely closed' /var/log/nginx/error.log | grep -o 'upstream: "http://[^/"]*' | sort | uniq -c
# Compare idle keep-alive on both sides of the hop
sudo nginx -T 2>/dev/null | grep -nE 'keepalive(_timeout)? '
systemctl cat gunicorn-app.service | grep ExecStart
```

```
     11 upstream: "http://10.0.1.15:8000
     12 upstream: "http://10.0.1.16:8000
41:    keepalive 32;
42:    keepalive_timeout 60s;
ExecStart=/srv/app/venv/bin/gunicorn app.wsgi:application --workers 4 --worker-class gthread --threads 4 --keep-alive 2 --bind 0.0.0.0:8000
```

The matching error lines are mostly `POST` requests: Nginx retries an
idempotent request (GET, HEAD) on another connection when a reused one fails,
so the race mainly reaches users on non-idempotent requests.

**What it means:** the failures are spread evenly over both backends, so no
single member is bad. Nginx keeps idle upstream connections for 60 s
(`keepalive_timeout` in the `upstream` block), while gunicorn closes them after
2 s. The proxy reuses an idle keep-alive connection at the
moment the backend closes it, and that request fails (`AH01102`, Nginx
`upstream prematurely closed`, Traefik `EOF`, ALB 502). Signs: rare, random,
worse at **low** traffic, no correlation with one backend. Known cases: Node.js
`server.keepAliveTimeout` 5 s behind an ALB with a 60 s idle timeout, gunicorn
`--keep-alive` 2 s behind a proxy that keeps connections longer. The rule:
**the backend must keep idle connections open longer than the proxy does**
(Node: `server.keepAliveTimeout = 65000` behind an ALB; Apache:
`ProxyPass ... ttl=` shorter than the backend's keep-alive).

**Why this step (now):** if Step 2 shows no single bad backend, this is the
next most common cause, and it is invisible unless you know to compare the two
keep-alive values.

**Next step:** align keep-alive timeouts, then repeat the Step 1 loop.

**Decision tree**

```
intermittent 5xx
├── loop 100 requests → failure ratio ≈ 1/N of N backends?
│     └── yes → group 5xx by upstream addr → one backend
│           ├── different image digest → failed rollout on that node → redeploy
│           ├── disk full / clock / DNS / dependency firewall on that node → fix node
│           └── health check too shallow (didn't notice) → deepen it
└── rare, random, low traffic, no single backend → keep-alive race → backend idle timeout > proxy's
```

**Fix & verify**

Take the bad replica out of rotation while you fix the node:

```bash
# Swarm: move tasks off web03 (check the other nodes have capacity first)
docker node update --availability drain web03
docker service ps app-web-3k2j1 --filter desired-state=running --format '{{.Name}} {{.Node}}'
for i in $(seq 1 100); do curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/health; done | sort | uniq -c
```

Equivalents: Nginx `server 10.0.1.17:8000 down;` in the upstream block plus
reload; Apache `balancer-manager` "Disabled"; ALB deregister the target. In
Kubernetes, a failing readiness probe removes the pod from the Service by
itself; that is why readiness probes exist.

> ⚠️ Draining a node moves **all** its tasks, including stateful ones pinned
> there. Check what runs on it (`docker node ps web03`) before draining.

**Rollback**

`docker node update --availability active web03` once the node is fixed (Swarm
does not move tasks back by itself; `docker service update --force SERVICE`
rebalances).

**Prevent it next time**

- Log the upstream address for every request (Nginx `$upstream_addr`, Traefik access log).
- Health checks that exercise dependencies, so a replica that cannot reach the DB leaves the pool on its own.
- Alert per node on disk, clock sync and failed units, not only on the service as a whole.

---

## 8. HTTP behaviour scenarios

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), area "HTTP", and [Web servers & proxies](29-learn-webservers-proxies.md) · 2) KodeKloud: *Nginx For Beginners*: Intermediate Config (URL redirect/rewrite, Reverse Proxy) ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 3) Docs: [Traefik documentation](https://doc.traefik.io/traefik/) · 4) Practice: Section 12 #12 and #13.

### 8.1 404 from Traefik vs 404 from the app

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Traefik in depth" · 2) KodeKloud: *Kubernetes Networking Deep Dive*: Kubernetes Ingress → Demo: Traefik Installation, which includes the access log ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Demo-Traefik-Installation/page)) · 3) Video: Christian Lempa *Is this the BEST Reverse Proxy for Docker? // Traefik Tutorial* ([YouTube](https://www.youtube.com/watch?v=wLrmmh1eI94); v2-era syntax, same concepts) · 4) Practice: the [Traefik Docker quick start](https://doc.traefik.io/traefik/getting-started/docker/) with a deliberately wrong `Host()` rule, then route your Apache sites as in [Deployment patterns](35-deployment-patterns.md).

**Level:** [L2 · Mid].

**Symptom:** the site, or one path, returns 404. Two completely different
problems produce it: Traefik found **no router**, or the app has **no route**.

**Step 1 — Fingerprint the 404**

**Goal:** find out who said 404.

```bash
curl -s -D - https://app.example.com/dashboard | head -n 8
```

```
HTTP/2 404
content-type: text/plain; charset=utf-8
x-content-type-options: nosniff
content-length: 19

404 page not found
```

**What it means:** a 19-byte plain-text `404 page not found` with no app
headers or cookies is Traefik's built-in answer: **no router matched** this
Host, path and entrypoint. An app 404 looks like the app: HTML in its layout,
a JSON error body, its cookies and headers. Apache and Nginx 404s carry their
`Server` header.

**Why this step (now):** the two cases are fixed in different places (Traefik
config vs app or path mapping). The body tells you which in one request.

**Next step:** Traefik 404 → Step 2. App 404 → Step 3.

**Step 2 — Find the router that should have matched**

**Goal:** compare the request with the routing rules Traefik actually has.

```bash
# Dokploy applications: routers live in the file provider directory
sudo grep -rn 'Host(' /etc/dokploy/traefik/dynamic/ | grep -i 'example.com'
# Compose apps: routers come from container labels (read at deploy time only)
docker inspect --format '{{json .Config.Labels}}' CONTAINER | tr ',' '\n' | grep -E 'rule|entrypoints|enable'
# Each entrypoint separately
curl -s -o /dev/null -w 'http  %{http_code}\n' -H 'Host: app.example.com' http://127.0.0.1/
curl -s -o /dev/null -w 'https %{http_code}\n' --resolve app.example.com:443:127.0.0.1 https://app.example.com/
# Traefik's own complaints about routers
docker logs --since 1h dokploy-traefik 2>&1 | grep -iE 'rule|router|does not exist' | tail -n 5
```

```
"traefik.http.routers.app.rule":"Host(`www.app.example.com`)"
"traefik.http.routers.app.entrypoints":"websecure"
http  404
https 404
```

**What it means:** the container's labels still route only
`www.app.example.com`. Someone added `app.example.com` in Dokploy but did not
redeploy, so the labels never changed. Other common findings:

- a typo in `Host(...)`, or a `PathPrefix` that does not cover the path;
- a router only on `websecure` while the request came over `web` (or the other way round);
- the container excluded: unhealthy, `traefik.enable=false`, or `exposedByDefault=false` without `traefik.enable=true`;
- a Traefik error such as `error while parsing rule` or `the service ... does not exist`, which disables that router;
- an Apache site after the 81/444 move: Apache still serves it on 81, but no Traefik router exists for its name yet, so Traefik answers 404 (and the default certificate on HTTPS). Add a router per Apache hostname ([Deployment patterns](35-deployment-patterns.md), Step 10).

**Why this step (now):** Traefik's 404 means "no rule matched". The only way
forward is to compare the request with the rules Traefik has, not the ones you
think it has.

**Next step:** fix the rule, redeploy, verify. If the rule matches and you still
get Traefik's 404, check Traefik's log for errors on that router.

**Step 3 — An app 404: compare the path the app received**

**Goal:** find out whether the proxy changed the path on the way.

```bash
docker logs --since 10m CONTAINER 2>&1 | grep ' 404 ' | tail -n 3
grep -RnE 'ProxyPass|ProxyPassReverse' /etc/apache2/sites-enabled/
```

```
10.0.1.4 - - [03/Oct/2026:11:58:02 +0000] "GET /dashboard HTTP/1.1" 404 179 "-" "curl/8.5.0"
/etc/apache2/sites-enabled/app-ssl.conf:12:    ProxyPass /app/ http://127.0.0.1:8000/
```

**What it means:** the user requested `/app/dashboard`; the app received
`/dashboard`. The proxy strips the prefix (Apache `ProxyPass /app/ .../`,
Traefik `StripPrefix`), but the app expects to live under `/app`, or the other
way round. Trailing slashes matter: `ProxyPass /app http://127.0.0.1:8000`
and `ProxyPass /app/ http://127.0.0.1:8000/` behave differently.

**Why this step (now):** the app's access log shows the path **after** the
proxy rewrote it, which is the only one that matters for the app's routing.

**Next step:** align the prefix: strip it in the proxy and tell the app its
base path (for example Django `FORCE_SCRIPT_NAME`), or do not strip it.

**Decision tree**

```
404
├── body "404 page not found", text/plain, no app headers → Traefik: no router matched
│     ├── labels/file don't contain this Host → add domain + REDEPLOY (labels read at deploy)
│     ├── works on https, 404 on http (or reverse) → entrypoint mismatch / missing redirect
│     ├── container excluded (unhealthy, enable=false) → fix health / labels
│     └── Traefik log "error while parsing rule" → fix rule syntax
├── Apache/Nginx 404 (Server header) → wrong vhost/server_name or DocumentRoot → apache2ctl -S / nginx -T
└── app-styled 404 → compare requested path vs path in app log → prefix stripping / base path
```

**Fix & verify**

```bash
# After correcting the domain in Dokploy (or the rule label), redeploy, then:
docker inspect --format '{{json .Config.Labels}}' CONTAINER | tr ',' '\n' | grep rule
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/dashboard
```

**Rollback**

Redeploy the previous configuration (Dokploy deployment history, or the
previous compose file from Git).

**Prevent it next time**

- After every domain change in Dokploy: redeploy, then verify with `curl` on both `http://` and `https://`.
- Keep routing rules in Git (compose files, dynamic YAML) and review them like code.
- Reference: [Traefik docs: Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

### 8.2 Redirect loop behind a TLS-terminating proxy

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Reverse proxy fundamentals" · 2) KodeKloud: *Nginx For Beginners*: Intermediate Config → Reverse Proxy ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) and the URL redirect/rewrite lesson · 3) Read: [What is a reverse proxy?](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/) · 4) Practice: Section 12 #12, then the redirect step in [Deployment patterns](35-deployment-patterns.md).

**Level:** [L2 · Mid].

**Symptom:** browsers show `ERR_TOO_MANY_REDIRECTS`; curl prints
`curl: (47) Maximum (50) redirects followed`. Typical right after putting an
app behind Traefik, an ALB, or Apache in front of Traefik during a migration.

**Step 1 — Watch the loop**

**Goal:** see where each redirect points.

```bash
curl -sIL --max-redirs 5 https://app.example.com/ 2>&1 | grep -iE '^(HTTP|location)|curl:'
```

```
HTTP/2 301
location: https://app.example.com/
HTTP/2 301
location: https://app.example.com/
HTTP/2 301
location: https://app.example.com/
curl: (47) Maximum (5) redirects followed
```

**What it means:** `https://app.example.com/` redirects to **itself**. The
app's "force HTTPS" logic believes the request arrived over plain HTTP. It
did: TLS ended at the proxy, which talked HTTP to the app and did not tell
it, through `X-Forwarded-Proto: https`, that the client used HTTPS (or the app
does not trust the header).

**Why this step (now):** the `location` values tell you which kind of loop it
is: same URL (scheme confusion), alternating http/https (two layers fighting),
or `www` ↔ apex (two canonical-host rules).

**Next step:** same-URL loop → Step 2.

**Step 2 — See what the app actually receives**

**Goal:** check the forwarded headers on the hop between proxy and app.

```bash
# App on loopback, plain HTTP: read the request headers on the wire
# (-l line-buffers tcpdump; without it the pipe holds the output back)
sudo tcpdump -lni lo -A -s0 'tcp dst port 8000' | grep -iE 'GET /|^(Host|X-Forwarded)'
# App in a container: capture in its namespace
docker run --rm --net container:CONTAINER nicolaka/netshoot tcpdump -ni eth0 -A -s0 'tcp dst port 8000'
```

```
E..x..@.@...........P.......GET / HTTP/1.1
Host: app.example.com
X-Forwarded-For: 192.0.2.50
X-Forwarded-Proto: http
```

The dots before `GET` are the IP and TCP headers, which `-A` prints as text.

**What it means:** the app receives `X-Forwarded-Proto: http`. In the
migration setup (Apache terminates TLS on 443 and forwards to Traefik on
`127.0.0.1:8081`), Traefik does not trust Apache, so it **overwrites** the
header with what it saw itself: plain HTTP. With a single proxy, a missing
header means the proxy does not set it.

**Why this step (now):** the capture shows the header the app really
receives, as opposed to the one the config suggests it should, and that
decides which layer to fix.

**Next step:** fix the header chain (Fix & verify).

**Decision tree**

```
redirect loop
├── location = same https URL → app thinks it's HTTP
│     ├── header missing at app → proxy must set X-Forwarded-Proto
│     ├── header "http" at app → an inner proxy overwrote it → trust the outer proxy (Traefik trustedIPs)
│     └── header "https" at app → app doesn't trust it → framework/gunicorn proxy settings
├── location alternates http ↔ https → two layers redirecting in opposite directions → remove one
└── location alternates www ↔ apex → two canonical-host rules → keep one
```

**Fix & verify**

Each layer has one job:

| Layer | Setting |
|---|---|
| Apache terminating TLS | `RequestHeader set X-Forwarded-Proto "https"` in the `:443` vhost (`sudo a2enmod headers`) |
| Nginx | `proxy_set_header X-Forwarded-Proto $scheme;` |
| Traefik behind another proxy | `entryPoints.web.forwardedHeaders.trustedIPs`: the address Traefik sees the outer proxy connect **from**; through a published port that is usually the Docker bridge gateway, for example `172.18.0.1/32` (check `ClientHost` in Traefik's access log) |
| gunicorn | honours forwarded headers only from `--forwarded-allow-ips` (default `127.0.0.1,::1`, or the `FORWARDED_ALLOW_IPS` environment variable); behind Traefik in Docker, set it to Traefik's network range |
| Django | `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` |
| Laravel | the `TrustProxies` middleware / trusted proxies setting |
| Express | `app.set('trust proxy', ...)` |
| WordPress | in `wp-config.php`, set `$_SERVER['HTTPS'] = 'on'` when `HTTP_X_FORWARDED_PROTO` is `https` |

```bash
curl -sIL http://app.example.com/ | grep -iE '^(HTTP|location)'
```

```
HTTP/1.1 301 Moved Permanently
location: https://app.example.com/
HTTP/2 200
```

One redirect from http to https, then 200: correct.

**Rollback**

Revert the header or trust setting you changed and reload that layer. Browsers
cache 301s: test with curl, or a private window, before concluding that a
rollback did not work.

**Prevent it next time**

- Trust forwarded headers only from known proxy addresses, never from everyone (clients can forge them).
- Put HTTP→HTTPS redirection in exactly one layer (the edge proxy), not in both proxy and app.
- Document the proxy chain for each site: who terminates TLS, who sets which header.

### 8.3 413 Request Entity Too Large

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Nginx in depth" (quick refresher) · 2) KodeKloud: *Nginx For Beginners*: Install & Config and Intermediate Config sections ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 3) Note: [Docker: registries and Harbor](30-learn-docker.md) for `docker push` through a proxy · 4) Practice: Section 12 #13 (`client_max_body_size 1k;`).

**Level:** [L1 · Junior].

**Symptom:** uploads above a certain size fail with `413 Request Entity Too
Large` (or `413 Content Too Large`). Small uploads work. A classic with
`docker push` to a registry such as Harbor behind an extra reverse proxy.

**Step 1 — Find out which layer rejects the body**

**Goal:** identify the responder and its log line.

```bash
head -c 20M /dev/urandom > /tmp/upload-test.bin
curl -s -o /dev/null -D - -F 'file=@/tmp/upload-test.bin' https://app.example.com/upload | head -n 3
sudo grep 'too large body' /var/log/nginx/error.log | tail -n 1
rm /tmp/upload-test.bin
```

```
HTTP/1.1 413 Request Entity Too Large
Server: nginx/1.24.0 (Ubuntu)
2026/10/03 11:50:02 [error] 2211#2211: *301 client intended to send too large body: 20971720 bytes, client: 192.0.2.50, server: app.example.com, request: "POST /upload HTTP/1.1", host: "app.example.com"
```

**What it means:** Nginx rejected the request before the app saw it, because
of `client_max_body_size` (default **1 MB**). The log line gives the size the
client tried to send.

**Why this step (now):** several layers have body limits, and only the first
one to reject answers. You raise **that** one, then test again to find the next.

**Next step:** Step 2.

**Step 2 — List every body limit on the path**

**Goal:** fix the whole chain in one go instead of one limit per incident.

```bash
sudo nginx -T 2>/dev/null | grep -n client_max_body_size                    # nothing printed = the 1 MB default
grep -RnE '^\s*LimitRequestBody' /etc/apache2/ 2>/dev/null                   # Apache, if it is on the path
grep -nE '^(upload_max_filesize|post_max_size)' /etc/php/8.3/fpm/php.ini      # PHP apps (Ubuntu 22.04: 8.1)
sudo grep -rn maxRequestBodyBytes /etc/dokploy/traefik/ 2>/dev/null         # Traefik buffering middleware
```

```
$ sudo nginx -T 2>/dev/null | grep -n client_max_body_size
$ grep -nE '^(upload_max_filesize|post_max_size)' /etc/php/8.3/fpm/php.ini
698:post_max_size = 8M
850:upload_max_filesize = 2M
```

**What it means:** Nginx sets no limit, so its 1 MB default applies, and
behind it PHP accepts only 2 MB files in an 8 MB request. Raise Nginx alone
and the 20 MB upload passes Nginx, then PHP drops the file without a 413.
The defaults per layer:

| Layer | Setting | Default |
|---|---|---|
| Nginx | `client_max_body_size` (http, server or location) | 1 MB |
| ingress-nginx (Kubernetes) | annotation `nginx.ingress.kubernetes.io/proxy-body-size` | 1 MB |
| Apache | `LimitRequestBody` | 1 GiB since 2.4.54 (unlimited before) |
| Traefik | `buffering` middleware `maxRequestBodyBytes` | no limit; but v3 `readTimeout` 60 s cuts slow uploads |
| PHP | `upload_max_filesize`, `post_max_size` | 2 MB, 8 MB (no 413: the file is silently missing) |
| Django | `DATA_UPLOAD_MAX_MEMORY_SIZE` (non-file data) | 2.5 MB → 400 |
| Registries (Harbor) behind your proxy | outer proxy must allow large layers | set `client_max_body_size 0;` (unlimited) on the outer Nginx |

The effective limit is the smallest one on the path.

**Why this step (now):** raising only Nginx often moves the failure to PHP's
silent limit, which is harder to see.

**Next step:** raise each limit to the agreed maximum (Fix & verify).

**Decision tree**

```
413
├── Server: nginx → client_max_body_size (server/location) → raise, nginx -t, reload
├── Server: Apache → LimitRequestBody
├── no Server header (Traefik) → buffering middleware limit
├── upload "succeeds" but file missing → PHP upload_max_filesize / post_max_size
└── slow large upload dies at 60 s through Traefik v3 → entrypoint readTimeout, not size
```

**Fix & verify**

```bash
sudo cp /etc/nginx/sites-available/app.conf /root/app.conf.bak
# in the server { } block for app.example.com:   client_max_body_size 100m;
sudoedit /etc/nginx/sites-available/app.conf
sudo nginx -t && sudo systemctl reload nginx
head -c 50M /dev/urandom > /tmp/upload-test.bin
curl -s -o /dev/null -w '%{http_code}\n' -F 'file=@/tmp/upload-test.bin' https://app.example.com/upload
rm /tmp/upload-test.bin
```

**Rollback**

`sudo cp /root/app.conf.bak /etc/nginx/sites-available/app.conf && sudo nginx -t && sudo systemctl reload nginx`.

**Prevent it next time**

- Agree on a maximum upload size per app and set it in **every** layer at deploy time.
- Keep limits as small as the app needs: a large body limit on every endpoint makes request floods cheaper.

### 8.4 WebSockets failing behind a proxy

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), area "HTTP" (hop-by-hop headers, the HTTP/1.1 upgrade) · 2) KodeKloud: *Nginx For Beginners*: Intermediate Config → Reverse Proxy ([notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) · 3) Docs: [Nginx documentation](https://nginx.org/en/docs/) and [Apache 2.4 documentation](https://httpd.apache.org/docs/2.4/) (KodeKloud has no WebSocket-proxy lesson) · 4) Practice: on the KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)), proxy a small WebSocket echo app through Nginx, remove the `Upgrade` headers, and watch the 400.

**Level:** [L2 · Mid].

**Symptom:** the browser console shows `WebSocket connection to
'wss://app.example.com/ws' failed`; live features (chat, notifications,
dashboards) do not update; or the connection works and drops after exactly
60 seconds.

**Step 1 — Test the upgrade handshake**

**Goal:** see whether the `Upgrade` reaches the app and comes back as 101.

```bash
curl -sv --http1.1 -o /dev/null --max-time 5 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==' \
  https://app.example.com/ws 2>&1 | grep -iE '^< (HTTP|upgrade|connection)'
# Same against the app directly, on the server:
curl -sv --http1.1 -o /dev/null --max-time 5 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==' \
  http://127.0.0.1:3000/ws 2>&1 | grep -iE '^< (HTTP|upgrade|connection)'
```

```
< HTTP/1.1 400 Bad Request
< HTTP/1.1 101 Switching Protocols
< Upgrade: websocket
< Connection: Upgrade
```

**What it means:** directly, the app answers `101 Switching Protocols`: it
supports WebSockets. Through the proxy you get 400: the proxy dropped the
`Upgrade` / `Connection` headers (they are hop-by-hop and are **not** forwarded
unless configured), so the app received a broken handshake. A 200 with HTML
means the proxy served the request as plain HTTP. `--http1.1` matters: the
classic upgrade does not exist in HTTP/2. After a 101, curl waits on the open
connection until `--max-time`, so an exit code 28 here is expected.

**Why this step (now):** comparing through-proxy with direct is the bypass
ladder again: it proves the proxy is the layer that breaks the upgrade.

**Next step:** fix the proxy (Fix & verify). Connection drops at 60 s → idle
timeouts (same section). Works with one replica, fails with several → sticky sessions.

**Decision tree**

```
WebSocket fails
├── direct to app: no 101 → app/route problem (path, auth, origin check)
└── direct 101, via proxy not 101
    ├── Nginx → proxy_http_version 1.1 + Upgrade/Connection headers (map)
    ├── Apache → mod_proxy_wstunnel, or ProxyPass ... upgrade=websocket (2.4.47+)
    └── Traefik → works natively → check middlewares, entrypoint, path rule
connects, then drops at 60 s → proxy_read_timeout / ALB idle timeout → raise, or app pings < timeout
works with 1 replica, fails with N → Socket.IO polling handshake needs sticky sessions
```

**Fix & verify**

Nginx:

```
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
server {
    # ...
    location /ws {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
```

Apache (the `map` block above goes in the `http` context of Nginx; for Apache
use one of these instead):

```
# Option 1, Apache 2.4.47+ (Ubuntu 22.04 and 24.04 qualify):
ProxyPass        /ws  http://127.0.0.1:3000/ws upgrade=websocket
ProxyPassReverse /ws  http://127.0.0.1:3000/ws
# Option 2, older Apache: sudo a2enmod proxy_wstunnel
ProxyPass        /ws  ws://127.0.0.1:3000/ws
```

Traefik needs nothing special for WebSockets. For several replicas with
Socket.IO, add a sticky cookie:
`traefik.http.services.NAME.loadbalancer.sticky.cookie=true`.

```bash
sudo nginx -t && sudo systemctl reload nginx          # or: sudo apache2ctl configtest && sudo systemctl reload apache2
curl -sv --http1.1 -o /dev/null --max-time 5 -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==' \
  https://app.example.com/ws 2>&1 | grep '^< HTTP'      # 101
```

**Rollback**

Restore the previous vhost / server block from backup, test, reload.

**Prevent it next time**

- Include the WebSocket block in your proxy templates for any app that uses it.
- Make the app send pings more often than the shortest idle timeout on the path.

---

## 9. Config and change scenarios

> 📚 **Study path:** 1) Note: [Case study: Apache 443 and Dokploy](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md) · 2) KodeKloud: *Fundamentals of SRE*: Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 3) Practice: Section 12 #14, then a timed rollback drill on a test VM.

### 9.1 Apache won't start after a config change

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md), area "Apache httpd in depth", and [Services & systemd](07-services-systemd.md) (quick refresher) · 2) KodeKloud: *DevOps Pre-Requisite Course*: Web Server → Apache Web Server and its lab ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · 3) KodeKloud: *Learning Linux Basics Course & Labs*: Service Management with SYSTEMD → SYSTEMD Tools ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) · 4) Practice: Section 12 #14, then replay your own 81/444 move from [Deployment patterns](35-deployment-patterns.md).

**Level:** [L1 · Junior].

**Symptom:** `sudo systemctl restart apache2` fails: `Job for apache2.service
failed because the control process exited with error code`. Every site on the
box is now down, not only the one you edited.

**Step 1 — Test the configuration**

**Goal:** find syntax and module errors with file and line number.

```bash
sudo apache2ctl configtest
```

```
AH00526: Syntax error on line 14 of /etc/apache2/sites-enabled/app-ssl.conf:
Invalid command 'ProxyPass', perhaps misspelled or defined by a module not included in the server configuration
Action 'configtest' failed.
The Apache error log may have more information.
```

**What it means:** `ProxyPass` belongs to `mod_proxy`, which is not enabled,
so the fix is `sudo a2enmod proxy proxy_http`. Other frequent `AH00526`
messages: `SSLCertificateFile: file '...' does not exist or is empty`, `Cannot
define multiple Listeners on the same IP:port`, and `Invalid command
'RequestHeader'` (`a2enmod headers`). The warning `AH00558: Could not reliably
determine the server's fully qualified domain name` is harmless.

**Why this step (now):** it is read-only, takes a second, and names file and
line. Most failed starts after an edit are found here.

**Next step:** `Syntax OK` but Apache still will not start → Step 2.

**Step 2 — Read the start-up error**

**Goal:** get the runtime error that configtest cannot see.

```bash
systemctl status apache2 --no-pager -l
journalctl -u apache2 -b --no-pager -n 30
```

```
× apache2.service - The Apache HTTP Server
     Active: failed (Result: exit-code) since Sat 2026-10-03 12:01:10 UTC; 8s ago
Oct 03 12:01:10 web01 apachectl[3011]: (98)Address already in use: AH00072: make_sock: could not bind to address [::]:443
Oct 03 12:01:10 web01 apachectl[3011]: (98)Address already in use: AH00072: make_sock: could not bind to address 0.0.0.0:443
Oct 03 12:01:10 web01 apachectl[3011]: no listening sockets available, shutting down
Oct 03 12:01:10 web01 apachectl[3011]: AH00015: Unable to open logs
Oct 03 12:01:10 web01 systemd[1]: apache2.service: Control process exited, code=exited, status=1/FAILURE
```

**What it means:** `AH00072 make_sock: could not bind to address ...:443` with
`(98)Address already in use`: another process owns 443, so Apache cannot open
its socket and exits. `AH00015: Unable to open logs` is a side effect.
Other start-time errors: `AH02565: Certificate and private key ... do not match`
(the key does not belong to the certificate; compare moduli as in
[Web, HTTP & TLS](18-web-http-tls.md)) and permission errors on key files.

**Why this step (now):** configtest only checks syntax. Ports, certificate and
key pairs and file permissions are only checked when Apache really starts,
and the journal records that attempt.

**Next step:** `AH00072` → Step 3. Certificate and key mismatch → point to the matching pair.

**Step 3 — Find who holds the port, and why Apache still asks for it**

**Goal:** resolve the port conflict properly.

```bash
sudo ss -ltnp 'sport = :443'
grep -RnE '^\s*Listen' /etc/apache2/ports.conf /etc/apache2/sites-enabled/
sudo apache2ctl -M 2>/dev/null | grep -i ssl
```

```
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*     users:(("docker-proxy",pid=2817,fd=7))
/etc/apache2/ports.conf:5:Listen 80
/etc/apache2/ports.conf:8:	Listen 443
/etc/apache2/ports.conf:12:	Listen 443
 ssl_module (shared)
```

**What it means:** Traefik (via `docker-proxy`) owns 443, which is the
Dokploy setup from [the case study](21-case-apache-443-dokploy.md). Apache still
asks for 443 because Ubuntu's `ports.conf` contains `Listen 443` inside
`<IfModule ssl_module>`, and `mod_ssl` is still enabled, even if no SSL vhost
remains. The same race happens at **boot**: whichever starts first gets 443,
and the loser fails (Traefik exits, §5.1, or Apache fails, this scenario).

**Why this step (now):** fixing the conflict means deciding who owns 443 for
good. Stopping one of them by hand only lasts until the next reboot.

**Next step:** move Apache off 80/443 for good (Fix & verify) and let Traefik
route the remaining Apache sites to it.

**Decision tree**

```
Apache won't start
├── apache2ctl configtest fails → file:line in AH00526
│     ├── Invalid command X → a2enmod the module that provides X
│     ├── SSLCertificateFile missing → fix path / install cert
│     └── multiple Listeners → duplicate Listen lines
└── Syntax OK, start fails → journalctl -u apache2
      ├── AH00072 (98) Address already in use → ss -ltnp: who owns the port?
      │     ├── docker-proxy / Traefik → move Apache to :8080 on an address Traefik can reach (+ drop Listen 443)
      │     └── old apache2 / nginx process → stop the stray one properly
      ├── AH02565 key/cert mismatch → right key file for that cert
      └── permission denied on key/log → ownership/permissions
```

**Fix & verify**

Move Apache off 80/443, to a port the Traefik container can reach, and let
Traefik front it:

```bash
sudo cp -a /etc/apache2 /root/apache2-backup-$(date +%F-%H%M)
sudoedit /etc/apache2/ports.conf                      # Listen 192.0.2.10:8080; remove the Listen 443 lines
sudo sed -i 's/<VirtualHost \*:80>/<VirtualHost *:8080>/' /etc/apache2/sites-available/*.conf
sudo a2dismod ssl                                     # only if no site still terminates TLS in Apache
sudo apache2ctl configtest
sudo systemctl restart apache2                        # restart, not reload: the listening sockets change
sudo ss -ltnp | grep apache2                          # 192.0.2.10:8080 only
# Allow 8080 only from the Docker bridge Traefik's traffic comes from
# (traffic to the host itself goes through INPUT, so ufw does apply here)
docker network inspect docker_gwbridge -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
sudo ufw allow proto tcp from 172.18.0.0/16 to any port 8080
```

Then route the remaining Apache sites through Traefik: a dynamic file with a
router per hostname and a service with `url: http://192.0.2.10:8080`. Do not
use `127.0.0.1` there: inside the Traefik container it is Traefik itself. The
full walk-through is in [the case study](21-case-apache-443-dokploy.md).

**The 81/444 variant (what you did).** Moving Apache to `Listen 81` and
`Listen 444` instead of 8080 fixes this scenario the same way: Apache no longer
asks for 80/443, so it starts. Two checks keep it fixed after a reboot:
`grep -RnE '^\s*Listen' /etc/apache2/ports.conf` shows only 81 and 444, and
no enabled vhost still says `<VirtualHost *:443>`. Then finish the job (Traefik
routes, certificate renewal, closing 81 and 444 from outside) with
[Deployment patterns](35-deployment-patterns.md).

**Rollback**

```bash
sudo mv /etc/apache2 /etc/apache2.failed-$(date +%F-%H%M)     # keep the broken config for comparison
sudo cp -a /root/apache2-backup-YYYY-MM-DD-HHMM /etc/apache2
sudo apache2ctl configtest && sudo systemctl restart apache2
sudo ufw delete allow proto tcp from 172.18.0.0/16 to any port 8080
```

> ⚠️ The rollback only works while 443 is free. If Traefik still holds it,
> Apache with the old config fails exactly like before. Decide the owner of 443
> first. The broken configuration stays in `/etc/apache2.failed-DATE` for
> comparison; nothing is deleted in a hurry.

**Prevent it next time**

- Always `sudo apache2ctl configtest && sudo systemctl reload apache2`. A **reload** (graceful) checks the config first and keeps the running server on the old config if the new one is broken. A **restart** stops Apache first, so a broken config means a full outage.
- Keep `/etc/apache2` under version control (`etckeeper` or a Git repo) so every change has a diff and an undo.
- Write down which service owns 80, 443 and 3000 on each host, and make sure only that service is configured for them (see [Ports inventory](22-playbook-ports-inventory.md)).

### 9.2 Site down right after a change: roll back first

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE*: Managing Complexity, Risk and Toil → Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 2) Note: [Deployment patterns](35-deployment-patterns.md) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for rollback plans · 3) Swarm: *Docker Certified Associate*: Docker Swarm → Scaling, Rolling Updates and Rollbacks ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) Practice: deploy a broken image as a Swarm service on the KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)) and recover with `docker service rollback`.

**Level:** [L2 · Mid] to roll back; [L3 · Senior] to write the change request and rollback plan before the change.

**Symptom:** the site broke shortly after a deploy, config edit, package
upgrade, DNS edit, certificate swap or firewall change. Assume the change
caused it until proven otherwise.

**Step 1 — Establish what changed and when**

**Goal:** build a short timeline of changes before the first error.

```bash
journalctl --since '2 hours ago' -p warning --no-pager | tail -n 30
grep -E '^(Start-Date|Commandline|Upgrade)' /var/log/apt/history.log | tail -n 6
sudo find /etc -xdev -type f -mmin -120 -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort | tail -n 15
docker service ps APP_SERVICE --format '{{.Name}} {{.Image}} {{.CurrentState}}' | head -n 4
last -n 5
```

```
Start-Date: 2026-10-03  10:05:12
Commandline: apt-get -y upgrade
Upgrade: apache2:amd64 (2.4.58-1ubuntu8.7, 2.4.58-1ubuntu8.8), php8.3-fpm:amd64 (...)
2026-10-03 10:41 /etc/apache2/sites-available/app-ssl.conf
app-web-3k2j1.1 harbor.example.com/apps/web:4f2c9e1 Running 25 minutes ago
app-web-3k2j1.1 harbor.example.com/apps/web:9a7d210 Shutdown 25 minutes ago
```

**What it means:** three candidates: an `apt upgrade` at 10:05, an edit of
`app-ssl.conf` at 10:41, and a new image `4f2c9e1` deployed 25 minutes ago.
Compare with the time the errors started (Step 0, monitoring, the first user
report). The change closest **before** the first error is the prime suspect.

**Why this step (now):** you cannot roll back what you have not identified.
Two minutes of timeline-building beats an hour of layer-walking when the cause
is a change someone made at 10:41.

**Next step:** Step 2. Roll back the prime suspect.

**Step 2 — Roll back first, diagnose second**

**Goal:** restore service using a known-good state.

| Change | Rollback |
|---|---|
| Apache / Nginx config | restore backup → `configtest` / `nginx -t` → `reload` |
| Dokploy deploy | redeploy the previous deployment or commit (or Dokploy's rollback feature if enabled) |
| Swarm service update | `docker service rollback APP_SERVICE` |
| Kubernetes Deployment | `kubectl rollout undo deployment/APP -n NAMESPACE` |
| DNS record | restore the old record (remember the TTL, §4.3) |
| Firewall rule | `sudo ufw delete RULE` / restore the saved ruleset |
| Certificate swap | point back at the previous files, reload |
| Package upgrade | last resort: `sudo apt install PACKAGE=OLD_VERSION` (see `apt-cache policy PACKAGE`) |

```bash
docker service rollback app-web-3k2j1
docker service ps app-web-3k2j1 --format '{{.Name}} {{.Image}} {{.CurrentState}}' | head -n 2
```

```
app-web-3k2j1
overall progress: rolling back update: 1 out of 1 tasks
verify: Service app-web-3k2j1 converged
app-web-3k2j1.1 harbor.example.com/apps/web:9a7d210 Running 6 seconds ago
```

**What it means:** the service is back on the previous image `9a7d210`.

**Why this step (now):** the change is the most likely cause, and rolling it
back is a known path to a known-good state. Users get their service back while
you investigate without time pressure. This is the SRE rule "stabilise first,
find the root cause second". The exception: a change that cannot be reversed
safely (an irreversible database migration). Then a forward fix may be safer;
decide that **before** the change, in its rollback plan.

**Next step:** Step 3.

**Step 3 — Verify recovery and keep the evidence**

**Goal:** prove the rollback fixed it, and keep what you need to find out why.

```bash
for i in $(seq 1 50); do curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/; done | sort | uniq -c
docker service logs --since 1h app-web-3k2j1 > ~/incident-2026-10-03-app-web.log 2>&1
```

**What it means:** 50 × 200 means recovery. The saved logs from the failed
version are your evidence for the diagnosis (diff the images, the configs and
the environment between `9a7d210` and `4f2c9e1` on staging).

**Why this step (now):** "it seems fine" is not verification. The same probe
you used to detect the outage confirms the recovery.

**Next step:** post an update (Section 10), then diagnose the change offline.

**Decision tree**

```
broken right after a change
├── list changes in the last 2 h (apt history, /etc mtime, deploys, DNS, FW, certs)
├── one candidate → roll it back → verified? → yes: diagnose offline
│                                            └── no: roll back the next candidate / layered walk
├── several candidates → roll back the most recent & riskiest first, one at a time
└── rollback impossible/riskier (DB migration) → forward fix (plan this BEFORE changing)
```

**Fix & verify**

The rollback **is** the fix for the incident. The real fix (correcting the
change) goes through review and is deployed again later, with verification and
a tested rollback.

**Rollback**

Rolling the rollback forward again is a new change. Treat it as one.

**Prevent it next time**

- Write a change request for risky changes: what, why, steps, how to verify, and how to roll back (the ops ladder's GitLab change management drill).
- Back up config before editing (`cp -a`), or better, keep `/etc` in Git with `etckeeper`.
- Validate configs in CI (`apache2ctl -t`, `nginx -t`, `docker compose config`) before they reach a server.
- Deploy to one node or a canary first; watch error rates for 10 minutes before continuing.
- Reference: [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/).

---

## 10. Communicating during an outage

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE*: Incident Management (Preparing for Incidents, roles, Blameless Postmortem Culture, Root Cause Analysis) ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page)) · 2) Read: [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 3) Note: [Senior architecture & leadership](39-learn-senior-architecture.md) and [Career ladder](40-career-ladder.md) · 4) Practice: write the three updates below for your last real incident, then a five-line note.

**Level:** [L2 · Mid] posts clear updates; [L3 · Senior] and [L4 · Lead] run the incident and the postmortem.

Technical skill fixes the outage; communication decides whether people trust
you during it. Juniors go silent and type; seniors post a two-line update
first, then type.

### Stabilise before root cause

Your priorities, in order:

1. **Stop the bleeding.** Roll back the last change, fail over, scale up, block an abusive client, or serve a maintenance page. Any safe action that restores service comes before understanding why.
2. **Restore and verify** with the same probe that detected the problem (Step 0, or the 100-request loop from §7.4).
3. **Find the root cause** once users are no longer waiting.

The one thing to do **before** a stabilising action that destroys evidence
(a restart, a redeploy, a rollback): spend 60 seconds saving it.

```bash
INC=~/incident-$(date +%F-%H%M); mkdir -p "$INC"
sudo journalctl --since '1 hour ago' --no-pager > "$INC/journal.txt"
sudo cp /var/log/apache2/error.log /var/log/nginx/error.log "$INC/" 2>/dev/null
docker logs --since 1h dokploy-traefik > "$INC/traefik.log" 2>&1
docker ps -a > "$INC/docker-ps.txt"; sudo ss -ltnp > "$INC/listeners.txt"; ss -s > "$INC/ss-summary.txt"
script -a "$INC/terminal.log"          # records everything you type and see from now on; exit with Ctrl-D
```

### Roles, even in a team of two

| Role | Job |
|---|---|
| Incident lead | decides what to try next and when to roll back; keeps the timeline |
| Hands on keyboard | runs the commands, reports findings to the lead |
| Communicator | posts updates to users and stakeholders on schedule |

Alone, you are lead and hands; ask a colleague or your manager to take
communication. Nobody can type commands and write good updates at the same time.

### What to say, and when

Send the first message within about 10 minutes, even if you know almost
nothing. Every message says what is affected, since when, what you are doing
and when the next update comes.

```
[INCIDENT] app.example.com returns errors (502) for all users since 10:38 UTC.
Impact: customers cannot log in or place orders. shop.example.com and legacy.example.com are fine.
Status: investigating. A deploy at 10:35 UTC is the main suspect.
Next update: 11:00 UTC or sooner.  Lead: ONCALL_NAME  Channel: #inc-2026-10-03-app
```

```
[UPDATE 11:00] We rolled back the 10:35 deploy at 10:52. Errors stopped at 10:54.
Monitoring for 30 minutes. No action needed from users.
Next update: 11:30 UTC.
```

```
[RESOLVED 11:30] app.example.com has worked normally since 10:54 UTC (16 minutes of errors).
Cause: the new release was missing a database setting. The fixed release will be deployed after review.
A short incident review will follow by Tuesday.
```

Rules that keep trust:

- Facts, not guesses. "We don't know yet" is a valid status; a wrong cause announced early is hard to take back.
- Times in UTC (or with an explicit time zone), impact in user terms ("cannot log in"), never internal jargon ("Traefik router").
- Always give the next update time, and keep it, even if the update is "no change".
- No blame, not even of yourself. Describe what happened, not who did it.

### Timeline notes

Keep a running log while you work. It costs seconds per line and turns into
the postmortem timeline for free:

```
10:38  Alert: probe https://app.example.com/ → 502
10:40  curl -v: 502 from Traefik (no Server header, body "Bad Gateway")
10:42  Traefik log: dial tcp 10.0.1.14:3000: connection refused
10:44  docker service ps: tasks exit 1; log: "Set the DATABASE_URL environment variable"
10:50  Decision: roll back to image 9a7d210 (deploy at 10:35 dropped an env var)
10:52  docker service rollback app-web-3k2j1
10:54  100/100 requests 200. Monitoring.
```

Note every change you make, with the time. When something odd happens at 10:47,
you need to know whether it was you.

### After the incident

- **Every incident, even small:** the five-line note from the ops ladder's weekly rhythm: the symptom, your first wrong guess, the evidence that settled it, the fix, and what you will check first next time.
- **Real outages:** a blameless postmortem: summary, impact, timeline, root cause, what went well, what went badly, and action items with owners and dates. Read [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/), then "Managing Incidents" and "Postmortem Culture" from the [table of contents](https://sre.google/sre-book/table-of-contents/).
- Turn the action items into prevention: the "Prevent it next time" lists in this module are where they usually come from.

---

## 11. Master decision tree

> 📚 **Study path:** 1) Note: the failure-signature table in Section 1 · 2) KodeKloud: *Linux Challenges* (free, timed) ([course](https://kodekloud.com/courses/linux-challenges)) · 3) Practice: [SadServers scenarios](https://sadservers.com/scenarios) tagged dns, nginx and ssl, using only this tree.

**Level:** [L2 · Mid].

Start at the top with the Step 0 probe and follow the first branch that
matches. Every leaf names a section of this module.

```
"THE SITE IS DOWN"
│
├─ Step 0: curl -sS -o /dev/null -w '%{http_code} %{remote_ip}\n' https://SITE/
│          + "what changed in the last 2 h?" ── yes, recent change → §9.2 roll back first
│
├─ curl (6) could not resolve host ─────────────────────► DNS
│     ├─ getent ahosts ≠ dig .......................... §4.2  /etc/hosts, nsswitch, .local, search domains
│     ├─ resolvectl: "No appropriate name servers" .... §4.1  netplan nameservers
│     ├─ resolvectl: "All attempts ... failed" ........ §4.1  tcpdump port 53, dig @each resolver
│     ├─ NXDOMAIN ..................................... §4.1  dig @authority: record / split horizon
│     ├─ resolves to the OLD IP ....................... §4.3  TTL, caches, negative caching
│     └─ slow / flaky lookups ......................... §4.4  resolvectl log-level debug
│
├─ curl (7) refused ────────────────────────────────────► LISTENER  §5.1
│     ├─ curl -v shows an unexpected IP ............... §4.3
│     ├─ ss -ltnp: nothing on the port ................ service down → Step 14; port clash → §9.1
│     └─ ss -ltnp: 127.0.0.1 only ..................... §5.3
│
├─ curl (28) timeout / "No route to host" ──────────────► PATH and FILTERS  §5.2
│     ├─ ip route get: wrong interface / docker0 ...... §5.2 Step 3
│     ├─ tcpdump on server: no SYN arrives ............ Step 9  SG, NACL, edge firewall, NAT
│     ├─ tcpdump: SYN in, nothing out ................. Step 8  ufw / nftables / firewalld
│     └─ ip neigh FAILED .............................. host / NIC / VLAN down
│
├─ curl (35) / (60) TLS ────────────────────────────────► TLS  §6
│     ├─ unable to get local issuer (code 20/21) ...... §6.1  chain or trust store
│     ├─ no alternative subject name matches .......... §6.2  SAN, vhost, SNI
│     ├─ expired / not yet valid ...................... §6.3  renewal, reload, clock
│     ├─ self-signed: TRAEFIK DEFAULT CERT ............ §6.4  router or ACME
│     └─ wrong version number ......................... Step 12  HTTPS to a plain-HTTP port
│
├─ curl (52) empty reply / (56) reset ──────────────────► APP died mid-request
│     ├─ container app bound to 127.0.0.1 ............. §5.3 Step 4
│     ├─ fixed time (30 s) ............................ §7.3
│     └─ random ....................................... §7.4 keep-alive race
│
└─ an HTTP status ── WHO answered? (Server header, body format: Section 3)
      ├─ 404 ........ Traefik plain text → router | app page → path ...... §8.1
      ├─ 301 loop ........................................................ §8.2  X-Forwarded-Proto
      ├─ 413 ............................................................. §8.3  body limits
      ├─ 400 / 426 on the WebSocket path ................................. §8.4  Upgrade headers
      ├─ 500 ............................................................. Step 14 app log, Step 16 dependencies
      ├─ 502 ............................................................. §7.1  proxy error log: refused / timeout / EOF
      ├─ 503 ............................................................. §7.2  capacity, health, retry window
      ├─ 504, or always dies at 30 / 60 s ................................ §7.3  timeout chain
      └─ only some requests fail ......................................... §7.4  one bad backend
```

When no branch fits: walk Section 2 from Step 0, one step at a time, and write
down each result. The step where the answer changes from "as expected" to
"not as expected" is your layer.

---

## 12. Practice: break it on purpose

> 📚 **Study path:** 1) Practice: the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) and Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)) for the table below · 2) KodeKloud: *Linux Challenges* ([course](https://kodekloud.com/courses/linux-challenges)) as a timed warm-up · 3) Note: [Career ladder](40-career-ladder.md) for where this exit test sits · 4) Record each break as a five-line incident note.

**Level:** [L2 · Mid] exit test; [L1 · Junior] can start with #1–#5.

The L2 exit test: someone breaks one thing on a test VM; within 15 minutes you
write one line: **"Broken layer: X. Evidence: Y."** (a capture line, a log
line or `curl -v` output). Reading this module does not prepare you for that;
breaking things does.

> ⚠️ Run these only on a **test VM** you can rebuild. Several of them break
> networking, time or the web server on purpose. Keep a console (Proxmox,
> VirtualBox, cloud serial console) open in case you lock yourself out of SSH.

| # | Break it (test VM only) | You should see | Practise |
|---|---|---|---|
| 1 | `sudo resolvectl dns ens18 192.0.2.250` (a dead resolver) | `curl: (6)` after a long pause | §4.1, §4.4 |
| 2 | add `192.0.2.99 app.example.com` to `/etc/hosts` | `dig` right, `curl` to the wrong IP | §4.2 |
| 3 | `sudo ufw deny 443/tcp` (keep SSH allowed) | `curl: (28)` timeout, SYN in tcpdump with no reply | §5.2, Step 8 |
| 4 | `sudo systemctl stop nginx` | `curl: (7)` refused, RST in tcpdump | §5.1 |
| 5 | run gunicorn without `--bind`, test from a second VM | refused remotely, fine locally | §5.3 |
| 6 | Compose app with a wrong `loadbalancer.server.port` label | Traefik 502, `connection refused` in its log | §7.1 |
| 7 | add `time.sleep(40)` to one view, gunicorn default timeout | 502 at exactly 30 s, `WORKER TIMEOUT` | §7.3 |
| 8 | in the php-fpm pool: `pm = ondemand`, `pm.max_children = 1`, `listen.backlog = 5`; then `ab -n 200 -c 50 https://app.example.com/` against a page that takes about a second | 503 with `AH02454` + `AH01079`, `max_children` warning | §7.2 |
| 9 | configure the leaf certificate without its intermediate | `curl: (60)`, `Verify return code: 21` | §6.1 |
| 10 | `sudo timedatectl set-ntp false; sudo date -s '2025-01-01'` (undo: `sudo timedatectl set-ntp true`) | `certificate is not yet valid` | §6.3 |
| 11 | Dokploy domain with an internal-only name and Let's Encrypt | `TRAEFIK DEFAULT CERT`, ACME error in the log | §6.4 |
| 12 | app forces HTTPS, proxy does not send `X-Forwarded-Proto` | `curl: (47)` redirect loop | §8.2 |
| 13 | `client_max_body_size 1k;` in Nginx | 413 on any form post | §8.3 |
| 14 | `sudo a2enmod ssl` while Traefik holds 443, then restart Apache | `AH00072 make_sock` | §9.1 |

For #8: with Ubuntu's default `pm = dynamic`, a `pm.max_children` below the
spare-server values makes php-fpm refuse to start (check with
`sudo php-fpm8.3 -t`), so use `ondemand`. The small `listen.backlog` makes the
socket queue overflow quickly; with the default of 511, extra requests only
queue and get slow instead of failing with 503.

Free practice from the ops ladder, all of it hands-on:

- [SadServers scenarios](https://sadservers.com/scenarios), tags dns, nginx, ssl: real broken servers against a timer.
- [badssl.com](https://badssl.com/): expired, wrong.host, self-signed, untrusted-root and incomplete-chain hosts for §6.
- [Mess With DNS](https://messwithdns.net/): a real subdomain with a live view of queries; do the negative-caching experiment for §4.3.
- [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) before you rely on Steps 3 and 7.
- [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) for the model behind Step 4.
- [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html) for Step 12.
- [Some things about getaddrinfo that surprised me](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/) and [Some ways DNS can break](https://jvns.ca/blog/2022/01/15/some-ways-dns-can-break/) for §4.
- [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) for §6.4, §7.1 and §8.1.

---

## 13. Quick reference by layer

> 📚 **Study path:** 1) Note: [Cheat sheet](19-cheatsheet.md) · 2) KodeKloud Notes ([notes.kodekloud.com](https://notes.kodekloud.com/)): search the lesson behind any command you cannot explain.

| Layer | Command | Good | Bad |
|---|---|---|---|
| DNS (app path) | `getent ahosts HOST` | expected IP | nothing (exit 2) / wrong IP |
| DNS (resolver) | `resolvectl query HOST` | IP, `Data from: network` | `All attempts ... failed`, `not found` |
| DNS (wire) | `sudo tcpdump -ni any port 53` | query out, answer in | query out, silence |
| Route | `ip route get IP` | expected `dev` / `via` | VPN, docker0, wrong NIC |
| Path | `mtr -rwn -c 50 IP` | 0 % at the last hop | loss persisting to the last hop |
| Port | `nc -vz -w 3 HOST PORT` | `succeeded!` | `refused` / `timed out` |
| Listener | `sudo ss -ltnp 'sport = :PORT'` | right process on `0.0.0.0` / `*` | nothing / `127.0.0.1` |
| Arrival | `sudo tcpdump -ni any 'tcp port PORT and host CLIENT'` | `[S]` in, `[S.]` out | no `[S]` / `[S]` with no reply / `[R.]` |
| Host firewall | `sudo ufw status verbose`; `journalctl -k` UFW BLOCK | rule allows | BLOCK lines for your flow |
| TLS | `openssl s_client -connect HOST:443 -servername HOST -showcerts` | `Verify return code: 0`, name in SAN | 19/20/21/10/9/18 |
| HTTP | `curl -v https://HOST/` | `< HTTP/2 200` | which `*` line is the last good one? |
| Bypass DNS | `curl -v --resolve HOST:443:IP https://HOST/` | works → DNS was the problem | fails → not DNS |
| Proxy | Apache / Nginx `error.log`, `docker logs dokploy-traefik` | no errors for your request | `AH01114`, `connect() failed (111)`, `dial tcp ... refused` |
| App | `systemctl status UNIT`, `docker service ps SERVICE` | running, stable | restart loop, exit 1 / 137 |
| App direct | `curl -sv http://127.0.0.1:APP_PORT/health` | 200 | refused, hang, 500 |
| Dependency | `pg_isready -h DB`, `redis-cli -h REDIS ping` | accepting / PONG | `no response`, `rejecting connections`, no PONG; a full server still says "accepting", so look for `too many clients` in the app log (Step 16) |

Related modules: [DNS](08-dns.md) · [Network](02-network.md) ·
[Web, HTTP & TLS](18-web-http-tls.md) · [Time & NTP](12-time-ntp.md) ·
[Services & systemd](07-services-systemd.md) · [Docker](14-docker-containers.md) ·
[AWS](16-aws-cloud.md) · [Case study: Apache 443 and Dokploy](21-case-apache-443-dokploy.md) ·
[Ports inventory](22-playbook-ports-inventory.md) · [Slow system](23-playbook-slow-system.md) ·
[Network speed](24-playbook-network-speed.md) · [Containers & Kubernetes](26-playbook-containers-k8s.md) ·
[Learn: networking, DNS, HTTP, TLS](28-learn-networking.md) ·
[Learn: web servers and proxies](29-learn-webservers-proxies.md) ·
[Roadmap](34-roadmap.md)

---

## 14. Self-check and exit test

> 📚 **Study path:** 1) Note: re-read the failure-signature table (Section 1) and the master decision tree (Section 11) · 2) KodeKloud: *Linux Challenges* (free, timed) as a warm-up ([course](https://kodekloud.com/courses/linux-challenges)) · 3) Practice: [SadServers scenarios](https://sadservers.com/scenarios) tagged dns, nginx and ssl · 4) Record every attempt as a five-line incident note.

**Level:** the questions are for every stage; the timed tasks are split by stage.

### Questions

Answer each one out loud before you read the short answer.

| # | Question | Short answer |
|---|---|---|
| 1 | curl says `Connection refused`. What does that prove about DNS, the route and the firewalls? | DNS resolved and a host answered with RST, so the path works. Nothing listens on that IP:PORT, or a REJECT rule answered (Section 1, §5.1). |
| 2 | curl says `Timeout was reached`. Where do you capture first, and what are the three patterns? | On the server. No SYN arrives: upstream drop. SYN with no reply: host firewall. SYN-ACK on the wrong interface: return route (Step 7, §5.2). |
| 3 | Why can `dig` and `getent ahosts` return different answers? Name two causes. | `getent` follows nsswitch, `dig` asks DNS directly. A stale `/etc/hosts` line, or `mdns4_minimal [NOTFOUND=return]` for `.local` names (§4.2). |
| 4 | `/etc/resolv.conf` says `nameserver 127.0.0.53`. How do you see the real upstream servers? | `resolvectl status`, per link (Step 2). |
| 5 | You changed an A record an hour ago and clients still reach the old IP. What do you compare first? | `dig @AUTHORITY NAME +norecurse` against your resolver: was it published, and how much TTL is left in which cache (§4.3)? |
| 6 | Why does `ufw deny 8081` not protect a published Docker port, and where do you filter instead? | Docker's DNAT sends the packet through FORWARD, not INPUT. Filter in `DOCKER-USER`, or publish on `127.0.0.1` only (Step 9). |
| 7 | `openssl s_client -showcerts` shows only certificate `0` and `Verify return code: 21`. Client or server problem? | Server: the intermediate is missing. Serve the full chain (§6.1). |
| 8 | Why test HTTPS with `--resolve` rather than `-H 'Host: ...'` against the IP? | With `-H` against `https://IP/`, curl sends no SNI at all (an IP is never sent as SNI) and checks the certificate against the IP, so the proxy picks its default certificate and the check fails. `--resolve` keeps SNI, Host and verification correct (Step 12). |
| 9 | How do you tell Traefik's 404 from the app's 404 in one request? | Traefik: a 19-byte plain-text `404 page not found` with no app headers. The app: its own layout, cookies or JSON (§8.1). |
| 10 | Requests always die at 30 s with a 502. What do you suspect, and how do you prove it? | gunicorn's `--timeout 30`. The same request fails when sent straight to the app, and its log shows `WORKER TIMEOUT` (§7.3). |
| 11 | You fixed the backend, and Apache still answers 503 for a minute. Why? | The worker is in its retry window after `AH00959` (`retry=60`). Wait, reload, or set `retry=0` (§7.2). |
| 12 | Why can't Traefik's route for an Apache site point at `http://127.0.0.1:81`? | Inside the Traefik container, 127.0.0.1 is Traefik itself. Use the host address Apache binds, allowed from the Docker bridge only (Step 6, §9.1). |
| 13 | Apache now listens on 81 and 444. Why will certbot renewals for the Apache names fail? | HTTP-01 always uses port 80 and TLS-ALPN-01 port 443, and both belong to Traefik. Let Traefik issue the certificates, or use DNS-01 (§6.3). |
| 14 | The site broke ten minutes after a deploy. What do you do first, and what just before it? | Save the evidence (60 seconds), then roll back. Diagnose afterwards (§9.2, Section 10). |
| 15 | What four things go into your first outage message? | What is affected, since when, what you are doing, and when the next update comes (Section 10). |

### Timed practical tasks

Do these on test VMs or a KodeKloud playground, never on production.

| Stage | Task | Time | Pass when |
|---|---|---|---|
| [L0 · Fresher] | On a VM with Nginx, run the Step 0 probe against three URLs: one working, one with Nginx stopped, one with a hostname that does not exist. Then explain every `*` line of one `curl -v` output. | 20 min | Each failure is labelled with its curl exit code and its layer. |
| [L1 · Junior] | A colleague breaks one of Section 12 #1–#5 without telling you which. Find it and fix it. | 15 min | One line "Broken layer: X. Evidence: Y." with the pasted capture, log line or curl output, and the fix verified with the Step 0 probe. |
| [L2 · Mid] | **The ops ladder's L2 exit test.** A colleague breaks anything from Section 12, or invents a new break. Walk the layers and name the broken one with evidence. Repeat with three different breaks. | 15 min each | Three correct one-liners with evidence. No guess, and no change made before the evidence was captured. |
| [L3 · Senior] | Take two scenarios you met this quarter and turn their "Prevent it next time" lists into code: an external HTTPS and certificate-expiry probe, explicit bind addresses, Docker address pools in `daemon.json`, `DOCKER-USER` rules in configuration management. | 2 h | A reviewer breaks the same thing on a test VM and an alert fires before a user would notice. |
| [L4 · Lead] | Run a game day: inject a Section 12 fault into staging without warning the on-call engineer, act as incident lead, post updates on the Section 10 schedule, then hold a blameless review. | 90 min plus review | A timeline, three updates and a postmortem with owned, dated action items exist within 48 hours. |

After each task, write the five-line incident note from the ops ladder:
symptom, first wrong guess, deciding evidence, fix, and what you will check
first next time. Keep the notes in a Git repository; they become portfolio
material (see [Career ladder](40-career-ladder.md)).

---

## 15. Where to go next

> 📚 **Study path:** 1) Note: [Career ladder](40-career-ladder.md), stage "Mid-level · L2 Troubleshooter" · 2) KodeKloud: *AWS Networking Fundamentals* to run this same walk in the cloud ([course](https://kodekloud.com/courses/aws-networking-fundamentals)) · 3) Practice: finish your 81/444 setup with [Deployment patterns](35-deployment-patterns.md) · 4) Then the L3 exit test in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

**Level:** [L2 · Mid] moving towards [L3 · Senior].

Go where this module showed you a gap:

| Gap | Read | Then |
|---|---|---|
| DNS (§4) | [DNS](08-dns.md), [Learn: networking](28-learn-networking.md) "DNS in depth" | KodeKloud *Demystifying DNS* |
| Packets, routes, firewalls (§5) | [Network](02-network.md), [Network speed playbook](24-playbook-network-speed.md) | LFCS Networking section, the tcpdump zine |
| Certificates and the private CA (§6) | [Web, HTTP & TLS](18-web-http-tls.md), [Security & DevSecOps](37-learn-security-devsecops.md) | every failure host on badssl.com |
| Apache, Nginx, Traefik, Dokploy (§7–§9) | [Web servers & proxies](29-learn-webservers-proxies.md), [Case study](21-case-apache-443-dokploy.md), [Deployment patterns](35-deployment-patterns.md) | route your Apache sites through Traefik |
| Containers and Swarm networks | [Containers & Kubernetes playbook](26-playbook-containers-k8s.md), [Learn: Docker](30-learn-docker.md) | DCA Docker Swarm section |
| "It is not down, it is slow" | [Slow system playbook](23-playbook-slow-system.md), [Performance & observability](32-learn-performance-observability.md) | the 60-second checklist drill |
| Database dependencies (Step 16) | [Databases for DevOps](38-learn-databases-ops.md) | a "too many connections" drill |
| The same walk on AWS | [Learn: cloud & AWS](36-learn-cloud-aws.md), [AWS](16-aws-cloud.md) | Route 53 → route tables → SG and NACL → ALB and ACM → target health |
| Kubernetes Ingress and Service outages | [Learn: Kubernetes](31-learn-kubernetes.md), [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) | the CKA Troubleshooting section |
| Leading incidents, designing them away | [Senior architecture & leadership](39-learn-senior-architecture.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) | KodeKloud *Fundamentals of SRE* |

**Next level.** Passing the L2 exit test with three different breaks in a row
means you are ready for L3 Platform. Its exit test is "GitLab CI builds, tags
with the commit SHA, pushes to Harbor, Dokploy deploys, rollback tested". The
plan is in the [Roadmap](34-roadmap.md) and the [Career ladder](40-career-ladder.md).
