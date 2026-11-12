# More Linux tools

Tools the handbook uses once or twice, each for one precise question: keep a job alive after you disconnect (`tmux`, `setsid`), stop scheduled runs from overlapping (`flock`), look inside a hung or broken binary (`gdb`, `ldd`), see CPU queueing, single disk I/Os and TCP retransmits (BCC), repair what boots (`update-grub`, `grubby`), write sturdier bash, and read the manual for the version installed. Reach for them once the everyday tools have narrowed the problem down.

| If you would reach for | Prefer | Because |
|---|---|---|
| a long upgrade in a plain SSH session | `tmux new -s work`, later `tmux attach -t work` | a dropped connection no longer kills the job |
| cron jobs that might overlap | `flock -n /run/lock/JOB.lock CMD` | the kernel releases the lock even after a crash |
| restarting a hung native service blind | `gdb -p PID -batch -ex "thread apply all bt"` first | the stacks show where it hangs; a restart erases that |
| symlinking a library to the name an app wants | `ldd BINARY` | it lists every missing library and the file the loader would use |
| editing `/boot/grub/grub.cfg` | `/etc/default/grub`, then `update-grub`; `grubby` on RHEL | grub.cfg is regenerated, and your edit with it |
| a web search for a flag | `man 5 crontab`, `man -k WORD` | the page matches the version installed here |

### tmux / screen / setsid / disown — keep a long job running after the SSH session ends
Match: tmux, screen, setsid, disown
Instead of: nohup, a long job in a plain SSH session
Safety: read-only themselves · what runs inside keeps running, and changing things, after you leave

**In one line:** when an SSH session closes, the shell sends SIGHUP to its jobs and they usually die; `tmux` keeps a whole terminal session alive to reattach later, `setsid` starts a command outside your session, `disown -h` shields a running job.

**Read the command:** `setsid ./long.sh </dev/null &>/dev/null &`

| Part | Meaning |
|---|---|
| `setsid` | run in a new session without a controlling terminal: logout sends it no SIGHUP |
| `</dev/null &>/dev/null &` | nothing tied to the terminal (output discarded: name a log file instead), prompt back |
| `tmux new -s work` · Ctrl-b d · `tmux attach -t work` | start a named session · detach · reattach after reconnecting |
| `screen -S work` · Ctrl-a d · `screen -r work` | the same with screen |
| `disown -h %1` | bash: do not send HUP to job 1 when the shell gets it (forgot nohup) |

**Why it is effective:** a dropped Wi-Fi during `apt upgrade` or a data copy leaves half-done work; inside tmux the job never notices, and you reattach to its output and prompts.

**Compared with `nohup`:** it ignores HUP and logs to `nohup.out`, fine for fire-and-forget, but you cannot reattach to answer a prompt.

**Trap:** a `disown -h` job still writes to the closed terminal, which kills some programs: redirect output first. With logind's `KillUserProcesses=yes`, logout kills tmux too. None survives a reboot.

**Next step:** must survive reboots → a systemd unit or `systemd-run --unit=NAME CMD`. Forgotten sessions → `tmux ls`.

### flock / lslocks — run a scheduled job one copy at a time, and see which file locks are held
Match: flock, lslocks
Instead of: a PID file checked by hand, cron runs that pile up
Safety: `flock` changes state: creates the lock file if missing, then runs the command · `lslocks` is read-only

**In one line:** `flock FILE CMD` runs CMD while holding an exclusive lock on FILE, so a second copy waits or, with `-n`, gives up; `lslocks` lists the file locks held on this host and who holds them.

**Read the command:** `flock -n /run/backup.lock /usr/local/bin/backup.sh`

| Part | Meaning |
|---|---|
| `-n` | lock already held → exit at once with status 1 instead of waiting |
| `/run/backup.lock` | any agreed file, created if missing (`/run` needs root) |
| `-w 600` | wait up to 600 s for the lock, then give up |
| `lslocks` | every lock: command, PID, type, mode, path |

**What the output tells you:**

```
COMMAND     PID  TYPE SIZE MODE  M START END PATH
flock      4182 FLOCK   0B WRITE 0     0   0 /run/backup.lock
```

Last night's run still holds the lock, so tonight's `flock -n` exits 1: the backup is skipped.

**Why it is effective:** the kernel drops the lock when the process ends, even after `kill -9`, so no stale lock blocks later runs, unlike a PID file left by a crash.

**Trap:** a run skipped by `-n` is silent: alert on exit 1 (`-E` sets another code). The lock is per host: jobs on two servers need a shared lock (restic's own, a database row). lslocks shows kernel file locks only, not Java monitors or row locks.

**Next step:** a lock held for hours → `ps -o pid,etime,cmd -p PID`: stuck or slow? Overlaps persist → a systemd timer, which never starts a unit still running.

### gdb — what is every thread of a hung native program doing, right now?
Match: gdb
Instead of: cat /proc/PID/task/*/stack, restarting the hung service blind
Safety: pauses the target while attached · needs root or the same user (Ubuntu's ptrace_scope blocks attaching to processes that are not your children)

**In one line:** `gdb -p PID` attaches the debugger to a running process; in batch mode it prints every thread's call stack and detaches: a thread dump for C, C++ and other native programs.

**Read the command:** `gdb -p 1234 -batch -ex "thread apply all bt"`

| Part | Meaning |
|---|---|
| `-p 1234` | attach to PID 1234; all its threads stop |
| `-batch` | run the `-ex` commands, then exit; the process continues |
| `-ex "thread apply all bt"` | a backtrace (`bt`) of every thread |

**What the output tells you:**

```
Thread 3 (Thread 0x7f2a9bfff640 (LWP 1240) "worker"):
#0  0x00007f2a9d4e2f9a in ?? () from /lib/x86_64-linux-gnu/libc.so.6
#1  0x00007f2a9d4e9b11 in pthread_mutex_lock () from /lib/x86_64-linux-gnu/libc.so.6
#2  0x000055d1c3a2b1f4 in cache_get ()
#3  0x000055d1c3a2a870 in handle_request ()
```

Read upwards: `handle_request` called `cache_get`, now waiting for a mutex. Many threads with the same frames are queued on one lock.

**Why it is effective:** a hung process logs nothing and looks idle in `top`; the stacks name the function each thread waits in.

**Compared with `/proc/PID/task/*/stack`:** the kernel side only (a futex wait), not the application function behind it.

**Trap:** without debug symbols frames show `??` (install the `-dbgsym` or `debuginfo` packages). All threads stop while gdb runs. For a JVM use `jstack`, for Python `py-spy dump`: gdb shows only the interpreter's C frames.

**Next step:** threads queued on one lock → the code holding it (`offcputime-bpfcc`). Stuck inside a system call → `strace -p PID`. Evidence before a restart → `gcore PID` writes a core file (as big as its memory).

### ldd / ldconfig — which shared libraries does this binary need, and can the loader find them?
Match: ldd, ldconfig
Instead of: reinstalling the application, symlinking a similar library
Safety: `ldd` reads, but may execute the program: never on an untrusted binary · `sudo ldconfig` rebuilds the loader cache

**In one line:** `ldd` lists the shared libraries a program needs and the file the loader would use for each; `not found` explains `error while loading shared libraries`.

**Read the command:** `ldd /usr/bin/app`

| Part | Meaning |
|---|---|
| `ldd FILE` | each needed library `=>` the path it resolves to, or `not found` |
| `ldconfig -p | grep libssl` | is the library in the cache (`/etc/ld.so.cache`), and where |
| `sudo ldconfig` | rebuild the cache after adding a library to a directory listed in `/etc/ld.so.conf.d/` |
| `objdump -p FILE | grep NEEDED` | the needed names only, without running anything (binutils) |

**What the output tells you:**

```
	linux-vdso.so.1 (0x00007ffd5b9f2000)
	libssl.so.1.1 => not found
	libcrypto.so.1.1 => not found
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f0c1a200000)
```

Built against OpenSSL 1.1; Ubuntu 22.04 and later ship only `libssl.so.3`.

**Why it is effective:** the start-up error names one library; ldd lists every missing one at once, and the path each found one comes from.

**Compared with reinstalling the application:** usually the same build, with the same gap.

**Trap:** never symlink `libssl.so.3` to the old name: the ABI differs and the crash only moves later. `LD_LIBRARY_PATH` fixes one shell, not the service. A static binary (most Go builds) prints `not a dynamic executable`; a glibc binary on Alpine fails with `no such file or directory`.

**Next step:** missing library → the package that ships it (`apt-file search libssl.so.1.1`, `dnf provides '*/libssl.so.1.1'`), or a build for this release.

### runqlat-bpfcc / biosnoop-bpfcc / tcpretrans-bpfcc — CPU queueing, every disk I/O, every TCP retransmit
Match: runqlat-bpfcc, biosnoop-bpfcc, tcpretrans-bpfcc
Instead of: vmstat's r column, iostat's await, nstat TcpRetransSegs
Safety: needs root (loads eBPF programs) · read-only; biosnoop on a busy disk prints thousands of lines a second

**In one line:** more BCC tools (`bpfcc-tools`; RHEL: `/usr/share/bcc/tools/`, no suffix): `runqlat` is a histogram of how long runnable threads wait for a CPU, `biosnoop` prints each block I/O with its latency, `tcpretrans` each TCP retransmit.

**Read the command:** `sudo runqlat-bpfcc 10 1`

| Part | Meaning |
|---|---|
| `10 1` | one 10-second interval, one histogram, then exit (without: until Ctrl-C) |
| `biosnoop-bpfcc | head -30` | per I/O: time, process, PID, disk, R or W, sector, bytes, latency in ms |
| `tcpretrans-bpfcc` | per retransmit: local and remote address and port, TCP state |

**What the output tells you:**

```
     usecs               : count     distribution
         0 -> 1          : 2342     |*****                                   |
         2 -> 3          : 15671    |****************************************|
         4 -> 7          : 6120     |***************                         |
         8 -> 15         : 1803     |****                                    |
```

Most waits are microseconds: the CPUs keep up. Counts in millisecond buckets mean work queues for a CPU, a delay `%CPU` hides.

**Why it is effective:** counters say *that* it happened; these show the distribution, or each event with its process or address.

**Compared with `nstat TcpRetransSegs`:** a host-wide count, good for a trend, blind to which connection retransmits.

**Trap:** tcpretrans's PID is usually 0 or unrelated (kernel context): trust the addresses. biosnoop often names a kernel flusher thread for buffered writes. Missing kernel headers → `linux-headers-$(uname -r)`.

**Next step:** long run-queue tail → `mpstat -P ALL 1`. Slow I/Os on one disk → `iostat -xz 1`, `smartctl`. Retransmits to one peer → `mtr`, `ethtool -S`.

### update-grub / grubby / grub-install — which kernel boots next, with which options, and can this disk boot?
Match: update-grub, grub-mkconfig, grub2-mkconfig, grubby, grub-install
Instead of: editing grub.cfg by hand
Safety: changes state: what the next boot does (`grubby --default-kernel` only reads) · needs root

**In one line:** on Ubuntu, `update-grub` regenerates `/boot/grub/grub.cfg` from `/etc/default/grub` and the kernels in `/boot`; on RHEL, `grubby` reads and sets the default kernel and its arguments; `grub-install` writes the boot loader onto a disk.

**Read the command:** `grubby --default-kernel`

| Part | Meaning |
|---|---|
| `grubby --default-kernel` | RHEL: the kernel the next boot picks |
| `grubby --update-kernel=ALL --args="…"` | add kernel arguments to every entry (`--remove-args` removes) |
| `sudo update-grub` | Ubuntu: rebuild the menu (it runs `grub-mkconfig -o /boot/grub/grub.cfg`) |
| `sudo grub-install /dev/sdb` | BIOS boot: GRUB onto the second disk of a RAID 1, so either disk boots |

**What the output tells you:**

```
$ sudo update-grub
Sourcing file `/etc/default/grub'
Generating grub configuration file ...
Found linux image: /boot/vmlinuz-6.8.0-85-generic
Found linux image: /boot/vmlinuz-6.8.0-79-generic
Found initrd image: /boot/initrd.img-6.8.0-79-generic
done
```

Each kernel needs its initrd line: 6.8.0-85 has none, so it cannot mount an LVM root.

**Why it is effective:** a new `GRUB_CMDLINE_LINUX` or kernel counts only after the rebuild, and the output lists what the next boot can choose.

**Compared with editing grub.cfg:** the next kernel update regenerates it: the edit is gone.

**Trap:** RHEL 8 and 9 keep kernel entries in `/boot/loader/entries/` (BLS): change arguments with `grubby`, not by editing files. UEFI hosts boot from the EFI system partition: a replaced RAID disk needs its own ESP copy.

**Next step:** after the reboot → `cat /proc/cmdline`; keep the old kernel until the new one boots. Nothing boots → rescue ISO, chroot, `update-initramfs`, `update-grub`.

### declare / mapfile / getopts / shopt — arrays, option flags and empty globs in bash scripts
Match: declare, mapfile, readarray, getopts, shopt
Instead of: for x in $(cmd), parsing "$1" by hand
Safety: read-only · they change only variables and options of the running shell

**In one line:** bash builtins for sturdier scripts: `declare -A` makes a lookup table, `mapfile -t` reads lines into an array, `getopts` parses `-d 90`-style options, and `shopt -s nullglob` makes a glob that matches nothing expand to nothing.

**Read the command:** `mapfile -t failed < <(systemctl list-units --state=failed --no-legend --plain | awk '{print $1}')`

| Part | Meaning |
|---|---|
| `mapfile -t failed` | one array element per line; `-t` drops the newline |
| `< <(…)` | the array stays in this shell (after a pipe it would vanish in a subshell) |
| `${#failed[@]}` · `"${failed[@]}"` | element count · every element, each kept whole |
| `declare -A CID_NAME=()` | a table keyed by strings: `CID_NAME[$id]=web`, read `${CID_NAME[$id]}` |
| `while getopts ':d:m:h' opt` | `-d VALUE`, `-m VALUE`, `-h`; value in `$OPTARG`; leading `:` = the script reports errors |
| `shopt -s nullglob` | `for f in /etc/apache2/sites-enabled/*.conf` runs zero times when nothing matches |

**Why it is effective:** names with spaces, empty directories and bad options are where quick scripts break.

**Compared with `for x in $(cmd)`:** fine for simple words, but splits on spaces and expands `*`.

**Trap:** without `declare -A` first, string keys are read as numbers and collide or fail. macOS ships bash 3.2: no `declare -A`, no `mapfile`. getopts takes short options only; `shift $((OPTIND-1))` drops them after parsing. With nullglob, an unmatched `ls *.log` runs plain `ls`.

**Next step:** a growing script → `shellcheck`. Long options → a `while`/`case` loop over `"$1"` with `shift`.

### man — what exactly does this option or file format mean, for the version installed here?
Match: man, apropos
Instead of: a web search that answers for another version
Safety: read-only

**In one line:** `man` shows the manual installed with a program, so it matches the version you run; pages sit in numbered sections, and `man -k` searches every page's one-line description.

**Read the command:** `man 5 crontab`

| Part | Meaning |
|---|---|
| `5` | section 5, file formats: the crontab *file* syntax; plain `man crontab` opens section 1, the command |
| sections | 1 user commands, 5 file formats, 7 overviews (`man 7 signal`), 8 admin commands (`man 8 sshd`) |
| `man -k "listening socket"` | search names and descriptions (same as `apropos`) |
| `man -f crontab` | which sections have a page of that name |

**What the output tells you:**

```
$ man -f crontab
crontab (1)          - maintain crontab files for individual users (Vixie Cron)
crontab (5)          - tables for driving cron
```

Two pages: the command, and the file format that answers questions such as why a `%` breaks a line.

**Why it is effective:** the page documents the build on this host, and its FILES and EXAMPLES sections show where configuration lives.

**Compared with a web search:** quicker for common tasks, but may describe another version or distribution.

**Trap:** minimal and container images ship without pages (Ubuntu: `unminimize`). Pages added by hand reach `man -k` after `sudo mandb`. Builtins such as `set` have none: `help set`. Inside, `/word` searches, `q` quits.

**Next step:** a quick flag reminder → `CMD --help | less`. Example configs → `/usr/share/doc/PACKAGE/`.
