# 22 — Who Owns This Port? Inventory, Logs & Dispatching Services

This module answers the question behind the Apache → Dokploy incident: *"Something already holds 443. What is it, which application is it, where are its logs, does anyone still need it, and how do I get it out of the way without breaking anything?"* It is general and reusable. It covers:

- how a port is "owned" on Linux, including the Docker and Kubernetes cases where `ss` simply doesn't show the owner
- the exact chain from a port number to the process, the unit, the config file and the logs
- a read-only inventory script
- an evidence-based way to decide what is still needed
- a ladder for stopping or moving services, from least to most invasive
- Windows and macOS equivalents, and five step-by-step scenarios.

It also turns the **L1 Operator exit test** from your ops ladder into a repeatable method: *given only a port number, name the process, the unit that starts it, its config file and the command that shows its logs, in five minutes.*

**Who it serves, fresher to senior.** A **Fresher** [L0] learns to read `ss` output and bind addresses. A **Junior** [L1] masters the port → PID → unit → config → logs chain and stops services safely. A **Mid-level** engineer [L2] finds invisible owners (NAT, Swarm, Kubernetes) and proves what is still used. A **Senior** [L3] plans the hand-over of 80/443 on a Dokploy or Kubernetes host. A **Lead** [L4] turns all of it into an inventory standard, change requests and prevention rules. Each section below carries a level tag such as [L2 · Mid], and section 1 has the full map.

Related modules: the full Apache/Dokploy story is in [21 — Case study: Apache holds 443](21-case-apache-443-dokploy.md). The command references are [Network](02-network.md), [Processes](05-processes.md), [Logs & journal](06-logs-journal.md), [systemd](07-services-systemd.md), [Docker](14-docker-containers.md) and [Kubernetes](15-kubernetes.md). The theory behind sockets and NAT is in [Learn: networking](28-learn-networking.md), and Apache, Nginx and Traefik are covered in depth in [Learn: web servers & proxies](29-learn-webservers-proxies.md).

> Everything here is read-only unless the section says otherwise. Section 10 ("Dispatching") and the "Fix & verify" blocks change the system on purpose and say so. Uppercase words such as PORT, PID, UNIT, CONTAINER, POD, NS, DOMAIN and HOST are placeholders. All sample outputs are illustrative (Ubuntu 24.04 unless noted) and use documentation IP ranges.

---

## 1. How to use this module

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 2) Note: this module, sections 2–4, then [Network reference](02-network.md) · 3) Video: KodeKloud *Linux Crash Course for Beginners* (141 min) — networking and services parts only ([YouTube](https://www.youtube.com/watch?v=a3ujwK65dgs)) · 4) Practice: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)), then the drills in section 19.

**Level:** the whole module spans [L0 · Fresher] to [L4 · Lead]. The table in "Who this module is for" below tells you where to start.

### Who this module is for

| Career stage | Ops Ladder | What to master in this module | Sections |
|---|---|---|---|
| Fresher (0–1 yr) | L0 Foundations | Read `ss -tulpn`; LISTEN vs ESTABLISHED; 127.0.0.1 vs 0.0.0.0; find one log file | 2 (first four topics), 3, 12 |
| Junior (1–2 yrs) | L1 Operator | The five-minute drill: port → PID → unit → config → logs; stop a service without it coming back; "Address already in use" | 4, 8, 10 (rungs 1–4), 13, 15 |
| Mid-level (2–4 yrs) | L2 Troubleshooter | Invisible owners (NAT, Swarm ingress, kube-proxy); "listening but unreachable"; URL → app proof; evidence of use | 5, 6, 9, 14, 16, 17 |
| Senior (4–7 yrs) | L3 Platform | Port ownership on Dokploy/Swarm and Kubernetes hosts; choosing between migration options; moving Apache behind Traefik | 6, 7, 9, 10 |
| Senior/Lead (5+ yrs) | L4 SRE | Change requests with rollback, inventory automation across hosts, prevention rules the team follows | 8 (extending), 10, every "Prevent it next time" |

Work through it in that order. A Junior can skip sections 7 and 16 at first. A Senior should still do the section 19 drills against the clock, because speed under pressure is what the stage tags measure.

### The five-minute drill at a glance

```
PORT ──ss / lsof──▶ PID ──/proc/PID/cgroup──▶ systemd UNIT │ CONTAINER │ POD │ user session
                     │
                     ├── readlink /proc/PID/exe ──▶ binary ──dpkg -S / rpm -qf──▶ package
                     ├── systemctl cat UNIT │ docker inspect │ app's "dump config" flag ──▶ config
                     └── lsof -p PID │ /proc/PID/fd/1 │ journalctl -u UNIT │ docker logs ──▶ logs
```

Read it left to right. Each arrow is one command, and every command is in section 4. If `ss` shows **no** owner, or the owner is `systemd`, `docker-proxy` or `dockerd`, read section 2 first. Those owners mean the port is held by a mechanism, and the application is somewhere else.

### Which section answers which question

| You need to… | Go to | First command |
|---|---|---|
| See everything listening on a Linux box | 3 | `sudo ss -tulpn` |
| Turn one port into process, unit, config and logs | 4 | `sudo ss -ltnp 'sport = :PORT'` |
| Know which Apache/Nginx vhost is which application | 5 | `sudo apache2ctl -S` |
| Map a port to a container, Compose project or Swarm service | 6 | `docker ps --format 'table {{.Names}}\t{{.Ports}}'` |
| Find who answers a Kubernetes NodePort | 7 | `kubectl get svc -A` |
| Produce a full inventory table in one go | 8 | `sudo ./port-inventory.sh` |
| Prove whether a service is still used | 9 | `sudo ss -Htn state established '( sport = :PORT )'` |
| Stop or move a service safely | 10 | the ladder table |
| Do the same on Windows or macOS | 11, 12 | `netstat -ano`, `sudo lsof -nP -iTCP -sTCP:LISTEN` |
| Fix a concrete problem step by step | 13–17 | scenario playbooks |

### Ground rules a senior engineer follows

1. **Look before you touch.** Nothing in sections 3–9 changes the system. Do the whole inventory before you stop anything. A stopped service can't show you its connections anymore.
2. **Prove the owner from two angles.** For example, `ss` plus `systemctl status PID`, or `docker ps` plus the NAT rule. A port can be owned by a mechanism (socket activation, NAT, routing mesh) and not by the process you expect.
3. **Change one thing, verify, and know your rollback before you start.** Every dispatch in section 10 comes with its undo.
4. **Write it down.** The inventory table in section 9 is the deliverable. Your future self, the client and the next on-call engineer need it more than they need the fix.

---

## 2. Mental model: what owning a port means

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *IPs and Ports* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine → *Publishing Ports* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 3) Note: [Learn: networking](28-learn-networking.md) and Docker docs *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)) · 4) Video: KodeKloud *How Docker Networking Actually Works* (9 min, [YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 5) Practice: KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)): publish a port, then compare `ss -ltnp` with `iptables -t nat -L DOCKER -n`.

**Level:** [L0 · Fresher] for the first four topics (sockets, states, bind addresses, privileged ports) · [L2 · Mid] for socket activation, Docker NAT and the Swarm mesh · [L3 · Senior] for the Kubernetes table.

### A listening socket is a (protocol, IP, port) triple

A program does not own "port 443". It owns a **socket** bound to a protocol, a local IP address and a port, for example `tcp 0.0.0.0:443` or `udp 127.0.0.53:53`. Consequences you will use daily:

- **TCP and UDP are separate namespaces.** `tcp/53` and `udp/53` can belong to different programs. Traefik with HTTP/3 holds both `tcp/443` and `udp/443`, so check both.
- **The IP is part of the identity.** `127.0.0.1:8080` and `192.0.2.10:8080` are different sockets. On Linux, though, a **wildcard** bind (`0.0.0.0:443` or `[::]:443`) conflicts with any specific-IP bind on the same port, and the reverse is also true. That's why Apache with a bare `Listen 443` blocks Traefik on every IP of the machine.
- **The kernel tracks ownership through file descriptors.** The socket is an fd inside one or more processes. A forking server such as Apache has the *same* listening socket open in the parent and in every worker. That's why `ss` lists several PIDs for one port.
- **Two processes can share a port legitimately** when both set `SO_REUSEPORT` (Nginx `reuseport`, Envoy, some Go servers). You then see two LISTEN lines for the same address and port. That isn't a conflict.

### LISTEN, ESTABLISHED and TIME_WAIT

| State | What it is | Where you see it | What it tells you |
|---|---|---|---|
| `LISTEN` | server socket waiting for new connections | `ss -ltn` | **who owns the port** |
| `UNCONN` | a bound UDP socket (UDP has no connections) | `ss -lun` | who owns a UDP port |
| `ESTAB` | a live connection: local IP:port plus peer IP:port | `ss -tn` | **who is using the service right now** |
| `TIME_WAIT` | a closed connection kept for about 60 s by the side that closed first | `ss -tan state time-wait` | recent traffic. It does **not** own the port |
| `SYN-SENT` / `SYN-RECV` | handshake in progress | `ss -tan` | stuck SYN-SENT means the remote isn't answering; many SYN-RECV can mean a SYN flood or a full backlog |

On a server, an ESTABLISHED connection *to* your service has the service port as its **local** port and a random high port (the ephemeral port) on the **peer** side. So filter with `sport = :443` to see clients of your 443 and with `dport = :5432` to see connections your box makes *to* a database.

On a LISTEN line, `Recv-Q` is the number of connections waiting in the accept queue and `Send-Q` is the backlog limit. A `Recv-Q` that sits close to `Send-Q` means the application isn't accepting fast enough. That's a busy or stuck service, not a port conflict.

### Bind addresses: 0.0.0.0, 127.0.0.1, a specific IP, [::]

| `ss` shows | Meaning | Reachable from |
|---|---|---|
| `0.0.0.0:80` | all IPv4 addresses of the host | anywhere the firewall allows (IPv4) |
| `[::]:80` | all IPv6 addresses (IPv6 only if the app set `IPV6_V6ONLY`) | IPv6 clients |
| `*:80` | `[::]` **dual-stack**: all IPv6 **and** all IPv4 addresses | everyone (Apache, Node and Java usually look like this) |
| `127.0.0.1:3306` | loopback only | **only this host**. Other machines get "connection refused" |
| `[::1]:3000` | IPv6 loopback only | only this host, and only clients that connect to `::1` |
| `192.0.2.10:443` | one interface address | only traffic sent to that IP |
| `127.0.0.53%lo:53` | bound to an IP **and** to a device (`SO_BINDTODEVICE`) | systemd-resolved's stub resolver |

Three traps hide in this table:

- **Dual-stack sockets show IPv4 clients as IPv6 addresses.** A client 198.51.100.23 talking to Apache's `*:443` appears as `[::ffff:198.51.100.23]`. It's the same client.
- **"localhost" is not always 127.0.0.1.** An app told to listen on `localhost` may bind only `::1` (Node.js 17+ commonly does). Then `curl http://127.0.0.1:3000` is refused while `curl http://localhost:3000` works. Compare `ss -ltn` with what the client actually dials.
- **A container's localhost is the container itself.** A Traefik container can't reach a host service bound to `127.0.0.1`. The host's loopback is a different network namespace. See [Docker](14-docker-containers.md) and section 10.

The kernel switch behind dual-stack is `net.ipv6.bindv6only` (default `0`, meaning `[::]` sockets also accept IPv4). Leave it alone. Fix the application's listen directive instead.

### Privileged ports and CAP_NET_BIND_SERVICE

Ports below 1024 (the value of `net.ipv4.ip_unprivileged_port_start`) can only be bound by root or by a process with the `CAP_NET_BIND_SERVICE` capability. That's why:

- **Apache and Nginx start as root**, bind 80 and 443 in the master process, then run workers as `www-data`. In `ss` the master is root and the workers are www-data, all on the same socket.
- **A non-root app** that should bind 80 needs `AmbientCapabilities=CAP_NET_BIND_SERVICE` in its systemd unit, or `setcap 'cap_net_bind_service=+ep' BINARY` on the binary. Better still, keep it on a high port behind a reverse proxy.
- **Inside Docker containers** (Docker 20.10+), the engine sets the unprivileged-port start to 0 within the container's namespace, so a non-root process in a container can bind 80. The *host* side of `-p 80:80` is still opened by root (dockerd or docker-proxy).
- **Rootless Docker and rootless Podman** can't publish host ports below 1024 unless that sysctl is lowered on the host.

The error is different from a port conflict: `EACCES` / "Permission denied" (errno 13), **not** "Address already in use" (errno 98).

```bash
sysctl net.ipv4.ip_unprivileged_port_start   # 1024 by default on the host
getcap /usr/bin/node                         # any file capabilities set on a binary?
grep ^Cap /proc/PID/status                   # CapInh/CapPrm/CapEff/CapBnd/CapAmb (hex bitmasks); decode with: capsh --decode=HEX
```

### systemd socket activation: the port without the program

A `.socket` unit makes **systemd (PID 1) itself** open and hold the listening socket. The matching `.service` starts on the first connection, or immediately if you start it by hand. Consequences:

- `ss` shows `users:(("systemd",pid=1,...))`, alone before the first connection, or next to the real daemon after it.
- `systemctl stop UNIT.service` does **not** free the port. The next connection starts the service again. You must also stop the `.socket` unit.
- On **Ubuntu 22.10 and later (including 24.04), SSH is socket-activated** through `ssh.socket`. The port comes from the socket unit. On 24.04 a generator derives it from `Port` / `ListenAddress` in `sshd_config`, so changing the port takes `systemctl daemon-reload` and `systemctl restart ssh.socket`.
- **Docker** ships `docker.socket` (the API unix socket, not a TCP port). That's why stopping `docker.service` prints *"Stopping docker.service, but it can still be activated by: docker.socket"*, and the next `docker` command restarts the daemon.

```bash
systemctl list-sockets --all            # every socket unit: LISTEN address → UNIT → ACTIVATES
```

```
LISTEN                          UNIT                         ACTIVATES
/run/dbus/system_bus_socket     dbus.socket                  dbus.service
/run/docker.sock                docker.socket                docker.service
/run/systemd/journal/stdout     systemd-journald.socket      systemd-journald.service
[::]:22                         ssh.socket                   ssh.service
[::]:9090                       cockpit.socket               cockpit.service
```

→ Two TCP ports here, 22 and 9090, are held by PID 1. `ss` reports them as `systemd` until a client connects.

### Docker published ports: docker-proxy and DNAT

`docker run -p 8081:3000 IMAGE` (or `ports: ["8081:3000"]` in Compose) does **two** things:

1. **A DNAT rule** in the `nat` table (`DOCKER` chain): packets arriving for host port 8081 are rewritten to `CONTAINER_IP:3000` *before* the host's socket lookup. They then traverse the **FORWARD** chain into the container. UFW's INPUT rules never see them, which is why `ufw deny 8081` doesn't protect a published port. Filtering for containers belongs in the `DOCKER-USER` chain ([Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)).
2. **A `docker-proxy` process** (the "userland proxy", on by default) that really LISTENs on `0.0.0.0:8081` and `[::]:8081`. It handles cases the NAT rule can't, mainly connections from the host to its own loopback. It is also why `ss` shows *something* for a published port.

With `"userland-proxy": false` in `/etc/docker/daemon.json`, only the DNAT rule exists. **`ss` then shows nothing for the port, yet the port answers.** Scenario 16 covers this.

```
                 client → 192.0.2.10:8081/tcp
                              │
            ┌─────────────────▼──────────────────┐
            │ nat PREROUTING → DOCKER chain      │  DNAT 8081 → 172.18.0.3:3000
            └─────────────────┬──────────────────┘  (happens BEFORE socket lookup)
                              │ rewritten
            ┌─────────────────▼──────────────────┐
            │ filter FORWARD → DOCKER-USER, ...  │  ← UFW INPUT rules not involved
            └─────────────────┬──────────────────┘
                              ▼
            container netns: app LISTEN 0.0.0.0:3000  (only visible from inside:
                                                        nsenter / netshoot)
   Meanwhile on the host: docker-proxy LISTEN 0.0.0.0:8081, used mainly for
   host-local and hairpin connections, and the reason ss shows a PID at all.
```

### Docker Swarm ingress routing mesh

A Swarm service published in the default **ingress** mode (`--publish published=8080,target=80`) is reachable on port 8080 of **every node in the swarm**, whether or not a task runs there. `dockerd` reserves the port, so `ss` shows `users:(("dockerd",...))`. The traffic goes through the hidden `ingress-sbox` namespace and IPVS to a task on any node.

- The port belongs to the **service**, not to the tasks. Scaling to 0 replicas does **not** free it. You need `docker service update --publish-rm 80 SERVICE` (`--publish-rm` matches the **target** port, 80 here, not the published 8080) or `docker service rm SERVICE`.
- **Host mode** (`mode=host`) publishes only on nodes where a task runs, through the normal docker-proxy and DNAT path.
- Swarm needs its own ports between nodes: `2377/tcp` (management), `7946/tcp+udp` (gossip) and `4789/udp` (VXLAN overlay). Dokploy runs Docker in Swarm mode, so these appear on a Dokploy host.

### Kubernetes: NodePort, hostPort and hostNetwork

| Mechanism | Who answers | What `ss` on the node shows |
|---|---|---|
| **NodePort / LoadBalancer Service** (30000–32767 by default) | kube-proxy's iptables, IPVS or nftables rules DNAT to a pod IP. With Cilium's kube-proxy replacement, eBPF programs do it | **Nothing.** Current kube-proxy versions don't hold a listening socket for NodePorts. Older ones showed `kube-proxy` LISTEN on each NodePort |
| **hostPort** in a pod spec | the CNI `portmap` plugin's DNAT rules (`CNI-HOSTPORT-DNAT`) | **Nothing** |
| **hostNetwork: true** pod | the pod's process binds directly in the node's namespace | **The real process** (for example `nginx` for a hostNetwork ingress controller), with a `kubepods` cgroup |
| Static control-plane pods (kubeadm) | `kube-apiserver` on 6443, `etcd` on 2379–2380, `kube-scheduler` on 10259, `kube-controller-manager` on 10257, all hostNetwork | the real binaries |
| kubelet, kube-proxy | `kubelet` on 10250, `kube-proxy` on 10256 (health) and 127.0.0.1:10249 (metrics) | real processes |

The rule: **on a Kubernetes node, "nothing in ss" is normal for Service ports.** Look at the rules (section 7), not for a process.

### Who can own a port: summary

| `ss` owner column shows | What really owns the port | Where the application is | Section |
|---|---|---|---|
| a normal process (`apache2`, `nginx`, `node`, `java`, `mysqld`) | that process | in its systemd unit, a user session, pm2 or supervisord | 4 |
| `systemd` (pid 1) | a `.socket` unit | the `.service` it activates | 2, 10 |
| `docker-proxy` | Docker's userland proxy for `-p` | the container whose IP is in docker-proxy's arguments | 6 |
| `dockerd` | the Swarm ingress routing mesh | a Swarm service | 6 |
| `rootlessport`, `rootlesskit`, `pasta`, `slirp4netns` | rootless Podman or Docker port forwarding | a rootless container | 6 |
| a process whose cgroup is `kubepods…` | a hostNetwork pod | that pod | 7 |
| **nothing**, port still answers | NAT (Docker without userland proxy, kube-proxy, hostPort, a manual REDIRECT), IPVS, eBPF, or another machine holding the IP | rules, IPVS table, or another host | 16 |
| line present but **no process**, even as root | a kernel socket: nfsd on 2049, lockd, the VXLAN socket on 4789/udp (Swarm overlay), WireGuard's UDP port | the kernel module or interface that opened it | 16 |

### Ports you will meet on your servers

| Port | Usual owner | Notes |
|---|---|---|
| 22/tcp | sshd (via `ssh.socket` on Ubuntu 22.10+) | changing it remotely can lock you out |
| 25/tcp | Postfix `master` | 127.0.0.1 only if installed as "Local only"; check `postconf inet_interfaces` |
| 53/tcp+udp on 127.0.0.53 and 127.0.0.54 | systemd-resolved stub | not a DNS server for the LAN |
| 80, 443/tcp (+443/udp) | Apache, Nginx, Traefik (Dokploy), HAProxy, Caddy | 443/udp = HTTP/3 |
| 3000/tcp | Dokploy UI; also Grafana and many Node apps by default | Dokploy's installer refuses to run if 80, 443 or 3000 is taken |
| 3306, 33060 | MySQL (classic, X protocol) | default bind 127.0.0.1 on Ubuntu |
| 5432 | PostgreSQL | default `listen_addresses = 'localhost'` |
| 6379 | Redis | protected mode, bind 127.0.0.1 by default |
| 8080 | Tomcat, Jenkins, Traefik API/dashboard, alt-HTTP | a common clash |
| 9090, 9100 | Cockpit (socket-activated) or Prometheus; node_exporter | |
| 2377, 7946, 4789/udp | Docker Swarm | must be open between swarm nodes only |
| 6443, 2379–2380, 10250, 10257, 10259 | Kubernetes control plane and kubelet | CKA material |
| 30000–32767 | Kubernetes NodePort range | no LISTEN socket |
| 111, 2049 | rpcbind, NFS (kernel) | 2049 has no process |
| 5000, 7000 (macOS) | AirPlay Receiver (ControlCenter) | section 12 |

---

## 3. Linux: list every listener

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → *Troubleshooting* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 3) Note: [Network reference](02-network.md) · 4) Practice: [Killercoda Linux scenarios](https://killercoda.com/linux) or the KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)): explain every line of `sudo ss -tulpn` out loud.

**Level:** [L0 · Fresher] for `ss -tulpn` and lsof · [L1 · Junior] for filters, state queries and nmap from outside · [L2 · Mid] for decoding `/proc/net/tcp` by hand.

### ss -tulpn: the first command

`ss` comes with `iproute2` and is installed on every modern distribution. Run it as **root**, because without root the Process column is empty for sockets other users own.

```bash
sudo ss -tulpn            # -t TCP  -u UDP  -l listening only  -p process  -n numeric (no DNS / service names)
sudo ss -tlpn             # TCP listeners only: the usual question
sudo ss -tulpn -4         # IPv4 only (-6 for IPv6 only)
```

```
Netid State  Recv-Q Send-Q      Local Address:Port   Peer Address:Port Process
udp   UNCONN 0      0              127.0.0.54:53          0.0.0.0:*     users:(("systemd-resolve",pid=598,fd=16))
udp   UNCONN 0      0           127.0.0.53%lo:53          0.0.0.0:*     users:(("systemd-resolve",pid=598,fd=14))
tcp   LISTEN 0      4096        127.0.0.53%lo:53          0.0.0.0:*     users:(("systemd-resolve",pid=598,fd=15))
tcp   LISTEN 0      4096           127.0.0.54:53          0.0.0.0:*     users:(("systemd-resolve",pid=598,fd=17))
tcp   LISTEN 0      151             127.0.0.1:3306        0.0.0.0:*     users:(("mysqld",pid=1120,fd=23))
tcp   LISTEN 0      70              127.0.0.1:33060       0.0.0.0:*     users:(("mysqld",pid=1120,fd=21))
tcp   LISTEN 0      100             127.0.0.1:25          0.0.0.0:*     users:(("master",pid=1544,fd=13))
tcp   LISTEN 0      511             127.0.0.1:3001        0.0.0.0:*     users:(("node",pid=2210,fd=19))
tcp   LISTEN 0      4096              0.0.0.0:8081        0.0.0.0:*     users:(("docker-proxy",pid=3302,fd=7))
tcp   LISTEN 0      4096                 [::]:8081           [::]:*     users:(("docker-proxy",pid=3309,fd=7))
tcp   LISTEN 0      4096                    *:22                *:*     users:(("sshd",pid=1350,fd=3),("systemd",pid=1,fd=104))
tcp   LISTEN 0      511                     *:80                *:*     users:(("apache2",pid=1344,fd=4),("apache2",pid=1343,fd=4),("apache2",pid=1201,fd=4))
tcp   LISTEN 0      511                     *:443               *:*     users:(("apache2",pid=1344,fd=6),("apache2",pid=1343,fd=6),("apache2",pid=1201,fd=6))
```

Read it like a senior:

→ **Lines bound to 127.0.0.x** (DNS stub, MySQL, Postfix, the Node app on 3001) are local-only. They can't be what an outside client hits, and they don't conflict with anything you bind on a public IP. Note them, then move on.

→ **`*:80` and `*:443` owned by `apache2`**: several PIDs share one socket. The **lowest PID (1201) is usually the master**, and the others are workers. You stop or reconfigure the master, through its unit, never the workers.

→ **`*:22` owned by `sshd` *and* `systemd` pid 1**: socket activation (`ssh.socket`). Stopping `ssh.service` alone wouldn't free 22.

→ **`docker-proxy` on 8081**: a published container port. The application is a container, and section 6 tells you which one. Also remember that this port bypasses UFW.

→ **`Send-Q`** on a LISTEN line is the backlog (511 for Apache and Node, 4096 for Go and Docker). `Recv-Q` is the current accept queue. Non-zero `Recv-Q` on a listener means the app is falling behind.

### ss filters and state queries

The filter language saves you from `grep` mistakes like `:80` matching `:8081`.

```bash
# Who owns one port (TCP, then UDP — HTTP/3 uses udp/443)
sudo ss -ltnp 'sport = :443'
sudo ss -lunp 'sport = :443'

# Several ports at once
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :3000 )'

# A port range (e.g. the Kubernetes NodePort range)
sudo ss -ltn '( sport >= :30000 and sport <= :32767 )'

# Only listeners bound to a given local address
sudo ss -ltn 'src 192.0.2.10'

# No header (-H) for scripts; -e adds uid and inode (needed to match /proc)
sudo ss -Hltnpe 'sport = :3306'

# Connection states — useful names: established, syn-sent, syn-recv,
# time-wait, close-wait, fin-wait-1, fin-wait-2, listening, connected
ss -tan state time-wait | wc -l          # recent closed connections (harmless)
ss -tanp state close-wait                # app NOT closing sockets it got EOF on (app bug / leak)
ss -tan state syn-sent                   # this box trying to reach something that doesn't answer
ss -s                                    # totals per state and protocol
```

```
$ sudo ss -ltnp 'sport = :443'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1344,fd=6),("apache2",pid=1343,fd=6),("apache2",pid=1201,fd=6))
```

→ An empty result (header only) means **no local process listens** on that port in this network namespace. That does *not* prove the port is free: see NAT owners in section 2 and scenario 16.

> When you add a `state` filter, `ss` drops the State column, so the field positions in your `awk` shift. Always test an awk one-liner on a few lines first.

### Who is connected right now

Listeners tell you who *owns* a port. Established connections tell you who *uses* it. That evidence decides whether a service can go (section 9).

```bash
# Every live connection to local port 443, with the serving process
sudo ss -tnp state established '( sport = :443 )'

# Count connections per client IP (IPv6-safe: strip the trailing :port)
ss -Htn state established '( sport = :443 )' \
  | awk '{sub(/:[0-9]+$/,"",$4); print $4}' | sort | uniq -c | sort -rn | head

# Outgoing: which local processes talk to the database on 192.0.2.30:5432?
sudo ss -tnp state established '( dport = :5432 and dst 192.0.2.30 )'
```

```
$ ss -Htn state established '( sport = :443 )' | awk '{sub(/:[0-9]+$/,"",$4); print $4}' | sort | uniq -c | sort -rn
     14 [::ffff:203.0.113.45]
      3 [::ffff:198.51.100.23]
      1 [::ffff:192.0.2.5]
```

→ `[::ffff:203.0.113.45]` is an IPv4 client on Apache's dual-stack socket. 14 connections from one IP is typical of a reverse proxy, NAT gateway or monitoring system in front of you. Find out which before you conclude "lots of users".

→ A snapshot is one moment. Before you retire anything, sample over a day (section 9).

### lsof views

`lsof` ("list open files") sees sockets as files. It's slower than `ss`, but its output is easier to read and it combines nicely with process filters.

```bash
sudo lsof -nP -iTCP -sTCP:LISTEN          # all TCP listeners (-n no DNS, -P numeric ports)
sudo lsof -nP -iTCP:443 -sTCP:LISTEN      # one TCP port
sudo lsof -nP -i :443                     # everything on 443: listeners AND connections
sudo lsof -nP -iUDP:53                    # UDP
sudo lsof -t -iTCP:3001 -sTCP:LISTEN      # PIDs only, for scripting
sudo lsof -nP -a -p 1201 -i               # all network sockets of one PID (-a = AND the filters)
```

```
COMMAND    PID            USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
systemd      1            root  104u  IPv6  18322      0t0  TCP *:22 (LISTEN)
systemd-r  598 systemd-resolve   15u  IPv4  20113      0t0  TCP 127.0.0.53:53 (LISTEN)
mysqld    1120           mysql   23u  IPv4  24510      0t0  TCP 127.0.0.1:3306 (LISTEN)
apache2   1201            root    4u  IPv6  25120      0t0  TCP *:80 (LISTEN)
apache2   1201            root    6u  IPv6  25124      0t0  TCP *:443 (LISTEN)
apache2   1343        www-data    4u  IPv6  25120      0t0  TCP *:80 (LISTEN)
node      2210          deploy   19u  IPv4  41877      0t0  TCP 127.0.0.1:3001 (LISTEN)
```

→ `COMMAND` is cut to 9 characters (`systemd-r` is systemd-resolved). The `USER` column shows at a glance which privileges each listener runs with. For IP sockets, `DEVICE` holds the socket's inode number and `NODE` the protocol (`TCP`). The same `DEVICE` value on two lines (25120) means the same socket is shared, as with the Apache master and its workers.

### fuser: owner of a port in one line

```bash
sudo fuser -v 443/tcp          # who has tcp/443 open (verbose table)
sudo fuser -v -n udp 53        # same for UDP
```

```
                     USER        PID ACCESS COMMAND
443/tcp:             root       1201 F.... apache2
                     www-data   1343 F.... apache2
                     www-data   1344 F.... apache2
```

> `fuser -k 443/tcp` **kills every process** holding the port, immediately, with SIGKILL by default. It kills masters and workers alike and bypasses systemd. Don't use it on servers. Identify the owner, then stop it through its manager (section 10).

### netstat: the legacy view

`netstat` is in the `net-tools` package, which isn't installed by default on recent Ubuntu. You will still meet it on older boxes and in other people's runbooks.

```bash
sudo netstat -tulpn            # same idea as ss -tulpn
sudo netstat -tanp | grep ESTABLISHED
```

```
Proto Recv-Q Send-Q Local Address    Foreign Address  State    PID/Program name
tcp        0      0 127.0.0.1:3306   0.0.0.0:*        LISTEN   1120/mysqld
tcp6       0      0 :::443           :::*             LISTEN   1201/apache2
```

→ netstat prints dual-stack `[::]` sockets as `tcp6 :::443`. That's the same as `*:443` in `ss`. It accepts IPv4 as well.

### No tools installed: read /proc/net/tcp by hand

Minimal containers, rescue shells and locked-down appliances often have no `ss`, `lsof` or `netstat`. The kernel exposes the same tables as text, in hex:

```bash
cat /proc/net/tcp        # IPv4 TCP sockets of THIS network namespace (tcp6, udp, udp6 exist too)
```

```
  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 3500007F:0035 00000000:0000 0A 00000000:00000000 00:00000000 00000000   991        0 20113 1 0000000000000000 100 0 0 10 5
   1: 0100007F:0CEA 00000000:0000 0A 00000000:00000000 00:00000000 00000000   113        0 24510 1 0000000000000000 100 0 0 10 0
   2: 00000000:1F91 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 31877 1 0000000000000000 100 0 0 10 0
```

How to decode a line by hand:

- `local_address` is `IP:PORT` in hex. The IPv4 address is stored **little-endian** on x86/ARM, so read the bytes backwards: `0100007F` → `7F 00 00 01` → `127.0.0.1`. `3500007F` → `127.0.0.53`.
- The port is plain hex: `0CEA` → 3306, `0035` → 53, `1F91` → 8081.
- `st` is the state: `0A` LISTEN, `01` ESTABLISHED, `06` TIME_WAIT, `08` CLOSE_WAIT, `02` SYN_SENT, `03` SYN_RECV.
- `uid` is the owning user's UID (991 = systemd-resolve here, 113 = mysql). `inode` is the socket's inode, which leads you to the PID.

A bash-only decoder (no gawk needed; Ubuntu's default awk is mawk, which lacks `strtonum`):

```bash
# List IPv4 TCP listeners from /proc/net/tcp with nothing but bash
while read -r sl local rem st txrx trtm retr uid timeout inode rest; do
  [ "$st" = "0A" ] || continue                       # LISTEN only
  ip=${local%:*}; port=${local#*:}
  printf '%d.%d.%d.%d:%d uid=%s inode=%s\n' \
    0x${ip:6:2} 0x${ip:4:2} 0x${ip:2:2} 0x${ip:0:2} 0x$port "$uid" "$inode"
done < <(tail -n +2 /proc/net/tcp)

# Inode → PID: find which process has that socket open
sudo find /proc/[0-9]*/fd -lname 'socket:\[24510\]' 2>/dev/null
```

```
127.0.0.53:53 uid=991 inode=20113
127.0.0.1:3306 uid=113 inode=24510
0.0.0.0:8081 uid=0 inode=31877
/proc/1120/fd/23
```

→ `/proc/1120/fd/23` means PID 1120 owns the socket on fd 23. From there, follow section 4.

Two things to know about these files:

- **Dual-stack and IPv6 listeners are in `/proc/net/tcp6`**, not `tcp`. Apache's `*:443` appears there as `00000000000000000000000000000000:01BB` (all zeros = `[::]`, `01BB` = 443). The port is easy to read even when the 128-bit address isn't.
- **`/proc/net/tcp` is per network namespace.** On the host you see the host's sockets only. To see a container's listeners from the host, read the file through one of the container's processes: `sudo cat /proc/$(docker inspect -f '{{.State.Pid}}' CONTAINER)/net/tcp`.

### UDP listeners are different

UDP has no LISTEN state. A bound UDP socket shows as `UNCONN` in `ss -uln`. Also:

- **`nc -zu` and `nmap -sU` from outside are unreliable.** No answer can mean "open" or "filtered". Only an ICMP port-unreachable reply proves "closed". Test with the real protocol instead: `dig @HOST` for DNS, `ntpdate -q HOST` for NTP (package `ntpsec-ntpdate` on Ubuntu 24.04), `snmpget` for SNMP. Don't use `chronyc -h HOST` for this: it talks to chronyd's command port 323, not to NTP on 123, and remote access to it is refused by default.
- **QUIC / HTTP/3** uses `udp/443`. Dokploy's Traefik publishes it next to `tcp/443`, and any older service on `udp/443` blocks it as well.

```bash
sudo ss -ulnp                       # all bound UDP sockets
sudo ss -ulnp 'sport = :443'        # anything on udp/443 (HTTP/3)?
```

### From another machine: what is actually reachable

`ss` tells you what is bound. Only a test **from another machine** tells you what a client can actually reach through firewalls, NAT and routing. Run these from a box on the client's side of the network (only against hosts you're authorized to test):

```bash
nc -zv -w 3 192.0.2.10 443                  # one TCP port: succeeded / refused / timed out
nmap -Pn -p 22,80,443,3000,3306,8081 192.0.2.10   # a short list (-Pn: don't require ping)
nmap -Pn -sV -p 443 192.0.2.10              # also guess the service/version answering
sudo nmap -Pn -sU -p 53,123 192.0.2.10      # UDP (slow, ambiguous; see above)
```

```
Nmap scan report for 192.0.2.10
Host is up (0.00041s latency).

PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
443/tcp  open   https
3000/tcp closed ppp
3306/tcp closed mysql
8081/tcp open   blackice-icecap
```

→ **`open`**: something accepted the TCP handshake. **`closed`**: the host answered with a reset, so the path works but nothing listens on a reachable address. 3306 is closed here because MySQL binds 127.0.0.1. **`filtered`**: no answer at all, so a firewall is dropping the packets.

→ **8081 is open from outside** even if `ufw status` doesn't allow it. That's the Docker-published-port bypass from section 2. If it should only be reachable through Traefik, publish it on `127.0.0.1:8081:3000` or don't publish it at all.

→ The `SERVICE` column is nmap's **guess from the port number**, not a fact (8081 isn't "blackice"). Use `-sV` or `curl -v` to see what actually answers.

> Testing from the server against its own public IP is **not** the same as testing from outside. Locally generated traffic skips PREROUTING and often matches different firewall rules. Always confirm from a second machine.

---

## 4. The chain: port to PID, unit, config and logs

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment → *Diagnose and Manage Processes* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) and *Locate and Analyze System Log Files* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD → *SYSTEMD Tools* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) · 3) Note: [Processes](05-processes.md), [Logs & journal](06-logs-journal.md), [systemd](07-services-systemd.md) · 4) Read: the [strace zine](https://wizardzines.com/zines/strace/) for Step 6 · 5) Practice: drill 1 in section 19 (the five-minute drill).

**Level:** [L1 · Junior]. This section *is* the L1 exit test. Steps 1–3 are expected of a Fresher by the end of the first year.

This is the L1 exit test as a procedure. The worked example is port 443 on the Apache box from section 3. Variants show what changes when the owner is a pm2-managed Node app, a container or a socket unit.

### Step 1 — Port to PID

**Goal:** get the PID (or the mechanism) that owns the port.

```bash
sudo ss -ltnp 'sport = :443'          # TCP
sudo ss -lunp 'sport = :443'          # and UDP
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1344,fd=6),("apache2",pid=1343,fd=6),("apache2",pid=1201,fd=6))
```

**What it means:** a dual-stack TCP listener (`*:443`) shared by three apache2 processes. Take the lowest PID, 1201, as the candidate master and confirm it in step 2. An empty UDP result is good: nothing holds `udp/443`.

**Why this step (now):** every later step needs a PID, and `ss` is the cheapest and most direct source. It reads the kernel's socket table, with no guessing from config files that may not even be loaded.

**Next step:** a normal process → Step 2. The owner is `systemd` → it's a socket unit: `systemctl list-sockets | grep ':443'`, then Step 3 with that unit. `docker-proxy` or `dockerd` → section 6. Nothing, but the port answers → scenario 16.

### Step 2 — PID to process details and parent

**Goal:** know exactly what the process is, who runs it, since when, and who its parent is.

```bash
ps -o pid,ppid,user,lstart,etime,cmd -p 1201
pstree -aps 1343                      # ancestors of a worker: proves who the master is
ps -o pid,user,unit,cmd -p 1201,2210  # procps can print the systemd unit directly
```

```
    PID    PPID USER                      STARTED     ELAPSED CMD
   1201       1 root     Tue Sep 29 08:14:02 2026  4-01:22:10 /usr/sbin/apache2 -k start

systemd,1 --system --deserialize=31
  `-apache2,1201 -k start
      `-apache2,1343 -k start

    PID USER     UNIT                         CMD
   1201 root     apache2.service              /usr/sbin/apache2 -k start
   2210 deploy   pm2-deploy.service           node /srv/crm/server.js
```

**What it means:** PID 1201 runs as root, its parent is PID 1 (systemd), and it has been up 4 days. The worker 1343 is its child, so 1201 is the master. The Node app 2210 belongs to `pm2-deploy.service`, which means pm2, not a plain unit, starts it (relevant for "why does it come back", section 10).

Parent patterns worth recognizing:

| Parent (PPID) | Meaning |
|---|---|
| `systemd` (1) | a systemd unit, or an orphan that daemonized itself (check the cgroup in step 3) |
| `containerd-shim-runc-v2` | a container (Docker or Kubernetes) |
| `PM2 v5.x: God Daemon`, `supervisord`, `runsv`, `s6-supervise` | a process manager restarts it |
| `bash`, `sshd: user@pts/0`, `tmux: server`, `screen` | **started by hand**; it won't survive a reboot and may die on logout |
| `cron` / `CRON` | launched from a crontab |

**Why this step (now):** the PID alone doesn't tell you how the process is *managed*, and the manager decides how you stop it safely. A start time that matches an incident or a deploy is also evidence.

**Next step:** → Step 3 to name the unit or container precisely.

### Step 3 — PID to systemd unit, container or session

**Goal:** find the thing that *manages* the process. You'll talk to that manager, not to the PID.

```bash
systemctl status 1201 --no-pager      # systemctl accepts a PID and shows its unit
cat /proc/1201/cgroup                 # the raw truth (cgroup v2 on Ubuntu 22.04+)
```

```
● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-09-29 08:14:02 UTC; 4 days ago
       Docs: https://httpd.apache.org/docs/2.4/
    Process: 1185 ExecStart=/usr/sbin/apachectl start (code=exited, status=0/SUCCESS)
   Main PID: 1201 (apache2)
      Tasks: 109 (limit: 9387)
     Memory: 214.6M (peak: 260.1M)
        CPU: 6min 12.004s
     CGroup: /system.slice/apache2.service
             ├─1201 /usr/sbin/apache2 -k start
             ├─1343 /usr/sbin/apache2 -k start
             └─1344 /usr/sbin/apache2 -k start

0::/system.slice/apache2.service
```

**What it means:** the unit is `apache2.service`, enabled at boot, and its unit file is in `/usr/lib/systemd/system/` (Ubuntu 24.04; 22.04 uses `/lib/systemd/system/`). `Main PID` confirms 1201 is the master.

How to read the cgroup line for other owners:

```
0::/system.slice/apache2.service                         → systemd service "apache2.service"
0::/system.slice/pm2-deploy.service                      → pm2, itself run by a systemd unit
0::/system.slice/docker-8c1f0e5b2d7a….scope              → Docker container 8c1f0e5b2d7a… (section 6)
0::/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod3c…slice/cri-containerd-4b1c….scope
                                                         → Kubernetes pod container 4b1c… (section 7)
0::/user.slice/user-1000.slice/session-12.scope          → started by hand in login session 12 (!)
0::/user.slice/user-1000.slice/user@1000.service/app.slice/…  → a systemd --user service or rootless Podman
0::/system.slice/cron.service                            → started by a cron job and never left cron's cgroup
```

**Why this step (now):** the cgroup is the one piece of ownership evidence that can't lie. A process can rename itself and daemonize, but it can't leave the cgroup its manager put it in. It's also the bridge to containers and pods, which `ps` alone doesn't show.

**Next step:** a `.service` → Step 4. A container or pod → section 6 or 7. A `session-N.scope` → someone ran it by hand. Run `loginctl session-status N` to see who, and treat it as unmanaged (it won't come back after a reboot). Then continue with Step 4.

### Step 4 — Binary, working dir, command line, environment

**Goal:** know exactly which file runs, from where, with which arguments and environment.

```bash
sudo readlink /proc/2210/exe          # the real binary (resolves symlinks)
sudo readlink /proc/2210/cwd          # working directory: relative paths resolve from here
tr '\0' ' ' < /proc/2210/cmdline; echo   # exact argv
sudo cat /proc/2210/environ | tr '\0' '\n' | grep -vE 'PASS|SECRET|TOKEN|KEY' | sort   # sudo on cat: a '<' redirect would run as you
```

```
/usr/bin/node
/srv/crm
node /srv/crm/server.js
HOME=/home/deploy
NODE_ENV=production
PM2_HOME=/home/deploy/.pm2
PORT=3001
pm_id=0
```

**What it means:** the CRM app's code lives in `/srv/crm`. It gets its port from the `PORT` environment variable, set by pm2. So the port isn't in a config file at all; it's in pm2's ecosystem file or saved process list (`pm2 describe crm`). An `exe` ending in `(deleted)` means the binary was upgraded on disk and the running process is still the old version.

> `/proc/PID/environ` often contains passwords and tokens. Filter it as above, and never paste it raw into a ticket or chat. Note also that it shows the environment **at process start**. Later changes to an `.env` file aren't reflected until a restart.

**Why this step (now):** the cwd and the arguments are where the config is usually referenced (`-f`, `-c`, `--config`, `.env` in the cwd), so this step points straight at Step 6. It also exposes the "port comes from an env var" case, which no config grep would find.

**Next step:** → Step 5 to learn where the binary came from (package, manual install or snap).

### Step 5 — Binary to package

**Goal:** know who installed this binary and therefore where its default config and logs live.

```bash
dpkg -S /usr/sbin/apache2             # Debian/Ubuntu: which package owns the file
dpkg -L apache2 | grep -E '^/etc|^/var/log|\.service$'   # that package's config, log dirs, units
apt-cache policy apache2              # installed version and repo it came from
rpm -qf /usr/sbin/httpd               # RHEL/Rocky equivalent
rpm -qc httpd                         # RHEL: list the package's config files
snap list 2>/dev/null ; snap services 2>/dev/null    # snaps run as snap.NAME.SERVICE.service units
```

```
apache2-bin: /usr/sbin/apache2

/etc/apache2/apache2.conf
/etc/apache2/ports.conf
/etc/apache2/sites-available/000-default.conf
/etc/apache2/envvars
/var/log/apache2
/usr/lib/systemd/system/apache2.service

apache2:
  Installed: 2.4.58-1ubuntu8.5
  Candidate: 2.4.58-1ubuntu8.5
```

**What it means:** a packaged service follows the distribution's layout, which is good news. When `dpkg -S` answers `dpkg-query: no path found matching pattern`, the binary was installed by hand: a tarball in `/opt`, `/usr/local/bin`, a language version manager (`~/.nvm`, `~/.pyenv`), or a vendor installer. Then its config and logs are wherever the vendor or your predecessor decided. Look at the cwd, the unit's `ExecStart` and the `lsof` output.

> On usr-merged systems (Ubuntu 22.04+), `dpkg -S /usr/sbin/X` can fail when the package registered `/sbin/X`. Retry with the other prefix before you conclude "not packaged".

**Why this step (now):** "packaged or not" decides how you upgrade, remove or migrate the service, and whether `apt purge` would delete config you need. It's cheap and it finds the canonical config and log directories in one command.

**Next step:** → Step 6 for the *effective* config, which may differ from the package defaults.

### Step 6 — Find the config files

**Goal:** find the config the running process actually loaded, not the one you assume.

```bash
systemctl cat apache2                 # unit file + drop-ins: ExecStart flags, EnvironmentFile=
systemctl show apache2 -p ExecStart -p EnvironmentFiles -p WorkingDirectory -p User
sudo apache2ctl -t -D DUMP_INCLUDES   # every file Apache really includes, in order
```

```
# /usr/lib/systemd/system/apache2.service
[Unit]
Description=The Apache HTTP Server
After=network.target remote-fs.target nss-lookup.target
Documentation=https://httpd.apache.org/docs/2.4/

[Service]
Type=forking
Environment=APACHE_STARTED_BY_SYSTEMD=true
ExecStart=/usr/sbin/apachectl start
ExecStop=/usr/sbin/apachectl graceful-stop
ExecReload=/usr/sbin/apachectl graceful
KillMode=mixed
PrivateTmp=true
Restart=on-abort

[Install]
WantedBy=multi-user.target

Included configuration files:
  (*) /etc/apache2/apache2.conf
    (146) /etc/apache2/mods-enabled/ssl.load
    (147) /etc/apache2/mods-enabled/proxy.conf
    (189) /etc/apache2/ports.conf
    (222) /etc/apache2/sites-enabled/000-default.conf
    (222) /etc/apache2/sites-enabled/app1-le-ssl.conf
    (222) /etc/apache2/sites-enabled/crm-ssl.conf
    (222) /etc/apache2/sites-enabled/wiki-ssl.conf
```

**What it means:** the unit has no `-f` flag, so Apache uses its compiled-in default `/etc/apache2/apache2.conf`. `ports.conf` holds the `Listen` lines, and the three `sites-enabled` files are the vhosts. `Restart=on-abort` means systemd restarts Apache only after a crash signal, not after a clean stop. Remember that for section 10.

Most daemons can print their own effective config. Use that before grepping:

| Program | Show the effective config |
|---|---|
| Apache (Ubuntu) | `apache2ctl -S` (vhosts), `apache2ctl -t -D DUMP_INCLUDES`, `apache2ctl -M` (modules) |
| Apache (RHEL/Rocky) | `httpd -S`, `httpd -t -D DUMP_INCLUDES` (config in `/etc/httpd/`) |
| Nginx | `nginx -T` (full merged config) |
| HAProxy | `haproxy -c -f /etc/haproxy/haproxy.cfg` (check), then read the file |
| OpenSSH | `sshd -T` |
| PHP-FPM | `php-fpm8.3 -tt` (pools in `/etc/php/8.3/fpm/pool.d/`) |
| MySQL / MariaDB | `my_print_defaults mysqld`, `mysql -e "SHOW VARIABLES LIKE 'bind_address'"` |
| PostgreSQL | `sudo -u postgres psql -c 'SHOW config_file' -c 'SHOW listen_addresses'` |
| Redis | `redis-cli CONFIG GET bind`, `redis-cli CONFIG GET port` |
| pm2 apps | `pm2 describe APP` (as the pm2 user), the ecosystem file in the app dir |
| Docker containers | `docker inspect CONTAINER` (Cmd, Env, Mounts), compose file path from labels (section 6) |
| Tomcat | `CATALINA_BASE/conf/server.xml`, the `Connector port=` lines |

When the app has no such flag, watch what it opens. `lsof -p PID` only shows files that are *still* open, and most apps close their config after reading it. A config test under `strace` shows everything:

```bash
# Which files does Apache read during a config test? (read-only; -f follows apachectl's child processes)
sudo strace -f -e trace=openat -o /tmp/apache-open.txt apache2ctl -t
grep -v ENOENT /tmp/apache-open.txt | grep -oE '"/etc[^"]+"' | sort -u
```

**Why this step (now):** you can't move a port without editing the right file. On older servers, the `sites-available` file you're reading may not even be enabled. The include list and `strace` show what actually loads.

**Next step:** → Step 7 for the logs. If the process is a reverse proxy (Apache, Nginx, Traefik), also go to section 5 to map each vhost to its real backend.

### Step 7 — Find the logs

**Goal:** find where this process writes its logs right now.

```bash
journalctl -u apache2 -n 20 --no-pager        # what systemd and stdout/stderr captured
journalctl _PID=2210 -n 20 --no-pager          # by PID (when the unit is unclear)
sudo ls -l /proc/1201/fd/1 /proc/1201/fd/2 /proc/2210/fd/1   # where stdout/stderr point
sudo lsof -nP -p 1201 | grep -E '\.log|/log/'  # log files the process holds open
# Files written in the last 15 minutes: "where is it logging right now?"
sudo find /var/log /srv /opt /home -xdev -type f -mmin -15 \( -name '*.log' -o -name '*.out' \) 2>/dev/null
```

```
Oct 03 00:00:01 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Oct 03 00:00:01 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.

l-wx------ 1 root   root   64 Oct  3 08:01 /proc/1201/fd/1 -> /dev/null
l-wx------ 1 root   root   64 Oct  3 08:01 /proc/1201/fd/2 -> /var/log/apache2/error.log
l-wx------ 1 deploy deploy 64 Oct  3 08:01 /proc/2210/fd/1 -> pipe:[48211]

apache2 1201 root    2w   REG  252,0   18234 1835210 /var/log/apache2/error.log
apache2 1201 root    7w   REG  252,0  981245 1835233 /var/log/apache2/other_vhosts_access.log
apache2 1201 root    8w   REG  252,0  204117 1835240 /var/log/apache2/crm_access.log
apache2 1201 root    9w   REG  252,0   55120 1835241 /var/log/apache2/crm_error.log
```

**What it means:**

→ The journal for Apache only shows the nightly logrotate reload. **Apache's real logs are files**, and `lsof` lists every one it holds open, per vhost.

→ Where **fd 1 (stdout)** points tells you where an app's output goes:

| `/proc/PID/fd/1` points to | Logs are in |
|---|---|
| `socket:[NNNN]` | the journal: `journalctl -u UNIT` (a normal systemd service) |
| a file such as `/var/log/app/out.log` | that file |
| `pipe:[NNNN]` | a **parent** collects it: pm2 (`~/.pm2/logs/APP-out.log`), supervisord (`/var/log/supervisor/`), the Docker shim (`docker logs`), or `rotatelogs` |
| `/dev/null` | discarded. Only files the app opens itself count, so check `lsof` |

Where logs usually live:

| Service | Ubuntu/Debian | RHEL/Rocky |
|---|---|---|
| Apache | `/var/log/apache2/` (dir set by `APACHE_LOG_DIR` in `/etc/apache2/envvars`) | `/var/log/httpd/` |
| Nginx | `/var/log/nginx/` | same |
| MySQL | `/var/log/mysql/error.log` | `/var/log/mysql/mysqld.log` (AppStream) or `/var/log/mysqld.log` (MySQL community repo); confirm with `SELECT @@log_error` |
| PostgreSQL | `/var/log/postgresql/postgresql-16-main.log` | journal, or `PGDATA/log/` |
| PHP-FPM | `/var/log/php8.3-fpm.log` (pool slowlogs per pool config) | `/var/log/php-fpm/` |
| pm2 apps | `~USER/.pm2/logs/APP-out.log` and `APP-error.log` | same |
| supervisord apps | `/var/log/supervisor/` | same |
| Tomcat | `CATALINA_BASE/logs/catalina.out` | same |
| Docker containers | `docker logs CONTAINER`; files at `/var/lib/docker/containers/ID/ID-json.log` | same |
| Kubernetes pods | `kubectl logs`; on the node `/var/log/pods/NS_POD_UID/CONTAINER/0.log` | same |
| Anything else | `journalctl -u UNIT`, then the `find -mmin` trick above | same |

**Why this step (now):** logs prove whether the service is used (section 9) and why it fails. They're also what you'll need when something breaks after the move. Find them *before* you change anything.

**Next step:** record port, PID, unit, config and logs in your inventory (section 9). Owner is a proxy → section 5. You're about to stop it → section 10.

---

## 5. Reverse proxies: which vhost is which app

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *Apache Web Server* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · 2) KodeKloud: *Nginx For Beginners* — Intermediate Config → *Virtual Servers & Multiple Sites* ([lesson](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Virtual-Servers-Multiple-Sites/page)) · 3) Note: [Learn: web servers & proxies](29-learn-webservers-proxies.md) · 4) Docs: Apache *Virtual Host documentation* ([docs](https://httpd.apache.org/docs/2.4/vhosts/)) and Traefik *Docker and Traefik Quick Start* ([docs](https://doc.traefik.io/traefik/getting-started/docker/)) · 5) Practice: drill 6 in section 19.

**Level:** [L1 · Junior] for `apache2ctl -S` and the per-vhost grep · [L2 · Mid] for mod_status, Traefik routers and labels.

On the client's server, "Apache on 443" was really **three or four applications behind one socket**. The proxy owns the port, and the applications sit behind it as virtual hosts (vhosts), selected by the `Host` header and the TLS SNI name. To migrate them you need the map *domain → vhost → backend → logs*.

### Apache: apache2ctl -S maps names to vhosts

```bash
sudo apache2ctl -S         # RHEL/Rocky: sudo httpd -S
```

```
VirtualHost configuration:
*:443                  is a NameVirtualHost
         default server app1.example.com (/etc/apache2/sites-enabled/app1-le-ssl.conf:2)
         port 443 namevhost app1.example.com (/etc/apache2/sites-enabled/app1-le-ssl.conf:2)
                 alias www.app1.example.com
         port 443 namevhost crm.example.com (/etc/apache2/sites-enabled/crm-ssl.conf:2)
         port 443 namevhost wiki.example.com (/etc/apache2/sites-enabled/wiki-ssl.conf:2)
*:80                   is a NameVirtualHost
         default server 192.0.2.10 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost 192.0.2.10 (/etc/apache2/sites-enabled/000-default.conf:1)
         port 80 namevhost app1.example.com (/etc/apache2/sites-enabled/app1.conf:1)
ServerRoot: "/etc/apache2"
Main DocumentRoot: "/var/www/html"
Main ErrorLog: "/var/log/apache2/error.log"
PidFile: "/var/run/apache2/apache2.pid"
User: name="www-data" id=33
Group: name="www-data" id=33
```

**Reading it:** three HTTPS sites share `*:443`. **`default server`** is the vhost that answers when no name matches (a request by IP, or a domain nobody configured). Here that's app1. This is why a stray DNS record "works" and shows the wrong site. Each line gives you the exact file and line number, which is your starting point for each application.

### Per-vhost details: proxy, docroot, logs

```bash
# One line per interesting directive, with file:line — the whole map in one screen
sudo grep -nE '^\s*(ServerName|ServerAlias|DocumentRoot|ProxyPass|ProxyPassReverse|SetHandler|CustomLog|ErrorLog|SSLCertificateFile)\b' \
  /etc/apache2/sites-enabled/*.conf
```

```
/etc/apache2/sites-enabled/app1-le-ssl.conf:3:  ServerName app1.example.com
/etc/apache2/sites-enabled/app1-le-ssl.conf:5:  DocumentRoot /var/www/app1/public
/etc/apache2/sites-enabled/app1-le-ssl.conf:10:     SetHandler "proxy:unix:/run/php/php8.3-fpm.sock|fcgi://localhost"
/etc/apache2/sites-enabled/app1-le-ssl.conf:14: SSLCertificateFile /etc/letsencrypt/live/app1.example.com/fullchain.pem
/etc/apache2/sites-enabled/crm-ssl.conf:3:      ServerName crm.example.com
/etc/apache2/sites-enabled/crm-ssl.conf:7:      ProxyPass / http://127.0.0.1:3001/
/etc/apache2/sites-enabled/crm-ssl.conf:8:      ProxyPassReverse / http://127.0.0.1:3001/
/etc/apache2/sites-enabled/crm-ssl.conf:10:     CustomLog ${APACHE_LOG_DIR}/crm_access.log combined
/etc/apache2/sites-enabled/crm-ssl.conf:11:     ErrorLog ${APACHE_LOG_DIR}/crm_error.log
/etc/apache2/sites-enabled/wiki-ssl.conf:3:     ServerName wiki.example.com
/etc/apache2/sites-enabled/wiki-ssl.conf:6:     ProxyPass / http://127.0.0.1:8080/
```

Each vhost is one of three kinds:

| Kind | Tell-tale directive | The real application is | Migrating it means |
|---|---|---|---|
| **Static / PHP** | `DocumentRoot`, `SetHandler proxy:unix:/run/php/...` or mod_php | files under the DocumentRoot plus a PHP-FPM pool | a container with PHP-FPM + web server, or keep Apache as a backend |
| **Reverse proxy** | `ProxyPass / http://127.0.0.1:3001/` | **another process on another port**. Run section 4 again on 3001 | point Traefik at it, or containerize it |
| **Redirect only** | `Redirect permanent / https://...` | nothing | a Traefik redirect middleware |

→ `crm.example.com` proxies to `127.0.0.1:3001`, the pm2 Node app from section 4. `wiki.example.com` proxies to 8080 (probably Tomcat or a Java wiki). `app1` is PHP through PHP-FPM. **Three different migrations**, all hidden behind "Apache holds 443".

→ A vhost without its own `CustomLog` logs to `/var/log/apache2/other_vhosts_access.log` on Ubuntu, in `vhost_combined` format. The **first field is the vhost**, which section 9 uses to count traffic per site.

### Which vhost is busy right now: mod_status

```bash
# Ubuntu enables mod_status by default and allows it from localhost only
curl -s 'http://127.0.0.1/server-status?auto' | head -20      # machine-readable counters
curl -s http://127.0.0.1/server-status | sed 's/<[^>]*>/ /g' | grep -E '\.example\.com' | head -20   # active requests with their vhost
```

→ The full page lists every active request with its **VHost** and client. That's a live view of which applications are in use at this moment. If the page 404s, mod_status isn't enabled, or the vhost answering on 127.0.0.1 proxies `/` elsewhere (exclude it with `ProxyPass /server-status !`). If the VHost column is missing, `ExtendedStatus` is off.

### Nginx: nginx -T

```bash
sudo nginx -T 2>/dev/null | grep -nE '^\s*(server_name|listen|root|proxy_pass|fastcgi_pass|access_log|error_log)\b|# configuration file'
```

→ `nginx -T` prints the whole merged config with `# configuration file /etc/nginx/sites-enabled/X:` markers. The grep turns it into a vhost map just like `apache2ctl -S`. In Nginx, the default server is the one marked `default_server` on the `listen` line, otherwise the first one loaded for that address and port.

### Traefik and Dokploy: routers and labels

After the migration, Traefik is the proxy. Its "vhosts" are **routers** (a `Host()` rule) that point to **services** (backend URL or container port). They come from two sources: Docker labels and dynamic files.

```bash
# Router rules from Docker labels on every running container (Compose apps, many Dokploy apps)
for c in $(docker ps --format '{{.Names}}'); do
  docker inspect --format '{{json .Config.Labels}}' "$c" \
  | jq -r --arg c "$c" 'to_entries[] | select(.key | test("^traefik\\.http\\.routers\\..+\\.rule$")) | "\($c)\t\(.value)"'
done

# All Traefik labels of one container (rule, entrypoints, tls, service port)
docker inspect --format '{{json .Config.Labels}}' CONTAINER | jq 'with_entries(select(.key | startswith("traefik.")))'

# Routers defined in Dokploy's dynamic file-provider config (path used by current Dokploy installs)
sudo grep -rnE 'rule:|url:|service:' /etc/dokploy/traefik/dynamic/ 2>/dev/null

# If the Traefik API/dashboard is enabled on an internal entrypoint:
curl -s http://127.0.0.1:8080/api/http/routers | jq -r '.[] | "\(.name)\t\(.rule)\t\(.service)\t\(.status)"'
```

→ A router rule like ``Host(`crm.example.com`)`` plus `loadbalancer.server.port=3000` tells you the domain and the container port. Swarm services carry the same labels on the *service* (`docker service inspect SERVICE --format '{{json .Spec.Labels}}'`). Dokploy's UI shows the same mapping under each application's **Domains** tab ([Dokploy docs](https://docs.dokploy.com/)). See [Traefik docs](https://doc.traefik.io/traefik/) for the label syntax.

→ When no router matches, Traefik answers **404** and serves its self-signed `TRAEFIK DEFAULT CERT`. That's the signature of "the request reached Traefik but no route matched", the Traefik equivalent of Apache's default vhost.

### Other proxies: dump the config the same way

| Proxy | Map domains → backends |
|---|---|
| HAProxy | `haproxy -c -f /etc/haproxy/haproxy.cfg` to validate, then the grep below |
| Caddy | `caddy adapt --config /etc/caddy/Caddyfile --pretty` (JSON of routes), or read the Caddyfile |
| IIS | `Get-IISSite` or `appcmd list sites` (section 11) |
| Kubernetes Ingress | `kubectl get ingress -A` (HOSTS column), then `kubectl describe ingress` for backends |

```bash
# HAProxy: frontends, binds, ACLs and the backends they route to
sudo grep -nE '^\s*(frontend|backend|bind|acl|use_backend|default_backend|server)\b' /etc/haproxy/haproxy.cfg
```

---

## 6. Containers: Docker, Compose, Swarm, Podman

> 📚 **Study path:** 1) KodeKloud: *Docker Training Course for the Absolute Beginner* — Docker Run Commands (Port Mapping, Inspect and Logs) and Docker Compose ([course](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner)) · 2) KodeKloud: *Docker Certified Associate* — Docker Engine → *Restart Policies* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)), then the Docker Swarm section → *Docker Overlay Network* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page)) · 3) Note: [Docker reference](14-docker-containers.md), [Learn: Docker](30-learn-docker.md) · 4) Video: KodeKloud *How Docker Networking Actually Works* ([YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 5) Practice: KodeKloud Docker playground ([link](https://kodekloud.com/playgrounds/playground-docker)), then drill 4.

**Level:** [L2 · Mid] for docker ps, inspect, docker-proxy and Compose labels · [L3 · Senior] for Swarm services, the ingress mesh and Dokploy hosts.

When `ss` names `docker-proxy`, `dockerd`, `rootlessport`, `rootlesskit` or `pasta`, or names a process whose cgroup is `docker-….scope`, the application is a container. These commands turn "a container" into "this Compose project, in this directory, with these logs".

### docker ps: names, ports, status

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'   # include stopped ones
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E ':8081->'       # which container publishes host port 8081?
```

```
NAMES                   PORTS                                         STATUS
metabase                0.0.0.0:8081->3000/tcp, [::]:8081->3000/tcp   Up 6 days
crm-app-4fd1ab-web-1    3000/tcp                                      Up 2 days
redis                   6379/tcp                                      Up 6 days
```

→ `0.0.0.0:8081->3000/tcp` is **published**: host port 8081 forwards to container port 3000, on every host IPv4 address (and IPv6 through the `[::]` entry).

→ `3000/tcp` or `6379/tcp` alone is only **exposed**. No host port exists, and only containers on the same Docker network can connect. That's the normal, desired state for anything behind Traefik.

→ `127.0.0.1:18000->8000/tcp` would mean published on loopback only. That's the right pattern for temporary test ports, and it doesn't bypass the firewall towards the outside.

### docker port and docker inspect

```bash
docker port metabase                                         # all mappings of one container
docker inspect -f '{{json .NetworkSettings.Ports}}' metabase | jq
docker inspect -f '{{.HostConfig.NetworkMode}} restart={{.HostConfig.RestartPolicy.Name}}' metabase
```

```
3000/tcp -> 0.0.0.0:8081
3000/tcp -> [::]:8081

{
  "3000/tcp": [
    { "HostIp": "0.0.0.0", "HostPort": "8081" },
    { "HostIp": "::", "HostPort": "8081" }
  ]
}

metabase_default restart=unless-stopped
```

→ `NetworkMode` = `host` means **no port mapping at all**: the app binds directly in the host namespace, `ss` shows the real process (for example `traefik` or `java`), and `docker port` prints nothing. Its cgroup still says `docker-ID.scope`.

→ The restart policy matters when you stop it (section 10). `always` and `unless-stopped` behave differently after a reboot.

### From docker-proxy back to the container

When `ss` shows only `docker-proxy`, its command line names the container's IP and port:

```bash
ps -o pid,args -C docker-proxy
# map container IPs to names on every network
docker ps -q | xargs -r docker inspect --format '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}'
# the NAT rule behind it (iptables-nft on Ubuntu; Docker 29+ can use nftables directly only if "firewall-backend": "nftables"
# is set, experimental and not allowed in Swarm mode, so a Dokploy host always has these iptables rules)
sudo iptables -t nat -L DOCKER -n --line-numbers
```

```
    PID COMMAND
   3302 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8081 -container-ip 172.18.0.3 -container-port 3000
   3309 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8081 -container-ip 172.18.0.3 -container-port 3000

/metabase 172.18.0.3
/crm-app-4fd1ab-web-1 10.0.1.14
/redis 172.17.0.2

Chain DOCKER (2 references)
num  target     prot opt source               destination
1    DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8081 to:172.18.0.3:3000
```

→ 172.18.0.3 is `metabase`. The DNAT rule shows the same mapping at kernel level. If you only see the rule and no docker-proxy, the userland proxy is disabled. Same container, no LISTEN socket.

### Container to host PID and back

```bash
# Container → host PID (main process) and all its processes as seen from the host
docker inspect -f '{{.State.Pid}}' metabase
docker top metabase -eo pid,ppid,user,cmd

# Use HOST tools inside the container's network namespace (no tools needed in the image)
sudo nsenter -t "$(docker inspect -f '{{.State.Pid}}' metabase)" -n ss -ltnp

# Host PID → container: the cgroup path carries the full container ID
cat /proc/3420/cgroup
docker ps --no-trunc --format '{{.ID}} {{.Names}}' | grep 8c1f0e5b2d7a
```

```
3420

PID     PPID    USER    CMD
3420    3398    2000    java -jar /app/metabase.jar

State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      50                 *:3000            *:*    users:(("java",pid=3420,fd=12))

0::/system.slice/docker-8c1f0e5b2d7a9e4f60b1c3d5e7f9a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2.scope
8c1f0e5b2d7a9e4f60b1c3d5e7f9a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2 metabase
```

→ Inside its namespace, Metabase listens on `*:3000` as PID 3420, which is a host PID; `nsenter` with `ss -p` shows host PIDs. If the app listened on `127.0.0.1:3000` here, the published port and Traefik would both get "connection refused" / 502. That's the most common container networking bug ([Docker reference](14-docker-containers.md)).

→ The parent PID 3398 is `containerd-shim-runc-v2`. That's how you recognize a container process in `ps` output.

### Compose projects: which stack is this?

Compose labels every container with its project, service and **the directory and file it was started from**. That's the fastest route from a container to "whose app is this and where is its config".

```bash
docker compose ls                                  # projects, status and their compose files
docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Label "com.docker.compose.service"}}' | column -t
docker inspect -f '{{index .Config.Labels "com.docker.compose.project.working_dir"}} {{index .Config.Labels "com.docker.compose.project.config_files"}}' metabase
```

```
NAME             STATUS       CONFIG FILES
metabase         running(1)   /opt/metabase/docker-compose.yml
crm-app-4fd1ab   running(1)   /etc/dokploy/compose/crm-app-4fd1ab/code/docker-compose.yml

metabase              metabase        metabase
crm-app-4fd1ab-web-1  crm-app-4fd1ab  web
redis

/opt/metabase /opt/metabase/docker-compose.yml
```

→ `redis` has **no** Compose labels, so someone created it with a plain `docker run`. Its exact original command line isn't stored anywhere. Rebuild it from `docker inspect` (image, env, mounts, ports, restart policy) before you remove it, or you may never be able to recreate it.

→ The `crm-app-4fd1ab` project lives under `/etc/dokploy/compose/`, which means Dokploy deployed it. Manage it from the Dokploy UI, not with `docker compose` by hand, or Dokploy's next deploy undoes your change.

### Swarm services and the ingress mesh

Dokploy runs Docker in **Swarm mode**, so on a Dokploy host some "containers" are really tasks of Swarm services.

```bash
docker info --format '{{.Swarm.LocalNodeState}}'           # "active" = this node is in a swarm
docker service ls
docker service inspect grafana --format '{{json .Endpoint.Ports}}' | jq
docker service ps grafana --no-trunc                        # tasks, node, state, errors
sudo ss -ltnp | grep dockerd                                # ingress ports reserved by dockerd
```

```
ID             NAME               MODE         REPLICAS   IMAGE                              PORTS
q2m9x8ad1f0k   dokploy            replicated   1/1        dokploy/dokploy:latest             *:3000->3000/tcp
7hn2c4k0z1pe   dokploy-postgres   replicated   1/1        postgres:16
m3k8s0d9f7g2   shop-api-9d3e7a    replicated   1/1        harbor.example.com/shop/api:2.0.1
z9y8x7w6v5u4   grafana            replicated   1/1        grafana/grafana:11.2.0             *:3300->3000/tcp

[
  {
    "Protocol": "tcp",
    "TargetPort": 3000,
    "PublishedPort": 3300,
    "PublishMode": "ingress"
  }
]

LISTEN 0      4096       *:3300       *:*    users:(("dockerd",pid=812,fd=61))
```

→ `PublishMode: ingress` → port 3300 is open on **every swarm node** and owned by `dockerd`. `host` → only where a task runs, through docker-proxy and NAT. Check the mode on your own install before you assume either.

→ Services without PORTS (`dokploy-postgres`, `shop-api-…`) are reachable only over overlay networks such as `dokploy-network`. Traefik reaches the app that way, with no host port involved.

### Dokploy hosts: what to expect

On a typical current Dokploy install (verify on yours, since layouts change between versions):

| Component | Kind | Ports on the host |
|---|---|---|
| `dokploy` (UI and API) | Swarm service | 3000/tcp, published in **host** mode by the installer, so `ss` shows `docker-proxy` (not `dockerd`) on 3000 |
| `dokploy-traefik` | a plain container with `restart: always` in current versions (older versions ran it as a Swarm service) | 80/tcp, 443/tcp, 443/udp |
| `dokploy-postgres` (older installs also have `dokploy-redis`) | Swarm services | none |
| your applications | Swarm services or Compose projects | none. Traefik routes to them over `dokploy-network` |

```bash
docker ps --filter name=dokploy --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
docker service ls --filter name=dokploy
docker network inspect dokploy-network --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
sudo ls /etc/dokploy/ /etc/dokploy/traefik/            # traefik.yml (static) and dynamic/ (routes)
```

Dokploy's installer checks that 80, 443 and 3000 are free and stops with an error when something already listens there. That's exactly the Apache conflict ([Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting), [case study](21-case-apache-443-dokploy.md)).

### Podman equivalents

```bash
podman ps --format "table {{.Names}} {{.Ports}} {{.Status}}"
podman port CONTAINER
podman inspect -f '{{.State.Pid}}' CONTAINER
podman logs --tail 100 -f CONTAINER
sudo ss -ltnp | grep -E 'rootlessport|pasta|slirp4netns|conmon'   # who holds rootless ports
systemctl --user list-units --type=service                          # Quadlet / generated units (rootless)
```

→ **Rootless** Podman's published ports are held by a helper in the host namespace: `rootlessport`, or `pasta` on Podman 5. They run as the user, and their cgroup is under `user@UID.service`. **Rootful** Podman uses NAT rules (netavark). Depending on the version, `conmon` may also hold the port, or nothing shows in `ss` at all.

→ Rootless containers started as systemd user units die at logout unless lingering is enabled (`loginctl enable-linger USER`). That's a common reason a port disappears overnight.

### Container logs: docker logs, service logs, json-file

```bash
docker logs --tail 100 -f CONTAINER                 # stdout/stderr of the main process
docker logs --since 1h CONTAINER 2>&1 | grep -iE 'error|listen|bind'
docker compose -p PROJECT logs --tail 100 SERVICE   # one Compose service (by project name)
docker service logs --tail 100 -f SERVICE           # all tasks of a Swarm service, merged
docker info --format '{{.LoggingDriver}}'           # json-file (default), local, journald...
docker inspect -f '{{.LogPath}}' CONTAINER          # the json-file on disk
journalctl CONTAINER_NAME=CONTAINER                  # when the driver is journald
```

```
/var/lib/docker/containers/8c1f0e5b2d7a…/8c1f0e5b2d7a…-json.log
```

→ `docker logs` shows only what the process writes to **stdout/stderr**. If the app writes to files *inside* the container (`/var/log/app/*.log`, Tomcat's `logs/`), look there with `docker exec CONTAINER ls -l /var/log/app` or in the mounted volume. Official images send their logs to stdout for this reason: nginx symlinks `/var/log/nginx/access.log` and `error.log` to `/dev/stdout` and `/dev/stderr`, and httpd's config writes to `/proc/self/fd/1` and `/proc/self/fd/2`.

→ The default json-file driver doesn't rotate. Set `log-opts` `max-size` and `max-file` in `/etc/docker/daemon.json` (see [Docker reference](14-docker-containers.md)).

---

## 7. Kubernetes: who answers on a node port

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts (kube-proxy, Services), then Networking ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Services → *Troubleshooting Internal Networking* ([lesson](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page)) · 3) Note: [Kubernetes reference](15-kubernetes.md), [Learn: Kubernetes](31-learn-kubernetes.md) · 4) Practice: KodeKloud Kubernetes multi-cluster playground ([link](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster)) or [Killercoda](https://killercoda.com/), then drill 7.

**Level:** [L3 · Senior] (CKA track). A Mid-level engineer should at least know that NodePorts have no listening socket.

On a Kubernetes node, most "who owns this port" questions are answered by **Service objects and kube-proxy rules**, not by processes. The method is to ask the API first and the node second.

### Services: NodePort and LoadBalancer

```bash
kubectl get svc -A -o wide | grep -E 'NAMESPACE|NodePort|LoadBalancer'     # keep the header line
# Which Service owns NodePort 30080?
kubectl get svc -A -o json \
  | jq -r '.items[] | select(any(.spec.ports[]?; .nodePort == 30080)) | "\(.metadata.namespace)/\(.metadata.name)"'
# Which pods are behind it?
kubectl -n demo get endpointslices -l kubernetes.io/service-name=web
```

```
NAMESPACE       NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                      AGE   SELECTOR
ingress-nginx   ingress-nginx-controller   LoadBalancer   10.96.120.15   192.0.2.240   80:31080/TCP,443:31443/TCP   40d   app.kubernetes.io/name=ingress-nginx
demo            web                        NodePort       10.96.44.7     <none>        80:30080/TCP                 3d    app=web

demo/web

NAME        ADDRESSTYPE   PORTS   ENDPOINTS                AGE
web-7xk2p   IPv4          8080    10.244.1.12,10.244.2.7   3d
```

→ `80:30080/TCP` reads as *Service port 80, NodePort 30080*. The NodePort is open on **every node**, even nodes without a `web` pod. The traffic is forwarded to the endpoints (pod IP:8080).

→ A `LoadBalancer` Service on bare metal gets its EXTERNAL-IP from something like MetalLB. In L2 mode, one node answers ARP for 192.0.2.240, and *that* node is "who owns the IP". It can move between nodes.

→ No endpoints → the selector matches no Ready pods → connections are refused or reset even though the NodePort rule exists ([Kubernetes reference](15-kubernetes.md)).

### hostPort and hostNetwork pods

These are the two ways a pod grabs a port on the node itself. They're the usual culprits when something on the node collides with a pod, or when a pod is stuck **Pending** with *"didn't have free ports for the requested pod ports"*.

```bash
# Pods that declare a hostPort (namespace/pod, node, port)
kubectl get pods -A -o json | jq -r '
  .items[] | . as $p | .spec.containers[] | .ports[]? | select(.hostPort)
  | "\($p.metadata.namespace)/\($p.metadata.name)\t\($p.spec.nodeName)\thostPort=\(.hostPort)/\(.protocol // "TCP")"'

# Pods running in the node's network namespace
kubectl get pods -A -o json | jq -r '
  .items[] | select(.spec.hostNetwork == true)
  | "\(.metadata.namespace)/\(.metadata.name)\t\(.spec.nodeName)\tports=\([.spec.containers[].ports[]?.containerPort] | join(","))"'
```

```
ingress-nginx/ingress-nginx-controller-5d8f7c9b6-xk2lp	node-2	hostPort=80/TCP
ingress-nginx/ingress-nginx-controller-5d8f7c9b6-xk2lp	node-2	hostPort=443/TCP
monitoring/node-exporter-x8f2d	node-1	hostPort=9100/TCP

kube-system/etcd-cp-1	cp-1	ports=
kube-system/kube-apiserver-cp-1	cp-1	ports=
kube-system/kube-proxy-7tq4m	node-1	ports=
monitoring/node-exporter-x8f2d	node-1	ports=9100
```

→ For hostNetwork pods, the API server fills `hostPort` with the `containerPort` automatically. That's why the first query lists the hostNetwork `node-exporter` pod too (`hostPort=9100`).

→ Control-plane static pods show no declared ports, yet they listen on 6443, 2379–2380, 10257 and 10259. `ss -ltnp` on the control-plane node shows the real binaries, because hostNetwork means real sockets.

### kube-proxy rules: iptables, IPVS, nftables

```bash
# Which mode is kube-proxy in? (run on a node)
curl -s http://127.0.0.1:10249/proxyMode; echo
kubectl -n kube-system get cm kube-proxy -o yaml | grep -E '^\s*mode:'     # kubeadm clusters

# iptables mode: the NodePort rule (comment = namespace/service:portname)
sudo iptables-save -t nat | grep -E '^-A KUBE-NODEPORTS' | grep -- '--dport 30080'
# IPVS mode: one virtual server per node IP and NodePort
sudo ipvsadm -Ln | grep -A3 ':30080'
# nftables mode (GA in recent releases)
sudo nft list table ip kube-proxy | grep 30080
# hostPort rules from the CNI portmap plugin
sudo iptables-save -t nat | grep -E 'CNI-HOSTPORT-DNAT|CNI-DN-' | grep -- '--dport 80'
```

```
iptables

-A KUBE-NODEPORTS -p tcp -m comment --comment "demo/web:http" -m tcp --dport 30080 -j KUBE-EXT-QK3T2ZB4HMQK7ACX

TCP  192.0.2.21:30080 rr
  -> 10.244.1.12:8080             Masq    1      0          0
  -> 10.244.2.7:8080              Masq    1      0          0
```

→ The rule's comment names the Service directly (`demo/web`). This is how you answer "who owns 30080" from the node alone, without `kubectl`.

→ With **Cilium's kube-proxy replacement**, none of these tables contain the Service. Ask Cilium instead: `kubectl -n kube-system exec ds/cilium -- cilium-dbg service list` (older releases: `cilium service list`).

### On the node: crictl and cgroups

```bash
sudo crictl ps                                       # running containers, with their pod names
sudo crictl pods --name ingress                      # pod sandboxes
sudo crictl inspect CONTAINER_ID | jq '.info.pid'    # container → host PID
# host PID → pod: take the 64-hex ID from the cgroup, then ask crictl
grep -oE 'cri-containerd-[0-9a-f]{64}' /proc/PID/cgroup
sudo crictl inspect 4b1c9e0d2f3a1 | jq -r '.status.labels | "\(.["io.kubernetes.pod.namespace"])/\(.["io.kubernetes.pod.name"])"'
```

```
CONTAINER       IMAGE           CREATED      STATE     NAME         ATTEMPT   POD ID          POD
4b1c9e0d2f3a1   8f2c1d0e9b7a6   3 days ago   Running   controller   0         9a8b7c6d5e4f3   ingress-nginx-controller-5d8f7c9b6-xk2lp

ingress-nginx/ingress-nginx-controller-5d8f7c9b6-xk2lp
```

### Logs: kubectl logs and on-node files

```bash
kubectl -n NS logs POD -c CONTAINER --tail 100      # current container
kubectl -n NS logs POD --previous                   # the crashed instance
kubectl -n NS logs -l app=web --tail 50 --prefix    # all pods of an app, lines prefixed by pod
sudo crictl logs --tail 100 CONTAINER_ID             # on the node, when the API is down
sudo ls /var/log/pods/                               # NS_POD_UID/CONTAINER/0.log
```

→ For "which app is behind this URL", the **ingress controller's access log** is gold. Each line names the host, the upstream Service and the pod IP that served it.

### Static pods and control-plane ports

On kubeadm control-plane nodes, `kube-apiserver` (6443), `etcd` (2379–2380), `kube-scheduler` (10259) and `kube-controller-manager` (10257) are **static pods**. The kubelet runs them from files in `/etc/kubernetes/manifests/`.

```bash
ls /etc/kubernetes/manifests/
kubectl -n kube-system get pod kube-apiserver-cp-1 -o jsonpath='{.metadata.annotations.kubernetes\.io/config\.source}'; echo
```

```
etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
file
```

→ `config.source = file` means `kubectl delete` only removes the *mirror* object, and the kubelet recreates it at once. To stop a static pod, move its manifest out of the directory (section 10). This trick is common in CKA tasks.

---

## 8. The read-only inventory script

> 📚 **Study path:** 1) KodeKloud: *Shell Scripts for Beginners* — Shebang (Exit Codes, Functions, Tips & Tricks – ShellCheck & IDE) ([course](https://kodekloud.com/courses/shell-scripts-for-beginners)) · 2) KodeKloud: *Advanced Bash Scripting* — Streams, Good Practices Applied, awk ([course](https://kodekloud.com/courses/advanced-bash-scripting)) · 3) Read: [Bash Guide](https://mywiki.wooledge.org/BashGuide) · 4) Practice: paste the script into [ShellCheck](https://www.shellcheck.net/), then drill 2.

**Level:** [L1 · Junior] to run it and read its output · [L2 · Mid] to understand every part · [L4 · Lead] to run it across hosts and diff it daily.

One command that prints the table you would otherwise build by hand: every listener with its PID, process, systemd unit, container, current connection count and a log hint, followed by the ports that answer through **rules** (Docker publishing, Swarm, kube-proxy, hostPort, REDIRECT, IPVS) and may have no listener at all.

It only *reads*: `ss`, `/proc`, `systemctl list-sockets`, `docker inspect`, `crictl inspect`, `iptables-save` and `ipvsadm -Ln`. It's safe on production. Run it as root, or PIDs owned by other users are missing.

### The script

```bash
#!/usr/bin/env bash
# port-inventory.sh — READ-ONLY inventory of listening sockets on a Linux host.
# Columns: PROTO  ADDRESS:PORT  PID  PROCESS  UNIT  CONTAINER  CONNS  LOG_HINT
# Usage:   sudo bash port-inventory.sh
# Reads only: ss, /proc, systemctl list-sockets, docker/crictl inspect, iptables-save, ipvsadm -Ln

set -o nounset
export LC_ALL=C
TAB=$'\t'

[ "$(id -u)" -eq 0 ] || echo "WARNING: not root - PIDs of other users' sockets will be missing" >&2

have()      { command -v "$1" >/dev/null 2>&1; }
docker_ok() { have docker && docker info >/dev/null 2>&1; }
row()       { local IFS=$TAB; echo "$*"; }
fmt()       { if have column; then column -t -s "$TAB"; else cat; fi; }

# ---------- 1. Container lookups, computed once ----------
declare -A CID_NAME=() CIP_NAME=()
if docker_ok; then
  while read -r id name ips; do
    CID_NAME[$id]=${name#/}
    for ip in $ips; do CIP_NAME[$ip]=${name#/}; done
  done < <(docker ps -q | xargs -r docker inspect \
             --format '{{.Id}} {{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}')
fi

# ---------- 2. Helpers ----------
unit_of() {                       # PID -> systemd unit or scope (from the cgroup path)
  local cg
  cg=$(sed -n 's|^0::||p' "/proc/$1/cgroup" 2>/dev/null)                                   # cgroup v2
  [ -n "$cg" ] || cg=$(sed -n 's|^[0-9]*:name=systemd:||p' "/proc/$1/cgroup" 2>/dev/null)  # cgroup v1
  if [ -n "$cg" ]; then basename "$cg"; else echo "-"; fi
}

container_of() {                  # PID -> container / pod name, or "-"
  local pid=$1 comm cg id ip name=""
  comm=$(cat "/proc/$pid/comm" 2>/dev/null)
  if [ "$comm" = "docker-proxy" ]; then                       # host side of a -p mapping
    ip=$(tr '\0' ' ' < "/proc/$pid/cmdline" | grep -oE -- '-container-ip [^ ]+' | cut -d' ' -f2)
    if [ -n "$ip" ]; then echo "${CIP_NAME[$ip]:-ip:$ip}(docker-proxy)"; else echo "docker-proxy"; fi
    return
  fi
  [ "$comm" = "dockerd" ] && { echo "swarm-ingress"; return; }
  cg=$(cat "/proc/$pid/cgroup" 2>/dev/null)
  id=$(grep -oE '(docker|cri-containerd|libpod)-[0-9a-f]{64}' <<<"$cg" | head -n1 | grep -oE '[0-9a-f]{64}')
  [ -n "$id" ] || id=$(grep -oE '/(docker|kubepods)/.*[0-9a-f]{64}' <<<"$cg" | grep -oE '[0-9a-f]{64}$' | head -n1)
  [ -n "$id" ] || { echo "-"; return; }
  name=${CID_NAME[$id]:-}
  if [ -z "$name" ] && have crictl; then
    name=$(crictl inspect "$id" 2>/dev/null | grep -m1 -oE '"io.kubernetes.pod.name": *"[^"]+"' | cut -d'"' -f4)
    [ -n "$name" ] && name="pod:$name"
  fi
  echo "${name:-cid:${id:0:12}}"
}

log_hint() {                      # best guess at where this process logs
  local pid=$1 unit=$2 ctr=$3 files out
  case $ctr in
    -) ;;
    pod:*)         echo "kubectl logs ${ctr#pod:} -n NS"; return ;;
    swarm-ingress) echo "docker service logs SERVICE"; return ;;
    cid:*)         echo "podman/docker logs ${ctr#cid:}"; return ;;
    *)             echo "docker logs ${ctr%%(*}"; return ;;
  esac
  files=$(ls -l "/proc/$pid/fd" 2>/dev/null | grep -oE '/[^ ]+\.log$' | sort -u | head -n3 | paste -sd, -)
  [ -n "$files" ] && { echo "$files"; return; }
  out=$(readlink "/proc/$pid/fd/1" 2>/dev/null)
  case $out in
    socket:*) echo "journalctl -u $unit" ;;
    pipe:*)   echo "stdout piped to parent (pm2/supervisord?): pstree -ps $pid" ;;
    ""|/dev/null) if [[ $unit == *.service ]]; then echo "journalctl -u $unit"; else echo "-"; fi ;;
    *)        echo "$out" ;;
  esac
}

# ---------- 3. One row per listening socket ----------
listeners() {
  row PROTO ADDRESS:PORT PID PROCESS UNIT CONTAINER CONNS LOG_HINT
  ss -Htulpn | while read -r proto _state _rq _sq local _peer users; do
    local pid name unit svc ctr hint conns port
    users=${users:-}; port=${local##*:}; svc=""
    pid=$(grep -oE 'pid=[0-9]+' <<<"$users" | cut -d= -f2 | sort -n | head -n1)
    conns="-"
    [ "$proto" = "tcp" ] && conns=$(ss -Htn state established "( sport = :$port )" | wc -l)
    if [ -z "$pid" ]; then
      row "$proto" "$local" - "(no process: kernel socket, or not root)" - - "$conns" -
      continue
    fi
    name=$(cat "/proc/$pid/comm" 2>/dev/null || echo "?")
    unit=$(unit_of "$pid"); ctr=$(container_of "$pid"); hint=$(log_hint "$pid" "$unit" "$ctr")
    if [ "$pid" = 1 ]; then                                  # PID 1 holds it = socket activation
      read -r unit svc < <(systemctl list-sockets --no-legend 2>/dev/null \
                             | awk -v p=":$port" '$1 ~ p"$" {print $2, $3; exit}') || true
      unit=${unit:-"?.socket"}; hint="journalctl -u ${svc:-?}"
    fi
    row "$proto" "$local" "$pid" "$name" "$unit" "$ctr" "$conns" "$hint"
  done
}

# ---------- 4. Ports answered by rules, not sockets ----------
rule_owned() {
  row SOURCE PORT TARGET
  if docker_ok; then
    docker ps --format '{{.Names}}\t{{.Ports}}' | while IFS=$TAB read -r n p; do
      grep -oE '[0-9]+->[0-9]+/(tcp|udp)' <<<"$p" | sort -u | while read -r m; do
        row docker-publish "${m%%->*}/${m##*/}" "$n:${m#*->}"
      done
    done
    docker service ls --format '{{.Name}}\t{{.Ports}}' 2>/dev/null | while IFS=$TAB read -r n p; do
      grep -oE '[0-9]+->[0-9]+/(tcp|udp)' <<<"$p" | sort -u | while read -r m; do
        row swarm-publish "${m%%->*}/${m##*/}" "service $n:${m#*->}"
      done
    done
  fi
  if have iptables-save; then
    iptables-save -t nat 2>/dev/null | awk -v OFS='\t' '
      /^-A KUBE-NODEPORTS/ && /--dport/ { c="-"; d="-"
        for (i = 1; i <= NF; i++) { if ($i == "--comment") c = $(i+1); if ($i == "--dport") d = $(i+1) }
        gsub(/"/, "", c); print "k8s-nodeport", d, c }
      /^-A CNI-DN-/ && /--to-destination/ { d="-"; t="-"
        for (i = 1; i <= NF; i++) { if ($i == "--dport") d = $(i+1); if ($i == "--to-destination") t = $(i+1) }
        print "k8s-hostport", d, t }
      /-j REDIRECT/ && /--to-ports/ { d="-"; t="-"
        for (i = 1; i <= NF; i++) { if ($i == "--dport") d = $(i+1); if ($i == "--to-ports") t = $(i+1) }
        print "redirect", d, "local port " t }' | sort -u
  fi
  if have ipvsadm; then
    ipvsadm -Ln 2>/dev/null | awk -v OFS='\t' '/^(TCP|UDP)/ {print "ipvs", $2, "virtual server"}'
  fi
}

echo "== Listening sockets on $(hostname) at $(date -Is) =="
listeners | fmt
echo
echo "== Ports answered by rules (may have NO listening socket above) =="
rule_owned | fmt
```

### How each part works

**Part 1, container lookups.** One `docker inspect` call for all running containers builds two maps, *full container ID → name* and *container IP → name*. Calling Docker once per port would be slow on a busy host. If Docker isn't installed or not running, the maps stay empty and the script carries on.

**Part 2, `unit_of`.** This reads the cgroup path from `/proc/PID/cgroup` (the `0::` line on cgroup v2, the `name=systemd` line on v1). Its last component is the unit (`apache2.service`), the scope (`docker-ID.scope`, `session-12.scope`) or the pod slice. That's the same evidence you used by hand in section 4, Step 3.

**Part 2, `container_of`.** It handles three cases. A **docker-proxy** names the container IP in its arguments, which the IP map turns into a name. **dockerd** holding a port means the Swarm ingress. Otherwise it pulls a 64-hex container ID out of the cgroup (`docker-`, `cri-containerd-`, `libpod-` prefixes, or the cgroupfs layout) and resolves it with the Docker map or `crictl`.

**Part 2, `log_hint`.** For containers it suggests the right logs command. For host processes it prefers **log files the process holds open** (from `/proc/PID/fd`), then decides from **where stdout points**: a socket means the journal, a pipe means a parent such as pm2 collects it, and a file is shown as is.

**Part 3, `listeners`.** This parses `ss -Htulpn` (no header, so it parses cleanly), takes the **lowest PID** in the users list as the master, and counts current ESTABLISHED connections to that port, which is cheap first evidence of use. When the owner is **PID 1**, it looks the port up in `systemctl list-sockets` to name the socket unit and the service it activates.

> CONNS undercounts Docker-published ports. External connections are DNAT-ed straight into the container and never become sockets on the host, so only connections that went through docker-proxy (mostly from the host itself) are counted. For the real number, count conntrack entries (`sudo conntrack -L -p tcp --dport 8081 2>/dev/null | grep -c ESTABLISHED`, package `conntrack`) or run `ss` inside the container with `nsenter`.

**Part 4, `rule_owned`.** These are ports that may have no socket at all: Docker and Swarm published ports, kube-proxy NodePorts (the rule comment names the Service), CNI hostPorts, local `REDIRECT` rules, and IPVS virtual servers. This is the part that answers "nothing in ss but the port answers".

### Sample output

```
== Listening sockets on web01 at 2026-10-03T10:20:41+00:00 ==
PROTO  ADDRESS:PORT      PID   PROCESS          UNIT                      CONTAINER                CONNS  LOG_HINT
udp    127.0.0.54:53     598   systemd-resolve  systemd-resolved.service  -                        -      journalctl -u systemd-resolved.service
udp    127.0.0.53%lo:53  598   systemd-resolve  systemd-resolved.service  -                        -      journalctl -u systemd-resolved.service
tcp    127.0.0.53%lo:53  598   systemd-resolve  systemd-resolved.service  -                        0      journalctl -u systemd-resolved.service
tcp    127.0.0.1:3306    1120  mysqld           mysql.service             -                        6      /var/log/mysql/error.log
tcp    127.0.0.1:33060   1120  mysqld           mysql.service             -                        0      /var/log/mysql/error.log
tcp    127.0.0.1:25      1544  master           postfix@-.service         -                        0      journalctl -u postfix@-.service
tcp    127.0.0.1:3001    2210  node             pm2-deploy.service        -                        4      stdout piped to parent (pm2/supervisord?): pstree -ps 2210
tcp    0.0.0.0:8081      3302  docker-proxy     docker.service            metabase(docker-proxy)   1      docker logs metabase
tcp    [::]:8081         3309  docker-proxy     docker.service            metabase(docker-proxy)   1      docker logs metabase
tcp    *:22              1     systemd          ssh.socket                -                        2      journalctl -u ssh.service
tcp    *:80              1201  apache2          apache2.service           -                        3      /var/log/apache2/crm_access.log,/var/log/apache2/crm_error.log,/var/log/apache2/error.log
tcp    *:443             1201  apache2          apache2.service           -                        18     /var/log/apache2/crm_access.log,/var/log/apache2/crm_error.log,/var/log/apache2/error.log

== Ports answered by rules (may have NO listening socket above) ==
SOURCE          PORT      TARGET
docker-publish  8081/tcp  metabase:3000/tcp
```

How a senior reads it:

→ **Public-facing:** 22 (socket-activated SSH), 80/443 (Apache, 18 live HTTPS connections) and 8081 (Metabase in Docker, which bypasses UFW). Everything else is loopback-only.

→ **The Node app on 3001** has four connections. They're Apache's `ProxyPass` from the crm vhost, so it's in use, but only *through* Apache. Its logs are in pm2, not in the journal.

→ **To free 443 for Traefik**, only one row matters: `apache2.service`. The question becomes "move or retire the three vhosts behind it" (sections 5, 9 and 10).

### Extending it

Useful additions once you're comfortable with the base script:

- An **ENABLED** column (`systemctl is-enabled UNIT`) shows what comes back after a reboot.
- An **ACTIVE SINCE** column (`systemctl show UNIT -p ActiveEnterTimestamp --value`) shows what changed recently.
- **Run it from cron daily** into a dated file and `diff` today against yesterday. New listeners are either a deploy you forgot or something you need to know about.
- **Run it across hosts** with `ssh HOST 'sudo bash -s' < port-inventory.sh` (needs passwordless sudo on HOST, because the script occupies stdin and sudo can't prompt) or an Ansible `script` task with `become: true`, and merge the outputs into one inventory.
- Port **ranges** published by Docker (`8000-8010->8000-8010/tcp`) aren't matched by the simple regex. Extend it if you use them.

Lint it with ShellCheck before you rely on it (your L0 drill), and keep it in your runbook repository.

---

## 9. Which services are still needed?

> 📚 **Study path:** 1) Note: section 4 of this module and [Logs & journal](06-logs-journal.md) (quick refresher) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment → *Locate and Analyze System Log Files* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 3) KodeKloud: *Advanced Bash Scripting* — awk and sed modules, for slicing access logs ([course](https://kodekloud.com/courses/advanced-bash-scripting)) · 4) Docs: Apache *Log Files* ([docs](https://httpd.apache.org/docs/2.4/logs.html)) · 5) Practice: run Evidence 2 on your lab vhosts and fill the inventory template.

**Level:** [L2 · Mid] for gathering the evidence · [L3 · Senior] for the keep/migrate/retire decision and the migration options.

"Is this still used?" is the question everyone answers from memory, and memory is usually wrong. Build the answer from evidence. Collect **at least three independent signals** before you retire anything, and keep the evidence in the inventory, because the client will ask.

| Signal | What it proves | Weakness |
|---|---|---|
| Live connections, sampled over a day or more | someone or something talks to it **now** | can't tell users from monitors and bots |
| Access logs (per vhost) | who used it, how often, and when last | needs retention; health checks inflate it |
| DNS still pointing here | the public name leads to this server | direct-IP clients ignore DNS |
| TLS certificate valid and renewed | someone cared recently | auto-renewal hides abandonment |
| Dependencies (other units, cron, certbot, apps) | other things break if it goes | easy to miss, so grep widely |
| Install date, last config change, last deploy | how alive the project is | old ≠ unused |
| A named owner who confirms | business need | people forget too, so combine with data |

### Evidence 1 — Live connections over time

```bash
# Sample ESTABLISHED connections per port every 5 minutes for 24 hours (read-only; run inside tmux)
for i in $(seq 1 288); do
  printf '%s' "$(date -Is)"
  for p in 80 443 3001 8080 8081; do
    printf ',%s' "$(ss -Htn state established "( sport = :$p )" | wc -l)"
  done
  echo
  sleep 300
done >> ~/conn-sample-$(hostname)-$(date +%F).csv
```

```
2026-10-03T10:25:00+00:00,3,18,4,0,1
2026-10-03T10:30:00+00:00,2,22,5,0,0
2026-10-03T10:35:00+00:00,1,15,3,0,0
```

→ Columns follow the port list (80, 443, 3001, 8080, 8081). Port **8080** (the wiki's Tomcat) shows zero connections across the samples. Remember that Apache's `ProxyPass` opens those connections only *while* a wiki request is running, so check the access log too (Evidence 2).

→ For Docker-published ports, count connections with conntrack or inside the container (section 8 note). Host-side `ss` doesn't see DNAT-ed connections.

### Evidence 2 — Access logs and last access

```bash
# Requests per vhost (Ubuntu's shared vhost log: first field = vhost:port), all rotations (14 days by default)
sudo zcat -f /var/log/apache2/other_vhosts_access.log* | awk '{print $1}' | sort | uniq -c | sort -rn

# Requests per day for one site, in date order
sudo zcat -f /var/log/apache2/crm_access.log* \
  | awk '{print substr($4, 2, 11)}' | sort -t/ -k3,3n -k2,2M -k1,1n | uniq -c

# Who really uses it: top client IPs, minus monitoring and bots
sudo zcat -f /var/log/apache2/crm_access.log* \
  | grep -viE 'uptimerobot|pingdom|kube-probe|bot|crawler|spider' \
  | awk '$1 != "192.0.2.5" {print $1}' | sort | uniq -c | sort -rn | head

# The last request and when the log was last written
sudo tail -n 1 /var/log/apache2/crm_access.log
sudo ls -l --time-style=long-iso /var/log/apache2/
```

```
  48211 app1.example.com:443
   1290 app1.example.com:80
    312 wiki.example.com:443

    1406 19/Sep/2026
    1512 20/Sep/2026
    ...
```

→ `crm.example.com` is **missing** from the shared log, and that's expected: a vhost with its own `CustomLog` (crm has `crm_access.log`) writes only there, never to `other_vhosts_access.log`. Count such sites from their own files, as the second command does. `app1.example.com:80` is the HTTP-to-HTTPS redirect vhost.

→ `wiki` had 312 requests in 14 days, about 22 a day. Look at *who* sent them. If it's only your monitoring IP and crawlers, real use is zero.

→ Requests **by IP** hit the default vhost. On port 80 that's Ubuntu's stock `000-default.conf`, which has its own `CustomLog` (`access.log`), so look there: `sudo zcat -f /var/log/apache2/access.log* | awk '{print $1}' | sort | uniq -c | sort -rn | head`. They're often scanners, and occasionally a forgotten integration that hard-coded the IP. Check the client IPs before you ignore them.

Databases have their own evidence:

```bash
# MySQL: who is connected right now, and which schemas changed (InnoDB update_time is kept in memory only: reset by a restart,
# and MySQL 8 caches these statistics for up to information_schema_stats_expiry = 86400 s, so it can lag by a day)
sudo mysql -e "SELECT user, host, db, command, time FROM information_schema.processlist WHERE command <> 'Sleep'"
sudo mysql -e "SELECT table_schema, MAX(update_time) AS last_write FROM information_schema.tables GROUP BY table_schema"
# PostgreSQL: connections and transaction counters per database (compare two readings a day apart)
sudo -u postgres psql -c "SELECT datname, numbackends, xact_commit, stats_reset FROM pg_stat_database"
```

### Evidence 3 — What systemd runs, enables and depends on

```bash
systemctl list-units --type=service --state=running --no-pager          # running now
systemctl list-unit-files --type=service --state=enabled --no-pager     # starts at boot
systemctl list-sockets --no-pager                                       # socket-activated
systemctl show apache2 -p ActiveEnterTimestamp -p NRestarts -p UnitFileState -p FragmentPath
systemctl list-dependencies --reverse apache2.service                   # who Wants/Requires it?
```

```
ActiveEnterTimestamp=Tue 2026-09-29 08:14:02 UTC
NRestarts=0
UnitFileState=enabled
FragmentPath=/usr/lib/systemd/system/apache2.service

apache2.service
● └─multi-user.target
●   └─graphical.target
```

→ Only the boot target pulls Apache in, so no other unit depends on it. If you saw another service in that tree, stopping Apache would stop or break it too.

→ A **running but not enabled** service was started by hand at some point and won't come back after a reboot. Its owner is often someone who "just tested something" months ago.

### Evidence 4 — Timers, cron, @reboot jobs and certbot

Things that *use* the service, or *restart* it, often live outside it:

```bash
systemctl list-timers --all --no-pager
ls -l /etc/cron.d/ /etc/cron.hourly/ /etc/cron.daily/
# Every crontab line that mentions the service, its paths or its port
sudo grep -rIn -E 'apache|apache2ctl|/var/www|/srv/crm|:3001|wiki' /etc/cron* /var/spool/cron/crontabs 2>/dev/null
sudo grep -rIn '@reboot' /etc/cron* /var/spool/cron/crontabs 2>/dev/null
# Certificates renewed THROUGH Apache (these renewals fail once Apache no longer owns port 80)
sudo grep -h -E '^(authenticator|installer)' /etc/letsencrypt/renewal/*.conf 2>/dev/null | sort | uniq -c
```

```
/var/spool/cron/crontabs/deploy:4:@reboot cd /srv/crm && /usr/bin/pm2 resurrect
/etc/cron.d/wiki-backup:2:30 2 * * * root /opt/wiki/bin/backup.sh >> /var/log/wiki-backup.log 2>&1

      3 authenticator = apache
      3 installer = apache
```

→ Two findings that change the plan. First, a **`@reboot` pm2 resurrect** exists *in addition to* the `pm2-deploy.service` unit, so the CRM app has two start mechanisms. Second, **three certificates renew through Apache's certbot plugin**. When Traefik takes over port 80, these renewals fail silently until the certificates expire. Plan to move those domains' TLS to Traefik, or switch their certbot authenticator, *as part of the same change*.

### Evidence 5 — DNS, certificates and install history

```bash
# Does each Apache vhost name still resolve to this server?
for d in $(sudo apache2ctl -S 2>/dev/null | awk '/namevhost/ {print $4}' | sort -u); do
  printf '%-25s %s\n' "$d" "$(dig +short "$d" A | tr '\n' ' ')"
done

# Certificate state for each name
sudo certbot certificates 2>/dev/null | grep -E 'Certificate Name|Domains|Expiry'

# When was it installed, and when was its config last changed?
zgrep -h ' install ' /var/log/dpkg.log* 2>/dev/null | grep -E ' install (apache2|php8\.[0-9]-fpm|nodejs):' | sort   # dpkg logs "apache2:amd64"
ls -l --time-style=long-iso /var/lib/dpkg/info/apache2.list      # rough install/upgrade date when dpkg.log has rotated away
sudo ls -lt --time-style=long-iso /etc/apache2/sites-enabled/ /etc/apache2/sites-available/
rpm -qi httpd | grep -E 'Install Date|Version'                     # RHEL/Rocky
```

```
app1.example.com          192.0.2.10
crm.example.com           192.0.2.10
wiki.example.com          203.0.113.80
192.0.2.10

  Certificate Name: wiki.example.com
    Domains: wiki.example.com
    Expiry Date: 2026-03-14 09:12:40+00:00 (INVALID: EXPIRED)
```

→ `wiki.example.com` **resolves to another server** (203.0.113.80), and its certificate here **expired in March** with no complaints. Together with Evidence 2, that's a strong retire signal: the wiki was migrated away long ago and this vhost is a leftover.

### Evidence 6 — Owners and the humans

```bash
stat -c '%U %y %n' /var/www/* /srv/* 2>/dev/null                           # who owns the code, when it last changed
sudo -u deploy git -C /srv/crm log -1 --format='%h %an %ad %s' 2>/dev/null   # last deploy and who did it
sudo -u deploy git -C /srv/crm remote -v 2>/dev/null                        # which repo (and team) it comes from
sudo grep -h -E '^\s*#' /etc/apache2/sites-available/*.conf | head          # comments: ticket IDs, names, dates
last -n 20                                                                  # who logs in to this box
```

Then ask people: the client, the team named in the Git remote, the CMDB or wiki, old tickets. Write down **who confirmed what, and when**. "Kept because Priya (CRM team) confirmed on 2026-10-02 it is used by sales" is an inventory entry that survives audits and staff changes.

### The inventory table template

Keep this as a living document (Markdown in your runbook repo, or a spreadsheet). One row per *application*, not per port:

| Port / bind | Owner (PID → unit / container) | Application & domain(s) | Config | Logs | Evidence of use | Depends on / used by | Owner (person) | Decision | Target | Rollback |
|---|---|---|---|---|---|---|---|---|---|---|
| 443 `*` (vhost app1) | apache2.service | app1.example.com (PHP 8.3) | `/etc/apache2/sites-enabled/app1-le-ssl.conf` | `/var/log/apache2/other_vhosts_access.log` | ~3,400 req/day, real clients | php8.3-fpm, MySQL `app1` | Marketing | Migrate | Dokploy app (PHP-FPM + Nginx image) | re-enable vhost, DNS back |
| 443 `*` (vhost crm) → 127.0.0.1:3001 | apache2 → pm2-deploy.service (node) | crm.example.com | `/srv/crm/.env`, `ecosystem.config.js` | `~/.pm2/logs/crm-*.log`, `crm_access.log` | ~1,450 req/day; sales team | MySQL `crm`, @reboot cron | Priya, CRM team | Migrate | Dokploy app from Harbor image | pm2 resurrect + vhost |
| 443 `*` (vhost wiki) → 8080 | apache2 → tomcat9.service | wiki.example.com | `/etc/tomcat9/server.xml` | `/var/log/tomcat9/` | only monitoring; DNS points elsewhere; cert expired | backup cron | nobody claims it | Retire (scream test) | none | start tomcat9 + enable vhost |
| 8081 `0.0.0.0` | docker-proxy → metabase | (none, by IP) | `/opt/metabase/docker-compose.yml` | `docker logs metabase` | 1 conn/day, BI team | MySQL read user | BI team | Keep; publish on 127.0.0.1 behind Traefik | Traefik route | old compose file |

### Decide: keep, migrate or retire

| What the evidence says | Decision | How |
|---|---|---|
| Real traffic, owner known, still needed | **Migrate** (or keep for now) | Put it behind the new proxy first, then containerize it ([case study](21-case-apache-443-dokploy.md)) |
| Real traffic, owner unknown | **Keep, investigate** | Don't touch it. Tag it in the inventory and chase an owner |
| Only monitors or bots, DNS elsewhere, cert expired, nobody claims it | **Retire** with a scream test | Below |
| Something else depends on it (cron, certbot, another app) | **Keep until the dependents are moved** | List the dependents in the inventory row |

**The scream test, done safely.** Use it when you're fairly sure something is unused:

1. Announce a date and a contact.
2. Back up its config and data.
3. **Stop and disable** it. Don't remove or purge anything.
4. Watch logs, tickets and monitoring for one to two weeks.
5. If nobody screams, remove it in a second, separate change. If somebody does, `systemctl enable --now` brings it back in seconds, and you've found the owner.

### Options when two services want the same port

The Apache vs Traefik conflict on 443 has five classic resolutions:

| Option | How | Good | Bad |
|---|---|---|---|
| **A. New proxy in front, old one behind** | Apache moves to a backend port (section 10, Rung 1). Traefik owns 80/443 and routes the old domains to Apache through its file provider | one entry point, certificates in one place, migrate vhost by vhost (the "strangler" pattern) | one planned cutover; Apache must trust `X-Forwarded-For` (`mod_remoteip`) to log real client IPs |
| **B. Second IP address** | Add 192.0.2.11. Apache uses `Listen 192.0.2.10:443`, Traefik publishes `192.0.2.11:443:443` | old vhosts untouched | DNS change per domain; Dokploy publishes Traefik on all addresses by default, so you'd customize and maintain that |
| **C. Different port for the new app** | Client uses `https://app.example.com:8443` | trivial | ugly URLs, firewall rules, blocked by some corporate proxies |
| **D. Old proxy in front of the new one** | Apache proxies the new domains to Traefik on a backend port | old vhosts untouched | fights Dokploy's design (Traefik expects 80/443 for ACME challenges), double TLS hops; not recommended |
| **E. Retire the old proxy** | after migrating every vhost | simplest end state | requires the migration first |

**A as the transition and E as the destination** is what most teams do, and it's the path the [case study](21-case-apache-443-dokploy.md) walks through in detail.

**What you did in the real incident [L3 · Senior].** You moved Apache to ports **81 and 444** and gave 80/443 to Dokploy's Traefik. That's the first half of option A: the old owner leaves the contested ports, and nothing has to be rebuilt in a hurry. Run this module's checks against that state, because three things decide whether the job is finished:

- **Who answers the old domains on 443 now?** DNS for the Apache sites still points at this host, so their visitors reach Traefik. Without a Traefik route for each domain (an HTTP route to Apache on 81, or a TCP passthrough by SNI to 444), they get Traefik's 404 and `TRAEFIK DEFAULT CERT`. Scenario 17 proves which one each domain gets.
- **Are 81 and 444 reachable from outside?** `Listen 81` binds every address. Check with `sudo ss -ltnp '( sport = :81 or sport = :444 )'` and `nmap` from another machine (section 3). Bind them to an address the Traefik container can reach and firewall them from the internet (section 10, Rung 1).
- **Do certificate renewals still work?** Apache's certbot plugin can no longer answer HTTP-01 challenges on port 80 (section 9, Evidence 4).

[Deployment patterns](35-deployment-patterns.md) analyses the 81/444 move in full and shows how to finish it with Traefik routing.

---

## 10. Dispatching a service safely

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — *SYSTEMD Tools* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) · 2) KodeKloud: *Docker Certified Associate* — *Restart Policies* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)) · 3) KodeKloud: *Fundamentals of SRE* — *Change Management for Reliability* ([lesson](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · 4) Note: [systemd](07-services-systemd.md) and [Deployment patterns](35-deployment-patterns.md) · 5) Practice: drills 3, 5 and 8 in section 19.

**Level:** [L1 · Junior] for rungs 1–4 on a single service · [L2 · Mid] for "why does it come back" and verification · [L3 · Senior] for Swarm and Kubernetes rungs · [L4 · Lead] for the change checklist and rollback plan.

"Dispatching" a service means getting it off a port: moving it, stopping it, or removing it. **Pick the lowest rung that solves the problem.** Every rung up is harder to undo.

> This section changes the system. Do it in a change window, with the inventory done, a backup taken, a second SSH session open, and the rollback written down *before* you start. Ops-ladder L4 drill: write the change request in GitLab's format (criticality, steps, verification, rollback) first.

### Before you touch anything: the change checklist

```bash
# 1. Save state and config (these only write backups)
# (a plain "> /root/..." redirect runs as YOU and fails with "Permission denied", so write through sudo tee)
sudo cp -a /etc/apache2 /root/apache2.bak-$(date +%F)
{ systemctl is-enabled apache2; systemctl is-active apache2; } | sudo tee /root/apache2.state-$(date +%F)
sudo ss -tulpn | sudo tee /root/listeners-before-$(date +%F).txt >/dev/null
# 2. Containers: save what you can't easily recreate
docker inspect CONTAINER | sudo tee /root/CONTAINER-inspect-$(date +%F).json >/dev/null
# 3. Kubernetes: save the objects you will scale or patch
kubectl -n NS get deploy,svc NAME -o yaml > NAME-backup-$(date +%F).yaml
```

Also:

- Lower the DNS TTL a day ahead if domains will move.
- Tell the people from the inventory's Owner column.
- Have console (iDRAC/iLO, hypervisor, cloud serial console) access ready if SSH, the network or the firewall is involved.

### The ladder from least to most invasive

| Rung | Action | Frees the port now | Still off after reboot | Undo |
|---|---|---|---|---|
| 1 | Change its port or bind address, then reload or restart | yes | yes (it's config) | revert the config and restart |
| 2 | Graceful stop or drain (`apache2ctl graceful-stop`, `nginx -s quit`) | yes, after in-flight requests finish | no, if enabled | start |
| 3a | `systemctl stop UNIT` (and its `.socket`) | yes | no, if enabled | `systemctl start` |
| 3b | `systemctl disable UNIT` | no (combine with stop: `disable --now`) | yes | `systemctl enable` |
| 3c | `systemctl mask UNIT` | no (combine with stop) | yes, and nothing can start it | `systemctl unmask` |
| 4a | `docker stop` plus `docker update --restart=no` | yes | yes | `docker update --restart=POLICY` and `docker start` |
| 4b | `docker rm` / `docker compose down` | yes | yes | recreate (you need the compose file or the saved inspect) |
| 5 | Swarm: `docker service scale S=0`, `--publish-rm`, `rm`. Kubernetes: `scale --replicas=0`, patch or `delete` | depends (section below) | yes | scale back, re-apply the backup YAML |
| 6 | `kill -TERM PID`, wait | yes, unless a manager restarts it | depends on the manager | start via the manager |
| 7 | `kill -KILL PID` | yes, unless a manager restarts it | depends | start, check for corruption |

### Rung 1 — Move the port or bind address

This is the gentlest option: the service keeps running and only stops occupying the contested port. For Apache on Ubuntu, `Listen` lives in `/etc/apache2/ports.conf`, and every `<VirtualHost ADDR:PORT>` must match a `Listen`.

```
# /etc/apache2/ports.conf — BEFORE
Listen 80
<IfModule ssl_module>
	Listen 443
</IfModule>
<IfModule mod_gnutls.c>
	Listen 443
</IfModule>

# AFTER — Apache becomes a plain-HTTP backend on 8080, TLS moves to Traefik
Listen 192.0.2.10:8080
```

```bash
sudoedit /etc/apache2/ports.conf                          # the Listen lines
sudoedit /etc/apache2/sites-available/crm-ssl.conf        # <VirtualHost *:8080>, without the SSL directives (repeat for every vhost)
sudo apache2ctl configtest                                # must print "Syntax OK"
sudo systemctl restart apache2                            # Listen changes: restart, not reload
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :8080 )'
```

```
Syntax OK
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      511       192.0.2.10:8080       0.0.0.0:*    users:(("apache2",pid=5014,fd=4),("apache2",pid=5013,fd=4),("apache2",pid=5012,fd=4))
```

→ 80 and 443 are gone, and Apache answers only on 192.0.2.10:8080. A graceful reload *usually* applies `Listen` changes too, but a restart is unambiguous and costs about a second of downtime. Schedule it.

Things that bite at this rung:

- **Containers can't reach the host's 127.0.0.1.** If Traefik runs in a container, bind the backend to an address the container *can* reach: the host's LAN IP (as above) or the Docker bridge gateway. Then make sure the host firewall allows that traffic from the Docker networks and blocks it from outside. The [case study](21-case-apache-443-dokploy.md) walks through this, and [Learn: networking](28-learn-networking.md) explains why.
- **RHEL/Rocky with SELinux:** Apache may only bind ports labelled `http_port_t`. A new port fails with `(13)Permission denied: AH00072: make_sock: could not bind to address`. Check with `sudo semanage port -l | grep -w http_port_t` and add one with `sudo semanage port -a -t http_port_t -p tcp 8085`.
- **The redirect vhosts on :80 and the certbot renewals** that used port 80 (section 9, Evidence 4) must move with it.

The same move for other servers:

```bash
# Nginx: change "listen 80;" to "listen 127.0.0.1:8080;" in the server blocks, then
sudo nginx -t && sudo systemctl reload nginx          # nginx re-binds on reload
# pm2 app: change PORT in the ecosystem file (as the app user, in the app dir), then reload FROM THE FILE
# ("pm2 restart crm --update-env" would take the env of your current shell, not the edited file)
pm2 restart ecosystem.config.js --only crm --update-env && pm2 save
# Compose: change "8081:3000" to "127.0.0.1:18081:3000" (or delete the ports: block), then
cd /opt/metabase && docker compose up -d               # recreates the container with the new mapping
```

**Rollback:** restore the backed-up files (`sudo cp -a /root/apache2.bak-DATE/. /etc/apache2/`), run `apache2ctl configtest`, then `systemctl restart apache2`.

### Rung 2 — Graceful stop and drain

```bash
watch -n 2 "ss -Htn state established '( sport = :443 )' | wc -l"   # watch traffic drain (e.g. after a DNS move)
sudo apache2ctl graceful-stop     # stop accepting, let in-flight requests finish
sudo nginx -s quit                # Nginx equivalent (its unit stops with QUIT too)
```

→ Ubuntu's `apache2.service` already uses `ExecStop=/usr/sbin/apachectl graceful-stop` (section 4, Step 6), so `systemctl stop apache2` *is* graceful. systemd waits up to `TimeoutStopSec` (90 s by default) and then kills what's left.

### Rung 3 — systemctl stop, disable, mask

```bash
sudo systemctl stop apache2
sudo systemctl disable apache2       # don't start at boot
sudo systemctl mask apache2          # nothing can start it: no dependency, no admin by mistake
systemctl is-enabled apache2; systemctl is-active apache2
```

```
Synchronizing state of apache2.service with SysV service script with /usr/lib/systemd/systemd-sysv-install.
Executing: /usr/lib/systemd/systemd-sysv-install disable apache2
Removed "/etc/systemd/system/multi-user.target.wants/apache2.service".
Created symlink /etc/systemd/system/apache2.service → /dev/null.
masked
inactive
```

| Command | Stops it now | Prevents start at boot | Prevents start by another unit, socket or admin |
|---|---|---|---|
| `stop` | yes | no | no |
| `disable` | no | yes | no |
| `disable --now` | yes | yes | no |
| `mask` (+ `stop`) | with stop | yes | **yes**. `systemctl start` says "Unit apache2.service is masked." |

**Socket-activated services need the socket stopped too**, or the next connection starts them again:

```bash
sudo systemctl stop cockpit.socket cockpit.service
sudo systemctl disable cockpit.socket
```

> **Never stop `ssh.socket` / `ssh.service` on a remote box** unless you have console access and are deliberately moving SSH. On Ubuntu 24.04, change the SSH port through `sshd_config`, then run `systemctl daemon-reload` and `systemctl restart ssh.socket`. Allow the new port in UFW *first*, and test a new connection before you close the old session.

→ `mask` fails with "File /etc/systemd/system/UNIT.service already exists" when the unit file itself lives in `/etc/systemd/system` (a custom unit). Use `disable --now`, and rename the file out of the way if it must never start.

**Rollback:** `sudo systemctl unmask apache2 && sudo systemctl enable --now apache2`.

### Rung 4 — Docker and Compose containers

```bash
docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' CONTAINER    # know the policy BEFORE stopping
docker stop -t 30 CONTAINER          # SIGTERM, wait up to 30 s, then SIGKILL
docker update --restart=no CONTAINER # so a daemon restart or reboot doesn't bring it back
docker compose -p PROJECT stop       # stops containers, keeps them (restart policy still applies at boot!)
docker compose -p PROJECT down       # removes containers and project networks, KEEPS named volumes
```

| Restart policy | After `docker stop` | After daemon restart or reboot |
|---|---|---|
| `no` | stays stopped | stays stopped |
| `on-failure` | stays stopped | stays stopped |
| `always` | stays stopped… | **starts again** |
| `unless-stopped` | stays stopped | stays stopped |

→ The `always` row explains a classic "I stopped it and after the reboot it was back". Combine `docker stop` with `docker update --restart=no`, or remove the container.

> `docker compose down -v` and `docker rm -v` **delete volumes**, which means data (databases, uploads). Use plain `down` / `rm`, and remove volumes in a separate, deliberate step after a backup. `docker system prune -a --volumes` is never part of dispatching a single service.

Before `docker rm` on a container that has **no** Compose labels, save its definition (`docker inspect` to a file, as in the checklist). A plain `docker run` command line isn't stored anywhere else.

**Rollback:** `docker update --restart=POLICY CONTAINER && docker start CONTAINER` with the policy you recorded before stopping, or `docker compose up -d` from the original project directory.

### Rung 5 — Swarm and Kubernetes: scale to zero

**Docker Swarm** (Dokploy applications are Swarm services):

```bash
docker service inspect SERVICE | sudo tee /root/SERVICE-spec-$(date +%F).json >/dev/null   # backup first
docker service scale SERVICE=0                 # tasks stop; an INGRESS-published port stays reserved by dockerd
docker service update --publish-rm 3000 SERVICE   # release the published port (argument: the target port)
docker service rm SERVICE                      # remove it entirely
```

→ Scaling to 0 frees **host-mode** ports, but an **ingress** port belongs to the service and stays reserved until you remove the publish or the service. For apps that Dokploy manages, use **Stop** in the Dokploy UI. Manual changes are overwritten on the next deploy.

→ `dokploy-traefik` is the front door for every app on the host. `docker stop dokploy-traefik` frees 80/443 but takes every site down. With `restart: always` it comes back after a daemon restart or reboot.

**Kubernetes:**

```bash
kubectl -n NS get deploy NAME -o yaml > NAME-deploy-$(date +%F).yaml      # backup first
kubectl -n NS scale deploy/NAME --replicas=0      # pods stop and hostPorts are freed; the Service and its NodePort STAY
kubectl -n NS get svc NAME -o yaml > NAME-svc-$(date +%F).yaml
kubectl -n NS patch svc NAME -p '{"spec":{"type":"ClusterIP"}}'   # release the NodePort, keep the Service
# DaemonSets can't be scaled: park them with a nodeSelector that matches no node
kubectl -n NS patch ds NAME -p '{"spec":{"template":{"spec":{"nodeSelector":{"parked":"true"}}}}}'
# Static pods: move the manifest out of the kubelet's directory (the pod stops within seconds)
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /root/
```

→ **A NodePort belongs to the Service**, not to the pods. Scaling to zero doesn't free it. Changing the type to ClusterIP does: current API servers drop the `nodePort` values on that change, while older ones may ask you to remove them from the ports list yourself.

> `kubectl delete` is the top of this rung. Save the YAML first, prefer `scale` or `patch`, and never delete in `kube-system` to "free a port". Moving `kube-apiserver.yaml` out of the manifests directory takes the cluster API down. That's a CKA lab exercise, not a production move.

**Rollback:** `kubectl apply -f NAME-deploy-DATE.yaml` (or `scale --replicas=N`), `kubectl apply -f NAME-svc-DATE.yaml`, and move the static manifest back.

### Rung 6 — Signals: TERM, wait, then KILL

Use signals only for processes **no manager owns** (section 4, Step 3 showed a `session-N.scope` or similar), or when the manager itself is broken.

```bash
ps -o pid,ppid,unit,cmd -p PID                  # managed by something? then use THAT instead
pgrep -af 'PATTERN'                             # preview exactly what a pkill PATTERN would hit
sudo kill -TERM PID                             # polite: close sockets, flush buffers, remove pid files
timeout 30 tail --pid=PID -f /dev/null && echo "exited" || echo "still running after 30 s"
sudo kill -KILL PID                             # LAST resort (see below)
```

> **What `kill -9` costs.** The process gets no chance to clean up. In-flight requests are cut, and buffered log lines and unflushed writes are lost. Databases go through crash recovery, or worse. Stale PID and lock files can block the next start. Repeated SIGKILLs to Apache can leak IPC semaphores until it fails with `AH00023: Couldn't create the ... mutex` (visible with `ipcs -s`). And under systemd it often achieves nothing: SIGKILL is an "unclean" exit, so `Restart=on-failure`, `on-abort` (Apache's setting) and `always` all **restart the service immediately**. Use it only on a process that ignores TERM, after you've confirmed that nothing will restart it and that you accept the data risk.

→ Killing Apache or Nginx **workers** is pointless: the master spawns new ones. Stop the master through its unit.

→ A process in state `D` (uninterruptible I/O) ignores even SIGKILL until the I/O returns. See [Processes](05-processes.md).

### Why does it come back?

| Mechanism | How to see it | Stop it properly |
|---|---|---|
| systemd `Restart=` | `systemctl show UNIT -p Restart -p NRestarts`; the journal says "Scheduled restart job, restart counter is at N" | `systemctl stop` (a deliberate stop never triggers Restart=), then disable or mask |
| systemd socket activation | `systemctl list-sockets`; `ss` shows `systemd` pid 1 | stop and disable the `.socket` as well |
| Another unit `Wants=` / `Requires=` it | `systemctl list-dependencies --reverse UNIT` | `mask` it, or fix the depending unit |
| A systemd timer | `systemctl list-timers --all` | stop and disable the `.timer` |
| cron (`@reboot`, watchdog scripts like `pgrep app ... start app`) | `sudo grep -rIn APP /etc/cron* /var/spool/cron/crontabs` | comment out the line (and note it in the change) |
| Docker restart policy | `docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' CONTAINER` | `docker update --restart=no`, or `docker rm` |
| Docker Compose `restart: always` | `docker compose ls` | `docker compose down` (not just `stop`) |
| Swarm service (including Dokploy apps) | `docker service ls`, `docker service ps S` | scale to 0, or `rm`; Dokploy apps via the UI |
| Kubernetes controller (Deployment, ReplicaSet, StatefulSet, DaemonSet, Job) | `kubectl get pod POD -o jsonpath='{.metadata.ownerReferences[*].kind}'` | scale or patch the **owner**, not the pod |
| Kubernetes static pod | `config.source` annotation = `file` | move the manifest out of `/etc/kubernetes/manifests` |
| supervisord | `sudo supervisorctl status` | `supervisorctl stop APP`, set `autostart=false`, then `supervisorctl update` |
| pm2 | `pm2 list` (as the app user); `pm2-USER.service` | `pm2 stop APP && pm2 save`; for good, `pm2 delete APP && pm2 save` (a stopped app stays in the saved list, and `pm2 resurrect` may start it again depending on the pm2 version) |
| monit, runit, s6, daemontools | `monit summary`; `sv status`; process tree | stop the supervisor's entry for it |
| Configuration management (Ansible pull, Puppet agent, Salt minion, Chef client) | timers or daemons such as `puppet`, `salt-minion`; a file header "managed by…" | change the desired state **in the code**, or it reverts at the next run |
| CI/CD auto-deploy (Dokploy webhook, GitLab pipeline) | the deploy log, `docker events --since 30m` | disable auto-deploy or the pipeline trigger first |
| inetd / xinetd (legacy) | `/etc/inetd.conf`, `/etc/xinetd.d/` | disable the entry, then reload xinetd |

Scenario 15 turns this table into a step-by-step hunt.

### Verify the port is really free

"I stopped it" isn't proof. Check every kind of owner from section 2:

```bash
sudo ss -ltnp 'sport = :443'; sudo ss -lunp 'sport = :443'     # no socket, TCP or UDP
systemctl list-sockets --no-pager | grep -E ':443\b'             # no socket unit
docker ps --format '{{.Names}} {{.Ports}}' | grep -E ':443->'    # no container publishes it
sudo iptables-save -t nat | grep -E -- '--dport 443\b'           # no DNAT / REDIRECT for it
nc -zv -w 3 192.0.2.10 443                                       # FROM ANOTHER HOST: expect "Connection refused"
```

```
nc: connect to 192.0.2.10 port 443 (tcp) failed: Connection refused
```

→ "Refused" from outside means the packet arrived and nothing answered, so the port really is free. The one exception is a firewall `REJECT` rule, which also answers with a reset; check `sudo nft list ruleset | grep -i reject` if in doubt. A timeout would mean a firewall drops it, which is a different problem.

→ The ultimate test is to start the new owner and watch it bind (`docker logs dokploy-traefik`, `journalctl -u UNIT`).

### TIME_WAIT, Address already in use and SO_REUSEADDR

After you stop a busy server, `ss -tan` still shows lines on its port for up to a minute:

```
$ ss -tan '( sport = :443 )'
State      Recv-Q Send-Q          Local Address:Port              Peer Address:Port Process
TIME-WAIT  0      0      [::ffff:192.0.2.10]:443   [::ffff:203.0.113.45]:51544
TIME-WAIT  0      0      [::ffff:192.0.2.10]:443   [::ffff:198.51.100.23]:60212
```

→ **TIME_WAIT isn't an owner.** It's the kernel remembering recently closed connections (about 60 s on Linux) so that late packets aren't mistaken for new ones.

→ A server that sets **`SO_REUSEADDR`** before binding can bind the port despite TIME_WAIT entries. Apache, Nginx, Traefik and other Go servers, Node, Java servers and Python's `http.server` all do. So for real servers, "Address already in use" **always means a live owner**: a LISTEN socket, a socket unit, or another bind. Your own quick scripts that don't set it can fail for up to a minute after a restart.

→ **`SO_REUSEPORT`** is different. It lets several sockets *listen* on the same port for load balancing, as long as all of them set it and run as the same user. Two LISTEN lines on one port can be deliberate.

> Don't "fix" bind errors with sysctls. `net.ipv4.tcp_tw_reuse` only affects *outgoing* connections, and `tcp_tw_recycle` was removed from Linux in 4.12 because it broke clients behind NAT. Find the owner.

---

## 11. Windows: who owns this port

> 📚 **Study path:** 1) Note: [Windows reference](17-windows.md) (refresher on netstat and PowerShell networking) · 2) KodeKloud: no Windows Server course appears in the verified study map, so this section and the reference module are your material · 3) Practice: a Windows Server evaluation VM: find who owns 80, 443 and 5985, then list the excluded port ranges.

**Level:** [L1 · Junior] for netstat and Get-NetTCPConnection · [L2 · Mid] for http.sys and excluded port ranges.

The Linux method carries over: *port → PID → service or process → config → logs*. Windows adds two twists. Many web ports belong to the **kernel HTTP driver (http.sys)** and show up as PID 4, and **Hyper-V/WinNAT reserve whole port ranges** that block binds without anything listening. Run PowerShell **as Administrator**. Basic network commands are in [Windows reference](17-windows.md).

### netstat -ano and Get-NetTCPConnection

```powershell
netstat -ano | findstr LISTENING            # all listeners with PID (-o)
netstat -ano -p tcp | findstr /C:":443 "    # one port (/C: makes the trailing space literal, so :4430 doesn't match)
netstat -abno                               # + executable and service name per line (admin, slow)

Get-NetTCPConnection -State Listen |
  Sort-Object LocalPort |
  Select-Object LocalAddress, LocalPort, OwningProcess,
    @{n='Process'; e={ (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName }} |
  Format-Table -AutoSize

Get-NetUDPEndpoint | Sort-Object LocalPort | Select-Object LocalAddress, LocalPort, OwningProcess
```

```
LocalAddress LocalPort OwningProcess Process
------------ --------- ------------- -------
0.0.0.0             80             4 System
0.0.0.0            135          1032 svchost
0.0.0.0            443             4 System
0.0.0.0           3389          1188 svchost
127.0.0.1         3000          9412 node
0.0.0.0           5985             4 System
::                 443             4 System
```

→ **PID 4 "System"** on 80, 443 and 5985 means http.sys owns them on behalf of some service. Go to the http.sys section below; `tasklist` can't tell you more.

→ **svchost** hosts one or more services. Map the PID to the service name in the next step.

→ `127.0.0.1:3000` is local-only, exactly as on Linux.

### From PID to process, service and command line

```powershell
tasklist /svc /fi "PID eq 1188"                                   # services inside this process
Get-CimInstance Win32_Service -Filter "ProcessId = 1188" |
  Select-Object Name, DisplayName, State, StartMode, PathName
Get-CimInstance Win32_Process -Filter "ProcessId = 9412" |
  Select-Object ProcessId, ParentProcessId, CreationDate, ExecutablePath, CommandLine | Format-List
```

```
Image Name                     PID Services
========================= ======== ============================================
svchost.exe                   1188 TermService

Name        : TermService
DisplayName : Remote Desktop Services
State       : Running
StartMode   : Manual
PathName    : C:\Windows\System32\svchost.exe -k NetworkService

ProcessId       : 9412
ParentProcessId : 7720
CreationDate    : 03/10/2026 08:15:22
ExecutablePath  : C:\Program Files\nodejs\node.exe
CommandLine     : "C:\Program Files\nodejs\node.exe" D:\apps\reporting\server.js
```

→ The command line reveals the app directory (`D:\apps\reporting`), which is where its config and logs usually are. Check the **parent**: `Get-CimInstance Win32_Process -Filter "ProcessId = 7720"`. If it's `nssm.exe` or `winsw.exe`, the Node app is wrapped as a Windows service, and that service restarts it (`Get-CimInstance Win32_Service | Where-Object PathName -like '*nssm*'`).

→ Logs: the Event Log (`Get-WinEvent -LogName Application -MaxEvents 50`), the app directory, or the wrapper's configured stdout file.

### PID 4 System: ports owned by http.sys

IIS, WinRM (5985/5986), SSRS, WSUS, Web Deploy (8172), UPnP Device Host (2869), WS-Discovery (5357) and many vendor tools don't open sockets themselves. They register URLs with **http.sys**, the kernel driver that owns the port. To find the real owner, ask http.sys:

```powershell
netsh http show servicestate view=requestq verbose=no   # request queues: registered URLs + process IDs
netsh http show urlacl                                   # URL reservations (who MAY listen)
netsh http show sslcert                                  # certificate bindings on ip:port
netsh http show iplisten                                 # if set, http.sys binds ONLY these IPs
```

```
Snapshot of HTTP service state (Request Queue View):
-----------------------------------------------------

Request queue name: DefaultAppPool
    Version: 2.0
    State: Active
    Number of active processes attached: 1
    Process IDs:
        5132
    URL groups:
    URL group ID: FE00000040000001
        State: Active
        Number of registered URLs: 2
        Registered URLs:
            HTTP://*:80/
            HTTPS://*:443/

Request queue name: Request queue is unnamed.
    Version: 2.0
    State: Active
    Process IDs:
        2280
    URL groups:
        Registered URLs:
            HTTP://+:5985/WSMAN/
```

→ 80 and 443 belong to the IIS application pool **DefaultAppPool**, whose worker is `w3wp.exe` PID 5132. 5985 belongs to PID 2280. `tasklist /svc /fi "PID eq 2280"` shows `WinRM`.

> `net stop http` stops the HTTP driver **and every service that depends on it** (IIS, WinRM, and others). It's the Windows version of `fuser -k`. Stop the specific service that registered the URL instead.

→ To let two web servers share 443 on one Windows box, give http.sys only one IP (`netsh http add iplisten ipaddress=192.0.2.10`) and bind the other server to a second IP. The change takes effect when the HTTP service restarts, which restarts its dependents, so schedule it. This is the same "second IP" option as on Linux (section 9).

### Excluded port ranges: Hyper-V, WSL2 and WinNAT

Symptom: your app fails to bind a port with **"An attempt was made to access a socket in a way forbidden by its access permissions"** (WSAEACCES, 10013) or Node's `listen EACCES`. Yet `netstat -ano` shows **nothing** on that port. Hyper-V, WSL2 or Docker Desktop (through WinNAT) has **reserved** a range that includes it.

```powershell
netsh int ipv4 show excludedportrange protocol=tcp
netsh int ipv4 show dynamicport tcp            # the range Windows hands out for ephemeral ports
```

```
Protocol tcp Port Exclusion Ranges

Start Port    End Port
----------    --------
      2869        2869
      5357        5357
     49709       49808
     50000       50059     *
     50060       50159

* - Administered port exclusions.

Protocol tcp Dynamic Port Range
---------------------------------
Start Port      : 49152
Number of Ports : 16384
```

→ A port inside one of these ranges can't be bound even though no process holds it. Ranges move after reboots, which is why "it worked yesterday".

Fixes, in order of preference:

1. **Use a port outside the excluded ranges.**
2. If the **dynamic range starts low** (for example at 1025, which some updates and Hyper-V setups cause), restore the default with `netsh int ipv4 set dynamic tcp start=49152 num=16384` and reboot.
3. As a one-off, stop WinNAT (`net stop winnat`), start your service so it takes the port, then `net start winnat`. That briefly breaks WSL2, Docker Desktop and Hyper-V NAT networking.

### IIS bindings and logs

```powershell
& "$env:windir\system32\inetsrv\appcmd.exe" list sites
Get-IISSite                                       # IISAdministration module (Server 2016+)
Import-Module WebAdministration; Get-WebBinding | Select-Object protocol, bindingInformation
```

```
SITE "Default Web Site" (id:1,bindings:http/*:80:,https/*:443:,state:Started)
SITE "crm" (id:2,bindings:https/*:443:crm.example.com,state:Started)
```

→ `bindingInformation` is `IP:PORT:HOSTNAME`. `*:443:crm.example.com` is the IIS equivalent of an Apache name-based vhost. Site **id 2** logs to `%SystemDrive%\inetpub\logs\LogFiles\W3SVC2\`. Requests that http.sys rejects before IIS sees them are in `%SystemRoot%\System32\LogFiles\HTTPERR\`.

### Stopping and disabling Windows services

```powershell
Get-Service -Name W3SVC, WAS | Select-Object Name, Status, StartType
& "$env:windir\system32\inetsrv\appcmd.exe" stop site /site.name:"crm"   # one IIS site only (rung 1-2)
Stop-Service -Name W3SVC                         # stop through the Service Control Manager
Set-Service -Name W3SVC -StartupType Disabled    # don't start at boot
sc.exe config W3SVC start= disabled              # same with sc.exe (the space after "start=" is required)
sc.exe qfailure W3SVC                            # recovery actions: "RESTART" = why it comes back
Get-ScheduledTask | Where-Object State -ne 'Disabled' | Where-Object TaskName -like '*report*'
```

→ In PowerShell always type **`sc.exe`**. In Windows PowerShell, plain `sc` is an alias for `Set-Content`, so it writes a file instead of configuring a service.

→ "It came back" on Windows usually means one of: the service's **recovery options** (restart on failure), a **scheduled task**, an IIS application pool with AlwaysRunning, or a service wrapper (NSSM, WinSW). Check those before you reach for `Stop-Process -Force`, which, like `kill -9`, gives the app no chance to clean up.

---

## 12. macOS: who owns this port

> 📚 **Study path:** 1) Note: [macOS reference](20-macos.md) (launchd and networking basics) · 2) KodeKloud: no macOS course in the verified study map · 3) Practice: on your own Mac, name the owner of every listener in `sudo lsof -nP -iTCP -sTCP:LISTEN`, including 5000 and 7000.

**Level:** [L0 · Fresher] for lsof · [L1 · Junior] for launchctl.

macOS has no `ss`, and its `netstat` doesn't show PIDs in the familiar form. Use `lsof`, then `launchctl` to find which job starts the process. Background on launchd is in [macOS reference](20-macos.md).

### lsof: listeners and one port

```bash
sudo lsof -nP -iTCP -sTCP:LISTEN               # all TCP listeners
sudo lsof -nP -iTCP:5000 -sTCP:LISTEN          # one port
sudo lsof -nP -iUDP:5353                       # UDP (mDNS here)
```

```
COMMAND     PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
ControlCe   612   dev   10u  IPv4 0x5c7a1f3e9b2d4a11      0t0  TCP *:5000 (LISTEN)
ControlCe   612   dev   11u  IPv6 0x5c7a1f3e9b2d4b22      0t0  TCP *:5000 (LISTEN)
ControlCe   612   dev   12u  IPv4 0x5c7a1f3e9b2d4c33      0t0  TCP *:7000 (LISTEN)
com.docke  1450   dev  145u  IPv6 0x5c7a1f3e9b2d4d44      0t0  TCP *:8080 (LISTEN)
postgres    988   dev    7u  IPv6 0x5c7a1f3e9b2d4e55      0t0  TCP [::1]:5432 (LISTEN)
```

→ `ControlCe` is **ControlCenter**, the AirPlay Receiver, on 5000 and 7000. `com.docke` is **com.docker.backend**: Docker Desktop's VM forwards published container ports through it, so `docker ps` names the real container. `postgres` on `[::1]:5432` is local-only (IPv6 loopback).

### From PID to launchd job

```bash
ps -o pid,ppid,user,lstart,command -p 988                   # full command and parent (PPID 1 = launchd)
launchctl list | awk -v p=988 '$1 == p'                     # user agents: PID  STATUS  LABEL
sudo launchctl list | awk -v p=988 '$1 == p'                # system daemons
launchctl print gui/$(id -u)/homebrew.mxcl.postgresql@16 | grep -E 'path =|program =|state =|stdout path|stderr path'
```

```
  PID  PPID USER  STARTED                      COMMAND
  988     1 dev   Fri Oct  2 09:02:11 2026     /opt/homebrew/opt/postgresql@16/bin/postgres -D /opt/homebrew/var/postgresql@16

988	0	homebrew.mxcl.postgresql@16

	path = /Users/dev/Library/LaunchAgents/homebrew.mxcl.postgresql@16.plist
	state = running
	program = /opt/homebrew/opt/postgresql@16/bin/postgres
	stdout path = /opt/homebrew/var/log/postgresql@16.log
	stderr path = /opt/homebrew/var/log/postgresql@16.log
```

→ The job's plist names the program, its config (`-D` data directory here) and **its log files** (stdout/stderr path). That's the macOS equivalent of `systemctl cat` and `journalctl -u`. A plist with `KeepAlive` set to true is macOS's `Restart=always`: launchd restarts the process if you kill it.

### AirPlay Receiver on ports 5000 and 7000

Since macOS 12 (Monterey), the AirPlay Receiver listens on **5000 and 7000**. Flask's development server, local registries and many tutorials default to 5000 and fail with "Address already in use" or get unexpected 403 responses from AirPlay.

Fix:

- Turn off **System Settings → General → AirDrop & Handoff → AirPlay Receiver**, or
- run your app on another port (`flask run --port 5001`, `docker run -p 5001:5000 ...`).

### Docker Desktop and Homebrew services

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'      # the container behind com.docker.backend
brew services list                                      # Homebrew-managed launchd jobs
brew services stop postgresql@16                        # stop and don't start at login
launchctl bootout gui/$(id -u)/LABEL                    # unload any user agent now
launchctl disable gui/$(id -u)/LABEL                    # keep it from loading again (persistent)
sudo launchctl bootout system/LABEL                     # system daemon
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate   # inbound firewall on/off
```

→ "Listening but unreachable from other machines" on a Mac is usually a bind to `127.0.0.1`/`::1`, or the application firewall blocking inbound connections for that binary (`socketfilterfw --listapps`).

---

## 13. Scenario — bind: Address already in use

> 📚 **Know this first:** 1) Note: sections 3 and 4 of this module (quick refresher) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Start, Stop, and Check Status of Network Services* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) KodeKloud: *Docker Certified Associate* — *Publishing Ports* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page)) · 4) Practice: [SadServers](https://sadservers.com/scenarios) "service won't start" scenarios, then drill 5.

**Level:** [L1 · Junior]. Handling this alone, end to end, is what employers expect of a Junior. The hand-over in Steps 5–7 is [L2 · Mid] work.

**Situation:** a service won't start because its port is taken. In your incident it was the Dokploy installer, or Traefik's container, failing on 443 because Apache held it. The same method works for any "the port is busy" error, on any service.

### Step 1 — Read the exact error and classify it

**Goal:** be sure this is a real port conflict (errno 98) and not a permissions or address problem that looks similar.

```bash
journalctl -u UNIT -n 30 --no-pager           # systemd services
docker logs --tail 30 CONTAINER               # containers that started then failed
# For a docker run / compose / installer failure, the error is on your terminal
```

```
# Real conflicts (errno 98, EADDRINUSE)
docker: Error response from daemon: driver failed programming external connectivity on endpoint dokploy-traefik (3f6c…): Error starting userland proxy: listen tcp4 0.0.0.0:443: bind: address already in use.
Bind for 0.0.0.0:443 failed: port is already allocated
(98)Address already in use: AH00072: make_sock: could not bind to address [::]:443
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
Error: listen EADDRINUSE: address already in use :::3000
OSError: [Errno 98] Address already in use
0/3 nodes are available: 3 node(s) didn't have free ports for the requested pod ports.

# Look-alikes that are NOT conflicts
(13)Permission denied: AH00072: make_sock: could not bind to address 0.0.0.0:80
listen EACCES: permission denied 0.0.0.0:80
(99)Cannot assign requested address: AH00072: make_sock: could not bind to address 192.0.2.11:443
```

**What it means:**

| Error | Meaning | Where to go |
|---|---|---|
| "address already in use", errno 98 | another socket holds this (proto, IP, port) **on the host** | Step 2 |
| Docker "**port is already allocated**" | **another container** already publishes this host port (Docker's own bookkeeping) | `docker ps --format '{{.Names}} {{.Ports}}'`, then Step 3 |
| Docker "**Error starting userland proxy** … address already in use" | a **host process** holds the port | Step 2 |
| Pod "didn't have free ports" | a hostPort is already taken on every candidate node | section 7, hostPort query |
| errno 13, EACCES | not allowed to bind: port below 1024 without privileges, SELinux, or a Windows excluded range | section 2 (privileged ports), section 10 (SELinux), section 11 |
| errno 99, EADDRNOTAVAIL | the IP in the bind isn't configured on this host (yet) | `ip -br addr`; at boot, order the unit after `network-online.target` |

**Why this step (now):** the three errno values need completely different fixes. Looking for a "port owner" when the real problem is SELinux or a missing IP wastes the whole investigation. The exact text also tells you **which IP** was requested (`0.0.0.0`, `[::]`, a specific address), and that matters for the conflict rules in section 2.

**Next step:** errno 98 or the userland-proxy variant → Step 2. "Port is already allocated" → find the container with `docker ps`, then Step 3. Anything else → follow the table.

### Step 2 — Find the current owner on TCP and UDP

**Goal:** name the PID or mechanism that holds the port right now.

```bash
sudo ss -ltnp 'sport = :443'
sudo ss -lunp 'sport = :443'                  # Traefik also wants udp/443 (HTTP/3)
systemctl list-sockets --no-pager | grep -E ':443\b'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1344,fd=6),("apache2",pid=1343,fd=6),("apache2",pid=1201,fd=6))
```

**What it means:** Apache holds `*:443`, a dual-stack wildcard. That blocks a bind on `0.0.0.0:443`, on `[::]:443` and on any specific IP's port 443. Nothing holds `udp/443`, and no socket unit is involved.

**Why this step (now):** it's the cheapest command that reads the kernel's truth. Checking UDP and socket units at the same time avoids the "I freed TCP but the new service still fails on UDP" second round.

**Next step:** a normal process → Step 3. `systemd` (pid 1) → the `.socket` unit named by `list-sockets` → Step 5. `docker-proxy` or `dockerd` → section 6 to name the container or service → Step 5. Nothing at all → Step 4.

### Step 3 — Identify the owner through its manager

**Goal:** turn the PID into "which service, managed by what, configured where".

```bash
systemctl status 1201 --no-pager | head -12
cat /proc/1201/cgroup
pgrep -af apache2 | head -3                   # is it maybe a second copy of the thing you're starting?
```

```
● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-09-29 08:14:02 UTC; 4 days ago
   Main PID: 1201 (apache2)
0::/system.slice/apache2.service
1201 /usr/sbin/apache2 -k start
1343 /usr/sbin/apache2 -k start
1344 /usr/sbin/apache2 -k start
```

**What it means:** the owner is `apache2.service`, enabled at boot and managed by systemd. If the owner had turned out to be **an older copy of the very service you're trying to start** (a common case after a hand-started test run, or a unit with the wrong `Type=` that systemd thinks is dead), the fix would be to stop that stale copy, not to touch anything else.

**Why this step (now):** you never act on a PID. You act on its manager (section 10). The cgroup also catches the hand-started case (`session-N.scope`), which has no unit to stop.

**Next step:** → Step 5 to decide who should own the port. To understand what the owner serves first (vhosts, backends), run section 4 Steps 4–7 and section 5.

### Step 4 — Nothing listens: find rule or allocator owners

**Goal:** explain a conflict when `ss` shows no listener.

```bash
docker ps --format '{{.Names}} {{.Ports}}' | grep -E ':443->'           # another container publishes it
docker service ls --format '{{.Name}} {{.Ports}}' | grep -E ':443->'    # a Swarm service reserves it
kubectl get svc -A -o wide 2>/dev/null | grep -E ':30080/'               # NodePort taken by another Service
ip -br addr                                                              # for errno 99: is the IP really here?
```

```
dokploy-traefik 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:443->443/udp, [::]:443->443/udp
```

**What it means:** another container, here Dokploy's own Traefik, already publishes 443, so a second container asking for 443 gets "port is already allocated". With the userland proxy disabled, nothing shows in `ss`, yet Docker's allocator knows the port is taken. Inside Kubernetes, NodePorts are allocated by the API server, not by sockets.

**Why this step (now):** the "nothing in ss" case means the owner is bookkeeping (Docker's allocator, Swarm's ingress, the Kubernetes API) or NAT. Those registries can only be read with their own tools.

**Next step:** an owner found → Step 5. Still nothing, and the error persists after a fresh retry → the deeper hunt in scenario 16.

### Step 5 — Decide who should have the port

**Goal:** make a deliberate, evidence-based choice between moving the old owner, moving the new service, or sharing through a second IP.

```bash
ss -Htn state established '( sport = :443 )' | wc -l                     # is the old owner in use right now?
sudo zcat -f /var/log/apache2/other_vhosts_access.log* | awk '{print $1}' | sort | uniq -c | sort -rn
sudo zcat -f /var/log/apache2/crm_access.log* | wc -l                    # crm has its own CustomLog, so count it separately
sudo grep -h -E '^authenticator' /etc/letsencrypt/renewal/*.conf 2>/dev/null | sort | uniq -c
```

```
18
  48211 app1.example.com:443
   1290 app1.example.com:80
    312 wiki.example.com:443
20377
      3 authenticator = apache
```

**What it means:** Apache is busy and serves two live sites and one dead one. Stopping it outright would take down app1 and crm. Three certificates also depend on Apache for renewal. So the right plan isn't "stop Apache". It's **option A** from section 9: Apache becomes a backend behind Traefik, and the dead wiki vhost is retired.

**Why this step (now):** this is where incidents become outages. Freeing a port is easy. Freeing it without breaking the applications behind it takes the evidence from section 9 *before* the change.

**Next step:** → Step 6 with the rung you chose: Rung 1 (move Apache) for option A, Rung 3 (stop/disable/mask) only if every vhost is migrated or retired.

### Step 6 — Free the port with the lowest rung that works

**Goal:** release 443 (and 80) with a change you can undo in one command.

```bash
# Option A (Rung 1): Apache moves to a backend port. Back up first, then edit.
sudo cp -a /etc/apache2 /root/apache2.bak-$(date +%F)
sudoedit /etc/apache2/ports.conf                       # Listen 192.0.2.10:8080 (instead of 80 and 443)
sudo a2dissite wiki-ssl                                # retire the dead vhost (scream test: config stays on disk)
sudoedit /etc/apache2/sites-available/crm-ssl.conf     # <VirtualHost *:8080>, SSL directives removed
sudoedit /etc/apache2/sites-available/app1-le-ssl.conf # the same for app1, or it is left on a port nobody listens on
sudo apache2ctl configtest && sudo systemctl restart apache2

# Option E (Rung 3), only when nothing behind Apache is needed anymore:
# sudo systemctl disable --now apache2 && sudo systemctl mask apache2
```

```
Site wiki-ssl disabled.
To activate the new configuration, you need to run:
  systemctl reload apache2
Syntax OK
```

**What it means:** `configtest` passed before the restart, so Apache came back on its new port. `a2dissite` removed only the `sites-enabled` symlink. The wiki config is still in `sites-available` for a one-command rollback.

**Why this step (now):** you change only after the evidence (Step 5) and the backup. Rung 1 keeps every live application running, and only its entry point changes.

**Next step:** → Step 7 to prove 443 is free and the new owner takes it.

### Step 7 — Verify the port is free, then start the new owner

**Goal:** confirm the release and the hand-over, end to end.

```bash
sudo ss -ltnp '( sport = :80 or sport = :443 )'                     # empty: 80/443 are free
docker start dokploy-traefik 2>/dev/null || true                    # or re-run the installer / redeploy
sudo ss -ltnp '( sport = :80 or sport = :443 or sport = :8080 )'    # Apache on 8080, Traefik on 80/443
docker ps --format '{{.Names}} {{.Ports}}' --filter name=traefik
curl -sv --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/ -o /dev/null 2>&1 | grep -E '^< HTTP|subject:|issuer:'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process

State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511       192.0.2.10:8080       0.0.0.0:*    users:(("apache2",pid=5012,fd=4))
LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*    users:(("docker-proxy",pid=6120,fd=7))
LISTEN 0      4096         0.0.0.0:80         0.0.0.0:*    users:(("docker-proxy",pid=6141,fd=7))
LISTEN 0      4096            [::]:443           [::]:*    users:(("docker-proxy",pid=6127,fd=7))
LISTEN 0      4096            [::]:80            [::]:*    users:(("docker-proxy",pid=6148,fd=7))
dokploy-traefik 0.0.0.0:80->80/tcp, [::]:80->80/tcp, 0.0.0.0:443->443/tcp, [::]:443->443/tcp, 0.0.0.0:443->443/udp, [::]:443->443/udp
*  subject: CN=crm.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
< HTTP/2 200
```

**What it means:** 80 and 443 now belong to docker-proxy, which means Traefik, and Apache sits on 8080. The request for `crm.example.com` gets a valid certificate and a 200. That proves Traefik routes the domain, through its file-provider route to Apache, and the chain works end to end.

**Why this step (now):** "the port is free" and "the new service works" are two separate claims, and both need evidence. `--resolve` tests the real TLS name against this exact server, whatever DNS currently says.

**Next step:** done → monitor the logs for an hour (Traefik's logs and the Apache backend's access log). A 404 or `TRAEFIK DEFAULT CERT` → the route isn't defined; a 502 → Traefik can't reach Apache on 8080 (container → host path, see [case study](21-case-apache-443-dokploy.md) and [containers playbook](26-playbook-containers-k8s.md)).

#### Decision tree (address in use)

```
"address already in use" on PORT
├─ errno 13 / 99 instead? ─────────────▶ privileges, SELinux, or IP not configured (not a conflict)
├─ ss -ltnp/-lunp 'sport = :PORT'
│   ├─ process ──▶ systemctl status PID ──▶ stale copy of itself? stop it
│   │                                   └─▶ other service ──▶ evidence (sec 9) ──▶ move it (rung 1) or retire (rung 3)
│   ├─ systemd pid 1 ──▶ .socket unit ──▶ stop + disable the socket
│   ├─ docker-proxy / dockerd ──▶ container / swarm service ──▶ change its publish or stop it
│   └─ nothing ──▶ docker ps / service ls / kubectl svc ──▶ allocator owner ──▶ else scenario 16
└─ verify: ss empty + nc "refused" from outside ──▶ start the new owner ──▶ curl --resolve
```

#### Fix & verify (address in use)

The fix is the rung chosen in Step 6. Verification has three parts, and all three must pass:

1. `ss` shows the **new** owner on the port, and the old owner only where you moved it.
2. From **another machine**, `curl -v --resolve DOMAIN:443:IP https://DOMAIN/` returns the expected status and certificate for every domain the old owner served.
3. Both the new owner's log and the old owner's access log (now behind the new proxy) show real traffic arriving.

#### Rollback (address in use)

```bash
# Undo Option A. The new owner must release 80/443 first (this takes down everything Traefik serves; that's the point)
docker stop dokploy-traefik
docker update --restart=no dokploy-traefik           # only if the rollback must survive a reboot
sudo cp -a /root/apache2.bak-DATE/. /etc/apache2/    # restore every edited file and the wiki-ssl symlink
sudo apache2ctl configtest && sudo systemctl restart apache2
sudo ss -ltnp '( sport = :80 or sport = :443 )'      # Apache back on 80/443
```

→ `cp -a BACKUP/. /etc/apache2/` overwrites what you changed and puts back what you removed, without deleting anything. Files you *added* after the backup stay, so remove them by hand if they conflict. Don't "clean restore" with `rm -rf /etc/apache2` followed by a copy: one typo in the path and the live config is gone.

Undoing Option E is just `sudo systemctl unmask apache2 && sudo systemctl enable --now apache2`. Put `restart: always` back on Traefik (`docker update --restart=always dokploy-traefik`) when you roll forward again.

#### Prevent it next time (address in use)

- Keep the **port inventory** (sections 8 and 9) current and check it *before* promising a client a port.
- New services go behind the **one reverse proxy** that owns 80/443. Apps get internal ports or Docker networks only, never their own public 443.
- Bind backends to loopback or an internal IP by default. Publish Docker ports as `127.0.0.1:PORT:PORT`, or not at all when Traefik can reach the container over a Docker network.
- Add a **pre-flight check** to deployment runbooks and CI: `ss -Htln 'sport = :PORT' | grep -q . && echo "PORT busy"`.

---

## 14. Scenario — listening but unreachable from outside

> 📚 **Know this first:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Configure Packet Filtering (Firewall)* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → *Troubleshooting* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)) · 3) Read: [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) · 4) Note: [Learn: networking](28-learn-networking.md) · 5) Practice: drill 9 in section 19.

**Level:** [L2 · Mid]. Steps 1–4 are within reach of a Junior. The capture and path analysis in Steps 5–6 are the Mid-level skill.

**Situation:** `ss` shows the service listening and `curl` works on the server itself, but other machines get a timeout or "connection refused". This is the "works on localhost" case from your case library, followed layer by layer.

### Step 1 — Classify the failure from the client

**Goal:** know whether packets are **refused** (they arrive, nothing answers on that address) or **dropped** (they never get an answer).

```bash
# From the CLIENT side (another machine)
nc -zv -w 3 192.0.2.10 8080
curl -sv --connect-timeout 5 http://192.0.2.10:8080/ -o /dev/null
```

```
nc: connect to 192.0.2.10 port 8080 (tcp) timed out: Operation now in progress
*   Trying 192.0.2.10:8080...
* Connection timed out after 5001 milliseconds
```

**What it means:** **timed out** → something drops packets (a firewall on the host or in the network, wrong routing, or the wrong IP). **Refused** → the host answered with a reset: nothing listens on *that* address (often a 127.0.0.1 bind), or a REJECT rule. **Succeeded but HTTP errors** → the network is fine and the problem is in the app or vhost; go to [site-down playbook](25-playbook-site-down.md).

**Why this step (now):** refused versus timeout splits the problem space in half before you log in anywhere. Refused points at the host's bind; timeout points at firewalls and paths.

**Next step:** refused → Step 2. Timeout → Step 2 anyway (it's quick), then Step 4. Success → [site-down playbook](25-playbook-site-down.md).

### Step 2 — Check the bind address on the server

**Goal:** make sure the socket accepts connections on the address the client uses.

```bash
sudo ss -ltnp 'sport = :8080'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      100        127.0.0.1:8080      0.0.0.0:*    users:(("java",pid=2788,fd=41))
```

**What it means:** `127.0.0.1:8080` accepts **only local** connections, so a remote client gets "refused". Other bad binds: `[::1]:8080` (IPv6 loopback only), `[::]:8080` with IPv6-only set while the client uses IPv4, or a specific IP that isn't the one the client targets (for example a private IP when the client uses the public NAT address). Good binds for remote access: `0.0.0.0:8080`, `*:8080`, or the exact IP the client dials.

**Why this step (now):** a wrong bind is the most common cause of "works locally" and it's a one-line check. Nothing else matters until the socket is reachable on the right address.

**Next step:** wrong bind → fix the app's listen setting (Fix & verify below), then re-test from the client. Bind is fine → Step 3.

### Step 3 — Test the real interface from the server itself

**Goal:** separate "the app doesn't answer on its LAN address" from "the network path is blocked".

```bash
curl -sv http://192.0.2.10:8080/ -o /dev/null 2>&1 | grep -E 'Connected|HTTP/|refused|timed out'
curl -sv http://127.0.0.1:8080/ -o /dev/null 2>&1 | grep -E 'Connected|HTTP/|refused|timed out'
```

```
* Connected to 192.0.2.10 (192.0.2.10) port 8080
< HTTP/1.1 200
* Connected to 127.0.0.1 (127.0.0.1) port 8080
< HTTP/1.1 200
```

**What it means:** the app answers on its LAN address from the server itself, so the socket and the app are fine. Whatever drops the client's packets sits on the **input path**: the host firewall for remote sources, or the network. Local tests use the loopback path and skip most INPUT rules, which is why they pass.

**Why this step (now):** it proves the application layer works before you spend time on firewalls, and it shows that "works on the server" doesn't test the same path as a remote client.

**Next step:** works locally on the LAN IP → Step 4. Fails even locally on the LAN IP → back to Step 2, or the app has its own allow-list (Tomcat `RemoteAddrValve`, Apache `Require ip`, a database `pg_hba.conf`, Redis protected mode).

### Step 4 — Read the host firewall

**Goal:** find a rule that drops or rejects the client's traffic, and prove it with counters or logs.

```bash
sudo ufw status verbose
sudo journalctl -k --since '-10 min' | grep -E 'UFW (BLOCK|AUDIT)' | grep 'DPT=8080' | tail -3
sudo nft list ruleset | grep -nE 'dport|policy' | head -40        # the full picture under UFW
sudo iptables -L DOCKER-USER -n -v --line-numbers 2>/dev/null      # for Docker-published ports
```

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80,443/tcp (Apache Full)   ALLOW IN    Anywhere
22/tcp (v6)                ALLOW IN    Anywhere (v6)
80,443/tcp (Apache Full (v6)) ALLOW IN    Anywhere (v6)

Oct 03 10:41:03 web01 kernel: [UFW BLOCK] IN=ens18 OUT= MAC=... SRC=198.51.100.23 DST=192.0.2.10 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=4021 DF PROTO=TCP SPT=53122 DPT=8080 WINDOW=64240 RES=0x00 SYN URGP=0
```

**What it means:** the default policy is *deny incoming*, there's no rule for 8080, and the kernel log shows the client's SYN being blocked (`[UFW BLOCK] ... SRC=198.51.100.23 ... DPT=8080`). That's direct proof, not inference. With Docker-published ports, UFW is the **wrong** place to look: they bypass INPUT entirely, and only `DOCKER-USER` filters them (section 2).

**Why this step (now):** the host firewall is the most likely drop point for a timeout when the app answers locally, and it's the only one you can read directly from the server. A log line is stronger evidence than any guess.

**Next step:** a block found → Fix & verify. No block and no log line → Step 5, to see whether the packets even arrive.

### Step 5 — Capture packets on the server

**Goal:** see whether the client's packets reach the server and what the server sends back.

```bash
sudo tcpdump -ni any 'tcp port 8080 and host 198.51.100.23'       # run this, then retry from the client
```

```
10:41:02.120331 ens18 In  IP 198.51.100.23.53122 > 192.0.2.10.8080: Flags [S], seq 1880433, win 64240, length 0
10:41:03.141220 ens18 In  IP 198.51.100.23.53122 > 192.0.2.10.8080: Flags [S], seq 1880433, win 64240, length 0
10:41:05.189101 ens18 In  IP 198.51.100.23.53122 > 192.0.2.10.8080: Flags [S], seq 1880433, win 64240, length 0
```

**What it means:**

| You see | Meaning |
|---|---|
| **No packets at all** | blocked **before** the server: network firewall or VLAN ACL, cloud security group, wrong routing, or the client uses another IP or DNS answer |
| **SYN in, nothing out** (as above: retransmitted SYNs) | dropped **on the server** after capture: host firewall (tcpdump sees packets before netfilter INPUT), or the app's backlog is full |
| **SYN in, RST out** | nothing listens on that IP:port, or a REJECT rule |
| **SYN in, SYN-ACK out, SYN retransmitted** | the reply leaves but never reaches the client: asymmetric return route, or a stateful firewall on the way back |

**Why this step (now):** a capture replaces reasoning with observation (blind spot #1 in your ops ladder). It pins the drop to before, on or after the server in one run. Read the [tcpdump zine](https://wizardzines.com/zines/tcpdump/) if the flags are new.

**Next step:** nothing arrives → Step 6. SYN in and nothing out, with no UFW log → `sudo nft list ruleset` in full (another tool's rules, Docker's, fail2ban's). SYN-ACK out and the client still retrying → Step 6 (return path).

### Step 6 — Check the path outside the host

**Goal:** find the drop between the client and the server.

```bash
ip route get 198.51.100.23                      # which interface/source the REPLY would use
sysctl net.ipv4.conf.all.rp_filter              # 1 = strict reverse-path filtering (drops asymmetric traffic), 2 = loose (Ubuntu default)
# From the client:
tracepath -n 192.0.2.10                         # where the path stops
nc -zv -w 3 192.0.2.10 22                       # does a port that IS allowed work? (isolates port-specific filtering)
```

```
198.51.100.23 via 192.0.2.1 dev ens18 src 192.0.2.10 uid 0
net.ipv4.conf.all.rp_filter = 2
```

**What it means:** the reply leaves through `ens18`, the interface the request arrived on, so routing is symmetric. If it showed a *different* interface on a multi-homed server, replies could be dropped by `rp_filter` or by a stateful firewall upstream. If port 22 works from the same client but 8080 doesn't, something filters **by port**: a network firewall, a cloud security group or NACL ([AWS reference](16-aws-cloud.md)), or a corporate proxy on the client side.

**Why this step (now):** only after the host is cleared does it make sense to involve the network team, and now you can hand them precise evidence: "SYNs from 198.51.100.23 to 192.0.2.10:8080 never arrive; port 22 from the same client works".

**Next step:** a network or cloud rule is found → change it through its owner. The path is fine → Step 7.

### Step 7 — Confirm the right application answers

**Goal:** make sure that once packets flow, the response is the expected app and not a default vhost or another service.

```bash
curl -sv -H 'Host: app.example.com' http://192.0.2.10:8080/ -o /dev/null 2>&1 | grep -E '^< (HTTP|Server|Location|Set-Cookie)'
```

```
< HTTP/1.1 200
< Set-Cookie: JSESSIONID=4F2A9C0B1D7E3A5C6B8D0E2F4A6C8E01; Path=/; HttpOnly
```

**What it means:** the expected Tomcat app answers: the `JSESSIONID` cookie is Java's, and Tomcat 8.5 and later send no `Server` header by default. A 404, an unexpected `Server` header (for example `Apache/2.4.58`) or a different cookie would mean a vhost or Host-header mismatch, which is an HTTP-layer problem ([site-down playbook](25-playbook-site-down.md)).

**Why this step (now):** "reachable" isn't the same as "working". This closes the scenario with application-level proof.

**Next step:** done. Record the bind and firewall decision in the inventory.

#### Decision tree (unreachable from outside)

```
client: nc -zv HOST PORT
├─ refused ──▶ server: ss -ltn ──▶ 127.0.0.1 / [::1] / wrong IP? ──▶ fix bind
│                                └─ bind OK ──▶ REJECT rule? (nft list ruleset)
├─ timeout ──▶ server: curl LAN-IP:PORT works? ──no──▶ bind / app allow-list
│              └─ yes ──▶ ufw status + "UFW BLOCK" in journalctl -k ──▶ allow rule
│                         └─ no log ──▶ tcpdump on server
│                              ├─ nothing arrives ──▶ network / SG / NACL / route / DNS
│                              ├─ SYN in, no reply ──▶ other netfilter rules / backlog
│                              └─ SYN-ACK out, client retries ──▶ return path / rp_filter
└─ success but HTTP error ──▶ vhost / app ──▶ playbook 25
```

#### Fix & verify (unreachable from outside)

**Bind fix** (when remote access is really wanted). Change the app's listen setting, for example Tomcat `address="0.0.0.0"` on the Connector, MySQL `bind-address`, PostgreSQL `listen_addresses`, Node `server.listen(PORT, '0.0.0.0')`. Restart, then `sudo ss -ltnp 'sport = :PORT'` must show the new bind.

> Before exposing a database or admin port, ask whether it *should* be reachable. Usually the right fix is a reverse proxy or an SSH tunnel, not `0.0.0.0` plus a firewall hole.

**Firewall fix.** Allow only the sources that need it, never "Anywhere" by reflex:

```bash
sudo ufw allow from 192.0.2.0/24 to any port 8080 proto tcp comment 'wiki backend from LAN'
sudo ufw status numbered
# Docker-published ports: filter in DOCKER-USER (match the ORIGINAL port; after DNAT the port is the container's)
sudo iptables -I DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 8081 --ctdir ORIGINAL ! -s 192.0.2.0/24 -j DROP
```

→ `--ctdir ORIGINAL` limits the match to client-to-server packets. Without it, replies to a container's own outgoing connections to some remote port 8081 would match too and be dropped.

→ The `DOCKER-USER` rule isn't persistent by itself. Make it permanent through your firewall management (for example UFW's `after.rules`, or a systemd unit run after Docker), and test after a reboot.

Verify from the client: `nc -zv -w 3 192.0.2.10 8080` reports `succeeded`, and `curl` returns the expected app.

#### Rollback (unreachable from outside)

```bash
sudo ufw status numbered          # find the rule number
sudo ufw delete NUMBER            # remove exactly that rule (asks for confirmation)
sudo iptables -D DOCKER-USER -i ens18 -p tcp -m conntrack --ctorigdstport 8081 --ctdir ORIGINAL ! -s 192.0.2.0/24 -j DROP
```

For a bind change, restore the previous listen setting and restart the service.

#### Prevent it next time (unreachable from outside)

- The deploy checklist includes a test **from another machine** (`nc -zv` and `curl -v`), not just from the server.
- Firewall rules are code: UFW rules in Ansible, Docker filtering in `DOCKER-USER` managed in one place, cloud security groups in Terraform.
- Run a blackbox probe from outside (Uptime Kuma, Prometheus blackbox exporter) for every public endpoint, so you learn about a closed path before the client does.
- Document every service's intended bind in the inventory: "127.0.0.1 by design" stops the next engineer from "fixing" it.

---

## 15. Scenario — I killed it and it came back

> 📚 **Know this first:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — *Creating a SYSTEMD Service* ([lesson](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page)) · 2) KodeKloud: *Docker Certified Associate* — *Restart Policies* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page)) · 3) Note: [systemd](07-services-systemd.md) and [Processes](05-processes.md) · 4) Practice: drill 3 in section 19.

**Level:** [L1 · Junior] for systemd and Docker restarters · [L2 · Mid] for out-of-band starters and auditd.

**Situation:** you killed a process (or stopped a container) to free a port. Seconds or minutes later the port is busy again, with a new PID. Something is restarting it. The job is to find that **something** and turn it off at the source, instead of killing the process in a loop.

### Step 1 — Record the new PID and its start time

**Goal:** confirm it really is a *new* process and note exactly when it started.

```bash
sudo ss -ltnp 'sport = :3001'
ps -o pid,ppid,user,lstart,etime,cmd -p "$(sudo lsof -t -iTCP:3001 -sTCP:LISTEN | head -n1)"
```

```
LISTEN 0      511       127.0.0.1:3001      0.0.0.0:*    users:(("node",pid=48891,fd=19))
    PID    PPID USER                      STARTED     ELAPSED CMD
  48891   48870 deploy   Sat Oct  3 11:20:01 2026       00:41 node /srv/crm/server.js
```

**What it means:** PID 48891 is new (the old one was 2210) and started at **11:20:01**, a suspiciously round time. Round minutes smell like cron or a timer. A start a few seconds after your kill smells like `Restart=` or a supervisor.

**Why this step (now):** the start time is your best clue to the restarter's *type*, and the new PID is the handle for every next step. Write both down before they change again.

**Next step:** → Step 2.

### Step 2 — Look at the parent and the process tree

**Goal:** see which process spawned the new one.

```bash
pstree -aps 48891
ps -o pid,ppid,user,cmd -p 48870
```

```
systemd,1 --system --deserialize=31
  `-PM2 v5.4.2: God,48870
      `-node,48891 /srv/crm/server.js

    PID    PPID USER     CMD
  48870       1 deploy   PM2 v5.4.2: God Daemon (/home/deploy/.pm2)
```

**What it means:** the parent is the **pm2 God daemon**. pm2 restarts apps that die, which is its whole job. Other parents you'll meet:

| Parent | Restarter |
|---|---|
| `systemd` (1), with the process in a `.service` cgroup | the unit's `Restart=` (or socket activation) |
| `containerd-shim-runc-v2` | Docker restart policy, Swarm, or Kubernetes |
| `supervisord`, `runsv`, `s6-supervise`, `monit` | that supervisor |
| `cron` / `CRON`, or a short-lived `sh -c` | a cron job (maybe a watchdog script) |
| `bash` / `sshd: user@pts` | a human or a script in a terminal (`while true; do …; done`) |

**Why this step (now):** the parent usually *is* the answer, and `pstree` costs nothing. When the parent is PID 1, the next step disambiguates.

**Next step:** pm2 or supervisord → Step 7 (stop it through that tool) and Step 6 (pm2 itself may be resurrected by cron). systemd → Step 3. containerd-shim → Step 5. cron or unknown → Step 6.

### Step 3 — Read the cgroup

**Goal:** get the manager's exact name from the one source a process can't fake.

```bash
cat /proc/48891/cgroup
```

```
0::/system.slice/pm2-deploy.service
```

**What it means:** pm2 itself runs inside `pm2-deploy.service`, so there are **two layers** of restarting: systemd keeps pm2 alive, and pm2 keeps the app alive. A `docker-….scope` here would point to Step 5, and `session-N.scope` to a human or terminal script.

**Why this step (now):** the parent shows the immediate restarter. The cgroup shows the whole chain of ownership, which is exactly what you must unwind from the top.

**Next step:** a systemd unit → Step 4. A container scope → Step 5.

### Step 4 — If systemd: read Restart= and the journal

**Goal:** confirm systemd's role and check its other start triggers (sockets, timers, dependencies).

```bash
systemctl show crm-worker.service -p Restart -p RestartUSec -p NRestarts -p TriggeredBy
journalctl -u crm-worker.service --since '-30 min' --no-pager | tail -6
systemctl list-dependencies --reverse crm-worker.service --no-pager
systemctl list-timers --all --no-pager | grep -i crm
```

```
Restart=on-failure
RestartUSec=5s
NRestarts=3
TriggeredBy=

Oct 03 11:02:14 web01 systemd[1]: crm-worker.service: Main process exited, code=killed, status=9/KILL
Oct 03 11:02:14 web01 systemd[1]: crm-worker.service: Failed with result 'signal'.
Oct 03 11:02:19 web01 systemd[1]: crm-worker.service: Scheduled restart job, restart counter is at 3.
Oct 03 11:02:19 web01 systemd[1]: Started crm-worker.service - CRM background worker.
```

**What it means:** your `kill -9` counted as a **failure** (`status=9/KILL`), so `Restart=on-failure` restarted the unit 5 seconds later. That's working as designed. `NRestarts=3` means you've been fighting it three times. `TriggeredBy=` is empty, so there's no socket or timer. If it listed `crm-worker.socket` or a `.timer`, those would start it as well.

**Why this step (now):** systemd logs every restart decision with its reason. Reading it takes seconds, and it tells you whether `stop` alone will be enough. It will be, because a deliberate `systemctl stop` never triggers `Restart=`.

**Next step:** → Step 7 (`systemctl stop`, plus `disable` or `mask` if it must stay down). But first → Step 6, to make sure nothing *outside* systemd starts it too.

### Step 5 — If a container: read the events and the owner

**Goal:** find which layer restarts the container: restart policy, Compose, Swarm or Kubernetes.

```bash
docker events --since 15m --until 0s --filter container=metabase
docker inspect -f 'restart={{.HostConfig.RestartPolicy.Name}} project={{index .Config.Labels "com.docker.compose.project"}} swarm={{index .Config.Labels "com.docker.swarm.service.name"}}' metabase
kubectl get pod POD -n NS -o jsonpath='{.metadata.ownerReferences[*].kind}{"/"}{.metadata.ownerReferences[*].name}{"\n"}' 2>/dev/null
```

```
2026-10-03T11:05:40.402771099Z container die 8c1f0e5b2d7a (exitCode=137, image=metabase/metabase:v0.50.20, name=metabase)
2026-10-03T11:05:41.023150877Z container start 8c1f0e5b2d7a (image=metabase/metabase:v0.50.20, name=metabase)

restart=unless-stopped project=metabase swarm=
```

**What it means:** the same container ID died (exit 137 = 128 + 9, SIGKILL) and started again within a second. There's no `container kill` or `container stop` event before the `die`, so the signal came from outside Docker (your `kill -9` on the host PID). That's Docker's **restart policy** reacting to a death it didn't initiate. `docker stop` would have been honored. A Swarm task would show up as a *new* container with a `com.docker.swarm.service.name` label. In Kubernetes, the `ownerReferences` (ReplicaSet, DaemonSet, StatefulSet, Job) name the controller you must scale or patch.

**Why this step (now):** containers have up to three restarters stacked (policy, Compose or Swarm, an orchestrator). The event stream and labels tell you which one acted.

**Next step:** → Step 7 with section 10, Rung 4 or 5. Then → Step 6 if a CI pipeline or Dokploy auto-deploy might recreate it.

### Step 6 — Hunt for out-of-band starters

**Goal:** find restarters that aren't the process's parent: cron watchdogs, `@reboot` lines, configuration management, CI/CD.

```bash
sudo grep -rIn -E 'crm|server\.js|pm2|3001' /etc/cron* /var/spool/cron/crontabs 2>/dev/null
journalctl --since '-30 min' -o short-iso --no-pager | grep -iE 'CRON|ansible|puppet|salt|pm2' | tail
systemctl list-timers --all --no-pager
ps -eo pid,cmd | grep -E '[p]uppet|[s]alt-minion|[c]hef-client|[a]nsible-pull'
```

```
/var/spool/cron/crontabs/deploy:4:@reboot cd /srv/crm && /usr/bin/pm2 resurrect
/var/spool/cron/crontabs/deploy:5:*/5 * * * * /home/deploy/bin/crm-watchdog.sh >/dev/null 2>&1

2026-10-03T11:20:01+00:00 web01 CRON[48862]: (deploy) CMD (/home/deploy/bin/crm-watchdog.sh >/dev/null 2>&1)
```

**What it means:** a **watchdog script runs every 5 minutes** and restarts the app, at 11:20:01, matching Step 1's round start time exactly. There's also an `@reboot pm2 resurrect`. Stopping pm2 alone wouldn't have helped: the watchdog would bring it back within 5 minutes, and the next reboot would too.

When nothing obvious turns up, catch the starter in the act with **auditd** (package `auditd`; adding a temporary audit rule is a small, reversible change):

```bash
sudo auditctl -w /usr/bin/node -p x -k who-starts-node        # log every execution of the node binary
# ... wait for the next restart, then:
sudo ausearch -k who-starts-node -i | grep -E 'type=SYSCALL' | tail -3
sudo auditctl -W /usr/bin/node -p x -k who-starts-node        # remove the rule afterwards
```

```
type=SYSCALL msg=audit(10/03/2026 11:25:01.512:4821) : arch=x86_64 syscall=execve success=yes exit=0 ppid=48990 pid=48991 auid=deploy uid=deploy comm=node exe=/usr/bin/node key=who-starts-node
```

→ `ppid=48990` is the starter. Run `ps -o pid,ppid,cmd -p 48990` while it's alive, or look up its parent chain in the audit log. `auid` is the *login* user behind it, even through `sudo`.

**Why this step (now):** this is the step people skip, and the reason the process "keeps coming back" after they've stopped the obvious manager. It's cheaper to grep every starter now than to discover the watchdog at 3 a.m.

**Next step:** → Step 7, unwinding **every** layer you found, from the outermost (cron, config management, CI) to the innermost (pm2, systemd).

### Step 7 — Stop it at the controller level, outermost first

**Goal:** turn off every restarter so the service stays down, and prove it stays down.

```bash
# 1. Outer layers first: the watchdog and the @reboot line (edit the crontab as its owner)
sudo crontab -u deploy -e                     # comment out the watchdog and @reboot lines, note the change ticket
# 2. The process manager
sudo -u deploy pm2 stop crm && sudo -u deploy pm2 save
# 3. If pm2 itself should go: its systemd unit
sudo systemctl disable --now pm2-deploy.service
# 4. Prove it stays down past the longest restart interval (here: the 5-minute cron)
sudo ss -ltnp 'sport = :3001'; date
```

```
[PM2] Applying action stopProcessId on app [crm](ids: [ 0 ])
[PM2] [crm](0) ✓
[PM2] Saving current process list...
[PM2] Successfully saved in /home/deploy/.pm2/dump.pm2
Removed "/etc/systemd/system/multi-user.target.wants/pm2-deploy.service".
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
Sat Oct  3 11:31:12 UTC 2026
```

**What it means:** pm2 stopped the app and saved the process list. Note that `pm2 stop` keeps `crm` in that list, marked stopped, and depending on the pm2 version a later `pm2 resurrect` (the `@reboot` line, or `pm2-deploy.service` at boot) can start it again. That's why the `@reboot` line is commented out and the unit disabled too. If pm2 must keep running for other apps, use `pm2 delete crm && pm2 save` instead (rollback is then `pm2 start ecosystem.config.js --only crm` in `/srv/crm`). The unit is disabled and stopped, and `ss` shows no listener. Check again after 11:35 (the next cron slot) and after the next reboot window.

**Why this step (now):** you remove restarters from the outside in. If you stop the inner one first, an outer one starts it again before you finish. Verifying past the longest interval is the only proof.

**Next step:** done. Record every mechanism you disabled in the inventory and the change ticket, since rollback needs the full list.

#### Decision tree (came back)

```
new PID on the port (ps -o lstart: when?)
├─ seconds after the kill ──▶ parent?
│   ├─ systemd + .service cgroup ──▶ Restart= (journal: "Scheduled restart job") ──▶ systemctl stop/disable/mask
│   ├─ systemd, port held by pid 1 ──▶ .socket unit ──▶ stop + disable the socket
│   ├─ containerd-shim ──▶ docker events / ownerReferences ──▶ policy / compose / swarm / k8s owner
│   └─ pm2 / supervisord / monit ──▶ stop + save in that tool (+ its own unit)
├─ on a round minute ──▶ cron / timer / watchdog ──▶ grep crontabs, list-timers
├─ after a deploy ──▶ CI/CD or Dokploy auto-deploy ──▶ disable the trigger
└─ after a config run ──▶ Ansible / Puppet / Salt ──▶ change desired state in code
nothing found ──▶ auditctl -w BINARY -p x ──▶ ausearch: ppid / auid of the starter
```

#### Fix & verify (came back)

The fix is to disable **every** layer, outermost first (Step 7), and verify past the longest interval:

1. No listener on the port after the longest cron or timer interval.
2. `systemctl is-enabled` reports `disabled` or `masked` for each unit involved.
3. The crontab no longer contains the lines (`sudo crontab -u USER -l`).
4. After the next planned reboot, the port is still free.

#### Rollback (came back)

Re-enable in the reverse order, innermost first:

```bash
sudo systemctl enable --now pm2-deploy.service
sudo -u deploy pm2 start crm && sudo -u deploy pm2 save
sudo crontab -u deploy -e                     # uncomment the @reboot and watchdog lines
sudo ss -ltnp 'sport = :3001'                 # listener back
```

#### Prevent it next time (came back)

- **One supervisor per process.** systemd *or* pm2 *or* a cron watchdog, never stacked. Prefer systemd units (or containers) with `Restart=on-failure`. A watchdog in cron is a smell.
- Record the **start mechanism** in the inventory for every service ("pm2 under pm2-deploy.service; @reboot cron; watchdog cron").
- Stop services through their manager (`systemctl stop`, `docker stop`, `pm2 stop`), never with `kill -9`, so restart policies don't fight you.
- Keep cron, systemd units and pm2 ecosystem files in configuration management, so they're visible in a repository instead of hidden on the box.

---

## 16. Scenario — port answers but ss shows nothing

> 📚 **Know this first:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → *Port Redirection and NAT* ([lesson](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 2) KodeKloud: *Docker Certified Associate* — *Networking Deep Dive – Docker* ([lesson](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Docker/page)) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking → *Prerequisite Network Namespaces* ([lesson](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Network-Namespaces/page)) · 4) Note: section 2 of this module · 5) Practice: drill 4 in section 19.

**Level:** [L2 · Mid] for Docker NAT · [L3 · Senior] for IPVS, eBPF, namespaces and conntrack.

**Situation:** from outside, `nc -zv 192.0.2.10 8081` succeeds (or a NodePort serves pages), but on the server `ss -ltnp` shows no listener on that port. Something answers without a visible socket. On Docker and Kubernetes hosts this is **normal**. The job is to name the mechanism.

### Step 1 — Prove what answers and from where

**Goal:** confirm the port really answers, and capture *what* answers (banner, headers, certificate).

```bash
# From another machine
nc -zv -w 3 192.0.2.10 8081
curl -sv http://192.0.2.10:8081/ -o /dev/null 2>&1 | grep -E 'Connected|^< (HTTP|Server|X-)'
```

```
Connection to 192.0.2.10 8081 port [tcp/*] succeeded!
* Connected to 192.0.2.10 (192.0.2.10) port 8081
< HTTP/1.1 200 OK
< X-Frame-Options: DENY
< Server: Jetty(11.0.24)
```

**What it means:** something accepts TCP on 8081 and answers HTTP as a Jetty server, which is Java. That's already a strong hint about the application behind it.

**Why this step (now):** before you hunt for an invisible owner, make sure there *is* one, and collect its fingerprint so you can recognize it later.

**Next step:** → Step 2.

### Step 2 — Make sure ss isn't hiding it and the IP is local

**Goal:** rule out the boring explanations: no root, the wrong protocol or family, or **another machine** answering for this IP.

```bash
sudo ss -ltnp 'sport = :8081'; sudo ss -lunp 'sport = :8081'     # as root, both protocols, all families
ip -br addr | grep -w 192.0.2.10                                  # is 192.0.2.10 configured on THIS host?
# From another host on the same LAN: which MAC answers for the IP? (two different MACs = IP conflict)
arping -c 3 -I ens18 192.0.2.10
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process

ens18            UP             192.0.2.10/24 fe80::be24:11ff:fe4a:1b2c/64

ARPING 192.0.2.10
60 bytes from bc:24:11:4a:1b:2c (192.0.2.10): index=0 time=0.301 msec
60 bytes from bc:24:11:4a:1b:2c (192.0.2.10): index=1 time=0.288 msec
```

**What it means:** really no listener, the IP is on this host, and one consistent MAC answers. So *this* machine answers without a socket. If the IP were missing from `ip addr`, or `arping` showed two MACs, another machine would be answering: a keepalived VIP that moved, MetalLB announcing from another node, or a duplicate IP. You'd be debugging the wrong box.

**Why this step (now):** it's cheap and it prevents the most embarrassing outcome, hours spent on a server that never received the traffic.

**Next step:** → Step 3 (NAT rules).

### Step 3 — Look for NAT rules

**Goal:** find a DNAT or REDIRECT rule that rewrites the port before any socket lookup.

```bash
sudo iptables-save -t nat | grep -E -- '--dport 8081\b'
sudo nft list ruleset | grep -nE 'dport 8081\b'               # nftables-native rules (kube-proxy nftables mode; Docker 29+ with the experimental nftables backend)
sudo iptables-save -t nat | grep -E -- '-j REDIRECT'          # local port redirects (e.g. 443 → 8443)
```

```
-A DOCKER ! -i br-5e1f0c7a9b2d -p tcp -m tcp --dport 8081 -j DNAT --to-destination 172.18.0.3:3000
```

**What it means:** Docker's `DOCKER` chain DNATs 8081 to `172.18.0.3:3000`, a container. With the userland proxy disabled, there's no docker-proxy and therefore no socket. Other signatures you may find:

| Rule | Owner |
|---|---|
| `-A DOCKER ... --dport P -j DNAT --to-destination 172.x.x.x:PORT` | a Docker-published container |
| `-A KUBE-NODEPORTS ... --comment "NS/SVC:port" ... --dport P` | a Kubernetes NodePort Service |
| `-A CNI-DN-... --dport P -j DNAT --to-destination 10.244.x.x:PORT` | a pod hostPort |
| `-A PREROUTING ... --dport 443 -j REDIRECT --to-ports 8443` | a manual redirect: the app listens on 8443 (check `ss` for **8443**) |
| `-A DOCKER-INGRESS ... --dport P -j DNAT --to-destination 172.x.x.x:P` | Swarm ingress (dockerd usually also shows in `ss`) |

**Why this step (now):** NAT is the most common invisible owner on container hosts, and the rule names the real destination directly.

**Next step:** a Docker DNAT → Step 4. A KUBE or CNI rule → Step 5. A REDIRECT → run `ss` on the target port and continue with section 4. Nothing → Step 5 anyway (IPVS and eBPF don't appear in iptables).

### Step 4 — Check Docker and Swarm

**Goal:** turn the container IP into a container name, and confirm why there's no docker-proxy.

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E ':8081->'
docker network inspect $(docker network ls -q) --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}' | grep -w '172.18.0.3'
grep -i userland /etc/docker/daemon.json
```

```
metabase	0.0.0.0:8081->3000/tcp, [::]:8081->3000/tcp
metabase 172.18.0.3/16
  "userland-proxy": false,
```

**What it means:** it's the `metabase` container. `"userland-proxy": false` explains the empty `ss`, since Docker relies purely on NAT. The Jetty fingerprint from Step 1 matches Metabase, a Java app. Mystery solved.

**Why this step (now):** the NAT rule gave an IP. Docker's own metadata gives the name, the Compose project and the logs, which is what you need for the inventory.

**Next step:** → Fix & verify. Not Docker → Step 5.

### Step 5 — Check Kubernetes, IPVS and eBPF

**Goal:** find Service-level owners that don't use iptables.

```bash
curl -s http://127.0.0.1:10249/proxyMode; echo                   # kube-proxy mode on this node
sudo ipvsadm -Ln | grep -A3 ':8081'                              # IPVS virtual servers (kube-proxy ipvs, keepalived/LVS)
kubectl get svc -A -o wide 2>/dev/null | grep -E ':8081/|8081:'
kubectl -n kube-system exec ds/cilium -- cilium-dbg service list 2>/dev/null | grep 8081   # Cilium eBPF
```

```
ipvs
TCP  192.0.2.10:8081 rr
  -> 10.244.1.12:8080             Masq    1      2          0
```

**What it means:** in an IPVS-mode cluster, the node's kernel load-balances 8081 to a pod. Because 8081 is outside the default NodePort range (30000–32767), the Service behind it uses `externalIPs` (or the LoadBalancer IP) set to this node's address, or the cluster runs a custom `--service-node-port-range`; `kubectl get svc -A -o wide` shows which. IPVS virtual servers are kernel objects, not sockets, so `ss` can't show them. The same applies to keepalived/LVS setups outside Kubernetes. With Cilium's kube-proxy replacement, the Service lives in eBPF maps and only `cilium-dbg service list` shows it.

**Why this step (now):** after NAT, these are the remaining kernel-level owners. Each has its own tool, and none of them appears in `ss` or iptables.

**Next step:** found → map the Service to its pods (section 7) → Fix & verify. Nothing → Step 6.

### Step 6 — Check other network namespaces and kernel sockets

**Goal:** catch listeners that live in another network namespace, or inside the kernel itself.

```bash
sudo lsns -t net                                              # every network namespace and a PID inside it
sudo nsenter -t PID -n ss -ltnp 'sport = :8081'               # look inside one of them
sudo ss -ltnp 'sport = :2049'                                 # kernel sockets show with NO process, even as root
lsmod | grep -E '^nfsd|^lockd'
```

```
        NS TYPE NPROCS   PID USER    NETNSID NSFS COMMAND
4026531840 net     212     1 root unassigned      /sbin/init
4026532611 net       3  3420 2000          0      java -jar /app/metabase.jar

State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      64           0.0.0.0:2049      0.0.0.0:*
nfsd                  860160  13
```

**What it means:** a listener inside another namespace answers only if traffic is routed or NAT-ed into that namespace, so you would also have found a rule in Step 3 or 4. Port 2049 shows **no process** because the NFS server is a kernel module (`nfsd`). Manage it with `systemctl status nfs-server`, not with `kill`.

**Why this step (now):** namespaces and kernel sockets are the last places a listener can hide. By this point you've ruled out every user-space explanation.

**Next step:** → Step 7, to confirm with a live connection.

### Step 7 — Follow one connection through conntrack

**Goal:** prove the real backend from the kernel's connection-tracking table, whatever mechanism did the rewriting.

```bash
# Hold a connection open from the client (e.g. curl a slow page, or nc 192.0.2.10 8081), then on the server:
sudo conntrack -L -p tcp --dport 8081 2>/dev/null | head -3     # package: conntrack
```

```
tcp      6 431999 ESTABLISHED src=198.51.100.23 dst=192.0.2.10 sport=53510 dport=8081 src=172.18.0.3 dst=198.51.100.23 sport=3000 dport=53510 [ASSURED] mark=0 use=1
```

**What it means:** the first tuple is what the client sent (to `192.0.2.10:8081`). The second is the **reply direction**: it comes from `172.18.0.3:3000`, the real backend. Conntrack shows the translation no matter whether iptables, nftables or IPVS did it.

**Why this step (now):** it's the ground truth for any NAT-based owner and settles disagreements between tools.

**Next step:** done → Fix & verify.

#### Decision tree (answers without listener)

```
port answers, ss shows nothing
├─ IP not on this host / two MACs ──▶ another machine answers (VIP, MetalLB, conflict)
├─ iptables-save / nft: DNAT or REDIRECT for the port?
│   ├─ DOCKER chain ──▶ docker ps / network inspect ──▶ container (userland-proxy off)
│   ├─ KUBE-NODEPORTS ──▶ comment names NS/SVC ──▶ kubectl get endpointslices
│   ├─ CNI-DN ──▶ hostPort pod (section 7)
│   └─ REDIRECT ──▶ ss on the --to-ports port
├─ ipvsadm -Ln ──▶ IPVS Service (kube-proxy ipvs / LVS)
├─ cilium-dbg service list ──▶ eBPF Service
├─ lsns -t net + nsenter ──▶ listener in another namespace
├─ ss line with no process ──▶ kernel socket (nfsd, lockd)
└─ confirm: conntrack -L --dport PORT ──▶ reply tuple = real backend
```

#### Fix & verify (answers without listener)

Usually nothing is broken. The fix is to **record the owner** in the inventory and decide whether the exposure is intended. If it isn't (for example Metabase reachable from anywhere on 8081):

```bash
# Publish only on loopback (Traefik reaches it over a Docker network anyway): edit the compose file
#   ports: ["127.0.0.1:8081:3000"]      (or remove the ports: block)
cd /opt/metabase && docker compose up -d
docker ps --format '{{.Names}}\t{{.Ports}}' | grep metabase
```

Verify from another machine: `nc -zv -w 3 192.0.2.10 8081` must now be refused or time out, while the app still works through its intended route (Traefik domain or SSH tunnel).

#### Rollback (answers without listener)

Restore the previous `ports:` line in the compose file and run `docker compose up -d` again. Keep the old file as `docker-compose.yml.bak-DATE` before editing.

#### Prevent it next time (answers without listener)

- Run the inventory script (section 8). Its second table lists rule-owned ports precisely so they don't surprise you.
- Make "no host ports for apps behind Traefik" a rule. Use Docker networks (`dokploy-network`) instead of `ports:`.
- Remember that **UFW doesn't see Docker-published ports**. Filter them in `DOCKER-USER`, or don't publish them.
- On Kubernetes, prefer Ingress over NodePort for anything user-facing, and keep NodePort Services documented.

---

## 17. Scenario — which application is behind this URL

> 📚 **Know this first:** 1) Note: section 5 of this module and [DNS reference](08-dns.md) (quick refresher) · 2) KodeKloud: *DevOps Pre-Requisite Course* — Web Server → *Apache Web Server* ([lesson](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page)) · 3) KodeKloud: *Demystifying DNS* — Miscellaneous → *Troubleshooting DNS* ([lesson](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page)) · 4) Read: everything curl, *Name resolve tricks* ([link](https://everything.curl.dev/usingcurl/connections/name.html)) · 5) Practice: drill 6 in section 19.

**Level:** [L2 · Mid]. In the Apache → Dokploy migration you run this once per domain, so a Junior should practise it early.

**Situation:** someone gives you a URL, `https://crm.example.com`, and asks "what is this, where does it run, who owns it?". In the Apache migration you had to answer this for every domain on the server. The method walks from DNS down to a process and a log line.

### Step 1 — Resolve the name the way clients do

**Goal:** get the IP the clients actually use, and spot CDNs or load balancers in between.

```bash
getent ahosts crm.example.com | head -3        # what curl/browsers on this machine get (follows /etc/hosts too)
dig +short crm.example.com                     # what DNS says (CNAME chain + A)
dig +short -x 192.0.2.10                       # reverse name, sometimes a hint at the host's role
```

```
192.0.2.10      STREAM crm.example.com
192.0.2.10      DGRAM
192.0.2.10      RAW
192.0.2.10
web01.example.com.
```

**What it means:** the name points straight at `192.0.2.10` (web01), with no CNAME to a CDN or cloud load balancer. A CNAME like `xyz.cdn-provider.net`, or an IP in a cloud provider's range, would mean you must first find the **origin** behind it (check the CDN or LB configuration).

**Why this step (now):** every later step happens on a specific host, and this step names it. `getent` follows the same resolution path as the clients, while `dig` asks DNS only. Compare them when results differ ([DNS reference](08-dns.md)).

**Next step:** → Step 2.

### Step 2 — Ask the endpoint who it is

**Goal:** fingerprint the server software and the certificate without touching the server.

```bash
curl -svk --resolve crm.example.com:443:192.0.2.10 https://crm.example.com/ -o /dev/null 2>&1 \
  | grep -E 'subject:|issuer:|^< (HTTP|server|x-powered-by|set-cookie|via)' -i
```

```
*  subject: CN=crm.example.com
*  issuer: C=US; O=Let's Encrypt; CN=R11
< HTTP/1.1 200 OK
< Server: Apache/2.4.58 (Ubuntu)
< X-Powered-By: Express
< Set-Cookie: connect.sid=s%3A...; Path=/; HttpOnly
```

**What it means:** **Apache** terminates TLS (`Server:`), but the app behind it is **Node.js Express** (`X-Powered-By: Express`, the `connect.sid` session cookie). Useful fingerprints: `PHPSESSID` (PHP), `JSESSIONID` (Java), `laravel_session` (Laravel), `csrftoken` (Django), `Via` (proxies), and `TRAEFIK DEFAULT CERT` as the subject (Traefik with no matching router).

**Why this step (now):** headers and cookies tell you what kind of application to look for before you log in. That saves a lot of guessing at Step 5.

**Next step:** → Step 3 on the host from Step 1.

### Step 3 — Find the listener on that host

**Goal:** name the front process on port 443.

```bash
sudo ss -ltnp 'sport = :443'
```

```
LISTEN 0      511                *:443             *:*    users:(("apache2",pid=1344,fd=6),("apache2",pid=1343,fd=6),("apache2",pid=1201,fd=6))
```

**What it means:** Apache owns 443, consistent with the `Server:` header. On a Dokploy host you would see docker-proxy (Traefik). On Kubernetes you would see nothing or the ingress controller (section 7).

**Why this step (now):** it confirms the fingerprint from the inside and tells you which proxy's config to read next.

**Next step:** → Step 4.

### Step 4 — Ask the proxy which vhost or router matches

**Goal:** find the exact config block that handles `crm.example.com`.

```bash
sudo apache2ctl -S 2>/dev/null | grep -E 'crm\.example\.com|default server'
sudo grep -nE 'ServerName|ServerAlias|ProxyPass|DocumentRoot|CustomLog|ErrorLog' /etc/apache2/sites-enabled/crm-ssl.conf
```

```
         default server app1.example.com (/etc/apache2/sites-enabled/app1-le-ssl.conf:2)
         port 443 namevhost crm.example.com (/etc/apache2/sites-enabled/crm-ssl.conf:2)
3:      ServerName crm.example.com
7:      ProxyPass / http://127.0.0.1:3001/
8:      ProxyPassReverse / http://127.0.0.1:3001/
10:     CustomLog ${APACHE_LOG_DIR}/crm_access.log combined
11:     ErrorLog ${APACHE_LOG_DIR}/crm_error.log
```

**What it means:** the crm vhost proxies everything to `127.0.0.1:3001` and logs to `crm_access.log`. If the name weren't listed at all, requests for it would land on the **default server** (app1), which is a classic "the domain shows the wrong site" bug. For Nginx, Traefik or Kubernetes Ingress, use the equivalents in section 5.

**Why this step (now):** the proxy config is the only place where the domain → backend mapping is written down.

**Next step:** a `ProxyPass` or `proxy_pass` → Step 5. A `DocumentRoot` with PHP → Step 5, PHP variant.

### Step 5 — Follow the backend to a process

**Goal:** turn `127.0.0.1:3001` (or a docroot) into a process, unit, config and logs.

```bash
sudo ss -ltnp 'sport = :3001'
ps -o pid,user,unit,cmd -p 2210
sudo readlink /proc/2210/cwd
# PHP variant: which FPM pool serves the docroot's socket?
sudo grep -lE 'listen = /run/php/php8.3-fpm.sock' /etc/php/8.3/fpm/pool.d/*.conf
```

```
LISTEN 0      511       127.0.0.1:3001      0.0.0.0:*    users:(("node",pid=2210,fd=19))
    PID USER     UNIT                         CMD
   2210 deploy   pm2-deploy.service           node /srv/crm/server.js
/srv/crm
/etc/php/8.3/fpm/pool.d/www.conf
```

**What it means:** `crm.example.com` is the Node app in `/srv/crm`, run as `deploy` by pm2 (inside `pm2-deploy.service`). From here, section 4 Steps 4–7 give the config (`.env`, ecosystem file) and logs (`~/.pm2/logs/`).

**Why this step (now):** the proxy only forwards. The application, and everything you need to migrate it, is behind that port.

**Next step:** → Step 6 to prove the mapping with a real request.

### Step 6 — Prove it with a marker request

**Goal:** send one uniquely tagged request and watch it appear in each layer's log. This turns inference into proof.

```bash
MARK="trace-$(date +%s)"
curl -s -o /dev/null --resolve crm.example.com:443:192.0.2.10 "https://crm.example.com/?$MARK"
sudo grep "$MARK" /var/log/apache2/crm_access.log
sudo grep -h "$MARK" /home/deploy/.pm2/logs/crm-out.log 2>/dev/null | tail -1
```

```
198.51.100.23 - - [03/Oct/2026:11:42:07 +0000] "GET /?trace-1791027727 HTTP/1.1" 200 5120 "-" "curl/8.5.0"
GET /?trace-1791027727 200 12.418 ms - 5120
```

**What it means:** the tagged request passed through the **crm vhost** (Apache's log) and was served by the **Node app** (its own request log). The mapping is proven end to end. If the marker appeared in a *different* vhost's log, the routing isn't what the config suggests: check `ServerAlias` lines, the default vhost, or a second proxy in front.

**Why this step (now):** config files show intent, and logs show what actually happened. This is the strongest evidence you can attach to the inventory.

**Next step:** → Step 7.

### Step 7 — Record it in the inventory

**Goal:** make the answer permanent and shareable.

```bash
printf '%s\n' "| 443 (vhost crm) → 127.0.0.1:3001 | apache2 → pm2-deploy.service (node, /srv/crm) | crm.example.com | /srv/crm/.env | crm_access.log, ~/.pm2/logs/crm-*.log | proven by marker $(date +%F) |" >> ~/inventory-web01.md
tail -n 1 ~/inventory-web01.md                   # check the row landed as intended
```

```
| 443 (vhost crm) → 127.0.0.1:3001 | apache2 → pm2-deploy.service (node, /srv/crm) | crm.example.com | /srv/crm/.env | crm_access.log, ~/.pm2/logs/crm-*.log | proven by marker 2026-10-03 |
```

**What it means:** one table row now answers "what is crm.example.com" for everyone, including you in six months. If `tail` shows a literal `$(date +%F)`, you used single quotes around the row, so fix the date by hand.

**Why this step (now):** the investigation is worthless if it lives only in your terminal scrollback. The inventory feeds section 9's decisions and the migration plan ([case study](21-case-apache-443-dokploy.md)).

**Next step:** repeat for every name in `apache2ctl -S`, then decide keep, migrate or retire for each (section 9).

#### Decision tree (URL to app)

```
URL
├─ getent ahosts / dig ──▶ CNAME to CDN/LB? ──▶ find the origin first
├─ curl -v --resolve ──▶ Server / X-Powered-By / cookies / cert (fingerprint)
├─ ss -ltnp :443 on the origin
│   ├─ apache2 ──▶ apache2ctl -S ──▶ vhost ──▶ ProxyPass port │ DocumentRoot + PHP-FPM pool
│   ├─ nginx ──▶ nginx -T ──▶ server_name ──▶ proxy_pass │ root + fastcgi_pass
│   ├─ docker-proxy (Traefik) ──▶ labels / dynamic files ──▶ router rule ──▶ container
│   └─ nothing / ingress (K8s) ──▶ kubectl get ingress -A ──▶ Service ──▶ pods
├─ backend port ──▶ section 4 chain (PID → unit → config → logs)
└─ marker request in every layer's log ──▶ proven ──▶ inventory row
```

#### Fix & verify (URL to app)

Nothing is changed in this scenario. The deliverable is the **proven mapping** (domain → proxy vhost or router → backend port → process → unit → config → logs → owner). It's verified when the marker request appears in the expected logs, and in no other vhost's log. There's no rollback, because nothing was modified.

#### Prevent it next time (URL to app)

- Give every vhost or router **its own access log** (Apache `CustomLog` per vhost, Traefik access logs with the router name), so the marker trick and per-site traffic counts always work.
- Add a comment block at the top of each vhost file: owner, ticket, backend, date.
- After the migration, Dokploy's application pages *are* the inventory (domain, image, ports, logs in one place). Keep an exported copy in your runbook repository anyway.

---

## 18. Quick reference across platforms

> 📚 **Study path:** 1) Note: [Cheatsheet](19-cheatsheet.md) next to this table · 2) Practice: once a week, rebuild this table from memory and compare. Every gap is a section to reread.

**Level:** all stages. A Junior should know the Linux column by heart. A Senior should know all of it.

| Task | Linux | Windows | macOS |
|---|---|---|---|
| All listeners | `sudo ss -tulpn` | `Get-NetTCPConnection -State Listen` | `sudo lsof -nP -iTCP -sTCP:LISTEN` |
| One port | `sudo ss -ltnp 'sport = :PORT'` | `netstat -ano -p tcp`, then `findstr :PORT` | `sudo lsof -nP -iTCP:PORT -sTCP:LISTEN` |
| Who is connected | `ss -tn state established '( sport = :PORT )'` | `Get-NetTCPConnection -LocalPort PORT -State Established` | `lsof -nP -iTCP:PORT -sTCP:ESTABLISHED` |
| PID details | `ps -o pid,ppid,user,lstart,cmd -p PID` | `Get-CimInstance Win32_Process -Filter "ProcessId = PID"` | `ps -o pid,ppid,user,lstart,command -p PID` |
| PID → manager | `systemctl status PID`, `cat /proc/PID/cgroup` | `tasklist /svc /fi "PID eq PID"` | `launchctl list` (PID column) |
| Effective config | `systemctl cat UNIT`, the app's dump flag | `sc.exe qc NAME`, app directory | `launchctl print gui/UID/LABEL` |
| Logs | `journalctl -u UNIT`, `lsof -p PID`, `/proc/PID/fd/1` | `Get-WinEvent`, app directory, IIS `W3SVCn` | plist stdout path, `log show` |
| Stop now | `systemctl stop UNIT` (+ `.socket`) | `Stop-Service NAME` | `launchctl bootout DOMAIN/LABEL`, `brew services stop` |
| Keep it stopped | `systemctl disable` / `mask` | `Set-Service NAME -StartupType Disabled` | `launchctl disable DOMAIN/LABEL` |
| Hidden owners | socket units, Docker NAT, Swarm ingress, kube-proxy, IPVS | http.sys (PID 4), excluded port ranges | AirPlay (5000/7000), Docker Desktop backend |

| Task | Docker / Compose | Swarm (Dokploy) | Kubernetes |
|---|---|---|---|
| Who publishes PORT | `docker ps --format '{{.Names}} {{.Ports}}'` | `docker service ls` | `kubectl get svc -A` (NodePort), hostPort jq query |
| Details | `docker inspect CONTAINER` | `docker service inspect SERVICE` | `kubectl describe svc/pod` |
| Process on the host | `docker inspect -f '{{.State.Pid}}'` | `docker service ps` → node → `docker inspect` | `crictl inspect ID` (`.info.pid`) |
| Logs | `docker logs CONTAINER` | `docker service logs SERVICE` | `kubectl logs POD` |
| Stop, keep it stopped | `docker stop` + `docker update --restart=no`, or `compose down` | `docker service scale S=0`, `--publish-rm`, Dokploy Stop | `kubectl scale --replicas=0`, patch the Service type |

---

## 19. Practice drills and exit test

> 📚 **Study path:** 1) KodeKloud: *Linux Challenges* (free) as your L1 check ([course](https://kodekloud.com/courses/linux-challenges)) · 2) KodeKloud Engineer for daily reps ([link](https://engineer.kodekloud.com/)) · 3) Practice: [SadServers](https://sadservers.com/scenarios) for timed broken servers · 4) Lab: KodeKloud Ubuntu playground ([link](https://kodekloud.com/playgrounds/playground-ubuntu)) or your homelab VM for the drills below.

**Level:** every drill carries its own tag. The stage exit test at the end of this section tells you which drills prove which stage.

Reading this module gives you the commands. The drills make them reflexes. Do them on a **homelab VM**, never on the client's server. They line up with your ops ladder: L1 (Operator) exit test, L2 (Troubleshooter) and the L3 Dokploy migration.

### Self-check questions

Answer out loud or in writing, without looking. The section number in brackets is where to check your answer.

1. `ss` shows `*:443` owned by three `apache2` PIDs. Which PID do you act on, and through which tool? (2, 4)
2. Why can't Traefik bind `0.0.0.0:443` while Apache holds only `192.0.2.10:443`? (2)
3. You ran `systemctl stop cockpit.service` and port 9090 still answers. Why, and what do you stop instead? (2, 10)
4. `docker run -p 8081:3000` makes port 8081 answer. Name the two mechanisms involved, and explain why `ufw deny 8081` doesn't block it. (2)
5. On a Kubernetes node, NodePort 30080 answers but `ss` shows nothing. Which command names the owning Service from the node alone? (7, 16)
6. A process's `/proc/PID/fd/1` points to `pipe:[48211]`. Where are its logs most likely to be? (4)
7. Name three independent signals you'd collect before retiring a vhost, and the weakness of each. (9)
8. What's the difference between `stop`, `disable` and `mask`? Which of them survive a reboot? (10)
9. You `kill -9` a process and a new PID holds the port 5 seconds later. Name three possible restarters and the command that reveals each. (10, 15)
10. Docker says "port is already allocated" in one case and "Error starting userland proxy: … address already in use" in another. Which owner does each point to? (13)
11. A client gets a timeout on port 8080, but `curl` on the server works. Which three checks come next, in order? (14)
12. How do you prove which application serves `crm.example.com` without trusting the config files? (17)
13. Why can moving Apache off port 80 break certificate renewals, and how do you find the affected certificates before the change? (9)
14. [L3 · Senior] After moving Apache to 81/444, what is still exposed, what do visitors of the old domains see, and what is the clean end state? (9, 35)

### Build the lab once

On an Ubuntu 24.04 VM, recreate the incident's shape:

1. Install Apache with three name-based vhosts (use `/etc/hosts` entries on your workstation for `app1.example.com`, `crm.example.com` and `wiki.example.com`).
2. Make one of them a `ProxyPass` to a tiny backend: `python3 -m http.server 3001 --bind 127.0.0.1` wrapped in a systemd unit with `Restart=on-failure`.
3. Add a socket-activated service: an `echo.socket` with `ListenStream=9999` and `Accept=yes`, plus a matching `echo@.service` template. The [Arch Wiki: systemd](https://wiki.archlinux.org/title/Systemd) page shows the pattern.
4. Install Docker, set `"userland-proxy": false` in `/etc/docker/daemon.json`, and run one container published on 8081 with `--restart always`.
5. Add a cron watchdog line that restarts the Python backend every 5 minutes if it's down.

### Drills

1. **The five-minute drill (L1 exit test).** [L1 · Junior] Have someone (or a script) pick a random listening port on the lab VM. Within 5 minutes, write down the process, the unit or container, the config file and the command that shows its logs, using only section 4. Repeat until you pass with every port, including 22 (socket-activated) and 8081 (NAT only).
2. **Inventory script.** [L1 · Junior → L2 · Mid] Run the section 8 script, fix every ShellCheck warning, and add an ENABLED column. Run it from cron daily and diff the outputs.
3. **Came back.** [L1 · Junior → L2 · Mid] Kill the Python backend with `kill -9` and find all three restarters (systemd `Restart=`, the cron watchdog, and for the container the restart policy) with the scenario 15 method. Then disable them outermost first, and prove the port stays free past the 5-minute interval.
4. **Invisible owner.** [L2 · Mid] Prove port 8081 answers from another VM while `ss` shows nothing. Name the container from `iptables-save` and `conntrack` alone (scenario 16), without looking at `docker ps` first.
5. **Address in use.** [L2 · Mid → L3 · Senior] Try to start a second web server (for example `docker run -p 443:443 traefik`) and work through scenario 13 to a clean hand-over: Apache moves to 8080 and Traefik takes 443. Then roll back, and time the rollback.
6. **Which app is this URL.** [L2 · Mid] For each of the three domains, produce a proven inventory row with a marker request (scenario 17).
7. **Kubernetes (CKA).** [L3 · Senior] In your homelab cluster, create a NodePort Service and a pod with a `hostPort`. From the node, using only `iptables-save` or `ipvsadm` plus `crictl`, name both owners. Then move a static pod manifest out of `/etc/kubernetes/manifests`, watch the pod disappear, and put it back.
8. **Change request.** [L4 · Lead] Write the change request for "move Apache off 443 behind Traefik" in GitLab's format (criticality, steps, verification, rollback), using your lab timings. This is the L4 drill from the ops ladder.
9. **Unreachable from outside.** [L2 · Mid] Break the lab three ways, one at a time: bind the Python backend to `127.0.0.1` only, then bind it to `0.0.0.0` with UFW denying the port, then publish a container port and drop it in `DOCKER-USER`. For each, diagnose from a second VM using scenario 14 only. Write down refused or timeout, and the log line or capture that proves the cause.
10. **Your real fix, finished.** [L3 · Senior] Repeat drill 5, but move Apache to 81 and 444 as you did at work. Then add one Traefik route per legacy domain, bind 81/444 so only the Traefik container can reach them, and prove each domain with `curl -v --resolve` from the second VM ([Deployment patterns](35-deployment-patterns.md) shows the routes).

For timed practice on real broken servers, [SadServers](https://sadservers.com/scenarios) has several "port in use / service won't start" scenarios. [Killercoda Linux scenarios](https://killercoda.com/linux) work for quick reps without a VM. The [strace zine](https://wizardzines.com/zines/strace/) makes Step 6 of section 4 (finding config files) second nature.

### Exit test by career stage

Pass a stage when you can do its tasks on the lab VM, alone, within the time, with every claim backed by command output.

| Stage | Timed tasks | Time | You pass when |
|---|---|---|---|
| Fresher [L0] | List every listener and mark each one local-only or public; name the owner of three ports | 10 min | every line of `ss -tulpn` explained correctly |
| Junior [L1] | Drill 1 on three random ports; drill 3; free a port with Rung 1 and roll it back | 5 min per port, 20 min each for the rest | process, unit, config and logs right every time; nothing comes back; rollback tested |
| Mid-level [L2] | Drills 4, 6 and 9 | 15 min each | owner named from rules and conntrack alone; marker request found in every layer; cause of each break proven with a log line or capture |
| Senior [L3] | Drills 5, 7 and 10 | 60 min for 5 or 10, 30 min for 7 | every domain returns 200 with a valid certificate through `--resolve`; 81/444 not reachable from outside; rollback under 5 minutes |
| Lead [L4] | Drill 8 plus drill 2 across three hosts with a daily diff; review someone else's change request | one working day | another engineer can run your change and its rollback without asking you anything |

Record your times. Repeat the drills a month later, because the goal is speed you keep, not speed you had once.

### Where to go next

- The full Apache → Dokploy migration, with real rollback: [21 — Case study](21-case-apache-443-dokploy.md)
- "Site down" across DNS, routing, TLS, proxy and app: [25 — Site down playbook](25-playbook-site-down.md)
- Docker, Traefik and Kubernetes incidents: [26 — Containers & Kubernetes playbook](26-playbook-containers-k8s.md)
- The foundations behind this module: [27 — Learn Linux](27-learn-linux.md) (processes, systemd, /proc), [28 — Learn networking](28-learn-networking.md) (sockets, NAT, firewalls), [29 — Learn web servers & proxies](29-learn-webservers-proxies.md) (vhosts, Traefik routers)
- Your 81/444 fix analysed, and how to finish it with Traefik routing: [35 — Deployment patterns](35-deployment-patterns.md)
- Go deeper on the platforms in sections 6 and 7: [30 — Learn Docker](30-learn-docker.md) (publishing, networks, Swarm) and [31 — Learn Kubernetes](31-learn-kubernetes.md) (Services, kube-proxy, CKA)
- When the port is fine but the box is slow, or the network is: [23 — Slow system](23-playbook-slow-system.md) and [24 — Network speed](24-playbook-network-speed.md)
- Where these skills sit in your career, and what each stage expects: [40 — Career ladder](40-career-ladder.md) and the [34 — Roadmap](34-roadmap.md)
