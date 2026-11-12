# 18 — Web, HTTP & TLS Troubleshooting

Typical symptoms: 4xx/5xx errors, "connection reset", slow responses, TLS
handshake failures, expired certificates, redirects looping.

---

## 1. `curl` — the HTTP swiss army knife

Annotated `curl -v` — each line tells you which layer just succeeded:
```
$ curl -v https://api.example.com/health
* Host api.example.com:443 was resolved.
* IPv4: 203.0.113.20                        ← DNS worked (and THIS is the IP used)
* Connected to api.example.com (203.0.113.20) port 443    ← TCP path open (no firewall block)
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384   ← TLS handshake OK
* Server certificate:
*  subject: CN=api.example.com              ← name matches?
*  expire date: Nov 12 23:59:59 2026 GMT    ← not expired?
*  SSL certificate verify ok.               ← chain trusted
> GET /health HTTP/2                        ← '>' = what we SENT
> Host: api.example.com
< HTTP/2 200                                ← '<' = what came BACK
< content-type: application/json
{"status":"ok"}
```
Whichever step is missing from the output is the layer that failed — resolution,
TCP connect, TLS, or the HTTP exchange itself.

```bash
curl -v https://api.example.com/health          # ★ verbose: DNS→TCP→TLS→request→response
curl -I https://example.com                     # HEAD — headers only
curl -sS https://example.com -o /dev/null -w '%{http_code}\n'   # just the status code
curl -L https://example.com                     # follow redirects
curl -sI https://example.com | grep -i location # where does it redirect?
curl -H "Host: app.example.com" http://10.0.1.20/    # ★ test a vhost by IP —
                                                #   bypasses DNS/LB entirely
curl --resolve app.example.com:443:10.0.1.20 https://app.example.com/
                                                # same, but with real TLS/SNI ★
curl -x http://proxy:3128 https://example.com   # via a proxy
curl --noproxy '*' https://example.com          # ignore proxy env vars
curl -4 / curl -6 https://example.com           # force IPv4/IPv6 (split-stack bugs)
curl --connect-timeout 3 --max-time 10 URL      # fail fast, not hang
curl -X POST -H "Content-Type: application/json" -d '{"a":1}' URL   # POST JSON
curl -u user:pass URL ; curl -H "Authorization: Bearer $TOKEN" URL  # auth
curl -k https://self-signed.local               # skip TLS verify (diagnosis only!)
curl --cacert internal-ca.pem https://internal  # verify with private CA
```

### Latency breakdown — WHERE is it slow? ★
```bash
curl -o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://example.com
```
```
dns=0.523 tcp=0.541 tls=0.799 ttfb=2.410 total=2.591
```
- big `dns` → resolver problem (08-dns.md)
- big `tcp-dns` gap → network RTT/loss (02-network.md)
- big `tls-tcp` gap → handshake (cert chain fetch, OCSP, weak server crypto)
- big `ttfb-tls` gap → **backend is slow** (app/DB — not the network)

### Environment proxies (invisible cause of "curl works, app doesn't" & vice versa)
```bash
env | grep -i proxy            # http_proxy, https_proxy, no_proxy
```
Remember: systemd services and docker daemon have their OWN proxy env — check
`systemctl show <svc> -p Environment`.

## 2. Status-code triage

| Code | Usual cause | First check |
|---|---|---|
| 400 | malformed request, oversized headers | replay with minimal curl |
| 401/403 | auth/token expired; 403 on S3/CDN = policy/WAF | auth headers; WAF logs |
| 404 | wrong path/vhost | `curl -H "Host: ..."` against the backend directly |
| 405 | method blocked (often by proxy) | try against backend directly |
| 408 | client too slow / idle timeout | timeouts, LB idle settings |
| 413 | body too large | `client_max_body_size` (nginx), LB limits |
| 429 | rate limiting | `Retry-After` header, WAF/API GW rules |
| 500 | app exception | **app logs** |
| 502 | proxy got bad/no response from upstream | is upstream up? ports? keepalive mismatch |
| 503 | no healthy backends / maintenance mode | LB target health, app health endpoint |
| 504 | upstream timed out | backend latency; proxy timeout values |

The layered-bypass method for 5xx behind a chain (CDN → LB → nginx → app):
```bash
curl -v https://site.com/api            # 1. through everything
curl -v --resolve site.com:443:<LB-IP> https://site.com/api    # 2. skip CDN
curl -v -H "Host: site.com" http://<instance-ip>/api           # 3. skip LB
curl -v http://localhost:8080/api       # 4. on the box: skip nginx → app itself
```
The first hop where the error appears is the guilty layer.

## 3. TLS / certificates — `openssl`

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null
                                        # ★ -servername = SNI; ALWAYS include it —
                                        #   without it you may get the default vhost cert
# in output: certificate chain, "Verify return code: 0 (ok)" or the error

# expiry — the #1 TLS incident:
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -dates
# notBefore=...  notAfter=Sep  1 12:00:00 2026 GMT

echo | openssl s_client -connect host:443 -servername host 2>/dev/null \
  | openssl x509 -noout -subject -issuer -ext subjectAltName
                                        # ★ SAN list — name mismatch errors live here
openssl s_client -connect host:443 -servername host -showcerts </dev/null
                                        # full chain — MISSING INTERMEDIATE = works in
                                        #   browsers, fails in curl/java/python!
openssl x509 -in cert.pem -noout -text  # inspect a cert file
openssl x509 -enddate -noout -in cert.pem -checkend 2592000   # expires within 30d? (rc!=0)
openssl rsa -noout -modulus -in key.pem | openssl md5          # ★ do key and cert match?
openssl x509 -noout -modulus -in cert.pem | openssl md5        #   (compare these hashes)
openssl s_client -connect host:443 -tls1_2   # test a specific protocol version
openssl verify -CAfile chain.pem cert.pem
curl -vI https://host 2>&1 | grep -A5 "Server certificate"
```
Common failures decoded:

- `certificate has expired` → renew; also check **system clock** (12-time-ntp.md)
- `self-signed certificate in certificate chain` → private CA not in trust store →
  add to `/etc/pki/ca-trust/source/anchors/` + `update-ca-trust` (RHEL) or
  `/usr/local/share/ca-certificates/` + `update-ca-certificates` (Debian)
- `unable to get local issuer certificate` → server not sending intermediates
- `hostname mismatch` → name not in SAN (check the SAN command above)
- handshake failure/protocol version → legacy client vs modern server (or reverse)

## 4. Web server side

```bash
nginx -t                                # ★ config syntax check BEFORE reload
nginx -T | less                         # dump FULL effective config (all includes)
systemctl reload nginx                  # apply without dropping connections
tail -f /var/log/nginx/error.log        # upstream errors, permission problems
tail -f /var/log/nginx/access.log
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn   # code histogram
apachectl configtest ; apachectl -S     # Apache: syntax + vhost layout
ss -tlnp sport = :443                   # is the server even listening?
```
502 from nginx with SELinux: `httpd_can_network_connect` boolean (10-users-permissions-security.md).

## 5. Quick API/service probes

```bash
curl -s http://localhost:8080/health | jq .          # health endpoint
watch -n2 'curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8080/health'
                                        # poll status+latency while you fix things
ab -n 1000 -c 50 http://host/ ; wrk -t4 -c100 -d30s http://host/   # quick load tests
                                        # (only against systems you own!)
websocat wss://host/socket              # websocket test (if installed)
python3 -m http.server 8000             # instant test server — is the PATH to this
                                        #   box the problem, or the real app?
```

## Decision tree: "the site is down/slow"

```
curl -v https://site
├── couldn't resolve        → 08-dns.md
├── connection timed out    → 02-network.md path checks (+ AWS SG/NACL)
├── connection refused      → service down / wrong port / wrong bind → ss -tlnp on server
├── TLS error               → openssl s_client -servername ... → expiry/chain/SAN/clock
├── 4xx/5xx                 → table above + layered-bypass to find the guilty hop
└── slow                    → curl -w timing breakdown → dns / network / tls / backend
```
