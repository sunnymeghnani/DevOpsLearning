# 04 — Memory Troubleshooting

Typical symptoms: processes killed randomly (OOM), swapping/thrashing, "cannot
allocate memory", app latency spikes, memory "disappearing".

---

## 1. The overview

### `free` — first look
```bash
free -h                        # human readable
free -h -s 5                   # refresh every 5s
```
```
$ free -h
              total   used   free  shared  buff/cache  available
Mem:           15Gi   9.2Gi  400Mi  120Mi       5.9Gi      5.4Gi
Swap:         2.0Gi   1.8Gi  200Mi
```
**The #1 misconception:** low `free` is normal — Linux uses spare RAM as
disk cache (`buff/cache`) and gives it back on demand.
**Look at `available`, not `free`.**
Real trouble signs: `available` near 0, and **swap heavily used while `si/so`
in vmstat is nonzero** (active swapping, not just old pages parked in swap).

### `vmstat` — is swapping happening NOW?
```bash
vmstat 1 10
```
`si` (swap-in) / `so` (swap-out) columns nonzero and sustained = thrashing.
Swap *usage* alone (from `free`) is not a problem; swap *activity* is.

---

## 2. Who is using the memory?

```bash
ps aux --sort=-%mem | head -15          # top consumers by RSS
top                                     # then press M
smem -tk                                # PSS view — fair shared-memory accounting
pmap -x 1234 | tail -5                  # memory map + total for one process
cat /proc/1234/status | grep -E "Vm|Rss" # VmRSS (real), VmSwap, VmSize (virtual)
```
Notes:

- `VIRT`/`VmSize` is address space, often huge and harmless (JVM!). **RSS** is real.
- For many forked workers sharing memory (nginx, postgres), `smem` PSS is the
  honest number; summing RSS double-counts shared pages.

Watch a suspected leak:
```bash
while true; do ps -o rss= -p 1234; sleep 60; done   # RSS steadily climbing = leak
pidstat -r -p 1234 60                                # same, with page faults
```

---

## 3. The OOM killer — "my process vanished"

When memory truly runs out, the kernel kills the process with the highest
oom_score. The evidence is in the kernel log:

```bash
dmesg -T | grep -iE "out of memory|oom|killed process"
journalctl -k | grep -i oom
```
```
[Tue Aug  4 03:12:44 2026] Out of memory: Killed process 2134 (java)
  total-vm:18321412kB, anon-rss:14873220kB
```
That's your smoking gun — the app didn't "crash", the kernel killed it.

Inspect / influence OOM choices:
```bash
cat /proc/1234/oom_score               # likelihood of being chosen
echo -1000 > /proc/1234/oom_score_adj  # protect a critical process (careful)
```
systemd services: `OOMScoreAdjust=`, and check `systemctl status` — it will say
`oom-kill` / `Result: oom-kill` for killed units.

In containers/K8s, OOMKilled with exit code **137** = the *cgroup* limit was hit,
even if the host had free memory — see 14/15.

---

## 4. Deep inspection

### `/proc/meminfo` — the source of truth
```bash
cat /proc/meminfo
grep -E "MemAvailable|Dirty|Writeback|Slab|Shmem|HugePages|CommitLimit|Committed_AS" /proc/meminfo
```
Useful fields:

- `Dirty`/`Writeback` high & stuck → storage can't keep up with writes
- `Shmem` big → tmpfs! (`df -h /dev/shm`, `/tmp` on some distros, containers)
  Files in tmpfs eat RAM and don't show in `ps`.
- `Committed_AS` vs `CommitLimit` → overcommit pressure

### Slab — kernel object memory ("missing" memory)
```bash
slabtop -o | head -15          # biggest kernel caches (dentry/inode caches often huge)
cat /proc/meminfo | grep Slab
```
Huge dentry cache from workloads that scan millions of files is normal and
reclaimable; it drains under pressure.

### Drop caches (diagnostic only — brief perf hit, safe otherwise)
```bash
sync; echo 3 > /proc/sys/vm/drop_caches   # confirm cache is what's using RAM
```

### Swap configuration
```bash
swapon --show                  # active swap devices/files
sysctl vm.swappiness           # 0..100 tendency to swap (60 default; DBs often 1-10)
# add emergency swap (temporary relief on a swapless box):
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
```

### Huge pages / NUMA (databases, big-memory hosts)
```bash
grep Huge /proc/meminfo         # HugePages allocated vs used (reserved = unusable by others!)
numactl --hardware              # NUMA nodes and free memory per node
numastat -m                     # per-node memory stats
```

---

## Decision tree: "memory problems"

```
Process disappeared?        → dmesg -T | grep -i oom   → found: reduce usage/add RAM/limit others
                                                       → not found: app crashed on its own → its logs
Box slow + high wa/si/so?   → thrashing → ps --sort=-%mem → stop/limit the hog; check swappiness
"Cannot allocate memory"?   → free -h (available≈0?) → also check ulimit -v and overcommit
                            → fork failing with free RAM? → pid limit: cat /proc/sys/kernel/pid_max,
                              threads: ulimit -u, cgroup pids.max
Memory "missing"            → tmpfs? df -h | grep tmpfs → slab? slabtop → hugepages? grep Huge /proc/meminfo
(ps doesn't add up)?
```
