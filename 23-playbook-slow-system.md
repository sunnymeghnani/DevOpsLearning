# 23 — Why Is the System Slow? (Step-by-Step)

"The server is slow" is the vaguest ticket you will ever get, and the most
common one. This playbook turns it into a method. First you pin down what
"slow" means, then you run a 60-second checklist that looks at every resource
once, then you follow the branch the evidence points to: CPU, memory, disk,
network, the application itself, or "only sometimes". Every step says what to
run, how to read the output, why that step comes at that point, and where to go
next.

It targets Ubuntu 22.04/24.04 servers (on-prem and AWS) and calls out
RHEL/Rocky differences. Windows and macOS get short playbooks near the end. The
command references behind it are [CPU & performance](03-cpu-performance.md),
[Memory](04-memory.md), [Storage & disk](01-storage-disk.md) and
[Processes](05-processes.md). The theory (queueing, USE, flame graphs,
Prometheus) is in [Learn: performance & observability](32-learn-performance-observability.md).

> ⚠️ All outputs are illustrative samples. Most come from one fictional host,
> `web01` (4 vCPU, 8 GB RAM, Ubuntu 22.04), which runs Apache with three vhosts
> next to Dokploy (Traefik, Docker Swarm) and a few containers, like the servers
> you are migrating. Numbers vary by kernel, distro and hardware. Uppercase
> words (PID, HOST, CONTAINER, UNIT, DEVICE, SERVICE) are placeholders.
> Nothing in this module needs to be run on a healthy machine. Practise on a
> lab VM (section 20).
>
> Some samples show Apache still on 443, as before your migration. On your
> servers Apache now listens on 81 and 444 with Traefik in front
> ([Deployment patterns](35-deployment-patterns.md)): put your own Apache
> ports into filters such as `sport = :443`, and remember that a slow vhost
> is then measured twice, in Traefik's access log and in Apache's (Step A10).

**How to use this module**

| Your situation | Start here |
|---|---|
| Fresh complaint, no idea yet | Section 1 (define slow), then section 2 (60-second checklist) |
| The checklist points at one resource | Sections 3–7 (CPU, memory, disk, network, application) |
| It happened last night, or it comes and goes | Section 8 (slow only sometimes) |
| A known symptom: slow boot, slow SSH login, hung shell, slow container, slow VM, high load with idle CPU, softirq | Sections 9–15 |
| Windows or macOS | Sections 16–17 |
| You want the whole method on one screen | Section 18 (master decision tree) |
| You fixed it and never want the 2 a.m. call again | Section 19 (monitoring, alerts, baselines) |
| You want to practise, or test yourself | Sections 20–21 (labs, self-check / exit test) |

**Who this module is for, from Fresher to Senior.** "The server is slow" lands
on every desk, but each career stage owns a different part of the answer. Tags
like [L2 · Mid] under each section heading say where that section sits on the
Ops Ladder (Fresher ≈ L0, Junior ≈ L1, Mid-level ≈ L2, Senior ≈ L3,
Senior/Lead/SRE ≈ L4).

| Stage | What you should own in this module | Sections |
|---|---|---|
| Fresher (0–1 yr) · [L0 · Fresher] | Read every output in the 60-second checklist on a lab VM; time a request with `curl -w`; never restart before taking the snapshot | 1, 2, 20 (drills 1–2) |
| Junior (1–2 yrs) · [L1 · Junior] | Run the checklist on call and name the saturated resource; fix the everyday scenarios (boot, SSH, hung shell); know when to escalate | 1, 2, 9–11, 16–17 |
| Mid-level (2–4 yrs) · [L2 · Mid] | Own the deep dives end to end: CPU, memory, disk, network, application, "only sometimes"; containers; write the incident note | 3–8, 12, 14, 18 |
| Senior (4–7 yrs) · [L3 · Senior] | Profilers and flame graphs, cgroup limits, hypervisor and storage evidence, NIC queues; set limits and budgets so it cannot recur | 3 (C5–C7), 4 (M8–M9), 5 (D5–D7), 13, 15 |
| Senior/Lead/SRE (5+ yrs) · [L4 · Lead] | Saturation-based alerting, baselines, capacity forecasts, game days and postmortems that change the platform | 8 (H5–H6), 19, 21 |

**Step labels.** The 60-second checklist uses Step 1 to Step 10. The deep
dives use a letter so that "next step" pointers are unambiguous: **C** = CPU,
**M** = memory, **D** = disk, **N** = network, **A** = application,
**H** = history, **W** = Windows, **X** = macOS (from "OS X"). Scenario
sections (9–15) number their own steps; other sections refer to them as
"section 12, Step 2".

---

## 1. Define slow before you touch anything

> 📚 **Study path:** 1) Note: [Learn: performance & observability](32-learn-performance-observability.md), sections 1–2 (vocabulary, USE and RED) · 2) Read: Netflix [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) · 3) KodeKloud: *Fundamentals of SRE* — Observability and Monitoring → Performance Monitoring Deep Dive ([lesson note](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page), [course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 5) Practice: time three pages of your own sites with `curl -w` and write down p50/max (this section). KodeKloud teaches the tools but not the USE method, so the note and the article come first.

**Level:** [L1 · Junior]. A Fresher can do all of it; from Junior on it is
expected before every investigation.

Most wasted hours in a slowness incident come from fixing the wrong thing:
adding RAM to a disk problem, restarting Apache when the database is slow,
blaming the network when DNS takes five seconds. Two minutes of questions
before the first command prevents that.

### Latency versus throughput

**Latency** is how long one unit of work takes: one HTTP request, one query,
one `fsync`, one SSH login. You measure it in milliseconds. **Throughput** is
how much work gets done per second: requests per second, MB/s, IOPS.

They are different problems with different fixes:

| Complaint | It is really about | First measurement |
|---|---|---|
| "The page takes 4 seconds" | latency of one request | `curl -w` timing (below) |
| "The nightly backup now finishes at 09:00" | throughput of a batch job | MB/s of the job, `iostat`, `sar` history |
| "The API times out under load" | latency that grows with load (queueing) | latency at several request rates |
| "SSH takes 20 seconds to give me a prompt" | latency of one login | `ssh -vvv` with timestamps (section 10) |
| "Builds are slow on this runner" | throughput, CPU and disk | `pidstat`, `iostat` during a build |

A disk can deliver 500 MB/s of sequential throughput and still take 200 ms per
`fsync`. Users only feel the 200 ms.

**Queueing explains most slowness.** When a resource is busy, new work waits.
As a rough rule from queueing theory, response time ≈ service time ÷ (1 −
utilisation):

| Utilisation of the busy resource | Response time compared with an idle system |
|---|---|
| 50% | about 2× |
| 80% | about 5× |
| 90% | about 10× |
| 95% | about 20× |

That is why a resource at "only 80%" can already be the latency problem, and
why the checklist looks at **saturation** (work waiting) and not just
utilisation.

### Six questions before the first command

Ask the person who reported it, or answer them yourself from monitoring:

1. **Slow for whom?** One user, one vhost, one office, one region, or everyone? Internal and external users alike? One user points to the client or their network; everyone points to the server or a shared dependency.
2. **Slow doing what?** A page, an API call, a login, a shell command, a backup, a deploy? Name the exact action so you can time it.
3. **Since when?** Get a timestamp. Everything else (graphs, logs, deploys, cron) gets correlated against it.
4. **Always or sometimes?** Every hour at :00 suggests cron. Nightly suggests backups. Only under load suggests saturation. Random spikes suggest GC pauses, noisy neighbours or locks.
5. **How slow, in numbers?** "200 ms normally, 4 s now" is a ticket you can close. "It feels slow" is not. Measure it yourself (next heading).
6. **What changed?** Deploys, config edits, package upgrades, kernel updates and reboots, a new vhost or container, traffic growth, a new cron job or backup, DNS or certificate changes.

### Find what changed in the last 24 hours

**Goal:** list every recent change on the box before you form a theory.

```bash
# Package changes (Ubuntu/Debian). RHEL/Rocky: sudo dnf history list | head
grep -E ' (install|upgrade|remove) ' /var/log/dpkg.log | tail -20
zgrep -h -A1 'Start-Date' /var/log/apt/history.log* | grep Commandline | tail

# Reboots and the running kernel
last -x reboot | head -5
journalctl --list-boots --no-pager | tail -5
uname -r

# Config files changed in the last day
sudo find /etc/apache2 /etc/netplan /etc/docker /etc/systemd/system /etc/sysctl.d \
  /etc/cron.d -type f -mtime -1 -ls 2>/dev/null

# Containers created or restarted recently (Dokploy deploys show up here)
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.RunningFor}}\t{{.Status}}'
docker events --since "$(date -d '24 hours ago' +%s)" --until "$(date +%s)" \
  --filter type=container --filter event=start

# Who logged in, and what ran through sudo
last -n 20
sudo journalctl --since "24 hours ago" _COMM=sudo --no-pager | tail -20
```

```
2026-10-03 06:14:02 install linux-image-5.15.0-122-generic:amd64 <none> 5.15.0-122.132
2026-10-03 06:14:09 upgrade openssl:amd64 3.0.2-0ubuntu1.17 3.0.2-0ubuntu1.18
reboot   system boot  5.15.0-122-gene Sat Oct  3 06:20   still running
NAMES                 IMAGE                                 RUNNING FOR      STATUS
shop-api.1.x8k2...    harbor.example.com/shop/api:4f1c2a9   58 minutes ago   Up 58 minutes
dokploy-traefik       traefik:v3.1                          3 weeks ago      Up 3 weeks
```

→ A kernel update and reboot at 06:20, and `shop-api` was redeployed 58
minutes ago. Write both down with their times. If the slowness started right
after a deploy, the deploy is suspect number one: roll it back first and
investigate second. The Google SRE book's troubleshooting chapter makes the
same point: stabilise first, then find the root cause.

### Turn the complaint into a number

**Goal:** get a repeatable measurement that also tells you which phase is slow.

```bash
# Break one HTTPS request into phases (times are cumulative from the start)
curl -o /dev/null -s -w 'dns=%{time_namelookup}s connect=%{time_connect}s tls=%{time_appconnect}s ttfb=%{time_starttransfer}s total=%{time_total}s code=%{http_code}\n' \
  https://app.example.com/

# The same request from the server itself, skipping DNS and the network path
curl -o /dev/null -s -w 'connect=%{time_connect}s ttfb=%{time_starttransfer}s total=%{time_total}s\n' \
  --resolve app.example.com:443:127.0.0.1 https://app.example.com/

# Twenty requests: min / median / max shows whether it is always or sometimes slow
for i in $(seq 20); do curl -o /dev/null -s -w '%{time_total}\n' https://app.example.com/; done \
  | sort -n | awk '{a[NR]=$1} END {print "min="a[1], "p50="a[int(NR/2)], "max="a[NR]}'

# For a command instead of a web request
time tar czf /var/tmp/etc.tgz /etc
```

```
dns=0.004s connect=0.021s tls=0.067s ttfb=3.912s total=3.958s code=200
connect=0.000s ttfb=3.871s total=3.902s
min=3.701 p50=3.902 max=4.388

tar: Removing leading `/' from member names
real    0m9.214s
user    0m1.102s
sys     0m0.388s
```

**What it means:**

- `dns` 4 ms, `connect` 17 ms after that, `tls` 46 ms after that: the network and TLS are fine.
- `ttfb` minus `tls` = 3.85 s: the server took almost 4 seconds to produce the first byte. The problem is on the server or behind it (app, database, upstream API).
- The request from the server itself is just as slow, so the path between the user and the server is innocent.
- min/p50/max are close together: it is slow every time, not intermittently. That makes it easier to catch live.
- `time`: `real` is wall-clock time, `user + sys` is CPU time. Here 9.2 s real but only 1.5 s CPU, so the command spent about 7.7 s **waiting** (disk, network, locks). When `real ≈ user + sys`, the command is CPU-bound.

| What is large | Where the problem is | Go to |
|---|---|---|
| `dns` (often exactly 5 s or 10 s) | resolver timeouts | Step N1 |
| `connect` | network path, SYN drops, full accept queue | Step A5, [Network speed](24-playbook-network-speed.md) |
| `tls` minus `connect` | TLS handshake, OCSP, slow proxy, CPU | [Web, HTTP & TLS](18-web-http-tls.md) |
| `ttfb` minus `tls` | the server or application | Section 2 |
| `total` minus `ttfb` | body transfer (size or bandwidth) | [Network speed](24-playbook-network-speed.md) |

### The USE method for every resource

Brendan Gregg's **USE method**: for every resource, check

- **Utilisation:** how busy it is (percent of time, or percent of capacity).
- **Saturation:** how much work is waiting because it is busy (queues, run queue, swapping).
- **Errors:** error events (I/O errors, drops, OOM kills, retransmits).

It works because it is a checklist. You cannot forget the disk because the
CPU looked interesting. It also applies to software resources: worker pools,
connection pools, file descriptors and locks saturate too.

| Resource | Utilisation | Saturation | Errors |
|---|---|---|---|
| CPU | `mpstat -P ALL 1` (%usr + %sys per core) | `vmstat 1` r above core count, `/proc/pressure/cpu` | `dmesg` (machine check, thermal) |
| Memory | `free -m` (available) | `vmstat` si/so, `/proc/pressure/memory`, `sar -B` pgscand/s | OOM kills in `journalctl -k` |
| Disk | `iostat -x` %util (careful, see section 5) | `iostat -x` aqu-sz and await, `/proc/pressure/io` | `dmesg` I/O errors, `smartctl -H` |
| Network | `sar -n DEV 1` against link speed | `sar -n ETCP 1` retransmits, `ip -s link` drops | `ip -s link` errors, `ethtool -S` |
| Filesystem capacity | `df -h`, `df -i` | (nearly full slows writes) | ENOSPC in application logs |
| File descriptors | `/proc/sys/fs/file-nr`, `ls /proc/PID/fd` | (none) | "Too many open files" |
| Conntrack table | `nf_conntrack_count` against `nf_conntrack_max` | (none) | "table full, dropping packet" |
| Apache workers | BusyWorkers against MaxRequestWorkers | listen queue Recv-Q in `ss -ltn` | AH00161 or AH00484 in error.log |
| DB connection pool | active connections against pool size | threads waiting for a connection | pool timeout errors |
| Container CPU quota | `cpu.stat` usage_usec | `cpu.stat` nr_throttled | (none) |

### The RED method for services

USE looks at resources. **RED** looks at each service the way users feel it:

- **Rate:** requests per second.
- **Errors:** failed requests per second (5xx, timeouts).
- **Duration:** how long requests take, as percentiles (p50, p95, p99), never only the average.

Apply RED to each Apache vhost, each Traefik router and each API. It answers
*which* service suffers and *when*. USE then answers *which resource* causes
it. Where to read RED: access logs with a duration field (Step A10), Traefik
metrics, application metrics. Google's SRE book calls the same idea the four
golden signals: latency, traffic, errors, saturation.

> Averages lie. If 95 requests take 100 ms and 5 take 10 s, the average is
> about 600 ms, which nobody experienced. The p99 of 10 s is what the angry
> users saw.

### Measure, do not guess

- **Guessing** sounds like "it's probably the database". **Measuring** sounds like "requests wait 2.9 s in `poll()` on the socket to 10.0.20.15:5432, so it's the database". Only the second one tells you what to fix.
- **Write down each hypothesis next to the measurement that could kill it.** "If it were CPU, `vmstat` r would exceed 4 and id would be near 0." Then look.
- **Restarting destroys evidence.** The leak, the stuck thread and the hung NFS call all disappear with the restart, and come back next week. Take the 60-second snapshot (section 2) first. It costs one minute.
- **Stabilise first if the business is burning.** If a deploy 10 minutes ago obviously caused it, roll back, then investigate on a copy or in the logs.
- **Change one thing at a time** and re-measure with the same command you used before.
- **Keep a timeline** in a text file as you work: time, command, what you saw, what you changed. It becomes the postmortem.

---

## 2. The 60-second checklist

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment → Diagnose and Manage Processes ([lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)), then Storage → Monitor Storage Performance (`iostat`, `pidstat`; [lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page); [course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Read: Netflix [Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55) · 3) Video: Brendan Gregg *Linux Performance Tools, LinuxCon Europe 2014* ([49 min](https://www.youtube.com/watch?v=SN7Z0eCn0VY)) · 4) Note: [CPU & performance](03-cpu-performance.md) and [Memory](04-memory.md) for the flags · 5) Practice: run the checklist under `stress-ng` on the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) (section 20, drills 1–3).

**Level:** [L1 · Junior]. Freshers practise it on a lab VM ([L0 · Fresher]);
from Junior on you run it, unprompted, in the first minute of every "slow"
ticket.

This is Netflix's "first 60 seconds" list from
[Linux Performance Analysis in 60,000 ms](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55),
adapted for Ubuntu. Ten commands, one pass, every resource. **Do not fix
anything yet**: collect, then decide.

The sample outputs tell one story. `web01` became slow at about 10:30. Read
each step's output as a clue; Step 10 puts them together.

### Install the tools before you need them

**Goal:** have every tool in this module present on every server, so the
incident does not start with `apt install`.

```bash
# Ubuntu / Debian
sudo apt install sysstat htop iotop atop smem strace ltrace \
  linux-tools-common linux-tools-$(uname -r) bpfcc-tools

# RHEL / Rocky / Alma (htop, atop and smem come from EPEL)
sudo dnf install sysstat htop iotop atop smem strace ltrace perf bcc-tools
```

→ `sysstat` provides `mpstat`, `pidstat`, `iostat` and `sar`. Live sampling
(`sar 1`) works straight away. History (`sar` for last night) only exists if
collection is enabled; see Step H1. Put this list in your Ansible base role
so every new server has it.

### Save a snapshot before you dig

**Goal:** keep a copy of the whole checklist's output so you can compare
after a fix, attach it to the ticket, or read it later if the box gets
rebooted.

```bash
sudo -i        # run the block as root
OUT=/var/tmp/slow-$(hostname)-$(date +%Y%m%d-%H%M%S).txt
{
  date; uptime; nproc
  head -n 2 /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
  dmesg -T | tail -40
  vmstat -w 1 5
  mpstat -P ALL 1 3
  pidstat -l 1 3
  iostat -xyz 1 3
  free -m
  sar -n DEV 1 3
  sar -n TCP,ETCP 1 3
  top -b -n 1 -o %CPU | head -30
  ps -eo pid,ppid,user,state,%cpu,%mem,rss,wchan:24,etime,args --sort=-%cpu | head -40
  df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay
} > "$OUT" 2>&1
echo "saved $OUT"
```

→ Takes about 20 seconds. Run it once on a **healthy** day too, and keep that
file as your baseline. You cannot recognise abnormal if you have never seen
normal.

### Step 1 — Load average and its trend

**Goal:** see whether the machine is overloaded right now, and whether it is
getting worse or better.

```bash
uptime
nproc                  # number of CPUs to compare the load with
cat /proc/loadavg      # same three numbers, plus runnable/total tasks and the last PID
```

```
 10:42:17 up 23 days,  4:11,  2 users,  load average: 7.82, 5.10, 2.31
4
7.82 5.10 2.31 9/431 51877
```

**What it means:**

- The three numbers are exponentially damped averages over 1, 5 and 15 minutes.
- On Linux, load counts tasks that are **running or waiting for a CPU, plus tasks in uninterruptible sleep (state D)**, which are usually waiting on disk or NFS. High load therefore does not prove a CPU problem.
- 7.82 on 4 CPUs means about two tasks for every CPU.
- 1-minute (7.82) much higher than 15-minute (2.31): the problem started within the last 10–15 minutes and is still climbing. That matches "slow since 10:30".
- `9/431`: 9 tasks runnable at this instant, out of 431 (threads included).
- Good: load at or below `nproc` and flat. Bad: load well above `nproc` and rising. If the 15-minute value is high but the 1-minute value is low, the peak has passed.

**Why this step (now):** it costs nothing and answers two questions that shape
the rest: is the problem happening now (so you can observe it live), and is it
growing. It cannot tell you which resource is the cause, so you never stop here.

**Next step:** in almost every case → Step 2. If load is near zero and the
service is still slow, the box is probably waiting on something else
(database, upstream API, DNS): measure with `curl -w` (section 1) and go to
section 7 or Step N1. If the peak has passed → finish the checklist quickly,
then go to section 8 for history.

### Step 2 — Kernel messages

**Goal:** catch the loud failures first: OOM kills, disk errors, hung tasks,
dropped packets, thermal throttling.

```bash
sudo dmesg -T | tail -20                       # Ubuntu restricts dmesg to root
sudo dmesg -T --level=err,warn | tail -20      # only warnings and errors
sudo journalctl -k --since "1 hour ago" --no-pager | tail -20   # same messages, via the journal
```

```
[Sat Oct  3 10:31:02 2026] INFO: task jbd2/dm-0-8:398 blocked for more than 120 seconds.
[Sat Oct  3 10:31:02 2026]       Not tainted 5.15.0-122-generic #132-Ubuntu
[Sat Oct  3 10:31:02 2026] "echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
[Sat Oct  3 10:31:02 2026] task:jbd2/dm-0-8     state:D stack:    0 pid:  398 ppid:     2 flags:0x00004000
```

**What it means:**

- `jbd2/dm-0-8` is the ext4 journal thread for the root logical volume (`dm-0`). It has been stuck in state D (waiting for I/O) for over two minutes. Writes to that filesystem are taking far too long.
- A hung-task warning is a **symptom**. The disk might be failing, saturated by another process, or flooded with swap traffic. Keep going; Steps 3 and 6 will say which.
- `-T` converts timestamps to wall-clock time. They can be slightly off on a VM that was paused or migrated.
- Good: nothing new since boot. Bad: any of the lines in the table below.

| Message contains | Meaning | Go to |
|---|---|---|
| `Out of memory: Killed process` | the whole host ran out of memory | Step M4 |
| `Memory cgroup out of memory` | one container or service hit its memory limit | Step M4, section 12 |
| `blocked for more than 120 seconds` | a task stuck in D state | Step D3 |
| `I/O error`, `ata... failed command`, `nvme... timeout` | storage errors | Step D8 |
| `nf_conntrack: table full, dropping packet` | connection tracking table full | Step N2 |
| `Possible SYN flooding on port` | a listen queue overflowing | Step A5 |
| `soft lockup`, `rcu_sched self-detected stall` | a CPU stuck, often a starved VM | section 13 |
| `temperature above threshold, cpu clock throttled` | thermal throttling | Step C9 |
| `link is down`, `NETDEV WATCHDOG` | NIC problems | [Network speed](24-playbook-network-speed.md) |

**Why this step (now):** kernel messages are rare and high-signal. One OOM line
or one I/O error can end the investigation in ten seconds, and it is cheaper to
read them than to infer the same thing from statistics.

**Next step:** OOM kill → Step M4. I/O errors → Step D8. Conntrack full → Step
N2. Hung tasks only → note them and continue with Step 3 (expect a disk or
memory story). Nothing relevant → Step 3.

### Step 3 — vmstat: the whole machine, one line per second

**Goal:** split the problem into CPU, memory or I/O in five seconds.

```bash
vmstat 1 5        # 5 samples, 1 s apart. IGNORE the first line: it is the average since boot
vmstat -w 1 5     # wide output when the numbers are large
```

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  4 1669120 145620   2104 1008840  41  112  2210   960  612 1180 14  7 48 31  0
 5  3 1672704 139876   2104 1006120 1844 5212 9180  6412 2311 3920 18 11 33 38  0
 4  5 1680896 141204   2096 1001844 2216 6940 10452 7380 2490 4105 16 12 30 42  0
 6  3 1686016 137512   2096  998432 1912 5128 8876  5560 2207 3790 19 10 35 36  0
 5  4 1690112 136900   2096  995120 2004 5880 9310  6020 2302 3866 17 11 33 39  0
```

**What it means** (skip line 1, read lines 2–5):

- `r` 4–6: runnable tasks (running plus waiting for a CPU). Compare with 4 CPUs: slightly above, not dramatic.
- `b` 3–5: tasks blocked in uninterruptible sleep, waiting on I/O. Healthy is 0.
- `swpd` about 1.6 GB of swap in use (KiB), and growing.
- `si` / `so` around 2 MB/s swapped **in** and 5–7 MB/s swapped **out**, every second. That is active swapping in both directions: pages written out are needed again moments later. This is the most important number on the screen.
- `free` about 140 MB and `cache` shrinking: the kernel is squeezing the page cache to find memory.
- `bi` / `bo`: KiB/s read from and written to block devices. Busy.
- `in` / `cs`: interrupts and context switches per second. Only meaningful against your baseline.
- `us` 17, `sy` 11: CPU doing real work is moderate. `id` 33: a third of CPU time is idle.
- `wa` 36–42: CPUs idle **while I/O is outstanding**. `st` 0: no hypervisor steal.
- On Ubuntu 24.04 you may see an extra `gu` (guest) column at the end.

Verdict for `web01`: memory pressure (si/so), causing swap I/O (bi/bo, wa),
causing blocked tasks (b), causing load. The CPU itself is not saturated.

| Pattern in vmstat | Likely bottleneck | Go to |
|---|---|---|
| `r` well above CPU count, `us + sy` near 100, `wa` near 0 | CPU | Section 3 |
| `sy` above 20–30 | kernel work: syscalls, locks, interrupts | Step C6 |
| `b` above 0 and `wa` high, `si`/`so` zero | disk or NFS | Section 5 |
| `si`/`so` non-zero for several seconds | memory | Section 4 |
| `st` above 5–10 | hypervisor steal | Step C8, section 13 |
| everything quiet | not this box, or the app is waiting on something | Section 7, Step N1 |

> `wa` is a kind of idle time, and it is diluted across all CPUs. On a 32-core
> host, one thread stuck on a slow disk barely moves it. Low `wa` does not prove
> the disks are fine; `iostat` (Step 6) and PSI (Step M3) do.

**Why this step (now):** one cheap tool covers CPU, memory, I/O and
virtualisation at one-second resolution. After five lines you know which of
the deep-dive sections matters, so every later step is targeted.

**Next step:** `si`/`so` non-zero → keep going through Steps 4–10 quickly
(they will confirm), then section 4. `wa` and `b` high without swapping → Step
6, then section 5. `r` high with `id` near 0 → Steps 4 and 5, then section 3.
`st` high → Step C8.

### Step 4 — mpstat: all cores busy, or just one?

**Goal:** see the load per CPU, because averages hide one pinned core.

```bash
mpstat -P ALL 1 3
```

```
Linux 5.15.0-122-generic (web01)    10/03/2026    _x86_64_    (4 CPU)

10:42:31     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
10:42:32     all   16.92    0.00   10.77   36.41    0.00    0.51    0.00    0.00    0.00   35.39
10:42:32       0   15.31    0.00   11.22   38.78    0.00    1.02    0.00    0.00    0.00   33.67
10:42:32       1   19.00    0.00    9.00   35.00    0.00    0.00    0.00    0.00    0.00   37.00
10:42:32       2   16.16    0.00   12.12   34.34    0.00    1.01    0.00    0.00    0.00   36.36
10:42:32       3   17.17    0.00   10.10   37.37    0.00    0.00    0.00    0.00    0.00   35.35
```

**What it means:**

- All four cores look alike: about 17% user, 11% system, 36% iowait, 35% idle. The load is spread evenly, so there is no single-thread bottleneck, and every core is waiting on I/O.
- `%soft` and `%irq` near 0: no interrupt storm.
- `%steal` 0: the hypervisor is not taking CPU away.

Compare a **single-thread bottleneck** on the same box on another day:

```
10:42:32     all   26.10    0.00    0.75    0.00    0.00    0.25    0.00    0.00    0.00   72.90
10:42:32       0    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00   97.00
10:42:32       1    1.01    0.00    1.01    0.00    0.00    1.01    0.00    0.00    0.00   96.97
10:42:32       2  100.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00
10:42:32       3    1.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00   98.00
```

→ The average says 26% busy; CPU 2 is at 100% user. Something single-threaded
(a Node.js main thread, Redis, a Python process without workers, a PHP cron
script, `gzip`) is maxed out. More cores will not help it.

**Why this step (now):** `vmstat` and `top`'s summary line average across
cores. Imbalance changes the whole diagnosis (parallelise or speed up one
thread, instead of adding capacity), and you can only see it per CPU.

**Next step:** one core at 100% `%usr` → Step C2 and Step C4. One core high in
`%soft` or `%irq` → section 15. All cores high `%usr` → Step 5, then section 3.
High `%iowait` everywhere (our story) → Step 5, then Step 6.

### Step 5 — pidstat: which processes use the CPU

**Goal:** put names on the CPU usage, per second.

```bash
pidstat 1 5        # per-process CPU each second; only processes active in the interval
pidstat -l 1 5     # same, with the full command line (tells apart java apps and PHP pools)
```

```
10:42:40      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
10:42:41        0        97    0.00   18.81    0.00    0.00   18.81     2  kswapd0
10:42:41     1001      2817   31.68    4.95    0.00    6.93   36.63     1  java
10:42:41       33     41522    5.94    1.98    0.00    1.98    7.92     3  apache2
10:42:41       33     41530    4.95    0.99    0.00    0.99    5.94     0  apache2
10:42:41        0      1187    1.98    0.99    0.00    0.00    2.97     0  dockerd
10:42:41        0      1544    0.99    0.99    0.00    0.00    1.98     2  traefik
```

**What it means:**

- `%CPU` is a percentage of **one** CPU. A multi-threaded process can show 250%.
- `%wait` is time the task was runnable but **waiting for a CPU** (run-queue delay). It is not I/O wait. Here it is small, which agrees with Step 3: the CPU is not the bottleneck.
- `kswapd0` at 19% system time: the kernel's memory-reclaim thread is working hard. That alone confirms memory pressure.
- `java` (PID 2817) at 37%, owned by UID 1001. `pidstat` always prints numeric UIDs (add `-U` for user names); in `top` and `ps`, a UID that stays numeric usually means a container user that does not exist in the host's `/etc/passwd`.
- `apache2` processes run as UID 33 (`www-data`). `traefik` and `dockerd` are quiet.
- Good: CPU users you expect, at levels you expect. Bad: a kernel thread (`kswapd0`, `ksoftirqd/N`, `kworker`) near the top, or one process near 100% × its thread count.

**Why this step (now):** it turns "the CPU is busy" into a name, prints a
per-second record you can paste into a ticket, and exposes kernel threads that
point straight at a subsystem (`kswapd` = memory, `ksoftirqd` = interrupts,
`jbd2` = filesystem journal).

**Next step:** `kswapd0` high → memory (Step 7, then section 4). One process
dominating → Step C3. CPU busy but no process stands out (many short-lived
processes) → section 14, Step 4. Otherwise → Step 6.

### Step 6 — iostat: disk latency, queue and utilisation

**Goal:** find which device is slow, and whether the problem is latency,
queueing or throughput.

```bash
iostat -xyz 1 3     # -x extended, -y skip the since-boot report, -z hide idle devices
iostat -xyzN 1 3    # -N shows LVM names (ubuntu--vg-ubuntu--lv) instead of dm-0
lsblk               # map sda / dm-0 / nvme0n1 to filesystems
```

```
Linux 5.15.0-122-generic (web01)    10/03/2026    _x86_64_    (4 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
          16.42    0.00   10.80   36.95    0.00   35.83

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     f/s f_await  aqu-sz  %util
dm-0           514.00   9196.00     0.00   0.00   19.10    17.89  414.00   6440.00     0.00   0.00   43.22    15.56    0.00    0.00   27.71 100.00
sda            512.00   9180.00     0.00   0.00   18.42    17.93  402.00   6412.00    12.00   2.90   41.77    15.95    6.00   38.50   26.43 100.00
```

(The discard columns `d/s` … `dareq-sz` are removed here for width.)

**What it means:**

- `dm-0` is the LVM volume on top of `sda`. The same I/O is counted at both layers; look at the physical device for the hardware picture.
- `r/s` 512, `w/s` 402: about 900 I/O operations per second.
- `rareq-sz` / `wareq-sz` around 16–18 KB: small, random requests. Swap and page-fault traffic looks like this. A backup or a file copy would show 128 KB or more.
- `r_await` 18 ms and `w_await` 42 ms: average time per request, including time queued in the kernel. For an SSD-backed VM disk, healthy is 0.1–2 ms; 18–42 ms is terrible. (A spinning disk is normally 5–15 ms.)
- `aqu-sz` 26: on average 26 requests in flight. The device is queueing.
- `%util` 100: the device had at least one request in flight all the time. On SSDs and RAID this number can lie (section 5), but here latency and queue are also bad, so the disk really is saturated.
- `f/s`, `f_await`: flush requests (from `fsync`) and their latency. They matter for databases (Step D5).

**Why this step (now):** Step 3 showed I/O wait and blocked tasks. `iostat`
names the device and separates "slow per request" (await) from "too many
requests" (queue, IOPS) from "too much data" (kB/s), which lead to different
fixes.

**Next step:** small random I/O while `si`/`so` are non-zero (our story) → the
I/O is caused by swapping; Step 7, then section 4. Large I/O with no swapping
→ Step D2 to find the process. High await with low IOPS → Step D6 (cloud
limits) or Step D8 (failing disk). All devices healthy → Step 7.

### Step 7 — free: memory headroom

**Goal:** see how much memory is really available, and how much swap is in
use.

```bash
free -m
free -m -s 2 -c 3     # three samples, two seconds apart
```

```
               total        used        free      shared  buff/cache   available
Mem:            7941        6812         142          45         986         812
Swap:           2047        1630         417
```

**What it means:**

- `free` (142 MB) being low is normal on Linux: spare RAM is used as page cache. Ignore it.
- `available` (812 MB, about 10% of RAM) is the kernel's estimate of memory that can be handed to programs without swapping. This is the number that matters. Below about 10% while swapping actively is real pressure.
- `buff/cache` 986 MB: page cache that has already been squeezed hard. On this box it is normally 3–4 GB.
- `Swap used` 1.6 GB on its own proves nothing; old idle pages can sit in swap for weeks. Together with the `si`/`so` activity from Step 3 it means **thrashing**.
- The `used` column is computed slightly differently by newer procps (Ubuntu 24.04: `used = total − available`). Always read `available`.

**Why this step (now):** Steps 3, 5 and 6 all pointed at memory (`si`/`so`,
`kswapd0`, small random I/O). `free` confirms the shortage in plain numbers
before you spend time on the disk.

**Next step:** low `available` and active swapping → finish Steps 8–10, then
section 4 (Step M5: who holds the memory). Plenty available → the I/O comes
from somewhere else; go to Step D2.

### Step 8 — sar -n DEV: network throughput per interface

**Goal:** rule a saturated network interface in or out.

```bash
sar -n DEV 1 3
ethtool ens3 | grep -i speed      # link speed; virtio NICs often report "Unknown!"
```

```
10:43:10        IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil
10:43:11           lo     41.00     41.00      6.12      6.12      0.00      0.00      0.00      0.00
10:43:11         ens3   1812.00   2104.00    1820.44   9310.71      0.00      0.00      0.00      7.63
10:43:11      docker0      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
10:43:11 docker_gwbridge    96.00    102.00     38.20    410.66      0.00      0.00      0.00      0.00
```

**What it means:**

- `ens3` transmits about 9.3 MB/s (≈ 76 Mbit/s) on a 1 Gbit/s link: about 8%. Nowhere near saturation.
- `%ifutil` is only computed when the kernel knows the link speed. On virtio NICs it often shows 0.00; compute it yourself: sar's kB is 1024 bytes, so kB/s × 8.192 ÷ 1000 = Mbit/s (× 8 ÷ 1000 is close enough), compared with the link or the cloud instance's bandwidth limit.
- `docker_gwbridge` carries traffic for Swarm services (Dokploy). `veth...` interfaces appear for each container.
- Good: well below line rate. Bad: near line rate, or `rxpck/s` far above your baseline (a packet flood).

**Why this step (now):** a saturated link makes everything slow and is cheap
to rule out. It also gives you the current traffic level to compare with your
baseline ("is it simply more traffic than usual?").

**Next step:** an interface near line rate → [Network speed playbook](24-playbook-network-speed.md).
Otherwise → Step 9.

### Step 9 — sar -n TCP,ETCP: connection rate and retransmits

**Goal:** see the connection rate and whether TCP is losing packets.

```bash
sar -n TCP,ETCP 1 3
```

```
10:43:20     active/s passive/s    iseg/s    oseg/s
10:43:21         4.00     38.00   2611.00   3104.00

10:43:20     atmptf/s  estres/s retrans/s isegerr/s   orsts/s
10:43:21         0.00      1.00      2.00      0.00      3.00
```

**What it means:**

- `active/s` 4: outbound connections opened by this host (to databases, APIs).
- `passive/s` 38: inbound connections accepted. Roughly the new-connection rate from clients. Compare with your baseline to spot a traffic surge or a crawler.
- `retrans/s` 2 of `oseg/s` 3104: a retransmit ratio of about 0.06%. Healthy. Above about 1% is worth a look; several percent hurts latency badly.
- `atmptf/s`: failed outbound connection attempts (for example a database refusing connections).
- `estres/s`, `orsts/s`: resets of established connections and RSTs sent. A spike in `orsts/s` can mean a full listen queue or a closed port.

**Why this step (now):** retransmits add hundreds of milliseconds per lost
packet and are invisible in CPU or disk numbers. The connection rate tells you
whether load itself changed.

**Next step:** retransmits above about 1% → Step N3. `passive/s` far above
baseline → traffic surge; check the top client IPs (Step A10). Otherwise →
Step 10.

### Step 10 — top or htop: confirm and look around

**Goal:** see everything at once, sorted by the resource your evidence points
to, and catch anything the previous steps missed.

```bash
top                                  # keys: 1 per-CPU, M sort by memory, P by CPU, c full command, H threads
top -b -n 1 -o %MEM | head -20       # batch mode, sorted by memory; paste into the ticket
htop                                 # F2 → Display options → "Detailed CPU time" shows wa/st/irq
```

```
top - 10:43:31 up 23 days,  4:12,  2 users,  load average: 7.91, 5.44, 2.60
Tasks: 213 total,   3 running, 210 sleeping,   0 stopped,   0 zombie
%Cpu(s): 17.1 us, 10.2 sy,  0.0 ni, 34.9 id, 37.3 wa,  0.0 hi,  0.5 si,  0.0 st
MiB Mem :   7941.6 total,    139.8 free,   6813.4 used,    988.4 buff/cache
MiB Swap:   2048.0 total,    417.9 free,   1630.1 used.    811.9 avail Mem

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
   2817 1001      20   0 7612344   4.9g  21480 S  35.8  63.4 412:51.07 java
   1931 root      20   0 1302144 251880  41212 S   1.3   3.1  58:12.90 node
   1187 root      20   0 2384116 118204  38916 S   2.0   1.5 911:40.22 dockerd
   1602 999       20   0  221436 104320  98112 S   0.3   1.3  12:03.51 postgres
   1544 root      20   0 1271956  86412  52104 S   1.0   1.1 132:18.04 traefik
  41522 www-data  20   0  412880  61204  31120 D   7.9   0.8   0:41.13 apache2
  41530 www-data  20   0  410512  58876  30988 S   5.9   0.7   0:39.80 apache2
```

**What it means:**

- The header repeats Steps 1, 3 and 7: load about 8, 37% wa, 812 MB available, 1.6 GB swap used.
- `RES` is resident memory (real RAM in use). `VIRT` is address space and is usually meaningless (JVMs reserve gigabytes they never touch).
- `java` (PID 2817) holds 4.9 GB, 63% of RAM, on an 8 GB host that also runs Apache, Docker, Traefik and Dokploy (`node`, `postgres`).
- `S` column: `D` means the process is in uninterruptible sleep right now (here an Apache worker waiting on disk). `R` is running, `S` sleeping, `Z` zombie.
- `TIME+` is total CPU time since the process started.

**Story verdict for `web01`:** `java` (PID 2817, a container) holds 4.9 GB on
an 8 GB host → the host swaps → swap I/O saturates `sda` → I/O wait, blocked
tasks, a hung journal thread and a load of 8 → every request is slow. Next:
section 4, Step M5 (why is java that big, and which container is it?).

**Why this step (now):** `top` is where most people start, but it is easier to
read once you know what you are looking for. Sorting by the suspect resource
turns the earlier clues into a culprit, and the full view catches surprises
(zombies, a forgotten `tar`, a D-state process).

**Next step:** a memory hog → Step M5. A CPU hog → Step C3. D-state processes
→ Step D3. Nothing stands out and the evidence is mixed → section 18 (master
decision tree).

### Checklist wrap-up: tree, verify, prevent

```
60-second checklist → what did it show?
├── dmesg: OOM / I/O errors / conntrack full ─→ M4 / D8 / N2 (shortcut)
├── vmstat si/so > 0, kswapd busy, available low ─→ Section 4 (memory)
├── vmstat wa + b high, iostat await/aqu-sz high ─→ Section 5 (disk)
├── vmstat r > CPUs, id ≈ 0 ─────────────────────→ Section 3 (CPU)
│     └── mpstat: one core 100% ─────────────────→ C2 / C4 (single thread)
├── vmstat st > 5–10 ─────────────────────────────→ C8 / Section 13 (steal)
├── mpstat %soft high on one core ────────────────→ Section 15 (interrupts)
├── sar retrans > 1%, link near line rate ────────→ Section 6 / module 24
└── everything quiet but requests slow ───────────→ Section 7 (application), N1 (DNS)
```

**Fix & verify:** the checklist itself changes nothing. After whatever fix the
deep-dive section leads to, re-run the snapshot from "Save a snapshot before
you dig" and compare it line by line with the one you took at the start, and
re-run the `curl -w` measurement from section 1. "It feels faster" is not
verification.

**Rollback:** not applicable; every command here is read-only.

**Prevent it next time:**

- Keep `sysstat` collection and `atop` logging on everywhere (Steps H1, H2), so "what happened at 02:10" has an answer.
- Save a healthy-day snapshot for each server and keep it with the runbook.
- Alert on saturation, not just utilisation: PSI, swap activity, disk await, retransmits (section 19).
- Practise the checklist in the homelab until you can read all ten outputs without notes (section 20).

---

## 3. CPU-bound slowness

> 📚 **Study path:** 1) Note: [Learn: performance & observability](32-learn-performance-observability.md), section 4 (CPU deep dive) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes (`top`, `nice`, signals; [lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) · 3) KodeKloud: *Docker Certified Associate* — Docker Engine – Security → resource limits and cgroups, for Step C7 ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 5) Practice: section 20, drills 1 and 4 (a CPU hog, then a throttled container), and a flame graph from [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html).

**Level:** [L2 · Mid] for Steps C1–C4 and C8; [L3 · Senior] for perf and
flame graphs (C5), syscall analysis (C6), cgroup throttling (C7) and bare-metal
thermal work (C9). A Junior should get as far as C3 and hand over the evidence.

You are here because `vmstat` showed `r` above the CPU count with `id` near 0,
or `mpstat` showed a pinned core, or `pidstat` showed one process eating the
machine. The example in this section is a different morning on `web01`: the
`shop.example.com` vhost (Apache with mod_php) becomes slow while a crawler
hammers its search page.

### Read the CPU split: us, sy, wa, st, si

Every CPU tool (`top`, `vmstat`, `mpstat`, `sar -u`) splits CPU time the same
way. Learn the fields once:

| Field | What the CPU was doing | When it is high, suspect | Next |
|---|---|---|---|
| `us` (`%usr`) | running application code | busy loops, regex, compression, crypto, GC, template rendering | Steps C3–C5 |
| `ni` (`%nice`) | running niced (low-priority) code | batch jobs you already deprioritised; usually harmless | Step C3 |
| `sy` (`%sys`) | running kernel code for processes | syscall storms, context switches, lock contention, page faults | Step C6 |
| `wa` (`%iowait`) | idle, with I/O outstanding | disk or NFS (not a CPU problem) | Section 5 |
| `hi` (`%irq`) | hardware interrupt handlers | NIC or storage interrupt storms | Section 15 |
| `si` (`%soft`) | softirq processing (network stack, timers, block completion) | packet floods, one NIC queue on one core | Section 15 |
| `st` (`%steal`) | your vCPU wanted to run, the hypervisor ran someone else | overcommitted host, AWS burstable credits exhausted | Step C8, section 13 |
| `id` (`%idle`) | nothing to do | (good) | |

In `top`'s process list, 100% means one full core, so a 4-core box can show a
process at 400%.

### Step C1 — Run queue versus cores

**Goal:** prove that the CPU is **saturated** (work waiting), not merely busy.

```bash
nproc
vmstat 1 5
cat /proc/pressure/cpu
```

```
4
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 9  0  10240 2214400 98112 3611204   0    0    12   140 4120 8810 71  8 21  0  0
14  0  10240 2209812 98112 3611320   0    0     0   212 6811 15240 88  9  3  0  0
17  0  10240 2205100 98112 3611388   0    0     0   180 7012 16102 90 10  0  0  0
15  0  10240 2201880 98120 3611412   0    0     4   244 6934 15870 89  9  2  0  0
16  0  10240 2199440 98120 3611460   0    0     0   196 7101 16330 89 10  1  0  0
some avg10=71.42 avg60=54.10 avg300=22.87 total=812345678
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

**What it means:**

- `r` 14–17 on 4 CPUs: about four runnable tasks per core. Each one gets roughly a quarter of a CPU, so CPU-heavy requests take about four times longer than on an idle box.
- `us` 89, `sy` 10, `id` 0–3, `wa` 0, `si`/`so` 0: pure CPU work, no memory or I/O involvement.
- PSI `some avg10=71.42`: in the last 10 seconds, at least one task was waiting for a CPU 71% of the time. The `avg300` of 23 shows it ramped up within the last few minutes.
- The system-wide `full` line for CPU is always zero; it only has meaning per cgroup.
- Good: `r` at or below the core count, PSI cpu `some` below about 5%. Bad: `r` well above the cores for minutes, PSI cpu `some` above about 20–25%.

**Why this step (now):** 90% utilisation with a short run queue is a healthy,
well-used machine. 90% with four tasks waiting per core is queueing, and
queueing is what users feel as latency. Proving saturation first stops you
from "optimising" a CPU that was never the bottleneck.

**Next step:** saturated → Step C2. `r` normal but one process is slow → Step
C4 (single thread) or section 7 (it is waiting, not computing).

### Step C2 — One core pinned or all cores busy

**Goal:** decide between "not enough CPU in total" and "one thread is the
limit".

```bash
mpstat -P ALL 1 3
```

```
11:02:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
11:02:02     all   88.75    0.00    9.50    0.00    0.00    0.50    0.00    0.00    0.00    1.25
11:02:02       0   87.00    0.00   11.00    0.00    0.00    1.00    0.00    0.00    0.00    1.00
11:02:02       1   90.00    0.00    9.00    0.00    0.00    0.00    0.00    0.00    0.00    1.00
11:02:02       2   89.11    0.00    8.91    0.00    0.00    0.99    0.00    0.00    0.00    0.99
11:02:02       3   88.89    0.00    9.09    0.00    0.00    0.00    0.00    0.00    0.00    2.02
```

**What it means:**

- All four cores are at about 89% user. The work is parallel and there is simply more of it than the CPUs can do. The fix is less work (block, cache, rate-limit), cheaper work (fix the code) or more CPU.
- If instead one core showed 100% `%usr` and the others idled (see the contrast output in Step 4), the limit is a single thread: more cores will not help. You need to make that thread faster or split its work.
- If one core showed high `%soft` or `%irq`, the "CPU problem" is really interrupt handling (section 15).

**Why this step (now):** the two cases have opposite fixes. Scaling a VM from
4 to 8 vCPUs does nothing for a single-threaded bottleneck, and parallelising
code does nothing for a box that is simply out of CPU.

**Next step:** all cores busy → Step C3. One core pinned → Step C3 to name the
process, then Step C4 to find the thread.

### Step C3 — Find the hot process (and the vhost or container)

**Goal:** name the service, the process and, on a shared box, the vhost or
container responsible.

```bash
systemd-cgtop -n 2 -d 1 --depth 3   # CPU per service / container cgroup (sorted by CPU); read the 2nd pass:
                                    # CPU % needs two samples, so a single pass (-n 1) shows "-"
pidstat -l 1 5                      # per process, with full command lines
ps -eo pid,user,%cpu,etime,args --sort=-%cpu | head -12   # NOTE: ps %cpu = lifetime average
docker stats --no-stream            # per container
# Which Apache vhost? (mod_status with ExtendedStatus; Ubuntu allows it from localhost only)
sudo apt install lynx               # apache2ctl fullstatus needs a text browser
sudo apache2ctl fullstatus | grep -E '^ *[0-9]+-[0-9]+ ' | sort -k5 -rn | head
```

```
Control Group                                       Tasks   %CPU   Memory  Input/s Output/s
/                                                     612  389.2     5.6G        -        -
/system.slice                                         498  381.0     5.1G        -        -
/system.slice/apache2.service                         157  342.7     1.3G        -        -
/system.slice/docker-3f1c2a9e5b7d...scope              41   21.4   612.0M        -        -
/system.slice/docker.service                           28    6.3   201.4M        -        -
/user.slice                                            14    1.2   118.0M        -        -

   Srv  PID    Acc         M  CPU     SS  Req   Dur   Conn  Child  Slot   Client          Protocol  VHost                 Request
  12-0  41611  0/88/1203   W  61.40   41    0  98112   0.0   0.94  18.11  198.51.100.23   http/1.1  shop.example.com:443  GET /search?q=%25a%25b%25c&sort=price HTTP/1.1
  17-0  41622  0/91/1311   W  58.77   39    0  95120   0.0   0.91  17.80  198.51.100.23   http/1.1  shop.example.com:443  GET /search?q=%25x%25y&sort=name HTTP/1.1
   4-0  41530  0/12/980    W  12.02    3    0   4012   0.0   0.12   9.40  203.0.113.41    http/1.1  blog.example.com:443  GET /feed HTTP/1.1
```

**What it means:**

- `systemd-cgtop` sums CPU per cgroup: `apache2.service` uses 343% of the 400% available. Docker containers appear as `docker-ID.scope`. This is the fastest way to answer "which service?" on a shared box.
- `ps` `%cpu` is CPU time divided by the process's lifetime, so a process that just started spinning shows a low value. Use `pidstat` or `top` for current usage.
- Apache's scoreboard: `M` = W means "sending reply" (busy). `CPU` is CPU seconds used by that worker. `SS` is seconds since the request started. `VHost` and `Request` say exactly what each worker is doing.
- Most busy workers serve `GET /search?...` on `shop.example.com` for the same client IP, 198.51.100.23, and have been at it for about 40 seconds each. That is one expensive endpoint being hammered by one client (a crawler or a scraper).
- Apache's `ExtendedStatus` is on by default in 2.4 when `mod_status` is loaded. On Ubuntu, `mod_status` only answers requests from localhost.

**Why this step (now):** on a box with several vhosts and containers, "Apache
is hot" is not actionable. "One client hits `/search` on the shop vhost" is: you
can rate-limit it, block it, or hand the endpoint to the developers with
evidence. Cgroups and mod_status give that answer without attaching any tracer.

**Next step:** an abusive client → fix in "CPU wrap-up" (block or rate-limit),
then verify. Your own code is genuinely CPU-hungry → Step C4 and Step C5. The
hot process is a container → also check Step C7 (throttling). A kernel thread
is hot (`ksoftirqd`, `kswapd`, `kworker`) → section 15, section 4 or Step C6.

### Step C4 — Find the hot thread

**Goal:** inside a multi-threaded process, find which thread burns the CPU,
and for Java, map it to a stack trace.

```bash
top -H -p PID                      # threads of one process, sorted by CPU
pidstat -t -p PID 1 5              # same, per second, with thread IDs (TID)

# Java: convert the hot TID to hex and find it in a thread dump
printf 'nid=0x%x\n' TID
sudo -u APPUSER jstack PID > /var/tmp/jstack.txt              # JVM on the host
docker exec CONTAINER jstack 1 > /var/tmp/jstack.txt          # JVM as PID 1 in a container
grep -A 12 -E 'nid=(0xHEX|TID)[^0-9a-f]' /var/tmp/jstack.txt
```

```
11:08:11      UID      TGID       TID    %usr %system  %guest   %wait    %CPU   CPU  Command
11:08:12     1001      2817         -   99.00    1.00    0.00    0.00  100.00     2  java
11:08:12     1001         -      2851   98.00    1.00    0.00    0.00   99.00     2  |__http-nio-8080-e
11:08:12     1001         -      2830    1.00    0.00    0.00    0.00    1.00     0  |__GC Thread#0
11:08:12     1001         -      2836    0.00    0.00    0.00    0.00    0.00     1  |__C2 CompilerThre

nid=0xb23

"http-nio-8080-exec-7" #41 daemon prio=5 os_prio=0 cpu=812345.12ms elapsed=9123.45s tid=0x00007f3a2c0b9800 nid=0xb23 runnable  [0x00007f39f4dfa000]
   java.lang.Thread.State: RUNNABLE
        at java.util.regex.Pattern$Loop.match(Pattern.java:5061)
        at java.util.regex.Pattern$GroupTail.match(Pattern.java:4863)
        at java.util.regex.Pattern$Curly.match0(Pattern.java:4320)
        at java.util.regex.Matcher.find(Matcher.java:745)
        at com.example.shop.SearchService.filter(SearchService.java:118)
        at com.example.shop.SearchController.search(SearchController.java:54)
```

**What it means:**

- One thread (TID 2851, a Tomcat request thread `http-nio-8080-exec-7`; thread names are cut to 15 characters) uses a whole core. GC and JIT compiler threads are quiet.
- 2851 in hex is `0xb23`. Older JDKs print `nid` in hex; JDK 19 and later print it in decimal (`nid=2851`), which is why the `grep` above accepts both.
- The stack shows the thread deep inside `java.util.regex` called from `SearchService.filter` line 118: a regular expression with catastrophic backtracking on certain input. That is the bug report for the developers, with the exact line.
- If `GC Thread#N` threads were the hot ones, the problem would be garbage collection (Step A7), not your code. Hot `C2 CompilerThre` threads for a few minutes after a deploy are normal JIT warm-up.

**Why this step (now):** process-level CPU says which application. Thread-level
CPU says which code path (request handling, GC, JIT, a background job), which
decides who has to fix it and how. For Java the TID → `nid` mapping gets you
from "java uses 100%" to a line number in two commands, without a profiler.

**Next step:** a request or worker thread → Step C5 to profile it properly (or
hand the stack to the developers). GC threads → Step A7. Not Java → Step C5
(perf) or Step A8 (py-spy for Python).

### Step C5 — Find the hot code with perf

**Goal:** sample where CPU time is spent at the function level, for any
process, including the kernel.

```bash
# One-time install on Ubuntu (perf must match the running kernel)
sudo apt install linux-tools-common linux-tools-$(uname -r)

sudo perf top -p PID                     # live: hottest functions of one process
sudo perf top                            # whole system, kernel included
# Record 30 s at 99 Hz with call stacks, then summarise
sudo perf record -F 99 -g -p PID -o /var/tmp/perf.data -- sleep 30
sudo perf report -i /var/tmp/perf.data --stdio --sort comm,dso,symbol | head -40
```

```
Samples: 112K of event 'cpu-clock:pppH', 4000 Hz, Event count (approx.): 28123456789 lost: 0/0 drop: 0/0
Overhead  Shared Object                 Symbol
  38.12%  libpcre2-8.so.0.10.4          [.] 0x000000000003c1a2
  14.77%  libphp8.1.so                  [.] execute_ex
   6.03%  libc.so.6                     [.] __memmove_avx_unaligned_erms
   3.88%  [kernel]                      [k] copy_user_enhanced_fast_string
   2.41%  libphp8.1.so                  [.] zend_hash_find
   1.96%  libphp8.1.so                  [.] zend_string_tolower_ex
```

**What it means:**

- `Overhead` is the share of CPU samples spent in that function. The top lines are where the time goes.
- 38% inside `libpcre2` (the regex library PHP uses) plus 15% in the PHP interpreter loop (`execute_ex`): the PHP version of the same story, an expensive regular expression in the search endpoint.
- A raw address instead of a name (`0x...3c1a2`) means the library has no symbols. Install the debug-symbol package if you need the exact function.
- `[.]` is user space, `[k]` is kernel. If `[k]` functions dominate, the time is `sy` time (Step C6).
- `cpu-clock:pppH` instead of `cycles`: this is a VM without hardware performance counters, so perf samples on a timer. That is fine for finding hot code.
- For interpreted or JIT languages, perf mostly shows the interpreter (`execute_ex` for PHP, JIT addresses for Java/Node). Use the language's own profiler for function names: py-spy (Python), async-profiler (Java), `node --cpu-prof` (Node.js).

**Flame graphs.** `perf report` is a long text tree. A **flame graph** draws
the same stacks as boxes: each box is a function, its width is the share of
samples it (and everything it called) was on-CPU, and boxes above it are the
functions it called. The x-axis is sorted alphabetically, not by time. Look
for the **widest boxes near the top**: that is where the CPU actually burns.
Generate one with Brendan Gregg's FlameGraph scripts (linked from his
[Linux performance page](https://www.brendangregg.com/linuxperf.html)):

```bash
sudo perf record -F 99 -a -g -o /var/tmp/perf.data -- sleep 30      # whole system, 30 s
sudo perf script -i /var/tmp/perf.data > /var/tmp/out.perf
./stackcollapse-perf.pl /var/tmp/out.perf | ./flamegraph.pl > /var/tmp/cpu-flame.svg
```

→ Open the SVG in a browser; it is interactive (click to zoom). Ubuntu 24.04
builds its packages with frame pointers, so stacks there are much more complete
than on 22.04.

> ⚠️ `perf` at 99 Hz costs very little, but `perf top` on a huge box and
> `perf record -a` for minutes can produce large files. Keep recordings short,
> write them to `/var/tmp`, and delete them afterwards. Inside a container,
> run perf on the **host** against the host PID.

**Why this step (now):** Step C4 shows *which thread*; perf shows *which
function*, works for any language and for the kernel, and its overhead is low
enough for production. It is the step that turns "CPU is high" into a
specific code change.

**Next step:** hot user-space code → hand the profile to the developers and
mitigate meanwhile (CPU wrap-up). Hot kernel functions → Step C6. Nothing hot
but the process is still slow → it is waiting, not computing: section 7.

### Step C6 — High system time: syscalls and context switches

**Goal:** explain a high `sy`: which process makes the kernel work, and on
what.

```bash
pidstat -w 1 5                          # context switches per process
sudo strace -c -f -p PID                # syscall summary; Ctrl-C after ~10 s (slows the process!)
sudo perf top --sort comm,symbol        # which kernel functions burn the sy time
```

```
11:15:20      UID       PID   cswch/s nvcswch/s  Command
11:15:21       33     41611    212.00   1904.00  apache2
11:15:21       33     41622    198.00   1877.00  apache2
11:15:21     1001      2817  18342.00    310.00  java

strace: Process 41611 attached
^Cstrace: Process 41611 detached
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 52.31    0.912345           3    281240    198112 newfstatat
 21.08    0.367611           2    150334    150101 openat
  9.77    0.170403           5     31221           read
  6.12    0.106742           4     24110           mmap
  4.40    0.076741           6     12804           munmap
  6.32    0.110369           2     52410           other
------ ----------- ----------- --------- --------- ----------------
100.00    1.744211           3    552119    348213 total
```

(The `other` row sums the remaining syscalls by hand for width; strace itself
lists every syscall on its own line.)

**What it means:**

- `cswch/s` are **voluntary** context switches: the thread gave up the CPU to wait (I/O, a lock, a sleep). Very high values with little CPU used (java, 18k/s) point to lock contention or chatty I/O (Step A9).
- `nvcswch/s` are **involuntary**: the thread was preempted because others wanted the CPU. High values mean CPU contention (Apache workers fighting for 4 cores).
- `strace -c`: in 10 seconds, one Apache worker made 281,000 `newfstatat` (stat) calls, 70% of them failing, and 150,000 failed `openat` calls. PHP is probing many paths for files that do not exist (a long `include_path`, an autoloader without a class map, a disabled realpath or opcache). That is `sy` time spent on nothing.
- In `perf top`, kernel symbols like `native_queued_spin_lock_slowpath` mean CPUs spinning on a kernel lock; `do_syscall_64` plus `__x64_sys_*` names mean plain syscall volume.

> ⚠️ `strace` stops the target at every syscall and can slow it 10–100×.
> Attach for seconds, not minutes, and prefer `perf trace -s -p PID` or
> `syscount-bpfcc -p PID` (from `bpfcc-tools`) on a busy production process.

**Why this step (now):** user-space profilers do not see kernel time. When
`sy` is a large share, the fix is usually in how the application calls the
kernel (caching, batching, fewer threads), and only syscall and switch counts
show that.

**Next step:** a syscall storm → fix the configuration (for PHP: enable
opcache, raise `realpath_cache_size`, use a classmap autoloader), then verify.
High voluntary switches with low CPU → Step A9. High `si` or `hi` → section 15.

### Step C7 — Container CPU throttling (cgroup v2)

**Goal:** detect a container (or systemd service) that is slow because it hits
its **CPU quota**, even while the host has idle CPU.

How it works: `docker run --cpus 1.5`, a Swarm service limit, or a Kubernetes
`limits.cpu` becomes a CFS bandwidth quota: "150 ms of CPU time per 100 ms
period". When the cgroup's threads use the quota up, **all of them are
stopped until the next period**. A service with 8 busy threads and a 1-CPU
limit burns its 100 ms of quota in 12.5 ms and then sits frozen for 87.5 ms.
Requests that happen to need CPU in that window wait, so p99 latency explodes
while average CPU looks modest.

```bash
stat -fc %T /sys/fs/cgroup              # cgroup2fs = cgroup v2 (Ubuntu 22.04+ default); tmpfs = v1

# Docker (cgroup v2 with the systemd driver): the container's cgroup directory
CID=$(docker inspect -f '{{.Id}}' CONTAINER)
CG=/sys/fs/cgroup/system.slice/docker-$CID.scope
cat $CG/cpu.max                         # quota and period in microseconds ("max" = unlimited)
cat $CG/cpu.stat                        # cumulative counters since the container started
sleep 10; grep -E 'nr_periods|nr_throttled|throttled_usec' $CG/cpu.stat   # read again and diff

# The same from inside the container (it sees its own cgroup as the root)
docker exec CONTAINER cat /sys/fs/cgroup/cpu.stat

# Configured limits: plain container, and Swarm service (Dokploy apps run as Swarm services)
docker inspect -f '{{.HostConfig.NanoCpus}} {{.HostConfig.CpuQuota}} {{.HostConfig.CpuPeriod}}' CONTAINER
docker service inspect --format '{{json .Spec.TaskTemplate.Resources}}' SERVICE
```

```
150000 100000
usage_usec 912345678
user_usec 801234567
system_usec 111111111
nr_periods 182340
nr_throttled 61877
throttled_usec 4123456789
nr_bursts 0
burst_usec 0
nr_periods 182440
nr_throttled 61911
throttled_usec 4125012345
1500000000 0 0
{"Limits":{"NanoCPUs":1500000000,"MemoryBytes":1073741824},"Reservations":{}}
```

**What it means:**

- `cpu.max` `150000 100000`: 150 ms of CPU per 100 ms period, which is 1.5 CPUs (`NanoCPUs` 1500000000 says the same).
- Since start, 61,877 of 182,340 periods (34%) were throttled, and the container spent about 4,123 seconds frozen in total.
- In the 10-second re-read, 34 of 100 periods were throttled: it is happening **now**, about a third of the time.
- Rule of thumb: more than about 5–10% of periods throttled on a latency-sensitive service is a visible latency problem, even if `docker stats` shows the container "only" at 1.4 CPUs.
- The Swarm service has a 1.5-CPU and 1 GiB limit set in its spec; that is where the quota comes from.

**Kubernetes:** the same counters live in the pod's cgroup on the node.

```bash
kubectl top pod POD -n NAMESPACE --containers                    # needs metrics-server
kubectl get pod POD -n NAMESPACE -o jsonpath='{.spec.containers[*].resources}'; echo
kubectl exec -n NAMESPACE POD -c CONTAINER -- cat /sys/fs/cgroup/cpu.stat
# Prometheus (cAdvisor metrics): fraction of periods throttled per container
#   rate(container_cpu_cfs_throttled_periods_total[5m]) / rate(container_cpu_cfs_periods_total[5m])
```

**A common cause: thread pools sized from the host's core count.** Inside a
container, `nproc` and many runtimes see all of the host's CPUs, not the
quota. An app that starts 16 worker threads (or nginx `worker_processes auto`,
gunicorn workers from the CPU count, older JVMs and Go runtimes) under a
1.5-CPU quota throttles constantly. Size workers to the quota explicitly
(for Java `-XX:ActiveProcessorCount=2`, for Go `GOMAXPROCS=2`). JDK 10 and
later and Go 1.25 and later read the cgroup CPU limit themselves, but only
for their own defaults; worker counts in the app's configuration still need
setting by hand.

**Why this step (now):** host-level tools say the machine has spare CPU, so
without this check you would conclude "not a CPU problem" and go hunting in the
application. Throttling is invisible everywhere except `cpu.stat` and the
latency graph.

**Next step:** throttled → raise or remove the CPU limit (keep the
reservation/request), or reduce worker threads; see "CPU wrap-up". Not
throttled but the container is still slower than the host → section 12. For
Kubernetes specifics → [Containers & Kubernetes playbook](26-playbook-containers-k8s.md).

### Step C8 — Steal time and burstable credits

**Goal:** detect a VM whose vCPUs are not getting the physical CPU they ask
for.

```bash
mpstat 1 5                 # %steal column
vmstat 1 5                 # st column

# AWS: which instance type is this? (IMDSv2)
TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type; echo

# T2/T3/T3a/T4g: credit mode and CPU credit balance over the last 12 hours
aws ec2 describe-instance-credit-specifications --instance-ids i-0123456789abcdef0
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUCreditBalance \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --start-time 2026-10-03T00:00:00Z --end-time 2026-10-03T12:00:00Z \
  --period 3600 --statistics Average --output text
```

```
11:20:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
11:20:02     all   18.03    0.00    3.28    0.00    0.00    0.27   38.52    0.00    0.00   39.89

t3.medium

{
    "InstanceCreditSpecifications": [
        {
            "InstanceId": "i-0123456789abcdef0",
            "CpuCredits": "standard"
        }
    ]
}
CPUCreditBalance
DATAPOINTS	288.0	2026-10-03T00:00:00+00:00	Count
DATAPOINTS	201.4	2026-10-03T03:00:00+00:00	Count
DATAPOINTS	62.9	2026-10-03T07:00:00+00:00	Count
DATAPOINTS	0.0	2026-10-03T10:00:00+00:00	Count
DATAPOINTS	0.0	2026-10-03T11:00:00+00:00	Count
```

(CloudWatch output trimmed to a few datapoints.)

**What it means:**

- `%steal` 38.5: for more than a third of the time, the vCPUs wanted to run and were not allowed to.
- The instance is a `t3.medium` in **standard** credit mode, and its credit balance reached 0 at about 10:00. A burstable instance with no credits is capped at its baseline (20% per vCPU for a t3.medium); the guest sees the rest as steal.
- On-prem (VMware, Proxmox, KVM), steal means the hypervisor host is overcommitted: more vCPUs want to run than there are physical cores (section 13).
- Good: `%steal` near 0. Worrying: above 5% sustained. Bad: above 10–20%.

**Why this step (now):** steal looks like "the CPU is slow" from inside the
guest, and no amount of tuning inside the VM fixes it. Checking it early stops
you from profiling an application that is simply not being given the CPU.

**Next step:** AWS credits exhausted → switch to `unlimited` mode (extra cost
when above baseline) or move to a non-burstable family; see "CPU wrap-up". On-prem
steal → section 13 and the virtualisation team. No steal → Step C9 on bare
metal, or back to Step C3.

### Step C9 — CPU frequency and thermal throttling (bare metal)

**Goal:** on physical servers, make sure the CPU runs at its rated speed.

```bash
grep -E '^cpu MHz' /proc/cpuinfo | sort | uniq -c        # current per-core clock
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cpupower frequency-info               # Ubuntu: linux-tools-common; RHEL: kernel-tools
sudo turbostat --quiet --show Busy%,Bzy_MHz,PkgTmp,PkgWatt --interval 5
sensors                               # package lm-sensors
sudo dmesg -T | grep -iE 'throttl|temperature'
grep -H . /sys/devices/system/cpu/cpu*/thermal_throttle/package_throttle_count 2>/dev/null | head -4
sudo ipmitool sdr type Temperature    # BMC sensors (iDRAC / iLO / IPMI)
```

```
     16 cpu MHz		: 1197.312
powersave
Busy%   Bzy_MHz PkgTmp  PkgWatt
97.12   1197    98      61.20
[Sat Oct  3 11:31:44 2026] CPU2: Package temperature above threshold, cpu clock throttled (total events = 18234)
[Sat Oct  3 11:31:44 2026] CPU6: Package temperature above threshold, cpu clock throttled (total events = 18234)
/sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_count:18234
```

**What it means:**

- All cores run at about 1.2 GHz while 97% busy, on a CPU rated at 2.9 GHz: everything CPU-bound takes about 2.4× longer.
- The package is at 98 °C and the kernel logged thousands of thermal throttle events. This is a cooling problem: a failed fan, dust, a blocked airflow path, a hot aisle.
- `scaling_governor` `powersave` with the `intel_pstate` driver is normal and still boosts under load. With the older `acpi-cpufreq` driver, `powersave` pins the lowest frequency and is a real problem.
- A BIOS power profile set to "power saving" can also cap the clock. Check the BMC event log (`ipmitool sel list`).
- On VMs you cannot see this; it is the hypervisor team's job.

**Why this step (now):** it is the last CPU explanation that is not about your
software. It is quick to rule out, and when it is the cause, nothing else in
this section will fix it.

**Next step:** thermal → hardware ticket (fans, airflow), check the BMC. Wrong
governor or BIOS profile → see "CPU wrap-up". Clock normal → the CPU really is
busy with work; back to Step C3 and C5.

### CPU wrap-up: tree, fix, rollback, prevent

```
CPU busy?
├── r > cores and id ≈ 0? (C1) ── no → not saturated → section 7 / other resources
└── yes → mpstat (C2)
    ├── one core 100% usr ───────→ single thread → C3 + C4 → profile (C5), parallelise or speed up
    ├── one core high soft/irq ──→ section 15
    ├── st high ─────────────────→ C8 (credits / overcommitted host)
    └── all cores busy → who? (C3: systemd-cgtop, pidstat, mod_status)
        ├── one client / endpoint ──→ block or rate-limit, then fix the endpoint
        ├── our code is hot ────────→ C4 thread → C5 perf / flame graph → developers
        ├── high sy ────────────────→ C6 syscalls / context switches
        ├── container slow, host has idle CPU → C7 throttling
        └── bare metal, low MHz ────→ C9 thermal / BIOS
```

**Fix & verify** (pick the one that matches the cause):

```bash
# 1. One abusive client on a service Apache owns directly (UFW sees this traffic)
sudo ufw insert 1 deny from 198.51.100.23 to any port 443 proto tcp
#    Ports published by Docker (Traefik on 80/443 under Dokploy) BYPASS UFW:
#    rate-limit or block in Traefik (ipAllowList / rateLimit middleware) or in the DOCKER-USER chain.

# 2. A batch job or cron script competing with the web tier: lower its priority
sudo renice -n 10 -p PID
sudo systemctl set-property --runtime UNIT CPUQuota=50%     # cap a service; --runtime = until reboot

# 3. Container throttled: raise the limit (plain container / Swarm service)
docker update --cpus 2 CONTAINER
docker service update --limit-cpu 2 SERVICE                 # redeploys the service's tasks

# 4. Bare metal on a power-saving governor (acpi-cpufreq)
sudo cpupower frequency-set -g performance

# Verify: run queue and PSI back to normal, latency back to baseline
vmstat 1 5; cat /proc/pressure/cpu
curl -o /dev/null -s -w 'ttfb=%{time_starttransfer}s total=%{time_total}s\n' https://shop.example.com/search?q=test
```

> ⚠️ Killing the runaway process is tempting. Prefer `systemctl stop UNIT` or
> `kill -TERM PID` (lets it clean up) and wait a few seconds. Use
> `kill -9 PID` only if it ignores SIGTERM: SIGKILL skips cleanup, can leave
> lock files and half-written data behind, and destroys the evidence (take a
> `jstack`, `py-spy dump` or `perf record` first).

**Rollback:**

```bash
sudo ufw status numbered                            # find the rule number
sudo ufw delete deny from 198.51.100.23 to any port 443 proto tcp
sudo renice -n 0 -p PID
sudo systemctl set-property --runtime UNIT CPUQuota=    # empty value removes the quota
docker update --cpus 1.5 CONTAINER                      # back to the old value
sudo cpupower frequency-set -g powersave
```

**Prevent it next time:**

- Alert on saturation: PSI cpu `some` above about 20% for 5 minutes, or load per core above about 1.5 (section 19).
- Track latency per endpoint (Step A10). A single slow endpoint shows up there days before it melts the box.
- Put rate limits on expensive endpoints. After the Dokploy migration, Traefik's rateLimit middleware does this per router.
- **Keep builds off the production box.** Dokploy builds images on the server by default, so every deploy competes with live traffic for CPU and disk. Build in GitLab CI, push to Harbor, and let Dokploy deploy the image.
- For containers, set CPU requests/reservations deliberately, and remove CPU limits from latency-sensitive services unless you have a reason for them. Size thread pools to the quota.
- On AWS, alarm on `CPUCreditBalance` for any T-family instance, or do not run production on burstable types.

---

## 4. Memory pressure

> 📚 **Study path:** 1) Note: [Memory](04-memory.md), then [Learn: performance & observability](32-learn-performance-observability.md), section 5 (memory deep dive) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment → Verify Integrity and Availability of Resources and Processes, and Storage → swap ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) KodeKloud: *Docker Certified Associate* — Docker Engine – Security → memory limits ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 4) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 5) Practice: section 20, drill 2 (make a VM swap with `stress-ng --vm`, then OOM-kill a container on purpose).

**Level:** [L2 · Mid] for Steps M1–M7; [L3 · Senior] for kernel memory, huge
pages and NUMA (M8–M9) and for writing a memory budget per host.

Memory problems rarely announce themselves as memory problems. They show up as
disk I/O (swap and re-read page cache), as high load (tasks blocked on that
I/O), as CPU (`kswapd`, direct reclaim, GC), or as processes that silently
disappear (OOM kills). This section continues the `web01` story from section
2: `java` holds 4.9 GB on an 8 GB host and the box swaps.

### free, available and buff/cache explained

| Term | Meaning | Read it as |
|---|---|---|
| `total` | RAM the kernel can use | fixed |
| `used` | memory in use by processes and the kernel | not very useful on its own |
| `free` | completely unused RAM | low is **normal**; Linux uses spare RAM as cache |
| `buff/cache` | page cache (file contents) and buffers | mostly reclaimable, but evicting it means re-reading files from disk later |
| `shared` | tmpfs and shared memory | counts against RAM, cannot be dropped like cache |
| `available` | estimate of memory programs can still get **without swapping** | **the number that matters** |
| swap used | pages currently stored in swap | harmless on its own |
| swap activity (`si`/`so`) | pages moving in and out of swap per second | the real signal of pressure |

### PSI: pressure stall information

Since kernel 4.20, Linux reports **how much time work was stalled** waiting
for CPU, memory or I/O. It is the most direct "is this resource making things
slow?" signal the kernel offers. Ubuntu 22.04 and 24.04 have it enabled.
RHEL-family kernels may ship it disabled (the files are missing or return an
error); enable it by adding `psi=1` to the kernel command line.

```bash
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
# Per service or container (cgroup v2): the same files inside each cgroup directory
cat /sys/fs/cgroup/system.slice/apache2.service/memory.pressure
```

```
some avg10=0.85 avg60=0.62 avg300=0.40 total=81234512
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
some avg10=38.12 avg60=29.40 avg300=11.25 total=611234880
full avg10=21.40 avg60=16.88 avg300=6.12 total=402118734
some avg10=52.77 avg60=41.03 avg300=15.90 total=901223411
full avg10=33.10 avg60=25.71 avg300=9.88 total=588120344
```

- **some**: percentage of time at least one task was stalled on this resource. Work got slower.
- **full**: percentage of time **all** non-idle tasks were stalled at once. No useful work happened at all; that time is simply lost.
- `avg10`, `avg60`, `avg300`: averages over 10 s, 60 s and 5 min. `total`: cumulative stall time in microseconds, for computing your own rates.
- Here memory `full avg10=21.40`: for a fifth of the last 10 seconds, everything on the box waited for memory. I/O pressure is even higher because the memory shortage turned into swap I/O.

Rough guide (rules of thumb, not standards; compare with your baseline):

| Resource | some avg10 | full avg10 | Reading |
|---|---|---|---|
| cpu | above 20–25 | (always 0 system-wide) | CPU queueing is hurting latency |
| memory | above 5–10 | above 1–5 | reclaim or swapping is slowing work; full above 10 is severe |
| io | above 10–20 | above 5 | storage latency is slowing work |

### Step M1 — Headroom: free and MemAvailable

**Goal:** know how much memory is really left, and where the rest went in
broad terms.

```bash
free -m
grep -E '^(MemTotal|MemAvailable|Cached|AnonPages|Shmem|SwapTotal|SwapFree|Dirty|Writeback):' /proc/meminfo
```

```
               total        used        free      shared  buff/cache   available
Mem:            7941        6812         142          45         986         812
Swap:           2047        1630         417
MemTotal:        8132196 kB
MemAvailable:     831412 kB
Cached:           842104 kB
SwapTotal:       2097148 kB
SwapFree:         427912 kB
Dirty:             41220 kB
Writeback:         12304 kB
AnonPages:       6512880 kB
Shmem:             46080 kB
```

**What it means:**

- `MemAvailable` 812 MB of 7.9 GB (10%) and almost 1.6 GB of swap in use.
- `AnonPages` 6.5 GB: memory owned by processes (heaps, stacks), as opposed to file cache. Anonymous memory can only be freed by the process or by swapping it out, which is why the box swaps.
- `Cached` 842 MB is already small for this host; the kernel has shrunk the cache as far as it reasonably can.
- `Dirty`/`Writeback` small: write-back is not the issue (compare Step M7).
- Good: `MemAvailable` above about 15–20% of RAM. Bad: below 10% with swap activity.

**Why this step (now):** it separates "processes own the memory" (anonymous)
from "the kernel is caching files" (reclaimable) and from "tmpfs or shared
memory" (`Shmem`). Each leads to a different next step.

**Next step:** → Step M2 to see whether the box is swapping right now.

### Step M2 — Is it swapping right now?

**Goal:** separate harmless swap *usage* from harmful swap *activity*.

```bash
vmstat 1 5               # si / so columns (KiB per second)
sar -W 1 5               # pswpin/s pswpout/s (pages per second)
swapon --show
cat /proc/sys/vm/swappiness
```

```
10:46:01     pswpin/s pswpout/s
10:46:02       461.00   1303.00
10:46:03       554.00   1735.00
NAME      TYPE SIZE  USED PRIO
/swap.img file   2G  1.6G   -2
60
```

**What it means:**

- 461 pages/s in and 1,303 pages/s out (4 KiB pages): about 1.8 MB/s in and 5.2 MB/s out, matching `vmstat`'s `si`/`so`.
- Pages going **out and back in** at the same time is thrashing: the working set no longer fits in RAM.
- `/swap.img` is the swap file the Ubuntu Server installer creates on the root filesystem (its size depends on RAM and disk; 2 GB on this host; cloud images usually have no swap at all), so swap I/O competes with every other write on that disk (Step 6 of the checklist).
- `swappiness` 60 is the default. It changes *which* memory gets reclaimed first (cache versus anonymous), not whether a box that is out of memory swaps.
- Good: `si`/`so` at 0 even with swap used. Bad: non-zero for more than a few seconds.

**Why this step (now):** swap used with no activity means old pages parked
weeks ago, and chasing it wastes time. Active swapping means memory is *the*
bottleneck and explains the disk and load symptoms.

**Next step:** active swapping → Step M3 to quantify it, then Step M5. No
activity → Step M4 (OOM history) and Step M7 (page-cache thrash).

### Step M3 — Quantify the damage with PSI

**Goal:** measure how much time work is actually stalled on memory, for the
host and per service.

```bash
cat /proc/pressure/memory
CID=$(docker inspect -f '{{.Id}}' CONTAINER)
cat /sys/fs/cgroup/system.slice/docker-$CID.scope/memory.pressure
cat /sys/fs/cgroup/system.slice/apache2.service/memory.pressure
```

```
some avg10=38.12 avg60=29.40 avg300=11.25 total=611234880
full avg10=21.40 avg60=16.88 avg300=6.12 total=402118734
some avg10=41.80 avg60=33.02 avg300=12.71 total=210443120
full avg10=30.12 avg60=22.40 avg300=8.03 total=150223988
some avg10=24.33 avg60=19.10 avg300=7.40 total=88120411
full avg10=3.01 avg60=2.12 avg300=0.88 total=12004311
```

**What it means:**

- Host: 21% of recent time fully stalled on memory. Severe.
- The java container is stalled 30% of the time; Apache 24% `some`. Every service on the box suffers, not just the one using the memory: memory is a shared resource.
- `avg300` lower than `avg10`: it is getting worse, consistent with load climbing since 10:30.

**Why this step (now):** PSI turns "it is swapping" into "a fifth of the
machine's time is being lost", which is what justifies urgent action, and the
per-cgroup files show who suffers.

**Next step:** → Step M4 (has anything been killed?) then Step M5 (who holds
the memory).

### Step M4 — OOM kills in the kernel log

**Goal:** find out whether the kernel has already killed processes, and
whether it was the whole host or a cgroup limit.

```bash
sudo journalctl -k --since today --no-pager | grep -iE 'out of memory|oom-kill|killed process'
systemctl list-units --failed --no-pager
journalctl -u systemd-oomd --since today --no-pager | tail     # only where systemd-oomd is enabled
docker inspect -f '{{.Name}} OOMKilled={{.State.OOMKilled}} Exit={{.State.ExitCode}} Restarts={{.RestartCount}}' $(docker ps -aq)
grep -E '^(max|oom|oom_kill) ' /sys/fs/cgroup/system.slice/docker-$CID.scope/memory.events
```

Example from another day, on a container with a 1 GiB limit:

```
Oct 03 09:12:44 web01 kernel: java invoked oom-killer: gfp_mask=0xcc0(GFP_KERNEL), order=0, oom_score_adj=0
Oct 03 09:12:44 web01 kernel: oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=docker-9b1e0c47a2f3d5e6b7c8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0.scope,mems_allowed=0,oom_memcg=/system.slice/docker-9b1e0c47a2f3d5e6b7c8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0.scope,task_memcg=/system.slice/docker-9b1e0c47a2f3d5e6b7c8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0.scope,task=java,pid=27731,uid=1001
Oct 03 09:12:44 web01 kernel: Memory cgroup out of memory: Killed process 27731 (java) total-vm:6123456kB, anon-rss:1043712kB, file-rss:21344kB, shmem-rss:0kB, UID:1001 pgtables:2512kB oom_score_adj:0
/shop-api.1.x8k2m4n6p8q0 OOMKilled=true Exit=137 Restarts=0
max 4182
oom 6
oom_kill 6
```

**What it means:**

- `CONSTRAINT_MEMCG` and "Memory cgroup out of memory": the **container's limit** was hit (here 1 GiB, matching `anon-rss` of about 1 GB). The host may have had plenty of free memory. `CONSTRAINT_NONE` and plain "Out of memory: Killed process" mean the **whole host** ran out.
- The cgroup path contains the container ID; `docker ps --no-trunc | grep 9b1e0c47` names the container.
- Exit code 137 = 128 + 9: the process received SIGKILL. With `OOMKilled=true`, Docker confirms the cause. A Swarm task that gets OOM-killed is replaced by a **new** container, so the restart count stays 0 and the old task shows as failed in `docker service ps SERVICE`.
- `memory.events`: `max 4182` = the cgroup hit its limit 4,182 times and was forced into reclaim (slow, even without a kill); `oom_kill 6` = six processes were killed.
- On Ubuntu desktops (and wherever it is enabled), `systemd-oomd` may kill whole cgroups earlier, based on PSI; check its journal.
- Kubernetes shows the same as `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` in `kubectl describe pod` (see [Containers & Kubernetes playbook](26-playbook-containers-k8s.md)).

**Why this step (now):** an OOM kill explains "the app restarted by itself" and
"some requests failed", and it tells you whether the fix is a limit (cgroup)
or capacity (host). Hitting `memory.max` repeatedly makes a container slow
long before it is killed.

**Next step:** repeated OOM kills or growing usage → Step M5, then Step M6
(leak?). Host-level OOM → Step M5 to find what grew. Nothing killed → Step M5.

### Step M5 — Who holds the memory?

**Goal:** name the process, the container and the reason it is that big.

```bash
ps -eo pid,user,rss,vsz,etime,comm --sort=-rss | head -10       # RSS in KiB
sudo smem -tk -s pss -r | head -10                                # PSS: shared pages split fairly
systemd-cgtop -m -n 1 --depth 3                                   # per service / container (includes page cache)
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'

# Which container owns host PID 2817, and how was it started?
cat /proc/2817/cgroup
docker ps --no-trunc --format '{{.ID}}  {{.Names}}' | grep 4c7d1e
tr '\0' ' ' < /proc/2817/cmdline; echo
```

```
    PID USER       RSS    VSZ     ELAPSED COMMAND
   2817 1001   5138212 7612344  2-03:14:09 java
   1931 root    251880 1302144 23-04:10:51 node
   1187 root    118204 2384116 23-04:11:20 dockerd
   1602 999     104320  221436 23-04:10:40 postgres
   1544 root     86412 1271956 23-04:10:44 traefik
  41522 www-data  61204  412880    00:41:13 apache2

  PID User     Command                         Swap      USS      PSS      RSS
 2817 1001     java -Xms6g -Xmx6g -jar /app   1.4G     4.8G     4.8G     4.9G
 ...
-------------------------------------------------------------------------------
  157 15                                        1.9G     6.0G     6.2G     7.4G

0::/system.slice/docker-4c7d1e9a0b2c3d4e5f60718293a4b5c6d7e8f9012a3b4c5d6e7f8091a2b3c4d5e.scope
4c7d1e9a0b2c3d4e5f60718293a4b5c6d7e8f9012a3b4c5d6e7f8091a2b3c4d5e  shop-api.1.x8k2m4n6p8q0
java -Xms6g -Xmx6g -jar /app/app.jar
```

**What it means:**

- **RSS** is resident memory, but it double-counts pages shared between processes (Apache children, PostgreSQL backends). **PSS** splits shared pages fairly between the processes that share them and is the honest number to add up. **USS** is memory unique to the process: what you would get back by killing it. **VSZ** is address space; ignore it.
- `java` holds 4.9 GB resident plus 1.4 GB already pushed to swap.
- `/proc/2817/cgroup` names the Docker scope, so PID 2817 is the `shop-api` Swarm service (deployed through Dokploy).
- Its command line is the root cause: `-Xms6g -Xmx6g`, a 6 GB fixed heap on an 8 GB host that also runs Apache (about 1.3 GB), Docker, Traefik and Dokploy (about 0.8 GB). The box is oversubscribed **by configuration**: nothing leaked, the numbers simply do not fit.
- If the JVM had no `-Xmx`, recent JVMs default to a quarter of the RAM they can see. Without a container memory limit, that is a quarter of the **host's** RAM.

**Why this step (now):** you have proven memory pressure; now you need the
owner and the reason. "Configured too big" is fixed with a config change.
"Growing without bound" is a leak (Step M6). "No process is big but memory is
gone" means kernel memory or tmpfs (Step M8).

**Next step:** sized too big by configuration (our story) → "Memory wrap-up"
fix. Usage grows over hours or days → Step M6. `ps` totals do not explain the
missing memory → Step M8.

### Step M6 — Leak or just warm?

**Goal:** tell a memory leak from a process that has simply grown to its
normal working size.

```bash
# RSS of one PID every 60 s with a timestamp (leave it running in tmux or screen)
while sleep 60; do printf '%s %s\n' "$(date +%T)" "$(ps -o rss= -p PID)"; done | tee /var/tmp/rss-PID.log
pidstat -r -p PID 60                      # RSS plus minor/major page faults per second
# JVM: is the heap still full right after a full GC? (in the container)
docker exec CONTAINER jcmd 1 GC.heap_info
```

```
11:00:00  2104332
11:01:00  2131876
11:02:00  2158012
11:03:00  2186440
11:04:00  2213208
```

**What it means:**

- RSS grows about 27 MB per minute, steadily, with no plateau. Projected over a day, that is 38 GB: a leak.
- A **warm-up** curve grows fast after start and then flattens (caches filling, a JVM heap expanding to `-Xmx`). That is not a leak.
- For the JVM, compare old-generation usage right after successive full GCs (Step A7). If each full GC frees less and less, objects are being retained: a heap leak. If the heap is stable but RSS keeps growing, the leak is off-heap (direct buffers, native libraries, threads).
- For Apache with mod_php, children that grow over thousands of requests leak inside PHP or an extension; `MaxConnectionsPerChild` recycles them as a stopgap.

**Why this step (now):** a leak needs a code fix (and a planned restart as a
stopgap); a correctly sized process that does not fit needs capacity or a
limit. Raising limits for a leak only delays the outage.

**Next step:** leak → schedule a restart during low traffic, capture evidence
for the developers first (heap dump, see the warning below), then "Memory
wrap-up". Not a leak → Step M7 or the fix for oversubscription.

> ⚠️ A heap dump (`jcmd PID GC.heap_dump /var/tmp/heap.hprof`) pauses the JVM
> for seconds and writes a file about as large as the heap. Make sure the disk
> has room, and do it when a pause is acceptable.

### Step M7 — Page-cache thrash and dirty write-back

**Goal:** find memory pressure that does not involve swap: the file cache is
too small for the working set, or too much unwritten data piles up.

```bash
sar -B 1 5
grep -E '^(Dirty|Writeback):' /proc/meminfo
sysctl vm.dirty_ratio vm.dirty_background_ratio vm.dirty_bytes vm.dirty_background_bytes
```

```
11:20:01     pgpgin/s pgpgout/s   fault/s  majflt/s  pgfree/s pgscank/s pgscand/s pgsteal/s    %vmeff
11:20:02     48212.00   1204.00  15321.00    812.00  51234.00  60123.00   8123.00  41234.00     60.43
Dirty:           3912044 kB
Writeback:        402112 kB
vm.dirty_ratio = 20
vm.dirty_background_ratio = 10
vm.dirty_bytes = 0
vm.dirty_background_bytes = 0
```

**What it means:**

- `majflt/s` 812: page faults that had to read from disk. Hundreds per second with no swap activity means file pages (database files, binaries, container images) are evicted and re-read constantly: **page-cache thrash**.
- `pgscank/s`: pages scanned by `kswapd` (background reclaim). `pgscand/s`: pages scanned by **direct reclaim**, meaning application threads had to free memory themselves before they could continue. Any sustained direct reclaim adds latency to requests.
- `%vmeff` is how many scanned pages could actually be freed. Low values mean the kernel works hard to find reclaimable memory.
- `Dirty` 3.9 GB: modified data not yet written to disk. Under the default ratios, a large-RAM host can accumulate gigabytes, then block writers for seconds while it flushes (processes stall in `balance_dirty_pages`).

**Why this step (now):** a box can be memory-starved without swapping at all
(no swap configured, or only file cache under pressure). These counters are
the only way to see it, and the symptom ("disk reads are high") otherwise sends
you to the disk section to fix the wrong thing.

**Next step:** thrash → more RAM, or keep big batch readers (backups, scans)
from flushing the cache (schedule them, or cap them in a cgroup). Huge dirty
pages with write stalls → lower the dirty thresholds (wrap-up). Neither → Step M8.

### Step M8 — Memory that ps cannot see: slab, tmpfs, huge pages

**Goal:** account for memory that does not belong to any process.

```bash
grep -E '^(Slab|SReclaimable|SUnreclaim|Shmem|HugePages_Total|HugePages_Free|Hugetlb):' /proc/meminfo
sudo slabtop -o -s c | head -12
df -h -t tmpfs
```

```
Shmem:           1843200 kB
Slab:            2412880 kB
SReclaimable:    2201004 kB
SUnreclaim:       211876 kB
HugePages_Total:       0
HugePages_Free:        0
Hugetlb:               0 kB
 Active / Total Objects (% used)    : 9812345 / 10012346 (98.0%)
  OBJS ACTIVE  USE OBJ SIZE  SLABS OBJ/SLAB CACHE SIZE NAME
6123456 6101230  99%    0.19K 291593       21   1166372K dentry
1812345 1801200  99%    0.59K  67124       27   1073984K ext4_inode_cache
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           3.9G  1.7G  2.2G  44% /dev/shm
tmpfs           795M  2.1M  793M   1% /run
```

**What it means:**

- `Slab` 2.4 GB, almost all `SReclaimable` (dentry and inode caches from something scanning millions of files). Reclaimable slab is given back under pressure; large `SUnreclaim` that keeps growing suggests a kernel or driver leak.
- `Shmem` 1.8 GB and `/dev/shm` using 1.7 GB: files in tmpfs live in RAM, do not show in any process's RSS, and cannot be dropped like cache. Clean up the files or limit the tmpfs size.
- `HugePages_Total` above 0 reserves memory for huge pages that nothing else can use, even if unused (`HugePages_Free`). A database misconfiguration can waste gigabytes this way.

**Why this step (now):** when the process table does not explain where memory
went, these three are almost always the answer, and they need very different
fixes from killing a process.

**Next step:** see [Memory reference](04-memory.md) for slab and huge pages in
depth. Nothing unusual here → Step M9.

### Step M9 — Transparent huge pages and NUMA

**Goal:** catch two kernel memory features that cause latency spikes on
databases and big servers.

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
grep -E '^(thp_fault_alloc|thp_collapse_alloc|compact_stall) ' /proc/vmstat
numactl --hardware            # package numactl
numastat -p PID               # per-NUMA-node memory of one process
cat /proc/sys/vm/zone_reclaim_mode
```

```
always [madvise] never
always defer defer+madvise [madvise] never
thp_fault_alloc 1823451
thp_collapse_alloc 98123
compact_stall 412339
available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3 4 5 6 7 16 17 18 19 20 21 22 23
node 0 size: 64326 MB
node 0 free: 1123 MB
node 1 cpus: 8 9 10 11 12 13 14 15 24 25 26 27 28 29 30 31
node 1 size: 64507 MB
node 1 free: 41876 MB
node distances:
node   0   1
  0:  10  21
  1:  21  10
0
```

**What it means:**

- **THP** (transparent huge pages) backs memory with 2 MB pages automatically. The brackets show the active mode: Ubuntu defaults to `madvise` (only for programs that ask). RHEL-family systems default to `always`.
- With `always`, the kernel may stall a process to compact memory into 2 MB blocks. A fast-growing `compact_stall` counter means allocation stalls, seen as random latency spikes. Redis and many database vendors recommend `never`. MongoDB is the exception to check: up to 7.0 it said `never`, but from 8.0 (new TCMalloc) it recommends enabling THP, so read your database's current production notes before changing it.
- **NUMA**: on a 2-socket server, each socket has its own memory. Node 0 has 1 GB free while node 1 has 41 GB free. A process bound to node 0 (by `numactl --membind`, a VM's vNUMA layout, or `zone_reclaim_mode=1`) can reclaim and swap while half the RAM sits unused. Remote-node access is also slower (distance 21 versus 10).
- Small VMs usually have a single node; then NUMA is not your problem.

**Why this step (now):** these are last because they are rarer, but they
explain "memory looks fine and latency still spikes" on big hosts and
databases, which nothing earlier in this section would catch.

**Next step:** THP stalls → set `never` for the database host (wrap-up). NUMA
imbalance → `zone_reclaim_mode=0`, interleave memory for the database
(`numactl --interleave=all`), or fix the VM's vNUMA sizing.

### Memory wrap-up: tree, fix, rollback, prevent

```
Memory suspected?
├── OOM in dmesg? (M4)
│   ├── CONSTRAINT_MEMCG → container/service limit → raise wisely or fix usage (M5/M6)
│   └── CONSTRAINT_NONE  → host out of memory → M5 who / M6 leak / capacity
├── si/so > 0? (M2) → thrashing → M3 how bad → M5 who
│   ├── sized too big by config (-Xmx, MaxRequestWorkers, too many containers) → resize / limit
│   └── growing over time → M6 leak → planned restart + developers
├── no swap activity but majflt/s, pgscand/s high → M7 page-cache thrash
├── Dirty in GBs + write stalls → M7 dirty thresholds
├── ps does not add up → M8 slab / tmpfs / huge pages
└── latency spikes, compact_stall rising, 2+ NUMA nodes → M9 THP / NUMA
```

**Fix & verify** (the `web01` story): give the JVM a heap that fits, and give
the container a hard memory limit so it can never starve the host again.

```bash
# Budget for an 8 GB host: OS ~0.5 GB, Apache ~1.3 GB, Docker + Traefik + Dokploy ~0.8 GB
# → the app container gets 4 GB, the JVM heap 75% of that.
#   JAVA_OPTS="-XX:MaxRAMPercentage=75.0"   (remove the fixed -Xms6g -Xmx6g)
#   JAVA_OPTS only works if the image's start script passes it to java; the JVM itself reads
#   JAVA_TOOL_OPTIONS. Either way, an -Xmx on the command line wins, so it must go.
docker service update --limit-memory 4g --env-add 'JAVA_OPTS=-XX:MaxRAMPercentage=75.0' SERVICE
# (in Dokploy: set the environment variable and the memory limit in the application's
#  settings, then redeploy, so the next deploy does not undo it)

# Apache prefork + mod_php: MaxRequestWorkers must fit in the RAM you give Apache
ps -C apache2 -o rss= | awk '{s+=$1; n++} END {printf "%d children, average %.0f MB\n", n, s/n/1024}'
#   e.g. 1300 MB budget / 60 MB per child → MaxRequestWorkers about 20, not the default 150

# Verify: swapping stops, pressure drops, latency returns
vmstat 1 5; cat /proc/pressure/memory; free -m
curl -o /dev/null -s -w 'ttfb=%{time_starttransfer}s\n' https://app.example.com/
```

Other fixes by cause:

```bash
# Large-RAM host with write stalls: start write-back earlier, cap dirty data
printf 'vm.dirty_background_bytes = 268435456\nvm.dirty_bytes = 1073741824\n' | sudo tee /etc/sysctl.d/90-dirty.conf
sudo sysctl --system

# Database host suffering THP compaction stalls (until reboot; persist with a kernel parameter
# transparent_hugepage=never or a small systemd unit)
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Cap a systemd service: MemoryHigh throttles and reclaims before MemoryMax OOM-kills
sudo systemctl set-property UNIT MemoryHigh=1G MemoryMax=1200M
```

> ⚠️ Do not run `swapoff -a` on a box under memory pressure "to stop the
> swapping". It forces every swapped page back into RAM that is not there and
> can trigger the OOM killer on random processes. Do not use
> `echo 3 > /proc/sys/vm/drop_caches` as a fix either: it throws away the page
> cache, makes the next minutes slower (everything is re-read from disk) and
> frees nothing a process owns.

**Rollback:** redeploy the previous service definition (`docker service
rollback SERVICE` returns a Swarm service to its previous spec; in Dokploy,
redeploy the previous deployment). Remove `/etc/sysctl.d/90-dirty.conf` and
set `sudo sysctl -w vm.dirty_ratio=20 vm.dirty_background_ratio=10` (writing
a `*_ratio` value resets the matching `*_bytes` value to 0). `echo madvise |
sudo tee /sys/kernel/mm/transparent_hugepage/enabled`. `sudo systemctl
set-property UNIT MemoryHigh= MemoryMax=` (empty values remove the limits).

**Prevent it next time:**

- Every container gets a memory limit, and every JVM gets a heap sized as a percentage of that limit, never a fixed size copied from another server.
- Keep a written memory budget per host (OS, Apache, Docker stack, each app). Check it before adding a vhost or a container.
- Alert on `MemAvailable` below 10–15%, on swap-in activity, on PSI memory `full` above a few percent, and on any OOM kill (section 19).
- Graph RSS of the main services over weeks: leaks show as a slope long before they hurt.

---

## 5. Disk I/O

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Storage → Monitor Storage Performance ([lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)), then LVM and mount options ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: [Storage & disk](01-storage-disk.md), then [Learn: performance & observability](32-learn-performance-observability.md), section 6 (disk deep dive) · 3) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 4) Practice: section 20, drill 3 (an `fio` or `stress-ng --hdd` neighbour next to a database), then the free KodeKloud *Linux Challenges* ([course](https://kodekloud.com/courses/linux-challenges)).

**Level:** [L2 · Mid] for Steps D1–D4; [L3 · Senior] for fsync behaviour,
cloud volume limits, RAID and failing disks (D5–D8), where the fix is a
storage or architecture decision.

You are here because `vmstat` showed `wa` and `b`, `iostat` showed high await
or queue, PSI io is high, or there are D-state processes. The example: on
another `web01` morning, a backup copies Docker volumes from the data disk
`sdb` while PostgreSQL and the apps keep writing to it.

### Reading iostat -x column by column

| Column | Meaning | Healthy (rough guide) | Worry when |
|---|---|---|---|
| `r/s`, `w/s` | read and write operations completed per second (IOPS) | within the device's rating | flat at a round number (a cap, Step D6) |
| `rkB/s`, `wkB/s` | throughput | within the device's rating | near the device or volume limit |
| `rrqm/s`, `wrqm/s` | requests merged with neighbours before dispatch | any | (informational) |
| `r_await`, `w_await` | average ms per request, **queue time plus device time** | NVMe under 1, SATA SSD 1–5, HDD 5–15, cloud SSD volumes 1–3 | many times the normal value |
| `rareq-sz`, `wareq-sz` | average request size in KB | (shows the pattern) | small (4–16 KB) = random I/O; 128 KB+ = sequential |
| `f/s`, `f_await` | flush requests (from fsync) and their latency | low ms | tens of ms (Step D5) |
| `aqu-sz` | average number of requests in flight | below the device's parallelism | sustained above 1 on an HDD, far above normal on SSD |
| `%util` | share of time the device had **at least one** request in flight | (see below) | 100% on a single HDD |

`svctm` is gone from modern sysstat because it was misleading. Ignore guides
that still use it.

### Why %util lies on SSD, NVMe and RAID

`%util` only measures whether *anything* was in flight. A single spinning disk
handles one request at a time, so 100% really means "full". An NVMe drive
works on dozens of requests in parallel, a RAID array spreads them over many
disks, and a SAN LUN or a cloud volume sits on large backend storage. Such a
device can show 100% `%util` while serving a small fraction of what it can do.

| Device shows | Reading |
|---|---|
| HDD: `%util` 100, `await` 80 ms, `aqu-sz` 12 | saturated |
| NVMe: `%util` 100, `r_await` 0.2 ms, `aqu-sz` 1.1 | busy but fast; not the bottleneck |
| NVMe: `%util` 100, `r_await` 9 ms, `aqu-sz` 60 | saturated (or throttled) |
| Cloud volume: `%util` 60, `await` 25 ms, IOPS flat at 3000 | capped by the volume's IOPS limit |

→ Judge storage by **latency** (`await` against the device's normal), by
**queue** (`aqu-sz`), by **PSI io**, and by IOPS or MB/s against the
device's known limit. `%util` is only trustworthy for single HDDs.

### Step D1 — Device latency and queue

**Goal:** find which device is slow and what kind of I/O it is doing.

```bash
iostat -xyz 1 3
lsblk -o NAME,SIZE,TYPE,ROTA,MOUNTPOINTS      # ROTA 1 = spinning disk; MOUNTPOINTS on newer util-linux
cat /proc/pressure/io
```

```
Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     f/s f_await  aqu-sz  %util
sda              2.00     16.00     0.00   0.00    0.61     8.00   14.00    112.00    14.00  50.00    0.94     8.00    3.00    0.67    0.02   1.60
sdb            381.00  48768.00     2.00   0.52   71.24   128.00  162.00   3112.00    40.00  19.80  148.92    19.21   21.00  210.33   56.79 100.00

NAME   SIZE TYPE ROTA MOUNTPOINTS
sda     50G disk    0
└─sda2  49G part    0 /
sdb      2T disk    1
└─sdb1   2T part    1 /srv
some avg10=61.20 avg60=48.33 avg300=20.12 total=1203344512
full avg10=38.75 avg60=30.10 avg300=12.40 total=812004332
```

(Discard columns removed for width.)

**What it means:**

- `sda` (the SSD root disk) is idle and fast: 0.6–0.9 ms. Not involved.
- `sdb` (a 2 TB spinning disk, `ROTA 1`, mounted at `/srv` with Docker volumes and PostgreSQL data) reads 48 MB/s in 128 KB requests: a sequential reader, typical of a backup or a large copy.
- Meanwhile its writes wait 149 ms and its flushes 210 ms: every database commit waits behind the reader. `aqu-sz` 57 confirms a deep queue.
- PSI io `full` 39%: for over a third of the time nothing on the box could make progress because of I/O.

**Why this step (now):** you need the device and the I/O pattern before
looking for a culprit. Sequential 128 KB reads point at a copy or backup;
small random writes point at a database or swap; high latency at low IOPS
points at a cap or a failing disk.

**Next step:** → Step D2 to name the process. Latency high with modest IOPS
→ also Step D6 (cloud caps) and Step D8 (failing disk).

### Step D2 — Which process is doing the I/O?

**Goal:** name the process (and container) behind the disk traffic.

```bash
sudo iotop -oPa                 # -o only active, -P per process, -a accumulated since start
sudo pidstat -d 1 5             # per-process kB/s read and written, plus iodelay
sudo cat /proc/PID/io           # cumulative bytes this process read and wrote
# iotop needs delay accounting for its IO> and SWAPIN columns; newer kernels default it off:
sudo sysctl kernel.task_delayacct=1        # until reboot
```

```
Total DISK READ:        47.12 M/s | Total DISK WRITE:         5.01 M/s
Actual DISK READ:       46.90 M/s | Actual DISK WRITE:        4.77 M/s
    PID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
  10421 be/4 root          2.61 G      0.00 B  0.00 % 86.41 % rsync -a /srv/docker-volumes/ /mnt/backup/volumes/
   1290 be/4 999           0.00 B     81.20 M  0.00 % 41.12 % postgres: walwriter
   1288 be/4 999           0.00 B     40.80 M  0.00 % 22.37 % postgres: checkpointer
    398 be/3 root          0.00 B     12.04 M  0.00 % 18.90 % [jbd2/sdb1-8]

10:12:31      UID       PID   kB_rd/s   kB_wr/s kB_ccwr/s iodelay  Command
10:12:32        0     10421  47104.00      0.00      0.00      97  rsync
10:12:32      999      1290      0.00   1912.00      0.00      41  postgres
10:12:32      999      1288      0.00    988.00      0.00      23  postgres
```

**What it means:**

- `rsync` (PID 10421) reads at 47 MB/s and spends 86% of its time waiting on I/O (`IO>`): it is the main consumer.
- PostgreSQL (UID 999, the container's postgres user) writes WAL and checkpoints; it is the victim, spending 41% of its time waiting.
- `PRIO be/4` is the default best-effort I/O class. The backup has the same I/O priority as the database.
- `[jbd2/sdb1-8]` is the ext4 journal thread for `sdb1`; it rises with any write-heavy load.
- `iodelay` in `pidstat` is the number of clock ticks spent waiting for block I/O.
- If `iotop` prints a warning about delay accounting and `?unavailable?` columns, enable `kernel.task_delayacct` as shown.

**Why this step (now):** the fix depends entirely on *who* does the I/O: a
batch job can be throttled or rescheduled, an application needs tuning, a
kernel thread points at another subsystem (`kswapd` = memory, `md*_resync` =
RAID, `jbd2` = journal/fsync).

**Next step:** a batch job (backup, `find`, `updatedb`, a build) → throttle or
reschedule it ("Disk wrap-up"), and check its schedule (Step H3). The
application itself → Step D5 (fsync) and section 7. `kswapd` → section 4.
Processes stuck in state D → Step D3.

### Step D3 — D-state processes and what they wait on

**Goal:** list the tasks stuck in uninterruptible sleep and find what kernel
code they are waiting in.

```bash
ps -eo state,pid,ppid,wchan:32,etime,cmd | awk 'NR==1 || $1 ~ /^D/'
sudo cat /proc/PID/stack                  # kernel stack of one stuck task
# Dump all blocked tasks with stacks into the kernel log (read-only), then read them
echo w | sudo tee /proc/sysrq-trigger > /dev/null
sudo dmesg -T | tail -60
```

```
S     PID    PPID WCHAN                             ELAPSED CMD
D   10421   10420 wait_on_page_bit_common             41:12 rsync -a /srv/docker-volumes/ /mnt/backup/volumes/
D     398       2 jbd2_journal_commit_transaction 23-04:11:32 [jbd2/sdb1-8]
D    1290    1201 io_schedule                     23-04:10:40 postgres: walwriter
D   51120   51001 rpc_wait_bit_killable                 03:02 df -h
```

**What it means:**

- `WCHAN` is the kernel function the task sleeps in, and it names the subsystem:

| WCHAN contains | Waiting for |
|---|---|
| `io_schedule`, `wait_on_page_bit_common` (kernel 5.15 and older) or `folio_wait_bit_common` (5.16+), `blk_mq_get_tag` | block I/O on a local disk (`blk_mq_get_tag` = the device queue is full) |
| `jbd2_*` | the ext4 journal commit (fsync-heavy load, slow disk) |
| `xfs_*`, `xlog_*` | the XFS log |
| `rpc_wait_bit_killable`, `nfs_*` | an NFS server |
| `md_*`, `raid*` | software RAID |

- The first three are waiting on `sdb`, as expected.
- `df -h` waiting in `rpc_wait_bit_killable` for three minutes is a **different** problem: an NFS mount whose server does not answer. `df` touches every mount, so it hangs on the dead one (section 11).
- Tasks in D state cannot be killed, not even with `kill -9`, until the I/O they wait for completes or fails. With a `hard` NFS mount to a dead server, that can be forever.
- The sysrq `w` command only prints information; it does not change anything. Stacks land in `dmesg`.

**Why this step (now):** D-state tasks are what turns slow I/O into high
load and frozen processes. Their wait channels tell you which device or
server to fix, especially when several storage problems overlap.

**Next step:** local disk → Steps D4–D8 depending on the device. NFS →
section 11 and section 14. RAID → Step D7.

### Step D4 — Filesystem nearly full

**Goal:** rule out a nearly full or exhausted filesystem as the cause of slow
writes.

```bash
df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay      # squashfs = snap loop devices
df -i -x tmpfs -x devtmpfs -x squashfs -x overlay
sudo e4defrag -c /srv/pgdata                              # ext4 fragmentation score (read-only check)
sudo xfs_db -r -c frag /dev/sdb1                          # XFS fragmentation factor (read-only)
docker system df
```

```
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda2      ext4   49G   21G   26G  45% /
/dev/sdb1      ext4  2.0T  1.9T   61G  97% /srv
Filesystem       Inodes   IUsed    IFree IUse% Mounted on
/dev/sda2       3276800  412880  2863920   13% /
/dev/sdb1     134217728 1201334 133016394    1% /srv
```

**What it means:**

- `/srv` is 97% full. ext4 and XFS both slow down when nearly full: the allocator searches harder for free blocks, new files fragment, and databases that extend files suffer. As a rule of thumb, keep data filesystems below 80–85%.
- ext4 reserves 5% of blocks for root by default, so normal users hit "No space left on device" while `df` still shows space for root.
- Inodes are fine here. 100% `IUse%` produces "No space left on device" with free blocks (see [Storage & disk](01-storage-disk.md)).
- `docker system df` shows images, build cache and volumes; build cache on a Dokploy server that builds images grows quietly.

**Why this step (now):** it is a cheap check that explains slow writes
without any device-level problem, and the fix (free space) is completely
different from tuning I/O.

**Next step:** nearly full → free space using [Storage & disk](01-storage-disk.md)
(and see the prune warning in "Disk wrap-up"). Plenty of space → Step D5.

### Step D5 — fsync-heavy applications

**Goal:** check whether the application waits on `fsync` (data forced to
stable storage), and how slow each one is.

Databases (every commit), etcd (every write), message queues, SQLite, Gitaly
and journald call `fsync` or `fdatasync` and wait for the device to confirm.
On a spinning disk that costs 5–15 ms. On an SSD without power-loss
protection it can be several ms. On a RAID controller with a battery-backed
write cache, or an enterprise NVMe drive, it is well under 1 ms.

```bash
iostat -xyz 1 3                         # f/s and f_await = flushes reaching the device
sudo strace -f -T -e trace=fsync,fdatasync,sync_file_range -p PID 2>&1 | head -10   # brief!
# Measure fsync latency of a filesystem (creates a 64 MB test file in that directory; delete it after)
fio --name=fsynctest --directory=/srv/fio-test --rw=write --bs=4k --size=64m \
    --fdatasync=1 --runtime=30 --time_based
# Kubernetes control plane: etcd logs slow disk writes
sudo crictl logs $(sudo crictl ps --name etcd -q) 2>&1 | grep -iE 'slow fdatasync|took too long' | tail -5
```

```
[pid  1290] fdatasync(23)               = 0 <0.148210>
[pid  1290] fdatasync(23)               = 0 <0.131877>
[pid  1290] fdatasync(23)               = 0 <0.162004>

  fsync/fdatasync/sync_file_range:
    sync (usec): min=812, max=91234, avg=6120.44, stdev=5012.33
    sync percentiles (usec):
     |  1.00th=[ 1012],  5.00th=[ 1450], 10.00th=[ 2073], 50.00th=[ 5538],
     | 90.00th=[10159], 95.00th=[12780], 99.00th=[22938], 99.90th=[61080]
```

**What it means:**

- Each `fdatasync` by the WAL writer takes 130–160 ms under the backup's load, so every commit waits at least that long. Under normal load on this disk, `fio` shows a median of 5.5 ms and a p99 of 23 ms: acceptable for a small app on HDD, far too slow for etcd (which wants p99 fsync under 10 ms).
- High `f_await` in `iostat` shows the same from the device side.
- Hardware RAID: if the controller's battery or capacitor is failing or in a "learn cycle", the controller switches from write-back to **write-through** and every fsync suddenly takes disk time. That shows up as periodic, unexplained slowness (Step H3); the vendor CLI (storcli, perccli, ssacli) or the BMC shows the cache policy.

> ⚠️ Never "fix" fsync latency by turning durability off (`fsync=off` in
> PostgreSQL, the `nobarrier` mount option, `innodb_flush_log_at_trx_commit=0`)
> on data you care about. A power cut or crash then loses or corrupts
> committed data. Move the fsync-heavy data to faster storage instead.

**Why this step (now):** fsync latency hurts transactional apps far more than
throughput numbers suggest, and it is the one storage property that defines
etcd, database and registry performance.

**Next step:** slow fsync under contention → remove the contention (wrap-up).
Slow fsync even when idle → faster storage for the WAL or etcd data
(NVMe/SSD with power-loss protection, or a working RAID cache). Cloud volume →
Step D6.

### Step D6 — Cloud volume limits: EBS gp2 credits and gp3

**Goal:** detect a volume capped by its IOPS or throughput allowance.

```bash
# On the instance: is IOPS flat at a round number while latency climbs?
iostat -xyz 1 5
lsblk -o NAME,SIZE,SERIAL                 # Nitro NVMe: SERIAL shows the EBS volume ID (vol0abc...)

# Volume type, size, provisioned IOPS and throughput
aws ec2 describe-volumes --filters Name=attachment.instance-id,Values=i-0123456789abcdef0 \
  --query 'Volumes[].[VolumeId,VolumeType,Size,Iops,Throughput]' --output text

# gp2 burst bucket in percent (0 = stuck at baseline)
aws cloudwatch get-metric-statistics --namespace AWS/EBS --metric-name BurstBalance \
  --dimensions Name=VolumeId,Value=vol-0abc1234def567890 \
  --start-time 2026-10-03T00:00:00Z --end-time 2026-10-03T12:00:00Z \
  --period 3600 --statistics Average --output text
```

```
Device            r/s     rkB/s r_await rareq-sz     w/s     wkB/s w_await wareq-sz  aqu-sz  %util
nvme1n1        212.00   3392.00   38.12    16.00   88.00   1408.00   61.40    16.00   13.48  64.20

vol-0abc1234def567890	gp2	100	300	None
BurstBalance
DATAPOINTS	100.0	2026-10-03T00:00:00+00:00	Percent
DATAPOINTS	41.7	2026-10-03T06:00:00+00:00	Percent
DATAPOINTS	0.0	2026-10-03T09:00:00+00:00	Percent
DATAPOINTS	0.0	2026-10-03T11:00:00+00:00	Percent
```

(Columns and datapoints trimmed.)

**What it means:**

- `r/s + w/s` = 300, flat, with 38–61 ms await and `%util` only 64%: the device is not busy, it is **capped**.
- The volume is gp2, 100 GiB. gp2 gives 3 IOPS per GiB (minimum 100), so 300 IOPS baseline, with bursts up to 3,000 IOPS while its credit bucket lasts. `BurstBalance` hit 0% at 09:00; since then it has been held at 300 IOPS.
- gp3 gives 3,000 IOPS and 125 MiB/s baseline regardless of size, with no credits, and more can be provisioned. It is usually also cheaper per GB than gp2.
- Smaller instance types also have an instance-level EBS bandwidth limit, with their own burst balance (CloudWatch `EBSIOBalance%` and `EBSByteBalance%`).
- On-prem, a SAN or vSphere storage policy with an IOPS limit (storage QoS) produces the same signature: a flat line at a round number and rising latency.

**Why this step (now):** no amount of tuning inside the VM raises a cap set
outside it. The flat line at a round number is the tell, and catching it
avoids days of application tuning.

**Next step:** gp2 out of credits → convert to gp3 (wrap-up; online, no
downtime). Instance EBS limit → larger or EBS-optimised instance type.
On-prem QoS cap → storage team. No cap → Step D7 / D8.

### Step D7 — RAID degraded or rebuilding

**Goal:** check whether a software RAID array is degraded, rebuilding or
running its monthly check.

```bash
cat /proc/mdstat
sudo mdadm --detail /dev/md0
sysctl dev.raid.speed_limit_min dev.raid.speed_limit_max
cat /etc/cron.d/mdadm 2>/dev/null; systemctl list-timers 'mdcheck*' --no-pager   # scheduled checks
# Hardware RAID: vendor CLI (storcli / perccli / ssacli) or the BMC web UI (iDRAC / iLO)
```

```
Personalities : [raid1] [linear] [multipath] [raid0] [raid6] [raid5] [raid4] [raid10]
md0 : active raid1 sde1[2] sdd1[0]
      1953382464 blocks super 1.2 [2/1] [U_]
      [=====>...............]  recovery = 27.4% (535226368/1953382464) finish=164.6min speed=143512K/sec
      bitmap: 3/15 pages [12KB], 65536KB chunk

unused devices: <none>
dev.raid.speed_limit_min = 1000
dev.raid.speed_limit_max = 200000
```

**What it means:**

- `[2/1] [U_]`: the array should have 2 members and has 1 working. It is degraded; `sde1` (a replacement disk) is being rebuilt from `sdd1` (`recovery`).
- The rebuild reads and writes at 143 MB/s, competing with application I/O, and will take almost three more hours.
- A degraded RAID5 or RAID6 array also has slower reads, because missing data is reconstructed from parity on every read.
- `check = 12.5%` instead of `recovery` is the scheduled consistency check (Ubuntu runs it monthly, on the first Sunday). Harmless, but it reads the whole array and can make a busy server slow for hours.
- `speed_limit_min`/`max` (KB/s per device) bound the rebuild speed. Lowering the max reduces impact but lengthens the time the array runs without redundancy.

**Why this step (now):** a rebuild or check is invisible to the application
and looks like "the disk got slow for no reason". It also matters for risk: a
second failure during a degraded rebuild loses data.

**Next step:** rebuild in business hours → temporarily lower
`speed_limit_max` (wrap-up), never stop the rebuild. Array degraded with no
rebuild → replace the disk (Step D8). Healthy → Step D8.

### Step D8 — Disk health: SMART and kernel errors

**Goal:** catch a failing disk that has become slow before it fails outright.

```bash
sudo dmesg -T | grep -iE 'i/o error|ata[0-9.]+: (exception|failed)|nvme.*(timeout|reset)|medium error' | tail
sudo smartctl -H /dev/sdb
sudo smartctl -A /dev/sdb | grep -E 'Reallocated_Sector|Current_Pending|Offline_Uncorrectable|UDMA_CRC|Reported_Uncorrect'
sudo smartctl -a /dev/nvme0 | grep -E 'Critical Warning|Percentage Used|Media and Data Integrity|Error Information Log'
iostat -xyz 1 3      # in a RAID set, compare members: one disk with much higher await is the sick one
```

```
[Sat Oct  3 10:05:12 2026] ata3.00: exception Emask 0x0 SAct 0x40000 SErr 0x0 action 0x0
[Sat Oct  3 10:05:12 2026] ata3.00: failed command: READ FPDMA QUEUED
[Sat Oct  3 10:05:12 2026] ata3.00: status: { DRDY ERR }
[Sat Oct  3 10:05:12 2026] ata3.00: error: { UNC }
[Sat Oct  3 10:05:14 2026] blk_update_request: I/O error, dev sdb, sector 1953124352 op 0x0:(READ) flags 0x80700 phys_seg 16 prio class 0
SMART overall-health self-assessment test result: PASSED
  5 Reallocated_Sector_Ct   0x0033   097   097   010    Pre-fail  Always       -       312
187 Reported_Uncorrect      0x0032   076   076   000    Old_age   Always       -       24
197 Current_Pending_Sector  0x0012   100   100   000    Old_age   Always       -       24
198 Offline_Uncorrectable   0x0010   100   100   000    Old_age   Offline      -       24
199 UDMA_CRC_Error_Count    0x003e   200   200   000    Old_age   Always       -       0
```

**What it means:**

- `UNC` (uncorrectable) read errors and an I/O error on `sdb`: the disk cannot read some sectors. Before giving up, it retries internally, which can take seconds per attempt; every process touching those sectors hangs meanwhile. A dying disk is often **slow** long before it is **failed**.
- SMART overall says `PASSED`, but that only means no attribute crossed the vendor's failure threshold. The raw values tell the truth: 312 reallocated sectors and 24 pending/uncorrectable sectors mean the disk is degrading. Plan to replace it.
- `UDMA_CRC_Error_Count` above 0 points at the cable or backplane rather than the disk.
- NVMe: `Percentage Used` near or above 100, or `Media and Data Integrity Errors` above 0, mean the drive is worn or failing.
- In a VM, SMART is not visible; slow storage there is a hypervisor or SAN question.

**Why this step (now):** it is last because it needs the most interpretation,
but it is the cause you must not miss: tuning a disk that is dying wastes the
time you need to replace it while redundancy still exists.

**Next step:** failing disk in an array → replace it (wrap-up); standalone
disk → back up now, then replace. Healthy → the disk is fine and simply
overloaded: back to Step D2 and the wrap-up.

### Disk wrap-up: tree, fix, rollback, prevent

```
I/O wait / D-state / PSI io high?
├── which device? (D1: iostat await, aqu-sz, request size)
│   ├── IOPS flat at round number, latency up → D6 cloud / QoS cap
│   ├── one RAID member much slower, dmesg errors → D8 failing disk
│   ├── recovery / check in /proc/mdstat → D7 rebuild
│   └── genuinely busy → D2 who?
│       ├── batch job (backup, scan, build) → throttle / reschedule
│       ├── kswapd / swap traffic → Section 4
│       ├── database / etcd fsync slow → D5
│       └── filesystem 95%+ full → D4
└── D-state in rpc_* / nfs_* → Section 11 (NFS)
```

**Fix & verify** (pick the one that matches the cause):

```bash
# 1. Throttle a running backup without killing it.
#    ionice classes are honoured by BFQ and (classes only, kernel 5.14+) by mq-deadline;
#    with "none" (the usual NVMe default) they do nothing. Check first:
cat /sys/block/sdb/queue/scheduler            # e.g. [mq-deadline] none
sudo ionice -c3 -p 10421                      # idle class: disk time only when others are not waiting (reads; not page-cache write-back)
#    Works with any scheduler (cgroup v2 io controller): run the job in a throttled scope
sudo systemd-run --scope -p IOReadBandwidthMax='/dev/sdb 20M' -p IOWriteBandwidthMax='/dev/sdb 20M' \
  rsync -a /srv/docker-volumes/ /mnt/backup/volumes/
#    or let rsync limit itself (KB/s)
rsync -a --bwlimit=20000 /srv/docker-volumes/ /mnt/backup/volumes/

# 2. gp2 volume out of credits → gp3 (online; no detach, no downtime)
aws ec2 modify-volume --volume-id vol-0abc1234def567890 --volume-type gp3 --iops 3000 --throughput 125
aws ec2 describe-volumes-modifications --volume-ids vol-0abc1234def567890

# 3. RAID rebuild hurting production: slow it down during business hours
sudo sysctl -w dev.raid.speed_limit_max=50000

# 4. Replace a failing member of an md array. FIRST confirm with mdadm --detail that every
#    OTHER member is "active sync": failing the last good member destroys the array.
sudo mdadm --detail /dev/md0
sudo mdadm /dev/md0 --fail /dev/PARTITION --remove /dev/PARTITION
# ...swap the disk, partition it like the old one, then:
sudo mdadm /dev/md0 --add /dev/PARTITION

# Verify: latency and PSI io back to normal, app latency back to baseline
iostat -xyz 1 3; cat /proc/pressure/io
```

> ⚠️ Freeing space on a Docker host: `docker system prune -a --volumes`
> first removes every **stopped container**, then every unused image and
> (Docker 23 and later) every **anonymous** volume no remaining container
> uses, so a stopped database container's anonymous data volume goes with it.
> `docker volume prune -a` also deletes unused **named** volumes. Start with
> `docker builder prune` (build cache) and `docker image prune` (dangling
> images), check `docker system df -v`, and remove volumes one by one by name.
> Never `rm -rf` inside `/var/lib/docker`.

**Rollback:** remove the scope limits by stopping the scoped command (they
only apply to it). `sudo sysctl -w dev.raid.speed_limit_max=200000` restores
the default. An EBS volume can be modified again only after the previous
modification has completed (the `optimizing` phase can take hours on large
volumes). Since January 2026 AWS allows up to four modifications per volume
in a rolling 24 hours; before that, a 6-hour wait applied, and older guides
still say so. Plan gp3 conversions and do not expect an instant revert (gp3
at 3,000 IOPS is never slower than a gp2 volume at baseline, so a revert is
rarely needed).

**Prevent it next time:**

- Schedule backups and scans outside business hours, and run them throttled (`IOReadBandwidthMax` in the backup's systemd unit, or `--bwlimit`).
- Keep databases, etcd and Docker data on SSD/NVMe; never put the database WAL on the same spinning disk as backups.
- Use gp3 instead of gp2 on AWS, and alarm on `BurstBalance` for any remaining gp2 volume.
- Run `smartd` (package `smartmontools`) and mdadm monitoring (`MAILADDR` in `/etc/mdadm/mdadm.conf`), and alert on disk latency, PSI io and filesystems above 80–85% (section 19).

---

## 6. Network-caused slowness

> 📚 **Study path:** 1) Note: [DNS](08-dns.md) and [Network](02-network.md) as a refresher · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → DNS ([lesson note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)) and Troubleshooting ([lesson note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting); [course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* ([14 min](https://www.youtube.com/watch?v=9nCIjLlLVzY)) · 4) Read: Julia Evans, [Some things about getaddrinfo that surprised me](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/) · 5) Practice: section 20, drill 5 (a dead first resolver), then the [Network speed playbook](24-playbook-network-speed.md).

**Level:** [L2 · Mid]. Juniors should recognise the 5-second DNS signature
(Step N1); conntrack and retransmit analysis belong to Mid-level and up.

This section covers the three network problems that make a **server** feel
slow even though its CPU, memory and disks are fine. Bandwidth, latency,
packet loss and path problems between hosts have their own playbook:
[Network slow / speed troubleshooting](24-playbook-network-speed.md).

### Step N1 — DNS timeouts make everything slow

**Goal:** check whether name lookups stall, which adds seconds to logins,
`sudo`, outbound API calls and database connections that use hostnames.

```bash
time getent ahosts api.example.com        # the resolver path applications actually use (glibc/NSS)
cat /etc/resolv.conf
resolvectl status | sed -n '1,25p'        # Ubuntu: which upstream DNS server is "Current"
# Test each upstream server directly; a dead one times out
dig @192.0.2.53 api.example.com +tries=1 +time=2
dig @192.0.2.54 api.example.com +tries=1 +time=2
```

```
198.51.100.20   STREAM api.example.com
198.51.100.20   DGRAM
198.51.100.20   RAW

real    0m5.019s
user    0m0.002s
sys     0m0.003s

nameserver 192.0.2.53
nameserver 192.0.2.54
search example.internal

;; communications error to 192.0.2.53#53: timed out
;; no servers could be reached

;; ANSWER SECTION:
api.example.com.        300     IN      A       198.51.100.20
```

**What it means:**

- The lookup succeeded but took 5.0 seconds of wall time with almost no CPU: it waited.
- This host uses `/etc/resolv.conf` directly (RHEL-style, or a container) with two nameservers. The first one, 192.0.2.53, does not answer; the second does.
- glibc's defaults are `timeout:5` and `attempts:2`: every lookup first waits 5 s for the dead server, then asks the next one. Every name lookup on the box is now 5 s slower. glibc normally sends the A and AAAA queries together, but `options single-request` (sequential A then AAAA) or several search domains can multiply the wait.
- On Ubuntu with `systemd-resolved` (`nameserver 127.0.0.53`), resolved tracks a "current" server and switches away from dead ones, but lookups still stall while it times out and switches. `resolvectl status` shows which server it is using; [DNS](08-dns.md) shows how to enable its debug log.
- Typical victims: SSH logins (reverse lookup of the client, section 10), `sudo` (looks up the host's own name: add it to `/etc/hosts`), Apache with `HostnameLookups On`, apps connecting to `db.example.internal`, containers (Docker's embedded DNS forwards to the host's upstream servers).

**Why this step (now):** DNS stalls look like "everything is slow" while the
CPU idles, and none of the resource tools in sections 2–5 can see them. A
lookup timed with `getent` is the cheapest possible test.

**Next step:** a dead or slow resolver → fix the resolver list (wrap-up) and
see [DNS](08-dns.md). Lookups fast → Step N2.

### Step N2 — Connection tracking table full

**Goal:** check whether the kernel drops new connections because its
connection-tracking (conntrack) table is full. Docker, Kubernetes, UFW and
any NAT use conntrack.

```bash
sudo dmesg -T | grep -i 'nf_conntrack: table full'
cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max
sudo conntrack -S | head -4                 # per-CPU drop / insert_failed counters (package conntrack)
sudo conntrack -L 2>/dev/null | awk '{print $1}' | sort | uniq -c     # entries per protocol
```

```
[Sat Oct  3 11:20:41 2026] nf_conntrack: nf_conntrack: table full, dropping packet
262144
262144
cpu=0   found=1203 invalid=88 insert=0 insert_failed=41233 drop=41233 early_drop=1820 error=0 search_restart=312
 251802 tcp
  10342 udp
```

**What it means:**

- The table holds 262,144 entries and is completely full. New connections that need an entry are dropped silently.
- Clients retransmit their SYN after 1 s, then 3 s, so the symptom is **random 1–3 second delays and occasional timeouts**, worst under peak traffic. It looks like "slow only sometimes".
- Causes: a traffic spike, many short-lived connections without keep-alive, a very long `ESTABLISHED` timeout (5 days by default), UDP floods (DNS).

**Why this step (now):** conntrack drops are invisible to the application and
to every resource metric; only `dmesg` and these counters show them, and they
are common on busy Docker and Kubernetes hosts.

**Next step:** full or near full → raise the limit (wrap-up) and find out why
it filled (`conntrack -L` by source and destination). Fine → Step N3.

### Step N3 — TCP retransmits

**Goal:** see whether packets are lost between this host and its clients or
dependencies.

```bash
nstat -az TcpRetransSegs TcpOutSegs TcpExtTCPTimeouts TcpExtListenOverflows   # absolute counters
nstat TcpRetransSegs TcpOutSegs                # increments since the previous nstat run
ss -ti state established '( dport = :5432 )' | head -6     # per-connection RTT and retransmits
```

```
#kernel
TcpOutSegs                      912345678          0.0
TcpRetransSegs                  1823456            0.0
TcpExtTCPTimeouts               20311              0.0
TcpExtListenOverflows           0                  0.0

Recv-Q Send-Q   Local Address:Port    Peer Address:Port
0      0          10.0.10.21:48812     10.0.20.15:5432
	 cubic wscale:7,7 rto:412 rtt:208.5/12.1 ato:40 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:4 ssthresh:7 bytes_sent:812345 bytes_retrans:41223 bytes_acked:771122 segs_out:9123 segs_in:8810 retrans:0/57 lastsnd:12 lastrcv:12 lastack:12
```

**What it means:**

- Since boot, 0.2% of segments were retransmitted. Fine as a lifetime figure, but take two `nstat` readings a minute apart for the current rate.
- The connection to the database (10.0.20.15:5432) has an RTT of 208 ms on what should be a sub-millisecond LAN, a small congestion window (`cwnd:4`) and 57 retransmits. Every query on it pays for lost packets and a collapsed window.
- `TcpExtListenOverflows` above 0 and growing means this host's own listen queues overflow (Step A5), which looks like packet loss to clients.

**Why this step (now):** a slow dependency over a lossy link looks exactly
like a slow dependency. Per-connection RTT and retransmits separate "the
database is slow" from "the path to the database is slow".

**Next step:** retransmits or high RTT to one peer → [Network speed playbook](24-playbook-network-speed.md).
Clean network → section 7.

### Network wrap-up: tree, fix, rollback, prevent

```
Server slow, resources fine?
├── time getent ahosts NAME ≈ 5 s / 10 s? → N1 dead resolver → fix resolver list
├── dmesg "nf_conntrack: table full"?    → N2 raise limit, find the flood
├── retrans / high RTT to a peer?        → N3 → module 24 (path, MTU, duplex, loss)
└── none → Section 7 (the application waits on something)
```

**Fix & verify:**

```bash
# Dead resolver on Ubuntu (netplan): edit nameservers in /etc/netplan/*.yaml, then
sudo netplan try            # applies and rolls back automatically unless you confirm within 120 s
# glibc hosts with a static resolv.conf: fail over faster (RHEL: set via NetworkManager, not by hand)
#   options timeout:1 attempts:2 rotate
# sudo slow because the host's own name does not resolve:
grep -q "$(hostname)" /etc/hosts || echo "127.0.1.1 $(hostname)" | sudo tee -a /etc/hosts

# Conntrack: raise the limit now and persist it (each entry costs roughly 300 bytes of RAM)
sudo sysctl -w net.netfilter.nf_conntrack_max=524288
echo 'net.netfilter.nf_conntrack_max = 524288' | sudo tee /etc/sysctl.d/90-conntrack.conf
# If the value is back to the default after a reboot, nf_conntrack loaded after systemd-sysctl ran:
echo nf_conntrack | sudo tee /etc/modules-load.d/conntrack.conf

# Verify
time getent ahosts api.example.com
cat /proc/sys/net/netfilter/nf_conntrack_count /proc/sys/net/netfilter/nf_conntrack_max
```

**Rollback:** `netplan try` reverts by itself if you do not confirm; otherwise
restore the backup of the YAML file and run `sudo netplan apply`. Conntrack:
`sudo sysctl -w net.netfilter.nf_conntrack_max=262144` and delete
`/etc/sysctl.d/90-conntrack.conf` (and `/etc/modules-load.d/conntrack.conf` if you added it). Remove the `/etc/hosts` line if it was wrong.

**Prevent it next time:** monitor every upstream resolver directly (not just
"DNS works"), alert on conntrack usage above 80% and on retransmit ratio
(section 19), and use keep-alive between proxies and backends so each request
does not open a new connection.

---

## 7. Application-level slowness

> 📚 **Study path:** 1) Read: Julia Evans's free zine [Spying on your programs with strace](https://wizardzines.com/zines/strace/) (KodeKloud has nothing on strace) · 2) Note: [Learn: performance & observability](32-learn-performance-observability.md), section 8 (application performance), and [Processes](05-processes.md) · 3) KodeKloud: *Fundamentals of SRE* — Observability and Monitoring ([course](https://kodekloud.com/courses/fundamentals-of-sre)) for RED metrics and latency percentiles · 4) Optional: [Learn: databases for ops](38-learn-databases-ops.md) for Step A6 · 5) Practice: section 20, drill 6 (`strace` a deliberately slow endpoint and name the peer it waits on).

**Level:** [L2 · Mid] for Steps A1, A2, A4, A5 and A10; [L3 · Senior] for
runtime profilers, GC analysis and lock contention (A7–A9), where you hand
developers a stack trace instead of a guess.

When CPU, memory, disk and network all look fine and requests are still slow,
the application is **waiting**: on a database, an upstream API, a lock, a
pool, DNS or a garbage collector. The OS tools so far measure busy
resources; this section measures waiting. The example is `orders-api`, a
Python (gunicorn) service behind Traefik whose requests take about 3 seconds.

### Step A1 — Where does the time go? strace -c

**Goal:** get a syscall-level summary of where a process spends its
wall-clock time.

```bash
# Attach for ~10 s, then Ctrl-C. -f follows all threads, -w measures wall-clock time per call
sudo strace -c -w -f -p PID
```

```
strace: Process 3121 attached with 9 threads
^Cstrace: Process 3121 detached
strace: Process 3122 detached
...
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 61.42   37.912044      473900        80           poll
 23.10   14.258102      678957        21           futex
  9.87    6.091876       24367       250           epoll_wait
  2.31    1.425821        1187      1201           recvfrom
  1.20    0.740699         616      1202           sendto
  2.10    1.296030          52     24923           other
------ ----------- ----------- --------- --------- ----------------
100.00   61.724572        2230     27677           total
```

(As in Step C6, the `other` row is a hand-made sum of the remaining syscalls.)

**What it means:**

- With `-w`, `% time` is **wall-clock** time spent inside each syscall. Without `-w`, strace reports CPU time in the kernel, and a process waiting in `poll()` uses almost none, so the waiting would be invisible.
- 9 threads over about 10 seconds are up to 90 s of thread-time; about 62 s of it was spent inside syscalls, 61% of that in `poll`, averaging 474 ms per call. The process mostly waits for sockets to become readable: for a remote peer to answer.
- `futex` (23%) is threads waiting for each other: locks or condition variables (Step A9).
- `epoll_wait` on idle worker threads is normal (waiting for new requests).

> ⚠️ `strace` uses ptrace and can slow the target 10–100×. Attach for seconds,
> never leave it running on a busy production process. Lower-overhead
> alternatives: `sudo perf trace -s -p PID` and `sudo syscount-bpfcc -L -p PID`.

**Why this step (now):** it splits "the app is slow" into "computing" (little
syscall time, high CPU: go to section 3), "waiting on the network" (`poll`,
`epoll_wait`, `recvfrom`), "waiting on disk" (`read`, `fsync`) or "waiting on
each other" (`futex`) in ten seconds.

**Next step:** waiting on sockets → Step A2 to find which peer. `futex`
dominates → Step A9. `fsync` or `read` dominate → section 5, Step D5.

### Step A2 — Find the slow call with strace -T

**Goal:** see individual slow calls with timestamps, and identify the remote
endpoint behind them.

```bash
sudo strace -f -tt -T -e trace=network,poll,epoll_wait -p PID 2>&1 | head -40
# Which remote endpoint is file descriptor 12 of that process?
sudo ls -l /proc/PID/fd/12
sudo ss -tnp | grep 'pid=PID,'
```

```
[pid  3127] 11:31:07.204118 sendto(12, "Q\0\0\0\216SELECT o.id, o.total, c.name FROM orders o JOIN"..., 143, MSG_NOSIGNAL, NULL, 0) = 143 <0.000037>
[pid  3127] 11:31:07.204201 poll([{fd=12, events=POLLIN|POLLERR}], 1, -1) = 1 ([{fd=12, revents=POLLIN}]) <2.913552>
[pid  3127] 11:31:10.117820 recvfrom(12, "T\0\0\0\36\0\2id\0\0\0@\r\0\1\0\0\0\27\0\4\377\377\377\377\0\0total"..., 16384, 0, NULL, NULL) = 4096 <0.000019>

lrwx------ 1 root root 64 Oct  3 11:31 /proc/3127/fd/12 -> socket:[812345]
ESTAB 0      0      10.0.10.21:48812    10.0.20.15:5432   users:(("gunicorn",pid=3121,fd=12))
```

**What it means:**

- `<2.913552>` is the time the call took. The worker sends a SQL query (`Q` is PostgreSQL's simple-query message) over fd 12, then waits 2.9 s in `poll` for the answer.
- fd 12 is a TCP socket to 10.0.20.15:5432, the PostgreSQL server. The request is slow because **this query** is slow. (`ss -p` names the process, 3121; strace's `[pid 3127]` is one of its threads, and threads share the fd table.)
- Other patterns: a `connect()` to port 53 followed by a 5 s `poll` is DNS (Step N1); a `connect()` whose `poll` takes 1 or 3 s is SYN retransmission (Step N2, N3); a slow `poll` on an HTTPS socket is a slow upstream API.

**Why this step (now):** A1 said "waiting on the network". A2 names the peer
and even the query, which turns a vague slowness ticket into a specific one
for the database or the API owner.

**Next step:** database → Step A6. Upstream API → time it directly with
`curl -w` (section 1). DNS → Step N1. No slow calls at all but requests are
slow → Steps A4, A5 (queueing before the app even sees the request).

### Step A3 — Library calls with ltrace

**Goal:** time calls into shared libraries (DNS resolution, TLS, compression)
when syscalls do not explain the delay.

```bash
sudo ltrace -c -f -p PID                               # summary of library calls (Ctrl-C to stop)
ltrace -f -T -e getaddrinfo curl -so /dev/null https://api.example.com/   # time one function
```

```
[pid 51231] getaddrinfo("api.example.com", "443", 0x7f2b1c000b70, 0x7f2b1c000b48) = 0 <5.012334>
```

**What it means:**

- `getaddrinfo` (name resolution) took 5.0 s: the DNS problem from Step N1, confirmed at the library level.
- `ltrace` is fragile on modern hardened binaries and very slow; if it shows nothing, use `perf` with uprobes or `funclatency-bpfcc` (from `bpfcc-tools`), which time library functions with much lower overhead.

**Why this step (now):** some waits happen inside library code that makes
few syscalls, for example CPU-heavy TLS handshakes or blocking resolver
calls. ltrace is the quick way to time one suspect function.

**Next step:** a slow library call → fix the dependency it waits on (DNS,
TLS, upstream). Nothing obvious → Step A4.

### Step A4 — Too many threads or file descriptors

**Goal:** check whether the process is near its file-descriptor or thread
limits, where new connections fail or queue.

```bash
ps -o pid,nlwp,cmd -p PID                     # nlwp = number of threads
sudo ls /proc/PID/fd | wc -l                  # open file descriptors now
grep -E 'Max open files|Max processes' /proc/PID/limits
systemctl show UNIT -p LimitNOFILE -p LimitNOFILESoft -p TasksMax -p TasksCurrent
cat /proc/sys/fs/file-nr                      # system-wide: allocated, unused, maximum
# What kinds of fds? (sockets, files, pipes)
sudo ls -l /proc/PID/fd | awk 'NR>1 {print $NF}' | sed 's/:.*//' | sort | uniq -c | sort -rn | head -5
```

```
    PID NLWP CMD
   3121  103 /usr/bin/python3 /usr/local/bin/gunicorn -w 4 --threads 100 app:app
1021
Max open files            1024                 524288               files
Max processes             31439                31439                processes
LimitNOFILE=524288
LimitNOFILESoft=1024
TasksMax=9431
TasksCurrent=431
12352	0	9223372036854775807
    988 socket
     21 /srv/app/logs/app.log
      8 anon_inode
```

**What it means:**

- 1,021 open descriptors against a **soft** limit of 1,024: the next `accept()` or `open()` fails with "Too many open files" (EMFILE). Depending on the app, new connections hang, get reset, or produce 500 errors.
- systemd's default for services is a soft limit of 1,024 and a hard limit of 524,288. `ulimit -n` in your shell does **not** apply to services started by systemd or Docker; the limit comes from the unit (`LimitNOFILE=`) or the container (`--ulimit nofile=`).
- 988 of the descriptors are sockets: either many concurrent clients or a socket leak (a count that only ever grows).
- 103 threads in this one worker: gunicorn runs each of its 4 workers as a separate process, and `--threads 100` gives each of them 100 request threads plus a few of its own. The whole unit holds 431 tasks (`TasksCurrent`). Thread counts in the hundreds cost memory and context switches; `TasksMax` caps them per unit and produces "fork: Resource temporarily unavailable" when hit.

**Why this step (now):** limits fail in ugly, intermittent ways (some
requests hang, some error) that look like slowness, and they are invisible in
resource graphs.

**Next step:** near the fd limit → raise it in the unit or container (wrap-up)
and check for a leak (count over time). Within limits → Step A5.

### Step A5 — Connection pools, worker limits and accept queues

**Goal:** check whether requests queue **before** the application processes
them: a full listen queue, all Apache workers busy, or an exhausted database
connection pool.

```bash
# Listen sockets: Recv-Q = connections waiting to be accepted, Send-Q = backlog size
ss -ltn '( sport = :443 or sport = :8000 )'
nstat -az TcpExtListenOverflows TcpExtListenDrops
# Apache workers (mod_status, localhost only on Ubuntu) and the "out of workers" message
curl -s 'http://127.0.0.1/server-status?auto' | grep -E '^(BusyWorkers|IdleWorkers|ReqPerSec)'
sudo grep -hE 'AH00161|AH00484|reached MaxRequestWorkers' /var/log/apache2/error.log | tail -3
# Connections from this host to the database, compared with the app's pool size
ss -tn state established '( dport = :5432 )' | tail -n +2 | wc -l
# PostgreSQL side: connections by state
sudo -u postgres psql -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state ORDER BY 2 DESC;"
```

```
State   Recv-Q  Send-Q   Local Address:Port   Peer Address:Port
LISTEN  512     511            0.0.0.0:443         0.0.0.0:*
LISTEN  0       2048         127.0.0.1:8000        0.0.0.0:*
TcpExtListenOverflows           48211              0.0
TcpExtListenDrops               48211              0.0
ReqPerSec: 41.2
BusyWorkers: 150
IdleWorkers: 0
[Sat Oct 03 11:02:13.441234 2026] [mpm_prefork:error] [pid 1187] AH00161: server reached MaxRequestWorkers setting, consider raising the MaxRequestWorkers setting
20
        state        | count
---------------------+-------
 active              |    20
 idle                |     3
 idle in transaction |     2
```

**What it means:**

- Port 443 (Apache): `Recv-Q` 512 is one more than the backlog `Send-Q` 511, which is how a full accept queue looks (the kernel admits backlog + 1 before it overflows), and `ListenOverflows` keeps rising. The kernel drops new connection attempts; clients retry after 1 s, 3 s and so on. Users see slow or failed page loads even though the server's CPU might be idle.
- All 150 Apache workers are busy and none idle, and the error log says so explicitly (AH00161 for prefork, AH00484 for the event MPM; grepping for the text "reached MaxRequestWorkers" catches every MPM). Each prefork worker handles one request; if requests are slow (waiting on the database), workers run out.
- 20 connections to PostgreSQL, all active, equal to the app's pool size of 20: every connection is busy and other requests wait **inside the app** for a free one. That wait does not appear in any OS metric, only in the app's logs ("timeout waiting for connection from pool", HikariCP's "Connection is not available, request timed out").
- `idle in transaction` connections hold a pool slot and their locks while doing nothing: an application bug (a transaction left open).

**Why this step (now):** queueing in front of the app (accept queue, workers,
pools) multiplies a small slowness downstream into a large one upstream. It
also warns you against the obvious wrong fix: raising `MaxRequestWorkers` or
the pool size when the real cause is slow queries just pushes more load onto
the database.

**Next step:** pool or workers exhausted because each request is slow → find
why the requests are slow (Step A6 database, Step A2 upstream). Exhausted
because of more traffic → capacity (more workers that fit in RAM, see the
memory wrap-up; or rate limits). `idle in transaction` → application bug,
report it.

### Step A6 — Slow database queries

**Goal:** see which queries are running long right now and who blocks whom.
(Database tuning itself is outside this handbook; this is the pointer.)

```bash
# PostgreSQL: longest-running statements now
sudo -u postgres psql -c "SELECT pid, now()-query_start AS runtime, state, wait_event_type, left(query,70) AS query
  FROM pg_stat_activity WHERE state <> 'idle' ORDER BY runtime DESC LIMIT 8;"
# PostgreSQL: blocked sessions and their blockers
sudo -u postgres psql -c "SELECT pid, pg_blocking_pids(pid) AS blocked_by, left(query,60) AS query
  FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;"
# MySQL / MariaDB: running statements, slowest first
sudo mysql -e "SELECT id, user, time, state, left(info,70) AS query FROM information_schema.processlist
  WHERE command <> 'Sleep' ORDER BY time DESC LIMIT 8;"
# Database in a container: same queries through docker exec
docker exec -it CONTAINER psql -U USER -d DB -c "SELECT ... ;"
```

```
  pid  |     runtime     | state  | wait_event_type |                                 query
-------+-----------------+--------+-----------------+------------------------------------------------------------------------
 41233 | 00:00:02.871203 | active | IO              | SELECT o.id, o.total, c.name FROM orders o JOIN customers c ON c.id = o
 41240 | 00:00:02.640118 | active | IO              | SELECT o.id, o.total, c.name FROM orders o JOIN customers c ON c.id = o
 41251 | 00:00:01.902277 | active | Lock            | UPDATE orders SET status = 'paid' WHERE id = $1
```

**What it means:**

- The same `orders`/`customers` join runs for almost 3 s and waits on `IO`: probably a sequential scan of a large table (a missing index), reading from disk.
- An `UPDATE` waits on a `Lock`: someone holds a row lock (often an `idle in transaction` session from Step A5).
- Next stops for the DBA or developer: `EXPLAIN (ANALYZE, BUFFERS)` of the slow query, the slow-query log (`log_min_duration_statement = 500ms` in PostgreSQL, `slow_query_log = ON` with `long_query_time = 1` in MySQL), and `pg_stat_statements` for the top queries by total time.

**Why this step (now):** Step A2 or A5 pointed at the database. This shows
whether it is one bad query, lock contention or general overload, which
decides whether the fix is an index, an application change or database
capacity.

**Next step:** one slow query → index or query fix (developers/DBA). Locks →
find and end the blocking session after agreeing with the app owner, then
fix the code. Database host itself slow → run section 2 on the database
server.

### Step A7 — JVM garbage-collection pauses

**Goal:** check whether a Java service stops for garbage collection.

```bash
# jstat/jcmd find the JVM through /tmp/hsperfdata_USER (jcmd then attaches over /tmp/.java_pid<PID>): run them as the JVM's user, or inside the container
sudo -u APPUSER jstat -gcutil PID 1000 5
docker exec CONTAINER jstat -gcutil 1 1000 5          # JVM as PID 1 in the container (needs a JDK image)
docker exec CONTAINER jcmd 1 GC.heap_info
# Thread dumps: three, 5 s apart, to see what threads are stuck on
for i in 1 2 3; do docker exec CONTAINER jcmd 1 Thread.print > /var/tmp/jstack-$i.txt; sleep 5; done
```

```
  S0     S1     E      O      M     CCS    YGC     YGCT     FGC    FGCT     CGC    CGCT       GCT
  0.00   0.00 100.00  99.91  97.12  93.40   2412   48.112   311  1290.551    18    0.912  1339.575
  0.00   0.00 100.00  99.91  97.12  93.40   2412   48.112   311  1290.551    18    0.912  1339.575
  0.00   0.00 100.00  99.93  97.12  93.40   2412   48.112   312  1294.807    18    0.912  1343.831
  0.00   0.00  12.40  99.90  97.12  93.40   2412   48.112   312  1294.807    18    0.912  1343.831
```

**What it means:**

- `O` (old generation) is 99.9% full, and `FGC` (full GC count) increases: the JVM runs full collections that free almost nothing.
- `FGCT / FGC` = 1294.8 / 312 ≈ 4.2 s per full GC. During a full GC every application thread is stopped, so requests that arrive meanwhile wait 4 seconds.
- Either the heap is too small for the live data (raise it, if the host has memory; see section 4), or something retains objects (a leak; take a heap dump for the developers, see the warning in Step M6).
- In a thread dump, many threads in `BLOCKED` state "waiting to lock" the same object point to lock contention (Step A9). JRE-only images lack `jcmd`/`jstat`; use a JDK image for debugging or enable GC logging (`-Xlog:gc*:file=/var/log/app/gc.log`).

**Why this step (now):** GC pauses produce exactly the "slow sometimes, for a
few seconds, then fine" pattern, with CPU spent on GC threads (Step C4) and no
other resource saturated. jstat proves it in five seconds.

**Next step:** heap full after full GCs → heap sizing or leak (section 4,
Step M6). GC healthy → Step A9 (locks) or Step A2.

### Step A8 — Python, PHP, Node and other runtimes

**Goal:** see the application-level stack of a running process in its own
language, without restarting it.

```bash
# Python: py-spy (pip install py-spy). Run it on the host against the host PID;
# inside a container it needs the SYS_PTRACE capability.
sudo py-spy dump --pid PID                     # current stack of every thread
sudo py-spy top --pid PID                      # live "top" of Python functions
sudo py-spy record -o /var/tmp/profile.svg --pid PID --duration 30    # flame graph
# PHP-FPM: log a stack trace for any request slower than 5 s (pool config, then reload)
#   request_slowlog_timeout = 5s
#   slowlog = /var/log/php8.1-fpm-slow.log
# Node.js: start with --cpu-prof (CPU profile on exit) or --inspect and attach DevTools
# Go: import net/http/pprof, then: go tool pprof http://127.0.0.1:6060/debug/pprof/profile?seconds=30
```

```
Process 3121: /usr/bin/python3 /usr/local/bin/gunicorn -w 4 --threads 100 app:app
Python v3.10.12 (/usr/bin/python3.10)

Thread 3127 (idle): "ThreadPoolExecutor-0_7"
    execute (psycopg2/extras.py:146)
    _execute_context (sqlalchemy/engine/base.py:1900)
    execute (sqlalchemy/orm/session.py:1717)
    list_orders (shop/views.py:88)
    dispatch_request (flask/app.py:1799)
```

**What it means:**

- The thread is `idle` from Python's point of view (blocked in C code, GIL released) inside a database `execute` called from `list_orders` in `shop/views.py` line 88. The same story as Step A2, now with the exact line of application code.
- `active` threads with stacks in your own code are burning CPU; `py-spy top` ranks them.
- mod_php under Apache has no slow log; PHP-FPM does, and it is the best tool for slow PHP requests.

**Why this step (now):** OS tools see syscalls and native functions; language
profilers see the function and line in the developer's code. That is the
evidence that gets a fix scheduled.

**Next step:** hand the stack to the developers; mitigate meanwhile (cache,
rate-limit, scale). Waiting on locks → Step A9.

### Step A9 — Lock contention

**Goal:** detect threads that spend their time waiting for each other.

```bash
pidstat -w -p PID 1 5                        # many voluntary switches + low CPU = waiting
sudo strace -c -w -f -p PID                  # futex dominating wall time = waiting on locks
sudo offcputime-bpfcc -p PID 10              # stacks where threads sleep, over 10 s (bpfcc-tools)
grep -c 'java.lang.Thread.State: BLOCKED' /var/tmp/jstack-1.txt
grep 'waiting to lock' /var/tmp/jstack-1.txt | sort | uniq -c | sort -rn | head -3
lslocks                                      # file locks held on this host
```

```
11:40:10      UID       PID   cswch/s nvcswch/s  Command
11:40:11     1001      2817  24812.00    120.00  java
87
     84 	- waiting to lock <0x00000006c1a2b3c8> (a com.example.shop.cache.PriceCache)
      3 	- waiting to lock <0x00000006c0f00a10> (a java.util.Hashtable)
```

**What it means:**

- 24,812 voluntary context switches per second with low CPU: threads constantly block and wake up.
- 87 threads are `BLOCKED`, 84 of them waiting for the same monitor on a `PriceCache` object. One `synchronized` method serialises the whole application: only one request at a time can use the cache.
- Other common locks: database row locks (Step A6), PHP file-based sessions (one slow request blocks every other request from the same user, because the session file is locked), SQLite (one writer at a time), file locks shown by `lslocks`.
- In `perf top`, kernel symbols such as `native_queued_spin_lock_slowpath` mean kernel-level spinlock contention instead.

**Why this step (now):** lock contention caps throughput no matter how many
CPUs you add, and it shows up as idle CPUs with slow requests, which every
earlier step would call "not a resource problem".

**Next step:** report the contended lock with the thread dump to the
developers. Short-term: reduce concurrency or traffic to the contended path.

### Step A10 — Read latency from the access logs

**Goal:** get RED numbers (rate, errors, duration) per vhost and URL from the
logs you already have, and separate proxy time from backend time.

```bash
# Apache: log the vhost (%v) and the response time in microseconds (%D). In apache2.conf:
#   LogFormat "%v %h %l %u %t \"%r\" %>s %b %D" vhost_timed
#   CustomLog ${APACHE_LOG_DIR}/timed_access.log vhost_timed
sudo apache2ctl configtest && sudo systemctl reload apache2

# p50 / p95 / p99 over the last 10,000 requests (last field = %D in microseconds)
tail -n 10000 /var/log/apache2/timed_access.log | awk '{print $NF}' | sort -n | awk '{a[NR]=$1}
  END {printf "n=%d p50=%.0fms p95=%.0fms p99=%.0fms max=%.0fms\n", NR, a[int(NR*0.50)]/1000,
  a[int(NR*0.95)]/1000, a[int(NR*0.99)]/1000, a[NR]/1000}'
# Slowest requests with vhost and path ($1 = vhost, $8 = path)
tail -n 10000 /var/log/apache2/timed_access.log | awk '{printf "%.0f ms %s %s\n", $NF/1000, $1, $8}' | sort -rn | head -5
# Busiest clients (crawler? attack?)
tail -n 10000 /var/log/apache2/timed_access.log | awk '{print $2}' | sort | uniq -c | sort -rn | head -5

# Traefik (Dokploy): JSON access log, Duration and OriginDuration in nanoseconds
docker logs --since 10m dokploy-traefik 2>&1 | grep '"Duration"' \
  | jq -r '[(.Duration/1000000|floor), (.OriginDuration/1000000|floor), .RequestHost, .RequestPath, .DownstreamStatus] | @tsv' \
  | sort -rn | head -5
```

```
n=10000 p50=84ms p95=2912ms p99=4120ms max=9871ms
9871 ms shop.example.com /search?q=%25a%25b%25c&sort=price
9620 ms shop.example.com /search?q=%25x%25y&sort=name
4410 ms shop.example.com /orders/export
   4120 198.51.100.23
    312 203.0.113.41
    188 192.0.2.77

3012	2998	api.example.com	/v1/orders	200
2871	2860	api.example.com	/v1/orders	200
```

**What it means:**

- p50 84 ms but p95 2.9 s and p99 4.1 s: most requests are fast, a minority are very slow. The average would hide this completely.
- The slowest requests are all `/search` on `shop.example.com`, and 41% of recent requests come from one IP: the crawler from section 3.
- Traefik: `Duration` (total) 3,012 ms, `OriginDuration` (time waiting for the backend) 2,998 ms. Traefik itself adds about 14 ms; the backend is slow. If `Duration` were much larger than `OriginDuration`, the time would be in the proxy or the client connection.
- nginx has the same split: `$request_time` (total) versus `$upstream_response_time` (backend).
- Traefik writes its access log to stdout or to the file set in `accessLog.filePath` in its static configuration; on Dokploy, check the Traefik configuration in the web UI. Access logging must be enabled first, and in JSON format (`accessLog.format: json`; the default is the text "common" format) for the `jq` command above to work.

**Why this step (now):** logs give you per-URL, per-vhost latency history for
free, including for the minutes before you were paged. They answer "which
endpoint", "since when" and "for which clients" without touching the process.

**Next step:** one endpoint slow → Steps A2, A6, A8 on the process serving it.
One client dominating → rate-limit or block (CPU wrap-up). Backend fast but
total slow → proxy or network: [Site down playbook](25-playbook-site-down.md),
[Network speed](24-playbook-network-speed.md).

### Application wrap-up: tree, fix, rollback, prevent

```
Resources fine, requests slow → the app waits. On what?
├── strace -c -w (A1): poll/recvfrom dominate → A2: which peer?
│   ├── database → A6 (slow query, locks)
│   ├── upstream API → curl -w to it directly
│   └── port 53 / getaddrinfo slow → N1 DNS
├── futex dominates / many BLOCKED threads → A9 lock contention
├── Recv-Q > backlog, AH00161, pool at max → A5 queueing in front of the app
├── fd count near limit → A4 limits
├── JVM: O ≈ 100%, FGC rising → A7 GC
└── need the line of code → A8 (py-spy, PHP-FPM slowlog, pprof) / C5 perf
```

**Fix & verify:**

```bash
# Raise the fd limit for a systemd service
sudo systemctl edit UNIT
#   [Service]
#   LimitNOFILE=65536
sudo systemctl restart UNIT
grep 'Max open files' /proc/$(systemctl show -p MainPID --value UNIT)/limits

# Containers: per-container ulimit (or default-ulimits in /etc/docker/daemon.json)
docker run --ulimit nofile=65536:65536 IMAGE

# Verify against the same measurement as before the fix
tail -n 2000 /var/log/apache2/timed_access.log | awk '{print $NF}' | sort -n | awk '{a[NR]=$1} END {print "p95=" a[int(NR*0.95)]/1000 "ms"}'
```

Most application fixes belong to the developers (an index, a query, a lock, a
leak). Your job is the evidence: the slow call with its duration (A2), the
stack (C4, A7, A8), the percentile numbers (A10), and a mitigation that buys
time (rate limit, cache, more workers that fit in RAM, a rollback).

**Rollback:** `sudo systemctl revert UNIT` removes drop-ins created with
`systemctl edit`, then `sudo systemctl restart UNIT`. Application changes roll
back by redeploying the previous version (Dokploy keeps previous deployments;
`docker service rollback SERVICE` for Swarm; `kubectl rollout undo` for
Kubernetes).

**Prevent it next time:**

- Log request duration in every access log (Apache `%D`, nginx `$request_time`, Traefik access log) and graph p95/p99 per vhost.
- Set explicit timeouts everywhere: database statement timeouts, HTTP client timeouts, pool wait timeouts. A request that fails after 2 s is better than one that holds a worker for 60 s.
- Enable slow-query logs on every database and review them weekly.
- Size pools and workers on purpose: workers × memory per worker must fit in RAM, and pool size × number of app instances must stay below the database's `max_connections`.

---

## 8. Slow only sometimes

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Locate and Analyze System Log Files ([lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 2) Note: [Logs & journal](06-logs-journal.md) · 3) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals → Node Exporter ([lesson note](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page); [course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 4) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([68 min](https://www.youtube.com/watch?v=6xmWr7p5TE0)) · 5) Practice: section 20, drill 7 (a cron job that hurts at a fixed minute, found from history only), then the L4 node_exporter drill in section 19.

**Level:** [L2 · Mid] for sar, atop, cron and journal correlation (H1–H4);
[L4 · Lead] for monitoring-driven analysis and automatic evidence capture
(H5–H6).

"It was slow at 2 a.m." or "every now and then it hangs for a minute" cannot
be debugged live. You need **history**: what each resource did at that
minute, which processes were active, which jobs started. Without history the
only honest answer is "set up recording and wait for it to happen again", so
the real lesson of this section is to switch recording on **before** you need
it. The example: users report the API was slow between about 02:00 and 02:30.

### Step H1 — sar history: what happened at 02:10?

**Goal:** see each resource's state at the time of the complaint.

```bash
ls /var/log/sysstat/                     # Ubuntu/Debian: saDD files (DD = day of month); RHEL: /var/log/sa/
F=/var/log/sysstat/sa03                  # 3rd of the month
sar -q -f $F -s 01:50:00 -e 02:40:00     # run queue, load, blocked tasks
sar -u -f $F -s 01:50:00 -e 02:40:00     # CPU split (us, sy, iowait, steal)
sar -r -f $F -s 01:50:00 -e 02:40:00     # memory
sar -B -f $F -s 01:50:00 -e 02:40:00     # paging (majflt/s, pgscand/s)
sar -d -p -f $F -s 01:50:00 -e 02:40:00  # per-device latency (-p = readable device names)
sar -n DEV -f $F -s 01:50:00 -e 02:40:00 # network
```

```
01:50:01      runq-sz  plist-sz   ldavg-1   ldavg-5  ldavg-15   blocked
02:00:01            1       418      0.62      0.71      0.69         0
02:10:01            2       431      9.84      6.12      2.88        11
02:20:01            1       427      8.91      7.95      4.71         9
02:30:01            0       419      0.88      3.10      3.92         0

01:50:01          DEV       tps     rkB/s     wkB/s     dkB/s   areq-sz    aqu-sz     await     %util
02:00:01          sdb     31.20    210.44    402.12      0.00     19.61      0.18      5.80      9.12
02:10:01          sdb    412.31  51230.12   2210.44      0.00    129.61     41.20     99.92     99.81
02:20:01          sdb    398.02  49812.40   2087.91      0.00    130.40     38.77     97.40     99.60
02:30:01          sdb     29.88    188.12    388.70      0.00     19.30      0.16      5.41      8.70
```

**What it means:**

- Between 02:00 and 02:30, load jumped to about 9 with 9–11 tasks **blocked**, while the run queue stayed small: an I/O problem, not CPU.
- `sdb` went from 31 to 412 operations per second, reading about 50 MB/s in 130 KB requests, with 100 ms latency. Something read the data disk sequentially for 30 minutes, then stopped.
- sar's default interval is 10 minutes, so a 2-minute spike is averaged away. Shorten the interval if your problems are short (below).

**Enable or tune collection** (Ubuntu 22.04 ships it disabled. On Ubuntu 24.04
`sysstat` is part of the default install and fresh systems usually collect
from the first boot, even though `/etc/default/sysstat` may still say
`ENABLED="false"`; check with `systemctl is-enabled sysstat` and
`ls /var/log/sysstat/`):

```bash
sudo sed -i 's/^ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
sudo systemctl enable --now sysstat
systemctl list-timers 'sysstat*' --no-pager
# Optional: sample every 2 minutes instead of 10
sudo systemctl edit sysstat-collect.timer
#   [Timer]
#   OnCalendar=
#   OnCalendar=*:00/2
# History length: HISTORY= in /etc/sysstat/sysstat (Ubuntu default 7 days)
```

**Why this step (now):** sar is the cheapest, most widely available history
of every resource. It turns "slow at 2 a.m." into "disk-bound from 02:00 to
02:30", which narrows the search to whatever started at 02:00.

**Next step:** a resource spiked → Step H2 to find which process. No sar data
→ enable it now, and use the journal (Step H4) and monitoring (Step H5) for
this occurrence.

### Step H2 — atop logs: which process, at that minute

**Goal:** see per-process CPU, memory and disk usage at a past time. sar
shows resources; atop also records processes.

```bash
sudo apt install atop                     # logs every 10 minutes by default to /var/log/atop/
sudo atop -r /var/log/atop/atop_20261003 -b 02:00 -e 02:30
#   t / T = next / previous sample, d = disk view, m = memory view, c = full command lines, q = quit
atopsar -r /var/log/atop/atop_20261003 -b 02:00 -e 02:30 -D    # top-3 disk consumers per sample
atopsar -r /var/log/atop/atop_20261003 -b 02:00 -e 02:30 -O    # top-3 CPU consumers per sample
# Finer history: LOGINTERVAL=60 in /etc/default/atop, then: sudo systemctl restart atop
```

```
02:10:01   pid command   dsk% |  pid command   dsk% |  pid command  dsk%
02:10:01 10421 rsync      81% | 1290 postgres    9% |  398 jbd2/sdb  4%
02:20:01 10421 rsync      79% | 1290 postgres   11% |  398 jbd2/sdb  5%
```

(atopsar output abbreviated.)

**What it means:**

- `rsync` (PID 10421) did 80% of all disk activity during the slow window. PostgreSQL was the victim, not the cause.
- In interactive `atop -r`, pressing `c` shows the full command line (which backup, which paths), and `d` sorts processes by disk usage for that sample.

**Why this step (now):** it names the culprit for a time you were not there,
which no live tool can do. atop's process-level history is the single most
useful thing to have installed on a server that is "slow sometimes".

**Next step:** a known process → Step H3 to find what schedules it. A
process you do not recognise → its parent, unit and owner (`atop` shows the
PPID; then [Ports & services inventory](22-playbook-ports-inventory.md) for
mapping processes to services).

### Step H3 — Correlate with cron, timers, backups and logrotate

**Goal:** find which scheduled job starts at the time of the slowness.

```bash
systemctl list-timers --all --no-pager
ls /etc/cron.d /etc/cron.hourly /etc/cron.daily /etc/cron.weekly
grep -hvE '^\s*(#|$)' /etc/crontab /etc/cron.d/* 2>/dev/null
for u in $(cut -d: -f1 /etc/passwd); do sudo crontab -l -u "$u" 2>/dev/null | grep -vE '^\s*(#|$)' | sed "s/^/$u: /"; done
journalctl -u cron --since "2026-10-03 01:55" --until "2026-10-03 02:15" --no-pager    # RHEL: -u crond
# Containers and clusters schedule work too
kubectl get cronjobs -A
```

```
NEXT                        LEFT       LAST                        PASSED      UNIT                     ACTIVATES
Sat 2026-10-03 11:50:00 UTC 4min left  Sat 2026-10-03 11:40:00 UTC 5min ago    sysstat-collect.timer    sysstat-collect.service
Sun 2026-10-04 00:00:00 UTC 12h left   Sat 2026-10-03 00:00:00 UTC 11h ago     logrotate.timer          logrotate.service
Sun 2026-10-04 03:10:00 UTC 15h left   Sun 2026-09-27 03:10:01 UTC 6 days ago  e2scrub_all.timer        e2scrub_all.service
Sun 2026-10-04 06:31:12 UTC 18h left   Sat 2026-10-03 06:12:40 UTC 5h ago      apt-daily-upgrade.timer  apt-daily-upgrade.service
Mon 2026-10-05 00:41:20 UTC 1 day 12h  Mon 2026-09-28 00:12:09 UTC 5 days ago  fstrim.timer             fstrim.service

0 2 * * * root /usr/local/sbin/backup-volumes.sh
57 0 * * 0 root if [ -x /usr/share/mdadm/checkarray ] && [ $(date +\%d) -le 7 ]; then /usr/share/mdadm/checkarray --cron --all --idle --quiet; fi

Oct 03 02:00:01 web01 CRON[10418]: (root) CMD (/usr/local/sbin/backup-volumes.sh)
```

**What it means:**

- `/etc/cron.d` contains a backup at `0 2 * * *` (every day at 02:00), and the cron log confirms it started at 02:00:01. Together with Steps H1 and H2, that closes the case.
- The second cron line is Ubuntu's monthly RAID check (Step D7).
- Usual suspects on Ubuntu and in your stack:

| Job | When | What it costs |
|---|---|---|
| `logrotate.timer` | daily around 00:00 | compressing large logs (CPU, disk); reloads services |
| `apt-daily.timer`, `apt-daily-upgrade.timer` | twice daily (randomised) and around 06:00–07:00 | downloads, unpacking, service restarts by unattended-upgrades |
| `fstrim.timer` | weekly (Monday) | discards can stall some SSDs and SAN volumes |
| `e2scrub_all.timer` | weekly (Sunday 03:10) | LVM snapshot plus filesystem check |
| `man-db.timer`, `plocate-updatedb.timer` | daily (randomised) | scanning the filesystem |
| mdadm `checkarray` or `mdcheck` timers | monthly (first Sunday) | reads the whole RAID array |
| Backups (rsync, restic, database dumps, Dokploy scheduled backups) | site-specific | disk and network |
| Image builds (Dokploy on the server, GitLab runner on the same host) | on every push | CPU, memory, disk |
| Harbor garbage collection, registry replication | scheduled in Harbor | disk on the registry host |
| Kubernetes CronJobs, etcd defragmentation | site-specific | node CPU, disk |
| RAID controller battery learn cycle | vendor schedule (often monthly) | write-through mode: slow fsync (Step D5) |

**Why this step (now):** periodic slowness is almost always a periodic job.
Matching the start time from history against the schedule is faster than any
amount of live analysis, because the cause is not running right now.

**Next step:** found the job → make it polite or move it (wrap-up). No
scheduled job matches → Step H4 (the logs) and Step H5 (traffic, external
dependencies).

### Step H4 — The journal around the bad minutes

**Goal:** read everything the system logged in the slow window.

```bash
journalctl --since "2026-10-03 02:00" --until "2026-10-03 02:30" -p warning --no-pager
journalctl --since "2026-10-03 02:00" --until "2026-10-03 02:30" -o short-precise --no-pager | less
journalctl -k --since "2026-10-03 02:00" --until "2026-10-03 02:30" --no-pager       # kernel only
journalctl -b -1 -p err --no-pager | tail -30            # the previous boot, if it rebooted
journalctl --list-boots --no-pager | tail -3             # only one boot listed = journal not persistent
```

```
Oct 03 02:00:01 web01 CRON[10418]: (root) CMD (/usr/local/sbin/backup-volumes.sh)
Oct 03 02:04:12 web01 kernel: INFO: task postgres:1290 blocked for more than 120 seconds.
Oct 03 02:11:40 web01 dockerd[1187]: time="2026-10-03T02:11:40.118Z" level=warning msg="Health check for container 3f1c2a9e5b7d failed: context deadline exceeded"
Oct 03 02:31:02 web01 backup-volumes.sh[10418]: backup finished: 87.4 GiB in 30m59s
```

**What it means:**

- The backup's start and end bracket the slow window exactly.
- PostgreSQL blocked for over two minutes on I/O, and a container health check timed out. In Swarm, failed health checks cause task restarts, which can turn a slow period into an outage.
- On Ubuntu the journal is persistent by default. If `--list-boots` shows only the current boot, create `/var/log/journal` and restart `systemd-journald` so the next incident keeps its history.

**Why this step (now):** the journal provides the narrative (what started,
what failed, what restarted) around the numbers from sar and atop, and it is
often where the consequences show up, such as health-check failures.

**Next step:** cause found → wrap-up. Still nothing → Step H5.

### Step H5 — Monitoring graphs and the questions to ask them

**Goal:** use long-term metrics to see the pattern: when, how often, which
hosts, and what else changed at the same moment.

Useful PromQL for node_exporter (Prometheus) dashboards in Grafana:

```
# CPU busy, iowait and steal (fraction of time, per instance)
1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))
avg by (instance) (rate(node_cpu_seconds_total{mode="iowait"}[5m]))
avg by (instance) (rate(node_cpu_seconds_total{mode="steal"}[5m]))
# Pressure (seconds per second = fraction of time): *_waiting_* = PSI "some", *_stalled_* = PSI "full"
rate(node_pressure_cpu_waiting_seconds_total[5m])
rate(node_pressure_memory_stalled_seconds_total[5m])
rate(node_pressure_io_stalled_seconds_total[5m])
# Memory headroom and swap-in activity
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
rate(node_vmstat_pswpin[5m])
# Average disk read latency per device (seconds)
rate(node_disk_read_time_seconds_total[5m]) / rate(node_disk_reads_completed_total[5m])
# TCP retransmit ratio and conntrack usage
rate(node_netstat_Tcp_RetransSegs[5m]) / rate(node_netstat_Tcp_OutSegs[5m])
node_nf_conntrack_entries / node_nf_conntrack_entries_limit
# Traefik p95 latency per service
histogram_quantile(0.95, sum by (le, service) (rate(traefik_service_request_duration_seconds_bucket[5m])))
```

You can ask the same questions from a shell through Prometheus's read-only
HTTP API, which is handy for pasting numbers into the ticket:

```bash
# I/O pressure on web01 over the slow window, one point per 5 minutes (times in UTC)
curl -s 'http://PROMETHEUS:9090/api/v1/query_range' \
  --data-urlencode 'query=rate(node_pressure_io_stalled_seconds_total{instance="web01:9100"}[5m])' \
  --data-urlencode 'start=2026-10-03T01:50:00Z' --data-urlencode 'end=2026-10-03T02:40:00Z' \
  --data-urlencode 'step=300' \
  | jq -r '.data.result[0].values[] | "\(.[0] | todate)  \(.[1] | tonumber * 100 | floor)% stalled"'
```

```
2026-10-03T01:50:00Z  0% stalled
2026-10-03T01:55:00Z  0% stalled
2026-10-03T02:00:00Z  3% stalled
2026-10-03T02:05:00Z  31% stalled
2026-10-03T02:10:00Z  38% stalled
2026-10-03T02:15:00Z  36% stalled
2026-10-03T02:20:00Z  35% stalled
2026-10-03T02:25:00Z  33% stalled
2026-10-03T02:30:00Z  12% stalled
2026-10-03T02:35:00Z  0% stalled
2026-10-03T02:40:00Z  1% stalled
```

**What it means:**

- `rate(...stalled_seconds_total[5m])` is "seconds stalled per second", so 0.38 means that for 38% of the time **every** non-idle task was waiting for I/O (PSI `full`). node_exporter names PSI `some` as `..._waiting_seconds_total` and PSI `full` as `..._stalled_seconds_total`. The window 02:00–02:30 matches sar (Step H1) and the backup's start and end (Step H4).
- A 5-minute `rate` smooths short spikes. If the graph shows a plateau but users report 20-second freezes, query with `[1m]` and `step=60`.
- Each point is the value at that timestamp computed over the *previous* 5 minutes, so the curve lags the real start by up to one window.
- The same query on the other hosts answers "one host or all hosts?" in one go: drop the `instance` filter.

Questions to ask the graphs:

- **Does the latency spike line up with one resource's saturation?** That resource is the lead.
- **Does it repeat at the same time** every day or week? A schedule (Step H3).
- **Did it start with a deploy?** Add deploy annotations to dashboards so you can see it.
- **One host or all hosts?** All hosts at once points to a shared dependency (database, DNS, storage, the network) rather than each server.
- **What shape is it?** A slow ramp over days means a leak or growth; a step change means a deploy or configuration change; short spikes mean jobs, bursts or GC.

**Why this step (now):** graphs cover weeks and many hosts at once, so they
show patterns that per-host tools cannot. They are also the first place to
look **next** time, before anyone logs in.

**Next step:** pattern identified → wrap-up. No monitoring yet → set it up
(section 19; the L4 drill in your learning plan does exactly this) and use
Step H6 meanwhile.

### Step H6 — Catch it in the act next time

**Goal:** if history is missing or too coarse, record detailed evidence
automatically the next time pressure rises.

```bash
sudo tee /usr/local/sbin/slowcatch.sh > /dev/null <<'EOF'
#!/usr/bin/env bash
# Save evidence when CPU, memory or I/O pressure crosses a threshold.
set -u
OUTDIR=/var/tmp/slowcatch
THRESH=20                         # PSI "some avg10" percentage that triggers a capture
mkdir -p "$OUTDIR"
while true; do
  for r in cpu memory io; do
    v=$(awk '/^some/ {split($2, a, "="); print int(a[2])}' /proc/pressure/$r)
    if [ "$v" -ge "$THRESH" ]; then
      f="$OUTDIR/$(date +%Y%m%d-%H%M%S)-$r.txt"
      {
        date; uptime
        head -n 2 /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
        vmstat -w 1 5
        iostat -xyz 1 3
        mpstat -P ALL 1 2
        ps -eo pid,ppid,user,state,%cpu,%mem,rss,wchan:24,etime,args --sort=-%cpu | head -30
        ps -eo state,pid,wchan:32,args | awk '$1 ~ /^D/'
        ss -s
      } > "$f" 2>&1
      find "$OUTDIR" -name '*.txt' -mtime +7 -delete     # keep one week (only this directory)
      sleep 300                                          # at most one capture per 5 minutes
    fi
  done
  sleep 10
done
EOF
sudo chmod 755 /usr/local/sbin/slowcatch.sh

sudo tee /etc/systemd/system/slowcatch.service > /dev/null <<'EOF'
[Unit]
Description=Capture evidence when pressure is high
[Service]
ExecStart=/usr/local/sbin/slowcatch.sh
Restart=always
Nice=10
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now slowcatch.service
ls -l /var/tmp/slowcatch/
```

```
-rw-r--r-- 1 root root 48211 Oct  4 02:00 20261004-020013-io.txt
```

**What it means:** the next night, a capture appeared at 02:00:13, triggered
by I/O pressure. It holds the same evidence you would have collected live,
taken while the problem was happening.

**Why this step (now):** when the slowness is rare and short, waiting for it
with a terminal open does not work. A trigger on PSI captures exactly the
moments that matter and costs almost nothing in between.

**Next step:** read the capture like a section 2 snapshot, then follow the
branch it points to.

### Intermittent wrap-up: tree, fix, rollback, prevent

```
Slow only sometimes
├── sar (H1): which resource spiked, exactly when?
│   └── atop (H2): which process at that minute?
│       └── schedule (H3): cron / timer / backup / build / CronJob at that time?
│           ├── yes → reschedule, throttle, or move the job
│           └── no  → journal (H4) + graphs (H5): deploys, traffic, other hosts
└── no history → enable sysstat + atop now, run slowcatch (H6), wait for the next one
```

**Fix & verify** (the 02:00 backup):

```bash
# Run the backup throttled, at a quieter time, as a systemd timer instead of cron
sudo tee /etc/systemd/system/backup-volumes.service > /dev/null <<'EOF'
[Unit]
Description=Back up Docker volumes
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/backup-volumes.sh
Nice=10
IOReadBandwidthMax=/dev/sdb 25M
EOF
sudo tee /etc/systemd/system/backup-volumes.timer > /dev/null <<'EOF'
[Unit]
Description=Nightly volume backup
[Timer]
OnCalendar=*-*-* 03:30:00
RandomizedDelaySec=15min
Persistent=true
[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now backup-volumes.timer
sudo sed -i 's|^0 2 \* \* \* root /usr/local/sbin/backup-volumes.sh|# moved to backup-volumes.timer: &|' /etc/cron.d/backup
systemctl list-timers backup-volumes.timer --no-pager
# Verify the next morning: sar -d for 03:30-04:30 shows bounded throughput, latency stays low
```

**Rollback:** `sudo systemctl disable --now backup-volumes.timer`, uncomment
the original line in `/etc/cron.d/backup`, and `sudo systemctl daemon-reload`.

**Prevent it next time:**

- Install and enable `sysstat` (2-minute interval) and `atop` (60-second interval) on every server through your base Ansible role.
- Keep a schedule of every heavy job per host and spread them out; give each a bandwidth or CPU limit in its systemd unit.
- Add deploy and backup annotations to Grafana dashboards so correlations are visible at a glance.

---

## 9. Scenario: slow boot

> 📚 **Study path:** 1) Note: [Services & systemd](07-services-systemd.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD → SYSTEMD Tools ([lesson note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)), then LFCS — Manage Startup Process and Services ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: Sanjeev Thiyagarajan *Linux for Beginners: systemd start/stop services & journalctl* ([18 min](https://www.youtube.com/watch?v=jZfNVROoF74)) · 4) Read: [Arch Wiki: systemd](https://wiki.archlinux.org/title/Systemd) · 5) Practice: section 20, drill 8 (a netplan interface without a link, and a stale fstab entry, on a test VM).

**Level:** [L1 · Junior]. Reading `systemd-analyze` is a Junior skill; the
fix is usually a one-line change in netplan or fstab.

A server that takes minutes to come back after a reboot stretches every
maintenance window and every incident. systemd records exactly where boot
time went, so this scenario is mostly about reading its output.

### Step 1 — Total boot time and the slowest units

**Goal:** measure how long boot takes and which units took longest.

```bash
systemd-analyze
systemd-analyze blame | head -10
```

```
Startup finished in 3.912s (kernel) + 2min 8.441s (userspace) = 2min 12.353s
multi-user.target reached after 2min 8.402s in userspace

2min 552ms systemd-networkd-wait-online.service
     6.732s cloud-init.service
     3.512s docker.service
     2.371s systemd-udev-settle.service
     1.904s snapd.seeded.service
     1.201s apache2.service
```

**What it means:**

- The kernel needs 4 s; userspace (systemd starting services) needs 2 min 8 s. Physical servers also show `firmware` and `loader` times, where 30–90 s of firmware (RAID controller, NIC boot ROMs) is normal.
- `blame` lists how long each unit took to start. `systemd-networkd-wait-online.service` took 2 minutes, its default timeout: it waited for a network condition that never came.
- `blame` is not the critical path: units start in parallel, so a slow unit only delays boot if something waits for it.

**Why this step (now):** it splits kernel, firmware and userspace time in
one command and gives you a suspect list.

**Next step:** → Step 2 to see whether the slow unit is on the critical path.

### Step 2 — The critical chain

**Goal:** see which chain of units actually delayed the boot target.

```bash
systemd-analyze critical-chain
systemd-analyze critical-chain docker.service
systemd-analyze plot > /var/tmp/boot.svg        # timeline chart; open it in a browser
```

```
The time when unit became active or started is printed after the "@" character.
The time the unit took to start is printed after the "+" character.

multi-user.target @2min 8.402s
└─docker.service @2min 4.881s +3.512s
  └─network-online.target @2min 4.870s
    └─systemd-networkd-wait-online.service @4.318s +2min 552ms
      └─systemd-networkd.service @4.101s +201ms
        └─systemd-udevd.service @2.611s +1.488s
          └─systemd-tmpfiles-setup-dev.service @2.412s +190ms
```

**What it means:**

- `@` is when the unit became active; `+` is how long it took to start.
- `docker.service` waits for `network-online.target`, which waits for `systemd-networkd-wait-online.service`, which took 2 minutes. Docker (and therefore Dokploy and every container) starts 2 minutes late.

**Why this step (now):** fixing a slow unit that is not on the critical path
changes nothing. The chain shows which wait matters.

**Next step:** → Step 3 to read why that unit was slow.

### Step 3 — Why the slow unit waited

**Goal:** read the slow unit's own log for this boot.

```bash
journalctl -b -u systemd-networkd-wait-online.service --no-pager
networkctl
cat /etc/netplan/*.yaml
```

```
Oct 03 06:20:05 web01 systemd[1]: Starting Wait for Network to be Configured...
Oct 03 06:22:05 web01 systemd-networkd-wait-online[612]: Timeout occurred while waiting for network connectivity.
Oct 03 06:22:05 web01 systemd[1]: systemd-networkd-wait-online.service: Main process exited, code=exited, status=1/FAILURE
Oct 03 06:22:05 web01 systemd[1]: Failed to start Wait for Network to be Configured.

IDX LINK TYPE     OPERATIONAL SETUP
  1 lo   loopback carrier     unmanaged
  2 ens3 ether    routable    configured
  3 ens4 ether    no-carrier  configuring

3 links listed.
```

**What it means:**

- `ens3` is up and routable; `ens4` is defined in netplan but has no cable or no virtual link (`no-carrier`). wait-online waits for **every** managed interface by default, so it sits until its 2-minute timeout.
- Other classic slow-boot causes and their fixes:

| Symptom in the journal or on the console | Cause | Fix |
|---|---|---|
| wait-online timeout | an interface in netplan with no link | `optional: true` on that interface |
| "A start job is running for /dev/disk/by-uuid/..." (1 min 30 s) | an fstab entry for a disk that is gone | fix fstab; `nofail` for non-essential disks |
| NFS or CIFS mount waits at boot | the network share is unreachable | `_netdev,nofail`, or `x-systemd.automount` |
| `cloud-init` takes long on on-prem VMs | it searches for cloud metadata | `sudo touch /etc/cloud/cloud-init.disabled` on hosts that do not need it |
| fsck runs at boot | max mount count or an unclean shutdown | let it finish; check why it was unclean |
| long `firmware` time | RAID controller or NIC boot ROM | BIOS settings; disable PXE ROMs not in use |

**Why this step (now):** the unit's own log says *what* it waited for, which
is what you change.

**Next step:** → fix and verify below.

### Boot wrap-up: tree, fix, rollback, prevent

```
Slow boot
├── systemd-analyze: firmware/loader large? → BIOS, controller ROMs (hardware)
├── kernel large? → dmesg -T for timeouts (storage, drivers)
└── userspace large → blame → critical-chain → journalctl -b -u UNIT
    ├── wait-online → netplan optional: true
    ├── device job 1min30s → fstab (nofail / remove stale entry)
    ├── network mounts → _netdev,nofail or x-systemd.automount
    └── cloud-init on-prem → disable it
```

**Fix & verify** (mark the unused interface optional):

```bash
sudo cp /etc/netplan/50-cloud-init.yaml /root/50-cloud-init.yaml.bak
sudo nano /etc/netplan/50-cloud-init.yaml
#   network:
#     version: 2
#     ethernets:
#       ens3:
#         addresses: [192.0.2.10/24]
#         routes:
#           - to: default
#             via: 192.0.2.1
#         nameservers:
#           addresses: [192.0.2.53]
#       ens4:
#         dhcp4: false
#         optional: true
#   If cloud-init still manages networking, it can regenerate 50-cloud-init.yaml at the next boot:
#   put "network: {config: disabled}" in /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
sudo chmod 600 /etc/netplan/50-cloud-init.yaml      # netplan warns about world-readable files
sudo netplan generate && sudo netplan try           # auto-reverts after 120 s unless you confirm
# After the next planned reboot:
systemd-analyze
systemctl status systemd-networkd-wait-online.service --no-pager
```

**Rollback:** `sudo cp /root/50-cloud-init.yaml.bak /etc/netplan/50-cloud-init.yaml && sudo netplan apply`.
`netplan try` already reverts automatically if the change cuts your
connection and you cannot confirm.

> ⚠️ Do not reboot a production server just to test boot time. Make the fix,
> verify it with `netplan try` and `findmnt --verify` (for fstab), and measure
> boot time at the next planned maintenance reboot.

**Prevent it next time:** run `findmnt --verify` after every fstab edit, mark
non-essential interfaces and mounts optional when you add them, and record
`systemd-analyze` after every planned reboot so you notice when boot time
grows. More on units and boot in [Services & systemd](07-services-systemd.md).

---

## 10. Scenario: slow SSH login

> 📚 **Study path:** 1) Note: [SSH & remote access](09-ssh-remote-access.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking → Configure SSH Servers and Clients ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) KodeKloud: *Learning Linux Basics Course & Labs* — Networking → DNS ([lesson note](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)) · 4) Practice: section 20, drill 5 (dead resolver plus `UseDNS yes`, then time the login with `ssh -vvv`).

**Level:** [L1 · Junior]. Every Junior should be able to find the gap in an
`ssh -vvv` trace; the server-side fix is a one-line drop-in.

A login that takes 10–30 seconds is almost always waiting for a timeout: a
DNS lookup, a Kerberos/GSSAPI attempt, or something slow in the login session
(PAM, the message of the day, shell start-up files). The trick is to find
**where** in the login the gap is.

### Step 1 — Time the login and find the gap

**Goal:** see which phase of the SSH connection stalls.

```bash
time ssh -o BatchMode=yes deploy@192.0.2.10 true
# Verbose client output with a timestamp on every line (ts from the moreutils package)
ssh -vvv deploy@192.0.2.10 exit 2>&1 | ts -s '%.s'
# Without moreutils:
ssh -vvv deploy@192.0.2.10 exit 2>&1 | while IFS= read -r l; do printf '%s %s\n' "$(date +%T.%N | cut -c1-12)" "$l"; done
```

```
real    0m10.412s
user    0m0.031s
sys     0m0.012s

0.000012 OpenSSH_8.9p1 Ubuntu-3ubuntu0.10, OpenSSL 3.0.2 15 Mar 2022
0.003101 debug1: Reading configuration data /etc/ssh/ssh_config
0.142877 debug1: Authenticating to 192.0.2.10:22 as 'deploy'
0.211304 debug1: SSH2_MSG_SERVICE_ACCEPT received
0.215672 debug1: Authentications that can continue: publickey,gssapi-keyex,gssapi-with-mic,password
0.215701 debug1: Next authentication method: gssapi-with-mic
10.231904 debug1: Unspecified GSS failure.  Minor code may provide more information
10.236118 debug1: Next authentication method: publickey
10.301442 debug1: Server accepts key: /home/deploy/.ssh/id_ed25519 ED25519 SHA256:3fP0...
10.338120 Authenticated to 192.0.2.10 ([192.0.2.10]:22) using "publickey".
```

**What it means:**

- 10.4 s in total, nearly all of it waiting. The gap is between `Next authentication method: gssapi-with-mic` (0.21 s) and the GSS failure (10.23 s).
- The server offers GSSAPI (Kerberos) authentication, as RHEL's default `sshd_config` does, and the client tries it first (Debian and Ubuntu clients enable `GSSAPIAuthentication` in `/etc/ssh/ssh_config`). Without a working Kerberos setup, the attempt waits for DNS lookups of the host's canonical name to time out.
- Where the gap sits tells you the cause:

| Gap appears | Usual cause | Next |
|---|---|---|
| before `SSH2_MSG_SERVICE_ACCEPT` / the auth list | server does reverse DNS of your IP (`UseDNS yes`) | Step 2 |
| at `gssapi-with-mic` | GSSAPI/Kerberos attempt timing out | Step 3 |
| after `Authenticated to` | session set-up: PAM, motd, home directory, shell files | Step 4 |
| before `Authenticating to` | the client resolving the server name, or TCP connect | Step N1, [SSH reference](09-ssh-remote-access.md) |

**Why this step (now):** the timestamps turn "SSH is slow" into one specific
phase; each phase has a different, small fix.

**Next step:** follow the table.

### Step 2 — Server-side reverse DNS

**Goal:** check whether `sshd` looks up the client's IP address and waits on
DNS.

```bash
sudo sshd -T | grep -iE '^(usedns|gssapiauthentication)'      # effective server settings
time getent hosts 198.51.100.23                                 # reverse lookup of the client IP, on the server
```

```
usedns yes
gssapiauthentication yes
198.51.100.23   client23.office.example.com

real    0m10.008s
```

**What it means:** `UseDNS yes` makes `sshd` resolve every client IP, and
that lookup takes 10 s here (the first resolver is dead, Step N1). Modern
OpenSSH defaults to `UseDNS no`; older or hardened configs sometimes turn it
on.

**Why this step (now):** it is a one-line check of the most common
server-side cause, and it also catches a broken resolver that hurts the
whole box.

**Next step:** `usedns yes` and slow reverse lookups → set `UseDNS no`
(wrap-up) and fix DNS. Fast → Step 3 or Step 4.

### Step 3 — Client-side GSSAPI

**Goal:** confirm that skipping GSSAPI removes the delay.

```bash
time ssh -o GSSAPIAuthentication=no deploy@192.0.2.10 true
```

```
real    0m0.402s
```

**What it means:** without the GSSAPI attempt the login takes 0.4 s, so
GSSAPI was the whole delay. Fix it on the client for that host (or all
hosts), or disable it on the server if Kerberos is not used.

**Why this step (now):** a single-flag comparison proves the cause before you
change any configuration.

**Next step:** → wrap-up. No change → Step 4.

### Step 4 — Session set-up: PAM, motd, shell files

**Goal:** find delays that happen after authentication.

```bash
# Server journal: compare timestamps of "Accepted publickey" and "session opened"
sudo journalctl -u ssh --since "10 min ago" -o short-precise --no-pager | tail -8     # RHEL: -u sshd
# Ubuntu's dynamic message of the day: time all its scripts
time sudo run-parts --lsbsysinit /etc/update-motd.d > /dev/null
# Login without running the remote shell's start-up files, versus a full login shell
time ssh deploy@192.0.2.10 true
time ssh deploy@192.0.2.10 'bash -lic exit'
time id deploy                                  # slow = user lookups through LDAP/SSSD
```

```
Oct 03 11:51:20.104112 web01 sshd[52211]: Accepted publickey for deploy from 198.51.100.23 port 51544 ssh2: ED25519 SHA256:3fP0...
Oct 03 11:51:20.162004 web01 sshd[52211]: pam_unix(sshd:session): session opened for user deploy(uid=1001) by (uid=0)
Oct 03 11:51:20.231771 web01 systemd-logind[701]: New session 412 of user deploy.

real    0m8.912s
real    0m0.511s
real    0m6.204s
real    0m0.004s
```

**What it means:**

- Authentication and the PAM session are fast (60 ms apart).
- `run-parts` on `/etc/update-motd.d` takes 8.9 s: one of the dynamic motd scripts (commonly `50-landscape-sysinfo` or scripts that check for updates or reach the internet) is slow. pam_motd runs them on every interactive login.
- `bash -lic exit` takes 6.2 s: the user's shell start-up files (`.bashrc`, `.profile`) do something slow, such as initialising nvm or conda, or a git prompt in a huge repository.
- `id` is instant, so user lookups (LDAP, SSSD) are fine. A home directory on an unreachable NFS server would also stall here (section 11).

**Why this step (now):** after authentication, the delay is in your own
server's session set-up. Timing each piece separately shows which one to
disable or fix.

**Next step:** → wrap-up.

### SSH wrap-up: tree, fix, rollback, prevent

```
Slow SSH login → ssh -vvv with timestamps (Step 1): where is the gap?
├── before auth list → server reverse DNS (UseDNS) → Step 2
├── at gssapi-with-mic → GSSAPI → Step 3
├── after "Authenticated" → motd / PAM / shell files / NFS home → Step 4
└── before connect → client-side DNS or network → Step N1 / module 24
```

**Fix & verify:**

```bash
# Client side: skip GSSAPI for your servers (in ~/.ssh/config)
#   Host *.example.internal 192.0.2.*
#       GSSAPIAuthentication no
# Server side: no reverse DNS, no GSSAPI when Kerberos is not used
echo -e 'UseDNS no\nGSSAPIAuthentication no' | sudo tee /etc/ssh/sshd_config.d/50-fast-login.conf
sudo sshd -t && sudo systemctl reload ssh         # validate first! RHEL: systemctl reload sshd
# Slow motd script: disable just that one
sudo chmod -x /etc/update-motd.d/50-landscape-sysinfo
# Verify from a NEW terminal (keep the old session open)
time ssh deploy@192.0.2.10 true
```

> ⚠️ When changing `sshd` configuration, keep your current SSH session open
> and test the login from a second terminal. A typo can lock you out; `sshd -t`
> catches syntax errors but not every logical mistake.

**Rollback:** `sudo rm /etc/ssh/sshd_config.d/50-fast-login.conf && sudo sshd -t && sudo systemctl reload ssh`;
`sudo chmod +x /etc/update-motd.d/50-landscape-sysinfo`.

**Prevent it next time:** keep `UseDNS no` in your base SSH configuration,
keep resolvers monitored (a dead resolver shows up in SSH logins first), and
keep interactive shell start-up files light on servers.

---

## 11. Scenario: shell hangs and slow commands

> 📚 **Study path:** 1) Note: [Storage & disk](01-storage-disk.md) (mounts, fstab) and [Processes](05-processes.md) (process states) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux → NFS ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) Read: Julia Evans's free zine [Linux debugging tools](https://wizardzines.com/zines/debugging/) · 4) Practice: section 20, drill 9 (stop the NFS server under a `hard` mount on a test VM and recover without rebooting).

**Level:** [L1 · Junior] to recognise a D-state hang and test mounts safely;
[L2 · Mid] to decide on a lazy unmount and on mount options.

`df` never returns, `ls` freezes on one directory, tab completion hangs, the
prompt takes seconds to appear, `sudo` pauses before asking for the password.
The common thread: something the command touches is waiting, most often a
network filesystem or a name lookup.

### Step 1 — What is the stuck command waiting on?

**Goal:** from a second terminal, see the hung process's state and the
kernel or system call it is stuck in.

```bash
pgrep -a df                                       # find the PID of the hung command
ps -o pid,state,wchan:32,etime,cmd -p PID
sudo cat /proc/PID/stack
sudo strace -p PID                                # shows the syscall it is blocked in (Ctrl-C to detach)
```

```
  52310 df -h
    PID S WCHAN                             ELAPSED CMD
  52310 D rpc_wait_bit_killable               02:41 df -h
[<0>] rpc_wait_bit_killable+0x1e/0x90 [sunrpc]
[<0>] __rpc_execute+0x10b/0x3f0 [sunrpc]
[<0>] rpc_run_task+0x14f/0x1a0 [sunrpc]
[<0>] nfs4_call_sync_sequence+0x6b/0xa0 [nfsv4]
[<0>] _nfs4_proc_statfs+0xc5/0xf0 [nfsv4]
strace: Process 52310 attached
statfs("/mnt/share",
```

**What it means:**

- State `D` in `rpc_wait_bit_killable`, a stack full of `sunrpc` and `nfsv4` functions, and `strace` stuck inside `statfs("/mnt/share"`: `df` is waiting for the NFS server behind `/mnt/share` to answer.
- The same pattern hits `ls`, shell tab completion and anything that touches that path, plus logins whose home directory is on that share.

**Why this step (now):** you cannot fix a hang you have not located. Process
state, wait channel and the blocked syscall name the path and the subsystem
in seconds.

**Next step:** NFS or CIFS in the stack → Step 2. A local disk path → Step D3.
Not in D state, waiting in `connect`/`poll` to port 53 → Step N1. Shell
prompt itself slow → Step 3.

### Step 2 — Find the dead network mount

**Goal:** confirm which mount does not answer, without hanging your own
shell.

```bash
findmnt -t nfs,nfs4,cifs                          # network mounts and their options
timeout 5 stat -f /mnt/share > /dev/null && echo OK || echo "HUNG or failed"
df -h -x nfs -x nfs4 -x cifs                      # df that skips network filesystems
sudo dmesg -T | grep -iE 'nfs: server|cifs' | tail -5
nfsstat -m                                        # mount options per NFS mount
```

```
TARGET     SOURCE                 FSTYPE OPTIONS
/mnt/share 192.0.2.40:/export/app nfs4   rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,hard,proto=tcp,timeo=600,retrans=2,sec=sys
HUNG or failed
[Sat Oct  3 11:58:02 2026] nfs: server 192.0.2.40 not responding, still trying
```

**What it means:**

- The share from 192.0.2.40 is mounted `hard`: the client retries **forever** and every process that touches it waits in D state until the server comes back. That protects data (no silent write failures) but freezes everything that touches the path.
- The kernel says so: `nfs: server 192.0.2.40 not responding, still trying`.
- `timeout 5 stat -f` is the safe way to test a mount without hanging your shell.

**Why this step (now):** it confirms the server and the mount, so you can
take it to whoever owns the NFS server or the network in between.

**Next step:** fix the server or the network path (the real fix). If the
share is not needed right now, detach it (wrap-up).

### Step 3 — Slow shell start, slow sudo, huge directories

**Goal:** find delays in the shell itself, `sudo`, or directory listings.

```bash
time bash -i -c exit                                        # interactive shell start-up time
PS4='+ $EPOCHREALTIME ' bash -x -i -c exit 2>&1 | head -60   # trace start-up files with timestamps
time sudo true
sudo true 2>&1 | head -2                                    # look for "unable to resolve host"
time ls /srv/app/sessions | wc -l                           # sorting millions of entries is slow
time ls -f /srv/app/sessions | head                         # -f: no sorting, streams immediately
```

```
real    0m4.812s
+ 1791028201.412377 . /home/deploy/.nvm/nvm.sh
+ 1791028205.981004 nvm use default
real    0m5.031s
sudo: unable to resolve host web01: Name or service not known
2481233
real    0m38.120s
```

**What it means:**

- The shell start-up spends 4.5 s sourcing `nvm.sh` (the timestamps jump between the two lines). Lazy-load nvm or remove it on servers.
- `sudo` takes 5 s and complains that it cannot resolve the host's own name: it waits for DNS. Add the hostname to `/etc/hosts` (Step N1 fix).
- 2.5 million files in one directory: `ls` reads and sorts all of them (38 s). Use `ls -f` or `find DIR -maxdepth 1` to look, and clean the directory up (old PHP sessions, cache files).

**Why this step (now):** these delays are local to your session and easy to
fix, but they make the whole server "feel slow" to everyone who logs in.

**Next step:** → wrap-up.

### Shell hangs wrap-up: tree, fix, rollback, prevent

```
Command hangs / shell slow
├── state D, rpc/nfs in stack → dead NFS server (Steps 1–2)
├── state D, io/jbd2 in stack → local disk (Step D3)
├── waiting on port 53 / "unable to resolve host" → DNS (N1), /etc/hosts
├── shell start-up slow → bash -x with timestamps (Step 3)
└── ls slow in one directory → millions of entries → ls -f, clean up
```

**Fix & verify:**

```bash
# NFS server down and the mount not needed right now: force and lazily detach it
sudo umount -f -l /mnt/share
findmnt /mnt/share || echo "detached"
# Make future mounts fail more gracefully: mount on access, and do not block boot
#   192.0.2.40:/export/app  /mnt/share  nfs4  _netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30  0 0
sudo findmnt --verify
```

> ⚠️ `umount -l` (lazy) only detaches the mount point from the tree. Processes
> already stuck on files in it stay stuck until the server returns or they are
> stopped, and any unwritten data for that share is lost. Prefer fixing the
> server or the network; use the lazy unmount when the share is not needed and
> it is blocking everything else. The `soft` mount option makes hung calls
> return errors instead, which can corrupt data written by applications that
> do not handle those errors; keep `hard` for data you write.

**Rollback:** `sudo mount /mnt/share` once the server is back (with the fstab
entry in place).

**Prevent it next time:** monitor NFS servers and the client mounts
(`node_exporter` has NFS statistics), use `x-systemd.automount` and
`nofail` for shares that are not essential at boot, keep hostnames in
`/etc/hosts`, and clean up directories that collect millions of small files.

---

## 12. Scenario: container slow, host fast

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine – Security (namespaces, cgroups, resource limits), then Logging Driver ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: [Learn: Docker](30-learn-docker.md) and [Docker reference](14-docker-containers.md) · 3) Video: KodeKloud *How Docker Networking Actually Works* ([9 min](https://www.youtube.com/watch?v=W7X6u2BGVRY)) for the embedded DNS in Step 3 · 4) KodeKloud: PCA — Monitoring Containers ([lesson note](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Monitoring-Containers/page)) · 5) Practice: section 20, drill 4 (a 0.5-CPU container with 8 busy threads), with [netshoot](https://github.com/nicolaka/netshoot) for the DNS test.

**Level:** [L2 · Mid]. The Dokploy/Swarm specifics (service limits,
`dokploy-network`) are daily work for Mid-level engineers running your stack.

"The same code runs fast on the host (or on my laptop) and slow in the
container." Containers share the host kernel, so the difference almost always
comes from the container's **limits**, its **DNS**, its **storage layer** or
its **logging**. For Kubernetes specifics see the
[Containers & Kubernetes playbook](26-playbook-containers-k8s.md).

### Step 1 — Prove where the time goes

**Goal:** measure the same request directly at the container and through the
proxy, so you know whether the container or the path to it is slow.

```bash
# The container's IP on its network (Dokploy apps join dokploy-network)
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' CONTAINER
# From the host: straight to the container, then through Traefik
curl -o /dev/null -s -w 'direct ttfb=%{time_starttransfer}s\n' http://10.0.1.23:8000/health
curl -o /dev/null -s -w 'proxy  ttfb=%{time_starttransfer}s\n' https://api.example.com/health
docker stats --no-stream CONTAINER
```

```
10.0.1.23
direct ttfb=2.812s
proxy  ttfb=2.830s
CONTAINER ID   NAME                 CPU %     MEM USAGE / LIMIT   MEM %     NET I/O         BLOCK I/O     PIDS
3f1c2a9e5b7d   shop-api.1.x8k2...   149.87%   998MiB / 1GiB       97.46%    1.2GB / 3.4GB   8.1GB / 2GB   212
```

**What it means:**

- Direct and proxied requests are equally slow, so Traefik is not the problem; the container is.
- CPU at 150% sits exactly at a 1.5-CPU limit (Step C7), and memory sits at 97% of a 1 GiB limit: two limits pressing at once.
- With Swarm's routing mesh, the container IP is on an overlay network; when it is not reachable from the host, run the test from a debug container on the same network: `docker run --rm --network dokploy-network nicolaka/netshoot curl -s -o /dev/null -w '%{time_starttransfer}\n' http://10.0.1.23:8000/health`.

**Why this step (now):** it separates the proxy from the container and shows
at a glance which limits are pressing.

**Next step:** at the CPU limit → Step C7. At the memory limit → Step 2. Far
from both → Step 3 (DNS) and Step 4 (storage, logs).

### Step 2 — Memory limit pressure inside the container

**Goal:** check whether the container spends its time reclaiming memory
under its limit.

```bash
CID=$(docker inspect -f '{{.Id}}' CONTAINER)
CG=/sys/fs/cgroup/system.slice/docker-$CID.scope
cat $CG/memory.max $CG/memory.current
grep -E '^(max|oom_kill) ' $CG/memory.events
cat $CG/memory.pressure
grep -E '^(anon|file) ' $CG/memory.stat
```

```
1073741824
1046478848
max 18342
oom_kill 0
some avg10=34.12 avg60=28.80 avg300=12.40 total=88123401
full avg10=21.07 avg60=17.30 avg300=7.71 total=52003318
anon 978321408
file 61440000
```

**What it means:**

- The container uses 998 MiB of its 1 GiB limit. `max 18342` counts how often usage hit the limit and forced reclaim.
- Its own memory PSI shows 21% `full` stall: the container is slow because it constantly reclaims memory, even though the host has free RAM and nothing has been killed yet.
- `anon` (process memory) is 933 MiB, `file` (page cache) only 59 MiB: there is almost no cache left to drop, so it reclaims by evicting what it needs.

**Why this step (now):** host tools see a healthy host. Only the cgroup's
own files show the container starving inside its limit, before any OOM kill
makes it obvious.

**Next step:** raise the limit or reduce usage (wrap-up; section 4 for heap
sizing). Not memory → Step 3.

### Step 3 — DNS inside the container

**Goal:** check the container's resolver configuration and how long lookups
take from inside.

```bash
docker exec CONTAINER cat /etc/resolv.conf
docker run --rm --network container:CONTAINER nicolaka/netshoot \
  sh -c 'time dig +search api.example.com > /dev/null'
# Kubernetes: same idea from the pod
kubectl exec -n NAMESPACE POD -- cat /etc/resolv.conf
```

```
nameserver 127.0.0.11
options ndots:0

real    0m4.021s

search shop.svc.cluster.local svc.cluster.local cluster.local example.internal
nameserver 10.96.0.10
options ndots:5
```

**What it means:**

- In Docker, `127.0.0.11` is the embedded DNS server, which forwards to the host's upstream servers. A 4 s lookup means an upstream is slow or unreachable from Docker's point of view (the ops ladder's "containers have their own resolver" blind spot).
- In Kubernetes, `ndots:5` means any name with fewer than 5 dots is first tried with every search domain: `api.example.com` becomes four or five failed lookups before the real one. Many apps do this for every outbound call.

**Why this step (now):** the host resolves quickly through its own
configuration, while the container takes a different path. Name lookups
inside containers are a common hidden delay on every outbound request.

**Next step:** fix the upstream DNS for Docker (`"dns"` in
`/etc/docker/daemon.json`) or reduce `ndots` / use fully qualified names
ending with a dot in Kubernetes (wrap-up). DNS fast → Step 4.

### Step 4 — Storage layer, logging and thread counts

**Goal:** check the container's write path and its view of the CPU.

```bash
docker info --format '{{.Driver}}'                                 # overlay2 expected; vfs is very slow
docker inspect -f '{{json .Mounts}}' CONTAINER                     # which paths are volumes or bind mounts
docker inspect -f '{{.HostConfig.LogConfig}}' CONTAINER
sudo ls -lh /var/lib/docker/containers/$CID/$CID-json.log
docker exec CONTAINER nproc                                        # what the app thinks it has
docker exec CONTAINER sh -c 'ls /proc/1/task | wc -l'              # threads of the main process
```

```
overlay2
[]
{json-file map[]}
-rw-r----- 1 root root 14G Oct  3 12:04 /var/lib/docker/containers/3f1c.../3f1c...-json.log
4
212
```

**What it means:**

- No volumes (`[]`): everything the app writes (uploads, SQLite, caches) goes into the container's overlay2 layer. The first write to any file from the image copies the whole file up; heavy write paths belong on a volume.
- `json-file` logging without `max-size`: a 14 GB log file, still growing. Docker writes every stdout line to it, and a very chatty app can be slowed down by its own logging, besides filling the disk.
- `nproc` says 4 (the host's CPUs) while the quota is 1.5: the app sized its pools for 4 CPUs and runs 212 threads, which throttles constantly (Step C7).

**Why this step (now):** these are container-only causes that never appear
when the same code runs on the host, which is exactly the symptom.

**Next step:** → wrap-up.

### Container wrap-up: tree, fix, rollback, prevent

```
Container slow, host fast
├── direct vs via proxy (Step 1): proxy adds the time? → Traefik / module 25
├── CPU at limit, nr_throttled rising → C7 (raise limit, size threads)
├── memory.current ≈ memory.max, memory PSI high → Step 2 (raise limit, fix heap)
├── slow lookups inside (127.0.0.11 / ndots:5) → Step 3
└── overlay writes, huge json logs, threads sized to host CPUs → Step 4
```

**Fix & verify:**

```bash
# Limits for a Swarm service (Dokploy: set them in the app's resource settings and redeploy)
docker service update --limit-cpu 2 --limit-memory 1536m SERVICE
# Log rotation for all NEW containers (existing ones keep their old setting until recreated)
sudo cp /etc/docker/daemon.json /root/daemon.json.bak     # back up FIRST
sudoedit /etc/docker/daemon.json
#   { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" },
#     "dns": ["192.0.2.53", "192.0.2.54"] }
sudo dockerd --validate --config-file /etc/docker/daemon.json   # Docker 23+: catches JSON typos before the restart
# Restarting dockerd stops EVERY container. Only those with a restart policy (and Swarm/Dokploy
# tasks) come back, unless "live-restore" is enabled. Do it in a maintenance window.
sudo systemctl restart docker
# Kubernetes: lower ndots for one workload
#   spec.dnsConfig.options: [{name: ndots, value: "2"}]
# Verify
docker stats --no-stream CONTAINER
curl -o /dev/null -s -w 'ttfb=%{time_starttransfer}s\n' https://api.example.com/health
```

**Rollback:** `docker service rollback SERVICE` (previous spec), or restore
`/root/daemon.json.bak` to `/etc/docker/daemon.json` and restart Docker in a
maintenance window.

**Prevent it next time:** every service gets explicit CPU and memory
settings and an app configuration sized to them (threads, heap, workers);
log rotation in `daemon.json` from day one (your L3 Ansible drill); volumes
for every write-heavy path; DNS servers set explicitly for Docker.

---

## 13. Scenario: slow VM on a busy hypervisor

> 📚 **Study path:** 1) Note: [AWS & cloud](16-aws-cloud.md) and [Learn: Cloud & AWS](36-learn-cloud-aws.md) for burstable instances and EBS · 2) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — Monitoring, Logging and Remediation, then Cost and Performance ([course](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 3) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)), the virtualisation part · 4) Practice: on a Proxmox/KVM homelab host, give two VMs more vCPUs than the host has cores, load both with `stress-ng`, and watch `%steal` in each guest (section 20, drill 10).

**Level:** [L3 · Senior]. Collecting the guest-side evidence is Mid-level
work; negotiating reservations, vCPU sizing and instance families with the
virtualisation or cloud owners is a Senior conversation.

A VM that is slow while its own numbers look modest often suffers from what
it cannot see: other VMs on the same host competing for CPU, memory and
storage. From inside the guest, you look for the fingerprints; the proof and
the fix usually sit with whoever runs the hypervisor.

### Step 1 — Steal and stalls from inside the guest

**Goal:** measure how much CPU the hypervisor withholds, and spot signs of
the VM being paused.

```bash
mpstat 1 5                   # %steal
vmstat 1 5                   # st
sudo dmesg -T | grep -iE 'soft lockup|rcu.*stall|clocksource' | tail -5
chronyc tracking | grep -E 'System time|Last offset'
```

```
11:20:02     all   21.30    0.00    4.10    0.80    0.00    0.30   27.40    0.00    0.00   46.10
[Sat Oct  3 11:18:40 2026] watchdog: BUG: soft lockup - CPU#1 stuck for 23s! [kworker/1:2:3312]
System time     : 0.000412881 seconds fast of NTP time
Last offset     : -0.812004112 seconds
```

**What it means:**

- `%steal` 27: more than a quarter of the time, the vCPUs were ready but not scheduled by the hypervisor.
- A "soft lockup" of 23 s in a VM usually means the whole VM was not scheduled (or was paused) for that long, not that the guest kernel hung.
- A sudden clock correction of 0.8 s is another sign of the VM being paused or starved.

**Why this step (now):** steal is the one hypervisor problem the guest can
measure directly, and it rules out tuning inside the VM as a fix.

**Next step:** → Step 2 (memory ballooning) and Step 3 (storage), then take
the evidence to the virtualisation team. On AWS → Step C8.

### Step 2 — Memory ballooning

**Goal:** check whether the hypervisor is reclaiming the VM's memory.

```bash
lsmod | grep -E 'virtio_balloon|vmw_balloon'
grep -E '^balloon_(inflate|deflate) ' /proc/vmstat
vmware-toolbox-cmd stat balloon            # VMware guests with open-vm-tools
free -m
```

```
virtio_balloon         28672  0
balloon_inflate 524288
balloon_deflate 0
               total        used        free      shared  buff/cache   available
Mem:            5893        3165         310          41        2418        1102
```

**What it means:**

- The balloon driver has inflated by 524,288 pages (2 GB; the counters are cumulative, so subtract `balloon_deflate`): the hypervisor took 2 GB of this VM's 8 GB back for other VMs. With `virtio_balloon`, inflated pages are removed from `MemTotal`, so `free` shows about 5.9 GB total on a VM configured with 8 GB (unless the host enabled the deflate-on-OOM option, in which case the total stays and the balloon counts as used). Either way the real workload is short of memory and pushed into reclaim (section 4).
- On VMware, the balloon is counted as used memory inside an unchanged total, and `vmware-toolbox-cmd stat balloon` prints its size directly.

**Why this step (now):** ballooning makes a VM short of memory without any
change inside it, which is otherwise baffling.

**Next step:** → Step 3, then the virtualisation team (memory reservation for
the VM, or fewer VMs on the host).

### Step 3 — Noisy neighbours on shared storage

**Goal:** recognise storage latency caused by other VMs on the same
datastore or SAN.

```bash
iostat -xyz 1 5
```

```
Device            r/s     rkB/s r_await rareq-sz     w/s     wkB/s w_await wareq-sz  aqu-sz  %util
sda             38.00    608.00   46.21    16.00   21.00    336.00   88.40    16.00    3.61  31.20
```

**What it means:** only 59 IOPS, a shallow queue and `%util` 31%, yet 46–88
ms per request. This VM is not pushing its disk hard; the latency comes from
the shared storage underneath, busy with someone else's work (or from a QoS
limit, Step D6).

**Why this step (now):** high latency at low load is the guest-side
fingerprint of contention you cannot see, and it is the evidence the storage
team needs.

**Next step:** → wrap-up with the evidence from Steps 1–3.

### Hypervisor wrap-up: tree, fix, rollback, prevent

```
VM slow, guest metrics modest
├── %steal > 5–10 → CPU contention on the host (or AWS credits → C8)
├── balloon inflated → host memory overcommit
├── high await at low IOPS → shared storage contention or QoS cap
└── soft lockups / clock jumps → VM paused or starved
```

**Fix & verify:** the fix happens on the hypervisor side. Bring the numbers
(steal %, balloon size, await at low IOPS, timestamps) to the virtualisation
team and ask for:

- **CPU:** the host's CPU ready time for this VM (VMware `esxtop` `%RDY`; above about 5–10% per vCPU is bad) and co-stop (`%CSTP`, caused by too many vCPUs). Often the fix is **fewer** vCPUs, a CPU reservation, or moving the VM (vMotion, live migration) to a quieter host.
- **Memory:** a memory reservation for the VM so it cannot be ballooned, or less overcommit on the host.
- **Storage:** datastore latency for this VM, and moving it or its disks to less busy storage.
- On Proxmox/KVM you can check the host yourself: `virsh domstats --vcpu VM`, `virsh dommemstat VM`, and PSI on the host.

Verify with the same guest-side commands afterwards: `%steal` near 0, the
balloon deflated, `await` back to normal.

**Rollback:** not applicable inside the guest; hypervisor changes follow the
virtualisation team's change process.

**Prevent it next time:** graph steal time for every VM (node_exporter's
`mode="steal"`), alert above 5–10%, and agree on reservations for production
VMs that must not be squeezed.

---

## 14. Scenario: high load, idle CPU

> 📚 **Study path:** 1) Note: [Processes](05-processes.md) (process states) and [CPU & performance](03-cpu-performance.md) (load average) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes ([lesson note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) · 3) Read: [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html) (load averages) · 4) Practice: section 20, drill 9 (hung NFS mount), the Ops Ladder case "High load average while the CPU is mostly idle", then a timed scenario on [SadServers](https://sadservers.com/scenarios).

**Level:** [L2 · Mid]. Juniors should know that Linux load includes D-state
tasks; grouping them by wait channel is the Mid-level move.

`uptime` says load 25 on a 4-core box, `top` says the CPUs are 90% idle. Both
are right: Linux load counts tasks in uninterruptible sleep (state D), and
those tasks use no CPU. High load with idle CPU means **many tasks are stuck
waiting**, almost always on storage or NFS.

### Step 1 — Confirm the mismatch

**Goal:** prove that load comes from blocked tasks, not runnable ones.

```bash
uptime; nproc
vmstat 1 5
```

```
 12:10:44 up 41 days,  2:01,  3 users,  load average: 24.81, 22.10, 15.33
4
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1 23      0 3211420 98112 3011204    0    0     0     4  412  610  2  1 89  8  0
 0 24      0 3211380 98112 3011208    0    0     0     0  398  588  1  1 91  7  0
```

**What it means:** `r` is 0–1 (nothing is waiting for a CPU) and `b` is
23–24: the load of about 24 is made of blocked tasks. CPUs are 90% idle and
almost no I/O completes (`bi`/`bo` near 0): tasks wait on something that is
not answering.

**Why this step (now):** it rules out CPU in one look and tells you to hunt
for blocked tasks, not busy ones.

**Next step:** → Step 2.

### Step 2 — Group the blocked tasks by what they wait on

**Goal:** see which kernel wait channel holds most of the blocked tasks.

```bash
ps -eo state,wchan:32 | awk '$1 ~ /^D/ {print $2}' | sort | uniq -c | sort -rn
ps -eo state,pid,etime,wchan:32,cmd | awk '$1 ~ /^D/' | head
```

```
     21 rpc_wait_bit_killable
      2 nfs_wait_bit_killable
      1 io_schedule
D   61221    12:02 rpc_wait_bit_killable            ls /mnt/share/reports
D   61244    11:40 rpc_wait_bit_killable            /usr/sbin/apache2 -k start
D   61307    09:12 nfs_wait_bit_killable            php /srv/app/cron/export.php
```

**What it means:**

- 23 of 24 blocked tasks wait in NFS client code: the NFS server (or the path to it) is not answering. Apache workers that serve files from the share are stuck too, so the site slows down as workers run out.
- `io_schedule` alone would point to a local disk (Step D3); `jbd2_*` to the filesystem journal; `blk_mq_get_tag` to a full device queue.

**Why this step (now):** grouping by wait channel names the subsystem
responsible for the whole load figure, even when hundreds of tasks are
stuck.

**Next step:** NFS → section 11, Step 2. Local disk → section 5, Step D1.

### Step 3 — Process storms and kernel threads

**Goal:** cover the two less common causes: bursts of short-lived processes,
and kernel threads in D state.

```bash
sar -w 1 5                                    # proc/s = new processes per second
sudo execsnoop-bpfcc -T | head -20            # every exec as it happens (bpfcc-tools)
ps -eo state,pid,cmd | awk '$1 ~ /^D/ && $3 ~ /^\[/'     # kernel threads in D state
```

```
12:20:01       proc/s   cswch/s
12:20:02       812.00  21233.00
TIME     PCOMM            PID     PPID    RET ARGS
12:20:02 sh               71201   2795      0 /bin/sh -c curl -fs http://127.0.0.1:8000/health || exit 1
12:20:02 curl             71202   71201     0 /usr/bin/curl -fs http://127.0.0.1:8000/health
```

**What it means:** 812 new processes per second: something forks constantly
(here Docker health checks running `sh` and `curl` very frequently; their
parent is the container's `containerd-shim`, PID 2795). Each
process is too short-lived for `top` to show, but together they create load
and CPU spikes. Lengthen the health-check interval or use a cheaper check.

**Why this step (now):** it catches the cases where neither Step 2 nor
`top` explains the load.

**Next step:** → wrap-up.

### High-load wrap-up: tree, fix, rollback, prevent

```
Load high, CPU idle
├── vmstat b high, r low (Step 1)
│   └── group D tasks by wchan (Step 2)
│       ├── rpc_* / nfs_* → NFS server or path → section 11
│       ├── io_schedule / wait_on_page_* / folio_* / blk_mq_* → local disk → section 5
│       └── jbd2_* → journal / fsync → D5
└── r spikes, proc/s high → process storm → execsnoop (Step 3)
```

**Fix & verify:** fix the thing the tasks wait for (the NFS server, the
disk, the noisy health check). Load falls on its own as the blocked tasks
complete; check with `uptime` and `vmstat` (`b` back to 0).

> ⚠️ Rebooting a box with tasks stuck on a hard NFS mount often hangs at
> shutdown too, and it destroys the evidence. Fix or detach the mount first
> (section 11). Reboot only as a last resort, through the normal procedure
> (`sudo systemctl reboot`), with the console (iDRAC, iLO, hypervisor) at hand.

**Rollback:** depends on the fix; health-check interval changes roll back by
redeploying the previous service definition.

**Prevent it next time:** alert on blocked tasks (`node_procs_blocked`) and
on PSI io, not only on load average, so the alert already says "waiting on
I/O" instead of "CPU high".

---

## 15. Scenario: high softirq and interrupts

> 📚 **Study path:** 1) Note: [Learn: performance & observability](32-learn-performance-observability.md), section 7 (network deep dive), and [Network](02-network.md) · 2) KodeKloud: no dedicated course on interrupts or NIC queues (check the current catalog); LFCS — Change Kernel Runtime Parameters covers the `sysctl` basics ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: Brendan Gregg *Linux Performance Tools, part 1 of 2* ([54 min](https://www.youtube.com/watch?v=FJW8nGV4jxY)) · 4) Practice: section 20, drill 11 (a small-packet flood into a one-queue VM, then spread it with RPS).

**Level:** [L3 · Senior]. It mostly appears on busy proxies and load
balancers (Traefik, Apache, HAProxy) that Senior engineers size and tune.

On a busy network server, all of a NIC's interrupts and their softirq work
(the kernel's network processing) can land on one CPU. That CPU hits 100% in
`%soft` while the others idle, packets get dropped, and latency climbs, even
though "CPU usage" looks low on average.

### Step 1 — Spot the overloaded CPU

**Goal:** find a CPU that is busy with interrupt and softirq work.

```bash
mpstat -P ALL 1 3
top                              # press 1; look for ksoftirqd/N near the top
```

```
12:30:02     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
12:30:03     all    9.80    0.00    6.10    0.00    0.25   25.75    0.00    0.00    0.00   58.10
12:30:03       0    3.00    0.00    1.00    0.00    1.00   95.00    0.00    0.00    0.00    0.00
12:30:03       1   12.00    0.00    8.00    0.00    0.00    3.00    0.00    0.00    0.00   77.00
12:30:03       2   13.00    0.00    8.00    0.00    0.00    2.00    0.00    0.00    0.00   77.00
12:30:03       3   11.00    0.00    7.00    0.00    0.00    3.00    0.00    0.00    0.00   79.00
```

**What it means:** CPU 0 spends 95% of its time in softirq and is never idle;
the other CPUs are mostly idle. The average (26% soft) hides it. `ksoftirqd/0`
high in `top` means the kernel could not keep up inline and deferred the work
to that thread.

**Why this step (now):** it is the only view that shows this problem; every
average says the box has spare CPU.

**Next step:** → Step 2 to see which interrupts and softirqs.

### Step 2 — Which interrupts, and on which CPUs

**Goal:** map interrupt sources to CPUs and check for dropped packets.

```bash
grep -E 'CPU|virtio|ens|eth|mlx|ixgbe|i40e' /proc/interrupts
watch -d -n1 "grep -E 'NET_RX|NET_TX' /proc/softirqs"
# softnet_stat: per CPU, column 2 = dropped, column 3 = time_squeeze (both hex)
while read a b c rest; do echo "processed=$((16#$a)) dropped=$((16#$b)) squeezed=$((16#$c))"; done < /proc/net/softnet_stat
ip -s link show ens3 | sed -n '3,6p'
```

```
            CPU0       CPU1       CPU2       CPU3
 24:   91823411          0          0          0   PCI-MSI 49153-edge      virtio0-input.0
 25:   80211344          0          0          0   PCI-MSI 49154-edge      virtio0-output.0
processed=1823412311 dropped=48120 squeezed=912334
processed=1203 dropped=0 squeezed=0
processed=1187 dropped=0 squeezed=0
processed=1301 dropped=0 squeezed=0
    RX:  bytes   packets errors dropped  missed   mcast
    912345678901 1203448812      0   48120       0       0
```

**What it means:**

- The NIC has one receive queue (`virtio0-input.0`) and all its interrupts go to CPU 0.
- CPU 0 processed almost all packets, dropped 48,120 (backlog full) and was "squeezed" (ran out of its time budget with work left) 912,334 times. The other CPUs did almost nothing.
- The drops show up as `dropped` on the interface too. Each drop costs the sender a retransmit (Step N3).

**Why this step (now):** it confirms that the network path, not an
application, is consuming CPU 0, and the drop counters prove user impact.

**Next step:** → Step 3.

### Step 3 — Queues, irqbalance and packet steering

**Goal:** check whether the work can be spread over more CPUs.

```bash
ethtool -l ens3                                   # NIC channels (queues): maximum and current
systemctl is-active irqbalance
cat /proc/irq/24/smp_affinity_list                # which CPUs IRQ 24 may run on
cat /sys/class/net/ens3/queues/rx-0/rps_cpus      # software steering mask (0 = off)
ethtool -k ens3 | grep -E 'generic-receive-offload|large-receive-offload'
```

```
Channel parameters for ens3:
Pre-set maximums:
RX:		n/a
TX:		n/a
Other:		n/a
Combined:	4
Current hardware settings:
RX:		n/a
TX:		n/a
Other:		n/a
Combined:	1
inactive
0
00000000
generic-receive-offload: on
large-receive-offload: off [fixed]
```

**What it means:**

- The NIC supports 4 combined queues but uses 1. With 4 queues, each queue gets its own interrupt that can run on a different CPU.
- `irqbalance` is not running, so nothing spreads interrupts. Ubuntu server installs it by default; it was disabled here.
- RPS (receive packet steering, software spreading) is off (`00000000`).
- GRO is on (good: it merges packets and reduces per-packet work).

**Why this step (now):** these three settings decide whether network work can
use more than one CPU, and they are cheap to change and to revert.

**Next step:** → wrap-up.

### Softirq wrap-up: tree, fix, rollback, prevent

```
One CPU pinned in %soft / %irq
├── /proc/interrupts: one queue, one CPU? → more queues (ethtool -L)
├── irqbalance inactive? → enable it
├── single-queue NIC? → RPS to spread in software
└── packet rate itself abnormal? → flood / DDoS → module 24, upstream filtering
```

**Fix & verify:**

```bash
ethtool -l ens3 | tail -4 > /root/ens3-channels.before         # record the current setting
sudo ethtool -L ens3 combined 4             # more queues (may reset the link briefly: plan it)
sudo systemctl enable --now irqbalance
echo f | sudo tee /sys/class/net/ens3/queues/rx-0/rps_cpus      # RPS over CPUs 0-3 (bitmask f)
# Verify
mpstat -P ALL 1 3
grep -E 'CPU|virtio0-input' /proc/interrupts
while read a b c rest; do echo "dropped=$((16#$b))"; done < /proc/net/softnet_stat
```

> ⚠️ Changing NIC channels can reset the link for a moment. Do it from a
> console or in a maintenance window, not over an SSH session through that
> NIC on a production box without a fallback.

**Rollback:** `sudo ethtool -L ens3 combined 1`, `echo 0 | sudo tee /sys/class/net/ens3/queues/rx-0/rps_cpus`,
and `sudo systemctl disable --now irqbalance` if it was intentionally off.
`ethtool -L` and RPS settings do not survive a reboot unless persisted (a
systemd unit or a udev rule), so a reboot also rolls them back.

**Prevent it next time:** keep `irqbalance` enabled on multi-core servers,
size NIC queues to the CPU count on busy proxies (Traefik, Apache, HAProxy),
and alert on per-CPU softirq time and on `node_softnet_dropped_total`.

---

## 16. Windows: quick playbook

> 📚 **Study path:** 1) Note: [Windows reference](17-windows.md), section 2 (processes, CPU & memory) and section 5 (events & logs) · 2) KodeKloud: no verified Windows Server performance course (check the current catalog) · 3) Practice: on a Windows Server evaluation VM, start a CPU hog and find it with `Get-Counter` and `Get-Process` before you open Task Manager (section 20, drill 12).

**Level:** [L1 · Junior]. You will meet Windows less often than Linux; the
goal is to run the same method (define, USE, name the process, prove it) with
different tools, not to become a Windows performance specialist.

The method from sections 1 and 2 does not change. Only the tools do:

| Linux (section 2) | Windows equivalent | Read it as |
|---|---|---|
| `uptime`, `vmstat` r | `\System\Processor Queue Length` | above about 2 per logical CPU, sustained = CPU saturation |
| `mpstat -P ALL` | Task Manager → Performance → CPU → "Logical processors"; `\Processor(*)\% Processor Time` | one core pinned = single thread |
| `vmstat` si/so, `free` | `\Memory\Available MBytes`, `\Memory\Pages/sec`, `\Memory\% Committed Bytes In Use` | low available **and** high pages/sec = paging |
| `iostat -x` await, aqu-sz | `\PhysicalDisk(*)\Avg. Disk sec/Read` and `sec/Write`, `Current Disk Queue Length` | above about 10 ms on SSD, 20 ms on HDD |
| `sar -n DEV` | `\Network Interface(*)\Bytes Total/sec`, Resource Monitor → Network | against link speed |
| `pidstat`, `top`, `iotop` | `Get-Process`, `\Process(*)\...` counters, Resource Monitor | the hot process |
| `dmesg`, `journalctl -k` | Event Viewer → System, `Get-WinEvent` | IDs 2004, 153, 129, 7 |
| `sar` / `atop` history | Performance Monitor data collector (`logman`) | needs to be set up before the incident |

The sample host is `win-app01`, a 4-vCPU, 8 GB Windows Server VM running IIS
and SQL Server, and it tells the same story as `web01` in section 2.

### Step W1 — Key counters with Get-Counter

**Goal:** one pass over CPU, memory, disk and network, like the 60-second
checklist, in numbers you can paste into a ticket.

```powershell
# Elevated PowerShell. 5 samples 1 s apart; print the last one.
$counters = @(
  '\Processor(_Total)\% Processor Time'
  '\Processor(_Total)\% Privileged Time'
  '\System\Processor Queue Length'
  '\Memory\Available MBytes'
  '\Memory\Pages/sec'
  '\Memory\% Committed Bytes In Use'
  '\PhysicalDisk(_Total)\Avg. Disk sec/Read'
  '\PhysicalDisk(_Total)\Avg. Disk sec/Write'
  '\PhysicalDisk(_Total)\Current Disk Queue Length'
  '\Network Interface(*)\Bytes Total/sec'
)
Get-Counter -Counter $counters -SampleInterval 1 -MaxSamples 5 |
  Select-Object -Last 1 -ExpandProperty CounterSamples |
  Select-Object Path, @{n='Value'; e={[math]::Round($_.CookedValue, 3)}} |
  Format-Table -AutoSize
(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
```

```
Path                                                                    Value
----                                                                    -----
\\win-app01\processor(_total)\% processor time                         34.812
\\win-app01\processor(_total)\% privileged time                        21.406
\\win-app01\system\processor queue length                                   1
\\win-app01\memory\available mbytes                                       388
\\win-app01\memory\pages/sec                                         2411.902
\\win-app01\memory\% committed bytes in use                             93.71
\\win-app01\physicaldisk(_total)\avg. disk sec/read                     0.046
\\win-app01\physicaldisk(_total)\avg. disk sec/write                    0.091
\\win-app01\physicaldisk(_total)\current disk queue length                 17
\\win-app01\network interface(vmxnet3 ethernet adapter)\bytes total/sec 812331.4
4
```

**What it means:**

- CPU 35% with a queue length of 1 on 4 logical CPUs: not CPU-bound. `% Privileged Time` 21 (kernel time) is a large share of the total: the kernel is busy with paging and disk I/O.
- `Available MBytes` 388 on an 8 GB VM (under 5%) with `Pages/sec` around 2,400: Windows is reading and writing the page file. `Pages/sec` alone can be high from memory-mapped files; it matters when `Available MBytes` is also low.
- `% Committed Bytes In Use` 94%: the commit charge is close to the commit limit (RAM plus page file). At 100%, allocations fail and applications report "out of memory".
- Disk reads take 46 ms and writes 91 ms with 17 requests queued: on an SSD-backed VM, a few ms is normal. The disk is saturated, by paging.
- Network about 0.8 MB/s: idle.
- Rough thresholds: queue length above 2 per logical CPU sustained; `Available MBytes` below 10% of RAM; disk sec/Read or sec/Write above 0.010 (SSD) or 0.020 (HDD); `Current Disk Queue Length` persistently above about 2 per physical disk.

**Why this step (now):** it is the Windows version of the 60-second
checklist: every resource once, as numbers, from one command that also works
over PowerShell remoting on Server Core, where there is no Task Manager to
click through.

**Next step:** memory low and paging (our story) → Step W2, sorted by memory.
CPU or queue high → Step W2, sorted by CPU. Disk latency high without paging
→ Step W3. Nothing saturated → Step W4, then think like section 7 (the
application is waiting on a database, DNS or a lock).

### Step W2 — Who uses it: Get-Process and per-process CPU

**Goal:** name the process (and the service inside it) that holds the memory
or burns the CPU.

```powershell
# Top memory users. WS = working set (in RAM now), PM = private bytes (committed)
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 6 Id, ProcessName,
  @{n='WS(MB)'; e={[int]($_.WorkingSet64/1MB)}}, @{n='PM(MB)'; e={[int]($_.PagedMemorySize64/1MB)}},
  @{n='CPU(s)'; e={[int]$_.CPU}}, Handles | Format-Table -AutoSize

# CURRENT CPU per process. Get-Process's CPU column is total seconds since start, not a percentage.
$n = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
(Get-Counter '\Process(*)\% Processor Time' -SampleInterval 2).CounterSamples |
  Where-Object InstanceName -notin '_total','idle' | Sort-Object CookedValue -Descending |
  Select-Object -First 5 InstanceName, @{n='CPU%'; e={[math]::Round($_.CookedValue / $n, 1)}}

# Which service lives inside a shared svchost process, and how was it started?
tasklist /svc /fi "PID eq 3120"
Get-CimInstance Win32_Process -Filter "ProcessId=3120" | Select-Object ProcessId, ParentProcessId, CommandLine
```

```
   Id ProcessName WS(MB) PM(MB) CPU(s) Handles
   -- ----------- ------ ------ ------ -------
 2140 sqlservr      5212   5398  81231    1890
 4416 w3wp           812    944  12044    2310
 3120 svchost        402    388   4120    1204
 2988 MsMpEng        311    402  22013     998
 5521 java           288    512   1880     611
 1104 dwm             61     41    112     412

InstanceName  CPU%
------------  ----
msmpeng       11.8
sqlservr       9.6
w3wp           6.2
system         4.1
svchost#4      2.0

Image Name                     PID Services
========================= ======== ============================================
svchost.exe                   3120 wuauserv

ProcessId ParentProcessId CommandLine
--------- --------------- -----------
     3120             812 C:\Windows\system32\svchost.exe -k netsvcs -p -s wuauserv
```

**What it means:**

- `sqlservr` holds 5.2 GB of an 8 GB VM. SQL Server's default "max server memory" is effectively unlimited: its buffer pool grows until Windows signals low memory, and IIS (`w3wp`) and the OS are left to page. It is the same root cause as the JVM on `web01`: a cache sized for the whole machine on a shared box.
- `WS` is RAM in use now. `PM` (private bytes) is memory the process has committed, which counts against the commit limit even when it is paged out. A `PM` that only ever grows over hours is the Windows leak signature; watch `\Process(NAME)\Private Bytes` in Performance Monitor.
- `MsMpEng` is the Microsoft Defender engine. 12% of all CPUs during a scan or a signature update is normal; constant scanning of hot directories on a build or file server is not.
- The `\Process(*)\% Processor Time` counter is per core (a process can reach 400% on 4 cores), hence the division by the CPU count.
- `svchost` processes host services. `tasklist /svc` names them: PID 3120 is Windows Update (`wuauserv`), a common midday surprise when update installs are not scheduled.

**Why this step (now):** W1 named the resource; this names the owner. On
Windows the owner is often a service hidden inside `svchost`, or a product
default that lets one program take the whole machine.

**Next step:** a product's memory default (SQL Server, Exchange, a JVM) →
"Windows wrap-up" fix. A service inside `svchost` → check its schedule
(Windows Update, Defender scans) and move it. Disk latency still unexplained →
Step W3.

### Step W3 — Disk per process with Resource Monitor

**Goal:** find which process and which file cause the disk traffic, and
which disk is slow.

```powershell
resmon.exe     # GUI. Disk tab: "Processes with Disk Activity" sorted by Total (B/sec);
               # "Disk Activity" shows file names; "Storage" shows queue length per disk.

# Command-line view: I/O bytes per process (all I/O: file, network and device)
(Get-Counter '\Process(*)\IO Data Bytes/sec' -SampleInterval 2).CounterSamples |
  Where-Object InstanceName -notin '_total','idle' | Sort-Object CookedValue -Descending |
  Select-Object -First 5 InstanceName, @{n='MB/s'; e={[math]::Round($_.CookedValue/1MB, 1)}}

# Latency and IOPS per physical disk
(Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Transfer','\PhysicalDisk(*)\Disk Transfers/sec' -SampleInterval 2).CounterSamples |
  Select-Object InstanceName, @{n='Counter'; e={($_.Path -split '\\')[-1]}}, @{n='Value'; e={[math]::Round($_.CookedValue, 3)}}
```

```
InstanceName MB/s
------------ ----
sqlservr     38.2
system       21.7
msmpeng       6.4
w3wp          1.1
svchost#4     0.9

InstanceName Counter                Value
------------ -------                -----
0 c:         avg. disk sec/transfer 0.072
1 d:         avg. disk sec/transfer 0.011
_total       avg. disk sec/transfer 0.064
0 c:         disk transfers/sec     612.4
1 d:         disk transfers/sec      88.0
_total       disk transfers/sec     700.4
```

**What it means:**

- `sqlservr` moves 38 MB/s. `System` (PID 4) moves 22 MB/s: kernel work such as paging I/O and cache write-back is charged to it.
- Disk 0 (C:, where `pagefile.sys` lives) answers in 72 ms at 612 IOPS, while disk 1 (D:, the SQL data disk) is fine at 11 ms. The page file is the hot spot, which confirms the memory story from W1 and W2.
- In Resource Monitor's Disk tab, `C:\pagefile.sys` near the top of "Disk Activity" shows the same thing visually.
- `IO Data Bytes/sec` counts every kind of I/O, including network. When you need disk-only numbers and file names, use Resource Monitor.

**Why this step (now):** Windows hides the "who" of disk I/O deeper than
Linux's `iotop`. Resource Monitor and per-process counters answer it without
installing anything, and they separate "paging" from "an application or a
backup reading the disk".

**Next step:** page-file I/O → the memory fix ("Windows wrap-up"). A backup,
antivirus scan or application → reschedule or throttle it. High latency at
low IOPS → storage contention or a cap: Step D6 and section 13 apply to
Windows VMs too. Then Step W4.

### Step W4 — Event log: the errors behind the slowness

**Goal:** read the rare, high-signal events that confirm the story or reveal
a second problem, as `dmesg` does on Linux.

```powershell
# Errors and warnings in the System log, last 24 hours (first line of each message)
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3; StartTime=(Get-Date).AddHours(-24)} -MaxEvents 40 |
  Select-Object TimeCreated, Id, ProviderName, @{n='Message'; e={$_.Message.Split("`n")[0]}} | Format-Table -Wrap
# The usual suspects: 2004 low virtual memory, 153 I/O retried, 129 device reset, 7 bad block
Get-WinEvent -FilterHashtable @{LogName='System'; Id=2004,153,129,7} -MaxEvents 10 | Format-List TimeCreated, Id, Message
# Unexpected reboots: 41 (Kernel-Power), 6008 (unexpected shutdown)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=41,6008} -MaxEvents 5 -ErrorAction SilentlyContinue
```

```
TimeCreated : 10/3/2026 10:31:12 AM
Id          : 2004
Message     : Windows successfully diagnosed a low virtual memory condition. The following programs
              consumed the most virtual memory: sqlservr.exe (2140) consumed 5662310400 bytes,
              w3wp.exe (4416) consumed 989855744 bytes, and MsMpEng.exe (2988) consumed 421527552 bytes.

TimeCreated : 10/3/2026 10:29:47 AM
Id          : 153
Message     : The IO operation at logical block address 0x2c1a3f8 for Disk 0 (PDO name:
              \Device\00000032) was retried.
```

**What it means:**

- Event 2004 (source Resource-Exhaustion-Detector) lists the processes that held the most commit when Windows ran low: the culprit from Step W2, now with a timestamp you can match against user complaints.
- Event 153 means the storage stack retried an I/O that timed out. A few during a burst of paging can simply be load; a steady stream, or Event 129 (the driver reset the device), points at the storage path or the hypervisor (section 13). Event 7 ("bad block") points at a failing disk.
- Events 41 and 6008 tell you whether the server rebooted unexpectedly, which explains "it was slow, then it was down".

**Why this step (now):** one event can settle the story (2004 names the
memory hog) or reveal a second, independent problem (storage retries) that
the counters only hint at.

**Next step:** storage retries without memory pressure → the storage or
virtualisation team (section 13). Memory exhaustion confirmed → "Windows
wrap-up". Slowness that comes and goes → Step W5.

### Step W5 — Record history with a data collector

**Goal:** have per-second-ish history for "it was slow at 2 a.m.", which
Windows does not keep by default.

```powershell
# Circular binary log, one sample every 15 s, capped at 512 MB
logman create counter SlowCatch -si 00:00:15 -f bincirc -max 512 -o "C:\PerfLogs\SlowCatch" -c `
  "\Processor(*)\% Processor Time" "\System\Processor Queue Length" "\Memory\Available MBytes" `
  "\Memory\Pages/sec" "\Memory\% Committed Bytes In Use" "\PhysicalDisk(*)\Avg. Disk sec/Read" `
  "\PhysicalDisk(*)\Avg. Disk sec/Write" "\PhysicalDisk(*)\Current Disk Queue Length" `
  "\Network Interface(*)\Bytes Total/sec" "\Process(*)\% Processor Time" "\Process(*)\Private Bytes"
logman start SlowCatch
# Data collectors do not restart after a reboot on their own: add a start-up task
schtasks /create /tn "Start SlowCatch" /sc onstart /ru SYSTEM /tr "logman start SlowCatch"
logman query SlowCatch
# Later: open the .blg in Performance Monitor (View Log Data), or export the slow window to CSV
relog "C:\PerfLogs\BLGFILE.blg" -f csv -o "C:\PerfLogs\slowcatch.csv" -b "10/3/2026 1:50:00AM" -e "10/3/2026 2:40:00AM"
```

```
Name:                 SlowCatch
Status:               Running
Root Path:            C:\PerfLogs
Segment:              Off
Schedules:            On
Run as:               SYSTEM

Name:                 SlowCatch\SlowCatch
Type:                 Counter
Append:               Off
Circular:             On
Overwrite:            Off
Sample Interval:      15
Output Location:      C:\PerfLogs\SlowCatch.blg

The command completed successfully.
```

**What it means:**

- `Status: Running` and `Circular: On`: the collector records continuously and overwrites its oldest data at 512 MB, so it never fills the disk. `Output Location` is the file name to use in place of BLGFILE when you export.
- `\Process(*)` counters are what make this useful for "which process at 02:10", the Windows version of `atop` logs (Step H2). They are also what makes the file grow fastest; drop them if space is tight.
- For a fleet, a monitoring agent (for example Prometheus's `windows_exporter`) is the long-term answer; the collector is the zero-install stopgap.

**Why this step (now):** without history, intermittent slowness on Windows
can only be caught live. Like Step H6 on Linux, this records the evidence
before the next occurrence.

**Next step:** at the next complaint, export the window and read it like
Step H1, then apply Steps W2–W4 to that time. Also check Task Scheduler
history and Windows Update history for jobs that started then (the Windows
version of Step H3).

### Windows wrap-up: tree, fix, rollback, prevent

```
Windows slow
├── Get-Counter (W1): which resource?
│   ├── Available MBytes low + Pages/sec high ─→ W2 by memory
│   │     ├── product cache default (SQL Server, JVM) ─→ cap it
│   │     └── Private Bytes rising for hours ─────────→ leak → developers / planned restart
│   ├── queue > 2 per CPU, CPU high ───────────→ W2 by CPU → Defender / Windows Update / app
│   ├── % Privileged Time high ───────────────→ paging, drivers, filter drivers (AV) → W3, W4
│   ├── disk sec/Read or sec/Write high ───────→ W3 who → page file? backup? storage (W4: 153/129)
│   └── nothing saturated ─────────────────────→ the app waits (section 7 thinking)
└── comes and goes ────────────────────────────→ W5 collector + Task Scheduler / update history
```

**Fix & verify** (the `win-app01` story): cap SQL Server's memory so the OS
and IIS keep room. The setting is dynamic; no restart is needed. Agree the
value with the DBA.

```powershell
# 8 GB VM: about 4 GB for SQL Server leaves room for Windows, IIS and the agents
sqlcmd -S localhost -E -Q "EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'max server memory (MB)', 4096; RECONFIGURE;"
# Verify: paging stops and disk latency falls within a few minutes
Get-Counter '\Memory\Available MBytes','\Memory\Pages/sec','\PhysicalDisk(_Total)\Avg. Disk sec/Write' -SampleInterval 2 -MaxSamples 5
```

> ⚠️ Do not turn off Microsoft Defender real-time protection to "fix" CPU or
> disk load. Add exclusions only for paths the software vendor documents (for
> example SQL Server data and log files), with your security team's
> agreement, and move full scans out of business hours.

**Rollback:** `sqlcmd -S localhost -E -Q "EXEC sp_configure 'max server memory (MB)', 2147483647; RECONFIGURE;"`
restores the default. Remove the collector with `logman stop SlowCatch`,
`logman delete SlowCatch` and `schtasks /delete /tn "Start SlowCatch" /f`.

**Prevent it next time:** run a monitoring agent or the `SlowCatch`
collector on every Windows server; alert on `Available MBytes`, disk latency
and events 2004, 153 and 129; set an explicit memory cap for every database
or JVM on a shared server; schedule Windows Update installs and full
antivirus scans into maintenance windows.

---

## 17. macOS: quick playbook

> 📚 **Study path:** 1) Note: [macOS reference](20-macos.md), section 3 (processes & performance) and section 6 (the unified log) · 2) KodeKloud: no macOS performance course (check the current catalog) · 3) Practice: on your own Mac, start two `yes > /dev/null &` jobs and find them with `top -o cpu`, then `kill %1 %2` (section 20, drill 12).

**Level:** [L1 · Junior]. It is your own laptop most of the time, sometimes a
Mac build agent (a GitLab runner on a Mac mini). Same method, different tools.

Three macOS facts change how you read the numbers:

- The load average counts runnable threads only. Unlike Linux, it does not include tasks waiting on disk, so "high load, idle CPU" (section 14) does not happen the same way.
- macOS **compresses** memory before it swaps. A large compressor is the first warning; swap-outs per second are the real pain.
- Apple Silicon uses 16 KB pages, Intel Macs 4 KB. Multiply page counts accordingly.

### Step X1 — top sorted by CPU, and the load

**Goal:** see the load, the CPU split, memory and the hottest processes in
one screen, with nothing to install.

```bash
# macOS (Terminal), not Linux
sysctl -n hw.ncpu hw.memsize       # logical CPUs, RAM in bytes
# -l 2 takes two samples: read the SECOND one (the first sample's %CPU is not meaningful)
top -l 2 -o cpu -n 6 -stats pid,command,cpu,mem,threads,state,time | tail -n 18
```

```
10
17179869184
Processes: 612 total, 4 running, 608 sleeping, 3011 threads
2026/10/03 10:42:31
Load Avg: 9.81, 7.42, 4.10
CPU usage: 61.12% user, 18.40% sys, 20.48% idle
SharedLibs: 512M resident, 98M data, 61M linkedit.
MemRegions: 412339 total, 6012M resident, 312M private, 2114M shared.
PhysMem: 15G used (2811M wired, 3012M compressor), 312M unused.
VM: 241T vsize, 4321M framework vsize, 1823412(0) swapins, 2412331(0) swapouts.
Networks: packets: 9123412/9812M in, 6123411/2101M out.
Disks: 4123412/81G read, 3123120/92G written.

PID    COMMAND          %CPU  MEM    #TH  STATE    TIME
4121   com.apple.Virtua 312.4 6144M  28   running  41:12:09
612    mds_stores       98.1  412M   9    running  02:31:44
1288   Google Chrome He 41.2  1012M  24   sleeping 03:12:01
901    WindowServer     12.3  402M   21   running  08:44:12
3311   node             9.8   811M   14   sleeping 00:41:10
```

**What it means:**

- `Load Avg` 9.8 on 10 CPUs with 20% idle: busy but not yet queueing badly.
- `com.apple.Virtua...` (the virtual machine behind Docker Desktop and similar tools) uses 312%, three cores: the containers inside it are busy. Look inside with `docker stats`, then apply sections 3 and 12 there.
- `mds_stores` near 100%: Spotlight indexing, typical after a macOS update or when a huge folder (`node_modules`, a Docker data directory, build caches) sits in an indexed location.
- `PhysMem` shows only 312 MB unused and 3 GB in the compressor, and the swap-in/swap-out counters are large: memory pressure as well (Step X2).
- The `(0)` after the swap counters is the change since the previous sample: 0 here, so the swapping happened earlier. Non-zero values there mean swapping right now.

**Why this step (now):** `top` ships with every Mac and gives load, CPU
split, memory and the culprit list at once. Activity Monitor shows the same
data, but `top` output can be pasted into a ticket.

**Next step:** memory signs → Step X2. A process doing disk I/O
(`mds_stores`, `backupd`) → Step X3. Everything hot and the fans loud → Step
X4. The Docker VM is the hot process → `docker stats`, then section 12.

### Step X2 — Memory pressure, compression and swap

**Goal:** decide whether the Mac is short of memory right now.

```bash
# macOS (Terminal), not Linux
memory_pressure                 # the number behind Activity Monitor's "Memory Pressure" graph
vm_stat 1 | head -n 4           # per-second page counters; watch the swapins / swapouts columns
sysctl vm.swapusage
top -l 1 -o mem -n 5 -stats pid,command,mem | tail -n 6
```

```
The system has 17179869184 (1048576 pages with a page size of 16384).

Stats:
Pages free: 19112
Pages purgeable: 1201
Pages purged: 412331

Swap I/O:
Swapins: 1823412
Swapouts: 2412331

Compressor Stats:
Pages used by compressor: 192771
Pages decompressed: 8123412
Pages compressed: 9812331

System-wide memory free percentage: 8%

vm.swapusage: total = 4096.00M  used = 3411.25M  free = 684.75M  (encrypted)

PID    COMMAND          MEM
4121   com.apple.Virtua 6144M
1288   Google Chrome He 1012M
3311   node             811M
2201   Code Helper (Ren 744M
612    mds_stores       412M
```

(`memory_pressure` output abbreviated. `vm_stat 1` output omitted for width:
its last two columns, swapins and swapouts per second, should be 0 on a
healthy Mac.)

**What it means:**

- "System-wide memory free percentage" 8%: Activity Monitor would draw the memory pressure graph yellow or red. Below about 10–15% with swap-outs per second, the Mac is short of memory.
- 192,771 compressor pages × 16 KB = about 3 GB of compressed memory: the first line of defence is already working hard.
- 3.4 GB of swap used is history on its own; swap-outs per second in `vm_stat 1` are the live signal, exactly like `si`/`so` on Linux (Step M2).
- The Docker Desktop VM holds 6 GB of a 16 GB Mac. Its memory is set in Docker Desktop → Settings → Resources and is reserved for the VM whether the containers need it or not.

**Why this step (now):** Macs with 8 or 16 GB of unified memory, running a
container VM, an IDE and a browser, are memory-bound far more often than
CPU-bound, and the compressor hides it until it suddenly does not.

**Next step:** shrink the biggest consumer (the container VM's memory
setting, browser tabs, an IDE's language servers) and re-check. Disk busy as
well → Step X3.

### Step X3 — Disk and file activity with fs_usage

**Goal:** name the process and the files behind the disk activity.

```bash
# macOS (Terminal), not Linux
iostat -w 1 -c 5                                      # per disk: KB/transfer, transfers/s, MB/s
sudo fs_usage -w -f diskio -t 10 | head -n 20         # who reads/writes the disk, for 10 s
sudo fs_usage -w -f filesys mds_stores | head -n 10   # file-level calls of one process (Ctrl-C)
tmutil status                                         # is a Time Machine backup running?
mdutil -s /                                           # Spotlight indexing state of a volume
```

```
              disk0       cpu    load average
    KB/t  tps  MB/s  us sy id   1m   5m   15m
   48.12 2311 108.62 61 18 21  9.81 7.42 4.10

10:43:01.123412  RdData[A]   D=0x01a2b3c0  B=0x10000  /dev/disk3s5  /Users/dev/projects/shop/node_modules/.cache/babel/4f1c.json  0.004211 W mds_stores.612
10:43:01.130021  WrData[A]   D=0x02b1c4d8  B=0x8000   /dev/disk3s5  /System/Volumes/VM/swapfile3                                   0.012001 W kernel_task.0

Backup session status:
{
    BackupPhase = Copying;
    ClientID = "com.apple.backupd";
    Percent = "0.41";
    Running = 1;
}
/:
	Indexing enabled.
```

**What it means:**

- The internal disk moves 108 MB/s at 2,311 transfers per second while you are just editing code.
- `mds_stores` reads files in a project's `node_modules` cache: Spotlight is indexing build artefacts nobody will ever search for.
- `kernel_task` writes to `/System/Volumes/VM/swapfile3`: swap traffic from Step X2.
- Time Machine is copying (41% done). Three kinds of background work compete with your foreground work at once.

**Why this step (now):** on a Mac, "slow" is often housekeeping (Spotlight,
Time Machine, Photos analysis, cloud sync) competing with you, and
`fs_usage` names it down to the file path.

**Next step:** Spotlight on development folders → exclude them (wrap-up).
Time Machine during working hours → let it finish, or stop it and schedule
it. Swap traffic → back to Step X2. Nothing obvious → Step X4.

### Step X4 — Thermal throttling and hang reports

**Goal:** check whether the CPU is being held back by heat, and whether apps
have been freezing.

```bash
# macOS (Terminal), not Linux
pmset -g therm                                       # thermal and performance warnings, CPU speed limit
sudo powermetrics --samplers thermal -n 1            # Apple Silicon: thermal pressure level
ls -lt /Library/Logs/DiagnosticReports | head -n 5   # .hang and .spin reports from frozen apps
```

```
2026-10-03 10:44:12 +0200 CPU Power notify
	CPU_Scheduler_Limit 	= 100
	CPU_Available_CPUs 	= 8
	CPU_Speed_Limit 	= 56

**** Thermal pressure ****

Current pressure level: Heavy

-rw-r-----  1 root  admin  812331 Oct  3 10:39 Xcode_2026-10-03-103912_mbp.hang
```

**What it means:**

- `CPU_Speed_Limit 56` (Intel Macs): the CPU is capped at 56% of its speed because of heat. Everything CPU-bound takes almost twice as long.
- On Apple Silicon, `powermetrics` reports the thermal pressure level instead: `Nominal` is fine, `Heavy` or `Critical` means the chip is slowing itself down.
- Causes: blocked vents (a laptop on a bed or in a closed dock), dust, a hot room, a failing fan, or simply a sustained heavy build on a fanless model.
- A `.hang` report means an app's main thread stopped responding; it contains the stack, which is what the app's developers need.

**Why this step (now):** when everything is slow and no single process
explains it, the CPU itself may be throttled. Nothing in software fixes that.

**Next step:** → wrap-up.

### macOS wrap-up: tree, fix, rollback, prevent

```
Mac slow
├── top -o cpu (X1): one process hot? ─────────→ quit or restart it; container VM → docker stats
├── memory free < 10–15%, swapouts/s > 0 (X2) ─→ shrink the container VM, close the biggest apps
├── fs_usage (X3): mds_stores / backupd / swap ─→ exclude folders, reschedule backup, fix memory
└── speed limit < 100 / pressure Heavy (X4) ────→ cooling, airflow, hardware check
```

**Fix & verify:**

```bash
# macOS (Terminal), not Linux
# Stop Spotlight indexing a dedicated development or data volume
sudo mdutil -i off /Volumes/Dev
# Folders on the system volume: System Settings → Spotlight → Search Privacy → add the folder
# Stop a running Time Machine backup now (it resumes at the next scheduled run)
tmutil stopbackup
# Verify
top -l 2 -o cpu -n 5 -stats pid,command,cpu | tail -n 6
memory_pressure | tail -n 1
```

**Rollback:** `sudo mdutil -i on /Volumes/Dev` re-enables indexing (it
rebuilds the index); `tmutil startbackup` starts a backup immediately.

**Prevent it next time:** keep 15–20% of the disk free (APFS snapshots and
swap need room), exclude source trees, `node_modules` and container data from
Spotlight and Time Machine, size the container VM's CPU and memory
deliberately, and glance at the memory pressure graph before blaming the
network.

---

## 18. Master decision tree

> 📚 **Study path:** 1) Note: the wrap-up trees at the end of sections 2–17, and the short tree in [CPU & performance](03-cpu-performance.md) · 2) Read: Google SRE book, [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) · 3) Book: [Debugging: The 9 Indispensable Rules](https://debuggingrules.com/) ("Quit thinking and look", "Change one thing at a time") · 4) Practice: section 20, drill 13 (the random game day), using only this tree.

**Level:** [L2 · Mid]. Mid-level engineers should carry this tree in their
head; Seniors teach it and extend it with what their own platform does wrong.

The whole module on one screen. Read it top to bottom: each line is cheaper
and more general than the ones below it.

```
"It's slow"
│
├─ 0. Business burning AND a deploy or change in the last hour?
│     └─ yes → roll back first (Dokploy previous deployment, docker service rollback,
│              kubectl rollout undo), then investigate on evidence ............ section 1
│
├─ 1. Define it: for whom, doing what, since when, always or sometimes,
│     how slow in numbers, what changed? ................................... section 1
│     └─ measure: curl -w phases / time COMMAND
│         ├─ dns 5 s or 10 s ............................................. Step N1
│         ├─ connect large ............................... Step A5, module 24
│         ├─ tls minus connect large ................... module 18, section 3
│         ├─ total minus ttfb large (transfer) ...................... module 24
│         └─ ttfb large → the server or what is behind it ↓
│
├─ 2. Happening now?
│     ├─ no  → history: sar (H1) → atop (H2) → schedules (H3) → journal (H4)
│     │        → graphs (H5) → nothing recorded? slowcatch (H6) ............ section 8
│     └─ yes → snapshot + 60-second checklist ............................. section 2
│
├─ 3. Shortcuts from the kernel log (Step 2)
│     OOM → M4 · I/O errors → D8 · conntrack full → N2 · hung tasks → D3
│     soft lockup → section 13 · thermal → C9 · SYN flooding → A5
│
├─ 4. Which resource is saturated? (USE: utilisation, saturation, errors)
│     ├─ CPU: r > cores, id ≈ 0, PSI cpu ............................... section 3
│     │     ├─ one core at 100% usr → C2, C4 (single thread)
│     │     ├─ one core high in soft/irq → section 15
│     │     ├─ st high → C8, section 13
│     │     ├─ container slow, host idle → C7 (throttling)
│     │     └─ sy high → C6 (syscalls, context switches)
│     ├─ Memory: si/so > 0, PSI memory, OOM kills, kswapd .............. section 4
│     ├─ Disk: wa + b, await, aqu-sz, PSI io ........................... section 5
│     │     └─ load high but CPU idle, tasks in D state → section 14 → NFS? section 11
│     ├─ Network: DNS stalls, conntrack, retransmits ......... section 6, module 24
│     └─ nothing saturated → the application is waiting ................ section 7
│           A1 strace -c -w → A2 which peer → A6 database / A9 locks /
│           A5 pools and queues / A7 GC / A4 limits / A10 which endpoint
│
├─ 5. A known symptom? boot → 9 · SSH login → 10 · hung shell → 11
│     container only → 12 · VM on a busy host → 13
│
├─ 6. Not Linux? Windows → 16 · macOS → 17
│
└─ 7. After the fix: re-measure with the SAME command as before (curl -w, the
      snapshot), keep the rollback ready, add the alert or limit that would have
      caught it (section 19), write the five-line note.
```

**Quick index: symptom to first command.**

| Symptom or clue | First command | Go to |
|---|---|---|
| "Everything is slow", no detail | `curl -w` phases, then the snapshot | Sections 1, 2 |
| Load high, CPU busy | `vmstat 1`, `mpstat -P ALL 1` | Section 3 |
| Load high, CPU idle | `vmstat 1` (`b` high, `r` low), then `ps -eo state,pid,wchan:32,cmd` | Section 14 |
| `kswapd0` near the top, swap activity | `vmstat 1` (si/so), `cat /proc/pressure/memory` | Section 4 |
| Exit code 137, "Killed" | `journalctl -k -g 'out of memory'` | Step M4 |
| `wa` high, slow writes | `iostat -xyz 1` | Section 5 |
| Lookups take 5 s, `sudo` slow | `time getent ahosts NAME` | Step N1 |
| Random 1–3 s delays under load | `journalctl -k -g conntrack`, `nstat` | Steps N2, N3 |
| Requests slow, all resources quiet | `strace -c -w -f -p PID` | Section 7 |
| Slow at night or "sometimes" | `sar -q -f /var/log/sysstat/saDD` | Section 8 |
| Slow only inside a container | `cat .../cpu.stat`, `docker stats` | Step C7, section 12 |
| One CPU at 100% in `%soft` | `grep NET_RX /proc/softirqs`, `/proc/interrupts` | Section 15 |

**When to escalate, and what to bring.** Your job is to find the layer and
bring evidence. The owner of that layer applies the fix.

| The evidence says | Escalate to | Bring |
|---|---|---|
| Steal, ballooning, high latency at low IOPS | virtualisation or storage team | `%steal`, balloon size, `iostat` await versus IOPS, timestamps (section 13) |
| Credits at 0, EBS burst balance at 0 | cloud owner or budget holder | CloudWatch graphs, instance and volume types (Steps C8, D6) |
| One slow query, locks, pool exhaustion | DBA or developers | the query, its runtime, `pg_stat_activity` output (Steps A5, A6) |
| A hot function, a leak, GC thrash, a contended lock | developers | flame graph, thread dump, `jstat`, RSS over time (Steps C4, C5, M6, A7, A9) |
| Retransmits or high RTT to one peer | network team | `ss -ti` RTT and retransmits, `mtr` from module 24 |
| Failing disk, thermal events | hardware or data-centre team | SMART attributes, `dmesg` lines, BMC event log (Steps C9, D8) |

**Fix & verify, every time:** one change at a time; re-run the exact
measurement you took before the change; compare with the healthy-day
baseline; keep the rollback command written next to the change; and only
then close the ticket.

---

## 19. Prevent it next time: monitoring, alerts, baselines

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals (installation as a systemd service, Node Exporter; [lesson note](https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page)), then the Alerting section ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 2) Note: [Learn: performance & observability](32-learn-performance-observability.md), sections 11–13 (Prometheus, Alertmanager, Grafana) · 3) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([68 min](https://www.youtube.com/watch?v=6xmWr7p5TE0)) · 4) Read: the [Grafana fundamentals](https://grafana.com/tutorials/grafana-fundamentals/) tutorial · 5) Practice: the Ops Ladder L4 drill: node_exporter, Prometheus and Grafana in the homelab, alerts on disk above 85% and failed systemd units, then the saturation rules below.

**Level:** [L3 · Senior] to build it; [L4 · Lead] to own the alerting
policy, the baselines and the capacity reviews.

Every wrap-up in this module ended with "Prevent it next time". They come
down to five habits: **record** history on every box, **baseline** what normal
looks like, **alert on saturation** instead of utilisation, **forecast**
capacity, and **write down** what happened.

### Record: history on every server

Put the evidence collectors in your base Ansible role so that no server ever
reaches an incident without them. The excerpt below assumes Ubuntu and the
distribution's `prometheus-node-exporter` package (handlers not shown).

```yaml
# roles/base/tasks/observability.yml (excerpt)
- name: Install evidence collectors
  ansible.builtin.apt:
    name: [sysstat, atop, prometheus-node-exporter]
    state: present
    update_cache: true

- name: Enable sysstat history
  ansible.builtin.lineinfile:
    path: /etc/default/sysstat
    regexp: '^ENABLED='
    line: 'ENABLED="true"'

- name: Drop-in directory for the sysstat timer
  ansible.builtin.file:
    path: /etc/systemd/system/sysstat-collect.timer.d
    state: directory
    mode: "0755"

- name: Sample sysstat every 2 minutes instead of 10
  ansible.builtin.copy:
    dest: /etc/systemd/system/sysstat-collect.timer.d/override.conf
    content: |
      [Timer]
      OnCalendar=
      OnCalendar=*:00/2
    mode: "0644"
  notify: reload systemd

- name: atop samples every 60 s
  ansible.builtin.lineinfile:
    path: /etc/default/atop
    regexp: '^LOGINTERVAL='
    line: 'LOGINTERVAL=60'
  notify: restart atop

- name: node_exporter with the systemd collector (pressure/PSI is on by default)
  ansible.builtin.lineinfile:
    path: /etc/default/prometheus-node-exporter
    regexp: '^ARGS='
    line: 'ARGS="--collector.systemd"'
  notify: restart prometheus-node-exporter

- name: Collectors enabled and running
  ansible.builtin.systemd_service:
    name: "{{ item }}"
    enabled: true
    state: started
  loop: [sysstat, atop, prometheus-node-exporter]
```

Verify on one host after the play:

```bash
systemctl is-active sysstat atop prometheus-node-exporter
systemctl list-timers 'sysstat-collect*' --no-pager | head -2
curl -s http://127.0.0.1:9100/metrics | grep -E '^node_pressure_(cpu|memory|io)_(waiting|stalled)_seconds_total'
sudo ufw status | grep 9100          # 9100 must be open to the Prometheus server only
```

```
active
active
active
NEXT                        LEFT          LAST                        PASSED       UNIT                  ACTIVATES
Sat 2026-10-03 12:02:00 UTC 1min 12s left Sat 2026-10-03 12:00:00 UTC 47s ago      sysstat-collect.timer sysstat-collect.service
node_pressure_cpu_waiting_seconds_total 81234.51
node_pressure_io_stalled_seconds_total 4021.88
node_pressure_io_waiting_seconds_total 9120.33
node_pressure_memory_stalled_seconds_total 402.11
node_pressure_memory_waiting_seconds_total 611.23
9100/tcp                   ALLOW       192.0.2.50
```

→ All three collectors run, sysstat now samples every 2 minutes, node_exporter
exports PSI, and only the Prometheus server (192.0.2.50) may scrape port 9100.
node_exporter runs as a normal systemd service, not a published Docker port,
so UFW does filter it. On Docker hosts, also scrape container metrics
(cAdvisor) and Traefik's own Prometheus metrics, which give you RED per router
(see the [Traefik documentation](https://doc.traefik.io/traefik/)).

### Baselines: know what normal looks like

You cannot call a number abnormal if you never wrote down the normal one.
Once a month, and after every big change, record per server:

| Metric | Where it comes from | `web01` normal (example) | Worry when |
|---|---|---|---|
| CPU busy, p95 over business hours | `sar -u`, `node_cpu_seconds_total` | 35% | above 70% (queueing grows fast, see section 1) |
| Run queue per core, p95 | `sar -q` | 0.6 | above 1.5 |
| `MemAvailable`, minimum of the day | `sar -r`, node_exporter | 3.1 GB (39%) | below 15–20% |
| Swap-in per second | `sar -W` | 0 | anything sustained |
| Disk await per device, p95 | `sar -d -p` | `sdb` 6 ms | 3× normal |
| PSI io `some`, p95 | `/proc/pressure/io` | 2% | above 10% |
| Retransmit ratio | `nstat`, node_exporter | 0.05% | above 1% |
| p95 latency per vhost or router | access logs (Step A10), Traefik metrics | shop 180 ms | 2× normal |
| Boot time, SSH login time | `systemd-analyze`, `time ssh HOST true` | 38 s, 0.4 s | growing release after release |

Keep the healthy-day snapshot from section 2 next to this table in the
runbook repository. During an incident you compare against both.

### Alert on saturation, not utilisation

"CPU above 90%" pages people for healthy batch jobs and stays silent while a
1.5-CPU container throttles on an idle host. Alert on **work waiting**
(saturation and errors), and page humans on **symptoms users feel** (RED:
latency and errors); everything else becomes a ticket.

```yaml
# /etc/prometheus/rules/slow-host.yml
groups:
  - name: slow-host
    rules:
      - alert: HostCpuSaturated
        expr: rate(node_pressure_cpu_waiting_seconds_total[5m]) > 0.20
        for: 10m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: tasks wait for a CPU {{ $value | humanizePercentage }} of the time"
          runbook: "Handbook module 23, section 3"
      - alert: HostMemoryPressure
        expr: rate(node_pressure_memory_stalled_seconds_total[5m]) > 0.05
        for: 5m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: all tasks stalled on memory {{ $value | humanizePercentage }} of the time"
          runbook: "Handbook module 23, section 4"
      - alert: HostSwapInActive
        expr: rate(node_vmstat_pswpin[5m]) > 100
        for: 10m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: swapping in {{ $value | humanize }} pages/s"
      - alert: HostOomKill
        expr: increase(node_vmstat_oom_kill[15m]) > 0
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: the kernel OOM-killed a process (Step M4)"
      - alert: HostIoPressure
        expr: rate(node_pressure_io_stalled_seconds_total[5m]) > 0.10
        for: 10m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: all tasks stalled on I/O {{ $value | humanizePercentage }} of the time"
          runbook: "Handbook module 23, section 5"
      - alert: HostDiskReadLatencyHigh
        expr: rate(node_disk_read_time_seconds_total[5m]) / rate(node_disk_reads_completed_total[5m]) > 0.05
        for: 10m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }} {{ $labels.device }}: reads take {{ $value | humanizeDuration }}"
      - alert: HostFilesystemFullIn3Days
        expr: predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"}[12h], 3*24*3600) < 0
        for: 30m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }} {{ $labels.mountpoint }} will be full within 3 days at this rate"
      - alert: HostBlockedTasks
        expr: node_procs_blocked > 10
        for: 10m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: {{ $value }} tasks in D state (section 14)"
      - alert: HostCpuSteal
        expr: avg by (instance) (rate(node_cpu_seconds_total{mode="steal"}[5m])) > 0.10
        for: 15m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: hypervisor steals {{ $value | humanizePercentage }} of CPU (section 13)"
      - alert: HostConntrackNearFull
        expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.80
        for: 5m
        labels: {severity: page}
        annotations:
          summary: "{{ $labels.instance }}: conntrack table {{ $value | humanizePercentage }} full; new connections will be dropped"
      - alert: HostSystemdUnitFailed
        expr: node_systemd_unit_state{state="failed"} == 1
        for: 5m
        labels: {severity: ticket}
        annotations:
          summary: "{{ $labels.instance }}: {{ $labels.name }} has failed"
      - alert: RouterLatencyHigh
        expr: histogram_quantile(0.95, sum by (le, service) (rate(traefik_service_request_duration_seconds_bucket[5m]))) > 1
        for: 10m
        labels: {severity: page}
        annotations:
          summary: "{{ $labels.service }}: p95 latency {{ $value | humanizeDuration }} (users feel this)"
          runbook: "Handbook module 23, section 18"
```

```bash
promtool check rules /etc/prometheus/rules/slow-host.yml
```

```
Checking /etc/prometheus/rules/slow-host.yml
  SUCCESS: 12 rules found
```

→ Twelve rules, and only two of them page: a symptom users feel (p95 latency
per Traefik service) and an imminent hard failure (conntrack about to drop
connections). The other ten open tickets that name the section of this
module to start from. Tune the thresholds against your baselines; the
numbers above are starting points, not standards. For containers, add the
cAdvisor throttling ratio from Step C7 (above about 0.25 for 15 minutes).

**Why this split:** pages are for "users are hurting now"; tickets are for
"a resource is heading there". Paging on every saturated resource trains
people to ignore pages; never alerting on saturation means you only learn
about it from users.

### Capacity: forecast before it bites

Remember the queueing table in section 1: at 80% utilisation, response times
are already about five times the idle value. Capacity planning means acting
before a resource reaches that zone.

```
# PromQL for a monthly capacity review (Grafana table panels)
# CPU busy, p95 of hourly values over 30 days
quantile_over_time(0.95, (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))[30d:1h])
# Lowest memory headroom seen in 30 days
min_over_time((node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)[30d:1h])
# Days until /srv is full at the 7-day trend (negative = never at this rate)
node_filesystem_avail_bytes{mountpoint="/srv"} / -deriv(node_filesystem_avail_bytes{mountpoint="/srv"}[7d]) / 86400
```

Headroom targets that keep latency flat (adapt them to your SLOs):

| Resource | Keep below / above | Why |
|---|---|---|
| CPU busy, p95 | below 60–70% for latency-sensitive hosts | queueing (section 1) |
| `MemAvailable`, minimum | above 20% | room for page cache and spikes; no swapping |
| Filesystems | below 80% (data volumes) | allocator slowdown, time to react (Step D4) |
| IOPS and throughput | below 70% of the device or volume limit | caps cause sudden latency (Step D6) |
| Conntrack | below 50% of the limit | bursts double it quickly (Step N2) |
| Container CPU | throttled periods below 5% | tail latency (Step C7) |

The senior habit is a **written budget per host**: OS, Apache, the Docker and
Dokploy stack, each application, each with its CPU and memory share. Every
new vhost or container is checked against it before it is deployed, not
after the box starts swapping.

### Write it down: the five-line incident note

From your learning plan: after any incident, even a small one, write five
lines. They take five minutes and build the experience that makes you
faster next time.

```
Symptom:        web01 slow since 10:30, p95 4 s on every vhost (normal 180 ms).
First wrong guess: "Apache needs more workers."
Evidence that settled it: vmstat si/so 2–7 MB/s, PSI memory full 21%, java (shop-api) RSS 4.9 GB
                with -Xmx6g on an 8 GB host (Steps 3, M3, M5).
Fix:            shop-api heap via MaxRAMPercentage=75 inside a 4 GB service limit; swap stopped,
                p95 back to 190 ms at 11:20.
Next time I check first: PSI memory and the memory budget before any deploy that adds a container.
```

For bigger incidents, write a blameless postmortem (timeline, impact, root
cause, follow-ups with owners). See
[Learn: Git, CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) and the
[career ladder](40-career-ladder.md) for how postmortems become evidence of
seniority.

---

## 20. Practice lab: break it on purpose

> 📚 **Study path:** 1) Practice: KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) (free, Ubuntu 24.04) or a homelab VM · 2) KodeKloud: *Linux Challenges* (free; [course](https://kodekloud.com/courses/linux-challenges)) as the timed L1 check · 3) Practice: [SadServers](https://sadservers.com/scenarios) and [Killercoda Linux scenarios](https://killercoda.com/linux) for real broken servers against the clock · 4) Note: [Learn: performance & observability](32-learn-performance-observability.md), section 9 (benchmarking and load testing safely).

**Level:** every stage. Each drill carries its own tag; start at your level
and work up.

> ⚠️ Run every drill on a **throwaway test VM** (2–4 vCPU, 4 GB RAM, Ubuntu
> 24.04), never on a shared, production or Dokploy host. Take a VM snapshot
> first. `stress-ng` and `fio` can make a small VM unresponsive; every
> command below has a timeout, and the reset is "revert the snapshot".

### Lab setup and the one rule

```bash
sudo apt install stress-ng fio sysstat atop strace nfs-kernel-server nfs-common iperf3 docker.io
sudo systemctl enable --now sysstat atop docker
mkdir -p /var/tmp/fio
```

**The one rule (from your learning plan):** someone else, or a script, runs
the break command. You run the 60-second checklist and **name the saturated
resource before you look at the flags they used**. Then fix, verify with the
same command, and write the five-line note.

| # | Drill | Level | Use |
|---|---|---|---|
| 1 | CPU saturation, then a single hot thread | [L0 · Fresher] | Section 2, Steps C1–C3 |
| 2 | Memory pressure and a container OOM kill | [L0 · Fresher] → [L2 · Mid] | Section 4 |
| 3 | A backup starving a database's fsync | [L2 · Mid] | Section 5 |
| 4 | A throttled container on an idle host | [L2 · Mid] | Step C7, section 12 |
| 5 | A dead first DNS resolver | [L1 · Junior] | Step N1, section 10 |
| 6 | An endpoint waiting on a slow "database" | [L2 · Mid] | Section 7 |
| 7 | Slowness you only see in history | [L2 · Mid] | Section 8 |
| 8 | A slow boot | [L1 · Junior] | Section 9 |
| 9 | A hung NFS mount | [L1 · Junior] → [L2 · Mid] | Sections 11, 14 |
| 10 | Steal time on an overcommitted hypervisor | [L3 · Senior] | Section 13 |
| 11 | One CPU drowning in softirq | [L3 · Senior] | Section 15 |
| 12 | Windows and macOS hogs | [L1 · Junior] | Sections 16, 17 |
| 13 | The random game day | [L4 · Lead] | Sections 18, 19 |

### Drills 1–4: CPU, memory, disk, containers

**Drill 1 — CPU saturation, then one hot thread.** [L0 · Fresher]

```bash
stress-ng --cpu 8 --timeout 300s &                 # 8 busy workers on a 4-vCPU VM
# expect: vmstat r ≈ 8, us ≈ 100, PSI cpu some high; pidstat names stress-ng
stress-ng --cpu 1 --timeout 300s &                 # later, alone: one worker
# expect: mpstat shows ONE core at 100% usr, the average only ~25%
```

**Drill 2 — memory pressure, then an OOM-killed container.** [L0 · Fresher] → [L2 · Mid]

```bash
stress-ng --vm 2 --vm-bytes 60% --vm-keep --timeout 300s &   # raise the % until si/so appear
# expect: vmstat si/so > 0, kswapd0 in pidstat, PSI memory full > 0, available < 10%
docker run --rm -m 256m --memory-swap 256m python:3.12-slim \
  python3 -c "a=[]; [a.append(' ' * 10**6) for _ in range(1000)]"; echo "exit=$?"
# expect: exit=137; journalctl -k shows "Memory cgroup out of memory" with CONSTRAINT_MEMCG
```

**Drill 3 — a backup starving a database.** [L2 · Mid]

```bash
# The "database": small synchronous writes, an fdatasync after each one
fio --name=db --directory=/var/tmp/fio --rw=randwrite --bs=4k --size=256m \
    --fdatasync=1 --runtime=600 --time_based > /var/tmp/fio-db.txt &
# The "backup": a big sequential reader, started a minute later
fio --name=backup --directory=/var/tmp/fio --rw=read --bs=1m --size=2g \
    --direct=1 --runtime=300 --time_based > /dev/null &
# expect: iostat w_await and f_await jump, pidstat -d names the backup fio,
# PSI io rises. Then repeat the backup inside systemd-run with IOReadBandwidthMax
# (Disk wrap-up) and watch the database's latency recover.
```

**Drill 4 — a throttled container on an idle host.** [L2 · Mid]

```bash
docker run -d --name hog --cpus 0.5 ubuntu:24.04 \
  bash -c 'for i in $(seq 8); do (while :; do :; done) & done; wait'
# expect: host mostly idle; docker stats ~50%; cpu.stat nr_throttled climbing every period
docker rm -f hog                                   # clean up
```

### Drills 5–9: DNS, waiting, history, boot, NFS

**Drill 5 — a dead first resolver.** [L1 · Junior] Replace GOODDNS with a
resolver that works in your lab (your router or LAN DNS server).

```bash
# Inside a container, glibc reads resolv.conf directly: the classic 5-second wait
docker run --rm --dns 192.0.2.1 --dns GOODDNS ubuntu:24.04 bash -c 'time getent ahosts example.com'
# On the host (systemd-resolved): a dead server first in the list, until reverted
sudo resolvectl dns ens3 192.0.2.1 GOODDNS          # ens3 = your interface (ip -br link)
time getent ahosts example.org; time sudo true
sudo resolvectl revert ens3                         # undo
# Bonus (section 10): set "UseDNS yes" in an sshd drop-in, log in from another VM, time it
```

**Drill 6 — an endpoint waiting on a slow "database".** [L2 · Mid]

```bash
cat > /var/tmp/slowdb.py <<'EOF'
# A fake database: every query takes 2 seconds
import socketserver, time
class H(socketserver.StreamRequestHandler):
    def handle(self):
        self.rfile.readline(); time.sleep(2); self.wfile.write(b"result\n")
socketserver.ThreadingTCPServer(("127.0.0.1", 9999), H).serve_forever()
EOF
cat > /var/tmp/slowapp.py <<'EOF'
# A web app that asks the "database" on every request
import http.server, socket
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        s = socket.create_connection(("127.0.0.1", 9999)); s.sendall(b"query\n"); s.recv(100); s.close()
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")
http.server.ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
EOF
python3 /var/tmp/slowdb.py & python3 /var/tmp/slowapp.py &
for i in $(seq 20); do curl -s -o /dev/null http://127.0.0.1:8000/; done &
# Now find it WITHOUT reading the code: Steps A1 and A2
sudo strace -c -w -f -p "$(pgrep -f slowapp.py)"          # Ctrl-C after ~10 s
sudo strace -f -tt -T -e trace=network,poll -p "$(pgrep -f slowapp.py)" 2>&1 | head -20
ss -tnp | grep 9999
# expect: ~2 s spent in recvfrom on a socket to 127.0.0.1:9999 → "the database is slow"
```

**Drill 7 — slowness you can only see in history.** [L2 · Mid]

```bash
echo '*/15 * * * * root /usr/bin/stress-ng --hdd 2 --timeout 120s' | sudo tee /etc/cron.d/lab-noise
# Have someone else do this, wait an hour, then work ONLY from sar (H1), atop (H2) and the
# schedules (H3) to name the job and its exact minute. Clean up:
sudo rm /etc/cron.d/lab-noise
```

**Drill 8 — a slow boot.** [L1 · Junior] Snapshot first; this drill reboots
the test VM.

```bash
# Option A (any VM): a unit that holds up the boot target for 45 s
sudo tee /etc/systemd/system/lab-slowboot.service > /dev/null <<'UNIT'
[Unit]
Description=Lab: pretend to wait for something
Before=multi-user.target
[Service]
Type=oneshot
ExecStart=/bin/sleep 45
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload && sudo systemctl enable lab-slowboot.service
sudo systemctl reboot
# Option B (realistic): add a second NIC to the VM, disconnect its virtual cable in the
# hypervisor, and give it "dhcp4: true" in netplan: wait-online now times out after 2 minutes.
# After boot: systemd-analyze, blame, critical-chain, journalctl -b -u UNIT (section 9).
# Clean up: sudo systemctl disable lab-slowboot.service && sudo rm /etc/systemd/system/lab-slowboot.service
```

> ⚠️ Do not practise with a bogus `/etc/fstab` line. Without `nofail`, a
> missing disk does not just slow the boot: after the 90-second device
> timeout the VM drops into emergency mode and needs the console.

**Drill 9 — a hung NFS mount.** [L1 · Junior] → [L2 · Mid]

```bash
sudo mkdir -p /srv/export /mnt/share
echo '/srv/export 127.0.0.1(rw,sync,no_subtree_check)' | sudo tee /etc/exports.d/lab.exports
sudo exportfs -ra
sudo mount -t nfs4 -o hard 127.0.0.1:/srv/export /mnt/share
sudo systemctl stop nfs-server                      # the "server" dies
for i in 1 2 3 4 5; do (df /mnt/share > /dev/null 2>&1 &); done   # statfs always asks the server
# expect: load climbs, vmstat b rises, ps shows D state in rpc_wait_bit_killable (sections 11, 14)
# Recover: start the server (the stuck commands finish), then clean up
sudo systemctl start nfs-server
sudo umount /mnt/share; sudo rm /etc/exports.d/lab.exports; sudo exportfs -ra
```

### Drills 10–13: hypervisor, softirq, other OSes, game day

**Drill 10 — steal time.** [L3 · Senior] Homelab hypervisor only (Proxmox or
KVM): two test VMs with 4 vCPUs each on a host with 4 physical cores.

```bash
# In BOTH guests at the same time
stress-ng --cpu 4 --timeout 600s &
mpstat 1 10                 # expect %steal of 30–50% in each guest; compare with the host's PSI
```

**Drill 11 — one CPU drowning in softirq.** [L3 · Senior] A test VM with a
single-queue virtio NIC, and a second VM as the sender.

```bash
iperf3 -s                                           # on the test VM
iperf3 -c TESTVM -u -b 0 -l 64 -t 60                # on the sender: unlimited 64-byte UDP packets
# On the test VM: mpstat -P ALL 1 (one CPU high in %soft), /proc/softirqs NET_RX,
# /proc/net/softnet_stat drops. Then enable RPS (section 15 wrap-up) and compare.
```

**Drill 12 — Windows and macOS hogs.** [L1 · Junior]

```powershell
# Windows Server evaluation VM: four busy jobs, then find them with Step W2
1..4 | ForEach-Object { Start-Job { while ($true) {} } } | Out-Null
# ...investigate, then clean up:
Get-Job | Stop-Job; Get-Job | Remove-Job
```

```bash
# macOS (Terminal), not Linux: two busy processes, then find them with Step X1
yes > /dev/null & yes > /dev/null &
top -l 2 -o cpu -n 5 -stats pid,command,cpu | tail -n 6
kill %1 %2
```

**Drill 13 — the random game day.** [L4 · Lead] This is the Ops Ladder's L4
exit test: a script breaks one thing at a random time, you learn about it from
an alert (section 19), fix it, and publish a one-page postmortem.

```bash
cat > /var/tmp/gameday.sh <<'EOF'
#!/usr/bin/env bash
# Picks one fault at random and runs it for 10 minutes. TEST VM ONLY.
faults=(
  "stress-ng --cpu $(nproc) --timeout 600s"
  "stress-ng --vm 2 --vm-bytes 60% --vm-keep --timeout 600s"
  "stress-ng --hdd 2 --timeout 600s"
  "stress-ng --fork 4 --timeout 600s"
)
i=$((RANDOM % ${#faults[@]}))
echo "$(date -Is) ${faults[$i]}" >> /var/tmp/gameday.answer    # read only AFTER your postmortem
${faults[$i]} > /dev/null 2>&1
EOF
chmod 755 /var/tmp/gameday.sh
# Fire once, at a random moment in the next 10–70 minutes
sudo systemd-run --on-active=$((RANDOM % 3600 + 600)) /var/tmp/gameday.sh
```

→ Pass when the alert fired before you looked, you named the resource from
the checklist alone, the fault stopped (or would have been contained by a
limit), and the postmortem has a timeline, a root cause and at least one
follow-up that prevents the whole class of problem.

---

## 21. Self-check and exit test

> 📚 **Study path:** 1) Note: re-read the wrap-up trees (sections 2–17) and the master tree (section 18) · 2) KodeKloud: *Linux Challenges* (free; [course](https://kodekloud.com/courses/linux-challenges)) as the timed L1 check · 3) Practice: three [SadServers](https://sadservers.com/scenarios) scenarios, 30 minutes each, no hints · 4) Note: [Career ladder](40-career-ladder.md) to see what each stage is expected to show.

**Level:** questions and tasks are tagged per stage. Pass your own stage
before you move to the next one.

### Questions

Answer without notes, then check the answer key.

1. [L0 · Fresher] Load is 6 on a 4-CPU box and `top` shows 85% idle. Give two possible explanations and the one command that tells them apart.
2. [L0 · Fresher] `free -m` shows `free` 150 and `available` 5,200 on an 8 GB host. Is it short of memory?
3. [L1 · Junior] Which `vmstat` columns tell you the box is swapping right now, and why is "1.6 GB of swap used" alone not a problem?
4. [L1 · Junior] `curl -w` shows `dns=5.004s`. What is the likely cause, and what is your first command?
5. [L1 · Junior] An SSH login takes 10 s and the gap follows "Next authentication method: gssapi-with-mic". Give the client-side and the server-side fix.
6. [L1 · Junior] Why do you take the snapshot before restarting the slow service?
7. [L2 · Mid] An NVMe drive shows `%util` 100 with `r_await` 0.2 ms and `aqu-sz` 1.1. Is it saturated?
8. [L2 · Mid] A Dokploy app is slow, the host is 70% idle, and `docker stats` shows the container at 150% CPU. What do you check, and where?
9. [L2 · Mid] The kernel log says "Memory cgroup out of memory: Killed process ... (java)". Host or container limit? What do you check before raising the limit?
10. [L2 · Mid] `strace -c` without `-w` shows almost no time for a process that takes 3 s per request. Why, and what do you run instead?
11. [L2 · Mid] Users say the API was slow from 02:00 to 02:30. Name the four sources you check, in order, and what each one tells you.
12. [L3 · Senior] A gp2 volume shows IOPS flat at 300, `await` 40 ms and `%util` 64%. What is happening, and what is the fix without downtime?
13. [L3 · Senior] One CPU is at 95% `%soft` on a Traefik node and the others idle. Which three settings do you check, in order?
14. [L3 · Senior] Why can raising `MaxRequestWorkers` or the database pool size make a slow site slower?
15. [L4 · Lead] For the `web01` memory story, write one alert that pages and one that opens a ticket. Why that split?
16. [L4 · Lead] What must a capacity review show before you approve a bigger VM, and what would make you refuse?

### Answer key

1. Runnable tasks (CPU) or tasks in uninterruptible sleep (D state, usually disk or NFS); Linux load counts both. `vmstat 1`: `r` versus `b` (Step 1, section 14).
2. No. `free` is unused RAM, which Linux keeps low on purpose; `available` (65%) is what programs can still get without swapping (Step 7).
3. `si` and `so` non-zero for several seconds. Swap used can be old pages parked weeks ago; only swap activity hurts (Step M2).
4. The first resolver is dead and glibc waits its 5-second timeout. `time getent ahosts NAME`, then test each resolver with `dig @SERVER` (Step N1).
5. Client: `GSSAPIAuthentication no` for those hosts in `~/.ssh/config`. Server: a drop-in with `GSSAPIAuthentication no` (and `UseDNS no`), `sshd -t`, reload, test from a second session (section 10).
6. A restart destroys the evidence (the leak, the stuck thread, the hung call) and the problem returns. The snapshot costs about 20 seconds (section 2).
7. Probably not. `%util` only says something was always in flight; NVMe serves many requests in parallel. Latency and queue are low (section 5).
8. CPU throttling: `cpu.max` and `cpu.stat` (`nr_throttled`, `throttled_usec`) in the container's cgroup, and the Swarm service's limits (Step C7). Also thread pools sized to the host's CPU count.
9. A container limit (`CONSTRAINT_MEMCG`). Check whether usage is a leak (RSS over time, Step M6) or a heap or pool sized wrongly for the limit (Step M5) before raising it.
10. Without `-w`, strace reports CPU time in syscalls, and waiting in `poll` or `recvfrom` uses almost none. Use `strace -c -w -f -p PID`, then `-T` to find the slow call and its peer (Steps A1, A2).
11. sar (which resource, when: H1), atop (which process: H2), schedules: cron, timers, backups (H3), journal (what failed or restarted: H4); graphs if you have them (H5).
12. gp2 burst credits are exhausted and the volume is held at its baseline (3 IOPS per GiB). `aws ec2 modify-volume --volume-type gp3`, which works online (Step D6).
13. NIC channels (`ethtool -l`, more queues with `-L`), `irqbalance` running and IRQ affinity, then RPS for single-queue NICs (section 15).
14. If each request is slow because of the database, more workers or connections only push more concurrent work onto the database and use more RAM, which can make the host swap (Step A5, memory wrap-up).
15. Page on the symptom: p95 latency per Traefik router above 1 s for 10 minutes. Ticket on the cause: PSI memory `full` above 5%, swap-in activity, or an OOM kill. Pages are for user pain now; tickets for resources heading there (section 19).
16. It must show sustained saturation (PSI, run queue, swap, await) at normal traffic and a growth trend, with the current budget per service. Refuse if the "need" is a leak, an unsized heap or pool, a missing limit, or a batch job that could move (sections 4, 19).

### Practical exit test (timed)

Someone else picks the drill from section 20 and breaks the VM; you do not
see the command.

| Stage | Task | Time | Pass when |
|---|---|---|---|
| Fresher · [L0 · Fresher] | Drill 1 or 2: run section 2, save the snapshot, name the saturated resource | 15 min | The right resource, and three output lines that prove it |
| Junior · [L1 · Junior] | Drills 5 and 8 back to back: find, fix, verify, roll back | 30 min | Both fixed with before/after numbers; one rollback demonstrated |
| Mid-level · [L2 · Mid] | Drill 3 or 4, then drill 6, in an unknown order | 45 min | Culprit process and the peer it waits on named; mitigation applied; five-line note written |
| Senior · [L3 · Senior] | Drill 10 or 11, or a flame graph of drill 1's single-thread case | 60 min | An evidence package (counters, profile) and a change request with verification and rollback in GitLab's format |
| Senior/Lead · [L4 · Lead] | Drill 13, the random game day | 2 h | The alert fired before anyone looked; a one-page postmortem with timeline, root cause and a follow-up that prevents the class of problem |

---

## 22. Where to go next

> 📚 **Study path:** the KodeKloud order for this whole module: 1) *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Diagnose and Manage Processes, Monitor Storage Performance, Locate and Analyze System Log Files ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) *Docker Certified Associate* — Docker Engine – Security (resource limits) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 3) *Prep Course - Prometheus Certified Associate (PCA)* — Fundamentals and Alerting ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) · 4) *Fundamentals of SRE* — Observability and Monitoring, Incident Management ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 5) Outside KodeKloud, which has no Linux performance course: [Brendan Gregg's Linux performance page](https://www.brendangregg.com/linuxperf.html).

- **Slow between hosts, not on one host:** [Network slow / speed troubleshooting](24-playbook-network-speed.md).
- **Not slow but down (errors, timeouts, TLS):** [Site down](25-playbook-site-down.md).
- **Containers, Dokploy/Traefik and Kubernetes incidents:** [Containers & Kubernetes playbook](26-playbook-containers-k8s.md).
- **Which process owns that port, and what is it:** [Ports & services inventory](22-playbook-ports-inventory.md).
- **The theory behind every step** (queueing, USE, flame graphs, Prometheus): [Learn: performance & observability](32-learn-performance-observability.md).
- **Command references:** [CPU & performance](03-cpu-performance.md), [Memory](04-memory.md), [Storage & disk](01-storage-disk.md), [Processes](05-processes.md), [Logs & journal](06-logs-journal.md).
- **Your Apache and Dokploy context** (why Apache workers, Traefik and Swarm services appear in the examples): [Case study: Apache, 443 and Dokploy](21-case-apache-443-dokploy.md), [Deployment patterns](35-deployment-patterns.md), [Learn: web servers & proxies](29-learn-webservers-proxies.md).
- **Postmortems, SLOs and change management:** [Learn: Git, CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md); databases behind slow queries: [Learn: databases for ops](38-learn-databases-ops.md).
- **Where this skill sits in your career:** [Career ladder](40-career-ladder.md). "Can find why a server is slow, prove it, and stop it recurring" is a Mid-level skill on the way in and a Senior expectation on the way out.
