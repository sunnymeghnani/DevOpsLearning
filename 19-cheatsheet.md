# 19 — Quick Cheat Sheet

## First 5 minutes on a broken Linux box

```bash
uptime                                   # load vs core count (nproc)
dmesg -T | tail -30                      # kernel screaming? OOM? disk errors?
df -h ; df -i                            # disk or inodes full?
free -h                                  # memory 'available'; swap active?
top -b -n1 | head -20                    # who burns CPU? us/sy/wa/st split?
vmstat 1 5                               # r (runq), si/so (swapping), wa (I/O wait)
iostat -xz 1 3                           # disk %util and await
ss -tulpn                                # is everything listening that should be?
ss -s                                    # connection counts sane?
systemctl --failed                       # dead services
journalctl -p err -b --no-pager | tail -30    # errors this boot
last -x | head                           # recent reboots/logins
```

## One-liner index (the command I always forget)

| Need | Command |
|---|---|
| Biggest dirs from / | `du -xh --max-depth=1 / | sort -rh | head` |
| Disk full but no big files | `df -i` (inodes) then `lsof +L1` (deleted-open) |
| Who listens on port | `ss -tlnp sport = :443` |
| Refused vs filtered | `nc -zv host port` |
| Per-hop packet loss | `mtr -rwc 100 host` (Windows: `pathping host`) |
| Which route/iface is used | `ip route get 8.8.8.8` |
| Resolve like the app does | `getent hosts name` (vs `dig name`) |
| Ask a specific DNS server | `dig @10.0.0.2 name +short` |
| Watch service logs live | `journalctl -u svc -f` |
| Previous boot's end | `journalctl -b -1 -e` |
| Was it OOM-killed? | `dmesg -T | grep -i oom` |
| Top CPU / memory procs | `ps aux --sort=-%cpu | head` / `--sort=-%mem` |
| Unkillable process? | `ps -o stat= -p PID` → D = I/O hang; Z = reap parent |
| What files does PID touch | `strace -e trace=openat -p PID` |
| Stale binary running? | `readlink /proc/PID/exe` → "(deleted)" |
| Effective sshd config | `sshd -T | grep -i passwordauth` |
| Why is auth failing (server) | `journalctl -u sshd -f` while client retries |
| Perms along a whole path | `namei -l /full/path/to/file` |
| SELinux blocking? | `ausearch -m avc -ts recent` |
| What package owns a file | `dpkg -S /path` / `rpm -qf /path` |
| What updated recently | `/var/log/apt/history.log` / `dnf history` |
| Clock sane? | `timedatectl` ; `chronyc tracking` |
| Cert expiry from shell | `echo | openssl s_client -connect h:443 -servername h 2>/dev/null | openssl x509 -noout -dates` |
| Where is HTTP slow | `curl -o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer}\n' URL` |
| Test vhost bypassing DNS | `curl --resolve host:443:IP https://host/` |
| Container died why | `docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' c1` |
| Pod crash reason | `kubectl logs pod --previous` ; `kubectl describe pod` |
| Empty service endpoints | `kubectl get endpoints svc` |
| Who am I to AWS | `aws sts get-caller-identity` |
| EC2 boot log w/o SSH | `aws ec2 get-console-output --instance-id i-x --latest` |
| Shell w/o SSH (AWS) | `aws ssm start-session --target i-x` |
| LB target health + reason | `aws elbv2 describe-target-health --target-group-arn ...` |
| Who changed AWS resource | `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=...` |

On Windows or a Mac, the same questions have their own tools: [Linux ↔ Windows cheat table](17-windows.md#linux-windows-cheat-table), [Linux ↔ macOS cheat table](20-macos.md#linux-macos-cheat-table), and port ownership on every platform in [Quick reference across platforms](22-playbook-ports-inventory.md#18-quick-reference-across-platforms). Slowness and network speed on both are in [Why is it slow?](23-playbook-slow-system.md#16-windows-quick-playbook) (sections 16 and 17) and [Network speed](24-playbook-network-speed.md#12-windows-speed-and-latency-tools) (sections 12 and 13).

## Top community problems → first command

The errors that fill forum threads and GitHub issues, with the first read-only command to run. The linked entry has the cause, the fix and the prevention. UPPERCASE words are placeholders.

| You see | First command | Entry |
|---|---|---|
| `Could not get lock /var/lib/dpkg/lock-frontend` | `sudo fuser -v /var/lib/dpkg/lock-frontend` (wait for it; never delete the lock) | [41 2.1](41-problems-linux-systems.md#21-could-not-get-lock-apt-or-dpkg-is-busy) |
| `Start request repeated too quickly` | `journalctl -u UNIT -b --no-pager | grep -v 'Scheduled restart' | head -20` | [41 3.1](41-problems-linux-systems.md#31-restart-loop-start-request-repeated-too-quickly) |
| No space left on device, but `df -h` shows free space | `df -i -x tmpfs -x devtmpfs -x squashfs` (inodes) | [41 1.3](41-problems-linux-systems.md#13-no-space-left-but-df-shows-free-space) |
| A service vanished with `status=9/KILL` | `journalctl -k -b --no-pager | grep -iE 'invoked oom-killer|Killed process'` | [41 6.1](41-problems-linux-systems.md#61-oom-killer-took-the-database) |
| `Temporary failure in name resolution` | `ls -l /etc/resolv.conf; resolvectl status` | [42 2.1](42-problems-network-dns-tls-vpn.md#21-temporary-failure-in-name-resolution) |
| UFW denies a port, yet the container answers from the internet | `docker ps --format '{{.Names}} {{.Ports}}'`, then `nc -vz -w 3 PUBLIC_IP PORT` from outside | [42 3.1](42-problems-network-dns-tls-vpn.md#31-docker-publishes-ports-past-ufw), [44 4.4](44-problems-docker-swarm-registry.md#44-published-ports-bypass-ufw) |
| Let's Encrypt HTTP-01: `Timeout during connect (likely firewall problem)` | from outside: `curl -4 -sv -m 10 http://DOMAIN/.well-known/acme-challenge/probe` | [42 5.1](42-problems-network-dns-tls-vpn.md#51-timeout-during-connect-from-the-ca) |
| `x509: certificate signed by unknown authority` on `docker login` or `pull` | `ls /usr/local/share/ca-certificates/ /etc/docker/certs.d/` (which trust store does the failing tool read?) | [42 6.3](42-problems-network-dns-tls-vpn.md#63-private-ca-certificate-signed-by-unknown-authority) |
| Dokploy app answers `404 page not found` right after a CI or webhook redeploy | `docker service inspect SERVICE --format '{{json .Spec.Labels}}' | jq -c 'keys'` (traefik.* labels gone?) | [45 6.6](45-dokploy-and-self-hosted-paas.md#66-image-app-404-after-a-webhook-redeploy), else [43 5.1](43-traefik-and-reverse-proxies.md#51-traefik-answers-404-page-not-found) |
| `no space left on device` on a Docker pull or build | `docker system df` | [44 2.1](44-problems-docker-swarm-registry.md#21-no-space-left-on-device) |
| GitLab job stuck pending: no runners that match the job's tags | `sudo gitlab-runner verify`, then compare the runner's tags with the job's `tags:` | [47 5.1](47-cicd-gitlab-jenkins-actions-argocd.md#51-job-stuck-pending-no-runner-matches) |
| `ImagePullBackOff` pulling from Harbor (x509 in the events) | `kubectl -n NS describe pod POD | sed -n '/Events:/,$p'` | [46 2.4](46-problems-kubernetes.md#24-images-crictl-ctr-and-harbors-private-ca) |
| Wazuh agent stays `Never connected` | `sudo tail -n 5 /var/ossec/logs/ossec.log`; `nc -vz MANAGER_IP 1514` | [48 5.1](48-wazuh-and-security-tools.md#51-agent-never-connects) |
| Prometheus target DOWN: `connection refused` or `context deadline exceeded` | on the target: `sudo ss -ltnp 'sport = :9100'` | [49 5.1](49-observability-stack-problems.md#51-target-down-refused-or-deadline-exceeded) |
| Terraform: `Error acquiring the state lock` | read `Who`, `Operation` and `Created` under `Lock Info`, then `aws s3 ls s3://BUCKET/PATH.tfstate.tflock` (S3 native lock): is that job still running? | [50 3.3](50-problems-cloud-iac-proxmox.md#33-error-acquiring-the-state-lock) |
| Proxmox `apt update`: `401 Unauthorized` from enterprise.proxmox.com | `apt update 2>&1 | grep -A1 '^Err'`, then `ls /etc/apt/sources.list.d/` | [50 7.1](50-problems-cloud-iac-proxmox.md#71-apt-update-401-from-the-enterprise-repo) |
| `FATAL: sorry, too many clients already` | `psql -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC"` | [51 2.2](51-problems-databases-storage-backup.md#22-too-many-clients-already) |

## Who owns this port?

Port → PID → unit → config → logs. Full drill: [Who owns this port?](22-playbook-ports-inventory.md#4-the-chain-port-to-pid-unit-config-and-logs)

```bash
sudo ss -ltnup 'sport = :443'                  # PID and process name, TCP and UDP
ps -o pid,ppid,user,unit,cmd -p PID            # the systemd unit, straight from procps
systemctl cat UNIT                             # ExecStart, drop-ins, EnvironmentFile
journalctl -u UNIT -n 50 --no-pager            # its logs
docker ps --format '{{.Names}}  {{.Ports}}' | grep ':443->'   # ss shows docker-proxy or nothing?
```

## Free a port (dispatch a service)

Back up, use the least invasive rung, verify. Ladder and rollbacks: [Dispatching a service safely](22-playbook-ports-inventory.md#10-dispatching-a-service-safely). The Apache case: [Phase 5 of the case](21-case-apache-443-dokploy.md#6-phase-5-dispatch-apache-off-80-and-443) and [Apache moved to 81 and 444](35-deployment-patterns.md#1-your-fix-apache-moved-to-81-and-444).

```bash
sudo cp -a /etc/apache2 /root/apache2.bak-$(date +%F)          # 0. back up, record listeners
sudo ss -tulpn | sudo tee /root/listeners-before-$(date +%F).txt >/dev/null
# 1. move it: Listen 81/444 in ports.conf AND every VirtualHost *:80 -> *:81, *:443 -> *:444
sudo apache2ctl configtest && sudo systemctl restart apache2   # Listen changes need a restart
# 2. or stop it for good: sudo systemctl disable --now apache2 && sudo systemctl mask apache2
# 3. a container: docker update --restart=no CONTAINER && docker stop -t 30 CONTAINER
sudo ss -ltnp '( sport = :80 or sport = :443 )'                # 4. verify: nothing listens
```

Moving a port is half a fix: route the names through the new proxy and close the old ports from outside ([Finish the job](35-deployment-patterns.md#finish-the-job-overview)).

## Why is it slow? (60-second checklist)

Collect first, fix nothing yet. Then open the matching section of [Why is it slow?](23-playbook-slow-system.md#2-the-60-second-checklist)

```bash
uptime                   # load vs nproc; rising or falling?
dmesg -T | tail -20      # OOM kills, disk or NIC errors
vmstat -w 1 5            # r > cores = CPU queue; si/so = swapping; wa = I/O wait
mpstat -P ALL 1 3        # one core at 100% = a single-threaded hot spot
pidstat 1 3              # which process burns CPU
iostat -xz 1 3           # r_await/w_await and %util per disk
free -m                  # read 'available', not 'free'
sar -n DEV 1 3           # NIC throughput close to link speed?
sar -n TCP,ETCP 1 3      # retransmits point at the network
top -b -n 1 | head -20   # confirm the suspect
```

## Network speed quick checks

Path, then phases, then throughput, then the link. Steps with sample output: [Network speed](24-playbook-network-speed.md#4-core-method-path-setup-and-latency-steps-03)

```bash
ip route get 203.0.113.10                      # which interface and gateway
curl -o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://app.example.com/
mtr -rwc 100 203.0.113.10                      # loss and latency per hop
iperf3 -c 10.0.20.15 -t 10; iperf3 -c 10.0.20.15 -t 10 -R    # both directions (server: iperf3 -s)
sudo ethtool eno1 | grep -E 'Speed|Duplex'     # negotiated 1000Mb/s Full?
ip -s link show eno1                           # errors and drops
ping -c 3 -M do -s 1472 203.0.113.10           # fails = path MTU below 1500
```

## Exit codes / signals quick reference

- `137` = 128+9 (SIGKILL) → OOM or forced kill
- `139` = 128+11 (SIGSEGV) → crash
- `143` = 128+15 (SIGTERM) → normal stop
- `126` not executable, `127` command not found
- ssh/scripts: `$?` holds the last exit code

## Safety habits

1. Read logs **before** restarting — restarts destroy evidence.
2. `nginx -t`, `sshd -t`, `visudo -c`, `findmnt --verify`, `logrotate -d` —
   **syntax-check before applying**, especially for anything that can lock you out.
3. Changing sshd/firewall remotely? Keep a second session open until verified
   (`netplan try` auto-rollbacks; consider `at now + 5 min` job restoring config).
4. `rsync -n`, `logrotate -d`, `fsck -n` — dry-run flags exist, use them.
5. Never `rm` an active log file — `truncate -s 0` it.
6. Note times: `date -u` before/after actions — it makes log correlation trivial.
7. On AWS: prefer stop/start over reboot for host-level issues; know it changes
   public IPs and wipes instance-store.
