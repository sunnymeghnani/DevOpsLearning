# 05 — Process Troubleshooting

Typical tasks: find a process, see why it's stuck, kill it properly, trace what
it's doing, deal with zombies and orphans.

---

## 1. Finding processes

```bash
ps aux                                  # everything (BSD style)
ps -ef                                  # everything (System V style, shows PPID)
ps aux | grep -i [n]ginx                # [n] trick: excludes the grep itself
pgrep -a nginx                          # PIDs + full command line
pgrep -u appuser -f "worker"            # by user + full-cmdline match
pidof java                              # PIDs by exact program name
ps -eo pid,ppid,user,stat,etime,rss,cmd --sort=-etime | head    # oldest first
```

Useful `ps` output selectors:
```bash
ps -o pid,stat,wchan:20,cmd -p 1234     # STAT + what kernel func it's waiting in
ps -eo state,pid,cmd | awk '$1=="D"'    # all uninterruptible (I/O-stuck) processes
ps -eo state,pid,cmd | awk '$1=="Z"'    # all zombies
```

STAT codes: `R` running, `S` sleeping, `D` uninterruptible sleep (I/O — cannot be
killed!), `Z` zombie, `T` stopped, `<` high prio, `s` session leader, `+` foreground.

### `pstree` — parent/child relationships
```bash
pstree -p            # tree with PIDs
pstree -aps 1234     # ancestors + arguments for one PID
```

---

## 2. Killing processes (properly)

```bash
kill 1234                    # SIGTERM (15) — polite, allows cleanup. ALWAYS TRY FIRST.
kill -9 1234                 # SIGKILL — cannot be caught; no cleanup; last resort
kill -HUP 1234               # many daemons: reload config without restart
kill -0 1234 && echo alive   # signal 0 = existence/permission check only
pkill -f "runaway_script.py" # kill by command-line match (careful with the pattern!)
killall -v java              # kill by exact name
kill -STOP 1234 ; kill -CONT 1234   # pause / resume (triage a runaway without killing)
```

Signals cheat: `kill -l` lists all. Common: 1 HUP (reload), 2 INT (Ctrl-C),
3 QUIT (+core), 9 KILL, 15 TERM, 19 STOP, 18 CONT, 30/31 USR1/USR2 (app-defined —
nginx USR1 reopens logs).

**`kill -9` doesn't work?**

- `D` state → blocked in kernel I/O (dead NFS, dying disk). Fix the I/O source;
  the process reaps only when the syscall returns.
- Zombie (`Z`) → already dead; it's just an unreaped exit status. Kill/fix the
  **parent** (`ps -o ppid= -p <zombiepid>`), or it reparents to init when parent dies.

---

## 3. Priorities

```bash
nice -n 19 ./batchjob.sh       # start at lowest priority
renice -n 10 -p 1234           # lower priority of a running process
renice -n -5 -p 1234           # raise priority (root only for negative)
ionice -c3 -p 1234             # idle-class disk I/O (backups that hurt prod)
ionice -c2 -n0 -p 1234         # best-effort, highest
```

---

## 4. What is this process doing? (tracing)

### `strace` — system calls (slows target ~10-100x; use briefly)
```bash
strace -p 1234                       # attach live (Ctrl-C detaches)
strace -f -tt -T -s 200 -p 1234      # follow forks, timestamps, syscall durations
strace -c -p 1234                    # summary table: which syscalls, how much time
strace -e trace=network -p 1234      # only network syscalls
strace -e trace=open,openat,stat ./app   # which files it tries to open (great for
                                          # "config not found" / "permission denied")
strace -o /tmp/trace.txt ./app       # trace from launch into a file
```
Typical diagnoses:

- hangs in `connect(...)` → waiting on a remote service
- `EACCES`/`ENOENT` on open → permissions / wrong path
- tight `futex` loops → lock contention
- endless `wait4()` → waiting for a child

### `ltrace` — library calls (malloc, str*, SSL_*)
```bash
ltrace -p 1234
ltrace -c ./app
```

### `lsof` — open files, sockets, everything
```bash
lsof -p 1234                   # all files/sockets one process has open
lsof -i :8080                  # who owns port 8080
lsof -i TCP -s TCP:ESTABLISHED # established TCP by process
lsof /var/log/app.log          # who has this file open
lsof +D /data                  # everything open under a directory (slow)
lsof -u appuser                # by user
lsof -p 1234 | wc -l           # fd count → compare to limit (fd leak?)
```

### File descriptor limits ("Too many open files")
```bash
ulimit -n                              # limit of YOUR shell
cat /proc/1234/limits | grep files     # limit of the RUNNING process (what matters)
ls /proc/1234/fd | wc -l               # current fd count
```
Raise: systemd unit → `LimitNOFILE=65535`; PAM → `/etc/security/limits.conf`.
Note: a systemd service ignores limits.conf — it takes limits from the unit file.

### `/proc/<pid>/` — direct inspection
```bash
cat /proc/1234/cmdline | tr '\0' ' '   # exact command line
readlink /proc/1234/cwd                # working directory
readlink /proc/1234/exe                # actual binary ("(deleted)" = updated on disk
                                       #   but old version still running → restart!)
cat /proc/1234/environ | tr '\0' '\n'  # environment variables
cat /proc/1234/stack                   # kernel stack — WHERE a D-state proc is stuck
ls -l /proc/1234/fd                    # every open fd and what it points to
```

### Stack dumps for hung apps
```bash
cat /proc/1234/task/*/stack            # kernel-side stacks of all threads
gdb -p 1234 -batch -ex "thread apply all bt"   # userspace stacks (pauses briefly)
jstack 1234                            # JVM thread dump
kill -3 <jvm-pid>                      # JVM: dump threads to stdout/log (harmless)
py-spy dump --pid 1234                 # Python stack without stopping it
```

---

## 5. Background jobs & daemonizing

```bash
jobs ; bg ; fg %1              # shell job control
nohup ./long.sh &              # survive terminal close
setsid ./long.sh </dev/null &>/dev/null &   # fully detach
tmux / screen                  # the better answer for long remote jobs
disown -h %1                   # forgot nohup? detach an already-running job
```

---

## Quick answers

| Question | Command |
|----------|---------|
| Who is using port 443? | `ss -tlnp sport = :443` or `lsof -i :443` |
| Why can't I kill PID? | `ps -o stat= -p PID` → D = I/O hang, Z = kill the parent |
| What files does it read? | `strace -e trace=openat -p PID` |
| Is the running binary stale? | `readlink /proc/PID/exe` → "(deleted)" = yes, restart |
| Is it leaking fds? | `ls /proc/PID/fd | wc -l` vs `grep files /proc/PID/limits` |
| What's it waiting on? | `cat /proc/PID/stack`, `strace -p PID` |
