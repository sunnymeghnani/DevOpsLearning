# 03 — CPU & General Performance

Typical symptoms: high load, sluggish box, one core pinned, app latency spikes.

Key distinction to make early: **CPU-bound** (high us/sy) vs **I/O-bound**
(high wa, load high but CPU idle) vs **saturated run queue** (load >> cores).

---

## 1. Load average

### `uptime` — the 10-second health check
```bash
uptime
```
```
$ uptime
 14:02:11 up 41 days,  3:12,  2 users,  load average: 8.42, 6.10, 2.33
```
- Three numbers = 1, 5, 15-minute load averages.
- Rule of thumb: load ≈ number of CPU cores is "full". Get core count: `nproc`.
- 1-min ≫ 15-min → problem is **ramping up now**; 1-min ≪ 15-min → recovering.
- **Linux load includes tasks in uninterruptible I/O wait (`D` state)** — high load
  with idle CPUs means disk/NFS wait, not CPU. Check `vmstat` `wa` and `ps` for D-state.

```bash
nproc                          # number of CPUs
cat /proc/loadavg              # raw values + running/total tasks
ps -eo state,pid,cmd | grep '^D'   # who is stuck in uninterruptible sleep
```

---

## 2. Live process view

### `top` — always available
```bash
top                            # then interactively:
                               #   1 = per-CPU view, M = sort by memory,
                               #   P = sort by CPU, c = full command, k = kill
top -b -n 1 | head -20         # batch mode (for scripts/logs)
top -H -p 1234                 # threads of one process (find hot thread)
```
Header line to read carefully:
```
%Cpu(s): 12.3 us,  4.2 sy,  0.0 ni, 43.1 id, 39.6 wa,  0.0 hi,  0.8 si,  0.0 st
```
| Field | Meaning | High value suggests |
|-------|---------|---------------------|
| `us` | user code | app burning CPU (busy loop, GC, crypto) |
| `sy` | kernel code | syscall storm, context switches, bad driver |
| `wa` | I/O wait | disk/NFS bottleneck → see 01-storage-disk.md |
| `id` | idle | (good) |
| `si` | soft interrupts | network packet storm |
| `st` | steal | **VM not getting CPU from hypervisor** — on AWS: undersized/burstable instance out of CPU credits |

### `htop` — nicer top (if installed)
```bash
htop                           # F5 tree view, F6 sort, F4 filter
```

### `ps` — snapshots & sorting
```bash
ps aux --sort=-%cpu | head     # top CPU consumers
ps aux --sort=-%mem | head     # top memory consumers
ps -eLf | wc -l                # total thread count
ps -o pid,ppid,state,wchan,cmd -p 1234    # what a stuck process is waiting on
```

---

## 3. Per-CPU and per-process breakdown (sysstat package)

### `mpstat` — per-core utilization
```bash
mpstat -P ALL 1                # every core, 1s interval
```
One core at 100% while others idle = **single-threaded bottleneck** (or IRQs
pinned to one core — check `/proc/interrupts`).

### `pidstat` — per-process over time (better than eyeballing top)
```bash
pidstat 1                      # per-process CPU every second
pidstat -d 1                   # disk I/O per process
pidstat -r 1                   # memory (page faults, RSS) per process
pidstat -w 1                   # context switches per process (cswch = voluntary,
                               # nvcswch = involuntary → fighting for CPU)
pidstat -t -p 1234 1           # per-thread within one process
```

### `vmstat` — system-wide vitals in one line per second
```bash
vmstat 1
```
```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
12  0      0 823400  90120 5312000   0    0     3    88 4800 9200 85 10  3  2  0
```
- `r` > CPU count sustained → run-queue saturation (need more CPU or fewer tasks)
- `b` → processes blocked on I/O
- `si/so` ≠ 0 → **swapping** → memory problem, see 04-memory.md
- `cs` very high → context-switch storm (too many threads, lock contention)

### `sar` — history! What happened at 3am? (sysstat collector)
```bash
sar -u                          # today's CPU history (10-min samples)
sar -u -f /var/log/sa/sa07      # CPU for the 7th of the month
sar -q                          # load average history
sar -r                          # memory history
sar -b                          # I/O history
sar -n DEV                      # network history
sar -u -s 02:30:00 -e 04:00:00  # zoom into a time window
```
If sar has no data: enable the collector — `systemctl enable --now sysstat`.

---

## 4. Digging deeper

### `perf` — where is the CPU time actually going?
```bash
perf top                        # live: hottest functions system-wide
perf top -p 1234                # hottest functions of one process
perf record -g -p 1234 -- sleep 30   # sample 30s with call graphs
perf report                     # analyze the recording
perf stat -p 1234 -- sleep 10   # IPC, cache misses, branch misses
```

### `strace` — is it stuck in a syscall? (big slowdown — avoid on hot prod paths)
```bash
strace -c -p 1234               # syscall count/time summary (Ctrl-C to stop)
strace -f -tt -T -p 1234        # live syscalls with timestamps and durations
```
Common findings: thousands of `stat()`/`open()` calls (config re-read loop),
`futex` waits (lock contention), blocking `connect()`/`read()` (slow dependency).

### CPU throttling & frequency
```bash
lscpu                                        # topology, max MHz
grep MHz /proc/cpuinfo                       # current per-core frequency
turbostat --quiet --interval 5               # freq + C-states (on-prem thermal issues)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor   # "powersave" can hurt
```

### cgroup limits (containers/systemd slices)
A process can be slow with the *host* idle because its **cgroup** is throttled:
```bash
cat /sys/fs/cgroup/system.slice/app.service/cpu.max         # cgroup v2 quota
cat /sys/fs/cgroup/system.slice/app.service/cpu.stat        # nr_throttled ↑ = hitting quota
systemctl show app.service | grep -i cpu
```
In Kubernetes this shows up as CPU throttling from `limits.cpu` — see 15-kubernetes.md.

---

## Decision tree: "the box is slow"

```
uptime: load high?
├── no  → not a CPU issue → check memory (04), disk latency (01), network (02), app logs
└── yes → top:
    ├── high %us  → ps --sort=-%cpu → profile the top process (perf top -p)
    ├── high %sy  → strace -c the busy process; check cs in vmstat
    ├── high %wa  → iostat -xz 1 → storage bottleneck (01-storage-disk.md)
    ├── high %st  → hypervisor starving you (AWS: t2/t3 CPU credits! CloudWatch CPUCreditBalance)
    └── all idle but load high → D-state processes → NFS/disk hang
```
