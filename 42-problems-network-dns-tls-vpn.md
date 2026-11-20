# 42 — Real-World Problems: Networking, DNS, TLS, Firewalls & VPN

This module is a problem library for the network layer under everything else you run: netplan and routes, systemd-resolved and split DNS, BIND, Unbound, Pi-hole and AdGuard Home, Let's Encrypt and private CAs, UFW, firewalld and nftables next to Docker, NAT and port forwarding on OPNsense or pfSense, MTU black holes, WireGuard, OpenVPN, Tailscale, Headscale, NetBird and IPv6. It collects 41 problems that engineers really hit. They come from the Let's Encrypt community forum, GitHub issues of the VPN projects, the OPNsense, Docker and Ubuntu forums, official docs and engineering blogs; Stack Overflow, Server Fault and Reddit are reachable through search links. [Learn networking](28-learn-networking.md) teaches the fundamentals, and this module assumes them. Every command is documented for your own lab VMs or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Network problems lie about where they are. A DNS problem looks like "the site is down", an MTU problem looks like "the TLS handshake hangs", a firewall in front of Let's Encrypt looks like a certbot bug, and a missing return route looks like a broken VPN. That's why every entry here starts by proving which layer is at fault (name, route, filter, listener, certificate) before changing anything, and ends with a test from the other side of the network, not just from the server itself.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | entries 1.1, 2.1, 3.2 and 5.1 | you change a static IP with netplan without losing SSH, and explain "Temporary failure in name resolution" from `resolvectl status` |
| Junior | L1 Operator | sections 1 to 5 (every L1 entry) | you fix a failed certbot renewal, a Docker port that slipped past UFW and a port forward that "does nothing", without help |
| Mid-level | L2 Troubleshooter | sections 2, 6, 7 and 8 | you explain any "x509: certificate signed by unknown authority", stale DNS answer or silent WireGuard tunnel from evidence alone |
| Senior | L3 Platform | sections 9 and 10, entries 1.4, 3.5 and 7.3 | split DNS, private CA trust, mesh VPN routing and MTU across tunnels work in your lab and are written down |
| Senior/Lead | L4 SRE | entries 3.5, 6.2, 10.1 and the Self-check | you own certificate expiry monitoring, a firewall policy others follow, and a postmortem for a network outage |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**On-prem or cloud:** most network problems are the same on a rack server and an EC2 instance, so most entries apply to both. Where the answer really differs (console access when you lock yourself out, cloud-init owning netplan, security groups instead of an edge firewall, no port forwarding in a VPC, MTU inside AWS), the entry has a short block for each environment; the selector at the top of the page shows one or both.

**How to practise:** build four lab VMs on Proxmox or VirtualBox (Ubuntu 24.04, 1–2 vCPU and 2 GB RAM each, OPNsense needs 2 GB): fw1 runs OPNsense with a WAN and a LAN side; web1 runs Docker with Traefik (or Dokploy) plus Apache on 81/444 like your real server; dns1 runs Unbound or Pi-hole, later BIND; vpn1 runs WireGuard, then Tailscale or NetBird. Put a laptop or a small VM "outside" on the WAN side so you can test from the internet's point of view. Snapshot everything, break one thing at a time on purpose, fix it using only the entry, and write a five-line note: symptom, evidence, cause, fix, prevention. Never practise firewall or routing changes on a production host without console access.

**Safety rules for network changes:**

- Have a way back before you change anything remote: a console (IPMI, iDRAC, Proxmox noVNC, EC2 Serial Console or SSM), `netplan try`, or a scheduled rollback.
- Change one layer at a time and test from outside after each change. "It works from the server" proves almost nothing.
- Never fix a TLS problem by turning verification off (`curl -k`, `insecureSkipVerify`, `GIT_SSL_NO_VERIFY`, `insecure-registries`), and never fix a firewall problem by disabling the firewall "for now".
- Keep a copy of the ruleset before editing it (`sudo nft list ruleset | sudo tee /root/nft-before.txt >/dev/null`, `sudo iptables-save | sudo tee /root/ipt-before.txt >/dev/null`).

**Placeholders and examples:** UPPERCASE words are placeholders (IFACE, DOMAIN, PEER, PORT, CONTAINER, ZONE). The examples use a 10.0.1.0/24 lab LAN behind fw1 (10.0.1.1, WAN address 203.0.113.10): web1 at 10.0.1.10 serving www.example.com, dns1 at 10.0.1.53, vpn1 at 10.0.1.20 with the WireGuard network 10.8.0.0/24, a backup network 10.0.2.0/24, a remote office at 198.51.100.0/24, the IPv6 prefix 2001:db8:10::/64, an internal zone corp.example.com, and the admin user ops.

**First minute: symptom to entry.**

| You see | First check | Go to |
|---|---|---|
| SSH froze right after `netplan apply` | the console, then `sudo netplan get` | 1.1 |
| no IP after a reset, a disk or NIC swap, or a reconnected adapter | the console: `ip -br link` against the names in the config | 1.6 |
| Temporary failure in name resolution | `ls -l /etc/resolv.conf` and `resolvectl status` | 2.1 |
| `dig` answers but the app can't resolve | `getent ahosts NAME` | 2.2 |
| a database port reachable from the internet although UFW denies it | `docker ps` port column and `sudo iptables -S DOCKER-USER` | 3.1 |
| open locally, closed from outside | `tcpdump` on the server while you test from outside | 3.4 |
| works from outside, not from the office LAN | DNS answer inside vs outside | 4.1 |
| Timeout during connect (likely firewall problem) from certbot | `curl` the challenge path from an outside host | 5.1 |
| unable to get local issuer certificate | `openssl s_client -showcerts` chain length | 6.1, 6.2 |
| x509: certificate signed by unknown authority on a registry pull | which trust store the failing tool reads | 6.3 |
| DNS change "not propagated" after hours | `dig` against each authoritative server | 7.1 |
| SERVFAIL from Unbound, Pi-hole or OPNsense | `dig +cd` versus plain `dig` | 7.3 |
| WireGuard "Handshake did not complete after 5 seconds" | `tcpdump udp port 51820` on the server | 8.1 |
| tunnel up, ping across it fails | `wg show` counters and the FORWARD policy | 8.2 |
| Tailscale works but slowly, "relay" in status | `tailscale netcheck` | 9.1 |
| small requests work, large downloads or `git clone` hang | `tracepath` and `ping -M do` | 10.1 |
| every `apt update` stalls for minutes | `curl -6` versus `curl -4` | 10.3 |

> 📚 **Study path:** KodeKloud *DevOps Pre-Requisite Course* — Networking Basics, DNS, then Security: SSL & TLS Basics ([course](https://kodekloud.com/courses/devops-pre-requisite-course)) → *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure IPv4/IPv6 Networking and Hostname Resolution, Configure Packet Filtering (Firewall), Port Redirection and NAT ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) → *Demystifying DNS* — DNS as a System, Troubleshooting DNS ([course](https://kodekloud.com/courses/demystifying-dns)) → *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt ([course](https://kodekloud.com/courses/kubernetes-networking)) → handbook [Learn networking](28-learn-networking.md) (sections 4, 7, 8, 10 and 12 first) → docs: [netplan](https://netplan.readthedocs.io/), [systemd-resolved](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html), [Let's Encrypt](https://letsencrypt.org/docs/), [WireGuard](https://www.wireguard.com/quickstart/) → lab: the four VMs above and the Self-check. KodeKloud has no WireGuard, OpenVPN, Tailscale, OPNsense or netplan course in the verified map, so the handbook and the official docs lead for those.

---

The problem library starts here. Sections 1 to 10 run from first-week problems (an IP change, a resolver, a firewall rule) to platform work (private CAs, DNS servers, mesh VPNs, MTU across tunnels); each entry stands on its own.

## 1. Interfaces, routes and netplan

On Ubuntu servers, netplan writes the config and systemd-networkd applies it. Most problems here are one of three things: a change applied remotely without a way back, two pieces of software both thinking they own the default route, or a host with more than one network that answers from the wrong one. After a reset or a hardware change, add a fourth: settings saved for an interface name that no longer exists (1.6).

### 1.1 netplan apply locks you out

> **Seen as:** the SSH session freezes right after `sudo netplan apply`; or `Error in network definition ... (check indentation)`; plus warnings such as `gateway4 has been deprecated, use default routes instead` and `Permissions for /etc/netplan/50-cloud-init.yaml are too open` · **Where:** Ubuntu 22.04 and 24.04 servers when you change a static IP, gateway or DNS over SSH · **Level:** [L1 · Junior] · **How common:** a rite of passage; endless Server Fault and r/linuxadmin threads, plus cloud-init and Foreman issues about the gateway4 deprecation

**Why it happens:** `netplan apply` rewrites the systemd-networkd files and reconfigures the interfaces at once. One wrong value (a typo in the address, a /32 instead of /24, the wrong interface name such as eth0 on a host where the NIC is ens18) and the address you are connected through is gone. YAML mistakes (tabs, a key at the wrong indent) make netplan refuse the file instead. The two warnings are not errors: `gateway4` still works but has been deprecated in favour of a route `to: default`, and newer netplan expects its files to be readable only by root, because they can hold Wi-Fi passwords.

**Diagnose:**

```bash
ip -br link                      # the real interface names
ip -br addr                      # what is configured right now
sudo netplan generate            # parse only: shows YAML errors, touches nothing
sudo netplan get                 # the merged view of every file in /etc/netplan
ls -l /etc/netplan/
```

```text
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
ens18            UP             bc:24:11:5e:7a:01 <BROADCAST,MULTICAST,UP,LOWER_UP>
lo               UNKNOWN        127.0.0.1/8 ::1/128
ens18            UP             10.0.1.10/24 fe80::be24:11ff:fe5e:7a01/64
/etc/netplan/01-static.yaml:9:9: Error in network definition: expected mapping (check indentation)
          via: 10.0.1.1
        ^
-rw-r--r-- 1 root root 412 Oct  4 09:12 01-static.yaml
```

**What the output tells you:** the NIC is ens18, the file has an indentation error at line 9 (the route list is not nested under `routes:`), and the file is world-readable, which is where the permissions warning comes from. Nothing was applied yet because generate failed.

**Fix:**

```yaml
# /etc/netplan/01-static.yaml  (chmod 600, spaces only, no tabs)
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: false
      addresses: [10.0.1.10/24]
      routes:
        - to: default            # replaces the deprecated gateway4
          via: 10.0.1.1
      nameservers:
        addresses: [10.0.1.53]
        search: [corp.example.com]
```

```bash
sudo chmod 600 /etc/netplan/*.yaml
sudo netplan generate                 # must print nothing
sudo netplan try --timeout 120        # applies, then rolls back unless you press ENTER
# In a second SSH session to the NEW address, confirm it works, then press ENTER in the first one
```

<div class="env" data-env="onprem" markdown="1">

**Already locked out on-prem:** use the out-of-band console (IPMI or iDRAC, the Proxmox noVNC console, the VMware remote console), fix the YAML there and run `sudo netplan apply` from the console. If the server is in a remote room with no console, the only rollback is a scheduled one you set up before the change, for example `echo 'cp /root/netplan-backup/*.yaml /etc/netplan/ && netplan apply' | sudo at now + 10 minutes`.

</div>

<div class="env" data-env="cloud" markdown="1">

**Already locked out on AWS:** connect with EC2 Serial Console or SSM Session Manager if they were enabled, fix the file and apply. Without either, stop the instance, attach its root volume to a rescue instance, edit /etc/netplan there, and move the volume back. On cloud images, also read entry 1.2: cloud-init may own the file you edited.

</div>

**Why this fix works:** `netplan try` keeps the old configuration ready and restores it automatically if you don't confirm, so a mistake costs two minutes instead of a trip to the data centre. Fixing the YAML and the permissions removes the error and the warnings without changing behaviour. Do not "fix" a lockout by editing systemd-networkd files directly: netplan regenerates them on the next apply or reboot.

**Prevent it:** always use `netplan try` (or a console) for remote changes, keep a copy of /etc/netplan before editing, validate with `netplan generate` in your config-management pipeline, and template netplan files with Ansible so a typo can't reach only one host.

**Next step:** [Network reference: netplan](02-network.md) · [Learn networking: IP addressing](28-learn-networking.md) · [SSH and remote access](09-ssh-remote-access.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure IPv4/IPv6 Networking and Hostname Resolution · [netplan docs](https://netplan.readthedocs.io/)

**Community threads:** [cloud-init#4031: gateway4 and gateway6 deprecated in netplan](https://github.com/canonical/cloud-init/issues/4031) · Search: [Server Fault](https://serverfault.com/search?q=netplan+apply+lost+ssh+connection) · [Stack Overflow](https://stackoverflow.com/search?q=netplan+%22check+indentation%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=netplan+try+locked+out&restrict_sr=1)

### 1.2 Two default routes, or the wrong gateway

> **Seen as:** `ip route` shows two `default via` lines; the host answers from its own subnet but not from other networks; traffic works after one reboot and fails after the next; your edits to the netplan file vanish after a reboot · **Where:** hosts with two NICs (a LAN and a backup or storage network), a DHCP interface next to a static one, cloud VMs · **Level:** [L1 · Junior] · **How common:** very common on multi-NIC servers and cloud images; a classic Server Fault question

**Why it happens:** every interface configured by DHCP installs its own default route unless told not to, so a second NIC on the backup network adds a second default with its own metric. Whichever route wins sends replies for "everything else" out of that interface, where there is no path back to the client. The same symptom comes from a wrong prefix length (a /16 that swallows the remote office's addresses, so the host thinks they are on the local wire) or a gateway in the wrong subnet. On cloud images, cloud-init writes /etc/netplan/50-cloud-init.yaml from the instance metadata and rewrites it at boot.

**Diagnose:**

```bash
ip route
ip route get 198.51.100.20          # which route, interface and source IP the kernel picks
networkctl status ens19 | grep -iE 'gateway|dhcp'
ls /etc/netplan/ ; sudo head -3 /etc/netplan/50-cloud-init.yaml
```

```text
default via 10.0.2.1 dev ens19 proto dhcp src 10.0.2.10 metric 100
default via 10.0.1.1 dev ens18 proto dhcp src 10.0.1.10 metric 100
10.0.1.0/24 dev ens18 proto kernel scope link src 10.0.1.10 metric 100
10.0.2.0/24 dev ens19 proto kernel scope link src 10.0.2.10 metric 100
198.51.100.20 via 10.0.2.1 dev ens19 src 10.0.2.10 uid 1000
         Gateway: 10.0.2.1
# This file is generated from information provided by the datasource.  Changes
# to it will not persist across an instance reboot.
```

**What the output tells you:** both NICs got a default route from DHCP with the same metric (netplan's DHCP default is 100), so whichever lease arrived first wins, which is why it works after one reboot and fails after the next. This time the backup NIC won, and `ip route get` shows the remote office is now reached through the backup network's router, which has no route back or drops the flow. The cloud-init header says edits to that file are temporary.

**Fix:**

```yaml
# Keep DHCP on the second NIC but refuse its default route and DNS
network:
  version: 2
  ethernets:
    ens19:
      dhcp4: true
      dhcp4-overrides:
        use-routes: false
        use-dns: false
      routes:
        - to: 10.0.2.0/23              # only what really lives behind that network
          via: 10.0.2.1
```

```bash
sudo netplan try
ip route | grep -c '^default'          # expect 1
```

<div class="env" data-env="cloud" markdown="1">

**On cloud images:** don't edit 50-cloud-init.yaml. Either put your changes in a separate, later file (for example 90-local.yaml, which netplan merges after it), or tell cloud-init to stop managing the network with a file /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg containing `network: {config: disabled}`, and then own the whole netplan config yourself. In AWS a second ENI in another subnet is the usual trigger, and the source-based routing in entry 1.4 is the fix for its replies.

</div>

**Why this fix works:** a host can only have one useful default route per routing table; refusing the DHCP default on the second NIC leaves one clear path for "everything else", and an explicit route covers only the networks that really sit behind the second router. Don't solve it by deleting the route by hand (`ip route del`): it returns at the next DHCP renewal or reboot.

**Prevent it:** decide per host which interface owns the default route and write it down; use `dhcp4-overrides` on every secondary interface; check `ip route | grep -c default` in your post-provisioning tests.

**Next step:** [Learn networking: Routing](28-learn-networking.md) · [Network reference](02-network.md) · KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics (Switching and Routing) · [netplan docs](https://netplan.readthedocs.io/)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=netplan+two+default+routes+dhcp4-overrides) · [Stack Overflow](https://stackoverflow.com/search?q=netplan+second+interface+default+route+use-routes) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=two+default+gateways+netplan&restrict_sr=1)

### 1.3 Boot hangs on "Wait for Network to be Configured"

> **Seen as:** `A start job is running for Wait for Network to be Configured (1min 45s / no limit)` at boot (the unit has no start timeout of its own; wait-online stops itself after 120 seconds), then the system comes up anyway; `systemd-analyze blame` puts systemd-networkd-wait-online.service at the top · **Where:** Ubuntu servers with an unused NIC, a bridge without carrier, or netplan set to NetworkManager · **Level:** [L1 · Junior] · **How common:** very common; several Launchpad bugs across 22.04 and 24.04, a systemd issue about bridges, and many how-to posts

**Why it happens:** services that need the network order themselves after network-online.target, and on networkd systems that target waits for systemd-networkd-wait-online, which by default waits until every managed interface is configured. An interface with no cable, a bridge whose ports never come up, or a static interface on a disconnected switch never reaches that state, so the wait runs into its two-minute timeout on every boot. When netplan uses NetworkManager, the networkd wait service can still be enabled and wait for interfaces it doesn't control.

**Diagnose:**

```bash
systemd-analyze blame | head -5
networkctl list
sudo netplan get | grep -nE 'renderer|optional'
```

```text
2min 0.211s systemd-networkd-wait-online.service
     4.102s docker.service
IDX LINK    TYPE     OPERATIONAL SETUP
  1 lo      loopback carrier     unmanaged
  2 ens18   ether    routable    configured
  3 ens19   ether    no-carrier  configuring
3 links listed.
```

**What the output tells you:** ens19 has no carrier and stays "configuring" forever, so the wait service burns its full timeout.

**Fix:**

```yaml
# Mark interfaces that may legitimately be down as optional
network:
  version: 2
  ethernets:
    ens19:
      dhcp4: true
      optional: true
```

```bash
sudo netplan apply
# Alternative: wait only for "any routable interface" instead of all of them
sudo systemctl edit systemd-networkd-wait-online.service
#   [Service]
#   ExecStart=
#   ExecStart=/usr/lib/systemd/systemd-networkd-wait-online --any
```

**Why this fix works:** `optional: true` tells the wait service not to require that link, and `--any` changes the rule to "at least one interface is up". Masking the service also removes the delay, but then units that need the network at boot (NFS mounts, Docker with remote volumes, a database that binds to a specific IP) may start before it exists and fail in harder-to-read ways. Prefer marking interfaces optional.

**Prevent it:** mark spare NICs and lab bridges optional when you provision, and watch boot time in your monitoring; a jump of two minutes after a hardware change is this entry.

**Next step:** [Services and systemd](07-services-systemd.md) · [Network reference: netplan](02-network.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD · [netplan docs](https://netplan.readthedocs.io/)

**Community threads:** [Launchpad #2063331: wait-online runs into a timeout](https://bugs.launchpad.net/bugs/2063331) · [Launchpad #2036358: wait-online times out after jammy](https://bugs.launchpad.net/bugs/2036358) · [systemd#27724: wait-online fails with a bridge interface](https://github.com/systemd/systemd/issues/27724) · Search: [Server Fault](https://serverfault.com/search?q=systemd-networkd-wait-online+timeout+netplan+optional) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=systemd-networkd-wait-online+2+minutes&restrict_sr=1)

### 1.4 Two networks: replies leave the wrong NIC

> **Seen as:** the server's second address (10.0.2.10) can't be reached from the remote office although ping from the same subnet works; `tcpdump` shows the SYN arriving on ens19 and the SYN-ACK leaving on ens18; the edge firewall logs blocked packets "without a matching state" · **Where:** multi-homed servers (management plus service network, a DMZ leg, a second ISP), VMs with two bridges, cloud instances with two ENIs · **Level:** [L2 · Mid] · **How common:** a classic Server Fault question; one of the hardest network bugs for juniors because each half looks fine

**Why it happens:** Linux routes replies by destination only, using the main table. A packet that arrives on ens19 from 198.51.100.20 gets its reply sent out of whichever interface has the route to 198.51.100.20, usually the default route on ens18. The reply then leaves with the source 10.0.2.10 through a router that never saw the request: a stateful firewall drops it as invalid, and a host with strict reverse-path filtering (`rp_filter=1`) drops the inbound packets on the other side too.

**Diagnose:**

```bash
sudo tcpdump -tni any host 198.51.100.20 and tcp port 443 -c 6
ip route get 198.51.100.20 from 10.0.2.10
sysctl net.ipv4.conf.all.rp_filter net.ipv4.conf.ens19.rp_filter
ip rule
```

```text
ens19 In  IP 198.51.100.20.53122 > 10.0.2.10.443: Flags [S], seq 1880211
ens18 Out IP 10.0.2.10.443 > 198.51.100.20.53122: Flags [S.], seq 990121, ack 1880212
ens19 In  IP 198.51.100.20.53122 > 10.0.2.10.443: Flags [S], seq 1880211
198.51.100.20 from 10.0.2.10 via 10.0.1.1 dev ens18 uid 0
net.ipv4.conf.all.rp_filter = 2
net.ipv4.conf.ens19.rp_filter = 2
0:      from all lookup local
32766:  from all lookup main
32767:  from all lookup default
```

**What the output tells you:** the request comes in on ens19, the reply goes out on ens18 through 10.0.1.1, and the client retransmits the SYN because the reply never arrives. There is no policy rule that sends traffic sourced from 10.0.2.10 back through 10.0.2.1.

**Fix:**

```yaml
# Source-based routing: anything sourced from the second address uses its own table
network:
  version: 2
  ethernets:
    ens19:
      addresses: [10.0.2.10/24]
      routes:
        - to: default
          via: 10.0.2.1
          table: 102
        - to: 10.0.2.0/24
          scope: link
          table: 102
      routing-policy:
        - from: 10.0.2.10
          table: 102
```

```bash
sudo netplan try
ip rule ; ip route show table 102
# Loose reverse-path filtering for multi-homed hosts, if packets are dropped on the way in
echo 'net.ipv4.conf.all.rp_filter = 2' | sudo tee /etc/sysctl.d/60-rp-filter.conf
sudo sysctl --system
```

**Why this fix works:** the policy rule makes the kernel look up table 102 for every packet sourced from 10.0.2.10, so replies leave through the interface and router the request came in on, and the stateful devices on that path see both halves of the flow. Loose `rp_filter=2` accepts packets that arrive on an interface which is not the best route back, which multi-homed hosts need. Don't disable reverse-path filtering entirely on internet-facing hosts, and don't paper over it by allowing "invalid" state on the firewall.

**Prevent it:** give each multi-homed host a documented routing design (which network carries what), add source-based rules at provisioning time, and test every address from a remote network, not only from its own subnet.

**Next step:** [Learn networking: Routing](28-learn-networking.md) · [Kernel and sysctl](13-kernel-system.md) · KodeKloud: *Networks and Communications* — Network Troubleshooting · [kernel ip-sysctl docs](https://docs.kernel.org/networking/ip-sysctl.html)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=multi-homed+linux+reply+wrong+interface+policy+routing) · [Server Fault (rp_filter)](https://serverfault.com/search?q=rp_filter+asymmetric+routing) · [Reddit r/networking](https://www.reddit.com/r/networking/search/?q=asymmetric+routing+linux+two+nics&restrict_sr=1)

### 1.5 Docker's subnets collide with a real network

> **Seen as:** right after installing Docker, running `docker compose up` or installing Dokploy, the host can no longer reach a VPN or office subnet such as 172.18.0.0/16 or 192.168.0.0/20; `ip route` shows a `br-` interface owning that range · **Where:** hosts in networks that use 172.16.0.0/12 or 192.168.0.0/16 internally, corporate VPNs, AWS VPCs in 172.31.0.0/16 · **Level:** [L2 · Mid] · **How common:** very common in companies; a long-running theme on Stack Overflow, r/docker and the Docker forum

**Why it happens:** Docker carves bridge networks out of its default address pools (172.17.0.0/16 to 172.31.0.0/16, then 192.168.0.0/16 in /20 steps). Every Compose project creates a new network, so the next free /16 eventually lands on a range your company already uses, and the host's connected route for the bridge beats the route through the VPN or gateway. Swarm (and so Dokploy) has its own pool for overlay networks, chosen at `docker swarm init`.

**Diagnose:**

```bash
ip route | grep -E 'docker0|br-'
docker network ls -q | xargs docker network inspect -f '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}'
ip route get 172.18.5.20
```

```text
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev br-6f2c0e1a9b3d proto kernel scope link src 172.18.0.1
bridge 172.17.0.0/16
shop_default 172.18.0.0/16
172.18.5.20 dev br-6f2c0e1a9b3d src 172.18.0.1 uid 1000
```

**What the output tells you:** the Compose network shop_default took 172.18.0.0/16, so traffic for the office host 172.18.5.20 goes into the local bridge instead of the VPN.

**Fix:**

```json
{
  "bip": "10.200.0.1/24",
  "default-address-pools": [
    { "base": "10.201.0.0/16", "size": 24 }
  ]
}
```

```bash
# /etc/docker/daemon.json as above, then recreate the networks that collide
sudo systemctl restart docker
docker compose -p shop down && docker compose -p shop up -d
# New Swarm clusters: choose the overlay pool at init time
docker swarm init --default-addr-pool 10.202.0.0/16 --default-addr-pool-mask-length 24
```

**Why this fix works:** pools only affect networks created afterwards, so moving them to a range nobody uses and recreating the colliding networks removes the overlapping connected route. Small /24 networks also stop Docker from burning a /16 per project. Existing Swarm overlays keep their subnets; changing the Swarm pool on a live Dokploy cluster means rebuilding the swarm, so plan it.

**Prevent it:** reserve a range for containers in your IP plan and put `default-address-pools` in the Docker install role before the first container starts; do the same for Kubernetes pod and service CIDRs.

**Next step:** [Learn Docker: networking](30-learn-docker.md) · [Learn networking: IP addressing](28-learn-networking.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Docker docs: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+network+overlaps+vpn+subnet+default-address-pools) · [Server Fault](https://serverfault.com/search?q=docker+bridge+172.18+conflict+vpn) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=default-address-pools+subnet+conflict&restrict_sr=1)

### 1.6 A server or NAS gets no IP after a reset or a hardware change

> **Seen as:** after a reset, a reinstall, a disk or NIC swap, or an adapter pulled and reconnected, the box never comes up on its address; the static IP and gateway look right in the UI, yet `ip -br -4 addr` shows nothing on the live NIC · **Where:** TrueNAS SCALE, Proxmox VE, Ubuntu with netplan, ESXi · **Level:** [L1 · Junior] · **How common:** a steady stream of TrueNAS forum threads, and Proxmox threads after upgrades that renamed a NIC

**Why it happens:** "no IP" is two questions. Either the box doesn't hold the address (never saved, saved for the wrong NIC, DHCP still on, overwritten at boot), or it holds it and nobody reaches it (link, VLAN, gateway, ARP, a duplicate). On appliances (TrueNAS, OMV, ESXi) the vendor's database is the source of truth, settings are stored per interface name, and files under /etc are generated. When a hardware change renames the NIC, the saved settings stay on the old name and the live NIC gets nothing. Samples use 192.0.2.0/24 (gateway 192.0.2.1, host 192.0.2.10); the TrueNAS case keeps its real 192.168.1.26/24.

**Diagnose from the console, bottom-up:** use the local console or IPMI/iKVM, not the network you are debugging, and prove each layer before moving up.

**Step 1 — Live names and link (L1).** **Goal:** know what the kernel calls each NIC this boot, and whether the cabled one has carrier.

```bash
ip -br link                                  # real names, state and MAC (all platforms)
sudo ethtool enp4s0 | grep -E 'Speed|Link detected'
sudo dmesg | grep -i 'renamed from'          # how udev named each NIC at this boot
```

```text
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp4s0           UP             3c:ec:ef:12:34:56 <BROADCAST,MULTICAST,UP,LOWER_UP>
        Speed: 1000Mb/s
        Link detected: yes
[    2.911402] igb 0000:04:00.0 enp4s0: renamed from eth0
```

**What it means:** one NIC, enp4s0 at this boot, with carrier. `NO-CARRIER` or `Link detected: no` stops you here (cable, port, switch). A USB adapter appears as `enx` plus its MAC. **Why this step:** a config naming an interface not in this list can't work. **Next step:** link up → Step 2; link down → reseat or swap the cable first.

**Step 2 — Address and route (L3).** **Goal:** see what the box really holds right now.

```bash
ip -br -4 addr
ip route
ip neigh show 192.0.2.1 ; ping -c3 192.0.2.1
```

```text
lo               UNKNOWN        127.0.0.1/8
enp4s0           UP
ping: connect: Network is unreachable
```

**What it means:** link up, no IPv4 address, no route (`ip route` printed nothing): config, not network. With the address and `default via 192.0.2.1` present but the gateway's neighbour entry `FAILED` or `INCOMPLETE`, go back to L2 (VLAN, LACP, port security). **Why this step:** it splits "doesn't hold the IP" from "holds it, nobody reaches it". **Next step:** no address → Step 3; no default route, or a dead UI → the table below.

**Step 3 — Who owns the config, and which name does it use?** **Goal:** compare the saved config with the live names from Step 1.

```bash
# Ubuntu (netplan + networkd)
ls /etc/netplan /run/netplan ; sudo netplan get
networkctl status enp4s0 | grep -E 'Network File|State'
# Proxmox VE (ifupdown2)
grep -nE 'iface|address|gateway|bridge-ports' /etc/network/interfaces
journalctl -b -u networking --no-pager | grep -i 'does not exist'
# TrueNAS SCALE: the middleware database, not /etc
midclt call interface.query | jq -c '.[] | {name, ipv4_dhcp, aliases}'
midclt call network.configuration.config | jq '{ipv4gateway, nameserver1}'
```

```text
7:iface enp3s0 inet manual
10:iface vmbr0 inet static
11:        address 192.0.2.10/24
12:        gateway 192.0.2.1
13:        bridge-ports enp3s0
Nov 10 07:02:11 pve1 ifreload[905]: error: vmbr0: bridge port enp3s0 does not exist
```

**What it means:** this Proxmox config is correct, but for enp3s0, which no longer exists; the live NIC is enp4s0. That is the rename case below. **Why this step:** most "no IP" configs are right but aimed at the wrong thing: a gone name, a rewritten file, an unsaved test. **Next step:** names differ → the teaching case; names match → the table.

**Step 4 — Apply through the owner, reboot, re-check.** **Goal:** a change that survives a reboot.

```bash
sudo netplan try --timeout 180     # Ubuntu: reverts unless confirmed (entry 1.1)
sudo ifreload -a                   # Proxmox: no rollback, keep the console open
# TrueNAS: console menu 1) Configure network interfaces, then 2) Configure network settings
ip -br -4 addr ; ip route ; ping -c3 192.0.2.1    # after the change, and again after a reboot
```

**What it means:** address and `default via` survive the reboot, so the config lives where its owner reads it. **Why this step:** a runtime `ip addr add`, or a hand-edited file on an appliance, lasts until the next boot. **Next step:** works → record NIC names and MACs, export a config backup; fails → the table. ESXi's console path is the DCUI: F2, Configure Management Network (adapters, IPv4, DNS), then Test Management Network.

**The teaching case: hardware changed, interface renamed, settings stuck on the old name.** A TrueNAS SCALE box after pools were destroyed and a network adapter was pulled and reconnected:

- Static IP 192.168.1.26/24 set in the web UI with Test Changes, then Save Changes, done correctly; the gateway was present. Still no IP.
- Link light on and the NIC listed in the console: cable and NIC detection were fine.
- DNS records, dynamic DNS, a router reservation, another switch port and reboots changed nothing.
- Fixed from the console: option 1 on the listed NIC (DHCP off, alias 192.168.1.26/24, save), option 2 (gateway, DNS), then a reboot.

> **Most likely cause, inferred from the evidence, not proven:** reconnecting the adapter gave it a new interface name (a USB adapter is named after its MAC, `enx…`; another slot or PCI layout turns `enp3s0` into `enp4s0`). TrueNAS keeps settings per interface name, so the saved IP stayed on a gone name and the live NIC had no config. Configuring the interface that exists now fixed it, which fits, but nobody captured the names before and after.

**Prove it next time,** before changing anything: compare `ip -br link` with the console list (option 1) or `midclt call interface.query | jq -r '.[].name'` and with the names you recorded. A configured name that is missing or down next to an unconfigured new name is the signature; `sudo dmesg | grep -i 'renamed from'` shows this boot's naming (`journalctl -k -b -1` the previous boot's, if the journal persists).

**Fix:**

- **TrueNAS:** console option 1 on the interface that exists now (DHCP no, Alias = IP/prefix, save), option 2 for gateway and DNS, reboot, Step 4 checks. Don't edit /etc, and don't pick "Reset configuration to defaults": it wipes users, shares and pool config, not just the network.
- **Proxmox:** the new name in the `iface` and `bridge-ports` lines, then `ifreload -a`; full walk-through in [50 §7.2](50-problems-cloud-iac-proxmox.md#72-web-ui-dead-after-an-ip-hostname-or-nic-change).
- **Ubuntu:** fix the interface key in netplan, or match the NIC by MAC so its name stops mattering:

```yaml
network:
  version: 2
  ethernets:
    lan0:
      match: { macaddress: "3c:ec:ef:12:34:56" }
      set-name: lan0
      addresses: [192.0.2.10/24]
      routes: [{ to: default, via: 192.0.2.1 }]
```

**Why this fix works:** the settings now sit on an interface that exists, written by the tool that owns them, and the reboot proves they persist. A MAC match survives a slot change or kernel rename, not a replacement NIC with a new MAC: keep the MACs in your notes.

**Other confirmed causes** (numbers are TrueNAS or Proxmox forum threads where the poster confirmed the fix):

| Cause | Signature | Fix | Source |
|---|---|---|---|
| TrueNAS Test Changes rolled back after 60 s | works briefly, then DHCP is back | longer timer, open the **new** IP in a new tab in time, Save Changes; or the console | [57424](https://forums.truenas.com/t/unable-to-configure-static-ip-addresses/57424) |
| TrueNAS static IP not in Alias | DHCP off, no address; or DHCP on plus alias, two IPv4s | the static address is the Alias field | [103146](https://cdn.truenas.com/community/threads/impossible-to-configure-static-ip-without-dhcp-server.103146/) |
| TrueNAS gateway not in Global Configuration; router IP typed into DNS | LAN works, nothing beyond; no `default via`, or via the box itself | Global Configuration: IPv4 Default Gateway = router (console option 2) | [48605](https://forums.truenas.com/t/factory-reset-network-settings-and-or-assign-static-ip/48605) |
| Leftover bridge, LAGG or alias | br0 or bond0 holds the IP; old install fails, fresh one works | console option 1, Y to reset the interface, re-add the alias, option 2 | [100604](https://cdn.truenas.com/community/threads/old-truenas-install-cant-find-web-fresh-install-can.100604/), [45429](https://forums.truenas.com/t/issue-setting-default-gateway/45429) |
| TrueNAS web UI bound to an old IP | pings, SMB works, browser refused | System > General > GUI: Web Interface IPv4 Address 0.0.0.0 | [46460](https://forums.truenas.com/t/cannot-change-ip-address-of-truenas-ce/46460) |
| Proxmox: bridge port does not exist | `vmbr0: bridge port eno8 does not exist` after an upgrade | new name in /etc/network/interfaces, `ifreload -a` | [145727](https://forum.proxmox.com/threads/no-networking-after-upgrade-to-8-2.145727/) |
| Ubuntu: cloud-init rewrites 50-cloud-init.yaml | static config gone after reboot | `network: {config: disabled}` in cloud.cfg.d, own file (entry 1.2) | [cloud-init docs](https://docs.cloud-init.io/en/latest/reference/network-config.html) |
| Ubuntu: `dhcp4: true` next to `addresses:` | two IPv4s, the DHCP route wins | `dhcp4: false`; check `netplan get` and /run/netplan | [netplan(5)](https://manpages.ubuntu.com/manpages/noble/man5/netplan.5.html) |
| Ubuntu: `netplan try` not confirmed | new IP gone after 120 s | confirm from a second session (entry 1.1) | entry 1.1 |
| Ubuntu: DUID, not MAC, as DHCP client id | pool address, not the reservation | `dhcp-identifier: mac` | [netplan YAML](https://netplan.readthedocs.io/en/stable/netplan-yaml/) |
| Router ARP cache holds the old MAC | after a NIC swap, others can't reach the box | clear the entry, or `arping -U -I IFACE 192.0.2.10` | [Cisco community](https://community.cisco.com/t5/switching/arp-timeout-lt-mac-aging-timeout/td-p/2478506) (unverified) |
| IP inside the DHCP pool, or a duplicate | works, then flaps; two MACs answer ARP | `arping -D -I IFACE -c3 192.0.2.10` first; statics outside the pool | [arping(8)](https://man7.org/linux/man-pages/man8/arping.8.html); no confirmed thread, rule it out |
| Wrong VLAN or tagging | IP present, gateway `INCOMPLETE` | fix the access VLAN, or tagged versus native | [Broadcom KB 443098](https://knowledge.broadcom.com/external/article/443098/management-network-or-gui-inaccessible-o.html) |
| LACP on one side only | bond up, partner MAC all zeros in /proc/net/bonding/bond0 | both ends, or active-backup | [kernel bonding docs](https://www.kernel.org/doc/html/latest/networking/bonding.html) |

**Red herrings:** DNS records, dynamic DNS and a DHCP reservation don't give an address to a box set to static; they matter only while it is a DHCP client. "Another switch port" rules out one port, not a VLAN or port-security profile both share.

**Prevent it:** after any hardware change, check interface names first (`ip -br link` against your notes); pin names with a systemd .link file on Ubuntu and Proxmox (`[Match] MACAddress=`, `[Link] Name=lan0`, then `update-initramfs -u`; Proxmox ships `pve-network-interface-pinning`, see 50 §7.2); avoid USB NICs on TrueNAS; download a config backup (TrueNAS: System > General > Manage Configuration) before every change; record each NIC's MAC for router reservations; keep statics outside the DHCP pool.

**Next step:** [Linux systems: Boot waits two minutes for the network](41-problems-linux-systems.md#35-boot-waits-two-minutes-for-the-network) (a renamed NIC can leave a netplan interface with no carrier) · [Linux systems: SMART warnings](41-problems-linux-systems.md#112-smart-warnings-is-the-disk-dying) (before a pool goes back on a suspect disk) · [Network reference](02-network.md) · [Learn networking: IP addressing](28-learn-networking.md) · [TrueNAS docs: interfaces](https://www.truenas.com/docs/scale/25.10/scaletutorials/network/interfaces/) · [TrueNAS docs: console menu](https://www.truenas.com/docs/scale/25.10/gettingstarted/install/consolesetupmenuscale/) · [Proxmox wiki: Network Configuration](https://pve.proxmox.com/wiki/Network_Configuration)

**Community threads:** [TrueNAS: unseated cable, config wiped first](https://forums.truenas.com/t/lost-network-connectivity-ipv4/14872) · [Broadcom KB 405795: ESXi vmnic order changed after reinstall](https://knowledge.broadcom.com/external/article/405795/network-connectivity-lost-on-esxi-after.html) · Search: [Reddit r/truenas](https://www.reddit.com/r/truenas/search/?q=static%20ip%20reverts%20dhcp&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=netplan+static+ip+lost+after+reboot)

## 2. Name resolution on the host

Ubuntu resolves names through a chain: the application calls getaddrinfo, NSS reads /etc/nsswitch.conf (files, then mDNS, then DNS), DNS goes to the systemd-resolved stub at 127.0.0.53, and resolved forwards to the servers and routing domains it learned per interface. Almost every "DNS is broken" ticket on a host is one broken link in that chain, and `dig` skips half of it.

### 2.1 Temporary failure in name resolution

> **Seen as:** `ping: www.example.com: Temporary failure in name resolution`, `apt update` failing with `Temporary failure resolving 'archive.ubuntu.com'`, `curl: (6) Could not resolve host` · **Where:** fresh installs, hosts after `do-release-upgrade`, servers where someone edited /etc/resolv.conf by hand, desktops turned into servers · **Level:** [L0 · Fresher] · **How common:** one of the most viewed Linux errors anywhere; recurring Ubuntu Discourse threads after 24.04 upgrades

**Why it happens:** on Ubuntu /etc/resolv.conf should be a symlink to /run/systemd/resolve/stub-resolv.conf, which points every program at 127.0.0.53. The chain breaks when the symlink was replaced by a hand-written file, when a leftover resolvconf package points it somewhere else after an upgrade, when systemd-resolved is stopped or masked, when NetworkManager and netplan fight over the same interface, or simply when no interface has any DNS server configured (a static netplan file without `nameservers:`).

**Diagnose:**

```bash
ls -l /etc/resolv.conf
systemctl is-active systemd-resolved
resolvectl status
resolvectl query www.example.com
```

```text
lrwxrwxrwx 1 root root 29 Mar 12  2024 /etc/resolv.conf -> ../run/resolvconf/resolv.conf
active
Global
         Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
  resolv.conf mode: foreign
Link 2 (ens18)
    Current Scopes: none
         Protocols: -DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
www.example.com: resolve call failed: No appropriate name servers or networks for name found
```

**What the output tells you:** resolv.conf points at a leftover resolvconf file ("resolv.conf mode: foreign"), and ens18 has no DNS servers at all ("Current Scopes: none"), so even resolved has nobody to ask. Two problems, both on the host, none on the network.

**Fix:**

```bash
dpkg -l resolvconf 2>/dev/null | grep ^ii && sudo apt purge resolvconf    # only a leftover; check what installed it first
sudo ln -sf ../run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl enable --now systemd-resolved
# Put the DNS servers where they belong: the netplan file (nameservers: addresses: [...]), then
sudo netplan apply
resolvectl status ens18 | grep -E 'Current DNS Server|DNS Servers'
getent ahosts www.example.com
```

<div class="env" data-env="onprem" markdown="1">

**On-prem:** point servers at your internal resolvers (two of them, for example 10.0.1.53 and 10.0.1.54), not at public resolvers, otherwise internal zones such as corp.example.com stop resolving. If DHCP hands out DNS, fix it once on the DHCP server or OPNsense instead of on each host.

</div>

<div class="env" data-env="cloud" markdown="1">

**On AWS:** the VPC resolver (the VPC base address plus two, or 169.254.169.253) is the only one that answers Route 53 private hosted zones and EC2 internal names, so keep it first; the DHCP options set of the VPC decides what instances get. Hybrid setups that need on-prem names use Route 53 Resolver outbound endpoints and forwarding rules, not a hand-edited resolv.conf.

</div>

**Why this fix works:** restoring the symlink sends every program to the stub again, and DNS servers in netplan reach resolved through systemd-networkd, so they survive reboots and renewals. Hand-editing /etc/resolv.conf "works" until the next reboot or package update rewrites it. Don't disable systemd-resolved to fix this unless you deliberately run another local resolver (entry 7.4).

**Prevent it:** check `readlink /etc/resolv.conf` and `resolvectl query` in your post-upgrade checklist, keep DNS in netplan or DHCP only, and remove resolvconf from images that don't need it.

**Next step:** [DNS reference: which resolver is this box using](08-dns.md) · [Learn networking: DNS in depth](28-learn-networking.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Networking: DNS ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)) · [systemd-resolved docs](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html)

**Community threads:** [Ubuntu Discourse: DNS not working on 24.04.4 after do-release-upgrade](https://discourse.ubuntu.com/t/dns-nameservers-are-not-configured-or-dont-work-on-ubuntu-24-04-4-lts-after-do-release-upgrade/79606) · [Ubuntu Discourse: Nameservers on Ubuntu 24.04](https://discourse.ubuntu.com/t/nameservers-ubuntu-24-04/56589) · Search: [Server Fault](https://serverfault.com/search?q=%22Temporary+failure+in+name+resolution%22+systemd-resolved) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=%22Temporary+failure+in+name+resolution%22&restrict_sr=1)

### 2.2 dig answers, the application can't resolve

> **Seen as:** `dig +short api.example.com` returns the right address while `curl` fails with `Could not resolve host`, or connects to an old IP; `ping db` works but the app's `db.corp.local` doesn't · **Where:** any Linux host; especially hosts with old /etc/hosts entries, Active Directory domains named .local, and containers based on Alpine · **Level:** [L1 · Junior] · **How common:** extremely common; the reason Julia Evans and others keep writing "dig is not what your app uses"

**Why it happens:** `dig` and `nslookup` speak DNS directly to the server in resolv.conf; applications call getaddrinfo, which goes through NSS. NSS reads /etc/hosts first, so a forgotten line from a migration wins over DNS. On hosts with avahi installed, `mdns4_minimal [NOTFOUND=return]` sends every .local name to multicast DNS and stops there, so an AD domain called corp.local never reaches your DNS server. Search domains and `ndots` change which name is really asked, and some runtimes cache answers on their own (the JVM, Node's agent pools, nginx resolving upstreams only at start-up).

**Diagnose:**

```bash
dig +short api.example.com
getent ahosts api.example.com | head -1      # exactly what applications get
grep -n 'api' /etc/hosts
grep '^hosts' /etc/nsswitch.conf
resolvectl query api.example.com             # the resolved path, with the link it used
```

```text
10.0.1.40
10.0.1.99       STREAM api.example.com
7:10.0.1.99 api.example.com
hosts:          files mdns4_minimal [NOTFOUND=return] dns
api.example.com: 10.0.1.40                      -- link: ens18
```

**What the output tells you:** DNS and resolved both say 10.0.1.40, but /etc/hosts line 7 still pins the name to the old server 10.0.1.99, and NSS reads files first. The nsswitch line also shows that any .local name would never reach DNS on this host.

**Fix:**

```bash
sudo sed -i.bak '/api\.example\.com/d' /etc/hosts     # or remove it in the Ansible template that wrote it
getent ahosts api.example.com | head -1
# AD domain under .local and avahi not needed on a server:
sudo apt purge avahi-daemon libnss-mdns
# Test a client against a specific address without touching DNS or /etc/hosts:
curl -sv --resolve api.example.com:443:10.0.1.40 https://api.example.com/health -o /dev/null
```

**Why this fix works:** removing the stale entry lets NSS fall through to DNS, and removing the mDNS module returns .local names to the normal resolver. `curl --resolve` proves which backend is healthy without changing anything for other programs. Don't "fix" resolution by adding more /etc/hosts lines: that is how this entry happened.

**Prevent it:** treat /etc/hosts as managed config (only localhost and the host's own name), test with `getent` in health checks instead of `dig`, and avoid .local for internal domains in new designs (use a subdomain you own, such as corp.example.com, or home.arpa for homelabs).

**Next step:** [DNS reference](08-dns.md) · [Learn networking: DNS in depth](28-learn-networking.md) · KodeKloud: *Demystifying DNS* — Miscellaneous: Troubleshooting DNS ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page)) · [systemd-resolved docs](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=dig+works+but+curl+%22could+not+resolve+host%22) · [Server Fault](https://serverfault.com/search?q=nsswitch+mdns4_minimal+.local+domain+not+resolving) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=dig+works+getent+fails&restrict_sr=1)

### 2.3 Split DNS over a VPN breaks or leaks

> **Seen as:** on the VPN, internal names such as gitlab.corp.example.com don't resolve while internal IPs work; or every DNS query, including public ones, goes through the VPN; `wg-quick` prints `resolvconf: command not found`; after installing Tailscale, /etc/resolv.conf suddenly says `nameserver 100.100.100.100` · **Where:** WireGuard, OpenVPN, Tailscale and NetBird clients on Ubuntu servers and laptops · **Level:** [L2 · Mid] · **How common:** very common; Tailscale has a dedicated Linux DNS page and several issues about resolv.conf handling

**Why it happens:** systemd-resolved keeps DNS servers and routing domains per link. Split DNS works only when the VPN link (wg0, tun0, tailscale0) carries its own DNS server plus a routing domain such as `~corp.example.com`; then only those names go into the tunnel. Plain WireGuard sets none of that unless you tell it to, and wg-quick's `DNS =` line calls a `resolvconf` command that minimal Ubuntu servers don't have. A routing domain of `~.` sends everything into the tunnel. Tailscale integrates cleanly only when resolv.conf is the resolved stub symlink; otherwise it overwrites /etc/resolv.conf and proxies all DNS through 100.100.100.100.

**Diagnose:**

```bash
resolvectl status wg0
resolvectl query gitlab.corp.example.com
readlink /etc/resolv.conf
resolvectl status tailscale0 2>/dev/null | grep -E 'DNS Servers|DNS Domain'
```

```text
Link 5 (wg0)
    Current Scopes: none
         Protocols: -DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
gitlab.corp.example.com: resolve call failed: 'gitlab.corp.example.com' not found
../run/systemd/resolve/stub-resolv.conf
       DNS Servers: 100.100.100.100
        DNS Domain: ~tail1a2b3.ts.net ~.
```

**What the output tells you:** wg0 has no DNS server and no domain, so internal names go to the public resolver and come back NXDOMAIN. The Tailscale link carries `~.`, which means "send all names here": the admin console has an override for global DNS turned on, which is what makes every lookup go through the tailnet.

**Fix:**

```ini
# /etc/wireguard/wg0.conf on the client: route only corp names to the office resolver
[Interface]
Address = 10.8.0.2/32
PrivateKey = CLIENT_PRIVATE_KEY
PostUp = resolvectl dns %i 10.8.0.1; resolvectl domain %i '~corp.example.com'; resolvectl default-route %i false
PostDown = resolvectl revert %i
```

```bash
sudo wg-quick down wg0 && sudo wg-quick up wg0
resolvectl query gitlab.corp.example.com
# Servers that must keep their own resolver config: don't let Tailscale manage DNS
sudo tailscale set --accept-dns=false
```

**Why this fix works:** a routing domain with `~` tells resolved "use this link's server for names under this suffix", and `default-route false` keeps public names on the normal uplink, which is split DNS with no leak in either direction. Using resolvectl directly avoids the missing resolvconf command. `--accept-dns=false` keeps servers on their managed resolvers while still joining the tailnet. Don't paste the office DNS server into /etc/resolv.conf: every lookup then breaks when the tunnel is down.

**Prevent it:** decide per VPN which suffixes go through it and write them into the VPN config, not into each laptop by hand; keep /etc/resolv.conf as the stub symlink on every host so VPN clients can integrate; test both an internal and a public name after every VPN change.

**Next step:** [Learn networking: VPNs, overlays and MTU](28-learn-networking.md) · [DNS reference](08-dns.md) · KodeKloud: *Demystifying DNS* — DNS as a System · [Tailscale docs: Linux DNS](https://tailscale.com/docs/reference/linux-dns)

**Community threads:** [Tailscale docs: Configuring Linux DNS](https://tailscale.com/docs/reference/linux-dns) · [tailscale#7816: DNS broken on Amazon Linux 2023 (forwarding loop)](https://github.com/tailscale/tailscale/issues/7816) · Search: [Server Fault](https://serverfault.com/search?q=wireguard+split+dns+systemd-resolved+resolvectl+domain) · [Reddit r/WireGuard](https://www.reddit.com/r/WireGuard/search/?q=resolvconf+command+not+found&restrict_sr=1) · [Reddit r/Tailscale](https://www.reddit.com/r/Tailscale/search/?q=resolv.conf+100.100.100.100&restrict_sr=1)

### 2.4 Containers and pods can't resolve

> **Seen as:** inside a container `nslookup gitlab.corp.example.com` times out or returns NXDOMAIN while the host resolves it; `docker run` shows `nameserver 8.8.8.8` in the container's resolv.conf; CoreDNS pods crash with `[FATAL] plugin/loop: Loop (127.0.0.1:55953 -> :53) detected for zone "."` · **Where:** Docker, Compose, Dokploy and Swarm on hosts with systemd-resolved or VPN split DNS; kubeadm, k3s or hand-built Kubernetes nodes on Ubuntu · **Level:** [L2 · Mid] · **How common:** very common; CoreDNS issues #2087 and #2391 plus a whole troubleshooting section in the CoreDNS loop plugin docs

**Why it happens:** 127.0.0.53 lives in the host's network namespace, so a container can't use it. Docker therefore reads the real upstream list from /run/systemd/resolve/resolv.conf and hands it to the container (default bridge) or to its embedded DNS server at 127.0.0.11 (user-defined networks, Compose, Swarm). Per-link routing domains don't survive that copy, so split-DNS names disappear, and if no usable upstream is left Docker falls back to Google's public resolvers, which corporate firewalls often block. In Kubernetes, if the kubelet passes the stub resolv.conf to pods, CoreDNS forwards to 127.0.0.53 inside its own pod, which is itself: the loop plugin detects that and stops the pod on purpose.

**Diagnose:**

```bash
docker run --rm busybox cat /etc/resolv.conf
docker run --rm busybox nslookup gitlab.corp.example.com
cat /run/systemd/resolve/resolv.conf | grep nameserver
# Kubernetes
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=3
grep -i resolvConf /var/lib/kubelet/config.yaml
```

```text
nameserver 8.8.8.8
nameserver 8.8.4.4
;; connection timed out; no servers could be reached
nameserver 127.0.0.1
[FATAL] plugin/loop: Loop (127.0.0.1:55953 -> :53) detected for zone ".", see https://coredns.io/plugins/loop#troubleshooting. Query: "HINFO 4547991504243258144.3688648895315093531."
resolvConf: /etc/resolv.conf
```

**What the output tells you:** the host's real upstream list holds only 127.0.0.1 (a local dnsmasq or Pi-hole on the host), which Docker drops because a container can't reach the host's loopback; with nothing usable left, Docker fell back to 8.8.8.8, which the office firewall blocks. On the Kubernetes node the kubelet hands pods /etc/resolv.conf, the stub, which is exactly the loop CoreDNS reports.

**Fix:**

```json
{
  "dns": ["10.0.1.53", "10.0.1.54"],
  "dns-search": ["corp.example.com"]
}
```

```bash
# /etc/docker/daemon.json as above, then
sudo systemctl restart docker && docker run --rm busybox nslookup gitlab.corp.example.com
# Kubernetes node: give pods the real upstream list, then restart CoreDNS
sudo sed -i 's#^resolvConf: .*#resolvConf: /run/systemd/resolve/resolv.conf#' /var/lib/kubelet/config.yaml
sudo systemctl restart kubelet
kubectl -n kube-system rollout restart deployment coredns
```

**Why this fix works:** explicit `dns` servers are reachable from inside container namespaces and resolve internal zones, so containers stop depending on what the host's stub learned from a VPN. Pointing the kubelet at the real upstream file breaks the loop at its source; kubeadm normally detects systemd-resolved and does this for you, so the broken state usually comes from a hand-edited config or a custom install. Don't delete the loop plugin from the Corefile: the loop is still there and now silently eats CPU.

**Prevent it:** set `dns` in the Docker install role for hosts in networks with internal zones; on Kubernetes nodes keep resolvConf pointing at /run/systemd/resolve/resolv.conf and test pod DNS (`kubectl run -it --rm dnsutils --restart=Never --image=busybox:1.28 -- nslookup kubernetes.default`; keep the 1.28 tag, because newer busybox nslookup builds ignore the search list and report false failures) after every node build.

**Next step:** [Learn Docker: networking and DNS](30-learn-docker.md) · [Learn Kubernetes: DNS](31-learn-kubernetes.md) · [Containers and K8s playbook](26-playbook-containers-k8s.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: CoreDNS in Kubernetes ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page)) · [Kubernetes docs: Debugging DNS resolution](https://www.kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)

**Community threads:** [coredns#2087: loop plugin with systemd-resolved](https://github.com/coredns/coredns/issues/2087) · [coredns#2391: CoreDNS crashing due to loop detection](https://github.com/coredns/coredns/issues/2391) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+container+dns+8.8.8.8+systemd-resolved+127.0.0.53) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=coredns+loop+detected+systemd-resolved&restrict_sr=1)

## 3. Host firewalls: UFW, firewalld, nftables

The kernel has one packet filter (netfilter), and on a typical Docker host four programs write rules into it: UFW or firewalld, Docker, sometimes Kubernetes or Tailscale, and maybe fail2ban or CrowdSec. Most firewall surprises come from not knowing which program's rule sees the packet first.

### 3.1 Docker publishes ports past UFW

> **Seen as:** `ufw status` shows only 22, 80 and 443 allowed, yet a port scan from outside finds PostgreSQL on 5432 or Redis on 6379; a Dokploy database with an "external port" is reachable from the internet · **Where:** every Ubuntu host running Docker, Compose, Swarm or Dokploy with UFW (and firewalld hosts too) · **Level:** [L1 · Junior] · **How common:** one of the best-known Docker pitfalls; a section in Docker's own firewall docs, the ufw-docker project, and a steady stream of exposed-database incidents

**Why it happens:** a published port (`-p 5432:5432`, `ports:` in Compose) becomes a DNAT rule in the nat table's PREROUTING chain. After DNAT the packet is no longer for the host, so it goes through the FORWARD chain, where Docker's own chains (DOCKER-USER first, then Docker's accept rules) come before UFW's forward rules. UFW's INPUT rules never see it. Docker 28 tightened the defaults (ports that are not published are no longer reachable by routing straight to the container IP, and 28.3.3 fixed a firewalld-reload exposure, CVE-2025-54388), but a port published on 0.0.0.0 is still open to every address by design. Swarm's routing mesh publishes on every node.

**Diagnose:**

```bash
sudo ufw status
docker ps --format '{{.Names}}\t{{.Ports}}'
sudo iptables -t nat -S DOCKER | grep 5432
sudo iptables -S DOCKER-USER
# From an outside host, never from the server itself:
nc -vz -w 3 203.0.113.10 5432
```

```text
Status: active
To                         Action      From
22/tcp                     ALLOW       10.0.1.0/24
80,443/tcp                 ALLOW       Anywhere
shop-db-1	0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
traefik	0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
-A DOCKER ! -i br-6f2c0e1a9b3d -p tcp -m tcp --dport 5432 -j DNAT --to-destination 172.18.0.2:5432
-N DOCKER-USER
Connection to 203.0.113.10 5432 port [tcp/postgresql] succeeded!
```

**What the output tells you:** the database is published on all IPv4 and IPv6 addresses, the DNAT rule sends outside traffic to it, DOCKER-USER is empty, and the outside test proves it is reachable despite UFW.

**Fix:**

```yaml
# Best: don't publish internal services at all; Traefik and the app reach them on the Docker network
services:
  db:
    image: postgres:17
    # no "ports:" section
  adminer:
    image: adminer
    ports:
      - "127.0.0.1:8081:8080"      # admin tools only on loopback, reach them with an SSH tunnel
```

```bash
# If a port must be published but only for the LAN, filter in DOCKER-USER (matches the original port)
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 5432 --ctdir ORIGINAL ! -s 10.0.1.0/24 -j DROP
# Make it persistent in /etc/ufw/after.rules (a *filter section with :DOCKER-USER and the same rule) or with a systemd unit
# Admin access without publishing anything:
ssh -L 5432:172.18.0.2:5432 ops@web1.example.com
```

**Why this fix works:** a service that isn't published has no DNAT rule, so nothing outside the Docker network can reach it, whatever the firewall says. Binding to 127.0.0.1 keeps the convenience of a host port without exposing it. DOCKER-USER is the chain Docker promises never to touch, and matching on the original destination port keeps the rule correct after DNAT. With Docker 29's experimental nftables backend there is no DOCKER-USER chain; Docker's docs describe adding your own nftables table instead. Don't set `"iptables": false` in daemon.json: container networking and publishing break in subtle ways.

**Prevent it:** review every `ports:` line in code review, prefer internal networks plus Traefik, scan your public IPs from outside on a schedule (nmap from a cloud VM, or an external attack-surface tool), and keep Docker updated for firewall fixes.

**Next step:** [Ports inventory playbook](22-playbook-ports-inventory.md) · [Security & DevSecOps: network security](37-learn-security-devsecops.md) · [Learn Docker](30-learn-docker.md) · KodeKloud: *Docker Certified Associate* — Docker Engine: Publishing Ports ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · [Docker docs: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

**Community threads:** [Docker blog: Engine v28 hardening container networking by default](https://www.docker.com/blog/docker-engine-28-hardening-container-networking-by-default/) · [Docker forum: update to 28.2.2 breaks bridge networking](https://forums.docker.com/t/update-to-docker-ce-28-2-2-breaks-bridge-networking-to-container/148399/10) · [Docker forum: blocking ports with nftables on v29](https://forums.docker.com/t/how-to-block-ports-inusing-nftables-with-docker-v29/151450) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+bypasses+ufw+published+port) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+ufw+bypass+DOCKER-USER&restrict_sr=1)

### 3.2 UFW locked you out, or a rule never matches

> **Seen as:** the SSH session dies right after `sudo ufw enable` (you answered "y" to `Command may disrupt existing ssh connections`); a new `ufw allow from 198.51.100.0/24 to any port 22` changes nothing; `[UFW BLOCK]` lines in the kernel log for traffic you think you allowed · **Where:** Ubuntu servers managed by hand, first hardening of a new VM · **Level:** [L0 · Fresher] · **How common:** a beginner classic; countless Server Fault and r/linuxadmin threads

**Why it happens:** UFW's default policy is deny incoming, so enabling it without an SSH rule cuts you off. UFW rules are evaluated in order and the first match wins: a `deny 22/tcp` added earlier sits above the new allow, and `ufw allow` appends to the end. Rules for a specific interface or protocol (`proto udp`) don't match traffic you assumed they would.

**Diagnose:**

```bash
sudo ufw status numbered
sudo ufw logging low
sudo journalctl -k --since '10 min ago' | grep 'UFW BLOCK' | tail -3
```

```text
     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     DENY IN     Anywhere
[ 2] 22/tcp                     ALLOW IN    198.51.100.0/24
[ 3] 443/tcp                    ALLOW IN    Anywhere
[UFW BLOCK] IN=ens18 OUT= MAC=bc:24:11:5e:7a:01 SRC=198.51.100.7 DST=10.0.1.10 LEN=60 TTL=57 ID=40612 DF PROTO=TCP SPT=50122 DPT=22 WINDOW=64240 RES=0x00 SYN URGP=0
```

**What the output tells you:** rule 1 denies SSH from anywhere before rule 2 can allow the office range, and the log shows the office address being blocked on port 22.

**Fix:**

```bash
sudo ufw delete 1
sudo ufw insert 1 allow proto tcp from 198.51.100.0/24 to any port 22
# Safe first-time enable on a remote host: allow SSH, set a rollback, enable, then cancel the rollback
sudo ufw allow OpenSSH
echo 'ufw disable' | sudo at now + 5 minutes
sudo ufw enable
sudo atq            # note the job number, then remove it once you know you can still log in: sudo atrm JOB
```

**Why this fix works:** inserting the allow at position 1 makes it the first match, and the `at` job is a dead-man switch that turns the firewall off if your new session can't reach the server. If you are already locked out, the console route from entry 1.1 is the way back. Don't run `ufw reset` on a production host to "start over": it removes every rule, including the ones for services you forgot about.

**Prevent it:** manage UFW rules with Ansible (the community.general.ufw module) so the order is reviewed and reproducible; keep a numbered, commented list of rules per host; remember that UFW does not see Docker-published ports (entry 3.1).

**Next step:** [Users, permissions and security: UFW](10-users-permissions-security.md) · [SSH and remote access](09-ssh-remote-access.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · [Ubuntu Server docs](https://documentation.ubuntu.com/server/)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=ufw+enable+locked+out+ssh) · [Server Fault (rule order)](https://serverfault.com/search?q=ufw+rule+order+deny+before+allow) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=ufw+locked+out&restrict_sr=1)

### 3.3 Firewall rules vanish or apply twice

> **Seen as:** after `systemctl restart nftables` every container loses its published ports until Docker restarts; `iptables -L` is empty although traffic is clearly filtered; `# Warning: iptables-legacy tables present, use iptables-legacy to see them`; after a `firewall-cmd --reload`, Docker or fail2ban rules are gone · **Where:** hosts where more than one tool manages netfilter: UFW or firewalld plus Docker, Kubernetes, Tailscale, CrowdSec or a hand-written nftables.conf · **Level:** [L2 · Mid] · **How common:** common on upgraded hosts and Kubernetes nodes; a known issue class in Docker, kube-proxy and firewalld trackers

**Why it happens:** the kernel has two iptables front ends (legacy and nf_tables) that keep separate rule sets; when one tool writes legacy rules and another writes nft rules, both are active but each listing shows only half. The stock /etc/nftables.conf starts with `flush ruleset`, which deletes every table on the host, including Docker's, Kubernetes' and Tailscale's, whenever the nftables service restarts. firewalld reloads rebuild its own ruleset; Docker now re-applies its rules after a reload and integrates with a firewalld "docker" zone, but older versions and other tools don't.

**Diagnose:**

```bash
iptables -V
sudo iptables-legacy -S 2>/dev/null | wc -l ; sudo iptables-nft -S 2>/dev/null | wc -l
sudo nft list tables
head -3 /etc/nftables.conf
```

```text
iptables v1.8.10 (nf_tables)
41
112
# Warning: iptables-legacy tables present, use iptables-legacy to see them
table ip nat
table ip filter
table ip6 nat
table inet filter
#!/usr/sbin/nft -f
flush ruleset
```

**What the output tells you:** both backends hold rules (41 legacy, 112 nft), so some tool still uses iptables-legacy, and the nftables service config will wipe everyone's tables on its next restart.

**Fix:**

```bash
# One backend for every tool
sudo update-alternatives --set iptables /usr/sbin/iptables-nft
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-nft
# Find what still writes legacy rules (an old script, an old kube-proxy image) and update it; then reboot in a window
```

```text
#!/usr/sbin/nft -f
# /etc/nftables.conf: manage only your own table, never flush everybody's
table inet hostfw
delete table inet hostfw
table inet hostfw {
  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept
    iif lo accept
    tcp dport { 22, 80, 443 } accept
    icmp type { echo-request, destination-unreachable, time-exceeded } accept
    icmpv6 type { echo-request, nd-neighbor-solicit, nd-neighbor-advert, nd-router-advert, packet-too-big } accept
  }
}
```

**Why this fix works:** with one backend, every listing shows every rule and tools that check for each other's chains find them. Declaring and then deleting your own table makes the file idempotent: reloading it replaces only your rules and leaves Docker, Kubernetes and VPN tables alone. Don't run `iptables -F` or `nft flush ruleset` on a container host to "clean up"; restart Docker afterwards if you already did.

**Prevent it:** pick one firewall manager per host (UFW or firewalld or your own nftables table), never two; document which other tools write rules; after any firewall change, check that containers still publish (`curl` a published port) and that `nft list tables` still shows Docker's tables.

**Next step:** [Learn networking: Firewalls and connection tracking](28-learn-networking.md) · [Network reference: firewalls](02-network.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Security: IPTABLES Introduction ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)) · [nftables wiki](https://wiki.nftables.org/)

**Community threads:** [Docker docs: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · Search: [Server Fault](https://serverfault.com/search?q=%22iptables-legacy+tables+present%22) · [Stack Overflow](https://stackoverflow.com/search?q=nftables+flush+ruleset+docker+rules+removed) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=nftables+docker+flush+ruleset&restrict_sr=1)

### 3.4 Open locally, closed from outside

> **Seen as:** `curl http://localhost:8443` works on the server, but from outside the connection times out or is refused · **Where:** any new service, any new server, after moving a service to a new port (for example Apache moved to 81/444 behind Traefik) · **Level:** [L1 · Junior] · **How common:** the most common network ticket there is; the core of the site-down and ports playbooks

**Why it happens:** a connection from outside crosses up to five gates: the address the service listens on (127.0.0.1 only reaches local clients), the host firewall, a network firewall or cloud filter in front of the host, NAT or port forwarding at the edge, and a return path for the reply. "Works locally" only proves the first gate for the loopback address.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :8443'
# Watch the server's wire while you test from outside (a phone on mobile data, a cloud VM):
sudo tcpdump -tni ens18 'tcp port 8443' -c 4
```

```text
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511        127.0.0.1:8443      0.0.0.0:*     users:(("node",pid=2213,fd=19))
tcpdump: listening on ens18, link-type EN10MB (Ethernet), snapshot length 262144 bytes
IP 198.51.100.7.51022 > 10.0.1.10.8443: Flags [S], seq 3011762, win 64240
IP 10.0.1.10.8443 > 198.51.100.7.51022: Flags [R.], seq 0, ack 3011763, win 0
```

**What the output tells you:** read tcpdump like a decision tree. No packets at all: the SYN is stopped before the host, so look upstream. A SYN answered with RST (as here): nothing listens on that address, and `ss` confirms the app is bound to 127.0.0.1 only. A SYN with no answer: the host firewall drops it (look for `[UFW BLOCK]`). A SYN-ACK that leaves but the client still times out: the reply takes a different path (entry 1.4) or an upstream stateful firewall drops it.

**Fix:**

```bash
# Make the app listen on the right address (setting depends on the app: HOST=0.0.0.0, Listen 0.0.0.0:8443, bind_address)
sudo ufw allow proto tcp from any to any port 8443
sudo ss -ltnp 'sport = :8443'          # expect 0.0.0.0:8443 or the LAN address
```

<div class="env" data-env="onprem" markdown="1">

**On-prem upstream gates:** on fw1 (OPNsense), check Firewall > Log Files > Live View filtered on the port while you test, and check that the NAT port forward has its associated filter rule on the WAN interface. Also check for a corporate firewall or a provider that blocks inbound ports (25 and 80 are commonly blocked on business and residential lines), and for double NAT (entry 4.2).

</div>

<div class="env" data-env="cloud" markdown="1">

**AWS upstream gates:** the security group needs an inbound rule for the port; a network ACL, being stateless, also needs the ephemeral return ports (1024–65535) allowed outbound; the subnet's route table needs a route to an internet gateway; and the instance needs a public IP or Elastic IP (or a load balancer in front). VPC Reachability Analyzer traces all of these for one source and destination; VPC Flow Logs show REJECT entries for the port.

</div>

**Why this fix works:** each command opens exactly the gate that tcpdump showed was closed, instead of opening everything and hoping. Don't "test" by disabling UFW or allowing all traffic in a security group: you lose the evidence and risk forgetting to close it again.

**Prevent it:** document every exposed port per host (the ports inventory playbook), add an external probe (blackbox exporter or Uptime Kuma from outside your network) for each public service, and keep admin-only ports on loopback or the VPN.

**Next step:** [Site-down playbook](25-playbook-site-down.md) · [Ports inventory playbook](22-playbook-ports-inventory.md) · [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Start, Stop, and Check Status of Network Services ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · KodeKloud: *AWS Networking Fundamentals* (security groups, routing) · [tcpdump docs](https://www.tcpdump.org/)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=port+open+locally+not+accessible+from+outside) · [Stack Overflow](https://stackoverflow.com/search?q=works+on+localhost+but+not+from+outside+0.0.0.0) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=port+open+locally+closed+externally&restrict_sr=1)

### 3.5 conntrack table full, packets dropped

> **Seen as:** `nf_conntrack: nf_conntrack: table full, dropping packet` in `dmesg`, random connection timeouts under load, new connections failing while established ones keep working · **Where:** busy reverse proxies, DNS resolvers, NAT gateways and VPN servers, Kubernetes nodes, hosts under a SYN or UDP flood · **Level:** [L3 · Senior] · **How common:** a well-known production incident; vendor KB articles from SUSE, NVIDIA, Alibaba and Huawei, and classic blog posts

**Why it happens:** every flow that netfilter tracks (anything touched by NAT or a stateful rule, so every Docker-published or Kubernetes service connection) takes one entry in a fixed-size table. When the table is full, new flows are dropped. Many short-lived connections (DNS over UDP, health checks, connection-per-request HTTP clients) or long default timeouts (established TCP entries live five days by default) fill it far below the real connection count.

**Diagnose:**

```bash
sudo dmesg -T | grep -i conntrack | tail -2
cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max
sudo conntrack -S | head -2
sudo conntrack -L 2>/dev/null | grep -oE 'dport=[0-9]+' | sort | uniq -c | sort -rn | head -4
```

```text
[Sat Oct  4 09:41:12 2026] nf_conntrack: nf_conntrack: table full, dropping packet
[Sat Oct  4 09:41:17 2026] net_ratelimit: 412 callbacks suppressed
262144
262144
cpu=0       found=0 invalid=1204 insert=0 insert_failed=0 drop=48211 early_drop=0 error=3 search_restart=0
cpu=1       found=0 invalid=988 insert=0 insert_failed=0 drop=51077 early_drop=0 error=1 search_restart=0
 198211 dport=53
  41022 dport=443
   9120 dport=5432
   1302 dport=22
```

**What the output tells you:** the table is at its limit and both CPUs count tens of thousands of drops. Three quarters of the entries are DNS flows, so this host is tracking a resolver's UDP traffic it doesn't need to track.

**Fix:**

```bash
# 1. Size the table for the host (each entry costs roughly 300 bytes of kernel memory)
cat <<'CONF' | sudo tee /etc/sysctl.d/70-conntrack.conf
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
CONF
sudo sysctl --system
echo 262144 | sudo tee /sys/module/nf_conntrack/parameters/hashsize   # buckets: about a quarter of the max
# 2. Stop tracking traffic that needs no state (a DNS resolver's own port 53)
sudo nft add table inet raw
sudo nft add chain inet raw pre '{ type filter hook prerouting priority raw; }'
sudo nft add chain inet raw out '{ type filter hook output priority raw; }'
sudo nft add rule inet raw pre udp dport 53 notrack
sudo nft add rule inet raw out udp sport 53 notrack
```

**Why this fix works:** a larger table and buckets give headroom, a shorter established timeout frees entries left by peers that disappeared, and `notrack` removes high-volume stateless traffic from the table entirely. Only use notrack for traffic that needs no NAT and no stateful rule, or replies will be dropped. On Kubernetes nodes set the limit in kube-proxy's configuration (conntrack settings per core), because kube-proxy rewrites the sysctl at start.

**Prevent it:** alert when `node_nf_conntrack_entries / node_nf_conntrack_entries_limit` (node_exporter) passes 80%, size the table in your host baseline, and find the clients that open a new connection per request (connection pooling fixes them at the source).

**Next step:** [Network reference: connection tracking](02-network.md) · [Network speed playbook: contention and limits](24-playbook-network-speed.md) · [Kernel and sysctl](13-kernel-system.md) · [CPU and softirq load](03-cpu-performance.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT · [conntrack-tools manual](https://conntrack-tools.netfilter.org/manual.html)

**Community threads:** [major.io: nf_conntrack table full, dropping packet](https://major.io/p/nf-conntrack-table-full-dropping-packet/) · [SUSE KB 000020149: conntrack table full](https://www.suse.com/support/kb/doc/?id=000020149) · Search: [Server Fault](https://serverfault.com/search?q=%22nf_conntrack%3A+table+full%2C+dropping+packet%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=nf_conntrack+table+full&restrict_sr=1)

## 4. NAT, port forwarding and the edge router

At the edge, an OPNsense or pfSense box (or a Linux router, or the ISP's modem) translates between one public address and your private network. The two classic tickets are mirror images: it works from outside but not from inside, or it should work from outside and nothing arrives.

### 4.1 Works from outside, not from the office LAN

> **Seen as:** www.example.com loads from a phone on mobile data but times out (or shows the firewall's login page) from the office LAN; pfSense shows `Potential DNS Rebind attack detected`; a Traefik or Dokploy app is unreachable by its public name from the same network · **Where:** small offices and homelabs with one public IP and port forwards on OPNsense, pfSense or a consumer router · **Level:** [L1 · Junior] · **How common:** one of the most asked OPNsense forum questions, with its own page in the OPNsense docs

**Why it happens:** a LAN client resolves www.example.com to the public address 203.0.113.10 and sends the request to the firewall. Without hairpin NAT (NAT reflection) the firewall doesn't apply the port forward to traffic coming from the inside, so the request goes to the firewall itself or nowhere. Even with a DNAT, if the source isn't rewritten too, web1 answers the client directly over the LAN, and the client drops a reply that comes from 10.0.1.10 instead of 203.0.113.10. DNS rebind protection (pfSense, OPNsense and Unbound's private-address option) adds a second trap: it removes answers that point a public name at a private address, which breaks a split-horizon setup until the domain is exempted.

**Diagnose:**

```bash
# From a LAN client
dig +short www.example.com
curl -sv -m 5 https://www.example.com -o /dev/null 2>&1 | grep -E 'Trying|Connected|timed out'
# Bypass DNS to prove the server itself is fine from the LAN
curl -s -o /dev/null -w '%{http_code}\n' --resolve www.example.com:443:10.0.1.10 https://www.example.com
```

```text
203.0.113.10
*   Trying 203.0.113.10:443...
* Connection timed out after 5001 milliseconds
200
```

**What the output tells you:** the LAN client gets the public address and can't reach it, but the same request sent straight to 10.0.1.10 works. The server and certificate are fine; only the path through the public address is broken from the inside.

**Fix:**

```text
# Preferred: split-horizon DNS on the LAN resolver (OPNsense: Services > Unbound DNS > Overrides,
# Pi-hole: Local DNS > DNS Records). Plain Unbound equivalent:
server:
    local-zone: "example.com." transparent
    local-data: "www.example.com. 300 IN A 10.0.1.10"
    private-domain: "example.com"          # allow private answers for this domain despite rebind protection
```

```bash
# Alternative on a Linux edge router: hairpin NAT needs both DNAT and SNAT
sudo nft add rule ip nat prerouting iifname "lan0" ip daddr 203.0.113.10 tcp dport { 80, 443 } dnat to 10.0.1.10
sudo nft add rule ip nat postrouting oifname "lan0" ip saddr 10.0.1.0/24 ip daddr 10.0.1.10 tcp dport { 80, 443 } masquerade
```

**Why this fix works:** split-horizon DNS sends LAN clients straight to the server, with no detour through the firewall and with the real client IP in the server logs, and the private-domain line keeps rebind protection on for every other domain. Hairpin NAT works too, but the SNAT makes every LAN request appear to come from the firewall, which hides client IPs from Traefik and from rate limits. In OPNsense, either enable reflection under Firewall > Settings > Advanced or, as its docs now recommend, write the reflection rules by hand so they are visible and auditable. Don't disable rebind protection globally.

**Prevent it:** keep internal overrides for every public name you host in the same change as the public DNS record (a checklist line or the same Terraform or Ansible run), and test new sites from both the LAN and outside.

**Next step:** [Learn networking: NAT](28-learn-networking.md) · [Apache 443 and Dokploy case](21-case-apache-443-dokploy.md) · [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT · [OPNsense docs: Reflection and Hairpin NAT](https://docs.opnsense.org/manual/how-tos/nat_reflection.html)

**Community threads:** [OPNsense forum: NAT Reflection not working](https://forum.opnsense.org/index.php?topic=16783.0) · [OPNsense forum: port forwarding with NAT reflection](https://forum.opnsense.org/index.php?topic=41838.0) · [opnsense/core#5941: reflection rules not created](https://github.com/opnsense/core/issues/5941) · [Netgate docs: DNS rebinding protections](https://docs.netgate.com/pfsense/en/latest/services/dns/rebinding.html) · Search: [Reddit r/opnsense](https://www.reddit.com/r/opnsense/search/?q=nat+reflection+not+working&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=hairpin+nat+split+dns+internal+clients)

### 4.2 Port forward configured, nothing arrives

> **Seen as:** the port forward on the router or OPNsense looks right, but from outside the port times out; a packet capture on the WAN shows nothing during the test; online port checkers say "closed" · **Where:** home and small-office lines, ISP-supplied routers in front of your own firewall, mobile and fibre providers that use carrier-grade NAT · **Level:** [L1 · Junior] · **How common:** extremely common in homelab and small-office threads; growing as ISPs move to CGNAT

**Why it happens:** a port forward only works on the device that owns the public address. With carrier-grade NAT, your WAN address is itself private (100.64.0.0/10) and the ISP's NAT in front of you never forwards anything inbound. With double NAT, the ISP's router holds the public address and your firewall sits behind it. Other causes are closer to home: the forward points at an old internal IP, the forward has no matching WAN filter rule, the service listens only on 127.0.0.1, the server's default route doesn't go through the device that did the DNAT, or you are testing from inside (entry 4.1).

**Diagnose:**

```bash
# On fw1 (OPNsense shell is FreeBSD): what address does the WAN interface really have?
ifconfig vtnet0 | grep 'inet '
# What address does the internet see? (a DNS-based "what is my IP")
dig +short myip.opendns.com @resolver1.opendns.com
# Does anything arrive while you test from outside?
tcpdump -ni vtnet0 'tcp port 443' -c 3
```

```text
	inet 100.72.14.9 netmask 0xffc00000 broadcast 100.127.255.255
203.0.113.77
tcpdump: listening on vtnet0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
^C
0 packets captured
```

**What the output tells you:** the WAN address is in 100.64.0.0/10 (netmask 0xffc00000 is a /10) and differs from the address the internet sees, so the ISP's carrier-grade NAT sits in front of you. Nothing you configure on fw1 can make inbound connections arrive.

**Fix:**

<div class="env" data-env="onprem" markdown="1">

**On-prem line:** ask the ISP for a public (ideally static) IPv4 address or a business line, or put the ISP router in bridge mode so your firewall owns the public address. If neither is possible, reverse the direction: run a small VPS with a public IP and connect your server out to it over WireGuard (entry 8.2), or use an outbound tunnel service, and publish the service on the VPS. IPv6 often still works inbound behind CGNAT, which is enough for some users but not all.

</div>

<div class="env" data-env="cloud" markdown="1">

**On AWS there is no port forwarding:** an instance is reachable inbound only through a public IP or Elastic IP on its interface, or through a load balancer. A NAT gateway only carries outbound traffic. Open the port in the security group, and put an ALB or NLB in front for anything public.

</div>

```bash
# When you do own the public address: a Linux edge router needs DNAT, a forward rule and IP forwarding
sudo nft add rule ip nat prerouting iifname "wan0" tcp dport 443 dnat to 10.0.1.10:443
sudo nft add rule inet filter forward iifname "wan0" ip daddr 10.0.1.10 tcp dport 443 ct state new accept
sysctl net.ipv4.ip_forward                     # must be 1
```

**Why this fix works:** inbound traffic can only be steered by whoever holds the public address, so the fix is either to become that holder (public IP, bridge mode) or to make the connection outbound from your side (VPS plus tunnel). For your own router, DNAT alone is not enough: the forward chain must accept the translated packet and the server's replies must return through the same router. Don't expose the ISP router's admin page or enable UPnP on a business network to "make it work".

**Prevent it:** check the WAN address against the public address when you take over a site, write down who owns the public IP at each location, and keep an external probe on every forwarded service.

**Next step:** [Learn networking: NAT](28-learn-networking.md) · [Site-down playbook](25-playbook-site-down.md) · [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · [OPNsense docs: NAT](https://docs.opnsense.org/manual/nat.html)

**Community threads:** [OPNsense forum: port forward translation configuration](https://forum.opnsense.org/index.php?topic=41176.0) · Search: [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=port+forward+not+working+cgnat&restrict_sr=1) · [Reddit r/networking](https://www.reddit.com/r/networking/search/?q=double+nat+port+forwarding&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=port+forwarding+not+working+cgnat)

## 5. Let's Encrypt and ACME

The Let's Encrypt community forum is one of the richest problem collections in this whole field, and its most-read help topics are about the same few failures: the CA can't reach your server, reaches the wrong one, hits a limit, or can't see your DNS record. Two facts explain most of them. The CA validates from several network vantage points at once, and HTTP-01 always starts on port 80.

### 5.1 Timeout during connect from the CA

> **Seen as:** `Type: connection` ... `Timeout during connect (likely firewall problem)` from certbot, Traefik, Caddy or acme.sh; a renewal that worked for years suddenly fails; errors that mention "secondary validation" · **Where:** servers behind OPNsense or a home router, hosts with geo-blocking, CrowdSec or Fail2ban, Apache moved off port 80 · **Level:** [L1 · Junior] · **How common:** the most common certbot failure on community.letsencrypt.org, with dozens of threads every year

**Why it happens:** for HTTP-01 the CA connects to port 80 on every address in the name's A and AAAA records, from a primary and several secondary vantage points in different regions, and most of them must succeed. A closed port 80 anywhere on the path (UFW, the edge firewall, a security group, an ISP that blocks inbound 80) gives a timeout. Geo-blocking or IP-reputation lists block some vantage points but not others, which fails only the secondary checks. In 2025 one provider's path MTU problem made validations time out too. And for your own setup: with Traefik on 80 and Apache moved to 81, a certbot on the host can't answer HTTP-01 for Apache, because the CA never connects to port 81.

**Diagnose:**

```bash
# On the server: a test file in the webroot certbot uses
sudo mkdir -p /var/www/letsencrypt/.well-known/acme-challenge
echo ok | sudo tee /var/www/letsencrypt/.well-known/acme-challenge/probe
dig +short A www.example.com ; dig +short AAAA www.example.com
# From OUTSIDE (a cloud VM or a phone hotspot), both address families
curl -4 -sv -m 10 http://www.example.com/.well-known/acme-challenge/probe 2>&1 | tail -3
# On the server while you run: sudo certbot renew --dry-run
sudo tcpdump -ni ens18 'tcp port 80' -c 6
```

```text
Certbot failed to authenticate some domains (authenticator: webroot). The Certificate Authority reported these problems:
  Domain: www.example.com
  Type:   connection
  Detail: 203.0.113.10: Fetching http://www.example.com/.well-known/acme-challenge/k3Jf0QxWv1: Timeout during connect (likely firewall problem)
203.0.113.10
* Connection timed out after 10002 milliseconds
0 packets captured
```

**What the output tells you:** no AAAA record, the outside curl times out, and no packet for port 80 reaches the server: the block is upstream (edge firewall, security group or ISP), not certbot.

**Fix:**

```bash
# Open port 80 to everyone at every gate (host, edge, security group); keep it only for the challenge and the HTTPS redirect
sudo ufw allow 80/tcp
# Fail2ban or CrowdSec banned a validation address? Check, then exempt the challenge path at the proxy, not by IP
sudo cscli decisions list 2>/dev/null | head ; sudo fail2ban-client status 2>/dev/null
# Port 80 can't be opened at all (ISP block, internal-only host): use DNS-01 instead (entry 5.5)
# certbot's Cloudflare plugin is a separate package: sudo apt install python3-certbot-dns-cloudflare
sudo certbot certonly --dns-cloudflare --dns-cloudflare-credentials /root/.secrets/cloudflare.ini -d www.example.com
```

**Why this fix works:** the CA has to reach port 80 from several places on the internet, so the only stable fix is a port 80 that is open to the world and answers the challenge path. Let's Encrypt doesn't publish its validation addresses and changes them, so allowlisting "their IPs" breaks again. When 80 can't be opened, DNS-01 proves control without any inbound connection. In the Traefik and Dokploy setup, let Traefik own ACME for every name it routes, including the legacy Apache vhosts it forwards to port 81 (see the Traefik module).

**Prevent it:** add an external probe for `http://NAME/.well-known/acme-challenge/` returning 404 (reachable) rather than a timeout, run `certbot renew --dry-run` after every firewall change, and alert on certificate age, not on renewal logs.

**Next step:** [Traefik: certificates](43-traefik-and-reverse-proxies.md) · [Apache 443 and Dokploy case](21-case-apache-443-dokploy.md) · [Web, HTTP and TLS reference](18-web-http-tls.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt · [Let's Encrypt docs](https://letsencrypt.org/docs/)

**Community threads:** [LE forum: Certbot Timeout during connect (likely firewall problem)](https://community.letsencrypt.org/t/certbot-timeout-during-connect-likely-firewall-problem/224717) · [LE forum: timeouts from validation servers caused by path MTU](https://community.letsencrypt.org/t/https-connection-failures-timeouts-from-validation-servers/243673) · [LE forum: tried disabling the firewall](https://community.letsencrypt.org/t/timeout-during-connect-likely-firewall-problem-tried-disable-firewall/209408) · Search: [Server Fault](https://serverfault.com/search?q=certbot+%22Timeout+during+connect%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=letsencrypt+timeout+during+connect+firewall&restrict_sr=1)

### 5.2 Challenge answered with 404 or by the wrong server

> **Seen as:** `Type: unauthorized` ... `Invalid response from http://www.example.com/.well-known/acme-challenge/...: 404`, sometimes with an IPv6 address in front of the message; HTML from another site in the error detail · **Where:** webroot setups, apps that route every path, hosts behind Traefik or Dokploy, domains with a forgotten AAAA record · **Level:** [L1 · Junior] · **How common:** very common; the "authenticator: webroot" and "IPv6 returns 404" threads recur every year

**Why it happens:** the CA reached a web server, but not the file certbot wrote. Typical reasons: the `--webroot-path` is not the directory the vhost serves for that path; a rewrite or framework router catches /.well-known/ and returns its own 404; a proxy in front (Traefik, Dokploy, Cloudflare) answers instead of the host; or the name has an AAAA record pointing at an old or different server. Let's Encrypt prefers IPv6 when both records exist and falls back to IPv4 only when the IPv6 connection itself fails, never when IPv6 answers with a 404.

**Diagnose:**

```bash
dig +short A www.example.com ; dig +short AAAA www.example.com
# From outside, the probe file from entry 5.1, once per address family
curl -4 -si http://www.example.com/.well-known/acme-challenge/probe | head -1
curl -6 -si http://www.example.com/.well-known/acme-challenge/probe | head -1
```

```text
  Domain: www.example.com
  Type:   unauthorized
  Detail: 2001:db8:10::99: Invalid response from http://www.example.com/.well-known/acme-challenge/k3Jf0QxWv1: 404
203.0.113.10
2001:db8:10::99
HTTP/1.1 200 OK
HTTP/1.1 404 Not Found
```

**What the output tells you:** IPv4 serves the probe, IPv6 doesn't, and the CA's error names the IPv6 address: the AAAA record points at another machine (the old server), and the CA used it first.

**Fix:**

```bash
# Point the AAAA at the right server, or delete it if the site isn't really served over IPv6, then
sudo certbot renew --dry-run
```

```apache
# Apache: serve the challenge path from one directory for every vhost
Alias /.well-known/acme-challenge/ /var/www/letsencrypt/.well-known/acme-challenge/
<Directory "/var/www/letsencrypt/.well-known/acme-challenge/">
    Require all granted
</Directory>
```

```nginx
# nginx: in the port-80 server block, before the redirect to HTTPS
location ^~ /.well-known/acme-challenge/ {
    root /var/www/letsencrypt;
    default_type text/plain;
}
location / { return 301 https://$host$request_uri; }
```

**Why this fix works:** a correct AAAA (or none) makes every vantage point land on the server that holds the token, and one shared challenge directory outside the application keeps routers and rewrites out of the way. There is no option to make Let's Encrypt prefer IPv4; the DNS has to be right. If Traefik answers port 80, a certbot on the host never sees the request: issue the certificate in Traefik instead.

**Prevent it:** audit A and AAAA records together whenever a site moves, include `curl -6` in post-migration checks, and use a shared ACME directory or the proxy's own ACME support rather than per-app webroots.

**Next step:** [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) · IPv6 surprises (section 10 of this module) · [Learn web servers and proxies](29-learn-webservers-proxies.md) · KodeKloud: *DevOps Pre-Requisite Course* — Web Server: Apache Web Server ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · [Let's Encrypt docs: IPv6 support](https://letsencrypt.org/docs/ipv6-support/)

**Community threads:** [LE forum: IPv6 address returns 404, IPv4 is good](https://community.letsencrypt.org/t/ipv6-address-returns-404-ipv4-is-good-but-failed-to-verify-the-domain/36203) · [LE forum: certbot failed to authenticate (webroot)](https://community.letsencrypt.org/t/certbot-failed-to-authenticate-some-domains-authenticator-webroot/246763) · [LE forum: nginx config for the challenge on all vhosts](https://community.letsencrypt.org/t/how-to-nginx-configuration-to-enable-acme-challenge-support-on-all-http-virtual-hosts/5622) · Search: [Stack Overflow](https://stackoverflow.com/search?q=certbot+%22Invalid+response%22+acme-challenge+404) · [Reddit r/letsencrypt](https://www.reddit.com/r/letsencrypt/search/?q=404+acme-challenge&restrict_sr=1)

### 5.3 Renewal fails, or succeeds and nothing changes

> **Seen as:** `Could not bind TCP port 80 because it is already in use by another process on this system (such as a web server)` in the renewal log; a certificate that expires although `certbot renew` "ran"; a renewed file on disk while browsers still get the old certificate · **Where:** certbot installed from snap or apt on hosts with nginx, Apache or HAProxy; containers that mount a single certificate file · **Level:** [L1 · Junior] · **How common:** very common; "Could not bind" alone has many forum threads and GitHub issues in projects that wrap certbot

**Why it happens:** certbot renews with the authenticator recorded at first issue. A certificate first obtained with `--standalone` (while the web server was stopped) tries to bind port 80 again at every renewal and fails once nginx or Apache is running. Renewal also fails silently when the timer is disabled or the disk is full. When renewal works, the running service keeps the old certificate in memory until it reloads, and a container that bind-mounted only the old file keeps seeing that file, because certbot swaps symlinks under /etc/letsencrypt/live. Since 2025 Let's Encrypt no longer sends expiry warning emails, so nobody notices.

**Diagnose:**

```bash
sudo certbot certificates
sudo grep -E 'authenticator|webroot' /etc/letsencrypt/renewal/www.example.com.conf
systemctl list-timers --all | grep -i certbot
sudo journalctl -u snap.certbot.renew.service --since '-3 days' | grep -iE 'could not bind|error' | tail -2
# What clients really get (run from outside too)
echo | openssl s_client -connect www.example.com:443 -servername www.example.com 2>/dev/null | openssl x509 -noout -enddate
```

```text
  Certificate Name: www.example.com
    Domains: www.example.com
    Expiry Date: 2026-10-11 08:14:03+00:00 (VALID: 6 days)
authenticator = standalone
Sun 2026-10-05 03:21:00 UTC 17h left Sat 2026-10-04 09:11:00 UTC 47min ago snap.certbot.renew.timer snap.certbot.renew.service
Could not bind TCP port 80 because it is already in use by another process on this system (such as a web server). Please stop the program in question and then try again.
notAfter=Oct 11 08:14:03 2026 GMT
```

**What the output tells you:** the timer runs, but every renewal uses the standalone authenticator and loses the fight for port 80 against the running web server. Six days are left.

**Fix:**

```bash
# Switch the stored renewal method to webroot (reconfigure test-renews against staging before saving)
sudo certbot reconfigure --cert-name www.example.com --webroot --webroot-path /var/www/letsencrypt
# Reload the service after every successful renewal
cat <<'HOOK' | sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-web.sh
#!/bin/sh
systemctl reload nginx
HOOK
sudo chmod 755 /etc/letsencrypt/renewal-hooks/deploy/reload-web.sh
sudo certbot renew --dry-run
```

**Why this fix works:** webroot (or the nginx and apache plugins) answers the challenge through the running server, so nothing has to stop or bind port 80, and the deploy hook runs only when a certificate really changed, so the new one gets loaded. For containers, mount the whole /etc/letsencrypt directory read-only (not single files), or let the proxy manage ACME itself. Don't schedule a `systemctl stop nginx` around renewals: it trades a certificate outage for a site outage.

**Prevent it:** monitor expiry from outside (blackbox exporter `probe_ssl_earliest_cert_expiry`, Uptime Kuma or a small script) with an alert when less than a third of the lifetime is left. Lifetimes are shrinking (64 days in 2027, 45 days in 2028), so a monthly manual check stops being enough; use clients that support ACME Renewal Information where you can.

**Next step:** [Web, HTTP and TLS reference: openssl](18-web-http-tls.md) · [Services and systemd timers](07-services-systemd.md) · [Disk full](01-storage-disk.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands: Work With SSL Certificates ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · [Certbot user guide](https://eff-certbot.readthedocs.io/en/stable/using.html)

**Community threads:** [LE forum: Could not bind TCP port 80](https://community.letsencrypt.org/t/could-not-bind-tcp-port-80-because-it-is-already-in-use/222758) · [LE forum: an expiry monitor for those missing the old emails](https://community.letsencrypt.org/t/built-a-rust-based-monitor-for-those-missing-the-old-expiration-emails/244532) · [LE forum: some domains suddenly failing renewal](https://community.letsencrypt.org/t/some-domains-suddenly-failing-renewal-or-new-cert-issue/245797) · Search: [Server Fault](https://serverfault.com/search?q=certbot+renew+%22Could+not+bind+TCP+port+80%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=certbot+renewal+deploy+hook+reload&restrict_sr=1)

### 5.4 Rate limited, or CAA forbids issuance

> **Seen as:** `urn:ietf:params:acme:error:rateLimited :: too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s, retry after 2026-10-06 14:02:11 UTC`; `too many failed authorizations (5) for "www.example.com" in the last 1h0m0s`; `CAA record for example.com prevents issuance` · **Where:** Traefik or Caddy containers that lose their ACME storage on redeploy, CI pipelines that create preview environments, scripts that retry in a loop · **Level:** [L2 · Mid] · **How common:** common in container setups; the rate-limit page is one of the most linked documents on the LE forum

**Why it happens:** Let's Encrypt limits issuance per account, per registered domain and per exact set of names. The usual trigger in Docker is an ACME store that doesn't survive a redeploy (acme.json not on a volume, or a new container each deploy), so every start asks for a brand-new certificate for the same names: five times and the week is used up. Failed validations count separately (five per name per account per hour), so a retry loop against a broken challenge locks you out quickly. A CAA record that names another CA, or restricts validation methods, makes the CA refuse outright.

**Diagnose:**

```bash
docker logs traefik 2>&1 | grep -iE 'rateLimited|CAA' | tail -2
docker inspect traefik --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
dig +short CAA example.com
```

```text
2026-10-04T09:12:01Z ERR Unable to obtain ACME certificate for domains error="unable to generate a certificate for the domains [www.example.com]: acme: error: 429 :: POST :: https://acme-v02.api.letsencrypt.org/acme/new-order :: urn:ietf:params:acme:error:rateLimited :: too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s, retry after 2026-10-06 14:02:11 UTC" ACME CA=https://acme-v02.api.letsencrypt.org/directory domains=["www.example.com"] providerName=le.acme
/var/run/docker.sock -> /var/run/docker.sock
0 issue "sectigo.com"
```

**What the output tells you:** Traefik has no volume for its ACME storage, so each recreate re-issued the certificate until the limit hit; separately, the CAA record allows only another CA, so even a fresh week would fail for the apex domain.

**Fix:**

```yaml
# Persist the ACME store and test against staging first
services:
  traefik:
    image: traefik:v3
    command:
      - --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json
      - --certificatesresolvers.le.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory   # remove after a clean test
    volumes:
      - letsencrypt:/letsencrypt
volumes:
  letsencrypt:
```

```text
; DNS: allow Let's Encrypt (keep other CAs you really use)
example.com.  3600  IN  CAA  0 issue "letsencrypt.org"
example.com.  3600  IN  CAA  0 issue "sectigo.com"
```

**Why this fix works:** a persistent store means a redeploy reuses the existing certificate and account, and staging has much higher limits, so mistakes there cost nothing. The limit itself has to expire (the error tells you when), and renewals of an existing certificate are treated more generously than new orders. For certbot, `--test-cert` (or `--dry-run`) is the staging switch. Don't create new ACME accounts to dodge the limit: the exact-set and registered-domain limits are global.

**Prevent it:** put the ACME store on a backed-up volume, make CI preview environments share a wildcard certificate (DNS-01) instead of issuing per run, add jitter and backoff to retry logic, and review CAA whenever you add or drop a CA.

**Next step:** [Traefik: certificates](43-traefik-and-reverse-proxies.md) · [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt · [Let's Encrypt docs: rate limits](https://letsencrypt.org/docs/rate-limits/)

**Community threads:** [Let's Encrypt docs: rate limits](https://letsencrypt.org/docs/rate-limits/) · [LE forum: ACME-CAA validationmethods support](https://community.letsencrypt.org/t/acme-caa-validationmethods-support/63125) · Search: [Stack Overflow](https://stackoverflow.com/search?q=letsencrypt+%22too+many+certificates%22+traefik+acme.json) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=rate+limit+acme.json&restrict_sr=1)

### 5.5 DNS-01: TXT record not found

> **Seen as:** `DNS problem: NXDOMAIN looking up TXT for _acme-challenge.example.com - check that a DNS record exists for this domain`; `Incorrect TXT record ... found at _acme-challenge.example.com`; `DNS problem: SERVFAIL looking up TXT ... the domain's nameservers may be malfunctioning` from secondary validation · **Where:** wildcard certificates, internal-only hosts, Traefik, certbot and acme.sh with Cloudflare, Hetzner, Route 53 or self-hosted BIND · **Level:** [L2 · Mid] · **How common:** very common; the forum's NXDOMAIN-TXT threads have tens of thousands of views, and the DNS-providers topic is among its most viewed of all time

**Why it happens:** the client creates the TXT record and asks the CA to check, but the CA's resolvers ask your authoritative servers directly, and not all of them have it yet: a secondary that lags behind the primary, a provider API that returns before its edge is updated, or a client that checks propagation through an internal resolver that has its own copy of the zone. If anything queried the name before the record existed, resolvers may cache the NXDOMAIN for up to the SOA's negative TTL (often 300 to 3600 seconds). A wildcard plus the apex needs two TXT values at the same name at once, and some plugins overwrite the first. A nameserver that rate-limits bursts can fail the secondary vantage points only.

**Diagnose:**

```bash
dig +short NS example.com
for ns in $(dig +short NS example.com); do echo "$ns: $(dig +short +norecurse TXT _acme-challenge.example.com @$ns)"; done
dig +short SOA example.com          # the last field is the negative-caching TTL
dig +short CNAME _acme-challenge.example.com
```

```text
ns1.example.net.
ns2.example.net.
ns1.example.net.: "gF3k1x9Qm2vV0rT7yHcW4bP8sLzA6nEuJqD5oR1iKtY"
ns2.example.net.:
ns1.example.net. hostmaster.example.com. 2026100402 7200 3600 1209600 3600
```

**What the output tells you:** ns1 has the record, ns2 doesn't yet (a stale secondary, entry 7.2), and negative answers may be cached for an hour, so a quick retry will keep failing even after ns2 catches up.

**Fix:**

```bash
# Give propagation time before the CA checks (certbot DNS plugins)
# certbot's Cloudflare plugin is a separate package: sudo apt install python3-certbot-dns-cloudflare
sudo certbot certonly --dns-cloudflare --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 60 -d example.com -d '*.example.com'
```

```text
; Delegate only the challenge name to a zone your ACME client may edit (acme-dns or a small sub-zone)
_acme-challenge.example.com.  300  IN  CNAME  d420c923-bbd7-4056-ab64-c3ca54c9b3cf.acme.example.net.
```

**Why this fix works:** waiting until every authoritative server answers (and not querying the name before it exists) avoids both the lagging secondary and the cached NXDOMAIN. A CNAME delegation lets the ACME client hold an API key for one throwaway zone instead of your whole DNS, and the CA follows the CNAME. Point the client's propagation check at public resolvers when you run split-horizon DNS internally. For Traefik's DNS-01 settings and provider quirks, see the Traefik module. Don't use a DNS API token with rights to every zone in the account.

**Prevent it:** keep secondaries in sync with NOTIFY (entry 7.2), monitor them for serial drift, give ACME clients least-privilege tokens or a delegated zone, and keep the SOA negative TTL modest (300 to 900 seconds).

**Next step:** [Traefik: DNS-01 and wildcard certificates](43-traefik-and-reverse-proxies.md) · [DNS reference: dig](08-dns.md) · KodeKloud: *Demystifying DNS* — DNS as a System: Time to Live (TTL) ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/DNS-as-a-System/Time-to-Live-TTL/page)) · [Certbot user guide](https://eff-certbot.readthedocs.io/en/stable/using.html)

**Community threads:** [LE forum: NXDOMAIN looking up TXT for _acme-challenge (solved)](https://community.letsencrypt.org/t/solved-dns-problem-nxdomain-looking-up-txt-for-acme-challenge/70102) · [LE forum: secondary SERVFAIL running certbot](https://community.letsencrypt.org/t/secondary-servfail-dns-error-running-certbot/244512) · [LE forum: DNS providers that integrate with DNS validation](https://community.letsencrypt.org/t/dns-providers-who-easily-integrate-with-lets-encrypt-dns-validation/86438) · [Lego, ACME DNS-01 and negatively cached surprises](https://chameth.com/lego-acme-dns-01-surprises/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22NXDOMAIN+looking+up+TXT%22+_acme-challenge) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dns+challenge+NXDOMAIN+TXT&restrict_sr=1)

## 6. Certificate chains and private CAs

A TLS client trusts a server when it can build a path from the server's certificate, through the intermediates the server sends, to a root in its own trust store, and when the name and dates match. Each entry below is one broken link in that path. "It works in my browser" proves little, because browsers fill gaps that curl, Java, Python, Go and Docker don't.

### 6.1 Server sends only its own certificate

> **Seen as:** `curl: (60) SSL certificate problem: unable to get local issuer certificate`, Node's `unable to verify the first certificate`, Java's `PKIX path building failed`, Android apps failing, while desktop browsers show a padlock · **Where:** nginx, Apache, HAProxy, Postfix and Java servers configured by hand; appliances where you upload certificates · **Level:** [L1 · Junior] · **How common:** a perennial LE forum topic ("you may need to install an intermediate chain certificate"), plus a 2026 thread about fullchain files missing intermediates

**Why it happens:** the server was pointed at cert.pem (the leaf only) instead of fullchain.pem, or a chain file was built by hand from an old intermediate. Browsers hide the mistake because they cache intermediates from other sites or fetch them from the address in the certificate (AIA); most other clients only use what the server sends, so the path stops at the leaf.

**Diagnose:**

```bash
openssl s_client -connect www.example.com:443 -servername www.example.com -showcerts </dev/null 2>/dev/null | grep -E '^ *[0-9] s:|^ +i:'
curl -sS https://www.example.com -o /dev/null
grep -rn 'ssl_certificate ' /etc/nginx/sites-enabled/
```

```text
 0 s:CN=www.example.com
   i:C=US, O=Let's Encrypt, CN=R11
curl: (60) SSL certificate problem: unable to get local issuer certificate
/etc/nginx/sites-enabled/www.example.com:14:    ssl_certificate     /etc/letsencrypt/live/www.example.com/cert.pem;
```

**What the output tells you:** the server sends one certificate (depth 0) whose issuer, the R11 intermediate, is never sent; nginx is configured with cert.pem.

**Fix:**

```bash
# nginx: the leaf followed by the intermediates
sudo sed -i 's#live/www.example.com/cert.pem#live/www.example.com/fullchain.pem#' /etc/nginx/sites-enabled/www.example.com
sudo nginx -t && sudo systemctl reload nginx
# Apache 2.4.8+: SSLCertificateFile /etc/letsencrypt/live/www.example.com/fullchain.pem
# HAProxy wants one file: chain plus key
sudo sh -c 'cat /etc/letsencrypt/live/www.example.com/fullchain.pem /etc/letsencrypt/live/www.example.com/privkey.pem > /etc/haproxy/certs/www.example.com.pem'
# Verify like a strict client would
openssl s_client -connect www.example.com:443 -servername www.example.com -verify_return_error </dev/null 2>&1 | grep 'Verify return code'
```

**Why this fix works:** fullchain.pem holds the leaf first and then every intermediate the CA says to send, so any client with the root in its store can complete the path. Order matters (leaf first); the root itself doesn't need to be sent. Don't fix it on the client side by adding the intermediate to each client's trust store: the next client breaks again.

**Prevent it:** always configure the full chain, add `-verify_return_error` checks (or the blackbox exporter's TLS probe) to monitoring, and test new endpoints with curl, not only a browser.

**Next step:** [Web, HTTP and TLS reference: openssl](18-web-http-tls.md) · [Learn networking: TLS and certificates](28-learn-networking.md) · KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)) · [Let's Encrypt docs](https://letsencrypt.org/docs/)

**Community threads:** [LE forum: certificate not trusted, install an intermediate chain](https://community.letsencrypt.org/t/the-certificate-is-not-trusted-in-all-web-browsers-you-may-need-to-install-an-intermediate-chain-certificate-to-link-it-to-a-trusted-root-certificate/242371) · [LE forum: certbot fullchain missing intermediates](https://community.letsencrypt.org/t/certbot-fullchain-missing-intermediates/247897) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22unable+to+get+local+issuer+certificate%22+nginx+fullchain) · [Server Fault](https://serverfault.com/search?q=intermediate+certificate+missing+works+in+browser+not+curl)

### 6.2 Let's Encrypt in 2026: new chain, no client auth

> **Seen as:** after a renewal in mid-2026, some clients report `unable to get local issuer certificate` (new distributions such as Debian 13, Ubuntu 26.04 and Fedora 44 included), strongSwan IKEv2 peers or Android apps reject the chain, SSL checkers flag the chain on pfSense; separately, mutual-TLS or server-to-server connections that used a Let's Encrypt certificate as a client certificate fail with `unsupported certificate purpose` · **Where:** anything that pins, rebuilds or truncates chains (appliances, VPN gateways, the pfSense ACME package), and setups that use public certificates for client authentication · **Level:** [L3 · Senior] · **How common:** the hottest topics of the past year on the LE forum: Gen Y chain validation, YR2 chain issues, pfSense invalid chains, strongSwan failures and the client EKU sunset

**Why it happens:** Let's Encrypt moved its default profile to the "Generation Y" hierarchy on 13 May 2026. New leaf certificates come from Gen Y intermediates whose roots (ISRG Root YE and YR) are cross-signed by the older ISRG roots, because the new roots are not yet in the Mozilla and OS trust stores. A client can only validate if the server sends the full chain including those cross-signs; servers or appliances that send a shortened chain (a hand-made chain file, an ACME client writing an incomplete fullchain) fail on strict clients. Second change: the default profile stopped including the TLS Client Authentication usage in February 2026, and support for it ended completely in mid-2026, so certificates used as client certificates stop working at their next renewal. Lifetimes are shrinking too (45-day certificates opt-in now, 64 days by default in 2027, 45 in 2028).

**Diagnose:**

```bash
# How many certificates does the server send, and how many are in the current fullchain?
openssl s_client -connect www.example.com:443 -servername www.example.com -showcerts </dev/null 2>/dev/null | grep -cE '^ *[0-9] s:'
grep -c 'BEGIN CERTIFICATE' /etc/letsencrypt/live/www.example.com/fullchain.pem
# Which hierarchy and which key usages does the leaf have?
openssl x509 -in /etc/letsencrypt/live/www.example.com/cert.pem -noout -issuer -ext extendedKeyUsage
```

```text
2
3
issuer=C=US, O=Let's Encrypt, CN=YR2
X509v3 Extended Key Usage:
    TLS Web Server Authentication
```

**What the output tells you:** the leaf is from a Gen Y intermediate, the current fullchain holds three certificates (leaf, intermediate, cross-signed root; an ECDSA chain can be one longer), but the server sends only two, so clients that don't yet trust Root YR can't reach a root they know. The leaf has only server authentication, so it can no longer serve as a client certificate.

**Fix:**

```bash
# Serve the fullchain exactly as the CA delivered it, from the live path (no copies, no hand-built chains)
sudo grep -rn 'chain\|ssl_certificate\|SSLCertificate' /etc/nginx /etc/apache2 /etc/haproxy 2>/dev/null | grep -v '#'
# acme.sh-based appliances: build the served chain from the leaf plus the full ca.cer the client saved
cat www.example.com.cer ca.cer > fullchain-served.pem
# Clients: keep trust stores current
sudo apt update && sudo apt install --only-upgrade ca-certificates
```

**Why this fix works:** the cross-signed certificates in the CA-provided chain bridge the new roots to the old roots that every trust store already has, so serving the complete chain makes old and new clients validate. For client authentication, a public CA is the wrong tool now; issue client certificates from your own CA (step-ca, Vault or OpenBao PKI, entry 6.3), where you control the usages and lifetimes. Don't pin intermediates or roots in apps or VPN configs; pin your own CA if you must pin.

**Prevent it:** read the CA's announcements (the LE forum's API Announcements category) and test on its staging environment before default changes land; keep chain-length and verification checks in monitoring; inventory every place a public certificate is used for client auth.

**Next step:** [Learn networking: TLS and certificates](28-learn-networking.md) · [Security & DevSecOps: TLS and PKI](37-learn-security-devsecops.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: TLS Basics ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) · [Let's Encrypt docs](https://letsencrypt.org/docs/)

**Community threads:** [LE forum: upcoming changes to Let's Encrypt certificates](https://community.letsencrypt.org/t/upcoming-changes-to-let-s-encrypt-certificates/243873) · [LE forum: chain validation issues with YE/YR under Linux distributions](https://community.letsencrypt.org/t/chain-validation-issues-with-ye-yr-under-linux-distributions/247836) · [LE forum: pfSense invalid chains after Y generation](https://community.letsencrypt.org/t/pfsense-invalid-chains-after-y-generation-cert/247667) · [LE forum: strongSwan fails with the YR2 chain](https://community.letsencrypt.org/t/ikev2-strongswan-fails-with-lets-encrypt-yr2-chain-works-with-other-servers-chain-mismatch-suspected/247614) · [LE forum: ending TLS client authentication support](https://community.letsencrypt.org/t/ending-tls-client-authentication-certificate-support-in-2026/237403) · Search: [Server Fault](https://serverfault.com/search?q=letsencrypt+2026+chain+YR2+unable+to+get+local+issuer) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=lets+encrypt+client+authentication+EKU&restrict_sr=1)

### 6.3 Private CA: certificate signed by unknown authority

> **Seen as:** `x509: certificate signed by unknown authority` on `docker login` or `docker pull harbor.example.com/...`; `failed to pull image ... tls: failed to verify certificate` in Kubernetes events; `server certificate verification failed. CAfile: none CRLfile: none` from git; `CERTIFICATE_VERIFY_FAILED` from Python, `SELF_SIGNED_CERT_IN_CHAIN` from Node, `PKIX path building failed` from Java · **Where:** Harbor, GitLab, Nexus, Vault, Wazuh and internal APIs signed by a company or homelab CA; GitLab runners and docker:dind jobs · **Level:** [L2 · Mid] · **How common:** among the most common errors for anyone with a private registry; countless Stack Overflow questions and GitLab and Harbor forum threads

**Why it happens:** there is no single trust store. Ubuntu's system bundle is used by curl, git and apt; Docker also reads per-registry files in /etc/docker/certs.d; containerd (Kubernetes nodes) reads /etc/containerd/certs.d; Python's requests often uses its own certifi bundle; Node and Java ship their own stores; and every container image has its own copy of whatever its base image includes. Installing the CA in one place fixes exactly the tools that read that place. A second cause: the server doesn't send its intermediate (entry 6.1), so even a correctly installed root doesn't help.

**Diagnose:**

```bash
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com </dev/null 2>/dev/null | grep -E '^ +i:|Verify return code'
ls /usr/local/share/ca-certificates/ /etc/docker/certs.d/ /etc/containerd/certs.d/ 2>&1
docker pull harbor.example.com/library/alpine:3.20
/opt/app/venv/bin/python -c 'import requests; print(requests.certs.where())'   # an app's virtualenv
```

```text
   i:CN=Example Corp Issuing CA 1
Verify return code: 20 (unable to get local issuer certificate)
/usr/local/share/ca-certificates/:
/etc/docker/certs.d/:
ls: cannot access '/etc/containerd/certs.d/': No such file or directory
Error response from daemon: Get "https://harbor.example.com/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
/opt/app/venv/lib/python3.12/site-packages/certifi/cacert.pem
```

**What the output tells you:** the CA isn't installed anywhere on this host, and the Python app in its virtualenv uses its own certifi bundle, so it would still fail after the OS store is fixed.

**Fix:**

```bash
# 1. The OS store (PEM file, .crt extension): curl, git, apt, Go programs
sudo cp example-root-ca.crt /usr/local/share/ca-certificates/example-root-ca.crt
sudo update-ca-certificates
# 2. Docker, per registry
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp example-root-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
# 3. Language runtimes
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/example-root-ca.crt
sudo keytool -importcert -cacerts -storepass changeit -alias example-root-ca -file example-root-ca.crt -noprompt   # Ubuntu's ca-certificates-java also syncs the OS store into Java
```

```toml
# 4. containerd on Kubernetes nodes: /etc/containerd/certs.d/harbor.example.com/hosts.toml
# (config_path = "/etc/containerd/certs.d" must be set in containerd's registry config)
server = "https://harbor.example.com"

[host."https://harbor.example.com"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
```

**Why this fix works:** each command adds the root to the store one family of tools reads, so verification stays on and only your CA is added. For CI, the GitLab runner needs the CA for its own connection (`tls-ca-file` in config.toml), and a docker:dind service needs it in its own /etc/docker/certs.d, because dind is a separate Docker daemon; bake the CA into your CI images instead of copying it per job. Never "fix" this with `insecure-registries`, `curl -k`, `GIT_SSL_NO_VERIFY=true` or `NODE_TLS_REJECT_UNAUTHORIZED=0`: they turn off the very check that protects your registry credentials.

**Prevent it:** distribute the root CA to every host with Ansible, add it to your base container images, document the per-tool locations in a runbook, and consider an ACME-capable internal CA (step-ca) so internal services renew automatically like public ones.

**Next step:** [CI/CD toolbox: Harbor with a private CA](47-cicd-gitlab-jenkins-actions-argocd.md) · [Security & DevSecOps: TLS and PKI](37-learn-security-devsecops.md) · [Learn Docker: registries](30-learn-docker.md) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Registry ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page)) · [containerd docs: registry hosts](https://containerd.io/docs/main/hosts/) · [step-ca docs](https://smallstep.com/docs/step-ca/getting-started/)

**Community threads:** [containerd discussion #11129: configuring certs.d hosts for a private registry](https://github.com/containerd/containerd/discussions/11129) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+login+%22x509%3A+certificate+signed+by+unknown+authority%22+private+registry) · [Server Fault](https://serverfault.com/search?q=update-ca-certificates+python+requests+certifi) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=x509+unknown+authority+runner+harbor&restrict_sr=1)

### 6.4 Name mismatch, missing SAN or a wrong clock

> **Seen as:** `x509: certificate is valid for traefik.default, not www.example.com`; `x509: certificate relies on legacy Common Name field, use SANs instead`; `x509: cannot validate certificate for 10.0.1.30 because it doesn't contain any IP SANs`; `certificate is not yet valid` or `certificate has expired` for a certificate that is fine elsewhere · **Where:** self-signed and private-CA certificates made with old openssl recipes, services reached by IP, proxies serving a default certificate, VMs and firewalls with a wrong clock · **Level:** [L1 · Junior] · **How common:** very common; Go-based tools (Docker, kubectl, Terraform, Harbor clients) made the legacy-CN error famous

**Why it happens:** clients match the name they connected to against the certificate's Subject Alternative Names; the Common Name has been ignored by modern clients for years. A certificate made with only `-subj "/CN=harbor"` has no SANs at all, and one without an IP SAN can't be used when you connect by IP. A proxy that doesn't find a certificate for the requested name (or receives no SNI) serves its default one (Traefik's "TRAEFIK DEFAULT CERT"). Validity is checked against the client's clock, so a VM that booted with a dead RTC, a snapshot restored without NTP, or a firewall at 1970 rejects every valid certificate.

**Diagnose:**

```bash
echo | openssl s_client -connect 10.0.1.30:443 -servername harbor.example.com 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName -dates
date -u ; timedatectl | grep -E 'synchronized|NTP service'
```

```text
subject=CN=harbor
No extensions in certificate
notBefore=Oct  4 08:00:00 2026 GMT
notAfter=Oct  4 08:00:00 2027 GMT
Sat Jan  3 00:04:51 UTC 2026
System clock synchronized: no
              NTP service: inactive
```

**What the output tells you:** two separate problems: the certificate has no SAN extension (CN only, so modern clients refuse it), and this client's clock is nine months behind with NTP off, so even a perfect certificate would be "not yet valid" here.

**Fix:**

```bash
# Issue with SANs for every name and IP clients really use
openssl req -new -newkey rsa:3072 -nodes -keyout harbor.key -out harbor.csr -subj "/CN=harbor.example.com" \
  -addext "subjectAltName=DNS:harbor.example.com,DNS:harbor,IP:10.0.1.30"
# When signing with your own CA (OpenSSL 3), keep the requested extensions
openssl x509 -req -in harbor.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -copy_extensions copyall -out harbor.crt
# Fix the clock
sudo timedatectl set-ntp true && timedatectl timesync-status | head -3
```

**Why this fix works:** SANs are what clients compare, so listing every DNS name and IP makes the match succeed without disabling verification. Signing tools drop extensions from the request unless told to copy them, which is how many "but I added the SAN" certificates lose it. A synchronised clock makes validity checks meaningful again. For a proxy serving its default certificate, the cause is routing (no router or no certificate for that host name), covered in the Traefik module.

**Prevent it:** generate internal certificates from a template or an internal ACME CA, never by hand-typed openssl one-liners; monitor clock sync on every host (`node_timex_sync_status`), including firewalls and hypervisors.

**Next step:** [Time and NTP](12-time-ntp.md) · [Traefik: TRAEFIK DEFAULT CERT](43-traefik-and-reverse-proxies.md) · [Web, HTTP and TLS reference](18-web-http-tls.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands: Work With SSL Certificates · [OpenSSL docs](https://docs.openssl.org/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=%22relies+on+legacy+Common+Name+field%22) · [Stack Overflow (IP SANs)](https://stackoverflow.com/search?q=%22doesn%27t+contain+any+IP+SANs%22) · [Server Fault](https://serverfault.com/search?q=%22certificate+is+not+yet+valid%22+clock) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=self+signed+certificate+SAN+missing&restrict_sr=1)

## 7. Running DNS: BIND, Unbound, Pi-hole, AdGuard

Running your own DNS adds a second set of problems on top of the client side: caches you don't control, zone transfers, DNSSEC validation and devices that ignore your resolver. The rule that helps most: always ask the authoritative servers directly before you believe any cache.

### 7.1 DNS changed, old answers won't go away

> **Seen as:** hours after a change, some users and monitors still reach the old IP; "propagation" checkers show a mix; a brand-new name returns NXDOMAIN for an hour although the record exists · **Where:** migrations, failovers, new subdomains, registrar nameserver changes · **Level:** [L1 · Junior] · **How common:** one of the most common DNS questions anywhere; a staple of r/sysadmin and the LE forum

**Why it happens:** DNS doesn't propagate; caches expire. Every resolver that fetched the old record keeps it for the TTL it had when it was fetched, so a record that carried a TTL of 86400 lives up to a day in caches, whatever you set later. Negative answers are cached too: if anyone asked for a name before it existed, resolvers may keep the NXDOMAIN for up to the zone's SOA negative TTL. A nameserver change at the registrar is governed by the parent zone's TTLs, often two days. Some runtimes add their own cache (the JVM, browsers, nscd).

**Diagnose:**

```bash
dig +short NS example.com
dig +norecurse www.example.com @ns1.example.net | grep -A1 'ANSWER SECTION'     # the truth
dig www.example.com @10.0.1.53 | grep -A1 'ANSWER SECTION'                      # your resolver's cache
dig +short SOA example.com                                                     # last field: negative TTL
```

```text
ns1.example.net.
ns2.example.net.
;; ANSWER SECTION:
www.example.com.	300	IN	A	203.0.113.20
;; ANSWER SECTION:
www.example.com.	71422	IN	A	203.0.113.10
ns1.example.net. hostmaster.example.com. 2026100402 7200 3600 1209600 3600
```

**What the output tells you:** the authoritative answer is already new (203.0.113.20, TTL 300), but the internal resolver cached the old record with a one-day TTL and will serve it for another 71,422 seconds unless you flush it.

**Fix:**

```bash
# Flush what you control
sudo unbound-control flush www.example.com          # Unbound (OPNsense: Services > Unbound DNS > flush the cache)
sudo rndc flushname www.example.com                  # BIND resolver
sudo resolvectl flush-caches                         # each Ubuntu host's stub
# For caches you don't control: keep the old server answering (or proxying to the new one) until the old TTL has passed
```

**Why this fix works:** flushing removes the stale entry where you have access; everywhere else only time helps, so the old endpoint must stay useful until the longest old TTL has expired. The real fix is the process: lower the TTL to 300 at least one old-TTL period before the change, switch, verify against the authoritative servers, then raise it again. Don't create a name and query it in a loop "to see when it appears": that is how negative caching pins the NXDOMAIN.

**Prevent it:** a migration checklist with the TTL step and its lead time, a modest SOA negative TTL (300 to 900 seconds), and checks against authoritative servers (`dig +norecurse @ns1`) rather than public "propagation" sites.

**Next step:** [DNS reference: dig](08-dns.md) · [Learn networking: DNS in depth](28-learn-networking.md) · KodeKloud: *Demystifying DNS* — DNS as a System: Time to Live (TTL) ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/DNS-as-a-System/Time-to-Live-TTL/page)) · [BIND 9 docs](https://bind9.readthedocs.io/)

**Community threads:** [Lego, ACME DNS-01 and negatively cached surprises](https://chameth.com/lego-acme-dns-01-surprises/) · Search: [Server Fault](https://serverfault.com/search?q=dns+change+not+propagated+ttl+cache) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=dns+propagation+ttl+old+ip&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=negative+caching+NXDOMAIN+SOA+minimum)

### 7.2 BIND secondaries serve an old zone

> **Seen as:** ns1 answers the new record, ns2 the old one; the secondary's log says `transfer of 'example.com/IN' from 10.0.1.53#53: failed while receiving responses: REFUSED`; `named-checkzone` or the primary log reports the zone failed to load; a record edited in the file reverts · **Where:** self-hosted BIND 9 primaries and secondaries (Ubuntu's `named` service), internal zones, hidden primaries feeding public secondaries · **Level:** [L2 · Mid] · **How common:** a classic in every BIND course and on Server Fault; stale secondaries also cause the "secondary validation" ACME failures in entry 5.5

**Why it happens:** secondaries only fetch a zone when its SOA serial increases, so editing records without bumping the serial changes the primary only. Transfers fail when the primary doesn't allow them (`allow-transfer`), when TCP port 53 is blocked between the servers (zone transfers use TCP), or when NOTIFY isn't sent, so the secondary waits for its refresh timer. A syntax error stops the primary from loading the new zone at all, and for zones with dynamic updates, BIND keeps changes in a .jnl journal, so a hand edit of the zone file is overwritten.

**Diagnose:**

```bash
for ns in 10.0.1.53 10.0.1.54; do echo "$ns $(dig +short SOA example.com @$ns | awk '{print $3}')"; done
sudo named-checkconf && sudo named-checkzone example.com /etc/bind/db.example.com
sudo journalctl -u named --since '-1h' | grep -iE 'transfer|notify|refused' | tail -3     # run on the secondary
```

```text
10.0.1.53 2026100403
10.0.1.54 2026100401
zone example.com/IN: loaded serial 2026100403
OK
transfer of 'example.com/IN' from 10.0.1.53#53: failed while receiving responses: REFUSED
```

**What the output tells you:** the primary loaded serial 2026100403 cleanly, the secondary is two edits behind, and the primary refuses the transfer, so this is an access-control problem, not a zone-file problem.

**Fix:**

```text
// Primary: /etc/bind/named.conf.local (create the key with: tsig-keygen xfr-key, shared by both servers)
zone "example.com" {
    type primary;
    file "/etc/bind/db.example.com";
    notify yes;
    also-notify { 10.0.1.54; };
    allow-transfer { key "xfr-key"; };
};
// Secondary
zone "example.com" {
    type secondary;
    file "/var/cache/bind/db.example.com";
    primaries { 10.0.1.53 key "xfr-key"; };
};
```

```bash
sudo named-checkconf && sudo rndc reload                  # on both servers
sudo rndc retransfer example.com                          # on the secondary, to pull now
# Dynamic zones: freeze before a manual edit, bump the serial (YYYYMMDDNN), thaw after
sudo rndc freeze example.com ; sudo editor /var/lib/bind/db.example.com ; sudo rndc thaw example.com
```

**Why this fix works:** TSIG-authenticated transfers plus NOTIFY make the secondary fetch every new serial within seconds, and the checks catch syntax errors before a reload. Freezing a dynamic zone writes the journal into the file and stops updates while you edit, so your change isn't lost. Don't `allow-transfer { any; }`: it publishes your whole internal zone to anyone who asks.

**Prevent it:** generate zones from version control (or use a DNS API with Terraform or OctoDNS), check serials across all nameservers in monitoring, and keep TCP 53 open between DNS servers in the firewall policy.

**Next step:** [DNS reference: running BIND or Unbound](08-dns.md) · [Learn networking: DNS in depth](28-learn-networking.md) · KodeKloud: *Demystifying DNS* — Final Project (set up a DNS server) · [BIND 9 docs](https://bind9.readthedocs.io/)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=bind+secondary+not+updating+serial+allow-transfer) · [Server Fault (REFUSED)](https://serverfault.com/search?q=%22failed+while+receiving+responses%3A+REFUSED%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=bind9+slave+zone+transfer+not+working&restrict_sr=1)

### 7.3 SERVFAIL from a validating resolver

> **Seen as:** `status: SERVFAIL` for some names from Unbound, Pi-hole with Unbound, or OPNsense, while public resolvers answer; internal names under a public domain fail; after an OPNsense upgrade or a power cut, everything fails until DNSSEC is switched off · **Where:** resolvers with DNSSEC validation on (Unbound is the default resolver on OPNsense and the recommended upstream for Pi-hole), internal zones such as corp.example.com or home.arpa · **Level:** [L2 · Mid] · **How common:** recurring OPNsense forum threads (DNSSEC BOGUS for a private domain, DNS broken after an upgrade) and Pi-hole and Unbound questions

**Why it happens:** a validating resolver rejects answers it can't prove. Three causes dominate: the clock is wrong (a firewall without RTC battery boots in the past, so every signature looks "not yet valid", and NTP can't resolve its pool names to fix the clock); an internal-only zone lives under a public, signed domain, so the public chain proves the internal name shouldn't exist and the internal answer is "bogus"; or the resolver forwards to an upstream that strips DNSSEC records (some ISP and filtering resolvers).

**Diagnose:**

```bash
dig gitlab.corp.example.com @10.0.1.53 | grep status
dig +cd +short gitlab.corp.example.com @10.0.1.53            # +cd: checking disabled
dig +short DS example.com @1.1.1.1                           # is the public parent signed?
timedatectl | grep synchronized
```

```text
;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 31842
10.0.1.30
2371 13 2 3B9A1C0F5E7D2A64B8C1E0F9D3A6B5C4E2F1A0B9C8D7E6F5A4B3C2D1E0F9A8B7
System clock synchronized: yes
```

**What the output tells you:** with validation off (+cd) the name resolves, so the data is there and validation rejects it; the parent example.com is signed and the clock is fine, so this is the internal-zone-under-a-signed-domain case.

**Fix:**

```text
# unbound.conf (OPNsense: Services > Unbound DNS > Query Forwarding plus the custom options;
# Pi-hole's unbound: /etc/unbound/unbound.conf.d/pi-hole.conf)
server:
    domain-insecure: "corp.example.com"
    private-domain: "corp.example.com"
forward-zone:
    name: "corp.example.com"
    forward-addr: 10.0.1.60
    forward-addr: 10.0.1.61
```

```bash
sudo unbound-checkconf && sudo systemctl reload unbound
sudo unbound-control flush_bogus
# Clock case: give the firewall NTP servers by IP (or local NTP) so it can fix its time before DNSSEC works
```

**Why this fix works:** domain-insecure tells Unbound not to apply the public chain of trust to that internal subtree, so its answers are accepted, while every public name stays validated. private-domain lets those answers contain private addresses despite rebind protection. Fixing time restores validation for everything at once. Don't turn off DNSSEC validation globally: you lose protection for every domain to fix one internal zone.

**Prevent it:** list all internal zones and declare them in the resolver config at build time, monitor clock sync on firewalls, and after resolver upgrades test one signed public name, one internal name and `dig +cd`.

**Next step:** [DNS reference](08-dns.md) · [Time and NTP](12-time-ntp.md) · [Learn networking: DNS in depth](28-learn-networking.md) · KodeKloud: *Demystifying DNS* — DNS as a Protocol (DNSSEC) · [Unbound docs: unbound.conf](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html)

**Community threads:** [OPNsense forum: DNSSEC BOGUS/SERVFAIL for a private domain](https://forum.opnsense.org/index.php?topic=44888.0) · [OPNsense forum: update broke DNS using Unbound with DNSSEC](https://forum.opnsense.org/index.php?topic=44058.0) · [Pi-hole docs: unbound](https://docs.pi-hole.net/guides/dns/unbound/) · Search: [Server Fault](https://serverfault.com/search?q=unbound+servfail+dnssec+internal+domain) · [Reddit r/opnsense](https://www.reddit.com/r/opnsense/search/?q=unbound+servfail+dnssec&restrict_sr=1)

### 7.4 Pi-hole or AdGuard: port 53 busy, clients bypass

> **Seen as:** `failed to bind host port for 0.0.0.0:53:172.20.0.2:53/tcp: address already in use` when starting Pi-hole or AdGuard Home in Docker; ads and blocked domains still resolve on some devices; one busy client gets refused answers · **Where:** Pi-hole or AdGuard Home on Ubuntu (Docker or bare metal), homelab and small-office networks · **Level:** [L1 · Junior] · **How common:** the top Pi-hole Docker question, with a pinned how-to on the Pi-hole forum and a section in its Docker docs

**Why it happens:** systemd-resolved's stub listens on 127.0.0.53:53, and Docker publishing on 0.0.0.0:53 includes the loopback addresses, so the bind fails. Bypass has several sources: the router advertises its own IPv6 DNS server through router advertisements, browsers and phones use DNS over HTTPS or "Private DNS" (DoT on 853), and some devices hard-code public resolvers. Pi-hole's rate limit (1000 queries per minute per client by default) hits clients that forward everything, such as a Docker host or a mail server.

**Diagnose:**

```bash
sudo ss -lunp 'sport = :53'
# From a client: which server answers, over IPv4 and IPv6?
resolvectl status | grep -E 'DNS Servers|Current DNS'
dig +short whoami.akamai.net        # the public address of the resolver that really asked upstream
```

```text
UNCONN 0      0      127.0.0.53%lo:53        0.0.0.0:*    users:(("systemd-resolve",pid=612,fd=13))
UNCONN 0      0         127.0.0.54:53        0.0.0.0:*    users:(("systemd-resolve",pid=612,fd=15))
       DNS Servers: 10.0.1.53 2001:db8:10::1
Current DNS Server: 2001:db8:10::1
203.0.113.10
```

**What the output tells you:** resolved holds port 53 on loopback, which blocks the Docker publish; the client got two DNS servers, Pi-hole and the router's IPv6 address, and it is currently using the router, so filtering is bypassed whenever the client prefers IPv6.

**Fix:**

```yaml
# Option 1: publish Pi-hole only on the LAN address and leave the host's stub alone
services:
  pihole:
    image: pihole/pihole:latest
    ports:
      - "10.0.1.53:53:53/udp"
      - "10.0.1.53:53:53/tcp"
```

```bash
# Option 2: free port 53 entirely (the Pi-hole docs' method), keeping host resolution working
sudo mkdir -p /etc/systemd/resolved.conf.d
printf '[Resolve]\nDNSStubListener=no\n' | sudo tee /etc/systemd/resolved.conf.d/no-stub.conf
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
# Bypass: on OPNsense, set the DNS server in Router Advertisements and DHCPv6 to Pi-hole's address,
# redirect outbound port 53 from the LAN to Pi-hole, and block port 853 except from Pi-hole
```

**Why this fix works:** binding only the LAN address avoids the loopback overlap without touching the host resolver; disabling the stub frees the port while the symlink keeps the host's own lookups working. Handing out only Pi-hole (for IPv4 and IPv6) and redirecting stray port-53 traffic at the firewall closes the common bypasses; DoH can't be fully blocked by port, so managed devices need browser policy too. Raise or exempt the rate limit for known forwarding clients instead of disabling it.

**Prevent it:** run two resolvers (Pi-hole plus a second instance or plain Unbound) so a container restart doesn't take DNS down for everyone, keep them out of Docker's own DNS path (entry 2.4), and check IPv6 DNS settings whenever router firmware changes.

**Next step:** [DNS reference](08-dns.md) · [Learn Docker: publishing ports](30-learn-docker.md) · [Ports inventory playbook](22-playbook-ports-inventory.md) · KodeKloud: *Demystifying DNS* — Miscellaneous: DNS Monitoring Tools · [Pi-hole docs: Docker tips and tricks](https://docs.pi-hole.net/docker/tips-and-tricks/)

**Community threads:** [Pi-hole forum: what to do if port 53 is already in use](https://discourse.pi-hole.net/t/update-what-to-do-if-port-53-is-already-in-use/52033) · [Pi-hole forum: port 53 taken on Ubuntu (solved)](https://discourse.pi-hole.net/t/pihole-via-docker-ubuntu-port-forwarding-port-53-taken-solved/29973) · Search: [Reddit r/pihole](https://www.reddit.com/r/pihole/search/?q=ipv6+dns+bypass+router+advertisement&restrict_sr=1) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=adguard+home+port+53+already+in+use&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=systemd-resolved+port+53+already+in+use)

## 8. VPNs: WireGuard and OpenVPN

WireGuard is silent by design: it never answers a packet it can't authenticate, so a wrong key and a closed port look exactly alike from the client. OpenVPN is chatty but old configurations meet new defaults. In both, "the tunnel is up" and "traffic flows" are two separate facts to prove.

### 8.1 WireGuard: no handshake

> **Seen as:** the client log repeats `Handshake for peer 1 (203.0.113.10:51820) did not complete after 5 seconds, retrying (try 2)`; `wg show` has no `latest handshake` line and `transfer: 0 B received, 2.89 KiB sent` · **Where:** a WireGuard server (vpn1) behind OPNsense or a home router, on a cloud VM, or in a wg-easy container · **Level:** [L1 · Junior] · **How common:** the most common WireGuard question; many OPNsense, GL.iNet and LowEndTalk threads with exactly this message

**Why it happens:** the handshake needs one UDP packet in and one out. It fails silently when UDP 51820 is blocked anywhere on the way (UFW, the edge firewall, a security group, a missing port forward), when the client's Endpoint is wrong (old IP, old port, a DNS name that changed), when the server isn't listening (the interface didn't come up), when the keys don't match (the server holds a different public key for this client, or the client has the wrong server key), or when a server with several uplinks sends its reply out of the wrong one. A server behind carrier-grade NAT can't receive the first packet at all (entry 4.2).

**Diagnose:**

```bash
sudo wg show wg0
sudo tcpdump -tni any 'udp port 51820' -c 4         # on the server, while the client tries
# Temporary kernel debug messages for WireGuard (needs debugfs); turn off afterwards with -p
echo 'module wireguard +p' | sudo tee /sys/kernel/debug/dynamic_debug/control
sudo dmesg -T | grep wireguard | tail -2
```

```text
interface: wg0
  public key: Fq0rG1xI5u4mC1d0+2vP8sQ7wB3kE9yZ6tL0aN4hJ2s=
  private key: (hidden)
  listening port: 51820

peer: 7mN2pQ9rS1tU3vW5xY7zA9bC1dE3fG5hI7jK9lM1nO0=
  allowed ips: 10.8.0.2/32
ens18 In  IP 198.51.100.7.51413 > 10.0.1.20.51820: UDP, length 148
ens18 In  IP 198.51.100.7.51413 > 10.0.1.20.51820: UDP, length 148
[Sat Oct  4 10:02:11 2026] wireguard: wg0: Invalid handshake initiation from 198.51.100.7:51413
```

**What the output tells you:** the client's 148-byte handshake initiations reach the server, so the network path is fine, but the server can't match them to any peer: the key pair doesn't match. If tcpdump had shown nothing, the packets would be blocked before the server, and the keys would be irrelevant for now.

**Fix:**

```bash
# On the client: the public key that belongs to its private key
sudo wg show wg0 public-key
# On the server: replace the stored peer key with that one, then make it permanent in /etc/wireguard/wg0.conf
sudo wg set wg0 peer CLIENT_PUBLIC_KEY allowed-ips 10.8.0.2/32
sudo wg set wg0 peer 7mN2pQ9rS1tU3vW5xY7zA9bC1dE3fG5hI7jK9lM1nO0= remove
# If no packets arrived instead: open the path
sudo ufw allow 51820/udp            # plus a UDP 51820 port forward to 10.0.1.20 on fw1, or a security group rule
echo 'module wireguard -p' | sudo tee /sys/kernel/debug/dynamic_debug/control
```

**Why this fix works:** WireGuard identifies peers only by public key, so the handshake succeeds the moment both sides hold each other's correct keys and UDP can pass. `PersistentKeepalive = 25` on clients behind NAT keeps their mapping open so the server can reach them when idle. Don't post private keys in tickets or chats when comparing configs; compare public keys only.

**Prevent it:** generate peer configs from one source of truth (an Ansible template, wg-easy, or a mesh VPN from section 9), keep the server's public key and endpoint in your documentation, and alert on handshake age with a WireGuard exporter.

**Next step:** [Learn networking: VPNs, overlays and MTU](28-learn-networking.md) · [Network speed playbook: VPN users are slow](24-playbook-network-speed.md) · KodeKloud: no WireGuard course in the verified map; use *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT for the NAT part · [WireGuard quick start](https://www.wireguard.com/quickstart/) · [Ubuntu docs: WireGuard VPN](https://ubuntu.com/server/docs/explanation/intro-to/wireguard-vpn/)

**Community threads:** [OPNsense forum: handshake did not complete, multi-WAN](https://forum.opnsense.org/index.php?topic=30540.0) · [OPNsense forum: WireGuard no handshake (solved)](https://forum.opnsense.org/index.php?topic=43997.0) · Search: [Reddit r/WireGuard](https://www.reddit.com/r/WireGuard/search/?q=%22did+not+complete+after+5+seconds%22&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=wireguard+handshake+did+not+complete) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=wireguard+no+handshake+port+forward&restrict_sr=1)

### 8.2 WireGuard: handshake fine, no traffic

> **Seen as:** `latest handshake: 12 seconds ago` and bytes counting up in both directions, yet `ping 10.0.1.10` from the client fails, or the client has no internet with a full tunnel; it broke right after Docker was installed on the VPN server; `wg-quick` printing `resolvconf: command not found` · **Where:** a WireGuard server that routes clients into a LAN or to the internet, especially on a host that also runs Docker or UFW · **Level:** [L2 · Mid] · **How common:** very common; "handshake ok but no internet" threads on the OPNsense forum and in wireguard-install discussions, and the Docker docs have a section on exactly this router case

**Why it happens:** after the handshake, the server has to forward the client's packets: IP forwarding must be on, the FORWARD chain must accept wg0 traffic, and either the LAN must know the way back to 10.8.0.0/24 or the server must masquerade the clients behind its own address. Docker sets the FORWARD policy to DROP when it starts, and UFW's default forward policy is DROP, so a working VPN router stops routing the day Docker or UFW arrives. AllowedIPs is both an access list and a routing table: on the server it must contain the client's tunnel address (plus any network behind that client); on the client it decides what goes into the tunnel. A client whose home LAN uses the same subnet as the office can't reach the office range at all.

**Diagnose:**

```bash
sudo wg show wg0 latest-handshakes ; sudo wg show wg0 transfer
sysctl net.ipv4.ip_forward
sudo iptables -S FORWARD | head -3
sudo iptables -t nat -S POSTROUTING | grep -c 10.8.0.0
sudo tcpdump -tni wg0 icmp -c 2        # do the client's pings arrive in the tunnel?
```

```text
7mN2pQ9rS1tU3vW5xY7zA9bC1dE3fG5hI7jK9lM1nO0=	1791101233
7mN2pQ9rS1tU3vW5xY7zA9bC1dE3fG5hI7jK9lM1nO0=	18244	1032
net.ipv4.ip_forward = 1
-P FORWARD DROP
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-FORWARD
0
IP 10.8.0.2 > 10.0.1.10: ICMP echo request, id 7, seq 1, length 64
IP 10.8.0.2 > 10.0.1.10: ICMP echo request, id 7, seq 2, length 64
```

**What the output tells you:** the tunnel works (fresh handshake, pings arrive on wg0), forwarding is on, but the FORWARD policy is DROP (set by Docker) and nothing masquerades 10.8.0.0/24, so the pings die on the server.

**Fix:**

```ini
# /etc/wireguard/wg0.conf on vpn1 (a Docker host): accept wg0 forwarding in DOCKER-USER and masquerade the clients
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = SERVER_PRIVATE_KEY
PostUp = iptables -I DOCKER-USER -i %i -o ens18 -j ACCEPT; iptables -I DOCKER-USER -i ens18 -o %i -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o ens18 -j MASQUERADE
PostDown = iptables -D DOCKER-USER -i %i -o ens18 -j ACCEPT; iptables -D DOCKER-USER -i ens18 -o %i -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT; iptables -t nat -D POSTROUTING -s 10.8.0.0/24 -o ens18 -j MASQUERADE

[Peer]
PublicKey = CLIENT_PUBLIC_KEY
AllowedIPs = 10.8.0.2/32
```

```bash
sudo wg-quick down wg0 && sudo wg-quick up wg0
# Without Docker, with UFW: allow routed traffic instead
sudo ufw route allow in on wg0 out on ens18
# Client side: split tunnel AllowedIPs = 10.8.0.0/24, 10.0.1.0/24 ; full tunnel AllowedIPs = 0.0.0.0/0, ::/0
```

**Why this fix works:** DOCKER-USER is evaluated before Docker's DROP policy, so explicit ACCEPT rules for wg0 restore routing without touching Docker's own rules (Docker's docs recommend exactly this for a Docker host that is also a router; recent releases also offer `"ip-forward-no-drop": true` in daemon.json to leave the policy alone), and masquerading gives replies a path back without changing the LAN. If you prefer to keep client IPs visible in LAN logs, drop the masquerade and add a static route for 10.8.0.0/24 via 10.0.1.20 on fw1 instead. Include ::/0 in a full tunnel, or IPv6 traffic leaks around it (entry 10.4). For the `resolvconf` error, use resolvectl in PostUp (entry 2.3).

**Prevent it:** keep the forwarding and NAT rules in the WireGuard config itself (PostUp and PostDown), not in a one-off command; re-test the VPN after installing Docker or enabling UFW on any router; choose an uncommon office subnet so home LANs don't overlap.

**Next step:** [Learn networking: NAT](28-learn-networking.md) · [Learn networking: VPNs, overlays and MTU](28-learn-networking.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT · [Docker docs: Docker with iptables](https://docs.docker.com/engine/network/firewall-iptables/)

**Community threads:** [OPNsense forum: no internet with a WireGuard road warrior setup](https://forum.opnsense.org/index.php?topic=16847.0) · [wireguard-install discussion #210: handshake OK but no internet](https://github.com/angristan/wireguard-install/discussions/210) · [Linux Containers forum: LXD and Docker FORWARD policy set to drop](https://discuss.linuxcontainers.org/t/lxd-and-docker-firewall-redux-how-to-deal-with-forward-policy-set-to-drop/9953) · Search: [Reddit r/WireGuard](https://www.reddit.com/r/WireGuard/search/?q=handshake+but+no+internet&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=wireguard+handshake+no+traffic+ip_forward+masquerade)

### 8.3 OpenVPN: cipher, TLS and certificate errors

> **Seen as:** `OPTIONS ERROR: failed to negotiate cipher with server.  Add the server's cipher ('BF-CBC') to --data-ciphers`; `TLS Error: TLS key negotiation failed to occur within 60 seconds (check your network connectivity)`; `VERIFY ERROR` or `ca md too weak` after a client upgrade · **Where:** OpenVPN 2.4 servers or appliances meeting OpenVPN 2.6 clients, clients on Ubuntu 22.04 and later (OpenSSL 3), old PKIs built years ago · **Level:** [L2 · Mid] · **How common:** a wave of OpenVPN forum and vendor-forum threads after 2.6, still recurring as old appliances meet new laptops

**Why it happens:** since 2.5, OpenVPN negotiates only modern AEAD data ciphers by default (AES-256-GCM, AES-128-GCM, CHACHA20-POLY1305), the old `cipher` option is just a fallback, and BF-CBC needs OpenSSL 3's legacy provider. OpenSSL 3 also refuses certificates signed with SHA-1 or using 1024-bit keys at its default security level, which hits old CA files. "TLS key negotiation failed" means no TLS conversation happened at all: UDP 1194 is blocked, the client uses the wrong protocol or port, or the tls-auth or tls-crypt key differs, so the server drops every packet.

**Diagnose:**

```bash
# On the 2.6 client (the cipher error is printed by the client, not the server)
sudo journalctl -u openvpn-client@office -n 50 --no-pager | grep -iE 'error|cipher|verify|tls'
# On the server
grep -E '^(cipher|data-ciphers|proto|port|tls-auth|tls-crypt)' /etc/openvpn/server/server.conf
openssl x509 -in /etc/openvpn/server/ca.crt -noout -text | grep -E 'Signature Algorithm|Public-Key' | head -2
```

```text
2026-10-04 10:14:02 OPTIONS ERROR: failed to negotiate cipher with server.  Add the server's cipher ('BF-CBC') to --data-ciphers (currently 'AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305') if you want to connect to this server.
2026-10-04 10:14:02 ERROR: Failed to apply push options
cipher BF-CBC
proto udp
port 1194
        Signature Algorithm: sha1WithRSAEncryption
                Public-Key: (1024 bit)
```

**What the output tells you:** the server still runs a pre-2.5 style config with BF-CBC, and its CA is SHA-1 with a 1024-bit key: the cipher error is the first failure, and the certificate checks are the next one waiting.

**Fix:**

```text
# server.conf: modern negotiation (2.5+ servers); old clients only during a short migration window
data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305
# data-ciphers-fallback AES-256-CBC     # temporary, for clients that can't negotiate
tls-crypt /etc/openvpn/server/tls-crypt.key
```

```bash
# Rebuild the PKI with current defaults (Easy-RSA 3: SHA-256, 2048-bit RSA or EC), then reissue client profiles
./easyrsa init-pki && ./easyrsa build-ca && ./easyrsa build-server-full vpn1 nopass && ./easyrsa build-client-full laptop01 nopass
sudo systemctl restart openvpn-server@server
```

**Why this fix works:** both sides now agree on an AEAD cipher that every 2.5+ client supports, and a SHA-256 PKI passes OpenSSL 3's checks without lowering security levels. Upgrading the server (or appliance) to 2.6 removes the mismatch for good; OpenVPN 2.6 can also use the kernel data channel offload (DCO), and `disable-dco` is the quick way to rule it out if routing behaves oddly after an upgrade. Don't paper over it with `tls-cipher DEFAULT:@SECLEVEL=0` or by re-enabling BF-CBC permanently.

**Prevent it:** track the OpenVPN version of every server and appliance, set an expiry and rotation plan for the VPN PKI, and test new client releases against the server in a lab before rollout. For new deployments, compare WireGuard or a mesh VPN (section 9).

**Next step:** [Learn networking: VPNs](28-learn-networking.md) · [Security & DevSecOps: TLS and PKI](37-learn-security-devsecops.md) · KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics · [OpenVPN 2.6 manual](https://openvpn.net/community-docs/community-articles/openvpn-2-6-manual.html)

**Community threads:** [OpenVPN forum: failed to negotiate cipher with server](https://forums.openvpn.net/viewtopic.php?t=35810) · [OpenVPN forum: connection failed after upgrade to 2.6.0](https://forums.openvpn.net/viewtopic.php?t=35283) · [OpenVPN forum: cipher vs data-ciphers in 2.6](https://forums.openvpn.net/viewtopic.php?t=34936) · [OpenVPN community: cipher negotiation](https://community.openvpn.net/Pages/CipherNegotiation) · Search: [Server Fault](https://serverfault.com/search?q=openvpn+%22TLS+key+negotiation+failed+to+occur+within+60+seconds%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=openvpn+2.6+failed+to+negotiate+cipher&restrict_sr=1)

## 9. Mesh VPNs: Tailscale, Headscale, NetBird

Mesh VPNs build WireGuard tunnels between every pair of devices and use a coordination server to exchange keys. When a direct path can't be punched through NAT, they fall back to a relay, which still works, only slower. Most tickets are about that fallback, about routes into a LAN, and, for the self-hosted control planes, about the reverse proxy in front of them.

### 9.1 Tailscale connects only through a relay

> **Seen as:** `tailscale status` shows `active; relay "fra"` for a peer, transfers crawl at a few Mbit/s, `tailscale ping` always answers `via DERP(fra)` · **Where:** both peers behind restrictive NAT (OPNsense and pfSense outbound NAT, corporate firewalls, mobile networks), servers in clouds with outbound UDP blocked · **Level:** [L2 · Mid] · **How common:** very common; NAT traversal is the main theme of Tailscale's troubleshooting docs and many highly reacted issues (such as excluding interfaces from endpoint advertisement)

**Why it happens:** for a direct path, both peers must learn each other's public address and port and send UDP to it at the same time. Firewalls that randomise the source port per destination ("hard" or endpoint-dependent NAT, which is what OPNsense and pfSense outbound NAT do by default) make the learned port useless to the other peer. If both sides are hard, or UDP is blocked outright, Tailscale keeps traffic on its DERP relays over HTTPS.

**Diagnose:**

```bash
tailscale status | grep web1
tailscale ping web1
tailscale netcheck
```

```text
100.101.102.103 web1                 ops@         linux   active; relay "fra", tx 182340 rx 991204
pong from web1 (100.101.102.103) via DERP(fra) in 48ms
Report:
	* UDP: true
	* IPv4: yes, 203.0.113.10:62044
	* IPv6: no, but OS has support
	* MappingVariesByDestIP: true
	* PortMapping:
	* Nearest DERP: Frankfurt
```

**What the output tells you:** UDP works, but `MappingVariesByDestIP: true` means this side's NAT changes the public port for each destination, and no port-mapping protocol is available, so the other peer can't aim at a stable port: the connection stays relayed.

**Fix:**

```bash
# Give the Tailscale host a fixed UDP port...
grep -E '^PORT|^FLAGS' /etc/default/tailscaled     # Ubuntu packages default to PORT="41641"
# ...and make the firewall keep it: on OPNsense, Firewall > NAT > Outbound (hybrid mode): a rule for source 10.0.1.20,
# protocol UDP, source port 41641, with "Static port" enabled; optionally a UDP 41641 port forward to 10.0.1.20
# Verify: the second or third ping should switch to a direct path
tailscale ping web1
```

**Why this fix works:** a static source port makes this side's NAT "easy", so peers can reach the learned address directly, and a forwarded port makes it reachable even when the other side is hard. In a cloud, allow outbound UDP and, ideally, inbound UDP 41641 in the security group. Newer Tailscale versions can also use peer relays (a node of yours that relays for others), which keeps relayed traffic inside your network. Don't disable the relays: they are the fallback that keeps things working when direct paths fail.

**Prevent it:** document the static-port rule for every site firewall that hosts mesh VPN nodes, and add `tailscale netcheck` to the checks you run on new sites.

**Next step:** [Network speed playbook: VPN users are slow](24-playbook-network-speed.md) · [Learn networking: NAT](28-learn-networking.md) · KodeKloud: no Tailscale course in the verified map; *Networks and Communications* — Network Troubleshooting for the basics · [Tailscale docs: troubleshooting](https://tailscale.com/kb/1023/troubleshooting)

**Community threads:** [tailscale#1552: exclude interfaces from endpoint advertisements](https://github.com/tailscale/tailscale/issues/1552) · [tailscale issues by reactions](https://github.com/tailscale/tailscale/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Reddit r/Tailscale](https://www.reddit.com/r/Tailscale/search/?q=relay+derp+opnsense+static+port&restrict_sr=1) · [Reddit r/opnsense](https://www.reddit.com/r/opnsense/search/?q=tailscale+static+port+outbound+nat&restrict_sr=1)

### 9.2 Subnet router, exit node or 100.64 conflicts

> **Seen as:** a subnet router advertises 10.0.1.0/24 but Linux clients can't reach it; an exit node is selected and the client has no internet; after installing Tailscale on a router whose ISP hands out a 100.64.x.x WAN address, upstream traffic or DHCP renewals break; a laptop on the office LAN sends office traffic through the subnet router anyway · **Where:** Tailscale (and Headscale) subnet routers and exit nodes on Linux, ISPs and clouds that use 100.64.0.0/10 · **Level:** [L2 · Mid] · **How common:** very common; the most-reacted Tailscale issue is about local routes versus subnet routes, and Tailscale has a page dedicated to CGNAT conflicts

**Why it happens:** a route works only when four things line up: the router advertises it, an admin approves it (or an autoApprover policy does), the client accepts routes (on Linux `--accept-routes` is off by default), and the router can forward (IP forwarding on, and no FORWARD DROP from Docker or UFW, entry 8.2). Tailscale uses 100.64.0.0/10 for its addresses and installs a rule that drops traffic from that range arriving on any other interface, which collides with ISPs and clouds that use the same shared address space. Accepted subnet routes also live in a routing table that is consulted before the main table, so a client on the office LAN sends LAN traffic through the tunnel.

**Diagnose:**

```bash
# On the subnet router
sysctl net.ipv4.ip_forward
tailscale debug prefs | grep -A1 AdvertiseRoutes
# On a Linux client
tailscale debug prefs | grep RouteAll
ip route show table 52 | grep 10.0.1.0
# CGNAT conflict: Tailscale's input chain
sudo iptables -S ts-input | grep 100.64
```

```text
net.ipv4.ip_forward = 0
	"AdvertiseRoutes": [
		"10.0.1.0/24"
	"RouteAll": false,
-A ts-input -s 100.64.0.0/10 ! -i tailscale0 -j DROP
```

**What the output tells you:** the router advertises the route but can't forward, and the Linux client doesn't accept routes, so table 52 has no 10.0.1.0/24. The ts-input rule is the one that drops 100.64/10 traffic from a CGNAT ISP on the WAN interface.

**Fix:**

```bash
# Subnet router: forwarding, then advertise (approve in the admin console or with autoApprovers)
printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' | sudo tee /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
sudo tailscale set --advertise-routes=10.0.1.0/24 --advertise-exit-node
# Linux client
sudo tailscale set --accept-routes
sudo tailscale set --exit-node=vpn1 --exit-node-allow-lan-access
# CGNAT conflict: manage the firewall yourself instead of letting tailscaled add its rules (then write your own rules)
sudo tailscale set --netfilter-mode=off
```

**Why this fix works:** forwarding plus an approved, accepted route completes the path, and allow-LAN-access keeps the local network reachable while an exit node carries everything else. For the 100.64 conflict, Tailscale's docs list turning off its netfilter management (and filtering yourself) or moving the tailnet to IPv6-only; with Headscale you also choose the prefix it hands out. For a laptop that moves between office and home, the open issue about local routes has workarounds (disable accept-routes on the office network). Don't advertise 0.0.0.0/0 as a subnet route: use the exit-node feature.

**Prevent it:** use autoApprovers and tags so routes are approved by policy, include `--accept-routes` in your Linux client role, check IP plans for 100.64.0.0/10 before rolling out a mesh VPN, and remember the Docker FORWARD policy on subnet routers.

**Next step:** [Learn networking: Routing](28-learn-networking.md) · [On-prem vs cloud: hybrid](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Port Redirection and NAT · [Tailscale docs: subnet routers](https://tailscale.com/docs/features/subnet-routers)

**Community threads:** [tailscale#1227: bypass the subnet router when a local route exists](https://github.com/tailscale/tailscale/issues/1227) · [Tailscale docs: troubleshoot CGNAT conflicts](https://tailscale.com/docs/reference/troubleshooting/network-configuration/cgnat-conflicts) · [tailscale#18762: DHCP renewals intercepted in CGNAT environments](https://github.com/tailscale/tailscale/issues/18762) · [Headscale docs: routes](https://headscale.net/stable/ref/routes/) · Search: [Reddit r/Tailscale](https://www.reddit.com/r/Tailscale/search/?q=subnet+router+accept-routes+linux&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=tailscale+exit+node+no+internet&restrict_sr=1)

### 9.3 Headscale behind a reverse proxy

> **Seen as:** `tailscale up --login-server https://headscale.example.com` hangs or loops; clients register but never get a direct path or a home relay; everything works when you bypass the proxy · **Where:** self-hosted Headscale behind Traefik (Dokploy), nginx, Caddy or a CDN proxy · **Level:** [L3 · Senior] · **How common:** common enough that Headscale's docs have a page just for reverse proxies and ask you to test without one before opening an issue

**Why it happens:** the Tailscale control protocol upgrades an HTTP POST to a long-lived connection with the header `Upgrade: tailscale-control-protocol`; a proxy that doesn't pass upgrades (or buffers them) breaks registration. CDN proxies such as Cloudflare's orange cloud or Cloudflare Tunnel don't support these POST upgrades at all. `server_url` must be the exact public HTTPS URL, because it is what clients are told to use. The embedded DERP server needs UDP 3478 for STUN reachable directly, which an HTTP proxy can't carry, and gRPC can't be proxied either.

**Diagnose:**

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://headscale.example.com/health
grep -nE '^server_url|^listen_addr|stun_listen_addr|^trusted_proxies' /etc/headscale/config.yaml
dig +short headscale.example.com
sudo ss -lunp 'sport = :3478'
```

```text
200
1:server_url: http://headscale:8080
3:listen_addr: 0.0.0.0:8080
41:    stun_listen_addr: "0.0.0.0:3478"
198.51.100.200
```

**What the output tells you:** the HTTP side is up, but server_url is the internal container address (clients are told to use a URL they can't reach), the name resolves to a CDN proxy address (198.51.100.200) rather than your server, and nothing listens on UDP 3478 on the host because the port isn't published.

**Fix:**

```yaml
# /etc/headscale/config.yaml (excerpt)
server_url: https://headscale.example.com
listen_addr: 0.0.0.0:8080
tls_cert_path: ""
tls_key_path: ""
trusted_proxies: ["10.0.1.0/24"]
```

```yaml
# compose service behind Traefik (Dokploy or plain Compose); DNS record set to DNS-only, not proxied
services:
  headscale:
    image: headscale/headscale:VERSION      # pin the release you tested
    command: serve
    volumes:
      - ./config:/etc/headscale
      - headscale-data:/var/lib/headscale
    ports:
      - "3478:3478/udp"                     # STUN for the embedded DERP, straight to the container
    labels:
      - traefik.enable=true
      - traefik.http.routers.headscale.rule=Host(`headscale.example.com`)
      - traefik.http.routers.headscale.entrypoints=websecure
      - traefik.http.routers.headscale.tls.certresolver=le
      - traefik.http.services.headscale.loadbalancer.server.port=8080
volumes:
  headscale-data:
```

**Why this fix works:** a correct server_url gives clients a reachable URL, a DNS-only record removes the CDN that can't carry the upgrade, Traefik passes connection upgrades without extra configuration (nginx needs the Upgrade and Connection headers set explicitly, as in Headscale's example), and publishing UDP 3478 lets clients discover their public address through your DERP. Keep metrics and gRPC on localhost; they are not meant to go through the proxy. Don't run the control plane without a backup of its database and keys: losing it means re-enrolling every node.

**Prevent it:** follow the Headscale reverse-proxy page for your proxy, keep a test client that logs in after each Headscale or proxy upgrade, and back up /var/lib/headscale.

**Next step:** [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) · [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) · [Headscale docs: reverse proxy](https://headscale.net/stable/ref/integration/reverse-proxy/)

**Community threads:** [Headscale docs: running behind a reverse proxy](https://headscale.net/stable/ref/integration/reverse-proxy/) · [headscale issues by reactions](https://github.com/juanfont/headscale/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · [headscale#3415: macOS and iOS with no exit nodes available](https://github.com/juanfont/headscale/issues/3415) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=headscale+reverse+proxy+traefik&restrict_sr=1) · [Reddit r/Tailscale](https://www.reddit.com/r/Tailscale/search/?q=headscale+cloudflare+proxy&restrict_sr=1)

### 9.4 NetBird peers relayed or resources unreachable

> **Seen as:** `netbird status -d` shows `Connection type: Relayed` and `ICE candidate (Local/Remote): -/-` for peers that should connect directly; a network resource (a LAN behind a routing peer) is unreachable although the peer is connected; peers whose own networks use 100.64.0.0/10 can't reach parts of them · **Where:** NetBird cloud or self-hosted (management, signal, relay and STUN on your server), routing peers on Linux · **Level:** [L2 · Mid] · **How common:** common; NetBird's client troubleshooting guide is built around these checks, and configurable network ranges and MTU were long-requested issues

**Why it happens:** like Tailscale, NetBird uses ICE to find a direct WireGuard path and falls back to a relay when NAT or a firewall blocks UDP or when the self-hosted STUN port (UDP 3478) isn't reachable. A resource behind a routing peer additionally needs IP forwarding on that peer, a network route or resource definition, and an access policy that allows the source group to reach it; a missing policy looks exactly like a routing failure. NetBird's default overlay range is also inside 100.64.0.0/10, which can overlap with CGNAT networks.

**Diagnose:**

```bash
netbird status -d | grep -E 'Management|Signal|Connection type|ICE candidate|Last WireGuard handshake' | head -6
sysctl net.ipv4.ip_forward                                  # on the routing peer
sudo netbird debug trace in 100.92.14.7 self -p tcp --dport 443   # would the local firewall allow it?
sudo netbird debug bundle -A -S                             # anonymised bundle with logs and routes for an issue
```

```text
Management: Connected to https://netbird.example.com:443
Signal: Connected to https://netbird.example.com:443
  Connection type: Relayed
  ICE candidate (Local/Remote): -/-
  Last WireGuard handshake: 41 seconds ago
net.ipv4.ip_forward = 0
```

**What the output tells you:** control-plane connections are fine and the tunnel is alive, but ICE found no usable candidate (both sides blocked from direct UDP), and the routing peer can't forward, so the resource behind it is unreachable regardless of the relay.

**Fix:**

```bash
# Routing peer: forwarding on (and keep Docker's FORWARD policy in mind, entry 8.2)
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-netbird.conf && sudo sysctl --system
# Self-hosted: STUN/relay reachable from the internet
sudo ufw allow 3478/udp
# Dashboard: the network resource exists, has the routing peer assigned (masquerade on unless the LAN has a return route),
# and an access policy allows the client group to reach the resource group
netbird status -d | grep -E 'Connection type'
```

**Why this fix works:** forwarding plus a route plus a policy is the complete path to a resource, and a reachable STUN service lets peers discover their public mapping so ICE can try a direct path. If peers stay relayed, the same NAT advice as entry 9.1 applies (static ports on the edge firewall). Don't delete the client's config file to "reset" unless you also re-enrol it with a fresh setup key; it holds the peer identity.

**Prevent it:** model access with groups and policies from day one, monitor the relayed-versus-P2P ratio, check the overlay range against your IP plan, and use the debug bundle when you open an issue instead of screenshots.

**Next step:** [Learn networking: VPNs, overlays and MTU](28-learn-networking.md) · [Security & DevSecOps: network security](37-learn-security-devsecops.md) · KodeKloud: no NetBird course in the verified map; *Networks and Communications* — Network Troubleshooting · [NetBird docs: client troubleshooting](https://docs.netbird.io/help/troubleshooting-client)

**Community threads:** [netbird#1633: configure the NetBird network range](https://github.com/netbirdio/netbird/issues/1633) · [netbird#743: MTU configuration](https://github.com/netbirdio/netbird/issues/743) · [netbird issues by reactions](https://github.com/netbirdio/netbird/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=netbird+relayed+p2p&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=netbird+routing+peer+not+working&restrict_sr=1)

## 10. MTU and IPv6 surprises

The last two sources of "impossible" network bugs: packets that are too big for some hop on the path and vanish without an error, and a second address family that nobody planned for but that is very much switched on.

### 10.1 Small requests work, large ones hang

> **Seen as:** SSH logs in but `cat` of a large file or `git clone` freezes; `curl` stops after the TLS ClientHello for some sites; pages load half-way; Let's Encrypt validation times out although port 80 is open · **Where:** paths with a smaller MTU somewhere (PPPoE lines, WireGuard, OpenVPN and IPsec tunnels, VXLAN overlays, some provider backbones) plus a firewall that drops ICMP · **Level:** [L3 · Senior] · **How common:** a classic network-engineering puzzle; Cloudflare has written about it several times, and in 2025 it broke Let's Encrypt validations for one country's hosting providers

**Why it happens:** TCP sends the largest segments the local interface allows (1500 bytes on Ethernet). When a hop has a smaller MTU, it drops the big packet and sends back an ICMP "fragmentation needed" (IPv4) or "packet too big" (IPv6) message, and the sender lowers its size. That is path MTU discovery. If any firewall on the way drops those ICMP messages, the sender never learns, keeps retransmitting the big packet, and the connection hangs: a PMTUD black hole. Small packets (keystrokes, a login, a ClientHello) fit, which is why the symptom looks so selective.

**Diagnose:**

```bash
tracepath -n 198.51.100.20
ping -c 2 -M do -s 1472 198.51.100.20       # 1472 bytes + 28 bytes of headers = 1500
ping -c 2 -M do -s 1372 198.51.100.20
sudo tcpdump -ni ens18 'icmp[icmptype] == 3 and icmp[icmpcode] == 4' -c 3
```

```text
 1?: [LOCALHOST]                      pmtu 1500
 1:  10.0.1.1                                              0.512ms
 2:  203.0.113.1                                           1.204ms
 3:  no reply
2 packets transmitted, 0 received, 100% packet loss, time 1012ms
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
^C
0 packets captured
```

**What the output tells you:** full-size packets with "don't fragment" vanish while 1400-byte packets pass, and no "fragmentation needed" message ever arrives: the path MTU is somewhere between 1400 and 1500, and something filters the ICMP that would announce it.

**Fix:**

```bash
# 1. Let PMTUD work: never drop ICMP type 3 (IPv4) or ICMPv6 type 2 at your firewalls
# 2. Clamp TCP MSS on the router or tunnel endpoint so TCP never sends oversized segments
sudo nft add rule inet filter forward tcp flags syn tcp option maxseg size set rt mtu
sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu   # iptables equivalent
# 3. Set tunnel MTUs explicitly (WireGuard: MTU = 1380 in [Interface] over PPPoE), and as a host-side safety net:
echo 'net.ipv4.tcp_mtu_probing = 1' | sudo tee /etc/sysctl.d/60-mtu-probing.conf && sudo sysctl --system
```

<div class="env" data-env="onprem" markdown="1">

**On-prem usual suspects:** PPPoE uplinks (1492), every VPN and IPsec tunnel, VXLAN in Proxmox SDN or between hypervisors (1450), and firewalls with a blanket "block all ICMP" rule. Write the MTU of each link into your network diagram and clamp MSS on every tunnel endpoint.

</div>

<div class="env" data-env="cloud" markdown="1">

**On AWS:** instances use jumbo frames (9001) inside a VPC, but an internet gateway only forwards packets up to 1500 bytes, and VPN and some peering paths are smaller still. PMTUD only works if the security group has an inbound ICMP rule for "Destination Unreachable: fragmentation needed" (and no network ACL denies it); without that rule, large replies to internet clients can black-hole.

</div>

**Why this fix works:** with ICMP allowed, senders learn the real path MTU; MSS clamping makes TCP pick a small enough segment size at connection setup, so it works even across networks you don't control; MTU probing lets the host itself recover when it detects a black hole. Lowering the interface MTU on one server (the 1280 workaround from the Let's Encrypt case) helps that server only. Don't "fix" it by disabling the don't-fragment bit or by blocking ICMP "for security": ICMP errors are part of how IP works.

**Prevent it:** keep ICMP error types in every firewall baseline, clamp MSS on every router and tunnel by default, and include a `ping -M do -s 1472` test in VPN and new-link acceptance checks.

**Next step:** [Network speed playbook: this host's link, TCP and MTU](24-playbook-network-speed.md) · [Learn networking: VPNs, overlays and MTU](28-learn-networking.md) · KodeKloud: *Networks and Communications* — Network Troubleshooting · [AWS docs: network MTU for EC2](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/network_mtu.html)

**Community threads:** [LE forum: timeouts from validation servers caused by path MTU](https://community.letsencrypt.org/t/https-connection-failures-timeouts-from-validation-servers/243673) · [Cloudflare blog: IP fragmentation is broken](https://blog.cloudflare.com/ip-fragmentation-is-broken/) · [Cloudflare blog: ending the silent drop with dynamic PMTUD](https://blog.cloudflare.com/client-dynamic-path-mtu-discovery/) · Search: [Server Fault](https://serverfault.com/search?q=pmtud+black+hole+ssh+hangs+large+output) · [Reddit r/networking](https://www.reddit.com/r/networking/search/?q=mtu+black+hole+mss+clamping&restrict_sr=1)

### 10.2 Containers inside a tunnel or overlay hang

> **Seen as:** in GitLab CI with docker:dind, `docker build` hangs at `RUN apt-get update` or `pip install`, or fails with `TLS handshake timeout`; pods pull fine but their outbound HTTPS calls stall; the same commands work on the host · **Where:** GitLab runners on OpenStack, Proxmox SDN or a VPN; Kubernetes with VXLAN-based CNIs (Flannel, Calico VXLAN) on top of a tunnel; Docker hosts whose uplink MTU is below 1500 · **Level:** [L3 · Senior] · **How common:** a well-known GitLab Runner issue (its docs describe the dind MTU fix) and a recurring CNI support question

**Why it happens:** each layer of encapsulation needs room for its own headers (about 50 bytes for VXLAN, 60 to 80 for WireGuard, more for IPsec), so the usable MTU inside shrinks with every layer. The host's uplink may say 1450, but Docker creates its bridges with 1500, and a docker:dind service starts its own daemon with 1500 regardless of the outer runner's settings. Containers send 1500-byte packets that the uplink can't carry, and if PMTUD is blocked (entry 10.1), the result is a silent hang.

**Diagnose:**

```bash
ip -o link | awk '{print $2, $4, $5}' | grep -E '^(ens|docker0|br-|flannel|vxlan|wg)'   # ip -br link does not show the MTU
docker run --rm alpine ip link show eth0 | grep -o 'mtu [0-9]*'
# Inside a CI job that uses docker:dind
docker network inspect bridge -f '{{index .Options "com.docker.network.driver.mtu"}}'
```

```text
ens3: mtu 1450
docker0: mtu 1500
mtu 1500
1500
```

**What the output tells you:** the VM's uplink carries 1450 bytes, but Docker's bridge, the containers and the dind daemon all use 1500.

**Fix:**

```json
{ "mtu": 1450 }
```

```yaml
# /etc/docker/daemon.json as above for the default bridge; Compose networks need it per network
networks:
  default:
    driver_opts:
      com.docker.network.driver.mtu: "1450"
```

```yaml
# .gitlab-ci.yml: the dind daemon must use an MTU no larger than the runner's
build:
  image: docker:29
  services:
    - name: docker:29-dind
      command: ["--mtu=1400"]
  script:
    - docker build -t harbor.example.com/shop/web:$CI_COMMIT_SHORT_SHA .
```

**Why this fix works:** every inner network now uses a packet size that fits through every outer layer, so no packet depends on PMTUD to get through. On Kubernetes, set the CNI's MTU (for example Calico's veth MTU or Cilium's mtu setting) to the underlay MTU minus the encapsulation overhead; most CNIs detect the host MTU, but only at install time. Don't raise the inner MTU to "match" a jumbo underlay unless every hop really supports it.

**Prevent it:** record the underlay MTU of every environment (cloud, OpenStack, Proxmox SDN, VPN) in the runner and cluster build docs, set Docker's and the CNI's MTU at install, and include a large download in your CI smoke test.

**Next step:** [CI/CD toolbox: GitLab runners and dind](47-cicd-gitlab-jenkins-actions-argocd.md) · [Network speed playbook: containers and Kubernetes](24-playbook-network-speed.md) · [Learn Kubernetes: networking](31-learn-kubernetes.md) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: Prerequisite Docker Networking ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Docker-Networking/page)) · [GitLab docs: Docker executor](https://docs.gitlab.com/runner/executors/docker/)

**Community threads:** [GitLab docs: Docker executor (MTU with docker:dind)](https://docs.gitlab.com/runner/executors/docker/) · [gitlab-runner#6697: job hangs with newer docker:dind](https://gitlab.com/gitlab-org/gitlab-runner/issues/6697) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+dind+mtu+gitlab+hangs+apt-get) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=mtu+vxlan+pods+hang+https&restrict_sr=1)

### 10.3 IPv6 that half works: slow fallbacks

> **Seen as:** `apt update` sits at `Connecting to archive.ubuntu.com (2001:db8:91::17)` for a minute or two per mirror, then continues; `curl` to some sites takes exactly as long as a timeout; `Network is unreachable` errors that mention an IPv6 address · **Where:** servers on networks where a router advertises an IPv6 prefix but the IPv6 path upstream is broken, after an ISP or firewall change, VMs on bridges that pass router advertisements · **Level:** [L1 · Junior] · **How common:** very common; a long-running Server Fault and Ask Ubuntu theme ("apt hangs on IPv6")

**Why it happens:** when a host has a global IPv6 address and a default route learned from router advertisements, programs prefer the AAAA records. Modern browsers and curl race IPv4 and IPv6 ("happy eyeballs") and hide a broken IPv6 path, but apt, many scripts and some runtimes try addresses one by one and wait for a full timeout first. The IPv6 path breaks when the ISP prefix changes, when a firewall allows IPv4 only, or when a router keeps advertising a prefix it can't route.

**Diagnose:**

```bash
ip -6 addr show scope global ; ip -6 route show default
curl -6 -sS -m 5 -o /dev/null -w '%{http_code}\n' https://www.example.com
curl -4 -sS -m 5 -o /dev/null -w '%{http_code}\n' https://www.example.com
getent ahosts archive.ubuntu.com | head -2
```

```text
    inet6 2001:db8:10::10/64 scope global dynamic mngtmpaddr noprefixroute
       valid_lft 86022sec preferred_lft 14022sec
default via fe80::1 dev ens18 proto ra metric 100 expire 1720sec pref medium
curl: (28) Connection timed out after 5002 milliseconds
000
200
2001:db8:91::17 STREAM archive.ubuntu.com
2001:db8:91::17 DGRAM
```

**What the output tells you:** the host has a global address and a default route from router advertisements, IPv6 connections time out, IPv4 works, and the resolver returns the IPv6 address first: every sequential client waits for that timeout.

**Fix:**

```bash
# Real fix: repair IPv6 upstream (router, firewall, ISP prefix), or stop advertising a prefix that can't route.
# If this network has no working IPv6, stop accepting router advertisements on servers (netplan):
#   ethernets: { ens18: { accept-ra: false } }
sudo netplan try
# Workarounds while the network is fixed (remove them afterwards):
echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99force-ipv4
echo 'precedence ::ffff:0:0/96  100' | sudo tee -a /etc/gai.conf      # prefer IPv4 for getaddrinfo callers
```

**Why this fix works:** fixing the path (or not configuring IPv6 where it doesn't work) removes the broken address family, so no client waits for it; the gai.conf precedence line changes the sort order of getaddrinfo so IPv4 addresses come first. Don't disable IPv6 with `disable_ipv6` sysctls across the board: software that binds to ::1 or expects dual-stack sockets breaks in confusing ways, and you lose IPv6 where it does work.

**Prevent it:** treat IPv6 as a production protocol (monitor it with `curl -6` probes like IPv4), and make router-advertisement settings part of the network design rather than a vendor default.

**Next step:** [Learn networking: IPv6 essentials](28-learn-networking.md) · [Slow system playbook](23-playbook-slow-system.md) · [Package management](11-packages.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure IPv4/IPv6 Networking and Hostname Resolution · [netplan docs](https://netplan.readthedocs.io/)

**Community threads:** [LE docs: IPv6 support (why a wrong AAAA also breaks validation)](https://letsencrypt.org/docs/ipv6-support/) · Search: [Server Fault](https://serverfault.com/search?q=apt+update+hangs+ipv6+connecting) · [Stack Overflow](https://stackoverflow.com/search?q=gai.conf+prefer+ipv4+precedence) · [Reddit r/ipv6](https://www.reddit.com/r/ipv6/search/?q=broken+ipv6+slow+fallback&restrict_sr=1)

### 10.4 IPv6 slips past the firewall or the VPN

> **Seen as:** a port closed over IPv4 answers over IPv6 from outside; `ss` shows services on `[::]`; users on a "full tunnel" VPN reach IPv6 sites without going through the tunnel · **Where:** hosts with old UFW defaults, hand-written iptables rules without ip6tables, nftables rules in `table ip` only, WireGuard configs with `0.0.0.0/0` but no `::/0`, networks where IPv6 was switched on by a router update · **Level:** [L2 · Mid] · **How common:** common and dangerous; IPv4 NAT used to hide hosts, and IPv6 gives each of them a reachable global address

**Why it happens:** IPv4 and IPv6 have separate filter rules unless you use a combined family. An iptables-only ruleset leaves the IPv6 policy at ACCEPT; UFW with `IPV6=no` (found in old images) writes no IPv6 rules at all; nftables rules in `table ip` don't see IPv6. Services that listen on `[::]` accept both families. On the VPN side, a WireGuard full tunnel with only `0.0.0.0/0` in AllowedIPs sends IPv6 out of the local connection. In AWS, security group rules for 0.0.0.0/0 don't cover IPv6 either way; each family has its own rules.

**Diagnose:**

```bash
grep '^IPV6' /etc/default/ufw
sudo ip6tables -S | head -3
sudo nft list tables
sudo ss -ltn | grep -E '\[::\]:(5432|6379|8080)'
# From an outside host with IPv6
nc -6 -vz -w 3 2001:db8:10::10 5432
```

```text
IPV6=no
-P INPUT ACCEPT
-P FORWARD ACCEPT
-P OUTPUT ACCEPT
table ip filter
table ip nat
LISTEN 0      200          [::]:5432          [::]:*
Connection to 2001:db8:10::10 5432 port [tcp/postgresql] succeeded!
```

**What the output tells you:** UFW manages only IPv4, the IPv6 policies are wide open, the nftables tables are IPv4-only, and PostgreSQL listens on all IPv6 addresses: the database is reachable over IPv6 from the internet.

**Fix:**

```bash
# UFW: manage both families, then reload so every rule gets its IPv6 twin
sudo sed -i 's/^IPV6=no/IPV6=yes/' /etc/default/ufw
sudo ufw disable && sudo ufw enable
sudo ufw status | grep '(v6)' | head -3
# nftables: write host rules in "table inet" (one ruleset for IPv4 and IPv6), see entry 3.3
# Services: bind explicitly where possible (PostgreSQL: listen_addresses = '10.0.1.10')
# WireGuard full tunnel: AllowedIPs = 0.0.0.0/0, ::/0
nc -6 -vz -w 3 2001:db8:10::10 5432        # from outside again: must fail now
```

**Why this fix works:** a firewall that covers both families (UFW with IPv6 on, nftables inet tables) closes the second door with the same rules as the first; explicit bind addresses limit exposure even if a rule is missing; adding ::/0 sends IPv6 into the tunnel too. Don't rely on "nobody knows the IPv6 address": addresses leak through DNS, certificates' transparency logs and outbound connections.

**Prevent it:** scan both address families from outside on a schedule, check `ip6tables -S` or `nft list ruleset` in host compliance checks (Wazuh SCA can check firewall settings), and review IPv6 whenever a router or ISP change turns it on.

**Next step:** [Security & DevSecOps: network security](37-learn-security-devsecops.md) · [Ports inventory playbook](22-playbook-ports-inventory.md) · [Users, permissions and security: UFW](10-users-permissions-security.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — System Hardening: UFW Firewall Basics ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) · [Ubuntu Server docs](https://documentation.ubuntu.com/server/)

**Community threads:** Search: [Server Fault](https://serverfault.com/search?q=ufw+ipv6+ports+open+IPV6%3Dno) · [Reddit r/ipv6](https://www.reddit.com/r/ipv6/search/?q=firewall+ipv6+exposed+services&restrict_sr=1) · [Reddit r/WireGuard](https://www.reddit.com/r/WireGuard/search/?q=ipv6+leak+allowedips&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=docker+published+port+ipv6+exposed)

## Self-check

Ten timed break-and-fix exercises on the lab VMs from section 0. Snapshot first, break it exactly as described, then fix it using only the entry, and write your five-line note (symptom, evidence, cause, fix, prevention). Test every fix from the other side of the network, not from the server.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | On web1, change the static IP in netplan with a tab in the YAML, then do the change properly over SSH with `netplan try` | 15 min | 1.1 |
| 2 | Fresher | Replace /etc/resolv.conf with a hand-written file pointing at a dead server; restore resolution the Ubuntu way and prove it with `getent` | 10 min | 2.1, 2.2 |
| 3 | Junior | Publish a Postgres container on 0.0.0.0:5432 behind UFW, prove from outside that it's exposed, then close it in two different ways | 20 min | 3.1 |
| 4 | Junior | Block port 80 on fw1 and run `certbot renew --dry-run`; read the error, fix it, then issue one name with DNS-01 against staging | 25 min | 5.1, 5.5 |
| 5 | Junior | Add a stale AAAA record for www pointing at a second VM; reproduce the 404 from the CA on staging and fix it | 20 min | 5.2, 10.3 |
| 6 | Mid-level | Make nginx serve cert.pem and reproduce curl error 60; then trust a private CA for a registry in the OS, Docker and containerd stores | 30 min | 6.1, 6.3 |
| 7 | Mid-level | Build WireGuard on vpn1, install Docker on it, reproduce "handshake but no traffic", fix it, and add split DNS for corp.example.com | 40 min | 8.2, 2.3 |
| 8 | Senior | Give web1 a second NIC with DHCP; reproduce the double default route and the asymmetric reply from the remote office, fix both | 40 min | 1.2, 1.4 |
| 9 | Senior | Lower the MTU on fw1's WAN to 1420 and block ICMP fragmentation-needed; reproduce a hanging `git clone` through the VPN and in a dind job, then fix with MSS clamping and explicit MTUs | 45 min | 10.1, 10.2 |
| 10 | Senior/Lead | Run a cutover drill: lower TTLs, move www to a new IP with split-horizon and DNSSEC-validating resolvers in place, measure how long until every probe sees the new IP, and write it up as a postmortem | 60 min | 7.1, 7.3, 4.1 |

Quick questions to answer from memory:

1. Why does `dig` prove nothing about what an application resolves, and which command does?
2. Which chain sees a packet to a Docker-published port first, and why does UFW never see it?
3. Why does Let's Encrypt's HTTP-01 fail for a site served on port 81, even with a perfect redirect?
4. What does `dig +cd` tell you about a SERVFAIL, and what are the three usual causes of a validation failure?
5. A WireGuard tunnel shows a fresh handshake but no traffic: name three things to check on the server.
6. Why do small requests work and large ones hang across some tunnels, and which two fixes address it?

---

## Where to go next

- [Learn networking](28-learn-networking.md): the fundamentals behind every entry: routing, NAT, firewalls and conntrack, DNS, TLS, VPNs and MTU, IPv6 and packet capture.
- [Network reference](02-network.md), [DNS reference](08-dns.md) and [Web, HTTP and TLS reference](18-web-http-tls.md): the commands used here, one page each.
- [Site-down playbook](25-playbook-site-down.md), [Network speed playbook](24-playbook-network-speed.md) and [Ports inventory playbook](22-playbook-ports-inventory.md): step-by-step walks when you don't yet know which entry you are in.
- [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md): ACME inside Traefik, the default certificate, DNS-01 providers and everything between the proxy and your apps; the [Apache 443 and Dokploy case](21-case-apache-443-dokploy.md) shows the same layers on your own server.
- [Linux systems problems](41-problems-linux-systems.md): the sibling library for systemd, storage, memory and kernel problems that often sit under a "network" ticket; see also [Kernel and sysctl](13-kernel-system.md), [Logs and journal](06-logs-journal.md), [Processes](05-processes.md), [Memory](04-memory.md) and [Time and NTP](12-time-ntp.md).
- [Security & DevSecOps](37-learn-security-devsecops.md), [Users, permissions and security](10-users-permissions-security.md) and [SSH and remote access](09-ssh-remote-access.md): firewall policy, PKI and safe remote administration.
- [Learn Linux](27-learn-linux.md) and [Slow system playbook](23-playbook-slow-system.md): when the host, not the network, is the bottleneck; [CPU performance](03-cpu-performance.md) for softirq load from heavy packet rates.
- [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md): which of these problems you meet first on each path, and the AWS equivalents of OPNsense, port forwards and resolvers.
- [Practice arena](54-practice-arena.md): free labs and challenge sites for networking, DNS and TLS (section 4) to train beyond your own homelab.
- Official docs: [netplan](https://netplan.readthedocs.io/) · [systemd-resolved](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html) · [Let's Encrypt](https://letsencrypt.org/docs/) · [Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html) · [Docker firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · [BIND 9](https://bind9.readthedocs.io/) · [Unbound](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html) · [Pi-hole](https://docs.pi-hole.net/docker/tips-and-tricks/) · [OPNsense](https://docs.opnsense.org/manual/nat.html) · [WireGuard](https://www.wireguard.com/quickstart/) · [OpenVPN 2.6](https://openvpn.net/community-docs/community-articles/openvpn-2-6-manual.html) · [Tailscale](https://tailscale.com/kb/1023/troubleshooting) · [Headscale](https://headscale.net/stable/ref/integration/reverse-proxy/) · [NetBird](https://docs.netbird.io/help/troubleshooting-client)
