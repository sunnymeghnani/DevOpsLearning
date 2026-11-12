# 08 — DNS Troubleshooting

Typical symptoms: "could not resolve host", intermittent name failures, slow
first-connection (DNS timeout then fallback), app resolves differently than `dig`.

**"It's always DNS."** Test name resolution *and* the same connection by raw IP —
if IP works and name doesn't, it's DNS.

---

## 1. `dig` — the primary tool

```bash
dig example.com                        # A record, full detail
dig +short example.com                 # just the answer
dig example.com AAAA                   # IPv6
dig example.com MX                     # mail
dig example.com TXT                    # SPF/verification records
dig example.com NS                     # authoritative servers
dig example.com CNAME
dig example.com SOA                    # zone serial — did the update publish?
dig -x 10.0.1.20                       # reverse (PTR)
dig @8.8.8.8 example.com               # ask a SPECIFIC server — bypass local resolver
dig @10.0.0.2 internal.corp            # ask your internal/VPC resolver directly
dig +trace example.com                 # full delegation walk from the root
dig +norecurse @ns1.example.com example.com   # what the authoritative server itself says
dig example.com +tcp                   # force TCP (UDP blocked? big responses?)
```

Reading the output:
```
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 31337
;; ANSWER SECTION:
example.com.  300  IN  A  93.184.216.34
;; Query time: 23 msec
;; SERVER: 10.0.0.2#53(10.0.0.2)
```
- `status: NOERROR` + answer → resolution fine
- `status: NXDOMAIN` → name does not exist (typo? wrong search domain? record missing?)
- `status: NOERROR` but **empty answer** → name exists, no record of that TYPE
- `status: SERVFAIL` → resolver failure (upstream broken, DNSSEC validation failing)
- `status: REFUSED` → server won't answer you (ACL — asking the wrong server?)
- **Query time > 1000 ms or timeouts** → resolver unhealthy → app latency
- `SERVER:` → confirms *which* resolver actually answered — often the whole story
- `300` = TTL seconds → how long caches keep it (why changes propagate slowly)

Key comparison — cache vs truth:
```bash
dig example.com                        # via local resolver (cached)
dig @ns1.example.com example.com +norecurse    # straight from authority
# different answers → stale cache / TTL not expired / split-horizon DNS
```

## 2. `nslookup` and `host` — quick checks (also exist on Windows)

```bash
nslookup example.com
nslookup example.com 8.8.8.8           # against a specific server
host example.com
host -t mx example.com
host 10.0.1.20                         # reverse
```

## 3. What resolver is this box actually using?

```bash
cat /etc/resolv.conf                   # nameserver / search / options lines
resolvectl status                      # systemd-resolved: real upstream per interface
resolvectl query example.com           # resolve exactly as the system would
resolvectl statistics                  # cache hits, failures
resolvectl flush-caches                # clear systemd-resolved cache
cat /etc/nsswitch.conf | grep hosts    # order: files dns myhostname ...
cat /etc/hosts                         # static overrides — check for surprises!
getent hosts example.com               # resolve THROUGH nsswitch (what apps really get)
```
**`getent hosts` vs `dig`:** dig talks straight to DNS; apps use the libc path
(nsswitch: /etc/hosts first, then DNS). When "dig works but the app can't
resolve", compare these two, and check /etc/hosts for a stale entry.

`resolv.conf` gotchas:

- `127.0.0.53` = systemd-resolved stub → real upstreams via `resolvectl status`
- may be overwritten by DHCP/NetworkManager/cloud-init — edits silently reverted
- `options timeout:5 attempts:2` + dead first nameserver = seconds of delay on
  *every* lookup → looks like "app is slow", is actually DNS
- `search corp.internal` + `ndots` → short names expand oddly (big one in K8s)

## 4. Watching DNS on the wire

```bash
tcpdump -i any -nn port 53                       # queries and answers live
tcpdump -i any -nn port 53 and host 10.0.0.2     # to one resolver
```
See the query leave with no reply → resolver/firewall issue.
See NXDOMAIN replies for names like `db.corp.internal.corp.internal` → search-domain expansion bug.

## 5. DNS server side (if you run BIND/unbound/dnsmasq)

```bash
named-checkconf                        # BIND config syntax
named-checkzone example.com db.example.com     # zone file syntax
rndc status ; rndc flush               # BIND control
systemctl status dnsmasq unbound named # is it even running?
ss -ulpn sport = :53                   # is something listening on 53?
```

## 6. AWS specifics

- VPC resolver = **VPC CIDR base + 2** (e.g. 10.0.0.2 for 10.0.0.0/16) — test
  directly: `dig @10.0.0.2 internal.name`
- Private hosted zones need `enableDnsSupport` + `enableDnsHostnames` on the VPC.
- Security groups don't block DNS to the VPC resolver, but custom NACLs can (UDP/TCP 53).
- Hybrid on-prem↔AWS name resolution → Route 53 Resolver endpoints + forwarding
  rules; test each direction with `dig @<endpoint-ip> name`.

## Decision tree

```
"could not resolve host"
├── getent hosts NAME works but app fails → app has its own resolver config/cache (JVM caches forever by default!)
├── dig NAME fails, dig @8.8.8.8 NAME works → local resolver broken → resolv.conf/resolvectl
├── dig NXDOMAIN everywhere → record really missing/typo → check authority: dig @ns1 NAME
├── works sometimes → one of several nameservers is bad → test each: dig @nsX NAME
└── slow but works → dead first nameserver or DNSSEC issues → resolv.conf order, resolvectl statistics
```
