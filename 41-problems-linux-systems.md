# 41 — Real-World Problems: Linux, systemd, Storage & Performance

This module is a problem library for the Linux host itself: Ubuntu 22.04/24.04 and RHEL 9 servers, systemd and journald, apt and dpkg, cron and timers, sudo and permissions, SSH, disks, LVM, RAID and NFS, memory and OOM, kernel limits and time sync. It collects 40 problems that people hit again and again on production servers. They come from GitHub issues sorted by reactions, the Ubuntu and Fedora forums, the DigitalOcean community, ArchWiki, Red Hat and cloud-vendor docs, Brendan Gregg's work and public postmortems; Stack Overflow, Server Fault and Reddit are reachable through search links. [Learn Linux](27-learn-linux.md) teaches the fundamentals, and this module assumes them. Every command is documented for your own lab VMs or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Host problems are the floor everything else stands on. When Dokploy, Traefik, GitLab runners or Kubernetes nodes misbehave, a surprising share of the root causes sit one layer down: a full disk, a unit stuck in a restart loop, an apt lock held by a timer, a file-descriptor limit nobody raised, a clock that drifted, an fstab line that stops the next boot. The entries below are the ones that keep coming back in forum threads and postmortems, ordered from first-week problems to bare-metal hardware.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | entries 1.1, 2.1, 3.1 and 5.1 | you can say which filesystem is full, which unit failed and why a key login is refused, using only `df`, `systemctl status` and the auth log |
| Junior | L1 Operator | sections 1 to 5 (every L1 entry) | you fix a full disk, a broken apt run, a service restart loop, a cron job that never runs and a sudo lockout without help |
| Mid-level | L2 Troubleshooter | sections 6 to 10 | you explain high load with idle CPU, an OOM kill, "too many open files", an emergency-mode boot and a stale NFS handle from evidence alone |
| Senior | L3 Platform | entries 2.6, 9.3, 10.2, 11.1 and 11.2 | patching, disk replacement and boot recovery are runbooks your team follows, with alerts that fire before users notice |
| Senior/Lead | L4 SRE | entry 8.2 and the Self-check | you design fleet-wide policies (patch windows, time sources, limits, out-of-band access) and can show the drill results |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** build three lab VMs on Proxmox, VirtualBox or a cloud account: web1 (Ubuntu 24.04, 2 vCPU, 2 GB RAM, a second 10 GB disk for LVM and RAID drills), db1 (Ubuntu 24.04 with PostgreSQL or any service you care about) and rh1 (Rocky Linux or RHEL 9 for the SELinux and dnf entries). Add a fourth small VM as an NFS server when you reach section 10. Snapshot every VM, break one thing at a time exactly as an entry describes, fix it using only the entry, and write a five-line note: symptom, evidence, cause, fix, prevention. Keep a console (hypervisor or cloud serial console) open for every drill that touches SSH, fstab, sudo or the kernel, because those are the ones that lock you out.

**Safety rules for host incidents:**

- Read before you write: `df`, `journalctl`, `systemctl status` and `dmesg` change nothing, so run them first and keep the output for the postmortem.
- Never delete lock files, never `rm` files under /var/lib/dpkg, /var/lib/docker or a database data directory, and never `chmod -R 777` anything to make an error go away.
- Before you touch sshd, the firewall, sudoers or fstab, open a second session and keep it open until you have tested a fresh login or a reboot.
- On a server with users, a reboot is a change: announce it, check what will not come back (fstab, NFS, services not enabled), and know how you will reach the console if it fails.

**Placeholders and examples:** UPPERCASE words are placeholders (UNIT, PID, PKG, DEVICE, VG, LV, MOUNTPOINT, USER). The examples use a 10.0.1.0/24 lab with web1 at 10.0.1.10, db1 at 10.0.1.20, the NFS server nfs1 at 10.0.1.40 and the hypervisor or BMC network at 10.0.9.0/24; the public address is 203.0.113.10, the admin user is ops and the application user is deploy.

**First minute: symptom to entry.**

| You see | First check | Go to |
|---|---|---|
| No space left on device | `df -hT` and `df -i` | 1.1, 1.2, 1.3 |
| Read-only file system | `dmesg -T` for ext4 or I/O errors | 1.6 |
| Could not get lock /var/lib/dpkg/lock-frontend | which process holds it | 2.1 |
| Sub-process /usr/bin/dpkg returned an error code (1) | the first error above it | 2.2, 1.5 |
| Start request repeated too quickly | `journalctl -u UNIT -b` | 3.1, 3.2 |
| a cron job that silently never ran | the cron log and the job's PATH | 3.4 |
| Permission denied with correct-looking modes | `namei -l PATH`, then the audit log | 4.2, 4.4 |
| Permission denied (publickey) | the server's auth log | 5.1 |
| a process that vanished, "Killed" | `journalctl -k` for the OOM killer | 6.1 |
| load average 30 with idle CPUs | processes in D state | 7.1 |
| Too many open files | `/proc/PID/limits` | 7.2 |
| a clock several minutes off | `chronyc tracking` | 8.1 |
| "You are in emergency mode" | `journalctl -xb` for the failed mount | 9.2 |
| Stale file handle or a hung `ls` on a mount | `findmnt -t nfs,nfs4` | 10.1, 10.2 |
| [U_] in /proc/mdstat | `mdadm --detail` | 11.1 |

> 📚 **Study path:** KodeKloud *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD, Storage in Linux, Security and File Permissions ([course](https://kodekloud.com/courses/the-linux-basics-course), [SYSTEMD Tools notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)) → *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment, then Storage ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs), [Locate and Analyze System Log Files](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page), [Monitor Storage Performance](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) → *Linux Challenges* as the L1 exit check ([course](https://kodekloud.com/courses/linux-challenges)) → *Fundamentals of SRE* — Performance Monitoring Deep Dive ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page)) → handbook [Learn Linux](27-learn-linux.md) (sections 6, 7, 8 and 17 first) → docs: [systemd man pages](https://www.freedesktop.org/software/systemd/man/latest/), [Ubuntu Server docs](https://ubuntu.com/server/docs), [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html) → lab: the VMs above, the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) and the Self-check. KodeKloud has no dedicated Linux performance, RAID or NFS-operations course in the verified map, so the handbook, ArchWiki and the vendor docs lead there.

---

The problem library starts here. Sections 1 to 11 run from first-day disk and package problems to bare-metal hardware; each entry stands on its own.

## 1. Disk full and filesystems

A full or broken filesystem is the most common host incident of all, and it rarely announces itself as "disk full": you see failed deploys, a database refusing writes, a shell that can't create a here-document, or a service that won't start. The trick is to know which counter ran out (bytes, inodes or blocks held by deleted files) and which filesystem it is on.

### 1.1 Disk full: find what is eating the space

> **Seen as:** `No space left on device` in app logs, `write error: No space left on device` from `cp` or `tar`, `cannot create temp file for here-document`, Docker builds failing with `no space left on device`, Postgres `could not extend file` · **Where:** any server; most often Docker hosts, CI runners and Dokploy managers · **Level:** [L0 · Fresher] · **How common:** the number one host incident; DigitalOcean community questions on it have very high view counts and postmortems (Tarsnap 2016) start the same way

**Why it happens:** something writes faster than anything deletes. The usual suspects on a DevOps host: container json logs without rotation, Docker images and build cache, application logs written outside logrotate's reach, the systemd journal, old kernels and snap revisions, core dumps, and backups or database dumps that someone pointed at the local disk "for now". It feels sudden because nobody alerts at 80%.

**Diagnose:**

```bash
# Which filesystem is full? (-x hides pseudo filesystems)
df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay
# Biggest directories on THAT filesystem only (-x: don't cross into other mounts)
sudo du -xh --max-depth=1 / 2>/dev/null | sort -h | tail -8
sudo du -xh --max-depth=1 /var 2>/dev/null | sort -h | tail -8
# Docker's own view: images, containers, volumes, build cache
sudo docker system df
# Container logs over 500 MB
sudo find /var/lib/docker/containers -name '*-json.log' -size +500M -exec ls -lh {} \;
```

```text
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   48G   48G     0 100% /
/dev/sda2                         ext4  2.0G  196M  1.6G  11% /boot
3.1G	/usr
41G	/var
45G	/
36G	/var/lib
3.9G	/var/log
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          47        9         9.4GB     6.1GB (64%)
Containers      12        9         1.2GB     0B (0%)
Local Volumes   18        11        2.3GB     310MB (13%)
Build Cache     212       0         4.9GB     4.9GB
-rw-r----- 1 root root 18G Oct  3 22:41 /var/lib/docker/containers/4f2a9c.../4f2a9c...-json.log
```

**What the output tells you:** the root LV is full and almost all of it is /var/lib. Docker accounts for most: 18 GB is one container's json log, which `docker system df` does not count at all (its "Containers" size is only the writable layers, moby#32205), so the `find` is the step that reveals it; 6.1 GB are unused images and 4.9 GB build cache. The journal and /var/log are a smaller second problem.

**Fix:**

```bash
# 1. Emergency space: empty the giant log in place (the container keeps its open file)
sudo truncate -s 0 /var/lib/docker/containers/4f2a9c*/4f2a9c*-json.log
# 2. Reclaimable Docker data that no running container needs
sudo docker builder prune --filter until=168h -f
sudo docker image prune -a --filter until=168h -f
# 3. Rotate container logs from now on (applies to containers created after the restart).
#    If /etc/docker/daemon.json already exists (registry mirrors, Harbor CA settings), merge these keys into it instead.
sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{ "log-driver": "json-file", "log-opts": { "max-size": "50m", "max-file": "3" } }
EOF
sudo systemctl restart docker      # plan this: it restarts containers unless live-restore is set
# 4. Smaller wins
sudo journalctl --vacuum-size=500M
sudo apt-get clean
```

**Why this fix works:** truncating keeps the inode the daemon writes to, so space comes back immediately without restarting the container (deleting the file would not free anything, see 1.2). The prune filters remove only what is older than a week and unused. The log options cap every new container at 150 MB of logs. What NOT to do: `docker system prune -a --volumes` on a host with databases (it deletes unused named volumes, which can be your data), `rm -rf /var/lib/docker/overlay2/*` (corrupts Docker's metadata), or deleting files under /var/lib/postgresql to "make room".

**Prevent it:** alert at 80% and 90% on every filesystem (node_exporter plus a Prometheus rule, or Netdata), put /var/lib/docker on its own LV or disk so a runaway container can't fill /, set daemon.json log rotation in your server baseline, and schedule a weekly builder prune on CI runners.

**Next step:** [Storage & disk: Disk space usage](01-storage-disk.md) · [Learn Linux: Storage and filesystems](27-learn-linux.md) · [Learn Docker](30-learn-docker.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux · [Docker docs](https://docs.docker.com/)

**Community threads:** [DigitalOcean: No space left on device - can't start apache, mysql or install anything](https://www.digitalocean.com/community/questions/no-space-left-on-device-i-can-t-start-apache-mysql-or-install-anything) · [Tarsnap 2016 outage: a runaway log filled the filesystem](https://mail.tarsnap.com/tarsnap-announce/msg00035.html) · Search: [Server Fault](https://serverfault.com/search?q=%22no+space+left+on+device%22+docker+json+log) · [Stack Overflow](https://stackoverflow.com/search?q=docker+%22no+space+left+on+device%22+prune) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=disk+full+docker+logs&restrict_sr=1)

### 1.2 df says full, du finds nothing

> **Seen as:** `df -h` shows 100% (or 30 GB used) while `du -sh /` adds up to far less; deleting a huge log "did nothing" · **Where:** hosts running nginx, Apache, Java apps or anything with long-lived log files · **Level:** [L1 · Junior] · **How common:** a classic interview question and one of the most written-about df/du puzzles

**Why it happens:** `rm` removes the directory entry, not the data. If a process still has the file open, the blocks stay allocated until that process closes it, and `du` (which walks directories) can't see a file that has no name any more. Typical story: someone deletes a 20 GB access.log by hand, nginx keeps writing into the deleted inode, and the disk stays full. A second, rarer cause: files written into a directory before something was mounted over it are hidden under the mount point but still use space on the parent filesystem.

**Diagnose:**

```bash
# Open files with a link count below 1 = deleted but still held open
sudo lsof -nP +L1 | awk 'NR==1 || $7 > 100000000'
# The same through /proc for one process
sudo ls -l /proc/PID/fd | grep deleted
# Files hidden under a mount point: look at / without the mounts on top
sudo mkdir -p /mnt/rootonly && sudo mount --bind / /mnt/rootonly
sudo du -xsh /mnt/rootonly/var/lib/docker /mnt/rootonly/srv 2>/dev/null
```

```text
COMMAND  PID  USER  FD  TYPE DEVICE    SIZE/OFF NLINK    NODE NAME
nginx   1184 www-data 5w REG  253,0 21474836480     0 1835121 /var/log/nginx/access.log (deleted)
java    2290 deploy  12w REG  253,0  6442450944     0 1835412 /opt/app/logs/app.log.1 (deleted)
```

**What the output tells you:** 20 GB belong to nginx's deleted access.log and 6 GB to a rotated Java log the app never let go of. NLINK 0 plus "(deleted)" is the signature. If lsof shows nothing but the bind mount reveals data under /srv, you have the hidden-under-mount case.

**Fix:**

```bash
# Best: make the process reopen its logs (nginx and Apache reopen on reload / USR1)
sudo systemctl reload nginx
# If the process can't be reloaded now: empty the deleted file through its descriptor
sudo truncate -s 0 /proc/2290/fd/12
# Hidden-under-mount case: move the data, then remove the bind mount
sudo umount /mnt/rootonly
```

**Why this fix works:** a reload makes nginx close and reopen its log files, which drops the last reference and frees the blocks. Truncating through /proc/PID/fd empties the inode the process holds, without killing it. What NOT to do: `rm` more files (they will also stay allocated), or reboot a production box just to free space when a reload does it.

**Prevent it:** rotate with logrotate and a postrotate reload (or `copytruncate` for apps that can't reopen logs), never delete live logs by hand (use `truncate -s 0`), and add an alert on the difference between df and du-style usage via node_exporter's filesystem metrics.

**Next step:** [Storage & disk: Decision tree "No space left on device"](01-storage-disk.md) · [Logs & journal: Log rotation issues](06-logs-journal.md) · [Processes](05-processes.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) · [Brendan Gregg: Linux performance](https://www.brendangregg.com/linuxperf.html)

**Community threads:** [DEV: Your disk is full but du says it's empty](https://dev.to/arthurpro/your-disk-is-full-but-du-says-its-empty-1dhj) · [Find and recover space used by deleted files (jensd)](https://jensd.be/326/linux/find-and-recover-space-used-by-deleted-files-shown-by-df-but-not-by-du) · Search: [Server Fault](https://serverfault.com/search?q=df+du+difference+deleted+files+lsof) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=df+du+deleted+files+lsof&restrict_sr=1)

### 1.3 No space left, but df shows free space

> **Seen as:** `No space left on device` (PHP: `fopen(/var/lib/php/sessions/...): failed to open stream: No space left on device`) while `df -h` shows 40% used · **Where:** web servers with PHP sessions, mail queues, caches, CI runners with millions of small files, small root disks · **Level:** [L1 · Junior] · **How common:** several highly viewed DigitalOcean community questions; a classic on shared hosting and small VPS disks

**Why it happens:** ext4 creates a fixed number of inodes at mkfs time, one per file or directory. Millions of tiny files (PHP sessions never garbage-collected, a mail queue, thumbnail caches, node_modules trees on a CI runner) use up all inodes long before the bytes run out. XFS allocates inodes dynamically and hits this far more rarely.

**Diagnose:**

```bash
df -i -x tmpfs -x devtmpfs -x squashfs
# Which directories hold the most inodes (GNU du 8.22+)
sudo du --inodes -x / 2>/dev/null | sort -n | tail -6
# Directories whose own size is huge = millions of entries
sudo find / -xdev -type d -size +10M 2>/dev/null
```

```text
Filesystem                         Inodes   IUsed IFree IUse% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv 3145728 3145728     0  100% /
2861904	/var/lib/php/sessions
2864211	/var/lib/php
2871540	/var/lib
3145728	/
/var/lib/php/sessions
```

**What the output tells you:** zero free inodes on / and 2.8 million of them under /var/lib/php, almost all session files. The directory itself has grown past 10 MB, which only happens with millions of entries.

**Fix:**

```bash
# Delete old sessions without building a huge argument list
sudo find /var/lib/php/sessions -xdev -type f -name 'sess_*' -mmin +1440 -delete
# Confirm the session GC timer exists and runs (Ubuntu ships phpsessionclean)
systemctl list-timers 'phpsessionclean*'
sudo systemctl enable --now phpsessionclean.timer
```

**Why this fix works:** `find -delete` removes files one by one without hitting "Argument list too long", and the age filter keeps active sessions. The packaged phpsessionclean timer is the cleanup that was missing (often because PHP runs in a container or a custom path the timer doesn't know). What NOT to do: `rm -rf /var/lib/php/sessions/*` (the glob fails with millions of files and kills active sessions), or reformat to "add inodes" before you know what is creating the files.

**Prevent it:** monitor inode usage beside bytes (node_exporter exposes node_filesystem_files_free), store sessions in Redis or the database, add tmpfiles.d rules (`d /var/cache/app 0755 deploy deploy 7d`) for caches, and for filesystems that will hold millions of small files choose XFS or `mkfs.ext4 -i 8192`.

**Next step:** [Storage & disk: Disk space usage](01-storage-disk.md) · [Learn Linux: Storage and filesystems](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux · [Linux kernel docs](https://docs.kernel.org/)

**Community threads:** [DigitalOcean: No space left on device (28)](https://www.digitalocean.com/community/questions/no-space-left-on-device-28) · [DigitalOcean: PHP sessions No space left on device](https://www.digitalocean.com/community/questions/php-error-message-fopen-var-lib-php-sessions-failed-to-open-stream-no-space-left-on-device) · Search: [Server Fault](https://serverfault.com/search?q=%22no+space+left+on+device%22+inodes+df+-i) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=out+of+inodes&restrict_sr=1)

### 1.4 The journal eats /var

> **Seen as:** `journalctl --disk-usage` reports `Archived and active journals take up 4.0G`, /var/log/journal is the biggest directory in /var, or journald writes hammer the disk · **Where:** busy servers, chatty containers logging through journald, units stuck in restart loops · **Level:** [L1 · Junior] · **How common:** frequent Fedora and Ubuntu forum topic; the journald filter request is one of the most-reacted systemd issues (#6432) and excessive journald I/O is a current open issue (#40262)

**Why it happens:** journald keeps persistent logs in /var/log/journal and, by default, may use up to 10% of the filesystem capped at 4 GB (SystemMaxUse) while keeping 15% free (SystemKeepFree). On a 40 GB root that is a big share, and on a small disk the cap is reached quickly. A unit in a restart loop (3.1) or a debug-level app logging to stdout multiplies the volume, and a full journal means heavy rotation I/O.

**Diagnose:**

```bash
journalctl --disk-usage
# Which units wrote the most entries in the last hour
sudo journalctl --since "-1h" -o export | grep -a '^_SYSTEMD_UNIT=' | sort | uniq -c | sort -n | tail -5
# Current effective limits (the log line journald prints at start)
sudo journalctl -b -u systemd-journald | grep -iE 'system journal|runtime journal'
# Rate limiting kicking in = a very noisy unit
sudo journalctl -b -u systemd-journald | grep -i suppressed | tail -3
```

```text
Archived and active journals take up 3.9G in the file system.
   1823 _SYSTEMD_UNIT=cron.service
   4410 _SYSTEMD_UNIT=docker.service
 211904 _SYSTEMD_UNIT=worker.service
System Journal (/var/log/journal/5f1c...) is 3.9G, max 4.0G, 0B free.
systemd-journald[412]: Suppressed 48211 messages from worker.service
```

**What the output tells you:** the journal is at its 4 GB cap, and worker.service produces 200 000 lines an hour, enough that journald's rate limiter is dropping messages. The cap works as designed; the noisy unit is the problem.

**Fix:**

```bash
# Set an explicit budget with a drop-in (survives package upgrades)
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/50-size.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=1G
SystemKeepFree=5G
MaxRetentionSec=1month
EOF
sudo systemctl restart systemd-journald
# Shrink now
sudo journalctl --vacuum-size=1G
# Quieten the noisy unit at the source (its own log level), or cap it per unit:
sudo systemctl edit worker.service    # add: [Service] LogRateLimitIntervalSec=30s / LogRateLimitBurst=1000
```

**Why this fix works:** journald.conf.d drop-ins override the packaged defaults and journald applies them on restart; vacuum deletes the oldest archived files. Fixing the app's log level removes the cause; the per-unit rate limit protects the rest of the journal. What NOT to do: `rm -rf /var/log/journal/*` while journald runs (you lose the current boot's logs and journald complains about missing files), or set Storage=none on a server (no logs after the next incident).

**Prevent it:** budget journal space in your baseline, ship logs off the host (Loki/Alloy, Wazuh, rsyslog) so local retention can be short, and alert on units that restart more than N times an hour.

**Next step:** [Logs & journal: journalctl](06-logs-journal.md) · [Learn Linux: Logs and log rotation](27-learn-linux.md) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Locate and Analyze System Log Files · [journald.conf](https://www.freedesktop.org/software/systemd/man/latest/journald.conf.html)

**Community threads:** [Fedora Discussion: /var/log/journal larger than expected](https://discussion.fedoraproject.org/t/var-log-journal-larger-than-exepected/61357) · [systemd#6432 Filter mechanism for logs in journald](https://github.com/systemd/systemd/issues/6432) · [systemd#40262 Excessive IO caused by systemd-journald](https://github.com/systemd/systemd/issues/40262) · Search: [Server Fault](https://serverfault.com/search?q=journald+SystemMaxUse+disk+usage) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=journald+disk+usage&restrict_sr=1)

### 1.5 /boot full breaks the kernel upgrade

> **Seen as:** `gzip: stdout: No space left on device`, `update-initramfs: failed for /boot/initrd.img-6.8.0-85-generic with 1.`, `dpkg: error processing package linux-image-...`, and every later apt run ends in `E: Sub-process /usr/bin/dpkg returned an error code (1)` · **Where:** older Ubuntu installs with a 512 MB or 1 GB /boot, hosts where autoremove never runs, servers with held kernel packages · **Level:** [L1 · Junior] · **How common:** a long-running classic on every Ubuntu forum; it also causes the "kernel panic after update" in entry 9.3

**Why it happens:** each kernel adds a vmlinuz plus an initramfs of 60 to 120 MB. Unattended-upgrades installs new kernels, but old ones are removed only by autoremove, which some setups never run (or which is blocked because a kernel package is marked manually installed). When /boot fills, the new initramfs is written half-way, dpkg marks the package as failed, and apt refuses to do anything else until it is fixed.

**Diagnose:**

```bash
df -h /boot
uname -r                                  # the running kernel: never remove this one
dpkg -l 'linux-image-*' | awk '/^ii|^iF|^iU/ {print $1, $2}'
ls -lh /boot | sort -k5 -h | tail -6
```

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       474M  474M     0 100% /boot
6.8.0-79-generic
ii linux-image-6.8.0-71-generic
ii linux-image-6.8.0-76-generic
ii linux-image-6.8.0-79-generic
iF linux-image-6.8.0-85-generic
-rw-r--r-- 1 root root 112M Sep 12 06:14 initrd.img-6.8.0-76-generic
-rw-r--r-- 1 root root 113M Sep 30 06:20 initrd.img-6.8.0-79-generic
```

**What the output tells you:** /boot is full, four kernels are installed, the new one (85) is half-configured (`iF`), and you are running 79. Kernels 71 and 76 are safe to remove.

**Fix:**

```bash
# Free space by purging kernels that are neither running nor newest
sudo apt-get purge linux-image-6.8.0-71-generic linux-modules-6.8.0-71-generic linux-headers-6.8.0-71-generic
# If apt refuses because of the broken state, let dpkg remove one kernel directly
sudo dpkg --purge linux-image-6.8.0-71-generic linux-modules-6.8.0-71-generic
# Finish the interrupted upgrade, then clean up the rest
sudo dpkg --configure -a
sudo apt-get -f install
sudo apt-get autoremove --purge
# Smaller initramfs on VMs: include only modules this host needs
echo 'MODULES=dep' | sudo tee /etc/initramfs-tools/conf.d/modules-dep
sudo update-initramfs -u -k all
```

**Why this fix works:** removing two unused kernels gives initramfs room to finish; `dpkg --configure -a` completes the half-configured package and regenerates the initramfs; autoremove clears the rest. `MODULES=dep` shrinks each initramfs considerably on VMs (keep the default on bare metal where you may move disks between controllers). What NOT to do: delete files in /boot by hand (dpkg still thinks those kernels exist, and you can delete the running kernel's initramfs), or reboot before `dpkg --configure -a` has succeeded (see 9.3).

**Prevent it:** set `Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";` (default on current Ubuntu), alert on /boot above 70%, and check `apt-mark showmanual | grep linux-image` for kernels pinned by hand.

**Next step:** [Packages](11-packages.md) · [Kernel & system: Boot & GRUB](13-kernel-system.md) · [Learn Linux: Package management](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [DEV: free up space in /boot on Ubuntu by removing old kernels](https://dev.to/mitchellclong/how-to-free-up-more-space-in-boot-on-ubuntu-remove-old-kernels-1ecb?comments_sort=latest) · Search: [Server Fault](https://serverfault.com/search?q=%2Fboot+full+update-initramfs+%22no+space+left%22) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=boot+partition+full+update-initramfs&restrict_sr=1)

### 1.6 Filesystem suddenly read-only

> **Seen as:** `Read-only file system` on every write, `EXT4-fs error (device dm-0): ext4_lookup:1855: inode #1835121: comm nginx: deleted inode referenced` followed by `Remounting filesystem read-only`, services failing one by one · **Where:** VMs on a struggling SAN or NFS datastore, hypervisor storage hiccups, failing physical disks, cloud volumes with I/O errors · **Level:** [L2 · Mid] · **How common:** common across Proxmox, VMware and bare-metal forums; every vendor has a KB article on it

**Why it happens:** ext4 root filesystems are mounted with `errors=remount-ro`. When the kernel sees metadata corruption or an I/O error from the block device, it switches the filesystem to read-only to stop further damage. The trigger is usually below the filesystem: a disk with bad sectors, a SAN path that disappeared for a few seconds, a full thin-provisioned datastore on the hypervisor, or a snapshot chain gone wrong.

**Diagnose:**

```bash
findmnt -no OPTIONS /                     # ro in the options = it happened
sudo dmesg -T | grep -iE 'ext4-fs|i/o error|blk_update_request|failed result|remount' | tail -8   # Ubuntu restricts dmesg to root
sudo smartctl -H /dev/sda                 # bare metal only; see 11.2
sudo tune2fs -l /dev/mapper/ubuntu--vg-ubuntu--lv | grep -iE 'state|errors|error count'
```

```text
ro,relatime,errors=remount-ro
[Sat Oct  4 02:11:07 2026] sd 2:0:0:0: [sda] tag#18 FAILED Result: hostbyte=DID_OK driverbyte=DRIVER_OK cmd_age=31s
[Sat Oct  4 02:11:07 2026] I/O error, dev sda, sector 41208832 op 0x1:(WRITE) flags 0x800 phys_seg 4 prio class 2
[Sat Oct  4 02:11:07 2026] EXT4-fs warning (device dm-0): ext4_end_bio:343: I/O error 10 writing to inode 1835121
[Sat Oct  4 02:11:08 2026] EXT4-fs error (device dm-0): ext4_journal_check_start:84: comm kworker/u8:2: Detected aborted journal
[Sat Oct  4 02:11:08 2026] EXT4-fs (dm-0): Remounting filesystem read-only
Filesystem state:         clean with errors
Errors behavior:          Continue
FS Error count:           3
```

**What the output tells you:** the block device returned write errors first, then ext4 aborted its journal and went read-only. This is a storage problem (disk, controller, SAN path or datastore), not "ext4 broke by itself". Without I/O errors and with only `EXT4-fs error` lines, suspect corruption from an earlier unclean event.

**Fix:**

```bash
# 1. Save evidence while you can (to tmpfs or another host)
sudo dmesg -T > /dev/shm/dmesg-$(date +%F).txt
# 2. Fix the storage layer first: datastore space, SAN path, failing disk (11.1, 11.2)
# 3. Repair offline: reboot into rescue/single-user mode (or attach the disk to another VM)
sudo fsck.ext4 -f /dev/mapper/ubuntu--vg-ubuntu--lv
# 4. Only for a non-root data filesystem, once the cause is fixed:
sudo umount /data && sudo fsck.ext4 -f /dev/vg_data/lv_data && sudo mount /data
```

**Why this fix works:** fsck can only repair an unmounted filesystem; doing it after the storage is healthy prevents new errors during the repair. Evidence first, because a reboot clears dmesg. What NOT to do: `mount -o remount,rw /` and carry on (you write onto a corrupted filesystem and make it worse), or run fsck on a mounted read-write filesystem.

**Prevent it:** monitor kernel I/O errors (Wazuh or a Loki alert on "I/O error"), datastore free space on the hypervisor, SMART on bare metal, and test that backups restore; a filesystem that went read-only once will do it again if the storage cause is not fixed.

**Next step:** [Storage & disk: Filesystem integrity](01-storage-disk.md) · [Learn Linux: The boot process and recovery](27-learn-linux.md) · [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage · [Linux kernel docs](https://docs.kernel.org/)

**Community threads:** [Proxmox forum: EXT4 remounting filesystem read only and fsck repair](https://forum.proxmox.com/threads/no-network-connection-after-ext4-fs-dm-1-remounting-filesystem-read-only-fsck-repair.174823/) · [Broadcom KB: VM shows EXT4-fs remounting filesystem read-only](https://knowledge.broadcom.com/external/article/419387/usage-meter-vm-shows-ext4fs-remounting-f.html) · Search: [Server Fault](https://serverfault.com/search?q=%22remounting+filesystem+read-only%22+ext4) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=filesystem+remounted+read-only&restrict_sr=1)

## 2. Packages and upgrades

apt and dpkg are reliable, but they share one lock, one status database and many maintainer scripts that start and stop services. Most "apt is broken" threads come down to four things: something else holds the lock, a script failed half-way, the repository or its key changed, or a background upgrade did something nobody planned for.

### 2.1 Could not get lock: apt or dpkg is busy

> **Seen as:** `E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 1873 (unattended-upgr)` and `E: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?` · **Where:** the first minutes after booting a new VM, cloud-init and Packer builds, Ansible and CI provisioning, two admins on one host · **Level:** [L1 · Junior] · **How common:** one of the most searched Ubuntu errors; Launchpad bugs, DEV write-ups and countless CI failures

**Why it happens:** Ubuntu runs apt-daily.timer (refresh package lists) and apt-daily-upgrade.timer (unattended-upgrades) with a randomised delay after boot, and cloud-init may install packages at first boot too. dpkg allows exactly one writer, enforced with real file locks on /var/lib/dpkg/lock-frontend and /var/lib/dpkg/lock. Your script starts while one of them runs and fails at once. The lock file existing is normal; only a process holding it matters.

**Diagnose:**

```bash
# Who holds the lock, and for how long?
sudo fuser -v /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock
ps -o pid,etime,cmd -p "$(pgrep -d, -f 'apt|dpkg|unattended')"
# Background jobs and their schedule
systemctl list-timers 'apt-daily*' --no-pager
cloud-init status
sudo tail -3 /var/log/unattended-upgrades/unattended-upgrades.log
```

```text
                     USER        PID ACCESS COMMAND
/var/lib/dpkg/lock-frontend:
                     root       1873 F.... unattended-upgr
    PID     ELAPSED CMD
   1873       03:12 /usr/bin/python3 /usr/bin/unattended-upgrade
NEXT                        LEFT    LAST                        PASSED UNIT                         ACTIVATES
Sat 2026-10-04 18:02:11 UTC 9h left Sat 2026-10-04 08:41:37 UTC 3min ago apt-daily-upgrade.timer apt-daily-upgrade.service
status: running
2026-10-04 08:43:02,118 INFO Packages that will be upgraded: libssl3t64 openssl
```

**What the output tells you:** unattended-upgrades started three minutes ago from apt-daily-upgrade.timer, and cloud-init is still running too. Nothing is stuck; your command simply arrived during the first-boot upgrade.

**Fix:**

```bash
# Interactive: wait. In scripts: let apt wait for the lock (apt 1.9.11+)
sudo apt-get -o DPkg::Lock::Timeout=600 install -y nginx
# Provisioning: wait for cloud-init and the boot-time apt jobs to finish first
cloud-init status --wait
sudo systemd-run --property="After=apt-daily.service apt-daily-upgrade.service" --wait /bin/true
```

In Ansible, the apt module's `lock_timeout` option does the same. In image builds (Packer), stop and disable the two apt timers at the start of the build and re-enable them in the last step, so the image boots with updates on.

**Why this fix works:** DPkg::Lock::Timeout makes apt retry the lock instead of failing, and waiting for cloud-init and the apt services removes the race at its source. What NOT to do: `rm /var/lib/dpkg/lock*` (the other process still runs, and two dpkg writers corrupt /var/lib/dpkg/status), or `kill -9` the unattended-upgrade process in the middle of an install (that leaves dpkg interrupted, entry 2.2).

**Prevent it:** put the lock timeout in every automation path (a file such as /etc/apt/apt.conf.d/90lock-timeout with `DPkg::Lock::Timeout "600";`), wait for `cloud-init status --wait` at the start of user-data scripts, and move unattended-upgrades to a fixed window instead of "shortly after boot".

**Next step:** [Packages: Debian / Ubuntu](11-packages.md) · [Learn Linux: Package management](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs: Automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/)

**Community threads:** [DEV: Resolving dpkg lock contention in Ubuntu deployments](https://dev.to/yulin/resolving-dpkg-lock-contention-in-ubuntu-deployments-5fkk) · [Launchpad 1260041: unattended-upgrades crashes with a dpkg error](https://bugs.launchpad.net/ubuntu/+source/unattended-upgrades/+bug/1260041) · Search: [Server Fault](https://serverfault.com/search?q=%22could+not+get+lock%22+lock-frontend+unattended-upgr) · [Stack Overflow](https://stackoverflow.com/search?q=%22Could+not+get+lock+%2Fvar%2Flib%2Fdpkg%2Flock-frontend%22+cloud-init) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=could+not+get+lock+lock-frontend&restrict_sr=1)

### 2.2 dpkg interrupted: error code (1)

> **Seen as:** `E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a' to correct the problem.` or `Errors were encountered while processing: apache2` followed by `E: Sub-process /usr/bin/dpkg returned an error code (1)` on every apt command · **Where:** upgrades over SSH that dropped, packages whose service fails to start in postinst, hosts with a full disk, mixed PPAs · **Level:** [L1 · Junior] · **How common:** one of the most common apt errors of all; dozens of how-to articles and a standard Server Fault question

**Why it happens:** dpkg unpacks a package, then runs its maintainer scripts (preinst, postinst and so on). Most postinst scripts restart the service. If that restart fails (invalid config, port already in use, full disk), or the upgrade is interrupted (SSH dropped without tmux, kill -9, power loss), the package stays half-configured and apt refuses further work until it is resolved. The error code (1) line is only the summary: the real cause is printed above it.

**Diagnose:**

```bash
sudo dpkg --audit                                   # what is half-installed or half-configured
sudo dpkg --configure -a 2>&1 | tail -15            # re-run and read the FIRST error
sudo grep -n -iE 'error|failed' /var/log/apt/term.log | tail -10
journalctl -u apache2 -n 10 --no-pager              # the service whose postinst failed
```

```text
The following packages are only half configured, probably due to problems
configuring them the first time.  The configuration should be retried using
dpkg --configure <package> or the configure menu option in dselect:
 apache2              Apache HTTP Server
Job for apache2.service failed because the control process exited with error code.
invoke-rc.d: initscript apache2, action "restart" failed.
dpkg: error processing package apache2 (--configure):
 installed apache2 package post-installation script subprocess returned error exit status 1
apachectl[48211]: (98)Address already in use: AH00072: make_sock: could not bind to address [::]:443
```

**What the output tells you:** the package files are fine; the postinst failed because Apache could not bind 443, which Traefik (or docker-proxy for Dokploy) already owns. This is the exact clash described in [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md). dpkg will keep failing until Apache can start or is told not to listen on 443.

**Fix:**

```bash
# 1. Fix the cause the log names (here: move Apache to other ports, or disable it)
#    (Ubuntu indents "Listen 443" inside IfModule blocks; change the 443 VirtualHosts in sites-enabled too)
sudo sed -i -E 's/^(\s*)Listen 443\b/\1Listen 444/' /etc/apache2/ports.conf
# 2. Finish configuring every half-done package, then let apt repair dependencies
sudo dpkg --configure -a
sudo apt-get -f install
# Interrupted run with no service error: the same two commands are usually enough.
# A "trying to overwrite '/usr/bin/X', which is also in package Y" conflict between repos:
# remove the package from the wrong repository instead of forcing the overwrite.
```

**Why this fix works:** once the service can start, the postinst succeeds and dpkg marks the package configured; `apt-get -f install` then completes any dependency left unconfigured. What NOT to do: edit /var/lib/dpkg/status or delete files under /var/lib/dpkg/info to "unstick" a package, or reach for `--force-overwrite` and `--force-all` before you know why two packages own the same file (that is usually a third-party repository for the wrong release).

**Prevent it:** run interactive upgrades inside tmux or screen, keep 2 GB free before upgrading, run `apachectl configtest` or `nginx -t` before upgrades on hosts with hand-edited configs, and don't mix PPAs and third-party repos built for another Ubuntu release.

**Next step:** [Packages: Common scenarios](11-packages.md) · [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) · [Ports inventory playbook](22-playbook-ports-inventory.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [tecmint: Fix Sub-process /usr/bin/dpkg returned an error code (1)](https://www.tecmint.com/sub-process-usr-bin-dpkg-returned-an-error-in-ubuntu/) · Search: [Server Fault](https://serverfault.com/search?q=%22dpkg+returned+an+error+code+%281%29%22+post-installation+script) · [Stack Overflow](https://stackoverflow.com/search?q=%22sub-process+%2Fusr%2Fbin%2Fdpkg+returned+an+error+code+%281%29%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=dpkg+configure+-a+post-installation+script&restrict_sr=1)

### 2.3 Packages kept back, held or unmet

> **Seen as:** `The following packages have been kept back:` after `apt upgrade`, or `The following packages have unmet dependencies: ... E: Unable to correct problems, you have held broken packages.` · **Where:** Ubuntu 22.04 and later fleets, hosts with PPAs or vendor repos, servers someone pinned by hand · **Level:** [L1 · Junior] · **How common:** very common; Ubuntu wrote a Server documentation page about it and Launchpad bug 1988819 tracks the confusion

**Why it happens:** four different causes produce similar messages. Phased updates: Ubuntu releases most non-security updates to a growing percentage of machines over several days, and on 22.04 and later apt itself honours the phase, so two identical servers can see different versions on the same day. New dependencies: `apt-get upgrade` never installs new packages, so an update that needs one is kept back. Holds: `apt-mark hold` (or a pin) freezes a package. Broken mixes: a third-party repository for the wrong release, or a PPA that replaced a library, makes the dependency solver give up, and apt calls this "held broken packages" even when nothing is held.

**Diagnose:**

```bash
apt list --upgradable 2>/dev/null | head
apt-cache policy openssh-server | head -8     # look for "(phased NN%)"
apt-mark showhold
sudo apt-get install --dry-run docker-ce 2>&1 | tail -6
grep -rhE '^(deb|Suites:|URIs:)' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null | sort -u
```

```text
openssh-server/noble-updates 1:9.6p1-3ubuntu13.14 amd64 [upgradable from: 1:9.6p1-3ubuntu13.13]
openssh-server:
  Installed: 1:9.6p1-3ubuntu13.13
  Candidate: 1:9.6p1-3ubuntu13.13
  Version table:
     1:9.6p1-3ubuntu13.14 500 (phased 30%)
        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
containerd.io
 docker-ce : Depends: containerd.io (>= 1.6.24) but it is not going to be installed
E: Unable to correct problems, you have held broken packages.
Suites: noble noble-updates noble-backports
URIs: http://archive.ubuntu.com/ubuntu
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu jammy stable
```

**What the output tells you:** openssh-server is simply phased at 30%, which is not an error. containerd.io is held on purpose, and the Docker repository points at jammy on a noble host, which explains the unmet dependency.

**Fix:**

```bash
# Phased update: wait, or install that one package now if you need it
sudo apt-get install openssh-server
# A hold you no longer want
sudo apt-mark unhold containerd.io
# Wrong-release repository: point it at this release, then retry
sudo sed -i 's/ jammy stable/ noble stable/' /etc/apt/sources.list.d/docker.list
sudo apt-get update && sudo apt-get install docker-ce
# Kept back because of new dependencies: let apt install them (it still never removes)
sudo apt upgrade        # or: sudo apt-get --with-new-pkgs upgrade
```

**Why this fix works:** each command removes the specific reason the solver refused. Phasing exists to stop a bad update from reaching every machine at once, so Ubuntu recommends leaving it on for production. If you need every host on identical versions, make that a decision: either set `APT::Get::Always-Include-Phased-Updates "true";` fleet-wide, or better, serve updates from a snapshot mirror (Landscape, aptly or Pulp) and promote snapshots through staging. What NOT to do: `apt full-upgrade -y` on a host with broken mixes without reading what it removes, or install single packages with `dpkg -i` to bypass the solver.

**Prevent it:** pin every third-party repo to `$(. /etc/os-release; echo $VERSION_CODENAME)` in your automation, record why each hold exists (a comment in the config management code), and decide the phasing policy for your fleet once.

**Next step:** [Packages: Debian / Ubuntu](11-packages.md) · [Learn Linux: Package management](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs: About apt upgrade and phased updates](https://ubuntu.com/server/docs/explanation/software/about-apt-upgrade-and-phased-updates/)

**Community threads:** [Launchpad 1988819: when apt keeps back packages due to phased updates](https://bugs.launchpad.net/bugs/1988819) · [Ubuntu Community Help Wiki: PhasedUpdates](https://help.ubuntu.com/community/PhasedUpdates) · Search: [Server Fault](https://serverfault.com/search?q=%22have+been+kept+back%22+phased+ubuntu) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=packages+kept+back+phased&restrict_sr=1)

### 2.4 NO_PUBKEY and legacy keyring after an upgrade

> **Seen as:** `W: https://download.docker.com/linux/ubuntu/dists/noble/InRelease: Key is stored in legacy trusted.gpg keyring (/etc/apt/trusted.gpg), see the DEPRECATION section in apt-key(8) for details.`, `NO_PUBKEY 8D81803C0EBFCD88`, or third-party repos silently gone after `do-release-upgrade` · **Where:** servers upgraded from 20.04 or 22.04 to 24.04, old provisioning scripts that still call `apt-key add` · **Level:** [L1 · Junior] · **How common:** a steady stream of Ubuntu Discourse threads after every LTS upgrade

**Why it happens:** apt-key and the single shared /etc/apt/trusted.gpg keyring are deprecated (apt-key is gone after Ubuntu 24.04 and Debian 12) because any key in that file could sign any repository. Current practice is one key file per repository, referenced with signed-by. A release upgrade also disables third-party sources and converts Ubuntu's own sources to the deb822 format in /etc/apt/sources.list.d/ubuntu.sources, so old one-line entries and the keys they relied on stop working. A related message, `no longer has a Release file`, means the release itself reached end of life and moved to old-releases.ubuntu.com.

**Diagnose:**

```bash
sudo apt-get update 2>&1 | grep -E 'NO_PUBKEY|legacy|Release file|disabled'
ls -l /etc/apt/trusted.gpg /etc/apt/trusted.gpg.d/ /etc/apt/keyrings/ 2>/dev/null
grep -rl 'disabled on upgrade' /etc/apt/sources.list.d/ 2>/dev/null
gpg --no-default-keyring --keyring /etc/apt/trusted.gpg --list-keys 2>/dev/null | grep -A1 '^pub'
```

```text
W: https://download.docker.com/linux/ubuntu/dists/noble/InRelease: Key is stored in legacy trusted.gpg keyring (/etc/apt/trusted.gpg), see the DEPRECATION section in apt-key(8) for details.
-rw-r--r-- 1 root root 2794 Mar 14  2023 /etc/apt/trusted.gpg
/etc/apt/keyrings/:
total 0
/etc/apt/sources.list.d/gitlab-runner.list
pub   rsa4096 2017-02-22 [SCEA]
      9DC858229FC7DD38854AE2D88D81803C0EBFCD88
```

**What the output tells you:** the Docker key lives in the legacy shared keyring, /etc/apt/keyrings is empty, and the GitLab Runner repository was disabled by the release upgrade. Both need the per-repository pattern.

**Fix:**

```bash
# One key per repository in /etc/apt/keyrings (ASCII-armored .asc works with signed-by)
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# deb822 source that names its key explicitly
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<'EOF'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo rm -f /etc/apt/sources.list.d/docker.list     # the old one-line entry
# Remove the key from the legacy keyring once nothing else needs it
sudo gpg --no-default-keyring --keyring /etc/apt/trusted.gpg --batch --yes --delete-keys 9DC858229FC7DD38854AE2D88D81803C0EBFCD88
sudo apt-get update
```

Re-enable each disabled third-party source the same way, with the vendor's current key URL and the new codename.

**Why this fix works:** signed-by binds a repository to exactly one key, so apt verifies the Docker repository with Docker's key and nothing else; the deb822 file makes the binding explicit and survives future release upgrades. What NOT to do: `[trusted=yes]` or `--allow-unauthenticated` to silence the error (that disables signature checks for the repository), or copying keys into /etc/apt/trusted.gpg.d where they again sign everything.

**Prevent it:** template every third-party repository in config management with signed-by and the release codename, check vendor docs before a release upgrade, and plan LTS upgrades before end of standard support.

**Next step:** [Packages](11-packages.md) · [Security & DevSecOps](37-learn-security-devsecops.md) (supply chain basics) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [Ubuntu Discourse: apt-key is deprecated and apt sources changed after release-upgrade to 24.04](https://discourse.ubuntu.com/t/apt-key-is-deprecated-and-apt-sources-changed-after-release-upgrade-to-24-04/53548) · [linuxize: Fix the NO_PUBKEY GPG error](https://linuxize.com/post/fix-no-pubkey-gpg-error-apt/) · Search: [Server Fault](https://serverfault.com/search?q=apt+%22legacy+trusted.gpg+keyring%22+signed-by) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=legacy+trusted.gpg+keyring+24.04&restrict_sr=1)

### 2.5 needrestart prompt hangs a script

> **Seen as:** an Ansible task or CI job running `apt-get upgrade` never finishes; on a terminal a text dialog asks `Which services should be restarted?` and lists dbus.service, networkd-dispatcher.service, polkit.service; or "Daemons using outdated libraries" appears in the middle of an install · **Where:** Ubuntu 22.04 and later, any automation that calls apt · **Level:** [L1 · Junior] · **How common:** very common since 22.04; vendors such as Wazuh received issues about the pop-up (wazuh-indexer#769)

**Why it happens:** Ubuntu 22.04 added needrestart as an apt hook. After an upgrade it finds daemons still running old library versions and, in interactive mode, asks which ones to restart (and shows a separate "pending kernel upgrade" notice). With a pseudo-terminal but nobody watching, the dialog waits forever. In automatic mode it restarts services by itself, which is the opposite surprise (entry 2.6). Later releases changed the defaults again, so check the config on your release rather than assuming.

**Diagnose:**

```bash
grep -rhE 'nrconf\{(restart|kernelhints)\}' /etc/needrestart/needrestart.conf /etc/needrestart/conf.d/ 2>/dev/null
ps -ef --forest | grep -B2 -A2 '[n]eedrestart'
# List what needrestart would restart, without restarting anything
sudo needrestart -r l -b
```

```text
#$nrconf{restart} = 'i';
root     30211 30188  0 09:14 pts/1    00:00:00  \_ /usr/bin/perl /usr/sbin/needrestart
NEEDRESTART-VER: 3.6
NEEDRESTART-KCUR: 6.8.0-79-generic
NEEDRESTART-KEXP: 6.8.0-85-generic
NEEDRESTART-KSTA: 3
NEEDRESTART-SVC: containerd.service
NEEDRESTART-SVC: ssh.service
```

**What the output tells you:** needrestart runs in its default interactive mode and is waiting under the apt process; it wants to restart containerd (which would restart every container on the host) and ssh, and a newer kernel is installed (KSTA 3 means a reboot is pending).

**Fix:**

```bash
# Per run in scripts: no prompts, list-only, decide restarts yourself
sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l apt-get -y upgrade
# Host default: list only, and no kernel dialog
sudo tee /etc/needrestart/conf.d/50-local.conf >/dev/null <<'EOF'
$nrconf{restart} = 'l';
$nrconf{kernelhints} = -1;
# If you choose 'a' (automatic) instead, never auto-restart the container runtime:
$nrconf{override_rc}{qr(^(docker|containerd)\.service$)} = 0;
EOF
```

**Why this fix works:** list mode keeps the useful information (which services run old libraries) without blocking or restarting anything, so restarts happen in your maintenance window. The override_rc entry keeps automatic mode from bouncing every container. What NOT to do: uninstall needrestart and then forget that daemons keep running vulnerable library versions after a security update, or let it auto-restart containerd on a Swarm or Kubernetes node without draining it.

**Prevent it:** bake the conf.d file into your image or baseline role, run `needrestart -r l -b` in your patch report, and keep needrestart itself updated (it had local privilege-escalation fixes in late 2024).

**Next step:** [Packages](11-packages.md) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [wazuh/wazuh-indexer#769: "Daemons using outdated libraries" pop-up under Ubuntu 22.04](https://github.com/wazuh/wazuh-indexer/issues/769) · [Prevent Ubuntu 22.04 and newer from prompting during updates for restart](https://www.hydrogen18.com/blog/disable-ubuntu-upgrade-needrestart.html) · [TechRadar: needrestart security flaw](https://www.techradar.com/pro/security/ubuntu-linux-has-a-worrying-security-flaw-that-may-have-gone-unseen-for-a-decade) · Search: [Server Fault](https://serverfault.com/search?q=needrestart+%22which+services+should+be+restarted%22) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=needrestart+ubuntu+22.04+prompt&restrict_sr=1)

### 2.6 Unattended-upgrades restarted or rebooted prod

> **Seen as:** a server rebooted at 04:00 with no change ticket; every container on a Docker host restarted at the same minute; a database restarted after a security update · **Where:** Ubuntu servers with unattended-upgrades on (the default), cloud images with Automatic-Reboot enabled by someone's user-data, hosts using Ubuntu's own docker.io or containerd packages · **Level:** [L3 · Senior] · **How common:** a recurring r/sysadmin and Server Fault complaint; the root of many "nobody touched it" incidents

**Why it happens:** unattended-upgrades installs security updates daily, which is good. But security updates to containerd, docker.io, OpenSSH or a database restart those services in their postinst, and with needrestart in automatic mode other daemons follow. A kernel update writes /var/run/reboot-required, and if `Unattended-Upgrade::Automatic-Reboot "true";` is set, the host reboots at Automatic-Reboot-Time (or immediately if no time is set). Each piece is reasonable on its own; together, on a node nobody drained, they are an outage.

**Diagnose:**

```bash
last -x reboot shutdown | head -4
sudo grep -hE 'Packages that will be upgraded|reboot' /var/log/unattended-upgrades/unattended-upgrades.log | tail -4
zgrep -h ' upgrade ' /var/log/dpkg.log* | grep -E 'containerd|docker|openssh|linux-image' | tail -4
apt-config dump | grep -E 'Unattended-Upgrade::(Automatic-Reboot|Package-Blacklist|Allowed-Origins)'
cat /var/run/reboot-required.pkgs 2>/dev/null
```

```text
reboot   system boot  6.8.0-85-generic Sat Oct  4 04:00 still running
shutdown system down  6.8.0-79-generic Sat Oct  4 04:00 - 04:00  (00:00)
2026-10-04 03:31:14,201 INFO Packages that will be upgraded: containerd linux-image-6.8.0-85-generic linux-modules-6.8.0-85-generic
2026-10-04 03:33:40,512 WARNING Found /var/run/reboot-required, rebooting
2026-10-04 03:32:02 upgrade containerd:amd64 1.7.27-0ubuntu1~24.04.1 1.7.28-0ubuntu1~24.04.1
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
```

**What the output tells you:** a containerd security update (restarting all containers at 03:32) and a kernel update arrived together, Automatic-Reboot was on, and the host rebooted at 04:00 as configured. Nothing failed; the policy did exactly what it says.

**Fix:**

```bash
sudo tee /etc/apt/apt.conf.d/52unattended-upgrades-local >/dev/null <<'EOF'
// Keep daily security updates, but take the runtime and reboots out of the robot's hands
Unattended-Upgrade::Package-Blacklist { "containerd"; "docker.io"; "docker-ce"; "containerd.io"; };
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
EOF
sudo unattended-upgrade --dry-run --debug 2>&1 | grep -iE 'blacklist|allowed' | head -5
```

Then patch the blacklisted packages and reboot in a planned window: drain the node first, upgrade, reboot, check, undrain, and stagger hosts so that never more than one node per role is down.

<div class="env" data-env="onprem" markdown="1">

On-premise, long-lived hosts are patched in place. Give each group of hosts a fixed weekly window, drain before touching anything (`docker node update --availability drain NODE` on Swarm, `kubectl drain NODE --ignore-daemonsets` on Kubernetes), patch and reboot one host per role at a time, and record the run. Canonical Livepatch (Ubuntu Pro) applies many kernel security fixes without a reboot and stretches the reboot interval. Keep the BMC or hypervisor console reachable during the window in case a host does not come back (9.3).

</div>

<div class="env" data-env="cloud" markdown="1">

In the cloud, prefer replacing over patching: rebuild the AMI monthly (or on critical CVEs) with Packer, then roll it out with an Auto Scaling group instance refresh, which drains and replaces instances in batches. Unattended-upgrades can stay on for security fixes between rebuilds with reboots disabled, while AWS Systems Manager Patch Manager or the instance refresh handles reboots. The same draining rules apply to ECS, EKS or Swarm nodes before replacement.

</div>

**Why this fix works:** security updates for everything else keep arriving daily, while the components whose restart is an outage (the container runtime, the kernel reboot) move into a controlled, drained, staggered process. What NOT to do: disable unattended-upgrades entirely (the usual outcome is a fleet months behind on security patches), or blacklist half the system "to be safe".

**Prevent it:** write the patch policy down (what updates automatically, what waits for the window, who reboots and how), alert on /var/run/reboot-required older than N days, and track reboots and package changes in your monitoring so "nobody touched it" is answered in a minute.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) · [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page)) · [Ubuntu Server docs: Automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/)

**Community threads:** [Ubuntu Server docs: Automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/) · [Launchpad 1260041: unattended-upgrades crashes with a dpkg error](https://bugs.launchpad.net/ubuntu/+source/unattended-upgrades/+bug/1260041) · Search: [Server Fault](https://serverfault.com/search?q=unattended-upgrades+containerd+restarted+containers) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=unattended-upgrades+rebooted+server&restrict_sr=1) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=unattended+upgrades+containers+restarted&restrict_sr=1)

## 3. systemd services and scheduled jobs

systemd starts, restarts, orders and stops everything on a modern server, and it logs why. Nearly every "service won't start" thread is answered by three commands: `systemctl status UNIT`, `journalctl -u UNIT -b` and `systemctl cat UNIT`. The entries below are the patterns behind those outputs.

### 3.1 Restart loop: Start request repeated too quickly

> **Seen as:** `systemctl status app` shows `Active: failed (Result: exit-code)`, and the journal ends with `app.service: Scheduled restart job, restart counter is at 5.`, `app.service: Start request repeated too quickly.`, `app.service: Failed with result 'exit-code'.` · **Where:** your own units with `Restart=always`, units installed by vendor packages, services that depend on a database or a mount · **Level:** [L1 · Junior] · **How common:** a classic; systemd#30804 asks systemd to warn about `Restart=always` without limits, and #39247 shows even D-Bus activated services tripping the limit

**Why it happens:** the service exits soon after starting (bad config, a missing environment variable, a port in use, a permission problem, a dependency not ready yet). `Restart=` starts it again, and after 5 starts within 10 seconds (the default StartLimitBurst and StartLimitIntervalSec) systemd stops trying and marks the unit failed. The "repeated too quickly" line is only the rate limiter speaking; the real error is in the lines before the first restart.

**Diagnose:**

```bash
systemctl status app --no-pager -l | head -15
# The real error: read the earliest lines of this boot, not the last ones
journalctl -u app -b --no-pager | grep -v 'Scheduled restart' | head -20
systemctl show app -p NRestarts -p ExecMainStatus -p Result -p RestartUSec
# Run the exact ExecStart as the service user to see the error directly
systemctl cat app | grep -E '^(User|ExecStart|EnvironmentFile)='
```

```text
× app.service - Shop API
     Loaded: loaded (/etc/systemd/system/app.service; enabled; preset: enabled)
     Active: failed (Result: exit-code) since Sat 2026-10-04 09:21:44 UTC; 12s ago
    Process: 51022 ExecStart=/opt/app/bin/server --config /etc/app/config.yml (code=exited, status=1/FAILURE)
Oct 04 09:21:42 web1 server[51004]: FATAL: DATABASE_URL is not set
Oct 04 09:21:42 web1 systemd[1]: app.service: Main process exited, code=exited, status=1/FAILURE
NRestarts=5
ExecMainStatus=1
Result=exit-code
RestartUSec=100ms
User=deploy
ExecStart=/opt/app/bin/server --config /etc/app/config.yml
```

**What the output tells you:** the binary starts and exits at once because DATABASE_URL is missing (no EnvironmentFile line), and RestartSec is the default 100 ms, so five restarts take half a second and trip the limit. Restarting faster will never fix a configuration error.

**Fix:**

```bash
sudo systemctl edit app
# In the editor, add:
#   [Unit]
#   StartLimitIntervalSec=300
#   StartLimitBurst=5
#   [Service]
#   EnvironmentFile=/etc/app/app.env
#   Restart=on-failure
#   RestartSec=5s
#   # systemd 254+ (Ubuntu 24.04, not RHEL 9): back off up to a minute
#   RestartSteps=5
#   RestartMaxDelaySec=60s
sudo systemctl reset-failed app
sudo systemctl restart app && journalctl -u app -f
```

**Why this fix works:** the drop-in adds the missing environment, waits 5 seconds (growing to 60 with RestartSteps) between attempts, and allows 5 failures in 5 minutes before giving up, which rides out a database that is still booting without hammering it. `reset-failed` clears the counter so the unit can start again. StartLimit settings belong in [Unit]; in [Service] only the legacy names StartLimitInterval= and StartLimitBurst= are still accepted for compatibility, and StartLimitIntervalSec= there is ignored with an "Unknown key" warning in the journal. What NOT to do: `StartLimitBurst=0` or `StartLimitIntervalSec=0` to restart forever (you get a hot loop and a full journal, entry 1.4).

**Prevent it:** run `systemd-analyze verify` on new units in CI, alert on failed units (node_exporter's systemd collector or a `systemctl --failed` check), and order units after what they need (`After=` and `Wants=` on postgresql.service or the mount).

**Next step:** [Services & systemd: Service status & control](07-services-systemd.md) · [Learn Linux: systemd and journald](27-learn-linux.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Create systemd Services · [systemd man pages: systemd.service](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [systemd#30804: warn about Restart=always without preventing the "repeated too quickly" loop](https://github.com/systemd/systemd/issues/30804) · [systemd#39247: D-Bus activated service trips StartLimitBurst earlier than expected](https://github.com/systemd/systemd/issues/39247) · [systemd#6129: exponentially increasing RestartSec](https://github.com/systemd/systemd/issues/6129) · Search: [Server Fault](https://serverfault.com/search?q=%22start+request+repeated+too+quickly%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=start+request+repeated+too+quickly&restrict_sr=1)

### 3.2 Works in my shell, fails as a service

> **Seen as:** `status=203/EXEC`, `status=217/USER`, `status=200/CHDIR`, `node: not found`, an app that can't find its config or env vars, or `start operation timed out. Terminating.` — while the same command works when you type it · **Where:** hand-written units for Node, Python, Java and Go apps, binaries installed with nvm, pyenv or sdkman, hardened units · **Level:** [L1 · Junior] · **How common:** one of the most common systemd questions on every forum

**Why it happens:** systemd does not run your login shell. A service gets a minimal PATH (/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin), no ~/.bashrc or ~/.profile, no variables except Environment= and EnvironmentFile=, the working directory /, the user in User=, no terminal, and possibly hardening such as ProtectHome= or ProtectSystem=strict that hides paths. Type= must match how the program behaves: a program that forks into the background under Type=simple looks like it exited, and one under Type=notify that never sends READY=1 hits the start timeout.

**Diagnose:**

```bash
systemctl status app --no-pager | grep -E 'status=|Main PID'
systemctl show app -p Type -p User -p WorkingDirectory -p Environment -p ProtectHome
# Reproduce the service context interactively (same user, env file, no login shell)
sudo systemd-run --uid=deploy --gid=deploy -p EnvironmentFile=/etc/app/app.env \
     -p WorkingDirectory=/opt/app --pty --wait --collect /opt/app/start.sh
systemd-analyze verify /etc/systemd/system/app.service
```

```text
   Process: 6120 ExecStart=/home/deploy/.nvm/versions/node/v22.11.0/bin/node server.js (code=exited, status=200/CHDIR)
Type=simple
User=deploy
WorkingDirectory=/opt/shop
Environment=
ProtectHome=yes
/etc/systemd/system/app.service:9: Executable "node" not found in PATH ... ignoring
```

**What the output tells you:** status 200/CHDIR means WorkingDirectory /opt/shop does not exist, ProtectHome=yes would hide the nvm binary under /home/deploy anyway, and an older ExecStart line used a bare `node` that systemd can't find. Common exit codes: 200/CHDIR (WorkingDirectory missing), 203/EXEC (binary missing, not executable or bad shebang), 217/USER (user doesn't exist), 226/NAMESPACE (a path named in a hardening option is missing).

**Fix:**

```ini
# /etc/systemd/system/app.service
[Unit]
Description=Shop API
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
User=deploy
Group=deploy
WorkingDirectory=/opt/app
EnvironmentFile=/etc/app/app.env
ExecStart=/usr/bin/node /opt/app/server.js
Restart=on-failure
RestartSec=5s
ProtectSystem=strict
ReadWritePaths=/var/lib/app /var/log/app

[Install]
WantedBy=multi-user.target
```

Install Node (or the runtime) system-wide under /usr or /opt rather than in a home directory, then `sudo systemctl daemon-reload && sudo systemctl restart app`.

**Why this fix works:** absolute paths, an explicit environment file and an existing working directory remove every dependency on your interactive shell; Type=exec reports a failure to execute the binary as a start failure instead of a vague exit later; ReadWritePaths opens exactly the directories a hardened unit needs. What NOT to do: `ExecStart=/bin/bash -lc "..."` to load a login profile (fragile, and signals then go to bash instead of your app), or run the service as root to get past permission errors.

**Prevent it:** keep a unit template in your repository, test it with `systemd-run` and `systemd-analyze verify`, and ship runtimes as packages or containers.

**Next step:** [Services & systemd: Unit files](07-services-systemd.md) · [Learn Linux: systemd and journald](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Creating a SYSTEMD Service ([notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page)) · [systemd man pages: systemd.exec](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [systemd issues by reactions](https://github.com/systemd/systemd/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Server Fault](https://serverfault.com/search?q=systemd+%22status%3D203%2FEXEC%22) · [Stack Overflow](https://stackoverflow.com/search?q=systemd+service+works+manually+environment+variables+PATH) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=systemd+service+works+manually+not+as+service&restrict_sr=1)

### 3.3 Unit edits that never take effect

> **Seen as:** `Warning: The unit file, source configuration file or drop-ins of nginx.service changed on disk. Run 'systemctl daemon-reload' to reload units.`; an override that "does nothing"; `Service has more than one ExecStart= setting, which is only allowed for Type=oneshot services. Refusing.`; your change to /lib/systemd/system/nginx.service vanished after an upgrade · **Where:** every host where people edit units by hand · **Level:** [L1 · Junior] · **How common:** very common; systemctl prints the reload warning so often that people stop reading it

**Why it happens:** systemd reads unit files into memory and only rereads them on `daemon-reload`. Vendor units live in /usr/lib/systemd/system (on Ubuntu /lib is the same directory) and are replaced by package upgrades; your changes belong in /etc/systemd/system, which wins over /run and /usr/lib. Drop-ins in UNIT.d/*.conf apply in file-name order, and list settings such as ExecStart= append instead of replacing, so an override must first clear the list with an empty `ExecStart=`.

**Diagnose:**

```bash
systemctl cat nginx                 # every fragment, with its path, in the order applied
systemctl show nginx -p FragmentPath -p DropInPaths -p NeedDaemonReload
systemd-delta --type=overridden,extended --no-pager
```

```text
# /usr/lib/systemd/system/nginx.service
[Service]
ExecStart=/usr/sbin/nginx -g 'daemon on; master_process on;'
# /etc/systemd/system/nginx.service.d/override.conf
[Service]
ExecStart=/usr/sbin/nginx -c /etc/nginx/custom.conf -g 'daemon on;'
FragmentPath=/usr/lib/systemd/system/nginx.service
DropInPaths=/etc/systemd/system/nginx.service.d/override.conf
NeedDaemonReload=yes
[EXTENDED]   /usr/lib/systemd/system/nginx.service → /etc/systemd/system/nginx.service.d/override.conf
```

**What the output tells you:** the override adds a second ExecStart instead of replacing the first (no empty `ExecStart=` line), and systemd has not reloaded since the file changed (NeedDaemonReload=yes).

**Fix:**

```bash
sudo systemctl edit nginx           # opens the override; daemon-reload happens on save
# Content:
#   [Service]
#   ExecStart=
#   ExecStart=/usr/sbin/nginx -c /etc/nginx/custom.conf -g 'daemon on; master_process on;'
sudo systemctl restart nginx
# Undo all local overrides of a unit
sudo systemctl revert nginx
```

**Why this fix works:** the empty assignment clears the vendor ExecStart list, the drop-in lives in /etc so package upgrades never touch it, and `systemctl edit` reloads systemd for you. What NOT to do: edit files under /usr/lib/systemd/system (lost on upgrade), or copy the whole vendor unit into /etc/systemd/system (you then miss every future vendor fix silently).

**Prevent it:** always use `systemctl edit`, keep drop-ins in config management, and add `systemd-delta` output to your host audit so local overrides are visible.

**Next step:** [Services & systemd: Unit files](07-services-systemd.md) · [Learn Linux: systemd and journald](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — SYSTEMD Tools · [systemd man pages: systemd.unit](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [ArchWiki: systemd/Timers (drop-in and unit examples)](https://wiki.archlinux.org/title/Systemd/Timers) · Search: [Server Fault](https://serverfault.com/search?q=systemd+override+ExecStart+%22more+than+one+ExecStart%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=systemctl+edit+override+not+working&restrict_sr=1)

### 3.4 Cron job runs by hand but not from cron

> **Seen as:** the backup script works when you run it, but from crontab nothing happens; the log shows `CRON[2211]: (deploy) CMD (/opt/scripts/backup.sh)` and then nothing, `(CRON) info (No MTA installed, discarding output)`, or the job's mail says `/bin/sh: 1: pg_dump: not found` · **Where:** every server with crontabs; /etc/cron.d and /etc/cron.daily scripts · **Level:** [L1 · Junior] · **How common:** one of the most-asked Linux questions of all time on Stack Overflow and Server Fault

**Why it happens:** cron runs jobs with /bin/sh, a PATH of /usr/bin:/bin, no login profile and the user's home as working directory. Then the crontab-specific traps: an unescaped `%` is turned into a newline; files in /etc/cron.d need a user field and a name without dots; scripts in /etc/cron.daily are run by run-parts, which on Debian and Ubuntu skips names containing a dot (backup.sh never runs); output goes to local mail, which is discarded when no MTA is installed. And a job scheduled while the server is down simply never runs.

**Diagnose:**

```bash
grep CRON /var/log/syslog | tail -5          # Ubuntu; RHEL: journalctl -u crond or /var/log/cron
journalctl -u cron --since today --no-pager | tail -5
run-parts --test /etc/cron.daily             # lists what WOULD run; backup.sh missing = skipped
# Run the job with cron's environment to see the real error
sudo -u deploy env -i HOME=/home/deploy SHELL=/bin/sh PATH=/usr/bin:/bin /bin/sh -c '/opt/scripts/backup.sh'
```

```text
Oct  4 02:00:01 web1 CRON[2211]: (deploy) CMD (/opt/scripts/backup.sh > /tmp/backup-$(date +)
Oct  4 02:00:01 web1 CRON[2209]: (CRON) info (No MTA installed, discarding output)
/etc/cron.daily/apt-compat
/etc/cron.daily/dpkg
/etc/cron.daily/logrotate
/opt/scripts/backup.sh: 7: pg_dump: not found
```

**What the output tells you:** the command line was cut at `%` (date +%F became the end of the command), the error output was thrown away, run-parts ignores backup.sh in cron.daily, and inside cron's PATH pg_dump (in /usr/lib/postgresql/16/bin or /usr/local/bin) is not found.

**Fix:**

```bash
# Option 1: a correct crontab line (crontab -e as deploy)
#   PATH=/usr/local/bin:/usr/bin:/bin
#   0 2 * * * flock -n /tmp/backup.lock /opt/scripts/backup.sh >> /var/log/app/backup.log 2>&1
# In a crontab line write % as \% (for example $(date +\%F)); inside the script plain %F is fine.

# Option 2: a systemd timer (logs in the journal, catches up after downtime, no overlap)
sudo tee /etc/systemd/system/backup.service >/dev/null <<'EOF'
[Unit]
Description=Nightly app backup
OnFailure=notify-failure@%n.service
[Service]
Type=oneshot
User=deploy
ExecStart=/opt/scripts/backup.sh
EOF
sudo tee /etc/systemd/system/backup.timer >/dev/null <<'EOF'
[Unit]
Description=Nightly app backup
[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=10m
Persistent=true
[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now backup.timer
systemctl list-timers backup.timer
```

The OnFailure line assumes a small notify-failure@.service template you write once (it can call a webhook or send mail); drop the line if you don't have one yet.

**Why this fix works:** an explicit PATH, redirected output and flock fix the classic cron failures; the timer goes further: output lands in `journalctl -u backup`, Persistent=true runs a missed job at the next boot, a oneshot service never overlaps itself, and OnFailure turns a silent failure into an alert. What NOT to do: `* * * * *` jobs that pile up without flock, or silencing a failing job with `> /dev/null 2>&1`.

**Prevent it:** prefer timers for new jobs, name cron.d and cron.daily files without dots, and monitor that each important job succeeded recently (a "last success" timestamp metric or a heartbeat check in Uptime Kuma) instead of trusting that it ran.

**Next step:** [Services & systemd: Timers and classic cron](07-services-systemd.md) · [Learn Linux: Scheduling](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (cron) · [systemd man pages: systemd.timer](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [ArchWiki: systemd/Timers](https://wiki.archlinux.org/title/Systemd/Timers) · [Amazon Linux 2023: systemd timers replace cron](https://docs.aws.amazon.com/linux/al2023/ug/cron.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=cron+job+works+manually+but+not+in+crontab) · [Server Fault](https://serverfault.com/search?q=cron+job+not+running+PATH+environment) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=cron+job+not+running&restrict_sr=1)

### 3.5 Boot waits two minutes for the network

> **Seen as:** the console shows `A start job is running for Wait for Network to be Configured (1min 41s / no limit)`, every boot takes two minutes longer than it should, and `systemctl --failed` lists systemd-networkd-wait-online.service · **Where:** Ubuntu servers with netplan and a second NIC, an unused port, a bridge or VLAN without carrier; VMs with a detached interface · **Level:** [L2 · Mid] · **How common:** many systemd issues (#27724, #30345, #25607) and downstream reports from appliance builders

**Why it happens:** network-online.target waits for systemd-networkd-wait-online, which by default waits until every interface networkd manages is configured, with a 120 second timeout. An interface in netplan that never gets a carrier or a DHCP lease (a spare NIC, a bridge with no ports up, a storage VLAN on a switch port that isn't patched) keeps it waiting until the timeout. Everything ordered after network-online.target (Docker, NFS mounts with _netdev, cloud-init, your units with `After=network-online.target`) waits too.

**Diagnose:**

```bash
systemd-analyze blame | head -4
systemd-analyze critical-chain network-online.target
networkctl list
journalctl -b -u systemd-networkd-wait-online --no-pager | tail -3
```

```text
2min 1.032s systemd-networkd-wait-online.service
     8.114s cloud-init.service
network-online.target @2min 3.410s
└─systemd-networkd-wait-online.service @2.371s +2min 1.032s
IDX LINK   TYPE     OPERATIONAL SETUP
  1 lo     loopback carrier     unmanaged
  2 enp6s0 ether    routable    configured
  3 enp7s0 ether    no-carrier  configuring
Oct 04 07:12:44 web1 systemd-networkd-wait-online[611]: Timeout occurred while waiting for network connectivity.
```

**What the output tells you:** the main NIC enp6s0 was routable after a few seconds, but enp7s0 has no carrier and stays "configuring", so wait-online burns its full two minutes.

**Fix:**

```yaml
# /etc/netplan/50-cloud-init.yaml (or your netplan file): mark the spare NIC optional
network:
  version: 2
  ethernets:
    enp6s0:
      dhcp4: true
    enp7s0:
      dhcp4: true
      optional: true
```

```bash
sudo netplan try          # applies with automatic rollback if you lose access
# Alternative: wait only for the interface that matters
sudo systemctl edit systemd-networkd-wait-online.service
#   [Service]
#   ExecStart=
#   ExecStart=/usr/lib/systemd/systemd-networkd-wait-online --interface=enp6s0 --timeout=30
```

**Why this fix works:** optional interfaces don't count towards "online", and the drop-in limits the wait to the uplink with a shorter timeout. What NOT to do: `systemctl mask systemd-networkd-wait-online` on hosts with NFS mounts or services that truly need the network at start (they then start before the network and fail in other ways, see 9.2 and 10.2).

**Prevent it:** describe only real interfaces in netplan, mark the rest optional, and look at `systemd-analyze blame` after each new server build.

**Next step:** [Services & systemd: Boot problems & slowness](07-services-systemd.md) · [Network](02-network.md) · [Networking, DNS, TLS & VPN problems](42-problems-network-dns-tls-vpn.md) · [No IP after a reset or a hardware change](42-problems-network-dns-tls-vpn.md#16-a-server-or-nas-gets-no-ip-after-a-reset-or-a-hardware-change) (a renamed NIC leaves the configured one without carrier) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Manage Startup Process and Services · [systemd man pages: systemd-networkd-wait-online.service](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [systemd#27724: wait-online failing with a bridge interface, boot pauses two minutes](https://github.com/systemd/systemd/issues/27724) · [systemd#30345: wait-online fails if an interface is not connected](https://github.com/systemd/systemd/issues/30345) · [systemd#25607: wait-online event loop failed, connection timed out](https://github.com/systemd/systemd/issues/25607) · Search: [Server Fault](https://serverfault.com/search?q=systemd-networkd-wait-online+timeout+boot) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=wait+for+network+to+be+configured+2+minutes&restrict_sr=1)

### 3.6 Shutdown hangs on a stop job

> **Seen as:** `A stop job is running for Docker Application Container Engine (1min 12s / 1min 30s)`, `A stop job is running for User Manager for UID 1000`, or a reboot that never finishes while an NFS mount unmounts · **Where:** Docker hosts, servers with NFS mounts, apps that ignore SIGTERM, hosts with lingering tmux sessions · **Level:** [L2 · Mid] · **How common:** a classic across Ubuntu, openSUSE and Podman reports (containers/podman#15284)

**Why it happens:** at shutdown systemd sends SIGTERM to each unit and waits up to TimeoutStopSec (DefaultTimeoutStopSec is 90 s) before SIGKILL. Units that ignore SIGTERM, an ExecStop that blocks (a drain script waiting forever), containers with long stop grace periods, and NFS unmounts after the network is already down (missing _netdev ordering, see 10.2) all show up as the countdown. A hung NFS mount can block indefinitely.

**Diagnose:**

```bash
# After the slow reboot: what did the previous boot wait for?
journalctl -b -1 --no-pager | grep -E 'stop job|Stopping|timed out|State .stop-sigterm. timed out|Killing process' | tail -10
systemctl show docker -p TimeoutStopUSec -p KillMode -p ExecStop
# For a hang you can't get past: a root shell on tty9 during the next shutdown (remove afterwards!)
sudo systemctl enable debug-shell.service
```

```text
Oct 04 06:58:31 web1 systemd[1]: Stopping docker.service - Docker Application Container Engine...
Oct 04 06:58:41 web1 dockerd[1022]: level=info msg="Container failed to exit within 10s of signal 15 - using the force" container=7c1e...
Oct 04 07:00:01 web1 systemd[1]: docker.service: State 'stop-sigterm' timed out. Killing.
Oct 04 07:00:01 web1 systemd[1]: docker.service: Killing process 1022 (dockerd) with signal SIGKILL.
TimeoutStopUSec=1min 30s
KillMode=process
ExecStop=
```

**What the output tells you:** one container ignored SIGTERM and Docker itself then took the whole 90 seconds before systemd killed dockerd. The cause is the app's signal handling (or a shell entrypoint that doesn't forward signals), not systemd.

**Fix:**

```bash
# Fix the app: handle SIGTERM, or run it with an init that forwards signals
#   compose:  init: true      stop_grace_period: 20s
# Give the unit an explicit, realistic stop budget instead of the global default
sudo systemctl edit docker.service
#   [Service]
#   TimeoutStopSec=120
# Remove the debug shell again once you have your evidence
sudo systemctl disable debug-shell.service
```

**Why this fix works:** an app that exits on SIGTERM stops in seconds, `init: true` adds a tiny init process as PID 1 in the container so signals reach the app, and a per-unit timeout documents how long a clean stop really needs. What NOT to do: set DefaultTimeoutStopSec=5s globally (databases and queues get SIGKILL mid-write and need crash recovery on the next start), or leave debug-shell enabled (it is an unauthenticated root shell on the console).

**Prevent it:** test `docker stop` and `systemctl stop` times for each service, mount network filesystems with `_netdev` (and automount), and record expected stop times in the service's runbook.

**Next step:** [Services & systemd](07-services-systemd.md) · [Learn Docker](30-learn-docker.md) · [Processes: signals](05-processes.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Manage Startup Process and Services · [systemd man pages: systemd.kill](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [containers/podman#15284](https://github.com/containers/podman/issues/15284) · [ubuntuhandbook: slow shutdown, "A stop job is running"](https://ubuntuhandbook.org/index.php/2019/12/slow-shutdown-stop-job-running/) · Search: [Server Fault](https://serverfault.com/search?q=%22a+stop+job+is+running%22+shutdown) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=a+stop+job+is+running+shutdown&restrict_sr=1)

## 4. Users, sudo and permissions

"Permission denied" is the most overloaded error on Linux: it can come from mode bits on any directory in the path, ACLs, mount options, AppArmor, SELinux or sudo itself. The fix is never `chmod 777`; it is finding which layer said no.

### 4.1 sudo broken: sudoers syntax or host name

> **Seen as:** `>>> /etc/sudoers.d/deploy: syntax error near line 1 <<<`, `sudo: parse error in /etc/sudoers.d/deploy near line 1`, `sudo: no valid sudoers sources found, quitting`; or every sudo pauses for seconds and prints `sudo: unable to resolve host web02: Name or service not known` · **Where:** hosts where sudoers files are written by echo, templates or a quick edit; servers renamed with hostnamectl · **Level:** [L1 · Junior] · **How common:** classic; AWS and Google Cloud each publish a recovery page for broken sudoers

**Why it happens:** sudo refuses to run at all if any sudoers file has a syntax error, so one bad line in /etc/sudoers.d removes root access for everyone (Ubuntu has no root password by default). Files in sudoers.d must be mode 0440 and owned by root, and files whose names contain a dot or end in ~ are silently ignored. The host-name variant is harmless but noisy: sudo looks up the machine's own name, and after `hostnamectl set-hostname web02` nobody added web02 to /etc/hosts.

**Diagnose:**

```bash
# sudo itself is broken, so use polkit to check the files as root
pkexec visudo -c
ls -l /etc/sudoers.d/
hostnamectl --static
getent hosts "$(hostname)" || echo "own hostname does not resolve"
```

```text
/etc/sudoers: parsed OK
>>> /etc/sudoers.d/deploy: syntax error near line 1 <<<
-r--r----- 1 root root  958 Feb 20  2024 README
-rw-r--r-- 1 root root   42 Oct  4 10:02 deploy
web02
own hostname does not resolve
```

**What the output tells you:** /etc/sudoers is fine, the new file /etc/sudoers.d/deploy has a syntax error (and the wrong mode), and web02 is missing from /etc/hosts. Two separate problems, one urgent.

**Fix:**

```bash
# Fix the file with validation (pkexec asks for your password; works if you are in the sudo group)
pkexec visudo -f /etc/sudoers.d/deploy
#   deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart app
pkexec chmod 0440 /etc/sudoers.d/deploy
# Host name: map it to 127.0.1.1 (Debian/Ubuntu convention)
pkexec sed -i 's/^127\.0\.1\.1.*/127.0.1.1 web02/' /etc/hosts
```

If pkexec reports `No authentication agent found` (common over SSH), use the console: reboot into the GRUB "recovery mode" entry, choose root, run `mount -o remount,rw /`, then `visudo -f /etc/sudoers.d/deploy`. Without console access, use the out-of-band paths in entry 5.3. On cloud images, cloud-init may regenerate /etc/hosts from a template (`manage_etc_hosts: true`), so change the template or set the hostname through cloud-init.

**Why this fix works:** visudo checks the syntax before saving, so you can't lock yourself out again, and mode 0440 is what sudo expects. The hosts entry lets sudo resolve its own name instantly. What NOT to do: write sudoers files with `echo >>` or an unvalidated template, or "fix" sudo by enabling a root password over SSH.

**Prevent it:** in Ansible, write sudoers with `validate: 'visudo -cf %s'`; in other tools, run `visudo -cf FILE` before moving the file into place; keep a second session open when changing sudo rules; set the hostname and /etc/hosts together.

**Next step:** [Users, permissions & security: sudo problems](10-users-permissions-security.md) · [Learn Linux: Users, groups and sudo](27-learn-linux.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Users and Groups · [sudo documentation](https://www.sudo.ws/docs/)

**Community threads:** [AWS re:Post: fix sudo errors in EC2 or Lightsail](https://repost.aws/knowledge-center/ec2-sudoers-syntax-errors-sudo) · [Google Cloud: troubleshooting the sudoers file](https://docs.cloud.google.com/compute/docs/troubleshooting/troubleshooting-sudoers-file) · [Linux Handbook: sudo unable to resolve host](https://linuxhandbook.com/sudo-unable-resolve-host/) · Search: [Server Fault](https://serverfault.com/search?q=%22no+valid+sudoers+sources+found%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=broke+sudoers+locked+out&restrict_sr=1)

### 4.2 Permission denied although the file is 755

> **Seen as:** `nginx: [crit] open() "/home/deploy/site/index.html" failed (13: Permission denied)` and a 403, `bash: ./run.sh: Permission denied` on an executable file, `permission denied while trying to connect to the Docker daemon socket` right after adding yourself to the docker group · **Where:** web roots in home directories, /tmp mounted noexec, freshly added group memberships, AppArmor-confined services · **Level:** [L1 · Junior] · **How common:** among the most common Linux questions; nginx 403 from a home directory alone is a Stack Overflow classic

**Why it happens:** to open /home/deploy/site/index.html, the user needs x (search) permission on every directory in the path, not just read on the file, and Ubuntu 21.04 and later create home directories as 750, so www-data can't pass /home/deploy. A file with x set still won't run from a filesystem mounted noexec (hardened /tmp, /dev/shm, some /home mounts). New group memberships only apply to new login sessions. On Ubuntu, AppArmor profiles can deny a path even when modes allow it (on RHEL that is SELinux, entry 4.4).

**Diagnose:**

```bash
namei -l /home/deploy/site/index.html
sudo -u www-data head -c 80 /home/deploy/site/index.html
findmnt -no OPTIONS -T /tmp
id deploy; id          # the group in /etc/group vs. the groups of your current session
sudo journalctl -k --since -1h | grep -i 'apparmor="DENIED"' | tail -3
```

```text
f: /home/deploy/site/index.html
drwxr-xr-x root   root   /
drwxr-xr-x root   root   home
drwxr-x--- deploy deploy deploy
drwxr-xr-x deploy deploy site
-rw-r--r-- deploy deploy index.html
head: cannot open '/home/deploy/site/index.html' for reading: Permission denied
rw,nosuid,nodev,noexec,relatime
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),988(docker)
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy)
```

**What the output tells you:** the file is world-readable, but /home/deploy is 750, so www-data stops at the third component. /tmp is noexec, which explains the script error there. And the current session does not have the docker group yet, although the account does.

**Fix:**

```bash
# Best: serve content from a path meant for it
sudo install -d -o deploy -g www-data -m 2750 /srv/www/site
# Or grant traverse-only access to one user, nothing more
sudo setfacl -m u:www-data:x /home/deploy
# Group change: start a new login session (or newgrp docker in the current shell)
exit    # and log in again
# Scripts in a noexec mount: run them from /opt or /usr/local/bin, or call the interpreter
bash /tmp/run.sh
```

**Why this fix works:** /srv with a setgid directory owned by the web group is the designed place for served content; the ACL gives www-data passage through the home directory without letting it list or read anything else; a new session picks up the new group list. What NOT to do: `chmod -R 777 /home/deploy` (every user and every compromised process can now change the site and the deploy user's keys), or remove noexec from /tmp on a hardened server to make one script work.

**Prevent it:** keep served files and app data under /srv, /var/www or /opt with explicit owners, check paths with `namei -l` when you design them, and document required group memberships in the provisioning code.

**Next step:** [Users, permissions & security: File permissions](10-users-permissions-security.md) · [Learn Linux: Files, permissions and ownership](27-learn-linux.md) · [Web, HTTP & TLS](18-web-http-tls.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions · [AppArmor docs](https://apparmor.net/)

**Community threads:** [ArchWiki: Access Control Lists](https://wiki.archlinux.org/title/Access_Control_Lists) · Search: [Stack Overflow](https://stackoverflow.com/search?q=nginx+13+permission+denied+home+directory+403) · [Server Fault](https://serverfault.com/search?q=%2213%3A+Permission+denied%22+nginx+home+directory) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=permission+denied+namei&restrict_sr=1)

### 4.3 Shared deploy directory: ACL mask and setgid

> **Seen as:** the CI deploy user and the app user overwrite each other's permissions: `cp: cannot create regular file '/srv/app/releases/42/config.yml': Permission denied`, or getfacl shows `group:deployers:rwx    #effective:r-x` · **Where:** shared release directories, upload folders written by an app and read by a backup job, directories used by two systemd services · **Level:** [L2 · Mid] · **How common:** a recurring sysadmin puzzle; the ArchWiki ACL page and its talk page discuss the mask behaviour at length

**Why it happens:** new files get the creating user's primary group and its umask (022 removes group write). A default ACL on the directory is inherited by new files, but the ACL mask on each new file is limited by the mode the program asked for, so a program creating files 0644 yields `mask::r--` and every named group entry is cut to read-only. `chmod g-w` on a file with an ACL changes the mask, not the group entry. Tools such as `cp -p`, `rsync -a`, tar and git also set modes from the source, overriding what the directory intended.

**Diagnose:**

```bash
getfacl -p /srv/app /srv/app/releases/42/config.yml
stat -c '%A %U:%G %n' /srv/app /srv/app/releases/42
# The umask a running service really uses
grep Umask /proc/"$(systemctl show -p MainPID --value app)"/status
```

```text
# file: /srv/app
# owner: deploy
# group: deployers
user::rwx
group::rwx
group:deployers:rwx
mask::rwx
other::r-x
default:user::rwx
default:group::rwx
default:group:deployers:rwx
default:mask::rwx
default:other::r-x

# file: /srv/app/releases/42/config.yml
# owner: ci
# group: ci
user::rw-
group::rwx			#effective:r--
group:deployers:rwx		#effective:r--
mask::r--
other::r--

drwxrwsr-x deploy:deployers /srv/app
drwxr-xr-x ci:ci /srv/app/releases/42
Umask:	0022
```

**What the output tells you:** the default ACL was inherited, but the CI job created the file 0644 (rsync -a copied the mode from the build), so the mask is r-- and deployers can't write. The release directory also lost the setgid bit and the deployers group, so files inside it get the ci group.

**Fix:**

```bash
# Repair existing tree: group, setgid on directories, ACL entries and default ACL
sudo chgrp -R deployers /srv/app
sudo find /srv/app -type d -exec chmod g+rwxs {} +
sudo setfacl -R -m g:deployers:rwX,m::rwX /srv/app
sudo setfacl -R -d -m g:deployers:rwX /srv/app
# Make writers create group-writable files from now on
sudo systemctl edit app            # [Service] UMask=0002
rsync -rlt --chmod=Dg+rwxs,Fg+rw build/ /srv/app/releases/43/   # in the CI job: don't copy source modes
```

**Why this fix works:** setgid on directories makes new files inherit the deployers group, `rwX` gives execute only to directories and already-executable files, the default ACL covers new files, and a 002 umask (or rsync's --chmod) stops the creating program from cutting the mask. What NOT to do: run the app and CI as the same user "to avoid permissions", or `chmod 777` the release tree.

**Prevent it:** prefer one writer: CI deploys as deploy, the app runs as another user with read access and writes only to a dedicated data directory; when you do need a shared directory, set it up with the commands above in config management and test with both users.

**Next step:** [Users, permissions & security: File permissions](10-users-permissions-security.md) · [Learn Linux: Files, permissions and ownership](27-learn-linux.md) · [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Users and Groups · [setfacl man page](https://www.man7.org/linux/man-pages/man1/setfacl.1.html)

**Community threads:** [ArchWiki: Access Control Lists](https://wiki.archlinux.org/title/Access_Control_Lists) · [ArchWiki talk: Access Control Lists](https://wiki.archlinux.org/title/Talk:Access_Control_Lists) · Search: [Server Fault](https://serverfault.com/search?q=setfacl+default+acl+mask+effective+group+write) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=setfacl+default+acl+mask&restrict_sr=1)

### 4.4 SELinux blocks a service on RHEL

> **Seen as:** nginx returns 502 with `connect() to 127.0.0.1:8080 failed (13: Permission denied) while connecting to upstream`, or `nginx: [emerg] bind() to 0.0.0.0:8444 failed (13: Permission denied)`, or a 403 for files you moved into the web root; the audit log shows `avc:  denied` · **Where:** RHEL, Rocky, Alma and Fedora servers with SELinux enforcing (the default); containers with bind mounts on those hosts · **Level:** [L2 · Mid] · **How common:** the classic RHEL "permission denied"; Red Hat documents it in a whole chapter and a dedicated CLI troubleshooting article

**Why it happens:** SELinux checks a second set of rules after the normal permissions: each process has a type (nginx runs as httpd_t) and each file and port has a label. Files moved with `mv` keep their original label (user_home_t instead of httpd_sys_content_t), non-standard ports are not labelled for the service, and network connections from web servers to other ports are off unless the httpd_can_network_connect boolean is set.

**Diagnose:**

```bash
getenforce
sudo ausearch -m AVC,USER_AVC -ts recent | tail -4
ls -Z /srv/www/index.html
sudo semanage port -l | grep -w http_port_t
# Human-readable advice (package setroubleshoot-server)
sudo sealert -a /var/log/audit/audit.log | head -20
```

```text
Enforcing
type=AVC msg=audit(1791106011.412:812): avc:  denied  { name_connect } for  pid=1402 comm="nginx" dest=8080 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:http_cache_port_t:s0 tclass=tcp_socket permissive=0
type=AVC msg=audit(1791106040.118:815): avc:  denied  { read } for  pid=1403 comm="nginx" name="index.html" dev="dm-0" ino=3301 scontext=system_u:system_r:httpd_t:s0 tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file permissive=0
unconfined_u:object_r:user_home_t:s0 /srv/www/index.html
http_port_t                    tcp      80, 81, 443, 488, 8008, 8009, 8443, 9000
```

**What the output tells you:** two denials: nginx may not connect to port 8080 (a boolean is off), and index.html carries the user_home_t label because it was moved from a home directory. Port 8444 is not in the http_port_t list, so nginx can't bind it until you label it (8443 would have worked).

**Fix:**

```bash
sudo setsebool -P httpd_can_network_connect 1        # allow proxying to upstream ports
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www(/.*)?'
sudo restorecon -Rv /srv/www                           # apply the labels to existing files
sudo semanage port -a -t http_port_t -p tcp 8444       # only if you need a new, unlabelled port
# Containers with bind mounts on SELinux hosts: let the runtime relabel
#   podman run -v /srv/data:/data:Z ...
```

**Why this fix works:** each command changes the policy input that caused one denial: a boolean, a persistent file-context rule plus relabel, or a port label. The rest of SELinux protection stays on. What NOT to do: `setenforce 0` or SELINUX=disabled as the fix (you remove a security layer for the whole host), or `audit2allow -M` on every denial without reading it (that can grant far more than needed).

**Prevent it:** create web roots and data directories with semanage rules in your Ansible role, deploy with `cp` or packages rather than `mv` from home directories, and review AVC denials in your log pipeline (Wazuh decodes them).

**Next step:** [Users, permissions & security: SELinux](10-users-permissions-security.md) · [Security & DevSecOps](37-learn-security-devsecops.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Users and Groups · [RHEL 9: Using SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/using_selinux/index)

**Community threads:** [RHEL 9 docs: Troubleshooting problems related to SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/troubleshooting-problems-related-to-selinux_using-selinux) · [Red Hat: Basic SELinux troubleshooting in CLI](https://access.redhat.com/articles/2191331) · Search: [Server Fault](https://serverfault.com/search?q=selinux+nginx+%22permission+denied%22+upstream+httpd_can_network_connect) · [Reddit r/redhat](https://www.reddit.com/r/redhat/search/?q=selinux+permission+denied+nginx&restrict_sr=1)

## 5. SSH access and lockouts

SSH is how you reach everything else, so SSH problems escalate fast. The client error is almost always vague (`Permission denied (publickey)`, `Connection timed out`); the precise reason is in the server's log, which is why every entry here starts on the server side or at the console.

### 5.1 Key login refused: bad ownership or modes

> **Seen as:** the client prints `deploy@10.0.1.10: Permission denied (publickey).`; the server logs `Authentication refused: bad ownership or modes for directory /home/deploy`, `userauth_pubkey: key type ssh-rsa not in PubkeyAcceptedAlgorithms [preauth]` or `User deploy from 198.51.100.7 not allowed because not listed in AllowUsers` · **Where:** new users created by hand, home directories changed by a careless chown or chmod, old RSA keys against OpenSSH 8.8 and later, hardened sshd configs · **Level:** [L1 · Junior] · **How common:** a classic; nixCraft and many other guides, plus a large share of SSH questions on Server Fault

**Why it happens:** with StrictModes (the default), sshd refuses to use authorized_keys if the home directory or ~/.ssh is writable by group or others, or owned by someone else, because then another user could plant a key. Other common server-side reasons: the key file was copied by root and is owned by root, the client offers an old ssh-rsa (SHA-1) key that current OpenSSH rejects, the user is not in AllowUsers or AllowGroups, the account is locked or expired, or the home directory sits on NFS with root_squash and sshd can't read it.

**Diagnose:**

```bash
# Server side (Ubuntu unit: ssh; RHEL unit: sshd)
sudo journalctl -u ssh -n 20 --no-pager | grep -iE 'refused|not allowed|userauth|invalid'
sudo namei -l /home/deploy/.ssh/authorized_keys
sudo sshd -T | grep -iE '^(strictmodes|pubkeyacceptedalgorithms|allowusers|allowgroups|authorizedkeysfile)'
# Client side: which keys are offered and what the server answers
ssh -v deploy@10.0.1.10 2>&1 | grep -E 'Offering|Server accepts|Authentications that can continue'
```

```text
Oct 04 10:31:12 web1 sshd[51877]: Authentication refused: bad ownership or modes for directory /home/deploy
f: /home/deploy/.ssh/authorized_keys
drwxr-xr-x root   root   /
drwxr-xr-x root   root   home
drwxrwxr-x deploy deploy deploy
drwx------ deploy deploy .ssh
-rw------- root   root   authorized_keys
strictmodes yes
authorizedkeysfile .ssh/authorized_keys .ssh/authorized_keys2
debug1: Offering public key: /home/ops/.ssh/id_ed25519 ED25519 SHA256:3qL0... explicit
debug1: Authentications that can continue: publickey
```

**What the output tells you:** the home directory is group-writable (775) and authorized_keys belongs to root. Either is enough for StrictModes to refuse the key, even though the client offers the right one.

**Fix:**

```bash
sudo chmod go-w /home/deploy
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
# Old RSA key rejected: create a modern key on the client and install it
ssh-keygen -t ed25519 -C "ops@laptop"
ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@10.0.1.10
```

**Why this fix works:** the modes and owners now match what StrictModes demands, so sshd reads the key file; an ed25519 key avoids the SHA-1 signature algorithm that OpenSSH disabled by default. What NOT to do: `StrictModes no` (it hides real tampering risks), or re-enabling ssh-rsa server-wide for one old client instead of replacing the key.

**Prevent it:** create users and keys with config management (Ansible's authorized_key module sets owner and mode), never edit another user's authorized_keys as root without fixing ownership afterwards, and keep `sshd -T` output in your host audit.

**Next step:** [SSH & remote access: Server side](09-ssh-remote-access.md) · [Learn Linux: SSH](27-learn-linux.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure SSH Servers and Clients · [OpenSSH manual pages](https://www.openssh.com/manual.html)

**Community threads:** [nixCraft: Authentication refused: bad ownership or modes](https://www.cyberciti.biz/faq/openssh-server-authentication-refused-bad-ownership-or-modes/) · [fabianlee: fixing "bad ownership or modes"](https://fabianlee.org/2023/11/05/bash-fixing-ssh-authentication-error-bad-ownership-or-modes-for-file-directory/) · Search: [Server Fault](https://serverfault.com/search?q=%22bad+ownership+or+modes%22+authorized_keys) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=ssh+permission+denied+publickey+authorized_keys&restrict_sr=1)

### 5.2 sshd config changes ignored on Ubuntu 24.04

> **Seen as:** after setting `Port 2222` and `systemctl restart ssh`, `ss -ltnp` still shows port 22 owned by `systemd`; or `PasswordAuthentication no` in /etc/ssh/sshd_config has no effect and passwords still work · **Where:** Ubuntu 22.10 and later (socket activation), Ubuntu cloud images and installs with files in /etc/ssh/sshd_config.d/ · **Level:** [L1 · Junior] · **How common:** a multi-page Ubuntu Discourse thread, Launchpad bug 2069041, and many lockouts when the firewall was changed to the new port first

**Why it happens:** two separate surprises. Socket activation: since 22.10, ssh.socket (owned by systemd) listens on the port and starts ssh.service when the first connection arrives. On 22.10 to 23.10 the upgrade moved Port and ListenAddress into /etc/systemd/system/ssh.socket.d/addresses.conf; on 24.04 a systemd generator reads them from sshd_config, but only when systemd reloads, so restarting ssh.service changes nothing. First match wins: sshd_config starts with `Include /etc/ssh/sshd_config.d/*.conf`, and for most options sshd keeps the first value it reads, so a cloud-init file such as 50-cloud-init.conf with `PasswordAuthentication yes` beats your line further down in sshd_config.

**Diagnose:**

```bash
systemctl is-active ssh.socket ssh.service
sudo ss -ltnp | grep -E ':(22|2222)\s'
systemctl cat ssh.socket | grep -E '^#|ListenStream'
# Effective sshd settings, after all includes
sudo sshd -T | grep -E '^(port|passwordauthentication)'
grep -rn -iE '^(Port|PasswordAuthentication)' /etc/ssh/sshd_config.d/ /etc/ssh/sshd_config
```

```text
active
inactive
LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*    users:(("systemd",pid=1,fd=137))
LISTEN 0      4096            [::]:22           [::]:*    users:(("systemd",pid=1,fd=138))
# /usr/lib/systemd/system/ssh.socket
ListenStream=22
port 2222
passwordauthentication yes
/etc/ssh/sshd_config.d/50-cloud-init.conf:1:PasswordAuthentication yes
/etc/ssh/sshd_config:14:Port 2222
/etc/ssh/sshd_config:58:PasswordAuthentication no
```

**What the output tells you:** ssh.socket is active and systemd (PID 1) still listens on 22; the socket unit only has the packaged `ListenStream=22`, because the 24.04 generator writes its drop-in (under /run/systemd/generator/ssh.socket.d/) only when systemd reloads, which has not happened since you edited the file. sshd -T shows that passwords stay enabled because the cloud-init include is read first.

**Fix:**

```bash
# 1. Open the new port in the firewall BEFORE moving SSH
sudo ufw allow 2222/tcp
# 2. Put your settings in an early drop-in so they win, and validate
echo -e 'Port 2222\nPasswordAuthentication no' | sudo tee /etc/ssh/sshd_config.d/10-local.conf
sudo sshd -t
# 3. 24.04: regenerate the socket config and restart the SOCKET
sudo systemctl daemon-reload
sudo systemctl restart ssh.socket
# 4. In a SECOND terminal: ssh -p 2222 ops@10.0.1.10, and only then remove port 22 from the firewall
# Prefer the classic daemon? Revert socket activation:
#   sudo systemctl disable --now ssh.socket
#   sudo rm -f /etc/systemd/system/ssh.service.d/00-socket.conf /etc/systemd/system/ssh.socket.d/addresses.conf
#   sudo systemctl daemon-reload && sudo systemctl enable --now ssh.service
```

**Why this fix works:** daemon-reload reruns the generator, which writes the new ListenStream lines, and restarting ssh.socket rebinds the listener; the 10-local.conf file is read before 50-cloud-init.conf, so your values are the first ones sshd sees. Opening the firewall first and testing in a second session keeps a way back. What NOT to do: change the firewall and close your only session before testing, or edit 50-cloud-init.conf (cloud-init may rewrite it).

**Prevent it:** manage sshd settings as a low-numbered drop-in, always check `sshd -T` instead of reading sshd_config, and keep a console path ready (entry 5.3).

**Next step:** [SSH & remote access](09-ssh-remote-access.md) · [Ports inventory playbook](22-playbook-ports-inventory.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure SSH Servers and Clients · [OpenSSH manual pages](https://www.openssh.com/manual.html)

**Community threads:** [Ubuntu Discourse: SSHd now uses socket-based activation (22.10 and later)](https://discourse.ubuntu.com/t/sshd-now-uses-socket-based-activation-ubuntu-22-10-and-later/30189?page=2) · [Launchpad 2069041: changing Port in sshd_config requires calling systemctl daemon-reload](https://bugs.launchpad.net/ubuntu/+source/openssh/+bug/2069041) · Search: [Server Fault](https://serverfault.com/search?q=ubuntu+24.04+ssh+port+change+ssh.socket) · [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=24.04+ssh+port+ssh.socket&restrict_sr=1)

### 5.3 Locked out: recovering a server you can't reach

> **Seen as:** `ssh: connect to host 203.0.113.10 port 22: Connection timed out` right after `ufw enable`, `Connection refused` after an sshd config edit, or your office IP banned by fail2ban · **Where:** every server, usually during a hardening change made over the same SSH session it could break · **Level:** [L2 · Mid] · **How common:** a rite of passage; r/sysadmin and Server Fault are full of "I locked myself out" threads

**Why it happens:** the change cut the path you were using: UFW's default policy denies incoming traffic and the SSH rule was missing or for the wrong port; sshd was restarted with an invalid config and did not start; fail2ban banned the address after a few failed attempts; or sudo broke (4.1) so you can log in but can't repair anything. Timed out usually means a firewall drops packets; refused means nothing listens.

**Diagnose:**

```bash
# From outside: dropped (firewall) or refused (no listener)?
nc -vz -w 5 203.0.113.10 22
# From the console once you have it:
sudo ufw status numbered
sudo sshd -t
systemctl status ssh.socket ssh.service --no-pager | grep -E 'Active|Listen'
sudo fail2ban-client status sshd | grep -A1 'Banned IP'
```

```text
nc: connect to 203.0.113.10 port 22 (tcp) timed out: Operation now in progress
Status: active
     To                         Action      From
     --                         ------      ----
[ 1] 443/tcp                    ALLOW IN    Anywhere
[ 2] 80/tcp                     ALLOW IN    Anywhere
/etc/ssh/sshd_config.d/10-local.conf line 3: Bad configuration option: PermitRootlogn
   `- Banned IP list:	198.51.100.7
```

**What the output tells you:** UFW is active with no SSH rule (packets are dropped, hence the timeout), there is a typo in the sshd drop-in that would stop sshd on its next restart, and fail2ban has banned the office address. Three independent locks.

**Fix:** first get a console that doesn't depend on SSH or the host's network.

<div class="env" data-env="onprem" markdown="1">

**On-premise console paths.** For a VM, open the hypervisor console (Proxmox noVNC or xterm.js, the VMware or Hyper-V console). For bare metal, use the BMC: iDRAC, iLO or IPMI on the management network, either through its web KVM or with serial-over-LAN, for example `ipmitool -I lanplus -H 10.0.9.21 -U admin sol activate`. Log in with a local account that has a password (keep one for exactly this), or reboot into GRUB's recovery mode for a root shell. If you are really stuck, boot with `init=/bin/bash` on the kernel line, then `mount -o remount,rw /` and repair the files.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud console paths (AWS).** Use Systems Manager Session Manager if the SSM agent and an instance profile with AmazonSSMManagedInstanceCore are in place, since it needs no inbound port. Otherwise use the EC2 Serial Console (enabled per account and region, and you need a local user with a password). As a last resort: stop the instance, detach the root volume, attach it to a rescue instance in the same availability zone, mount it, fix the files, then reattach it as the root device and start the original instance. Security groups are a separate layer: check them too, they can cause the same timeout.

</div>

Then repair from the console:

```bash
sudo ufw allow from 198.51.100.0/24 to any port 22 proto tcp
sudo sed -i 's/PermitRootlogn/PermitRootLogin/' /etc/ssh/sshd_config.d/10-local.conf
sudo sshd -t && sudo systemctl restart ssh.socket
sudo fail2ban-client set sshd unbanip 198.51.100.7
```

**Why this fix works:** an out-of-band console bypasses the broken network path, the explicit UFW rule restores SSH from your admin network only, `sshd -t` proves the config is valid before restarting, and unbanning removes the fail2ban rule. What NOT to do: `ufw disable` and forget it, or reboot repeatedly hoping a bad config fixes itself.

**Prevent it:** before risky changes, start a dead-man switch that undoes them unless you cancel it, for example `sudo systemd-run --on-active=10min --unit=undo-fw /usr/sbin/ufw disable` (cancel with `sudo systemctl stop undo-fw.timer` once a new session works); always run `sshd -t` before restarting; whitelist admin networks in fail2ban's ignoreip; keep the BMC on a separate management network and SSM installed on every cloud instance.

**Next step:** [SSH & remote access: AWS alternatives when SSH is blocked](09-ssh-remote-access.md) · [Users, permissions & security](10-users-permissions-security.md) · [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Configure Packet Filtering (Firewall) ([notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [Ubuntu Discourse: SSHd socket-based activation, lockout reports](https://discourse.ubuntu.com/t/sshd-now-uses-socket-based-activation-ubuntu-22-10-and-later/30189?page=2) · Search: [Server Fault](https://serverfault.com/search?q=locked+out+ssh+ufw+enable) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=locked+myself+out+ssh+firewall&restrict_sr=1) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=locked+out+ec2+ssh+serial+console&restrict_sr=1)

## 6. Memory, swap and OOM

Linux uses free memory for cache on purpose, so "free" is almost always low and that is fine. Trouble starts when the working set no longer fits: either the kernel kills something (OOM) or it spends its time reclaiming pages (thrashing), and the second is often worse because nothing tells you.

### 6.1 OOM killer took the database

> **Seen as:** a process vanished; `systemctl status` says `A process of this unit has been killed by the OOM killer.` and `Main process exited, code=killed, status=9/KILL`; the kernel log has `Out of memory: Killed process 2291 (java)`; a container exits with code 137 and `OOMKilled: true` · **Where:** small VMs without swap, Docker hosts without memory limits, JVMs and databases sized for a bigger machine · **Level:** [L2 · Mid] · **How common:** one of the most frequent production incidents; countless guides and postmortems

**Why it happens:** when RAM and swap are exhausted and nothing can be reclaimed, the kernel picks the process with the highest oom_score (mostly its share of memory, adjusted by oom_score_adj) and kills it. That is often the biggest process, such as the database or the JVM, not the one that is leaking. A second kind of OOM happens inside a cgroup: a container with `--memory 512m` or a unit with MemoryMax= is killed when it hits its own limit, even if the host has free RAM. The kernel log tells the two apart.

**Diagnose:**

```bash
journalctl -k -b --no-pager | grep -iE 'invoked oom-killer|oom-kill:|Killed process' | tail -4
free -h
ps -eo pid,rss,comm --sort=-rss | head -6
systemctl show postgresql@16-main -p MemoryMax -p MemoryCurrent -p OOMScoreAdjust
docker inspect -f '{{.Name}} OOMKilled={{.State.OOMKilled}} limit={{.HostConfig.Memory}}' $(docker ps -aq) 2>/dev/null | grep 'OOMKilled=true'
```

```text
kernel: java invoked oom-killer: gfp_mask=0x140cca(GFP_HIGHUSER_MOVABLE|__GFP_COMP), order=0, oom_score_adj=0
kernel: oom-kill:constraint=CONSTRAINT_NONE,nodemask=(null),cpuset=/,mems_allowed=0,global_oom,task_memcg=/system.slice/postgresql@16-main.service,task=postgres,pid=1874,uid=114
kernel: Out of memory: Killed process 1874 (postgres) total-vm:4412880kB, anon-rss:1630220kB, file-rss:0kB, shmem-rss:812004kB, UID:114 pgtables:5144kB oom_score_adj:0
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       3.5Gi       118Mi       812Mi       401Mi       142Mi
Swap:             0B          0B          0B
   PID   RSS COMMAND
  2291 2048120 java
MemoryMax=infinity
MemoryCurrent=21430272
OOMScoreAdjust=0
```

**What the output tells you:** CONSTRAINT_NONE and global_oom mean the whole machine ran out (a cgroup limit would show CONSTRAINT_MEMCG). Java triggered it while growing to 2 GB, but Postgres was killed because it had the higher score. There is no swap and no memory limit on either service.

**Fix:**

```bash
# 1. Cap the grower and size it to the box (container or unit)
#    JVM: -Xmx1g or -XX:MaxRAMPercentage=50 inside a container with a limit
sudo systemctl edit app.service        # [Service] MemoryHigh=1200M  MemoryMax=1500M
# 2. Protect what must survive (makes it a less attractive victim; not immune)
sudo systemctl edit postgresql@16-main.service   # [Service] OOMScoreAdjust=-500
# 3. A small swap file as a buffer against short spikes
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Why this fix works:** MemoryHigh throttles the app (it reclaims and slows down) before MemoryMax kills it within its own cgroup, so the rest of the host is unaffected; a negative oom_score_adj moves the database down the victim list; swap absorbs short spikes. What NOT to do: OOMScoreAdjust=-1000 on everything (the kernel then kills something random or panics), `vm.overcommit_memory=2` without testing (fork-heavy apps start failing), or "fixing" a container OOM by removing the limit.

**Prevent it:** set memory limits on every container and important unit, size JVM heaps and database memory (shared_buffers, work_mem times connections) against the host, alert on available memory and on OOM kills (node_exporter's node_vmstat_oom_kill), and add memory to capacity reviews.

**Next step:** [Memory: The OOM killer](04-memory.md) · [Slow system playbook](23-playbook-slow-system.md) · [Performance & observability](32-learn-performance-observability.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes · [Linux kernel docs](https://docs.kernel.org/)

**Community threads:** [Last9: Linux OOM killer scores, logs and configuration](https://last9.io/blog/understanding-the-linux-oom-killer/) · [Baeldung: Linux memory overcommitment and the OOM killer](https://www.baeldung.com/linux/memory-overcommitment-oom-killer) · [systemd issues mentioning OOM, by reactions](https://github.com/systemd/systemd/issues?q=is%3Aissue+oom+sort%3Areactions-%2B1-desc) · Search: [Server Fault](https://serverfault.com/search?q=%22out+of+memory%3A+killed+process%22+mysql+postgres) · [Stack Overflow](https://stackoverflow.com/search?q=docker+exit+code+137+OOMKilled) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=oom+killer+killed+database&restrict_sr=1)

### 6.2 Swap thrashing and kswapd at 100%

> **Seen as:** the server is alive but useless: SSH takes 30 seconds, `kswapd0` sits at the top of `top`, `vmstat` shows si and so in the thousands, and no OOM kill has happened yet; sometimes kswapd burns CPU on a host without any swap · **Where:** VMs sized too small, hosts running many containers without limits, databases with too-large caches · **Level:** [L2 · Mid] · **How common:** frequent on Linode, DigitalOcean and Arch forums; the PSI work in the kernel exists largely because of it

**Why it happens:** when the working set is larger than RAM, the kernel keeps reclaiming: it swaps out anonymous memory that is needed again a moment later, or, without swap, evicts page cache and program code that has to be read back from disk. The OOM killer only acts when reclaim fails completely, so the host can stay in this state for minutes or hours. kswapd is the kernel thread doing the reclaim; its CPU use is the symptom, not the cause.

**Diagnose:**

```bash
vmstat 1 5
cat /proc/pressure/memory
free -h; swapon --show
ps -eo pid,rss,comm --sort=-rss | head -5
cat /proc/sys/vm/swappiness
```

```text
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3 14 1981420  60112   1120  88340 3820 4410 41220  5120 9212 8811  6 31  8 55  0
 2 16 1984100  58876   1072  86210 4102 3988 43890  4380 9504 9120  5 33  6 56  0
some avg10=71.40 avg60=63.22 avg300=40.17 total=918822114
full avg10=48.93 avg60=41.05 avg300=24.61 total=601227781
```

**What the output tells you:** every second roughly 4 MB is swapped in and out, page cache is down to 86 MB, 14 to 16 processes are blocked, and memory PSI "full" says that for about half the time all non-idle tasks were stalled waiting for memory. The host needs less memory demand or more RAM; tuning won't save it.

**Fix:**

```bash
# 1. Relieve pressure now: stop or restart the biggest non-critical consumer
sudo systemctl restart worker.service
# 2. Put batch jobs and noisy services under a soft limit so they slow down instead of the host
sudo systemctl set-property worker.service MemoryHigh=800M
# 3. Kill early instead of thrashing for hours: systemd-oomd (or earlyoom) on PSI thresholds
sudo apt-get install systemd-oomd && sudo systemctl enable --now systemd-oomd
sudo systemctl edit worker.service      # [Service] ManagedOOMMemoryPressure=kill
# 4. Database hosts: prefer page cache over swapping the DB
echo 'vm.swappiness = 10' | sudo tee /etc/sysctl.d/60-swappiness.conf && sudo sysctl --system
```

**Why this fix works:** removing demand ends the reclaim loop; MemoryHigh makes the offender pay for its own reclaim; systemd-oomd watches memory pressure per cgroup and kills the offending unit long before the global OOM killer would act; lower swappiness biases reclaim towards cache. What NOT to do: `swapoff -a` during thrashing (all swapped pages must come back into RAM at once, which usually triggers the OOM killer on the wrong process), or `echo 3 > /proc/sys/vm/drop_caches` as a fix (the cache refills and the pressure returns).

**Prevent it:** alert on memory PSI (node_exporter's pressure collector) and on swap-in rate, not just on used memory; give every container a memory limit; right-size the VM based on peak working set.

**Next step:** [Memory: Who is using the memory?](04-memory.md) · [CPU & performance](03-cpu-performance.md) · [Slow system playbook](23-playbook-slow-system.md) · KodeKloud: *Fundamentals of SRE* — Performance Monitoring Deep Dive · [Brendan Gregg: Linux performance](https://www.brendangregg.com/linuxperf.html)

**Community threads:** [Linode community: High CPU from kswapd0](https://www.linode.com/community/questions/18027/high-cpu-from-kswapd0) · [Arch forums: kswapd using 100% CPU without swap](https://bbs.archlinux.org/viewtopic.php?id=144702) · Search: [Server Fault](https://serverfault.com/search?q=kswapd0+100%25+cpu+swap) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=kswapd+high+cpu+thrashing&restrict_sr=1)

## 7. Load, CPU and kernel limits

Many "the server is slow" and "the app randomly fails" tickets end at a counter: load average, file descriptors, tasks, map counts, inotify watches. Each has a different owner (the kernel, systemd, the container runtime, the app), and the fix only works at the right layer.

### 7.1 High load average, idle CPU

> **Seen as:** `load average: 38.12, 35.40, 30.02` on a 4-vCPU VM while `top` shows the CPUs mostly idle or in `wa`; an alert on load with no CPU-heavy process; `INFO: task kworker/u8:1:2211 blocked for more than 120 seconds.` in dmesg · **Where:** VMs on busy or slow storage, hosts with NFS mounts, servers doing heavy writes (backups, log bursts, database checkpoints) · **Level:** [L2 · Mid] · **How common:** a perennial confusion; Brendan Gregg's article explaining Linux load averages is one of the most-cited performance posts

**Why it happens:** on Linux the load average counts tasks that are running or waiting for a CPU plus tasks in uninterruptible sleep (D state), which mostly means waiting for disk or NFS I/O. So load measures demand on the system, not CPU use: 30 tasks stuck behind a slow disk give a load of 30 with idle CPUs. Usual causes are slow or saturated storage (a busy SAN, a failing disk, a cloud volume out of IOPS or burst credit), a dead NFS server (10.2), or a large dirty-page writeback stalling writers. When a task stays in D state for 120 seconds, the kernel prints the hung-task warning.

**Diagnose:**

```bash
uptime
vmstat 1 5                                   # r = runnable, b = blocked (D state), wa = I/O wait
ps -eo state,pid,wchan:28,comm | awk '$1=="D"' | head
iostat -xz 1 3                               # r_await / w_await latency, aqu-sz queue, %util (sample shows only these columns)
cat /proc/pressure/io
pidstat -d 1 3 | sort -k6 -n | tail -4       # which process writes the most
sudo dmesg -T | grep -i 'blocked for more than' | tail -2
```

```text
 10:42:07 up 41 days,  2:11,  2 users,  load average: 38.12, 35.40, 30.02
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1 33      0 412004  81200 2210400    0    0   120 98400 2210 3011  2  3 41 54  0
D    2211 io_schedule                  kworker/u8:1+flush-253:0
D    3120 wait_on_page_bit_common      postgres
D    3398 io_schedule                  rsync
Device  r/s     w/s   rkB/s    wkB/s  r_await w_await aqu-sz %util
sda    4.00  210.00   96.00 98112.00    41.20  856.40 178.11 100.00
some avg10=88.10 avg60=85.42 avg300=71.03 total=7211871299
full avg10=79.45 avg60=76.80 avg300=62.11 total=6022918877
```

**What the output tells you:** 33 tasks are blocked, CPUs are 41% idle with 54% I/O wait, and the disk takes 856 ms per write with a queue of 178 and 100% utilisation. An rsync backup and the kernel's flush thread are writing faster than the disk can absorb, and Postgres waits behind them. The load is a storage problem.

**Fix:**

```bash
# 1. Take pressure off now: throttle the bulk writer
sudo ionice -c3 -p 3398                    # idle I/O class; honoured by the bfq and mq-deadline schedulers, not by "none"
sudo systemctl set-property backup.service IOWriteBandwidthMax="/dev/sda 40M"
# 2. On large-RAM hosts, start writeback earlier and cap dirty data so writers don't stall
sudo tee /etc/sysctl.d/60-writeback.conf >/dev/null <<'EOF'
vm.dirty_background_bytes = 268435456
vm.dirty_bytes = 1073741824
EOF
sudo sysctl --system
# 3. Then fix capacity: faster storage tier, more IOPS, backups at night or from a replica
```

**Why this fix works:** ionice and an I/O bandwidth cap (cgroup v2) keep the bulk job from monopolising the device; byte-based dirty limits make the kernel flush in smaller, steadier chunks instead of large bursts that freeze writers. The real fix is matching storage to the workload. What NOT to do: `echo 0 > /proc/sys/kernel/hung_task_timeout_secs` (silences the warning, the stall stays), or add CPUs to a host that is waiting on disk.

**Prevent it:** alert on disk latency (await), I/O PSI and CPU saturation rather than raw load; schedule backups and batch jobs; on-prem, watch datastore latency and RAID-controller cache status (a controller that drops to write-through during a battery learn cycle causes exactly this); in the cloud, watch volume burst balance and per-instance EBS throughput limits.

**Next step:** [CPU & performance](03-cpu-performance.md) · [Storage & disk: Disk performance](01-storage-disk.md) · [Slow system playbook](23-playbook-slow-system.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Monitor Storage Performance · [Brendan Gregg: Linux load averages, solving the mystery](https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html)

**Community threads:** [Brendan Gregg: Linux load averages](https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html) · [Linux performance analysis in 60 seconds (video and checklist)](https://www.brendangregg.com/blog/2015-12-03/linux-perf-60s-video.html) · [vivani.net: task blocked for more than 120 seconds](https://vivani.net/2020/02/08/task-blocked-for-more-than-120-seconds/) · Search: [Server Fault](https://serverfault.com/search?q=high+load+average+low+cpu+iowait) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=high+load+average+idle+cpu&restrict_sr=1)

### 7.2 Too many open files

> **Seen as:** nginx `accept4() failed (24: Too many open files)`, Java `java.net.SocketException: Too many open files`, Go `accept tcp [::]:8080: accept4: too many open files; retrying in 1s`, Elasticsearch, Prometheus or Loki failing under load · **Where:** busy proxies and APIs, databases and proxies with many connections, containers after a Docker or containerd upgrade · **Level:** [L2 · Mid] · **How common:** extremely common; it also took part in GitHub's February 2020 incidents, when the intended LimitNOFILE for ProxySQL was silently capped far lower

**Why it happens:** every socket and file is a file descriptor, limited per process by RLIMIT_NOFILE. Since systemd 240 services get a soft limit of 1024 and a hard limit of 524288, and the program must raise its own soft limit (Go does this automatically since 1.19; many others don't). /etc/security/limits.conf is applied by PAM to login sessions only, so it does nothing for systemd services. Containers inherit their limits from the runtime: Docker and containerd removed `LimitNOFILE=infinity` from their units (moby#45534, containerd#8924), so after an upgrade containers see 1024:524288 instead of a huge number. Values above fs.nr_open (1048576 on Ubuntu 24.04, whose systemd build leaves the kernel default alone; distributions that keep upstream systemd's default raise it to 1073741816 at boot, so check yours with `sysctl fs.nr_open`) are rejected or capped. And sometimes the limit is fine and the app leaks descriptors.

**Diagnose:**

```bash
PID=$(pgrep -f 'nginx: worker process' | head -1)    # a worker holds the client sockets, not the master
grep 'open files' /proc/$PID/limits
sudo ls /proc/$PID/fd | wc -l
systemctl show nginx -p LimitNOFILE -p LimitNOFILESoft
sysctl fs.nr_open fs.file-nr
docker exec CONTAINER sh -c 'ulimit -Sn; ulimit -Hn'
# Leak or load? What kind of descriptors, and does the count keep growing?
sudo ls -l /proc/$PID/fd | awk '{print $NF}' | sed 's/:.*//' | sort | uniq -c | sort -n | tail -3
```

```text
Max open files            1024                 524288               files
1019
LimitNOFILE=524288
LimitNOFILESoft=1024
fs.nr_open = 1048576
fs.file-nr = 21344	0	9223372036854775807
1024
524288
     12 /var/log/nginx/access.log
     31 anon_inode
    976 socket
```

**What the output tells you:** the nginx worker runs with a soft limit of 1024 and already hold 1019 descriptors, almost all sockets, so this is load, not a leak (a leak shows a count that grows without bound, often of one file or of sockets in CLOSE_WAIT). The system-wide counter (file-nr) is nowhere near its maximum, so the kernel-wide limit is not the problem.

**Fix:**

```bash
# systemd service: raise soft and hard together in a drop-in
sudo systemctl edit nginx
#   [Service]
#   LimitNOFILE=65536
sudo systemctl restart nginx
# nginx also needs to be told (worker_rlimit_nofile >= 2 x worker_connections)
#   worker_rlimit_nofile 65536;   events { worker_connections 16384; }
# Containers: per service in compose, or a daemon-wide default
#   ulimits:
#     nofile: { soft: 65536, hard: 65536 }
```

**Why this fix works:** LimitNOFILE in the unit sets the limits the process actually starts with, which limits.conf never touches; nginx's own directive makes workers use them; compose ulimits set the container's rlimit directly instead of inheriting the runtime's. What NOT to do: `LimitNOFILE=infinity` (some programs loop over every possible descriptor at start and become very slow, which is why Docker and containerd removed it), values above fs.nr_open, or raising limits to hide a leak.

**Prevent it:** set LimitNOFILE explicitly for every network-heavy service in your baseline, export descriptor usage (process_open_fds and process_max_fds in most exporters) and alert at 80%, and read runtime release notes when Docker or containerd changes major versions.

**Next step:** [Kernel & system: Resource limits](13-kernel-system.md) · [Processes](05-processes.md) · [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Change Kernel Runtime Parameters · [systemd man pages (systemd.exec: LimitNOFILE)](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [GitHub: February 2020 service disruptions, post-incident analysis](https://github.blog/news-insights/company-news/february-service-disruptions-post-incident-analysis/) · [moby/moby#45060: container ulimits inherited from containerd](https://github.com/moby/moby/issues/45060) · [moby/moby#45534: normalize RLIMIT_NOFILE](https://github.com/moby/moby/pull/45534) · [containerd#8924: remove LimitNOFILE from containerd.service](https://github.com/containerd/containerd/pull/8924) · Search: [Server Fault](https://serverfault.com/search?q=%22too+many+open+files%22+systemd+LimitNOFILE+limits.conf) · [Stack Overflow](https://stackoverflow.com/search?q=%22too+many+open+files%22+systemd+service+ulimit) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=too+many+open+files+LimitNOFILE&restrict_sr=1)

### 7.3 fork: Resource temporarily unavailable

> **Seen as:** `bash: fork: retry: Resource temporarily unavailable` in your shell, Java `java.lang.OutOfMemoryError: unable to create native thread`, Go `runtime/cgo: pthread_create failed: Resource temporarily unavailable`, and in the kernel log `cgroup: fork rejected by pids controller in /system.slice/app.service` · **Where:** thread-heavy apps (Java, Elasticsearch, CI runners), users running many processes, containers with a pids limit · **Level:** [L2 · Mid] · **How common:** regular in vendor knowledge bases (SUSE, Red Hat) and project issue trackers such as NixOS/nix#3717

**Why it happens:** threads count as tasks, and four different ceilings can refuse a new one: the unit's TasksMax (systemd's default is 15% of the lowest of kernel.pid_max, kernel.threads-max and the root cgroup's pids limit: 4915 on a VM with about 4 GB of RAM), the user slice's TasksMax for logged-in users, the per-user process limit (`ulimit -u`, RLIMIT_NPROC) for login sessions, or the kernel-wide kernel.pid_max and kernel.threads-max. Containers add their own `--pids-limit`. Very often the real cause is a thread or process leak that eventually hits whichever limit is lowest.

**Diagnose:**

```bash
journalctl -k -b | grep -i 'fork rejected' | tail -2
systemctl show app -p TasksMax -p TasksCurrent
systemctl show user-1001.slice -p TasksMax -p TasksCurrent
ulimit -u
sysctl kernel.pid_max kernel.threads-max
ps -eo nlwp,pid,comm --sort=-nlwp | head -4      # threads per process
```

```text
kernel: cgroup: fork rejected by pids controller in /system.slice/app.service
TasksMax=4915
TasksCurrent=4915
TasksMax=10813
TasksCurrent=41
16384
kernel.pid_max = 4194304
kernel.threads-max = 32768
NLWP     PID COMMAND
 4902   7731 java
  204   1022 dockerd
```

**What the output tells you:** app.service hit its TasksMax of 4915, nearly all of them threads of one Java process (4915 is 15% of threads-max, and the user slice's 10813 is logind's 33%). The kernel-wide limits are much higher. Before raising anything, ask whether 4900 threads is normal for this app (usually it is a pool or connection leak).

**Fix:**

```bash
# Find out whether the thread count grows over time (leak) or is steady (sizing)
for i in 1 2 3; do ps -o nlwp= -p 7731; sleep 60; done
# If the need is real: raise the unit's limit explicitly
sudo systemctl edit app.service            # [Service] TasksMax=16384
sudo systemctl restart app
# Containers: set a sane explicit limit rather than none
#   docker run --pids-limit 4096 ...   (compose: pids_limit: 4096)
```

**Why this fix works:** TasksMax is enforced by the cgroup pids controller, so a drop-in raises exactly the limit that rejected the fork; measuring growth first separates a leak (fix the app or its pool settings) from a legitimate need. What NOT to do: TasksMax=infinity on every unit (one runaway service or fork bomb can then exhaust the whole system's PIDs), or raising ulimit -u in limits.conf for a systemd service (it doesn't apply, see 7.2).

**Prevent it:** monitor tasks per unit (TasksCurrent via the systemd exporter) and threads per process, set explicit pids limits on containers, and review thread pool sizes when connection counts grow.

**Next step:** [Processes](05-processes.md) · [Kernel & system: Resource limits](13-kernel-system.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes · [systemd man pages (systemd.resource-control: TasksMax)](https://www.freedesktop.org/software/systemd/man/latest/)

**Community threads:** [SUSE KB: error fork: Resource temporarily unavailable](https://www.suse.com/support/kb/doc/?id=000020612) · [NixOS/nix#3717: fork: retry: resource temporarily unavailable](https://github.com/NixOS/nix/issues/3717) · Search: [Server Fault](https://serverfault.com/search?q=%22fork%3A+retry%3A+resource+temporarily+unavailable%22+TasksMax) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=fork+resource+temporarily+unavailable&restrict_sr=1)

### 7.4 sysctl and limits lost after reboot

> **Seen as:** the search node worked until the reboot, then `max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]`; `sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-iptables: No such file or directory` on a Kubernetes node; `ENOSPC: System limit for number of file watchers reached` from a log shipper or build tool · **Where:** OpenSearch, Elasticsearch and the Wazuh indexer, Kubernetes nodes, hosts running Promtail, Alloy or file-watching dev tools · **Level:** [L2 · Mid] · **How common:** a classic first-reboot surprise; the vm.max_map_count error is one of the most frequent search-cluster startup failures

**Why it happens:** `sysctl -w` changes only the running kernel. Persistent values must live in /etc/sysctl.d/*.conf, which systemd-sysctl applies at boot in file-name order across /usr/lib/sysctl.d, /run/sysctl.d and /etc/sysctl.d, so a later file can silently override yours. Keys that belong to a kernel module (net.bridge.* needs br_netfilter) fail at boot if the module loads after systemd-sysctl. On RHEL, a tuned profile can also set the same keys. inotify watch limits (fs.inotify.max_user_watches) are the same story: kernels before 5.11 default to 8192, and current kernels scale the default with RAM (roughly 1% of memory, about 18 000 to 20 000 on a 2 GB VM), which log shippers and file-watching tools still exhaust quickly.

**Diagnose:**

```bash
sysctl vm.max_map_count net.ipv4.ip_forward fs.inotify.max_user_watches
# Every sysctl file in the order systemd applies them, with the line that sets the key
systemd-analyze cat-config sysctl.d | grep -nE '^# /|max_map_count|ip_forward'
journalctl -b -u systemd-sysctl --no-pager | tail -3
lsmod | grep -c br_netfilter
tuned-adm active 2>/dev/null
```

```text
vm.max_map_count = 65530
net.ipv4.ip_forward = 1
fs.inotify.max_user_watches = 18563
14:# /usr/lib/sysctl.d/50-default.conf
52:# /etc/sysctl.d/99-sysctl.conf
80:#net.ipv4.ip_forward=1
Oct 04 07:12:03 web1 systemd-sysctl[402]: Couldn't write '1' to 'net/bridge/bridge-nf-call-iptables', ignoring: No such file or directory
0
```

**What the output tells you:** no sysctl file sets vm.max_map_count at all, so the earlier fix was a `sysctl -w` that died with the reboot. ip_forward is 1 only because Docker turns it on when it starts (the only file line is the commented-out example in sysctl.conf). The bridge key failed at boot because br_netfilter was not loaded yet, and the inotify limit is still the small RAM-based kernel default.

**Fix:**

```bash
# Clear, numbered files: later numbers win
sudo tee /etc/sysctl.d/90-search.conf >/dev/null <<'EOF'
vm.max_map_count = 262144
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024
EOF
# Load modules at boot before their sysctls are applied
echo br_netfilter | sudo tee /etc/modules-load.d/k8s.conf
sudo tee /etc/sysctl.d/91-k8s.conf >/dev/null <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo modprobe br_netfilter && sudo sysctl --system
```

**Why this fix works:** numbered files make the order explicit, `sysctl --system` applies them exactly as boot will (so you see errors now, not after the next reboot), and modules-load.d loads br_netfilter early enough for its keys to exist. What NOT to do: put `sysctl -w` lines in rc.local or a cron @reboot job, or edit /usr/lib/sysctl.d files that packages overwrite.

**Prevent it:** manage sysctl files in config management, reboot every new host once before it takes traffic (a "reboot test" catches this whole class of problems), and check the effective values in your monitoring (node_exporter can export selected sysctls).

**Next step:** [Kernel & system: Kernel parameters](13-kernel-system.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) (indexer requirements) · [Learn Kubernetes](31-learn-kubernetes.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Change Kernel Runtime Parameters · [Linux kernel docs](https://docs.kernel.org/)

**Community threads:** [GitLab issue 434329: Vite on Linux, number of file watchers reached](https://gitlab.com/gitlab-org/gitlab/-/issues/434329) · [Gentoo forums: System limit for number of file watchers reached](https://forums.gentoo.org/viewtopic-p-8521685.html?sid=6b4e43d6f34efe7a18ce6ab4802b0a97) · Search: [Server Fault](https://serverfault.com/search?q=sysctl+setting+lost+after+reboot+sysctl.d) · [Stack Overflow](https://stackoverflow.com/search?q=vm.max_map_count+65530+too+low+reboot) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=bridge-nf-call-iptables+no+such+file&restrict_sr=1)

## 8. Time and clocks

Time is invisible until it is wrong. A few minutes of drift breaks TLS, apt, TOTP, Kerberos, JWTs and log correlation; a clock that jumps breaks software that assumes time only moves forward. Time sync is a fleet design question, not a per-host setting.

### 8.1 Clock drift: chrony won't correct it

> **Seen as:** `chronyc tracking` shows `System time : 312.441253662 seconds slow of NTP time`; `timedatectl` says `System clock synchronized: no`; apt prints `Release file for http://archive.ubuntu.com/ubuntu/dists/noble-updates/InRelease is not valid yet (invalid for another 5min 12s)`; TLS clients complain `certificate is not yet valid`; TOTP codes fail · **Where:** VMs restored from snapshots or resumed after suspend, on-prem networks that block outbound UDP 123, hosts running two time daemons · **Level:** [L2 · Mid] · **How common:** common on VPS and VM fleets; chrony's own docs and vendor guides cover it repeatedly

**Why it happens:** Ubuntu up to 24.04 uses systemd-timesyncd by default and newer Ubuntu releases and RHEL use chrony. chrony's default `makestep 1 3` steps the clock only during the first three updates after it starts; later it only slews, by default at most about 83 ms per second (maxslewrate 83333 ppm), so a five-minute error after a VM resume takes an hour or more to disappear while TLS, apt and tokens see the wrong time. Other causes: no reachable time source (UDP 123 blocked, only internet pools configured on an isolated network), two daemons fighting (timesyncd and chrony, or chrony plus the hypervisor tools' periodic time sync), and a wrong hardware clock after a power loss.

**Diagnose:**

```bash
timedatectl status | grep -E 'Local time|synchronized|NTP service'
systemctl is-active systemd-timesyncd chrony chronyd 2>/dev/null
chronyc tracking | grep -E 'Reference ID|System time|Leap status'
chronyc -n sources -v | tail -5
```

```text
               Local time: Sat 2026-10-04 11:02:41 UTC
System clock synchronized: no
              NTP service: active
inactive
active
inactive
Reference ID    : 00000000 ()
System time     : 0.000000000 seconds fast of NTP time
Leap status     : Not synchronised
MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^? 10.0.1.2                      0   6     0     -     +0ns[   +0ns] +/-    0ns
^? 10.0.1.3                      0   6     0     -     +0ns[   +0ns] +/-    0ns
```

**What the output tells you:** chrony runs, but both configured servers show `^?` with Reach 0: it has never received an answer, so it can't correct anything. It doesn't even know the offset: with Reference ID 00000000, "System time" stays at 0 although apt and TLS show the clock is minutes off (the "312 seconds slow" line appears only once a source answers). This is a network or server problem (UDP 123 blocked, or the internal NTP servers are down), not a chrony setting.

**Fix:** make a time source reachable, then let chrony step once.

<div class="env" data-env="onprem" markdown="1">

**On-premise:** run two or more internal time servers (chrony on small VMs, or the core switches or AD domain controllers) that sync to a GPS appliance or public pools, allow UDP 123 from all server VLANs to them, and point every host at them (`server 10.0.1.2 iburst` and `server 10.0.1.3 iburst` in /etc/chrony/chrony.conf, or `NTP=` in /etc/systemd/timesyncd.conf). Disable the hypervisor's periodic time sync for guests that run chrony (for VMware Tools: `vmware-toolbox-cmd timesync disable`) so only one mechanism adjusts the clock.

</div>

<div class="env" data-env="cloud" markdown="1">

**AWS:** use the Amazon Time Sync Service, reachable from every instance at the link-local address 169.254.169.123 (IPv6 fd00:ec2::123) without any security group rule: `server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4` in chrony.conf. Amazon Linux and recent Ubuntu AMIs already use it. It applies leap smearing, so don't mix it with non-smeared public servers (see 8.2).

</div>

```bash
sudo systemctl disable --now systemd-timesyncd     # only one daemon
sudo systemctl restart chrony
chronyc -n sources                                 # wait for ^* (selected source) and Reach 377
sudo chronyc makestep                              # step the remaining offset once, now
sudo hwclock --systohc                             # fix the hardware clock too
```

**Why this fix works:** chrony can only correct against a source it can reach; once one is selected, `makestep` removes the big offset in one step and normal slewing keeps it small afterwards. What NOT to do: `date -s` by hand on a running server (the next sync fights it, and a backwards jump breaks running software), or `makestep 1 -1` everywhere (it allows steps at any time, including backwards steps under load).

**Prevent it:** alert on clock offset and sync status (node_exporter's timex collector: node_timex_offset_seconds above 0.1 and node_timex_sync_status), open UDP 123 to the time servers in the firewall baseline, and include "check time sync" in the VM restore runbook.

**Next step:** [Time & NTP](12-time-ntp.md) · [Web, HTTP & TLS](18-web-http-tls.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Set and Synchronize System Time · [chrony documentation: chronyc](https://chrony-project.org/doc/4.3/chronyc.html)

**Community threads:** [chrony docs: chronyc (tracking, sources, makestep)](https://chrony-project.org/doc/4.3/chronyc.html) · Search: [Server Fault](https://serverfault.com/search?q=chrony+makestep+large+offset+not+syncing) · [Stack Overflow](https://stackoverflow.com/search?q=apt+%22release+file%22+%22is+not+valid+yet%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=chrony+clock+drift+vm&restrict_sr=1)

### 8.2 Time jumps that break TLS, apt and clusters

> **Seen as:** after a VM snapshot revert or a long power-off, chronyd logs `System clock wrong by -3602.118 seconds` and `System clock was stepped by -3602.118 seconds`, and then: JWTs rejected as "issued in the future", etcd or Consul leader elections, Kafka sessions expiring, cron jobs skipped or run twice, logs out of order; historically, the 2012 leap second sent Java and MySQL processes to 100% CPU at Reddit, LinkedIn, Mozilla and airline reservation systems · **Where:** clusters and distributed systems, VM platforms with snapshot reverts, fleets that mix time sources · **Level:** [L4 · Senior/Lead] · **How common:** rare per host but fleet-wide when it happens; the leap-second incident is a standard postmortem example (LWN, Hacker News, danluu's collection)

**Why it happens:** software assumes wall-clock time moves forward smoothly. A step (forwards or backwards) violates that: timeouts computed from wall time fire early or never, certificates and tokens look not-yet-valid, and consensus systems see leases expire. In 2012 the leap-second insertion hit a kernel timer bug, so timers expired early and applications sleeping in loops spun on the CPU. Today large providers smear leap seconds over many hours, but a fleet that mixes smeared and unsmeared sources sees servers disagree by up to a second during a leap event.

**Diagnose:**

```bash
journalctl -b --no-pager | grep -iE 'clock (was stepped|wrong)|time has been changed|Selected source' | tail -4
chronyc tracking | grep -E 'Reference ID|Leap status|Last offset'
chronyc -n sources | awk 'NR<3 || /^\^/'
# Which hosts disagree? Compare offsets fleet-wide from your metrics
#   PromQL: max by (instance) (abs(node_timex_offset_seconds)) > 0.05
```

```text
Oct 04 08:14:02 db1 chronyd[702]: Selected source 10.0.1.2
Oct 04 08:14:02 db1 chronyd[702]: System clock wrong by -3602.118342 seconds
Oct 04 08:14:02 db1 chronyd[702]: System clock was stepped by -3602.118342 seconds
Oct 04 08:14:02 db1 systemd[1]: Time has been changed
Reference ID    : 0A000102 (10.0.1.2)
Leap status     : Normal
Last offset     : -0.000021113
```

**What the output tells you:** db1 came back an hour fast (restored from a snapshot or with a wrong RTC) and chrony stepped it back by one hour at boot, after services had already started with the wrong time. Anything that cached timestamps or leases during that window is suspect.

**Fix:**

```bash
# Make time-sensitive services wait for a synchronised clock at boot
sudo systemctl enable chrony-wait.service          # RHEL: chrony-wait; timesyncd hosts: systemd-time-wait-sync
sudo systemctl edit etcd.service
#   [Unit]
#   After=time-sync.target
#   Wants=time-sync.target
# chrony: step only at startup, slew afterwards (the default; keep it)
grep -E '^makestep' /etc/chrony/chrony.conf        # makestep 1 3
```

Fleet design (the senior part): one source hierarchy for every host (internal servers or the cloud provider's service, never a mix of smeared and unsmeared sources), a written leap-second policy, a VM-restore procedure that syncs time before services start, and applications that measure durations with a monotonic clock rather than wall time.

**Why this fix works:** ordering services after time-sync.target (with chrony-wait or systemd-time-wait-sync providing it) means they start only once the clock is right, so the one-time boot step happens before anyone depends on the time; a single consistent source hierarchy removes disagreement between hosts. What NOT to do: disable stepping entirely on VMs (a restored VM then runs hours off for a long time), or "fix" a cluster split by restarting nodes one by one without first checking their clocks.

**Prevent it:** alert on offset and on step events (the "System clock was stepped" log line in Loki or Wazuh), test snapshot-revert procedures, and include time in your incident checklist for any distributed-system flap.

**Next step:** [Time & NTP](12-time-ntp.md) · [Senior architecture](39-learn-senior-architecture.md) · [DevOps day to day](52-devops-day-to-day.md) · KodeKloud: *Fundamentals of SRE* — Root Cause Analysis ([notes](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page)) · [chrony documentation](https://chrony-project.org/doc/4.3/chronyc.html)

**Community threads:** [LWN: Leaping seconds and looping servers](https://lwn.net/Articles/504744/) · [Hacker News: critical Linux bug leads to 100% CPU (leap second)](https://news.ycombinator.com/item?id=4188412) · [danluu/post-mortems](https://github.com/danluu/post-mortems) · Search: [Server Fault](https://serverfault.com/search?q=leap+second+smear+chrony+mixed+sources) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=clock+jump+snapshot+revert+cluster&restrict_sr=1)

## 9. Growing disks, LVM and boot failures

Storage layout decisions made at install time come back months later: a root volume that is half the disk, a data disk in fstab that disappears, a kernel update that can't find its root filesystem. These entries are where on-prem and cloud differ the most, because the first step happens in the hypervisor or the cloud API, not in Linux.

### 9.1 Disk grown, filesystem still small

> **Seen as:** "I gave the VM 100 GB but `df -h /` shows 48G", or the EBS volume was resized to 100 GiB and the filesystem still reports 20G · **Where:** Ubuntu Server installs with the default LVM layout, VMs whose virtual disk was enlarged in Proxmox or VMware, cloud volumes after modify-volume · **Level:** [L1 · Junior] · **How common:** one of the most asked Ubuntu Server questions; Ubuntu Discourse threads and AWS's own knowledge-center article exist because of it

**Why it happens:** storage is a stack (disk, partition, LVM physical volume, volume group, logical volume, filesystem) and each layer must be grown on its own. The Ubuntu Server installer's default LVM layout deliberately gives ubuntu-lv only part of the volume group (roughly half on mid-size disks) and leaves the rest free for snapshots and growth. When the hypervisor or cloud enlarges the disk, Linux sees a bigger device, but the partition, PV, LV and filesystem keep their old sizes until you grow them.

**Diagnose:**

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
sudo pvs; sudo vgs; sudo lvs
df -hT /
```

```text
NAME                      SIZE TYPE FSTYPE      MOUNTPOINTS
sda                       100G disk
├─sda1                      1M part
├─sda2                      2G part ext4        /boot
└─sda3                     48G part LVM2_member
  └─ubuntu--vg-ubuntu--lv  48G lvm  ext4        /
  PV         VG        Fmt  Attr PSize  PFree
  /dev/sda3  ubuntu-vg lvm2 a--  47.99g    0
  VG        #PV #LV #SN Attr   VSize  VFree
  ubuntu-vg   1   1   0 wz--n- 47.99g    0
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   47G   44G  1.3G  98% /
```

**What the output tells you:** the disk is already 100 GB, but partition sda3 is still 48 GB and the VG has no free space. You need to grow the partition, then the PV, then the LV and the filesystem. (On a fresh install where `vgs` shows VFree of about 50 GB, you only need the last step.)

**Fix:** first make sure the virtual disk itself is bigger, then grow each layer.

<div class="env" data-env="onprem" markdown="1">

**On-premise:** grow the virtual disk in the hypervisor (Proxmox: `qm resize 101 scsi0 +50G` on the host, or the VM's Hardware tab; VMware: edit the VM's disk size). If the guest still shows the old size, rescan the device: `echo 1 | sudo tee /sys/class/block/sda/device/rescan`. On bare metal you add a new disk instead and extend the volume group with it: `sudo pvcreate /dev/sdb && sudo vgextend ubuntu-vg /dev/sdb`.

</div>

<div class="env" data-env="cloud" markdown="1">

**AWS:** grow the volume with `aws ec2 modify-volume --volume-id vol-0abc123def4567890 --size 100` (or the console) and wait until the modification state is optimizing or completed; since January 2026 the old six-hour cooldown is gone, and you can modify the same volume up to four times in a rolling 24 hours, each once the previous modification has completed. Current Nitro instances show the disk as /dev/nvme0n1. Ubuntu and Amazon Linux AMIs usually have no LVM: after `sudo growpart /dev/nvme0n1 1`, grow the filesystem with `sudo resize2fs /dev/nvme0n1p1` (ext4) or `sudo xfs_growfs -d /` (XFS). cloud-init also grows the root partition automatically at the next boot.

</div>

```bash
# LVM layout (the Ubuntu Server default), after the disk itself is bigger:
sudo growpart /dev/sda 3                                   # grow partition 3 to the end of the disk
sudo pvresize /dev/sda3                                    # tell LVM the PV is bigger
sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv     # -r also grows ext4/XFS online
df -h /
```

**Why this fix works:** growpart moves the partition's end without touching its start or data, pvresize and lvextend hand the space up the stack, and `-r` calls resize2fs or xfs_growfs so the filesystem grows online without unmounting. What NOT to do: delete and recreate partitions with fdisk unless you are certain of the start sector, try to shrink XFS (impossible), or run lvreduce without shrinking the filesystem first (instant data loss).

**Prevent it:** decide the LV layout at install time (or keep some VG space free on purpose and document it), alert at 80%, and write the grow procedure for your platform into a runbook so it is a five-minute task.

**Next step:** [Storage & disk: LVM](01-storage-disk.md) · [Learn Linux: Storage and filesystems](27-learn-linux.md) · [Learn AWS](36-learn-cloud-aws.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage (LVM) · [AWS: Extend the file system after resizing an EBS volume](https://docs.aws.amazon.com/ebs/latest/userguide/recognize-expanded-volume-linux.html)

**Community threads:** [Ubuntu Community Hub: How to expand disk space](https://discourse.ubuntu.com/t/how-to-expand-disk-space/68505) · [AWS re:Post: extend a Linux file system for an EBS volume](https://repost.aws/knowledge-center/extend-linux-file-system) · Search: [Server Fault](https://serverfault.com/search?q=ubuntu-lv+only+half+disk+lvextend) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=resize+disk+ubuntu+lvm+growpart&restrict_sr=1) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=ebs+resized+filesystem+still+small+growpart&restrict_sr=1)

### 9.2 Emergency mode after an fstab change

> **Seen as:** the console says `You are in emergency mode. After logging in, type "journalctl -xb" to view system logs ...`, the journal shows `Timed out waiting for device /dev/disk/by-uuid/9c2e4f1a-...` and `Dependency failed for /data.`; on Ubuntu, often followed by `Cannot open access to console, the root account is locked.` · **Where:** a data disk that was removed, replaced or detached, a typo in a new fstab line, an NFS mount without network options, /dev/sdX names that changed order · **Level:** [L2 · Mid] · **How common:** a classic; Microsoft and Google publish dedicated "VM won't boot because of fstab" guides, and forum threads appear weekly

**Why it happens:** systemd turns every fstab line into a mount unit that local-fs.target (or remote-fs.target) requires. If the device never appears (wrong UUID, disk gone, /dev/sdb is now a different disk), the mount fails after the device timeout and boot stops in emergency mode. Ubuntu's root account has no password, so the emergency shell can't be opened and you need another way in.

**Diagnose:**

```bash
# From the emergency shell (or the recovery path in the Fix): what failed?
journalctl -xb -p err --no-pager | head -12
systemctl --failed --no-pager
lsblk -o NAME,FSTYPE,UUID,MOUNTPOINTS
findmnt --verify --verbose
```

```text
Oct 04 07:31:12 web1 systemd[1]: dev-disk-by\x2duuid-9c2e4f1a\x2d7b3c\x2d4d8e\x2da1f0\x2d2b6c9d0e1f22.device: Job dev-disk-by\x2duuid-9c2e4f1a....device/start timed out.
Oct 04 07:31:12 web1 systemd[1]: Timed out waiting for device dev-disk-by\x2duuid-9c2e4f1a\x2d7b3c\x2d4d8e\x2da1f0\x2d2b6c9d0e1f22.device - /dev/disk/by-uuid/9c2e4f1a-7b3c-4d8e-a1f0-2b6c9d0e1f22.
Oct 04 07:31:12 web1 systemd[1]: Dependency failed for data.mount - /data.
Oct 04 07:31:12 web1 systemd[1]: Dependency failed for local-fs.target - Local File Systems.
NAME   FSTYPE      UUID                                 MOUNTPOINTS
sda
├─sda2 ext4        0d1e6b4c-2f8a-4c1e-9d3b-7a5e8f9c1b20 /boot
└─sda3 LVM2_member 7Hq2Lx-...                           
sdb    ext4        51a7c3e9-8d2f-4b6a-9e1c-3f0d7b8a2c64
/data
   [E] unreachable on boot required source: UUID=9c2e4f1a-7b3c-4d8e-a1f0-2b6c9d0e1f22
```

**What the output tells you:** /data points at a UUID that no longer exists; the data disk sdb was replaced (or reformatted) and has a new UUID. Because the mount is required, all of local-fs.target failed.

**Fix:** get a root shell first. If the emergency shell refuses (locked root), reboot, press e on the GRUB entry, add `systemd.setenv=SYSTEMD_SULOGIN_FORCE=1` (or, as a last resort, `init=/bin/bash`) to the linux line and boot with Ctrl-X. Then:

```bash
mount -o remount,rw /
cp /etc/fstab /etc/fstab.bak-$(date +%F)
# Point the line at the right UUID, and make non-critical data mounts non-blocking
sed -i 's/UUID=9c2e4f1a-7b3c-4d8e-a1f0-2b6c9d0e1f22/UUID=51a7c3e9-8d2f-4b6a-9e1c-3f0d7b8a2c64/' /etc/fstab
#   UUID=51a7c3e9-...  /data  ext4  defaults,nofail,x-systemd.device-timeout=10s  0 2
#   10.0.1.40:/srv/shared /mnt/shared nfs4 _netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30 0 0
systemctl daemon-reload
findmnt --verify && mount -a
systemctl default        # continue booting (or reboot)
```

**Why this fix works:** the corrected UUID lets the mount succeed; `nofail` makes a missing data disk a warning instead of a boot failure, the device timeout shortens the wait, and `_netdev` plus automount keep network filesystems out of the local boot path entirely. What NOT to do: comment out the root or /boot line "to get it booting", or use /dev/sdX names in fstab (they can change between boots).

**Prevent it:** after every fstab edit, run `findmnt --verify` and `mount -a` before rebooting; use UUID= or LABEL=; mark every non-root data mount nofail; keep console access ready for reboots that include storage changes. In the cloud, the serial console is the only way to see this screen (entry 5.3).

**Next step:** [Storage & disk: Block devices & partitions](01-storage-disk.md) · [Learn Linux: The boot process and recovery](27-learn-linux.md) · [Services & systemd: Boot problems](07-services-systemd.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage (mount options) · [systemd.mount](https://www.freedesktop.org/software/systemd/man/latest/systemd.mount.html)

**Community threads:** [Microsoft Learn: troubleshoot Linux VM boot issues due to fstab errors](https://learn.microsoft.com/en-US/troubleshoot/azure/virtual-machines/linux/linux-virtual-machine-cannot-start-fstab-errors) · [ArchWiki: fstab](https://wiki.archlinux.org/title/Fstab) · [systemd, fstab and nofail (Nelson's log)](https://nelsonslog.wordpress.com/2022/08/16/systemd-fstab-and-nofail/) · Search: [Server Fault](https://serverfault.com/search?q=emergency+mode+fstab+%22dependency+failed%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=emergency+mode+fstab+boot&restrict_sr=1)

### 9.3 Kernel panic: unable to mount root after an update

> **Seen as:** `Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)` right after rebooting into a new kernel; or `Gave up waiting for root file system device` and a BusyBox `(initramfs)` prompt (RHEL: a dracut emergency shell after `dracut-initqueue` timeouts) · **Where:** hosts where /boot filled up or the upgrade was interrupted, VMs whose disk controller type changed, cloned disks · **Level:** [L3 · Senior] · **How common:** regular in Microsoft Q&A, distro forums and DEV write-ups; often the second act of entry 1.5

**Why it happens:** the kernel needs its initramfs to load the storage drivers and assemble LVM or RAID before it can mount root. `unknown-block(0,0)` almost always means there was no usable initramfs for that kernel: /boot was full, `update-initramfs` failed, or the upgrade was interrupted before the postinst ran. The initramfs-prompt variant means it loaded but couldn't find root: a changed root UUID after cloning, a storage driver missing from a slim initramfs (MODULES=dep, then the VM's disk moved from SCSI to VirtIO), or LVM or mdadm metadata not included.

**Diagnose:**

```bash
# Boot the previous kernel: GRUB menu > Advanced options for Ubuntu > the older version
uname -r
ls -lh /boot/initrd.img-* /boot/vmlinuz-*
dpkg -l 'linux-image-*' | grep -v '^ii'
lsinitramfs /boot/initrd.img-6.8.0-85-generic 2>/dev/null | grep -cE 'virtio_scsi|nvme|dm-mod'
grep -m2 'root=' /boot/grub/grub.cfg; sudo blkid | grep -E 'ubuntu--lv|sda'
```

```text
6.8.0-79-generic
-rw-r--r-- 1 root root 113M Sep 30 06:20 /boot/initrd.img-6.8.0-79-generic
-rw------- 1 root root  15M Oct  4 03:31 /boot/vmlinuz-6.8.0-85-generic
-rw------- 1 root root  15M Sep 12 06:14 /boot/vmlinuz-6.8.0-79-generic
iF  linux-image-6.8.0-85-generic   6.8.0-85.85   amd64   Signed kernel image generic
0
	linux	/vmlinuz-6.8.0-85-generic root=/dev/mapper/ubuntu--vg-ubuntu--lv ro
```

**What the output tells you:** the new kernel 6.8.0-85 has a vmlinuz but no initrd.img at all, and its package is half-configured (`iF`). GRUB booted it anyway and the kernel had nothing to mount root with. The older kernel is intact, which is why it boots.

**Fix:**

```bash
# Running on the older kernel: make room if needed (1.5), then finish the upgrade
sudo dpkg --configure -a
sudo update-initramfs -c -k 6.8.0-85-generic       # create the missing initramfs
sudo update-grub
ls -lh /boot/initrd.img-6.8.0-85-generic && sudo reboot
# RHEL equivalent:  sudo dracut -f --kver 5.14.0-570.12.1.el9_6.x86_64
# No kernel boots at all: boot a rescue ISO, then
#   vgchange -ay && mount /dev/ubuntu-vg/ubuntu-lv /mnt && mount /dev/sda2 /mnt/boot
#   for d in dev proc sys run; do mount --rbind /$d /mnt/$d; done
#   chroot /mnt update-initramfs -c -k 6.8.0-85-generic && chroot /mnt update-grub
```

**Why this fix works:** finishing dpkg's configure step and generating the initramfs gives the new kernel the drivers and LVM tools it needs; update-grub refreshes the menu. Booting the old kernel first means you repair from a working system instead of a rescue environment. What NOT to do: remove the old kernel before the new one has booted successfully, or copy another kernel's initramfs under the new name (modules must match the kernel version exactly).

**Prevent it:** keep at least two kernels installed, never reboot while `dpkg --audit` reports anything, keep /boot below 70%, use a GRUB menu timeout on servers where you have a console, and after hypervisor changes to disk controllers rebuild the initramfs before the next reboot. In the cloud, practise the detach-the-root-volume recovery (5.3) before you need it.

**Next step:** [Kernel & system: Boot & GRUB](13-kernel-system.md) · [Learn Linux: The boot process and recovery](27-learn-linux.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Linux Core Concepts (kernel, boot) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [Microsoft Q&A: kernel panic due to missing initramfs](https://learn.microsoft.com/en-us/answers/questions/2146821/kernel-panic-due-to-missing-initramfs) · [DEV: fixing "VFS: Unable to mount root fs on unknown-block(0,0)"](https://dev.to/dm8ry/fixing-the-kernel-panic-not-syncing-vfs-unable-to-mount-root-fs-on-unknown-block00-error-3ado) · Search: [Server Fault](https://serverfault.com/search?q=%22unable+to+mount+root+fs+on+unknown-block%280%2C0%29%22) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=kernel+panic+unknown-block+initramfs&restrict_sr=1)

## 10. NFS and network storage

NFS is simple to set up and subtle to operate: the defaults favour data safety (retry forever) over availability, so a slow or missing server shows up as hung processes and huge load on every client rather than as clean errors.

### 10.1 Stale file handle

> **Seen as:** `ls: cannot access '/mnt/shared': Stale file handle`, `df: /mnt/shared: Stale file handle`, or `mount.nfs: Stale file handle` when remounting · **Where:** clients of an NFS export that was recreated, moved, failed over or restored; Kubernetes pods with NFS volumes · **Level:** [L2 · Mid] · **How common:** a classic; Red Hat has KB articles on it and many RHEL troubleshooting guides start here

**Why it happens:** an NFS client refers to files and directories by opaque handles the server issued, built from the exported filesystem's ID and the inode. If the server can no longer resolve a handle, it answers ESTALE: the exported directory was deleted and recreated, the filesystem behind the export was reformatted, restored or replaced, a failover moved the export to a server that derives a different filesystem ID, or a file another client still had open was deleted on the server.

**Diagnose:**

```bash
# Client
findmnt -t nfs,nfs4 -o TARGET,SOURCE,OPTIONS
sudo dmesg -T | grep -i nfs | tail -3
# Server
sudo exportfs -v
ls -lid /srv/exports/shared
```

```text
TARGET      SOURCE                   OPTIONS
/mnt/shared 10.0.1.40:/srv/exports/shared rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,hard,proto=tcp,timeo=600,retrans=2,sec=sys
[Sat Oct  4 09:58:12 2026] NFS: server 10.0.1.40 error: fileid changed
/srv/exports/shared  10.0.1.0/24(sync,wdelay,hide,no_subtree_check,sec=sys,rw,secure,root_squash,no_all_squash)
1048577 drwxrwsr-x 4 deploy deploy 4096 Oct  4 09:41 /srv/exports/shared
```

**What the output tells you:** the export was recreated at 09:41 (a new directory with a new inode), so every client handle that pointed at the old directory is now stale. The client mount itself is healthy; it just has to forget the old handles.

**Fix:**

```bash
# Client: remount to get fresh handles (lazy unmount if processes still hold the path)
sudo umount /mnt/shared || sudo umount -l /mnt/shared
sudo mount /mnt/shared
# Restart processes that had their working directory or open files inside the mount
sudo fuser -vm /mnt/shared
# Server: give exports a stable ID so restores and failovers don't change handles
#   /srv/exports/shared 10.0.1.0/24(rw,sync,no_subtree_check,fsid=101)
sudo exportfs -ra
```

**Why this fix works:** a fresh mount asks the server for new handles; restarting the processes clears handles they cached; an explicit fsid in /etc/exports keeps the filesystem ID stable across reboots, restores and HA failovers. What NOT to do: `umount -f` in a loop on a busy production mount without finding the processes, or delete and recreate exported directories as a cleanup routine.

**Prevent it:** never replace exported directories in place (sync into them instead), set fsid for every export, and in Kubernetes prefer an NFS CSI driver with a stable server name and restart pods after a server-side restore.

**Next step:** [Storage & disk: NFS / network storage](01-storage-disk.md) · [Containers & K8s playbook](26-playbook-containers-k8s.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux (NFS) · [ArchWiki: NFS](https://wiki.archlinux.org/title/NFS)

**Community threads:** [Red Hat: Stale file handle when mounting an NFS exported XFS filesystem](https://access.redhat.com/solutions/437813) · [ArchWiki: NFS](https://wiki.archlinux.org/title/NFS) · Search: [Server Fault](https://serverfault.com/search?q=nfs+%22stale+file+handle%22+fsid) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=nfs+stale+file+handle&restrict_sr=1)

### 10.2 NFS server gone: hung shells and D state

> **Seen as:** dmesg says `nfs: server 10.0.1.40 not responding, still trying`; `df`, `ls /mnt` and even SSH logins hang; `kill -9` seems to do nothing; load climbs to 50 (7.1); shutdown waits forever (3.6); later `nfs: server 10.0.1.40 OK` and everything resumes · **Where:** every NFS client when the server reboots, its network flaps or it is overloaded; hosts whose monitoring agent stats every mount · **Level:** [L3 · Senior] · **How common:** one of the oldest operational NFS complaints; the reason most guides recommend automount and _netdev

**Why it happens:** NFS mounts are `hard` by default: the client retries forever so applications never see a write silently fail. Every process touching the mount waits in uninterruptible sleep until the server answers, and those D-state tasks raise the load average. Anything that walks all mounts (df, monitoring agents such as node_exporter's filesystem collector, shell prompts, backup scripts) hangs with them. `soft` mounts return errors instead, but a soft timeout during a write can corrupt data, which is why it is the wrong default for anything that writes.

**Diagnose:**

```bash
sudo dmesg -T | grep -iE 'not responding|nfs: server' | tail -3
ps -eo state,pid,wchan:30,cmd | awk '$1=="D"' | head
timeout 5 stat -f /mnt/shared >/dev/null || echo "mount is hanging"
nc -vz -w 3 10.0.1.40 2049
```

```text
[Sat Oct  4 11:20:44 2026] nfs: server 10.0.1.40 not responding, still trying
D    4410 rpc_wait_bit_killable          df -h
D    4498 rpc_wait_bit_killable          /usr/bin/node_exporter
D    5120 nfs_wait_on_request            rsync -a /var/backups/ /mnt/shared/
mount is hanging
nc: connect to 10.0.1.40 port 2049 (tcp) timed out: Operation now in progress
```

**What the output tells you:** the server doesn't answer on 2049 at all, and df, the monitoring agent and the backup job are all waiting inside the NFS client. Nothing on this client is broken; it is waiting exactly as a hard mount should.

**Fix:**

```bash
# Best outcome: bring the server (or the network path) back; waiting processes then continue
# Server gone for good: detach the mount so the rest of the host recovers
sudo umount -f -l /mnt/shared
sudo kill -9 4410 4498 5120          # killable once the RPCs are aborted
# Design the mount so a dead server can't take the host down next time
#   10.0.1.40:/srv/exports/shared /mnt/shared nfs4 _netdev,nofail,hard,timeo=600,retrans=2,x-systemd.automount,x-systemd.idle-timeout=600,x-systemd.mount-timeout=30 0 0
sudo systemctl daemon-reload
```

**Why this fix works:** a forced lazy unmount aborts outstanding requests and detaches the mount point, so blocked tasks get errors and can exit; automount means the mount only exists while something uses it and drops after ten idle minutes, so df, agents and logins don't touch a dead server; hard stays on for data safety. What NOT to do: switch writable mounts to `soft` to "avoid hangs" (silent data corruption risk), or put NFS paths in root's PATH, login scripts or shell prompts.

**Prevent it:** run NFS on a highly available server (or object storage where possible), exclude NFS from agents that stat mounts (node_exporter: `--collector.filesystem.mount-timeout` and fs-type excludes; `df -l` in scripts), alert on "not responding" kernel messages, and test a server reboot while clients are busy.

**Next step:** [Storage & disk: NFS / network storage](01-storage-disk.md) · [Slow system playbook](23-playbook-slow-system.md) · [Networking, DNS, TLS & VPN problems](42-problems-network-dns-tls-vpn.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux (NFS) · [systemd.mount (automount options)](https://www.freedesktop.org/software/systemd/man/latest/systemd.mount.html)

**Community threads:** [ArchWiki: NFS](https://wiki.archlinux.org/title/NFS) · [ArchWiki: fstab (automount and _netdev)](https://wiki.archlinux.org/title/Fstab) · Search: [Server Fault](https://serverfault.com/search?q=nfs+%22server+not+responding%2C+still+trying%22+hung+processes) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=nfs+server+not+responding+hung&restrict_sr=1)

## 11. Bare-metal hardware: RAID and SMART

On your own hardware, disks fail on a schedule you don't choose, and Linux only tells you if you ask. In the cloud the provider hides this layer and gives you different signals instead. Both entries below include the on-prem and the cloud view.

### 11.1 RAID degraded: replacing a disk in mdadm

> **Seen as:** `/proc/mdstat` shows `[2/1] [U_]`, mdadm mails `DegradedArray event on /dev/md0`, or a boot message `mdadm: /dev/md0 has been started with 1 drive (out of 2).` · **Where:** bare-metal servers and homelab boxes with Linux software RAID (often RAID1 for the OS, RAID5/6/10 for data) · **Level:** [L3 · Senior] · **How common:** routine bare-metal work; the Linux RAID wiki's "Replacing a failed drive" page and the old Software-RAID HOWTO are standard references

**Why it happens:** md kicks a member out after I/O errors it cannot recover from, and the array keeps running on the rest. Real disk failure is the usual reason, but cables, backplanes and timeout mismatches also do it: a desktop disk without SCT ERC may spend minutes retrying a bad sector while the kernel gives up after 30 seconds and drops a disk that is mostly fine. A degraded RAID1 or RAID5 has no redundancy left, and the rebuild itself reads every sector of the remaining disks, which is when a second weak disk tends to fail.

**Diagnose:**

```bash
cat /proc/mdstat
sudo mdadm --detail /dev/md0 | grep -E 'State|Devices|/dev/sd'
sudo dmesg -T | grep -iE 'md/raid|md0|sdb' | tail -4
ls -l /dev/disk/by-id/ | grep -E 'ata-|nvme-' | grep -v part    # map sdX to serial numbers
sudo smartctl -l scterc /dev/sda                                # error-recovery timeout support
```

```text
Personalities : [raid1]
md0 : active raid1 sda3[0]
      976630464 blocks super 1.2 [2/1] [U_]
      bitmap: 6/8 pages [24KB], 65536KB chunk
             State : clean, degraded
    Active Devices : 1
   Working Devices : 1
    Failed Devices : 0
       0       8        3        0      active sync   /dev/sda3
       -       0        0        1      removed
[Sat Oct  4 03:12:44 2026] md/raid1:md0: Disk failure on sdb3, disabling device.
[Sat Oct  4 03:12:44 2026] md/raid1:md0: Operation continuing on 1 devices.
lrwxrwxrwx 1 root root  9 Oct  4 03:15 ata-WDC_WD1003FBYZ-010FB0_WD-WCAW3PL81234 -> ../../sda
lrwxrwxrwx 1 root root  9 Oct  4 03:15 ata-WDC_WD1003FBYZ-010FB0_WD-WCAW3PL85678 -> ../../sdb
SCT Error Recovery Control:
           Read:     70 (7.0 seconds)
          Write:     70 (7.0 seconds)
```

**What the output tells you:** md0 runs on sda3 alone after sdb3 failed at 03:12. The serial number of sdb (ending 85678) is the disk to pull, and these drives support a 7-second error recovery, so a timeout mismatch is unlikely: check sdb's SMART data (11.2) to confirm it is the disk.

**Fix:**

```bash
# 1. Make sure the failed member is out of the array
sudo mdadm --manage /dev/md0 --fail /dev/sdb3 --remove /dev/sdb3
# 2. Replace the disk with serial ...85678 (hot-swap bay, or shut down first)
# 3. Copy the partition table from the healthy disk onto the new one, then give it new GUIDs
sudo sgdisk /dev/sda -R /dev/sdb && sudo sgdisk -G /dev/sdb
# 4. Add it back and watch the rebuild
sudo mdadm --manage /dev/md0 --add /dev/sdb3
watch -n 30 cat /proc/mdstat
# 5. OS array: make the new disk bootable too (BIOS boot shown; for UEFI, copy the ESP)
sudo grub-install /dev/sdb
```

Hardware RAID controllers follow the same logic with the vendor's tool (storcli, perccli or ssacli) and their BMC; the controller rebuilds, but you still identify the disk by serial and watch the rebuild.

**Why this fix works:** removing the failed member and adding a correctly partitioned new disk lets md resync it from the healthy copy; `-R` copies sda's layout onto sdb (the destination comes after -R), and `-G` avoids two disks with identical GUIDs. Installing the bootloader on the new disk means the server still boots if sda dies next. What NOT to do: pull a disk by its sdX name alone (names can change; use serials and bay LEDs), run `mdadm --create` on an existing array to "fix" it (it can destroy the metadata), or treat RAID as a backup.

**Prevent it:** set `MAILADDR ops@example.com` in /etc/mdadm/mdadm.conf and test with `sudo mdadm --monitor --scan --test --oneshot`, keep the monthly array check (Debian and Ubuntu ship it), run smartd (11.2), keep a cold or hot spare, and prefer RAID6 or RAID10 over RAID5 for large disks.

**Next step:** [Storage & disk: Software RAID (mdadm)](01-storage-disk.md) · [Kernel & system: Hardware health](13-kernel-system.md) · [Databases, storage & backup problems](51-problems-databases-storage-backup.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux · [Linux RAID wiki](https://raid.wiki.kernel.org/index.php/Replacing_a_failed_drive)

**Community threads:** [Linux RAID wiki: Replacing a failed drive](https://raid.wiki.kernel.org/index.php/Replacing_a_failed_drive) · [TLDP Software-RAID HOWTO: detecting, querying and testing](https://tldp.org/HOWTO/Software-RAID-HOWTO-6.html) · Search: [Server Fault](https://serverfault.com/search?q=mdadm+degraded+replace+failed+disk+raid1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=mdadm+degraded+replace+disk&restrict_sr=1)

### 11.2 SMART warnings: is the disk dying?

> **Seen as:** smartd mails `Device: /dev/sdb [SAT], 8 Currently unreadable (pending) sectors`; `smartctl -H` says `PASSED` while Reallocated_Sector_Ct keeps climbing; an NVMe drive reports `Percentage Used: 98%` or `Media and Data Integrity Errors: 12` · **Where:** bare-metal servers, homelab boxes, Proxmox hosts; in the cloud you get different signals · **Level:** [L3 · Senior] · **How common:** routine on any fleet of physical disks; Thomas-Krenn and Fedora maintain widely used guides to reading smartctl output

**Why it happens:** disks wear out: HDDs develop bad sectors and remap them to spares, SSDs and NVMe drives use up their rated write endurance. SMART counts these events, but the overall "PASSED" only means no attribute has crossed the vendor's (often very lenient) threshold. Rising reallocated, pending or offline-uncorrectable counts mean the disk is failing even while it still says PASSED. A rising UDMA CRC error count, by contrast, usually points at the cable or backplane, not the disk.

**Diagnose:**

```bash
sudo smartctl -H -A /dev/sdb | grep -E 'result|Reallocated_Sector|Current_Pending|Offline_Uncorrectable|UDMA_CRC|Power_On_Hours'
sudo smartctl -l error -l selftest /dev/sdb | tail -6
sudo smartctl -t long /dev/sdb                      # full surface test; check results hours later
sudo smartctl -a /dev/nvme0 | grep -E 'Percentage Used|Media and Data Integrity|Critical Warning'
# Behind a MegaRAID/PERC controller: address disks through it
sudo smartctl -a -d megaraid,1 /dev/sda | head -20
```

```text
SMART overall-health self-assessment test result: PASSED
  5 Reallocated_Sector_Ct   0x0033   188   188   140    Pre-fail  Always       -       364
  9 Power_On_Hours          0x0032   027   027   000    Old_age   Always       -       53410
197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       8
198 Offline_Uncorrectable   0x0030   200   200   000    Old_age   Offline      -       8
199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0
# 1  Extended offline    Completed: read failure       90%     53388         1953525160
Critical Warning:                   0x00
Percentage Used:                    41%
Media and Data Integrity Errors:    0
```

**What the output tells you:** sdb is six years into service, has remapped 364 sectors, has 8 it can't read at all, and failed its last long self-test at 90%. "PASSED" notwithstanding, it is failing: replace it (in RAID, follow 11.1). The CRC count of 0 rules out the cable. The NVMe drive is healthy at 41% of its endurance.

**Fix:** replace the disk before it fails completely; without RAID, copy the data off first (rsync from the live filesystem, or `ddrescue` to clone a failing disk onto a new one with a map file).

<div class="env" data-env="onprem" markdown="1">

**On-premise:** make smartd watch every disk and mail you, and feed the same data to monitoring. A typical /etc/smartd.conf line: `DEVICESCAN -a -o on -S on -n standby,q -s (S/../.././02|L/../../6/03) -W 4,45,55 -m ops@example.com` (all attributes, a short test daily at 02:00, a long test on Saturdays at 03:00, temperature warnings, mail on problems). Then `sudo systemctl enable --now smartmontools` (the unit is smartd on RHEL). Export SMART data to Prometheus with smartctl_exporter, and let the BMC alert on controller and drive status for hardware RAID.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud (AWS):** EBS volumes don't expose SMART; the provider replaces failing hardware behind the volume. Your signals are EC2 status checks (a failed system status check means the host underneath has a problem: stop and start the instance to move it to new hardware), scheduled events such as instance retirement (`aws ec2 describe-instance-status --include-all-instances`), and EBS volume status (`aws ec2 describe-volume-status`, status impaired). Instance-store NVMe disks are ephemeral: treat their data as disposable and keep anything important on EBS or S3. Keep EBS snapshots (Data Lifecycle Manager or AWS Backup) so a damaged volume is a restore, not a loss.

</div>

**Why this fix works:** SMART attributes predict failure well enough that replacing on rising reallocated, pending or uncorrectable counts avoids most emergency rebuilds; long self-tests find bad areas before your data does. In the cloud the equivalent is reacting to status checks and retirement events and having snapshots ready. What NOT to do: wait for "FAILED" (many disks die without ever reporting it), run long tests on every disk of an array at the same time during business hours, or keep a disk in service because a short test passed.

**Prevent it:** smartd plus a metric and an alert for every physical disk, replacement thresholds written down (for example: any pending sector, or reallocated count rising week over week), spare disks on the shelf, and a tested restore path.

**Next step:** [Storage & disk: Physical disk health](01-storage-disk.md) · [Kernel & system: Hardware health](13-kernel-system.md) · [Observability stack problems](49-observability-stack-problems.md) · [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Monitor Storage Performance · [smartmontools](https://www.smartmontools.org/)

**Community threads:** [Thomas-Krenn wiki: Smartctl tool](https://www.thomas-krenn.com/en/wiki/Smartctl_Tool) · [Thomas-Krenn wiki: analyzing a faulty hard disk using smartctl](https://www.thomas-krenn.com/en/wiki/Analyzing_a_Faulty_Hard_Disk_using_Smartctl) · [Fedora wiki: Smartctl](https://fedoraproject.org/wiki/Smartctl) · Search: [Server Fault](https://serverfault.com/search?q=smart+reallocated+sector+count+pending+replace+disk) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=smart+reallocated+sectors+replace&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises on the lab VMs from section 0 (a second virtual disk on web1 for the storage ones, the small NFS VM for exercise 8). Snapshot first, break it exactly as described, then fix it using only the entry and write your five-line note: symptom, evidence, cause, fix, prevention.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Run a container that logs a line every millisecond until / is above 95%; find the space and free it without stopping the container | 15 min | 1.1, 1.2 |
| 2 | Fresher | Write a unit whose ExecStart needs an env var you don't provide, with Restart=always; find the real error behind "repeated too quickly" | 10 min | 3.1, 3.2 |
| 3 | Junior | Start `apt-get upgrade` in one session and kill dpkg with kill -9 halfway from another; make apt work again | 15 min | 2.1, 2.2 |
| 4 | Junior | Add a crontab line that calls pg_dump or another tool by name and uses `date +%F`; prove it fails, fix it, then convert it to a timer with Persistent=true | 20 min | 3.4 |
| 5 | Junior | chmod 775 the deploy user's home, then move SSH to port 2222 on Ubuntu 24.04 the wrong way; get back in through the console and fix both | 25 min | 5.1, 5.2, 5.3 |
| 6 | Mid-level | Add the second disk to fstab by UUID, detach the disk in the hypervisor, reboot; recover from emergency mode and make the mount non-blocking | 20 min | 9.2 |
| 7 | Mid-level | Run a small server under systemd, load-test it until it logs "too many open files"; fix it with a drop-in and prove it via /proc/PID/limits | 25 min | 7.2 |
| 8 | Mid-level | Mount an NFS export on web1, run a writer, then stop the NFS server; watch D state and load, recover the client, redesign the mount with automount | 30 min | 10.2, 7.1 |
| 9 | Senior | Build an mdadm RAID1 from two virtual disks, fail and remove one, replace it with a new disk, rebuild, and make it bootable | 40 min | 11.1 |
| 10 | Senior/Lead | Write the patch policy for ten Ubuntu hosts (unattended-upgrades config, blacklist, reboot windows, drain steps, time sources, alerts), then run it on two lab VMs with a forced kernel update | 60 min | 2.6, 8.2 |

Quick questions to answer from memory:

1. Why does deleting a 20 GB log not free any space, and which two commands fix it without a reboot?
2. Which three different counters can make "No space left on device" appear, and how do you check each?
3. Why does a line in /etc/security/limits.conf not change a systemd service's open-file limit, and what does?
4. What does a load average of 30 with idle CPUs mean on Linux, and which column of vmstat confirms it?
5. Why does changing Port in sshd_config and restarting ssh.service do nothing on Ubuntu 24.04?
6. What do `nofail`, `_netdev` and `x-systemd.automount` each change for an fstab entry?

---

## Where to go next

- [Learn Linux](27-learn-linux.md): the fundamentals behind every entry: systemd, boot and recovery, storage, users and sudo, SSH, scheduling, logs and the debugging tools.
- The quick references this module builds on: [Storage & disk](01-storage-disk.md), [CPU & performance](03-cpu-performance.md), [Memory](04-memory.md), [Processes](05-processes.md), [Logs & journal](06-logs-journal.md), [Services & systemd](07-services-systemd.md), [SSH & remote access](09-ssh-remote-access.md), [Users, permissions & security](10-users-permissions-security.md), [Time & NTP](12-time-ntp.md) and [Kernel & system](13-kernel-system.md).
- [Slow system playbook](23-playbook-slow-system.md) and [Site down playbook](25-playbook-site-down.md): the step-by-step incident flows that send you into sections 1, 6, 7 and 10.
- [Networking, DNS, TLS & VPN problems](42-problems-network-dns-tls-vpn.md), [Network](02-network.md), [DNS](08-dns.md) and [Learn networking](28-learn-networking.md): when the host is fine and the path is not.
- [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md), [Web, HTTP & TLS](18-web-http-tls.md) and [Ports inventory playbook](22-playbook-ports-inventory.md): the services on top of these hosts, and who owns which port.
- [Security & DevSecOps](37-learn-security-devsecops.md): hardening SSH, sudo, SELinux and AppArmor without locking yourself out.
- [Practice arena](54-practice-arena.md): more break-and-fix drills to run on the same lab VMs.
- [Paths: on-prem vs cloud](55-paths-onprem-vs-cloud.md): how patching, consoles, disks and time sources differ between your own hardware and AWS.
- Official docs: [systemd man pages](https://www.freedesktop.org/software/systemd/man/latest/) · [Ubuntu Server docs](https://ubuntu.com/server/docs) · [RHEL 9 documentation](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9) · [Linux kernel docs](https://docs.kernel.org/) · [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html) · [chrony](https://chrony-project.org/doc/4.3/chronyc.html) · [Linux RAID wiki](https://raid.wiki.kernel.org/index.php/Replacing_a_failed_drive)
