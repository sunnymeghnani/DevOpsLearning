# 14 — Docker & Container Troubleshooting

Typical symptoms: container exits immediately, restart loops, can't reach the
app inside, image pulls fail, disk filled by Docker, "works on my machine".

---

## 1. State of the world

```bash
docker ps                                  # running containers
docker ps -a                               # + exited ones (see EXIT CODES) ★
docker ps -a --filter status=exited
docker stats                               # live CPU/mem/net/io per container
docker system df                           # disk used by images/containers/volumes ★
docker info                                # daemon config, storage driver, runtime
docker version
systemctl status docker                    # the daemon itself
journalctl -u docker -e                    # daemon logs (pull errors, OOM, networking)
```

```
$ docker ps -a
CONTAINER ID  IMAGE         STATUS                            PORTS                  NAMES
f3a91c2ee01a  webapp:2.1    Up 3 hours                        0.0.0.0:8080->80/tcp   web
9c2d11ab4e77  worker:2.1    Restarting (1) 20 seconds ago                            worker
71b0d9c3aa15  migrate:2.1   Exited (0) 3 hours ago                                   migrate
0d4e8f7b3c21  cache:7       Exited (137) 10 minutes ago                              redis
```
Reading it: `web` is fine • `worker` is **crash-looping** (exit code 1 in
parentheses — read `docker logs worker`) • `migrate` exited 0 = a one-shot job
that finished normally • `redis` exited **137** = killed, most likely OOM —
confirm with `docker inspect --format '{{.State.OOMKilled}}' redis`.

Exit codes tell the story (`docker ps -a` STATUS column):

| Code | Meaning |
|---|---|
| 0 | normal exit — for services: the process finished (wrong CMD? ran in background?) |
| 1 / app-specific | app error → `docker logs` |
| 125 | docker itself failed to run the container (bad flags) |
| 126 | entrypoint not executable |
| 127 | entrypoint/command not found |
| **137** | SIGKILL — **OOM-killed** (or docker kill / stop timeout). Check `docker inspect --format '{{.State.OOMKilled}}' c1` |
| 139 | segfault |
| 143 | SIGTERM (normal stop) |

## 2. Logs & inspection

```bash
docker logs c1                             # stdout/stderr of the container
docker logs -f --tail 100 c1               # follow last 100
docker logs c1 --since 10m
docker logs c1 2>&1 | grep -i error
docker inspect c1                          # EVERYTHING: config, mounts, network, state
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' c1
docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' c1
docker inspect --format '{{json .Mounts}}' c1 | jq
docker top c1                              # processes inside, from outside
docker diff c1                             # files changed since image start
docker events --since 1h                   # daemon event stream (kills, ooms, restarts)
```

## 3. Getting inside

```bash
docker exec -it c1 sh                      # shell in a running container (bash if present)
docker exec c1 env                         # env vars as the app sees them
docker exec c1 cat /etc/resolv.conf        # DNS inside
docker run -it --entrypoint sh image:tag   # container won't start? bypass entrypoint
                                           #   and poke around the image ★
docker cp c1:/app/config.yml /tmp/         # copy files out (works on stopped too)
docker export c1 | tar tv | less           # full filesystem listing of a container
```
Distroless/minimal image with no shell:
```bash
docker debug c1                            # Docker Desktop only (a paid-plan feature): not in Docker Engine
                                           #   or Ubuntu's docker.io. Anywhere else, a toolbox that shares
                                           #   c1's processes and network:
docker run --rm -it --pid container:c1 --network container:c1 nicolaka/netshoot
# or nsenter from the host:
PID=$(docker inspect -f '{{.State.Pid}}' c1)
nsenter -t $PID -n ss -tlnp                # run HOST tools inside container's netns ★
nsenter -t $PID -n -m -p ps aux
```

## 4. Networking

```bash
docker network ls
docker network inspect bridge              # who's on it, subnet, gateway
docker port c1                             # published port mappings
ss -tlnp | grep docker-proxy               # host side of -p mappings
iptables -t nat -L DOCKER -n               # NAT rules docker created
docker run --rm --network container:c1 nicolaka/netshoot ss -tlnp
                                           # full net toolbox INSIDE c1's network ns ★
```
Common cases:

- **Port published but connection refused** → app inside binds `127.0.0.1`;
  it must bind `0.0.0.0` inside the container.
- **Container can't resolve names** → check `/etc/resolv.conf` inside; daemon DNS
  options; corporate VPN/DNS conflicts with the docker bridge subnet (172.17/16) —
  change `bip`/`default-address-pools` in `/etc/docker/daemon.json`.
- **Container-to-container by name fails** → name resolution only works on
  **user-defined** networks, not the default bridge: `docker network create app && docker run --network app ...`

## 5. Images & registry

```bash
docker images ; docker images --digests
docker pull image:tag                      # manual pull shows the real error
docker history image:tag                   # layer sizes — what bloats the image
docker manifest inspect image:tag          # does it exist for your ARCH? (arm64 vs amd64 ★)
docker login registry.example.com
docker build --no-cache -t app .           # rule out stale build cache
docker build --progress=plain -t app .     # full build output
```
Pull failures: `unauthorized` → login/token expired; `manifest unknown` → tag typo
or missing arch; TLS/x509 → proxy or private CA (add CA to
`/etc/docker/certs.d/registry:5000/ca.crt`); timeouts → proxy env for the DAEMON
(`systemctl show docker -p Environment`), not just your shell.

## 6. Disk usage & cleanup

```bash
docker system df -v                        # per-image/container/volume detail
docker system prune                        # stopped containers, dangling images, networks
docker system prune -a --volumes           # AGGRESSIVE: also unused images and volumes —
                                           #   make sure nothing needed is "unused"!
docker volume ls ; docker volume prune
du -sh /var/lib/docker/                    # daemon storage root
docker logs c1 2>/dev/null | wc -c         # huge? cap logs in daemon.json:
# { "log-driver": "json-file", "log-opts": { "max-size": "50m", "max-file": "3" } }
```
JSON log files live at `/var/lib/docker/containers/<id>/<id>-json.log` — a classic
disk-filler on hosts without log-opts.

## 7. Resources

```bash
docker stats --no-stream                   # snapshot
docker run -m 512m --cpus 1.5 image        # set limits
docker inspect -f '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}' c1
docker update -m 1g --memory-swap 2g c1    # change limits live
```
137/OOMKilled → raise `-m`, or fix the app; remember: host `free -h` can look fine
while the *container's* cgroup limit is hit.

## 8. docker compose

```bash
docker compose ps ; docker compose logs -f svc
docker compose config                      # rendered effective config (env substituted) ★
docker compose up -d --force-recreate svc
docker compose exec svc sh
docker compose down && docker compose up -d    # full recycle (keeps volumes)
```

## 9. containerd / K8s nodes without docker CLI

```bash
crictl ps ; crictl ps -a                   # containers (uses CRI)
crictl logs <id> ; crictl inspect <id>
crictl images ; crictl pull image
ctr -n k8s.io containers list              # containerd directly
journalctl -u containerd -e ; journalctl -u kubelet -e
```
