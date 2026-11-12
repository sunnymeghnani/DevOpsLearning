# Firewalls & intrusion blocking

Everything in this family ends up in one kernel packet filter, netfilter: ufw, firewalld, Docker, kube-proxy, fail2ban and CrowdSec's bouncers each add rules of their own. So work in this order: find out which tools have rules on the host, read the real ruleset with its counters, then change one rule at a time with a way back. Two facts explain most surprises: the first matching rule wins, and a Docker-published port is rewritten (DNAT) and forwarded, so it never passes ufw's INPUT rules.

| If you would reach for | Prefer | Because |
|---|---|---|
| `ufw status` | `ufw status numbered`, then `iptables -L ufw-user-input -n -v` | the numbers show the order (first match wins); the counters prove which rule really matches |
| `ufw deny 3000` for a container's port | a `DOCKER-USER` rule matching `--ctorigdstport 3000`, or not publishing the port | the DNAT-ed packet goes through FORWARD and never meets ufw's INPUT rules |
| `iptables -L` | `iptables -L CHAIN -n -v --line-numbers` | no DNS lookups, per-rule counters, and the positions that `-I` and `-D` need |
| an empty-looking `iptables -L` | `nft list ruleset`, `iptables-legacy -S`, `ip6tables -S` | native nftables tables, legacy rules and IPv6 rules are invisible to it |
| `iptables -F` or `nft flush ruleset` "to test" | one narrow temporary rule, deleted afterwards | a flush can lock you out and deletes Docker's NAT, so every container loses its network |
| `ufw enable` over SSH | `ufw allow OpenSSH`, a rollback scheduled with `at`, then `ufw --force enable` | the default deny incoming cuts every new SSH session |
| timeouts from one address only | `fail2ban-client status sshd`, `cscli decisions list --ip IP` | an automatic ban drops one source while everyone else connects |

### ufw status — which rules are active, in what order, behind which default policy?
Match: ufw status, ufw show
Instead of: plain ufw status, iptables -L
Safety: read-only · needs root

**In one line:** `ufw status verbose` shows whether ufw is on, its logging level, the default policies for incoming, outgoing and routed traffic, and the rules in the order ufw checks them; `numbered` adds the positions that `insert` and `delete` use.

**Read the command:** `ufw status verbose`

| Part | Meaning |
|---|---|
| `status` | active or inactive, then the rules |
| `verbose` | adds the `Logging:`, `Default:` and `New profiles:` lines |
| `numbered` | `[ 1]`, `[ 2]`… before each rule: the positions for `ufw insert N` and `ufw delete N` |
| `show added` | the rules as the commands that created them, even while ufw is inactive |

**What the output tells you:**

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    192.0.2.0/24
80,443/tcp                 ALLOW IN    Anywhere
3000/tcp                   DENY IN     Anywhere
```

`deny (incoming)`: whatever no rule allows is dropped without an answer, so clients time out. `deny (routed)`: the kernel forwards packets, and ufw drops those that no `ufw route` rule allows (`disabled (routed)`: forwarding is off). `Logging: on (low)` logs drops as `[UFW BLOCK]` in the kernel log. `(v6)` lines, the IPv6 twins, exist only with `IPV6=yes` in `/etc/default/ufw`.

**Why it is effective:** the three things that decide a packet's fate in ufw (is it on, which rule matches first, what happens to the rest) fit on one screen, and `numbered` lets you fix one rule instead of reaching for `ufw disable`.

**Compared with plain `ufw status` and `iptables -L`:** plain status lists the same rules, enough for "is 443 allowed?", but not the defaults, the logging or the positions. `iptables -L ufw-user-input -n -v` shows ufw's rules with packet counters: harder to read, but proof that a rule matches.

**Trap:** this is ufw's view only. Rules from Docker, fail2ban, CrowdSec or kube-proxy never appear, and a Docker-published port never passes these rules: if a container publishes 3000, `3000/tcp DENY IN Anywhere` changes nothing. `Status: inactive` hides every rule. A listed rule is not a matching rule: order, interface (`on ens18`) and protocol decide.

**Next step:** prove a match → `iptables -L ufw-user-input -n -v`. Find drops → `journalctl -k | grep 'UFW BLOCK'`. Container port → `iptables -t nat -L DOCKER -n`, then the DOCKER-USER card. The whole picture → `nft list ruleset`.

### ufw allow / deny / insert / delete — add, place and remove rules; the first match wins
Match: ufw allow, ufw deny, ufw reject, ufw limit, ufw insert, ufw delete
Instead of: ufw allow PORT, ufw disable
Safety: changes state: each command edits the live firewall at once and is saved, so it survives reboots · a wrong `deny` or `delete` can cut your SSH access

**In one line:** these commands add a rule scoped by source, port, protocol and interface, place it at a chosen position, or remove exactly one; ufw checks rules from the top and the first match decides.

**Read the command:** `ufw insert 1 deny from 198.51.100.23 to any port 443 proto tcp`

| Part | Meaning |
|---|---|
| `insert 1` | position 1, above all others; `allow` and `deny` alone append at the end |
| `deny` | drop silently, the client times out; `reject` refuses at once; `limit` blocks a source that tries 6 connections within 30 seconds |
| `from 198.51.100.23 to any` | from this source (or a network) to any address of this host |
| `port 443 proto tcp` | destination port and protocol; without `proto`, TCP and UDP |
| `in on docker_gwbridge`, `comment '…'` | only packets arriving on that interface; a label shown in `ufw status` |
| `delete 2`, `delete allow from …` | remove by position, or by repeating the exact rule |

**What the output tells you:**

```
Rule inserted
$ sudo ufw status numbered
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 443/tcp                    DENY IN     198.51.100.23
[ 2] 22/tcp                     ALLOW IN    192.0.2.0/24
[ 3] 80,443/tcp                 ALLOW IN    Anywhere
```

The deny sits above the `Anywhere` allow, so it wins. Added with `ufw deny from …`, it would land below rule 3 and never match.

**Why it is effective:** a scoped rule opens or closes one door, not a whole port; `insert` puts a block or an exception above a broader allow; a delete removes one rule, where `disable` removes all protection.

**Compared with `ufw allow 8080` and `ufw disable`:** `ufw allow 8080` works, but opens TCP and UDP to every source. `disable` shows in seconds whether ufw is the culprit, by leaving the host without a firewall while you test.

**Trap:** connections that are already open survive a new `deny` (ufw accepts established traffic before your rules), so the block seems not to work until the client reconnects. Positions shift after every delete: read `status numbered` again before the next one. Rules for Docker-published ports are accepted and do nothing. Traffic from containers to the host itself (Traefik to Apache on port 81) **is** filtered and needs an allow such as `in on docker_gwbridge`.

**Next step:** test from outside (`nc -zv -w 3 HOST PORT`) and watch the counters (`iptables -L ufw-user-input -n -v`). Cut a blocked client's open connections → `conntrack -D -s 198.51.100.23`. A container port → the DOCKER-USER card.

### ufw — switch it on safely, set the defaults, log drops, allow routed traffic
Match: ufw
Instead of: ufw enable over SSH, ufw default allow routed
Safety: changes state: `enable`, `disable`, `default`, `logging`, `route` and `reload` act at once · `enable` without an SSH rule cuts new SSH sessions; `reset` deletes every rule

**In one line:** the ufw commands for the firewall as a whole: switch it on or off (now and at boot), set the default policies, log what it drops, allow forwarded traffic with `route` rules, and re-read edited rule files.

**Read the command:** `ufw route allow in on wg0 out on ens18`

| Part | Meaning |
|---|---|
| `route allow` | a rule for **forwarded** traffic (FORWARD chain), such as VPN clients or pods |
| `in on wg0 out on ens18` | from the WireGuard interface to the uplink (`from 10.244.0.0/16`: a network instead) |
| `default deny incoming` | the verdict for packets no rule matches (also `outgoing`, `routed`) |
| `--force enable` | switch on, now and at boot, without the "may disrupt existing ssh connections" prompt |
| `logging low` | log drops as `[UFW BLOCK]`, rate-limited (`on` = `low`; `medium` and `high` log more) |
| `disable`, `reload` | all rules off, also after reboot / re-read `before.rules` and `after.rules` after an edit |

**What the output tells you:**

```
$ sudo ufw route allow in on wg0 out on ens18
Rule added
Rule added (v6)
$ sudo ufw status | grep FWD
Anywhere on ens18          ALLOW FWD   Anywhere on wg0
Anywhere (v6) on ens18     ALLOW FWD   Anywhere (v6) on wg0
$ sudo ufw --force enable
Firewall is active and enabled on system startup
```

`ALLOW FWD` marks a route rule, `(v6)` its IPv6 twin.

**Why it is effective:** the defaults decide everything your rules do not mention, a `route` rule opens forwarding for one path only, and `[UFW BLOCK]` lines turn silent drops into evidence: `SRC`, `DST`, `DPT`.

**Compared with `ufw enable` over SSH and `default allow routed`:** a plain enable is fine from a console, or once an SSH rule exists; remotely, allow OpenSSH first and schedule a rollback (`echo 'ufw --force disable' | sudo at now + 5 minutes`), cancelled with `atrm` after a new login works. `default allow routed` also makes a VPN work, by forwarding everything.

**Trap:** your own session survives `enable` (its packets are established), so a missing SSH rule shows only at the next login. `disable` and `reset` drop all protection, and `reset` deletes every rule. On a Docker host, published ports pass Docker's FORWARD chains first, so neither `deny (routed)` nor `route` rules govern them; for VPN and pod traffic, route rules work.

**Next step:** find drops → `journalctl -k | grep 'UFW BLOCK'`. Forwarding still fails → `sysctl net.ipv4.ip_forward`, `iptables -L FORWARD -n -v --line-numbers`. Container ports → the DOCKER-USER card.

### iptables — which rule in which chain matches, and how many packets has it counted?
Match: iptables
Instead of: iptables -L, ufw status
Safety: read-only for `-L`, `-S` and `-V` (needs root) · changes state: `-I`, `-A`, `-D`, `-F` and `-P` act at once and are lost at reboot; `-F` under a DROP policy locks you out and empties Docker's chains

**In one line:** `iptables -L -n -v --line-numbers` lists each chain with its policy and, for every rule, its position and the packets and bytes it has matched: proof of which rule catches the traffic.

**Read the command:** `iptables -L -n -v --line-numbers`

| Part | Meaning |
|---|---|
| `-L` | list the filter table's chains, or one (`-L INPUT`) |
| `-n` | numeric: no reverse DNS, which hangs when DNS is broken |
| `-v` | packet and byte counters, interfaces, the policy's counters |
| `--line-numbers` | the positions for `-I CHAIN N` and `-D CHAIN N` |
| `-S FORWARD` | the rules as the commands that made them: exact, easy to diff |
| `-V` | version and backend: `(nf_tables)` or `(legacy)` |
| `-I INPUT -p udp --dport 4789 -j DROP` | **changes state**: insert at the top (`-D` with the same rule deletes it) |

**What the output tells you:**

```
Chain INPUT (policy DROP 2210 packets, 132K bytes)
num   pkts bytes target  prot opt in     out  source           destination
1     8.1M  9.6G ACCEPT  all  --  *      *    0.0.0.0/0        0.0.0.0/0     ctstate RELATED,ESTABLISHED
2     1903  114K ACCEPT  tcp  --  ens18  *    192.0.2.0/24     0.0.0.0/0     tcp dpt:22
3      317 19020 DROP    tcp  --  *      *    0.0.0.0/0        0.0.0.0/0     tcp dpt:8443
4        0     0 ACCEPT  tcp  --  ens18  *    198.51.100.0/24  0.0.0.0/0     tcp dpt:8443
```

The first matching `ACCEPT`, `DROP` or `REJECT` ends the search: rule 3 drops 8443 for everyone, so the partner's allow below it has never matched. Policy counters: packets that no rule matched. A `target` can be another chain (`ufw-user-input`, `DOCKER-USER`): follow it. Some iptables releases print `prot` as a number with `-n` (6 = tcp, 0 = all).

**Why it is effective:** a rule that exists is not a rule that matches. Retry from the client and watch which counter rises: that rule decides, whatever the config files say.

**Compared with `iptables -L` and `ufw status`:** bare `-L` looks up every address in DNS (slow, or stuck) and shows no counters, interfaces or positions. `ufw status` is readable but shows only ufw's rules, without counters.

**Trap:** counters keep adding up, so compare two readings while you reproduce the problem (`watch -d -n 2 'iptables -L INPUT -n -v'`). The filter table never shows NAT, and `iptables` lists one backend and IPv4 only. Positions shift after each `-I` or `-D`: list again before deleting by number.

**Next step:** a DROP counter rising → delete it, or `-I` an allow above it. Published container port → the DOCKER-USER card. A rewritten port → `iptables -t nat -L -n -v`. "legacy tables present" → the iptables-nft card.

### iptables DOCKER-USER — let only chosen sources reach a Docker-published port
Match: iptables docker-user
Instead of: ufw deny PORT, iptables -A INPUT
Safety: changes state: acts at once on forwarded container traffic; hand-made rules are lost at reboot · a rule without `-i ens18` or a port match can cut containers off

**In one line:** Docker rewrites a published port's destination (DNAT) before filtering, so the packet crosses FORWARD, not INPUT where ufw's rules sit; `DOCKER-USER`, first in FORWARD, is the chain Docker leaves for your own rules.

**Read the command:** `iptables -I DOCKER-USER -i ens18 -s 198.51.100.0/24 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL -j ACCEPT`

| Part | Meaning |
|---|---|
| `-I DOCKER-USER` | insert at the top (`-A` appends, `-D` deletes the identical rule) |
| `-i ens18` | only traffic arriving from outside; container-to-container and outbound traffic stay untouched |
| `-s 198.51.100.0/24` | the admin network (`! -s …`: everyone else) |
| `-p tcp -m conntrack --ctorigdstport 3000` | TCP **originally** sent to port 3000; after DNAT the packet carries the container's port |
| `--ctdir ORIGINAL` | client-to-container packets only, never replies to a container's own connections |
| `-j ACCEPT` | let it through; `DROP` discards it; `RETURN` hands it back to Docker's rules |

**What the output tells you:** with a `DROP` inserted first and this `ACCEPT` above it, `iptables -L DOCKER-USER -n -v --line-numbers` shows:

```
Chain DOCKER-USER (1 references)
num   pkts bytes target  prot opt in     out  source            destination
1        4   240 ACCEPT  tcp  --  ens18  *    198.51.100.0/24   0.0.0.0/0    ctorigdstport 3000 ctdir ORIGINAL
2       17  1020 DROP    tcp  --  ens18  *    0.0.0.0/0         0.0.0.0/0    ctorigdstport 3000 ctdir ORIGINAL
```

The admin network got in (4 packets) and 17 packets from elsewhere were dropped. `(1 references)`: FORWARD jumps here, so the rules are live. An empty chain, or a lone `RETURN` (older engines), filters nothing.

**Why it is effective:** it runs before Docker's own accept rules and Docker never edits it: the port stays open to the sources you choose only.

**Compared with `ufw deny 3000`:** ufw accepts and lists the rule, but it sits in INPUT, which these packets never cross: its counter stays at 0. ufw remains the right tool for host services (sshd, Apache) and `network_mode: host` containers.

**Trap:** `-I` puts each new rule on top: insert the `DROP` first, then the `ACCEPT`. Hand-made rules vanish at reboot: re-create them with a oneshot unit ordered after docker.service, or in ufw's `after.rules`, never by saving the whole table (that freezes Docker's changing rules). With IPv6 enabled in Docker, repeat them with `ip6tables`; Docker's experimental nftables backend has no DOCKER-USER chain.

**Next step:** prove it from outside: `nmap -Pn -p 3000 HOST` shows `filtered` from a foreign network, `open` from the admin one. Counters stay at 0 → wrong interface name (`ip route show default`). Better still → do not publish the port (route it through Traefik), or bind it to 127.0.0.1.

### iptables -t nat / iptables-save — which rule rewrites this port, and where does it send it?
Match: iptables nat, iptables-save
Instead of: ss -ltnp, docker ps
Safety: read-only as shown (needs root) · changes state: `-t nat -A` and `-D` add or delete NAT rules at once, until reboot; restoring an old dump on a Docker or Kubernetes host brings back stale addresses

**In one line:** the nat table rewrites addresses: DNAT for published ports, port forwards and Kubernetes Services, MASQUERADE for containers, pods and VPN clients going out; `iptables-save` prints it as plain rules to grep, diff or back up.

**Read the command:** `iptables -t nat -L DOCKER -n --line-numbers`

| Part | Meaning |
|---|---|
| `-t nat` | the nat table instead of the default filter table |
| `-L DOCKER` | Docker's chain: one DNAT rule per published port |
| `-n`, `--line-numbers` | numeric, with rule positions |
| `-S POSTROUTING` | rules as commands: one `MASQUERADE` per Docker subnet or VPN range |
| `iptables-save -t nat | grep -- '--dport 30080'` | every NAT rule for one port, in all chains, in exact syntax |
| `iptables-save > /root/ipt-before.txt` | a full backup to `diff` against after a change |

**What the output tells you:**

```
Chain DOCKER (2 references)
num  target     prot opt source               destination
1    DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8081 to:10.201.0.3:3000
$ sudo iptables-save -t nat | grep -- '--dport 30080'
-A KUBE-NODEPORTS -p tcp -m comment --comment "demo/web:http" -m tcp --dport 30080 -j KUBE-EXT-QK3T2ZB4HMQK7ACX
```

`dpt:8081 to:10.201.0.3:3000`: connections to host port 8081 go to port 3000 of container 10.201.0.3. `(2 references)`: PREROUTING (traffic from outside) and OUTPUT (from the host itself) jump here. kube-proxy's comment names the Service (`demo/web`) behind NodePort 30080; its chain leads on to `KUBE-SVC-…` and one `KUBE-SEP-…` per endpoint.

**Why it is effective:** many ports answer without any listening socket (Docker without its userland proxy, kube-proxy NodePorts), and these rules are their real owner. `iptables-save` prints exact rules you can grep by port, comment or target.

**Compared with `ss -ltnp` and `docker ps`:** ss shows sockets, at best `docker-proxy`, not the rule the kernel applies. `docker ps` shows the mapping Docker intended; the nat table shows what is enforced, including other tools' rules, such as a `REDIRECT` from 443 to 8443.

**Trap:** plain `iptables -L` never shows these rules. After DNAT, filter rules see the container's port (3000), not the published one (8081). Never `iptables-restore` an old dump, or persist the whole table, on a Docker or Kubernetes host: their addresses change and their rules are rebuilt at start.

**Next step:** which container is 10.201.0.3 → `docker network inspect NET`. Port should not be public → the DOCKER-USER card. NodePort missing → IPVS or nftables mode: `ipvsadm -Ln`, `nft list table ip kube-proxy`. Live translations → `conntrack -L -p tcp --dport PORT`.

### iptables-nft / iptables-legacy / ip6tables — which rule sets does this listing leave out?
Match: iptables-nft, iptables-legacy, ip6tables
Instead of: iptables -L
Safety: read-only for `-S` and `-L` (needs root) · changes state: `ip6tables -I`, `-A` and `-D` edit the IPv6 rules at once

**In one line:** iptables rules can live in three separate sets, each listed only by its own command: the nf_tables backend (`iptables-nft`, what `iptables` means on current Ubuntu), the old x_tables backend (`iptables-legacy`) and IPv6 (`ip6tables`). Packets must pass the legacy and the nft rules alike.

**Read the command:** `iptables-legacy -S 2>/dev/null | wc -l ; iptables-nft -S 2>/dev/null | wc -l`

| Part | Meaning |
|---|---|
| `iptables-legacy`, `iptables-nft` | the same syntax, aimed at one backend each |
| `-S` | the filter table's rules as commands |
| `2>/dev/null` | hide errors (tool or kernel module missing), so an unused backend counts 0 |
| `| wc -l` | count lines: 3 are only the default policies; dozens mean a tool writes there |
| `;` | run the second count whatever the first returns |
| `ip6tables -S` | the IPv6 rules, separate from IPv4 in both backends |

**What the output tells you:**

```
$ iptables -V
iptables v1.8.10 (nf_tables)
$ sudo iptables-legacy -S 2>/dev/null | wc -l ; sudo iptables-nft -S 2>/dev/null | wc -l
41
112
$ sudo ip6tables -S | head -3
-P INPUT ACCEPT
-P FORWARD ACCEPT
-P OUTPUT ACCEPT
```

`iptables` is the nf_tables backend, yet 41 legacy lines exist: some tool (an old script, a CNI or kube-proxy image, fail2ban in a container) still writes legacy rules, which neither `iptables -L` nor `nft list ruleset` shows. The IPv6 policies are `ACCEPT` with no rules, so services listening on `[::]` are open over IPv6.

**Why it is effective:** "no rule, yet traffic is dropped", rules that vanish or apply twice, and "closed over IPv4, open over IPv6" each come down to one of these sets, and two line counts expose it.

**Compared with `iptables -L`:** it lists one backend and IPv4 only. iptables-nft does warn `iptables-legacy tables present`, but nothing warns about IPv6.

**Trap:** an allow in one backend does not help if the other drops. Switching backends (`update-alternatives --set iptables /usr/sbin/iptables-nft`, likewise `ip6tables`) leaves Docker's and kube-proxy's rules in the old set until they restart: plan a maintenance window and reboot. ufw writes IPv6 rules only with `IPV6=yes` in `/etc/default/ufw`.

**Next step:** legacy rules → read them with `iptables-legacy -S`; chain names (`KUBE-`, `DOCKER`, `f2b-`) reveal the writer, which you then move to one backend. IPv6 open → `IPV6=yes` for ufw or a `table inet` in nftables, then test from outside with `nc -6 -zv -w 3 HOST PORT`.

### nft list — every table, chain and rule, whichever tool wrote it
Match: nft list
Instead of: iptables -L, ufw status
Safety: read-only · needs root

**In one line:** `nft list ruleset` prints every nftables table on the host (ufw's and Docker's rules via iptables-nft, fail2ban's `f2b-table`, kube-proxy's, your own) with each chain's hook, priority and policy: everything that can drop a packet, except legacy iptables rules.

**Read the command:** `nft list ruleset`

| Part | Meaning |
|---|---|
| `list ruleset` | all tables of all families: `ip`, `ip6`, `inet` (IPv4 and IPv6 together), `bridge`… |
| `list tables` | names only: which tools have rules here |
| `list table inet f2b-table` | one table, by family and name (here fail2ban's bans) |
| `list table ip kube-proxy` | kube-proxy's rules in nftables mode |
| `| grep -nE 'dport (22|80|443)'` | every rule for these ports, with line numbers |

**What the output tells you:**

```
table ip filter {
	chain INPUT {
		type filter hook input priority filter; policy drop;
		counter packets 9212 bytes 11034520 jump ufw-before-logging-input
…
table inet f2b-table {
	set addr-set-sshd {
		type ipv4_addr
		elements = { 198.51.100.23, 203.0.113.45 }
	}
```

`table ip filter` with upper-case chains holds rules written by iptables-nft (ufw, Docker). `type filter hook input priority filter; policy drop;` makes a base chain: the `hook` is where in the packet's path it runs (prerouting, input, forward, output, postrouting), `priority` orders the chains on one hook (lower first: `raw` -300, `dstnat` -100, `filter` 0, `srcnat` 100), and `policy` decides what no rule matched. Only rules with `counter` count hits. The `f2b-table` set holds fail2ban's banned addresses, which `ufw status` never shows.

**Why it is effective:** ufw, iptables-nft and firewalld all write here, so this is the ground truth for every tool at once, and the hook and priority lines explain why a rule never sees a packet.

**Compared with `iptables -L` and `ufw status`:** each shows only its own tool's rules; `iptables -L` misses native tables such as `f2b-table`, `kube-proxy` or a hand-written `inet hostfw`.

**Trap:** every base chain on a hook sees the packet: `accept` ends only that chain, and another table's chain can still drop it, while `drop` is final. So "my table accepts it" proves nothing. Legacy iptables rules never appear here. Docker and Kubernetes hosts produce hundreds of lines: list one table, or grep for `dport`, `policy`, `drop` and `reject`.

**Next step:** a drop in a tool's table → change it with that tool (`ufw`, `fail2ban-client set JAIL unbanip`, `cscli decisions delete`), which would overwrite a hand edit. Several tools fighting → `systemctl status ufw firewalld nftables`. A rewritten port → `nft list table ip nat`.

### nft — add, check and delete nftables rules without touching anyone else's
Match: nft
Instead of: systemctl restart nftables, nft flush ruleset
Safety: changes state: `add`, `insert`, `delete`, `flush` and `-f` change the live ruleset at once, lost at reboot unless in `/etc/nftables.conf`; `flush ruleset` deletes every tool's tables · `-c` only checks

**In one line:** `nft` creates tables, chains and rules, loads a whole file as one transaction, checks a file without applying it, and deletes exactly what you created.

**Read the command:** `nft add rule ip nat prerouting iifname "lan0" ip daddr 203.0.113.10 tcp dport { 80, 443 } dnat to 10.0.1.10`

| Part | Meaning |
|---|---|
| `add rule` | append at the end of a chain (`insert rule`: at the top) |
| `ip nat prerouting` | family `ip` (IPv4), table `nat`, chain `prerouting`; both must exist already |
| `iifname "lan0" ip daddr 203.0.113.10 tcp dport { 80, 443 }` | came in on lan0, for the public IP, port 80 or 443 (`{ }` is a set) |
| `dnat to 10.0.1.10` | rewrite the destination to the internal web server |
| `'add chain inet x in { type filter hook input priority 0; }'` | a base chain on the input hook; the quotes keep `{`, `;` and `}` from the shell |
| `-c -f /etc/nftables.conf` | parse and check the file, apply nothing |

**What the output tells you:**

```
$ sudo nft -c -f /etc/nftables.conf && echo OK
OK
$ sudo nft list table inet x
table inet x {
	chain in {
		type filter hook input priority filter; policy accept;
		tcp dport 443 drop
	}
}
```

nft prints nothing on success; errors name the file, line and column. `nft -a list …` shows each rule's `# handle N`, which `nft delete rule inet x in handle N` removes; `nft delete table inet x` removes everything in the table.

**Why it is effective:** `nft -f` applies a file atomically (`-f -` reads a here-document), so a typo cannot leave half a firewall, and `-c` catches it first. Your own table can be replaced or deleted without touching anyone else's.

**Compared with `systemctl restart nftables`:** it applies `/etc/nftables.conf`, but Ubuntu's stock file starts with `flush ruleset`, deleting every table on the host, Docker's NAT included. Begin the file with `table inet hostfw` and `delete table inet hostfw` instead: a reload then replaces only yours.

**Trap:** typed rules vanish at reboot. `add rule` appends, so an `accept` added after a `drop` is never reached. Your `accept` does not override another table's `drop` on the same hook, but your `drop` is final for everyone. `notrack` is only for traffic that needs neither NAT nor stateful rules.

**Next step:** after a change → `nft list table inet NAME` and its counters. Lab finished → `nft delete table inet lab`. Make it permanent → put the table in `/etc/nftables.conf`, check it with `nft -c -f`, then `systemctl enable --now nftables`.

### firewall-cmd — what does firewalld allow, in which zone, now and after a reload?
Match: firewall-cmd
Instead of: nft list ruleset on RHEL, systemctl stop firewalld
Safety: `--state` and `--list-*` are read-only · changes state: `--add-*` and `--remove-*` act at once; without `--permanent` they are lost at the next `--reload` or reboot, and `--permanent` alone waits for `--reload`

**In one line:** on RHEL, Rocky and Fedora, firewalld manages the firewall in zones; `firewall-cmd --list-all` shows what the active zone allows (services, ports, rich rules) and which interfaces and sources it governs.

**Read the command:** `firewall-cmd --add-rich-rule='rule family=ipv4 source address=10.0.20.11 port port=5201 protocol=tcp accept'`

| Part | Meaning |
|---|---|
| `--add-rich-rule='…'` | add a rich rule (source, port and action in one line) to the default zone, **runtime only** |
| `rule family=ipv4 source address=10.0.20.11` | IPv4 packets from this client only |
| `port port=5201 protocol=tcp accept` | to TCP port 5201 (iperf3 here): let them in (`reject` and `drop` also exist) |
| `--remove-rich-rule='…'` | remove the identical rule |
| `--state`, `--list-all` | is firewalld running? / the default zone's settings |
| `--permanent`, `--reload` | change the saved configuration / load it, dropping runtime-only changes |

**What the output tells you:**

```
$ sudo firewall-cmd --list-all
public (active)
  target: default
  …
  interfaces: ens192
  services: cockpit dhcpv6-client ssh
  ports: 8443/tcp
  …
  rich rules:
	rule family="ipv4" source address="10.0.20.11" port port="5201" protocol="tcp" accept
```

`(active)`: the zone is bound to an interface or a source. `interfaces`: the NICs it governs; packets from a source bound to another zone are handled there. `services` are named port sets (`ssh` = 22/tcp). `target: default` rejects what nothing allows, so clients see `No route to host`, not a timeout.

**Why it is effective:** a firewalld port is open only in its zone, for the packets that land in that zone; `--list-all` (with `--get-active-zones`) shows the zone that really applies, in one short block.

**Compared with `nft list ruleset` and `systemctl stop firewalld`:** nft shows the generated rules (`table inet firewalld`), complete but long. Stopping firewalld proves it is the culprit by opening everything.

**Trap:** the rich rule above is runtime only: ideal for a test, gone at anyone's next `--reload` or a reboot. A `--permanent` change does nothing until `--reload`. `--list-all` shows the runtime state; compare it with `--list-all --permanent`. `No route to host` from a firewalld host is a reject, not a routing fault.

**Next step:** zone unclear → `firewall-cmd --get-active-zones`. Keep a tested change → `firewall-cmd --runtime-to-permanent`. Open a port for good → `--permanent --add-port=8443/tcp`, then `--reload`. A bind that fails with "Permission denied" → SELinux (`semanage port`), not the firewall.

### fail2ban-client — is this IP banned, by which jail, and how do I lift the ban?
Match: fail2ban-client, fail2ban-regex
Instead of: ufw status, iptables -L INPUT
Safety: `status` and `get` are read-only (needs root) · changes state: `set JAIL unbanip` and `set JAIL banip` change bans at once

**In one line:** fail2ban counts failures per IP in a log or the journal and bans an IP in the firewall for a while; `fail2ban-client` asks the running daemon which jails exist, what each has counted and banned, and lifts a ban.

**Read the command:** `fail2ban-client status sshd`

| Part | Meaning |
|---|---|
| `status` | the daemon's jails (`Jail list`) |
| `status sshd` | one jail: failures, bans and the `Banned IP list` |
| `get sshd actions` | how this jail bans (`nftables`, `iptables-multiport`, `ufw`…): where its rule lives |
| `set sshd unbanip 198.51.100.7` | **changes state**: lift this IP's ban in that jail |
| `status traefik-auth` | a jail that reads a proxy's access log for failed logins |

**What the output tells you:**

```
Status for the jail: sshd
|- Filter
|  |- Currently failed:	3
|  |- Total failed:	1874
|  `- Journal matches:	_SYSTEMD_UNIT=sshd.service + _COMM=sshd
`- Actions
   |- Currently banned:	2
   |- Total banned:	241
   `- Banned IP list:	198.51.100.7 203.0.113.45
```

`Currently failed`: sources with failures counted, not banned yet. `Total failed`: matches since the jail started; 0 while the log fills with attacks means the filter or the backend does not match. `Journal matches` (or `File list`): what the jail reads. `Banned IP list`: the answer to "is it a ban?".

**Why it is effective:** a timeout from one address while everyone else connects is the signature of a ban, and one command confirms it and names the jail, without reading firewall tables.

**Compared with `ufw status` and `iptables -L INPUT`:** ufw never lists fail2ban's bans; they sit in fail2ban's own nftables table (`nft list table inet f2b-table`) or `f2b-…` iptables chains, which prove that a ban is enforced but not why.

**Trap:** bans land in INPUT by default, so traffic to Docker-published ports (Traefik on Dokploy) still gets through: such jails need `chain = DOCKER-USER` with an iptables action. An unbanned office NAT or monitoring host is banned again at its next failures unless it is in `ignoreip`. Behind a proxy that hides client addresses, the jail bans the proxy, and with it everyone.

**Next step:** banned → `set JAIL unbanip IP`, then add the address to `ignoreip` in `jail.local`. Not banned → `cscli decisions list --ip IP`, then the `UFW BLOCK` log. Never bans → test the filter with `fail2ban-regex`. Daemon dead → `journalctl -u fail2ban`. Related: `fail2ban-regex LOG FILTER` runs a filter over a log offline, read-only: LOG is a file or `systemd-journal`, FILTER a file in `filter.d/` or a name such as `sshd`. Its `Lines: 5214 lines, 0 ignored, 0 matched, 5214 missed` means the regex or the date format does not fit that log (a JSON access log read by a common-log-format filter).

### cscli — what did CrowdSec decide, why, and is anything enforcing it?
Match: cscli
Instead of: fail2ban-client status, reading the access log
Safety: `list`, `inspect`, `metrics`, `explain` and `status` only read · changes state: `decisions add` and `delete` ban or unban at once; `bouncers add` and `delete` create or revoke API keys (a new key is shown once); `collections install` adds parsers and scenarios

**In one line:** CrowdSec turns attack patterns in logs into decisions ("ban 198.51.100.23 for 4 h") kept by its Local API, and separate bouncers (the host firewall, a Traefik plugin) enforce them; `cscli` shows each link: lines parsed, alerts, decisions, and when each bouncer last pulled.

**Read the command:** `cscli decisions list --ip 198.51.100.23 -o raw`

| Part | Meaning |
|---|---|
| `decisions list --ip 198.51.100.23` | active decisions for this address: scenario, action, time left |
| `-o raw` | CSV, one line per decision, easy to paste into a ticket |
| `decisions delete --ip …` | **changes state**: unban now |
| `alerts inspect 812 -d` | the alert behind a decision, with its events (paths, status codes) |
| `bouncers list -o raw` | registered bouncers and their `last_pull`: is anything enforcing? |
| `metrics` | per log source: lines read, parsed and unparsed |
| `explain --file /var/log/traefik/access.log --type traefik` | run a log through the parsers, stage by stage |

**What the output tells you:**

```
id,source,ip,reason,action,country,as,events_count,expiration,simulated,alert_id
41301,crowdsec,198.51.100.23,crowdsecurity/http-probing,ban,NL,64500 EXAMPLE-NET,14,3h12m4s,false,812
$ sudo cscli bouncers list -o raw
name,ip,revoked,last_pull,type,version,auth_type
traefik-bouncer,10.0.1.14,false,2026-09-30T08:12:40Z,Crowdsec-Bouncer-Traefik-Plugin,1.x,api-key
```

`reason` is the scenario that fired, `expiration` the time left, `simulated=false` means the decision should be enforced, and `alert_id` leads to the evidence. The bouncer's `last_pull` is days old, so the Traefik plugin is not fetching decisions: the ban exists only on paper.

**Why it is effective:** CrowdSec separates deciding from enforcing, so "is it banned?" and "is the ban applied?" are two questions; decisions and bouncers answer both, and the alert's events tell an attack from a false positive.

**Compared with `fail2ban-client status` and reading the access log:** fail2ban writes its bans straight into the firewall; a CrowdSec decision does nothing without a working bouncer. The access log shows the 403s, not their reason.

**Trap:** private addresses are whitelisted by default, so a test from your LAN is never banned. The host firewall bouncer filters INPUT unless its chains include DOCKER-USER. Behind Swarm's ingress mesh or a proxy, clients can share one address, and banning it locks everyone out. A deleted decision returns if the scenario fires again. With CrowdSec in a container, run `docker exec CONTAINER cscli …`.

**Next step:** decision but no block → `bouncers list`, `cscli lapi status`, the bouncer's chains. No decisions ever → `metrics` (nothing parsed?), `collections list`, `explain`. False positive → `alerts inspect ID -d`, `decisions delete --ip IP`, then the app's collection (`collections install crowdsecurity/nextcloud`) or a whitelist.
