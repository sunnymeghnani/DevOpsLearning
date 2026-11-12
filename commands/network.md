# Network: reachability, paths, sockets & speed

Work up the layers: is the link up, does the host answer, which path do packets take, is anything listening, and how fast does data really move? The first command people reach for usually answers only one of those questions, so each card says what its command adds.

| If you would reach for | Prefer | Because |
|---|---|---|
| `ping 8.8.8.8` | `mtr -rwbzc 100 8.8.8.8` | ping gives one end-to-end loss figure; mtr shows the hop where loss starts |
| `ping host` to ask "is the service up?" | `nc -zv -w 3 host 443` | the service lives on a TCP port, and "refused" and "timed out" point to different culprits |
| `netstat -tulpn` | `ss -ltnp 'sport = :443'` | same socket table, installed by default, and the filter cannot mistake `:80` for `:8081` |
| `ifconfig` | `ip -br addr`, `ip route get IP` | every address (ifconfig hides secondary ones) and the route and source IP the kernel really picks |
| `arp -a` | `ip neigh`, `arping -I IFACE IP` | neighbour states (`REACHABLE`, `FAILED`) and a direct layer-2 question, even when ICMP is blocked |
| `scp` or a download as a speed test | `iperf3 -c host -t 10`, then `-R` | measures the network alone, in each direction, without disks, TLS or the application |
| `netstat -s` | `nstat -n`, wait, then `nstat` | the change in each TCP counter while the problem happens, not totals since boot |
| `netplan apply` over SSH | `netplan try` | rolls the change back by itself if you lose the connection |

### ping — is the host answering, and how steady is the round trip?
Match: ping, ping6
Instead of: —
Safety: read-only · sends ICMP echo requests; -f (flood) needs root and can hurt a link

**In one line:** `ping` sends ICMP echo requests and times each reply, so it proves basic layer-3 reachability and gives you round-trip time plus an **end-to-end** packet-loss percentage.

**Read the command:** `ping -c 100 -i 0.2 10.0.1.20`

| Part | Meaning |
|---|---|
| `-c 100` | send 100 probes, then stop and print the summary (without it Linux ping runs until Ctrl-C) |
| `-i 0.2` | 0.2 s between probes (very short intervals need root) |
| `-s 1472 -M do` | 1472-byte payload with "don't fragment": 1472 + 28 bytes of headers = 1500, a quick MTU test |
| `-I eth1` | leave through this interface or source address |
| `-W 1` | wait at most 1 s for each reply |

**What the output tells you:**

```
64 bytes from 10.0.1.20: icmp_seq=1 ttl=64 time=0.42 ms
...
100 packets transmitted, 97 received, 3% packet loss, time 19803ms
rtt min/avg/max/mdev = 0.31/0.52/4.10/0.38 ms
```

`time=` is the round trip of one probe. The summary gives **loss for the whole path** and the spread of latency: `mdev` (jitter) is often more telling than `avg`. `ttl=` hints at how many hops away the host is, and at its OS (64 is typical of Linux, 128 of Windows).

**Why it is effective:** it is available everywhere, needs no server software, and in one line separates "the network path to this IP works" from "a higher layer (port, TLS, app) is broken".

**Compared with "it just times out":** an application error tells you only that something failed. A clean ping (0% loss, steady rtt) moves the investigation up to ports and the application; loss or jitter keeps it at the network layer.

**Trap:** ping does report loss, but only end-to-end: it cannot tell you *where* on the path packets disappear. Many clouds and firewalls also drop ICMP, so **no reply does not mean the host is down**: confirm with a TCP check (`nc -zv host 443`). A reply does not mean the service works either.

**Next step:** loss or jitter → run `mtr` to find the hop where it starts. Clean ping but the app fails → `nc -zv host PORT`, then `curl -v`. "Frag needed" with `-M do` → an MTU problem (VPNs and tunnels are typical).

### mtr — where along the path packets are lost
Match: mtr
Instead of: ping, traceroute
Safety: read-only · sends probe packets to every hop on the path

**In one line:** `mtr` is traceroute and ping combined: it probes **every hop** on the path repeatedly and shows loss and latency per hop, so you see **where** a problem starts, not just that one exists.

**Read the command:** `mtr -rwbzc 100 8.8.8.8`

| Part | Meaning |
|---|---|
| `-r` | report mode: run the cycles, then print one table (paste-able into a ticket) |
| `-w` | wide report: do not cut long hostnames |
| `-b` | show both the hostname and the IP of each hop |
| `-z` | show the AS number of each hop, i.e. which network owns it (your LAN, your ISP, a transit provider) |
| `-c 100` | 100 cycles: enough samples for a loss percentage you can trust |
| `-T -P 443` | probe with TCP SYN to port 443 instead of ICMP, when ICMP is filtered |
| `-u` | probe with UDP |

**What the output tells you:**

```
HOST: web01                        Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.|-- 10.0.1.1                    0.0%   100    0.4   0.5   0.3   1.1   0.1
  2.|-- 100.64.0.1                  0.0%   100    8.2   8.4   7.9  12.0   0.7
  3.|-- 198.51.100.9               60.0%   100    9.1   9.3   8.8  10.2   0.4
  4.|-- 203.0.113.50                0.0%   100   22.1  22.4  21.8  30.5   1.2
```

`Loss%` is per hop; `Snt` the probes sent; `Last/Avg/Best/Wrst` the latency in ms; `StDev` the jitter. Read it **top to bottom**: hop 1 is your gateway, the last line is the destination.

**Why it is effective:** a single ping to 8.8.8.8 says "3% loss" and stops there. mtr tells you whether the loss starts on your Wi-Fi or LAN (hop 1), at your ISP's edge (hop 2–3) or far away. That decides who has to fix it, and the report is evidence you can attach to an ISP or cloud ticket.

**Compared with `ping`:** ping measures only the end-to-end path. **Compared with `traceroute`:** traceroute takes one snapshot (3 probes per hop), so short bursts of loss are missed; mtr keeps sampling and builds statistics.

**Trap:** in the example, hop 3 shows 60% loss but the destination shows 0%: that router simply rate-limits its own ICMP replies, and traffic **through** it is fine. **Real loss starts at one hop and continues on every hop after it, down to the destination.** Also run mtr in both directions if you can; the return path is often different.

**Next step:** loss from hop 1 → check the local link (`ip -s link`, `ethtool`, Wi-Fi). Loss from an ISP hop onward → send the `-rwbzc 100` report to the ISP. ICMP blocked everywhere → repeat with `mtr -T -P 443`. Path clean but transfers slow → measure throughput with `iperf3`.

### traceroute / tracepath — which routers does the path cross, and where does the MTU shrink?
Match: traceroute, tracepath
Instead of: ping
Safety: read-only · sends probes with a rising TTL; `traceroute -T` needs root

**In one line:** both send probes with a growing TTL, so each router on the way answers "time exceeded" and the hops appear in order. `tracepath` needs no root and also reports the **path MTU**; `traceroute` can probe with ICMP or TCP when UDP is filtered.

**Read the command:** `tracepath -n 203.0.113.10`

| Part | Meaning |
|---|---|
| `tracepath` | UDP probes with a rising TTL, no root needed; learns the path MTU on the way |
| `-n` | addresses only, no reverse-DNS lookups (faster, and no DNS noise) |
| `203.0.113.10` | the destination |
| `traceroute -n host` | the classic tool: 3 UDP probes per hop, a time for each |
| `traceroute -I host` | ICMP echo probes instead, like Windows `tracert` |
| `traceroute -T -p 443 host` | TCP SYN probes to port 443, which most firewalls let through |

**What the output tells you:**

```
 1?: [LOCALHOST]                      pmtu 1420
 1:  10.8.0.1                                 21.034ms
 2:  198.51.100.1                             22.214ms
 3:  no reply
 4:  203.0.113.10                             42.551ms reached
     Resume: pmtu 1420 hops 4 back 4
```

One line per hop with its round-trip time. `pmtu 1420` on `[LOCALHOST]`: the route leaves through a tunnel (WireGuard here); a `pmtu` on a later line: a router in front of a smaller link. `Resume` gives the path MTU, the hop count and `back`, a guess of the return path's length (a different number hints at asymmetric routing). In traceroute, `* * *` is a silent hop, and `!H`, `!N`, `!X` mean host or network unreachable, or blocked by a firewall.

**Why it is effective:** ping gives end-to-end loss and delay but no route. The hop list shows which networks the traffic really crosses (LAN, VPN, ISP) and where the delay jumps; tracepath adds the MTU, the usual cause of "small requests work, big transfers hang".

**Compared with `ping`:** ping proves the destination answers, enough for "is it reachable?". These tools take one snapshot of the path; for loss per hop over time, use `mtr`.

**Trap:** `no reply` or `* * *` in the middle is usually a router that ignores probes: if later hops answer, the path works. tracepath learns the MTU from the same ICMP "fragmentation needed" messages that a PMTUD black hole drops, so `pmtu 1500` all the way does not prove that 1500-byte packets arrive.

**Next step:** path goes somewhere unexpected → `ip route get DEST`. Delay jumps at one hop and stays high → `mtr -rwbzc 100 DEST`. Small pmtu or a suspected black hole → bisect with `ping -M do -s 1472`. Stars from one hop to the end → `traceroute -T -p 443 DEST` or `nc -zv DEST 443`.

### ip link — is the interface up, with a carrier, the right MTU and the right bridge?
Match: ip link, ip l
Instead of: ifconfig
Safety: read-only for `show` · changes state: `set`, `add` and `del` reconfigure interfaces at once; taking down the interface you are connected through cuts your SSH session

**In one line:** `ip link` shows layer 2 only: every interface, whether it is switched on and has a carrier, its MAC, MTU and bridge. It also creates and changes interfaces.

**Read the command:** `ip link show ens18`

| Part | Meaning |
|---|---|
| `link` | layer-2 object: state, MAC, MTU (addresses: `ip addr`) |
| `show ens18` | one interface (omit for all); `show type bridge`, `show master docker0` filter |
| `-br` | one line per interface |
| `-d` | details: VLAN id, bridge, veth, VXLAN, WireGuard |
| `-s -s` | counters with the error breakdown (see the `ip` card) |
| `set eth1 up` / `down` | **changes state**: switch it on or off |
| `set r-eth0 mtu 1400` | **changes state**: new MTU at once, lost at reboot |
| `add br0 type bridge`, `set sw-p1 master br0` | **changes state**: create a bridge (or veth, dummy, vlan), plug a port in |

**What the output tells you:**

```
$ ip link show ens18
2: ens18: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc fq_codel state DOWN mode DEFAULT group default qlen 1000
    link/ether bc:24:11:5e:7a:01 brd ff:ff:ff:ff:ff:ff
$ ip -br link
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
ens18            DOWN           bc:24:11:5e:7a:01 <NO-CARRIER,BROADCAST,MULTICAST,UP>
veth3a1f2c9@if6  UP             9a:3c:51:0e:22:17 <BROADCAST,MULTICAST,UP,LOWER_UP>
```

Inside `< >`: `UP` = switched on, `LOWER_UP` = physical link up, `NO-CARRIER` = on, but nothing connected (cable, switch port, detached vNIC). `state` is the result; `UNKNOWN` is normal for `lo` and tunnels such as `wg0`. `@if6` on a veth is the interface number of its other end, inside a container's namespace; the long format adds `master br-…`, the bridge it is plugged into.

**Why it is effective:** "the network is down" becomes one of three facts: switched off (`set up` fixes it), no carrier (a physical or hypervisor problem), or up with a wrong MTU or bridge. `-br` fits a whole host, Docker veths included, on one screen.

**Compared with `ifconfig`:** ifconfig (net-tools, not installed by default on current Ubuntu) shows flags (`RUNNING` = carrier), MTU and counters, but not bridge membership or veth peers, and it cannot create bridges, veths or VLANs.

**Trap:** `UP` in the flags is not a link; only `LOWER_UP` is. `docker0` with `NO-CARRIER` just means no container is attached. `set` and `add` changes are runtime only (netplan restores the configured state at reboot), and `ip link set ens18 down` over SSH through ens18 locks you out.

**Next step:** `NO-CARRIER` → `ethtool ens18`, then the cable, switch port or VM NIC. Up but no address → `ip addr`, `networkctl status ens18`. Errors → `ip -s link show ens18`. MTU doubts → `tracepath`, `ping -M do -s 1472`. veth on the wrong bridge → `bridge link`, `docker network inspect`.

### ethtool — did the NIC negotiate the right speed and duplex, and is it counting errors?
Match: ethtool
Instead of: ip link
Safety: read-only as shown (some queries need root) · changes state: `-s`, `-G`, `-L` and `-K` reconfigure the NIC; `-s`, `-G` and `-L` reset the link on most drivers

**In one line:** `ethtool` asks the network driver what the physical link negotiated (speed, duplex, autonegotiation), which driver and firmware run it, and what its hardware counters, rings and queues look like.

**Read the command:** `ethtool eno1`

| Part | Meaning |
|---|---|
| `ethtool eno1` | link settings: speed, duplex, autonegotiation, `Link detected` |
| `-S eno1` | the driver's hardware counters (`rx_crc_errors`, `rx_missed_errors`…; names differ per driver) |
| `-i eno1` | driver, version, firmware and bus address, for vendor bug searches |
| `-g` / `-G eno1 rx 4096 tx 4096` | show / **change** the ring buffer sizes |
| `-l` / `-L ens3 combined 4` | show / **change** the number of queues (channels) |
| `-k` / `-K eno1 gro off` | show / **change** offloads (segmentation, GRO, checksums) |
| `-m` | SFP or fibre module data: optical power and temperature, if the module supports it |
| `-s eno1 autoneg on` | **change** speed, duplex or autonegotiation |

**What the output tells you:**

```
Settings for eno1:
    Supported link modes:   10baseT/Half 10baseT/Full
                            100baseT/Half 100baseT/Full
                            1000baseT/Full
    Link partner advertised link modes:  Not reported
    Speed: 100Mb/s
    Duplex: Half
    Auto-negotiation: on
    Link detected: yes
```

A gigabit NIC at `Speed: 100Mb/s` tops out near 94 Mbit/s; a cable with one broken pair falls back to 100 Mb exactly like this (gigabit needs all four pairs). `Duplex: Half` with autonegotiation on and the partner `Not reported` means the switch port is forced while this side negotiates: a **duplex mismatch**. `Link detected: no` means no carrier.

**Why it is effective:** a 100 Mb half-duplex link is simply "up" for every other tool. Only the driver knows what was negotiated, and `-S` shows errors at the hardware level, which explains "ping fine, transfers crawl, one direction worse".

**Compared with `ip link`:** ip link shows the carrier (`LOWER_UP`) and the kernel's counters, enough to know the cable is plugged in, but not speed, duplex or driver counters. Ping stays perfect through a duplex mismatch, because small packets rarely collide.

**Trap:** in VMs (virtio_net, vmxnet3, AWS ena) the speed is nominal or `Unknown!`; cable and CRC problems show on the hypervisor and the switch. Counters are cumulative: compare over time. `-s`, `-G` and `-L` drop the link for a second or more, so use a console and a maintenance window; every change is lost at reboot unless persisted.

**Next step:** wrong speed or duplex → autonegotiation on both ends, swap the cable, repeat `iperf3`. CRC errors rising → cable, patch port, switch port, SFP, in that order. Missed or no-buffer counters rising → bigger rings (`-G`), more queues (`-L`), `irqbalance`. All clean → `ss -ti` for TCP-level problems.

### ip addr — which addresses does this host have, and on which interface?
Match: ip addr, ip address, ip a
Instead of: ifconfig
Safety: read-only for `show` · changes state: `add` and `del` last until reboot; deleting the address you are connected through cuts your session

**In one line:** `ip addr` lists every interface with all of its IPv4 and IPv6 addresses and their prefix lengths: what this host *is* on the network, and which subnets it believes are directly connected.

**Read the command:** `ip -br addr`

| Part | Meaning |
|---|---|
| `-br` | brief: one line per interface with name, state and addresses |
| `addr` | the address object (`ip a` is the same) |
| `-4` / `-6` | only IPv4 / only IPv6 addresses |
| `show wg0` | one interface only |
| `show scope global` | hide loopback and link-local (`fe80::`) addresses: only what other hosts can reach |
| `-o` / `-j` | one line per address for `grep` and `awk` / JSON for `jq` |
| `add 10.0.1.5/24 dev eth1` | **changes state**: add an address, plus the connected route for 10.0.1.0/24 |
| `del 10.10.1.10/16 dev c-eth0` | **changes state**: remove it; routes through it disappear too |

**What the output tells you:**

```
lo               UNKNOWN        127.0.0.1/8 ::1/128
ens18            UP             192.0.2.10/24 fe80::be24:11ff:fe5e:7a01/64
ens19            DOWN
wg0              UNKNOWN        10.8.0.1/24
```

Column 2 is the operational state (`UNKNOWN` is normal for `lo` and tunnels). `192.0.2.10/24` is the address **and** its prefix: the /24 tells the kernel that 192.0.2.0–192.0.2.255 is on this wire, reachable without a router. `fe80::…/64` is IPv6 link-local, present everywhere and useless from other subnets. ens19 has no address, so it carries no IP traffic.

**Why it is effective:** the prefix length is what people misread, and this view puts it next to every address, secondary ones included (keepalived VIPs, addresses added by hand), for the whole host on one screen.

**Compared with `ifconfig`:** Linux ifconfig shows only the first IPv4 address of each interface (plus labelled aliases such as `eth0:1`), so a VIP added with `ip addr add` is invisible there. On macOS and BSD, ifconfig is the native tool and lists them all.

**Trap:** a wrong prefix looks perfectly normal here: 10.10.1.10/16 instead of /24 makes the host treat a remote subnet as local and ARP for it instead of using the gateway. `ip addr add` and `del` change the live host and are lost at reboot; make addresses permanent in netplan.

**Next step:** address missing or wrong → the netplan file, `networkctl status IFACE`, DHCP logs. Address fine but a host is unreachable → `ip route get IP` (look for `via`). Suspected duplicate → `arping -D -I IFACE IP`. Gateway questions → `ip neigh`.

### ip route — which way will a packet go, and with which source address?
Match: ip route, ip r
Instead of: route -n, netstat -rn
Safety: read-only for `show` and `get` · changes state: `add`, `del`, `replace` and `flush` act at once and last until reboot; deleting the default route can cut your session

**In one line:** `ip route` prints the routing table; `ip route get DEST` makes the kernel do the real lookup for one destination and prints its decision: gateway, outgoing interface and source address.

**Read the command:** `ip route get 203.0.113.10`

| Part | Meaning |
|---|---|
| `route get 203.0.113.10` | the kernel's real decision for this one destination |
| `from 10.0.2.10` | …for a packet from this source address (multi-homed hosts) |
| `ip route`, `ip route show default` | the main table, or only its default route |
| `show table 100`, `show table all` | other routing tables (VPNs, policy routing); `-6` for IPv6 |
| `add 203.0.113.40/32 via 10.0.20.1 dev eno1 mtu 1400` | **changes state**: a host route with its own MTU |
| `del default`, `replace default via 10.10.1.1` | **changes state**: remove or swap the default route |
| `flush cache` | **changes state**: forget learned path MTUs |

**What the output tells you:**

```
$ ip route
default via 192.0.2.1 dev ens18 proto static
10.8.0.0/24 dev wg0 proto kernel scope link src 10.8.0.1
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10
$ ip route get 203.0.113.10
203.0.113.10 via 192.0.2.1 dev ens18 src 192.0.2.10 uid 1000
    cache
```

`via`: the next-hop router; **no `via`**: the destination counts as directly connected (subnet, Docker bridge, tunnel) and the host ARPs for it itself. `dev`: the outgoing interface. `src`: the address the far end and its firewall will see. `proto kernel` routes come from an address's prefix; `metric` breaks ties (lower wins); `cache expires 587sec mtu 1420` is a smaller path MTU learned for that destination.

**Why it is effective:** the decision combines longest-prefix match, metrics, policy rules and several tables. `ip route get` lets the kernel do that work and shows the result, source address included: a Docker bridge swallowing an office subnet, or a VPN capturing traffic, shows up in one line.

**Compared with `route -n`:** route -n and netstat -rn print the main IPv4 table, enough to see the default gateway on an old box, but they show no other tables or rules and leave the matching to you.

**Trap:** `get` shows only this host's decision: it does not test the gateway's MAC, firewalls, NAT or the return path. Hand-made changes last until reboot (a deleted DHCP route even returns at the next renewal), and `ip route del default` over SSH from another subnet locks you out. Table right but traffic goes elsewhere → check `ip rule`.

**Next step:** `dev docker0` or `br-…` for an outside address → Docker pool overlap (`default-address-pools`). Wrong source on a multi-homed host → `ip rule`, source-based routing in netplan. No `via` for a remote subnet → wrong prefix in `ip addr`. Decision fine → `ip neigh` for the gateway, then `mtr` or `tracepath`.

### ip neigh — does this host know the MAC address of its gateway or peer?
Match: ip neigh, ip neighbor, ip neighbour, ip n
Instead of: arp -a
Safety: read-only for `show` · changes state: `flush`, `del` and `replace` edit the cache; flushed entries are relearned, a wrong static entry breaks traffic until removed

**In one line:** `ip neigh` shows the neighbour table, the IP-to-MAC answers learned by ARP (IPv4) and Neighbour Discovery (IPv6), with a state for each, so you know whether layer 2 to the gateway works before you debug anything above it.

**Read the command:** `ip neigh show 192.0.2.1`

| Part | Meaning |
|---|---|
| `neigh` | the neighbour table (ARP and IPv6 ND entries) |
| `show 192.0.2.1` | one address only: the gateway, here |
| `show nud failed` | only entries in one state (`nud` = neighbour unreachability detection) |
| `-6` | IPv6 neighbours only |
| `-n client` | the table inside namespace `client` (the labs) |
| `flush dev c-eth0`, `flush all` | **changes state**: forget learned entries so they are resolved again |
| `replace 10.10.1.1 lladdr 02:00:00:00:00:99 dev c-eth0 nud permanent` | **changes state**: a static entry (the lab's deliberately wrong one) |

**What the output tells you:**

```
192.0.2.1 dev ens18 lladdr 00:1a:2b:3c:4d:5e REACHABLE
192.0.2.53 dev ens18 lladdr 00:1a:2b:3c:4d:60 STALE
192.0.2.77 dev ens18 FAILED
10.10.1.1 dev c-eth0 lladdr 02:00:00:00:00:99 PERMANENT
```

`REACHABLE`: confirmed recently. `STALE`: still valid, re-checked on next use (normal). `DELAY`/`PROBE`: being re-checked now. `INCOMPLETE`: asked, no answer yet. `FAILED`: nobody answered, so the host is down, in another VLAN, or the IP is wrong. `PERMANENT`: a static entry set by an admin or a tool.

**Why it is effective:** "I cannot reach the gateway" and "the gateway is fine, the problem is further away" lead to different teams. One look at the gateway's entry tells you which, and a MAC that differs from the gateway's real one exposes a stale or duplicate entry.

**Compared with `arp -a`:** arp -a (Linux, macOS and Windows) lists the IPv4 cache with MACs, enough for a quick look, but without the state names and without IPv6 neighbours.

**Trap:** remote hosts never appear here, only the gateway; a remote IP in this table means the host thinks it is local (wrong prefix). `STALE` is not an error. A `FAILED` entry can be old: check right after a fresh attempt. A `nud permanent` entry stays until deleted and silently breaks traffic when the real MAC changes.

**Next step:** gateway `FAILED` or `INCOMPLETE` → `arping -I IFACE GW`, `ip link` for the carrier, then the switch port's VLAN. A MAC that keeps changing → `ip monitor neigh`, and `arping -D` for a duplicate IP. Gateway `REACHABLE` → `ip route get`, then `mtr`.

### arping — does anyone on this segment answer for this IP, and with which MAC?
Match: arping
Instead of: ping
Safety: read-only · sends ARP requests on one segment and needs root; `-U` updates other hosts' ARP caches

**In one line:** `arping` asks the local segment at layer 2 "who has this IP?" and prints each answer with its MAC address, so it works where ping is blocked and it exposes duplicate addresses.

**Read the command:** `arping -D -c 2 -I ens18 192.0.2.10`

| Part | Meaning |
|---|---|
| `-D` | duplicate address detection: ask from 0.0.0.0, stop at the first reply; a reply means another machine uses this IP (exit 1), silence means it is free (exit 0) |
| `-c 2` | send at most 2 requests |
| `-I ens18` | the interface, i.e. the segment, to ask on |
| `192.0.2.10` | the address in question (here this host's own) |
| `-U` | unsolicited ARP: announce a new MAC after a failover (**changes** neighbours' caches) |

**What the output tells you:**

```
$ sudo arping -c 2 -I ens18 192.0.2.1
ARPING 192.0.2.1 from 192.0.2.10 ens18
Unicast reply from 192.0.2.1 [00:1A:2B:3C:4D:5E]  0.711ms
Unicast reply from 192.0.2.1 [00:1A:2B:3C:4D:5E]  0.644ms
...
$ sudo arping -D -c 2 -I ens18 192.0.2.10
ARPING 192.0.2.10 from 0.0.0.0 ens18
Unicast reply from 192.0.2.10 [00:50:56:9A:11:22]  0.811ms
Sent 1 probes (1 broadcast(s))
Received 1 response(s)
```

The gateway answers from its MAC, so layer 2 to the router works. In `-D` mode any reply means **someone else owns your IP**; two different MACs answering for one address mean the same.

**Why it is effective:** a host's firewall can drop ping, but a host on your segment must answer ARP for its own address. So arping proves "this IP is alive on this wire, at this MAC", and catches the duplicate IP behind "connections randomly die or land on the wrong server".

**Compared with `ping`:** ping tests IP reachability end to end and crosses routers, so it is the test for remote hosts. arping never leaves the segment: it answers same-subnet questions about gateways, VIPs and duplicates.

**Trap:** two different `arping` programs exist; these flags are iputils-arping's (Ubuntu package `iputils-arping`), and the package named `arping` behaves differently. An off-subnet address never answers, and a router with proxy ARP may answer for addresses that are not its own. `-U` rewrites other hosts' caches: use it only for an address you own.

**Next step:** no reply from the gateway → `ip link` (carrier), the switch port's VLAN, `ip neigh show GW`. Duplicate → find the other MAC's owner (switch MAC table, DHCP leases, hypervisor) and change one address. A MAC that keeps changing → `ip monitor neigh`, keepalived logs.

### bridge — which ports, MACs and VLANs does this Linux bridge have?
Match: bridge
Instead of: brctl show
Safety: read-only for `show` and `link` · changes state: `bridge vlan add/del` change forwarding at once (runtime only)

**In one line:** a Linux bridge is a software switch (`docker0`, `br-…`, Proxmox `vmbr0`); `bridge` shows its switch view: ports and their STP state, the MAC table it learned, and which VLANs each port carries.

**Read the command:** `bridge fdb show br br-6c1e2f0a9b3d`

| Part | Meaning |
|---|---|
| `fdb` | forwarding database: the MAC table (which MAC sits behind which port) |
| `show br br-6c1e2f0a9b3d` | only this bridge (here a Docker Compose network) |
| `link`, `link show master br-lab` | bridge ports with their state (`forwarding`, `blocking`, `disabled`) |
| `vlan show` | the VLANs on each port, with `PVID` (where untagged frames go) and `Egress Untagged` |
| `-c` | compress VLAN lists into ranges such as `2-4094` |
| `vlan add dev sw-p1 vid 10 pvid untagged`, `vlan del dev sw-p1 vid 1` | **changes state**: make sw-p1 an access port in VLAN 10, then drop VLAN 1 from it |

**What the output tells you:**

```
$ bridge link
12: veth3a1f2c9@if11: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 master br-6c1e2f0a9b3d state forwarding priority 32 cost 2
$ bridge fdb show br br-6c1e2f0a9b3d | grep -v permanent
02:42:ac:12:00:03 dev veth3a1f2c9 master br-6c1e2f0a9b3d
$ bridge -c vlan show dev tap101i0
port              vlan-id
tap101i0          20 PVID Egress Untagged
```

The container's veth is plugged into the bridge and `forwarding`, and the bridge has learned the container's MAC behind it. `permanent` entries are the bridge's and ports' own addresses, hence the `grep -v`. The Proxmox VM port `tap101i0` is an access port in VLAN 20.

**Why it is effective:** `ip link show master BR` says which ports exist; `bridge` says whether frames can flow (STP state, learned MACs, VLAN membership), which proves a Docker network or a VLAN-aware Proxmox bridge is wired correctly before you blame the physical switch.

**Compared with `brctl show`:** brctl (bridge-utils, deprecated, often not installed) lists bridges and their ports, enough for a quick look, but has no view of VLAN filtering.

**Trap:** on a VLAN-aware bridge a port without the VLAN, or with the wrong PVID, drops frames silently while every link shows `UP`; the physical switch port must carry that VLAN too. `vlan add/del` act at once and vanish at reboot unless the Proxmox or netplan config holds them.

**Next step:** port not forwarding → `ip link` for the veth, `docker network inspect`. VLAN right on the host but no answer → `tcpdump -eni UPLINK vlan 20`, then the switch trunk config. MAC never learned → capture on that port.

### ip netns — run a command inside another network namespace
Match: ip netns
Instead of: —
Safety: needs root · changes state: `add`/`del` and whatever you run inside change that namespace; named namespaces vanish at reboot

**In one line:** a network namespace is a separate network stack (its own interfaces, routes, firewall and sockets) inside the same kernel; `ip netns exec NS COMMAND` runs any program inside one, which is how the handbook's client/router/server labs work and how containers get their network.

**Read the command:** `ip netns exec client ping -c2 10.10.2.20`

| Part | Meaning |
|---|---|
| `netns` | named network namespaces (they live under `/run/netns`) |
| `exec client` | run the rest of the line inside the namespace `client` |
| `ping -c2 10.10.2.20` | the program to run there (`curl`, `ss`, `tcpdump`, `nft` work too) |
| `ip netns` | list the named namespaces |
| `add red`, `del red` | **changes state**: create or delete a namespace |
| `ip -n client route` | shortcut for `ip` itself, the same as `ip netns exec client ip route` |
| `ip link add c-eth0 netns client type veth peer name r-eth0 netns router` | **changes state**: a virtual cable with one end in each namespace |
| `ip link set veth-red netns red` | **changes state**: move an interface into a namespace |

**What the output tells you:**

```
$ ip netns exec client ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
c-eth0           UP             10.10.1.10/24 fe80::d4b2:4fff:fe1a:2b3c/64
$ ip netns exec client ip route
default via 10.10.1.1 dev c-eth0
10.10.1.0/24 dev c-eth0 proto kernel scope link src 10.10.1.10
```

Inside the namespace only its own interfaces and routes exist: the host's ens18 and default route are invisible. The same isolation is why a container cannot reach a service on the host's 127.0.0.1, and why `ss` on the host does not list a container's listeners.

**Why it is effective:** one VM becomes a client, a router and a server, so you can break and repair routing, NAT, MTU and firewalls safely; and the host's tools (tcpdump, ss, curl) run in a namespace that has none installed.

**Trap:** Docker does not register container namespaces in `/run/netns`, so `ip netns` does not list them: use `nsenter -t PID -n` with the PID from `docker inspect -f '{{.State.Pid}}' NAME`. Names do not resolve in the lab namespaces: their `/etc/resolv.conf` points at 127.0.0.53, the host's loopback, not theirs (an `/etc/netns/NS/resolv.conf` file fixes that). Commands run with `exec` really change that namespace: `sysctl -w net.ipv4.ip_forward=0` there stops the lab router.

**Next step:** a lab step fails → diagnose from inside with `ip -n NS route get IP`, `ip -n NS neigh` and `ip netns exec NS tcpdump -ni IFACE`. Container networking → `nsenter -t PID -n ss -ltnp`. Clean up with `ip netns del NS`.

### ip — interface counters, policy rules and live events
Match: ip
Instead of: netstat -i, ifconfig
Safety: read-only for `-s`, `rule` and `monitor` · changes state: `ip rule add`/`del` change routing at once, until reboot

**In one line:** the `ip` uses without a card of their own: `-s` adds packet, error and drop counters; `ip rule` lists the policy rules that pick a packet's routing table; `ip monitor` prints changes as they happen.

**Read the command:** `ip -s link show eth0`

| Part | Meaning |
|---|---|
| `-s` | counters since boot: bytes, packets, errors, drops; `-s -s` adds the error breakdown |
| `link show eth0` | the interface (see the `ip link` card) |
| `rule` | policy rules in priority order: which table each packet consults |
| `-n client rule add from 10.10.1.11 table 100 priority 1000` | **changes state**: packets from 10.10.1.11 use table 100 (in namespace `client`) |
| `monitor neigh` | neighbour (ARP) changes, live until Ctrl-C (`monitor route`, `monitor link` likewise) |
| `-br`, `-j`, `-4`/`-6`, `-n NS` | global options: brief, JSON, one address family, another namespace |

**What the output tells you:**

```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 52:54:00:12:34:56 brd ff:ff:ff:ff:ff:ff
    RX:  bytes packets errors dropped  missed   mcast
    9831245113 9123441  18342    4512       0   20412
    TX:  bytes packets errors dropped carrier collsns
    4432115098 6234112      0       0       0   91234
```

RX `errors`: frames that arrived damaged (CRC: cable, SFP, duplex mismatch). RX `dropped`: discarded by the kernel or driver, often harmless. `missed`: the NIC's ring was full because the host did not empty it in time. `collsns`: collisions exist only in half duplex, so on a switched network they mean a duplex mismatch, as here. `ip rule` lists `0: from all lookup local`, your rules, then `32766: from all lookup main` and `32767: from all lookup default`.

**Why it is effective:** the counters separate a physical fault (errors, collisions) from a host that cannot keep up (missed, drops). `ip rule` explains "the route looks right but packets go elsewhere": VPN clients (Tailscale's table 52) and source-based routing add rules. `ip monitor` catches intermittent changes.

**Compared with `netstat -i`:** netstat -i and ifconfig show the same per-interface counters, enough for a glance, but without the error breakdown or policy rules.

**Trap:** counters add up since boot: 4512 drops in three months mean nothing; watch whether they rise while you reproduce the problem (`watch -d -n 2 'ip -s link show eth0'`). In a VM, cable errors are counted on the hypervisor host. `ip rule add` changes routing at once and is lost at reboot (netplan `routing-policy` persists it).

**Next step:** errors or collisions rising → `ethtool eth0`, `ethtool -S eth0`. `missed` rising → `ethtool -g` and `-l`, softirq CPU. Traffic in an unexpected table → `ip route show table N`, `ip route get DEST from SRC`. Gateway MAC changing → duplicate IP or failover: `arping -D`.

### ipcalc — what network, broadcast and host range does this address and prefix give?
Match: ipcalc
Instead of: —
Safety: read-only · pure calculation, sends nothing

**In one line:** `ipcalc` turns an address with a prefix length into its netmask, network, broadcast and usable host range, so you can check subnet arithmetic before it goes into netplan, Docker, Kubernetes or a VPN config.

**Read the command:** `ipcalc 10.20.35.200/20`

| Part | Meaning |
|---|---|
| `10.20.35.200` | any address inside the network you want to understand |
| `/20` | the prefix length: the first 20 bits are the network part |

**What the output tells you:**

```
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

`Network` to `Broadcast` is the whole range; `HostMin` to `HostMax` are the usable addresses; the space inside the binary column marks the prefix boundary. Two addresses are in the same subnet only if they share the same `Network`.

**Why it is effective:** a /16 typed instead of /24, or a Docker pool overlapping an office range, looks like a routing or firewall failure. ipcalc answers in a second whether two addresses share a subnet and what a prefix covers, before you apply anything.

**Trap:** Ubuntu's `ipcalc` (this output) and RHEL's `ipcalc` are different programs with different options and output. The "Class A" label is historical; only the prefix matters. It checks arithmetic, not the host: `ip route get` shows what the kernel really does, and clouds reserve extra addresses (AWS keeps 5 per subnet).

**Next step:** compare with `ip -br addr` and `ip route` on the host. Overlap with a Docker pool → `default-address-pools` in daemon.json. Wrong prefix in production → fix the netplan file and apply it with `netplan try`.

### ss — who owns this port, and what state are its connections in?
Match: ss
Instead of: netstat, lsof -i
Safety: read-only · run it with sudo, or `-p` shows no process for sockets that other users own

**In one line:** `ss` reads the kernel's socket table: which process listens on which address and port, every connection with its state and queues, even TCP internals, and its filters select exactly the sockets you ask for.

**Read the command:** `ss -ltnp 'sport = :443'`

| Part | Meaning |
|---|---|
| `-l` | listening sockets only (without it: connections) |
| `-t` / `-u` / `-x` | TCP / UDP (HTTP/3 is udp/443) / unix sockets |
| `-n` | numeric: `:443`, not `:https`; no DNS |
| `-p` | owning process: name, PID, file descriptor |
| `'sport = :443'` | filter on the local port; also `dport`, `src`, `dst`, combined as `'( … or … )'`; quote it |
| `state established` | one TCP state (`time-wait`, `close-wait`, `syn-sent`…); the State column disappears |
| `-i` | TCP internals per connection: rtt, cwnd, retransmits |
| `-s` / `-H` | totals per state / no header, for scripts |

**What the output tells you:**

```
$ sudo ss -ltnp 'sport = :443'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1344,fd=6),("apache2",pid=1201,fd=6))
$ sudo ss -Hltnp '( sport = :3306 or sport = :8081 )'
LISTEN 0      151        127.0.0.1:3306      0.0.0.0:*    users:(("mysqld",pid=1120,fd=23))
LISTEN 0      4096         0.0.0.0:8081      0.0.0.0:*    users:(("docker-proxy",pid=3302,fd=7))
```

Local address `*` = every IPv4 and IPv6 address, `0.0.0.0` = every IPv4 address, `127.0.0.1` = this host only (remote clients are refused). Several PIDs on one socket are a parent and its workers (the lowest PID is usually the parent). On a LISTEN line `Recv-Q` is the accept queue, `Send-Q` its limit. `docker-proxy` is a published container port. This is the Apache-versus-Dokploy picture: while Apache holds `*:443`, Traefik cannot bind 443 (`address already in use`).

**Why it is effective:** one command goes from port to PID, the start of the chain port → process → unit → config. The filter cannot confuse `:80` with `:8081` the way `grep :80` does, state filters count `TIME_WAIT` or `CLOSE_WAIT` piles, and `-i` shows why one connection is slow.

**Compared with `netstat`:** netstat -tulpn lists the same listeners, but net-tools is not installed by default on current Ubuntu and has no filters or TCP internals; fine on an old box. `lsof -nP -iTCP -sTCP:LISTEN` answers from the process side, more slowly.

**Trap:** an empty result means no socket in *this* network namespace, not a free port: containers have their own, and Docker without its userland proxy or kube-proxy NodePorts answer through NAT rules with no socket at all. Without sudo the Process column is blank for other users' sockets. Listening does not mean reachable: test from another host.

**Next step:** wrong process on the port → `systemctl status PID`, fix that unit's config. Bound to 127.0.0.1 → change the bind address. Port answers, no listener → `ipvsadm -Ln`, `conntrack -L -p tcp --dport PORT`. Listening but unreachable → `nc -zv -w 3 HOST PORT` from outside, then the firewall. `CLOSE_WAIT` growing → the app does not close connections. One slow connection → `ss -tin dst IP`.

### netstat — sockets, routes and counters on old Linux, Windows and macOS
Match: netstat
Instead of: —
Safety: read-only · Linux `-p` needs root to name other users' processes; Windows `-b` needs an elevated prompt

**In one line:** `netstat` is the older, cross-platform socket lister. On Linux `ss` and `ip` replace it, but on Windows (`netstat -ano`) and macOS it is still the built-in way to see listeners, connections, routes and protocol counters.

**Read the command:** `netstat -ano`

| Part | Meaning |
|---|---|
| `-a` | all sockets: listening and connected |
| `-n` | numeric addresses and ports, no name lookups |
| `-o` | **Windows**: the owning PID. On **Linux** `-o` shows timers instead |
| `-b` | Windows: the program (and service) behind each socket; elevated prompt, slow |
| `-p tcp` | Windows and macOS: one protocol only. On **Linux** `-p` is the PID/program column |
| `-t -u -l` | Linux: TCP, UDP, listening only, so `netstat -tulpn` matches `ss -tulpn` |
| `-s` | per-protocol counters since boot: retransmits, resets, listen overflows |
| `-r` / `-i` | the routing table / per-interface counters (macOS `-ib -I en0` adds bytes) |

**What the output tells you:**

```
  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:443            0.0.0.0:0              LISTENING       4
  TCP    127.0.0.1:3000         0.0.0.0:0              LISTENING       9412
  TCP    10.0.1.10:52011        10.0.2.9:1433          ESTABLISHED     7788
  TCP    [::]:443               [::]:0                 LISTENING       4
```

`0.0.0.0:443` listens on every IPv4 address; `127.0.0.1:3000` is local only, the classic "works on the server, refused from outside". The PID leads to the program: `tasklist /fi "PID eq 9412"`. PID 4 is "System": the kernel HTTP driver (http.sys) holds the port for IIS, WinRM or another registered service. Thousands of `TIME_WAIT` lines mean connection churn; a `SYN_SENT` that stays means the remote side does not answer.

**Why it is effective:** on Windows and macOS it is always installed and works the same over RDP, a jump host or a support call; `-ano` answers "which PID owns port 443?" on one screen.

**Trap:** the same letters mean different things per OS: Linux `-o` shows timers, not PIDs, and Linux `-p` shows programs while Windows `-p` filters a protocol. On Windows, `findstr :443` also matches `:4430`; use `findstr /C:":443 "` with the trailing space. Plain `netstat -an` on macOS shows no PIDs (use `lsof -nP -iTCP -sTCP:LISTEN`). On Linux, net-tools is not installed by default on current Ubuntu.

**Next step:** Windows PID 4 → `netsh http show servicestate`; any other PID → `tasklist /svc /fi "PID eq N"` or `Get-NetTCPConnection`. Linux → `ss -ltnp 'sport = :PORT'` and `nstat` instead. macOS → `lsof -nP -iTCP:PORT -sTCP:LISTEN`.

### nc — does this TCP or UDP port answer from here?
Match: nc, ncat, telnet
Instead of: ping, telnet
Safety: read-only · `-z` opens and closes one connection per port; `-l` opens a listening port on this host until you stop it

**In one line:** `nc -zv` makes a real TCP connection to one port and tells you which of three things happened: it succeeded, it was refused, or it timed out. Each answer points to a different culprit.

**Read the command:** `nc -zv -w 3 192.0.2.10 443`

| Part | Meaning |
|---|---|
| `-z` | connect and close at once, sending no data |
| `-v` | print the result (otherwise only the exit status tells) |
| `-w 3` | give up after 3 s, not the kernel's default of about two minutes |
| `192.0.2.10 443` | host and port; `8000-8010` checks a range |
| `-u` / `-6` | UDP (unreliable, see the trap) / IPv6 only |
| `-l 9000` | listen on 9000 to test a path before the app exists (`-k` keeps listening) |
| `-q 2` | quit 2 s after the input ends, so a piped request gets its answer (Ubuntu's netcat-openbsd) |

**What the output tells you:**

```
$ nc -zv -w 3 10.0.1.20 5432
Connection to 10.0.1.20 5432 port [tcp/postgresql] succeeded!
$ nc -zv -w 3 10.0.1.20 8080
nc: connect to 10.0.1.20 port 8080 (tcp) failed: Connection refused
$ nc -zv -w 3 10.0.2.9 443
nc: connect to 10.0.2.9 port 443 (tcp) timed out: Operation now in progress
```

**succeeded**: the handshake completed; path and listener are fine. **refused**: the packet arrived and the host (or a rejecting firewall rule) answered with a reset: the path works, but nothing listens on that address (service down, or bound to 127.0.0.1). **timed out**: no answer at all; something dropped the packets (firewall, security group, routing, wrong IP), and the host may be perfectly healthy.

**Why it is effective:** it tests what users actually use, the TCP port, so it works where ICMP is blocked, and its three outcomes split "service problem" from "network or firewall problem" in a second.

**Compared with `ping`:** ping tests ICMP only: it can succeed while the port is firewalled, or fail while the service works. **Compared with `telnet`:** the same connect test, without a timeout or UDP, and often not installed; on Windows use `Test-NetConnection host -Port 443`.

**Trap:** "succeeded" proves only the handshake: a reverse proxy, docker-proxy or load balancer accepts connections even when the app behind it is down (follow up with `curl -v`). With `-u`, "succeeded" only means no ICMP error came back; test UDP services with their own protocol (`dig @HOST`). Testing a server from itself skips the outside firewall. netcat-traditional needs `-l -p PORT`, and RHEL's `nc` is Nmap's ncat, with different options.

**Next step:** refused → on the target, `ss -ltnp 'sport = :PORT'` (down? bound to 127.0.0.1?). Timed out → firewalls on the path (ufw or nftables on the target, security groups), `tcpdump` on the target to see whether SYNs arrive, `traceroute -T -p PORT`. Succeeded but the app fails → `curl -v`, the application logs. Related: `telnet host 3306` is the same connect test: `Connected to …` (leave with Ctrl+] then `quit`), `Connection refused`, or a hang at `Trying …`; it sends everything in clear text, so never log in with it.

### nmap — which ports are open, closed or filtered from where I stand?
Match: nmap
Instead of: nc -zv
Safety: read-only for the target, but active probing: scan only hosts you are authorised to test; as root nmap sends raw SYN probes, and `-sU` needs root

**In one line:** `nmap` probes many ports and hosts at once and classifies each port as **open**, **closed** or **filtered**: what a client in your position can really reach through firewalls and NAT.

**Read the command:** `nmap -Pn -p 22,80,443,3000,3306,8081 192.0.2.10`

| Part | Meaning |
|---|---|
| `-Pn` | skip the "is it up?" probe and scan anyway (hosts that drop ping look down otherwise) |
| `-p 22,80,443,3000,3306,8081` | these TCP ports only; `-p-` = all 65535; default: the 1000 most common |
| `192.0.2.10` | the target (a range such as `10.0.1.0/24` works too) |
| `-sV` | identify the service and version behind open ports |
| `-sU` | UDP scan (slow, often ambiguous) |
| `-sn` | host discovery only: which IPs answer |
| `--min-rate 1000`, `-oX FILE` | at least 1000 probes per second / XML output for `ndiff` |
| `--script ssl-enum-ciphers` | an NSE script listing TLS versions and ciphers |

**What the output tells you:**

```
PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
443/tcp  open   https
3000/tcp closed ppp
3306/tcp closed mysql
8081/tcp open   blackice-icecap
```

**open**: something accepted the handshake. **closed**: the host answered with a reset, so the path works but nothing listens on a reachable address (MySQL is bound to 127.0.0.1 here). **filtered**: no answer, a firewall drops the probes. `SERVICE` is only a guess from the port number (8081 is not "blackice"); `-sV` or `curl -v` shows what really answers.

**Why it is effective:** `ss` shows what is bound; nmap shows what is reachable. Here 8081 is open although UFW does not allow it: a Docker-published port bypassing UFW, which only an outside scan reveals. Saved `-oX` scans compared with `ndiff` catch newly exposed ports.

**Compared with `nc -zv`:** nc checks one port (or a small range) with a plain connect, enough to test one service. nmap scales to every port and host, and separates closed from filtered in one report.

**Trap:** scanning a host from itself, or from its own subnet, skips the firewalls outside clients go through: scan from where the clients are. Without `-p`, a service on port 18000 can be missed. UDP results like `open|filtered` mean "no answer", not "open". Scans trigger IDS, fail2ban or CrowdSec blocks, and on hosts you do not own they may break policy or law.

**Next step:** unexpected open port → `ss -ltnp 'sport = :PORT'` on the target, then bind it to 127.0.0.1 or stop publishing it. filtered where you expect open → the firewall chain (ufw, nftables, security groups). closed where you expect open → the service or its bind address.

### socat — talk to a unix socket, such as HAProxy's runtime API
Match: socat
Instead of: nc -U
Safety: read-only for `show` commands · the same socket accepts state-changing commands (`disable server`, `set weight`) that act immediately

**In one line:** `socat` connects any two data channels (stdin/stdout, files, TCP, UDP, unix sockets, TLS) and copies data between them; the handbook uses it to send a command to HAProxy's admin socket and read the answer.

**Read the command:** `socat stdio /run/haproxy/admin.sock`

| Part | Meaning |
|---|---|
| `socat` | relay data between two addresses, in both directions |
| `stdio` | first address: this shell's stdin and stdout |
| `/run/haproxy/admin.sock` | second address: a path; socat opens it, which for a unix socket means connecting to it |
| `echo 'show stat'` piped in | the command HAProxy should run; the answer comes back on stdout |
| `show servers state be_git` | another command: the runtime state of each server in backend `be_git` |
| `TCP-LISTEN:8080,fork TCP:10.0.1.20:80` | a typical other use: relay local port 8080 to 10.0.1.20:80 (**opens a port**) |

**What the output tells you:** the handbook pipes `show stat` through `cut -d, -f1,2,18 | column -s, -t`:

```
# pxname  svname    status
fe_web    FRONTEND  OPEN
be_app    app1      UP
be_app    app2      DOWN
be_app    BACKEND   UP
```

Field 1 is the proxy (frontend or backend), field 2 the server or the `FRONTEND`/`BACKEND` summary row, field 18 the status: `UP`, `DOWN`, `MAINT` (put in maintenance by an admin), `OPEN` for a frontend, `no check` when health checks are off. Here app2 fails its health check.

**Why it is effective:** the stats socket is HAProxy's live truth: which servers its health checks mark DOWN right now, without a dashboard or a reload. socat makes that a one-line, scriptable request.

**Compared with `nc -U`:** OpenBSD nc can also connect to a unix socket and is enough for a one-shot command; socat joins any pair of addresses with options (TLS, forking listeners) and is what HAProxy's own documentation uses.

**Trap:** "Permission denied" or "No such file or directory" means missing sudo or a wrong path: both come from the `stats socket` line in haproxy.cfg. Commands such as `disable server` or `set server … state maint` take effect at once and are lost at the next reload unless a server-state file keeps them.

**Next step:** a server DOWN → `curl -v` its health-check URL from the HAProxy host, then that backend's logs. Everything UP but clients fail → the frontend's listener (`ss -ltnp`), certificates, the HAProxy log.

### tcpdump — did the packet leave, did it arrive, and what came back?
Match: tcpdump
Instead of: ping, nc -zv
Safety: needs root · read-only for traffic, but captures can hold passwords, cookies and personal data: treat pcap files as secrets, and always limit with `-c` or rotation

**In one line:** `tcpdump` copies the packets the kernel sees on an interface and prints or saves them. It is the ground truth: whether a packet left, whether it arrived, and what the answer was.

**Read the command:** `tcpdump -tni any host 198.51.100.20 and tcp port 443 -c 6`

| Part | Meaning |
|---|---|
| `-t` | no timestamps (shorter lines for a ticket) |
| `-n` | no reverse DNS (`-nn`: numeric ports too) |
| `-i any` | every interface; lines then show the interface and `In`/`Out` |
| `host 198.51.100.20 and tcp port 443` | the BPF capture filter: this client's HTTPS only (quote filters with brackets or parentheses) |
| `-c 6` | stop after 6 packets; always limit on a busy host |
| `-w FILE` / `-r FILE` | save for Wireshark / read a saved capture |
| `-e` | MAC addresses and VLAN tags |
| `-s 128`, `-C 100 -W 5` | headers only / rotate 100 MB files, keep 5 |

**What the output tells you:**

```
ens19 In  IP 198.51.100.20.53122 > 10.0.2.10.443: Flags [S], seq 1880211, …
ens18 Out IP 10.0.2.10.443 > 198.51.100.20.53122: Flags [S.], seq 990121, ack 1880212, …
ens19 In  IP 198.51.100.20.53122 > 10.0.2.10.443: Flags [S], seq 1880211, …
```

Flags: `[S]` SYN (new connection), `[S.]` SYN-ACK (accepted), `[.]` ACK, `[P.]` data, `[F.]` FIN (close), `[R]`/`[R.]` reset (refused or aborted). Here the SYN arrives on ens19, the SYN-ACK leaves through ens18, and the client repeats its SYN: the reply takes the wrong interface and never arrives (asymmetric routing on a host with two networks).

**Why it is effective:** every other tool infers; a capture shows. Taken at both ends, it turns "the network is broken" into a fact such as "the SYN reaches the server and the server never answers", which says whose problem it is.

**Compared with `nc -zv` and `ping`:** they report success, refusal or timeout from the client's side only. A timeout can mean "never arrived" or "the reply got lost"; only a capture on the server tells which.

**Trap:** you see only what crosses the interface you capture on: no packets can mean the wrong interface (start with `-i any`) or an application that never sent (DNS failed). Incoming packets are captured before the local firewall, so a packet in the capture may still be dropped by it: "arrived" is not "accepted". Without `-c` or `-C`/`-W`, a long capture on a busy host can fill the disk.

**Next step:** SYN out, nothing back → capture on the server: does it arrive? Then its firewall and `ss -ltnp`. SYN answered by RST → nothing listens: `ss -ltnp`. Reply leaves by the wrong NIC → `ip route get CLIENT from SERVER_IP`, `ip rule`. Same segment repeated → loss: `mtr`. Deeper analysis → `-w`, then Wireshark or `tshark`.

### tshark — what went wrong inside this capture?
Match: tshark
Instead of: tcpdump -r
Safety: read-only on a saved file · a live capture (`-i`) needs root or the wireshark group; pcap files can hold secrets

**In one line:** `tshark` is Wireshark on the command line: it decodes every protocol in a pcap and filters on decoded fields (retransmissions, resets, DNS error codes, TLS server names) that a tcpdump filter cannot express.

**Read the command:** `tshark -r incident.pcap -Y 'tcp.flags.reset == 1' -T fields -e frame.time -e ip.src -e ip.dst`

| Part | Meaning |
|---|---|
| `-r incident.pcap` | read a saved capture (made with `tcpdump -w`) |
| `-Y 'tcp.flags.reset == 1'` | display filter, in Wireshark syntax: only packets with the RST flag |
| `-T fields` | print chosen fields instead of the usual one-line packet summary |
| `-e frame.time -e ip.src -e ip.dst` | the fields to print: time, source, destination |
| `-q -z conv,tcp` | no packet lines, only statistics: one row per TCP conversation |
| `-Y 'tcp.analysis.retransmission'` | the packets Wireshark's TCP analysis marks as retransmissions |
| `-i any -f 'tcp port 443'` | live capture; `-f` takes a capture filter in tcpdump (BPF) syntax |

**What the output tells you:** with `-T fields`, each matching packet becomes one tab-separated line with the fields in the order you listed them, ready for `sort | uniq -c`: here, when each reset happened and between whom. Other useful display filters: `dns.flags.rcode != 0` (DNS errors) and `tls.handshake.type == 1` (ClientHello; add `-e tls.handshake.extensions_server_name` for the requested name).

**Why it is effective:** tcpdump filters on header bits; tshark understands the protocols. It marks retransmissions, duplicate ACKs and zero windows, reads DNS response codes and TLS server names, and summarises conversations, turning a 50 MB capture into one list such as "these clients got resets from this server at 10:14".

**Compared with `tcpdump -r`:** reading a pcap with tcpdump prints every packet and can filter by addresses, ports and flags, which is enough for a short capture or one handshake. It cannot select by decoded fields or by TCP analysis.

**Trap:** `-Y` (display filter) and `-f` (capture filter) are different languages: `tcp.port == 443` versus `tcp port 443`. A capture taken with a small snap length (`tcpdump -s 128`) has no payload, so application fields such as the TLS server name come out empty. TCP analysis is most reliable when the file holds both directions from the start of the connection.

**Next step:** retransmissions concentrated on one peer → `mtr` to that peer, `ss -ti dst IP`. Resets sent by the server → nothing listening (`ss -ltnp`) or a firewall reject. DNS errors → `dig @SERVER NAME`. A huge capture → `tshark -r big.pcap -Y FILTER -w small.pcap`, then Wireshark.

### iperf3 — how fast can the network itself move data, in each direction?
Match: iperf3
Instead of: scp, curl
Safety: generates load: a full-speed test, and any UDP `-b` rate, competes with production traffic; the server opens port 5201 (TCP and UDP)

**In one line:** `iperf3` sends data memory to memory between two hosts you control and reports throughput and TCP retransmits, or UDP loss and jitter: the network path alone, without disks, TLS or the application.

**Read the command:** `iperf3 -c 10.0.20.15 -t 10 -R`

| Part | Meaning |
|---|---|
| `-c 10.0.20.15` | client, against a server running `iperf3 -s` (`-s -1`: one test, then exit) |
| `-t 10` | run 10 seconds |
| `-R` | reverse: the server sends (`--bidir`: both directions at once) |
| `-P 8` | 8 parallel streams; compare `[SUM]` with one stream |
| `-u -b 500M` | UDP at 500 Mbit/s: loss and jitter (UDP's default is only 1 Mbit/s) |
| `-O 2` | skip the first 2 s (slow start) in the summary |
| `-w 16M`, `-C bbr` | bigger socket buffer / other congestion control, this test only |
| `-J`, `-p 5202` | JSON output / a port other than 5201 |

**What the output tells you:**

```
Reverse mode, remote host 10.0.20.15 is sending
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  40.1 MBytes  33.6 Mbits/sec  2871             sender
[  5]   0.00-10.00  sec  39.8 MBytes  33.4 Mbits/sec                  receiver
```

Read the `receiver` line: what really arrived. `Retr` on the sender line counts TCP retransmissions. If the forward test gave 940 Mbit/s with 0 retransmits and the reverse gives 33 Mbit/s with thousands, the fault is one-directional: a duplex mismatch or a bad cable pair. In UDP mode, `Lost/Total Datagrams` on the receiver line is the loss at that rate.

**Why it is effective:** "iperf3 fast, copy slow" clears the network; "iperf3 slow" proves it is guilty. Testing each direction separately catches the faults that only hit one way.

**Compared with `scp` and `curl`:** they measure what users experience end to end (disk, encryption, the far server and the application included), which is the right final check, but they cannot tell you which layer is slow.

**Trap:** one TCP stream can be limited by RTT and window, not capacity: low with one stream but high with `-P 8` is a per-flow limit. UDP has no congestion control: `-b 900M` really pushes 900 Mbit/s over a shared link. Before iperf3 3.16, all `-P` streams share one thread, so one CPU core can cap multi-gigabit tests. Close the 5201 firewall rule afterwards.

**Next step:** about 94 Mbit/s, or one direction poor with retransmits → `ethtool` and `ip -s link` on both ends. Loss beginning at a precise UDP rate → shaping or policing (`tc -s qdisc`, provider limits). One stream low, parallel high → windows and buffers (`ss -ti`). Both directions near line rate → the disks, the tool or the application.

### nstat — which TCP counters are rising right now?
Match: nstat
Instead of: netstat -s
Safety: read-only · `-n` only updates nstat's own history

**In one line:** `nstat` prints the kernel's network counters (TCP, IP, UDP: the same ones `netstat -s` shows) by name, and by default only how much each changed since its last run, so you can measure retransmits or listen-queue drops over the minute the problem happens.

**Read the command:** `nstat -az TcpRetransSegs TcpOutSegs TcpExtTCPTimeouts`

| Part | Meaning |
|---|---|
| `-a` | absolute values since boot, instead of the change since the last run |
| `-z` | also print counters that are zero (hidden otherwise) |
| `TcpRetransSegs TcpOutSegs TcpExtTCPTimeouts` | only these counters |
| `-n` | print nothing, just remember the current values: the start of a measurement |

**What the output tells you:**

```
$ nstat -n; sleep 60; nstat TcpOutSegs TcpRetransSegs TcpExtTCPTimeouts TcpExtListenOverflows
#kernel
TcpOutSegs                      4123110            0.0
TcpRetransSegs                  98211              0.0
TcpExtTCPTimeouts               412                0.0
TcpExtListenOverflows           1840               0.0
```

Retransmit rate = `TcpRetransSegs` / `TcpOutSegs` = 98211 / 4123110 ≈ 2.4% over that minute, far above the half per cent still acceptable on the internet. `TcpExtTCPTimeouts` are the slow retransmissions after a full timeout (severe loss or a black hole). `TcpExtListenOverflows` (with `ListenDrops`) means this server's accept queue was full and incoming SYNs were dropped: clients see 1 s or 3 s connect delays that look like network loss. Ignore the third column here.

**Why it is effective:** totals since boot mix last month's incident with now; the delta isolates the problem window, and the counter names are stable enough to script and alert on (node_exporter exposes the same ones).

**Compared with `netstat -s`:** it prints the same counters since boot as sentences ("98211 segments retransmitted"): readable, but you take two snapshots and subtract yourself, and net-tools may not be installed.

**Trap:** a plain `nstat` shows the change since the *last* run, which may have been days ago, so always start with `nstat -n`. The counters are host-wide: one busy service can hide another one's problem (use `ss -ti` per connection). Ratios need traffic: 5 retransmits out of 50 segments is noise.

**Next step:** retransmits high → find the loss: `mtr`, `ip -s link`, `ethtool -S`. `ListenOverflows` rising → the application accepts too slowly (workers, backlog, `net.core.somaxconn`); `ss -ltn` shows `Recv-Q` at `Send-Q`. Timeouts or SYN retransmits → a firewall or a black hole: `tcpdump`.

### iftop / nethogs — who is using the bandwidth right now?
Match: iftop, nethogs
Instead of: nload, ip -s link
Safety: read-only · both need root to capture

**In one line:** `iftop` shows live bandwidth per **connection** (which local port talks to which peer, how fast), and `nethogs` per **process** (which program, which user), so a full link turns into a name you can act on.

**Read the command:** `iftop -i eno1 -nNP -t -s 10`

| Part | Meaning |
|---|---|
| `-i eno1` | the interface to watch |
| `-n` | no DNS lookups of addresses |
| `-N` | port numbers, not service names |
| `-P` | show ports at all, so you see `:443`, not only the host |
| `-t` | text mode instead of the full-screen display |
| `-s 10` | with `-t`: collect for 10 s, print once and exit (paste-able into a ticket) |
| `nethogs eno1` | the per-process view of the same interface, live (sent and received KB/s per PID) |

**What the output tells you:**

```
   1 10.0.20.11:443                           =>      812Mb      790Mb      790Mb      987MB
     198.51.100.77:60412                      <=     9.11Mb     8.80Mb     8.80Mb     11.0MB
   2 10.0.20.11:22                            =>     1.21Mb     1.18Mb     1.18Mb     1.47MB
     10.0.30.44:51544                         <=     21.8Kb     20.9Kb     20.9Kb     26.1KB
Total send rate:                                       813Mb      791Mb      791Mb
```

`=>` is sent by this host, `<=` received. The three rate columns are averages over the last 2, 10 and 40 seconds in bits per second, then the total so far. One client downloading from port 443 fills the gigabit uplink. nethogs prints `PID USER PROGRAM DEV SENT RECEIVED`, and would name, say, an `rsync` run by the `backup` user.

**Why it is effective:** a saturated link is slow for everyone, and no tuning fixes contention. Counters say *that* the link is busy; these tools say *who*: one client, one cron job, one backup.

**Compared with `nload` and `ip -s link`:** they show the interface total (how much), enough to prove the link is full, but not which connection or program fills it.

**Trap:** Docker and Kubernetes traffic is NATed, so nethogs often shows it as `unknown TCP`; watch the bridge instead (`iftop -i docker0` or `-i br-…`) to see container IPs. Both show only the present: a 2 a.m. saturation is gone by the time you log in, so keep history with `vnstat` or `sar`. iftop counts in bits (Mb), nethogs in bytes (KB/sec).

**Next step:** one client or job fills the link → schedule it off-peak, rate-limit it (`rsync --bwlimit`), or add QoS. Link not full but still slow → `tc -s qdisc` for shaping, then `conntrack -S`. No history → set up `vnstat`.

### nload / vnstat — how much traffic, right now and over the last days?
Match: nload, vnstat
Instead of: ip -s link
Safety: read-only · vnstat reads the database that its daemon (`vnstatd`) must already have been collecting

**In one line:** `nload` draws the live incoming and outgoing rate of one interface; `vnstat` keeps history in 5-minute, hourly and daily buckets, so you can see when a link was full even after the fact.

**Read the command:** `vnstat -i eno1 -5`

| Part | Meaning |
|---|---|
| `-i eno1` | the interface |
| `-5` | 5-minute buckets, the most detailed history |
| `-h` / `-d` | hourly / daily totals |
| `nload eno1` | live in/out graphs with current, average, min, max and total |

**What the output tells you:**

```
        time        rx      |     tx      |    total    |   avg. rate
     ------------------------+-------------+-------------+---------------
         01:55    210.12 MiB |   14.20 MiB |  224.32 MiB |    6.27 Mbit/s
         02:00     32.41 GiB |  301.10 MiB |   32.71 GiB |  936.55 Mbit/s
         02:05     32.38 GiB |  298.77 MiB |   32.67 GiB |  935.40 Mbit/s
         02:10    198.40 MiB |   13.95 MiB |  212.35 MiB |    5.94 Mbit/s
```

`rx` is received, `tx` sent, `avg. rate` the average over the bucket. From 02:00 to 02:10 the interface ran at about 936 Mbit/s: a gigabit link saturated by something scheduled, which explains "it is slow every night around two".

**Why it is effective:** complaints arrive after the fact. History lets you match "slow at 2 a.m." to a full link and then look for the job that runs then; nload gives an instant, readable picture while you reproduce a problem.

**Compared with `ip -s link`:** it gives raw byte counters since boot; you sample twice and do the arithmetic yourself, and there is no history.

**Trap:** vnstat knows only what the daemon recorded: if the `vnstat` service was not enabled before the incident, there is no history to read. Five-minute averages hide short bursts: a 10-second spike to line rate barely shows. Totals never say *who*.

**Next step:** saturation at a fixed time → find the job (cron, backups, CI) and confirm it live with `iftop` or `nethogs`. Never near line rate → the bottleneck is elsewhere: `iperf3`, `tc -s qdisc`, `ss -ti`.

### tc — is a shaper, policer or delay emulator slowing this interface?
Match: tc
Instead of: —
Safety: read-only for `show` · changes state: `tc qdisc add`, `change` and `del` alter how every packet leaves the interface, immediately (the labs add delay and loss on purpose)

**In one line:** `tc` shows and sets the queueing disciplines (qdiscs) of each interface: the normal fair queue, or a token-bucket shaper, an HTB QoS tree, a policer, or a `netem` emulator someone left behind that caps or delays all traffic.

**Read the command:** `tc -s qdisc show dev eno1`

| Part | Meaning |
|---|---|
| `-s` | statistics: bytes and packets sent, `dropped`, `overlimits`, `backlog` |
| `qdisc show` | the queueing disciplines (omit `dev` for every interface) |
| `dev eno1` | this interface only |
| `class show`, `filter show dev eno1 ingress` | QoS classes with their `rate` and `ceil`; filters, including ingress policers |
| `qdisc add dev $IFACE root netem delay 40ms loss 1%` | **changes state**: add 40 ms of delay and 1% loss to everything leaving the interface |
| `qdisc del dev r-eth1 root` | **changes state**: remove the root qdisc, back to the default |

**What the output tells you:**

```
qdisc tbf 8001: root refcnt 2 rate 100Mbit burst 125000b lat 50ms
 Sent 81234567890 bytes 56123412 pkt (dropped 412331, overlimits 9123456 requeues 0)
 backlog 0b 0p requeues 0
```

`mq` with `fq_codel` (or `fq`) children is the normal default: no limit. `tbf … rate 100Mbit` caps this host at 100 Mbit/s, and `dropped` and `overlimits` counting up prove it is actively limiting. `netem … delay … loss …` adds latency and loss to everything; `htb` means a deliberate QoS tree, so read its classes.

**Why it is effective:** a flat, round throughput number (exactly 100 Mbit/s) or loss that starts at a precise rate is the fingerprint of a limiter, not of a fault. tc shows the host's own limiters, with counters proving that they drop.

**Trap:** qdiscs act on packets **leaving** an interface: netem on one side delays one direction only (the labs put it on both router legs), and incoming traffic is limited only by ingress filters. Deleting a qdisc can undo QoS someone needs: save `tc -s qdisc show` to a file and find who added it first. netem needs the `sch_netem` module (on some Ubuntu kernels it comes with `linux-modules-extra`); never leave it on production.

**Next step:** a forgotten tbf or netem → remove it with the owner's agreement, then repeat `iperf3`. HTB classes dropping → review the QoS policy. Nothing on the host but a flat limit anyway → look upstream: switch port, ISP or cloud instance limits.

### conntrack — which connections is the kernel tracking and translating, and is the table full?
Match: conntrack
Instead of: ss -tn
Safety: read-only for `-L`, `-S` and `-C` (needs root) · changes state: `-D` deletes entries and `-F` flushes them all, breaking NAT for every live connection

**In one line:** `conntrack` reads netfilter's connection-tracking table: every flow the kernel tracks for NAT and stateful firewalling, with its state and both address tuples, plus the counters that show when the table overflows.

**Read the command:** `conntrack -L -p tcp --dport 443`

| Part | Meaning |
|---|---|
| `-L` | list the tracked connections |
| `-p tcp` | only TCP flows |
| `--dport 443` | only flows whose original destination port is 443 |
| `-s 198.51.100.23` | only flows from this original source |
| `-C` | just the number of entries (compare with `net.netfilter.nf_conntrack_max`) |
| `-S` | per-CPU statistics: `drop`, `early_drop`, `insert_failed` |
| `2>/dev/null` | hide the summary line that conntrack prints on stderr |

**What the output tells you:**

```
tcp      6 431999 ESTABLISHED src=198.51.100.23 dst=192.0.2.10 sport=51544 dport=443 src=10.201.0.3 dst=198.51.100.23 sport=443 dport=51544 [ASSURED] mark=0 use=1
```

`tcp 6`: protocol and number; `431999`: seconds until the entry expires (established TCP: 5 days by default); then the state. The first tuple is the original packet (client → host:443), the second the reply the kernel expects. The reply comes from 10.201.0.3, a container, not from 192.0.2.10: that difference **is** the DNAT of a published port. `[ASSURED]`: traffic seen both ways; `[UNREPLIED]`: no reply yet.

**Why it is effective:** it shows NAT as it really happens, per connection: which backend a published port, a container or a Kubernetes Service sent this client to. `-C`, `-S` and the kernel log line `nf_conntrack: table full, dropping packet` prove the silent failure where new connections are dropped under load while old ones keep working.

**Compared with `ss -tn`:** ss lists sockets owned by local processes. Connections forwarded or NATed through the host (to containers, VPN clients, routed networks) have no local socket and appear only in conntrack.

**Trap:** `-F` "fixes" a full table by deleting the NAT state of every live connection: published ports, Services and VPN sessions break for everyone at once. Raise `nf_conntrack_max` instead (on Kubernetes nodes through kube-proxy's settings, which overwrite the sysctl) and fix the source of churn. A rising `insert_failed` is a race (parallel DNS A and AAAA queries) behind the classic 5-second DNS delays, not a full table.

**Next step:** count near the maximum with drops → raise the limit, find the top destinations, add keep-alive or pooling. `insert_failed` with 5 s DNS delays → `single-request-reopen` or NodeLocal DNSCache. A port forwarded to the wrong backend → the NAT rules (`iptables -t nat -S`, `nft list ruleset`, `ipvsadm -Ln`).

### ipvsadm — where does the kernel load balancer send this virtual service?
Match: ipvsadm
Instead of: ss -ltnp
Safety: read-only with `-L` (needs root) · changes state: `-A`, `-a`, `-D` and `-C` edit or clear the table; on Kubernetes, kube-proxy owns it

**In one line:** `ipvsadm -Ln` lists IPVS, the kernel's layer-4 load balancer used by kube-proxy in IPVS mode and by keepalived/LVS: each virtual address and port, its scheduler, and the real servers behind it with their connection counts.

**Read the command:** `ipvsadm -Ln`

| Part | Meaning |
|---|---|
| `-L` | list the virtual server table |
| `-n` | numeric addresses and ports, no DNS lookups |

**What the output tells you:**

```
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  192.0.2.21:30080 rr
  -> 10.244.1.12:8080             Masq    1      0          0
  -> 10.244.2.7:8080              Masq    1      0          0
```

A `TCP` or `UDP` line is a virtual service (here a NodePort on the node's address) with its scheduler (`rr`, round robin). Each `->` line is a real server (here a pod) with its forwarding method (`Masq` = NAT), weight, and active and inactive connections. A service with no `->` lines has no ready backends.

**Why it is effective:** in IPVS mode NodePorts and ClusterIPs have no listening socket, so `ss` shows nothing on 30080 although the port answers. This table shows where that port really goes, from the node alone, without kubectl.

**Compared with `ss -ltnp`:** ss shows ports held by local processes; IPVS virtual services are kernel forwarding rules and never appear there.

**Trap:** on Kubernetes, kube-proxy rewrites this table continuously, so edits made with ipvsadm are overwritten; its state-changing options are for LVS and keepalived hosts. Empty output means IPVS is not in use (kube-proxy in iptables or nftables mode, or Cilium's replacement), not that the service is missing. In IPVS mode the ClusterIPs also appear as addresses on the `kube-ipvs0` dummy interface.

**Next step:** no backends → `kubectl get endpointslices`, readiness probes. Backends listed but failing → test a pod IP with `nc -zv`. Not IPVS → `iptables-save -t nat` or `nft list ruleset`, searching for the port.

### netplan — validate and apply Ubuntu's network configuration without locking yourself out
Match: netplan, ifreload
Instead of: netplan apply over SSH
Safety: `get` and `generate` are read-only (sudo to read root-only files) · changes state: `try` and `apply` reconfigure the live network; `try` rolls back unless you confirm

**In one line:** netplan turns the YAML files in `/etc/netplan/` into configuration for systemd-networkd (servers) or NetworkManager (desktops). `generate` checks them, `try` applies them with an automatic rollback, `apply` makes them final.

**Read the command:** `netplan try --timeout 120`

| Part | Meaning |
|---|---|
| `try` | apply the new configuration, then restore the old one unless you press Enter in time |
| `--timeout 120` | seconds to wait for your confirmation (120 is the default) |
| `get` | print the merged configuration of every file in `/etc/netplan/` |
| `generate` | render the backend files only: shows YAML errors, applies nothing |
| `apply` | **changes state**: apply for good, with no way back |

**What the output tells you:**

```
$ sudo netplan generate
/etc/netplan/01-static.yaml:9:9: Error in network definition: expected mapping (check indentation)
          via: 10.0.1.1
        ^
```

`generate` names the file, line and column of a YAML mistake (tabs or a key at the wrong indent) and changes nothing. Two common warnings are not errors: `gateway4 has been deprecated` (write a route `to: default` instead) and `Permissions for /etc/netplan/… are too open` (`chmod 600`). `try` counts down the seconds and waits for Enter.

**Why it is effective:** a typo in an address, a prefix or an interface name, applied over SSH, removes the address you are connected through. `try` turns that into a two-minute outage that heals itself, and `generate` catches YAML errors before anything is touched.

**Compared with `netplan apply`:** apply is the final step; it is fine from a console (IPMI, Proxmox noVNC, a cloud serial console), or after `try` has proved the change.

**Trap:** `try` protects you only if you test before confirming: open a second SSH session to the new address first. Files are merged in name order, and on cloud images cloud-init rewrites `50-cloud-init.yaml` at boot, so put changes in a later file or disable cloud-init's network config. Changes made with `ip` commands are not in netplan and vanish at reboot.

**Next step:** generate errors → fix the indentation (spaces only) and run it again. Applied but no connectivity → `ip -br addr`, `ip route`, `networkctl status IFACE`. Locked out → the out-of-band console, restore the backup, `netplan apply`. Related, Proxmox VE and Debian with ifupdown2: `ifreload -a` applies `/etc/network/interfaces` without a reboot, changing only what differs (**changes state**), and `ifquery -a -c` compares the running state with the file. There is no `try`-style rollback: keep a console open when you change the bridge that carries the management address.

### networkctl — what does systemd-networkd think each interface is doing?
Match: networkctl
Instead of: ip addr
Safety: read-only for `list` and `status` · changes state: `reconfigure` re-applies networkd's configuration to a live link and can briefly interrupt it

**In one line:** on Ubuntu servers netplan hands its configuration to systemd-networkd; `networkctl` shows networkd's view: which links it manages, whether each is configured and routable, and the addresses, gateway and DNS it applied.

**Read the command:** `networkctl status ens18`

| Part | Meaning |
|---|---|
| `status ens18` | one link in detail: state, addresses, gateway, DNS, recent log lines |
| `list` (or no argument) | one line per link: type, operational state, setup state |
| `reconfigure ens18` | **changes state**: drop and re-apply networkd's configuration for this link |

**What the output tells you:**

```
$ networkctl list
IDX LINK    TYPE     OPERATIONAL SETUP
  1 lo      loopback carrier     unmanaged
  2 ens18   ether    routable    configured
  3 ens19   ether    no-carrier  configuring
  4 docker0 bridge   no-carrier  unmanaged
```

OPERATIONAL: `routable` (an address and a route out), `degraded` (only link-local addresses), `carrier` or `no-carrier` (physical link or not), `off`. SETUP: `configured` (networkd is done), `configuring` (still waiting, for a carrier or a DHCP lease), `failed`, and `unmanaged` (not networkd's business: Docker bridges, or interfaces NetworkManager owns). `status` adds `Address`, `Gateway`, `DNS` and the link's latest journal lines.

**Why it is effective:** `ip addr` shows what is configured now, not who configured it or whether something is still pending. networkctl answers "is networkd really in charge of this interface, and has it finished?", the key to boot delays and to changes that "don't apply" because another manager owns the link.

**Compared with `ip addr`:** it shows the live addresses and state, enough to see the result, but not the manager, the DHCP progress or the DNS servers networkd learned.

**Trap:** a link stuck in `configuring` (no cable, a bridge without ports) makes `systemd-networkd-wait-online` hold the boot for two minutes; mark it `optional: true` in netplan. `unmanaged` is normal for Docker's bridges, and on desktops where NetworkManager owns everything (then use `nmcli`). `reconfigure` touches a live link.

**Next step:** `configuring` → cable or DHCP server, or `optional: true`. Wrong DNS → `resolvectl status IFACE`. Wrong address or gateway → fix the netplan YAML and `netplan try`.

### nmcli — what does NetworkManager manage, and what did it apply?
Match: nmcli
Instead of: ip addr
Safety: read-only for `show`, `status` and `wifi list` · changes state: `connection modify` edits a saved profile, which applies at the next `nmcli connection up`

**In one line:** on desktops, RHEL/Rocky and some cloud images, NetworkManager owns the network; `nmcli` shows its devices and connection profiles, the addresses, routes and DNS it applied, and the Wi-Fi networks in range.

**Read the command:** `nmcli -t -f DEVICE,TYPE,STATE device`

| Part | Meaning |
|---|---|
| `-t` | terse: colon-separated fields without padding, for scripts |
| `-f DEVICE,TYPE,STATE` | only these columns |
| `device` | the device list (`device status` is the same view) |
| `device show eth0` | one device as applied: `IP4.ADDRESS`, `IP4.GATEWAY`, `IP4.DNS` |
| `connection show` | the saved profiles, and the device each one is active on |
| `-f SSID,CHAN,FREQ,SIGNAL,RATE device wifi list` | Wi-Fi networks in range with channel and signal |
| `connection modify eno1 ethtool.ring-rx 4096 ethtool.ring-tx 4096` | **changes state**: store NIC ring sizes in the profile |

**What the output tells you:**

```
eno1:ethernet:connected
wlp2s0:wifi:disconnected
ens19:ethernet:unavailable
```

`connected`: NetworkManager manages the device and a profile is active. `disconnected`: managed, nothing active. `unavailable`: cannot be activated now (an Ethernet port without carrier). `unmanaged`: NetworkManager leaves the device alone, as it does on most Ubuntu servers where netplan and networkd own the interfaces.

**Why it is effective:** NetworkManager re-applies its profiles whenever a link changes, so an address set with `ip` disappears and a fix written in the wrong file never takes effect. nmcli shows who owns each device and exactly what was applied, DNS included.

**Compared with `ip addr`:** it shows the live result, enough to see what is configured right now, but not the owner or the profile behind it.

**Trap:** `connection modify` changes only the saved profile: nothing happens until `nmcli connection up eno1`, which briefly drops that link. On Ubuntu Server, devices are usually `unmanaged` or NetworkManager is not installed at all, so use `networkctl`. Wi-Fi `SIGNAL` is a 0–100 quality figure, not dBm (`iw` shows dBm).

**Next step:** device `unmanaged` → `networkctl status IFACE`. Wrong DNS → `resolvectl status`. Weak Wi-Fi → `iw dev IFACE link`.

### ifconfig / route / arp — the legacy tools, still native on macOS, BSD and Windows
Match: ifconfig, route, arp
Instead of: —
Safety: read-only as shown · changes state when given arguments (`ifconfig eth0 down`, `route add`, `arp -d`)

**In one line:** on Linux these net-tools commands are replaced by `ip addr`, `ip route` and `ip neigh`, and are not installed by default on current Ubuntu; on macOS and BSD firewalls (OPNsense, pfSense) `ifconfig` and `route` are the native tools, and Windows has its own `route print` and `arp -a`.

**Read the command:** `route -n get default`

| Part | Meaning |
|---|---|
| `route -n get default` | macOS and BSD: the gateway and interface of the default route, numeric (like `ip route get`) |
| `route -n get 203.0.113.10` | the same question for one destination |
| `route -n` | Linux: the routing table, numeric (like `ip route`) |
| `route print` | Windows: the interface list and the IPv4 and IPv6 routing tables |
| `ifconfig -a` | Linux: every interface, including down ones (like `ip addr`) |
| `ifconfig en0`, `ifconfig vtnet0` | macOS Wi-Fi or first NIC; a virtio NIC on FreeBSD-based OPNsense |
| `arp -a` | the ARP cache on Linux, macOS and Windows (like `ip neigh`) |

**What the output tells you:**

```
   route to: default
destination: default
       mask: default
    gateway: 192.0.2.1
  interface: en0
...
```

`gateway` and `interface` are the answer. With a VPN connected, an `interface` such as `utun3` shows that the traffic goes into the tunnel.

**Why it is effective:** these are the commands present on the machine in front of you: a Mac laptop, an OPNsense firewall, a Windows jump host. `route -n get` answers "which way does this packet go?" just like `ip route get` on Linux.

**Trap:** on Linux, `ifconfig` shows only the first IPv4 address of each interface (VIPs and addresses added with `ip addr add` are invisible), and `route -n` shows only the main table, without policy rules: use `ip` there. The same flag differs per OS: on macOS `route -n` just means "numeric" and the whole table comes from `netstat -rn`. On Windows `route add` without `-p` lasts until reboot. With arguments, all three change state immediately.

**Next step:** Linux → `ip -br addr`, `ip route get IP`, `ip neigh`. macOS → `netstat -rn` for the full table, `scutil --dns` for resolvers. Windows → `Get-NetRoute`, `Get-NetNeighbor`, `Test-NetConnection`.

### wg / wg-quick — is the WireGuard tunnel up, and does each peer have a recent handshake?
Match: wg, wg-quick, swanctl
Instead of: ping
Safety: `wg show` is read-only (needs root) · changes state: `wg set` and `wg-quick up/down`; never paste private keys into tickets or chats

**In one line:** `wg show` prints each WireGuard interface and peer: endpoint, allowed IPs, the time of the latest handshake and the bytes transferred. `wg-quick` brings an interface up or down from `/etc/wireguard/wg0.conf`, with its addresses, routes, DNS and PostUp rules.

**Read the command:** `wg show wg0`

| Part | Meaning |
|---|---|
| `show wg0` | one interface (`wg show`: all) |
| `show wg0 latest-handshakes` | per peer: Unix time of the last handshake (0 = never) |
| `show wg0 transfer` | per peer: bytes received and sent |
| `set wg0 peer KEY allowed-ips 10.8.0.2/32` | **changes state**: add or update a peer, runtime only |
| `set wg0 peer KEY remove` | **changes state**: delete a peer |
| `genkey`, `pubkey` | a new private key / its public key (private key on stdin) |
| `wg-quick up wg0`, `wg-quick down wg0` | **changes state**: build or remove the interface from wg0.conf (addresses, routes, PostUp/PostDown) |

**What the output tells you:**

```
interface: wg0
  public key: (server public key)
  private key: (hidden)
  listening port: 51820

peer: (client public key)
  endpoint: 198.51.100.7:51413
  allowed ips: 10.8.0.2/32
  latest handshake: 1 minute, 12 seconds ago
  transfer: 17.82 KiB received, 1.01 KiB sent
```

A `latest handshake` at most a few minutes old while traffic flows: the keys match and UDP passes. **No** `latest handshake` line: it never completed (wrong key or UDP blocked). `received` stuck at 0 while `sent` grows: packets leave and nothing comes back. `allowed ips` is both the access list and the routing table for that peer.

**Why it is effective:** WireGuard never answers a packet it cannot authenticate, so a closed port and a wrong key look identical from the client: ping just times out. The handshake time and the transfer counters separate "no tunnel" from "tunnel up, routing or forwarding broken".

**Compared with `ping`:** a ping through the tunnel tells you only that traffic does not arrive; it is the right final test once the handshake is fresh.

**Trap:** handshakes happen only with traffic: an idle tunnel without `PersistentKeepalive` shows an old handshake and is still fine. `wg set` changes are lost at `wg-quick down` or reboot unless written to wg0.conf. A fresh handshake does not mean routing works: IP forwarding, the FORWARD policy (Docker sets it to DROP) and NAT on the server decide that. Compare public keys only, never private ones.

**Next step:** no handshake → `tcpdump -ni any udp port 51820` on the server: packets arriving means a key mismatch, none means firewall, port forward or endpoint. Handshake but no traffic → `sysctl net.ipv4.ip_forward`, `iptables -S FORWARD`, the masquerade rule. Big transfers stall → MTU: `ping -M do -s 1392 10.8.0.1`. Related, IPsec with strongSwan: `sudo swanctl --list-sas` lists each IKE SA (`ESTABLISHED`: the peers authenticated) and its child SAs (`INSTALLED`: the kernel encrypts that traffic); an IKE SA without its child SA points at mismatched subnets or proposals. `swanctl --terminate --ike NAME` and `--initiate --child NAME` take a tunnel down and up (**changes state**).

### tailscale / netbird — is the mesh VPN path direct or relayed, and are routes accepted?
Match: tailscale, netbird
Instead of: ping, wg show
Safety: `status`, `ping`, `netcheck` and `debug prefs` are read-only · changes state: `tailscale set …` changes routing, DNS or firewall handling at once

**In one line:** both build WireGuard tunnels between devices and fall back to a relay when NAT blocks a direct path; their CLIs show per peer whether traffic is direct or relayed, why, and which routes are active.

**Read the command:** `tailscale ping web1`

| Part | Meaning |
|---|---|
| `tailscale ping web1` | ping a peer through the tailnet; the reply names the path: a direct address or `DERP(region)` |
| `tailscale status` | every peer: tailnet IP, name, OS, and `active; direct …` or `active; relay "fra"` |
| `tailscale netcheck` | this node's NAT: UDP allowed, public address, `MappingVariesByDestIP`, nearest relay |
| `tailscale set --accept-routes` | **changes state**: use subnet routes that others advertise (off by default on Linux) |
| `tailscale set --advertise-routes=10.0.1.0/24 --advertise-exit-node` | **changes state**: offer a LAN and an exit node (needs IP forwarding and approval) |
| `netbird status -d` | per peer: `Connection type: P2P` or `Relayed`, ICE candidates, last handshake |
| `netbird debug trace in 100.92.14.7 self -p tcp --dport 443` | would NetBird's own firewall let this packet in? |

**What the output tells you:**

```
$ tailscale ping web1
pong from web1 (100.101.102.103) via DERP(fra) in 48ms
$ tailscale netcheck
Report:
	* UDP: true
	* IPv4: yes, 203.0.113.10:62044
	* IPv6: no, but OS has support
	* MappingVariesByDestIP: true
	* PortMapping:
	* Nearest DERP: Frankfurt
```

`via DERP(fra)`: relayed through Frankfurt, working but slower (a direct path shows `via ADDRESS:PORT`). `MappingVariesByDestIP: true`: this side's NAT picks a new public port per destination, so peers cannot aim at it and the connection stays relayed. NetBird shows the same as `Connection type: Relayed` with `ICE candidate (Local/Remote): -/-`.

**Why it is effective:** a relayed connection still answers, so ping looks fine while transfers crawl. These commands show the path type, the NAT behaviour behind it, and whether a route was advertised, approved and accepted.

**Compared with `ping` and `wg show`:** ping proves only that the peer answers. `wg show` is the tool for plain WireGuard; mesh clients manage keys and peers themselves, and only their own CLI shows relays, NAT type and route approval.

**Trap:** `active; relay` is a working connection, not an outage: fix the NAT (a static outbound UDP port on the edge firewall), do not disable relays. On Linux `--accept-routes` is off by default, and routes also need approval. Both tools use addresses from 100.64.0.0/10, which collides with CGNAT ISPs. `tailscale set` applies at once, and `--netfilter-mode=off` makes the firewall rules your job.

**Next step:** relayed → `tailscale netcheck` on both peers, a static UDP port (41641) on the edge firewall. Route not working → `tailscale debug prefs`, `ip route show table 52`, `sysctl net.ipv4.ip_forward` on the router, Docker's FORWARD policy. NetBird resource unreachable → `netbird status -d`, forwarding on the routing peer, the access policy.

### iw — how good is this Wi-Fi link really?
Match: iw
Instead of: iwconfig
Safety: read-only for `link` and `station dump`

**In one line:** `iw` asks the wireless driver about the current association: which access point, the frequency, the signal strength in dBm and the bitrates in use, plus retry and failure counters that reveal a poor radio link.

**Read the command:** `iw dev wlp2s0 link`

| Part | Meaning |
|---|---|
| `dev wlp2s0` | the wireless interface |
| `link` | the current connection: access point, SSID, frequency, signal, bitrates |
| `station dump` | per-station counters: `tx retries`, `tx failed`, signal, bitrates |

**What the output tells you:**

```
Connected to 02:00:00:aa:bb:01 (on wlp2s0)
	SSID: office-5g
	freq: 5180
	signal: -71 dBm
	rx bitrate: 58.5 MBit/s VHT-MCS 6 VHT-NSS 1
	tx bitrate: 26.0 MBit/s VHT-MCS 3 VHT-NSS 1
```

`freq` 5180 MHz is 5 GHz channel 36 (2412–2472 would be 2.4 GHz). `signal`: −30 to −55 dBm excellent, −56 to −67 good (−67 is the usual target for calls), −68 to −75 weak, below −75 poor. Bitrates are the current modulation rates, not throughput: real TCP is often 30–60% of them. Here −71 dBm and 26 Mbit/s transmit: too far from the access point.

**Why it is effective:** "Wi-Fi is slow" becomes a number: weak signal, a crowded channel or many retries. And it tells you when to stop debugging the network core: the first test of any Wi-Fi complaint is the same test on a cable.

**Compared with `iwconfig`:** the old wireless-tools command shows similar link quality, but it is deprecated and often missing; iw uses the current nl80211 interface.

**Trap:** a good signal with many `tx retries` or `tx failed` means interference or a crowded channel, so signal alone is not enough. Bitrates change from second to second. The access point's own view of the client can differ from the client's.

**Next step:** weak signal → move closer, use 5 GHz, or use a cable. Crowded channel → `nmcli -f SSID,CHAN,FREQ,SIGNAL,RATE device wifi list`. Radio fine but slow → `iperf3` to a wired host, and `ping` while loaded (bufferbloat).
