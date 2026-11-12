# 43 — Traefik Deep Dive & Reverse-Proxy Problems (Traefik, Nginx, Apache, Caddy, HAProxy, NPM)

Traefik is the front door of every Dokploy host you run. This module first teaches it as a tool: how it works, a homelab install, day-2 operations and a learning path. Then it gives you a library of 33 reverse-proxy problems that DevOps engineers hit most often with Traefik, Nginx, Apache httpd, Caddy, HAProxy and Nginx Proxy Manager (NPM), plus a production postmortem worth knowing.

The problems come from the most-viewed community forum threads, GitHub issues and official documentation, checked in October 2026. Stack Overflow, Server Fault and Reddit are linked through search links. Every command is documented for you to run on your own test VM or server. None of it was run while writing this module.

---

## 0. How to use this module

**Who it serves.**

| Stage | Level | Start with | What you should be able to do after it |
|---|---|---|---|
| Fresher | L0 Foundations | 1, 9.1 | Explain the request path and apply a config change the right way |
| Junior | L1 Operator | 2, 7.1, 7.4, 10.1, 10.2, 11.1 | Install Traefik on a VM, decide who owns 80/443, read nginx and Apache errors |
| Mid-level | L2 Troubleshooter | 5, 6, 9, 10.1, 13.1, 13.2, 14.1 | Fix 404, 502, 504, certificate and redirect problems from the logs alone |
| Senior | L3 Platform | 3, 7.3, 7.5, 8.1–8.3, 15 | Run Traefik for a team: Swarm, raw TCP, SSO, client IPs, registries, upgrades |
| Senior/Lead | L4 SRE | 3.4–3.7, 8.4, 8.5, 10.3, the 13 postmortem | Own timeouts and keep-alive across hops, capacity, HA, ingress migration, safe change |

**How the entries are laid out.** Each problem has a short heading and a one-line card (Seen as · Where · Level · How common). Then come: why it happens, the commands to diagnose it, a realistic sample output, what that output tells you, the fix, why the fix works (and what not to do), how to prevent it, where to study next, and community threads. Levels are tagged like [L2 · Mid] so you can filter by your career stage.

**How to practise.**

1. Build section 2 on a throwaway Ubuntu 24.04 VM, or on the [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) or [Docker playground](https://kodekloud.com/playgrounds/playground-docker).
2. Pick an entry, break the lab on purpose so it shows the same error, and fix it using only the Diagnose commands. The Self-check at the end has ten timed exercises.
3. Write a five-line note: symptom, first wrong guess, deciding evidence, fix, what to check first next time.
4. Never practise on the production Dokploy host. Proxy mistakes take every site down at once.

> 📚 **Study path:** KodeKloud *Nginx For Beginners* ([course](https://kodekloud.com/courses/nginx-for-beginners)): Intermediate Config → Reverse Proxy, Security → HTTPS, Performance → Monitoring & Troubleshooting → KodeKloud *Kubernetes Networking Deep Dive* ([course](https://kodekloud.com/courses/kubernetes-networking)): Kubernetes Ingress → Traefik Overview, Demo/Lab: Traefik Installation, Demo: Traefik Observability → handbook [29 §4 Traefik in depth](29-learn-webservers-proxies.md#4-traefik-in-depth) and this module → [Traefik docs](https://doc.traefik.io/traefik/) → lab: section 2 here, then the Self-check.

**Two habits that solve half of the community threads.**

- **Find out who generated the error** before changing anything: the proxy or the app (1.9). A plain-text "404 page not found" and a Traefik 502 mean very different things from the same codes sent by your app.
- **Draw the hop chain**: client → CDN or cloud load balancer → Traefik → app. For each hop, note who terminates TLS, who is trusted to set X-Forwarded-* headers, and its idle and read timeouts. Most "mysterious" 502s, 504s, redirect loops and wrong client IPs are a disagreement between two neighbouring hops.

---

## 1. Traefik in 10 minutes

### 1.1 What Traefik is

Traefik Proxy is an open-source reverse proxy and load balancer written in Go. You don't write one vhost per site. Traefik builds its routes from **providers**: Docker or Swarm labels, Kubernetes objects, or YAML files. It applies changes live and requests and renews Let's Encrypt certificates by itself. Dokploy, Coolify and k3s all ship it as their edge proxy, so on your hosts "the proxy" usually means Traefik.

**Versions (October 2026).** 3.7 (May 2026) is the only line with security support. 3.6 lost security support on 16 Aug 2026 and v2.11 on 7 Sept 2026, according to Traefik's release support table. Dokploy's current install script still creates `dokploy-traefik` from `traefik:v3.6.25`, so check the tag on your own hosts (3.1, 7.5).

**What it is not.** Traefik is not a web server for static files and not a WAF. It routes, terminates TLS, applies middlewares and load-balances. For PHP sites keep Apache or nginx behind it (5.5).

### 1.2 The request path

```
                client (browser, docker CLI, git, curl)
                               |
                DNS: app.example.com -> 203.0.113.10
                               |
 +-----------------------------v---------------------------------------+
 | Ubuntu host 203.0.113.10   (Docker-published ports bypass UFW)      |
 |                                                                     |
 |  dokploy-traefik container                                          |
 |  +---------------------------------------------------------------+  |
 |  | entryPoints   web :80  ---- redirect ---->  websecure :443    |  |
 |  |                                              (443/udp = HTTP/3)|  |
 |  |                      |                                        |  |
 |  | routers       rule Host(`app.example.com`), tls.certResolver   |  |
 |  |                      |                                        |  |
 |  | middlewares   headers -> forwardAuth -> ipAllowList -> ...    |  |
 |  |                      |                                        |  |
 |  | services      loadBalancer -> 10.0.1.15:3000 (serversTransport)|  |
 |  +----------------------|----------------------------------------+  |
 |                         |  dokploy-network (overlay)                |
 |        app container :3000          host Apache :81 (file provider) |
 +---------------------------------------------------------------------+
   providers feed routers and services: docker labels, swarm labels,
   files in a watched directory; certificatesResolvers talk to Let's Encrypt
```

Read it top-down when you debug. Does DNS point here? Is the port reachable? Which entryPoint received the request? Did a router match? Did the middlewares let it through? Can Traefik reach the service? What did the app answer? Each problem in this module breaks exactly one of those steps.

### 1.3 The building blocks

| Object | Config type | What it does | Typical example |
|---|---|---|---|
| entryPoint | static | A listening port, with its timeouts, trusted headers and HTTP/3 | web :80, websecure :443 |
| router | dynamic | Matches requests by rule, applies middlewares, picks a service, asks for TLS | a Host rule for app.example.com |
| middleware | dynamic | Changes or guards the request on the way | redirectScheme, basicAuth, forwardAuth, ipAllowList, headers, rateLimit, buffering, retry, stripPrefix |
| service | dynamic | Where the request goes: servers, health check, sticky cookie | loadbalancer.server.port=3000 |
| provider | static | Where dynamic config comes from | docker, swarm, file, kubernetesCRD, kubernetesGateway |
| certificatesResolver | static | One ACME account plus one challenge type | letsencrypt (HTTP-01), le-dns (DNS-01) |
| serversTransport | dynamic | How Traefik talks to backends: CA trust, SNI, timeouts | rootCAs, serverName, idleConnTimeout |
| TLS options and stores | dynamic | Minimum TLS version, default certificate | minVersion VersionTLS12 |

**Static** config is read once at start, from one source only: the file `traefik.yml`, CLI flags, or environment variables. These sources are mutually exclusive, so if you mix them, one set silently disappears. **Dynamic** config comes from providers and reloads live. Every dynamic object lives in a provider namespace: `app@docker`, `secure-headers@file`, `api@internal`. To use an object from another provider, add its suffix (5.4). Handbook detail: [29 §4.1 Static vs dynamic configuration](29-learn-webservers-proxies.md#41-static-vs-dynamic-configuration).

### 1.4 Rules and priority

v3 rule matchers: `Host`, `HostRegexp` (Go regular expressions), `Path`, `PathPrefix`, `PathRegexp`, `Method`, `Header`, `HeaderRegexp`, `Query`, `QueryRegexp` and `ClientIP`, combined with `&&`, `||`, `!` and parentheses. One `Host()` takes one domain, so join several with `||`. TCP routers use `HostSNI`, `HostSNIRegexp`, `ClientIP` and `ALPN`.

By default a router's priority is the **length of its rule**, so the longer, more specific rule wins. Set `priority` yourself when a short rule must win, or when two rules are about the same length.

```yaml
# Docker labels: two routers on one host. The longer rule (/api) wins by default.
- traefik.http.routers.shop.rule=Host(`shop.example.com`)
- traefik.http.routers.shop-api.rule=Host(`shop.example.com`) && PathPrefix(`/api`)
# Maintenance page: an explicit priority beats any rule length
- traefik.http.routers.maintenance.rule=Host(`shop.example.com`)
- traefik.http.routers.maintenance.priority=1000
```

### 1.5 Certificates: resolvers and the default certificate

| Challenge | Needs | Wildcards | Internal-only hosts | Behind a TLS-terminating CDN |
|---|---|---|---|---|
| HTTP-01 (httpChallenge) | Public DNS and port 80 reaching Traefik from the internet | No | No | Often breaks: use DNS-only records or DNS-01 |
| TLS-ALPN-01 (tlsChallenge) | Port 443 reaching Traefik directly | No | No | No |
| DNS-01 (dnsChallenge) | A DNS provider API token | Yes | Yes | Yes |

- **Storage.** `acme.json` holds the ACME account and every private key. It must be mode 600 and on a persistent volume. Several resolvers can share one file, because entries are stored per resolver name.
- **Default certificate.** If no certificate matches the name the client asked for (SNI), Traefik serves its self-signed `TRAEFIK DEFAULT CERT`. That is a symptom, not a cause. The cause is in the ACME lines of the log (6.1).
- **Renewal.** Traefik renews ACME certificates about 30 days before expiry for 90-day certificates. Let's Encrypt lifetimes are shrinking (3.7), so monitor expiry yourself.
- **Test against staging** (`caServer: https://acme-staging-v02.api.letsencrypt.org/directory`) while you experiment, to stay clear of production rate limits.

Handbook detail: [29 §4.7 Certificates](29-learn-webservers-proxies.md#47-certificates-acme-resolvers-and-the-default-certificate).

### 1.6 TCP, UDP and passthrough

HTTP carries the hostname in the Host header and TLS carries it in SNI, so Traefik can route many names on one port. Plain TCP (SSH, MySQL, Redis, Postgres before TLS starts) carries no name. Traefik can only route it by **port**: give it its own entryPoint and a TCP router with ``HostSNI(`*`)``. A TCP router with `tls.passthrough=true` routes by SNI but leaves TLS to the backend, which keeps its own certificate. UDP routers have no rule at all: one entryPoint, one UDP service. Worked example: 8.1.

### 1.7 Middlewares, plugins and forward auth

Middlewares run in the order you list them on the router. The ones you will use most: `redirectScheme` (HTTP to HTTPS), `headers` (HSTS and security headers), `basicAuth`, `forwardAuth` (SSO), `ipAllowList` (LAN only), `rateLimit`, `buffering` (body size limits), `retry`, `stripPrefix` and `chain`.

**Plugins** come from the Traefik plugin catalog and are declared in static config under `experimental.plugins`. Traefik downloads them at start, so the host needs outbound HTTPS. If a download fails, the routers that use the plugin break. Pin the version and test upgrades. On air-gapped hosts use `experimental.localPlugins`. A common example is the CrowdSec bouncer:

```yaml
# traefik.yml (static)
experimental:
  plugins:
    bouncer:
      moduleName: github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
      version: vX.Y.Z              # pin the current release shown in the plugin catalog
```

```yaml
# dynamic/crowdsec.yml (dynamic)
http:
  middlewares:
    crowdsec:
      plugin:
        bouncer:
          enabled: true
          crowdsecMode: stream            # refreshes decisions every 60 s, lowest overhead
          crowdsecLapiScheme: http
          crowdsecLapiHost: crowdsec:8080
          crowdsecLapiKey: REPLACE_WITH_BOUNCER_KEY   # template it at deploy time, keep it out of Git
          forwardedHeadersTrustedIPs:
            - 10.20.0.0/24                # only if a load balancer or CDN sits in front
```

The plugin only enforces decisions. The CrowdSec agent creates them by reading Traefik's access log, and both depend on real client IPs (8.3).

**Forward auth** asks an auth server about every request before it reaches the app:

```
browser --> Traefik router (middleware: authentik or authelia)
              |
              |-- 1. copy of the request headers --> auth server (Authentik :9000, Authelia :9091)
              |<- 2a. 200 + identity headers  ----> request continues to the app
              |<- 2b. 302 to the login portal  ---> browser logs in, comes back with a cookie
```

The usual breakages (unreachable auth server, the outpost path not routed, the middleware on the portal itself) are in 8.2.

### 1.8 Where Traefik sits in your stack

| Component | How it reaches users through Traefik | Watch out for |
|---|---|---|
| Dokploy Applications | Dokploy writes one file-provider router per app | Domain port must match the app's port (5.2) |
| Dokploy Compose apps and templates | Traefik labels, read at deploy time | Redeploy after every domain change (5.1) |
| Dokploy panel | Port 3000 directly, or a domain routed by Traefik | Don't leave 3000 open to the internet |
| Legacy Apache sites | File-provider router to the host's LAN IP on :81 | UFW must let Docker networks reach :81 (5.5) |
| GitLab | HTTP router to the container's port 80, TCP router on :2222 for SSH | 422 CSRF errors without X-Forwarded-Proto (9.3) |
| Harbor | HTTP router with long read timeouts | external_url, body size and the private CA (15.1) |
| Wazuh dashboard | HTTPS backend on 8443 that uses its own CA | Agent ports 1514/1515 and API 55000 are not HTTP routes (5.6) |
| Authentik or Authelia | forwardAuth middleware on protected routers | Outpost route priority, shared network (8.2) |
| CrowdSec | Bouncer plugin, plus the agent reading the access log | Needs real client IPs (8.3) |
| Prometheus | Scrapes Traefik's metrics entryPoint | Router labels raise cardinality (3.4) |

### 1.9 Who generated the error?

| What you see | Generated by | Meaning and where to go |
|---|---|---|
| Plain-text "404 page not found" | Traefik | No router matched this host and path on this entryPoint (5.1) |
| 502 Bad Gateway | Traefik | Backend refused the connection, reset it or closed it early (5.2, 8.4) |
| 504 Gateway Timeout | Traefik | Traefik could not connect in time: wrong network or firewall (5.3) |
| 500 with x509 in Traefik's log | Traefik | Backend certificate failed verification (5.6) |
| 499 in the access log | the client connection | The client connection ended before a response: the client gave up, or the entryPoint's read deadline cut it (15.1) |
| 401, 403 or 429 | a Traefik middleware | basicAuth or forwardAuth, ipAllowList, rateLimit |
| Same code in OriginStatus and DownstreamStatus | the app | Traefik only passed on what the app returned |

In Traefik's JSON access log, **OriginStatus 0** means no backend ever answered: a routing, auth or connection problem, not an app bug. Section 3.3 shows how to switch that log on and query it.

---

## 2. Install and first configuration

This is a homelab-safe Traefik on one Ubuntu VM, with Docker Compose. It uses the same building blocks as Dokploy, so everything you learn here carries over (2.6 shows the Dokploy paths). Use a test domain or `/etc/hosts` entries, and keep the Let's Encrypt staging CA until the first certificate works.

### 2.1 Layout on disk

```
/opt/traefik/
├── compose.yaml
├── traefik.yml              # STATIC config: read once at start
├── dynamic/                 # file provider: a watched DIRECTORY, not a single file
│   ├── middlewares.yml
│   ├── tls.yml
│   └── legacy-apache.yml
├── certs/
│   └── private-ca.crt       # your internal CA root (the same one Harbor uses)
├── letsencrypt/
│   └── acme.json            # chmod 600, persistent
├── secrets/
│   └── cf_dns_token         # DNS-01 API token, chmod 600, never in Git
└── logs/
    └── access.log
```

```bash
sudo mkdir -p /opt/traefik/{dynamic,certs,letsencrypt,secrets,logs}
sudo touch /opt/traefik/letsencrypt/acme.json && sudo chmod 600 /opt/traefik/letsencrypt/acme.json
docker network create proxy        # the one network every routed app joins
```

Mount the `dynamic/` **directory**, not single files. Editors save by writing a new file and renaming it, and a single-file bind mount keeps pointing at the old inode, so Traefik never sees the change.

### 2.2 Static configuration

```yaml
# /opt/traefik/traefik.yml - STATIC config. Restart Traefik after any change here.
global:
  checkNewVersion: false
  sendAnonymousUsage: false

log:
  level: INFO                     # DEBUG only while troubleshooting; it is very noisy
  format: json

accessLog:
  filePath: /logs/access.log
  format: json
  bufferingSize: 100
  fields:
    headers:
      defaultMode: drop
      names:
        User-Agent: keep
        X-Forwarded-For: keep

api:
  dashboard: true                 # published only through a protected router (2.4), never api.insecure

ping: {}                          # /ping on the internal "traefik" entryPoint (:8080, never published)

metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true
    addRoutersLabels: false       # per-router series multiply fast; enable only when you need them

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
    http:
      tls:
        certResolver: letsencrypt # default resolver for every router on this entryPoint
    http3: {}                     # needs 443/udp published
    transport:
      respondingTimeouts:
        readTimeout: 600s         # the 60s default cuts large uploads and docker push (15.1)
  metrics:
    address: ":8082"              # scraped over the Docker network, never published

providers:
  docker:
    endpoint: "tcp://socket-proxy:2375"
    exposedByDefault: false       # only containers with traefik.enable=true get routes
    network: proxy
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: ops@example.com
      storage: /letsencrypt/acme.json
      caServer: https://acme-staging-v02.api.letsencrypt.org/directory   # remove after the first good test
      httpChallenge:
        entryPoint: web
  le-dns:
    acme:
      email: ops@example.com
      storage: /letsencrypt/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:                # check propagation against public DNS, not split-horizon (6.2)
          - "1.1.1.1:53"
          - "1.0.0.1:53"
```

**Why these choices:**

- **One static source.** No CLI flags in the Compose file. A single flag would make Traefik ignore this whole file (5.4).
- **`exposedByDefault: false`.** A new container never gets published by accident.
- **Socket proxy endpoint.** Traefik never touches `/var/run/docker.sock` directly (3.5).
- **Global redirect on `web`.** Every router lives on `websecure` only. ACME HTTP-01 challenges still work, because Traefik answers them before the redirect applies.
- **Explicit `readTimeout`.** Sized for your largest upload, instead of the 60 s default.

### 2.3 Dynamic configuration

```yaml
# /opt/traefik/dynamic/middlewares.yml - DYNAMIC: reloads on save
http:
  middlewares:
    secure-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        contentTypeNosniff: true
        frameDeny: true
        referrerPolicy: strict-origin-when-cross-origin
    dash-auth:
      basicAuth:
        users:
          - "admin:$2y$05$REPLACE_WITH_HTPASSWD_HASH"   # htpasswd -nB admin; no $$ escaping in files
    lan-only:
      ipAllowList:
        sourceRange:
          - 192.168.0.0/16
          - 10.0.0.0/8
  serversTransports:
    internal-ca:
      rootCAs:
        - /certs/private-ca.crt                       # trust your CA instead of skipping verification
```

```yaml
# /opt/traefik/dynamic/tls.yml
tls:
  options:
    default:
      minVersion: VersionTLS12
```

Check the YAML before you save it. In current v3 releases a **syntax** error makes the file provider reject the reload and keep the last good config, so your edit seems to do nothing. After the next restart every file-based route is gone.

```bash
python3 -c 'import sys, yaml; [yaml.safe_load(open(f)) for f in sys.argv[1:]]; print("YAML OK")' /opt/traefik/dynamic/*.yml
```

### 2.4 Compose file with a socket proxy

```yaml
# /opt/traefik/compose.yaml
services:
  socket-proxy:
    image: tecnativa/docker-socket-proxy:VERSION   # pin a release tag
    environment:
      CONTAINERS: 1          # read-only container list/inspect; the swarm provider also needs SERVICES, TASKS, NETWORKS
      POST: 0                # no write calls at all
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [socket]
    restart: unless-stopped

  traefik:
    image: traefik:v3.7.13                         # pin the newest 3.7.x patch
    container_name: traefik                        # so "docker logs traefik" etc. work (Compose would name it traefik-traefik-1)
    depends_on: [socket-proxy]
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
      - ./dynamic:/etc/traefik/dynamic:ro
      - ./certs:/certs:ro
      - ./letsencrypt:/letsencrypt
      - ./logs:/logs
    environment:
      CF_DNS_API_TOKEN_FILE: /run/secrets/cf_dns_token   # lego also reads *_FILE variables
    secrets: [cf_dns_token]
    extra_hosts:
      - "host.docker.internal:host-gateway"         # lets file-provider routes reach host services (5.5)
    healthcheck:
      test: ["CMD", "traefik", "healthcheck", "--ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks: [proxy, socket]
    restart: unless-stopped
    labels:
      - traefik.enable=true
      - traefik.http.routers.dashboard.rule=Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))
      - traefik.http.routers.dashboard.entrypoints=websecure
      - traefik.http.routers.dashboard.service=api@internal
      - traefik.http.routers.dashboard.middlewares=lan-only@file,dash-auth@file

networks:
  proxy:
    external: true
  socket:
    internal: true

secrets:
  cf_dns_token:
    file: ./secrets/cf_dns_token
```

Port 8080 is never published, and the dashboard is a normal router with an allowlist and a password. The socket proxy only answers read calls. A `:ro` mount of the raw socket does **not** limit what the Docker API allows: it still gives root on the host (3.5).

### 2.5 First app and smoke test

```yaml
# /opt/stacks/whoami/compose.yaml - the test app used by every lab in this module
services:
  whoami:
    image: traefik/whoami
    networks: [proxy]
    labels:
      - traefik.enable=true
      - traefik.http.routers.whoami.rule=Host(`whoami.example.com`)
      - traefik.http.routers.whoami.entrypoints=websecure
      - traefik.http.routers.whoami.middlewares=secure-headers@file
      - traefik.http.services.whoami.loadbalancer.server.port=80
networks:
  proxy:
    external: true
```

```bash
cd /opt/traefik && docker compose up -d
docker logs --since 2m traefik 2>&1 | grep -E '"level":"(error|warn)"' | tail -5
# HTTP must redirect and HTTPS must answer. --resolve skips DNS; -k because staging certs are untrusted.
curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}\n' --resolve whoami.example.com:80:192.168.56.20 http://whoami.example.com/
curl -sk --resolve whoami.example.com:443:192.168.56.20 https://whoami.example.com/ | head -12
```

```
301 -> https://whoami.example.com/
Hostname: 6f3c2a1b9d8e
IP: 127.0.0.1
IP: 172.20.0.4
RemoteAddr: 172.20.0.3:47112
GET / HTTP/1.1
Host: whoami.example.com
User-Agent: curl/8.5.0
Accept: */*
Accept-Encoding: gzip
X-Forwarded-For: 192.168.56.1
X-Forwarded-Host: whoami.example.com
X-Forwarded-Port: 443
```

→ The redirect works (301 for GET, 308 for other methods). The app sees the original Host and the forwarded headers, and `X-Forwarded-For` holds the real client address (192.168.56.1, the VM host). Keep `whoami` running: it is the quickest way to see what a backend receives, and 8.2, 8.3 and 9.3 use it.

### 2.6 Dokploy: same pieces, different paths

| Piece | Plain Traefik (this lab) | Dokploy (from its install script, October 2026) |
|---|---|---|
| Container | `traefik` from compose.yaml | `dokploy-traefik`, created with docker run, restart always, on dokploy-network |
| Image | traefik:v3.7.x, pinned by you | traefik:v3.6.25 in the current installer |
| Ports | 80, 443, 443/udp | 80/tcp, 443/tcp, 443/udp; 8080 only after Enable Dashboard (7.4) |
| Static config | /opt/traefik/traefik.yml | /etc/dokploy/traefik/traefik.yml, mounted as /etc/traefik/traefik.yml |
| Dynamic files | /opt/traefik/dynamic | /etc/dokploy/traefik/dynamic (one file per Application, plus middlewares.yml) |
| ACME storage | /opt/traefik/letsencrypt/acme.json | /etc/dokploy/traefik/dynamic/acme.json |
| Docker access | socket proxy | /var/run/docker.sock mounted read-only (still full API access) |
| Shared network | proxy | dokploy-network (overlay, attachable) |

```bash
docker ps --filter name=dokploy-traefik --format '{{.Names}}  {{.Image}}  {{.Status}}'
docker inspect dokploy-traefik --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} rw={{.RW}}{{println}}{{end}}'
sudo ls -l /etc/dokploy/traefik/dynamic/
```

```
dokploy-traefik  traefik:v3.6.25  Up 6 days
/etc/dokploy/traefik/traefik.yml -> /etc/traefik/traefik.yml rw=true
/etc/dokploy/traefik/dynamic -> /etc/dokploy/traefik/dynamic rw=true
/var/run/docker.sock -> /var/run/docker.sock rw=false
-rw------- 1 root root 48211 Oct  1 02:10 acme.json
-rw-r--r-- 1 root root   612 Sep 18 11:02 crm-web-8f2k1q.yml
-rw-r--r-- 1 root root   204 Aug  3 09:40 middlewares.yml
```

**Dokploy rules of thumb:**

- **Use Dokploy's UI, not the container.** Change Traefik through its file editor and its Traefik actions (reload, environment, dashboard, extra ports). Dokploy may rewrite files or recreate the container behind your back.
- **Treat every Traefik action that changes ports or environment as a proxy restart.** It recreates `dokploy-traefik`, and every site is down until the new container starts. Schedule it (7.4).
- **Remote servers run their own `dokploy-traefik`.** Manage them from the server's own actions. Dokploy issue #2351 reported an environment change landing on the local server instead.
- **Follow Dokploy's releases for the Traefik image.** If a security fix can't wait, recreate the container with the same flags and a newer tag on a staging Dokploy first (the command is in 7.4).

Deeper: [29 §5.4 How a domain becomes a Traefik router](29-learn-webservers-proxies.md#54-how-a-domain-becomes-a-traefik-router) and [45 Dokploy deep dive](45-dokploy-and-self-hosted-paas.md).

---

## 3. Day-2 operations

### 3.1 Upgrades without surprises

The edge proxy breaks most often after an upgrade, and usually because a default changed:

| Change | Effect seen in the community | Entry |
|---|---|---|
| Traefik 2.11.2 and 3.0: readTimeout defaults to 60 s (CVE-2024-28869 fix) | Uploads and docker push die at 60 s | 15.1 |
| Docker Engine 29 (Nov 2025): minimum API 1.44 | Traefik older than 3.6.1 loses every Docker route | 7.2 |
| Traefik 3.7.6+: ACME library moved to lego v5 | Some Cloudflare DNS-01 setups fail | 6.2 |
| nginx 1.29.7 mainline (Mar 2026): upstream keep-alive and HTTP/1.1 by default | Keep-alive races appear on nginx too | 8.4 |
| Caddy 2.11.0: Host rewritten for HTTPS upstreams; 2.11.6: 16 KiB header limit | Different upstream behaviour, large SSO cookies rejected | 12 |
| NPM 2.13.3: one-way database migration ("not easily" reversible, per its release notes) | Rollback impractical without a /data backup | 14.1 |

```bash
# 1. What runs now? Read every release note between that and the target.
docker exec traefik traefik version | head -1
# 2. Back up (3.2). On STAGING first: bump the pinned tag, pull, recreate.
sudo sed -i 's|traefik:v3.7.12|traefik:v3.7.13|' /opt/traefik/compose.yaml
docker compose -f /opt/traefik/compose.yaml pull traefik && docker compose -f /opt/traefik/compose.yaml up -d traefik
# 3. Verify: no new errors, router counts unchanged, smoke tests green.
docker logs --since 5m traefik 2>&1 | grep -E '"level":"(error|warn)"' | tail -5
curl -s -u admin:PASSWORD https://traefik.example.com/api/overview | jq -c '.http.routers'
# 4. Keep Docker itself from moving under the proxy.
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

```
Version:      3.7.12
{"total":14,"warnings":0,"errors":0}
```

→ Compare the router totals before and after. Any warnings or errors after the upgrade mean a rule or option changed meaning. Rollback is the previous image tag plus the backed-up `acme.json`. Keep the edge proxy out of Watchtower and similar auto-updaters, and watch the GitHub releases and security advisories of every proxy you run.

### 3.2 Backups and restore

Back up the static file, the dynamic directory, `acme.json` (it holds every private key, so encrypt the archive) and the Compose file and secrets. On Dokploy hosts, back up all of `/etc/dokploy/traefik` together with Dokploy's own database (see [45](45-dokploy-and-self-hosted-paas.md)).

```bash
sudo tar -czf /var/backups/traefik-$(date +%F).tgz -C /opt traefik/compose.yaml traefik/traefik.yml traefik/dynamic traefik/letsencrypt traefik/certs traefik/secrets
sudo tar -czf /var/backups/dokploy-traefik-$(date +%F).tgz -C /etc/dokploy traefik
sudo chmod 600 /var/backups/*traefik-*.tgz
```

**Restore drill (quarterly, on a test VM).** Unpack, `chmod 600` the `acme.json`, start Traefik, then check with `openssl s_client` that the old certificate is served and that the log shows no new ACME order. If certificates are re-requested on every restore, your backup does not contain what you think it does.

### 3.3 Logs: read them, ship them

Traefik writes no access log until you enable it. Enable it in JSON from day one (2.2). Most proxy problems are solved by reading what the proxy actually did, not by re-reading the config.

| Access-log field | What it tells you |
|---|---|
| ClientHost | TCP peer address: the real client only if nothing sits in front, or with PROXY protocol |
| RequestHost, RequestPath, RequestMethod | What was asked |
| RouterName, ServiceName | Which router matched (empty: none did) and where it sent the request |
| OriginStatus | What the backend answered; 0 means no backend answered |
| DownstreamStatus | What the client received |
| Duration, OriginDuration | Total and backend time, in nanoseconds |
| RetryAttempts | Retries made by the retry middleware |

```bash
# requests where no backend answered: routing, auth or connection problems
jq -c 'select(.OriginStatus == 0) | {RequestHost, RequestPath, RouterName, DownstreamStatus}' /opt/traefik/logs/access.log | tail -3
# 5xx per router in the last 10 000 requests
tail -n 10000 /opt/traefik/logs/access.log | jq -r 'select(.DownstreamStatus >= 500) | .RouterName' | sort | uniq -c | sort -rn
```

```
{"RequestHost":"app.example.com","RequestPath":"/","RouterName":"","DownstreamStatus":404}
{"RequestHost":"wiki.example.com","RequestPath":"/","RouterName":"wiki@docker","DownstreamStatus":504}
     41 api@docker
      3 shop@docker
```

→ The first line is a routing miss (5.1). The second is a router that never got a backend answer (5.3). The counts show where the 5xx come from.

**Noise or signal?**

| Log line | Verdict |
|---|---|
| use of closed network connection, around restarts | Normal during restarts and reloads (Dokploy's docs say so); investigate only if constant |
| failed to sufficiently increase receive buffer size (was: 208 kiB, wanted: 7168 kiB, got: 416 kiB) | HTTP/3 throughput hint from quic-go; raise the host's UDP buffers |
| Could not find network named ... Maybe you're missing the project's prefix in the label? | Real problem: wrong network (5.3) |
| Provider error, retrying | Real problem: provider down, so routes are missing (7.2) |
| Unable to obtain ACME certificate | Real problem: the ACME path is broken (6.1) |

```bash
# QUIC buffer warning: set on the HOST, not in the container
printf 'net.core.rmem_max=7500000\nnet.core.wmem_max=7500000\n' | sudo tee /etc/sysctl.d/99-quic.conf
sudo sysctl --system
```

```
# /etc/logrotate.d/traefik - Traefik reopens its log files on SIGUSR1
/opt/traefik/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        docker kill --signal=USR1 traefik >/dev/null 2>&1 || true
    endscript
}
```

**Ship the log** to Loki (Alloy tails the file), Wazuh and CrowdSec. Each needs real client IPs (8.3).

```xml
<!-- Wazuh agent, /var/ossec/etc/ossec.conf -->
<localfile>
  <log_format>json</log_format>
  <location>/opt/traefik/logs/access.log</location>
</localfile>
```

```yaml
# CrowdSec agent, /etc/crowdsec/acquis.d/traefik.yaml (with the crowdsecurity/traefik collection)
filenames:
  - /opt/traefik/logs/access.log
labels:
  type: traefik
```

Threads: [Traefik forum: Use of closed network connection error](https://community.traefik.io/t/use-of-closed-network-connection-error/18991) · [quic-go wiki: UDP Buffer Sizes](https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes) · [Dokploy docs: Domains troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains). More: [32 §14 Logs and tracing](32-learn-performance-observability.md#14-logs-and-tracing), [48 Wazuh](48-wazuh-and-security-tools.md).

### 3.4 Metrics and alerts

```yaml
# prometheus.yml - Prometheus on the same Docker network as Traefik
scrape_configs:
  - job_name: traefik
    static_configs:
      - targets: ["traefik:8082"]
```

| Metric | Use it for |
|---|---|
| traefik_entrypoint_requests_total | Traffic and error rate per entryPoint |
| traefik_service_requests_total | 5xx ratio per backend service |
| traefik_service_request_duration_seconds_bucket | Latency percentiles per backend |
| traefik_open_connections | Saturation |
| traefik_config_last_reload_success | Whether the last dynamic reload worked |
| traefik_tls_certs_not_after | Certificate expiry, as a Unix timestamp |

```yaml
groups:
  - name: traefik
    rules:
      - alert: TraefikServiceHigh5xx
        expr: |
          sum by (service) (rate(traefik_service_requests_total{code=~"5.."}[5m]))
            / sum by (service) (rate(traefik_service_requests_total[5m])) > 0.05
        for: 10m
        labels: {severity: page}
        annotations: {summary: "{{ $labels.service }} returns more than 5% 5xx"}
      - alert: TraefikReloadFailed
        expr: traefik_config_last_reload_success == 0
        for: 5m
        labels: {severity: ticket}
      - alert: TraefikCertExpiresSoon
        expr: (traefik_tls_certs_not_after - time()) / 86400 < 14
        for: 1h
        labels: {severity: ticket}
```

Alert on the 5xx **ratio** per service, not only on "site up". Several entries here (8.4, 15.1) show up as a small, steady stream of 502s or 499s long before anyone complains. More: [32 §11 Prometheus](32-learn-performance-observability.md#11-prometheus) and [32 §12 Alertmanager and alert rules](32-learn-performance-observability.md#12-alertmanager-and-alert-rules).

### 3.5 Hardening checklist

- **Supported versions only.** Traefik 3.7.x (2.11 and 3.6 are out of security support), HAProxy on a maintained LTS branch (upstream 3.0, 3.2 or 3.4; Ubuntu 24.04's 2.8 gets only critical fixes upstream, plus Ubuntu security updates), and nginx or Apache from Ubuntu security updates. ingress-nginx is retired (8.5).
- **Pin images and patch on a schedule.** Pin a tag (a digest in production), hold a monthly patch window, and keep auto-updaters away from the edge. Read advisories as they appear. Examples: CVE-2023-44487 (HTTP/2 Rapid Reset), CVE-2024-28869 (fixed by the 60 s readTimeout default), and GHSA-7ghq-v6jf-g56c (readTimeout not applied to HTTP/3 in older releases).
- **The Docker socket is root.** Put a socket proxy that allows only read calls in front of it. A `:ro` bind mount doesn't restrict the API.
- **Publish only 80, 443 and 443/udp.** Docker-published ports bypass UFW, so `api.insecure` on 8080, NPM's admin on 81 or an HAProxy stats port are open to the internet if published. Put admin UIs behind forward auth plus an IP allowlist, or a VPN.
- **TLS and headers.** Set minVersion VersionTLS12 and the security-headers middleware. Add HSTS only once HTTPS works for every name under the domain.
- **Abuse control.** Rate-limit login paths, run the CrowdSec bouncer, and trust forwarded headers only from exact proxy IPs.
- **Scan.** Scan proxy images with Trivy or Grype in CI.

```bash
docker ps --format '{{.Names}}\t{{.Image}}' | grep -Ei 'traefik|nginx|caddy|haproxy|proxy-manager'
docker inspect traefik --format '{{range .Mounts}}{{if eq .Source "/var/run/docker.sock"}}raw socket mounted, rw={{.RW}}{{end}}{{end}}'
sudo ss -ltnp | grep -E ':(8080|81|8404|2019) '      # admin surfaces: Traefik API, NPM, HAProxy stats, Caddy admin
trivy image --severity HIGH,CRITICAL traefik:v3.7.13
```

Sources: [Traefik release support table](https://doc.traefik.io/traefik/deprecation/releases/) · [Traefik advisory GHSA-7ghq-v6jf-g56c](https://github.com/traefik/traefik/security/advisories/GHSA-7ghq-v6jf-g56c) · [Traefik forum: Is Traefik vulnerable to CVE-2023-44487?](https://community.traefik.io/t/is-traefik-vulnerable-to-cve-2023-44487/20125) · Search: [Reddit r/selfhosted: docker socket proxy traefik](https://www.reddit.com/r/selfhosted/search/?q=docker+socket+proxy+traefik+security&restrict_sr=1). More: [37 §9 Web and edge hardening](37-learn-security-devsecops.md#9-web-and-edge-hardening), [37 §6 Container security](37-learn-security-devsecops.md#6-container-security).

### 3.6 Scaling and high availability

- **One host, one Traefik.** Restarting it is a short outage for every site, so restarts belong in a change window. Traefik itself is rarely the bottleneck. Check file-descriptor limits, open connections and backend keep-alive first (8.4, 10.3).
- **Several Swarm nodes.** Run Traefik on each edge node with **host-mode** ports, so client IPs survive (8.3). Put DNS round-robin or a floating IP in front.
- **A floating IP for two edge nodes.** keepalived (VRRP) moves one virtual IP between two Traefik hosts, and a check script that calls Traefik's ping endpoint decides who holds it. Test failover by stopping Traefik, not by powering off the VM.
- **ACME with several instances.** Traefik's `acme.json` is a local file. It isn't designed to be shared by several running instances. Let one instance issue certificates (DNS-01 is easiest) and distribute them as files, terminate TLS on an external load balancer, or use cert-manager on Kubernetes.
- **Load-test before launches** with k6 or wrk against a staging copy ([32 §9 Benchmarking and load testing safely](32-learn-performance-observability.md#9-benchmarking-and-load-testing-safely)).

### 3.7 Certificates in 2026

Let's Encrypt stopped sending expiry reminder emails on 4 June 2025. 45-day certificates have been opt-in since 13 May 2026 (the tlsserver profile). The default lifetime drops to 64 days on 10 Feb 2027 and to 45 days on 16 Feb 2028, and authorization reuse shrinks to 7 hours. A renewal path that breaks silently now becomes an outage sooner, with no warning email.

**What silently breaks renewal:**

- Port 80 closed by a later firewall change.
- DNS moved to another provider, or a rotated DNS API token.
- `acme.json` not writable, or the proxy container stopped.
- The Docker 29 API break (7.2).
- Private-CA certificates (Harbor, Wazuh, internal GitLab) that nobody tracks at all.

```yaml
# blackbox.yml
modules:
  https_2xx:
    prober: http
    timeout: 10s
    http:
      fail_if_not_ssl: true
```

```yaml
# prometheus.yml - probe every public AND internal HTTPS endpoint
  - job_name: tls-expiry
    metrics_path: /probe
    params:
      module: [https_2xx]
    static_configs:
      - targets: [https://app.example.com, https://harbor.example.com, https://gitlab.example.com]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox:9115
# alert rule:
#   expr: probe_ssl_earliest_cert_expiry - time() < 14 * 24 * 3600
#   for: 1h
```

```bash
# one-off check from any machine
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -enddate
```

```
notAfter=Nov 14 08:21:07 2026 GMT
```

Run a **renewal game day** each quarter: in staging, close port 80 or revoke the DNS token, and confirm that the alert fires before the certificate expires. Prefer ACME clients that support ARI (ACME Renewal Information), and renew at about two-thirds of the lifetime.

Sources: [Let's Encrypt: Expiration Emails](https://letsencrypt.org/docs/expiration-emails/) · [Let's Encrypt: Decreasing Certificate Lifetimes to 45 Days](https://letsencrypt.org/2025/12/02/from-90-to-45) · Search: [Reddit r/selfhosted: lets encrypt expiration monitoring](https://www.reddit.com/r/selfhosted/search/?q=lets+encrypt+expiration+emails+monitoring&restrict_sr=1) · [Reddit r/PrometheusMonitoring: blackbox ssl expiry](https://www.reddit.com/r/PrometheusMonitoring/search/?q=blackbox+ssl+expiry+alert&restrict_sr=1).

---

## 4. Learning path

### 4.1 Fresher to senior

| Stage | Learn | Prove it |
|---|---|---|
| Fresher · L0 | HTTP, the Host header, ports, DNS; what a reverse proxy does; 1.1–1.3 | Explain the 1.2 diagram out loud; enable an nginx site and reload it the right way (9.1) |
| Junior · L1 | nginx and Apache vhosts, Traefik labels, ACME basics; section 2 | Build section 2 on a VM; move Apache to 81/444 behind Traefik (7.1, 5.5) |
| Mid-level · L2 | The status-code map, access logs, ACME debugging, redirects, WebSockets | Fix any of 5.1–5.6, 6.1 or 9.2–9.5 in under 15 minutes from the logs alone |
| Senior · L3 | Swarm, TCP routers, forward auth, client IPs, registries behind proxies, upgrades | Run the Docker 29 or v2-to-v3 upgrade drill on staging with a written rollback (7.2, 7.5) |
| Senior/Lead · L4 | Timeout and keep-alive budgets, capacity, HA, Gateway API, change management | Write the hop-by-hop timeout table for your platform; run a renewal game day (3.7, 8.4) |

Career context and interview questions: [40 Career ladder](40-career-ladder.md).

### 4.2 Courses, docs and videos

1. *DevOps Pre-Requisite Course* ([course](https://kodekloud.com/courses/devops-pre-requisite-course)): Web Server → Apache Web Server, IPs and Ports; Security → SSL & TLS Basics. **L0.**
2. *Nginx For Beginners* ([course](https://kodekloud.com/courses/nginx-for-beginners), [Reverse Proxy notes](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page)): Intermediate Config → Virtual Servers & Multiple Sites, Reverse Proxy, Load Balancer; Security → HTTPS; Performance → Monitoring & Troubleshooting. **L1.**
3. *Prep Course - Linux Foundation Certified System Administrator (LFCS)* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs), [Implement Reverse Proxies and Load Balancers notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)): Networking → Implement Reverse Proxies and Load Balancers, Configure Packet Filtering (Firewall); Essential Commands → Work With SSL Certificates. **L1–L2.**
4. *Docker Certified Associate* ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)): Docker Engine → Publishing Ports, Troubleshooting Docker Daemon; Docker Swarm → Swarm Services, Docker Overlay Network, Scaling, Rolling Updates and Rollbacks. **L2–L3.**
5. *Kubernetes Networking Deep Dive* ([course](https://kodekloud.com/courses/kubernetes-networking), [Traefik Overview notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)): Kubernetes Ingress → Traefik Overview, Demo/Lab: Traefik Installation, Demo: Traefik Observability; Network Security → Cert Manager and Let's Encrypt, Lab: Securing Ingress. **L3.**
6. *Certified Kubernetes Administrator (CKA)* ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)): Networking → Ingress, Gateway API. **L3–L4.**
7. *Prep Course - Prometheus Certified Associate (PCA)* ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) for 3.4 and 3.7. **L4.**

**Gaps KodeKloud does not cover:** Traefik with Docker labels, Caddy, HAProxy and NPM. Fill them with:

- **Traefik docs.** The [Docker quick start](https://doc.traefik.io/traefik/getting-started/docker/) and the [Docker routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).
- **Forum top topics as a syllabus.** The [Traefik forum all-time top topics](https://community.traefik.io/top?period=all) list the questions everyone hits, in order of views. The [HAProxy forum top topics](https://discourse.haproxy.org/top?period=all) do the same for HAProxy.
- **Videos.** Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* ([video](https://www.youtube.com/watch?v=CmUzMi5QLzI), 32 min, current v3 syntax) and KodeKloud *NGINX For Beginners | NGINX Tutorial* ([video](https://www.youtube.com/watch?v=Hfg7_y0fGTg)).

### 4.3 Practice ladder

1. **L0.** whoami behind Traefik (2.5). Then break the Host rule and read the plain-text 404.
2. **L1.** Apache on :81 behind Traefik through the file provider, with the UFW rule (5.5).
3. **L1.** nginx on a second VM: upload limit, WebSocket echo server, timeouts (10.2, 9.5, 10.1).
4. **L2.** The ops-ladder drill: a wrong port gives a 502, and you fix it from Traefik's logs alone (5.2).
5. **L2.** Staging ACME with a stale AAAA record (6.1), then DNS-01 for an internal-only name (6.2).
6. **L3.** GitLab SSH through a TCP entryPoint, and Authelia or Authentik in front of whoami (8.1, 8.2).
7. **L3.** A two-node Swarm with host-mode Traefik: real client IPs, start-first deploys with zero 502s (8.3, 7.3).
8. **L4.** Reproduce the keep-alive race and remove it (8.4). Then write the timeout table for every hop.
9. **L4.** On a k3s VM, translate three ingress-nginx annotations to Traefik and to Gateway API (8.5).

---

## 5. Traefik: routing and backends

The six problems below are the bulk of the Traefik forum's all-time top topics. Before you start, run one test request with `curl --resolve` and look at Traefik's access log, so you know which of them you have (1.9).

### 5.1 Traefik answers 404 page not found

> **Seen as:** plain-text `404 page not found`, with an empty RouterName in the access log · **Where:** Traefik or Dokploy on Docker · **Level:** [L2 · Mid] · **How common:** a 21k-view forum thread, a 2025-26 top topic, and its own section in Dokploy's troubleshooting docs

**Why it happens:** the request reached Traefik, but no router on that entryPoint matched it, so Traefik answered itself. The usual causes:

- The Host rule doesn't match what the client sends: a typo, www vs apex, or access by IP.
- Traefik ignores the container. With `exposedByDefault=false` it needs `traefik.enable=true`. Traefik also skips containers that aren't running or whose health check is failing or still starting.
- The router is attached to `web` while the request arrived on `websecure`, or the entryPoint name is misspelled.
- A Dokploy Compose app or template got a new domain without a redeploy, and labels are only read at deploy time.
- Swarm services have their labels outside `deploy.labels` (7.3), or the Docker provider is broken and no routers exist at all (7.2).

**Diagnose:**

```bash
# 1. Ask Traefik directly: no DNS, no browser cache
curl -sk -o /dev/null -w '%{http_code}\n' --resolve app.example.com:443:203.0.113.10 https://app.example.com/
# 2. Which routers exist? (through the protected dashboard router from 2.4)
curl -s -u admin:PASSWORD https://traefik.example.com/api/http/routers | jq -r '.[] | select(.provider != "internal") | [.name, .rule, (.entryPoints|join(",")), .status] | @tsv'
# 3. Did Traefik see the container at all?
docker inspect -f '{{json .Config.Labels}}' app | jq 'with_entries(select(.key|startswith("traefik")))'
docker ps --filter name=app --format '{{.Names}}  {{.Status}}'
```

```
404
dashboard@docker  Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))  websecure  enabled
whoami@docker     Host(`whoami.example.com`)  websecure  enabled
{
  "traefik.enable": "true",
  "traefik.http.routers.app.rule": "Host(`app.example.com`)"
}
app  Up 2 minutes (health: starting)
```

**What the output tells you:** the labels are right, but there is no `app@docker` router, because the container is still `health: starting`. Traefik adds it only once it is healthy. If the router exists but lists only `web`, it is an entryPoint mismatch. If this list is empty (the jq filter hides Traefik's own `@internal` routers such as `acme-http` and `ping`), the provider is broken (7.2).

**Fix:**

```yaml
# Compose labels (Docker provider)
labels:
  - traefik.enable=true
  - traefik.http.routers.app.rule=Host(`app.example.com`) || Host(`www.app.example.com`)
  - traefik.http.routers.app.entrypoints=websecure
  - traefik.http.routers.app.tls.certresolver=letsencrypt
  - traefik.http.services.app.loadbalancer.server.port=3000
```

Make the health check pass (or fix a wrong check). In Dokploy, click **Redeploy** after any domain change on a Compose app or template. For Applications, check the domain's container port.

**Why this fix works:** a router now exists, matches the name the client sends, and listens on the entryPoint the request arrives on, and the container is healthy enough to be included. Don't "fix" a 404 by adding a catch-all router that sends everything to one app. It hides the next routing mistake.

**Prevent it:** use one label template per app. After every deploy, run a `curl --resolve` smoke test. Keep the JSON access log on, and remember that the plain-text 404 means Traefik's routing, never the app.

**Next step:** [29 §4.3 Routers: rules and priority](29-learn-webservers-proxies.md#43-routers-rules-and-priority) · [25 §3 Status codes: which layer said it](25-playbook-site-down.md#3-status-codes-which-layer-said-it) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Can't seem to get new Docker containers to show up as Routers](https://community.traefik.io/t/cant-seem-to-get-new-docker-containers-to-show-up-as-routers/29500) · [Traefik docs: Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/) · [Dokploy docs: Domains troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+%22404+page+not+found%22+docker+labels) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=%22404+page+not+found%22+docker+labels&restrict_sr=1)

### 5.2 Traefik returns 502 Bad Gateway

> **Seen as:** `Bad Gateway`; debug log `error="dial tcp 10.0.1.15:80: connect: connection refused"` · **Where:** a container app behind Traefik or Dokploy · **Level:** [L2 · Mid] · **How common:** a 32k-view forum thread, a 2026 thread about `loadbalancer.server.port`, and a Bad Gateway section in Dokploy's docs

**Why it happens:** a router matched, but the backend refused the connection. Traefik guesses the port: with one exposed port it uses that one, and with several it takes the first, lowest-numbered one. Images that expose other ports than the one the app uses, or a Dokploy domain set to the wrong container port, send Traefik to a closed port. The second classic is an app that listens on 127.0.0.1 inside its container (Vite and Next dev servers, Flask defaults). Traefik connects to the container's network IP, so loopback-only apps refuse it. Less often the app is still starting or crash-looping, or Dokploy's Ports feature is enabled on a domain-routed app. An HTTPS-only backend gives a 400 or a 500 instead (5.6).

**Diagnose:**

```bash
# what Traefik tried (log.level=DEBUG, or OriginStatus 0 + 502 in the access log)
docker logs --since 10m traefik 2>&1 | grep -E 'dial tcp|connection refused' | tail -2
# which ports the image exposes (Traefik's guess when no port label exists)
docker inspect -f '{{json .Config.ExposedPorts}}' app
# what the app REALLY listens on, from inside its network (and PID) namespace; without --pid the Process column is empty
docker run --rm --net container:app --pid container:app nicolaka/netshoot ss -ltnp
```

```
... error="dial tcp 10.0.1.15:80: connect: connection refused"
{"3000/tcp":{},"80/tcp":{}}
State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
LISTEN 0      511         127.0.0.1:3000       0.0.0.0:*     users:(("node",pid=1,fd=21))
```

**What the output tells you:** two bugs. Traefik dialled port 80, the lowest exposed port, while the app uses 3000. The app also listens only on 127.0.0.1, so even port 3000 would be refused from Traefik's side.

**Fix:**

```yaml
# 1. Never let Traefik guess the port
labels:
  - traefik.http.services.app.loadbalancer.server.port=3000
```

```bash
# 2. Make the app listen on all interfaces inside its container
#    Node:     server.listen(3000, '0.0.0.0')
#    Gunicorn: gunicorn -b 0.0.0.0:8000 app:app
#    Vite:     vite --host 0.0.0.0   (or server.host: true)
# 3. Prove it from the proxy network, the way Traefik connects
docker run --rm --network proxy nicolaka/netshoot curl -s -o /dev/null -w '%{http_code}\n' http://app:3000/
```

In Dokploy, set the domain's container port to the port the app listens on, turn off the Ports feature for domain-routed apps, and redeploy.

**Why this fix works:** an explicit port removes the guess, and `0.0.0.0` makes the app reachable on the network Traefik uses. Don't publish the app's port on the host (`-p 3000:3000`) to "test around" the proxy. It bypasses UFW, and the port tends to stay open.

**Prevent it:** set `loadbalancer.server.port` on every service, even single-port images. Give every image a health check. Practise the ops-ladder drill: break the port on purpose and fix it from Traefik's logs alone.

**Next step:** [26 §7 Dokploy, Traefik and Swarm](26-playbook-containers-k8s.md#7-dokploy-traefik-and-swarm) · [25 §7 Proxy error scenarios](25-playbook-site-down.md#7-proxy-error-scenarios-502-503-504) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Bad Gateway 502 with docker containers](https://community.traefik.io/t/bad-gateway-502-with-docker-containers/3044) · [Traefik forum: works only if loadbalancer.server.port is included](https://community.traefik.io/t/traefik-works-but-only-if-loadbalancer-server-port-is-included/29970) · [Dokploy docs: Bad Gateway](https://docs.dokploy.com/docs/core/troubleshooting/domains) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+502+bad+gateway+docker+port) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=502+bad+gateway+loadbalancer.server.port&restrict_sr=1)

### 5.3 504 or flapping: container on several networks

> **Seen as:** `Gateway Timeout`; warning `Could not find network named "proxy" for container "/shop-app-1". Maybe you're missing the project's prefix in the label?` (v2 adds `Defaulting to first available network.`) · **Where:** Compose or Dokploy apps with a private DB network plus the proxy network · **Level:** [L2 · Mid] · **How common:** a 30k-view forum thread; GitHub traefik#5731; the opening error of the 2025-26 Authentik thread

**Why it happens:** Traefik connects to the container's IP on **one** Docker network. If the container is on several, Traefik picks one at random unless `traefik.docker.network` says which. If it picks the private DB network, which Traefik isn't attached to, the dial times out and Traefik returns 504. Compose also prefixes network names it creates with the project name, so a label that says `proxy` matches nothing when Docker actually created `shop_proxy`. Traefik's response-header timeout is 0 by default, so a Traefik 504 almost always means the dial failed, not that the app was slow.

**Diagnose:**

```bash
docker inspect -f '{{json .NetworkSettings.Networks}}' shop-app-1 | jq -r 'to_entries[] | "\(.key) \(.value.IPAddress)"'
docker inspect -f '{{json .NetworkSettings.Networks}}' traefik | jq -r 'keys[]'
docker logs traefik 2>&1 | grep -i 'could not find network' | tail -1
```

```
shop_backend 172.22.0.4
shop_proxy 172.21.0.6
proxy
traefik_socket
... Could not find network named "proxy" for container "/shop-app-1". Maybe you're missing the project's prefix in the label?
```

**What the output tells you:** Traefik lives on `proxy`, but Compose created a new `shop_proxy` for the app because the network wasn't declared external. Traefik fell back to `shop_backend` (172.22.0.4), a network it cannot reach.

**Fix:**

```yaml
services:
  app:
    networks: [backend, proxy]
    labels:
      - traefik.docker.network=proxy        # Dokploy: dokploy-network
networks:
  backend:
    internal: true                          # DB-only network, no route to the outside
  proxy:
    external: true
    name: proxy                             # an exact name: no project prefix
```

**Why this fix works:** `external` plus `name` stops Compose from creating a prefixed copy, and the label tells Traefik which IP to dial. Keep databases on internal networks that Traefik never joins. Don't attach Traefik to every app network to "make it work". That gives the edge proxy a path to every database.

**Prevent it:** set `traefik.docker.network` (or `providers.docker.network`) whenever a container has more than one network, and alert on the "Could not find network" warning in Loki or Wazuh.

**Next step:** [30 §7 Networking](30-learn-docker.md#7-networking) · [26 §4 Docker: DNS and container networking](26-playbook-containers-k8s.md#4-docker-dns-and-container-networking) · KodeKloud: *Docker Certified Associate* — Docker Engine – Networking: Networking Deep Dive – Docker · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Traefik gateway timeout](https://community.traefik.io/t/traefik-gateway-timeout/17889) · [GitHub traefik#5731: Could not find network for container](https://github.com/traefik/traefik/issues/5731) · [Traefik docs: Docker routing (network selection)](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+gateway+timeout+docker+multiple+networks) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=traefik+504+multiple+networks&restrict_sr=1)

### 5.4 Static vs dynamic configuration mix-ups

> **Seen as:** `failed to decode configuration from flags: field not found, node: tls` · `middleware "auth@docker" does not exist` · `EntryPoint doesn't exist entryPointName=websecure` · `service "app" error: port is missing` · **Where:** any Traefik install built from copied examples · **Level:** [L2 · Mid] · **How common:** forum threads with 27.8k and 24.5k views, plus "Cannot start traefik" (18k)

**Why it happens:** Traefik has two kinds of config (1.3), and copied examples mix them all the time:

- **Dynamic items in static config.** TLS certificates, middlewares or routers placed in `traefik.yml` or in CLI flags are rejected (`field not found`) or silently ignored.
- **Mixed static sources.** Static config is split across the file, CLI flags and environment variables. Traefik reads only one source, so the other settings "disappear".
- **Missing provider suffix.** A middleware defined in a file must be referenced from labels as `NAME@file`.
- **Wrong reload expectations.** Static changes need a restart, and dynamic files reload only from a watched directory.

**Diagnose:**

```bash
docker logs traefik 2>&1 | head -5                    # startup errors are printed first
docker inspect -f '{{json .Args}}' traefik            # any CLI flags? then traefik.yml is NOT read
curl -s -u admin:PASSWORD https://traefik.example.com/api/rawdata \
  | jq '.routers | to_entries[] | select(.value.status != "enabled") | {name: .key, error: .value.error}'
```

```
2026-10-02T09:14:03Z ERR Command error error="command traefik error: failed to decode configuration from flags: field not found, node: tls"
["--providers.docker=true","--entrypoints.web.address=:80","--tls.options.default.minVersion=VersionTLS12"]
{
  "name": "app@docker",
  "error": [
    "middleware \"auth@docker\" does not exist"
  ]
}
```

**What the output tells you:** a dynamic TLS option was passed as a CLI flag, so Traefik refuses to start. Because flags exist at all, `traefik.yml` is ignored. On a running instance, the router refers to `auth@docker` while the middleware is defined in a file, so it is `auth@file`.

**Fix:**

```yaml
# traefik.yml (STATIC) - top-level keys such as:
#   global, entryPoints, providers, certificatesResolvers, api, ping, log, accessLog, metrics,
#   tracing, serversTransport, core, experimental (never routers, middlewares, services or tls)
providers:
  file:
    directory: /etc/traefik/dynamic
    watch: true
```

```yaml
# dynamic/tls.yml (DYNAMIC) - routers, services, middlewares, tls, serversTransports
tls:
  options:
    default:
      minVersion: VersionTLS12
```

```bash
# remove every CLI flag from the Compose file, reference across providers explicitly:
#   traefik.http.routers.app.middlewares=auth@file
docker compose -f /opt/traefik/compose.yaml up -d --force-recreate traefik   # static change = restart
```

**Why this fix works:** each setting now lives where Traefik reads it, and one static source means nothing is silently dropped. The `@file` suffix names the provider that owns the middleware.

**Prevent it:** keep the two-part layout from 2.1, lint YAML in CI, and check `/api/rawdata` (or the dashboard's error badges) after every change. Learn the routers, services and middlewares model before copying labels.

**Next step:** [29 §4.1 Static vs dynamic configuration](29-learn-webservers-proxies.md#41-static-vs-dynamic-configuration) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Demo/Lab: Traefik Installation · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: field not found, node: tls](https://community.traefik.io/t/traefik-error-failed-to-decode-configuration-from-flags-field-not-found-node-tls/3975) · [Traefik forum: all-time top topics](https://community.traefik.io/top?period=all) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+%22field+not+found%22+node) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=middleware+does+not+exist&restrict_sr=1)

### 5.5 Routing to a service on the host or LAN

> **Seen as:** 504 or 502 for file-provider routes; `dial tcp: lookup host.docker.internal on 127.0.0.11:53: no such host`; `dial tcp 192.0.2.10:81: i/o timeout` · **Where:** Apache moved to :81 (your setup), Proxmox, a NAS or printers behind Traefik · **Level:** [L2 · Mid] · **How common:** forum threads with 32.5k and 22.5k views; GitHub traefik#8753 (34 comments)

**Why it happens:** Docker labels can only describe containers, so a host or LAN service needs a **file-provider** route with a server URL. Inside its container, Traefik's 127.0.0.1 is the container itself, not the host. `host.docker.internal` doesn't exist on Linux unless the container was started with `host-gateway`, and Dokploy's `docker run` doesn't add it. The host service may also listen only on 127.0.0.1. And UFW's default-deny INPUT policy drops traffic from Docker networks to host ports. Published container ports bypass UFW, but container-to-host traffic does not. On Dokploy, Traefik's traffic to the host arrives on `docker_gwbridge` (172.18.0.0/16).

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :81'                                   # 127.0.0.1:81 or *:81?
docker exec dokploy-traefik wget -qO- -T 5 http://192.0.2.10:81/ >/dev/null; echo "exit=$?"
sudo journalctl -k --since '10 min ago' | grep 'UFW BLOCK' | grep 'DPT=81' | tail -1
```

```
LISTEN 0 511 127.0.0.1:81 0.0.0.0:* users:(("apache2",pid=1123,fd=4))
wget: download timed out
exit=1
kernel: [UFW BLOCK] IN=docker_gwbridge OUT= MAC=02:42:... SRC=172.18.0.3 DST=192.0.2.10 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=40812 DF PROTO=TCP SPT=40512 DPT=81 WINDOW=64240 RES=0x00 SYN URGP=0
```

**What the output tells you:** two blocks in a row. UFW drops Traefik's SYN coming from `docker_gwbridge` (source 172.18.0.3), and even with UFW open, Apache only listens on loopback.

**Fix:**

```apache
# /etc/apache2/ports.conf - Apache off 80/443, reachable from Docker networks
Listen 81
<IfModule ssl_module>
    Listen 444
</IfModule>
```

```bash
sudo apachectl configtest && sudo systemctl reload apache2
# allow only Traefik's path to :81, not the internet
sudo ufw allow in on docker_gwbridge to 192.0.2.10 port 81 proto tcp comment 'traefik -> apache'
# plain Compose Traefik (section 2): its traffic arrives on the proxy network's br-XXXXXXXXXXXX bridge instead
# (docker network inspect proxy -f '{{.Id}}' gives the first 12 characters), so scope the rule to that interface
```

```yaml
# /etc/dokploy/traefik/dynamic/legacy-apache.yml (plain Traefik: /opt/traefik/dynamic/)
http:
  routers:
    legacy:
      rule: Host(`old.example.com`)
      entryPoints: [websecure]
      service: legacy
      tls:
        certResolver: letsencrypt
  services:
    legacy:
      loadBalancer:
        servers:
          - url: "http://192.0.2.10:81"   # host LAN IP; plain Compose Traefik can use host.docker.internal:81
```

**Why this fix works:** the file provider describes a non-container backend, and the host's LAN IP is reachable from any Docker network. The UFW rule is scoped to the bridge interface, so port 81 stays closed to the internet. Don't run Traefik with `network_mode: host` just to reach localhost. You lose isolation, and on Dokploy you can't anyway.

**Prevent it:** write the host-service pattern into the runbook, mount a directory for the file provider (not single files), and re-test container-to-host paths after every UFW change.

**Next step:** [21 §8 Route the legacy Apache sites through Traefik](21-case-apache-443-dokploy.md#8-phase-7-route-the-legacy-apache-sites-through-traefik) · [29 §8 Capstone lab: Apache behind Traefik](29-learn-webservers-proxies.md#8-capstone-lab-apache-behind-traefik) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure Packet Filtering (Firewall) · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Forwarding one Traefik endpoint to dockers host network](https://community.traefik.io/t/forwarding-one-traefik-endpoint-to-dockers-host-network/5675) · [Traefik forum: Reverse proxy to external host](https://community.traefik.io/t/reverse-proxy-to-external-host/3615) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+container+cannot+reach+host+port+ufw) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=host.docker.internal+file+provider&restrict_sr=1)

### 5.6 HTTPS backend with a self-signed certificate

> **Seen as:** `Internal Server Error` (500); log `tls: failed to verify certificate: x509: certificate signed by unknown authority` or `x509: cannot validate certificate for 192.168.10.5 because it doesn't contain any IP SANs`; from the backend `400 Bad Request: Client sent an HTTP request to an HTTPS server.` · **Where:** Proxmox (:8006), Portainer (:9443), UniFi, the Wazuh dashboard · **Level:** [L2 · Mid] · **How common:** forum threads "insecureSkipVerify explanation" (57.5k views), "Problem using ssl Backend with selfsigned certificates" (42k), "Proxmox behind Traefik" (27k)

**Why it happens:** many admin UIs listen only on HTTPS, with a self-signed or private-CA certificate. Traefik verifies backend certificates by default. A failed verification is not a network error, so Traefik returns 500, not 502. Without `scheme=https`, Traefik speaks plain HTTP to a TLS port and the backend answers 400. A serversTransport defined in static config, or referenced without `@file`, is simply not found. Connecting by IP to a certificate that only lists DNS names also needs `serverName`.

The **Wazuh dashboard** adds a port clash. Its all-in-one install listens on 443, which collides with Traefik (`FATAL Error: Port 443 is already in use`). Move it to 8443, then proxy it as an HTTPS backend. Agent ports 1514/1515 and the API on 55000 are separate and must not go through HTTP routers.

**Diagnose:**

```bash
docker logs --since 10m traefik 2>&1 | grep -i x509 | tail -1
# what does the backend present?
openssl s_client -connect 192.168.10.5:8006 -servername pve.example.internal </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -subject -ext subjectAltName
# Wazuh on the same host: who owns which port now?
sudo ss -ltnp | grep -E ':(443|8443|1514|1515|55000) '
```

```
... error="tls: failed to verify certificate: x509: certificate signed by unknown authority"
issuer=CN = Proxmox Virtual Environment, OU = 4f1d0c2e-5b7a-4c39-9d0e-1a2b3c4d5e6f, O = PVE Cluster Manager CA
subject=OU = PVE Cluster Node, O = Proxmox Virtual Environment, CN = pve.example.internal
X509v3 Subject Alternative Name:
    DNS:pve, DNS:pve.example.internal, IP Address:192.168.10.5
```

**What the output tells you:** the backend certificate comes from Proxmox's own cluster CA. Give Traefik that CA and a `serverName` that is in the SAN list. Don't turn off verification.

**Fix:**

```yaml
# /opt/traefik/dynamic/pve.yml
http:
  serversTransports:
    pve-ca:
      serverName: pve.example.internal
      rootCAs:
        - /certs/pve-root-ca.pem        # copy of /etc/pve/pve-root-ca.pem from the Proxmox host
  routers:
    pve:
      rule: Host(`pve.example.com`)
      entryPoints: [websecure]
      middlewares: [lan-only@file]
      service: pve
  services:
    pve:
      loadBalancer:
        serversTransport: pve-ca
        servers:
          - url: "https://192.168.10.5:8006"
```

```bash
# container backends with labels:
#   traefik.http.services.portainer.loadbalancer.server.scheme=https
#   traefik.http.services.portainer.loadbalancer.serverstransport=internal-ca@file
# Wazuh dashboard: move it off 443, then route https://192.0.2.10:8443 with a transport
# that trusts /etc/wazuh-dashboard/certs/root-ca.pem
sudo sed -i 's/^server.port: .*/server.port: 8443/' /etc/wazuh-dashboard/opensearch_dashboards.yml
sudo systemctl restart wazuh-dashboard
```

**Why this fix works:** `rootCAs` keeps verification on, so a machine on the LAN can't impersonate the backend, while trusting your own CA. A per-service transport scopes that trust, and `serverName` fixes SNI and SAN matching for IP URLs. Lab only: a per-service transport with `insecureSkipVerify: true`. Never set the global static `serversTransport.insecureSkipVerify`, which turns verification off for every backend.

**Prevent it:** run one small internal CA (the same one Harbor uses) and give Traefik its root. Keep a list of which backends speak HTTPS. Decide on the edge proxy **before** installing an all-in-one package that grabs 443.

**Next step:** [37 §4 TLS and PKI](37-learn-security-devsecops.md#4-tls-and-pki) · [48 Wazuh deep dive](48-wazuh-and-security-tools.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands: Work With SSL Certificates · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: insecureSkipVerify explanation](https://community.traefik.io/t/insecureskipverify-explanation/2195) · [Traefik forum: Proxmox behind Traefik](https://community.traefik.io/t/proxmox-behind-traefik/9338) · [Traefik docs: ServersTransport](https://doc.traefik.io/traefik/reference/routing-configuration/http/load-balancing/serverstransport/) · [Wazuh group: dashboard --port override, 443 conflict](https://groups.google.com/g/wazuh/c/sXlJ4zGgLGA) · [Wazuh docs: dashboard behind NGINX](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/configuring-third-party-certs/ssl-nginx.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+insecureSkipVerify+self+signed+backend) · [Reddit r/Wazuh](https://www.reddit.com/r/Wazuh/search/?q=dashboard+reverse+proxy+traefik+nginx&restrict_sr=1)

---

## 6. Traefik: certificates

### 6.1 TRAEFIK DEFAULT CERT instead of Let's Encrypt

> **Seen as:** browser `NET::ERR_CERT_AUTHORITY_INVALID`, issuer `TRAEFIK DEFAULT CERT`; log `Unable to obtain ACME certificate for domains ... acme: error: 400 :: urn:ietf:params:acme:error:connection :: ... Timeout during connect (likely firewall problem)` or `permissions 644 for /letsencrypt/acme.json are too open, please use 600` · **Where:** Traefik or Dokploy with HTTP-01 · **Level:** [L2 · Mid] · **How common:** forum threads with 21.9k, 18.5k, 17.7k and 12.5k views; the same class tops NPM's issue tracker (14.1)

**Why it happens:** when Traefik has no valid certificate for a name, it serves its self-signed default certificate. The real reason is always in the ACME log lines:

- **Port 80 isn't reachable from the internet.** Router NAT, a cloud security group, the ISP, or another service on port 80 blocks it.
- **DNS points elsewhere, or a stale AAAA record exists.** Let's Encrypt prefers IPv6, so a wrong AAAA record can fail validation even when IPv4 is right.
- **No certificate was requested.** The router has only `tls=true` and no `tls.certresolver`, so Traefik never asks for one.
- **TLS-ALPN-01 behind a CDN.** It can't work behind a TLS-terminating CDN.
- **`acme.json` problems.** If it isn't mode 600, Traefik refuses it. If it isn't on a volume, every restart re-requests certificates until rate limits hit.
- **Dokploy order.** The domain was added before DNS pointed at the server.

**Diagnose:**

```bash
docker logs dokploy-traefik 2>&1 | grep -iE 'unable to obtain|acme' | tail -2
dig +short A app.example.com; dig +short AAAA app.example.com     # compare with the server's real IPs
# from OUTSIDE your network (phone hotspot, another VPS): expect Traefik's 404, not a timeout
curl -s -m 10 -o /dev/null -w '%{http_code}\n' http://app.example.com/.well-known/acme-challenge/test
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -issuer
sudo stat -c '%a %n' /etc/dokploy/traefik/dynamic/acme.json
```

```
ERR Unable to obtain ACME certificate for domains error="... acme: error: 400 :: urn:ietf:params:acme:error:connection :: 2001:db8:5::10: Timeout during connect (likely firewall problem)" providerName=letsencrypt.acme routerName=app-web@file
203.0.113.10
2001:db8:5::10
404
issuer=CN = TRAEFIK DEFAULT CERT
600 /etc/dokploy/traefik/dynamic/acme.json
```

**What the output tells you:** IPv4 works (an outside curl gets Traefik's 404), but Let's Encrypt validated over IPv6. The AAAA record points to an address that doesn't reach this host. The file permissions are fine.

**Fix:**

```bash
# DNS: delete or correct the stale AAAA record, then wait out its TTL.
# Network: port 80 must reach Traefik from the internet for HTTP-01. Docker-published ports bypass UFW,
# so check router NAT and cloud security groups. If you see a permissions error:
sudo chmod 600 /etc/dokploy/traefik/dynamic/acme.json
docker restart dokploy-traefik
```

```yaml
# plain Traefik router labels: request a certificate, not just "tls=true"
- traefik.http.routers.app.entrypoints=websecure
- traefik.http.routers.app.tls.certresolver=letsencrypt
```

In Dokploy: point DNS first, then add the domain, then redeploy. While you experiment, use the staging CA (2.2) and remove its entries from `acme.json` before you switch back to production.

**Why this fix works:** HTTP-01 is Let's Encrypt connecting to port 80 of whatever DNS returns, IPv6 first. Once that path works, Traefik retries by itself. Don't delete `acme.json` again and again. Let's Encrypt allows only 5 certificates for the same set of names per 7 days, and a loop of fresh requests locks you out for days.

**Prevent it:** before adding a domain, check DNS (A and AAAA) and port 80 from outside. Persist `acme.json`, alert on "Unable to obtain ACME certificate" log lines, and monitor expiry (3.7).

**Next step:** [25 §6 TLS scenarios](25-playbook-site-down.md#6-tls-scenarios) · [29 §4.7 Certificates](29-learn-webservers-proxies.md#47-certificates-acme-resolvers-and-the-default-certificate) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: How to fix ACME error 400 connection refused](https://community.traefik.io/t/how-to-fix-acme-error-400-connection-refused/8533) · [Traefik forum: falling back to self-signed certificate](https://community.traefik.io/t/traefik-falling-back-to-self-signed-certificate-instead-of-requesting-lets-encrypt-certificate/29367) · [Traefik forum: permission denied with acme.json 600](https://community.traefik.io/t/getting-permission-denied-error-with-lets-encrypt-if-acme-json-permission-is-set-to-600/4495) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22TRAEFIK+DEFAULT+CERT%22+letsencrypt) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=%22TRAEFIK+DEFAULT+CERT%22&restrict_sr=1)

### 6.2 DNS-01 and wildcard certificates fail

> **Seen as:** Traefik `cloudflare: failed to find zone com.: zone could not be found` · `NS 127.0.0.11:53 did not return the expected TXT record` · `time limit exceeded`; Caddy `module not registered: dns.providers.cloudflare`; NPM/certbot `CloudFlareAPIError adding TXT record: 10000 Authentication error` · **Where:** wildcards, internal-only hosts, Traefik 3.7.6+ · **Level:** [L3 · Senior] · **How common:** Caddy's most-read wiki page (170k views) is about DNS modules; past-year Traefik threads on the 3.7.6+ regression, zone detection and the new Hetzner API

**Why it happens:** DNS-01 is the only challenge that issues wildcards. It also works for on-prem services the internet can't reach. It depends on a DNS provider API token and on propagation checks that ask DNS whether the TXT record is visible. What goes wrong:

- **Token scope.** Cloudflare needs Zone:DNS:Edit plus Zone:Zone:Read.
- **Split horizon.** Zone detection and propagation checks go through Docker's embedded resolver (127.0.0.11), then the host, then your internal DNS. An internal copy of `example.com` never shows the TXT record.
- **ACME library change.** Traefik 3.7.6+ moved to lego v5, and some Cloudflare setups broke (3.7.5 was reported as working).
- **Provider API changes.** Hetzner's new DNS API is one example.
- **Caddy's standard binary** contains no DNS providers at all.

**Diagnose:**

```bash
docker logs traefik 2>&1 | grep -iE 'propagation|zone|dns01' | tail -1
docker exec traefik cat /etc/resolv.conf | grep nameserver
dig +short TXT _acme-challenge.example.com @1.1.1.1          # what the world sees (while a challenge is pending)
dig +short TXT _acme-challenge.example.com @192.168.1.53     # what your internal DNS answers
```

```
... error="... propagation: time limit exceeded: last error: recursive nameservers: NS 127.0.0.11:53 did not return the expected TXT record [fqdn: _acme-challenge.example.com., value: Nn3vQ0mT1kq2c8Lr0b8Hk7c5Zx1yP4wq6s9tA2dE3fG]" providerName=le-dns.acme
nameserver 127.0.0.11
"Nn3vQ0mT1kq2c8Lr0b8Hk7c5Zx1yP4wq6s9tA2dE3fG"
```

**What the output tells you:** the provider API worked, because public DNS already has the TXT record. Traefik checked through 127.0.0.11, which forwards to an internal DNS server with its own `example.com` zone, and that server returns nothing. This is a split-horizon problem, not a token problem.

**Fix:**

```yaml
# traefik.yml: check propagation against public resolvers (full resolver block in 2.2)
certificatesResolvers:
  le-dns:
    acme:
      dnsChallenge:
        provider: cloudflare
        resolvers: ["1.1.1.1:53", "1.0.0.1:53"]
        # 3.7.6+ Cloudflare regression, forum workaround until a fixed 3.7.x:
        # propagation:
        #   requireAllRNS: false
```

```yaml
# router labels: ask for the wildcard explicitly; the token comes from CF_DNS_API_TOKEN_FILE (2.4)
- traefik.http.routers.app.tls.certresolver=le-dns
- traefik.http.routers.app.tls.domains[0].main=example.com
- traefik.http.routers.app.tls.domains[0].sans=*.example.com
```

```dockerfile
# Caddy with a DNS provider: build it in
FROM caddy:2-builder AS builder
RUN xcaddy build --with github.com/caddy-dns/cloudflare
FROM caddy:2
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
# Caddyfile site block:  tls { dns cloudflare {env.CF_API_TOKEN} }
```

**Why this fix works:** public resolvers see what Let's Encrypt sees. Explicit `tls.domains` tells the resolver what to order, since ACME can't derive a wildcard from a Host rule. A token scoped to one zone, read from a secret file, limits the damage if it leaks.

**Prevent it:** prefer DNS-01 for internal services, since it needs no inbound port 80. Keep least-privilege tokens in secrets. Pin proxy minor versions and read the release notes, because ACME library upgrades change behaviour. Rebuild custom Caddy images on every release.

**Next step:** [28 §8 DNS in depth](28-learn-networking.md#8-dns-in-depth) · [6.1](#61-traefik-default-cert-instead-of-lets-encrypt) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: ACME Cloudflare not working after 3.7.6+](https://community.traefik.io/t/acme-cloudflare-not-working-after-3-7-6/29983) · [Caddy wiki: How to use DNS provider modules in Caddy 2](https://caddy.community/t/how-to-use-dns-provider-modules-in-caddy-2/8148) · [Traefik forum: top topics of the past year](https://community.traefik.io/top?period=yearly) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+dnschallenge+cloudflare+wildcard) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dns+challenge+cloudflare+wildcard+traefik+caddy&restrict_sr=1)

---

## 7. Traefik on Docker, Swarm and Dokploy

### 7.1 Ports 80 and 443 already taken

> **Seen as:** `Bind for 0.0.0.0:443 failed: port is already allocated` · `listen tcp4 0.0.0.0:80: bind: address already in use` · `AH00072: make_sock: could not bind to address [::]:443` · `nginx: [emerg] bind() to 0.0.0.0:80 failed (13: Permission denied)` · **Where:** one on-prem host running Apache, nginx, NPM, GitLab, Harbor or the Wazuh dashboard next to Dokploy · **Level:** [L1 · Junior] · **How common:** your own Apache-vs-Dokploy incident; the forum thread on running Traefik and NPM on one server (27k views); NPM #2750 (87 comments)

**Why it happens:** only one process can own a TCP port on a given address. Ubuntu enables `apache2` right after install. GitLab Omnibus, Harbor and the Wazuh dashboard each bring their own web server on 80 or 443. A container with `restart: always` takes the port back after a reboot. Error 13 (Permission denied) instead of 98 means a non-root process without `CAP_NET_BIND_SERVICE`, typically rootless Docker or Podman. Dokploy's installer refuses to start if anything listens on 80, 443 or 3000.

**Diagnose:**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 )'
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E ':(80|443)->'
systemctl list-units --type=service --state=running | grep -Ei 'apache|nginx|haproxy|caddy|wazuh|gitlab'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:80              *:*    users:(("apache2",pid=912,fd=3),("apache2",pid=911,fd=3))
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=912,fd=4),("apache2",pid=911,fd=4))
apache2.service   loaded active running The Apache HTTP Server
```

**What the output tells you:** Apache owns both ports on every address (`*:443` is dual-stack), so Traefik can't bind. No container is involved.

**Fix:**

```bash
# One edge proxy owns 80/443: Traefik when Dokploy is installed. Move Apache, as you did:
#   /etc/apache2/ports.conf : Listen 81  and  Listen 444 (inside the ssl_module IfModule block)
#   sites-available/*.conf  : VirtualHost *:80 -> *:81, VirtualHost *:443 -> *:444
sudo apachectl configtest && sudo systemctl restart apache2
sudo systemctl disable --now apache2          # instead, if Apache is no longer needed
# Wazuh dashboard: server.port 8443 (5.6). Rootless Docker (errno 13), persistently:
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee /etc/sysctl.d/99-unpriv-ports.conf && sudo sysctl --system
```

**Why this fix works:** ports are exclusive, so you choose one owner and route everything else behind it (5.5). Don't expose 81 and 444 to the internet "for now". Keep them reachable only from Docker networks.

**Prevent it:** keep a port inventory per host, and before you install a package, check whether it bundles a web server. Disable distro web servers you don't use.

**Next step:** [22 §13 Scenario — bind: Address already in use](22-playbook-ports-inventory.md#13-scenario-bind-address-already-in-use) · [21 §6 Dispatch Apache off 80 and 443](21-case-apache-443-dokploy.md#6-phase-5-dispatch-apache-off-80-and-443) · [35 §1 Apache moved to 81 and 444](35-deployment-patterns.md#1-your-fix-apache-moved-to-81-and-444) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Start, Stop, and Check Status of Network Services · [Apache docs](https://httpd.apache.org/)

**Community threads:** [Traefik forum: Running Traefik and Nginx Proxy Manager on the same Server](https://community.traefik.io/t/running-traefik-and-nginx-proxy-manager-on-the-same-server/15573) · [Wazuh group: FATAL Error: Port 443 is already in use](https://groups.google.com/g/wazuh/c/OHasiOoL8S8) · [NPM #2750: bind() to 0.0.0.0:80 failed (13: Permission denied)](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/2750) · Search: [Server Fault](https://serverfault.com/search?q=%22make_sock%22+%22could+not+bind+to+address%22+443) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=port+443+already+in+use+traefik+apache&restrict_sr=1)

### 7.2 Docker 29: every route vanished

> **Seen as:** `ERR Provider error, retrying in 26.37s error="Error response from daemon: client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version"` · **Where:** Traefik before 3.6.1 (v2 before 2.11.31) after an apt upgrade to Docker Engine 29 · **Level:** [L2 · Mid] · **How common:** GitHub traefik#12253 (112 comments, labelled P0, the top Traefik issue by reactions) and the top forum topic of the past year (32k views)

**Why it happens:** Docker Engine 29.0 (November 2025) dropped API versions older than 1.44. Older Traefik asked for API 1.24, so after a routine `apt upgrade` the Docker provider failed. (unattended-upgrades only does this if someone added Docker's repository to its `Allowed-Origins`; by default it installs Ubuntu security updates only.) Every label-based router disappeared, and sites answered 404 or showed the default certificate. Dokploy's installer pins Docker 28.5.0 only when it installs Docker itself. A later `apt upgrade` can still move the host to 29.

**Diagnose:**

```bash
docker version --format 'server {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'
docker inspect -f '{{.Config.Image}}' dokploy-traefik
docker logs --since 1h dokploy-traefik 2>&1 | grep -c 'too old'
grep -B1 'docker-ce:' /var/log/apt/history.log | tail -2    # the Commandline line sits just above the Upgrade line
```

```
server 29.0.1 api 1.52 min 1.44
traefik:v3.1.2
118
Commandline: apt upgrade -y
Upgrade: docker-ce:amd64 (5:28.5.2-1~ubuntu.24.04~noble, 5:29.0.1-1~ubuntu.24.04~noble)
```

**What the output tells you:** a routine `apt upgrade` moved the engine to 29, and the old Traefik image can't talk to it any more.

**Fix:**

```bash
# Preferred: a Traefik that negotiates the API (3.6.1+; 3.7.x is the supported line)
docker compose -f /opt/traefik/compose.yaml pull traefik && docker compose -f /opt/traefik/compose.yaml up -d traefik
# Dokploy: update Dokploy, or recreate dokploy-traefik with a newer tag (command in 7.4)
# Emergency only, reported in the forum: let dockerd accept old clients again (restarts containers)
sudo mkdir -p /etc/systemd/system/docker.service.d
printf '[Service]\nEnvironment=DOCKER_MIN_API_VERSION=1.24\n' | sudo tee /etc/systemd/system/docker.service.d/min-api.conf
sudo systemctl daemon-reload && sudo systemctl restart docker
# (Docker 29 write-ups also show "min-api-version": "1.24" in /etc/docker/daemon.json; check the daemon.json reference for your version)
# Or roll back the engine and hold it
sudo apt-get install --allow-downgrades docker-ce=5:28.5.2-1~ubuntu.24.04~noble docker-ce-cli=5:28.5.2-1~ubuntu.24.04~noble
sudo apt-mark hold docker-ce docker-ce-cli
```

**Why this fix works:** the real fix is API negotiation inside Traefik. The dockerd override turns deprecated API versions back on, so treat it as a bridge for hours, not months, and remove it after upgrading. Restarting Docker restarts every container, so announce it.

**Prevent it:** hold `docker-ce` and upgrade it deliberately on a staging VM with your proxy first. Alert on `Provider error` lines in Traefik's log.

**Next step:** [30 §12 The daemon and daemon.json](30-learn-docker.md#12-the-daemon-and-daemonjson) · [3.1 Upgrades without surprises](#31-upgrades-without-surprises) · KodeKloud: *Docker Certified Associate* — Docker Engine: Troubleshooting Docker Daemon · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [GitHub traefik#12253: client version 1.24 is too old](https://github.com/traefik/traefik/issues/12253) · [Traefik forum: Traefik stops working, it uses old API version 1.24](https://community.traefik.io/t/traefik-stops-working-it-uses-old-api-version-1-24/29019) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22client+version+1.24+is+too+old%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=%22client+version+1.24+is+too+old%22&restrict_sr=1)

### 7.3 Swarm labels ignored and blips on deploy

> **Seen as:** `service "app" error: port is missing`; routers never appear; short bursts of 502 and 404 during every redeploy · **Where:** Dokploy Applications (Swarm services) and plain Swarm stacks · **Level:** [L3 · Senior] · **How common:** forum threads "Traefik 2.0 Swarm not working with Services on Ports" (16.6k) and "Zero-downtime deployments with Docker Swarm" (12.5k); Dokploy's docs warn that failing health checks stop domains from working

**Why it happens:** Swarm differs from plain Compose in three ways that matter to Traefik:

- **Labels go on the service.** In Swarm, Traefik reads service labels (`deploy.labels`), not container labels, and v3 uses the separate `swarm` provider.
- **No port discovery.** Swarm services don't advertise ports, so `loadbalancer.server.port` is mandatory.
- **Rolling updates kill too early.** The default update order is stop-first, which removes the old task before the new one is ready. Without a health check, "running" doesn't mean "ready". Old tasks also get only 10 s to finish in-flight requests after SIGTERM.

**Diagnose:**

```bash
docker service inspect app --format '{{json .Spec.UpdateConfig}}'
docker service inspect app --format '{{json .Spec.Labels}}' | jq 'with_entries(select(.key|startswith("traefik")))' | head -3
# run this during a deploy: every non-200 is user-visible downtime
while true; do curl -s -o /dev/null -w '%{http_code} ' https://app.example.com/healthz; sleep 0.5; done
```

```
{"Parallelism":1,"FailureAction":"pause","Monitor":5000000000,"MaxFailureRatio":0,"Order":"stop-first"}
{
  "traefik.enable": "true",
  "traefik.http.routers.app.entrypoints": "websecure",
200 200 200 502 502 404 404 404 200 200
```

**What the output tells you:** the labels are on the service, so routing works. The stop-first update leaves a gap: 502 while the old task dies, then 404 while no healthy task exists. If the labels command prints `{}`, the labels sit on the container and Traefik sees nothing.

**Fix:**

```yaml
services:
  app:
    image: registry.example.com/shop/app:1.4.2
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/healthz"]
      interval: 10s
      start_period: 20s
    stop_grace_period: 30s
    deploy:
      replicas: 2
      update_config: {order: start-first, parallelism: 1, failure_action: rollback, monitor: 30s}
      labels:
        - traefik.enable=true
        - traefik.http.routers.app.rule=Host(`app.example.com`)
        - traefik.http.routers.app.entrypoints=websecure
        - traefik.http.services.app.loadbalancer.server.port=3000
```

In Dokploy, set the application's health check and Swarm update settings in its advanced settings, then redeploy.

**Why this fix works:** with start-first plus a health check, an old task keeps serving until its replacement is healthy. The grace period lets in-flight requests finish, provided the app handles SIGTERM. Sticky sessions need Traefik to target task IPs, not the Swarm VIP.

**Prevent it:** give every deployable image a `/healthz` endpoint and a health check. Run the curl loop during staging deploys, and graph the 5xx rate around deploy markers.

**Next step:** [35 §3 Pattern catalogue](35-deployment-patterns.md#3-pattern-catalogue) · [30 §14 Docker Swarm for Dokploy](30-learn-docker.md#14-docker-swarm-for-dokploy) · [45 Dokploy](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm: Scaling, Rolling Updates and Rollbacks · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Zero-downtime deployments with Docker Swarm](https://community.traefik.io/t/zero-downtime-deployments-with-docker-swarm-whats-the-proper-way/10965) · [Traefik forum: Swarm not working with Services on Ports](https://community.traefik.io/t/traefik-2-0-swarm-not-working-with-services-on-ports/1877) · [Dokploy docs: Domains troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+swarm+%22port+is+missing%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+zero+downtime+traefik+start-first&restrict_sr=1)

### 7.4 Dashboard: 404, open on 8080, or a Dokploy outage

> **Seen as:** `404 page not found` on /dashboard; the dashboard open to anyone on http://SERVER_IP:8080; every Dokploy domain down right after clicking **Enable Dashboard** · **Where:** Traefik, Dokploy, k3s · **Level:** [L1 · Junior] · **How common:** forum threads "Traefik Dashboard 404 not found - Docker" (54.5k views) and the basic-auth example (38k); GitHub traefik#5853 (74 comments); Dokploy issues #2722 and #2996

**Why it happens:**

- **Rule doesn't cover both paths.** The dashboard is the internal service `api@internal`. It lives under `/dashboard/` (with the trailing slash) and calls `/api`, so a rule that misses either path gives 404 or a half-loaded page.
- **The open port.** `api.insecure=true` serves the dashboard without authentication on port 8080. If 8080 is published, Docker's NAT bypasses UFW and the dashboard is open to the world.
- **Dokploy's toggle recreates Traefik.** Dokploy's static config uses `api.insecure`, and its Enable Dashboard toggle publishes 8080 by recreating `dokploy-traefik`. If the new container can't start, for example because 8080 is already taken, the old one is already gone and every site is down.
- **k3s.** The Helm chart doesn't expose the dashboard unless its values ask for it.

**Diagnose:**

```bash
curl -sk -o /dev/null -w '%{http_code}\n' --resolve traefik.example.com:443:203.0.113.10 https://traefik.example.com/dashboard/
docker ps -a --filter name=traefik --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo ss -ltnp 'sport = :8080'
```

```
000
dokploy-traefik	Created
LISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:(("docker-proxy",pid=20411,fd=4))
```

**What the output tells you:** nothing answers on 443 at all (`000`). The new `dokploy-traefik` is stuck in `Created`, because another container's docker-proxy already holds 8080.

**Fix:**

```bash
# 1. Restore service first: free 8080 (or turn the toggle off again), or recreate Traefik exactly as install.sh does
docker rm -f dokploy-traefik
docker run -d --name dokploy-traefik --restart always --network dokploy-network \
  -v /etc/dokploy/traefik/traefik.yml:/etc/traefik/traefik.yml \
  -v /etc/dokploy/traefik/dynamic:/etc/dokploy/traefik/dynamic \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -p 80:80/tcp -p 443:443/tcp -p 443:443/udp \
  traefik:v3.6.25          # the tag you ran before; check Dokploy's release notes before changing it
```

```yaml
# 2. A dashboard that needs no published port (plain Traefik labels as in 2.4; on Dokploy the same
#    router can live in a file such as /etc/dokploy/traefik/dynamic/dashboard.yml)
- traefik.http.routers.dashboard.rule=Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))
- traefik.http.routers.dashboard.service=api@internal
- traefik.http.routers.dashboard.entrypoints=websecure
- traefik.http.routers.dashboard.middlewares=lan-only@file,dash-auth@file
```

**Why this fix works:** a normal router on 443 with an allowlist and a password replaces the unauthenticated port. With no 8080 to publish, there is no recreate and no UFW bypass. Generate the password with `htpasswd -nB admin`, and in Compose labels double every `$` as `$$`.

**Prevent it:** never publish 8080 on internet-facing hosts. Treat every Traefik action in Dokploy's UI as a proxy restart: run it in a window, check `ss` for port conflicts first, and keep the recreate command in your runbook.

**Next step:** [29 §4.9 Dashboard, API, logs and access logs](29-learn-webservers-proxies.md#49-dashboard-api-logs-and-access-logs) · [26 §3 Docker: ports, host and firewall](26-playbook-containers-k8s.md#3-docker-ports-host-and-firewall) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Demo: Traefik Observability · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Traefik Dashboard 404 not found - Docker](https://community.traefik.io/t/traefik-dashboard-404-not-found-docker/6685) · [Dokploy #2996: Enable dashboard, traefik container gone, all domains down](https://github.com/Dokploy/dokploy/issues/2996) · [Dokploy #2722: Traefik disappearing after Enable Dashboard](https://github.com/Dokploy/dokploy/issues/2722) · [Dokploy discussion #696: accessing the dashboard after enabling it](https://github.com/Dokploy/dokploy/discussions/696) · [GitHub traefik issues by reactions (#5853)](https://github.com/traefik/traefik/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+dashboard+404+api%40internal) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=dashboard+404+api%40internal&restrict_sr=1)

### 7.5 Traefik v2 to v3 migration breaks routers

> **Seen as:** Traefik won't start with `swarmMode` on the docker provider; routers using ``HostRegexp(`{sub:[a-z]+}.example.com`)``, `Headers()` or regex in `PathPrefix` stop matching; `No domain found in rule HostRegexp` warnings; IngressRoutes in `traefik.containo.us` ignored · **Where:** old Compose files, templates and Helm values · **Level:** [L3 · Senior] · **How common:** v2.11 left security support on 7 Sept 2026 and 3.6 on 16 Aug 2026, so every remaining v2 or 3.6 install has to move; past-year forum threads on HostRegexp warnings

**Why it happens:** v3 changed several things at once:

- **Rule syntax.** `HostRegexp` and `PathRegexp` take Go regular expressions, and `PathPrefix` no longer accepts regex placeholders. `Headers` and `HeadersRegexp` became `Header` and `HeaderRegexp`, and one `Host()` takes one domain.
- **Swarm provider.** Swarm moved to its own `swarm` provider.
- **Renames and removals.** `ipWhiteList` became `ipAllowList`, content-type auto-detection is off by default (the `contentType` middleware turns it back on), and tracing is OpenTelemetry only.
- **CRD group.** Kubernetes CRDs moved from `traefik.containo.us` to `traefik.io`.
- **ACME and regex.** ACME can't derive domains from regex rules, so those routers need `tls.domains`.

**Diagnose:**

```bash
docker exec traefik traefik version | head -1
grep -RnE 'HostRegexp|Headers\(|swarmMode|ipWhiteList|containo\.us' /opt/stacks /opt/traefik 2>/dev/null | head -5
```

```
Version:      2.11.14
/opt/stacks/shop/compose.yaml:31:      - traefik.http.routers.shop.rule=HostRegexp(`{sub:[a-z]+}.shop.example.com`)
/opt/traefik/traefik.yml:12:    swarmMode: true
/opt/traefik/dynamic/mw.yml:4:    ipWhiteList:
```

**What the output tells you:** three v2-only constructs. Each one either blocks startup (`swarmMode`) or silently stops matching after the upgrade.

**Fix:**

```yaml
# Stage 1 (static): upgrade the binary but keep v2 rule syntax everywhere
core:
  defaultRuleSyntax: v2
providers:
  swarm:                                  # replaces docker.swarmMode
    endpoint: unix:///var/run/docker.sock
    exposedByDefault: false
```

```yaml
# Stage 2: migrate routers one by one; a per-router override lets v2 and v3 rules coexist
- traefik.http.routers.shop.rule=HostRegexp(`^[a-z]+\.shop\.example\.com$`)
- traefik.http.routers.shop.ruleSyntax=v3
- traefik.http.routers.shop.tls.domains[0].main=shop.example.com
- traefik.http.routers.shop.tls.domains[0].sans=*.shop.example.com
# Stage 3: rename ipWhiteList -> ipAllowList, update CRDs to traefik.io/v1alpha1, remove defaultRuleSyntax
```

**Why this fix works:** the staged path separates "new binary" from "new rules", so each step is small and you can roll it back. Comparing the router list before and after (3.1) proves nothing was lost.

**Prevent it:** follow Traefik's support table and upgrade inside each minor's support window. Keep proxy config in Git, and run the new version on staging against a copy of the real labels.

**Next step:** [29 §4.3 Routers: rules and priority](29-learn-webservers-proxies.md#43-routers-rules-and-priority) · [33 §3 Deployment strategies](33-learn-cicd-iac-sre.md#3-deployment-strategies) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik docs: v2 to v3 details](https://doc.traefik.io/traefik/migrate/v2-to-v3-details/) · [Traefik docs: release support table](https://doc.traefik.io/traefik/deprecation/releases/) · [Traefik forum: Constant "No domain found in rule HostRegexp" warnings](https://community.traefik.io/t/constant-no-domain-found-in-rule-hostregexp-warnings/29438) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+v3+migration+HostRegexp) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=v3+migration+HostRegexp&restrict_sr=1)

---

## 8. Traefik: TCP, auth, client IP and Kubernetes

### 8.1 SSH and databases through the proxy

> **Seen as:** ssh `kex_exchange_identification: Connection closed by remote host`; MySQL `Can't connect to MySQL server ... Connection refused`; TLS-passthrough clients receiving the proxy's certificate · **Where:** GitLab SSH, Kubernetes API, databases behind the same edge as the web apps · **Level:** [L3 · Senior] · **How common:** "Routing SSH traffic with Traefik v2" is the most-viewed topic on the Traefik forum (77k); HAProxy's "Mixing mode tcp and http" has 43.5k views

**Why it happens:** HTTP has a Host header and TLS has SNI. SSH, MySQL, Redis and Postgres before TLS have neither, so the proxy can only route them by **port**: one entryPoint per service and ``HostSNI(`*`)``. TLS passthrough needs `tls.passthrough=true`, or Traefik terminates TLS with its own certificate. Host port 22 already belongs to sshd, so GitLab's SSH needs another port. In HAProxy a frontend is either `mode tcp` or `mode http`. Mixing termination and passthrough on one port needs `mode tcp` with SNI inspection.

**Diagnose:**

```bash
nc -vz git.example.com 2222
ssh -v -p 2222 git@git.example.com 2>&1 | grep -E 'Connecting to|kex_exchange'
openssl s_client -connect 203.0.113.10:443 -servername k8s.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject
```

```
Connection to git.example.com (203.0.113.10) 2222 port [tcp/*] succeeded!
debug1: Connecting to git.example.com [203.0.113.10] port 2222.
kex_exchange_identification: Connection closed by remote host
subject=CN = TRAEFIK DEFAULT CERT
```

**What the output tells you:** the entryPoint on 2222 accepts the connection but no TCP router forwards it, so Traefik closes it. On 443, Traefik terminated TLS itself, so passthrough isn't configured for `k8s.example.com`.

**Fix:**

```yaml
# static: one entryPoint per raw-TCP service
entryPoints:
  ssh:
    address: ":2222"
```

```yaml
# labels on the GitLab container: SSH has no SNI, so match everything on this port
- traefik.tcp.routers.gitlab-ssh.rule=HostSNI(`*`)
- traefik.tcp.routers.gitlab-ssh.entrypoints=ssh
- traefik.tcp.routers.gitlab-ssh.service=gitlab-ssh
- traefik.tcp.services.gitlab-ssh.loadbalancer.server.port=22
```

```yaml
# dynamic/k8s-api.yml (file provider): TLS passthrough by name; the API server keeps its own certificate
tcp:
  routers:
    k8s-api: {rule: "HostSNI(`k8s.example.com`)", entryPoints: [websecure], service: k8s-api, tls: {passthrough: true}}
  services:
    k8s-api: {loadBalancer: {servers: [{address: "10.0.5.10:6443"}]}}
```

In `gitlab.rb`, set `gitlab_rails['gitlab_shell_ssh_port'] = 2222` so clone URLs show the right port. The HAProxy equivalent:

```
frontend fe_443
    bind :443
    mode tcp
    tcp-request inspect-delay 5s
    tcp-request content accept if { req_ssl_hello_type 1 }
    use_backend be_k8s if { req_ssl_sni -i k8s.example.com }
    default_backend be_https
```

**Why this fix works:** for raw TCP, the port is the only routing key, so each service gets its own. Passthrough keeps TLS end to end, so the client sees the real backend certificate.

**Prevent it:** don't expose databases on the public edge at all. Use WireGuard or an SSH tunnel. Record every raw-TCP port in the port inventory.

**Next step:** [29 §4.8 TCP routers, HostSNI and passthrough](29-learn-webservers-proxies.md#48-tcp-routers-hostsni-and-passthrough) · [21 Option C — Traefik passes TLS through](21-case-apache-443-dokploy.md#option-c-traefik-passes-tls-through-to-apache) · [47 CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure SSH Servers and Clients · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Routing SSH traffic with Traefik v2](https://community.traefik.io/t/routing-ssh-traffic-with-traefik-v2/717) · [Traefik forum: Can't connect to MySQL server](https://community.traefik.io/t/cant-connect-to-mysql-server-connection-refused/986) · [HAProxy forum: Mixing mode tcp and http](https://discourse.haproxy.org/t/mixing-mode-tcp-and-http-ssl-termination-and-passthrough/2698) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+tcp+router+HostSNI+ssh) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=tcp+router+ssh+HostSNI&restrict_sr=1)

### 8.2 Forward auth: loops, 404s and 504s

> **Seen as:** `ERR_TOO_MANY_REDIRECTS` between the app and the login portal; 404 on `/outpost.goauthentik.io/...`; 504 on protected routes; JSON access-log lines with `"OriginStatus":0` · **Where:** Traefik with Authentik, Authelia, OAuth2-Proxy or Keycloak · **Level:** [L3 · Senior] · **How common:** "Configurating Traefik with Authentik (gateway timeouts and 404s galore)" is the #2 Traefik forum topic of the past year; "Forwardauth + openid (keycloak)" has 19k views

**Why it happens:** forward auth has many moving parts, and each one fails differently:

- **Traefik can't reach the auth server.** It sits on a different network, or the Compose prefix strikes again (5.3).
- **The outpost path isn't routed.** Without a router for `/outpost.goauthentik.io/` above the app router, you get 404s or loops.
- **The middleware is on the portal itself.** Protecting the login portal with its own middleware is an instant loop.
- **Wrong endpoint.** Authelia uses `/api/authz/forward-auth`; older guides show `/api/verify`.
- **Missing headers.** Without `authResponseHeaders` the app never learns who the user is.
- **The auth container is down.** A crash-looping outpost, for example one missing `AUTHENTIK_TOKEN`, breaks every protected app.

**Diagnose:**

```bash
jq -c 'select(.RequestHost=="app.example.com") | {RouterName, OriginStatus, DownstreamStatus}' /opt/traefik/logs/access.log | tail -2
docker exec traefik wget -q -O /dev/null -T 5 http://authentik-server:9000/-/health/live/; echo "exit=$?"
curl -sI https://app.example.com/ | grep -iE '^(HTTP|location)'
```

```
{"RouterName":"app@docker","OriginStatus":0,"DownstreamStatus":504}
wget: download timed out
exit=1
HTTP/2 504
```

**What the output tells you:** the app router matched, but no backend ever answered. Traefik can't reach the auth server, so the forward-auth call times out before the app is even tried. Check the networks (5.3) before touching any auth settings.

**Fix:**

```yaml
# labels on the Authentik server (embedded outpost); Traefik and Authentik share the "proxy" network
- traefik.enable=true
- traefik.http.services.authentik.loadbalancer.server.port=9000
- traefik.http.middlewares.authentik.forwardauth.address=http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
- traefik.http.middlewares.authentik.forwardauth.trustForwardHeader=true
- traefik.http.middlewares.authentik.forwardauth.authResponseHeaders=X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
- traefik.docker.network=proxy
# on the protected app: the app router at priority 10, the outpost route above it at 15
- traefik.http.routers.app.rule=Host(`app.example.com`)
- traefik.http.routers.app.priority=10
- traefik.http.routers.app.middlewares=authentik@docker
- traefik.http.routers.app-outpost.rule=Host(`app.example.com`) && PathPrefix(`/outpost.goauthentik.io/`)
- traefik.http.routers.app-outpost.priority=15
- traefik.http.routers.app-outpost.service=authentik@docker
```

```yaml
# Authelia instead (file provider); Authelia listens on 9091
http:
  middlewares:
    authelia:
      forwardAuth:
        address: http://authelia:9091/api/authz/forward-auth
        trustForwardHeader: true
        authResponseHeaders: [Remote-User, Remote-Groups, Remote-Email, Remote-Name]
```

**Why this fix works:** the auth server is reachable on a shared network, and the outpost callback path wins over the app router, so it is never itself protected. The identity headers reach the app. Never put the middleware on the auth portal's own router.

**Prevent it:** protect `traefik/whoami` first, then real apps. Run the auth stack as its own monitored Compose project, and document bypasses such as health endpoints or a LAN `ipAllowList`.

**Next step:** [48 Security tools (Authentik, Authelia)](48-wazuh-and-security-tools.md) · [37 §9 Web and edge hardening](37-learn-security-devsecops.md#9-web-and-edge-hardening) · KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview · [authentik docs](https://docs.goauthentik.io/add-secure-apps/providers/proxy/server_traefik/)

**Community threads:** [Traefik forum: Configurating Traefik with Authentik](https://community.traefik.io/t/configurating-traefik-with-authentik-running-into-gateway-timeouts-and-404s-galore/29673) · [authentik docs: Traefik forward auth](https://docs.goauthentik.io/add-secure-apps/providers/proxy/server_traefik/) · [Authelia docs: Traefik integration](https://www.authelia.com/integration/proxies/traefik/) · [Caddy wiki: Caddy and Authelia in Docker Compose](https://caddy.community/t/securing-web-apps-with-caddy-and-authelia-in-docker-compose-an-opinionated-practical-and-minimal-production-ready-login-portal-guide/20465) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+forwardauth+authentik+redirect+loop) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=authentik+traefik+forward+auth+redirect+loop&restrict_sr=1)

### 8.3 Real client IP lost

> **Seen as:** every request in the logs comes from 10.0.0.2 (Swarm ingress) or 172.18.0.1 (a bridge gateway); `X-Forwarded-For` holds a proxy; IP allowlists, CrowdSec, fail2ban and Wazuh see one address · **Where:** Swarm ingress-mode ports, rootless Docker, Traefik behind a CDN or load balancer · **Level:** [L3 · Senior] · **How common:** forum threads "Real IP and Host Header" (28.7k) and "X-Forwarded-For and X-Real-Ip not correctly transmitted" (10.5k); HAProxy's "How to receive source IP address?" (26k)

**Why it happens:** each hop can replace the source address, and it passes the real one on only if it is told to and the next hop trusts it:

- **Swarm's ingress mesh** source-NATs published ports.
- **Rootless Docker or the userland proxy** rewrites the source address.
- **Behind a CDN or load balancer,** Traefik needs `forwardedHeaders.trustedIPs` or PROXY protocol on both ends. Traefik ignores X-Forwarded-* from untrusted senders by default.
- **The backend** (Apache, nginx, the app) must trust Traefik's X-Forwarded-For in turn.

Dokploy's standalone `dokploy-traefik` with `-p` ports usually keeps client IPv4 addresses. The losses start when Traefik runs as a Swarm service with ingress-mode ports, or when something sits in front.

**Diagnose:**

```bash
curl -s https://whoami.example.com/ | grep -E '^(RemoteAddr|X-Forwarded-For|X-Real-Ip)'
docker service inspect traefik --format '{{json .Endpoint.Ports}}' | jq -c '.[] | {PublishedPort, PublishMode}'
sudo tcpdump -ni any -c 3 'tcp dst port 443 and tcp[tcpflags] & tcp-syn != 0'
```

```
RemoteAddr: 10.0.1.9:52144
X-Forwarded-For: 10.0.0.2
X-Real-Ip: 10.0.0.2
{"PublishedPort":443,"PublishMode":"ingress"}
09:41:07.218455 eth0  In  IP 198.51.100.23.51234 > 203.0.113.10.443: Flags [S], seq 1802213456, win 64240, options [mss 1460,sackOK,TS val 3521877 ecr 0,nop,wscale 7], length 0
```

**What the output tells you:** the NIC sees the real client (198.51.100.23), but Traefik sees 10.0.0.2. That is Swarm's ingress SNAT, because the ports are published in ingress mode.

**Fix:**

```yaml
# Swarm: host-mode ports keep the client address (run one Traefik per edge node)
ports:
  - {target: 80, published: 80, protocol: tcp, mode: host}
  - {target: 443, published: 443, protocol: tcp, mode: host}
```

```yaml
# Behind a load balancer or CDN: trust ONLY its addresses
entryPoints:
  websecure:
    address: ":443"
    forwardedHeaders:
      trustedIPs: ["10.20.0.0/24"]       # the LB subnet, or the CDN's published ranges
    # if the LB sends PROXY protocol v2 (HAProxy send-proxy-v2, AWS NLB):
    # proxyProtocol:
    #   trustedIPs: ["10.20.0.0/24"]
```

```apache
# Apache behind Traefik (a2enmod remoteip), then log %a instead of %h
RemoteIPHeader X-Forwarded-For
RemoteIPTrustedProxy 172.16.0.0/12
```

For nginx backends, use `set_real_ip_from 172.16.0.0/12; real_ip_header X-Forwarded-For; real_ip_recursive on;`. For Caddy, see section 12. For HAProxy, use `option forwardfor` or `send-proxy-v2`.

**Why this fix works:** host-mode publishing skips the mesh NAT, and explicit trust lets exactly one known hop vouch for the client address. Never set `forwardedHeaders.insecure=true` on an internet-facing entryPoint. Anyone could then forge their IP and walk through allowlists and bans.

**Prevent it:** draw the hop chain and record who is trusted at each hop. Re-test with whoami after every topology change. CrowdSec and Wazuh are only as good as this.

**Next step:** [28 §5 NAT: SNAT, masquerade and DNAT](28-learn-networking.md#5-nat-snat-masquerade-and-dnat) · [48 Wazuh and CrowdSec](48-wazuh-and-security-tools.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm: Docker Overlay Network · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Traefik forum: Real IP and Host Header](https://community.traefik.io/t/real-ip-and-host-header/12336) · [Traefik docs: EntryPoints](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/) · [Nuvotex blog: Docker Swarm, preserve client IP](https://blog.nuvotex.de/docker-swarm-preserve-client-ip-on-incoming-connections/) · Search: [Server Fault](https://serverfault.com/search?q=real+client+ip+behind+reverse+proxy+docker+x-forwarded-for) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=real+client+ip+x-forwarded-for&restrict_sr=1)

### 8.4 Intermittent 502 on idle routes

> **Seen as:** Traefik 502 with `error="EOF"` or `read: connection reset by peer`; nginx `upstream prematurely closed connection while reading response header from upstream`; Apache `AH01102: error reading status line from remote server`; spikes in an ALB's `HTTPCode_ELB_502_Count` · **Where:** Node, Gunicorn or Puma backends behind Traefik, nginx, Apache or an ALB · **Level:** [L4 · Lead] · **How common:** AWS's ALB troubleshooting guide; gitlab-recipes #313; a classic Server Fault question that is rare, random and hard to reproduce

**Why it happens:** proxies keep idle connections to backends and reuse them. If the backend closes an idle connection at the moment the proxy sends a new request on it, that request fails. Traefik keeps idle backend connections for 90 s and an ALB for 60 s. Node closes idle keep-alive connections after 5 s and Gunicorn after 2 s. nginx 1.29.7 mainline (March 2026) turned on upstream keep-alive and HTTP/1.1 by default, so nginx users on new releases now meet this too. POSTs aren't retried, so users see the error.

**Diagnose:**

```bash
# 502s with no backend answer, on routes that were idle just before
jq -r 'select(.DownstreamStatus==502) | [.StartUTC, .RouterName, .OriginStatus] | @tsv' /opt/traefik/logs/access.log | tail -3
# FIN or RST from the backend right before a failure
sudo tcpdump -ni any -c 20 'tcp port 3000 and (tcp[tcpflags] & (tcp-fin|tcp-rst) != 0)'
```

```
2026-10-02T03:14:07.52Z	api@docker	0
2026-10-02T05:02:44.10Z	api@docker	0
2026-10-02T06:47:13.88Z	api@docker	0
```

**What the output tells you:** rare 502s at quiet hours, always with OriginStatus 0. The backend closed a pooled connection just as Traefik reused it. Under load the pool stays fresh, so it never happens at peak.

**Fix:**

```js
// Node behind Traefik or an ALB: the backend's idle timeout must be LONGER than the proxy's
server.keepAliveTimeout = 95000;   // > Traefik idleConnTimeout 90s and ALB idle timeout 60s
server.headersTimeout = 96000;
```

```yaml
# or make Traefik give up on idle connections first (file provider), and retry safe requests
http:
  serversTransports:
    short-idle:
      forwardingTimeouts:
        idleConnTimeout: 4s
  middlewares:
    retry-idempotent:
      retry:
        attempts: 2
# labels: traefik.http.services.api.loadbalancer.serverstransport=short-idle@file
```

Apache: `ProxyPass / http://127.0.0.1:3000/ disablereuse=On` (or `ttl=`). nginx: set the upstream `keepalive_timeout` lower than the backend's.

**Why this fix works:** the rule is that whoever opens a connection must give up on idle connections first. Then the backend never closes a connection the proxy is about to use. Add retries only on routes whose requests are safe to repeat.

**Prevent it:** keep a table with every hop's keep-alive and idle timeouts. Alert on the 502 rate, not just on availability, and re-check after any proxy upgrade that changes defaults.

**Next step:** [32 §8 Application performance](32-learn-performance-observability.md#8-application-performance) · [36 §6 Load balancing and Route 53](36-learn-cloud-aws.md#6-load-balancing-and-route-53) · KodeKloud: *Nginx For Beginners* — Performance: Monitoring & Troubleshooting · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [AWS docs: Troubleshoot Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) · [nginx CHANGES](https://nginx.org/en/CHANGES) · [gitlab-recipes #313: AH01102 error reading status line](https://github.com/gitlabhq/gitlab-recipes/issues/313) · Search: [Server Fault](https://serverfault.com/search?q=%22upstream+prematurely+closed+connection%22+keepalive) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=alb+502+keep-alive+timeout&restrict_sr=1)

### 8.5 Kubernetes ingress after ingress-nginx retired

> **Seen as:** after migrating, paths that used rewrite or regex annotations return 404; uploads hit 413 or time out under different defaults; HTTP is no longer redirected to HTTPS; Traefik Helm values silently ignored ("404 responses to everything on HTTP (web) including ACME challenges"); the k3s dashboard unreachable · **Where:** k3s and kubeadm clusters, CKA labs · **Level:** [L4 · Lead] · **How common:** Kubernetes announced the ingress-nginx retirement in Nov 2025 (no releases or security fixes after March 2026) and published "Before You Migrate" in Feb 2026; forum threads on middlewares with Kubernetes Ingress (43.5k) and Ingress vs IngressRoute (22.5k)

**Why it happens:**

- **Annotations don't carry over.** nginx-specific annotations (rewrite-target, use-regex, proxy-body-size, proxy-read-timeout, ssl-redirect, configuration-snippet) mean nothing to other controllers, and the default behaviours differ.
- **Helm values with wrong keys are silently ignored.** Your settings never reach the pod.
- **Mixed object types.** Ingress, IngressRoute and Gateway API objects get mixed for the same host.
- **Staying put isn't safe.** Staying on the retired controller leaves the cluster edge unpatched.

Traefik 3.7 offers an ingress-nginx compatibility provider (80+ annotations) as a bridge, and Ingress2Gateway 1.0 generates Gateway API resources.

**Diagnose:**

```bash
kubectl get ingress -A -o json | jq -r '.items[].metadata.annotations // {} | keys[]' | grep nginx.ingress | sort | uniq -c | sort -rn
kubectl -n kube-system get deploy traefik -o jsonpath='{.spec.template.spec.containers[0].args}' | tr ',' '\n' | grep -iE 'redirect|readTimeout'
kubectl get gatewayclass,gateway,httproute -A
```

```
     14 nginx.ingress.kubernetes.io/proxy-body-size
      9 nginx.ingress.kubernetes.io/rewrite-target
      6 nginx.ingress.kubernetes.io/ssl-redirect
      3 nginx.ingress.kubernetes.io/proxy-read-timeout
No resources found
```

**What the output tells you:** 32 annotations need a translation, and the redirect and timeout settings you thought you set are not in the rendered pod arguments. The Helm keys were wrong.

**Fix:**

| ingress-nginx annotation | Traefik equivalent | Gateway API equivalent |
|---|---|---|
| proxy-body-size | No limit by default; buffering middleware to cap it | Implementation-specific policy |
| proxy-read-timeout | entryPoint respondingTimeouts, serversTransport timeouts | HTTPRoute timeouts |
| rewrite-target | stripPrefix or replacePathRegex middleware | URLRewrite filter |
| ssl-redirect | entryPoint redirections or redirectScheme middleware | RequestRedirect filter |
| use-regex | PathRegexp rule | RegularExpression path match (implementation-specific) |
| configuration-snippet | No equivalent: redesign | None |

```yaml
# Traefik Helm values: additionalArguments are passed through as-is, then verify the rendered args
additionalArguments:
  - "--entryPoints.web.http.redirections.entryPoint.to=websecure"
  - "--entryPoints.web.http.redirections.entryPoint.scheme=https"
  - "--entryPoints.websecure.transport.respondingTimeouts.readTimeout=600s"
```

Migrate one host at a time with a canary (a second load-balancer IP or weighted DNS), and keep the old controller until its access logs are empty.

**Why this fix works:** an annotation inventory turns hidden behaviour into a checklist. Checking the rendered Deployment, not the values file, proves the settings arrived.

**Prevent it:** treat the ingress controller as a product with an owner and an upgrade calendar. Keep annotations few and documented, and test ingress behaviour in CI with curl assertions on status codes, redirects and headers.

**Next step:** [31 §8 Ingress and the Gateway API](31-learn-kubernetes.md#8-ingress-and-the-gateway-api) · [26 §9 Kubernetes: Services, Ingress and DNS](26-playbook-containers-k8s.md#9-kubernetes-services-ingress-and-dns) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: Ingress, Gateway API · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [Kubernetes blog: Ingress NGINX Retirement](https://www.kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/) · [Kubernetes blog: Before You Migrate](https://kubernetes.io/blog/2026/02/27/ingress-nginx-before-you-migrate/) · [Traefik forum: Traefik 3.7 release](https://community.traefik.io/t/traefik-3-7-release/29694) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ingress-nginx+migration+traefik+gateway+api) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=ingress-nginx+retirement+migration+traefik+gateway+api&restrict_sr=1)

---

## 9. Any proxy: HTTP behaviour

These five problems look the same whichever proxy you run, because they come from HTTP itself: which config is loaded, which vhost answers, which hop thinks the request is HTTPS, which path the app believes it lives at, and how long a connection may stay open.

### 9.1 A config change has no effect

> **Seen as:** the old behaviour stays; after a reload `nginx: [emerg] unknown directive ...` or `AH00526: Syntax error on line 14 of /etc/apache2/sites-enabled/app.conf` · **Where:** every proxy, every stage · **Level:** [L0 · Fresher] · **How common:** a classic Server Fault and Ask Ubuntu question; Dokploy's docs say every domain change on a Compose app or template needs a redeploy

**Why it happens:** each tool has its own apply step, and it is easy to skip:

- **Reload and enable.** nginx and Apache read files only on reload, and Debian/Ubuntu load only sites linked into `sites-enabled`.
- **Traefik's two kinds of config.** Static config is read only at start, and dynamic files only from a watched directory.
- **Dokploy labels.** Dokploy reads Compose labels only at deploy time.
- **Other traps.** A file edited inside a container is lost on recreate. A `*.bak` copy gets loaded by a wildcard include. Browsers cache 301 redirects and HSTS.

**Diagnose:**

```bash
sudo nginx -T 2>/dev/null | grep -E '^# configuration file|server_name'    # what nginx REALLY loaded
ls -l /etc/nginx/sites-enabled/
curl -sI https://app.example.com/ | head -3                                  # no browser cache involved
```

```
# configuration file /etc/nginx/nginx.conf:
# configuration file /etc/nginx/sites-enabled/default:
        server_name _;
lrwxrwxrwx 1 root root 34 Mar  4  2026 default -> /etc/nginx/sites-available/default
```

**What the output tells you:** your `app.conf` isn't in the loaded configuration at all. It exists only in `sites-available`, so nginx never saw your edit.

**Fix:**

```bash
sudo ln -s /etc/nginx/sites-available/app.conf /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx
sudo a2ensite app && sudo apachectl configtest && sudo systemctl reload apache2      # Apache
caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy          # Caddy
docker restart traefik      # Traefik STATIC changes only; dynamic files in the watched directory reload by themselves
# Dokploy Compose app or template: click Redeploy after changing domains or labels
```

**Why this fix works:** the site is now part of the loaded configuration, and testing before reloading protects the running sites. A failed `nginx -t` or `configtest` stops the reload, and the old config keeps serving. Use 302 instead of 301 while you test redirects, so browsers don't cache a mistake.

**Prevent it:** keep configs in Git, and apply them through an Ansible handler that runs the config test before reloading. Learn each tool's "show the effective config" command: `nginx -T`, `apachectl -S`, `caddy adapt`, and Traefik's `/api/rawdata`.

**Next step:** [25 §9 Config and change scenarios](25-playbook-site-down.md#9-config-and-change-scenarios) · [29 §3 Nginx in depth](29-learn-webservers-proxies.md#3-nginx-in-depth) · KodeKloud: *Nginx For Beginners* — Intermediate Config: Virtual Servers & Multiple Sites · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [Dokploy docs: redeploy after every domain change](https://docs.dokploy.com/docs/core/troubleshooting/domains) · Search: [Server Fault](https://serverfault.com/search?q=nginx+config+changes+not+taking+effect+sites-enabled) · [Stack Overflow](https://stackoverflow.com/search?q=nginx+changes+not+applied+sites-available+sites-enabled) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=nginx+sites-enabled+reload+not+applied&restrict_sr=1)

### 9.2 Wrong site or wrong certificate served

> **Seen as:** app2.example.com shows app1's page; curl `SSL: no alternative certificate subject name matches target host name`; `NET::ERR_CERT_COMMON_NAME_INVALID`; nginx `conflicting server name "example.com" on 0.0.0.0:80, ignored`; Apache `_default_ VirtualHost overlap on port 443, the first has precedence` · **Where:** nginx, Apache, Traefik, NPM · **Level:** [L2 · Mid] · **How common:** Traefik forum threads on picking custom certificates (21.6k) and "Invalid SSL certificate - even though I got a correct one" (18.5k); a classic for every vhost-based server

**Why it happens:** every name-based server first narrows candidates by IP and port, then matches the Host header (HTTP) or SNI (TLS). If nothing matches, a **default** answers with its own content and certificate:

- **Apache:** the first vhost listed for that IP:port, and `000-default` sorts first.
- **nginx:** the `default_server`, or the first server block.
- **Traefik:** its default certificate.

The usual triggers are a new DNS name nobody added to a vhost, access by IP, a missing ServerAlias, duplicate names in old files, and a Traefik router without a certificate resolver.

**Diagnose:**

```bash
sudo apachectl -S 2>/dev/null | head -6
openssl s_client -connect 203.0.113.10:443 -servername app2.example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName
```

```
VirtualHost configuration:
*:444                  is a NameVirtualHost
         default server app1.example.com (/etc/apache2/sites-enabled/000-app1-ssl.conf:2)
         port 444 namevhost app1.example.com (/etc/apache2/sites-enabled/000-app1-ssl.conf:2)
         port 444 namevhost app3.example.com (/etc/apache2/sites-enabled/app3-ssl.conf:2)
subject=CN = app1.example.com
```

**What the output tells you:** no vhost on *:444 claims app2.example.com, so the default (app1) answers with app1's certificate. The fix is a vhost for app2, plus a default that never serves a real site.

**Fix:**

```nginx
# nginx: a deliberate catch-all that serves nothing (ssl_reject_handshake needs nginx 1.19.4+)
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;
    ssl_reject_handshake on;
}
server {
    listen 80 default_server;
    server_name _;
    return 444;
}
```

In Apache, give every site a `ServerName` and `ServerAlias`, and make the first vhost per IP:port a deliberate catch-all. In Traefik, set `tls.certresolver` (or `tls.domains`) on every router, and define a default certificate in the TLS store if clients hit unknown names.

**Why this fix works:** unknown names now get a refusal instead of somebody else's site and certificate, and every real name has an explicit match. Remove duplicates and `*.bak` files from `sites-enabled`, and include only `*.conf`.

**Prevent it:** keep one file per site with a naming convention, and run an automated check that every DNS name returns a matching certificate (blackbox exporter, 3.7).

**Next step:** [22 §5 Reverse proxies: which vhost is which app](22-playbook-ports-inventory.md#5-reverse-proxies-which-vhost-is-which-app) · [21 One IP, many sites: SNI and the Host header](21-case-apache-443-dokploy.md#one-ip-many-sites-sni-and-the-host-header) · KodeKloud: *DevOps Pre-Requisite Course* — Web Server: Apache Web Server · [Apache docs](https://httpd.apache.org/)

**Community threads:** [Apache docs: virtual host matching in depth](https://httpd.apache.org/docs/2.4/vhosts/details.html) · [Traefik forum: Invalid SSL certificate - even though I got a correct one](https://community.traefik.io/t/invalid-ssl-certificate-even-though-i-got-a-correct-one/12190) · [NGINX wiki mirror: pitfalls and common mistakes](https://nginx-wiki.getpagespeed.com/config/pitfalls/) · Search: [Server Fault](https://serverfault.com/search?q=%22VirtualHost+overlap+on+port+443%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=reverse+proxy+wrong+certificate+wrong+site&restrict_sr=1)

### 9.3 Redirect loops and 422 CSRF errors

> **Seen as:** `ERR_TOO_MANY_REDIRECTS`; curl shows 301 to the same https URL again and again; GitLab `422 The change you requested was rejected.` with `Can't verify CSRF token authenticity` · **Where:** Cloudflare or an ALB in front of Traefik, nginx, Apache or NPM, with GitLab, WordPress, Django or Nextcloud behind · **Level:** [L2 · Mid] · **How common:** Cloudflare has an official troubleshooting page for it; Traefik forum redirect threads with 37.4k, 31.7k and 21k views; GitLab's NGINX docs have a section on the 422 case

**Why it happens:** when TLS terminates at a CDN or proxy, the next hop receives plain HTTP. If that hop, or the app, forces HTTPS without trusting `X-Forwarded-Proto`, it redirects forever. Some apps reject the login as a CSRF failure instead. The usual causes:

- **Cloudflare's Flexible SSL mode.** Cloudflare talks HTTP to the origin, and the origin redirects back to HTTPS.
- **The app doesn't trust the forwarded scheme.**
- **Two layers both redirect,** for example NPM's Force SSL and the app's own redirect.
- **GitLab's bundled nginx still serves HTTPS** behind a proxy that already terminates TLS.

**Diagnose:**

```bash
curl -sIL --max-redirs 4 https://app.example.com/ | grep -iE '^(HTTP|location|server)'
curl -sI -H 'Host: app.example.com' http://203.0.113.10/ | grep -iE '^(HTTP|location)'     # origin without the CDN
```

```
HTTP/2 301
location: https://app.example.com/
server: cloudflare
HTTP/2 301
location: https://app.example.com/
server: cloudflare
HTTP/1.1 301 Moved Permanently
Location: https://app.example.com/
```

**What the output tells you:** the origin redirects plain HTTP to HTTPS, and Cloudflare keeps sending it plain HTTP. That is the Flexible-mode loop. Switch Cloudflare to Full (strict), with a valid origin certificate.

**Fix:**

```nginx
# nginx in front of an app: pass the original scheme and host
proxy_set_header Host              $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
```

```ruby
# /etc/gitlab/gitlab.rb - GitLab Omnibus behind Traefik (Traefik terminates TLS)
external_url 'https://gitlab.example.com'
nginx['listen_port'] = 80
nginx['listen_https'] = false
letsencrypt['enable'] = false
nginx['proxy_set_headers'] = { 'X-Forwarded-Proto' => 'https', 'X-Forwarded-Ssl' => 'on' }
nginx['real_ip_trusted_addresses'] = ['172.16.0.0/12']
nginx['real_ip_header'] = 'X-Forwarded-For'
gitlab_rails['gitlab_shell_ssh_port'] = 2222      # SSH via a Traefik TCP entryPoint (8.1)
# then: sudo gitlab-ctl reconfigure
```

Django uses `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` and Laravel uses TrustProxies. In Apache, set `ProxyPreserveHost On` and `RequestHeader set X-Forwarded-Proto "https"`. Redirect in exactly one place, the edge (2.2).

**Why this fix works:** every hop now agrees that the original request was HTTPS, so nobody "upgrades" it again. GitLab's bundled nginx stops fighting Traefik for TLS and for Let's Encrypt on port 80.

**Prevent it:** let exactly one hop own redirects, write down the scheme at each hop, and test with `curl -IL` after every proxy or CDN change. For GitLab, after any proxy change, check three things: web login, `git push` over SSH, and `docker push` to the registry.

**Next step:** [25 §8 HTTP behaviour scenarios](25-playbook-site-down.md#8-http-behaviour-scenarios) · [47 CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Nginx For Beginners* — Intermediate Config: Reverse Proxy · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [Cloudflare docs: ERR_TOO_MANY_REDIRECTS](https://developers.cloudflare.com/ssl/troubleshooting/too-many-redirects/) · [Traefik forum: Global http to https redirect in v2](https://community.traefik.io/t/global-http-to-https-redirect-in-v2/1658) · [GitLab docs: NGINX settings](https://docs.gitlab.com/omnibus/settings/nginx/) · [GitLab forum: GitLab behind an Apache reverse proxy with SSL](https://forum.gitlab.com/t/gitlab-behind-a-apache-revers-proxy-with-ssl/17062) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ERR_TOO_MANY_REDIRECTS+reverse+proxy+X-Forwarded-Proto) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=gitlab+behind+traefik+reverse+proxy+422&restrict_sr=1)

### 9.4 The subfolder problem

> **Seen as:** a blank or unstyled page; assets requested as `/static/...` (404) instead of `/app/static/...`; `Location: /login` drops the prefix; redirect loops · **Where:** an app published at example.com/app with Caddy, nginx, Traefik or NPM · **Level:** [L2 · Mid] · **How common:** Caddy's wiki post "The subfolder problem" (50k views); NPM issue #104 "How do i forward to a folder?" (117 comments); a classic Stack Overflow question about `proxy_pass` trailing slashes

**Why it happens:** the proxy can strip `/app` on the way in, but it can't rewrite every link, redirect and API call the app generates on the way out. The app thinks it lives at `/`, so it emits `/static/...` and `/login`. In nginx, `proxy_pass` with a URI part (such as a trailing slash) replaces the matched prefix, and without one it passes the URI unchanged. Traefik's `stripPrefix` and Caddy's `handle_path` strip the prefix, but they can't teach the app its base path.

**Diagnose:**

```bash
curl -s https://example.com/app/ | grep -oE '(src|href)="[^"]+"' | head -3
curl -sI https://example.com/app/login | grep -i '^location'
```

```
href="/static/css/main.3f2a.css"
src="/static/js/main.9c1d.js"
location: /login
```

**What the output tells you:** the app generates root-relative URLs. The browser then asks for `/static/...` and `/login` outside `/app`, where another site, or nothing, answers.

**Fix:**

```nginx
# Best: give the app its own name (app.example.com); wildcard DNS and ACME make that cheap.
# If the app supports a base path, configure it AND keep the prefix when proxying:
location /grafana/ { proxy_pass http://grafana:3000; }      # no URI part: /grafana/... passed unchanged
# (grafana.ini: root_url = https://example.com/grafana/ and serve_from_sub_path = true)
# For an app that really expects "/", strip the prefix (a trailing URI part replaces it):
location /app/ { proxy_pass http://backend:3000/; }
```

**Why this fix works:** a subdomain removes the problem entirely. With a configured base path, the app itself generates `/grafana/...` links, so nothing needs rewriting. Stripping only works for apps that never emit absolute paths.

**Prevent it:** default to one subdomain per app, and use sub-paths only for apps that document base-path support (Grafana `root_url`, GitLab relative URL, a `BASE_URL` setting).

**Next step:** [29 §3 Nginx in depth](29-learn-webservers-proxies.md#3-nginx-in-depth) · KodeKloud: *Nginx For Beginners* — Intermediate Config: Reverse Proxy · [nginx proxy module docs](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

**Community threads:** [Caddy wiki: The subfolder problem](https://caddy.community/t/the-subfolder-problem-or-why-cant-i-reverse-proxy-my-app-into-a-subfolder/8575) · [nginx docs: proxy_pass with and without a URI](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=nginx+proxy_pass+trailing+slash+location+subfolder) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=reverse+proxy+subfolder+subpath&restrict_sr=1)

### 9.5 WebSockets fail or drop at 60 seconds

> **Seen as:** browser console `WebSocket connection to 'wss://app.example.com/socket' failed`; 400 Bad Request from the backend; the app falls back to long-polling; Apache `AH01144: No protocol handler was valid for the URL /ws/ (scheme 'ws')`; disconnects at exactly 60 s · **Where:** nginx, Apache, HAProxy and NPM (Traefik and Caddy handle the upgrade automatically) · **Level:** [L2 · Mid] · **How common:** Caddy forum "Caddy V2 how to proxy websocket" (51k views); NPM #5503; the Proxmox noVNC console behind any proxy

**Why it happens:** a WebSocket starts as an HTTP/1.1 Upgrade request and then stays open for a long time. `Upgrade` and `Connection` are hop-by-hop headers, so nginx and Apache don't forward them unless told to. Before 1.29.7, nginx also spoke HTTP/1.0 to upstreams by default, and Ubuntu 22.04 and 24.04 ship 1.18 and 1.24. After the upgrade, idle timeouts kill quiet sockets: nginx `proxy_read_timeout` 60 s, HAProxy without `timeout tunnel`, ALB idle 60 s.

**Diagnose:**

```bash
curl -s -i -N --http1.1 -m 5 -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==' https://app.example.com/socket | head -2
```

```
HTTP/1.1 400 Bad Request
Server: nginx/1.24.0 (Ubuntu)
```

**What the output tells you:** the handshake never reached the app as an upgrade. A working path answers `101 Switching Protocols`. A 400 relayed through nginx (the backend refusing a plain GET) means the Upgrade headers were dropped on the way.

**Fix:**

```nginx
# http context
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
# server context
location /socket {
    proxy_pass http://app:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_read_timeout 1h;
}
```

In Apache 2.4.47+, use `ProxyPass /ws/ http://backend:3000/ws/ upgrade=websocket`. Older versions need `a2enmod proxy_wstunnel` and a `ws://` target. In HAProxy, add `timeout tunnel 1h`. In NPM, enable **Websockets Support** on the proxy host. In the app, send a ping every 20–30 s so no idle timer fires.

**Why this fix works:** the upgrade headers now reach the backend, and the long read timeout applies only to the socket path, not the whole site.

**Prevent it:** add a WebSocket check to the smoke tests, and set tunnel and idle timeouts deliberately at every hop.

**Next step:** [25 §8 HTTP behaviour scenarios](25-playbook-site-down.md#8-http-behaviour-scenarios) · [29 §1 Reverse proxy fundamentals](29-learn-webservers-proxies.md#1-reverse-proxy-fundamentals) · KodeKloud: *Nginx For Beginners* — Intermediate Config: Reverse Proxy · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [F5/NGINX blog: NGINX as a WebSocket Proxy](https://www.f5.com/company/blog/nginx/websocket-nginx) · [Apache docs: mod_proxy_wstunnel](https://httpd.apache.org/docs/2.4/mod/mod_proxy_wstunnel.html) · [NPM #5503: WebSocket over HTTP/2 gets 400](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/5503) · Search: [Stack Overflow](https://stackoverflow.com/search?q=nginx+websocket+proxy+upgrade+400) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=websocket+reverse+proxy+400+nginx&restrict_sr=1)

---

## 10. Nginx

### 10.1 nginx 502 and 504: read the error.log line

> **Seen as:** `502 Bad Gateway` or `504 Gateway Time-out` from nginx or NPM; `nginx: [emerg] host not found in upstream "app:8080"` when an nginx container starts · **Where:** nginx on Ubuntu, NPM, nginx containers in Compose · **Level:** [L1 · Junior] (the Docker DNS variant is L3) · **How common:** among the most-asked nginx questions on Stack Overflow and Server Fault; "requests die after 30 or 60 seconds" is in your ops-ladder case library

**Why it happens:** nginx always writes **why** it returned 502 or 504. Beginners read the browser instead of `/var/log/nginx/error.log`, or NPM's per-host logs. Each wording points to a different cause:

| error.log says | Usually means | First fix |
|---|---|---|
| connect() failed (111: Connection refused) | Backend down, wrong port, or `localhost` used inside a container | Start it; point proxy_pass at a reachable address |
| upstream timed out (110) while reading response header | Slow endpoint beyond proxy_read_timeout (60 s default) | Fix the endpoint; longer timeout for that location only |
| upstream timed out (110) while connecting | Network or firewall, not a slow app | Routes, firewall, is the backend listening? |
| upstream sent too big header | Large SSO cookies or JWTs | Bigger proxy_buffer_size |
| upstream prematurely closed connection | Backend crashed, was OOM-killed, hit a worker timeout, or the keep-alive race | Backend logs, then 8.4 |
| no live upstreams | Every server marked failed by max_fails | Fix the backends first |
| host not found in upstream (at start) | A Docker name that doesn't resolve yet; nginx resolves names once, at start | Runtime resolver (below) |
| (113: No route to host) to an old IP | Container recreated with a new IP, nginx kept the old one | Runtime resolver (below) |

**Diagnose:**

```bash
sudo tail -n 2 /var/log/nginx/error.log
docker exec npm tail -n 2 /data/logs/proxy-host-3_error.log      # NPM keeps one error log per proxy host
```

```
2026/10/02 12:20:41 [error] 2211#2211: *9602 upstream timed out (110: Connection timed out) while reading response header from upstream, client: 198.51.100.23, server: app.example.com, request: "GET /reports/export HTTP/1.1", upstream: "http://10.0.2.15:8000/reports/export", host: "app.example.com"
2026/10/02 12:31:07 [error] 2211#2211: *9640 connect() failed (111: Connection refused) while connecting to upstream, client: 198.51.100.23, server: app.example.com, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:8080/", host: "app.example.com"
```

**What the output tells you:** two different problems. One slow endpoint (`/reports/export`) exceeds the 60 s read timeout and gives a 504. Separately, `proxy_pass` points at 127.0.0.1:8080, where nothing listens: inside an nginx container 127.0.0.1 is that container itself, not the app container. The refused connection gives a 502.

**Fix:**

```nginx
# 1. a backend address nginx can reach: a service name on the shared Docker network, never localhost in a container
proxy_pass http://app:8080;
# 2. a longer timeout for the one slow endpoint, not for the whole site
location /reports/export { proxy_pass http://app:8080; proxy_read_timeout 300s; proxy_send_timeout 300s; }
# 3. SSO-heavy apps (Authentik, Keycloak, OIDC): bigger header buffers
proxy_buffer_size 16k; proxy_buffers 8 16k; proxy_busy_buffers_size 32k;
# 4. nginx in Docker: resolve names per request via Docker's DNS (with a variable, the URI is passed unchanged)
resolver 127.0.0.11 valid=10s ipv6=off;
location / { set $upstream http://app:8080; proxy_pass $upstream; }
```

On nginx 1.27.3 or newer, the cleaner form for Docker names is an upstream with `zone`, `resolver 127.0.0.11` and `server app:8080 resolve;`. Raise the app server's own limit too (`gunicorn --timeout 300`) and every hop in front, such as the ALB idle timeout. Then `sudo nginx -t && sudo systemctl reload nginx`.

**Why this fix works:** each change answers one log wording. Scoped timeouts keep slow-request protection everywhere else, and runtime DNS follows containers as they move. Never raise timeouts globally to hide one slow endpoint. Move long work to a background job when you can.

**Prevent it:** log the upstream timings, so the next 502 or 504 names its backend and phase.

```nginx
log_format upstreamlog '$remote_addr [$time_local] "$request" $status rt=$request_time '
                       'ua=$upstream_addr us=$upstream_status uct=$upstream_connect_time urt=$upstream_response_time';
```

**Next step:** [25 §7 Proxy error scenarios](25-playbook-site-down.md#7-proxy-error-scenarios-502-503-504) · [26 §4 Docker: DNS and container networking](26-playbook-containers-k8s.md#4-docker-dns-and-container-networking) · KodeKloud: *Nginx For Beginners* — Performance: Monitoring & Troubleshooting · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [nginx docs: proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) · [nginx CHANGES (1.27.3 upstream resolve)](https://nginx.org/en/CHANGES) · [F5/NGINX blog: Avoiding the Top 10 NGINX Configuration Mistakes](https://www.f5.com/company/blog/nginx/avoiding-top-10-nginx-configuration-mistakes) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22upstream+timed+out%22+%22while+reading+response+header+from+upstream%22) · [Server Fault](https://serverfault.com/search?q=%22upstream+sent+too+big+header%22) · [Stack Overflow: host not found in upstream](https://stackoverflow.com/search?q=nginx+%22host+not+found+in+upstream%22+docker)

### 10.2 413 Request Entity Too Large

> **Seen as:** `413 Request Entity Too Large`; error.log `client intended to send too large body: 5242880 bytes`; docker `error parsing HTTP 413 response body: invalid character '<' looking for beginning of value` · **Where:** nginx, NPM, Harbor's internal nginx, GitLab's bundled nginx, ingress-nginx · **Level:** [L1 · Junior] · **How common:** Harbor issue #22353; a classic Stack Overflow and Server Fault question; one of ingress-nginx's most-used annotations

**Why it happens:** nginx limits request bodies to 1 MB by default (`client_max_body_size 1m`). Every nginx in the chain applies its own limit, and so do PHP (`upload_max_filesize`, `post_max_size`), CDN plans and a Traefik `buffering` middleware with `maxRequestBodyBytes`. Traefik and Caddy have no body limit unless you set one.

**Diagnose:**

```bash
sudo grep 'too large body' /var/log/nginx/error.log | tail -1
sudo nginx -T 2>/dev/null | grep -n client_max_body_size
curl -sI https://app.example.com/ | grep -i '^server'      # which hop answers? check every hop's log
```

```
2026/10/02 11:02:13 [error] 2211#2211: *9120 client intended to send too large body: 5242880 bytes, client: 198.51.100.23, server: app.example.com, request: "POST /upload HTTP/1.1", host: "app.example.com"
server: nginx
```

**What the output tells you:** nginx itself refused the 5 MB body. `nginx -T` printed nothing for `client_max_body_size`, so the 1 MB default applies.

**Fix:**

```nginx
# per site or location; 0 disables the check (common for registries)
client_max_body_size 1g;
# big uploads and registries behind nginx: stream instead of buffering to disk
proxy_request_buffering off;
```

In NPM, open the proxy host's Advanced tab and add `client_max_body_size 0;`. On ingress-nginx (until migrated, 8.5), use the annotation `nginx.ingress.kubernetes.io/proxy-body-size: "0"`. Then `sudo nginx -t && sudo systemctl reload nginx`.

**Why this fix works:** the limit now matches the largest legitimate upload. Find the hop that answers 413 before you change anything, because raising the limit on the wrong hop changes nothing.

**Prevent it:** document the maximum upload size per app, set it at every hop, and keep a large-file upload and a multi-GB `docker push` in the smoke tests (15.1).

**Next step:** [15.1 docker push and big uploads](#151-docker-push-and-big-uploads-fail-through-the-proxy) · KodeKloud: *Nginx For Beginners* — Intermediate Config: Reverse Proxy · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [Harbor #22353: 413 when pushing an image](https://github.com/goharbor/harbor/issues/22353) · [nginx docs: proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22413+Request+Entity+Too+Large%22+nginx+client_max_body_size) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=%22413+Request+Entity+Too+Large%22&restrict_sr=1)

### 10.3 Capacity limits under load

> **Seen as:** nginx `worker_connections are not enough`, `accept4() failed (24: Too many open files)`, `connect() to 10.0.0.5:8080 failed (99: Cannot assign requested address) while connecting to upstream`; HAProxy sessions queued (`sQ--`) and then 503; Traefik `too many open files` · **Where:** busy nginx, HAProxy or Traefik edges · **Level:** [L4 · Lead] · **How common:** F5's "Top 10 NGINX Configuration Mistakes" puts file descriptors and upstream keep-alive near the top, and the post got its own Hacker News discussion; HAProxy forum threads on maxconn (11k) and nbthread (12.5k)

**Why it happens:** each proxied request uses at least two sockets. The common limits:

- **File-descriptor limits** from systemd (soft 1024 by default) or Docker are far below what `worker_connections` assumes.
- **No upstream keep-alive,** the default before nginx 1.29.7 (and still the default in Ubuntu's 1.18 and 1.24 packages). Every request opens a new TCP connection to the same backend IP and port, uses one of about 28k ephemeral ports, and leaves it in TIME_WAIT.
- **HAProxy `maxconn`** below the real concurrency queues requests until they time out.

**Diagnose:**

```bash
grep 'open files' /proc/$(pgrep -o nginx)/limits
ss -s | head -2
sysctl net.ipv4.ip_local_port_range
```

```
Max open files            1024                 524288               files
Total: 40211
TCP:   39874 (estab 512, closed 38990, orphaned 3, timewait 38977)
net.ipv4.ip_local_port_range = 32768	60999
```

**What the output tells you:** a 1024 soft FD limit, and 39k TIME_WAIT sockets against about 28k ephemeral ports. nginx opens a fresh upstream connection per request, so it runs out of ports (error 99) long before it runs out of CPU.

**Fix:**

```nginx
worker_rlimit_nofile 65535;
events { worker_connections 16384; }
upstream app {
    server 10.0.0.5:8080;
    keepalive 64;                       # on by default (32) since nginx 1.29.7; required on Ubuntu's 1.18/1.24
}
server {
    location / {
        proxy_pass http://app;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

```bash
sudo systemctl edit nginx              # [Service]  LimitNOFILE=65535
sudo systemctl restart nginx
# Docker: ulimits: {nofile: {soft: 65535, hard: 65535}}. HAProxy: set global and per-server maxconn deliberately.
```

**Why this fix works:** pooled upstream connections remove the per-request handshake and the TIME_WAIT pile-up, and the FD limit now matches the configured connections. Widening `ip_local_port_range` is a stopgap, not a fix.

**Prevent it:** load-test with k6 or wrk before launches. Graph connections, FDs and TIME_WAIT, and alert on "Too many open files". Keep capacity notes per proxy in the runbook.

**Next step:** [32 §9 Benchmarking and load testing safely](32-learn-performance-observability.md#9-benchmarking-and-load-testing-safely) · [23 Why is it slow?](23-playbook-slow-system.md) · KodeKloud: *Nginx For Beginners* — Performance: Monitoring & Troubleshooting · [nginx docs](https://nginx.org/en/docs/)

**Community threads:** [F5/NGINX blog: Avoiding the Top 10 NGINX Configuration Mistakes](https://www.f5.com/company/blog/nginx/avoiding-top-10-nginx-configuration-mistakes) · [Hacker News discussion of that post](https://news.ycombinator.com/item?id=30435282) · [HAProxy forum: Is HAProxy 2.0 default maxconn still enforced?](https://discourse.haproxy.org/t/is-haproxy-2-0-default-maxconn-still-enforced/4418) · Search: [Server Fault](https://serverfault.com/search?q=%22Cannot+assign+requested+address%22+%22while+connecting+to+upstream%22) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=nginx+too+many+open+files+worker_connections&restrict_sr=1)

---

## 11. Apache httpd

### 11.1 Apache won't start after proxy changes

> **Seen as:** `(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443` plus `no listening sockets available, shutting down`; `Invalid command 'ProxyPass', perhaps misspelled or defined by a module not included in the server configuration`; `AH01144: No protocol handler was valid for the URL /`; the noisy `AH00558: Could not reliably determine the server's fully qualified domain name` · **Where:** Ubuntu's apache2 after moving it behind Traefik · **Level:** [L1 · Junior] · **How common:** classic Ask Ubuntu and Server Fault questions; your own Apache/443 incident

**Why it happens:** on Ubuntu, Apache's proxy features live in modules that are off by default (proxy, proxy_http, headers, ssl, remoteip, proxy_wstunnel). `Listen` lines belong in `ports.conf`. A duplicate `Listen` in a site file, or a port Traefik now owns, stops startup. AH00558 is only a warning, but it sits right above the real error, so people chase it instead.

**Diagnose:**

```bash
sudo apachectl configtest
sudo apachectl -M 2>/dev/null | grep -E 'proxy|headers|remoteip'
sudo grep -rn '^Listen' /etc/apache2/
```

```
AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message
AH00526: Syntax error on line 6 of /etc/apache2/sites-enabled/old-site.conf:
Invalid command 'ProxyPass', perhaps misspelled or defined by a module not included in the server configuration
Action 'configtest' failed.
/etc/apache2/ports.conf:5:Listen 81
/etc/apache2/sites-available/old-site.conf:1:Listen 81
```

**What the output tells you:** ignore AH00558. The real error is that mod_proxy isn't loaded (the `-M` grep printed nothing). Fix that and the duplicate `Listen 81` is the next failure waiting.

**Fix:**

```bash
sudo a2enmod proxy proxy_http headers ssl remoteip
echo 'ServerName localhost' | sudo tee /etc/apache2/conf-available/servername.conf && sudo a2enconf servername
# edit the real file in sites-available: sed -i on the sites-enabled symlink would replace the link with a copy
sudo sed -i '/^Listen 81$/d' /etc/apache2/sites-available/old-site.conf
sudo apachectl configtest && sudo systemctl restart apache2
```

```apache
# a proxied site behind Traefik
<VirtualHost *:81>
    ServerName old.example.com
    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    ProxyPass        / http://127.0.0.1:8085/
    ProxyPassReverse / http://127.0.0.1:8085/
</VirtualHost>
```

**Why this fix works:** the modules provide the directives, each port is opened once, and silencing AH00558 makes the real errors stand out. Keep trailing slashes consistent between `ProxyPass` and `ProxyPassReverse`.

**Prevent it:** run `apachectl configtest` before every reload, in scripts and Ansible handlers. Keep vhosts in Git, with a note of the modules each site needs.

**Next step:** [21 §6 Dispatch Apache off 80 and 443](21-case-apache-443-dokploy.md#6-phase-5-dispatch-apache-off-80-and-443) · [29 §2 Apache httpd in depth](29-learn-webservers-proxies.md#2-apache-httpd-in-depth) · KodeKloud: *DevOps Pre-Requisite Course* — Web Server: Apache Web Server · [Apache docs](https://httpd.apache.org/)

**Community threads:** [Apache docs: Binding to Addresses and Ports](https://httpd.apache.org/docs/2.4/bind.html) · Search: [Server Fault: Invalid command ProxyPass](https://serverfault.com/search?q=%22Invalid+command%22+ProxyPass+%22perhaps+misspelled%22) · [Stack Overflow: AH00558](https://stackoverflow.com/search?q=AH00558+ServerName+globally) · [Server Fault: AH00072](https://serverfault.com/search?q=AH00072+make_sock+could+not+bind+to+address) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=apache+ProxyPass+invalid+command&restrict_sr=1)

---

## 12. Caddy

Caddy is the simplest of these proxies to start with, and its problems cluster in a few places. Know these before you run it:

- **Certificates live in the data directory** (`/data` in Docker). Lose it, and Caddy orders everything again.
- **Behind a CDN or load balancer,** Caddy sets X-Forwarded-For, -Proto and -Host itself, and ignores incoming values unless the sender is listed in `trusted_proxies`.
- **HTTPS upstreams.** Since v2.11.0 Caddy rewrites the Host header for them automatically. Older versions need `header_up Host {upstream_hostport}`.
- **New limits in 2.11.6.** It added a 16 KiB default request-header limit and new idle timeouts, so watch large SSO cookies and very slow clients.
- **No DNS providers in the standard binary.** Wildcards need a custom build (6.2).
- **Check before reload** with `caddy fmt`, `caddy validate` and `caddy adapt` (the JSON Caddy really runs).

```
# Caddyfile: trust the load balancer, and verify a private-CA upstream instead of skipping verification
{
    servers {
        trusted_proxies static 10.20.0.0/24
    }
}
app.example.com {
    reverse_proxy https://10.0.0.5:8443 {
        transport http {
            tls_server_name app.internal
            tls_trust_pool file /etc/caddy/private-ca.crt
        }
    }
}
```

Read more: [Caddy docs: reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) · [Caddy wiki: local HTTPS between a front proxy and LAN hosts](https://caddy.community/t/use-caddy-for-local-https-tls-between-front-end-reverse-proxy-and-lan-hosts/11650) · Search: [Reddit r/selfhosted: caddy trusted_proxies](https://www.reddit.com/r/selfhosted/search/?q=caddy+trusted_proxies+real+ip&restrict_sr=1).

### 12.1 Caddy can't get a certificate

> **Seen as:** `could not get certificate from issuer` with `HTTP 400 urn:ietf:params:acme:error:connection ... Timeout during connect (likely firewall problem)` or `HTTP 429 urn:ietf:params:acme:error:rateLimited - too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s` · **Where:** Caddy in Docker or under systemd · **Level:** [L2 · Mid] · **How common:** Caddy forum "How to force renewal of Let's Encrypt certificates" (28.6k views, 44 replies) and the Caddy FAQ (24k)

**Why it happens:** Caddy's automatic HTTPS needs what every ACME client needs: public DNS for the name, and ports 80 and 443 reachable (6.1). It stores certificates and the ACME account in its data directory. In Docker, a missing `/data` volume means every recreate orders certificates again, until Let's Encrypt's limit of 5 per week for the same names kicks in. Internal-only names need DNS-01 or `tls internal`.

**Diagnose:**

```bash
docker logs caddy 2>&1 | grep '"logger":"tls' | tail -1
docker inspect caddy -f '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

```
{"level":"error","ts":1790930000.12,"logger":"tls.obtain","msg":"could not get certificate from issuer","identifier":"app.example.com","issuer":"acme-v02.api.letsencrypt.org-directory","error":"HTTP 429 urn:ietf:params:acme:error:rateLimited - too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s, retry after 2026-10-04 08:11:00 UTC: see https://letsencrypt.org/docs/rate-limits/#new-certificates-per-exact-set-of-identifiers"}
bind /opt/caddy/Caddyfile -> /etc/caddy/Caddyfile
```

**What the output tells you:** only the Caddyfile is mounted, and there is no `/data` volume. Every container recreate lost the certificates and the ACME account, ordered again, and finally hit the weekly limit.

**Fix:**

```yaml
services:
  caddy:
    image: caddy:2.11
    ports: ["80:80", "443:443", "443:443/udp"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data          # certificates and the ACME account: never delete it
      - caddy_config:/config
volumes:
  caddy_data:
  caddy_config:
```

While you test, add `acme_ca https://acme-staging-v02.api.letsencrypt.org/directory` to the global options. For internal names, use `tls internal` (and trust Caddy's root CA on clients) or DNS-01. After a rate limit, wait for the "retry after" time. Caddy retries by itself once the path works.

**Why this fix works:** a persistent data volume means Caddy reuses its account and certificates and renews them in place, instead of ordering new ones.

**Prevent it:** persist `/data`, run the DNS and port-80 checklist before adding a site, and monitor expiry yourself (3.7).

**Next step:** [6.1 TRAEFIK DEFAULT CERT](#61-traefik-default-cert-instead-of-lets-encrypt) (same root causes) · [25 §6 TLS scenarios](25-playbook-site-down.md#6-tls-scenarios) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Essential Commands: Work With SSL Certificates · [Caddy docs](https://caddyserver.com/docs/)

**Community threads:** [Caddy forum: How to force renewal of Let's Encrypt certificates](https://caddy.community/t/how-to-force-renewal-of-lets-encrypt-certificates/14843) · [Caddy forum: Caddy FAQ](https://caddy.community/t/caddy-frequently-asked-questions-faq/13) · Search: [Stack Overflow](https://stackoverflow.com/search?q=caddy+%22could+not+get+certificate+from+issuer%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=caddy+certificate+challenge+failed&restrict_sr=1)

---

## 13. HAProxy

### 13.1 HAProxy fails to start

> **Seen as:** systemd `Failed to start HAProxy Load Balancer.`; `Starting frontend http-in: cannot bind socket (Address already in use) [0.0.0.0:80]`; `parsing [/etc/haproxy/haproxy.cfg:42] : 'server db-global' : could not resolve address 'db-global'.` with `Failed to initialize server(s) addr.`; errors loading a certificate PEM · **Where:** HAProxy from Ubuntu (2.4 on 22.04, 2.8 on 24.04) or in Docker · **Level:** [L2 · Mid] · **How common:** "Failed to start HAProxy Load Balancer" is the HAProxy forum's most-viewed topic (68k); "HAProxy fails to start if backend server names don't resolve" (50.8k)

**Why it happens:** systemd only reports a generic failure, and the real message comes from `haproxy -c`. By default HAProxy resolves server hostnames with libc **while parsing**, so a backend container or VM that doesn't exist yet makes startup fatal. Other causes are a port already in use, a non-root process binding below 1024, and `bind ... ssl crt` pointing at a PEM without the key or the chain.

**Diagnose:**

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo ss -ltnp '( sport = :80 or sport = :443 )'
```

```
[NOTICE]   (4121) : haproxy version is 2.8.5-1ubuntu3
[ALERT]    (4121) : config : parsing [/etc/haproxy/haproxy.cfg:42] : 'server db-global' : could not resolve address 'db-global'.
[ALERT]    (4121) : config : Failed to initialize server(s) addr.
```

**What the output tells you:** the syntax is fine, but one backend name doesn't resolve at parse time, and that alone is fatal.

**Fix:**

```
defaults
    default-server init-addr last,libc,none      # start even if a name doesn't resolve yet
resolvers docker
    nameserver dns1 127.0.0.11:53
    hold valid 10s
backend be_app
    server-template app 1-5 app:8080 check resolvers docker init-addr none
```

```bash
# bind :443 ssl crt /etc/haproxy/certs/  wants certificate + chain + key in one PEM per site
cat fullchain.pem privkey.pem | sudo tee /etc/haproxy/certs/app.example.com.pem >/dev/null
sudo chmod 600 /etc/haproxy/certs/app.example.com.pem
sudo haproxy -c -f /etc/haproxy/haproxy.cfg && sudo systemctl reload haproxy
```

**Why this fix works:** `init-addr` lets HAProxy start with unresolved servers marked down, and the `resolvers` section keeps re-resolving them at runtime. `server-template` adds slots for scaled replicas.

**Prevent it:** run `haproxy -c` in CI and in Ansible handlers before every reload. Use runtime resolvers for anything dynamic, such as containers or autoscaled VMs.

**Next step:** [29 §6 HAProxy, choosing a proxy, Kubernetes ingress](29-learn-webservers-proxies.md#6-haproxy-choosing-a-proxy-kubernetes-ingress) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Implement Reverse Proxies and Load Balancers · [HAProxy](https://www.haproxy.org/)

**Community threads:** [HAProxy forum: Failed to start HAProxy Load Balancer](https://discourse.haproxy.org/t/failed-to-start-haproxy-load-balancer/5224) · [HAProxy forum: fails to start if backend server names don't resolve](https://discourse.haproxy.org/t/haproxy-fails-to-start-if-backend-server-names-dont-resolve/322) · [HAProxy wiki: Domain Name Resolution](https://github.com/haproxy/wiki/wiki/Domain-Name-Resolution-(DNS)) · Search: [Server Fault](https://serverfault.com/search?q=haproxy+%22cannot+bind+socket%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=haproxy+could+not+resolve+address&restrict_sr=1)

### 13.2 HAProxy 503 and 504: checks and flags

> **Seen as:** `503 Service Unavailable - No server is available to handle this request.`; `Server be_app/web2 is DOWN, reason: Layer7 wrong status, code: 404`; 504 with `sH--` in the log; the startup warning `missing timeouts for frontend` · **Where:** HAProxy in front of web tiers · **Level:** [L2 · Mid] · **How common:** HAProxy forum threads "Layer4 connection problem" (18.5k), "503 ... The plain HTTP request was sent to HTTPS port" (15.4k), "Backend no server has available" (12k), "Intermittent 504 errors and sR--" (13k)

**Why it happens:** HAProxy sends traffic only to servers that pass their health checks. When every check fails, HAProxy answers 503 itself. Checks often fail for reasons that have nothing to do with app health: no Host header, so a vhost-based backend returns 404; an HTTPS backend without `ssl` on the server line (400, plain HTTP sent to an HTTPS port); a firewall; or servers left in maintenance. For 504s, every log line ends with a four-character termination state. The first character says who ended the session (c/s = client/server timeout, C/S = client/server abort, P = proxy, R = resource). The second gives the phase (R request, Q queue, C connect, H headers, D data).

**Diagnose:**

```bash
sudo journalctl -u haproxy --since '1 hour ago' | grep -E 'is DOWN|no server available' | tail -2
curl -s -o /dev/null -w '%{http_code}\n' http://10.0.3.22:8080/health                            # like the check
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: app.example.com' http://10.0.3.22:8080/health
sudo grep -E ' (sH|cD|SC|sQ)-- ' /var/log/haproxy.log | tail -1                                # syslog:adm, mode 640
```

```
haproxy[3120]: [WARNING]  (3120) : Server be_app/web2 is DOWN, reason: Layer7 wrong status, code: 404, info: "Not Found", check duration: 3ms. 0 active and 0 backup servers left. 0 sessions active, 0 requeued, 0 remaining in queue.
haproxy[3120]: [ALERT]    (3120) : backend 'be_app' has no server available!
404
200
Oct  2 14:02:11 lb1 haproxy[3120]: 198.51.100.23:51522 [02/Oct/2026:14:01:41.204] fe_https~ be_reports/rep1 0/0/1/-1/30001 504 198 - - sH-- 12/10/3/1/0 0/0 "GET /reports/export HTTP/1.1"
```

**What the output tells you:** the check gets 404 without a Host header and 200 with one, so the check is wrong, not the app. Separately, `sH--` with a response time of `-1` and a total of 30001 ms means `timeout server 30s` fired while HAProxy waited for headers on a slow export.

**Fix:**

```
defaults
    mode http
    option httplog
    timeout connect 5s
    timeout client 60s
    timeout server 60s
    timeout http-request 10s
    timeout queue 30s
    timeout tunnel 1h                     # WebSockets and long polls
backend be_app
    option httpchk
    http-check send meth GET uri /health ver HTTP/1.1 hdr Host app.example.com
    http-check expect status 200
    server web1 10.0.3.21:8080 check
    server web2 10.0.3.22:8080 check
    # HTTPS backend: server web3 10.0.3.23:443 check ssl verify required ca-file /etc/haproxy/private-ca.pem sni str(app.example.com)
backend be_reports
    timeout server 300s                   # only where the slow endpoints live
```

**Why this fix works:** the check now asks the same question a real request asks, and every timeout is set on purpose instead of missing. The long server timeout is scoped to the one backend that needs it.

**Prevent it:** use health endpoints that exercise the app, not just TCP. Alert on DOWN events and "no server available", and graph per-server state and termination flags from the built-in Prometheus exporter (`http-request use-service prometheus-exporter if { path /metrics }` on a stats frontend).

**Next step:** [28 §11 Load balancing and health checks](28-learn-networking.md#11-load-balancing-and-health-checks) · [25 §7 Proxy error scenarios](25-playbook-site-down.md#7-proxy-error-scenarios-502-503-504) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Implement Reverse Proxies and Load Balancers · [HAProxy](https://www.haproxy.org/)

**Community threads:** [HAProxy forum: 503, plain HTTP request sent to HTTPS port](https://discourse.haproxy.org/t/503-service-unavailable-the-plain-http-request-was-sent-to-https-port/1538) · [HAProxy forum: Layer4 connection problem](https://discourse.haproxy.org/t/layer4-connection-problem-info-connection-refused-at-step-1-of-tcp-check-connect/3676) · [HAProxy forum: Backend no server has available](https://discourse.haproxy.org/t/backend-no-server-has-available/2008) · [HAProxy forum: Intermittent 504 errors and sR--](https://discourse.haproxy.org/t/intermittent-504-errors-and-sr-after-upgrade-to-1-7-10/2029) · Search: [Server Fault](https://serverfault.com/search?q=haproxy+%22No+server+is+available+to+handle+this+request%22) · [Stack Overflow](https://stackoverflow.com/search?q=haproxy+websocket+%22timeout+tunnel%22)

**A postmortem worth knowing [L4 · Lead].** GitLab's SREs rolled out an HAProxy change that moved backend servers to a new port and turned on PROXY protocol v2. Right after the reload, clients got TLS handshake errors. Packet captures showed HAProxy still connecting to the **old** port. The `server-state-file` had restored the saved state, port included, over the new config for every server whose name hadn't changed. They fixed it by renaming the servers. Two other options: skip state loading for that backend during the change (`load-server-state-from-file none`), or regenerate the state file before the reload. The lesson applies to any proxy: after a reload, verify the **running** state, canary one node first, roll back before you debug, and trust packet captures over config files.

```bash
grep -nE 'server-state-file|load-server-state-from-file' /etc/haproxy/haproxy.cfg
echo 'show servers state be_git' | sudo socat stdio /run/haproxy/admin.sock | awk 'NR>2 {print $4, $5, $19}'
sudo tcpdump -ni any -c 5 'tcp[tcpflags] & tcp-syn != 0 and (port 1443 or port 2443)'
```

Read: [GitLab blog: This SRE attempted to roll out an HAProxy change](https://about.gitlab.com/blog/this-sre-attempted-to-roll-out-an-haproxy-change/) · [HAProxy forum: Seamless reloads don't work with systemd](https://discourse.haproxy.org/t/seamless-reloads-dont-work-with-systemd/1954) · KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil: Change Management for Reliability · [33 §7 SRE practice](33-learn-cicd-iac-sre.md#7-sre-practice).

---

## 14. Nginx Proxy Manager

### 14.1 NPM: certificate errors or login Bad Gateway

> **Seen as:** `Internal Error` in the UI when requesting or renewing a certificate; certbot `Some challenges have failed.`; `CloudFlareAPIError adding TXT record: 10000 Authentication error`; the admin login page shows `Bad Gateway`, often right after an upgrade, while proxy hosts keep working · **Where:** NPM in homelabs and small offices · **Level:** [L2 · Mid] · **How common:** NPM's most-commented issues are certificate errors (#2011 with 145 comments, #3324, #2713) and login Bad Gateway (#310 with 114, #2753 with 138, #4606)

**Why it happens:** NPM is OpenResty/nginx plus a Node.js API and an admin UI on port 81. It runs certbot for you, and its UI hides the real errors.

- **Certificate failures.** These have the usual ACME causes: HTTP-01 can't reach NPM on port 80, DNS is wrong, or a Cloudflare-proxied record answers instead of your server. DNS challenges add their own: the token's scope, or a certbot DNS plugin that can't be installed at request time.
- **Login Bad Gateway.** The API didn't start. Typical reasons are a database that isn't ready or has wrong credentials, a failed migration because of permissions on `/data`, or plugin dependency conflicts.
- **Surprise upgrades.** An unpinned image pulled by an auto-updater. Version 2.13.3 adds a database migration that its release notes say you can't easily roll back, 2.14.0 dropped armv7, and 2.15.0 moved to a Debian Trixie base.

**Diagnose:**

```bash
docker logs --tail 100 npm 2>&1 | grep -iE 'error|certbot|migrat' | tail -2
docker exec npm tail -n 3 /tmp/letsencrypt-log/letsencrypt.log        # certbot's own log inside the container
docker inspect npm -f '{{.Config.Image}}'; docker ps --filter name=watchtower --format '{{.Names}} {{.Status}}'
```

```
[10/2/2026] [3:02:11 AM] [Global   ] › error     ER_ACCESS_DENIED_ERROR: Access denied for user 'npm'@'172.19.0.3' (using password: YES)
  Type:   unauthorized
  Detail: 198.51.100.77: Invalid response from http://app.example.com/.well-known/acme-challenge/x8KpQ2: 403
jc21/nginx-proxy-manager:latest
watchtower Up 6 days
```

**What the output tells you:** two separate problems. An auto-updater pulled `:latest` at 3 AM, and the new API can't log into its database, which explains the admin 502. Separately, the HTTP-01 check reached a CDN edge (198.51.100.77) that answered 403. The DNS record is proxied.

**Fix:**

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:2.12.3      # the last known-good tag; upgrade one minor version at a time
    labels:
      - com.centurylinklabs.watchtower.enable=false
    depends_on:
      db:
        condition: service_healthy              # and give the db service a healthcheck
```

```bash
sudo tar -czf /var/backups/npm-$(date +%F).tgz -C /opt/npm data letsencrypt     # BEFORE any upgrade or rollback
```

For HTTP-01, set the Cloudflare record to DNS-only, or switch to the DNS challenge with a zone-scoped token. If a migration already ran, restore `/data` from the backup before you roll back the image. Never publish port 81.

**Why this fix works:** a pinned image stops surprise migrations, the health-gated start removes the database race, and the certificate request now reaches NPM itself. Reading certbot's own log replaces guessing behind "Internal Error".

**Prevent it:** back up `/data` and `/etc/letsencrypt` before every upgrade, test upgrades on a copy of the volumes, and monitor certificate expiry yourself (3.7).

**Next step:** [6.1 TRAEFIK DEFAULT CERT](#61-traefik-default-cert-instead-of-lets-encrypt) (same ACME causes) · [30 §9 Docker Compose](30-learn-docker.md#9-docker-compose) · KodeKloud: *Nginx For Beginners* — Security: HTTPS · [NPM releases](https://github.com/NginxProxyManager/nginx-proxy-manager/releases)

**Community threads:** [NPM #2011: SSL certificate error](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/2011) · [NPM #3291: Internal Error on a new certificate](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/3291) · [NPM #4606: cannot log into admin after upgrade](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/4606) · [NPM #310: Bad Gateway on login](https://github.com/NginxProxyManager/nginx-proxy-manager/issues/310) · [NPM issues sorted by comments](https://github.com/NginxProxyManager/nginx-proxy-manager/issues?q=is%3Aissue+sort%3Acomments-desc) · [Let's Encrypt community: error creating a certificate in NPM](https://community.letsencrypt.org/t/error-while-creating-ssl-certificate-in-nginx-proxy-manager/210583) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=nginx+proxy+manager+%22internal+error%22+ssl&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=nginx+proxy+manager+bad+gateway+login&restrict_sr=1)

---

## 15. Apps and clouds behind the proxy

### 15.1 docker push and big uploads fail through the proxy

> **Seen as:** large layers loop on `Retrying in 5 seconds` and end in EOF; Traefik 499 or 502 at about 60 s; `error parsing HTTP 413 response body`; `blob unknown to registry`; `unauthorized: authentication required` with a token realm on http://; `x509: certificate signed by unknown authority` · **Where:** GitLab CI pushing to Harbor or the GitLab registry through Traefik or nginx; Immich and Nextcloud uploads · **Level:** [L3 · Senior] · **How common:** Immich discussion #8872; a 2025-26 Traefik forum thread on registry uploads failing with 499 in Swarm; Harbor issues #7258, #12135 and #22353; a GitLab forum thread on the registry behind Traefik

**Why it happens:** four separate limits sit on your CI-to-Harbor path:

- **Traefik's 60 s read deadline.** Since 2.11.2 and 3.0, `respondingTimeouts.readTimeout` defaults to 60 s on every entryPoint (the CVE-2024-28869 fix). It is a deadline for reading the whole request, body included, not an idle timeout.
- **nginx body limits.** Every nginx hop (Harbor's internal one included) limits bodies (10.2).
- **Wrong public URL.** A registry that isn't told its public URL hands out an `http://` token realm and internal upload URLs.
- **Untrusted private CA.** dockerd, containerd and the runner each keep their own trust store.

**Diagnose:**

```bash
curl -sI https://harbor.example.com/v2/ | grep -i '^www-authenticate'
grep -nE '^(hostname|external_url)' /opt/harbor/harbor.yml
jq -c 'select(.RequestHost=="harbor.example.com" and .DownstreamStatus>=499) | {RequestMethod, DownstreamStatus, Duration}' /opt/traefik/logs/access.log | tail -1
```

```
www-authenticate: Bearer realm="http://harbor.example.com/service/token",service="harbor-registry"
5:hostname: harbor.example.com
{"RequestMethod":"PATCH","DownstreamStatus":499,"Duration":60000412311}
```

**What the output tells you:** two faults. The token realm is `http://` because `external_url` isn't set, so clients fail authentication. A layer upload (PATCH) was cut at exactly 60.0 s, which is Traefik's read deadline.

**Fix:**

```yaml
# Traefik static (Dokploy: change it through Dokploy's Traefik settings, then restart Traefik)
entryPoints:
  websecure:
    address: ":443"
    transport:
      respondingTimeouts:
        readTimeout: 900s       # sized to your biggest push: upload time + 20%
```

```bash
# harbor.yml behind a TLS-terminating proxy: https block commented out, plus
#   external_url: https://harbor.example.com
cd /opt/harbor && sudo ./prepare && sudo docker compose down && sudo docker compose up -d
# trust the private CA on every Docker host and runner
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp private-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
```

On nginx hops, use `client_max_body_size 0; proxy_request_buffering off;`. For the GitLab registry behind Traefik, set `registry_external_url 'https://registry.example.com'` and `registry_nginx['listen_https'] = false`. If "blob unknown" persists, use the registry's `relativeurls` option (Harbor #12135).

**Why this fix works:** the read deadline now fits real pushes, the registry builds correct public URLs, and every client trusts the CA. Setting `readTimeout: 0s` restores unlimited reads, but a measured value keeps the slow-request protection that the CVE fix added.

**Prevent it:** keep a timeout table per hop (CDN, load balancer, Traefik entryPoint, Traefik-to-backend, app). Make "push a 1 GB image from CI" part of the platform smoke test, and distribute the private CA with Ansible.

**Next step:** [10.2 413 Request Entity Too Large](#102-413-request-entity-too-large) · [30 §11 Registries and Harbor](30-learn-docker.md#11-registries-and-harbor) · [47 CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab: Publish Image to GitLab Container Registry · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [Immich discussion #8872: uploads longer than 60 s](https://github.com/immich-app/immich/discussions/8872) · [Traefik forum: registry uploads fail with 499 in Swarm](https://community.traefik.io/t/docker-registry-uploads-fail-with-http-499-errors-when-running-behind-traefik-v3-6-in-docker-swarm-buffering-or-timeout-behavior-during-large-image-pushes/29527) · [Claudio Kuenzler: Harbor behind a reverse proxy](https://www.claudiokuenzler.com/blog/958/running-harbor-registry-behind-reverse-proxy-solve-docker-push-errors) · [Harbor #12135: relativeurls](https://github.com/goharbor/harbor/issues/12135) · [GitLab forum: Container Registry behind Traefik](https://forum.gitlab.com/t/troubles-enabling-container-registry-behind-traefik-reverse-proxy/97005) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+reverse+proxy+%22blob+unknown%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=traefik+upload+fails+60+seconds+readTimeout&restrict_sr=1)

### 15.2 AWS ALB in front of Traefik or nginx

> **Seen as:** target group `Health checks failed with these codes: [404]` (Target.ResponseCodeMismatch); 502 and 504 from the load balancer; `NET::ERR_CERT_COMMON_NAME_INVALID` on the ALB's DNS name; HTTP 460 · **Where:** EC2 hosts running Traefik or nginx behind an Application Load Balancer · **Level:** [L3 · Senior] · **How common:** every cause is documented in AWS's ALB troubleshooting guide; a recurring r/aws question

**Why it happens:** the ALB adds its own health checks, idle timeout (60 s by default) and error codes:

- **Host-less health checks.** The checks send the target's IP as the Host header. Traefik and nginx have no router or server block for that, so they answer 404 and the target is marked unhealthy.
- **Blocked check ports.** Security groups or NACLs block the health-check port.
- **Keep-alive too short.** A target keep-alive shorter than the idle timeout gives 502 (8.4), and responses slower than it give 504.
- **TLS ends at the ALB.** The app sees plain HTTP and loops unless X-Forwarded-Proto is trusted (9.3).

**Diagnose:**

```bash
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]' --output text
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: 10.0.1.23' http://10.0.1.23/      # from a host in the VPC
```

```
i-0a1b2c3d4e5f60718	unhealthy	Target.ResponseCodeMismatch
404
```

**What the output tells you:** the proxy is healthy. It just has no route for a request whose Host is its own IP, which is exactly what the health check sends.

**Fix:**

```yaml
# Traefik static: a host-independent health endpoint on its own port
entryPoints:
  health:
    address: ":8081"
ping:
  entryPoint: health            # GET /ping answers 200 OK
```

```bash
aws elbv2 modify-target-group --target-group-arn "$TG_ARN" \
  --health-check-port 8081 --health-check-path /ping --matcher HttpCode=200
```

For nginx, add a `default_server` block with `location = /healthz { return 200; }`. Allow the ALB's security group to reach the targets on the traffic and health-check ports. Set Traefik's `forwardedHeaders.trustedIPs` to the VPC CIDR, and keep target keep-alive above the ALB idle timeout.

**Why this fix works:** the health check now asks a question the proxy can always answer, so "unhealthy" means the proxy is really down. Separating ELB-generated from target-generated errors tells you which side to fix.

**Prevent it:** define target groups and health checks in Terraform with explicit paths and matchers. Graph `HTTPCode_ELB_5XX_Count` and `HTTPCode_Target_5XX_Count` separately.

**Next step:** [36 §6 Load balancing and Route 53](36-learn-cloud-aws.md#6-load-balancing-and-route-53) · [8.4 Intermittent 502 on idle routes](#84-intermittent-502-on-idle-routes) · KodeKloud: *AWS Networking Fundamentals* — load balancers · [AWS ELB docs](https://docs.aws.amazon.com/elasticloadbalancing/)

**Community threads:** [AWS docs: Troubleshoot your Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=aws+alb+health+check+404+host+header+traefik) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=alb+health+check+404+host+header+nginx&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises from this module, ordered by stage. Run them on the section 2 lab or a KodeKloud playground, never on a production host. You pass the module with 8 of 10 inside the time limit, each with its five-line note (symptom, first wrong guess, deciding evidence, fix, what to check first next time).

1. **Fresher · L0, 10 min.** Create `/etc/nginx/sites-available/lab.conf` with a new `server_name` and curl it without enabling it. Explain why the default site answers, then enable, test and reload it the right way. *Pass:* `curl --resolve` returns your page, and you can name the command that prints the loaded config (9.1).
2. **Junior · L1, 15 min.** On a VM where Apache owns 80 and 443, start the section 2 Traefik. Read the bind error, move Apache to 81 and 444, and publish one Apache site through a file-provider router. *Pass:* `ss -ltnp` shows the owners you expect, the site loads through Traefik, and port 81 is not reachable from outside (7.1, 5.5).
3. **Junior · L1, 10 min.** Upload a 5 MB file through nginx with its default config. *Pass:* you quote the error.log line and raise the limit only for the upload location (10.2).
4. **Mid · L2, 15 min.** Set whoami's `loadbalancer.server.port` to 8080. *Pass:* you prove it is a Traefik-generated 502 from the access log (OriginStatus 0) and fix it before you open the Compose file (5.2).
5. **Mid · L2, 15 min.** Attach whoami to a second network and remove `traefik.docker.network`. *Pass:* you find the network warning, explain the random 504s, and fix it with an external, explicitly named network (5.3).
6. **Mid · L2, 20 min.** Point a staging-CA router at a name with a wrong AAAA record, or block port 80 at the router. *Pass:* you quote the ACME error and explain why the browser shows TRAEFIK DEFAULT CERT (6.1).
7. **Senior · L3, 20 min.** Publish a Gitea or GitLab SSH port through a Traefik TCP entryPoint on 2222. *Pass:* `ssh -T -p 2222` reaches the app, and port 22 still reaches the host's sshd (8.1).
8. **Senior · L3, 25 min.** Put Authelia or Authentik in front of whoami, then add the middleware to the portal's own router as well. *Pass:* you reproduce the redirect loop, fix it, and whoami shows the identity header (`Remote-User` or `X-authentik-username`) (8.2).
9. **Senior · L3, 20 min.** Upload a file that takes 90 s through Traefik with the default `readTimeout`. *Pass:* you show the 499 and 60 s pair in the access log, and fix it per entryPoint with a measured value instead of 0 (15.1).
10. **Lead · L4, 30 min.** Run a Node backend with `keepAliveTimeout = 1000` behind Traefik and send one request every 1–5 s for 10 minutes. *Pass:* you capture the backend's FIN or RST with tcpdump, remove the 502s by changing one timeout, and write the hop-by-hop timeout table for your platform (8.4).

---

## Where to go next

- **Deeper fundamentals:** [29 Web servers & proxies](29-learn-webservers-proxies.md) covers Apache, nginx, Traefik and Dokploy in depth. [28 Networking](28-learn-networking.md) covers NAT, TLS and load balancing.
- **Your own incident:** [21 Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md), [22 Who owns this port?](22-playbook-ports-inventory.md) and [35 Deployment patterns](35-deployment-patterns.md).
- **When a site is down:** [25 Site down: DNS, TLS, proxy](25-playbook-site-down.md) and [26 Docker & K8s incidents](26-playbook-containers-k8s.md).
- **The tools around Traefik:** [45 Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md), [47 CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) (GitLab and Harbor pushes) and [48 Wazuh & security tools](48-wazuh-and-security-tools.md) (CrowdSec, Authentik, Authelia).
- **Kubernetes ingress and the Gateway API:** [31 §8 Ingress and the Gateway API](31-learn-kubernetes.md#8-ingress-and-the-gateway-api).
- **Hardening, TLS and monitoring the edge:** [37 Security & DevSecOps](37-learn-security-devsecops.md) and [32 Performance & observability](32-learn-performance-observability.md).
- **Career:** [40 Career ladder](40-career-ladder.md) covers proxy skills per stage and interview practice. Proxy debugging from logs alone is a standard mid-level interview task.
- **Official docs:** [Traefik](https://doc.traefik.io/traefik/), [nginx](https://nginx.org/en/docs/), [Apache httpd](https://httpd.apache.org/), [Caddy](https://caddyserver.com/docs/), [HAProxy](https://www.haproxy.org/), [Nginx Proxy Manager releases](https://github.com/NginxProxyManager/nginx-proxy-manager/releases) and [Dokploy domain troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains).
- **Where the problems come from:** the [Traefik forum top topics](https://community.traefik.io/top?period=all), [Traefik issues by reactions](https://github.com/traefik/traefik/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc), the [HAProxy forum top topics](https://discourse.haproxy.org/top?period=all), [NPM issues by comments](https://github.com/NginxProxyManager/nginx-proxy-manager/issues?q=is%3Aissue+sort%3Acomments-desc) and [Dokploy issues by reactions](https://github.com/Dokploy/dokploy/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc). Read a few threads a week. It is the fastest way to learn what breaks in real deployments.
