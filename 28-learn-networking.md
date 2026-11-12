# 28 — Learn: Networking, DNS, HTTP & TLS

This is the networking course behind every "site is down", "it's slow" and
"connection refused" ticket. It goes from Ethernet frames up to TLS
certificates, one layer at a time. Each topic explains how the layer works,
shows it on a real Ubuntu server, has you break it on a test VM and fix it,
and lists the error text it produces when it fails in production. The
reference modules [Network](02-network.md), [DNS](08-dns.md) and
[Web, HTTP & TLS](18-web-http-tls.md) hold the command lists. This module
explains why those commands work, so you can tell which one to run next.

The Apache-on-443 incident that started this handbook comes up throughout.
Several layers were involved: which process owned the socket, which address it
was bound to, how Docker's NAT publishes a port, which certificate Traefik
serves and why Let's Encrypt needs port 80. You'll be able to explain all of
it by the end. You solved that clash by moving Apache to ports 81 and 444 so
that Traefik could take 80 and 443. Section 6 shows why that works at the
socket level, and [Deployment patterns](35-deployment-patterns.md) shows how
to finish the job with Traefik routing.

**Who it serves, fresher to senior.** A **Fresher** [L0] learns the layers,
addresses and subnetting (sections 1–3). A **Junior** [L1] learns routing,
ports, NAT, firewalls and the basics of DNS and HTTP. A **Mid-level**
engineer [L2] learns the core of this module: name the broken layer with
evidence, using TCP states, DNS resolver paths, proxy headers, TLS chains,
tcpdump and strace. A **Senior** [L3] designs address plans, overlays, VPNs,
MTU, mTLS and load-balancing choices. A **Lead** [L4] runs the layered walk
for others during incidents and turns each one into a monitored check. The
table in section 0 maps each stage to its sections, and every topic carries
a **Level** tag such as [L2 · Mid].

> All sample outputs are illustrative (Ubuntu 22.04/24.04 unless noted) and use
> documentation addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24,
> 2001:db8::/32) or private ranges. UPPERCASE words in commands (HOST, PORT,
> DOMAIN, CONTAINER, IFACE) are placeholders. Every lab is for a **test VM
> only**. Never run the "break it" steps on a server people depend on.

---

## 0. How to use this module

### Who this module is for

Networking shows up at every career stage. What changes is how deep you go
and who relies on your answer. Find your stage, do its sections first, and
use section 16 to decide when you've passed it. The stage names match the
[career ladder](40-career-ladder.md) used across the handbook.

| Career stage | Ops Ladder | What to master in this module | Sections |
|---|---|---|---|
| Fresher (0–1 yr) | L0 Foundations | OSI/TCP-IP vocabulary, `ip -br addr` and `ip route`, MAC vs IP, subnetting by hand, what `127.0.0.1` and `0.0.0.0` mean | 1, 2 (Ethernet), 3 |
| Junior (1–2 yrs) | L1 Operator | ARP, routing tables, TCP vs UDP, ports and bind addresses, refused vs timed out, SNAT, ufw, DNS records, HTTP status codes, reading a certificate with openssl | 2, 4, 5, 6 (first two topics), 7 (ufw), 8 and 9 (first two topics each) |
| Mid-level (2–4 yrs) | L2 Troubleshooter | Name the broken layer with evidence: TCP states, retransmissions, conntrack, Docker vs UFW, the resolver path, proxy headers, TLS chains and private CAs, ACME, 502/503/504, IPv6, tcpdump and strace | 6–11, 13, 14, 15 |
| Senior (4–7 yrs) | L3 Platform | Design and change safely: address plans without overlaps, policy routing, mTLS and certificate lifecycles, L4 vs L7, overlays, WireGuard and MTU, DNS and TLS cut-over plans | 3 (planning), 4, 10, 11, 12 |
| Senior/Lead (5+ yrs) | L4 SRE | Run the layered walk for others during incidents, turn each incident into a monitored check (certificate expiry, conntrack fill, DNS latency), teach the drills | 15, 16, and the playbooks linked from each topic |

You already work at about L1–L2: you found and solved the Apache/Dokploy
port clash yourself. Skim sections 1–3, answer the Fresher and Junior
questions in section 16 to confirm, then spend your real hours on sections
6–10 and 14–15. That's where the L2 exit test lives.

### Learning path

Work through the sections in this order. The level tags match the Ops Ladder
(L0 Foundations, L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE) and
the career stages above (Fresher, Junior, Mid, Senior, Lead). If you're short
on time, cover the L1 items quickly and put your hours into L2.

| # | Topic | Section | Level · stage | Why now |
|---|---|---|---|---|
| 1 | Layers and which tool tests which layer | 1 | L0→L1 · Fresher | Everything else plugs into this map |
| 2 | Ethernet, MAC, ARP, switches, VLANs | 2 | L0→L1 · Fresher | "Can I even reach the gateway?" |
| 3 | IPv4 addressing, CIDR, subnetting | 3 | L0 · Fresher | You read prefixes every day (Docker, K8s, VPNs) |
| 4 | Routing, default gateway, policy routing | 4 | L1→L2 · Junior | "Gateway answers, nothing beyond does" |
| 5 | TCP vs UDP, ports, sockets, bind addresses | 6 | L1 · Junior | The Apache/Dokploy port clash lives here |
| 6 | TCP handshake, states, RST vs timeout | 6 | L2 · Mid | Reading `ss` output and refused vs timed out |
| 7 | Retransmissions, windows, BDP | 6 | L2 · Mid | Why a fast link gives slow transfers |
| 8 | NAT: SNAT, masquerade, DNAT | 5 | L1→L2 · Junior | How Docker publishes ports and why it bypasses UFW |
| 9 | Firewalls: netfilter, nftables, ufw, conntrack, Docker chains | 7 | L1→L2 · Junior→Mid | Timed-out connections, "UFW doesn't block my container" |
| 10 | DNS in depth | 8 | L1→L2 · Junior→Mid | "It's always DNS": resolver path, caches, containers |
| 11 | HTTP | 9 | L1→L2 · Junior→Mid | Which component produced this 502? |
| 12 | TLS and certificates | 10 | L2 · Mid | Harbor private CA, Traefik certs, Let's Encrypt |
| 13 | Load balancing and health checks | 11 | L2→L3 · Mid→Senior | Traefik, K8s Services, 503s |
| 14 | Packet capture and syscall tracing | 14 | L2 · Mid | Look at the layer directly instead of guessing |
| 15 | IPv6 essentials | 13 | L2 · Mid | Dual-stack surprises, `*:443` in `ss` |
| 16 | VPNs, overlays and MTU | 12 | L3 · Senior | WireGuard, Docker Swarm overlay, Calico/Flannel |
| 17 | One request, every layer | 15 | L2 exit · Mid | The "site is down" walk, end to end |

> Packet capture is listed late in the reading order, but start using
> `tcpdump` from section 2 onward. Every lab below includes a capture line,
> and the earlier it becomes a habit, the better.

### Study method

Do these five steps for every topic:

1. **Read this note.** Read the concept and key terms, then run the "See it on
   a real system" commands on your own machine. They are all read-only.
2. **KodeKloud course or lesson.** Each section starts with a 📚 Study path
   line that points to the matching KodeKloud course and lesson. Do the lesson
   and its built-in lab.
3. **Optional video.** Only when the concept still feels fuzzy. One good
   explanation is enough; don't binge.
4. **Hands-on lab.** Build it, break it on purpose, then diagnose it from
   evidence *before* you fix it. Write down the exact error text you saw.
   That text is what you'll search for later in an incident.
5. **Related playbook.** Read the playbook linked under "How it breaks"
   ([network speed](24-playbook-network-speed.md),
   [site down](25-playbook-site-down.md),
   [ports inventory](22-playbook-ports-inventory.md),
   [containers and Kubernetes](26-playbook-containers-k8s.md)) so you know
   which runbook to open when this failure happens at work.

Free resources from your Ops Ladder that fit this module:
[Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/)
(sections 2–5), [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/)
and [Spying on your programs with strace](https://wizardzines.com/zines/strace/)
(section 14), [Mess With DNS](https://messwithdns.net/) (section 8),
[badssl.com](https://badssl.com/) (section 10) and
[everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html)
(sections 9–10).

**KodeKloud spine for this module.** The 📚 line at the top of each section
names the exact lesson. Across the whole module, the courses come in this
order:

1. *Networks and Communications* ([course](https://kodekloud.com/courses/networks-and-communications)):
   only if switching and routing feel shaky. About one hour.
2. *DevOps Pre-Requisite Course* ([course](https://kodekloud.com/courses/devops-pre-requisite-course)):
   Networking Basics, DNS, Web Server (IPs and Ports) and Security (SSL & TLS
   Basics). Sections 1–4, 6, 9 and 10.
3. *Prep Course - Linux Foundation Certified System Administrator (LFCS)*
   ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)):
   the Networking section (network services, packet filtering, port
   redirection and NAT, reverse proxies and load balancers) and Essential
   Commands → Work With SSL Certificates. Sections 4–7, 10 and 11.
4. *Demystifying DNS* ([course](https://kodekloud.com/courses/demystifying-dns)):
   section 8.
5. *Docker Certified Associate* ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)):
   Publishing Ports, Networking Deep Dive and Docker Overlay Network.
   Sections 5, 12 and 14.
6. *Certified Kubernetes Administrator (CKA)* ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)):
   the Networking prerequisites, CoreDNS and TLS Basics, when you reach the
   Kubernetes parts of sections 8, 10 and 12.

KodeKloud has nothing on tcpdump, strace, `getent` vs `dig`, systemd-resolved
debugging or MTU. Those sections point at the free Ops Ladder resources
above instead. For brand-new topics the study path starts with KodeKloud.
For topics that are a quick refresher for you (HTTP, the final walk) it
starts with the handbook note.

### Build your lab once

You need one Ubuntu 24.04 (or 22.04) VM with 2 vCPU, 2 GB RAM and a snapshot.
Take a snapshot before every lab and revert it afterwards. Install the tools:

```bash
# Ubuntu / Debian lab VM
sudo apt update
sudo apt install -y iproute2 iputils-ping iputils-arping iputils-tracepath \
  traceroute mtr-tiny dnsutils tcpdump tshark netcat-openbsd curl openssl \
  conntrack nftables iperf3 ipcalc ethtool strace wireguard-tools
# tshark asks "Should non-superusers be able to capture packets?"  -> No is fine (use sudo)
# iperf3 asks whether to start a daemon automatically                -> No
# The tc netem labs (section 6) need the sch_netem module. If tc says
# "Error: Specified qdisc kind is unknown", install the extra kernel modules:
#   sudo apt install -y linux-modules-extra-$(uname -r)

# RHEL / Rocky equivalent (ipcalc there is a different program with different flags)
sudo dnf install -y iproute iputils bind-utils tcpdump wireshark-cli nmap-ncat curl \
  openssl conntrack-tools nftables iperf3 ipcalc ethtool strace wireguard-tools traceroute mtr
```

Most labs use **network namespaces**. A namespace is a separate network stack
(its own interfaces, routes, firewall and sockets) inside the same kernel.
Three of them joined by virtual cables (veth pairs) give you a client, a
router and a server without needing three VMs. Docker and Kubernetes build
container networking from these same parts, so the practice carries over
directly.

```
   netns "client"                 netns "router"                    netns "server"
 ┌────────────────┐   veth   ┌────────────────────────────┐  veth  ┌────────────────┐
 │ c-eth0         ├──────────┤ r-eth0            r-eth1   ├────────┤ s-eth0         │
 │ 10.10.1.10/24  │          │ 10.10.1.1/24  10.10.2.1/24 │        │ 10.10.2.20/24  │
 │ gw 10.10.1.1   │          │ ip_forward=1               │        │ gw 10.10.2.1   │
 └────────────────┘          └────────────────────────────┘        └────────────────┘
```

Save this script once and reuse it in every lab:

```bash
cat > ~/netlab.sh <<'EOF'
#!/usr/bin/env bash
# netlab.sh up|down  - client/router/server lab built from network namespaces
#   client 10.10.1.10/24 --- 10.10.1.1/24 [router] 10.10.2.1/24 --- 10.10.2.20/24 server
set -euo pipefail
case "${1:-}" in
  up)
    for ns in client router server; do
      ip netns add "$ns"
      ip -n "$ns" link set lo up
    done
    ip link add c-eth0 netns client type veth peer name r-eth0 netns router
    ip link add s-eth0 netns server type veth peer name r-eth1 netns router
    ip -n client addr add 10.10.1.10/24 dev c-eth0
    ip -n router addr add 10.10.1.1/24  dev r-eth0
    ip -n router addr add 10.10.2.1/24  dev r-eth1
    ip -n server addr add 10.10.2.20/24 dev s-eth0
    ip -n client link set c-eth0 up
    ip -n router link set r-eth0 up
    ip -n router link set r-eth1 up
    ip -n server link set s-eth0 up
    ip -n client route add default via 10.10.1.1
    ip -n server route add default via 10.10.2.1
    ip netns exec router sysctl -qw net.ipv4.ip_forward=1
    echo "lab up - test with: sudo ip netns exec client ping -c2 10.10.2.20"
    ;;
  down)
    for ns in client router server; do ip netns del "$ns" 2>/dev/null || true; done
    echo "lab removed"
    ;;
  *) echo "usage: sudo $0 up|down"; exit 1 ;;
esac
EOF
chmod +x ~/netlab.sh
sudo ~/netlab.sh up
sudo ip netns exec client ping -c2 10.10.2.20     # should succeed
```

Two commands do most of the work in the labs:

- `sudo ip -n NS ...` runs an `ip` subcommand inside namespace NS.
- `sudo ip netns exec NS COMMAND` runs any program (ping, curl, tcpdump,
  python3, nft) inside it.

> Names don't resolve inside the lab namespaces. They share the host's
> `/etc/resolv.conf`, which points to 127.0.0.53, and that address is the
> *host's* loopback, not the namespace's. Use IP addresses in the labs. If you
> do want DNS in a namespace, `ip netns exec` bind-mounts
> `/etc/netns/NS/resolv.conf` over `/etc/resolv.conf` when that file exists.

Reset everything at any time with `sudo ~/netlab.sh down && sudo ~/netlab.sh up`.
Namespaces don't survive a reboot.

### Conventions in this module

- **Concept** starts in plain language, then gets precise.
- **See it on a real system** commands are read-only. They're safe on
  production, though `tcpdump` and `ss -p` need sudo.
- **Hands-on lab** has numbered phases: build, break, diagnose, fix. Diagnose
  first, every time, before you look at the fix.
- **How it breaks** maps an error text to the first command to run and the
  playbook to open.

---

## 1. Layers and the tools that test them

> 📚 **Study path:** 1) KodeKloud: *Networks and Communications* — protocols (TCP/IP, HTTP) and Network Troubleshooting ([course](https://kodekloud.com/courses/networks-and-communications)) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → *Troubleshooting* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 3) Note: this section, then [Network reference](02-network.md) · 4) Read: [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) · 5) Practice: the five-break drill below in the netns lab, or on the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)).

### The OSI and TCP/IP models

**Level:** [L0 · Fresher] · the vocabulary every later section uses.

**Concept.** Networking is built in layers. Each layer does one job and relies
on the layer below it. An HTTP request doesn't care whether it travels over
Wi-Fi or fibre. TCP doesn't care what's in the HTTP request. The practical
value of the model is that **a failure lives at one layer, and every layer
has its own test**. If you can prove layers 1–4 work, stop looking at the
network and look at TLS or the application.

The OSI model has 7 layers. The internet actually uses the 4-layer TCP/IP
model. Engineers still speak in OSI numbers ("an L4 load balancer", "an L7
proxy"), so learn both:

```
 OSI layer         TCP/IP layer      Unit (PDU)   Examples                         Address
 7 Application  ┐
 6 Presentation ├─ Application       message      HTTP, DNS, TLS*, SSH, SMTP        URL, hostname
 5 Session      ┘
 4 Transport    ── Transport         segment/     TCP, UDP, QUIC                    port
                                     datagram
 3 Network      ── Internet          packet       IPv4, IPv6, ICMP                  IP address
 2 Data link    ┐                    frame        Ethernet, 802.1Q VLAN, ARP, Wi-Fi MAC address
 1 Physical     ┘─ Link              bits         copper, fibre, radio, veth        -

 * TLS sits between TCP and HTTP. People call it L6, "L4.5" or just "part of L7".
```

**Encapsulation.** On the way out, each layer wraps the data from the layer
above in its own header. On the way in, each layer strips its header off and
hands the rest up. That's why a capture shows MAC, IP, TCP and HTTP stacked in
one frame:

```
 ┌──────────────┬──────────────┬──────────────┬──────────────────────────┬─────┐
 │ Ethernet hdr │ IP header    │ TCP header   │ HTTP request (payload)   │ FCS │
 │ dst/src MAC  │ src/dst IP   │ src/dst port │ GET / HTTP/1.1           │     │
 │ 14 bytes     │ 20 bytes     │ 20-60 bytes  │ Host: app.example.com    │  4  │
 └──────────────┴──────────────┴──────────────┴──────────────────────────┴─────┘
                 └──────── IP packet: at most MTU bytes (1500 on Ethernet) ─────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| PDU | Protocol data unit: frame (L2), packet (L3), segment (TCP) or datagram (UDP) |
| Header / payload | Control information the layer adds / the data it carries |
| MTU | Largest IP packet a link carries without fragmenting (1500 on Ethernet) |
| MSS | Largest TCP payload in one segment (MTU − IP − TCP headers, usually 1460) |
| Hop | One router the packet crosses. TTL drops by one at each hop |
| Control plane / data plane | Deciding where traffic goes (routing tables, ARP) / actually moving it |

**See it on a real system**

```bash
ip -br link            # L1/L2: is the interface up, does it have carrier, what is its MAC
ip -br addr            # L3: which IP addresses this host owns
ip route               # L3: where packets go
sudo ss -ltnp          # L4: which processes listen on which TCP ports
curl -sv -o /dev/null https://example.com   # L4 + TLS + L7 in one go
```

```
$ ip -br link
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
ens18            UP             bc:24:11:4a:2b:1c <BROADCAST,MULTICAST,UP,LOWER_UP>
docker0          DOWN           02:42:9c:1e:5a:0b <NO-CARRIER,BROADCAST,MULTICAST,UP>

$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
ens18            UP             192.0.2.10/24 fe80::be24:11ff:fe4a:2b1c/64
docker0          DOWN           172.17.0.1/16
```

- `ens18 UP ... LOWER_UP` means the interface is administratively up (`UP`)
  *and* has carrier (`LOWER_UP`). L1 and L2 are fine.
- `docker0 DOWN ... NO-CARRIER` is normal. The default bridge has no carrier
  until a container joins it.
- `192.0.2.10/24` means this host's address is 192.0.2.10, and every address
  in 192.0.2.0–255 is directly reachable without a router (section 3).

**Hands-on lab (test VM only)**: see encapsulation with your own eyes.

```bash
# 1. Build: start the lab
sudo ~/netlab.sh up

# 2. Watch: capture on the router's client-side interface with link-layer headers (-e)
sudo ip netns exec router tcpdump -ni r-eth0 -e -c 4 icmp or arp
# (second terminal)
sudo ip netns exec client ping -c 1 10.10.2.20

# 3. Read each line: MAC addresses (L2) -> IP addresses (L3) -> ICMP (the payload)
```

```
12:01:10.100201 5a:3c:11:22:33:44 > ff:ff:ff:ff:ff:ff, ethertype ARP (0x0806), length 42: Request who-has 10.10.1.1 tell 10.10.1.10, length 28
12:01:10.100230 9e:1d:44:55:66:77 > 5a:3c:11:22:33:44, ethertype ARP (0x0806), length 42: Reply 10.10.1.1 is-at 9e:1d:44:55:66:77, length 28
12:01:10.100251 5a:3c:11:22:33:44 > 9e:1d:44:55:66:77, ethertype IPv4 (0x0800), length 98: 10.10.1.10 > 10.10.2.20: ICMP echo request, id 4242, seq 1, length 64
12:01:10.100390 9e:1d:44:55:66:77 > 5a:3c:11:22:33:44, ethertype IPv4 (0x0800), length 98: 10.10.2.20 > 10.10.1.10: ICMP echo reply, id 4242, seq 1, length 64
```

- The destination **IP** is the server (10.10.2.20), but the destination
  **MAC** is the router's. A frame only ever travels one hop. The IP header
  carries the end-to-end address. Section 2 builds on this.

**How it breaks**: you'll name the layer in every incident, so learn what each
layer's failure looks like:

| Layer | Typical evidence | First command |
|---|---|---|
| L1/L2 | `NO-CARRIER`, `state DOWN`, gateway in `ip neigh` shows `FAILED` | `ip -br link`, `ip neigh` |
| L3 | `Network is unreachable`, `No route to host`, ping times out | `ip route get IP` |
| L4 | `Connection refused`, `Connection timed out` | `sudo ss -ltnp`, `nc -zv HOST PORT` |
| DNS (L7) | `Could not resolve host` | `getent ahosts HOST` |
| TLS | `SSL certificate problem`, `handshake failure` | `openssl s_client -connect HOST:443 -servername HOST` |
| HTTP (L7) | `502`, `503`, `404 page not found` | `curl -v`, proxy and app logs |

**Why it matters for troubleshooting:** "The site is down" tells you nothing
about which layer failed. Naming the layer from evidence ("TCP connects, TLS
fails with an unknown CA") cuts the search space down to one layer and tells
the next person what to look at.

**Next step:** learn which concrete tool answers each layer's question. That's
the next topic, and it's the table you'll use most.

### Which tool tests which layer

**Level:** [L1 · Junior] for the table and the five-break drill · [L2 · Mid] for choosing top-down vs bottom-up under pressure.

**Concept.** Every layer has a yes/no question and a tool that answers it
directly. You can troubleshoot bottom-up (link, then IP, then TCP, then app)
or top-down from one `curl -v` that shows how far it got. Seniors start with
`curl -v` because it covers DNS, TCP, TLS and HTTP in one shot, then drop to
the layer where the output stopped.

| Layer | Question | Tool | Success looks like | Failure looks like |
|---|---|---|---|---|
| L1 | Is there a link? | `ip -br link`, `ethtool IFACE` | `UP ... LOWER_UP`, `Link detected: yes` | `NO-CARRIER`, `Link detected: no` |
| L2 | Can I reach my gateway's MAC? | `ip neigh`, `arping -I IFACE GW` | gateway `REACHABLE`/`STALE` with lladdr | `FAILED`, `INCOMPLETE`, no ARP reply |
| L3 | Do I have an address and a route? | `ip -br addr`, `ip route get IP` | `via GW dev IFACE src MYIP` | `Network is unreachable` |
| L3 | Do packets get there and back? | `ping`, `mtr -n`, `tracepath -n` | replies, 0% loss | timeouts, loss to the last hop |
| L3 | Does the path take a full-size packet? | `ping -M do -s 1472 HOST`, `tracepath` | replies | `Frag needed`, `message too long` |
| L4 | Is something listening? | `sudo ss -ltnp` (server side) | `LISTEN ... users:(("proc",...))` | nothing on that port, or bound to 127.0.0.1 |
| L4 | Can I open a TCP connection? | `nc -zv -w3 HOST PORT` | `succeeded!` | `refused` (RST) or `timed out` (drop) |
| L4 | What is actually on the wire? | `sudo tcpdump -ni any port PORT` | SYN, SYN-ACK, ACK | SYN with no answer, or RST |
| L7 DNS | What does the app resolve? | `getent ahosts NAME`, `resolvectl query NAME` | expected IP | NXDOMAIN, timeout, wrong IP |
| L7 DNS | What does the DNS server say? | `dig NAME`, `dig @SERVER NAME` | `status: NOERROR` + answer | `NXDOMAIN`, `SERVFAIL`, timeout |
| TLS | Is the certificate right? | `openssl s_client -connect H:443 -servername H` | `Verify return code: 0 (ok)` | `unable to get local issuer`, expired, wrong name |
| L7 HTTP | What does the server answer? | `curl -v`, `curl --resolve`, `curl -H 'Host: ...'` | expected status and body | 4xx/5xx, redirect loop |
| Syscall | What does the program really do? | `strace -f -e trace=openat,connect CMD` | files and addresses you expect | wrong config file, wrong IP, `ECONNREFUSED` |

**Key terms**

| Term | Meaning |
|---|---|
| Bottom-up | Prove L1, then L2, L3 and so on. Slow but thorough. Best when nothing works at all |
| Top-down | Start with `curl -v` and go down from where it stopped. Fast. Best when something works |
| Divide and conquer | Test the middle layer first (for example `nc -zv`) and halve the search space |
| Bypass test | Skip a layer on purpose (`curl --resolve`, `-H 'Host:'`, `127.0.0.1:PORT`) to prove the rest works |

**See it on a real system**: read one `curl -v` as a layer checklist.

```bash
curl -v https://app.example.com/health 2>&1 | grep -E '^\*|^< HTTP'
```

```
* Host app.example.com:443 was resolved.               <- DNS ok
* IPv4: 203.0.113.10
*   Trying 203.0.113.10:443...
* Connected to app.example.com (203.0.113.10) port 443 <- L3 + L4 ok (handshake done)
* ALPN: curl offers h2,http/1.1
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256 / X25519 / RSASSA-PSS
* ALPN: server accepted h2
* Server certificate:
*  subject: CN=app.example.com
*  SSL certificate verify ok.                          <- TLS ok
< HTTP/2 502                                           <- the HTTP layer answered: proxy says upstream broke
```

- DNS, TCP and TLS all succeeded, so the network is fine. A 502 means the
  proxy (Traefik, Nginx, Apache) couldn't get a good answer from the app
  behind it. Go straight to the proxy logs ([site down playbook](25-playbook-site-down.md)).

**Hands-on lab (test VM only)**: the five-break drill. Each break leaves
different evidence. For each one, run only the evidence commands and name the
layer before you read the comment.

```bash
# 0. Build: lab up, plus a web server in the server namespace (second terminal)
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20
# baseline from the client:
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code}\n' http://10.10.2.20/   # 200

# Evidence commands (run after each break):
sudo ip netns exec client curl -sv -m 5 http://10.10.2.20/ -o /dev/null
sudo ip netns exec client ip route get 10.10.2.20
sudo ip -n client neigh

# Break A (L1): pull the virtual cable
sudo ip -n router link set r-eth0 down
#   -> client's c-eth0 loses carrier (NO-CARRIER); ip neigh shows 10.10.1.1 FAILED/INCOMPLETE;
#      curl fails after ~3 s with "No route to host" (ARP for the gateway failed) or times out. Fix:
sudo ip -n router link set r-eth0 up

# Break B (L3): remove the client's default route
sudo ip -n client route del default
#   -> curl: "Immediate connect fail ... Network is unreachable". Fix:
sudo ip -n client route add default via 10.10.1.1

# Break C (L3 forwarding): router stops forwarding
sudo ip netns exec router sysctl -w net.ipv4.ip_forward=0
#   -> curl times out; route and neigh look fine. Capture on r-eth1 shows nothing leaving. Fix:
sudo ip netns exec router sysctl -w net.ipv4.ip_forward=1

# Break D (L4 firewall drop): router drops TCP/80 silently
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd tcp dport 80 drop
#   -> curl "Connection timed out" but ping works. Fix:
sudo ip netns exec router nft delete table inet lab

# Break E (L4 service): stop the python server (Ctrl+C in its terminal)
#   -> curl "Connection refused" instantly: the path is fine, nothing listens.
```

**How it breaks**: the drill above *is* the list. Memorise the pairs.
"Network is unreachable" is a local routing problem. "Timed out" means
something dropped the packet on the way. "Refused" means the packet arrived
and nothing was listening. Full walk: [site down playbook](25-playbook-site-down.md).

**Why it matters for troubleshooting:** In the Apache incident you had to work
out "which application is on which port" by searching for commands one at a
time. With this table you know that question is L4 on the server side, so the
tool is `ss -ltnp` and nothing else ([ports inventory playbook](22-playbook-ports-inventory.md)).

**Next step:** start at the bottom. Layer 2 explains why a host must find
the gateway's MAC address before anything else works.

---

## 2. Layer 2: Ethernet, ARP, switches, VLANs

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics → *Networking Basics*, then *Labs – Switching and Routing* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page)) · 2) Read: [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) (ARP, MAC tables, switches) · 3) Note: this section, then `ip link` and `ip neigh` in [Network reference](02-network.md) · 4) Practice: the ARP and VLAN labs below; Docker bridges come back in [Learn Docker](30-learn-docker.md).

### Ethernet frames and MAC addresses

**Level:** [L0 · Fresher] · read `ip link` and know what `UP` vs `LOWER_UP` means.

**Concept.** On a local network, machines don't send to IP addresses. They
send Ethernet **frames** to **MAC addresses**, the 48-bit hardware address of
a network card. A frame never leaves its local segment (the broadcast domain).
To reach anything further away, a host sends the frame to the **router's
MAC**, and the router builds a new frame for the next hop. The IP header stays
the same end to end; the Ethernet header is rewritten at every hop.

```
 client 192.0.2.50                router                         server 203.0.113.10
 MAC aa:aa..                 MAC bb:bb.. | MAC cc:cc..             MAC dd:dd..
     │  frame 1: dst MAC bb:bb  src MAC aa:aa                          │
     │           IP 192.0.2.50 -> 203.0.113.10  (unchanged)            │
     └──────────────────────────►│                                     │
                                 │  frame 2: dst MAC dd:dd src MAC cc:cc
                                 │           IP 192.0.2.50 -> 203.0.113.10
                                 └────────────────────────────────────►│
```

**Key terms**

| Term | Meaning |
|---|---|
| MAC address | 48 bits, written `bc:24:11:4a:2b:1c`. The first 3 bytes (OUI) identify the vendor |
| Locally administered | Second-lowest bit of the first byte is set (`02:..`, `06:..`, `0a:..`, `0e:..`). Used by VMs, veths and Docker containers (`02:42:..` up to Docker 27; random locally administered MACs from Docker 28) |
| Broadcast | `ff:ff:ff:ff:ff:ff`. Every host on the segment receives it (ARP requests use this) |
| Broadcast domain | The set of hosts that receive each other's broadcasts: one switch or VLAN |
| Carrier | Physical link signal. `LOWER_UP` in `ip link` means carrier is present |
| Ethertype | Field saying what's inside the frame: 0x0800 IPv4, 0x0806 ARP, 0x86dd IPv6, 0x8100 VLAN tag |

**See it on a real system**

```bash
ip link show ens18                  # MAC, MTU, state
ethtool ens18 | grep -E 'Speed|Duplex|Link detected'   # physical link (on VMs Speed may be "Unknown!")
ip -s link show ens18               # RX/TX counters: errors and drops
```

```
$ ip link show ens18
2: ens18: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether bc:24:11:4a:2b:1c brd ff:ff:ff:ff:ff:ff
    altname enp0s18
```

- `UP` means an admin set the interface up. `LOWER_UP` means there's carrier.
  `UP` without `LOWER_UP` means the cable, switch port or virtual NIC is
  disconnected.
- `mtu 1500` is standard Ethernet. Remember this number for section 12.
- `link/ether bc:24:11:...` is this NIC's MAC. `brd ff:ff:...` is the
  broadcast address.

**Hands-on lab (test VM only)**

```bash
# 1. Build
sudo ~/netlab.sh up
sudo ip -n client link show c-eth0          # note the client MAC
sudo ip -n router link show r-eth0          # note the router MAC

# 2. Break: change the router's MAC while the client still has the old one cached
sudo ip netns exec client ping -c1 10.10.1.1            # populate the ARP cache
sudo ip -n router link set r-eth0 address 02:00:00:00:00:99
sudo ip netns exec client ping -c3 -W1 10.10.1.1        # may fail until the cache entry is re-validated

# 3. Diagnose
sudo ip -n client neigh show 10.10.1.1                  # which MAC does the client believe?
sudo ip netns exec router tcpdump -ni r-eth0 -e -c 6    # frames addressed to the old MAC are ignored

# 4. Fix: flush the stale entry (what a gratuitous ARP would have done automatically)
sudo ip -n client neigh flush dev c-eth0
sudo ip netns exec client ping -c2 10.10.1.1
```

> Linux re-validates stale neighbour entries within seconds, so the outage in
> this lab is short. In real networks, firewalls, switches and other OSes can
> keep a stale MAC for minutes. That's why a keepalived VIP failover sends
> gratuitous ARP.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Cable, switch port or VM NIC disconnected | `NO-CARRIER`, `state DOWN`, `Link detected: no` | `ip -br link`, `ethtool IFACE` | [02-network.md](02-network.md) |
| Speed/duplex mismatch, bad cable | Slow transfers, `rx_crc_errors` climbing | `ethtool -S IFACE | grep -i err` | [Network speed playbook](24-playbook-network-speed.md) |
| NIC or ring buffer overrun | `dropped` / `overrun` counters rising in `ip -s link` | `ip -s link show IFACE` (twice, compare) | [Network speed playbook](24-playbook-network-speed.md) |
| MAC changed (VIP failover, replaced NIC) | Some clients reach the old box, others the new one | `ip neigh`, `arping -I IFACE IP` | section 2 ARP topic |

**Why it matters for troubleshooting:** Every connectivity problem sits on top
of L2. If the gateway's MAC can't be learned, nothing above it can work, and
no amount of DNS or firewall debugging will help. Check `ip -br link` and
`ip neigh` in the first 10 seconds of an incident.

**Next step:** ARP is how a host learns which MAC belongs to an IP. It's the
glue between L2 and L3.

### ARP and the neighbour table

**Level:** [L1 · Junior] for `ip neigh` as a first-10-seconds check · [L2 · Mid] for duplicate IPs and gratuitous ARP after failover.

**Concept.** A host knows the *IP* it wants to reach but needs a *MAC* to
build a frame. ARP (Address Resolution Protocol, IPv4) broadcasts "who has
10.10.1.1? tell 10.10.1.10", and the owner replies "10.10.1.1 is at
9e:1d:...". The answer is cached in the **neighbour table**. The host only ARPs
for addresses in its own subnet. For everything else it ARPs for the
**gateway**. IPv6 does the same job with Neighbour Discovery (NDP, ICMPv6)
instead of ARP (section 13).

```
 client: "is 203.0.113.10 in my subnet 192.0.2.0/24?"  -> no
         -> next hop = default gateway 192.0.2.1
         -> ARP: who-has 192.0.2.1?   (broadcast ff:ff:ff:ff:ff:ff)
 router: 192.0.2.1 is-at bb:bb:bb:bb:bb:bb   (unicast reply)
 client: send frame to bb:bb..., IP destination 203.0.113.10
```

**Key terms**: neighbour states as `ip neigh` shows them.

| State | Meaning |
|---|---|
| `REACHABLE` | Confirmed recently. Healthy |
| `STALE` | Valid but not confirmed recently. Normal; re-checked on next use |
| `DELAY` / `PROBE` | Kernel is re-confirming the entry right now |
| `FAILED` | ARP got no answer. That IP isn't on this segment or is down |
| `INCOMPLETE` | ARP request sent, no answer yet |
| `PERMANENT` | Static entry set by an admin (or by Docker/K8s tooling) |

**See it on a real system**

```bash
ip neigh                            # whole table
ip neigh show 192.0.2.1             # the gateway only
ip neigh show nud failed            # every entry that did not answer
sudo arping -c 3 -I ens18 192.0.2.1 # ask the gateway directly (iputils-arping)
sudo arping -D -c 2 -I ens18 192.0.2.10   # duplicate address detection: does anyone ELSE own my IP?
```

```
$ ip neigh
192.0.2.1 dev ens18 lladdr 00:1a:2b:3c:4d:5e REACHABLE
192.0.2.53 dev ens18 lladdr 00:1a:2b:3c:4d:60 STALE
192.0.2.77 dev ens18 FAILED
172.18.0.3 dev br-6c1e2f0a9b3d lladdr 02:42:ac:12:00:03 STALE
```

- The gateway is `REACHABLE`, so L2 to the router is fine.
- 192.0.2.77 is `FAILED`: something tried to reach it and it never answered
  ARP. It's down, unplugged, in another VLAN, or the IP is wrong.
- The entry on `br-...` is a Docker container on a user-defined bridge. The
  `02:42:...` prefix gives it away on Docker 27 and older; Docker 28+ gives
  containers random MACs, so go by the `br-...`/`docker0` device instead.

```
$ sudo arping -D -c 2 -I ens18 192.0.2.10
ARPING 192.0.2.10 from 0.0.0.0 ens18
Unicast reply from 192.0.2.10 [00:50:56:9A:11:22]  0.811ms
Sent 1 probes (1 broadcast(s))
Received 1 response(s)
```

- In `-D` mode any reply means **someone else uses your IP**: a duplicate
  address. `-D` stops at the first reply and exits with status 1; exit 0
  (no replies) means the address is free. That explains "connections randomly die or hit the wrong server".

**Hands-on lab (test VM only)**

```bash
# 1. Build and observe a normal ARP exchange
sudo ~/netlab.sh up
sudo ip -n client neigh flush all
sudo ip netns exec router tcpdump -ni r-eth0 -e -c 6 arp &  # background capture (stops after 6 packets)
sudo ip netns exec client ping -c1 10.10.2.20
sudo ip -n client neigh                                     # 10.10.1.1 REACHABLE - only the gateway, never 10.10.2.20

# 2. Break: a static ARP entry with the wrong MAC (simulates a stale or poisoned entry)
sudo ip -n client neigh replace 10.10.1.1 lladdr 02:00:00:00:00:99 dev c-eth0 nud permanent
sudo ip netns exec client ping -c3 -W1 10.10.2.20           # 100% loss

# 3. Diagnose
sudo ip -n client neigh show 10.10.1.1                      # PERMANENT, wrong lladdr
sudo ip -n router link show r-eth0 | grep ether             # the real MAC differs

# 4. Fix
sudo ip -n client neigh del 10.10.1.1 dev c-eth0
sudo ip netns exec client ping -c2 10.10.2.20
sudo pkill -x tcpdump                                       # stop the background capture if still running
```

- Notice that the client never ARPs for 10.10.2.20. It's off-subnet, so the
  client only needs the gateway's MAC. That's the most important fact in this
  topic.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Gateway down or wrong VLAN | Gateway `FAILED`/`INCOMPLETE`; nothing off-subnet works | `ip neigh show GW`, `arping -I IFACE GW` | [Site down playbook](25-playbook-site-down.md) |
| Duplicate IP | Intermittent drops, SSH lands on the "wrong" server, MAC for an IP keeps changing | `arping -D -I IFACE IP` | [02-network.md](02-network.md) |
| VIP failover without gratuitous ARP | Clients reach the old node after a keepalived/Pacemaker failover | `ip neigh` on clients; `arping -U -I IFACE VIP` on the new owner | section 11 |
| Neighbour table overflow (big flat L2, many containers) | `neighbour: arp_cache: neighbor table overflow!` in `dmesg` | `ip neigh | wc -l`, `sysctl net.ipv4.neigh.default.gc_thresh3` | [Kernel](13-kernel-system.md) |

**Why it matters for troubleshooting:** "I can ping the gateway but not the
server" and "I can't even ping the gateway" are different worlds. The
neighbour table tells you which one you're in without any guessing.

**Next step:** ARP stays within one broadcast domain. Switches and VLANs
decide how big that domain is.

### Switches, bridges and VLANs

**Level:** [L1 · Junior] for Linux and Docker bridges · [L2 · Mid] for proving a VLAN mistake before you call the network team.

**Concept.** A **switch** forwards frames by MAC. It learns which MAC lives
behind which port by watching source addresses (the MAC table or FDB), and it
floods broadcasts and unknown destinations to every port. A Linux **bridge**
is a software switch. `docker0`, `br-xxxx` (Compose and Dokploy networks),
`cni0` and `virbr0` are all bridges, and the `veth` interfaces are the cables
plugged into them. A **VLAN** splits one physical switch into several virtual
ones: frames get an 802.1Q tag with a 12-bit VLAN ID (1–4094), and hosts in
different VLANs can't talk at L2. They need a router.

```
                 physical switch
   ┌─────────────────────────────────────────────┐
   │ port1 access VLAN10  port2 access VLAN20    │  access port: untagged, one VLAN
   │ port24 TRUNK (VLAN 10,20 tagged) ───────────┼──► to router / hypervisor / server NIC
   └─────────────────────────────────────────────┘
   Linux server on the trunk:  ens19 (no IP)
                               ├── ens19.10  192.0.2.10/24     (VLAN 10)
                               └── ens19.20  198.51.100.10/24  (VLAN 20)
```

**Key terms**

| Term | Meaning |
|---|---|
| FDB / MAC table | Switch's map of MAC to port. `bridge fdb` shows it on Linux |
| Access port | Carries one VLAN, untagged. The host doesn't know VLANs exist |
| Trunk port | Carries several VLANs, tagged. The host or hypervisor must create VLAN subinterfaces |
| Native VLAN / PVID | VLAN assigned to untagged frames on a port |
| veth pair | Two virtual interfaces joined like a cable. Containers use one end, the bridge the other |
| STP | Spanning Tree Protocol. Blocks loops between switches (a loop = broadcast storm) |

**See it on a real system**

```bash
ip -br link show type bridge                 # all software switches on this host
ip -br link show master docker0              # which veths are plugged into docker0
bridge link                                  # every bridge port and its state
bridge fdb show br br-6c1e2f0a9b3d | grep -v permanent   # learned MACs on a Docker network
ip -d link show ens19.20                     # VLAN details: "vlan protocol 802.1Q id 20"
cat /etc/netplan/*.yaml                      # how VLANs are configured on Ubuntu
```

```
$ ip -br link show type bridge
docker0          DOWN           02:42:9c:1e:5a:0b <NO-CARRIER,BROADCAST,MULTICAST,UP>
br-6c1e2f0a9b3d  UP             02:42:5f:aa:13:07 <BROADCAST,MULTICAST,UP,LOWER_UP>

$ bridge link
12: veth3a1f2c9@if11: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 master br-6c1e2f0a9b3d state forwarding priority 32 cost 2
14: veth91be0d4@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 master br-6c1e2f0a9b3d state forwarding priority 32 cost 2
```

- Each `vethXXXX@ifNN` is one container's cable. `@if11` is the interface
  index of the other end, inside the container's namespace.

A netplan VLAN definition looks like this (on a test VM, apply with
`sudo netplan try`, which rolls back automatically after 120 s unless you
confirm):

```yaml
network:
  version: 2
  ethernets:
    ens19: {}
  vlans:
    ens19.20:
      id: 20
      link: ens19
      addresses: [198.51.100.10/24]
```

**Hands-on lab (test VM only)**: build a switch, then split it with VLANs.

```bash
# 1. Build: two hosts on one software switch
for ns in h1 h2 sw; do sudo ip netns add $ns; done
sudo ip link add h1-eth0 netns h1 type veth peer name sw-p1 netns sw
sudo ip link add h2-eth0 netns h2 type veth peer name sw-p2 netns sw
sudo ip -n sw link add br0 type bridge
sudo ip -n sw link set sw-p1 master br0
sudo ip -n sw link set sw-p2 master br0
for i in br0 sw-p1 sw-p2; do sudo ip -n sw link set $i up; done
sudo ip -n h1 addr add 192.168.50.1/24 dev h1-eth0 && sudo ip -n h1 link set h1-eth0 up
sudo ip -n h2 addr add 192.168.50.2/24 dev h2-eth0 && sudo ip -n h2 link set h2-eth0 up
sudo ip netns exec h1 ping -c2 192.168.50.2
sudo ip netns exec sw bridge fdb show br br0 | grep -v permanent   # the switch learned both MACs

# 2. Break: put the two ports in different VLANs
sudo ip -n sw link set br0 type bridge vlan_filtering 1
sudo ip netns exec sw bridge vlan add dev sw-p1 vid 10 pvid untagged
sudo ip netns exec sw bridge vlan add dev sw-p2 vid 20 pvid untagged
sudo ip netns exec sw bridge vlan del dev sw-p1 vid 1
sudo ip netns exec sw bridge vlan del dev sw-p2 vid 1
sudo ip -n h1 neigh flush all                           # forget the MAC learned in step 1, so h1 must ARP again
sudo ip netns exec h1 ping -c2 -W1 192.168.50.2          # fails

# 3. Diagnose: link is up, IPs are right, but ARP gets no answer
sudo ip -n h1 neigh                                     # 192.168.50.2 INCOMPLETE, then FAILED
sudo ip netns exec sw bridge vlan show                  # sw-p1 in 10, sw-p2 in 20

# 4. Fix: same VLAN on both access ports
sudo ip netns exec sw bridge vlan add dev sw-p2 vid 10 pvid untagged
sudo ip netns exec sw bridge vlan del dev sw-p2 vid 20
sudo ip netns exec h1 ping -c2 192.168.50.2

# 5. Clean up
for ns in h1 h2 sw; do sudo ip netns del $ns; done
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Server port in the wrong VLAN | Link `UP`, IP correct, gateway `FAILED` in `ip neigh` | `ip neigh`, then ask the network team for the port's VLAN | [Site down playbook](25-playbook-site-down.md) |
| Trunk delivered but no VLAN subinterface | `tcpdump -e -ni IFACE` shows `vlan 20` tagged frames, no IP traffic | `sudo tcpdump -eni ens19 -c 10` | [02-network.md](02-network.md) |
| Switching loop | Whole segment slow, broadcast storm, CPU high on switches | `sudo tcpdump -eni IFACE broadcast -c 100` (count per second) | network team |
| Container not on the proxy's bridge | Traefik gets `no route to host` or 502 | `docker network inspect NET` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting:** On-prem, "the new server can't reach
anything" is often a switch-port VLAN mistake, and you can prove it in two
minutes (link up, ARP fails, tagged frames visible) before you call the
network team. In Docker, "two containers can't see each other" is the same
idea: they're on different bridges, which are different broadcast domains.

**Next step:** with L2 understood, move to IP addressing and the subnet mask,
which decides "same segment (ARP directly) or send to the gateway".

---

## 3. IP addressing, CIDR and subnetting

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics → *Networking Basics* (IP addresses, subnets, gateways) ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page)) · 2) Note: the worked examples and practice questions in this section, on paper · 3) Video: KodeKloud *AWS Networking Basics | AWS VPC & Subnets for Beginners* (18 min, the CIDR and subnet part; [YouTube](https://www.youtube.com/watch?v=QM63dyA_4Pc)) · 4) Practice: check every answer with `ipcalc`, then the overlap lab below; the AWS view of subnets is in [AWS reference](16-aws-cloud.md).

### IPv4 addresses, CIDR and special ranges

**Level:** [L0 · Fresher] · read prefixes and special ranges on sight.

**Concept.** An IPv4 address is 32 bits, written as four bytes
(192.0.2.10). The **prefix length** (`/24`) says how many leading bits are
the **network** part. The remaining bits identify a **host** inside that
network. Every host compares the destination address with its own prefix:
same network means "deliver directly (ARP for it)", different network means
"send to the gateway". Get the prefix wrong and the host makes the wrong
decision. That's a classic outage that looks like a routing problem.

```
 192.0.2.10/24
 11000000.00000000.00000010 . 00001010
 └──── network (24 bits) ──┘   └ host ┘
 mask      255.255.255.0
 network   192.0.2.0      (all host bits 0, not usable for a host)
 broadcast 192.0.2.255    (all host bits 1, not usable for a host)
 hosts     192.0.2.1 - 192.0.2.254   = 2^8 - 2 = 254
```

**Key terms**: prefixes you'll meet every week.

| Prefix | Mask | Addresses | Usable hosts | Where you see it |
|---|---|---|---|---|
| /8 | 255.0.0.0 | 16,777,216 | 16,777,214 | 10.0.0.0/8 corporate supernet |
| /12 | 255.240.0.0 | 1,048,576 | - | 172.16.0.0/12 private block (Docker pools live here) |
| /16 | 255.255.0.0 | 65,536 | 65,534 | Docker `docker0` 172.17.0.0/16, K8s pod CIDR 10.244.0.0/16, AWS VPC |
| /20 | 255.255.240.0 | 4,096 | 4,094 | Docker user-defined/Compose networks once the default pools' 172.17–172.31 /16s are used up: the next ones are 192.168.x.0/20 |
| /22 | 255.255.252.0 | 1,024 | 1,022 | Office/VPN segments |
| /24 | 255.255.255.0 | 256 | 254 | Typical server VLAN, K8s per-node pod range |
| /26 | 255.255.255.192 | 64 | 62 | Small DMZ |
| /30 | 255.255.255.252 | 4 | 2 | Old point-to-point links |
| /31 | 255.255.255.254 | 2 | 2 | Point-to-point (no network/broadcast, RFC 3021) |
| /32 | 255.255.255.255 | 1 | 1 | Single host: firewall rules, WireGuard AllowedIPs, VIPs |

Special ranges you must recognise on sight:

| Range | Meaning |
|---|---|
| 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 | Private (RFC 1918). Not routed on the internet, needs NAT to get out |
| 100.64.0.0/10 | Carrier-grade NAT (ISP), also used by Tailscale |
| 127.0.0.0/8 | Loopback. Never leaves the host (and inside a container it's the *container's* loopback) |
| 169.254.0.0/16 | Link-local. On Windows, macOS and Linux desktops, a host with only this address got no DHCP answer (Ubuntu Server with netplan doesn't self-assign IPv4 link-local by default: there you just see no IPv4 address). 169.254.169.254 is the cloud metadata service |
| 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 | Documentation (TEST-NET-1/2/3). Use them in docs and runbooks |
| 224.0.0.0/4 | Multicast |
| 0.0.0.0 | "This host / any address". As a bind address: all IPv4 interfaces |

**See it on a real system**

```bash
ip -br -4 addr                                    # every IPv4 address and prefix on this host
ip route | grep 'proto kernel'                    # the "connected" networks the prefixes created
ipcalc 192.0.2.10/24                              # Ubuntu's ipcalc (perl version); RHEL's differs
python3 -c "import ipaddress as i; n=i.ip_interface('192.0.2.10/24').network; print(n, n.netmask, n.broadcast_address, n.num_addresses-2)"
```

```
$ ip route | grep 'proto kernel'
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev br-6c1e2f0a9b3d proto kernel scope link src 172.18.0.1
```

- Each address with a prefix automatically creates a "connected" route. This
  host believes that everything in 172.17.0.0/16 and 172.18.0.0/16 is behind
  its Docker bridges. If your office VPN hands out 172.18.20.0/24, those users
  can't reach this server (see "How it breaks").

**Hands-on lab (test VM only)**: the wrong-prefix outage.

```bash
# 1. Build
sudo ~/netlab.sh up

# 2. Break: give the client /16 instead of /24 (a typo that happens in netplan files)
sudo ip -n client addr del 10.10.1.10/24 dev c-eth0
sudo ip -n client addr add 10.10.1.10/16 dev c-eth0
sudo ip -n client route add default via 10.10.1.1     # re-add: deleting the address removed it
sudo ip netns exec client ping -c2 -W1 10.10.2.20     # fails

# 3. Diagnose: the client thinks 10.10.2.20 is on its own segment
sudo ip -n client route get 10.10.2.20     # "10.10.2.20 dev c-eth0 src 10.10.1.10" - no "via"!
sudo ip -n client neigh                    # 10.10.2.20 INCOMPLETE/FAILED: it ARPed for the server directly

# 4. Fix
sudo ip -n client addr del 10.10.1.10/16 dev c-eth0
sudo ip -n client addr add 10.10.1.10/24 dev c-eth0
sudo ip -n client route add default via 10.10.1.1
sudo ip -n client route get 10.10.2.20     # now "via 10.10.1.1"
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Prefix too big (/16 instead of /24) | Some remote subnets unreachable; `ip route get` shows no `via`; neighbour `FAILED` | `ip route get IP`, `ip neigh` | [Site down playbook](25-playbook-site-down.md) |
| Prefix too small | Hosts in your own subnet go through the gateway; works but odd (ICMP redirects) | `ip route get IP` | section 4 |
| Docker bridge overlaps a corporate or VPN range | Server can't reach clients in 172.17–172.31.x.x; replies go into `docker0`/`br-*` | `ip route get CLIENT_IP` shows `dev br-...` | [Containers playbook](26-playbook-containers-k8s.md) |
| Only a 169.254.x.x address (desktops), or no IPv4 address at all (Ubuntu Server) | DHCP failed | `journalctl -u systemd-networkd -b` | [Network reference](02-network.md) |

> The Docker overlap is very common on-prem. The fix is to give Docker pools
> that don't collide, in `/etc/docker/daemon.json`
> (`"bip": "10.200.0.1/24"` and
> `"default-address-pools": [{"base": "10.201.0.0/16", "size": 24}]`). Docker
> must be restarted afterwards, and existing networks keep their old subnet
> until they're recreated. Plan that as a change with a rollback. See
> [Learn Docker](30-learn-docker.md).

**Why it matters for troubleshooting:** You read prefixes in netplan, Docker
networks, K8s pod and service CIDRs, VPN configs, firewall rules and AWS
security groups. A single wrong bit breaks reachability for a whole range, and
the error looks the same as a routing or firewall problem until you run
`ip route get`.

**Next step:** practise calculating subnets by hand until it takes under a
minute. The next topic gives you the method.

### Subnetting step by step

**Level:** [L0 · Fresher] for the arithmetic (a classic interview topic) · [L3 · Senior] for planning Docker, Kubernetes and VPN ranges that never overlap.

**Concept.** You don't need binary for everyday subnetting. Use the
**block-size method**:

1. Find the **interesting octet**: the octet where the prefix boundary falls
   (/8–/15 → 2nd octet, /16–/23 → 3rd octet, /24–/32 → 4th octet).
2. **Block size** = 256 − the mask value in that octet. Equivalently,
   2^(boundary of that octet − prefix): /26 → 2^(32−26) = 64, /20 → 2^(24−20) = 16.
3. The network starts at the largest **multiple of the block size** that's ≤
   the address's value in that octet. The broadcast is the next multiple − 1.
4. Usable hosts = 2^(32 − prefix) − 2.

| Prefix within an octet | /x+1 | /x+2 | /x+3 | /x+4 | /x+5 | /x+6 | /x+7 | /x+8 |
|---|---|---|---|---|---|---|---|---|
| Mask value | 128 | 192 | 224 | 240 | 248 | 252 | 254 | 255 |
| Block size | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
| Example (4th octet) | /25 | /26 | /27 | /28 | /29 | /30 | /31 | /32 |

**Worked example 1: 192.168.10.77/26**

- The interesting octet is the 4th. Block size = 256 − 192 = 64.
- Multiples of 64: 0, 64, 128, 192. 77 falls between 64 and 128.
- Network 192.168.10.64, broadcast 192.168.10.127, hosts .65–.126 (62 hosts).

**Worked example 2: 10.20.35.200/20**

- /20 falls in the 3rd octet (16 + 4). Block size = 256 − 240 = 16.
- Multiples of 16: 0, 16, 32, 48. 35 falls between 32 and 48.
- Network 10.20.32.0, broadcast 10.20.47.255, hosts 10.20.32.1–10.20.47.254
  (2^12 − 2 = 4094 hosts).

**Worked example 3: are 172.16.5.10/22 and 172.16.6.20 on the same subnet?**

- /22 falls in the 3rd octet. Block size = 256 − 252 = 4. Multiples: 0, 4, 8.
- 5 and 6 both fall in 4–7, so the network is 172.16.4.0/22 (172.16.4.0 to
  172.16.7.255). **Yes**, they're on the same subnet and can talk without a
  router.

**Worked example 4: split 192.168.50.0/24 into four equal subnets**

- Four subnets need 2 more bits: /24 + 2 = /26, block size 64.
- 192.168.50.0/26, .64/26, .128/26, .192/26, with 62 hosts each.

**Worked example 5: how big must a subnet be for 500 hosts?**

- 2^9 − 2 = 510 ≥ 500, so 9 host bits are needed → /23 (e.g. 10.0.4.0/23 =
  10.0.4.0–10.0.5.255).

**Worked example 6: Kubernetes pod CIDR**

- kubeadm with Flannel uses 10.244.0.0/16, and each node gets a /24.
- That's 2^(24−16) = 256 node ranges with 254 pod IPs each. kubelet's default
  limit is 110 pods per node, so the /24 has plenty of room.

**Worked example 7: AWS subnet 10.0.1.0/24**

- 256 − 2 = 254 by the formula, but AWS reserves 5 addresses (network, +1
  router, +2 DNS, +3 reserved, broadcast), so 251 are usable
  ([AWS module](16-aws-cloud.md)).

**Key terms**

| Term | Meaning |
|---|---|
| Interesting octet | The octet in which the prefix boundary falls |
| Block size | How far apart consecutive subnets start in that octet |
| Supernet / summarisation | Combining ranges: 10.0.0.0/23 covers 10.0.0.0/24 and 10.0.1.0/24 |
| Wildcard mask | Inverse of the mask (0.0.0.255 for /24). Used in some ACLs |

**See it on a real system**: check your arithmetic with a tool, never in
place of it.

```bash
ipcalc 10.20.35.200/20
python3 -c "import ipaddress as i; print(list(i.ip_network('192.168.50.0/24').subnets(new_prefix=26)))"
python3 -c "import ipaddress as i; print(i.ip_address('172.16.6.20') in i.ip_network('172.16.5.10/22', strict=False))"
```

```
$ ipcalc 10.20.35.200/20
Address:   10.20.35.200         00001010.00010100.0010 0011.11001000
Netmask:   255.255.240.0 = 20   11111111.11111111.1111 0000.00000000
Wildcard:  0.0.15.255           00000000.00000000.0000 1111.11111111
=>
Network:   10.20.32.0/20        00001010.00010100.0010 0000.00000000
HostMin:   10.20.32.1           00001010.00010100.0010 0000.00000001
HostMax:   10.20.47.254         00001010.00010100.0010 1111.11111110
Broadcast: 10.20.47.255         00001010.00010100.0010 1111.11111111
Hosts/Net: 4094                  Class A, Private Internet
```

**Practice questions.** Answer on paper first, then check with `ipcalc`.

1. 192.0.2.130/25: network, broadcast, first and last host?
2. How many usable hosts in a /27?
3. 172.20.14.9/21: network and broadcast?
4. Smallest prefix that holds 60 hosts? And 1000 hosts?
5. Are 10.1.200.5/17 and 10.1.100.5 on the same subnet?
6. A server has 192.0.2.10/24 and gateway 192.0.2.1. Does traffic to
   192.0.2.200 go through the gateway? Traffic to 198.51.100.7?
7. Docker created 172.18.0.0/16 on a server. Your VPN users get addresses in
   172.18.20.0/24. What symptom do they report, and why?
8. Split 10.50.0.0/22 into /24s. List them.
9. A firewall rule allows 203.0.113.64/27. Is 203.0.113.100 allowed?
10. Write 255.255.255.248 as a prefix length. How many hosts does it hold?

**Answers**

| # | Answer |
|---|---|
| 1 | Block 128: network 192.0.2.128, broadcast .255, hosts .129–.254 |
| 2 | 2^5 − 2 = 30 |
| 3 | 3rd-octet block 8: 8–15 → network 172.20.8.0, broadcast 172.20.15.255 |
| 4 | 60 hosts → /26 (62). 1000 hosts → /22 (1022) |
| 5 | /17 falls in the 3rd octet, block 128: .200 is in 128–255, .100 is in 0–127 → **no** |
| 6 | 192.0.2.200: no, it's on-link (direct ARP). 198.51.100.7: yes, via 192.0.2.1 |
| 7 | "Can't reach the server": its replies match the connected route 172.18.0.0/16 and go into the Docker bridge, not to the gateway |
| 8 | 10.50.0.0/24, 10.50.1.0/24, 10.50.2.0/24, 10.50.3.0/24 |
| 9 | Block 32: .64–.95 → .100 is **not** allowed |
| 10 | /29 → 8 addresses, 6 usable hosts |

**Hands-on lab (test VM only)**: prove answer 7 in the lab.

```bash
# 1. Build: pretend the server namespace has a "docker bridge" that overlaps the client's network
sudo ~/netlab.sh up
sudo ip -n server link add fakedocker type bridge
sudo ip -n server addr add 10.10.0.1/16 dev fakedocker    # 10.10.0.0/16 contains 10.10.1.10!
sudo ip -n server link set fakedocker up

# 2. Observe the break
sudo ip netns exec client ping -c2 -W1 10.10.2.20          # fails
sudo ip -n server route get 10.10.1.10                     # "dev fakedocker" - replies go into the bridge
sudo ip -n server route                                    # 10.10.0.0/16 dev fakedocker AND 10.10.2.0/24 dev s-eth0

# 3. Fix: remove the overlap (in real life: re-plan Docker's address pools)
sudo ip -n server link del fakedocker
sudo ip netns exec client ping -c2 10.10.2.20
```

- The more specific route (10.10.2.0/24) still wins for the server's *own*
  subnet. The /16 bridge captures everything else in 10.10.x.x, which
  includes the client. Section 4 explains longest-prefix match.

**How it breaks**: see the previous topic. The arithmetic itself doesn't
break, but people's assumptions do. Every time you add a network (Docker,
K8s, VPN, a new VLAN), check it for overlaps.

**Why it matters for troubleshooting:** "Can X reach Y?" starts with "are they
on the same subnet?" A firewall rule with /27 instead of /26 silently excludes
half the hosts. With fast subnet arithmetic you can read these at a glance.

**Next step:** routing. When the destination isn't on-link, which gateway does
the kernel pick, and with which source address?

---

## 4. Routing

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics → *Labs – Switching and Routing* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → Configure IPv4/IPv6 Networking and Hostname Resolution ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking → *Prerequisite Network Namespaces*, the same idea as this module's lab ([lesson](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Network-Namespaces/page)) · 4) Note: [Network reference](02-network.md) (ip route, netplan) · 5) Practice: the return-path and policy-routing labs below, then the routing steps of the [network speed playbook](24-playbook-network-speed.md).

### Routing tables and the default gateway

**Level:** [L1 · Junior] for `ip route` and netplan · [L2 · Mid] for return-path reasoning.

**Concept.** A **routing table** is a list of "to reach this range, send to
that next hop through this interface". For every packet the kernel picks the
**most specific matching route** (longest prefix match). The **default route**
(`0.0.0.0/0`, written `default`) matches everything and is used when nothing
more specific does. Its next hop is the **default gateway**. Every router on
the path makes its own independent decision, and the **return path** must
work too. Half of all "routing" problems are replies that can't get back.

```
 destination 172.18.0.5          destination 203.0.113.50
   │                               │
   ▼  candidates:                  ▼  candidates:
   default            /0   ✓       default            /0   ✓  <- only match, use it
   172.18.0.0/16      /16  ✓  <- longest match wins
   192.0.2.0/24       /24  ✗
```

**Key terms**

| Term | Meaning |
|---|---|
| Connected route | Created automatically from an address+prefix (`proto kernel scope link`) |
| Static route | Added by config (netplan `routes:`) or by hand (`ip route add`) |
| Next hop / `via` | The router to hand the packet to. It must be on-link (in a connected subnet) |
| Metric | Tie-breaker between routes with the same prefix. Lower wins |
| `src` | Preferred source address for packets using this route |
| Asymmetric routing | Request and reply take different paths. Stateful firewalls and `rp_filter` drop it |
| `rp_filter` | Reverse-path filter: drop packets arriving on an interface the reply wouldn't use. Ubuntu default 2 = loose |

**See it on a real system**

```bash
ip route                          # main routing table
ip -6 route                       # IPv6 has its own table
ip route show default             # just the default route(s): there should normally be ONE
cat /etc/netplan/*.yaml           # where the gateway is configured (Ubuntu)
networkctl status ens18           # systemd-networkd view: addresses, gateway, DNS
sysctl net.ipv4.ip_forward        # 1 = this host routes for others (Docker sets it to 1)
```

```
$ ip route
default via 192.0.2.1 dev ens18 proto static
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev br-6c1e2f0a9b3d proto kernel scope link src 172.18.0.1
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10
```

- `default via 192.0.2.1 dev ens18 proto static` means anything not matched
  below goes to 192.0.2.1. `proto static` means it came from config (netplan),
  not DHCP (`proto dhcp`).
- `linkdown` on docker0 is harmless: no containers on the default bridge.

A minimal netplan static configuration (Ubuntu 22.04+; `gateway4:` is
deprecated, use `routes:`):

```yaml
network:
  version: 2
  ethernets:
    ens18:
      addresses: [192.0.2.10/24]
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53, 192.0.2.54]
        search: [corp.example.com]
```

```bash
sudo netplan generate        # syntax check, writes nothing live
sudo netplan try             # apply with automatic rollback after 120 s unless you press Enter
```

> Over SSH, always use `netplan try`, never `netplan apply`. A wrong gateway
> or address cuts your own session. With `try`, the old config comes back
> automatically if you can't confirm.

**Hands-on lab (test VM only)**: a broken return path.

```bash
# 1. Build
sudo ~/netlab.sh up
sudo ip netns exec client ping -c1 10.10.2.20          # works

# 2. Break: the server loses its default route (so it has no way back to 10.10.1.0/24)
sudo ip -n server route del default
sudo ip netns exec client ping -c2 -W1 10.10.2.20      # 100% loss

# 3. Diagnose: requests ARRIVE, replies can't LEAVE
sudo ip netns exec server tcpdump -ni s-eth0 -c 4 icmp &   # shows "echo request" only, no reply
sudo ip netns exec client ping -c2 -W1 10.10.2.20
sudo ip -n server route get 10.10.1.10                 # RTNETLINK answers: Network is unreachable

# 4. Fix
sudo ip -n server route add default via 10.10.2.1
sudo ip netns exec client ping -c2 10.10.2.20
```

- The client sees a plain timeout, the same as a firewall drop. Only a
  capture *on the server* shows that the requests arrive. That's why the
  playbooks say "capture on both ends".

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| No default route | `Network is unreachable` immediately (ping, curl, ssh) | `ip route show default` | [Site down playbook](25-playbook-site-down.md) |
| Wrong gateway IP | Timeouts to everything off-subnet; gateway `FAILED` in `ip neigh` | `ip neigh show GW` | [02-network.md](02-network.md) |
| Two default routes (two NICs, DHCP on both) | Intermittent: some flows leave via the wrong NIC and are dropped upstream | `ip route show default` | section 4 policy routing |
| Missing return route on the far side | Capture shows requests arriving, no replies leaving | `tcpdump` on the server, `ip route get CLIENT` there | [Site down playbook](25-playbook-site-down.md) |
| Strict `rp_filter` with asymmetric paths | Packets visible on the NIC but never reach the socket | `sysctl net.ipv4.conf.all.rp_filter` | [Kernel](13-kernel-system.md) |
| Upstream loss or latency | `mtr` loss persisting to the last hop | `mtr -rwn -c 100 HOST` | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting:** "The gateway answers, nothing beyond
it does" (Ops Ladder case) is a routing question. `ip route` and
`ip route get` answer it on your side in seconds. The return path is the half
people forget. The far side's routing table matters as much as yours.

**Next step:** `ip route get` shows exactly which route, interface and source
address the kernel will use for one destination. It's the single most useful
routing command.

### Choosing a route: ip route get and the source address

**Level:** [L2 · Mid] · hosts with several NICs, VPNs and Docker bridges.

**Concept.** `ip route get DEST` asks the kernel "if I sent a packet to DEST
now, what would you do?" It evaluates the policy rules (next topic), the
tables, the longest prefix match and the source address selection, then prints
the result. It's what you use when a host has several NICs, VPNs, Docker
bridges or WireGuard tunnels. The **source address** matters because the reply
comes back to it. A packet leaving with the wrong source IP gets a reply that
can't return, or gets dropped by a firewall that only allows the "right" IP.

**Key terms**

| Term | Meaning |
|---|---|
| `ip route get DEST` | Resolve the full decision for one destination |
| `from SRC` / `iif IFACE` / `mark N` | Evaluate as if the packet had this source, input interface or firewall mark |
| `src` hint | Route attribute picking the source IP. Otherwise the kernel picks the primary address on the outgoing interface |
| `tracepath` / `mtr` | Show the path beyond your host |

**See it on a real system**

```bash
ip route get 203.0.113.50                       # out to the internet
ip route get 172.18.0.5                         # into a Docker network
ip route get 10.8.0.2                           # into a VPN tunnel?
ip route get 203.0.113.50 from 198.51.100.10    # as if sent from a second IP
tracepath -n 203.0.113.50                       # path + path MTU, no root needed
mtr -rwn -c 50 203.0.113.50                     # per-hop loss/latency report
```

```
$ ip route get 203.0.113.50
203.0.113.50 via 192.0.2.1 dev ens18 src 192.0.2.10 uid 1000
    cache

$ ip route get 172.18.0.5
172.18.0.5 dev br-6c1e2f0a9b3d src 172.18.0.1 uid 1000
    cache
```

- First: off-subnet, so via the gateway 192.0.2.1 out of `ens18` with source
  192.0.2.10. This is what the internet sees.
- Second: no `via`, so directly on the Docker bridge. The host itself talks to
  containers from 172.18.0.1.

**Hands-on lab (test VM only)**: two exits and a surprising source address.

```bash
# 1. Build: give the client a second interface/subnet toward the router
sudo ~/netlab.sh up
sudo ip link add c-eth1 netns client type veth peer name r-eth2 netns router
sudo ip -n client addr add 10.10.3.10/24 dev c-eth1 && sudo ip -n client link set c-eth1 up
sudo ip -n router addr add 10.10.3.1/24 dev r-eth2 && sudo ip -n router link set r-eth2 up

# 2. Compare decisions
sudo ip -n client route get 10.10.2.20                    # via 10.10.1.1 dev c-eth0 src 10.10.1.10
sudo ip -n client route add 10.10.2.20/32 via 10.10.3.1   # a more specific host route
sudo ip -n client route get 10.10.2.20                    # now via 10.10.3.1 dev c-eth1 src 10.10.3.10

# 3. See the effect on the server: the source address changed
sudo ip netns exec server tcpdump -ni s-eth0 -c 2 icmp &
sudo ip netns exec client ping -c1 10.10.2.20             # server sees 10.10.3.10 now

# 4. Fix/clean: remove the host route
sudo ip -n client route del 10.10.2.20/32
```

- A firewall on the server that only allows 10.10.1.10 would now block this
  client, even though "nothing changed". A new route changed the source IP.
  This happens in real life when a VPN or a second NIC comes up.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Traffic leaves via the VPN/second NIC unexpectedly | Remote firewall denies you; reply never returns | `ip route get DEST` | section 4 policy routing |
| Wrong source IP after adding an address | Allow-lists stop matching | `ip route get DEST`, look at `src` | [02-network.md](02-network.md) |
| Loss somewhere upstream | Slow or lossy transfers | `mtr -rwn -c 100 HOST` | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting:** `ip route get` replaces guessing. On a
Dokploy/Kubernetes host with Docker bridges, overlays, `cni0`, WireGuard and
two NICs, it's the only reliable way to know where a packet goes.

**Next step:** sometimes the *destination* isn't enough to choose a route. You
need the source too. That's policy routing.

### Policy routing basics

**Level:** [L2 · Mid] to recognise it · [L3 · Senior] to design two-uplink or multi-ENI routing.

**Concept.** Normal routing looks only at the destination. **Policy routing**
first consults a list of **rules** (`ip rule`) that can select a different
**routing table** based on the source address, input interface, firewall mark
and so on. The classic use case is a server with two uplinks: replies to
traffic that arrived on NIC2 must leave via NIC2's gateway, otherwise the
upstream firewall or ISP drops them. WireGuard (`wg-quick`), Tailscale,
Kubernetes CNIs and AWS multi-ENI instances all use policy routing.

```
 packet ──► ip rule list (by priority)
            0:      from all lookup local          (local/broadcast addresses)
            1000:   from 198.51.100.10 lookup 100  ─► table 100: default via 198.51.100.1 dev ens19
            32766:  from all lookup main           ─► main:      default via 192.0.2.1 dev ens18
            32767:  from all lookup default
```

**Key terms**

| Term | Meaning |
|---|---|
| Rule | `ip rule` entry: selector (from/to/iif/fwmark) and action (lookup TABLE) |
| Table | A separate routing table, by number or name (`/etc/iproute2/rt_tables`) |
| `main` / `local` | The normal table / the kernel's table of local and broadcast addresses |
| fwmark | Mark set by nftables/iptables, matched by `ip rule fwmark` |

**See it on a real system**

```bash
ip rule                             # rules in priority order
ip route show table all | grep -v '^local\|^broadcast' | head -40
ip route show table 100             # a specific table
```

```
$ ip rule
0:	from all lookup local
1000:	from 198.51.100.10 lookup 100
32766:	from all lookup main
32767:	from all lookup default
```

Netplan can express the same thing persistently:

```yaml
network:
  version: 2
  ethernets:
    ens19:
      addresses: [198.51.100.10/24]
      routes:
        - to: default
          via: 198.51.100.1
          table: 100
      routing-policy:
        - from: 198.51.100.10
          table: 100
          priority: 1000
```

**Hands-on lab (test VM only)**

```bash
# 1. Build: client gets a second address that should use table 100
sudo ~/netlab.sh up
sudo ip -n client addr add 10.10.1.11/24 dev c-eth0
sudo ip -n client rule add from 10.10.1.11 table 100 priority 1000

# 2. Break: table 100 says "unreachable"
sudo ip -n client route add unreachable default table 100
sudo ip netns exec client ping -c1 -I 10.10.1.11 10.10.2.20     # fails: "Network is unreachable"
sudo ip netns exec client ping -c1 10.10.2.20                   # normal source still works

# 3. Diagnose
sudo ip -n client rule
sudo ip -n client route get 10.10.2.20 from 10.10.1.11          # RTNETLINK answers: Network is unreachable
sudo ip -n client route show table 100

# 4. Fix: give table 100 a real default route
sudo ip -n client route replace default via 10.10.1.1 dev c-eth0 table 100
sudo ip -n client route get 10.10.2.20 from 10.10.1.11          # ... via 10.10.1.1 dev c-eth0 table 100
sudo ip netns exec client ping -c1 -I 10.10.1.11 10.10.2.20
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Replies leave via the wrong uplink | Service reachable on one IP but not the other | `ip rule`, `ip route get CLIENT from SERVER_IP` | [Site down playbook](25-playbook-site-down.md) |
| VPN client installs a catch-all rule | Everything goes through the tunnel; LAN unreachable | `ip rule`, `ip route show table all` | section 12 |
| Rules lost on reboot | Worked until reboot | `cat /etc/netplan/*.yaml` (no `routing-policy`) | [02-network.md](02-network.md) |

**Why it matters for troubleshooting:** When `ip route` looks correct but
traffic still goes the wrong way, check `ip rule` next. It's the hidden layer
that VPN clients and CNIs add.

**Next step:** routers don't just forward. Often they also rewrite addresses.
NAT is how your home router, Docker and Kubernetes connect private addresses
to the world.

---

## 5. NAT: SNAT, masquerade and DNAT

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Port Redirection and NAT* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine → *Publishing Ports* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 3) Video: KodeKloud *How Docker Networking Actually Works* (9 min, [YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Note: [Docker reference](14-docker-containers.md) and Docker docs *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)) · 5) Practice: the hand-built port forward below, then publish a port on the KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)) and compare `sudo ss -ltnp` with `sudo iptables -t nat -S DOCKER`.

### SNAT and masquerade

**Level:** [L1 · Junior] · why containers reach the internet and why servers log the wrong client IP.

**Concept.** **Source NAT** rewrites the *source* address of outgoing packets
to the router's own address, and remembers the mapping (in conntrack, section
7) so replies can be translated back. That's how many private hosts share one
public IP. **Masquerade** is SNAT that automatically uses the outgoing
interface's current address. Use it when that address can change (DHCP).
Your home router does this for every device. Docker does it for every
container going out (`172.17.0.2` leaves as the host's IP). Kubernetes does it
for pod egress.

```
 container 172.17.0.2:40000 ──► host (MASQUERADE on ens18) ──► 203.0.113.50:443
                               src rewritten to 192.0.2.10:40000
 reply 203.0.113.50:443 ──► 192.0.2.10:40000 ──► conntrack maps back ──► 172.17.0.2:40000
```

A side effect: the remote server only sees the router's IP. It also means the
destination doesn't need a route back to your private network. The reply goes
to the router's own address, which is on a connected subnet.

**Key terms**

| Term | Meaning |
|---|---|
| SNAT | Rewrite source to a fixed address (`snat to 192.0.2.10`) |
| MASQUERADE | Rewrite source to the outgoing interface's address, whatever it is now |
| POSTROUTING | The netfilter hook where SNAT happens: after the routing decision |
| Port translation (PAT/NAPT) | The source port may also change, so thousands of hosts share one IP |
| Hairpin NAT | An inside client reaches an inside server via the public IP. Needs special rules |

**See it on a real system**

```bash
sudo iptables -t nat -S POSTROUTING          # Docker's MASQUERADE rules (iptables-nft on Ubuntu)
sudo nft list table ip nat                   # same rules, nftables view
sudo conntrack -L -p tcp --dport 443 2>/dev/null | head   # live translations (conntrack package)
```

```
$ sudo iptables -t nat -S POSTROUTING
-P POSTROUTING ACCEPT
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
-A POSTROUTING -s 172.18.0.0/16 ! -o br-6c1e2f0a9b3d -j MASQUERADE
```

- Traffic from a container network that leaves through any *other*
  interface gets the host's address. Delete these rules (for example with
  `iptables -t nat -F`, `nft flush ruleset`, or a firewall script that
  flushes the nat table) and containers lose internet access. A plain
  `iptables -F` only flushes the *filter* table, which breaks other things
  (section 7) but leaves these rules in place.

**Hands-on lab (test VM only)**: make the server see the router, not the client.

```bash
# 1. Build: web server in the server namespace (second terminal)
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20
sudo ip netns exec client curl -s -o /dev/null http://10.10.2.20/   # server log shows 10.10.1.10

# 2. Add masquerade on the router's server-facing interface
sudo ip netns exec router nft add table ip nat
sudo ip netns exec router nft 'add chain ip nat postrouting { type nat hook postrouting priority srcnat; }'
sudo ip netns exec router nft add rule ip nat postrouting oifname "r-eth1" masquerade
sudo ip netns exec client curl -s -o /dev/null http://10.10.2.20/   # server log now shows 10.10.2.1

# 3. Prove the "no route back needed" effect: remove the server's default route
sudo ip -n server route del default
sudo ip netns exec client curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://10.10.2.20/   # still 200!
sudo ip netns exec router conntrack -L 2>/dev/null | grep dport=80   # see both tuples

# 4. Break: remove the NAT -> now the missing return route bites
sudo ip netns exec router nft delete table ip nat
sudo ip netns exec client curl -s -m 3 http://10.10.2.20/ || echo "timed out"

# 5. Fix
sudo ip -n server route add default via 10.10.2.1
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Containers can't reach the internet after a firewall change | `curl` from a container times out; host works | `sudo iptables -t nat -S POSTROUTING` | [Containers playbook](26-playbook-containers-k8s.md) |
| `ip_forward` disabled (hardening script) | Same as above, all containers | `sysctl net.ipv4.ip_forward` | [Learn Docker](30-learn-docker.md) |
| App sees every client as the proxy/NAT IP | Logs, rate limits and allow-lists use the wrong IP | Check `X-Forwarded-For` (section 9) | [Learn web servers](29-learn-webservers-proxies.md) |
| Conntrack table full on the NAT box | New connections dropped; `nf_conntrack: table full, dropping packet` | `sudo dmesg -T | grep conntrack` | section 7 |

**Why it matters for troubleshooting:** Whenever you see "the server logs show
the wrong client IP" or "containers lost outbound access", NAT is involved.
Knowing that SNAT happens in POSTROUTING and DNAT in PREROUTING tells you
where to look.

**Next step:** the reverse direction. DNAT and port forwarding are exactly
what `docker run -p 443:443` does.

### DNAT, port forwarding and Docker published ports

**Level:** [L1 · Junior] for `docker ps` and `ss` · [L2 · Mid] for reading the DNAT rules and conntrack entries.

**Concept.** **Destination NAT** rewrites the *destination* of incoming
packets, typically "anything arriving on port 8080 of my public IP goes to
10.0.0.5:80". That's port forwarding on a home router, a Kubernetes NodePort,
and Docker's `-p HOSTPORT:CONTAINERPORT`. DNAT happens in **PREROUTING**,
*before* the routing decision. So the kernel then *forwards* the packet to the
container (FORWARD chain) instead of delivering it locally (INPUT chain). That
one fact explains why UFW (which filters INPUT) doesn't protect published
Docker ports (section 7).

```
 client 198.51.100.23 ──► 192.0.2.10:443 (host)
     PREROUTING  nat DOCKER chain:  DNAT to 172.18.0.3:443   (Traefik container)
     routing:    172.18.0.3 is behind br-6c1e2f0a9b3d  -> FORWARD, not INPUT
     FORWARD:    DOCKER-USER -> Docker's accept rules     (UFW's INPUT rules never see it)
 reply 172.18.0.3:443 ──► conntrack un-DNATs: source becomes 192.0.2.10:443
```

Docker also starts a small userland process, `docker-proxy`, for each
published port. It's the listener `ss` shows, and it handles cases the
iptables rules don't (for example connections to 127.0.0.1 from the host
itself). So `ss -ltnp` shows `docker-proxy` owning 443, not Traefik.

**Key terms**

| Term | Meaning |
|---|---|
| DNAT | Rewrite destination address/port. Happens in PREROUTING (and OUTPUT for local traffic) |
| Port forwarding | DNAT of one port to an inside host |
| `docker-proxy` | Userland forwarder Docker runs per published port. It's the process `ss` shows |
| Publish (`-p`, `ports:`) | Create DNAT + docker-proxy. `127.0.0.1:18000:8000` publishes on loopback only |
| `expose:` | Documentation/hint only. Creates **no** NAT and restricts nothing |
| NodePort | Kubernetes DNAT from every node's port 30000–32767 to pod endpoints |

**See it on a real system**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'   # who owns the web ports
sudo iptables -t nat -S DOCKER                                    # Docker's DNAT rules
docker ps --format 'table {{.Names}}\t{{.Ports}}'                 # the same mapping, Docker's view
sudo conntrack -L -p tcp --dport 443 2>/dev/null | head -3        # live DNAT translations
```

```
$ sudo ss -ltnp '( sport = :80 or sport = :443 )'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*     users:(("docker-proxy",pid=2211,fd=7))
LISTEN 0      4096         0.0.0.0:80        0.0.0.0:*     users:(("docker-proxy",pid=2190,fd=7))
LISTEN 0      4096            [::]:443          [::]:*     users:(("docker-proxy",pid=2218,fd=7))
LISTEN 0      4096            [::]:80           [::]:*     users:(("docker-proxy",pid=2197,fd=7))

$ sudo iptables -t nat -S DOCKER
-N DOCKER
-A DOCKER -i docker0 -j RETURN
-A DOCKER ! -i br-6c1e2f0a9b3d -p tcp -m tcp --dport 443 -j DNAT --to-destination 172.18.0.3:443
-A DOCKER ! -i br-6c1e2f0a9b3d -p tcp -m tcp --dport 80 -j DNAT --to-destination 172.18.0.3:80

$ sudo conntrack -L -p tcp --dport 443
tcp      6 431999 ESTABLISHED src=198.51.100.23 dst=192.0.2.10 sport=51544 dport=443 src=172.18.0.3 dst=198.51.100.23 sport=443 dport=51544 [ASSURED] mark=0 use=1
```

- `docker-proxy` owns 0.0.0.0:443 and [::]:443. To find *which container*,
  match the port with `docker ps`. The process name alone won't tell you
  ([ports inventory playbook](22-playbook-ports-inventory.md)).
- In the conntrack line, the first tuple is the original packet
  (client → host:443). The second is the expected reply (container
  172.18.0.3 → client). The difference between them *is* the DNAT.
- The exact chain names and whether `docker-proxy` is used vary between Docker
  versions and settings (`userland-proxy`). The principle doesn't.

**Hands-on lab (test VM only)**: build a port forward by hand, the way Docker does.

```bash
# 1. Build: server listens on 80; client will connect to the ROUTER's 8080
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20     # second terminal
sudo ip netns exec router nft add table ip nat
sudo ip netns exec router nft 'add chain ip nat prerouting { type nat hook prerouting priority dstnat; }'
sudo ip netns exec router nft add rule ip nat prerouting iifname "r-eth0" tcp dport 8080 dnat to 10.10.2.20:80
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code}\n' http://10.10.1.1:8080/   # 200

# 2. Look at the translation
sudo ip netns exec router conntrack -L 2>/dev/null | grep 8080
sudo ip netns exec router nft list table ip nat

# 3. Break: forwarding off on the router (DNAT still happens, forwarding doesn't)
sudo ip netns exec router sysctl -w net.ipv4.ip_forward=0
sudo ip netns exec client curl -s -m 3 http://10.10.1.1:8080/ || echo "timed out"

# 4. Diagnose: packets arrive at the router and go nowhere
#    (start the capture, then re-run the step 3 curl in a second terminal)
sudo ip netns exec router tcpdump -ni any -c 6 'tcp port 8080 or tcp port 80'   # SYNs to :8080 on r-eth0, nothing on r-eth1
sudo ip netns exec router sysctl net.ipv4.ip_forward

# 5. Fix
sudo ip netns exec router sysctl -w net.ipv4.ip_forward=1
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Host port already taken (your Apache incident) | Another container holds it: `Bind for 0.0.0.0:443 failed: port is already allocated`. A host process holds it: `failed to bind host port for 0.0.0.0:443:172.18.0.3:443/tcp: address already in use` (Docker 28+) or `Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use` (older) | `sudo ss -ltnp 'sport = :443'` | [Apache/Dokploy case](21-case-apache-443-dokploy.md) |
| Published port reachable from everywhere despite `ufw deny` | Port scan from outside shows it open | `sudo iptables -S DOCKER-USER` | section 7 |
| Published, but app inside listens on 127.0.0.1 | `curl: (56) Recv failure: Connection reset by peer` or empty reply | `docker exec CONTAINER ss -ltn` (or netshoot) | [Containers playbook](26-playbook-containers-k8s.md) |
| Hairpin: inside client uses the public name/IP | Works from outside, times out from inside the LAN | `ip route get PUBLIC_IP`, split DNS | section 8 |
| NodePort unreachable | Timeout on NODE:3xxxx | `kubectl get svc`, `sudo iptables -t nat -S KUBE-NODEPORTS` | [Learn Kubernetes](31-learn-kubernetes.md) |

**Why it matters for troubleshooting:** This is how Dokploy's Traefik gets
ports 80 and 443. It also explains why Docker refused to start Traefik while
Apache owned 443: DNAT plus `docker-proxy` need the host port free. And it's
why a "firewalled" test port turned out to be open to the world.

**Next step:** NAT and firewalls act on TCP and UDP ports, so learn what those
really are. The transport layer is next.

---

## 6. Transport: TCP, UDP, ports and sockets

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *IPs and Ports* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) Note: [Who owns this port?](22-playbook-ports-inventory.md) sections 2–4 · 4) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) for reading handshakes and resets · 5) Practice: the labs below, then five [SadServers](https://sadservers.com/scenarios) easy scenarios.

### TCP vs UDP

**Level:** [L1 · Junior].

**Concept.** IP only delivers packets between *hosts*. The transport layer
delivers data between *programs*, identified by **ports**. **TCP** builds a
reliable, ordered byte stream on top of IP. It sets up a connection
(handshake), numbers every byte, retransmits losses, and slows down when the
network is congested. **UDP** sends independent datagrams with no connection,
no retransmission and no ordering. It's cheap and fast, and the application
handles reliability if it needs it. QUIC (HTTP/3) and WireGuard run over UDP
and add their own reliability and encryption.

| | TCP | UDP |
|---|---|---|
| Connection | Yes: 3-way handshake, then teardown | No |
| Reliability and order | Retransmits, reorders, flow and congestion control | None (the app decides) |
| "Is the port open?" test | Clear: SYN-ACK = open, RST = closed, nothing = filtered | Ambiguous: silence can mean open *or* filtered |
| Closed port answer | TCP RST | ICMP "port unreachable" |
| Typical users | HTTP/1.1, HTTP/2, TLS, SSH, databases, K8s API | DNS, NTP, QUIC/HTTP3, WireGuard, VXLAN, syslog, SNMP |

Ports you'll meet in this stack:

| Port | Service | Port | Service |
|---|---|---|---|
| 22/tcp | SSH | 3000/tcp | Dokploy UI |
| 53/udp+tcp | DNS (TCP for big answers and zone transfers) | 2377/tcp | Docker Swarm cluster management |
| 80, 443/tcp | HTTP, HTTPS | 7946/tcp+udp | Swarm node gossip |
| 443/udp | HTTP/3 (QUIC) | 4789/udp | VXLAN overlay data (Swarm) |
| 123/udp | NTP | 6443/tcp | Kubernetes API server |
| 5432, 3306, 6379 | PostgreSQL, MySQL, Redis | 2379–2380/tcp | etcd |
| 51820/udp | WireGuard (by convention; you choose `ListenPort`) | 10250/tcp | kubelet API |
| 9090, 9100 | Prometheus, node_exporter | 30000–32767/tcp | Kubernetes NodePorts |

**Key terms**

| Term | Meaning |
|---|---|
| Port | 16-bit number (0–65535) identifying a program endpoint on a host |
| Well-known / privileged ports | 0–1023. Binding needs root or `CAP_NET_BIND_SERVICE` |
| Ephemeral ports | Client-side source ports picked by the kernel: `net.ipv4.ip_local_port_range` (32768–60999) |
| Segment / datagram | A TCP / UDP unit of data |
| ICMP port unreachable | What a host sends back for UDP to a closed port |

**See it on a real system**

```bash
sudo ss -tulpn                    # TCP+UDP listeners with process (needs sudo for -p)
getent services 443 53/udp 4789/udp   # port-to-name map from /etc/services
sysctl net.ipv4.ip_local_port_range   # ephemeral port range
```

```
$ sudo ss -tulpn
Netid State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
udp   UNCONN 0      0       127.0.0.54:53       0.0.0.0:*         users:(("systemd-resolve",pid=612,fd=16))
udp   UNCONN 0      0       127.0.0.53%lo:53    0.0.0.0:*         users:(("systemd-resolve",pid=612,fd=14))
udp   UNCONN 0      0       127.0.0.1:323       0.0.0.0:*         users:(("chronyd",pid=701,fd=5))
tcp   LISTEN 0      4096    127.0.0.53%lo:53    0.0.0.0:*         users:(("systemd-resolve",pid=612,fd=15))
tcp   LISTEN 0      4096    0.0.0.0:22          0.0.0.0:*         users:(("sshd",pid=880,fd=3))
tcp   LISTEN 0      511     *:443               *:*               users:(("apache2",pid=1342,fd=6),...)
```

- UDP sockets show `UNCONN`, not `LISTEN`. There are no connections.
- `127.0.0.53%lo:53` is the systemd-resolved stub, bound to loopback only
  (section 8).
- `127.0.0.1:323` is chrony's local command port (for `chronyc`), present
  only if chrony is installed. As a plain NTP *client* it doesn't listen on
  123. The default time client on Ubuntu 22.04/24.04, `systemd-timesyncd`,
  shows no listener at all.

**Hands-on lab (test VM only)**: how TCP and UDP answer a closed port.

```bash
# 1. Build + capture on the server
sudo ~/netlab.sh up
sudo ip netns exec server tcpdump -ni s-eth0 -c 6 'tcp port 81 or udp port 5353 or icmp' &

# 2. TCP to a closed port -> RST, the client knows instantly
sudo ip netns exec client nc -zv -w2 10.10.2.20 81
#   nc: connect to 10.10.2.20 port 81 (tcp) failed: Connection refused
#   capture: Flags [S] then Flags [R.]

# 3. UDP to a closed port -> ICMP port unreachable
echo hi | sudo ip netns exec client nc -u -w2 10.10.2.20 5353
#   capture: "ICMP 10.10.2.20 udp port 5353 unreachable"

# 4. Break: drop ICMP on the router, repeat step 3
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd icmp type destination-unreachable drop
echo hi | sudo ip netns exec client nc -u -w2 10.10.2.20 5353
#   silence: the client cannot tell "closed" from "open but quiet" -> UDP tests are ambiguous

# 5. Clean up
sudo ip netns exec router nft delete table inet lab
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| DNS works over UDP, fails for big answers | Large TXT/DNSSEC answers fail; `dig +tcp` times out | `dig +tcp NAME @SERVER` | section 8 |
| UDP port "open" per nc, service not working | No error, no data | `sudo tcpdump -ni any udp port PORT` on both ends | [02-network.md](02-network.md) |
| HTTP/3 blocked | Browser falls back to HTTP/2 (works, but slower first visit); no UDP 443 traffic | `sudo ss -ulpn 'sport = :443'`, firewall rules for 443/udp | section 9 |
| Ephemeral ports exhausted | `Cannot assign requested address` on outbound connects | `ss -tan state time-wait | wc -l` | next topics |

**Why it matters for troubleshooting:** Firewall rules, Docker `ports:` and
security groups are per protocol. "443 is open" usually means TCP only. Know
which protocol each service uses (DNS: both; WireGuard: UDP only) before you
call a port "open".

**Next step:** ports plus addresses make sockets. The bind address decides who
can reach a service, and it's the heart of your Apache/Dokploy incident.

### Ports, sockets and bind addresses

**Level:** [L1 · Junior] · half of the L1 exit test. A Fresher should already read `0.0.0.0` vs `127.0.0.1` correctly.

**Concept.** A **socket** is one endpoint: protocol + IP + port. A server
calls `bind()` to claim an address and port, then `listen()` to accept
connections. A TCP **connection** is identified by the **5-tuple** (protocol,
source IP, source port, destination IP, destination port). That's why one
server port can carry thousands of connections. The **bind address** decides
which incoming connections reach the socket:

| Bind address | Who can connect | `ss` shows | Typical use |
|---|---|---|---|
| `0.0.0.0` | Any IPv4 address of this host, from anywhere the firewall allows | `0.0.0.0:443` | Public services; Docker `-p 443:443` |
| `[::]` (`::`) | Any IPv6 address, and usually IPv4 too (dual-stack, `IPV6_V6ONLY=0`) | `[::]:443` or `*:443` | Apache `Listen 443`, Python `http.server` |
| `127.0.0.1` | Only processes on this host (and inside a container: only that container) | `127.0.0.1:5432` | Databases, admin UIs, apps behind a local proxy |
| A specific IP | Only connections to that IP | `192.0.2.10:443` | Multi-IP hosts; two services on the same port |

**The rule behind "address already in use":** two listeners can share a port
only if their addresses don't overlap. `192.0.2.10:443` and `192.0.2.11:443`
can coexist. `0.0.0.0:443` overlaps with *every* IPv4 address, so it conflicts
with any other listener on 443 (and `[::]` dual-stack conflicts with
`0.0.0.0`). The error is `EADDRINUSE`, which programs report as
`bind: Address already in use`.

```
 The Apache/Dokploy incident, as sockets:

   apache2   bound  *:443   (all IPv4 + IPv6 addresses)   <- holds the port
   Dokploy installs Traefik, publishes 0.0.0.0:443 and [::]:443
   docker-proxy bind(0.0.0.0:443) -> EADDRINUSE
   docker (older): "... listen tcp4 0.0.0.0:443: bind: address already in use"
   docker 28+:     "... failed to bind host port for 0.0.0.0:443:...: address already in use"

 Ways out (pick one, as a planned change):
   a) Traefik takes 80/443. Apache moves to a private port (e.g. 8080) and
      Traefik routes the old vhosts to it during the migration.         <- recommended
   b) Two IPs: Apache Listen 192.0.2.10:443, Traefik published on 192.0.2.11:443
   c) Traefik on other ports: breaks normal URLs and Let's Encrypt HTTP-01 (needs :80)
```

> Inside a container, 127.0.0.1 is the *container's* loopback. If Traefik
> (in a container) must reach Apache on the host, Apache can't listen only on
> the host's 127.0.0.1. It needs an address the container can reach (the
> host's IP or the Docker bridge gateway), protected by the firewall. The full
> procedure is in the [Apache/Dokploy case](21-case-apache-443-dokploy.md).

**Your actual fix, as sockets.** You took way (a) with different port
numbers: Apache now has `Listen 81` and `Listen 444 https`, and Traefik owns
80 and 443. No two listeners overlap any more, so both programs can bind:

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :81 or sport = :444 )'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:80        0.0.0.0:*    users:(("docker-proxy",pid=2190,fd=7))
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*    users:(("docker-proxy",pid=2211,fd=7))
LISTEN 0      511                *:81              *:*    users:(("apache2",pid=1338,fd=4),("apache2",pid=1341,fd=4))
LISTEN 0      511                *:444             *:*    users:(("apache2",pid=1338,fd=6),("apache2",pid=1341,fd=6))
LISTEN 0      4096            [::]:80           [::]:*    users:(("docker-proxy",pid=2197,fd=7))
LISTEN 0      4096            [::]:443          [::]:*    users:(("docker-proxy",pid=2218,fd=7))
```

**What it means:** `docker-proxy` holds 80 and 443 for the Traefik container
(section 5 explains why the owner isn't called "traefik"). Apache holds
`*:81` and `*:444`. Three consequences follow from these lines:

- `*:81` and `*:444` are wildcard binds. Anyone who can reach the server can
  talk to Apache directly and bypass Traefik. Apache is a host process, so
  UFW's INPUT rules *do* apply here (unlike Docker's published ports in
  section 7). Allow 81 and 444 only from the Docker network that Traefik's
  traffic comes from, or bind Apache to one specific address.
- Nobody types `:444` in a browser. The old sites keep their normal URLs
  only once Traefik has a router for each hostname that forwards to Apache:
  plain HTTP to 81, or TLS passthrough to 444.
- Traefik runs in a container, so it reaches Apache through the host's IP or
  the Docker bridge gateway, never through 127.0.0.1 (see the note above).

The step-by-step finish is in [Deployment patterns](35-deployment-patterns.md)
(section 1, "Your fix: Apache moved to 81 and 444"). The original inventory
is in the [case study](21-case-apache-443-dokploy.md).

**Key terms**

| Term | Meaning |
|---|---|
| `bind()` / `listen()` / `accept()` | Claim address:port / start queueing connections / take one from the queue |
| 5-tuple | proto + src IP + src port + dst IP + dst port. Uniquely identifies a connection |
| `EADDRINUSE` | "Address already in use": another socket holds an overlapping address:port |
| `SO_REUSEADDR` | Allows rebinding while old connections sit in `TIME_WAIT`. Doesn't allow two listeners |
| `SO_REUSEPORT` | Lets several processes listen on the same port on purpose (load-spread). Both must opt in |
| Socket activation | systemd holds the port and starts the service on first connection (`systemctl list-sockets`) |

**See it on a real system**

```bash
sudo ss -ltnp                                  # all TCP listeners + owning process
sudo ss -ltnp 'sport = :443'                   # who owns 443
sudo lsof -nP -iTCP:443 -sTCP:LISTEN           # same question, lsof style
systemctl list-sockets                         # ports held by systemd socket units
grep -rn '^\s*Listen' /etc/apache2/ports.conf /etc/apache2/sites-enabled/   # Apache's bind config
```

```
$ sudo ss -ltnp 'sport = :443'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1342,fd=6),("apache2",pid=1341,fd=6),("apache2",pid=1338,fd=6))

$ grep -rn '^\s*Listen' /etc/apache2/ports.conf
/etc/apache2/ports.conf:5:Listen 80
/etc/apache2/ports.conf:8:	Listen 443
/etc/apache2/ports.conf:12:	Listen 443
```

- `*:443` means Apache bound the IPv6 wildcard in dual-stack mode, so it
  holds 443 for IPv4 *and* IPv6. Several `apache2` PIDs share one listening
  socket (the parent and its workers). That's normal.
- `Recv-Q`/`Send-Q` on a `LISTEN` socket mean "connections waiting to be
  accepted" / "maximum queue (backlog)". If `Recv-Q` sits at or near `Send-Q`,
  the app isn't accepting fast enough and new connections get dropped (see
  `nstat -az TcpExtListenOverflows`).
- The two `Listen 443` lines are inside `<IfModule ssl_module>` and
  `<IfModule mod_gnutls.c>` blocks in Ubuntu's default `ports.conf`. Only the
  one for the loaded module applies.

**Hands-on lab (test VM only)**: reproduce "address already in use" and the bind-address rules.

```bash
# 1. Build
sudo ~/netlab.sh up

# 2. A service bound to loopback only (terminal 2)
sudo ip netns exec server python3 -m http.server 8080 --bind 127.0.0.1
# from the client:
sudo ip netns exec client curl -sS -m3 http://10.10.2.20:8080/ || echo "failed"
#   curl: (7) Failed to connect to 10.10.2.20 port 8080 ... Couldn't connect to server   (RST: refused)
sudo ip netns exec server ss -ltn 'sport = :8080'          # 127.0.0.1:8080 - explains it

# 3. A second listener on the SAME port but a DIFFERENT address: allowed (terminal 3)
sudo ip netns exec server python3 -m http.server 8080 --bind 10.10.2.20
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code}\n' http://10.10.2.20:8080/   # 200
sudo ip netns exec server ss -ltnp 'sport = :8080'         # two LISTEN lines

# 4. Break: a wildcard listener on the same port (terminal 4)
sudo ip netns exec server python3 -m http.server 8080 --bind 0.0.0.0
#   OSError: [Errno 98] Address already in use

# 5. Fix: stop the conflicting listeners (Ctrl+C in terminals 2 and 3), then start step 4 again -> works
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Port taken by another service | `bind: Address already in use`, `port is already allocated`, `(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443` (Apache) | `sudo ss -ltnp 'sport = :PORT'` | [Ports inventory playbook](22-playbook-ports-inventory.md) |
| Service bound to 127.0.0.1 | Works on the box (`curl localhost`), refused from outside | `sudo ss -ltn 'sport = :PORT'` | [Site down playbook](25-playbook-site-down.md) |
| App in a container bound to 127.0.0.1 | Traefik 502 / `Connection reset by peer` via the published port | `docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn` | [Containers playbook](26-playbook-containers-k8s.md) |
| systemd socket unit holds the port | Port busy but no daemon process obviously owns it | `systemctl list-sockets` | [Services](07-services-systemd.md) |
| Privileged port as non-root | `bind: Permission denied` on port 80/443 | `getcap /path/to/binary`, run via systemd with `AmbientCapabilities=CAP_NET_BIND_SERVICE` | [Learn Linux](27-learn-linux.md) |

**Why it matters for troubleshooting:** The L1 exit test in your Ops Ladder is
"given a port, name the process, unit, config and logs in five minutes". This
topic covers the first half: `ss -ltnp` gives the process and the bind
address, and the bind address tells you who can reach it. The
[ports inventory playbook](22-playbook-ports-inventory.md) covers the rest
(unit, config file, logs).

**Next step:** once a socket listens, clients connect to it. The TCP handshake
and the connection states tell you how those connections are doing.

### The TCP handshake and connection states

**Level:** [L2 · Mid].

**Concept.** A TCP connection opens with a **three-way handshake** (SYN,
SYN-ACK, ACK) and closes with a **FIN exchange** in each direction. At every
moment each side's socket is in a **state**, and `ss` shows it. You don't need
to memorise the whole state machine. What you need to know is what a *pile-up*
of each state tells you about the system.

```
   client                                              server (LISTEN)
     │ ── SYN (seq=x) ─────────────────────────────────► │
     │   SYN-SENT                                        │ SYN-RECV
     │ ◄──────────────────────── SYN,ACK (seq=y,ack=x+1) │
     │ ── ACK (ack=y+1) ───────────────────────────────► │
     │   ESTABLISHED                                     │ ESTABLISHED  (now in accept queue)
     │ ═══════════════ data both ways ═════════════════  │
     │ ── FIN ─────────────────────────────────────────► │  (client closes first)
     │   FIN-WAIT-1                                      │ CLOSE-WAIT  <- server app must call close()
     │ ◄───────────────────────────────────────── ACK    │
     │   FIN-WAIT-2                                      │
     │ ◄───────────────────────────────────────── FIN    │ LAST-ACK
     │ ── ACK ─────────────────────────────────────────► │ CLOSED
     │   TIME-WAIT (60 s on Linux), then CLOSED          │
```

**What an accumulation of each state means**

| State (`ss` / netstat name) | Normal | A pile-up means | Look at |
|---|---|---|---|
| `SYN-SENT` / `SYN_SENT` | Brief, on the client | Your outbound connections get no answer: firewall drop, wrong IP, destination down | `ss -tn state syn-sent`, capture |
| `SYN-RECV` / `SYN_RECV` | Brief, on the server | SYN flood, or your SYN-ACKs never get ACKed (broken return path, asymmetric routing) | `ss -tn state syn-recv`, `nstat -az TcpExtSyncookiesSent` |
| `ESTAB` / `ESTABLISHED` | Many on busy servers | Steady growth = connection leak or an exhausted pool; clients holding idle keep-alives | `ss -tn state established '( dport = :5432 )' | wc -l` |
| `CLOSE-WAIT` / `CLOSE_WAIT` | Near zero | **Application bug**: the peer closed, your app never called `close()`. Leaks FDs until "Too many open files" | `ss -tnp state close-wait` (shows the guilty process) |
| `FIN-WAIT-2` | Brief | Peer never sends its FIN (often the other side's CLOSE-WAIT bug) | the peer |
| `TIME-WAIT` / `TIME_WAIT` | Thousands are fine | Normal on the side that closes first. Only a problem when it exhausts ephemeral ports toward one destination | `ss -tan state time-wait | wc -l` |
| `LISTEN` with `Recv-Q` near `Send-Q` | Recv-Q ≈ 0 | Accept queue full: the app is too slow to accept; new SYNs dropped | `ss -ltn`, `nstat -az TcpExtListenOverflows` |

**Key terms**

| Term | Meaning |
|---|---|
| SYN / ACK / FIN / RST / PSH | TCP flags: open / acknowledge / graceful close / abort / push data to the app |
| Sequence number | Byte counter. Lets the receiver order data and detect loss |
| Accept queue (backlog) | Completed handshakes waiting for the app's `accept()`. Limited by `listen()` backlog and `net.core.somaxconn` |
| SYN cookies | Kernel defence when the SYN queue overflows (`net.ipv4.tcp_syncookies=1`) |
| `tcp_fin_timeout` | How long an orphaned socket stays in FIN-WAIT-2 (60 s default) |

**See it on a real system**

```bash
ss -s                                               # totals per state
ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn   # count per state
ss -tn state established '( sport = :443 )' | wc -l # connections to my HTTPS listener
sudo ss -tnp state close-wait                       # who leaks connections
ss -tn state syn-sent                               # outbound connects with no answer
```

```
$ ss -tan | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
   2114 TIME-WAIT
    412 ESTAB
     37 CLOSE-WAIT
     11 LISTEN
      3 SYN-SENT
      1 FIN-WAIT-2

$ sudo ss -tnp state close-wait
Recv-Q Send-Q Local Address:Port   Peer Address:Port  Process
1      0      172.18.0.5:41822     172.18.0.9:5432    users:(("python3",pid=3120,fd=27))
1      0      172.18.0.5:41830     172.18.0.9:5432    users:(("python3",pid=3120,fd=31))
```

- 2114 `TIME-WAIT` on a busy proxy is normal.
- 37 `CLOSE-WAIT` pointing at PostgreSQL from one python process: the
  database closed idle connections, and the app's pool never closed its side.
  That's an application/pool bug. Raising limits won't fix it.
- 3 `SYN-SENT`: run it again. If the same destinations stay stuck, something
  is dropping your SYNs.

**Hands-on lab (test VM only)**: create CLOSE-WAIT and SYN-SENT on purpose.

```bash
# 1. Build: a "buggy" server that accepts connections and never closes them (terminal 2)
sudo ~/netlab.sh up
sudo ip netns exec server python3 -c '
import socket, time
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("10.10.2.20", 9000)); s.listen()
leak = [s.accept()[0] for _ in range(5)]
print("accepted 5, never closing"); time.sleep(600)'

# 2. Break: five clients connect and close politely
for i in 1 2 3 4 5; do sudo ip netns exec client nc -z -w1 10.10.2.20 9000; done

# 3. Diagnose
sudo ip netns exec server ss -tnp state close-wait      # 5 sockets, owned by python3
sudo ip netns exec client ss -tn state fin-wait-2       # the client side waits for a FIN that never comes (60 s)

# 4. Fix: the app must close its sockets. Stopping the process frees them (Ctrl+C in terminal 2).
sudo ip netns exec server ss -tn state close-wait       # empty

# 5. SYN-SENT: drop SYNs to port 9001 on the router, then connect
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd tcp dport 9001 drop
sudo ip netns exec client nc -z -w10 10.10.2.20 9001 &
sudo ip netns exec client ss -tn state syn-sent         # stuck in SYN-SENT while SYNs are retransmitted
sudo ip netns exec router nft delete table inet lab
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| CLOSE-WAIT leak | `Too many open files`, app stops accepting, memory grows | `sudo ss -tnp state close-wait`, `ls /proc/PID/fd | wc -l` | [Slow system playbook](23-playbook-slow-system.md) |
| Ephemeral port exhaustion | `Cannot assign requested address` (`EADDRNOTAVAIL`) on connect | `ss -tan state time-wait '( dport = :PORT )' | wc -l` | [Network speed playbook](24-playbook-network-speed.md) |
| Accept queue overflow | Clients see random connect timeouts under load; `ListenOverflows` rising | `nstat -az TcpExtListenOverflows TcpExtListenDrops` | [Slow system playbook](23-playbook-slow-system.md) |
| SYN flood or return-path issue | Many `SYN-RECV`; `TCP: request_sock_TCP: Possible SYN flooding on port ... Sending cookies.` in `dmesg` | `ss -tn state syn-recv | wc -l` | [Site down playbook](25-playbook-site-down.md) |

> Don't "fix" TIME-WAIT with `net.ipv4.tcp_tw_recycle`. It broke clients
> behind NAT and was removed from Linux (4.12). If you really run out of
> ports, use connection pooling/keep-alive, more destination IPs or a wider
> `ip_local_port_range`. `net.ipv4.tcp_tw_reuse` (outbound only) is the safe
> knob.

**Why it matters for troubleshooting:** `ss` state counts are one of the
cheapest signals you have. One command tells you whether an app leaks
connections, a firewall eats SYNs, or a server is overloaded, before you open
a single log file.

**Next step:** the two most common connect failures, "refused" and "timed
out", and what retransmissions look like.

### RST, timeouts and retransmissions

**Level:** [L1 · Junior] for refused vs timed out · [L2 · Mid] for retransmissions and RST forensics.

**Concept.** A connection attempt can end three ways, and each tells you
something different:

| Outcome | What happened on the wire | Client error | Meaning |
|---|---|---|---|
| **Connected** | SYN → SYN-ACK → ACK | (none) | Path *and* listener fine |
| **Refused** | SYN → **RST** | `Connection refused` (`ECONNREFUSED`) | Packet *arrived*. Nothing listens on that IP:port, or a firewall answered with a TCP reset |
| **Timed out** | SYN → (nothing), SYN retried … | `Connection timed out` (`ETIMEDOUT`) | Packet or reply *vanished*: firewall DROP, wrong route, host down, missing return path |
| **No route to host** | SYN → ICMP host-unreachable / admin-prohibited | `No route to host` (`EHOSTUNREACH`) | A router couldn't deliver it, *or* a firewall REJECTs with ICMP. On RHEL, firewalld rejects with an ICMP "prohibited" message (`icmp-host-prohibited` in older versions), so "No route to host" there often just means "firewalld blocked it" |

Linux retries an unanswered SYN with exponential backoff
(`net.ipv4.tcp_syn_retries=6`: 1, 2, 4, 8, 16, 32, 64 s), so a raw `connect()`
can hang for **about 127 seconds** before it fails. That's why tools need
explicit timeouts (`nc -w3`, `curl --connect-timeout 3`).

**After** connecting, lost segments are **retransmitted**. A few
retransmissions are normal. Many of them mean loss or congestion, and every
retransmission costs at least one round-trip of time, often far more (RTO ≥
200 ms). Mid-stream failures:

- `Connection reset by peer` (`ECONNRESET`): the other side, or a middlebox,
  sent RST. Typical causes: the app crashed or closed abruptly, a proxy's
  idle timeout fired, or a firewall/NAT forgot an idle connection.
- `Broken pipe` (`EPIPE`): you wrote to a connection the peer had already
  closed.

**Key terms**

| Term | Meaning |
|---|---|
| RST | Abort a connection immediately. "No such connection / no listener" |
| DROP vs REJECT | Firewall silently discards (client times out) vs answers (RST or ICMP: client fails fast) |
| RTO | Retransmission timeout, derived from measured RTT, min 200 ms on Linux |
| Dup ACK / fast retransmit | Receiver repeats the last ACK; after 3 dup ACKs the sender retransmits without waiting for RTO |
| TCP keepalive | Probes on idle connections (default after 2 h). Apps often set it lower to survive NAT/firewall idle timeouts |

**See it on a real system**

```bash
nstat -az TcpRetransSegs TcpOutSegs TcpExtTCPTimeouts   # retransmitted vs total segments since boot
ss -ti dst 203.0.113.50                                 # per-connection rtt, cwnd, retrans counters
netstat -s | grep -iE 'retrans|reset'                   # legacy counters (net-tools)
sysctl net.ipv4.tcp_syn_retries
```

```
$ ss -ti dst 203.0.113.50
ESTAB 0      0      192.0.2.10:41822   203.0.113.50:443
	 cubic wscale:7,7 rto:204 rtt:3.1/1.2 ato:40 mss:1448 pmtu:1500 rcvmss:1448 advmss:1448 cwnd:10 bytes_sent:1520 bytes_acked:1521 bytes_received:8340 segs_out:14 segs_in:12 data_segs_out:4 data_segs_in:8 send 37.4Mbps lastsnd:1204 lastrcv:1180 lastack:1180 pacing_rate 74.7Mbps delivery_rate 12.1Mbps delivered:5 app_limited rcv_space:14480 rcv_ssthresh:64088 minrtt:2.4
```

- `rtt:3.1/1.2` means a smoothed RTT of 3.1 ms with 1.2 ms variance. `cwnd:10`
  is the congestion window in segments. If the connection had lost packets
  you'd also see `retrans:0/5` (currently unacked / total retransmitted).
- Retransmission rate = `TcpRetransSegs / TcpOutSegs`. Above roughly 1%
  sustained, users will notice.

**Hands-on lab (test VM only)**: the four outcomes, then loss.

```bash
# 1. Build: listener on 80 in the server namespace (terminal 2)
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'

# 2. Refused: closed port
sudo ip netns exec client curl -sv -m5 http://10.10.2.20:81/ 2>&1 | grep -iE 'refused|failed'

# 3. Timed out: firewall DROP
sudo ip netns exec router nft add rule inet lab fwd tcp dport 80 drop
sudo ip netns exec client curl -sSv -m5 http://10.10.2.20/ 2>&1 | tail -1    # curl: (28) ... timed out (-S prints the error despite -s)

# 4. Refused by a firewall: REJECT with TCP reset
sudo ip netns exec router nft flush chain inet lab fwd
sudo ip netns exec router nft add rule inet lab fwd tcp dport 80 reject with tcp reset
sudo ip netns exec client curl -sv -m5 http://10.10.2.20/ 2>&1 | grep -i refused   # looks like "nothing listens"!

# 5. "No route to host" from a firewall (firewalld style)
sudo ip netns exec router nft flush chain inet lab fwd
sudo ip netns exec router nft add rule inet lab fwd tcp dport 80 reject with icmpx type admin-prohibited
sudo ip netns exec client curl -sv -m5 http://10.10.2.20/ 2>&1 | grep -i 'no route'

# 6. Loss: remove the firewall, add 5% loss on the router, watch retransmissions
sudo ip netns exec router nft delete table inet lab
sudo ip netns exec router tc qdisc add dev r-eth1 root netem loss 5%
sudo ip netns exec client nstat -n                       # reset the counter baseline
for i in $(seq 1 20); do sudo ip netns exec client curl -s -o /dev/null http://10.10.2.20/; done
sudo ip netns exec client nstat TcpRetransSegs           # > 0
sudo ip netns exec router tc qdisc del dev r-eth1 root   # fix
```

- Steps 4 and 2 look identical from the client. Only a capture (or the
  firewall's counters) shows whether the RST came from the server or from a
  middlebox. Check the TTL in `tcpdump -v`: a RST with a different TTL from
  the server's normal packets came from somewhere else.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Nothing listening / bound to loopback | `Connection refused` | `sudo ss -ltnp 'sport = :PORT'` on the server | [Site down playbook](25-playbook-site-down.md) |
| Firewall DROP / security group / NACL | `Connection timed out` | `sudo tcpdump -ni any port PORT` on both ends | [Site down playbook](25-playbook-site-down.md) |
| firewalld REJECT on RHEL | `No route to host` although routing is fine | `sudo firewall-cmd --list-all` | section 7 |
| Idle connection killed by NAT/firewall | `Connection reset by peer` after idle periods (DB pools, SSH) | keepalive settings, `conntrack` timeouts | section 7 |
| Packet loss | Slow, stalls, `TcpRetransSegs` rising | `mtr -rwn -c 100 HOST`, `ss -ti` | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting:** "Refused" sends you to the server
(`ss`). "Timed out" sends you to the path (firewalls, routes, capture). Mixing
them up wastes hours. This one distinction is worth more than any tool.

**Next step:** a connection can be healthy and still slow. TCP windows and the
bandwidth-delay product explain why.

### Windows, BDP and throughput

**Level:** [L2 · Mid] to measure it · [L3 · Senior] to tune buffers and congestion control on long links.

**Concept.** TCP may only have a limited amount of unacknowledged data "in
flight": the smaller of the receiver's advertised **window** and the sender's
**congestion window (cwnd)**. The sender then waits for ACKs, which take one
round-trip. So a single connection's maximum throughput is roughly
**window ÷ RTT**, no matter how fast the link is. The amount of data needed to
fill a link is the **bandwidth-delay product (BDP)** = bandwidth × RTT. If the
window is smaller than the BDP, the link sits partly idle. Loss makes it
worse: every loss halves (or reduces) cwnd.

```
 BDP = bandwidth x RTT
   1 Gbit/s x 1 ms   (same datacenter)  = 125 KB
   1 Gbit/s x 50 ms  (cross-country)    = 6.25 MB
   1 Gbit/s x 150 ms (intercontinental) = 18.75 MB

 max single-stream throughput ~ window / RTT
   64 KB window, 50 ms RTT  -> 64*1024*8 / 0.05  ~ 10.5 Mbit/s   (on a 1 Gbit/s link!)
   6 MB window,  50 ms RTT  -> ~ 1 Gbit/s

 with loss p (Mathis approximation): throughput <~ (MSS / RTT) x (1.22 / sqrt(p))
   MSS 1448 B, RTT 50 ms, p = 0.1%  -> ~ 8.9 Mbit/s
```

**Key terms**

| Term | Meaning |
|---|---|
| Receive window (rwnd) | How much the receiver can buffer. Advertised in every ACK; scaled by `wscale` |
| Congestion window (cwnd) | Sender's estimate of what the network can take. Grows until loss |
| BDP | Bandwidth × RTT: bytes in flight needed to fill the pipe |
| Window scaling | TCP option allowing windows > 64 KB. Negotiated in the SYN (`wscale:7`) |
| `tcp_rmem` / `tcp_wmem` | Min/default/max socket buffers. Linux auto-tunes within them (max 6 MB / 4 MB by default) |
| Congestion control | Algorithm adjusting cwnd: `cubic` (default), `bbr` (better on lossy long paths) |

**See it on a real system**

```bash
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.ipv4.tcp_congestion_control
ss -tin dst 203.0.113.50              # rtt, cwnd, wscale, delivery_rate per connection
ping -c 5 203.0.113.50                # RTT -> compute BDP for your link
```

```
$ sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.ipv4.tcp_congestion_control
net.ipv4.tcp_rmem = 4096	131072	6291456
net.ipv4.tcp_wmem = 4096	16384	4194304
net.ipv4.tcp_congestion_control = cubic
```

- A max receive buffer of 6 MB covers roughly 0.5–1 Gbit/s at 50 ms RTT
  (the BDP is 6.25 MB, and part of the buffer goes to kernel bookkeeping, so
  the advertised window is smaller than the buffer). On 10 Gbit/s long-haul
  links that's far too small, and single-stream copies (rsync, backups,
  registry pulls) plateau.

**Hands-on lab (test VM only)**: watch latency and loss cap throughput.

```bash
# 1. Build: iperf3 server in the server namespace (terminal 2)
sudo ~/netlab.sh up
sudo ip netns exec server iperf3 -s -B 10.10.2.20

# 2. Baseline (veths are fast: several Gbit/s)
sudo ip netns exec client iperf3 -c 10.10.2.20 -t 5

# 3. Break: add 50 ms delay each way on the router's links (100 ms RTT)
sudo ip netns exec router tc qdisc add dev r-eth0 root netem delay 50ms
sudo ip netns exec router tc qdisc add dev r-eth1 root netem delay 50ms
sudo ip netns exec client iperf3 -c 10.10.2.20 -t 10          # slow start visible per second

# 4. Make it worse: 1% loss on one side
sudo ip netns exec router tc qdisc change dev r-eth1 root netem delay 50ms loss 1%
sudo ip netns exec client iperf3 -c 10.10.2.20 -t 10          # far lower; "Retr" column > 0

# 5. Compare parallel streams (each has its own cwnd)
sudo ip netns exec client iperf3 -c 10.10.2.20 -t 10 -P 8

# 6. Fix: remove the impairment
sudo ip netns exec router tc qdisc del dev r-eth0 root
sudo ip netns exec router tc qdisc del dev r-eth1 root
```

- `-P 8` getting much more total throughput than one stream is the signature
  of a window/latency/loss limit rather than a bandwidth limit.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Long RTT, small window | One transfer slow, parallel transfers fast; link not saturated | `ss -tin`, `iperf3 -P 1` vs `-P 8` | [Network speed playbook](24-playbook-network-speed.md) |
| Loss on the path | `Retr` in iperf3, `TcpRetransSegs` rising, throughput collapses | `mtr -rwn -c 200 HOST` | [Network speed playbook](24-playbook-network-speed.md) |
| Receiver app slow to read | Window shrinks to 0 ("zero window" in Wireshark) | `ss -tin` (`rcv_space`), app CPU | [Slow system playbook](23-playbook-slow-system.md) |
| Bufferbloat | Latency jumps from 5 ms to 500 ms under load | `ping` while a transfer runs | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting:** "We have a 1 Gbit/s link but the copy
runs at 10 MB/s" is almost never the link. It's RTT, window or loss. The BDP
arithmetic lets you predict the ceiling before you run a single test.

**Next step:** the firewall decides which of these packets are allowed at
all, and with conntrack it remembers every connection.

---

## 7. Firewalls and connection tracking

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions → *IPTABLES Introduction* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Configure Packet Filtering (Firewall)* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 3) KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — System Hardening → *UFW Firewall Basics* ([lesson](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) · 4) Note: [Users, permissions & security](10-users-permissions-security.md), then Docker docs *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)), which KodeKloud doesn't cover · 5) Practice: the labs below, then the packet-filtering challenge in KodeKloud *Linux Challenges* (free, [course](https://kodekloud.com/courses/linux-challenges)).

### Netfilter hooks and tables

**Level:** [L2 · Mid].

**Concept.** Every Linux firewall tool (iptables, nftables, ufw, firewalld,
Docker, kube-proxy) programs the same kernel framework: **netfilter**.
Netfilter offers five **hooks** along a packet's path. Rules attached to a hook
see every packet passing that point. Where a packet goes depends on the
routing decision: packets *for this host* go through INPUT, packets *being
routed through* (to containers, VMs, other hosts) go through FORWARD. This
diagram is the key to "why didn't my rule match?":

```
        NIC in
          │
   ┌──────▼───────┐   raw (notrack) -> conntrack -> mangle -> nat: DNAT (Docker -p, NodePort)
   │  PREROUTING  │
   └──────┬───────┘
          │ routing decision: is the (possibly DNAT-ed) destination this host?
     yes  │                         no
   ┌──────▼──────┐            ┌──────▼──────┐
   │    INPUT    │ ufw rules  │   FORWARD   │ Docker/K8s/router traffic: DOCKER-USER, DOCKER-*,
   └──────┬──────┘            └──────┬──────┘ KUBE-*, ufw "route" rules
          │                          │
    local process                    │
          │                          │
   ┌──────▼──────┐                   │
   │   OUTPUT    │ (locally generated; nat OUTPUT does DNAT for local connections)
   └──────┬──────┘                   │
          └────────────┬─────────────┘
                ┌──────▼───────┐
                │ POSTROUTING  │  nat: SNAT / MASQUERADE (containers going out)
                └──────┬───────┘
                       ▼  NIC out
```

**Key terms**

| Term | Meaning |
|---|---|
| Hook | PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING |
| Table | Group of chains by purpose: `raw`, `mangle`, `nat`, `filter`, `security` |
| Chain | Ordered list of rules. Built-in chains attach to hooks; user chains are jumped to |
| Policy | Verdict when no rule matches (ACCEPT or DROP) |
| Verdict / target | ACCEPT, DROP, REJECT, RETURN, jump to a chain, DNAT, SNAT, MASQUERADE |
| Counters | Packets/bytes that matched each rule. Your best debugging aid |

**See it on a real system**

```bash
sudo iptables -L -n -v --line-numbers          # filter table with counters
sudo iptables -t nat -L -n -v                  # nat table
sudo iptables -S FORWARD                       # rules as commands (easy to read and diff)
sudo nft list ruleset | less                   # everything, nftables view (includes iptables-nft rules)
iptables -V                                    # "(nf_tables)" = iptables-nft backend (Ubuntu 22.04+ default)
```

```
$ sudo iptables -L FORWARD -n -v --line-numbers
Chain FORWARD (policy DROP 0 packets, 0 bytes)
num   pkts bytes target                    prot opt in     out     source       destination
1     184K  210M DOCKER-USER               all  --  *      *       0.0.0.0/0    0.0.0.0/0
2     184K  210M DOCKER-FORWARD            all  --  *      *       0.0.0.0/0    0.0.0.0/0
3        0     0 ufw-before-logging-forward all --  *      *       0.0.0.0/0    0.0.0.0/0
...
```

- The FORWARD policy is DROP (Docker sets that), and Docker's chains come
  **before** UFW's. Traffic to containers is decided by Docker's rules first.
  Chain names differ slightly between Docker versions (older versions jump to
  `DOCKER`, `DOCKER-ISOLATION-STAGE-1` directly).

**Hands-on lab (test VM only)**: prove which hook sees what.

```bash
# 1. Build: counters on INPUT and FORWARD in the router namespace
sudo ~/netlab.sh up
sudo ip netns exec router nft add table inet watch
sudo ip netns exec router nft 'add chain inet watch in  { type filter hook input   priority 0; }'
sudo ip netns exec router nft 'add chain inet watch fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet watch in  icmp type echo-request counter
sudo ip netns exec router nft add rule inet watch fwd icmp type echo-request counter

# 2. Ping the router itself, then ping THROUGH it
sudo ip netns exec client ping -c3 10.10.1.1
sudo ip netns exec client ping -c5 10.10.2.20
sudo ip netns exec router nft list table inet watch     # input: 3 packets, forward: 5 packets

# 3. Break: a DROP on INPUT does NOT stop forwarded traffic
sudo ip netns exec router nft add rule inet watch in icmp type echo-request drop
sudo ip netns exec client ping -c2 -W1 10.10.1.1        # fails
sudo ip netns exec client ping -c2 10.10.2.20           # still works: different hook

# 4. Clean up
sudo ip netns exec router nft delete table inet watch
```

- This is exactly the UFW-vs-Docker situation: a rule in INPUT can't see
  traffic that's DNAT-ed and forwarded to a container.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Rule in the wrong hook/chain | Rule exists, counter stays 0, traffic passes or is blocked anyway | `sudo iptables -L -n -v` / `sudo nft list ruleset` (counters) | next topic |
| Rule order | An earlier ACCEPT/DROP matches first | `sudo iptables -L CHAIN -n -v --line-numbers` | next topic |
| Two tools fighting (ufw + firewalld + scripts + Docker) | Rules vanish or reappear after reloads | `systemctl status ufw firewalld nftables netfilter-persistent` | next topic |

**Why it matters for troubleshooting:** When a packet times out and you
suspect the firewall, the question is "which hook does this packet traverse,
and which rule there matched it?" Counters and the diagram answer that.

**Next step:** the tools that write these rules (iptables, nftables, ufw,
firewalld) and how to use them without locking yourself out.

### iptables, nftables, ufw and firewalld

**Level:** [L1 · Junior] for ufw and reading rules · [L2 · Mid] for nftables and rule-order debugging.

**Concept.** These are four front-ends to the same netfilter engine. Use one
per host, know which one owns the rules, and read the live ruleset with
`nft list ruleset` regardless of which tool wrote it.

| Tool | What it is | Where you meet it | Read state | Persistence |
|---|---|---|---|---|
| iptables (`iptables-nft`) | Classic rule syntax, now translated to nftables underneath | Docker, kube-proxy (iptables mode), old scripts | `iptables -S`, `iptables -L -n -v` | `netfilter-persistent` / `iptables-save` |
| nftables (`nft`) | Modern native syntax: tables, sets, maps, one tool for v4+v6 | RHEL 8+ backend, new setups | `nft list ruleset` | `/etc/nftables.conf` + `nftables.service` |
| ufw | Ubuntu's simple front-end generating iptables rules | Ubuntu servers | `ufw status verbose`, `ufw show added` | `/etc/ufw/*.rules`, `ufw.service` |
| firewalld | Zone-based daemon (D-Bus), nftables backend | RHEL, Rocky, Fedora | `firewall-cmd --list-all` | `--permanent` + `--reload` |

> **Lock-out warnings.** These lines have cut off many SSH sessions:
>
> - `sudo iptables -F` flushes every rule. If the chain *policy* is DROP,
>   you're instantly locked out. It also wipes Docker's and Kubernetes' rules,
>   so container networking breaks until Docker/kube-proxy recreates them.
>   **Safer:** back up first (`sudo iptables-save > ~/fw-$(date +%F-%H%M).rules`),
>   then delete only the one rule you mean (`sudo iptables -D CHAIN NUM`).
> - `sudo ufw enable` over SSH without allowing SSH first. **Safer:**
>   `sudo ufw allow OpenSSH` *before* `ufw enable`, and keep console access
>   (IPMI/iDRAC, hypervisor console) available.
> - For risky changes on a remote box, schedule an automatic rollback first:
>   `sudo systemd-run --on-active=5min /usr/sbin/ufw disable`. Cancel it with
>   `systemctl stop` on the transient timer when everything works.

**Key terms**

| Term | Meaning |
|---|---|
| ufw default policies | `deny (incoming), allow (outgoing), deny (routed)` on a typical server |
| ufw app profile | Named port set in `/etc/ufw/applications.d/` (`OpenSSH`, `Apache Full`) |
| firewalld zone | Trust level bound to interfaces/sources (`public`, `internal`, `trusted`) |
| `--permanent` (firewalld) | Write to config. Without it a change is runtime-only and lost on reload |
| nft set | Named list of addresses/ports matched in one rule (`ip saddr @admins`) |

**See it on a real system**

```bash
sudo ufw status verbose                       # Ubuntu
sudo ufw status numbered                      # with rule numbers (for "ufw delete NUM")
sudo firewall-cmd --state && sudo firewall-cmd --list-all    # RHEL family
sudo nft list ruleset | grep -c .             # how much is there at all
sudo journalctl -k --since '10 min ago' | grep -E 'UFW BLOCK|nft|REJECT' | tail
```

```
$ sudo ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere
80,443/tcp (Apache Full)   ALLOW IN    Anywhere
3000/tcp                   ALLOW IN    192.0.2.0/24
22/tcp (OpenSSH (v6))      ALLOW IN    Anywhere (v6)

$ sudo journalctl -k | grep 'UFW BLOCK' | tail -1
Oct 03 10:41:07 web01 kernel: [UFW BLOCK] IN=ens18 OUT= MAC=bc:24:11:4a:2b:1c:00:1a:2b:3c:4d:5e:08:00 SRC=198.51.100.23 DST=192.0.2.10 LEN=60 TOS=0x00 PREC=0x00 TTL=52 ID=40211 DF PROTO=TCP SPT=51544 DPT=3000 WINDOW=64240 RES=0x00 SYN URGP=0
```

- The Dokploy UI (3000) is allowed only from the admin subnet. The log line
  proves an outside host's SYN to 3000 was blocked: `SRC`, `DPT=3000`, `SYN`.
- Ubuntu's iptables uses the `nf_tables` backend, so `nft list ruleset` also
  shows ufw's and Docker's rules (translated).

**Hands-on lab (test VM only)**: ufw with logging, a rule-order mistake, and a fix.

```bash
# 1. Build (on the VM itself, with console access available)
sudo ufw allow OpenSSH
sudo ufw default deny incoming
sudo ufw logging on
sudo ufw --force enable
python3 -m http.server 8000 &                       # a test service on all addresses

# 2. Break: from ANOTHER machine, curl http://VM_IP:8000/ -> times out
sudo journalctl -k -f | grep --line-buffered 'DPT=8000'   # watch the block happen

# 3. Fix with a scoped rule, then check order and counters
sudo ufw allow from 192.0.2.0/24 to any port 8000 proto tcp
sudo ufw status numbered
sudo iptables -L ufw-user-input -n -v               # counters on ufw's generated rules

# 4. Order trap: insert a deny ABOVE the allow
sudo ufw insert 1 deny 8000/tcp
sudo ufw status numbered                            # deny is now [1] -> allow never reached
sudo ufw delete 1                                   # remove it

# 5. Clean up
kill %1; sudo ufw delete allow from 192.0.2.0/24 to any port 8000 proto tcp
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Port blocked by host firewall | Timeout from outside, works locally; `[UFW BLOCK]` with your `DPT` | `sudo journalctl -k | grep 'UFW BLOCK'` | [Site down playbook](25-playbook-site-down.md) |
| firewalld runtime change lost | Worked until `firewall-cmd --reload` or reboot | `sudo firewall-cmd --list-all --permanent` | [Security](10-users-permissions-security.md) |
| IPv6 forgotten | Works over IPv4, blocked or wide open over IPv6 | `sudo ufw status` (v6 lines), `IPV6=yes` in `/etc/default/ufw` | section 13 |
| Rules wiped by a flush | All containers lose network; Docker rules gone | `sudo iptables -t nat -S | grep -c DOCKER` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting:** "Timed out" plus "works from the
server itself" almost always means a host or network firewall. Knowing which
tool owns the rules (and how to read logs and counters) turns a guessing game
into a two-minute check.

**Next step:** modern firewalls are *stateful*. They remember connections.
That memory (conntrack) explains why one "allow established" rule matters so
much, and why NAT boxes fall over under load.

### Conntrack and stateful rules

**Level:** [L2 · Mid] · sizing conntrack on NAT boxes is [L3 · Senior].

**Concept.** The kernel's **connection tracking** (conntrack) records every
flow it sees: the 5-tuple, state and any NAT translation. Stateful rules use
it: "allow NEW connections to 443, and allow all packets belonging to
ESTABLISHED or RELATED connections". Without the established rule, replies to
your own outbound connections would be dropped. NAT depends on conntrack
completely: the reply translation comes from the stored entry. The table has
a size limit. When it's full, **new connections are dropped** and the kernel
logs it.

| ct state | Meaning |
|---|---|
| NEW | First packet of a flow (a SYN for TCP) |
| ESTABLISHED | Packets of a flow already seen in both directions |
| RELATED | New flow related to an existing one (ICMP errors, FTP data) |
| INVALID | Doesn't fit any known flow (often asymmetric routing or out-of-window). Usually dropped |

**Key terms**

| Term | Meaning |
|---|---|
| `nf_conntrack_max` | Table size limit |
| `nf_conntrack_count` | Current entries |
| `nf_conntrack_tcp_timeout_established` | How long an idle established TCP entry lives (432000 s = 5 days) |
| `[ASSURED]` | Entry has seen traffic both ways; won't be evicted early |
| `ct state established,related accept` | The standard stateful rule (nftables syntax) |

**See it on a real system**

```bash
cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max
sudo conntrack -S                               # per-CPU stats: insert_failed, drop, early_drop
sudo conntrack -L -p tcp --dport 443 | head     # entries for HTTPS
sudo conntrack -L -s 198.51.100.23              # everything from one client
sudo dmesg -T | grep -i conntrack               # "nf_conntrack: table full, dropping packet"
```

```
$ cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max
261988
262144

$ sudo dmesg -T | grep -i conntrack | tail -2
[Sat Oct  3 10:52:11 2026] nf_conntrack: nf_conntrack: table full, dropping packet
[Sat Oct  3 10:52:11 2026] nf_conntrack: nf_conntrack: table full, dropping packet
```

- 261,988 of 262,144: the table is full, so new connections are randomly
  dropped, which looks like intermittent timeouts. Short term, raise
  `net.netfilter.nf_conntrack_max` (it costs memory). Long term, find what
  creates so many flows (a scan, a retry storm, very short-lived connections,
  UDP floods).

**Hands-on lab (test VM only)**: a stateless mistake and its stateful fix.

```bash
# 1. Build: router FORWARD policy drop, allow only NEW tcp/80 client->server
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20     # terminal 2
sudo ip netns exec router nft add table inet fw
sudo ip netns exec router nft 'add chain inet fw fwd { type filter hook forward priority 0; policy drop; }'
sudo ip netns exec router nft add rule inet fw fwd iifname "r-eth0" tcp dport 80 accept

# 2. Break: the SYN passes, the server's SYN-ACK (going the other way) is dropped
sudo ip netns exec client curl -s -m3 http://10.10.2.20/ || echo "timed out"
sudo ip netns exec server tcpdump -ni s-eth0 -c 4 tcp port 80     # SYN in, SYN-ACK out, repeated (retransmits)

# 3. Fix: allow return traffic of tracked connections (put it first)
sudo ip netns exec router nft insert rule inet fw fwd ct state established,related accept
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code}\n' http://10.10.2.20/   # 200
sudo ip netns exec router conntrack -L 2>/dev/null | grep dport=80
sudo ip netns exec router nft list chain inet fw fwd

# 4. Clean up
sudo ip netns exec router nft delete table inet fw
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Conntrack table full | Random new-connection timeouts under load; `table full, dropping packet` | `sudo dmesg -T | grep conntrack`, `conntrack -S` | [Network speed playbook](24-playbook-network-speed.md) |
| Missing established/related rule | Outbound works one way only; SYN-ACKs dropped | `nft list ruleset`, capture | [02-network.md](02-network.md) |
| Asymmetric routing | Packets marked INVALID and dropped | `sudo conntrack -S` (invalid), `ip route get` both sides | section 4 |
| Idle timeout on a middlebox | Long-idle DB/SSH connections reset | keepalive settings on the app | [Site down playbook](25-playbook-site-down.md) |

**Why it matters for troubleshooting:** Every NAT gateway, Docker host and
Kubernetes node is a conntrack box. "Intermittent timeouts only at peak" on
such a host means: check conntrack first.

**Next step:** the firewall interaction that bites every Docker user: why
`ufw deny` doesn't protect a published container port, and where container
filtering belongs.

### Docker and the firewall

**Level:** [L2 · Mid] · a DOCKER-USER policy for the whole fleet is [L3 · Senior].

**Concept.** For a published port, Docker DNATs incoming packets in
PREROUTING to the container's IP and accepts them in FORWARD (via its own
chains). UFW's normal rules live on INPUT. So **UFW never sees traffic to
published container ports**, and `ufw deny 8080` doesn't block
`-p 8080:80`. Docker gives you one chain for your own rules, **DOCKER-USER**,
which is evaluated before Docker's accept rules. The cleanest protection is
not to publish at all: put services behind Traefik on a Docker network, and
publish test ports on loopback only (`127.0.0.1:18000:8000`).

```
 internet ──► ens18:8080 ──PREROUTING DNAT──► 172.18.0.7:80
                                │
                     FORWARD:   DOCKER-USER  (your filters here: subnet allow-lists)
                                DOCKER-FORWARD / DOCKER ... ACCEPT
                     INPUT:     ufw rules  <- never consulted for this packet
```

**Key terms**

| Term | Meaning |
|---|---|
| DOCKER-USER | Filter chain Docker creates and never touches. Your rules go here |
| `--ctorigdstport` | Match the *original* destination port (before DNAT). Needed in DOCKER-USER because the packet's port is already rewritten |
| `127.0.0.1:HOST:CONTAINER` | Publish on loopback only: reachable from the host, not the network |
| `"iptables": false` | daemon.json option that stops Docker managing rules. Breaks container networking unless you replace everything by hand. Avoid it |

**See it on a real system**

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'      # what is published, and on which address
sudo ss -ltnp | grep docker-proxy                      # host side of each published port
sudo iptables -S DOCKER-USER                           # your container filters (default: empty on Docker 28.2.2+, one RETURN rule on older)
sudo iptables -t nat -S DOCKER                         # the DNAT rules
```

```
$ docker ps --format 'table {{.Names}}\t{{.Ports}}'
NAMES             PORTS
dokploy-traefik   0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:443->443/udp, [::]:443->443/udp
grafana-test      127.0.0.1:13000->3000/tcp
legacy-api        0.0.0.0:8080->8000/tcp, [::]:8080->8000/tcp
```

- Traefik publishes 80, 443/tcp and 443/udp (HTTP/3). That's intended.
- `grafana-test` is on loopback only. Good: reach it through an SSH tunnel.
- `legacy-api` is open to the world on 8080 even if UFW says deny. Fix it by
  removing the publish (route via Traefik), binding to loopback, or filtering
  in DOCKER-USER.

**Hands-on lab (test VM only, Docker installed)**: see the bypass, then fix it two ways.

```bash
# 1. Build
sudo ufw allow OpenSSH && sudo ufw default deny incoming && sudo ufw --force enable
docker run -d --name web -p 8080:80 nginx:alpine
sudo ufw deny 8080/tcp

# 2. Break (observe): from ANOTHER machine -> curl -s -o /dev/null -w '%{http_code}\n' http://VM_IP:8080/   => 200 despite "deny"

# 3. Fix A (best for test ports): publish on loopback only
docker rm -f web
docker run -d --name web -p 127.0.0.1:8080:80 nginx:alpine
sudo ss -ltn 'sport = :8080'                  # 127.0.0.1:8080 only

# 4. Fix B (when it must be published): allow only the admin subnet in DOCKER-USER
docker rm -f web && docker run -d --name web -p 8080:80 nginx:alpine
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 8080 ! -s 192.0.2.0/24 -j DROP
sudo iptables -L DOCKER-USER -n -v            # counters climb when outsiders try

# 5. Clean up
docker rm -f web
sudo iptables -D DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 8080 ! -s 192.0.2.0/24 -j DROP
sudo ufw delete deny 8080/tcp
```

> DOCKER-USER rules added by hand don't survive a reboot. Make them persistent
> with a small systemd unit that runs after `docker.service`, or with your
> configuration management (Ansible). Test the reboot on the lab VM.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Published port exposed despite UFW | External scan shows the port open | `docker ps --format '{{.Names}} {{.Ports}}'` | [Ports inventory playbook](22-playbook-ports-inventory.md) |
| Containers lose network after a firewall reload/flush | No outbound, published ports dead | `sudo iptables -t nat -S | grep -c DOCKER`; restart Docker in a window | [Containers playbook](26-playbook-containers-k8s.md) |
| firewalld zone blocks docker0 (RHEL) | Containers can't reach the host or each other | `sudo firewall-cmd --get-active-zones` | [Learn Docker](30-learn-docker.md) |
| Host service unreachable from a container | Container → host IP:PORT times out (UFW INPUT drops 172.x sources) | `sudo journalctl -k | grep 'UFW BLOCK.*SRC=172.'` | [Apache/Dokploy case](21-case-apache-443-dokploy.md) |

Reference: [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).

**Why it matters for troubleshooting:** During the Apache → Dokploy migration
you'll publish test ports, move Apache to a private port and let Traefik
reach it. Each of those touches this interaction. If you get it wrong, either
the world sees your test service, or Traefik can't reach Apache (502).

**Next step:** with packets flowing, the next failure is the most famous one.
DNS is next.

---

## 8. DNS in depth

> 📚 **Study path:** 1) KodeKloud: *Demystifying DNS* — DNS as a System (Resolvers, Walking the DNS Tree, TTL) → Record Types → Miscellaneous → *Troubleshooting DNS* ([course](https://kodekloud.com/courses/demystifying-dns), [lesson](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page)) · 2) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* (14 min, [YouTube](https://www.youtube.com/watch?v=9nCIjLlLVzY)) · 3) Note: [DNS reference](08-dns.md); KodeKloud skips `getent` vs `dig` and systemd-resolved, so also read Julia Evans on [getaddrinfo](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/) and the [Arch Wiki on systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved) · 4) Practice: [Mess With DNS](https://messwithdns.net/) and the "break DNS three ways" lab below · 5) Kubernetes: *Certified Kubernetes Administrator (CKA)* — Networking → *CoreDNS in Kubernetes* ([lesson](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page)) when you reach the last topic.

### How a name gets resolved

**Level:** [L1 · Junior].

**Concept.** DNS is a distributed, cached, hierarchical database. Your
machine runs a **stub resolver**. It doesn't know any answers; it asks a
**recursive resolver** (company DNS, ISP, 1.1.1.1). With an empty cache, the
recursive resolver walks the tree from the top: the **root** servers say
"ask the `.com` servers", the **TLD** servers say "ask example.com's name
servers", and the **authoritative** servers for example.com give the real
answer. Every answer carries a **TTL** and is cached at every level on the
way back, so most lookups never go past the first cache.

```
 app ── getaddrinfo() ──► /etc/hosts? ──no──► stub 127.0.0.53 (systemd-resolved, cache)
                                                    │
                                                    ▼
                                      recursive resolver 192.0.2.53 (cache)
                                        │ 1. "."  root       -> "com. is served by a.gtld-servers.net ..."
                                        │ 2. com. TLD        -> "example.com. is served by ns1.example.com ..."
                                        │ 3. ns1.example.com -> "app.example.com. 300 IN A 203.0.113.10"  (aa flag)
                                                    ▼
                         answer + TTL cached at each level, returned to the app
```

**Key terms**

| Term | Meaning |
|---|---|
| Stub resolver | The client side (glibc, systemd-resolved stub). Sends queries with "recursion desired" (`rd`) |
| Recursive resolver | Does the walk for you and caches (`ra` flag = recursion available) |
| Authoritative server | Holds the zone data. Answers carry the `aa` flag |
| Zone / delegation | A part of the tree managed together / handing a subtree to other servers with NS records |
| Glue | A/AAAA records for name servers inside the zone they serve (ns1.example.com for example.com) |
| FQDN | Fully qualified name. The trailing dot (`app.example.com.`) means "don't append search domains" |
| Response codes | `NOERROR`, `NXDOMAIN` (name doesn't exist), `SERVFAIL` (resolver failed), `REFUSED` (not allowed to ask) |

**See it on a real system**

```bash
dig app.example.com                       # via your configured resolver (status, flags, SERVER line)
dig +trace app.example.com                # do the walk yourself from the root
dig NS example.com +short                 # which servers are authoritative
dig @ns1.example.com app.example.com +norecurse   # ask the authority directly: the truth
```

```
$ dig app.example.com

; <<>> DiG 9.18.28-0ubuntu0.24.04.1-Ubuntu <<>> app.example.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 40211
;; flags: qr rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 65494
;; QUESTION SECTION:
;app.example.com.		IN	A

;; ANSWER SECTION:
app.example.com.	300	IN	CNAME	lb.example.com.
lb.example.com.		300	IN	A	203.0.113.10

;; Query time: 24 msec
;; SERVER: 127.0.0.53#53(127.0.0.53) (UDP)
;; WHEN: Sat Oct 03 10:12:44 UTC 2026
;; MSG SIZE  rcvd: 78
```

- `status: NOERROR` with an ANSWER section means it resolved. `flags: qr rd ra`
  shows a response (`qr`) where recursion was desired and available. There's
  no `aa`, so this came from a cache/recursive resolver, not the authority.
- `SERVER: 127.0.0.53` means you asked the local systemd-resolved stub. The
  `udp: 65494` EDNS size is its signature. To see the real upstream, use
  `resolvectl status`.
- The CNAME chain (`app` → `lb` → IP) is followed automatically.

```
$ dig +trace app.example.com | grep -E 'IN\s+(NS|A)\s|Received'
.			518400	IN	NS	a.root-servers.net.
;; Received 239 bytes from 127.0.0.53#53(127.0.0.53) in 0 ms
com.			172800	IN	NS	a.gtld-servers.net.
;; Received 1170 bytes from 198.41.0.4#53(a.root-servers.net) in 20 ms
example.com.		172800	IN	NS	ns1.example.com.
;; Received 340 bytes from 192.5.6.30#53(a.gtld-servers.net) in 28 ms
app.example.com.	300	IN	A	203.0.113.10
;; Received 60 bytes from 198.51.100.53#53(ns1.example.com) in 12 ms
```

- Each block is one step of the walk. If the trace stops at the TLD step with
  an error, the delegation (NS records at the registrar) is broken. The zone
  itself might be fine.

**Hands-on lab (test VM only)**: walk the tree yourself and compare cache vs authority.

```bash
# 1. The walk
dig +trace www.wikipedia.org

# 2. Cache vs authority: the TTL counts down in a cache, never at the authority
dig +noall +answer www.wikipedia.org;  sleep 5;  dig +noall +answer www.wikipedia.org
AUTH=$(dig +short NS wikipedia.org | head -1)
dig @"$AUTH" www.wikipedia.org +norecurse +noall +answer +comments | grep -E 'flags|IN'
#   flags include "aa" and the TTL is the full configured value

# 3. Ask a server that refuses recursion for others (most authorities): status REFUSED or no answer
dig @"$AUTH" www.example.org +norecurse
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Record really missing / typo | `status: NXDOMAIN` everywhere | `dig @AUTH NAME +norecurse` | [DNS reference](08-dns.md) |
| Broken delegation (NS at registrar wrong) | `+trace` stops at the TLD; `SERVFAIL` | `dig +trace NAME`, `dig NS DOMAIN @a.gtld-servers.net` | [Site down playbook](25-playbook-site-down.md) |
| DNSSEC validation failure | `SERVFAIL` from validating resolvers, works with `+cd` | `dig NAME +dnssec`, `dig NAME +cd` | [DNS reference](08-dns.md) |
| Resolver unreachable | `communications error to ...: timed out`, `no servers could be reached` | `resolvectl status`, `sudo tcpdump -ni any port 53` | next topics |

**Why it matters for troubleshooting:** "DNS is broken" can mean the
authority has the wrong data, the delegation is wrong, a cache is stale, or
your local resolver can't reach upstream. Each has a different owner (you,
the registrar, time, the network team). `dig @authority` versus plain `dig`
tells you which one it is.

**Next step:** the records themselves. Each type has its own traps.

### Record types you must know

**Level:** [L1 · Junior].

**Concept.** A DNS record is `NAME TTL CLASS TYPE DATA`. These types cover
99% of DevOps work:

| Type | Example data | Used for | Trap |
|---|---|---|---|
| A | `203.0.113.10` | Name → IPv4 | Several A records = round-robin, not health-checked |
| AAAA | `2001:db8::10` | Name → IPv6 | A broken AAAA makes clients try IPv6 first and stall (section 13) |
| CNAME | `lb.example.com.` | Alias to another *name* | Can't coexist with any other record at that name; not allowed at the zone apex (`example.com` itself) |
| MX | `10 mail.example.com.` | Mail server, lower preference first | Must point to a name with A/AAAA, not a CNAME or IP |
| TXT | `"v=spf1 ip4:192.0.2.0/24 -all"` | SPF, DKIM, DMARC, ACME `_acme-challenge`, domain verification | Strings > 255 chars must be split; multiple SPF records = SPF fails |
| NS | `ns1.example.com.` | Which servers are authoritative for a zone or subzone | Must match at the parent (registrar) and in the zone |
| SOA | `ns1.example.com. hostmaster.example.com. 2026100301 7200 3600 1209600 300` | Zone metadata: serial, timers, **negative TTL** | Forget to bump the serial = secondaries never update |
| PTR | `web01.example.com.` (at `10.2.0.192.in-addr.arpa.`) | Reverse lookup IP → name | Missing PTR: mail rejected, slow SSH logins with `UseDNS yes`, odd logs |
| SRV | `10 50 5060 sip1.example.com.` (priority weight port target) | Service discovery: AD/LDAP, SIP, Kubernetes named ports | Name format is `_service._proto.name` |
| CAA | `0 issue "letsencrypt.org"` | Which CAs may issue certificates | If CAA records exist and don't list your CA, issuance **fails** |

SOA fields in order: primary name server, admin mailbox (first dot = @),
**serial**, refresh, retry, expire, and **minimum**. The last one is the TTL
for negative answers.

**Key terms**

| Term | Meaning |
|---|---|
| Apex / root of zone | The zone name itself (`example.com`). No CNAME here; providers offer ALIAS/ANAME/flattening |
| RRset | All records with the same name and type. They share a TTL |
| Wildcard | `*.example.com` matches names that don't exist explicitly |
| Reverse zone | `in-addr.arpa` (IPv4) / `ip6.arpa` (IPv6). Usually managed by whoever owns the IP block |

**See it on a real system**

```bash
dig +short example.com A
dig +short example.com AAAA
dig +short example.com MX
dig +short example.com TXT
dig +short example.com NS
dig example.com SOA +noall +answer
dig +short -x 192.0.2.10                       # PTR (reverse)
dig +short _ldap._tcp.corp.example.com SRV     # SRV (AD domain controllers)
dig +short example.com CAA
```

```
$ dig example.com SOA +noall +answer
example.com.		3600	IN	SOA	ns1.example.com. hostmaster.example.com. 2026100301 7200 3600 1209600 300

$ dig +short example.com CAA
0 issue "letsencrypt.org"
0 iodef "mailto:security@example.com"
```

- Serial `2026100301` is in date format (YYYYMMDDnn). The negative-cache TTL
  is the last field, `300`: a "doesn't exist" answer is cached for 5 minutes.
- CAA allows only Let's Encrypt. A certificate request to another CA fails.

**Hands-on lab (test VM only + browser)**: Mess With DNS.

[Mess With DNS](https://messwithdns.net/) gives you a real subdomain and a
live view of every query that reaches its authoritative server.

1. Open the site and get your subdomain (shown at the top; call it SUB below).
2. Create an `A` record `www.SUB` → `192.0.2.10`, then run
   `dig www.SUB +noall +answer` on your VM. Watch the query arrive in the
   site's live log, from your resolver's IP, not yours.
3. Create a `CNAME` `app.SUB` → `www.SUB`. Dig `app.SUB` and see the chain.
4. Try to create another record next to the CNAME at the same name and read
   the error. That's the "CNAME can't coexist" rule.
5. Create `TXT`, `MX` and `CAA` records and query each type with `dig`.
6. Do the site's "weird" experiments. Pay special attention to the one on
   negative caching (next topic).

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| CNAME at apex / next to other records | Provider refuses, or random breakage of MX/TXT | `dig DOMAIN ANY` (often limited), check each type | [DNS reference](08-dns.md) |
| CAA blocks Let's Encrypt | Traefik/certbot log: `CAA record for DOMAIN prevents issuance` | `dig DOMAIN CAA` (and parent domains) | section 10 ACME |
| Missing PTR | SMTP rejected, `UseDNS` delay on SSH | `dig -x IP` | [SSH](09-ssh-remote-access.md) |
| SOA serial not bumped | Secondary DNS servers return old data | `dig @ns1 DOMAIN SOA` vs `dig @ns2 DOMAIN SOA` | [DNS reference](08-dns.md) |

**Why it matters for troubleshooting:** Many "DNS outages" are really
record-type mistakes: a CNAME where an A was needed, a stale secondary, a CAA
record nobody remembered. Query the exact type with `dig` instead of assuming.

**Next step:** TTLs and negative caching explain "I fixed the record but it
still fails".

### TTL and negative caching

**Level:** [L2 · Mid] · planning TTLs for a cut-over is [L3 · Senior].

**Concept.** Every answer has a **TTL** (seconds). Each cache keeps it for
that long and counts down. Changes therefore propagate per cache, not
instantly: someone who looked the name up one minute before your change keeps
the old answer for up to TTL − 60 seconds. **Negative caching**: a
`NXDOMAIN`/"no such record" answer is cached too, for the SOA's minimum field
(capped by the SOA's own TTL). If anyone, including you or a health check,
looked the name up *before* you created the record, they keep getting
"doesn't exist" until that negative TTL runs out.

```
 t=0     dig new.example.com   -> NXDOMAIN (cached for 300 s = SOA minimum)
 t=60    you create new.example.com A 203.0.113.20
 t=61    dig new.example.com   -> still NXDOMAIN from the cache   ("DNS is broken!")
 t=300   cache expires         -> A 203.0.113.20
```

Caches you may have to think about, from the app outward: the app itself
(Java caches positive answers for 30 s by default and *forever* with a
security manager; some apps resolve only at startup, nginx `proxy_pass` with
a hostname resolves once at load), systemd-resolved, the company recursive
resolver, and any forwarding resolvers in between.

**Key terms**

| Term | Meaning |
|---|---|
| TTL | Seconds a record may be cached |
| Negative caching | Caching of NXDOMAIN/NODATA, duration from the SOA (RFC 2308) |
| NODATA | Name exists but has no record of this type: `NOERROR` with 0 answers |
| Propagation | Not a push: just old cache entries expiring everywhere |
| TTL lowering | Before a migration, lower the TTL (e.g. to 60) at least one *old* TTL in advance |

**See it on a real system**

```bash
dig +noall +answer app.example.com            # TTL now
sleep 10; dig +noall +answer app.example.com  # TTL 10 lower = served from cache
dig doesnotexist.example.com                  # NXDOMAIN + SOA in AUTHORITY = the negative TTL
resolvectl statistics                         # resolved's cache size, hits, misses
sudo resolvectl flush-caches                  # clear the LOCAL cache only (not the company resolver)
```

```
$ dig doesnotexist.example.com
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 5512
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 1, ADDITIONAL: 1
...
;; AUTHORITY SECTION:
example.com.		300	IN	SOA	ns1.example.com. hostmaster.example.com. 2026100301 7200 3600 1209600 300
```

- `NXDOMAIN` comes with the zone's SOA. The TTL on that SOA line (counting
  down from 300) is how long this "no" stays cached.

**Hands-on lab (test VM only + browser)**: reproduce the negative-caching trap.

```bash
# Using your Mess With DNS subdomain SUB:
# 1. Ask for a name that does not exist yet
dig later.SUB +noall +comments +authority      # NXDOMAIN, note the SOA TTL
# 2. Now create an A record "later.SUB -> 192.0.2.44" on the website
# 3. Ask again immediately through your normal resolver
dig later.SUB +short                           # still nothing: the NXDOMAIN is cached
# 4. Bypass caches: ask the zone's authoritative server directly
dig +short NS SUB                              # find the authority (one of the site's name servers)
dig @NS_FROM_ABOVE later.SUB +short            # 192.0.2.44 - the truth
# 5. Flush only YOUR cache and compare (the company/ISP resolver may still hold it)
sudo resolvectl flush-caches; dig later.SUB +short
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Changed a record, clients still get the old IP | Some users old, some new, for up to TTL | `dig +noall +answer NAME` (TTL), `dig @AUTH NAME` | [DNS reference](08-dns.md) |
| Created a record, still NXDOMAIN | `NXDOMAIN` for minutes after creating it | `dig NAME` (SOA TTL in AUTHORITY), `dig @AUTH NAME` | this topic |
| App never re-resolves | Restarting the app "fixes DNS" | App's DNS caching settings (JVM, nginx `resolver`) | [Learn web servers](29-learn-webservers-proxies.md) |
| Very low TTLs everywhere | Resolver load, latency spikes when the resolver is slow | `resolvectl statistics`, query times | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting:** In a migration (Apache → Dokploy on a
new IP, or a new server) the DNS cut-over is the riskiest step for user
impact. Plan TTLs ahead, verify at the authority, and expect a tail of old
answers. Don't keep changing records while the caches are still catching up.

**Next step:** on the client, `dig` and your applications don't even use the
same path. That's the next topic, and the most common source of "dig works,
curl doesn't".

### The Linux resolver path: getaddrinfo vs dig

**Level:** [L2 · Mid] · one of the Ops Ladder blind spots.

**Concept.** Applications (curl, Python, PHP, most daemons) resolve names
through glibc's **`getaddrinfo()`**. It reads **`/etc/nsswitch.conf`** to
decide which sources to ask and in which order. On Ubuntu servers that's
`hosts: files dns`: **`/etc/hosts` first**, then DNS through the nameserver
in `/etc/resolv.conf`. **`dig` skips all of that.** It sends a DNS packet
straight to the server in `/etc/resolv.conf` (or the one you name with `@`).
So `dig` and your app can legitimately disagree. **`getent ahosts NAME` uses
the same path as the app** and is the right tool to see what the app sees.

```
                         ┌──────────────── getaddrinfo() (curl, python, apache, ...) ───────────────┐
 app asks "app.example.com" │ /etc/nsswitch.conf  hosts: files dns                                │
                         │   1. files -> /etc/hosts        ("192.0.2.99 app.example.com" wins!)    │
                         │   2. dns   -> /etc/resolv.conf -> nameserver 127.0.0.53 (resolved)      │
                         │   + search domains, ndots, timeout/attempts, /etc/gai.conf sorting      │
                         └─────────────────────────────────────────────────────────────────────────┘
 dig asks "app.example.com" ─────────────────► nameserver from /etc/resolv.conf (no /etc/hosts, no nsswitch)
 getent ahosts            ─────────────────► exactly the getaddrinfo path (use this to see what apps see)
```

Not every program uses glibc. Go binaries often use Go's own resolver (it
reads `/etc/hosts` and `resolv.conf` itself). Alpine images use **musl**,
which ignores `nsswitch.conf` and handles `search`/`ndots` differently. Java
has its own cache. Remember this when "the container resolves differently
from the host".

**Key terms**

| Term | Meaning |
|---|---|
| `getaddrinfo()` | The libc call apps use to turn names into addresses |
| NSS / `nsswitch.conf` | Name Service Switch: ordered list of sources (`files`, `dns`, `resolve`, `mdns4_minimal`, `myhostname`) |
| `/etc/hosts` | Static name → IP map. Consulted first on a normal Ubuntu server |
| `search` / `ndots` | Domains appended to short names / how many dots a name needs before it's tried as-is first |
| `/etc/gai.conf` | Address-family preference (IPv6 vs IPv4 ordering) for getaddrinfo |

**See it on a real system**

```bash
grep '^hosts' /etc/nsswitch.conf          # source order
cat /etc/hosts
cat /etc/resolv.conf                      # nameserver, search, options
getent ahosts app.example.com             # what APPS get (follows nsswitch)
dig +short app.example.com                # what DNS says
curl -sv -o /dev/null http://app.example.com 2>&1 | grep -E 'Trying|Connected'   # what curl actually used
```

```
$ grep '^hosts' /etc/nsswitch.conf
hosts:          files dns

$ getent ahosts app.example.com
192.0.2.99      STREAM app.example.com
192.0.2.99      DGRAM
192.0.2.99      RAW

$ dig +short app.example.com
203.0.113.10
```

- They disagree: getent (and therefore curl) says 192.0.2.99, DNS says
  203.0.113.10. There is almost certainly a line in `/etc/hosts`. Run
  `grep app.example.com /etc/hosts`. Old hosts entries left over from a
  migration are a classic cause of "only this server sees the old site".

**Hands-on lab (test VM only)**: the /etc/hosts trap, and testing past DNS with `curl --resolve`.

```bash
# 1. Baseline
getent ahosts example.com; dig +short example.com

# 2. Break: a stale hosts entry
echo '192.0.2.99 example.com' | sudo tee -a /etc/hosts
getent ahosts example.com                 # 192.0.2.99 - what apps see
dig +short example.com                    # real answer - dig ignores /etc/hosts
curl -sv -m5 -o /dev/null http://example.com 2>&1 | grep -E 'Trying|timed out'   # tries 192.0.2.99

# 3. Diagnose like you would in production
grep -n 'example.com' /etc/hosts
strace -f -e trace=openat curl -s -m2 -o /dev/null http://example.com 2>&1 | grep -E 'hosts|resolv|nsswitch'

# 4. Fix: remove the line (sed keeps a backup)
sudo sed -i.bak '/^192\.0\.2\.99 example\.com$/d' /etc/hosts
getent ahosts example.com

# 5. Testing PAST DNS without touching it: pin a name to an IP for one request.
#    --resolve keeps the right Host header AND the right TLS SNI.
curl -sv -o /dev/null --resolve example.com:443:$(dig +short example.com | head -1) https://example.com/ 2>&1 | grep -E 'Added|Connected|subject'
#    For plain HTTP, a Host header does the same job:
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: example.com' http://$(dig +short example.com | head -1)/
```

See [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html)
for `--resolve` and `--connect-to`, and Julia Evans's
[Some things about getaddrinfo that surprised me](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/).

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Stale `/etc/hosts` entry | One server reaches the old IP; `dig` looks right | `getent ahosts NAME` vs `dig +short NAME` | [Site down playbook](25-playbook-site-down.md) |
| Search domain expansion | Short names resolve to something odd, or slowly | `getent ahosts SHORTNAME`, `grep search /etc/resolv.conf` | next topics |
| Dead first nameserver in `resolv.conf` (no resolved) | Every lookup takes 5 s+ ("app is slow") | `time getent ahosts NAME` | [Slow system playbook](23-playbook-slow-system.md) |
| Alpine/musl container behaves differently | Works in a Debian-based image, fails in Alpine | `docker exec CONTAINER cat /etc/resolv.conf` | section 8 containers topic |

**Why it matters for troubleshooting:** When `dig` and the app disagree,
`getent ahosts` is the tiebreaker. `curl --resolve` lets you test the
server, proxy and certificate *while* DNS is broken. You prove the rest of
the stack independently instead of waiting for DNS to be fixed.

**Next step:** on Ubuntu the nameserver in `resolv.conf` is 127.0.0.53, a
local stub. Learn what's behind it and how to make it talk.

### systemd-resolved and the 127.0.0.53 stub

**Level:** [L2 · Mid] · home of the Ops Ladder "break DNS three ways" drill.

**Concept.** On Ubuntu, `/etc/resolv.conf` is a symlink to
`/run/systemd/resolve/stub-resolv.conf`, which lists only
`nameserver 127.0.0.53`. That's **systemd-resolved**'s local stub listener.
It caches answers and forwards queries to the real upstream servers it got
from netplan/networkd, DHCP or a VPN, chosen *per interface*. The real
upstream list is in `resolvectl status` and in
`/run/systemd/resolve/resolv.conf`, which is also the file Docker and kubelet
should use, because 127.0.0.53 means nothing inside a container.

```
 /etc/resolv.conf -> /run/systemd/resolve/stub-resolv.conf   nameserver 127.0.0.53   (apps use this)
                     /run/systemd/resolve/resolv.conf        nameserver 192.0.2.53   (real upstreams;
                                                             nameserver 192.0.2.54    Docker/kubelet use this)
 systemd-resolved  listens 127.0.0.53:53 (stub) and 127.0.0.54:53 (proxy, no local logic)
                   per link: ens18 -> 192.0.2.53 192.0.2.54, DNS Domain corp.example.com
                             wg0   -> 10.8.0.1, DNS Domain ~corp.example.com (routing-only)
```

**Key terms**

| Term | Meaning |
|---|---|
| Stub listener | 127.0.0.53:53, the address in `resolv.conf` |
| Per-link DNS | Each interface has its own servers and domains |
| DNS Domain `~name` | Routing-only domain: send queries for this suffix to this link's servers; not used as a search suffix |
| DefaultRoute | Whether a link's servers are used for names that match no routing domain |
| resolv.conf mode | `stub` (normal), `uplink`, `static`, `foreign` (someone replaced the symlink) |

**See it on a real system**

```bash
ls -l /etc/resolv.conf                     # symlink to stub-resolv.conf?
resolvectl status                          # global + per-link servers and domains
resolvectl query app.example.com           # resolve through resolved, shows which link answered
resolvectl statistics                      # cache hits/misses, transactions
cat /run/systemd/resolve/resolv.conf       # the real upstreams in classic format
journalctl -u systemd-resolved -b --no-pager | tail -20
```

```
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
app.example.com: 203.0.113.10                    -- link: ens18

-- Information acquired via protocol DNS in 23.4ms.
-- Data is authenticated: no; Data was acquired via local or encrypted transport: no
-- Data from: network
```

- `Data from: network` means a cache miss that went upstream. Run it again
  and you'll see `Data from: cache`.

**Hands-on lab (test VM only)**: the Ops Ladder DNS drill. Break resolution
three ways and diagnose each with the four tools your notes were missing:
tcpdump, `getent ahosts`, resolver debug logs and `curl --resolve`.

```bash
# 0. Two terminals: in terminal 2 keep a capture running for the whole lab
sudo tcpdump -ni any port 53
# and turn on resolver debug logging (terminal 3)
sudo resolvectl log-level debug
journalctl -fu systemd-resolved

# --- Break 1: bad upstream (runtime only; reverts when networkd reconfigures) ---
sudo resolvectl dns ens18 192.0.2.254          # an address with no DNS server
sudo resolvectl flush-caches
getent ahosts example.com; echo "exit=$?"      # nothing, exit=2
resolvectl query example.com                   # resolve call failed: All attempts to contact name servers or networks failed
#   tcpdump: queries to 192.0.2.254.53, no answers
#   journal: "Using DNS server 192.0.2.254 ...", "Timeout reached on transaction ..."
curl -sv -o /dev/null --resolve example.com:443:$(dig @1.1.1.1 +short example.com | head -1) https://example.com/ 2>&1 | grep -E 'Connected|HTTP/'   # the site itself is fine
# Fix:
sudo resolvectl revert ens18 && sudo networkctl reconfigure ens18
resolvectl status ens18

# --- Break 2: resolved stopped ---
sudo systemctl stop systemd-resolved
dig example.com                                # communications error to 127.0.0.53#53: connection refused / no servers could be reached
curl -s -m5 https://example.com -o /dev/null; echo "curl exit=$?"   # 6 = couldn't resolve host
#   tcpdump: queries to 127.0.0.53 answered by ICMP "udp port 53 unreachable"
sudo systemctl start systemd-resolved          # Fix

# --- Break 3: wrong /etc/hosts line --- (see the previous topic's lab)

# Finally, turn debug logging back off
sudo resolvectl log-level info
```

> Don't edit `/etc/resolv.conf` by hand on Ubuntu. Replacing the symlink with
> a static file (`resolv.conf mode: foreign`) bypasses resolved, the per-link
> servers and VPN split DNS. Configure DNS in netplan (`nameservers:`) and
> apply with `sudo netplan try`.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| No reachable upstream | `curl: (6) Could not resolve host`, `resolve call failed: All attempts to contact name servers or networks failed` | `resolvectl status`, `sudo tcpdump -ni any port 53` | [DNS reference](08-dns.md) |
| resolved stopped or crashed | `dig`: `connection refused` to 127.0.0.53 | `systemctl status systemd-resolved` | [Services](07-services-systemd.md) |
| Another DNS server wants port 53 (Pi-hole, dnsmasq, CoreDNS on the host) | `bind: address already in use` for :53 | `sudo ss -lunp 'sport = :53'`; set `DNSStubListener=no` in a `/etc/systemd/resolved.conf.d/*.conf` drop-in | [Ports inventory playbook](22-playbook-ports-inventory.md) |
| Upstream blocks UDP/TCP 53 to outside resolvers | Only internal names work, or nothing | `dig @192.0.2.53 NAME` vs `dig @1.1.1.1 NAME` | [Site down playbook](25-playbook-site-down.md) |

Reference: [Arch Wiki: systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved).

**Why it matters for troubleshooting:** "Could not resolve host" on Ubuntu
almost always ends at `resolvectl status`: which upstream is configured, and
can it be reached? Debug logs and a port-53 capture show it directly instead
of making you guess.

**Next step:** with VPNs, internal and public names need *different*
servers. That's split DNS.

### Split DNS and VPNs

**Level:** [L2 · Mid].

**Concept.** **Split DNS** means different names go to different DNS
servers: `*.corp.example.com` to the internal resolver over the VPN,
everything else to the normal upstream. systemd-resolved does this with
**routing domains** (`~corp.example.com`) per link. **Split-horizon DNS** is
a different thing: the *same* name gets different answers depending on who
asks, for example the internal IP from inside the office and the public IP
from outside. You need it when the router can't do hairpin NAT. Both are
common sources of "works at home, not in the office" (or the reverse).

```
 query: git.corp.example.com           query: github.com
   │ matches ~corp.example.com on wg0     │ no routing domain matches
   ▼                                      ▼
 wg0  -> 10.8.0.1 (internal DNS)        ens18 (DefaultRoute) -> 192.0.2.53
```

**Key terms**

| Term | Meaning |
|---|---|
| Routing domain | `~corp.example.com`: queries for this suffix go to this link |
| Search domain | `corp.example.com`: appended to short names (`git` → `git.corp.example.com`) |
| `~.` | Route *all* queries to this link (full-tunnel DNS) |
| Split-horizon | Same name, different answers inside vs outside |
| Hairpin NAT | Inside client reaching an inside server via the public IP. Often unsupported |

**See it on a real system**

```bash
resolvectl status wg0                    # servers/domains of the VPN link
resolvectl domain                        # domains per link
resolvectl query git.corp.example.com    # "-- link: wg0" proves the routing
```

```
$ resolvectl status wg0
Link 5 (wg0)
    Current Scopes: DNS
         Protocols: -DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 10.8.0.1
       DNS Servers: 10.8.0.1
        DNS Domain: ~corp.example.com
```

A WireGuard client config (wg-quick) can set this up when the tunnel comes up:

```
[Interface]
PrivateKey = (from your key file)
Address = 10.8.0.2/24
PostUp = resolvectl dns %i 10.8.0.1; resolvectl domain %i ~corp.example.com; resolvectl default-route %i false
```

**Hands-on lab (test VM only)**: routing domains without a real VPN.

```bash
# 1. Build: a dummy interface stands in for the VPN link
#    (resolved only uses a link for DNS when it is up and has a routable address)
sudo ip link add vpn0 type dummy && sudo ip link set vpn0 up
sudo ip addr add 10.99.99.2/24 dev vpn0
sudo resolvectl dns vpn0 192.0.2.254              # "internal DNS" that does not exist
sudo resolvectl domain vpn0 '~internal.example'
sudo resolvectl default-route vpn0 false

# 2. Observe routing: only matching names go to vpn0
resolvectl status vpn0                            # DNS Domain: ~internal.example, -DefaultRoute
resolvectl query example.com                      # answered via ens18 as usual
sudo tcpdump -ni any port 53 -c 6 &               # see which interface/server each query uses
resolvectl query git.internal.example             # times out: sent only to vpn0's (dead) server
resolvectl query example.com                      # still fine: no routing domain matches -> ens18

# 3. Fix / clean up (deleting the link drops its DNS settings automatically)
sudo ip link del vpn0
resolvectl status | head -20
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Internal names fail on VPN | `NXDOMAIN` from the public resolver for `*.corp` | `resolvectl query NAME` (which link?) | [DNS reference](08-dns.md) |
| VPN takes all DNS (`~.`) | Public names slow or failing while connected | `resolvectl domain` | this topic |
| Split-horizon missing, no hairpin | Public name works from outside, times out from the LAN | `dig NAME` inside vs outside, `ip route get IP` | [Site down playbook](25-playbook-site-down.md) |
| Windows/macOS clients | Different mechanisms: NRPT on Windows, `/etc/resolver/` and `scutil --dns` on macOS | see [Windows](17-windows.md), [macOS](20-macos.md) | - |

**Why it matters for troubleshooting:** "It resolves for me but not for the
client" is often split DNS: you're on the VPN and they aren't, or the
reverse. Always ask *from where* a name is resolved, and test from the same
place.

**Next step:** containers and pods add one more resolver layer: Docker's
127.0.0.11 and Kubernetes' CoreDNS.

### DNS inside Docker and Kubernetes

**Level:** [L2 · Mid] for Docker · [L3 · Senior] for CoreDNS on the CKA track.

**Concept.** On a **user-defined Docker network** (Compose, Dokploy's
networks), every container's `resolv.conf` says `nameserver 127.0.0.11`.
That's Docker's **embedded DNS server**, running in the container's namespace
and served by the Docker daemon. It answers container and service names on
that network (`db`, `app`) and forwards everything else to the host's real
upstream servers. With systemd-resolved, Docker reads
`/run/systemd/resolve/resolv.conf`, not the 127.0.0.53 stub. If Docker finds
no usable upstream, it falls back to **8.8.8.8 and 8.8.4.4**, which on-prem
firewalls usually block. The **default bridge** network has no embedded DNS
and no name resolution between containers. In **Kubernetes**, pods use
**CoreDNS** (a Service, typically 10.96.0.10). Their `resolv.conf` has
cluster search domains and `ndots:5`.

```
 Docker user-defined network                   Kubernetes pod
 container /etc/resolv.conf                    pod /etc/resolv.conf
   nameserver 127.0.0.11                         nameserver 10.96.0.10          (kube-dns Service -> CoreDNS pods)
   options ndots:0                               search NS.svc.cluster.local svc.cluster.local cluster.local
      │                                          options ndots:5
      ▼                                                 │
 dockerd embedded DNS                                   ▼
   container/service names on this network   CoreDNS: *.cluster.local from the K8s API
   else -> host upstreams (or 8.8.8.8 fallback)        else -> forward . /etc/resolv.conf (the NODE's upstreams)
```

**Key terms**

| Term | Meaning |
|---|---|
| 127.0.0.11 | Docker embedded DNS (user-defined networks only) |
| `dns` in `daemon.json` | Upstream servers Docker gives containers: `"dns": ["192.0.2.53"]` |
| Service name / `tasks.NAME` | In Swarm: VIP of the service / IPs of its tasks |
| CoreDNS / kube-dns | Cluster DNS. The Service is still named `kube-dns` for compatibility |
| `SVC.NAMESPACE.svc.cluster.local` | Full Service name. A short name works only within the same namespace |
| `ndots:5` | Names with fewer than 5 dots try every search domain first. External lookups cost several extra queries |

**See it on a real system**

```bash
docker exec CONTAINER cat /etc/resolv.conf                     # what the container uses
docker run --rm --network NETWORK busybox:1.36 nslookup db     # name resolution on a network
docker run --rm -it --net container:CONTAINER nicolaka/netshoot dig example.com   # tools in its namespace
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- nslookup kubernetes.default
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system get configmap coredns -o yaml           # the Corefile
```

```
$ docker exec app cat /etc/resolv.conf
# Generated by Docker Engine.
# This file can be edited; Docker Engine will not make further changes once it
# has been modified.

nameserver 127.0.0.11
search corp.example.com
options ndots:0

# Based on host file: '/run/systemd/resolve/resolv.conf' (internal resolver)
# ExtServers: [192.0.2.53 192.0.2.54]
# Overrides: []
# Option ndots from: internal
```

- `ExtServers` are the upstreams the embedded DNS forwards to. If you see
  `8.8.8.8 8.8.4.4` here on an on-prem host, Docker fell back. Set `"dns"`
  in `/etc/docker/daemon.json` and restart Docker (plan it: containers
  restart).
- Newer Docker versions write these comment lines. Older ones show only the
  `nameserver`/`options` lines.

**Hands-on lab (test VM only, Docker installed)**

```bash
# 1. Build: two containers on a user-defined network vs the default bridge
docker network create labnet
docker run -d --name db --network labnet nginx:alpine
docker run --rm --network labnet busybox:1.36 nslookup db          # resolves via 127.0.0.11
docker run --rm busybox:1.36 nslookup db                           # default bridge: fails (no embedded DNS)

# 2. Watch the embedded DNS forward an external query
docker run --rm -it --network labnet nicolaka/netshoot bash -c 'cat /etc/resolv.conf; dig +short example.com'
sudo tcpdump -ni any port 53 -c 6       # in another terminal: dockerd forwarding from the host

# 3. Break: point Docker at a dead upstream (test VM only; restarts all containers)
echo '{ "dns": ["192.0.2.254"] }' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
docker run --rm --network labnet busybox:1.36 nslookup example.com   # times out
docker run --rm --network labnet busybox:1.36 nslookup db            # still works: internal names don't need upstream

# 4. Fix
echo '{ "dns": ["192.0.2.53"] }' | sudo tee /etc/docker/daemon.json  # your real internal resolver(s)
sudo systemctl restart docker
docker rm -f db; docker network rm labnet
```

> If `/etc/docker/daemon.json` already exists on the VM, back it up first and
> merge the `dns` key into it. Overwriting it drops other settings (log
> rotation, address pools).

On a **test** Kubernetes cluster (CKA practice):

```bash
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- cat /etc/resolv.conf
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- nslookup kubernetes.default
# Break (TEST cluster only): no CoreDNS
kubectl -n kube-system scale deployment coredns --replicas=0
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- nslookup kubernetes.default   # times out
kubectl -n kube-system scale deployment coredns --replicas=2     # Fix
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Resolves on the host, fails in a container | `Could not resolve host` / `bad address` in the container | `docker exec CONTAINER cat /etc/resolv.conf` (ExtServers) | [Containers playbook](26-playbook-containers-k8s.md) |
| Container names don't resolve | `nslookup db` fails | `docker network inspect NET` (both containers on it? default bridge?) | [Learn Docker](30-learn-docker.md) |
| CoreDNS CrashLoopBackOff: `Loop ... detected` | CoreDNS forwards to itself via a 127.0.0.53 node resolv.conf | `kubectl -n kube-system logs -l k8s-app=kube-dns`; kubelet `resolvConf` | [Learn Kubernetes](31-learn-kubernetes.md) |
| Pod can't resolve a Service in another namespace | `NXDOMAIN` for `svc` | use `svc.namespace`; check NetworkPolicy to port 53 | [Containers playbook](26-playbook-containers-k8s.md) |
| External lookups slow from pods | 4–10 queries per lookup (ndots:5 + A/AAAA) | `tcpdump` on the node, `dnsConfig.options ndots` | [Learn Kubernetes](31-learn-kubernetes.md) |

References: [Dokploy: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking),
[netshoot](https://github.com/nicolaka/netshoot),
[Kubernetes docs: Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/),
[CoreDNS: loop plugin](https://coredns.io/plugins/loop).

**Why it matters for troubleshooting:** After the Dokploy migration, every
app lives in a container with its own resolver. "The build can't reach
GitLab" or "the app can't find the database" are DNS problems at a layer the
host's `dig` doesn't see. Always test from inside the container's namespace.

**Next step:** once a name resolves and TCP connects, the conversation is
usually HTTP.

---

## 9. HTTP

> 📚 **Study path:** 1) Note: this section, then [Web, HTTP & TLS reference](18-web-http-tls.md). HTTP is a refresher for you, so start with the note · 2) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *Apache Web Server* (vhosts, logs) ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · 3) KodeKloud: *Nginx For Beginners* — Intermediate Config → *Reverse Proxy* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)) · 4) Read: [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html) and [What is a reverse proxy?](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/) · 5) Practice: the Apache labs below, then the 5xx walk in the [site down playbook](25-playbook-site-down.md).

### Request and response anatomy

**Level:** [L1 · Junior].

**Concept.** HTTP/1.1 is plain text over a TCP (or TLS) connection. The
client sends a **request**: a request line (method, path, version), headers,
an empty line, and an optional body. The server answers with a **response**:
a status line, headers, an empty line and a body. The **Host header** tells
the server which site you want. That's how Apache serves 3–4 sites (virtual
hosts) on one IP and port, and how Traefik picks a router.

```
 request                                        response
 GET /health HTTP/1.1            <- request line   HTTP/1.1 200 OK                     <- status line
 Host: app.example.com           <- which vhost    Date: Sat, 03 Oct 2026 10:15:02 GMT
 User-Agent: curl/8.5.0                            Server: Apache/2.4.58 (Ubuntu)       <- who answered
 Accept: */*                                       Content-Type: application/json
                                 <- empty line     Content-Length: 15
 (no body for GET)                                                                     <- empty line
                                                   {"status":"ok"}                      <- body
```

**Key terms**

| Term | Meaning |
|---|---|
| URL | `scheme://host:port/path?query#fragment`. The fragment never reaches the server |
| Virtual host (vhost) | One server, many sites, selected by the `Host` header (and by SNI for TLS) |
| Default vhost | What the server serves when no vhost matches the Host. Apache: the *first* vhost for that IP:port |
| Content-Length / chunked | Body size known up front / sent in chunks (`Transfer-Encoding: chunked`) |
| Idempotent | Repeating the request has the same effect (GET, PUT, DELETE). Proxies may retry these |

**See it on a real system**

```bash
curl -v http://app.example.com/ -o /dev/null           # '>' lines = request, '<' lines = response
curl -sI https://app.example.com/                       # headers only (HEAD request)
printf 'GET / HTTP/1.1\r\nHost: app.example.com\r\nConnection: close\r\n\r\n' | nc -q 3 192.0.2.10 80 | head -15
sudo apachectl -S                                       # Apache: which vhost is default for each IP:port
```

```
$ sudo apachectl -S
VirtualHost configuration:
*:80                   is a NameVirtualHost
         default server shop.example.com (/etc/apache2/sites-enabled/000-shop.conf:1)
         port 80 namevhost shop.example.com (/etc/apache2/sites-enabled/000-shop.conf:1)
         port 80 namevhost blog.example.com (/etc/apache2/sites-enabled/010-blog.conf:1)
         port 80 namevhost crm.example.com (/etc/apache2/sites-enabled/020-crm.conf:1)
*:443                  is a NameVirtualHost
         default server shop.example.com (/etc/apache2/sites-enabled/000-shop-ssl.conf:2)
...
```

- This is the inventory question from the incident ("which app is which?")
  answered in one command: every vhost, its name, and the file that defines
  it. Requests with an unknown Host go to the `default server`.

**Hands-on lab (test VM only)**: Host-header routing in Apache.

```bash
# 1. Build two name-based vhosts
sudo apt install -y apache2
sudo mkdir -p /var/www/a /var/www/b
echo 'site A' | sudo tee /var/www/a/index.html
echo 'site B' | sudo tee /var/www/b/index.html
sudo tee /etc/apache2/sites-available/lab.conf >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName a.example.com
    DocumentRoot /var/www/a
</VirtualHost>
<VirtualHost *:80>
    ServerName b.example.com
    DocumentRoot /var/www/b
</VirtualHost>
EOF
sudo a2ensite lab && sudo apachectl configtest && sudo systemctl reload apache2

# 2. Same IP and port, different Host -> different site
curl -s -H 'Host: a.example.com' http://127.0.0.1/
curl -s -H 'Host: b.example.com' http://127.0.0.1/
curl -s -H 'Host: nope.example.com' http://127.0.0.1/ | head -3     # default vhost (000-default) answers
sudo apachectl -S

# 3. Break: HTTP/1.1 without a Host header
printf 'GET / HTTP/1.1\r\n\r\n' | nc -q 2 127.0.0.1 80 | head -1   # HTTP/1.1 400 Bad Request

# 4. Diagnose in the logs: which vhost logged what
sudo tail -3 /var/log/apache2/access.log /var/log/apache2/error.log
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Wrong site served | Content of another app, or the Apache "It works!" page | `sudo apachectl -S`, `curl -H 'Host: NAME' http://IP/` | [Learn web servers](29-learn-webservers-proxies.md) |
| No Host / bad request syntax | `400 Bad Request` | replay with `curl -v` | [Web reference](18-web-http-tls.md) |
| Plain HTTP sent to the TLS port | Apache: `You're speaking plain HTTP to an SSL-enabled server port`; nginx: `The plain HTTP request was sent to HTTPS port` | check URL scheme and port | section 10 |
| Traefik: no router for this Host | `404 page not found` (plain text) | `curl -v -H 'Host: NAME' http://TRAEFIK_IP/` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting:** Behind a reverse proxy, the Host
header *is* the routing key. A typo in a Traefik rule, a missing
`ServerName` or a wrong DNS name all end up as "wrong site" or 404. Since
`curl -H 'Host:'` and `--resolve` let you set it yourself, you can test every
vhost without touching DNS.

**Next step:** the status line. Reading the code correctly, and knowing which
component sent it, is half of web troubleshooting.

### Methods and status codes

**Level:** [L1 · Junior] for the codes · [L2 · Mid] for naming the component that produced them.

**Concept.** The **method** says what the client wants. The **status code**
says what happened, in five families. The code alone is not enough: you also
need to know **which component produced it**. A 502 from Traefik, a 502 from
Cloudflare and a 502 from Apache's mod_proxy have different causes.

| Method | Meaning | Safe / idempotent |
|---|---|---|
| GET / HEAD | Fetch a resource / only its headers | safe, idempotent |
| POST | Submit data, create, trigger an action | neither |
| PUT / PATCH | Replace / partially update | idempotent / not necessarily |
| DELETE | Remove | idempotent |
| OPTIONS | Ask what's allowed. CORS preflight from browsers | safe |

| Family | Meaning | Who to look at |
|---|---|---|
| 1xx | Informational (101 Switching Protocols = WebSocket upgrade) | - |
| 2xx | Success | - |
| 3xx | Redirect / cached | Redirect rules, app config |
| 4xx | The *request* is wrong (client side, or routing/auth rules) | Client, auth, proxy routing, WAF |
| 5xx | The *server side* failed | Proxy and app logs |

The codes you must know exactly:

| Code | Exact meaning | Typical real cause | First check |
|---|---|---|---|
| 301 | Moved Permanently. Browsers **cache** it, so a wrong 301 sticks | HTTP → HTTPS redirect, domain move | `curl -sI URL` (Location), test in a private window |
| 302 | Found, a temporary redirect. Not cached by default (307/308 keep the method) | Login redirects, maintenance | `curl -sIL URL` (follow the chain) |
| 304 | Not Modified: answer to a conditional request (`If-None-Match`/`If-Modified-Since`). No body | Normal caching. Not an error | `curl -sI -H 'If-None-Match: "ETAG"' URL` |
| 400 | Bad Request: malformed syntax, missing Host, oversized headers/cookies | Huge cookies, broken client, plain HTTP to the TLS port | replay with minimal `curl -v` |
| 401 | Unauthorized means *not authenticated*. Comes with `WWW-Authenticate` | Missing/expired token, wrong basic-auth | `curl -v` (WWW-Authenticate header) |
| 403 | Forbidden: authenticated or not, *not allowed* | Apache `Require` rules (`AH01630: client denied by server configuration`), file permissions, WAF, IP allow-list | proxy/web server error log |
| 404 | Not Found: no such resource, *or* no route/vhost matched | Wrong path, wrong vhost, Traefik router missing (`404 page not found`) | `curl -H 'Host: ...'` against the backend directly |
| 408 | Request Timeout: the client didn't finish sending the request in time | Slow clients, idle keep-alives, Apache `mod_reqtimeout` | proxy timeouts |
| 413 | Content Too Large (body over the limit) | Uploads vs `client_max_body_size` (nginx default 1 MB), Apache `LimitRequestBody`, Traefik buffering middleware | upload size vs limits on *every* hop |
| 429 | Too Many Requests: rate limited. May carry `Retry-After` | Rate-limit middleware, API quotas, WAF | `curl -sI` (Retry-After), limiter config |
| 500 | Internal Server Error: the app (or server config) failed | Exception in the app, broken `.htaccess` | **app logs** |
| 502 | Bad Gateway: the proxy got **no valid response** from upstream (refused, reset, garbage) | App down, wrong port, app bound to 127.0.0.1, container not on the proxy network, app crashed mid-request | proxy log + `ss -ltn` in the app's namespace |
| 503 | Service Unavailable: no healthy upstream / overloaded / maintenance | All backends failing health checks, K8s Service with no endpoints, maintenance mode | LB/health status, `kubectl get endpoints` |
| 504 | Gateway Timeout: upstream accepted but didn't answer in time | Slow query or endpoint, proxy timeout lower than the app's run time | app latency, proxy timeout settings |

**Key terms**

| Term | Meaning |
|---|---|
| `Location` | Header carrying the redirect target |
| ETag / `If-None-Match` | Version tag of a resource / "send it only if it changed" (gives 304) |
| `Retry-After` | Seconds (or a date) to wait. Sent with 429/503 |
| `Server` / `Via` | Who generated or forwarded the response. Your hint for "which component?" |

**See it on a real system**

```bash
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://app.example.com/
curl -sIL http://app.example.com/ | grep -iE '^HTTP|^location'          # the whole redirect chain
curl -sI https://app.example.com/ | grep -iE '^server|^via|^x-'          # who answered?
awk '{print $9}' /var/log/apache2/access.log | sort | uniq -c | sort -rn # status histogram (combined log format)
```

```
$ curl -sIL http://app.example.com/ | grep -iE '^HTTP|^location'
HTTP/1.1 301 Moved Permanently
Location: https://app.example.com/
HTTP/2 302
location: https://app.example.com/login
HTTP/2 200
```

How to tell *who* generated an error page:

| Body / headers look like | Generated by |
|---|---|
| `404 page not found` (plain text, 19 bytes) | Traefik: no router matched |
| `Bad Gateway` / `Gateway Timeout` (plain text) | Traefik |
| HTML with `nginx` in the footer, `Server: nginx` | nginx |
| HTML "Proxy Error ... Error reading from remote server", `Server: Apache/2.4.xx` | Apache mod_proxy |
| JSON error body from your framework | The application itself |

**Hands-on lab (test VM only)**: make Apache produce 301, 304, 403, 404, 408 and 413.

```bash
# 1. Build: extend vhost A from the previous lab
sudo tee /etc/apache2/sites-available/lab.conf >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName a.example.com
    DocumentRoot /var/www/a
    Redirect permanent /old /index.html
    LimitRequestBody 1024
    <Location /private>
        Require all denied
    </Location>
</VirtualHost>
EOF
sudo apachectl configtest && sudo systemctl reload apache2
H='Host: a.example.com'

# 2. Produce each code and read the evidence
curl -si -H "$H" http://127.0.0.1/old | grep -iE '^HTTP|^Location'      # 301 + Location
curl -si -H "$H" http://127.0.0.1/private | head -1                      # 403
curl -si -H "$H" http://127.0.0.1/missing | head -1                      # 404
head -c 4096 /dev/zero | curl -si -H "$H" --data-binary @- http://127.0.0.1/ | head -1   # 413
ETAG=$(curl -sI -H "$H" http://127.0.0.1/ | awk -F': ' 'tolower($1)=="etag"{print $2}' | tr -d '\r')
curl -si -H "$H" -H "If-None-Match: $ETAG" http://127.0.0.1/ | head -1  # 304
(printf 'GET / HTTP/1.1\r\n'; sleep 45) | nc 127.0.0.1 80 | head -1     # unfinished request: ~20 s later "HTTP/1.1 408 Request Timeout"

# 3. Find each one in the logs
sudo tail -8 /var/log/apache2/access.log
sudo grep -E 'AH01630|AH00' /var/log/apache2/error.log | tail -3        # the 403 reason
```

> 502, 503 and 504 need a proxy in front of a backend. You'll produce them in
> the load-balancing lab (section 11) and the proxy-headers lab (next topic).

**How it breaks**: use the "exact meaning" table above as the decision table.
The [site down playbook](25-playbook-site-down.md) walks each 5xx through
the layered bypass (through the proxy → straight to the backend → on the box).

**Why it matters for troubleshooting:** A status code plus the component that
produced it narrows the problem to one hop. A Traefik `Bad Gateway` means
"Traefik couldn't talk to the container", not "the app threw an exception".
That points you at ports and networks, not application code.

**Next step:** proxies add and rely on headers. Get them wrong and you get
redirect loops and wrong client IPs.

### Headers that matter behind a proxy

**Level:** [L2 · Mid].

**Concept.** Once Traefik (or Apache/nginx) terminates TLS and forwards to
the app over plain HTTP, the app loses three facts: the original **host**,
the **client's IP** (it now sees the proxy's IP) and the original **scheme**
(it sees `http`). Proxies put these into headers. The app must read them,
and must trust them **only from the proxy**, because clients can forge them.
Keep-alive settings must also agree between the hops.

```
 client 198.51.100.23 ──HTTPS──► Traefik 172.18.0.3 ──HTTP──► app 172.18.0.9:8000
                                   adds / passes:
                                   Host: app.example.com              (passed through by Traefik)
                                   X-Forwarded-For: 198.51.100.23     (client chain, appended per proxy)
                                   X-Forwarded-Proto: https           (original scheme)
                                   X-Forwarded-Host: app.example.com
                                   X-Real-Ip: 198.51.100.23
 app without these: sees 172.18.0.3 as every client, thinks the request was http,
                    redirects to https://... -> proxy forwards as http again -> redirect loop
```

| Header | Purpose | Trap |
|---|---|---|
| `Host` | Which site | Apache `mod_proxy` sends the *backend's* host unless `ProxyPreserveHost On` |
| `X-Forwarded-For` | Client IP chain: `client, proxy1, proxy2` | Spoofable. Trust only the entries added by your own proxies. Apache's `mod_remoteip`, nginx `real_ip` |
| `X-Forwarded-Proto` | `https` or `http` as the client used it | Missing → app thinks http → infinite HTTPS redirect, or wrong `http://` links |
| `X-Forwarded-Host` / `X-Forwarded-Port` | Original host/port | Used for building absolute URLs |
| `Forwarded` | Standard form of all the above (RFC 7239) | Less widely supported |
| `Connection: keep-alive` / `close` | Reuse the TCP connection, or not | Backend idle timeout *shorter* than the proxy's → proxy reuses a closed connection → sporadic 502 |
| `Upgrade: websocket` | Switch protocols (101) | Proxy must pass Upgrade/Connection (Apache needs `mod_proxy_wstunnel` or `upgrade=websocket`) |

**Key terms**

| Term | Meaning |
|---|---|
| TLS termination | The proxy decrypts. Traffic proxy → app is plain HTTP (on a private network) |
| Trusted proxies | IPs whose `X-Forwarded-*` the app (or the next proxy) believes |
| Redirect loop | `ERR_TOO_MANY_REDIRECTS` / `curl: (47) Maximum (50) redirects followed` |

**See it on a real system**

```bash
curl -sIL https://app.example.com/ | grep -ciE '^location'     # count redirects (a loop hits curl's limit: about 50)
docker logs --tail 20 CONTAINER                                 # does the app log the client IP or Traefik's?
grep -rn 'RemoteIP\|ProxyPreserveHost\|RequestHeader' /etc/apache2/sites-enabled/
```

**Hands-on lab (test VM only)**: see exactly what a proxy sends, then produce a 502.

```bash
# 1. Build: Apache reverse-proxies vhost A to a fake backend (nc) on 127.0.0.1:9000
sudo a2enmod proxy proxy_http
sudo tee /etc/apache2/sites-available/lab.conf >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName a.example.com
    ProxyPass        / http://127.0.0.1:9000/
    ProxyPassReverse / http://127.0.0.1:9000/
</VirtualHost>
EOF
sudo apachectl configtest && sudo systemctl restart apache2

# 2. Observe: the "backend" prints the raw request Apache forwards (terminal 2)
nc -l 127.0.0.1 9000
# terminal 1:
curl -s -m 30 -H 'Host: a.example.com' http://127.0.0.1/hello
#   terminal 2 shows something like:
#     GET /hello HTTP/1.1
#     Host: 127.0.0.1:9000            <- backend host, NOT a.example.com (ProxyPreserveHost Off)
#     X-Forwarded-For: 127.0.0.1
#     X-Forwarded-Host: a.example.com
#     X-Forwarded-Server: a.example.com
#   (no X-Forwarded-Proto: Apache does not add it by itself)

# 3. Break: press Ctrl+C in terminal 2 (backend dies mid-request) -> curl gets 502 Proxy Error
sudo tail -2 /var/log/apache2/error.log          # AH01102: error reading status line from remote server

# 4. Fix the header gaps the way you would for a real app behind TLS
#    (this lab vhost is plain HTTP, so it sends "http"; in a real :443 vhost you'd set "https")
sudo sed -i 's|^    ProxyPass        /|    ProxyPreserveHost On\n    RequestHeader set X-Forwarded-Proto "http"\n    ProxyPass        /|' /etc/apache2/sites-available/lab.conf
sudo a2enmod headers && sudo apachectl configtest && sudo systemctl restart apache2
nc -l 127.0.0.1 9000     # terminal 2 again, then repeat the curl: Host is now a.example.com, X-Forwarded-Proto present
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Redirect loop behind TLS-terminating proxy | `ERR_TOO_MANY_REDIRECTS`, `curl: (47)` | `curl -sIL URL | grep -i location` | [Learn web servers](29-learn-webservers-proxies.md) |
| All clients logged as the proxy IP | Rate limits/allow-lists treat everyone as one client | app/access log fields; `mod_remoteip` / trusted proxies | [Learn web servers](29-learn-webservers-proxies.md) |
| Keep-alive mismatch | Sporadic 502 under light load, `connection reset` in proxy logs | proxy and app idle timeouts | [Site down playbook](25-playbook-site-down.md) |
| WebSocket fails through proxy | 400/404 on upgrade, or 101 never arrives | `curl -v` with `-H 'Upgrade: websocket' -H 'Connection: Upgrade'` | [Learn web servers](29-learn-webservers-proxies.md) |
| App generates `http://` links on an https site | Mixed-content warnings | X-Forwarded-Proto handling in the app | [Learn web servers](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting:** When you move apps from Apache to
Traefik, these headers change. Apache's mod_proxy and Traefik add different
defaults. Many "the app broke after the migration" bugs are a missing
`X-Forwarded-Proto` or Host header, not the app itself.

**Next step:** the protocol versions. HTTP/2 and HTTP/3 change how the bytes
travel, which changes what can break.

### HTTP/1.1, HTTP/2 and HTTP/3

**Level:** [L2 · Mid].

**Concept.** The semantics (methods, headers, codes) are the same in all
three. The transport differs:

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Wire format | Text | Binary frames | Binary frames over QUIC |
| Transport | TCP (+TLS) | TCP + TLS (in practice) | **UDP 443** (QUIC, TLS 1.3 built in) |
| Concurrency | One request at a time per connection; browsers open ~6 connections | Many streams multiplexed on one connection | Many streams, no TCP head-of-line blocking |
| Header compression | None | HPACK | QPACK |
| Negotiated by | default | TLS **ALPN** `h2` (cleartext `h2c` is rare) | `Alt-Svc: h3=":443"` header, then the client tries UDP |
| Host header | `Host:` | `:authority` pseudo-header | `:authority` |

A proxy can speak HTTP/2 or HTTP/3 to clients and HTTP/1.1 to the backend.
Traefik, nginx and Apache (`mod_http2`) all do this by default. gRPC needs
HTTP/2 end to end (`h2c` to the backend).

**Key terms**

| Term | Meaning |
|---|---|
| ALPN | TLS extension where client and server agree on `h2` or `http/1.1` during the handshake |
| Multiplexing | Several requests in flight on one connection |
| Head-of-line blocking | One lost TCP packet stalls every HTTP/2 stream. QUIC avoids it |
| `Alt-Svc` | Response header advertising HTTP/3 on another port/protocol |

**See it on a real system**

```bash
curl -sI --http1.1 https://app.example.com/ | head -1      # HTTP/1.1 200 OK
curl -sI --http2 https://app.example.com/ | head -1        # HTTP/2 200
curl -sv -o /dev/null https://app.example.com/ 2>&1 | grep -i alpn
curl -sI https://app.example.com/ | grep -i alt-svc        # h3 advertised?
sudo ss -ulpn 'sport = :443'                               # is anything listening on UDP 443 (HTTP/3)?
curl --version | grep -o 'HTTP3'                           # many distro curls are built without HTTP/3
```

```
$ curl -sv -o /dev/null https://app.example.com/ 2>&1 | grep -i alpn
* ALPN: curl offers h2,http/1.1
* ALPN: server accepted h2
$ curl -sI https://app.example.com/ | grep -i alt-svc
alt-svc: h3=":443"; ma=2592000
```

**Hands-on lab (test VM only)**: watch ALPN choose the protocol.

```bash
# 1. Against any HTTPS site you control (or a public one), compare offers
openssl s_client -connect app.example.com:443 -servername app.example.com -alpn h2,http/1.1 </dev/null 2>/dev/null | grep -i 'ALPN protocol'
openssl s_client -connect app.example.com:443 -servername app.example.com -alpn http/1.1 </dev/null 2>/dev/null | grep -i 'ALPN protocol'
# 2. Break (conceptually): a server without h2 support -> "No ALPN negotiated"; clients silently fall back to HTTP/1.1
# 3. HTTP/3 check: Alt-Svc present but UDP 443 blocked by a firewall -> browsers retry over TCP; works, but every new visit pays a delay
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| App sends HTTP/1-only headers through an h2 proxy | `curl: (92) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR` | `curl --http1.1 -v URL` (works?) | [Learn web servers](29-learn-webservers-proxies.md) |
| gRPC through a proxy speaking HTTP/1.1 to the backend | gRPC `UNAVAILABLE`, 502 | proxy scheme to backend (`h2c://`) | [Learn web servers](29-learn-webservers-proxies.md) |
| HTTP/3 advertised, UDP 443 blocked | Slow first connections in browsers | `sudo ss -ulpn 'sport = :443'`, firewall for 443/udp | section 7 |

**Why it matters for troubleshooting:** If something works with
`curl --http1.1` and fails by default (h2), the bug is protocol-specific.
That's a very different search from "the app is down".

**Next step:** almost all of this traffic is wrapped in TLS. TLS is next.

---

## 10. TLS and certificates

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Security → *SSL & TLS Basics* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands → *Work With SSL Certificates* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 3) Video: ByteByteGo *SSL, TLS, HTTPS Explained* (5 min, [YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo)) · 4) Note: [Web, HTTP & TLS reference](18-web-http-tls.md) and Harbor *Configure HTTPS Access to Harbor* ([docs](https://goharbor.io/docs/2.15.0/install-config/configure-https/)) · 5) Practice: the [badssl.com](https://badssl.com/) drill and the private-CA lab below · 6) Kubernetes: *Certified Kubernetes Administrator (CKA)* — Security → *TLS Basics* ([lesson](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) before the mutual TLS topic.

### The TLS handshake, SNI and ALPN

**Level:** [L2 · Mid].

**Concept.** TLS gives a TCP connection three properties: **encryption**,
**integrity** and **server authentication** (the client checks the server's
certificate). Before any HTTP is sent, the client and server do a
**handshake**. In its first message (**ClientHello**) the client sends,
unencrypted, the name it wants: **SNI** (Server Name Indication). With SNI,
one IP:443 can serve many certificates. It also sends **ALPN** (which HTTP
version it speaks). The server picks the certificate for that name. If no
certificate matches, it uses its **default certificate**: Traefik's
self-signed `TRAEFIK DEFAULT CERT`, or the certificate of Apache's first
`*:443` vhost. That's where "wrong certificate" errors come from.

```
 TLS 1.3 (1 round trip)
 client                                                         server
   │ ── ClientHello: versions, ciphers, key share,                 │
   │                 SNI=app.example.com, ALPN=h2,http/1.1 ───────► │  pick cert for SNI, pick ALPN
   │ ◄── ServerHello (key share)                                    │
   │     {EncryptedExtensions (ALPN=h2), Certificate chain,         │
   │      CertificateVerify, Finished} ──────────────────────────── │
   │  verify: chain -> trusted root? name in SAN? dates valid?      │
   │ ── {Finished} ───────────────────────────────────────────────► │
   │ ══ encrypted HTTP/2 ══════════════════════════════════════════ │
 TLS 1.2 needs 2 round trips. TLS 1.0/1.1 are obsolete and refused by modern clients.
```

**Key terms**

| Term | Meaning |
|---|---|
| SNI | Hostname in the ClientHello. Selects the certificate (and Traefik's TLS router) |
| ALPN | Protocol negotiation inside the handshake (`h2`, `http/1.1`, `acme-tls/1`) |
| Cipher suite | Algorithms used, e.g. `TLS_AES_256_GCM_SHA384` |
| Default certificate | Served when SNI matches nothing (or no SNI was sent) |
| TLS passthrough | Proxy routes by SNI without decrypting (Traefik TCP router `HostSNI`) |
| Session resumption | Cheaper reconnects using tickets/PSK |

**See it on a real system**

```bash
# Pass -servername (SNI) explicitly. OpenSSL 1.1.1+ sends the -connect hostname as SNI by itself,
# but never for an IP address, and older/other clients may not: then you get the default certificate
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | grep -E '^subject=|^issuer=|Verify return'
openssl s_client -connect 192.0.2.10:443 </dev/null 2>/dev/null | grep -E '^subject='       # no SNI -> default cert
curl -sv -o /dev/null https://app.example.com/ 2>&1 | grep -E 'SSL connection|ALPN|subject:|issuer:'
```

```
$ openssl s_client -connect 192.0.2.10:443 </dev/null 2>/dev/null | grep -E '^subject='
subject=CN = TRAEFIK DEFAULT CERT
```

- With no SNI, Traefik has no name to match and serves its default
  self-signed certificate. A client that sends a name Traefik has no router
  for gets the same thing. When you see this, check the router rule/domain,
  not the certificate.

**Hands-on lab (test VM only)**: one port, two certificates, chosen by SNI.

```bash
# 1. Build two self-signed certs (lab only)
mkdir -p ~/tlslab && cd ~/tlslab
openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=default.lab.example.com' \
  -addext 'subjectAltName=DNS:default.lab.example.com' -keyout default.key -out default.crt
openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj '/CN=app.lab.example.com' \
  -addext 'subjectAltName=DNS:app.lab.example.com' -keyout app.key -out app.crt

# 2. A TLS server that serves app.crt for SNI app.lab.example.com, default.crt otherwise (terminal 2)
openssl s_server -accept 8443 -cert default.crt -key default.key \
  -servername app.lab.example.com -cert2 app.crt -key2 app.key -www

# 3. Observe SNI selection
openssl s_client -connect 127.0.0.1:8443 -servername app.lab.example.com </dev/null 2>/dev/null | grep '^subject='
openssl s_client -connect 127.0.0.1:8443 -servername other.lab.example.com </dev/null 2>/dev/null | grep '^subject='
openssl s_client -connect 127.0.0.1:8443 -noservername </dev/null 2>/dev/null | grep '^subject='

# 4. Break: curl to a name the server has no cert for
curl -sv --resolve other.lab.example.com:8443:127.0.0.1 https://other.lab.example.com:8443/ -o /dev/null 2>&1 | tail -2
#   SSL certificate problem: self-signed certificate
#   (it received default.crt; even with that cert trusted, the name would not match)

# 5. Capture the SNI in clear text (terminal 3), then repeat step 3
sudo tcpdump -ni lo -A -c 8 'tcp port 8443' | grep -a 'lab.example.com'
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| No router/vhost for the SNI | `TRAEFIK DEFAULT CERT`, `no alternative certificate subject name matches` | `openssl s_client ... -servername NAME` (subject) | [Containers playbook](26-playbook-containers-k8s.md) |
| Client too old / server too strict | `tlsv1 alert protocol version`, `handshake failure` | `openssl s_client -connect H:443 -tls1_2` | [Web reference](18-web-http-tls.md) |
| Something inspects/blocks TLS (corporate proxy) | Unexpected issuer (proxy's CA) | check the `issuer=` line | next topics |
| Handshake hangs after ClientHello | Large certificate packet lost: MTU problem | `ping -M do -s 1472 HOST` | section 12 |

**Why it matters for troubleshooting:** SNI is why `curl https://IP/` and
`curl https://name/` can give different certificates, and why `--resolve`
(which keeps SNI) is the right way to test a backend by IP.

**Next step:** what the client actually checks in the certificate it gets:
the chain of trust.

### Certificates and the chain of trust

**Level:** [L1 · Junior] to read a certificate with openssl · [L2 · Mid] to diagnose chain errors.

**Concept.** A certificate binds a **public key** to **names** (in the
Subject Alternative Name, SAN), signed by an **issuer**. The client trusts it
if it can build a **chain** from the server's certificate (leaf) through
**intermediates** to a **root CA** that's already in its **trust store**, and
every link is valid (dates, signatures, usage). The **server must send the
leaf plus all intermediates**. The root is never sent; the client already has
it. Missing intermediates are the most common chain bug: browsers often
paper over it (they cache or fetch intermediates), while curl, Python, Java
and Go fail.

```
 trust store (/etc/ssl/certs)            sent by the server
 ┌──────────────────────────┐   signs   ┌───────────────────────────┐  signs  ┌─────────────────────────────┐
 │ ISRG Root X1 (root CA)   │ ────────► │ R11 (intermediate CA)     │ ──────► │ CN=app.example.com (leaf)   │
 │ self-signed, trusted     │           │ must be sent by the server│         │ SAN: app.example.com        │
 └──────────────────────────┘           └───────────────────────────┘         │ valid Sep 1 - Nov 30 2026   │
                                                                              └─────────────────────────────┘
 client checks: chain complete? root trusted? name in SAN? now between notBefore/notAfter? key usage ok?
```

**Key terms**

| Term | Meaning |
|---|---|
| Leaf / intermediate / root | Server cert / CA cert that signs leaves / self-signed anchor in the trust store |
| SAN | `subjectAltName`: the names (DNS, IP) the cert is valid for. Modern clients **ignore CN** |
| notBefore / notAfter | Validity window. A wrong client clock breaks it (see [Time & NTP](12-time-ntp.md)) |
| Full chain | Leaf + intermediates in one file (`fullchain.pem`), what servers must present |
| PEM / DER | Base64 text with `-----BEGIN CERTIFICATE-----` / binary |
| Wildcard | `*.example.com` covers one label: `a.example.com`, not `example.com` or `a.b.example.com` |

**See it on a real system**

```bash
openssl s_client -connect app.example.com:443 -servername app.example.com -showcerts </dev/null
# Just the useful fields of the leaf:
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
# A cert file on disk:
openssl x509 -in /etc/ssl/certs/ssl-cert-snakeoil.pem -noout -text | less
openssl x509 -in cert.pem -noout -checkend 2592000 && echo "valid > 30 days" || echo "expires within 30 days"
```

```
$ openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null
CONNECTED(00000003)
depth=2 C = US, O = Internet Security Research Group, CN = ISRG Root X1
verify return:1
depth=1 C = US, O = Let's Encrypt, CN = R11
verify return:1
depth=0 CN = app.example.com
verify return:1
---
Certificate chain
 0 s:CN = app.example.com
   i:C = US, O = Let's Encrypt, CN = R11
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Sep  1 08:12:03 2026 GMT; NotAfter: Nov 30 08:12:02 2026 GMT
 1 s:C = US, O = Let's Encrypt, CN = R11
   i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
   a:PKEY: rsaEncryption, 2048 (bit); sigalg: RSA-SHA256
   v:NotBefore: Mar 13 00:00:00 2024 GMT; NotAfter: Mar 12 23:59:59 2027 GMT
---
...
SSL handshake has read 3134 bytes and written 401 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
...
    Verify return code: 0 (ok)

$ echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
subject=CN = app.example.com
issuer=C = US, O = Let's Encrypt, CN = R11
notBefore=Sep  1 08:12:03 2026 GMT
notAfter=Nov 30 08:12:02 2026 GMT
X509v3 Subject Alternative Name:
    DNS:app.example.com
```

- `Certificate chain` lists what the **server sent**: 0 = leaf, 1 =
  intermediate. If you see only `0`, the intermediate is missing.
- Each `s:` (subject) must equal the `i:` (issuer) of the line above. That's
  the chain.
- `depth=2 ... ISRG Root X1` came from the local trust store, not from the
  server.
- `Verify return code: 0 (ok)` means the whole chain validated. Any other
  number names the problem (e.g. `20 (unable to get local issuer
  certificate)`, `10 (certificate has expired)`, `18/19` self-signed).

**Hands-on lab (internet access)**: the badssl.com error drill. Run each one,
write down the exact error, and match it to the cause.

```bash
for h in expired wrong.host self-signed untrusted-root incomplete-chain; do
  echo "== $h"; curl -sS -o /dev/null https://$h.badssl.com/ 2>&1
done
openssl s_client -connect incomplete-chain.badssl.com:443 -servername incomplete-chain.badssl.com </dev/null 2>/dev/null | sed -n '/Certificate chain/,/---/p'
curl -sS -o /dev/null https://tls-v1-0.badssl.com:1010/ 2>&1      # obsolete protocol version
```

| Host | Error you should get (curl + OpenSSL 3) | Real-world equivalent |
|---|---|---|
| expired | `SSL certificate problem: certificate has expired` | Renewal failed, or **your clock is wrong** |
| wrong.host | `SSL: no alternative certificate subject name matches target host name` | Name not in SAN; Traefik/Apache default cert |
| self-signed | `SSL certificate problem: self-signed certificate` | Test cert, Harbor default install |
| untrusted-root | `SSL certificate problem: self-signed certificate in certificate chain` | Private CA not in this machine's trust store |
| incomplete-chain | `SSL certificate problem: unable to get local issuer certificate` | Server config uses `cert.pem` instead of `fullchain.pem` |
| tls-v1-0 (port 1010) | `... tlsv1 alert protocol version` or `unsupported protocol` | Legacy appliance vs modern client |

> [badssl.com](https://badssl.com/) is community-maintained. If a "good" host
> there fails too, the site's own certificates may have lapsed. Compare
> against a site you know is healthy before you draw conclusions.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Missing intermediate | `unable to get local issuer certificate` in curl/Python/Java; browsers fine | `openssl s_client ... -showcerts` (only cert 0) | [Web reference](18-web-http-tls.md) |
| Expired | `certificate has expired`; monitoring alerts | `... | openssl x509 -noout -dates` | [Site down playbook](25-playbook-site-down.md) |
| Clock wrong on the *client* | Valid certs "expired" or "not yet valid" | `timedatectl` | [Time & NTP](12-time-ntp.md) |
| Name mismatch | `no alternative certificate subject name matches` | `... | openssl x509 -noout -ext subjectAltName` | [Site down playbook](25-playbook-site-down.md) |
| Key doesn't match cert (after manual renewal) | Server refuses to start: `key values mismatch` (nginx), `AH02565` (Apache) | compare `openssl x509 -noout -pubkey -in cert.pem` with `openssl pkey -pubout -in key.pem` | [Web reference](18-web-http-tls.md) |

**Why it matters for troubleshooting:** Every TLS error message maps to one
link in the chain picture. Read the error, find the link (missing
intermediate, untrusted root, wrong name, wrong date) and you know whether to
fix the server, the client's trust store or the clock.

**Next step:** your own CA. Harbor, internal GitLab and lab services use
certificates from a private CA, and every client must be taught to trust it.

### Private CAs and trust stores

**Level:** [L2 · Mid] · running the CA and distributing it to every host for Harbor is [L3 · Senior].

**Concept.** A private CA is just a root certificate you created. It works
exactly like a public CA, but **no machine trusts it until you install it**.
There isn't one trust store per machine. The OS has one, and Docker,
containerd, Java, Python, Node and every container image can each have their
own. "x509: certificate signed by unknown authority" means *this particular
client* lacks the root. On Ubuntu you add a PEM file with a `.crt` extension
to `/usr/local/share/ca-certificates/` and run `update-ca-certificates`,
which rebuilds `/etc/ssl/certs/ca-certificates.crt`.

| Client | Where it looks | How to add your CA |
|---|---|---|
| Ubuntu OS (curl, wget, apt, git, most C programs) | `/etc/ssl/certs/ca-certificates.crt` | copy to `/usr/local/share/ca-certificates/NAME.crt` + `sudo update-ca-certificates` |
| RHEL/Rocky OS | `/etc/pki/tls/certs/ca-bundle.crt` | copy to `/etc/pki/ca-trust/source/anchors/` + `sudo update-ca-trust` |
| Docker daemon (pull/push to Harbor) | system store + `/etc/docker/certs.d/HOST[:PORT]/ca.crt` | put `ca.crt` there (no restart needed for certs.d) |
| containerd (Kubernetes nodes) | `/etc/containerd/certs.d/HOST/hosts.toml` (only if the CRI registry `config_path` includes that directory: check with `sudo containerd config dump | grep config_path`) | `hosts.toml` with `ca = ".../ca.crt"`, on **every** node |
| A container's app | the *image's* `/etc/ssl/certs` | add the CA in the Dockerfile, or mount it |
| Python requests | `certifi` bundle | `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` |
| Node.js | built-in bundle | `NODE_EXTRA_CA_CERTS=/path/ca.crt` |
| Java | `cacerts` keystore | `keytool -importcert -cacerts -alias labca -file ca.crt` |
| GitLab Runner | system + its own config | `tls-ca-file` in runner `config.toml` |
| Firefox | its own NSS store | import, or enable enterprise roots |

**Key terms**

| Term | Meaning |
|---|---|
| Root CA cert | Self-signed, `CA:TRUE`. This is what you distribute |
| CA key | The secret that signs. Keep it offline / protected; whoever has it can impersonate any host |
| CSR | Certificate signing request: public key + requested names |
| Extensions | `basicConstraints`, `keyUsage`, `extendedKeyUsage` (`serverAuth`, `clientAuth`), `subjectAltName` |

**See it on a real system**

```bash
ls -l /usr/local/share/ca-certificates/                 # locally added CAs
grep -c 'BEGIN CERTIFICATE' /etc/ssl/certs/ca-certificates.crt   # roots in the bundle
ls /etc/docker/certs.d/ 2>/dev/null                      # registries with custom CAs (Docker)
ls /etc/containerd/certs.d/ 2>/dev/null                  # registries with custom CAs (containerd)
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts </dev/null 2>/dev/null | grep -E ' s:| i:'
```

```
$ sudo update-ca-certificates
Updating certificates in /etc/ssl/certs...
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
```

- `1 added` is the success line. The `rehash: warning` about the bundle file
  is normal and harmless.
- If it says `0 added`, the file doesn't end in `.crt`, isn't PEM, or sits in
  the wrong directory.

**Hands-on lab (test VM only)**: build a private CA, issue a server cert, trust it.

```bash
# 1. Build the CA and a server cert with a proper SAN
mkdir -p ~/lab-ca && cd ~/lab-ca
openssl req -x509 -new -nodes -newkey rsa:4096 -days 3650 -subj '/CN=Lab Root CA' -keyout ca.key -out ca.crt
openssl req -new -nodes -newkey rsa:2048 -subj '/CN=app.lab.example.com' -keyout app.key -out app.csr
cat > app.ext <<'EOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:app.lab.example.com
EOF
openssl x509 -req -in app.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -sha256 -extfile app.ext -out app.crt
openssl verify -CAfile ca.crt app.crt                   # app.crt: OK

# 2. Serve it (terminal 2)
openssl s_server -accept 8443 -cert app.crt -key app.key -www

# 3. Break: the client does not trust the CA yet
curl -sS --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/ -o /dev/null
#   curl: (60) SSL certificate problem: unable to get local issuer certificate

# 4. Diagnose: who issued it, and do we have that root?
openssl s_client -connect 127.0.0.1:8443 -servername app.lab.example.com </dev/null 2>/dev/null | grep -E '^issuer=|Verify return'
curl -sS --cacert ca.crt --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/ -o /dev/null && echo "trusted with --cacert"

# 5. Fix system-wide
sudo cp ca.crt /usr/local/share/ca-certificates/lab-root-ca.crt
sudo update-ca-certificates
curl -sS --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/ -o /dev/null && echo "trusted system-wide"

# 6. The container trap: the host trusts it now, a container does not
docker run --rm --network host curlimages/curl -sS --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/ -o /dev/null
#   curl: (60) ... -> images carry their own trust store

# 7. Clean up the trust store
sudo rm /usr/local/share/ca-certificates/lab-root-ca.crt && sudo update-ca-certificates --fresh
```

For Harbor with a private CA, the per-tool fixes look like this (replace
`harbor.example.com` with your registry name):

```bash
# Docker hosts (GitLab runners, Dokploy hosts)
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt

# containerd on every Kubernetes node (the CRI registry config_path must include /etc/containerd/certs.d;
# check with: sudo containerd config dump | grep config_path)
sudo mkdir -p /etc/containerd/certs.d/harbor.example.com
sudo cp ca.crt /etc/containerd/certs.d/harbor.example.com/ca.crt
sudo tee /etc/containerd/certs.d/harbor.example.com/hosts.toml >/dev/null <<'EOF'
server = "https://harbor.example.com"

[host."https://harbor.example.com"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
EOF
sudo crictl pull harbor.example.com/library/alpine:3.20     # test on the node
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Docker can't pull from Harbor | `x509: certificate signed by unknown authority` | `ls /etc/docker/certs.d/HARBOR/` | [Containers playbook](26-playbook-containers-k8s.md) |
| Kubernetes `ImagePullBackOff` from Harbor | `kubectl describe pod` shows the x509 error | `sudo crictl pull IMAGE` on the node; `hosts.toml` | [Learn Kubernetes](31-learn-kubernetes.md) |
| Leaf without SAN | Go clients: `x509: certificate relies on legacy Common Name field, use SANs instead` | `openssl x509 -noout -ext subjectAltName -in cert` | this topic |
| CA added but still untrusted | `0 added` from `update-ca-certificates` | file extension `.crt`? PEM? right directory? | this topic |
| App in a container ignores the host store | Host curl works, container fails | add the CA to the image or mount it | [Learn Docker](30-learn-docker.md) |

**Why it matters for troubleshooting:** Your Harbor registry, GitLab and lab
services all depend on this. When "pull works on one machine and not another",
the answer is almost always that one machine's (or one tool's) trust store
lacks the CA.

**Next step:** sometimes the *server* must check the *client's* certificate
too. That's mutual TLS, and it's everywhere inside Kubernetes.

### Mutual TLS

**Level:** [L3 · Senior] · the certificate topics of the CKA.

**Concept.** In normal TLS only the server proves its identity. In **mTLS**
the server also requests a **client certificate** and verifies it against a
client CA. The certificate *is* the credential. Kubernetes runs on mTLS:
kubelet ↔ API server, API server ↔ etcd, and your kubeconfig usually holds a
client certificate. Service meshes, Docker's TLS-protected daemon socket and
many internal APIs use it too. Failures look like TLS errors, but the cause
is on the client side: a missing, expired or wrongly issued client
certificate.

```
 client                                              server
   │ ── ClientHello ─────────────────────────────────► │
   │ ◄── ServerHello, Certificate, CertificateRequest ─ │  "send me a cert signed by Client CA"
   │ ── Certificate (client), CertificateVerify ──────► │  verify against client CA, check dates/usage
   │ ── Finished ─────────────────────────────────────► │
```

**Key terms**

| Term | Meaning |
|---|---|
| Client certificate | Cert with `extendedKeyUsage=clientAuth`, presented by the client |
| Client CA | The CA the server uses to verify client certs |
| CN / O as identity | Kubernetes maps a client cert's CN to the user and O to groups |
| `kubeadm certs check-expiration` | Lists control-plane cert expiry (they last 1 year by default) |

**See it on a real system**

```bash
# Kubernetes control plane node (read-only)
sudo kubeadm certs check-expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver-kubelet-client.crt -noout -subject -enddate
# Your kubeconfig's client cert identity
kubectl config view --raw -o jsonpath='{.users[0].user.client-certificate-data}' | base64 -d | openssl x509 -noout -subject -enddate
```

```
$ ... | openssl x509 -noout -subject -enddate
subject=O = kubeadm:cluster-admins, CN = kubernetes-admin
notAfter=Aug 14 09:02:11 2027 GMT
```

**Hands-on lab (test VM only)**: reuse the lab CA from the previous topic.

```bash
cd ~/lab-ca
# 1. Build: a client certificate signed by the lab CA
openssl req -new -nodes -newkey rsa:2048 -subj '/CN=ci-runner' -keyout client.key -out client.csr
printf 'basicConstraints=CA:FALSE\nkeyUsage=digitalSignature\nextendedKeyUsage=clientAuth\n' > client.ext
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 30 -sha256 -extfile client.ext -out client.crt

# 2. A server that REQUIRES a client cert from the lab CA (terminal 2)
openssl s_server -accept 8443 -cert app.crt -key app.key -CAfile ca.crt -Verify 1 -www

# 3. Break: connect without a client cert
curl -sS --cacert ca.crt --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/ -o /dev/null
#   fails, e.g. "... alert certificate required" (TLS 1.3) or "handshake failure"

# 4. Fix: present the client cert
curl -sS --cacert ca.crt --cert client.crt --key client.key -o /dev/null -w '%{http_code}\n' \
  --resolve app.lab.example.com:8443:127.0.0.1 https://app.lab.example.com:8443/          # 200
#   terminal 2 (s_server) prints the client certificate's subject: CN = ci-runner
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Expired kubeadm certs | `kubectl`: `x509: certificate has expired or is not yet valid`; API server unreachable | `sudo kubeadm certs check-expiration` | [Learn Kubernetes](31-learn-kubernetes.md) |
| kubelet client cert expired | Node `NotReady`, kubelet log x509 errors | `journalctl -u kubelet -b | grep -i x509` | [Containers playbook](26-playbook-containers-k8s.md) |
| Wrong client CA on server | `unknown ca` / `bad certificate` alert | `openssl x509 -noout -issuer -in client.crt` | this topic |
| Missing `clientAuth` usage | `unsupported certificate purpose` | `openssl x509 -noout -ext extendedKeyUsage -in client.crt` | this topic |

**Why it matters for troubleshooting:** In the CKA and in real clusters,
"certificate expired" breaks the whole control plane in one go, a year after
installation. Knowing that kubelet, kubectl and etcd all authenticate with
client certs tells you where to look.

**Next step:** public certificates for your sites come from Let's Encrypt
through ACME, which Traefik and Dokploy run automatically. Learn how it works
so you can fix it when it doesn't.

### ACME and Let's Encrypt: HTTP-01 vs DNS-01

**Level:** [L2 · Mid] · choosing HTTP-01 or DNS-01 per environment is [L3 · Senior].

**Concept.** **ACME** is the protocol Let's Encrypt uses to issue
certificates automatically. You prove you control a domain by solving a
**challenge**, then the CA signs a certificate (90 days today; Let's Encrypt
has announced shorter lifetimes, so renewal must be automatic). Traefik
(and therefore Dokploy) runs an ACME client built in, stores certificates in
an `acme.json` file, and renews them ahead of expiry.

```
 HTTP-01 (Dokploy/Traefik default)                 DNS-01
 1. Traefik asks LE for app.example.com            1. client asks LE for *.example.com
 2. LE: "serve TOKEN at                            2. LE: "publish TXT _acme-challenge.example.com = VALUE"
    http://app.example.com/.well-known/            3. client creates the TXT via the DNS provider's API
    acme-challenge/TOKEN"                          4. LE queries public DNS for the TXT
 3. LE connects from the INTERNET to port 80       5. certificate issued
    of the IP that public DNS gives for the name   needs: DNS API credentials; works for wildcards and
 4. Traefik answers -> certificate issued                 for hosts NOT reachable from the internet
 needs: public A/AAAA -> you, inbound TCP 80 open,
        nothing else answering on :80 (Apache!)
 TLS-ALPN-01: same idea on port 443 via ALPN "acme-tls/1" (Traefik tlsChallenge)
```

| | HTTP-01 | DNS-01 | TLS-ALPN-01 |
|---|---|---|---|
| Port needed from internet | 80 | none | 443 |
| Wildcards | no | **yes** | no |
| Internal-only hosts | no | **yes** | no |
| Needs DNS API credentials | no | yes | no |
| Typical breakage | Port 80 blocked/taken, wrong DNS, redirect quirks | API token, propagation delay, split DNS | Port 443 taken, TLS passthrough in front |

**Key terms**

| Term | Meaning |
|---|---|
| Certificate resolver | Traefik's name for an ACME configuration (`certificatesResolvers.letsencrypt`) |
| `acme.json` | Traefik's storage of account key and certificates. Must be mode 600 |
| Staging environment | Let's Encrypt's test CA. Use it while experimenting to avoid rate limits |
| Rate limits | Let's Encrypt limits issuance (for example duplicate certificates per week). Repeated failed attempts can lock you out for a while |
| CAA | DNS record that can forbid Let's Encrypt (section 8) |

**See it on a real system**

```bash
docker logs dokploy-traefik 2>&1 | grep -iE 'acme|certificate|error' | tail -20     # Traefik's ACME log lines
sudo ls -l /etc/dokploy/traefik/                     # Dokploy's Traefik config + acme storage location
dig +short app.example.com                           # does public DNS point at THIS server?
dig +short app.example.com CAA                       # is Let's Encrypt allowed?
curl -sv http://app.example.com/.well-known/acme-challenge/test 2>&1 | grep -E 'Connected|< HTTP|< Server'   # who answers on :80?
```

Traefik's static configuration for HTTP-01 looks like this (Dokploy generates
an equivalent file for you):

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/dokploy/traefik/dynamic/acme.json
      httpChallenge:
        entryPoint: web
```

Typical errors in Traefik's log (abbreviated) and what they mean:

```
... acme: error: 403 :: urn:ietf:params:acme:error:unauthorized :: ... Invalid response from http://app.example.com/.well-known/acme-challenge/...: 404
    -> port 80 is answered by something else (Apache!) or the request never reaches Traefik's router
... acme: error: 400 :: urn:ietf:params:acme:error:connection :: ... Timeout during connect (likely firewall problem)
    -> inbound TCP 80 blocked from the internet (firewall, NAT, security group)
... acme: error: 400 :: urn:ietf:params:acme:error:dns :: DNS problem: NXDOMAIN looking up A for app.example.com
    -> public DNS record missing (internal-only names can't use HTTP-01)
... urn:ietf:params:acme:error:caa :: CAA record for app.example.com prevents issuance
    -> fix the CAA record
... urn:ietf:params:acme:error:rateLimited :: too many ...
    -> stop retrying; wait for the window to pass; test against staging
```

**Hands-on lab (test VM + a real domain you control, optional)**

```bash
# 1. Build: a public test VM with Dokploy (or Traefik) and an A record test.YOURDOMAIN -> its IP.
#    Use the Let's Encrypt STAGING CA while you experiment (set caServer in the resolver).
# 2. Break: block inbound TCP 80 at the firewall / security group, then request a certificate
#    (if instead Apache holds *:80, dokploy-traefik can't even start: `docker ps -a` shows it Created/Exited)
sudo ss -ltnp 'sport = :80'                  # who really owns :80?
docker logs dokploy-traefik 2>&1 | grep -i acme | tail -5    # "Timeout during connect" or 404 "unauthorized"
# 3. Fix: free port 80 for Traefik (it redirects HTTP->HTTPS itself after issuance), open 80 inbound, retry
# 4. Verify: issuer is Let's Encrypt (or "(STAGING)" while testing)
echo | openssl s_client -connect test.YOURDOMAIN:443 -servername test.YOURDOMAIN 2>/dev/null | openssl x509 -noout -issuer -dates
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Port 80 from the internet still reaches Apache during migration (NAT rule or Apache on the public IP; if Apache holds `*:80`, Traefik doesn't start at all) | `unauthorized ... 404` in Traefik log; site serves `TRAEFIK DEFAULT CERT` | `sudo ss -ltnp 'sport = :80'` | [Apache/Dokploy case](21-case-apache-443-dokploy.md) |
| Port 80 blocked from outside | `Timeout during connect (likely firewall problem)` | external check, firewall/NAT rules | [Site down playbook](25-playbook-site-down.md) |
| Internal-only host | HTTP-01 can never work | switch to DNS-01 or the private CA | section 10 private CA |
| `acme.json` permissions/corruption | Traefik: `permissions 644 for acme.json are too open` | `ls -l acme.json` (must be 600) | [Containers playbook](26-playbook-containers-k8s.md) |
| Rate limited after many retries | `rateLimited` | stop, use staging, fix the cause first | this topic |

**Why it matters for troubleshooting:** In your incident, Dokploy needed 443
*and* 80. Port 80 is what Let's Encrypt's HTTP-01 challenge connects to.
Dokploy's `dokploy-traefik` container publishes 80 and 443 together, so if
Apache still holds `*:80` the container doesn't start at all (the bind error
from section 5). The quieter failure is when port 80 from the internet still
lands on Apache anyway (a NAT or firewall rule forwarding :80 to it, or Apache
bound to the public IP the DNS name resolves to). Then certificates silently
fail to issue and every site shows `TRAEFIK DEFAULT CERT`.

**Next step:** with one service per name working, scale out: several backends
behind one name means load balancing and health checks.

---

## 11. Load balancing and health checks

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Implement Reverse Proxies and Load Balancers* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 2) KodeKloud: *Nginx For Beginners* — Intermediate Config → Load Balancer, then Performance → *Monitoring & Troubleshooting* ([course](https://kodekloud.com/courses/nginx-for-beginners), [lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Performance/Monitoring-Troubleshooting/page)) · 3) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress → *Traefik Overview* ([lesson](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) · 4) Note: [Learn web servers and proxies](29-learn-webservers-proxies.md) · 5) Practice: the 502/504 lab below, then the Ops Ladder Traefik drill (wrong port gives 502; fix it from the Traefik log alone).

### L4 versus L7 load balancing

**Level:** [L2 · Mid] to debug it · [L3 · Senior] to choose between L4 and L7.

**Concept.** A load balancer spreads connections or requests over several
backends. An **L4** balancer works on TCP/UDP connections: it sees IPs and
ports, picks a backend per *connection* and forwards bytes without
understanding them. It's fast and protocol-agnostic, but it can't route by
URL or Host. An **L7** balancer terminates HTTP (and usually TLS): it reads
the Host, path and headers, routes per *request*, can retry, add headers and
rewrite. That's Traefik's HTTP routers, nginx, HAProxy in http mode and AWS
ALB. A Kubernetes Service (kube-proxy) is L4. An Ingress or Gateway is L7.

```
 L4 (Kubernetes Service, Traefik TCP router, AWS NLB, HAProxy mode tcp)
   client ──TCP──► VIP:5432 ──(pick per connection, NAT or pass-through)──► db-1:5432 | db-2:5432
   sees: IP, port, (SNI if TLS passthrough). Client IP preserved only with DSR/no-SNAT or PROXY protocol

 L7 (Traefik HTTP router, nginx, Apache mod_proxy_balancer, AWS ALB, Ingress)
   client ──HTTPS──► proxy terminates TLS, reads "Host: app.example.com", "GET /api/..."
                     ├── /api  -> api-1:8000 | api-2:8000   (per request, retries, headers)
                     └── /     -> web-1:3000
   client IP passed in X-Forwarded-For
```

| | L4 | L7 |
|---|---|---|
| Unit balanced | Connection | Request |
| Routing on | IP, port (SNI for TLS passthrough) | Host, path, headers, cookies |
| TLS | Passed through (or terminated by some) | Usually terminated at the proxy |
| Client IP for the backend | Kept (no SNAT) or via PROXY protocol | `X-Forwarded-For` |
| Error codes it can produce | None: just resets/timeouts | 502, 503, 504 |
| Examples in your stack | K8s Service, Traefik TCP router (`HostSNI`), Swarm routing mesh | Traefik HTTP router, Ingress, nginx, Apache |

**Key terms**

| Term | Meaning |
|---|---|
| Round robin / least connections | Rotate through backends / pick the one with the fewest active connections |
| Hash / sticky sessions | Same client → same backend (by IP hash or cookie) |
| VIP | Virtual IP the clients use (keepalived, cloud LB, K8s ClusterIP) |
| PROXY protocol | A header the L4 balancer prepends so the backend learns the client IP. Both sides must agree |
| Connection draining | Let in-flight requests finish before removing a backend |
| HTTP/2 and L4 | One long-lived h2/gRPC connection pins all of a client's requests to one backend |

**See it on a real system**

```bash
for i in $(seq 1 6); do curl -s https://app.example.com/whoami | grep -i hostname; done   # distribution (traefik/whoami)
kubectl get endpointslices -l kubernetes.io/service-name=SERVICE     # L4 backends of a K8s Service
sudo iptables -t nat -S | grep -c KUBE-SEP                           # kube-proxy (iptables mode) backend rules
docker service ps SERVICE                                            # Swarm tasks behind a service VIP
```

**Hands-on lab (test VM only)**: an L7 balancer, then make it return 502 and 504.

```bash
# 1. Build: two backends on loopback and nginx in front
sudo systemctl stop apache2 2>/dev/null   # free :80 first, or nginx's default site fails to start:
                                          #   nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
sudo apt install -y nginx
mkdir -p /tmp/b1 /tmp/b2; echo backend-1 > /tmp/b1/index.html; echo backend-2 > /tmp/b2/index.html
python3 -m http.server 8081 --bind 127.0.0.1 --directory /tmp/b1 &
python3 -m http.server 8082 --bind 127.0.0.1 --directory /tmp/b2 &
sudo tee /etc/nginx/conf.d/lb-lab.conf >/dev/null <<'EOF'
upstream lab_backends {
    server 127.0.0.1:8081 max_fails=2 fail_timeout=10s;
    server 127.0.0.1:8082 max_fails=2 fail_timeout=10s;
}
server {
    listen 8080;
    location / {
        proxy_pass http://lab_backends;
        proxy_read_timeout 5s;
    }
}
EOF
sudo nginx -t && sudo systemctl reload nginx
for i in 1 2 3 4; do curl -s http://127.0.0.1:8080/; done           # alternates 1,2,1,2

# 2. Break one backend: clients don't notice (nginx retries the other one)
kill %2                                                               # stop backend-2
for i in 1 2 3 4; do curl -s -o /dev/null -w '%{http_code} ' http://127.0.0.1:8080/; done; echo
sudo tail -3 /var/log/nginx/error.log      # connect() failed (111: Connection refused) while connecting to upstream

# 3. Break both: 502
kill %1
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/      # 502

# 4. A backend that accepts but never answers: 504 (single upstream on 8083)
sudo sed -i -e 's/127.0.0.1:8081 /127.0.0.1:8083 /' -e '/127.0.0.1:8082/d' /etc/nginx/conf.d/lb-lab.conf
sudo nginx -t && sudo systemctl reload nginx
nc -lk 127.0.0.1 8083 >/dev/null &
curl -s -o /dev/null -w '%{http_code} after %{time_total}s\n' http://127.0.0.1:8080/   # 504 after ~5 s
sudo tail -2 /var/log/nginx/error.log      # upstream timed out (110: Connection timed out) while reading response header

# 5. Clean up
kill $!; sudo rm /etc/nginx/conf.d/lb-lab.conf && sudo systemctl reload nginx   # $! = the nc from step 4 (jobs 1 and 2 are gone, so it isn't %3)
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| All backends down / wrong port | 502; proxy log `Connection refused` / `no route to host` | proxy error log, `ss -ltn` on the backend | [Site down playbook](25-playbook-site-down.md) |
| No healthy backends | 503 (Traefik, K8s ingress); nginx returns 502 and logs `no live upstreams` | health status, `kubectl get endpoints` | next topic |
| Backend slower than proxy timeout | 504 after a fixed number of seconds | `curl -w '%{time_total}'` direct to the backend | [Slow system playbook](23-playbook-slow-system.md) |
| Uneven load | One backend hot, others idle (long-lived h2/gRPC/WebSocket connections on L4) | per-backend request counts | [Learn performance](32-learn-performance-observability.md) |
| Sessions lost after scaling | Users logged out at random | sticky sessions or a shared session store | [Learn web servers](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting:** The status code tells you which layer
of the balancer failed. 502 means it couldn't talk to any backend. 503 means
it had none it considered healthy. 504 means a backend took too long. Each
points at a different fix.

**Next step:** how the balancer decides a backend is "healthy" is a common
source of outages by itself.

### Health checks

**Level:** [L2 · Mid] · designing shallow vs deep checks for a platform is [L3 · Senior].

**Concept.** **Active** health checks probe each backend on a schedule (GET
`/health` every 10 s). **Passive** checks watch real traffic and eject a
backend after errors (nginx `max_fails`). Kubernetes splits the idea:
**readiness** decides whether a pod gets traffic (it's removed from Service
endpoints when not ready), and **liveness** decides whether the container is
*restarted*. Docker's `HEALTHCHECK` sets a container's status, and Traefik's
Docker provider **skips containers that aren't healthy**, so their routes
disappear. A good health endpoint is cheap, answers fast, and checks only
what *this* instance needs to serve traffic.

| Mechanism | Effect of failing | Typical mistake |
|---|---|---|
| LB active check | Backend removed from rotation | Check hits a path that needs auth or the right Host → always "down" |
| Passive (`max_fails`) | Backend skipped for `fail_timeout` | Thresholds too sensitive → flapping |
| K8s readiness probe | Pod removed from endpoints → 503 if all fail | Probe checks the database → DB blip removes *every* pod |
| K8s liveness probe | Container restarted | Liveness too aggressive → restarts during slow startup → CrashLoopBackOff |
| Docker HEALTHCHECK + Traefik | Container ignored by Traefik → router missing → 404 | Health command uses a tool missing from the image (`curl: not found`) |

**Key terms**

| Term | Meaning |
|---|---|
| Interval / timeout / retries | How often, how long to wait, how many failures before "unhealthy" |
| Start period / startupProbe | Grace time for slow starters before failures count |
| Shallow vs deep check | Process up and serving vs all dependencies OK. Use shallow for liveness |
| Flapping | Backend toggles healthy/unhealthy repeatedly |

**See it on a real system**

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'                 # "(healthy)" / "(unhealthy)"
docker inspect --format '{{json .State.Health}}' CONTAINER | python3 -m json.tool | tail -15   # last probe outputs
kubectl get endpoints SERVICE                                       # empty = no ready pods
kubectl describe pod POD | grep -A3 -E 'Liveness|Readiness'         # probe definitions and failures
```

```
$ docker ps --format 'table {{.Names}}\t{{.Status}}'
NAMES             STATUS
dokploy-traefik   Up 3 days
shop-web          Up 2 hours (healthy)
crm-api           Up 14 minutes (unhealthy)
```

- `crm-api` is unhealthy, so Traefik dropped it and its domain answers
  `404 page not found`. The fix is in the health check or the app, not in
  Traefik.
- That's Traefik's Docker provider (containers routed by labels, such as
  Compose apps). An app that Dokploy routes to a Swarm service behaves
  differently: Swarm replaces the unhealthy task, so check
  `docker service ps SERVICE` too.

**Hands-on lab (test VM only, Docker installed)**

```bash
# 1. Build: a container with a health check
docker run -d --name hc --health-cmd 'wget -qO- http://127.0.0.1/ >/dev/null || exit 1' \
  --health-interval 5s --health-retries 2 nginx:alpine
sleep 12; docker ps --filter name=hc --format '{{.Names}} {{.Status}}'      # (healthy)

# 2. Break: the app stops serving its index (wget gets 403)
docker exec hc rm /usr/share/nginx/html/index.html
sleep 15; docker ps --filter name=hc --format '{{.Names}} {{.Status}}'      # (unhealthy)

# 3. Diagnose from the probe's own output
docker inspect --format '{{range .State.Health.Log}}{{.ExitCode}} {{.Output}}{{end}}' hc | tail -3

# 4. Fix
docker exec hc sh -c 'echo ok > /usr/share/nginx/html/index.html'
sleep 10; docker ps --filter name=hc --format '{{.Names}} {{.Status}}'      # (healthy) again
docker rm -f hc
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Health check wrong, app fine | 503/404 at the proxy while `curl` to the app works | `docker inspect ... .State.Health`, probe definition | [Containers playbook](26-playbook-containers-k8s.md) |
| Deep check cascades | Every instance "down" when one dependency blips | which dependencies the health endpoint checks | [Learn performance](32-learn-performance-observability.md) |
| Liveness kills slow starters | `CrashLoopBackOff`, `Liveness probe failed` events | `kubectl describe pod POD` | [Learn Kubernetes](31-learn-kubernetes.md) |
| Probe blocked by firewall / NetworkPolicy | Backend "down" only from the LB's point of view | capture on the backend for the LB's source IP | section 7 |

**Why it matters for troubleshooting:** When a site is "down" but the app
answers when you curl it directly, suspect the health check before the app.
The proxy is doing exactly what it was told.

**Next step:** traffic between sites and between nodes often runs through
tunnels. Tunnels change the MTU, and that breaks things in unusual ways.

---

## 12. VPNs, overlays and MTU

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm → *Docker Overlay Network* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking → CNI and Pod Networking ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Note: the MTU steps of the [network speed playbook](24-playbook-network-speed.md) and Docker's networking overview ([docs](https://docs.docker.com/engine/network/)). No KodeKloud lesson on WireGuard or MTU was found, so the labs below are the course · 4) Practice: the MTU black-hole, WireGuard and VXLAN labs below, then the iximiuz Labs tutorial [Container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch).

### MTU, fragmentation and path MTU discovery

**Level:** [L3 · Senior] · a Mid-level engineer should at least recognise "small works, big hangs".

**Concept.** Every link has an **MTU**, the biggest IP packet it carries
(1500 on Ethernet). Tunnels (WireGuard, VXLAN, IPsec, GRE) wrap each packet
in extra headers, so the packets *inside* must be smaller. A sender learns
the smallest MTU on the path through **Path MTU Discovery (PMTUD)**: it sends
with the Don't-Fragment bit, and a router that can't forward a packet that
big returns ICMP "fragmentation needed" (IPv6: "Packet Too Big") with the
allowed size. If a firewall **blocks that ICMP**, you get a **PMTU black
hole**: small packets pass, big ones vanish. The symptoms look like magic:
SSH logs in but hangs on `ls` of a big directory, the TLS handshake hangs
after ClientHello (the certificate is big), `git clone` stalls, small API
calls work and big responses never finish.

```
 overhead per tunnel (outer IPv4)          inner MTU on a 1500 underlay
   WireGuard        60 bytes (80 w/ IPv6)     1420 (wg-quick default)
   VXLAN            50 bytes                  1450 (Docker overlay, Flannel)
   IPIP (Calico)    20 bytes                  1480
   IPsec ESP        ~50-73 bytes              ~1400-1440

 MSS = MTU - 40 (IPv4 + TCP headers):  1500 -> 1460,  1420 -> 1380,  1450 -> 1410
 ping payload for a full-size test = MTU - 28 (IPv4 + ICMP headers): 1500 -> 1472
```

**Key terms**

| Term | Meaning |
|---|---|
| DF bit | "Don't fragment". Set by TCP on Linux, so PMTUD can work |
| ICMP frag-needed / Packet Too Big | Router's message "too big, max is N". **Must not be blocked** |
| PMTU black hole | ICMP blocked: big packets silently dropped |
| MSS clamping | Router rewrites the MSS in SYNs so TCP never sends packets too big for the tunnel |
| Jumbo frames | MTU 9000 inside data centres. All devices on the segment must agree |

**See it on a real system**

```bash
ip link | grep -o 'mtu [0-9]*' | sort | uniq -c              # MTUs on this host
ping -c 3 -M do -s 1472 HOST                                 # full 1500-byte packet, DF set
ping -c 3 -M do -s 1392 HOST                                 # 1420 (fits a WireGuard path)
tracepath -n HOST                                            # discovers the path MTU hop by hop
ip route get HOST                                            # shows "mtu N" once a PMTU was learned
ss -ti dst HOST | grep -o 'pmtu:[0-9]*\|mss:[0-9]*'          # what live connections use
```

```
$ ping -c 2 -M do -s 1472 10.20.0.5
PING 10.20.0.5 (10.20.0.5) 1472(1500) bytes of data.
ping: local error: message too long, mtu=1420
ping: local error: message too long, mtu=1420

$ ping -c 2 -M do -s 1472 203.0.113.50
PING 203.0.113.50 (203.0.113.50) 1472(1500) bytes of data.
From 192.0.2.1 icmp_seq=1 Frag needed and DF set (mtu = 1400)
```

- `local error: message too long, mtu=1420` means your own outgoing interface
  (here a WireGuard tunnel) is smaller. That's expected.
- `Frag needed and DF set (mtu = 1400)` means a router on the path told you.
  PMTUD works.
- **No reply at all** for big sizes while small sizes work means a black
  hole. Find the size that just works (bisect `-s`) and you know the real
  path MTU.

**Hands-on lab (test VM only)**: build a black hole and fix it two ways.

```bash
# 1. Build: a big file on the server, and a 1400-byte bottleneck on the router's client-side link
sudo ~/netlab.sh up
sudo ip netns exec server sh -c 'mkdir -p /tmp/www && head -c 2000000 /dev/urandom > /tmp/www/big.bin'
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20 --directory /tmp/www   # terminal 2
sudo ip -n router link set r-eth0 mtu 1400
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://10.10.2.20/big.bin   # works: PMTUD
sudo ip -n server route get 10.10.1.10            # "... mtu 1400": the server learned it from ICMP

# 2. Break: drop the router's ICMP "fragmentation needed" messages, forget the learned PMTU
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab out { type filter hook output priority 0; }'
sudo ip netns exec router nft add rule inet lab out icmp type destination-unreachable icmp code frag-needed drop
sudo ip -n server route flush cache
sudo ip netns exec client curl -s -m 10 -o /dev/null -w '%{http_code} %{size_download}\n' http://10.10.2.20/big.bin   # hangs, times out

# 3. Diagnose: small works, big vanishes
sudo ip netns exec server ping -c2 -W1 -M do -s 1372 10.10.1.10   # ok (1400 bytes)
sudo ip netns exec server ping -c2 -W1 -M do -s 1472 10.10.1.10   # silence: black hole
sudo ip netns exec router tcpdump -ni r-eth1 -c 6 'tcp port 80'    # full-size segments from the server retransmitted

# 4. Fix A (right fix): stop dropping the ICMP
sudo ip netns exec router nft delete table inet lab

# 5. Fix B (workaround when you don't own the firewall): clamp the MSS on the router
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab out { type filter hook output priority 0; }'
sudo ip netns exec router nft add rule inet lab out icmp type destination-unreachable icmp code frag-needed drop
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd tcp flags syn tcp option maxseg size set 1360
sudo ip -n server route flush cache
sudo ip netns exec client curl -s -m 10 -o /dev/null -w '%{http_code} %{size_download}\n' http://10.10.2.20/big.bin   # works again
sudo ip netns exec router nft delete table inet lab
```

- On real VPN gateways the clamp is usually written
  `tcp flags syn tcp option maxseg size set rt mtu`
  (nftables) or `-j TCPMSS --clamp-mss-to-pmtu` (iptables), applied to
  traffic entering and leaving the tunnel.

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| PMTU black hole over VPN | Small requests OK, big responses hang; TLS hangs after ClientHello | `ping -M do -s SIZE HOST` (bisect) | [Network speed playbook](24-playbook-network-speed.md) |
| Container overlay MTU larger than the underlay allows | Pod-to-pod/service-to-service big transfers hang; DNS fine | `ip link` in the container vs the host | [Containers playbook](26-playbook-containers-k8s.md) |
| Docker inside a VM or VPN with MTU < 1500 | `docker pull`/`apt` inside containers hang mid-download | set `"mtu"` in daemon.json or on the network | [Learn Docker](30-learn-docker.md) |
| Jumbo frame mismatch | Works for small traffic, storage/replication stalls | `ping -M do -s 8972 HOST` | [02-network.md](02-network.md) |

**Why it matters for troubleshooting:** MTU problems produce the most
confusing symptoms in networking, because connectivity tests (ping, `nc -z`,
small curls) all pass. Whenever "small works, big hangs", test the MTU first.

**Next step:** WireGuard, the VPN you're most likely to run between sites,
the homelab and the cloud.

### WireGuard

**Level:** [L3 · Senior].

**Concept.** WireGuard is a small, fast VPN built into the Linux kernel. Each
peer has a key pair. You configure the other side's **public key**, its
**endpoint** (IP:UDP port) and **AllowedIPs**. AllowedIPs does two jobs at
once (**cryptokey routing**). Outbound, it's the routing table ("send
10.20.0.0/24 through this peer"). Inbound, it's an ACL ("accept from this
peer only packets with these source IPs"). It runs over **UDP** (51820 by
convention; WireGuard has no built-in default, you set `ListenPort`), is silent to unauthenticated packets (no reply at all), and only
handshakes when there's traffic. Behind NAT, a `PersistentKeepalive` keeps
the NAT mapping alive.

```
 site A: wg0 10.8.0.1                                         site B: wg0 10.8.0.2
 [Peer] PublicKey = B_pub                                     [Peer] PublicKey = A_pub
        Endpoint = 198.51.100.7:51820   ── UDP 51820 ──►            AllowedIPs = 10.8.0.1/32, 10.10.0.0/24
        AllowedIPs = 10.8.0.2/32, 10.20.0.0/24
 + route 10.20.0.0/24 dev wg0 (wg-quick adds it from AllowedIPs)
 + on B: ip_forward=1 and firewall/NAT allowing wg0 <-> LAN if B is a gateway for 10.20.0.0/24
```

**Key terms**

| Term | Meaning |
|---|---|
| AllowedIPs | Routes out + source filter in. Overlapping AllowedIPs between peers = traffic goes to the wrong peer |
| Endpoint | Where to send UDP. Learned/updated from the last valid packet received |
| Handshake | Every 2 minutes while traffic flows. `latest handshake` in `wg show` |
| `wg-quick` | Helper that reads `/etc/wireguard/wg0.conf`, sets addresses, routes, DNS (systemd unit `wg-quick@wg0`) |
| PersistentKeepalive | Send a keepalive every N seconds (25 is typical) to hold NAT open |

**See it on a real system**

```bash
sudo wg show                            # peers, endpoints, latest handshake, transfer counters
ip -br addr show wg0; ip route | grep wg0
systemctl status wg-quick@wg0 --no-pager
sudo ss -ulpn 'sport = :51820'          # listed, but with no process: the kernel owns the socket
```

```
$ sudo wg show
interface: wg0
  public key: kX3cVq0D2c8Zr1sHq5oT1o0eXamPLEkeYk3yAAAAAAA=
  private key: (hidden)
  listening port: 51820

peer: Hn2b7sXamPLEpUbl1cKeYm9wQ5vL0tq8RcBBBBBBBBB=
  endpoint: 198.51.100.7:51820
  allowed ips: 10.8.0.2/32, 10.20.0.0/24
  latest handshake: 42 seconds ago
  transfer: 18.42 MiB received, 3.10 MiB sent
  persistent keepalive: every 25 seconds
```

- `latest handshake: 42 seconds ago` means the tunnel is alive. **No
  `latest handshake` line** means it never connected: UDP blocked, wrong
  endpoint or wrong key.
- Handshake OK but traffic to 10.20.0.x fails: AllowedIPs, routes,
  forwarding or the far side's firewall/NAT (the far LAN needs a route back
  to 10.8.0.0/24, or B must masquerade).

**Hands-on lab (test VM only)**: a tunnel between the client and server namespaces.

```bash
# 1. Build
sudo ~/netlab.sh up
mkdir -p ~/wglab && cd ~/wglab && umask 077
wg genkey | tee c.key | wg pubkey > c.pub
wg genkey | tee s.key | wg pubkey > s.pub
sudo ip -n client link add wg0 type wireguard
sudo ip -n server link add wg0 type wireguard
sudo ip netns exec client wg set wg0 private-key ./c.key listen-port 51820 \
  peer "$(cat s.pub)" allowed-ips 10.99.0.2/32 endpoint 10.10.2.20:51820
sudo ip netns exec server wg set wg0 private-key ./s.key listen-port 51820 \
  peer "$(cat c.pub)" allowed-ips 10.99.0.1/32 endpoint 10.10.1.10:51820
sudo ip -n client addr add 10.99.0.1/24 dev wg0 && sudo ip -n client link set wg0 up
sudo ip -n server addr add 10.99.0.2/24 dev wg0 && sudo ip -n server link set wg0 up
sudo ip netns exec client ping -c2 10.99.0.2
sudo ip netns exec client wg show                           # latest handshake: a few seconds ago
sudo ip -n client link show wg0 | grep -o 'mtu [0-9]*'      # mtu 1420

# 2. Watch it on the wire: only encrypted UDP 51820 crosses the router
sudo ip netns exec router tcpdump -ni r-eth0 -c 4 udp port 51820

# 3. Break A: the router blocks UDP 51820 (like an on-prem firewall)
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd udp dport 51820 drop
sudo ip -n client link set wg0 down && sudo ip -n client link set wg0 up   # force a fresh handshake attempt
sudo ip netns exec client ping -c3 -W1 10.99.0.2          # fails; wg show: handshake getting older / never
sudo ip netns exec router nft delete table inet lab       # fix

# 4. Break B: wrong AllowedIPs on the server (it now drops the client's source IP)
sudo ip netns exec server wg set wg0 peer "$(cat c.pub)" allowed-ips 10.99.0.50/32
sudo ip netns exec client ping -c3 -W1 10.99.0.2          # fails although handshakes succeed
sudo ip netns exec server wg show                          # allowed ips: 10.99.0.50/32 - mismatch
sudo ip netns exec server wg set wg0 peer "$(cat c.pub)" allowed-ips 10.99.0.1/32   # fix
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| UDP port blocked / wrong endpoint | No `latest handshake` | `sudo wg show`, `sudo tcpdump -ni any udp port 51820` on both sides | [Site down playbook](25-playbook-site-down.md) |
| Wrong public key | Handshake never completes. WireGuard logs nothing by default | compare keys on both sides | this topic |
| AllowedIPs wrong/overlapping | Handshake OK, traffic for some subnets fails or goes to the wrong peer | `sudo wg show` (allowed ips), `ip route get IP` | section 4 |
| Remote LAN can't answer | Tunnel IPs ping; LAN hosts behind B don't | forwarding/NAT on B, return route on the LAN | section 5 |
| MTU | Small traffic OK, big stalls | `ping -M do -s 1392 IP` through the tunnel | previous topic |
| DNS over VPN | Internal names fail | `resolvectl status wg0` | section 8 split DNS |

**Why it matters for troubleshooting:** WireGuard's silence (no error
messages, no reply to bad packets) means you troubleshoot from evidence:
`wg show` for handshakes, tcpdump for UDP, `ip route get` for AllowedIPs.

**Next step:** overlays. VXLAN is how Docker Swarm (dokploy-network) and
several Kubernetes CNIs stretch one L2 network across hosts.

### VXLAN and container overlays

**Level:** [L3 · Senior] · needed before you add a second Dokploy (Swarm) node or a Kubernetes worker.

**Concept.** **VXLAN** carries Ethernet frames inside UDP packets (port
**4789**; Linux and Flannel default to 8472). Each overlay network has a
24-bit **VNI**. The endpoints that wrap and unwrap traffic are **VTEPs**. The
underlay (your normal network) only sees UDP between host IPs. The
containers believe they share one L2 segment across hosts. **Docker Swarm
overlay networks**, such as the `dokploy-network` Dokploy creates when it
initialises Swarm, use VXLAN between nodes. Flannel (vxlan backend) and
Calico (VXLAN mode) do the same for Kubernetes pods. Overlays fail in two
typical ways: the underlay blocks the UDP port, or the MTU is too big.

```
 node-1 192.0.2.11                                          node-2 192.0.2.12
 container 10.0.1.5 ─► vxlan VTEP ══ UDP 4789, VNI 4097 ══► VTEP ─► container 10.0.1.9
                      outer: 192.0.2.11 -> 192.0.2.12  |  inner: Ethernet + IP 10.0.1.5 -> 10.0.1.9

 Docker Swarm ports between nodes:   2377/tcp (managers), 7946/tcp+udp (gossip), 4789/udp (VXLAN data)
 (encrypted overlays also need IP protocol 50, ESP)
```

**Key terms**

| Term | Meaning |
|---|---|
| VNI | VXLAN network identifier, one per overlay network |
| VTEP | Tunnel endpoint on each host |
| Underlay / overlay | Physical host network / virtual network carried inside it |
| FDB for VXLAN | Which remote VTEP has which MAC (`bridge fdb show dev vxlan0`) |
| Ingress routing mesh | Swarm's L4 load balancer: a published port works on every node |

**See it on a real system**

```bash
ip -d link show type vxlan                               # VXLAN devices: id (VNI), dstport, local/remote
docker network ls --filter driver=overlay                # Swarm overlays (dokploy-network, ingress)
docker network inspect dokploy-network --format '{{json .Options}} {{json .IPAM.Config}}'
docker node ls                                           # Swarm node status (managers)
sudo tcpdump -ni ens18 -c 10 udp port 4789               # overlay traffic between nodes
```

**Hands-on lab (test VM only)**: a VXLAN overlay over the lab's routed network.

```bash
# 1. Build: VTEPs in client and server namespaces, underlay = the routed lab
sudo ~/netlab.sh up
sudo ip -n client link add vx42 type vxlan id 42 local 10.10.1.10 remote 10.10.2.20 dstport 4789 dev c-eth0
sudo ip -n server link add vx42 type vxlan id 42 local 10.10.2.20 remote 10.10.1.10 dstport 4789 dev s-eth0
sudo ip -n client addr add 192.168.42.1/24 dev vx42 && sudo ip -n client link set vx42 up
sudo ip -n server addr add 192.168.42.2/24 dev vx42 && sudo ip -n server link set vx42 up
sudo ip netns exec client ping -c2 192.168.42.2           # overlay works across a ROUTED underlay
sudo ip -n client link show vx42 | grep -o 'mtu [0-9]*'   # mtu 1450

# 2. See the encapsulation on the router
sudo ip netns exec router tcpdump -ni r-eth0 -c 2 udp port 4789
#   IP 10.10.1.10.xxxxx > 10.10.2.20.4789: VXLAN, flags [I] (0x08), vni 42
#   IP 192.168.42.1 > 192.168.42.2: ICMP echo request ...

# 3. Break: the "network team" blocks UDP 4789
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd udp dport 4789 drop
sudo ip netns exec client ping -c2 -W1 192.168.42.2       # overlay dead...
sudo ip netns exec client ping -c2 10.10.2.20             # ...while the underlay is fine
sudo ip netns exec router nft delete table inet lab       # fix

# 4. MTU edge: 1450 is the limit inside the overlay
sudo ip netns exec client ping -c1 -M do -s 1422 192.168.42.2   # ok (1450)
sudo ip netns exec client ping -c1 -M do -s 1423 192.168.42.2   # local error: message too long, mtu=1450
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| UDP 4789 / 7946 blocked between nodes | Containers on different nodes can't reach each other; same node fine | `sudo tcpdump -ni IFACE udp port 4789` on both nodes | [Containers playbook](26-playbook-containers-k8s.md) |
| Swarm manager port 2377 blocked | Node can't join: `connection error ... 2377` | `nc -zv MANAGER 2377` | [Containers playbook](26-playbook-containers-k8s.md) |
| Overlay MTU vs underlay | Small requests OK, large hang between nodes | `ping -M do -s SIZE` container-to-container | previous topics |
| Overlay subnet overlaps LAN | Some LAN hosts unreachable from containers | `docker network inspect NET` (Subnet) vs LAN ranges | section 3 |

**Why it matters for troubleshooting:** If you add a second Dokploy server
(Swarm worker) or a Kubernetes node, the overlay is what joins them. "Works
on one node, fails across nodes" means overlay ports or MTU, almost always.

**Next step:** all of this has an IPv6 twin. The essentials are next.

---

## 13. IPv6 essentials

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → Configure IPv4/IPv6 Networking and Hostname Resolution ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: this section, then the IPv4 equivalents in [Network reference](02-network.md) · 3) Practice: the IPv6 lab and the Happy Eyeballs lab below, then run `curl -4` and `curl -6` against your own sites.

### IPv6 addressing and neighbour discovery

**Level:** [L2 · Mid].

**Concept.** IPv6 addresses are 128 bits, written as eight groups of hex
with two compression rules: drop leading zeros in a group, and replace one
run of zero groups with `::`. Subnets are almost always **/64**. Every
interface has several addresses at once: a **link-local** `fe80::/64`
(always there, only valid on that link) plus global ones. There's no ARP and
no broadcast. **Neighbour Discovery (NDP)**, made of ICMPv6 messages, finds
MACs and routers, and routers announce prefixes with **Router
Advertisements** so hosts can configure themselves (**SLAAC**). Because NDP,
RA and Path MTU (Packet Too Big) all ride on ICMPv6, **blocking ICMPv6 breaks
IPv6 completely**.

```
 2001:0db8:0010:0001:0000:0000:0000:0020  ->  2001:db8:10:1::20
 └──── routing prefix /48 ───┘└ subnet ┘└──── interface ID (64 bits) ────┘
                              /64 network
```

| Range | Meaning | IPv4 analogue |
|---|---|---|
| `::1/128` | Loopback | 127.0.0.1 |
| `fe80::/10` | Link-local. Needs the interface: `fe80::1%ens18` | 169.254/16 |
| `2000::/3` | Global unicast (internet) | public IPs |
| `fd00::/8` (in `fc00::/7`) | Unique local addresses (private) | RFC 1918 |
| `ff00::/8` | Multicast (replaces broadcast) | 224/4 |
| `2001:db8::/32` | Documentation | 192.0.2.0/24 etc. |
| `::ffff:192.0.2.10` | IPv4-mapped (an IPv4 client on a dual-stack socket) | - |

**Key terms**

| Term | Meaning |
|---|---|
| NDP | Neighbour Solicitation/Advertisement (≈ ARP), Router Solicitation/Advertisement |
| SLAAC | Host builds its own address from the RA prefix + an interface ID |
| DHCPv6 | Stateful alternative/complement to SLAAC |
| DAD | Duplicate Address Detection. A new address is `tentative` for a moment |
| Privacy addresses | Temporary random addresses for outgoing connections (desktops) |

**See it on a real system**

```bash
ip -6 -br addr
ip -6 route
ip -6 neigh
ping -6 -c 2 2001:db8:10:1::1
ping -c 2 fe80::1%ens18                      # link-local always needs %interface
```

```
$ ip -6 addr show ens18
2: ens18: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 2001:db8:10:1::20/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::be24:11ff:fe4a:2b1c/64 scope link
       valid_lft forever preferred_lft forever

$ ip -6 route
2001:db8:10:1::/64 dev ens18 proto kernel metric 256 pref medium
fe80::/64 dev ens18 proto kernel metric 256 pref medium
default via fe80::1 dev ens18 proto ra metric 1024 expires 1786sec pref medium
```

- The default route points to the router's **link-local** address, learned
  from a Router Advertisement (`proto ra`). That's normal in IPv6.

**Hands-on lab (test VM only)**: IPv6 through the lab router, then break NDP.

```bash
# 1. Build (nodad skips the short duplicate-address wait)
sudo ~/netlab.sh up
sudo ip -n client -6 addr add 2001:db8:1::10/64 dev c-eth0 nodad
sudo ip -n router -6 addr add 2001:db8:1::1/64 dev r-eth0 nodad
sudo ip -n router -6 addr add 2001:db8:2::1/64 dev r-eth1 nodad
sudo ip -n server -6 addr add 2001:db8:2::20/64 dev s-eth0 nodad
sudo ip -n client -6 route add default via 2001:db8:1::1
sudo ip -n server -6 route add default via 2001:db8:2::1
sudo ip netns exec router sysctl -qw net.ipv6.conf.all.forwarding=1
sudo ip netns exec client ping -6 -c2 2001:db8:2::20
sudo ip -n router -6 neigh                       # NDP entries, like ip neigh for IPv4

# 2. Break: a "hardening" rule that drops ICMPv6 neighbour solicitations on the server
sudo ip netns exec server nft add table inet lab
sudo ip netns exec server nft 'add chain inet lab in { type filter hook input priority 0; }'
sudo ip netns exec server nft add rule inet lab in icmpv6 type nd-neighbor-solicit drop
sudo ip -n router -6 neigh flush dev r-eth1
sudo ip netns exec client ping -6 -c2 -W1 2001:db8:2::20     # fails

# 3. Diagnose
sudo ip -n router -6 neigh show dev r-eth1       # 2001:db8:2::20 FAILED
sudo ip netns exec router tcpdump -ni r-eth1 -c 4 icmp6      # neighbor solicitation, no advertisement

# 4. Fix: never block NDP (types 133-137) or Packet Too Big
sudo ip netns exec server nft delete table inet lab
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| ICMPv6 blocked | IPv6 neighbours `FAILED`, PMTU black holes | `ip -6 neigh`, firewall rules for icmpv6 | section 7 |
| No RA / wrong RA | No global address or no default route | `ip -6 route show default`, `rdisc6 IFACE` (ndisc6 package) | [02-network.md](02-network.md) |
| Link-local without `%iface` | `connect: Invalid argument` | add `%ens18` | this topic |

**Why it matters for troubleshooting:** Even networks that "don't use IPv6"
have it on every host (link-local, `[::]` listeners, AAAA records). You need
to recognise it to rule it out.

**Next step:** dual stack. When a host has both, which one gets used, and
what happens when one is broken?

### Dual stack in practice

**Level:** [L2 · Mid].

**Concept.** With both IPv4 and IPv6, a client gets A *and* AAAA records and
by default **prefers IPv6** (RFC 6724 ordering via `getaddrinfo`, tunable in
`/etc/gai.conf`). Modern clients use **Happy Eyeballs**: start IPv6, and if
it doesn't connect within roughly 200–300 ms, race IPv4 in parallel. Broken
IPv6 then costs a small delay, not an outage. But older or simpler clients
(scripts, some libraries) try addresses one after another and wait a full
timeout. On the server side, a socket bound to `[::]` with `IPV6_V6ONLY=0`
accepts IPv4 as well (IPv4 clients appear as `::ffff:198.51.100.23`). That's
why Apache shows `*:443`. Firewalls need **parity**: a rule for IPv4 doesn't
cover IPv6.

**Key terms**

| Term | Meaning |
|---|---|
| Happy Eyeballs | Race IPv6 and IPv4 connection attempts, use the first that connects |
| `IPV6_V6ONLY` | Socket option: 0 = `[::]` also takes IPv4 (Linux default via `net.ipv6.bindv6only=0`) |
| `/etc/gai.conf` | `precedence ::ffff:0:0/96 100` makes getaddrinfo prefer IPv4 |
| Docker and IPv6 | IPv6 for containers is off by default, but `docker-proxy` still listens on `[::]` for published ports |

**See it on a real system**

```bash
getent ahosts app.example.com | head -4            # order apps will try (IPv6 first if AAAA exists)
curl -sv -o /dev/null https://app.example.com 2>&1 | grep -E 'Trying|Connected'
curl -4 -sI https://app.example.com | head -1; curl -6 -sI https://app.example.com | head -1
sudo ss -ltn '( sport = :443 )'                     # *:443, [::]:443, 0.0.0.0:443 ?
grep -E '^IPV6' /etc/default/ufw                    # UFW manages IPv6 rules too? (IPV6=yes)
```

```
$ curl -sv -o /dev/null https://app.example.com 2>&1 | grep -E 'Trying|Connected'
*   Trying [2001:db8:10:1::20]:443...
*   Trying 203.0.113.10:443...
* Connected to app.example.com (203.0.113.10) port 443
```

- curl tried IPv6 first and IPv4 shortly after, and IPv4 won. The IPv6 path
  is broken (AAAA points somewhere that doesn't answer on 443), and every
  client pays a small delay. Older clients pay a full timeout. Fix the AAAA
  or the IPv6 path. Don't hide it.

**Hands-on lab (test VM only)**: watch Happy Eyeballs rescue a broken IPv6 path.

```bash
# 1. Build: keep the IPv6 addresses from the previous lab, start a dual-stack server (terminal 2)
sudo ip netns exec server python3 -m http.server 80 --bind ::        # "Serving HTTP on :: port 80"
sudo ip netns exec server ss -ltn 'sport = :80'                       # *:80 (both families)

# 2. Both work
sudo ip netns exec client curl -s -o /dev/null -w '%{http_code} via %{remote_ip}\n' --resolve app.example.com:80:[2001:db8:2::20],10.10.2.20 http://app.example.com/

# 3. Break IPv6 only (drop on the router)
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd ip6 daddr 2001:db8:2::20 tcp dport 80 drop
sudo ip netns exec client curl -sv -o /dev/null -w '%{http_code} via %{remote_ip} in %{time_connect}s\n' \
  --resolve app.example.com:80:[2001:db8:2::20],10.10.2.20 http://app.example.com/ 2>&1 | grep -E 'Trying|via'
#   Trying [2001:db8:2::20]:80... then Trying 10.10.2.20:80... -> 200 via 10.10.2.20 after ~0.2 s
sudo ip netns exec client curl -6 -s -m 3 -o /dev/null http://[2001:db8:2::20]/ || echo "IPv6 path broken"

# 4. Fix / clean up
sudo ip netns exec router nft delete table inet lab
```

**How it breaks**

| Failure | What you see | First command | Go to |
|---|---|---|---|
| Broken AAAA / IPv6 path | Slow first connection, some clients fail | `curl -6 -v URL`, `curl -4 -v URL` | [Site down playbook](25-playbook-site-down.md) |
| Service only on `0.0.0.0`, AAAA published | IPv6 clients refused | `sudo ss -ltn 'sport = :PORT'` | section 6 |
| Firewall only for IPv4 | Port open (or blocked) only over IPv6 | `sudo ufw status` v6 lines, `nft list ruleset` | section 7 |
| IPv4 client logged as `::ffff:a.b.c.d` | Allow-lists/regexes don't match | app log format | [Learn web servers](29-learn-webservers-proxies.md) |

**Why it matters for troubleshooting:** "Slow for some users, fine for me" is
often IPv6: their network has it, yours doesn't, and the AAAA record points
at something broken. `curl -4` versus `curl -6` settles it in seconds.

**Next step:** the tools that show you all of this directly, packet capture
and syscall tracing, which you've been using in every lab so far.

---

## 14. Packet capture and syscall tracing

> 📚 **Study path:** 1) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/). KodeKloud has no tcpdump or strace lesson, so start with the zine · 2) Note: this section, then [Network reference](02-network.md) · 3) Read: [Spying on your programs with strace](https://wizardzines.com/zines/strace/) · 4) KodeKloud: *Docker Certified Associate* — Docker Engine – Networking → *Networking Deep Dive – Namespaces*, which you need to capture inside a container ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Namespaces/page)) · 5) Practice: the three-point capture and strace labs below, then [SadServers](https://sadservers.com/scenarios).

### tcpdump fundamentals and filters

**Level:** [L2 · Mid] · the Ops Ladder's first blind spot. A Junior should already run the basic filters.

**Concept.** `tcpdump` copies packets as the kernel sees them on an
interface and prints or saves them. It's the ground truth: a capture shows
whether a packet *left*, *arrived* and *got an answer*. The only reasoning
left is about where you captured. Filters use **BPF syntax** and run in the
kernel, so only matching packets are copied. Capture on the right interface
(`-i any` when unsure; a specific NIC, bridge or veth when you know) and
always use `-n`, so tcpdump doesn't do DNS lookups that pollute your own
capture.

**Key terms**

| Flag / filter | Meaning |
|---|---|
| `-i any` / `-i ens18` | All interfaces (shows interface and direction `In`/`Out`) / one interface |
| `-n` / `-nn` | Don't resolve addresses / addresses and ports |
| `-c N` | Stop after N packets. Always use it on busy production hosts |
| `-w FILE` / `-r FILE` | Write raw packets for Wireshark / read a saved capture |
| `-s 128` | Capture only the first 128 bytes of each packet (headers, no payload, smaller files) |
| `-A` / `-X` | Print payload as ASCII / hex+ASCII |
| `-e` | Show MAC addresses (L2) |
| `-v` / `-vv` | More header detail: TTL, IP ID, TCP options, DNS details |
| `-C 100 -W 5` | Rotate files: 100 MB each, keep 5 (ring buffer for long captures) |
| `host H`, `net 10.0.0.0/8`, `port 443`, `src`/`dst` | Basic BPF filters |
| `and` / `or` / `not`, parentheses in quotes | Combine: `'host 192.0.2.10 and (port 80 or port 443)'` |
| `'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'` | Only SYNs and RSTs: connection attempts and refusals |
| `icmp`, `icmp6`, `arp`, `udp port 53` | Protocol filters |

**See it on a real system** (read-only, but it needs sudo. Captures can contain passwords, cookies and personal data, so treat pcap files as secrets and delete them when done.)

```bash
sudo tcpdump -ni any -c 20 port 53                               # DNS
sudo tcpdump -ni ens18 -c 20 'tcp port 443 and host 198.51.100.23' # one client's HTTPS
sudo tcpdump -ni any -c 50 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0' # connection attempts / resets
sudo tcpdump -ni br-6c1e2f0a9b3d -c 20 port 8000                 # traffic on one Docker network
sudo tcpdump -ni any -s 128 -C 100 -W 5 -w /tmp/web.pcap port 443 # rotating capture, headers only
sudo tcpdump -nr /tmp/web.pcap | head                             # read it back
```

Inside a container that has no tools, capture from the host in its namespace,
or with netshoot:

```bash
PID=$(docker inspect -f '{{.State.Pid}}' CONTAINER)
sudo nsenter -t "$PID" -n tcpdump -ni any -c 20 port 53            # host's tcpdump, container's network
docker run --rm -it --net container:CONTAINER nicolaka/netshoot tcpdump -ni any -c 20 port 53
```

**Hands-on lab (test VM only)**: capture at three points to locate a drop.

```bash
# 1. Build: lab + web server (terminal 2), firewall drop on the router's FORWARD for port 80
sudo ~/netlab.sh up
sudo ip netns exec server python3 -m http.server 80 --bind 10.10.2.20
sudo ip netns exec router nft add table inet lab
sudo ip netns exec router nft 'add chain inet lab fwd { type filter hook forward priority 0; }'
sudo ip netns exec router nft add rule inet lab fwd tcp dport 80 drop

# 2. Capture at three points (three terminals), then run the curl
sudo ip netns exec client tcpdump -ni c-eth0 -c 3 tcp port 80     # A: client side
sudo ip netns exec router tcpdump -ni r-eth0 -c 3 tcp port 80     # B: router ingress
sudo ip netns exec router tcpdump -ni r-eth1 -c 3 tcp port 80     # C: router egress
sudo ip netns exec client curl -s -m 5 http://10.10.2.20/ || echo "timed out"

# 3. Read the evidence: SYNs at A and B, nothing at C -> dropped INSIDE the router
# 4. Fix
sudo ip netns exec router nft delete table inet lab
```

**How it breaks**

| Pattern in the capture | Meaning | Next step |
|---|---|---|
| SYN out, nothing back | Dropped on the way or reply path broken | Capture on the server: arrives? |
| SYN arrives at the server, SYN-ACK leaves, client never sees it | Return path or a firewall between them | `ip route get CLIENT` on the server, stateful firewall |
| SYN → RST | Nothing listening (or a firewall reset). Path fine | `ss -ltnp` on the server |
| Same segment repeated (`seq` unchanged) | Retransmissions: loss | `mtr`, [network speed playbook](24-playbook-network-speed.md) |
| Big segments repeated, small ones fine | MTU black hole | section 12 |
| DNS query out, no answer | Resolver unreachable / firewall on 53 | section 8 |
| No packets at all on the interface | Wrong interface, or the app never sent (DNS failed, wrong IP) | `-i any`, then `strace` |

**Why it matters for troubleshooting:** Your Ops Ladder's first blind spot was
"no view of the packets". A capture at both ends turns "the network is
broken" into "packets reach the server's NIC and the server never answers".
Nobody can argue with that, and it tells you exactly which team owns the
fix.

**Next step:** learn to read what tcpdump prints: a TCP handshake and a DNS
exchange, line by line.

### Reading a TCP handshake and a DNS exchange

**Level:** [L2 · Mid].

**Concept.** tcpdump prints one line per packet: time, interface/direction
(with `-i any`), protocol, source > destination, then protocol details. For
TCP, the **flags** are the story. For DNS, the **query ID, type and answer
counts** are.

**Key terms**: TCP flags as tcpdump prints them.

| TCP flag in tcpdump | Meaning |
|---|---|
| `[S]` | SYN: connection request |
| `[S.]` | SYN-ACK: server accepts |
| `[.]` | ACK only |
| `[P.]` | PSH+ACK: data |
| `[F.]` | FIN: graceful close |
| `[R]` / `[R.]` | RST: refused or aborted |
| `seq 1:79` | Relative byte range of this segment (tcpdump shows relative numbers after the handshake; `-S` shows absolute ones) |

DNS fields as tcpdump prints them:

| DNS field in tcpdump | Meaning |
|---|---|
| `51432+` | Query ID; `+` means recursion desired |
| `A?` / `AAAA?` | The question and its record type |
| `[1au]` | One additional record in the query (the EDNS OPT record) |
| `1/0/1` | Answer / authority / additional record counts in the response |
| `NXDomain` / `ServFail` | Error response codes, printed where the answers would be |

**See it on a real system**: a full HTTP connection to a local service.

```bash
sudo tcpdump -ni lo -c 12 'tcp port 8000'      # terminal 1
curl -s -o /dev/null http://127.0.0.1:8000/     # terminal 2 (any local service on 8000)
```

```
10:14:02.112233 IP 127.0.0.1.51234 > 127.0.0.1.8000: Flags [S], seq 1849021001, win 65495, options [mss 65495,sackOK,TS val 123 ecr 0,nop,wscale 7], length 0
10:14:02.112250 IP 127.0.0.1.8000 > 127.0.0.1.51234: Flags [S.], seq 302190044, ack 1849021002, win 65483, options [mss 65495,sackOK,TS val 123 ecr 123,nop,wscale 7], length 0
10:14:02.112262 IP 127.0.0.1.51234 > 127.0.0.1.8000: Flags [.], ack 1, win 512, options [nop,nop,TS val 123 ecr 123], length 0
10:14:02.112301 IP 127.0.0.1.51234 > 127.0.0.1.8000: Flags [P.], seq 1:79, ack 1, win 512, length 78: HTTP: GET / HTTP/1.1
10:14:02.112310 IP 127.0.0.1.8000 > 127.0.0.1.51234: Flags [.], ack 79, win 512, length 0
10:14:02.113920 IP 127.0.0.1.8000 > 127.0.0.1.51234: Flags [P.], seq 1:157, ack 79, win 512, length 156: HTTP: HTTP/1.0 200 OK
10:14:02.114002 IP 127.0.0.1.8000 > 127.0.0.1.51234: Flags [FP.], seq 157:1040, ack 79, win 512, length 883: HTTP
10:14:02.114050 IP 127.0.0.1.51234 > 127.0.0.1.8000: Flags [.], ack 1041, win 505, length 0
10:14:02.114120 IP 127.0.0.1.51234 > 127.0.0.1.8000: Flags [F.], seq 79, ack 1041, win 512, length 0
10:14:02.114131 IP 127.0.0.1.8000 > 127.0.0.1.51234: Flags [.], ack 80, win 512, length 0
```

- Lines 1–3: the three-way handshake. `mss`, `wscale` and `sackOK` are
  negotiated in the SYNs (section 6). On loopback the MSS is huge; on
  Ethernet you'd see `mss 1460`.
- After the handshake, tcpdump shows **relative** sequence numbers (`seq
  1:79` = bytes 1 to 78). `-S` shows absolute ones.
- `[P.] ... GET /` is the request, `[P.] ... 200 OK` the response.
- `[FP.]` is the server sending the last data and closing in one segment
  (HTTP/1.0 style). The client's `[F.]` closes its side. The client closed
  last, but the server closed *first*, so the server's socket enters
  TIME-WAIT.

A DNS lookup through systemd-resolved, captured with `-i any`:

```bash
sudo tcpdump -ni any -c 4 port 53     # then: getent ahosts app.example.com
```

```
10:20:11.402118 lo    In  IP 127.0.0.1.43122 > 127.0.0.53.53: 51432+ [1au] A? app.example.com. (44)
10:20:11.402871 ens18 Out IP 192.0.2.10.38211 > 192.0.2.53.53: 1201+ [1au] A? app.example.com. (44)
10:20:11.425540 ens18 In  IP 192.0.2.53.53 > 192.0.2.10.38211: 1201 1/0/1 A 203.0.113.10 (60)
10:20:11.425912 lo    In  IP 127.0.0.53.53 > 127.0.0.1.43122: 51432 1/0/1 A 203.0.113.10 (60)
```

- Line 1: the app asks the stub (127.0.0.53). `51432` is the query ID, `+`
  means recursion desired, `[1au]` is one additional record (the EDNS OPT),
  `A?` is the question.
- Line 2: resolved forwards to the real upstream 192.0.2.53 out of `ens18`
  with a *new* ID (1201).
- Line 3: the answer: `1/0/1` = 1 answer, 0 authority, 1 additional, and the
  A record itself. An error would show `NXDomain` or `ServFail` here.
- Line 4: resolved answers the app with the original ID.
- If line 2 appears and line 3 never does, the upstream (or a firewall in
  between) is the problem. If line 2 never appears, resolved answered from
  its cache or has no upstream configured.
- You'll usually also see a parallel `AAAA?` query for the same name.

**Hands-on lab (test VM only)**: record, then annotate.

```bash
# 1. Capture a handshake + request, a refused connection and a DNS lookup into one file
sudo tcpdump -ni any -w /tmp/lab.pcap 'port 53 or tcp port 8000 or tcp port 8001' &
python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &
sleep 1
curl -s -o /dev/null http://127.0.0.1:8000/        # handshake + request + close
curl -s -o /dev/null http://127.0.0.1:8001/        # refused: [S] then [R.]
getent ahosts example.com >/dev/null               # DNS
sudo resolvectl flush-caches; getent ahosts example.com >/dev/null   # DNS that must go upstream
sleep 1; sudo pkill -INT -x tcpdump; kill %2

# 2. Read it back and annotate every line on paper: who, what flag, why
sudo tcpdump -nr /tmp/lab.pcap
sudo tcpdump -nr /tmp/lab.pcap 'tcp[tcpflags] & tcp-rst != 0'     # just the refusal

# 3. Clean up (pcaps can hold secrets)
sudo rm /tmp/lab.pcap
```

**How it breaks**: see the pattern table in the previous topic. In DNS
captures, also watch for queries for `NAME.corp.example.com.corp.example.com`
(search-domain expansion), repeated identical queries without answers
(timeouts), and `TC` flag answers followed by TCP queries (big responses).

**Why it matters for troubleshooting:** Reading these lines fluently is what
lets you say, during an incident, "the SYN-ACK leaves the server and never
arrives" or "the resolver forwards to 192.0.2.53 and gets no answer". Those
sentences end arguments and start fixes.

**Next step:** for longer or messier captures, open the pcap in Wireshark.

### Wireshark and tshark on a pcap

**Level:** [L2 · Mid].

**Concept.** Wireshark is the GUI for packet analysis, and tshark is its
command-line twin. On servers, capture with `tcpdump -w` (small, safe,
available everywhere), copy the file to your workstation and analyse it
there. Wireshark decodes every protocol, reassembles streams, and marks TCP
problems for you (retransmissions, zero windows, resets). Its **display
filters** are a different language from tcpdump's capture filters.

| Task | Capture filter (tcpdump/BPF) | Display filter (Wireshark/tshark) |
|---|---|---|
| One host | `host 192.0.2.10` | `ip.addr == 192.0.2.10` |
| One port | `tcp port 443` | `tcp.port == 443` |
| SYNs without ACK | `'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0'` | `tcp.flags.syn == 1 && tcp.flags.ack == 0` |
| Resets | `'tcp[tcpflags] & tcp-rst != 0'` | `tcp.flags.reset == 1` |
| Retransmissions | (not possible) | `tcp.analysis.retransmission` |
| All TCP problems | (not possible) | `tcp.analysis.flags` |
| DNS errors | (not possible) | `dns.flags.rcode != 0` |
| TLS ClientHello for a name | (not possible) | `tls.handshake.extensions_server_name == "app.example.com"` |
| HTTP 5xx (cleartext) | (not possible) | `http.response.code >= 500` |

**Key terms**

| Term | Meaning |
|---|---|
| Follow TCP Stream | Right-click a packet → Follow → TCP Stream: the whole conversation as text |
| Statistics → Conversations | Who talked to whom, how much, how long |
| Expert Information | Wireshark's list of detected problems |
| `SSLKEYLOGFILE` | Environment variable that makes curl/browsers write TLS session keys, so Wireshark can decrypt *your own* test traffic |

**See it on a real system**

```bash
# On the server: capture headers only, rotate, limit time
sudo timeout 60 tcpdump -ni ens18 -s 256 -w /tmp/incident.pcap 'tcp port 443 and host 198.51.100.23'
# Copy to your workstation
scp HOST:/tmp/incident.pcap .
# Quick CLI analysis with tshark
tshark -r incident.pcap -q -z conv,tcp                           # conversations
tshark -r incident.pcap -Y 'tcp.analysis.retransmission' | wc -l # count retransmissions
tshark -r incident.pcap -Y 'tcp.flags.reset == 1' -T fields -e frame.time -e ip.src -e ip.dst
tshark -r incident.pcap -Y 'dns.flags.rcode != 0' -T fields -e dns.qry.name -e dns.flags.rcode
```

**Hands-on lab (test VM only)**: decrypt your own HTTPS in Wireshark.

```bash
# 1. Capture while curl logs its TLS keys
sudo tcpdump -ni any -w /tmp/tls.pcap 'tcp port 443' &
SSLKEYLOGFILE=/tmp/keys.log curl -s -o /dev/null https://example.com/
sleep 1; sudo pkill -INT -x tcpdump
# 2. Copy /tmp/tls.pcap and /tmp/keys.log to a machine with Wireshark.
#    Wireshark: Edit -> Preferences -> Protocols -> TLS -> (Pre)-Master-Secret log filename = keys.log
#    Filter "http2 || http" -> the decrypted request and response appear.
# 3. Filter "tls.handshake.type == 1" -> the ClientHello; expand it to find SNI and ALPN (section 10).
# 4. Clean up: keys.log decrypts that traffic. Delete both files.
sudo rm -f /tmp/tls.pcap /tmp/keys.log
```

**How it breaks**

| Problem | Symptom | Fix |
|---|---|---|
| Capture too big / CPU hit on a busy host | Disk fills, packets dropped by kernel (`N packets dropped by kernel`) | tighter filter, `-s 128`, `-c`, `-C/-W` rotation |
| Wrong interface | Empty capture while traffic flows | `-i any` first, then narrow down |
| Capture filter typo | `syntax error in filter expression` | quote the whole filter; test with `-c 1` |
| Opening a huge pcap | Wireshark slow | `tshark -r big.pcap -Y FILTER -w small.pcap` first |

**Why it matters for troubleshooting:** tcpdump answers "did the packet get
there?". Wireshark answers "what went wrong inside this conversation?":
retransmission bursts, zero windows, a reset in the middle of a TLS
handshake, a 502 body.

**Next step:** packets show the network. When the question is "what did the
*program* actually do?" (which config it read, which address it chose), use
strace.

### strace: what curl really does

**Level:** [L2 · Mid].

**Concept.** `strace` prints every system call a program makes: each file it
opens, each socket it connects, each error the kernel returns. For
networking it answers questions packets can't: which resolver config the
program read, whether it consulted `/etc/hosts`, which CA bundle it loaded,
which address it connected to, and the exact `errno` it got. curl resolves
names in a separate thread, so use `-f` to follow threads.

**Key terms**

| Term | Meaning |
|---|---|
| `-f` | Follow threads and child processes |
| `-e trace=openat,connect` | Only these syscalls (also: `network`, `%file`, `sendto,recvfrom`) |
| `-p PID` | Attach to a running process (e.g. a stuck worker) |
| `-tt -T` | Timestamps / time spent in each call (find the slow one) |
| `-s 200` | Show up to 200 characters of strings |
| `= -1 ENOENT (No such file or directory)` | The call failed, with the errno |

**See it on a real system**: the Ops Ladder strace exercise.

```bash
strace -f -e trace=openat,connect curl -so /dev/null https://example.com 2>&1 | grep -vE 'ENOENT|\.so|locale'
```

```
openat(AT_FDCWD, "/usr/lib/ssl/openssl.cnf", O_RDONLY) = 3
[pid  4122] openat(AT_FDCWD, "/etc/nsswitch.conf", O_RDONLY|O_CLOEXEC) = 7
[pid  4122] openat(AT_FDCWD, "/etc/host.conf", O_RDONLY|O_CLOEXEC) = 7
[pid  4122] openat(AT_FDCWD, "/etc/resolv.conf", O_RDONLY|O_CLOEXEC) = 7
[pid  4122] openat(AT_FDCWD, "/etc/hosts", O_RDONLY|O_CLOEXEC) = 7
[pid  4122] connect(7, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("127.0.0.53")}, 16) = 0
[pid  4122] openat(AT_FDCWD, "/etc/gai.conf", O_RDONLY|O_CLOEXEC) = 7
[pid  4121] connect(5, {sa_family=AF_INET, sin_port=htons(443), sin_addr=inet_addr("203.0.113.80")}, 16) = -1 EINPROGRESS (Operation now in progress)
[pid  4121] openat(AT_FDCWD, "/etc/ssl/certs/ca-certificates.crt", O_RDONLY) = 6
+++ exited with 0 +++
```

(Illustrative: the real IP of example.com and the exact list differ by version.)

- `pid 4122` is curl's resolver thread. It follows the getaddrinfo path from
  section 8: `nsswitch.conf` → `host.conf` → `resolv.conf` → `/etc/hosts` →
  a UDP "connect" to the stub 127.0.0.53:53 → `gai.conf` to sort the results.
- `connect(... 443 ...) = -1 EINPROGRESS` is normal: curl uses non-blocking
  sockets, and the handshake completes later. A real failure shows
  `ECONNREFUSED`, `ENETUNREACH` or `ETIMEDOUT` in a later call (`getsockopt`
  with `SO_ERROR`, or `poll`).
- `/etc/ssl/certs/ca-certificates.crt` is the trust store curl actually uses.
  If you added a CA and curl still fails, check this line.

**Hands-on lab (test VM only)**: answer three questions with strace alone.

```bash
# 1. Which file made the app use the wrong IP? (plant a hosts entry)
echo '192.0.2.99 example.com' | sudo tee -a /etc/hosts
strace -f -e trace=openat,connect curl -s -m 3 -o /dev/null http://example.com 2>&1 | grep -E 'hosts|connect\('
#   /etc/hosts was opened, then connect() went to 192.0.2.99 -> the hosts file decided, not DNS
sudo sed -i.bak '/^192\.0\.2\.99 example\.com$/d' /etc/hosts

# 2. Where does a stuck process spend its time? (attach to it)
python3 -c 'import socket; s=socket.create_connection(("192.0.2.1", 81), timeout=60)' &
sudo strace -f -tt -p $! -e trace=network,poll 2>&1 | head -5     # poll(...) waiting: the connect() never completes (Ctrl+C to detach)
kill %1

# 3. Which CA bundle does Python use vs curl?
strace -f -e trace=openat python3 -c 'import urllib.request; urllib.request.urlopen("https://example.com")' 2>&1 | grep -iE 'cert|\.pem|\.crt'
strace -f -e trace=openat curl -so /dev/null https://example.com 2>&1 | grep -iE 'cert|\.pem|\.crt'
```

**How it breaks**

| Question | strace evidence | Go to |
|---|---|---|
| "dig works, the app doesn't" | `openat("/etc/hosts")` then `connect()` to an unexpected IP | section 8 |
| "Which config file does it read?" | `openat(...) = 3` vs `= -1 ENOENT` lines | [Learn Linux](27-learn-linux.md) |
| "It hangs" | Last call is `poll`/`connect`/`recvfrom` with no return: waiting on the network | sections 6–7 |
| "CA installed but still untrusted" | It opens a different bundle (certifi, its own store) | section 10 private CA |

Read: [Spying on your programs with strace](https://wizardzines.com/zines/strace/).

**Why it matters for troubleshooting:** strace closes the last gap between
"what I think the program does" and "what it does". Together with tcpdump you
can see both sides: the syscalls going into the kernel and the packets
leaving it.

**Next step:** put every layer together in one walk. That's the L2 exit test.

---

## 15. One request, every layer

> 📚 **Study path:** 1) Note: the [site down playbook](25-playbook-site-down.md); this section is its mental model · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → *Troubleshooting* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 3) KodeKloud: *Networks and Communications* — Network Troubleshooting ([course](https://kodekloud.com/courses/networks-and-communications)) · 4) Practice: the L2 exit test below on a KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) or your homelab, then [SadServers](https://sadservers.com/scenarios) scenarios tagged dns, nginx and ssl · 5) Replay: the [Apache 443 / Dokploy case](21-case-apache-443-dokploy.md) from start to finish.

### The walk from browser to container

**Level:** [L2 · Mid] exit test · [L3 · Senior] when you can teach it · [L4 · Lead] when you run it for others during an incident.

**Concept.** Here is everything in this module as one request, after the
Dokploy migration: a user opens `https://shop.example.com`. Each step can
fail independently, and each has one command that proves it worked. This is
the mental model behind the [site down playbook](25-playbook-site-down.md).

```
 browser
   1. DNS        shop.example.com -> 203.0.113.10 (stub -> recursive -> authoritative; TTL; AAAA?)
   2. Route      laptop -> gateway -> internet -> office firewall (DNAT 203.0.113.10:443 -> 192.0.2.10:443)
   3. TCP        SYN to 192.0.2.10:443; host firewall; Docker DNAT -> dokploy-traefik 172.18.0.3:443
   4. TLS        SNI shop.example.com -> Traefik picks the Let's Encrypt cert (not TRAEFIK DEFAULT CERT)
   5. HTTP       Host: shop.example.com -> Traefik router -> service -> container 10.0.1.9:8000 on dokploy-network
   6. Upstream   Traefik -> app: TCP connect, app listening on 0.0.0.0:8000 inside its container, healthy
   7. App        app -> database (DNS via 127.0.0.11, TCP 5432), answers 200 within Traefik's timeout
   8. Return     response back through Traefik, conntrack un-DNAT, firewall, internet, browser
```

| Step | Proof it works | If it fails |
|---|---|---|
| 1 DNS | `getent ahosts shop.example.com` (client), `dig @AUTH shop.example.com` | section 8 |
| 2 Route | `ip route get 203.0.113.10`, `mtr -rwn -c 50 203.0.113.10` | section 4 |
| 3 TCP | `nc -zv -w3 shop.example.com 443`; server: `sudo ss -ltnp 'sport = :443'` | sections 5–7 |
| 4 TLS | `openssl s_client -connect shop.example.com:443 -servername shop.example.com` | section 10 |
| 5 HTTP routing | `curl -v --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/` | section 9 |
| 6 Upstream | `docker logs dokploy-traefik` (502/503?), netshoot `ss -ltn` in the app's namespace | sections 6, 11 |
| 7 App | app logs, `curl` from inside the network to `http://APP:8000/health` | [Containers playbook](26-playbook-containers-k8s.md) |
| 8 Return | capture on the server: SYN-ACK and data leave? | section 14 |

**Key terms**

| Term | Meaning |
|---|---|
| Layered bypass | Repeat the request skipping one hop at a time (CDN → LB → proxy → app) |
| First failing hop | The first bypass that *also* fails points at the hop beyond it |

**See it on a real system**: the layered bypass for one URL.

```bash
curl -sv -o /dev/null https://shop.example.com/                                        # 1. through everything
curl -sv -o /dev/null --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/   # 2. skip public DNS / edge
curl -sv -o /dev/null -H 'Host: shop.example.com' http://192.0.2.10/                   # 3. plain HTTP to Traefik (expect a redirect)
docker run --rm --network dokploy-network curlimages/curl -sv http://shop-app:8000/health   # 4. skip Traefik: straight to the app
```

**Hands-on lab (test VM only)**: the L2 exit test from your Ops Ladder.
Have someone (or a script) break **one** thing on a test VM running a small
site behind a proxy. Without being told what, walk DNS → route → firewall →
TLS → proxy → app and name the broken layer *with evidence*: a capture line,
a log line or `curl -v` output. Suggested breaks for a partner or script:

```bash
# pick ONE at random on the test VM, never on production
echo '192.0.2.99 shop.example.com' | sudo tee -a /etc/hosts                       # DNS (client side)
sudo resolvectl dns ens18 192.0.2.254                                            # DNS (resolver)
sudo ip route del default                                                        # routing (use the console!)
sudo nft add table inet x; sudo nft 'add chain inet x in { type filter hook input priority 0; }'; sudo nft add rule inet x in tcp dport 443 drop   # firewall
docker stop shop-app                                                             # upstream -> 502
sudo sed -i 's/shop.example.com/shpo.example.com/' /etc/dokploy/traefik/dynamic/shop.yml   # proxy routing -> 404 (file-provider example)
```

Time limit: 15 minutes. Write a five-line note afterwards: symptom, first
wrong guess, the evidence that settled it, fix, and what you'll check first
next time.

**How it breaks**: every row of the table above. The walk is the method.

**Why it matters for troubleshooting:** Incidents are rarely a single tool's
job. The value is in the *order*: each step either clears a layer or names
it, and you never debug the app while DNS is broken.

**Next step:** prove it with the self-check below, then move on to
[Learn web servers and proxies](29-learn-webservers-proxies.md).

---

## 16. Self-check / exit test

### Questions

Answer from memory, then check against the section in brackets.

1. A host has 192.0.2.10/24 and gateway 192.0.2.1. For which of these does it
   ARP for the destination itself: 192.0.2.77, 198.51.100.5, 192.0.3.1? (2, 3)
2. What's the network, broadcast and host range of 10.20.35.200/20? (3)
3. `ip route get 10.1.2.3` prints no `via`. What does that mean, and when is it
   a bug? (4)
4. Why does a server with no route back to the client still answer when the
   router masquerades? (5)
5. Which netfilter hook does a packet to a published Docker port traverse
   after DNAT, and why doesn't `ufw deny` stop it? (5, 7)
6. Explain `0.0.0.0:443`, `*:443`, `127.0.0.1:443` and `192.0.2.10:443` in
   `ss` output. Which ones conflict with each other? (6)
7. `Connection refused` vs `Connection timed out` vs `No route to host`: what
   happened on the wire in each case? (6)
8. 40 sockets in `CLOSE-WAIT` toward PostgreSQL. Whose bug is it, and what
   will eventually fail? (6)
9. 1 Gbit/s link, 80 ms RTT, 4 MB max window: what's the single-stream ceiling? (6)
10. Name the three conntrack facts you'd check on a NAT box with intermittent
    timeouts at peak. (7)
11. `dig` returns the new IP, `curl` connects to the old one. List three
    causes and the command that tells them apart. (8)
12. You created a record two minutes ago and still get NXDOMAIN. Why, and how
    do you prove the record exists? (8)
13. What's 127.0.0.11, and why might a container on an on-prem host try
    8.8.8.8? (8)
14. Which component typically returns 502, 503 and 504, and what does each
    mean? (9, 11)
15. An app behind Traefik redirects forever. Which header is the usual
    suspect? (9)
16. What does SNI do, and why does `openssl s_client` without `-servername`
    sometimes show `TRAEFIK DEFAULT CERT`? (10)
17. `unable to get local issuer certificate`: name the two common causes and
    how to tell them apart. (10)
18. Where must the Harbor CA go for Docker, for containerd, and for a Python
    app inside a container? (10)
19. Why does Let's Encrypt HTTP-01 fail while Apache still owns port 80? When
    would you use DNS-01 instead? (10)
20. Small requests work over the VPN, large downloads hang. What's your first
    test? (12)
21. Two Swarm nodes: containers talk on the same node, not across nodes.
    Which ports do you check? (12)
22. Why must you never block ICMPv6 wholesale? (13)
23. Write a tcpdump filter that shows only SYNs and RSTs for port 443. (14)
24. In a strace of curl, what do the `openat("/etc/hosts")` and
    `connect(... EINPROGRESS)` lines tell you? (14)

### Practical timed tasks (test VM)

| # | Task | Time limit | Pass when |
|---|---|---|---|
| 1 | Given only a port number on a multi-service box, name the process, its unit, config file and log command | 5 min | All four, with commands shown |
| 2 | Build the netns lab from memory (no script) and ping server from client | 15 min | Ping works; you can explain every command |
| 3 | Partner breaks one of: prefix, gateway, forwarding, firewall drop, listener. Name the layer with evidence | 10 min | Correct layer + one capture or command output as proof |
| 4 | Break DNS three ways (bad upstream, resolved stopped, `/etc/hosts`) and diagnose each with tcpdump, `getent`, resolver debug logs | 20 min | Three exact error texts recorded and explained |
| 5 | Create a private CA, issue a cert with SAN, serve it, make curl trust it system-wide, then show a container still doesn't | 20 min | `curl` OK on host without `--cacert`; container error explained |
| 6 | Reproduce the Apache/Dokploy clash: one service holds `*:443`, a second fails to bind; resolve by moving the first to another address/port | 15 min | Both run; `ss -ltnp` shows the new layout |
| 7 | Make a reverse proxy return 502, 503 (or "no live upstreams") and 504 on purpose, and find each cause from the proxy log alone | 20 min | Three log lines quoted and explained |
| 8 | Build an MTU black hole in the lab and fix it with MSS clamping | 15 min | Big download hangs, then works; `ping -M do` sizes recorded |
| 9 | Capture a full HTTPS connection, open it in Wireshark with `SSLKEYLOGFILE`, and point out SNI, ALPN and the HTTP status | 15 min | Screenshot or notes of the three fields |
| 10 | The L2 exit test: "the site is down", walk all layers, name the broken one with evidence | 15 min | Correct layer, evidence, five-line note |

If you can do tasks 1, 3, 4 and 10 inside the limits, you've passed the
networking part of L2.

### Senior and lead questions

**Level:** [L3 · Senior] and [L4 · Lead]. These have no single right answer.
Write a half-page plan for each, then compare it with the playbooks and with
[Deployment patterns](35-deployment-patterns.md). A senior's answer names
the evidence for each step and the rollback.

| # | Question | Sections |
|---|---|---|
| 25 | Plan the DNS and TLS side of moving four Apache vhosts behind Traefik with no visible downtime: the TTL timeline, the certificate strategy per host (HTTP-01, DNS-01 or the existing certificates), the command that verifies each step, and the rollback | 8, 10, 15 |
| 26 | Design one address plan for an office LAN, a WireGuard VPN, Docker on every server, a Swarm overlay and a kubeadm cluster, with no overlaps. Write the `daemon.json` pools and the pod and service CIDRs | 3, 12 |
| 27 | A NAT gateway times out intermittently every evening. Which three metrics go on a dashboard, with which alert thresholds, so the next occurrence is caught before users notice? | 7, 11 |
| 28 | The team keeps losing afternoons to expired or untrusted certificates (Harbor CA, Let's Encrypt, kubeadm). Propose the monitoring and the runbook that ends this | 10 |
| 29 | Write the one-page layered-walk checklist you'd hand a new Junior for their first on-call shift | 1, 15 |

### Exit test by career stage

| Stage | You pass when you can… | Questions | Tasks |
|---|---|---|---|
| Fresher [L0] | explain `ip -br addr` and `ip route` on your own server and subnet on paper | 1, 2 | 2 |
| Junior [L1] | do the port drill in five minutes and tell refused, timed out and unreachable apart | 3–10 | 1, 6 |
| Mid-level [L2] | name the broken layer with evidence within 15 minutes | 11–24 | 3, 4, 5, 7, 9, 10 |
| Senior [L3] | build and fix the MTU black hole, and write plans 25 and 26 that a colleague could run | 20, 21, 25, 26 | 8 |
| Lead [L4] | turn an incident into monitoring and teach the walk to someone else | 27–29 | 10, as the partner who breaks things for a Junior |

---

## 17. Where to go next

- **Next module:** [Learn: Apache, Nginx, Traefik, Dokploy](29-learn-webservers-proxies.md).
  Everything from sections 9–11 applied to the proxies you run, including
  the Apache → Traefik migration patterns.
- **Then:** [Learn Docker](30-learn-docker.md) (bridge networks, published
  ports and embedded DNS from the inside) and
  [Learn Kubernetes](31-learn-kubernetes.md) (Services, kube-proxy, CoreDNS,
  CNI overlays, mTLS certificates for the CKA).
- **Playbooks to keep open at work:**
  [Site down](25-playbook-site-down.md),
  [Network slow](24-playbook-network-speed.md),
  [Who owns this port?](22-playbook-ports-inventory.md),
  [Containers and Kubernetes](26-playbook-containers-k8s.md) and the
  [Apache 443 / Dokploy case study](21-case-apache-443-dokploy.md).
- **Your real incident, finished:** [Deployment patterns](35-deployment-patterns.md)
  takes your Apache-on-81/444 fix to the end (Traefik routes the legacy
  vhosts) and compares it with the other ways to share 80 and 443.
- **KodeKloud next:** *Nginx For Beginners* ([course](https://kodekloud.com/courses/nginx-for-beginners))
  before module 29, then the *Certified Kubernetes Administrator (CKA)*
  Networking section ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator))
  for Services, CNI and CoreDNS.
- **Your next career stage:** the [career ladder](40-career-ladder.md) lists
  what each stage is trusted with and which modules to master next.
- **Command references:** [Network](02-network.md), [DNS](08-dns.md),
  [Web, HTTP & TLS](18-web-http-tls.md), [Docker](14-docker-containers.md),
  [Kubernetes](15-kubernetes.md), [Time & NTP](12-time-ntp.md)
  (certificate errors from clock drift).
- **Practice on real broken systems:** [SadServers](https://sadservers.com/scenarios)
  (filter by the dns, nginx and ssl tags), [Killercoda](https://killercoda.com/linux),
  and the [iximiuz Labs tutorial that builds a bridge network from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch),
  which is the netns lab of this module taken further.
- **Reading:** [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/),
  Julia Evans's [blog](https://jvns.ca/) and [Some ways DNS can break](https://jvns.ca/blog/2022/01/15/some-ways-dns-can-break/),
  the zines ([tcpdump](https://wizardzines.com/zines/tcpdump/),
  [strace](https://wizardzines.com/zines/strace/),
  [How DNS Works](https://wizardzines.com/zines/dns/), paid), and
  [How Linux Works, 3rd ed.](https://nostarch.com/howlinuxworks3) for the
  kernel side of networking.
- **The habit that makes it stick:** after every incident at work, even a
  small one, write the five-line note (symptom, first wrong guess, evidence,
  fix, what you'll check first next time) and tag it with the layer from
  section 1.
