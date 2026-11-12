# DNS, HTTP, TLS & web servers

Follow a web request in the order it happens: the name resolves (`dig`, `resolvectl`), a TCP and TLS connection is made and the certificate checked (`curl -v`, `openssl s_client`), then a web server or proxy picks a virtual host and a backend (`apache2ctl -S`, `nginx -T`). Test each layer on its own, test every configuration before you reload it, and load-test only systems you own.

| If you would reach for | Prefer | Because |
|---|---|---|
| `nslookup name`, `ping name` | `dig +noall +answer name`, `dig @ns1.example.net name +norecurse` | dig shows the status code, the TTL and which server answered, one server at a time |
| `cat /etc/resolv.conf` | `resolvectl status`, `resolvectl query name` | on Ubuntu resolv.conf only says `127.0.0.53`; resolvectl shows the real servers per interface and which one answered |
| `curl -H 'Host: name' https://192.0.2.10/` | `curl -sv --resolve name:443:192.0.2.10 https://name/` | `--resolve` keeps the real name for SNI, the certificate check and the Host header |
| `curl -k` | `openssl s_client -connect host:443 -servername host -showcerts` | `-k` hides the certificate problem; s_client shows the chain the server sends and why it fails |
| `systemctl restart apache2` | `apache2ctl configtest && systemctl reload apache2` | a restart with a broken file leaves every site down; the test catches it first |
| `grep -r ServerName /etc/apache2` | `apache2ctl -S` | Apache's own map of ports, names, default vhost and file:line |
| `ls /etc/letsencrypt/live` | `certbot certificates`, `certbot renew --dry-run` | domains and expiry per certificate, and proof that renewal works today |

### dig — what does DNS answer for this name, and which server said so?
Match: dig, whois
Instead of: nslookup, ping name
Safety: read-only · sends DNS queries

**In one line:** `dig` asks one DNS server one precise question (a name and a record type) and prints the whole reply: status code, flags, each record with its TTL, the server that answered and the query time.

**Read the command:** `dig @ns1.example.net app.example.com +norecurse +noall +answer`

| Part | Meaning |
|---|---|
| `@ns1.example.net` | ask this server. Without `@`, dig uses the `nameserver` lines of /etc/resolv.conf (on Ubuntu `127.0.0.53`, the systemd-resolved stub) |
| `app.example.com` | the name; with no type dig asks for `A`. Add `AAAA`, `MX`, `TXT`, `NS`, `SOA` or `CAA` for other records |
| `+norecurse` | "answer from your own data only": how you read what an authoritative server really publishes |
| `+noall +answer` | hide every section, then show only the answer lines with their TTLs |
| `+short` | values only: good for scripts, but hides the status and the TTL |
| `+trace` | follow the delegation from the root servers down yourself, with no resolver cache in between |
| `-x 192.0.2.10` | reverse lookup (PTR) |
| `+time=2 +tries=1`, `+tcp` | one 2-second attempt instead of the default retries; query over TCP |

**What the output tells you:** (plain `dig app.example.com`, trimmed)

```
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 4242
;; flags: qr rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1
;; ANSWER SECTION:
app.example.com.     300   IN   CNAME   web01.example.com.
web01.example.com.   300   IN   A       192.0.2.10
;; Query time: 23 msec
;; SERVER: 127.0.0.53#53(127.0.0.53)
```

`status:` is the verdict: `NOERROR` with `ANSWER: 0` = the name exists but has no record of that type; `NXDOMAIN` = the name does not exist; `SERVFAIL` = the resolver failed (upstream down, DNSSEC, broken delegation); `REFUSED` = this server will not answer you. `aa` in `flags:` marks an authoritative answer. `300` is the TTL: how many more seconds caches may serve this answer.

**Why it is effective:** "DNS is broken" becomes a fact with a server, a status and a TTL. Asking the authoritative server (`+norecurse`), a public resolver (`@1.1.1.1`) and the local one in turn tells you whether the zone is wrong, a cache is stale or only this host's resolver is broken.

**Compared with `nslookup` and `ping name`:** nslookup prints the answer and the server but hides TTLs and flags. ping shows only the address it ended up with (/etc/hosts included), then tests ICMP.

**Trap:** dig speaks pure DNS: it ignores /etc/hosts and does not apply the `search` list unless you add `+search`, so `dig app` and your application can disagree (`getent ahosts app` shows what programs get). An empty `+short` hides whether the reply was NXDOMAIN, an empty answer or SERVFAIL.

**Next step:** NXDOMAIN → ask the authoritative server and check the delegation with `+trace`. SERVFAIL → try `@1.1.1.1`, then `+cd`: if that answers, DNSSEC validation is failing. Old answer after a change → wait out the TTL or flush (`resolvectl flush-caches`, `rndc flushname`). dig fine but the app fails → `resolvectl query`, /etc/hosts. Related: `whois example.com | grep -i 'name server'` shows the delegation the registry holds; if it differs from the name servers of the zone you edit, fix it at the registrar. Its format varies by TLD, contact data is usually redacted, and some registries now answer only over RDAP.

### nslookup / host — a quick lookup where dig is missing
Match: nslookup, host
Instead of: —
Safety: read-only · sends DNS queries

**In one line:** `nslookup` exists on Windows and in most minimal container images (busybox, alpine); `host` is the terse Linux lookup. Both answer "does this name resolve from here, and to what?"

**Read the command:** `nslookup example.com 8.8.8.8`

| Part | Meaning |
|---|---|
| `example.com` | the name to look up |
| `8.8.8.8` | ask this DNS server instead of the configured one |
| `nslookup -type=mx example.com`, `host -t mx example.com` | ask for another record type |
| `host 10.0.1.20` | given an IP, `host` does the reverse (PTR) lookup |

**What the output tells you:**

```
Server:         8.8.8.8
Address:        8.8.8.8#53

Non-authoritative answer:
Name:   example.com
Address: 192.0.2.80
```

`Server:` is who answered. "Non-authoritative answer" is normal: a resolver answered, not the zone's own server. Failures read `** server can't find NAME: NXDOMAIN` or `SERVFAIL`; host prints `Host NAME not found: 3(NXDOMAIN)`.

**Why it is effective:** inside a pod, a container or on a Windows box without dig, it still shows whether the name resolves from *there*, and through which server.

**Trap:** these query DNS directly and skip /etc/hosts (Windows nslookup also skips the hosts file and the DNS client cache), so a program can still get a different answer. busybox's nslookup is a separate, minimal implementation with its own search-list handling: when a short name such as `kubernetes.default` fails in a pod, retry the full name (`kubernetes.default.svc.cluster.local`) before blaming cluster DNS.

**Next step:** need TTLs, flags or a server-by-server comparison → `dig`. Fails only inside a container → compare its /etc/resolv.conf with the host's. On Windows → `Resolve-DnsName` shows what the OS resolver itself returns.

### resolvectl query — what does this machine resolve, and over which interface?
Match: resolvectl query
Instead of: dig name, ping name
Safety: read-only

**In one line:** `resolvectl query` resolves a name through systemd-resolved, the path most programs on Ubuntu take, and names the network link (interface) whose DNS servers answered.

**Read the command:** `resolvectl query app.example.com`

| Part | Meaning |
|---|---|
| `query` | resolve via systemd-resolved, with its cache, search domains and per-link routing (VPN split DNS) |
| `app.example.com` | the name; an IP address gives a reverse lookup |

**What the output tells you:**

```
app.example.com: 192.0.2.10                    -- link: ens18

-- Information acquired via protocol DNS in 23.4ms.
-- Data is authenticated: no
```

`-- link: ens18` says which interface's servers answered: the split-DNS question in one word. The time exposes a slow resolver. Newer systemd adds a `Data from:` line (cache or network). `authenticated: no` only means DNSSEC was not used.

**Why it is effective:** it answers "what does *this host* get" rather than "what does some DNS server say".

**Compared with `dig` and `ping name`:** dig without `@` also goes through 127.0.0.53 but shows no link and skips the search list; with `@server` it bypasses resolved entirely, which makes dig the better tool for questioning one server. ping shows the chosen address, then only ICMP.

**Trap:** the answer may come from resolved's cache, so right after a DNS change you can still see the old address until the TTL runs out. Not every program takes this path: containers have their own resolv.conf and some runtimes (the JVM) cache names themselves. `getent ahosts name` follows /etc/nsswitch.conf exactly as libc programs do.

**Next step:** wrong link or no answer → `resolvectl status`. Old answer → `resolvectl flush-caches` and query again. Fails here but `dig @192.0.2.53 name` works → resolved's settings (`resolvectl status`, `resolvectl log-level debug`).

### resolvectl status — which DNS servers and domains does each interface use?
Match: resolvectl status
Instead of: cat /etc/resolv.conf
Safety: read-only

**In one line:** on Ubuntu, /etc/resolv.conf usually says only `nameserver 127.0.0.53` (the local stub); `resolvectl status` shows the real upstream servers, the search and routing domains of every interface (link), and the server in use right now.

**Read the command:** `resolvectl status ens18`

| Part | Meaning |
|---|---|
| `status` | global DNS settings plus those of each link |
| `ens18` | only this link (for VPNs: `wg0`, `vpn0`, `tailscale0`) |

**What the output tells you:**

```
Link 2 (ens18)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53 192.0.2.54
        DNS Domain: corp.example.com
```

`DNS Servers` came from DHCP, netplan or the VPN; `Current DNS Server` is the one in use (resolved moves on after failures). `DNS Domain` lists search domains; an entry starting with `~` is routing-only: names under it go to this link's servers. `+DefaultRoute` means names matching no routing domain may be sent here too. The `Global` section shows servers from /etc/systemd/resolved.conf.

**Why it is effective:** it explains VPN and split-horizon trouble: which interface's servers handle `corp.example.com`, and whether a VPN link is also receiving every public lookup.

**Compared with `cat /etc/resolv.conf`:** on a stub host it shows only 127.0.0.53 and the search line. On hosts and containers without systemd-resolved, resolv.conf is the full truth.

**Trap:** names that match no routing domain go to *all* `+DefaultRoute` links and the first successful reply wins, so two links with different views of a zone give answers that change between queries. `Current DNS Server` may be a slow server resolved has not yet abandoned: test each one with `dig @server`.

**Next step:** wrong servers or domains → fix them permanently in netplan, NetworkManager or the VPN client; test live with `resolvectl dns` / `resolvectl domain`. Right servers, wrong answer → `dig @192.0.2.53 name` against each.

### resolvectl dns / domain / flush-caches — change or reset the resolver at runtime
Match: resolvectl
Instead of: editing /etc/resolv.conf
Safety: changes state: `dns`, `domain`, `default-route`, `revert`, `flush-caches` and `log-level` act on the running resolver (run with sudo; runtime only) · `statistics` and `monitor` only read

**In one line:** the resolvectl subcommands that act: point an interface at other DNS servers, send a domain to the VPN, empty the cache or log every lookup, all live and without restarting networking.

**Read the command:** `sudo resolvectl domain vpn0 '~internal.example'`

| Part | Meaning |
|---|---|
| `domain vpn0 '~internal.example'` | names under internal.example go to vpn0's servers; `~` = routing-only (not appended to short names), quoted so the shell leaves it alone |
| `dns vpn0 192.0.2.254` | set vpn0's DNS servers |
| `default-route vpn0 false` | send no other names to vpn0 (split DNS) |
| `revert ens18` | drop the runtime DNS settings of that link |
| `flush-caches` | empty resolved's cache, cached "does not exist" answers included |
| `statistics` | cache size, hits and misses, transactions |
| `log-level debug`, `monitor` | log every lookup to the journal; `monitor` (newer systemd) streams lookups live |

**What the output tells you:** the setters print nothing on success. Prove the effect: `resolvectl status vpn0` lists the new server and domain, and `resolvectl query git.internal.example` now ends in `-- link: vpn0`.

**Why it is effective:** you test a DNS fix on one interface in seconds and undo it with `revert`, before touching netplan or the VPN profile; `flush-caches` removes stale and negative answers after you fix a record.

**Compared with editing /etc/resolv.conf:** on Ubuntu that file is generated (a link to resolved's stub file); edits vanish at the next network change, and a hand-written `nameserver` line bypasses per-link routing.

**Trap:** these change DNS for every program on the host at once, and only until the link is reconfigured (VPN reconnect, `networkctl reconfigure`) or the host reboots, so yesterday's fix can silently disappear. `flush-caches` clears only this machine; other clients and upstream resolvers keep the old answer until its TTL ends. Set `log-level info` again when done.

**Next step:** it works → make it permanent in netplan (`nameservers:`), NetworkManager or the VPN client. Old answer after a flush → the upstream caches it too: compare `dig @192.0.2.53 name` with the authoritative server.

### rndc / unbound-control — flush, reload or re-sync a DNS server you run
Match: rndc, unbound-control
Instead of: systemctl restart named
Safety: changes state: flushes cache entries, reloads config and zones, re-transfers or freezes zones · `rndc status` only reads · needs root (control key)

**In one line:** `rndc` controls a running BIND server and `unbound-control` a running Unbound: reload, forget cached names or re-fetch a zone, without a restart.

**Read the command:** `sudo rndc flushname www.example.com`

| Part | Meaning |
|---|---|
| `sudo rndc` | talk to named's control channel (127.0.0.1 port 953 by default) with the key in /etc/bind/rndc.key, which ordinary users cannot read |
| `flushname www.example.com` | drop only this name from the cache (`rndc flush` empties it all) |
| `status` | version, zone count, recursive clients; ends with `server is up and running` |
| `reload` | re-read named.conf and changed zone files |
| `retransfer example.com` | on a secondary: copy the zone from the primary now, even if the serial did not change |
| `freeze example.com` … `thaw example.com` | stop dynamic updates and write the journal into the zone file so you can edit it; `thaw` reloads it and resumes updates |
| `unbound-control flush www.example.com`, `flush_bogus` | Unbound: drop that name; drop answers that failed DNSSEC validation |

**What the output tells you:** the actions print little or nothing on success. `rndc: connect failed: 127.0.0.1#953: connection refused` means named is down or has no control channel. Check the result with dig: `dig @127.0.0.1 example.com SOA +short` shows the serial now served.

**Why it is effective:** flushing one name or reloading keeps the rest of the cache warm and the server answering; a restart drops every cached answer and causes a burst of upstream lookups.

**Compared with `systemctl restart named`:** it applies changes too, but the server stops answering briefly, loses its cache, and stays down if the new config is broken.

**Trap:** these act on the live server everyone queries. A zone edited without raising the SOA serial reloads on the primary, but secondaries compare serials and keep the old data. Flushing your server does nothing for clients that already cached the answer (browsers, systemd-resolved) until their TTL ends. Never hand-edit a dynamic zone without `freeze`.

**Next step:** reload errors → `named-checkconf`, `named-checkzone`, `journalctl -u named`. Servers disagree → compare `dig @server example.com SOA +short` on each, then `rndc retransfer`. Clients still wrong → `resolvectl flush-caches` there.

### named-checkconf / named-checkzone — will BIND accept this config and zone?
Match: named-checkconf, named-checkzone, unbound-checkconf
Instead of: reloading to see whether it breaks
Safety: read-only · parses files, changes nothing

**In one line:** both parse BIND files exactly as named would and report the first error with file and line, before a reload turns a typo into an outage.

**Read the command:** `named-checkconf && named-checkzone example.com /etc/bind/db.example.com`

| Part | Meaning |
|---|---|
| `named-checkconf` | check /etc/bind/named.conf (the Debian/Ubuntu default) and every file it includes; silent with exit code 0 when all is well |
| `&&` | check the zone only if the config passed |
| `example.com` | the zone's origin: names in the file without a final dot get `.example.com` appended |
| `/etc/bind/db.example.com` | the zone file to load |
| `named-checkconf -z` | also test-load every primary zone the config lists |

**What the output tells you:**

```
zone example.com/IN: loaded serial 2026100401
OK
```

`loaded serial` must be higher than before, or secondaries ignore the change. A failure names the line and the reason (for example `CNAME and other data`) and ends with `not loaded due to errors`.

**Why it is effective:** it catches what makes named refuse a zone (a CNAME beside other records, a missing SOA or NS) or refuse to start (a missing `;`), while the running server keeps serving.

**Compared with reloading to find out:** a reload surfaces the same errors, but only after the server tried, with the details in the journal.

**Trap:** valid is not correct: `www CNAME web01.example.com` without the final dot is legal and silently becomes `web01.example.com.example.com.` Check real answers with `dig @127.0.0.1` after the reload.

**Next step:** OK → `rndc reload`, then dig the changed names and compare the SOA serial on every server. Error → fix the reported line and check again. Related, Unbound: `unbound-checkconf` parses `/etc/unbound/unbound.conf` and its includes, prints `unbound-checkconf: no errors in /etc/unbound/unbound.conf` or the file, line and error, and belongs before the reload: `unbound-checkconf && systemctl reload unbound`.

### curl — what does the web server really answer, and where does the time go?
Match: curl, websocat
Instead of: a browser, ping, telnet host 443
Safety: read-only for GET and HEAD · `-X POST/PUT/DELETE`, `-d` and `-F` send data and can change state · `-k` disables certificate checks

**In one line:** `curl` makes one HTTP(S) request and can show every layer of it: the IP it connected to, the TLS certificate, the headers sent and received, the status code, and a timing breakdown that separates DNS, network, TLS and server time.

**Read the command:** `curl -sv --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/ -o /dev/null 2>&1`

| Part | Meaning |
|---|---|
| `-sv` | `-s` hides the progress bar; `-v` prints each step on stderr: `*` connection and TLS notes, `>` request headers sent, `<` response headers received |
| `--resolve crm.example.com:443:192.0.2.10` | for this name **and port**, connect to this IP without asking DNS; SNI, the certificate check and the Host header still use the name |
| `-o /dev/null` | discard the body; the trace and headers remain |
| `2>&1` | shell: send stderr (where `-v` writes) into the pipe, so `grep` can filter it |
| `-I` | send HEAD: response headers only |
| `-w '%{http_code} %{time_total}\n'` | after the transfer, print chosen variables (timing below) |
| `-H 'Host: shop.example.com'` | set the HTTP Host header: picks the vhost on plain HTTP to an IP, but does not change TLS SNI |
| `-k`, `--cacert ca.crt` | `-k` skips certificate verification (diagnosis only); `--cacert` verifies against this CA file instead of the system store |

**What the output tells you:**

```
* Added crm.example.com:443:192.0.2.10 to DNS cache
*   Trying 192.0.2.10:443...
* Connected to crm.example.com (192.0.2.10) port 443
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
*  subject: CN=crm.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
*  SSL certificate verify ok.
> GET / HTTP/2
< HTTP/2 200
< server: Apache/2.4.58 (Ubuntu)
```

The last step that appears is the last layer that worked: a hang at `Trying` then a timeout = filtered port; `Connection refused` = nothing listening (or a REJECT rule); a TLS error names the certificate problem; the `<` status line and `server:`/`via:` headers tell you which program answered. For timing, `-o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n'` prints e.g. `dns=0.004 tcp=0.021 tls=0.068 ttfb=0.912 total=0.915`. Each value counts from the start, so subtract: TLS took 0.047 s and the server thought for 0.84 s, which points at the application, not the network.

**Why it is effective:** one command splits "the site is down" into DNS, TCP, TLS or HTTP, and the timing line splits "slow" the same way. `--resolve` tests one particular server (a new backend, Apache on 444, one node behind a load balancer) under its real name before DNS points there; `curl https://192.0.2.10/` cannot, because without the name you get the default certificate and the default vhost.

**Compared with a browser, `ping` and `telnet host 443`:** a browser hides the IP it used, caches redirects and HSTS, and retries quietly. ping proves only that the IP answers ICMP; telnet or `nc -zv` prove only that the port accepts connections. None of them checks the certificate or shows the HTTP status.

**Trap:** `-H 'Host: x'` with an `https://` URL changes only the HTTP header: TLS still takes SNI from the URL (and sends none for an IP), so you get the wrong certificate; use `--resolve`, whose port must match the URL's. `-k` hides exactly the error your users will see. curl exits 0 even on a 404 or 500 unless you add `-f`, and `-s` alone also hides error messages (use `-sS` in scripts). Without `-L`, a 301 or 302 is the answer, not a failure. `-X POST`, `-d` and `-F` really submit data.

**Next step:** refused or timeout → `ss -tlnp` on the server, then firewalls. TLS error → `openssl s_client -connect IP:443 -servername name`. 502 or 504 → curl the backend directly from the proxy host and read the proxy log. High `ttfb` → the application or database; high `tcp` → the network (`mtr`). Related: `websocat wss://host/socket` (a separate tool, if installed) opens a WebSocket: each line you type is sent as a message and replies are printed. If the upgrade fails, usually a proxy that does not pass the `Upgrade` and `Connection` headers, it reports the HTTP status it got instead of `101 Switching Protocols`.

### wget — can this container reach that URL?
Match: wget
Instead of: —
Safety: read-only with `-O-` or `-O /dev/null` · without `-O` it saves the page as a file in the current directory

**In one line:** `wget` is the HTTP client found where curl is missing (busybox and alpine images, Traefik's included), so it is the quick way to test a URL from *inside* a container's network.

**Read the command:** `docker exec dokploy-traefik wget -qO- -T 5 http://192.0.2.10:81/ >/dev/null; echo "exit=$?"`

| Part | Meaning |
|---|---|
| `docker exec dokploy-traefik` | run inside the Traefik container: its network, DNS and routes, the path the proxy really uses |
| `-q` | quiet: no progress output |
| `-O-` | write the body to stdout (`-O /dev/null` discards it, `-O file` saves it) |
| `-T 5` | give up after 5 seconds without progress |
| `http://192.0.2.10:81/` | Apache on its new port, addressed by the host's IP |
| `>/dev/null; echo "exit=$?"` | drop the body and print the exit code: 0 = a successful response |
| `-S` | print the response headers (to stderr), as in `wget -qS -O /dev/null URL 2>&1` |

**What the output tells you:** with `-q` only errors appear. busybox wget says `bad address 'api'` (no DNS answer in this container), `can't connect to remote host (192.0.2.10): Connection refused` (nothing listening on an address the container can reach), `download timed out`, or `server returned error: HTTP/1.1 502 Bad Gateway`.

**Why it is effective:** when Traefik returns 502, the question is whether its container can reach the backend at all; testing from inside it separates a network or firewall problem from a problem in Apache.

**Trap:** without `-O`, wget saves `index.html`, `index.html.1`… wherever you stand. busybox wget is a minimal re-implementation with fewer options, and it exits 1 for every failure; GNU wget uses distinct codes (4 network failure, 5 TLS verification, 8 an HTTP error status).

**Next step:** `bad address` → container DNS (Docker network, CoreDNS). Refused → `ss -tlnp` on the host: is Apache bound to 127.0.0.1 only? Timeout → the host firewall between the Docker bridge and the port. Need timings or TLS detail → curl from a netshoot-style debug container.

### openssl s_client — which certificate does this server send for this name, and does it verify?
Match: openssl s_client
Instead of: the browser padlock, curl -k
Safety: read-only · opens one TLS connection

**In one line:** `openssl s_client` performs a TLS handshake with any host and port and shows what the server sends for a given name (SNI): the certificate, the chain, and whether this machine can verify it.

**Read the command:** `openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName`

| Part | Meaning |
|---|---|
| `-connect app.example.com:443` | where to connect; an IP (`192.0.2.10:443`) tests one particular server or backend |
| `-servername app.example.com` | the SNI name, which picks the certificate on a shared IP (Traefik, Apache vhosts). Current OpenSSL sends a `-connect` hostname as SNI by itself, never an IP, so always pass it |
| `</dev/null` | no input, so s_client hangs up after the handshake instead of waiting for you to type (`echo |` in front does the same) |
| `2>/dev/null` | hide the `depth=… verify return:` lines on stderr |
| `| openssl x509 -noout -subject -issuer -dates -ext subjectAltName` | hand the leaf certificate to x509: no PEM dump (`-noout`), just subject, issuer, validity dates and the SAN list |
| `-showcerts` | print every certificate the server sends, not only the first |
| `-verify_hostname app.example.com` | also check that the certificate is valid for this name |
| `-CAfile ca.crt` | verify against this CA file (your private root) instead of the system store |

**What the output tells you:** (with `-showcerts`, trimmed)

```
Certificate chain
 0 s:CN = app.example.com
   i:C = US, O = Let's Encrypt, CN = R11
 1 s:C = US, O = Let's Encrypt, CN = R11
   i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
---
Verify return code: 0 (ok)
```

`0` is the leaf, `s:` its subject, `i:` its issuer; each `i:` should match the next `s:`. A lone `0` means the server does not send its intermediate. Return codes: `0` ok; `10` expired (or a wrong clock); `18` self-signed leaf, such as `TRAEFIK DEFAULT CERT`; `19` or `20` the chain ends at a CA this machine does not trust (a private CA), or an intermediate is missing; `21` only the leaf was sent; `62` name mismatch (with `-verify_hostname`).

**Why it is effective:** it tests one IP and one name at a time, so you can compare what Traefik and Apache each serve for `shop.example.com`, and it exposes missing intermediates that browsers paper over.

**Compared with the browser padlock and `curl -k`:** a browser verifies with its own trust store and fetches missing intermediates by itself; `curl -k` turns verification off. Plain `curl -v` is a fine quick check (subject, issuer, expiry, verify ok) but does not print the chain as sent.

**Trap:** connect to an IP without `-servername` and you get the default certificate, then "fix" a certificate that was never wrong. Code `0` does not cover the name unless you add `-verify_hostname`. The verdict uses *this* machine's trust store, not your users' or a container's.

**Next step:** wrong certificate for the name → find who serves it (`apache2ctl -S`, the Traefik routers API, `curl --resolve`). Missing intermediate → serve the full chain (`fullchain.pem`, not `cert.pem`). Private CA untrusted → `update-ca-certificates` on that client. Close to expiry → `certbot certificates`, `certbot renew --dry-run`.

### openssl x509 — what is in this certificate: names, issuer, dates, key?
Match: openssl x509
Instead of: the browser certificate viewer
Safety: read-only · `x509 -req … -out` (signing a CSR with your CA) writes a new certificate

**In one line:** `openssl x509` decodes a certificate file, or one piped in from s_client, and prints only the fields you ask for: who it is for, who signed it, when it expires, which names it covers and which key it holds.

**Read the command:** `openssl x509 -in /data/cert/harbor.crt -noout -subject -issuer -dates -ext subjectAltName,basicConstraints,extendedKeyUsage`

| Part | Meaning |
|---|---|
| `-in /data/cert/harbor.crt` | the PEM file to read; without `-in` x509 reads stdin (from s_client) |
| `-noout` | do not print the encoded certificate itself |
| `-subject -issuer` | who the certificate is for, and which CA signed it |
| `-dates` | `notBefore` and `notAfter`; `-enddate` prints only the expiry |
| `-ext subjectAltName,basicConstraints,extendedKeyUsage` | the names it is valid for, whether it is a CA, and what it may be used for |
| `-checkend 2592000` | exit 1 if it expires within 2,592,000 s (30 days), else 0: for scripts and monitoring |
| `-serial`, `-fingerprint -sha256` | identify one exact certificate, to compare a file with what a server sends |
| `-modulus`, `-pubkey` | print the public key (`-modulus` for RSA only); hash it and compare with the private key's to prove they belong together |

**What the output tells you:**

```
subject=CN = harbor.example.com
issuer=CN = Example Lab Intermediate CA 2026
notBefore=Oct  1 00:00:00 2026 GMT
notAfter=Nov  2 00:00:00 2027 GMT
X509v3 Subject Alternative Name:
    DNS:harbor.example.com, DNS:harbor, IP Address:10.0.1.30
X509v3 Basic Constraints: critical
    CA:FALSE
X509v3 Extended Key Usage:
    TLS Web Server Authentication
```

The SAN list is the truth: clients check the name against it and browsers ignore the CN; clients that connect by IP need an `IP Address:` entry. `CA:FALSE` is right for a server; your root and intermediates must say `CA:TRUE`. An issuer starting with `(STAGING)` is a Let's Encrypt test certificate nobody trusts.

**Why it is effective:** it reads the files a server *will* load (Apache, Traefik, `/etc/kubernetes/pki`, Wazuh), so a missing name, a wrong issuer or a near expiry shows up before a restart or a client finds it.

**Compared with the browser certificate viewer:** the same fields, but only for the one certificate that browser received; it cannot read files or compare a certificate with its key.

**Trap:** `fullchain.pem` holds several certificates, but x509 shows only the first (the leaf). `-checkend` answers through its exit code (`$?`). When you sign with `x509 -req`, the CSR's SANs are not copied unless you pass `-extfile` or `-copy_extensions copyall`, and a certificate without SANs is rejected by browsers and by Go-based tools such as Docker, Kubernetes and Traefik.

**Next step:** name missing from the SAN → reissue with every name. Expiring → `certbot certificates`, `certbot renew --dry-run`. Key hashes differ → the vhost points at the wrong key file. Served serial differs from the file → the server was not reloaded after renewal.

### openssl verify / req / genpkey — check a chain offline, make keys, CSRs and test certificates
Match: openssl
Instead of: —
Safety: `verify`, `rsa`/`pkey` key checks and `md5` only read · `req`, `genpkey`, `genrsa` and `rand` write keys, requests or certificates (protect `.key` files) · `s_server` opens a listening port

**In one line:** the rest of the openssl toolbox the handbook uses: verify a chain without a server, create keys, CSRs and lab certificates, prove a key matches a certificate, and run a throwaway TLS server.

**Read the command:** `openssl verify -CAfile root.crt -untrusted int.crt harbor.crt`

| Part | Meaning |
|---|---|
| `verify` | build and check the chain for a certificate file, offline |
| `-CAfile root.crt` | the root to trust for this check (your private CA) |
| `-untrusted int.crt` | intermediates that may be used to build the chain but are not trusted on their own |
| `harbor.crt` | the certificate to check |
| `req -new -nodes -newkey rsa:2048 -subj '/CN=app.lab.example.com' -keyout app.key -out app.csr` | new key plus signing request; `-nodes` = key not encrypted; `-x509 -days 30 -addext 'subjectAltName=DNS:…'` makes a self-signed certificate instead |
| `genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out root.key` | new EC P-256 private key (`genrsa -out x.key 2048` for RSA) |
| `rsa -noout -modulus -in key.pem | openssl md5` | short hash of an RSA key; equal to the certificate's (`x509 -noout -modulus`) only if they belong together |
| `s_server -accept 8443 -cert app.crt -key app.key -www` | a test TLS server on port 8443, for labs |

**What the output tells you:** `harbor.crt: OK` means a chain to `root.crt` was built and every signature and date checked. A failure names the reason and depth, for example `error 20 at 0 depth lookup: unable to get local issuer certificate` (the issuer is in neither file) or `error 10 at 0 depth lookup: certificate has expired`.

**Why it is effective:** it tests the files themselves, with no server, DNS or proxy in between, so a renewed CA or a new intermediate can be proven before deployment.

**Trap:** `verify` does not check the host name, and `-untrusted int.crt` makes it pass even if the server will not send `int.crt`: confirm the live chain with `s_client -showcerts`. `-nodes` keys are unencrypted secrets: `chmod 600`, never commit them. The md5 is only a quick comparison, not security.

**Next step:** OK offline but clients fail → what the server sends (`openssl s_client -showcerts`) and the client's trust store (`update-ca-certificates`). Error 20 → wrong or missing intermediate or root. Key hashes differ → find the matching key or reissue.

### update-ca-certificates — make this machine trust a private CA
Match: update-ca-certificates
Instead of: curl -k, insecure-registry settings
Safety: changes state: rebuilds the system trust bundle (needs root) · every program using it will trust the added CA

**In one line:** after you copy a CA certificate into `/usr/local/share/ca-certificates/`, `update-ca-certificates` rebuilds the trust store that curl, wget, apt, git and most programs on Debian/Ubuntu read.

**Read the command:** `sudo update-ca-certificates`

| Part | Meaning |
|---|---|
| reads | the CAs enabled in /etc/ca-certificates.conf, plus every `*.crt` under /usr/local/share/ca-certificates/ (PEM text, name ending in `.crt`) |
| writes | /etc/ssl/certs/ca-certificates.crt (one bundle) and hashed links in /etc/ssl/certs |
| `--fresh` | delete all links and rebuild from scratch: use it after removing a CA file |

**What the output tells you:**

```
Updating certificates in /etc/ssl/certs...
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
```

`1 added` is the line that matters. `0 added` means the file was not picked up: check the `.crt` extension, the directory and that it is PEM. A `rehash: warning: skipping ca-certificates.crt` line is harmless.

**Why it is effective:** one trusted root fixes every client of the system store, without `-k` or insecure flags that would also accept a forged certificate.

**Compared with `curl -k` and insecure-registry settings:** they switch the check off for one tool, accept anyone in the middle, and the next tool fails again.

**Trap:** this changes trust for the whole machine, so add only CAs you control. Not every program reads this store: Python requests (certifi), Node.js, Java, Firefox and every container image have their own, and the Docker daemon wants `/etc/docker/certs.d/REGISTRY/ca.crt` or a restart. Running programs keep the bundle they loaded at start: restart them.

**Next step:** verify with the program that failed, and with `openssl s_client -connect host:443 -servername host` (expect `Verify return code: 0`). Failing inside a container → add the CA in the Dockerfile and run `update-ca-certificates` at build time.

### certbot certificates — which certificates does certbot manage here, and when do they expire?
Match: certbot certificates
Instead of: ls /etc/letsencrypt/live
Safety: read-only · needs root to read /etc/letsencrypt

**In one line:** lists every certificate certbot manages on this host: its name, the domains it covers, its expiry, and the file paths a web server should use.

**Read the command:** `sudo certbot certificates 2>/dev/null | grep -E 'Certificate Name|Domains|Expiry'`

| Part | Meaning |
|---|---|
| `sudo` | /etc/letsencrypt is readable by root only |
| `certificates` | list every certificate (lineage) certbot knows |
| `2>/dev/null` | drop the "Saving debug log" line on stderr |
| `grep -E '…'` | keep the three lines per certificate that matter |

**What the output tells you:**

```
  Certificate Name: shop.example.com
    Domains: shop.example.com www.shop.example.com
    Expiry Date: 2026-12-20 08:14:02+00:00 (VALID: 76 days)
    Certificate Path: /etc/letsencrypt/live/shop.example.com/fullchain.pem
    Private Key Path: /etc/letsencrypt/live/shop.example.com/privkey.pem
```

`Certificate Name` is what `--cert-name` refers to; `Domains` is the SAN list; `INVALID: EXPIRED` or `INVALID: TEST_CERT` (a staging certificate) need action. Web servers should point at the `live/` paths, which always lead to the newest version.

**Why it is effective:** it is the inventory to take before moving ports 80/443 from Apache to Traefik or Dokploy: which names certbot still renews here, and which will move to Traefik's own ACME. Two systems issuing for one name means duplicate certificates, rate limits and doubt about which one is served.

**Compared with `ls /etc/letsencrypt/live`:** directory names only; a directory called `shop.example.com` may also cover `api.example.com`, and there is no expiry.

**Trap:** only certbot's certificates appear: Traefik's `acme.json`, Dokploy and copied files do not. `VALID` proves neither that renewal works (`renew --dry-run`) nor that the server loaded the renewed file: compare `openssl x509 -noout -serial` of the file with what `openssl s_client` receives.

**Next step:** expiring, or ports about to change → `certbot renew --dry-run`. A name Traefik now serves → disable the Apache `-le-ssl` site, then `certbot delete --cert-name`.

### certbot renew --dry-run — will renewal actually work today?
Match: certbot renew
Instead of: waiting for the renewal timer
Safety: `--dry-run` saves no certificates and uses the staging CA, but runs pre/post hooks and, with the apache or nginx plugin, briefly changes and reloads the web server · without it, renews for real

**In one line:** rehearses the renewal of every certificate certbot manages, with the full challenge against Let's Encrypt's staging server, so a broken renewal shows up weeks before the expiry instead of on the day.

**Read the command:** `sudo certbot renew --dry-run 2>&1 | tail -n 5`

| Part | Meaning |
|---|---|
| `renew` | renew due certificates, each with the settings saved in /etc/letsencrypt/renewal/NAME.conf (authenticator, webroot, hooks) |
| `--dry-run` | simulate every certificate, due or not, against the staging server; save nothing |
| `2>&1 | tail -n 5` | keep the verdict at the end |
| `--cert-name app.example.com` | only this certificate |

**What the output tells you:**

```
Certbot failed to authenticate some domains (authenticator: apache). The Certificate Authority reported these problems:
  Domain: shop.example.com
  Type:   unauthorized
  Detail: 203.0.113.10: Invalid response from http://shop.example.com/.well-known/acme-challenge/x1Y2z3: 404
Failed to renew certificate shop.example.com with error: Some challenges have failed.
All simulated renewals failed. The following certificates could not be renewed:
  /etc/letsencrypt/live/shop.example.com/fullchain.pem (failure)
```

Success ends with `Congratulations, all simulated renewals succeeded`. `authenticator:` says how certbot tried; `Type`/`Detail` say what Let's Encrypt saw: `unauthorized … 404` = something answered port 80 but not with the challenge file; `connection` or `Timeout during connect` = port 80 is unreachable from the internet; `dns` = the name does not resolve correctly.

**Why it is effective:** it tests everything renewal depends on (DNS records, port 80 reaching the right program, the authenticator, the hooks) today, without touching live certificates or production rate limits.

**Compared with waiting for the timer:** certbot's timer renews quietly in the background and logs to /var/log/letsencrypt/letsencrypt.log; if it fails, you find out when the certificate expires.

**Trap:** the authenticator is saved per certificate. After Apache moves to 81/444, a certificate with `authenticator = apache` still has the challenge served by Apache while Let's Encrypt connects to port 80, where Traefik answers 404: the failure above. A dry run executes pre- and post-hooks (a pre-hook that stops a service really stops it) but not deploy hooks, so a broken deploy hook stays untested.

**Next step:** 404 or timeout → `curl -sv http://name/.well-known/acme-challenge/test` to see who answers on port 80, then route that path, switch the method (`certbot reconfigure --webroot`) or let Traefik issue the name. Success → check the timer with `systemctl list-timers`.

### certbot certonly / delete / --apache — issue, install or remove Let's Encrypt certificates
Match: certbot
Instead of: hand-editing /etc/letsencrypt
Safety: changes state: issues certificates (rate-limited), edits Apache vhosts (`--apache`), deletes certificate files (`delete`), rewrites renewal settings (`reconfigure`) · needs root

**In one line:** the certbot subcommands that change things: obtain a certificate (and optionally install it into Apache), change how it renews, or delete it when another system takes the name over.

**Read the command:** `sudo certbot --apache --cert-name app.example.com -d app.example.com -d shop.example.com`

| Part | Meaning |
|---|---|
| no subcommand | `run`: obtain a certificate **and** install it into the web server |
| `--apache` | the Apache plugin answers the HTTP-01 challenge and writes the SSL vhost (`…-le-ssl.conf`) |
| `--cert-name app.example.com` | the certificate (lineage) to create or update |
| `-d app.example.com -d shop.example.com` | every name it must cover; for an existing `--cert-name` this list replaces the old one |
| `certonly --dns-cloudflare --dns-cloudflare-credentials FILE -d '*.example.com'` | obtain only, proving control with a DNS TXT record (DNS-01): the only way to get a wildcard |
| `delete --cert-name shop.example.com` | remove the certificate's files and renewal config; certbot stops renewing it |
| `reconfigure --cert-name www.example.com --webroot --webroot-path /var/www/letsencrypt` | change how future renewals authenticate (newer certbot versions) |

**What the output tells you:** success prints `Successfully received certificate.` with the paths and, for `--apache`, `Successfully deployed certificate for app.example.com to /etc/apache2/sites-available/app.example.com-le-ssl.conf`. Failures use the same `Type`/`Detail` lines as `renew --dry-run`.

**Why it is effective:** certbot keeps the `live/` links, the archive versions and the renewal config consistent; hand edits break renewals in ways you only notice at expiry.

**Compared with hand-editing /etc/letsencrypt:** moving or copying files there breaks the links and the renewal config certbot relies on.

**Trap:** `delete` removes files Apache vhosts may still reference, and Apache then refuses to start (`SSLCertificateFile: file … does not exist or is empty`): `a2dissite` those `-le-ssl` sites first, as the 81/444 move does. `--apache` needs Apache to answer port 80 from the internet, which stops being true after that move. Failed attempts and duplicates hit Let's Encrypt rate limits: rehearse with `--dry-run`. Keep DNS API credential files at `chmod 600`.

**Next step:** after issuing → `certbot certificates`, then `openssl s_client -servername` to see it served. Before deleting → `a2dissite`, `apache2ctl configtest`, reload, then `certbot delete`.

### apache2ctl -S — which vhost answers which name, on which port?
Match: apache2ctl, apachectl, apache2, httpd
Instead of: grep -r ServerName /etc/apache2
Safety: read-only

**In one line:** `apache2ctl -S` parses the whole Apache configuration as the server will and prints the virtual host map: every address and port, every name on it, the default vhost, and the file and line where each is defined.

**Read the command:** `sudo apache2ctl -S`

| Part | Meaning |
|---|---|
| `sudo` | read every included file, as the service does |
| `-S` | the parsed vhost map plus run settings (ServerRoot, PidFile, User); same as `-t -D DUMP_VHOSTS -D DUMP_RUN_CFG` |
| `-M` | loaded modules: are `ssl_module`, `proxy_http_module`, `remoteip_module` really there? |
| `-t -D DUMP_INCLUDES` | every configuration file actually included, in order |
| `-V` | version and build settings, including the MPM (event, prefork) |
| `apachectl`, `httpd -S`, `apache2 -v` | the same tool under other names: `httpd` on RHEL/Rocky; `apache2` is the Debian binary (fine for `-v`) |

**What the output tells you:** (after the move to 81/444)

```
VirtualHost configuration:
*:444                  is a NameVirtualHost
         default server shop.example.com (/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2)
         port 444 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com-le-ssl.conf:2)
         port 444 namevhost api.example.com (/etc/apache2/sites-enabled/api.example.com-le-ssl.conf:2)
*:81                   is a NameVirtualHost
         default server 127.0.1.1 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 81 namevhost 127.0.1.1 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 81 namevhost shop.example.com (/etc/apache2/sites-enabled/shop.example.com.conf:1)
                 alias www.shop.example.com
```

Each block is an address:port. `default server` is the first vhost there: it answers every request whose Host matches no `ServerName`/`ServerAlias`, requests by IP included. `namevhost` lines give each name with its file and line; `alias` lines are ServerAliases. `*:444` means all addresses: reachable from outside unless the firewall says no.

**Why it is effective:** it is Apache's own view after includes and `<IfModule>` blocks, not a guess from grep. One screen answers "which file serves shop.example.com on 444?", "what is the catch-all?" and "is a vhost still on `*:443`?".

**Compared with `grep -r ServerName /etc/apache2`:** grep also finds disabled sites and commented lines, and cannot tell the default vhost or the port a name belongs to. `ss -tlnp` shows apache2 listening on 81 and 444, not the names behind them.

**Trap:** it shows the configuration on disk, not what the running server loaded before your last edit. A name defined twice on one port is served by the first definition only. On Debian/Ubuntu use `apache2ctl`, not bare `apache2 -S`: without /etc/apache2/envvars it fails with `Config variable ${APACHE_RUN_DIR} is not defined`. The AH00558 "fully qualified domain name" warning is harmless.

**Next step:** wrong default → make the intended vhost sort first (`000-…`) or add a catch-all. Name missing → `a2ensite`, `apache2ctl configtest`, reload. Then prove it: `curl -sv -H 'Host: shop.example.com' http://127.0.0.1:81/ -o /dev/null`.

### apache2ctl configtest / graceful — is the config valid before I reload?
Match: apache2ctl configtest, apachectl configtest, apache2ctl graceful, apache2ctl graceful-stop
Instead of: systemctl restart apache2
Safety: `configtest` read-only · `graceful` reloads the configuration · `graceful-stop` stops Apache once in-flight requests finish

**In one line:** `configtest` parses every Apache file and the directives of every loaded module, then prints `Syntax OK` or the first error with its file and line, so a typo never reaches the running server.

**Read the command:** `sudo apache2ctl configtest && sudo systemctl reload apache2`

| Part | Meaning |
|---|---|
| `configtest` | syntax check of the whole configuration (same as `apache2ctl -t`) |
| `&&` | reload only if the test exits 0 |
| `systemctl reload apache2` | graceful reload: new configuration, current requests finish undisturbed |
| `apache2ctl graceful` | the same reload without systemd |
| `apache2ctl graceful-stop` | stop accepting connections, finish in-flight requests, exit: how you hand a port to another program |

**What the output tells you:**

```
AH00526: Syntax error on line 12 of /etc/apache2/sites-enabled/shop.example.com.conf:
Invalid command 'ProxyPass', perhaps misspelled or defined by a module not included in the server configuration
Action 'configtest' failed.
The Apache error log may have more information.
```

`Syntax OK` is the pass. `Invalid command 'X'` nearly always means the module providing X is off: `ProxyPass` → `a2enmod proxy proxy_http`, `RemoteIPHeader` → `remoteip`, `SSLEngine` → `ssl`.

**Why it is effective:** one second of testing replaces an outage: a restart with a broken file stops Apache and leaves every site down until someone fixes it.

**Compared with `systemctl restart apache2`:** a restart drops open connections, and when the start fails the reason sits in `systemctl status apache2` and the journal. Restart only when a reload is not enough, for example after switching the MPM.

**Trap:** `Syntax OK` does not test ports. `Listen 443` while Traefik holds 443 passes, then the (re)start fails with `(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443`: the Apache-versus-Dokploy clash. A valid config can still send a name to the wrong vhost (`apache2ctl -S`). `graceful-stop` really stops Apache: every site on it is down until it starts again.

**Next step:** syntax error → fix the file and line shown. `Invalid command` → `a2enmod` the module. Pass → reload, then `systemctl status apache2` and a `curl` per site. Address in use → `ss -tlnp 'sport = :443'` names the program holding the port.

### a2enmod / a2ensite / a2dissite — switch Apache modules, sites and snippets on or off
Match: a2enmod, a2dismod, a2ensite, a2dissite, a2enconf, a2disconf, a2query
Instead of: ln -s by hand in /etc/apache2/*-enabled
Safety: changes state: creates or removes symlinks in mods-, sites- and conf-enabled · no effect until a reload (restart for MPM changes) · needs root

**In one line:** Debian/Ubuntu helpers that enable or disable Apache modules, sites and configuration snippets by managing the `*-enabled` symlinks Apache actually loads.

**Read the command:** `sudo a2ensite 000-catchall && sudo apache2ctl configtest && sudo systemctl reload apache2`

| Part | Meaning |
|---|---|
| `a2ensite 000-catchall` | link sites-available/000-catchall.conf into sites-enabled (name without `.conf`); `000-` sorts first, so it becomes its port's default vhost |
| `&& apache2ctl configtest && systemctl reload apache2` | test, then apply: the link changes nothing until Apache reloads |
| `a2dissite shop.example.com-le-ssl` | remove the link; the file stays in sites-available |
| `a2enmod proxy proxy_http headers ssl remoteip` | enable modules (their `.load` and `.conf` files) plus the modules they depend on |
| `a2dismod mpm_prefork && a2enmod mpm_event` | swap the MPM: only one may be enabled, and it needs a restart |
| `a2enconf remoteip`, `a2disconf` | the same for snippets in conf-available |
| `a2query -M`, `a2query -s` | show the enabled MPM; list the enabled sites |

**What the output tells you:**

```
Enabling site 000-catchall.
To activate the new configuration, you need to run:
  systemctl reload apache2
```

`a2enmod` also prints `Considering dependency …` and asks for a restart. `already enabled` is harmless; `ERROR: Site X does not exist!` means no `X.conf` in sites-available; `… cannot proceed due to conflicts` names what to disable first (mod_php needs prefork).

**Why it is effective:** the enabled set *is* what Apache loads (apache2.conf includes `mods-enabled/*.load`, `*.conf` and `sites-enabled/*.conf`), and the helpers resolve dependencies and conflicts.

**Compared with `ln -s` by hand:** it works, but without dependency handling, and a link not ending in `.conf` is silently ignored.

**Trap:** `Enabling site` is not live until the reload. Disabling a site does not free its port: `Listen` lines are in ports.conf, so moving to 81/444 means editing ports.conf *and* every `<VirtualHost>`. Disable the site that served a name and the port's default vhost silently takes its requests.

**Next step:** `apache2ctl -S` for the new map → `apache2ctl configtest` → `systemctl reload apache2` (restart for MPM changes) → `curl -H 'Host: name' http://127.0.0.1:81/`.

### nginx -t / -T — is the nginx config valid, and what does it really contain?
Match: nginx
Instead of: systemctl restart nginx
Safety: `-t`, `-T`, `-V` read-only · `-s reload` / `-s quit` signal the running server

**In one line:** `nginx -t` tests the configuration before a reload; `nginx -T` tests it and prints the complete effective configuration, every included file in order, as one stream you can search.

**Read the command:** `sudo nginx -T 2>/dev/null | grep -nE '^\s*(server_name|listen|root|proxy_pass|fastcgi_pass|access_log|error_log)\b|# configuration file'`

| Part | Meaning |
|---|---|
| `sudo` | read every file and open the logs, as the service does |
| `-T` | test, then print all configuration files, each headed `# configuration file /path:` |
| `2>/dev/null` | drop the test result lines (stderr) |
| `grep -nE '…'` | with line numbers, keep the lines that map names and ports to roots and backends, plus the file headers |
| `-t` | test only: syntax, and that referenced files (certificates, logs) open |
| `-V` | version, build options and compiled-in modules (`--with-http_realip_module`…) |
| `-s reload`, `-s quit` | tell the running master to reload, or to stop after current requests |

**What the output tells you:** `-t` prints `syntax is ok` and `test is successful`, or a line such as `nginx: [emerg] unknown directive "proxy_pas" in /etc/nginx/sites-enabled/app:14`. In the `-T` dump each `listen` and `server_name` sits under the header of its file.

**Why it is effective:** if a reload's new configuration is invalid, nginx keeps running on the old one, so `-t` then reload is a safe change; `-T` reveals forgotten includes, such as a stray conf.d file that also claims a name.

**Compared with `systemctl restart nginx`:** a restart with a broken file stops nginx and does not bring it back.

**Trap:** `-t` does not bind ports, so `bind() to 0.0.0.0:443 failed (98: Address already in use)` appears only at start. The dump is what is on disk, not what the running master loaded. Without `default_server`, the first server block on a port answers unknown names. `-s quit` stops nginx for every site it serves.

**Next step:** error → fix the file and line shown. OK → `systemctl reload nginx`, then `curl -H 'Host: name' http://127.0.0.1/`. Missing module → `nginx -V`.

### haproxy -c / caddy validate — will this proxy accept its config?
Match: haproxy, caddy, traefik
Instead of: restarting the proxy to find out
Safety: read-only · checks the configuration or prints the version

**In one line:** the "test before reload" step for the other proxies: `haproxy -c` and `caddy validate` load the configuration as a start would, without serving traffic. Traefik has no offline check; you read its version and its API instead.

**Read the command:** `sudo haproxy -c -f /etc/haproxy/haproxy.cfg`

| Part | Meaning |
|---|---|
| `-c` | check mode: parse the configuration and exit before binding any port; exit code 0 = valid |
| `-f /etc/haproxy/haproxy.cfg` | the configuration to check |
| `haproxy -v` | version and release date |
| `caddy validate --config /etc/caddy/Caddyfile` | load and provision the config without running it; a file named Caddyfile is adapted automatically |
| `traefik version` | Traefik's version, run inside its container (`docker exec traefik traefik version`) |

**What the output tells you:** HAProxy prints `Configuration file is valid`, or `[ALERT]` lines with file and line ending in `Fatal errors found in configuration.`; `[WARNING]` lines do not block but deserve a read. Caddy ends with `Valid configuration` or names the directive that failed. For Traefik, `curl -s http://127.0.0.1:8080/api/http/routers` lists each router's `status` and any `error`.

**Why it is effective:** one broken line in a shared proxy takes down every site behind it; a one-second check replaces that gamble.

**Compared with restarting to find out:** the restart answers too, by failing, with every site down.

**Trap:** valid is not working: backends can be down, and Caddy can still fail to obtain a certificate at runtime. Neither check binds ports, so `address already in use` appears only at start. A Traefik router with a bad rule or a missing service simply serves nothing; only the API and the log say why.

**Next step:** valid → `systemctl reload haproxy` / `systemctl reload caddy`, then curl through the proxy with `-H 'Host: name'`. Traefik → the routers API and `docker logs traefik`.

### php-fpm8.3 -t / gunicorn — is the app server behind the web server healthy?
Match: php-fpm8.3, gunicorn
Instead of: systemctl restart php8.3-fpm
Safety: read-only

**In one line:** Apache and nginx hand PHP requests to PHP-FPM (and Python apps to gunicorn) over a socket; `php-fpm8.3 -t` checks FPM's own configuration, the first thing to rule out when PHP sites return 502 or 503.

**Read the command:** `sudo php-fpm8.3 -t`

| Part | Meaning |
|---|---|
| `php-fpm8.3` | the FPM binary for PHP 8.3 (the service is `php8.3-fpm`) |
| `-t` | test php-fpm.conf and every pool file in /etc/php/8.3/fpm/pool.d/, then exit |
| `sudo` | read all pool files, as the service does |

**What the output tells you:** `NOTICE: configuration file /etc/php/8.3/fpm/php-fpm.conf test is successful`, or an `ERROR:` naming the file and setting. At run time the FPM log (/var/log/php8.3-fpm.log) holds the usual 502 cause: `WARNING: [pool www] server reached pm.max_children setting (5), consider raising it`.

**Why it is effective:** a PHP site fails at one of three points: FPM will not start (config), FPM runs but every worker is busy (max_children), or the web server cannot reach the socket (path, permissions). The test rules out the first in a second.

**Compared with restarting FPM:** a restart with a broken pool file leaves FPM down, and every PHP site behind it returns 502 or 503.

**gunicorn** is the Python counterpart (Django, Flask) behind a proxy; the handbook only looks for it in service lists. Its `[CRITICAL] WORKER TIMEOUT` log line means a request outlived the worker timeout (30 s by default) and was killed, which the proxy reports as 502.

**Trap:** `test is successful` says nothing about capacity or the socket: compare `listen =` in the pool with the socket path in the vhost (`/run/php/php8.3-fpm.sock`) and its `listen.owner`. With several PHP versions installed, test the one the vhost uses.

**Next step:** config error → fix the reported pool file. Test passes but 502 → FPM log, then the web server's error log; `ss -xlp | grep php` shows whether the socket exists. Apply changes with `systemctl reload php8.3-fpm`.

### ab / hey — how does this URL behave under N concurrent requests?
Match: ab, hey
Instead of: a loop of curl
Safety: generates load: can slow or break the target and trip rate limits and alerts · only against systems you own

**In one line:** `ab` (ApacheBench) and `hey` fire many requests at one URL at a fixed concurrency and summarise throughput, errors and latency percentiles: the quickest way to see a server or proxy start failing under parallel load.

**Read the command:** `ab -n 300 -c 30 -H 'Host: who.lab.example.com' http://127.0.0.1/`

| Part | Meaning |
|---|---|
| `-n 300` | 300 requests in total |
| `-c 30` | 30 in flight at any moment |
| `-H 'Host: who.lab.example.com'` | extra header: picks the vhost or Traefik router while connecting to 127.0.0.1 |
| `http://127.0.0.1/` | the URL; ab needs a path, at least `/` |
| `hey -z 30s -c 50 https://staging.example.com/health` | hey: run 30 s (`-z`) with 50 concurrent workers; `-n` sets a request count instead |

**What the output tells you:** (ab, trimmed)

```
Complete requests:      300
Failed requests:        0
Non-2xx responses:      12
Requests per second:    412.37 [#/sec] (mean)
Percentage of the requests served within a certain time (ms)
  50%     61
  99%    240
```

`Non-2xx responses` are server answers such as 502, 503 or 429. `Failed requests` are connection errors or, misleadingly, responses whose length differs from the first (normal for dynamic pages; the breakdown says `Length:`). The percentiles show the tail an average hides. hey prints `Requests/sec`, a latency distribution and a `Status code distribution`.

**Why it is effective:** problems that need concurrency (worker and connection limits, backends queueing) never appear in a single request.

**Compared with a loop of curl:** one request at a time measures one user's latency, not behaviour under parallel load.

**Trap:** the load is real: on a shared server it slows every site. ab is single-threaded and speaks HTTP/1.0 without keep-alive unless you add `-k`, so every request opens a new connection and the generator may be the bottleneck. Testing via 127.0.0.1 skips the network and TLS. A fast run full of 502s or 429s is not a fast server.

**Next step:** errors from some concurrency on → server limits (Apache `MaxRequestWorkers`, FPM `pm.max_children`, proxy timeouts) and their logs. Sustained runs with percentiles → `wrk --latency`. User journeys → `k6`.

### wrk — throughput and tail latency under sustained load
Match: wrk
Instead of: ab
Safety: generates heavy load from little CPU · only against systems you own

**In one line:** `wrk` keeps a fixed number of keep-alive connections busy for a set time from several threads, and reports requests per second and, with `--latency`, the latency percentiles.

**Read the command:** `wrk -t4 -c100 -d30s --latency https://staging.example.com/health`

| Part | Meaning |
|---|---|
| `-t4` | 4 threads (about the load generator's CPU cores) |
| `-c100` | 100 open connections in total, shared by the threads |
| `-d30s` | run for 30 seconds |
| `--latency` | print the latency distribution (50/75/90/99 %) |

**What the output tells you:**

```
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    24.31ms   12.07ms 312.55ms   88.41%
  Latency Distribution
     50%   21.87ms
     99%   71.92ms
  124112 requests in 30.03s, 98.41MB read
  Socket errors: connect 0, read 0, write 0, timeout 12
  Non-2xx or 3xx responses: 310
Requests/sec:   4133.04
```

Read `Requests/sec` together with the 99 % line: p99 climbing while throughput flattens is the saturation point. `Socket errors` are failed or timed-out connections (wrk's default timeout is 2 s); `Non-2xx or 3xx responses` are errors that still count in `Requests/sec`.

**Why it is effective:** far more load per CPU than ab, over keep-alive connections like real clients, and it shows the slow tail users feel.

**Compared with `ab`:** a similar summary for a fixed request count from one thread over HTTP/1.0; fine for small, quick checks.

**Trap:** wrk waits for each response before sending the next request on that connection, so when the server stalls it sends less and the percentiles look better than users' reality (coordinated omission). Fast errors inflate `Requests/sec`. Running wrk on the server under test steals its CPU, and the load slows every other site on a shared box.

**Next step:** p99 high, average fine → queueing (worker pools, database connections, CPU throttling): profile during the run, as the handbook does with py-spy. Errors → server logs. Fixed arrival rate or user journeys → `k6`.

### k6 run — does a scripted user journey meet its targets?
Match: k6
Instead of: wrk, ab
Safety: generates load · a script pointed at production can create real data (orders, e-mails, sign-ups)

**In one line:** `k6 run` executes a JavaScript test in which virtual users walk through real flows (log in, browse, check out), checks every response, and passes or fails the run against thresholds you set, so it can gate a CI pipeline.

**Read the command:** `k6 run --vus 200 --duration 10m checkout.js`

| Part | Meaning |
|---|---|
| `run` | execute the test script |
| `--vus 200` | 200 virtual users, each looping over the script's default function |
| `--duration 10m` | for 10 minutes |
| `checkout.js` | the script: requests, `check()`s on responses, and `options` such as thresholds (`http_req_duration: ['p(95)<300']`) and scenarios |

**What the output tells you:** the end-of-test summary lists `http_req_duration` (avg, med, p(90), p(95)), `http_req_failed` (share of failed requests: network errors and, by default, statuses of 400 and above), `checks` (share passed), `http_reqs` and `iterations`. Each threshold shows as passed or failed; any failure makes k6 exit with code 99, which fails the CI job.

**Why it is effective:** it tests what users do, not one URL: a slow login or a failing payment shows up while `/health` stays fast, and thresholds turn "seems OK" into a repeatable pass or fail.

**Compared with `wrk` and `ab`:** raw throughput and latency for one URL, enough for "how much can this endpoint take", but no flows and no content checks.

**Trap:** `--vus` is not a request rate: each virtual user waits for responses (and any `sleep()`), so the rate drops as the server slows and hides overload. For a fixed rate use the `constant-arrival-rate` executor in the script options, as the handbook's health test does. A checkout script run against production places real orders. The k6 machine can saturate first; watch its CPU and network.

**Next step:** a threshold failed → find the slow or failing request (tags, groups), then look server-side (Grafana, logs, slow queries). Rerun the same script before and after each change.
