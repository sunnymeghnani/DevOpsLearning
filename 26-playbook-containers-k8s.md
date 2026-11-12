# 26 — Docker, Dokploy/Traefik & Kubernetes Incidents

This is the "it is broken right now" companion to the command references
[Docker & Containers](14-docker-containers.md) and [Kubernetes](15-kubernetes.md).
Every scenario below is a walk, not a list: you look at one layer, read the
evidence, and the evidence tells you which layer to look at next. Each step says
**what** to run, **what the output means**, **why this step comes now**, and
**where to go next**. Each scenario ends with a decision tree, the fix and how
to verify it, how to roll back, and how to stop it happening again.

**Who this module is for.** It serves every career stage from Junior to Lead, and
it is the module where a Mid-level engineer grows into a Senior one: these are
the incidents you get paged for on Docker, Dokploy and Kubernetes hosts. Every
scenario carries a tag such as [L2 · Mid]: the Ops Ladder level and the career
stage by which you should solve that incident **alone**, with evidence, in about
30 minutes. The tags follow the Ops Ladder and the
[Docker](30-learn-docker.md) and [Kubernetes](31-learn-kubernetes.md) learn
modules (Docker basics L1, Docker networking and proxies L2, Swarm and
Kubernetes L3, cluster maintenance L4).

| Stage | How to use this module | Start with |
|---|---|---|
| Fresher [L0 · Fresher] | Read section 1, run the "first five minutes" commands on a lab VM, be the note-taker in real incidents | Section 1, then section 2 on a lab |
| Junior [L1 · Junior] | Own alone: restart loops, port conflicts, Docker filling the disk, containers on different networks | Sections 2, 3, 5 |
| Mid-level [L2 · Mid] | Own alone: DNS inside containers, the UFW bypass, Harbor x509, Traefik 404/502/ACME, the Dokploy UI | Sections 3, 4, 6, 7 |
| Senior [L3 · Senior] | Kubernetes (CKA track), Swarm placement and overlays, subnet design, slow containers; fix it so it cannot recur | Sections 8–11, master trees in 12 |
| Lead / SRE [L4 · Lead] | Control-plane certificates and recovery, running the incident call, turning every "Prevent it next time" into a team standard | Sections 10–13 |

On the CKA track you practise the [L3 · Senior] Kubernetes scenarios long before
you are Senior: the tag says when you should own the incident, not when to
start learning it. The exit test in section 13 is graded per stage.

Placeholders are UPPERCASE: CONTAINER (name or ID), IMAGE, SERVICE (a Swarm
service), POD, NS (namespace), NODE, DOMAIN, HARBOR (your registry host, for
example harbor.example.com), PORT (container port), HOSTPORT (published host port).

> ⚠️ Sample outputs are illustrative: Ubuntu 22.04/24.04, Docker Engine 27 or
> newer, Traefik v3 as installed by Dokploy, and kubeadm clusters on containerd.
> Your versions will print slightly different text. Run the commands on the
> affected server or cluster, read before you change, and change one thing at a time.

---

## 1. How to use this playbook

> 📚 **Study path:** 1) Note: [Docker reference](14-docker-containers.md) and [Kubernetes reference](15-kubernetes.md) (the commands this playbook strings together) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands: Inspect and Logs ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 3) Read: [learnkube: Troubleshooting deployments](https://learnkube.com/troubleshooting-deployments) (the bottom-up flowchart) and [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 4) Practice: one [SadServers](https://sadservers.com/scenarios) scenario tagged docker, 30 minutes, then write the five-line incident note.

### The method in five moves

The same five moves work for a Compose app on one VM, a Dokploy fleet and a
Kubernetes cluster. They are the habits the ops ladder's L2 and L3 levels train.

1. **Stabilize first.** If the breakage started right after a change (deploy,
   daemon.json edit, upgrade), roll back first and diagnose second. Users care
   that it works; you can study the broken version later on a copy.
2. **Look before you touch.** Restarting destroys evidence. `docker rm` deletes
   the container's logs, `kubectl delete pod` throws away `--previous` logs,
   and a Docker daemon restart recreates every network rule. Capture first:
   `docker logs`, `docker inspect`, `kubectl describe`, `kubectl logs --previous`.
3. **Walk the layers in order.** Docker: process → container → network
   namespace → Docker network → published port / NAT → host firewall → proxy →
   DNS and client. Kubernetes (bottom-up, as in the CKA exam): pods → Services
   → Ingress → nodes → control plane.
4. **Change one thing at a time** and re-test after each change. Two changes at
   once means you will never know which one fixed it (or which one broke
   something else).
5. **Verify from the user's side**, then write the five-line incident note
   (template at the end of this section).

### Where a request can die

Read this map from left to right when "the app is down". Each box is a layer
you can test on its own, and each has a scenario below.

```
 client ──► DNS ──► host :80/:443 ──► Traefik ──────────► Docker network ──► container ──► app ──► dependencies
            │        │                 │                    │                 │             │       │
            │        │                 ├ entrypoint web/    ├ dokploy-network ├ listens on  ├ crash ├ DB on host
            │        │                 │ websecure          │ membership      │ 0.0.0.0:PORT│ OOM   │ (host-gateway)
            │        │                 ├ router rule (Host) ├ embedded DNS    ├ right port  │ slow  ├ other containers
            │        │                 ├ TLS cert (ACME)    │ 127.0.0.11      │             │       ├ DNS 127.0.0.11
            │        ├ who owns the    └ service port label └ subnet clashes  └ exit codes  │       └ registry (Harbor)
            │        │ port (Apache?)                         with on-prem LAN
            │        └ UFW vs DOCKER-USER (published ports skip UFW)
            └ A record, TTL, resolver cache
```

| Layer | Typical symptom | Scenario in this module |
|---|---|---|
| DNS (outside) | curl: (6) Could not resolve host | [Site down playbook](25-playbook-site-down.md), [DNS reference](08-dns.md) |
| Host port | port is already allocated / address already in use | Section 3 |
| Host firewall | works locally, times out remotely, or exposed when it should not be | Section 3 |
| Traefik | 404 page not found, 502 Bad Gateway, TRAEFIK DEFAULT CERT | Section 7 |
| Docker network | could not resolve, i/o timeout between containers | Section 4 |
| Container | Exited (1), Restarting, OOMKilled | Section 2 |
| Kubernetes workload | Pending, ImagePullBackOff, CrashLoopBackOff | Section 8 |
| Kubernetes traffic | no endpoints, Ingress 503, DNS NXDOMAIN | Section 9 |
| Kubernetes platform | NotReady, connection refused :6443, x509 expired | Section 10 |
| Kubernetes changes | rollout exceeded its progress deadline, HPA target unknown | Section 11 |

### Find your scenario by error text

Search this table (press `/` in the handbook) for the exact text you are looking at.

| Error text or symptom | Go to |
|---|---|
| `Exited (1)`, `Restarting (1)`, exit 125/126/127/139/143 | 2 → Container exits immediately or restart-loops |
| `exec format error`, `exec ... no such file or directory` | 2 → Container exits immediately or restart-loops |
| `Exited (137)`, `"OOMKilled": true` | 2 → OOMKilled and exit code 137 |
| `Job for docker.service failed`, `unable to configure the Docker daemon` | 2 → Docker daemon will not start |
| `Bind for 0.0.0.0:80 failed: port is already allocated` | 3 → Port already allocated or address in use |
| `listen tcp4 0.0.0.0:443: bind: address already in use` | 3 → Port already allocated or address in use |
| `connection refused` to host.docker.internal or 172.17.0.1 | 3 → Container cannot reach a service on the host |
| port reachable from the internet although UFW denies it | 3 → Published ports bypass UFW |
| `Temporary failure in name resolution` inside a container | 4 → DNS fails inside a container |
| `could not translate host name "db"`, `getaddrinfo EAI_AGAIN` | 4 → Containers on different networks cannot talk |
| SSH from the office dies after `docker compose up` | 4 → Docker subnet collides with on-prem networks |
| `no space left on device` on a Docker host | 5 → Docker filled the disk |
| `permission denied` / `Operation not permitted` on a volume | 5 → Permission denied on bind mounts or NFS |
| `x509: certificate signed by unknown authority` (Harbor) | 6 → x509 unknown authority pulling from Harbor |
| `failed to solve`, `failed to compute cache key`, apt/npm DNS errors in build | 6 → Image build failures |
| container slow, CPU pinned at exactly 100% or 200% | 6 → Slow container |
| `404 page not found` (Traefik) | 7 → Traefik returns 404 page not found |
| `Bad Gateway`, `Gateway Timeout` | 7 → Traefik returns 502 Bad Gateway |
| browser shows `TRAEFIK DEFAULT CERT`, ACME errors | 7 → Let's Encrypt certificate not issued |
| Dokploy panel on :3000 does not load | 7 → Dokploy UI unreachable on port 3000 |
| `docker service ps` shows Pending, Rejected, `no suitable node` | 7 → Swarm service stuck Pending or Rejected |
| new deploy "succeeded" but users still see the old version | 7 → Deploy succeeded but old version served |
| Swarm tasks on different nodes cannot talk, requests hang | 7 → Swarm overlay traffic hangs between nodes |
| `0/3 nodes are available` | 8 → Pod stuck in Pending |
| `ErrImagePull`, `ImagePullBackOff` | 8 → ImagePullBackOff and ErrImagePull |
| `CrashLoopBackOff`, `CreateContainerConfigError` | 8 → CrashLoopBackOff |
| `Reason: OOMKilled` in `kubectl describe` | 8 → OOMKilled in Kubernetes |
| `Evicted`, `The node was low on resource` | 8 → Evicted pods and DiskPressure |
| READY `0/1`, Service has no endpoints | 9 → Readiness fails so the Service has no endpoints |
| Service has endpoints but `connection refused` | 9 → Service selector, port or targetPort mismatch |
| Ingress returns 404 / 502 / 503 | 9 → Ingress returns 404, 502 or 503 |
| `NXDOMAIN`, `server can't find SERVICE` in a pod | 9 → Pod cannot resolve Service names |
| `[FATAL] plugin/loop: Loop ... detected` | 9 → CoreDNS CrashLoopBackOff with loop detected |
| everything times out after a NetworkPolicy was applied | 9 → NetworkPolicy blocks traffic or DNS |
| `NotReady`, `Kubelet stopped posting node status` | 10 → Node NotReady |
| PVC `Pending`, `waiting for a volume to be created` | 10 → PVC stuck in Pending |
| `The connection to the server ...:6443 was refused` | 10 → kubectl connection refused or apiserver down |
| `x509: certificate has expired or is not yet valid` (kubectl) | 10 → kubeadm certificate expiry |
| `exceeded its progress deadline` | 11 → Rollout stuck |
| HPA TARGETS `<unknown>/70%` | 11 → HPA not scaling |

### First five minutes on a Docker or Dokploy host

**Goal:** get the whole picture in one screen before you dive into one container.

```bash
# 1. What is running, what died recently, and how (exit codes)?
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | head -30

# 2. Swarm services (Dokploy apps and Dokploy itself run as Swarm services)
docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'

# 3. Is the daemon healthy, and what did it complain about recently?
systemctl is-active docker containerd
sudo journalctl -u docker --since '30 min ago' -p warning --no-pager | tail -20

# 4. Disk: the most common silent killer of Docker hosts
df -h / /var/lib/docker 2>/dev/null ; docker system df

# 5. Who holds the web ports? (Traefik should, not Apache)
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'

# 6. What does the proxy say? (Dokploy's Traefik container)
docker logs --since 10m dokploy-traefik 2>&1 | tail -30
```

```
NAMES                                   STATUS                         PORTS
dokploy-traefik                         Up 6 days                      0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, ...
shop-api-x1y2z3.1.k2v8x0q1m3n4p5q6     Up 2 hours
shop-worker-a7b8c9.1.r1s2t3u4v5w6x7    Restarting (1) 12 seconds ago
dokploy.1.p9c7d6e5f4a3b2c1d0e9f8g7     Up 6 days                      0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
dokploy-postgres.1.t3u4v5w6x7y8z9a0     Up 6 days                      5432/tcp
dokploy-redis.1.b2c3d4e5f6g7h8i9j0     Up 6 days                      6379/tcp

NAME               REPLICAS   IMAGE
dokploy            1/1        dokploy/dokploy:latest
dokploy-postgres   1/1        postgres:16
dokploy-redis      1/1        redis:7
shop-api-x1y2z3    1/1        harbor.example.com/shop/api:1.4.2
shop-worker-a7b8c9 0/1        harbor.example.com/shop/worker:1.4.2
```

**What it means:** Traefik is up and owns 80/443, the API is fine, and the
worker is crash-looping with exit code 1 (`0/1` replicas). That is where you
go next: section 2. Swarm task containers are named `SERVICE.SLOT.TASKID`, so
`docker logs` needs the full container name, while `docker service logs SERVICE`
takes the service name.

**Why this step (now):** six read-only commands cover the layers where most
Docker incidents live (container state, Swarm services, the daemon, the disk,
the web ports and the proxy), so you choose the scenario from evidence instead
of from the ticket's wording. Nothing here changes the system.

**Next step:** If a container or service is down → section 2. If the disk is
above 90% → section 5. If Apache or another process holds 80/443 → section 3.
If Traefik logs errors for one domain → section 7. If everything looks healthy →
walk the Docker master tree in section 12, level by level.

> 💡 In current Dokploy, Traefik runs as a plain container called
> `dokploy-traefik` (older installs ran it as a Swarm service: check
> `docker service ls`). Its static config is `/etc/dokploy/traefik/traefik.yml`,
> dynamic files live in `/etc/dokploy/traefik/dynamic/`, and certificates are
> stored in `acme.json` in that same dynamic folder.

### First five minutes on a Kubernetes cluster

**Goal:** confirm you are on the right cluster, then find everything unhappy.

```bash
kubectl config current-context                    # wrong cluster = wasted hour
kubectl get nodes -o wide                         # all Ready? versions skewed?
kubectl get pods -A | grep -vE 'Running|Completed' # everything not happy
kubectl get pods -A -o wide | awk '$3 ~ /^0\// || $5 > 5'   # not ready, or many restarts
kubectl get events -A --sort-by=.lastTimestamp | tail -25
kubectl get --raw='/readyz?verbose' | tail -5     # apiserver health checks
kubectl -n kube-system get pods -o wide           # control plane, CoreDNS, CNI, kube-proxy
```

```
NAMESPACE     NAME                              READY   STATUS             RESTARTS        AGE
kube-system   coredns-7c65d6cfc9-4xkqp          0/1     CrashLoopBackOff   9 (2m ago)      25m
shop          api-6d9f7b8c5-mx2lq               0/1     Running            0               4m
shop          worker-5c7d8f9b6-q8w2n            0/1     ImagePullBackOff   0               4m
```

**What it means:** three different layers are hurting. Fix them bottom-up:
CoreDNS first (section 9; every app that resolves names depends on it), then the
image pull (section 8), then the API that is Running but not Ready (section 9;
its readiness probe probably calls something that needs DNS).

**Why this step (now):** the context check prevents the classic hour spent
fixing the wrong cluster, and the rest lists every unhappy object in one screen,
so you can apply the bottom-up order (platform, then pods, then traffic) before
you open a single log.

**Next step:** If `kubectl` itself fails or nodes are NotReady → section 10. If
kube-system pods are failing → fix those first (CoreDNS and CNI in section 9,
control plane in section 10). Then the app pods → section 8, and pods that
are Running but not Ready, or Services → section 9. Nothing obviously wrong →
the Kubernetes master tree in section 12.

### Safety rules and dangerous commands

These commands appear in many blog answers. Each one can turn a small incident
into a big one. Do the safer thing first.

| Dangerous command | What can go wrong | Do this first |
|---|---|---|
| `docker system prune -a --volumes` | deletes every unused image (your rollback images), every stopped container and every anonymous volume no container uses (named volumes too on Docker before 23; `docker volume prune -a` removes named ones on any version), for example the data of a database started without a named volume | `docker system df -v`, then `docker builder prune`, then targeted prunes (section 5) |
| `docker rm -f CONTAINER` | deletes its logs and writable layer, the evidence | `docker logs CONTAINER > /root/CONTAINER.log 2>&1`, `docker inspect CONTAINER > /root/CONTAINER.json` |
| `systemctl restart docker` | stops every container on the host; on a Swarm (Dokploy) host `live-restore` cannot be used, so everything restarts | fix the one container or service; schedule a daemon restart |
| `iptables -F` / `nft flush ruleset` | wipes Docker's NAT and isolation rules: every published port and all container egress break | inspect with `iptables -L DOCKER-USER -n -v`; add rules to DOCKER-USER |
| `kill -9` on a container's PID | no graceful shutdown, possible data corruption | `docker stop -t 30 CONTAINER` (SIGTERM, then SIGKILL after 30 s) |
| `kubectl delete pod POD` | loses `kubectl logs --previous`; a bare pod (no controller) never comes back | `kubectl logs POD --previous`, `kubectl describe pod POD`; check `ownerReferences` |
| `kubectl delete pod --force --grace-period=0` | the old container may still run on the node (two writers on one volume) | find out why it hangs: finalizers, NotReady node |
| `kubectl delete pvc` / `namespace` | permanent data loss when the reclaim policy is Delete | back up; check `kubectl get pv` reclaim policy |
| `kubeadm reset` | wipes the node's cluster state | almost never needed for troubleshooting |
| editing `/etc/kubernetes/manifests/*.yaml` in place | a typo removes the apiserver and kubectl with it | copy the file to `/root/` first (never into the manifests folder) |

### Incident note template

After every incident, even a small one, write these five lines (the habit from
the ops ladder's weekly rhythm). After ten incidents you have a personal runbook.

```
Symptom:        502 on shop.example.com after deploy 14:05
First guess:    app crashed (wrong)
Evidence:       Traefik debug log: dial tcp 10.0.1.23:8000: connect: connection refused;
                netshoot ss -ltn inside container: LISTEN 127.0.0.1:8000
Fix:            gunicorn --bind 0.0.0.0:8000 ; redeployed 14:31
Check first next time:  ss -ltn inside the container before reading app logs
```

---

## 2. Docker: containers that will not stay up

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Inspect and Logs), then Docker Images (CMD vs ENTRYPOINT) ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Restart Policies, Troubleshooting Docker Daemon ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page)) · 3) Note: [Learn Docker](30-learn-docker.md) (lifecycle, PID 1, resource limits) · 4) Video: *Learn Docker in 2 Hours - A Full Tutorial (2025)* ([YouTube](https://www.youtube.com/watch?v=zJ6WbK9zFpI)) · 5) Practice: [Docker playground](https://kodekloud.com/playgrounds/playground-docker): make a container exit 127, 137 and 143 on purpose and read each one with `docker inspect`.

### Container exits immediately or restart-loops

> 📚 **Know this first:** 1) Note: [Docker reference](14-docker-containers.md) (logs, inspect, exec) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Images: CMD vs ENTRYPOINT ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 3) KodeKloud: *Docker Certified Associate* — Restart Policies ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)).

**Level:** [L1 · Junior] — pure operator work: status, exit code, logs, inspect.

**Symptom:** `docker ps -a` shows `Exited (N)` seconds after start, or
`Restarting (N)`; a Dokploy app shows `0/1` replicas and the deploy log ends
without errors.

#### Step 1 — Read the status and the exit code

**Goal:** turn "it doesn't start" into a number, because the exit code tells you which half of the problem you are in.

```bash
# Status of the suspect container (or all of them)
docker ps -a --filter name=worker --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'

# The state that matters, on one line
docker inspect -f 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}} policy={{.HostConfig.RestartPolicy.Name}} error={{.State.Error}}' CONTAINER

# Swarm service (Dokploy application): every task, including the dead ones
docker service ps SERVICE --no-trunc --format 'table {{.Name}}\t{{.CurrentState}}\t{{.Error}}'
```

```
NAMES    STATUS                         IMAGE
worker   Restarting (1) 8 seconds ago   harbor.example.com/shop/worker:1.4.2

exit=1 oom=false restarts=37 policy=unless-stopped error=

NAME                   CURRENT STATE            ERROR
shop-worker-a7b8c9.1   Starting 2 seconds ago
 \_ shop-worker-a7b8c9.1   Failed 9 seconds ago     "task: non-zero exit (1)"
 \_ shop-worker-a7b8c9.1   Failed 21 seconds ago    "task: non-zero exit (1)"
```

**What it means:** exit 1 with no OOM and 37 restarts: the application itself
gives up at startup. Use this table to choose where to look:

| Exit code | Meaning | Look next |
|---|---|---|
| 0 | the main process finished normally; for a service that means it ended or went to the background (`apachectl start`, `service x start`, nginx without `daemon off;`) | Step 3 (what command runs) |
| 1, 2, other small numbers | the application reported an error | Step 2 (logs) |
| 125 | `docker run` itself failed; the container never started (bad flag, port conflict, missing network) | read the CLI error; port conflicts → section 3 |
| 126 | the command exists but cannot be executed (no x bit, a directory, a `noexec` mount) | Step 4 |
| 127 | command not found (not installed, wrong PATH, missing interpreter) | Step 4 |
| 134 | SIGABRT: the program aborted itself (assertion, glibc error) | Step 2, then Step 4 |
| 137 | SIGKILL: OOM killer, or `docker stop` timed out and killed it | OOMKilled scenario below, or Step 5 |
| 139 | SIGSEGV: segmentation fault (glibc binary on musl/alpine, wrong arch library, app bug) | Step 4 |
| 143 | SIGTERM: something stopped it on purpose (docker stop, Swarm update, Dokploy redeploy) | Step 5 |

Codes above 128 are 128 + signal number: 137 = 128 + 9 (KILL), 143 = 128 + 15 (TERM).

**Why this step (now):** the exit code is free, it survives restarts, and it
splits the problem space in half before you read a single log line: "the app
said no" (1) versus "the app never ran" (126/127) versus "something killed it"
(137/143).

**Next step:** If 1/2/134 → Step 2. If 0 → Step 3. If 126/127/139 → Step 4. If
137 → check `oom=true` (OOMKilled scenario) else Step 5. If 143 → Step 5.

> 💡 If the loop is hurting something (hammering a database, filling logs),
> pause it while you investigate: `docker update --restart=no CONTAINER && docker stop CONTAINER`.
> For a Swarm service, `docker service scale SERVICE=0` stops it (this takes the
> service offline: say so in the incident channel first).

#### Step 2 — Read the logs of the failed runs

**Goal:** read the application's own last words.

```bash
# stdout/stderr; for a restarting container this includes the earlier runs
docker logs --tail 50 -t CONTAINER

# Only the interesting lines from the last 10 minutes
docker logs --since 10m CONTAINER 2>&1 | grep -iE 'error|fatal|exception|denied|refused|not found' | tail -20

# Swarm / Dokploy app: logs from all tasks of the service, old ones included
docker service logs --tail 50 --timestamps SERVICE
```

```
2026-10-03T09:14:02.118Z Traceback (most recent call last):
2026-10-03T09:14:02.120Z   File "/app/worker.py", line 12, in <module>
2026-10-03T09:14:02.121Z     REDIS_URL = os.environ["REDIS_URL"]
2026-10-03T09:14:02.121Z KeyError: 'REDIS_URL'
```

**What it means:** the worker needs a `REDIS_URL` variable and did not get one.
The usual exit-1 causes, in order of frequency:

- a missing or misspelled environment variable or secret
- a dependency that is not reachable at startup (the app exits instead of retrying): `connection refused`, `could not translate host name`
- a config file that is not mounted, or mounted as an empty directory
- database migrations that fail on start
- the app writes its log to a file instead of stdout, so `docker logs` is empty

**Why this step (now):** after the exit code, the app's own message is the
cheapest and most specific evidence. Most loops end here.

**Next step:** If an env var or file is missing → Step 3. If the log is empty →
Step 4 (the process probably never started). If it says `connection refused` or
`could not resolve` for a dependency → [section 4](26-playbook-containers-k8s.md)
on Docker networking, or the "host service" scenario in section 3.

#### Step 3 — Compare what the container actually received

**Goal:** see the real command, environment and mounts, not what you think the Compose file says.

```bash
# The command that really runs
docker inspect -f '{{json .Config.Entrypoint}} {{json .Config.Cmd}}' CONTAINER

# The environment, with secret values masked before you paste it anywhere
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' CONTAINER \
  | sed -E 's/^([^=]*(PASS|SECRET|TOKEN|KEY)[^=]*)=.*/\1=****/'

# Mounts: source on the host -> destination in the container
docker inspect -f '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}} rw={{.RW}}{{println}}{{end}}' CONTAINER

# Compose: the fully rendered config, with ${VARIABLES} substituted
docker compose config SERVICE
```

```
["/docker-entrypoint.sh"] ["python","worker.py"]
PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
DATABASE_URL=****
bind /srv/shop/config.yml -> /app/config.yml rw=true
```

**What it means:** `REDIS_URL` is simply not there. Typical reasons: the
`env_file` path is wrong, the variable was added in the Dokploy UI but the app
was not redeployed (environment changes apply only on the next deploy), or a
typo (`REDIS_URI`). A second classic: if `/srv/shop/config.yml` did not exist on
the host when the container was created, Docker created an empty **directory**
with that name and the app fails with "Is a directory".

```bash
ls -ld /srv/shop/config.yml      # a "d" in the first column = Docker created a directory
```

**Why this step (now):** the log told you what is missing; inspect tells you why
it is missing, from the daemon's point of view, which is the only one that counts.

**Next step:** If you found the gap → fix the env/mount, redeploy, go to "Fix &
verify". If everything looks right but the process still dies before logging →
Step 4.

#### Step 4 — Override the entrypoint and look inside

**Goal:** start the same image with a shell instead of the app, then run the real command by hand.

```bash
# Same image, shell instead of the entrypoint; nothing is modified
docker run --rm -it --entrypoint sh IMAGE

# Compose: a one-off twin with the same env, mounts and networks as the service
docker compose run --rm --entrypoint sh SERVICE

# A stopped container's files (works even if it never stays up)
docker cp CONTAINER:/app/config.yml ./config.from-container.yml

# Inside the shell: is the entrypoint executable, which interpreter, which arch?
ls -l /docker-entrypoint.sh
head -1 /docker-entrypoint.sh | od -c | head -2
command -v python gunicorn bash
uname -m
```

```
/ # ls -l /docker-entrypoint.sh
-rw-r--r--    1 root     root           412 Oct  3 08:55 /docker-entrypoint.sh
/ # head -1 /docker-entrypoint.sh | od -c | head -2
0000000   #   !   /   b   i   n   /   b   a   s   h  \r  \n
/ # command -v python gunicorn bash
/usr/local/bin/python
/usr/local/bin/gunicorn
/ #
```

**What it means:** three bugs in one image:

- `-rw-r--r--`: no execute bit → `exec: "/docker-entrypoint.sh": permission denied` inside the OCI runtime error (exit 126)
- `\r \n`: Windows line endings; the kernel looks for an interpreter literally called `/bin/bash\r` → `exec /docker-entrypoint.sh: no such file or directory`, although the file exists
- `bash` is not found (alpine ships only `sh`) → the same misleading "no such file or directory"

Other start-time messages and what they really mean:

| Message | Real cause | Fix |
|---|---|---|
| `exec: "gunicorn": executable file not found in $PATH` | not installed, or installed in a venv that is not on PATH | install it, or use the full path in CMD |
| `exec /app/start.sh: exec format error` | image built for another CPU (arm64 image on amd64), or a script without a shebang line | `docker image inspect -f '{{.Architecture}}' IMAGE`; build with `--platform linux/amd64`; add `#!/bin/sh` |
| `Segmentation fault`, exit 139 | glibc binary on an alpine (musl) image | use a matching base image (debian-slim) |
| exits 0 at once, no log | CMD starts a daemon that forks to the background | run in the foreground (`nginx -g 'daemon off;'`, `apache2ctl -D FOREGROUND`) |

**Why this step (now):** when the process dies before it can log, you can only
see the failure by reproducing it by hand inside the same filesystem. Overriding
the entrypoint changes nothing in the image, so it is safe on production hosts.

**Next step:** If you reproduced the failure → fix the Dockerfile (see
"Prevent it next time"), rebuild, redeploy. If the command works by hand but the
container still dies → Step 5 (something outside is stopping it).

#### Step 5 — Find out who stopped it

**Goal:** for exit 143, or 137 without OOM, find the actor that sent the signal.

```bash
# Daemon event stream for this container: kill signals, die, health status
docker events --since 30m --until "$(date +%s)" --filter container=CONTAINER

# Healthcheck state (Swarm replaces unhealthy tasks; plain Docker does not)
docker inspect -f '{{json .State.Health}}' CONTAINER | jq '{Status, FailingStreak, last: (.Log[-1] | {ExitCode, Output})}'
```

```
2026-10-03T09:20:11.402119871Z container kill 9c2d11ab4e77 (image=harbor.example.com/shop/worker:1.4.2, name=worker, signal=15)
2026-10-03T09:20:21.410551203Z container kill 9c2d11ab4e77 (image=harbor.example.com/shop/worker:1.4.2, name=worker, signal=9)
2026-10-03T09:20:21.538220415Z container die 9c2d11ab4e77 (exitCode=137, image=harbor.example.com/shop/worker:1.4.2, name=worker)

{
  "Status": "unhealthy",
  "FailingStreak": 5,
  "last": { "ExitCode": 1, "Output": "curl: (7) Failed to connect to localhost port 8000: Connection refused" }
}
```

**What it means:** signal 15, then signal 9 exactly 10 seconds later: someone
ran `docker stop` (or Swarm/Dokploy replaced the task) and the app ignored
SIGTERM, so Docker killed it after the 10-second grace period. Ignoring SIGTERM
almost always means the app is not PID 1: a shell-form `CMD python app.py` runs
`/bin/sh -c`, and `sh` does not forward signals. The healthcheck is also failing;
in Swarm mode an unhealthy task is killed and replaced, which looks exactly like
a restart loop.

**Why this step (now):** a container that works by hand but dies in service is
being killed from outside. The event stream names the actor and the signal, so
you stop guessing.

**Next step:** If the healthcheck fails → check that the healthcheck command
exists in the image (`curl` is missing from many slim images) and probes the
right port; give the app a longer `start_period`. If SIGTERM is ignored → exec-form
CMD or `exec "$@"` at the end of the entrypoint script. If signal 9 with OOM →
the OOMKilled scenario.

#### Decision tree: container will not stay up

```
docker ps -a / docker service ps --no-trunc
├── exit 0 ............ CMD ends or daemonizes → run in foreground
├── exit 1/2/134 ...... docker logs → missing env / file / dependency → inspect Env/Mounts
├── exit 125 .......... docker run error text (port in use? network missing?)
├── exit 126/127 ...... --entrypoint sh → x bit? CRLF? interpreter? PATH?
├── exit 139 .......... musl vs glibc, arch mismatch
├── exit 137 .......... OOMKilled=true → OOM scenario
│                       OOMKilled=false → docker events: stop timeout / kill
└── exit 143 .......... docker events: who stopped it? healthcheck in Swarm?
```

**Fix & verify**

```bash
# Rebuild and redeploy, then make sure the restart counter stops moving
docker inspect -f '{{.State.Status}} restarts={{.RestartCount}} started={{.State.StartedAt}}' CONTAINER
sleep 60
docker inspect -f '{{.State.Status}} restarts={{.RestartCount}} started={{.State.StartedAt}}' CONTAINER
docker service ps SERVICE --format '{{.Name}} {{.CurrentState}}' | head -3   # Swarm: Running for > 1 min
```

→ Same `StartedAt` and same restart count a minute apart means it is stable.

**Rollback**

```bash
docker service rollback SERVICE                                     # Swarm: previous spec
docker service update --image harbor.example.com/shop/worker:1.4.1 SERVICE   # or pin the last good tag
# Compose: set the previous tag in compose.yaml, then
docker compose up -d SERVICE
```

In Dokploy, redeploy the previous image tag or commit from the app's
Deployments tab.

**Prevent it next time**

- Exec-form `CMD ["python","worker.py"]`, and `exec "$@"` as the last line of entrypoint scripts, so the app is PID 1 and receives SIGTERM.
- `COPY --chmod=755 docker-entrypoint.sh /` and a `.gitattributes` line `*.sh text eol=lf` so CRLF never reaches an image.
- Validate required variables at startup with a clear message, and retry dependencies with backoff instead of exiting.
- Add a CI smoke test: start the image, wait for its health endpoint, fail the pipeline if it does not answer ([CI/CD module](33-learn-cicd-iac-sre.md)).
- Log to stdout/stderr, never only to files inside the container.

---

### OOMKilled and exit code 137

> 📚 **Know this first:** 1) Note: [Memory reference](04-memory.md) (OOM killer, cgroups) · 2) Note: [Learn Docker](30-learn-docker.md) (resource limits, OOM) · 3) KodeKloud: *Docker Certified Associate* — Docker Engine – Security: resource limits and cgroups ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)).

**Level:** [L2 · Mid] — reading cgroup limits and telling a leak from a spike takes Mid-level judgement.

**Symptom:** `Exited (137)`, a container that dies under load, or a process
that vanishes without any error in its own log.

#### Step 1 — Confirm it was the OOM killer

**Goal:** prove whether the kernel killed it, and whether it was the container's limit or the whole host.

```bash
docker inspect -f 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} finished={{.State.FinishedAt}}' CONTAINER
sudo journalctl -k --since '2 hours ago' --no-pager | grep -iE 'out of memory|oom-kill|killed process'
```

```
exit=137 oom=true finished=2026-10-03T09:41:17.552Z

Oct 03 09:41:17 web01 kernel: oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=docker-4be1c0d9e8f7.scope,mems_allowed=0,oom_memcg=/system.slice/docker-4be1c0d9e8f7.scope,task_memcg=/system.slice/docker-4be1c0d9e8f7.scope,task=java,pid=48211,uid=1000
Oct 03 09:41:17 web01 kernel: Memory cgroup out of memory: Killed process 48211 (java) total-vm:4815232kB, anon-rss:1046528kB, file-rss:20480kB, shmem-rss:0kB, UID:1000 pgtables:2788kB oom_score_adj:0
```

**What it means:**

- `oom=true` plus `Memory cgroup out of memory` and `constraint=CONSTRAINT_MEMCG`: the container hit **its own** memory limit (`-m`, `mem_limit`, `deploy.resources.limits.memory`).
- `constraint=CONSTRAINT_NONE` and `Out of memory: Killed process`: the **whole host** ran out of memory and the kernel picked a victim. That is a host problem → [Memory](04-memory.md) and the [slow system playbook](23-playbook-slow-system.md).
- `exit=137 oom=false`: not the OOM killer. Something sent SIGKILL (stop timeout, `docker kill`) → Step 5 of the previous scenario.

**Why this step (now):** "137" is often read as "out of memory", but it only
means SIGKILL. Raising a memory limit for a container that was killed by a stop
timeout fixes nothing.

**Next step:** If container limit → Step 2. If host-wide OOM → fix host memory
first (other containers without limits?). If not OOM → previous scenario, Step 5.

#### Step 2 — Compare usage with the limit

**Goal:** see how close to the limit the container lives and how often it hits it.

```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}'
docker inspect -f 'limit={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}}' CONTAINER
docker service inspect -f '{{json .Spec.TaskTemplate.Resources}}' SERVICE    # Swarm / Dokploy

# cgroup v2 (Ubuntu 22.04+, systemd cgroup driver): the kernel's own counters
CID=$(docker inspect -f '{{.Id}}' CONTAINER)
CG=/sys/fs/cgroup/system.slice/docker-$CID.scope
cat $CG/memory.max $CG/memory.current
cat $CG/memory.peak 2>/dev/null          # kernel 5.19+ (Ubuntu 24.04, 22.04 HWE)
cat $CG/memory.events
```

```
NAME       MEM USAGE / LIMIT   MEM %    CPU %
shop-api   1019MiB / 1GiB      99.51%   142.10%

limit=1073741824 swap=2147483648
{"Limits":{"MemoryBytes":1073741824},"Reservations":{}}
1073741824
1068429312
1073741824
low 0
high 0
max 2481
oom 3
oom_kill 3
oom_group_kill 0
```

**What it means:** the API lives at 99.5% of its 1 GiB limit. `max 2481` = the
kernel had to squeeze it 2481 times (reclaiming cache, which makes the app slow
long before it dies), `oom_kill 3` = it killed a process three times.
`swap=2147483648` means memory plus swap may total 2 GiB: if the host has swap,
the container swaps first, which is slow but alive.

**Why this step (now):** you need numbers before choosing between "raise the
limit" and "fix the app". The cgroup files are the kernel's truth; `docker stats`
is a friendly view of the same data.

**Next step:** → Step 3 to decide leak, spike or misconfigured runtime.

#### Step 3 — Decide: leak, spike or wrong runtime settings

**Goal:** find out why the app needs more memory than it is given.

```bash
# How many CPUs and how much memory does the app think it has?
docker exec CONTAINER sh -c 'nproc; cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max'

# Per-process memory inside the container (RSS in KB)
docker top CONTAINER -eo pid,rss,args

# Watch the trend for a few minutes: steady climb = leak, sudden jump = spike
while sleep 30; do printf '%s ' "$(date +%T)"; docker stats --no-stream --format '{{.MemUsage}}' CONTAINER; done
```

```
32
200000 100000
1073741824

PID     RSS      COMMAND
48190   61240    /usr/local/bin/python /usr/local/bin/gunicorn app:app --workers 65 --bind 0.0.0.0:8000
48201   15912    /usr/local/bin/python /usr/local/bin/gunicorn app:app --workers 65 --bind 0.0.0.0:8000
...
```

**What it means:** `nproc` says 32 because the container sees all host CPUs
(`cpu.max 200000 100000` is a 2-CPU quota, but `nproc` ignores quotas). The
app's Gunicorn config computes workers with the common "2 × cores + 1" formula
(Gunicorn itself defaults to 1 worker), so it started 65 workers in 1 GiB. The same trap
exists for JVMs (old versions size the heap from host RAM) and Node.js (default
heap ceiling unrelated to the limit).

| Pattern | Typical cause | Fix |
|---|---|---|
| climbs steadily for hours, then killed | memory leak | profile the app; a higher limit only delays it |
| jumps on one request type | big export, image resize, unbounded query | fix the code path, or a dedicated worker with a higher limit |
| high from the first second | runtime sized for the host, not the container | set workers / heap explicitly |

**Why this step (now):** raising limits blindly turns one OOM per hour into one
per day and hides a leak until it takes the host down.

**Next step:** apply the matching fix below, then verify.

#### Decision tree: exit code 137

```
exit 137
├── OOMKilled=false ........ SIGKILL from outside → docker events (stop timeout? kill?)
└── OOMKilled=true
    ├── CONSTRAINT_NONE ..... host out of memory → host memory playbook, set limits everywhere
    └── CONSTRAINT_MEMCG .... container limit
        ├── high from start → tune workers / heap to the limit
        ├── steady climb ...→ leak → fix app (temporary: higher limit + scheduled restart)
        └── spikes .........→ fix the heavy path or give it its own worker
```

**Fix & verify**

```bash
# Tune the runtime to the limit, for example:
#   gunicorn --workers 3            JVM: -XX:MaxRAMPercentage=75     Node: --max-old-space-size=768
# Change a limit live (standalone/Compose container; not persistent across recreate):
docker update --memory 1536m --memory-swap 1536m CONTAINER
# Swarm / Dokploy: change the service spec (Dokploy: app → Advanced → Resources), then redeploy
docker service update --limit-memory 1536M SERVICE
# Verify: oom_kill stops increasing, usage plateaus below ~80% of the limit
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' CONTAINER).scope/memory.events | grep oom_kill
```

**Rollback:** set the previous limit and runtime flags again (`docker update`,
or revert the Compose/service change and redeploy).

**Prevent it next time**

- Give every container a memory limit, so one leak cannot trigger a host-wide OOM that kills a neighbour.
- Set worker counts and heap sizes explicitly in the image or env, never from auto-detection.
- Alert when a container stays above 85% of its limit (cAdvisor or node_exporter metrics, see [performance & observability](32-learn-performance-observability.md)).
- Load-test with the production limits, not on a laptop without limits.

---

### Docker daemon will not start

> 📚 **Know this first:** 1) KodeKloud: *Docker Certified Associate* — Troubleshooting Docker Daemon, Demo – Docker Debug Mode ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page)) · 2) Note: [Services & systemd](07-services-systemd.md) · 3) Note: [Logs & journal](06-logs-journal.md).

**Level:** [L2 · Mid] — journalctl and JSON skills from L1, plus enough Docker internals to read the error.

**Symptom:** `Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?`, usually right after an edit of
`/etc/docker/daemon.json`, an upgrade or a reboot.

#### Step 1 — Read the unit status and the daemon's last words

**Goal:** get the exact error dockerd printed before it died.

```bash
systemctl status docker --no-pager -l
sudo journalctl -u docker -b --no-pager -n 40
```

```
× docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: failed (Result: exit-code) since Fri 2026-10-03 10:02:41 UTC; 8s ago
TriggeredBy: × docker.socket
       Docs: https://docs.docker.com
    Process: 51207 ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock (code=exited, status=1/FAILURE)
   Main PID: 51207 (code=exited, status=1/FAILURE)

Oct 03 10:02:41 web01 dockerd[51207]: unable to configure the Docker daemon with file /etc/docker/daemon.json: invalid character '}' looking for beginning of object key string
Oct 03 10:02:41 web01 systemd[1]: docker.service: Main process exited, code=exited, status=1/FAILURE
Oct 03 10:02:41 web01 systemd[1]: docker.service: Failed with result 'exit-code'.
```

**What it means:** a JSON syntax error (here a trailing comma before `}`). The
most common daemon start failures:

| Log line | Cause | Fix |
|---|---|---|
| `invalid character ... looking for beginning of object key string` | trailing comma, missing quote, a comment in JSON | Step 2 |
| `the following directives are specified both as a flag and in the configuration file: hosts` | `"hosts"` in daemon.json conflicts with `-H fd://` in the unit | remove it, or a systemd drop-in that resets `ExecStart=` |
| `--live-restore daemon configuration is incompatible with swarm mode` | `live-restore` on a Swarm (Dokploy) node | remove `live-restore` |
| `failed to dial "/run/containerd/containerd.sock"` | containerd is not running | Step 3 |
| `error initializing graphdriver`, `no space left on device` | disk full, or data-root on a disk that did not mount | Step 3 |
| `failed to create NAT chain DOCKER: iptables failed` | iptables backend or kernel module problem | Step 3 |
| `pid file found, ensure docker is not running` | a second dockerd is running, or a stale pid file | `pgrep -a dockerd` |
| `start request repeated too quickly` | systemd gave up after several failures | fix the cause, then `systemctl reset-failed docker` |

**Why this step (now):** the daemon nearly always says exactly why it refused to
start, and the journal keeps that line even though the process is gone.

**Next step:** If the error names daemon.json → Step 2. If containerd, disk or
iptables → Step 3. If the journal is empty or unclear → Step 4.

#### Step 2 — Validate daemon.json before restarting

**Goal:** prove the file is valid JSON and valid configuration before you try again.

```bash
sudo python3 -m json.tool /etc/docker/daemon.json >/dev/null && echo "JSON syntax OK"
sudo dockerd --validate --config-file /etc/docker/daemon.json     # Docker 23+
```

```
Expecting property name enclosed in double quotes: line 6 column 1 (char 112)

configuration OK
```

**What it means:** the first line points to line 6 of the file; after you fix it,
`dockerd --validate` checks option names and values as well as syntax and prints
`configuration OK`. A known-good daemon.json for the stack in this handbook:

```json
{
  "dns": ["192.0.2.53", "192.0.2.54"],
  "log-driver": "json-file",
  "log-opts": { "max-size": "20m", "max-file": "5" },
  "bip": "10.209.0.1/24",
  "default-address-pools": [ { "base": "10.210.0.0/16", "size": 24 } ]
}
```

**Why this step (now):** restarting a daemon with a broken file just fails
again and adds to systemd's start-limit counter. Validation is instant and safe.

**Next step:** If it validates → `sudo systemctl reset-failed docker && sudo systemctl start docker`
and go to "Fix & verify". If it still fails with a different error → Step 3.

#### Step 3 — Check containerd, disk, data-root and firewall

**Goal:** rule out the things dockerd depends on.

```bash
systemctl is-active containerd ; sudo journalctl -u containerd -b -n 20 --no-pager
df -h /var/lib/docker ; df -i /var/lib/docker
findmnt /var/lib/docker                    # a separate data disk that did not mount?
grep -s data-root /etc/docker/daemon.json
sudo iptables -V                           # "nf_tables" or "legacy"
sudo update-alternatives --display iptables | head -3
```

```
active
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   98G     0 100% /
iptables v1.8.10 (nf_tables)
```

**What it means:** the root filesystem is 100% full, so dockerd cannot write its
state. Free space first ([Docker filled the disk](26-playbook-containers-k8s.md)
in section 5, and [Storage](01-storage-disk.md)), then start Docker. If
`findmnt` prints nothing while daemon.json sets a `data-root` on another disk,
dockerd may have started on an empty directory: images and volumes "vanished".
Mount the disk (check `/etc/fstab`) before starting Docker.

**Why this step (now):** these are the three external dependencies that most
often break after a reboot or an upgrade, and each one is a single read-only check.

**Next step:** If all are fine and dockerd still fails → Step 4.

#### Step 4 — Run the daemon in the foreground

**Goal:** see every line dockerd prints, live, when the journal is not enough.

```bash
sudo systemctl stop docker.socket docker
sudo dockerd --debug 2>&1 | head -80        # wait for the error, then Ctrl-C
sudo systemctl start docker                 # back under systemd when you are done
```

```
time="2026-10-03T11:02:14.121534822Z" level=info msg="Starting up"
time="2026-10-03T11:02:14.122101345Z" level=debug msg="Listener created for HTTP on unix (/var/run/docker.sock)"
time="2026-10-03T11:02:14.140220187Z" level=info msg="[graphdriver] trying configured driver: overlay2"
time="2026-10-03T11:02:14.152884410Z" level=debug msg="Initialized graph driver overlay2"
time="2026-10-03T11:02:14.310402556Z" level=info msg="Loading containers: start."
time="2026-10-03T11:02:14.402771093Z" level=debug msg="/usr/sbin/iptables, [--wait -t nat -N DOCKER]"
failed to start daemon: Error initializing network controller: error obtaining controller instance:
failed to register "bridge" driver: unable to add return rule in DOCKER-ISOLATION-STAGE-1 chain:
(iptables failed: iptables --wait -A DOCKER-ISOLATION-STAGE-1 -j RETURN: iptables v1.8.10 (nf_tables):
RULE_APPEND failed (No such file or directory): rule in chain DOCKER-ISOLATION-STAGE-1 (exit status 4))
```

**What it means:** debug mode prints each initialization step (config, storage
driver, networks, iptables, containerd) and stops at the failing one. Read the
**last** lines: here storage came up fine and the network controller failed
while adding Docker's firewall rules. "RULE_APPEND failed (No such file or
directory)" usually means the running kernel cannot load the netfilter modules
the iptables-nft backend needs, typically after a kernel upgrade without a
reboot (the modules on disk belong to the new kernel). Reboot into the new
kernel, or check the firewall backend as in Step 3.

**Why this step (now):** last, because it bypasses systemd and briefly runs a
second way of starting Docker on a production host. Never leave it running.

**Next step:** fix what it names, then start the service normally.

#### Decision tree: daemon will not start

```
systemctl status docker + journalctl -u docker -b
├── daemon.json error ....... json.tool + dockerd --validate → fix → reset-failed → start
├── hosts / live-restore .... remove the conflicting option (live-restore is not allowed with Swarm)
├── containerd ............. systemctl status containerd → fix it first
├── no space / graphdriver .. df -h, findmnt data-root → free space or mount the disk
├── iptables ............... iptables -V, modules, backend
└── unclear ................. dockerd --debug in the foreground
```

**Fix & verify**

```bash
sudo systemctl reset-failed docker
sudo systemctl start docker
docker info --format '{{.ServerVersion}} {{.Driver}} swarm={{.Swarm.LocalNodeState}}'
docker ps --format '{{.Names}}\t{{.Status}}' | head      # restart policies bring containers back
docker service ls                                        # Swarm services converge again
```

**Rollback:** before every edit run `sudo cp -a /etc/docker/daemon.json /etc/docker/daemon.json.$(date +%F)`.
To roll back, copy that file over daemon.json and start Docker.

**Prevent it next time**

- Treat daemon.json as code: keep it in Git, deploy it with Ansible, and run `dockerd --validate` in the pipeline.
- Edit procedure: backup → edit → validate → restart in a maintenance window. A daemon restart restarts every container, and on a Swarm/Dokploy host `live-restore` cannot soften that.
- Monitor failed units (node_exporter systemd collector), so a dead daemon pages you before users do.

---

## 3. Docker: ports, host and firewall

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine: Publishing Ports ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure Packet Filtering (Firewall), then Port Redirection and NAT ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 3) Note: [Who owns this port?](22-playbook-ports-inventory.md) · 4) Read: [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) (KodeKloud does not cover DOCKER-USER) · 5) Video: *How Docker Networking Actually Works* ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 6) Practice: replay the [Apache/Dokploy case](21-case-apache-443-dokploy.md) on the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) and prove from a second machine which ports are really open.

### Port already allocated or address in use

> 📚 **Know this first:** 1) Note: [Who owns this port?](22-playbook-ports-inventory.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Start, Stop, and Check Status of Network Services ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) KodeKloud: *Docker Certified Associate* — Publishing Ports ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)).

**Level:** [L1 · Junior] — the Ops Ladder L1 exit test (port → process → unit) applied to Docker.

**Symptom:** a container or Dokploy's Traefik refuses to start because a port
is taken. This is the exact failure from the Apache → Dokploy migration: Apache
held 443 while Traefik needed 80 and 443. The full migration story is in the
[Apache 443 / Dokploy case study](21-case-apache-443-dokploy.md); how to
inventory every port, app and log on a host is in
[Who owns this port?](22-playbook-ports-inventory.md). This scenario is the
fast incident path.

#### Step 1 — Read which of the two errors you got

**Goal:** know whether a container or a host process is in the way. The error text tells you.

```bash
# Re-run the failing start and keep the full error
docker compose up -d 2>&1 | tail -3
docker start CONTAINER 2>&1 | tail -3
```

```
Error response from daemon: driver failed programming external connectivity on endpoint web (3f2a9c1d7e8b...): Bind for 0.0.0.0:80 failed: port is already allocated

Error response from daemon: driver failed programming external connectivity on endpoint dokploy-traefik (8c1d5e7f9a0b...): Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use
```

**What it means:**

- `port is already allocated` comes from Docker's own port allocator: **another container** already publishes that host port.
- `bind: address already in use` comes from the kernel: **a non-Docker process** (Apache, nginx, a systemd socket, a forgotten `python -m http.server`) is listening there.

Newer Docker versions prefix the message with `failed to set up container networking:`; the last part is what matters.

**Why this step (now):** the two messages send you to two different tools.
Reading the error carefully saves you from hunting through `ss` output for a
container, or through `docker ps` for Apache.

**Next step:** If `already allocated` → Step 2. If `address already in use` → Step 3.

#### Step 2 — Find the container that publishes the port

**Goal:** name the container or Swarm service that owns the host port.

```bash
docker ps --filter publish=80 --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker service ls --format '{{.Name}}  {{.Ports}}' | grep -E ':(80|443)->'
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E ':(80|443)->'
```

```
NAMES       STATUS        PORTS
old-nginx   Up 3 weeks    0.0.0.0:80->80/tcp, [::]:80->80/tcp
```

**What it means:** a three-week-old `old-nginx` container holds port 80. Before
you stop it, find out what it serves and whether anyone still needs it: its
labels, its Compose project, its logs (`docker logs --since 24h old-nginx | tail`).
The inventory method is in [Who owns this port?](22-playbook-ports-inventory.md).

**Why this step (now):** the allocator only tracks Docker's own publications, so
Docker's tools find the owner directly.

**Next step:** If it is no longer needed → stop it (`docker stop old-nginx`, keep
the container for a week before removing it). If it is needed → publish your new
container on a different host port, or better, put both behind Traefik with no
host ports at all. If no container shows the port → Step 4.

#### Step 3 — Find the host process that holds the port

**Goal:** name the process, its systemd unit and its config, so you can move it on purpose instead of killing it.

```bash
sudo ss -ltnp 'sport = :443'                       # who listens on 443
sudo lsof -nP -iTCP:443 -sTCP:LISTEN               # same, another angle
systemctl status 1123 --no-pager | head -5         # which unit owns PID 1123
systemctl list-sockets | grep -E ':(80|443)\b'     # a systemd socket holding it?
sudo apache2ctl -S 2>/dev/null | head -20          # if it is Apache: which vhosts (RHEL: httpd -S)
```

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       511                 *:443              *:*      users:(("apache2",pid=1131,fd=6),("apache2",pid=1130,fd=6),("apache2",pid=1123,fd=6))

● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-28 07:12:44 UTC; 5 days ago

VirtualHost configuration:
*:443                  is a NameVirtualHost
         default server crm.example.com (/etc/apache2/sites-enabled/crm-ssl.conf:2)
         port 443 namevhost crm.example.com (/etc/apache2/sites-enabled/crm-ssl.conf:2)
         port 443 namevhost wiki.example.com (/etc/apache2/sites-enabled/wiki-ssl.conf:2)
*:80                   is a NameVirtualHost
         default server crm.example.com (/etc/apache2/sites-enabled/crm.conf:1)
```

**What it means:** `apache2` (Send-Q 511 is Apache's default listen backlog)
listens on `*:443`, all addresses, IPv4 and IPv6. PID 1123 belongs to
`apache2.service`, and `apache2ctl -S` lists the vhosts it serves. You now know
what you would break by stopping it: `crm` and `wiki`.

**Why this step (now):** stopping an unknown listener is how a port conflict
becomes an outage of three other applications. Naming the unit and its vhosts
turns "kill it" into a decision you can explain to the client.

**Next step:** choose one of these, and agree it with the app owners:

| Option | When | How |
|---|---|---|
| Move Apache behind Traefik | the Apache apps must keep running | Apache `Listen 127.0.0.1:8080`, Traefik file-provider route per vhost (see [case study](21-case-apache-443-dokploy.md)) |
| Stop and disable Apache | its apps are migrated or retired | `sudo systemctl disable --now apache2`, keep the config for rollback |
| Give the new app another port | temporary test only | publish on `127.0.0.1:HOSTPORT`, not on 443 |

#### Step 4 — Handle a stale allocation

**Goal:** deal with the rare case where Docker says "allocated" but nothing owns the port.

```bash
docker ps -a --format '{{.Names}} {{.Ports}}' | grep ':80->'   # nothing?
ps -ef | grep '[d]ocker-proxy' | grep -E -- '-host-port 80( |$)' # an orphaned proxy process? (not 8080)
sudo ss -ltnp 'sport = :80'
```

```
(docker ps prints nothing: no container publishes :80)
root     48211       1  0 Sep30 ?        00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 80 -container-ip 172.17.0.4 -container-port 80
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:80        0.0.0.0:*     users:(("docker-proxy",pid=48211,fd=4))
```

**What it means:** an orphaned `docker-proxy` or a stale allocator entry after a
daemon crash. A daemon restart rebuilds the allocator. In this sample the
proxy's parent PID is `1` (a healthy docker-proxy is a child of dockerd), and it
forwards to `172.17.0.4`, an address no running container has: it is left over
from before a crash. If `ss` shows nothing at all on :80 and Docker still says
"allocated", it is the allocator entry alone.

**Why this step (now):** only after both normal owners are ruled out, because
the fix (daemon restart) restarts every container on the host.

**Next step:** schedule `sudo systemctl restart docker` in a maintenance window,
then start the container again.

#### Decision tree: port conflict

```
error text
├── "port is already allocated" → docker ps --filter publish=PORT / docker service ls
│   ├── found → still needed? yes: move it behind Traefik · no: stop it (keep it a week)
│   └── none  → orphaned docker-proxy? → daemon restart in a window
└── "address already in use" → ss -ltnp 'sport = :PORT' → systemctl status PID
    ├── Apache/nginx → apache2ctl -S → move behind Traefik on 127.0.0.1:8080, or disable
    ├── systemd socket unit → systemctl stop/disable UNIT.socket
    └── stray process → find its owner before stopping it
```

**Fix & verify**

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 )'      # now docker-proxy (or dockerd for Swarm ingress ports)
curl -sI http://127.0.0.1/ -H 'Host: app.example.com' | head -3
curl -sI --resolve app.example.com:443:127.0.0.1 https://app.example.com/ | head -3
```

**Rollback:** stop the new container (`docker stop dokploy-traefik`), then start
the old owner again (`sudo systemctl start apache2`) and check it with
`sudo ss -ltnp 'sport = :443'`. Rehearse this before the change window.

**Prevent it next time**

- One owner for 80/443 per host (Traefik); applications never publish host ports, they join the proxy network.
- Keep a port inventory per host in Git, refreshed by a script (`ss -ltnp` plus `docker ps`); see [Who owns this port?](22-playbook-ports-inventory.md).
- Add a pre-flight `ss -ltnp 'sport = :PORT'` to every deployment runbook.

---

### Container cannot reach a service on the host

> 📚 **Know this first:** 1) Note: [Learn networking](28-learn-networking.md) (bind addresses, NAT) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page)) · 3) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)).

**Level:** [L2 · Mid] — bind addresses, bridge gateways and host firewalls in one walk.

**Symptom:** the app in a container cannot connect to something running on the
host itself: PostgreSQL or MySQL installed with apt, a legacy API, an SMTP relay.
Errors: `Connection refused`, `could not translate host name "host.docker.internal"`,
or a timeout.

#### Step 1 — Reproduce from inside the container

**Goal:** test the exact name and port the app uses, from the container's network namespace.

```bash
# Does the name resolve inside the container?
docker exec CONTAINER getent hosts host.docker.internal

# Can we open the port? (netshoot shares the container's network namespace)
docker run --rm --net container:CONTAINER nicolaka/netshoot nc -vz -w3 host.docker.internal 5432
```

```
(empty: getent printed nothing)

nc: getaddrinfo for host "host.docker.internal" port 5432: Name does not resolve
```

or, once the name resolves:

```
172.17.0.1      host.docker.internal
nc: connect to host.docker.internal (172.17.0.1) port 5432 (tcp) failed: Connection refused
```

**What it means:**

- **Name does not resolve:** on Linux, `host.docker.internal` does not exist unless you add it: `--add-host=host.docker.internal:host-gateway` or, in Compose, `extra_hosts: ["host.docker.internal:host-gateway"]`. `host-gateway` resolves to the docker0 bridge address (172.17.0.1 by default), which is the host.
- **Connection refused:** the packet reached the host and nothing listens on that address → Step 2.
- **Timeout** (`timed out: Operation in progress` from netshoot's musl `nc`; glibc tools say `Operation now in progress`): something drops the packet → Step 3.

**Why this step (now):** testing from the host (`psql -h localhost`) proves
nothing about the container's path. Netshoot gives you `nc`, `dig` and `tcpdump`
even when the app image has no tools.

**Next step:** If the name is missing → add `host-gateway` and recreate the
container. If refused → Step 2. If timeout → Step 3.

#### Step 2 — Check which address the host service listens on

**Goal:** see whether the host service accepts connections from the bridge at all.

```bash
sudo ss -ltnp 'sport = :5432'
docker network inspect bridge -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}'      # docker0, e.g. 172.17.0.1
docker inspect -f '{{range $n, $c := .NetworkSettings.Networks}}{{$n}} gw={{$c.Gateway}} ip={{$c.IPAddress}}{{println}}{{end}}' CONTAINER
```

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       244         127.0.0.1:5432       0.0.0.0:*      users:(("postgres",pid=912,fd=6))

172.17.0.1
shop_default gw=172.18.0.1 ip=172.18.0.5
```

**What it means:** PostgreSQL listens on `127.0.0.1` only. Inside a container,
`127.0.0.1` is the **container's own** loopback, never the host's, and the
host's loopback does not accept packets that arrive on a bridge. That is the
single most common cause of this incident. The container sits on `shop_default`
(172.18.0.0/16), so its packets arrive at the host from 172.18.0.5.

**Why this step (now):** "refused" means the host answered; the listening
address is the first thing that decides whether it answers with data or with a reset.

**Next step:** make the service listen on the bridge address as well, and allow
the container subnet in its own access rules. For PostgreSQL:

```bash
# postgresql.conf (Ubuntu: /etc/postgresql/16/main/postgresql.conf)
#   listen_addresses = 'localhost,172.17.0.1'
# pg_hba.conf: allow the container subnet only
#   host  shopdb  shop  172.18.0.0/16  scram-sha-256
sudo systemctl restart postgresql
```

Then re-test from Step 1. If it now times out → Step 3.

PostgreSQL can bind 172.17.0.1 only if docker0 already exists when it starts.
After a reboot it may start before Docker, log `could not bind IPv4 address
"172.17.0.1": Cannot assign requested address`, and keep running on localhost
only, so the container is refused again. Order the units (a systemd drop-in
with `After=docker.service`) or listen on the host's LAN address instead.

#### Step 3 — Check the host firewall

**Goal:** prove whether UFW (or nftables) drops the packets coming from the bridge.

```bash
sudo ufw status verbose | head -8
sudo journalctl -k --since '10 min ago' --no-pager | grep 'UFW BLOCK' | grep 'DPT=5432' | tail -3
sudo tcpdump -ni any 'tcp port 5432' -c 6          # SYNs arriving? any answer?
```

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)

Oct 03 10:31:07 web01 kernel: [UFW BLOCK] IN=br-3f2a9c1d7e8b OUT= MAC=02:42:... SRC=172.18.0.5 DST=172.17.0.1 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=40121 DF PROTO=TCP SPT=41822 DPT=5432 WINDOW=64240 RES=0x00 SYN URGP=0

10:31:07.112 br-3f2a9c1d7e8b In  IP 172.18.0.5.41822 > 172.17.0.1.5432: Flags [S], seq 2120385001, win 64240, length 0
10:31:08.140 br-3f2a9c1d7e8b In  IP 172.18.0.5.41822 > 172.17.0.1.5432: Flags [S], seq 2120385001, win 64240, length 0
```

**What it means:** traffic from a container to the **host itself** goes through
the INPUT chain, so UFW's default `deny (incoming)` applies (the opposite of
published ports, which skip UFW: next scenario). The SYN arrives on
`br-3f2a9c1d7e8b` and is retransmitted with no answer: a firewall drop.

**Why this step (now):** a timeout means "silently dropped". The UFW log line and
the capture show the drop directly instead of making you infer it.

**Next step:** allow exactly this flow, from the container subnet to the one port:

```bash
sudo ufw allow in on br-3f2a9c1d7e8b from 172.18.0.0/16 to any port 5432 proto tcp comment 'shop containers -> host postgres'
```

The `br-...` name changes if the network is recreated. Give the bridge a stable
name when you create it (`docker network create -o com.docker.network.bridge.name=br-shop shop`)
or allow by subnet only.

#### Step 4 — Swarm and Dokploy services

**Goal:** apply the same idea to services on overlay networks.

Swarm tasks (Dokploy applications) leave the node through `docker_gwbridge`,
not docker0. The most robust target is the host's own LAN address (for example
`192.0.2.10`), with the service listening there and UFW allowing the
`docker_gwbridge` subnet:

```bash
docker network inspect docker_gwbridge -f '{{range .IPAM.Config}}{{.Subnet}} gw={{.Gateway}}{{end}}'
```

```
172.19.0.0/16 gw=172.19.0.1
```

**What it means:** tasks on this node reach the outside (and the host) from
`172.19.0.0/16`, not from docker0's `172.17.0.0/16`, so a UFW rule written for
docker0 never matches them. Allow that subnet to the service port, for example
`sudo ufw allow in on docker_gwbridge from 172.19.0.0/16 to 192.0.2.10 port 5432 proto tcp`,
and point the app at `192.0.2.10:5432`. Do not rely on the `host-gateway`
shortcut for Swarm services: it is resolved per container by the local daemon
and is not dependable in stacks, so use the host's LAN IP.

**Why this step (now):** the bridge-network fixes above do not apply to overlay
networks, and Dokploy apps are Swarm services.

**Next step:** better still, stop depending on the host: run the dependency as
a container on the same network, or on a separate database server with normal
firewall rules.

#### Decision tree: container to host

```
from inside the container (netshoot): nc -vz host.docker.internal PORT
├── name does not resolve → extra_hosts: host.docker.internal:host-gateway (Swarm: use host LAN IP)
├── refused → ss -ltnp on host: bound to 127.0.0.1? → listen on bridge IP + app ACL (pg_hba)
└── timeout → UFW BLOCK in kernel log / tcpdump shows SYN only → ufw allow in on br-X from SUBNET
```

**Fix & verify:** from inside the container, `nc -vz -w3 host.docker.internal 5432`
prints `succeeded`/`open`, and the app's own health check passes.

**Rollback:** `sudo ufw status numbered`, then `sudo ufw delete N` for the rule
you added; restore `listen_addresses` and restart the service.

**Prevent it next time:** document every container → host dependency in the app's
README, prefer containerized or remote dependencies, and never "fix" this with
`network_mode: host` on a multi-app server (it removes network isolation and
brings back port conflicts).

---

### Published ports bypass UFW

> 📚 **Know this first:** 1) Read: [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Port Redirection and NAT ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 3) KodeKloud: *Certified Kubernetes Security Specialist (CKS)* — UFW Firewall Basics ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)).

**Level:** [L2 · Mid] — you need the netfilter packet path, not just UFW commands.

**Symptom:** `sudo ufw status` does not allow port 8080 (or Dokploy's 3000), yet
it is reachable from the internet. Or a security scan reports a database port
you never opened.

#### Step 1 — Prove the exposure from outside

**Goal:** see what the world sees. Testing from the host itself proves nothing.

```bash
# From ANOTHER machine (your laptop, a VM in another network):
nc -vz -w3 203.0.113.10 8080
nc -vz -w3 203.0.113.10 3000

# On the server: what is published, and on which address?
docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep -E '0\.0\.0\.0|\[::\]'
sudo ufw status | grep -E '8080|3000' || echo "no UFW rule for 8080/3000"
```

```
Connection to 203.0.113.10 8080 port [tcp/http-alt] succeeded!
Connection to 203.0.113.10 3000 port [tcp/*] succeeded!

grafana   0.0.0.0:8080->3000/tcp, [::]:8080->3000/tcp
dokploy.1.p9c7d6e5f4a3b2c1d0e9f8g7   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
no UFW rule for 8080/3000
```

**What it means:** both ports are open to the world although UFW has no rule
for them. `0.0.0.0` and `[::]` mean "every address, IPv4 and IPv6".

**Why this step (now):** you need a test that reproduces the risk from the
attacker's position, and that you can repeat after the fix.

**Next step:** → Step 2 to see why UFW never saw the packet.

#### Step 2 — See the NAT rule that skips UFW

**Goal:** understand the packet path so you put the filter in the right place.

```bash
sudo iptables -t nat -L DOCKER -n --line-numbers | head
sudo iptables -L FORWARD -n --line-numbers | head -8
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
Chain DOCKER (2 references)
num  target     prot opt source       destination
1    RETURN     all  --  0.0.0.0/0    0.0.0.0/0
2    DNAT       tcp  --  0.0.0.0/0    0.0.0.0/0    tcp dpt:8080 to:172.18.0.7:3000

Chain FORWARD (policy DROP)
num  target                prot opt source      destination
1    DOCKER-USER           all  --  0.0.0.0/0   0.0.0.0/0
2    DOCKER-FORWARD        all  --  0.0.0.0/0   0.0.0.0/0
3    ufw-before-logging-forward  all  --  0.0.0.0/0   0.0.0.0/0
...

Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source       destination
1     812K  95M RETURN     all  --  *      *       0.0.0.0/0    0.0.0.0/0
```

**What it means:** the packet for :8080 is rewritten (DNAT) to 172.18.0.7:3000
in PREROUTING, **before** filtering. Its destination is now a container, so it
is routed through the FORWARD chain, not INPUT. UFW's rules for incoming traffic
live in INPUT and are never consulted. In FORWARD, Docker's chains come first;
`DOCKER-USER` is the one chain Docker leaves for you, evaluated before its own
accept rules. (Docker 28 and newer show `DOCKER-FORWARD`; older versions jump to
`DOCKER-ISOLATION-STAGE-1` and `DOCKER` directly; a Swarm host also has
`DOCKER-INGRESS`. Docker 28.2.2 and newer no longer add the final `RETURN` rule,
so an empty `DOCKER-USER` chain is normal there. On Ubuntu 22.04+ these are
nftables rules shown through `iptables-nft`.)

**Why this step (now):** without this picture, people add more UFW rules, see no
effect, and conclude the firewall is broken.

**Next step:** → Step 3 to pick the fix.

#### Step 3 — Pick the right fix

**Goal:** close the exposure with the least moving parts.

**Fix A: the port should not be public at all (most cases).** Bind it to
loopback, or do not publish it and let Traefik reach it over `dokploy-network`:

```yaml
# compose.yaml
services:
  grafana:
    ports:
      - "127.0.0.1:8080:3000"     # reachable from the host only (ssh -L for you)
```

**Fix B: public, but only from certain sources.** Filter in DOCKER-USER, matching
the **original** destination port (after DNAT the port is the container's):

```bash
# Allow the office range to reach published port 3000 (Dokploy panel); drop everyone else
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL ! -s 198.51.100.0/24 -j DROP
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1        0     0 DROP       tcp  --  ens18  *      !198.51.100.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
2     812K   95M RETURN     all  --  *      *       0.0.0.0/0            0.0.0.0/0
```

**What it means:** with Fix A, `docker ps` shows `127.0.0.1:8080->3000/tcp`
instead of `0.0.0.0:8080`, and there is nothing left to filter. With Fix B, your
DROP rule sits at the top of DOCKER-USER, **above** the final RETURN if your
version still adds one (rules are read top to bottom), it
matches only new connections from outside the office range to the original port
3000, and its packet counter (0 now) must grow when an outsider tries.

Rules added with `iptables -I` vanish on reboot (a Docker restart leaves
DOCKER-USER alone). To persist them with UFW, add a block at the end of
`/etc/ufw/after.rules` and reload UFW:

```
*filter
:DOCKER-USER - [0:0]
-A DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL ! -s 198.51.100.0/24 -j DROP
-A DOCKER-USER -j RETURN
COMMIT
```

> ⚠️ Never put a broad `-j DROP` in DOCKER-USER without `--ctorigdstport` or a
> conntrack state match: it also drops the reply packets of your containers'
> outbound connections, so every container loses internet and DNS. Never
> "reset" the firewall with `iptables -F` on a Docker host: it deletes Docker's
> own rules too. If you have switched Docker to its nftables firewall backend
> (experimental in recent Engine releases), there is no DOCKER-USER chain:
> follow the [packet filtering docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
> Repeat the rule with `ip6tables` if the host has public IPv6.

**Why this step (now):** Fix A removes the exposure; Fix B only narrows it. Prefer
A, use B for things like the Dokploy panel that must stay reachable for admins.

**Next step:** → Step 4.

#### Step 4 — Verify from outside again

**Goal:** prove the fix with the same outside test that proved the exposure.

```bash
# From the outside machine (not in 198.51.100.0/24):
nc -vz -w3 203.0.113.10 3000      # expect: timed out
nc -vz -w3 203.0.113.10 8080      # expect: refused (nothing on 0.0.0.0:8080 any more)
# From an admin machine inside 198.51.100.0/24 (the panel must still work for you):
nc -vz -w3 203.0.113.10 3000      # expect: succeeded
# Back on the server: did the DROP rule actually match?
sudo iptables -L DOCKER-USER -n -v --line-numbers | sed -n 3p
```

```
nc: connect to 203.0.113.10 port 3000 (tcp) timed out: Operation now in progress
nc: connect to 203.0.113.10 port 8080 (tcp) failed: Connection refused

Connection to 203.0.113.10 3000 port [tcp/*] succeeded!

1        2   120 DROP       tcp  --  ens18  *      !198.51.100.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
```

**What it means:** 3000 times out from outside because DOCKER-USER silently
drops it (a drop sends no answer), and the counter went from 0 to 2 packets, so
your rule is the one that matched. 8080 is **refused** because nothing listens
on the public address any more (the kernel answers with a reset). The admin
range still reaches the panel, so you did not lock yourself out.

**Why this step (now):** `iptables -L` only proves the rule exists; the outside
test proves the packet path, and it is the same test you will repeat after every
deploy.

**Next step:** If both ports are closed as expected → "Fix & verify" below. If
3000 still connects → the rule names the wrong interface (`-i`) or matches the
container port instead of `--ctorigdstport`; back to Step 3. If the IPv4 test
passes but a scan over IPv6 still finds the port → add the same rule with
`ip6tables`.

#### Decision tree: unexpected exposure

```
reachable from outside but not allowed in UFW?
├── docker ps shows 0.0.0.0:HOSTPORT → published port (DNAT → FORWARD, UFW never sees it)
│   ├── should not be public → bind 127.0.0.1:HOSTPORT:PORT or remove the publication
│   └── public for some sources → DOCKER-USER rule with --ctorigdstport, persist in after.rules
└── not a container → ss -ltnp: a host process; UFW should apply → check ufw status / rule order
```

**Fix & verify:** an outside scan of the host lists only the ports you meant to
publish (80 and 443 for Traefik; 3000 only from the admin range), `docker ps`
shows `127.0.0.1:` in front of every other published port, and the DOCKER-USER
rule survives a reboot because it lives in `/etc/ufw/after.rules`.

**Rollback:** `sudo iptables -L DOCKER-USER -n --line-numbers`, then
`sudo iptables -D DOCKER-USER N` for the rule you added; remove the block from
after.rules and `sudo ufw reload`.

**Prevent it next time**

- Rule for the whole team: no `0.0.0.0` publications except Traefik's 80/443. Review Compose files for `ports:` in merge requests.
- After every deploy, scan the host from outside (`nmap -Pn -p- 203.0.113.10` from an allowed scanner) and compare with the expected list.
- Read [Docker docs: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) once, end to end.

---

### expose does not restrict anything

> 📚 **Know this first:** 1) Read: [Traefik docs: Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)) · 3) Note: [Learn Docker](30-learn-docker.md) (networking).

**Level:** [L2 · Mid] — a design-level misunderstanding that shows up as a security finding or a 502.

**Symptom:** you assumed only the `expose:`d port of a container is reachable
(it is not), or Traefik routes to the wrong port and you get a 502.

#### Step 1 — Prove what a neighbour can reach

**Goal:** see that every listening port is reachable on a shared network, exposed or not.

```bash
docker inspect -f '{{json .Config.ExposedPorts}}' CONTAINER
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltn
docker run --rm --network shop_default nicolaka/netshoot nc -vz -w2 api 9090
```

```
{"8000/tcp":{}}

State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
LISTEN  0       2048          0.0.0.0:8000       0.0.0.0:*
LISTEN  0       128           0.0.0.0:9090       0.0.0.0:*

Connection to api (172.18.0.5) 9090 port [tcp/*] succeeded!
```

**What it means:** only 8000 is exposed, but the metrics/admin port 9090 is
reachable by every container on `shop_default`. `expose:` is documentation
plus a hint for tools; it filters nothing.

**Why this step (now):** you must replace a false belief with evidence before
you design the real isolation.

**Next step:** → Step 2 (what Traefik does with the hint) and Step 3 (real isolation).

#### Step 2 — See which port Traefik picked

**Goal:** confirm Traefik routes to the port the app really serves.

```bash
docker inspect -f '{{range $k, $v := .Config.Labels}}{{$k}}={{$v}}{{println}}{{end}}' CONTAINER | grep -i 'traefik.*port'
```

```
(no output: no port label)
```

**What it means:** with the Docker provider, Traefik uses the single exposed
port, or the **lowest** one if the container exposes several (an image that
exposes 80 and 8000 gets traffic on 80). With the Swarm provider there is no
port detection at all, so the label is mandatory. A wrong guess shows up as
a 502. Pin it:

```yaml
labels:
  - traefik.http.services.shop-api.loadbalancer.server.port=8000
```

**Why this step (now):** this is where the "harmless" `expose:` causes real
incidents. See the [Traefik Docker routing docs](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

**Next step:** → Step 3.

#### Step 3 — Build real isolation with networks

**Goal:** make the database unreachable from anything that does not need it.

```yaml
services:
  api:
    networks: [dokploy-network, backend]     # Traefik can reach it; it can reach db
  db:
    networks: [backend]                      # only api can reach it
networks:
  dokploy-network:
    external: true
  backend:
    internal: true                           # no route to the outside world either
```

Inside the container, bind admin or metrics ports to `127.0.0.1` if nothing
else should scrape them. After the redeploy, test from both sides:

```bash
# From the shared network (where Traefik and every other app live): must FAIL
docker run --rm --network dokploy-network nicolaka/netshoot nc -vz -w2 db 5432
# From inside the api container's network namespace: must SUCCEED
docker run --rm --net container:shop-api-1 nicolaka/netshoot nc -vz -w2 db 5432
```

```
nc: getaddrinfo for host "db" port 5432: Name does not resolve
Connection to db (172.20.0.3) 5432 port [tcp/postgresql] succeeded!
```

**What it means:** from `dokploy-network` the name `db` does not even resolve:
the database is invisible to Traefik and to every other app on the shared
network. From the api's namespace it connects over `backend`. That is real
isolation, enforced by network membership rather than by `expose:`.

**Why this step (now):** last, because it is the only step that changes the
deployment; Steps 1 and 2 first proved that `expose:` does not isolate and pinned
Traefik's port, so the redesign fixes a proven problem.

**Next step:** If the shared-network test still connects → `db` is still attached
to `dokploy-network` (check `docker inspect -f '{{json .NetworkSettings.Networks}}' CONTAINER`)
or someone published 5432 with `ports:`; fix and redeploy. If the api lost the
database → it is missing the `backend` network. Otherwise → decision tree.

#### Decision tree: what expose really does

```
"only the exposed port is reachable" — is it?
├── netshoot on the same network: nc -vz NAME OTHERPORT succeeds → expose filters nothing
│   ├── port must stay private to the container → bind it to 127.0.0.1 inside the app
│   └── service must be private to some apps → separate network with internal: true
└── Traefik 502 after an image exposes a second port → it picked the lowest one
    └── pin traefik.http.services.NAME.loadbalancer.server.port=PORT
```

**Fix & verify:** from a netshoot container on `dokploy-network`,
`nc -vz -w2 db 5432` must fail; from `api`, it must succeed.

**Rollback:** revert the Compose change and redeploy.

**Prevent it next time:** one network per trust zone, `internal: true` for data
stores, and a port label on every routed service.

---

## 4. Docker: DNS and container networking

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine – Networking: Networking Deep Dive – Namespaces, then Networking Deep Dive – Docker ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Namespaces/page)) · 2) Note: [Learn Docker](30-learn-docker.md) (networking, embedded DNS) and [DNS reference](08-dns.md) · 3) Video: *How Docker Networking Actually Works* ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Read: [netshoot](https://github.com/nicolaka/netshoot) and [Dokploy: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking) · 5) Practice: [iximiuz Labs: container networking from scratch](https://labs.iximiuz.com/tutorials/container-networking-from-scratch) (the ip netns + veth drill).

### DNS fails inside a container, works on the host

> 📚 **Know this first:** 1) Note: [DNS reference](08-dns.md) (resolv.conf, systemd-resolved) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking: DNS ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)) · 3) Read: [Dokploy: Networking & DNS](https://docs.dokploy.com/docs/core/troubleshooting/networking).

**Level:** [L2 · Mid] — the Ops Ladder L2 DNS skills (tcpdump, getent, resolvectl) inside a network namespace.

**Symptom:** `dig` and `curl` work on the host, but inside the container you get
`Temporary failure in name resolution`, `getaddrinfo EAI_AGAIN`,
`could not resolve host`, or internal names (`db.corp.example.com`) fail while
public names work. This is blind spot "containers have their own resolver" from
the ops ladder.

#### Step 1 — Reproduce inside, split DNS from connectivity

**Goal:** prove it is name resolution, not all outbound traffic.

```bash
# What resolver does the container use? (read the comment lines at the bottom too)
docker exec CONTAINER cat /etc/resolv.conf

# Resolve through the container's own resolver; netshoot brings dig
docker run --rm --net container:CONTAINER nicolaka/netshoot dig +time=2 +tries=1 db.corp.example.com
docker run --rm --net container:CONTAINER nicolaka/netshoot dig +time=2 +tries=1 example.com

# Raw connectivity by IP, no DNS involved
docker run --rm --net container:CONTAINER nicolaka/netshoot nc -vz -w2 192.0.2.53 53
```

```
# Generated by Docker Engine.
# This file can be edited; Docker Engine will not make further changes once it
# has been modified.

nameserver 127.0.0.11
search corp.example.com
options ndots:0

# Based on host file: '/run/systemd/resolve/resolv.conf' (internal resolver)
# ExtServers: [8.8.8.8 8.8.4.4]
# Overrides: [nameservers]
# Option ndots from: internal

;; communications error to 127.0.0.11#53: timed out
;; no servers could be reached

Connection to 192.0.2.53 53 port [tcp/domain] succeeded!
```

**What it means:**

- `nameserver 127.0.0.11`: the container is on a user-defined network (Compose, Dokploy) and asks Docker's **embedded DNS**, which answers container names itself and forwards everything else.
- `ExtServers: [8.8.8.8 8.8.4.4]` with `Overrides: [nameservers]`: the embedded DNS forwards to Google's public servers because someone configured them: a `dns` list in `/etc/docker/daemon.json`, `dns:` in the Compose file, or `--dns` (a "fix" often copied from blog posts). On-prem firewalls usually block 8.8.8.8, and it can never answer `corp.example.com` names anyway.
- Without an override, current Docker uses the host's upstreams: on systemd-resolved hosts it reads `/run/systemd/resolve/resolv.conf` (the real servers), and a loopback-only resolver such as a local dnsmasq on 127.0.0.1 shows up as `ExtServers: [host(127.0.0.1)]`, which the embedded DNS queries from the host's own network namespace. Both are usually fine.
- The internal DNS server 192.0.2.53 **is** reachable by IP, so outbound traffic works: this is purely a resolver problem.

On the default `bridge` network (plain `docker run` with no `--network`) there
is no embedded DNS: the container gets a filtered copy of the host's
resolv.conf, loopback entries removed, and Google's servers if nothing is left
(the comment block then says `# Used default nameservers.`). Image builds
resolve the same way (section 6), and so do builds inside a Docker-in-Docker CI
runner: that is where a loopback-only host resolver still leads to 8.8.8.8.

**Why this step (now):** "DNS is broken" often turns out to be "all egress is
broken". One `nc` by IP splits the two before you touch any resolver config.

**Next step:** If the IP test also fails → Step 4 (egress, not DNS). If
ExtServers shows public servers or wrong servers → Step 2. If upstreams look
right but answers are wrong → Step 3.

#### Step 2 — Compare with the host's resolver setup

**Goal:** understand why Docker picked those upstreams.

```bash
cat /etc/resolv.conf                       # stub 127.0.0.53, a local cache, or real servers?
resolvectl status | sed -n '1,30p'         # global and per-link DNS servers and domains
cat /run/systemd/resolve/resolv.conf       # the real upstreams systemd-resolved uses
grep -s '"dns"' /etc/docker/daemon.json    # a host-wide override?
docker inspect -f '{{.HostConfig.Dns}}' CONTAINER   # a per-container override (Compose dns:, --dns)?
```

```
nameserver 127.0.0.53
options edns0 trust-ad
search corp.example.com

Link 2 (ens18)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53 192.0.2.54
        DNS Domain: corp.example.com

nameserver 192.0.2.53
nameserver 192.0.2.54
search corp.example.com

  "dns": ["8.8.8.8", "8.8.4.4"],
[]
```

**What it means:** the host resolves through systemd-resolved, whose real
upstreams are the corporate servers 192.0.2.53 and .54; they answer internal
and external names. Docker would have used them, but daemon.json overrides them
with Google's public servers for every container (the per-container list is
empty, so the override is host-wide). Another variant: a VPN with **split DNS**
(resolved sends `*.corp.example.com` to one server and everything else to
another); that per-domain routing does not survive into containers. For a
failing default-bridge container or image build on a host whose resolv.conf
lists only a loopback cache (dnsmasq or unbound on `127.0.0.1`), dockerd logs
`No non-localhost DNS nameservers are left in resolv.conf. Using default external servers`
(`sudo journalctl -u docker | grep -i nameservers`).

**Why this step (now):** the fix must point Docker at servers that can answer
both internal and external names from the container's position. You can only
choose them once you know how the host resolves.

**Next step:** → Step 3 to watch the packets and confirm, or straight to the fix
if the log line is unambiguous.

#### Step 3 — Watch the DNS packets on both sides

**Goal:** see where the query goes and whether an answer comes back, instead of inferring it.

```bash
# Terminal 1, host side: queries leaving the host for real DNS servers
sudo tcpdump -ni any 'port 53 and not host 127.0.0.53' -c 20

# Terminal 2: repeat the failing lookup from inside the container
docker run --rm --net container:CONTAINER nicolaka/netshoot dig +time=2 +tries=1 db.corp.example.com

# Alternative: the host's own tcpdump inside the container's network namespace
sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' CONTAINER)" -n tcpdump -ni any port 53 -c 10
```

```
10:44:02.101 ens18 Out IP 192.0.2.10.51515 > 8.8.8.8.53: 41234+ [1au] A? db.corp.example.com. (48)
10:44:04.103 ens18 Out IP 192.0.2.10.51515 > 8.8.8.8.53: 41234+ [1au] A? db.corp.example.com. (48)
```

**What it means:** the query leaves the host (already NATed to the host's
address 192.0.2.10) towards 8.8.8.8 and never gets an answer: the perimeter
firewall drops it. If you saw the answer arrive and the app still failed, the
problem would be the answer itself (NXDOMAIN from the wrong server) or the
app's resolver library.

**Why this step (now):** this is the ops ladder's first blind spot: a capture
shows directly whether the query leaves, to whom, and whether an answer comes
back. It ends the argument with the network team in one screenshot.

**Next step:** → "Fix & verify" below. If no packet leaves the host at all →
Step 4.

#### Step 4 — Rule out general egress problems

**Goal:** when even the IP test fails, check forwarding and NAT.

```bash
sysctl net.ipv4.ip_forward                                   # must be 1 on a Docker host
sudo iptables -t nat -L POSTROUTING -n | grep -i masquerade  # one MASQUERADE per bridge subnet
ip route get 192.0.2.53                                      # leaves via the right interface?
docker run --rm --net container:CONTAINER nicolaka/netshoot ping -c2 -W2 192.0.2.1
```

```
net.ipv4.ip_forward = 0
MASQUERADE  all  --  172.17.0.0/16  0.0.0.0/0
MASQUERADE  all  --  172.18.0.0/16  0.0.0.0/0
```

**What it means:** `ip_forward = 0`. A hardening script or a sysctl file turned
off forwarding, so no container can reach anything outside the host. Docker
enables it at start; something disabled it later (look in `/etc/sysctl.d/`).
Missing MASQUERADE rules usually mean someone flushed iptables: restart Docker
in a window to rebuild them.

**Why this step (now):** only needed when Step 1's IP test failed; it explains
"DNS is broken" incidents that are really "everything is broken".

**Next step:** restore `net.ipv4.ip_forward = 1` (and remove the setting that
disabled it), then repeat Step 1.

#### Decision tree: DNS inside a container

```
inside the container (netshoot)
├── nc to DNS server IP fails ......... egress problem: ip_forward, MASQUERADE, routes, firewall (Step 4)
└── IP works, names fail
    ├── resolv.conf 127.0.0.11, ExtServers = 8.8.8.8 ... public "dns" override → daemon.json "dns" = internal resolvers
    ├── no 127.0.0.11, nameserver 8.8.8.8 .............. default bridge + loopback-only host resolver → user-defined network + "dns"
    ├── internal names fail, public work ............... split DNS / wrong upstream → internal resolvers in "dns"
    ├── container names fail ........................... not on a shared network → next scenario
    └── works after recreate ........................... upstreams changed after container start
```

**Fix & verify**

```bash
# 1. Back up and edit /etc/docker/daemon.json: internal resolvers that answer internal AND external names
#      { "dns": ["192.0.2.53", "192.0.2.54"] }
sudo cp -a /etc/docker/daemon.json /etc/docker/daemon.json.$(date +%F) 2>/dev/null
sudo dockerd --validate --config-file /etc/docker/daemon.json
# 2. Restart Docker in a window (restarts every container on the host)
sudo systemctl restart docker
# 3. Containers read DNS settings at creation: recreate them
docker compose up -d --force-recreate          # Compose; Dokploy: redeploy the app
# 4. Verify from a fresh container on the app's network
docker run --rm --network shop_default nicolaka/netshoot dig +short db.corp.example.com example.com
```

Per container instead of host-wide: `docker run --dns 192.0.2.53 ...` or `dns:`
in Compose. Dokploy documents the same daemon.json fix in its
[networking troubleshooting page](https://docs.dokploy.com/docs/core/troubleshooting/networking);
it also cures DNS failures during image builds on the Dokploy server.

**Rollback:** restore the dated copy of daemon.json, restart Docker, recreate the containers.

**Prevent it next time**

- Ship daemon.json with a `dns` list on every Docker host from day one (an Ansible task, as in the ops ladder L3 drill).
- Give CI runners (Docker-in-Docker) the same DNS settings; they fall back to 8.8.8.8 too.
- Practise: break DNS on purpose in the homelab and capture it with netshoot + tcpdump until it takes you under five minutes.

---

### Containers on different networks cannot talk

> 📚 **Know this first:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page)) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)) · 3) Note: [Docker reference](14-docker-containers.md).

**Level:** [L1 · Junior] — the most common Compose networking mistake; one inspect command finds it.

**Symptom:** `could not translate host name "db"`, `getaddrinfo ENOTFOUND redis`,
or a timeout to another container's IP; typical after splitting one Compose
file into two, or when a Dokploy Compose app must talk to a Dokploy Application.

#### Step 1 — List the networks of both containers

**Goal:** check whether they share at least one network.

```bash
for c in shop-api-1 billing-db-1; do
  printf '%-14s %s\n' "$c" "$(docker inspect -f '{{range $n, $_ := .NetworkSettings.Networks}}{{$n}} {{end}}' "$c")"
done
docker network inspect billing_default -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{println}}{{end}}'
```

```
shop-api-1     dokploy-network shop_default
billing-db-1   billing_default
billing-db-1 172.21.0.3/16
```

**What it means:** no shared network. Docker's embedded DNS only answers names
of containers on networks the **asking** container is attached to, and Docker's
isolation rules block traffic between different bridge networks even by IP.
Names that resolve on a shared network: the container name, the Compose service
name, and any `--alias`. On the default `bridge` network, no names resolve at all.

**Why this step (now):** it answers the question in one command, before you
debug the app's connection string.

**Next step:** If no shared network → Step 2 to confirm, then fix. If they share
one → check the name the app uses (service name vs container name vs Dokploy app
name) and the port, with Step 2.

#### Step 2 — Test resolution and reachability from the caller

**Goal:** see exactly what the caller sees.

```bash
docker run --rm --net container:shop-api-1 nicolaka/netshoot dig +short @127.0.0.11 billing-db-1
docker run --rm --net container:shop-api-1 nicolaka/netshoot nc -vz -w2 172.21.0.3 5432
```

```
(empty: no answer)
nc: connect to 172.21.0.3 port 5432 (tcp) timed out: Operation in progress
```

**What it means:** no name and no route between the two networks, as expected
from Step 1.

**Why this step (now):** it gives you a test to repeat after the fix.

**Next step:** → "Fix & verify".

#### Decision tree: container to container

```
caller → dig @127.0.0.11 NAME (from caller's netns)
├── no answer → shared network? (docker inspect Networks)
│   ├── no  → join a common network (external network in both Compose files)
│   └── yes → wrong name: use service name / alias / Dokploy app name
└── answer, but nc fails → wrong port? target listens on 127.0.0.1? (ss -ltn in its netns)
```

**Fix & verify**

```bash
# Quick test (lost when the container is recreated):
docker network connect --alias db shop_default billing-db-1
docker run --rm --net container:shop-api-1 nicolaka/netshoot nc -vz -w2 db 5432
```

The permanent fix goes in the Compose files: create a network once
(`docker network create shared-db`) and declare it as external in both projects:

```yaml
services:
  db:
    networks:
      shared-db:
        aliases: [db]
networks:
  shared-db:
    external: true
```

In Dokploy, Compose services that must reach an Application (a Swarm service)
both join `dokploy-network`, and the Application is addressed by its Dokploy
app name (the Swarm service name, for example `shop-api-x1y2z3`), not its
display name. A standalone container can only join an overlay network created
with `--attachable` (`dokploy-network` is).

**Rollback:** `docker network disconnect shop_default billing-db-1`, or revert the Compose change.

**Prevent it next time:** declare networks explicitly in every Compose file, give
dependencies stable aliases, and write the network diagram into the app's README.

---

### Docker subnet collides with on-prem networks

> 📚 **Know this first:** 1) Note: [Learn networking](28-learn-networking.md) (CIDR, routing tables) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page)) · 3) Read: [Docker docs: Networking](https://docs.docker.com/engine/network/).

**Level:** [L3 · Senior] — routing tables plus daemon.json address-pool design for a whole fleet.

**Symptom:** right after `docker compose up`, a Dokploy install or a new
network, SSH from part of the office dies, monitoring loses the host, or the
server can no longer reach an internal system (LDAP, NFS, a database on
172.20.x.x). The console still works. People say "the routes vanished".

> ⚠️ Work from the VM console or a jump host in another subnet. If your own SSH
> session comes from the colliding range, it dies with the first step that fixes
> things the wrong way round.

#### Step 1 — Ask the kernel which way it routes the lost address

**Goal:** prove that a Docker bridge has captured traffic meant for the LAN.

```bash
ip -br addr | grep -E 'docker0|br-|docker_gwbridge'
ip route
ip route get 172.20.5.14            # an address of the client that lost access
```

```
docker0          DOWN           172.17.0.1/16
br-7a1c2e3f4b5d  UP             172.20.0.1/16

default via 192.0.2.1 dev ens18 proto static
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.20.0.0/16 dev br-7a1c2e3f4b5d proto kernel scope link src 172.20.0.1
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10

172.20.5.14 dev br-7a1c2e3f4b5d src 172.20.0.1 uid 1000
```

**What it means:** the office subnet 172.20.0.0/16 is reached through the default
gateway, but a new Docker network got 172.20.0.0/16 too. Its connected route is
more specific than the default route, so replies to 172.20.5.14 now go into a
Docker bridge. Nothing vanished; a better-matching route won. Docker avoids
subnets that already have a route on the host, but it cannot know about networks
that sit behind the default gateway.

**Why this step (now):** `ip route get` gives the kernel's actual decision for
one address. It is the shortest proof there is.

**Next step:** → Step 2 to list every Docker subnet; or the emergency mitigation
in "Fix & verify" if users are down right now.

#### Step 2 — Compare every Docker subnet with the IP plan

**Goal:** find all collisions, not just the one that hurt first.

```bash
docker network ls -q | xargs docker network inspect -f '{{printf "%-22s" .Name}} {{.Driver}}  {{range .IPAM.Config}}{{.Subnet}} {{end}}'
grep -sE 'bip|default-address-pools' -A3 /etc/docker/daemon.json
docker info --format '{{json .Swarm.Cluster.DefaultAddrPool}} mask={{.Swarm.Cluster.SubnetSize}}' 2>/dev/null
```

```
bridge                 bridge   172.17.0.0/16
host                   host
none                   null
shop_default           bridge   172.20.0.0/16
docker_gwbridge        bridge   172.18.0.0/16
ingress                overlay  10.0.0.0/24
dokploy-network        overlay  10.0.1.0/24
["10.0.0.0/8"] mask=24
```

**What it means:** Docker's built-in pools hand out 172.17.0.0/16 to
172.31.0.0/16 and then pieces of 192.168.0.0/16 for local networks, and Swarm
overlays come from 10.0.0.0/8. If the company uses any of 172.16.0.0/12,
192.168.0.0/16 or 10.0.0.0/8 (most do), you will collide sooner or later. Get
the real list of office, VPN and data-centre ranges from the network team.

**Why this step (now):** fixing only `shop_default` leaves the next network to
collide next week.

**Next step:** → "Fix & verify" with a planned range.

#### Decision tree: routes "vanish" after a Docker change

```
ip route get LOST_IP
├── via the default gateway → not a Docker collision → firewall / remote side
└── dev br-XXXX or docker0 → Docker subnet overlaps a LAN range
    ├── users down now → temporary specific route via the gateway
    └── permanent → bip + default-address-pools (+ Swarm pool) → recreate networks
```

**Fix & verify**

Emergency mitigation (no restart; lost at reboot): a more specific route via
the real gateway wins over Docker's /16, as long as no container needs those
addresses:

```bash
sudo ip route add 172.20.5.0/24 via 192.0.2.1 dev ens18
ip route get 172.20.5.14            # now: via 192.0.2.1 dev ens18
```

Permanent fix, in a maintenance window:

```bash
# 1. Agree free ranges with the network team, e.g. 10.209.0.0/24 and 10.210.0.0/16
# 2. /etc/docker/daemon.json (back it up first):
#    {
#      "bip": "10.209.0.1/24",
#      "default-address-pools": [ { "base": "10.210.0.0/16", "size": 24 } ]
#    }
sudo dockerd --validate --config-file /etc/docker/daemon.json
sudo systemctl restart docker
# 3. Existing networks keep their old subnet: recreate them
docker compose down && docker compose up -d          # per Compose project
docker network rm shop_default                        # only networks with no containers
# 4. Verify
docker network ls -q | xargs docker network inspect -f '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}'
ip route get 172.20.5.14                              # via 192.0.2.1 dev ens18
```

Swarm (Dokploy) uses separate pools: the overlay pool is set only at
`docker swarm init --default-addr-pool 10.211.0.0/16 --default-addr-pool-mask-length 24`,
and `docker_gwbridge` and `ingress` can be recreated with custom subnets only
while no services use them. On an existing Dokploy host, plan this as a migration
and read the Docker networking docs first.

**Rollback:** restore the dated daemon.json, restart Docker, recreate the
networks; delete the emergency route with `sudo ip route del 172.20.5.0/24`.

**Prevent it next time**

- Put `bip` and `default-address-pools` in daemon.json **before the first container** on every new host (Ansible), and pass `--default-addr-pool` at `docker swarm init`.
- Keep the container ranges in the company IP plan so the network team never hands them out.
- Add `ip route` to your post-change checks.

---

## 5. Docker: disk, storage and permissions

> 📚 **Study path:** 1) Note: [Storage & disk reference](01-storage-disk.md) (df, du, deleted-but-open files) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Logging Driver ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 3) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands: Volumes and Bind Mounts; Docker Engine & Storage ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 4) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions; Storage in Linux (NFS) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 5) Practice: on the [Docker playground](https://kodekloud.com/playgrounds/playground-docker), fill the disk with a chatty container and recover it with the safe prune order below.

### Docker filled the disk

> 📚 **Know this first:** 1) Note: [Storage & disk reference](01-storage-disk.md) · 2) KodeKloud: *Docker Certified Associate* — Logging Driver ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 3) Note: [Learn Docker](30-learn-docker.md) (logging, daemon.json).

**Level:** [L1 · Junior] — df, du and safe cleanup; the senior part is setting log rotation for every host.

**Symptom:** `no space left on device` in builds or container logs, Postgres
refusing writes, the Docker daemon failing to start, or a disk alert at 95%+ on
a Docker host.

#### Step 1 — Confirm which filesystem is full and Docker's share

**Goal:** make sure Docker is the culprit before deleting anything Docker owns.

```bash
df -h / /var/lib/docker ; df -i /var/lib/docker
docker system df
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   95G  3.1G  97% /

TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          47        9         31.42GB   26.87GB (85%)
Containers      12        9         14.31GB   212.4MB (1%)
Local Volumes   18        6         9.734GB   6.11GB (62%)
Build Cache     214       0         14.2GB    14.2GB
```

**What it means:** Docker lives on the root filesystem, which is 97% full.
Images could give back 27 GB, build cache 14 GB. Container logs are **not** in
this table at all, so also check Step 2. "Reclaimable" volumes are volumes no
container uses right now; that includes the database of a stack you stopped
yesterday.

**Why this step (now):** you need to know the size of each bucket to free space
in the safest order. If Docker holds little, the culprit is elsewhere →
[Storage](01-storage-disk.md).

**Next step:** → Step 2 for the details Docker does not show here.

#### Step 2 — Break down /var/lib/docker, logs and layers

**Goal:** find the specific containers, logs or volumes that grew.

```bash
sudo du -xh --max-depth=1 /var/lib/docker | sort -h | tail -8

# Container JSON logs (not shown by docker system df)
sudo find /var/lib/docker/containers -name '*-json.log' -size +200M -printf '%s %p\n' \
  | sort -n | tail -5 | numfmt --field=1 --to=iec

# Writable layer per container: an app writing into its own filesystem
docker ps -s --format 'table {{.Names}}\t{{.Size}}'

# Detail per image / volume / build cache
docker system df -v | less
```

```
2.3G    /var/lib/docker/buildkit
9.8G    /var/lib/docker/volumes
21G     /var/lib/docker/containers
46G     /var/lib/docker/overlay2
80G     /var/lib/docker

19G /var/lib/docker/containers/4be1c0d9e8f7.../4be1c0d9e8f7...-json.log

NAMES       SIZE
shop-api    13.9GB (virtual 15.1GB)
worker      12kB (virtual 412MB)
```

**What it means:**

- `containers/` at 21 GB is almost all one JSON log of 19 GB: the default `json-file` driver never rotates unless you configure it.
- `shop-api` has a 13.9 GB writable layer: it writes uploads, temp or log files inside the container instead of into a volume. That data dies with the container and slows overlay2.
- `overlay2/` holds image layers plus writable layers.

Map a log file's ID to a name with `docker ps -a --no-trunc --format '{{.ID}} {{.Names}}' | grep 4be1c0d9`.

**Why this step (now):** pruning images would not touch a 19 GB log or a 14 GB
writable layer. Each grower has its own fix.

**Next step:** If logs → Step 3. If images/build cache → Step 4. If a writable
layer → move that path to a volume (Fix & verify).

#### Step 3 — Relieve a giant log safely

**Goal:** get space back right now without breaking the running container.

```bash
docker inspect -f '{{.HostConfig.LogConfig}}' CONTAINER        # {json-file map[]} = no rotation
docker logs --since 2h CONTAINER > /root/CONTAINER-last2h.log 2>&1   # keep recent evidence
sudo truncate -s 0 /var/lib/docker/containers/FULLID/FULLID-json.log
df -h /
```

```
{json-file map[]}
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   61G   33G  65% /
```

**What it means:** `{json-file map[]}` confirms the container logs with no
`max-size`, so its file grew without limit; after the truncate the root
filesystem dropped to 65%. `truncate` empties the file in place. Do not `rm` it: dockerd
keeps the file open, so the space would not come back until the container is
recreated (the "deleted but open" trap from [Storage](01-storage-disk.md)).

**Why this step (now):** it is the fastest big win with no impact on the
service. Rotation (Fix & verify) stops it from coming back.

**Next step:** → Step 4 if you still need space.

#### Step 4 — Prune in the safe order

**Goal:** free space from the least valuable data first, and never lose data you cannot re-create.

```bash
# 1. Build cache older than 3 days (always re-creatable)
docker builder prune -f --filter until=72h

# 2. Dangling images (untagged leftovers of rebuilds)
docker image prune -f

# 3. Stopped containers: LOOK first; some are one-shot jobs you may want to inspect
docker ps -a --filter status=exited --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
docker container prune -f --filter until=168h

# 4. Unused images older than 14 days (keep recent ones: they are your rollback)
docker image prune -a -f --filter until=336h

# 5. Volumes: never in bulk. List, inspect, back up, then remove one by one
docker volume ls -f dangling=true
docker volume inspect -f '{{.Name}} {{.CreatedAt}} {{.Labels}}' VOLUME
docker run --rm -v VOLUME:/v:ro alpine ls -la /v          # what is in it?
```

```
Deleted build cache objects:
k3j2h1g0f9e8...
Total reclaimed space: 13.8GB

Total reclaimed space: 4.12GB
Total reclaimed space: 18.9GB
```

**What it means:** each command prints what it freed. Stop as soon as you have
enough headroom; the rest can wait for a proper cleanup policy.

> ⚠️ `docker system prune -a --volumes` does steps 1–5 at once without asking
> per item: it removes every stopped container first, so the volumes those
> containers used become "unused" too. Since Docker 23, `--volumes` (and
> `docker volume prune`) removes only **anonymous** volumes unless you run
> `docker volume prune --all`; before 23 it removed named volumes as well. An
> anonymous volume can still be a database (an image with a `VOLUME` line started
> without a named volume), so know your version and your volumes before relying
> on that. Dokploy's server settings also offer cleanup buttons and a
> scheduled cleanup: read what each one removes before you enable it.

**Why this step (now):** the order follows "how hard is it to get back": build
cache and dangling images cost nothing, tagged images can be re-pulled from
Harbor, volumes may be the only copy of a database.

**Next step:** → "Fix & verify" to stop the growth.

#### Decision tree: Docker filled the disk

```
df -h → full filesystem holds /var/lib/docker?
├── no → not Docker → storage playbook
└── yes → docker system df + du /var/lib/docker
    ├── containers/ big → *-json.log → truncate now, log-opts rotation, recreate
    ├── docker ps -s big → app writes in its layer → move path to a volume
    ├── build cache big → docker builder prune --filter until=72h
    ├── images big → image prune (dangling) → prune -a --filter until=336h
    └── volumes big → inspect one by one, back up, remove deliberately
```

**Fix & verify**

```bash
# Rotation for all NEW containers: /etc/docker/daemon.json
#   { "log-driver": "json-file", "log-opts": { "max-size": "20m", "max-file": "5" } }
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
# Existing containers keep their old log config until recreated:
docker compose up -d --force-recreate        # Dokploy: redeploy
docker inspect -f '{{.HostConfig.LogConfig}}' CONTAINER     # {json-file map[max-file:5 max-size:20m]}
df -h /                                                     # below 80%
```

Per service in Compose instead:

```yaml
services:
  api:
    logging:
      driver: json-file
      options: { max-size: "20m", max-file: "5" }
    volumes:
      - uploads:/app/uploads          # the path that bloated the writable layer
volumes:
  uploads:
```

**Rollback:** pruned images can be pulled again from Harbor; removed volumes
cannot be restored without a backup, which is why they come last.

**Prevent it next time**

- daemon.json with `log-opts` on every host from day one.
- Put `/var/lib/docker` on its own LV or disk (`data-root`), so Docker filling up never stops the OS, SSH or journald.
- Alert at 80% disk (node_exporter); schedule `docker builder prune --filter until=72h` on build hosts.
- Keep every deployable image in Harbor, so local images are always disposable.

---

### Permission denied on bind mounts or NFS

> 📚 **Know this first:** 1) Note: [Users, permissions & security](10-users-permissions-security.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions; Storage in Linux (NFS) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands: Volumes and Bind Mounts ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)).

**Level:** [L1 · Junior] — numeric UIDs and file modes; the NFS root-squash and SELinux branches are Mid-level.

**Symptom:** `PermissionError: [Errno 13] Permission denied: '/app/data/...'`,
`chown: changing ownership of '/var/lib/postgresql/data': Operation not permitted`,
or `mkdir: cannot create directory: Permission denied` on a mounted path.

#### Step 1 — Compare numeric UIDs on both sides

**Goal:** see which user the process runs as and who owns the directory, as numbers.

```bash
docker exec CONTAINER id                          # who the app runs as
docker inspect -f 'user={{.Config.User}}' CONTAINER
docker exec CONTAINER ls -lnd /app/data           # owner as seen inside
ls -lnd /srv/shop/data                            # owner on the host
docker info --format '{{.SecurityOptions}}'       # userns-remap or rootless changes the mapping
```

```
uid=999(app) gid=999(app) groups=999(app)
user=app
drwxr-xr-x 2 1000 1000 4096 Oct  3 09:00 /app/data
drwxr-xr-x 2 1000 1000 4096 Oct  3 09:00 /srv/shop/data
[name=apparmor name=seccomp,profile=builtin name=cgroupns]
```

**What it means:** the app runs as UID 999; the directory belongs to UID 1000
(the admin who created it with `mkdir`) with mode 755, so 999 may only read.
Names are irrelevant: UID 1000 is `ops` on the host and maybe nobody in the
image; the kernel only compares numbers. No `name=userns` in security options,
so UIDs map 1:1.

**Why this step (now):** almost every bind-mount permission error is a UID
mismatch, and this is a read-only check.

**Next step:** If the path is a local disk → fix ownership (Fix & verify). If
`findmnt` shows NFS → Step 2. If owner and mode look right on RHEL/Rocky → Step 3.

#### Step 2 — Check for NFS root squash

**Goal:** detect when root in the container is not root on the file server.

```bash
findmnt -T /srv/shop/data
sudo touch /srv/shop/data/.root-test          # even host root fails with root_squash
ls -lnd /srv/shop/data
```

```
TARGET          SOURCE                         FSTYPE OPTIONS
/srv/shop/data  192.0.2.30:/exports/shop/data  nfs4   rw,relatime,vers=4.1,rsize=1048576,...

touch: cannot touch '/srv/shop/data/.root-test': Permission denied
drwxr-x--- 2 999 999 4096 Oct  3 09:10 /srv/shop/data
```

**What it means:** with `root_squash` (the NFS default), UID 0 is mapped to
`nobody` (65534) on the server. A container running as root, or an entrypoint
that tries to `chown` the data directory at startup (Postgres and many official
images do), fails. Only the export's owning UID (999 here) can write.

**Why this step (now):** NFS adds a second permission system on another machine;
local `chown` cannot fix it.

**Next step:** run the container as the UID that owns the export (`user: "999:999"`),
or have the storage team export the share with `all_squash,anonuid=999,anongid=999`
for this app. Avoid `no_root_squash`. Avoid databases on NFS altogether (locking
and fsync semantics); use local disks or the database's own replication.

#### Step 3 — Check SELinux labels on RHEL and Rocky

**Goal:** catch the denial that looks like a permission problem but is a label problem.

```bash
getenforce
ls -Zd /srv/shop/data
sudo ausearch -m avc -ts recent | tail -3
```

```
Enforcing
unconfined_u:object_r:var_t:s0 /srv/shop/data
type=AVC msg=audit(1759484400.123:812): avc:  denied  { write } for  pid=48211 comm="python" name="data" dev="dm-0" ino=1310722 scontext=system_u:system_r:container_t:s0:c123,c456 tcontext=unconfined_u:object_r:var_t:s0 tclass=dir permissive=0
```

**What it means:** containers run as `container_t` and may only write to files
labelled `container_file_t`. The directory is `var_t`, so the write is denied
even with perfect UIDs. Fix with a mount option: `:z` (shared label, several
containers) or `:Z` (private label, this container only), e.g.
`-v /srv/shop/data:/app/data:Z`; or label it permanently:
`sudo semanage fcontext -a -t container_file_t '/srv/shop/data(/.*)?' && sudo restorecon -Rv /srv/shop/data`.

> ⚠️ Never use `:z`/`:Z` on system paths such as `/home`, `/etc`, `/usr` or `/`:
> Docker relabels everything below the path and can break the host.

On Ubuntu, AppArmor rarely blocks bind mounts; check with
`sudo journalctl -k | grep 'apparmor="DENIED"'`.

**Why this step (now):** last, because it only applies once UIDs and NFS are
ruled out, and only on SELinux hosts.

**Next step:** apply the label fix and re-test.

#### Decision tree: permission denied on a mount

```
id (inside) vs ls -lnd (host)
├── UIDs differ → chown dir to the app UID, or run as the dir's UID, or group + g+rwX
├── NFS (findmnt) → root squashed → run as export owner UID / all_squash anonuid on server
├── SELinux Enforcing + AVC denied → :z / :Z or semanage fcontext container_file_t
└── userns-remap / rootless → host UID = container UID + offset (/etc/subuid)
```

**Fix & verify**

```bash
stat -c '%u:%g %a %n' /srv/shop/data              # record the old owner first (for rollback)
sudo chown -R 999:999 /srv/shop/data              # dedicated app directory only
docker exec CONTAINER sh -c 'touch /app/data/.write-test && rm /app/data/.write-test && echo WRITE OK'
```

Never use `chmod 777`: it hides the UID problem and lets every user on the host
change the data.

**Rollback:** `sudo chown -R OLDUID:OLDGID /srv/shop/data` with the values you
recorded; remove the `:Z` option or the fcontext rule (`semanage fcontext -d`).

**Prevent it next time**

- Build images with a fixed, documented UID (for example 10001) and create data directories for that UID in your Ansible role.
- Prefer named volumes: Docker copies the image's ownership into a new, empty named volume.
- Agree NFS export options with the storage team per application UID.

---

## 6. Docker: images, registry and builds

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Image Management: Authenticating to Registries, Build Cache, Multi-Stage Builds ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page)) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Registry ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page)) · 3) Read: [Harbor docs: Configure HTTPS Access to Harbor](https://goharbor.io/docs/2.15.0/install-config/configure-https/) (KodeKloud has no Harbor course) · 4) Note: [Learn Docker](30-learn-docker.md) (registries, Dockerfile) and [Web, HTTP & TLS](18-web-http-tls.md) · 5) Practice: on the [Docker playground](https://kodekloud.com/playgrounds/playground-docker), run a registry with a self-signed CA, see the x509 error, then fix the trust.

### x509 unknown authority pulling from Harbor

> 📚 **Know this first:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Work With SSL Certificates ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 3) Note: [Web, HTTP & TLS](18-web-http-tls.md).

**Level:** [L2 · Mid] — certificate chains and trust stores, the L2 TLS skill, on every client that pulls.

**Symptom:** `docker pull`, a Dokploy deploy, a GitLab CI job or a Swarm task
fails with `x509: certificate signed by unknown authority` for your Harbor
registry, which uses the company's private CA.

#### Step 1 — Pull by hand and read the exact error

**Goal:** separate trust problems from name, expiry and auth problems.

```bash
docker pull harbor.example.com/shop/api:1.4.2
```

```
Error response from daemon: Get "https://harbor.example.com/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
```

**What it means:** the TLS handshake worked, but this machine does not trust the
CA that signed Harbor's certificate. Related errors and where they point:

| Error | Real cause | Fix side |
|---|---|---|
| `certificate signed by unknown authority` | private CA not trusted here | this host (Step 3) |
| `certificate is valid for harbor.local, not harbor.example.com` | name not in the certificate's SAN | reissue the certificate |
| `certificate relies on legacy Common Name field, use SANs instead` | certificate has no SAN at all | reissue with SAN |
| `certificate has expired or is not yet valid` | expired, or this host's clock is wrong | Harbor, or [time](12-time-ntp.md) |
| `http: server gave HTTP response to HTTPS client` | the registry speaks plain HTTP on that port | registry config |
| `unauthorized`, `denied: requested access to the resource is denied` | login / robot account / project permissions | `docker login`, Harbor project |
| `manifest unknown`, `not found` | the tag does not exist | CI pipeline / tag |

**Why this step (now):** only one row of that table is solved by installing a
CA. Reading the error avoids distributing certificates to fix a typo.

**Next step:** If unknown authority → Step 2. Other rows → the matching fix.

#### Step 2 — Inspect the chain Harbor presents

**Goal:** know which CA to trust, and whether Harbor sends its intermediate.

```bash
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts </dev/null 2>/dev/null \
  | grep -E '^ *[0-9] s:|^ *i:|Verify return code'

# Check the CA file you were given BEFORE distributing it
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -CAfile ./corp-root-ca.crt </dev/null 2>/dev/null \
  | grep 'Verify return code'
openssl x509 -in ./corp-root-ca.crt -noout -subject -enddate
```

```
 0 s:CN = harbor.example.com
   i:CN = Example Corp Issuing CA 01
 1 s:CN = Example Corp Issuing CA 01
   i:CN = Example Corp Root CA
Verify return code: 20 (unable to get local issuer certificate)

Verify return code: 0 (ok)
subject=CN = Example Corp Root CA
notAfter=Mar 14 00:00:00 2034 GMT
```

**What it means:** Harbor sends its certificate plus the intermediate (good);
the root `Example Corp Root CA` is unknown to this host (code 20). With
`-CAfile` the chain verifies (code 0), so `corp-root-ca.crt` is the right file.
If you saw only certificate 0 and `21 (unable to verify the first certificate)`,
Harbor itself is missing the intermediate: fix Harbor's certificate file to
contain the full chain instead of patching every client.

**Why this step (now):** distributing the wrong file to ten nodes and then
debugging ten nodes is worse than one `openssl` test.

**Next step:** → Step 3.

#### Step 3 — Trust the CA on every host that pulls

**Goal:** make Docker trust Harbor without disabling verification.

```bash
# Docker's per-registry trust: no daemon restart needed
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp corp-root-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
#   Registry on a non-443 port? The directory name includes it:
#   /etc/docker/certs.d/harbor.example.com:8443/ca.crt
docker pull harbor.example.com/shop/api:1.4.2

# System-wide trust as well (curl, git, helm, and many apps); file must be PEM and end in .crt
sudo cp corp-root-ca.crt /usr/local/share/ca-certificates/corp-root-ca.crt
sudo update-ca-certificates
#   RHEL/Rocky: sudo cp corp-root-ca.crt /etc/pki/ca-trust/source/anchors/ && sudo update-ca-trust
#   A DER (.cer) file? convert: openssl x509 -inform der -in ca.cer -out ca.crt
```

```
1 added, 0 removed; done.
```

**What it means:** `certs.d` is scoped to that registry and read on each pull,
so it is the least invasive fix. The system store helps every other TLS client;
Docker reads it only at daemon start.

Everywhere else that pulls needs the same CA:

| Puller | Where the CA goes |
|---|---|
| every Swarm / Dokploy node that runs the service | `/etc/docker/certs.d/HARBOR/ca.crt` on each node |
| GitLab CI with Docker-in-Docker | inside the `dind` service container's `/etc/docker/certs.d/HARBOR/` (mount or custom image) |
| buildx builders (docker-container driver) | `buildkitd.toml`: `[registry."HARBOR"]` with `ca=["/etc/certs/ca.crt"]` |
| Kubernetes nodes (containerd) | `/etc/containerd/certs.d/HARBOR/hosts.toml` (section 8, ImagePullBackOff) |

**Why this step (now):** you proved in Step 2 that this CA fixes the chain; now
you install it in the narrowest place that works.

**Next step:** pull again. If it still fails with a different error, go back to
the table in Step 1.

#### Step 4 — Insecure registries only as a last resort

**Goal:** know the emergency option and why to avoid it.

```json
{ "insecure-registries": ["harbor.example.com"] }
```

```bash
# Audit: has someone already taken this shortcut on this host?
docker info 2>/dev/null | grep -A3 'Insecure Registries'
```

```
 Insecure Registries:
  harbor.example.com
  ::1/128
  127.0.0.0/8
```

**What it means:** loopback ranges are always listed; any real registry name in
this list (here `harbor.example.com`) means the shortcut is active on this host
and must be planned out. Docker then accepts any certificate (and falls back to HTTP)
for that registry. Anyone who can intercept traffic can serve you a different
image. `insecure-registries` is one of the options dockerd reloads on SIGHUP
(`sudo systemctl reload docker`, no container restart), which makes the
shortcut dangerously cheap to switch on; audit for it.

**Why this step (now):** it is listed last on purpose: use it only on a lab host,
and remove it as soon as the CA is distributed.

**Next step:** replace it with Step 3 and delete the setting.

#### Decision tree: registry pull errors

```
docker pull HARBOR/PROJECT/IMAGE:TAG
├── unknown authority → openssl s_client -showcerts
│   ├── chain incomplete (code 21) → fix Harbor's cert file (full chain)
│   └── chain fine, root unknown (code 20) → certs.d/HARBOR/ca.crt on every puller
├── valid for X, not Y / legacy CN → reissue certificate with the right SAN
├── expired / not yet valid → Harbor cert, or the client clock
├── unauthorized / denied → docker login, robot account, project membership
└── manifest unknown → tag does not exist (check the CI pipeline)
```

**Fix & verify:** `docker pull` succeeds; `docker login harbor.example.com`
works; on Swarm, `docker service update --force SERVICE` and
`docker service ps SERVICE` shows Running tasks on every node.

**Rollback:** remove `/etc/docker/certs.d/HARBOR/`, or the file in
`/usr/local/share/ca-certificates/` followed by `sudo update-ca-certificates --fresh`.

**Prevent it next time**

- Distribute the company CA to every Docker host, runner and Kubernetes node with Ansible, before the first pull.
- Issue Harbor's certificate with a SAN for every name clients use, serve the full chain, and alert 30 days before expiry.
- Use Harbor robot accounts per pipeline or cluster, never a personal login.

---

### Image build failures

> 📚 **Know this first:** 1) KodeKloud: *Docker Certified Associate* — Multi-Stage Builds ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page)) · 2) Note: [Learn Docker](30-learn-docker.md) (Dockerfile, build cache) · 3) Read: [GitLab docs: Use Docker to build Docker images](https://docs.gitlab.com/ci/docker/using_docker_build/) (DinD and DNS in CI).

**Level:** [L2 · Mid] — reading BuildKit output and separating DNS, context and cache problems.

**Symptom:** `docker build` (by hand, in GitLab CI or in a Dokploy deploy)
fails with `failed to solve`, apt/npm/pip cannot resolve hosts, `COPY` cannot
find a file, or the image builds but contains stale code.

#### Step 1 — Get the full output and find the first error

**Goal:** read the first failing instruction, not the last line of noise.

```bash
docker build --progress=plain -t shop-api:debug . 2>&1 | tee /tmp/build.log
grep -nE 'ERROR|error:|failed' /tmp/build.log | head
```

```
#7 [build 3/6] RUN apt-get update && apt-get install -y --no-install-recommends build-essential
#7 20.47 Err:1 http://deb.debian.org/debian bookworm InRelease
#7 20.47   Temporary failure resolving 'deb.debian.org'
#7 ERROR: process "/bin/sh -c apt-get update && apt-get install -y --no-install-recommends build-essential" did not complete successfully: exit code: 100
```

**What it means:** the `RUN` step inside the build cannot resolve names. The
common build failures:

| Error text | Cause | Go to |
|---|---|---|
| `Temporary failure resolving`, `EAI_AGAIN`, `Could not resolve host` | DNS/network inside build steps | Step 2 |
| `failed to compute cache key: ... "/dist": not found` | COPY source missing: wrong path, wrong context, `.dockerignore`, wrong stage | Step 3 |
| `failed to resolve source metadata for HARBOR/...: x509` | base image pull from Harbor | previous scenario |
| `no space left on device` | build cache filled the disk | section 5 |
| `exit code: 137` in a RUN step | build ran out of memory (npm, webpack, compilers) | more RAM or fewer parallel jobs |
| `exec format error` in RUN | building for another CPU architecture without emulation | `--platform` / native runner |
| builds fine, old code in the image | cache reused a stale layer | Step 3 |

**Why this step (now):** BuildKit runs steps in parallel and prints a lot; the
first ERROR is the real one, everything after is fallout.

**Next step:** follow the table.

#### Step 2 — Fix DNS and network during builds

**Goal:** give build steps the same name resolution as the host.

```bash
# Build RUN steps resolve like a container on the default bridge: test that path
docker run --rm busybox nslookup deb.debian.org
cat /etc/resolv.conf
```

```
;; connection timed out; no servers could be reached
nameserver 127.0.0.1
```

**What it means:** build steps resolve like the default bridge network
(section 4): with a loopback-only host resolver they fall back to public servers
that the firewall blocks. Fixes, best first:

- `"dns": ["192.0.2.53", "192.0.2.54"]` in daemon.json (also fixes Dokploy builds on that server).
- Behind an HTTP proxy: `--build-arg HTTP_PROXY=http://proxy.corp.example.com:3128 --build-arg HTTPS_PROXY=http://proxy.corp.example.com:3128 --build-arg NO_PROXY=harbor.example.com,.corp.example.com` (predefined build args, not saved in the image history).
- Workaround while you fix it: `docker build --network=host ...`.

**Why this step (now):** a DNS failure in a build is not a Dockerfile bug, and no
Dockerfile change fixes it.

**Next step:** rebuild; if pulls of the base image need a proxy, the daemon
needs it too (systemd drop-in `/etc/systemd/system/docker.service.d/http-proxy.conf`
with `Environment="HTTPS_PROXY=..."`, then `daemon-reload` and a restart).

#### Step 3 — Debug context, cache and multi-stage targets

**Goal:** see what each stage really produced.

```bash
cat .dockerignore                                     # is dist/ or the source excluded?
docker build --target build -t shop-api:stage-build .  # stop after the "build" stage
docker run --rm -it --entrypoint sh shop-api:stage-build
#   inside: ls -la /app /app/dist       (where did the build put its output?)
docker build --no-cache --pull -t shop-api:fresh .     # ignore cache, refresh base image
docker buildx du | tail -4                             # build cache size
```

```
node_modules
.git
*.log

/ # ls -la /app /app/dist
ls: /app/dist: No such file or directory
/app:
total 32
drwxr-xr-x    1 root     root          4096 Oct  3 10:12 .
drwxr-xr-x    1 root     root          4096 Oct  3 10:12 ..
drwxr-xr-x    3 root     root          4096 Oct  3 10:12 build
drwxr-xr-x  412 root     root         16384 Oct  3 10:12 node_modules
-rw-r--r--    1 root     root           612 Oct  3 10:11 package.json

Shared:         1.02GB
Private:        3.85GB
Reclaimable:    3.11GB
Total:          4.87GB
```

**What it means:** in this sample the build stage wrote its output to
`/app/build` (the framework's default), so the runtime stage's
`COPY --from=build /app/dist ./dist` has nothing to copy. In general,
`COPY --from=build /app/dist ./dist` fails when the build
stage wrote to `/app/build` instead, or when `.dockerignore` excluded the input.
`--target` stops at any stage so you can look inside it. Stale code usually
means a cached layer was reused: put dependency installs before `COPY . .`, keep
`apt-get update && apt-get install` in one `RUN`, and use `--pull` in CI so base
images are fresh.

**Why this step (now):** after DNS, context and cache cover nearly all remaining
build failures, and inspecting a stage is faster than guessing paths.

**Next step:** fix the Dockerfile and rebuild with `--progress=plain`.

#### Decision tree: build failures

```
first ERROR in --progress=plain output
├── resolving / EAI_AGAIN → busybox nslookup → daemon.json dns, proxy build-args, --network=host
├── cache key / not found → .dockerignore, context path, --target STAGE and look inside
├── x509 on base image → Harbor CA (certs.d, buildkitd.toml for buildx)
├── 137 / no space → memory / builder prune
└── stale content → --no-cache --pull, reorder layers
```

**Fix & verify:** a clean `docker build --no-cache --pull --progress=plain`
succeeds, and `docker run --rm IMAGE` passes the smoke test.

**Rollback:** keep deploying the last good tag from Harbor while the build is broken.

**Prevent it next time:** a pinned base image (`python:3.12-slim-bookworm`, not
`latest`), a reviewed `.dockerignore`, CI builds with `--pull`, and build runners
that share the hosts' DNS and CA settings ([CI/CD module](33-learn-cicd-iac-sre.md)).

---

### Slow container: CPU throttling, memory pressure, I/O

> 📚 **Know this first:** 1) Note: [Slow system playbook](23-playbook-slow-system.md) and [CPU & performance](03-cpu-performance.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Monitor Storage Performance ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) · 3) Read: [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html).

**Level:** [L3 · Senior] — cgroup v2 counters and the USE method applied per container.

**Symptom:** the app is slow or has latency spikes, but the host looks mostly
idle. For host-wide slowness use the [slow system playbook](23-playbook-slow-system.md).

#### Step 1 — Compare the container's usage with its limits

**Goal:** spot a container pinned at its CPU quota or memory limit.

```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.BlockIO}}\t{{.PIDs}}'
docker inspect -f 'cpus={{.HostConfig.NanoCpus}} mem={{.HostConfig.Memory}}' CONTAINER
```

```
NAME       CPU %     MEM USAGE / LIMIT     BLOCK I/O        PIDS
shop-api   199.84%   612MiB / 1GiB         1.2GB / 38GB     41
worker     3.10%     180MiB / 512MiB       0B / 0B          5

cpus=2000000000 mem=1073741824
```

**What it means:** `shop-api` sits at 199.8% with a 2-CPU limit
(`NanoCpus` 2000000000 = 2.0 CPUs): it uses all it is allowed. It has also
written 38 GB to disk, which is unusual for an API.

**Why this step (now):** a container can be starved while the host shows 80%
idle, because limits apply per container. This is the one-screen check.

**Next step:** CPU at the limit → Step 2. Memory near the limit → Step 3. High
block I/O → Step 4. Nothing near a limit → Step 5.

#### Step 2 — Read the CPU throttling counters

**Goal:** prove the kernel is pausing the container because of its quota.

```bash
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' CONTAINER).scope
cat $CG/cpu.max ; cat $CG/cpu.stat ; cat $CG/cpu.pressure
```

```
200000 100000
usage_usec 912334871
user_usec 801223456
system_usec 111111415
nr_periods 412233
nr_throttled 198102
throttled_usec 7712334981
some avg10=41.27 avg60=38.90 avg300=30.12 total=7812339911
full avg10=36.80 avg60=35.02 avg300=27.55 total=7001223455
```

**What it means:** `cpu.max 200000 100000` = 200 ms of CPU per 100 ms period (2
CPUs). It was throttled in 198102 of 412233 periods (48%); every throttle is a
pause of up to the rest of the 100 ms period, which is exactly what latency
spikes look like. `cpu.pressure some avg10=41` means tasks were waiting for CPU
41% of the last 10 seconds. Runtimes that size thread pools from the host's 32
CPUs make this worse.

**Why this step (now):** the counters separate "the app is CPU hungry" from "the
app is slow for another reason" with numbers.

**Next step:** raise `--cpus` (or remove the CPU limit and keep a reservation),
or size the runtime to the quota (gunicorn workers, `GOMAXPROCS`, Java
`-XX:ActiveProcessorCount`). Then re-check `nr_throttled` growth.

#### Step 3 — Check memory pressure below the OOM line

**Goal:** catch a container that is not killed but constantly reclaiming memory.

```bash
cat $CG/memory.events $CG/memory.pressure
grep -E '^(anon|file) ' $CG/memory.stat
```

```
low 0
high 0
max 18233
oom 0
oom_kill 0
some avg10=22.10 avg60=19.75 avg300=12.03 total=1022334455
full avg10=15.44 avg60=12.80 avg300=8.91 total=802233112
anon 1012334592
file 31457280
```

**What it means:** no kills, but `max 18233` reclaim events and memory pressure
of 22%: the app keeps hitting the limit and the kernel keeps squeezing its page
cache (`file` is only 30 MB). Everything that reads files gets slow.

**Why this step (now):** OOM kills are loud; memory pressure is silent and
shows up only as latency.

**Next step:** raise the limit or reduce the working set (see the OOMKilled
scenario, Step 3).

#### Step 4 — Check disk I/O and the writable layer

**Goal:** find heavy writes, especially into overlay2.

```bash
cat $CG/io.stat ; cat $CG/io.pressure
iostat -xz 1 3                       # host view: which device is saturated (sysstat package)
docker ps -s --filter name=shop-api --format '{{.Names}} {{.Size}}'
```

```
8:0 rbytes=1048576 wbytes=48318382080 rios=212 wios=1934120 dbytes=0 dios=0
some avg10=18.42 avg60=15.07 avg300=9.88 total=812345678
full avg10=17.90 avg60=14.61 avg300=9.52 total=790123456

Device   r/s    rkB/s  r_await     w/s      wkB/s  w_await  aqu-sz  %util     (columns trimmed)
sda     2.00     8.00     0.50  412.00   52340.00    38.20   15.71  98.40

shop-api-x1y2z3.1.k2v8x0q1m3n4p5q6 6.2GB (virtual 6.6GB)
```

**What it means:** in this sample the container has written 48 GB since it
started, its tasks were stalled on I/O about 18% of the time over the last 10
seconds (`some avg10=18.42`), the host disk `sda` is 98% busy with 38 ms write
latency, and the writable layer has grown to 6.2 GB. High `wbytes` in `io.stat`, `io.pressure` above a few percent,
and a growing writable layer mean the app writes into its container filesystem.
Overlay2 copies a whole file up on its first write, and every write goes through
the overlay. Write-heavy paths (uploads, caches, SQLite, logs) belong on volumes.

**Why this step (now):** after CPU and memory, I/O is the third resource with
a per-container limit and pressure file.

**Next step:** move the path to a volume; if the host disk itself is saturated,
see [Storage](01-storage-disk.md).

#### Step 5 — Check what the app is waiting on

**Goal:** when no resource is saturated, look at dependencies.

```bash
# Time each phase of one request, from the container's own network namespace
docker run --rm --net container:CONTAINER nicolaka/netshoot \
  curl -s -o /dev/null -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} total=%{time_total}\n' https://api.partner.example.com/health
# Which upstreams does the embedded DNS forward to?
docker exec CONTAINER tail -4 /etc/resolv.conf
```

```
dns=5.004 connect=5.012 tls=5.118 total=5.402

# Based on host file: '/etc/resolv.conf' (internal resolver)
# ExtServers: [192.0.2.99 192.0.2.53]
# Overrides: []
# Option ndots from: internal
```

**What it means:** the name lookup alone takes about 5 seconds, then connect
and TLS are fast. The first upstream (192.0.2.99, a decommissioned resolver)
times out and the second one answers, so every new connection first waits out a
multi-second forwarding timeout (the exact figure depends on the Docker version
and the app's resolver settings). Fix the resolver
list (section 4).

**Why this step (now):** "slow" without saturation is almost always waiting:
DNS, a database, a remote API.

**Next step:** fix the slow dependency; for app-level profiling see
[performance & observability](32-learn-performance-observability.md).

#### Decision tree: slow container

```
docker stats vs limits
├── CPU at quota → cpu.stat nr_throttled ↑ → raise --cpus or size threads to quota
├── memory near limit → memory.events max ↑, memory.pressure → raise limit / shrink working set
├── block I/O high → io.stat, docker ps -s → move write paths to volumes; check host disk
└── nothing saturated → time getent / curl -w timings → DNS, DB, remote API
```

**Fix & verify:** after the change, `nr_throttled` stops growing fast, pressure
`avg10` drops below a few percent, and the app's p95 latency returns to normal.

**Rollback:** `docker update --cpus N --memory M CONTAINER` back to the old values,
or revert the Compose/service change.

**Prevent it next time:** set limits from measured usage plus headroom, export
cgroup metrics (cAdvisor) and alert on throttling ratio and memory pressure, and
load-test with production limits.

---

## 7. Dokploy, Traefik and Swarm

> 📚 **Study path:** 1) Note: [Case study: Apache, 443 and Dokploy](21-case-apache-443-dokploy.md) and [Learn web servers & proxies](29-learn-webservers-proxies.md) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress: Traefik Overview, Demo Traefik Installation (Traefik on Kubernetes; the concepts carry over) ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) · 3) KodeKloud: *Docker Certified Associate* — Docker Swarm: Swarm Services, Docker Overlay Network, Swarm Service Discovery ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) · 4) Read: [Traefik: Docker quick start](https://doc.traefik.io/traefik/getting-started/docker/) and [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) (KodeKloud has no Dokploy content) · 5) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* ([YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 6) Practice: the Ops Ladder L3 drill: make Traefik return 502 with a wrong port, then fix it from Traefik's logs alone.

How Dokploy wires things, so the steps below make sense:

- **Traefik** (container `dokploy-traefik`) owns ports 80 and 443. Entrypoint `web` is :80, `websecure` is :443. Static config: `/etc/dokploy/traefik/traefik.yml`. Dynamic config: files in `/etc/dokploy/traefik/dynamic/`, watched live. Let's Encrypt certificates: `acme.json` in that folder.
- **Applications** in Dokploy run as Swarm services on the overlay network `dokploy-network`. Dokploy writes one dynamic file per application with its routers (one per entrypoint) pointing at `http://APPNAME:PORT`, the port you typed in the domain settings.
- **Compose** apps get their routing from Traefik **labels** that Dokploy injects at deploy time, and their services must join `dokploy-network`. Labels are read when the container is created: a domain change does nothing until you redeploy.
- **Dokploy itself** is the Swarm service `dokploy` (UI on :3000), with `dokploy-postgres` and `dokploy-redis` beside it.

Read the [Dokploy troubleshooting docs](https://docs.dokploy.com/docs/core/troubleshooting) and the
[Traefik Docker routing page](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/)
once with this map in mind.

### Traefik returns 404 page not found

> 📚 **Know this first:** 1) Note: [Learn web servers & proxies](29-learn-webservers-proxies.md) (routers, entrypoints) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) · 3) Read: [Traefik docs: Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

**Level:** [L2 · Mid] — reverse-proxy routing by Host and SNI, the L2 proxy skill.

**Symptom:** the browser shows a bare `404 page not found`, often with a
certificate warning for `TRAEFIK DEFAULT CERT`.

#### Step 1 — Prove the 404 is Traefik's, with exact Host and SNI

**Goal:** separate "Traefik found no route" from "the app answered 404", and test past DNS.

```bash
# Plain HTTP, Host header set by hand (port 80, entrypoint "web")
curl -sv -o /dev/null http://203.0.113.10/ -H 'Host: shop.example.com' 2>&1 | grep -E '^< HTTP|^< Content-Type'

# HTTPS with the right SNI, without depending on DNS (entrypoint "websecure");
# -k because Traefik's default certificate is self-signed (inspection only)
curl -skv --resolve shop.example.com:443:203.0.113.10 https://shop.example.com/ 2>&1 \
  | grep -E 'subject:|issuer:|^< HTTP|404 page'
```

```
< HTTP/1.1 404 Not Found
< Content-Type: text/plain; charset=utf-8

*  subject: CN=TRAEFIK DEFAULT CERT
*  issuer: CN=TRAEFIK DEFAULT CERT
< HTTP/2 404
404 page not found
```

**What it means:** `text/plain` with the body `404 page not found`, plus
Traefik's self-signed default certificate, means Traefik received the request
and **no router matched** this host on this entrypoint. An app 404 looks
different: an HTML page, the app's own headers, and the real certificate. If
`--resolve` works but the browser does not, DNS points somewhere else (the old
Apache server?) → [site down playbook](25-playbook-site-down.md).

**Why this step (now):** `--resolve` and `-H Host:` pin the request to this
Traefik, so you test routing alone, not DNS or the browser cache (ops ladder
blind spot "you can test past DNS without fixing it").

**Next step:** If Traefik's 404 → Step 2. If the app's 404 → the route works;
check the path and the app's logs.

#### Step 2 — List the routers Traefik actually has

**Goal:** compare the rule you think exists with what Traefik loaded.

```bash
# Via the API, if enabled (api.insecure, or the dashboard toggle in Dokploy)
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers \
  | jq -r '.[] | [.name, .rule, (.entryPoints | join(",")), .status] | @tsv'

# Without the API: Dokploy Application routers live in dynamic files
sudo grep -rn 'Host(' /etc/dokploy/traefik/dynamic/ | grep -i shop

# Compose apps and plain containers: the labels on the container
docker inspect -f '{{json .Config.Labels}}' CONTAINER | jq -r 'to_entries[] | select(.key | startswith("traefik")) | "\(.key)=\(.value)"'

# Swarm services: Traefik reads SERVICE labels (deploy.labels), not container labels
docker service inspect -f '{{json .Spec.Labels}}' SERVICE | jq
```

```
dokploy-router-app@file                     Host(`dokploy.example.com`)  web        enabled
shop-api-x1y2z3-router-1@file               Host(`shop.example.com`)     web        enabled
shop-api-x1y2z3-router-websecure-1@file     Host(`shop.example.com`)     websecure  enabled
crm-web@docker                              Host(`crm.exmaple.com`)      websecure  enabled
wiki-web@docker                             Host(`wiki.example.com`)     websecure  disabled
```

**What it means:**

- `crm.exmaple.com` is a typo in the rule: requests for `crm.example.com` match nothing.
- `wiki-web` exists but is **disabled**: Traefik found an error in it (a missing middleware, an unknown cert resolver, a service with no servers). `.../api/http/routers/wiki-web@docker` shows the error text.
- A router only on `websecure` does not answer plain HTTP on :80, and vice versa.
- A router that is missing entirely means Traefik never saw the app (Step 3).

**Why this step (now):** Traefik's own view is the only truth; Dokploy's UI and
your Compose file show intent, not what is loaded.

**Next step:** If the router is missing → Step 3. If it exists with a wrong rule
or entrypoint → fix the domain in Dokploy and redeploy. If disabled → read its
error in the API or the Traefik log.

#### Step 3 — Check why Traefik did not pick up the app

**Goal:** find the reason a container or config file produced no router.

```bash
docker logs --since 1h dokploy-traefik 2>&1 | grep -E ' ERR | WRN |error' | tail -10
docker ps --filter name=shop --format 'table {{.Names}}\t{{.Status}}'
ls -l --time-style=+%F_%T /etc/dokploy/traefik/dynamic/
```

```
2026-10-03T10:12:44Z ERR Error occurred during watcher callback error="/etc/dokploy/traefik/dynamic/shop.yml: yaml: line 7: did not find expected key" providerName=file
2026-10-03T10:14:02Z ERR error="middleware \"redirect-to-https@file\" does not exist" entryPointName=web routerName=wiki-web@docker

NAMES                                  STATUS
shop-web-1                             Up 4 minutes (unhealthy)
```

**What it means:** the usual reasons, all visible here:

- a YAML error in one dynamic file: the file provider rejects the update for the **whole directory**, so Traefik keeps serving the last good file configuration and your change (and every later one) silently does nothing; after a Traefik restart the file provider loads nothing at all, and every file-based route (all Dokploy Applications) returns 404 until the file is fixed
- a router referencing a middleware or resolver that does not exist → router disabled
- the container is `unhealthy` (or still `starting`): the Docker provider skips unhealthy containers, so the route disappears exactly when the healthcheck fails
- no `traefik.enable=true` label (Dokploy's Traefik uses `exposedByDefault: false`)
- labels written under `labels:` instead of `deploy: labels:` in a Swarm stack
- the domain was changed in Dokploy but the Compose app was not redeployed, so the container still carries the old labels (compare `docker inspect` labels with the UI)

**Why this step (now):** once you know the router is missing, the provider's
error messages explain why in one line.

**Next step:** fix the cause, redeploy (or save the file), then repeat Step 2
until the router shows `enabled`.

#### Decision tree: Traefik 404

```
curl -H Host / --resolve → "404 page not found" text/plain?
├── no, app HTML 404 → routing OK → app path / app logs
└── yes → router list (API, dynamic files, labels)
    ├── router missing
    │   ├── Traefik log: YAML / provider error → fix file
    │   ├── container unhealthy / not running → fix health first
    │   ├── traefik.enable missing / Swarm labels not under deploy.labels
    │   └── domain changed, app not redeployed → redeploy
    ├── router present, rule typo / www missing → fix domain, redeploy
    ├── router only on websecure, request on :80 (or reverse) → add entrypoint / redirect
    └── router disabled → its error (middleware, resolver) → fix reference
```

**Fix & verify**

```bash
curl -s -o /dev/null -w '%{http_code}\n' --resolve shop.example.com:443:203.0.113.10 https://shop.example.com/
echo | openssl s_client -connect 203.0.113.10:443 -servername shop.example.com 2>/dev/null | openssl x509 -noout -subject
```

→ The app's status code (200, 302) and the real certificate subject, not `TRAEFIK DEFAULT CERT`.

**Rollback:** restore the previous dynamic file (keep a copy before editing:
`sudo cp -a FILE FILE.bak`) or redeploy the previous app configuration.

**Prevent it next time**

- "Domain change = redeploy" in the team's Dokploy checklist.
- Enable Traefik access logs, so each request shows which router (or none) handled it.
- After every deploy, a smoke test with `curl --resolve` from CI or monitoring.

---

### Traefik returns 502 Bad Gateway

> 📚 **Know this first:** 1) Note: [Site down playbook](25-playbook-site-down.md) (502 and 504 per layer) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Implement Reverse Proxies and Load Balancers ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page)) · 3) Read: [Dokploy: Domains & Traefik](https://docs.dokploy.com/docs/core/troubleshooting/domains).

**Level:** [L2 · Mid] — the proxy-to-backend hop; the Ops Ladder L3 drill rehearses it under a timer.

**Symptom:** `Bad Gateway` (502) or `Gateway Timeout` (504) from Traefik. The
router matched; Traefik could not get an answer from the backend.

#### Step 1 — Find the backend Traefik tried and the exact error

**Goal:** read the backend URL and the network error, which name the broken layer.

```bash
# Access log line (if accessLog is enabled): router, backend URL, status
docker logs --since 15m dokploy-traefik 2>&1 | grep '" 502 ' | tail -3

# Error detail; 502 causes are logged at DEBUG. Temporarily set in traefik.yml:
#   log:
#     level: DEBUG
# then: docker restart dokploy-traefik   (brief interruption of all routes)
docker logs --since 5m dokploy-traefik 2>&1 | grep -E '50[24]|dial tcp|EOF|timeout' | tail -5
```

```
198.51.100.23 - - [03/Oct/2026:10:20:31 +0000] "GET / HTTP/2.0" 502 11 "-" "curl/8.5.0" 1834 "shop-api-x1y2z3-router-websecure-1@file" "http://shop-api-x1y2z3:3000" 2ms

2026-10-03T10:20:31Z DBG github.com/traefik/traefik/v3/pkg/proxy/httputil/proxy.go:117 > 502 Bad Gateway error="dial tcp 10.0.1.23:3000: connect: connection refused"
```

**What it means:** Traefik sent the request to `http://shop-api-x1y2z3:3000`
(10.0.1.23) and the host answered with a reset: the container exists and is
reachable, but **nothing listens on port 3000**. The error decides the next step:

| Error in the Traefik log | Meaning | Next |
|---|---|---|
| `connect: connection refused` | reached the container; wrong port, or the app listens on 127.0.0.1 inside | Step 2 |
| `lookup APPNAME on 127.0.0.11:53: no such host` | Traefik cannot resolve the service: not on a shared network, or the service is not running | Step 3 |
| `i/o timeout` (often a 504 after ~30 s) | Traefik uses an IP on a network it is not attached to | Step 3 |
| `EOF`, `connection reset by peer` | the app accepted, then died or closed (crash, worker timeout) | app logs, section 2 |
| 502/504 after exactly 30 or 60 s | app-server or proxy timeout (gunicorn kills workers after 30 s) | app logs: `WORKER TIMEOUT` |

**Why this step (now):** a 502 hides the real error from the client; Traefik's
log has it. Guessing between port, network and crash wastes an hour.

**Next step:** follow the table. Set the log level back to `INFO` or `ERROR`
afterwards; DEBUG is very chatty.

#### Step 2 — Check what the app listens on inside its container

**Goal:** see the listening address and port from inside the container's network namespace.

```bash
docker ps --filter name=shop-api --format '{{.Names}}'
docker run --rm --net container:CONTAINER nicolaka/netshoot ss -ltnp
```

```
shop-api-x1y2z3.1.k2v8x0q1m3n4p5q6r7s8t9u0

State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       2048        127.0.0.1:8000       0.0.0.0:*
```

**What it means:** two bugs at once: the app listens on port **8000**, not 3000
(the domain in Dokploy says 3000), and on **127.0.0.1**, which only the
container itself can reach. Defaults that cause this: uvicorn and gunicorn bind
127.0.0.1 unless told otherwise, `flask run` too, dev servers like Vite, and
`next start -H localhost`. Healthy output looks like `0.0.0.0:3000` or `*:3000`.

**Why this step (now):** `connection refused` from a reachable IP can only mean
"no listener on that address and port"; this shows the listener directly. The
app's logs would only say "listening on 127.0.0.1:8000" if you knew to look for it.

**Next step:** bind to `0.0.0.0` (`gunicorn --bind 0.0.0.0:8000`,
`uvicorn --host 0.0.0.0`), and make the domain's port in Dokploy equal the port
the app listens on (or pin `loadbalancer.server.port`). Redeploy, then verify.

#### Step 3 — Prove Traefik can reach the backend

**Goal:** check network membership and test the exact backend URL from the same network.

```bash
docker inspect -f '{{range $n, $_ := .NetworkSettings.Networks}}{{$n}} {{end}}' dokploy-traefik
docker inspect -f '{{range $n, $_ := .NetworkSettings.Networks}}{{$n}} {{end}}' CONTAINER

# Same network as Traefik, same URL as in the access log
docker run --rm --network dokploy-network nicolaka/netshoot curl -sv -m 5 http://shop-api-x1y2z3:3000/ 2>&1 | tail -4
```

```
dokploy-network bridge
shop_default

* Could not resolve host: shop-api-x1y2z3
curl: (6) Could not resolve host: shop-api-x1y2z3
```

**What it means:** the app is only on `shop_default`; Traefik is on
`dokploy-network`. No shared network means no name and no route. If the app is
on several networks, Traefik may also pick the IP from a network it cannot
reach (the timeout case); pin the network with a label:
`traefik.docker.network=dokploy-network` (Swarm provider in Traefik v3:
`traefik.swarm.network=dokploy-network`).

**Why this step (now):** testing from a throwaway container on Traefik's network
reproduces Traefik's exact path, so a success here means Traefik will succeed too.

**Next step:** add the network in the Compose file and redeploy:

```yaml
services:
  web:
    networks: [dokploy-network, default]
networks:
  dokploy-network:
    external: true
```

#### Decision tree: Traefik 502 / 504

```
Traefik log (access + DEBUG): backend URL + error
├── connection refused → netshoot ss -ltnp in the app's netns
│   ├── 127.0.0.1:PORT → bind 0.0.0.0
│   └── other port → fix Dokploy domain port / loadbalancer.server.port
├── no such host → app on dokploy-network? service running? → join network, redeploy
├── i/o timeout / 504 → multiple networks → traefik.docker.network (swarm: traefik.swarm.network)
├── EOF / reset → app crashed mid-request → docker logs, OOM, section 2
└── at 30 s / 60 s → WORKER TIMEOUT / slow endpoint → fix endpoint or raise timeouts deliberately
```

**Fix & verify**

```bash
docker run --rm --network dokploy-network nicolaka/netshoot curl -s -o /dev/null -w '%{http_code}\n' http://shop-api-x1y2z3:3000/
curl -s -o /dev/null -w '%{http_code}\n' --resolve shop.example.com:443:203.0.113.10 https://shop.example.com/
```

→ Both print the app's normal status code. Set Traefik's log level back.

**Rollback:** redeploy the previous app version or configuration from Dokploy;
revert traefik.yml from your backup if you changed it.

**Prevent it next time**

- Convention: every image reads `PORT` and binds `0.0.0.0:$PORT`; the Dokploy domain uses the same value.
- A Docker HEALTHCHECK that calls the app on its real port, so a wrong bind fails the deploy instead of producing 502s.
- Keep Traefik access logs on. Practise the ops ladder drill: break the port on purpose and fix it from Traefik's logs alone.

---

### Let's Encrypt certificate not issued

> 📚 **Know this first:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([notes](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)) · 2) Note: [Learn networking](28-learn-networking.md) (ACME HTTP-01 vs DNS-01) · 3) Practice: [badssl.com](https://badssl.com/) (self-signed and wrong.host look like Traefik's default certificate).

**Level:** [L2 · Mid] — ACME needs DNS, port 80 and TLS understood together.

**Symptom:** the site serves `TRAEFIK DEFAULT CERT` (browser warning) although
HTTPS with Let's Encrypt is enabled for the domain in Dokploy.

#### Step 1 — See which certificate is served

**Goal:** confirm the symptom for this exact name.

```bash
echo | openssl s_client -connect 203.0.113.10:443 -servername shop.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -enddate
```

```
subject=CN = TRAEFIK DEFAULT CERT
issuer=CN = TRAEFIK DEFAULT CERT
notAfter=Oct  3 10:31:07 2027 GMT
```

**What it means:** Traefik has no certificate for `shop.example.com`, so it uses
its default. (If the subject is right but the date has passed, renewal failed:
the same steps apply.) If even the router is missing you get a 404 as well →
the 404 scenario first.

**Why this step (now):** you need the served certificate, not the browser's
cached view, before reading ACME logs.

**Next step:** → Step 2.

#### Step 2 — Read Traefik's ACME errors

**Goal:** get Let's Encrypt's own reason for refusing.

```bash
docker logs --since 2h dokploy-traefik 2>&1 | grep -iE 'acme|certificate|resolver' | tail -8
```

```
2026-10-03T10:31:07Z ERR Unable to obtain ACME certificate for domains error="unable to generate a certificate for the domains [shop.example.com]: error: one or more domains had a problem:\n[shop.example.com] acme: error: 400 :: urn:ietf:params:acme:error:connection :: 203.0.113.10: Fetching http://shop.example.com/.well-known/acme-challenge/x3Jk...: Timeout during connect (likely firewall problem)\n" ACME CA=https://acme-v02.api.letsencrypt.org/directory acmeCA=https://acme-v02.api.letsencrypt.org/directory domains=["shop.example.com"] providerName=letsencrypt.acme routerName=shop-api-x1y2z3-router-websecure-1@file rule=Host(`shop.example.com`)
```

**What it means:** Let's Encrypt tried to fetch the HTTP-01 challenge on port 80
from the internet and could not connect. The common messages:

| ACME error | Cause | Fix |
|---|---|---|
| `Timeout during connect (likely firewall problem)` | port 80 not reachable from the internet | open 80 at the perimeter/cloud firewall; it must reach Traefik |
| `DNS problem: NXDOMAIN looking up A for ...` | no DNS record | create the A (and AAAA) record |
| `Invalid response from http://.../.well-known/acme-challenge/...: 404` | port 80 reaches something else (old Apache server, a CDN, another proxy) | point DNS / port 80 at Traefik |
| `rateLimited :: too many certificates ... already issued` | Let's Encrypt rate limit (e.g. 5 identical certificates per week) | wait; use the staging CA while testing |
| `CAA record for example.com prevents issuance` | a CAA record allows another CA only | add `letsencrypt.org` to CAA |
| `permissions 644 for .../acme.json are too open, please use 600` | wrong file mode | `chmod 600` (Step 4) |
| `router ... uses a non-existent resolver: letsencrypt` | resolver name mismatch | fix the label or file |

**Why this step (now):** Let's Encrypt tells you exactly which check failed;
the log saves you from testing DNS, firewall and rate limits blindly.

**Next step:** connection/404 errors → Step 3. Permission/resolver errors → Step 4.
Rate limit → wait for the window, and switch to staging while you experiment.

#### Step 3 — Test the challenge path from outside

**Goal:** reproduce what Let's Encrypt sees: public DNS and port 80 from the internet.

```bash
# From a machine OUTSIDE your network:
dig +short A shop.example.com @1.1.1.1
dig +short AAAA shop.example.com @1.1.1.1
curl -sv -m 10 http://shop.example.com/.well-known/acme-challenge/test 2>&1 | grep -E 'Connected to|^< HTTP|^< Server|timed out'
```

```
203.0.113.10
2001:db8:10::5

* Connected to shop.example.com (2001:db8:10::5) port 80
< HTTP/1.1 404 Not Found
< Server: Apache/2.4.58 (Ubuntu)
```

**What it means:** the domain has an **AAAA** record pointing to an IPv6 address
that still belongs to the old Apache server. Let's Encrypt prefers IPv6 when an
AAAA record exists, so validation hits Apache and gets Apache's 404. Healthy
output: the A/AAAA records point to the Traefik host, and the 404 comes from
Traefik (`Content-Type: text/plain`, no `Server: Apache`). A timeout here
confirms the firewall problem from Step 2.

If the server is **not reachable from the internet at all** (an internal
on-prem app), HTTP-01 can never succeed. Use the DNS-01 challenge (Traefik
supports DNS provider APIs) or a certificate from the company CA, loaded as a
custom certificate in Dokploy or via Traefik's file provider.

**Why this step (now):** testing from inside the LAN uses internal DNS and
internal routes, which Let's Encrypt never sees.

**Next step:** fix DNS or the firewall, then let Traefik retry (it tries again
when the router's configuration is reloaded, for example on a redeploy; a
Traefik restart triggers it immediately). Then verify with Step 1.

#### Step 4 — Check acme.json and the resolver

**Goal:** confirm Traefik can store certificates and which ones it holds.

```bash
sudo ls -l /etc/dokploy/traefik/dynamic/acme.json
sudo jq -r '.letsencrypt.Certificates[]?.domain.main' /etc/dokploy/traefik/dynamic/acme.json
sudo grep -A6 'certificatesResolvers' /etc/dokploy/traefik/traefik.yml
```

```
-rw------- 1 root root 23817 Oct  3 10:31 /etc/dokploy/traefik/dynamic/acme.json
dokploy.example.com
crm.example.com
certificatesResolvers:
  letsencrypt:
    acme:
      email: ops@example.com
      storage: /etc/dokploy/traefik/dynamic/acme.json
      httpChallenge:
        entryPoint: web
```

**What it means:** mode 600 is correct, and `shop.example.com` is not in the
store yet. The resolver is called `letsencrypt` and uses the HTTP challenge on
the `web` (port 80) entrypoint, which is why port 80 must stay open even if you
redirect everything to HTTPS.

> ⚠️ Do not delete acme.json to "force" a new certificate: Traefik then requests
> every certificate again at once and can hit rate limits for all your domains.
> Back it up (`sudo cp -a acme.json acme.json.bak`) before any manual change.

**Why this step (now):** storage and resolver problems block every certificate
on the host, so check them once you know the challenge path itself works.

**Next step:** fix permissions or the resolver name, restart Traefik in a quiet
moment, and watch the log for `Certificates obtained` style messages or new errors.

#### Decision tree: certificate not issued

```
served cert = TRAEFIK DEFAULT CERT
├── router missing? → 404 scenario first
└── Traefik log, ACME error
    ├── timeout / connection → port 80 closed at the perimeter → open it to Traefik
    ├── NXDOMAIN → create DNS records
    ├── invalid response 404 → A/AAAA points elsewhere (old server, IPv6!) → fix records
    ├── rate limited → wait; staging CA for tests
    ├── CAA → allow letsencrypt.org
    ├── acme.json perms / resolver name → chmod 600, fix name
    └── server not public → DNS-01 or company-CA certificate
```

**Fix & verify:** Step 1 shows `issuer=... Let's Encrypt` (an `R1x`/`E` style
intermediate) and a `notAfter` about 90 days ahead; `curl -sv https://shop.example.com/`
from outside shows `SSL certificate verify ok`.

**Rollback:** restore `acme.json.bak` and the previous traefik.yml if you changed them.

**Prevent it next time**

- Before switching DNS, check A **and** AAAA records and port 80 from outside.
- Test new setups against the Let's Encrypt staging CA (`caServer: https://acme-staging-v02.api.letsencrypt.org/directory` in the resolver), then switch to production.
- Monitor certificate expiry from outside (Blackbox exporter or an uptime checker), so a failed renewal pages you weeks before users see it.

---

### Dokploy UI unreachable on port 3000

> 📚 **Know this first:** 1) Read: [Dokploy docs](https://docs.dokploy.com/docs/core) · 2) Note: [Case study: Apache, 443 and Dokploy](21-case-apache-443-dokploy.md) (securing :3000) · 3) KodeKloud: *Docker Certified Associate* — Docker Swarm: Swarm Services ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)).

**Level:** [L2 · Mid] — Swarm service status plus the firewall rules you added yourself.

**Symptom:** `http://SERVER:3000` times out or is refused, or the Dokploy panel
domain shows an error, so you cannot deploy anything.

#### Step 1 — Test on the server itself

**Goal:** split "Dokploy is down" from "the path to Dokploy is blocked".

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
sudo ss -ltnp 'sport = :3000'
```

```
curl: (7) Failed to connect to 127.0.0.1 port 3000 after 0 ms: Couldn't connect to server
(no listener)
```

**What it means:** nothing listens on 3000 on the server itself, so Dokploy is
down (Step 2). If curl prints `200` or `307` here, Dokploy is fine and the
network path is the problem (Step 4). If `ss` shows another process on 3000
(Grafana and many Node apps default to 3000), that process took the port.

**Why this step (now):** testing locally removes the network, the firewall and
Traefik from the picture in one command.

**Next step:** If refused → Step 2. If 200/307 locally → Step 4.

#### Step 2 — Check the Dokploy services and the Swarm

**Goal:** see whether the service exists, runs, and why not.

```bash
docker info --format 'swarm={{.Swarm.LocalNodeState}} manager={{.Swarm.ControlAvailable}} addr={{.Swarm.NodeAddr}}'
docker service ls --filter name=dokploy --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'
docker service ps dokploy --no-trunc --format 'table {{.CurrentState}}\t{{.Error}}' | head -5
```

```
swarm=active manager=true addr=192.0.2.10

NAME               REPLICAS   IMAGE
dokploy            0/1        dokploy/dokploy:latest
dokploy-postgres   0/1        postgres:16
dokploy-redis      1/1        redis:7

CURRENT STATE             ERROR
Failed 20 seconds ago     "task: non-zero exit (1)"
```

**What it means:** the Swarm is fine, but `dokploy` and `dokploy-postgres` are
not running; Dokploy exits because its database is down. If `swarm=inactive` or
`error`, the node left the Swarm or its advertised address changed (for example
after a netplan IP change), and no service can run until that is fixed.

**Why this step (now):** Dokploy is three services; the panel is only the
visible one. The replica counts point at the broken dependency.

**Next step:** → Step 3 for the logs of the failing services.

#### Step 3 — Read the Dokploy and database logs

**Goal:** get the reason from the services themselves.

```bash
docker service logs --tail 30 dokploy 2>&1 | tail -10
docker service logs --tail 30 dokploy-postgres 2>&1 | tail -10
df -h / ; df -i /
```

```
dokploy.1.p9c7d6e5f4a3@web01 | Error: connect ECONNREFUSED 10.0.1.5:5432

dokploy-postgres.1.t3u4v5w6x7y8@web01 | PANIC:  could not write to file "pg_wal/xlogtemp.31": No space left on device

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   98G     0 100% /
```

**What it means:** the disk is full, so Postgres cannot write its WAL and
panics, and Dokploy cannot connect to it. Free space first (section 5), then the
services recover on their own or with a forced update.

**Why this step (now):** the dependency chain is panel → Dokploy → Postgres/Redis
→ disk; the logs walk it for you.

**Next step:** fix the root cause (disk, memory, a failed image pull), then
restart the service: `docker service update --force dokploy-postgres` and
`docker service update --force dokploy`.

#### Step 4 — Check the network path to port 3000

**Goal:** when Dokploy answers locally, find what blocks you.

```bash
# From your workstation:
nc -vz -w3 192.0.2.10 3000
# On the server: your own DOCKER-USER rule from section 3 may now block your current address
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
nc: connect to 192.0.2.10 port 3000 (tcp) timed out: Operation now in progress

Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1       37  2220 DROP       tcp  --  ens18  *      !198.51.100.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
2     1.2M  140M RETURN     all  --  *      *       0.0.0.0/0            0.0.0.0/0
```

**What it means:** in this sample the DROP counter (37 packets) grows each time
you retry, so the block is your own admin-range rule and your current address
is outside 198.51.100.0/24. In general, a timeout from outside while it works locally means a
firewall between you and the server: the perimeter/cloud firewall, or the
DOCKER-USER restriction you added for port 3000 (you are now on VPN with a
different source address). If you reach Dokploy by its domain through Traefik
instead, a failure there is a Traefik 404/502 problem (scenarios above).

**Why this step (now):** only after Dokploy is proven healthy locally.

**Next step:** allow your admin source range, or use an SSH tunnel:
`ssh -L 3000:127.0.0.1:3000 ops@192.0.2.10`, then open `http://127.0.0.1:3000`.

#### Decision tree: Dokploy UI

```
curl 127.0.0.1:3000 on the server
├── works → network path: perimeter firewall, DOCKER-USER rule, Traefik route for the panel domain
└── refused
    ├── ss: other process on 3000 → move it
    ├── swarm inactive / address changed → fix the Swarm (IP change!) before anything else
    ├── dokploy 0/1 → docker service logs dokploy
    │   └── DB/Redis down → their logs → disk full / OOM → fix → service update --force
    └── image pull failed → network/DNS/registry for docker.io
```

**Fix & verify:** `docker service ls` shows `1/1` for all three services and
`curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/` prints 200 or 307.

**Rollback:** if you changed the Dokploy version, redeploy the previous image tag
of the `dokploy` service; if you changed firewall rules, delete the rule you added.

**Prevent it next time:** back up `/etc/dokploy` and the Dokploy database (Dokploy
has built-in backups), alert on disk usage, never change a Swarm manager's IP
without a plan, and reach the panel via its domain or an SSH tunnel rather than
an open port 3000.

---

### Swarm service stuck Pending or Rejected

> 📚 **Know this first:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm: Section Introduction, Swarm Services, Placement ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction)) · 2) Read: [Docker docs: Getting started with Swarm mode](https://docs.docker.com/engine/swarm/swarm-tutorial/) · 3) Note: [Learn Docker](30-learn-docker.md) (Swarm essentials).

**Level:** [L3 · Senior] — scheduler constraints, reservations and per-node credentials across a cluster.

**Symptom:** a Dokploy deploy "finishes" but the app shows `0/1`;
`docker service ps` shows `Pending`, `Rejected` or repeating `Failed`.

#### Step 1 — Read the task errors without truncation

**Goal:** get the scheduler's or the node's exact reason.

```bash
docker service ps SERVICE --no-trunc --format 'table {{.Name}}\t{{.Node}}\t{{.DesiredState}}\t{{.CurrentState}}\t{{.Error}}' | head -6
```

```
NAME                NODE    DESIRED STATE   CURRENT STATE             ERROR
shop-api-x1y2z3.1           Running         Pending 3 minutes ago     "no suitable node (scheduling constraints not satisfied on 1 node; insufficient resources on 2 nodes)"

shop-api-x1y2z3.1   node2   Ready           Rejected 5 seconds ago    "No such image: harbor.example.com/shop/api:1.4.3@sha256:9f86d081884c…"
shop-api-x1y2z3.1   node1   Shutdown        Rejected 1 minute ago     "invalid mount config for type "bind": bind source path does not exist: /srv/shop/uploads"
```

**What it means:**

| Error | Cause | Next |
|---|---|---|
| `scheduling constraints not satisfied` | placement constraint (role, label, hostname) matches no available node | Step 2 |
| `insufficient resources` | CPU/memory **reservations** exceed what nodes have free | Step 2 |
| `host-mode port already in use` | a host-mode published port is taken on that node | section 3 |
| `No such image`, `pull access denied` | the node cannot pull: registry login, CA, or the tag does not exist | Step 3 |
| `bind source path does not exist` | the bind-mount directory is missing **on that node** | create it on every eligible node, or use volumes |
| `network ... not found` | the network was removed or is not attachable | recreate it / redeploy |

**Why this step (now):** without `--no-trunc` the Error column is cut off and
useless. With it, the scheduler states its reason in plain words.

**Next step:** follow the table.

#### Step 2 — Compare constraints and reservations with the nodes

**Goal:** find which constraint or reservation no node can satisfy.

```bash
docker node ls
docker service inspect -f '{{json .Spec.TaskTemplate.Placement}} {{json .Spec.TaskTemplate.Resources.Reservations}}' SERVICE
docker node inspect node2 -f '{{.Status.State}} {{.Spec.Availability}} labels={{.Spec.Labels}} cpu={{.Description.Resources.NanoCPUs}} mem={{.Description.Resources.MemoryBytes}}'
```

```
ID                            HOSTNAME   STATUS   AVAILABILITY   MANAGER STATUS   ENGINE VERSION
q1w2e3r4t5y6u7i8o9p0 *        node1      Ready    Active         Leader           28.4.0
a1s2d3f4g5h6j7k8l9z0          node2      Down     Active                          28.4.0
z9x8c7v6b5n4m3l2k1j0          node3      Ready    Drain                           28.4.0

{"Constraints":["node.labels.storage==ssd"]} {"NanoCPUs":2000000000,"MemoryBytes":4294967296}
down active labels=map[storage:ssd] cpu=4000000000 mem=8331542528
```

**What it means:** only node2 has the `storage=ssd` label and node2 is `Down`;
node3 is drained; node1 lacks the label. The task can never be placed. The fix
is node2 (or a label on another node), not the service.

**Why this step (now):** the scheduler said "constraints" and "resources"; this
puts the service's demands next to each node's facts.

**Next step:** bring node2 back, or add the label elsewhere
(`docker node update --label-add storage=ssd node1`), or relax the constraint /
reservation in the service spec.

#### Step 3 — Pull the image by hand on the rejecting node

**Goal:** see the real pull error on the node that rejected the task.

```bash
# On node2:
docker pull harbor.example.com/shop/api:1.4.3
# Deploying from the CLI? Send your registry credentials to the nodes:
docker service update --with-registry-auth --image harbor.example.com/shop/api:1.4.3 SERVICE
```

```
Error response from daemon: unauthorized: unauthorized to access repository: shop/api, action: pull: unauthorized to access repository: shop/api, action: pull

SERVICE
overall progress: 1 out of 1 tasks
1/1: running   [==================================================>]
verify: Service SERVICE converged
```

**What it means:** in this sample node2 has no Harbor credentials (`unauthorized`),
and the update with `--with-registry-auth` converges because it ships your
login to the nodes along with the task. The manual pull shows the true cause: `unauthorized` (no
credentials on that node: in Dokploy, select the registry in the app settings so
credentials are passed along), `x509` (CA missing on that node, section 6), or
`manifest unknown` (the tag was never pushed).

**Why this step (now):** "No such image" on one node while another runs the
service almost always means per-node credentials or trust.

**Next step:** fix credentials/CA/tag and redeploy.

#### Decision tree: Swarm task not running

```
docker service ps SERVICE --no-trunc
├── Pending: constraints → node ls / node inspect labels, availability (Down, Drain)
├── Pending: insufficient resources → lower reservations / add capacity
├── Rejected: No such image / denied → pull by hand on that node → --with-registry-auth, CA, tag
├── Rejected: bind source path → mkdir on every eligible node, or volumes
├── Rejected: host-mode port in use → ss on that node
└── Failed: non-zero exit → section 2 (container will not stay up)
```

**Fix & verify:** `docker service ps SERVICE` shows `Running` on an expected
node for more than a minute; `docker service ls` shows `1/1`.

**Rollback:** `docker service rollback SERVICE`, or redeploy the previous version in Dokploy.

**Prevent it next time:** label nodes in Ansible, keep reservations realistic,
avoid bind mounts on multi-node Swarms (use volumes or shared storage), and
configure registry credentials once per Dokploy server.

---

### Deploy succeeded but old version still served

> 📚 **Know this first:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm: Scaling, Rolling Updates and Rollbacks ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: [Deployment patterns](35-deployment-patterns.md) · 3) KodeKloud: *Demystifying DNS* — Time to Live (TTL) ([notes](https://notes.kodekloud.com/docs/Demystifying-DNS/DNS-as-a-System/Time-to-Live-TTL/page)).

**Level:** [L2 · Mid] — image digests, DNS TTLs and duplicate routes; evidence beats "redeploy again".

**Symptom:** the pipeline and Dokploy say "done", but users (or you) still see
the previous version, or the old and new version alternate between reloads.

#### Step 1 — Ask the app which version answered

**Goal:** stop judging by the UI and get a version string from the server.

```bash
curl -s https://shop.example.com/version
curl -sI https://shop.example.com/ | grep -iE 'x-app-version|etag|last-modified|^age|cache|^server'
for i in 1 2 3 4 5 6; do curl -s https://shop.example.com/version; echo; done
```

```
1.4.2 (commit 3f2a9c1)

x-app-version: 1.4.2
cache-control: public, max-age=3600
age: 1290

1.4.2
1.4.3
1.4.2
1.4.3
1.4.2
1.4.3
```

**What it means:** `age: 1290` with `max-age=3600` means a cache (CDN or a
caching proxy) served a stored copy. The alternating 1.4.2/1.4.3 means **two
backends** answer behind the same name: the old container is still running and
Traefik load-balances between old and new.

**Why this step (now):** without a version endpoint you cannot tell caching,
DNS, rollback and load balancing apart. If the app has none, add one; it is the
cheapest observability you will ever build.

**Next step:** If it alternates → Step 4. If always old → Step 2 (DNS) and
Step 3 (image). If a cache header shows a stored copy → purge the CDN/proxy
cache and use cache-busting asset names.

#### Step 2 — Make sure DNS points at the new server

**Goal:** rule out the old server (the old Apache box) still answering.

```bash
dig +short shop.example.com
curl -s --resolve shop.example.com:443:203.0.113.10 https://shop.example.com/version
```

```
198.51.100.40
1.4.3 (commit 9e8d7c6)
```

**What it means:** public DNS still points to 198.51.100.40, the old server,
while the new Traefik host (203.0.113.10) serves 1.4.3. Users still talk to the
old server until DNS changes and caches expire (the TTL).

**Why this step (now):** a migration from Apache to Dokploy usually changes the
server; the deploy can be perfect and invisible.

**Next step:** fix the DNS record; lower the TTL a day before future migrations.
If DNS is right → Step 3.

#### Step 3 — Check the image digest and the update status

**Goal:** prove which image the service runs and whether Swarm rolled back.

```bash
docker service inspect -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}' SERVICE
docker service inspect -f '{{json .UpdateStatus}}' SERVICE | jq
docker buildx imagetools inspect harbor.example.com/shop/api:latest | grep -m1 Digest
```

```
harbor.example.com/shop/api:latest@sha256:aa11bb22cc33dd44ee55ff66...
{
  "State": "rollback_completed",
  "StartedAt": "2026-10-03T11:02:13.511Z",
  "CompletedAt": "2026-10-03T11:03:01.882Z",
  "Message": "rollback completed"
}
Digest:    sha256:9f86d081884c7d659a2feaa0c55ad015...
```

**What it means:** Swarm tried the new version, the new task failed (healthcheck
or crash), and Swarm **rolled back** automatically to digest `aa11...`. The
registry's `latest` now points to `9f86...`, but the service runs the old one.
With mutable tags like `latest`, also check that the deploy really pulled
(nodes may reuse a cached image when the tag did not change in the spec).

**Why this step (now):** "deploy succeeded" in the UI only means the update was
submitted. The service's update status is what happened.

**Next step:** If rolled back → debug the new version (section 2), with
`docker service ps SERVICE --no-trunc` showing why its task failed. If the
digest is simply old → redeploy with an immutable tag.

#### Step 4 — Find duplicate backends behind one route

**Goal:** list every server behind the router.

```bash
docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/services \
  | jq -r '.[] | select(.name | test("shop")) | .name, (.loadBalancer.servers[]?.url)'
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep -i shop
```

```
shop-web@docker
http://172.20.0.4:3000
http://172.20.0.9:3000

shop-web-1            harbor.example.com/shop/web:1.4.3   Up 10 minutes
shop-old-web-1        harbor.example.com/shop/web:1.4.2   Up 3 weeks
```

**What it means:** two containers carry the same Traefik service labels (an old
Compose project from before the migration), so Traefik merged them into one
service with two servers and round-robins between them.

**Why this step (now):** alternating versions can only come from several
backends; the Traefik service list shows them all.

**Next step:** stop the old project (`docker compose -p OLDPROJECT stop`), confirm
only one server remains, then remove it after a grace period.

#### Decision tree: old version served

```
curl /version several times
├── alternates → several backends → Traefik services API → stop the old container/stack
├── always old
│   ├── --resolve to new host shows new → DNS / old server → fix record, wait TTL
│   ├── service image digest old, UpdateStatus rollback → new version failed → section 2
│   ├── mutable tag reused → deploy immutable tags (commit SHA)
│   └── built from wrong commit/branch → Dokploy deploy log shows the commit
└── headers show cache (age, CDN) → purge cache, hashed asset names
```

**Fix & verify:** six requests in a row all return the new version, from
outside and with `--resolve`.

**Rollback:** `docker service rollback SERVICE`, or redeploy the previous tag in Dokploy.

**Prevent it next time**

- Tag images with the commit SHA in GitLab CI and deploy that tag, never `latest` ([CI/CD module](33-learn-cicd-iac-sre.md)).
- Every app exposes `/version` (or a header) with the commit.
- After a migration, remove the old stacks and the old Apache vhosts within an agreed window, and keep DNS TTLs low around cut-over.

---

### Swarm overlay traffic hangs between nodes

> 📚 **Know this first:** 1) KodeKloud: *Docker Certified Associate* — Docker Overlay Network ([notes](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) · 2) Note: [Learn networking](28-learn-networking.md) (VXLAN and MTU) · 3) Note: [Network speed playbook](24-playbook-network-speed.md).

**Level:** [L3 · Senior] — VXLAN, MTU and inter-node firewalls: platform-level networking.

**Symptom:** on a multi-node Swarm (Dokploy with remote servers), services on
the same node talk fine, but traffic between nodes times out, or small requests
work while large responses and TLS handshakes hang.

#### Step 1 — Check the Swarm ports between the nodes

**Goal:** verify the control and data plane ports are open in both directions.

```bash
# From node1 to node2 (repeat in the other direction):
nc -vz -w3 192.0.2.12 2377         # cluster management (managers), TCP
nc -vz -w3 192.0.2.12 7946         # node gossip, TCP (and UDP)
nc -vzu -w3 192.0.2.12 7946
sudo tcpdump -ni ens18 udp port 4789 -c 10   # VXLAN data plane: do packets arrive on node2?
```

```
Connection to 192.0.2.12 2377 port [tcp/*] succeeded!
Connection to 192.0.2.12 7946 port [tcp/*] succeeded!
Connection to 192.0.2.12 7946 port [udp/*] succeeded!

tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on ens18, link-type EN10MB (Ethernet), snapshot length 262144 bytes
^C
0 packets captured
0 packets received by filter
0 packets dropped by kernel
```

**What it means:** in this sample the TCP control ports pass, but not one VXLAN
packet reaches node2 while a container on node1 calls one on node2: UDP 4789 is
blocked between the nodes (the "succeeded" for UDP 7946 proves little, see
below). Swarm needs 2377/tcp to managers, 7946/tcp+udp between all
nodes and 4789/udp for overlay data. UDP tests with `nc` are not conclusive;
the tcpdump on the receiving node is. No VXLAN packets arriving while a
container on node1 talks to one on node2 means a firewall between the nodes, or
something else already uses 4789 (VMware NSX does: initialize the Swarm with
`--data-path-port 7789` in that case).

**Why this step (now):** overlay traffic is ordinary UDP between the hosts;
when it is blocked, nothing inside Docker can help.

**Next step:** open the ports (UFW on each node and any firewall between), then
re-test. If small requests work and large ones hang → Step 2.

#### Step 2 — Test the MTU across the overlay

**Goal:** find packets that are too big for the path once VXLAN adds its 50 bytes.

```bash
docker network inspect dokploy-network -f '{{json .Options}}'
ip link show ens18 | grep -o 'mtu [0-9]*'
# From a container on node1 to a container IP on node2, don't fragment:
docker run --rm --network dokploy-network nicolaka/netshoot ping -c2 -W2 -M do -s 1422 10.0.1.12
docker run --rm --network dokploy-network nicolaka/netshoot ping -c2 -W2 -M do -s 1372 10.0.1.12
```

```
{"com.docker.network.driver.overlay.vxlanid_list":"4097"}
mtu 1450

PING 10.0.1.12 (10.0.1.12) 1422(1450) bytes of data.
--- 10.0.1.12 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1012ms

PING 10.0.1.12 (10.0.1.12) 1372(1400) bytes of data.
1380 bytes from 10.0.1.12: icmp_seq=1 ttl=64 time=0.61 ms
1380 bytes from 10.0.1.12: icmp_seq=2 ttl=64 time=0.55 ms
```

**What it means:** the host NIC has MTU 1450 (common inside OpenStack, VPNs and
some VMware setups). Docker gave the overlay the usual 1450 (1500 minus 50 bytes
of VXLAN header), so a full-size 1450-byte packet becomes 1500 bytes on a wire
that carries only 1450, and it is dropped silently. 1400-byte packets pass.
Small requests fit; big responses and TLS certificates do not.

**Why this step (now):** "small works, big hangs" is the signature of an MTU
problem, and a don't-fragment ping proves it in seconds.

**Next step:** create the overlay with a smaller MTU
(`docker network create -d overlay --attachable --opt com.docker.network.driver.mtu=1400 NAME`)
and recreate the services on it. On some VMware hosts, VXLAN traffic is also
dropped by NIC checksum offload; that is fixed on the host NIC, so involve the
virtualization team.

#### Decision tree: overlay between nodes

```
same node OK, cross-node fails
├── nothing works → 2377/7946/4789 between nodes (tcpdump udp 4789 on receiver)
│   └── 4789 used by NSX → swarm init --data-path-port
└── small OK, big hangs → MTU: ping -M do -s SIZE → overlay mtu option, recreate network
```

**Fix & verify:** a 1372-byte don't-fragment ping succeeds across nodes, and a
`curl` of a large page between services on different nodes completes.

**Rollback:** remove the firewall rules you opened; recreate the network with the old options.

**Prevent it next time:** document Swarm ports and MTU in the host build
(Ansible), and test cross-node traffic with a large payload when adding a node.

---

## 8. Kubernetes: pods that will not run

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Application Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure)) · 2) KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Image Pull Errors, Crashing Pods, Pending Pods, Create Container Errors ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 3) Note: [Learn Kubernetes](31-learn-kubernetes.md) (pods, scheduling) and [Kubernetes reference](15-kubernetes.md) · 4) Video: *Kubernetes Crash Course: Learn the Basics and Build a Microservice Application* ([YouTube](https://www.youtube.com/watch?v=XuSQU5Grv1g)) · 5) Practice: [Kubernetes Challenges](https://kodekloud.com/courses/kubernetes-challenges) (free), then homelab break-and-fix.

The Kubernetes method is bottom-up, the same order the CKA troubleshooting
domain uses and the [learnkube flowchart](https://learnkube.com/troubleshooting-deployments)
draws: **pods → Services → Ingress → nodes → control plane**. Do not debug the
Ingress while the pods are not Ready. Every command below takes `-n NS`; forgetting
the namespace is the most common reason for "No resources found".

### Pod stuck in Pending

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Scheduling: taints and tolerations, node selectors, affinity, resource requirements ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Learn Kubernetes](31-learn-kubernetes.md) (scheduling) · 3) Read: [learnkube: Troubleshooting deployments](https://learnkube.com/troubleshooting-deployments).

**Level:** [L3 · Senior] — scheduling is core CKA material; practise it from Mid-level on.

**Symptom:** `STATUS Pending`, `NODE` empty, for more than a few seconds.

#### Step 1 — Read the scheduler's verdict in the Events

**Goal:** let the scheduler tell you why no node fits.

```bash
kubectl -n NS get pod POD -o wide
kubectl -n NS describe pod POD | sed -n '/^Events:/,$p'
```

```
NAME                  READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
api-6d9f7b8c5-mx2lq   0/1     Pending   0          6m    <none>   <none>   <none>           <none>

Events:
  Type     Reason            Age                From               Message
  ----     ------            ----               ----               -------
  Warning  FailedScheduling  56s (x7 over 6m)   default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 2 Insufficient memory. preemption: 0/3 nodes are available: 1 Preemption is not helpful for scheduling, 2 No preemption victims found for incoming pod.
```

**What it means:** of 3 nodes, the control-plane node is excluded by its taint,
and the 2 workers do not have enough **unrequested** memory. The message
fragments you will meet:

| Fragment | Cause | Next |
|---|---|---|
| `Insufficient cpu` / `Insufficient memory` | requests do not fit in what is left of node allocatable | Step 2 |
| `had untolerated taint {...}` | taint without matching toleration (control-plane, maintenance, `disk-pressure`, `not-ready`) | Step 3 |
| `didn't match Pod's node affinity/selector` | nodeSelector / affinity labels match no node | Step 3 |
| `pod has unbound immediate PersistentVolumeClaims` | its PVC is Pending | section 10, PVC |
| `volume node affinity conflict` | the PV lives on a node/zone the pod cannot use | storage topology |
| `didn't have free ports for the requested pod ports` | `hostPort` already used on every node | drop hostPort |
| `Too many pods` | node's max-pods (110 by default) reached | more nodes |
| **no events at all** | the scheduler is not running, or `schedulerName` names one that does not exist | Step 4 |

**Why this step (now):** the scheduler evaluates every node and writes the
summary into the Events. Reading it is faster than checking nodes one by one.

**Next step:** follow the table.

#### Step 2 — Compare requests with node allocatable

**Goal:** see the numbers the scheduler used. It schedules on **requests**, not on actual usage.

```bash
kubectl -n NS get pod POD -o jsonpath='{range .spec.containers[*]}{.name}{"  requests="}{.resources.requests}{"  limits="}{.resources.limits}{"\n"}{end}'
kubectl describe node worker1 | sed -n '/^Allocatable:/,/^System Info:/p;/^Allocated resources:/,/^Events:/p'
kubectl top nodes        # actual usage, for comparison (needs metrics-server)
```

```
api  requests={"cpu":"500m","memory":"2Gi"}  limits={"memory":"2Gi"}

Allocatable:
  cpu:                2
  memory:             3880236Ki
  pods:               110
Allocated resources:
  Resource           Requests      Limits
  --------           --------      ------
  cpu                1450m (72%)   2 (100%)
  memory             3200Mi (84%)  4Gi (108%)

NAME      CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
worker1   310m         15%      1650Mi          43%
```

**What it means:** worker1 has about 3.7 GiB allocatable and 3200 Mi already
**requested**, so a 2 Gi request does not fit, even though actual usage is only
43%. Over-generous requests on other pods waste the cluster.

**Why this step (now):** "Insufficient memory" while `kubectl top` looks low
confuses everyone once; this shows why.

**Next step:** lower the request to measured usage plus headroom, lower other
over-sized requests, or add a node. Check for a namespace ResourceQuota too
(`kubectl -n NS describe quota`).

#### Step 3 — Check taints, selectors and affinity

**Goal:** find the label or taint that excludes the nodes.

```bash
kubectl get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key,EFFECT:.spec.taints[*].effect'
kubectl -n NS get pod POD -o jsonpath='{"selector: "}{.spec.nodeSelector}{"\ntolerations: "}{.spec.tolerations}{"\naffinity: "}{.spec.affinity}{"\n"}'
kubectl get nodes -L disktype -L topology.kubernetes.io/zone
```

```
NAME      TAINTS                                   EFFECT
cp1       node-role.kubernetes.io/control-plane    NoSchedule
worker1   <none>                                   <none>
worker2   node.kubernetes.io/unschedulable         NoSchedule

selector: {"disktype":"ssd"}
tolerations: [{"effect":"NoExecute","key":"node.kubernetes.io/not-ready","operator":"Exists","tolerationSeconds":300},...]
affinity:

NAME      STATUS                     ROLES           AGE   VERSION   DISKTYPE   ZONE
cp1       Ready                      control-plane   1y    v1.34.1
worker1   Ready                      <none>          1y    v1.34.1
worker2   Ready,SchedulingDisabled   <none>          1y    v1.34.1   ssd
```

**What it means:** the pod requires `disktype=ssd`, and the only node with that
label (worker2) is cordoned (`SchedulingDisabled`, someone ran `kubectl cordon`
for maintenance and forgot to `uncordon`).

**Why this step (now):** after resources, labels and taints are the next most
common exclusion, and both are visible in one screen.

**Next step:** `kubectl uncordon worker2` if maintenance is over, or label
another suitable node (`kubectl label node worker1 disktype=ssd`), or fix the
selector in the manifest.

#### Step 4 — When there are no events: check the scheduler

**Goal:** confirm the scheduler itself is alive.

```bash
kubectl -n NS get pod POD -o jsonpath='{.spec.schedulerName}{"\n"}'
kubectl -n kube-system get pods -l component=kube-scheduler -o wide
kubectl -n kube-system logs -l component=kube-scheduler --tail=20
```

```
default-scheduler
NAME                  READY   STATUS             RESTARTS      AGE
kube-scheduler-cp1    0/1     CrashLoopBackOff   6 (90s ago)   8m
```

**What it means:** the scheduler is a static pod and it is crashing, so nothing
gets scheduled and nobody writes events. A favourite CKA task: someone broke
`/etc/kubernetes/manifests/kube-scheduler.yaml` (a wrong flag, a wrong
kubeconfig path, a typo in the image). Fix it like the apiserver manifest in
section 10.

**Why this step (now):** "no events" is itself the evidence; it points away
from the pod and towards the control plane.

**Next step:** read the scheduler's logs (`crictl logs` on cp1 if kubectl logs
fail), fix the manifest, wait for it to be Running.

#### Decision tree: Pending

```
kubectl describe pod → Events
├── Insufficient cpu/memory → requests vs allocatable (describe node) → right-size / add node / quota
├── untolerated taint → cordoned? control-plane? pressure taint? → uncordon / toleration / fix node
├── node affinity/selector → node labels → label node or fix selector
├── unbound PVC → PVC Pending scenario
├── no events → kube-scheduler static pod / schedulerName
└── pod not even created → kubectl get rs / events: exceeded quota
```

**Fix & verify:** `kubectl -n NS get pod POD -o wide -w` shows a node name and
`ContainerCreating` → `Running`.

**Rollback:** revert the label/taint/request change (`kubectl label node worker1 disktype-`,
`kubectl cordon`), or `kubectl rollout undo` if you changed the Deployment.

**Prevent it next time:** set requests from measured usage, keep a node-label
convention in Git, and alert on pods Pending longer than 5 minutes.

---

### ImagePullBackOff and ErrImagePull

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: Docker vs ContainerD (crictl) ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page)) · 2) Note: "x509 unknown authority pulling from Harbor" in section 6 of this module · 3) Read: [Harbor docs](https://goharbor.io/docs/).

**Level:** [L3 · Senior] — registry auth and containerd trust on every node; the Harbor CA case in Kubernetes form.

**Symptom:** `ErrImagePull`, then `ImagePullBackOff`. The image is pulled by
**containerd on the node**, with the node's DNS, the node's trust store and the
pod's imagePullSecrets. CoreDNS and the pod's network play no part.

#### Step 1 — Read the pull error in the Events

**Goal:** get containerd's exact error text.

```bash
kubectl -n NS describe pod POD | sed -n '/^Events:/,$p'
```

```
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  2m                 default-scheduler  Successfully assigned shop/worker-5c7d8f9b6-q8w2n to worker1
  Normal   Pulling    52s (x4 over 2m)   kubelet            Pulling image "harbor.example.com/shop/worker:1.4.2"
  Warning  Failed     52s (x4 over 2m)   kubelet            Failed to pull image "harbor.example.com/shop/worker:1.4.2": failed to pull and unpack image "harbor.example.com/shop/worker:1.4.2": failed to resolve reference "harbor.example.com/shop/worker:1.4.2": failed to do request: Head "https://harbor.example.com/v2/shop/worker/manifests/1.4.2": tls: failed to verify certificate: x509: certificate signed by unknown authority
  Warning  Failed     52s (x4 over 2m)   kubelet            Error: ErrImagePull
  Normal   BackOff    13s (x7 over 2m)   kubelet            Back-off pulling image "harbor.example.com/shop/worker:1.4.2"
  Warning  Failed     13s (x7 over 2m)   kubelet            Error: ImagePullBackOff
```

**What it means:** worker1's containerd does not trust Harbor's private CA. The
messages you will meet:

| Message fragment | Cause | Next |
|---|---|---|
| `x509: certificate signed by unknown authority` | node does not trust Harbor's CA | Step 3, Step 4 |
| `401 Unauthorized`, `authorization failed`, `pull access denied` | no or wrong imagePullSecret, robot account lacks access | Step 2 |
| `not found`, `manifest unknown` | tag or repository does not exist (typo, CI did not push) | fix the image reference |
| `no match for platform in manifest` | image not built for the node's CPU architecture | build multi-arch |
| `lookup harbor.example.com on 127.0.0.53:53: no such host` | the **node** cannot resolve the registry | node DNS ([DNS](08-dns.md)) |
| `toomanyrequests` | Docker Hub rate limit | Harbor proxy cache project |
| `i/o timeout`, `context deadline exceeded` | firewall or proxy between node and registry | node network / containerd proxy settings |

**Why this step (now):** the event text is the raw containerd error; each row of
the table has a different fix on a different machine.

**Next step:** follow the table.

#### Step 2 — Check the imagePullSecret

**Goal:** make sure the pod presents valid credentials for exactly this registry host.

```bash
kubectl -n NS get pod POD -o jsonpath='{"secrets: "}{.spec.imagePullSecrets}{"\nserviceAccount: "}{.spec.serviceAccountName}{"\n"}'
kubectl -n NS get secret harbor-cred -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq '.auths | keys'
```

```
secrets: 
serviceAccount: default
Error from server (NotFound): secrets "harbor-cred" not found
```

**What it means:** the pod uses no pull secret, and the secret does not exist in
this namespace (secrets are namespaced; one in `default` does not help `shop`).
When the secret exists, the key under `auths` must match the registry host
exactly (`harbor.example.com`, plus `:PORT` if non-standard).

**Why this step (now):** authentication errors are the most common pull
failure with a private registry, and this check takes seconds.

**Next step:** create the secret with a Harbor robot account and attach it to the
ServiceAccount, so every pod in the namespace uses it:

```bash
# Leading space keeps the token out of shell history when HISTCONTROL=ignorespace (Ubuntu default: ignoreboth)
 kubectl -n NS create secret docker-registry harbor-cred \
   --docker-server=harbor.example.com --docker-username='robot$shop+k8s' --docker-password='TOKEN'
kubectl -n NS patch serviceaccount default -p '{"imagePullSecrets":[{"name":"harbor-cred"}]}'
kubectl -n NS rollout restart deploy/worker
```

#### Step 3 — Reproduce the pull on the node with crictl

**Goal:** see the raw error on the node, outside Kubernetes, and test fixes quickly.

```bash
kubectl -n NS get pod POD -o jsonpath='{.spec.nodeName}{"\n"}'
# on that node:
sudo crictl pull harbor.example.com/shop/worker:1.4.2
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com </dev/null 2>/dev/null | grep 'Verify return code'
```

```
worker1
E1003 11:20:14.551209   48211 remote_image.go:180] "PullImage from image service failed" err="rpc error: code = Unknown desc = failed to pull and unpack image \"harbor.example.com/shop/worker:1.4.2\": failed to resolve reference \"harbor.example.com/shop/worker:1.4.2\": failed to do request: Head \"https://harbor.example.com/v2/shop/worker/manifests/1.4.2\": tls: failed to verify certificate: x509: certificate signed by unknown authority" image="harbor.example.com/shop/worker:1.4.2"
Verify return code: 20 (unable to get local issuer certificate)
```

**What it means:** same error outside Kubernetes, so it is the node's trust, not
the manifest. (`crictl pull` without `--creds` only tests trust and network;
add `--creds 'USER:PASSWORD'` to test auth, minding your shell history.)

**Why this step (now):** testing on the node lets you iterate on the fix in
seconds instead of waiting for kubelet's back-off (up to 5 minutes).

**Next step:** → Step 4.

#### Step 4 — Make containerd trust Harbor's CA

**Goal:** install the CA where containerd's CRI plugin looks for registry config, on **every** node.

```bash
containerd --version
sudo containerd config dump | grep -n 'config_path'      # where CRI reads registry hosts from

sudo mkdir -p /etc/containerd/certs.d/harbor.example.com
sudo cp corp-root-ca.crt /etc/containerd/certs.d/harbor.example.com/ca.crt
sudo tee /etc/containerd/certs.d/harbor.example.com/hosts.toml >/dev/null <<'EOF'
server = "https://harbor.example.com"

[host."https://harbor.example.com"]
  capabilities = ["pull", "resolve"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
EOF

sudo crictl pull harbor.example.com/shop/worker:1.4.2
```

```
containerd containerd.io 2.1.4 ...
92:      config_path = '/etc/containerd/certs.d:/etc/docker/certs.d'

Image is up to date for sha256:4be1c0d9e8f7a6b5...
```

**What it means:** this containerd reads registry hosts from
`/etc/containerd/certs.d`, so the new `hosts.toml` applies immediately, without
a restart. If `config_path` is empty, set it in `/etc/containerd/config.toml`
and restart containerd (running containers keep running):

```toml
# containerd 2.x (config version 3)
[plugins.'io.containerd.cri.v1.images'.registry]
  config_path = '/etc/containerd/certs.d'

# containerd 1.6/1.7 (config version 2)
[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = "/etc/containerd/certs.d"
```

Adding the CA to the node's system store (`update-ca-certificates`, then
`systemctl restart containerd`) also works, but `certs.d` is scoped to Harbor
and needs no restart.

**Why this step (now):** you proved in Step 3 that trust is the problem; this is
the narrowest fix containerd supports.

**Next step:** roll it out to all nodes (Ansible), then `kubectl -n NS rollout restart deploy/worker`
or wait for the next kubelet retry.

#### Decision tree: image pull

```
describe pod → Failed to pull image ... : ERROR
├── x509 → crictl pull on that node → certs.d/HARBOR/hosts.toml + ca.crt on every node
├── 401 / denied → imagePullSecret in THIS namespace, key = registry host, robot account access
├── not found → tag/repository typo, CI push failed
├── no such host → node DNS (resolvectl on the node)
├── timeout → node firewall/proxy to registry
└── no match for platform → build for the node's arch
```

**Fix & verify:** `kubectl -n NS get pods -w` shows the pod going
`ContainerCreating` → `Running`; `kubectl -n NS describe pod POD` shows
`Successfully pulled image`.

**Rollback:** remove the `certs.d/HARBOR` directory or the secret/ServiceAccount
patch; restore `config.toml` from your backup and restart containerd.

**Prevent it next time**

- Distribute the CA and `hosts.toml` in the node bootstrap (Ansible) before nodes join.
- Use robot accounts with pull-only rights per cluster, and pin images by tag plus digest in production.
- Use a Harbor proxy-cache project for Docker Hub images so nodes never hit Hub's rate limits.

---

### CrashLoopBackOff

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Application Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure)) · 2) KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Crashing Pods, Ephemeral/Debug Containers ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 3) Note: "Container exits immediately or restart-loops" in section 2 (same exit codes).

**Level:** [L3 · Senior] — the most common CKA troubleshooting task; same exit codes as Docker.

**Symptom:** `CrashLoopBackOff` with a growing RESTARTS count. Kubernetes starts
the container, it exits, and kubelet waits longer each time (10 s, 20 s, 40 s …
up to 5 minutes) before the next try. Closely related:
`CreateContainerConfigError` (the container could not even be created).

#### Step 1 — Read the logs of the crashed container

**Goal:** read the last words of the previous run, not the current, empty one.

```bash
kubectl -n NS logs POD --previous --tail=50
kubectl -n NS logs POD -c CONTAINER --previous --tail=50      # multi-container pod
kubectl -n NS logs deploy/api --all-containers --prefix --tail=20
```

```
2026-10-03T11:31:03Z INFO  starting api 1.4.3
2026-10-03T11:31:04Z ERROR could not connect to database: dial tcp: lookup postgres on 10.96.0.10:53: no such host
2026-10-03T11:31:04Z FATAL exiting
```

**What it means:** the app exits because it cannot resolve `postgres`: the
database Service is in another namespace (it needs `postgres.data`) or is called
differently. Plain `kubectl logs` would show the current container, which may
have just started and printed nothing.

**Why this step (now):** `--previous` is the single most useful flag in
Kubernetes troubleshooting; it holds the log of the run that died.

**Next step:** If the log names the problem → fix it (config, Service name,
secret) and go to "Fix & verify". If the log is empty or the container was
killed → Step 2.

#### Step 2 — Read the last state, exit code and probe events

**Goal:** learn how it died: by itself, by OOM or by a probe.

```bash
kubectl -n NS describe pod POD | sed -n '/^Containers:/,/^Conditions:/p' | grep -E 'State|Reason|Exit Code|Started|Finished|Restart Count|Liveness|Readiness|Startup'
kubectl -n NS describe pod POD | sed -n '/^Events:/,$p' | tail -8
```

```
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    137
      Started:      Fri, 03 Oct 2026 11:31:02 +0000
      Finished:     Fri, 03 Oct 2026 11:31:34 +0000
    Restart Count:  9
    Liveness:       http-get http://:8080/healthz delay=5s timeout=1s period=10s #success=1 #failure=3

  Warning  Unhealthy  2m (x27 over 8m)   kubelet  Liveness probe failed: Get "http://10.244.1.17:8080/healthz": dial tcp 10.244.1.17:8080: connect: connection refused
  Normal   Killing    2m (x9 over 8m)    kubelet  Container api failed liveness probe, will be restarted
  Warning  BackOff    20s (x31 over 8m)  kubelet  Back-off restarting failed container api in pod api-6d9f7b8c5-mx2lq_shop(4b1e...)
```

**What it means:** the container ran 32 seconds and was killed (137) by kubelet
because the **liveness probe** failed 3 times: the app needs longer than
5 s + 3 × 10 s to start listening on 8080 (or listens on another port). How to
read Last State:

| Last State | Meaning | Next |
|---|---|---|
| Reason `Error`, exit 1/2 | app error | Step 1 logs, Step 3 config |
| Reason `OOMKilled`, exit 137 | memory limit hit | OOMKilled scenario below |
| exit 137 (or 143 if the app exits on SIGTERM) + "failed liveness probe" events | kubelet killed it | fix the probe: startupProbe, right port, longer timeout |
| Reason `Completed`, exit 0 | the process finished; a Deployment expects it to run forever | wrong command, or it should be a Job |
| exit 126 / 127 | command not executable / not found | Step 4 |
| `CreateContainerConfigError` | `configmap "X" not found`, `secret "Y" not found`, `couldn't find key K` | Step 3 |

**Why this step (now):** the logs say what the app thought; the last state says
what actually ended it. A probe kill leaves no error in the app's log at all.

**Next step:** follow the table.

#### Step 3 — Check the config the pod references

**Goal:** confirm every ConfigMap, Secret and key the pod expects exists in its namespace.

```bash
kubectl -n NS get pod POD -o jsonpath='{range .spec.containers[*]}{.name}{": "}{.command}{" "}{.args}{"\n"}{end}'
kubectl -n NS get pod POD -o yaml | grep -E -A2 'configMapKeyRef|secretKeyRef|configMapRef|secretRef'
kubectl -n NS get configmap,secret
```

```
api: ["/app/api"] ["--port=8080"]
        secretKeyRef:
          key: DATABASE_URL
          name: api-db
NAME                         DATA   AGE
configmap/api-config         3      5d
configmap/kube-root-ca.crt   1      90d
secret/harbor-cred           1      5d
```

**What it means:** the pod needs secret `api-db` with key `DATABASE_URL`, and
there is no `api-db` in this namespace: `CreateContainerConfigError`. Note:
changing a ConfigMap or Secret later does not update environment variables of
running pods; they need a restart (`kubectl rollout restart`).

**Why this step (now):** missing configuration is the most common startup
failure after a namespace or environment is created by hand.

**Next step:** create the missing object (from your secret store or Git),
then `kubectl -n NS rollout restart deploy/api`.

#### Step 4 — Debug inside a copy of the pod

**Goal:** get a shell with the same image, env and volumes, without the crashing command or the probes.

```bash
# A copy whose container runs sh instead of the app; labels and probes are dropped by default,
# so the copy receives no Service traffic and is not killed by liveness
kubectl -n NS debug POD -it --copy-to=api-debug --container=api -- sh
#   inside: env | sort ; ls -l /app ; /app/api --port=8080   (run the real command by hand)
kubectl -n NS delete pod api-debug          # clean up the copy when done

# A running pod with no shell (distroless): attach an ephemeral debug container
kubectl -n NS debug -it POD --image=nicolaka/netshoot --target=api
```

```
If you don't see a command prompt, try pressing enter.
/app $ /app/api --port=8080
2026-10-03T11:42:10Z INFO  starting api 1.4.3
2026-10-03T11:42:10Z FATAL open /app/config/settings.yaml: no such file or directory
/app $ ls /app/config /etc/api
ls: /app/config: No such file or directory
/etc/api:
settings.yaml
```

**What it means:** inside the copy you can run the real command by hand and see
the error the way you did with `docker run --entrypoint sh` (section 2). In this
sample the app expects `/app/config/settings.yaml`, but the ConfigMap volume is
mounted at `/etc/api`: fix the `volumeMounts.mountPath` (or the app's config
path), not the image.

**Why this step (now):** last, because Steps 1–3 solve most cases without
creating anything in the cluster.

**Next step:** fix the image or manifest, redeploy.

#### Decision tree: CrashLoopBackOff

```
kubectl logs --previous
├── clear error → config / dependency / Service name (svc.namespace) → fix → rollout restart
└── empty or unclear → describe: Last State
    ├── OOMKilled 137 → OOMKilled scenario
    ├── 137 + liveness failed → startupProbe / probe port / timeout
    ├── Completed 0 → command ends → fix command or use a Job
    ├── 126/127 → kubectl debug --copy-to ... -- sh → path, x bit, arch
    └── CreateContainerConfigError → missing ConfigMap/Secret/key in this namespace
```

**Fix & verify**

```bash
kubectl -n NS rollout status deploy/api --timeout=180s
kubectl -n NS get pods -l app=api -w        # RESTARTS stays put, READY 1/1
```

**Rollback:** `kubectl -n NS rollout undo deploy/api` (or revert the commit in
Git if a GitOps tool manages the cluster; otherwise it re-applies the bad version).

**Prevent it next time**

- Use a `startupProbe` for slow starters; keep liveness simple (is the process alive), never dependent on the database.
- Validate manifests in CI (`kubectl apply --dry-run=server`), and create Secrets from a secret manager, not by hand.
- Refer to Services in other namespaces as `NAME.NAMESPACE` (or the full `NAME.NAMESPACE.svc.cluster.local`).

---

### OOMKilled in Kubernetes

> 📚 **Know this first:** 1) Note: "OOMKilled and exit code 137" in section 2 · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Scheduling: resource requirements and limits ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Note: [Memory reference](04-memory.md).

**Level:** [L3 · Senior] — requests, limits and QoS classes decide who gets killed.

**Symptom:** `Last State: Terminated, Reason: OOMKilled, Exit Code: 137`,
restarts under load.

#### Step 1 — Confirm the OOM kill and see the limit

**Goal:** prove it was the memory limit, and find what limit applied.

```bash
kubectl -n NS get pod POD -o jsonpath='{range .status.containerStatuses[*]}{.name}{" "}{.lastState.terminated.reason}{" "}{.lastState.terminated.exitCode}{"\n"}{end}'
kubectl -n NS get pod POD -o jsonpath='{range .spec.containers[*]}{.name}{" "}{.resources}{"\n"}{end}'
kubectl -n NS get pod POD -o jsonpath='{.status.qosClass}{"\n"}'
kubectl -n NS describe limitrange
```

```
api OOMKilled 137
api {"limits":{"memory":"512Mi"},"requests":{"cpu":"100m","memory":"512Mi"}}
Burstable
Name:       defaults
Namespace:  shop
Type        Resource  Min  Max  Default Request  Default Limit  Max Limit/Request Ratio
----        --------  ---  ---  ---------------  -------------  -----------------------
Container   memory    -    -    512Mi            512Mi          -
```

**What it means:** the developer set **no** memory limit, but the namespace's
LimitRange injected a default of 512Mi, and the app needs more. Without the
LimitRange check you would search the Deployment for a limit that is not there.

**Why this step (now):** the limit you are hitting may not be in your manifest.

**Next step:** → Step 2 for real usage.

#### Step 2 — Measure real usage over time

**Goal:** choose a limit from data.

```bash
kubectl -n NS top pod -l app=api --containers
# on the node that ran it, the kernel's record of the kill:
sudo journalctl -k --since '1 hour ago' | grep -iE 'oom-kill|killed process'
```

```
POD                   NAME   CPU(cores)   MEMORY(bytes)
api-6d9f7b8c5-mx2lq   api    220m         498Mi
api-6d9f7b8c5-p4k7d   api    190m         505Mi
```

**What it means:** both pods live at the edge of 512Mi. Whether the right answer
is a higher limit or a fix in the app follows the same leak / spike / runtime
sizing logic as the Docker OOMKilled scenario (section 2, Step 3): JVM heap,
Node.js heap and worker counts must be sized to the **container** limit.

**Why this step (now):** the limit should be measured peak plus headroom, not a guess.

**Next step:** set memory `requests` equal to `limits` (memory cannot be
throttled, only killed, so overcommitting it causes surprise kills on busy
nodes), tune the runtime, and roll out.

#### Decision tree: OOMKilled in Kubernetes

```
Last State OOMKilled 137
├── limit from LimitRange default? → set explicit resources
├── usage near limit from the start → runtime sizing (heap, workers)
├── slow climb → leak → fix app; temporary higher limit
└── node-wide OOM (journalctl -k, CONSTRAINT_NONE) → node overcommitted → requests = limits for memory
```

**Fix & verify:** `kubectl -n NS rollout status deploy/api`, then
`kubectl -n NS get pods -l app=api` shows RESTARTS no longer increasing over an
hour of normal load, and `kubectl top` stays below ~80% of the limit.

**Rollback:** `kubectl -n NS rollout undo deploy/api`.

**Prevent it next time:** explicit resources on every container, a reviewed
LimitRange per namespace, and alerts on container memory near its limit.

---

### Evicted pods and DiskPressure

> 📚 **Know this first:** 1) Note: "Docker filled the disk" in section 5 · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Worker Node Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure)) · 3) Note: [Storage & disk reference](01-storage-disk.md).

**Level:** [L3 · Senior] — kubelet eviction thresholds on top of the Docker disk-full skills.

**Symptom:** pods in status `Evicted` (phase Failed), often many at once on one
node, and new pods not scheduling there.

#### Step 1 — Read why the pods were evicted

**Goal:** get the resource and the node.

```bash
kubectl get pods -A -o wide | grep -i evicted | head
kubectl -n NS describe pod POD | grep -E '^(Status|Reason|Message|Node):'
```

```
shop   api-6d9f7b8c5-zz9kd   0/1   Evicted   0   14m   <none>   worker2

Node:     worker2/192.0.2.22
Status:   Failed
Reason:   Evicted
Message:  The node was low on resource: ephemeral-storage. Threshold quantity: 4026531840, available: 3412004Ki. Container api was using 6820Ki, request is 0, has larger consumption of ephemeral-storage.
```

**What it means:** kubelet on worker2 ran low on node disk (`ephemeral-storage`
= the filesystem under `/var/lib/kubelet` and container logs) and evicted pods to
protect the node. Unlike an OOM kill, eviction is kubelet acting proactively.
Default hard thresholds on Linux nodes: `memory.available<100Mi`,
`nodefs.available<10%`, `imagefs.available<15%`, `nodefs.inodesFree<5%`,
`imagefs.inodesFree<5%`.

**Why this step (now):** the message names the resource; the fix for disk is
completely different from the fix for memory.

**Next step:** → Step 2 on that node.

#### Step 2 — Check the node's conditions and disk

**Goal:** find what is filling the node.

```bash
kubectl describe node worker2 | sed -n '/^Conditions:/,/^Addresses:/p' | grep -E 'Type|Pressure|Ready'
# on worker2:
df -h / /var/lib/containerd /var/lib/kubelet ; df -i /
sudo du -xh --max-depth=1 /var/lib/containerd /var/log 2>/dev/null | sort -h | tail -6
sudo du -sh /var/log/pods/* 2>/dev/null | sort -h | tail -3
sudo crictl images | wc -l
```

```
  Type             Status  ... Reason                       Message
  MemoryPressure   False   ... KubeletHasSufficientMemory   kubelet has sufficient memory available
  DiskPressure     True    ... KubeletHasDiskPressure       kubelet has disk pressure
  Ready            True    ... KubeletReady                 kubelet is posting ready status

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        40G   37G  3.3G  92% /

14G     /var/lib/containerd
9.6G    /var/log
8.9G    /var/log/pods/shop_api-6d9f7b8c5-p4k7d_1f2e.../
```

**What it means:** `DiskPressure True`, which also adds a
`node.kubernetes.io/disk-pressure:NoSchedule` taint. One pod writes 8.9 GB of
logs under `/var/log/pods` (debug logging left on), and images take 14 GB.

**Why this step (now):** eviction only relieves the symptom; the node will hit
the threshold again until you remove the cause.

**Next step:** reduce the chatty app's logging, then reclaim space (Fix & verify).

#### Decision tree: Evicted

```
describe evicted pod → Message: low on resource X
├── ephemeral-storage / nodefs → node: /var/log/pods, emptyDir, images → fix the writer, prune images
├── imagefs → crictl rmi --prune, image GC thresholds
├── memory → requests too low vs real use → right-size, requests = limits
└── inodes → many small files (df -i) → find the writer
```

**Fix & verify**

```bash
# on the node: remove images no container uses (re-pullable from the registry)
sudo crictl rmi --prune
# clean up the Failed pod records AFTER reading them (they hold no resources, only evidence):
kubectl get pods -A --field-selector=status.phase=Failed
kubectl -n NS delete pods --field-selector=status.phase=Failed
kubectl describe node worker2 | grep DiskPressure        # False after kubelet re-evaluates
```

> ⚠️ Deleting by `status.phase=Failed` also removes failed Job pods you may
> still want to investigate. List first, delete per namespace.

**Rollback:** nothing to roll back; pruned images are pulled again on demand.

**Prevent it next time:** set `ephemeral-storage` requests/limits for chatty
workloads, keep kubelet's `containerLogMaxSize`/`containerLogMaxFiles` sane,
give `/var/lib/containerd` its own disk, and alert on node disk at 80%.

---

## 9. Kubernetes: Services, Ingress and DNS

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: Prerequisite DNS, CoreDNS in Kubernetes, Ingress ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page)) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Services: Troubleshooting Internal Networking ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page)) · 3) Note: [Learn Kubernetes](31-learn-kubernetes.md) (Services, Ingress, cluster DNS, NetworkPolicies) · 4) Read: [Kubernetes docs: Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) · 5) Practice: *Kubernetes Troubleshooting for Application Developers* — Unreachable Pods + Leaky Network Policies, What the Ingress? ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)).

Traffic path inside the cluster, which these scenarios walk from right to left:

```
client → Ingress controller (or Gateway) → Service (ClusterIP, kube-proxy rules) → EndpointSlice (READY pod IPs) → pod:targetPort
                                                   ↑ name resolved by CoreDNS (kube-dns Service, 10.96.0.10)
```

### Readiness fails so the Service has no endpoints

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Application Developer (CKAD)* — Observability: readiness and liveness probes ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Application Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure)) · 3) Note: [Learn Kubernetes](31-learn-kubernetes.md) (Services).

**Level:** [L3 · Senior] — probes, endpoints and Services: the link between "Running" and "reachable".

**Symptom:** pods are `Running` but `READY 0/1`; the Service returns connection
refused or the Ingress returns 503.

#### Step 1 — Look at readiness and the endpoint list together

**Goal:** confirm the Service has no **ready** backends.

```bash
kubectl -n NS get pods -l app=api -o wide
kubectl -n NS get endpointslices -l kubernetes.io/service-name=api \
  -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{"  ready="}{.conditions.ready}{"\n"}{end}'
kubectl -n NS get endpoints api        # older view; prints a deprecation warning on v1.33+
```

```
NAME                  READY   STATUS    RESTARTS   AGE   IP            NODE
api-6d9f7b8c5-mx2lq   0/1     Running   0          9m    10.244.1.17   worker1
api-6d9f7b8c5-p4k7d   0/1     Running   0          9m    10.244.2.31   worker2

10.244.1.17  ready=false
10.244.2.31  ready=false

Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME   ENDPOINTS   AGE
api                9m
```

**What it means:** the Service selects both pods (they appear in the
EndpointSlice) but neither is ready, so the Service has nothing to send traffic
to. If the EndpointSlice had **no** entries at all, the selector would match no
pods → next scenario.

**Why this step (now):** it separates "pods not ready" from "Service selects the
wrong pods", which have different fixes.

**Next step:** → Step 2 to see why readiness fails.

#### Step 2 — Read the readiness probe failures

**Goal:** get the exact probe error.

```bash
kubectl -n NS describe pod api-6d9f7b8c5-mx2lq | grep -E 'Readiness|Unhealthy' | tail -4
```

```
    Readiness:      http-get http://:8080/ready delay=0s timeout=1s period=5s #success=1 #failure=3
  Warning  Unhealthy  12s (x110 over 9m)  kubelet  Readiness probe failed: HTTP probe failed with statuscode: 503
```

**What it means:** the app answers on 8080 but its `/ready` endpoint returns
HTTP 503. Other common texts:

| Probe message | Cause |
|---|---|
| `HTTP probe failed with statuscode: 503` | the app itself reports not ready (often a dependency check) |
| `connect: connection refused` | wrong probe port, or the app listens on 127.0.0.1 or another port |
| `context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | the endpoint is slower than `timeoutSeconds` (default 1 s) |
| `HTTP probe failed with statuscode: 404` | wrong probe path |

**Why this step (now):** kubelet records every failed probe with the reason;
no need to guess between port, path and timeout.

**Next step:** → Step 3 to call the endpoint yourself.

#### Step 3 — Call the probe endpoint yourself

**Goal:** see the response body the probe gets.

```bash
kubectl -n NS exec api-6d9f7b8c5-mx2lq -- wget -qO- -T 2 http://127.0.0.1:8080/ready
# image without wget/curl: an ephemeral debug container in the same pod
kubectl -n NS debug -it api-6d9f7b8c5-mx2lq --image=nicolaka/netshoot --target=api -- curl -s -m2 http://127.0.0.1:8080/ready
```

```
{"status":"not ready","checks":{"database":"timeout after 1000ms","cache":"ok"}}
```

**What it means:** readiness depends on the database, which times out. All pods
share the same database, so all of them go unready together and the whole
Service disappears. That may be intended, but often a liveness or readiness
check that depends on a shared dependency turns a database blip into a full
outage.

**Why this step (now):** the body explains what the status code only hints at.

**Next step:** fix the dependency (DB reachable? NetworkPolicy? DNS?), or adjust
the probe: right port/path, `timeoutSeconds: 3`, and a readiness check that
reflects "can this pod serve" rather than "is everything downstream perfect".

#### Decision tree: no ready endpoints

```
EndpointSlice for the Service
├── empty → selector matches no pods → next scenario
└── addresses with ready=false → describe pod: Readiness probe failed
    ├── refused → probe port / app bind address
    ├── 404 → probe path
    ├── timeout → timeoutSeconds, slow endpoint
    └── 503 → app says not ready → call it, read the body → fix dependency or probe design
```

**Fix & verify:** the EndpointSlice shows `ready=true` addresses and
`kubectl -n NS get pods` shows `1/1`; a request through the Service succeeds
(Step 3 of the next scenario).

**Rollback:** `kubectl -n NS rollout undo deploy/api` if the probe change made it worse.

**Prevent it next time:** review probes in merge requests (port, path, timeout),
keep liveness independent of dependencies, and alert when a Deployment has fewer
ready replicas than desired for 5 minutes.

---

### Service selector, port or targetPort mismatch

> 📚 **Know this first:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — Services ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Troubleshooting Internal Networking ([notes](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page)) · 3) Note: [Kubernetes reference](15-kubernetes.md).

**Level:** [L3 · Senior] — labels, selectors and the three port fields, a classic CKA trap.

**Symptom:** pods are `1/1 Ready`, but requests to the Service time out or are
refused, or the EndpointSlice is empty.

#### Step 1 — Compare the Service selector with the pod labels

**Goal:** check the Service actually selects your pods.

```bash
kubectl -n NS get svc api -o jsonpath='selector={.spec.selector}{"\n"}{range .spec.ports[*]}port {.port} -> targetPort {.targetPort}{"\n"}{end}'
kubectl -n NS get pods -l app=web-api                 # pods matching the Service's selector
kubectl -n NS get pods --show-labels | head -4        # the labels the pods really have
```

```
selector={"app":"web-api"}
port 80 -> targetPort 8080
No resources found in shop namespace.

NAME                  READY   STATUS    RESTARTS   AGE   LABELS
api-6d9f7b8c5-mx2lq   1/1     Running   0          12m   app=webapi,pod-template-hash=6d9f7b8c5
```

**What it means:** the Service selects `app=web-api`; the pods are labelled
`app=webapi`. One character, zero endpoints.

**Why this step (now):** a selector mismatch is the number one Service problem
and it is invisible from the pod side.

**Next step:** If no pods match → fix the selector (or the labels) in the
manifest. If pods match → Step 2.

#### Step 2 — Compare targetPort with the container's listener

**Goal:** make sure the Service forwards to a port the app actually serves.

```bash
kubectl -n NS get pod POD -o jsonpath='{range .spec.containers[*].ports[*]}{.name} {.containerPort}{"\n"}{end}'
kubectl -n NS debug -it POD --image=nicolaka/netshoot --target=api -- ss -ltn
```

```
http 8080

State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
LISTEN  0       511           0.0.0.0:3000       0.0.0.0:*
```

**What it means:** the Service sends to 8080 and the pod spec even declares
8080, but the app listens on **3000**. `containerPort` is documentation; it does
not change where the app listens. A named `targetPort: http` must match a
`ports[].name` in the pod, or the EndpointSlice will not get that port.

**Why this step (now):** with endpoints present but `connection refused`, the
listener is the next thing to check, exactly like the Traefik 502 case.

**Next step:** fix `targetPort` (or the app's port) and test with Step 3.

#### Step 3 — Test each hop from inside the cluster

**Goal:** find the first hop that fails: pod IP, ClusterIP, DNS name.

```bash
kubectl -n NS run nettest --rm -it --restart=Never --image=nicolaka/netshoot -- sh -c '
  curl -s -m3 -o /dev/null -w "pod IP     %{http_code}\n" http://10.244.1.17:3000/ ;
  curl -s -m3 -o /dev/null -w "ClusterIP  %{http_code}\n" http://10.96.112.40:80/ ;
  curl -s -m3 -o /dev/null -w "DNS name   %{http_code}\n" http://api.shop.svc.cluster.local/'
```

```
pod IP     200
ClusterIP  000
DNS name   000
```

**What it means:** the pod works directly; the Service path fails (`000` = no
HTTP response). With the selector and targetPort now correct, a failing
ClusterIP points at kube-proxy or the CNI on that node:
`kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide` and its logs.
Note that `kubectl port-forward svc/api` connects straight to one pod and
**bypasses** kube-proxy, so it can work while the Service is broken.

**Why this step (now):** testing hop by hop names the broken layer instead of
"the Service doesn't work".

**Next step:** if only the DNS name fails → "Pod cannot resolve Service names" below.

#### Decision tree: Service

```
kubectl get pods -l SELECTOR
├── none → selector/label mismatch → fix manifest
└── pods match
    ├── not ready → previous scenario
    └── ready → curl pod IP:targetPort
        ├── fails → app port/bind (ss -ltn) vs targetPort (named ports!)
        └── works → curl ClusterIP
            ├── fails → kube-proxy / CNI on the node
            └── works → curl DNS name → fails → DNS scenario
```

**Fix & verify:** the EndpointSlice lists the pod IPs with the right port, and
all three lines of Step 3 print 200.

**Rollback:** re-apply the previous Service manifest from Git.

**Prevent it next time:** use the same label set (for example
`app.kubernetes.io/name`) generated by one template or Helm/Kustomize for
Deployment and Service; use named ports; add a post-deploy check that the
Service has ready endpoints.

---

### Ingress returns 404, 502 or 503

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: Ingress ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page)) · 2) Note: "Traefik returns 404" and "Traefik returns 502" in section 7 · 3) Practice: *Kubernetes Troubleshooting for Application Developers* — What the Ingress? ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)).

**Level:** [L3 · Senior] — the Traefik 404/502 skills from section 7, the Kubernetes way.

**Symptom:** the site behind an Ingress returns 404, 502, 503 or 504. The status
code already tells you which layer to check.

#### Step 1 — Inspect the Ingress, its class and its backends

**Goal:** see whether a controller claimed the Ingress and which backends it resolved.

```bash
kubectl get ingressclass
kubectl -n NS get ingress
kubectl -n NS describe ingress shop | sed -n '/^Rules:/,/^Annotations:/p'
```

```
NAME    CONTROLLER                     PARAMETERS   AGE
nginx   k8s.io/ingress-nginx           <none>       200d

NAME   CLASS    HOSTS              ADDRESS   PORTS     AGE
shop   <none>   shop.example.com             80, 443   12m

Rules:
  Host              Path  Backends
  ----              ----  --------
  shop.example.com
                    /   api:80 (<error: services "api" not found>)
```

**What it means:** two problems: `CLASS <none>` and an empty `ADDRESS` mean no
controller picked up this Ingress (no `ingressClassName`, and no class is marked
default); and the backend Service `api` does not exist **in this namespace** (an
Ingress can only point to Services in its own namespace). Healthy output shows a
class, an address and `api:80 (10.244.1.17:3000,10.244.2.31:3000)`.

**Why this step (now):** `describe ingress` resolves the backends for you,
including the endpoints, in one screen.

**Next step:** fix class and backend if broken; otherwise → Step 2 with the status code.

#### Step 2 — Map the status code to the layer

**Goal:** turn the code into the next check.

```bash
# The code, then the page itself: who generated it, the controller or the app?
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.21:30080/
curl -s -H 'Host: shop.example.com' http://192.0.2.21:30080/ | head -6
```

```
503
<html>
<head><title>503 Service Temporarily Unavailable</title></head>
<body>
<center><h1>503 Service Temporarily Unavailable</h1></center>
<hr><center>nginx</center>
</body>
```

**What it means:** the bare page with an `nginx` footer was written by the
ingress controller itself, not by your app, so the request never reached a pod.
For ingress-nginx a 503 means "no ready endpoints behind this backend". An
app-generated error page (your framework's styling, a JSON body) means routing
worked and the app answered. Map any code with this table:

| Code and page | Meaning | Check |
|---|---|---|
| 404 from the controller (nginx "404 Not Found", Traefik "404 page not found") | no Ingress rule matched host/path | host spelling, `pathType` (Exact vs Prefix), `ingressClassName`, namespace |
| 404 from the app | routing works; the app does not know that path | rewrite annotations, app routes |
| 503 | the backend Service has **no ready endpoints** | readiness scenario above |
| 502 | endpoints exist, connection to the pod fails | targetPort / bind address (Service scenario), or HTTPS backend spoken as HTTP |
| 504 | the pod accepted but answered too slowly | app performance, proxy timeouts |

**Why this step (now):** each code points to one layer; skipping this sends
people to the controller logs for a selector typo.

**Next step:** → Step 3 for the controller's own view.

#### Step 3 — Read controller logs, test around the Ingress

**Goal:** see the upstream error and prove the Service works without the Ingress.

```bash
kubectl -n ingress-nginx logs deploy/ingress-nginx-controller --tail=30 | grep -E ' 50[234] |upstream|error'
# Bypass Ingress AND Service: talk to one pod on the port the app really listens on
kubectl -n NS port-forward pod/POD 8081:3000 &
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/
kill %1
# Through the controller with the right Host header (NodePort or LoadBalancer IP)
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://192.0.2.21:30080/
```

```
2026/10/03 12:01:44 [error] 812#812: *40412 connect() failed (111: Connection refused) while connecting to upstream, client: 10.244.0.1, server: shop.example.com, request: "GET / HTTP/1.1", upstream: "http://10.244.1.17:8080/", host: "shop.example.com"
200
502
```

**What it means:** the controller connects to the pod on **8080** (the Service's
targetPort) and is refused, while the same pod answers 200 on **3000**. The app
is healthy; the Service sends traffic to the wrong port (the targetPort mismatch
from the Service scenario). A plain `kubectl port-forward svc/api` would have
failed too, because it follows the Service's targetPort.

**Why this step (now):** the controller log names the exact upstream IP and
port; port-forward proves the app is fine on its own.

**Next step:** fix the Service/targetPort, then re-test through the controller.

> 💡 The community ingress-nginx controller has been retired upstream; new
> clusters move to other controllers or the **Gateway API**. Many clusters and
> CKA labs still run it, and the reasoning above is the same everywhere. With
> the Gateway API, `kubectl describe httproute NAME` shows conditions such as
> `Accepted` and `ResolvedRefs`; `BackendNotFound` or `RefNotPermitted` (a
> cross-namespace backend without a ReferenceGrant) are the usual culprits.

#### Decision tree: Ingress

```
status code
├── 404 controller page → describe ingress: class? host? path type? same namespace?
├── 503 → Service has no ready endpoints → readiness scenario
├── 502 → controller log: upstream IP:port refused → targetPort / bind / backend protocol
├── 504 → slow app / timeouts
└── no response at all → controller pods, its Service (NodePort/LB), firewall, DNS → site-down playbook
```

**Fix & verify:** `curl -sI -H 'Host: shop.example.com' http://INGRESS_IP/`
returns the app's status, and `describe ingress` shows a class, an address and
backends with pod IPs.

**Rollback:** re-apply the previous Ingress/Service manifests from Git.

**Prevent it next time:** always set `ingressClassName`, keep Ingress and Service
in the same template, and smoke-test the hostname after each deploy.

---

### Pod cannot resolve Service names

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: CoreDNS in Kubernetes ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page)) · 2) Read: [Kubernetes docs: Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) · 3) Note: "DNS fails inside a container" in section 4.

**Level:** [L3 · Senior] — cluster DNS, search domains and ndots, on top of the L2 DNS skills.

**Symptom:** `nslookup: can't resolve`, `NXDOMAIN`, `Name or service not known`,
`lookup postgres on 10.96.0.10:53: no such host` inside a pod.

#### Step 1 — Test from a pod in the same namespace

**Goal:** reproduce with the same search domains the app has.

```bash
kubectl -n NS run dnstest --rm -it --restart=Never --image=nicolaka/netshoot -- sh -c '
  cat /etc/resolv.conf;
  nslookup billing-api;
  nslookup billing-api.billing;
  nslookup kubernetes.default'
```

```
search shop.svc.cluster.local svc.cluster.local cluster.local corp.example.com
nameserver 10.96.0.10
options ndots:5

Server:     10.96.0.10
Address:    10.96.0.10#53
** server can't find billing-api: NXDOMAIN

Name:   billing-api.billing.svc.cluster.local
Address: 10.96.44.12

Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```

**What it means:** DNS works; the name was wrong. A short name only resolves in
the pod's **own** namespace (`shop.svc.cluster.local` is the first search
domain). `billing-api` lives in namespace `billing`, so the app must use
`billing-api.billing` (or the full `billing-api.billing.svc.cluster.local`).
If instead every lookup says `connection timed out; no servers could be reached`,
CoreDNS is unreachable → Step 2.

**Why this step (now):** the [Kubernetes DNS debugging guide](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)
starts exactly here: a known-good name (`kubernetes.default`), the name that
fails, and the pod's resolv.conf.

**Next step:** If names are wrong → fix the app config. If timeouts → Step 2.
If cluster names work but external names fail → Step 3. If lookups are just
slow → Step 4.

#### Step 2 — Check CoreDNS and the kube-dns Service

**Goal:** make sure the DNS server pods are running and reachable.

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns -o wide
kubectl -n kube-system get svc kube-dns
kubectl -n kube-system get endpointslices -l kubernetes.io/service-name=kube-dns
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=20
kubectl -n NS get networkpolicy
```

```
NAME                       READY   STATUS             RESTARTS      AGE
coredns-7c65d6cfc9-4xkqp   0/1     CrashLoopBackOff   9 (2m ago)    25m
coredns-7c65d6cfc9-9hmzt   0/1     CrashLoopBackOff   9 (2m ago)    25m

[FATAL] plugin/loop: Loop (127.0.0.1:43264 -> :53) detected for zone ".", see https://coredns.io/plugins/loop#troubleshooting. Query: "HINFO 4547991504243258144.3688648895315093531."
```

**What it means:** CoreDNS crashes with a forwarding loop → next scenario. Other
outcomes: CoreDNS healthy but a NetworkPolicy in the namespace blocks port 53
(→ NetworkPolicy scenario), or kube-proxy/CNI broken so the 10.96.0.10 ClusterIP
does not work (test the CoreDNS pod IP directly: `nslookup kubernetes.default POD_IP`).

**Why this step (now):** once the name is right, the server is the next layer.

**Next step:** follow what you found.

#### Step 3 — External names fail, cluster names work

**Goal:** check where CoreDNS forwards non-cluster names.

```bash
kubectl -n kube-system get configmap coredns -o jsonpath='{.data.Corefile}'
# on a node:
cat /run/systemd/resolve/resolv.conf
```

```
.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30 {
       disable success cluster.local
       disable denial cluster.local
    }
    loop
    reload
    loadbalance
}
```

(This is the current kubeadm default; clusters created with older kubeadm
versions may show a plain `cache 30` line.)

**What it means:** CoreDNS forwards everything outside `cluster.local` to the
servers in the resolv.conf that kubelet gave it, i.e. the node's upstreams. If
those cannot answer (wrong, unreachable, or no internal zones), external lookups
fail. To watch queries, add the `log` plugin to the Corefile for a few minutes
(the `reload` plugin applies changes within a minute or two), then remove it.

**Why this step (now):** the Corefile is the only place that decides forwarding.

**Next step:** fix the node's upstream DNS, or forward explicitly:
`forward . 192.0.2.53 192.0.2.54`.

#### Step 4 — Slow lookups and ndots

**Goal:** understand the extra queries that `ndots:5` causes.

```bash
kubectl -n shop exec deploy/api -- cat /etc/resolv.conf
# Show every query the resolver tries for one external name (dig follows the search list with +search)
kubectl -n shop run dnstest --rm -it --restart=Never --image=nicolaka/netshoot -- \
  sh -c "dig +search +showsearch api.partner.example.com | grep -E 'status:|^;api'"
```

```
search shop.svc.cluster.local svc.cluster.local cluster.local corp.example.com
nameserver 10.96.0.10
options ndots:5

;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 40211
;api.partner.example.com.shop.svc.cluster.local. IN A
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 7710
;api.partner.example.com.svc.cluster.local. IN A
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 52307
;api.partner.example.com.cluster.local. IN A
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 1934
;api.partner.example.com.corp.example.com. IN A
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 61522
;api.partner.example.com.	IN	A
pod "dnstest" deleted
```

**What it means:** four NXDOMAIN answers come back before the real name is
even asked; the pod inherited the node's `corp.example.com` search domain on
top of the three cluster ones. With `ndots:5`, a name with fewer than five dots (like `api.partner.example.com`)
is first tried with every search domain: `api.partner.example.com.shop.svc.cluster.local`,
`...svc.cluster.local`, `...cluster.local`, `...corp.example.com`, and only then
as-is. That is up to four NXDOMAIN round trips (times two for A and AAAA) per
lookup. Fixes: use a trailing dot (`api.partner.example.com.`) in config, or lower
ndots for that workload:

```yaml
spec:
  dnsConfig:
    options:
      - name: ndots
        value: "2"
```

**Why this step (now):** it explains latency that looks like a slow network.

**Next step:** measure with `curl -w '%{time_namelookup}'` before and after.

#### Decision tree: DNS in a pod

```
nslookup kubernetes.default from a pod
├── fails (timeout) → CoreDNS pods? → loop / crash → next scenario
│                    → NetworkPolicy blocking 53? → NetworkPolicy scenario
│                    → ClusterIP 10.96.0.10 broken → kube-proxy / CNI
└── works
    ├── short name NXDOMAIN → other namespace → NAME.NAMESPACE
    ├── external names fail → Corefile forward → node upstreams
    └── slow → ndots:5 search expansion → FQDN with trailing dot / dnsConfig ndots
```

**Fix & verify:** from a fresh pod, `nslookup NAME.NAMESPACE` and an external
name both answer in well under a second.

**Rollback:** restore the CoreDNS ConfigMap from your copy
(`kubectl -n kube-system get cm coredns -o yaml > /root/coredns-cm.yaml` before
editing).

**Prevent it next time:** always address other namespaces as `NAME.NAMESPACE`,
monitor CoreDNS (its `prometheus :9153` metrics), and back up the Corefile before edits.

---

### CoreDNS CrashLoopBackOff with loop detected

> 📚 **Know this first:** 1) Read: [CoreDNS: loop plugin](https://coredns.io/plugins/loop) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: Prerequisite DNS ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Prerequisite-DNS)) · 3) Note: [DNS reference](08-dns.md) (systemd-resolved and 127.0.0.53).

**Level:** [L3 · Senior] — a node-level resolver problem that breaks the whole cluster; on the Ops Ladder case list.

**Symptom:** CoreDNS pods in CrashLoopBackOff, log line
`[FATAL] plugin/loop: Loop (127.0.0.1:NNNNN -> :53) detected for zone "."`.
Typical on Ubuntu nodes with systemd-resolved or a local dnsmasq.

#### Step 1 — Confirm the loop in the logs

**Goal:** make sure it is the loop plugin, not another crash.

```bash
kubectl -n kube-system logs -l k8s-app=kube-dns --previous --tail=3
```

```
[INFO] plugin/reload: Running configuration SHA512 = 1b226df79860...
[FATAL] plugin/loop: Loop (127.0.0.1:43264 -> :53) detected for zone ".", see https://coredns.io/plugins/loop#troubleshooting. Query: "HINFO 4547991504243258144.3688648895315093531."
```

**What it means:** CoreDNS sent a test query upstream and received it back
itself: it is forwarding to itself. The [CoreDNS loop plugin page](https://coredns.io/plugins/loop)
explains the mechanism.

**Why this step (now):** the fatal line is unambiguous; no other diagnosis needed.

**Next step:** → Step 2.

#### Step 2 — Find the loopback resolver kubelet hands to CoreDNS

**Goal:** see which resolv.conf kubelet passes to pods with `dnsPolicy: Default` (CoreDNS uses that).

```bash
# on each node:
cat /etc/resolv.conf | grep -v '^#'
grep -n resolvConf /var/lib/kubelet/config.yaml
grep -v '^#' /run/systemd/resolve/resolv.conf
```

```
nameserver 127.0.0.53
options edns0 trust-ad
search corp.example.com

9:resolvConf: /etc/resolv.conf

nameserver 192.0.2.53
nameserver 192.0.2.54
search corp.example.com
```

**What it means:** kubelet gives CoreDNS `/etc/resolv.conf`, which only contains
the systemd-resolved stub `127.0.0.53`. Inside the CoreDNS pod, 127.0.0.53 is
CoreDNS's own loopback, so `forward . /etc/resolv.conf` forwards to itself.
kubeadm normally sets `resolvConf: /run/systemd/resolve/resolv.conf` when it
detects systemd-resolved; this node was changed by hand, or runs a local cache
on 127.0.0.1.

**Why this step (now):** the loop is created on the node, not in Kubernetes;
this shows the exact file.

**Next step:** → "Fix & verify".

#### Decision tree: CoreDNS loop

```
[FATAL] plugin/loop
└── node: kubelet resolvConf → file with 127.x only?
    ├── yes → resolvConf: /run/systemd/resolve/resolv.conf (or a file with real upstreams), restart kubelet
    └── no  → Corefile forwards to a resolver that forwards back to the cluster → forward . REAL_UPSTREAMS
```

**Fix & verify**

```bash
# on every node (back up first):
sudo cp -a /var/lib/kubelet/config.yaml /root/kubelet-config.yaml.$(date +%F)
sudo sed -i 's#^resolvConf: .*#resolvConf: /run/systemd/resolve/resolv.conf#' /var/lib/kubelet/config.yaml
sudo systemctl restart kubelet
# new nodes / upgrades read the cluster-wide copy: update it too
kubectl -n kube-system edit configmap kubelet-config          # set resolvConf the same way
# recreate CoreDNS pods so they get the new resolv.conf
kubectl -n kube-system rollout restart deployment coredns
kubectl -n kube-system get pods -l k8s-app=kube-dns -w
```

→ CoreDNS pods `1/1 Running`, and `nslookup kubernetes.default` plus an external
name work from a test pod.

Alternative without touching kubelet: in the Corefile, replace
`forward . /etc/resolv.conf` with `forward . 192.0.2.53 192.0.2.54`. Never
"fix" this by deleting the `loop` plugin: the loop stays and CoreDNS burns CPU
and memory until it is OOM-killed.

**Rollback:** copy back the saved kubelet config, restart kubelet, restart CoreDNS.

**Prevent it next time:** bake `resolvConf` into your kubeadm configuration
(KubeletConfiguration) and check it in the node bootstrap; avoid local DNS
caches on Kubernetes nodes.

---

### NetworkPolicy blocks traffic or DNS

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: Network Policies ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Practice: *Kubernetes Troubleshooting for Application Developers* — Unreachable Pods + Leaky Network Policies ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 3) Note: [Learn Kubernetes](31-learn-kubernetes.md) (NetworkPolicies).

**Level:** [L3 · Senior] — policy semantics (AND vs OR, pod ports) are a frequent CKA task.

**Symptom:** right after a NetworkPolicy was applied, pods cannot reach each
other, or **every** DNS lookup times out in a namespace.

#### Step 1 — List the policies that select the pod

**Goal:** find which policies apply and which directions they restrict.

```bash
kubectl -n NS get networkpolicy
kubectl -n NS describe networkpolicy
kubectl -n NS get pod POD --show-labels
```

```
NAME               POD-SELECTOR   AGE
default-deny-all   <none>         20m
allow-web-to-api   app=api        20m

Name:         default-deny-all
Spec:
  PodSelector:     <none> (Allowing the specific traffic to all pods in this namespace)
  Allowing ingress traffic:
    <none> (Selected pods are isolated for ingress connectivity)
  Allowing egress traffic:
    <none> (Selected pods are isolated for egress connectivity)
  Policy Types: Ingress, Egress
```

**What it means:** `default-deny-all` selects every pod (`PodSelector: <none>`
means all) and denies all ingress **and egress**. Only what another policy
explicitly allows gets through, and no policy allows DNS. So every lookup to
kube-dns (in `kube-system`) is dropped. Policies are additive allow-lists: you
cannot "deny" with a second policy, only fail to allow.

**Why this step (now):** after a policy change, policies are the first suspect,
and `describe` translates them into plain words.

**Next step:** → Step 2 to prove the drop.

#### Step 2 — Prove the drop with a test pod

**Goal:** compare the same test inside and outside the policy's reach.

```bash
kubectl -n NS run nptest --rm -it --restart=Never --image=nicolaka/netshoot -- sh -c 'nslookup kubernetes.default; nc -vz -w2 10.96.0.10 53'
kubectl -n default run nptest --rm -it --restart=Never --image=nicolaka/netshoot -- nslookup kubernetes.default
```

```
;; connection timed out; no servers could be reached
nc: connect to 10.96.0.10 port 53 (tcp) timed out: Operation in progress

Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```

**What it means:** in the policy namespace DNS times out; in `default` it works.
The policy is the cause.

**Why this step (now):** a controlled comparison rules out CoreDNS itself.

**Next step:** → Step 3 to allow DNS, then app traffic.

#### Step 3 — Allow DNS egress and the app's flows

**Goal:** write the narrowest policies that restore function.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: shop
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
```

```bash
kubectl apply -f allow-dns-egress.yaml
# Same test pod as Step 2: DNS must answer now
kubectl -n shop run np-test --rm -it --restart=Never --image=nicolaka/netshoot -- nslookup api.shop
```

```
networkpolicy.networking.k8s.io/allow-dns-egress created
Server:		10.96.0.10
Address:	10.96.0.10#53

Name:	api.shop.svc.cluster.local
Address: 10.103.44.12

pod "np-test" deleted
```

**What it means:** name resolution works again from inside the restricted
namespace; app traffic is still blocked until you allow it explicitly. Three
traps a CKA task loves:

- `namespaceSelector` and `podSelector` in the **same** list item mean AND (kube-dns pods in kube-system); as two separate items (`- namespaceSelector` / `- podSelector`) they mean OR.
- `ports` are the **pod's** ports (the targetPort), not the Service port. If a Service maps 80 → 8080, the policy must allow 8080.
- Policies are only enforced if the CNI supports them (Calico, Cilium); on plain Flannel they are accepted and silently ignored.

**Why this step (now):** DNS first, because without it every other test fails
for the wrong reason.

**Next step:** apply, re-run Step 2, then add the app flows (for example ingress
from the ingress controller's namespace to `app=api` on 8080).

#### Decision tree: NetworkPolicy

```
kubectl get netpol -n NS (and in the target namespace)
├── none → not a policy problem (does the CNI even enforce them?)
└── policies select the pod
    ├── DNS times out → egress to kube-system/kube-dns UDP+TCP 53
    ├── pod → pod fails → egress on source AND ingress on destination, port = targetPort
    └── selectors → AND (one item) vs OR (two items); namespace labels (kubernetes.io/metadata.name)
```

**Fix & verify:** Step 2 succeeds in the policy namespace, and the app's real
flows work; traffic you meant to block (for example from `default`) still fails.

**Rollback:** `kubectl -n NS delete networkpolicy allow-dns-egress` for a bad
allow rule, or remove the deny policy only as an emergency measure (it reopens
everything), then re-apply from Git.

**Prevent it next time:** ship every default-deny together with its DNS allow
policy, test policies in a staging namespace with netshoot, and keep them in Git.

---

## 10. Kubernetes: nodes, storage and control plane

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Worker Node Failure, then Control Plane Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Install Kubernetes the kubeadm way; Cluster Maintenance: Backup and Restore Methods ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Deployment-With-kubeadm-Introduction/page)) · 3) Note: [Services & systemd](07-services-systemd.md) and [Logs & journal](06-logs-journal.md) (kubelet and containerd are systemd units) · 4) Practice: [iximiuz Labs: Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes) and the CKA Lightning Labs.

### Node NotReady

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Worker Node Failure ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure)) · 2) Note: [Services & systemd](07-services-systemd.md) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: Docker vs ContainerD ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page)).

**Level:** [L3 · Senior] — kubelet, containerd and CNI on the node: L1 systemd skills inside Kubernetes.

**Symptom:** `kubectl get nodes` shows `NotReady`; pods on that node turn
`Unknown` or `Terminating` and, after about five minutes, are recreated elsewhere
(StatefulSet pods wait until the node is confirmed gone).

#### Step 1 — Read the node conditions

**Goal:** tell "kubelet stopped talking" apart from "kubelet reports a problem".

```bash
kubectl get nodes -o wide
kubectl describe node worker2 | sed -n '/^Conditions:/,/^Addresses:/p'
```

```
NAME      STATUS     ROLES           AGE   VERSION   INTERNAL-IP
cp1       Ready      control-plane   1y    v1.34.1   192.0.2.20
worker1   Ready      <none>          1y    v1.34.1   192.0.2.21
worker2   NotReady   <none>          1y    v1.34.1   192.0.2.22

Conditions:
  Type             Status    LastHeartbeatTime                 Reason              Message
  ----             ------    -----------------                 ------              -------
  MemoryPressure   Unknown   Fri, 03 Oct 2026 12:10:41 +0000   NodeStatusUnknown   Kubelet stopped posting node status.
  DiskPressure     Unknown   Fri, 03 Oct 2026 12:10:41 +0000   NodeStatusUnknown   Kubelet stopped posting node status.
  PIDPressure      Unknown   Fri, 03 Oct 2026 12:10:41 +0000   NodeStatusUnknown   Kubelet stopped posting node status.
  Ready            Unknown   Fri, 03 Oct 2026 12:10:41 +0000   NodeStatusUnknown   Kubelet stopped posting node status.
```

**What it means:**

- `Unknown` + `Kubelet stopped posting node status`: the control plane has not heard from kubelet (kubelet dead, node down, or the network to the API server broken).
- `Ready False` with a message such as `container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized`: kubelet is alive and tells you what is wrong (here the CNI).
- `DiskPressure True` / `MemoryPressure True` / `PIDPressure True`: resources (Evicted scenario).

**Why this step (now):** the conditions decide whether you start on the node
(kubelet, runtime) or in the cluster (CNI pods).

**Next step:** `Unknown` → Step 2 on the node. `False` with a CNI message → Step 3.
Pressure → Step 3 and the Evicted scenario.

#### Step 2 — Check kubelet and containerd on the node

**Goal:** read why kubelet is not running or not reporting.

```bash
# on worker2 (SSH or console):
systemctl is-active kubelet containerd
systemctl status kubelet --no-pager | sed -n '1,6p'
sudo journalctl -u kubelet -b --no-pager -n 80 | grep -E ' E[0-9]{4} |error|failed' | tail -8
```

```
activating
active
● kubelet.service - kubelet: The Kubernetes Node Agent
     Active: activating (auto-restart) (Result: exit-code) since Fri 2026-10-03 12:14:02 UTC; 4s ago

Oct 03 12:13:52 worker2 kubelet[2211]: E1003 12:13:52.402113    2211 run.go:72] "command failed" err="failed to run Kubelet: running with swap on is not supported, please disable swap or set --fail-swap-on flag to false"
```

**What it means:** kubelet restarts in a loop because swap is on (the node
rebooted and `/etc/fstab` re-enabled a swap file). Common kubelet failures:

| kubelet log | Cause | Fix |
|---|---|---|
| `running with swap on is not supported` | swap enabled after reboot | `sudo swapoff -a`, remove the swap line from `/etc/fstab` (or configure swap support deliberately) |
| `validate CRI v1 runtime API ... unknown service runtime.v1.RuntimeService` | containerd's CRI plugin disabled (`disabled_plugins = ["cri"]` from the containerd.io package) | regenerate `/etc/containerd/config.toml`, set `SystemdCgroup = true`, restart containerd |
| `x509: certificate has expired`, `part of the existing bootstrap client certificate ... is expired` | kubelet client certificate expired | certificate scenario below |
| `Unable to register node with API server ... connection refused` / `i/o timeout` | node cannot reach `CP_IP:6443` | Step 4 |
| `failed to get cgroup stats`, pods restarting randomly | cgroup driver mismatch (containerd not using systemd cgroups) | `SystemdCgroup = true` in containerd config |
| `kubelet.service: inactive (dead)` after reboot | kubelet not enabled | `sudo systemctl enable --now kubelet` |

**Why this step (now):** kubelet is the component that reports node status; if
it is not running, nothing else on the node matters yet.

**Next step:** fix what the log names, restart kubelet, and watch
`kubectl get node worker2 -w`. If kubelet runs but the node is still NotReady → Step 3.

#### Step 3 — Check the CNI and the node's resources

**Goal:** find network-plugin and resource problems when kubelet itself runs.

```bash
ls /etc/cni/net.d/ ; ls /opt/cni/bin | head -5                     # on the node
kubectl -n kube-system get pods -o wide --field-selector spec.nodeName=worker2
df -h / /var/lib/containerd ; free -h                              # on the node
timedatectl | grep -E 'synchronized|NTP'                           # TLS needs a correct clock
```

```
(empty)
bandwidth  bridge  dhcp  firewall  host-local

NAME                READY   STATUS                  RESTARTS   AGE
calico-node-7xk2p   0/1     Init:CrashLoopBackOff   8          30m
kube-proxy-j4m9s    1/1     Running                 0          1y
```

**What it means:** `/etc/cni/net.d/` is empty because the CNI DaemonSet pod on
this node (calico-node) cannot finish its init container, so it never wrote its
config. Its logs say why: `kubectl -n kube-system logs calico-node-7xk2p -c install-cni`
(or the failing init container's name from `describe`).

**Why this step (now):** a running kubelet with a broken CNI reports NotReady;
the CNI pod on that node is the next layer down.

**Next step:** fix the CNI pod (often an image pull, a wrong interface
autodetection, or a firewall blocking the CNI's ports between nodes).

#### Step 4 — Check the path to the API server

**Goal:** make sure the node can reach the control plane.

```bash
# on the node:
grep server /etc/kubernetes/kubelet.conf
nc -vz -w3 192.0.2.20 6443
curl -sk https://192.0.2.20:6443/livez ; echo
```

```
    server: https://192.0.2.20:6443
Connection to 192.0.2.20 6443 port [tcp/*] succeeded!
ok
```

**What it means:** the API server is reachable and live from this node, so
connectivity is not the issue. A timeout here points to a firewall, a routing
problem or a control-plane outage (next scenarios).

**Why this step (now):** only needed when kubelet logs complain about reaching
the API server; it is a two-command check.

**Next step:** if it fails, check the control plane (kubectl connection refused
scenario) and the firewall between node and control plane.

#### Decision tree: Node NotReady

```
describe node → Conditions
├── Unknown (kubelet silent) → on node: systemctl status kubelet / journalctl -u kubelet
│   ├── swap on → swapoff + fstab
│   ├── CRI unimplemented → containerd config (cri plugin, SystemdCgroup)
│   ├── cert expired → kubeadm certs / kubelet rotation
│   └── can't reach :6443 → network / control plane
├── False: CNI not initialized → CNI pod on that node (logs of its init containers), /etc/cni/net.d
└── Pressure True → disk / memory → Evicted scenario
```

**Fix & verify:** `kubectl get node worker2 -w` turns `Ready` within a minute,
and `kubectl -n kube-system get pods -o wide --field-selector spec.nodeName=worker2`
shows the DaemonSet pods Running.

**Rollback:** restore the config files you changed (keep dated copies of
`/etc/containerd/config.toml` and `/var/lib/kubelet/config.yaml` before editing).

**Prevent it next time:** build nodes with Ansible (swap off, containerd config,
CA, resolvConf), monitor kubelet and containerd with node_exporter's systemd
collector, and practise: stop kubelet on a homelab worker and recover it without notes.

---

### PVC stuck in Pending

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage: persistent volumes, claims and storage classes ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Learn Kubernetes](31-learn-kubernetes.md) (storage) · 3) Practice: *Kubernetes Troubleshooting for Application Developers* — Multi-Attach Volume Errors ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)).

**Level:** [L3 · Senior] — StorageClasses, provisioners and access modes.

**Symptom:** `kubectl get pvc` shows `Pending`, and the pod that uses it is
`Pending` with `pod has unbound immediate PersistentVolumeClaims`.

#### Step 1 — Read the PVC events

**Goal:** get the binder's or provisioner's reason.

```bash
kubectl -n NS get pvc
kubectl -n NS describe pvc data-postgres-0 | sed -n '/^Events:/,$p'
```

```
NAME              STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-postgres-0   Pending                                      nfs-client     <unset>                 6m

Events:
  Type    Reason                Age                 From                         Message
  ----    ------                ----                ----                         -------
  Normal  ExternalProvisioning  12s (x26 over 6m)   persistentvolume-controller  Waiting for a volume to be created either by the external provisioner 'k8s-sigs.io/nfs-subdir-external-provisioner' or manually by the system administrator. If volume creation is delayed, please verify that the provisioner is running and correctly registered.
```

**What it means:** the StorageClass delegates to an external provisioner that
is not creating the volume. The messages you will meet:

| Event | Cause | Next |
|---|---|---|
| `Waiting for a volume to be created ... external provisioner 'X'` | provisioner pod down or misconfigured | Step 3 |
| `waiting for first consumer to be created before binding` | `WaitForFirstConsumer` class: normal until a pod using it is scheduled | look at the pod (Pending scenario) |
| `no persistent volumes available for this claim and no storage class is set` | no default StorageClass, no matching static PV | Step 2 |
| `storageclass.storage.k8s.io "fast" not found` | typo or class not installed | Step 2 |
| static PV exists but does not bind | size, access mode or class mismatch | Step 2 |

**Why this step (now):** the PVC's events are the only place the binder and
provisioner report.

**Next step:** follow the table.

#### Step 2 — Compare the claim with classes and static PVs

**Goal:** check every field that must match.

```bash
kubectl get storageclass
kubectl get pv
kubectl -n NS get pvc data-postgres-0 -o jsonpath='class={.spec.storageClassName} modes={.spec.accessModes} size={.spec.resources.requests.storage}{"\n"}'
```

```
NAME                   PROVISIONER                                   RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path                         Delete          WaitForFirstConsumer   false                  200d
nfs-client             k8s-sigs.io/nfs-subdir-external-provisioner   Delete          Immediate              false                  90d

NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM           STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pv-data   2Gi        RWO            Retain           Released    shop/old-data   manual         <unset>                          60d

class=nfs-client modes=["ReadWriteMany"] size=5Gi
```

**What it means:** for a **static** PV to bind, the PVC's `storageClassName`,
access mode and size must all fit (PV capacity ≥ request). `storageClassName: ""`
means "only static PVs without a class"; leaving it unset means "the default
class". `pv-data` is `Released`: it still carries the `claimRef` of its old
claim and will not bind again until an admin clears it (its data is still on disk).

**Why this step (now):** binding is pure matching; one mismatched field keeps a
claim Pending forever without any error.

**Next step:** fix the claim (class, mode, size), or reuse the released PV on
purpose: `kubectl patch pv pv-data -p '{"spec":{"claimRef":null}}'` (only if
the data may be given to the new claim). For dynamic classes → Step 3.

#### Step 3 — Check the provisioner

**Goal:** see why the provisioner does not create volumes.

```bash
kubectl get pods -A | grep -iE 'provisioner|csi'
kubectl -n nfs-provisioner describe pod -l app=nfs-subdir-external-provisioner | sed -n '/^Events:/,$p' | tail -3
kubectl -n nfs-provisioner logs deploy/nfs-subdir-external-provisioner --tail=20   # once it runs
```

```
nfs-provisioner   nfs-subdir-external-provisioner-6f8b9c7d5-xk2lp   0/1   ContainerCreating   0   2d

  Warning  FailedMount  40s (x95 over 2d)  kubelet  MountVolume.SetUp failed for volume "nfs-subdir-external-provisioner-root" : mount failed: exit status 32 ... mount.nfs: access denied by server while mounting 192.0.2.30:/exports/k8s
```

**What it means:** the provisioner itself cannot mount its NFS export, so it
never runs. Typical causes: the NFS client package (`nfs-common`) missing on
the node, the export not allowing the node's IP, a firewall to the NFS server.

**Why this step (now):** a provisioner is just another pod; when it is broken,
every claim of its class waits.

**Next step:** fix the provisioner (install `nfs-common` on every node, fix the
export), then the PVC binds within seconds.

#### Decision tree: PVC Pending

```
describe pvc → Events
├── waiting for first consumer → normal; debug the pod's scheduling
├── waiting for external provisioner → provisioner pod running? logs? (NFS client, export, CSI driver)
├── no storage class set / class not found → default class? spelling?
└── static PV → class + access mode + size match? PV Released → clear claimRef deliberately
```

**Fix & verify:** `kubectl -n NS get pvc` shows `Bound` with a volume name, and
the pod starts.

**Rollback:** delete a wrongly created claim only if its reclaim policy will not
destroy data you need (`kubectl get pv` RECLAIM POLICY column).

**Prevent it next time:** one clearly marked default StorageClass, provisioner
prerequisites (NFS client, iSCSI tools) in the node bootstrap, and `Retain` for
data you cannot recreate.

---

### kubectl connection refused or apiserver down

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: Control Plane Failure ([notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Troubleshooting/Control-Plane-Failure/page)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: Cluster Architecture ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Core-Concepts/Cluster-Architecture)) · 3) Note: [Kubernetes reference](15-kubernetes.md).

**Level:** [L3 · Senior] — static pods and crictl on a control-plane node; a standard CKA task.

**Symptom:** every `kubectl` command fails. On a kubeadm cluster the API server
is a static pod: you fix it from the control-plane node with `crictl`, not with
`kubectl`.

#### Step 1 — Read the exact client error

**Goal:** separate "no kubeconfig", "server down", "network" and "TLS".

```bash
kubectl get nodes
kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
echo "KUBECONFIG=${KUBECONFIG:-unset}  whoami=$(whoami)"
```

```
The connection to the server 192.0.2.20:6443 was refused - did you specify the right host or port?
https://192.0.2.20:6443
KUBECONFIG=unset  whoami=ops
```

**What it means:** the client has a valid kubeconfig and reaches the host, but
nothing listens on 6443: the API server is down or restarting. The other errors:

| Client error | Meaning | Next |
|---|---|---|
| `The connection to the server localhost:8080 was refused` | no kubeconfig at all (wrong user, `sudo kubectl`, KUBECONFIG unset) | copy `/etc/kubernetes/admin.conf` to `~/.kube/config` |
| `...:6443 was refused` | API server not listening | Step 2 |
| `dial tcp ...:6443: i/o timeout` | host down, firewall, wrong IP / VIP | network ([site down](25-playbook-site-down.md) method) |
| `x509: certificate has expired or is not yet valid` | expired certificates, or a wrong clock | next scenario, [time](12-time-ntp.md) |
| `x509: certificate signed by unknown authority` | kubeconfig from another (or rebuilt) cluster | fresh admin.conf |
| `You must be logged in to the server (Unauthorized)` | client certificate expired or credentials revoked | next scenario |

**Why this step (now):** "kubectl is broken" has six different causes on
different machines; the first line of the error picks one.

**Next step:** refused → Step 2 on the control-plane node.

#### Step 2 — Check the API server and etcd with crictl

**Goal:** see whether the static pods run, crash or do not exist at all.

```bash
# on the control-plane node (cp1):
sudo ss -ltnp 'sport = :6443'
sudo crictl ps -a --name 'kube-apiserver|etcd'
ls -l /etc/kubernetes/manifests/
```

```
(no listener)

CONTAINER       IMAGE           CREATED          STATE    NAME             ATTEMPT   POD ID          POD
9b2e4f1a7c3d0   a1b2c3d4e5f6a   20 seconds ago   Exited   kube-apiserver   7         3f2e1d0c9b8a7   kube-apiserver-cp1
4be1c0d9e8f71   f6e5d4c3b2a19   3 days ago       Running  etcd             0         8c7b6a5f4e3d2   etcd-cp1

-rw------- 1 root root 2402 Oct  3 12:20 etcd.yaml
-rw------- 1 root root 3911 Oct  3 12:31 kube-apiserver.yaml
-rw------- 1 root root 3416 Oct  3 12:20 kube-controller-manager.yaml
-rw------- 1 root root 1463 Oct  3 12:20 kube-scheduler.yaml
```

**What it means:** etcd runs; the API server exits on every attempt, and its
manifest was modified at 12:31, a few minutes ago. If there were **no**
kube-apiserver container at all, kubelet could not even parse the manifest
(Step 3, kubelet log).

**Why this step (now):** with the API server down, `crictl` on the node is the
only view of the control plane.

**Next step:** → Step 3 for its logs.

#### Step 3 — Read the API server's logs and kubelet's view

**Goal:** get the exact startup error.

```bash
sudo crictl logs --tail 15 9b2e4f1a7c3d0
sudo journalctl -u kubelet --since '20 min ago' --no-pager | grep -iE 'manifest|static pod|apiserver' | tail -5
# Logs also survive as files:
sudo tail -5 /var/log/pods/kube-system_kube-apiserver-cp1_*/kube-apiserver/*.log
```

```
Error: unknown flag: --enable-admission-plugin
```

**What it means:** a typo in a flag (`--enable-admission-plugins` is correct).
Other classic outputs:

| Log | Cause |
|---|---|
| `unknown flag: --X` | typo in the manifest's command list |
| `open /etc/kubernetes/pki/X.crt: no such file or directory` | wrong certificate path in a flag |
| `failed to listen on 0.0.0.0:6443: bind: address already in use` | a second API server (often a backup manifest left in the manifests folder) |
| `transport: Error while dialing: dial tcp 127.0.0.1:2379: connect: connection refused` | etcd down → `crictl logs` of etcd (disk full, data dir, certificates) |
| kubelet: `Could not process manifest file ... couldn't parse as pod` | broken YAML, so no container is created at all |

**Why this step (now):** the API server prints its fatal error as the last line;
kubelet's log covers the case where it never started.

**Next step:** fix the manifest (Step 4).

#### Step 4 — Edit the static pod manifest safely

**Goal:** change the manifest without making things worse.

```bash
# Backup OUTSIDE the manifests folder: kubelet runs every manifest it finds there
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/kube-apiserver.yaml.$(date +%F-%H%M)
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# kubelet notices the change within ~20 s and recreates the pod; watch it
watch -n2 "sudo crictl ps -a --name kube-apiserver"
kubectl get --raw='/readyz?verbose' | tail -3
```

```
[+]poststarthook/apiservice-openapiv3-controller ok
[+]shutdown ok
readyz check passed
```

**What it means:** the API server is back and all readiness checks pass.

**Why this step (now):** a static pod is "managed" only by its file; editing
the file is the restart. A backup copy in the same folder would start a second
API server and fail with "address already in use".

**Next step:** check the rest of the control plane:
`kubectl -n kube-system get pods -l tier=control-plane`.

#### Decision tree: kubectl cannot talk to the cluster

```
kubectl error text
├── localhost:8080 → no kubeconfig → ~/.kube/config from admin.conf
├── i/o timeout → network / VM / VIP
├── x509 expired / unknown authority / Unauthorized → certificates, kubeconfig, clock
└── :6443 refused → on cp node: crictl ps -a
    ├── apiserver Exited → crictl logs → flag/path typo → fix manifest (backup outside the folder)
    ├── no apiserver container → kubelet log: manifest parse error
    ├── etcd Exited → crictl logs etcd → disk / certs / data dir
    └── kubelet itself down → systemctl status kubelet
```

**Fix & verify:** `kubectl get nodes` works, `kubectl get --raw='/readyz'` prints
`ok`, and all control-plane pods are Running.

**Rollback:** copy the backup from `/root/` back into `/etc/kubernetes/manifests/`.

**Prevent it next time:** keep control-plane manifests in Git (or at least
dated backups), change one flag at a time, back up etcd regularly
(`etcdctl snapshot save`), and rehearse static-pod breakage in the homelab:
it is a standard CKA task.

---

### kubeadm certificate expiry

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: TLS Basics ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) · 2) Note: [Time & NTP](12-time-ntp.md) (rule out the clock first) · 3) Read: kubeadm certificate management in the [Kubernetes docs](https://kubernetes.io/docs/).

**Level:** [L4 · Lead] — cluster maintenance with a full-outage risk; a Lead schedules it before it happens.

**Symptom:** exactly one year after `kubeadm init` (or the last upgrade),
`kubectl` fails with `x509: certificate has expired or is not yet valid` or
`Unauthorized`, and control-plane components start failing.

#### Step 1 — Check expiry dates

**Goal:** see which certificates expired and whether the CAs are still valid.

```bash
sudo kubeadm certs check-expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate
date -u ; timedatectl | grep synchronized
```

```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Oct 01, 2026 08:12 UTC   <invalid>       ca                      no
apiserver                  Oct 01, 2026 08:12 UTC   <invalid>       ca                      no
apiserver-etcd-client      Oct 01, 2026 08:12 UTC   <invalid>       etcd-ca                 no
apiserver-kubelet-client   Oct 01, 2026 08:12 UTC   <invalid>       ca                      no
controller-manager.conf    Oct 01, 2026 08:12 UTC   <invalid>       ca                      no
etcd-healthcheck-client    Oct 01, 2026 08:12 UTC   <invalid>       etcd-ca                 no
etcd-peer                  Oct 01, 2026 08:12 UTC   <invalid>       etcd-ca                 no
etcd-server                Oct 01, 2026 08:12 UTC   <invalid>       etcd-ca                 no
front-proxy-client         Oct 01, 2026 08:12 UTC   <invalid>       front-proxy-ca          no
scheduler.conf             Oct 01, 2026 08:12 UTC   <invalid>       ca                      no
super-admin.conf           Oct 01, 2026 08:12 UTC   <invalid>       ca                      no

CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
ca                      Sep 29, 2035 08:12 UTC   8y              no
etcd-ca                 Sep 29, 2035 08:12 UTC   8y              no
front-proxy-ca          Sep 29, 2035 08:12 UTC   8y              no

notAfter=Oct  1 08:12:44 2026 GMT
Fri Oct  3 12:40:11 UTC 2026
System clock synchronized: yes
```

**What it means:** every leaf certificate expired two days ago (`<invalid>`),
the CAs are valid until 2035, and the clock is right. kubeadm leaf certificates
last one year; `kubeadm upgrade` renews them, so clusters that are never
upgraded expire on their first birthday. If the clock were wrong instead, fix
time first ([Time & NTP](12-time-ntp.md)), not the certificates.

**Why this step (now):** you must know which certificates to renew and confirm
the CA is fine (an expired CA is a much bigger job).

**Next step:** → Step 2.

#### Step 2 — Back up and renew

**Goal:** renew all kubeadm-managed certificates and kubeconfigs.

```bash
sudo cp -a /etc/kubernetes /root/kubernetes-backup-$(date +%F)
sudo kubeadm certs renew all
```

```
[renew] Reading configuration from the "kubeadm-config" ConfigMap in namespace "kube-system"...
certificate embedded in the kubeconfig file for the admin to use and for kubeadm itself renewed
certificate for serving the Kubernetes API renewed
...
certificate embedded in the kubeconfig file for the scheduler manager to use renewed

Done renewing certificates. You must restart the kube-apiserver, kube-controller-manager, kube-scheduler and etcd, so that they can use the new certificates.
```

**What it means:** new certificate files are on disk, but the running
components still use the old ones in memory. (If the API server is down,
kubeadm warns that it cannot read the ConfigMap and uses defaults; that is fine
for a plain kubeadm cluster.)

**Why this step (now):** renewal is file-level and safe with a backup; the
restart is the step with impact.

**Next step:** → Step 3.

#### Step 3 — Restart static pods and refresh kubeconfig

**Goal:** make the components load the new certificates.

```bash
sudo mkdir -p /root/manifests-moved
sudo mv /etc/kubernetes/manifests/*.yaml /root/manifests-moved/
sleep 20                                    # kubelet stops the static pods
sudo crictl ps --name 'kube-apiserver|etcd|kube-controller|kube-scheduler'   # expect nothing
sudo mv /root/manifests-moved/*.yaml /etc/kubernetes/manifests/
# your kubeconfig embeds the old admin certificate: refresh it
sudo cp /etc/kubernetes/admin.conf ~/.kube/config && sudo chown "$(id -u):$(id -g)" ~/.kube/config
sleep 30 ; sudo crictl ps --name 'kube-apiserver|etcd|kube-controller|kube-scheduler'   # all four back
```

```
CONTAINER      IMAGE          CREATED          STATE     NAME   ATTEMPT   POD ID    POD
(first crictl ps: header only, the four static pods are stopped)

CONTAINER       IMAGE           CREATED          STATE     NAME                      ATTEMPT   POD ID          POD
9b1f0c3e2a7d4   6f1d2a4c8b3e5   14 seconds ago   Running   kube-apiserver            0         2c7e9a1b4d6f8   kube-apiserver-cp1
4e8a2d6c1f9b3   2e3b5c7d9a1f6   15 seconds ago   Running   etcd                      0         7a1c3e5b9d2f4   etcd-cp1
c3d5e7f9a1b24   8d4f6a2c1e3b7   14 seconds ago   Running   kube-controller-manager   0         5b9d1f3a7c2e9   kube-controller-manager-cp1
a1b2c3d4e5f60   1c3e5a7b9d2f8   14 seconds ago   Running   kube-scheduler            0         9f2b4d6a8c1e3   kube-scheduler-cp1
```

**What it means:** moving the manifests out stops the pods (the first listing
is empty); moving them back starts them with the new certificates (the second
listing shows all four created seconds ago). Repeat Steps 2–3 on **every**
control-plane node. Kubelet's own client certificate rotates automatically
(`/var/lib/kubelet/pki/kubelet-client-current.pem`); if a node was off for over
a year and its kubelet certificate also expired, rejoin or follow the kubeadm
documentation for kubelet certificate recovery.

**Why this step (now):** without the restart the API server keeps serving the
expired certificate and nothing changes.

**Next step:** verify.

#### Decision tree: certificate expiry

```
x509 expired from kubectl
├── clock wrong? (date, timedatectl) → fix time first
└── kubeadm certs check-expiration
    ├── leaf certs <invalid>, CA valid → backup → certs renew all → restart static pods → new admin.conf
    ├── CA expired → CA rotation (major procedure; read kubeadm docs first)
    └── only kubelet client cert → kubelet rotation / rejoin node
```

**Fix & verify**

```bash
sudo kubeadm certs check-expiration | head -5     # RESIDUAL TIME ~364d
kubectl get nodes
kubectl -n kube-system get pods -l tier=control-plane
```

**Rollback:** stop kubelet, restore `/root/kubernetes-backup-DATE` to
`/etc/kubernetes`, start kubelet (only useful if renewal itself broke something;
the old certificates are expired anyway).

**Prevent it next time**

- Upgrade the cluster at least once a year (it renews certificates), or schedule `kubeadm certs renew all` with a restart.
- Alert 30 days ahead: run `kubeadm certs check-expiration` from a cron job, or alert on the API server metric `apiserver_client_certificate_expiration_seconds`.
- Put the CA expiry date (10 years) in the team calendar.

---

## 11. Kubernetes: rollouts and autoscaling

> 📚 **Study path:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — PODs, ReplicaSets, Deployments with the rolling update labs ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Application Lifecycle Management, then Logging & Monitoring ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Note: [Learn Kubernetes](31-learn-kubernetes.md) (Deployments, rollouts, HPA) and [Deployment patterns](35-deployment-patterns.md) · 4) Video: *Kubernetes Crash Course: Learn the Basics and Build a Microservice Application* ([YouTube](https://www.youtube.com/watch?v=XuSQU5Grv1g)) · 5) Practice: on the [Kubernetes playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster), deploy a tag that does not exist, watch the rollout stall, undo it, then load a Deployment until the HPA scales it.

Both scenarios start with a change: a new image, a new manifest, or new load.
The Deployment controller and the HorizontalPodAutoscaler are controllers like
any other: they write their reasoning into `status.conditions` and into events.
Read those before you guess, and remember the bottom-up rule: a stuck rollout or
a flat HPA is usually a pod-level problem (section 8) seen from one level higher.

### Rollout stuck

> 📚 **Know this first:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — PODs, ReplicaSets, Deployments, with the rolling update labs ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)) · 2) Note: [Deployment patterns](35-deployment-patterns.md) (rolling, blue-green, canary) · 3) Note: "CrashLoopBackOff" and "ImagePullBackOff and ErrImagePull" in section 8 (what usually breaks the new pods).

**Level:** [L3 · Senior] — reading Deployment conditions and choosing between rolling back and fixing forward while users wait.

**Symptom:** `kubectl rollout status` hangs on `Waiting for deployment "api"
rollout to finish`, then prints `error: deployment "api" exceeded its progress
deadline`. A CI deploy job times out. Users may be fine (the old pods still
serve) or partly broken (some new pods take traffic and fail).

#### Step 1 — Read rollout status and Deployment conditions

**Goal:** learn whether users are affected and which ReplicaSet is the new one, before touching anything.

```bash
kubectl -n NS rollout status deploy/api
kubectl -n NS get deploy api -o wide
kubectl -n NS describe deploy api | sed -n '/^Conditions:/,/^Events:/p'
```

```
Waiting for deployment "api" rollout to finish: 1 out of 3 new replicas have been updated...
error: deployment "api" exceeded its progress deadline

NAME   READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                              SELECTOR
api    3/3     1            3           41d   api          harbor.example.com/shop/api:1.4.4   app=api

Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    False   ProgressDeadlineExceeded
OldReplicaSets:  api-6d9f7b8c5 (3/3 replicas created)
NewReplicaSet:   api-7f4c9d2b8 (1/1 replicas created)
Events:
```

**What it means:** read it line by line:

- `UP-TO-DATE 1` of 3: only one pod runs the new template. `READY 3/3` and `AVAILABLE 3` are the **old** pods still serving.
- `Available True`: users are being served right now. If it said `False`, the app is (partly) down.
- `Progressing False / ProgressDeadlineExceeded`: no progress for `progressDeadlineSeconds` (default 600 s). Kubernetes only **reports** this; it never rolls back on its own.
- `NewReplicaSet api-7f4c9d2b8 (1/1 replicas created)`: the new ReplicaSet made its surge pod, and that pod never became Ready. With the default strategy (maxSurge 25%, maxUnavailable 25%, rounded to 1 and 0 for three replicas), the controller will not remove an old pod until a new one is Ready, so the rollout simply stops.

**Why this step (now):** the conditions answer the first incident question
("are users affected?") and decide your next move: roll back now, or take the
time to diagnose.

**Next step:** If `Available` is `False` or users report errors → Step 4 now
(roll back first, diagnose second). If `Available` is `True` → Step 2 to see why
the new pods are not Ready.

#### Step 2 — Look only at the new ReplicaSet's pods

**Goal:** find the pod-level failure hiding behind "rollout stuck".

```bash
kubectl -n NS get rs -l app=api
kubectl -n NS get pods -l app=api -L pod-template-hash
kubectl -n NS describe pod -l pod-template-hash=7f4c9d2b8 | sed -n '/^Events:/,$p' | tail -4
kubectl -n NS describe rs api-7f4c9d2b8 | sed -n '/^Events:/,$p' | tail -3
```

```
NAME            DESIRED   CURRENT   READY   AGE
api-6d9f7b8c5   3         3         3       12d
api-7f4c9d2b8   1         1         0       14m

NAME                  READY   STATUS             RESTARTS   AGE   POD-TEMPLATE-HASH
api-6d9f7b8c5-4kq2x   1/1     Running            0          12d   6d9f7b8c5
api-6d9f7b8c5-9wz7m   1/1     Running            0          12d   6d9f7b8c5
api-6d9f7b8c5-mx2lq   1/1     Running            0          12d   6d9f7b8c5
api-7f4c9d2b8-t5r8p   0/1     ImagePullBackOff   0          14m   7f4c9d2b8

  Warning  Failed     13m (x4 over 14m)    kubelet  Failed to pull image "harbor.example.com/shop/api:1.4.4": rpc error: code = NotFound desc = failed to pull and unpack image "harbor.example.com/shop/api:1.4.4": failed to resolve reference "harbor.example.com/shop/api:1.4.4": harbor.example.com/shop/api:1.4.4: not found
  Normal   BackOff    4m (x42 over 14m)    kubelet  Back-off pulling image "harbor.example.com/shop/api:1.4.4"

  Normal  SuccessfulCreate  14m   replicaset-controller  Created pod: api-7f4c9d2b8-t5r8p
```

**What it means:** the stuck rollout is really one new pod in
`ImagePullBackOff`: tag `1.4.4` does not exist in Harbor (the pipeline failed
before its push step, or the tag was mistyped). The `-L pod-template-hash` column
is the trick: it separates new pods from old ones, which a plain `get pods`
hides behind three healthy old pods. Other states map to their scenarios:

| New pod state | Go to |
|---|---|
| `ImagePullBackOff`, `ErrImagePull` | section 8, ImagePullBackOff and ErrImagePull |
| `CrashLoopBackOff`, `Error` | section 8, CrashLoopBackOff |
| `Running` but `0/1` | section 9, readiness fails |
| `Pending` | section 8, Pod stuck in Pending (the surge pod needs room) |
| no new pod at all, RS events say `exceeded quota` or `forbidden` | ResourceQuota, LimitRange or an admission policy rejects the pod: `kubectl -n NS describe quota` |

**Why this step (now):** a stuck rollout is never its own disease; it is one of
the pod scenarios, limited to the new ReplicaSet. Looking only at the new pods
saves you from debugging the healthy old ones.

**Next step:** If the cause is clear and users are fine → Step 3 to confirm
what changed. If you cannot fix it within minutes → Step 4 (roll back), then
fix at leisure.

#### Step 3 — Compare the two revisions

**Goal:** see exactly what changed between the working and the stuck version.

```bash
kubectl -n NS rollout history deploy/api
diff <(kubectl -n NS get rs api-6d9f7b8c5 -o jsonpath='{.spec.template.spec.containers[0]}' | jq -S .) \
     <(kubectl -n NS get rs api-7f4c9d2b8 -o jsonpath='{.spec.template.spec.containers[0]}' | jq -S .)
```

```
deployment.apps/api
REVISION  CHANGE-CAUSE
6         <none>
7         <none>

12c12
<   "image": "harbor.example.com/shop/api:1.4.3",
---
>   "image": "harbor.example.com/shop/api:1.4.4",
```

**What it means:** revision 7 changed only the image tag. `CHANGE-CAUSE <none>`
means nobody recorded why; set it from CI with
`kubectl -n NS annotate deploy/api kubernetes.io/change-cause="1.4.4 pipeline 8812"`
so the next person sees it in `rollout history`. If the diff shows env,
probe or resource changes instead, those are your suspects.

**Why this step (now):** knowing the exact change lets you choose: fix forward
(push the missing tag, correct one value) or roll back. Guessing leads to a
third, untested version.

**Next step:** If the fix is small and certain → apply it and go to "Fix &
verify". Otherwise → Step 4.

#### Step 4 — Roll back, or fix forward, and watch it finish

**Goal:** get back to a known-good state with the old ReplicaSet, which still exists.

```bash
kubectl -n NS rollout undo deploy/api                    # to the previous revision
# or a specific one:  kubectl -n NS rollout undo deploy/api --to-revision=6
kubectl -n NS rollout status deploy/api --timeout=180s
kubectl -n NS get rs -l app=api
```

```
deployment.apps/api rolled back
Waiting for deployment "api" rollout to finish: 1 old replicas are pending termination...
deployment "api" successfully rolled out

NAME            DESIRED   CURRENT   READY   AGE
api-6d9f7b8c5   3         3         3       12d
api-7f4c9d2b8   0         0         0       19m
```

**What it means:** `undo` copies the old pod template back into the Deployment
(creating revision 8, identical to 6); the broken ReplicaSet is scaled to 0 but
kept, so you can inspect its template later. Kubernetes keeps
`revisionHistoryLimit` old ReplicaSets (10 by default); with 0, there is nothing
to roll back to.

> ⚠️ If Argo CD, Flux or a CI job applies the manifest from Git, `kubectl rollout
> undo` is overwritten at the next sync, which re-deploys the broken version.
> Roll back in Git (`git revert`) and let the tool apply it.

**Why this step (now):** rollback is the cheapest safe action because the old
ReplicaSet and its image are still on the cluster; it restores service while you
fix the real cause calmly.

**Next step:** verify, then fix the cause (push the image, fix the probe) and
roll forward again in the normal pipeline.

#### Decision tree: rollout stuck

```
rollout status: exceeded its progress deadline / hangs
├── describe deploy: Available False? → users down → rollout undo NOW, diagnose after
└── Available True → get pods -L pod-template-hash (new RS only)
    ├── ImagePullBackOff → tag missing / pull secret / Harbor CA (section 8) → push tag or undo
    ├── CrashLoopBackOff → logs --previous (section 8)
    ├── Running 0/1 → readiness probe (section 9)
    ├── Pending → no room for the surge pod (section 8)
    └── no new pod → describe rs NEW: exceeded quota / forbidden → quota, LimitRange, admission policy
```

**Fix & verify**

```bash
kubectl -n NS rollout status deploy/api --timeout=180s     # successfully rolled out
kubectl -n NS get deploy api                              # UP-TO-DATE = AVAILABLE = 3
kubectl -n NS get rs -l app=api                           # only one RS with pods
curl -s -H 'Host: shop.example.com' http://192.0.2.21:30080/version   # the version you expect
```

**Rollback:** `kubectl -n NS rollout undo deploy/api` (Step 4), or `git revert`
when a GitOps tool owns the manifest.

**Prevent it next time**

- In CI, deploy only images that exist: push first, then update the manifest with the image **digest** the push returned.
- Every Deployment has a readiness probe, so a bad version never receives traffic, and `maxUnavailable: 0` for small replica counts.
- Alert on `ProgressDeadlineExceeded` (kube-state-metrics exposes Deployment conditions) and make the CI job fail on `rollout status --timeout`.
- Record `kubernetes.io/change-cause` from the pipeline so `rollout history` explains itself.

---

### HPA not scaling

> 📚 **Know this first:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Logging & Monitoring (metrics server, `kubectl top`) ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Learn Kubernetes](31-learn-kubernetes.md) (Deployments, rollouts, HPA) · 3) Note: [CPU & performance](03-cpu-performance.md) (what "CPU utilization" really measures).

**Level:** [L3 · Senior] — the metrics pipeline, requests and the scaling formula together.

**Symptom:** `kubectl get hpa` shows `cpu: <unknown>/70%` in TARGETS, or the app
is overloaded and REPLICAS stays at the minimum, or it scales to the maximum at
idle.

#### Step 1 — Read the HPA status and conditions

**Goal:** let the HPA controller tell you why it cannot compute a replica count.

```bash
kubectl -n NS get hpa
kubectl -n NS describe hpa api | sed -n '/^Conditions:/,$p'
```

```
NAME   REFERENCE        TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
api    Deployment/api   cpu: <unknown>/70%   2         10        2          3d

Conditions:
  Type           Status  Reason                   Message
  ----           ------  ------                   -------
  AbleToScale    True    SucceededGetScale        the HPA controller was able to get the target's current scale
  ScalingActive  False   FailedGetResourceMetric  the HPA was unable to compute the replica count: failed to get cpu utilization: unable to get metrics for resource cpu: unable to fetch metrics from resource metrics API: the server could not find the requested resource (get pods.metrics.k8s.io)
Events:
  Type     Reason                   Age                From                       Message
  ----     ------                   ----               ----                       -------
  Warning  FailedGetResourceMetric  2m (x720 over 3d)  horizontal-pod-autoscaler  failed to get cpu utilization: unable to get metrics for resource cpu: unable to fetch metrics from resource metrics API: the server could not find the requested resource (get pods.metrics.k8s.io)
```

**What it means:** `<unknown>` plus `ScalingActive False` with "could not find
the requested resource (get pods.metrics.k8s.io)" means there is no working
metrics API: metrics-server is missing or broken. The condition text names the
cause; map it:

| Condition or message | Meaning | Next |
|---|---|---|
| `ScalingActive False`, `pods.metrics.k8s.io` not found, `Metrics API not available` | metrics-server missing or unhealthy | Step 2 |
| `missing request for cpu` (or memory) | the target pods have no request, so a percentage has no denominator | Step 3 |
| `ScalingLimited True`, `TooManyReplicas` | already at `maxReplicas` | raise the max only if the nodes have room |
| TARGETS shows a number below the target | the HPA works; per-pod load is lower than you think, or the request is too large | Step 3 (the math) |
| it scaled, but the new pods are `Pending` | the HPA works; the cluster is full | section 8, Pod stuck in Pending |

**Why this step (now):** the HPA writes its exact reason into conditions and
events; reading them takes ten seconds and replaces all guessing.

**Next step:** follow the table: metrics problems → Step 2; request or math
problems → Step 3.

#### Step 2 — Check metrics-server and the metrics API

**Goal:** make `kubectl top` work, because the HPA reads the same API.

```bash
kubectl top nodes
kubectl -n kube-system get deploy metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl -n kube-system logs deploy/metrics-server --tail=20 | grep -i -m3 error
```

```
error: Metrics API not available

NAME             READY   UP-TO-DATE   AVAILABLE   AGE
metrics-server   0/1     1            0           3d

NAME                     SERVICE                      AVAILABLE                  AGE
v1beta1.metrics.k8s.io   kube-system/metrics-server   False (MissingEndpoints)   3d

E1003 11:40:02.118214  1 scraper.go:149] "Failed to scrape node" err="Get \"https://192.0.2.21:10250/metrics/resource\": tls: failed to verify certificate: x509: cannot validate certificate for 192.0.2.21 because it doesn't contain any IP SANs" node="worker1"
```

**What it means:** metrics-server is installed but never became Ready, so the
APIService has no endpoints and both `kubectl top` and the HPA get nothing. The
log names the cause that hits almost every kubeadm homelab: each kubelet serves
a self-signed certificate without the node's IP in its SANs, and metrics-server
(correctly) refuses it. Two fixes:

- **Proper:** enable kubelet serving certificates signed by the cluster CA (`serverTLSBootstrap: true` in the kubelet configuration on each node, restart kubelet, then approve the pending CSRs with `kubectl get csr` and `kubectl certificate approve NAME`).
- **Homelab only:** add `--kubelet-insecure-tls` to the metrics-server container args. It disables verification of the kubelets, so never use it on a production cluster.

If the Deployment does not exist at all, metrics-server was never installed:
install it with Helm or its release manifest as part of the cluster build.

**Why this step (now):** the HPA, `kubectl top` and the VPA all depend on the
metrics API. Tuning HPA settings while the API is down changes nothing.

**Next step:** when `kubectl -n NS top pods` prints numbers, re-run
`kubectl -n NS get hpa`. If TARGETS is still `<unknown>` → Step 3.

#### Step 3 — Check the requests and the scaling math

**Goal:** make sure the percentage the HPA computes means something.

```bash
kubectl -n NS get deploy api -o jsonpath='{.spec.template.spec.containers[*].resources}{"\n"}'
kubectl -n NS top pods -l app=api
kubectl -n NS get hpa api -o jsonpath='{.spec.metrics}{"\n"}'
```

```
{"limits":{"memory":"512Mi"}}

NAME                  CPU(cores)   MEMORY(bytes)
api-6d9f7b8c5-4kq2x   870m         301Mi
api-6d9f7b8c5-9wz7m   910m         296Mi

[{"resource":{"name":"cpu","target":{"averageUtilization":70,"type":"Utilization"}},"type":"Resource"}]
```

**What it means:** the container has a memory limit (so its memory request
defaults to 512Mi) but **no CPU request**, so "70% CPU utilization" has no
denominator and the HPA reports `missing request for cpu`. Utilization is
always a percentage of the **request**, not of the limit or the node. The
formula is:

```
desiredReplicas = ceil( currentReplicas × currentUtilization / targetUtilization )

with requests.cpu: 500m and the usage above (average 890m = 178%):
desiredReplicas = ceil( 2 × 178 / 70 ) = ceil( 5.09 ) = 6
```

Two more behaviours that look like bugs: the HPA ignores changes within about
10% of the target (tolerance), and it waits for a 5-minute stabilization window
before scaling **down**, on purpose, to avoid flapping. A tiny request (50m)
makes the HPA scale to `maxReplicas` at idle; a huge request makes it never scale.

**Why this step (now):** once metrics flow, wrong or missing requests are the
remaining cause, and the formula tells you what the HPA should do before you
watch it.

**Next step:** set `resources.requests.cpu` from measured usage (for example
`500m`), roll it out, then go to "Fix & verify" and watch the HPA.

#### Decision tree: HPA not scaling

```
kubectl get hpa → TARGETS
├── <unknown> → describe hpa: Conditions
│   ├── pods.metrics.k8s.io not found / Metrics API not available → metrics-server (Step 2)
│   │   └── log: x509 ... doesn't contain any IP SANs → kubelet serving certs (lab: --kubelet-insecure-tls)
│   └── missing request for cpu → add requests to the pod template (Step 3)
├── number below target → working; check request size and real per-pod load
├── at MAXPODS (ScalingLimited) → raise max only if nodes have capacity
└── scaled, new pods Pending → cluster full → section 8 Pending / add nodes
```

**Fix & verify**

```bash
kubectl -n NS top pods -l app=api              # numbers, not an error
kubectl -n NS get hpa api -w                   # TARGETS shows cpu: 178%/70%, REPLICAS climbs to 6
kubectl -n NS describe hpa api | grep -A4 Conditions   # ScalingActive True
```

**Rollback:** `kubectl -n NS rollout undo deploy/api` reverts the request
change; revert the metrics-server change with `helm rollback` or by re-applying
its previous manifest.

**Prevent it next time**

- Install metrics-server as part of the cluster bootstrap (Ansible or Helm), with proper kubelet serving certificates, and alert when the `v1beta1.metrics.k8s.io` APIService is unavailable.
- Require CPU and memory requests on every container (a LimitRange default, or a policy in CI); no request, no autoscaling.
- Load-test once after enabling an HPA and write down the replica count you saw at a known request rate.
- Size `maxReplicas` against node capacity, or pair the HPA with a cluster autoscaler where you have one.

---

## 12. Master decision trees

> 📚 **Study path:** 1) Read: [learnkube: Troubleshooting deployments](https://learnkube.com/troubleshooting-deployments) (the bottom-up flowchart the Kubernetes tree follows) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting Section Introduction ([notes](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Troubleshooting-Section-Introduction)) · 3) Read: [Google SRE book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 4) Practice: print both trees, then solve three [SadServers](https://sadservers.com/scenarios) scenarios tagged docker using only the trees.

Use these when you do not yet know which scenario you are in. Each branch ends
in a section of this module. Walk them top to bottom, write down the evidence at
every level (a status, an exit code, a log line, a curl result), and stop at the
first level that fails: that is the broken layer.

### Master tree: Docker, Dokploy and Traefik

```
"the app is down" on a Docker / Dokploy host
│
├─ 1. Is it running?   docker ps -a  ·  docker service ls  ·  systemctl is-active docker
│   ├─ docker itself down → daemon will not start (section 2)
│   ├─ Exited / Restarting → docker inspect: exit code
│   │   ├─ 137 + OOMKilled true → OOMKilled (section 2)
│   │   ├─ 125 / 126 / 127 / exec format error → wrong command, image or arch (section 2)
│   │   ├─ 1 / 2 → app error → docker logs (section 2)
│   │   └─ 0 / 143 → finished or stopped by someone → docker events (section 2)
│   ├─ Created, never started → port is already allocated (section 3) / mount error (section 5)
│   ├─ Swarm 0/1, Pending / Rejected → docker service ps --no-trunc (section 7)
│   └─ Up ↓
│
├─ 2. Does the app answer inside its own network namespace?
│      docker run --rm --net container:CONTAINER nicolaka/netshoot curl -sv http://127.0.0.1:PORT/
│   ├─ refused → wrong port, still starting, or crashed worker → app config / logs
│   ├─ slow → CPU throttling, memory pressure, I/O (section 6)
│   └─ answers ↓
│
├─ 3. Can the proxy's network reach it?
│      docker run --rm --network dokploy-network nicolaka/netshoot curl -sv http://APPNAME:PORT/
│   ├─ name does not resolve → not on the same network (section 4)
│   ├─ refused → app bound to 127.0.0.1 inside the container (section 7, 502)
│   └─ answers ↓
│
├─ 4. Does Traefik route the name?   curl -v --resolve DOMAIN:443:SERVER_IP https://DOMAIN/
│   ├─ 404 page not found → no router matched (section 7, 404)
│   ├─ 502 / 504 → port label, network, timeouts (section 7, 502)
│   ├─ TRAEFIK DEFAULT CERT → ACME failed (section 7, certificate)
│   ├─ old version → stale image or duplicate backends (section 7)
│   └─ 200 ↓
│
├─ 5. Does the outside world get there?   from another network: curl -v https://DOMAIN/
│   ├─ resolves to the wrong IP → DNS and TTL (site down playbook, module 25)
│   ├─ timeout → firewall, security group, who owns 80/443 (section 3; module 22)
│   └─ works → the problem is client-side or intermittent: compare timestamps in Traefik's access log
│
└─ Side checks at any level: disk full (section 5) · DNS inside containers (section 4)
   · dependency on the host (section 3) · registry pulls and builds (section 6)
   · exposure you did not intend (section 3, published ports bypass UFW)
```

### Master tree: Kubernetes

```
"the app is down" on Kubernetes        first: kubectl config current-context
│
├─ 0. Can you talk to the cluster?   kubectl get nodes
│   ├─ refused :6443 / x509 expired / timeout → control plane, certificates (section 10)
│   ├─ node NotReady → kubelet, containerd, CNI, pressure (section 10)
│   └─ OK ↓
│
├─ 1. Pods   kubectl -n NS get pods -o wide
│   ├─ Pending → scheduler events (section 8) · PVC Pending (section 10)
│   ├─ ErrImagePull / ImagePullBackOff → tag, pull secret, containerd CA (section 8)
│   ├─ CrashLoopBackOff / Error / CreateContainerConfigError → logs --previous, Last State (section 8)
│   ├─ OOMKilled → limits vs real usage (section 8)
│   ├─ Evicted → node DiskPressure (section 8)
│   ├─ Running 0/1 → readiness probe (section 9)
│   └─ Running 1/1 ↓
│
├─ 2. Service   kubectl -n NS get endpointslices -l kubernetes.io/service-name=SVC
│   ├─ no endpoints → selector vs labels, readiness (section 9)
│   ├─ endpoints, but refused → targetPort vs container port (section 9)
│   └─ test pod: curl http://SVC.NS:PORT works ↓
│
├─ 3. DNS   test pod: nslookup SVC.NS
│   ├─ timeout → CoreDNS down or looping, NetworkPolicy on port 53 (section 9)
│   ├─ NXDOMAIN for a short name → other namespace: use NAME.NAMESPACE (section 9)
│   └─ resolves ↓
│
├─ 4. Ingress   curl -v -H 'Host: DOMAIN' http://INGRESS_IP/
│   ├─ 404 controller page → class, host, path, namespace (section 9)
│   ├─ 503 → no ready endpoints → back to levels 1–2
│   ├─ 502 / 504 → targetPort, backend protocol, timeouts (section 9)
│   └─ 200 ↓  → outside path: DNS, firewall, load balancer (module 25)
│
├─ 5. Policy   works from some pods, times out from others → NetworkPolicy (section 9)
│
└─ 6. Did something change?
    ├─ rollout exceeded its progress deadline → rollout stuck (section 11)
    ├─ overloaded, replicas flat → HPA not scaling (section 11)
    └─ anything else right after a change → roll back first, diagnose second (section 1)
```

---

## 13. Self-check and exit test

> 📚 **Study path:** 1) Practice: [Kubernetes Challenges](https://kodekloud.com/courses/kubernetes-challenges) (free, timed) · 2) KodeKloud: *Ultimate Certified Kubernetes Administrator (CKA) Mock Exam Series* ([course](https://kodekloud.com/courses/ultimate-certified-kubernetes-administrator-cka-mock-exam)) · 3) Practice: [killer.sh](https://killer.sh/) in the last two weeks before the CKA exam · 4) Practice: [SadServers](https://sadservers.com/scenarios) scenarios tagged docker and nginx for the Docker half.

Answer the questions without looking, then check against the section named in
the last column. Then do the practical tasks for your stage under a timer.

### Self-check questions

| # | Stage | Question | Key point to check |
|---|---|---|---|
| 1 | [L1 · Junior] | A container shows `Exited (127)`. What does the code tell you before you read any log? | Command not found: wrong CMD or ENTRYPOINT path, missing binary or shell; 126 = not executable (section 2) |
| 2 | [L1 · Junior] | Why is `docker rm -f` a bad first move on a crashing container? | It deletes the logs and the writable layer, the evidence; save `docker logs` and `docker inspect` first (section 1) |
| 3 | [L1 · Junior] | `port is already allocated` versus `bind: address already in use`: which owner does each point to? | Docker's own allocator (another container) versus a host process such as Apache (section 3) |
| 4 | [L1 · Junior] | Which daemon.json settings stop logs filling the disk, and which containers do they affect? | `log-opts` with `max-size` and `max-file`; only containers created after the change (section 5) |
| 5 | [L2 · Mid] | UFW denies 8080, yet 8080 answers from the internet. Explain the packet path in two sentences. | DNAT in PREROUTING sends it through FORWARD, so UFW's INPUT rules never see it; bind to 127.0.0.1 or filter in DOCKER-USER (section 3) |
| 6 | [L2 · Mid] | A container's resolv.conf says `nameserver 127.0.0.11`. What is it, and when does Docker fall back to 8.8.8.8? | The embedded DNS of user-defined networks; public servers there usually come from a `dns` override, while the 8.8.8.8 fallback hits the default bridge network and image builds when the host's resolv.conf lists only loopback resolvers (section 4) |
| 7 | [L2 · Mid] | Traefik returns `404 page not found` for a Compose app whose domain you just changed. First hypothesis? | Labels are read at deploy time: no router for the new Host until you redeploy; then check http vs https entrypoint (section 7) |
| 8 | [L2 · Mid] | Traefik returns 502. Give three causes in the order you test them. | Wrong port in the domain or label; app bound to 127.0.0.1 inside the container; container not on dokploy-network (section 7) |
| 9 | [L2 · Mid] | The browser shows `TRAEFIK DEFAULT CERT`. What does an HTTP-01 challenge need? | A DNS A record pointing at this host, port 80 open from the internet to Traefik, a writable acme.json, no rate limit hit (section 7) |
| 10 | [L2 · Mid] | Where does Docker look for Harbor's private CA, and where does containerd look? | `/etc/docker/certs.d/HARBOR/ca.crt`; `/etc/containerd/certs.d/HARBOR/hosts.toml` on every node (sections 6 and 8) |
| 11 | [L3 · Senior] | After `docker compose up` on a new host, SSH from the office drops. Cause and fleet-wide prevention? | A new bridge took a subnet that overlaps the office LAN; set `default-address-pools` (and `bip`) from the IP plan (section 4) |
| 12 | [L3 · Senior] | Pod is `Running` but `0/1` and the Service has no endpoints. What do you read next, and why not the Ingress? | Readiness probe events in `describe pod`; bottom-up, the Ingress can only return 503 until endpoints exist (section 9) |
| 13 | [L3 · Senior] | `kubectl logs POD` is empty for a CrashLoopBackOff pod. Which flag, and what if that is empty too? | `--previous`; then `describe` Last State: exit code, OOMKilled, liveness kill (section 8) |
| 14 | [L3 · Senior] | CoreDNS logs `Loop ... detected`. Which node file is to blame and what is the fix? | `/etc/resolv.conf` with 127.0.0.53; point kubelet `resolvConf` at `/run/systemd/resolve/resolv.conf`, restart kubelet and CoreDNS (section 9) |
| 15 | [L3 · Senior] | After a new NetworkPolicy every request times out, even by name. What did it forget? | Egress to kube-dns on UDP and TCP 53; also check AND vs OR selectors (section 9) |
| 16 | [L3 · Senior] | `connection to the server 192.0.2.20:6443 was refused`. You have SSH to the node. First three commands? | `sudo crictl ps -a --name kube-apiserver`, `sudo crictl logs CONTAINER`, `sudo journalctl -u kubelet -n 50`; back up the manifest outside the manifests folder before editing (section 10) |
| 17 | [L3 · Senior] | A rollout `exceeded its progress deadline`. Is the app down? How do you tell, and what is the fastest safe action? | `Available` condition and the old ReplicaSet; `rollout undo` if users are affected, then debug the new pods (section 11) |
| 18 | [L3 · Senior] | The HPA shows `cpu: <unknown>/70%`. Two most common causes? | metrics-server missing or failing (often kubelet certificate IP SANs), or no CPU request on the pods (section 11) |
| 19 | [L4 · Lead] | Your kubeadm cluster is 11 months old and was never upgraded. What happens next month, and what do you schedule today? | Leaf certificates expire at one year; schedule an upgrade or `kubeadm certs renew all` with a static-pod restart, and add expiry alerting (section 10) |
| 20 | [L4 · Lead] | Which "Prevent it next time" item from this module did you turn into a team standard, and how do you know it is followed? | Evidence is a check, not a wiki page: a CI rule against `0.0.0.0` publications, daemon.json from Ansible, an expiry alert |

### Practical exit test

Do these on a lab only: a KodeKloud playground, a SadServers box or your
homelab, never production. Ideally someone else (or a script) breaks the system
so you do not know the cause. You may use this module, nothing else. You pass a
task when it is fixed within the time **and** you have written the five-line
incident note from section 1 naming the deciding evidence.

| Stage | What gets broken | Your task | Time |
|---|---|---|---|
| [L1 · Junior] | A Compose service whose start script lost its execute bit | Name the cause from the exit code alone, fix the image, service stays Up for 5 minutes | 10 min |
| [L1 · Junior] | A host process takes 8080 before the app container starts | Name the owner (PID, unit or container, log command) and resolve it without stopping the wrong thing | 5 min |
| [L1 · Junior] | A container logs in a tight loop until `/var/lib/docker` is full | Free space without deleting volumes or in-use images, then add log rotation | 15 min |
| [L2 · Mid] | The host's resolv.conf is loopback-only, outbound DNS to the internet is blocked, and a default-bridge container (or a `docker build`) must resolve names | Prove with tcpdump in the container's namespace where queries go; fix with the `dns` key in daemon.json | 20 min |
| [L2 · Mid] | A Traefik port label points at the wrong port | Fix the 502 from Traefik's logs alone (an Ops Ladder drill) | 15 min |
| [L2 · Mid] | A database container is published on 0.0.0.0:5432 with UFW "denying" 5432 | Prove the exposure from a second machine, close it properly, prove it again | 20 min |
| [L2 · Mid] | A registry with a private CA that the host does not trust | Make Docker trust it without `insecure-registries` | 20 min |
| [L3 · Senior] | kubelet stopped (or pointed at the wrong containerd socket) on a worker | Node back to Ready, explained from `journalctl -u kubelet` | 15 min |
| [L3 · Senior] | The node's resolv.conf points at 127.0.0.53 and CoreDNS is restarted | Find the loop, fix kubelet's `resolvConf`, CoreDNS Running | 20 min |
| [L3 · Senior] | A wrong Service targetPort **and** a readiness probe on a wrong path | Ingress returns 200 again; name both faults in the note | 20 min |
| [L3 · Senior] | A typo in the kube-apiserver static pod manifest | kubectl works again; manifest backed up outside the folder before editing | 15 min |
| [L3 · Senior] | A rollout to an image tag that does not exist | Service healthy within 5 minutes via rollback, then fixed forward | 15 min |
| [L3 · Senior] | A two-node Swarm on hosts with MTU 1450 | Prove the MTU problem with a don't-fragment ping and fix the overlay | 30 min |
| [L4 · Lead] | Game day: a script breaks one of the above at random in the homelab | Learn about it from an alert, fix it, publish a one-page postmortem within 24 hours | 1 day |
| [L4 · Lead] | Nothing breaks: this is a rehearsal | Renew kubeadm certificates on every control-plane node end to end and write the runbook | 45 min |

You have passed a stage when you complete all of its tasks within the time on
two different days. Record the result in your incident notes; the
[career ladder](40-career-ladder.md) uses exactly this kind of evidence.

---

## 14. Where to go next

> 📚 **Study path:** 1) Note: the learn module for any task you failed: [Learn Docker](30-learn-docker.md) or [Learn Kubernetes](31-learn-kubernetes.md) · 2) KodeKloud: the course named in that section's study path, its labs first · 3) Practice: the drill for your level in the [roadmap](34-roadmap.md) · 4) Note: [Career ladder](40-career-ladder.md) to see which stage your exit-test results support.

Pick the row that matches what you just found out about yourself:

| If you… | Read next | Why |
|---|---|---|
| need the commands behind these steps | [Docker reference](14-docker-containers.md), [Kubernetes reference](15-kubernetes.md) | flags and output fields, without the story |
| failed a Docker task (sections 2–6) | [Learn Docker](30-learn-docker.md) | namespaces, networking, daemon.json and Swarm explained from first principles |
| failed a Kubernetes task (sections 8–11) | [Learn Kubernetes](31-learn-kubernetes.md) | the CKA-aligned path with break-and-fix labs |
| struggled with Traefik, Apache or certificates | [Learn web servers & proxies](29-learn-webservers-proxies.md), [Learn networking](28-learn-networking.md) | Host and SNI routing, TLS and ACME, the timeouts chain |
| are about to move another Apache site into Dokploy | [Case study: Apache, 443 and Dokploy](21-case-apache-443-dokploy.md), [Deployment patterns](35-deployment-patterns.md) | the real migration runbook and safe ways to cut over |
| could not tell which layer was broken | [Site down playbook](25-playbook-site-down.md), [Who owns this port?](22-playbook-ports-inventory.md) | the layered walk outside the container platform |
| passed everything for your stage | [Career ladder](40-career-ladder.md), [Senior architecture](39-learn-senior-architecture.md) | the next stage's scope: designing so these incidents cannot happen |

The habit that turns this module into seniority is the last line of every
scenario: **Prevent it next time**. A Junior fixes the incident; a Mid-level
engineer fixes it with evidence and writes the note; a Senior makes sure the
whole fleet cannot have it again; a Lead makes that the team's default.
