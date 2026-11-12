# 44 — Real-World Problems: Docker, Compose, Swarm, Portainer & Harbor

This module collects 40 problems that engineers really hit with Docker Engine, BuildKit, Compose v2, Swarm, Portainer, Docker Hub and Harbor, from "Cannot connect to the Docker daemon" on day one to a Swarm that lost its managers or a Harbor whose disk stays full after you deleted every old tag. The problems come from the most-viewed topics on forums.docker.com, GitHub issues of moby, compose, buildx, Portainer and Harbor sorted by reactions and comments, and the official docs; Stack Overflow and Reddit are reachable through search links. The fundamentals live in [Learn Docker](30-learn-docker.md); this module is the library of what goes wrong. Every command is documented for you to run on your own lab VMs or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Docker problems look random until you see that almost all of them sit in one of five places: the daemon and its config, the disk, the network between containers and the host, the registry and its trust, and the orchestrator (Swarm) on top. Dokploy, Portainer, Traefik and your GitLab runners all stand on that floor, so when it cracks they all fail at once. Use the part that matches your stage, then move up.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | entries 1.1, 3.1, 4.3 and 2.1 | you can tell "the daemon is down" from "I may not talk to it" and free a port without guessing |
| Junior | L1 Operator | sections 2 and 3, entries 1.2, 1.3, 1.5, 1.6, 4.1, 4.2, 4.6, 5.1, 5.2, 6.1, 7.1, 7.2, 8.1 | you keep a Docker host healthy for a month: disk, logs, restarts, pulls and Compose edits that land |
| Mid-level | L2 Troubleshooter | entries 1.4, 4.4, 4.5, 4.7, 5.3, 6.2, 8.2 to 8.6 and 9.1 to 9.4 | you prove from evidence why a port is open, a pull fails with x509 or a Swarm update stalled, and fix the cause |
| Senior | L3 Platform | entries 6.3, 8.7, 9.5 and every *Prevent it* paragraph | daemon.json, the IP plan, the registry and the Swarm topology are standards in Git, not tribal knowledge |
| Senior/Lead | L4 SRE | the Self-check exercises 9 and 10, plus [Career ladder](40-career-ladder.md) | upgrades are staged and pinned, Harbor has a tested DR copy, and others follow your runbooks |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** build three Ubuntu 24.04 lab VMs: dokploy-1 (4 vCPU, 8 GB RAM, Swarm manager with Dokploy), dokploy-2 (2 vCPU, 4 GB RAM, Swarm worker) and harbor-1 (2 vCPU, 4 GB RAM, 80 GB disk, Harbor with your lab CA). A Proxmox host is useful for entries 1.4 and 1.6 but not required; the KodeKloud Docker playground covers everything that needs only one host. Snapshot first, break one thing at a time on purpose, then fix it using only the entry. After each fix, write a five-line note: symptom, evidence, cause, fix, prevention. Never practise on production.

**On-prem or cloud:** most Docker problems are the same everywhere. Where the answer really differs (address ranges, DNS and proxies, firewalls between Swarm nodes, certificates) the entry shows an on-premise and a cloud (AWS) variant; the switch at the top of the page shows one, the other or both.

**Placeholders and examples:** UPPERCASE words are placeholders (CONTAINER, SERVICE, IMAGE, NODE, PROJECT, TOKEN). The examples use dokploy-1 (public 192.0.2.10, private 10.10.0.10) as the Swarm manager running Dokploy and Traefik, dokploy-2 (10.10.0.20) as a worker, runner-1 (10.10.0.30) as a GitLab runner and build host, harbor-1 (10.10.0.40) serving harbor.example.com with a certificate from your private CA (file example-ca.crt), the office LAN 10.10.0.0/24 with internal DNS on 10.10.0.2 and an HTTP proxy at proxy.example.com:3128, VPN clients in 172.20.0.0/16, the overlay dokploy-network on 10.0.1.0/24, the user ops and the network interface ens18.

> 📚 **Study path:** KodeKloud [*Docker Training Course for the Absolute Beginner*](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner) (Docker Compose → Docker Networking → Docker Registry) → [*Docker Certified Associate*](https://kodekloud.com/courses/docker-certified-associate-exam-course) (Docker Engine, Docker Image Management, Docker Swarm) → handbook [Learn Docker](30-learn-docker.md) (§7 networking, §11 registries and Harbor, §12 daemon.json, §14 Swarm for Dokploy) → [Docker docs](https://docs.docker.com/) and [Harbor docs](https://goharbor.io/docs/) → lab: the KodeKloud [Docker playground](https://kodekloud.com/playgrounds/playground-docker), then your three VMs and the Self-check.

---

## 1. Daemon, access and upgrades

The daemon is the floor everything stands on. These entries cover a daemon that will not start or cannot be reached, who is allowed to talk to it, and the upgrades that broke Traefik, Portainer and Proxmox containers across the community in 2025 and 2026.

### 1.1 Cannot connect to the Docker daemon

> **Seen as:** `Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?`, or `docker.service: Failed with result 'exit-code'` right after an edit to /etc/docker/daemon.json · **Where:** fresh installs, after a reboot, after a daemon.json change, or in a shell or CI job where DOCKER_HOST points somewhere else · **Level:** [L0 · Fresher] · **How common:** about 1.29 million views on forums.docker.com, the most-reacted docker/compose issue of its kind (#4181, 226 reactions) and a first-week question for every new engineer

**Why it happens:** the message covers three different situations. Most often dockerd is not running because it refused to start: daemon.json is invalid JSON (a trailing comma), contains an unknown key, or sets a directive that the systemd unit already passes as a flag. The classic is `"hosts"` in daemon.json while the unit starts `dockerd -H fd://`. Less often the client looks in the wrong place: DOCKER_HOST is exported in a profile, or `docker context use` switched to a remote or rootless endpoint. The third case, the daemon running but your user not allowed on the socket, prints *permission denied* instead and is entry 1.2.

**Diagnose:**

```bash
systemctl status docker --no-pager | head -4
sudo journalctl -u docker -b --no-pager | grep -E 'unable to configure|failed to start' | tail -3
sudo dockerd --validate --config-file /etc/docker/daemon.json     # checks the file only, not the unit's flags
echo "DOCKER_HOST=${DOCKER_HOST:-unset}"; docker context ls
```

```text
× docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: failed (Result: exit-code) since Sat 2026-10-03 09:02:11 UTC; 40s ago
Oct 03 09:02:11 dokploy-1 dockerd[2214]: unable to configure the Docker daemon with file /etc/docker/daemon.json: the following directives are specified both as a flag and in the configuration file: hosts: (from flag: [fd://], from file: [unix:///var/run/docker.sock tcp://0.0.0.0:2375])
configuration OK
DOCKER_HOST=unset
NAME        DESCRIPTION                               DOCKER ENDPOINT               ERROR
default *   Current DOCKER_HOST based configuration   unix:///var/run/docker.sock
```

**What the output tells you:** the file is valid JSON (`configuration OK`), so the problem is the combination: someone added `"hosts"` to expose the API on TCP 2375, and the unit already passes `-H fd://`. The client side is fine (no DOCKER_HOST, default context). If validation had failed you would see the line and column of the JSON error instead; if dockerd were running and the context pointed at `ssh://` or a rootless socket, you would fix the client, not the daemon.

**Fix:**

```bash
sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
sudo nano /etc/docker/daemon.json            # remove the "hosts" key
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
sudo systemctl enable docker                 # start on boot, not only on socket activation
# Client pointing elsewhere
unset DOCKER_HOST; docker context use default
# Remote administration without opening 2375: an SSH context
docker context create dokploy-1 --docker host=ssh://ops@10.10.0.10
docker --context dokploy-1 ps
```

**Why this fix works:** dockerd refuses to start when the same directive arrives twice, so removing one source lets it start. An SSH context reuses your SSH keys and the remote socket's permissions, so nothing new listens on the network. Never "fix" remote access with `tcp://0.0.0.0:2375`: an unauthenticated Docker API is root on the host for anyone who can reach the port, and scanners find it within hours. If you really need a TCP listener, use TLS client certificates on 2376 and move all `-H` flags into a systemd drop-in so there is a single source.

**Prevent it:** keep daemon.json in Git or Ansible, run `dockerd --validate` before every restart, and alert on `docker.service` entering the failed state (node_exporter's systemd collector, see [Observability problems](49-observability-stack-problems.md)).

**Next step:** [The daemon and daemon.json](30-learn-docker.md) (§12) · [Containers playbook](26-playbook-containers-k8s.md) (§2) · KodeKloud: *Docker Certified Associate* — Docker Engine → [Troubleshooting Docker Daemon](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page) · [Docker docs: troubleshoot the daemon](https://docs.docker.com/engine/daemon/troubleshoot/)

**Community threads:** [forums.docker.com all-time top topics](https://forums.docker.com/top?period=all) · [docker/compose #4181: Couldn't connect to Docker daemon](https://github.com/docker/compose/issues/4181) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Cannot+connect+to+the+Docker+daemon%22+daemon.json) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=cannot+connect+to+the+docker+daemon&restrict_sr=1)

### 1.2 docker.sock permission denied, and rootless mode

> **Seen as:** `permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`; in rootless mode `No subuid ranges found for user "ops"`, `cannot expose privileged port 80`, or on Docker 29.0.x `failed to bind host port 10.0.2.100:3000/tcp: address already in use` for every port · **Where:** new users and service accounts (deploy, gitlab-runner with the shell executor), after `sudo docker login`, and teams moving away from the docker group · **Level:** [L1 · Junior] · **How common:** one of the most-asked Docker questions on Stack Overflow; "running containers as non-root" and "networking fails with rootless Docker after update" are both in this year's forums.docker.com top list

**Why it happens:** the socket is owned by root:docker with mode 660, so only root and members of the docker group may use it, and a new group membership only applies to new login sessions. A `sudo docker login` leaves ~/.docker owned by root, which breaks the next non-sudo command in a different way. The bigger point is security: the docker group is root on the host, because any member can run `docker run -v /:/host` and edit /etc/shadow. Rootless mode avoids that by running dockerd as an ordinary user inside a user namespace, but it needs subordinate UID and GID ranges, an AppArmor profile for rootlesskit on Ubuntu 24.04 (which restricts unprivileged user namespaces), a systemd user session with lingering, and it cannot bind ports below 1024 by default. On Docker 29.0.x, rootless setups using slirp4netns hit "address already in use" on every published port after a change in port handling; switching the network driver to pasta or disabling the userland proxy fixed it for most people. Since 29.5.0 the default rootless network driver is gvisor-tap-vsock and slirp4netns is no longer installed by Docker's packages, so check which driver a host really uses before applying old advice.

**Diagnose:**

```bash
ls -l /var/run/docker.sock
id ops; getent group docker
ls -ld /home/ops/.docker
# Rootless only
grep '^ops:' /etc/subuid /etc/subgid
systemctl --user status docker --no-pager | head -3
```

```text
srw-rw---- 1 root docker 0 Oct  3 08:55 /var/run/docker.sock
uid=1001(ops) gid=1001(ops) groups=1001(ops),27(sudo)
docker:x:988:deploy
drwx------ 3 root root 4096 Sep 30 14:12 /home/ops/.docker
```

**What the output tells you:** ops is not in the docker group (only deploy is), and ~/.docker belongs to root after a `sudo docker login`, so even after joining the group ops could not read its own credentials. In rootless mode an empty grep on /etc/subuid explains the "No subuid ranges" error, and `systemctl --user` failing with "Failed to connect to bus" means you switched users with sudo instead of logging in.

**Fix:**

```bash
# Option A: docker group. Grant it like sudo, because it is root-equivalent
sudo usermod -aG docker ops            # then log out and back in
sudo chown -R ops:ops /home/ops/.docker
# Option B: rootless Docker for a user who must not be root (CI build hosts, dev boxes)
sudo apt install docker-ce-rootless-extras uidmap
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 ops
sudo loginctl enable-linger ops
# then, as ops in a real SSH login (not sudo su):
dockerd-rootless-setuptool.sh install
# Docker 29.0.x rootless: every published port "already in use" -> use pasta
mkdir -p ~/.config/systemd/user/docker.service.d
printf '[Service]\nEnvironment="DOCKERD_ROOTLESS_ROOTLESSKIT_NET=pasta"\nEnvironment="DOCKERD_ROOTLESS_ROOTLESSKIT_PORT_DRIVER=implicit"\n' \
  > ~/.config/systemd/user/docker.service.d/override.conf
systemctl --user daemon-reload && systemctl --user restart docker
```

**Why this fix works:** group membership is read at login, which is why the re-login matters, and fixing ~/.docker ownership lets the CLI read config.json again. Rootless mode maps the container's root to an unprivileged UID range on the host, so an escape lands in an ordinary account. Do not `chmod 666 /var/run/docker.sock`: that gives every local user and every compromised process root. Know the limits: Dokploy and Swarm need rootful Docker, rootless networking is slower, and ports below 1024 need `net.ipv4.ip_unprivileged_port_start` or a proxy in front.

**Prevent it:** treat the docker group as a privileged group (review `getent group docker` monthly, alert on changes with Wazuh, see [Wazuh & security tools](48-wazuh-and-security-tools.md)), give Traefik and Portainer a read-only socket proxy instead of the raw socket (see [Traefik deep dive](43-traefik-and-reverse-proxies.md), §2.4), and pin Docker versions on rootless hosts.

**Next step:** [Security](30-learn-docker.md) (§13) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), entry 6.4 (runner hosts are root) · KodeKloud: *Docker Certified Associate* — Docker Engine – Security · [Docker docs: rootless mode troubleshooting](https://docs.docker.com/engine/security/rootless/troubleshoot/) · [Linux post-install steps](https://docs.docker.com/engine/install/linux-postinstall/)

**Community threads:** [Docker forums: networking fails with rootless Docker after update](https://forums.docker.com/t/after-update-networking-fails-with-rootless-docker/150458) · [Docker forums: running containers as non-root user](https://forums.docker.com/t/running-docker-containers-as-non-root-user/151333) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22permission+denied+while+trying+to+connect+to+the+Docker+daemon+socket%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=rootless+docker+port&restrict_sr=1)

### 1.3 Docker 29: client version is too old

> **Seen as:** `Error response from daemon: client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version`; Portainer shows `Failed loading environment`; every Traefik route returns 404 while the apps keep running · **Where:** `apt upgrade` to docker-ce 29.x (released 2025-11-10) on hosts running Traefik older than v3.6.1 (dokploy-traefik), Portainer older than 2.33.5 LTS or 2.36.0 STS, or other tools that talk to the socket (Watchtower, cAdvisor, old Dokploy) · **Level:** [L1 · Junior] · **How common:** the second most-viewed forums.docker.com topic of the past year (about 41,000 views); Portainer #12925 is the most-reacted Portainer issue ever (439)

**Why it happens:** Engine 29.0 to 29.2 accept only API version 1.44 (Docker 25) or newer; 29.3.0 lowered the floor again to 1.40 (Docker 19.03), which rescued clients at 1.40 or 1.41 but not those pinned to 1.24, such as old Traefik builds. Check yours with the `docker version` line below. Tools that embed an old Docker Go client and pin an old API version are refused. Your containers keep running because the data plane is untouched, but anything that reads the Docker API stops working: Traefik loses its provider and drops every route, Portainer cannot load the environment, monitoring loses container metrics. It hits hosts where Docker packages are not pinned and an unattended or routine upgrade pulled 29 in.

**Diagnose:**

```bash
docker version --format 'server {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'
docker logs --since 1h dokploy-traefik 2>&1 | grep -i 'too old' | tail -1
zgrep -h 'docker-ce' /var/log/apt/history.log* | tail -2
apt-mark showhold
```

```text
server 29.1.3 api 1.52 min 1.44
2026-10-03T07:12:40Z ERR Provider error, retrying in 2.1s error="Error response from daemon: client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version" providerName=docker
Upgrade: docker-ce:amd64 (5:28.5.2-1~ubuntu.24.04~noble, 5:29.1.3-1~ubuntu.24.04~noble), docker-ce-cli:amd64 (5:28.5.2-1~ubuntu.24.04~noble, 5:29.1.3-1~ubuntu.24.04~noble)
```

**What the output tells you:** the daemon is 29.x with a minimum API of 1.44, Traefik asks for 1.24, and apt history shows last night's jump from 28.5.2. `apt-mark showhold` printed nothing, so nothing was pinned. The fault is the client's age, not the network or the labels.

**Fix:**

```bash
# 1. Real fix: upgrade every socket client (Traefik >= v3.6.1, Portainer >= 2.33.5 LTS / 2.36.0 STS;
#    on Dokploy use its own Traefik update path, see module 45)
# 2. Bridge while you upgrade: let Engine 29 accept older clients again
sudo nano /etc/docker/daemon.json          # add  "min-api-version": "1.24"
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker version --format 'min {{.Server.MinAPIVersion}}'
# 3. Last resort: go back to 28.x and hold the packages
sudo apt install --allow-downgrades docker-ce=5:28.5.2-1~ubuntu.24.04~noble docker-ce-cli=5:28.5.2-1~ubuntu.24.04~noble
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

**Why this fix works:** upgrading the clients removes the mismatch for good. The `min-api-version` setting lowers the floor the daemon enforces, so old clients work again while you schedule upgrades; remove it afterwards, because it exists only for compatibility. A daemon restart restarts containers unless `"live-restore": true` is set, so do it in a window. Don't downgrade as the default answer: you lose security fixes, and on hosts already using the containerd image store a downgrade can leave images invisible.

**Prevent it:** hold docker-ce, docker-ce-cli and containerd.io, upgrade on a staging VM first, read the Engine release notes for "deprecated" and "minimum API", and keep a synthetic check through Traefik (Uptime Kuma or blackbox) so a routing loss pages you within a minute.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 7.2 · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 6.5 · [Observability problems](49-observability-stack-problems.md), entry 5.5 (cAdvisor after Docker 29) · KodeKloud: *Docker Certified Associate* — Docker Engine · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: Docker 29 increased minimum API version, breaks Traefik](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384) · [portainer/portainer #12925: Failed Loading Environment](https://github.com/portainer/portainer/issues/12925) · [portainer/portainer #12934: Portainer and Docker 29](https://github.com/portainer/portainer/issues/12934) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22client+version+1.24+is+too+old%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+29+client+version+too+old+traefik&restrict_sr=1)

### 1.4 Proxmox LXC: ip_unprivileged_port_start denied

> **Seen as:** `unable to start container process: error during container init: open sysctl net.ipv4.ip_unprivileged_port_start file: reopen fd 8: permission denied: unknown` for every `docker run` · **Where:** Docker inside an unprivileged Proxmox LXC container (Debian 11 to 13, Ubuntu), after the November 2025 updates (docker-ce 28.4 or later together with containerd.io 1.7.28-2 or later) · **Level:** [L2 · Mid-level] · **How common:** in the top ten forums.docker.com topics of the past year (about 7,300 views); the same pattern runs through Proxmox and homelab communities

**Why it happens:** Docker in an LXC is a container inside a container: runc starts your container, but it does so inside an LXC whose AppArmor profile the Proxmox host controls. In November 2025 runc shipped fixes for three container-escape vulnerabilities, and the new way it writes sysctls during container start is denied by that outer profile. Nothing is wrong inside your Debian; the nesting is. Users reported docker-ce 5:28.3.3 with containerd.io 1.7.28-1 as the last working pair.

**Diagnose:**

```bash
# On the Proxmox host
pct config 120 | grep -E 'unprivileged|features|apparmor'
sudo journalctl -k --since '10 min ago' | grep 'apparmor="DENIED"' | grep ip_unprivileged | tail -1
# Inside CT 120
apt list --installed 2>/dev/null | grep -E '^(docker-ce|containerd.io)/'
```

```text
features: keyctl=1,nesting=1
unprivileged: 1
audit: type=1400 apparmor="DENIED" operation="open" class="file" name="/proc/sys/net/ipv4/ip_unprivileged_port_start" comm="runc:[2:INIT]" requested_mask="w" denied_mask="w"
containerd.io/now 1.7.28-2 amd64 [installed,local]
docker-ce/now 5:28.5.2-1~debian.12~bookworm amd64 [installed,local]
```

**What the output tells you:** the CT is unprivileged with nesting, the host's kernel log shows AppArmor denying runc's write to the sysctl, and the CT carries the affected package pair. That is this problem exactly; a disk or daemon.json error would show up in `journalctl -u docker` inside the CT instead.

**Fix:**

```bash
# Best: move the workload to a VM (own kernel, no outer AppArmor profile)
qm clone 9000 130 --name docker-1 --full        # from your Ubuntu cloud-init template
# Short term inside the CT: pin the last working pair and hold it
sudo apt install --allow-downgrades docker-ce=5:28.3.3-1~debian.12~bookworm \
  docker-ce-cli=5:28.3.3-1~debian.12~bookworm containerd.io=1.7.28-1
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
# Reported workaround that weakens isolation (trusted workloads only), on the host in /etc/pve/lxc/120.conf:
#   lxc.apparmor.profile: unconfined
#   lxc.mount.entry: /dev/null sys/module/apparmor/parameters/enabled none bind 0 0
```

**Why this fix works:** a VM gives Docker its own kernel and its own AppArmor, which is the configuration upstream supports. Pinning restores the pre-fix behaviour but also keeps the container-escape holes the update closed, so treat it as days, not months. Unconfining the LXC removes the outer protection entirely; on a shared Proxmox host that is a real downgrade in isolation.

**Prevent it:** run Docker hosts as VMs from a template, stage package upgrades on one CT or VM before the rest, and keep a list of which hosts are LXC so an advisory like this takes minutes to scope.

**Next step:** [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) · KodeKloud has no Proxmox course; use the [Proxmox VE documentation](https://pve.proxmox.com/pve-docs/) (Linux Container and Qemu/KVM chapters)

**Community threads:** [Docker forums: Docker fails to run on Debian (bullseye) after update](https://forums.docker.com/t/docker-fails-to-run-on-debian-bullseye-after-update-unable-to-start-container-process-error-during-container-init-open-sysctl-net-ipv4-ip-unprivileged-port-start-file-reopen-fd-8-permission-denied-unknown/150363) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+lxc+%22ip_unprivileged_port_start%22) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=docker+lxc+ip_unprivileged_port_start&restrict_sr=1)

### 1.5 Containers don't come back after a reboot

> **Seen as:** after a reboot `docker ps` is empty or short, the container shows `Exited (255)` or `Exited (128)`, or a container started with `--restart unless-stopped` stays down · **Where:** single-host Compose apps, NAS and homelab boxes, containers whose bind mounts live on NFS or iSCSI, containers bound to an IP that comes up late · **Level:** [L1 · Junior] · **How common:** in this year's forums.docker.com top list ("container with --restart unless-stopped is not restarted automatically upon system reboot"), and a classic on Stack Overflow

**Why it happens:** Docker only restarts what it has a policy for, and only once dockerd itself is up. The usual gaps: docker.service is not enabled (only docker.socket is, so the daemon starts on the first CLI call, not at boot); the container has no restart policy (`docker run` defaults to `no`, Compose too unless you set `restart:`); the container was stopped by hand before the reboot, which `unless-stopped` remembers; or dockerd started before the NFS mount or the extra IP existed, the container failed once and Docker gave up.

**Diagnose:**

```bash
systemctl is-enabled docker docker.socket
docker ps -a --format '{{.Names}}\t{{.Status}}' | head
docker inspect -f '{{.Name}} {{.HostConfig.RestartPolicy.Name}} exit={{.State.ExitCode}} {{.State.Error}}' app-files web
sudo journalctl -b -u docker --no-pager | grep -iE 'error|failed' | tail -3
```

```text
disabled
enabled
app-files	Exited (128) 6 minutes ago
web	Exited (0) 2 days ago
/app-files unless-stopped exit=128 invalid mount config for type "bind": bind source path does not exist: /mnt/nas/app
/web no exit=0
```

**What the output tells you:** three separate gaps. docker.service is disabled, so dockerd started late through the socket. app-files has the right policy but its NFS source did not exist when Docker tried, so it failed and stayed down. web has no restart policy at all, so it was never going to come back.

**Fix:**

```bash
sudo systemctl enable docker
docker update --restart unless-stopped web           # or restart: unless-stopped in compose.yaml
# Make dockerd wait for the mounts its containers need
sudo systemctl edit docker
#   [Unit]
#   RequiresMountsFor=/mnt/nas
#   After=remote-fs.target
docker start app-files
```

**Why this fix works:** an enabled unit starts dockerd at boot, and dockerd then starts every container whose policy asks for it. `RequiresMountsFor=` orders dockerd after the mount and pulls the mount in, so bind sources exist when containers start. Avoid `restart: always` on things you stop on purpose for maintenance; `unless-stopped` respects your manual stop. Swarm services are different: the orchestrator reschedules tasks regardless of policies, which is one reason Dokploy uses Swarm.

**Prevent it:** reboot every new host once before calling it done, keep restart policies in the Compose file rather than in someone's shell history, and have an external uptime check that notices a service missing after patch night.

**Next step:** [Resources and restart policies](30-learn-docker.md) (§10) · [Containers playbook](26-playbook-containers-k8s.md) (§2) · KodeKloud: *Docker Certified Associate* — Docker Engine → [Restart Policies](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page) · [docker run reference](https://docs.docker.com/reference/cli/docker/container/run/)

**Community threads:** [Docker forums: unless-stopped container not restarted after reboot](https://forums.docker.com/t/nginx-container-with-restart-unless-stopped-is-not-restarted-automatically-upon-system-reboot/150569) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+restart+unless-stopped+not+starting+after+reboot) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=containers+not+starting+after+reboot+nfs&restrict_sr=1)

### 1.6 Container exits 137, 139 or 143

> **Seen as:** `Exited (137)` with `OOMKilled: true`, `Exited (137)` after exactly 10 seconds of `docker stop`, `Exited (139)` or `Illegal instruction (core dumped)`, MongoDB's `WARNING: MongoDB 5.0+ requires a CPU with AVX support` · **Where:** memory-limited containers, apps that ignore SIGTERM, MongoDB and other images built for newer CPUs running on VMs with a generic CPU type · **Level:** [L1 · Junior] · **How common:** "Docker compose mongo exit code 139" is in this year's forums.docker.com top list; exit 137 is one of the most-searched container errors on Stack Overflow

**Why it happens:** an exit code above 128 means "killed by signal (code − 128)". 137 is SIGKILL: either the kernel OOM killer (the container hit its memory limit, or the host ran out) or Docker's own SIGKILL after the stop timeout (10 seconds) because the process ignored SIGTERM. That last one is often a shell-form `CMD`, which makes `/bin/sh -c` PID 1, and sh does not forward signals. 143 is SIGTERM: the process ended on the signal within the grace period, which is a normal stop (an app that catches SIGTERM and exits cleanly usually reports 0 instead). 139 is SIGSEGV; on VMs the surprising cause is a CPU feature the binary needs (AVX for MongoDB 5+, many ML images) that the virtual CPU does not expose.

**Diagnose:**

```bash
docker inspect -f 'oom={{.State.OOMKilled}} exit={{.State.ExitCode}} mem={{.HostConfig.Memory}}' mongo
sudo journalctl -k --since '1 hour ago' | grep -iE 'oom-kill|killed process' | tail -2
docker logs --tail 5 mongo
grep -o -m1 -w avx /proc/cpuinfo || echo "no avx"
docker inspect -f '{{json .Config.Cmd}} {{json .Config.Entrypoint}}' app
```

```text
oom=false exit=139 mem=0
WARNING: MongoDB 5.0+ requires a CPU with AVX support, and your current system does not appear to have that!
no avx
["/bin/sh","-c","node server.js"] null
```

**What the output tells you:** mongo was not OOM-killed; it crashed with SIGSEGV on a CPU without AVX, which its own log says. The app container runs its command through `/bin/sh -c`, so on `docker stop` node never sees SIGTERM and gets SIGKILLed after 10 seconds, which looks like 137 but is not memory.

**Fix:**

```bash
# 137 with oom=true: raise the limit or fix the leak, and set limits on purpose
#   deploy: { resources: { limits: { memory: 1g } } }   in compose.yaml
# 137 after 10 s on stop: exec-form CMD, an init, and a realistic grace period
#   CMD ["node", "server.js"]        (Dockerfile)
#   init: true  and  stop_grace_period: 30s   (compose.yaml)
```

<div class="env" data-env="onprem" markdown="1">

On Proxmox the default virtual CPU (kvm64 or x86-64-v2-AES) hides AVX. Give the VM a CPU type that exposes it, then stop and start the VM (a reboot inside the guest is not enough):

```bash
qm set 130 --cpu x86-64-v3      # or --cpu host when all cluster nodes have the same CPU generation
qm shutdown 130 && qm start 130
```

</div>

<div class="env" data-env="cloud" markdown="1">

Current EC2 instance families all expose AVX, so 139 in the cloud is usually a genuine bug or a wrong-architecture image (entry 6.1). Exit 137 is more common: small instances have no swap by default, so memory pressure turns into OOM kills quickly. Right-size the instance or set container memory limits so one container cannot take the whole host.

</div>

**Why this fix works:** a memory limit turns "the host is out of memory and kills something random" into "this container is killed and restarted", which is easier to see and to alert on. Exec form makes your app PID 1 so it receives SIGTERM, and `init: true` adds a tiny init that forwards signals and reaps zombies. Exposing AVX gives the binary the instructions it was compiled for. Don't hide OOM kills by removing limits or adding `--oom-kill-disable`; the host then pays.

**Prevent it:** alert on container restarts and OOM kills (cAdvisor or the kernel log via Loki, see [Observability problems](49-observability-stack-problems.md)), review Dockerfiles for shell-form `CMD`, and standardise the VM CPU type in your Proxmox templates.

**Next step:** [Resources and restart policies](30-learn-docker.md) (§10) · [Container lifecycle](30-learn-docker.md) (§5) · [Containers playbook](26-playbook-containers-k8s.md) (§2) · KodeKloud: *Docker Certified Associate* — Docker Engine – Security (cgroups and resource limits) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: Docker compose mongo exit code 139](https://forums.docker.com/t/docker-compose-mongo-exit-code-139/151353) · Search: [Stack Overflow: exit 137](https://stackoverflow.com/search?q=docker+%22exited+%28137%29%22+OOMKilled) · [Stack Overflow: mongo AVX](https://stackoverflow.com/search?q=mongodb+docker+%22AVX+support%22) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=mongodb+avx+cpu+type&restrict_sr=1)

---

## 2. Disk, logs and volumes

Docker's storage grows quietly: every deploy adds an image, every build adds cache, every chatty container adds log lines, and nothing is removed unless you ask. These entries cover the full disk, the logs that cause it, and the volumes that hold your data.

### 2.1 No space left on device

> **Seen as:** `no space left on device` on pull, build or write; `failed to register layer: ... no space left on device`; Dokploy builds failing; the root filesystem at 100% with /var/lib/docker as the biggest directory · **Where:** build hosts, GitLab runners and Dokploy servers that build locally, especially Ubuntu installs whose root logical volume uses only half the disk · **Level:** [L1 · Junior] · **How common:** among the most-viewed forums.docker.com topics of all time ("How to delete cache?" about 1.39 million views, cleaning /var/lib/docker/overlay about 974,000, the none images question about 734,000), plus "Huge disk usage" in this year's top list; disk is the first item in Dokploy's troubleshooting docs

**Why it happens:** four things accumulate. Old images from every deploy (each Dokploy or CI build leaves the previous one behind), BuildKit's build cache (unbounded unless garbage collection is configured), container logs in json-file format (no rotation by default, entry 2.2) and data written into the container layer instead of a volume. Prune commands skip named volumes on purpose, and on Docker 29 fresh installs use the containerd image store, which keeps image content under /var/lib/containerd rather than /var/lib/docker. On top of that, Ubuntu's installer gives the root LV only part of the volume group, so many servers run out at 30 to 60 GB while free space sits unused.

**Diagnose:**

```bash
df -h /
docker system df
sudo du -xsh /var/lib/docker/* /var/lib/containerd 2>/dev/null | sort -h | tail -4
sudo find /var/lib/docker/containers -name '*-json.log' -size +1G -exec ls -lh {} \;
sudo vgs
```

```text
Filesystem                         Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv   62G   62G     0 100% /
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          87        9         24.9GB    21.7GB (87%)
Containers      14        9         1.1GB     310MB (28%)
Local Volumes   22        8         6.8GB     1.2GB (17%)
Build Cache     412       0         14.2GB    14.2GB
4.1G	/var/lib/docker/containers
6.8G	/var/lib/docker/volumes
40G	/var/lib/docker/overlay2
-rw-r----- 1 root root 3.9G Oct  3 09:30 /var/lib/docker/containers/4f1c2a.../4f1c2a...-json.log
  VG        #PV #LV #SN Attr   VSize    VFree
  ubuntu-vg   1   1   0 wz--n- <125.00g  63.00g
```

**What the output tells you:** 36 GB is reclaimable without touching volumes (old images plus all of the build cache), one container log is 3.9 GB, and the volume group has 63 GB that the root LV never used. Volumes (6.8 GB) are not the problem, so nothing below needs `--volumes`.

**Fix:**

```bash
# Free space now, keeping anything recent
docker builder prune -f --filter until=72h
docker image prune -a -f --filter until=168h
docker container prune -f
sudo truncate -s 0 /var/lib/docker/containers/4f1c2a*/4f1c2a*-json.log   # emergency only, then entry 2.2
# Use the disk you already have
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
# Keep the build cache bounded (daemon.json), then validate and restart in a window
#   "builder": { "gc": { "enabled": true, "defaultKeepStorage": "20GB" } }
```

Moving Docker to a bigger disk instead:

```bash
sudo systemctl stop docker docker.socket
sudo rsync -aHAX --info=progress2 /var/lib/docker/ /srv/docker/
# daemon.json: "data-root": "/srv/docker"
# containerd image store (Docker 29 fresh installs): also move containerd's "root" in /etc/containerd/config.toml
sudo systemctl start docker && docker info --format '{{.DockerRootDir}}'
```

**Why this fix works:** the `until` filters keep what you deployed in the last days, so a rollback still has its image locally. `lvextend -r` grows the LV and the filesystem online. Build cache GC stops the cache from growing past the limit again. What not to do: `docker system prune -a --volumes` on a host with stopped stacks deletes their databases, and deleting directories under overlay2 by hand corrupts the image store in ways only a reinstall fixes.

**Prevent it:** a disk alert at 80% (node_exporter), a weekly pruning timer with the same filters, builder GC in daemon.json from day one, log limits (entry 2.2), and Harbor retention for the registry side (entry 9.2).

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 11.1 · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), entry 8.1 (runner disk full) · [Images, layers and overlay2](30-learn-docker.md) (§3) · [Docker command reference](14-docker-containers.md) (§6) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Engine & Storage · [Docker docs: prune unused objects](https://docs.docker.com/engine/manage-resources/pruning/)

**Community threads:** [forums.docker.com all-time top topics](https://forums.docker.com/top?period=all) · [Docker forums: Huge disk usage](https://forums.docker.com/t/huge-disk-usage/151053) · [Docker forums: which container makes overlay2 grow](https://forums.docker.com/t/how-can-i-find-out-which-container-is-causing-my-overlay2-folder-to-grow-and-crash-my-vm/150374) · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+overlay2+%22no+space+left+on+device%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+overlay2+disk+full&restrict_sr=1)

### 2.2 Logs never rotate, or docker logs is empty

> **Seen as:** a single `*-json.log` of tens of gigabytes, `docker logs` taking minutes to print, or the opposite: `docker logs` shows nothing while the app clearly runs; with some remote drivers `configured logging driver does not support reading` · **Where:** chatty apps on long-running hosts, hosts where log limits were added to daemon.json after the containers were created, images that log to files · **Level:** [L1 · Junior] · **How common:** docker/compose #1083 ("ability to clear log history", 158 reactions) and part of nearly every disk-full thread

**Why it happens:** the default json-file driver never rotates. Limits in daemon.json are copied into a container's config when it is created, so changing daemon.json does nothing for existing containers until they are recreated. The `local` driver rotates and compresses by default and is still readable with `docker logs`. An empty `docker logs` means the app is not writing to stdout or stderr: it logs to a file inside the container (which then grows the container layer), Python buffers stdout when there is no TTY, or dual logging was disabled for a remote driver.

**Diagnose:**

```bash
sudo sh -c 'du -h /var/lib/docker/containers/*/*-json.log' | sort -h | tail -2
docker info --format '{{.LoggingDriver}}'
docker inspect -f '{{.Name}} {{.HostConfig.LogConfig.Type}} {{json .HostConfig.LogConfig.Config}}' worker api traefik
docker exec api ls -l /proc/1/fd/1 /var/log/app/
```

```text
1.2G	/var/lib/docker/containers/9a0e71.../9a0e71...-json.log
38G	/var/lib/docker/containers/4f1c2a.../4f1c2a...-json.log
json-file
/worker json-file {}
/api json-file {}
/traefik json-file {"max-file":"3","max-size":"10m"}
lrwx------ 1 root root 64 Oct  3 09:41 /proc/1/fd/1 -> pipe:[48211]
-rw-r--r-- 1 app app 812M Oct  3 09:41 app.log
```

**What the output tells you:** the daemon default has no limits, so worker and api grow forever; only traefik got limits from its own Compose file. The api container writes to /var/log/app/app.log inside the container, which is why `docker logs api` is empty and why its container layer keeps growing.

**Fix:**

```bash
# /etc/docker/daemon.json (applies to containers created after the restart)
#   "log-driver": "local",
#   "log-opts": { "max-size": "10m", "max-file": "5" }
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
docker compose up -d --force-recreate        # existing containers keep their old log config until recreated
# Space now, without a restart: truncate, never rm (dockerd keeps the file open)
sudo truncate -s 0 /var/lib/docker/containers/4f1c2a*/4f1c2a*-json.log
# App side: log to stdout/stderr
#   RUN ln -sf /dev/stdout /var/log/app/app.log     (Dockerfile)
#   ENV PYTHONUNBUFFERED=1                          (Python)
```

**Why this fix works:** a rotating driver caps every new container at size times files. Recreating applies the new defaults to existing workloads. `rm` on an open log file frees nothing until dockerd restarts (`lsof +L1` shows such deleted-but-open files), which is why truncate is the emergency tool. Don't switch to the `none` driver to save disk; the next incident will have no evidence.

**Prevent it:** ship daemon.json with log limits before the first container on every host, and send logs to a central store so local files can stay small (Alloy to Loki, see [Observability problems](49-observability-stack-problems.md), entries 9.1 and 9.2, including why the Loki Docker driver can freeze containers).

**Next step:** [Logging](30-learn-docker.md) (§6) · [Logs & journal reference](06-logs-journal.md) · KodeKloud: *Docker Certified Associate* — Docker Engine → [Logging Driver](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page) · [Docker docs: configure logging drivers](https://docs.docker.com/engine/logging/configure/)

**Community threads:** [docker/compose #1083: ability to clear log history](https://github.com/docker/compose/issues/1083) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+json-file+log+max-size+existing+containers) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=container+log+file+huge+rotation&restrict_sr=1)

### 2.3 Volumes: data gone, space kept, root-owned files

> **Seen as:** a database empty after `docker compose down -v`; `docker volume prune` reports `Total reclaimed space: 0B` while volumes pile up; `permission denied` or `EACCES` when an image running as a non-root user writes to a volume or bind mount · **Where:** Compose projects with databases, renamed projects, images that run as UID 472, 999, 1000 or 65534 · **Level:** [L1 · Junior] · **How common:** moby #2259 ("mount volume as user other than root") has 254 reactions, docker/compose #3270 covers named volumes owned by root, and "volume space after container deletion" is in this year's forums top list

**Why it happens:** `down -v` means "and delete the named volumes of this project", so it is a data-deletion command. Since Engine 23, `docker volume prune` removes only anonymous volumes; unused named volumes need `--all`. Removing a container never removes its volumes, so a renamed project (its name comes from the directory) leaves the old project's volumes behind. Ownership: a new named volume copies ownership from the image path on first use, but a bind mount keeps whatever the host directory has, usually root, and an image that runs as UID 472 cannot write there.

**Diagnose:**

```bash
docker system df -v | sed -n '/Local Volumes space usage/,/Build cache usage/p' | head -6
docker volume ls -f dangling=true -q | wc -l
docker inspect -f '{{.Config.User}}' grafana/grafana:12.2.0
docker run --rm -v /srv/grafana:/v alpine ls -lnd /v
```

```text
Local Volumes space usage:

VOLUME NAME        LINKS     SIZE
shop_pgdata        1         5.9GB
old-shop_pgdata    0         2.3GB
3f9c0d1e7b2a...    0         412MB
37
472
drwxr-xr-x 2 0 0 4096 Oct  3 10:02 /v
```

**What the output tells you:** old-shop_pgdata belongs to the project before it was renamed and has no container (0 links); it is named, so a plain prune skips it. There are 37 anonymous volumes, typically from images that declare VOLUME and were run without naming it. The bind-mounted directory is owned by UID 0 while Grafana runs as 472, which is the whole permission error.

**Fix:**

```bash
# Before anything destructive on a stateful project, copy the data (databases: use a dump, see module 51)
docker run --rm -v shop_pgdata:/v:ro -v /srv/backup:/b alpine tar czf /b/shop_pgdata-$(date +%F).tgz -C /v .
docker compose down                     # never -v on a stateful project
docker volume prune -f                  # anonymous, unused volumes only
docker volume rm old-shop_pgdata        # named volumes: one by one, after checking
# Permissions: give the directory to the image's UID (or run the image as yours with user: "1000:1000")
sudo chown -R 472:472 /srv/grafana
```

**Why this fix works:** removing volumes by name forces you to look at each one. `chown` to the image's UID matches what the process inside expects, without widening access for everyone. Never `chmod -R 777` a data directory, and be very careful with `docker volume prune --all`: it deletes every unused named volume, including the database of a stack you stopped for maintenance.

**Prevent it:** set `name:` at the top of every compose.yaml so the project name does not depend on the directory, name every volume, keep `down -v` out of runbooks, and back up volumes as described in [Databases, storage & backups](51-problems-databases-storage-backup.md).

**Next step:** [Storage](30-learn-docker.md) (§8) · [Containers playbook](26-playbook-containers-k8s.md) (§5) · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Volumes and Bind Mounts) · [Docker docs](https://docs.docker.com/)

**Community threads:** [moby/moby #2259: mount volume as a user other than root](https://github.com/moby/moby/issues/2259) · [docker/compose #3270: named volumes mounted as root](https://github.com/docker/compose/issues/3270) · [Docker forums: volume space after container deletion](https://forums.docker.com/t/docker-volume-space-after-container-deletion/150050) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+volume+permission+denied+non-root+user) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=compose+down+-v+lost+data&restrict_sr=1)

---

## 3. Compose v2

Compose is where most engineers meet Docker, and where Dokploy's "compose" deployments live. The problems are rarely bugs: they are the gap between what people expect Compose to do and what it actually does.

### 3.1 docker-compose vs docker compose

> **Seen as:** `docker-compose: command not found`, `docker: unknown command: docker compose`, older CLIs printing `unknown shorthand flag: 'd' in -d`, or `the attribute "version" is obsolete, it will be ignored` · **Where:** tutorials written for Compose v1, servers with Ubuntu's docker.io package mixed with Docker's packages, scripts that grep for container names · **Level:** [L0 · Fresher] · **How common:** a fresher classic on Stack Overflow; "Docker will not start after installing docker compose" is in this year's forums.docker.com top list

**Why it happens:** Compose v1 was a Python program called `docker-compose` and is end of life. Compose v2 is a Docker CLI plugin, run as `docker compose`, shipped in the docker-compose-plugin package from Docker's apt repository. Without the plugin, `docker` does not know the `compose` subcommand. Mixing Ubuntu's docker.io, containerd and docker-compose packages with Docker's docker-ce packages leaves two sources fighting over the same files. The top-level `version:` key belonged to the old file formats; v2 ignores it. v2 also names containers `project-service-1` (hyphens) where v1 used underscores, which breaks scripts that grep names.

**Diagnose:**

```bash
docker compose version
which -a docker-compose && docker-compose version 2>/dev/null | head -1
apt list --installed 2>/dev/null | grep -E '^(docker|containerd|runc)'
ls /usr/libexec/docker/cli-plugins/
```

```text
docker: unknown command: docker compose

Run 'docker --help' for more information
/usr/bin/docker-compose
docker-compose version 1.29.2, build unknown
containerd/noble-updates,now 1.7.28-0ubuntu1~24.04.1 amd64 [installed,automatic]
docker.io/noble-updates,now 27.5.1-0ubuntu3~24.04.2 amd64 [installed]
runc/noble-updates,now 1.3.3-0ubuntu1~24.04.2 amd64 [installed,automatic]
ls: cannot access '/usr/libexec/docker/cli-plugins/': No such file or directory
```

**What the output tells you:** this host runs Ubuntu's docker.io package with the end-of-life Python docker-compose 1.29.2 and no CLI plugins at all. Following a modern guide on it will keep failing in small ways until there is one package source.

**Fix:**

```bash
# Pick one source. Docker's apt repository is what Dokploy and most current guides expect.
docker ps -q | xargs -r docker stop          # images and volumes in /var/lib/docker are kept
sudo apt remove docker-compose docker.io containerd runc
# add Docker's apt repository as in the official install guide, then:
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker compose version
# compose.yaml: delete the top-level "version:" line
```

**Why this fix works:** one source means one set of binaries, one containerd and a matching compose plugin, so behaviour matches the documentation. Compose v2 understands the current Compose Specification (profiles, depends_on conditions, include, watch) and builds with BuildKit. Don't install the old Python docker-compose with pip to make an old tutorial work; translate the tutorial instead.

**Prevent it:** install Docker with Ansible from one repository on every host, replace `docker-compose` in runbooks and scripts, and run `docker compose config -q` in CI so files are validated by the same version that deploys them.

**Next step:** [Docker Compose](30-learn-docker.md) (§9) · [Docker command reference](14-docker-containers.md) (§8) · KodeKloud: *Docker Training Course for the Absolute Beginner* — [Docker Compose](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: Docker will not start after installing docker compose](https://forums.docker.com/t/docker-will-not-start-after-installing-docker-compose-n-w-out-the/151374) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22docker-compose%22+vs+%22docker+compose%22+v2) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=docker-compose+command+not+found+v2&restrict_sr=1)

### 3.2 Variables: .env, env_file, $$ and secrets

> **Seen as:** `WARN[0000] The "Xk9" variable is not set. Defaulting to a blank string.`, a password containing `$` that arrives truncated, a variable set in .env that the app never sees, or an npm token visible in `docker history` · **Where:** Compose projects, Portainer stacks (entry 7.2) and Dokploy environment settings · **Level:** [L1 · Junior] · **How common:** docker/compose #6170 (--env-file), #6358 (build secrets) and #7025 (SSH for BuildKit) each collected 20 to 43 reactions; Portainer #1857 asks for env_file support

**Why it happens:** Compose has three separate mechanisms that look alike. The `.env` file in the project directory (or `--env-file`) only feeds *interpolation*: it fills `${VAR}` in compose.yaml. `env_file:` passes variables *into the container*. `environment:` sets them explicitly. A `$` in compose.yaml starts an interpolation, so `s3cr$Xk9!` becomes `s3cr` plus a warning about a variable called Xk9; a literal dollar needs `$$`, and in .env files single quotes keep a value literal. Build arguments (`ARG`) and `ENV` are stored in the image metadata, so a token passed that way ships to everyone who can pull the image.

**Diagnose:**

```bash
docker compose config 2>&1 | grep -E 'WARN|DB_PASS'
docker compose exec api printenv DB_PASS
docker history --no-trunc harbor.example.com/shop/api:1.4.2 | grep -oE 'NPM_TOKEN=[^ ]+' | head -1
```

```text
WARN[0000] The "Xk9" variable is not set. Defaulting to a blank string.
      DB_PASS: s3cr!
s3cr!
NPM_TOKEN=npm_4fQ2xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**What the output tells you:** the rendered config already shows the truncated password, so the bug is interpolation in compose.yaml, not the app. The image history contains the npm token from a build argument: anyone who can pull the image can read it, so it must be rotated, not just removed.

**Fix:**

```yaml
# compose.yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.3
    env_file: .env.api                # variables for the container (not interpolation)
    environment:
      DB_HOST: db
      DB_PASS_FILE: /run/secrets/db_password
    secrets: [db_password]
secrets:
  db_password:
    file: ./secrets/db_password.txt   # mounted at /run/secrets/db_password, not in docker inspect
```

```bash
# Build-time secret: available to one RUN step, never stored in a layer
#   Dockerfile:  RUN --mount=type=secret,id=npm_token,env=NPM_TOKEN npm ci
docker buildx build --secret id=npm_token,env=NPM_TOKEN -t harbor.example.com/shop/api:1.4.3 .
```

**Why this fix works:** `docker compose config` shows exactly what Compose will send, so you debug the rendered result, not your intention. File-based secrets keep passwords out of `docker inspect` and out of the environment that crash reporters dump. A secret mount exists only during one build step and leaves no trace in history. Rotate any token that ever reached an image pushed to Harbor; deleting the tag does not un-leak it.

**Prevent it:** `docker compose config -q` and a secret scanner in CI, .env files in .gitignore, and a review rule that rejects ARG or ENV for credentials (see [Security & DevSecOps](37-learn-security-devsecops.md), secrets management).

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), entry 13.4 (secrets leak into job logs) · [Docker Compose](30-learn-docker.md) (§9) · KodeKloud: *Docker Certified Associate* — Docker Image Management · [Docker docs](https://docs.docker.com/)

**Community threads:** [docker/compose #6358: build-time secrets](https://github.com/docker/compose/issues/6358) · [docker/compose #6170: --env-file option](https://github.com/docker/compose/issues/6170) · [portainer/portainer #1857: env_file in stacks](https://github.com/portainer/portainer/issues/1857) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22variable+is+not+set.+Defaulting+to+a+blank+string%22+compose) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=compose+env_file+vs+.env&restrict_sr=1)

### 3.3 depends_on doesn't wait for the database

> **Seen as:** `Error: connect ECONNREFUSED 172.18.0.2:5432` or `connection refused` in the first seconds after `docker compose up`; the app exits, restarts and sometimes works on the second try · **Where:** app plus database stacks, first start with an empty volume (initdb takes longer), Swarm stacks · **Level:** [L1 · Junior] · **How common:** docker/compose #374 ("delay container startup to support dependant services") has 316 reactions, one of the most-reacted Compose issues ever

**Why it happens:** the short form of `depends_on` only orders container *start*; the database process inside may need seconds before it accepts connections, and much longer on its first start. Without a healthcheck Compose cannot know when it is ready. In Swarm (`docker stack deploy`, Dokploy) `depends_on` is ignored completely, so apps there must retry anyway.

**Diagnose:**

```bash
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
docker compose logs --no-log-prefix api | head -2
docker inspect -f '{{json .State.Health}}' shop-db-1
```

```text
SERVICE   STATUS
api       Restarting (1) 4 seconds ago
db        Up 9 seconds
Error: connect ECONNREFUSED 172.18.0.2:5432
null
```

**What the output tells you:** the database container is up but the app could not connect, and `null` health means db has no healthcheck at all, so Compose had nothing to wait for.

**Fix:**

```yaml
services:
  db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 30s
  api:
    image: harbor.example.com/shop/api:1.4.3
    depends_on:
      db:
        condition: service_healthy
        restart: true
```

**Why this fix works:** `condition: service_healthy` makes Compose wait until the healthcheck passes before starting api, and `restart: true` restarts api when Compose restarts db. The `$$` stops Compose from interpolating variables that the shell inside the container should expand. `-h 127.0.0.1` matters: on the first start with an empty volume, the official image runs a temporary server on the Unix socket only while it initialises the database, so a socket check can pass before the port the app uses is open. Keep retry-with-backoff in the application as well: databases restart, fail over and get upgraded long after startup, and Swarm never honours `depends_on`.

**Prevent it:** require healthchecks for every stateful service in Compose reviews, and test "database restarts while the app runs" once per app.

**Next step:** [Docker Compose](30-learn-docker.md) (§9) · [Databases, storage & backups](51-problems-databases-storage-backup.md) · entry 8.5 for healthchecks in Swarm updates · KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Compose · [Docker docs](https://docs.docker.com/)

**Community threads:** [docker/compose #374: delay container startup for dependent services](https://github.com/docker/compose/issues/374) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+compose+depends_on+wait+for+postgres+healthcheck) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=depends_on+service_healthy&restrict_sr=1)

### 3.4 My change didn't show up

> **Seen as:** after `git pull` and `docker compose up -d` the old code is still served; an edited Caddyfile, nginx.conf or prometheus.yml has no effect even after `docker compose restart`; `WARN Found orphan containers ([shop-worker-1]) for this project` · **Where:** Compose projects updated in place on a server, Dokploy compose apps, config files bind-mounted one by one · **Level:** [L1 · Junior] · **How common:** docker/compose #1487 ("up doesn't rebuild image although Dockerfile has changed"); "Docker seems to cache Caddyfile" is in this year's forums top list

**Why it happens:** `up` reuses an existing image; it builds only when the image is missing unless you pass `--build`, and it does not re-pull a moving tag such as `latest` unless you pull first. BuildKit's cache tracks file contents, so a stale build usually means the change never reached the build context (.dockerignore) or a `RUN` step fetched something remote that is now cached. Single-file bind mounts are the sneakiest: editors save by writing a new file and renaming it, the host path now points at a new inode, and the container keeps the old one. Finally, the project name comes from the directory, so a copied or renamed directory starts a second project and renamed services leave orphans.

**Diagnose:**

```bash
docker compose config --images
docker inspect -f '{{.Created}}' harbor.example.com/shop/api:latest
git log -1 --format='%h %cd'
stat -c '%i %y' caddy/Caddyfile
docker compose exec caddy stat -c '%i %y' /etc/caddy/Caddyfile
```

```text
harbor.example.com/shop/api:latest
2026-09-28T14:02:11.402Z
a41f9e2 Fri Oct 2 16:40:03 2026 +0200
1319422 2026-10-03 10:12:40.118 +0200
1318977 2026-10-03 09:58:02.554 +0200
```

**What the output tells you:** the image was built five days before the latest commit, so nothing was rebuilt or pulled. The Caddyfile inside the container has a different inode and an older timestamp than the one on disk: the container still holds the file you replaced.

**Fix:**

```bash
docker compose pull && docker compose up -d          # registry images with moving tags
docker compose up -d --build                         # images built from this project
docker compose build --no-cache --pull api           # a RUN step must fetch fresh content
docker compose up -d --force-recreate caddy          # picks up the new inode of a single-file mount
docker compose up -d --remove-orphans
```

```yaml
# Mount the directory, not the file, and pin the project name
name: shop
services:
  caddy:
    volumes:
      - ./caddy:/etc/caddy:ro
```

**Why this fix works:** each command closes one specific gap: pull for moving tags, build for local images, no-cache for remote content, recreate for stale inodes. A directory mount follows the editor's rename, so the next reload sees the new file (Caddy, nginx and Prometheus still need their own reload). Immutable tags per commit, such as `:a41f9e2`, turn "which version runs?" into a question with one answer.

**Prevent it:** build in CI and tag images with the commit SHA (see [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md)), mount config directories, set `name:` in every compose.yaml, and never deploy `latest`.

**Next step:** [Dockerfile mastery](30-learn-docker.md) (§4, build cache) · [Observability problems](49-observability-stack-problems.md), entry 5.2 (the same single-file trap with Prometheus) · KodeKloud: *Docker Certified Associate* — Docker Image Management (Build Cache) · [Docker docs](https://docs.docker.com/)

**Community threads:** [docker/compose #1487: up doesn't rebuild](https://github.com/docker/compose/issues/1487) · [Docker forums: Docker seems to cache Caddyfile](https://forums.docker.com/t/docker-seems-to-cache-caddyfile/150638) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+compose+up+not+using+new+image) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=bind+mount+file+not+updating&restrict_sr=1)

---

## 4. Container networking

Most "Docker is broken" tickets are networking: a container that cannot reach the host, two containers that cannot find each other, a port someone else owns, a port that is open when it should not be, an address range that swallows the VPN, DNS that works on the host but not inside, and packets that are simply too big.

### 4.1 localhost is the container: reaching the host

> **Seen as:** `curl: (52) Empty reply from server` on a published port; `connect ECONNREFUSED 127.0.0.1:5432` from a container to a database on the host; `host.docker.internal: Name or service not known` on Linux · **Where:** apps that bind 127.0.0.1 inside the container (dev servers, Vite, Flask), containers using a database or API installed on the host, guides written for Docker Desktop applied to Ubuntu · **Level:** [L1 · Junior] · **How common:** "Accessing host machine from within docker container" has about 671,000 views on forums.docker.com, "network_mode: host not working" about 424,000, and three host.docker.internal or localhost questions are in this year's top list

**Why it happens:** every container has its own network namespace, so 127.0.0.1 inside a container is the container itself, not the host. An app listening on 127.0.0.1 inside the container cannot be reached through a published port, because Docker forwards to the container's eth0 address; the connection is accepted and dropped, which curl reports as an empty reply. In the other direction, `host.docker.internal` exists automatically only on Docker Desktop; on Linux you add it yourself. Even then the host service must listen on an address the bridge can reach, and UFW's default deny drops traffic arriving from docker0 or a br-xxxx bridge at host ports.

**Diagnose:**

```bash
docker exec web ss -ltn                      # what the app listens on, inside its namespace
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/
sudo ss -ltnp 'sport = :5432'                # the host's database
docker exec api getent hosts host.docker.internal || echo "no host.docker.internal"
sudo journalctl -k --since '10 min ago' | grep 'UFW BLOCK' | grep 'DPT=5432' | tail -1
```

```text
State  Recv-Q Send-Q Local Address:Port Peer Address:Port
LISTEN 0      511        127.0.0.1:3000      0.0.0.0:*
000
LISTEN 0      200        127.0.0.1:5432      0.0.0.0:*    users:(("postgres",pid=911,fd=6))
no host.docker.internal
Oct 03 10:21:07 dokploy-1 kernel: [UFW BLOCK] IN=br-5f2c1a9e7b31 OUT= SRC=172.18.0.3 DST=172.18.0.1 LEN=60 TTL=64 PROTO=TCP SPT=40312 DPT=5432 SYN
```

**What the output tells you:** three separate walls. The web app listens on 127.0.0.1:3000 inside its namespace, so the published port can never reach it. The host's PostgreSQL listens only on 127.0.0.1, the api container has no host.docker.internal entry, and UFW drops the SYN from the shop network before PostgreSQL would even refuse it.

**Fix:**

```bash
# App inside the container: listen on all interfaces of its own namespace
#   node: app.listen(3000, '0.0.0.0')    gunicorn -b 0.0.0.0:8000    vite --host 0.0.0.0
# Container to host: add the name, make the host service listen on the bridge, allow it in UFW
#   compose.yaml:     extra_hosts: ["host.docker.internal:host-gateway"]
#   postgresql.conf:  listen_addresses = 'localhost,172.18.0.1'
#   pg_hba.conf:      host  all  all  172.18.0.0/16  scram-sha-256
sudo ufw allow in on br-shop to any port 5432 proto tcp comment 'shop network -> host postgres'
```

```yaml
# Give the Compose network a stable bridge name so the UFW rule survives re-creation
networks:
  default:
    driver_opts:
      com.docker.network.bridge.name: br-shop
```

**Why this fix works:** binding 0.0.0.0 inside the container exposes the app only within its own namespace; the outside world still reaches it only through what you publish. `host-gateway` resolves to the host's address on the bridge, and the UFW rule opens one port to one bridge. Don't reach for `network_mode: host` as a cure: it removes isolation, ignores `ports:`, and does not exist for Swarm services.

**Prevent it:** prefer running the database as a container on the same network; when containers must use host services, document them, use stable bridge names, and keep the UFW rules in Ansible.

**Next step:** [Networking](30-learn-docker.md) (§7) · [Containers playbook](26-playbook-containers-k8s.md) (§3) · [Ports & inventory playbook](22-playbook-ports-inventory.md) (§14, listening but unreachable) · [Observability problems](49-observability-stack-problems.md), entry 5.1 (the same UFW trap for Prometheus) · KodeKloud: *Docker Training Course for the Absolute Beginner* — [Docker Networking](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page) · [docker run reference](https://docs.docker.com/reference/cli/docker/container/run/)

**Community threads:** [Docker forums: host.docker.internal cannot reach a localhost API](https://forums.docker.com/t/cant-access-localhost-api-from-within-docker-container-using-host-docker-internal/150788) · [Docker forums: can only access containers using localhost](https://forums.docker.com/t/can-only-access-containers-using-localhost-from-the-host/150125) · [Docker forums: cannot access containers via 127.0.0.1 or LAN IP](https://forums.docker.com/t/cannot-access-containers-via-127-0-0-1-or-lan-ip/150176) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+container+connect+to+host+postgres+linux+host.docker.internal) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=host.docker.internal+linux&restrict_sr=1)

### 4.2 Containers can't find each other by name

> **Seen as:** `getaddrinfo ENOTFOUND db`, `php_network_getaddresses: getaddrinfo for db failed: Name or service not known`, `network dokploy-network declared as external, but could not be found`, or requests that randomly reach the wrong database · **Where:** containers on the default bridge, an app and its database in two Compose projects or two Dokploy apps, services joining dokploy-network for Traefik · **Level:** [L1 · Junior] · **How common:** the phpMyAdmin getaddrinfo question is in this year's forums.docker.com top list; Dokploy documents ENOTFOUND for its own postgres in its troubleshooting pages

**Why it happens:** Docker's embedded DNS (127.0.0.11) answers names only for containers on the same user-defined network. The default bridge has no name resolution at all. Each Compose project gets its own default network, so services in two projects cannot see each other unless they share a network. An external network must exist before the project starts, and a Swarm overlay accepts standalone containers only if it was created `--attachable`. The nasty variant: two projects both call their database `db` and both join one shared network; the name now resolves to two containers and the app talks to whichever answers.

**Diagnose:**

```bash
docker inspect -f '{{json .NetworkSettings.Networks}}' shop-api-1 | jq -r 'keys[]'
docker inspect -f '{{json .NetworkSettings.Networks}}' billing-db-1 | jq -r 'keys[]'
docker exec shop-api-1 getent hosts billing-db || echo "not resolvable"
docker network inspect dokploy-network -f '{{.Driver}} attachable={{.Attachable}} scope={{.Scope}}'
```

```text
shop_default
dokploy-network
billing_default
not resolvable
overlay attachable=true scope=swarm
```

**What the output tells you:** shop-api is on its own project network and dokploy-network; billing-db is only on billing's project network. They share nothing, so no name can resolve. dokploy-network exists and is attachable, so it could be joined, but putting databases on the network Traefik uses is not where they belong.

**Fix:**

```bash
docker network create shared-db          # once, before both projects start
```

```yaml
# billing/compose.yaml: the database joins a dedicated shared network under an unambiguous alias
services:
  db:
    networks:
      default: {}
      shared:
        aliases: [billing-db]
networks:
  shared:
    name: shared-db
    external: true
# shop/compose.yaml: api joins the same external network and connects to billing-db:5432
```

**Why this fix works:** both containers now sit on one user-defined network, so the embedded DNS answers the alias. A dedicated network keeps the database off dokploy-network, and a unique alias avoids two `db` records on a shared network. Avoid `links:` and IP addresses in configs; links are legacy and IPs change on every re-creation.

**Prevent it:** a naming rule (project-role aliases on shared networks), one shared network per relationship instead of "everything on one network", and `docker compose config` reviews that show every network a service joins.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) (dokploy-network) · [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 5.3 (a container on several networks) · [Networking](30-learn-docker.md) (§7) · [Containers playbook](26-playbook-containers-k8s.md) (§4) · KodeKloud: *Docker Certified Associate* — [Networking Deep Dive – Docker](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Docker/page) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: phpMyAdmin getaddrinfo for db failed](https://forums.docker.com/t/phpmyadmin-not-connecting-tot-mysql-php-network-getaddresses-getaddrinfo-for-db-failed/150611) · [Dokploy instance troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+compose+service+name+not+resolved+different+projects+network) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=containers+different+compose+projects+network+name&restrict_sr=1)

### 4.3 Port is already allocated

> **Seen as:** `Bind for 0.0.0.0:443 failed: port is already allocated`, `failed to bind host port for 0.0.0.0:80:172.18.0.5:80/tcp: address already in use`, or in Swarm `port '443' is already in use by service 'dokploy-traefik' as an ingress port` · **Where:** a host web server (Apache, nginx) and a Traefik container both wanting 80 and 443, an old container or stack still publishing the port, Swarm services published through the ingress mesh · **Level:** [L0 · Fresher] · **How common:** moby #31698 ("address already in use when deploying service", 103 comments), "Container Port Mapping Issue" in this year's forums top list, and the first real incident of this handbook's reader: Apache holding 443 when Dokploy arrived

**Why it happens:** only one listener can own an address and port. The wording tells you who: *already allocated* means Docker itself has given the port to another container; *address already in use* means a host process holds it. In Swarm, a port published through the ingress mesh is reserved on every node of the cluster, even nodes without a task of that service.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :443'
docker ps -a --filter publish=443 --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
docker service ls --format '{{.Name}}\t{{.Ports}}' 2>/dev/null | grep ':443'
```

```text
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511          0.0.0.0:443       0.0.0.0:*     users:(("apache2",pid=1043,fd=6),("apache2",pid=1042,fd=6))
```

**What the output tells you:** Apache owns 443 on all addresses, and no container or Swarm service publishes it, so this is the host-process case. If the `docker ps` line had shown a stopped `old-traefik`, removing that container would be the whole fix.

**Fix:**

```bash
# The owner decides the fix. Case 21: move Apache to 81/444 and let Traefik route its hostnames
sudo sed -i -E 's/^Listen 80$/Listen 81/; s/^(\s*)Listen 443$/\1Listen 444/' /etc/apache2/ports.conf   # Ubuntu indents "Listen 443" inside IfModule blocks
sudo grep -rl 'VirtualHost \*:443' /etc/apache2/sites-enabled/   # change each to *:444 (and *:80 to *:81)
sudo apachectl configtest && sudo systemctl restart apache2
sudo ss -ltnp 'sport = :443'                                      # now empty: Traefik can start
# A leftover container or stack instead
docker rm -f old-traefik
```

**Why this fix works:** moving the old owner frees the port without stopping its sites, and Traefik then routes the Apache hostnames to 81/444 so users notice nothing. Don't `kill -9` the process you see in `ss`: systemd restarts it within seconds and you will have learned nothing. Remember to firewall 81/444 so they are reachable only through Traefik.

**Prevent it:** keep a port inventory per host and make "who owns 80/443" part of every new install; the read-only inventory script in the ports playbook does this in one run.

**Next step:** [Apache 443 vs Dokploy case](21-case-apache-443-dokploy.md) · [Ports & inventory playbook](22-playbook-ports-inventory.md) (§6 containers, §13 bind: address already in use) · [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *Docker Certified Associate* — Docker Engine → [Publishing Ports](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page) · [docker run reference](https://docs.docker.com/reference/cli/docker/container/run/)

**Community threads:** [moby/moby #31698: address already in use when deploying a service](https://github.com/moby/moby/issues/31698) · [Docker forums: Container Port Mapping Issue](https://forums.docker.com/t/container-port-mapping-issue/150171) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22port+is+already+allocated%22+docker) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=port+is+already+allocated&restrict_sr=1)

### 4.4 Published ports bypass UFW

> **Seen as:** `ufw status` allows only 22, 80 and 443, yet a scan from outside shows 5432, 6379 or 3000 open; after a firewall reload `iptables: No chain/target/match by that name` and containers lose connectivity · **Where:** UFW-only Ubuntu servers running Compose files that publish `"5432:5432"`, Dokploy hosts with databases exposed for "quick access" · **Level:** [L2 · Mid-level] · **How common:** a perennial Server Fault and r/selfhosted complaint; Docker's own packet-filtering documentation explains it, and Dokploy and Wazuh users hit it in their own forms

**Why it happens:** a published port is a DNAT rule in the nat table. The packet's destination is rewritten before filtering, so it travels through the FORWARD chain to the container and never touches INPUT, where UFW's rules live. `ports: "5432:5432"` also binds all addresses by default. Docker provides the DOCKER-USER chain as the place for your own rules; it is evaluated before Docker's. Flushing iptables (a hand-written reset script, an old firewalld reload) deletes Docker's chains, which gives "No chain/target/match" until dockerd recreates them. Docker 28 reorganised its chains, so rules that referenced Docker's internal chains by name may stop working; DOCKER-USER stays the supported hook.

**Diagnose:**

```bash
sudo ufw status | head -6
docker ps --format '{{.Names}}\t{{.Ports}}' | grep '0.0.0.0'
sudo iptables -L DOCKER-USER -n -v --line-numbers
nmap -Pn -p 22,80,443,5432,6379 192.0.2.10        # from a machine outside the LAN
```

```text
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       10.10.0.0/24
80,443/tcp                 ALLOW       Anywhere
dokploy-traefik	0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp
shop-db-1	0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
shop-redis-1	0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
PORT     STATE    SERVICE
22/tcp   filtered ssh
80/tcp   open     http
443/tcp  open     https
5432/tcp open     postgresql
6379/tcp open     redis
```

**What the output tells you:** UFW is correct for the host, and SSH is properly filtered from outside, but PostgreSQL and Redis are published on all addresses and reachable from the internet because DOCKER-USER is empty. Only Traefik's 80/443 should be public.

**Fix:**

```bash
# 1. Don't publish what only containers need: remove ports: from db and redis (Traefik and apps use the network)
# 2. What only the host needs: bind to loopback    ports: ["127.0.0.1:5432:5432"]
# 3. A host-wide guard: new connections from outside the LAN reach only 80/443 (original ports, before DNAT)
sudo iptables -I DOCKER-USER 1 -i ens18 ! -s 10.10.0.0/24 -m conntrack --ctstate NEW -j DROP
sudo iptables -I DOCKER-USER 1 -i ens18 -p tcp -m conntrack --ctstate NEW --ctorigdstport 443 -j RETURN
sudo iptables -I DOCKER-USER 1 -i ens18 -p tcp -m conntrack --ctstate NEW --ctorigdstport 80 -j RETURN
# Persist them in /etc/ufw/after.rules (a *filter block with :DOCKER-USER) or your Ansible role
# Chains lost after a firewall flush: let Docker recreate them
sudo systemctl restart docker
```

**Why this fix works:** removing `ports:` is the real fix, since a port that is not published cannot be exposed. The DOCKER-USER rules run before Docker's own, so they apply to every published port, current and future; `--ctorigdstport` matches the port the client asked for, because by the time the packet reaches DOCKER-USER its destination already points at the container. Don't set `"iptables": false` in daemon.json: containers lose outbound NAT and published ports, and you will rebuild Docker's rules by hand.

**Prevent it:** a scheduled external nmap of every public IP compared against an allow-list, a Compose review rule "no `ports:` for internal services", and DOCKER-USER rules shipped by Ansible with the host.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 13.2 (panel and databases open past UFW) · [Wazuh & security tools](48-wazuh-and-security-tools.md), entry 9.1 (bans do not stop Docker traffic) · [Ports & inventory playbook](22-playbook-ports-inventory.md) (§14) · KodeKloud: LFCS [*Configure Packet Filtering (Firewall)*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall) · [Docker docs: packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

**Community threads:** [Docker Engine 28 release notes (firewall changes)](https://docs.docker.com/engine/release-notes/28/) · Search: [Server Fault](https://serverfault.com/search?q=docker+ufw+published+ports+bypass) · [Stack Overflow](https://stackoverflow.com/search?q=docker+ufw+DOCKER-USER+published+port) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+ufw+bypass&restrict_sr=1)

### 4.5 Docker subnets collide with the LAN or VPN

> **Seen as:** after installing Docker or adding a Compose project, part of the office or every VPN user loses SSH to the server, while everyone else is fine; or `could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network` · **Where:** networks that use 172.16.0.0/12 or 192.168.0.0/16 for offices, VPN clients or peered VPCs; hosts with many small Compose projects · **Level:** [L2 · Mid-level] · **How common:** forums.docker.com topics 139459 and 69686 and docker/for-linux #599 cover the pool error; Dokploy users meet the same exhaustion (module 45, entry 11.3)

**Why it happens:** Docker's default pools are 172.17.0.0/16 to 172.31.0.0/16 for bridges, then slices of 192.168.0.0/16. Every bridge network adds a connected route on the host. If a project receives 172.20.0.0/16 and your VPN clients also live in 172.20.0.0/16, the server's replies to them go into the bridge instead of to the gateway. Docker only avoids ranges that appear in the host's routing table when the network is created; networks reached through the default gateway are invisible to it. Many projects also exhaust the pools, which gives the "non-overlapping" error. Changing the pools later does not move existing networks, and Swarm's overlay pool can only be chosen at `docker swarm init`.

**Diagnose:**

```bash
ip route | grep -E 'docker0|br-'
for n in $(docker network ls -q --filter driver=bridge); do docker network inspect -f '{{.Name}} {{range .IPAM.Config}}{{.Subnet}}{{end}}' "$n"; done
ip route get 172.20.14.7
```

```text
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev br-5f2c1a9e7b31 proto kernel scope link src 172.18.0.1
172.20.0.0/16 dev br-0c9d2e4f6a1b proto kernel scope link src 172.20.0.1
bridge 172.17.0.0/16
shop_default 172.18.0.0/16
monitoring_default 172.20.0.0/16
172.20.14.7 dev br-0c9d2e4f6a1b src 172.20.0.1 uid 1001
```

**What the output tells you:** the monitoring project's network took 172.20.0.0/16, and the route lookup for a VPN client (172.20.14.7) now points into that bridge. Every VPN user's SSH replies vanish into a Docker network.

<div class="env" data-env="onprem" markdown="1">

**On-premise:** offices, VPN pools, partner links and lab networks very often sit in 172.16.0.0/12 or 192.168.0.0/16. Reserve a block for Docker in the IP plan before the first install, for example 10.200.0.0/24 for docker0, 10.201.0.0/16 for bridge pools in /24 slices and 10.20.0.0/16 for Swarm overlays, and check it against every site and VPN range.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** the default VPC is 172.31.0.0/16, which is also Docker's last default pool, and peered VPCs, Transit Gateway attachments or Client VPN ranges in 172.16.0.0/12 are not in the instance's routing table, so Docker cannot see them. The symptom is the same: one peered subnet cannot reach one host. Take Docker's ranges from your IPAM plan outside every VPC CIDR you use or may peer with.

</div>

**Fix:**

```bash
# /etc/docker/daemon.json
#   "bip": "10.200.0.1/24",
#   "default-address-pools": [ { "base": "10.201.0.0/16", "size": 24 } ]
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
# Existing networks keep their old subnets: recreate them project by project
cd /srv/monitoring && docker compose down && docker compose up -d
docker network prune -f
# Swarm overlays: only at init, before Dokploy is installed on a new cluster
docker swarm init --advertise-addr 10.10.0.10 --default-addr-pool 10.20.0.0/16 --default-addr-pool-mask-length 24
```

**Why this fix works:** /24 slices of a /16 give 256 networks instead of a handful of /16s, and a reserved range cannot collide with anything you own. Recreating each project moves it into the new pool. On an existing Swarm the overlay pool cannot be changed in place; for Dokploy that means rebuilding the cluster in a window, which is why the range must be decided before the first `swarm init`.

**Prevent it:** Docker ranges belong in the IP plan and in the Ansible role that installs Docker, so every host gets daemon.json before its first container.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 11.3 · [Learn networking](28-learn-networking.md) · [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) · KodeKloud: *Docker Certified Associate* — Docker Engine – Networking · [Docker docs: Swarm networking](https://docs.docker.com/engine/swarm/networking/)

**Community threads:** [Docker forums: no non-overlapping IPv4 address pool](https://forums.docker.com/t/error-could-not-find-an-available-non-overlapping-ipv4-address-pool-among-the-defaults-to-assign-to-the-network/139459) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+default-address-pools+vpn+conflict) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=docker+subnet+conflict+vpn&restrict_sr=1)

### 4.6 No DNS or no internet in containers and builds

> **Seen as:** `Temporary failure in name resolution` during `apt-get update` in a Dockerfile; `Could not resolve host: gitlab.corp.example.com` inside a container while the host resolves it; `dial tcp: lookup registry-1.docker.io: i/o timeout` or `proxyconnect tcp` on pull; outbound mail from a container timing out · **Where:** hosts with a local caching resolver, corporate networks that block public DNS, internal-only zones, HTTP proxies · **Level:** [L1 · Junior] · **How common:** "Docker DNS Error", "accessing an external SMTP server from a container" and the getaddrinfo question are all in this year's forums.docker.com top list

**Why it happens:** Docker cannot hand loopback resolvers to containers. If the host's resolv.conf lists only 127.0.0.53 (systemd-resolved), Docker reads the real upstreams from systemd-resolved's file; if it lists only 127.0.0.1 (a local dnsmasq, Unbound or Pi-hole), Docker finds nothing usable and falls back to Google's 8.8.8.8 and 8.8.4.4. Corporate firewalls often block those, and they never know your internal zones. Proxies have three separate settings: dockerd's own environment (for pulls), the client's ~/.docker/config.json (injected into containers and builds) and the application's own configuration. NO_PROXY must list Harbor and internal hosts, or pulls go to the proxy and fail.

**Diagnose:**

```bash
cat /etc/resolv.conf | grep nameserver
docker run --rm busybox:1.36 cat /etc/resolv.conf
docker run --rm busybox:1.36 nslookup gitlab.corp.example.com
docker info --format 'proxy={{.HTTPProxy}} noproxy={{.NoProxy}}'
```

```text
nameserver 127.0.0.1
nameserver 8.8.8.8
nameserver 8.8.4.4
;; connection timed out; no servers could be reached
proxy= noproxy=
```

**What the output tells you:** the host uses a local resolver on 127.0.0.1, so containers fell back to 8.8.8.8, which this network blocks, and nothing internal could resolve anyway. dockerd has no proxy, so pulls from Docker Hub through the corporate proxy will fail next.

<div class="env" data-env="onprem" markdown="1">

**On-premise:** point Docker at the internal resolvers (here 10.10.0.2), add the search domain, and give dockerd the proxy with a NO_PROXY list that covers Harbor, GitLab and the private ranges. Split DNS over a VPN (only corp.example.com through the tunnel) needs the internal resolver listed explicitly, because containers do not inherit per-link routing domains.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** the VPC resolver (169.254.169.253, or the VPC base address plus two) is the only one that answers Route 53 private hosted zones, and Docker normally picks it up through systemd-resolved. Never hardcode 8.8.8.8 in daemon.json on EC2. In private subnets without a NAT gateway, pulls time out rather than fail DNS: add VPC endpoints for ECR (api and dkr) plus the S3 gateway endpoint, or pull through a registry inside the VPC.

</div>

**Fix:**

```bash
# /etc/docker/daemon.json
#   "dns": ["10.10.0.2"],
#   "dns-search": ["corp.example.com"],
#   "proxies": { "http-proxy": "http://proxy.example.com:3128",
#                "https-proxy": "http://proxy.example.com:3128",
#                "no-proxy": "localhost,127.0.0.1,10.0.0.0/8,.corp.example.com,harbor.example.com" }
sudo dockerd --validate --config-file /etc/docker/daemon.json && sudo systemctl restart docker
# Containers and builds started by this user: ~/.docker/config.json
#   { "proxies": { "default": { "httpProxy": "http://proxy.example.com:3128",
#                               "httpsProxy": "http://proxy.example.com:3128",
#                               "noProxy": "localhost,127.0.0.1,.corp.example.com,harbor.example.com" } } }
docker run --rm busybox:1.36 nslookup gitlab.corp.example.com
```

**Why this fix works:** `dns` replaces the fallback with resolvers that know your zones and are allowed through the firewall. The daemon's `proxies` cover image pulls; the client's proxies are injected as environment variables into containers and as build arguments into builds. A docker-container buildx builder is separate again and needs its own settings (entry 6.2).

**Prevent it:** one golden daemon.json per site, and a CI smoke test that resolves an internal name and fetches an external URL from inside a container.

**Next step:** [DNS reference](08-dns.md) · [Learn networking](28-learn-networking.md) · [Containers playbook](26-playbook-containers-k8s.md) (§4) · KodeKloud: [*Demystifying DNS*](https://kodekloud.com/courses/demystifying-dns) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: Docker DNS error](https://forums.docker.com/t/docker-dns-error-on-raspberry-pi/150418) · [Docker forums: external SMTP server from a container](https://forums.docker.com/t/accessing-to-external-smtp-server-from-a-docker-container/150289) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+build+%22Temporary+failure+in+name+resolution%22+corporate+dns) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=docker+dns+8.8.8.8+fallback&restrict_sr=1)

### 4.7 MTU: large transfers hang, pulls stall

> **Seen as:** `docker pull` stuck at `Pulling fs layer` or `Retrying in 5 seconds`; `curl` from a container prints the headers and then hangs; `git clone` or a TLS handshake stalls; small requests such as ping or a health check work · **Where:** hosts behind WireGuard (MTU 1420), OpenStack or VXLAN underlays (1450), PPPoE (1492) or IPsec; Swarm overlays; GitLab Docker-in-Docker jobs · **Level:** [L2 · Mid-level] · **How common:** "Docker stuck on Pulling fs layer" is in this year's forums top list; libnetwork #2661 and moby #53765 (overlay MTU 20 bytes too large on IPv6 data paths) track the overlay side

**Why it happens:** containers use MTU 1500 by default, whatever the real path allows. When a full-size packet with the don't-fragment bit meets a smaller link, the router should send back "fragmentation needed"; if a firewall drops that ICMP, the big packets vanish silently and only small ones get through. Overlays make it worse: VXLAN adds 50 bytes over IPv4 (70 over IPv6), so the overlay MTU must be the underlay MTU minus that overhead, and until the fix for moby #53765 Docker subtracted only the IPv4 overhead on IPv6 data paths.

**Diagnose:**

```bash
for i in ens18 wg0 docker0; do echo "$i $(cat /sys/class/net/$i/mtu)"; done
# iputils ping is needed for -M do (BusyBox ping in alpine has no such option); netshoot ships it
docker run --rm nicolaka/netshoot ping -c 2 -M do -s 1472 203.0.113.50     # 1500-byte packets
docker run --rm nicolaka/netshoot ping -c 2 -M do -s 1372 203.0.113.50     # 1400-byte packets
tracepath -n 203.0.113.50 | tail -1
```

```text
ens18 1500
wg0 1420
docker0 1500
PING 203.0.113.50 (203.0.113.50) 1472(1500) bytes of data.
2 packets transmitted, 0 received, 100% packet loss, time 1012ms
PING 203.0.113.50 (203.0.113.50) 1372(1400) bytes of data.
1380 bytes from 203.0.113.50: icmp_seq=1 ttl=57 time=12.4 ms
     Resume: pmtu 1420 hops 9 back 9
```

**What the output tells you:** the registry at 203.0.113.50 is reached through the WireGuard tunnel with a path MTU of 1420. Full-size packets from containers disappear while 1400-byte ones pass, which is the classic black hole: small requests work, anything big hangs.

**Fix:**

```bash
# daemon.json: docker0 and, through default-network-opts, every new bridge network
#   "mtu": 1400,
#   "default-network-opts": { "bridge": { "com.docker.network.driver.mtu": "1400" } }
# Compose networks created before the change: recreate them, or set it per network
#   networks: { default: { driver_opts: { com.docker.network.driver.mtu: "1400" } } }
# Swarm overlay across the tunnel: underlay 1420 minus 50 bytes of VXLAN
docker network create -d overlay --attachable --opt com.docker.network.driver.mtu=1370 apps-net
# Or once, on the router or tunnel host: clamp TCP MSS to the path MTU
sudo iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
```

**Why this fix works:** a lower container MTU makes every packet fit the smallest link, and MSS clamping makes TCP choose small enough segments even for hosts you do not control. Overlay MTU is fixed at creation, so you create a new network and move services to it. Don't "fix" it by allowing fragmentation everywhere or by turning off PMTU discovery; let the ICMP "fragmentation needed" messages through your firewalls instead.

**Prevent it:** record the MTU of every link and tunnel in the network documentation, and set overlay MTU explicitly whenever Swarm nodes talk through a VPN.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), entry 6.2 (DinD builds hang on downloads) · [Network speed playbook](24-playbook-network-speed.md) · [Learn networking](28-learn-networking.md) · KodeKloud: [*Networks and Communications*](https://kodekloud.com/courses/networks-and-communications) · [Docker docs: Swarm networking](https://docs.docker.com/engine/swarm/networking/)

**Community threads:** [moby/moby #53765: overlay MTU 20 bytes too large on IPv6 data paths](https://github.com/moby/moby/issues/53765) · [moby/libnetwork #2661: overlay broken when the outside MTU is smaller](https://github.com/moby/libnetwork/issues/2661) · [Docker forums: stuck on Pulling fs layer](https://forums.docker.com/t/docker-stuck-on-pulling-fs-layer-after-downloading-is-started/151108) · [cr0x: Docker network MTU and MSS fixes](https://cr0x.net/en/docker-network-mtu-mss-fixes/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+mtu+vpn+pull+hangs) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=docker+mtu+wireguard&restrict_sr=1)

---

## 5. Registries and Docker Hub

Every deploy starts with a pull. These entries cover the public registry's limits, credentials that go to the wrong place, and the private CA that every client has to trust separately.

### 5.1 Docker Hub rate limit, and mirrors that don't mirror

> **Seen as:** `toomanyrequests: You have reached your pull rate limit. You may increase the limit by authenticating and upgrading`; with Harbor's proxy cache `manifest unknown` for `dockerhub-proxy/nginx`; with a mirror configured in daemon.json, builds and Kubernetes nodes still hitting Docker Hub · **Where:** GitLab runners, Kubernetes nodes and Dokploy builds behind one NAT address pulling anonymously; Docker-in-Docker jobs that start with an empty cache · **Level:** [L1 · Junior] · **How common:** a constant theme since 2020; the limits were revised in 2025, Harbor recommends its proxy cache because of it, and Harbor issues #19609, #18335 and #21454 (proxy cache listing and tagging) collected dozens of comments each

**Why it happens:** Docker Hub counts anonymous pulls per IPv4 address or IPv6 /64 (the documentation in October 2026 lists 100 pulls per 6 hours anonymous and 200 for an authenticated Personal account; paid plans are unlimited). Every runner behind your NAT shares that budget, and DinD jobs re-pull base images every time. Mirrors are partial by design: `registry-mirrors` in daemon.json applies only to Docker Hub images pulled by dockerd, not to BuildKit docker-container builders, containerd or kubelet, or a DinD daemon. It also accepts only a host, not a path, so it cannot point at a Harbor proxy project. In Harbor's proxy cache, official images need the `library/` segment, and cached repositories appear only after their first pull.

**Diagnose:**

```bash
# Remaining budget for this IP (a HEAD request on Docker's test repository does not count as a pull)
TOKEN=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull" | jq -r .token)
curl -sI -H "Authorization: Bearer $TOKEN" https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest | grep -i ratelimit
jq -r '.auths | keys[]' ~/.docker/config.json 2>/dev/null | grep -c docker.io
docker pull harbor.example.com/dockerhub-proxy/nginx:1.27
```

```text
ratelimit-limit: 100;w=21600
ratelimit-remaining: 0;w=21600
0
Error response from daemon: manifest for harbor.example.com/dockerhub-proxy/nginx:1.27 not found: manifest unknown: repository dockerhub-proxy/nginx not found
```

**What the output tells you:** this address has used its 100 anonymous pulls in the 6-hour window, the host never logged in to Docker Hub, and the Harbor attempt failed only because the official image path lacks `library/`.

**Fix:**

```bash
# 1. Authenticate every host and runner with a read-only personal access token
echo "$DOCKERHUB_TOKEN" | docker login -u ciuser --password-stdin
# 2. Pull through Harbor's proxy cache, with library/ for official images
docker pull harbor.example.com/dockerhub-proxy/library/nginx:1.27
#    Dockerfile: FROM harbor.example.com/dockerhub-proxy/library/node:22-alpine
# 3. Transparent mirroring for containerd (Kubernetes nodes): /etc/containerd/certs.d/docker.io/hosts.toml
#      server = "https://registry-1.docker.io"
#      [host."https://harbor.example.com/v2/dockerhub-proxy"]
#        capabilities = ["pull", "resolve"]
#        override_path = true
# 4. dockerd mirrors take a host without a path; a path gives
#      invalid mirror: path, query, or fragment at end of the URI
#    so for "registry-mirrors" run a plain pull-through registry (registry:2 with a proxy remoteurl)
```

<div class="env" data-env="onprem" markdown="1">

**On-premise:** Harbor's proxy cache project (or a plain pull-through registry) inside the LAN gives you one Hub login, a local copy of every base image and pulls that keep working when the internet link is down. Put the proxy path in CI templates so new projects use it by default.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** ECR pull-through cache rules do the same for Docker Hub (with Hub credentials stored in Secrets Manager), and pulls from ECR inside the region avoid the NAT gateway's per-GB charge when you add the ECR VPC endpoints.

</div>

**Why this fix works:** authenticated pulls get their own, larger budget per account instead of sharing one per IP. A proxy cache turns a hundred identical pulls into one upstream pull. Mirroring has to be configured per client type because each one resolves registries on its own. Don't share one personal Docker Hub password across all servers; use tokens per purpose and revoke them when a host is retired.

**Prevent it:** base images always come through the proxy path, runners are logged in by their bootstrap role, and a weekly report from Harbor shows which projects still pull from Docker Hub directly.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) (runners and DinD) · [Registries and Harbor](30-learn-docker.md) (§11) · KodeKloud: *Docker Training Course for the Absolute Beginner* — [Docker Registry](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page) · [Docker Hub pull usage and limits](https://docs.docker.com/docker-hub/usage/pulls/) · [Docker Hub mirror](https://docs.docker.com/docker-hub/image-library/mirror/) · [Harbor: configure proxy cache](https://goharbor.io/docs/2.13.0/administration/configure-proxy-cache/)

**Community threads:** [goharbor/harbor #19609: proxy cache images not listed](https://github.com/goharbor/harbor/issues/19609) · [goharbor/harbor #21454: docker.io proxy cache not tagging official images](https://github.com/goharbor/harbor/issues/21454) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+hub+%22toomanyrequests%22+rate+limit+mirror) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=docker+hub+rate+limit+mirror&restrict_sr=1)

### 5.2 Push or pull denied

> **Seen as:** `denied: requested access to the resource is denied`; Harbor `unauthorized: unauthorized to access repository: team-a/api, action: push`; `pull access denied for shop/api, repository does not exist or may require 'docker login'`; ECR `no basic auth credentials` · **Where:** the first CI push to Harbor or ECR, a new project or robot account, sudo and non-sudo shells mixed, Swarm workers pulling private images · **Level:** [L1 · Junior] · **How common:** "requested access to the resource is denied" has about 504,000 views on forums.docker.com and "ECR no basic auth credentials" about 390,000

**Why it happens:** the image name decides where it goes. A tag without a registry host (`shop/api:1.4.2`) means Docker Hub, so the push goes there and is refused. Harbor never creates projects on push, and a robot account needs push permission on that project. Credentials in config.json are keyed by the exact host string, so a login to `harbor.example.com:443` is not used for `harbor.example.com`. `sudo docker` reads /root/.docker/config.json, not yours. ECR tokens last 12 hours and the repository must exist before the first push. Swarm workers have no credentials unless the manager forwards them (entry 8.1).

**Diagnose:**

```bash
docker image ls --format '{{.Repository}}:{{.Tag}}' | grep api
jq -r '.auths | keys[]' ~/.docker/config.json
jq -r '.credsStore // "none"' ~/.docker/config.json
docker push shop/api:1.4.2 2>&1 | tail -1
```

```text
shop/api:1.4.2
harbor.example.com:443
none
denied: requested access to the resource is denied
```

**What the output tells you:** two separate mistakes. The image carries no registry host, so the push went to Docker Hub's `shop` namespace, which you do not own. And the Harbor login was saved under `harbor.example.com:443`, which will not match images named `harbor.example.com/...`.

**Fix:**

```bash
docker tag shop/api:1.4.2 harbor.example.com/team-a/api:1.4.2
echo "$HARBOR_ROBOT_TOKEN" | docker login harbor.example.com -u 'robot$team-a+ci' --password-stdin
docker push harbor.example.com/team-a/api:1.4.2
# Harbor: the project must exist and the robot needs push (Projects > team-a > Robot Accounts)
# ECR: log in again every 12 hours and create the repository first
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin 111122223333.dkr.ecr.eu-central-1.amazonaws.com
```

**Why this fix works:** a fully qualified name sends the push to the right registry and project, and a login under the same host string lets Docker find the credentials. The single quotes keep the shell from expanding `$team` in the robot name (entry 9.3). Don't run CI jobs as root just to reuse root's login; give the job its own robot account.

**Prevent it:** CI templates that always build the image name from variables (registry, project, app, commit SHA), one robot account per project with an expiry date, and a project-creation step in the runbook for new apps.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) (pushing to Harbor) · entry 9.3 (robot accounts) · [Registries and Harbor](30-learn-docker.md) (§11) · KodeKloud: *Docker Certified Associate* — [Docker Image Registry](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Docker-Image-Registry/page) · *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — [Docker Push](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [forums.docker.com all-time top topics](https://forums.docker.com/top?period=all) · Search: [Stack Overflow: access denied](https://stackoverflow.com/search?q=%22denied%3A+requested+access+to+the+resource+is+denied%22) · [Stack Overflow: ECR](https://stackoverflow.com/search?q=ecr+%22no+basic+auth+credentials%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=harbor+push+unauthorized&restrict_sr=1)

### 5.3 x509: unknown authority for a private registry

> **Seen as:** `tls: failed to verify certificate: x509: certificate signed by unknown authority` on `docker login` or pull; the same from kubelet (`ErrImagePull`), from a buildx build while `docker pull` works, or from a DinD job; also `x509: certificate is valid for harbor-1, not harbor.example.com` · **Where:** Harbor or GitLab's registry behind a private CA; every client type keeps its own trust: Docker hosts, Swarm workers, Kubernetes nodes, DinD, buildx builders · **Level:** [L2 · Mid-level] · **How common:** "Adding (self signed) certificates" has about 134,000 views on forums.docker.com, moby #9118 has 75 comments, and buildx #1642 is among buildx's most-reacted issues

**Why it happens:** trust is per client. dockerd reads /etc/docker/certs.d/HOST[:PORT]/ca.crt plus the OS store; the directory name must match the registry exactly as written in the image name. Files ending in `.crt` there are CAs; `.cert` and `.key` are client certificates. containerd reads its own certs.d hosts.toml or the OS store. A docker-container buildx builder and a DinD daemon run in containers with their own stores. On the server side, Harbor must send the full chain (leaf plus intermediate) and a certificate with the registry name in its SAN list.

**Diagnose:**

```bash
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts 2>/dev/null | grep -E '^ *[0-9] s:|^ *i:'
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com 2>/dev/null | openssl x509 -noout -ext subjectAltName
ls /etc/docker/certs.d/
docker buildx ls | head -2
```

```text
 0 s:CN=harbor.example.com
   i:CN=Example Issuing CA 1
X509v3 Subject Alternative Name:
    DNS:harbor.example.com, IP Address:10.10.0.40
harbor.example.com:443
NAME/NODE          DRIVER/ENDPOINT                  STATUS    BUILDKIT   PLATFORMS
ci-builder*        docker-container
```

**What the output tells you:** three problems at once. Harbor sends only its own certificate (depth 0) without the intermediate "Example Issuing CA 1", so clients that trust only the root cannot build the chain. The certs.d directory is named `harbor.example.com:443`, but images are named without a port, so Docker never looks there. And builds run on a docker-container builder, which ignores certs.d entirely. The SAN list is fine.

**Fix:**

```bash
# Server: serve leaf + intermediate (the file harbor.yml points to), then ./prepare and restart Harbor
cat harbor.example.com.crt example-issuing-ca.crt | sudo tee /data/cert/harbor.example.com.crt
# Docker hosts and Swarm nodes: directory name exactly as in the image reference
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp example-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
# OS store (curl, git, Go tools, containerd's fallback)
sudo cp example-ca.crt /usr/local/share/ca-certificates/example-ca.crt && sudo update-ca-certificates
# containerd on Kubernetes nodes: /etc/containerd/certs.d/harbor.example.com/hosts.toml
#   server = "https://harbor.example.com"
#   [host."https://harbor.example.com"]
#     ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
# buildx builders: entry 6.2 (buildkitd.toml); DinD: mount the CA into the service, see module 47
```

<div class="env" data-env="onprem" markdown="1">

**On-premise:** a private CA is normal here, so treat its distribution as part of building a host: an Ansible role that installs the root into the OS store, Docker's certs.d and containerd's certs.d on every Docker host, runner and Kubernetes node, and bakes it into your DinD and builder images. Monitor certificate expiry on harbor.example.com with a blackbox probe.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** ECR endpoints use publicly trusted certificates, so this error appears only for self-hosted registries on EC2. The simplest route is a public certificate on the load balancer in front of Harbor (ACM on the ALB or NLB). If you use AWS Private CA, you still distribute its root to every client, through the AMI, user data or SSM, exactly as on-prem.

</div>

**Why this fix works:** the full chain lets any client that trusts the root verify the leaf, and the exact directory name is how Docker finds the CA for a host. Each further client gets the same root through its own mechanism. Never answer x509 with `insecure-registries` outside a throwaway lab: it disables verification for that registry, invites man-in-the-middle attacks on your image supply, and BuildKit ignores it anyway.

**Prevent it:** one CA-distribution role for every client type, the chain checked in CI with `openssl s_client`, and expiry alerts 30 days ahead.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 9.3 · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md), entry 7.2 · [Wazuh & security tools](48-wazuh-and-security-tools.md), entry 10.2 (Trivy scanning Harbor) · [Web, HTTP & TLS reference](18-web-http-tls.md) · KodeKloud: LFCS [*Work With SSL Certificates*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) · [Docker docs: registry certificates](https://docs.docker.com/engine/security/certificates/) · [Harbor: configure HTTPS](https://goharbor.io/docs/2.15.0/install-config/configure-https/)

**Community threads:** [docker/buildx #1642: BuildKit ignores insecure-registries](https://github.com/docker/buildx/issues/1642) · [Docker docs: BuildKit configuration](https://docs.docker.com/build/buildkit/configure/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+private+registry+%22x509%3A+certificate+signed+by+unknown+authority%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=harbor+x509+unknown+authority&restrict_sr=1)

---

## 6. Builds with BuildKit and buildx

BuildKit is Docker's build engine and buildx its front end. It is faster and smarter than the old builder, and it surprises people in three ways: images built for the wrong CPU, builders that live in their own container with their own configuration, and extra metadata that some registries and consumers do not expect.

### 6.1 exec format error or no matching manifest

> **Seen as:** `exec /usr/local/bin/docker-entrypoint.sh: exec format error`; `no matching manifest for linux/arm64/v8 in the manifest list entries`; `The requested image's platform (linux/arm64) does not match the detected host platform (linux/amd64/v3)`; `docker exporter does not currently support exporting manifest lists`; `exec ./entrypoint.sh: no such file or directory` for a file that exists · **Where:** images built on Apple silicon laptops or ARM boards and run on amd64 servers (or the reverse), scripts edited on Windows · **Level:** [L1 · Junior] · **How common:** buildx #59 (multi-arch with --load fails, 51 reactions), #166 (where did the multi-platform image go, 41) and #1595 (/bin/sh no such file or directory, 34)

**Why it happens:** a container runs the CPU instructions of the platform it was built for; the kernel refuses a foreign binary with "exec format error". An image built on an M-series Mac is arm64 unless you ask for amd64. A multi-platform build produces a manifest list, which the classic image store cannot hold, so `--load` fails unless the containerd image store is enabled. "No such file or directory" for a script that exists means its interpreter is missing: Windows line endings turn `#!/bin/sh` into `/bin/sh` followed by a carriage return, or the script asks for bash on Alpine.

**Diagnose:**

```bash
docker image inspect -f '{{.Os}}/{{.Architecture}}' harbor.example.com/shop/api:1.4.2
uname -m
docker buildx imagetools inspect harbor.example.com/shop/api:1.4.2 | grep Platform
head -1 entrypoint.sh | od -c | head -1
```

```text
linux/arm64
x86_64
  Platform:    linux/arm64
0000000   #   !   /   b   i   n   /   s   h  \r  \n
```

**What the output tells you:** the image exists only for arm64 (built on a laptop) and the server is x86_64, so the kernel cannot execute it. The entrypoint also has a carriage return after the shebang, which would fail next even on the right platform.

**Fix:**

```bash
# Build for the servers' platform (or several) in CI and push the result
docker buildx build --platform linux/amd64,linux/arm64 -t harbor.example.com/shop/api:1.4.3 --push .
# Line endings: fix the file and stop Git from converting it again
sed -i 's/\r$//' entrypoint.sh
printf '*.sh text eol=lf\n' >> .gitattributes
# Loading a multi-platform image locally needs the containerd image store (default on fresh Docker 29 installs)
docker info --format '{{.DriverStatus}}'
```

**Why this fix works:** `--platform` builds one image per architecture under one tag, and each host pulls its own. Pushing straight to the registry sidesteps the local store's limits. Cross-building through QEMU emulation works but is slow for compiled languages; native runners per architecture are the senior answer. Don't "fix" exec format errors by installing qemu-user-static on production servers to run foreign images.

**Prevent it:** images are built only in CI with an explicit `--platform`, a `.gitattributes` rule for scripts, and Harbor's artifact view (it shows the platforms of every tag) as part of release checks.

**Next step:** [Dockerfile mastery](30-learn-docker.md) (§4) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Docker Certified Associate* — [Multi-Stage Builds](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page) · [Docker docs](https://docs.docker.com/)

**Community threads:** [docker/buildx #59: multi-arch with --load fails](https://github.com/docker/buildx/issues/59) · [docker/buildx #166: where did the multi-platform image go?](https://github.com/docker/buildx/issues/166) · [docker/buildx #1595: /bin/sh no such file or directory](https://github.com/docker/buildx/issues/1595) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+%22exec+format+error%22+arm64+amd64) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=exec+format+error+m1+mac&restrict_sr=1)

### 6.2 buildx builder ignores daemon.json

> **Seen as:** `http: server gave HTTP response to HTTPS client` although insecure-registries is set; `x509: certificate signed by unknown authority` from `docker buildx build` while `docker pull` of the same image works; Docker Hub rate limits despite registry-mirrors; `network mode "shop_default" not supported by buildkit` · **Where:** CI runners and build hosts using `docker buildx create --driver docker-container` for cache export or multi-platform builds, behind a proxy or a private CA · **Level:** [L2 · Mid-level] · **How common:** buildx #1642 (BuildKit ignores insecure-registries, 38 reactions), #175 (custom network not supported, 82) and #476 (cannot load metadata for base images, 77)

**Why it happens:** a docker-container builder is a separate buildkitd running in its own container. It does not read daemon.json or /etc/docker/certs.d; it has its own configuration file (buildkitd.toml), its own CA store, its own mirrors and its own proxy environment. The default `docker` driver uses the daemon's settings but lacks some features (registry cache export and multi-platform output need the containerd image store). BuildKit's RUN steps support only the default, host and none network modes, never a Compose network, so a build cannot reach a service container by name.

**Diagnose:**

```bash
docker buildx ls
docker buildx inspect ci-builder | grep -E '^Driver|BuildKit version'
docker exec buildx_buildkit_ci-builder0 sh -c 'ls /etc/buildkit/; env | grep -i proxy'
```

```text
NAME/NODE          DRIVER/ENDPOINT                  STATUS    BUILDKIT   PLATFORMS
ci-builder*        docker-container
 \_ ci-builder0     \_ unix:///var/run/docker.sock   running   v0.25.1    linux/amd64, linux/386
default            docker
 \_ default         \_ default                       running   v0.25.1    linux/amd64, linux/386
Driver:           docker-container
BuildKit version: v0.25.1
buildkitd.toml
```

**What the output tells you:** builds go to ci-builder (the asterisk), a docker-container builder created with a default buildkitd.toml and no proxy variables. Nothing configured in daemon.json reaches it, which explains every symptom above.

**Fix:**

```toml
# /etc/buildkit/buildkitd.toml, kept in Git
[registry."docker.io"]
  mirrors = ["mirror.example.com"]
[registry."harbor.example.com"]
  ca = ["/etc/buildkit/certs/example-ca.crt"]
```

```bash
docker buildx rm ci-builder
docker buildx create --name ci-builder --driver docker-container \
  --buildkitd-config /etc/buildkit/buildkitd.toml \
  --driver-opt env.http_proxy=http://proxy.example.com:3128 \
  --driver-opt env.https_proxy=http://proxy.example.com:3128 \
  --driver-opt '"env.no_proxy=harbor.example.com,.corp.example.com"' \
  --use --bootstrap
# A RUN step that must reach a service: host networking, allowed explicitly
#   create with:  --buildkitd-flags '--allow-insecure-entitlement network.host'
#   build with:   docker buildx build --network host --allow network.host ...
```

**Why this fix works:** buildx copies the config file and the CA files it names into the new builder, so the builder trusts Harbor and uses your mirror. Proxy variables passed as driver options become the builder's environment. Host networking is an entitlement because it gives the build access to everything the host can reach, so it is off unless granted. Don't add `insecure = true` for Harbor in buildkitd.toml to silence x509; trust the CA instead.

**Prevent it:** create builders from a CI template with the config in Git, recreate them when the config changes, and use the plain docker driver when you need none of the extras.

**Next step:** entry 5.3 (x509 everywhere) · entry 4.6 (DNS and proxies) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) (runners and DinD) · KodeKloud: *Docker Certified Associate* — Docker Image Management (Build Cache) · [Docker docs: BuildKit configuration](https://docs.docker.com/build/buildkit/configure/)

**Community threads:** [docker/buildx #1642: BuildKit ignores insecure-registries](https://github.com/docker/buildx/issues/1642) · [docker/buildx #175: custom network not supported by BuildKit](https://github.com/docker/buildx/issues/175) · Search: [Stack Overflow](https://stackoverflow.com/search?q=buildx+docker-container+driver+x509+private+registry) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=buildx+builder+insecure+registry&restrict_sr=1)

### 6.3 Harbor shows unknown/unknown; cache export fails

> **Seen as:** every pushed image has an extra artifact with platform `unknown/unknown` in Harbor; a serverless platform or an older tool rejects the image's manifest type; `--cache-to type=registry` against Harbor fails with `unexpected status: 404 Not Found` · **Where:** CI pipelines on buildx 0.10 or newer pushing to Harbor; registry-backed build cache shared between runners · **Level:** [L3 · Senior] · **How common:** goharbor/harbor #14774 (BuildKit cache export 404, 64 reactions and 64 comments) and buildx #1533 (default output since 0.10 cannot run on some serverless platforms, 28 reactions)

**Why it happens:** since buildx 0.10, pushes include a provenance attestation by default. The result is an OCI image index whose extra entries describe the build rather than run code, and they carry the platform unknown/unknown. Registries store them as artifacts; consumers that expect a single image manifest choke on the index. Separately, BuildKit's classic registry cache is written with a cache-specific manifest type that some registries, Harbor among them, refuse; BuildKit can instead write the cache as an ordinary OCI image manifest.

**Diagnose:**

```bash
docker buildx imagetools inspect --raw harbor.example.com/shop/api:1.4.3 \
  | jq -r '.mediaType, (.manifests[] | "\(.platform.os)/\(.platform.architecture) \(.annotations["vnd.docker.reference.type"] // "image")")'
docker buildx version
```

```text
application/vnd.oci.image.index.v1+json
linux/amd64 image
unknown/unknown attestation-manifest
github.com/docker/buildx v0.29.1 0a5c2b6
```

**What the output tells you:** the tag points to an index with one real image (linux/amd64) and one attestation manifest. Nothing is broken in Harbor; the extra entry is the provenance record. Whether it is a problem depends only on the consumer.

**Fix:**

```bash
# Consumers that need a single plain manifest: turn attestations off for that build only
docker buildx build --provenance=false --sbom=false -t harbor.example.com/shop/api:1.4.3 --push .
# Registry cache in Harbor: write it as an OCI image manifest into its own repository
docker buildx build \
  --cache-from type=registry,ref=harbor.example.com/shop/api-cache:main \
  --cache-to type=registry,ref=harbor.example.com/shop/api-cache:main,mode=max,image-manifest=true,oci-mediatypes=true \
  -t harbor.example.com/shop/api:1.4.3 --push .
```

**Why this fix works:** without attestations the push is a plain image again, which every consumer understands. `image-manifest=true` stores the cache in a shape every OCI registry accepts. Keep attestations and SBOMs wherever consumers handle them: they are supply-chain evidence that scanners and auditors use. A separate cache repository lets retention clean it on its own schedule (entry 9.2).

**Prevent it:** pin the buildx version in the CI image, decide per target whether attestations are wanted, and document the cache repository convention for every project.

**Next step:** entry 9.2 (retention and GC) · [Security & DevSecOps](37-learn-security-devsecops.md) (supply chain security) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Docker Certified Associate* — Docker Image Management (Build Cache) · [Docker docs: BuildKit configuration](https://docs.docker.com/build/buildkit/configure/)

**Community threads:** [goharbor/harbor #14774: BuildKit cache export 404](https://github.com/goharbor/harbor/issues/14774) · [docker/buildx #1533: default image output since v0.10](https://github.com/docker/buildx/issues/1533) · [docker/buildx #271: intermittent 400 when pushing caches](https://github.com/docker/buildx/issues/271) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+buildx+%22unknown%2Funknown%22+provenance) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=buildx+provenance+unknown+unknown&restrict_sr=1)

---

## 7. Portainer

Portainer is a web UI over the Docker API, which makes it a mirror of whatever is wrong underneath: API versions, the socket, the network between server and agents, and Compose semantics. KodeKloud has no Portainer course; the official docs and GitHub issues are the learning material.

### 7.1 Portainer timed out, lost password, environment down

> **Seen as:** `Your Portainer instance timed out for security purposes. To re-enable your Portainer instance, you will need to restart Portainer.`; a forgotten admin password; `Failed loading environment` or `The environment named local is unavailable`; Swarm agent environments shown as down · **Where:** new installs left unattended, Docker Engine upgrades (26 and 29), Swarm clusters with the Portainer agent · **Level:** [L1 · Junior] · **How common:** Portainer #12925 (Docker 29, 439 reactions) and #11436 (Docker 26, 184 reactions) are its two most-reacted bug reports

**Why it happens:** for safety, a fresh Portainer gives you five minutes to create the admin user and then locks itself until restarted. The admin password is stored hashed in the portainer_data volume, so it can be reset but not read. An environment goes down when Portainer cannot talk to the Docker API: its embedded client is too old for the Engine (Docker 26 and 29 both raised requirements), the socket is not mounted, or the agent on port 9001 is unreachable over the overlay network.

**Diagnose:**

```bash
docker logs --tail 50 portainer 2>&1 | grep -iE 'timed out|too old|error' | tail -2
docker inspect -f '{{.Config.Image}}' portainer
docker service ps portainer_agent --format '{{.Node}} {{.CurrentState}} {{.Error}}' 2>/dev/null
```

```text
2026/10/03 08:14PM ERR unable to retrieve Docker info | error="Error response from daemon: client version 1.41 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version"
portainer/portainer-ce:2.21.5
dokploy-1 Running 3 days ago
dokploy-2 Running 3 days ago
```

**What the output tells you:** the agents are running on both nodes, so the network is not the problem; the Portainer server image is a 2.21 release whose client speaks API 1.41, which Engine 29.0 to 29.2 refuse (29.3.0 and later accept 1.40 again, so an Engine update also clears this particular error; upgrade Portainer anyway). This is entry 1.3 seen from Portainer.

**Fix:**

```bash
# Timed out before the admin user existed: restart and finish the wizard within five minutes
docker restart portainer
# Lost admin password: stop, reset with the helper (it prints a new password), start
docker stop portainer
docker run --rm -v portainer_data:/data portainer/helper-reset-password
docker start portainer
# Environment down after a Docker upgrade: replace server (and agents) with a current LTS
docker pull portainer/portainer-ce:lts
docker stop portainer && docker rm portainer
docker run -d --name portainer --restart=always -p 127.0.0.1:9443:9443 \
  -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:lts
```

**Why this fix works:** all state lives in the portainer_data volume, so replacing the container keeps users, environments and stacks. Upgrading server and agents together keeps their protocol in step. Publishing 9443 only on loopback and reaching it through Traefik with SSO or over the VPN matters, because Portainer with the socket mounted is root on the host (entry 1.2).

**Prevent it:** pin Portainer to a version tested against your Docker version, upgrade both in one change, back up portainer_data, and never leave a fresh install unconfigured on a reachable port.

**Next step:** entry 1.3 (Docker 29) · entry 1.2 (who may use the socket) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) (§2.4, socket proxy) · [Portainer documentation](https://docs.portainer.io/)

**Community threads:** [portainer/portainer #12925: Failed Loading Environment](https://github.com/portainer/portainer/issues/12925) · [portainer/portainer #11436: Docker 26 broke image details and console](https://github.com/portainer/portainer/issues/11436) · [portainer/portainer #12934: Portainer and Docker 29](https://github.com/portainer/portainer/issues/12934) · Search: [Stack Overflow](https://stackoverflow.com/search?q=portainer+%22timed+out+for+security+purposes%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=portainer+failed+loading+environment&restrict_sr=1)

### 7.2 Portainer stacks: variables, paths and limited stacks

> **Seen as:** variables typed into the stack editor never reach the container; `Failed to deploy a stack: volumes must be a mapping`; a Git-based stack whose `./config` bind mount is empty; `This stack was created outside of Portainer. Control over this stack is limited.` · **Where:** stacks created in the Portainer UI or from a Git repository, stacks first deployed with the CLI · **Level:** [L1 · Junior] · **How common:** Portainer #1857 (env_file in stacks, 45 reactions) and #6390 (relative paths in Git stacks, 34); "volumes must be a mapping" is in this year's forums.docker.com top list

**Why it happens:** Portainer writes the variables from its editor into a file called stack.env next to the compose file and uses them for interpolation; a container only receives them if the compose file references them (`env_file: stack.env` or `${VAR}` under `environment:`). "Must be a mapping" is YAML: the top-level `volumes:` was written as a list, or indentation put a key under the wrong parent. Git stacks are cloned inside Portainer's data volume, so a relative bind path points at a directory on the host that does not contain your files. Stacks deployed with the CLI have no Portainer metadata, so Portainer shows them read-only.

**Diagnose:**

```bash
docker run --rm -v portainer_data:/data alpine ls /data/compose/12/
docker compose -f docker-compose.yml --env-file stack.env config 2>&1 | head -2   # same files, on a workstation
docker inspect -f '{{json .Config.Env}}' "$(docker ps -qf name=shop_api)" | tr ',' '\n' | grep -c DB_
```

```text
docker-compose.yml
stack.env
validating docker-compose.yml: volumes must be a mapping
0
```

**What the output tells you:** Portainer saved your variables in stack.env, the compose file has a YAML shape error, and the running api container has no DB_ variables at all, because nothing in the file passes stack.env into it.

**Fix:**

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.3
    env_file: stack.env            # what you typed in Portainer's environment variables box
    volumes:
      - api-data:/var/lib/api       # a named volume instead of a ./relative path in Git stacks
volumes:                            # a mapping (name: options), not a list
  api-data: {}
```

**Why this fix works:** `env_file: stack.env` hands the editor's variables to the container, and the corrected `volumes:` block is what the Compose Specification requires. Named volumes do not depend on where Portainer cloned the repository; for config files, bake them into the image or use absolute host paths that your provisioning creates.

**Prevent it:** keep stacks in Git, run `docker compose config -q` in CI before Portainer pulls them, and decide which tool deploys what: Dokploy or a GitOps pipeline for apps, Portainer for visibility and occasional operations.

**Next step:** entry 3.2 (Compose variables) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) (Dokploy compared with other self-hosted tools) · [Portainer documentation](https://docs.portainer.io/)

**Community threads:** [portainer/portainer #1857: env_file for stacks](https://github.com/portainer/portainer/issues/1857) · [portainer/portainer #6390: relative paths in Git stacks](https://github.com/portainer/portainer/issues/6390) · [Docker forums: volumes must be a mapping](https://forums.docker.com/t/failed-to-deploy-a-stack-volumes-must-be-a-mapping/150293) · Search: [Stack Overflow](https://stackoverflow.com/search?q=portainer+stack+environment+variables+not+passed+container) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=portainer+stack+env+variables&restrict_sr=1)

---

## 8. Swarm: services, overlay and the routing mesh

Dokploy runs on Swarm, so every Dokploy app is a Swarm service and dokploy-network is a Swarm overlay. Swarm is stable and quiet, which means its sharp edges are old and well documented in moby issues with hundreds of comments. These entries go from a service that will not start to a cluster that lost its managers.

### 8.1 Service stuck at 0/1: pending or rejected tasks

> **Seen as:** `docker service ls` shows `0/1`; `docker service ps` shows `Pending` with `no suitable node (scheduling constraints not satisfied on 2 nodes)` or `insufficient resources on 2 nodes`, or `Rejected` with `No such image: harbor.example.com/team-a/api:1.4.2` · **Where:** Dokploy apps and stacks on clusters with more than one node, nodes that were rebuilt, private images in Harbor · **Level:** [L1 · Junior] · **How common:** a daily Swarm and Dokploy question; moby #33183 (service logs missing from other nodes, 74 comments) explains why the logs often look empty

**Why it happens:** the scheduler places a task only on a node that matches every placement constraint and has room for the task's reservations. Labels live in the cluster state, so a rebuilt node rejoins without them. Workers have no registry credentials of their own; they get them only when the manager forwards its login with `--with-registry-auth`. A task bound to a local volume or a bind path that exists on one node is effectively pinned there. `docker service ps` truncates its error column, which hides the most useful sentence.

**Diagnose:**

```bash
docker service ls --format '{{.Name}}\t{{.Replicas}}' | grep -w '0/[0-9]*'
docker service ps --no-trunc --format '{{.Node}}\t{{.CurrentState}}\t{{.Error}}' shop_api | head -3
docker node ls --format '{{.Hostname}}\t{{.Status}}\t{{.Availability}}\t{{.ManagerStatus}}'
docker node inspect dokploy-2 --format '{{json .Spec.Labels}}'
docker service inspect shop_api --format '{{json .Spec.TaskTemplate.Placement.Constraints}}'
```

```text
shop_api	0/1
	Pending 3 minutes ago	no suitable node (scheduling constraints not satisfied on 2 nodes)
dokploy-1	Ready	Active	Leader
dokploy-2	Ready	Active	
{}
["node.labels.role==app"]
```

**What the output tells you:** the service may only run on nodes labelled role=app, and dokploy-2, rebuilt last week, has no labels at all. Both nodes are Ready and Active, so this is placement, not node health.

**Fix:**

```bash
docker node update --label-add role=app dokploy-2
# Rejected with "No such image" on workers: forward the manager's registry login
docker service update --with-registry-auth --image harbor.example.com/team-a/api:1.4.2 shop_api
#   stacks: docker stack deploy --with-registry-auth -c compose.yml shop
# Insufficient resources: lower reservations or add capacity
docker service update --reserve-memory 256M shop_api
# A task that starts and dies: read its own error and logs
docker inspect "$(docker service ps -q shop_api | head -1)" --format '{{.Status.Err}}'
docker service logs --tail 50 --raw shop_api
```

**Why this fix works:** a matching label makes the node eligible again and the scheduler places the pending task within seconds. `--with-registry-auth` stores the credentials with the service so any node can pull. Reservations are promises the scheduler keeps, so they must fit real free capacity. Avoid constraints on hostnames: they break the first time a node is replaced.

**Prevent it:** node labels set by the provisioning role (so a rebuilt node gets them back), registry login forwarded by every deploy template, and an alert when running replicas stay below desired for five minutes.

**Next step:** [Swarm for Dokploy](30-learn-docker.md) (§14) · [Containers playbook](26-playbook-containers-k8s.md) (§7) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) (multi-server) · KodeKloud: *Docker Certified Associate* — Docker Swarm, Swarm Services and Placement ([section introduction](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction)) · [Docker docs: Swarm networking](https://docs.docker.com/engine/swarm/networking/)

**Community threads:** [moby/moby #33183: service logs stop showing logs from other nodes](https://github.com/moby/moby/issues/33183) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+%22no+suitable+node%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+service+pending+no+suitable+node&restrict_sr=1)

### 8.2 Works with compose up, fails with stack deploy

> **Seen as:** `Ignoring unsupported options: build, restart`; `container_name: Setting the container name is not supported.`; variables that were set in .env arrive empty; Traefik ignores the service and returns 404; a bind mount fails on another node · **Where:** taking a working compose.yaml to `docker stack deploy` or to Dokploy's stack mode · **Level:** [L2 · Mid-level] · **How common:** moby #29133 ("stack deploy doesn't load .env", 118 comments) and moby #31101 (extends in stack deploy, 173 reactions)

**Why it happens:** `docker stack deploy` implements the part of Compose that makes sense for a cluster. It cannot build (images must already be in a registry), ignores `container_name`, `restart` and `depends_on`, and uses `deploy:` for replicas, restart policy, resources and placement. It does not read .env by itself. Labels at the service's top level go onto containers, while Traefik's Swarm provider reads the *service* labels under `deploy.labels`. A bind path must exist on whichever node the task lands on.

**Diagnose:**

```bash
docker stack deploy -c compose.yml shop 2>&1 | head -2
docker stack config -c compose.yml | grep -n 'DB_HOST'
docker service inspect shop_api --format '{{json .Spec.Labels}}' | jq 'keys | length'
docker service inspect shop_api --format '{{json .Spec.TaskTemplate.ContainerSpec.Labels}}' | jq -r 'keys[]' | head -2
```

```text
Ignoring unsupported options: build, restart
container_name: Setting the container name is not supported.
14:      DB_HOST: ""
0
traefik.enable
traefik.http.routers.shop.rule
```

**What the output tells you:** build and restart were dropped, DB_HOST rendered empty because nothing loaded .env, and the service itself has zero labels while the Traefik labels sit on the containers. Traefik's Swarm provider therefore sees no router, which is the 404.

**Fix:**

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.3      # built and pushed by CI; no build: here
    environment:
      DB_HOST: ${DB_HOST:?set DB_HOST}             # fail loudly instead of deploying an empty value
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      labels:                                      # service labels: what Traefik's Swarm provider reads
        traefik.enable: "true"
        traefik.http.routers.shop.rule: Host(`shop.example.com`)
        traefik.http.services.shop.loadbalancer.server.port: "3000"
```

```bash
set -a; . ./.env; set +a                 # stack deploy does not read .env by itself
docker stack deploy --with-registry-auth -c compose.yml shop
```

**Why this fix works:** each change maps a Compose habit onto the Swarm equivalent: images from a registry, `deploy.restart_policy` instead of `restart`, service labels for Traefik, variables exported into the shell that runs the deploy. `${VAR:?}` turns a silent empty value into a failed deploy, which is what you want. Don't keep two diverging files by hand; derive the Swarm file and validate it with `docker stack config`.

**Prevent it:** a separate compose.swarm.yml checked by `docker stack config` in CI, and the rule that every service behind Traefik in Swarm carries `deploy.labels` with an explicit port.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 7.3 (Swarm labels ignored) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · [Swarm for Dokploy](30-learn-docker.md) (§14) · KodeKloud: *Docker Certified Associate* — [Docker Stack](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Stack/page) · [Docker docs](https://docs.docker.com/)

**Community threads:** [moby/moby #29133: stack deploy doesn't load .env](https://github.com/moby/moby/issues/29133) · [moby/moby #31101: extends in stack deploy](https://github.com/moby/moby/issues/31101) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+stack+deploy+%22Ignoring+unsupported+options%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=stack+deploy+env+file+variables&restrict_sr=1)

### 8.3 Overlay: tasks on other nodes unreachable

> **Seen as:** a service reaches tasks on its own node but times out to tasks on another; Traefik returns 502 or 504 for every second request; `docker service ps` shows everything Running; DNS returns the service VIP · **Where:** clusters spread over VLANs or sites, nodes with a public and a private interface, VMware hosts, cloud instances with security groups · **Level:** [L2 · Mid-level] · **How common:** moby #32195 ("occasional network connection problems between nodes", 250 comments), #30134 (DNS inside overlays, 74) and #26106 (VIP not routing, 62)

**Why it happens:** an overlay needs three flows between nodes: 2377/tcp to managers (control), 7946/tcp and udp (gossip about who runs what), and 4789/udp (VXLAN, the actual container traffic). If gossip works but VXLAN is blocked, names resolve and tasks look healthy while traffic to other nodes disappears. A node with two interfaces may advertise the wrong one, so VXLAN goes to an address the other side cannot reach. Some virtual NICs mishandle VXLAN checksum offload and drop the packets, and VMware NSX uses UDP 4789 itself; the data port can only be changed at `swarm init`. Overlay MTU is entry 4.7.

**Diagnose:**

```bash
docker node inspect dokploy-2 --format '{{.Status.Addr}}'
sudo ufw status | grep -cE '2377|7946|4789'
# On dokploy-2, while a container on dokploy-1 calls a task there: do VXLAN packets arrive?
sudo tcpdump -ni ens18 -c 5 udp port 4789
```

```text
192.0.2.20
0
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on ens18, link-type EN10MB (Ethernet), snapshot length 262144 bytes
^C
0 packets captured
```

**What the output tells you:** dokploy-2 joined advertising its public address 192.0.2.20, so dokploy-1 sends VXLAN to the public IP, where the provider's firewall drops it; UFW has no Swarm rules either, and not a single VXLAN packet arrives on the private interface.

**Fix:**

```bash
# Swarm ports, only between the nodes' private addresses
for p in 2377/tcp 7946/tcp 7946/udp 4789/udp; do
  sudo ufw allow from 10.10.0.0/24 to any port "${p%/*}" proto "${p#*/}" comment "swarm $p"
done
# Rejoin the worker on its private address
docker swarm leave                                    # on dokploy-2
docker swarm join --advertise-addr 10.10.0.20 --data-path-addr 10.10.0.20 --token SWMTKN-1-WORKERTOKEN 10.10.0.10:2377
docker node ls                                        # on the manager: remove the old, Down entry by ID
docker node rm OLD_NODE_ID
```

<div class="env" data-env="onprem" markdown="1">

**On-premise:** open the Swarm ports on every firewall between the node VLANs, not only in UFW. On VMware, if VXLAN packets arrive but are dropped, turn off TX checksum offload on the underlay NIC (`sudo ethtool -K ens192 tx-checksum-ip-generic off`, persisted in netplan or a systemd unit); where NSX already uses UDP 4789, build the swarm with `docker swarm init --data-path-port 4790`.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** give the nodes one security group with a self-referencing rule for 2377/tcp, 7946/tcp, 7946/udp and 4789/udp, and always advertise private addresses. Encrypted overlays (`--opt encrypted`) also need IP protocol 50 (ESP) allowed between the nodes.

</div>

**Why this fix works:** with the three flows open between private addresses, gossip and data use the same reachable path. Rejoining is the clean way to change a node's advertised address. Never open 2377, 7946 or 4789 to the internet: VXLAN has no authentication, so anyone who can reach 4789 can inject packets into your overlays.

**Prevent it:** a Swarm port matrix in your firewall code, join commands that always pass `--advertise-addr`, and a synthetic check that calls a task on every node across the overlay.

**Next step:** [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 5.3 (Swarm init fails: advertise address) · [Swarm for Dokploy](30-learn-docker.md) (§14) · KodeKloud: *Docker Certified Associate* — [Docker Overlay Network](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page) and [Swarm Service Discovery](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Swarm-Service-Discovery/page) · [Docker docs: Swarm networking](https://docs.docker.com/engine/swarm/networking/)

**Community threads:** [moby/moby #32195: network problems between Swarm nodes](https://github.com/moby/moby/issues/32195) · [moby/moby #30134: DNS resolver inside overlays](https://github.com/moby/moby/issues/30134) · [moby/moby #26106: overlay not routing via the VIP](https://github.com/moby/moby/issues/26106) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+overlay+containers+different+nodes+cannot+communicate) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+overlay+4789+nodes&restrict_sr=1)

### 8.4 Routing mesh: real client IP lost

> **Seen as:** Traefik's access log and the apps show every client as 10.0.0.2 or another ingress address; IP allow-lists, rate limits, CrowdSec and Fail2ban all see one address; a stack port written as `127.0.0.1:8080:80` still listens on every interface · **Where:** a reverse proxy deployed as a Swarm service with normal published ports · **Level:** [L2 · Mid-level] · **How common:** moby #25526 ("unable to retrieve user's IP address in docker swarm mode") is the most-discussed Swarm issue of all, open since 2016 with 365 comments; #32299 (127.0.0.1 ports exposed, 69) and #35082 (ingress performance, 146) sit next to it

**Why it happens:** a port published in the default *ingress* mode is opened on every node, and IPVS forwards each connection to some task, rewriting the source address to the node's address on the ingress network. The proxy behind it never sees the real client. Ingress mode also ignores a host IP in the port specification. Dokploy's own Traefik runs as a standalone container that publishes ports directly, which is why it keeps client IPs; a Traefik you deploy as a stack with plain `ports:` does not.

**Diagnose:**

```bash
docker service inspect traefik_traefik --format '{{range .Endpoint.Spec.Ports}}{{.PublishedPort}}/{{.PublishMode}} {{end}}'
docker service logs --tail 200 traefik_traefik 2>&1 | grep -oE '"ClientHost":"[^"]+"' | sort | uniq -c
```

```text
80/ingress 443/ingress 
    200 "ClientHost":"10.0.0.2"
```

**What the output tells you:** both ports use ingress mode, and the last 200 requests all came "from" 10.0.0.2, an ingress address. Nothing in Traefik's configuration can recover what the mesh already rewrote.

**Fix:**

```yaml
services:
  traefik:
    image: traefik:v3.6
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 443
        published: 443
        protocol: tcp
        mode: host
    deploy:
      mode: global                       # one Traefik per edge node
      placement:
        constraints: [node.labels.edge == true]
```

**Why this fix works:** host mode publishes the port on the node where the task runs, like `docker run -p`, with no SNAT, so Traefik sees the real source and passes it on in X-Forwarded-For. The trade-off: only one task per node can own the port, and spreading traffic across edge nodes moves to DNS, keepalived or an external load balancer. For ports that must stay local, don't publish them in Swarm at all; use host mode and the firewall, or a non-published overlay service.

**Prevent it:** the edge proxy always runs in host mode on labelled edge nodes, and Traefik trusts forwarded headers only from your own load balancers.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 8.3 (real client IP lost) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md), entry 6.9 (apps log the wrong client IP) · [Wazuh & security tools](48-wazuh-and-security-tools.md) (CrowdSec and Fail2ban need real IPs) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Swarm Service Discovery) · [Docker docs: Swarm networking](https://docs.docker.com/engine/swarm/networking/)

**Community threads:** [moby/moby #25526: user's IP address in swarm mode](https://github.com/moby/moby/issues/25526) · [moby/moby #32299: ports on 127.0.0.1 exposed to 0.0.0.0](https://github.com/moby/moby/issues/32299) · [moby/moby #35082: ingress performance with parallel requests](https://github.com/moby/moby/issues/35082) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+real+client+ip+mode+host) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=swarm+client+ip+ingress&restrict_sr=1)

### 8.5 Rolling update stuck or no rollback

> **Seen as:** `docker service update` stops at `overall progress: 1 out of 2 tasks`; `UpdateStatus` says `update paused due to failure or early termination of task`; every deploy causes 10 to 30 seconds of 502s; a bad image stays half-deployed · **Where:** Swarm services and Dokploy apps without healthchecks or update settings · **Level:** [L2 · Mid-level] · **How common:** moby #30321 ("zero-downtime deployments with rolling upgrades", 124 comments)

**Why it happens:** Swarm's defaults are cautious and slow to notice failure: one task at a time, stop the old task before starting the new one (stop-first), watch each new task for only 5 seconds, and *pause* on failure rather than roll back. Without a healthcheck, a task counts as running the moment its process starts, so traffic reaches an app that is still booting (502s) and an app that crashes after 20 seconds passes the monitor window. With one replica and stop-first, every deploy is a short outage.

**Diagnose:**

```bash
docker service inspect shop_api --format '{{json .UpdateStatus}}' | jq -c .
docker service inspect shop_api --pretty | sed -n '/UpdateConfig/,/RollbackConfig/p'
docker service ps shop_api --format '{{.Name}} {{.Image}} {{.CurrentState}} {{.Error}}' | head -3
docker image inspect -f '{{json .Config.Healthcheck}}' harbor.example.com/shop/api:1.4.3
```

```text
{"State":"paused","StartedAt":"2026-10-03T11:02:10.118Z","Message":"update paused due to failure or early termination of task 7xq2m9k1"}
UpdateConfig:
 Parallelism:	1
 On failure:	pause
 Monitoring Period: 5s
 Max failure ratio: 0
 Update order:      stop-first
RollbackConfig:
shop_api.1 harbor.example.com/shop/api:1.4.3 Failed 40 seconds ago task: non-zero exit (1)
shop_api.2 harbor.example.com/shop/api:1.4.2 Running 2 hours ago
null
```

**What the output tells you:** the new version crashed, Swarm paused with one task on 1.4.3 (failed) and one on 1.4.2, and nothing will roll back by itself. The image has no healthcheck, so even a successful update would have sent traffic to booting tasks.

**Fix:**

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.4.3
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/healthz"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 20s
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
        failure_action: rollback
        monitor: 30s
      rollback_config:
        parallelism: 1
        order: start-first
```

```bash
docker service rollback shop_api        # for the update that is paused right now
```

**Why this fix works:** start-first brings the new task up before the old one stops, the healthcheck keeps traffic away until the app answers, the 30-second monitor catches late crashes, and `failure_action: rollback` returns to the last good spec without a human. The exception is a single-writer stateful service (a database, Prometheus) that must use stop-first, because two copies would fight over the same data.

**Prevent it:** a healthcheck in every image, these update settings in the deploy template, and a deploy that is considered done only when `UpdateStatus` says completed.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [Observability problems](49-observability-stack-problems.md), entry 5.2 (stop-first for stateful services) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Scaling, Rolling Updates and Rollbacks) · [Docker docs](https://docs.docker.com/)

**Community threads:** [moby/moby #30321: zero-downtime deployments with rolling upgrades](https://github.com/moby/moby/issues/30321) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+rolling+update+zero+downtime+start-first) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+update+paused+rollback&restrict_sr=1)

### 8.6 Secrets and configs can't be updated

> **Seen as:** `rpc error: code = InvalidArgument desc = only updates to Labels are allowed` when a stack redeploys with a changed secret or config file; `secret 'db_password' is in use by the following service: shop_api` on `docker secret rm` · **Where:** rotating database passwords, renewing TLS certificates or changing nginx configs in Swarm stacks · **Level:** [L2 · Mid-level] · **How common:** moby #13490 (secrets best practices and roadmap, 223 reactions); every team that rotates a secret for the first time meets it

**Why it happens:** Swarm secrets and configs are immutable by design: they are written into the encrypted Raft log and handed to tasks as read-only files, and the only thing you may change afterwards is their labels. Redeploying a stack whose secret file changed under the same name is therefore refused, and a secret in use cannot be removed.

**Diagnose:**

```bash
docker secret ls --format '{{.Name}}\t{{.CreatedAt}}'
docker service inspect shop_api --format '{{range .Spec.TaskTemplate.ContainerSpec.Secrets}}{{.SecretName}} as {{.File.Name}} {{end}}'
```

```text
db_password	6 months ago
db_password as db_password 
```

**What the output tells you:** the service uses a secret created six months ago under a fixed name (the CreatedAt field of `docker secret ls` is printed as a relative age), so any change to its content needs a new secret object, not an update.

**Fix:**

```bash
# Rotate: new versioned secret, swapped in under the same file name, old one removed
printf '%s' "$NEW_DB_PASSWORD" | docker secret create db_password_v2 -
docker service update --secret-rm db_password \
  --secret-add source=db_password_v2,target=db_password shop_api
docker secret rm db_password
```

```yaml
# In stacks: a versioned name, so a rotation is just a new version number
secrets:
  db_password:
    name: shop_db_password_${DB_PASSWORD_VERSION:?}
    file: ./secrets/db_password.txt
```

**Why this fix works:** `target=` keeps the path /run/secrets/db_password stable, so the application does not change; the service update rolls tasks one by one (with the healthcheck from entry 8.5) and the old object can then go. Order matters on the database side: let the database accept the new password before the swap, or have the app retry. Don't move secrets back into environment variables to "make rotation easier"; they leak into `docker inspect` and crash dumps.

**Prevent it:** versioned secret and config names from day one, a written rotation runbook, and dynamic secrets from Vault or OpenBao where rotation is frequent (see [Wazuh & security tools](48-wazuh-and-security-tools.md)).

**Next step:** [Security & DevSecOps](37-learn-security-devsecops.md) (secrets management) · entry 3.2 (Compose secrets) · KodeKloud: *Docker Certified Associate* — Docker Swarm (Docker Config Objects) · [Docker docs](https://docs.docker.com/)

**Community threads:** [moby/moby #13490: secrets best practices](https://github.com/moby/moby/issues/13490) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+secret+%22only+updates+to+Labels+are+allowed%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+secret+rotation&restrict_sr=1)

### 8.7 Lost quorum: the swarm has no leader

> **Seen as:** `The swarm does not have a leader. It's possible that too few managers are online. Make sure more than half of the managers are online.`; `docker node ls` fails; running services keep serving but nothing can be deployed or changed, and Dokploy deploys hang · **Where:** clusters with two managers, a manager VM deleted without demotion, a manager whose IP changed, a manager restored from an old snapshot · **Level:** [L3 · Senior] · **How common:** moby #25432 ("corrupted manager not able to leave a cluster", 78 comments); a classic of small Swarm clusters

**Why it happens:** managers agree through Raft, which needs a majority (more than half) of managers online. With two managers the majority is two, so losing either one stops all changes: two managers are strictly worse than one. Deleting a manager VM without `docker node demote`, changing its IP, or restoring one manager from an old snapshot all remove a vote. Workloads keep running because tasks do not need the managers, which hides the problem until the next deploy.

**Diagnose:**

```bash
docker info --format '{{.Swarm.LocalNodeState}} managers={{.Swarm.Managers}} nodes={{.Swarm.Nodes}}'
docker node ls 2>&1 | tail -1
sudo journalctl -u docker --since '30 min ago' | grep -iE 'raft|leader' | tail -2
```

```text
active managers=2 nodes=3
Error response from daemon: rpc error: code = Unknown desc = The swarm does not have a leader. It's possible that too few managers are online. Make sure more than half of the managers are online.
level=error msg="error sending message to peer" error="rpc error: code = Unavailable desc = connection error: dial tcp 10.10.0.20:2377: connect: no route to host" module=raft
```

**What the output tells you:** this cluster had two managers and the second (10.10.0.20) is unreachable, so one of two votes is not a majority. If that VM can come back, bringing it back is the safest fix; if it is gone, the survivor must form a new cluster from its own state.

**Fix:**

```bash
# 1. The lost manager can return (VM, network, IP): bring it back, quorum returns, nothing is lost
# 2. It is gone for good: on the surviving manager, copy the state first, then rebuild membership
sudo systemctl stop docker && sudo tar czf /root/swarm-backup-$(date +%F).tgz -C /var/lib/docker swarm && sudo systemctl start docker
docker swarm init --force-new-cluster --advertise-addr 10.10.0.10
docker node ls                                   # services, networks, secrets and workers are kept
docker node rm --force OLD_MANAGER_ID
# 3. Back to an odd number of managers
docker node promote dokploy-3
```

**Why this fix works:** `--force-new-cluster` tells the surviving manager to become a cluster of one using its own Raft log, so the desired state of every service, network and secret survives and workers reconnect. Run it on exactly one manager; running it on two creates two clusters that each believe they are the truth. If the swarm is autolocked, you need the unlock key before any of this.

**Prevent it:** one manager for small Dokploy setups or three (five for large clusters), never two; static manager addresses; `docker node demote` before removing a manager; a regular copy of /var/lib/docker/swarm taken with Docker stopped on a manager (plus the unlock key), and a restore drill twice a year.

**Next step:** [Senior architecture](39-learn-senior-architecture.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) (backups and multi-server) · [Career ladder](40-career-ladder.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm (High Availability/Quorum, Disaster Recovery – Docker Swarm) · [Docker docs](https://docs.docker.com/)

**Community threads:** [moby/moby #25432: corrupted manager not able to leave a cluster](https://github.com/moby/moby/issues/25432) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22swarm+does+not+have+a+leader%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=swarm+lost+quorum+force-new-cluster&restrict_sr=1)

---

## 9. Harbor operations

Harbor is where your images live, so when it is down nothing deploys, and when its disk fills nothing builds. These entries follow a Harbor installed with the offline installer (Docker Compose) on harbor-1, the common on-prem setup; the same ideas apply to the Helm chart on Kubernetes.

### 9.1 Harbor down after a reboot or upgrade

> **Seen as:** after a reboot the UI returns 502; `harbor-core` and `harbor-jobservice` show `Exited (128)` with `failed to initialize logging driver: dial tcp 127.0.0.1:1514: connect: connection refused`; nginx logs `host not found in upstream "core:8080"`; edits to harbor.yml change nothing; after an upgrade the database migration fails · **Where:** Harbor from the offline installer on a VM, after patch-night reboots, configuration changes and version jumps · **Level:** [L2 · Mid-level] · **How common:** goharbor/harbor #7008 ("containers fail to start on docker startup", 42 comments) and #13589 (upgrade from 1.10 to 2.1, multiple issues, 50 comments)

**Why it happens:** the installer's Compose file sends every container's logs through the syslog driver to harbor-log on 127.0.0.1:1514. After a reboot Docker starts containers by restart policy, not in dependency order, so containers that come up before harbor-log fail to initialise logging and stay down, and nginx then cannot resolve the missing core. harbor.yml is not read at runtime: `./prepare` turns it into the files under ./common/config, so an edit without prepare does nothing. Upgrades are supported only from recent minor versions with a migration step, so skipping several versions or forgetting the migration breaks the database schema.

**Diagnose:**

```bash
cd /opt/harbor && docker compose ps -a --format 'table {{.Name}}\t{{.Status}}'    # -a: without it, exited containers are not listed
docker inspect harbor-core --format '{{.State.Status}} {{.State.Error}}'
docker logs --tail 2 nginx 2>&1
```

```text
NAME                STATUS
harbor-core         Exited (128) 2 minutes ago
harbor-db           Up 2 minutes (healthy)
harbor-jobservice   Exited (128) 2 minutes ago
harbor-log          Up 2 minutes (healthy)
harbor-portal       Up 2 minutes (healthy)
nginx               Restarting (1) 5 seconds ago
redis               Up 2 minutes (healthy)
registry            Up 2 minutes (healthy)
exited failed to initialize logging driver: dial tcp 127.0.0.1:1514: connect: connection refused
nginx: [emerg] host not found in upstream "core:8080" in /etc/nginx/nginx.conf:22
```

**What the output tells you:** harbor-log is up now, but core and jobservice tried to start before it existed and gave up; nginx restarts because core is missing. Nothing is corrupted: the start order was wrong.

**Fix:**

```bash
cd /opt/harbor && docker compose up -d          # harbor-log is up now: start the rest
# Configuration changes: always regenerate, then recreate
docker compose down && sudo ./prepare && docker compose up -d     # add --with-trivy if you use the scanner
# Upgrades: back up first, migrate harbor.yml with the new version's prepare image, then install
sudo tar czf /root/harbor-$(date +%F).tgz /opt/harbor/harbor.yml /data/database /data/secret
docker run -it --rm -v /:/hostfs goharbor/prepare:v2.14.0 migrate -i /opt/harbor/harbor.yml
```

```ini
# /etc/systemd/system/harbor.service: start Harbor as one unit after Docker, so order is handled for you
[Unit]
Description=Harbor registry
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/harbor
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```

**Why this fix works:** `docker compose up -d` respects the `depends_on` order in Harbor's Compose file, which Docker's restart policies do not, so a unit that runs it at boot starts harbor-log first every time (`sudo systemctl enable harbor` after creating it). `prepare` is the only path from harbor.yml to running config. The migrate step rewrites harbor.yml for the new version; the database schema is migrated when the new core starts. Never jump several minor versions at once, and never upgrade without the database and secret key backup.

**Prevent it:** the systemd unit, a reboot test after every Harbor change, upgrades rehearsed on a clone of harbor-1, and backups of the database, /data/secret and the registry storage (see [Databases, storage & backups](51-problems-databases-storage-backup.md)).

**Next step:** [Registries and Harbor](30-learn-docker.md) (§11) · [Services & systemd reference](07-services-systemd.md) · KodeKloud has no Harbor course; read the community post [*Setting up your own Container Registry with Harbor*](https://kodekloud.com/community/t/setting-up-your-own-container-registry-with-harbor/275367) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [goharbor/harbor #7008: containers fail to start on docker startup](https://github.com/goharbor/harbor/issues/7008) · [goharbor/harbor #13589: upgrade 1.10.3 to 2.1.1, multiple issues](https://github.com/goharbor/harbor/issues/13589) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+after+reboot+%22failed+to+initialize+logging+driver%22) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=harbor+upgrade+failed&restrict_sr=1)

### 9.2 Disk still full after deleting tags

> **Seen as:** /data at 96% although old repositories were deleted in the UI; pushes refused with `adding 312.5 MiB of storage resource, which when updated to current usage of 99.8 GiB will exceed the configured upper limit of 100.0 GiB`; a garbage collection that runs for hours · **Where:** long-running Harbor instances storing every CI build, projects with quotas, registry storage on local disk or S3-compatible storage · **Level:** [L2 · Mid-level] · **How common:** goharbor/harbor #15445 (GC deletes used blobs, 43 comments), #12948 (GC performance on S3, 52), and recent discussions #22734 (how to accelerate GC) and #20309 (orphaned files after GC)

**Why it happens:** deleting a tag or artifact removes references, not data; the layers stay on disk until garbage collection removes blobs that no manifest references any more. GC never touches blobs uploaded in the last two hours (they may belong to a push in progress), and untagged artifacts, such as the previous image behind an overwritten `latest`, stay referenced unless you ask GC to delete them. Quotas count per project and drop when artifacts are deleted, while disk space returns only after GC, so the two numbers disagree. Since Harbor 2.1, GC runs without putting the registry into read-only mode.

**Diagnose:**

```bash
df -h /data
sudo du -sh /data/registry /data/database 2>/dev/null
curl -s -u "admin:$HARBOR_ADMIN_PASS" "https://harbor.example.com/api/v2.0/system/gc?page_size=3" \
  | jq -r '.[] | "\(.creation_time) \(.job_status) \(.job_parameters)"'
curl -s -u "admin:$HARBOR_ADMIN_PASS" "https://harbor.example.com/api/v2.0/quotas?reference=project" \
  | jq -r '.[] | "\(.ref.name) used=\(.used.storage) hard=\(.hard.storage)"' | head -2
```

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1       492G  471G   21G  96% /data
466G	/data/registry
3.1G	/data/database
team-a used=107160723456 hard=107374182400
shop used=48318382080 hard=-1
```

**What the output tells you:** the GC history is empty, so garbage collection has never run: every layer ever pushed is still on disk. team-a is a few hundred megabytes below its 100 GiB quota, which explains the refused push; shop has no quota at all.

**Fix:**

```bash
# 1. Retention first (UI: Projects > team-a > Policy > Tag Retention):
#    keep the 10 most recently pushed artifacts per repository, plus anything tagged release-*
# 2. GC dry run: an estimate of what would be freed, nothing deleted
curl -s -u "admin:$HARBOR_ADMIN_PASS" -X POST -H 'Content-Type: application/json' \
  https://harbor.example.com/api/v2.0/system/gc/schedule \
  -d '{"schedule":{"type":"Manual"},"parameters":{"delete_untagged":true,"dry_run":true,"workers":2}}'
# 3. The real run: the same call with "dry_run": false, in a quiet hour;
#    then schedule it weekly (UI: Administration > Clean Up > Garbage Collection)
```

**Why this fix works:** retention decides which artifacts are worth keeping, GC turns that decision into free disk, and the dry run shows the size of the win before anything is deleted. Never delete files under /data/registry by hand or run the registry's own garbage-collect binary while Harbor runs: Harbor's database and the storage would disagree, and pulls fail with missing blobs. Raising the quota without retention only postpones the next refusal.

**Prevent it:** a retention policy on every project when it is created (short for build-cache repositories, see entry 6.3), weekly scheduled GC, quotas per team, and a disk alert on /data at 80%.

**Next step:** entry 2.1 (the same problem on Docker hosts) · [Databases, storage & backups](51-problems-databases-storage-backup.md) (object storage) · [Registries and Harbor](30-learn-docker.md) (§11) · [Harbor docs: garbage collection](https://goharbor.io/docs/2.13.0/administration/garbage-collection/)

**Community threads:** [goharbor/harbor #15445: GC deletes used blobs](https://github.com/goharbor/harbor/issues/15445) · [goharbor/harbor discussion #22734: accelerating GC](https://github.com/goharbor/harbor/discussions/22734) · [goharbor/harbor discussion #20309: orphaned files after GC](https://github.com/goharbor/harbor/discussions/20309) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+garbage+collection+disk+not+freed) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=harbor+registry+disk+garbage+collection&restrict_sr=1)

### 9.3 Robot accounts: robot$ names and 401s

> **Seen as:** `unauthorized: authentication required` from a CI job whose robot token works in your terminal; harbor-core logging `failed to verify secret, username: robot$gitlab, error: failed to get oidc user info` after OIDC was enabled; a pipeline that worked until the robot quietly expired · **Where:** GitLab CI, Jenkins and Dokploy registry settings using Harbor robot accounts; Harbor in OIDC authentication mode · **Level:** [L2 · Mid-level] · **How common:** goharbor/harbor #15253 (OIDC breaks robot accounts, 73 comments, the most-commented Harbor issue), #9553 (no $ in robot names, 24 reactions) and #8744 (configurable prefix)

**Why it happens:** Harbor robot names start with `robot$` and project robots look like `robot$team-a+ci`. The dollar sign is the problem: shells and CI systems expand `$team` as a variable, so the registry receives `robot-a+ci` or `robot`. GitLab expands variable references inside variable values unless that is switched off for the variable. Robots also expire (the default lifetime is set by the administrator) and carry permissions per project, so a pull-only robot cannot push. Some older Harbor versions mishandled robot authentication when OIDC was enabled; current versions handle it, which is one more reason to stay within supported releases.

**Diagnose:**

```bash
# Inside the CI job (masked values stay hidden): what user string reaches docker login?
echo "user=[${HARBOR_USER}] length=${#HARBOR_USER}"
# From a workstation: do the same credentials get a push token for the project?
curl -s -o /dev/null -w '%{http_code}\n' -u 'robot$team-a+ci:'"$HARBOR_ROBOT_TOKEN" \
  "https://harbor.example.com/service/token?service=harbor-registry&scope=repository:team-a/api:push,pull"
```

```text
user=[robot-a+ci] length=10
200
```

**What the output tells you:** the credentials are valid (200 from the token service), but inside CI the user name lost `$team`, which was expanded as an empty variable. The registry is rejecting a user that does not exist.

**Fix:**

```yaml
# .gitlab-ci.yml: the user comes from a variable whose value is NOT expanded
#   Settings > CI/CD > Variables: HARBOR_USER = robot$team-a+ci, "Expand variable reference" unchecked,
#   HARBOR_ROBOT_TOKEN masked and protected
push-image:
  stage: publish
  script:
    - echo "$HARBOR_ROBOT_TOKEN" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin
    - docker push "harbor.example.com/team-a/api:$CI_COMMIT_SHORT_SHA"
```

**Why this fix works:** a literal variable keeps the dollar sign intact, double quotes around `$HARBOR_USER` stop the shell from splitting or re-expanding it, and `--password-stdin` keeps the token out of the process list. In shells, write robot names in single quotes. If a robot expired or lacks push, refresh its secret or widen its permissions in the project rather than switching CI to an admin account.

**Prevent it:** one robot per project and purpose with least privilege, an inventory of robots with owners and expiry dates, a calendar reminder before expiry, and Harbor kept on a supported version.

**Next step:** entry 5.2 (push denied) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) (GitLab variables and Harbor pushes) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — [Docker Push](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [goharbor/harbor #15253: OIDC breaks robot accounts](https://github.com/goharbor/harbor/issues/15253) · [goharbor/harbor #9553: robot names with $](https://github.com/goharbor/harbor/issues/9553) · [goharbor/harbor #8744: configurable robot prefix](https://github.com/goharbor/harbor/issues/8744) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+robot+account+%22unauthorized%22+gitlab) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=harbor+robot+account&restrict_sr=1)

### 9.4 Harbor behind Traefik or Nginx

> **Seen as:** the UI login loops or shows `CSRF token invalid`; `docker login` fails while the UI works, and the registry's `www-authenticate` header points at `http://` or an internal host name; large pushes break off after a minute; only one of two host names works · **Where:** Harbor on HTTP inside the LAN with TLS terminated at Traefik or Nginx, the typical setup next to Dokploy · **Level:** [L2 · Mid-level] · **How common:** goharbor/harbor #12676 (CSRF token invalid, 60 comments), #3114 (Harbor on HTTP behind an HTTPS proxy) and #8243 (multiple host names, 43 reactions)

**Why it happens:** Harbor builds redirects, cookie settings and the registry's token-service address (the "realm" that Docker clients call to get a token) from `external_url`, or from `hostname` and its own protocol when external_url is unset. Behind a TLS-terminating proxy, a Harbor that thinks it is plain HTTP hands clients an `http://` realm and non-secure cookies, which produces login loops, CSRF errors and failed `docker login`. Harbor supports one canonical host name. Big layer uploads also need the proxy to allow long requests and large bodies.

**Diagnose:**

```bash
curl -sI https://harbor.example.com/v2/ | grep -i www-authenticate
grep -nE '^(hostname|external_url|http|https):' /opt/harbor/harbor.yml
```

```text
www-authenticate: Bearer realm="http://harbor.example.com/service/token",service="harbor-registry"
5:hostname: harbor.example.com
10:http:
```

**What the output tells you:** the realm is `http://`, so clients that came in over HTTPS are told to fetch tokens over plain HTTP, and `external_url` is not set at all. This is the whole login problem.

**Fix:**

```yaml
# /opt/harbor/harbor.yml: TLS ends at Traefik; Harbor listens on HTTP 8080, reachable only from the proxy
hostname: harbor.example.com
http:
  port: 8080
external_url: https://harbor.example.com
```

```bash
cd /opt/harbor && docker compose down && sudo ./prepare && docker compose up -d
curl -sI https://harbor.example.com/v2/ | grep -i www-authenticate     # the realm must now start with https://
```

**Why this fix works:** with `external_url` set, Harbor generates every URL and cookie for the address users actually use. Traefik passes X-Forwarded-Proto by default; on Nginx, set it yourself. Long pushes need the proxy's read timeout raised on the entry point that serves Harbor (see the Traefik module, entry 15.1). Firewall port 8080 on harbor-1 so only the proxy reaches it, and give internal clients the same name through split DNS rather than a second host name.

**Prevent it:** one canonical URL documented for everyone, and a post-change smoke test through the proxy: `docker login`, push of a large test image, pull.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 15.1 (docker push and big uploads through the proxy) · [Learn web servers & proxies](29-learn-webservers-proxies.md) · [Harbor: configure HTTPS](https://goharbor.io/docs/2.15.0/install-config/configure-https/)

**Community threads:** [goharbor/harbor #12676: CSRF token invalid](https://github.com/goharbor/harbor/issues/12676) · [goharbor/harbor #3114: Harbor on HTTP behind an HTTPS proxy](https://github.com/goharbor/harbor/issues/3114) · [goharbor/harbor #8243: multiple host names](https://github.com/goharbor/harbor/issues/8243) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+behind+reverse+proxy+external_url+docker+login) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=harbor+traefik+reverse+proxy&restrict_sr=1)

### 9.5 Replication jobs fail or time out

> **Seen as:** a replication execution marked Failed with a few failed tasks out of many; task logs with `504 Gateway Time-out` on large blobs, `x509: certificate signed by unknown authority`, `unauthorized`, `toomanyrequests` or `invalid manifest`; a rule that "succeeds" with zero artifacts · **Where:** a DR copy of harbor-1 at a second site, replication into or out of cloud registries, rules that pull from Docker Hub · **Level:** [L3 · Senior] · **How common:** goharbor/harbor #8037 (504 in pull mode, 40 comments) and #18813 (invalid manifest breaks transfer and scanning, 40), plus recent discussions on active-active Harbor across data centres

**Why it happens:** replication is Harbor's jobservice copying artifacts between registry endpoints, so every layer of the stack can fail it: TLS trust between the two Harbors (each has its own trust store), credentials of the endpoint's robot on the destination (it needs push there), proxies in front of the remote side that time out on big blobs, rate limits when the source is Docker Hub, filters that match nothing, and very old images in Docker's schema 1 format, which current Harbor and Docker 28 or later no longer handle.

**Diagnose:**

```bash
curl -s -u "admin:$HARBOR_ADMIN_PASS" "https://harbor.example.com/api/v2.0/replication/executions?policy_id=3&page_size=3" \
  | jq -r '.[] | "\(.id) \(.status) total=\(.total) failed=\(.failed)"'
docker logs --since 6h harbor-jobservice 2>&1 | grep -iE 'error|failed' | tail -2
```

```text
118 Failed total=42 failed=3
2026-10-03T02:14:07Z [ERROR] [/pkg/reg/adapter/native/adapter.go:212]: failed to push blob sha256:9b1f6c...: http status code: 504
2026-10-03T02:14:07Z [ERROR] [/controller/replication/transfer/image/transfer.go:340]: failed to copy blob sha256:9b1f6c...
```

**What the output tells you:** 39 of 42 artifacts arrived, so endpoint, trust and credentials are fine; the three failures are large blobs that the proxy in front of the DR Harbor cut off with 504. This is a timeout problem, not a Harbor bug.

**Fix:**

```bash
# 1. Give the DR proxy room for big blobs (Traefik: entry 15.1 in module 43), or point the
#    endpoint at the DR Harbor's direct LAN or VPN address that has no proxy timeout
# 2. Re-run the execution; blobs that already arrived are skipped
curl -s -u "admin:$HARBOR_ADMIN_PASS" -X POST -H 'Content-Type: application/json' \
  https://harbor.example.com/api/v2.0/replication/executions -d '{"policy_id": 3}'
# 3. Other causes, by log line: x509 -> make Harbor trust the remote CA (do not untick "Verify Remote Cert");
#    unauthorized -> the endpoint robot needs push on the destination project;
#    toomanyrequests -> replicate from a proxy cache, not from Docker Hub; schema 1 -> rebuild the image
```

<div class="env" data-env="onprem" markdown="1">

**On-premise:** a second Harbor at the DR site with push-based replication of release projects is the usual pattern. Set a bandwidth limit on the rule so the nightly copy does not saturate the site link, and replicate only what you would deploy in a disaster (release tags), not every CI build.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** Harbor can replicate to Amazon ECR as an endpoint type, which gives cloud workloads a regional copy and a DR path that does not depend on your data centre; the robot is replaced by IAM credentials scoped to the target repositories.

</div>

**Why this fix works:** the logs name the failing layer, and each fix removes exactly that obstacle. Re-runs are cheap because blobs already present at the destination are not copied again. Turning off certificate verification on the endpoint "to make it work" would let anyone in the path swap the images you will deploy in a disaster.

**Prevent it:** alerts on failed replication executions (Harbor exposes Prometheus metrics), a quarterly DR drill that deploys an app from the DR Harbor, and backups of both Harbors' databases.

**Next step:** [Senior architecture](39-learn-senior-architecture.md) (DR design) · [Databases, storage & backups](51-problems-databases-storage-backup.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md), entry 15.1 · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [goharbor/harbor #8037: 504 when replication uses pull mode](https://github.com/goharbor/harbor/issues/8037) · [goharbor/harbor #18813: invalid manifest breaks replication](https://github.com/goharbor/harbor/issues/18813) · [goharbor/harbor discussion #24019: active-active Harbor across two data centres](https://github.com/goharbor/harbor/discussions/24019) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+replication+failed+504) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=harbor+replication+disaster+recovery&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises on the lab VMs (dokploy-1, dokploy-2, harbor-1, plus a third Swarm node for exercise 10). Snapshot first, break it exactly as described, fix it using only the entry, and write your five-line note: symptom, evidence, cause, fix, prevention.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Add `"hosts": ["unix:///var/run/docker.sock"]` to daemon.json and restart Docker | 10 min | 1.1 |
| 2 | Fresher | Run Apache on 443, then start a Traefik container publishing 443; free the port the way case 21 did | 15 min | 4.3 |
| 3 | Junior | Fill the disk with build cache and a chatty container without log limits; get back to 70% and make it stay there | 20 min | 2.1, 2.2 |
| 4 | Junior | Run an app that binds 127.0.0.1 and talks to PostgreSQL on the host; make both work without `network_mode: host` | 15 min | 4.1 |
| 5 | Junior | Split an app and its database into two Compose projects with no healthcheck; make startup reliable | 15 min | 4.2, 3.3 |
| 6 | Mid-level | Publish PostgreSQL 5432 on dokploy-1 with UFW active; prove it is open from outside, then close it for good | 20 min | 4.4 |
| 7 | Mid-level | Add a route for 172.20.0.0/16 via another gateway, start a project that lands in that range, then move Docker's pools | 25 min | 4.5 |
| 8 | Mid-level | Serve Harbor's leaf certificate without the intermediate and name certs.d with :443; make docker, containerd and a buildx builder pull | 30 min | 5.3, 6.2 |
| 9 | Senior | Rejoin dokploy-2 advertising a wrong address and block 4789; restore cross-node traffic, then make Traefik see real client IPs | 45 min | 8.3, 8.4 |
| 10 | Senior/Lead | Run two managers, delete one VM, recover with force-new-cluster, return to three managers and write the DR runbook; then reclaim Harbor disk with retention and GC | 60 min | 8.7, 9.2 |

Quick questions to answer from memory:

1. Why does a published container port ignore UFW, and where do your own rules belong?
2. Which four kinds of clients each need your private CA, and where does each one read it?
3. What do exit codes 137, 139 and 143 mean, and how do you tell an OOM kill from a stop timeout?
4. Why does deleting tags in Harbor not free disk space, and what does?
5. Why is a Swarm with two managers less available than one with a single manager?
6. What does `min-api-version` do after a Docker 29 upgrade, and why is it only a bridge?

---

## Where to go next

- [Learn Docker](30-learn-docker.md): the fundamentals behind every entry here, from overlay2 and namespaces to daemon.json and Swarm for Dokploy; [Docker command reference](14-docker-containers.md) for the commands at a glance.
- [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) and [Ports & inventory playbook](22-playbook-ports-inventory.md): the incident walks that use these problems as branches.
- [Traefik deep dive](43-traefik-and-reverse-proxies.md) and [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md): the proxy and the platform that sit on top of Docker and Swarm.
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md): runners, Docker-in-Docker and pipelines that push to Harbor; [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for the concepts.
- [Kubernetes problems](46-problems-kubernetes.md), [Learn Kubernetes](31-learn-kubernetes.md) and the [Kubernetes reference](15-kubernetes.md): containerd, image pulls on nodes and the same private CA from the cluster side.
- [Wazuh & security tools](48-wazuh-and-security-tools.md) and [Observability problems](49-observability-stack-problems.md): Trivy scans of Harbor, the docker group as a security risk, and container metrics and logs.
- [DevOps day to day](52-devops-day-to-day.md): how these problems arrive as tickets and pages, and [Practice arena](54-practice-arena.md) for more break-and-fix drills.
- [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) and [Career ladder](40-career-ladder.md): where Docker, Swarm and registry skills sit on the way from fresher to senior.
- Official docs: [Docker](https://docs.docker.com/) · [Docker Hub pull limits](https://docs.docker.com/docker-hub/usage/pulls/) · [Harbor](https://goharbor.io/docs/) · [Portainer](https://docs.portainer.io/) · [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/instance).
