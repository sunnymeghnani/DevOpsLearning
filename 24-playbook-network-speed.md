# 24 — Network Is Slow: Speed, Latency & Loss Troubleshooting

"The network is slow" is the vaguest ticket you will ever get, and also one of the
most common. It can mean a slow DNS lookup, a lossy Wi-Fi link, a 100 Mbit/s
duplex-mismatched switch port, a VPN with the wrong MTU, a far-end server that is
simply overloaded, a full conntrack table, or one core drowning in network
interrupts. This playbook turns that vague complaint into numbers, then walks the
layers in the cheapest-first order until one of them confesses. Every step says
**what to run, how to read the output, why this step comes now, and where to go
next**.

How this module relates to the others:

- [Network reference](02-network.md) is the command dictionary (ping, mtr, ss, ip, tcpdump). This module is the *method* that strings those commands together for speed problems.
- [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md) teaches the theory from zero. Section 2 below is the condensed version you need while on call.
- [Learn: performance & observability](32-learn-performance-observability.md) covers the USE method, Prometheus and Grafana, which is where the baselines in section 21 live.
- [Why is the system slow?](23-playbook-slow-system.md) is the sibling playbook. If the box itself is starved (CPU, memory, disk), the network only *looks* slow.
- [Site down](25-playbook-site-down.md) is for "it does not work at all". This module is for "it works, but slowly or unreliably".

**Career stages this playbook serves.** Mid-level engineers (L2) use most of it.
Use the table to find your entry point, and see the
[career ladder](40-career-ladder.md) for the full picture. Sections are tagged
like **[L2 · Mid]** in their first lines.

| Stage | Level | What you should own in this module | Start at |
|-------|-------|------------------------------------|----------|
| Fresher | L0 Foundations | Bits vs bytes, RTT, loss, why "slow" needs a number | Section 2 |
| Junior | L1 Operator | Frame the ticket, run Steps 0–3, hand over clean evidence | Sections 3–4, 11–13 |
| Mid-level | L2 Troubleshooter | Steps 0–14 and Scenarios A–E alone; name the broken layer with evidence | Sections 4–7, 14–18, 20 |
| Senior | L3 Platform | Safe tuning, AWS limits, container/K8s speed, Scenario F, fleet-wide fixes | Sections 8–10, 19 |
| Senior/Lead | L4 SRE | Baselines, probes, alerts and postmortems so slowness is caught before tickets | Sections 21–22 |

> ⚠️ All commands are documented for you to run on **your** servers and clients.
> Sample outputs are illustrative (Ubuntu 22.04/24.04 unless stated; RHEL/Rocky
> differences are noted). Addresses use documentation ranges (192.0.2.0/24,
> 198.51.100.0/24, 203.0.113.0/24) and private ranges. UPPERCASE words such as
> HOST, IFACE, PORT, CONTAINER and POD are placeholders.

---

## 1. How to use this playbook

> 📚 **Study path (whole module):** 1) Note: [Learn: networking](28-learn-networking.md), sections 6 (TCP) and 12 (VPNs, overlays and MTU) · 2) KodeKloud: *Networks and Communications*, Network Troubleshooting module ([link](https://kodekloud.com/courses/networks-and-communications)) · 3) Read: [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) · 4) Practice: the section 22 drills on two test VMs or a KodeKloud *Ubuntu playground* ([link](https://kodekloud.com/playgrounds/playground-ubuntu)).

**Level:** [L1–L2 · Junior → Mid]. Juniors follow the method as a checklist.
Mid-level engineers also explain why each step comes next.

### The method in one paragraph

1. **Frame** the complaint: which path, which direction, which protocol, who is affected, since when, and what number counts as "slow" (section 3).
2. **Measure, cheapest first**: time the phases of one request (Step 1), then latency and loss along the path (Steps 2–3), then raw throughput between hosts you control (Steps 4–6). These tell you *which layer* to look at.
3. **Drill into the layer** the numbers point at: the local link (Step 7), the TCP stack (Step 8), MTU (Step 9), competing traffic (Step 10), shaping (Step 11), conntrack (Step 12), CPU/IRQ (Step 13), DNS (Step 14).
4. **Change one thing**, re-measure with the *same* test, keep or roll back.
5. **Write the baseline down** so next time "slow" has a reference number (section 21).

The single most important habit: **never accept "slow" without a number and a
comparison**. "Downloads are slow" becomes "a 1 GB file from mirror.example.com
takes 9 minutes (≈15 Mbit/s) from web01; the same file takes 20 s from web02 in
the same rack". The second sentence already points at the answer.

### Symptom to starting point

| You hear… | Start at | Likely layers |
|-----------|----------|---------------|
| "Every page takes a few seconds before it starts loading" | Step 1, then Step 14 | DNS, TLS handshake, IPv6 fallback |
| "Pages start fast but big downloads crawl" | Steps 4–6, Step 8 | BDP/window, loss, shaping, far end |
| "Everything is slow from this one server" | Step 7, Step 13 | NIC/duplex, IRQ, local shaping |
| "Copy between two servers is ~11 MB/s" | Scenario B | 100 Mbit/s link, duplex, disk, scp CPU |
| "SSH works but scp/git clone/docker pull hangs" | Scenario D | MTU / PMTUD black hole |
| "Only VPN users complain" | Scenario C | Tunnel MTU, full tunnel, concentrator CPU |
| "It is fine most of the time, then spikes" | Scenario E | Bufferbloat, Wi-Fi, CPU steal, cron jobs |
| "New server is slower than the old one" | Scenario F | NIC model, sysctls, CPU power, path |
| "New connections fail or stall under load" | Step 12 | conntrack table full, NAT ports |
| "Only from containers / pods" | Section 10 | Overlay MTU, NAT, CPU throttling |
| "Only on AWS, under load" | Section 9 | Instance bandwidth allowance, NAT GW |

### Install the toolkit once

Put these on every server image (Ansible role or cloud-init) so you are not
installing packages in the middle of an incident.

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y iperf3 mtr-tiny ethtool iftop nethogs nload bmon vnstat \
  sysstat conntrack tcpdump iproute2 iputils-ping iputils-tracepath \
  bind9-dnsutils net-tools
# iperf3 asks "Start Iperf3 as a daemon automatically?" -> answer No.
# A permanently listening test server is an open door and a DoS lever.

# RHEL / Rocky / Alma (iftop, nethogs, nload, bmon, vnstat come from EPEL).
# epel-release is in the Rocky/Alma repos; on RHEL itself enable CodeReady
# Builder and install EPEL as described in Fedora's EPEL documentation.
sudo dnf install -y epel-release
sudo dnf install -y iperf3 mtr ethtool iftop nethogs nload bmon vnstat \
  sysstat conntrack-tools tcpdump iproute iputils bind-utils net-tools
```

| Tool | Answers | Layer |
|------|---------|-------|
| `curl -w` | Where inside one request is the time going? | DNS, TCP, TLS, server |
| `ping`, `mtr`, `tracepath` | RTT, jitter, loss, path MTU, which hop | IP path |
| `iperf3` | What can the network carry, with no disk or app involved? | Transport |
| `ethtool`, `ip -s link` | Link speed, duplex, NIC errors and drops | Physical / link |
| `ss -ti`, `nstat` | Per-connection RTT, cwnd, retransmits | TCP |
| `iftop`, `nethogs`, `sar -n DEV` | Who uses the bandwidth, now and historically | Contention |
| `tc` | Is traffic being shaped or policed on this host? | Queueing |
| `conntrack` | Is the state table full? | Netfilter / NAT |
| `mpstat`, `/proc/interrupts` | Is one CPU drowning in softirq? | Host CPU |
| `resolvectl`, `dig` | Is name resolution the slow part? | DNS |

---

## 2. Concepts: what "slow" really means

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course*, Networking Basics lesson ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page)) · 2) KodeKloud: *Networks and Communications*, protocols (TCP/IP/HTTP) module ([link](https://kodekloud.com/courses/networks-and-communications)) · 3) Note: [Learn: networking](28-learn-networking.md), section 6 (TCP, retransmissions, window/BDP) · 4) Practice: answer self-check questions 1, 5 and 7 (section 22) without looking.

**Level:** [L0–L2 · Fresher → Mid]. Freshers need units, RTT and loss. Mid-level
engineers need BDP and the Mathis formula to explain why one stream is slow.

You cannot troubleshoot "speed" until you know which of five different quantities
the user is complaining about. They are related but not interchangeable.

### Bandwidth, throughput and goodput

**Bandwidth (capacity)** is the maximum rate a link can carry: a 1 GbE port is 1
Gbit/s, a 500/50 broadband line is 500 Mbit/s down and 50 up. It is a property of
the *narrowest link on the path*, not of your NIC.

**Throughput** is what you actually get through end to end, measured over time.

**Goodput** is throughput minus protocol overhead and retransmissions, which is
what the user sees as "MB/s" in a download dialog.

Overheads are real. On 1 GbE with a 1500-byte MTU, Ethernet framing, IP and TCP
headers leave about **940 Mbit/s of TCP goodput (~117 MB/s)**. If iperf3 shows 935
Mbit/s on a gigabit link, that is a *perfect* result, not a slow one.

**The units trap.** Network gear speaks in **bits** (Mbit/s, Mbps). Browsers,
`scp`, `rsync` and Windows Explorer speak in **bytes** (MB/s, MiB/s).
Multiply bytes by 8.

| User sees | In bits | Smells like |
|-----------|---------|-------------|
| 11–12 MB/s | ~94 Mbit/s | A **100 Mbit/s** link somewhere (bad cable, wrong port, duplex) |
| 110–118 MB/s | ~940 Mbit/s | Healthy gigabit, nothing to fix on the network |
| 1.1 GB/s | ~9.4 Gbit/s | Healthy 10 GbE |
| 3–6 MB/s over the internet | 25–50 Mbit/s | Single TCP stream limited by RTT × window or loss |

### Latency, RTT and jitter

**Latency** is how long one packet takes to get somewhere. **RTT** (round-trip
time) is there and back, which is what `ping` shows and what TCP feels. It has
three parts: propagation (speed of light in fibre, ~5 µs per km, so ~1 ms RTT per
100 km of fibre path), serialization (pushing bits onto the wire) and **queueing**
(waiting in buffers). Only queueing changes from second to second, so when RTT
rises under load, a queue is filling somewhere.

**Jitter** is the variation in latency from packet to packet (`mdev` in ping,
`StDev` in mtr, `Jitter` in iperf3 UDP). Bulk downloads tolerate jitter; voice,
video, games, remote desktops and anything with small request/response
round-trips do not.

Numbers worth memorizing (typical, not guarantees):

| Path | Typical RTT |
|------|-------------|
| Same host (loopback, container to container on one bridge) | 0.02–0.1 ms |
| Same LAN / same switch | 0.1–0.5 ms |
| Same AWS Availability Zone | well under 1 ms |
| Across AWS AZs in one region | ~0.5–2 ms |
| Same city / country over the internet | 5–30 ms |
| Europe ↔ US East | 70–100 ms |
| Europe ↔ India / US ↔ Asia | 120–250 ms |
| Geostationary satellite | 550–700 ms |
| Wi-Fi first hop (healthy) | 1–5 ms; spikes to 50+ ms when busy |

### Packet loss and why 1% is a disaster

Loss is packets that never arrive. Applications on UDP (voice, video, DNS) see
glitches or retries. **TCP sees loss as congestion and slows down**: classic
congestion control (Reno, CUBIC) cuts its sending window every time it detects a
loss. The well-known Mathis approximation gives the ceiling for one loss-based TCP
stream:

```
throughput  <=  (MSS / RTT) x (1.22 / sqrt(loss_rate))

MSS 1448 bytes, RTT 50 ms, loss 0.1 %  ->  about 9 Mbit/s
MSS 1448 bytes, RTT 50 ms, loss 1 %    ->  about 2.8 Mbit/s
MSS 1448 bytes, RTT 1 ms,  loss 0.1 %  ->  about 450 Mbit/s
```

→ The same 0.1% loss that is invisible on a LAN cripples a WAN transfer, because
the penalty scales with RTT. "It is only 1% loss" is never a reassuring sentence.

→ On a healthy wired path, loss should be **0%**. Anything persistent above
~0.1% is worth chasing.

### Bandwidth-delay product and the TCP window

TCP may only have a limited amount of unacknowledged data "in flight". That limit
is the **window**: the smaller of the receiver's advertised window (rwnd, how much
free buffer the receiver has) and the sender's congestion window (cwnd, the
sender's estimate of what the network can take). One stream can therefore never go
faster than:

```
max single-stream throughput = window / RTT
```

To fill a path, the window must be at least the **bandwidth-delay product (BDP)**:
capacity × RTT. That is how many bytes are "in the pipe" at once.

| Path | BDP (bytes needed in flight) |
|------|------------------------------|
| 1 Gbit/s × 1 ms (LAN) | 125 KB |
| 1 Gbit/s × 20 ms (same country) | 2.5 MB |
| 1 Gbit/s × 80 ms (Europe ↔ US) | 10 MB |
| 10 Gbit/s × 80 ms | 100 MB |

And the other way round, what a given window allows:

| Window | at 1 ms | at 20 ms | at 80 ms |
|--------|---------|----------|----------|
| 64 KB (no window scaling) | 524 Mbit/s | 26 Mbit/s | 6.5 Mbit/s |
| 4 MB | 33 Gbit/s | 1.7 Gbit/s | 420 Mbit/s |
| 16 MB | 134 Gbit/s | 6.7 Gbit/s | 1.7 Gbit/s |

This is why **one TCP stream across an ocean rarely fills a fast link** while
eight parallel streams do, and why download managers, `aria2c -x`, S3 multipart
transfers and `iperf3 -P` exist. Linux autotunes the window up to the third value
of `net.ipv4.tcp_rmem` / `tcp_wmem` (6 MB / 4 MB by default on Ubuntu), so long
fat paths need bigger maximums (section 8).

### Why "speed" complaints are rarely about bandwidth

In practice, "the network is slow" turns out to be, roughly in order of how often
you will meet them:

1. **The far end** — the server, API or mirror is overloaded, rate-limits per connection, or the CDN mapped you to a distant edge.
2. **Latency × chattiness** — an app that makes 300 sequential round-trips per page (N+1 queries, many small HTTP calls) is slow at 30 ms RTT no matter how fat the pipe is. Moving the app and its database into different AZs or sites does this.
3. **Loss** — a bad cable, Wi-Fi, an overloaded uplink or a policer; TCP backs off.
4. **DNS** — a dead first resolver adds 5 s (the default resolver timeout) to every new name.
5. **Connection setup** — TLS handshakes, proxies, IPv6 tried first and timing out.
6. **MTU** — small things work, large things stall.
7. **Actual bandwidth exhaustion** — someone's backup, a sync job, or a link that negotiated 100 Mbit/s.
8. **The host itself** — CPU, softirq, disk; see [Why is the system slow?](23-playbook-slow-system.md).

Measuring the phases (Step 1) separates 1, 2, 4 and 5 from the rest in one command.

### Latency under load (bufferbloat)

A link can have 20 ms RTT when idle and 600 ms when someone is uploading, because
a router or modem buffers far too many packets instead of dropping a few early.
That is **bufferbloat**: everything interactive becomes sluggish exactly when the
link is busy. You detect it by running `ping` *while* the link is loaded (Scenario
E). It is fixed with smart queue management (fq_codel or CAKE, with shaping a
little below the real line rate) on the bottleneck router, not by buying more
bandwidth.

### Direction matters

Upload and download are different paths with different bottlenecks, and for TCP
the **sender's** congestion control and buffers govern the speed. A user's slow
*download* from your server is controlled by your server's send side (its
`tcp_wmem`, its congestion control, its uplink) and the user's receive window.
Changing `tcp_congestion_control` on the *client* does nothing for downloads.
Always test both directions (`iperf3 -R`).

---

## 3. Frame the problem before measuring

> 📚 **Study path:** 1) Note: [Why is the system slow?](23-playbook-slow-system.md), section 1 (define slow first) · 2) Read: [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 3) KodeKloud: *Fundamentals of SRE*, Incident Management module ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Practice: fill the framing table below for your last "slow" ticket.

**Level:** [L1 · Junior]. Framing is the first thing a junior does on every
ticket, and the first thing a senior checks when reviewing one.

Five minutes of questions saves an hour of random commands. Write the answers in
the ticket.

### The framing questions

| Question | Why it matters | What the answer rules in or out |
|----------|----------------|---------------------------------|
| What exactly is slow, with what number? | "Slow" without a number cannot be verified as fixed | Sets the success criterion |
| From where to where? (source host, destination, path) | Speed is a property of a path, not of a host | Points at the segment |
| Which direction? Upload, download, both? | Different queues, shapers and senders | Asymmetric problems: duplex, shaping, one-way loss |
| Which protocol / app? (HTTPS, SMB, scp, git, docker pull) | App and tool overhead can dominate | scp CPU, SMB signing, proxy inspection |
| One user, one host, one site, or everyone? | Scope tells you how far from the user the fault is | One host → that host. Everyone → shared path or server |
| Wired or Wi-Fi? VPN on or off? | The two most common hidden layers | Tells you which extra hop to test first |
| Since when? Any change? (deploy, new switch, new VM, patch) | Most incidents follow a change | Roll back before deep diagnosis |
| Constant or intermittent? Time of day? | Intermittent = contention, scheduled jobs, Wi-Fi, CPU steal | Constant = configuration or a physical fault |
| Small requests, big transfers, or both? | Small slow = latency/DNS/setup; big slow = throughput/window/loss/MTU | Picks Steps 1–3 or 4–9 |
| What is the expected speed? (contract, link, last month's baseline) | You may be looking at a healthy link at its limit | Sometimes the answer is "this is normal" |

### Draw the path

Sketch the path before running anything. Every box is a place where speed can be
lost, and every arrow is a place you can measure across.

```
 user laptop ──Wi-Fi──> AP ──> office switch ──> firewall/NAT ──> ISP ──> internet
                                                                            │
 app.example.com  <── Traefik container <── Docker bridge/overlay <── host NIC
        │                                                  (web01, 10.0.20.11)
        └──> database on db01 (10.0.20.21), maybe another AZ or site
```

Inside each host there is a second, hidden path that matters just as much:

```
 application -> socket buffer -> TCP (cwnd, rwnd, retransmits) -> qdisc (tc)
             -> netfilter / conntrack -> driver ring buffer -> NIC -> cable/SFP
```

### Rules of engagement for speed tests

> ⚠️ Throughput tests (iperf3, big downloads) **saturate links on purpose**. On a
> production network that is a self-inflicted incident. Get agreement first, run
> short tests (10 s) outside peak hours, cap the rate with `-b` when you only need
> to prove a floor, never leave an iperf3 server running, and remove any firewall
> rule you opened for the test.

- Test one variable at a time, and keep the exact command so before and after are comparable.
- Test from the closest point outward: host → gateway → next site → far end.
- Test hosts **you control** for throughput. Public speed-test sites measure their own path and their own load, not yours.
- Record the time of every test so you can line it up with graphs and logs later.

---

## 4. Core method: path, setup and latency (Steps 0–3)

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs*, Networking → Troubleshooting lesson ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 2) Note: [Network reference](02-network.md), section 1 (reachability: ping, mtr, ip route get) · 3) Read: [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html) for `--resolve` · 4) Practice: run Steps 0–3 against your own server from a KodeKloud *Ubuntu playground* ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) and save the output as your first baseline.

**Level:** [L1–L2 · Junior → Mid]. A junior runs these four steps and attaches
the output to the ticket. A mid-level engineer reads mtr correctly and decides
who owns the fault.

These four steps are cheap, safe on production, and need nothing on the far end.
Together they answer: *is the time spent before the data starts flowing, or while
it flows?*

### Step 0 — Identify the path and hidden hops

**Goal:** know which interface, gateway, tunnel and proxy your traffic really uses before you measure it.

```bash
# Which interface, gateway and source IP will traffic to this destination use?
ip route get 203.0.113.10

# Any tunnels (wg0, tun0, vti), bridges or overlays that could be in the path?
ip -br link
ip -br addr

# Wi-Fi or wired? (Linux clients with NetworkManager)
nmcli -t -f DEVICE,TYPE,STATE device

# Is an HTTP(S) proxy configured for this shell? (systemd services and Docker
# have their own proxy settings, see the web reference)
env | grep -i _proxy

# Does the name resolve to IPv6 as well? Clients may try IPv6 first.
getent ahosts app.example.com
```

```
$ ip route get 203.0.113.10
203.0.113.10 dev wg0 src 10.8.0.5 uid 1000
    cache

$ ip -br link
lo        UNKNOWN  00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
eno1      UP       3c:ec:ef:12:34:56 <BROADCAST,MULTICAST,UP,LOWER_UP>
wg0       UNKNOWN  <POINTOPOINT,NOARP,UP,LOWER_UP>
docker0   DOWN     02:42:9a:11:22:33 <NO-CARRIER,BROADCAST,MULTICAST,UP>

$ env | grep -i _proxy
https_proxy=http://proxy.corp.example:3128
no_proxy=localhost,127.0.0.1,.corp.example

$ getent ahosts app.example.com
2001:db8:10::20 STREAM app.example.com
2001:db8:10::20 DGRAM
2001:db8:10::20 RAW
203.0.113.10    STREAM
203.0.113.10    DGRAM
203.0.113.10    RAW
```

**What it means:**

- `dev wg0` → traffic to this address goes **into a WireGuard tunnel**, not out of `eno1`. The tunnel adds encapsulation (MTU 1420 by default), encryption CPU and the VPN server's own uplink to the path.
- `https_proxy=...` → curl, apt, pip and most CLI tools in this shell send HTTPS through `proxy.corp.example`. The proxy's speed, its SSL inspection and its antivirus scanning are now part of "the network".
- `getent ahosts` lists the IPv6 address **first** → glibc prefers it. If IPv6 is broken somewhere on the path, clients waste time on it before falling back to IPv4.
- A healthy, simple case looks like `203.0.113.10 via 10.0.20.1 dev eno1 src 10.0.20.11`, no proxy variables, and either IPv4 only or an IPv6 path that works as well as IPv4.

**Why this step (now):** every later number is only meaningful if you know which path produced it. Engineers regularly spend an hour tuning `eno1` while the traffic was going through `wg0` or a proxy. It costs ten seconds and changes no state.

**Next step:** in every case continue to Step 1, but keep the hidden hops in mind. If a tunnel is in the path → also read section 11 and Scenario C. If a proxy is in the path → repeat Step 1 with and without it (`curl --noproxy '*'`). If IPv6 is listed first → compare `curl -4` and `curl -6` in Step 1.

### Step 1 — Time the request phases with curl

**Goal:** split one slow request into DNS, TCP connect, TLS, server think time and transfer, so you know which layer owns the delay.

```bash
# Create a reusable timing template once
cat > ~/curl-timing.txt <<'EOF'
   namelookup:  %{time_namelookup}s\n
      connect:  %{time_connect}s\n
   appconnect:  %{time_appconnect}s\n
  pretransfer:  %{time_pretransfer}s\n
starttransfer:  %{time_starttransfer}s\n
        total:  %{time_total}s\n
        speed:  %{speed_download} bytes/s\n
         size:  %{size_download} bytes\n
    remote_ip:  %{remote_ip}\n
         http:  %{http_code}  (http version %{http_version})\n
EOF

# Time a small page (setup-dominated) and a large file (transfer-dominated)
curl -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/
curl -o /dev/null -s -w @$HOME/curl-timing.txt https://downloads.example.com/big.iso

# Run it 5 times: one slow run can be a cold cache; five show the pattern
for i in 1 2 3 4 5; do
  curl -o /dev/null -s -w '%{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}\n' https://app.example.com/
done

# Compare address families and proxy/no proxy
curl -4 -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/
curl -6 -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/
curl --noproxy '*' -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/

# Bypass DNS entirely and hit one specific backend IP (SNI and Host stay correct)
curl --resolve app.example.com:443:203.0.113.10 -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/
```

The timings are **cumulative from the start**, so each phase is the difference to
the previous one:

```
$ curl -o /dev/null -s -w @$HOME/curl-timing.txt https://app.example.com/
   namelookup:  5.012844s
      connect:  5.041309s
   appconnect:  5.103877s
  pretransfer:  5.104020s
starttransfer:  5.322145s
        total:  5.324001s
        speed:  6412 bytes/s
         size:  34139 bytes
    remote_ip:  203.0.113.10
         http:  200  (http version 2)
```

**What it means:** read it as a timeline.

| Phase | Calculation | This run | Meaning |
|-------|-------------|----------|---------|
| DNS | `namelookup` | **5.01 s** | Name resolution. Anything over ~100 ms on a warm cache is suspicious |
| TCP handshake | `connect − namelookup` | 0.028 s | ≈ 1 RTT to the server (28 ms here, fine) |
| TLS handshake | `appconnect − connect` | 0.063 s | ≈ 1 RTT (TLS 1.3) or 2 RTT (TLS 1.2) plus crypto |
| Server think time | `starttransfer − pretransfer` | 0.218 s | 1 RTT plus the time the app needs to produce the first byte |
| Transfer | `total − starttransfer` | 0.002 s | Pushing the body; dominates only for large responses |

→ Here the network and server are fine; **the whole delay is a 5-second DNS
lookup**. Exactly 5 s is the signature of the resolver's default timeout: the
first DNS server did not answer, and the client retried the next one.

Other shapes you will see:

```
# Shape B: DNS fine, TCP connect slow -> RTT or SYN loss/retransmit
   namelookup:  0.004s
      connect:  1.031s        <- 1 s = one SYN retransmission (initial RTO is 1 s)
   appconnect:  1.090s
starttransfer:  1.152s

# Shape C: everything fast until the server -> the app/backend is slow, not the network
   namelookup:  0.003s
      connect:  0.031s
   appconnect:  0.094s
starttransfer:  2.871s        <- 2.7 s of server think time

# Shape D: fast start, slow body -> throughput problem (big file)
   namelookup:  0.002s
      connect:  0.030s
   appconnect:  0.088s
starttransfer:  0.141s
        total:  92.517s
        speed:  11602345 bytes/s   <- ~11.6 MB/s = ~93 Mbit/s: a 100 Mbit/s bottleneck?
```

- `connect` of almost exactly **1 s, 3 s or 7 s** means SYN packets were lost and retransmitted (1 s initial timeout, then doubling). That is loss or a firewall dropping the first SYN, not "slowness".
- `curl -4` fast but `curl -6` slow (or hanging) → broken IPv6 path; clients that do not implement Happy Eyeballs well suffer the full timeout.
- `--noproxy '*'` fast but default slow → the proxy is the bottleneck.
- `--resolve` to one backend fast but normal slow → DNS or one bad backend among several (repeat `--resolve` against each IP).
- `appconnect` is `0` for plain `http://` URLs, that is expected.

**Why this step (now):** it is one command, it runs against the real service, and it immediately splits the problem into "before the first byte" (DNS, path RTT, TLS, app) and "after the first byte" (throughput). Half of all speed tickets end here because the delay is DNS or the backend, which no amount of network tuning will fix.

**Next step:** if `namelookup` is high → Step 14 (DNS). If `connect − namelookup` is high or lands on 1/3/7 s → Step 2 (ping) and Step 3 (mtr). If `appconnect − connect` is high → TLS (OCSP, huge certificate chains, slow handshake CPU), see the [web/TLS reference](18-web-http-tls.md); if the TLS handshake *hangs* rather than being slow → Step 9 (MTU). If server think time is high → it is the application, see [Site down](25-playbook-site-down.md) and [Why is the system slow?](23-playbook-slow-system.md) on the server. If only `total − starttransfer` is large → throughput, Steps 4–6.

### Step 2 — Measure latency, jitter and loss with ping

**Goal:** get RTT, jitter and loss numbers, first to your own gateway and then to the destination.

```bash
# Find the default gateway
ip route show default

# 1. The first hop: is the local segment (switch, Wi-Fi) clean?
ping -c 50 -i 0.2 10.0.20.1

# 2. The destination (or the last hop that answers ICMP)
ping -c 100 -i 0.2 203.0.113.10

# 3. Bigger packets: does it get worse with size? (hints at errors or MTU)
ping -c 50 -i 0.2 -s 1400 203.0.113.10

# Long-running, timestamped, and "no answer yet" reported as it happens
ping -D -O -i 1 203.0.113.10 | tee ~/ping-$(date +%F-%H%M).log
```

> Very short intervals need root (the unprivileged minimum depends on the iputils
> version), and `ping -f` (flood) is a load test. Do not flood production paths or devices you do
> not own.

```
$ ping -c 50 -i 0.2 10.0.20.1
--- 10.0.20.1 ping statistics ---
50 packets transmitted, 50 received, 0% packet loss, time 9803ms
rtt min/avg/max/mdev = 0.281/0.402/0.913/0.088 ms

$ ping -c 100 -i 0.2 203.0.113.10
PING 203.0.113.10 (203.0.113.10) 56(84) bytes of data.
64 bytes from 203.0.113.10: icmp_seq=1 ttl=53 time=41.8 ms
64 bytes from 203.0.113.10: icmp_seq=2 ttl=53 time=42.1 ms
64 bytes from 203.0.113.10: icmp_seq=3 ttl=53 time=212 ms
...
--- 203.0.113.10 ping statistics ---
100 packets transmitted, 96 received, 4% packet loss, time 19842ms
rtt min/avg/max/mdev = 41.213/58.912/212.401/38.716 ms
```

**What it means:**

- **Gateway**: 0% loss, avg 0.4 ms, mdev 0.09 ms → the local wired segment is clean. On Wi-Fi expect 1–5 ms with occasional spikes; on wired, anything over ~1 ms or any loss to your own gateway is already a finding.
- **Destination**: `min` 41.2 ms is the true path RTT (propagation). `avg` 58.9 ms and `max` 212 ms with `mdev` 38.7 ms mean **queues are filling** somewhere: jitter. 4% loss would cap one TCP stream at a few Mbit/s (section 2).
- **min vs avg**: if `avg` is close to `min`, the path is calm. If `avg` is far above `min`, you are seeing queueing (congestion or bufferbloat).
- **TTL** (`ttl=53`) hints at hop count: most Linux hosts start at 64, Windows at 128, many routers at 255.
- `-s 1400` worse than default size → errors that scale with frame size (bad cable/SFP, CRC errors) or MTU trouble.
- **100% loss** does not prove the host is down: many firewalls and clouds drop ICMP. Use the TCP timing from Step 1 or `mtr -T` (Step 3) instead.

**Why this step (now):** ping is the cheapest way to measure the three numbers that limit TCP (RTT, jitter, loss), and testing the gateway first immediately tells you whether the problem is "local" or "out there". You do this before any throughput test because throughput is a *consequence* of these numbers.

**Next step:** if the **gateway** already shows loss or jitter → the problem is local: Step 7 (link health), and section 11 if it is Wi-Fi. If the gateway is clean but the **destination** shows loss or high jitter → Step 3 to find where along the path it starts. If both are clean but transfers are slow → Steps 4–6. If small pings work and large ones (`-s 1400`) do not → Step 9 (MTU).

### Step 3 — Locate loss and latency along the path with mtr

**Goal:** find the hop where loss or delay starts, and prove it continues to the destination.

```bash
# Report mode: -r report, -w wide, -z AS numbers, -b names and IPs, -c 100 cycles
mtr -rwzbc 100 203.0.113.10

# ICMP filtered somewhere? Use TCP SYNs to the real service port instead
sudo mtr -T -P 443 -rwzbc 100 app.example.com

# UDP mode (what traceroute uses by default on Linux)
sudo mtr -u -rwzbc 100 203.0.113.10

# Fewer, slower probes for long-term evidence (one per second for 10 minutes)
mtr -rwzbc 600 -i 1 203.0.113.10 > ~/mtr-$(date +%F-%H%M).txt
```

```
$ mtr -rwzbc 100 203.0.113.10
Start: 2026-10-03T10:12:01+0000
HOST: web01                                        Loss%   Snt   Last   Avg  Best  Wrst StDev
  1. AS???    _gateway (10.0.20.1)                  0.0%   100    0.4   0.5   0.3   1.2   0.1
  2. AS64500  198.51.100.1 (198.51.100.1)           0.0%   100    2.1   2.3   1.9   4.8   0.4
  3. AS64500  core1.isp.example (198.51.100.9)     42.0%   100    9.8  10.1   9.4  14.2   0.6
  4. AS64501  edge2.transit.example (203.0.113.1)   0.0%   100   38.4  38.9  38.1  45.0   0.9
  5. AS64501  203.0.113.10 (203.0.113.10)           0.0%   100   39.0  39.4  38.7  47.1   1.0
```

**What it means (path 1, healthy):**

- Hop 3 shows **42% loss**, but hops 4 and 5 show **0%**. That router simply rate-limits ICMP replies addressed *to itself* (control-plane policing). Packets forwarded *through* it are fine. **Ignore loss that does not carry through to the final hop.**
- Latency jumps from 10 ms (hop 3) to 38 ms (hop 4) and stays there → that is distance (a long-haul link between the two ASes), not a fault, as long as `StDev` stays small.
- `AS???` for your own private gateway is normal.

```
$ mtr -rwzbc 100 203.0.113.10
HOST: web01                                        Loss%   Snt   Last   Avg  Best  Wrst StDev
  1. AS???    _gateway (10.0.20.1)                  0.0%   100    0.4   0.5   0.3   1.1   0.1
  2. AS64500  198.51.100.1 (198.51.100.1)           0.0%   100    2.2   2.4   1.9   5.1   0.4
  3. AS64500  core1.isp.example (198.51.100.9)      6.0%   100   88.1  71.5   9.6 180.2  41.3
  4. AS64501  edge2.transit.example (203.0.113.1)   7.0%   100   95.4  79.9  38.2 191.0  40.8
  5. AS64501  203.0.113.10 (203.0.113.10)           6.0%   100   97.0  80.3  38.9 188.7  39.9
```

**What it means (path 2, real problem):**

- Loss **starts at hop 3 and persists** (6–7%) through the destination, and `Avg` jumps far above `Best` with a huge `StDev` from hop 3 onward → the link **between hop 2 and hop 3** (or hop 3 itself) is congested or faulty. That is real and it is where your ticket to the provider should point.
- The loss and jitter appear in AS64500 (your ISP), so the ISP owns it, not the transit provider or the destination.
- Small differences in loss between hops 3–5 (6%, 7%, 6%) are just sampling noise.

Rules for reading mtr that most people get wrong:

- Only loss that **continues to the last hop** matters. Loss at one middle hop that disappears afterwards is ICMP rate limiting.
- `???` or blank hops mean "this router does not answer probes". Fine, as long as later hops answer.
- Latency that rises at a hop and **stays** risen is added by that link. A spike at one hop that later hops do not show is the router being slow to answer, not the path.
- The return path can be **different** from the forward path (asymmetric routing). Ask someone at the far end, or use a host you control there, to run mtr back to you. Providers will ask for both directions.
- If the last hop shows loss but you know the host drops ICMP, repeat with `-T -P 443` to measure what TCP actually experiences.

**Why this step (now):** ping told you *that* there is loss or jitter; mtr tells you *where*, which decides who owns the fix (you, your ISP, a transit network, or the far end). It is still read-only and low-rate. Doing it before any tuning prevents you from "fixing" your server for a fault that lives three networks away.

**Next step:** if loss/jitter starts at hop 1 (your gateway) → Step 7 (local link) or section 11 (Wi-Fi). If it starts inside your own network (your firewall, your WAN link) → Step 10 (who is using the bandwidth) and Step 11 (shaping) on that device. If it starts in the ISP or beyond → collect mtr in both directions, open a ticket with the provider, and see Scenario A. If the path is clean (0% loss, stable latency) but transfers are still slow → Steps 4–6.

---

## 5. Core method: raw throughput with iperf3 (Steps 4–6)

> 📚 **Study path:** 1) Note: section 2 above (bandwidth-delay product) and [Learn: performance & observability](32-learn-performance-observability.md), section 7 (network deep dive, iperf3 baselines) · 2) KodeKloud: *Networks and Communications*, Network Troubleshooting module ([link](https://kodekloud.com/courses/networks-and-communications)); KodeKloud has no iperf3 lesson, so the handbook is the main source here · 3) Video: Brendan Gregg, *Linux Performance Tools, Brendan Gregg, part 1 of 2* ([link](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 4) Practice: the "Long fat pipe" and "Forgotten shaper" drills in section 22.

**Level:** [L2 · Mid]. Running iperf3 is easy. The L2 skill is reading
single vs parallel results, retransmits and UDP loss, and choosing the next layer
from them.

`curl` and `scp` measure the network **plus** disks, TLS, the application and the
far-end server. `iperf3` measures only the network and the two TCP stacks: memory
to memory, no disk, no app. If iperf3 is fast and your copy is slow, stop blaming
the network. If iperf3 is slow too, the network (or a NIC/stack) is guilty.

You need **two hosts you control**: one runs `iperf3 -s` (server), the other
`iperf3 -c` (client). By default the client sends and the server receives.

### Step 4 — Measure TCP throughput in both directions

**Goal:** get the single-stream TCP throughput from A to B and from B to A, and the retransmit count.

**On the server (B, 10.0.20.15):** open the port only for the client, and run a one-shot server.

```bash
# Ubuntu with UFW: allow only the test client, TCP and UDP (UDP is used in Step 6)
sudo ufw allow from 10.0.20.11 to any port 5201 proto tcp
sudo ufw allow from 10.0.20.11 to any port 5201 proto udp

# RHEL/Rocky with firewalld: runtime-only rule (gone at next reload/reboot);
# repeat with protocol=udp for the UDP test in Step 6
sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address=10.0.20.11 port port=5201 protocol=tcp accept'

# AWS: add a temporary security group rule for TCP/UDP 5201 from the client's IP

# Start a server that exits after ONE test (-1). Use -p to pick another port if
# 5201 is taken (see the ports playbook to find out who owns it).
iperf3 -s -1
```

```
-----------------------------------------------------------
Server listening on 5201 (test #1)
-----------------------------------------------------------
```

**On the client (A, 10.0.20.11):**

```bash
# A -> B: client sends (upload from A's point of view), 10 seconds
iperf3 -c 10.0.20.15 -t 10

# B -> A: reverse mode, the server sends (download from A's point of view)
iperf3 -c 10.0.20.15 -t 10 -R

# Both directions at the same time (iperf3 3.7+; Ubuntu 22.04 ships 3.9)
iperf3 -c 10.0.20.15 -t 10 --bidir

# Skip the first 2 s of TCP slow start in the summary (-O omit)
iperf3 -c 10.0.20.15 -t 15 -O 2

# Cap the rate when you only need to prove "at least 200 Mbit/s" on a busy link
iperf3 -c 10.0.20.15 -t 10 -b 200M
```

```
$ iperf3 -c 10.0.20.15 -t 10
Connecting to host 10.0.20.15, port 5201
[  5] local 10.0.20.11 port 50412 connected to 10.0.20.15 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec   112 MBytes   939 Mbits/sec    0    412 KBytes
[  5]   1.00-2.00   sec   112 MBytes   941 Mbits/sec    0    412 KBytes
[  5]   2.00-3.00   sec   112 MBytes   940 Mbits/sec    0    412 KBytes
...
[  5]   9.00-10.00  sec   112 MBytes   941 Mbits/sec    0    412 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  1.09 GBytes   940 Mbits/sec    0             sender
[  5]   0.00-10.00  sec  1.09 GBytes   937 Mbits/sec                  receiver

iperf Done.

$ iperf3 -c 10.0.20.15 -t 10 -R
Connecting to host 10.0.20.15, port 5201
Reverse mode, remote host 10.0.20.15 is sending
[  5] local 10.0.20.11 port 50418 connected to 10.0.20.15 port 5201
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  4.12 MBytes  34.6 Mbits/sec
[  5]   1.00-2.00   sec  3.88 MBytes  32.5 Mbits/sec
...
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  40.1 MBytes  33.6 Mbits/sec  2871             sender
[  5]   0.00-10.00  sec  39.8 MBytes  33.4 Mbits/sec                  receiver
```

**What it means:**

- **A → B: 940 Mbit/s, 0 retransmits, steady Cwnd** → perfect gigabit. Nothing to fix in that direction.
- **B → A: 33 Mbit/s with 2871 retransmits (Retr on the sender line)** → the path from B to A is losing packets. One direction clean and the other lossy is the classic signature of a **duplex mismatch** (one side full, the other half duplex) or a faulty transmit side on B (cable pair, SFP, NIC). Shaping on one direction would usually show few retransmits and a flat, round number instead.
- **sender vs receiver lines**: the receiver line is the truth (what arrived). A big gap between them means data was still in buffers at the end; run longer (`-t 30`).
- **Cwnd column** (client-as-sender only): a Cwnd that never grows, or keeps collapsing, means loss. A Cwnd that grows but bitrate stays low points at the receiver window (Step 8) or a shaper.
- **Interval lines**: steady per-second rates = stable path. A rate that swings wildly or drops to 0 for some seconds = loss bursts, a flapping link, or a policer.

| Result | Likely meaning | Go to |
|--------|----------------|-------|
| Near line rate both ways (940 Mbit/s on 1 GbE, 9.4 Gbit/s on 10 GbE) | The network between these hosts is fine | Look at disks, app, tool (Scenario B) |
| ~94 Mbit/s both ways, few retransmits | Something negotiated 100 Mbit/s | Step 7 |
| Good one way, poor with many retransmits the other way | Duplex mismatch, bad cable pair/SFP, one-way congestion | Step 7, Step 10 |
| Low, flat, suspiciously round number (100.0, 50.0) | Shaper or policer | Step 11, provider/cloud limits |
| Low with many retransmits both ways | Loss on the path | Step 3 (mtr), Step 7 |
| Low, zero retransmits, high RTT path | Window/BDP-limited single stream | Step 5, Step 8 |

**Why this step (now):** Steps 1–3 told you whether the path has latency or loss; this step tells you what that path can actually deliver, with disks and applications removed from the equation. Testing both directions separately is essential because the most common physical faults are one-directional.

**Next step:** if both directions are near line rate → the network is not the bottleneck; go to Scenario B (disk, tool, app) or Step 1 against the real service. If the result is ~94 Mbit/s or one-way bad with retransmits → Step 7. If low with zero retransmits on a high-RTT path → Step 5. If you see a flat round number → Step 11.

### Step 5 — Compare one stream with parallel streams

**Goal:** decide whether the limit is per flow (window, RTT, per-flow policing, one CPU core) or for the whole path.

```bash
# One stream (baseline)
iperf3 -c 203.0.113.50 -t 15 -O 2

# Eight parallel streams; look at the [SUM] line
iperf3 -c 203.0.113.50 -t 15 -O 2 -P 8

# Same test with a bigger socket buffer (window) for the single stream.
# -w sets SO_SNDBUF/SO_RCVBUF explicitly, which the kernel caps at
# net.core.wmem_max/rmem_max (212992 by default). Raise both TEMPORARILY on BOTH
# hosts first, or iperf3 aborts with "socket buffer size not set correctly".
# Restore 212992 afterwards (section 8's rollback).
sudo sysctl -w net.core.rmem_max=33554432 net.core.wmem_max=33554432
iperf3 -c 203.0.113.50 -t 15 -O 2 -w 16M

# Try a different congestion control for this test only. tcp_bbr must be loaded
# (sudo modprobe tcp_bbr), and a normal user may only pick algorithms listed in
# net.ipv4.tcp_allowed_congestion_control, so otherwise run this one with sudo.
iperf3 -c 203.0.113.50 -t 15 -O 2 -C bbr

# Machine-readable output for baselines and comparisons
iperf3 -c 203.0.113.50 -t 15 -O 2 -J > ~/iperf-$(date +%F-%H%M).json
```

```
$ iperf3 -c 203.0.113.50 -t 15 -O 2
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-15.00  sec   432 MBytes   241 Mbits/sec   12             sender
[  5]   0.00-15.04  sec   430 MBytes   240 Mbits/sec                  receiver

$ iperf3 -c 203.0.113.50 -t 15 -O 2 -P 8
...
[SUM]   0.00-15.00  sec  1.62 GBytes   928 Mbits/sec  103             sender
[SUM]   0.00-15.04  sec  1.61 GBytes   921 Mbits/sec                  receiver
```

**What it means:** one stream gets 240 Mbit/s, eight streams together get 921
Mbit/s. The path has the capacity; **a single flow cannot use it**. With 80 ms of
RTT, 240 Mbit/s means about 2.4 MB in flight (240 Mbit/s × 0.08 s ÷ 8), so the
window is the limit, not the wire.

| Single stream | Parallel `-P 8` | Interpretation |
|---------------|-----------------|----------------|
| Low | High (near line rate) | **Per-flow limit**: window too small for the BDP, a little loss amplified by RTT, a per-flow policer (common in clouds and some ISPs), or one CPU core (old iperf3) |
| Low | Also low | **Path limit**: capacity, congestion, shaping, or a lossy link affecting everything |
| High | High | No network problem between these hosts |
| `-w 16M` single stream jumps up | — | Buffers/autotuning limits: raise `tcp_rmem`/`tcp_wmem` maximums (section 8) |
| `-C bbr` jumps up, many retransmits with cubic | — | Random (non-congestion) loss on a long path; BBR on the **sending** servers helps |

Version note: iperf3 before **3.16** runs all `-P` streams in **one thread**, so
above roughly 10–20 Gbit/s a single CPU core becomes the limit. Ubuntu 24.04 ships
3.16 (multi-threaded); Ubuntu 22.04 ships 3.9. On older versions, run several
iperf3 server/client pairs on different ports (`-p 5201`, `-p 5202`, …) and add the
results.

**Why this step (now):** it is the cleanest experiment to separate "the pipe is too small" from "one TCP connection cannot fill the pipe". These have completely different fixes (buy/fix capacity vs tune windows, use parallel transfers, fix loss), so you must know which one you have before touching anything.

**Next step:** if single is low and parallel is high → Step 8 (TCP health and buffers) and section 8 (tuning), and consider parallel transfer tools for the users. If both are low → Step 6 (UDP: is it loss or a rate limit?) then Step 10 and Step 11. If `-w` fixed it → section 8.

### Step 6 — Measure loss and jitter at a fixed rate with UDP

**Goal:** send at a known rate with no congestion control in the way, and see exactly how much is lost and how much the delay varies.

```bash
# UDP needs an explicit rate; the default is only 1 Mbit/s
iperf3 -c 10.0.20.15 -u -b 100M -t 10

# Step the rate up to find where loss begins (the effective capacity or policer)
for r in 100M 300M 500M 700M 900M; do
  echo "== $r"; iperf3 -c 10.0.20.15 -u -b $r -t 5 | grep -E 'receiver'
done

# Reverse direction (server sends UDP to you)
iperf3 -c 10.0.20.15 -u -b 500M -t 10 -R
```

```
$ iperf3 -c 10.0.20.15 -u -b 500M -t 10
Connecting to host 10.0.20.15, port 5201
[  5] local 10.0.20.11 port 43817 connected to 10.0.20.15 port 5201
[ ID] Interval           Transfer     Bitrate         Total Datagrams
[  5]   0.00-1.00   sec  59.6 MBytes   500 Mbits/sec  43166
...
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-10.00  sec   596 MBytes   500 Mbits/sec  0.000 ms  0/431654 (0%)  sender
[  5]   0.00-10.00  sec   583 MBytes   489 Mbits/sec  0.052 ms  9310/431654 (2.2%)  receiver
```

**What it means:**

- The **receiver** line is the one to read: 2.2% of datagrams were lost at 500 Mbit/s, jitter 0.052 ms.
- **Loss at a rate well below the link speed** (2.2% at 500 Mbit/s on a gigabit path) → real loss: a faulty link, congestion from other traffic, or a policer set near that rate. With the stepping loop you will typically see 0% up to some rate and then loss climbing quickly; that knee is the effective capacity or the policer's rate.
- **Loss that also appears at low rates** (even 10–50 Mbit/s) → a physical problem (errors), not congestion → Step 7.
- **Jitter**: under 1 ms on a LAN is normal; several ms on a WAN is normal; tens of ms means queues are building (congestion, bufferbloat, Wi-Fi).
- On fast links (multi-gigabit), UDP loss can come from the **receiving host** being unable to keep up (socket buffer overflows). Check the receiver with `nstat -az UdpRcvbufErrors` before blaming the network.

> ⚠️ UDP has no congestion control: `-b 900M` really pushes 900 Mbit/s whether or
> not anyone else needs the link. Keep tests short and rates sane on shared paths.

**Why this step (now):** TCP hides loss behind retransmissions and backs off, so a slow TCP result does not tell you *how much* loss there is or at what rate it starts. UDP at a fixed rate measures the path itself, which is exactly the evidence a provider or network team needs.

**Next step:** if loss appears even at low rates → Step 7 (errors on the link). If loss starts at a precise rate → Step 11 (shaping/policing), then the provider or cloud limits (section 9). If UDP is clean at full rate but TCP is slow → the problem is in the TCP stacks or windows → Step 8. **Clean up**: stop the server (it exits by itself with `-1`) and remove the firewall rules:

```bash
# UFW: delete the exact rules you added
sudo ufw delete allow from 10.0.20.11 to any port 5201 proto tcp
sudo ufw delete allow from 10.0.20.11 to any port 5201 proto udp
# firewalld: remove the exact runtime rule (a --reload also drops all runtime rules)
sudo firewall-cmd --remove-rich-rule='rule family=ipv4 source address=10.0.20.11 port port=5201 protocol=tcp accept'
# AWS: delete the temporary security group rule
```

---

## 6. Core method: this host's link, TCP and MTU (Steps 7–9)

> 📚 **Study path:** 1) Note: [Network reference](02-network.md), sections 2 (interfaces, links) and 3 (ports and sockets, `ss`) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*, Networking section ([link](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) before the MTU capture in Step 9 · 4) Practice: the "Lossy link" and "MTU black hole" drills in section 22.

**Level:** [L2 · Mid]. Reading `ethtool`, `ss -ti` and a DF ping bisect is
core L2 work. Fixing duplex on switches and MTU on tunnels usually involves the
network team, which a senior coordinates.

If Steps 2–6 pointed at the first hop, at one host, or at one direction, the fault
is often physical or in the host's own TCP stack. These steps are read-only
except where a change is explicitly marked.

### Step 7 — Check link speed, duplex and NIC counters

**Goal:** prove the physical link negotiated the right speed and duplex, and that the NIC is not counting errors or drops.

```bash
IFACE=eno1                         # the interface Step 0 showed (ip route get)

# Negotiated speed, duplex, autonegotiation, link state
sudo ethtool $IFACE

# Driver and firmware (needed for vendor known-issue searches)
sudo ethtool -i $IFACE

# Kernel counters, with the detailed error breakdown (-s -s)
ip -s -s link show $IFACE

# NIC hardware counters: show only the non-zero error/drop ones
sudo ethtool -S $IFACE | grep -Ei 'err|drop|crc|miss|fifo|collision|discard|no_buffer|timeout' | grep -v ': 0$'

# Counters are cumulative since boot: watch them change while you reproduce
watch -d -n 2 "ip -s link show $IFACE"

# Ring buffer sizes and number of queues (channels)
sudo ethtool -g $IFACE
sudo ethtool -l $IFACE

# Fibre/SFP: optical power and temperature (only for modules that support DOM)
sudo ethtool -m $IFACE

# Kernel log: link flaps, renegotiation, NIC hangs and resets
sudo journalctl -k --since '24 hours ago' | grep -Ei "$IFACE|link is (up|down)|tx timeout|hang|reset"
```

```
$ sudo ethtool eno1
Settings for eno1:
	Supported ports: [ TP ]
	Supported link modes:   10baseT/Half 10baseT/Full
	                        100baseT/Half 100baseT/Full
	                        1000baseT/Full
	Supports auto-negotiation: Yes
	Advertised link modes:  10baseT/Half 10baseT/Full
	                        100baseT/Half 100baseT/Full
	                        1000baseT/Full
	Advertised auto-negotiation: Yes
	Link partner advertised link modes:  Not reported
	Speed: 100Mb/s
	Duplex: Half
	Auto-negotiation: on
	Port: Twisted Pair
	Link detected: yes

$ ip -s -s link show eno1
2: eno1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 3c:ec:ef:12:34:56 brd ff:ff:ff:ff:ff:ff
    RX:  bytes packets errors dropped  missed   mcast
    9831245113 9123441  18342       0       0   20412
    RX errors:  length    crc   frame    fifo overrun
                     0  18342       0       0       0
    TX:  bytes packets errors dropped carrier collsns
    4432115098 6234112      0       0       0   91234
    TX errors: aborted   fifo  window heartbt transns
                     0      0    1873       0       2

$ sudo ethtool -S eno1 | grep -Ei 'err|drop|crc|miss|fifo|collision' | grep -v ': 0$'
     rx_errors: 18342
     rx_crc_errors: 18342
     collisions: 91234
     tx_window_errors: 1873

$ sudo journalctl -k --since '24 hours ago' | grep -Ei 'eno1|link is'
Oct 03 08:14:02 web01 kernel: igb 0000:03:00.0 eno1: igb: eno1 NIC Link is Down
Oct 03 08:14:05 web01 kernel: igb 0000:03:00.0 eno1: igb: eno1 NIC Link is Up 100 Mbps Half Duplex, Flow Control: None
```

**What it means:**

- **`Speed: 100Mb/s` on a gigabit NIC** → this link will never exceed ~94 Mbit/s (~11.5 MB/s). Gigabit Ethernet needs **all four wire pairs**; 100 Mbit/s needs only two, so a cable with one broken pair, a bad patch panel port or a cheap two-pair cable silently falls back to 100 Mbit/s.
- **`Duplex: Half` with `Auto-negotiation: on`** → the switch port is probably **forced** to 100/Full while this side autonegotiates. Autonegotiation then cannot see the partner's capabilities and falls back to half duplex. This is the textbook **duplex mismatch**.
- **`Link partner advertised link modes: Not reported`** supports that: the other side is not advertising, i.e. it is hard-set.
- **CRC errors** on RX → frames arrived corrupted: bad cable, bad SFP/transceiver, electrical interference, or the far side of a duplex mismatch.
- **Collisions, late collisions, `tx_window_errors`** on a modern switched network → the half-duplex side of a mismatch. On full duplex these counters must be zero.
- **Link Down/Up in the kernel log** → a flapping link (loose cable, failing port, power saving). Each flap costs seconds of outage plus retransmits.
- **RX `missed`, `fifo`, `overrun`, or driver counters such as `rx_missed_errors`, `rx_no_buffer_count`** → the NIC received the frame but the host did not empty the ring buffer fast enough: ring too small or a CPU/softirq bottleneck (Step 13).
- **RX `dropped`** in `ip -s link` → dropped by the kernel after the NIC (unknown protocol, VLAN not configured, `rp_filter`, socket backlog). A slowly rising `dropped` with nothing else is often harmless broadcast/multicast noise; compare the rate against total packets.

Healthy looks like: expected speed (`1000Mb/s`, `10000Mb/s`), `Duplex: Full`, all error counters 0 (or not increasing while you watch), and no link flaps in the log.

| Duplex-mismatch symptom | Why it happens |
|-------------------------|----------------|
| Ping looks perfect, bulk transfers crawl | Ping is tiny and rarely collides; bulk traffic collides constantly |
| One direction much worse than the other | The half-duplex side backs off; the full-duplex side keeps sending |
| CRC/FCS errors on the full-duplex side, late collisions on the half side | Frames are cut off mid-transmission |
| Speed gets *worse* the more load you add | More traffic means more collisions |

Ring buffers, when `missed`/`no_buffer` counters climb:

```
$ sudo ethtool -g eno1
Ring parameters for eno1:
Pre-set maximums:
RX:		4096
RX Mini:	n/a
RX Jumbo:	n/a
TX:		4096
Current hardware settings:
RX:		256
RX Mini:	n/a
RX Jumbo:	n/a
TX:		256
```

→ Current RX ring 256 of a possible 4096. During bursts the NIC overflows the ring
and drops. Raising it (`sudo ethtool -G eno1 rx 4096 tx 4096`) gives more slack.

> ⚠️ `ethtool -G` (rings), `ethtool -L` (channels) and `ethtool -s` (speed/duplex)
> **reset the NIC on most drivers**: the link goes down for a second or more. On a
> remote server that can drop your SSH session or trigger failover. Do it in a
> maintenance window, from a console (iDRAC/iLO/IPMI, hypervisor console, AWS
> Serial Console), never on the only path you are logged in through without a
> fallback.

Virtual machines: `virtio_net`, `vmxnet3` and AWS `ena` report a nominal speed (or
`Speed: Unknown!`) that means nothing; cables and CRC errors live on the
hypervisor host and the physical switch. Inside a VM, focus on drops, ring/queue
counters and the driver type. An emulated **`e1000`** NIC instead of
`virtio_net`/`vmxnet3` is itself a performance bug (Scenario F).

**Why this step (now):** the physical layer is the foundation every other number sits on, and its faults (100 Mbit/s fallback, duplex mismatch, dirty fibre) produce exactly the confusing "ping fine, transfers slow, one direction worse" picture. It is read-only, takes a minute, and if it is broken nothing else is worth tuning.

**Next step:** if speed/duplex is wrong → fix both ends to **autonegotiate** (or both forced identically, if your network team insists), replace the cable or SFP, then repeat Step 4. If CRC errors rise → swap cable, then patch port, then switch port, then SFP, re-checking counters after each swap. If ring/missed drops rise → Step 13 (CPU/IRQ) and consider larger rings. If everything is clean → Step 8.

Fix commands for reference (RHEL equivalents use `nmcli`):

```bash
# Re-enable autonegotiation on this side (resets the link, see warning above)
sudo ethtool -s eno1 autoneg on

# Bigger rings (resets the link). Persist on Ubuntu with a networkd-dispatcher hook:
sudo ethtool -G eno1 rx 4096 tx 4096
sudo tee /etc/networkd-dispatcher/routable.d/50-eno1-rings >/dev/null <<'EOF'
#!/bin/sh
[ "$IFACE" = "eno1" ] && /usr/sbin/ethtool -G eno1 rx 4096 tx 4096
exit 0
EOF
sudo chmod 755 /etc/networkd-dispatcher/routable.d/50-eno1-rings

# RHEL/Rocky (NetworkManager): persistent ring sizes and autonegotiation
sudo nmcli connection modify eno1 ethtool.ring-rx 4096 ethtool.ring-tx 4096
sudo nmcli connection modify eno1 802-3-ethernet.auto-negotiate yes
```

### Step 8 — Read the TCP state of the slow connection

**Goal:** look inside the actual slow TCP connection (RTT, congestion window, retransmits, what limits it) and at host-wide retransmit rates.

```bash
# Per-connection internals for connections to one peer (run DURING the slow transfer)
ss -tin dst 203.0.113.10

# All established connections on port 443 with process names (root for -p)
sudo ss -tinp state established '( sport = :443 or dport = :443 )'

# Host-wide TCP counters: measure the DELTA over 60 s while the problem happens
nstat -n                         # reset nstat's history, prints nothing
sleep 60
nstat TcpOutSegs TcpRetransSegs TcpExtTCPTimeouts TcpExtTCPSynRetrans \
      TcpExtTCPLossProbes TcpExtListenOverflows TcpExtListenDrops

# Absolute counters since boot (-a), including zeros (-z)
nstat -az TcpRetransSegs TcpOutSegs

# The same with legacy net-tools
netstat -s | grep -Ei 'retrans|timeout|overflow|listen'

# Listening sockets: is the accept queue full? (Recv-Q = waiting, Send-Q = backlog)
ss -ltn 'sport = :443'

# Congestion control, qdisc, and buffer limits
sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_available_congestion_control net.core.default_qdisc
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.core.rmem_max net.core.wmem_max
sysctl net.ipv4.tcp_window_scaling net.ipv4.tcp_sack net.ipv4.tcp_timestamps net.ipv4.tcp_mtu_probing
```

```
$ ss -tin dst 203.0.113.10
State  Recv-Q Send-Q    Local Address:Port    Peer Address:Port
ESTAB  0      2304000   10.0.20.11:41822      203.0.113.10:443
	 cubic wscale:7,7 rto:452 rtt:248.512/12.4 ato:40 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:10 ssthresh:7 bytes_sent:48211234 bytes_retrans:1842211 bytes_acked:46113245 segs_out:33310 segs_in:15022 data_segs_out:33301 send 466Kbps lastsnd:8 lastrcv:12 lastack:8 pacing_rate 932Kbps delivery_rate 1.2Mbps delivered:31873 busy:182340ms sndbuf_limited:5300ms(2.9%) unacked:42 retrans:1/1268 lost:12 sacked:28 reordering:3 rcv_space:14480 rcv_ssthresh:64088 minrtt:238.2
```

**What it means:** this one line is a full health report of the connection.

| Field | Value here | How to read it |
|-------|-----------|----------------|
| `cubic` | congestion control | `bbr` would show `bbr` plus its own model fields |
| `rtt:248.5/12.4` | smoothed RTT / RTT variation (ms) | Compare with `minrtt`; far above it = queueing |
| `minrtt:238.2` | lowest RTT seen | The physical path RTT: this is a long-distance path |
| `cwnd:10` | congestion window (segments) | Tiny: 10 × 1448 B = 14 KB in flight. Loss keeps knocking it down |
| `ssthresh:7` | slow-start threshold | Low = there have been loss events |
| `retrans:1/1268`, `bytes_retrans` | now / total retransmits | 1.8 MB of 48 MB retransmitted ≈ **3.8% loss** |
| `send 466Kbps` | cwnd × mss / rtt | The ceiling TCP allows itself right now |
| `delivery_rate 1.2Mbps` | measured rate | What is actually getting through |
| `rwnd_limited:` | time limited by receiver window | High % = the **receiver** cannot take more (its buffers or app) |
| `sndbuf_limited:5300ms(2.9%)` | time limited by send buffer | High % = the **sender's** socket buffer or app is the limit |
| `Send-Q 2304000` | bytes queued to send | The app wants to send more than TCP can push |
| `pmtu:1500`, `mss:1448` | path MTU / segment size | Smaller than expected = PMTU discovery reduced it (Step 9) |

→ Verdict: a 240 ms path with ~4% loss. Cubic keeps cutting cwnd, so the
connection crawls at ~0.5–1 Mbit/s. The fix is to remove the loss (Step 3 says
where), or use BBR on the **sending** side (section 8), not bigger buffers.

How the "what limits it" fields map to fixes:

- `rwnd_limited` high → the receiver's window is too small: raise `tcp_rmem` max on the **receiver**, or the receiving app reads too slowly (CPU, disk). An app that sets `SO_RCVBUF` itself turns off autotuning and is capped by `net.core.rmem_max`.
- `sndbuf_limited` high → raise `tcp_wmem` max on the **sender**, or the sending app sets a small `SO_SNDBUF`.
- `cwnd` small, `retrans` climbing → **loss** on the path; buffers will not help.
- `cwnd` large, no retrans, still slow, `rtt` ≫ `minrtt` → a queue on the path is full (bufferbloat, shaper).
- Neither limited, cwnd fine, Send-Q 0 → the application is not producing data fast enough. Not a network problem.

```
$ nstat -n; sleep 60; nstat TcpOutSegs TcpRetransSegs TcpExtTCPTimeouts TcpExtTCPSynRetrans TcpExtListenOverflows TcpExtListenDrops
#kernel
TcpOutSegs                      4123110            0.0
TcpRetransSegs                  98211              0.0
TcpExtTCPTimeouts               412                0.0
TcpExtTCPSynRetrans             37                 0.0
TcpExtListenOverflows           1840               0.0
TcpExtListenDrops               1840               0.0
```

- **Retransmit rate** = `TcpRetransSegs / TcpOutSegs` = 98211 / 4123110 ≈ **2.4%**. Rough guide: under 0.1% healthy on a LAN, up to ~0.5% acceptable on the internet, above 1% hurts, above 2–3% is a fault to chase.
- `TcpExtTCPTimeouts` → retransmission *timeouts* (the slow kind, after a full RTO with no ACKs): severe loss or a black hole.
- `TcpExtTCPSynRetrans` → connection attempts that needed a second SYN: explains `connect` times of 1 s / 3 s in Step 1.
- **`TcpExtListenOverflows` / `ListenDrops`** → *this* server's accept queue was full, so the kernel dropped incoming SYNs. Clients see 1 s or 3 s connect delays that look exactly like network loss. The cause is the app not calling `accept()` fast enough (overloaded, too few workers) or a small backlog (`net.core.somaxconn`, the app's listen backlog). Confirm with `ss -ltn`: `Recv-Q` reaching `Send-Q` on the listening socket.

```
$ sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_available_congestion_control net.core.default_qdisc
net.ipv4.tcp_congestion_control = cubic
net.ipv4.tcp_available_congestion_control = reno cubic
net.core.default_qdisc = fq_codel

$ sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem net.core.rmem_max net.core.wmem_max
net.ipv4.tcp_rmem = 4096	131072	6291456
net.ipv4.tcp_wmem = 4096	16384	4194304
net.core.rmem_max = 212992
net.core.wmem_max = 212992
```

- `cubic` and `fq_codel` are the Ubuntu defaults. `bbr` is not in the available list until `tcp_bbr` is loaded (section 8).
- `tcp_rmem` / `tcp_wmem` are min / default / **max** bytes for autotuned sockets. A 6 MB receive max is enough for ~1 Gbit/s up to roughly 25–45 ms RTT (part of the buffer is overhead, not window). Longer or faster paths need more.
- `net.core.rmem_max` / `wmem_max` (≈208 KB) only cap applications that set their buffer sizes explicitly. They do not limit autotuning.
- `tcp_window_scaling`, `tcp_sack`, `tcp_timestamps` must be `1`. Someone disabling them "for security" limits every stream to a 64 KB window and makes loss recovery slow.

**Why this step (now):** iperf3 told you *that* throughput is low; `ss -ti` tells you *why* for a real connection: loss, receiver window, sender buffer or an app that is not sending. It turns "tune something" into a specific, justified change. Measuring retransmit deltas host-wide also catches problems that only show under real traffic.

**Next step:** if retransmits/loss are high → go back to Step 3 (where) and Step 7 (local link); then section 8 for BBR on senders. If `rwnd_limited`/`sndbuf_limited` dominate or `-w 16M` helped in Step 5 → section 8 (buffers). If `ListenOverflows` rise → the server application is overloaded, see [Why is the system slow?](23-playbook-slow-system.md). If `pmtu`/`mss` is smaller than expected or transfers stall rather than crawl → Step 9. If TCP looks healthy → Step 10 (competition) and Step 11 (shaping).

### Step 9 — Test for MTU and PMTUD black holes

**Goal:** find the largest packet that crosses the path unfragmented, and prove whether large packets are silently dropped.

The **MTU** is the largest IP packet a link carries (1500 bytes on standard
Ethernet). Tunnels and overlays wrap packets in extra headers, so their inner MTU
is smaller. TCP normally adapts through **Path MTU Discovery**: a router that
cannot forward a too-big packet with the "Don't Fragment" bit set sends back ICMP
"fragmentation needed" (IPv4, type 3 code 4) or "packet too big" (ICMPv6 type 2),
and the sender shrinks. When a firewall **blocks those ICMP messages**, large
packets vanish without any error: a **PMTUD black hole**.

Classic black-hole symptoms:

- SSH login works, but `scp`, `rsync`, `git clone`, `docker pull` or `apt` stall (often at 0% or after the first chunk).
- Small web pages load, large pages or big API responses hang.
- `curl -v` hangs right after `Client hello` (the server's certificate chain is a large packet).
- Ping works, `ping -s 1472` does not.
- Problems began after a VPN, overlay network, PPPoE line or new firewall was added.

```bash
# Interface MTUs (look at every interface in the path: eno1, wg0, docker0, br-*, flannel.1, cali*)
ip -br link
ip -o link show | awk '{print $2, $4, $5}'

# IPv4: payload + 28 bytes (20 IP + 8 ICMP) = packet size. 1472 -> 1500-byte packet
ping -c 3 -M do -s 1472 203.0.113.10
ping -c 3 -M do -s 1372 203.0.113.10

# IPv6: payload + 48 bytes (40 IPv6 + 8 ICMPv6). 1452 -> 1500-byte packet
ping -6 -c 3 -M do -s 1452 2001:db8:10::20

# Bisect the path MTU automatically
for s in 1472 1452 1432 1412 1392 1372 1352 1332; do
  if ping -c 1 -W 1 -M do -s $s 203.0.113.10 >/dev/null 2>&1; then
    echo "OK   payload $s -> packet $((s+28))"
  else
    echo "FAIL payload $s -> packet $((s+28))"
  fi
done

# Hop-by-hop path MTU discovery, no root needed
tracepath -n 203.0.113.10

# Has the kernel already learned a smaller PMTU for this destination?
ip route get 203.0.113.10

# Are "fragmentation needed" / "packet too big" messages arriving at all?
sudo tcpdump -ni any '(icmp[icmptype] == 3 and icmp[icmpcode] == 4) or (icmp6 and ip6[40] == 2)'
```

```
$ ping -c 3 -M do -s 1472 203.0.113.10
PING 203.0.113.10 (203.0.113.10) 1472(1500) bytes of data.

--- 203.0.113.10 ping statistics ---
3 packets transmitted, 0 received, 100% packet loss, time 2041ms

$ ping -c 3 -M do -s 1372 203.0.113.10
PING 203.0.113.10 (203.0.113.10) 1372(1400) bytes of data.
1380 bytes from 203.0.113.10: icmp_seq=1 ttl=53 time=42.3 ms
1380 bytes from 203.0.113.10: icmp_seq=2 ttl=53 time=42.1 ms
1380 bytes from 203.0.113.10: icmp_seq=3 ttl=53 time=42.6 ms

$ for s in ...; do ...; done
FAIL payload 1472 -> packet 1500
FAIL payload 1452 -> packet 1480
FAIL payload 1432 -> packet 1460
FAIL payload 1412 -> packet 1440
OK   payload 1392 -> packet 1420
OK   payload 1372 -> packet 1400
...

$ tracepath -n 203.0.113.10
 1?: [LOCALHOST]                      pmtu 1500
 1:  10.0.20.1                                             0.512ms
 1:  10.0.20.1                                             0.431ms
 2:  198.51.100.1                                          2.214ms
 3:  198.51.100.9                                          9.876ms
 4:  no reply
 5:  203.0.113.10                                         42.551ms reached
     Resume: pmtu 1500 hops 5 back 5
```

**What it means:**

- **1500-byte packets: 100% loss, no error message at all**. 1400 works. → Something on the path has an MTU between **1420 and 1439** (the bisect boundary; refine with 1-byte steps if you need the exact value, and 1420 is WireGuard's default), and the ICMP that should say so never reaches you. That is a **black hole**.
- If instead you see `From 10.8.0.1 icmp_seq=1 Frag needed and DF set (mtu = 1420)`, PMTUD *works*: a router told you its MTU. Applications should cope; if they do not, look for something stripping the DF bit or a UDP application that ignores PMTU.
- `ping: local error: message too long, mtu=1420` → the limit is **your own interface** (for example `wg0` with MTU 1420). That is expected for traffic through a tunnel; send smaller.
- `tracepath` reports `pmtu 1500` all the way although 1500 is dropped → tracepath relies on the same ICMP that is being filtered, so it cannot see the black hole. Trust the DF ping bisect.
- `ip route get` showing `cache expires 587sec mtu 1420` → the kernel learned a smaller PMTU from an ICMP message for that destination (good: PMTUD worked at least once).
- `tcpdump` showing **nothing** while a large transfer stalls (and `ss -ti` shows retransmits of full-size segments) → the "too big" messages are being dropped somewhere.

Encapsulation overhead and the MTU each layer should use:

| Path element | Overhead (bytes) | Inner MTU on a 1500 underlay |
|--------------|------------------|------------------------------|
| PPPoE (DSL / some fibre broadband) | 8 | 1492 |
| GRE tunnel | 24 | 1476 |
| IP-in-IP (Calico IPIP mode) | 20 | 1480 |
| VXLAN (Docker Swarm overlay, Flannel, Calico VXLAN) | 50 | 1450 |
| WireGuard (IPv4 outer 60, IPv6 outer 80) | 60–80 | 1420 (default, safe for both) |
| IPsec ESP tunnel mode | ~50–73, cipher dependent | ~1400–1438 (1400 is a common safe value) |
| OpenVPN over UDP | ~40–70, cipher dependent | ~1400–1450 |
| Tunnel inside a tunnel (overlay over WireGuard, VPN over PPPoE) | sum of both | e.g. 1420 − 50 = **1370** |

Common real-world traps in your stack:

- **Docker on a host whose own MTU is below 1500** (a VM on an OpenStack VXLAN network at 1450, GCP at 1460, a host reached through WireGuard): Docker bridges default to 1500 regardless of the host, so containers send packets that cannot leave. Set the MTU for Docker networks (section 10).
- **Docker-in-Docker in GitLab CI**: the inner `dockerd` creates 1500-byte networks inside a container whose network may be 1450. Builds hang on `apt-get` or `docker pull`. Start the `docker:dind` service with `--mtu=1450` (or your real value).
- **Swarm overlay (Dokploy's `dokploy-network`)** uses MTU 1450 (1500 minus 50 for VXLAN) whatever the host's real MTU is. **Kubernetes VXLAN CNIs** (Flannel, Calico) usually derive their MTU from the node interface they detect, minus the overhead, but only if they pick the right interface. If the *underlay* between nodes is smaller than 1500 (nodes linked over WireGuard or IPsec), set the overlay or CNI MTU by hand and check the result with a DF ping.
- **Firewalls that "block all ICMP"** break PMTUD. Never drop ICMP type 3 (destination unreachable, especially code 4) or ICMPv6 type 2 (packet too big). AWS security groups need an explicit inbound rule for "Destination Unreachable: fragmentation needed" for PMTUD to work (section 9).

**Why this step (now):** MTU problems do not look like slowness on graphs; they look like hangs, and every other test (ping with small packets, DNS, TCP handshake) passes. A DF ping bisect proves or kills the hypothesis in one minute, without changing anything, so it is worth running whenever "small works, big hangs" appears.

**Next step:** if a black hole is confirmed → choose a fix: allow ICMP "fragmentation needed"/"packet too big" through the firewall that drops it (the real fix), **clamp TCP MSS** on the router/tunnel endpoint, or lower the MTU on the tunnel or interface (section 8 and Scenario D). If MTU is fine end to end → Step 10.

---

## 7. Core method: contention and limits (Steps 10–14)

> 📚 **Study path:** 1) Note: [Network reference](02-network.md), section 7 (connection tracking and kernel limits), and [DNS reference](08-dns.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs*, IPTABLES Introduction lesson ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)), then *Demystifying DNS*, Troubleshooting DNS lesson ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page)) · 3) Read: [Arch Wiki: systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved) · 4) Practice: the "Conntrack full", "Forgotten shaper" and "Slow DNS" drills in section 22.

**Level:** [L2–L3 · Mid → Senior]. Steps 10, 11 and 14 are L2. Conntrack sizing,
IRQ and queue tuning (Steps 12–13) change kernel and NIC settings on shared
hosts, which is L3 work.

The link is healthy and TCP looks sane, yet it is still slow. Now look for
something *competing* for the path, something *deliberately limiting* it, or the
host's own kernel running out of a resource.

### Step 10 — Find who is using the bandwidth

**Goal:** identify which connections, processes and times of day consume the link, now and in the past.

```bash
# Live, per connection: -n no DNS, -N no port names, -P show ports
sudo iftop -i eno1 -nNP
# Text mode for tickets: one 10-second sample, printed and exit
sudo iftop -i eno1 -nNP -t -s 10

# Live, per PROCESS (which program is downloading?)
sudo nethogs eno1

# Simple live in/out graph, and a richer per-interface monitor
nload eno1
bmon -p eno1

# History (needs the vnstat daemon running beforehand: sudo systemctl enable --now vnstat)
vnstat -i eno1 -5        # 5-minute buckets
vnstat -i eno1 -h        # hourly
vnstat -i eno1 -d        # daily

# History from sysstat (Ubuntu: /var/log/sysstat/saDD, RHEL: /var/log/sa/saDD).
# On Ubuntu, collection only runs if /etc/default/sysstat says ENABLED="true"
# (check it now: grep ENABLED /etc/default/sysstat), then: sudo systemctl enable --now sysstat
sar -n DEV 1 5                                         # live, 1 s x 5
sar -n DEV -f /var/log/sysstat/sa03 -s 01:50:00 -e 02:20:00
sar -n EDEV -f /var/log/sysstat/sa03                   # interface errors over time
sar -n TCP,ETCP 1 5                                    # TCP retransmits per second

# Connections with the most unsent data queued (Send-Q is column 2 with a state filter)
sudo ss -tnp state established | sort -k2,2nr | head

# Which peers hold the most connections?
ss -tn state established | awk 'NR>1 {sub(/:[0-9]+$/,"",$4); print $4}' | sort | uniq -c | sort -nr | head
```

```
$ sudo iftop -i eno1 -nNP -t -s 10
interface: eno1
IP address is: 10.0.20.11
   # Host name (port/service if enabled)            last 2s   last 10s   last 40s cumulative
--------------------------------------------------------------------------------------------
   1 10.0.20.11:443                           =>      812Mb      790Mb      790Mb      987MB
     198.51.100.77:60412                      <=     9.11Mb     8.80Mb     8.80Mb     11.0MB
   2 10.0.20.11:22                            =>     1.21Mb     1.18Mb     1.18Mb     1.47MB
     10.0.30.44:51544                         <=     21.8Kb     20.9Kb     20.9Kb     26.1KB
--------------------------------------------------------------------------------------------
Total send rate:                                       813Mb      791Mb      791Mb
Total receive rate:                                   9.13Mb     8.82Mb     8.82Mb
--------------------------------------------------------------------------------------------

$ sudo nethogs eno1
NetHogs version 0.8.7

    PID USER     PROGRAM                      DEV        SENT      RECEIVED
  23411 backup   /usr/bin/rsync               eno1    612.443   52311.208 KB/sec
   1891 _apt     /usr/lib/apt/methods/http    eno1     88.112    4122.904 KB/sec
   2210 deploy   sshd: deploy@pts/0           eno1      1.204       0.402 KB/sec
      ? root     unknown TCP                            0.000       0.000 KB/sec

  TOTAL                                               701.759   56434.514 KB/sec

$ vnstat -i eno1 -5
 eno1  /  5 minute

        time        rx      |     tx      |    total    |   avg. rate
     ------------------------+-------------+-------------+---------------
     2026-10-03
         01:55    210.12 MiB |   14.20 MiB |  224.32 MiB |    6.27 Mbit/s
         02:00     32.41 GiB |  301.10 MiB |   32.71 GiB |  936.55 Mbit/s
         02:05     32.38 GiB |  298.77 MiB |   32.67 GiB |  935.40 Mbit/s
         02:10    198.40 MiB |   13.95 MiB |  212.35 MiB |    5.94 Mbit/s

$ sar -n DEV -f /var/log/sysstat/sa03 -s 01:50:00 -e 02:20:00 | grep -E 'IFACE|eno1'
01:50:01        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
02:00:01         eno1   1023.40    612.10    812.33     95.12      0.00      0.00      0.40      0.67
02:10:01         eno1  81234.11  42113.90 114320.33   3120.45      0.00      0.00      1.20     93.65
02:20:01         eno1   1101.22    640.80    901.12    101.44      0.00      0.00      0.38      0.74
```

**What it means:**

- `iftop`: one connection from port 443 to 198.51.100.77 is sending ~800 Mbit/s: one client is downloading something huge from your web server and filling the gigabit uplink. Everyone else's traffic now queues behind it.
- `nethogs`: an `rsync` run by the `backup` user is *receiving* ~52 MB/s (≈420 Mbit/s) and `apt` another ~4 MB/s. Now you know which program, which user, and therefore which team or cron job.
- `vnstat -5` / `sar`: between 02:00 and 02:10 the interface ran at ~936 Mbit/s (`%ifutil` 93.65): the link was **saturated**. If users complain "every night around 2 am", this is your answer: a scheduled job.
- Traffic from containers on Docker bridges is NATed, so `nethogs` often shows it as `unknown TCP`. Run `iftop -i docker0` or `-i br-XXXX` (the bridge of that network) to see container IPs, then map IPs to containers with `docker network inspect`.

**Why this step (now):** a link that is full is slow for everyone, and no amount of tuning fixes contention. Before you suspect shaping or kernel limits, prove the link is not simply busy, and find out who is using it. History (`vnstat`, `sar`) matters as much as the live view, because the problem is often gone by the time you log in.

**Next step:** if a single job or client saturates the link → schedule it off-peak, rate-limit it (`rsync --bwlimit=50M`, `scp -l KBIT`, `curl --limit-rate`), give it its own link/VLAN, or add QoS (Step 11 shows how shaping looks). If the link is not near capacity but traffic is still slow → Step 11. If you have no history at all → set up `vnstat`/`sysstat` now and prometheus `node_exporter` (section 21) so the next occurrence is recorded.

### Step 11 — Look for shaping and policing

**Goal:** detect deliberate rate limits on this host (tc qdiscs, classes, filters) and recognise the signature of limits upstream.

```bash
# Queueing disciplines on every interface: look for tbf, htb, cake, netem, ingress
tc qdisc show

# One interface, with statistics (sent, dropped, overlimits, backlog)
tc -s qdisc show dev eno1

# Classes and filters (HTB shaping trees, ingress policers)
tc -s class show dev eno1
tc filter show dev eno1
tc filter show dev eno1 ingress

# Kubernetes bandwidth annotations on pods (the CNI bandwidth plugin shapes with tc)
kubectl get pods -A -o json | grep -E 'kubernetes.io/(ingress|egress)-bandwidth'
```

```
# Healthy Ubuntu default on a multi-queue NIC
$ tc qdisc show dev eno1
qdisc mq 0: root
qdisc fq_codel 0: parent :4 limit 10240p flows 1024 quantum 1514 target 5ms interval 100ms memory_limit 32Mb ecn drop_batch 64
qdisc fq_codel 0: parent :3 limit 10240p flows 1024 quantum 1514 target 5ms interval 100ms memory_limit 32Mb ecn drop_batch 64
qdisc fq_codel 0: parent :2 limit 10240p flows 1024 quantum 1514 target 5ms interval 100ms memory_limit 32Mb ecn drop_batch 64
qdisc fq_codel 0: parent :1 limit 10240p flows 1024 quantum 1514 target 5ms interval 100ms memory_limit 32Mb ecn drop_batch 64

# Problem: a token-bucket shaper someone left behind
$ tc -s qdisc show dev eno1
qdisc tbf 8001: root refcnt 2 rate 100Mbit burst 125000b lat 50ms
 Sent 81234567890 bytes 56123412 pkt (dropped 412331, overlimits 9123456 requeues 0)
 backlog 0b 0p requeues 0

# Problem: a chaos-test delay/loss emulator that was never removed
$ tc -s qdisc show dev eno1
qdisc netem 8002: root refcnt 2 limit 1000 delay 100ms loss 1%
 Sent 9123456 bytes 61234 pkt (dropped 612, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
```

**What it means:**

- `mq` with `fq_codel` (or `fq`) children is the normal default: no shaping, fair queueing per flow. Nothing to see.
- **`tbf ... rate 100Mbit`** → this host caps itself at 100 Mbit/s. `dropped` and `overlimits` counting up confirm it is actively limiting. Someone (a test, a script like wondershaper, an old QoS policy) put it there.
- **`netem ... delay 100ms loss 1%`** → an emulator adding latency and loss to *everything*. It is a testing tool and should never be on a production interface.
- `htb` with classes → a deliberate QoS tree; read `tc -s class show` to see each class's `rate`/`ceil` and which one is dropping.
- Filters on `ingress` with `police rate ... drop` → incoming traffic is being policed.

Shaper vs policer, so you can recognise limits you cannot see (ISP, switch, cloud, hypervisor):

| Signature | Shaper (queues then sends) | Policer (drops above rate) |
|-----------|----------------------------|----------------------------|
| TCP throughput | Smooth, flat at the rate | Sawtooth, below the rate, many retransmits |
| Latency under load | Rises (packets wait in the queue) | Stays flat, loss instead |
| UDP iperf3 above the rate | Little loss until the queue overflows | Loss starts sharply at the rate |
| Typical places | Linux tc, firewalls, SD-WAN, hypervisor QoS | ISP edge, switch port policies, cloud per-flow limits |

> ⚠️ Removing a qdisc changes traffic behaviour immediately and may undo a QoS
> policy someone needs. Save the current state first
> (`tc -s qdisc show > ~/tc-before-$(date +%F).txt`), find out who added it (change
> log, config management, `grep -r 'tc qdisc' /etc`), and agree on it before
> deleting. `sudo tc qdisc del dev eno1 root` restores the default qdisc.

**Why this step (now):** a flat, round throughput number, or loss that begins at an exact rate, is the fingerprint of a limiter, not of a fault. Checking the host's own `tc` is cheap and read-only, and often finds a forgotten test. If the host is clean, the signature still tells you to look upstream at a device or contract with a limit.

**Next step:** if a local shaper/emulator explains it → remove or correct it with the owner's agreement, then repeat Step 4. If the signature points upstream → ask the network team/ISP for the port or contract rate (on AWS, section 9). If no limits anywhere → Step 12.

### Step 12 — Check the connection tracking table

**Goal:** make sure netfilter's conntrack table is not full, because when it is, the kernel silently drops new connections.

Every connection through a host that does NAT or stateful filtering (Docker,
Kubernetes kube-proxy, UFW, firewalld, any router/VPN gateway) gets an entry in
the conntrack table. When the table is full, **new** connections are dropped
while existing ones keep working, which users experience as "slow", "stalls" or
"random timeouts", especially under load.

```bash
# The definitive symptom
sudo journalctl -k --since '24 hours ago' | grep -i conntrack
sudo dmesg -T | grep -i conntrack

# Current usage vs the limit
sudo conntrack -C
cat /proc/sys/net/netfilter/nf_conntrack_count
sysctl net.netfilter.nf_conntrack_max net.netfilter.nf_conntrack_buckets

# Per-CPU statistics: drop, early_drop, insert_failed
sudo conntrack -S

# Who fills it? Top original destinations, and breakdown by TCP state
sudo conntrack -L 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^dst=/){print $i; break}}' | sort | uniq -c | sort -nr | head
sudo conntrack -L -p tcp 2>/dev/null | awk '{print $4}' | sort | uniq -c | sort -nr

# Timeouts: established TCP entries live 5 days by default
sysctl net.netfilter.nf_conntrack_tcp_timeout_established net.netfilter.nf_conntrack_tcp_timeout_time_wait
```

```
$ sudo journalctl -k --since '24 hours ago' | grep -i conntrack
Oct 03 09:41:12 gw01 kernel: nf_conntrack: nf_conntrack: table full, dropping packet
Oct 03 09:41:17 gw01 kernel: net_ratelimit: 2318 callbacks suppressed

$ sudo conntrack -C
262144
$ sysctl net.netfilter.nf_conntrack_max
net.netfilter.nf_conntrack_max = 262144

$ sudo conntrack -S
cpu=0   	found=0 invalid=1290 insert=0 insert_failed=3 drop=8812 early_drop=1520 error=0 search_restart=0
cpu=1   	found=0 invalid=1101 insert=0 insert_failed=1 drop=7930 early_drop=1398 error=0 search_restart=0

$ sudo conntrack -L -p tcp 2>/dev/null | awk '{print $4}' | sort | uniq -c | sort -nr
 201733 TIME_WAIT
  48211 ESTABLISHED
   9102 SYN_SENT
   2981 CLOSE_WAIT
```

**What it means:**

- **`table full, dropping packet`** in the kernel log is proof. `net_ratelimit: N callbacks suppressed` means thousands more were dropped without being logged.
- Count `262144` equals the max `262144` → the table is at its limit right now.
- `drop` and `early_drop` climbing → new connections are being refused (early_drop is the kernel evicting unassured entries to make room).
- `insert_failed` is a different problem: a **race** when two packets of a new flow (classically the parallel A and AAAA DNS queries from glibc over one UDP socket) try to create the same entry. It produces the famous intermittent **5-second DNS delays** in Docker and Kubernetes (Step 14).
- State breakdown dominated by `TIME_WAIT` → many short-lived connections (an app without HTTP keep-alive or connection pooling). Lots of `SYN_SENT` → connections to a destination that does not answer.

**Why this step (now):** conntrack exhaustion produces random, load-dependent stalls that look like network loss, and it happens on exactly the boxes in your stack that NAT a lot: Docker hosts, Kubernetes nodes, VPN gateways, and reverse proxies. It is one log grep to confirm or rule out.

**Next step:** if full → raise the limit (below), fix the source (keep-alive/pooling, shorter timeouts), then repeat the test. If `insert_failed` rises together with 5 s DNS delays → Step 14. If conntrack is fine → Step 13.

Raising the limit (memory cost is roughly 300 bytes per entry, so 524288 entries is about 150–200 MB at full use):

```bash
# Runtime change (lost at reboot)
sudo sysctl -w net.netfilter.nf_conntrack_max=524288

# Persistent: load the module early so the sysctl applies at boot
echo nf_conntrack | sudo tee /etc/modules-load.d/nf_conntrack.conf
echo 'options nf_conntrack hashsize=131072' | sudo tee /etc/modprobe.d/nf_conntrack.conf
sudo tee /etc/sysctl.d/90-conntrack.conf >/dev/null <<'EOF'
net.netfilter.nf_conntrack_max = 524288
# 1 day instead of 5 for idle established entries
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
EOF
sudo sysctl --system
```

> ⚠️ Do **not** "fix" this with `conntrack -F` (flush). It deletes the NAT state of
> every live connection: Docker published ports, Kubernetes Services and VPN
> sessions break for all users at once. On Kubernetes nodes, **kube-proxy sets
> `nf_conntrack_max` itself** (from `conntrack.maxPerCore`, default 32768 per
> core, minimum `conntrack.min` 131072), so change kube-proxy's configuration
> instead of the node sysctl, which kube-proxy would overwrite when it starts. Setting
> `maxPerCore: 0` tells kube-proxy to leave the node's value as it is.

### Step 13 — Check softirq load, IRQ spread and NIC queues

**Goal:** confirm the host's CPUs can process packets fast enough, and that network interrupts are spread across cores rather than piling onto one.

Every received packet is processed by a CPU in **softirq** context. If all NIC
interrupts land on one core, that core hits 100% `%soft` while the rest of the
machine is idle, and the NIC starts dropping (Step 7's `missed`/`fifo` counters).

```bash
# Per-core utilisation: watch %soft (softirq), %irq and %steal
mpstat -P ALL 1 5

# Which CPUs service the NIC's interrupt queues?
grep -E 'CPU|eno1' /proc/interrupts
watch -d -n 1 "grep -E 'CPU|eno1' /proc/interrupts"

# How many queues (channels) does the NIC have, and how many are in use?
sudo ethtool -l eno1

# Is irqbalance running? (it spreads IRQs across cores)
systemctl status irqbalance --no-pager

# Per-CPU backlog drops and "time squeeze" (budget ran out before the queue emptied)
cpu=0; while read -r processed dropped squeezed rest; do
  printf 'row%-3s processed=%d dropped=%d time_squeeze=%d\n' $cpu $((16#$processed)) $((16#$dropped)) $((16#$squeezed))
  cpu=$((cpu+1))
done < /proc/net/softnet_stat

sysctl net.core.netdev_max_backlog net.core.netdev_budget
```

```
$ mpstat -P ALL 1 1
10:20:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:20:02     all    6.13    0.00    4.80    0.00    0.00   23.50    0.00    0.00    0.00   65.58
10:20:02       0    2.00    0.00    3.00    0.00    0.00   94.00    0.00    0.00    0.00    1.00
10:20:02       1    8.00    0.00    5.00    0.00    0.00    0.00    0.00    0.00    0.00   87.00
10:20:02       2    7.00    0.00    6.00    0.00    0.00    0.00    0.00    0.00    0.00   87.00
10:20:02       3    7.50    0.00    5.20    0.00    0.00    0.00    0.00    0.00    0.00   87.30

$ grep -E 'CPU|eno1' /proc/interrupts
            CPU0       CPU1       CPU2       CPU3
 126:  918234112          0          0          0  IR-PCI-MSI 1572864-edge      eno1-TxRx-0

$ sudo ethtool -l eno1
Channel parameters for eno1:
Pre-set maximums:
RX:		n/a
TX:		n/a
Other:		1
Combined:	8
Current hardware settings:
RX:		n/a
TX:		n/a
Other:		1
Combined:	1

$ (softnet_stat loop)
row0   processed=1841234112 dropped=48211 time_squeeze=912334
row1   processed=1123 dropped=0 time_squeeze=0
row2   processed=998 dropped=0 time_squeeze=0
row3   processed=1201 dropped=0 time_squeeze=0
```

**What it means:**

- Overall the box is about 66% idle, but **CPU0 is at 94% `%soft`**. Averages hide this; always look per core.
- `/proc/interrupts`: one queue `eno1-TxRx-0`, every interrupt on CPU0.
- `ethtool -l`: the NIC supports 8 combined queues but only **1 is enabled**, so receive-side scaling (RSS) cannot spread flows over cores.
- `softnet_stat` row 0: `dropped` (backlog full) and a large `time_squeeze` (the softirq budget ran out with packets still waiting) → CPU0 cannot keep up; packets are lost *inside the host* and TCP sees it as network loss.
- `%steal` above a few percent on a VM → the hypervisor is not giving you CPU; packet processing (and everything else) stalls. That is a host/cloud capacity problem, see [CPU & performance](03-cpu-performance.md).
- A **single** TCP flow is always hashed to one queue and therefore one core. Very fast single flows (several Gbit/s) can be CPU-bound on one core by design; parallel flows spread out.

**Why this step (now):** by this point the link, path and TCP settings have been checked, so the remaining suspect for "drops with no visible cause" is the host's ability to process packets. It is especially common on older servers, on VMs with single-queue virtual NICs, and on busy reverse proxies and gateways.

**Next step:** if one core is saturated with `%soft` → enable more queues (`sudo ethtool -L eno1 combined 8`, which resets the link: maintenance window), make sure `irqbalance` is running (`sudo systemctl enable --now irqbalance`), and on single-queue virtual NICs enable multi-queue on the hypervisor or use RPS (`echo f | sudo tee /sys/class/net/eth0/queues/rx-0/rps_cpus` spreads to CPUs 0–3). If `%steal` is high → move/resize the VM. If CPUs are fine → Step 14.

### Step 14 — Rule out slow DNS resolution

**Goal:** prove whether name resolution is slow, which resolver is slow, and why.

```bash
# Which DNS servers does systemd-resolved use, and which one is "current"?
resolvectl status

# Cache hit rate and transaction counts
resolvectl statistics

# Resolve through systemd-resolved and see the timing it reports
resolvectl query app.example.com

# Time the full glibc path that curl and most apps use (/etc/hosts, nsswitch, IPv4+IPv6)
time getent ahosts app.example.com

# Ask the local stub, then each upstream directly, and compare "Query time"
# (2>&1 and the extra patterns keep timeout messages visible)
dig app.example.com 2>&1 | grep -E 'Query time|SERVER|timed out|no servers'
dig @192.0.2.53 app.example.com 2>&1 | grep -E 'Query time|SERVER|timed out|no servers'
dig @192.0.2.54 app.example.com 2>&1 | grep -E 'Query time|SERVER|timed out|no servers'

# Intermittent? Measure 20 lookups in a row
for i in $(seq 1 20); do dig +noall +stats app.example.com | awk '/Query time/{print $4" ms"}'; done

# What the resolver config and lookup order are
cat /etc/resolv.conf
grep -E '^hosts:' /etc/nsswitch.conf

# Watch the queries on the wire (which server, retries, timeouts, AAAA)
sudo tcpdump -ni any port 53
```

```
$ resolvectl status
Global
       Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
resolv.conf mode: stub

Link 2 (eno1)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.0.2.54
       DNS Servers: 192.0.2.53 192.0.2.54
        DNS Domain: corp.example

$ resolvectl query app.example.com
app.example.com: 203.0.113.10                  -- link: eno1
                 2001:db8:10::20               -- link: eno1

-- Information acquired via protocol DNS in 2.0123s.
-- Data is authenticated: no; Data was acquired via local or encrypted transport: no
-- Data from: network

$ dig @192.0.2.53 app.example.com 2>&1 | grep -E 'Query time|SERVER|timed out|no servers'
;; communications error to 192.0.2.53#53: timed out
;; communications error to 192.0.2.53#53: timed out
;; communications error to 192.0.2.53#53: timed out
;; no servers could be reached

$ dig @192.0.2.54 app.example.com 2>&1 | grep -E 'Query time|SERVER|timed out|no servers'
;; Query time: 14 msec
;; SERVER: 192.0.2.54#53(192.0.2.54) (UDP)

$ for i in $(seq 1 20); do ...; done
12 ms
0 ms
0 ms
2004 ms
0 ms
...
```

**What it means:**

- `Current DNS Server: 192.0.2.54` although `192.0.2.53` is listed first → systemd-resolved **switched away** from the first server because it failed. Each time it retries the first server (after a failure on the second, or a restart), clients wait.
- `resolvectl query` took **2 s** for a name that the working server answers in 14 ms → time is being lost on retries and timeouts, not on the answer itself.
- `dig @192.0.2.53` times out → the first upstream is dead or blocked (firewall, wrong IP in netplan, VPN-only server).
- In the loop, `0 ms` are cache hits, `12 ms` a normal miss, and the occasional **2000+ ms** is a lookup that hit the dead server first. Users experience this as "random slowness".
- `resolvectl statistics` with very few cache hits → every request goes upstream; check that apps are not bypassing the stub (for example by pointing straight at an upstream).

Common causes of slow (not failing) DNS:

| Cause | How it shows | Fix |
|-------|--------------|-----|
| First nameserver dead or filtered | 2–5 s delays, `Current DNS Server` is not the first one | Remove/fix it in netplan (`nameservers:`) or DHCP |
| Search domains with `ndots` (Kubernetes uses `ndots:5`) | One lookup of `api.example.com` becomes 4–6 queries | Use FQDNs with a trailing dot, or lower `ndots` in the pod's `dnsConfig` |
| AAAA queries slow or unanswered | IPv4-only names still wait for the AAAA answer | Fix the resolver; avoid disabling IPv6 blindly |
| conntrack race on parallel A/AAAA (Docker, K8s) | Exactly **5 s** delays, `insert_failed` in `conntrack -S` | `options single-request-reopen` in the pod/container resolv.conf, NodeLocal DNSCache on K8s |
| Docker embedded DNS falling back to 8.8.8.8 (blocked on-prem) | Containers slow/failing to resolve while the host is fine | Set `"dns": [...]` in `/etc/docker/daemon.json` |
| Upstream resolver far away (VPN, other region) | Every miss costs 50–200 ms | Use a local caching resolver |

**Why this step (now):** DNS is often the *first* suspect from Step 1 (`time_namelookup` high), but it is the last step here because, once Step 1 points at it, this step tells you which server and why. It is read-only and fast, and a dead first resolver is one of the most common "everything feels slow" causes on on-prem Ubuntu servers.

**Next step:** if one upstream is dead/slow → fix the resolver list (see the [DNS reference](08-dns.md); use `sudo netplan try` for safe changes). If only containers or pods are slow → section 10 and [Containers & K8s playbook](26-playbook-containers-k8s.md). If DNS is fast → the delay is elsewhere: go back to the Step 1 timeline, and use the master decision tree (section 20).

---

## 8. Safe tuning: buffers, BBR, MTU and offloads

> 📚 **Study path:** 1) Note: [Kernel & sysctl reference](13-kernel-system.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*, Operations Deployment → Change Kernel Runtime Parameters ([link](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Read: [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html), the network tuning material · 4) Practice: on the "Long fat pipe" drill (section 22), apply the buffer change, re-measure, then roll back with this section's commands.

**Level:** [L3 · Senior]. Persistent kernel and interface changes affect every
connection on the host. Seniors make them only after the evidence supports it,
roll them out through config management, and keep a tested rollback.

Tune only after a step above has *proved* which limit you are hitting. Every
change below is a sysctl or interface setting with a clear rollback. Make one
change, re-run the exact same test (Step 4/5 or the user's real transfer), and
keep it only if the number moved.

### Record the current state first

```bash
mkdir -p ~/net-baseline
sysctl -a 2>/dev/null | grep -E '^net\.(core|ipv4\.tcp|netfilter)' | sort \
  > ~/net-baseline/sysctl-before-$(date +%F).txt
tc qdisc show > ~/net-baseline/tc-before-$(date +%F).txt
for i in $(ls /sys/class/net); do echo "== $i"; sudo ethtool -k $i 2>/dev/null | grep -E 'segmentation-offload|receive-offload'; done \
  > ~/net-baseline/offloads-before-$(date +%F).txt
```

### Bigger TCP buffers for long, fat paths

Use when Step 5 showed one stream far below parallel streams with few
retransmits, or `ss -ti` showed `rwnd_limited`/`sndbuf_limited`, or `iperf3 -w 16M`
helped. Size the maximum to at least the BDP (section 2), with headroom, because
part of each buffer is bookkeeping overhead rather than window: 64 MB covers
roughly 10 Gbit/s at 25–50 ms or 1 Gbit/s at well over 200 ms.

```bash
sudo tee /etc/sysctl.d/90-tcp-buffers.conf >/dev/null <<'EOF'
# Only the MAXIMUM values are raised; autotuning grows a socket's buffer only
# when that connection actually needs it.
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 131072 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
EOF
sudo sysctl --system
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem
```

- Raise them on **both** ends: the receiver's `tcp_rmem` limits downloads to it, the sender's `tcp_wmem` limits uploads from it.
- Do not raise the *default* (middle) values much: with thousands of sockets that wastes memory. The global ceiling is `net.ipv4.tcp_mem` (in pages); leave it alone unless you see `TCP: out of memory` in the kernel log.
- New connections pick up the change; existing ones keep their old limits.

### BBR congestion control

BBR estimates the bottleneck bandwidth and minimum RTT instead of treating every
loss as congestion, so on long or slightly lossy paths a BBR sender often achieves
several times CUBIC's throughput. It only affects traffic the host **sends**.

```bash
# Load it now and at every boot
sudo modprobe tcp_bbr
echo tcp_bbr | sudo tee /etc/modules-load.d/bbr.conf

sudo tee /etc/sysctl.d/90-bbr.conf >/dev/null <<'EOF'
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
EOF
sudo sysctl --system

# Verify (new connections only; check a fresh one with ss -ti, it shows "bbr")
sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_available_congestion_control
```

- Good candidates: servers that send to far-away users or sites (web/download servers, Harbor and other registries, backup sources, CI artifact servers).
- `default_qdisc` only applies when an interface's qdisc is created (boot, link re-creation). Since kernel 4.13 BBR paces by itself, so it works even before `fq` is in place.
- Be careful on shared bottlenecks: BBR (v1, the version in mainline kernels) can take more than its fair share from CUBIC flows and may retransmit more. Test on one host, compare, then roll out with config management.

### MTU, MSS clamping and PMTU probing

Fix MTU where the smaller link actually is (the tunnel or overlay), not by
shrinking every interface.

```bash
# Netplan: set an interface MTU (only if THIS link really is smaller, or for jumbo
# frames when EVERY device on the segment supports them). netplan try rolls back
# automatically after 120 s unless you confirm, which saves you on remote servers.
# If the file is generated by cloud-init (its header says so), cloud-init can
# overwrite your edit: disable its network config first or use your own file.
sudo nano /etc/netplan/50-cloud-init.yaml
#   network:
#     version: 2
#     ethernets:
#       eno1:
#         mtu: 9000
sudo netplan try

# WireGuard: set the tunnel MTU in /etc/wireguard/wg0.conf, [Interface] section
#   MTU = 1380
# The restart drops the tunnel for a moment: never do it from a session that runs through wg0
sudo systemctl restart wg-quick@wg0

# Let TCP probe for a working packet size when it detects a black hole
echo 'net.ipv4.tcp_mtu_probing = 1' | sudo tee /etc/sysctl.d/90-mtu-probing.conf
sudo sysctl --system
```

MSS clamping on a Linux router, firewall or VPN gateway rewrites the MSS option in
TCP SYN packets it forwards, so the two endpoints agree on segments small enough
for the tunnel. It works even when ICMP is blocked, but only for TCP (UDP and
QUIC/HTTP3 are not affected).

```bash
# nftables (/etc/nftables.conf), a dedicated table so it cannot clash with others
#   table inet mss_clamp {
#     chain forward {
#       type filter hook forward priority mangle; policy accept;
#       tcp flags syn tcp option maxseg size set rt mtu
#     }
#   }
sudo nft -c -f /etc/nftables.conf      # syntax check first
sudo systemctl reload nftables
# Caution: Ubuntu's stock /etc/nftables.conf starts with "flush ruleset". Reloading
# it on a host that also runs Docker or UFW wipes THEIR rules too (published ports
# and container NAT stop working). Use this form only on a dedicated nftables
# gateway; on Docker/UFW hosts use the UFW block below.

# iptables equivalent
sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

# UFW: add this block at the TOP of /etc/ufw/before.rules, then: sudo ufw reload
#   *mangle
#   :FORWARD ACCEPT [0:0]
#   -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
#   COMMIT
```

> ⚠️ Jumbo frames (MTU 9000) must match on every host, switch port and router
> interface in the L2 segment. One device left at 1500 creates exactly the black
> hole Step 9 describes. Never flush firewall rules (`iptables -F`, `nft flush
> ruleset`) to "test" an MTU or speed theory on a remote server: you will lock
> yourself out and drop Docker's NAT rules. Add a specific rule instead.

### NIC offloads

Offloads (TSO/GSO on send, GRO/LRO on receive) let the NIC or kernel handle large
"super-packets", saving a lot of CPU. Keep them **on** unless a driver bug is
proven.

```bash
sudo ethtool -k eno1 | grep -E 'tcp-segmentation-offload|generic-segmentation-offload|generic-receive-offload|large-receive-offload'

# Diagnostic only (and only on a test host): turn GRO off, re-test, turn it back on
sudo ethtool -K eno1 gro off
sudo ethtool -K eno1 gro on
```

→ A classic false alarm: `tcpdump` on the sending or receiving host shows TCP
"packets" of 20 000–65 000 bytes, far larger than the MTU. That is TSO/GRO
working (tcpdump sees the super-packet before the NIC splits it or after GRO
merged it), not a bug.

### Rollback

```bash
# Remove only the files you created, then restore defaults at runtime
sudo rm -f /etc/sysctl.d/90-bbr.conf /etc/sysctl.d/90-tcp-buffers.conf /etc/sysctl.d/90-mtu-probing.conf
sudo rm -f /etc/modules-load.d/bbr.conf
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic net.core.default_qdisc=fq_codel
sudo sysctl -w net.ipv4.tcp_rmem='4096 131072 6291456' net.ipv4.tcp_wmem='4096 16384 4194304'
sudo sysctl -w net.core.rmem_max=212992 net.core.wmem_max=212992
sudo sysctl -w net.ipv4.tcp_mtu_probing=0
sudo sysctl --system
# default_qdisc only affects qdiscs created later; existing interfaces keep fq until
# their root qdisc is re-created (sudo tc qdisc del dev eno1 root) or the next boot

# Compare with what you recorded
sysctl -a 2>/dev/null | grep -E '^net\.(core|ipv4\.tcp|netfilter)' | sort | diff ~/net-baseline/sysctl-before-*.txt -
```

See [Kernel & sysctl reference](13-kernel-system.md) for how `/etc/sysctl.d/`
ordering works.

---

## 9. AWS: instance limits, ENA, AZs and NAT

> 📚 **Study path:** 1) KodeKloud: *AWS Networking Fundamentals*, VPC, gateways, routing and load balancer modules ([link](https://kodekloud.com/courses/aws-networking-fundamentals)) · 2) Video: KodeKloud, *AWS Networking Basics \| AWS VPC & Subnets for Beginners* ([link](https://www.youtube.com/watch?v=QM63dyA_4Pc)) · 3) Note: [Learn: cloud & AWS](36-learn-cloud-aws.md) and the [AWS reference](16-aws-cloud.md) · 4) Practice: KodeKloud *AWS Playground* ([link](https://kodekloud.com/cloud-playgrounds/aws)). Start two instances, run iperf3 with `-P 1` and `-P 8`, and read the `allowance` counters.

**Level:** [L3 · Senior]. Instance sizing, AZ placement and NAT design are
platform decisions. A mid-level engineer should still recognise the allowance
counters and escalate with them.

In AWS the "physical layer" is replaced by **allowances**: each instance type has
bandwidth, packets-per-second and connection-tracking limits enforced by the Nitro
system. When you exceed them, packets are queued or dropped *without any error in
the guest OS* except special ENA counters. The [AWS reference](16-aws-cloud.md)
covers security groups, NACLs and routing; this section covers speed.

### Instance bandwidth: baseline, burst and per-flow limits

```bash
# What does AWS promise for these instance types?
aws ec2 describe-instance-types --instance-types m6i.large c6in.xlarge \
  --query 'InstanceTypes[].[InstanceType, NetworkInfo.NetworkPerformance, NetworkInfo.NetworkCards[0].BaselineBandwidthInGbps, NetworkInfo.NetworkCards[0].PeakBandwidthInGbps]' \
  --output table
```

```
-----------------------------------------------------------
|                  DescribeInstanceTypes                  |
+-------------+-------------------------+--------+--------+
|  m6i.large  |  Up to 12.5 Gigabit     |  0.781 |  12.5  |
|  c6in.xlarge|  Up to 30 Gigabit       |  6.25  |  30.0  |
+-------------+-------------------------+--------+--------+
```

**What it means:**

- **"Up to 12.5 Gigabit"** is a *burst* figure. The sustained **baseline** for an m6i.large is ~0.78 Gbit/s. Instances accumulate network I/O credits while below baseline and spend them while above it; a burst typically lasts minutes up to about an hour depending on size, then the instance falls back to baseline. A nightly backup that ran fine for 10 minutes and then crawled is the classic symptom.
- Instances with a fixed figure ("25 Gigabit") have no burst model.
- **Per-flow limit**: a single TCP/UDP flow (one 5-tuple) is limited to about **5 Gbit/s** between instances unless both are in the same cluster placement group (higher, and more with ENA Express). That is why `iperf3 -P 8` beats `-P 1` on big instances.
- **Traffic leaving the region or going through an internet gateway** gets a smaller share (roughly 5 Gbit/s, or half the instance bandwidth on large instances). Check the current EC2 documentation on "instance network bandwidth" for the exact rules of your type.

### ENA driver and the allowance counters

```bash
# Driver must be ena (Nitro). Old instance types or AMIs may show something else.
ethtool -i ens5

# The allowance counters: how often AWS shaped this ENI
ethtool -S ens5 | grep -E 'allowance'
```

```
$ ethtool -i ens5
driver: ena
version: 6.8.0-1015-aws
firmware-version:
bus-info: 0000:00:05.0

$ ethtool -S ens5 | grep -E 'allowance'
     bw_in_allowance_exceeded: 0
     bw_out_allowance_exceeded: 128834
     pps_allowance_exceeded: 0
     conntrack_allowance_exceeded: 0
     linklocal_allowance_exceeded: 4312
     conntrack_allowance_available: 136812
```

| Counter | Packets queued or dropped because… | Typical fix |
|---------|-------------------------------------|-------------|
| `bw_in_allowance_exceeded` / `bw_out_allowance_exceeded` | Aggregate inbound/outbound bandwidth exceeded the instance's limit | Larger or network-optimised type (`n` variants), spread load, compress |
| `pps_allowance_exceeded` | Packets per second limit exceeded (small packets: DNS, VoIP, many tiny requests) | Larger type, batch requests, bigger packets |
| `conntrack_allowance_exceeded` | Security group connection-tracking limit reached | Larger type, untracked SG flows (TCP/UDP allowed from 0.0.0.0/0 inbound *and* to 0.0.0.0/0 on all ports outbound; see the EC2 "connection tracking" docs), fewer idle connections |
| `linklocal_allowance_exceeded` | More than ~1024 pps to link-local services: Route 53 Resolver (VPC+2), instance metadata, Amazon Time Sync | **Cache DNS locally** (systemd-resolved cache, NodeLocal DNSCache on EKS), cache IMDS credentials |
| `conntrack_allowance_available` | (not an error) remaining tracked connections before the limit | Watch it trend toward 0 |

→ The counters are cumulative since the driver loaded. Take two samples a minute
apart; any **increase** while users complain is your answer. `linklocal` drops
show up as slow or failing DNS lookups, which brings you back to Step 14. Ship
these counters to CloudWatch (CloudWatch agent `ethtool` plugin) or Prometheus
(`node_exporter` ethtool collector) so you have history.

### Cross-AZ latency and chatty applications

- Same-AZ RTT is well under a millisecond; cross-AZ is typically ~0.5–2 ms. Irrelevant for one request, decisive for an app that makes 500 sequential DB queries per page: 500 × 1.5 ms = 0.75 s added per page.
- After an Auto Scaling or failover event the app and its database may end up in different AZs: "it got slower after the failover" is often this.
- Cross-AZ traffic is also billed per GB in both directions.
- For latency-critical clusters, a **cluster placement group** keeps instances physically close.

### NAT gateway limits

A NAT gateway in the path of private-subnet traffic has its own limits:

- Bandwidth starts at 5 Gbit/s and scales automatically up to 100 Gbit/s.
- About **55,000 simultaneous connections to each unique destination** (IP, port, protocol) per NAT gateway IP address. A fleet hammering one API endpoint runs out of ports: the `ErrorPortAllocation` metric rises and new connections fail or stall. Add secondary IPs to the NAT gateway or spread destinations.
- **Idle timeout 350 s**: idle connections are silently dropped; the next packet gets a RST or nothing. Long-idle DB or SSH sessions through NAT "hang". Use TCP keep-alives under 350 s.
- Traffic to S3 and DynamoDB through a NAT gateway is slower and costs data-processing fees; a **gateway VPC endpoint** sends it directly, free, and usually faster.

```bash
# Port allocation errors and drops on a NAT gateway over the last 3 hours
aws cloudwatch get-metric-statistics --namespace AWS/NATGateway \
  --metric-name ErrorPortAllocation --dimensions Name=NatGatewayId,Value=nat-0abc123 \
  --start-time $(date -u -d '-3 hours' +%FT%TZ) --end-time $(date -u +%FT%TZ) \
  --period 300 --statistics Sum --output table
# repeat with --metric-name PacketsDropCount and IdleTimeoutCount
```

### MTU inside and outside the VPC

- Inside a VPC most current instances use **MTU 9001** (jumbo frames). Traffic through an internet gateway is limited to **1500**, Site-to-Site VPN to less (about 1446 or below inside the tunnel), and on-prem paths are usually 1500 unless Direct Connect is configured for jumbo frames. Transit Gateway supports 8500.
- PMTUD therefore matters for every instance talking to the internet. Security groups need an **inbound** custom ICMP rule for "Destination Unreachable: fragmentation needed" (IPv4) and ICMPv6 "Packet Too Big" so those messages are not dropped; otherwise you get Step 9's black hole on large responses.
- Check: `ip link show ens5` (mtu 9001) and `tracepath` to an internet host (pmtu 1500).

### Quick AWS speed checklist

```
1. iperf3 A <-> B inside the same AZ, -P 1 and -P 8      -> per-flow vs instance limit
2. ethtool -S ens5 | grep allowance (two samples)        -> AWS shaping you cannot otherwise see
3. Instance type baseline vs observed (describe-instance-types, CloudWatch NetworkOut)
4. Same AZ? (aws ec2 describe-instances ... Placement.AvailabilityZone)
5. Through a NAT GW? ErrorPortAllocation / PacketsDropCount / IdleTimeoutCount
6. To S3/DynamoDB? Gateway VPC endpoint in place?
7. %steal in mpstat (burstable t3/t4g out of CPU credits slows packet processing too)
```

**Next step:** if an allowance counter rises → resize or change the instance
family, or spread the load, then re-run item 1. If NAT gateway errors rise → add
NAT IPs or a VPC endpoint. If nothing on AWS is limiting → continue with Steps
7–14 inside the instance as on-prem.

---

## 10. Containers and Kubernetes network speed

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate*, Networking Deep Dive – Docker ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Docker/page)) and Docker Overlay Network ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)), then *Kubernetes Networking Deep Dive*, Troubleshooting Internal Networking ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page)) · 2) Note: [Learn: Docker](30-learn-docker.md), section 7 (networking) · 3) Video: KodeKloud, *How Docker Networking Actually Works* ([link](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Practice: [iximiuz: container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch), then the "Container throttling" and "Overlay MTU" drills in section 22.

**Level:** [L3 · Senior]. This section covers the Dokploy Swarm overlay, Docker
MTU and CNI MTU, which is the platform layer of your stack and part of CKA
homelab work. The netshoot measurements are useful from L2 onward.

Containers add layers between the application and the wire: veth pairs, bridges,
NAT, overlays, a reverse proxy, and CPU limits. Each layer is usually cheap, but
some (userland proxy, encrypted overlays, wrong MTU, CPU throttling) are not. The
method stays the same: measure each layer separately and compare.

### Where container traffic loses speed

| Path | Extra work | Typical impact |
|------|------------|----------------|
| Container ↔ container, same bridge network | veth + Linux bridge | Negligible |
| Outside client → published port (`-p 443:443`) | DNAT + conntrack | Small; conntrack table matters under load (Step 12) |
| Host → `localhost`/`127.0.0.1` published port | Goes through **docker-proxy** (a userland copy) | Noticeable CPU and latency at high rates; `"userland-proxy": false` in `daemon.json` switches to kernel hairpin NAT |
| `network_mode: host` | None | Native speed, but no isolation and port clashes (Apache vs Traefik on 443) |
| Swarm overlay (Dokploy's `dokploy-network`) between nodes | VXLAN encapsulation, MTU 1450 | Some CPU, and MTU problems if the underlay is below 1500 |
| Encrypted overlay (`--opt encrypted`) | IPsec ESP per packet | Large CPU cost, lower throughput, smaller MTU |
| Through Traefik | One more TCP/TLS hop, request buffering | Adds ms per request; problems show as high "server think time" in Step 1 |
| Kubernetes Service (ClusterIP) | kube-proxy DNAT (iptables/IPVS) or eBPF | Small; conntrack matters |
| CNI overlay (Flannel VXLAN, Calico IPIP/VXLAN, Cilium tunnel) | Encapsulation | Some CPU; MTU must be right |
| CPU limit on the container/pod | CFS throttling | **Latency spikes** that look like network jitter |

### Measure container-to-container with netshoot

`nicolaka/netshoot` contains iperf3, curl, mtr, tcpdump, dig and ss, so the
application image does not need any tools.

```bash
# Server on the same network your apps use (dokploy-network is an attachable overlay)
docker run -d --rm --name iperf-srv --network dokploy-network nicolaka/netshoot iperf3 -s

# Client on the same network, ideally scheduled on ANOTHER node (run it there)
docker run --rm --network dokploy-network nicolaka/netshoot iperf3 -c iperf-srv -t 10
docker run --rm --network dokploy-network nicolaka/netshoot iperf3 -c iperf-srv -t 10 -R

# Compare with the hosts themselves (host network namespace = no overlay)
docker run --rm --network host nicolaka/netshoot iperf3 -c 10.0.20.15 -t 10

# Stop the server (--rm removes it automatically)
docker stop iperf-srv

# Is Traefik adding the delay? Time the app directly, then through Traefik.
docker run --rm --network dokploy-network nicolaka/netshoot \
  curl -o /dev/null -s -w 'connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total}\n' http://APP_CONTAINER:PORT/
curl -o /dev/null -s -w 'connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://app.example.com/

# Join a running container's network namespace to test from exactly its point of view
docker run --rm -it --network container:CONTAINER nicolaka/netshoot
```

**How to read it:** if host ↔ host is at line rate but overlay container ↔
container is much lower, the overlay is the cost: check MTU and encryption below.
If the direct app timing is fast and the Traefik timing is slow, look at Traefik
(its logs, CPU, middlewares, TLS) in the [Containers & K8s playbook](26-playbook-containers-k8s.md).
If both are slow in `ttfb`, the application is slow, not the network.

### Docker and Swarm MTU settings

```bash
# MTU of a network and of a container's interface (no tools needed in the image)
docker network inspect dokploy-network --format '{{.Driver}} {{json .Options}}'
docker exec CONTAINER cat /sys/class/net/eth0/mtu
ip link show docker0

# Prove a black hole from inside the container's namespace (Step 9 method)
docker run --rm --network container:CONTAINER nicolaka/netshoot ping -c 3 -M do -s 1472 203.0.113.10
```

Setting the MTU when the host's real path MTU is below 1500:

```bash
# /etc/docker/daemon.json
#   "mtu": 1450                     -> applies to the default bridge (docker0) only
#   "default-network-opts": { "bridge": { "com.docker.network.driver.mtu": "1450" } }
#                                   -> default for NEW user-defined bridge networks (Docker 24+)

# Per network, at creation time (cannot be changed on an existing network)
docker network create -o com.docker.network.driver.mtu=1450 app-net
docker network create -d overlay --attachable --opt com.docker.network.driver.mtu=1370 app-overlay

# Compose
#   networks:
#     default:
#       driver_opts:
#         com.docker.network.driver.mtu: "1450"

# GitLab CI with Docker-in-Docker: give the inner daemon the right MTU
#   services:
#     - name: docker:dind
#       command: ["--mtu=1450"]
```

> ⚠️ Restarting Docker to apply `daemon.json` restarts all containers unless
> `"live-restore": true` is set, and live-restore covers standalone containers
> only, **not Swarm services** (which is how Dokploy runs the applications it deploys).
> An existing network's MTU can only be changed
> by **re-creating the network**, which means detaching every container. For
> `dokploy-network` that is a full maintenance window for every app on it: plan it,
> do not improvise it. Validate `daemon.json` (`sudo dockerd --validate --config-file /etc/docker/daemon.json`
> on recent versions) before restarting.

### Kubernetes: CNI MTU and pod-to-pod tests

```bash
# MTU as the pod sees it, and as the node sees the CNI interfaces
kubectl exec POD -- cat /sys/class/net/eth0/mtu
ip -br link | grep -E 'cali|flannel|cilium|vxlan|tunl|wireguard'

# Where the CNI stores its MTU
kubectl get installation default -o jsonpath='{.spec.calicoNetwork.mtu}'      # Calico (operator)
kubectl -n kube-system get cm calico-config -o yaml | grep -i mtu             # Calico (manifest)
cat /run/flannel/subnet.env                                                   # Flannel: FLANNEL_MTU
kubectl -n kube-system get cm cilium-config -o yaml | grep -i mtu             # Cilium
```

The test matrix: run iperf3 server and client pods pinned to specific nodes, and
compare four numbers.

```bash
# Terminal 1: server pod pinned to worker-1. --rm removes it when you press Ctrl+C,
# so no cleanup (and no kubectl delete) is needed afterwards.
kubectl run iperf-srv --rm -it --restart=Never --image=nicolaka/netshoot \
  --overrides='{"apiVersion":"v1","spec":{"nodeName":"worker-1"}}' --command -- iperf3 -s

# Terminal 2: find its IP
kubectl get pod iperf-srv -o wide

# Client on ANOTHER node (cross-node, through the overlay)
kubectl run iperf-cli --rm -it --restart=Never --image=nicolaka/netshoot \
  --overrides='{"apiVersion":"v1","spec":{"nodeName":"worker-2"}}' --command -- iperf3 -c POD_IP -t 10

# Client on the SAME node (no encapsulation)
kubectl run iperf-cli --rm -it --restart=Never --image=nicolaka/netshoot \
  --overrides='{"apiVersion":"v1","spec":{"nodeName":"worker-1"}}' --command -- iperf3 -c POD_IP -t 10

# Node-to-node baseline: same pods with hostNetwork (no CNI at all)
#   --overrides='{"apiVersion":"v1","spec":{"nodeName":"worker-2","hostNetwork":true}}'
```

| Test | What it includes | If only this one is slow |
|------|------------------|--------------------------|
| node ↔ node (`hostNetwork`) | Physical network only | Physical/host problem: Steps 4–13 on the nodes |
| pod ↔ pod, same node | veth + CNI datapath | CNI misconfiguration, CPU limits, eBPF/iptables cost |
| pod ↔ pod, different nodes | + overlay encapsulation and MTU | Overlay MTU, encryption (WireGuard/IPsec CNI mode), VXLAN offload issues |
| pod → Service ClusterIP | + kube-proxy DNAT | kube-proxy mode, conntrack table (Step 12) |

→ Node ↔ node 940 Mbit/s, cross-node pod ↔ pod 300 Mbit/s with many retransmits
is the classic **overlay MTU mismatch**: run the DF ping from a pod to a pod on
another node and lower the CNI MTU to underlay MTU minus the encapsulation
overhead (Step 9's table).

### CPU throttling looks like network latency

A container or pod with a CPU **limit** is paused by the kernel (CFS) for the rest
of each 100 ms period once it uses its quota. Requests that arrive during a pause
wait, so p99 latency spikes by tens of milliseconds while CPU graphs look
moderate. Users call it "the network is laggy".

```bash
docker exec CONTAINER cat /sys/fs/cgroup/cpu.stat
kubectl exec POD -- cat /sys/fs/cgroup/cpu.stat
```

```
usage_usec 912334112
user_usec 701223001
system_usec 211111111
nr_periods 81234
nr_throttled 23110
throttled_usec 412871004
```

→ `nr_throttled / nr_periods` = 23110 / 81234 ≈ **28% of periods throttled**: the
container regularly hits its limit. Raise or remove the CPU **limit** (keep a
sensible request), or fix what burns the CPU. More in
[Docker reference](14-docker-containers.md) and [Kubernetes reference](15-kubernetes.md).

**Next step:** if only the overlay path is slow → fix the network or CNI MTU
(above), then repeat the netshoot test. If only the Traefik timing is slow →
[Containers & K8s playbook](26-playbook-containers-k8s.md). If the hosts
themselves are slow → Steps 4–13 on the nodes. If `nr_throttled` is rising →
raise the limit, then re-measure p99 latency.

---

## 11. Wi-Fi, VPN and remote users

> 📚 **Study path:** 1) Note: [Learn: networking](28-learn-networking.md), section 12 (VPNs, overlays and MTU) · 2) KodeKloud: *Networks and Communications*, network types and hardware modules ([link](https://kodekloud.com/courses/networks-and-communications)); KodeKloud has no VPN or Wi-Fi course · 3) Note: section 2 above (latency under load) and Step 9 (MTU) · 4) Practice: run the bufferbloat test below on your home connection, with the VPN off and then on.

**Level:** [L1–L2 · Junior → Mid]. Juniors collect the remote-user evidence
from the checklist. Mid-level engineers read it and find the layer at fault.

### Wi-Fi versus wired

Wi-Fi is shared, half-duplex radio: every client and neighbouring network on the
same channel takes turns, frames are retried when they collide or fade, and the
"link speed" shown is a momentary modulation rate, not throughput. Real TCP
throughput is typically 30–60% of the displayed rate on a good day.

**The first test for any Wi-Fi complaint is the same test on a cable.** If wired
is fast, stop debugging the network core.

```bash
# Linux client: signal, bitrate, frequency
iw dev wlp2s0 link
# Retries and failures (a high ratio = a poor radio link)
iw dev wlp2s0 station dump | grep -E 'signal|tx bitrate|tx retries|tx failed'
# Neighbouring networks and channels
nmcli -f SSID,CHAN,FREQ,SIGNAL,RATE device wifi list
```

```
$ iw dev wlp2s0 link
Connected to 3c:84:6a:12:34:56 (on wlp2s0)
	SSID: office-5g
	freq: 5180
	signal: -71 dBm
	rx bitrate: 58.5 MBit/s VHT-MCS 6 VHT-NSS 1
	tx bitrate: 26.0 MBit/s VHT-MCS 3 VHT-NSS 1
```

| Signal (RSSI) | Quality | Good enough for |
|---------------|---------|-----------------|
| −30 to −55 dBm | Excellent | Anything |
| −56 to −67 dBm | Good | Video calls, VoIP (−67 is the usual design target) |
| −68 to −75 dBm | Weak | Browsing; calls and big transfers suffer |
| below −75 dBm | Poor | Expect retries, drops and roaming problems |

→ −71 dBm with a 26 Mbit/s transmit rate: the client is too far from the access
point (or behind walls). Expect real uploads of ~10–15 Mbit/s and high jitter.
2.4 GHz reaches further but is crowded and slower; 5/6 GHz are faster but weaker
through walls.

### VPN overhead

| Factor | Effect | Check |
|--------|--------|-------|
| Encapsulation | Smaller MTU (Step 9 table); black holes if PMTUD is blocked | DF ping through the tunnel |
| Encryption CPU | Single-threaded VPN daemons (classic OpenVPN) top out at a few hundred Mbit/s per tunnel | `top`/`mpstat` on the VPN server during a transfer |
| Full tunnel | All internet traffic hairpins through HQ: user → HQ → internet → HQ → user | `ip route get 1.1.1.1` on the client shows the tunnel |
| TCP over TCP (OpenVPN in TCP mode, SSL VPNs on 443) | Two retransmission layers fight under loss: throughput collapses | Prefer UDP transports |
| Concentrator uplink | All users share the HQ internet link | `iftop`/`vnstat` on the VPN server or firewall |
| DNS over the tunnel | Every lookup crosses the VPN (adds RTT) or hits an unreachable resolver | Step 14 on the client |

```bash
# On a WireGuard server: per-peer traffic and last handshake
sudo wg show
# Tunnel MTU and the path through it
ip link show wg0
ping -c 3 -M do -s 1392 10.8.0.1
# CPU on the VPN server while users transfer (one core at 100% = crypto bottleneck)
mpstat -P ALL 1 5
```

### Remote users checklist

Remote users cannot run your tools, so ask for a fixed set of evidence and compare
it with a baseline from someone who is fine:

1. A speed test with the VPN **off**, then **on** (same place, same minute). If both are slow, it is their connection.
2. Wired or Wi-Fi? Signal strength (Windows: `netsh wlan show interfaces`, macOS: `sudo wdutil info`).
3. `ping` to their home router for 60 s (Wi-Fi/LAN quality), then to the VPN gateway's public IP (ISP path).
4. `ping` to the VPN gateway **while** a large upload runs (bufferbloat, below).
5. `pathping` (Windows) or `mtr` (macOS/Linux) to the VPN gateway.
6. Which applications are slow: all of them (path) or one (that app's server or route).

### Bufferbloat test: latency under load

```bash
# Terminal 1: measure latency to a stable host just BEYOND the suspected bottleneck
# (the ISP's first hop or the VPN gateway). Not the router's own LAN address: the
# queue that bloats sits on the router's WAN side, which those pings never cross.
ping -i 0.2 198.51.100.1
# Terminal 2: load that link in the direction you suspect (upload shown), towards
# an iperf3 server you control on the far side of it
iperf3 -c 203.0.113.50 -t 30
# macOS does both at once and reports "Responsiveness":  networkQuality
```

→ Idle RTT 15 ms rising to 400–800 ms while the transfer runs = **bufferbloat** on
the bottleneck device (usually the home or branch router's upload side). The fix
is smart queue management (SQM: `fq_codel` or `cake`) with shaping set slightly
below the real line rate on that router. On a Linux router this is one line, for
example `sudo tc qdisc replace dev wan0 root cake bandwidth 45mbit` for a 50 Mbit/s
uplink.

**Next step:** if Wi-Fi is worse than a cable → fix the radio (closer, 5 GHz,
cable) and stop there. If the problem only appears with the VPN on → Scenario C.
If latency under load explodes → SQM on the bottleneck router. If one remote
user is slow and others are fine → their last mile (Step C5).

---

## 12. Windows: speed and latency tools

> 📚 **Study path:** 1) Note: [Windows reference](17-windows.md) · 2) Note: sections 4–6 above. The Windows commands map one to one onto Steps 1–9 · 3) KodeKloud: no Windows networking course in the verified map, so use *Networks and Communications* for the concepts ([link](https://kodekloud.com/courses/networks-and-communications)) · 4) Practice: run `Test-NetConnection -TraceRoute`, `pathping` and the `curl.exe` timing from a Windows laptop against your own server, and compare with Linux.

**Level:** [L1 · Junior]. Juniors usually collect evidence from Windows users.
The method is the same as on Linux.

The method is identical; only the commands change. Run PowerShell as
Administrator for adapter settings. More Windows networking basics are in the
[Windows reference](17-windows.md).

### Link speed, duplex and adapter errors

```powershell
# Negotiated speed and duplex for every adapter
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, LinkSpeed, FullDuplex

# Error and discard counters (cumulative; run twice and compare)
Get-NetAdapterStatistics -Name "Ethernet" | Format-List ReceivedBytes, SentBytes, ReceivedDiscardedPackets, ReceivedPacketErrors, OutboundDiscardedPackets, OutboundPacketErrors

# Is speed/duplex forced in the driver?
Get-NetAdapterAdvancedProperty -Name "Ethernet" -DisplayName "Speed & Duplex"

# Wi-Fi: signal, band, channel, rates
netsh wlan show interfaces
```

```
Name     InterfaceDescription                Status LinkSpeed  FullDuplex
----     --------------------                ------ ---------  ----------
Ethernet Intel(R) Ethernet Connection I219-V Up     100 Mbps         True
Wi-Fi    Intel(R) Wi-Fi 6 AX201 160MHz       Up     866.7 Mbps       True

    Name                   : Wi-Fi
    State                  : connected
    SSID                   : office-5g
    Radio type             : 802.11ac
    Band                   : 5 GHz
    Channel                : 36
    Receive rate (Mbps)    : 117
    Transmit rate (Mbps)   : 58.5
    Signal                 : 48%
```

→ The wired adapter linked at **100 Mbps** on a gigabit port: cable or switch port
(Step 7 applies unchanged). Windows `Signal` is a percentage that maps roughly to
dBm as `percent / 2 − 100`, so 48% ≈ −76 dBm: weak (section 11).

### Path, latency, loss and MTU

```powershell
# Ping + traceroute in one, as objects
Test-NetConnection app.example.com -TraceRoute

# TCP port test with name resolution details
Test-NetConnection app.example.com -Port 443 -InformationLevel Detailed

# Per-hop loss statistics (Windows' mtr); -n skips DNS, -q 50 queries per hop
pathping -n -q 50 app.example.com

# Latency and loss over 50 pings
ping -n 50 app.example.com

# MTU: -f sets Don't Fragment, -l is the payload (1472 + 28 = 1500)
ping -f -l 1472 app.example.com

# MTU of every interface (VPN adapters are often 1400 or lower)
netsh interface ipv4 show subinterfaces
```

```
PS> Test-NetConnection app.example.com -TraceRoute

ComputerName           : app.example.com
RemoteAddress          : 203.0.113.10
InterfaceAlias         : Ethernet
SourceAddress          : 192.168.1.50
PingSucceeded          : True
PingReplyDetails (RTT) : 42 ms
TraceRoute             : 192.168.1.1
                         198.51.100.1
                         0.0.0.0
                         203.0.113.10

PS> ping -f -l 1472 app.example.com
Pinging app.example.com [203.0.113.10] with 1472 bytes of data:
Packet needs to be fragmented but DF set.
Packet needs to be fragmented but DF set.
```

→ `0.0.0.0` in `TraceRoute` is a hop that did not answer (like `* * *`). `Packet
needs to be fragmented but DF set` means a smaller MTU on the path that *does*
report itself; plain timeouts at 1472 while smaller sizes work is the black hole
from Step 9. `pathping` is read exactly like mtr: only loss that continues to the
last hop is real (see the Windows reference for a sample).

### Request timing and DNS

Windows 10 1803+ ships the real curl as `curl.exe` (in Windows PowerShell 5.1,
plain `curl` is an alias for `Invoke-WebRequest`, so type the `.exe`).

```powershell
curl.exe -o NUL -s -w "dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} speed=%{speed_download}\n" https://app.example.com/

# DNS lookup time with a cold cache, and which DNS servers are configured
Clear-DnsClientCache
Measure-Command { Resolve-DnsName app.example.com -DnsOnly } | Select-Object TotalMilliseconds
Get-DnsClientServerAddress -AddressFamily IPv4
```

### TCP stack settings

```powershell
netsh interface tcp show global
Get-NetTCPSetting | Format-Table SettingName, AutoTuningLevelLocal, CongestionProvider
```

```
TCP Global Parameters
----------------------------------------------
Receive-Side Scaling State          : enabled
Receive Window Auto-Tuning Level    : disabled
Add-On Congestion Control Provider  : default
ECN Capability                      : disabled
RFC 1323 Timestamps                 : allowed
Initial RTO                         : 1000
Receive Segment Coalescing State    : enabled
```

→ **`Receive Window Auto-Tuning Level : disabled`** caps every download at a 64 KB
window: fine on the LAN, terrible over a WAN or VPN (6.5 Mbit/s at 80 ms, section
2). Someone disabled it with an old "speed tweak" guide. Restore it as
Administrator with `netsh interface tcp set global autotuninglevel=normal`.
`Receive-Side Scaling State: enabled` is the Windows equivalent of Step 13's
multi-queue spreading and should stay enabled.

### iperf3 and who is using the bandwidth

iperf3 is not built into Windows; the Windows builds are community-compiled, so
use one your organisation trusts. Commands are the same as on Linux.

```powershell
.\iperf3.exe -c 10.0.20.15 -t 10
.\iperf3.exe -c 10.0.20.15 -t 10 -R
.\iperf3.exe -c 10.0.20.15 -t 10 -P 4

# Running the SERVER on Windows: temporary firewall rule for one client, then remove it
New-NetFirewallRule -DisplayName "iperf3-test" -Direction Inbound -Protocol TCP -LocalPort 5201 -RemoteAddress 10.0.20.11 -Action Allow
.\iperf3.exe -s -1
Remove-NetFirewallRule -DisplayName "iperf3-test"

# Per-process network usage: Resource Monitor, Network tab, sort by Total (B/sec)
resmon

# Interface throughput counter, 5 samples
Get-Counter '\Network Interface(*)\Bytes Total/sec' -SampleInterval 1 -MaxSamples 5

# Which remote hosts hold the most connections?
Get-NetTCPConnection -State Established | Group-Object RemoteAddress | Sort-Object Count -Descending | Select-Object -First 10 Count, Name
```

Slow SMB copies from Windows: check `Get-SmbConnection` (the `Dialect` should be
3.x), whether SMB signing or encryption is forced (CPU cost on older hardware),
and for many small files use `robocopy SRC DST /E /MT:16` instead of Explorer.

**Next step:** if the adapter shows 100 Mbps or errors → Step 7 (cable, port).
If `pathping` shows loss continuing to the last hop → Step 3 rules and Scenario
A. If `ping -f -l` fails silently → Step 9 and Scenario D. If auto-tuning is
disabled → restore it and re-test. If all are clean → run the server-side steps
from Linux.

---

## 13. macOS: speed and latency tools

> 📚 **Study path:** 1) Note: [macOS reference](20-macos.md) · 2) Note: section 11 above (Wi-Fi, bufferbloat, remote users) · 3) KodeKloud: no macOS networking course in the verified map; the concepts are in *Networks and Communications* ([link](https://kodekloud.com/courses/networks-and-communications)) · 4) Practice: run `networkQuality` on Wi-Fi and then on a cable, with the VPN off and then on, and explain the four results.

**Level:** [L1 · Junior]. You collect the evidence from Mac users and remote
workers here.

macOS has the best built-in speed test of the three platforms
(`networkQuality`), and most Linux habits carry over. Basics are in the
[macOS reference](20-macos.md).

```bash
# macOS (Terminal), not Linux
# Capacity AND latency under load ("responsiveness"), macOS 12+
networkQuality
networkQuality -s            # sequential: upload and download measured separately
networkQuality -I en0        # force a specific interface (e.g. wired vs Wi-Fi)

# Wi-Fi details: RSSI, noise, transmit rate, channel
sudo wdutil info
system_profiler SPAirPortDataType | grep -E 'PHY Mode|Channel|Signal / Noise|Transmit Rate'

# Which interface/route is used (the macOS "ip route get"); utunN = VPN
route -n get 203.0.113.10

# Latency/loss, and an MTU test (-D sets Don't Fragment on macOS)
ping -c 50 -i 0.2 192.168.1.1
ping -c 3 -D -s 1472 203.0.113.10
networksetup -getMTU en0

# Interface errors (Ierrs/Oerrs) and per-process live traffic
netstat -ib -I en0
nettop -P -m tcp

# mtr and iperf3 from Homebrew (Homebrew's mtr needs sudo)
brew install mtr iperf3
sudo mtr -rwzbc 100 203.0.113.10
iperf3 -c 10.0.20.15 -t 10 -R

# DNS: resolver configuration and lookup time through the system resolver
scutil --dns | grep -E 'resolver|nameserver' | head -20
time dscacheutil -q host -a name app.example.com
```

```
$ networkQuality
==== SUMMARY ====
Uplink capacity: 21.344 Mbps
Downlink capacity: 286.120 Mbps
Responsiveness: Medium (146.341 milliseconds | 410 RPM)
Idle Latency: 24.500 milliseconds

$ sudo wdutil info
...
WIFI
    MAC Address          : (redacted)
    SSID                 : office-5g
    RSSI                 : -73 dBm
    Noise                : -91 dBm
    Tx Rate              : 144.0 Mbps
    Channel              : 5g36/80
    PHY Mode             : 11ac
...
```

**What it means:** (exact layout varies by macOS version)

- Capacity 286 down / 21 up is fine for most work. **Responsiveness "Medium"** with ~146 ms latency under load versus 24.5 ms idle is moderate **bufferbloat**: video calls and SSH will lag whenever someone uploads. RPM is round-trips per minute under load (60000 ÷ RPM = ms); more is better. In practice macOS labels results below about 200 RPM as Low and about 1000 RPM or more as High, with Medium in between.
- RSSI −73 dBm with noise −91 dBm gives an SNR of 18 dB: weak. Above ~25 dB SNR is comfortable. Move closer or use 5 GHz with less obstruction, or a cable.
- `route -n get` showing `interface: utun3` means the traffic goes through a VPN tunnel (section 11).
- `ping -D -s 1472` failing with `Message too long` = your own interface MTU is smaller; timeouts while smaller sizes work = black hole (Step 9).

**Next step:** if responsiveness is low → bufferbloat (section 11). If RSSI is
weak → fix the radio or use a cable. If traffic goes through `utunN` → Scenario
C. If all of these look fine → take the `mtr` and `iperf3` results to Steps 3–6.

---

## 14. Scenario A — Downloads from one site are slow

> 📚 **Study path:** 1) Note: Steps 1, 3 and 5 above · 2) KodeKloud: *Networks and Communications*, Network Troubleshooting module ([link](https://kodekloud.com/courses/networks-and-communications)) · 3) Read: [everything curl: Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html) for pinning one backend with `--resolve` · 4) Practice: time the same large file with `curl -w` from your server and from a KodeKloud *Ubuntu playground* ([link](https://kodekloud.com/playgrounds/playground-ubuntu)), then explain the difference.

**Level:** [L2 · Mid]. The L2 skill here is deciding, with evidence, whether
the problem belongs to the site, the ISP or your own egress.

**Ticket:** "`apt` / `docker pull` / `curl` from `mirror.example.com` runs at 2 MB/s
on web01. Everything else is fine." The question is whether the problem is that
site, the path to it, or your own egress (proxy, firewall, ISP).

### Step A1 — Measure the site against a known-good one

**Goal:** turn "slow" into a number and prove whether your host and uplink can go faster.

```bash
# The slow site
curl -o /dev/null -s -w 'speed=%{speed_download} B/s  ttfb=%{time_starttransfer}s  ip=%{remote_ip}\n' \
  https://mirror.example.com/images/big.iso
# A large file from somewhere you know is fast (your own server in another site, another mirror)
curl -o /dev/null -s -w 'speed=%{speed_download} B/s  ttfb=%{time_starttransfer}s  ip=%{remote_ip}\n' \
  https://files.example.org/test/1GB.bin
```

```
speed=2214093 B/s  ttfb=0.412s  ip=198.51.100.80
speed=103412557 B/s  ttfb=0.061s  ip=203.0.113.200
```

**What it means:** the slow site gives ~2.2 MB/s (≈18 Mbit/s); another site gives
~103 MB/s (≈830 Mbit/s). Your NIC, host and uplink are fine. The problem is
specific to the slow site or the path to it.

**Why this step (now):** without a comparison you cannot tell "my side is slow" from "their side is slow". It is cheap and uses the real protocol.

**Next step:** if *everything* is slow → it is not this scenario; go to Step 2 and Step 7. If only this site → Step A2.

### Step A2 — Check which server and address family you get

**Goal:** make sure you are talking to the server you think you are, over the address family you expect.

```bash
dig +short mirror.example.com A
dig +short mirror.example.com AAAA
curl -4 -o /dev/null -s -w 'v4 %{remote_ip} %{speed_download}\n' https://mirror.example.com/images/big.iso
curl -6 -o /dev/null -s -w 'v6 %{remote_ip} %{speed_download}\n' https://mirror.example.com/images/big.iso
# Pin each A record in turn (CDNs and mirror pools return several)
curl --resolve mirror.example.com:443:198.51.100.81 -o /dev/null -s -w '%{remote_ip} %{speed_download}\n' https://mirror.example.com/images/big.iso
```

```
198.51.100.80
198.51.100.81
2001:db8:80::80
v4 198.51.100.80 2231093
v6 2001:db8:80::80 61324551
198.51.100.81 58122004
```

**What it means:** one IPv4 backend (`.80`) is slow; the other IPv4 backend and the
IPv6 address are fast. Either one node of their pool is unhealthy, or the IPv4
route to it is poor. If *all* addresses are equally slow, the backend choice is
not the issue. Also check where the address is: a CDN that geolocates you by your
**resolver's** location (a corporate resolver in another country, or a public
resolver) may send you to a far-away edge; compare with `dig @YOUR_LOCAL_RESOLVER`.

**Why this step (now):** "the site" is often many servers. Finding that one backend or one address family is slow narrows the problem to something you can route around immediately.

**Next step:** if one backend is slow → you can pin a working one temporarily (`/etc/hosts` or a mirror list) and report the bad node to the operator; continue to A3 for evidence. If all are slow → Step A3.

### Step A3 — Check the path quality to that site

**Goal:** find loss or latency on the path, with evidence a provider will accept.

```bash
mtr -rwzbc 100 198.51.100.80
sudo mtr -T -P 443 -rwzbc 100 198.51.100.80
```

```
HOST: web01                                        Loss%   Snt   Last   Avg  Best  Wrst StDev
  1. AS???    _gateway (10.0.20.1)                  0.0%   100    0.4   0.4   0.3   0.9   0.1
  2. AS64500  198.51.100.1 (198.51.100.1)           0.0%   100    2.0   2.2   1.8   4.1   0.3
  3. AS64510  ix-peer.transit.example (192.0.2.33)  3.0%   100   61.2  64.8  58.9 121.4  11.2
  4. AS64520  198.51.100.70 (198.51.100.70)         3.0%   100   62.0  65.1  59.4 118.0  10.9
  5. AS64520  198.51.100.80 (198.51.100.80)         4.0%   100   62.4  65.6  59.8 125.3  11.4
```

**What it means:** 3–4% loss and rising jitter start at hop 3 (the interconnect into
AS64510) and persist to the destination. Read Step 3 for the rules. Loss on a
~60 ms path holds one loss-based TCP stream far below line rate (section 2's Mathis
formula), which fits the 18 Mbit/s you see. Treat mtr's percentage as evidence of
*where* the loss starts, not as TCP's exact loss rate: 100 ICMP probes are a coarse
sample, and a literal 3% in the formula would predict under 2 Mbit/s.

**Why this step (now):** it tells you who owns the problem. Loss inside your network is yours; loss at an interconnect belongs to your ISP or their peer; loss only at the last hop is the site.

**Next step:** if loss starts inside your own network → Step 10 and Step 11 on your edge. If it starts at the ISP or beyond → Step A4 (to know whether parallel transfers work around it) and open a ticket with mtr output from both directions. If the path is clean → Step A4.

### Step A4 — Compare one stream with several

**Goal:** decide whether the limit is per connection (server throttling, window × RTT, loss) or for the whole path.

```bash
URL=https://mirror.example.com/images/big.iso
# One stream
curl -o /dev/null -s -w 'single %{speed_download}\n' $URL
# Four parallel range requests of 256 MiB each (the server must support Range)
for i in 0 1 2 3; do
  curl -o /dev/null -s -r $((i*268435456))-$(((i+1)*268435456-1)) -w "part$i %{speed_download}\n" $URL &
done; wait
# While a download runs, in another terminal. On a DOWNLOAD this host is the
# receiver: cwnd and retrans here describe our own (tiny) sending side, so read
# the receive-side fields (rcv_space, rcv_rtt, rcv_ooopack). The sender's cwnd and
# retransmits are only visible with ss on the server.
ss -tin dst 198.51.100.80
```

```
single 2214093
part0 2198112
part2 2203771
part1 2187345
part3 2210038

ESTAB 0 0 10.0.20.11:51234 198.51.100.80:443
	 cubic wscale:7,7 rto:268 rtt:64.8/9.1 mss:1448 ... bytes_received:118734210 ... rcv_rtt:66.2 rcv_space:2453120 rcv_ssthresh:3145728 minrtt:59.4 rcv_ooopack:1873
```

**What it means:** each of four connections gets the same ~2.2 MB/s, so together
they reach ~8.8 MB/s. A per-connection cap that is this *even* usually means the
**server throttles per connection**. On our receiving side, `rcv_space` (~2.4 MB of
receive window) is far more than 2.2 MB/s × 65 ms ≈ 140 KB needs, so our window is
not the limit, while a climbing `rcv_ooopack` (segments arriving out of order after
losses) shows the path loss from Step A3 is involved too. If parallel streams
scale linearly, the path has spare capacity and the limit is per flow.

**Why this step (now):** it decides the workaround: parallel downloads (aria2c, `docker` pulls layers in parallel already, S3 multipart) help with per-flow limits, but not with a congested path.

**Next step:** if parallel scales → per-flow limit: use parallel tools, ask the operator about throttling, consider BBR if *you* own the sending server. If parallel does not scale → Step A5.

### Step A5 — Test from outside and bypass your egress

**Goal:** separate "this site is slow for everyone" from "our proxy/firewall/ISP is slow to this site".

```bash
# Through and around the corporate proxy (if one is configured)
curl -o /dev/null -s -w 'proxy   %{speed_download}\n' https://mirror.example.com/images/big.iso
curl --noproxy '*' -o /dev/null -s -w 'noproxy %{speed_download}\n' https://mirror.example.com/images/big.iso
# The same command from a host on a different network (a cloud VM, another office)
curl -o /dev/null -s -w 'cloud   %{speed_download}\n' https://mirror.example.com/images/big.iso
```

```
proxy   2214093
noproxy 2209876
cloud   97551230
```

**What it means:** from a cloud VM the same site delivers ~97 MB/s, while from your
network it is ~2.2 MB/s with or without the proxy. The site is fine; the path from
your ISP to it (Step A3 showed loss at the interconnect) is the problem. If the
proxy number were much lower than `noproxy`, the proxy (SSL inspection, antivirus
scanning, a small proxy box) would be the bottleneck instead.

**Why this step (now):** it is the final split between "their problem" and "our egress". Providers and site operators respond far faster when you can say "fast from AWS, slow from our ISP, here is mtr both ways".

**Next step:** slow from everywhere → the site: contact its operator, use another mirror. Fast elsewhere, slow from you → open an ISP ticket with A3/A5 evidence; meanwhile use another mirror or a cache.

#### Scenario A decision tree

```
Only one site slow?
├── No, everything is slow ──────────────> Step 2 / Step 7 (local problem)
└── Yes
    ├── One backend / one IP family slow ─> pin a good one, report the bad node
    ├── mtr: loss starts inside our net ──> Step 10/11 on our edge
    ├── mtr: loss starts at ISP/transit ──> ISP ticket with mtr both ways
    ├── parallel streams scale ───────────> per-flow limit: parallel tools / BBR on our senders
    ├── proxy slower than --noproxy ──────> proxy capacity / SSL inspection
    └── fast from cloud, slow from us ────> our ISP path: ticket + alternate mirror
```

#### Scenario A fix and verify

- Use a mirror or backend that tests fast (`/etc/apt/sources.list.d/`, a registry mirror), or pin the good IP *temporarily* in `/etc/hosts` with a comment and a ticket number.
- If you control the sending server: BBR on that server (section 8).
- For package and image downloads, run a local cache so only one copy crosses the slow path: `apt-cacher-ng` for apt, and a **Harbor proxy-cache project** for Docker Hub and other registries.
- **Verify** with the exact Step A1 command and record the before/after numbers in the ticket.

#### Scenario A rollback

Remove any temporary `/etc/hosts` pin as soon as the provider fixes the path
(stale pins cause outages when the IP changes later). Revert sysctl changes with
section 8's rollback.

#### Scenario A prevention

- Monitor the external endpoints you depend on with a Prometheus **blackbox exporter** HTTP probe (section 21) so you see the degradation before users do.
- Keep caches (apt, registries) close to the consumers.
- Keep one `curl -w` baseline per critical external dependency in the runbook.

---

## 15. Scenario B — LAN file copy is slow

> 📚 **Study path:** 1) Note: Step 7 above and [Storage & disk](01-storage-disk.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*, Monitor Storage Performance lesson ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) · 3) Note: [SSH & remote access](09-ssh-remote-access.md) for ciphers, scp and rsync · 4) Practice: copy a 2 GB file between two test VMs, first with `-c chacha20-poly1305@openssh.com` and then with `-c aes128-gcm@openssh.com`, and compare the rates with iperf3.

**Level:** [L1–L2 · Junior → Mid]. A junior can do the B1 arithmetic and the
`ethtool` check. Separating network, disk and tool (B3–B5) is L2.

**Ticket:** "Copying a 20 GB backup from app01 to backup01 (same datacenter) runs at
about 11 MB/s. It used to be much faster." A copy involves the source disk, the
copy tool (often encrypting), the network, and the destination disk. Test each
one alone.

### Step B1 — Translate the number into bits

**Goal:** see whether the speed matches a suspicious "round" link speed.

```bash
# Watch the copy's real rate (rsync shows overall progress)
rsync -a --info=progress2 /srv/backup/db.dump backup01:/data/backups/
```

```
  4,912,312,320  24%   11.21MB/s    0:22:41
```

**What it means:** 11.2 MB/s × 8 ≈ **90 Mbit/s**. That is what a 100 Mbit/s link
delivers after overhead (section 2's units table). A gigabit path would give
100+ MB/s, so something in the path probably negotiated 100 Mbit/s.

**Why this step (now):** a 30-second calculation that often names the culprit before you run a single diagnostic.

**Next step:** ~11 MB/s → Step B2 first. Any other number → Step B3.

### Step B2 — Check link speed and duplex on both hosts

**Goal:** confirm both NICs (and the switch ports, with the network team) are at full speed and full duplex.

```bash
# On app01 AND on backup01
sudo ethtool eno1 | grep -E 'Speed|Duplex|Auto-negotiation|Link detected'
ip -s link show eno1
```

```
app01:      Speed: 1000Mb/s   Duplex: Full   Auto-negotiation: on   Link detected: yes
backup01:   Speed: 100Mb/s    Duplex: Full   Auto-negotiation: on   Link detected: yes
```

**What it means:** backup01 linked at 100 Mbit/s full duplex: a cable with a broken
pair, a 100 Mbit/s-only switch port or patch panel, or a misbehaving NIC. Step 7
explains how to read the counters (CRC errors point to the cable).

**Why this step (now):** the number from B1 points straight at a link-speed fault, and this check is read-only and takes seconds on both ends.

**Next step:** if a link is at 100 Mbit/s or half duplex → replace cable/patch port, set the switch port to auto, verify with `ethtool`, then Step B3 to confirm. If both are at 1000/Full → Step B3.

### Step B3 — Measure the network alone with iperf3

**Goal:** know what the network between the two hosts can do with disks and tools removed.

```bash
# backup01 (server):
iperf3 -s -1
# app01 (client), both directions:
iperf3 -c backup01 -t 10
iperf3 -c backup01 -t 10 -R
```

```
[  5]   0.00-10.00  sec  1.09 GBytes   937 Mbits/sec    0             sender
[  5]   0.00-10.00  sec  1.09 GBytes   935 Mbits/sec                  receiver
```

**What it means:** after the cable fix (or if B2 was clean) the network does ~935
Mbit/s ≈ 117 MB/s both ways. If the copy is still slow, the network is innocent:
it is a disk or the tool. If iperf3 is low, go through Steps 7–13 on both hosts.

**Why this step (now):** it is the single test that separates network from everything else for a host-to-host copy.

**Next step:** network fast → Step B4 (disks). Network slow → Steps 7, 8, 10 and 13 on both hosts, and ask whether the path crosses a firewall or router between VLANs (Step B5's last point).

### Step B4 — Test the disks on both ends

**Goal:** measure how fast the source can read and the destination can write, without the network.

```bash
# Source: sequential read of the real file, thrown away (safe: reads only)
dd if=/srv/backup/db.dump of=/dev/null bs=1M status=progress

# Destination: sequential write test into a scratch file in the target directory
# (fio is not installed by default: sudo apt install fio; iostat comes with sysstat)
fio --name=seqwrite --directory=/data/backups --rw=write --bs=1M --size=4G \
    --direct=1 --numjobs=1 --group_reporting
# then delete ONLY the scratch file fio created
rm /data/backups/seqwrite.0.0

# While a copy runs: is a disk at 100% util with long waits?
iostat -xz 1 5
```

> ⚠️ `dd` is safe here **only** because `of=` is `/dev/null`. Never point `of=` at a
> device (`/dev/sdX`): it overwrites the disk. For write tests, use `fio` into a
> scratch file in a directory, as above.

```
$ dd if=/srv/backup/db.dump of=/dev/null bs=1M status=progress
20401094656 bytes (20 GB, 19 GiB) copied, 51 s, 400 MB/s

$ fio ... (summary)
  WRITE: bw=38.2MiB/s (40.1MB/s), io=4096MiB (4295MB), run=107214-107214msec

$ iostat -xz 1 5   (on backup01)
Device   r/s     w/s    rkB/s    wkB/s  ...  w_await  aqu-sz  %util
sdb     0.00  312.00     0.00 39936.00  ...    41.20   12.80  99.60
```

**What it means:** the source reads at 400 MB/s, but the destination disk only
writes ~40 MB/s and sits at 99.6% util with 41 ms write waits. Even with a perfect
network the copy cannot beat ~40 MB/s: the backup disk (a slow RAID rebuild, an
SMR drive, a degraded array, a nearly full filesystem) is the bottleneck. See
[Storage & disk](01-storage-disk.md) and [Why is the system slow?](23-playbook-slow-system.md).

**Why this step (now):** once the network is proven fast, the disks are the next most common bottleneck, and they are often forgotten because "it is a network copy".

**Next step:** a disk is slower than the network → fix or accept the disk limit. Disks and network both fast but the copy slow → Step B5.

### Step B5 — Test the copy tool and the protocol

**Goal:** find overhead from encryption, compression, per-file costs or protocol settings.

```bash
# scp/rsync over SSH encrypt everything on ONE core per connection: watch it
top -o %CPU          # ssh or sshd at ~100% = cipher-bound

# Which cipher is used, and is AES hardware acceleration available?
ssh -v backup01 true 2>&1 | grep -i 'cipher'
grep -o -m1 -w aes /proc/cpuinfo

# Faster: an AES-GCM cipher, no compression on a LAN, rsync whole files
rsync -a --info=progress2 -e 'ssh -c aes128-gcm@openssh.com -o Compression=no' \
  /srv/backup/db.dump backup01:/data/backups/

# Many small files: stream one tar instead of per-file round-trips
tar -C /srv/backup -cf - . | ssh backup01 'tar -C /data/backups -xf -'

# NFS client: check negotiated rsize/wsize, protocol version and sync mode
nfsstat -m
```

Example from a pair of hosts whose disks tested fast in Step B4:

```
$ top -o %CPU            (while scp runs)
    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
  48211 backup    20   0   15432   7112   5920 R  99.3   0.1   2:41.07 ssh

$ ssh -v backup01 true 2>&1 | grep -i 'cipher'
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none

$ grep -o -m1 -w aes /proc/cpuinfo
aes

$ rsync -a --info=progress2 -e 'ssh -c aes128-gcm@openssh.com -o Compression=no' ...
 20,401,094,656 100%  108.92MB/s    0:02:58 (xfr#1, to-chk=0/1)
```

**What it means:**

- Here `ssh` sits at 99% of one core with `chacha20-poly1305`, and the CPU has AES-NI (`aes` flag). Switching to `aes128-gcm` lifted the copy to ~109 MB/s, i.e. line rate. The network was never the problem.
- `ssh` at 100% of one core → the transfer is CPU-bound on encryption. `chacha20-poly1305` (a common default) is slower than `aes128-gcm` on CPUs with AES-NI. On old CPUs, this alone caps copies at 50–150 MB/s.
- `Compression=yes` on a fast LAN *slows* transfers: the CPU compresses slower than the wire sends.
- Thousands of small files → per-file latency dominates; `tar | ssh` or `rsync` of a single archive is much faster.
- NFS with small `rsize/wsize`, `sync` exports, or NFSv3 over UDP → poor throughput; SMB with forced signing/encryption → CPU-bound on the server.
- If the two servers are in **different VLANs**, the copy may be routed through a firewall that inspects every packet at far less than line rate. `tracepath -n backup01` showing a firewall hop between two "local" servers is the giveaway.

**Why this step (now):** after network and disks are cleared, the tool and protocol are what remains. Changing the cipher or tool is cheap and reversible.

**Next step:** tool overhead found → change the tool/cipher and re-measure. A firewall hop between VLANs → talk to the network team about a direct path or a higher-capacity inspection policy.

#### Scenario B decision tree

```
Copy slow between two LAN hosts
├── ~11 MB/s? ──────────────────────> ethtool both ends: 100 Mbit/s or half duplex? -> cable/port
├── iperf3 slow ────────────────────> Steps 7-13 on both hosts; firewall between VLANs?
├── iperf3 fast
│   ├── destination write slow ─────> disk problem (01-storage-disk.md, 23-playbook)
│   ├── source read slow ───────────> disk problem on the source
│   └── disks fast
│       ├── ssh at 100% CPU ────────> faster cipher, no compression
│       ├── many small files ───────> tar | ssh, rsync, archives
│       └── NFS/SMB ────────────────> mount options, signing/encryption cost
└── fixed? -> re-run B1 and record the new number
```

#### Scenario B fix and verify

Replace the cable or patch port, set both NIC and switch port to autonegotiate,
and confirm `Speed: 1000Mb/s` / `Duplex: Full` with `ethtool`. Then repeat B3
(iperf3) and the original copy (B1). Record both numbers.

#### Scenario B rollback

Cable swaps and cipher choices have no persistent state. If you forced speed or
duplex during testing (`ethtool -s`), set it back to `autoneg on`; forced settings
on one side only are exactly what causes duplex mismatches.

#### Scenario B prevention

- Alert when `node_network_speed_bytes` drops below the expected speed and when interface error counters increase (section 21).
- Keep a host-to-host iperf3 baseline for backup and storage paths.
- Label patch cables and ports; log every cabling change.

---

## 16. Scenario C — VPN users are slow

> 📚 **Study path:** 1) Note: section 11 and Step 9 above · 2) Note: [Learn: networking](28-learn-networking.md), section 12 (VPNs, overlays and MTU) · 3) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*, Port Redirection and NAT lesson ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) for routing through a gateway (KodeKloud has no WireGuard course) · 4) Practice: build WireGuard between two test VMs, leave the tunnel MTU too high, and reproduce Step C3.

**Level:** [L2 · Mid]. The diagnosis is L2. Changing the tunnel mode (full or
split) is a security and architecture decision that a senior takes with the
security team.

**Ticket:** "Since we moved to the new VPN, home workers say GitLab and internal apps
are slow; video calls stutter." The VPN adds a tunnel (MTU), encryption (CPU), a
concentrator (shared uplink) and often a full tunnel (internet hairpin) to every
user's path, on top of their home Wi-Fi and ISP.

### Step C1 — Compare the same user with and without the VPN

**Goal:** separate the user's own connection from the VPN.

```bash
# Linux/macOS client (Windows: curl.exe, same flags). Ask the user to run both.
curl -o /dev/null -s -w 'public  %{speed_download}\n' https://files.example.org/test/100MB.bin   # VPN off
curl -o /dev/null -s -w 'via-vpn %{speed_download}\n' https://files.example.org/test/100MB.bin   # VPN on
curl -o /dev/null -s -w 'internal %{time_total}s\n' https://gitlab.corp.example/users/sign_in   # VPN on: page time
```

```
public  11532001        (VPN off: ~92 Mbit/s, their line is fine)
via-vpn  1843210        (VPN on:  ~15 Mbit/s for the same public file)
```

**What it means:** the user's internet connection is fine; turning the VPN on drops
the same download from ~92 to ~15 Mbit/s. The VPN path is the bottleneck. If the
number was low with the VPN off as well, the user's connection or Wi-Fi is the
problem (Step C5).

**Why this step (now):** it is the only test that cleanly splits "their home network" from "our VPN", and users can run it without admin rights.

**Next step:** slow only with VPN → Step C2. Slow without VPN too → Step C5.

### Step C2 — Check for a full tunnel

**Goal:** find out if the VPN is a full tunnel that hairpins all internet traffic through HQ.

```bash
# Linux client
ip route get 1.1.1.1
ip route get 10.20.0.15        # an internal server
```

```bash
# macOS client (Terminal), not Linux
route -n get 1.1.1.1
```

```powershell
# Windows client
Find-NetRoute -RemoteIPAddress 1.1.1.1 | Select-Object InterfaceAlias, NextHop
```

```
$ ip route get 1.1.1.1
1.1.1.1 dev wg0 table 51820 src 10.8.0.23 uid 1000
    cache
```

**What it means:** traffic to a public address goes into `wg0`: this is a **full
tunnel**. Every video call, software update and web page goes home → HQ → internet
→ HQ → home, sharing the HQ uplink with every other user, and paying the VPN's
latency and MTU penalties. With split tunnelling, only internal prefixes would use
`wg0`.

**Why this step (now):** full tunnels are the most common reason for "everything got slower with the VPN", and they explain why video calls suffer even though they have nothing to do with internal apps.

**Next step:** full tunnel → consider split tunnelling for high-volume SaaS (a security decision, agree it with the security team), and check the HQ uplink in Step C4. Split tunnel already → Step C3.

### Step C3 — Check the MTU through the tunnel

**Goal:** make sure full-size packets cross the tunnel, or are clamped correctly.

```bash
ip link show wg0                                   # tunnel MTU
ping -c 3 -M do -s 1392 10.20.0.15                 # 1420-byte packet to an internal host
ping -c 3 -M do -s 1352 10.20.0.15                 # 1380-byte packet
tracepath -n 10.20.0.15
```

```
4: wg0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000

--- 10.20.0.15 ping statistics ---           (1392 payload)
3 packets transmitted, 0 received, 100% packet loss
--- 10.20.0.15 ping statistics ---           (1352 payload)
3 packets transmitted, 3 received, 0% packet loss
```

**What it means:** the tunnel's MTU is 1420, but 1420-byte packets do not arrive while
1380-byte packets do. WireGuard adds 60 bytes of outer headers over IPv4 and 80
over IPv6, so a 1420-byte inner packet becomes a 1500-byte outer packet when the
user reaches the gateway over IPv6. Their home line carries less than 1500 (PPPoE
1492, DS-Lite, many LTE links), so those packets are dropped. Large transfers stall
or crawl; small requests work (Scenario D explains the mechanism).

**Why this step (now):** VPN MTU problems produce exactly the "some things work, big things crawl" complaint, and the test takes a minute.

**Next step:** MTU too big → lower the tunnel MTU (WireGuard `MTU = 1380` in the client config; for other VPNs, their MTU/MSS setting) and/or clamp MSS on the VPN gateway (section 8). MTU fine → Step C4.

### Step C4 — Check the VPN server's CPU and uplink

**Goal:** see whether the concentrator is the bottleneck for everybody.

```bash
# On the VPN server during working hours
mpstat -P ALL 1 5                     # one core at 100% = single-threaded crypto
top -o %CPU                           # openvpn, charon (strongSwan), or kernel softirq
sudo wg show                          # WireGuard: per-peer transfer counters
sudo iftop -i eno1 -nNP -t -s 10      # uplink usage
vnstat -i eno1 -h                     # uplink history by hour
```

```
10:42:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:42:02       0   97.00    0.00    3.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00
10:42:02       1    4.00    0.00    2.00    0.00    0.00    1.00    0.00    0.00    0.00   93.00

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 1123 nobody    20   0   68412  21004   7720 R  99.7   0.5 812:14.33 openvpn
```

**What it means:** a single OpenVPN process pins CPU0 at ~100% while other cores
idle. Classic OpenVPN handles all clients of one instance in one thread, so the
whole VPN is limited by one core's crypto speed (often a few hundred Mbit/s in
total, shared by everyone). If instead the uplink is at its capacity in `iftop` /
`vnstat`, the HQ internet link is saturated (very likely with a full tunnel).

**Why this step (now):** once one user's path is understood, check the shared component; a saturated concentrator explains complaints from *everyone* at peak hours.

**Next step:** CPU-bound → run several VPN instances/ports, enable the VPN's kernel offload (OpenVPN DCO) where supported, move to a kernel-based VPN (WireGuard, IPsec), or bigger hardware. Uplink saturated → split tunnel, QoS, or more bandwidth. Neither → Step C5.

### Step C5 — Check the user's last mile

**Goal:** rule out home Wi-Fi, ISP congestion and bufferbloat.

```bash
# Ask the user (macOS shown; Windows: netsh wlan show interfaces / pathping)
networkQuality                         # capacity + responsiveness under load
sudo wdutil info | grep -E 'RSSI|Noise|Tx Rate|Channel'
ping -c 60 192.168.1.1                 # home router: Wi-Fi quality
sudo mtr -rwzbc 100 VPN_GATEWAY_PUBLIC_IP
```

```
$ networkQuality
==== SUMMARY ====
Uplink capacity: 9.871 Mbps
Downlink capacity: 94.220 Mbps
Responsiveness: Low (412.371 milliseconds | 145 RPM)
Idle Latency: 21.000 milliseconds

$ ping -c 60 192.168.1.1
...
--- 192.168.1.1 ping statistics ---
60 packets transmitted, 57 packets received, 5.0% packet loss
round-trip min/avg/max/stddev = 1.912/38.441/412.003/71.880 ms
```

**What it means:** in this example the user loses 5% of pings to their **own home
router** with up to 412 ms delay: the Wi-Fi is poor before any VPN or ISP is
involved. Latency under load of 412 ms against 21 ms idle is also severe
bufferbloat on a 10 Mbit/s uplink. In general: loss or jitter to the home router → Wi-Fi (section 11). Clean to
the router but loss starting at the ISP toward your VPN gateway → their ISP path.
"Responsiveness: Low" with fine capacity → bufferbloat on their router: calls lag
whenever someone at home uploads.

**Why this step (now):** after the VPN itself is cleared, the remaining variable is the user's environment, which you cannot see without their help.

**Next step:** Wi-Fi → move closer, 5 GHz, or cable. Bufferbloat → enable SQM/QoS on the home router if possible. ISP → the user contacts their ISP with the mtr output.

#### Scenario C decision tree

```
VPN users slow
├── slow even with VPN off ─────────> their Wi-Fi / ISP (C5)
└── slow only with VPN on
    ├── full tunnel + HQ uplink busy ─> split tunnel / more bandwidth / QoS
    ├── DF ping through tunnel fails ─> lower tunnel MTU + MSS clamp on gateway
    ├── VPN daemon at 100% of a core ─> scale out / kernel VPN / offload
    ├── internal DNS slow over VPN ───> Step 14 on the client, split DNS
    └── TCP-mode VPN on lossy links ──> switch transport to UDP
```

#### Scenario C fix and verify

Apply one change at a time (MTU/MSS first: cheapest and most common), then ask the
same pilot users to repeat C1 with and without the VPN. Keep their before/after
numbers in the ticket.

#### Scenario C rollback

Keep the previous VPN client profile and gateway config in version control. MTU
and MSS changes are config lines: revert the line and restart the service. Split
tunnel changes should go through the security team's change process, with the
old route set documented.

#### Scenario C prevention

- Monitor the concentrator's CPU per core, uplink utilisation and active sessions.
- Probe internal apps from a test client *through* the VPN with the blackbox exporter.
- Document the tunnel MTU and the MSS clamp in the VPN runbook.

---

## 17. Scenario D — SSH works but scp or large transfers hang

> 📚 **Study path:** 1) Note: Step 9 above · 2) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) before Step D3 · 3) KodeKloud: *Learning Linux Basics Course & Labs*, IPTABLES Introduction lesson ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)), so you can read the rule that drops ICMP · 4) Practice: the "MTU black hole" drill in section 22, timed: under 15 minutes from symptom to proof.

**Level:** [L2 · Mid]. This is a classic L2 interview and on-call scenario.
You prove it with a DF ping bisect and a capture, not by guessing.

**Ticket:** "I can SSH into the server in the other site and run commands, but
`scp` of a 50 MB file stalls at 0%, `git clone` hangs, and `docker pull` never
finishes. Ping works." This is almost always a **PMTUD black hole** (Step 9).

### Step D1 — Characterise the hang

**Goal:** confirm the pattern "small works, large stalls" with concrete commands.

```bash
# Small vs large over the same path
ssh deploy@203.0.113.40 'echo ok'                         # works
ssh deploy@203.0.113.40 'seq 1 100000'                    # a large burst of output: hangs?
scp -v ./bigfile.tar deploy@203.0.113.40:/tmp/            # stalls?

# HTTPS: does the handshake stall after "Client hello" (large certificate packets)?
curl -v https://203.0.113.40/ 2>&1 | head -20
```

```
$ ssh deploy@203.0.113.40 'echo ok'
ok
$ ssh deploy@203.0.113.40 'seq 1 100000'
1
2
...
5821
(no further output)

$ curl -v https://203.0.113.40/
*   Trying 203.0.113.40:443...
* Connected to 203.0.113.40 (203.0.113.40) port 443
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
(hangs)
```

**What it means:** short exchanges work; as soon as one side sends full-size
packets (bulk command output, file data, a certificate chain), the transfer
stops. Throughput "slowness" would still make progress; this **stops**. That is
the black-hole signature.

**Why this step (now):** it distinguishes "slow" (bandwidth, loss) from "stuck" (MTU) before you waste time on throughput tests.

**Next step:** pattern confirmed → Step D2. Transfers progress slowly instead of stopping → Steps 2–8.

### Step D2 — Bisect the path MTU with DF pings

**Goal:** find the largest packet that crosses the path.

```bash
for s in 1472 1452 1432 1412 1392 1372 1352 1332; do
  if ping -c 1 -W 1 -M do -s $s 203.0.113.40 >/dev/null 2>&1; then
    echo "OK   payload $s -> packet $((s+28))"
  else
    echo "FAIL payload $s -> packet $((s+28))"
  fi
done
```

```
FAIL payload 1472 -> packet 1500
FAIL payload 1452 -> packet 1480
FAIL payload 1432 -> packet 1460
FAIL payload 1412 -> packet 1440
FAIL payload 1392 -> packet 1420
OK   payload 1372 -> packet 1400
OK   payload 1352 -> packet 1380
OK   payload 1332 -> packet 1360
```

**What it means:** 1400-byte packets pass, 1420 do not, and no "Frag needed"
message came back: the path MTU is between 1400 and 1419 (for example an IPsec
site-to-site tunnel at 1400), and something drops the ICMP that should say so.

**Why this step (now):** it proves the hypothesis with numbers and gives you the value you need for the fix.

**Next step:** → Step D3 to see it on the wire (evidence for the network team), or straight to D4 if you just need to confirm the fix.

### Step D3 — Watch the stall on the wire

**Goal:** show full-size segments being retransmitted with no ICMP coming back.

```bash
# Terminal 1: TCP to the remote host, and any ICMP "too big" messages
sudo tcpdump -ni eno1 'host 203.0.113.40 and (tcp or icmp)'
# Terminal 2: reproduce
scp ./bigfile.tar deploy@203.0.113.40:/tmp/
# Terminal 3: the TCP view of the stuck connection
ss -tin dst 203.0.113.40
```

```
10:31:02.114 IP 10.0.20.11.51822 > 203.0.113.40.22: Flags [.], seq 38913:40361, ack 3302, win 501, length 1448
10:31:02.114 IP 10.0.20.11.51822 > 203.0.113.40.22: Flags [.], seq 40361:41809, ack 3302, win 501, length 1448
10:31:02.432 IP 10.0.20.11.51822 > 203.0.113.40.22: Flags [.], seq 38913:40361, ack 3302, win 501, length 1448
10:31:03.072 IP 10.0.20.11.51822 > 203.0.113.40.22: Flags [.], seq 38913:40361, ack 3302, win 501, length 1448
10:31:04.352 IP 10.0.20.11.51822 > 203.0.113.40.22: Flags [.], seq 38913:40361, ack 3302, win 501, length 1448

ESTAB 0 1209800 10.0.20.11:51822 203.0.113.40:22
	 cubic ... mss:1448 pmtu:1500 ... cwnd:1 ssthresh:7 ... retrans:1/9 ... lost:12 ...
```

**What it means:** the same 1448-byte segment (`seq 38913:40361`) is retransmitted
with doubling gaps (0.3 s, 0.6 s, 1.3 s): exponential backoff. No ICMP appears.
`ss` shows `pmtu:1500` (the kernel never learned the smaller MTU), `cwnd:1` and a
growing `Send-Q`. Small packets (ACKs, keystrokes) still pass, which is why SSH
"works". With TSO active, tcpdump may show larger "super-packets" on the sender;
the retransmission pattern is the same.

**Why this step (now):** it is the evidence that convinces a network team ("your device drops ICMP type 3 code 4") and it rules out any other cause.

**Next step:** → Step D4.

### Step D4 — Prove the fix with a temporary per-route MTU

**Goal:** confirm that smaller packets fix the transfer, without changing anything permanently or globally.

```bash
# A more specific route for just this destination, with a lower MTU (runtime only)
sudo ip route add 203.0.113.40/32 via 10.0.20.1 dev eno1 mtu 1400
ip route get 203.0.113.40
scp ./bigfile.tar deploy@203.0.113.40:/tmp/

# Remove the test route afterwards (it also disappears at reboot)
sudo ip route del 203.0.113.40/32 via 10.0.20.1 dev eno1 mtu 1400
```

```
203.0.113.40 via 10.0.20.1 dev eno1 src 10.0.20.11 uid 1000
    cache mtu 1400
bigfile.tar                         100%   50MB  38.2MB/s   00:01
```

**What it means:** with a 1400 MTU toward that host, `scp` completes at full speed.
The diagnosis is confirmed. This per-route change affects only one destination,
which is much safer than changing the MTU of `eno1` on a remote server.

**Why this step (now):** you change one variable in the narrowest possible scope and see the symptom disappear, which is the strongest proof you can have before a permanent fix.

**Next step:** → Step D5 to fix it where it belongs.

### Step D5 — Fix it in the layer that owns the MTU

**Goal:** apply the permanent fix at the right place.

```bash
# Who drops the ICMP? Check your own firewalls first: is ICMP allowed in and forwarded?
sudo nft list ruleset | grep -iE 'icmp|reject|drop'
sudo ufw status verbose

# Is a tunnel or overlay on this host involved?
ip -br link | grep -E 'wg|tun|vti|ipsec|vxlan|flannel|cali|docker|br-'
```

```
$ sudo nft list ruleset | grep -iE 'icmp|reject|drop'
		ip protocol icmp drop
		meta l4proto ipv6-icmp drop
		policy drop;

$ ip -br link | grep -E 'wg|tun|vti|ipsec|vxlan|flannel|cali|docker|br-'
vti0@NONE        UNKNOWN        <NOARP,UP,LOWER_UP>
docker0          DOWN           <NO-CARRIER,BROADCAST,MULTICAST,UP>
```

**What it means and what to change, in order of preference:** in this example a
custom "hardening" rule on *our own* gateway drops **all** ICMP and ICMPv6, and the
site-to-site traffic leaves through an IPsec VTI (`vti0`) with a smaller MTU. The
ICMP rule is what turns a normal MTU reduction into a black hole (and dropping
all ICMPv6 also breaks IPv6 neighbour discovery). The fixes:

1. **Allow the ICMP** that PMTUD needs on every firewall in the path: IPv4 ICMP type 3 code 4 ("fragmentation needed") and ICMPv6 type 2 ("packet too big"). UFW and default nftables setups on Ubuntu allow these; custom "drop all ICMP" rules and some appliances do not.
2. **Clamp TCP MSS** on the tunnel endpoint or router (section 8). It fixes all TCP through that device even when ICMP stays blocked elsewhere.
3. **Set the correct MTU on the tunnel/overlay itself**: IPsec/WireGuard interface MTU, Docker network MTU, CNI MTU (section 10). Lowering a physical interface's MTU is the last resort.
4. On hosts you cannot otherwise fix, `net.ipv4.tcp_mtu_probing = 1` lets TCP find a working size after a black hole is detected.

**Why this step (now):** the per-route test proved the cause; now the fix goes to the component that is actually wrong, so every host and protocol benefits, not just the one you tested.

**Next step:** after the change, repeat D1 and D2 from the affected host. Then remove any temporary per-route MTU.

#### Scenario D decision tree

```
Small works, large stalls
├── DF ping 1472 OK? ── yes ──> not MTU; transfers slow rather than stuck -> Steps 2-8
└── no
    ├── "Frag needed (mtu = N)" received ──> PMTUD works; app/UDP ignores it, or DF cleared
    ├── "local error: message too long" ───> our own interface (tunnel) MTU is N: expected
    └── silence (black hole)
        ├── per-route mtu test fixes it ───> confirmed
        ├── our firewall drops ICMP ───────> allow type 3 code 4 / ICMPv6 type 2
        ├── tunnel/overlay we own ─────────> set its MTU + MSS clamp
        └── someone else's device ─────────> ticket with D2/D3 evidence; clamp MSS meanwhile
```

#### Scenario D fix and verify

After the permanent fix: `ping -M do -s 1472` (or the largest size the path should
carry) succeeds, `ss -ti` shows the expected `pmtu`, and `scp`, `git clone` and
`curl -v` complete. Test from a container too if Docker is involved.

#### Scenario D rollback

`sudo ip route del` the test route. For netplan MTU changes use `sudo netplan try`
(auto-reverts after 120 s if you lose access). For nftables, keep the previous
`/etc/nftables.conf` and restore it with `sudo nft -f /etc/nftables.conf.bak`.

#### Scenario D prevention

- Write down the MTU of every segment and tunnel in the network documentation (including PPPoE lines and the IPsec tunnels between sites).
- Never deploy "block all ICMP" firewall policies; allow the PMTUD types explicitly.
- Probe with DF set: the blackbox exporter's ICMP module can send large packets with the don't-fragment bit (section 21), so a black hole raises an alert instead of a ticket.

---

## 18. Scenario E — Intermittent latency spikes

> 📚 **Study path:** 1) Note: [Learn: performance & observability](32-learn-performance-observability.md) and [Why is the system slow?](23-playbook-slow-system.md), section 8 (slow only sometimes) · 2) KodeKloud: *Fundamentals of SRE*, Performance Monitoring Deep Dive lesson ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page)) · 3) Read: [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) · 4) Practice: on test VMs, schedule an iperf3 run with a systemd timer, leave the E1 recorders running for an hour, and find the spikes from the logs alone.

**Level:** [L2–L3 · Mid → Senior]. Recording and correlating evidence over time
is L2. Seeing the pattern across hosts and schedules, and fixing it with SQM or
job scheduling, is senior work.

**Ticket:** "The app is usually fast, but several times an hour requests take 2–5
seconds. By the time we look, it is fine." Intermittent problems need **recorded
evidence with timestamps**, then correlation. Do not guess from a single snapshot.

### Step E1 — Record timestamped latency at several points

**Goal:** capture spikes as they happen and locate them: LAN, WAN, or the far end.

```bash
mkdir -p ~/spikes && cd ~/spikes
# Gateway, first ISP hop, and the destination, in parallel, timestamped (-D),
# reporting missing replies as they happen (-O). Leave running for an hour.
ping -D -O -i 0.5 10.0.20.1  > gw.log  2>&1 &
ping -D -O -i 0.5 198.51.100.1  > isp.log 2>&1 &
ping -D -O -i 0.5 203.0.113.10  > dst.log 2>&1 &
# HTTP timing every 5 s against the real service
while true; do
  printf '%s ' "$(date +%T)"
  curl -o /dev/null -s -w '%{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}\n' https://app.example.com/health
  sleep 5
done > http.log &

# Later: find the slow samples (time= over 100 ms, or missing replies)
grep -E 'time=[0-9]{3,}|no answer' gw.log isp.log dst.log | head
awk '$6 > 1' http.log
# Stop the background jobs when done
kill %1 %2 %3 %4
```

```
dst.log:[1791022322.412113] 64 bytes from 203.0.113.10: icmp_seq=4410 ttl=53 time=812 ms
dst.log:[1791022322.902551] 64 bytes from 203.0.113.10: icmp_seq=4411 ttl=53 time=338 ms
isp.log:[1791022322.405871] 64 bytes from 198.51.100.1: icmp_seq=4410 ttl=254 time=796 ms
gw.log  (no matches)

10:12:02 0.002 0.031 0.093 2.871 2.873
```

**What it means:** at the same timestamp, the ISP hop and the destination spike to
~800 ms while the gateway stays clean. The delay is added **between your gateway
and the ISP**: your uplink (likely saturated, Step 10) or the ISP's first hop. If
only `dst.log` spiked, it would be the far end or its network. If `gw.log` spiked
too, it is local (switch, Wi-Fi, or this host). The `http.log` line with a 2.8 s
`starttransfer` and fast connect points at the server instead; correlate with its
logs.

**Why this step (now):** with intermittent problems the first job is to catch them in the act, at several points of the path simultaneously, so the comparison localises the fault.

**Next step:** spikes start at the uplink → Step E2. Spikes only in HTTP timing (server think time) → the server: [Why is the system slow?](23-playbook-slow-system.md). Spikes on the gateway → Step E4. Spikes only for DNS (`time_namelookup`) → Step E5.

### Step E2 — Correlate spikes with load and schedules

**Goal:** find what else happens at spike time (backups, syncs, cron jobs, traffic peaks).

```bash
# Convert the ping epoch timestamp to a wall-clock time
date -d @1791022322
# Interface load around that time (sysstat history)
sar -n DEV -f /var/log/sysstat/sa03 -s 10:00:00 -e 10:30:00 | grep -E 'IFACE|eno1'
vnstat -i eno1 -5
# Scheduled jobs on this host and when they run
systemctl list-timers --all --no-pager
sudo ls /etc/cron.d/ ; sudo crontab -l ; sudo ls /var/spool/cron/crontabs/
# Run a latency-under-load test yourself (bufferbloat): ping while saturating.
# The iperf3 server must be BEYOND the uplink (a host you control in another site
# or cloud); a LAN target would not load the uplink at all.
ping -i 0.2 198.51.100.1 &  iperf3 -c 203.0.113.50 -t 20 ; kill %1
```

```
$ date -d @1791022322
Sat Oct  3 10:12:02 UTC 2026

$ sar -n DEV -f /var/log/sysstat/sa03 -s 10:00:00 -e 10:30:00 | grep -E 'IFACE|eno1'
10:00:01        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
10:10:01         eno1   3120.44  79811.02    201.10 115173.34      0.00      0.00      0.30     94.35
10:20:01         eno1   1180.10    902.33    844.12    512.40      0.00      0.00      0.31      0.68

$ systemctl list-timers --all --no-pager | grep -i backup
Sat 2026-10-03 11:10:00 UTC 57min Sat 2026-10-03 10:10:00 UTC 2min ago offsite-backup.timer offsite-backup.service
```

**What it means:** in this example the spike at 10:12 falls inside a 10-minute
window where `eno1` **transmitted** at ~94% of a gigabit, and an hourly
`offsite-backup.timer` fired at 10:10. The upload queue fills, so every packet
leaving the site (pings and user traffic alike) waits behind the backup.
In general: if the spikes line up with `%ifutil` near 100% or with a timer
(backup at 10:10, `apt` daily, log shipping), the link's queue is filling: classic
bufferbloat or plain saturation. Reproducing it with ping + iperf3 proves it.

**Why this step (now):** a recurring spike almost always has a recurring cause. Correlating timestamps is cheaper than any packet capture.

**Next step:** saturation/bufferbloat confirmed → reschedule or rate-limit the job, add SQM (`fq_codel`/`cake` with shaping) on the bottleneck router, or more capacity. No correlation with load → Step E3.

### Step E3 — Check the host for CPU stalls

**Goal:** rule out the host pausing (CPU steal, softirq saturation, container throttling) rather than the network.

```bash
LC_ALL=C mpstat -P ALL 1 60 | awk '$NF ~ /[0-9]/ && ($9 > 5 || $8 > 50)'   # %steal > 5 or %soft > 50
sar -u -f /var/log/sysstat/sa03 -s 10:00:00 -e 10:30:00             # %steal history
cpu=0; while read -r p d s rest; do echo "row$cpu dropped=$((16#$d)) squeeze=$((16#$s))"; cpu=$((cpu+1)); done < /proc/net/softnet_stat
docker exec CONTAINER cat /sys/fs/cgroup/cpu.stat                   # nr_throttled
```

```
$ LC_ALL=C mpstat -P ALL 1 60 | awk '$NF ~ /[0-9]/ && ($9 > 5 || $8 > 50)'
10:12:02     all    4.20    0.00    2.10    0.00    0.00    0.30   41.60    0.00    0.00   51.80
10:12:03     all    3.90    0.00    1.80    0.00    0.00    0.20   38.70    0.00    0.00   55.40
10:12:03       0    5.00    0.00    2.00    0.00    0.00    0.00   44.00    0.00    0.00   49.00
```

**What it means:** (example from a VM where this *was* the cause) for a few
seconds around 10:12 roughly **40% steal**. Empty output from this filter means
no second had more than 5% steal or 50% softirq, which clears the host. `%steal` spiking on a VM means the hypervisor took the CPU away
(noisy neighbour, burstable instance out of credits): everything, including packet
processing, pauses. `%soft` near 100% on one core, or growing `dropped`/`squeeze`,
means packet processing cannot keep up (Step 13). A throttled container (section
10) produces exactly this "usually fast, sometimes 100+ ms slower" pattern.

**Why this step (now):** when the network path shows no correlated spikes, the remaining suspect is the endpoint, and these counters are read-only.

**Next step:** steal → resize/move the VM or change instance family. Softirq → Step 13. Throttling → raise the CPU limit. All clean → Step E4.

### Step E4 — Check for link flaps, errors and duplicate IPs

**Goal:** catch physical or L2 events that cause brief outages.

```bash
sudo journalctl -k --since today | grep -Ei 'link is (up|down)|tx timeout|reset'
watch -d -n 5 'ip -s link show eno1'
# Duplicate IP: does anyone ELSE answer for our address? (replies = conflict)
# iputils syntax: on Ubuntu install iputils-arping (the other "arping" package uses different flags)
sudo arping -D -I eno1 -c 3 10.0.20.11
# Watch neighbour (ARP) changes live: a gateway MAC that keeps changing is a red flag
ip monitor neigh
```

```
$ sudo arping -D -I eno1 -c 3 10.0.20.11
ARPING 10.0.20.11 from 0.0.0.0 eno1
Unicast reply from 10.0.20.11 [52:54:00:AB:CD:EF]  0.812ms
Sent 1 probes (1 broadcast(s))
Received 1 response(s)
```

**What it means:** another machine (MAC `52:54:00:...`, a KVM/libvirt prefix) also
claims `10.0.20.11`. Traffic randomly goes to the wrong host as ARP caches flip,
producing intermittent timeouts and "slowness" that no tuning will fix. Link
down/up messages, or error counters that jump at spike times, point back to Step 7.

**Why this step (now):** these faults are invisible in averages and graphs, but they produce the most frustrating intermittent tickets. The checks take minutes.

**Next step:** duplicate IP → find the other host (switch MAC table, DHCP leases, hypervisor inventory) and fix the addressing. Flaps/errors → Step 7. Clean → Step E5.

### Step E5 — Check for intermittent DNS delays

**Goal:** catch lookups that occasionally take seconds.

```bash
# /usr/bin/time comes from the 'time' package (sudo apt install time)
for i in $(seq 1 50); do
  /usr/bin/time -f '%e s' getent ahosts app.example.com >/dev/null
done 2>&1 | sort | uniq -c | sort -nr
sudo conntrack -S | grep -o 'insert_failed=[0-9]*'
```

```
     44 0.00 s
      4 0.01 s
      2 5.01 s
```

**What it means:** 2 of 50 lookups took **5.01 s**: the resolver timeout. Combined
with a rising `insert_failed`, this is the conntrack race on parallel A/AAAA
queries (common in containers and pods); otherwise a flaky first nameserver. Step
14 has the fixes.

**Why this step (now):** DNS delays look exactly like network spikes from the application's point of view, but only affect requests that need a fresh lookup, which is why they feel random.

**Next step:** fix per Step 14. If none of E1–E5 found anything, leave the recorders from E1 running for a day and set up continuous probes (section 21).

#### Scenario E decision tree

```
Intermittent spikes
├── E1: spikes at gateway too ───────> local: Wi-Fi, switch, this host (E3/E4)
├── E1: spikes from ISP hop onward ──> E2: saturation/bufferbloat at the uplink?
│                                        └── yes -> reschedule/limit job, SQM, capacity
├── E1: only far end ────────────────> their server/network: evidence + ticket
├── only HTTP ttfb spikes ───────────> server/app (23-playbook)
├── %steal / %soft / throttling ─────> host CPU (E3, Step 13, section 10)
├── duplicate IP / link flaps ───────> E4, Step 7
└── 5 s lookups ─────────────────────> E5, Step 14
```

#### Scenario E fix and verify

Fix the cause found, then leave the E1 recorders running for at least as long as
the original problem's interval (a day if it was "a few times a day") and confirm
no spikes.

#### Scenario E rollback

Rescheduled jobs and QoS policies are config changes: keep the old cron/timer and
qdisc definitions so you can restore them. Kill the background recorders
(`kill %1 %2 %3 %4` or by PID).

#### Scenario E prevention

Continuous latency monitoring with history (smokeping or blackbox exporter ICMP
probes) turns the next intermittent ticket into a graph you can read in a minute
(section 21).

---

## 19. Scenario F — New server is slower than the old one

> 📚 **Study path:** 1) Note: [Kernel & sysctl reference](13-kernel-system.md) and [CPU & performance](03-cpu-performance.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)*, Operations Deployment → Change Kernel Runtime Parameters ([link](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: Brendan Gregg, *Linux Performance Tools, Brendan Gregg, part 1 of 2* ([link](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 4) Practice: build two test VMs, one with an emulated e1000 NIC and one with virtio_net, run the F1 test set on both, and explain the gap.

**Level:** [L3 · Senior]. Comparing whole servers layer by layer, and making the
fix part of the build (templates, Ansible, acceptance tests), is platform work.

**Ticket:** "We migrated the app from web-old to web-new (more CPU, more RAM), and
downloads and API calls are slower." Treat it as a diff: run identical tests on
both servers, then compare every layer until something differs.

### Step F1 — Run identical tests on both servers

**Goal:** get comparable numbers from both servers against the same targets.

```bash
# On BOTH servers, same target, same commands, same time window
iperf3 -c 10.0.20.15 -t 10 ; iperf3 -c 10.0.20.15 -t 10 -R
curl -o /dev/null -s -w '%{time_connect} %{time_starttransfer} %{speed_download}\n' https://files.example.org/test/1GB.bin
ping -c 50 -i 0.2 10.0.20.15 | tail -1
```

```
web-old$ iperf3 -c 10.0.20.15 -t 10 | tail -4 | head -2
[  5]   0.00-10.00  sec  1.09 GBytes   940 Mbits/sec    0             sender
[  5]   0.00-10.00  sec  1.09 GBytes   937 Mbits/sec                  receiver
web-new$ iperf3 -c 10.0.20.15 -t 10 | tail -4 | head -2
[  5]   0.00-10.00  sec   727 MBytes   610 Mbits/sec   48             sender
[  5]   0.00-10.00  sec   725 MBytes   608 Mbits/sec                  receiver
```

Put all results side by side:

| Test | web-old | web-new |
|------|---------|---------|
| iperf3 send | 940 Mbit/s | 610 Mbit/s |
| iperf3 receive (-R) | 938 Mbit/s | 590 Mbit/s |
| ping avg / mdev to 10.0.20.15 | 0.21 / 0.03 ms | 0.48 / 0.22 ms |
| curl 1 GB download | 112 MB/s | 71 MB/s |

**What it means:** web-new is slower on raw iperf3 too, so the difference is in the
network stack, NIC, CPU or path, not in the application. Higher and noisier ping
suggests virtualisation, power management or a different path.

**Why this step (now):** a diff needs two measurements taken the same way; without it every later comparison is guesswork.

**Next step:** iperf3 differs → Steps F2–F5. iperf3 identical but app slower → the app or its dependencies (DB in another AZ/site? Step F4) and [Why is the system slow?](23-playbook-slow-system.md).

### Step F2 — Diff the NIC, driver, offloads and queues

**Goal:** find hardware or virtual NIC differences.

```bash
# On both servers
sudo ethtool -i eno1 | grep -E 'driver|version|firmware'
sudo ethtool eno1 | grep -E 'Speed|Duplex'
sudo ethtool -k eno1 | grep -E 'segmentation-offload|receive-offload' > ~/offloads-$(hostname).txt
sudo ethtool -l eno1 | tail -5
sudo ethtool -g eno1 | tail -5
lspci | grep -i ethernet
# then copy one file over and: diff ~/offloads-web-old.txt ~/offloads-web-new.txt
```

```
web-old:  driver: virtio_net   Combined: 4
web-new:  driver: e1000        (no channel support)
00:03.0 Ethernet controller: Intel Corporation 82540EM Gigabit Ethernet Controller (rev 03)
```

**What it means:** web-new's VM was created with an **emulated Intel e1000** NIC
instead of the paravirtual `virtio_net` (or `vmxnet3` on VMware). Emulated NICs
cost a lot of hypervisor CPU per packet, have a single queue, and cap throughput
well below what virtio delivers. One template setting, a large difference.

**Why this step (now):** the NIC model and its features are the most common hardware-level diff, and they are invisible unless you look.

**Next step:** NIC model wrong → change the VM's NIC model to virtio/vmxnet3 (maintenance window: the interface name and MAC handling may change, so update netplan). NICs identical → Step F3.

### Step F3 — Diff the kernel network settings

**Goal:** catch sysctl, qdisc and congestion control differences.

```bash
# On both servers
sysctl -a 2>/dev/null | grep -E '^net\.(core|ipv4\.tcp|netfilter)' | sort > ~/sysctl-$(hostname).txt
tc qdisc show > ~/tc-$(hostname).txt
uname -r > ~/kernel-$(hostname).txt
# After copying the files to one place
diff ~/sysctl-web-old.txt ~/sysctl-web-new.txt
```

```
< net.ipv4.tcp_congestion_control = bbr
> net.ipv4.tcp_congestion_control = cubic
< net.ipv4.tcp_rmem = 4096	131072	33554432
> net.ipv4.tcp_rmem = 4096	131072	6291456
< net.ipv4.tcp_wmem = 4096	65536	33554432
> net.ipv4.tcp_wmem = 4096	16384	4194304
```

**What it means:** web-old had BBR and larger buffers, added by hand years ago and
never put into configuration management. web-new runs the defaults. For remote
clients on long paths that alone explains slower downloads (section 8).

**Why this step (now):** "hand-tuned and forgotten" settings are the most common reason a fresh server performs worse than an old pet server.

**Next step:** differences found → decide which values are correct, put them in Ansible / cloud-init, apply to web-new, re-run F1. No differences → Step F4.

### Step F4 — Diff the network path

**Goal:** make sure both servers reach the targets the same way.

```bash
# On both servers
ip route get 10.0.20.15
ip route get 203.0.113.10
tracepath -n 10.0.20.15
mtr -rwzbc 50 203.0.113.10
```

```
web-old$ tracepath -n 10.0.20.15
 1?: [LOCALHOST]                      pmtu 1500
 1:  10.0.20.15                                            0.212ms reached
     Resume: pmtu 1500 hops 1 back 1

web-new$ tracepath -n 10.0.20.15
 1?: [LOCALHOST]                      pmtu 1500
 1:  10.0.30.1                                             0.381ms
 2:  10.0.20.15                                            0.502ms reached
     Resume: pmtu 1500 hops 2 back 2
```

**What it means:** web-old sits in the same subnet as the target (one hop, direct).
web-new was placed in `10.0.30.0/24`, so every packet to the app's backends is
routed through `10.0.30.1`, here the inter-VLAN firewall. In general, a different VLAN or subnet for the new server can route its
traffic through a firewall that the old one bypassed, through a different uplink,
or (in AWS) from a different AZ than its database. A tracepath with an extra hop,
or a higher `Best` RTT in mtr, is the evidence.

**Why this step (now):** after hardware and kernel, location in the network is the last structural difference.

**Next step:** path differs → move the server or adjust routing, or put the app and its DB in the same AZ/site. Path identical → Step F5.

### Step F5 — Diff CPU power management and virtualisation

**Goal:** catch CPU frequency scaling, power saving or steal on the new host.

```bash
# Frequency driver, governor and current speeds (bare metal, or VMs that expose them)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver 2>/dev/null
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null
# Run this WHILE an iperf3 test is going, so the CPUs should be busy
grep MHz /proc/cpuinfo | sort | uniq -c
# Steal time and virtualisation type
mpstat 1 10 | tail -1
systemd-detect-virt
```

```
web-new$ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver
acpi-cpufreq
web-new$ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
powersave
web-new$ grep MHz /proc/cpuinfo | sort | uniq -c
     16 cpu MHz		: 1000.000
web-new$ systemd-detect-virt
none
```

**What it means:** web-new is bare metal (`none`) with the `acpi-cpufreq` driver
and its `powersave` governor, which **pins every core at the minimum frequency**
(1 GHz here, even under load). Packet processing, TLS and the app all run at a
fraction of the CPU's speed, which shows as higher, noisier ping (F1) and lower
small-packet throughput. Caution when comparing: with the `intel_pstate` or
`amd-pstate` drivers, a governor named `powersave` is the normal *dynamic* default
and is not a problem by itself; judge by the MHz under load. A BIOS power profile
that allows deep C-states adds wake-up latency to every interrupt as well: compare
the profiles ("Maximum Performance" vs "Balanced/OS-controlled") with the hardware
team. On VMs, `%steal` and the virtualisation type (`kvm`, `vmware`, `microsoft`)
explain host contention instead.

**Why this step (now):** it is the last common difference between "same OS, same config" servers and it explains latency differences that throughput tests alone hide.

**Next step:** power profile → set performance mode (BIOS / `sudo cpupower frequency-set -g performance` from the `linux-tools` packages; persist it through your config management, it resets at reboot) and re-run F1. Steal → move/resize the VM.

#### Scenario F decision tree

```
New server slower
├── F1 iperf3 same, app slower ─────> app deps: DB location (F4), app config (23-playbook)
└── F1 iperf3 slower
    ├── NIC model/driver differs ───> virtio/vmxnet3, queues, offloads (F2)
    ├── sysctl/qdisc differs ───────> codify the right values (F3, section 8)
    ├── path differs ───────────────> routing/VLAN/AZ (F4)
    └── CPU power/steal differs ────> BIOS profile, governor, VM placement (F5)
```

#### Scenario F fix and verify

Change one difference at a time and re-run the full F1 table after each. Stop when
web-new matches or beats web-old, and keep the table in the migration notes.

#### Scenario F rollback

The old server is your rollback: keep it (or its DNS record/load-balancer
membership) ready until web-new has matched the baseline for a full business
cycle. Revert sysctl changes with section 8's rollback.

#### Scenario F prevention

- Make network tuning part of the server build (Ansible role, cloud-init), never manual.
- Run the F1 test set as an **acceptance test** for every new server and VM template, and store the results next to the inventory.
- Keep VM templates with the paravirtual NIC model and multiple queues by default.

---

## 20. Master decision tree

> 📚 **Study path:** 1) Note: reread only the **Goal** and **Next step** lines of Steps 0–14 · 2) Practice: the timed exit test in section 22 · 3) KodeKloud: *Linux Challenges* (free, timed scenarios) ([link](https://kodekloud.com/courses/linux-challenges)) · 4) Practice: [SadServers scenarios](https://sadservers.com/scenarios), saying out loud which branch of this tree you are on.

**Level:** [L2 · Mid]. When you can walk this tree from memory and justify every
branch, you have reached L2 for network speed.

Print this one. Every branch names the step or scenario that continues it.

```
"The network is slow"
│
├─ 0. FRAME: which path, direction, protocol, who, since when, what number?   (section 3)
│     └─ Step 0: ip route get / proxies / tunnels / IPv6 first?
│
├─ 1. curl -w timeline (Step 1)
│     ├─ namelookup high ─────────────────────────────> Step 14 (DNS)          [also E5]
│     ├─ connect high, or 1 s / 3 s / 7 s ────────────> Step 2-3 (loss), Step 8 (ListenOverflows)
│     ├─ appconnect high ─────────────────────────────> TLS (18-web-http-tls.md); hangs -> Step 9
│     ├─ starttransfer high (server think time) ──────> the app/server (23, 25, 26 playbooks)
│     └─ total - starttransfer high (body slow) ──────> throughput: continue at 2
│
├─ 2. ping gateway, then destination (Step 2)
│     ├─ gateway lossy/jittery ───────────────────────> Step 7 (link) / section 11 (Wi-Fi)
│     └─ destination lossy/jittery ───────────────────> 3
│
├─ 3. mtr both directions (Step 3)
│     ├─ loss starts in our network ──────────────────> Step 10 (who uses it), Step 11 (shaping)
│     ├─ loss starts at ISP/transit ──────────────────> provider ticket, Scenario A
│     └─ clean ───────────────────────────────────────> 4
│
├─ 4. iperf3 both directions (Step 4)
│     ├─ ~94 Mbit/s or one direction bad + retrans ──> Step 7 (speed/duplex/cable)   [Scenario B]
│     ├─ flat round number ───────────────────────────> Step 11 (shaper/policer), section 9 (AWS)
│     ├─ near line rate ──────────────────────────────> network fine: disk/tool/app [Scenario B]
│     └─ low ─────────────────────────────────────────> 5
│
├─ 5. -P 1 vs -P 8, -w, -C bbr (Step 5) + UDP loss (Step 6)
│     ├─ parallel fast, single slow ──────────────────> Step 8 (window/loss), section 8 (tuning)
│     ├─ UDP loss even at low rate ───────────────────> Step 7 (errors)
│     └─ UDP loss above a precise rate ───────────────> Step 11, provider/cloud limits
│
├─ 6. Small works, big stalls? ───────────────────────> Step 9 (MTU)                 [Scenario D]
│
├─ 7. Host limits
│     ├─ "table full, dropping packet" ───────────────> Step 12 (conntrack)
│     ├─ one core 100% %soft / softnet drops ─────────> Step 13 (IRQ/RSS)
│     ├─ %steal / CPU throttling ─────────────────────> Step 13, section 10, 23-playbook
│     └─ AWS allowance counters rising ───────────────> section 9
│
└─ 8. Context-specific
      ├─ only containers/pods ────────────────────────> section 10 (MTU, overlay, Traefik, throttling)
      ├─ only VPN users ──────────────────────────────> Scenario C
      ├─ only sometimes ──────────────────────────────> Scenario E
      └─ only the new server ─────────────────────────> Scenario F
```

---

## 21. Prevention: baselines, probes and alerts

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)*, Prometheus Fundamentals → Node Exporter ([notes](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page)), then the Alerting module ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) Note: [Learn: performance & observability](32-learn-performance-observability.md), sections 11–12 (Prometheus, Alertmanager) · 3) Video: KodeKloud, *Kubernetes Monitoring Made Easy with Prometheus* ([link](https://www.youtube.com/watch?v=6xmWr7p5TE0)) · 4) Practice: [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/), then deploy the blackbox DF probe below in your homelab and make it fire by breaking the MTU.

**Level:** [L4 · Senior/Lead]. Turning one-off measurements into baselines,
probes and alerts, so the team learns about slowness before users do, is SRE
work.

The difference between a two-hour "is it slow?" debate and a five-minute fix is
**a number from last week**. Build these once; the
[performance & observability module](32-learn-performance-observability.md) covers
Prometheus, Grafana and alerting in depth.

### Throughput baselines with iperf3

A weekly off-hours job per important path (app ↔ DB, backup source ↔ backup
target, site ↔ site) gives you "normal" to compare against. The script starts a
one-shot iperf3 server on the target over SSH, so no server is left listening.

```bash
sudo tee /usr/local/bin/net-baseline.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
# Usage: net-baseline.sh TARGET_HOST   (needs: iperf3 + jq here, iperf3 + SSH key access on TARGET)
set -euo pipefail
TARGET=${1:?usage: net-baseline.sh TARGET_HOST}
OUT=/var/lib/net-baseline
mkdir -p "$OUT"
TS=$(date +%F-%H%M)
for dir in send recv; do
  ssh "$TARGET" 'iperf3 -s -1 -D'        # one-shot server, exits after the test
  sleep 1
  if [ "$dir" = recv ]; then R=-R; else R=; fi
  iperf3 -c "$TARGET" -t 10 -O 2 $R -J > "$OUT/$TS-$TARGET-$dir.json"
  printf '%s %s %s %.0f Mbit/s retrans=%s\n' "$TS" "$TARGET" "$dir" \
    "$(jq '.end.sum_received.bits_per_second / 1e6' "$OUT/$TS-$TARGET-$dir.json")" \
    "$(jq '.end.sum_sent.retransmits // 0' "$OUT/$TS-$TARGET-$dir.json")"
done | tee -a "$OUT/summary.log"
EOF
sudo chmod 755 /usr/local/bin/net-baseline.sh
# Run it as the user whose SSH key reaches the target; give that user the output dir once
sudo install -d -o "$USER" /var/lib/net-baseline
/usr/local/bin/net-baseline.sh backup01
```

```
2026-10-05-0310 backup01 send 936 Mbit/s retrans=0
2026-10-05-0310 backup01 recv 934 Mbit/s retrans=2
```

Schedule it with a systemd timer (or cron) at a quiet hour, and keep
`summary.log` in your runbook repo. A line that suddenly says `94 Mbit/s` is a
cable or port fault caught before anyone complains.

### Latency and loss history: smokeping or blackbox exporter

Two good options:

- **SmokePing** draws latency and loss over time per target, with the distribution of each sample ("smoke"). Simple to run and excellent for "was it slow at 10:10 yesterday?".
- **Prometheus blackbox exporter** fits the Prometheus/Grafana stack from your plan. Its HTTP probe reports durations per phase (`resolve`, `connect`, `tls`, `processing`, `transfer`), which is `curl -w` running every 15 seconds forever.

```yaml
# blackbox.yml: modules
modules:
  http_2xx:
    prober: http
    timeout: 10s
  icmp:
    prober: icmp
    timeout: 5s
  icmp_df_1472:                 # 1500-byte packets with Don't Fragment: detects MTU black holes
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: ip4
      dont_fragment: true
      payload_size: 1472
```

```yaml
# prometheus.yml: one scrape job per module (the standard blackbox relabelling)
scrape_configs:
  - job_name: blackbox_icmp_df
    metrics_path: /probe
    params:
      module: [icmp_df_1472]
    static_configs:
      - targets: [10.20.0.15, 203.0.113.40]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:9115
```

Useful queries:

| Question | PromQL |
|----------|--------|
| Where does the HTTP time go? | `probe_http_duration_seconds{instance="https://app.example.com/"}` (by `phase`) |
| RTT to a target over time | `probe_icmp_duration_seconds{phase="rtt"}` |
| DNS lookup time per probe | `probe_dns_lookup_time_seconds` |
| Probe failing | `probe_success == 0` |

### Alerts on the things that silently degrade speed

`node_exporter` already exposes most of what this playbook checks by hand.

```yaml
groups:
  - name: network-speed
    rules:
      - alert: NetworkInterfaceErrors
        expr: |
          rate(node_network_receive_errs_total{device!~"lo|veth.*|docker.*|br-.*"}[5m]) > 0
          or rate(node_network_transmit_errs_total{device!~"lo|veth.*|docker.*|br-.*"}[5m]) > 0
        for: 10m
        labels: {severity: warning}
        annotations:
          summary: "NIC errors on {{ $labels.instance }} {{ $labels.device }} (cable/SFP/duplex?)"

      - alert: LinkSpeedBelowExpected
        # 125000000 bytes/s = 1 Gbit/s. Virtual NICs may report -1 or a fake value: scope by device.
        expr: node_network_speed_bytes{device=~"eno.*"} > 0 and node_network_speed_bytes{device=~"eno.*"} < 125000000
        for: 5m
        labels: {severity: warning}

      - alert: InterfaceSaturated
        expr: rate(node_network_receive_bytes_total{device=~"eno.*"}[5m]) / (node_network_speed_bytes{device=~"eno.*"} > 0) > 0.9
        for: 15m
        labels: {severity: info}

      - alert: TcpRetransmitRateHigh
        expr: rate(node_netstat_Tcp_RetransSegs[5m]) / rate(node_netstat_Tcp_OutSegs[5m]) > 0.02
        for: 15m
        labels: {severity: warning}

      - alert: ConntrackTableNearlyFull
        expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8
        for: 5m
        labels: {severity: critical}

      - alert: PathMtuBlackHole
        expr: probe_success{job="blackbox_icmp_df"} == 0
        for: 5m
        labels: {severity: warning}
```

Also worth collecting: the AWS ENA allowance counters (node_exporter's `ethtool`
collector, disabled by default, or the CloudWatch agent), `vnstat` on every edge
host, and `sysstat` everywhere so `sar` history exists.

### Habits that prevent "slow" tickets

- Every new server, VM template and link gets an acceptance test (Scenario F's F1 table) and the result is stored.
- Network tuning lives in configuration management, never only on one pet server.
- MTU per segment, tunnel and overlay is documented; ICMP for PMTUD is never blocked.
- Bulk jobs (backups, syncs, image pulls) are scheduled and rate-limited, not left to fight production traffic.
- After every incident, write the five-line note from your weekly rhythm: symptom, first wrong guess, the evidence that settled it, the fix, and what you will check first next time.

---

## 22. Practice lab and where to go next

> 📚 **Study path:** 1) Practice: two test VMs in your homelab, or a KodeKloud *Ubuntu playground* ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) for the single-host drills · 2) KodeKloud: *Linux Challenges* (free, timed) ([link](https://kodekloud.com/courses/linux-challenges)) · 3) Practice: [SadServers scenarios](https://sadservers.com/scenarios) · 4) Practice: [iximiuz: container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch) before the container drills.

**Level:** every drill below is tagged. Pass the L2 drills and the L2 part of
the exit test before you start the L3 and L4 ones.

Reading this playbook makes you faster at *recognising* the patterns; breaking a
homelab makes you fast at *proving* them. Do these on a **test VM with console
access**, never on a production host.

### Break-and-fix drills

| Drill | Level | Break it (test VM only) | Diagnose with | Undo |
|-------|-------|-------------------------|---------------|------|
| Long fat pipe | L2 · Mid | `sudo tc qdisc add dev eth0 root netem delay 80ms limit 10000` | Step 5: `-P 1` vs `-P 8` vs `-w 16M` | `sudo tc qdisc del dev eth0 root` |
| Lossy link | L2 · Mid | `sudo tc qdisc add dev eth0 root netem loss 1%` | Steps 2, 4, 8 (`ss -ti` retrans) | `sudo tc qdisc del dev eth0 root` |
| Forgotten shaper | L2 · Mid | `sudo tc qdisc add dev eth0 root tbf rate 50mbit burst 64kb latency 50ms` | Steps 4 and 11 | `sudo tc qdisc del dev eth0 root` |
| MTU black hole | L2 · Mid | On a router VM: lower the far side MTU to 1400 and drop ICMP type 3 code 4 | Step 9, Scenario D | Restore MTU, remove the drop rule |
| Conntrack full | L3 · Senior | `sudo sysctl -w net.netfilter.nf_conntrack_max=2000`, then open many connections | Step 12 | Set the value back |
| Slow DNS | L1 · Junior | Put a dead IP first in netplan `nameservers`, `sudo netplan try` | Steps 1 and 14 | Let `netplan try` revert, or restore the file |
| Container throttling | L3 · Senior | `docker run --cpus 0.2 ...` a small web app, load it | Section 10 (`cpu.stat`) | Re-run without `--cpus` |
| Overlay MTU (CKA homelab) | L3 · Senior | Set the CNI MTU higher than the underlay allows | Section 10 pod matrix | Restore the CNI MTU |

Why `limit 10000` in the long-fat-pipe drill: netem holds delayed packets in a
queue of 1000 packets by default. At 1 Gbit/s and 80 ms, about 6,900 full-size
packets are in flight, so the default queue overflows and silently turns the
"window" drill into a "loss" drill.

> ⚠️ `tc netem` on the interface you are connected through also delays your own
> SSH session; with heavy loss you can lose the session. Have a console open, and
> schedule an automatic undo first, which runs even if your session dies:
> `sudo systemd-run --on-active=5min /usr/sbin/tc qdisc del dev eth0 root`.

### Self-check questions

Answer each one in one or two sentences, without scrolling up. Then compare with
the short answers below the list.

1. [L0] A download dialog shows 11.5 MB/s. What is that in Mbit/s, and what does it suggest?
2. [L1] `curl -w` shows `namelookup` 5.01 s and every other phase fast. Which layer is it, and which step comes next?
3. [L1] mtr shows 40% loss at hop 3 and 0% at hops 4 and 5. Is hop 3 a problem?
4. [L2] iperf3 A → B gives 940 Mbit/s. B → A gives 33 Mbit/s with thousands of retransmits. Name two likely causes and the first command you run.
5. [L2] Over an 80 ms path, one stream gives 240 Mbit/s and eight streams give 920 Mbit/s. What limits the single stream, and what are two fixes?
6. [L2] SSH works but `scp` stalls at 0%. `ping -M do -s 1472` fails silently and `-s 1372` works. What is the diagnosis, and what is the preferred order of fixes?
7. [L2] Why does switching a laptop's `tcp_congestion_control` to BBR not speed up downloads *to* that laptop?
8. [L2] `ss -ti` shows a high `rwnd_limited` share. Which host do you change, and what do you change?
9. [L3] A Kubernetes node logs `nf_conntrack: table full, dropping packet`. Why not just raise the sysctl, and why never run `conntrack -F`?
10. [L3] A server is 66% idle overall but drops packets, and one core shows 94% `%soft`. What do you check, and what do you fix?
11. [L3] Node ↔ node iperf3 gives 940 Mbit/s, but cross-node pod ↔ pod gives 300 Mbit/s with many retransmits. What is the most likely cause?
12. [L3] On AWS, `bw_out_allowance_exceeded` rises during a nightly backup that runs at full speed for the first 10 minutes and then slows down. Explain why.
13. [L4] Which alerts from section 21 would have caught Scenarios B and D before any user complained?
14. [L4] Write the five-line incident note for "the network is slow every night around 2 am", using the Step 10 sample outputs.

**Answers:**

1. About 92 Mbit/s: a 100 Mbit/s link somewhere in the path (section 2, Step 7, Scenario B).
2. DNS: the first resolver is timing out (5 s is the default timeout). Go to Step 14.
3. No. That router rate-limits ICMP sent to itself. Only loss that continues to the last hop matters (Step 3).
4. A duplex mismatch, or a faulty transmit side on B (cable pair, SFP, NIC). Run `ethtool` and `ip -s -s link` on both ends (Step 7).
5. The TCP window is too small for the bandwidth-delay product (a per-flow limit). Raise the `tcp_rmem`/`tcp_wmem` maximums on both ends, use BBR on the sender, or use parallel transfers (Step 5, section 8).
6. A PMTUD black hole. Fix in this order: allow ICMP type 3 code 4 and ICMPv6 type 2, clamp TCP MSS on the tunnel or router, set the correct MTU on the tunnel or overlay, and use `tcp_mtu_probing` only where nothing else is possible (Step 9, Scenario D).
7. Congestion control works on the **sending** side. Downloads to the laptop are sent by the server, so BBR must be enabled there (section 2, "Direction matters").
8. The **receiver**. Raise its `tcp_rmem` maximum, or fix a receiving application that reads too slowly or sets a small `SO_RCVBUF` (Step 8).
9. kube-proxy sets `nf_conntrack_max` itself from `conntrack.maxPerCore`, so change the kube-proxy configuration. `conntrack -F` deletes the NAT state of every live connection, which breaks Services and published ports for all users (Step 12).
10. Check `/proc/interrupts`, `ethtool -l` (queues in use) and `irqbalance`. Enable more NIC channels in a maintenance window, or use RPS on single-queue virtual NICs (Step 13).
11. An overlay MTU mismatch. Lower the CNI MTU to the underlay MTU minus the encapsulation overhead (section 10, Step 9 table).
12. The instance used up its network burst credits and dropped to its baseline bandwidth. Move to a larger or network-optimised instance type, or spread the backup over a longer window (section 9).
13. `LinkSpeedBelowExpected` and `NetworkInterfaceErrors` for Scenario B, `PathMtuBlackHole` (the blackbox DF probe) for Scenario D, plus the weekly iperf3 baseline (section 21).
14. Symptom: interactive traffic slow 02:00–02:10. First wrong guess: the ISP. Evidence: `sar`/`vnstat` show `eno1` at ~936 Mbit/s, and `nethogs` shows the `backup` user's `rsync`. Fix: `rsync --bwlimit` plus a reschedule. Check first next time: interface history (Step 10).

### Timed exit test

Use test VMs only. A partner (or a script you have not read) breaks the system,
and you fix it within the time limit. Write down the evidence line that proved
each answer. If you pass tasks 1–3, you have the L2 skills for network speed.
Tasks 4–5 are L3 and task 6 is L4.

| # | Task | Level | Time | Pass when |
|---|------|-------|------|-----------|
| 1 | Given only "app.example.com is slow", produce the Step 1 phase table and name the slow phase | L1 · Junior | 5 min | The slow phase is named with numbers from `curl -w` |
| 2 | Your partner applies **one** of: netem delay, netem loss, a tbf shaper, an MTU black hole, a dead first resolver. Identify it without running `tc qdisc show` first | L2 · Mid | 20 min | Correct fault, plus the step and output line that proved it |
| 3 | Over an 80 ms netem link, measure single vs parallel streams, raise the buffers, prove the gain, then roll back | L2 · Mid | 20 min | Before/after numbers recorded and the sysctls restored |
| 4 | Docker host whose path MTU is 1400: find a container's hang from inside its namespace with netshoot, then fix it with the network MTU | L3 · Senior | 25 min | The DF ping from inside the container passes and the transfer completes |
| 5 | Kubernetes homelab: run the four-way iperf3 matrix from section 10 and explain every number | L3 · Senior | 30 min | Each gap is attributed to a layer (physical, CNI, overlay, kube-proxy) |
| 6 | Deploy the section 21 alert rules and blackbox DF probe, break the MTU, and show the alert firing and then resolving | L4 · Senior/Lead | 45 min | Alert fires within its `for:` window and clears after the fix |

### Related modules in this handbook

- [Network command reference](02-network.md): ping, mtr, ss, ip, tcpdump, nc in depth.
- [Learn: networking, DNS, HTTP, TLS](28-learn-networking.md): TCP, windows, MTU and DNS from first principles.
- [Learn: performance & observability](32-learn-performance-observability.md): USE method, Prometheus, Grafana, alerting.
- [Why is the system slow?](23-playbook-slow-system.md): CPU, memory and disk when the host is the bottleneck.
- [Site down](25-playbook-site-down.md): the layered walk when it does not work at all.
- [Docker, Dokploy/Traefik & Kubernetes incidents](26-playbook-containers-k8s.md): container-specific failures.
- [Who owns this port?](22-playbook-ports-inventory.md): when port 5201 (or any test port) is already taken.
- [DNS reference](08-dns.md), [Web, HTTP & TLS](18-web-http-tls.md), [Kernel & sysctl](13-kernel-system.md), [AWS](16-aws-cloud.md), [Windows](17-windows.md), [macOS](20-macos.md).

### Where to go next by career stage

- **Fresher → Junior (L0 → L1):** [Learn: networking](28-learn-networking.md), sections 1–6, then [Network reference](02-network.md). Run Steps 0–3 on every "slow" ticket until it is a habit. *Why:* the numbers mean nothing until RTT, loss and windows do. *Next:* the "Slow DNS" drill.
- **Junior → Mid (L1 → L2):** [Site down](25-playbook-site-down.md) uses the same layered method for hard failures. [Why is the system slow?](23-playbook-slow-system.md) covers the host side. *Why:* L2 means naming the broken layer with evidence on any ticket, not only speed tickets. *Next:* exit-test tasks 2 and 3.
- **Mid → Senior (L2 → L3):** [Learn: Docker](30-learn-docker.md) (networking), [Learn: Kubernetes](31-learn-kubernetes.md) (CNI and Services), [Learn: cloud & AWS](36-learn-cloud-aws.md) and the [containers & K8s playbook](26-playbook-containers-k8s.md). *Why:* in your stack, speed problems increasingly live in overlays, proxies and cloud allowances. *Next:* exit-test tasks 4 and 5.
- **Senior → Lead (L3 → L4):** [Learn: performance & observability](32-learn-performance-observability.md) (SLOs, alerting), [Learn: senior architecture](39-learn-senior-architecture.md) and the [career ladder](40-career-ladder.md). *Why:* at L4 you prevent tickets with baselines and probes, and you teach the method to others. *Next:* exit-test task 6, then run the section 22 drills as a team game day.

### External reading

- [Practical Networking: Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/): how packets cross switches and routers (the model behind Steps 2–3).
- [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/): the free zine that makes Step 9 and Scenario D's captures easy.
- [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) and [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55): the host side of "slow".
- [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/): the method behind "measure, isolate, change one thing".
- [netshoot](https://github.com/nicolaka/netshoot), [Docker docs: Networking](https://docs.docker.com/engine/network/) and [Dokploy: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking): container networking for section 10.
- [iximiuz: container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch): build the veth/bridge path by hand to see where overhead comes from.
- [Prometheus documentation](https://prometheus.io/docs/), [Kubernetes documentation](https://kubernetes.io/docs/), and the [Linux man pages](https://man7.org/linux/man-pages/) for `tc`, `ss`, `ip`, `ethtool` and `tcp(7)`.
