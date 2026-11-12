# 02 — Network Troubleshooting (Linux)

Typical symptoms: "can't reach host", timeouts, packet loss, slow transfers,
"connection refused", intermittent drops.

Layered approach (bottom-up): **link → IP → routing → DNS → port → firewall → application**.

---

## 1. Reachability

### `ping` — basic ICMP reachability + latency
```bash
ping -c 4 10.0.1.20            # 4 packets and stop
ping -c 100 -i 0.2 host        # flood-ish loss test (100 pkts, 0.2s apart)
ping -s 1472 -M do host        # test MTU (1472 + 28 hdr = 1500); "Frag needed" = MTU problem
ping -I eth1 host              # ping out a specific interface
ping6 -c 4 host                # IPv6
```
Example:
```
$ ping -c 4 10.0.1.20
64 bytes from 10.0.1.20: icmp_seq=1 ttl=64 time=0.42 ms
...
4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 0.31/0.40/0.45/0.05 ms
```
Interpretation:

- **0% loss, low rtt** → L3 is fine; problem is higher (port/app/DNS).
- **100% loss** → routing, firewall, or host down. Note: many clouds/firewalls
  **block ICMP** — no ping ≠ host down. Always confirm with a TCP check (`nc -zv`).
- **Partial loss / jittery rtt** → congestion or bad link → use `mtr`.

### `mtr` — ping + traceroute combined, live per-hop loss (best loss-locator)
```bash
mtr host                       # interactive live view
mtr -rwbzc 100 host            # report mode: 100 cycles, wide, show IPs+ASN
mtr -T -P 443 host             # TCP mode to port 443 (when ICMP is filtered)
mtr -u host                    # UDP mode
```
Example report:
```
$ mtr -rwc 50 example.com
HOST: web01                    Loss%  Snt  Last  Avg  Best  Wrst StDev
  1.|-- 10.0.1.1                0.0%   50   0.4   0.5   0.3   1.1  0.1
  2.|-- isp-edge.net           0.0%   50   8.2   8.4   7.9  12.0  0.7
  3.|-- core1.isp.net          80.0%   50   9.1   9.3   8.8  10.2  0.4   ← ignore!
  4.|-- example.com             0.0%   50  22.1  22.4  21.8  30.5  1.2
```
**Reading mtr correctly:** loss at an intermediate hop that does NOT continue to
the final hop = that router just deprioritizes ICMP replies (normal). Real loss
**starts at one hop and persists to the destination**.

### `traceroute` / `tracepath` — path discovery
```bash
traceroute host                # UDP by default
traceroute -I host             # ICMP (like Windows tracert)
traceroute -T -p 443 host      # TCP SYN to 443 — passes most firewalls
tracepath host                 # no root needed, also discovers path MTU
```
```
$ traceroute -n 203.0.113.50
 1  10.0.1.1      0.412 ms  0.380 ms  0.401 ms
 2  100.64.0.1    8.310 ms  8.270 ms  8.412 ms
 3  * * *                                        ← hop ignores probes (usually fine)
 4  203.0.113.50  22.101 ms  22.087 ms  22.240 ms
```
`* * *` rows = hop doesn't reply (often fine — later hops still answering proves
the path works) or packets die there (if every row after it is also `* * *`).
The hop where latency jumps and stays high for all later hops is where delay is added.

---

## 2. Interfaces, addresses, links

### `ip` — the modern do-everything tool (replaces ifconfig/route/arp)
```bash
ip addr           # or: ip a      — all interfaces + IPs; look for state UP/DOWN
ip -br addr                      # brief one-line-per-interface view
ip link                          # L2 state, MTU, MAC
ip -s link show eth0             # RX/TX counters — errors/dropped/overruns
ip route                         # routing table
ip route get 8.8.8.8             # WHICH route/interface/source IP is used for a dest
ip neigh                         # ARP/neighbor table (replaces `arp -a`)
ip link set eth1 up              # bring an interface up
ip addr add 10.0.1.5/24 dev eth1 # add address (temporary, until reboot)
```
Examples:
```
$ ip -br addr
lo       UNKNOWN  127.0.0.1/8
eth0     UP       10.0.1.20/24
eth1     DOWN                     ← cable/attachment problem?

$ ip route get 8.8.8.8
8.8.8.8 via 10.0.1.1 dev eth0 src 10.0.1.20
```
```
$ ip -s link show eth0
    RX: bytes  packets  errors  dropped overrun mcast
    981M       12M      0       4512    0       0      ← drops: ring buffer/NIC pressure
```

### `ethtool` — NIC speed/duplex/offloads (mostly on-premise)
```bash
ethtool eth0                   # Speed: 1000Mb/s  Duplex: Full  Link detected: yes
ethtool -S eth0                # NIC hardware stats (crc errors → bad cable/port)
ethtool -i eth0                # driver and firmware version
```
**Classic on-prem issue:** speed/duplex mismatch (100Mb/Half) with a switch port
→ terrible performance, CRC errors. Fix negotiation on both ends.

### Legacy equivalents (still on older boxes)
```bash
ifconfig -a                    # = ip addr
route -n                       # = ip route
arp -a                         # = ip neigh
netstat -i                     # per-interface counters
```

---

## 3. Ports & sockets — "is it listening?" / "who's connected?"

### `ss` — socket statistics (modern netstat)
```bash
ss -tulpn                      # listening TCP+UDP with owning process (root for -p)
ss -tn                         # established TCP connections
ss -tn state time-wait | wc -l # count TIME_WAIT sockets
ss -tnp dst 10.0.1.50          # connections to a specific host
ss -tlnp sport = :443          # who listens on 443
ss -s                          # summary counters
```
Example:
```
$ ss -tulpn
Netid State  Local Address:Port  Process
tcp   LISTEN 0.0.0.0:22          users:(("sshd",pid=890,fd=3))
tcp   LISTEN 127.0.0.1:5432      users:(("postgres",pid=1204,fd=5))
```
→ Postgres listens on **127.0.0.1 only** — remote clients get "connection refused".
This is one of the most common findings in practice.

### `netstat` (legacy, same ideas)
```bash
netstat -tulpn                 # listening + process
netstat -an | grep ESTABLISHED | wc -l
netstat -s                     # protocol counters (retransmits, resets)
```

### `nc` (netcat) — test a TCP/UDP port without the app
```bash
nc -zv host 443                # TCP connect test:  succeeded / refused / timeout
nc -zvu host 53                # UDP probe (less reliable by nature)
nc -zv host 8000-8010          # scan a small range
nc -l 9000                     # LISTEN on 9000 (server side of a path test)
nc host 9000                   # connect to it (client side) — proves the path
```
The three possible outcomes — this split drives the whole diagnosis:
```
$ nc -zv 10.0.1.20 5432
Connection to 10.0.1.20 5432 port [tcp/postgresql] succeeded!    ← path AND service OK

$ nc -zv 10.0.1.20 8080
nc: connect to 10.0.1.20 port 8080 (tcp) failed: Connection refused
   ← packet ARRIVED, host replied "nothing here": service down or bound to
     127.0.0.1 only. The network path is fine!

$ nc -zv -w 3 10.0.2.9 443
nc: connect to 10.0.2.9 port 443 (tcp) timed out
   ← packet silently DROPPED in transit: firewall / security group / NACL /
     routing. The host may be perfectly healthy.
```

### `telnet` — same connect test, older habit
```bash
telnet host 3306               # "Connected" vs hang vs refused
```

### `nmap` — port scanner (**only scan hosts you are authorized to test**)
```bash
nmap -p 22,80,443 10.0.1.20    # specific ports
nmap -p- 10.0.1.20             # all 65535 TCP ports
nmap -sU -p 53,123 10.0.1.20   # UDP scan
nmap -sn 10.0.1.0/24           # ping-sweep: which hosts are up
```
`open` vs `closed` (RST received) vs `filtered` (silently dropped → firewall).

---

## 4. Packet capture — the ground truth

### `tcpdump`
```bash
tcpdump -i eth0 -nn host 10.0.1.50                  # traffic to/from a host
tcpdump -i any -nn port 443                          # any interface, port 443
tcpdump -i eth0 -nn 'tcp port 80 and host 10.0.1.5' # combined filter
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0'  # only SYNs
tcpdump -i eth0 -nn icmp                             # pings
tcpdump -i eth0 -nn -c 1000 -w /tmp/cap.pcap        # save 1000 pkts for Wireshark
tcpdump -nn -r /tmp/cap.pcap                         # read a capture back
```
Flags: `-nn` no name/port resolution, `-c` count, `-w`/`-r` write/read, `-v` verbose,
`-A` ASCII payload, `-s0` full packets.

Diagnostic patterns:

- SYN out, **nothing back** → dropped upstream (firewall/SG) or no route back
  (asymmetric routing).
- SYN out, **RST back** → host reachable, port closed.
- Repeated retransmits of same seq → loss between capture point and peer.
- Capture on **both ends**: packet leaves A, never arrives at B → the network
  in between (on AWS: SG on B, NACL either way, route tables).

---

## 5. Bandwidth & throughput

### `iperf3` — measured throughput between two hosts
```bash
iperf3 -s                      # on host A (server)
iperf3 -c hostA                # on host B: TCP throughput test
iperf3 -c hostA -R             # reverse direction
iperf3 -c hostA -u -b 500M     # UDP at 500 Mbit/s → shows loss & jitter
iperf3 -c hostA -P 8           # 8 parallel streams
```

### Live usage — who/what is using the bandwidth NOW
```bash
iftop -i eth0                  # per-connection live bandwidth (root)
nload eth0                     # simple in/out graph
sar -n DEV 1                   # per-interface kb/s history (sysstat)
ip -s link                     # raw counters, run twice and diff
```

---

## 6. Firewalls (local host)

```bash
iptables -L -n -v --line-numbers   # legacy: rules with hit counters
iptables -t nat -L -n -v           # NAT table (port forwards, masquerade)
nft list ruleset                   # nftables (modern)
firewall-cmd --list-all            # firewalld (RHEL/CentOS/Fedora)
ufw status verbose                 # ufw (Ubuntu)
```
Debug trick: the `-v` hit counters in `iptables -L -n -v` show whether a DROP rule
is actually matching your traffic.

Temporarily (and carefully) test with firewall off on a test box:
```bash
systemctl stop firewalld       # then retest; start it again after!
```

---

## 7. Connection tracking & kernel limits

```bash
conntrack -L | wc -l                         # current tracked connections
sysctl net.netfilter.nf_conntrack_max        # limit — table full = dropped conns
dmesg -T | grep conntrack                    # "nf_conntrack: table full, dropping packet"
sysctl net.ipv4.ip_local_port_range          # ephemeral ports (port exhaustion)
ss -s                                        # timewait counts
sysctl net.core.somaxconn                    # listen backlog limit
```
Symptoms: NAT boxes/proxies dropping new connections under load → conntrack full.
Many short-lived outbound conns failing → ephemeral port exhaustion / TIME_WAIT.

---

## 8. NetworkManager / netplan (config layer)

```bash
nmcli device status             # which devices NM manages, their state
nmcli connection show           # profiles
nmcli device show eth0          # IP/DNS/routes NM applied
netplan get                     # Ubuntu netplan config
netplan try                     # apply with auto-rollback in 120s (safe for remote!)
cat /etc/network/interfaces     # Debian legacy
```

---

## Decision tree: "Cannot connect to service X on host Y"

```
1. ping Y                → loss? → mtr Y (find the hop) ; no ICMP? don't panic, go on
2. nc -zv Y port         → refused  → service down or bound to 127.0.0.1 → on Y: ss -tlnp
                         → timeout  → firewall path: local iptables → (AWS: SG/NACL) → Y's iptables
3. dig service-name      → wrong/missing record? → 08-dns.md
4. curl -v http://Y:port → connects but app errors → 18-web-http-tls.md
5. still lost?           → tcpdump on BOTH ends and find where packets vanish
```
