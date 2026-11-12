# Processes, CPU & memory

These commands answer "where do the time and the memory go?", from the whole box down to one line of code. Work from cheap and wide to narrow: load and core count (`uptime`, `nproc`), the per-second split of CPU, memory and I/O (`vmstat`, `mpstat`, `free`), the busy process or service (`pidstat`, `ps`, `systemd-cgtop`), and only then a tracer or profiler on one process (`strace`, `perf`, `py-spy`, `jstack`), which you keep to seconds. For "it was slow at 02:00 last night", only recorded history (`sar`, `atop`) can answer.

| If you would reach for | Prefer | Because |
|---|---|---|
| `top` | `vmstat 1 5`, `mpstat -P ALL 1 5`, `pidstat 1 5` | one line per second that separates CPU work, iowait, steal and swapping, for the box, each core and each process |
| `uptime` alone | `uptime` with `nproc`, then `vmstat 1 5` (`r` versus `b`) | Linux load also counts tasks stuck on disk or NFS (state D), so high load does not prove a CPU problem |
| the `free` column of `free -h` | the `available` column, and `si`/`so` in `vmstat` | spare RAM is used as cache; available memory and swap traffic show real pressure |
| `ps aux --sort=-%cpu` for "busy now" | `pidstat 1` | ps `%CPU` is an average over the process's whole lifetime |
| summing RSS from `ps` | `smem -tk -s pss -r` | RSS counts a shared page in every process that maps it; PSS splits it fairly |
| `ps aux | grep app`, then `kill -9` | `pgrep -af app`, then `kill PID` | no self-match, and TERM lets the process flush data and release locks |
| `top` the morning after | `sar -q -f FILE`, `atopsar -r FILE -O` | live tools cannot show what happened at 02:00 |
| `strace -p PID` left running | `strace -c -f -p PID` for 10 seconds, or `perf top -p PID` | strace stops the target at every system call; perf samples it at low cost |

### uptime / nproc — is the box overloaded, compared with how many CPUs it has?
Match: uptime, nproc
Instead of: —
Safety: read-only

**In one line:** `uptime` prints how long the box has been up and the 1-, 5- and 15-minute load averages; `nproc` prints how many CPUs this process may use, the number to compare the load with.

**Read the command:** `uptime; nproc`

| Part | Meaning |
|---|---|
| `uptime` | time, time since boot, logged-in users, three load averages |
| `;` | then run the next command |
| `nproc` | CPUs available to this process (respects CPU affinity and cpusets) |
| `uptime -s` | boot time as a date: "did it reboot last night?" |
| `nproc --all` | every installed CPU, ignoring affinity |

**What the output tells you:**

```
 10:42:17 up 23 days,  4:11,  2 users,  load average: 7.82, 5.10, 2.31
4
```

Load counts tasks that are **running, waiting for a CPU, or in uninterruptible sleep (state D, usually disk or NFS I/O)**, averaged with decay over 1, 5 and 15 minutes. 7.82 on 4 CPUs is about two tasks per CPU. A 1-minute value far above the 15-minute one means the problem started minutes ago and is growing; the reverse means it is fading.

**Why it is effective:** it costs two seconds and tells you whether the problem is happening now and whether it is getting worse, before you open any other tool.

**Trap:** load average is not CPU usage. Because D-state tasks count, load 25 with idle CPUs is what a box waiting on a dead NFS server looks like; `vmstat 1 5` splits it into `r` (runnable) and `b` (blocked). In a container limited with `--cpus` (a CFS quota), `nproc` still prints the host's CPU count, because a quota is not an affinity mask, and apps that size their worker pools from it overshoot. A 30-second spike barely moves the 15-minute figure.

**Next step:** load above `nproc` → `vmstat 1 5`: high `r` → CPU (`mpstat`, `pidstat`); high `b` → D-state tasks (`ps -eo state,pid,wchan:32,cmd`), then disk or NFS. Load low but users complain → the box is waiting on something else (database, upstream API, DNS).

### vmstat — CPU, memory, swap and I/O pressure, one line per second
Match: vmstat
Instead of: top, free
Safety: read-only

**In one line:** `vmstat` prints one line per interval with the run queue, blocked tasks, memory, swap traffic, disk I/O and the CPU split: in five seconds you know whether the box is short of CPU, memory or disk.

**Read the command:** `vmstat 1 5`

| Part | Meaning |
|---|---|
| `1` | one report per second |
| `5` | five reports, then exit |
| `-w` | wide columns, for large memory figures |

**What the output tells you:**

```
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  4 1669120 145620   2104 1008840  41  112  2210   960  612 1180 14  7 48 31  0
 5  3 1672704 139876   2104 1006120 1844 5212 9180  6412 2311 3920 18 11 33 38  0
```

**Ignore the first data line:** its rates are averages since boot. `r` = tasks running or waiting for a CPU (compare with `nproc`); `b` = tasks blocked in uninterruptible sleep (state D). `si`/`so` = KiB per second swapped in and out: non-zero for several seconds means the working set no longer fits in RAM. `bi`/`bo` = KiB per second read from and written to disk. `us sy id wa st` = CPU time in applications, in the kernel, idle, idle with I/O outstanding, and stolen by the hypervisor.

**Why it is effective:** it sorts the usual causes at once: `r` well above the CPU count with `id` near 0 is CPU; `b` and `wa` high with `si`/`so` at 0 is disk or NFS; busy `si`/`so` is memory, even when the symptom looks like slow disks.

**Compared with `top`:** top shows the same CPU split and names processes, but has no blocked-task count or swap traffic. **Compared with `free`:** free shows swap *used*; only `si`/`so` show swapping *now*.

**Trap:** `wa` is idle time averaged over all CPUs: on 32 cores one thread stuck on a slow disk barely moves it, so a low `wa` does not clear the disks (`iostat -xz 1` does). A large `swpd` with `si`/`so` at 0 is old pages parked in swap: harmless.

**Next step:** `r` high → `mpstat -P ALL 1 5`, `pidstat 1 5`. `b` or `wa` high → `iostat -xz 1`, then the D-state tasks with `ps`. `si`/`so` → `free -h`, then who holds the memory. `st` above 5–10 → cloud CPU credits or an overcommitted host.

### mpstat — are all cores busy, or is one pinned?
Match: mpstat
Instead of: top
Safety: read-only

**In one line:** `mpstat` prints the CPU split for each core separately, every second, so one saturated core, a core busy with interrupts, or steal on a vCPU stands out instead of being averaged away.

**Read the command:** `mpstat -P ALL 1 5`

| Part | Meaning |
|---|---|
| `-P ALL` | one line per CPU plus the `all` average (without it: only `all`) |
| `1` | one report per second |
| `5` | five reports, then an `Average:` block |

**What the output tells you:**

```
11:02:01     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
11:02:02     all   26.10    0.00    0.75    0.00    0.00    0.25    0.00    0.00    0.00   72.90
11:02:02       0    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00   97.00
11:02:02       2  100.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00
```

The average says 26% busy, but CPU 2 runs at 100% `%usr` (CPUs 1 and 3 idle like CPU 0): one single-threaded process such as a Node.js main thread, Redis, a PHP cron script or `gzip` is the limit, and more cores will not help it. `%iowait` = idle with I/O outstanding; `%irq`/`%soft` = interrupt and softirq work (network packets, disk completions); `%steal` = your vCPU wanted to run but the hypervisor ran something else.

**Why it is effective:** the cases need opposite fixes. All cores busy: less work or more CPU. One pinned core: make that thread faster or split its work. One core high in `%soft`: spread the interrupts (NIC queues, irqbalance).

**Compared with `top`:** top's `%Cpu(s)` line is the `all` row only; its per-CPU view (key `1`) is interactive and hard to log second by second.

**Trap:** the scheduler moves threads between cores, so one busy thread can show as two half-busy cores; `pidstat -t -p PID 1` settles it. On a burstable cloud instance (AWS T family) that has used up its CPU credits, the cap shows as `%steal`.

**Next step:** one core at 100% `%usr` → `top -H -p PID` or `pidstat -t -p PID 1` for the thread. One core high in `%soft` → `/proc/interrupts` and the NIC queues. High `%steal` → CPU credits or the hypervisor team. All cores busy → `pidstat 1` for names.

### pidstat — which process (or thread) uses the CPU, disk or memory, second by second
Match: pidstat
Instead of: top, ps aux --sort=-%cpu
Safety: read-only · run it as root to see disk I/O (-d) of other users' processes

**In one line:** `pidstat` prints per-process statistics for every interval, listing only the processes active in it: CPU by default, disk I/O with `-d`, memory and page faults with `-r`, context switches with `-w`, threads with `-t`.

**Read the command:** `pidstat -l 1 3`

| Part | Meaning |
|---|---|
| `-l` | show the full command line (tells two java apps or PHP pools apart) |
| `1 3` | 1-second interval, 3 reports, then `Average:` lines |
| `-d` | disk: kB read and written per second, `iodelay` (clock ticks waiting for block I/O) |
| `-r` | memory: minor and major page faults per second, VSZ, RSS |
| `-w` | context switches: `cswch/s` voluntary, `nvcswch/s` involuntary |
| `-t -p 1234` | every thread (TID) of process 1234 |

**What the output tells you:**

```
10:42:40   UID   PID   %usr %system  %guest   %wait    %CPU   CPU  Command
10:42:41     0    97   0.00   18.81    0.00    0.00   18.81     2  kswapd0
10:42:41  1001  2817  31.68    4.95    0.00    6.93   36.63     1  java -jar /app/app.jar
```

`%CPU` is a share of **one** CPU: a multi-threaded process can show 250%. `%wait` (recent versions) is time the task was runnable but waiting for a CPU, not I/O wait. Kernel threads point at a subsystem: `kswapd0` = memory reclaim, `ksoftirqd/N` = interrupts, `jbd2` = filesystem journal.

**Why it is effective:** it names every busy process each second, as plain lines you can paste into a ticket, and `-d` gives disk I/O per process, which `top` does not show at all.

**Compared with `top`:** the same CPU figures, but interactive and one screen at a time. **Compared with `ps aux --sort=-%cpu`:** ps `%CPU` is a lifetime average, so a process that started spinning a minute ago looks idle.

**Trap:** processes that start and exit within one interval (fork storms, health checks) never appear: use `execsnoop-bpfcc`. `iodelay` stays 0 while the kernel's delay accounting (`kernel.task_delayacct`) is off. High `cswch/s` with little CPU means waiting (locks, chatty I/O); high `nvcswch/s` means fighting for a CPU.

**Next step:** one process dominates → `pidstat -t -p PID 1`, then `perf top -p PID` or the runtime's profiler. Heavy disk I/O → `iostat -xz 1` for the device. RSS climbing → `pidstat -r -p PID 60` for an hour: a leak keeps growing, a warm-up levels off.

### top / htop — what is busy right now, on one screen
Match: top, htop
Instead of: —
Safety: read-only (the k key in top and F9 in htop send signals)

**In one line:** `top` refreshes a live process table under a summary header (load, CPU split, memory, swap); `htop` is the friendlier version with per-core bars, a tree view and mouse support.

**Read the command:** `top -b -n 1 -o %CPU`

| Part | Meaning |
|---|---|
| `-b` | batch mode: plain text for `head`, a file or a ticket |
| `-n 1` | one refresh, then exit |
| `-o %CPU` | sort by this field (`%MEM`, `RES`, `TIME+` also work) |
| `-H -p 1234` | the threads of process 1234 instead of processes |
| keys `1` `P` `M` `c` | per-CPU lines, sort by CPU, by memory, full command lines |
| `top -o cpu -l 1` | macOS: sort by CPU, one sample |
| `htop` | F5 tree, F6 sort, F4 filter, `H` hide or show threads |

**What the output tells you:**

```
top - 10:43:31 up 23 days,  4:12,  2 users,  load average: 7.91, 5.44, 2.60
%Cpu(s): 17.1 us, 10.2 sy,  0.0 ni, 34.9 id, 37.3 wa,  0.0 hi,  0.5 si,  0.0 st
MiB Swap:   2048.0 total,    417.9 free,   1630.1 used.    811.9 avail Mem
    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
   2817 1001      20   0 7612344   4.9g  21480 S  35.8  63.4 412:51.07 java
  41522 www-data  20   0  412880  61204  31120 D   7.9   0.8   0:41.13 apache2
```

(Lines trimmed.) `us` application code, `sy` kernel, `wa` idle waiting for I/O, `hi`/`si` interrupt work, `st` CPU time the hypervisor gave to someone else. `avail Mem` is the memory headroom. `RES` is real RAM; `VIRT` is mostly reserved address space. `S` = `D`: stuck in the kernel waiting for I/O.

**Why it is effective:** it is everywhere and shows load, CPU split, memory and the top processes together, so it confirms what the per-second tools found and catches surprises: zombies, a forgotten `tar`, a D-state worker.

**Trap:** process `%CPU` is per core (400% is possible on 4 cores), but the `%Cpu(s)` header averages all cores: one pinned core out of 16 looks like 6% busy until you press `1`. htop shows threads by default, so one JVM fills the screen with copies of the same memory figure.

**Next step:** high `us` → `pidstat 1`, then `perf top -p PID`. High `wa` or `D` processes → `iostat -xz 1`, `ps -eo state,pid,wchan:32,cmd`. High `st` → steal. Memory → `free -h`, then `vmstat` `si`/`so`.

### ps — which processes exist, in what state, holding how much memory
Match: ps
Instead of: —
Safety: read-only

**In one line:** `ps` takes a one-off snapshot of the process table: who runs what, as which user, in which state, with how much real memory, in columns you can sort, filter and script.

**Read the command:** `ps aux --sort=-%mem`

| Part | Meaning |
|---|---|
| `aux` | BSD-style options, no dash: `a` every user's processes, `x` also those without a terminal (daemons), `u` user-oriented columns |
| `--sort=-%mem` | sort by %MEM, largest first (`-%cpu`, `-rss` work too) |
| `-eo state,pid,ppid,wchan:32,cmd` | every process (`-e`) with your own columns (`-o`); WCHAN = the kernel function a sleeping task waits in |
| `-o rss= -p 1234` | one PID; `=` drops the header, handy in scripts |
| `-eLf` | one line per thread, full format |

**What the output tells you:**

```
USER       PID %CPU %MEM     VSZ     RSS TTY  STAT START    TIME COMMAND
1001      2817 13.4 63.2 7612344 5138212 ?    Ssl  Oct01  412:51 java -Xms6g -Xmx6g -jar /app/app.jar
root      1931  0.2  3.1 1302144  251880 ?    Ssl  Sep10   58:12 node /app/server.js
...
www-data 41522  0.9  0.8  412880   61204 ?    D    09:27    0:41 /usr/sbin/apache2 -k start
```

`RSS` (KiB) is memory actually in RAM; `VSZ` is all the address space mapped, including memory reserved but never used, and is rarely meaningful. `STAT`: `R` running or waiting for a CPU, `S` sleeping (normal), `D` uninterruptible sleep in the kernel, usually disk or NFS I/O, `Z` zombie, `T` stopped; then `s` session leader, `l` multi-threaded, `+` foreground.

**Why it is effective:** it is on every box and its custom columns answer exact questions: `ps -eo state,pid,wchan:32,cmd` lists every D-state task with the kernel function it waits in, which explains "load 20, CPUs idle" in one screen.

**Trap:** `%CPU` is CPU time divided by the process's whole lifetime, not current usage: a process that started spinning a minute ago after days idle shows 1% (use `pidstat 1` or `top`). RSS counts shared pages in every process that maps them, so summing RSS overstates usage (use `smem`). A `D` task usually ignores even `kill -9` until its I/O returns.

**Next step:** large RSS → `pidstat -r -p PID 60` to see whether it grows. Many `D` tasks → group them by WCHAN: disk → `iostat -xz 1`, NFS → the server. Zombie → its parent (`ps -o ppid= -p PID`). Unknown process → `pstree -aps PID`, `ps -o unit= -p PID`.

### pstree — who started this process, and what did it start?
Match: pstree
Instead of: ps -ef (following PPIDs by hand)
Safety: read-only

**In one line:** `pstree` draws processes as a family tree, so you see at once which service, cron job, login session or container a process belongs to and what it spawned.

**Read the command:** `pstree -aps 1343`

| Part | Meaning |
|---|---|
| `-a` | show each process's command-line arguments |
| `-p` | show PIDs |
| `-s` | show the parents of the given process, up to PID 1 |
| `1343` | start from this PID instead of the whole tree |
| `-u` | mark where the user changes (root master, `www-data` workers) |

**What the output tells you:**

```
systemd,1
  └─apache2,1123 -k start
      └─apache2,1343 -k start
          └─sh,51120 -c /usr/local/bin/report.sh
```

PID 1343 is an Apache worker under the master 1123, which systemd started: it belongs to `apache2.service`. Its child `sh` was launched by the web application itself (a CGI script or `exec()` from PHP). Threads, when shown, appear in curly braces.

**Why it is effective:** "who owns this?" is the first question about any unknown process or port, and the chain of parents answers it: under `containerd-shim` it is a container, under `cron` a scheduled job, under `sshd` and `bash` someone's login session.

**Compared with `ps -ef`:** ps shows the PPID column, so you can walk up the chain one PID at a time; pstree does the walk and draws it.

**Trap:** when a parent dies, its children are re-parented to PID 1 (or a subreaper such as `systemd --user`), so a branch hanging from `systemd` does not prove systemd started it; ask `ps -o unit= -p PID` or `systemctl status PID`. Killing a parent does not kill its children either.

**Next step:** container shim → `docker ps` or `crictl ps` to name the container. `cron` → the crontab or timer. Login session → `who`, `loginctl`. Then `lsof -p PID` for what it holds open.

### pgrep / pkill — find, then signal, processes by name, user or command line
Match: pgrep, pkill, pidof
Instead of: ps aux | grep
Safety: pgrep is read-only · pkill changes state: it signals every matching process (TERM by default)

**In one line:** `pgrep` prints the PIDs of processes whose name, full command line or owner matches a pattern; `pkill` sends a signal to exactly the same set, so preview with `pgrep -a` first.

**Read the command:** `pgrep -a -f 'python3 -m http.server'`

| Part | Meaning |
|---|---|
| `-a` | print the full command line next to each PID |
| `-f` | match against the whole command line, not only the process name |
| `'python3 -m http.server'` | the pattern: an extended regular expression, quoted to stay one word |
| `-x` | the name must match exactly (`pkill -x yes` spares `yes-server`) |
| `-u appuser` | only processes of this user |
| `pkill -INT -x tcpdump` | send SIGINT (like Ctrl-C), so tcpdump flushes its capture file |
| `pkill -TERM -x stress-ng` | send TERM, which is also the default |

**What the output tells you:**

```
48211 python3 -m http.server 8000 --bind 127.0.0.1 --directory /var/tmp/www
```

One line per match. Exit status 0 means at least one match and 1 means none, so `pgrep -x app >/dev/null || echo down` is a quick check in scripts.

**Why it is effective:** it never matches itself, it filters by user and exact name, and the same pattern drives `pkill`, so what you previewed is what you signal.

**Compared with `ps aux | grep`:** that works everywhere and shows every column, but it matches its own `grep` line, matches the text in any column (a user name, a path), and needs `awk` to extract PIDs.

**Trap:** without `-f`, matching uses the kernel's process name, which is cut to 15 characters, so a pattern for a longer name matches nothing (pgrep warns). With `-f`, the regex matches anywhere: `pkill -f app` also hits `tail -f /var/log/app.log` and someone's `vim app.conf`. A too-loose `pkill` stops production processes.

**Next step:** several matches → `pstree -aps PID` to see which service each belongs to. A systemd service → `systemctl stop UNIT`, not `pkill`, or systemd may restart it. No match but the program runs → try `-f`: scripts run as `python3` or `java`, not under their own name. Related: `pidof java` prints the PIDs of processes whose program name is exactly `java`, on one line; unlike `pgrep -f` it never matches arguments.

### kill / killall — ask a process to stop, reload, pause or dump its threads
Match: kill, killall
Instead of: kill -9 as the first move
Safety: changes state: delivers a signal · -9 ends the process with no cleanup · -0 only checks

**In one line:** `kill` sends a signal to a PID (TERM unless you name another): the program decides what TERM, HUP or QUIT mean, while KILL and STOP are enforced by the kernel. `killall` does the same by process name.

**Read the command:** `kill -TERM PID`

| Part | Meaning |
|---|---|
| `-TERM` (15, the default) | "please exit": the process can flush data, release locks and remove its PID file |
| `-9` / `-KILL` | the kernel ends it at once, with no cleanup; exit code 137 |
| `-HUP` (1) | many daemons reload their configuration |
| `-0` | sends nothing: succeeds if the PID exists and you may signal it |
| `-STOP` / `-CONT` | freeze / resume a runaway without killing it |
| `-3` (QUIT) | a JVM prints a thread dump to its stdout and keeps running |
| `killall -v java` | every process named exactly `java`; `-v` reports each one signalled |

**What the output tells you:** usually nothing, so check the effect: `kill -0 PID && echo alive`. A process that died from a signal reports exit code 128 + the signal number: 143 after TERM, 137 after KILL (also what an OOM kill leaves). On macOS, `sudo killall -HUP mDNSResponder` flushes the DNS cache.

**Why it is effective:** signals are the process's own interface: TERM for a clean shutdown, HUP for a reload without a restart, QUIT for a Java thread dump.

**Compared with `kill -9`:** KILL always works on a process that is not stuck in the kernel, which is why people start with it. It also skips every cleanup handler: half-written files, stale lock and PID files, databases that need recovery, and lost evidence (take a `jstack` or `py-spy dump` first).

**Trap:** HUP or QUIT sent to a program that does not handle them **terminates** it (QUIT also dumps core). A `D`-state task usually ignores even KILL until its I/O returns; a zombie is already dead, so the fix is its parent. `killall java` hits every Java process on the host, including other teams' services. For a systemd service use `systemctl stop` or `reload`, or systemd may restart what you killed.

**Next step:** still running after TERM → wait 10–30 s, check `ps -o stat= -p PID` (D? Z?), then `-9`. Reload ignored → check the unit's `ExecReload=`. Zombie → `ps -o ppid= -p PID`, then fix or restart the parent.

### free — how much memory is really left?
Match: free
Instead of: —
Safety: read-only

**In one line:** `free` shows RAM and swap totals from `/proc/meminfo`; the column that answers "is memory short?" is `available`, not `free`.

**Read the command:** `free -h`

| Part | Meaning |
|---|---|
| `-h` | human-readable units (Mi, Gi) |
| `-m` | MiB: easier to compare over time and in scripts |
| `-s 5` | repeat every 5 seconds |
| `-c 3` | stop after 3 reports (used with `-s`) |

**What the output tells you:**

```
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       6.6Gi       142Mi        45Mi       986Mi       812Mi
Swap:          2.0Gi       1.6Gi       417Mi
```

`free` is RAM nobody uses; low is normal, because Linux fills spare RAM with page cache. `buff/cache` is file data kept in RAM, mostly reclaimable. `available` is the kernel's estimate of what programs can still get **without swapping** (roughly free plus the cache that can be dropped): 812 Mi of 7.8 Gi, about 10%, is tight. `shared` is tmpfs and shared memory: it counts against RAM and cannot be dropped like cache.

**Why it is effective:** one line separates "RAM is full of cache, all fine" from "programs are running out", which the word "free" hides.

**Trap:** swap *used* is not swapping: idle pages can sit in swap for weeks. Only `vmstat 1 5` `si`/`so` (or `sar -W`) show swapping now. How `used` is computed differs between procps versions, so compare `available` across hosts, not `used`. Inside a container, `free` usually shows the **host's** memory, while the container's own limit (`memory.max`) is what triggers its OOM kill. A large `shared` usually means files in `/dev/shm` or another tmpfs.

**Next step:** `available` low and `si`/`so` busy → who holds memory (`ps -eo pid,rss,comm --sort=-rss`, `smem`, `systemd-cgtop -m`). `available` low but no process big enough → kernel memory (`slabtop`), tmpfs (`df -h -t tmpfs`), huge pages (`grep Huge /proc/meminfo`). A process vanished → `journalctl -k | grep -i oom`.

### smem / slabtop — whose memory is it really: shared pages and kernel caches
Match: smem, slabtop, pmap
Instead of: ps aux --sort=-%mem (adding up RSS)
Safety: read-only · needs root to read every process's smaps and /proc/slabinfo

**In one line:** `smem` reports each process's PSS (shared pages divided between the processes that share them) and USS (memory only that process uses); `slabtop` lists the kernel's own object caches, memory that belongs to no process.

**Read the command:** `smem -tk -s pss -r`

| Part | Meaning |
|---|---|
| `-t` | add a totals line |
| `-k` | show unit suffixes (K, M, G) |
| `-s pss` | sort by PSS |
| `-r` | reverse the sort: biggest first |
| `-P apache2` | only processes whose command line matches this regex |
| `slabtop -o -s c` | print the slab caches once (`-o`), sorted by cache size (`-s c`) |

**What the output tells you:**

```
  PID User     Command                        Swap      USS      PSS      RSS
 2817 1001     java -Xms6g -Xmx6g -jar /app   1.4G     4.8G     4.8G     4.9G
 1831 www-data /usr/sbin/apache2 -k start        0    18.1M    24.6M    59.6M
-------------------------------------------------------------------------------
  157 15                                      1.9G     6.0G     6.2G     7.4G
```

The Apache worker has 60 MB resident but only 18 MB of its own (USS): killing it frees 18 MB, not 60. Summed RSS (7.4G) overstates the real total (PSS 6.2G). In `slabtop`, a huge `dentry` or `ext4_inode_cache` comes from something that walked millions of files.

**Why it is effective:** forked servers (Apache prefork, PHP-FPM, PostgreSQL) share most of their pages, so RSS sums can claim more memory than the box has; PSS adds up honestly, and slabtop explains memory that no process list shows.

**Compared with `ps aux --sort=-%mem`:** ps ranks single processes correctly, is always installed, and is enough to find one obvious hog. It cannot separate shared from private pages and shows nothing of kernel memory.

**Trap:** smem reads `/proc/PID/smaps` for every process: slow on hosts with thousands of processes, and without root it sees only your own. slabtop does not say whether a cache can be reclaimed; `SReclaimable` versus `SUnreclaim` in `/proc/meminfo` does. Big reclaimable dentry and inode caches are normal and shrink under pressure; an `SUnreclaim` that keeps growing suggests a kernel or driver leak.

**Next step:** one process large in USS → watch it over time (`pidstat -r -p PID 60`). Growing `SUnreclaim` → kernel or driver update, vendor ticket. Still unexplained → tmpfs (`df -h -t tmpfs`) and huge pages. Related: `pmap -x PID` lists one process's mappings (heap, libraries, anonymous memory) with RSS and dirty kB for each; the last line is the total.

### sar — what did CPU, load and memory look like at 02:00 last night?
Match: sar
Instead of: top, uptime
Safety: read-only · history exists only if the sysstat collector is enabled

**In one line:** `sar` reads the history that the sysstat collector records (every 10 minutes by default) and prints CPU, load, memory, paging, disk and network figures for any past window; given an interval instead of a file, it samples live.

**Read the command:** `sar -u -f /var/log/sysstat/sa03 -s 10:00:00 -e 10:30:00`

| Part | Meaning |
|---|---|
| `-u` | CPU split: %user %nice %system %iowait %steal %idle |
| `-f /var/log/sysstat/sa03` | the file for day 03 of the month (RHEL: `/var/log/sa/saDD`); without `-f`: today |
| `-s 10:00:00 -e 10:30:00` | only records from 10:00 to 10:30 |
| `-q` | run queue, task count, load averages and `blocked` (D-state) tasks |
| `-n DEV` | packets and kB per second for each network interface |
| `1 3` (instead of `-f`) | live: three 1-second samples |

**What the output tells you:**

```
10:00:01   CPU   %user   %nice  %system  %iowait   %steal   %idle
10:10:01   all   12.41    0.00     4.02     1.10     0.00   82.47
10:20:01   all   71.88    0.00     9.75     0.42     0.00   17.95
10:30:01   all   69.10    0.00     8.91     0.50     0.00   21.49
Average:   all   51.13    0.00     7.56     0.67     0.00   40.64
```

Between 10:10 and 10:20 user CPU jumped from 12% to 72% and stayed: a CPU story, not disk (`%iowait` low) and not the hypervisor (`%steal` 0). Each line covers the 10 minutes ending at its timestamp.

**Why it is effective:** most "slow" tickets arrive after the fact. sar turns "slow around 10:15" into "CPU-bound from 10:10", or "disk-bound from 02:00 to 02:30", which tells you what to look for in cron jobs, timers, deploys and logs.

**Compared with `top` and `uptime`:** they show only now; uptime's 15-minute average is as far back as they reach.

**Trap:** each line is a 10-minute average, so a 2-minute spike is flattened into a small bump; shorten the collection interval where problems are short. If `sar` cannot open the file, collection was never enabled (check `systemctl is-enabled sysstat` and `ls /var/log/sysstat/`): enable it now so the next incident is recorded.

**Next step:** CPU high → which process (`atopsar -r FILE -O`, if atop was logging). `-q` shows `blocked` tasks → `sar -d -p` for disk latency in the same window. Memory → `sar -B` for page-cache thrash. Then line the start time up with `systemctl list-timers` and `journalctl --since`.

### atop / atopsar — which process was it, at a minute nobody was watching?
Match: atop, atopsar
Instead of: top, sar
Safety: read-only when reading logs · installing atop starts a service that writes a daily log under /var/log/atop/

**In one line:** atop records system **and per-process** CPU, memory and disk use at fixed intervals (every 10 minutes by default); `atop -r` replays a day's log sample by sample, and `atopsar` prints reports from it, such as the top three processes per sample.

**Read the command:** `atopsar -r /var/log/atop/atop_20261003 -b 02:00 -e 02:30 -D`

| Part | Meaning |
|---|---|
| `-r /var/log/atop/atop_20261003` | read the raw log of 3 October 2026 |
| `-b 02:00` | begin at 02:00 |
| `-e 02:30` | end at 02:30 |
| `-D` | top three processes by disk transfers, per sample |
| `-O` | top three processes by CPU, per sample |
| `atop -r FILE -b 02:00 -e 02:30` | interactive replay: `t`/`T` next/previous sample, `d` disk, `m` memory, `c` full command lines, `q` quit |

**What the output tells you:**

```
02:10:01   pid command   dsk% |  pid command   dsk% |  pid command  dsk%
02:10:01 10421 rsync      81% | 1290 postgres    9% |  398 jbd2/sdb  4%
02:20:01 10421 rsync      79% | 1290 postgres   11% |  398 jbd2/sdb  5%
```

`rsync` (PID 10421) caused about 80% of all disk activity in the slow window; PostgreSQL was the victim, not the cause.

**Why it is effective:** it names the culprit for a past minute, which no live tool can do. For a server that is "slow sometimes, at night", atop's per-process history ends the guessing.

**Compared with `sar`:** sar's history says *which resource* was busy at 02:10, not *which process*. **Compared with `top`:** top only shows now.

**Trap:** a 10-minute interval averages a 1-minute burst into a small bump; on hosts with short incidents lower `LOGINTERVAL` in `/etc/default/atop` (and expect bigger logs). The history starts when atop is installed, so it cannot explain last night unless it was already running: install it before you need it.

**Next step:** a known process → find what scheduled it (`systemctl list-timers`, crontabs, backup configs). An unknown one → its parent and unit (`pstree -aps PID` if it is still running). Only a resource, no process → `sar` for that device or interface.

### lscpu / numactl / numastat — how many CPUs, cores and NUMA nodes the box really has
Match: lscpu, numactl, numastat
Instead of: cat /proc/cpuinfo
Safety: read-only (numactl --hardware only reads; its binding options change how a program runs)

**In one line:** `lscpu` summarises the CPU topology (sockets, cores, threads per core, NUMA nodes, VM or bare metal); `numactl --hardware` and `numastat` show how memory is split between NUMA nodes and how much each node and process uses.

**Read the command:** `lscpu`

| Part | Meaning |
|---|---|
| `lscpu` | topology summary from /proc and /sys, no options needed |
| `numactl --hardware` | each NUMA node's CPUs, memory size, free memory, and the distances between nodes |
| `numastat -m` | /proc/meminfo-style figures per node |
| `numastat -p PID` | how one process's memory is spread over the nodes |

**What the output tells you:**

```
CPU(s):                  8
Thread(s) per core:      2
Core(s) per socket:      4
Socket(s):               1
NUMA node(s):            1
Hypervisor vendor:       KVM
Virtualization type:     full
```

These 8 CPUs are 4 cores with 2 hyper-threads each: the two threads of a core share its execution units, so 8 busy threads do not get 8 cores' worth of work. `Hypervisor vendor` means a VM: steal time matters, and clock speed and temperature belong to the host team. More than one NUMA node means each socket has its own, faster local memory.

**Why it is effective:** one screen answers questions you would otherwise reconstruct from hundreds of lines.

**Compared with `cat /proc/cpuinfo`:** cpuinfo lists every logical CPU with its flags and current clock, so you have to count `physical id` and `core id` values by hand to get the topology. It is still the place to check a single CPU flag.

**Trap:** on a two-socket server `numactl --hardware` can show node 0 with 1 GB free and node 1 with 40 GB free: a process bound to node 0 reclaims and swaps while half the RAM sits idle, and `free` shows only the total. A small VM has one node; there NUMA is not your problem.

**Next step:** VM → `mpstat -P ALL 1 5` for `%steal`. Several nodes, one nearly full → `numastat -p PID` for the database or JVM, then check `zone_reclaim_mode` and any `numactl` binding. Bare metal with a low clock → `turbostat`.

### turbostat / cpupower — is the CPU running at its rated speed?
Match: turbostat, cpupower
Instead of: grep MHz /proc/cpuinfo
Safety: turbostat needs root (reads CPU model-specific registers) · cpupower frequency-set changes state: the frequency governor, until reboot

**In one line:** `turbostat` measures how busy each CPU is, the clock it actually ran at while busy, the package temperature and power; `cpupower` shows and sets the frequency driver and governor. Both are for bare metal: inside most VMs there is nothing to read.

**Read the command:** `turbostat --quiet --show Busy%,Bzy_MHz,PkgTmp,PkgWatt --interval 5`

| Part | Meaning |
|---|---|
| `--quiet` | skip the long hardware description at start-up |
| `--show Busy%,Bzy_MHz,PkgTmp,PkgWatt` | only these columns: % of time not idle, average MHz while busy, package °C, package watts |
| `--interval 5` | one report every 5 seconds |
| `cpupower frequency-info` | driver, available governors, current policy and frequency |
| `cpupower frequency-set -g performance` | switch every CPU to the `performance` governor (`-g powersave` to go back) |

**What the output tells you:**

```
Busy%   Bzy_MHz PkgTmp  PkgWatt
97.12   1197    98      61.20
```

97% busy at only 1.2 GHz on a CPU rated at 2.9 GHz, at 98 °C: thermal throttling. Everything CPU-bound takes about 2.4 times longer, and no software change fixes it.

**Why it is effective:** CPU-percentage tools count time, not work: a core at 1.2 GHz and one at 2.9 GHz both show 100%. Only the busy clock and the temperature show that the same 100% does less than half the work.

**Compared with `grep MHz /proc/cpuinfo`:** cpuinfo gives an instant snapshot of each core's clock, which jumps with load and idle states; it says nothing about how busy the core was, how hot, or at what power.

**Trap:** with the `intel_pstate` driver, the `powersave` governor is normal and still boosts under load; with `acpi-cpufreq`, `powersave` pins the lowest frequency, a real problem. A BIOS power profile can cap the clock whatever the governor says. `frequency-set` does not survive a reboot; make it permanent only once you know the cause.

**Next step:** hot package and throttle messages in `dmesg` → hardware ticket (fans, airflow) and the BMC sensors. Low clock with `powersave` on `acpi-cpufreq` → `performance`, then verify latency. Normal clock → the CPU really is busy: `pidstat 1`, `perf top`.

### systemd-cgtop / lsns — resources per service or container, and the namespaces behind them
Match: systemd-cgtop, lsns, systemd-cgls
Instead of: top, docker stats
Safety: read-only · lsns needs root to see every namespace

**In one line:** `systemd-cgtop` is `top` for control groups: CPU, memory and task count per systemd service, slice and container; `lsns` lists the namespaces (network, PID, mount and so on) on the host and a process inside each.

**Read the command:** `systemd-cgtop -n 2 -d 1 --depth 3`

| Part | Meaning |
|---|---|
| `-n 2` | two refreshes, then exit (CPU % needs two samples; with `-n 1` it shows `-`) |
| `-d 1` | one second between refreshes |
| `--depth 3` | levels below `/` to show (`/system.slice` is 1, `/system.slice/apache2.service` is 2) |
| `-m` | sort by memory instead of CPU (same as `--order=memory`) |
| `lsns -t net` | network namespaces only: one per container or `ip netns` |
| `lsns -p PID` | every namespace that one process lives in |

**What the output tells you:**

```
Control Group                                Tasks   %CPU   Memory  Input/s Output/s
/                                              612  389.2     5.6G        -        -
/system.slice/apache2.service                  157  342.7     1.3G        -        -
/system.slice/docker-3f1c2a9e5b7d...scope       41   21.4   612.0M        -        -
```

Apache's 157 tasks together use 343% of the 400% the box has; a Docker container appears as a `docker-ID.scope`. On a mixed Apache and Docker host this is the fastest answer to "which service?".

**Why it is effective:** it adds up every process of a service or container, so 150 Apache workers at 2% each become one line at 300%, and services and containers sit in one list.

**Compared with `top`:** one line per process; the service total is left to you. **Compared with `docker stats`:** containers only, nothing for systemd services.

**Trap:** `Memory` is the cgroup's charge, which includes page cache the service caused, so a service that reads big files looks larger than its processes' RSS. Container IDs are cut; match them with `docker ps --no-trunc`. `lsns` shows one PID per namespace (the lowest), not every member.

**Next step:** one service dominates → `pidstat -l 1 5` for its processes, then profile. A busy container → also check its CPU throttling (`cpu.stat` in its cgroup). A namespace of interest → look inside with `nsenter -t PID -n ss -ltn`. Related: `systemd-cgls --no-pager` prints the same cgroup tree once, every process under its slice, service or scope: which unit owns a PID.

### taskset / renice — which CPUs a process may use, and how readily it yields
Match: taskset, renice
Instead of: kill (stopping a noisy batch job outright)
Safety: changes state: CPU affinity or scheduling priority of a process · raising priority (a lower nice value) needs root

**In one line:** `taskset` pins a process to a set of CPUs; `renice` changes the nice value (-20 highest priority to 19 lowest) of a running process, so a backup or batch job yields CPU to the web tier instead of being killed.

**Read the command:** `taskset -c 0 nice -n 15 yes > /dev/null &`

| Part | Meaning |
|---|---|
| `taskset -c 0` | allow only CPU 0 (lists work too: `0,2` or `0-3`) |
| `nice -n 15` | start the program at nice 15, a low priority |
| `yes > /dev/null` | a pure CPU burner, its output thrown away |
| `&` | run it in the background |
| `renice -n 10 -p 1234` | give running PID 1234 nice value 10 |
| `renice -n -5 -p 1234` | raise its priority (root only) |
| `taskset -cp 1234` | show which CPUs PID 1234 may use |

**What the output tells you:** `renice` prints the old and the new priority; check that the new one is what you meant. In `top`, the `NI` column shows the nice value: with two burners pinned to CPU 0, one at nice 0 and one at nice 15, the niced one gets only a small share of that core.

**Why it is effective:** on a contended box, nice decides who waits. Lowering a backup's priority (and its disk priority with `ionice -c3`) often removes the slowness without stopping the job, and pinning reproduces single-core saturation in a lab.

**Compared with `kill`:** stopping the job ends the contention at once, but the work is lost and has to be rerun; renice keeps it running, more slowly.

**Trap:** nice only matters when CPUs are contended: on an idle box a nice-19 job still gets a whole core. On Linux the nice value is per **thread**: `renice -p PID` changes only the thread whose ID is PID (the main thread), so the existing worker threads of a Java server keep their old value; check with `ps -eLo pid,tid,ni,comm`. For a systemd service, set `Nice=` or `CPUWeight=` in the unit instead. With default limits, a normal user can raise a nice value but cannot lower it again, not even back to 0.

**Next step:** still too slow → cap the job in a cgroup (`systemd-run -p CPUQuota=50% CMD`) or move it to a quieter hour. One busy core → `mpstat -P ALL 1`.

### ulimit — which resource limits this shell, and everything it starts, runs with
Match: ulimit
Instead of: —
Safety: read-only when reading · with a value it changes the limit of the current shell and its children only

**In one line:** `ulimit` is a shell builtin that shows or sets the per-process limits (open files, processes, core-dump size) that the shell and every program started from it inherit.

**Read the command:** `ulimit -n; ulimit -Hn`

| Part | Meaning |
|---|---|
| `-n` | open file descriptors: the soft limit, the one enforced |
| `-Hn` | the hard limit: the ceiling a normal user may raise the soft limit to |
| `-a` | every limit at once |
| `-u` | processes for this user, threads included |
| `-c` | core-dump size; `0` means no core dumps from this shell |
| `ulimit -n 65535` | set the limit; without `-S` or `-H`, bash sets soft **and** hard |
| `( ulimit -n 64; CMD )` | a subshell: the limit applies only to CMD, a safe way to test |

**What the output tells you:**

```
1024
524288
```

This shell may open 1,024 files and could raise that to 524,288 without root. A process at its soft limit gets `EMFILE`, "Too many open files", on its next `open()` or `accept()`.

**Why it is effective:** it is the quickest way to see and test limits, and the subshell trick reproduces "Too many open files" on purpose.

**Trap:** `ulimit` shows **your shell's** limits, not a service's. systemd services take theirs from the unit (`LimitNOFILE=`), containers from `--ulimit` or the Docker daemon, and `/etc/security/limits.conf` applies only to PAM logins (SSH, su), never to services. The truth for a running process is `/proc/PID/limits`. A normal user who lowers the hard limit cannot raise it again in that shell.

**Next step:** a service near its limit (`ls /proc/PID/fd | wc -l` versus `/proc/PID/limits`) → `LimitNOFILE=` in a drop-in (`systemctl edit UNIT`), restart, verify in `/proc/PID/limits`. A count that only grows → a descriptor leak (`lsof -p PID`). `fork: Resource temporarily unavailable` → `ulimit -u` and the unit's `TasksMax=`.

### lsof — which process holds this port, file, mount or deleted file?
Match: lsof
Instead of: du -sh when df and du disagree, netstat -tulpn
Safety: read-only · needs root to see other users' processes; can hang on a dead NFS mount (-b avoids that)

**In one line:** `lsof` lists the open files of every process (regular files, directories, pipes, sockets) and answers both "what does this process hold open?" and "who holds this file, mount or port?".

**Read the command:** `lsof -nP -iTCP:443 -sTCP:LISTEN`

| Part | Meaning |
|---|---|
| `-n` | no DNS lookups for addresses: faster, and no hang on a broken resolver |
| `-P` | port numbers, not service names |
| `-iTCP:443` | network files: TCP port 443 (`-i :443` = any protocol, listeners and connections) |
| `-sTCP:LISTEN` | only sockets in the LISTEN state |
| `+L1` | files with a link count below 1: deleted but still open |
| `+f -- /data` | everything open on the filesystem mounted at `/data` |
| `-p 1234` | everything process 1234 has open |

**What the output tells you:**

```
$ sudo lsof -nP -iTCP:443 -sTCP:LISTEN
COMMAND  PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
apache2 1123     root    4u  IPv6  23456      0t0  TCP *:443 (LISTEN)
$ sudo lsof -nP +L1
COMMAND  PID USER   FD   TYPE DEVICE   SIZE/OFF NLINK   NODE NAME
java    2671  app    5w   REG  252,0 7516192768     0 131202 /var/log/app/app.log.1 (deleted)
```

`FD` is the descriptor number plus mode (`r` read, `w` write, `u` both). The second listing is a 7 GB log deleted while Java still writes to it: `df` counts the space, `du` cannot see it.

**Why it is effective:** it closes the two most confusing disk incidents (space `du` cannot find, `umount: target is busy`) and finds any process's logs and connections without knowing anything about the app.

**Compared with `du -sh`:** du adds up directory entries, so a deleted-but-open file is invisible to it. **Compared with `netstat -tulpn`:** for ports alone, `ss -tlnp` is faster and names the same owner; lsof is the tool when files matter too, and on macOS, which has no `ss`.

**Trap:** without root it silently lists only your own processes, so "nothing listens" may be wrong. The COMMAND column is cut to 9 characters (`docker-pr` is `docker-proxy`). Freeing deleted space means reloading or restarting the holder; truncating through `/proc/PID/fd/N` works but destroys the content.

**Next step:** deleted log held open → reload or restart the service, then fix logrotate (`copytruncate`, or a reload in `postrotate`). Busy mount → stop or move the listed processes. Unknown listener → `pstree -aps PID`, `ps -o unit= -p PID`.

### strace — which system calls a process makes, and which one it is stuck in
Match: strace
Instead of: —
Safety: needs root to attach to a running process · slows the traced process 10–100 times: attach for seconds

**In one line:** `strace` stops the process at every system call (open a file, read a socket, wait on a lock) and prints the call, its arguments, its result and its duration, so you see what a hung or slow program is actually doing.

**Read the command:** `strace -f -tt -T -s 200 -p 1234`

| Part | Meaning |
|---|---|
| `-f` | follow all threads and child processes (without it: the main thread only) |
| `-tt` | wall-clock time with microseconds on every line |
| `-T` | time spent inside each call, in `<…>` at the end |
| `-s 200` | print up to 200 characters of each string (default 32) |
| `-p 1234` | attach to this running process; Ctrl-C detaches, the process carries on |
| `-c -w` | instead of lines: a summary per syscall; `-w` counts wall-clock time, so waiting shows |
| `-e trace=network` | only network-related calls |
| `-o FILE ./app` | start a program under strace, writing the trace to a file |

**What the output tells you:**

```
[pid  3127] 11:31:07.204118 sendto(12, "Q\0\0\0\216SELECT o.id, o.total"..., 143, MSG_NOSIGNAL, NULL, 0) = 143 <0.000037>
[pid  3127] 11:31:07.204201 poll([{fd=12, events=POLLIN|POLLERR}], 1, -1) = 1 ([{fd=12, revents=POLLIN}]) <2.913552>
```

The thread sends a SQL query on file descriptor 12, then waits 2.9 s in `poll` for the answer: the database is the slow part, and `ls -l /proc/PID/fd/12` plus `ss -tnp` name the peer. `ENOENT` and `EACCES` results explain "config not found" and "permission denied"; long `futex` calls are threads waiting for each other.

**Why it is effective:** it works on any binary in any language, with no logs, debug builds or restarts, and shows exactly where the program meets the outside world: files, sockets, locks, child processes.

**Trap:** a busy server slows down for every user while traced; prefer `-c -w` for 10 s, or `perf trace` and `syscount-bpfcc` on hot paths. Pure computation makes few syscalls, so a process at 100% CPU in its own code shows almost nothing (use `perf top`). Current glibc often makes `stat()` through `newfstatat` or `statx`, so a filter on `stat` alone can print nothing.

**Next step:** waiting on a socket → name the peer and time that dependency. `futex` dominates → thread dumps or `offcputime-bpfcc`. Slow `read` or `fsync` → `iostat -xz 1`. Nothing useful → `ltrace` or the runtime's profiler.

### ltrace — time the calls a program makes into shared libraries
Match: ltrace
Instead of: strace (when the time is spent inside a library)
Safety: needs root to attach to a running process · slows the target heavily: use briefly, on a test box if you can

**In one line:** `ltrace` intercepts calls from a program into shared libraries (`getaddrinfo`, `SSL_read`, `malloc`) and can time each one, for waits that happen inside library code rather than in one slow system call.

**Read the command:** `ltrace -f -T -e getaddrinfo curl -so /dev/null https://api.example.com/`

| Part | Meaning |
|---|---|
| `-f` | also trace child processes |
| `-T` | time spent inside each call, as `<seconds>` |
| `-e getaddrinfo` | trace only this function (name resolution) |
| `curl -so /dev/null https://api.example.com/` | the program to start and trace (silent, body discarded) |
| `-c` | instead of per-call lines: calls and total time per function |
| `-p PID` | attach to a running process instead of starting one |

**What the output tells you:**

```
[pid 51231] getaddrinfo("api.example.com", "443", 0x7f2b1c000b70, 0x7f2b1c000b48) = 0 <5.012334>
```

Name resolution took 5.0 s and then succeeded (`= 0`): the classic sign of a dead first DNS server, with the resolver waiting out its 5-second timeout before trying the next one.

**Why it is effective:** some waits never appear as one slow syscall: the resolver spreads its retries over several sockets, and TLS spends its time computing in user space. Timing the one suspect function gives a single unambiguous number.

**Compared with `strace`:** strace shows the `sendto` and `poll` calls to port 53 and their timeouts, from which you can infer the DNS wait; ltrace shows the library call that wraps them. For most problems strace is enough and far more robust.

**Trap:** ltrace is fragile on modern hardened binaries and may print nothing at all, which does not mean nothing happened. It is also very slow on busy programs. Lower-overhead ways to time library functions: `perf` with uprobes, or `funclatency-bpfcc` from `bpfcc-tools`.

**Next step:** slow `getaddrinfo` → check `/etc/resolv.conf` and each server with `dig @SERVER name`. Slow TLS calls → the peer or the certificate chain (`openssl s_client`). Nothing visible → `strace -f -T` or `perf`.

### perf top / perf stat — which function burns the CPU right now, and how efficiently
Match: perf, perf top, perf stat
Instead of: top
Safety: needs root on Ubuntu (kernel.perf_event_paranoid) · read-only, low overhead

**In one line:** `perf top` is `top` for functions: a live ranking of the code using the CPU, system-wide or for one process, kernel included; `perf stat` counts events (CPU time, context switches, page faults and, on bare metal, cycles and instructions) for a process or a command.

**Read the command:** `perf top -p 1234`

| Part | Meaning |
|---|---|
| `top` | live sampling view, refreshed every few seconds |
| `-p 1234` | only this process; without it, the whole system |
| `--sort comm,symbol` | group by command and function, to see who causes kernel (`sy`) time |
| `perf stat -p 1234 -- sleep 10` | count events for process 1234 for 10 seconds |
| `perf stat -e task-clock CMD` | count only the CPU time of a command you start |

**What the output tells you:**

```
Samples: 48K of event 'cpu-clock:ppp', 4000 Hz, Event count (approx.): 9874123456
Overhead  Shared Object            Symbol
  31.42%  libcrypto.so.3           [.] sha512_block_data_order_avx2
  12.08%  php-fpm8.3               [.] execute_ex
   6.77%  [kernel]                 [k] rep_movs_alternative
```

31% of CPU time is SHA-512 hashing called from PHP: password hashing on every request. `[.]` is user space, `[k]` the kernel. `cpu-clock` instead of `cycles` means a VM without hardware counters; perf then samples on a timer, which still finds hot code. In `perf stat`, `insn per cycle` (IPC) well below 1 often means the CPU is waiting on memory; VMs often print `<not supported>` for cycles and instructions.

**Why it is effective:** in seconds, without restarting anything, it names the function, which decides whether the fix is in your code, a library or the kernel (`native_queued_spin_lock_slowpath` = kernel lock contention, `__x64_sys_*` = plain syscall volume).

**Compared with `top`:** top says "php-fpm uses 300%"; perf top says which function inside it.

**Trap:** perf must match the running kernel: on Ubuntu install `linux-tools-$(uname -r)` (otherwise the `perf` wrapper warns that perf is not found for this kernel), and run it with sudo. Raw addresses or `[unknown]` mean missing symbols or JIT-compiled code, not a perf failure. It sees only on-CPU time: a process that is slow because it waits looks idle.

**Next step:** hot function confirmed → `perf record -g` for call stacks and a flame graph. Kernel lock or syscall symbols → `strace -c -f -p PID`, `pidstat -w 1`. Interpreted language → `py-spy top` or the runtime's own profiler.

### perf record / report / script — a CPU profile you can keep, read and turn into a flame graph
Match: perf record, perf report, perf script
Instead of: top
Safety: needs root · read-only for the target, but writes perf.data, which grows quickly on big hosts

**In one line:** `perf record` samples the call stacks running on the CPU for a process or the whole box, `perf report` ranks the functions by their share of samples, and `perf script` exports the stacks for a flame graph.

**Read the command:** `perf record -F 99 -g -p PID -o /var/tmp/perf.data -- sleep 30`

| Part | Meaning |
|---|---|
| `-F 99` | 99 samples per second (not 100, to avoid lock-step with timers) |
| `-g` | record whole call stacks, not only the current function |
| `-p PID` | only this process, all its threads |
| `-a` | instead of `-p`: every CPU, kernel included |
| `-o /var/tmp/perf.data` | output file (default: `./perf.data`) |
| `-- sleep 30` | record while this command runs: 30 seconds |
| `perf report -i FILE --stdio --sort comm,dso,symbol` | text report by command, library (DSO) and function |
| `perf script -i FILE > /var/tmp/out.perf` | one stack per sample, the input for the FlameGraph scripts |

**What the output tells you:**

```
# Overhead  Command  Shared Object          Symbol
    38.12%  apache2  libpcre2-8.so.0.10.4   [.] 0x000000000003c1a2
    14.77%  apache2  libphp8.1.so           [.] execute_ex
     3.88%  apache2  [kernel.kallsyms]      [k] copy_user_enhanced_fast_string
```

38% of samples are in the PCRE regex library and 15% in PHP's interpreter loop: an expensive regular expression in the application. A hex address instead of a name means missing symbols. `--no-children` ranks by each function's own time, without its callees.

**Why it is effective:** it turns "the CPU is high" into a function name for any language and the kernel, at an overhead low enough for production, and the file is evidence for the developers. In a flame graph, the widest boxes near the top are where the CPU burns.

**Compared with `top`:** top names the process and its CPU share, not the code inside it that is hot.

**Trap:** perf samples only **on-CPU** time: a request that is slow because it waits (locks, database, network) barely appears; use `offcputime-bpfcc`, `strace -c -w` or thread dumps. Interpreted and JIT languages show the interpreter (`execute_ex`) or `[unknown]`; their own profilers (py-spy, async-profiler) give real function names. For a container, run perf on the host against the host PID.

**Next step:** hot user-space code → hand the report or flame graph to the developers. Hot `[k]` functions → high `sy`: `pidstat -w 1`, `strace -c`. Nothing hot but still slow → it is waiting: `strace -f -T`, `offcputime-bpfcc`.

### execsnoop-bpfcc / offcputime-bpfcc / biolatency-bpfcc — what top cannot see: short-lived processes, blocked time, disk latency
Match: execsnoop-bpfcc, offcputime-bpfcc, biolatency-bpfcc
Instead of: top, ps (short-lived processes never appear)
Safety: needs root (loads eBPF programs into the kernel) · read-only, low overhead

**In one line:** these BCC tools (package `bpfcc-tools` on Ubuntu, hence the `-bpfcc` suffix) run small verified eBPF programs in the kernel: `execsnoop` prints every new process as it starts, `offcputime` sums where threads sleep instead of running, `biolatency` draws a histogram of disk I/O latency.

**Read the command:** `execsnoop-bpfcc -T`

| Part | Meaning |
|---|---|
| `execsnoop-bpfcc` | trace every `exec()` on the host until Ctrl-C |
| `-T` | add a time-of-day column |
| `offcputime-bpfcc -p PID 10` | for 10 s, the stacks where PID's threads were blocked, with total blocked microseconds |
| `-f` | folded output for `flamegraph.pl`: an off-CPU flame graph |
| `biolatency-bpfcc -D 10 1` | one 10-second histogram of block I/O latency, per disk (`-D`) |

**What the output tells you:**

```
TIME     PCOMM            PID     PPID    RET ARGS
12:20:02 sh               71201   2795      0 /bin/sh -c curl -fs http://127.0.0.1:8000/health || exit 1
12:20:02 curl             71202   71201     0 /usr/bin/curl -fs http://127.0.0.1:8000/health
```

Hundreds of these per second: a container health check forks `sh` and `curl` again and again. `RET` 0 is a successful exec; `PPID` leads to the parent (here a `containerd-shim`).

**Why it is effective:** each of those processes lives a few milliseconds, too short for `top` to list, yet together they create load and CPU spikes. offcputime is the other half of `perf`: perf shows time **on** the CPU, offcputime the time **off** it (locks, I/O, sleeps), where waiting requests spend theirs. biolatency shows the latency distribution, so rare 100 ms outliers stand out from an average that looks fine.

**Compared with `top` and `ps`:** they read the process table now and then; a process that starts and exits in between is never listed, although the CPU it used still shows in the totals.

**Trap:** on RHEL the package is `bcc-tools`, installed in `/usr/share/bcc/tools/` without the suffix. offcputime also counts idle threads that simply wait for work, so read the stacks, not only the totals.

**Next step:** a process storm → find what spawns it (the PPID, a health check, a cron job), then lengthen its interval or make it cheaper. Off-CPU time in locks → thread dumps (`jstack`, `py-spy dump`). A latency tail on one disk → `iostat -xz 1` for that device.

### py-spy — which Python function and line, in a live process, without restarting it
Match: py-spy
Instead of: strace, perf
Safety: needs root to read another process's memory (in a container: the SYS_PTRACE capability) · read-only, low overhead

**In one line:** `py-spy` reads a running CPython process's memory from outside and shows every thread's Python stack (`dump`), a live top of Python functions (`top`), or records a flame graph (`record`), without changing the code or restarting the service.

**Read the command:** `py-spy record -o /var/tmp/profile.svg --pid PID --duration 30`

| Part | Meaning |
|---|---|
| `record` | sample the stacks over time and write a profile |
| `-o /var/tmp/profile.svg` | output file; the default format is an interactive flame graph |
| `--pid PID` | the running Python process (for a container: its host PID) |
| `--duration 30` | stop after 30 seconds (default: at Ctrl-C) |
| `dump --pid PID` | print the current stack of every thread once |
| `top --pid PID` | live view of the functions using the most time |

**What the output tells you:** a `py-spy dump`:

```
Thread 3127 (idle): "ThreadPoolExecutor-0_7"
    execute (psycopg2/extras.py:146)
    _execute_context (sqlalchemy/engine/base.py:1900)
    list_orders (shop/views.py:88)
```

The thread is `idle` (not running: blocked in a call) inside a database query made from `list_orders` in `shop/views.py`, line 88. `active` threads whose stacks end in your own code are the ones burning CPU.

**Why it is effective:** it gives the function and line in the developers' own code, the evidence that gets a fix scheduled, and it is safe to point at production.

**Compared with `strace` and `perf`:** strace shows the `poll` on the database socket and perf shows the interpreter's C functions (`_PyEval_EvalFrameDefault`); both are true, and neither names your Python function.

**Trap:** `record` and `top` leave idle threads out by default (`--idle` includes them), so a service that is slow because it **waits** can look quiet; take two or three `dump`s a few seconds apart instead. Native frames from C extensions appear only with `--native`.

**Next step:** waiting on a database or HTTP call → time that dependency (slow-query log, `curl -w`). A hot Python function → hand the flame graph to the developers. Every thread waiting on the same lock → report the lock with the dumps.

### jstack / jstat — what every Java thread is doing, and whether garbage collection is eating the JVM
Match: jstack, jstat
Instead of: kill -3 (the dump lands in the app's log), restarting the JVM
Safety: read-only · run as the JVM's user or inside its container · a thread dump pauses the JVM for a moment

**In one line:** `jstack` prints a thread dump of a running JVM (every thread's state and Java stack); `jstat` samples the garbage collector's counters, showing how full the heap is and how much time goes to collection.

**Read the command:** `jstat -gcutil PID 1000 5`

| Part | Meaning |
|---|---|
| `-gcutil` | GC summary: fill level of each heap area in %, GC counts and times |
| `PID` | the JVM's process ID (`1` when run inside its container) |
| `1000` | sample every 1000 ms |
| `5` | five samples |
| `jstack PID > /var/tmp/jstack.txt` | a thread dump into a file; take three, 5 s apart |

**What the output tells you:**

```
  S0     S1     E      O      M     CCS    YGC     YGCT     FGC    FGCT     CGC    CGCT       GCT
  0.00   0.00 100.00  99.91  97.12  93.40   2412   48.112   311  1290.551    18    0.912  1339.575
  0.00   0.00  12.40  99.90  97.12  93.40   2412   48.112   312  1294.807    18    0.912  1343.831
```

`O` (old generation) stays at 99.9% while `FGC` (full collections) keeps rising: each full GC frees almost nothing and takes about 4 s (`FGCT`/`FGC`), with every application thread stopped. In a `jstack` dump, many threads `BLOCKED` "waiting to lock" the same object mean lock contention.

**Why it is effective:** GC pauses and lock contention cause "slow for a few seconds, then fine" with no OS resource saturated; these two tools prove or rule them out in a minute, without a restart.

**Compared with `kill -3`:** SIGQUIT makes the JVM print the same thread dump, but into its stdout (the container log or journal), not your terminal. A restart destroys the evidence.

**Trap:** both attach through files under `/tmp` of the JVM's user: run them as that user (`sudo -u APPUSER`) or via `docker exec` inside the container, otherwise jstack fails with "Unable to open socket file" and jstat finds no JVM. JRE-only images have no `jstack` or `jstat`. The `nid=` in a dump is the OS thread ID, printed in hex on many JDKs, which links a hot thread from `top -H` to its stack.

**Next step:** old generation still full after full GCs → heap too small or a leak (heap dump for the developers). Many threads blocked on one lock → the dump to the developers. One hot thread → `top -H -p PID`, `printf '%x\n' TID`, find that `nid` in the dump.

### stress-ng / sysbench — create a known load, or a comparable benchmark number
Match: stress-ng, sysbench, yes
Instead of: yes > /dev/null, dd if=/dev/zero
Safety: changes state: deliberately loads CPU, memory or disk and can trigger the OOM killer · test VMs only, always with a timeout

**In one line:** `stress-ng` generates a chosen kind of load (CPU, memory, disk, context switches, sockets) so you can see what each looks like in `vmstat`, `mpstat` and `pidstat`; `sysbench` is a benchmark that prints comparable numbers (events per second, latency percentiles) for CPU, memory and file I/O.

**Read the command:** `stress-ng --vm 2 --vm-bytes 60% --vm-keep --timeout 300s &`

| Part | Meaning |
|---|---|
| `--vm 2` | two memory-stressing workers |
| `--vm-bytes 60%` | how much memory they use, as a share of available RAM (raise it until swapping starts) |
| `--vm-keep` | keep rewriting the same memory instead of freeing and remapping it |
| `--timeout 300s` | stop by itself after 300 seconds |
| `&` | run in the background while you watch other tools |
| `--cpu 4`, `--switch 4`, `--hdd 2` | other loads: CPU workers, a context-switch storm, disk writers |
| `sysbench cpu --threads=4 --time=20 run` | CPU benchmark: 4 threads for 20 seconds |

**What the output tells you:** stress-ng itself prints little; the lesson is in the other tools (`--vm`: `si`/`so` and `kswapd0`; `--cpu`: `r` and `us`; `--hdd`: `b` and `wa`). sysbench (excerpt):

```
CPU speed:
    events per second:  4321.07
Latency (ms):
         max:                                   14.21
         95th percentile:                        0.97
```

Compare `events per second` between VMs or instance types; a max far above the 95th percentile means a thread was briefly descheduled (another process, or steal).

**Why it is effective:** you learn each signature on a box you are allowed to break, before you meet it in an incident, and you can test alerts, cgroup limits and "is the new VM as fast as the old one?" with numbers.

**Compared with `yes > /dev/null` and `dd`:** they load one core or one disk stream and run until killed; stress-ng covers each subsystem, scales to N workers and stops itself.

**Trap:** without `--timeout`, or with too large a `--vm-bytes` on a box without swap, the OOM killer may pick a real service instead of stress-ng. `sysbench fileio prepare` writes gigabytes of test files: always run `cleanup`, and use files larger than RAM (or direct I/O), or you benchmark the page cache. stress-ng's "bogo ops" are not comparable between versions.

**Next step:** watch with `vmstat 1`, `mpstat -P ALL 1` and `pidstat 1` while it runs, stop it with `pkill -TERM -x stress-ng`, and confirm the box returns to idle. Related: `yes > /dev/null &` keeps one core busy with nothing to install (macOS too); stop it with `kill %1`.

### jobs / wait — what runs in the background of this shell, and wait until it ends
Match: jobs, wait
Instead of: sleep N (guessing when background work is done)
Safety: read-only (wait blocks the shell until the jobs end)

**In one line:** `jobs` lists the background and stopped jobs of the current shell with their job numbers (`%1`); `wait` blocks until background jobs finish and hands back their exit status, so a script continues exactly when the work is done.

**Read the command:** `kill %1; wait %1; echo "exit=$?"`

| Part | Meaning |
|---|---|
| `kill %1` | send TERM to job 1 of this shell (`%1` is a job number, not a PID) |
| `wait %1` | block until job 1 has exited |
| `echo "exit=$?"` | print job 1's exit status: 143 = ended by TERM, 0 = it caught TERM and exited cleanly |
| `jobs -l` | list the jobs with their PIDs |
| `wait` | with no argument: wait for every background job |
| `$!` | PID of the most recent background job (`wait $!`, `pstree -p $!`) |

**What the output tells you:**

```
[1]-  4211 Running                 sleep 900 &
[2]+  4230 Running                 taskset -c 0 yes > /dev/null &
exit=143
```

`[1]` is the job number, `+` the current job (what `fg` picks), `-` the previous one, then the PID, the state (Running, Stopped, Done) and the command.

**Why it is effective:** in labs and scripts you often start a load or a capture in the background, measure, then stop it; `wait` gives the real exit status instead of a guessed `sleep`, and `jobs` shows what is still running before you log out.

**Compared with `sleep N`:** a fixed sleep is either too short (the work is not done) or wastes time, and it says nothing about how the job ended.

**Trap:** jobs belong to one shell: another terminal, `sudo -i` or a new SSH session cannot see them, and `wait` works only on this shell's own children. When the SSH session closes, the shell sends HUP to its jobs and they usually die: use `nohup`, tmux or, better, a systemd unit (`systemd-run`) for anything that must keep running. `sudo kill %1` fails, because only the shell's built-in `kill` understands `%1`.

**Next step:** a job that must outlive the session → `systemd-run --unit=NAME CMD` (logs go to the journal). Lost track of a background process → `pgrep -af PATTERN`.
