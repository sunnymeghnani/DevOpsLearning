# Docker, Compose, Swarm & container runtimes

Containers fail in layers, so check them in that order: the container's state and exit code (`docker ps -a`, `docker inspect`), what the app said (`docker logs`) and what the engine did to it (`docker events`), then its network, volumes and image, then the engine and the orchestrator around it (Compose, Swarm, Dokploy). On Kubernetes nodes the Docker CLI is often missing or blind; `crictl`, `ctr` and `nsenter` reach the runtime and the namespaces directly.

| If you would reach for | Prefer | Because |
|---|---|---|
| `docker ps` | `docker ps -a` | a container that crashed and stayed down is missing from plain `ps`; `-a` shows it with its exit code |
| `docker logs c1 | grep error` | `docker logs --since 10m c1 2>&1 | grep -i error` | the app's stderr arrives on docker's stderr, which a plain pipe never sees |
| reading `Exited (137)` in `docker ps` as "it crashed" | `docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' c1` | 137 is any SIGKILL; OOMKilled says whether memory was the reason |
| `docker exec c1 ss -tlnp` in a slim image | `nsenter -t PID -n ss -tlnp` | the host's tools in the container's network, even when the image has none |
| `docker ps` on a Swarm or Dokploy host | `docker service ps --no-trunc SERVICE` | a task that never got a container (no image, no node) exists only in the task list |
| `docker restart c1` | `docker logs`, `docker inspect`, `docker events --since 1h` first | the restart replaces the failing process, and its state goes with it |
| `docker compose restart` | `docker compose up -d` | restart ignores changes to the compose file and `.env` |
| `docker system prune -a --volumes` | `docker system df -v`, then a targeted prune | see what is reclaimable first; volumes hold data |

### docker ps — which containers exist, which crashed, and how they exited
Match: docker ps
Instead of: docker ps without -a, ps aux | grep
Safety: read-only

**In one line:** `docker ps` lists containers with image, status and published ports; `-a` adds the stopped ones, whose STATUS carries the exit code that says how each one ended.

**Read the command:** `docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'`

| Part | Meaning |
|---|---|
| `-a` | all containers: exited, created and restarting as well as running |
| `--format 'table …'` | a Go template; `table` prints a header row, `\t` separates the columns |
| `{{.Names}}` `{{.Image}}` `{{.Status}}` `{{.Ports}}` | only these columns, so nothing is cut or wrapped |
| `--filter status=exited` | only exited containers (also `running`, `restarting`, `created`, `paused`, `dead`) |
| `--filter name='^app$'` | the name filter is a regular expression: the anchors stop `app` matching `app-worker` |
| `--filter publish=443` | only containers that publish port 443 |

**What the output tells you:**

```
NAMES     IMAGE         STATUS                          PORTS
web       webapp:2.1    Up 3 hours (healthy)            127.0.0.1:18000->8000/tcp
worker    worker:2.1    Restarting (1) 20 seconds ago
migrate   migrate:2.1   Exited (0) 3 hours ago
redis     redis:7       Exited (137) 10 minutes ago
```

`Restarting (1)` is a crash loop with exit code 1; `Exited (0)` a job that finished; `Exited (137)` a SIGKILL, often the OOM killer. `(healthy)` appears only when a HEALTHCHECK is defined. PORTS reads host address:port → container port; `8000/tcp` alone would mean exposed but not published.

**Why it is effective:** one screen answers "is it running, did it crash, how did it end, where can I reach it?", and the exit code picks the next tool: 1 → logs, 137 → OOM check, 127 → command not found in the image.

**Compared with plain `docker ps` or `ps aux | grep`:** plain `docker ps` is enough to confirm "it is up", but a container that crashed and was not restarted is simply absent. `ps aux` finds the process, not its container, image or ports.

**Trap:** `Up 2 seconds` may be one moment of a crash loop: run it again, or check `{{.RestartCount}}` with `docker inspect`. "Up" is not "working": without a healthcheck Docker only knows the process exists. Containers behind Traefik or Dokploy normally show **empty** PORTS; they are reached over a Docker network, not a host port.

**Next step:** `Exited (137)` → `docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}'`. `Restarting` or `Exited (1)` → `docker logs --tail 100`. Port missing → `docker port`, then `ss -tlnp`. Dokploy or Swarm app without a container → `docker service ps --no-trunc`.

### docker inspect — why it stopped, and what it really runs with
Match: docker inspect
Instead of: docker ps, docker logs
Safety: read-only · the full output includes environment variables, which often hold secrets

**In one line:** `docker inspect` prints the engine's complete JSON record of a container (or of an image, network or volume): configuration, state, exit code, OOM flag, health-check results, mounts, networks and limits; `--format` extracts just the field you need.

**Read the command:** `docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' c1`

| Part | Meaning |
|---|---|
| `--format` (`-f`) | a Go template over the JSON instead of hundreds of lines |
| `.State.ExitCode` | the main process's last exit code |
| `.State.OOMKilled` | `true` if the out-of-memory killer ended it |
| `.State.Status`, `.RestartCount` | `running`, `exited`, `restarting` …, and how often the restart policy has restarted it |
| `{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}` | the IP on every attached network |
| `{{json .State.Health}}` | health status, failing streak and the output of the last probes |
| `{{json .Mounts}}` | each volume and bind mount: host source, container destination |
| `.HostConfig.Memory`, `.HostConfig.NanoCpus`, `.State.Pid` | limits in bytes and in billionths of a CPU (`0` = none); the host PID for `nsenter` |

**What the output tells you:**

```
$ docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' redis
137 true
```

`137 true`: the OOM killer ended it, usually because of the container's own memory limit. `137 false`: something else sent SIGKILL, such as a `docker stop` that timed out, `docker kill` or an orchestrator. `0`: the process ended by itself (its command finished, or it went to the background).

**Why it is effective:** `docker ps` says "Exited (137)" but not **who** killed the process. inspect separates OOM from a manual kill and shows the limits, mounts and health-check output the container really has, not what the compose file was supposed to give it, and it works on stopped containers.

**Compared with `docker ps` / `docker logs`:** ps gives state and exit code in one line, enough for "is it up?"; logs give the app's side. Neither shows OOM, limits, mounts or probe output.

**Trap:** without `--format` the output includes `Config.Env`, where passwords and tokens often sit: never paste it whole into a ticket. `{{json .State.Health}}` prints `null` when no healthcheck is defined, which is not the same as healthy. If an image and a container share a name, add `--type container`.

**Next step:** OOM → `docker stats --no-stream`, then `docker update -m` or fix the leak. Unhealthy → run the health command yourself with `docker exec`. Wrong mount source → fix the compose `volumes:`. Tools needed inside → `.State.Pid` with `nsenter`.

### docker logs — what the app printed before it failed
Match: docker logs
Instead of: cat /var/lib/docker/containers/ID/ID-json.log, journalctl -u docker
Safety: read-only

**In one line:** `docker logs` replays what the container's main process wrote to stdout and stderr, as stored by the logging driver, for running **and** stopped containers.

**Read the command:** `docker logs -f --tail 100 c1`

| Part | Meaning |
|---|---|
| `-f` | follow: keep printing new lines until Ctrl-C |
| `--tail 100` | start with the last 100 lines instead of the whole history |
| `c1` | container name or ID; a stopped container works too |
| `--since 10m` | only the last 10 minutes (a timestamp also works); `--until` closes the window |
| `-t` | prefix every line with the time Docker received it |
| `2>&1` | the container's stderr comes out on docker's stderr; this merges it into the pipe |

**What the output tells you:**

```
$ docker logs --since 10m -t c1 2>&1 | tail -3
2026-10-04T09:12:01.512304118Z Starting app on :8000
2026-10-04T09:12:02.031877240Z Error: connect ECONNREFUSED 10.0.2.15:5432
2026-10-04T09:12:02.035101952Z exiting with code 1
```

The last lines before a crash usually name the cause. The history includes **every previous run** of the same container, so a crash loop shows the same error repeated; `-t` lets you line it up with `docker events` and host logs.

**Why it is effective:** it is the application's own explanation (stack trace, "address already in use", "permission denied") without knowing where any log file lives, and it still works after the container died, when `docker exec` no longer can.

**Compared with the json file or `journalctl -u docker`:** the file under `/var/lib/docker/containers/` holds the same lines as raw JSON, useful only when the CLI is unusable. `journalctl -u docker` is the **daemon's** log (pulls, networking), not the app's.

**Trap:** without `2>&1`, `docker logs c1 | grep -i error` silently skips stderr. Empty output does not mean "no errors": the app may log to a file inside the container, or the log driver may send logs elsewhere (`docker info --format '{{.LoggingDriver}}'`). Logs belong to one container: after `docker rm`, `compose up --force-recreate` or a Dokploy redeploy, the new container starts empty.

**Next step:** error names a host or port → `docker exec c1 cat /etc/resolv.conf`, `docker network inspect`. Exit without a message → `docker inspect` (ExitCode, OOMKilled). Logs filling the disk → `--log-opt max-size` or daemon-wide `log-opts`.

### docker events — what the engine did to your containers, and when
Match: docker events
Instead of: journalctl -u docker, docker ps
Safety: read-only

**In one line:** `docker events` prints the daemon's event stream (container create, start, die with exit code, oom, kill, restart and health changes, plus image, network and volume events), so you can rebuild the timeline of an incident.

**Read the command:** `docker events --since 30m --filter type=container --filter event=die --filter event=oom`

| Part | Meaning |
|---|---|
| `--since 30m` | replay events from the last 30 minutes (a timestamp also works) |
| `--filter type=container` | container events only (others include `image`, `network`, `volume`, `daemon`) |
| `--filter event=die --filter event=oom` | the same key twice is OR: die **or** oom; different keys are AND |
| `--until 0s` | stop at "now" and return; without `--until` it keeps streaming new events |
| `--filter container=metabase` | one container only |
| `--format '{{.Time}} {{.Action}} {{.Actor.Attributes.name}}'` | compact lines: Unix time, action, container name |

**What the output tells you:**

```
2026-10-04T09:41:02.118250310Z container oom 4c1e9a… (image=shop-api:1.4.2, name=shop-api)
2026-10-04T09:41:02.402914771Z container die 4c1e9a… (exitCode=137, image=shop-api:1.4.2, name=shop-api)
2026-10-04T09:41:03.010455102Z container start 4c1e9a… (image=shop-api:1.4.2, name=shop-api)
```

`oom`, then `die` with `exitCode=137`, then `start`: the memory limit killed it and the restart policy brought it back. A `kill` with `signal=15` before `die` means someone or something stopped it, such as a deploy or `docker stop`.

**Why it is effective:** logs show what the app said; events show what **Docker** did to it, with exact times, including the 3 a.m. restarts and OOM kills the app never got to log.

**Compared with `journalctl -u docker` / `docker ps`:** the journal holds the daemon's own messages (errors, network setup) but no clean lifecycle per container; `docker ps` shows only the current state, not the history behind it.

**Trap:** the event backlog lives in the daemon's memory: it is limited in size and lost when the daemon restarts, so "no events" for yesterday proves nothing. A script that runs `docker events --since …` without `--until` never finishes.

**Next step:** `oom` → `docker stats` and the limits in `docker inspect`. Repeated `die`/`start` → `docker logs --since`. A `kill` you did not expect → check deploys, cron jobs and orchestrators (Dokploy, Swarm, auto-updaters).

### docker stats — CPU, memory, I/O and process count per container
Match: docker stats
Instead of: top, htop, free -h
Safety: read-only

**In one line:** `docker stats` reads each container's cgroup counters and shows CPU %, memory against its limit, network and block I/O and the number of processes, one row per container.

**Read the command:** `docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.BlockIO}}\t{{.PIDs}}'`

| Part | Meaning |
|---|---|
| `--no-stream` | one snapshot, then exit (without it the screen refreshes until Ctrl-C) |
| `--format 'table …'` | choose the columns; `table` keeps the header |
| `{{.CPUPerc}}` | CPU use, where 100% is one full core: 250% is two and a half cores |
| `{{.MemUsage}}`, `{{.MemPerc}}` | memory used / limit, and the same as a percentage of the limit |
| `{{.BlockIO}}` | bytes read / written to block devices since the container started |
| `{{.PIDs}}` | processes and threads in the container |
| `CONTAINER` at the end | only this container |

**What the output tells you:**

```
NAME       CPU %     MEM USAGE / LIMIT    BLOCK I/O        PIDS
shop-api   148.20%   1.43GiB / 1.5GiB     12.1MB / 0B      61
shop-db    3.10%     402MiB / 15.6GiB     2.3GB / 8.1GB    24
```

`shop-api` is at 95% of its 1.5 GiB limit: the next spike gets it OOM-killed. `shop-db` shows the host's whole RAM as its limit, which means **no limit is set**.

**Why it is effective:** `free -h` can look healthy while one container sits at its own cgroup limit. stats groups usage per container and puts it next to the limit that will actually kill it.

**Compared with `top` / `htop` / `free -h`:** better for "which process?" (combine with `docker top`) and for the host as a whole, but they cannot show a container's limit or group processes by container.

**Trap:** CPU % does not show **throttling**: a container limited with `--cpus 1.5` can be slow while its CPU % looks modest. `docker exec CONTAINER cat /sys/fs/cgroup/cpu.stat` (cgroup v2) shows it: a growing `nr_throttled` means the limit is biting. MEM USAGE leaves out inactive file cache, so it differs from raw cgroup or `free` figures.

**Next step:** near the memory limit → `docker inspect` for OOMKilled, then raise it with `docker update -m` or fix the leak. High CPU → `docker top`. Heavy block I/O → `iostat -xz 1` on the host.

### docker top — the processes in a container, seen from the host
Match: docker top
Instead of: docker exec c1 ps aux
Safety: read-only

**In one line:** `docker top` lists a running container's processes using the **host's** `ps`, so it works even when the image has no `ps`, and it shows host PIDs that other host tools understand.

**Read the command:** `docker top CONTAINER -o pid,ppid,user,etime,args`

| Part | Meaning |
|---|---|
| `CONTAINER` | name or ID of a running container |
| `-o …` | everything after the container is passed to `ps`; without it Docker uses `-ef` |
| `pid`, `ppid` | host PID and parent PID: who started what |
| `user` | the process's user, resolved on the host |
| `etime` | time since each process started: young workers beside an old master mean restarts |
| `args` | the full command line |
| `-eo pid,rss,args` | resident memory (KiB) per process, to find the one that grows |

**What the output tells you:**

```
PID      PPID     USER   ELAPSED       COMMAND
48211    48190    999    3-02:11:45    postgres -D /var/lib/postgresql/data
51877    48211    999    00:00:04      postgres: app shop 10.0.2.7(51544) idle
```

PID 48211 is the host PID of what the container calls PID 1; its parent is the container's shim process.

**Why it is effective:** nothing has to exist inside the image and no shell is started in the container; the host PIDs go straight into `nsenter -t`, `strace -p` or `/proc/PID/status`.

**Compared with `docker exec c1 ps aux`:** shows container-local PIDs (1, 7, 12 …) and the image's user names, which match the app's own logs, but only if the image ships `ps`.

**Trap:** user names are looked up in the **host's** user database, so container UID 999 may print as an unrelated host account or as a bare number. Host PIDs do not match the ones the app logs ("worker 7 exited").

**Next step:** one process with growing RSS → `docker stats`, then a heap or thread dump (`docker exec CONTAINER jstack 1`). Many zombie children → PID 1 does not reap them; run with `--init` or fix the entrypoint.

### docker exec — run a command inside a running container
Match: docker exec
Instead of: docker attach
Safety: depends on what you run · the extra process can change the container (lost again on recreate)

**In one line:** `docker exec` starts an **extra** process inside a running container's namespaces, so you see its filesystem, network, DNS and environment exactly as the app sees them.

**Read the command:** `docker exec dokploy-traefik wget -qO- http://127.0.0.1:8080/api/http/routers`

| Part | Meaning |
|---|---|
| `dokploy-traefik` | the target container (name or ID); it must be running |
| `wget` | a program from **inside the image**: Traefik's Alpine-based image has BusyBox `wget`, not `curl` |
| `-q`, `-O-` | wget: quiet, write the response body to stdout |
| `http://127.0.0.1:8080/api/http/routers` | the container's **own** loopback, where Traefik's API listens when enabled; not published on the host |
| `-it … sh` | as in `docker exec -it c1 sh`: keep stdin open and allocate a terminal for an interactive shell |
| `env`, `cat /etc/resolv.conf` | the variables the container was given, and the DNS servers it uses |

**What the output tells you:** here, Traefik's JSON list of routers with each rule, entry point, service and status, as Traefik itself has loaded them. `cat /etc/resolv.conf` on a user-defined network shows `nameserver 127.0.0.11`: Docker's embedded DNS, which resolves other containers by name.

**Why it is effective:** it answers "what does the **app** see?": `curl 127.0.0.1:8080` on the host reaches a different loopback. DNS, variables, mounted files and permissions are all checked from the inside.

**Compared with `docker attach`:** attach connects your terminal to the **main** process's stdin and stdout, where Ctrl-C can stop the container. exec starts a separate process and leaves PID 1 alone.

**Trap:** distroless and slim images have no `sh`, `curl` or `ps`, and exec fails with "executable file not found". `docker exec c1 env` shows the configured environment, not what the entrypoint script exported for PID 1 (that is in `/proc/1/environ`). Anything you change inside disappears when the container is recreated.

**Next step:** no tools in the image → `docker run --rm --network container:c1 nicolaka/netshoot …` or `nsenter -t PID -n`. Container not running → `docker logs`, `docker inspect`, or `docker run -it --entrypoint sh image:tag` to explore the image.

### docker port — which host addresses and ports a container publishes
Match: docker port
Instead of: the PORTS column of docker ps, netstat -tlnp
Safety: read-only

**In one line:** `docker port` prints a container's published port mappings, container port → host address and port, one per line.

**Read the command:** `docker port dokploy-traefik`

| Part | Meaning |
|---|---|
| `port` | list the mappings Docker set up from `-p` or a compose `ports:` entry |
| `dokploy-traefik` | the container to look at |
| `443/tcp` (optional, as in `docker port c1 443/tcp`) | only where that container port is published |

**What the output tells you:**

```
80/tcp -> 0.0.0.0:80
80/tcp -> [::]:80
443/tcp -> 0.0.0.0:443
443/tcp -> [::]:443
```

Left: the port inside the container. Right: the host side. `0.0.0.0` and `[::]` mean every IPv4 and IPv6 interface, so reachable from outside unless something blocks it; `127.0.0.1:18000` would mean "only from this host", the usual pattern behind a host reverse proxy such as Apache. No output: nothing is published, or the container uses `--network host` and binds host ports directly (then `ss -tlnp` shows the real process).

**Why it is effective:** a clean, untruncated answer to "where can the host reach this container?", easier to read and to script than the crowded PORTS column of `docker ps`.

**Compared with `docker ps` / `ss -tlnp` / `netstat -tlnp`:** ps shows the same mappings squeezed into one column. ss and netstat show what the host listens on (often `docker-proxy`) but not which container is behind it; `docker port` shows the mapping but not whether the app inside answers. Use both.

**Trap:** a mapping proves only that Docker forwards the port: if the app inside binds `127.0.0.1` instead of `0.0.0.0`, connections are reset. Published ports are handled by Docker's own iptables rules (NAT and FORWARD), so UFW's INPUT rules do not block them. Swarm services published through the ingress mesh may show nothing here: check `docker service inspect`.

**Next step:** mapping present but no answer → `nsenter -t PID -n ss -tlnp` to see what the app binds. Exposed to the world by mistake → publish as `-p 127.0.0.1:HOST:CONTAINER`, or filter in the `DOCKER-USER` chain.

### docker network — who is on which network, with which subnet
Match: docker network
Instead of: ip addr, docker inspect on every container
Safety: read-only for ls and inspect · create, rm, connect, disconnect and prune change networking

**In one line:** `docker network ls` lists networks with driver and scope; `docker network inspect` shows a network's subnet, gateway, options and the containers attached to it, with their IPs.

**Read the command:** `docker network inspect dokploy-network --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'`

| Part | Meaning |
|---|---|
| `dokploy-network` | the network Dokploy attaches Traefik and the apps to |
| `{{range .Containers}}…{{end}}` | loop over the containers attached **on this host** |
| `{{.Name}} {{.IPv4Address}}` | container name and address with prefix length, e.g. `10.0.1.12/24` |
| `{{"\n"}}` | a newline after each one |
| `--format '{{range .IPAM.Config}}{{.Subnet}} gw={{.Gateway}}{{end}}'` | the network's subnet and gateway |
| `--format '{{.Driver}} {{json .Options}}'` | driver (`bridge`, `overlay`, `macvlan` …) and options such as the MTU |
| `network ls` | NAME, DRIVER and SCOPE (`local` or `swarm`) of every network |

**What the output tells you:**

```
dokploy-traefik 10.0.1.4/24
shop-web.1.mz3w4b2v0q5h 10.0.1.12/24
```

If Traefik and the app are not both listed, they cannot reach each other and Traefik returns gateway errors (502/504) for that site. A subnet that overlaps your LAN, VPN or VPC makes traffic to those real addresses vanish into the Docker network.

**Why it is effective:** one command answers both classic questions, "are these containers on the same network?" and "does Docker's address range collide with a real one?", without inspecting containers one by one.

**Compared with `ip addr`:** it shows the bridges (`docker0`, `br-…`) and their addresses, enough to spot a clash on this host, but not which containers sit behind each bridge, and nothing about overlay networks.

**Trap:** for an overlay (Swarm) network, `Containers` lists only the containers on the node where you run the command. Containers resolve each other by name only on user-defined networks, never on the default `bridge`. A network's subnet cannot be changed in place: the network has to be removed and recreated, with every container on it.

**Next step:** app missing → attach it (compose `networks:` or the Dokploy settings) and redeploy. Subnet clash → `default-address-pools` in daemon.json (`--default-addr-pool` for Swarm), then recreate the networks. Same network but no answer → test from `docker run --rm --network container:c1 nicolaka/netshoot`.

### docker volume — where persistent data lives, and what a prune would delete
Match: docker volume
Instead of: du -sh /var/lib/docker/volumes/*
Safety: read-only for ls and inspect · create, rm and prune change state (prune deletes data)

**In one line:** `docker volume ls` lists named and anonymous volumes; `inspect` shows where a volume lives on the host, when it was made and which Compose project owns it; `prune` deletes volumes no container references.

**Read the command:** `docker volume ls -f dangling=true`

| Part | Meaning |
|---|---|
| `volume ls` | DRIVER and VOLUME NAME of every volume |
| `-f dangling=true` | only volumes that no container, running **or** stopped, references |
| `--filter name=dokploy` | only names containing `dokploy` |
| `inspect shop_pgdata --format '{{.Mountpoint}}'` | the host directory with the data, normally under `/var/lib/docker/volumes/` |
| `inspect -f '{{.Name}} {{.CreatedAt}} {{.Labels}}' VOLUME` | age and labels; Compose sets `com.docker.compose.project` |
| `volume prune` | delete unused volumes, after a prompt |

**What the output tells you:**

```
DRIVER    VOLUME NAME
local     3f8a1c0d9e7b…
local     shop_pgdata
```

A long hex name is an **anonymous** volume (a `VOLUME` line in a Dockerfile, or `-v /path` without a name); `shop_pgdata` is volume `pgdata` of Compose project `shop`.

**Why it is effective:** the data that matters (databases, uploads) lives in volumes, not in containers. Knowing which volumes are dangling and who owns them is the difference between freeing space and deleting a database.

**Compared with `du` on the volumes directory:** gives sizes (so does `docker system df -v`) but not which volumes are in use or which project they belong to.

**Trap:** "dangling" means "no container **right now**": after `docker compose down`, a database's named volume is dangling until the next `up`, and a prune deletes it. Current engines prune only **anonymous** volumes unless you add `-a`; older ones removed named volumes too, so the same command is far more dangerous on an old host. `docker compose down -v` deletes the project's volumes outright.

**Next step:** sizes → `docker system df -v`. Before any prune, back up what matters, a database with its own dump tool. Unknown volume → `inspect` its labels and creation date.

### docker system — how much disk Docker uses, and what a cleanup would free
Match: docker system
Instead of: du -sh /var/lib/docker
Safety: df is read-only · prune deletes stopped containers, unused networks, images, build cache and (with --volumes) volumes

**In one line:** `docker system df` splits Docker's disk use into images, containers, volumes and build cache, with how much of each is reclaimable; `docker system prune` removes the unused parts.

**Read the command:** `docker system df -v`

| Part | Meaning |
|---|---|
| `system df` | per type: TOTAL, ACTIVE (in use), SIZE and RECLAIMABLE |
| `-v` | every image, container and volume with its size and whether it is in use |
| `system prune` | remove stopped containers, unused networks, dangling images and unused build cache (asks first) |
| `-a` | also every image no container uses, not just dangling ones |
| `--volumes` | also unused volumes (only anonymous ones on current engines): **data** |
| `-f` | no confirmation prompt |

**What the output tells you:**

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          42        9         18.3GB    14.1GB (77%)
Containers      12        9         1.2GB     310MB (25%)
Local Volumes   15        6         36.5GB    4.2GB (11%)
Build Cache     230       0         9.8GB     9.8GB
```

Old images and build cache are the cheap wins here; the volumes are large but mostly in use.

**Why it is effective:** `du -sh /var/lib/docker` only says "Docker is big". system df says *which kind* of object is big and how much a prune would free, before you delete anything.

**Compared with `du`:** still needed for what system df does not count, and the only view when the daemon is down. Never delete files under `/var/lib/docker` by hand: the daemon's metadata goes out of sync.

**Trap:** container **log files** are not in these numbers: a runaway json log under `/var/lib/docker/containers/` fills the disk while system df looks harmless. "Images no container uses" include the previous release you may need for a rollback. `-a --volumes` while a stack is briefly down removes its images and data.

**Next step:** logs → `du -sh /var/lib/docker/containers/*/*-json.log`, then set `log-opts`. Images or cache → `docker image prune -a --filter until=…`, `docker builder prune --filter until=…`. Volumes → `docker volume ls -f dangling=true`, and inspect each before deleting.

### docker run — create and start a new container, with every setting fixed at creation
Match: docker run
Instead of: —
Safety: changes state: creates and starts a container; -p opens host ports

**In one line:** `docker run` creates a **new** container from an image and starts it; ports, environment, restart policy, limits, log rotation and network are fixed into that container, and most can only be changed by recreating it.

**Read the command:** `docker run -d --name app --restart unless-stopped -p 127.0.0.1:18000:8000 --env-file /opt/app/app.env --log-opt max-size=50m --log-opt max-file=3 harbor.example.com/client/app:1.4.2`

| Part | Meaning |
|---|---|
| `-d` | detached: run in the background, print the container ID |
| `--name app` | a fixed name; another `run` with the same name fails with a conflict |
| `--restart unless-stopped` | restart after crashes and daemon or host restarts, unless you stopped it yourself |
| `-p 127.0.0.1:18000:8000` | host 127.0.0.1:18000 → container port 8000: reachable only from this host (e.g. by Apache) |
| `--env-file /opt/app/app.env` | read `KEY=value` lines as environment variables |
| `--log-opt max-size=50m --log-opt max-file=3` | rotate this container's json log: at most 3 files of 50 MB |
| `--rm --network container:c1` | debug runs: delete on exit; share c1's network namespace (its `localhost`) |
| `-it --entrypoint sh` | a shell instead of the entrypoint, to explore an image that will not start |

**What the output tells you:** with `-d`, only the new container's ID. Problems come straight back: `Conflict. The container name "/app" is already in use`, `port is already allocated`, `pull access denied` or `manifest unknown` for the image, and exit code 125 when Docker rejected the command itself.

**Why it is effective:** the command line is the container's whole runtime contract: where it listens, which env file it reads, how it restarts, how big its logs may grow. `-m 512m --cpus 1.5` and `--ulimit nofile=65536:65536` add resource limits.

**Compared with `docker start`:** start reuses an existing container with its original settings and writable layer; `run` always makes a new one.

**Trap:** everything **after the image name** goes to the container's command, not to Docker: `docker run nginx -p 80:80` publishes nothing. `--env-file` takes values literally, so quotes become part of the value. Without log limits (here or in daemon.json) the json log grows until the disk is full. `-p 18000:8000` without an address listens on every interface.

**Next step:** exits at once → `docker logs app`, then `docker run -it --entrypoint sh IMAGE`. Port taken → `ss -tlnp 'sport = :18000'`. Different limits → `docker update`; anything else → remove and run again, or move it into a compose file.

### docker update — change limits or the restart policy of a live container
Match: docker update
Instead of: docker rm and docker run again
Safety: changes state: rewrites the container's resource limits or restart policy while it runs

**In one line:** `docker update` changes a container's memory and CPU limits and its restart policy **in place**, without recreating it, so you can relieve an OOM loop or freeze a crash loop and keep the evidence.

**Read the command:** `docker update -m 1g --memory-swap 2g c1`

| Part | Meaning |
|---|---|
| `-m 1g` (`--memory`) | new hard memory limit; above it the kernel OOM-kills inside the container |
| `--memory-swap 2g` | the limit for memory **plus** swap: 1 GB RAM + 1 GB swap here; equal to `-m` means no swap |
| `--cpus 1.5` | at most one and a half CPUs of time, enforced by throttling |
| `--restart=no` | turn the restart policy off, so a stopped container stays down, even after a reboot (a crash loop, a rolled-back Traefik) |
| `c1` | one or more containers |

**What the output tells you:** the container name when it worked. Confirm with `docker inspect -f '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}' c1` and watch the effect with `docker stats --no-stream c1`.

**Why it is effective:** recreating the container wipes its writable layer and logs and costs downtime; update rewrites the cgroup limits while the process keeps running.

**Compared with removing and re-running:** that is the only way to change ports, env or volumes, and the way to make a change permanent; update is the fast, reversible fix.

**Trap:** it is **not permanent** for managed containers: the next `docker compose up`, Dokploy redeploy or Swarm task replacement brings back the limits from the definition. Raising `-m` above the current `--memory-swap` is refused, so set both together. A limit below what the process already uses can fail or trigger an immediate OOM kill. For Swarm services use `docker service update --limit-memory`.

**Next step:** after raising memory keep watching `docker stats`: a leak simply reaches the new limit later. Then put the value into the compose file (`mem_limit` or `deploy.resources.limits`) or the Dokploy app settings.

### docker stop / start / restart / rm — stop, start or delete a container, and what each keeps
Match: docker stop, docker start, docker restart, docker rm, docker kill
Instead of: systemctl restart docker
Safety: changes state: stop and kill end processes; rm deletes the container with its writable layer and logs

**In one line:** `stop` asks the main process to exit (stop signal, then SIGKILL after a timeout), `start` runs an existing container again with its original settings, `restart` does both, `kill` sends one signal, and `rm` deletes the container.

**Read the command:** `docker stop -t 30 CONTAINER`

| Part | Meaning |
|---|---|
| `stop` | send the stop signal (SIGTERM unless the image sets another), wait, then SIGKILL |
| `-t 30` | wait up to 30 s for a clean exit instead of the default 10 s |
| `start` | run a stopped container again: same config, same writable layer, logs kept |
| `restart` | stop + start; the container ID and log history stay |
| `rm -f` | kill if running, then delete the container, its writable layer and its logs (named volumes stay) |
| `kill --signal=HUP` | send just this signal: Prometheus, for example, reloads its config on SIGHUP |

**What the output tells you:** each prints the container name. The way it ended shows later in `docker ps -a`: `Exited (0)` or `Exited (143)` after a clean SIGTERM exit, `Exited (137)` when the timeout ran out and Docker had to SIGKILL.

**Why it is effective:** knowing what each verb keeps lets you act without destroying evidence: `restart` keeps the logs and the filesystem changes, `rm` throws both away.

**Compared with `systemctl restart docker`:** that restarts the daemon and with it every container on the host (unless `live-restore` is enabled); it is for daemon configuration changes, not for one sick container.

**Trap:** a stop that always takes exactly the timeout means the app ignores SIGTERM (often a shell script as PID 1 that does not pass signals on); it gets SIGKILLed and may lose in-flight work. Stopping a container that belongs to a Swarm service (Dokploy apps run as services) makes Swarm start a replacement: scale the service to 0 instead.

**Next step:** before any restart, save `docker logs --since 1h` and `docker inspect` output (and a thread dump for a JVM). `start` fails → `docker logs`, `docker events --since 5m`. New settings needed → recreate (`docker compose up -d`, or `rm` and `run`).

### docker images / docker history — which images are here, how big, built from what
Match: docker images, docker image, docker history
Instead of: docker system df
Safety: read-only · except docker image prune, which deletes images

**In one line:** `docker images` lists local images with tag, ID, age and size; `docker image inspect` shows one image's platform, config and digests; `docker history` lists its layers with the instruction and size of each.

**Read the command:** `docker history --format 'table {{.Size}}\t{{.CreatedBy}}' --no-trunc shop-web:dev`

| Part | Meaning |
|---|---|
| `history` | one row per layer or instruction, newest first |
| `--format 'table {{.Size}}\t{{.CreatedBy}}'` | only the size and the instruction that made the layer |
| `--no-trunc` | full instructions, including long `RUN` lines and any build-arg values in them |
| `images --digests` | adds the registry digest (`sha256:…`) that identifies the exact content |
| `image inspect --format '{{.Os}}/{{.Architecture}}'` | the platform the image was built for |
| `image inspect --format '{{index .RepoDigests 0}}'` | the pinned `name@sha256:…` reference |
| `image prune -a -f --filter until=336h` | delete every image no container uses that is older than 14 days, without asking |

**What the output tells you:**

```
SIZE      CREATED BY
0B        CMD ["node" "server.js"]
412MB     RUN /bin/sh -c npm install # buildkit
1.2MB     COPY . . # buildkit
```

The big `RUN` layer is what to fix (dev dependencies, caches not cleaned in the **same** step). `0B` rows are metadata only.

**Why it is effective:** a tag is only a name; the digest says which content you have, `history` explains the size and exposes what was baked in, and `inspect` proves the architecture before you deploy to an ARM or x86 host.

**Compared with `docker system df`:** system df gives totals and reclaimable space but cannot say which image, layer or instruction is responsible.

**Trap:** the SIZE column of `docker images` counts shared base layers in every image, so adding it up overstates disk use. The same tag (`nginx:1.27`, `latest`) can be different content on two hosts: compare digests. Deleting a file in a later layer does not shrink the image; the earlier layer still contains it, secrets included.

**Next step:** secret visible in `history` → rotate it, rebuild with build secrets. Wrong platform → rebuild with `docker buildx build --platform`. Old images filling the disk → `docker image prune -a --filter until=…` after checking what a rollback needs.

### docker pull / docker push — move images between this host and a registry
Match: docker pull, docker push, docker tag
Instead of: the orchestrator's ImagePullBackOff or "No such image" message
Safety: pull downloads layers; push publishes to the registry; tag only adds a name

**In one line:** `docker pull` fetches an image through the daemon, with the daemon's proxy, CA certificates and your login, so it reproduces exactly the error a deploy hits; `docker tag` adds a registry name to a local image and `docker push` uploads it.

**Read the command:** `docker pull harbor.example.com/shop/api:1.4.2`

| Part | Meaning |
|---|---|
| `harbor.example.com` | registry host: the first part counts as a registry only if it contains `.` or `:` or is `localhost` |
| `shop/api` | project and repository in that registry |
| `:1.4.2` | the tag; `@sha256:…` instead pins the exact content |
| `tag myapp:latest harbor.example.com/shop/myapp:3f9c2a1` | give a local image its full registry name (no copy is made) |
| `push harbor.example.com/shop/web:3f9c2a1` | upload the layers the registry does not have yet |
| `push shop/api:1.4.2` | no registry part, so this goes to **Docker Hub**, not to Harbor |

**What the output tells you:**

```
1.4.2: Pulling from shop/api
Digest: sha256:4f1c…
Status: Downloaded newer image for harbor.example.com/shop/api:1.4.2
```

Or the real failure: `unauthorized` (login, robot account), `manifest unknown` (no such tag), `no matching manifest for linux/arm64` (not built for this CPU), `x509: certificate signed by unknown authority` (private CA not trusted), `http: server gave HTTP response to HTTPS client` (plain-HTTP registry not listed as insecure), `toomanyrequests` (Docker Hub rate limit), or a timeout (no proxy for the daemon).

**Why it is effective:** orchestrators reduce all of these to ImagePullBackOff or "No such image"; one manual pull on the same host shows the registry's actual answer.

**Compared with the deploy's error:** it tells you *that* the pull failed and on which node; the manual pull tells you *why*.

**Trap:** the daemon, not your shell, downloads: `export https_proxy` in your terminal does not help (the daemon needs its own proxy settings, e.g. a systemd drop-in), and a private CA goes into `/etc/docker/certs.d/HOST/ca.crt`. Logins are per user: `sudo docker pull` uses root's. A tag can be overwritten; deploy by digest or use immutable tags.

**Next step:** `unauthorized` → `docker login`. `manifest unknown` or wrong platform → `docker buildx imagetools inspect IMAGE`. x509 → install the CA. Kubernetes node → repeat with `crictl pull`, which uses containerd's settings, not Docker's.

### docker login — store registry credentials for pull and push
Match: docker login
Instead of: docker login -p PASSWORD
Safety: changes state: writes credentials to the user's Docker config file

**In one line:** `docker login` checks a username and password or token against a registry and, if accepted, stores them so later pulls and pushes to that registry are authenticated.

**Read the command:** `docker login harbor.example.com -u 'robot$shop+ci' --password-stdin`

| Part | Meaning |
|---|---|
| `harbor.example.com` | the registry; without it Docker Hub is used |
| `-u 'robot$shop+ci'` | a Harbor robot account; single quotes stop the shell expanding `$shop` |
| `--password-stdin` | read the secret from stdin (e.g. a CI variable piped in), so it never appears in shell history or the process list |
| `--username AWS … 123456789012.dkr.ecr.ap-south-1.amazonaws.com` | Amazon ECR: fixed user `AWS`, password from `aws ecr get-login-password`, valid 12 hours |

**What the output tells you:** `Login Succeeded`, possibly with a warning that the credentials are stored unencrypted in `~/.docker/config.json` (base64 is not encryption). Failures: `unauthorized` or `incorrect username or password`; TLS errors and timeouts are network problems, not password problems.

**Why it is effective:** it isolates authentication: if login works and the pull or push still fails, the account lacks permission on that project, or the image or project does not exist.

**Compared with `docker login -p PASSWORD`:** works, but the secret lands in shell history and is visible in the process list while it runs; Docker itself warns against it.

**Trap:** a successful login proves the **credentials**, not the **permissions**: a pull-only robot account still gets `denied` on push. Logins are per user, so a login as `ops` does not help `sudo docker` or the CI runner. In CI, a `$` in a stored robot name or token may be expanded by the CI system itself unless variable expansion is turned off for it.

**Next step:** `denied` on push → the robot account's permissions on that Harbor project. Expired token (ECR after 12 hours, short-lived robot secrets) → log in again inside the job. Credentials on disk → configure a credential helper.

### docker build — build an image and see exactly which step fails
Match: docker build, docker buildx, docker builder
Instead of: docker build -t app . with cached, collapsed output
Safety: changes state: creates images and build cache; buildx --push publishes to a registry; builder prune deletes cache

**In one line:** `docker build` runs a Dockerfile's steps against a build context and produces an image; its flags decide whether the cache is trusted, whether base images are refreshed and how much of each step's output you see.

**Read the command:** `docker build --no-cache --pull -t shop-api:fresh .`

| Part | Meaning |
|---|---|
| `--no-cache` | run every step again instead of reusing cached layers |
| `--pull` | check the registry for a newer version of each `FROM` image |
| `-t shop-api:fresh` | name and tag of the result |
| `.` | the build context: this directory, minus `.dockerignore`, is sent to the builder |
| `--progress=plain` | every step's full output instead of the collapsed live view |
| `--target build` | stop after the stage named `build` of a multi-stage Dockerfile |
| `buildx build --platform linux/amd64,linux/arm64 … --push` | build for two CPU architectures and push straight to the registry |
| `builder prune -af --filter until=72h` | delete all build cache older than 72 hours, without asking |

**What the output tells you:** with `--progress=plain`, each step is numbered (`#7 [build 3/6] RUN npm ci`), followed by its output and `#7 DONE 41.2s`, or by `ERROR: process "/bin/sh -c npm ci" did not complete successfully: exit code: 1`. `CACHED` means the step did not run at all.

**Why it is effective:** a failed build is usually one step whose output the default view hides; `plain` shows all of it. `--no-cache --pull` rules out the classic "builds on CI, not here" causes: a stale cached `apt-get update` layer or an old local base image.

**Compared with plain `docker build -t app .`:** fine for routine builds, and the cache is what makes them fast; it just cannot show whether a step really ran, and on a terminal it collapses the output of steps that succeeded.

**Trap:** `--no-cache` alone still uses the **local** base image; add `--pull`. A context with `node_modules` or `.git` and no `.dockerignore` makes every build slow. Values passed as `ARG` or `ENV` stay readable in `docker history`: use build secrets for tokens.

**Next step:** a step fails → build the stage before it with `--target` and explore it with `docker run -it --entrypoint sh`. Image too big → `docker history`. `exec format error` at runtime → wrong platform: `docker buildx imagetools inspect IMAGE`, rebuild with `--platform`. Disk full of cache → `docker buildx du`, then `builder prune`.

### docker info / docker version — which engine is this, and how is it configured?
Match: docker info, docker version
Instead of: docker --version
Safety: read-only

**In one line:** `docker info` reports the daemon's configuration and state (storage and log drivers, cgroup setup, root directory, Swarm state, registries, proxy, warnings); `docker version` reports client **and** server versions and the API versions each side speaks.

**Read the command:** `docker info --format '{{.ServerVersion}} {{.Driver}} swarm={{.Swarm.LocalNodeState}}'`

| Part | Meaning |
|---|---|
| `--format` | a Go template over the info data |
| `{{.ServerVersion}}` | the daemon's engine version |
| `{{.Driver}}` | storage driver, normally `overlay2` |
| `{{.Swarm.LocalNodeState}}` | `inactive`, `active`, `pending`, `error` or `locked` |
| `{{.LoggingDriver}}` | default log driver for new containers (`json-file`, `local`, `journald` …) |
| `docker info >/dev/null 2>&1` | only the exit status: 0 means the daemon answered |
| `docker version --format 'server {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'` | engine version, the newest API version it speaks and the oldest it still accepts |

**What the output tells you:**

```
28.5.1 overlay2 swarm=active
```

Plain `docker info` also lists `Docker Root Dir`, `Cgroup Driver` (`systemd` or `cgroupfs`), `Registry Mirrors`, `Insecure Registries` and any proxy the **daemon** uses, and ends with WARNING lines worth reading.

**Why it is effective:** most "works on one host, fails on the other" puzzles are engine settings: another storage or log driver, no daemon proxy, a registry missing from the insecure list, Swarm active on one host only. One command shows them as the daemon has them, not as a file claims.

**Compared with `docker --version`:** prints only the **client** version and works even when the daemon is down. `docker version` shows both sides, and its Server part (or the error in its place) proves whether the CLI reaches the daemon.

**Trap:** tools that call the Docker API themselves (Traefik, Portainer, CI runners) can fail after an engine upgrade with "client version … is too old": compare the API version they use with `MinAPIVersion`. `.Swarm.Cluster` fields exist only on managers. Another user, context or rootless daemon gives a different answer, so run it the way the failing command runs.

**Next step:** daemon unreachable → `systemctl status docker`, `journalctl -u docker -b`. Settings not as expected → `dockerd --validate --config-file /etc/docker/daemon.json`, then restart the daemon. Swarm `inactive` on a Dokploy host → `docker swarm`.

### docker compose — work with all containers of one project
Match: docker compose
Instead of: docker ps, docker logs per container
Safety: ps and logs are read-only · down, stop, restart, rm and exec can change state

**In one line:** `docker compose` acts on a **project** (the services in a compose file, named after its directory unless set otherwise): it lists, logs, enters, stops or removes the project's containers by **service** name.

**Read the command:** `docker compose ps ; docker compose logs -f svc`

| Part | Meaning |
|---|---|
| `compose ps` | this project's containers: NAME, SERVICE, STATUS, PORTS (`-a` adds stopped ones) |
| `compose logs -f svc` | follow the logs of every container of service `svc`, each line prefixed with the container name |
| `compose exec svc sh` | a shell in the service's container, addressed by service |
| `compose down` | stop and remove the containers and the project's networks; volumes stay unless `-v` |
| `compose restart` | restart the containers **without** applying changes made to the file |
| `-f FILE`, `-p NAME` | another compose file, another project name |

**What the output tells you:**

```
NAME         IMAGE         SERVICE   STATUS                         PORTS
shop-db-1    postgres:16   db        Up 2 hours (healthy)           5432/tcp
shop-web-1   shop-web:3    web       Restarting (1) 5 seconds ago
```

Names are `<project>-<service>-<number>`: project `shop`, services `db` and `web`.

**Why it is effective:** it works from the file that defines the stack: service names instead of container names, only this project's containers instead of everything on the host, and the logs of a scaled service merged into one stream.

**Compared with `docker ps` / `docker logs`:** they need exact container names and show every project on the host mixed together; fine for a one-off check.

**Trap:** compose finds the project from the current directory (or `-f` / `-p`): from another directory `ps` shows nothing, or acts on a different project. `restart` does not apply file or `.env` changes; `up -d` does. `down -v` also deletes volumes, databases included.

**Next step:** service restarting → `docker compose logs --tail 100 svc`. File changed → `docker compose config`, then `docker compose up -d`. Details → `docker inspect shop-web-1`.

### docker compose up — make the running containers match the file
Match: docker compose up
Instead of: docker compose restart, docker restart
Safety: changes state: creates, recreates and starts containers; a recreated container loses its old logs

**In one line:** `docker compose up -d` compares each service's container with the compose file and image, recreates those whose configuration changed, starts what is missing and leaves the rest running.

**Read the command:** `docker compose up -d --force-recreate svc`

| Part | Meaning |
|---|---|
| `up` | create or start the services so they match the file |
| `-d` | detached: return once the containers are started instead of streaming their logs |
| `--force-recreate` | recreate even if nothing changed: a fresh container with the same volumes |
| `svc` | only this service, plus the services it `depends_on` (unless `--no-deps`) |
| `--build` | build images that have a `build:` section first |
| `--remove-orphans` | remove containers of services that are no longer in the file |

**What the output tells you:** one line per container saying whether it was created, recreated, started or left running. A warning such as `The "DB_PASSWORD" variable is not set. Defaulting to a blank string.` means a `${…}` value came out empty, a common cause of a broken start.

**Why it is effective:** it applies the file declaratively, the same command the first time and every time after, and only touches what changed. `--force-recreate` gives a guaranteed fresh container without hunting for its name.

**Compared with `docker compose restart` / `docker restart`:** they stop and start the **existing** containers, so a changed tag, variable or port in the file is silently ignored; enough only when the definition did not change.

**Trap:** `up` does not fetch a newer image for a tag you already have: run `docker compose pull` first (or `up --pull always`). `depends_on` waits for the dependency to **start**, not to be ready, unless it uses `condition: service_healthy`. A recreated container starts with empty logs; save them first when debugging.

**Next step:** a container keeps restarting → `docker compose logs -f svc`. Unexpected values → `docker compose config`. Old version still running → `docker compose pull`, `up -d`, then compare `docker inspect --format '{{.Image}}'`.

### docker compose config — the compose file exactly as Compose will run it
Match: docker compose config
Instead of: cat compose.yaml
Safety: read-only · prints interpolated values, including secrets from .env

**In one line:** `docker compose config` merges all compose files and overrides, substitutes `${VARIABLES}` from the shell and the `.env` file, validates the result and prints the final model that `up` would use.

**Read the command:** `docker compose config --quiet`

| Part | Meaning |
|---|---|
| `config` | print the effective configuration |
| `--quiet` (`-q`) | print nothing, only validate: exit code 0 means the files parse and are valid |
| `--services` | only the service names |
| `-f a.yml -f b.yml` | the files to merge, later ones overriding earlier ones |

**What the output tells you:** the full YAML with defaults filled in, relative paths made absolute and every variable replaced by its value. An empty `${DB_HOST}`, an unexpected image tag or a volume pointing at the wrong path is visible at once. With `--quiet`, success is silent and any problem is printed as an error.

**Why it is effective:** the file you read is not what runs: `compose.override.yaml` (or `docker-compose.override.yml`) is merged automatically, `.env` replaces variables and YAML anchors expand. config shows the result in one place, and `--quiet` makes it a cheap lint step before `up` or in CI.

**Compared with `cat compose.yaml`:** shows what was written, enough for one file without variables; it cannot show what `${TAG}` resolves to or what an override changed.

**Trap:** the output contains real secret values: keep it out of tickets and CI logs. The `.env` file (for `${…}` substitution) and `env_file:` (variables passed into the container) are different mechanisms. Variables set in your shell override `.env`, so CI and your terminal can render different results.

**Next step:** wrong value → find its source (shell, `.env`, override file). Valid config but containers misbehave → `docker compose up -d`, then `docker compose logs`. Swarm stack → `docker stack config -c compose.yml`.

### docker-compose (v1) — is the old standalone Compose still here, and which one runs?
Match: docker-compose
Instead of: —
Safety: version is read-only · up, down and restart change state, as with docker compose

**In one line:** `docker-compose`, with a hyphen, is the older standalone Compose binary; `docker-compose version` tells you whether a host still has it, and which generation it is.

**Read the command:** `docker-compose version 2>/dev/null`

| Part | Meaning |
|---|---|
| `docker-compose` | the standalone binary, separate from the `docker compose` plugin |
| `version` | print its version (v1 also prints its Python and library versions) |
| `2>/dev/null` | hide "command not found" in scripts: empty output means it is not installed |

**What the output tells you:** `docker-compose version 1.29.2, build …` is Compose v1, written in Python and no longer maintained. `Docker Compose version v2.…` is a v2 binary installed under the old name. Nothing at all: only the `docker compose` plugin, if any.

**Why it is effective:** v1 and v2 name containers differently (`shop_web_1` against `shop-web-1`), so scripts, cron jobs and monitoring rules written for one break on the other; knowing which one deployed a project explains "No such container" after a migration.

**Compared with `docker compose version`:** that checks the v2 plugin. A host can have both, and old scripts may still call the hyphenated one.

**Trap:** the hyphen matters in automation: a CI job or systemd unit that calls `docker-compose` may run a different, older Compose than the one you test with by hand, and v1 can reject or misread newer compose-file features.

**Next step:** v1 found → move the project to `docker compose` (usually the same file), fix container names in scripts and monitoring, then remove the old binary.

### docker swarm — create or join a Swarm, and choose its address pool
Match: docker swarm
Instead of: —
Safety: changes state: init, join and leave reconfigure the engine; leave --force on the last manager discards all services, overlay networks and secrets

**In one line:** `docker swarm init` turns this engine into a Swarm manager (Dokploy needs one), `join-token` prints the command other nodes use to join, and `leave` takes a node out.

**Read the command:** `docker swarm init --advertise-addr 192.0.2.10 --default-addr-pool 10.220.0.0/16 --default-addr-pool-mask-length 24`

| Part | Meaning |
|---|---|
| `init` | create a new Swarm with this node as its first manager |
| `--advertise-addr 192.0.2.10` | the address other nodes use to reach this manager; needed when the host has several IPs |
| `--default-addr-pool 10.220.0.0/16` | the range overlay networks take their subnets from (default `10.0.0.0/8`) |
| `--default-addr-pool-mask-length 24` | each overlay network gets a /24 from that range |
| `join-token worker` (or `manager`) | print the full `docker swarm join --token … 192.0.2.10:2377` command |
| `leave --force` | leave even as a manager, losing quorum or the whole Swarm |

**What the output tells you:** init prints the node ID and a ready-made `docker swarm join` command. Afterwards `docker info --format '{{.Swarm.LocalNodeState}}'` says `active`. Nodes talk on 2377/tcp (management), 7946/tcp and udp (node gossip) and 4789/udp (overlay traffic); a firewall in between breaks joins or overlay networking.

**Why it is effective:** the address pool is chosen once, at init. A range that overlaps nothing on your LAN, VPN or cloud avoids the classic "containers cannot reach the 10.x office network" problem, which is very hard to undo later.

**Trap:** the default `10.0.0.0/8` overlaps many company networks, and changing the pool later means leaving and recreating the Swarm: on a single-node Dokploy host `leave --force` takes every service with it. The Dokploy installer itself runs `docker swarm leave --force` before `init`, so installing it on a node of an existing Swarm silently pulls that node out. The join token is a credential; rotate it with `docker swarm join-token --rotate worker` if it leaks.

**Next step:** `inactive` on a Dokploy host → `init` with an explicit `--advertise-addr`. Node will not join → `nc -zv MANAGER 2377`. Overlay subnet clash → `docker network inspect NETWORK --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'`, then plan a re-init in a maintenance window.

### docker node — Swarm nodes: are they up, and may tasks run on them?
Match: docker node
Instead of: docker info
Safety: ls and inspect are read-only · update (drain, labels) changes where tasks run

**In one line:** `docker node ls`, run on a manager, lists every Swarm node with its status, availability and manager role; `docker node update` drains a node for maintenance or labels it for placement rules.

**Read the command:** `docker node update --availability drain web03`

| Part | Meaning |
|---|---|
| `node update` | change a node's settings in the Swarm |
| `--availability drain` | schedule nothing here and move the existing tasks to other nodes |
| `--availability active` | allow scheduling again; tasks do not move back by themselves |
| `--label-add disk=ssd` | a label that placement constraints can use (`node.labels.disk==ssd`) |
| `web03` | node hostname or ID |
| `node inspect self --format '{{.Status.Addr}} {{.Spec.Availability}}'` | this node's address and availability |

**What the output tells you:** after the drain, `docker node ls` shows:

```
ID                HOSTNAME   STATUS   AVAILABILITY   MANAGER STATUS   ENGINE VERSION
p8d1k2m4x7q9 *    web01      Ready    Active         Leader           28.5.1
7fj3m9c2v5b8      web02      Ready    Active         Reachable        28.5.1
x2b6q1n8z4w3      web03      Ready    Drain                           28.5.1
```

`*` marks the node you are on. STATUS `Down` means the managers lost contact; AVAILABILITY `Drain` or `Pause` means deliberately not scheduling; MANAGER STATUS is `Leader`, `Reachable` or `Unreachable`, and blank for workers.

**Why it is effective:** a service stuck at `0/1` with "no suitable node" is very often a node that is down, drained or missing a label, and this table shows all three at once.

**Compared with `docker info`:** shows only the local node's Swarm state; node ls is the cluster as the managers see it.

**Trap:** it works only on a manager ("This node is not a swarm manager"). Draining the only node, as on a single-server Dokploy host, stops every service. After `active`, the node stays empty until tasks are rescheduled (`docker service update --force SERVICE`). Losing most managers (2 of 3) blocks every change to the cluster.

**Next step:** node `Down` → check the host, then ports 2377, 7946 and 4789 between the nodes. Service not scheduling → `docker service ps --no-trunc SERVICE` for the exact constraint error.

### docker service — Swarm services: desired versus running, and why tasks fail
Match: docker service
Instead of: docker ps, docker logs
Safety: ls, ps, logs and inspect are read-only · update, scale and rm change the running service

**In one line:** `docker service ls` compares running with desired replicas for every Swarm service; `docker service ps` lists a service's tasks with state and error, including tasks that never got a container; `docker service logs` merges the logs of all its tasks.

**Read the command:** `docker service ps --no-trunc --format '{{.Name}} {{.CurrentState}} {{.Error}}' client-app-x7k2qd`

| Part | Meaning |
|---|---|
| `service ps` | the task history of one service (Dokploy names services like `client-app-x7k2qd`) |
| `--no-trunc` | the full error text instead of a cut-off one |
| `{{.Name}} {{.CurrentState}} {{.Error}}` | task (`service.slot`), its state with age, its error |
| `service ls --format '{{.Name}} {{.Replicas}} {{.Image}}'` | running/desired replicas and image per service |
| `service logs --tail 20 SERVICE` | the last lines of every task, on every node |
| `service scale SERVICE=0` | stop all tasks but keep the service definition |
| `service update --publish-rm "published=3000,target=3000,mode=host" dokploy` | remove a published port, e.g. Dokploy's UI port 3000 once its domain works (the task is replaced) |

**What the output tells you:**

```
client-app-x7k2qd.1 Running 2 hours ago
client-app-x7k2qd.1 Shutdown 2 hours ago
client-app-x7k2qd.1 Rejected 3 hours ago No such image: harbor.example.com/shop/web:1.4.2
client-app-x7k2qd.1 Failed 3 hours ago task: non-zero exit (1)
```

The top line is the current task. `Rejected` means it failed **before** a container existed (image, secret, network, placement), so `docker ps` and `docker logs` have nothing; `Failed … non-zero exit` means the container ran and crashed, and `service logs` holds the reason.

**Why it is effective:** in Swarm, and so in Dokploy, a broken deploy often leaves no container behind at all; the task list keeps the scheduler's error, the only place it is written down.

**Compared with `docker ps` / `docker logs`:** they see only containers on the node you are logged into: fine when the task runs there, blind to tasks that were rejected or placed on another node.

**Trap:** `1/1` replicas can hide a crash loop; the history shows tasks dying every few minutes, but it keeps only the last few tasks per slot. `scale` and `update` act immediately, and the next Dokploy deploy may overwrite them.

**Next step:** `No such image` → `docker pull` on that node; for stacks, deploy with `--with-registry-auth`. `no suitable node` → `docker node ls`, constraints and labels. `non-zero exit` → `docker service logs --tail 100 SERVICE`.

### docker stack — deploy a compose file as Swarm services, then watch its tasks
Match: docker stack
Instead of: docker compose up
Safety: deploy and rm create, update or remove services; ls, services, ps and config are read-only

**In one line:** `docker stack deploy` turns a compose file into Swarm services named `<stack>_<service>` and updates them on every re-run; `stack services` and `stack ps` show the state of the whole stack at once.

**Read the command:** `docker stack deploy --with-registry-auth -c compose.yml shop`

| Part | Meaning |
|---|---|
| `stack deploy` | create or update the stack's services, networks, secrets and configs |
| `--with-registry-auth` | send this client's registry login to the nodes, so workers can pull private images |
| `-c compose.yml` | the compose file to deploy |
| `shop` | the stack name: services become `shop_web`, `shop_db` … |
| `stack ps shop --no-trunc --format 'table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}'` | every task of the stack: node, state and full error |
| `stack services shop` | running/desired replicas per service |
| `stack config -c compose.yml` | the final file after merging and variable substitution |

**What the output tells you:** deploy prints `Creating service shop_web` or `Updating service shop_web` per service, and `Ignoring unsupported options: build` for compose keys Swarm does not use. `stack ps` then shows each task's node, state (`Running`, `Rejected`, `Failed`) and error.

**Why it is effective:** the whole application is deployed and inspected as one unit, and `stack ps` across all its services shows the one failing task and the node it failed on.

**Compared with `docker compose up`:** compose runs containers on this one host and can build images; it does not schedule across nodes or roll updates. Use compose for a single host, stack for Swarm.

**Trap:** stack deploy does not build images and does not read a `.env` file the way `docker compose` does: variables must be in the shell environment (check with `stack config`). Without `--with-registry-auth`, the manager pulls fine while workers fail with "No such image". Services removed from the file keep running unless you deploy with `--prune`.

**Next step:** a task `Rejected` or `Failed` → `docker service ps --no-trunc shop_web`, `docker service logs shop_web`. Wrong value → `docker stack config -c compose.yml`. Remove the stack → `docker stack rm shop` (volumes are kept).

### docker — every other subcommand: evidence, contexts, secrets
Match: docker
Instead of: —
Safety: depends on the subcommand · cp out of a container, diff, export and the ls/inspect forms are read-only; create, rm, prune and secret create change state

**In one line:** the subcommands without their own card are mostly evidence collection (`cp`, `diff`, `export`), choosing which engine the CLI talks to (`context`), Swarm secrets and housekeeping; all follow `docker [--context NAME] COMMAND [options] [arguments]`.

**Read the command:** `docker cp c1:/app/config.yml /tmp/`

| Part | Meaning |
|---|---|
| `cp c1:/app/config.yml /tmp/` | copy a file out of a container (`CONTAINER:PATH` → host directory); works on stopped containers too |
| `diff c1` | files changed against the image: `A` added, `C` changed, `D` deleted |
| `export c1 -o c1.fs.tar` / `save IMAGE -o x.tar` | a container's whole filesystem as one tar (volumes not included) / an image with all its layers |
| `create alpine:3.20` | a container that is never started, e.g. to `cp` files out of an image |
| `--context dokploy-1 ps` / `context use default` | run against another engine (one made with `--docker host=ssh://ops@10.10.0.10`) / switch back |
| `secret create db_password_v2 -` | a Swarm secret whose value is read from stdin (`-`); also `secret ls`, `secret rm` |
| `manifest inspect image:tag` | which platforms an image exists for in the registry, without pulling it |
| `container prune -f --filter until=168h` | delete stopped containers older than 7 days, without asking |

**What the output tells you:** `docker diff` lines such as `C /etc`, `A /etc/nginx/conf.d/extra.conf` and `A /tmp/x.sh` show what changed at runtime: hand-made hot fixes that the next redeploy will lose, or files an attacker dropped.

**Why it is effective:** these commands preserve evidence before a container is restarted or removed, and `--context` runs the same commands against a remote Dokploy host over SSH without logging in there.

**Trap:** `diff` and `export` ignore volumes and bind mounts, where most data lives. A context is sticky: after `docker context use dokploy-1` every later command targets that host until you switch back (`docker context ls` marks the current one). Secrets cannot be edited: rotating means a new name (`db_password_v2`) and a service update. `docker debug` is a Docker Desktop feature and usually missing on servers; use `nsenter` there.

**Next step:** suspicious `diff` → `docker export` and `docker inspect` into files **before** `docker rm`. Commands hitting the wrong host → `docker context ls`. Platform question → `docker buildx imagetools inspect`.

### dockerd / containerd — check the daemon configuration before you restart it
Match: dockerd, containerd
Instead of: systemctl restart docker, then hope
Safety: --validate and config dump/default are read-only · a foreground dockerd --debug needs root and the service stopped

**In one line:** `dockerd --validate` checks `daemon.json` and exits without starting anything; `containerd config dump` prints the configuration containerd really uses, which on Kubernetes nodes decides the cgroup driver, whether the CRI plugin runs and which sandbox image is used.

**Read the command:** `dockerd --validate --config-file /etc/docker/daemon.json`

| Part | Meaning |
|---|---|
| `dockerd` | the Docker Engine daemon (normally started by systemd as `docker.service`) |
| `--validate` | check the configuration and exit: `configuration OK` or the error |
| `--config-file /etc/docker/daemon.json` | which file to check (this is the default path) |
| `dockerd --debug` | run the daemon in the foreground with debug logging, to watch why it fails to start |
| `containerd config dump` | the effective config: the file merged with built-in defaults |
| `containerd config default` | the defaults of **this** containerd version, to start a config file from |
| `containerd --version` | the installed containerd version |

**What the output tells you:** for dockerd, `configuration OK` or the exact problem: invalid JSON (a trailing comma), an unknown key, or "the following directives are specified both as a flag and in the configuration file: hosts", which means `-H` in the systemd unit plus `"hosts"` in daemon.json. For containerd, check `SystemdCgroup = true` (it must match the kubelet's cgroup driver), `disabled_plugins` (Docker's packaged config disables `cri`, which the kubelet needs) and the sandbox (pause) image.

**Why it is effective:** a daemon restart with a broken config takes **every** container on the host down until it is fixed; validating first turns that outage into an error message. `config dump` shows what is in effect, not what you believe the file says.

**Compared with `systemctl restart docker`, then `journalctl -u docker`:** you find the same error, but only after the outage has started.

**Trap:** `--validate` checks syntax and options, not the system: a `data-root` on a disk that is not mounted passes, and the daemon then starts with an empty store. A foreground `dockerd --debug` needs `docker.service` and `docker.socket` stopped first, or it clashes with them. containerd's section names differ between major versions, so copy settings from `config default` of the installed version, not from an old guide.

**Next step:** config OK but the daemon still fails → `journalctl -u docker -b` or `journalctl -u containerd -b`. Pods failing on a new node → compare `SystemdCgroup` with the kubelet config, restart containerd, then `crictl info`.

### crictl — pods and containers on a Kubernetes node, through the kubelet's own API
Match: crictl
Instead of: docker ps, kubectl when the API server is down
Safety: ps, logs, inspect, pods, images and info are read-only · pull downloads; stop and rmi --prune change state; needs root for the runtime socket

**In one line:** `crictl` talks to the node's container runtime (containerd or CRI-O) through the CRI socket, so it shows this node's pods and containers, exited ones and their logs included, even when `kubectl` cannot reach the API server.

**Read the command:** `crictl ps -a --name kube-apiserver`

| Part | Meaning |
|---|---|
| `ps` | containers on this node, running ones by default |
| `-a` | include exited containers: the earlier, crashed attempts |
| `--name kube-apiserver` | filter on the container name (a regular expression) |
| `-q` | IDs only, to feed into `logs` or `inspect` |
| `logs --tail 20 ID` | the last lines of that container's log, also after it exited |
| `inspect ID` | JSON with state, exit code, reason (e.g. `OOMKilled`), mounts and PID |
| `pull --creds 'robot$shop+k8s-pull:TOKEN' IMAGE` | test a pull with the runtime's own registry settings |
| `--runtime-endpoint unix:///run/containerd/containerd.sock` | which runtime socket to use (normally set in `/etc/crictl.yaml`) |

**What the output tells you:**

```
CONTAINER      IMAGE          CREATED          STATE     NAME             ATTEMPT   POD ID         POD
9b2e4f1a7c3d0  6f1d3c0e2b9a4  20 seconds ago   Running   kube-apiserver   7         c3a1e9d2b4f60  kube-apiserver-cp1
1f7a2c9e8d4b3  6f1d3c0e2b9a4  2 minutes ago    Exited    kube-apiserver   6         c3a1e9d2b4f60  kube-apiserver-cp1
```

`ATTEMPT` counts restarts: 7 is a crash loop. The **exited** attempt holds the error: run `crictl logs` on its ID.

**Why it is effective:** when the control plane itself is down (a bad API server flag, an expired certificate, etcd unhealthy), `kubectl` only says "connection refused"; crictl reads the failing static-pod containers straight from the runtime.

**Compared with `docker ps` / `kubectl`:** current Kubernetes nodes run pods on containerd without Docker, so `docker ps` shows nothing or unrelated containers; `kubectl` needs a working API server.

**Trap:** without `/etc/crictl.yaml`, crictl tries several default sockets and prints warnings or connection errors: set the endpoint. The newest container is not always the useful one: the running attempt may have just started, the exited one holds the crash. It only sees this node.

**Next step:** API server exiting → `crictl logs` of the exited attempt, then fix `/etc/kubernetes/manifests/kube-apiserver.yaml`. ImagePullBackOff → `crictl pull` the same image on the same node. Runtime errors → `crictl info`, `journalctl -u containerd`.

### ctr / nerdctl — containerd's own view, below Docker and Kubernetes
Match: ctr, nerdctl
Instead of: docker ps on a node without Docker
Safety: read-only as used here · ctr can also pull and delete behind the kubelet's and Docker's back

**In one line:** `ctr` is containerd's low-level debug client: it lists the containers, images and tasks containerd holds in each **namespace**, the layer underneath both Docker and Kubernetes.

**Read the command:** `ctr -n k8s.io containers ls`

| Part | Meaning |
|---|---|
| `-n k8s.io` | the containerd namespace Kubernetes (CRI) uses; Docker uses `moby`; without `-n` ctr looks in `default` |
| `containers ls` (or `list`) | container records: ID, image, runtime |
| `images ls -q` | image references only |
| `tasks ls` | the processes actually **running**; a container record can exist without one |
| `namespaces ls` | which namespaces exist on this host |
| `nerdctl -n k8s.io ps` | nerdctl, if installed, is a Docker-style CLI for the same containerd |

**What the output tells you:** one record per container, including the `pause` containers that hold each pod's namespaces; the IDs are the full forms of the ones `crictl ps` shows. An empty list usually means the wrong namespace, not "no containers".

**Why it is effective:** when the kubelet, the API server or dockerd are broken, containerd itself may be fine; ctr shows what the runtime holds, independent of all of them.

**Compared with `docker ps` and `crictl`:** `docker ps` sees only Docker's own containers, or nothing where Docker is not installed. crictl speaks the Kubernetes CRI and shows pods, names and restart attempts: prefer it on Kubernetes nodes. ctr is lower level, knows nothing about pods and **ignores the CRI registry settings**, so a `ctr` pull test proves little about the kubelet's pulls.

**Trap:** forgetting `-n k8s.io` gives an empty list that looks like "containerd lost everything". Changing things with ctr behind the kubelet's back confuses it; leave changes to `kubectl` and `crictl`.

**Next step:** pod names, logs, restart counts → `crictl ps -a`, `crictl logs`. containerd unhealthy → `journalctl -u containerd -b`, `containerd config dump`.

### podman — the daemonless, often rootless, Docker-style CLI
Match: podman
Instead of: docker ps on a host that runs Podman
Safety: read-only as used here (ps, port, inspect, logs)

**In one line:** `podman` runs the same OCI containers as Docker with nearly the same commands, but without a central daemon, and containers started by a normal user are **rootless**: they belong to, and are visible only to, that user.

**Read the command:** `podman ps --format "table {{.Names}} {{.Ports}} {{.Status}}"`

| Part | Meaning |
|---|---|
| `ps` | running containers **of the current user** (`-a` adds stopped ones) |
| `--format "table …"` | a Go template as in Docker: name, published ports, status |
| `port CONTAINER` | the published port mappings |
| `inspect -f '{{.State.Pid}}' CONTAINER` | host PID of the main process, for `nsenter` |
| `logs --tail 100 -f CONTAINER` | the last 100 log lines, then follow |

**What the output tells you:** the columns you know from Docker. In a port inventory, a rootless container's published port is held by a Podman helper process (such as `rootlessport` or `pasta`) instead of `docker-proxy`, which is how you recognise Podman in `ss -tlnp`.

**Why it is effective:** some hosts, especially in the RHEL family, run containers with Podman (often as systemd services) instead of Docker; there `docker ps` is empty or missing, and only podman shows them.

**Compared with `docker ps`:** same idea and output, but Docker asks one root daemon for every container on the host, while podman lists only the containers in the storage of the user running it.

**Trap:** `podman ps` as `ops` and `sudo podman ps` show **different** containers, because each user has separate storage: check every user that runs containers. Rootless containers cannot publish ports below 1024 by default.

**Next step:** unknown process on a port → find its owner with `ss -tlnp`, then run `podman ps` as that user. Need to look inside the network namespace → `nsenter -t PID -n`.

### nsenter / unshare — the host's tools inside a container's namespaces
Match: nsenter, unshare
Instead of: docker exec c1 ss in an image without tools
Safety: needs root · nsenter runs host programs inside the container's namespaces; unshare starts a shell in new namespaces

**In one line:** `nsenter` joins the namespaces of a running process, usually a container's main process, so the **host's** `ss`, `ip` and `tcpdump` see the container's network; `unshare` does the opposite and creates new namespaces, which is how a container is built by hand.

**Read the command:** `nsenter -t "$PID" -n tcpdump -ni any -c 20 port 53`

| Part | Meaning |
|---|---|
| `-t "$PID"` | the target process: the container's host PID from `docker inspect -f '{{.State.Pid}}' c1` |
| `-n` | enter its **network** namespace only: interfaces, routes, sockets |
| `tcpdump -ni any -c 20 port 53` | the host's tcpdump: no name lookups, all interfaces, 20 packets, DNS only |
| `-m -p` | also its mount and PID namespaces, so `ps aux` shows the container's processes |
| `-u` | its UTS namespace: `hostname` prints the container's hostname |
| `unshare --pid --fork --mount-proc --uts --net --ipc bash` | a shell in new PID, mount, UTS, network and IPC namespaces, with its own `/proc` |

**What the output tells you:** exactly what the tool would print inside the container: `nsenter -t $PID -n ss -tlnp` shows whether the app listens on `0.0.0.0:8000` or only on `127.0.0.1:8000`; the tcpdump above shows whether DNS queries leave the container and whether answers come back.

**Why it is effective:** distroless and slim images have no shell, `ss` or `tcpdump`, so `docker exec` fails; nsenter brings the host's binaries and still sees the container's network. It works the same for Kubernetes pods (PID from `crictl inspect`) and Podman.

**Compared with `docker exec`:** exec runs programs from the **image**, fine when the image has them. A `nicolaka/netshoot` container with `--network container:c1` gives the same network view plus a full toolbox, but needs an image pull.

**Trap:** with `-n` alone you are still on the **host's** filesystem: `cat /etc/resolv.conf` shows the host's DNS settings, not the container's. With `-m` it flips: programs come from the container, so `ps` must exist in the image. The PID changes whenever the container restarts.

**Next step:** app bound to `127.0.0.1` → change its listen address to `0.0.0.0`. DNS queries without answers → the host's resolver and firewall. To understand isolation itself → the `unshare` lab in the Docker learning module.

### dockerd-rootless-setuptool.sh — set up a per-user, rootless Docker daemon
Match: dockerd-rootless-setuptool.sh
Instead of: adding users to the docker group
Safety: changes state: installs and starts a per-user dockerd as a systemd user service

**In one line:** `dockerd-rootless-setuptool.sh install`, run as a **normal user**, sets up a second Docker daemon that runs entirely as that user, so a container breakout lands in an unprivileged account instead of root.

**Read the command:** `dockerd-rootless-setuptool.sh install`

| Part | Meaning |
|---|---|
| `dockerd-rootless-setuptool.sh` | helper from Docker's rootless extras package |
| `install` | check prerequisites, then create and start a systemd **user** service for the daemon |
| no `sudo` | run it as the target user; it refuses to set this up as root |

**What the output tells you:** missing prerequisites first, typically the `uidmap` tools or no subordinate ID range for the user in `/etc/subuid` and `/etc/subgid`. On success it prints the socket to use, `unix:///run/user/UID/docker.sock`, for `DOCKER_HOST` or a CLI context.

**Why it is effective:** membership of the `docker` group controls the root daemon, which amounts to root on the host; a rootless daemon removes that risk for developers, build users and CI runners.

**Compared with the `docker` group:** simpler and fully featured, and acceptable only for users you would trust with root.

**Trap:** there are now **two** daemons: the same `docker ps` shows different containers depending on `DOCKER_HOST` or the current context, so containers seem to vanish. Rootless containers cannot bind ports below 1024 by default, and the user service stops at logout unless lingering is enabled (`loginctl enable-linger USER`).

**Next step:** `docker context ls` and `docker info` show which daemon you are talking to. Setup fails → check `/etc/subuid`, `/etc/subgid` and the `uidmap` package.
