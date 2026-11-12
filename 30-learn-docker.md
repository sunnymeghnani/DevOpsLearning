# 30 — Learn: Docker Zero to Hero

This is the Docker learning module of the handbook. It takes you from "what is a container" to
running containers as a platform: images built in GitLab CI, stored in Harbor behind a private CA,
deployed by Dokploy on Docker Swarm behind Traefik, on on-prem Ubuntu servers that still run
Apache. Every topic follows the same loop: understand the concept, look at it on a real system,
build it on a test VM, break it on purpose, fix it, and know which playbook to open when it breaks
at work. The command reference lives in [Docker reference](14-docker-containers.md), the incident
playbook in [Containers & Kubernetes playbook](26-playbook-containers-k8s.md), and the real
incident that started this handbook in [Apache holds 443, deploy Dokploy](21-case-apache-443-dokploy.md).
This module is the *why* behind all three.

**Who this module is for.** It covers five career stages (the full map is in the
[Career ladder](40-career-ladder.md)). Each topic carries a tag such as **[L2 · Mid]**: the Ops
Ladder level, then the stage at which you should be able to do it alone.

| Stage | Level | Use this module for | Start at |
|---|---|---|---|
| Fresher (0–1 yr) | L0 | what a container is; run, stop and read your first containers safely | sections 1 and 5 |
| Junior (1–2 yrs) | L1 | daily operation: images, Dockerfiles, logs, volumes, Compose, restart policies | sections 3–6, 8, 9 |
| Mid-level (2–4 yrs) | L2 | troubleshooting: networking, DNS, firewall, limits and OOM, the debugging toolkit | sections 7, 10, 15 |
| Senior (4–7 yrs) | L3 | platform: internals, daemon.json, Harbor, security, Swarm under Dokploy, the L3 exit test | sections 2, 11–14, 16 |
| Senior/Lead (5+ yrs) | L4 | operating it at scale: monitoring, game days, postmortems | [Observability](32-learn-performance-observability.md), [SRE practice](33-learn-cicd-iac-sre.md) |

> All sample outputs are illustrative: Ubuntu 22.04/24.04 hosts, Docker Engine 27–29, cgroup v2.
> IPs come from documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) or private
> ranges; lab VMs use 192.168.56.0/24. UPPERCASE words in commands are placeholders: CONTAINER,
> IMAGE, PORT, HOST, VOLUME, SERVICE, PID, NETWORK.

---

## 0. How to use this module

### Learning path

The areas below are grouped by subject so the module also works as a reference. To learn from
zero, follow this order instead. Level tags come from your Ops Ladder (L0 Foundations,
L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE). The Ops Ladder puts "container internals,
images, Docker networking, Traefik and Dokploy" at L3, but you need the L1 operator skills first,
so the early steps are L1. The stage after the level says when you should own the skill.

| # | Topic | Level · stage | Section | Why it is in this position |
|---|---|---|---|---|
| P | Processes, users, systemd, journald, ports | L0–L1 · Fresher/Junior | [Linux](27-learn-linux.md) | dockerd is a systemd service; a container is a process |
| 1 | Why containers, container vs VM, architecture | L0–L1 · Fresher/Junior | 1 | the mental model everything else hangs on |
| 2 | Container lifecycle: run, exec, logs, inspect | L1 · Junior | 5 | daily operator commands |
| 3 | Logging drivers and rotation | L1 · Junior | 6 | the most common "Docker filled my disk" cause |
| 4 | Images, layers, tags vs digests | L1 · Junior | 3 | what you actually ship and deploy |
| 5 | Dockerfile mastery (Python and Node examples) | L1–L3 · Junior→Senior | 4 | you will containerize your Apache workloads |
| 6 | Volumes, bind mounts, permissions | L1–L2 · Junior/Mid | 8 | data survives redeploys only if you get this right |
| 7 | Docker Compose | L1–L3 · Junior→Senior | 9 | how multi-container apps are described (and how Dokploy deploys Compose apps) |
| 8 | Resource limits, OOM, restart policies | L2 · Mid | 10 | exit 137, restart loops, noisy neighbours |
| 9 | Networking: bridges, DNS, ports, firewall | L2–L3 · Mid/Senior | 7 | where most of your real incidents will live |
| 10 | Debugging toolkit: netshoot, nsenter, events | L2 · Mid | 15 | look at the layer instead of guessing |
| 11 | Internals: namespaces and cgroups | L3 · Senior | 2 | turns "magic" into Linux you already know |
| 12 | daemon.json, address pools, data-root | L3 · Senior | 12 | on-prem subnet clashes and DNS fallbacks |
| 13 | Registries, Harbor, private CA, Trivy | L3 · Senior | 11 | your CI pipeline ends here |
| 14 | Security hardening | L3 · Senior | 13 | the docker group and the socket are root |
| 15 | Swarm essentials for Dokploy | L3 · Senior | 14 | Dokploy runs your apps as Swarm services |
| 16 | L3 drills and exit test: one Apache app to Dokploy | L3 exit · Senior | 16 | the Ops Ladder L3 exit test, done for real |
| 17 | Self-check per stage | all | 17 | prove each stage before you move on |
| 18 | Monitoring containers, game days, postmortems | L4 · Senior/Lead | [Observability](32-learn-performance-observability.md), [SRE practice](33-learn-cicd-iac-sre.md) | operate it, not just run it |

### Study method

For every ### topic, use the same five steps, in this order:

1. **Read this note** for the topic: concept, key terms, the "see it" commands. Ten to twenty minutes.
2. **Do the matching KodeKloud course lesson** (pointers sit at the top of each area under "Study path"), including its lab. KodeKloud labs are pre-built, so you practise the skill without fighting setup.
3. **Optional video** if a concept still feels fuzzy. Stop as soon as it clicks.
4. **Hands-on lab on your own test VM.** Build it, break it on purpose, fix it. This is where the skill actually forms; do not skip the "break" half.
5. **Open the related playbook** ([Containers & K8s playbook](26-playbook-containers-k8s.md) and the others linked in "How it breaks") and read the scenario that matches what you just broke, so the incident version feels familiar.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time. Those notes become your
public runbook repo later.

> Timebox. One topic per morning slot (30–45 minutes) is the Ops Ladder rhythm. Until your CKA
> exam, CKA sessions come first; Docker topics that also serve the CKA (sections 2, 3, 7, 10, 11)
> count double.

### Set up your Docker lab VM

Use two Ubuntu 24.04 VMs (2 vCPU, 4 GB RAM, 30 GB disk each) on a host-only or NAT network,
for example lab1 at 192.168.56.11 and lab2 at 192.168.56.12. One VM is enough for most labs;
the Swarm and overlay labs need both. **Take a snapshot after installing Docker** so every
"break it" lab can be undone in seconds.

> Never run the labs in this module on a work server. Several of them deliberately break DNS,
> the firewall, routing or the Docker daemon.

Install Docker Engine from Docker's own apt repository (the Ubuntu `docker.io` package works,
but lags behind and has a different package layout):

```bash
# 1. Remove distro packages that conflict with Docker's packages (safe if none are installed)
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  sudo apt-get remove -y "$pkg"
done

# 2. Add Docker's signing key and repository
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Install engine, CLI, containerd, buildx and the compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Lab-only convenience: run docker without sudo (root-equivalent, see section 13)
sudo usermod -aG docker "$USER"     # log out and back in afterwards

# 5. Tools used throughout the labs
sudo apt-get install -y jq tcpdump dnsutils netcat-openbsd iproute2
```

Verify:

```bash
docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'
docker info --format '{{.Driver}} | cgroup {{.CgroupDriver}} v{{.CgroupVersion}} | root {{.DockerRootDir}}'
docker run --rm hello-world
```

```
client 28.3.3 / server 28.3.3
overlay2 | cgroup systemd v2 | root /var/lib/docker
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

→ `overlay2` is the storage driver (a fresh Docker 29+ install shows `overlayfs`, the containerd
image store; see section 3). `systemd v2` means cgroup v2 with the systemd driver, the default on
Ubuntu 22.04 and later.

**RHEL/Rocky difference:** install `dnf-plugins-core` (it provides `config-manager`), add the repo with
`sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo`,
remove `podman` and `buildah` first if they conflict, then `sudo systemctl enable --now docker`
(on Ubuntu the package starts and enables the service for you). SELinux is enforcing on RHEL
family hosts; once dockerd's SELinux support is enabled (`"selinux-enabled": true`, off by default
in Docker CE) it changes how bind mounts behave (section 8).

---

## 1. Why containers

> 📚 **Study path:** 1) KodeKloud: *Crash Course: Docker For Absolute Beginners* (free, about 30 min) ([course](https://kodekloud.com/courses/crash-course-docker-for-absolute-beginner)) · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* (free) — Docker Commands ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 3) Note: this section, then the [Docker reference](14-docker-containers.md) · 4) Video: KodeKloud *Learn Docker in 2 Hours - A Full Tutorial (2025)*, first part ([YouTube](https://www.youtube.com/watch?v=zJ6WbK9zFpI)) · 5) Practice: KodeKloud Docker Playground ([playground](https://kodekloud.com/playgrounds/playground-docker)) or your lab VM.

### The problem containers solve

**Level:** [L0 · Fresher]

**Concept.** Look at the server from your incident: one Apache, three or four vhosts, one PHP
version, one OpenSSL, one set of system libraries, and one restart that affects every app at once.
Upgrading PHP for one app risks breaking the others, and nobody remembers which app needs which
port, log file or cron job. A **container** packages one app together with its userland (its
libraries, runtime, config defaults) into an **image**, and runs it as an isolated process with
its own filesystem view, network stack, process tree and resource budget. The same image runs on
your laptop, in GitLab CI and on the server.

Precisely: a container is an ordinary Linux process started with **namespaces** (what it can
see), **cgroups** (how much it can use), a root filesystem assembled from **image layers**
(overlayfs), and security filters (capabilities, seccomp, AppArmor/SELinux). There is no
"container" object in the kernel. That is the single most useful fact for troubleshooting:
every Linux tool you know still works on a container, from the host.

```
 Before: one Apache host                    After: one Dokploy host
 ┌────────────────────────────────┐         ┌──────────────────────────────────────┐
 │ apache2  :80 :443              │         │ Traefik container  :80 :443          │
 │  ├─ vhost shop   (PHP 8.1)     │         │  ├─ shop  container  (PHP 8.3)       │
 │  ├─ vhost blog   (PHP 8.1)     │         │  ├─ blog  container  (PHP 8.1)       │
 │  └─ vhost api  → :8080 (Java)  │         │  └─ api   container  (JRE 21)        │
 │ shared libs, one PHP, one      │         │ own libs per app, own limits, own    │
 │ restart affects every app      │         │ logs, redeploy and roll back one app │
 └────────────────────────────────┘         └──────────────────────────────────────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| Image | Read-only template: filesystem layers plus config (command, env, user, ports) |
| Container | A running (or stopped) instance of an image, with its own writable layer |
| Registry | Server that stores images (Docker Hub, Harbor, GitLab registry) |
| Tag | Human name for an image version, e.g. `web:1.4.2`; can be moved |
| Digest | Content hash of an image, e.g. `sha256:9b1e…`; can never change |
| Docker Engine | The daemon `dockerd` plus containerd and runc that actually run containers |

**See it on a real system**

```bash
uname -r                                          # host kernel
docker run --rm alpine:3.20 uname -r              # same kernel inside the container
docker run --rm alpine:3.20 cat /etc/os-release   # but a different userland
```

```
6.8.0-45-generic
6.8.0-45-generic
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.20.3
```

→ Same kernel, different distribution. The "Alpine" is only files in the image; the kernel is
always the host's.

**Hands-on lab (test VM only)**

**Step 1 — Run two versions side by side.** Two nginx versions, two host ports, zero conflict
over libraries:

```bash
docker run -d --name web-old -p 8081:80 nginx:1.26
docker run -d --name web-new -p 8082:80 nginx:1.27
curl -sI http://127.0.0.1:8081 | grep -i server
curl -sI http://127.0.0.1:8082 | grep -i server
```

```
Server: nginx/1.26.2
Server: nginx/1.27.2
```

**Step 2 — Break it: two containers want the same host port.** This is your Apache-holds-443
problem in miniature.

```bash
docker run -d --name web-clash -p 8081:80 nginx:1.27
```

```
docker: Error response from daemon: driver failed programming external connectivity on endpoint
web-clash (5c1d…): Bind for 0.0.0.0:8081 failed: port is already allocated.
```

→ "port is already allocated" means another **container** owns the port. When a non-Docker
process such as Apache owns it, the message instead ends in
`listen tcp4 0.0.0.0:443: bind: address already in use` (exact wording varies by version).

**Step 3 — Fix it.** Either pick another host port, or bind to loopback only when a reverse proxy
on the same host will front it:

```bash
docker rm web-clash
docker run -d --name web-clash -p 127.0.0.1:8083:80 nginx:1.27
sudo ss -ltnp | grep -E ':808[123]'
docker rm -f web-old web-new web-clash          # clean up
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `port is already allocated` | `docker ps --filter publish=PORT` | [Ports inventory](22-playbook-ports-inventory.md) |
| `bind: address already in use` | `sudo ss -ltnp 'sport = :PORT'` | [Ports inventory](22-playbook-ports-inventory.md) |
| "Works on my laptop", fails on the server | `docker image inspect IMAGE --format '{{.Architecture}}'` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** Containers do not remove the classic questions (which
process owns this port, where are its logs, what does it need); they move the answers into
`docker ps`, `docker logs` and `docker inspect`. Once you know a container is just a process, you
can always fall back to `ss`, `ps`, `/proc` and `journalctl`.

**Next step:** compare containers with the VMs you already run, so you know what a container does
*not* isolate.

### Container vs virtual machine

**Level:** [L0 · Fresher]

**Concept.** A VM virtualizes **hardware**: a hypervisor gives each guest its own virtual CPU,
memory, disk and NIC, and each guest boots its own kernel. A container virtualizes the
**operating system view**: all containers share the host kernel, and the kernel shows each one a
filtered view. Containers therefore start in milliseconds and cost megabytes, but they cannot run
a different kernel, cannot load kernel modules, and a kernel bug is shared by everyone.

```
   Virtual machines                         Containers
 ┌──────┐ ┌──────┐ ┌──────┐            ┌──────┐ ┌──────┐ ┌──────┐
 │ app  │ │ app  │ │ app  │            │ app  │ │ app  │ │ app  │
 │ libs │ │ libs │ │ libs │            │ libs │ │ libs │ │ libs │
 │kernel│ │kernel│ │kernel│            └──┬───┘ └──┬───┘ └──┬───┘
 └──┬───┘ └──┬───┘ └──┬───┘               namespaces + cgroups
 ┌──┴────────┴────────┴───┐            ┌──────────────────────────┐
 │ hypervisor (KVM/ESXi)  │            │ ONE host kernel          │
 ├────────────────────────┤            ├──────────────────────────┤
 │ hardware               │            │ hardware or a VM         │
 └────────────────────────┘            └──────────────────────────┘
```

| Aspect | Virtual machine | Container |
|---|---|---|
| Kernel | Own kernel per VM | Shares the host kernel |
| Start time | Tens of seconds (boot) | Milliseconds to seconds (exec a process) |
| Size | GBs (full OS) | MBs (userland only) |
| Isolation boundary | Hypervisor, strong | Kernel features, weaker; a kernel exploit escapes |
| Other OS | Any (Windows on Linux host) | Same kernel family only (Linux images on Linux) |
| CPU architecture | Emulated if needed | Must match the host (amd64 vs arm64) unless emulated by QEMU |
| Typical use | Tenancy boundary, different OS | Packaging and running apps densely |

In practice you run **containers inside VMs**: the VM is the security and tenancy boundary,
containers are the packaging inside it. Your Dokploy host is exactly that.

**Key terms:** hypervisor (KVM, ESXi, Hyper-V), guest kernel, shared kernel, platform
(`linux/amd64`, `linux/arm64`), emulation (QEMU binfmt).

**See it on a real system**

```bash
systemd-detect-virt                                # on the VM: kvm, vmware, microsoft, none…
docker run -d --name sleeper alpine:3.20 sleep 600
ps -eo pid,ppid,uid,cmd | grep '[s]leep 600'       # the container is a plain host process
docker image inspect alpine:3.20 --format '{{.Os}}/{{.Architecture}}'
docker rm -f sleeper
```

```
kvm
  48211   48188     0 sleep 600
linux/amd64
```

→ The "container" is PID 48211 on the host, a child of its containerd shim (PID 48188).

**Hands-on lab (test VM only)**

**Step 1 — Break it: a container cannot change the kernel.**

```bash
docker run --rm alpine:3.20 sh -c 'modprobe dummy; sysctl -w kernel.hostname=x'
```

```
modprobe: can't change directory to '/lib/modules': No such file or directory
sysctl: error setting key 'kernel.hostname': Read-only file system
```

→ No kernel modules, and `/proc/sys` is read-only. Kernel tuning belongs on the host
(or in per-container namespaced sysctls via `--sysctl`, for the few that are namespaced).

**Step 2 — Break it: wrong CPU architecture.** This is the classic "built on an Apple Silicon Mac,
fails on the amd64 server" incident:

```bash
docker run --rm --platform linux/arm64 alpine:3.20 uname -m
```

```
exec /bin/uname: exec format error
```

→ `exec format error` means the binary is for another CPU architecture (or a script has a broken
shebang, see section 4). Without QEMU emulation installed, an arm64 image cannot run on amd64.

**Step 3 — Fix it.** Build for the server's platform explicitly:

```bash
docker buildx build --platform linux/amd64 -t harbor.example.com/shop/web:1.4.2 .
docker buildx build --platform linux/amd64,linux/arm64 -t harbor.example.com/shop/web:1.4.2 --push .
```

→ The multi-platform line needs two things the single-platform one does not: a builder that can
produce multi-platform images (the containerd image store, default on fresh Docker 29+ installs, or
a `docker-container` builder from `docker buildx create --use`; the classic store with the default
`docker` driver refuses with "Multi-platform build is not supported for the docker driver"), and
QEMU binfmt handlers for any `RUN` step of the foreign architecture.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `exec format error` at start | `docker image inspect IMAGE --format '{{.Architecture}}'` | [Containers playbook](26-playbook-containers-k8s.md) |
| `no matching manifest for linux/amd64` on pull | `docker buildx imagetools inspect IMAGE` | [Containers playbook](26-playbook-containers-k8s.md) |
| App needs a kernel module or sysctl | load it on the host, not in the image | [Kernel reference](13-kernel-system.md) |

**Why it matters for troubleshooting.** Anything kernel-level (conntrack table, OOM killer,
`vm.max_map_count` for Elasticsearch, time) is shared. When a container misbehaves because of a
kernel setting, you fix it on the host, and the fix affects every container on that host.

**Next step:** see the pieces that turn `docker run` into a process.

### Docker architecture: CLI, dockerd, containerd, runc

**Level:** [L1 · Junior]

**Concept.** `docker` is only a client. It sends REST calls over a Unix socket to **dockerd**,
which manages images, networks, volumes and the API. dockerd hands container execution to
**containerd**, which starts one **shim** per container; the shim calls **runc** to create the
namespaces and cgroups and exec your process, then runc exits and the shim stays as the parent.
Kubernetes uses the same containerd and runc through the CRI, which is why this knowledge
transfers directly to your CKA work ([Kubernetes](31-learn-kubernetes.md)).

```
 docker CLI ──REST──▶ /var/run/docker.sock ──▶ dockerd          (docker.service)
                                                  │ gRPC
                                                  ▼
                       /run/containerd/containerd.sock ──▶ containerd   (containerd.service)
                                                  │ one shim per container
                                                  ▼
                                   containerd-shim-runc-v2 ──▶ runc (sets up ns + cgroups, execs, exits)
                                                  │
                                                  └── your app = PID 1 inside the container

 kubelet ──CRI──▶ containerd ──▶ shim ──▶ runc        (same bottom half on Kubernetes nodes)
```

**Key terms**

| Term | Meaning |
|---|---|
| dockerd | The Docker daemon; owns the API, images, networks, volumes, Swarm |
| docker.socket | systemd socket unit that starts dockerd on first API call |
| containerd | Container supervisor; also the Kubernetes runtime on your CKA nodes |
| shim | Small per-container parent process; keeps the container alive if dockerd restarts |
| runc | OCI runtime that actually creates the container, then exits |
| OCI | Open Container Initiative: the image and runtime standards everyone follows |

**See it on a real system**

```bash
systemctl status docker containerd --no-pager | grep -E '●|Active'
ps -eo pid,ppid,uid,cmd --forest | grep -A2 '[c]ontainerd-shim'
ls -l /var/run/docker.sock
docker context ls
```

```
● docker.service - Docker Application Container Engine
     Active: active (running) since Fri 2026-10-03 08:02:11 UTC; 2h 10min ago
● containerd.service - containerd container runtime
     Active: active (running) since Fri 2026-10-03 08:02:09 UTC; 2h 10min ago
   4188       1     0 /usr/bin/containerd-shim-runc-v2 -namespace moby -id 3f9c2a1b7d4e… -address /run/containerd/containerd.sock
   4211    4188     0  \_ nginx: master process nginx -g daemon off;
   4262    4211   101      \_ nginx: worker process
srw-rw---- 1 root docker 0 Oct  3 08:02 /var/run/docker.sock
NAME        DESCRIPTION                               DOCKER ENDPOINT               ERROR
default *   Current DOCKER_HOST based configuration   unix:///var/run/docker.sock
```

→ Containerd namespace `moby` is Docker's; Kubernetes uses `k8s.io`. The nginx worker runs as
UID 101 on the host too, because Docker does not use a user namespace by default. The socket is
owned by group `docker`: membership of that group is root access (section 13).

**Hands-on lab (test VM only)**

**Step 1 — Break it: stop the daemon.**

```bash
docker run -d --name web nginx:1.27
sudo systemctl stop docker
```

```
Warning: Stopping docker.service, but it can still be activated by:
  docker.socket
```

```bash
docker ps -a --format '{{.Names}} {{.Status}}'   # this call re-activates dockerd via the socket
```

→ The container was stopped with the daemon (unless `live-restore` is on, see section 12), and
started again only if it had a restart policy. Without one it now shows `Exited (0)`.

**Step 2 — Break it differently: a user without socket access.**

```bash
sudo -u nobody docker ps
```

```
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

→ Newer CLIs (Docker 29 era) word connection errors as "… the docker API at
unix:///var/run/docker.sock" instead of "Docker daemon socket"; grep for `docker.sock` rather than
the exact sentence.

**Step 3 — Fix and observe.** Start what you stopped and read the daemon's own log:

```bash
sudo systemctl start docker
docker start web
journalctl -u docker -n 30 --no-pager
docker rm -f web
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Cannot connect to the Docker daemon at unix:///var/run/docker.sock` (newer CLIs: `failed to connect to the docker API at …`) | `systemctl status docker` then `journalctl -u docker -b` | [Containers playbook](26-playbook-containers-k8s.md) |
| `permission denied ... docker.sock` | `id` (is the user in group docker?) | [Users & permissions](10-users-permissions-security.md) |
| dockerd fails after editing daemon.json | `sudo dockerd --validate --config-file /etc/docker/daemon.json` | section 12 |
| All containers stopped after a Docker upgrade | `docker ps -a`, check restart policies | section 10 |

**Why it matters for troubleshooting.** When `docker` commands hang or fail, you debug a systemd
service (dockerd) with journalctl like any other unit. When containers survive a dockerd crash,
thank the shim. On Kubernetes nodes there is no dockerd, but the same containerd and shim are
there, so `crictl` and `ctr` replace the `docker` CLI.

**Next step:** open the box and see what namespaces and cgroups a container really consists of.

---

## 2. What a container really is

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Engine & Storage (namespaces, cgroups) ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine – Security, plus the lesson note *Networking Deep Dive – Namespaces* ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Namespaces/page)) · 3) Note: this section, with [Linux processes and /proc](27-learn-linux.md) as background · 4) Practice: the unshare lab below, then the iximiuz Labs Docker roadmap ([roadmap](https://labs.iximiuz.com/roadmaps/docker)).

### Namespaces: what the process can see

**Level:** [L3 · Senior]

**Concept.** A namespace wraps one kind of global kernel resource so that processes inside it see
their own private copy. A container is a process placed into a fresh set of namespaces. Plainly:
namespaces are the **walls**; they decide what the process can see, not how much it can use.

| Namespace | Isolates | Docker shares it with the host when you pass |
|---|---|---|
| pid | Process IDs; the app becomes PID 1 | `--pid host` |
| net | Interfaces, IPs, routes, iptables rules, ports | `--network host` |
| mnt | The mount table, so the filesystem view | (bind mounts deliberately punch holes) |
| uts | Hostname and domain name | `--uts host` |
| ipc | System V IPC, POSIX message queues, `/dev/shm` | `--ipc host` |
| user | UID/GID mapping (root inside = unprivileged outside) | only used with rootless or `userns-remap` |
| cgroup | The process's view of `/sys/fs/cgroup` | `--cgroupns host` |
| time | Boot and monotonic clock offsets | not used by Docker |

```
 Host PID namespace                         Container PID namespace (a child of the host's)
 PID 1     systemd                          (invisible to the container)
 PID 4188  containerd-shim-runc-v2
 PID 4211  nginx: master   ─── same process ──▶  PID 1  nginx: master
 PID 4262  nginx: worker   ─── same process ──▶  PID 29 nginx: worker
```

→ The host sees every container process with host PIDs; the container sees only its own,
renumbered from 1. That asymmetry is why you can debug any container from the host.

**Key terms:** `lsns` (list namespaces), `nsenter` (run a command inside a process's
namespaces), `unshare` (start a process in new namespaces), `/proc/PID/ns/` (namespace handles),
`/run/docker/netns/` (Docker's named network namespaces).

**See it on a real system**

```bash
docker run -d --name web nginx:1.27
PID=$(docker inspect -f '{{.State.Pid}}' web); echo "$PID"
sudo lsns -p "$PID"
sudo ls -l /proc/"$PID"/ns
sudo nsenter -t "$PID" -n ip -br addr          # host's ip binary, container's network
sudo nsenter -t "$PID" -n ss -ltn              # what listens INSIDE the container
sudo nsenter -t "$PID" -u hostname
```

```
4211
        NS TYPE   NPROCS   PID USER COMMAND
4026531834 time      196     1 root /sbin/init
4026531837 user      196     1 root /sbin/init
4026532297 mnt         3  4211 root nginx: master process nginx -g daemon off;
4026532298 uts         3  4211 root nginx: master process nginx -g daemon off;
4026532299 ipc         3  4211 root nginx: master process nginx -g daemon off;
4026532300 pid         3  4211 root nginx: master process nginx -g daemon off;
4026532302 net         3  4211 root nginx: master process nginx -g daemon off;
4026532361 cgroup      3  4211 root nginx: master process nginx -g daemon off;
lrwxrwxrwx 1 root root 0 Oct  3 10:12 cgroup -> 'cgroup:[4026532361]'
lrwxrwxrwx 1 root root 0 Oct  3 10:12 ipc -> 'ipc:[4026532299]'
lrwxrwxrwx 1 root root 0 Oct  3 10:12 mnt -> 'mnt:[4026532297]'
lrwxrwxrwx 1 root root 0 Oct  3 10:12 net -> 'net:[4026532302]'
lrwxrwxrwx 1 root root 0 Oct  3 10:12 pid -> 'pid:[4026532300]'
…
lo               UNKNOWN        127.0.0.1/8
eth0@if23        UP             172.17.0.2/16
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      511          0.0.0.0:80        0.0.0.0:*
LISTEN 0      511             [::]:80           [::]:*
3f9c2a1b7d4e
```

→ `time` and `user` belong to PID 1 (shared with the host); the other six are new. `eth0@if23`
means the container's eth0 is one end of a veth pair whose other end is host interface index 23
(section 7). The hostname is the short container ID.

**Hands-on lab (test VM only)**

**Step 1 — Build a "container" by hand with unshare.** No Docker involved:

```bash
sudo unshare --pid --fork --mount-proc --uts --net --ipc bash
hostname box1; hostname       # changes only this UTS namespace
ps -ef                        # bash is PID 1, nothing else exists
ip link                       # only lo, and it is DOWN: an empty network namespace
exit
```

**Step 2 — Give it a root filesystem.** Borrow Alpine's filesystem from an image:

```bash
sudo mkdir -p /srv/lab/alpine-root
docker export "$(docker create alpine:3.20)" | sudo tar -C /srv/lab/alpine-root -xf -
sudo unshare --pid --fork --mount-proc=/srv/lab/alpine-root/proc --uts --net --ipc \
  chroot /srv/lab/alpine-root /bin/sh
cat /etc/os-release | head -1    # NAME="Alpine Linux"
ps                               # PID 1 is sh
exit
```

→ That is 80% of what runc does. The remaining 20% is cgroups, pivot_root instead of chroot,
capabilities, seccomp and a network interface.

**Step 3 — Break it: share host namespaces.**

```bash
docker run --rm --network host alpine:3.20 ip -br addr    # sees the HOST's interfaces
docker run --rm --pid host alpine:3.20 ps | head -5       # sees every host process
```

→ `--network host` and `--pid host` remove the walls. With `--pid host`, root in the container
can also signal host processes unless an LSM stops it: on Ubuntu the `docker-default` AppArmor
profile only allows signals between confined container processes, so `kill` of a host process
fails there; on hosts without AppArmor (or with `--privileged`) it succeeds. Legitimate for a few tools (node exporters,
debugging), dangerous for apps.

**Step 4 — Fix and clean up.** Drop the host flags, then `docker rm -f web` and
`sudo rm -rf /srv/lab/alpine-root` (lab directory only; double-check the path before you run it).

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `OCI runtime exec failed: exec failed: unable to start container process: exec: "bash": executable file not found in $PATH` | `docker exec -it CONTAINER sh`, or `nsenter` with host tools | [Containers playbook](26-playbook-containers-k8s.md) |
| `nsenter: cannot open /proc/PID/ns/net: No such file or directory` | the container restarted; re-read `docker inspect -f '{{.State.Pid}}'` | section 15 |
| App reachable from inside the container but not from the host | `sudo nsenter -t PID -n ss -ltn` (listening on 127.0.0.1?) | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** "localhost" inside a container is the container's own
loopback, not the host's. A minimal image without `ss`, `ip` or `tcpdump` can still be debugged:
`nsenter -t PID -n` runs the host's tools inside the container's network namespace.

**Next step:** namespaces limit what a process sees; cgroups limit what it uses.

### Cgroups v2: what the process may use

**Level:** [L3 · Senior]

**Concept.** Control groups put processes into a hierarchy and attach **budgets** and
**accounting** to each node: memory, CPU time, I/O bandwidth, number of processes. Ubuntu 22.04+
and RHEL 9 use **cgroup v2**, a single unified tree mounted at `/sys/fs/cgroup`. Docker with the
systemd cgroup driver creates one systemd scope per container:
`/sys/fs/cgroup/system.slice/docker-FULL_CONTAINER_ID.scope/`. Plainly: cgroups are the
**budget**; when a container exceeds its memory budget, the kernel OOM-kills inside that cgroup
even if the host has plenty of free memory.

```
 /sys/fs/cgroup                      (root of the unified hierarchy)
 ├── system.slice
 │   ├── docker.service              dockerd itself
 │   ├── containerd.service
 │   ├── docker-3f9c2a1b….scope      container "web"   memory.max=268435456  cpu.max="50000 100000"
 │   └── docker-9c2d11ab….scope      container "worker"
 └── user.slice                      your SSH sessions
```

**Key terms**

| File | Meaning |
|---|---|
| `memory.max` | Hard memory limit (`max` = unlimited); set by `--memory` |
| `memory.current` | Current usage including page cache |
| `memory.events` | Counters: `max` (hit the limit), `oom`, `oom_kill` |
| `memory.peak` | Highest usage seen (kernel 5.19+, so Ubuntu 24.04 yes, 22.04 GA kernel no) |
| `cpu.max` | Quota and period in µs: `50000 100000` = 0.5 CPU; set by `--cpus` |
| `cpu.stat` | `nr_throttled`, `throttled_usec`: how often the quota bit |
| `pids.max` / `pids.current` | Process/thread limit; set by `--pids-limit` |
| `io.max` / `io.stat` | Block I/O limits and counters |

**See it on a real system**

```bash
stat -fc %T /sys/fs/cgroup                      # cgroup2fs = v2
docker info --format '{{.CgroupDriver}} {{.CgroupVersion}}'
docker run -d --name lim -m 256m --cpus 0.5 --pids-limit 100 nginx:1.27
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' lim).scope
cat /proc/"$(docker inspect -f '{{.State.Pid}}' lim)"/cgroup
cat "$CG"/memory.max "$CG"/cpu.max "$CG"/pids.max
cat "$CG"/memory.events
grep -E 'nr_periods|nr_throttled|throttled_usec' "$CG"/cpu.stat
systemd-cgtop -n 1 | head -12
```

```
cgroup2fs
systemd 2
0::/system.slice/docker-8a1f0c2e5b7d9e3f4a6c8b0d2e4f6a8c0b2d4e6f8a0c2e4f6a8b0c2d4e6f8a0c.scope
268435456
50000 100000
100
low 0
high 0
max 0
oom 0
oom_kill 0
oom_group_kill 0
nr_periods 1204
nr_throttled 0
throttled_usec 0
```

→ 256 MiB, half a CPU, 100 PIDs, no OOM events yet. `/proc/PID/cgroup` is also the reverse
lookup: given any process on the host, it tells you which container it belongs to.

**RHEL/Rocky difference:** RHEL 9 is cgroup v2 like Ubuntu. RHEL 8 and older Ubuntu (20.04) use
cgroup v1 by default, where the same files live under `/sys/fs/cgroup/memory/docker/ID/` with
v1 names (`memory.limit_in_bytes`, `memory.oom_control`).

**Hands-on lab (test VM only)**

**Step 1 — Break it: a contained fork bomb.**

```bash
docker run --rm --pids-limit 50 alpine:3.20 sh -c 'for i in $(seq 1 100); do sleep 60 & done; wait'
```

```
sh: can't fork: Resource temporarily unavailable
```

→ The cgroup stopped process number 51. Without `--pids-limit`, a runaway process could exhaust
the host's PID space and take SSH down with it.

**Step 2 — Break it: CPU throttling.** The host is idle, yet the app is slow:

```bash
docker run -d --name burn --cpus 0.5 alpine:3.20 sh -c 'while :; do :; done'
docker stats --no-stream burn
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' burn).scope
sleep 5; grep -E 'nr_throttled|throttled_usec' "$CG"/cpu.stat
```

```
CONTAINER ID   NAME   CPU %    MEM USAGE / LIMIT   MEM %   NET I/O     BLOCK I/O   PIDS
7c0e41d2a9b3   burn   50.12%   400KiB / 3.82GiB    0.01%   796B / 0B   0B / 0B     1
nr_throttled 52
throttled_usec 2581234
```

→ Exactly 50% and a growing `nr_throttled`: the process wants more and the quota says no. In a
real app this looks like slow responses while `top` shows an idle host.

**Step 3 — Fix it.** Raise or remove the limit live, then clean up:

```bash
docker update --cpus 1.5 burn
docker rm -f burn lim
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Exit 137, `OOMKilled: true`, host `free -h` looks fine | `cat CG/memory.events`, `journalctl -k -g 'out of memory'` | section 10, [Memory](04-memory.md) |
| Slow app, host CPU idle | `grep throttled CG/cpu.stat` | [Slow system playbook](23-playbook-slow-system.md) |
| `can't fork` / `Resource temporarily unavailable` | `cat CG/pids.current CG/pids.max` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** The kernel enforces limits per cgroup, so host-wide tools
lie by omission: `free` shows a healthy host while the container hits its own wall.
`memory.events` and `cpu.stat` are the ground truth, and they are exactly what Kubernetes uses for
pod limits ([Kubernetes](31-learn-kubernetes.md)).

**Next step:** map processes, ports and files on the host back to the container that owns them.

### Seeing a container from the host

**Level:** [L2 · Mid]

**Concept.** During an incident you usually start from the host side: a PID eating CPU, a port in
`ss`, a big file under `/var/lib/docker`. You need to translate host objects into container
names, and back. Four mappings cover almost everything.

| You have | You want | How |
|---|---|---|
| Container name | Host PID | `docker inspect -f '{{.State.Pid}}' CONTAINER` |
| Host PID | Container | `cat /proc/PID/cgroup` (scope name contains the container ID) |
| Host port | Container | `docker ps --filter publish=PORT` |
| Container | Its files, from the host | `sudo ls /proc/PID/root/` (the container's `/`) |

**Key terms:** *host PID* (the container's main process as the host numbers it, from `docker inspect -f '{{.State.Pid}}'`), *cgroup scope* (`docker-ID.scope`, the cgroup whose name carries the container ID), *docker-proxy* (the userland helper that may hold a published port in `ss`), *`/proc/PID/root`* (the container's root filesystem, seen from the host).

**See it on a real system**

```bash
# Which container is PID 4262 (seen burning CPU in top)?
cat /proc/4262/cgroup
docker ps --no-trunc --format '{{.ID}} {{.Names}}' | grep 3f9c2a1b7d4e

# Who owns host port 443? ss shows only the proxy process, not the container
sudo ss -ltnp 'sport = :443'
docker ps --filter publish=443 --format '{{.Names}}\t{{.Ports}}'

# Read a container's config file without exec (works for distroless images too)
sudo cat /proc/4211/root/etc/nginx/conf.d/default.conf | head -5

# One-shot table: every container with its PID
docker ps -q | xargs docker inspect --format '{{.State.Pid}}  {{.Name}}'
```

```
0::/system.slice/docker-3f9c2a1b7d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a.scope
3f9c2a1b7d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a web
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:443       0.0.0.0:*     users:(("docker-proxy",pid=5123,fd=7))
dokploy-traefik	0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
server {
    listen       80;
    listen  [::]:80;
    server_name  localhost;
4211  /web
4877  /worker
```

→ On a plain container, `ss` shows `docker-proxy` as the owner of a published port. For a port
published by a **Swarm** service through the routing mesh, `ss` shows `dockerd` instead
(section 14). For a plain container, `docker ps --filter publish=PORT` names it; a routing-mesh port
belongs to the *service*, not to a task container, so there use
`docker service ls --format '{{.Name}} {{.Ports}}' | grep ':PORT->'`. This is the
missing link in the "which app owns which port" inventory from your Apache incident
([Ports inventory](22-playbook-ports-inventory.md)).

**Hands-on lab (test VM only)**

**Step 1 — Build it.** Start three containers, one publishing 8443:

```bash
docker run -d --name a nginx:1.27
docker run -d --name b -p 8443:80 nginx:1.27
docker run -d --name c alpine:3.20 sh -c 'while :; do :; done'   # the CPU hog
```

**Step 2 — Break it (pretend you do not know the names).** Find the hog from `top` alone, then
find the owner of 8443 from `ss` alone, using only the mappings above.

**Step 3 — Fix it.** `docker update --cpus 0.2 c` (or `docker stop c`), confirm with
`docker stats --no-stream`, then `docker rm -f a b c`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| `ss` shows `docker-proxy` or `dockerd` on a port; nobody knows which app | `docker ps --filter publish=PORT` (docker-proxy) or `docker service ls` PORTS column (dockerd, Swarm) | [Ports inventory](22-playbook-ports-inventory.md) |
| A host PID is hot in `top` | `cat /proc/PID/cgroup` | [Slow system playbook](23-playbook-slow-system.md) |
| Need a file from a container that has no shell | `sudo cat /proc/PID/root/PATH` or `docker cp` | section 5 |

**Why it matters for troubleshooting.** The Apache incident was slow because every mapping
(port to process to config to logs) was a fresh search. With containers the mappings are
mechanical, if you know these four.

**Next step:** what the container's filesystem is made of: images and layers.

---

## 3. Images, layers and overlay2

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Images, then Docker Engine & Storage ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Image Management: Image Addressing Convention, Build Cache ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Note: this section · 4) Video: *Learn Docker in 2 Hours - A Full Tutorial (2025)*, images part ([YouTube](https://www.youtube.com/watch?v=zJ6WbK9zFpI)) · 5) Practice: take one real image apart with `docker image inspect`, `docker history` and `dive` on your lab VM.

### Image anatomy: manifest, config and layers

**Level:** [L1 · Junior]

**Concept.** An image is three kinds of content-addressed objects. **Layers** are tar archives of
filesystem changes (files added, changed, deleted). The **config** is a JSON document with the
runtime defaults (command, entrypoint, env, user, working directory, exposed ports, stop signal)
and the build history. The **manifest** lists the config and the layers by their sha256 digests.
A multi-architecture image adds an **index** (manifest list) that points to one manifest per
platform. Plainly: an image is a stack of tarballs plus a note saying how to start it.

```
 nginx:1.27 (tag) ──▶ index sha256:2840…             (multi-arch)
                        ├─ linux/amd64 manifest sha256:7c1a… ─▶ config sha256:3b25… + layers L1…L7
                        └─ linux/arm64 manifest sha256:d0e4… ─▶ config sha256:9f02… + layers L1…L7
```

**Key terms**

| Term | Meaning |
|---|---|
| Layer | One tarball of filesystem changes; shared between images that use the same base |
| Config | JSON with Cmd, Entrypoint, Env, User, WorkingDir, ExposedPorts, StopSignal, history |
| Manifest | Lists the config digest and layer digests for one platform |
| Index | Lists manifests per platform (amd64, arm64…) |
| Image ID | Local identifier (digest of the config, or of the manifest with the containerd store) |
| Repo digest | Digest of what the registry serves; the value you pin with `@sha256:` |

**See it on a real system**

```bash
docker pull nginx:1.27
docker image inspect nginx:1.27 --format '{{json .Config}}' \
  | jq -c '{Entrypoint, Cmd, User, WorkingDir, ExposedPorts, StopSignal}'
docker image inspect nginx:1.27 --format '{{len .RootFS.Layers}} layers'
docker history nginx:1.27
```

```
{"Entrypoint":["/docker-entrypoint.sh"],"Cmd":["nginx","-g","daemon off;"],"User":"","WorkingDir":"","ExposedPorts":{"80/tcp":{}},"StopSignal":"SIGQUIT"}
7 layers
IMAGE          CREATED       CREATED BY                                      SIZE      COMMENT
3b25b682ea82   3 weeks ago   CMD ["nginx" "-g" "daemon off;"]                0B        buildkit.dockerfile.v0
<missing>      3 weeks ago   STOPSIGNAL SIGQUIT                              0B        buildkit.dockerfile.v0
<missing>      3 weeks ago   EXPOSE map[80/tcp:{}]                           0B        buildkit.dockerfile.v0
<missing>      3 weeks ago   ENTRYPOINT ["/docker-entrypoint.sh"]            0B        buildkit.dockerfile.v0
<missing>      3 weeks ago   COPY 30-tune-worker-processes.sh /docker-ent…   4.62kB    buildkit.dockerfile.v0
…              (four more COPY rows: docker-entrypoint.sh and the other entrypoint scripts)
<missing>      3 weeks ago   RUN /bin/sh -c set -x     && groupadd --syst…   112MB     buildkit.dockerfile.v0
…              (ENV and LABEL rows, 0B each)
<missing>      3 weeks ago   # debian.sh --arch 'amd64' out/ 'bookworm' '…   74.8MB    debuerreotype 0.15
```

→ `User` is empty, so nginx's master runs as root (the workers drop to UID 101). `StopSignal`
is `SIGQUIT`, nginx's graceful shutdown. In `docker history`, `0B` rows are metadata only;
`<missing>` just means that intermediate layer was built elsewhere, not that something is broken.
The 112 MB row is where you would look first if the image were too big.

**Hands-on lab (test VM only)**

**Step 1 — Build it: an image that "deletes" a secret.**

```bash
mkdir -p ~/lab/leak && cd ~/lab/leak
cat > Dockerfile <<'EOF'
FROM alpine:3.20
RUN echo "db_password=Sup3rS3cret" > /root/.cred
RUN rm /root/.cred
EOF
docker build -t leak:1 .
docker run --rm leak:1 ls -la /root          # the file is gone… in the final view
```

**Step 2 — Break it: recover the secret from the layers.** Layers are immutable; the `rm` only
added a whiteout on top.

```bash
docker save leak:1 -o leak.tar && mkdir -p x && tar -xf leak.tar -C x
find x -type f | while read -r f; do
  tar -tf "$f" 2>/dev/null | grep -qx 'root/.cred' && { echo "found in $f"; tar -xOf "$f" root/.cred; }
done
```

```
found in x/blobs/sha256/6f0a…
db_password=Sup3rS3cret
```

**Step 3 — Fix it.** Never put secrets in a layer, even briefly. Use a BuildKit secret mount
(section 4, "COPY vs ADD and ARG vs ENV"), which is never written to any layer. Clean up with
`cd ~ && rm -rf ~/lab/leak && docker rmi leak:1`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Image is huge, pulls are slow | `docker history --no-trunc IMAGE`, `dive IMAGE` (section 15) | [Containers playbook](26-playbook-containers-k8s.md) |
| Credentials found in an image by a scanner | `docker history --no-trunc IMAGE` | section 13 |
| Container starts the wrong command | `docker image inspect IMAGE --format '{{json .Config}}'` | section 4 |

**Why it matters for troubleshooting.** `docker image inspect` tells you how a container *will*
start (user, command, ports, stop signal) before you run it. When "the same image" behaves
differently on two hosts, compare digests, not tags.

**Next step:** how those read-only layers become a writable filesystem for a running container.

### overlay2 and the writable layer

**Level:** [L2 · Mid]

**Concept.** The storage driver stacks the image's read-only layers (**lowerdir**) under one
writable directory per container (**upperdir**) and presents the union as the container's `/`
(**merged**). Reading a file finds the topmost copy. Modifying a lower file first copies it up
(**copy-up**); deleting it writes a **whiteout** in the upper layer. Removing the container
deletes its upperdir, so every change made inside a container dies with it.

```
 merged/      what the container sees as /
    ▲
 upperdir     container layer (read-write)   ← writes, copy-ups, whiteouts; deleted with the container
 lowerdir     "-init" layer (hosts, resolv.conf, hostname mount points)
 lowerdir     image layer N (read-only)
 lowerdir     …
 lowerdir     image layer 1 (read-only)       shared by every container from this image
```

**Key terms:** storage driver (`overlay2`, or `overlayfs` with the containerd image store), copy-up,
whiteout, `docker diff` (A = added, C = changed, D = deleted), `docker ps -s` (writable layer size).

> Docker Engine 29 made the **containerd image store** the default for fresh installs; upgraded
> hosts keep the classic `overlay2` driver. With the containerd store, `docker info` shows
> `Storage Driver: overlayfs` and image data lives under containerd's root (by default
> `/var/lib/containerd`) instead of `/var/lib/docker/overlay2`. When hunting disk usage, check both.

**See it on a real system**

```bash
docker run -d --name web nginx:1.27
docker info --format '{{.Driver}}'
docker inspect web --format '{{json .GraphDriver}}' | jq
docker diff web
docker ps -s --format 'table {{.Names}}\t{{.Size}}'
sudo du -sh /var/lib/docker/overlay2
```

```
overlay2
{
  "Data": {
    "LowerDir": "/var/lib/docker/overlay2/5f1e…-init/diff:/var/lib/docker/overlay2/a9c3…/diff:…",
    "MergedDir": "/var/lib/docker/overlay2/5f1e…/merged",
    "UpperDir": "/var/lib/docker/overlay2/5f1e…/diff",
    "WorkDir": "/var/lib/docker/overlay2/5f1e…/work"
  },
  "Name": "overlay2"
}
C /etc
C /etc/nginx
C /etc/nginx/conf.d
C /etc/nginx/conf.d/default.conf
C /var/cache/nginx
A /var/cache/nginx/client_temp
A /var/cache/nginx/fastcgi_temp
C /run
A /run/nginx.pid
NAMES     SIZE
web       1.09kB (virtual 192MB)
6.4G    /var/lib/docker/overlay2
```

→ `default.conf` changed because the image's entrypoint script edits it at start (IPv6 listen).
The container's own layer is 1.09 kB; the 192 MB "virtual" size is the shared image underneath.

**Hands-on lab (test VM only)**

**Step 1 — Break it: an app that writes inside its container.**

```bash
docker exec web sh -c 'dd if=/dev/zero of=/var/log/nginx/app-debug.log bs=1M count=500 status=none'
docker ps -s --format 'table {{.Names}}\t{{.Size}}'
docker diff web | grep app-debug
```

```
NAMES     SIZE
web       524MB (virtual 716MB)
A /var/log/nginx/app-debug.log
```

→ This is how a container silently fills `/var/lib/docker`: an app logging to a file inside the
container instead of stdout or a volume.

**Step 2 — Break it again: hand-edit a running container, then redeploy.**

```bash
docker exec web sh -c 'echo "hotfix" > /usr/share/nginx/html/index.html'
docker rm -f web && docker run -d --name web -p 8080:80 nginx:1.27
curl -s http://127.0.0.1:8080 | head -3          # the hotfix is gone
```

**Step 3 — Fix it.** Changes belong in the image (rebuild) or in a volume/bind mount (section 8);
logs belong on stdout (section 6). Clean up with `docker rm -f web`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `no space left on device` during pull, build or run | `docker system df`, `sudo du -xh --max-depth=1 /var/lib/docker` | [Containers playbook](26-playbook-containers-k8s.md) |
| Container's writable layer keeps growing | `docker ps -s`, `docker diff CONTAINER` | section 6 |
| Manual fix vanished after redeploy | it lived in the upperdir; put it in the image or a volume | section 8 |
| dockerd refuses overlay2 on XFS (`d_type` / `ftype=0` message in the journal) | `xfs_info /var/lib/docker` (needs `ftype=1`) | section 12 |

**Why it matters for troubleshooting.** Disk incidents on Docker hosts come from four places:
image layers, writable layers, volumes and JSON logs. `docker diff` and `docker ps -s` find the
writable-layer culprit in seconds.

**Next step:** tags versus digests, which decide *which* image actually runs.

### Tags vs digests

**Level:** [L1 · Junior]

**Concept.** A **tag** (`web:1.4.2`, `web:latest`) is a movable pointer, like a Git branch. A
**digest** (`web@sha256:9b1e…`) identifies exact content, like a Git commit hash. `latest` is
just a tag name with no special meaning. Deploying by tag means two nodes that pulled at
different times can run different code under the same name. A running container is bound to the
image **ID** it was created from; pulling a newer image under the same tag changes nothing until
you recreate the container.

**Key terms:** tag, digest, `RepoDigests`, dangling image (`<none>:<none>`), immutable tags
(a Harbor project rule that forbids overwriting matching tags).

**See it on a real system**

```bash
docker images --digests nginx
docker image inspect nginx:1.27 --format '{{index .RepoDigests 0}}'
docker buildx imagetools inspect nginx:1.27 | head -12
docker inspect CONTAINER --format '{{.Config.Image}} -> {{.Image}}'   # requested name -> actual image ID
```

```
REPOSITORY   TAG    DIGEST                                                                    IMAGE ID       CREATED       SIZE
nginx        1.27   sha256:28402db69fec7c17e179ea87882667f1e054391138f77ffaf0c3eb388efc3ffb   3b25b682ea82   3 weeks ago   192MB
nginx@sha256:28402db69fec7c17e179ea87882667f1e054391138f77ffaf0c3eb388efc3ffb
Name:      docker.io/library/nginx:1.27
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:28402db69fec7c17e179ea87882667f1e054391138f77ffaf0c3eb388efc3ffb

Manifests:
  Name:        docker.io/library/nginx:1.27@sha256:7c1a4b…
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/amd64
```

**Hands-on lab (test VM only)**

**Step 1 — Build it.** Version 1 under the tag `latest`:

```bash
mkdir -p ~/lab/tags && cd ~/lab/tags
printf 'FROM alpine:3.20\nRUN echo v1 > /version\nCMD ["sh","-c","cat /version; sleep 3600"]\n' > Dockerfile
docker build -q -t myapp:latest .
docker run -d --name t1 myapp:latest
```

**Step 2 — Break it: "I deployed the new version but it still serves the old one."**

```bash
sed -i 's/v1/v2/' Dockerfile && docker build -q -t myapp:latest .
docker logs t1                                     # still v1
docker run --rm myapp:latest cat /version          # v2
docker inspect t1 --format '{{.Image}}'
docker image inspect myapp:latest --format '{{.Id}}'
docker images myapp
```

```
v1
v2
sha256:41c7…
sha256:b98e…
REPOSITORY   TAG       IMAGE ID       CREATED          SIZE
myapp        latest    b98e0d6f2a11   5 seconds ago    7.8MB
myapp        <none>    41c7a3e9b0f4   40 seconds ago   7.8MB
```

→ The tag moved; the container did not. The old image is now dangling (`<none>`) but still in
use by `t1`.

> Docker CLI 29 changed the plain `docker images` output: it prints a new compact view (columns
> such as IMAGE, ID, DISK USAGE, CONTENT SIZE) and hides untagged images unless you add `-a`. To get
> the classic columns shown in this module on any version, pass a format, for example
> `docker images -a --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}' myapp`.

**Step 3 — Fix it.** Recreate the container, and in CI tag every build with the commit SHA so a
tag never moves:

```bash
docker rm -f t1 && docker run -d --name t1 myapp:latest      # now v2
docker tag myapp:latest harbor.example.com/shop/myapp:3f9c2a1
# Compose: docker compose pull && docker compose up -d   (recreates changed services)
# Swarm:   docker service update --image harbor.example.com/shop/myapp:3f9c2a1 SERVICE
docker rm -f t1 && cd ~ && rm -rf ~/lab/tags
```

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| New version pulled, old one still served | `docker inspect CONTAINER --format '{{.Image}}'` vs the tag's ID | [Containers playbook](26-playbook-containers-k8s.md) |
| Two Swarm nodes run different code under one tag | `docker service ps SERVICE --no-trunc` (shows the digest per task) | section 14 |
| `manifest unknown` on pull | tag typo or tag deleted; `docker buildx imagetools inspect IMAGE` | section 11 |

**Why it matters for troubleshooting.** "What exactly is running?" is the first question in any
regression. A digest answers it; a tag does not. Rollback is also only reliable when the old
version still has an unchanged tag or a pinned digest.

**Next step:** write images yourself: Dockerfile mastery.

---

## 4. Dockerfile mastery

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Images (BuildKit, docker init, CMD vs ENTRYPOINT, env vars) ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Image Management: Build Cache, Multi-Stage Builds ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page)), Dockerfile Best Practices · 3) Note: this section and its two worked examples · 4) Practice: build the Python and Node images below, then a Docker task from 100 Days of DevOps ([100 Days](https://kodekloud.com/100-days-of-devops)).

### Dockerfile instructions at a glance

**Level:** [L1 · Junior]

**Concept.** A Dockerfile is a recipe executed top to bottom by BuildKit (the default builder
since Docker Engine 23). Instructions that change files (`RUN`, `COPY`, `ADD`) create layers; the
rest only edit the image config. Each instruction is also a **cache key**: if it and everything
before it are unchanged, BuildKit reuses the previous result.

| Instruction | What it does | Layer? | Senior rule |
|---|---|---|---|
| `FROM` | Base image; starts a stage | — | Pin a version (`python:3.12-slim`), never bare `latest`; name stages with `AS` |
| `RUN` | Runs a command at build time | yes | Chain related steps with `&&`; clean package caches in the same `RUN` |
| `COPY` | Copies from the build context or another stage | yes | Prefer over `ADD`; use `--chown`, `--chmod`, `--from` |
| `ADD` | `COPY` plus local tar auto-extract and remote URLs | yes | Only for extracting a local tarball, or URLs with `--checksum` |
| `WORKDIR` | Sets (and creates) the working directory | dir only | Absolute paths; never `RUN cd …` |
| `ENV` | Variable at build time and at runtime | no | Never for secrets: visible in `docker inspect` |
| `ARG` | Variable at build time only | no | Never for secrets: visible in `docker history` |
| `USER` | User for later `RUN` steps and for runtime | no | Numeric `UID:GID` for the runtime user |
| `EXPOSE` | Documents a port | no | Publishes nothing; a hint for humans, `-P` and Traefik |
| `VOLUME` | Declares a mount point | no | Creates anonymous volumes on every run; avoid in app images |
| `HEALTHCHECK` | Command that reports health | no | Use a tool that exists in the image |
| `ENTRYPOINT` | The fixed executable | no | Exec form (JSON array) |
| `CMD` | Default command or default arguments | no | Exec form (JSON array) |
| `LABEL` | Metadata | no | OCI labels: source repo, revision |
| `STOPSIGNAL` | Signal sent by `docker stop` | no | Match the app's graceful-shutdown signal |
| `SHELL` | Shell used by shell-form `RUN` | no | `["/bin/bash", "-o", "pipefail", "-c"]` when you pipe in `RUN` |

**Key terms:** build context (the directory sent to the builder), stage, target, BuildKit,
`# syntax=docker/dockerfile:1` (first line; pins the Dockerfile frontend so new features work).

**See it on a real system**

```bash
docker buildx version
docker buildx ls                                   # builders; "default" uses the docker driver
docker build --progress=plain -t demo:dev .        # full, uncollapsed build log
docker build --no-cache -t demo:dev .              # rule out stale cache
docker build --target test -t demo:test .          # build only up to stage "test"
docker build -f docker/Dockerfile.prod -t demo:prod .
docker buildx du | tail -3                         # build cache usage
docker run --rm -i hadolint/hadolint < Dockerfile  # lint the Dockerfile
```

```
-:4 DL3008 warning: Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install <package>=<version>`
-:4 DL3009 info: Delete the apt-get lists after installing something
-:9 DL3025 warning: Use arguments JSON notation for CMD and ENTRYPOINT arguments
```

→ hadolint catches most of the rules in this section automatically; add it to CI next to Trivy.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** A minimal but correct Dockerfile:

```bash
mkdir -p ~/lab/first && cd ~/lab/first
echo 'print("hello from the container")' > app.py
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
USER 10001:10001
CMD ["python", "app.py"]
EOF
docker build -t first:dev . && docker run --rm first:dev
```

**Step 2 — Break it: the build cannot see a file.**

```bash
echo 'app.py' > .dockerignore
docker build -t first:dev .
```

```
ERROR: failed to solve: failed to compute cache key: failed to calculate checksum of ref …: "/app.py": not found
```

→ `"/app.py": not found` means the file is not in the **build context**: wrong directory,
wrong `-f`/context path, or excluded by `.dockerignore`.

**Step 3 — Fix it.** `rm .dockerignore`, rebuild, run. Then lint it with hadolint.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `failed to compute cache key … not found` | `cat .dockerignore`; check the context path at the end of `docker build` | [Containers playbook](26-playbook-containers-k8s.md) |
| `E: Unable to locate package` or `404 Not Found` from apt | `apt-get update` is cached in a separate layer; merge it into the install `RUN` | this section |
| `transferring context: 1.2GB` and slow builds | add a `.dockerignore` | "Layer caching and .dockerignore" |

**Why it matters for troubleshooting.** Most "the container is broken" tickets are really "the
image is built wrong": wrong user, wrong command, missing file, stale package index. Reading a
Dockerfile critically is a troubleshooting skill.

**Next step:** the instruction pairs people confuse most.

### COPY vs ADD and ARG vs ENV

**Level:** [L1 · Junior]

**Concept.** `COPY` copies files from the build context (or from another stage with `--from`).
`ADD` does the same plus two surprises: it auto-extracts local tar archives, and it can download
URLs and Git repositories. Surprises are bad in builds, so use `COPY` unless you want tar
extraction. `ARG` exists only while building and can be set with `--build-arg`; `ENV` is baked
into the image and present in every container. Both are **visible to anyone who has the image**:
`ARG` values used by a `RUN` step appear in `docker history`, `ENV` values in `docker inspect`.
Secrets go through BuildKit secret mounts instead.

| | `ARG` | `ENV` |
|---|---|---|
| Available during build | yes (from its declaration to the end of the stage) | yes |
| Available in the running container | no | yes |
| Override | `docker build --build-arg NAME=value` | `docker run -e NAME=value` |
| Leaks via | `docker history` | `docker inspect`, `/proc/1/environ` |
| Typical use | base image version, Git SHA for a label | `PYTHONUNBUFFERED=1`, `NODE_ENV=production`, `PATH` |

An `ARG` declared before `FROM` is only usable in `FROM` lines; redeclare it (`ARG NAME`) inside a
stage to use it there.

**Key terms:** *build context* (the files sent to the builder; `COPY` can only read from it), *`COPY --from`* (copy from another stage or image), *build argument* (`ARG`, build time only), *environment variable* (`ENV`, baked into the image and every container), *secret mount* (`RUN --mount=type=secret`, a credential that never lands in a layer).

**See it on a real system**

```bash
docker history --no-trunc IMAGE | grep -iE 'token|password|secret'
docker inspect CONTAINER --format '{{range .Config.Env}}{{println .}}{{end}}'
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: pass a token as a build argument.**

```bash
mkdir -p ~/lab/argleak && cd ~/lab/argleak
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM alpine:3.20
ARG API_TOKEN
RUN test -n "$API_TOKEN" && echo "downloading private package with token"
EOF
docker build --build-arg API_TOKEN=tok_live_abc123 -t argleak:1 .
docker history --no-trunc argleak:1 | grep -o 'API_TOKEN=[^ ]*'
```

```
API_TOKEN=tok_live_abc123
```

**Step 2 — Fix it: a BuildKit secret mount.** The secret is mounted at
`/run/secrets/ID` for that single `RUN` and never stored in a layer or in history.

```bash
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM alpine:3.20
RUN --mount=type=secret,id=api_token \
    API_TOKEN="$(cat /run/secrets/api_token)" \
    && test -n "$API_TOKEN" && echo "downloading private package with token"
EOF
printf 'tok_live_abc123' > api_token.txt
docker build --secret id=api_token,src=api_token.txt -t argleak:2 .
docker history --no-trunc argleak:2 | grep -c tok_live || echo "not in history"
rm -f api_token.txt
```

**Step 3 — Bonus: ADD surprises.** `ADD app.tar.gz /opt/` extracts the archive;
`COPY app.tar.gz /opt/` copies the file. If you must download, use
`ADD --checksum=sha256:HASH https://… /dst` so a changed upstream file fails the build instead of
silently changing your image.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Scanner or auditor finds a token in an image | `docker history --no-trunc IMAGE` | section 13 |
| Variable empty inside `RUN` although passed with `--build-arg` | `ARG` declared before `FROM` but not redeclared in the stage | this topic |
| App sees a different value than expected | `docker inspect` env vs Compose `environment:` precedence | section 9 |

**Why it matters for troubleshooting.** When a secret leaks, the image itself is the leak: every
copy in every registry and on every node. Rotate the secret; deleting the tag is not enough.

**Next step:** the instructions that decide how the container runs in production.

### USER, EXPOSE and HEALTHCHECK

**Level:** [L1 · Junior]

**Concept.**

**`USER`** — containers run as root by default, and without a user namespace that is the host's
UID 0 (limited by capabilities and seccomp, but still root on any file you bind-mount). Create a
dedicated user with a **fixed numeric UID** (for example 10001) and switch to it with
`USER 10001:10001`. Numeric matters twice: volume permissions are numeric on the host, and
Kubernetes `runAsNonRoot` refuses images whose user is a name it cannot verify. Copy application
code as root (the default) so the app user can read but not modify it; only directories the app
must write to are `chown`ed to it.

**`EXPOSE`** — documentation only. It does not publish a port and does not restrict anything:
containers on the same network can reach every port a process listens on, exposed or not. It is
used by `docker run -P` and, importantly for you, by Traefik to **guess** the backend port when
you do not set `loadbalancer.server.port`. A wrong guess shows up as a 502.

**`HEALTHCHECK`** — a command Docker runs inside the container on a schedule. Exit 0 = healthy,
1 = unhealthy. Status goes `starting` → `healthy` or `unhealthy`. Plain Docker does **not**
restart unhealthy containers; Swarm replaces unhealthy tasks, Compose uses health for
`depends_on: condition: service_healthy`, and Traefik's Docker provider leaves unhealthy
containers out of its load balancer.

| HEALTHCHECK option | Default | Meaning |
|---|---|---|
| `--interval` | 30s | Time between checks |
| `--timeout` | 30s | A check slower than this counts as failed |
| `--start-period` | 0s | Grace period: failures do not count while the app boots |
| `--start-interval` | 5s | Check interval during the start period (Engine 25+) |
| `--retries` | 3 | Consecutive failures before `unhealthy` |

**Key terms:** *numeric UID* (what the kernel checks; user names are only labels), *exposed port* (`EXPOSE`, metadata only), *published port* (`-p`, actually reachable from outside), *health status* (`starting`, then `healthy` or `unhealthy`), *start period* (grace time before failed checks count).

**See it on a real system**

```bash
docker image inspect IMAGE --format 'user={{.Config.User}} ports={{json .Config.ExposedPorts}}'
docker exec CONTAINER id
docker ps --format 'table {{.Names}}\t{{.Status}}'            # (healthy) / (unhealthy) / (health: starting)
docker inspect CONTAINER --format '{{json .State.Health}}' | jq '.Status, .FailingStreak, .Log[-1]'
```

```
"unhealthy"
5
{
  "Start": "2026-10-03T10:41:02.118Z",
  "End": "2026-10-03T10:41:02.164Z",
  "ExitCode": 127,
  "Output": "/bin/sh: 1: curl: not found\n"
}
```

→ Exit code 127 with `curl: not found`: the health check itself is broken, not the app. This is
the single most common unhealthy container on slim images.

**Hands-on lab (test VM only)**

**Step 1 — Break it: a health check that uses a missing tool.**

```bash
docker run -d --name hc --health-cmd 'curl -fsS http://127.0.0.1:8000/ || exit 1' \
  --health-interval 5s --health-retries 2 python:3.12-slim python -m http.server 8000
sleep 15; docker ps --filter name=hc --format '{{.Status}}'
docker inspect hc --format '{{(index .State.Health.Log 0).Output}}'
```

**Step 2 — Fix it.** Use a tool that exists in the image (Python's `urllib` in Python images,
`wget` in BusyBox-based Alpine images, `node -e "fetch(...)"` in Node 18+ images). Always check
first: `docker run --rm --entrypoint sh IMAGE -c 'command -v curl wget'`.

```bash
docker rm -f hc
docker run -d --name hc \
  --health-cmd 'python -c "import urllib.request; urllib.request.urlopen(\"http://127.0.0.1:8000/\", timeout=2)"' \
  --health-interval 5s --health-retries 2 python:3.12-slim python -m http.server 8000
sleep 10; docker ps --filter name=hc --format '{{.Status}}'
docker rm -f hc
```

**Step 3 — Break USER: a non-root app cannot write.** Run as UID 10001 and try to write to a
root-owned directory:

```bash
docker run --rm --user 10001:10001 alpine:3.20 sh -c 'id; touch /srv/test'
```

```
uid=10001 gid=10001 groups=10001
touch: /srv/test: Permission denied
```

→ Fix in the image with `RUN mkdir -p /srv/data && chown 10001:10001 /srv/data`, or mount a
volume there (section 8). Do not "fix" it by going back to root.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `(unhealthy)` with exit 127 in the health log | `docker inspect CONTAINER --format '{{json .State.Health}}'` | [Containers playbook](26-playbook-containers-k8s.md) |
| Traefik 502 though the app is up | the exposed port differs from the listening port; set `loadbalancer.server.port` | [Containers playbook](26-playbook-containers-k8s.md) |
| `Permission denied` writing files as non-root | `docker exec CONTAINER id`; `ls -ln` on the path | section 8 |
| Kubernetes: `container has runAsNonRoot and image has non-numeric user` | `USER 10001:10001` instead of `USER app` | [Kubernetes](31-learn-kubernetes.md) |

**Why it matters for troubleshooting.** Health status is the fastest signal you have, but only if
the check itself is trustworthy. And `EXPOSE` is the root cause of a whole family of Traefik 502s.

**Next step:** how the container's main process is chosen: ENTRYPOINT and CMD.

### ENTRYPOINT vs CMD, shell vs exec form

**Level:** [L1 · Junior]

**Concept.** The container's main process is `ENTRYPOINT` followed by `CMD`. `ENTRYPOINT` is the
fixed executable; `CMD` is the default that `docker run IMAGE ARGS` replaces. Each can be written
in **exec form** (`["gunicorn", "app:app"]`, a JSON array, run directly) or **shell form**
(`gunicorn app:app`, wrapped in `/bin/sh -c`). Shell form makes `/bin/sh` your PID 1, which
breaks signal handling (next topic). Use exec form for both.

| | No ENTRYPOINT | `ENTRYPOINT ["ep", "a"]` | `ENTRYPOINT ep a` (shell) |
|---|---|---|---|
| No CMD | error: nothing to run | `ep a` | `/bin/sh -c "ep a"` |
| `CMD ["c", "x"]` | `c x` | `ep a c x` | `/bin/sh -c "ep a"` (CMD ignored) |
| `CMD c x` (shell) | `/bin/sh -c "c x"` | `ep a /bin/sh -c "c x"` | `/bin/sh -c "ep a"` (CMD ignored) |

Override at runtime: `docker run IMAGE new args` replaces `CMD`;
`docker run --entrypoint sh IMAGE` replaces `ENTRYPOINT` (and clears `CMD`). In Compose:
`command:` and `entrypoint:`.

The **entrypoint script pattern** does one-time setup and then hands PID 1 to the real process:

```sh
#!/bin/sh
# docker-entrypoint.sh
set -eu
echo "starting $* (APP_ENV=${APP_ENV:-prod})"
# one-time setup here: render a config file, wait for a dependency, run migrations if asked
exec "$@"          # replace the shell with CMD, so the app becomes PID 1 and receives signals
```

```dockerfile
COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

**Key terms:** *exec form* (a JSON array, run directly without a shell), *shell form* (wrapped in `/bin/sh -c`), *entrypoint script* (one-time setup, then `exec "$@"`), *`--entrypoint`* (runtime override that also clears `CMD`).

**See it on a real system**

```bash
docker image inspect nginx:1.27 --format 'EP={{json .Config.Entrypoint}} CMD={{json .Config.Cmd}}'
docker inspect CONTAINER --format '{{.Path}} {{json .Args}}'    # what actually ran
docker top CONTAINER -o pid,comm,args                            # is PID 1 your app or a shell?
```

```
EP=["/docker-entrypoint.sh"] CMD=["nginx","-g","daemon off;"]
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: Windows line endings in the entrypoint.** Very common when someone edits
the script on Windows:

```bash
mkdir -p ~/lab/ep && cd ~/lab/ep
printf '#!/bin/sh\r\necho hello\r\nexec "$@"\r\n' > docker-entrypoint.sh
cat > Dockerfile <<'EOF'
FROM alpine:3.20
COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sleep", "5"]
EOF
docker build -q -t ep:1 . && docker run --rm ep:1
file docker-entrypoint.sh
```

```
exec /usr/local/bin/docker-entrypoint.sh: no such file or directory
docker-entrypoint.sh: POSIX shell script, ASCII text executable, with CRLF line terminators
```

→ "no such file or directory" for a file that clearly exists means the **interpreter** in the
shebang does not exist: here `/bin/sh\r`. The same message appears for a binary built against
glibc running on Alpine or `scratch` (section 4, multi-stage).

**Step 2 — Break it: not executable.** Replace `COPY --chmod=0755` with plain `COPY` and rebuild.
Because the ENTRYPOINT is a bare name looked up in `$PATH`, a file without the execute bit is
skipped during the lookup, so the error reads like a missing file:

```
docker: Error response from daemon: … exec: "docker-entrypoint.sh": executable file not found in $PATH: unknown.
```

→ Exit code 127. With an absolute path (`ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]`) the
same mistake reports `exec: "/usr/local/bin/docker-entrypoint.sh": permission denied` and exit
code 126. Either way, check the mode with `ls -l` inside the image.

**Step 3 — Fix it.** `sed -i 's/\r$//' docker-entrypoint.sh`, restore `--chmod=0755`, rebuild.
Prevent it in Git with a `.gitattributes` line `*.sh text eol=lf`. Clean up with
`cd ~ && rm -rf ~/lab/ep`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `exec … no such file or directory` | `file SCRIPT` (CRLF?), check the shebang, `ldd` the binary | [Containers playbook](26-playbook-containers-k8s.md) |
| Exit 126 / `permission denied` | `docker run --rm --entrypoint ls IMAGE -l /path/to/script` | [Containers playbook](26-playbook-containers-k8s.md) |
| Exit 127 / `executable file not found in $PATH` | `docker run --rm --entrypoint sh IMAGE -c 'echo $PATH; ls -l /usr/local/bin'` (missing, or present without the execute bit) | [Containers playbook](26-playbook-containers-k8s.md) |
| Container exits 0 immediately | the main process finished or daemonized (`daemon off;` missing) | section 5 |

**Why it matters for troubleshooting.** `docker run --rm -it --entrypoint sh IMAGE` is your
universal "let me look inside an image that will not start" move, and it works only once you
understand which part you are replacing.

**Next step:** why PID 1 is special, and why `docker stop` sometimes takes exactly 10 seconds.

### PID 1, signals and tini

**Level:** [L2 · Mid]

**Concept.** `docker stop` sends the image's stop signal (SIGTERM unless `STOPSIGNAL` says
otherwise), waits 10 seconds (`docker stop -t N`, Compose `stop_grace_period`), then sends
SIGKILL. Two kernel rules make PID 1 special inside a PID namespace:

1. **Signals with no handler are ignored by PID 1.** A normal process dies on SIGTERM by default; PID 1 only reacts if it installed a handler. Many runtimes (Python, Node) install none, so as PID 1 they ignore SIGTERM (the JVM is an exception: it handles SIGTERM itself and exits 143), wait out the 10 seconds and get SIGKILLed: exit 137, dropped connections, unflushed data.
2. **PID 1 must reap zombies.** Orphaned child processes are re-parented to PID 1; if PID 1 never calls `wait()`, they stay as zombies until the PID limit is hit.

Shell form makes `/bin/sh` PID 1: it ignores SIGTERM for the reason above and never forwards it to
your app. The fixes, from best to simplest: exec form plus an app that handles SIGTERM; a tiny
init (**tini**) as PID 1 that forwards signals and reaps zombies; or `docker run --init`
(Compose `init: true`), which injects Docker's bundled tini for you.

```
 docker stop ──SIGTERM──▶ PID 1
   shell form:  /bin/sh (PID 1, no handler: ignored) ──✗──▶ app never told ──10 s──▶ SIGKILL ─▶ exit 137
   exec form:   python  (PID 1, no handler: ignored) ───────────────────────10 s──▶ SIGKILL ─▶ exit 137
   with tini:   tini (PID 1) ──forwards SIGTERM──▶ python (PID 7, default action: exit) ─▶ exit 143, < 1 s
   app handler: gunicorn/node with a SIGTERM handler ─▶ graceful shutdown ─▶ exit 0, < 1 s
```

**Key terms:** PID 1, SIGTERM (15, exit 143), SIGKILL (9, exit 137), SIGQUIT (nginx graceful),
zombie (defunct), reaping, tini, `--init`, `STOPSIGNAL`, grace period.

**See it on a real system**

```bash
docker top CONTAINER -o pid,ppid,comm                          # is PID 1 sh, tini or the app?
time docker stop CONTAINER                                     # ~10.2 s = signal was ignored
docker inspect CONTAINER --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}'
ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/'                     # zombies on the host (all containers)
```

**Hands-on lab (test VM only)**

**Step 1 — Build it: three ways to start the same app.**

```bash
mkdir -p ~/lab/sig && cd ~/lab/sig
cat > start.sh <<'EOF'
#!/bin/sh
echo "starting web server"
python -m http.server 8000
EOF
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
COPY --chmod=0755 start.sh /start.sh
CMD ["/start.sh"]
EOF
docker build -q -t sig:shell .
```

**Step 2 — Break it: the shell is PID 1.**

```bash
docker run -d --name s1 sig:shell
docker top s1 -o pid,comm
time docker stop s1
docker inspect s1 --format '{{.State.ExitCode}}'
```

```
PID     COMMAND
50121   start.sh
50140   python
real    0m10.27s
137
```

→ Ten seconds and exit 137: the shell ignored SIGTERM, Docker gave up and sent SIGKILL.

**Step 3 — Half a fix: `exec` makes python PID 1.** Change the last line of `start.sh` to
`exec python -m http.server 8000`, rebuild as `sig:exec`, repeat. Still about 10 seconds and 137:
Python has no SIGTERM handler, and as PID 1 an unhandled SIGTERM is ignored.

**Step 4 — Fix it: an init as PID 1.**

```bash
docker run -d --name s3 --init sig:exec
docker top s3 -o pid,comm
time docker stop s3
docker inspect s3 --format '{{.State.ExitCode}}'
```

```
PID     COMMAND
50411   docker-init
50430   python
real    0m0.41s
143
```

→ `docker-init` (tini) forwarded SIGTERM; python, no longer PID 1, took the default action and
exited. 143 = 128 + 15 (SIGTERM). For images, bake it in with
`ENTRYPOINT ["tini", "--"]` (Debian/Ubuntu package `tini`, Alpine package `tini`), or keep
`init: true` in Compose. Clean up with `docker rm -f s1 s3; cd ~ && rm -rf ~/lab/sig`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Every `docker stop` or redeploy takes exactly ~10 s | `docker top CONTAINER -o pid,comm` (PID 1 is a shell?) | [Containers playbook](26-playbook-containers-k8s.md) |
| Exit 137 on every stop, `OOMKilled=false` | signal ignored; add tini or a handler | this topic |
| Dropped requests during each deploy | app killed instead of draining; handle SIGTERM, raise the grace period | [Site-down playbook](25-playbook-site-down.md) |
| Hundreds of `<defunct>` processes, then `can't fork` | PID 1 does not reap; add `--init` | section 2 (cgroups) |

**Why it matters for troubleshooting.** Exit 137 has two causes, the OOM killer and the stop
timeout, and they need opposite fixes. `docker inspect --format '{{.State.OOMKilled}}'` tells them
apart. The same rules apply to Kubernetes pods (`terminationGracePeriodSeconds`).

**Next step:** make builds fast and images small: caching and `.dockerignore`.

### Layer caching and .dockerignore

**Level:** [L1 · Junior]

**Concept.** BuildKit walks the Dockerfile and, for each instruction, checks for a cached result.
`RUN` is cached by its command text; `COPY`/`ADD` by the checksums of the copied files. **The
first miss invalidates every later instruction.** So order instructions from least to most
frequently changing: base image and OS packages, then dependency manifests and dependency
install, then your source code last. The `.dockerignore` file keeps junk and secrets out of the
build context, which speeds up builds and stops `COPY . .` from copying `.git`, `.env` or
`node_modules` into the image.

```
 bad order                               good order
 FROM python:3.12-slim                   FROM python:3.12-slim
 COPY . .              ← any edit        COPY requirements.txt .        ← changes rarely
 RUN pip install -r …  ← reinstalls      RUN pip install -r …           ← cached
                         every time      COPY . .                       ← only this reruns
```

Rules for package managers: put `apt-get update` and `apt-get install` in **one** `RUN` (a
separately cached `update` layer goes stale and installs fail with 404), use
`--no-install-recommends`, and remove `/var/lib/apt/lists/*` in the same `RUN`, because deleting
files in a later layer does not shrink the image.

A starting `.dockerignore` for Python and Node projects:

```
.git
.gitignore
.env
.env.*
**/__pycache__
**/*.pyc
.venv
node_modules
npm-debug.log
dist
coverage
*.log
compose*.yaml
Dockerfile*
```

**Key terms:** *build cache* (stored results of earlier instructions), *cache miss* (the first changed instruction; everything after it reruns), *build context* (what `docker build .` sends to the builder), *`.dockerignore`* (patterns kept out of the context).

**See it on a real system**

```bash
docker build --progress=plain -t web:dev . 2>&1 | grep -E -B1 'CACHED|transferring context'
```

```
#5 [internal] load build context
#5 transferring context: 2.41kB done
--
#7 [2/5] WORKDIR /app
#7 CACHED
--
#8 [3/5] COPY requirements.txt .
#8 CACHED
--
#9 [4/5] RUN pip install -r requirements.txt
#9 CACHED
```

→ In plain progress mode `CACHED` is printed on its own line under the step it belongs to, so
`-B1` shows the step name with it.

**Hands-on lab (test VM only)**

**Step 1 — Break it: bad order.**

```bash
mkdir -p ~/lab/cache && cd ~/lab/cache
printf 'flask==3.0.3\n' > requirements.txt
echo 'print("v1")' > app.py
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
EOF
docker build -q -t cache:bad . >/dev/null
echo '# tiny change' >> app.py
time docker build --progress=plain -t cache:bad . 2>&1 | grep -c 'pip install'
```

→ A one-line change in `app.py` reruns `pip install` (several seconds, network needed).

**Step 2 — Fix it: dependencies first.**

```bash
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
EOF
docker build -q -t cache:good . >/dev/null
echo '# another change' >> app.py
time docker build -t cache:good .        # pip step shows CACHED, build takes about a second
```

**Step 3 — Break it: secrets in the context.**

```bash
echo 'DB_PASSWORD=hunter2' > .env
docker build -q -t cache:good . >/dev/null && docker run --rm cache:good cat /app/.env
printf '.env\n.git\n' > .dockerignore
docker build -q -t cache:good . >/dev/null && docker run --rm cache:good cat /app/.env
cd ~ && rm -rf ~/lab/cache
```

→ The first run prints the password (it is now in a layer); after `.dockerignore`, `cat` fails.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Every build reinstalls dependencies | `docker build --progress=plain` and find the first non-CACHED step | this topic |
| `.env`, `.git` or keys inside the image | `docker run --rm --entrypoint ls IMAGE -la /app` | section 13 |
| Huge build context, slow CI | the `transferring context` line | this topic |
| apt `404 Not Found` in a cached build | merge `apt-get update` into the install `RUN` or build with `--no-cache` | this topic |

**Why it matters for troubleshooting.** A slow pipeline is an incident multiplier: when a hotfix
build takes 12 minutes instead of 40 seconds, every outage lasts 11 minutes longer.

**Next step:** separate build tools from the runtime with multi-stage builds.

### Multi-stage builds and BuildKit mounts

**Level:** [L2 · Mid]

**Concept.** A multi-stage Dockerfile has several `FROM` lines. Early stages hold compilers,
dev dependencies and test tools; the final stage copies only the artifacts it needs with
`COPY --from=STAGE`. The result is small, with less attack surface, and the build tools never
reach production. BuildKit only builds the stages the chosen target needs, so a `test` stage can
live in the same file and run only when CI asks for `--target test`.

BuildKit **mounts** for `RUN` make builds faster without bloating layers:

| Mount | Example | Use |
|---|---|---|
| `type=cache` | `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt` | Package manager caches survive between builds but never enter the image |
| `type=secret` | `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci` | Credentials for private registries during build only |
| `type=ssh` | `RUN --mount=type=ssh git clone git@gitlab.example.com:shop/lib.git` | Use the build host's SSH agent (`docker build --ssh default`) |
| `type=bind` | `RUN --mount=type=bind,source=go.mod,target=go.mod go mod download` | Read files without a `COPY` layer |

Typical sizes for the same small web service:

| Image | Typical size | Contains |
|---|---|---|
| `python:3.12` (full) | about 1 GB | compilers, headers, many tools |
| `python:3.12-slim` single stage | about 150–200 MB | runtime plus whatever you installed |
| multi-stage on `-slim` with a venv | about 130–160 MB | runtime and your dependencies only |
| Go static binary on `scratch` | about 5–10 MB | one binary; no shell, no tools |

**Key terms:** *stage* (one `FROM … AS NAME` block), *`--target`* (build only up to a named stage), *`COPY --from=STAGE`* (take artifacts from an earlier stage), *cache, secret and ssh mounts* (BuildKit `RUN --mount` types that never enter a layer), *`scratch`* (the empty base image).

**See it on a real system**

```bash
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | sort
docker build --target test -t web:test .     # run only up to the test stage
docker buildx du --verbose | head -20        # what the build cache holds (cache mounts included)
```

**Hands-on lab (test VM only)**

**Step 1 — Build it: a Go service on `scratch`.**

```bash
mkdir -p ~/lab/ms && cd ~/lab/ms
cat > main.go <<'EOF'
package main

import (
	"fmt"
	"net"
	"net/http"
)

func main() {
	addrs, _ := net.LookupHost("localhost") // forces Go's resolver code into the binary
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { fmt.Fprintln(w, "hello", addrs) })
	http.ListenAndServe(":8080", nil)
}
EOF
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM golang:1.23 AS build
WORKDIR /src
COPY main.go .
RUN go build -o /out/hello main.go

FROM scratch
COPY --from=build /out/hello /hello
USER 65534:65534
ENTRYPOINT ["/hello"]
EOF
docker build -q -t ms:1 . && docker run --rm ms:1
```

**Step 2 — Break it.** The run fails:

```
exec /hello: no such file or directory
```

→ The `golang` image builds with cgo enabled, so a program using `net` is dynamically linked
against glibc, and `scratch` has no dynamic loader. Same message as the CRLF case: the missing
file is the *interpreter* (`/lib64/ld-linux-x86-64.so.2`), not `/hello`. Confirm with
`docker run --rm -v "$PWD":/s -w /s golang:1.23 sh -c 'go build -o /tmp/h main.go && ldd /tmp/h'`,
which lists `libc.so.6` and the loader.

**Step 3 — Fix it.** Build a static binary:

```bash
sed -i 's#RUN go build#RUN CGO_ENABLED=0 go build#' Dockerfile
docker build -q -t ms:2 . && docker run -d --name ms -p 127.0.0.1:18080:8080 ms:2
curl -s http://127.0.0.1:18080/
docker images ms --format '{{.Tag}} {{.Size}}'
docker exec ms sh                      # fails: there is no shell in scratch
docker rm -f ms && cd ~ && rm -rf ~/lab/ms
```

→ About 7 MB, and no shell to exec into. Debug such containers from the host with `nsenter` or
`netshoot` (section 15).

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `exec /BINARY: no such file or directory` on `scratch`/Alpine | `ldd BINARY` in the build stage; build static or use a glibc base | this topic |
| `COPY --from=build` fails: `not found` | the artifact path in the build stage is different; `docker build --target build` and look | this topic |
| No shell to debug the container | `nsenter -t PID -n …` or `docker run --net container:NAME nicolaka/netshoot` | section 15 |

**Why it matters for troubleshooting.** Minimal images are the right production choice and the
reason you need host-side debugging skills. They also shrink the scanner report (section 11):
fewer packages, fewer CVEs to triage.

**Next step:** put all of it together in two real services.

### Worked example: Python service

**Level:** [L1 · Junior]

**Concept.** A Flask app served by Gunicorn, the shape of many of your future Dokploy apps. Create these
files in `~/lab/shop-web` on the test VM. Project layout:

```
shop-web/
├── app.py
├── gunicorn.conf.py
├── requirements.txt
├── .dockerignore
└── Dockerfile
```

`app.py`:

```python
import os
from flask import Flask

app = Flask(__name__)


@app.get("/healthz")
def healthz():
    return "ok\n"


@app.get("/")
def index():
    return f"hello from {os.uname().nodename}\n"
```

`requirements.txt` (pin exact versions so builds are reproducible):

```
flask==3.0.3
gunicorn==23.0.0
```

`gunicorn.conf.py`:

```python
bind = "0.0.0.0:8000"        # 0.0.0.0, not 127.0.0.1: traffic arrives on the container's eth0
workers = 2
timeout = 30                 # a request slower than this kills the worker -> 502 at the proxy
graceful_timeout = 20        # time to finish requests after SIGTERM
worker_tmp_dir = "/dev/shm"  # heartbeat files in RAM: works with a read-only root filesystem
accesslog = "-"              # access log to stdout -> docker logs
errorlog = "-"
```

`Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1

# ---------- stage 1: build a virtualenv with the dependencies ----------
FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /src
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# ---------- stage 2: runtime ----------
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app.py gunicorn.conf.py ./
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.source="https://gitlab.example.com/shop/shop-web"
ENTRYPOINT ["tini", "--"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

**Why each choice:**

- **Two stages** — pip, its cache and any build tools stay in `builder`; only the finished `/opt/venv` is copied.
- **Cache mount for pip** — rebuilding after a dependency change downloads only what changed, and the cache never enters a layer.
- **`PYTHONUNBUFFERED=1`** — log lines reach `docker logs` immediately instead of sitting in a buffer when the container dies.
- **Fixed UID 10001, code owned by root** — the app can read its code but not modify it; volume permissions are predictable; Kubernetes `runAsNonRoot` can verify it.
- **Python-based health check** — no curl needed in a slim image.
- **`ARG GIT_SHA` near the end** — a new SHA every build would otherwise invalidate the cache of everything after it.
- **tini as PID 1, Gunicorn in exec form** — `docker stop` sends SIGTERM, tini forwards it, Gunicorn drains for up to 20 s.

**Key terms:** *WSGI server* (Gunicorn runs the Python app in worker processes), *worker timeout*
(a request slower than `timeout` kills the worker), *virtualenv copy* (the finished dependency set
moved from the builder stage), *OCI labels* (`org.opencontainers.image.revision` records the
commit inside the image).

Build, run and verify:

```bash
cd ~/lab/shop-web
docker build -t shop-web:dev --build-arg GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo dev)" .
docker run -d --name shop-web -p 127.0.0.1:18000:8000 --read-only --tmpfs /tmp shop-web:dev
sleep 2; curl -s http://127.0.0.1:18000/
sleep 20; docker ps --filter name=shop-web --format '{{.Names}} {{.Status}}'
docker exec shop-web id
docker logs --tail 3 shop-web
time docker stop shop-web
```

```
hello from 6a1d9e0c4b2f
shop-web Up 22 seconds (healthy)
uid=10001(app) gid=10001(app) groups=10001(app)
[2026-10-03 10:52:11 +0000] [9] [INFO] Booting worker with pid: 9
172.17.0.1 - - [03/Oct/2026:10:52:13 +0000] "GET / HTTP/1.1" 200 24 "-" "curl/8.5.0"
127.0.0.1 - - [03/Oct/2026:10:52:16 +0000] "GET /healthz HTTP/1.1" 200 3 "-" "Python-urllib/3.12"
real    0m0.62s
```

→ During `--start-period`, Engine 25+ probes every `--start-interval` (default 5 s), so the
container turns `(healthy)` about 5 s after boot and the probe shows up in the access log; after
that it probes every `--interval` (30 s). Older engines wait a full `--interval` before the first
probe, so the status reads `(health: starting)` for the first 30 s.

**Break it on purpose (test VM only).** Change `bind` to `"127.0.0.1:8000"`, rebuild, run, and
curl again:

```
curl: (56) Recv failure: Connection reset by peer
```

→ The port is published and the container is "Up", but Gunicorn listens only on the container's
loopback, so Docker's forwarded connection to the container's eth0 finds nothing. From another
machine the same mistake shows as `Connection refused`. Confirm with
`sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' shop-web)" -n ss -ltn` and fix by binding
`0.0.0.0`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `curl: (56) Recv failure: Connection reset by peer` on the published port | `sudo nsenter -t PID -n ss -ltn` (listening on 127.0.0.1?) | [Containers playbook](26-playbook-containers-k8s.md) |
| `[CRITICAL] WORKER TIMEOUT` in `docker logs`, 502 at the proxy | `docker logs --since 10m CONTAINER | grep -i timeout` | [Site-down playbook](25-playbook-site-down.md) |
| `(unhealthy)` while the app answers on the host port | `docker inspect CONTAINER --format '{{json .State.Health}}'` (wrong URL or port in the check) | this module, section 4 |
| `Read-only file system` at start with `--read-only` | find the path in the error; add a `tmpfs` or volume for it | section 13 |
| `docker stop` takes 10 s every time | `docker top CONTAINER -o pid,comm` (is PID 1 a shell instead of tini?) | this module, section 4 |

**Why it matters for troubleshooting.** Each line of this Dockerfile removes one incident class:
the bind address (Traefik 502), the unbuffered logs (empty `docker logs` after a crash), tini (slow
stops and lost requests on every deploy), the numeric UID (volume permission errors), the health
check (traffic sent to a container that is still booting). When a Python app misbehaves in a
container, compare its Dockerfile with this one first.

**Next step:** the same discipline for Node.js, plus a test stage that CI runs and production never
ships.

### Worked example: Node.js service

**Level:** [L2 · Mid]

**Concept.** An Express API with a test stage that CI runs and production never ships. Create these files
in `~/lab/shop-api`. Layout:

```
shop-api/
├── server.js
├── package.json
├── package-lock.json
├── test/health.test.js
├── .dockerignore
└── Dockerfile
```

`server.js`:

```js
const express = require("express");

const app = express();
app.get("/healthz", (req, res) => res.send("ok\n"));
app.get("/", (req, res) => res.send("hello from node\n"));

const server = app.listen(3000, "0.0.0.0", () => console.log("listening on :3000"));

// Node installs no SIGTERM handler by default; as PID 1 it would ignore docker stop.
process.on("SIGTERM", () => {
  console.log("SIGTERM received, draining connections");
  server.close(() => process.exit(0));
});
```

`package.json`:

```json
{
  "name": "shop-api",
  "version": "1.0.0",
  "private": true,
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "node --test"
  },
  "dependencies": {
    "express": "^4.21.0"
  }
}
```

`test/health.test.js`:

```js
const test = require("node:test");
const assert = require("node:assert");

test("sanity", () => {
  assert.strictEqual(1 + 1, 2);
});
```

Generate the lockfile without installing Node on the host (`npm ci` refuses to run without it):

```bash
docker run --rm -u "$(id -u):$(id -g)" -e npm_config_cache=/tmp/.npm \
  -v "$PWD":/app -w /app node:22-bookworm-slim npm install --package-lock-only
```

`Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS base
WORKDIR /app
ENV NODE_ENV=production

# ---------- production dependencies only ----------
FROM base AS deps
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev

# ---------- test stage: built only with --target test ----------
FROM base AS test
ENV NODE_ENV=development
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm test

# ---------- runtime ----------
FROM base AS runtime
COPY --from=deps /app/node_modules ./node_modules
COPY package.json server.js ./
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"]
CMD ["node", "server.js"]
```

**Why each choice:**

- **`npm ci`, not `npm install`** — installs exactly what the lockfile says and fails if `package.json` and the lockfile disagree, so CI and production get identical trees.
- **`--omit=dev` in `deps`** — test frameworks and linters never reach production.
- **`test` stage** — `docker build --target test .` in CI runs the tests in the same environment as production; the default build (last stage) skips it entirely.
- **`USER node`** — the official image ships user `node` with UID 1000. Use `USER 1000:1000` if Kubernetes `runAsNonRoot` must verify it.
- **`CMD ["node", "server.js"]`, not `npm start`** — npm adds a process in front of node and historically did not forward signals reliably; run node directly.
- **SIGTERM handler in code** — Node as PID 1 then shuts down gracefully. Still add `--init` (Compose `init: true`) if the app spawns child processes, so zombies are reaped.

**Key terms:** *`npm ci`* (installs exactly the lockfile), *`--omit=dev`* (production dependencies
only), *test stage* (built only with `--target test`), *graceful shutdown* (finish in-flight
requests after SIGTERM, then exit).

Build, test and run:

```bash
cd ~/lab/shop-api
docker build --target test -t shop-api:test .        # CI step: fails the pipeline if tests fail
docker build -t shop-api:dev .                       # production image
docker run -d --name shop-api -p 127.0.0.1:13000:3000 --init shop-api:dev
curl -s http://127.0.0.1:13000/
time docker stop shop-api && docker logs shop-api | tail -2
docker rm shop-api
```

```
hello from node
real    0m0.38s
listening on :3000
SIGTERM received, draining connections
```

**Break it on purpose (test VM only).** Add a dependency to `package.json` by hand without
regenerating the lockfile, then build:

```
npm error `npm ci` can only install packages when your package.json and package-lock.json or npm-shrinkwrap.json are in sync. Please update your lock file with `npm install` before continuing.
```

→ Fix by regenerating the lockfile (command above) and committing both files together.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `npm ci` can only install packages when package.json and package-lock.json are in sync | regenerate the lockfile, commit both files | this topic |
| CI passes, production image crashes with `Cannot find module` | `docker run --rm --entrypoint sh IMAGE -c 'ls node_modules | head'` (dev dependency used at runtime?) | [Containers playbook](26-playbook-containers-k8s.md) |
| Deploys drop in-flight requests | `time docker stop CONTAINER` and check for the SIGTERM log line | this module, section 4 |
| Exit code 137 under load, no error in the log | `docker inspect -f '{{.State.OOMKilled}}' CONTAINER` (Node heap above the container limit?) | section 10 |

**Why it matters for troubleshooting.** The test stage turns "it worked on my machine" into a
failed pipeline instead of a failed deploy, and the SIGTERM handler is the difference between a
clean rolling update in Dokploy and a burst of 502s during every release.

**Next step:** run, inspect and stop containers with intent: the lifecycle and the run flags that
matter.

---

## 5. Container lifecycle

> 📚 **Study path:** 1) Note: [Docker reference](14-docker-containers.md) as a 10-minute refresher, then this section · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Port Mapping, Volumes and Bind Mounts, Inspect and Logs) ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 3) Video: *Learn Docker in 2 Hours - A Full Tutorial (2025)*, docker run part ([YouTube](https://www.youtube.com/watch?v=zJ6WbK9zFpI)) · 4) Practice: KodeKloud Docker Playground ([playground](https://kodekloud.com/playgrounds/playground-docker)).

### States and the run flags that matter

**Level:** [L1 · Junior]

**Concept.** A container moves through a few states. `docker run` is `docker create` plus
`docker start` (plus attach). The container is `running` exactly as long as its **main process**
(PID 1) runs; when that process exits, the container exits, whatever else is still running
inside. A restart policy may bring it back.

```
            docker create           docker start              PID 1 exits / docker stop
  IMAGE ─────────────────▶ created ─────────────▶ running ───────────────────────────▶ exited
                                                   │   ▲                                   │
                                      docker pause │   │ docker unpause      restart policy │
                                                   ▼   │                                   ▼
                                                  paused              running ◀── restarting
  docker rm: removes created/exited containers;  docker rm -f: SIGKILL, then remove
```

| Flag | Example | Why it matters |
|---|---|---|
| `-d` | `docker run -d …` | Run in the background; otherwise your terminal is attached |
| `--name` | `--name shop-web` | Stable name for scripts, and the DNS name on user-defined networks |
| `--rm` | `docker run --rm …` | Removes the container **and its logs** on exit: for one-off tools only |
| `-p` | `-p 127.0.0.1:18000:8000` | Publish a port; the bind address decides who can reach it |
| `-e`, `--env-file` | `--env-file ./web.env` | Configuration |
| `-v`, `--mount` | `--mount type=volume,src=pgdata,dst=/var/lib/postgresql/data` | Data that must outlive the container |
| `--network` | `--network shop` | Join a user-defined network (name resolution between containers) |
| `--restart` | `--restart unless-stopped` | Survive crashes and reboots |
| `-m`, `--cpus`, `--pids-limit` | `-m 512m --cpus 1` | Budgets (section 10) |
| `--user` | `--user 10001:10001` | Override the image's user |
| `--read-only`, `--tmpfs` | `--read-only --tmpfs /tmp` | Immutable root filesystem (section 13) |
| `--init` | `--init` | tini as PID 1 (section 4) |
| `--log-opt` | `--log-opt max-size=50m` | Per-container log rotation (section 6) |
| `--add-host` | `--add-host host.docker.internal:host-gateway` | Reach a service on the Docker host itself |
| `--entrypoint` | `--entrypoint sh` | Debug an image that will not start |
| `-it` | `docker run -it alpine:3.20 sh` | Interactive terminal |

**Key terms:** *created, running, paused, restarting, exited, dead* (the container states), *exit code* (PID 1's exit status; 128+N means killed by signal N, so 137 = SIGKILL), *`--rm`* (remove the container when it exits), *`--init`* (a tiny init as PID 1 that forwards signals and reaps zombies).

**See it on a real system**

```bash
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker inspect CONTAINER --format '{{.State.Status}} exit={{.State.ExitCode}} restarts={{.RestartCount}} started={{.State.StartedAt}}'
docker ps -a --filter status=exited --filter status=restarting
```

```
NAMES       STATUS                          PORTS
shop-web    Up 2 hours (healthy)            127.0.0.1:18000->8000/tcp
worker      Restarting (1) 12 seconds ago
migrate     Exited (0) 2 hours ago
```

→ `Exited (0)` is a finished one-shot job, fine for `migrate`, a bug for a web server.
`Restarting (1)` is a crash loop with exit code 1: read its logs.

**Hands-on lab (test VM only)**

**Step 1 — Break it: containers that exit immediately.**

```bash
docker run -d --name u1 ubuntu:24.04                 # bash with no terminal: reads EOF, exits 0
docker run -d --name u2 nginx:1.27 nginx             # nginx daemonizes; PID 1 exits, container exits 0
sleep 2; docker ps -a --filter name=u --format '{{.Names}} {{.Status}}'
```

```
u2 Exited (0) 2 seconds ago
u1 Exited (0) 3 seconds ago
```

→ The main process must stay in the **foreground**. The nginx image's default CMD adds
`-g 'daemon off;'` for exactly this reason; overriding CMD dropped it.

**Step 2 — Break it: `--rm` destroys the evidence.**

```bash
docker run -d --rm --name crash alpine:3.20 sh -c 'sleep 2; echo "fatal: config missing" >&2; exit 3'
sleep 4; docker logs crash
```

```
Error response from daemon: No such container: crash
```

**Step 3 — Fix it.** Foreground process (`docker run -d --name u2 nginx:1.27 nginx -g 'daemon off;'`),
no `--rm` on anything you may need to debug, and a restart policy for services. Clean up with
`docker rm -f u1 u2`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| `Exited (0)` right after start | `docker logs CONTAINER`; is the process daemonizing? | [Containers playbook](26-playbook-containers-k8s.md) |
| `Restarting (N)` loop | `docker logs --tail 50 CONTAINER`, then `docker run --rm -it --entrypoint sh IMAGE` | [Containers playbook](26-playbook-containers-k8s.md) |
| `Exited (137)` | `docker inspect CONTAINER --format '{{.State.OOMKilled}}'` | section 10 |
| `Exited (125)` | Docker itself refused the flags; read the error printed by `docker run` | [Docker reference](14-docker-containers.md) |

**Why it matters for troubleshooting.** The status column plus the exit code is your first triage
signal; the exit code table in [Docker reference](14-docker-containers.md) decodes it.

**Next step:** the commands you use to look inside running and dead containers.

### exec, logs, inspect, stats, top, cp, events, diff

**Level:** [L1 · Junior]

**Concept.** Eight commands cover nearly every look into a container. Learn what each one answers.

| Command | Answers | Works on a stopped container? |
|---|---|---|
| `docker logs` | What did the app print (stdout and stderr)? | yes |
| `docker inspect` | How was it configured, and what is its state? | yes |
| `docker exec` | Let me run a command inside it | no (must be running) |
| `docker top` | Which processes run inside, with host PIDs? | no |
| `docker stats` | Live CPU, memory, network, block I/O, PIDs | no |
| `docker cp` | Copy files in or out | yes |
| `docker diff` | Which files changed versus the image? | yes |
| `docker events` | What happened (start, die, oom, kill, health) and when? | daemon-wide stream |

Useful variants:

```bash
docker logs -f --tail 100 CONTAINER          # follow the last 100 lines
docker logs --since 10m -t CONTAINER         # last 10 minutes, with timestamps
docker logs CONTAINER 2>&1 | grep -i error   # stderr is kept separate: merge it before grep
docker exec -it CONTAINER sh                 # shell (bash only if the image has it)
docker exec -u 0 -it CONTAINER sh            # root shell in a non-root container (debugging)
docker exec CONTAINER env                    # the environment the app really sees
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.PIDs}}'
docker top CONTAINER -o pid,ppid,user,etime,args
docker cp CONTAINER:/app/logs/error.log ./   # works on exited containers too
docker events --since 30m --filter type=container --filter event=die --filter event=oom
```

`docker inspect` format cookbook:

| Question | Command |
|---|---|
| IP per network | `docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}' C` |
| Exit code, OOM, error | `docker inspect -f '{{.State.ExitCode}} {{.State.OOMKilled}} {{.State.Error}}' C` |
| Restart policy and count | `docker inspect -f '{{.HostConfig.RestartPolicy.Name}} {{.RestartCount}}' C` |
| Mounts | `docker inspect -f '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}' C` |
| Environment | `docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' C` |
| Labels (Traefik routers) | `docker inspect -f '{{json .Config.Labels}}' C` |
| Log file path | `docker inspect -f '{{.LogPath}}' C` |
| Compose project and service | `docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}/{{index .Config.Labels "com.docker.compose.service"}}' C` |

**Key terms:** *`docker exec`* (a new process inside the container's existing namespaces), *`docker logs`* (what PID 1 wrote to stdout and stderr, read back through the logging driver), *`docker inspect`* (the full JSON config and state), *`docker events`* (the daemon's event stream), *`docker diff`* (A/C/D changes in the writable layer).

**See it on a real system**

```bash
docker stats --no-stream
docker events --since 1h --filter type=container
```

```
CONTAINER ID   NAME       CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS
3f9c2a1b7d4e   shop-web   0.12%     71.3MiB / 512MiB      13.93%    1.21MB / 3.4MB    0B / 8.19kB       5
9c2d11ab4e77   worker     98.70%    498.2MiB / 512MiB     97.30%    88kB / 41kB       12.3MB / 0B       9
2026-10-03T10:58:01.204417332Z container oom 9c2d11ab4e77… (image=worker:2.1, name=worker)
2026-10-03T10:58:01.391108776Z container die 9c2d11ab4e77… (exitCode=137, image=worker:2.1, name=worker)
2026-10-03T10:58:02.513925140Z container start 9c2d11ab4e77… (image=worker:2.1, name=worker)
```

→ `worker` sits at 97% of its memory limit; the event stream shows the story: `oom`, `die`
with 137, `start` (restart policy). `docker events` keeps only a short in-memory history and
nothing across daemon restarts, so for long-term history ship events or logs elsewhere
([Observability](32-learn-performance-observability.md)).

**Hands-on lab (test VM only): crash forensics**

**Step 1 — Build a container that crashes and leaves evidence.**

```bash
docker run -d --name crashy alpine:3.20 sh -c \
  'echo "loading config"; echo "trace: db timeout after 5s" > /tmp/crash.trace; sleep 3; echo "FATAL: cannot connect to db:5432" >&2; exit 2'
sleep 5
```

**Step 2 — Investigate with only the eight commands.** Status, logs with timestamps, state,
changed files, then copy the evidence out of the dead container:

```bash
docker ps -a --filter name=crashy --format '{{.Status}}'
docker logs -t crashy
docker inspect crashy --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} finished={{.State.FinishedAt}}'
docker diff crashy
docker cp crashy:/tmp/crash.trace . && cat crash.trace
```

```
Exited (2) 3 seconds ago
2026-10-03T11:02:10.118Z loading config
2026-10-03T11:02:13.125Z FATAL: cannot connect to db:5432
exit=2 oom=false finished=2026-10-03T11:02:13.127Z
C /tmp
A /tmp/crash.trace
trace: db timeout after 5s
```

**Step 3 — Fix and clean up.** Here the "fix" is the dependency (section 9, `depends_on` with
health checks). `docker rm crashy; rm crash.trace`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Error response from daemon: container … is not running` on exec | `docker logs` and `docker inspect` instead; or `docker run --rm -it --entrypoint sh IMAGE` | [Containers playbook](26-playbook-containers-k8s.md) |
| `docker logs` is empty but the app is busy | the app logs to a file inside; `docker exec CONTAINER ls -l /var/log` | section 6 |
| `grep` misses errors in `docker logs` output | the errors are on stderr; add `2>&1` | this topic |

**Why it matters for troubleshooting.** These commands are the container equivalents of
`journalctl`, `systemctl show`, `ps`, `top` and `find -newer`. Same questions, new tools.

**Next step:** where those logs physically go, and how to stop them filling the disk.

---

## 6. Logging

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine: Logging Driver ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page)) · 2) KodeKloud: LFCS lesson *Locate and Analyze System Log Files* for the journald side ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 3) Note: this section, then [Logs & journal](06-logs-journal.md) · 4) Practice: the log-flood lab below on your test VM.

### Logging drivers and where logs live

**Level:** [L1 · Junior]

**Concept.** Everything a container's main process writes to **stdout and stderr** is captured by
dockerd and handed to a **logging driver**. The default driver, `json-file`, appends each line as
JSON to `/var/lib/docker/containers/ID/ID-json.log`, and by default it **never rotates**. That
single default is behind a large share of "Docker filled the disk" incidents. Apps that write log
files inside the container bypass all of this: `docker logs` stays empty and the writable layer
grows instead.

| Driver | Where logs go | `docker logs` works | Notes |
|---|---|---|---|
| `json-file` | `/var/lib/docker/containers/ID/ID-json.log` | yes | Default; no rotation unless `max-size`/`max-file` are set |
| `local` | compressed files under the container directory | yes | Rotates by default (5 files of 20 MB); good default for single hosts |
| `journald` | the systemd journal | yes | One retention policy for host and containers; query with `journalctl` |
| `syslog`, `gelf`, `fluentd`, `awslogs` | remote collectors | via the dual-logging cache | Remote outage can block or drop logs |
| `none` | nowhere | no | Only for truly noisy, useless output |

```
 app ─stdout/stderr─▶ containerd-shim ─▶ dockerd ─▶ log driver ─▶ json-file on disk ─▶ docker logs
                                                              └─▶ journald / syslog / collector
```

**Key terms:** log driver, `log-opts`, `LogPath`, `max-size`, `max-file`, dual logging,
`mode: non-blocking`.

**See it on a real system**

```bash
docker info --format '{{.LoggingDriver}}'
docker inspect CONTAINER --format '{{.HostConfig.LogConfig}}'
sudo ls -lh "$(docker inspect -f '{{.LogPath}}' CONTAINER)"
sudo head -c 230 "$(docker inspect -f '{{.LogPath}}' CONTAINER)"; echo
sudo sh -c 'du -h /var/lib/docker/containers/*/*-json.log' | sort -h | tail -5
```

```
json-file
{json-file map[]}
-rw-r----- 1 root root 7.9G Oct  3 11:10 /var/lib/docker/containers/9c2d…/9c2d…-json.log
{"log":"2026-10-03 11:10:01 INFO processed batch 88123\n","stream":"stdout","time":"2026-10-03T11:10:01.204417332Z"}
{"log":"2026-10-03 11:10:01 WARN retrying upstream\n","stream":"stderr","time":"2026-10-03T11:10:01.391108776Z"}
12M     /var/lib/docker/containers/3f9c…/3f9c…-json.log
7.9G    /var/lib/docker/containers/9c2d…/9c2d…-json.log
```

→ `map[]` means **no log options**: this container's log will grow until the disk is full. The
7.9 GB file belongs to `worker`. Note that `docker system df` does not count these files.

**Hands-on lab (test VM only)**

**Step 1 — Break it: a log flood.**

```bash
docker run -d --name noisy alpine:3.20 sh -c 'while :; do echo "$(date) noisy line with some padding to grow faster"; done'
sleep 20; sudo ls -lh "$(docker inspect -f '{{.LogPath}}' noisy)"
docker system df          # the log file is not in this report
```

**Step 2 — Emergency relief, the safe way.** Do **not** `rm` the log file: dockerd keeps it open,
the space is not freed (`sudo lsof -nP +L1` would show it as deleted but held), and `docker logs`
breaks for that container. Truncating in place frees the space immediately:

> Truncation destroys the log history of that container. Copy what you need first
> (`docker logs --since 1h CONTAINER > ~/CONTAINER-last-hour.log 2>&1`). It is an emergency
> measure, not a fix.

```bash
sudo truncate -s 0 "$(docker inspect -f '{{.LogPath}}' noisy)"
```

**Step 3 — Fix it properly.** Recreate the container with rotation (or set it daemon-wide, next
topic):

```bash
docker rm -f noisy
docker run -d --name noisy --log-opt max-size=10m --log-opt max-file=3 alpine:3.20 \
  sh -c 'while :; do echo "$(date) noisy line with some padding to grow faster"; done'
sleep 30; sudo ls -lh "$(dirname "$(docker inspect -f '{{.LogPath}}' noisy)")"
docker rm -f noisy
```

→ You now see `…-json.log`, `…-json.log.1`, `…-json.log.2`, each at most 10 MB.

**Step 4 — Break it differently: the app logs to a file.** For an app that writes
`/var/log/app/access.log` inside the container, `docker logs` is empty. The fix used by the
official nginx image is a symlink in the Dockerfile:
`RUN ln -sf /dev/stdout /var/log/app/access.log && ln -sf /dev/stderr /var/log/app/error.log`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Disk full on a Docker host | `sudo sh -c 'du -sh /var/lib/docker/containers/*'` | [Containers playbook](26-playbook-containers-k8s.md), [Storage](01-storage-disk.md) |
| `docker logs` empty, app clearly running | `docker exec CONTAINER ls -l /var/log` | this topic |
| `docker logs` says the driver does not support reading | the driver is remote without dual logging; read at the collector | next topic |

**Why it matters for troubleshooting.** Logs are your first evidence, and an unbounded log is
also your most common disk-full cause. Getting both right is one `daemon.json` change.

**Next step:** rotation for every container, and the journald alternative.

### Log rotation and the journald driver

**Level:** [L1 · Junior]

**Concept.** Set logging defaults once in `/etc/docker/daemon.json` so every **new** container
inherits them. Existing containers keep the configuration they were created with, so after the
change you must **recreate** containers (`docker compose up -d --force-recreate`, redeploy in
Dokploy); a plain restart is not enough.

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

→ At most 250 MB per container. Values must be **strings** (`"5"`, not `5`).

The **journald** driver is attractive on systemd hosts you already manage with journalctl: one
retention policy (`SystemMaxUse=` in `/etc/systemd/journald.conf`), one place to forward from,
and `docker logs` still works.

```json
{
  "log-driver": "journald",
  "log-opts": { "tag": "{{.Name}}" }
}
```

Per service in Compose (overrides the daemon default):

```yaml
services:
  web:
    image: harbor.example.com/shop/web:3f9c2a1
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"
```

| Option | Meaning |
|---|---|
| `max-size`, `max-file` | Rotation for `json-file` and `local` |
| `compress` | Gzip rotated `json-file` files (`"true"`) |
| `tag` | Name used by journald/syslog (`{{.Name}}`, `{{.ImageName}}`, `{{.ID}}`) |
| `mode` | `blocking` (default) or `non-blocking`: whether a slow driver may block the app's writes |
| `max-buffer-size` | Buffer for `non-blocking` mode, e.g. `"4m"`; lines beyond it are dropped |

**Key terms:** *`log-opts`* (`max-size` and `max-file`, per-container rotation), *`local` driver* (compressed files, rotated by default), *journald driver* (log lines go to the journal with `CONTAINER_NAME` and `CONTAINER_ID` fields), *dual logging* (`docker logs` keeps working with remote drivers through a local cache).

**See it on a real system**

```bash
journalctl CONTAINER_NAME=shop-web -n 20 --no-pager           # journald driver
journalctl -f CONTAINER_NAME=shop-web
journalctl -o verbose CONTAINER_NAME=shop-web -n 1 | grep -E 'CONTAINER_|IMAGE_NAME|SYSLOG_IDENTIFIER'
docker inspect shop-web --format '{{.HostConfig.LogConfig.Type}} {{.HostConfig.LogConfig.Config}}'
```

```
    CONTAINER_ID=3f9c2a1b7d4e
    CONTAINER_ID_FULL=3f9c2a1b7d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a
    CONTAINER_NAME=shop-web
    CONTAINER_TAG=shop-web
    IMAGE_NAME=harbor.example.com/shop/web:3f9c2a1
    SYSLOG_IDENTIFIER=shop-web
journald map[tag:{{.Name}}]
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: invalid daemon.json.** Write the values as numbers:

```bash
echo '{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": 3 } }' | sudo tee /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json
```

```
unable to configure the Docker daemon with file /etc/docker/daemon.json: json: cannot unmarshal number into Go value of type string
```

→ Had you restarted Docker instead of validating, dockerd would have failed to start and every
container on the host would have stayed down. **Always validate before restarting.**

**Step 2 — Fix it and apply.**

```bash
echo '{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }' | sudo tee /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker run -d --name rot alpine:3.20 sleep 600
docker inspect rot --format '{{.HostConfig.LogConfig.Config}}'     # map[max-file:3 max-size:10m]
docker rm -f rot
```

**Step 3 — Try journald.** Switch the driver to `journald`, validate, restart, run a container that
prints a line, read it with `journalctl CONTAINER_NAME=NAME`, then switch back.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Docker will not start after a daemon.json edit | `sudo dockerd --validate --config-file /etc/docker/daemon.json`; `journalctl -u docker -b` | section 12 |
| Rotation configured but files still grow | the container predates the change: `docker inspect … LogConfig`; recreate it | this topic |
| App hangs when the remote log server is down | blocking mode with a remote driver; use `mode: non-blocking` or a local driver | this topic |
| Container logs missing from the journal in bursts | journald rate limiting; check `journalctl -u systemd-journald` for "Suppressed" lines | [Logs & journal](06-logs-journal.md) |

**Why it matters for troubleshooting.** Dokploy's log viewer and `docker logs` both read through
the driver, so pick one that supports reading (`json-file`, `local`, `journald`). Rotation is a
platform default to set once, in daemon.json, through Ansible (section 12 drill).

**Next step:** networking, where most of your real incidents will happen.

---

## 7. Networking

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Networking ([note](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page)) · 2) KodeKloud: *Docker Certified Associate* — Publishing Ports ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)), then Networking Deep Dive – Docker ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Docker/page)) · 3) Video: KodeKloud *How Docker Networking Actually Works* (9 min) ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 4) Note: this section; KodeKloud does not cover DOCKER-USER, UFW or 127.0.0.11, so also read Docker docs *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)) · 5) Practice: the ip netns lab below, then iximiuz *Container networking from scratch* ([tutorial](https://labs.iximiuz.com/tutorials/container-networking-from-scratch)).

Docker networking is ordinary Linux networking, automated: network namespaces, veth pairs,
Linux bridges, routes, and NAT and filter rules in iptables (nftables underneath on Ubuntu).
Learn it at that level and the incidents stop being mysterious. Background on routing, NAT and
DNS is in [Networking](28-learn-networking.md).

### Default bridge vs user-defined bridge

**Level:** [L2 · Mid]

**Concept.** Each container gets its own network namespace with an `eth0`. That `eth0` is one end
of a **veth pair** (a virtual cable); the other end sits on the host, plugged into a **Linux
bridge** (a virtual switch). Containers started without `--network` land on the **default
bridge** `docker0` (172.17.0.0/16). Networks you create yourself, including the `PROJECT_default`
network Compose creates, are **user-defined bridges** (`br-ID`). They differ in ways that matter:

| | Default bridge (`docker0`) | User-defined bridge |
|---|---|---|
| Name resolution between containers | none (IP only; legacy `--link`) | yes, via embedded DNS at 127.0.0.11 |
| Who is on it | every container started without `--network` | only containers you attach |
| Isolation from other networks | — | traffic between different bridges is blocked |
| Attach/detach a running container | no | `docker network connect/disconnect` |
| Container `/etc/resolv.conf` | filtered copy of the host's | `nameserver 127.0.0.11` |

```
                  host ens18 192.0.2.10   (outbound: MASQUERADE to 192.0.2.10; inbound: DNAT for -p)
                              │
        ┌─────────────────────┴───────────────────────┐
   docker0 172.17.0.1/16                     br-8c1e… 172.18.0.1/16  (network "shop")
     │            │                            │                │
  veth…a       veth…b                       veth…c           veth…d          ← host ends of the cables
     │            │                            │                │
  eth0         eth0                         eth0             eth0            ← inside each container
  web          tool                         api              db
  172.17.0.2   172.17.0.3                   172.18.0.2       172.18.0.3
  (no names; IPs only)                      api resolves "db" through 127.0.0.11
```

**Key terms:** veth pair, Linux bridge, `docker0`, `br-ID`, subnet and gateway (the bridge's own
IP), IPAM, network alias, multi-homed container (on several networks, like Traefik).

**See it on a real system**

```bash
docker network ls
docker network inspect shop --format '{{range .IPAM.Config}}{{.Subnet}} gw {{.Gateway}}{{end}}'
docker network inspect shop --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{println}}{{end}}'
ip -br link show type bridge
ip -br addr show docker0
bridge link show | head
ip route | grep -E 'docker0|br-'
# Which host veth belongs to container "api"?
docker exec api cat /sys/class/net/eth0/iflink
ip -o link | grep '^23:'
```

```
NETWORK ID     NAME           DRIVER    SCOPE
1b2c3d4e5f60   bridge         bridge    local
8c1e2f3a4b5c   shop           bridge    local
2a3b4c5d6e7f   host           host      local
3c4d5e6f7a8b   none           null      local
172.18.0.0/16 gw 172.18.0.1
api 172.18.0.2/16
db 172.18.0.3/16
docker0          UP
br-8c1e2f3a4b5c  UP
docker0          UP             172.17.0.1/16
9: veth3f1a2b9@if8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 master docker0 state forwarding priority 32 cost 2
23: vethd41c7e2@if22: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 master br-8c1e2f3a4b5c state forwarding priority 32 cost 2
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1
172.18.0.0/16 dev br-8c1e2f3a4b5c proto kernel scope link src 172.18.0.1
23
23: vethd41c7e2@if22: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-8c1e2f3a4b5c state UP …
```

→ Every Docker network adds a **route on the host** (`172.18.0.0/16 dev br-…`). Remember that:
it is the root cause of the subnet-clash incident in section 12. The `iflink` trick maps a
container to its host veth, which is the interface to run `tcpdump -i` on.

**Hands-on lab (test VM only)**

**Step 1 — Break it: names do not resolve on the default bridge.**

```bash
docker run -d --name a1 nginx:1.27
docker run --rm alpine:3.20 ping -c1 -W2 a1
```

```
ping: bad address 'a1'
```

**Step 2 — Fix it: a user-defined network.**

```bash
docker network create shop
docker run -d --name a2 --network shop nginx:1.27
docker run --rm --network shop alpine:3.20 wget -qO- http://a2 | grep -o '<title>.*</title>'
```

```
<title>Welcome to nginx!</title>
```

**Step 3 — Break it: networks are isolated.** From the default bridge, try `a2`'s IP:

```bash
A2_IP=$(docker inspect -f '{{.NetworkSettings.Networks.shop.IPAddress}}' a2)
docker run --rm alpine:3.20 wget -T 3 -qO- "http://$A2_IP"
```

```
wget: download timed out
```

**Step 4 — Fix it: make a container multi-homed.** This is exactly how Traefik reaches apps on
several networks:

```bash
docker network connect shop a1
docker exec a1 getent hosts a2            # nginx image is Debian: getent exists
docker network disconnect shop a1
docker rm -f a1 a2 && docker network rm shop
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `bad address`, `Could not resolve host: db`, `Name or service not known` between containers | `docker network inspect NETWORK` (are both on it?) | [Containers playbook](26-playbook-containers-k8s.md) |
| Connection to another container times out | different networks; `docker inspect -f '{{json .NetworkSettings.Networks}}' C` | [Containers playbook](26-playbook-containers-k8s.md) |
| Traefik/Dokploy 502 or 504 for one app | the app is not on the network Traefik uses (`dokploy-network`) | [Containers playbook](26-playbook-containers-k8s.md) |
| Host loses access to part of the LAN after a deploy | a Docker network's route overlaps the LAN | section 12 |

**Why it matters for troubleshooting.** "Can container A reach container B" is answered by two
facts: are they on a common network, and does B listen on `0.0.0.0` inside. Check those before
anything else.

**Next step:** the DNS server inside every user-defined network.

### Embedded DNS at 127.0.0.11

**Level:** [L2 · Mid]

**Concept.** On user-defined networks, a container's `/etc/resolv.conf` says
`nameserver 127.0.0.11`. Docker answers there itself: container names, Compose service names and
network aliases resolve to container IPs. Every other name is forwarded to **upstream** servers,
taken from `"dns"` in daemon.json (or `--dns`/Compose `dns:`) if set, otherwise from the host's
resolver configuration. When the host uses systemd-resolved (stub `127.0.0.53`), Docker reads the
real upstreams from `/run/systemd/resolve/resolv.conf`. Other loopback-only resolvers (a local
dnsmasq or unbound on 127.0.0.1) are still used on user-defined networks: current Engines send
those queries from the host's network namespace (the resolv.conf comment then lists them as
`host(127.0.0.1)` or similar). If Docker finds **no usable upstream** at all, which happens on the
default bridge (no embedded DNS, loopback entries are simply dropped) and in some Docker-in-Docker
CI jobs, it falls back to Google's 8.8.8.8 and 8.8.4.4, which on-prem firewalls usually block.
This is blind spot number four in your Ops Ladder: "resolves on the host, fails in the container".

```
 container "api"                                    dockerd embedded DNS (inside the container's netns)
 getaddrinfo("db") ──▶ 127.0.0.11:53 ──▶ container / service / alias on this network? ──yes──▶ 172.18.0.3
                                          │ no
                                          ▼
                       upstream: daemon.json "dns"  ─or─  host upstreams
                       (/run/systemd/resolve/resolv.conf when the host uses 127.0.0.53;
                        other loopback resolvers are queried from the host's netns)
                                          │ none usable (default bridge, some DinD jobs)
                                          ▼
                       fallback 8.8.8.8 / 8.8.4.4   ← usually blocked on-prem: external names time out
```

**Key terms:** embedded DNS, upstream (external) servers, `ndots` (Docker sets `ndots:0`;
Kubernetes uses `ndots:5`), search domain, network alias.

**See it on a real system**

```bash
docker exec api cat /etc/resolv.conf
docker exec api getent hosts db                  # what the app's resolver library sees
docker run --rm --network shop nicolaka/netshoot dig +short db
docker run --rm --network shop nicolaka/netshoot dig example.com | grep -E 'SERVER|status'
resolvectl status | grep -E 'Current DNS|DNS Servers'    # the host's real upstreams
```

```
# Generated by Docker Engine.
# This file can be edited; Docker Engine will not make further changes once it
# has been modified.

nameserver 127.0.0.11
search example.com
options ndots:0

# Based on host file: '/run/systemd/resolve/resolv.conf' (internal resolver)
# ExtServers: [192.0.2.53 192.0.2.54]
# Overrides: []
# Option ndots from: internal
172.18.0.3      db
172.18.0.3
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 40412
;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53 192.0.2.54
```

→ `ExtServers` is the line that matters during an incident: these are the upstreams the
embedded DNS forwards to. If it says `[8.8.8.8 8.8.4.4]` on an on-prem host, you found the bug.

**Hands-on lab (test VM only)**

**Step 1 — Break it: an unreachable upstream.** Point Docker at a documentation address that
answers nothing:

```bash
echo '{ "dns": ["192.0.2.253"] }' | sudo tee /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker network create dnslab
docker run -d --name db --network dnslab nginx:1.27
docker run --rm --network dnslab alpine:3.20 nslookup db            # still works: answered locally
docker run --rm --network dnslab alpine:3.20 nslookup example.com   # fails
```

```
;; connection timed out; no servers could be reached
```

→ Internal names resolve, external names time out: the signature of a bad **upstream**, not of
broken Docker DNS.

**Step 2 — Prove where it dies.** In a second terminal, watch DNS on the host while repeating the
failing lookup:

```bash
sudo tcpdump -ni any port 53
```

```
11:31:02.410 ens18 Out IP 192.168.56.11.41234 > 192.0.2.253.53: 41865+ A? example.com. (29)
11:31:04.412 ens18 Out IP 192.168.56.11.41234 > 192.0.2.253.53: 41865+ A? example.com. (29)
```

→ The query leaves the host towards the configured upstream and no answer comes back.

**Step 3 — Fix it.** Put your real internal resolvers (from `resolvectl status`) in daemon.json,
validate, restart, retest, then clean up:

```bash
echo '{ "dns": ["192.0.2.53", "192.0.2.54"] }' | sudo tee /etc/docker/daemon.json   # use YOUR resolvers
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker run --rm --network dnslab alpine:3.20 nslookup example.com
docker rm -f db && docker network rm dnslab
```

> On the lab VM, restore the daemon.json you had before (or remove the `dns` key) when done.
> Restarting Docker stops every container (unless `live-restore` is on); only those with a
> restart policy come back by themselves.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Resolves on the host, fails in the container | `docker exec CONTAINER cat /etc/resolv.conf` (ExtServers?) | [Containers playbook](26-playbook-containers-k8s.md), [DNS](08-dns.md) |
| `nslookup` works, the app still fails | the app uses getaddrinfo: `docker exec CONTAINER getent hosts NAME` | [Site-down playbook](25-playbook-site-down.md) |
| DNS fails inside CI builds (Docker-in-Docker) | dind fell back to 8.8.8.8; pass `--dns` to the dind service | section 11 |
| Service name resolves to the wrong container | two containers share an alias on one network | this topic |

**Why it matters for troubleshooting.** There are two resolvers in play, the embedded one and
the upstream one, and they fail differently. Internal names failing means network membership;
external names failing means upstream servers or the firewall.

**Next step:** the network modes that are not bridges.

### Host, none, macvlan and ipvlan

**Level:** [L3 · Senior]

**Concept.** Bridges cover 95% of cases. The other drivers trade isolation or simplicity for a
specific need.

| Mode | What the container gets | Use it for | Watch out for |
|---|---|---|---|
| `--network host` | The host's network namespace | Node exporters, high-throughput tools | No isolation; `-p` is ignored; port clashes with host services (Apache!) |
| `--network none` | Only `lo` | Batch jobs that must not touch the network | Nothing to debug, by design |
| `macvlan` | Its own MAC and an IP on the physical LAN | Legacy apps that need a LAN IP | The host cannot reach its own macvlan containers; switch port security and VMware "forged transmits" can drop frames |
| `ipvlan` (l2) | Its own IP on the LAN, sharing the host's MAC | Like macvlan where port security limits MACs | Same host-to-container limitation; DHCP does not work |
| `overlay` | A network spanning several Swarm nodes | Swarm services, Dokploy | VXLAN ports and MTU (section 14) |

**Key terms:** *host network* (the container shares the host's network namespace), *`none`* (loopback only), *macvlan* (the container gets its own MAC address on the LAN), *ipvlan* (its own IP, sharing the parent's MAC), *parent interface* (the host NIC that a macvlan or ipvlan network hangs off).

**See it on a real system**

```bash
docker run --rm --network host alpine:3.20 ip -br addr            # the host's interfaces
docker run --rm --network none alpine:3.20 ip -br addr            # lo only
docker network create -d macvlan --subnet 192.168.50.0/24 --gateway 192.168.50.1 \
  --ip-range 192.168.50.192/27 -o parent=ens18 lan50               # LAN 192.168.50.0/24 on ens18
# alternative to the macvlan network above (create one or the other: Docker rejects a second
# network with an overlapping subnet)
docker network create -d ipvlan --subnet 192.168.50.0/24 --gateway 192.168.50.1 \
  -o parent=ens18 -o ipvlan_mode=l2 lan50-ipvlan
```

To let the host talk to its macvlan containers, add a macvlan "shim" interface on the host:

```bash
sudo ip link add mvl-shim link ens18 type macvlan mode bridge
sudo ip addr add 192.168.50.250/32 dev mvl-shim
sudo ip link set mvl-shim up
sudo ip route add 192.168.50.192/27 dev mvl-shim
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: host networking reproduces the Apache port clash.**

```bash
docker run -d --name h1 --network host nginx:1.27
docker run -d --name h2 --network host nginx:1.27
sleep 5; docker ps -a --filter name=h --format '{{.Names}} {{.Status}}'   # nginx retries bind() for ~2 s
docker logs h2 2>&1 | tail -2
```

```
h2 Exited (1) 2 seconds ago
h1 Up 6 seconds
2026/10/03 11:40:12 [emerg] 1#1: bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
```

→ With host networking there is no NAT layer: the container competes for host ports exactly
like Apache does, and `ss -ltnp` shows `nginx` directly instead of `docker-proxy`.

**Step 2 — Fix it.** Use bridge networking with published ports (or with no published port at
all, behind Traefik). `docker rm -f h1 h2`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `bind() … failed (98: Address already in use)` in a host-network container | `sudo ss -ltnp 'sport = :PORT'` | [Ports inventory](22-playbook-ports-inventory.md) |
| `WARNING: Published ports are discarded when using host network mode` | remove `-p` or stop using host mode | this topic |
| macvlan container unreachable from its own host | expected; add the shim interface | this topic |
| macvlan container unreachable from the LAN on VMware | vSwitch security: promiscuous mode / forged transmits; or use ipvlan | [Network reference](02-network.md) |

**Why it matters for troubleshooting.** Know which mode a container uses before you debug it:
`docker inspect -f '{{.HostConfig.NetworkMode}}' CONTAINER`. In host mode, every rule about NAT,
docker-proxy and DOCKER-USER below does not apply.

**Next step:** how `-p` actually works, packet by packet.

### Port publishing: DNAT and docker-proxy

**Level:** [L2 · Mid]

**Concept.** `-p [HOST_IP:]HOST_PORT:CONTAINER_PORT[/udp]` makes a container port reachable via a
host port. Docker implements it with three mechanisms:

1. **DNAT rule** in the nat table: packets arriving for `HOST_PORT` get their destination rewritten to `CONTAINER_IP:CONTAINER_PORT`. Conntrack remembers the translation and reverses it for replies.
2. **FORWARD accept rule**: because the rewritten destination is not the host, the packet is *forwarded* (through the FORWARD chain), not delivered locally (INPUT chain).
3. **docker-proxy**: a small userland process that listens on the host port. It handles connections from the host itself to `127.0.0.1:HOST_PORT` (which NAT rules do not see) and reserves the port so nothing else can take it. That is why `ss` shows `docker-proxy` as the owner.

Without `HOST_IP`, Docker binds `0.0.0.0` (and `::`): **every interface, every client**. Bind
`127.0.0.1:` for anything that should only be reached through a proxy on the same host or an SSH
tunnel. Your Dokploy apps normally publish **no** host port at all: Traefik reaches them over
the Docker network.

**How a packet travels from the internet into a container**

```
 client 203.0.113.50 ──▶ app.example.com:443 (DNS A record → 192.0.2.10)
   │
   ▼ arrives on host ens18, dst 192.0.2.10:443
 nat PREROUTING ──▶ chain DOCKER: tcp dport 443 ──▶ DNAT to 172.18.0.5:443     (conntrack entry created)
   │
   ▼ routing decision: 172.18.0.5 lives on br-8c1e…, so FORWARD, not INPUT
 filter FORWARD ──▶ DOCKER-USER (your rules, evaluated first)
                ──▶ Docker's rules: ACCEPT tcp to 172.18.0.5:443 arriving from outside the bridge
   │                (UFW's rules sit in INPUT and in later FORWARD jumps: never reached)
   ▼
 br-8c1e… ──▶ veth… ──▶ container netns: eth0 172.18.0.5 ──▶ Traefik listening on 0.0.0.0:443
   │
   ▼ reply 172.18.0.5:443 → 203.0.113.50: conntrack reverses the DNAT, the client sees 192.0.2.10:443
 Traefik ──▶ app container on dokploy-network (overlay) ──▶ app listening on 0.0.0.0:8000
```

**Key terms:** DNAT, SNAT/MASQUERADE, conntrack, PREROUTING/FORWARD/POSTROUTING, docker-proxy,
userland proxy, hairpin NAT.

**See it on a real system**

```bash
docker run -d --name pub -p 8080:80 nginx:1.27
docker port pub
sudo ss -ltnp 'sport = :8080'
sudo iptables -t nat -S PREROUTING
sudo iptables -t nat -S DOCKER
sudo iptables -t nat -S POSTROUTING | grep MASQUERADE
sudo iptables -S FORWARD
sudo iptables -t nat -L DOCKER -nv          # packet counters per DNAT rule
```

```
80/tcp -> 0.0.0.0:8080
80/tcp -> [::]:8080
LISTEN 0  4096    0.0.0.0:8080  0.0.0.0:*  users:(("docker-proxy",pid=5123,fd=7))
LISTEN 0  4096       [::]:8080     [::]:*  users:(("docker-proxy",pid=5130,fd=7))
-P PREROUTING ACCEPT
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
-N DOCKER
-A DOCKER ! -i docker0 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:80
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
-P FORWARD DROP
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-FORWARD
```

→ `-P FORWARD DROP`: Docker sets the FORWARD policy to DROP when it enables IP forwarding, which
also breaks other bridges on the host (KVM, LXD, your hand-made lab bridge below) until you allow
them. Chain names vary by Engine version (Engine 28 introduced `DOCKER-FORWARD` and friends; older
versions jump to `DOCKER-ISOLATION-STAGE-1` and `DOCKER` directly). On Ubuntu, `iptables` is the
nftables-backed variant, so the same rules also appear in `sudo nft list ruleset`. Docker 29 adds
an experimental native nftables backend (`"firewall-backend": "nftables"`), with different chain
names and no `DOCKER-USER`; read the packet filtering page before switching.

**Hands-on lab (test VM only)**

**Step 1 — Watch DNAT happen.** In one terminal on lab1, capture SYN packets; from lab2, curl
the published port:

```bash
sudo tcpdump -ni any -c 3 'tcp[tcpflags] == tcp-syn'          # on lab1
curl -sI http://192.168.56.11:8080 | head -1                   # on lab2
```

```
11:50:01.100212 ens18 In   IP 192.168.56.12.51514 > 192.168.56.11.8080: Flags [S], seq 1203…
11:50:01.100260 docker0 Out IP 192.168.56.12.51514 > 172.17.0.2.80: Flags [S], seq 1203…
11:50:01.100266 veth3f1a2b9 Out IP 192.168.56.12.51514 > 172.17.0.2.80: Flags [S], seq 1203…
```

→ Same packet three times: on the wire to `:8080`, then rewritten to `172.17.0.2:80`. The client
IP is preserved, so the app's access log shows the real client (unlike the Swarm routing mesh,
section 14). `sudo conntrack -L -p tcp --dport 8080` (package `conntrack`) shows both tuples.

**Step 2 — Break it (on purpose): bind to loopback only.**

```bash
docker rm -f pub && docker run -d --name pub -p 127.0.0.1:8080:80 nginx:1.27
curl -sI http://127.0.0.1:8080 | head -1                       # on lab1: works
curl -sI -m 3 http://192.168.56.11:8080 | head -1              # on lab2: refused
```

→ `curl: (7) Failed to connect to 192.168.56.11 port 8080: Connection refused` from lab2. For a
database or an admin UI, this is not broken: it is the **desired** state. Reach it with
`ssh -L 8080:127.0.0.1:8080 lab1` instead of opening it to the network.

**Step 3 — Break it: wrong container port.** `docker run -d --name pub2 -p 8081:8080 nginx:1.27`
(nginx listens on 80, not 8080) and curl it: `Connection reset by peer` locally, refused or a
hang remotely. `docker port pub2` looks fine; `sudo nsenter -t PID -n ss -ltn` shows the truth.
Clean up with `docker rm -f pub pub2`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `curl: (56) Recv failure: Connection reset by peer` on a published port | `sudo nsenter -t PID -n ss -ltn` (app on 127.0.0.1 or another port?) | [Containers playbook](26-playbook-containers-k8s.md) |
| Reachable locally, refused from other hosts | `docker port CONTAINER` (bound to 127.0.0.1?) | [Site-down playbook](25-playbook-site-down.md) |
| `port is already allocated` / `address already in use` | `docker ps --filter publish=PORT`, `sudo ss -ltnp 'sport = :PORT'` | [Ports inventory](22-playbook-ports-inventory.md) |
| KVM/LXD VMs lost network after installing Docker | `sudo iptables -S FORWARD` (policy DROP) | next topic |

**Why it matters for troubleshooting.** A published port has three layers that can each be wrong:
the host binding (`docker port`, `ss`), the NAT rule (`iptables -t nat -L DOCKER -nv` counters)
and the app's listen address inside the container. Check them in that order.

**Next step:** the firewall consequences: why UFW does not protect published ports.

### DOCKER-USER, UFW and the firewall

**Level:** [L2 · Mid]

**Concept.** UFW (and most host firewalls) filter in the **INPUT** chain: traffic addressed to the
host. A published container port is DNATed in PREROUTING and then **forwarded**, so it never
touches INPUT. Docker also inserts its FORWARD jumps at the top, before UFW's own forward chains.
Result: `ufw deny 8080` does **not** block a container published on 8080. This is blind spot five
in your Ops Ladder, and it has exposed many databases to the internet.

Docker's answer is the **DOCKER-USER** chain: it is evaluated first in FORWARD, and Docker never
puts its own rules in it. Two details make rules there work:

- By the time a packet reaches FORWARD, its destination is already rewritten to the **container** IP and port. Match the original host port with `-m conntrack --ctorigdstport PORT --ctdir ORIGINAL`.
- Insert with `-I`, never `-A`: on older Engines the chain ends with `-j RETURN`, and appended rules after it never match.

```
 packet for 192.0.2.10:5432 (published postgres)
   PREROUTING DNAT ─▶ 172.18.0.3:5432 ─▶ FORWARD ─▶ DOCKER-USER  ◀── put your filtering HERE
                                                 ─▶ Docker's ACCEPT rules
                                       INPUT (UFW) ── never consulted for this packet
```

**Key terms:** INPUT vs FORWARD, DOCKER-USER, conntrack original destination, `ufw route`
(UFW's forward rules), persistence of iptables rules across reboots.

**See it on a real system**

```bash
sudo ufw status verbose
sudo iptables -S DOCKER-USER
sudo iptables -L DOCKER-USER -nv --line-numbers
sudo iptables -L FORWARD -nv --line-numbers | head -8     # DOCKER-USER first, ufw-* chains later
```

**Hands-on lab (test VM only)**

> Enabling UFW on a remote VM can cut your SSH session. Allow SSH **before** `ufw enable`, and
> keep the VM console open.

**Step 1 — Break it: prove UFW does not protect a published port.**

```bash
docker run -d --name pg -p 5432:5432 -e POSTGRES_PASSWORD=labonly postgres:16
sudo ufw allow OpenSSH
sudo ufw default deny incoming
sudo ufw deny 5432/tcp
sudo ufw --force enable
nc -vz -w 3 192.168.56.11 5432          # run on lab2
```

```
Connection to 192.168.56.11 5432 port [tcp/postgresql] succeeded!
```

→ UFW says deny, the port is open. Every published port on a UFW host behaves like this.

**Step 2 — Fix it with DOCKER-USER.** Allow only the admin subnet (here lab2's network, pretend
it is 198.51.100.0/24 at work) to reach published port 5432:

```bash
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 5432 --ctdir ORIGINAL -j DROP
sudo iptables -I DOCKER-USER -i ens18 -s 192.168.56.12 -p tcp -m conntrack --ctorigdstport 5432 --ctdir ORIGINAL -j RETURN
sudo iptables -L DOCKER-USER -nv --line-numbers
```

→ `-I` puts each rule at the top, so insert the DROP first and the allow second; the allow ends
up above the drop. Test from lab2 (allowed) and from any third machine (times out). Replace
`ens18` with your external interface (`ip -br addr`).

**Step 3 — Better fix: do not publish it at all.** A database only its app talks to needs no
`-p`; put both on one network. For admin access use `-p 127.0.0.1:5432:5432` and an SSH tunnel.

**Step 4 — Persist a DOCKER-USER policy across reboots.** Rules added by hand vanish on reboot.
A small script plus a systemd unit tied to docker.service is the most predictable approach on
Ubuntu. Example policy for a Dokploy host: only Traefik's 80/443 and the admin subnet may reach
published container ports from outside.

```sh
#!/bin/sh
# /usr/local/sbin/docker-user-rules.sh
set -eu
EXT_IF="ens18"                    # external interface
ADMIN_NET="198.51.100.0/24"       # admin/VPN subnet
CHAIN="LOCAL-DOCKER-POLICY"

# Our own chain: safe to flush and rebuild (never flush Docker's chains or the whole table)
iptables -N "$CHAIN" 2>/dev/null || iptables -F "$CHAIN"
iptables -A "$CHAIN" -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN
iptables -A "$CHAIN" -s "$ADMIN_NET" -j RETURN
iptables -A "$CHAIN" -p tcp -m conntrack --ctorigdstport 80  --ctdir ORIGINAL -j RETURN
iptables -A "$CHAIN" -p tcp -m conntrack --ctorigdstport 443 --ctdir ORIGINAL -j RETURN
iptables -A "$CHAIN" -p udp -m conntrack --ctorigdstport 443 --ctdir ORIGINAL -j RETURN
iptables -A "$CHAIN" -j DROP

# Hook it into DOCKER-USER for traffic arriving from outside (idempotent)
iptables -C DOCKER-USER -i "$EXT_IF" -j "$CHAIN" 2>/dev/null \
  || iptables -I DOCKER-USER -i "$EXT_IF" -j "$CHAIN"
```

```ini
# /etc/systemd/system/docker-user-rules.service
[Unit]
Description=Local policy for published Docker ports (DOCKER-USER)
After=docker.service
Requires=docker.service
PartOf=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/docker-user-rules.sh

[Install]
WantedBy=docker.service
```

```bash
sudo chmod 0755 /usr/local/sbin/docker-user-rules.sh
sudo systemctl daemon-reload && sudo systemctl enable --now docker-user-rules.service
sudo iptables -L LOCAL-DOCKER-POLICY -nv
```

> Never run a bare `iptables -F` (or `iptables -t nat -F`) on a Docker host to "reset" the
> firewall: it deletes Docker's NAT and forward rules, every published port and all outbound
> container traffic stop, and with a DROP policy you can lock yourself out. Flush only chains you
> own, as above, and restart Docker if you ever need its rules rebuilt. If IPv6 is enabled for
> Docker, mirror the rules with `ip6tables`. A community pattern (often called "ufw-docker") hooks
> UFW's `ufw route` rules into DOCKER-USER via `/etc/ufw/after.rules`; it works, but understand the
> plain version first.

Clean up the lab: `docker rm -f pg`, `sudo ufw disable` (lab only), delete the test rules with
`sudo iptables -D DOCKER-USER RULE_NUMBER` using the numbers from `--line-numbers`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Port "blocked" in UFW is reachable from the internet | `docker ps --format '{{.Names}} {{.Ports}}'` (0.0.0.0 bindings) | [Site-down playbook](25-playbook-site-down.md) |
| DOCKER-USER rule has no effect | rule appended after `RETURN`, or matching the host port instead of `--ctorigdstport` | this topic |
| Rules gone after reboot | `systemctl status docker-user-rules` | this topic |
| Containers lost outbound access after a firewall change | `sudo iptables -t nat -S POSTROUTING` (MASQUERADE gone?), `sudo systemctl restart docker` | [Network reference](02-network.md) |

**Why it matters for troubleshooting.** On a Docker host, "is this port open to the world?" is
answered by `docker ps` and DOCKER-USER, not by `ufw status`. Include it in every port inventory
([Ports inventory](22-playbook-ports-inventory.md)). Read the Docker docs page on packet filtering
and firewalls once, end to end: https://docs.docker.com/engine/network/packet-filtering-firewalls/

**Next step:** build the whole bridge-and-NAT machinery by hand, so none of it is magic.

### Lab: build a bridge by hand with ip netns

**Level:** [L3 · Senior]

**Concept.** This is the L3 drill from your Ops Ladder: "Build a bridge network by hand with ip netns
and veth pairs". You will recreate what Docker does for every bridge network: two namespaces (the
"containers"), a bridge (`docker0`), veth pairs, a gateway IP, IP forwarding and MASQUERADE.

```
   netns red                 netns blue
   veth-red 10.99.0.2        veth-blue 10.99.0.3
        │                         │
   veth-red-br               veth-blue-br
        └──────── br-lab 10.99.0.1/24 ────────┘   (gateway, like docker0's 172.17.0.1)
                       │ ip_forward + MASQUERADE
                    host ens18 ──▶ LAN / internet
```

**Key terms:** *network namespace* (a private network stack: interfaces, routes, firewall rules),
*veth pair* (a virtual cable; what enters one end leaves the other), *bridge* (a virtual switch,
like `docker0`), *MASQUERADE* (source NAT to the host's outgoing address).

**See it on a real system:** `ip -br link show type bridge`, `ip -br link show type veth` and
`sudo iptables -t nat -S POSTROUTING` on any Docker host show the same pieces Docker built for you.

**Hands-on lab (test VM only)**

**Step 1 — Namespaces and a bridge.**

```bash
sudo ip netns add red
sudo ip netns add blue
sudo ip link add br-lab type bridge
sudo ip addr add 10.99.0.1/24 dev br-lab
sudo ip link set br-lab up
```

**Step 2 — One veth pair per namespace.** One end moves into the namespace, the other plugs
into the bridge:

```bash
for ns in red blue; do
  sudo ip link add "veth-$ns" type veth peer name "veth-$ns-br"
  sudo ip link set "veth-$ns" netns "$ns"
  sudo ip link set "veth-$ns-br" master br-lab
  sudo ip link set "veth-$ns-br" up
  sudo ip netns exec "$ns" ip link set lo up
  sudo ip netns exec "$ns" ip link set "veth-$ns" up
done
sudo ip netns exec red  ip addr add 10.99.0.2/24 dev veth-red
sudo ip netns exec blue ip addr add 10.99.0.3/24 dev veth-blue
sudo ip netns exec red  ip route add default via 10.99.0.1
sudo ip netns exec blue ip route add default via 10.99.0.1
```

**Step 3 — Test and observe.**

```bash
sudo ip netns exec red ping -c2 10.99.0.3        # red → blue across the bridge
sudo ip netns exec red ping -c2 10.99.0.1        # red → its gateway (the host)
bridge link show master br-lab
```

**Step 4 — Break it (on a host with Docker installed): red cannot even reach blue.** If ping in
step 3 failed, you just met two Docker side effects. `br_netfilter` makes bridged frames pass
through iptables, and Docker set the FORWARD policy to DROP:

```bash
sysctl net.bridge.bridge-nf-call-iptables 2>/dev/null   # = 1 means bridged traffic hits iptables
sudo iptables -S FORWARD | head -3                      # -P FORWARD DROP
```

Fix it the way Docker wants you to, in DOCKER-USER:

```bash
sudo iptables -I DOCKER-USER -i br-lab -j ACCEPT
sudo iptables -I DOCKER-USER -o br-lab -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

**Step 5 — Reach the outside world.** Enable forwarding (Docker already did) and NAT the lab
subnet, exactly like Docker's MASQUERADE rule for 172.17.0.0/16:

```bash
sysctl net.ipv4.ip_forward                               # 1 on a Docker host
sudo iptables -t nat -A POSTROUTING -s 10.99.0.0/24 ! -o br-lab -j MASQUERADE
sudo ip netns exec red ping -c2 192.0.2.1                # replace with your LAN gateway
```

**Step 6 — Break it again: remove MASQUERADE, then capture.** Delete the NAT rule
(`sudo iptables -t nat -D POSTROUTING -s 10.99.0.0/24 ! -o br-lab -j MASQUERADE`), ping again,
and run `sudo tcpdump -ni ens18 icmp`: packets leave with source 10.99.0.2, a private address the
LAN gateway has no route back to, so replies never come. Add the rule back and watch the source
change to the host's IP.

**Step 7 — Compare with Docker, then clean up.**

```bash
docker network inspect bridge --format '{{range .IPAM.Config}}{{.Subnet}} {{.Gateway}}{{end}}'
ip -d link show docker0 | head -3                       # "bridge" in the details
sudo ip netns del red; sudo ip netns del blue; sudo ip link del br-lab
sudo iptables -t nat -D POSTROUTING -s 10.99.0.0/24 ! -o br-lab -j MASQUERADE 2>/dev/null
sudo iptables -D DOCKER-USER -i br-lab -j ACCEPT
sudo iptables -D DOCKER-USER -o br-lab -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

→ Docker's namespaces are not listed by `ip netns list` (they live in `/run/docker/netns/`), but
you can enter one with `sudo nsenter --net=/run/docker/netns/ID` or by PID as in section 2.

**How it breaks**

| Symptom | What is missing | First command | Playbook |
|---|---|---|---|
| Namespaces cannot ping each other | a veth end is DOWN or not attached to the bridge | `ip -br link show master br-lab` | [Network reference](02-network.md) |
| Namespace pings the bridge, not the LAN | no default route inside the namespace, or `ip_forward=0` | `sudo ip netns exec red ip route`; `sysctl net.ipv4.ip_forward` | [Networking](28-learn-networking.md) |
| Packets leave the host, replies never return | MASQUERADE rule missing | `sudo iptables -t nat -S POSTROUTING`; `tcpdump -ni ens18 icmp` | this lab, step 6 |
| Forwarding is on, still dropped | FORWARD policy DROP (Docker sets it) with no ACCEPT for the bridge | `sudo iptables -S FORWARD`; `sudo iptables -S DOCKER-USER` | section 7, DOCKER-USER topic |

**Why it matters for troubleshooting.** Every Docker bridge problem is one of these four rows:
link, route, NAT or filter. Having built them by hand, you can check them in that order on a real
host (`ip link`, `ip route`, `iptables -t nat`, `iptables -S FORWARD`) instead of restarting
Docker and hoping.

**Next step:** continue with the iximiuz tutorial that builds the same thing in more depth
(https://labs.iximiuz.com/tutorials/container-networking-from-scratch), then the networking
challenges in the Docker roadmap (https://labs.iximiuz.com/roadmaps/docker). Afterwards, read
the Docker networking docs (https://docs.docker.com/engine/network/) and notice that you now
understand every page.

---

## 8. Storage

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands: Volumes and Bind Mounts, then Docker Engine & Storage ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine – Storage ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Note: this section, with [Storage & disk](01-storage-disk.md) and [Users & permissions](10-users-permissions-security.md) for UIDs · 4) Practice: the backup-and-restore lab below, timed.

### Volumes, bind mounts and tmpfs

**Level:** [L1 · Junior]

**Concept.** A container's writable layer dies with the container (section 3), so anything that
must survive a redeploy lives in a **mount**. There are three kinds:

| | Named volume | Bind mount | tmpfs |
|---|---|---|---|
| Syntax | `-v pgdata:/var/lib/postgresql/data` | `-v /srv/shop/config:/etc/app:ro` | `--tmpfs /tmp:size=64m` |
| Managed by | Docker (`docker volume …`) | You (any host path) | Kernel (RAM) |
| Lives at | `/var/lib/docker/volumes/NAME/_data` | the host path you gave | memory, gone on stop |
| First mount when empty | **copies** the image's content at that path into the volume | **hides** the image's content at that path | empty |
| Best for | databases, uploads, app state | config files, certificates, code in development | scratch space, secrets at runtime, read-only root filesystems |
| Main risk | deleted by `docker compose down -v` or `docker volume prune -a` (Engine 23+: plain `prune` removes only anonymous volumes) | wrong ownership; missing path silently created as a root-owned directory | eats RAM; counts towards the memory limit |

**Anonymous volumes** are named volumes with a random 64-character name. They appear when an
image declares `VOLUME /path` (the official `postgres`, `mysql` and `redis` images do) and you do
not mount anything there. Each new container gets a **new** anonymous volume: "we redeployed and
the database is empty" is usually this. (The official postgres image changed its data directory
layout in version 18; check the image docs when you upgrade and mount the path they document.)

`--mount` is the explicit syntax and fails loudly when a bind source does not exist; `-v` creates
the missing path as an empty root-owned **directory**, which is how a missing config **file**
turns into a confusing error.

```bash
docker run --mount type=volume,src=pgdata,dst=/var/lib/postgresql/data postgres:16
docker run --mount type=bind,src=/srv/shop/config,dst=/etc/app,readonly IMAGE
docker run --mount type=tmpfs,dst=/tmp,tmpfs-size=67108864 IMAGE
```

**Key terms:** named volume, anonymous volume, bind mount, propagation, `:ro`, `:z`/`:Z`
(SELinux relabel), volume driver (local, NFS via `local` with options).

**See it on a real system**

```bash
docker volume ls
docker volume ls -f dangling=true                    # not used by any container
docker volume inspect pgdata
docker inspect CONTAINER --format '{{range .Mounts}}{{.Type}} {{if .Name}}{{.Name}}{{else}}{{.Source}}{{end}} -> {{.Destination}} rw={{.RW}}{{println}}{{end}}'
docker system df -v | sed -n '/Local Volumes space usage/,/^$/p'
```

```
DRIVER    VOLUME NAME
local     4f1c9e0a8b7d6c5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0
local     shop_pgdata
[
    {
        "CreatedAt": "2026-09-12T08:14:02Z",
        "Driver": "local",
        "Labels": { "com.docker.compose.project": "shop", "com.docker.compose.volume": "pgdata" },
        "Mountpoint": "/var/lib/docker/volumes/shop_pgdata/_data",
        "Name": "shop_pgdata",
        "Scope": "local"
    }
]
volume shop_pgdata -> /var/lib/postgresql/data rw=true
bind /srv/shop/config -> /etc/app rw=false
```

→ The first volume is anonymous (random name, no Compose labels; Engine 23+ marks it with the
`com.docker.volume.anonymous` label): find out what created it before deleting it. Compose-created volumes are prefixed with the project name (`shop_pgdata`).

**Hands-on lab (test VM only)**

**Step 1 — Break it: data "lost" on redeploy.**

```bash
docker run -d --name db1 -e POSTGRES_PASSWORD=labonly postgres:16
sleep 5; docker exec db1 psql -U postgres -c 'CREATE TABLE orders(id int);'
docker rm -f db1
docker run -d --name db1 -e POSTGRES_PASSWORD=labonly postgres:16
sleep 5; docker exec db1 psql -U postgres -c '\dt'
docker volume ls -f dangling=true
```

```
Did not find any relations.
DRIVER    VOLUME NAME
local     9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f4f1c9e0a8b7d6c5e4f3a2b1c0d
```

→ The table is not gone: it sits in the **previous** anonymous volume, now dangling. Recovery is
possible by mounting that volume into a new container. Prevention is a named volume.

**Step 2 — Fix it.**

```bash
docker rm -f db1
docker run -d --name db1 -e POSTGRES_PASSWORD=labonly -v pgdata:/var/lib/postgresql/data postgres:16
```

**Step 3 — Break it: a bind mount for a file that does not exist.**

```bash
docker run --rm -v /srv/lab/nginx.conf:/etc/nginx/nginx.conf:ro nginx:1.27
ls -ld /srv/lab/nginx.conf
```

```
docker: Error response from daemon: failed to create task for container: … error mounting "/srv/lab/nginx.conf" to rootfs at "/etc/nginx/nginx.conf": … not a directory: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type
drwxr-xr-x 2 root root 4096 Oct  3 12:01 /srv/lab/nginx.conf
```

→ `-v` created a **directory** named `nginx.conf`. Fix: `sudo rmdir /srv/lab/nginx.conf`, create
the real file, and prefer `--mount type=bind,…` which would have said
`bind source path does not exist` instead.

**Step 4 — Break it: an edit to a single-file bind mount is not seen.** Mount a real file, then
edit it on the host with `sed -i` (which writes a new file and renames it): the container keeps
the **old inode** and never sees the change. Mount the containing directory instead, or restart
the container after edits. Clean up: `docker rm -f db1; docker volume rm pgdata`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Data gone after redeploy | `docker volume ls -f dangling=true`; `docker inspect` mounts of the old and new containers | [Containers playbook](26-playbook-containers-k8s.md) |
| `Are you trying to mount a directory onto a file (or vice-versa)?` | `ls -ld HOST_PATH` | this topic |
| Config edit on the host not picked up | single-file bind mount plus an editor that replaces the file | this topic |
| `/var/lib/docker/volumes` fills the disk | `docker system df -v` | [Storage](01-storage-disk.md) |

**Why it matters for troubleshooting.** Before any destructive action (`down -v`, `prune`,
deleting a "stale" volume), list which container uses which mount. Most Docker data losses are
self-inflicted during cleanup.

**Next step:** the other half of storage problems: ownership and permissions.

### Permissions and UIDs

**Level:** [L2 · Mid]

**Concept.** The kernel checks **numeric** UIDs and GIDs. Without a user namespace there is no
translation: UID 10001 inside the container is UID 10001 on the host, and root inside is root on
the host's files. Names (`app`, `www-data`) are only labels looked up in each side's own
`/etc/passwd`, which is why `ls -l` on the host shows a different (or no) name for files written
by a container. Use `ls -ln` to see the truth.

| Situation | Fix |
|---|---|
| Non-root container cannot write to a bind-mounted host directory | `sudo chown -R 10001:10001 /srv/shop/uploads` (the container's UID), or a shared group with setgid on the directory |
| Container running as root leaves root-owned files in your project directory | run with `--user "$(id -u):$(id -g)"` for dev tooling |
| Named volume has the wrong owner | Docker copies ownership from the image path on first use: create and `chown` the directory in the Dockerfile before declaring it |
| RHEL/Rocky with SELinux (and dockerd's `selinux-enabled` on): `Permission denied` although modes look right | relabel with `:z` (shared) or `:Z` (private) on the mount; check `ausearch -m avc -ts recent` |
| NFS share: root in the container gets `Operation not permitted` | NFS `root_squash` maps root to `nobody`; run as a UID the export allows |

**Key terms:** *numeric UID/GID* (what the kernel compares), *`ls -ln`* (shows numbers instead of names), *root squash* (NFS maps root to `nobody`), *`:z` / `:Z`* (SELinux relabel of a bind mount, shared or private), *`--user UID:GID`* (run the container as that identity).

**See it on a real system**

```bash
docker exec CONTAINER id                              # who the app runs as
docker run --rm --entrypoint id IMAGE                 # who the image runs as by default
ls -ln /srv/shop/uploads                              # numeric owner on the host
stat -c '%u:%g %a %n' /srv/shop/uploads
```

**Hands-on lab (test VM only)**

**Step 1 — Break it.**

```bash
sudo mkdir -p /srv/lab/data && sudo chown 1000:1000 /srv/lab/data
docker run --rm --user 10001:10001 -v /srv/lab/data:/data alpine:3.20 touch /data/x
```

```
touch: /data/x: Permission denied
```

**Step 2 — Diagnose with numbers.**

```bash
ls -ldn /srv/lab/data                                         # owner 1000
docker run --rm --user 10001:10001 alpine:3.20 id             # writer is 10001
```

**Step 3 — Fix it (least privilege first).** Give the directory to the container's UID; do not
`chmod 777`, and do not switch the container to root:

```bash
sudo chown 10001:10001 /srv/lab/data
docker run --rm --user 10001:10001 -v /srv/lab/data:/data alpine:3.20 sh -c 'touch /data/x && ls -ln /data'
```

**Step 4 — RHEL/Rocky variant (if you have one).** With SELinux enforcing **and** SELinux support
enabled in dockerd (`"selinux-enabled": true` in daemon.json; Docker CE leaves it off by default,
check for `name=selinux` in `docker info --format '{{.SecurityOptions}}'`), the same mount fails
even with correct ownership until you add `:Z` (`-v /srv/lab/data:/data:Z`). Never disable
SELinux to fix it. Clean up: `sudo rm -rf /srv/lab/data` (lab path only).

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Permission denied` on a bind mount | `ls -ln HOST_PATH` vs `docker exec CONTAINER id` | [Containers playbook](26-playbook-containers-k8s.md) |
| `chown: … Operation not permitted` at container start (NFS) | `findmnt -t nfs,nfs4` and check the export for `root_squash` | [Users & permissions](10-users-permissions-security.md) |
| Works on Ubuntu, fails on Rocky | `sudo ausearch -m avc -ts recent` (SELinux) | [Users & permissions](10-users-permissions-security.md) |

**Why it matters for troubleshooting.** Migrating Apache apps means moving upload and data
directories that were owned by `www-data` (UID 33 on Debian/Ubuntu). Decide the container UID
first, then `chown` the migrated data to it, and write that into the runbook.

**Next step:** backups, because a volume is only as safe as its last tested restore.

### Backing up and restoring volumes

**Level:** [L2 · Mid]

**Concept.** A volume is a directory, so the universal backup is "tar it from a helper container
that mounts it read-only". For **databases**, a file-level copy of a running database can be
inconsistent; use the database's own dump tool (`pg_dump`, `mysqldump`) or stop the container
first. A backup that has never been restored is a hope, not a backup.

| Data | Method |
|---|---|
| Static files, uploads | `tar` via a helper container, or `restic`/`borg` on the host path |
| PostgreSQL | `docker exec db pg_dump -Fc …` (no `-t`: a TTY corrupts binary output) |
| MySQL/MariaDB | `docker exec db mysqldump --single-transaction …` |
| Whole host | VM snapshot plus off-host copies; snapshots are not backups by themselves |

**Key terms:** *named volume* (a Docker-managed directory under `/var/lib/docker/volumes`), *helper container* (a throwaway container that mounts the volume so you can tar it), *logical dump* (`pg_dump`, `mysqldump`: consistent while the database runs), *restore test* (the only proof that a backup works).

**See it on a real system**

```bash
docker volume inspect shop_pgdata --format '{{.Mountpoint}}'
docker ps -a --filter volume=shop_pgdata --format '{{.Names}}'       # who uses it
```

**Hands-on lab (test VM only)**

**Step 1 — Create data.**

```bash
docker volume create appdata
docker run --rm -v appdata:/data alpine:3.20 sh -c 'echo "order 1001" > /data/orders.txt'
```

**Step 2 — Back it up** (read-only mount, archive written to the current host directory):

```bash
docker run --rm -v appdata:/data:ro -v "$PWD":/backup alpine:3.20 \
  tar czf /backup/appdata-$(date +%F).tar.gz -C /data .
ls -lh appdata-*.tar.gz
```

**Step 3 — Break it: delete the volume.**

> `docker volume rm` is permanent; there is no trash. In real life, confirm the backup file is
> complete (`tar tzf FILE`) before removing anything.

```bash
tar tzf appdata-$(date +%F).tar.gz
docker volume rm appdata
```

**Step 4 — Restore and verify.**

```bash
docker volume create appdata
docker run --rm -v appdata:/data -v "$PWD":/backup alpine:3.20 \
  tar xzf /backup/appdata-$(date +%F).tar.gz -C /data
docker run --rm -v appdata:/data alpine:3.20 cat /data/orders.txt
```

**Step 5 — Database dump and restore (PostgreSQL).**

```bash
docker exec db pg_dump -U app -d app -Fc > app-$(date +%F).dump        # no -t!
docker exec -i db pg_restore -U app -d app --clean --if-exists < app-$(date +%F).dump
```

**Step 6 — Copy a volume to another host** (for example during a migration), streaming over SSH:

```bash
docker run --rm -v appdata:/data:ro alpine:3.20 tar cz -C /data . \
  | ssh lab2 'docker volume create appdata && docker run --rm -i -v appdata:/data alpine:3.20 tar xz -C /data'
```

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Restored database is corrupt or will not start | the files were copied while the DB was running; restore from a dump | this topic |
| `pg_restore: error: input file does not appear to be a valid archive` | the dump was made with `docker exec -t`; redo it without `-t` | this topic |
| `docker volume rm`: `volume is in use` | `docker ps -a --filter volume=NAME` | this topic |

**Why it matters for troubleshooting.** During an incident, "restore from backup" must be a
tested, timed procedure. Put the restore commands and the measured time in the runbook of every
stateful app you move to Dokploy.

**Next step:** describe whole applications declaratively with Compose.

---

## 9. Docker Compose

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose ([note](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page)) · 2) KodeKloud: *Docker Certified Associate* — Docker Compose section ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Video: KodeKloud *Docker Compose Tutorial | Docker for Beginners* (44 min) ([YouTube](https://www.youtube.com/watch?v=iOGEBj7Ozak)) · 4) Note: this section · 5) Practice: KodeKloud Docker Playground, which includes Compose ([playground](https://kodekloud.com/playgrounds/playground-docker)).

### Compose file anatomy and project names

**Level:** [L1 · Junior]

**Concept.** Compose describes a multi-container application in one YAML file (`compose.yaml`;
`docker-compose.yml` still works) and `docker compose up` turns it into networks, volumes and
containers, labelled so Compose can find them again. It is also one of the deployment types
Dokploy offers, so the file you test on your laptop is the file Dokploy runs. The top-level
`version:` key is obsolete; Compose ignores it with a warning.

```yaml
# compose.yaml
name: shop                         # project name (else: -p, COMPOSE_PROJECT_NAME, or the directory name)

services:
  web:
    image: harbor.example.com/shop/web:${TAG:-latest}
    build: .                       # used by "docker compose build" / "up --build"
    init: true                     # tini as PID 1
    environment:
      DATABASE_URL: postgresql://app:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}@db:5432/app
    env_file:
      - ./web.env                  # injected into the container (not used for interpolation)
    ports:
      - "127.0.0.1:18000:8000"     # loopback only; Traefik will front it in production
    depends_on:
      db:
        condition: service_healthy
        restart: true
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 20s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512m
          cpus: "1.0"
    logging:
      driver: json-file
      options: { max-size: "50m", max-file: "5" }
    networks: [backend]

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U app -d app"]   # TCP, not the socket (see the depends_on lab)
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    restart: unless-stopped
    networks: [backend]

  adminer:
    image: adminer:4
    profiles: [debug]              # only started with --profile debug
    ports: ["127.0.0.1:18080:8080"]
    networks: [backend]

volumes:
  pgdata:

networks:
  backend:
```

Names Compose derives from the project name `shop`:

| Object | Name |
|---|---|
| Containers | `shop-web-1`, `shop-db-1` (service name plus replica index) |
| Default/declared network | `shop_backend` (or `shop_default` when none is declared) |
| Volume | `shop_pgdata` |
| Labels on everything | `com.docker.compose.project=shop`, `com.docker.compose.service=web` |
| DNS names inside the network | `web`, `db` (service names), plus the container names |

> Two different directories with the same name (say two folders called `app`) give the same
> default project name. Compose then treats them as one project: it recreates or warns about the
> other's containers as "orphans". Always set `name:` explicitly.

**Key terms:** *project* (one Compose application; its name comes from `name:`, `-p`, `COMPOSE_PROJECT_NAME` or the directory), *service* (one container definition, possibly several replicas), *default network* (`PROJECT_default`), *Compose labels* (`com.docker.compose.project` and `com.docker.compose.service` on every container), *container name* (`PROJECT-SERVICE-N`).

**See it on a real system**

```bash
docker compose ls                                    # all projects on this host
docker compose -p shop ps --format 'table {{.Name}}\t{{.Image}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}'
docker ps --filter label=com.docker.compose.project=shop --format '{{.Names}}'
docker inspect shop-web-1 --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
```

```
NAME      STATUS                 CONFIG FILES
shop      running(2)             /srv/shop/compose.yaml
NAME         IMAGE                                  SERVICE   STATUS                   PORTS
shop-db-1    postgres:16                            db        Up 2 hours (healthy)     5432/tcp
shop-web-1   harbor.example.com/shop/web:3f9c2a1    web       Up 2 hours (healthy)     127.0.0.1:18000->8000/tcp
shop-web-1
shop-db-1
/srv/shop
```

→ `working_dir` label answers "where is the compose file for this container?", the Compose
version of "which vhost file configures this site?" from your Apache incident.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** Save the file above as `~/lab/shop/compose.yaml`, create `web.env` with
`LOG_LEVEL=info`, build the Python image from section 4 as `harbor.example.com/shop/web:latest`
(or change `image:` to `shop-web:dev`), then:

```bash
cd ~/lab/shop
echo 'POSTGRES_PASSWORD=labonly' > .env
docker compose up -d
docker compose ps
```

**Step 2 — Break it: project-name collision.** Copy the directory to `/tmp/x/shop`, remove the
`name:` line from both copies, and run `docker compose up -d` in the copy. Both copies now derive
the project name `shop` from their directory name and manage the same containers: Compose
recreates or adopts the original's containers, and if the service lists differ it also warns
about "orphan containers". Check with `docker compose ls`: there is only one `shop` project.

**Step 3 — Fix it.** Put `name:` back (unique per app), `docker compose down` in the copy, delete
it.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Found orphan containers ([…]) for this project` | `docker compose ls`; give each app a unique `name:` | this topic |
| `the attribute version is obsolete, it will be ignored` | delete the `version:` line; harmless | this topic |
| Cannot find which file runs a container | `docker inspect C --format '{{json .Config.Labels}}'` (working_dir, config_files) | [Ports inventory](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting.** Compose labels turn "what is this container and where is
its config?" into a single `docker inspect`. That is the inventory question from your incident,
answered by design.

**Next step:** start order and readiness with `depends_on` and health checks.

### depends_on and healthchecks

**Level:** [L2 · Mid]

**Concept.** Short-form `depends_on: [db]` only waits until the `db` **container has started**,
not until PostgreSQL accepts connections. The long form waits for a condition:

| Condition | Waits until |
|---|---|
| `service_started` | the dependency's container is running (same as the short form) |
| `service_healthy` | its HEALTHCHECK reports healthy |
| `service_completed_successfully` | it exited 0 (migrations, one-shot setup jobs) |

Extra keys: `restart: true` restarts this service when the dependency is restarted by Compose;
`required: false` tolerates a missing optional dependency. Three limits to remember: ordering
applies only to `docker compose up`, not to later restarts by the restart policy; `docker stack
deploy` (Swarm) ignores `depends_on` completely; and a database can still restart under a running
app. So the application must **retry** its connections anyway; `depends_on` only makes cold starts
clean.

**Key terms:** *`service_started`* (the default: wait only until the dependency's container has started), *`service_healthy`* (wait until its health check passes), *`service_completed_successfully`* (wait for a one-shot job such as migrations to exit 0), *`restart: true`* (Compose restarts this service when it restarts or updates the dependency).

**See it on a real system**

```bash
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
docker compose up -d --wait            # returns only when services are running/healthy (or fails)
docker inspect shop-db-1 --format '{{.State.Health.Status}}'
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: a client that starts too early.**

```bash
mkdir -p ~/lab/dep && cd ~/lab/dep
cat > compose.yaml <<'EOF'
name: dep
services:
  db:
    image: postgres:16
    environment: { POSTGRES_PASSWORD: labonly }
  client:
    image: postgres:16
    depends_on: [db]
    environment: { PGPASSWORD: labonly }
    command: ["psql", "-h", "db", "-U", "postgres", "-c", "select 'connected'"]
EOF
docker compose up client; docker compose down
```

```
client-1  | psql: error: connection to server at "db" (172.21.0.2), port 5432 failed: Connection refused
client-1  | 	Is the server running on that host and accepting TCP/IP connections?
client-1 exited with code 2
```

**Step 2 — Fix it: health check plus condition.**

```bash
cat > compose.yaml <<'EOF'
name: dep
services:
  db:
    image: postgres:16
    environment: { POSTGRES_PASSWORD: labonly }
    healthcheck:
      # -h 127.0.0.1: during first-run init the image starts a temporary server on the Unix
      # socket only; a socket check would report "ready" before TCP clients can connect
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U postgres"]
      interval: 2s
      timeout: 3s
      retries: 15
  client:
    image: postgres:16
    depends_on:
      db: { condition: service_healthy }
    environment: { PGPASSWORD: labonly }
    command: ["psql", "-h", "db", "-U", "postgres", "-c", "select 'connected'"]
EOF
docker compose up client; docker compose down; cd ~ && rm -rf ~/lab/dep
```

→ Compose now prints `Waiting`/`Healthy` for `db` first, then the client prints `connected`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| App crashes on first boot with `Connection refused` to its DB, fine after a restart | `docker compose logs db web` (timestamps); add health plus condition | this topic |
| `dependency failed to start: container … is unhealthy` | `docker inspect DEP --format '{{json .State.Health}}'` | section 4 (HEALTHCHECK) |
| Works with Compose, flaps as a Swarm stack/Dokploy stack | `depends_on` ignored by Swarm; the app must retry | section 14 |

**Why it matters for troubleshooting.** A boot-order race looks like a random crash that "fixes
itself". Compare the first log timestamps of both services to see it.

**Next step:** where Compose gets its values from: env files and interpolation.

### Env files and variable interpolation

**Level:** [L1 · Junior]

**Concept.** Two features look alike and are constantly confused:

1. **Interpolation**: `${VAR}` inside `compose.yaml` is replaced **when Compose reads the file**. Values come from your shell environment and from the `.env` file in the project directory (or `--env-file FILE`). The container never sees `.env` itself.
2. **Container environment**: `environment:` and `env_file:` set variables **inside the container**. `env_file:` files are not used for interpolation.

```
 shell env ─┐
 .env ──────┴─▶ interpolation of compose.yaml ─▶ rendered config ─▶ environment: + env_file: ─▶ container
                (docker compose config shows this)                   (docker exec C env shows this)
```

| Syntax | Result |
|---|---|
| `${VAR}` | value, or empty with a warning if unset |
| `${VAR:-default}` | default if unset **or empty** |
| `${VAR-default}` | default only if unset |
| `${VAR:?message}` | fail with `message` if unset or empty (use for required secrets) |
| `${VAR:+alt}` | `alt` if set and non-empty |
| `$$` | a literal `$` (for passwords and shell commands) |

Precedence for interpolation: shell environment, then `--env-file`/`.env`. Precedence inside the
container: `docker compose run -e`, then `environment:`, then `env_file:`, then the image's `ENV`.
In Dokploy, the app's Environment settings play the role of the `.env` file for Compose
deployments.

**Key terms:** *`.env`* (feeds `${VAR}` interpolation inside the compose file), *`env_file:`* (variables passed into the container), *`${VAR:-default}`* (fallback when unset or empty), *`${VAR:?message}`* (fail when unset or empty), *`docker compose config`* (the fully resolved file, secrets included).

**See it on a real system**

```bash
docker compose config                       # the fully rendered file: the truth
docker compose config --services
docker compose exec web env | sort          # what the container really got
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: a missing required variable.** In `~/lab/shop`, remove `.env` and run
`docker compose config`:

```
error while interpolating services.db.environment.POSTGRES_PASSWORD: required variable POSTGRES_PASSWORD is missing a value: set POSTGRES_PASSWORD
```

→ Exactly what `:?` is for: fail at deploy time, not with a half-configured database.

**Step 2 — Break it: a `$` in a password.** Under `db.environment` in `compose.yaml`,
temporarily replace the password line with `POSTGRES_PASSWORD: Pa$word42` and run
`docker compose config`:

```
WARN[0000] The "word42" variable is not set. Defaulting to a blank string.
```

→ Compose interpolated `$word42`, so the database would have been initialised with the password
`Pa`. In YAML write `Pa$$word42`. In `.env`, single-quote such values
(`POSTGRES_PASSWORD='Pa$word42'`), because unquoted and double-quoted `.env` values are
interpolated as well. Always check with `docker compose config`.

**Step 3 — Fix and verify.** Restore `.env`, run `docker compose config | grep -A3 environment`
and `docker compose exec db env | grep POSTGRES`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `required variable … is missing a value` | `ls -la .env`; run Compose from the project directory | this topic |
| `The "X" variable is not set. Defaulting to a blank string.` | a `$` in a value; escape as `$$` | this topic |
| App sees an old value after editing `.env` | the container was not recreated; `docker compose up -d` | next topic |
| Secret committed to Git in `compose.yaml` | rotate it; move it to `.env` (git-ignored) or secrets | section 13 |

**Why it matters for troubleshooting.** `docker compose config` and `docker compose exec SERVICE env`
are the two commands that end every "but I set the variable" discussion.

**Next step:** profiles, overrides and the commands you will use daily.

### Profiles, overrides and daily commands

**Level:** [L2 · Mid]

**Concept.** **Profiles** mark optional services (debug tools, one-off jobs) that start only with
`--profile NAME`. **Override files** layer environment-specific changes over a base file:
`compose.override.yaml` is merged automatically when present; anything else is explicit with
`-f`. Merging rules: mappings merge by key (`environment`, `labels`), most lists are combined
(`ports`, `volumes` by target), single values are replaced. YAML tags `!reset` (drop an inherited
value) and `!override` (replace instead of merge) handle the exceptions.

```bash
# base + automatic override (development)
docker compose up -d
# base + production file, no automatic override
docker compose -f compose.yaml -f compose.prod.yaml up -d
# start the optional debug tools too
docker compose --profile debug up -d
```

Daily commands:

| Command | What it does | Gotcha |
|---|---|---|
| `docker compose up -d` | Create or **recreate changed** services | the command that applies config changes |
| `docker compose up -d --build` | Rebuild images first | |
| `docker compose up -d --wait` | Block until healthy, fail otherwise | good in CI and scripts |
| `docker compose up -d --force-recreate SERVICE` | Recreate even if unchanged | |
| `docker compose up -d --no-deps SERVICE` | Touch only this service | |
| `docker compose pull` | Fetch newer images for the tags | does not restart anything by itself |
| `docker compose ps -a` | Status of this project's containers | |
| `docker compose logs -f --tail 100 SERVICE` | Follow logs | |
| `docker compose exec SERVICE sh` | Shell in a running service | |
| `docker compose run --rm SERVICE CMD` | One-off container (migrations) | new container, same config |
| `docker compose restart SERVICE` | Restart the **existing** container | does **not** apply compose.yaml or .env changes |
| `docker compose stop` / `start` | Stop/start without removing | |
| `docker compose down` | Remove containers and networks | volumes kept |
| `docker compose down -v` | Also delete named volumes | **destroys data** |
| `docker compose down --remove-orphans` | Also remove containers of services no longer in the file | |
| `docker compose config` | Render the final configuration | |

> `docker compose down -v` deletes the project's named volumes, which means your database. Use
> plain `down` unless you really want a clean slate, and take a dump first (section 8).

**Key terms:** *profile* (services that start only when their profile is enabled), *override file* (`compose.override.yaml`, merged automatically), *`-f a.yaml -f b.yaml`* (explicit merge order, later files win), *`--wait`* (block until services are running or healthy).

**See it on a real system**

```bash
docker compose -f compose.yaml -f compose.prod.yaml config | less   # what production will get
docker compose ls
docker compose --profile debug ps
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: restart does not apply changes.** In `~/lab/shop`, change `LOG_LEVEL` in
`web.env` to `debug`, then:

```bash
docker compose restart web
docker compose exec web env | grep LOG_LEVEL        # still info
docker compose up -d
docker compose exec web env | grep LOG_LEVEL        # now debug: container was recreated
```

**Step 2 — Override for production.** Create `compose.prod.yaml` that removes the host port and
adds Traefik labels:

```yaml
services:
  web:
    ports: !reset []
    labels:
      - traefik.enable=true
      - traefik.http.routers.shop.rule=Host(`shop.example.com`)
      - traefik.http.services.shop.loadbalancer.server.port=8000
```

Render it with `docker compose -f compose.yaml -f compose.prod.yaml config` and confirm `ports`
is gone and labels are present.

**Step 3 — Profiles.** `docker compose --profile debug up -d`, open
`http://127.0.0.1:18080` through an SSH tunnel, then `docker compose --profile debug down`.
Finally `docker compose down` (no `-v`) to clean up.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Change made, nothing happened | used `restart`; run `docker compose up -d` | this topic |
| Production unexpectedly has dev settings | a stray `compose.override.yaml` on the server; `docker compose config` | this topic |
| Old containers keep running after a service was renamed | `docker compose up -d --remove-orphans` | this topic |
| Database empty after "cleanup" | someone ran `down -v`; restore from dump | section 8 |

**Why it matters for troubleshooting.** Most Compose incidents are "the running state does not
match the file". `docker compose config` shows the file's intent, `docker compose ps` and
`docker inspect` show reality; the difference is your bug.

**Next step:** budgets and restarts: resource limits and restart policies.

---

## 10. Resources and restart policies

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine: Restart Policies ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)), then Docker Engine – Security: resource limits for CPU and memory ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: this section, then [Memory](04-memory.md) for the kernel OOM killer · 3) Practice: the OOM lab below, then the OOMKilled scenario in the [Containers playbook](26-playbook-containers-k8s.md).

### Memory, CPU, PIDs and ulimits

**Level:** [L2 · Mid]

**Concept.** Without limits, one container can take the whole host: a memory leak triggers the
**host** OOM killer, which may kill a neighbour (or your SSH session) instead of the culprit. With
limits, each container has its own budget enforced by its cgroup (section 2). Flags map directly
to cgroup v2 files:

| Flag (`docker run`) | Compose | cgroup v2 file | Behaviour at the limit |
|---|---|---|---|
| `-m 512m` | `deploy.resources.limits.memory` or `mem_limit` | `memory.max` | reclaim cache, then OOM kill inside the container |
| `--memory-swap 512m` | `memswap_limit` | `memory.swap.max` | total memory+swap; equal to `-m` means no swap |
| `--memory-reservation 256m` | `deploy.resources.reservations.memory` | `memory.low` | soft protection under host pressure |
| `--cpus 1.5` | `deploy.resources.limits.cpus` | `cpu.max` (`150000 100000`) | throttled, never killed |
| `--cpu-shares 512` | `cpu_shares` | `cpu.weight` | relative share, only matters under contention |
| `--cpuset-cpus 0,1` | `cpuset` | `cpuset.cpus` | pinned to those CPUs |
| `--pids-limit 200` | `pids_limit` | `pids.max` | `fork` fails with EAGAIN |
| `--ulimit nofile=65536:65536` | `ulimits:` | (rlimit, not a cgroup) | `Too many open files` |

Runtimes need to know their budget: the JVM reads cgroup limits (tune with
`-XX:MaxRAMPercentage=75`); Node.js heap size should be set explicitly with
`--max-old-space-size` (in MB, below the container limit); Gunicorn memory is roughly
workers × per-worker size, so the worker count is a memory setting. The default open-files limit
inside containers has changed between Engine/containerd versions: check it
(`docker run --rm alpine:3.20 sh -c 'ulimit -n'`) and set it explicitly for proxies and databases.

**OOM behaviour.** When a cgroup hits `memory.max` and cannot reclaim, the kernel OOM killer picks
a victim **inside that cgroup**:

- If the victim is **PID 1**, the container exits with **137** and `State.OOMKilled` is `true`; a restart policy brings it back, so you see a loop of 137s.
- If the victim is a **child** (a Gunicorn worker, a PHP-FPM child), the container keeps running, the parent respawns the child, and users see sporadic 502s. Only `docker events` (`oom`), `memory.events` (`oom_kill` count) and the kernel log show it.
- Without limits, the **host** OOM killer chooses among all processes on the host. dockerd and containerd run with a negative `oom_score_adj`, so containers die first.

**Key terms:** *`memory.max`* (the hard memory limit set by `--memory`), *memory reservation* (a soft target used under host pressure), *`--cpus`* (a CFS quota, a hard cap), *`--cpu-shares`* (a relative weight that only matters under contention), *throttling* (`nr_throttled` in `cpu.stat`), *OOMKilled / exit 137* (the kernel killed the container's process at its memory limit).

**See it on a real system**

```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}\t{{.PIDs}}'
docker inspect CONTAINER --format 'mem={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}} nanocpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}'
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' CONTAINER).scope
cat "$CG"/memory.events
journalctl -k -b --no-pager | grep -iE 'out of memory|oom-kill|killed process' | tail -5
docker events --since 24h --filter event=oom --until "$(date +%s)"
```

```
Memory cgroup out of memory: Killed process 61234 (python) total-vm:224876kB, anon-rss:64412kB, file-rss:9216kB, shmem-rss:0kB, UID:0 pgtables:204kB oom_score_adj:0
```

→ "Memory **cgroup** out of memory" means a container limit; plain "Out of memory: Killed
process" means the whole host ran out.

**Hands-on lab (test VM only)**

**Step 1 — Break it: the main process exceeds its limit.**

```bash
docker run --name oom1 -m 64m --memory-swap 64m python:3.12-slim \
  python -c "x = b'x' * (200 * 1024 * 1024)"
docker inspect oom1 --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}'
```

```
exit=137 oom=true
```

**Step 2 — Break it: a child is killed, the container survives.**

```bash
docker run -d --name oom2 -m 64m --memory-swap 64m python:3.12-slim \
  sh -c 'python -c "x = b\"x\" * (200 * 1024 * 1024)"; echo "child exited with $?"; sleep 600'
sleep 5; docker ps --filter name=oom2 --format '{{.Status}}'; docker logs oom2
CG=/sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' oom2).scope
grep oom_kill "$CG"/memory.events
```

```
Up 6 seconds
child exited with 137
oom_kill 1
```

→ The container is "Up" and would look healthy on a dashboard that only checks status. Whether
`State.OOMKilled` flips for a child kill depends on the Engine version, so do not rely on it alone;
`memory.events`, `docker events` and the kernel log are authoritative.

**Step 3 — Fix it.** First find out *why* memory grows (a leak, too many workers, an unbounded
cache); only then raise the limit, live if needed:

```bash
docker update -m 256m --memory-swap 256m oom2
docker rm -f oom1 oom2
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Exited (137)` loop | `docker inspect C --format '{{.State.OOMKilled}}'`, `journalctl -k -b` | [Containers playbook](26-playbook-containers-k8s.md), [Memory](04-memory.md) |
| Random 502s, container never restarts | `grep oom_kill CG/memory.events`, `docker events --filter event=oom` | [Site-down playbook](25-playbook-site-down.md) |
| Slow with idle host CPU | `grep throttled CG/cpu.stat` | [Slow system playbook](23-playbook-slow-system.md) |
| `Too many open files` | `docker exec C sh -c 'ulimit -n'`; set `--ulimit nofile=` | [Kernel reference](13-kernel-system.md) |
| Host OOM kills random containers | no limits set; `docker stats` to find the hog | [Memory](04-memory.md) |

**Why it matters for troubleshooting.** Exit 137 has two causes (OOM, stop timeout) and a
silent cousin (a child OOM kill). Knowing which you face decides between "fix the leak", "fix
signal handling" and "raise the limit".

**Next step:** what Docker does after a container dies: restart policies.

### Restart policies

**Level:** [L1 · Junior]

**Concept.** A restart policy tells dockerd what to do when a container's main process exits, and
whether to start it when the daemon starts (for example after a reboot).

| Policy | Restarts after a crash | After `docker stop`, then daemon restart/reboot | Use for |
|---|---|---|---|
| `no` (default) | no | stays stopped | one-off jobs, debugging |
| `on-failure[:N]` | only on non-zero exit, at most N times | stays stopped | jobs that may fail transiently |
| `always` | yes | **starts again** | rarely what you want |
| `unless-stopped` | yes | stays stopped (respects your manual stop) | long-running services |

Details that matter: restarts use an increasing delay (doubling from 100 ms, capped), which is
why a crash-looping container shows `Restarting (1) 40 seconds ago`; the delay resets once the
container has run for 10 seconds; `--rm` and a restart policy cannot be combined. In **Swarm**
(and therefore Dokploy apps) the equivalent is `deploy.restart_policy`, and failed tasks are
replaced by new containers rather than restarted in place. Do not wrap a container with a
restart policy in a systemd unit that also restarts it; two supervisors fight each other.

**Key terms:** *restart policy* (`no`, `on-failure[:N]`, `always`, `unless-stopped`), *backoff* (the growing delay between restarts), *`deploy.restart_policy`* (the Swarm equivalent, used by stacks and Dokploy services).

**See it on a real system**

```bash
docker inspect CONTAINER --format '{{.HostConfig.RestartPolicy.Name}}:{{.HostConfig.RestartPolicy.MaximumRetryCount}} count={{.RestartCount}}'
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -i restarting
docker update --restart unless-stopped CONTAINER     # change it live
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: a capped crash loop.**

```bash
docker run -d --name flaky --restart on-failure:3 alpine:3.20 sh -c 'echo "start $(date +%T)"; exit 1'
sleep 20; docker logs flaky
docker inspect flaky --format 'status={{.State.Status}} restarts={{.RestartCount}}'
```

```
start 12:30:01
start 12:30:01
start 12:30:02
start 12:30:02
status=exited restarts=3
```

**Step 2 — Compare `always` and `unless-stopped` across a daemon restart.**

```bash
docker run -d --name p-always  --restart always         nginx:1.27
docker run -d --name p-unless  --restart unless-stopped nginx:1.27
docker stop p-always p-unless
sudo systemctl restart docker
docker ps -a --filter name=p- --format '{{.Names}} {{.Status}}'
```

```
p-unless Exited (0) 15 seconds ago
p-always Up 3 seconds
```

→ `always` resurrected a container you stopped on purpose. During an incident ("I stopped the
broken app, why is it back after the reboot?") this is the answer.

**Step 3 — Fix and clean up.** Use `unless-stopped` for services; `docker rm -f flaky p-always p-unless`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| `Restarting (1) N seconds ago` forever | `docker logs --tail 50 C`; fix the crash, the policy only hides it | [Containers playbook](26-playbook-containers-k8s.md) |
| Stopped container came back after reboot | `docker inspect C --format '{{.HostConfig.RestartPolicy.Name}}'` (always) | this topic |
| Containers did not come back after reboot | policy `no`, or docker.service disabled: `systemctl is-enabled docker` | [Services & systemd](07-services-systemd.md) |

**Why it matters for troubleshooting.** A restart policy converts a crash into a loop; the loop is
the symptom, the exit code and logs are the cause. Read `docker logs --tail` from the latest
attempt before anything else.

**Next step:** where images come from and go to: registries and Harbor.

---

## 11. Registries and Harbor

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Registry ([note](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page)) · 2) KodeKloud: *Docker Certified Associate* — Authenticating to Registries and Docker Image Registry ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Docker-Image-Registry/page)) · 3) KodeKloud has no Harbor course: read the Harbor docs ([docs](https://goharbor.io/docs/)) and *Configure HTTPS Access to Harbor* ([docs](https://goharbor.io/docs/2.15.0/install-config/configure-https/)), with the LFCS lesson *Work With SSL Certificates* ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 4) Note: this section · 5) Practice: the GitLab CI drill at the end of this section; Trivy returns in *Certified Kubernetes Security Specialist (CKS)* — Supply Chain Security, after CKA ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)).

### Image names, login, push and pull

**Level:** [L1 · Junior]

**Concept.** A full image reference is
`REGISTRY[:PORT]/NAMESPACE/REPOSITORY[:TAG][@sha256:DIGEST]`. Missing parts get defaults:
registry `docker.io`, namespace `library`, tag `latest`. The **first** path component decides the
registry, so `harbor.example.com/shop/web` goes to Harbor while `shop/web` silently goes to Docker
Hub.

| You type | Docker uses |
|---|---|
| `nginx` | `docker.io/library/nginx:latest` |
| `bitnami/redis:7.4` | `docker.io/bitnami/redis:7.4` |
| `harbor.example.com/shop/web:3f9c2a1` | Harbor, project `shop`, repository `web` |
| `harbor.example.com:8443/shop/web@sha256:9b1e…` | Harbor on port 8443, exact digest |

`docker login` stores credentials in `~/.docker/config.json` of the user who ran it (root's file
for `sudo docker login`), only base64-encoded unless a credential helper (`credsStore`) is
configured. Anonymous pulls from Docker Hub are rate-limited; busy CI runners and Swarm nodes hit
`toomanyrequests`. On-prem, the fix is a Harbor **proxy cache** project, so every node pulls Hub
images through Harbor by naming the project (`harbor.example.com/PROXY_PROJECT/library/nginx:1.27`),
or a plain pull-through mirror configured in `registry-mirrors` (section 12). Note that
`registry-mirrors` cannot point at a Harbor proxy-cache project directly: it accepts only a
registry root without a path, while Harbor serves the cache under the project name.

**Key terms:** *registry host* (the first path component when it contains a dot, a colon or is `localhost`), *repository* (`PROJECT/NAME` in Harbor), *tag* (a movable name) and *digest* (immutable content hash), *credential store* (`~/.docker/config.json` or a credential helper), *`--password-stdin`* (keeps the secret out of the process list and shell history).

**See it on a real system**

```bash
jq '.auths | keys' ~/.docker/config.json             # which registries this user is logged in to
docker login harbor.example.com
docker tag shop-web:dev harbor.example.com/shop/web:3f9c2a1
docker push harbor.example.com/shop/web:3f9c2a1
docker buildx imagetools inspect harbor.example.com/shop/web:3f9c2a1
```

```
[
  "harbor.example.com"
]
WARNING! Your password will be stored unencrypted in /home/ops/.docker/config.json.
Login Succeeded
The push refers to repository [harbor.example.com/shop/web]
5f70bf18a086: Pushed
b1c9e2a7d3f4: Pushed
8d4a2c1e9f0b: Layer already exists
3f9c2a1: digest: sha256:9b1e7c0a4d2f6e8b1a3c5d7e9f0b2d4c6e8a0b1c3d5e7f9a2b4c6d8e0f1a3b5c size: 1784
```

→ The digest printed by `docker push` is what you record in the release note and what you
roll back to.

**Hands-on lab (test VM only)**

**Step 1 — Build it: a local registry.**

```bash
docker run -d --name registry -p 5000:5000 registry:2
docker tag alpine:3.20 localhost:5000/lab/alpine:3.20
docker push localhost:5000/lab/alpine:3.20
curl -s http://localhost:5000/v2/_catalog
```

**Step 2 — Break it: push from another host over plain HTTP.** On lab2:

```bash
docker tag alpine:3.20 192.168.56.11:5000/lab/alpine:3.20
docker push 192.168.56.11:5000/lab/alpine:3.20
```

```
Get "https://192.168.56.11:5000/v2/": http: server gave HTTP response to HTTPS client
```

→ Docker insists on TLS for every registry except localhost. The lab-only escape hatch is
`"insecure-registries": ["192.168.56.11:5000"]` in daemon.json; the real fix is TLS with a CA
the nodes trust (next topic).

**Step 3 — Clean up.** `docker rm -f registry` on lab1.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `toomanyrequests: You have reached your unauthenticated pull rate limit` | pull through a Harbor proxy cache or `registry-mirrors` | section 12 |
| `manifest unknown` / `not found` | tag typo or deleted: `docker buildx imagetools inspect IMAGE` | [Containers playbook](26-playbook-containers-k8s.md) |
| `no matching manifest for linux/amd64` | image built for arm64 only (section 1) | section 1 |
| `http: server gave HTTP response to HTTPS client` | registry has no TLS; add TLS | next topic |
| Push went to Docker Hub instead of Harbor | the reference has no registry host in front | this topic |

**Why it matters for troubleshooting.** Image pull failures stop deployments on every platform
you use (Docker, Dokploy/Swarm, Kubernetes). Reading the exact error text tells you whether the
problem is the name, the auth, the TLS trust or the network.

**Next step:** your registry: Harbor, robot accounts and the private CA.

### Harbor projects, robot accounts and private CA

**Level:** [L3 · Senior]

**Concept.** Harbor is a registry with an access-control and policy layer:

| Harbor feature | What it gives you |
|---|---|
| **Project** | Namespace (`harbor.example.com/shop/…`), public or private, with member roles |
| **Robot account** | Non-human credential scoped to projects and actions (push, pull); the right identity for CI and for servers |
| **Proxy cache project** | Pull-through cache for Docker Hub and other registries |
| **Tag immutability** | Rules that forbid overwriting matching tags (protects release tags) |
| **Tag retention** | Automatic cleanup of old tags (keep the last N builds) |
| **Vulnerability scanning** | Built-in Trivy; scan on push; block pulls above a severity |
| **Replication** | Copy images between registries (DR, another site) |

Robot accounts are named like `robot$PROJECT+NAME` (the `robot$` prefix is configurable). That
`$` is a trap: in a shell, `docker login -u robot$shop+ci` expands `$shop` to nothing. Always
single-quote it, and in GitLab CI store the name in a variable with "Expand variable reference"
turned off (or write `$$`).

**Private CA trust.** Harbor on-prem usually has a certificate from an internal CA. Every client
that talks to it must trust that CA, and each tool has its own trust store:

| Client | Where it looks | Restart needed |
|---|---|---|
| Docker daemon | `/etc/docker/certs.d/HARBOR_HOST/ca.crt` (`HARBOR_HOST:PORT` for a non-443 port) | no |
| Docker daemon, alternative | system store: `/usr/local/share/ca-certificates/*.crt` then `sudo update-ca-certificates` | yes (`systemctl restart docker`) |
| curl, Trivy, git, most CLIs | system store (as above); RHEL: `/etc/pki/ca-trust/source/anchors/` + `update-ca-trust` | no |
| containerd (Kubernetes nodes) | `/etc/containerd/certs.d/HARBOR_HOST/hosts.toml` | no, with the config_path set ([Kubernetes](31-learn-kubernetes.md)) |
| Docker-in-Docker CI jobs | inside the dind service container | rebuild the dind image with the CA |
| Swarm/Dokploy | **every node** that may run the task | no |

**Key terms:** *project* (Harbor's unit of access control, quotas and policies), *robot account* (`robot$PROJECT+NAME`, a scoped token for CI), *private CA* (your own certificate authority), *`/etc/docker/certs.d/HOST/ca.crt`* (per-registry trust for Docker), *`update-ca-certificates`* (the Ubuntu system trust store, used by curl and most tools).

**See it on a real system**

```bash
ls -l /etc/docker/certs.d/harbor.example.com/
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -enddate -ext subjectAltName
curl -sS -o /dev/null -w '%{http_code}\n' https://harbor.example.com/v2/     # 401 = TLS fine, auth needed
echo "$ROBOT_TOKEN" | docker login harbor.example.com -u 'robot$shop+ci' --password-stdin
```

```
-rw-r--r-- 1 root root 1952 Sep 20 09:12 ca.crt
subject=CN = harbor.example.com
issuer=CN = Example Corp Issuing CA 01
notAfter=Mar 18 23:59:59 2027 GMT
X509v3 Subject Alternative Name:
    DNS:harbor.example.com
401
Login Succeeded
```

**Hands-on lab (test VM only): your own CA and a TLS registry**

**Step 1 — Create a CA and a server certificate.**

```bash
mkdir -p ~/lab/ca/certs && cd ~/lab/ca
openssl req -x509 -newkey rsa:4096 -nodes -keyout ca.key -out ca.crt -days 365 -subj "/CN=Lab Root CA"
openssl req -newkey rsa:2048 -nodes -keyout certs/registry.key -out registry.csr -subj "/CN=registry.lab.test"
printf 'subjectAltName=DNS:registry.lab.test\n' > san.ext
openssl x509 -req -in registry.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out certs/registry.crt -days 90 -extfile san.ext
echo "192.168.56.11 registry.lab.test" | sudo tee -a /etc/hosts
```

**Step 2 — Run a TLS registry.**

```bash
docker run -d --name registry -p 443:5000 -v ~/lab/ca/certs:/certs:ro \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registry.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/registry.key registry:2
```

**Step 3 — Break it: an untrusted CA.**

```bash
docker tag alpine:3.20 registry.lab.test/lab/alpine:3.20
docker push registry.lab.test/lab/alpine:3.20
```

```
Get "https://registry.lab.test/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
```

**Step 4 — Fix it for Docker only, then for everything else.**

```bash
sudo mkdir -p /etc/docker/certs.d/registry.lab.test
sudo cp ~/lab/ca/ca.crt /etc/docker/certs.d/registry.lab.test/ca.crt
docker push registry.lab.test/lab/alpine:3.20                  # works, no restart
curl -s https://registry.lab.test/v2/_catalog                  # still fails: curl uses the system store
sudo cp ~/lab/ca/ca.crt /usr/local/share/ca-certificates/lab-root-ca.crt
sudo update-ca-certificates
curl -s https://registry.lab.test/v2/_catalog                  # {"repositories":["lab/alpine"]}
```

**Step 5 — Break it: name mismatch.** Trust the CA for the IP as well, then push by IP:

```bash
sudo mkdir -p /etc/docker/certs.d/192.168.56.11
sudo cp ~/lab/ca/ca.crt /etc/docker/certs.d/192.168.56.11/ca.crt
docker tag alpine:3.20 192.168.56.11/lab/alpine:3.20
docker push 192.168.56.11/lab/alpine:3.20
```

```
tls: failed to verify certificate: x509: cannot validate certificate for 192.168.56.11 because it doesn't contain any IP SANs
```

→ Trust is fine; the certificate simply is not issued for that name. Certificates are issued
for names: use the name (or reissue with the extra SAN).

**Step 6 — Optional, with 4+ GB RAM on lab2:** install Harbor with its installer, create a
private project `shop` and a robot account with push and pull, and repeat the push with
`docker login -u 'robot$shop+ci'`. Then try it unquoted and read the `unauthorized` error.

Clean up: `docker rm -f registry`, remove the hosts line, and on a lab VM you may keep the lab CA
trusted or remove `/usr/local/share/ca-certificates/lab-root-ca.crt` and run
`sudo update-ca-certificates --fresh`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `x509: certificate signed by unknown authority` | `ls /etc/docker/certs.d/HOST/`; `openssl s_client … -showcerts` | [Containers playbook](26-playbook-containers-k8s.md), [Web & TLS](18-web-http-tls.md) |
| `x509: certificate is valid for X, not Y` | `openssl x509 -noout -ext subjectAltName` | [Web & TLS](18-web-http-tls.md) |
| `x509: certificate has expired or is not yet valid` on a valid cert | `timedatectl` (clock skew) | [Time & NTP](12-time-ntp.md) |
| `unauthorized: unauthorized to access repository: shop/web, action: push` | robot account lacks push on that project, or the `$` in its name was expanded | this topic |
| `unauthorized: authentication required` on a Swarm node | service created without `--with-registry-auth` | section 14 |
| Pull works with docker, fails on Kubernetes | containerd has its own trust (`/etc/containerd/certs.d/`) | [Kubernetes](31-learn-kubernetes.md) |

**Why it matters for troubleshooting.** "Works on one node, fails on another" with a private
registry is nearly always trust or credentials on that node. Check the node, not the registry.

**Next step:** make the registry a security gate: scanning and signing.

### Scanning and signing: Trivy and Cosign

**Level:** [L3 · Senior]

**Concept.** **Trivy** scans an image's OS packages and language dependencies against vulnerability
databases (and Dockerfiles/IaC for misconfigurations). Run it in CI as a gate and let Harbor scan
on push as a second line. **Cosign** signs an image digest with a key so a deployer can verify
the image came from your pipeline and was not swapped in the registry. Harbor stores Cosign
signatures next to the image and can refuse unsigned or vulnerable images per project.

| Command | Use |
|---|---|
| `trivy image IMAGE` | Full report |
| `trivy image --severity HIGH,CRITICAL --ignore-unfixed IMAGE` | Only actionable findings |
| `trivy image --exit-code 1 --severity CRITICAL IMAGE` | CI gate: non-zero exit fails the job |
| `trivy config Dockerfile` | Dockerfile misconfigurations (root user, no healthcheck…) |
| `trivy fs .` | Dependencies in a source tree (lockfiles) |
| `cosign generate-key-pair` | Creates `cosign.key` (protect it) and `cosign.pub` |
| `cosign sign --key cosign.key IMAGE@sha256:DIGEST` | Sign a digest, never a tag |
| `cosign verify --key cosign.pub IMAGE:TAG` | Verify before deploying |

**Key terms:** *CVE* (a published vulnerability), *severity* (LOW to CRITICAL), *`--ignore-unfixed`* (hide findings that have no fix yet), *SBOM* (the list of packages in an image), *signature* (a Cosign proof that a digest came from your pipeline).

**See it on a real system**

```bash
trivy image --severity HIGH,CRITICAL --ignore-unfixed shop-web:dev
trivy image --severity HIGH,CRITICAL --ignore-unfixed python:3.12 | grep Total
trivy image --severity HIGH,CRITICAL --ignore-unfixed python:3.12-slim | grep Total
```

```
shop-web:dev (debian 12.7)
==========================
Total: 2 (HIGH: 2, CRITICAL: 0)

┌───────────┬────────────────┬──────────┬────────┬───────────────────┬──────────────────┬────────────────────────┐
│ Library   │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version    │ Title                  │
├───────────┼────────────────┼──────────┼────────┼───────────────────┼──────────────────┼────────────────────────┤
│ libexpat1 │ CVE-YYYY-NNNNN │ HIGH     │ fixed  │ 2.5.0-1           │ 2.5.0-1+deb12u1  │ expat: example issue   │
│ libssl3   │ CVE-YYYY-MMMMM │ HIGH     │ fixed  │ 3.0.14-1~deb12u1  │ 3.0.15-1~deb12u1 │ openssl: example issue │
└───────────┴────────────────┴──────────┴────────┴───────────────────┴──────────────────┴────────────────────────┘
Total: 412 (HIGH: 389, CRITICAL: 23)
Total: 6 (HIGH: 6, CRITICAL: 0)
```

→ The full `python:3.12` image carries hundreds of findings the slim image does not: base image
choice is your biggest lever. "fixed" status means rebuilding with a fresh base
(`docker build --pull`) removes it.

**Hands-on lab (test VM only)**

**Step 1 — Gate a build.** `trivy image --exit-code 1 --severity CRITICAL python:3.12; echo "exit=$?"`
shows how a CI job would fail.

**Step 2 — Fix it the right way.** Switch to the slim base, rebuild with `--pull`, rescan. Only if
a finding is a false positive or has no fix, add it to `.trivyignore` with a comment and a review
date; never raise the gate to make the build green.

**Step 3 — Sign and verify** (against the TLS lab registry from the previous topic):

```bash
cosign generate-key-pair                                  # prompts for a password
DIGEST=$(docker buildx imagetools inspect registry.lab.test/lab/alpine:3.20 | awk '/^Digest:/ {print $2}')
cosign sign --key cosign.key "registry.lab.test/lab/alpine@$DIGEST"
cosign verify --key cosign.pub registry.lab.test/lab/alpine:3.20 >/dev/null && echo verified
```

> By default Cosign also uploads a record of every signature (image name and digest included) to
> the **public** Sigstore transparency log, and `verify` expects to find it there. For private
> on-prem images, sign with `--tlog-upload=false` and verify with `--insecure-ignore-tlog=true`, or
> run your own Rekor. Flag names and defaults have shifted between Cosign 2 and 3, so check
> `cosign sign --help` for your version before putting it in CI.

**Step 4 — Break it.** Push a different image under the same tag and run `cosign verify` again:
it fails, because the signature belongs to the old digest. That is the attack signing detects.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| CI fails on a new CRITICAL overnight | rebuild with `--pull`; the base image published a fix | [CI/CD & SRE](33-learn-cicd-iac-sre.md) |
| Harbor refuses the pull: vulnerability policy | Harbor project settings; rescan after rebuild | this topic |
| `cosign verify`: `no matching signatures` | tag now points to another digest, or wrong public key | this topic |
| Trivy cannot reach Harbor: x509 | Trivy uses the system trust store; add the CA there | previous topic |

**Why it matters for troubleshooting.** A security gate that fails a hotfix pipeline at 2 a.m. is
an operational event. Know how to read the report, how to fix by rebuilding, and how to record an
exception properly.

**Next step:** wire it all into the L3 drill: a GitLab pipeline that pushes to Harbor.

### Drill: GitLab CI builds and pushes to Harbor

**Level:** [L3 · Senior]

**Concept.** CI turns the Dockerfile into an artifact with an identity: one image per commit, named
by its short SHA, pushed to a registry the servers trust, scanned before anyone deploys it.

This is the L3 drill "Write a GitLab CI pipeline that builds an image, tags it with the commit SHA
and pushes it to Harbor". Start with the GitLab CI quick start
(https://docs.gitlab.com/ci/quick_start/) if you have never written a pipeline; the full CI/CD
material is in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

**Runner choice.** The simplest reliable setup on-prem is a dedicated VM with Docker, a GitLab
Runner using the **shell executor**, and the Harbor CA already trusted (Harbor topic above). Docker-in-
Docker works too, but the dind service then needs the CA baked into its own image and an explicit
`--dns` (it is the "Docker-in-Docker fell back to 8.8.8.8" case from your Ops Ladder).

> The `gitlab-runner` user must be in the `docker` group for a shell executor, which makes every
> pipeline root on that VM (section 13). Use a dedicated runner VM, never your Dokploy host.

**Key terms:** *runner* (the machine that executes jobs), *executor* (shell, docker or kubernetes:
how a job runs), *`CI_COMMIT_SHORT_SHA`* (the predefined variable used as the image tag), *masked /
protected variable* (hidden in logs / only on protected branches), *robot account* (Harbor's CI
identity).

**CI/CD variables** (Settings → CI/CD → Variables): `HARBOR_HOST` = `harbor.example.com`;
`HARBOR_USER` = `robot$shop+gitlab-ci` with "Expand variable reference" **off**; `HARBOR_PASSWORD`
= the robot token, **masked** and **protected**.

```yaml
# .gitlab-ci.yml
stages: [test, build, scan]

variables:
  IMAGE: "$HARBOR_HOST/shop/web"

test:
  stage: test
  tags: [docker-shell]
  script:
    - docker build --target test -t "web-test:$CI_COMMIT_SHORT_SHA" .   # needs a "test" stage in the Dockerfile

build:
  stage: build
  tags: [docker-shell]
  script:
    - echo "$HARBOR_PASSWORD" | docker login "$HARBOR_HOST" -u "$HARBOR_USER" --password-stdin
    - docker build --pull --build-arg GIT_SHA="$CI_COMMIT_SHORT_SHA" -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
    - |
      if [ "$CI_COMMIT_BRANCH" = "$CI_DEFAULT_BRANCH" ]; then
        docker tag "$IMAGE:$CI_COMMIT_SHORT_SHA" "$IMAGE:main"
        docker push "$IMAGE:main"
      fi
  after_script:
    - docker logout "$HARBOR_HOST"        # do not leave robot credentials on a shared runner

scan:
  stage: scan
  tags: [docker-shell]
  script:
    - trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed "$IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Why each choice:** the commit SHA tag never moves, so rollback means "deploy the previous SHA";
`--pull` refreshes the base image so security fixes arrive; `--password-stdin` keeps the token out
of the process list; `main` is a convenience tag for "latest on the default branch", never what
production pins.

**Break it on purpose, then fix:**

| Break | Expected failure | Fix |
|---|---|---|
| Robot name stored with "Expand variable reference" on | `unauthorized` at `docker login` (name lost `$shop`) | turn expansion off |
| Remove `/etc/docker/certs.d/HARBOR_HOST/ca.crt` on the runner | `x509: certificate signed by unknown authority` at push | restore the CA |
| Robot account with pull-only permission | `unauthorized to access repository … action: push` | grant push on the project |
| Introduce a CRITICAL (old base image) | `scan` job fails with exit code 1 | update the base, rebuild |

**Rollback (test it, do not just write it):** find the previous good SHA in Harbor or with
`git log --oneline -5`, deploy `harbor.example.com/shop/web:PREVIOUS_SHA` (in Dokploy: change the
image tag and redeploy; with Compose: `TAG=PREVIOUS_SHA docker compose up -d`), verify with curl and
logs, and write down how long it took.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| Job stuck at `This job is stuck because you don't have any active runners` | runner tags in the job vs the runner (`tags: [docker-shell]`) | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| `permission denied while trying to connect to the Docker daemon socket` | `id gitlab-runner` on the runner VM (not in the `docker` group) | section 13 |
| `x509: certificate signed by unknown authority` at login or push | `ls /etc/docker/certs.d/HARBOR_HOST/` on the runner | Harbor topic above |
| Pipeline green, Dokploy still runs the old code | which tag Dokploy deploys (`main` vs the SHA); `docker service ps SERVICE --no-trunc` | section 14 |

**Why it matters for troubleshooting.** Once every image carries the commit SHA, "what is running
in production?" has a one-command answer, and every rollback is a redeploy of a known digest
instead of a rebuild under pressure.

**Next step:** the daemon configuration that every runner, Swarm node and Dokploy host shares.

---

## 12. The daemon and daemon.json

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine: Docker Service Configuration, Troubleshooting Docker Daemon ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page)), Demo – Docker Debug Mode · 2) Note: this section, then the daemon scenarios in the [Containers playbook](26-playbook-containers-k8s.md) · 3) KodeKloud: *Ansible Basics Course* — Playbooks, Handlers, Templates, for the drill ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · 4) Video: Jeff Geerling *Ansible 101* ([playlist](https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN)) · 5) Practice: the address-pool lab and the Ansible drill below.

### daemon.json keys that matter on-prem

**Level:** [L3 · Senior]

**Concept.** `/etc/docker/daemon.json` is dockerd's configuration file. On-prem hosts need a few
settings that cloud defaults hide: your internal DNS servers, log rotation, a data directory on
the big disk, address pools that do not collide with the corporate network, a registry mirror and
sometimes an HTTP proxy. JSON has no comments, so keep a commented copy in Git (and deploy it
with Ansible, drill below).

```json
{
  "dns": ["192.0.2.53", "192.0.2.54"],
  "log-driver": "json-file",
  "log-opts": { "max-size": "50m", "max-file": "5" },
  "data-root": "/srv/docker",
  "bip": "10.209.0.1/24",
  "default-address-pools": [ { "base": "10.210.0.0/16", "size": 24 } ],
  "registry-mirrors": ["https://hub-mirror.example.com"],
  "proxies": {
    "http-proxy": "http://proxy.example.com:3128",
    "https-proxy": "http://proxy.example.com:3128",
    "no-proxy": "localhost,127.0.0.1,.example.com,10.0.0.0/8"
  },
  "metrics-addr": "127.0.0.1:9323"
}
```

| Key | What it does | On-prem notes |
|---|---|---|
| `dns` | Upstream resolvers for containers (embedded DNS forwards here) | Prevents the 8.8.8.8 fallback (section 7) |
| `log-driver`, `log-opts` | Default logging for new containers | Values are strings; recreate containers to apply |
| `data-root` | Where images, containers and volumes live (default `/var/lib/docker`) | Put it on the large data disk; XFS needs `ftype=1` |
| `bip` | Address of `docker0` and the default bridge subnet | Avoid 172.17.0.0/16 if the LAN or VPN uses it |
| `default-address-pools` | Ranges for networks you and Compose create | The subnet-clash fix (next topic) |
| `live-restore` | Containers keep running while dockerd restarts/upgrades | **Incompatible with Swarm mode**: never on a Dokploy host |
| `registry-mirrors` | Pull-through mirror for **Docker Hub only** | Needs a mirror served at the registry root (for example a `registry` container in proxy mode); a Harbor proxy-cache project lives under a path, so pull it by name instead (section 11) |
| `insecure-registries` | Allow HTTP or untrusted TLS for listed registries | Lab only; trust the CA instead |
| `proxies` | HTTP proxy for the **daemon** (pulls), Engine 23+ | Builds and containers need their own proxy settings |
| `metrics-addr` | Prometheus metrics endpoint for dockerd | Bind to loopback; scrape locally ([Observability](32-learn-performance-observability.md)) |
| `userland-proxy` | Use docker-proxy for published ports (default true) | Leave it unless you know why |
| `ipv6`, `ip6tables` | IPv6 for containers and its firewall rules | Plan before enabling; mirror DOCKER-USER rules |

The workflow, every time:

```bash
sudoedit /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json     # prints "configuration OK"
sudo systemctl restart docker                                      # stops containers unless live-restore
docker info --format 'root={{.DockerRootDir}} log={{.LoggingDriver}} mirrors={{.RegistryConfig.Mirrors}} live={{.LiveRestoreEnabled}}'
journalctl -u docker -b --no-pager | tail -20
```

> Restarting Docker stops every container on the host (without live-restore), and only those with
> a restart policy (or Swarm tasks) come back by themselves. On a production Dokploy host that is an
> outage: schedule it, announce it, and have the rollback (the previous
> daemon.json) ready.

A setting may be given **either** as a dockerd flag in the systemd unit **or** in daemon.json,
never both. The classic case is `hosts`:

```
unable to configure the Docker daemon with file /etc/docker/daemon.json: the following directives are specified both as a flag and in the configuration file: hosts: (from flag: [fd://], from file: [tcp://127.0.0.1:2376])
```

→ Remove it from one side; to change the unit's flags use a drop-in (`sudo systemctl edit docker`)
that clears and redefines `ExecStart=`.

**Moving data-root to a bigger disk** (stop, copy preserving everything, switch, verify, only then
delete the old copy):

```bash
sudo systemctl stop docker.socket docker.service
sudo rsync -aHAXS --numeric-ids /var/lib/docker/ /srv/docker/
# add "data-root": "/srv/docker" to daemon.json, then:
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl start docker
docker info --format '{{.DockerRootDir}}'; docker ps -a; docker volume ls
```

> Delete the old `/var/lib/docker` only after the host has run correctly for days, and only with
> the exact path typed out, never through a variable that might be empty. With the containerd
> image store (section 3), image data lives under containerd's root as well; move it
> consistently or start fresh and re-pull.

**Key terms:** *`dns`* (the upstream resolvers Docker's embedded DNS forwards to), *`log-driver` / `log-opts`* (defaults for new containers), *`data-root`* (where images, containers and volumes live), *`live-restore`* (containers keep running while dockerd restarts), *`registry-mirrors`* (a pull-through cache for Docker Hub), *`dockerd --validate`* (check the file before a restart).

**See it on a real system**

```bash
cat /etc/docker/daemon.json 2>/dev/null || echo "no daemon.json: all defaults"
systemctl cat docker | grep -E '^ExecStart|^Environment'
docker info 2>/dev/null | grep -E 'Server Version|Storage Driver|Logging Driver|Cgroup|Docker Root Dir|Live Restore|Registry Mirrors' -A0
docker info 2>&1 | grep -i warning
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: live-restore on a Swarm host.**

```bash
echo '{ "live-restore": true }' | sudo tee /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker run -d --name lr nginx:1.27
sudo systemctl restart docker && docker ps --filter name=lr --format '{{.Status}}'   # still "Up N minutes"
docker swarm init --advertise-addr 192.168.56.11
```

```
Error response from daemon: --live-restore daemon configuration is incompatible with swarm mode
```

**Step 2 — Fix it.** Choose: live-restore for standalone hosts, Swarm for Dokploy hosts. Remove the
key, validate, restart. `docker rm -f lr`.

**Step 3 — Break it: invalid JSON.** Leave a trailing comma in daemon.json and run the validator;
then (lab only) restart anyway and read `systemctl status docker` and `journalctl -u docker -b`.
You will see dockerd failing to start and every container down. Fix the comma, validate, start.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `docker.service: Failed with result 'exit-code'` after an edit | `sudo dockerd --validate --config-file /etc/docker/daemon.json` | [Containers playbook](26-playbook-containers-k8s.md) |
| `specified both as a flag and in the configuration file` | `systemctl cat docker` | this topic |
| `--live-restore daemon configuration is incompatible with swarm mode` | remove `live-restore` | this topic |
| Pulls fail behind a proxy, curl works | the daemon has no proxy: `docker info --format '{{.HTTPProxy}} {{.HTTPSProxy}} {{.NoProxy}}'` | this topic |
| Containers still use 8.8.8.8 after setting `dns` | containers not recreated, or set on another host | section 7 |

**Why it matters for troubleshooting.** Half of on-prem Docker incidents trace back to a daemon
default that was never changed: no log rotation, wrong DNS, colliding subnets. One validated,
version-controlled daemon.json prevents all three.

**Next step:** the subnet clash in detail, because on-prem it can take the whole host off the
network.

### Address pools and subnet clashes

**Level:** [L3 · Senior]

**Concept.** Every Docker network adds a route on the host (section 7). Docker's default ranges
are 172.17.0.0/16 for `docker0`, then 172.18.0.0/16 through 172.31.0.0/16 and 192.168.0.0/16 (in
/20 pieces) for networks you or Compose create. Swarm overlay networks, including `ingress`, come
from **10.0.0.0/8** in /24 pieces. If any of those overlap a real network your host must reach (an
office LAN, a VPN pool, a monitoring subnet), traffic for those real hosts is routed into the Docker
bridge instead and disappears. Symptoms are bizarre: SSH from the VPN dies right after a
`docker compose up`, monitoring loses the host, one client network cannot reach the site.

```
 before:  198.51.100.0/24 (office VPN) ── via default gateway ──▶ reachable
 after "docker compose up" picked 198.51.100.0/24 for its network (pretend):
          ip route:  198.51.100.0/24 dev br-5e1a…   ◀── more specific than the default route
          replies to VPN users go into an empty bridge ──▶ their SSH sessions hang
```

Prevention: pick ranges nobody uses, write them into daemon.json **before** creating networks, and
pass a Swarm pool at `docker swarm init`. Existing networks keep their subnets; changing pools
only affects networks created afterwards.

```bash
# daemon.json (local bridges):  "bip": "10.209.0.1/24",
#                               "default-address-pools": [ { "base": "10.210.0.0/16", "size": 24 } ]
# Swarm (overlay, at init):
docker swarm init --advertise-addr 192.0.2.10 \
  --default-addr-pool 10.220.0.0/16 --default-addr-pool-mask-length 24
```

**Key terms:** *`bip`* (docker0's own address and subnet), *`default-address-pools`* (where new bridge networks take their subnets), *`--default-addr-pool`* (the Swarm overlay pool, set at `docker swarm init`), *route hijack* (a Docker subnet overlapping a real network you must reach), *`docker_gwbridge`* (the bridge that gives Swarm containers outbound access).

**See it on a real system**

```bash
ip route | grep -E 'docker0|br-|docker_gwbridge'
docker network ls -q | xargs docker network inspect --format '{{.Name}} {{.Driver}} {{range .IPAM.Config}}{{.Subnet}} {{end}}'
ip route get 172.20.5.10                       # which interface would carry traffic to this real host?
docker network inspect ingress --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null
```

```
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev docker_gwbridge proto kernel scope link src 172.18.0.1
172.20.0.0/16 dev br-5e1a7c2d9b04 proto kernel scope link src 172.20.0.1
bridge bridge 172.17.0.0/16
shop_backend bridge 172.20.0.0/16
ingress overlay 10.0.0.0/24
dokploy-network overlay 10.0.1.0/24
172.20.5.10 dev br-5e1a7c2d9b04 src 172.20.0.1 uid 1000
10.0.0.0/24
```

→ If 172.20.5.10 is a real server on your LAN, this host can no longer reach it: the route points
into the `shop_backend` bridge. And `ingress`/`dokploy-network` sit in 10.0.0.0/24 and 10.0.1.0/24:
fine only if no 10.0.x.0/24 network matters to this host.

**Hands-on lab (test VM only)**

**Step 1 — Break it (safely).** Pretend 198.51.100.0/24 is your office VPN:

```bash
ip route get 198.51.100.20                      # before: via your default gateway
docker network create --subnet 198.51.100.0/24 clash
ip route get 198.51.100.20                      # after: dev br-… — hijacked
```

**Step 2 — Fix it.** Remove the clashing network, set address pools, restart, and create networks
again:

```bash
docker network rm clash
echo '{ "bip": "10.209.0.1/24", "default-address-pools": [ { "base": "10.210.0.0/16", "size": 24 } ] }' \
  | sudo tee /etc/docker/daemon.json
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker network create poolcheck && docker network inspect poolcheck --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
ip -br addr show docker0
docker network rm poolcheck
```

```
10.210.0.0/24
docker0          DOWN           10.209.0.1/24
```

**Step 3 — Swarm ingress (read, then practise on the lab).** The routing-mesh network is
recreated like this, after removing every service that publishes ports through it:

> Removing `ingress` breaks every published Swarm port until it is recreated and services are
> redeployed. On a real Dokploy host this is a maintenance-window change with a rollback plan.

```bash
docker network rm ingress
docker network create --driver overlay --ingress --subnet 10.221.0.0/24 --gateway 10.221.0.1 ingress
```

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| SSH from VPN dies after a deploy | `ip route get VPN_CLIENT_IP` from the host's console | [Site-down playbook](25-playbook-site-down.md) |
| One remote network cannot reach the host, others can | `ip route get REMOTE_IP`, then `ip route | grep br-` | [Network reference](02-network.md) |
| Pools changed, old networks unchanged | expected; recreate them (`docker compose down && docker compose up -d`) | this topic |

**Why it matters for troubleshooting.** This failure looks like a network outage but lives
entirely on the host's routing table. `ip route get` is the one-line test, and it belongs in your
Dokploy pre-install checklist ([Apache 443 case](21-case-apache-443-dokploy.md)).

**Next step:** make the daemon configuration repeatable with Ansible.

### Drill: Ansible installs Docker with your daemon.json

**Level:** [L3 · Senior]

**Concept.** A daemon.json you typed by hand exists on one host. The same file rendered by an
idempotent playbook exists on every host, is reviewed in Git, and is validated before Docker ever
reads it.

This is the L3 drill "Write an Ansible playbook that installs Docker with your daemon.json (DNS
servers and log rotation) on a fresh VM". If Ansible is new, watch the first episodes of Jeff
Geerling's Ansible 101
(https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN) first.

**Key terms:** *inventory* (the hosts Ansible manages), *idempotent* (a second run changes nothing),
*handler* (a task that runs only when notified, here "restart docker"), *`validate:`* (a command that
must accept the new file before it replaces the live one), *`--check --diff`* (preview changes).

`inventory.ini`:

```ini
[docker_hosts]
lab1 ansible_host=192.168.56.11
lab2 ansible_host=192.168.56.12
```

`docker.yml`:

```yaml
- name: Install Docker Engine with our daemon.json
  hosts: docker_hosts
  become: true
  vars:
    docker_daemon_json:
      dns: ["192.0.2.53", "192.0.2.54"]           # your internal resolvers
      log-driver: json-file
      log-opts: { max-size: "50m", max-file: "5" }
      bip: "10.209.0.1/24"
      default-address-pools:
        - { base: "10.210.0.0/16", size: 24 }
  tasks:
    - name: Prerequisites
      ansible.builtin.apt:
        name: [ca-certificates, curl]
        state: present
        update_cache: true

    - name: Keyring directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"

    - name: Docker apt signing key
      ansible.builtin.get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: /etc/apt/keyrings/docker.asc
        mode: "0644"

    - name: Docker apt repository
      ansible.builtin.apt_repository:
        repo: >-
          deb [arch={{ 'arm64' if ansible_architecture == 'aarch64' else 'amd64' }}
          signed-by=/etc/apt/keyrings/docker.asc]
          https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable
        filename: docker
        state: present

    - name: Docker packages
      ansible.builtin.apt:
        name: [docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]
        state: present
        update_cache: true

    - name: /etc/docker exists
      ansible.builtin.file:
        path: /etc/docker
        state: directory
        mode: "0755"

    - name: daemon.json, validated before it replaces the live file
      ansible.builtin.copy:
        dest: /etc/docker/daemon.json
        content: "{{ docker_daemon_json | to_nice_json }}\n"
        mode: "0644"
        validate: dockerd --validate --config-file %s
      notify: Restart docker

    - name: Docker enabled and running
      ansible.builtin.systemd:
        name: docker
        state: started
        enabled: true

  handlers:
    - name: Restart docker
      ansible.builtin.systemd:
        name: docker
        state: restarted
```

**Run it, prove idempotency, break it, fix it:**

```bash
ansible-playbook -i inventory.ini docker.yml --diff          # first run: many "changed"
ansible-playbook -i inventory.ini docker.yml                 # second run must report changed=0
ssh lab1 "docker info --format '{{.LoggingDriver}}'; docker run --rm alpine:3.20 cat /etc/resolv.conf"
```

```
PLAY RECAP *********************************************************************
lab1 : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
lab2 : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Break it: change `max-file: "5"` to `max-file: 5` (a number) and rerun. The `validate` step fails,
the live daemon.json is **not** replaced and Docker is **not** restarted: a broken config never
reaches the host. Fix the quotes and rerun. That `validate:` line is the most valuable line in the
playbook.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Second run still reports `changed` | `ansible-playbook … --diff` and read which task changes every time (a `shell:` task without `creates:`?) | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| `UNREACHABLE! … Permission denied (publickey)` | `ssh -v lab1` with the same user and key | [SSH](09-ssh-remote-access.md) |
| Docker restarted on every run | the handler is notified by a task that always changes | this drill |
| `docker.service` fails after the play | `sudo journalctl -u docker -n 30` on the host; `dockerd --validate` | daemon.json topic above |

**Why it matters for troubleshooting.** A host you can rebuild from a playbook is a host you can
replace instead of repair at 3 a.m., and the validate step means one typo can no longer take every
container on a host down at once.

**Next step:** security. Everything in this section ran as root through the Docker socket; section
13 explains why that matters and how to shrink it.

---

## 13. Security

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine – Security (namespaces, capabilities, cgroups) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: this section, then [Users & permissions](10-users-permissions-security.md) · 3) After CKA: *Certified Kubernetes Security Specialist (CKS)* — System Hardening and Supply Chain Security ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Practice: the socket-escape and hardening labs below on a test VM; rootless setup from the Docker docs (https://docs.docker.com/).

### The docker group and the socket are root

**Level:** [L1 · Junior]

**Concept.** Whoever can talk to the Docker API can start a container that mounts the host's `/`,
runs privileged, or joins the host's namespaces. So membership of the `docker` group, access to
`/var/run/docker.sock`, and any container that has the socket mounted are all **root on the
host**. Mounting the socket `:ro` does not help: read-only applies to the socket *file*, not to
the API calls sent through it. An API exposed on TCP 2375 without TLS is remote root for anyone who
can reach it, and scanners look for it constantly.

```
 user in group docker ──▶ docker run -v /:/host … chroot /host ──▶ root shell on the host
 Traefik / Dokploy / Portainer with docker.sock mounted ──▶ a bug in them = root on the host
 dockerd -H tcp://0.0.0.0:2375 (no TLS) ──▶ anyone on the network = root on the host
```

Mitigations, in order of value: keep the `docker` group to admins who already have sudo; reach
remote engines over SSH (`docker context create lab2 --docker host=ssh://USER@lab2`) instead of
TCP; give socket-hungry tools only what they need (Traefik's Docker provider only reads; a
filtering socket proxy can enforce that); run CI builds on dedicated VMs; consider rootless mode
where its limits are acceptable (last topic of this section).

**Key terms:** *`/var/run/docker.sock`* (the Docker API socket), *docker group* (members may use the socket, so they are root-equivalent), *TCP 2375 / 2376* (the API without / with TLS), *socket proxy* (a filter that allows only selected API calls).

**See it on a real system**

```bash
getent group docker                                    # who is effectively root
sudo ss -ltnp | grep -E ':2375|:2376'                  # API on TCP?
systemctl cat docker | grep ExecStart                  # -H flags
docker ps -q | xargs -r docker inspect --format '{{.Name}}{{range .Mounts}}{{if eq .Destination "/var/run/docker.sock"}} has docker.sock{{end}}{{end}}'
```

```
docker:x:999:ops,gitlab-runner
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
/dokploy-traefik has docker.sock
/shop-web-1
```

**Hands-on lab (test VM only)**

**Step 1 — Break it: become root through the docker group.** As a non-sudo user who is in the
`docker` group:

```bash
docker run --rm -it -v /:/host alpine:3.20 chroot /host /bin/bash -c 'id; tail -1 /etc/shadow'
```

```
uid=0(root) gid=0(root) groups=0(root)
lab:$y$j9T$…:20004:0:99999:7:::
```

→ A user who could not read `/etc/shadow` now can, and could add an SSH key for root just as
easily.

**Step 2 — Fix it.** Remove users who do not need it (`sudo gpasswd -d USER docker`), require
`sudo docker …` for humans (logged in the journal), and record the decision in your security notes.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Unknown containers mining crypto | `sudo ss -ltnp | grep 2375` is in the playbook; here: `systemctl cat docker` for `-H tcp://` | [Users & permissions](10-users-permissions-security.md) |
| Audit finding: too many users in `docker` | `getent group docker` | this topic |
| A web UI with the socket mounted is internet-facing | `docker inspect` mounts as above; restrict it | [Site-down playbook](25-playbook-site-down.md) |

**Why it matters for troubleshooting.** During an incident someone always proposes "just add the
user to the docker group" or "just mount the socket". Now you can say exactly what that grants.

**Next step:** reduce what each container is allowed to do.

### Capabilities, read-only rootfs, no-new-privileges

**Level:** [L3 · Senior]

**Concept.** Root inside a container is limited by four layers you can tighten further:

| Layer | Default | Hardening |
|---|---|---|
| **Capabilities** (root's powers split into pieces) | 14 kept: `CHOWN DAC_OVERRIDE FOWNER FSETID KILL SETGID SETUID SETPCAP NET_BIND_SERVICE NET_RAW SYS_CHROOT MKNOD AUDIT_WRITE SETFCAP` | `--cap-drop ALL`, add back only what fails |
| **seccomp** (syscall filter) | default profile blocks dozens of dangerous syscalls | keep it; never `seccomp=unconfined` in production |
| **AppArmor / SELinux** | `docker-default` profile on Ubuntu; `container_t` on RHEL when dockerd runs with `selinux-enabled` | keep it (and enable SELinux support on RHEL) |
| **Root filesystem** | writable | `--read-only` plus `--tmpfs` for the few writable paths |
| **Privilege escalation** | setuid binaries work | `--security-opt no-new-privileges` (daemon-wide: `"no-new-privileges": true`) |

`--privileged` turns all of this off and gives access to host devices; it is root on the host
with extra steps. Running as a **non-root user** already zeroes the effective capabilities, and
Docker lets non-root processes bind ports below 1024 inside containers by default
(`net.ipv4.ip_unprivileged_port_start=0` in the container's namespace), so most apps need no
capabilities at all.

**Key terms:** *capability* (one slice of root's power, such as `NET_BIND_SERVICE`), *`--cap-drop ALL` / `--cap-add`* (start from nothing, add back what the app proves it needs), *read-only rootfs* (`--read-only` plus `tmpfs` for scratch paths), *`no-new-privileges`* (setuid binaries cannot raise privileges), *seccomp profile* (a system-call filter), *`--privileged`* (removes nearly every wall).

**See it on a real system**

```bash
docker info --format '{{.SecurityOptions}}'
docker run --rm alpine:3.20 grep -E 'CapEff|NoNewPrivs|Seccomp:' /proc/self/status
docker run --rm --cap-drop ALL --security-opt no-new-privileges alpine:3.20 grep -E 'CapEff|NoNewPrivs' /proc/self/status
capsh --decode=00000000a80425fb
```

```
[name=apparmor name=seccomp,profile=builtin name=cgroupns]
CapEff:	00000000a80425fb
NoNewPrivs:	0
Seccomp:	2
CapEff:	0000000000000000
NoNewPrivs:	1
0x00000000a80425fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_raw,cap_sys_chroot,cap_mknod,cap_audit_write,cap_setfcap
```

**Hands-on lab (test VM only): harden nginx one layer at a time**

**Step 1 — Read-only root filesystem.**

```bash
docker run --rm --read-only nginx:1.27 2>&1 | tail -2
```

```
nginx: [emerg] mkdir() "/var/cache/nginx/client_temp" failed (30: Read-only file system)
```

**Step 2 — Fix with tmpfs for exactly the paths that must be writable.**

```bash
docker run -d --name hard --read-only --tmpfs /var/cache/nginx --tmpfs /var/run -p 127.0.0.1:8088:80 nginx:1.27
curl -sI http://127.0.0.1:8088 | head -1 && docker rm -f hard
```

**Step 3 — Drop all capabilities.**

```bash
docker run --rm --read-only --tmpfs /var/cache/nginx --tmpfs /var/run --cap-drop ALL nginx:1.27 2>&1 | tail -1
```

```
nginx: [emerg] chown("/var/cache/nginx/client_temp", 101) failed (1: Operation not permitted)
```

**Step 4 — Add back only what fails.** The nginx master (root) needs `CHOWN`, `SETUID` and
`SETGID` to prepare directories and drop to its worker user:

```bash
docker run -d --name hard --read-only --tmpfs /var/cache/nginx --tmpfs /var/run \
  --cap-drop ALL --cap-add CHOWN --cap-add SETUID --cap-add SETGID \
  --security-opt no-new-privileges -p 127.0.0.1:8088:80 nginx:1.27
curl -sI http://127.0.0.1:8088 | head -1 && docker rm -f hard
```

→ Even better: images designed to run unprivileged (an app running as UID 10001 like the worked
examples in section 4) need no capabilities at all.

The same hardening in Compose:

```yaml
services:
  web:
    image: harbor.example.com/shop/web:3f9c2a1
    user: "10001:10001"
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    pids_limit: 200
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `Read-only file system` at start | find the path in the error; add a `tmpfs` or volume for it | this topic |
| `Operation not permitted` after hardening | add back the one capability the error implies | this topic |
| An image "only works with --privileged" | find the real need (a device, one capability, a sysctl) | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** Hardening breaks apps in predictable ways: the error
names the path or the operation. Add back exactly that, and record it next to the service.

**Next step:** secrets, the thing attackers want from your containers.

### Secrets done right

**Level:** [L2 · Mid]

**Concept.** Environment variables are the most common and the leakiest place for secrets: they
show up in `docker inspect`, `/proc/PID/environ`, crash reports, child processes, CI logs and
`docker compose config` output. Better: deliver secrets as **files** in a tmpfs at
`/run/secrets/NAME` and have the app read the file. Many official images support the `_FILE`
convention (`POSTGRES_PASSWORD_FILE=/run/secrets/db_password`).

| Method | Where the secret sits | Verdict |
|---|---|---|
| `ENV`/`ARG` in the Dockerfile | in the image, forever | never |
| `environment:` in a committed compose file | in Git | never |
| `.env` / `env_file` (git-ignored) | plain file on the host; visible in `docker inspect` | acceptable for low-value config |
| Compose `secrets:` (file-based) | plain file on the host, bind-mounted at `/run/secrets` | good for single hosts |
| Swarm secrets | encrypted in the Swarm Raft log, tmpfs in the container | good for Swarm/Dokploy services |
| External manager (Vault, cloud KMS) | outside the host | best for many apps and rotation |

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
secrets:
  db_password:
    file: ./secrets/db_password.txt          # chmod 600, git-ignored
```

**Key terms:** *secret file* (`/run/secrets/NAME`, on a tmpfs), *`_FILE` convention* (`POSTGRES_PASSWORD_FILE` instead of `POSTGRES_PASSWORD`), *Compose secrets* (file-based, single host), *Swarm secrets* (encrypted in the Raft log, delivered only to services granted them), *rotation* (replace, redeploy, revoke the old value).

**See it on a real system**

```bash
docker run -d --name leaky -e DB_PASSWORD=hunter2 alpine:3.20 sleep 600
docker inspect leaky --format '{{range .Config.Env}}{{println .}}{{end}}' | grep PASSWORD
sudo tr '\0' '\n' < /proc/"$(docker inspect -f '{{.State.Pid}}' leaky)"/environ | grep PASSWORD
docker rm -f leaky
```

**Hands-on lab (test VM only)**

**Step 1 — Fix the leak with Compose secrets.** Put the snippet above into
`~/lab/secrets/compose.yaml`, create `secrets/db_password.txt` (`chmod 600`), `docker compose up -d`,
then confirm: `docker inspect` shows only the `_FILE` path, and
`docker compose exec db cat /run/secrets/db_password` shows the value inside.

**Step 2 — Break it: the app ignores `_FILE`.** An app that only reads `DB_PASSWORD` will start
with an empty password. Read the image's documentation for `_FILE` support, or add a tiny
entrypoint that does `export DB_PASSWORD="$(cat /run/secrets/db_password)"` and then `exec "$@"`.

**Step 3 — Rotate.** Change the file, `docker compose up -d --force-recreate db`, and update the
database user's password to match. Rotation is a procedure; write it down once.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Secret visible in a ticket screenshot of `docker inspect` | rotate it; move it to secrets | this topic |
| `cat: /run/secrets/X: No such file or directory` | service not granted the secret (`secrets:` on the service) | this topic |
| Swarm: `secret not found` at deploy | `docker secret ls`; secrets are per swarm | section 14 |

**Why it matters for troubleshooting.** Debug output, support bundles and screenshots travel. If
secrets are not in the environment, they do not travel with them.

**Next step:** shrink what root inside a container can ever mean: rootless and user namespaces.

### Rootless mode and userns-remap

**Level:** [L3 · Senior]

**Concept.** Both use **user namespaces** so that root inside a container maps to an unprivileged
UID on the host.

| | Rootless Docker | `userns-remap` |
|---|---|---|
| Daemon runs as | your user | root |
| Container root maps to | your UID (then subordinate UIDs) | the `dockremap` user's subordinate range (e.g. 100000+) |
| Setup | `dockerd-rootless-setuptool.sh install` (package `docker-ce-rootless-extras`, plus `uidmap`) | `"userns-remap": "default"` in daemon.json |
| Ports below 1024 | need `net.ipv4.ip_unprivileged_port_start` lowered on the host | normal |
| Overlay networks / Swarm | not supported | supported, with limits |
| Gotchas | Ubuntu 24.04 restricts unprivileged user namespaces through AppArmor; the rootless install docs give the profile to add | existing images and containers "disappear" (a new storage directory per mapping); bind-mount ownership is offset |
| Fits | CI runners, developer machines, single-user hosts | hosts where you want remapping but rootful features |

For your platform: Dokploy needs rootful Docker with Swarm and the socket, so harden it with
non-root users per container, dropped capabilities, read-only filesystems and a short `docker`
group. Rootless is a strong option for GitLab runners.

**Key terms:** *user namespace* (maps container UIDs to different host UIDs), *subordinate IDs* (`/etc/subuid` and `/etc/subgid` ranges), *rootless daemon* (dockerd running as your user), *`userns-remap`* (a rootful daemon whose containers are remapped), *`dockremap`* (the default remap user).

**See it on a real system**

```bash
docker info --format '{{.SecurityOptions}}'          # "name=rootless" or "name=userns" when active
grep -E '^(dockremap|USER):' /etc/subuid /etc/subgid  # subordinate ID ranges
docker context ls                                     # rootless shows its own socket under /run/user/UID
```

**Hands-on lab (test VM only)**

**Step 1 — Install rootless for a second user** (follow the rootless page under
https://docs.docker.com/ for the current steps and the Ubuntu 24.04 AppArmor note):

```bash
sudo apt-get install -y uidmap dbus-user-session docker-ce-rootless-extras systemd-container   # last one provides machinectl
sudo useradd -m -s /bin/bash rl && sudo loginctl enable-linger rl
sudo machinectl shell rl@ /bin/bash          # a real login session for that user
dockerd-rootless-setuptool.sh install
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
docker info --format '{{.SecurityOptions}}'
```

**Step 2 — Repeat the root-escape from the first topic.**

```bash
docker run --rm -v /:/host alpine:3.20 sh -c 'id; touch /host/root/pwned'
```

```
uid=0(root) gid=0(root) groups=0(root)
touch: /host/root/pwned: Permission denied
```

→ Root inside, nobody special outside: the escape that worked with rootful Docker fails.

**Step 3 — Break it: low ports.** `docker run -d -p 80:80 nginx:1.27` as the rootless user fails
to bind. Either publish a high port (`-p 8080:80`) or lower
`net.ipv4.ip_unprivileged_port_start` on the host (a host-wide trade-off).

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Rootless install fails on Ubuntu 24.04 with user-namespace errors | AppArmor userns restriction; add the documented profile | [Users & permissions](10-users-permissions-security.md) |
| All images gone after enabling `userns-remap` | they are in the old storage directory; the remapped daemon uses a new one | this topic |
| Rootless: cannot publish port 80 | `sysctl net.ipv4.ip_unprivileged_port_start` | this topic |

**Why it matters for troubleshooting.** When someone hits "permission denied" on a volume on a
remapped or rootless host, the UIDs on disk are offset. `ls -ln` plus `/etc/subuid` explains it.

**Next step:** Docker Swarm, the orchestrator under Dokploy.

---

## 14. Docker Swarm for Dokploy

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm section ([intro note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction)), in this order: Swarm Architecture → Swarm Services → Scaling, Rolling Updates and Rollbacks → Docker Config Objects → Docker Overlay Network ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) → Swarm Service Discovery ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Swarm-Service-Discovery/page)) → Docker Stack ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Stack/page)) · 2) Official: Docker docs *Getting started with Swarm mode* ([tutorial](https://docs.docker.com/engine/swarm/swarm-tutorial/)) · 3) Note: this section, then Dokploy in the [Apache 443 case](21-case-apache-443-dokploy.md) · 4) Video: none verified for Swarm; use the DCA labs instead · 5) Practice: the two-VM labs below, then the Dokploy troubleshooting docs ([docs](https://docs.dokploy.com/docs/core/troubleshooting)).

Dokploy's installer turns your host into a **one-node Docker Swarm**: it runs `docker swarm init`,
creates the attachable overlay network `dokploy-network`, and runs Dokploy itself, its Postgres and
its Redis as Swarm services. Every "Application" you deploy in Dokploy becomes a Swarm service too.
You do not need to run a big cluster, but you do need to read Swarm's state when a deploy hangs, a
task is rejected, or Traefik cannot reach an app. This section gives you exactly that.

### Swarm architecture: managers, workers, Raft

**Level:** [L3 · Senior]

**Concept.** Swarm mode is built into dockerd; there is nothing extra to install. `docker swarm init`
makes the engine a **manager**: it stores the cluster's desired state (services, networks, secrets)
in a replicated **Raft** log and schedules work. **Workers** only run what managers assign. Like
Kubernetes, Swarm is a **reconciliation loop**: you declare "two replicas of this image", and the
managers keep creating tasks until reality matches. A manager is also a worker unless you drain it,
which is why a single Dokploy host works.

```
            docker CLI / Dokploy UI
                    │  Docker API (unix socket)
                    ▼
   ┌───────── manager (Leader) ─────────┐     Raft log: services, networks,
   │ dockerd: API, orchestrator,        │     secrets, configs (encrypted)
   │ scheduler, dispatcher, Raft store  │◀──── 2377/tcp ────▶ other managers
   │ + runs tasks like a worker         │
   └──────────────┬─────────────────────┘
        7946/tcp+udp (gossip, membership)  4789/udp (VXLAN overlay data)
                  ▼
   ┌────────── worker ──────────┐
   │ dockerd + containerd: runs │
   │ the tasks it is given      │
   └────────────────────────────┘
```

Managers need a **quorum** (a majority) to change anything:

| Managers | Majority needed | Can lose | Use |
|---|---|---|---|
| 1 | 1 | 0 | Dokploy single host, labs |
| 3 | 2 | 1 | small production clusters |
| 5 | 3 | 2 | larger clusters; more managers only slow Raft down |

**Key terms:** *node* (one Docker engine in the swarm), *manager* / *worker* (decides / executes),
*Leader* (the manager currently writing the Raft log), *quorum* (a majority of managers), *join
token* (the secret a new node presents; worker and manager tokens differ), *advertise address* (the
IP other nodes use to reach this one), *availability* (`active`, `pause`, `drain`).

**See it on a real system**

```bash
docker info --format 'swarm={{.Swarm.LocalNodeState}} manager={{.Swarm.ControlAvailable}} managers={{.Swarm.Managers}} nodes={{.Swarm.Nodes}}'
docker node ls
docker node inspect self --format '{{.Status.Addr}} {{.Spec.Availability}} {{.ManagerStatus.Addr}}'
sudo ss -ltnp | grep -E ':(2377|7946)\b'
sudo ss -lunp | grep -E ':(4789|7946)\b'
```

```
swarm=active manager=true managers=1 nodes=1
ID                            HOSTNAME   STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
k3j2h1g0f9e8d7c6b5a4z3y2x *   dokploy1   Ready     Active         Leader           28.3.3
192.0.2.10 active 192.0.2.10:2377
LISTEN 0      4096               *:2377            *:*    users:(("dockerd",pid=812,fd=31))
LISTEN 0      4096               *:7946            *:*    users:(("dockerd",pid=812,fd=33))
UNCONN 0      0            0.0.0.0:4789      0.0.0.0:*
UNCONN 0      0                  *:7946            *:*    users:(("dockerd",pid=812,fd=34))
```

→ One node, Leader, active: the normal Dokploy picture. 2377 and 7946 belong to dockerd. 4789 shows
no process because the VXLAN socket lives in the kernel. On a single node nothing else needs these
ports, so the firewall should **not** open them to the internet.

**Hands-on lab (test VM only)**

**Step 1 — Build a two-node swarm.** On lab1, pick the address pool now (section 12 explains why):

```bash
docker swarm init --advertise-addr 192.168.56.11 \
  --default-addr-pool 10.220.0.0/16 --default-addr-pool-mask-length 24
docker swarm join-token worker          # prints the full join command for lab2
```

On lab2, paste the printed command (`docker swarm join --token SWMTKN-1-… 192.168.56.11:2377`), then
on lab1 run `docker node ls`: two nodes, lab1 Leader, lab2 with an empty MANAGER STATUS.

**Step 2 — Break it: a firewall between the nodes.** On lab2 run `docker swarm leave`. On lab1, enable
UFW with only SSH allowed (`sudo ufw allow OpenSSH && sudo ufw enable`, SSH rule **first**), then
join again from lab2:

```
Error response from daemon: Timeout was reached before node joined. The attempt to join the swarm
will continue in the background. Use the "docker info" command to see the current swarm status of
your node.
```

→ 2377/tcp is blocked, so lab2 can never reach the manager.

**Step 3 — Fix it with the narrowest rules.** On lab1, allow only lab2, only the Swarm ports:

```bash
for p in 2377/tcp 7946/tcp 7946/udp 4789/udp; do
  sudo ufw allow from 192.168.56.12 to any port "${p%/*}" proto "${p#*/}"
done
sudo ufw status numbered
```

Repeat on lab2 for lab1's address (7946 and 4789 are needed in both directions). The join completes
in the background; `docker node ls` on lab1 shows lab2 `Ready`.

**Step 4 — Maintenance the Swarm way.** Drain lab2, watch tasks move, then bring it back:

```bash
docker node update --availability drain lab2
docker node ls
docker node update --availability active lab2
```

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `This node is not a swarm manager. Use "docker swarm init" or "docker swarm join"…` | `docker info --format '{{.Swarm.LocalNodeState}}'` (on a worker, or swarm never initialised) | [Containers playbook](26-playbook-containers-k8s.md) |
| `Timeout was reached before node joined` | `nc -vz MANAGER_IP 2377` from the joining node; firewall and security groups | [Ports inventory](22-playbook-ports-inventory.md) |
| Node shows `Down` | `sudo journalctl -u docker -n 50` on that node; clock and network | [Containers playbook](26-playbook-containers-k8s.md) |
| `The swarm does not have a leader` | how many managers are reachable (`docker node ls` on each) | this topic |
| Dokploy host changed its IP, services stopped talking | `docker node inspect self --format '{{.Status.Addr}}'` vs `ip -br addr` | [Containers playbook](26-playbook-containers-k8s.md) |

> Lost quorum is repaired with `docker swarm init --force-new-cluster` on a surviving manager. It
> rewrites the cluster around that one node. Take a backup of `/var/lib/docker/swarm` first, read
> the Swarm admin guide under https://docs.docker.com/, and treat it as a change with a rollback plan.

**Why it matters for troubleshooting.** Swarm is the layer between the Dokploy UI and your
containers. When the UI says "deploying" forever, the answer is in Swarm's state (node, service,
task), not in the container, because the container may never have been created.

**Next step:** services and tasks, the objects Dokploy creates for each app.

### Services, tasks and rolling updates

**Level:** [L3 · Senior]

**Concept.** A **service** is desired state: image, replicas, networks, ports, limits, update
policy. The orchestrator turns it into **tasks** (numbered slots: `web.1`, `web.2`), and each task
runs exactly one container on one node. A task never changes; to change anything, Swarm replaces
tasks. When a task dies, the slot gets a new task, and `docker service ps` keeps the history, with
the **reason** in the ERROR column. That column is the single most useful thing in Swarm debugging.

```
 service web (replicas: 2, image web:3f9c2a1)
   ├── slot web.1 ── task a1… Running  on lab1 ── container web.1.a1…
   │                └ task 9z… Shutdown (replaced by an update)
   └── slot web.2 ── task b2… Running  on lab2 ── container web.2.b2…

 task states: NEW → PENDING → ASSIGNED → ACCEPTED → PREPARING → STARTING → RUNNING
              PENDING forever = cannot schedule;  REJECTED = node refused it (image, mount)
              FAILED = container exited non-zero;  SHUTDOWN = stopped on purpose
```

| Update setting | Flag | Typical value | Why |
|---|---|---|---|
| How many tasks at once | `--update-parallelism` | 1 | one bad task, not all of them |
| Pause between batches | `--update-delay` | 10s | time to notice errors |
| New before old | `--update-order start-first` | start-first | no capacity dip (needs room for one extra task) |
| How long to watch a new task | `--update-monitor` | 30s | a crash after 20 s still counts as failure |
| What to do on failure | `--update-failure-action` | rollback | default is `pause`, which leaves a half-updated service |

**Key terms:** *service* (desired state), *task* (one scheduled container, never modified), *slot*
(`NAME.N`, the stable position a task fills), *replicated* vs *global* mode (N copies vs one per
node), *constraint* (`node.role==manager`, `node.labels.disk==ssd`), *rollback* (return to the
previous service spec).

**See it on a real system**

```bash
docker service ls
docker service ps web --no-trunc --format 'table {{.Name}}\t{{.Image}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}'
docker service inspect --pretty web | sed -n '/UpdateStatus/,/Message/p'
```

```
ID             NAME   MODE         REPLICAS   IMAGE               PORTS
r7t1k2m3n4p5   web    replicated   2/2        nginx:1.27-alpine   *:8080->80/tcp
NAME        IMAGE                       NODE   CURRENT STATE            ERROR
web.1       nginx:1.27-alpine@sha256:…  lab1   Running 2 minutes ago
 \_ web.1   nginx:1.26-alpine@sha256:…  lab1   Shutdown 2 minutes ago
web.2       nginx:1.27-alpine@sha256:…  lab2   Running 2 minutes ago
 \_ web.2   nginx:1.26-alpine@sha256:…  lab2   Shutdown 2 minutes ago
UpdateStatus:
 State:         completed
 Started:       3 minutes ago
 Completed:     2 minutes ago
 Message:       update completed
```

→ `REPLICAS 2/2` means running/desired. Each task records the image **digest** it ran, so "which
code is node X running?" has an exact answer. The `\_` lines are history: why a slot was replaced.

**Hands-on lab (test VM only)**

**Step 1 — Create a service with a safe update policy** (on lab1, the manager):

```bash
docker service create --name web --replicas 2 --publish published=8080,target=80 \
  --update-parallelism 1 --update-delay 10s --update-order start-first \
  --update-monitor 15s --update-failure-action rollback \
  --health-cmd 'wget -qO- http://127.0.0.1/ >/dev/null || exit 1' --health-interval 5s \
  nginx:1.26-alpine
docker service update --image nginx:1.27-alpine web      # watch the progress bars
```

**Step 2 — Break it: deploy a tag that does not exist.**

```bash
docker service update --image nginx:9.99-alpine web
docker service ps web --no-trunc --format 'table {{.Name}}\t{{.CurrentState}}\t{{.Error}}' | head -4
```

```
image nginx:9.99-alpine could not be accessed on a registry to record its digest. Each node will
access nginx:9.99-alpine independently, possibly leading to different nodes running different
versions of the image.
…
rollback: update rolled back due to failure or early termination of task …
NAME        CURRENT STATE            ERROR
web.1       Running 5 seconds ago
 \_ web.1   Rejected 20 seconds ago  "No such image: nginx:9.99-alpine"
```

→ Rejected on the node, the update failed, and `--update-failure-action rollback` put the previous
spec back automatically. With the default (`pause`), the service would sit half-updated until you
ran `docker service rollback web`.

**Step 3 — Break it: a constraint nobody satisfies.**

```bash
docker service create --detach --name pinned --constraint node.labels.disk==ssd nginx:1.27-alpine
docker service ps pinned --format '{{.CurrentState}} | {{.Error}}'
```

```
Pending 12 seconds ago | no suitable node (scheduling constraints not satisfied on 2 nodes)
```

**Step 4 — Fix it.** Label a node, and the pending task schedules within seconds:

```bash
docker node update --label-add disk=ssd lab2
docker service ps pinned --format '{{.Node}} {{.CurrentState}}'
docker service rm pinned
```

**How it breaks**

| Symptom / error text (in `docker service ps --no-trunc`) | First command | Playbook |
|---|---|---|
| `no suitable node (scheduling constraints not satisfied…)` | `docker service inspect --pretty SERVICE` (Placement) and `docker node inspect NODE --format '{{.Spec.Labels}}'` | [Containers playbook](26-playbook-containers-k8s.md) |
| `insufficient resources on N nodes` | reservations vs node capacity (`docker node inspect NODE --pretty`) | section 10 |
| `No such image` / `manifest unknown` | the tag in Harbor; `docker manifest inspect IMAGE` from that node | section 11 |
| `unauthorized: authentication required` on some nodes only | redeploy with `--with-registry-auth` | section 11 |
| `task: non-zero exit (1)` repeating | `docker service logs --tail 50 SERVICE` | next topics |
| `update paused due to failure or early termination of task` | `docker service rollback SERVICE`, then read the failed task's error | this topic |

**Why it matters for troubleshooting.** Dokploy's "deploy succeeded but the app is down" and
"deploy hangs" cases are almost always one of the ERROR strings above. Reading `docker service ps
--no-trunc` first saves you from guessing at the container, which may not exist yet.

**Next step:** how tasks on different nodes, and Traefik, reach each other: overlay networks.

### Overlay networks and the routing mesh

**Level:** [L3 · Senior]

**Concept.** An **overlay** network is one Layer-2 segment spread across nodes: each node keeps a
bridge inside a hidden namespace, and frames between nodes travel inside **VXLAN** packets on
UDP port 4789. Containers on the same overlay reach each other by IP and by name, whatever node they run on.
Service discovery works through Docker's embedded DNS (section 7): the service name resolves to a
**virtual IP** (VIP) that load-balances over healthy tasks, and `tasks.NAME` resolves to every task's
own IP. **Attachable** overlays also accept plain `docker run` and Compose containers, which is how
Dokploy's Compose apps and its Traefik container join `dokploy-network`.

Publishing a port on a service uses the **routing mesh** by default: every node listens on that
port (dockerd owns it, see `ss`), and the hidden `ingress` overlay plus IPVS forward the connection to
a task on any node. `mode=host` publishing skips the mesh and binds only on nodes that run a task.

```
 client ──▶ any node :8080 (dockerd listens, routing mesh)
              │ ingress overlay (VXLAN 4789/udp) + IPVS load balancing
              ▼
   lab1: web.1 (10.220.0.7)        lab2: web.2 (10.220.0.8)
     │ also on: shopnet overlay 10.220.2.0/24  ──  VIP "web" = 10.220.2.2
     │ outbound to the internet via docker_gwbridge (172.18.0.0/16) + MASQUERADE
     ▼
 Dokploy: dokploy-traefik ──(dokploy-network, attachable overlay)──▶ app service VIP:PORT
```

VXLAN adds 50 bytes per packet, so overlay interfaces default to MTU 1450. If the underlay is
itself smaller (a VPN between sites, some cloud links), set a smaller overlay MTU at creation
(`--opt com.docker.network.driver.mtu=1400`) or large responses stall while small ones work.

**Key terms:** *overlay* (multi-host network over VXLAN), *attachable* (standalone containers may
join), *VIP* (one virtual IP per service, load-balanced), *`tasks.NAME`* (DNS name returning every
task IP), *routing mesh* / *`ingress`* (publish on every node), *`mode=host`* publishing (only where
a task runs), *`docker_gwbridge`* (outbound path for overlay containers).

**See it on a real system**

```bash
docker network ls --filter driver=overlay
docker network inspect dokploy-network --format 'attachable={{.Attachable}} subnet={{range .IPAM.Config}}{{.Subnet}}{{end}}'
docker service inspect web --format '{{json .Endpoint.VirtualIPs}}' | jq .
docker run --rm --network shopnet nicolaka/netshoot sh -c 'dig +short web; echo ---; dig +short tasks.web'
sudo ss -ltnp 'sport = :8080'
```

```
NETWORK ID     NAME              DRIVER    SCOPE
q8w7e6r5t4y3   dokploy-network   overlay   swarm
j1h2g3f4d5s6   ingress           overlay   swarm
k9l8m7n6b5v4   shopnet           overlay   swarm
attachable=true subnet=10.220.1.0/24
[
  { "NetworkID": "j1h2g3f4d5s6…", "Addr": "10.220.0.5/24" },
  { "NetworkID": "k9l8m7n6b5v4…", "Addr": "10.220.2.2/24" }
]
10.220.2.2
---
10.220.2.7
10.220.2.8
LISTEN 0      4096       *:8080       *:*    users:(("dockerd",pid=812,fd=58))
```

→ `web` is one VIP; `tasks.web` lists the two replicas. Port 8080 is held by **dockerd**, not by
docker-proxy or a container: that is the routing mesh, and it is why `ss` on a Swarm host names
dockerd for published service ports.

**Hands-on lab (test VM only)**

**Step 1 — An attachable overlay with a service on it.**

```bash
docker network create -d overlay --attachable shopnet
docker service create --name api --replicas 2 --network shopnet traefik/whoami:v1.10.1
docker run --rm --network shopnet nicolaka/netshoot sh -c \
  'for i in 1 2 3 4; do curl -s http://api/ | grep Hostname; done'
```

→ Hostnames alternate: the VIP balances across both tasks, on both nodes.

**Step 2 — The routing mesh.** Pin one task to lab1 and publish it, then call lab2:

```bash
docker service create --name mesh --publish published=8081,target=80 \
  --constraint node.hostname==lab1 traefik/whoami:v1.10.1
curl -s http://192.168.56.12:8081/ | grep Hostname      # lab2 answers, lab1's task serves
```

**Step 3 — Break it: block VXLAN on lab2** (lab only; this deliberately breaks the overlay):

```bash
sudo iptables -I INPUT -p udp --dport 4789 -j DROP      # on lab2
curl -s --max-time 5 http://192.168.56.12:8081/ || echo "timed out"
docker run --rm --network shopnet nicolaka/netshoot dig +short api   # on lab2: DNS still answers
```

→ Names still resolve (DNS is answered locally on each node) but connections across nodes time out.
"DNS works, connection hangs" between Swarm nodes is the VXLAN signature.

**Step 4 — Fix and prove it.** Remove the rule and watch the encapsulated traffic:

```bash
sudo iptables -D INPUT -p udp --dport 4789 -j DROP
sudo tcpdump -ni IFACE -c 4 udp port 4789               # IFACE = the 192.168.56.x interface; repeat the curl
docker service rm api mesh
```

**Step 5 — Break it: attach to a non-attachable overlay.**

```bash
docker network create -d overlay private-net
docker run --rm --network private-net alpine:3.20 true
```

```
docker: Error response from daemon: Could not attach to network private-net: rpc error:
code = PermissionDenied desc = network private-net not manually attachable.
```

→ Fix: recreate it with `--attachable`, or attach a **service** instead of a container.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `network NAME not manually attachable` | `docker network inspect NAME --format '{{.Attachable}}'` | this topic |
| Name resolves, connections across nodes time out | `sudo tcpdump -ni IFACE udp port 4789` on both nodes; firewall and security groups | [Network speed playbook](24-playbook-network-speed.md) |
| Small requests fine, big responses hang | overlay MTU vs path MTU (`tracepath OTHER_NODE`) | [Network speed playbook](24-playbook-network-speed.md) |
| Traefik: `dial tcp: lookup APP … no such host` | the app is not on `dokploy-network` (`docker service inspect APP --format '{{json .Spec.TaskTemplate.Networks}}'`) | [Containers playbook](26-playbook-containers-k8s.md) |
| Published port answers only on some nodes | `mode=host` publishing, or 7946/4789 blocked to those nodes | this topic |
| `ingress` subnet clashes with a real 10.x network | `docker network inspect ingress` | section 12 |

**Why it matters for troubleshooting.** The Dokploy 502 "container not on dokploy-network" case,
cross-node hangs and MTU stalls all live in this topic. Test from the same network as the caller
(netshoot on `dokploy-network`), because that is the only view that matches what Traefik sees.

**Next step:** secrets, configs and stacks, the way multi-service apps are deployed on Swarm.

### Secrets, configs and stacks

**Level:** [L3 · Senior]

**Concept.** Swarm keeps **secrets** encrypted in its Raft log and delivers them only to the tasks
of services that were granted them, as files on a tmpfs at `/run/secrets/NAME`. **Configs** work the
same way for non-sensitive files (an nginx.conf, a Traefik dynamic file). Both are **immutable**: to
rotate, create a new object (`db_password_v2`) and switch the service to it. A **stack** is a Compose
file deployed to Swarm with `docker stack deploy`: each Compose service becomes a Swarm service named
`STACK_SERVICE`, and the `deploy:` section (replicas, update_config, restart_policy, resources,
placement) finally takes effect.

| Compose file key | `docker compose up` | `docker stack deploy` |
|---|---|---|
| `build:` | builds the image | ignored: images must already be in a registry |
| `depends_on:` | start order (and health with `condition:`) | ignored: apps must retry their dependencies |
| `container_name:` | used | ignored: tasks are named `STACK_SERVICE.SLOT.TASKID` |
| `restart:` | restart policy | ignored: use `deploy.restart_policy` |
| `deploy:` | partly: resources, replicas and restart_policy are applied; Swarm-only keys such as placement are ignored | fully used |
| `secrets:` | bind-mounted files | encrypted Swarm secrets (`external: true` for pre-created ones) |

Dokploy offers both worlds: a Compose deployment can run as plain Compose or as a stack (check the
Compose type setting in your Dokploy version), and Applications are Swarm services directly.

**Key terms:** *secret* (encrypted, delivered as a file to granted services), *config* (the same for
non-secret files), *external* (created outside the stack file), *stack* (a Compose file deployed as
Swarm services), *`--with-registry-auth`* (forward your registry login to the nodes that pull).

**See it on a real system**

```bash
docker secret ls
docker stack ls
docker stack services shop
docker stack ps shop --no-trunc --format 'table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}'
docker service inspect shop_db --format '{{json .Spec.TaskTemplate.ContainerSpec.Secrets}}' | jq '.[] | {SecretName, File: .File.Name}'
```

```
ID                          NAME             DRIVER    CREATED          UPDATED
v1q2w3e4r5t6y7u8i9o0p1a2s   db_password_v1             10 minutes ago   10 minutes ago
NAME      SERVICES
shop      2
ID             NAME       MODE         REPLICAS   IMAGE                    PORTS
a1s2d3f4g5h6   shop_db    replicated   1/1        postgres:16
z9x8c7v6b5n4   shop_web   replicated   2/2        traefik/whoami:v1.10.1
{ "SecretName": "db_password_v1", "File": "db_password" }
```

→ The service sees the file `/run/secrets/db_password`, while the Swarm object is
`db_password_v1`. That indirection is what makes rotation possible without changing the app.

**Hands-on lab (test VM only)**

**Step 1 — Create a secret and deploy a stack.**

```bash
mkdir -p ~/lab/stack && cd ~/lab/stack
printf '%s' 'lab-only-pass-1' | docker secret create db_password_v1 -
cat > stack.yaml <<'EOF'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - source: db_password_v1
        target: db_password
    networks: [backend]
    deploy:
      restart_policy:
        condition: on-failure
  web:
    image: traefik/whoami:v1.10.1
    networks: [backend]
    deploy:
      replicas: 2
      update_config: { parallelism: 1, order: start-first, failure_action: rollback }
networks:
  backend:
    driver: overlay
secrets:
  db_password_v1:
    external: true
EOF
docker stack deploy -c stack.yaml shop
```

```
Creating network shop_backend
Creating service shop_db
Creating service shop_web
```

**Step 2 — Break it: remove a secret that is in use.**

```bash
docker secret rm db_password_v1
```

```
Error response from daemon: rpc error: code = InvalidArgument desc = secret 'db_password_v1' is in
use by the following service: shop_db
```

→ Swarm protects you. Rotation means "add the new one, switch, then remove the old one".

**Step 3 — Rotate.** Create `db_password_v2`, change both `db_password_v1` entries in
`stack.yaml` to `db_password_v2`, run `docker stack deploy -c stack.yaml shop` again, then
`docker secret rm db_password_v1`. Postgres reads `POSTGRES_PASSWORD_FILE` only when it initialises
an **empty** data directory, so also change the password inside the database
(`ALTER USER postgres PASSWORD '…'`). Rotation is always "new value in the store **and** in the
system that checks it".

**Step 4 — Clean up.** `docker stack rm shop`, then `docker secret rm db_password_v2`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `service shop_db: secret not found: NAME` at deploy | `docker secret ls`; secrets belong to one swarm and must exist first | this topic |
| `Ignoring unsupported options: build` | build in CI, push to Harbor, reference the tag | section 11 |
| App crashes at start because the DB is not ready yet | `depends_on` is ignored in a stack: add retries in the app or entrypoint | section 9 |
| `secret … is in use by the following service` | expected; switch services to the new secret first | this topic |
| Stack works on lab1, tasks on lab2 cannot pull | redeploy with `docker stack deploy --with-registry-auth` | section 11 |

**Why it matters for troubleshooting.** Moving an app from your laptop's Compose to Dokploy or a
stack changes behaviour silently: no build, no start order, no container names. Knowing which keys
are ignored explains a whole class of "works locally, fails on the server".

**Next step:** read a misbehaving Swarm service and Dokploy's own services from the logs.

### Service logs, ps and Dokploy's services

**Level:** [L3 · Senior]

**Concept.** Debugging a Swarm service follows a fixed order, from the desired state down to the
process. `docker service ls` (does it have its replicas?), `docker service ps --no-trunc` (why were
tasks replaced?), `docker service logs` (what did the app print, across all tasks and nodes?), and
only then the container on the node (`docker inspect`, `nsenter`, netshoot). `docker service logs`
needs a logging driver Docker can read back (json-file, local or journald), the same rule as `docker
logs` (section 6).

```
 docker service ls ─▶ REPLICAS 0/1?            ─▶ docker service ps SERVICE --no-trunc  (ERROR column)
                      REPLICAS 1/1 but broken? ─▶ docker service logs --since 15m SERVICE
                                               ─▶ on the node: docker ps --filter label=com.docker.swarm.service.name=SERVICE
                                               ─▶ docker inspect / nsenter / netshoot (section 15)
```

On a Dokploy host you will find:

| Object | Kind | Check it with |
|---|---|---|
| `dokploy` (UI and API, port 3000) | Swarm service | `docker service ps dokploy --no-trunc`, `docker service logs dokploy` |
| `dokploy-postgres`, `dokploy-redis` | Swarm services | `docker service ps NAME --no-trunc` |
| `dokploy-traefik` | a plain container on current versions (check `docker ps` vs `docker service ls` on yours) | `docker logs dokploy-traefik` |
| Each Application | a Swarm service with a generated name such as `shop-web-8f3k2a` | `docker service ps`, `docker service logs` |
| Compose deployments | Compose containers or a stack, joined to `dokploy-network` | `docker compose ls`, `docker stack ls` |

**Key terms:** *service logs* (aggregated logs of all tasks, prefixed `SERVICE.SLOT.TASKID@NODE`),
*task history* (the `\_` lines of `docker service ps`), *UpdateStatus* (state of the last rolling
update), *generated service name* (Dokploy's app name plus a random suffix).

**See it on a real system** (a Dokploy host)

```bash
docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'
docker ps --filter name=dokploy-traefik --format '{{.Names}}  {{.Status}}  {{.Ports}}'
docker service logs --since 15m --tail 3 shop-web-8f3k2a
```

```
NAME               REPLICAS   IMAGE
dokploy            1/1        dokploy/dokploy:latest
dokploy-postgres   1/1        postgres:16
dokploy-redis      1/1        redis:7
shop-web-8f3k2a    2/2        harbor.example.com/shop/web:3f9c2a1
dokploy-traefik  Up 3 days  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp
shop-web-8f3k2a.1.x7k2m9p4q1r3@dokploy1    | 10.0.1.4 - - [03/Oct/2026:11:02:13 +0000] "GET / HTTP/1.1" 200 24 "-" "curl/8.5.0"
shop-web-8f3k2a.2.c4v5b6n7m8q9@dokploy1    | 10.0.1.4 - - [03/Oct/2026:11:02:14 +0000] "GET /healthz HTTP/1.1" 200 3 "-" "-"
shop-web-8f3k2a.1.x7k2m9p4q1r3@dokploy1    | [2026-10-03 11:02:20 +0000] [9] [INFO] Booting worker with pid: 9
```

→ Every log line names its slot, task and node, so one noisy replica stands out. The client IP is
10.0.1.4, Traefik's address on `dokploy-network`, not the real visitor: real client IPs come from
`X-Forwarded-For` ([Web servers & proxies](29-learn-webservers-proxies.md)).

**Hands-on lab (test VM only)**

**Step 1 — Break it: a service that cannot start.**

```bash
docker service create --detach --name crashy --restart-max-attempts 3 alpine:3.20 sh -c \
  'test -n "$DB_HOST" || { echo "DB_HOST not set" >&2; exit 1; }; echo "using $DB_HOST"; sleep 3600'
sleep 30
docker service ps crashy --no-trunc --format 'table {{.Name}}\t{{.CurrentState}}\t{{.Error}}'
docker service logs --tail 5 crashy
```

```
NAME           CURRENT STATE            ERROR
crashy.1       Failed 7 seconds ago     "task: non-zero exit (1)"
 \_ crashy.1   Failed 13 seconds ago    "task: non-zero exit (1)"
 \_ crashy.1   Failed 19 seconds ago    "task: non-zero exit (1)"
 \_ crashy.1   Failed 25 seconds ago    "task: non-zero exit (1)"
crashy.1.p2k8d1s9f7g6@lab1    | DB_HOST not set
crashy.1.h5j6k7l8z9x0@lab1    | DB_HOST not set
crashy.1.q1w2e3r4t5y6@lab1    | DB_HOST not set
crashy.1.z8x7c6v5b4n3@lab1    | DB_HOST not set
```

→ `service ps` says *that* it fails (exit 1: the first run plus three restarts, about 5 s apart
with the default `--restart-delay`, then Swarm gives up); `service logs` says *why*. Always read both.

**Step 2 — Fix it.**

```bash
docker service update --env-add DB_HOST=db.lab.example.com crashy
docker service ps crashy --format '{{.Name}} {{.CurrentState}}' | head -1
docker service logs --tail 1 crashy
docker service rm crashy
```

**Step 3 — Read Dokploy's own services** (on a Dokploy test VM): open a deployment in the Dokploy UI,
then find the same information with `docker service ps APP --no-trunc` and `docker service logs APP`.
Knowing both views means you are never stuck when the UI itself is down.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Dokploy UI unreachable on :3000 | `docker service ps dokploy --no-trunc`; `docker service logs --tail 50 dokploy` | [Containers playbook](26-playbook-containers-k8s.md) |
| Deploy "succeeded", old version still served | `docker service ps APP --no-trunc` (image digest per task) | [Containers playbook](26-playbook-containers-k8s.md) |
| `docker service logs` prints nothing | `docker service inspect APP --format '{{json .Spec.TaskTemplate.LogDriver}}'` | section 6 |
| App healthy, domain returns 502 | `docker logs --tail 50 dokploy-traefik` | section 15 walk |
| Tasks restart every few minutes, no error in the log | `docker inspect TASK_CONTAINER --format '{{.State.OOMKilled}} {{json .State.Health}}'` | section 10 |

**Why it matters for troubleshooting.** The Dokploy UI shows a summary of exactly these commands.
When the UI, its database or Traefik is the thing that is broken, the CLI is all you have, and the
order (service, tasks, logs, container) keeps you from restarting things at random.

**Next step:** the toolkit for the container itself: netshoot, nsenter, events, disk usage and
image layers.

---

## 15. The debugging toolkit

> 📚 **Study path:** 1) Note: this section first; KodeKloud does not cover netshoot or nsenter debugging · 2) KodeKloud: *Docker Certified Associate* — Docker Engine: Troubleshooting Docker Daemon ([note](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page)) and Demo – Docker Debug Mode ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) Read: the netshoot README ([GitHub](https://github.com/nicolaka/netshoot)) and Dokploy *Networking & DNS* troubleshooting ([docs](https://docs.dokploy.com/docs/core/troubleshooting/networking)) · 4) Practice: the iximiuz Labs Docker roadmap challenges ([roadmap](https://labs.iximiuz.com/roadmaps/docker)), then the scenarios in the [Containers playbook](26-playbook-containers-k8s.md).

Production images are small on purpose: no shell, no `curl`, no `ss`, no `tcpdump`. You should not
install tools into a running container (it changes the thing you are debugging, and the next deploy
erases it). Instead, bring the tools **to** the container's namespaces from outside. Five tools
cover almost every case; the last topic puts them together in one incident.

### netshoot: a toolbox in the container's namespace

**Level:** [L2 · Mid]

**Concept.** `nicolaka/netshoot` is an image packed with network tools (dig, curl, ss, ip, tcpdump,
nc, mtr, iperf3, nmap, termshark). The trick is **which namespace you start it in**:

| You want to see… | Run netshoot with | It behaves like |
|---|---|---|
| exactly what the app sees (its IP, its sockets, its DNS) | `--net container:CONTAINER` | a second process inside the app's network namespace |
| what a **peer** on the same network sees (Traefik's view) | `--network NETWORK` (attachable overlays included) | a new container next to the app |
| the host's view | `--net host` | the host, with better tools |
| the app's processes too | add `--pid container:CONTAINER` | `ps` shows the app's processes |

In Kubernetes the same idea is `kubectl debug` with an ephemeral container
([Kubernetes](31-learn-kubernetes.md)). On an air-gapped host, pull netshoot through your Harbor
proxy cache and pin a tag you have tested, rather than relying on `latest`.

**Key terms:** *shared network namespace* (`--net container:`), *peer view* (a new container on the
same network), *embedded DNS* (127.0.0.11, section 7), *upstream forwarding* (Docker forwards names it
does not know to the host's resolvers, from inside the container's namespace).

**See it on a real system**

```bash
docker exec shop-web grep -E '^(nameserver|options)' /etc/resolv.conf
docker run --rm --net container:shop-web nicolaka/netshoot ss -ltn
docker run --rm --net container:shop-web nicolaka/netshoot dig +short db
docker run --rm --network shop nicolaka/netshoot curl -s -o /dev/null -w '%{http_code}\n' http://shop-web:8000/healthz
```

```
nameserver 127.0.0.11
options ndots:0
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port
LISTEN 0      2048         0.0.0.0:8000       0.0.0.0:*
LISTEN 0      4096      127.0.0.11:41623      0.0.0.0:*
172.20.0.3
200
```

→ The app listens on 0.0.0.0:8000, Docker's DNS listener sits on 127.0.0.11 (a random port that
Docker's NAT rules map from 53), `db` resolves, and a peer on the same network gets 200. Each line
rules out one layer.

**Hands-on lab (test VM only)** — this is the Ops Ladder L3 drill "attach netshoot to a running
container's network namespace and capture its DNS queries with tcpdump".

**Step 1 — A container that keeps resolving names.**

```bash
docker network create shop
docker run -d --name db --network shop alpine:3.20 sleep 3600
docker run -d --name app --network shop alpine:3.20 sh -c \
  'while true; do nslookup db >/dev/null 2>&1; nslookup example.com >/dev/null 2>&1; sleep 5; done'
```

**Step 2 — Capture its DNS from inside its namespace.**

```bash
docker run --rm --net container:app nicolaka/netshoot \
  tcpdump -ni any -c 8 'udp and (port 53 or host 127.0.0.11)'
```

```
10:41:02.112233 lo    In  IP 127.0.0.1.48213 > 127.0.0.11.41623: 51234+ A? db. (20)
10:41:02.112502 lo    In  IP 127.0.0.11.53 > 127.0.0.1.48213: 51234 1/0/0 A 172.21.0.2 (38)
10:41:02.113010 lo    In  IP 127.0.0.1.39811 > 127.0.0.11.41623: 2201+ A? example.com. (29)
10:41:02.113420 eth0  Out IP 172.21.0.3.51877 > 192.0.2.53.53: 2201+ A? example.com. (29)
10:41:02.121904 eth0  In  IP 192.0.2.53.53 > 172.21.0.3.51877: 2201 1/0/0 A 198.51.100.80 (45)
10:41:02.122150 lo    In  IP 127.0.0.11.53 > 127.0.0.1.39811: 2201 1/0/0 A 198.51.100.80 (45)
```

→ Read it as two stories. `db` is answered on `lo` by Docker's embedded DNS and never leaves the
container. `example.com` is forwarded out of **eth0** to the upstream resolver 192.0.2.53 (from the
host's resolv.conf or daemon.json `dns`). Port numbers on 127.0.0.11 are rewritten by Docker's NAT
rules inside the namespace and differ on your machine.

**Step 3 — Break it: an upstream that never answers.** As in the embedded DNS topic (section 7),
set `{ "dns": ["192.0.2.253"] }` in daemon.json on the lab VM, validate, restart Docker, start `db`
and `app` again with the Step 1 commands, and capture again: the `db` lines on `lo` still get answers,
while the eth0 lines go to 192.0.2.253 and nothing comes back. Where Docker found no usable upstream
at all (a container on the default bridge, some Docker-in-Docker CI jobs), the same capture shows
queries to **8.8.8.8** and **8.8.4.4** instead, which an on-prem firewall usually drops; check the
`ExtServers` comment in the container's `/etc/resolv.conf` to see which case you are in. Either way, every external name fails
inside containers while the host resolves fine.

**Step 4 — Fix it.** Put your real internal resolvers in daemon.json
(`"dns": ["192.0.2.53", "192.0.2.54"]`, section 12), validate, restart Docker, recreate the
containers, capture once more and confirm the upstream address and the answers. Clean up with
`docker rm -f app db && docker network rm shop`, and restore the daemon.json you had before.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| External names fail only inside containers | the netshoot capture above: where do eth0 queries go? | [Containers playbook](26-playbook-containers-k8s.md) |
| Container names fail, external names work | both containers on the same **user-defined** network? (`docker inspect CONTAINER --format '{{json .NetworkSettings.Networks}}'`) | section 7 |
| `docker run --network dokploy-network` fails | the network is not attachable (only for overlays you created yourself) | section 14 |
| netshoot cannot be pulled on an air-gapped host | pull through the Harbor proxy cache project | section 11 |

**Why it matters for troubleshooting.** It replaces "DNS is broken" with a packet-level answer:
which resolver, which name, which answer, which interface. That is the evidence a postmortem needs,
and it works on images that contain nothing but the app.

**Next step:** when even netshoot is not an option (no registry access, a host-level question), use
the host's own tools with nsenter.

### nsenter and tcpdump from the host

**Level:** [L2 · Mid]

**Concept.** `nsenter` runs a host binary inside some of a process's namespaces. With only `-n`
(network), you use the **host's** `ss`, `ip` and `tcpdump` against the **container's** network stack,
with the host's filesystem still visible. That is the universal fallback: no image pull, no shell in
the container needed. Each container's eth0 is one end of a veth pair (section 7); the other end on
the host is where host-side captures happen.

| Flag | Namespace entered | Typical use |
|---|---|---|
| `-n` | network | `ss -ltnp`, `ip addr`, `tcpdump` as the container sees them |
| `-m` | mount | read the container's files with its own paths (needs tools inside the image) |
| `-p` | PID | `ps` inside the container's PID namespace (combine with `-m`) |
| `-u`, `-i` | UTS, IPC | rarely needed |
| `-a` | all of them | close to `docker exec`, but works when exec is blocked |

**Key terms:** *target PID* (`-t`, the container's main process from `docker inspect`), *veth peer*
(the host end of the container's eth0; `eth0@ifN` names its index), *`/proc/PID/root`* (the
container's filesystem without entering any namespace).

**See it on a real system**

```bash
PID=$(docker inspect -f '{{.State.Pid}}' shop-web)
sudo nsenter -t "$PID" -n ss -ltnp
sudo nsenter -t "$PID" -n ip -o link show eth0          # "eth0@if23": host peer has index 23
ip -o link | awk -F': ' '$1==23 {print $2}'              # the host-side veth name
sudo tcpdump -ni veth3c1d2e4 -c 4 'tcp port 8000'        # the name printed above, without the @… suffix
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      2048         0.0.0.0:8000      0.0.0.0:*     users:(("gunicorn",pid=4262,fd=5))
2: eth0@if23: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT …
veth3c1d2e4@if2
```

→ The process column shows host PIDs (4262), because `ss` reads them from the host's `/proc`. The
veth name is what you capture on from the host when you want to see traffic as it leaves or enters
the container, including packets the container never answers.

**Hands-on lab (test VM only)**

**Step 1 — A container with no shell.**

```bash
docker run -d --name tiny -p 127.0.0.1:18080:80 traefik/whoami:v1.10.1
docker exec tiny sh
```

```
OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file
not found in $PATH: unknown
```

**Step 2 — Debug it anyway.**

```bash
PID=$(docker inspect -f '{{.State.Pid}}' tiny)
sudo nsenter -t "$PID" -n ss -ltn                       # listens on :80
sudo ls -l /proc/"$PID"/root/                           # its filesystem: a single binary
sudo nsenter -t "$PID" -n tcpdump -ni eth0 -c 2 'tcp port 80' & sleep 1; curl -s http://127.0.0.1:18080/ >/dev/null; wait
```

→ You saw its sockets, its files and its packets without a single tool in the image.

**Step 3 — Break it: a stale PID.** Run `docker restart tiny`, then reuse the old `$PID`:
`nsenter: cannot open /proc/4211/ns/net: No such file or directory`. A restarted container has a new
main process; always re-read the PID. Clean up with `docker rm -f tiny`.

**How it breaks**

| Symptom / error text | First command | Playbook |
|---|---|---|
| `nsenter: cannot open /proc/PID/ns/net` | re-read `docker inspect -f '{{.State.Pid}}' CONTAINER` | this topic |
| `nsenter -m` then `ss: command not found` | use `-n` only: host tools, container network | this topic |
| tcpdump on the host bridge shows SYNs, the container shows none | DOCKER-USER or FORWARD rules (`sudo iptables -S DOCKER-USER`) | section 7 |
| `exec: "sh": executable file not found` | the image has no shell; nsenter or netshoot | this topic |

**Why it matters for troubleshooting.** It is the tool that always works, on any host where you have
root, even when the registry is down and the image is distroless. It also proves the "container is
just a process" model from section 2 every time you use it.

**Next step:** step back from one container to the whole daemon: what happened, and where the disk
went.

### docker events and docker system df

**Level:** [L2 · Mid]

**Concept.** `docker events` is the daemon's **timeline**: every create, start, die (with exit code),
oom, kill, health change, pull, network connect and volume mount. It answers "what happened at
03:12?" when logs are gone with the container. The daemon keeps only a short in-memory history, so
for incidents you want it **recorded** (journald or a log shipper). `docker system df` is the
**disk** view: images, containers' writable layers, volumes and build cache, with what is
reclaimable. Container log files are **not** counted there (section 6).

| Question | Command |
|---|---|
| Which containers died in the last hour, with exit codes? | `docker events --since 1h --filter event=die --format '{{.Time}} {{.Actor.Attributes.name}} exit={{.Actor.Attributes.exitCode}}'` |
| Was anything OOM-killed today? | `docker events --since 24h --until "$(date +%s)" --filter event=oom` |
| Health flapping? | `docker events --filter event=health_status` |
| What uses Docker's disk? | `docker system df` then `docker system df -v` |
| What is outside Docker's accounting? | `sudo du -xh --max-depth=1 /var/lib/docker | sort -h` and `sudo du -sh /var/lib/docker/containers/*/*-json.log` |

**Safe cleanup order** (least to most destructive; never on a host whose volumes you have not backed
up):

| Order | Command | Removes | Risk |
|---|---|---|---|
| 1 | `docker builder prune --filter until=168h` | build cache older than a week | slower next build |
| 2 | `docker container prune` | stopped containers | loses their logs and writable layers |
| 3 | `docker image prune` | dangling (untagged) images | none for running apps |
| 4 | `docker image prune -a --filter until=720h` | unused images older than 30 days | removes images you might roll back to |
| never casually | `docker system prune -a --volumes`, `docker volume prune -a` | everything unused, **including volumes** | data loss |

> `docker system prune -a --volumes` first removes every stopped container, then every volume no
> remaining container uses: a database whose container is stopped for maintenance loses its data if
> that data sits in an anonymous volume (the "no named volume" mistake from section 8). On Engine
> 23+ `--volumes` and plain `docker volume prune` remove only **anonymous** volumes;
> `docker volume prune -a` removes unused **named** volumes too. Use the ordered list above and
> inspect `docker system df -v` first.

**Key terms:** *event* (one daemon action with a timestamp and attributes), *reclaimable* (space that
unused objects hold), *dangling image* (no tag, usually an old build), *build cache* (BuildKit layers
and cache mounts, section 4).

**See it on a real system**

```bash
docker system df
docker events --since 30m --filter type=container --format '{{.Time}} {{.Action}} {{.Actor.Attributes.name}}' | tail -5
```

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          41        9         14.2GB    10.9GB (76%)
Containers      12        9         312MB     41MB (13%)
Local Volumes   7         5         6.8GB     1.1GB (16%)
Build Cache     214       0         8.4GB     8.4GB
1791026401 die shop-web-8f3k2a.1.x7k2m9p4q1r3
1791026402 destroy shop-web-8f3k2a.1.x7k2m9p4q1r3
1791026403 create shop-web-8f3k2a.1.n4b5v6c7x8z9
1791026404 start shop-web-8f3k2a.1.n4b5v6c7x8z9
1791026419 health_status: healthy shop-web-8f3k2a.1.n4b5v6c7x8z9
```

→ 19 GB is reclaimable from images and build cache without touching a running app. The event lines
show a task being replaced and becoming healthy 15 s later: a normal rolling update, or a crash the
orchestrator hid from you. `docker service ps` tells you which.

**Hands-on lab (test VM only)**

**Step 1 — Watch the timeline.** In one terminal run
`docker events --filter type=container --format '{{.Action}} {{.Actor.Attributes.name}} {{.Actor.Attributes.exitCode}}'`.
In another: `docker run --name boom alpine:3.20 sh -c 'exit 3'`, then
`docker run --name hog -m 32m alpine:3.20 sh -c 'tail /dev/zero'`. You see `die … 3`, then `oom`
and `die … 137`.

**Step 2 — Break it: fill the disk with build cache.** Build the Python example from section 4 a few
times with `--no-cache` and different `GIT_SHA` values, then compare `docker system df` before and
after.

**Step 3 — Fix it with the ordered cleanup.** Run steps 1–3 of the cleanup table, then
`docker system df` again. Remove `boom` and `hog`.

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| `no space left on device` on pull or build | `docker system df`; `sudo du -xh --max-depth=1 /var/lib/docker` | [Containers playbook](26-playbook-containers-k8s.md) |
| Disk full but `docker system df` looks small | container log files (`/var/lib/docker/containers/*/*-json.log`) | section 6 |
| "It restarted at night, nobody knows why" | recorded `docker events` or the journal (`journalctl -u docker --since …`) | [Logs & journal](06-logs-journal.md) |
| Rollback impossible: old image pruned | Harbor still has it: pull by SHA tag | section 11 |

**Why it matters for troubleshooting.** Events give you the order of things, and the order is
usually the root cause ("OOM, then restart, then 502s"). `system df` turns "Docker ate the disk" into
a list you can clean safely instead of a panic prune.

**Next step:** look inside an image layer by layer.

### dive and docker history

**Level:** [L2 · Mid]

**Concept.** `docker history` lists an image's layers with the instruction that created each one and
its size. `dive` adds what history cannot show: the **files** each layer adds, changes or deletes,
and "wasted space" (files that a later layer deleted or overwrote but that still ship in an earlier
layer). Use them when an image is unexpectedly large, when a secret might be baked into a layer, or
to confirm that a multi-stage build really left the build tools behind. dive also has a CI mode with
thresholds, so an image that grows fat fails the pipeline.

**Key terms:** *layer* (one filesystem diff per `RUN`, `COPY` or `ADD`), *efficiency* (dive's ratio
of useful bytes to shipped bytes), *wasted space* (bytes removed later but still shipped), *CI mode*
(`CI=true dive IMAGE` with limits such as `--lowestEfficiency` and `--highestUserWastedPercent`).

**See it on a real system**

```bash
docker history --format 'table {{.Size}}\t{{.CreatedBy}}' --no-trunc shop-web:dev | head -12
# dive as a container (it mounts the Docker socket, which is root: lab or CI runner only)
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive shop-web:dev
```

```
SIZE      CREATED BY
0B        CMD ["gunicorn" "--config" "gunicorn.conf.py" "app:app"]
0B        ENTRYPOINT ["tini" "--"]
0B        LABEL org.opencontainers.image.revision=3f9c2a1 …
0B        ARG GIT_SHA=unknown
0B        HEALTHCHECK &{["CMD" "python" "-c" "import urllib.request; …"] …}
0B        EXPOSE map[8000/tcp:{}]
0B        USER 10001:10001
1.24kB    COPY app.py gunicorn.conf.py ./ # buildkit
21.3MB    COPY /opt/venv /opt/venv # buildkit
0B        WORKDIR /app
4.05MB    RUN /bin/sh -c apt-get update  && apt-get install -y --no-install-recommends tini …
```

→ The application layer is about 1 kB; dependencies are 21 MB; the rest is the base image. If a
change to `app.py` re-ships 21 MB, the layer order is wrong (section 4).

**Hands-on lab (test VM only)**

**Step 1 — Break it: delete in a later layer.**

```bash
mkdir -p ~/lab/fat && cd ~/lab/fat
cat > Dockerfile <<'EOF'
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
RUN apt-get purge -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
EOF
docker build -t fat:1 . && docker images fat:1
```

**Step 2 — Measure it.** Run dive on `fat:1`: the purge layer is tiny, but the install layer still
ships hundreds of MB, shown as wasted space.

**Step 3 — Fix it.** Install, use and remove in **one** `RUN`, or better, use a multi-stage build
so the compiler never reaches the final image. Rebuild as `fat:2`, compare sizes, and try CI mode:
`docker run --rm -e CI=true -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive fat:1`
(it exits non-zero when the image fails the default thresholds).

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Image is huge, pulls are slow on every deploy | `docker history --no-trunc IMAGE`; dive | section 4 |
| A token appears in an old layer | `docker history --no-trunc IMAGE | grep -i token`; rotate it, rebuild with a secret mount | section 4 |
| Every build re-uploads the dependency layer | layer order (manifests before source) | section 4 |

**Why it matters for troubleshooting.** Image size is deploy time and disk usage on every node, and
a leaked layer is a leaked credential forever (anyone who can pull the image can read it). Both are
visible in two commands.

**Next step:** use the whole toolkit on one real incident, step by step.

### A debugging walk, step by step

**Level:** [L2 · Mid]

**Concept.** The method is the same for every container incident: start where the user is (the
proxy's answer), then move inwards one layer at a time (orchestrator, process, network, packets),
and **name the broken layer with evidence** before you change anything. Scenario: a Dokploy app
`shop-web-8f3k2a` was redeployed; `https://shop.example.com/` now returns **502**, and the Dokploy UI
shows the app as running.

**Key terms:** *layer isolation* (test one layer at a time, from the outside in), *evidence* (a log
line, a socket listing or a packet capture that proves the layer), *bypass test* (call the backend
directly, without the proxy).

**See it on a real system** — the six steps below are the "see it" part; all commands are
read-only until Step 6.

**Step 1 — Read Traefik's verdict**

**Goal:** confirm the 502 comes from Traefik and see which backend it tried.

```bash
curl -sk -o /dev/null -w '%{http_code}\n' --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/
docker logs --since 10m dokploy-traefik 2>&1 | grep -E '" 50[234] ' | tail -2   # access log must be enabled
```

```
502
203.0.113.50 - - [03/Oct/2026:11:20:04 +0000] "GET / HTTP/2.0" 502 11 "-" "-" 4182 "shop-web-8f3k2a-router-websecure@file" "http://shop-web-8f3k2a:8000" 0ms
```

**What it means:** Traefik matched a router (so DNS, TLS and the Host rule are fine; a routing
problem would be a 404), chose the backend `http://shop-web-8f3k2a:8000`, and failed in **0 ms**.
An instant failure means refused or unresolvable, not slow; a timeout would show thousands of
milliseconds and usually a 504.

**Why this step (now):** it splits the request path in half with one command. Everything in front of
Traefik is proven good, so you stop looking at DNS, certificates and firewalls.

**Next step:** if the access log shows 404 → the router does not match (see the
[Site-down playbook](25-playbook-site-down.md)). If 502 with 0 ms → Step 2. If 504 or a long duration
→ the app is slow or unreachable over the network: go to Step 4.

**Step 2 — Check the service and its tasks**

**Goal:** prove the tasks exist, run the new image and are healthy.

```bash
docker service ps shop-web-8f3k2a --no-trunc --format 'table {{.Name}}\t{{.Image}}\t{{.CurrentState}}\t{{.Error}}' | head -3
docker ps --filter label=com.docker.swarm.service.name=shop-web-8f3k2a --format '{{.Names}}  {{.Status}}'
```

```
NAME                IMAGE                                          CURRENT STATE           ERROR
shop-web-8f3k2a.1   harbor.example.com/shop/web:7d41e0b@sha256:…   Running 6 minutes ago
shop-web-8f3k2a.2   harbor.example.com/shop/web:7d41e0b@sha256:…   Running 6 minutes ago
shop-web-8f3k2a.1.n4b5v6c7x8z9  Up 6 minutes (healthy)
shop-web-8f3k2a.2.m3n4b5v6c7x8  Up 6 minutes (healthy)
```

**What it means:** both tasks run the new SHA `7d41e0b` and report **healthy**. The health check runs
*inside* the container, so "healthy" only proves the app answers on its own loopback.

**Why this step (now):** a missing or crash-looping task would explain the 502 immediately and is
cheaper to check than the network. It also tells you the change that preceded the incident: a new
image.

**Next step:** if tasks are missing, Pending or Failed → read the ERROR column and
`docker service logs` (section 14). If they run and are healthy → Step 3.

**Step 3 — See what the app listens on, inside its namespace**

**Goal:** compare the app's listening address with the port Traefik uses.

```bash
CID=$(docker ps -q --filter label=com.docker.swarm.service.name=shop-web-8f3k2a | head -1)
PID=$(docker inspect -f '{{.State.Pid}}' "$CID")
sudo nsenter -t "$PID" -n ss -ltn
sudo nsenter -t "$PID" -n ip -br addr
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      2048       127.0.0.1:8000      0.0.0.0:*
lo               UNKNOWN        127.0.0.1/8
eth0@if41        UP             10.0.1.12/24
eth1@if43        UP             172.18.0.4/16
```

**What it means:** the app listens on **127.0.0.1:8000** only. Traffic from Traefik arrives on eth0
(10.0.1.12, the `dokploy-network` address), where nothing listens, so the kernel refuses it. eth1 is
`docker_gwbridge`, the outbound path. Good would be `0.0.0.0:8000` (or `*:8000`).

**Why this step (now):** Step 2 proved the process is alive, so the next cheapest question is
whether it listens where Traefik connects. nsenter answers it without a shell in the image and
without restarting anything.

**Next step:** if it listens on 127.0.0.1 → this is the cause; collect one more piece of evidence in
Step 5, then fix in Step 6. If it listens on 0.0.0.0 but on another port (for example 3000) → the
Dokploy domain's container port is wrong: Step 6. If it listens on 0.0.0.0:8000 → Step 4.

**Step 4 — Test from Traefik's network**

**Goal:** reproduce Traefik's connection from a peer on `dokploy-network`.

```bash
docker run --rm --network dokploy-network nicolaka/netshoot sh -c '
  dig +short shop-web-8f3k2a; dig +short tasks.shop-web-8f3k2a;
  curl -sS -o /dev/null -w "%{http_code}\n" --max-time 3 http://shop-web-8f3k2a:8000/healthz'
```

```
10.0.1.9
10.0.1.12
10.0.1.13
curl: (7) Failed to connect to shop-web-8f3k2a port 8000 after 1 ms: Couldn't connect to server
000
```

**What it means:** the name resolves to a VIP and two task IPs, so the service **is** on
`dokploy-network`; the connection is refused at once, matching Traefik's 0 ms. If `dig` printed
nothing, the app is not on Traefik's network; if curl timed out instead, packets are being dropped
(firewall rules, VXLAN between nodes, section 14).

**Why this step (now):** it is the bypass test: same network as Traefik, no Traefik in the path. It
separates "the proxy is misconfigured" from "the backend cannot be reached by anyone".

**Next step:** refused → Step 5 for packet proof, then Step 6. No DNS answer → attach the app to
`dokploy-network` in Dokploy and redeploy. Timeout → capture on both ends (Step 5) and check
section 14's VXLAN topic.

**Step 5 — Prove it at the packet level**

**Goal:** see the SYN arrive and the kernel answer with a reset.

```bash
sudo nsenter -t "$PID" -n tcpdump -ni eth0 -c 2 'tcp port 8000'
# meanwhile, in another terminal, repeat the netshoot curl from Step 4
```

```
11:24:10.501122 IP 10.0.1.4.51234 > 10.0.1.12.8000: Flags [S], seq 1234567890, win 64860, length 0
11:24:10.501160 IP 10.0.1.12.8000 > 10.0.1.4.51234: Flags [R.], seq 0, ack 1234567891, win 0, length 0
```

**What it means:** the SYN from 10.0.1.4 (Traefik or netshoot) reaches the container, and the
container's kernel replies RST: "nothing listens on this address and port". The network is fine; the
app's bind address is wrong.

**Why this step (now):** one capture turns a strong hypothesis into proof, and it costs seconds. It
also rules out every network layer at once for the postmortem.

**Next step:** RST → Step 6 (fix the bind address). SYN never arrives → the problem is between
Traefik and the task: firewall rules, overlay, or the wrong network.

**Step 6 — Fix and verify**

**Goal:** make the app listen on all interfaces, redeploy, and prove the fix end to end.

```bash
# The new release changed the bind address. Fix it in the app config (gunicorn: bind = "0.0.0.0:8000",
# or the app's HOST/BIND environment variable), commit, let CI build a new SHA, deploy it in Dokploy.
docker service ps shop-web-8f3k2a --format '{{.Name}} {{.Image}} {{.CurrentState}}' | head -2
sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' "$(docker ps -q --filter label=com.docker.swarm.service.name=shop-web-8f3k2a | head -1)")" -n ss -ltn
curl -sk -o /dev/null -w '%{http_code}\n' --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/
```

```
shop-web-8f3k2a.1 harbor.example.com/shop/web:a9c3f52 Running 40 seconds ago
shop-web-8f3k2a.2 harbor.example.com/shop/web:a9c3f52 Running 25 seconds ago
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      2048         0.0.0.0:8000      0.0.0.0:*
200
```

**What it means:** new SHA on both tasks, listening on 0.0.0.0, and the public URL answers 200.
Check the Traefik access log once more for 200s from real clients.

**Why this step (now):** you change exactly one thing, only after the broken layer is proven, and you
verify at the same place you started (the user's URL), so the incident is closed with evidence.

**Next step:** if it is still 502 → go back to Step 3 on the new task (the fix may not be in the
deployed image). If 200 → write the five-line note and the prevention items below.

**Decision tree**

```
502 from the domain
 ├─ Traefik access log shows 404 ............ router/Host rule (Site-down playbook)
 ├─ 502 in ~0 ms
 │   ├─ tasks missing / failing ............. service ps + service logs (section 14)
 │   ├─ app listens on 127.0.0.1 ............ fix the bind address, redeploy
 │   ├─ app listens on another port ......... fix the container port in the Dokploy domain
 │   └─ dig from dokploy-network is empty ... attach the app to dokploy-network
 └─ 504 / long duration
     ├─ SYN never reaches the task .......... firewall, VXLAN 4789, wrong network (section 14)
     └─ SYN reaches, app slow ................ app logs, worker timeouts (Site-down playbook)
```

**Fix & verify:** bind to `0.0.0.0` in the app config, redeploy through CI and Dokploy, confirm with
`nsenter … ss -ltn`, the netshoot curl and the public `curl --resolve`.

**Rollback:** if the fix cannot ship quickly, redeploy the previous image SHA in Dokploy (the last
release that listened on 0.0.0.0), verify with the same three checks, and fix forward afterwards.

**Prevent it next time:** add a CI smoke test that runs the image with `-p 127.0.0.1:18000:8000` and
curls it from the host (a loopback-only app fails it); make the bind address a fixed part of the
Dockerfile or entrypoint, not an app default; add an external uptime check through Traefik so a
"healthy but unreachable" app pages someone in minutes.

**Hands-on lab (test VM only)** — rebuild this exact incident with the Python example from section 4
on a Dokploy test VM: deploy it, change `bind` to `127.0.0.1:8000`, redeploy, and walk Steps 1–6
without looking at the answers.

**How it breaks**

| Symptom | Step that finds it | Playbook |
|---|---|---|
| 404 from Traefik | Step 1 | [Site-down playbook](25-playbook-site-down.md) |
| 502 in 0 ms, healthy tasks | Steps 3–5 | [Containers playbook](26-playbook-containers-k8s.md) |
| 502/504 after a delay | Steps 4–5 | [Containers playbook](26-playbook-containers-k8s.md) |
| Tasks Pending or Rejected | Step 2 | section 14 |

**Why it matters for troubleshooting.** This is the method in miniature: outside in, one layer per
step, evidence before change, verify where you started. It is the same walk as the
[Site-down playbook](25-playbook-site-down.md), applied inside a container platform.

**Next step:** prove you can do it alone: the L3 drills and the exit test.

---

## 16. L3 drills and exit test

> 📚 **Study path:** 1) Note: the [Apache 443 case](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md) first, because this section applies them · 2) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Integration with GitLab, then Self-Managed Runners ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 3) KodeKloud: *Kubernetes Networking Deep Dive* — Traefik Overview, for Traefik concepts ([note](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page)) · 4) Official: Traefik Docker routing ([docs](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/)) and Dokploy *Domains & Traefik* troubleshooting ([docs](https://docs.dokploy.com/docs/core/troubleshooting/domains)) · 5) Practice: the drills below on two lab VMs, then the exit test on a staging copy of a real Apache app.

Your Ops Ladder ends L3 with five drills and one weekend exit test. This section collects them,
says where each one is taught in this module, and adds the one drill that had no home yet: making
Traefik fail on purpose.

### Your L3 drill checklist

**Level:** [L3 · Senior]

**Concept.** A drill is a timed rep of one skill on a lab, done until you can do it without notes.
Tick each one only when you can do it alone, inside the time limit, and explain every command.

| # | Ops Ladder drill | Where it is taught | Done when | Time limit |
|---|---|---|---|---|
| 1 | Build a bridge network by hand with ip netns and veth pairs, then the Docker roadmap networking challenges | section 7, lab topic; [iximiuz Docker roadmap](https://labs.iximiuz.com/roadmaps/docker) | two namespaces talk to each other and to the LAN; you can name the four failure rows | 45 min |
| 2 | Attach netshoot to a running container's network namespace and capture its DNS queries with tcpdump | section 15, netshoot topic | you show which names stay on `lo` and which go upstream, and to which resolver | 20 min |
| 3 | Make Traefik return 502 on purpose with a wrong port, then find and fix it from Traefik's logs alone | next topic | fixed using only Traefik's log lines, no `docker inspect` | 15 min |
| 4 | GitLab CI pipeline that builds an image, tags it with the commit SHA and pushes it to Harbor | section 11, drill topic | a push to `main` produces `harbor.example.com/PROJECT/APP:SHA`, scanned | 60 min |
| 5 | Ansible playbook that installs Docker with your daemon.json (DNS servers and log rotation) on a fresh VM | section 12, drill topic | the second run reports `changed=0`; a broken daemon.json never reaches the host | 45 min |

**Key terms:** *drill* (a timed, repeatable rep), *exit test* (the integrated task that proves the
level), *done when* (an observable result, not "I read it").

**See it on a real system** — the evidence for each drill is a command output you can paste into
your notes: `ip netns list` and a successful ping (1), the tcpdump lines (2), the Traefik log line
before and after (3), the pipeline page and `docker manifest inspect` of the SHA tag (4), the
`PLAY RECAP` with `changed=0` (5).

**Hands-on lab (test VM only)** — do one drill per morning slot (Ops Ladder rhythm), in the order of
the table, then repeat the whole set a week later without notes and record your times.

**How it breaks** — the failure tables in each drill's home topic list what usually goes wrong; when
a drill takes more than twice its time limit, reread that topic's "How it breaks" before retrying.

**Why it matters for troubleshooting.** Each drill is one of your real incidents in small: the
bridge (Docker networking), DNS (the 8.8.8.8 fallback), the 502 (Dokploy routing), CI (what is
running?), Ansible (rebuildable hosts).

**Next step:** drill 3, the only one taught here.

### Drill: Traefik 502 from the logs alone

**Level:** [L3 · Senior]

**Concept.** Traefik's two logs answer different questions. The **access log** has one line per
request: status, router name, the backend URL Traefik chose, and the duration. The **general log**
at DEBUG level explains failures (`connection refused`, `no such host`, `i/o timeout`). Together
they tell you which layer failed without touching the backend. Dokploy's Traefik is the same
software; only the configuration source differs (file provider and labels).

| Traefik answer | Typical meaning |
|---|---|
| `404 page not found` | no router matched (Host rule, entrypoint, router not loaded) |
| 502 in a few ms | backend refused or name did not resolve: wrong port, app on 127.0.0.1, wrong network |
| 504 after a long wait | backend unreachable or too slow: firewall, overlay, app timeouts |
| default certificate on HTTPS | no router with TLS for that host, or certificate not issued yet |

**Key terms:** *access log* (one line per request), *router* (rule plus entrypoint plus service),
*service URL* (the backend address Traefik chose), *DEBUG log* (the reason behind a 5xx).

**See it on a real system**

```bash
docker logs --tail 20 dokploy-traefik 2>&1 | grep -E 'level=(error|warn)|ERR|WRN'
docker logs --since 10m dokploy-traefik 2>&1 | grep -E '" 5[0-9]{2} ' | tail -3
```

→ On a Dokploy host, enable the access log first if it is off (the [Apache 443 case](21-case-apache-443-dokploy.md)
shows how), otherwise only errors are logged.

**Hands-on lab (test VM only)**

**Step 1 — Build it.** A Traefik v3 container and one backend, on a user-defined network:

```bash
mkdir -p ~/lab/traefik502 && cd ~/lab/traefik502
cat > compose.yaml <<'EOF'
services:
  traefik:
    image: traefik:v3.6
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.network=traefik502_default
      - --entrypoints.web.address=:80
      - --accesslog=true
      - --log.level=DEBUG
    ports:
      - "127.0.0.1:8088:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro   # root-equivalent (section 13); lab only
  whoami:
    image: traefik/whoami:v1.10.1
    labels:
      - traefik.enable=true
      - traefik.http.routers.whoami.rule=Host(`whoami.lab.example.com`)
      - traefik.http.routers.whoami.entrypoints=web
      - traefik.http.services.whoami.loadbalancer.server.port=80
EOF
docker compose up -d
curl -s -H 'Host: whoami.lab.example.com' http://127.0.0.1:8088/ | head -2
```

**Step 2 — Break it: the wrong port.** Change the port label to `8081`, run `docker compose up -d`,
then:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: whoami.lab.example.com' http://127.0.0.1:8088/
docker compose logs --since 2m traefik | grep -E '" 502 |connection refused'
```

```
502
traefik-1  | 172.22.0.1 - - [03/Oct/2026:11:02:13 +0000] "GET / HTTP/1.1" 502 11 "-" "-" 3 "whoami@docker" "http://172.22.0.3:8081" 1ms
traefik-1  | 2026-10-03T11:02:13Z DBG … 502 Bad Gateway error="dial tcp 172.22.0.3:8081: connect: connection refused"
```

→ From the logs alone: router `whoami@docker` matched, backend `172.22.0.3:8081` refused in 1 ms.
The container exists (it has an IP) but nothing listens on 8081. Fix the label back to `80` and
redeploy. (Exact log formats differ between Traefik versions; the fields are the same.)

**Step 3 — Break it: the wrong Host rule.** Change the rule to `whoami.lab.example.org`: curl now
gets `404 page not found`, and the access log names no router. Fix the rule.

**Step 4 — Break it: no shared network.** Put `whoami` on its own network
(`networks: [isolated]` plus a top-level `networks: { isolated: {} }`). Traefik either skips the
container or logs that it cannot reach it, and requests fail with 404, 502 or 504 depending on
version. Fix it by putting both on the network named in `--providers.docker.network` (on Dokploy:
`dokploy-network`). Finish with `docker compose down`.

**How it breaks**

| Symptom / log text | Layer | Fix |
|---|---|---|
| `connect: connection refused` to the right IP | port or bind address | service port label / Dokploy container port; app binds 0.0.0.0 |
| `lookup NAME … no such host` | network membership | attach the app to Traefik's network |
| `404 page not found`, no router in the access log | routing | Host rule, entrypoint, `traefik.enable=true` |
| `client version 1.24 is too old` in Traefik's log, no routers at all | Traefik too old for the Docker Engine API | upgrade Traefik (recent Docker releases dropped old API versions) |

**Why it matters for troubleshooting.** In Dokploy you often cannot attach a debugger to every app,
but you can always read Traefik. Reading status, router, backend URL and duration from one line is
the fastest triage you have for any web app behind it.

**Next step:** the exit test, where all of this runs together on a real workload.

### Exit test: one Apache app to Dokploy

**Level:** [L3 · Senior] (exit test)

**Concept.** The Ops Ladder L3 exit test, word for word: *move one of your three Apache workloads into
a container behind Dokploy, built by a GitLab CI pipeline that pushes to your Harbor registry, with a
written rollback you have actually tested.* It is your real incident finished properly: in the
[Apache 443 case](21-case-apache-443-dokploy.md) you moved Apache to ports 81 and 444 so that
Dokploy's Traefik could own 80 and 443; this test migrates one app off Apache entirely. Budget one
weekend on a staging copy first, then repeat it for real inside a change window.

```
 GitLab push ──▶ CI: test → build → push harbor/…/APP:SHA → Trivy scan
                                                  │
 Dokploy: Application (image APP:SHA, registry creds) ──▶ Swarm service on dokploy-network
                                                  │
 Traefik :443 ── Host(app.example.com) ──▶ APP service :8080        (was: Apache vhost on :444)
 rollback A: redeploy previous SHA      rollback B: route back to the Apache vhost (kept, disabled)
```

**Key terms:** *acceptance criterion* (an observable pass condition), *cutover* (the moment traffic
moves), *rollback A / B* (previous image vs previous platform), *change window* (agreed time with
a rollback plan, see [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md)).

**See it on a real system** — before you start, collect the facts from the inventory you built in
the case study:

```bash
sudo apache2ctl -S 2>/dev/null | grep -E 'namevhost|port'         # which vhost, which port
grep -RhiE 'DocumentRoot|ProxyPass |SetHandler' /etc/apache2/sites-enabled/APP.conf
sudo tail -n 3 /var/log/apache2/APP-access.log                    # last real traffic
php -v 2>/dev/null | head -1                                      # PHP version to match in the image
```

**Hands-on lab (staging copy first)** — each phase has a "done when":

**Phase 1 — Pick the app.** The smallest, least-visited vhost with no shared state (sessions on
disk, uploads, cron jobs) is the best first candidate. Done when: you can name its DocumentRoot or
backend, PHP version, writable paths, cron jobs, log files and owner.

**Phase 2 — Containerize it.** A PHP site usually fits the official `php:8.3-apache` image (match the
PHP version you found), a static site fits nginx, and a proxied app gets its own Dockerfile as in
section 4. Listen on an unprivileged port inside (8080; for `php:8.3-apache` that means changing
`Listen` in `ports.conf` and the default vhost in the Dockerfile), write logs to stdout/stderr, keep
uploads in a volume, add a `HEALTHCHECK`. Done when: `docker run -p 127.0.0.1:18080:8080 IMAGE` serves the site
on the lab VM and `docker logs` shows the requests.

**Phase 3 — CI to Harbor.** Reuse drill 4: test, build, push `APP:SHA`, scan. Done when: a commit
produces a scanned image in Harbor without you touching the runner.

**Phase 4 — Deploy in Dokploy.** Add the Harbor registry (and make sure every Swarm node trusts the
private CA in `/etc/docker/certs.d/HARBOR_HOST/ca.crt`), create an Application from the image
`harbor.example.com/PROJECT/APP:SHA`, set the domain, container port 8080 and HTTPS. Verify the menu
names against https://docs.dokploy.com/ for your version. Done when the test below returns 200 with a
valid certificate **before** DNS changes:

```bash
curl -sv --resolve app.example.com:443:192.0.2.10 https://app.example.com/ -o /dev/null 2>&1 \
  | grep -E 'subject:|issuer:|expire date:|< HTTP'
docker service ps APP_SERVICE --no-trunc --format '{{.Name}} {{.Image}} {{.CurrentState}}'
```

**Phase 5 — Cut over.** If the domain already reaches this host through Traefik, routed to Apache on
port 81 or 444 (see [Deployment patterns](35-deployment-patterns.md)), remove that route so the
Dokploy domain takes over; otherwise change the DNS record. Watch the Traefik access log and the
app's service logs, then disable (not delete) the Apache vhost: `sudo a2dissite APP && sudo apache2ctl configtest && sudo systemctl reload apache2`.
Done when real client traffic shows in `docker service logs` and none in the old Apache log.

**Phase 6 — Test both rollbacks, with a stopwatch.** Rollback A: redeploy the previous SHA in Dokploy,
verify, redeploy the current one. Rollback B: `sudo a2ensite APP`, reload Apache, restore the Traefik
route to Apache (or the DNS record), verify, then return to Dokploy. Done when both are written as numbered steps with their
measured times.

**Phase 7 — Write it up.** A runbook (what you did, in order, with verification), the five-line
note (symptom, first wrong guess, evidence, fix, what you check first next time) and a short
postmortem-style summary for your portfolio ([Career ladder](40-career-ladder.md)).

| Acceptance criterion | How you prove it |
|---|---|
| Image built by CI, tagged with the commit SHA, in Harbor | pipeline URL; `docker manifest inspect harbor.example.com/PROJECT/APP:SHA` |
| No critical unfixed CVEs | the Trivy job log |
| Served by Dokploy over HTTPS with a valid certificate | `curl -sv` output above, from outside the host |
| Real client IPs in the app logs | `X-Forwarded-For` handling ([Web servers & proxies](29-learn-webservers-proxies.md)) |
| Apache no longer serves it | vhost disabled; `apache2ctl -S` no longer lists it |
| Rollback A and B tested and timed | your runbook with times |
| Nothing new exposed | `sudo ss -ltnp` and the DOCKER-USER rules (section 7) show no new public ports |

**How it breaks**

| Symptom | First command | Playbook |
|---|---|---|
| Image works locally, `Forbidden` or blank page in Dokploy | `docker service logs APP_SERVICE`; file ownership of the volume (`ls -ln`) | section 8 |
| Redirect loop after cutover | the app thinks it is on HTTP: `X-Forwarded-Proto` handling | [Site-down playbook](25-playbook-site-down.md) |
| Let's Encrypt certificate not issued | port 80 reachable from the internet and the DNS A record | [Containers playbook](26-playbook-containers-k8s.md) |
| Uploads vanish after a redeploy | uploads not on a volume | section 8 |
| Swarm node cannot pull from Harbor | CA on that node; registry credentials in Dokploy | section 11 |

**Why it matters for troubleshooting.** It joins every layer of this module in one change you own
end to end, with a rollback you have proved. It is also the best answer you will ever have to the
interview question "tell me about a migration you led" ([Career ladder](40-career-ladder.md)).

**Next step:** check yourself against every stage of this module.

---

## 17. Self-check and exit test

Answer without notes, then check the section named in the last column. A stage is done when you can
answer all its questions and pass its timed tasks.

### Questions by career stage

**Fresher [L0 · Fresher]**

| Question | A good answer contains | Section |
|---|---|---|
| What is the difference between an image and a container? | read-only template vs a running instance with its own writable layer | 1 |
| Why does `docker run alpine uname -r` print the host's kernel version? | containers share the host kernel; only the userland comes from the image | 1 |
| What happens to files written inside a container when you `docker rm` it? | they are gone unless they were in a volume or bind mount | 8 |
| A container exits right after starting. Which two commands do you run first? | `docker ps -a` (exit code), `docker logs CONTAINER` | 5 |

**Junior [L1 · Junior]**

| Question | A good answer contains | Section |
|---|---|---|
| `port is already allocated` vs `address already in use`: what owns the port in each case? | another container vs a non-Docker process; `docker ps --filter publish=PORT` / `ss -ltnp` | 1 |
| Why use exec form for `CMD` and `ENTRYPOINT`? | shell form makes `/bin/sh` PID 1, signals are lost, `docker stop` waits 10 s and kills | 4 |
| Where does a json-file container log live, and how do you stop it filling the disk? | `/var/lib/docker/containers/ID/ID-json.log`; `max-size`/`max-file` in daemon.json; recreate containers | 6 |
| What do you deploy to production: a tag or a digest? | an immutable SHA tag, ideally pinned by digest; never `latest` | 3 |
| Does `EXPOSE` restrict access to other ports? | no; it is metadata, used by `-P` and by Traefik's port guess | 4 |
| `unless-stopped` vs `always` after a reboot | `always` restarts a container you stopped by hand; `unless-stopped` respects your stop | 10 |
| Why must the `docker` group stay small? | membership is root on the host | 13 |

**Mid-level [L2 · Mid]**

| Question | A good answer contains | Section |
|---|---|---|
| Two containers on the default bridge cannot resolve each other's names. Why, and the fix? | embedded DNS works only on user-defined networks; create one and attach both | 7 |
| Walk a packet from the internet to a published container port. | PREROUTING DNAT, FORWARD with DOCKER-USER first, bridge, veth, container eth0; conntrack reverses on the way back | 7 |
| UFW denies 8080, yet 8080 is reachable from the internet. Why, and two fixes? | DNAT happens before UFW's rules; publish on 127.0.0.1, or filter in DOCKER-USER | 7 |
| Exit code 137: how do you prove OOM rather than a manual kill? | `State.OOMKilled`, `memory.events` `oom_kill`, `docker events --filter event=oom`, kernel log | 10 |
| The image has no shell. How do you see its listening sockets? | `nsenter -t PID -n ss -ltn`, or netshoot with `--net container:` | 15 |
| External names fail only inside containers on-prem. What do you check? | where the queries go (netshoot capture); 8.8.8.8 fallback; daemon.json `dns` | 15 |
| Traefik returns 502 in 0 ms and the task is healthy. Most likely cause? | the app listens on 127.0.0.1 inside the container, or the wrong container port | 15 |

**Senior [L3 · Senior]**

| Question | A good answer contains | Section |
|---|---|---|
| Which namespaces does a container get by default, and which does it share with the host? | pid, net, mnt, uts, ipc, cgroup are new; user and time are shared unless userns is enabled | 2 |
| Why does deleting a file in a later layer not shrink the image? | layers are immutable; a whiteout hides the file but the earlier layer still ships | 3, 15 |
| Why set `default-address-pools` before the first deploy on-prem? | Docker routes hijack real subnets; existing networks keep their subnets | 12 |
| Why is `live-restore` not allowed on a Dokploy host? | it is incompatible with Swarm mode; dockerd refuses to start | 12 |
| In Swarm DNS, what is the difference between `web` and `tasks.web`? | the VIP (load-balanced) vs every task's own IP | 14 |
| One Swarm node cannot pull from Harbor while the manager can. Two causes? | no `--with-registry-auth`; the private CA is missing in that node's `/etc/docker/certs.d/HOST/` | 11, 14 |
| How do you rotate a Swarm secret without downtime? | create `NAME_v2`, update the service to it (same target), remove the old one, change it in the backing system | 14 |
| Design: how do you guarantee a Dokploy app can roll back in under five minutes? | SHA tags, images kept in Harbor, a written redeploy procedure, rollback tested and timed | 16 |

### Timed practical tasks

| Stage | Task (test VM or lab only) | Time limit | Pass when |
|---|---|---|---|
| Fresher | Run nginx published on 127.0.0.1:8080, read its logs, stop and remove it | 10 min | curl works, logs show the request, nothing left in `docker ps -a` |
| Junior | Write the Python Dockerfile from section 4 from memory: multi-stage, non-root, exec form, health check | 30 min | builds, runs with `--read-only`, shows `(healthy)`, stops in under 2 s |
| Junior | Configure log rotation in daemon.json and prove new containers use it | 15 min | `docker inspect` shows the `max-size` on a new container |
| Mid | A partner breaks one of: loopback bind, wrong network, DOCKER-USER drop, DNS fallback. Find and fix it | 20 min each | broken layer named with evidence before any change |
| Mid | From `ss -ltnp` alone, find which container owns host port 443 and where its logs are | 5 min | container name, image and log path written down |
| Senior | Two-node swarm, attachable overlay, two-replica service, rolling update, forced failure, rollback | 45 min | `docker service ps` history shows the rejected update and the rollback |
| Senior | All five L3 drills (section 16) | one week of morning slots | every drill inside its limit, without notes |
| Senior (exit) | The L3 exit test: one Apache app to Dokploy | one weekend | every acceptance criterion in section 16 proved |
| Senior/Lead | Game day: a script breaks one container-platform thing at random; you learn of it from an alert, fix it, publish a postmortem | half a day | alert fired, fix verified, one-page postmortem with timeline ([SRE practice](33-learn-cicd-iac-sre.md)) |

---

## 18. Where to go next

- **Kubernetes:** [Learn Kubernetes](31-learn-kubernetes.md). Same namespaces, cgroups and image layers, with containerd and `crictl` instead of dockerd. The KodeKloud lesson *Docker vs ContainerD* ([note](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page)) bridges the two, and the CKA stays your top priority.
- **Incidents:** [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) for every failure named in the "How it breaks" tables, and the [Docker reference](14-docker-containers.md) for quick commands.
- **Your migration:** [Apache 443 case](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md), which take your Apache-on-81/444 setup to Traefik routing and zero-downtime releases.
- **Proxies in depth:** [Web servers & proxies](29-learn-webservers-proxies.md) for Traefik routers, middlewares, certificates and real client IPs.
- **Operate it:** [Observability](32-learn-performance-observability.md) for container metrics and alerts, [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for pipelines, Ansible, change requests and game days.
- **Harden it:** [Security & DevSecOps](37-learn-security-devsecops.md) for supply-chain security, scanning policy and secrets management beyond a single host.
- **Your path:** [Career ladder](40-career-ladder.md) for what each stage expects, and the [Roadmap](34-roadmap.md) for where this module sits in the whole curriculum.
