# 27 — Learn: Linux Zero to Hero

This module teaches Linux from first principles up to operator level (Ops Ladder
L0 and L1) and hands you the four L2 tools that let you look at a layer directly:
`strace`, `lsof`, `ss` and `tcpdump`. The reference modules 01–13 tell you
*which command* to type. This module tells you *how the system works*, so you know
*why* that command, how to read its output, and *what to run next*.

Everything is anchored in the incident that started this handbook: a client wanted
a new app on a port, Apache already served three or four vhosts on 443, and Dokploy
(Traefik) needed 80, 443 and 3000. You solved it by moving Apache to ports 81 and 444
([Deployment patterns](35-deployment-patterns.md) shows how to finish that with Traefik
routing). By the end of this module, "who owns port 443, which unit starts it, where
is its config, where are its logs, can I stop it safely and roll back?" should take
five minutes, not an afternoon of searching.

**Which career stages this module serves.** Use the tags on every topic to find your
place on the [career ladder](40-career-ladder.md):

| Stage | Ops Ladder level | What this module gives you |
|-------|------------------|----------------------------|
| Fresher (0–1 yr) | L0 Foundations | Sections 1–5, 10, 12–13 and the L0 exit test: shell, files, permissions, users, packages, SSH keys, scripting, text tools |
| Junior (1–2 yrs) | L1 Operator | Sections 6–11 and 14–16 and the L1 exit test: systemd, boot, storage, network config, scheduling, logs, kernel, security |
| Mid-level (2–4 yrs) | L2 Troubleshooter | Section 17, the bridge: `ss`, `lsof`, `strace` and `tcpdump` to look at a layer directly |
| Senior and Lead | L3–L4 | Not here. This module is the floor they stand on; continue in modules 30–33, 35 and 39 |

Each topic carries a tag such as **[L1 · Junior]**: the Ops Ladder level, then the
career stage. A topic marked **[L1 · Junior] → [L2 · Mid]** starts at the first level
and its lab or "How it breaks" table reaches into the second.

> ⚠️ Commands here are examples for YOUR servers or a test VM. Every "Hands-on lab"
> is for a disposable test VM with a snapshot — never for production. Sample outputs
> are illustrative (Ubuntu 22.04/24.04 unless stated); versions, PIDs and sizes will
> differ on your systems.

---

## 0. How to use this module

### Learning path

Work top to bottom. The level tag is the Ops Ladder level the topic belongs to.
Skim what you already know, but **do every lab and the exit tests** — the ladder's
advice applies here too: skim L0 and L1, prove them with the exit tests, then put
your real hours into L2.

| # | Area | Level · stage | Why it is in the path |
|---|------|---------------|-----------------------|
| 1 | Shell basics and the filesystem hierarchy | [L0 · Fresher] | You can't troubleshoot what you can't find: where config, state and logs live |
| 2 | Files, permissions and ownership | [L0 · Fresher] | Half of all "it doesn't work" is a permission or ownership problem |
| 3 | Users, groups and sudo | [L0 · Fresher] | Service accounts, docker group, safe privilege |
| 4 | Processes, signals and jobs | [L0 · Fresher] → [L1 · Junior] | Every service is a process; states and signals explain hangs and restarts |
| 5 | Package management | [L0 · Fresher] | "Which package put this file here?" and controlled upgrades |
| 6 | systemd and journald | [L1 · Junior] | Every service you run is a unit; this is where "who starts it" lives |
| 7 | The boot process and recovery | [L1 · Junior] | Getting a box back when it won't boot (fstab, GRUB, root password) |
| 8 | Storage and filesystems | [L1 · Junior] | Disk full, inodes, fstab, LVM growth — the most common pages |
| 9 | Networking configuration on Ubuntu | [L1 · Junior] | netplan, resolved and ss basics; the deep dive is in 28 |
| 10 | SSH | [L0 · Fresher] → [L1 · Junior] | Keys, hardening without locking yourself out, tunnels |
| 11 | Scheduling: cron, timers and at | [L1 · Junior] | Jobs that "didn't run", plus the rollback safety net |
| 12 | Bash scripting for operations | [L0 · Fresher] → [L1 · Junior] | Turning your checks into repeatable scripts |
| 13 | Text processing toolkit | [L0 · Fresher] → [L1 · Junior] | Answering questions from logs in one line |
| 14 | Logs and log rotation | [L1 · Junior] | Finding any app's logs, journal filters, logrotate |
| 15 | Kernel basics | [L1 · Junior] | Modules, sysctl, dmesg, limits, cgroups — prerequisites for Docker and Kubernetes |
| 16 | Security basics | [L1 · Junior] | UFW, fail2ban, unattended-upgrades, SELinux/AppArmor |
| 17 | Debugging tools: the bridge to L2 | [L2 · Mid] | strace, lsof, ss, tcpdump — look instead of guessing |
| 18 | Self-check / exit test | [L0 · Fresher] → [L1 · Junior] | Prove it under time pressure |
| 19 | Where to go next | — | Modules 22–40 and practice sites, by career stage |

### Study method: five steps per topic

For each `###` topic in this module:

1. **Read this note** — the concept, the diagram and the "See it on a real system"
   commands. Run those read-only commands on your own VM and compare.
2. **KodeKloud course or lesson** — the "📚 Study path" line at the top of each area
   names the KodeKloud course and lesson that matches it. Do its labs in the browser.
   The line is ordered for you: when an area is brand new at its level, the KodeKloud
   lesson comes first; when it is a refresher of something you use daily, this note
   comes first and the lesson is the backup.
3. **Optional video** — only if the note and the lesson did not click. Short and
   targeted; the Ops Ladder warns against long bootcamps that re-explain tools you
   already use and never hand you a broken server.
4. **Hands-on lab** — on your own test VM: build it, break it on purpose, fix it.
   This is the step that turns reading into skill. Don't skip the "break" part.
5. **Related playbook** — read the linked playbook (22–26) as if it were a live
   incident and predict each next step before you read it.

After each area, write the five-line note the Ops Ladder asks for after any incident:
the symptom, your first wrong guess, the evidence that settled it, the fix, and what
you'll check first next time.

### Build your lab VM

You need a disposable machine you are allowed to break.

| Option | Good for | Notes |
|--------|----------|-------|
| Ubuntu 24.04 server VM (KVM/Proxmox/VirtualBox/Multipass) | Everything in this module | 2 vCPU, 2–4 GB RAM, 20 GB disk, plus a **second 5 GB virtual disk** for storage labs |
| Rocky Linux 9 VM | RHEL differences: dnf, SELinux, firewalld | Optional, but SELinux only makes sense when you've broken it once |
| [Killercoda Linux scenarios](https://killercoda.com/linux) | Days you don't want to start a VM | Browser terminal, resets itself |
| [SadServers](https://sadservers.com/scenarios) | Timed break-fix practice | Free tier, automatic check when you think you fixed it |

```bash
# Example with Multipass (any hypervisor works the same way)
multipass launch 24.04 --name lab1 --cpus 2 --memory 4G --disk 20G
multipass shell lab1
```

Lab safety rules — follow them every time:

- Take a **snapshot** before each lab and restore it when you're done.
- Keep a **console** open (hypervisor console, not SSH) before touching SSH,
  the firewall, netplan, fstab or sudoers. SSH can't save you from an SSH mistake.
- Some labs reboot the VM. A reboot stops every service and drops every session; on a
  real server it needs `who` (who is logged in), an announcement and a change window.
- Never copy a lab "break" step to a production server. The labs exist so the
  first time you see each error is not in front of a client.

### No VM? Use these

No hypervisor yet, or a locked-down laptop? Climb this ladder from the easiest to the most real,
and move up as soon as a lab needs `sudo`, `systemctl` or the network. Limits were checked on
9 Nov 2026; free tiers change, so look again before you rely on one.

| # | Option | What you get | Limits (checked 9 Nov 2026) | Good for |
|---|---|---|---|---|
| 1 | [WebTerm free play](https://webterm.app/en/free-play) | A simulated shell with canned output and a virtual file system in your tab | No sign-up. A simulator, not a VM: the site claims 100+ commands, about 70 worked when tested, and there is no `sudo`, `apt`, `ip`, `ss` or `journalctl` | Day one only: files, permissions, pipes |
| 2 | [JSLinux](https://bellard.org/jslinux/) or [v86](https://copy.sh/v86/) | Real Linux emulated in your tab (Alpine 3.23 on JSLinux; Arch or Buildroot on v86) | No account, nothing uploaded, no network unless you turn on a v86 relay. Not Ubuntu: `apk` or `pacman`, not `apt` | Real commands and kernel messages, nothing to install |
| 3 | [Killercoda Ubuntu playground](https://killercoda.com/playgrounds/scenario/ubuntu) | A real Ubuntu VM with root and systemd | Free account; one-hour sessions (PLUS gives four) | Troubleshooting practice: break a unit, read the journal |
| 4 | [iximiuz Labs playgrounds](https://labs.iximiuz.com/playgrounds) | Real VMs: Ubuntu 26.04, Docker, Podman, kubeadm and k3s clusters, a four-VM MiniLAN | Free account, no card; one playground at a time, one hour a day, 2 CPU and 4 GB, restricted internet | Docker, Kubernetes and multi-host networking |
| 5 | [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) | A real Ubuntu 24.04 server | Free account; one hour, plus 15-minute extensions | Any lab in this module that fits in an hour |
| 6 | [Google Cloud Shell](https://shell.cloud.google.com/) or [GitHub Codespaces](https://github.com/codespaces) | A persistent real shell with Docker; add `kubectl` or `terraform` if missing | A container, so no `systemctl`. Cloud Shell: Google account, 50 hours a week, 5 GB `$HOME` deleted after 120 days unused. Codespaces: GitHub account, 120 core-hours (60 h on 2 cores) and 15 GB a month, no card (usage stops at the quota) | Scripts, Git, Docker builds, tooling |
| 7 | The handbook's own [Hands-on labs](#m-labs) | Real Ubuntu 24.04 with systemd in a Docker container on your machine, destroyed when you finish | Needs Docker: `docker compose --profile labs up -d --build` | Guided rooms with automatic checks |

### How each topic is laid out

Every `###` topic follows the same pattern, so you always know where you are:

| Label | What it gives you |
|-------|-------------------|
| Level | Ops Ladder level and career stage, e.g. [L1 · Junior] |
| Concept | Plain language first, then the precise version, often with an ASCII diagram |
| Key terms | The vocabulary you'll meet in docs and error messages |
| See it on a real system | Safe, read-only commands with sample output and how to read it (→ lines) |
| Hands-on lab (test VM only) | Build it, break it on purpose, fix it |
| How it breaks | Symptom or exact error → first command → which playbook/reference to open |
| Why it matters for troubleshooting | The link to real incidents |
| Next step | What to learn next and why |

Placeholders in commands are UPPERCASE words: HOST, PORT, UNIT, USER, PID,
CONTAINER, DOMAIN, PACKAGE, FILE.

---

## 1. Shell basics and the filesystem hierarchy

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Working with Shell I, then Linux Core Concepts (file types, FHS) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 2) Note: this section, then the [cheat sheet](19-cheatsheet.md) · 3) Video (optional): KodeKloud *Linux Crash Course for Beginners | Free Linux Lab Access | KodeKloud* ([YouTube](https://www.youtube.com/watch?v=a3ujwK65dgs), 141 min) · 4) Practice: [Linux Upskill Challenge](https://linuxupskillchallenge.org/) days 1–5 on your lab VM

### How the shell runs a command

**Level:** [L0 · Fresher]

**Concept**

The shell (bash on Ubuntu) is just a program that reads your line, expands it,
finds the program to run, starts it and waits for it. Precisely: bash splits the
line into words, expands variables, `~` and globs (`*.log`), sets up redirections,
then looks the first word up as alias → function → builtin → a file found by
searching `$PATH` left to right. For an external program it calls `fork()` to make
a child and `exec()` to replace the child with the program. Every process starts
with three open file descriptors: 0 = stdin, 1 = stdout, 2 = stderr. When the
child exits, its exit code (0–255, 0 = success) lands in `$?`.

```
 you type:  grep -i error /var/log/syslog > errors.txt 2>&1
                │
                ▼
 bash: split words → expand $VARS, ~, *globs → prepare redirections
                │
                ▼
 find "grep": alias? function? builtin? → else search $PATH left → right
                │   /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
                ▼
 fork() a child → child exec()s /usr/bin/grep with:
                fd 0 stdin  ← terminal
                fd 1 stdout → errors.txt
                fd 2 stderr → same place as fd 1
                ▼
 child exits with a code → bash stores it in $?  (0 = success, anything else = failure)
```

**Key terms**

| Term | Meaning |
|------|---------|
| stdin / stdout / stderr | File descriptors 0, 1, 2. Errors normally go to stderr, which a plain pipe does **not** carry |
| Exit code | Number a program returns; `0` success, `1`–`125` program-defined failure, `126` not executable, `127` not found, `128+N` killed by signal N |
| `$PATH` | Colon-separated list of directories searched for commands |
| Builtin | Command implemented inside bash (`cd`, `export`, `echo`, `type`) |
| Environment variable | Variable exported to child processes (`export VAR=x`); a plain shell variable is not inherited |

**See it on a real system**

```bash
type cd ls grep                 # builtin, alias or file?
command -v apachectl            # the path the shell would run (use in scripts instead of which)
echo "$PATH"
ls /nonexistent; echo "exit code: $?"
ls /etc/hostname /nonexistent > out.txt 2> err.txt   # split the two streams
cat out.txt err.txt
```

```
$ type cd ls grep
cd is a shell builtin
ls is aliased to `ls --color=auto'
grep is aliased to `grep --color=auto'
$ ls /nonexistent; echo "exit code: $?"
ls: cannot access '/nonexistent': No such file or directory
exit code: 2
```

→ `ls` returned 2 ("serious trouble" in its man page). Scripts and systemd read exit
codes, not messages — learn to look at both.

Redirection cheat sheet:

| Syntax | Effect |
|--------|--------|
| `cmd > file` | stdout to file (truncate) |
| `cmd >> file` | stdout appended |
| `cmd 2> file` | stderr to file |
| `cmd > file 2>&1` | both to file — order matters: `2>&1 > file` sends stderr to the terminal |
| `cmd &> file` | bash shorthand for both |
| `cmd 2>&1 | grep x` | search errors too (a plain pipe only carries stdout) |
| `cmd < file` | file as stdin |
| `cmd | tee file` | show and save at the same time |
| `echo x | sudo tee /etc/FILE` | write a root-owned file (see the trap below) |

The classic trap: `sudo echo "x" > /etc/FILE` fails with "Permission denied" because
**your** shell does the redirection before sudo ever runs. Use `sudo tee`.

**Hands-on lab (test VM only)**

**Step 1 — Break PATH.** Run `export PATH=/nonexistent`, then `ls`. You get
`bash: ls: command not found`. Builtins like `echo` and `cd` still work, which
tells you the shell is fine and only the lookup is broken. Fix it with
`export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin` or just
open a new shell (the change was only in this shell).

**Step 2 — The sudo redirect trap.**

```bash
sudo echo "test" > /etc/lab-test.conf          # Permission denied — your shell opened the file
echo "test" | sudo tee /etc/lab-test.conf      # works
sudo rm /etc/lab-test.conf                      # clean up (a single named file, not a glob)
```

**Step 3 — Where did my error go?** Run `ls /nonexistent | grep -c cannot`. It prints
`0` because the error went to stderr, not through the pipe. Now run
`ls /nonexistent 2>&1 | grep -c cannot` and you get `1`.

**Step 4 — Shadowing.** Define `ls() { echo "hijacked"; }`, run `ls` and `type ls`,
then `unset -f ls`. This is why `type` is the first command when "the command
behaves strangely on this box".

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `bash: CMD: command not found` | `type CMD`, `echo "$PATH"`, `apt-file search bin/CMD` | [Packages](11-packages.md) |
| `sudo: CMD: command not found` but it works without sudo | `sudo sh -c 'echo $PATH'` (sudo uses `secure_path`) | Section 3 of this module |
| `bash: ./script.sh: Permission denied` | `ls -l script.sh` (x bit?), `findmnt -no OPTIONS -T script.sh` (noexec?) | Section 2 |
| `/bin/bash^M: bad interpreter` | `file script.sh` → "with CRLF line terminators" → `sed -i 's/\r$//' script.sh` | Section 12 |
| Works by hand, fails in cron or systemd | Compare `env` in both — different PATH, HOME, no TTY | Sections 6 and 11 |

**Why it matters for troubleshooting**

Every investigation is reading stdout, stderr and exit codes. Misreading where an
error went (`cmd | grep` silently drops stderr) or which binary ran (`/usr/local/bin`
shadows `/usr/bin`) sends you down the wrong path for an hour.

**Next step**

Learn the map of the filesystem, so you know where to look before you search.

### Getting help and working fast

**Level:** [L0 · Fresher]

**Concept**

Nobody remembers every flag. Seniors are fast because they know *where the answer
is*: the man page section, `--help`, the package's docs directory, or shell history.

**Key terms**

| Term | Meaning |
|------|---------|
| man sections | 1 user commands, 5 file formats (`man 5 crontab`), 8 admin commands (`man 8 sshd`) |
| `apropos` / `man -k` | Search man page descriptions |
| `/usr/share/doc/PACKAGE/` | Example configs, changelogs, README.Debian |
| tmux / screen | Terminal multiplexer: your session survives an SSH disconnect |

**See it on a real system**

```bash
man 5 crontab              # the crontab FILE format (man crontab = the command)
man -k "listening socket"  # which tools mention this?
ss --help | head -20       # quick flag list
ls /usr/share/doc/apache2/ # README.Debian.gz explains Ubuntu's a2ensite layout
history | grep -i netplan  # what did I (or the last admin) run?
```

Keyboard: `Ctrl-R` searches history backwards, `Alt-.` inserts the last argument of
the previous command, `!!` repeats the last command (`sudo !!`), `Ctrl-A`/`Ctrl-E`
jump to line start/end.

**Hands-on lab (test VM only)**

**Step 1.** Install tmux (`sudo apt install tmux`), start `tmux new -s work`, run
`top`, then close your SSH window. Reconnect and run `tmux attach -t work` — `top`
is still there.

**Step 2 — Break.** Without tmux, start `sleep 600` and close the SSH window.
Reconnect and run `pgrep -a sleep` — it's gone (it got SIGHUP when the terminal
closed; section 4 explains why).

**Step 3.** Look up three things using only the system: the crontab time field order
(`man 5 crontab`), the meaning of `ss -p` (`man 8 ss`), and the default Apache layout
on Ubuntu (`zless /usr/share/doc/apache2/README.Debian.gz`).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Long upgrade or migration died when Wi-Fi dropped | Use tmux next time; check `/var/log/apt/term.log` for how far it got | [Packages](11-packages.md) |
| `No manual entry for X` | `sudo apt install man-db manpages` (minimal images strip man pages; `unminimize` on Ubuntu minimal) | — |

**Why it matters for troubleshooting**

Running long changes (upgrades, data copies, migrations) inside tmux on production
is a habit that prevents half-finished changes. History tells you what the last
person did before "it broke".

**Next step**

The filesystem hierarchy — the map of where everything lives.

### The filesystem hierarchy (FHS)

**Level:** [L0 · Fresher]

**Concept**

Linux puts things in predictable places: configuration in `/etc`, things that grow
in `/var`, installed software in `/usr`, live kernel and process data in `/proc` and
`/sys`. Once you know the map, "where are this app's logs?" becomes a guess you can
verify in seconds instead of a web search.

```
/
├── bin, sbin, lib  → symlinks into /usr on modern Ubuntu ("usrmerge")
├── boot     kernels (vmlinuz-*), initramfs (initrd.img-*), grub/     ← "/boot full" breaks kernel updates
├── dev      device files: /dev/sda, /dev/nvme0n1, /dev/null          ← managed by udev
├── etc      CONFIGURATION (text) — look here first
│   └── apache2/  nginx/  ssh/  netplan/  systemd/system/  docker/  logrotate.d/
├── home     users' homes (root's home is /root)
├── opt      third-party software shipped as one directory
├── proc     kernel and process info as files (virtual, lives in RAM) ← /proc/PID/...
├── run      runtime state since boot: PID files, sockets (tmpfs)    ← /run/docker.sock
├── srv      data this host serves (by convention)
├── sys      kernel objects: devices, cgroups, power (virtual)
├── tmp      world-writable scratch space, sticky bit, may be cleaned at boot
├── usr      installed software: /usr/bin, /usr/lib, /usr/share
│   └── local   software you installed by hand (not from a package)
└── var      VARIABLE data that grows — ideally its own filesystem
    ├── log      logs: apache2/, nginx/, syslog, auth.log, journal/
    ├── lib      state: docker/, containerd/, mysql/, dpkg/, kubelet/
    ├── cache    re-creatable caches (apt archives)
    ├── spool    queues: cron, mail
    └── www      web roots (Debian/Ubuntu convention)
```

**Key terms**

| Term | Meaning |
|------|---------|
| FHS | Filesystem Hierarchy Standard — the convention above |
| Virtual filesystem | `/proc`, `/sys`, `/run`, `/dev` exist only in memory; nothing there survives a reboot |
| usrmerge | `/bin`, `/sbin`, `/lib` are symlinks to their `/usr` versions |
| Package-owned vs admin-owned | Files from packages live in `/usr`; your changes belong in `/etc` |

Where a typical service keeps its pieces (Ubuntu, RHEL in brackets):

| Piece | Apache | Nginx | Docker | systemd units |
|-------|--------|-------|--------|---------------|
| Binary | `/usr/sbin/apache2` (`/usr/sbin/httpd`) | `/usr/sbin/nginx` | `/usr/bin/dockerd` | — |
| Config | `/etc/apache2/` (`/etc/httpd/`) | `/etc/nginx/` | `/etc/docker/daemon.json` | `/etc/systemd/system/` (yours) |
| Enabled sites | `/etc/apache2/sites-enabled/` (`/etc/httpd/conf.d/`) | `/etc/nginx/sites-enabled/` (`conf.d/` on RHEL) | — | — |
| Logs | `/var/log/apache2/` (`/var/log/httpd/`) | `/var/log/nginx/` | `docker logs`, files under `/var/lib/docker/containers/` | journal |
| State/data | `/var/www/` | `/var/www/` | `/var/lib/docker/` | — |
| Unit | `apache2.service` (`httpd.service`) | `nginx.service` | `docker.service` | `/usr/lib/systemd/system/` (packages) |

Dokploy keeps its own configuration under `/etc/dokploy` (Traefik's static and
dynamic config live below it); its services run as Docker Swarm services, so their
"logs" are `docker service logs` — see [Docker](30-learn-docker.md) and
[Web servers & proxies](29-learn-webservers-proxies.md).

**See it on a real system**

```bash
ls -l /                                  # notice the usrmerge symlinks
df -hT / /var /boot /tmp                 # which of these are separate filesystems?
dpkg -L apache2 | grep -E '^/etc|^/usr/sbin|systemd'   # where a package put its files
systemctl show -p FragmentPath apache2   # where its unit file lives
ls -l /etc/apache2/sites-enabled/        # enabled vhosts (symlinks into sites-available)
```

```
$ ls -l / | head -8
total 2097228
lrwxrwxrwx   1 root root          7 Apr 22  2024 bin -> usr/bin
drwxr-xr-x   4 root root       4096 Sep 30 06:12 boot
drwxr-xr-x  20 root root       4040 Oct  3 06:01 dev
drwxr-xr-x 109 root root       4096 Oct  2 14:20 etc
drwxr-xr-x   4 root root       4096 Sep 12 10:31 home
lrwxrwxrwx   1 root root          7 Apr 22  2024 lib -> usr/lib
drwxr-xr-x   2 root root       4096 Aug 27  2024 opt
$ df -hT / /var /boot
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   48G   17G   29G  37% /
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   48G   17G   29G  37% /
/dev/sda2                         ext4  2.0G  196M  1.6G  11% /boot
```

→ `/var` shows the same device as `/`: it is **not** a separate filesystem here, so a
runaway log in `/var/log` can fill the root filesystem and take everything down.

**Hands-on lab (test VM only)**

**Step 1 — Build the map.** Install Apache (`sudo apt install apache2`). For
`apache2`, `ssh` and `cron`, write down: binary, main config file, unit file, log
location, state directory. Use `dpkg -L`, `systemctl cat` and `ls /var/log`.

**Step 2 — Break it.** Move Apache's log directory away and restart:

```bash
sudo mv /var/log/apache2 /var/log/apache2.lab-moved
sudo apache2ctl configtest          # still says "Syntax OK"
sudo systemctl restart apache2      # fails
systemctl status apache2 --no-pager -l
```

You'll see a line like
`AH00091: apache2: could not open error log file /var/log/apache2/error.log.`

**Step 3 — Fix it** with `sudo mv /var/log/apache2.lab-moved /var/log/apache2` and
restart. Lesson: "Syntax OK" checks the config grammar, not whether the paths it
needs exist.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Services fail to write, "No space left on device" | `df -hT; df -i` | [Storage](01-storage-disk.md), [Slow system playbook](23-playbook-slow-system.md) |
| Kernel update fails with "No space left" | `df -h /boot`, `dpkg -l 'linux-image-*'` | Section 7 |
| A PID file or socket directory vanished after reboot | It was in `/run` (tmpfs) — use `RuntimeDirectory=` in the unit | Section 6 |
| Your edit to a unit file vanished after an upgrade | You edited `/usr/lib/systemd/system/...` — use a drop-in in `/etc` | Section 6 |

**Why it matters for troubleshooting**

In the Apache → Dokploy incident, most of the searching was "where does this app
keep its config and logs?". With the map plus `dpkg -L`, `systemctl cat` and
`apachectl -S` (section 17) that answer is mechanical.

**Next step**

Inodes and links — what a "file" really is, which explains the deleted-but-open
disk trap and Apache's `sites-enabled` symlinks.

### Files, inodes and links

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

A filename is only a label. The real file is an **inode**: a record holding type,
permissions, owner, size, timestamps and pointers to the data blocks. A directory is
a list of `name → inode number` entries. A **hard link** is a second name for the
same inode; a **symlink** is a tiny separate file that contains a path. Deleting a
file removes a name; the data is freed only when the link count reaches 0 **and** no
process still has the file open.

```
 directory /var/log/app/        inode 131                      data blocks
 ┌──────────────────────┐      ┌─────────────────────────┐     ┌───────────┐
 │ app.log    → 131     │ ───▶ │ type, mode, uid, gid    │ ──▶ │ log text  │
 │ app.log.1  → 140     │      │ size, times, links = 1  │     └───────────┘
 └──────────────────────┘      └─────────────────────────┘
                                     ▲
 process 2134, fd 4 ─────────────────┘   an open file descriptor also keeps the inode alive
```

**Key terms**

| Term | Meaning |
|------|---------|
| Inode | The file's metadata record; a filesystem has a fixed or limited number of them |
| Link count | How many names point at the inode (column 2 of `ls -l`) |
| Hard link | Another name for the same inode; same filesystem only |
| Symlink | A file containing a path; can point anywhere, can dangle |
| File types | `-` regular, `d` directory, `l` symlink, `c`/`b` char/block device, `s` socket, `p` pipe |

**See it on a real system**

```bash
ls -li /etc/hostname               # first column = inode number
stat /etc/hostname                 # full inode metadata
readlink -f /etc/resolv.conf       # where a symlink chain ends
ls -l /etc/apache2/sites-enabled/  # a2ensite just creates symlinks here
file /usr/sbin/apache2 /etc/hosts  # what kind of content?
```

```
$ stat /etc/hostname
  File: /etc/hostname
  Size: 6               Blocks: 8          IO Block: 4096   regular file
Device: 252,0   Inode: 1048602     Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2026-10-03 08:01:12.415993000 +0000
Modify: 2026-09-12 10:22:40.000000000 +0000
Change: 2026-09-12 10:22:40.000000000 +0000
 Birth: 2026-09-12 10:22:40.000000000 +0000
$ readlink -f /etc/resolv.conf
/run/systemd/resolve/stub-resolv.conf
$ ls -l /etc/apache2/sites-enabled/
lrwxrwxrwx 1 root root 35 Sep 12 11:02 000-default.conf -> ../sites-available/000-default.conf
lrwxrwxrwx 1 root root 32 Sep 14 09:40 app1.conf -> ../sites-available/app1.conf
```

→ `Modify` is when the content changed, `Change` is when the inode (permissions,
owner) changed. "Who changed this config and when?" starts with `stat`.

**Hands-on lab (test VM only)**

**Step 1 — Links.**

```bash
mkdir -p ~/lab/links && cd ~/lab/links
echo "hello" > original.txt
ln original.txt hard.txt           # hard link: same inode
ln -s original.txt soft.txt        # symlink: points to the name
ls -li                             # compare inode numbers and link counts
rm original.txt
cat hard.txt                       # still works: data had 2 names
cat soft.txt                       # "No such file or directory": dangling symlink
```

**Step 2 — Break it: the deleted-but-open trap.**

```bash
fallocate -l 300M /var/tmp/big.log
tail -f /var/tmp/big.log > /dev/null &      # a process holds it open
rm /var/tmp/big.log
df -h /var/tmp                               # space NOT freed
sudo lsof -nP +L1 | grep big.log             # shows "(deleted)" with NLINK 0
kill %1                                      # the holder exits → space returns
df -h /var/tmp
```

**Step 3 — Fix the habit.** For a live log you need to empty, use
`truncate -s 0 FILE` instead of `rm`: the writer keeps its descriptor and the space
is released immediately.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `df` says full, `du` can't find the space | `sudo lsof -nP +L1` | [Storage](01-storage-disk.md) |
| "No space left on device" with free blocks | `df -i` (inodes exhausted) | Section 8 |
| Apache: `Could not open configuration file /etc/apache2/sites-enabled/X.conf` | `ls -l /etc/apache2/sites-enabled/` (dangling symlink) | [Web servers](29-learn-webservers-proxies.md) |
| `ln: failed to create hard link ... Invalid cross-device link` | Hard links can't cross filesystems — use a symlink | — |

**Why it matters for troubleshooting**

Two of the four classic "disk full" causes (deleted-but-open files, inode
exhaustion) only make sense once you know what an inode is. And `sites-enabled`
being symlinks is how you cleanly disable an Apache vhost (`a2dissite`) while
keeping its config for rollback.

**Next step**

Permissions — the metadata in the inode that decides who can do what.

---

## 2. Files, permissions and ownership

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (the file permissions lessons and labs) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 2) Note: this section, then [Users, permissions & security](10-users-permissions-security.md) · 3) Read (optional): [Linux Journey](https://labex.io/linuxjourney) permissions lessons · 4) Practice: this section's labs, then explain every field of `ls -l` aloud (L0 exit test)

### Reading ls -l field by field

**Level:** [L0 · Fresher]

**Concept**

Every file has an owner (user), a group, and three sets of permissions: for the
owner, for members of the group, and for everyone else. The kernel checks them in
that order and uses the **first matching class only** — if you are the owner, only
the owner bits count, even if "other" would allow more. Explaining every field of
`ls -l` is part of the L0 exit test.

```
 -rwsr-xr-x  1  root  root  64152  May 30  2024  /usr/bin/passwd
 │└┬┘└┬┘└┬┘  │   │     │      │    └─────┬─────┘  └─ name (" -> target" for symlinks)
 │ │  │  │   │   │     │      │          └─ mtime (shows the year instead of the time if older than ~6 months)
 │ │  │  │   │   │     │      └─ size in bytes (for a directory: size of its entry list)
 │ │  │  │   │   │     └─ group owner
 │ │  │  │   │   └─ user owner
 │ │  │  │   └─ link count (directories: 2 + number of subdirectories)
 │ │  │  └─ other:  r-x
 │ │  └─ group:  r-x
 │ └─ user:  rws  (s = setuid AND x; capital S = setuid without x)
 └─ type: - file, d dir, l symlink, c char device, b block device, s socket, p pipe
 An 11th character may follow the bits: "+" = ACL present, "." = SELinux context
```

What `r`, `w`, `x` mean depends on the object:

| Bit | On a file | On a directory |
|-----|-----------|----------------|
| r (4) | Read the content | List the names inside (`ls`) |
| w (2) | Change the content | Create, delete, rename entries inside — **even files you don't own** (unless sticky) |
| x (1) | Execute it | Enter / traverse it (`cd`, or reach anything below it) |

Deleting a file needs `w` on the **directory**, not on the file. Reaching
`/var/www/app/index.html` needs `x` on **every** directory in the path.

**Key terms**

| Term | Meaning |
|------|---------|
| Owner / group / other | The three permission classes, checked in that order, first match wins |
| Mode | The permission bits, written symbolically (`rwxr-x---`) or in octal (`750`) |
| Traverse (search) permission | `x` on a directory |
| root | UID 0 bypasses read/write checks (but still needs one `x` bit to execute a file) |

**See it on a real system**

```bash
ls -ld /etc/shadow /usr/bin/passwd /tmp /var/log/apache2
namei -l /var/www/html/index.html     # permissions of EVERY component of a path
stat -c '%A %a %U:%G %n' /etc/ssh/sshd_config
```

```
$ ls -ld /etc/shadow /usr/bin/passwd /tmp /var/log/apache2
-rw-r-----  1 root shadow  1342 Sep 30 06:14 /etc/shadow
-rwsr-xr-x  1 root root   64152 May 30  2024 /usr/bin/passwd
drwxrwxrwt 14 root root    4096 Oct  3 08:05 /tmp
drwxr-x---  2 root adm     4096 Oct  3 00:00 /var/log/apache2
$ namei -l /var/www/html/index.html
f: /var/www/html/index.html
drwxr-xr-x root root /
drwxr-xr-x root root var
drwxr-xr-x root root www
drwxr-xr-x root root html
-rw-r--r-- root root index.html
```

→ `/var/log/apache2` is `root:adm` mode 750: members of the `adm` group can read
Apache logs without sudo — that is the Ubuntu way to give a colleague log access.
→ `namei -l` is the fastest answer to "why 403 / Permission denied?": one line with
a missing `x` in the path is the culprit.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Create a tiny site and read it as the web server user:

```bash
sudo mkdir -p /srv/site
echo "hello" | sudo tee /srv/site/index.html
sudo -u www-data cat /srv/site/index.html     # test access AS the service user
```

**Step 2 — Break.** Remove traverse permission on the parent:

```bash
sudo chmod 700 /srv/site
sudo -u www-data cat /srv/site/index.html     # Permission denied
namei -l /srv/site/index.html                 # spot the directory without x for others
```

**Step 3 — Fix.** `sudo chmod 755 /srv/site`, then repeat the `sudo -u www-data`
test. Make "test as the service user" a reflex: it reproduces exactly what the app sees.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| Apache `AH00035: access to /index.html denied ... because search permissions are missing on a component of the path` | `namei -l FULL_PATH` | [Permissions reference](10-users-permissions-security.md) |
| Nginx `open() "/srv/site/index.html" failed (13: Permission denied)` | `sudo -u www-data cat FILE` | [Web servers](29-learn-webservers-proxies.md) |
| Can't delete a file you own | `ls -ld DIR` — you lack `w` on the directory, or the sticky bit is set | Special bits below |
| Permissions look right but still denied | `getfacl FILE`, `lsattr FILE`, SELinux/AppArmor | ACLs below, section 16 |

**Why it matters for troubleshooting**

When moving an Apache vhost into a container, the files now get read by a UID inside
the container that may not match the owner on the host. Reading `ls -ln` (numeric
IDs) and testing as the service user tells you in a minute whether a 403 is a
permission problem or a config problem.

**Next step**

Changing permissions correctly: chmod, chown and octal modes.

### chmod, chown and numeric modes

**Level:** [L0 · Fresher]

**Concept**

Octal mode is three digits, one per class, each the sum of r=4, w=2, x=1. `chmod`
changes the bits, `chown` changes owner and group. Use symbolic mode (`u+x`, `g-w`,
`o=`) for small changes, octal for setting a known state.

| Octal | Symbolic | Typical use |
|-------|----------|-------------|
| 644 | `rw-r--r--` | Normal files, web content |
| 640 | `rw-r-----` | Config with secrets readable by a group (`root:www-data`) |
| 600 | `rw-------` | Private keys, `~/.ssh/authorized_keys`, `.env` files |
| 755 | `rwxr-xr-x` | Directories, scripts, binaries |
| 750 | `rwxr-x---` | Directories only a group may enter |
| 700 | `rwx------` | `~/.ssh` |
| 2775 | `rwxrwsr-x` | Shared team directory (setgid, see below) |

**Key terms**

| Term | Meaning |
|------|---------|
| `chmod -R` | Recursive — dangerous: applies file modes to directories and vice versa |
| `X` (capital) | Execute only on directories (and files already executable): `chmod -R u=rwX,go=rX DIR` |
| `chown USER:GROUP` | Change both; `chown :GROUP` changes only the group |
| `chown -h` | Change the symlink itself instead of its target (`chmod` has no such option on Linux: symlink modes are ignored) |

**See it on a real system**

```bash
stat -c '%a %U:%G %n' /etc/ssh/ssh_host_*_key /etc/ssh/sshd_config
find /var/www -maxdepth 2 -printf '%m %u:%g %p\n' | head
```

```
600 root:root /etc/ssh/ssh_host_ecdsa_key
600 root:root /etc/ssh/ssh_host_ed25519_key
600 root:root /etc/ssh/ssh_host_rsa_key
644 root:root /etc/ssh/sshd_config
```

→ Private host keys are 600. sshd refuses to use keys that are readable by others —
many daemons do the same for secrets.

> ⚠️ **Never** `chmod -R 777` to "fix" a permission error — it hides the real cause and
> opens the files to every user and every compromised process. Never run `chown -R` or
> `chmod -R` on a path you built from a variable without checking it (an empty
> variable turns `/$DIR` into `/`). Safer: fix files and directories separately with
> `find`, and look first.

```bash
# Safer recursive fix: look, then change directories and files separately
find /srv/site -maxdepth 2 -printf '%m %u:%g %p\n'
sudo find /srv/site -type d -exec chmod 755 {} +
sudo find /srv/site -type f -exec chmod 644 {} +
sudo chown -R root:www-data /srv/site       # only after checking the path is right
```

**Hands-on lab (test VM only)**

**Step 1.** Create `/srv/app/config/app.env` containing `DB_PASSWORD=lab`, owned
`root:www-data`, mode 640. Confirm `sudo -u www-data cat` works and your normal user
can't read it.

**Step 2 — Break.** Run `sudo chmod 600 /srv/app/config/app.env`. Now the app user
can't read its own config. Reproduce with `sudo -u www-data cat`.

**Step 3 — Fix** with `sudo chmod 640` and explain to yourself why 640 + group
`www-data` is better than 644 (secrets shouldn't be world-readable) and better than
`chown www-data` (the app shouldn't be able to rewrite its own config).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `WARNING: UNPROTECTED PRIVATE KEY FILE!` from ssh | `ls -l ~/.ssh/id_ed25519` → `chmod 600` | Section 10 |
| App can't read its `.env` after a deploy | `ls -l FILE` — deploy tool rewrote mode or owner | Section 12, [CI/CD](33-learn-cicd-iac-sre.md) |
| Script runs by hand, "Permission denied" from systemd | `ls -l` the script, `namei -l` its path, the unit's `User=` | Section 6 |

**Why it matters for troubleshooting**

Most permission incidents are created by a well-meant `chmod -R` or a deploy that
ran as the wrong user. Knowing the "right" mode for each kind of file lets you spot
the wrong one at a glance.

**Next step**

umask — why new files get the permissions they get.

### umask and default permissions

**Level:** [L0 · Fresher]

**Concept**

New files start from `666` (files) or `777` (directories) and the **umask** removes
bits. umask `022` → files `644`, dirs `755`. umask `002` → `664`/`775` (group can
write). umask `077` → `600`/`700`. Each process has its own umask, inherited from its
parent: your shell, a cron job and a systemd service can all have different ones.

**Key terms**

| Term | Meaning |
|------|---------|
| umask | Bits to remove from the default mode of new files |
| `UMask=` | systemd unit setting (default `0022` for services) |
| pam_umask / `/etc/login.defs` | Where login sessions get their umask on Ubuntu |
| User private groups | Each user has their own group, which is why Ubuntu users often get umask `0002` |

**See it on a real system**

```bash
umask                         # your shell's umask, e.g. 0002 (user) or 0022 (root)
umask -S                      # symbolic form: u=rwx,g=rwx,o=rx
grep -E '^UMASK|^USERGROUPS_ENAB' /etc/login.defs
systemctl show -p UMask apache2
```

```
$ umask; umask -S
0002
u=rwx,g=rwx,o=rx
$ systemctl show -p UMask apache2
UMask=0022
```

**Hands-on lab (test VM only)**

**Step 1.** In a shell run `umask 077; touch /tmp/u-test; ls -l /tmp/u-test` → `-rw-------`.

**Step 2 — Break.** Simulate a deploy script that runs with umask 077 and writes a
file the web server must read. Like most deploy tools it writes a new file and moves it
into place — umask only applies when a file is **created**; overwriting an existing
file with `>` keeps its old mode:

```bash
sudo bash -c 'umask 077; echo "<h1>v2</h1>" > /srv/site/index.html.new && mv /srv/site/index.html.new /srv/site/index.html'
sudo -u www-data cat /srv/site/index.html     # Permission denied → users see 403
```

**Step 3 — Fix.** Either set `umask 022` at the top of the deploy script, or use
`install -m 644 SRC DEST`, which sets the mode explicitly regardless of umask.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Files created by a cron job/CI runner unreadable by the app | `ls -l` new files, check the job's umask | Sections 11 and 12 |
| Uploaded files from a web app unreadable by the other container | `ls -ln` on the volume, the app's `UMask=`/umask | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

"It works when I copy the file by hand but not when the pipeline deploys it" is very
often a umask difference. `install -m` and explicit `chmod` in scripts remove the
guesswork.

**Next step**

The three special bits: setuid, setgid and sticky.

### Special bits: setuid, setgid and sticky

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

A fourth octal digit in front of the mode holds three special bits:

| Bit | Octal | On a file | On a directory | Shows as |
|-----|-------|-----------|----------------|----------|
| setuid | 4000 | Runs with the **file owner's** UID (`passwd` runs as root) | (ignored) | `s` in user x position |
| setgid | 2000 | Runs with the file's group | New files **inherit the directory's group** | `s` in group x position |
| sticky | 1000 | (ignored) | Only a file's owner (or root) can delete/rename it — `/tmp` | `t` in other x position |

A capital `S` or `T` means the special bit is set but the matching `x` is not — almost
always a mistake. Linux ignores setuid on scripts (`#!`) for security.

**Key terms**

| Term | Meaning |
|------|---------|
| setuid binary | A privilege escalation point — audit them |
| `nosuid` mount option | Makes the kernel ignore setuid/setgid on that filesystem |
| Shared directory pattern | setgid dir + group-writable files (umask 002) |

**See it on a real system**

```bash
ls -ld /tmp /usr/bin/passwd /usr/bin/sudo
sudo find / -xdev -perm -4000 -type f 2>/dev/null     # every setuid file on this filesystem
findmnt -no OPTIONS /tmp                              # nosuid? noexec?
```

```
$ sudo find / -xdev -perm -4000 -type f 2>/dev/null
/usr/bin/passwd
/usr/bin/sudo
/usr/bin/mount
/usr/bin/su
/usr/bin/chsh
/usr/bin/gpasswd
/usr/bin/newgrp
/usr/bin/umount
/usr/bin/chfn
/usr/lib/openssh/ssh-keysign
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
```

→ Save this list on a clean server. A new setuid file in `/tmp`, `/home` or `/var/www`
during an incident is a red flag for compromise.

**Hands-on lab (test VM only)**

**Step 1 — Build a shared team directory.**

```bash
sudo groupadd webdev
sudo usermod -aG webdev "$USER"          # then log out and back in before the touch below (not newgrp: it would change your primary group and spoil step 2)
sudo mkdir -p /srv/shared
sudo chown root:webdev /srv/shared
sudo chmod 2775 /srv/shared              # setgid: new files get group webdev
touch /srv/shared/a.txt && ls -l /srv/shared/a.txt     # group = webdev
```

**Step 2 — Break.** `sudo chmod g-s /srv/shared`, create `b.txt`, and see that its
group is now your personal group: colleagues in `webdev` can no longer edit it.

**Step 3 — Fix.** Restore with `sudo chmod g+s /srv/shared` and repair the stray
file with `sudo chgrp webdev /srv/shared/b.txt`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Team members can't edit each other's files | `ls -ld DIR` (setgid?), `umask` (002?) | This topic |
| "Operation not permitted" deleting a file in `/tmp` you can write to | Sticky bit — only the owner can delete | — |
| A setuid helper stopped working after a move | `findmnt -T PATH` → `nosuid` | Section 8 |

**Why it matters for troubleshooting**

Shared deploy directories, log directories and upload folders depend on setgid and
group modes. Security audits always start with the setuid list.

**Next step**

ACLs and file attributes — when classic permissions aren't the whole story.

### ACLs and file attributes

**Level:** [L1 · Junior]

**Concept**

POSIX **ACLs** add extra entries ("user `deploy` may also read") beyond the
owner/group/other triplet. A `+` after the mode in `ls -l` tells you an ACL exists.
The ACL **mask** caps what named users and groups can get. **Default ACLs** on a
directory are inherited by new files — essential when files are created later, for
example by logrotate. Separately, **file attributes** like immutable (`chattr +i`)
block changes even for root.

**Key terms**

| Term | Meaning |
|------|---------|
| `getfacl` / `setfacl` | Read / change ACLs |
| mask | Upper limit for named entries; `chmod g=` on an ACL file changes the mask |
| Default ACL (`-d`) | Template inherited by new files in a directory |
| `chattr +i` / `lsattr` | Immutable flag: no write, delete or rename, even by root |
| `chattr +a` | Append-only (useful for some logs) |

**See it on a real system**

```bash
getfacl /var/log/apache2 2>/dev/null
lsattr /etc/resolv.conf 2>/dev/null       # some admins replace the symlink with a file and "pin" it with +i — a trap (lsattr prints nothing for the default symlink)
ls -l /var/log/journal/                   # journal dirs often carry ACLs (note the +)
```

```
$ getfacl /var/log/journal/
# file: var/log/journal/
# owner: root
# group: systemd-journal
# flags: -s-
user::rwx
group::r-x
group:adm:r-x
mask::r-x
other::r-x
default:user::rwx
default:group::r-x
default:group:adm:r-x
default:mask::r-x
default:other::r-x
```

→ The journal grants the `adm` group read access through an ACL, with a default ACL
so new journal files inherit it. Same pattern you'd use for any log directory.

**Hands-on lab (test VM only)**

**Step 1 — Give one user read access to Apache logs without the adm group.**

```bash
sudo adduser --disabled-password --gecos "" auditor               # 24.04 prefers --comment ""; --gecos is deprecated there
sudo setfacl -m u:auditor:rx /var/log/apache2                        # the directory
sudo sh -c 'setfacl -m u:auditor:r /var/log/apache2/*.log'           # existing files (glob expanded as root)
sudo setfacl -d -m u:auditor:r /var/log/apache2                       # template for files created later
sudo -u auditor tail -n 2 /var/log/apache2/access.log
```

**Step 2 — Break.** Remove the default ACL (`sudo setfacl -k /var/log/apache2`), then
simulate a new vhost's log file appearing:

```bash
sudo install -m 640 -o root -g adm /dev/null /var/log/apache2/app2-access.log
sudo -u auditor cat /var/log/apache2/app2-access.log      # Permission denied
getfacl /var/log/apache2/app2-access.log                  # no user:auditor entry
```

Brand-new files only get extra access from the directory's **default** ACL.

**Step 3 — Fix.** Re-add the default ACL, delete and recreate `app2-access.log`, and
confirm `auditor` can read it. Then try the immutable trap:

```bash
sudo chattr +i /srv/site/index.html
sudo rm /srv/site/index.html              # "Operation not permitted" — even as root
lsattr /srv/site/index.html               # ----i---------e------- shows the i flag
sudo chattr -i /srv/site/index.html
```

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Access works for some files in a dir, not for new ones | `getfacl DIR` — missing default ACL | This topic |
| "Operation not permitted" as root | `lsattr FILE` (immutable), then SELinux/AppArmor | Section 16 |
| resolv.conf never updates, DNS changes ignored | `lsattr /etc/resolv.conf` → remove `+i`, fix the real config | Section 9, [DNS](08-dns.md) |
| ACL entry present but no effect | `getfacl` shows `#effective:` limited by mask | This topic |

**Why it matters for troubleshooting**

When `ls -l` "looks right" and access still fails, the answer is in one of four
places: ACLs, attributes, mount options, or the MAC layer (SELinux/AppArmor). Check
them in that order.

**Next step**

Users and groups — who those owners actually are.

---

## 3. Users, groups and sudo

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (the accounts lessons) ([course](https://kodekloud.com/courses/the-linux-basics-course)), then *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Users and Groups ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: this section, then [Users, permissions & security](10-users-permissions-security.md) · 3) Video: skip — the labs teach more · 4) Practice: create a sudo user with key-only SSH (the L0 exit-test task in section 10)

### The account files: passwd, shadow and group

**Level:** [L0 · Fresher]

**Concept**

Local accounts live in three text files. `/etc/passwd` (world-readable) maps names to
UIDs, primary groups, homes and shells. `/etc/shadow` (root only) holds password
hashes and ageing. `/etc/group` lists groups and their extra members. Always query
them with `getent`, which also sees LDAP/SSSD users that never appear in the files.

```
/etc/passwd   deploy:x:1001:1001:Deploy User,,,:/home/deploy:/bin/bash
              │      │ │    │    │                │            └─ login shell (/usr/sbin/nologin = no login)
              │      │ │    │    │                └─ home directory
              │      │ │    │    └─ GECOS comment (full name)
              │      │ │    └─ primary GID
              │      │ └─ UID (0 = root, 1–999 system accounts, 1000+ people on Ubuntu)
              │      └─ "x" = the hash is in /etc/shadow
              └─ user name

/etc/shadow   deploy:$y$j9T$Vb3...$Qe8...:20729:0:99999:7:::
              │      │                    │     │ │     │ │││
              │      │                    │     │ │     │ ││└─ reserved
              │      │                    │     │ │     │ │└─ account expiry (days since 1970)
              │      │                    │     │ │     │ └─ inactive days after the password expires
              │      │                    │     │ │     └─ warn days
              │      │                    │     │ └─ max days between changes
              │      │                    │     └─ min days between changes
              │      │                    └─ last change (days since 1970-01-01)
              │      └─ hash: $y$ yescrypt (Ubuntu 22.04+), $6$ SHA-512 (RHEL); "!" prefix = locked; "*" = no password
              └─ user name

/etc/group    sudo:x:27:ops,deploy
              │    │ │  └─ supplementary members (comma-separated)
              │    │ └─ GID
              │    └─ password placeholder
              └─ group name
```

**Key terms**

| Term | Meaning |
|------|---------|
| UID / GID | Numeric IDs — the kernel only knows numbers; names are a lookup |
| Primary group | The GID in `/etc/passwd`, used for new files |
| Supplementary groups | Extra memberships from `/etc/group` |
| System account | UID below 1000, usually with `nologin` shell (`www-data` is UID 33) |
| NSS | Name Service Switch (`/etc/nsswitch.conf`): where names are looked up (files, sss, ldap) |

**See it on a real system**

```bash
getent passwd www-data deploy
getent group sudo docker adm
id deploy                       # UID, primary group, all groups
sudo getent shadow deploy       # root only
sudo chage -l deploy            # password ageing in readable form
awk -F: '$3 >= 1000 && $3 < 65534 {print $1, $3, $7}' /etc/passwd   # human accounts
```

```
$ getent passwd www-data
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
$ id deploy
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),4(adm),27(sudo),988(docker)
```

→ `deploy` is in `docker`: that is root-equivalent (anyone who can run containers can
mount `/` into one). Treat docker group membership like sudo.

**Hands-on lab (test VM only)**

**Step 1.** Create `labuser` with `sudo adduser labuser`, then find it in all three
files with `getent`.

**Step 2 — Break.** `sudo usermod -s /usr/sbin/nologin labuser`, then
`su - labuser` → "This account is currently not available."

**Step 3 — Fix** with `sudo usermod -s /bin/bash labuser`. Then learn the trap:
`sudo usermod -L labuser` (lock password) does **not** stop SSH key logins on a
default Ubuntu server. To really disable an account use
`sudo usermod -L -e 1 labuser` (lock + expire) and check with `sudo chage -l labuser`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `This account is currently not available.` | `getent passwd USER` (shell = nologin) | This topic |
| "Your account has expired; please contact your system administrator" | `sudo chage -l USER` | [Users reference](10-users-permissions-security.md) |
| Files show a number instead of a name in `ls -l` | The UID has no account here (e.g. container UID on a bind mount) | [Docker](30-learn-docker.md) |
| Departed employee can still SSH with a key | Password lock isn't enough: expire the account, remove `authorized_keys` | Section 10 |

**Why it matters for troubleshooting**

Permission problems are UID problems in disguise: containers, NFS and bind mounts
compare numbers, not names. Reading these three files fluently tells you who a
service really runs as.

**Next step**

Creating and changing users and groups safely.

### Creating and managing users and groups

**Level:** [L0 · Fresher]

**Concept**

Debian/Ubuntu have two tools: `adduser` (friendly, creates home, asks for a password)
and `useradd` (low-level, does exactly what the flags say — without `-m` no home,
without `-s` the shell comes from `/etc/default/useradd`, traditionally `/bin/sh` on
Ubuntu; `useradd -D` prints the defaults on your system). Group membership is read **at login**:
adding yourself to a group doesn't affect shells that are already open.

**Key terms**

| Command | What it does |
|---------|--------------|
| `adduser NAME` | Interactive human account (Debian/Ubuntu) |
| `useradd -m -s /bin/bash NAME` | Same, non-interactive (RHEL default tool) |
| `useradd --system --no-create-home --shell /usr/sbin/nologin svc-app` | Service account |
| `usermod -aG GROUP USER` | **Append** to a group — without `-a` you **replace** all groups |
| `gpasswd -d USER GROUP` | Remove a user from one group |
| `newgrp GROUP` / log out-in | Activate a new membership |
| `userdel -r` / `deluser --remove-home` | Delete account **and its home** |

**See it on a real system**

```bash
id                        # your CURRENT session's groups
id "$USER"                # what the account database says now
grep -E '^(SHELL|CREATE_HOME)' /etc/default/useradd /etc/login.defs 2>/dev/null
```

→ If `id` and `id "$USER"` differ, you were added to a group after you logged in.

**Hands-on lab (test VM only)**

> ⚠️ Keep a hypervisor console logged in as another sudo user (or root) before this
> lab: step 2 removes your own sudo rights on purpose.

**Step 1.** Create `ops1` with `sudo adduser ops1` and `sudo usermod -aG sudo ops1`.
Log in as `ops1` and run `sudo -v`.

**Step 2 — Break the classic way.** As your admin user run
`sudo usermod -G adm ops1` (no `-a`; `adm` exists on every Ubuntu, `docker` only once
Docker is installed). Run `id ops1`: the `sudo` group is gone. In a
new `ops1` login `sudo -v` fails with "ops1 is not in the sudoers file".

**Step 3 — Fix** from your other admin session: `sudo usermod -aG sudo ops1`.
Then remember the deletion warning:

> ⚠️ `userdel -r USER` / `deluser --remove-home USER` deletes the home directory and its
> data permanently. Safer first: `sudo usermod -L -e 1 USER` (disable), archive the home
> (`sudo tar -czf /root/USER-home.tgz /home/USER`), and delete later.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| "permission denied while trying to connect to the Docker daemon socket" right after `usermod -aG docker` | `id` vs `id USER` → log out/in or `newgrp docker` | [Docker](30-learn-docker.md) |
| User lost sudo after a group change | `id USER` (forgot `-a`) | This topic |
| Service account can log in interactively | `getent passwd USER` → set `/usr/sbin/nologin` | Section 16 |

**Why it matters for troubleshooting**

Most "I added them to the group but it still fails" tickets are about sessions that
predate the change — including long-running services, which must be restarted to pick
up new groups.

**Next step**

sudo — giving exactly the privilege needed, and nothing more.

### sudo and the sudoers file

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

`sudo` runs a command as another user (root by default) if a rule in
`/etc/sudoers` or `/etc/sudoers.d/*` allows it, and logs every use. A rule reads:
**who** may run, on **which host**, **as whom**, **which commands**. Ubuntu grants
full sudo to the `sudo` group; RHEL uses `wheel`. Always edit with `visudo`, which
refuses to save a broken file — a syntax error in sudoers disables sudo completely.

```
 %sudo    ALL   =  (ALL:ALL)   ALL
  │        │        │    │      └─ commands allowed
  │        │        │    └─ as which group
  │        │        └─ as which user
  │        └─ on which host (ALL in practice)
  └─ who (% = a group)

 deploy  ALL=(root) NOPASSWD: /usr/bin/systemctl restart myapp.service
         ↑ a narrow rule: one exact command, no password (for a CI job or a script)
```

**Key terms**

| Term | Meaning |
|------|---------|
| `visudo` / `visudo -f /etc/sudoers.d/FILE` | Safe editors with syntax check |
| `visudo -c` | Check all sudoers files |
| `sudo -l` | What may I run here? |
| `sudo -i` | Login shell as root (root's environment) |
| `sudo -s` | Root shell keeping much of your environment |
| `secure_path` | The PATH sudo uses, regardless of yours |
| Ignored drop-ins | Files in `/etc/sudoers.d` whose name contains a `.` or ends in `~` are **skipped** |

**See it on a real system**

```bash
sudo -l                                    # your rights
sudo visudo -c                             # syntax check every file
ls -l /etc/sudoers.d/
sudo grep -h 'sudo:' /var/log/auth.log | tail -5     # or: journalctl _COMM=sudo -n 20
```

```
$ sudo -l
Matching Defaults entries for deploy on web01:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User deploy may run the following commands on web01:
    (ALL : ALL) ALL
$ journalctl _COMM=sudo -n 2 --no-pager
Oct 03 09:12:40 web01 sudo[48211]:   deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/usr/bin/systemctl stop apache2
Oct 03 09:12:40 web01 sudo[48211]: pam_unix(sudo:session): session opened for user root(uid=0) by deploy(uid=1001)
```

→ The sudo log is your audit trail: "who stopped Apache at 09:12?" is one command.

**Hands-on lab (test VM only)**

> ⚠️ Keep a root console open (hypervisor) during this lab.

**Step 1 — Narrow rule.**

```bash
sudo visudo -f /etc/sudoers.d/ops1-restart
# add this single line, then save:
# ops1 ALL=(root) NOPASSWD: /usr/bin/systemctl restart apache2.service
sudo -l -U ops1                       # verify what ops1 may run
```

**Step 2 — Break.** Write a file *without* visudo containing a typo, e.g.
`echo 'ops1 ALL=(root NOPASSWD: ALL' | sudo tee /etc/sudoers.d/broken`. The next
`sudo` command prints something like:

```
>>> /etc/sudoers.d/broken: syntax error near line 1 <<<
sudo: parse error in /etc/sudoers.d/broken near line 1
sudo: no valid sudoers sources found, quitting
sudo: unable to initialize policy plugin
```

The exact wording varies by sudo version: the sudo 1.9 releases in Ubuntu 22.04/24.04
report the position as `/etc/sudoers.d/broken:1:N: syntax error` and print the bad line
with a caret under it. The last two lines are the same — sudo refuses to run at all.

**Step 3 — Fix** from the root console (`rm /etc/sudoers.d/broken`), or, if polkit is
installed, `pkexec visudo -f /etc/sudoers.d/broken`. On a real server without a root
console you'd need recovery mode (section 7). Then name a test file
`/etc/sudoers.d/ops1.conf` and notice it is silently ignored — the dot.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `USER is not in the sudoers file.` | `id USER` (group membership), `sudo -l -U USER` from another admin | [Users reference](10-users-permissions-security.md) |
| `sudo: parse error in /etc/sudoers.d/X` | Root console / recovery mode, then `visudo -c` | Section 7 |
| Rule in sudoers.d has no effect | File name contains `.` or ends in `~`; `visudo -c` | This topic |
| `sudo: unable to resolve host HOSTNAME` | `/etc/hosts` lacks the hostname | [DNS](08-dns.md) |

**Why it matters for troubleshooting**

CI jobs and deploy users need *some* root actions (restart a unit, reload a proxy).
A narrow NOPASSWD rule is safer than handing out full sudo or the docker group, and
the sudo log tells you who changed what during an incident.

**Next step**

Processes — what actually runs when you start a service.

---

## 4. Processes, signals and jobs

> 📚 **Study path:** 1) Note: this section, then [Processes reference](05-processes.md) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment: Diagnose and Manage Processes ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) · 3) Read (optional): [Linux debugging tools zine](https://wizardzines.com/zines/debugging/) (free) · 4) Practice: two [SadServers](https://sadservers.com/scenarios) easy scenarios

### What a process is: PID, parent, fork and exec

**Level:** [L0 · Fresher]

**Concept**

A process is a running program: code plus memory, open files, a user identity,
an environment and a current directory. Every process has a **PID** and a parent
(**PPID**). New processes are made by `fork()` (copy myself) followed by `exec()`
(become another program). PID 1 is `systemd`; every service you run is somewhere in
its tree. Daemons like Apache start as root, bind privileged ports (below 1024), then
spawn worker children that run as an unprivileged user.

```
systemd (PID 1)
├─ sshd: listener (PID 901)
│  └─ sshd: deploy [priv] → sshd: deploy@pts/0 → bash → top      ← your session
├─ apache2 -k start (PID 1123, root)      ← binds :80/:443, reads config, never serves
│  ├─ apache2 (PID 1124, www-data)        ← workers that answer requests
│  └─ apache2 (PID 1125, www-data)
└─ containerd / dockerd
   └─ containerd-shim → your container's PID 1
```

**Key terms**

| Term | Meaning |
|------|---------|
| PID / PPID | Process ID / parent's PID |
| Orphan | Process whose parent died; re-parented to PID 1 (or a "subreaper" such as `systemd --user`) |
| Thread | Execution unit inside a process, sharing its memory (`ps -L` shows them) |
| RSS / VSZ | Resident memory actually in RAM / virtual size reserved |
| `etime` | Elapsed time since start — "did this restart recently?" |

**See it on a real system**

```bash
ps -o pid,ppid,user,stat,etime,cmd -C apache2      # one program's processes
pstree -p -u | less                                # whole tree with PIDs and user changes
pgrep -a -f 'python3 -m http.server'               # find by full command line
ps -eo pid,user,rss,etime,cmd --sort=-rss | head   # biggest memory users
ps -o unit= -p 1123                                # which systemd unit owns this PID?
```

```
$ ps -o pid,ppid,user,stat,etime,cmd -C apache2
    PID    PPID USER     STAT     ELAPSED CMD
   1123       1 root     Ss    12-03:14:55 /usr/sbin/apache2 -k start
   1124    1123 www-data S     12-03:14:55 /usr/sbin/apache2 -k start
   1125    1123 www-data Sl    12-03:14:55 /usr/sbin/apache2 -k start
$ ps -o unit= -p 1123
apache2.service
```

→ PPID 1 = started by systemd; `ps -o unit=` names the unit, which tells you how to
stop, start and read logs for it (section 6). This is step 2 of "who owns this port".

**Hands-on lab (test VM only)**

**Step 1 — Build a little tree.**

```bash
bash -c 'sleep 1000 & sleep 1000 & wait' &
pstree -p $!            # $! = PID of the last background job
```

**Step 2 — Break: orphan the children.** Kill only the parent bash:
`kill $!`. Run `pgrep -a sleep` and `ps -o pid,ppid,cmd -C sleep` — the sleeps
survive with a new PPID (PID 1 or your `systemd --user`).

**Step 3 — Fix/clean.** `pkill -x sleep` (exact name match). Lesson: killing a
parent does not kill its children — which is why systemd tracks services by cgroup,
not by PID (section 15).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| "Stopped" a script but its workers keep running | `pstree -p PID`, `systemd-cgls` | [Processes reference](05-processes.md) |
| Unknown process using CPU or a port | `ps -o pid,ppid,user,etime,cmd -p PID`, `ps -o unit= -p PID` | [Ports playbook](22-playbook-ports-inventory.md) |
| Service "restarts" every few minutes | `ps -o etime -p MAINPID`, `systemctl show -p NRestarts UNIT` | Section 6 |

**Why it matters for troubleshooting**

From any PID you can walk up to the parent and the unit, and from the unit to the
config and logs. That walk is the core of the L1 exit test.

**Next step**

Process states — the single letter that tells you whether a process is working,
waiting, stuck or dead.

### Process states: R, S, D, Z and T

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

The STAT column tells you what a process is doing *right now*. Most processes sleep
most of the time (S) — that's healthy. The interesting ones are **D** (stuck waiting on
I/O, cannot be killed, counts in load average) and **Z** (finished but not yet
collected by its parent).

```
            fork/exec
               │
               ▼
   ┌──────▶ R running/runnable ◀──────┐
   │           │        │             │
   │     waits for      waits for     │  SIGCONT
   │     event/socket   disk / NFS    │
   │           ▼        ▼             │
   │  S sleeping     D uninterruptible│        T stopped (Ctrl-Z, SIGSTOP, debugger)
   │  (interruptible)   (ignores signals,
   │           │         counts in load)
   └───────────┴────────┘
               │ exit()
               ▼
          Z zombie (exit code kept until the parent calls wait())
```

**Key terms**

| State | Meaning | What to do |
|-------|---------|------------|
| R | Running or waiting for a CPU | Many R → CPU saturation (`vmstat` r column) |
| S | Sleeping, waiting for an event (socket, timer) | Normal |
| D | Uninterruptible sleep, usually disk or NFS I/O | Find the device/mount; `kill -9` won't work |
| Z | Zombie: exited, parent hasn't reaped it | Fix or restart the **parent**; zombies use no memory, only a PID slot |
| T | Stopped by a signal or debugger | `kill -CONT PID` |
| I | Idle kernel thread | Ignore |

Extra STAT characters: `s` session leader, `l` multi-threaded, `+` foreground,
`<` high priority, `N` low priority.

**See it on a real system**

```bash
ps -eo stat= | cut -c1 | sort | uniq -c            # how many in each state
ps -eo state,pid,ppid,wchan:32,cmd | awk '$1=="D"' # stuck in I/O, and the kernel function
ps -eo state,pid,ppid,cmd | awk '$1=="Z"'          # zombies and their parents
grep State /proc/1123/status
```

```
$ ps -eo stat= | cut -c1 | sort | uniq -c
      2 D
     94 I
      1 R
    151 S
$ ps -eo state,pid,ppid,wchan:32,cmd | awk '$1=="D"'
D    48712    1 nfs_wait_bit_killable           /usr/bin/rsync -a /srv/ /mnt/backup/
D    48790 48701 nfs_wait_bit_killable          du -sh /mnt/backup
```

→ Two D processes, both waiting in an NFS function: the backup NFS server is slow or
gone. Load average will be high while CPU looks idle — the classic sign from the Ops
Ladder case library.

**Hands-on lab (test VM only)**

**Step 1 — Stopped.** Start `sleep 500`, press `Ctrl-Z`, then
`ps -o stat,pid,cmd -C sleep` → `T`. Resume with `bg` or `kill -CONT PID`.

**Step 2 — Break: make a zombie.**

```bash
python3 -c '
import os, time
if os.fork() == 0:
    os._exit(0)        # child exits immediately
time.sleep(300)        # parent never calls wait()
' &
ps -eo state,pid,ppid,cmd | awk '$1=="Z"'     # [python3] <defunct>
```

**Step 3 — Fix.** `kill -9` on the zombie does nothing (it's already dead). Kill the
**parent** (`kill %1`): the zombie is re-parented to PID 1, which reaps it at once.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| High load, CPU idle | `ps -eo state,pid,wchan:32,cmd | awk '$1=="D"'`, `iostat -xz 1` | [Slow system playbook](23-playbook-slow-system.md) |
| `kill -9` has no effect | State D (wait for I/O / fix storage) or Z (kill parent) | [Processes reference](05-processes.md) |
| Thousands of zombies, "fork: retry: Resource temporarily unavailable" | Find the parent (`ps -o ppid=`), restart it | [Kernel reference](13-kernel-system.md) |

**Why it matters for troubleshooting**

The state letter decides the next command: R → CPU tools, D → disk/NFS tools,
Z → the parent, T → someone stopped it. It saves you from killing the wrong thing.

**Next step**

Signals — how you (and systemd) ask processes to stop, reload or die.

### Signals and kill

**Level:** [L0 · Fresher]

**Concept**

A signal is a small message the kernel delivers to a process. Most can be caught and
handled (TERM: "please finish and exit"; HUP: "reload your config"). Two cannot be
caught: **KILL (9)** and **STOP (19)**. `systemctl stop` sends TERM, waits
`TimeoutStopSec` (default 90 s), then sends KILL. When a process dies from a signal,
shells and Docker report exit code **128 + signal number**.

| Signal | No. | Default meaning | Typical use |
|--------|-----|-----------------|-------------|
| HUP | 1 | Terminal hung up | Many daemons reload config on HUP |
| INT | 2 | Interrupt (Ctrl-C) | Exit code 130 |
| QUIT | 3 | Quit with core dump | Java prints a thread dump on QUIT |
| KILL | 9 | Kill immediately, uncatchable | Last resort; exit code 137 (also the OOM killer) |
| USR1 / USR2 | 10 / 12 | App-defined | Apache: USR1 = graceful restart; nginx: USR1 = reopen logs |
| TERM | 15 | Polite stop | `kill` default, `systemctl stop`, `docker stop`; exit code 143 |
| CONT / STOP | 18 / 19 | Resume / freeze | Pausing a process |

**Key terms**

| Term | Meaning |
|------|---------|
| `kill PID` | Sends TERM (not necessarily "kill") |
| `pkill` / `killall` | Signal by name/pattern — check matches with `pgrep -a` first |
| Graceful reload | Re-read config without dropping connections (`systemctl reload UNIT`) |
| Exit 137 / 143 | Died from KILL / TERM |

**See it on a real system**

```bash
kill -l                                 # list signal names and numbers
grep -E 'Sig(Cgt|Ign|Blk)' /proc/1123/status    # which signals the process catches/ignores (hex masks)
systemctl show -p KillMode,KillSignal,TimeoutStopUSec apache2
pgrep -a -f gunicorn                    # ALWAYS preview what pkill -f would match
```

```
$ systemctl show -p KillMode,KillSignal,TimeoutStopUSec apache2
KillMode=mixed
KillSignal=15
TimeoutStopUSec=1min 30s
```

→ Apache's packaged unit first runs `ExecStop=apachectl graceful-stop`; whatever is
still running then gets `KillMode=mixed` treatment: TERM to the main process only, and
after the timeout KILL to **every** process left in the unit's cgroup. The default for
units that don't set it, `KillMode=control-group`, sends TERM to every process in the
cgroup at once. Either way: no orphaned workers.

> ⚠️ `kill -9` gives the process no chance to flush data, release locks, remove PID
> files or close client connections; databases can need recovery afterwards. Safer
> order: `systemctl stop UNIT` (or `kill PID` = TERM), wait 10–30 s, check with
> `ps -p PID`, and only then `kill -9 PID`. Never `pkill -9 -f PATTERN` without
> running `pgrep -a -f PATTERN` first — `-f` matches anywhere in the command line,
> including your own SSH session's arguments.

**Hands-on lab (test VM only)**

**Step 1 — Build a script that handles signals.**

```bash
cat > ~/lab/sig.sh <<'EOF'
#!/usr/bin/env bash
trap 'echo "got TERM, cleaning up"; exit 0' TERM
trap 'echo "got HUP, reloading config"' HUP
echo "PID $$ running"
while true; do sleep 1; done
EOF
chmod +x ~/lab/sig.sh
~/lab/sig.sh &
```

**Step 2 — Send signals and read exit codes.**

```bash
kill -HUP %1        # prints "reloading", keeps running
kill %1; wait %1; echo "exit=$?"            # TERM handled → exit=0
~/lab/sig.sh & kill -KILL %1; wait %1; echo "exit=$?"   # lab only: exit=137, no cleanup message
```

**Step 3 — Break/fix understanding.** Remove the TERM trap, run it again and send
TERM: exit is now 143. That's the code `docker ps -a` and Kubernetes show when a
container is stopped by TERM; 137 when it was killed (or OOM-killed).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Container/pod "Exited (137)" | `docker inspect -f '{{.State.OOMKilled}}' CONTAINER`, `journalctl -k | grep -i oom` | [Memory](04-memory.md), [Docker](30-learn-docker.md) |
| `systemctl stop` takes 90 s | App ignores TERM; `journalctl -u UNIT` shows "State 'stop-sigterm' timed out. Killing." | Section 6 |
| Reload had no effect | App doesn't reload on HUP; check `ExecReload=` with `systemctl cat UNIT` | Section 6 |

**Why it matters for troubleshooting**

Exit codes 137 and 143 appear everywhere — Docker, Kubernetes, systemd. Knowing they
mean "killed by signal 9/15" points you straight at OOM, a probe, or someone's stop.

**Next step**

Jobs and sessions — why your command died when SSH dropped.

### Jobs, background work and sessions

**Level:** [L0 · Fresher]

**Concept**

Your interactive shell manages **jobs**: `&` starts one in the background, `Ctrl-Z`
stops the foreground job, `bg`/`fg` move it. When the terminal (SSH session) closes,
the shell sends **SIGHUP** to its jobs and they usually die. `nohup` makes a command
ignore HUP; tmux keeps a whole session alive. For anything that must keep running,
the right tool is a systemd unit — or `systemd-run` for a one-off.

**Key terms**

| Command | Purpose |
|---------|---------|
| `cmd &`, `jobs`, `fg %1`, `bg %1` | Job control in the current shell |
| `nohup cmd > out.log 2>&1 &` | Ignore HUP, survive logout |
| `disown %1` | Detach a running job from the shell |
| `tmux new -s NAME` / `tmux attach -t NAME` | Persistent terminal session |
| `systemd-run --unit=NAME CMD` | Run as a transient service: logs in the journal, survives logout |

**See it on a real system**

```bash
jobs -l
loginctl list-sessions             # who is logged in, and their sessions
systemctl list-units --type=service --all | grep run-   # transient units from systemd-run
```

**Hands-on lab (test VM only)**

**Step 1.** Run `sleep 900 &`, close SSH, reconnect, `pgrep -a sleep` → gone.

**Step 2.** Repeat with `nohup sleep 900 > /dev/null 2>&1 &` → survives.

**Step 3 — The production way.**

```bash
sudo systemd-run --unit=lab-reindex --property=Nice=10 /usr/bin/sleep 900
systemctl status lab-reindex --no-pager      # a real unit with a cgroup and logs
journalctl -u lab-reindex
sudo systemctl stop lab-reindex
```

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Long job "randomly" stopped overnight | `last -x`, was it tied to an SSH session? | This topic |
| Job started with `nohup` has no logs | Output went to `nohup.out` in the cwd, or `/dev/null` | — |
| Process started from a shell missing after reboot | Nothing starts it at boot — write a unit | Section 6 |

**Why it matters for troubleshooting**

Ad-hoc `nohup` processes are the "mystery apps" you find years later on a port with
no unit, no logs and no owner. On the Apache server inventory, these are the hardest
to identify. Use units so the next person (or you) can find them.

**Next step**

Priorities — making the important process win.

### Priorities: nice, renice and ionice

**Level:** [L1 · Junior]

**Concept**

When the CPU is contended, the scheduler favours processes with a lower **nice**
value (-20 highest priority, 19 lowest, default 0). `ionice` does the same for disk
I/O. Only root can raise priority (lower nice). Use it to keep backups and reindexing
from hurting the web server.

**Key terms**

| Term | Meaning |
|------|---------|
| nice / NI | Priority hint, -20..19 |
| PRI | Kernel's internal priority (shown by top) |
| `ionice -c3` | Idle I/O class: only gets disk when nobody else wants it |
| `Nice=`, `IOSchedulingClass=`, `CPUWeight=` | systemd unit equivalents |

**See it on a real system**

```bash
ps -eo pid,ni,pri,comm --sort=-ni | head
ionice -p 1123
systemctl show -p Nice,CPUWeight apache2
```

**Hands-on lab (test VM only)**

**Step 1.** Pin two CPU burners to one core with different nice values:

```bash
taskset -c 0 yes > /dev/null &
taskset -c 0 nice -n 15 yes > /dev/null &
top -p "$(pgrep -d, -x yes)"      # the niced one gets a small share of CPU 0
```

**Step 2.** `sudo renice -n -5 -p PID` on the niced one and watch the shares swap.

**Step 3 — Clean up** with `pkill -x yes` (check `pgrep -a -x yes` first).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Site slow every night at 02:00 | `sar -u`, `crontab -l`, `systemctl list-timers` — backup without nice/ionice | [Slow system playbook](23-playbook-slow-system.md) |
| `renice: failed to set priority ... Permission denied` | Only root can lower nice | — |

**Why it matters for troubleshooting**

Noisy neighbours on a shared VM (backups, log compression, CI builds) are a common
cause of "slow sometimes". Nice/ionice and systemd's `CPUWeight=` are the fix that
doesn't need new hardware.

**Next step**

/proc — the window into every process.

### The /proc filesystem

**Level:** [L1 · Junior]

**Concept**

`/proc` is a virtual filesystem the kernel generates on the fly. Each process has a
directory `/proc/PID/` describing it: its command line, environment, current
directory, open files, limits, memory and cgroup. System-wide files (`/proc/loadavg`,
`/proc/meminfo`, `/proc/cmdline`) and tunables (`/proc/sys/`) live there too. Almost
every tool (`ps`, `top`, `free`, `lsof`) is just a reader of `/proc`.

```
/proc/1123/
├── cmdline   full command line (NUL-separated)
├── environ   environment at start (NUL-separated, readable only by the owner and root)
├── cwd  →    current directory (symlink)
├── exe  →    the binary; "(deleted)" if upgraded on disk but not restarted
├── fd/       one symlink per open file / socket / pipe
├── status    state, PPid, Uid, VmRSS, Threads, signal masks
├── limits    effective ulimits (max open files!)
├── cgroup    which cgroup → which systemd unit or container
└── io        bytes read/written
```

**Key terms**

| Path | Answers |
|------|---------|
| `/proc/PID/cgroup` | Which unit or container does this PID belong to? |
| `/proc/PID/limits` | What limits does the *running* process really have? |
| `/proc/PID/fd/` | Which files and sockets does it have open? |
| `/proc/PID/environ` | Which environment variables did it start with? |
| `/proc/sys/` | Kernel tunables (section 15) |

**See it on a real system**

```bash
sudo cat /proc/1123/cgroup
sudo readlink /proc/1123/exe /proc/1123/cwd
sudo ls -l /proc/1123/fd | head
sudo grep -E 'Max open files|Max processes' /proc/1123/limits
sudo tr '\0' '\n' < /proc/1123/environ | grep -i -E 'apache|lang'
cat /proc/loadavg
```

```
$ sudo cat /proc/1123/cgroup
0::/system.slice/apache2.service
$ sudo cat /proc/2201/cgroup
0::/system.slice/docker-4f3c2a9e8b7d1c6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e.scope
$ sudo ls -l /proc/1123/fd | head -5
total 0
lr-x------ 1 root root 64 Oct  3 09:20 0 -> /dev/null
l-wx------ 1 root root 64 Oct  3 09:20 2 -> /var/log/apache2/error.log
lrwx------ 1 root root 64 Oct  3 09:20 3 -> socket:[23455]
lrwx------ 1 root root 64 Oct  3 09:20 4 -> socket:[23456]
$ sudo grep 'Max open files' /proc/1123/limits
Max open files            8192                 8192                 files
```

(Debian/Ubuntu's `apachectl` runs `ulimit -n 8192` before starting Apache, hence 8192;
a service without such a wrapper shows systemd's default soft/hard pair, `1024` and
`524288`.)

→ PID 2201 belongs to a Docker container (the long ID is the container ID — match it
with `docker ps --no-trunc`). PID 1123 is the `apache2.service` unit.
→ fd 2 points at `error.log`: an open-files listing is how you find logs for an app
you don't know.

**Hands-on lab (test VM only)**

**Step 1.** Start a throwaway server: `cd /tmp && python3 -m http.server 8090 &`.

**Step 2.** Answer from `/proc` only: its cwd, its binary, its open sockets (`ls -l
/proc/PID/fd`), its max open files and its cgroup. Compare with `ss -ltnp` and `lsof
-p PID`.

**Step 3 — Break.** Delete a running process's working directory:

```bash
mkdir /tmp/lab-cwd-test && cd /tmp/lab-cwd-test
python3 -m http.server 8091 > /dev/null 2>&1 &
pid=$!
cd /tmp && rmdir /tmp/lab-cwd-test     # empty directory, so rmdir is enough
readlink /proc/$pid/cwd                # /tmp/lab-cwd-test (deleted)
kill $pid
```

The same "(deleted)" marker on `/proc/PID/exe` after a package upgrade means the
process still runs the **old** binary — restart it to get the fix.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| "Too many open files" | `sudo ls /proc/PID/fd | wc -l` vs `grep 'open files' /proc/PID/limits` | Section 15 |
| Security fix installed but still vulnerable | `sudo ls -l /proc/*/exe 2>/dev/null | grep deleted` (or `needrestart -r l`) | Section 16 |
| "Which container is this PID?" | `cat /proc/PID/cgroup` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting**

`/proc/PID/cgroup` answers "which unit or container is this?" for any process, and
`/proc/PID/fd` answers "which log file is it writing?". Together they turn an unknown
process on a port into a named app with known logs.

**Next step**

Package management — the other way to find out what something is and where it
came from.

---

## 5. Package management

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 2) Note: this section, then [Packages reference](11-packages.md) · 3) Video: skip · 4) Practice: the nginx-versus-Apache port-conflict lab below on the KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu)

### apt, dpkg and repositories

**Level:** [L0 · Fresher]

**Concept**

On Ubuntu, **dpkg** installs individual `.deb` files and keeps the database of what is
installed (`/var/lib/dpkg/`). **apt** sits on top: it downloads package lists from
**repositories**, resolves dependencies, and calls dpkg. Repositories are signed;
apt trusts a repo only if it has the matching key.

```
 /etc/apt/sources.list.d/*.sources|*.list ──▶ apt update ──▶ package lists (/var/lib/apt/lists)
                                                                  │
 apt install apache2 ──▶ resolve dependencies ──▶ download .debs (/var/cache/apt/archives)
                                                                  │
                                                       dpkg -i → files on disk,
                                                       maintainer scripts (start the service!),
                                                       record in /var/lib/dpkg/status
```

Ubuntu 24.04 uses the deb822 format in `/etc/apt/sources.list.d/ubuntu.sources`;
22.04 uses `/etc/apt/sources.list`. Third-party repos (Docker, Kubernetes, GitLab
Runner) get their own file plus a key in `/etc/apt/keyrings/`, referenced with
`signed-by`.

**Key terms**

| Command | Meaning |
|---------|---------|
| `apt update` | Refresh package lists (installs nothing) |
| `apt upgrade` | Upgrade installed packages; installs new dependencies if needed, never removes any (`apt-get upgrade` adds nothing new) |
| `apt full-upgrade` | Upgrade, also removing packages when an upgrade needs it |
| `apt remove` / `apt purge` | Remove, keeping / deleting config files in `/etc` |
| `apt autoremove --purge` | Remove no-longer-needed dependencies (old kernels) |
| `apt policy PACKAGE` | Installed vs candidate version and which repo each comes from |
| `/var/log/apt/history.log` | What was installed/upgraded, when, by which command |

**See it on a real system**

```bash
cat /etc/apt/sources.list.d/ubuntu.sources       # 24.04 (22.04: /etc/apt/sources.list)
ls /etc/apt/sources.list.d/ /etc/apt/keyrings/
apt policy apache2
apt list --upgradable 2>/dev/null | head
zgrep -h -A1 '^Start-Date' /var/log/apt/history.log* | grep -E 'Start-Date|Commandline' | tail -10
```

```
$ cat /etc/apt/sources.list.d/ubuntu.sources
Types: deb
URIs: http://archive.ubuntu.com/ubuntu/
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
$ apt policy apache2
apache2:
  Installed: 2.4.58-1ubuntu8.4
  Candidate: 2.4.58-1ubuntu8.5
  Version table:
     2.4.58-1ubuntu8.5 500
        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
 *** 2.4.58-1ubuntu8.4 100
        100 /var/lib/dpkg/status
$ zgrep -h -A1 '^Start-Date' /var/log/apt/history.log* | grep -E 'Start-Date|Commandline' | tail -4
Start-Date: 2026-09-30  06:12:01
Commandline: /usr/bin/unattended-upgrade
Start-Date: 2026-10-02  14:20:33
Commandline: apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

→ `apt policy` shows an update is pending (candidate newer than installed) and where
each version comes from.

→ The history log answers "what changed on this box right
before it broke?" — the first question after any incident.

**Hands-on lab (test VM only)**

**Step 1.** Install and remove a package, watching the logs:
`sudo apt install -y tree`, then `tail -n 15 /var/log/apt/history.log`, then
`sudo apt purge -y tree`.

**Step 2 — Break: port conflict during install.** With Apache running on port 80,
run `sudo apt install -y nginx`. On Ubuntu, package installs start the service
immediately. On 22.04 nginx can't bind 80 and the install reports an error:

```
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
...
dpkg: error processing package nginx-core (--configure):
 installed nginx-core package post-installation script subprocess returned error exit status 1
```

On 24.04 the nginx package checks the port first, prints
`Not attempting to start NGINX, port 80 is already in use.` and finishes the install
with nginx **stopped** — the conflict only bites when you run
`sudo systemctl start nginx` and get the same `bind() ... (98: Address already in use)`
in `journalctl -u nginx`.

**Step 3 — Fix.** Find the holder (`sudo ss -ltnp 'sport = :80'`), decide which server
should own 80, then either stop Apache or change nginx's `listen` port, and finish with
`sudo dpkg --configure -a` (22.04) or `sudo systemctl start nginx` (24.04). This is
the same conflict as Apache vs Traefik on 443 — see the
[case study](21-case-apache-443-dokploy.md).

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 2345 (unattended-upgr)` | Wait; `ps -fp 2345`; `tail -f /var/log/unattended-upgrades/unattended-upgrades.log`. **Never delete lock files** | [Packages reference](11-packages.md) |
| `NO_PUBKEY ...` or "repository is not signed" | `ls /etc/apt/keyrings/`, check the `signed-by` path | [Packages reference](11-packages.md) |
| `E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a'` | `sudo dpkg --configure -a` | [Packages reference](11-packages.md) |
| `Release file ... is not valid yet` | Clock is wrong: `timedatectl` | [Time & NTP](12-time-ntp.md) |
| Upgrade wants to remove many packages | Stop; read the list; `apt policy` the key ones | This topic |

**Why it matters for troubleshooting**

"What changed?" is the first question in every incident, and `history.log` plus
`dpkg.log` answer it for packages. The nginx-vs-Apache install error is a ten-second
diagnosis once you know installs start services.

**Next step**

Mapping files back to packages — the "what is this thing?" tool.

### Which package owns this file

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

dpkg knows every file every package installed. Given a binary path from `ps` or `ss`,
`dpkg -S` tells you which package it came from. If no package owns it, someone
installed it by hand (`/opt`, `/usr/local`, a home directory) or it lives in a
container — which changes how you upgrade, configure and remove it.

**Key terms**

| Ubuntu / Debian | RHEL / Rocky | Answers |
|-----------------|--------------|---------|
| `dpkg -S /path/file` | `rpm -qf /path/file` | Which package owns this file? |
| `dpkg -L PACKAGE` | `rpm -ql PACKAGE` | Which files does it install? |
| `apt-file search NAME` | `dnf provides '*/NAME'` | Which (not yet installed) package provides it? |
| `apt show PACKAGE` / `dpkg -s PACKAGE` | `rpm -qi PACKAGE` | Description, version, homepage |
| `dpkg -V PACKAGE` | `rpm -V PACKAGE` | Which packaged files were modified? |
| `apt-cache rdepends --installed PACKAGE` | `dnf repoquery --installed --whatrequires PACKAGE` | Who depends on it (safe to remove?) |

**See it on a real system**

```bash
dpkg -S "$(command -v apachectl)"
dpkg -S /opt/legacyapp/bin/server
dpkg -V apache2                       # config files you changed show up here
apt-cache rdepends --installed apache2-bin
```

```
$ dpkg -S /usr/sbin/apachectl
apache2: /usr/sbin/apachectl
$ dpkg -S /opt/legacyapp/bin/server
dpkg-query: no path found matching pattern /opt/legacyapp/bin/server
$ dpkg -V apache2
??5?????? c /etc/apache2/apache2.conf
??5?????? c /etc/apache2/ports.conf
```

→ `legacyapp` isn't packaged: look for its unit, deploy script or README in `/opt`.
→ `dpkg -V` shows `apache2.conf` and `ports.conf` were edited locally (5 = checksum
differs, c = config file). Those are the files to review before moving the workload.

**Hands-on lab (test VM only)**

**Step 1.** For every listening port on your VM (`sudo ss -ltnp`), take the process
name, find its binary (`readlink /proc/PID/exe`) and its package (`dpkg -S`).

**Step 2 — Break.** Edit `/etc/apache2/ports.conf` (add a comment), then run
`dpkg -V apache2` and see it reported.

**Step 3 — Fix/learn.** On `apt purge apache2` dpkg would delete those configs; on
`apt remove` it keeps them (state `rc` in `dpkg -l`). Check with
`dpkg -l | grep '^rc'`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Unknown binary listening on a port | `dpkg -S BINARY`, `ls -l /proc/PID/exe` | [Ports playbook](22-playbook-ports-inventory.md) |
| Packaged file corrupted/changed | `dpkg -V PACKAGE`, `sudo apt install --reinstall PACKAGE` | [Packages reference](11-packages.md) |
| "Removing X will remove Y and Z" surprise | `apt-cache rdepends --installed X` before removing | This topic |

**Why it matters for troubleshooting**

During the Apache inventory, `dpkg -S` and `dpkg -V` separate "packaged, edited
config" from "hand-installed mystery app", which tells you how much archaeology a
migration needs.

**Next step**

Holds and pinning — controlling when and to what version things upgrade.

### Holds, pinning and controlled upgrades

**Level:** [L1 · Junior]

**Concept**

Some packages must not change version on their own: Kubernetes components
(`kubeadm`, `kubelet`, `kubectl`, whose docs tell you to hold them), Docker Engine on a
production Swarm/Dokploy host, database servers. A **hold** freezes a package at its
current version. A **pin** (apt preferences) controls which version or repo wins.

**Key terms**

| Term | Meaning |
|------|---------|
| `apt-mark hold PACKAGE` / `unhold` / `showhold` | Freeze / unfreeze / list |
| `apt install PACKAGE=VERSION` | Install an exact version (`apt-cache madison PACKAGE` lists them) |
| Pin-Priority | 500 = normal repo, 100 = installed, 1000 or more = allow downgrade |
| `dnf versionlock add PACKAGE` | RHEL equivalent (plugin `python3-dnf-plugin-versionlock`) |

**See it on a real system**

```bash
apt-mark showhold
apt-cache madison docker-ce | head -3
apt-cache policy kubelet
```

```
$ apt-mark showhold
containerd.io
docker-ce
docker-ce-cli
kubeadm
kubectl
kubelet
$ apt-cache madison docker-ce | head -2
 docker-ce | 5:27.3.1-1~ubuntu.24.04~noble | https://download.docker.com/linux/ubuntu noble/stable amd64 Packages
 docker-ce | 5:27.3.0-1~ubuntu.24.04~noble | https://download.docker.com/linux/ubuntu noble/stable amd64 Packages
```

A pin file example:

```
# /etc/apt/preferences.d/docker-pin
Package: docker-ce docker-ce-cli
Pin: version 5:27.3.*
Pin-Priority: 1001
```

**Hands-on lab (test VM only)**

**Step 1.** `sudo apt-mark hold tree` (install it first), then `apt list --upgradable`
and `sudo apt upgrade` — held packages show as "kept back".

**Step 2 — Break (the automation failure).** With the hold in place, run
`sudo apt remove -y tree`. apt refuses:

```
E: Held packages were changed and -y was used without --allow-change-held-packages.
```

This is exactly how an Ansible play or a CI job fails on a host where someone held
packages. Without `-y` apt lists "The following held packages will be changed" and
asks first.

**Step 3 — Fix** with `sudo apt-mark unhold tree` (or pass
`--allow-change-held-packages` deliberately). Write down: a hold is a promise to
upgrade **deliberately** later, not "never".

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `The following packages have been kept back` | `apt-mark showhold`; a phased update (wait, or `apt install PACKAGE`); needs a removal → `apt full-upgrade` after reading what it removes | [Packages reference](11-packages.md) |
| `E: Unable to correct problems, you have held broken packages.` | `apt-mark showhold`, `apt policy` on the conflicting packages | [Packages reference](11-packages.md) |
| kubelet upgraded itself, cluster version skew | Hold missing; `apt-mark showhold` | [Kubernetes](31-learn-kubernetes.md) |
| Docker restarted at 06:00, all containers bounced | unattended-upgrades upgraded Ubuntu's `docker.io`/`containerd`/`runc` (or `docker-ce` if someone added Docker's repo to its allowed origins); hold or blacklist them | Section 16 |

**Why it matters for troubleshooting**

An unplanned Docker or kubelet upgrade is a self-inflicted outage. Holds turn
upgrades into change requests you schedule and can roll back.

**Next step**

The RHEL/Rocky equivalents, so you aren't lost on the other half of the fleet.

### dnf and rpm on RHEL and Rocky

**Level:** [L1 · Junior]

**Concept**

Same model, different names: **rpm** is the low-level installer and database,
**dnf** (formerly yum) resolves dependencies from repos in `/etc/yum.repos.d/`. dnf
keeps a transaction history you can undo.

**Key terms**

| Ubuntu | RHEL / Rocky |
|--------|--------------|
| `apt update && apt upgrade` | `dnf upgrade` (metadata refreshes automatically) |
| `apt install / remove` | `dnf install / remove` |
| `apt search` / `apt show` | `dnf search` / `dnf info` |
| `/var/log/apt/history.log` | `dnf history`, `dnf history info N` |
| (no direct undo) | `dnf history undo N` |
| `apt-mark hold` | `dnf versionlock add` |
| Universe / PPAs | EPEL (`dnf install epel-release`) |
| `apache2`, `/etc/apache2` | `httpd`, `/etc/httpd` |
| `ssh.service` | `sshd.service` |

**See it on a real system**

```bash
dnf history | head
dnf repolist
rpm -qa --last | head           # most recently installed packages
rpm -qf /usr/sbin/httpd
```

**Hands-on lab (test VM only)**

On the optional Rocky VM: install `httpd`, look at `dnf history`, then
`sudo dnf history undo last` and confirm it's gone. Break: disable the appstream repo
(`sudo dnf config-manager --set-disabled appstream`, needs `dnf-plugins-core`) and try
installing a package → "No match for argument". Fix by re-enabling it.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `Error: Failed to download metadata for repo` | `dnf repolist`, DNS/proxy, `curl -I` the baseurl | [Packages reference](11-packages.md) |
| `No match for argument: PACKAGE` | Repo disabled or package in EPEL | This topic |

**Why it matters for troubleshooting**

Clients rarely run one distro. Knowing the mapping lets you apply every Ubuntu habit
on RHEL without searching.

**Next step**

Snaps and installer scripts — the "other" ways software lands on a server.

### Snaps, install scripts and hand-installed software

**Level:** [L1 · Junior]

**Concept**

Not everything comes from apt. Ubuntu also uses **snaps** (self-contained packages
under `/snap` with data in `/var/snap`). Many tools — Dokploy included — install via a
`curl ... | sh` script that adds repos, installs Docker, initialises Swarm and
creates networks. Others are copied into `/opt` or `/usr/local`. Each source has its
own upgrade and removal path, and mixing two sources for the same tool (Docker from
snap **and** from Docker's apt repo) creates two daemons and endless confusion.

**Key terms**

| Source | How to see it |
|--------|---------------|
| apt/dpkg | `dpkg -l`, `dpkg -S` |
| snap | `snap list`, `snap services`, units named `snap.NAME.*` |
| Install script | Read it first; it usually logs what it did; look in `/etc/apt/sources.list.d/` and `docker ps` afterwards |
| By hand | `/opt/*`, `/usr/local/bin/*`, units in `/etc/systemd/system/` without a package |

**See it on a real system**

```bash
snap list 2>/dev/null
systemctl list-units --type=service | grep -E 'snap\.' 
ls /opt /usr/local/bin
type -a docker                    # more than one docker on PATH? (bash's command -v has no -a)
```

**Hands-on lab (test VM only)**

**Step 1.** Before running any install script, download it and read it:
`curl -fsSL URL -o install.sh; less install.sh`. List every system change it makes
(packages, repos, ports, firewall, Swarm init).

**Step 2 — Break (concept).** Install `docker` from snap on a VM that already has
docker-ce from apt; `type -a docker` and `systemctl list-units | grep -i docker`
show two of everything. Remove the snap (`sudo snap remove docker`) to fix.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `docker ps` shows different containers in different shells | `type -a docker`, `snap list` | [Docker](30-learn-docker.md) |
| Bind mounts from `/srv` or `/mnt` fail with snap Docker | Snap confinement limits paths | [Docker](30-learn-docker.md) |
| A tool updated itself overnight | `snap changes` (snaps auto-refresh) | This topic |

**Why it matters for troubleshooting**

When you inventory a server before a migration, "how was this installed?" decides how
you stop it, upgrade it and roll it back. Dokploy's installer also needs 80, 443 and
3000 free — the root of the original incident.

**Next step**

systemd — the thing that actually starts and supervises all of it.

---

## 6. systemd and journald

> 📚 **Study path:** 1) Note: this section, then [Services & systemd reference](07-services-systemd.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Service Management with SYSTEMD: Creating a SYSTEMD Service ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page)) and SYSTEMD Tools ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page)), then LFCS — Operations Deployment: Manage Startup Process and Services, Create systemd Services ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Video: *Linux for Beginners: systemd start/stop services & journalctl* by Sanjeev Thiyagarajan, a KodeKloud instructor ([YouTube](https://www.youtube.com/watch?v=jZfNVROoF74), 18 min) · 4) Practice: the Ops Ladder L1 drill in "Writing a service unit from scratch", with [Arch Wiki: systemd](https://wiki.archlinux.org/title/Systemd) open for drop-ins

### Units and where unit files live

**Level:** [L1 · Junior]

**Concept**

systemd is PID 1: it starts everything else at boot and supervises it afterwards.
Everything it manages is a **unit**, described by a small INI-style file. A service
unit says how to start a program; a socket unit holds a port; a timer unit triggers
another unit on a schedule; a mount unit mounts a filesystem; a target groups units
into a "state" such as multi-user.

```
 Where unit files come from (highest priority first)

 /etc/systemd/system/            ← YOURS: custom units, overrides (UNIT.d/*.conf)
 /run/systemd/system/            ← runtime, generated (lost at reboot)
 /usr/lib/systemd/system/        ← PACKAGES (/lib/systemd/system on older Ubuntu)

 systemctl cat UNIT  = the file that wins + every drop-in, in order
```

| Unit type | Example | What it does |
|-----------|---------|--------------|
| `.service` | `apache2.service` | Runs and supervises a process |
| `.socket` | `ssh.socket`, `docker.socket` | Holds a port/socket, starts the service on first connection |
| `.timer` | `logrotate.timer` | Starts a service on a schedule |
| `.target` | `multi-user.target` | A synchronisation point / group of units |
| `.mount` | `data.mount` | A mount point (generated from `/etc/fstab`) |
| `.path` | `foo.path` | Starts a service when a file changes |
| `.slice` / `.scope` | `system.slice`, `docker-ID.scope` | cgroup groupings for resource control |

**Key terms**

| Term | Meaning |
|------|---------|
| Unit file | The configuration (`[Unit]`, `[Service]`, `[Install]` sections) |
| Drop-in | A `UNIT.d/NAME.conf` file that overrides parts of a unit |
| Fragment path | The main file in use (`systemctl show -p FragmentPath UNIT`) |
| Generator | Program that creates units at boot (fstab → mount units, ssh socket) |

**See it on a real system**

```bash
systemctl status apache2 --no-pager
systemctl cat apache2
systemctl list-units --type=service --state=running
systemctl list-unit-files --state=enabled
systemctl show -p FragmentPath,DropInPaths,MainPID,NRestarts apache2
```

```
$ systemctl status apache2 --no-pager
● apache2.service - The Apache HTTP Server
     Loaded: loaded (/usr/lib/systemd/system/apache2.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-21 06:14:03 UTC; 1 week 5 days ago
       Docs: https://httpd.apache.org/docs/2.4/
    Process: 1110 ExecStart=/usr/sbin/apachectl start (code=exited, status=0/SUCCESS)
   Main PID: 1123 (apache2)
      Tasks: 55 (limit: 4558)
     Memory: 21.4M (peak: 38.0M)
        CPU: 3min 12.551s
     CGroup: /system.slice/apache2.service
             ├─1123 /usr/sbin/apache2 -k start
             ├─1124 /usr/sbin/apache2 -k start
             └─1125 /usr/sbin/apache2 -k start
```

How to read it, line by line:

| Line | Tells you |
|------|-----------|
| Loaded | Which file defines it; `enabled` = starts at boot; `preset` = distro default |
| Active | `active (running)`, `inactive (dead)`, `failed`, or `activating (auto-restart)` = crash loop |
| Process | Helper commands that ran (ExecStart via `apachectl`, which forks the real daemon) |
| Main PID | The process systemd watches |
| CGroup | **Every** process belonging to the unit — nothing escapes it |
| (bottom) | The last ~10 journal lines for the unit |

**Hands-on lab (test VM only)**

**Step 1.** For `ssh`, `cron`, `apache2` and `systemd-resolved`, run `systemctl cat`
and note the `ExecStart=`, `User=` (if any), and the `[Install]` `WantedBy=`.

**Step 2 — Break.** Copy the Apache unit to `/etc/systemd/system/` and change its
`Description=`. Run `systemctl status apache2` — systemd warns that the unit file
changed on disk. Run `sudo systemctl daemon-reload` and check `Loaded:` now points to
`/etc/systemd/system/apache2.service`.

**Step 3 — Fix.** Remove your copy (`sudo rm /etc/systemd/system/apache2.service`),
`sudo systemctl daemon-reload`, and confirm the package file is back in use. Lesson:
full copies in `/etc` silently stop receiving package fixes — use drop-ins instead.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `Warning: The unit file, source configuration file or drop-ins of UNIT changed on disk. Run 'systemctl daemon-reload'` | `sudo systemctl daemon-reload` | [systemd reference](07-services-systemd.md) |
| `Unit UNIT.service could not be found.` | `systemctl list-unit-files | grep -i NAME` (different name: `ssh` vs `sshd`, `apache2` vs `httpd`) | This topic |
| Your change has no effect | `systemctl cat UNIT` — another drop-in sorts later and wins | Drop-ins below |

**Why it matters for troubleshooting**

`systemctl status` + `systemctl cat` answer three of the four L1 exit-test questions
(which unit, which binary and arguments, where config comes from). The CGroup tree
shows every process the unit owns.

**Next step**

The lifecycle: start vs enable, stop vs disable vs mask — the exact verbs you need to
"dispatch" Apache safely.

### Service lifecycle: start, enable and mask

**Level:** [L1 · Junior]

**Concept**

Two independent questions: **is it running now?** (active/inactive — `start`, `stop`)
and **will it start at boot?** (enabled/disabled — `enable`, `disable`). **mask** goes
further: it links the unit to `/dev/null` so nothing can start it — not you, not a
dependency, not a package upgrade.

```
                 start ─────────▶            enable ──────▶
   inactive  ◀──────────── stop    active    disabled ◀── disable   enabled
   (now)                           (now)     (at boot)               (at boot)

   mask   = cannot be started at all (by anyone, by any dependency)
   unmask = undo mask (then enable/start as usual)

   enable --now = enable + start          disable --now = disable + stop
```

| Goal | Command | Rollback |
|------|---------|----------|
| Stop for now, back at next boot | `systemctl stop UNIT` | `systemctl start UNIT` |
| Stop now and at boot | `systemctl disable --now UNIT` | `systemctl enable --now UNIT` |
| Make sure nothing restarts it (another package, a dependency, a colleague) | `systemctl mask --now UNIT` | `systemctl unmask UNIT && systemctl enable --now UNIT` |
| Re-read config, keep connections | `systemctl reload UNIT` | — |
| Full restart | `systemctl restart UNIT` | — |

**Key terms**

| Term | Meaning |
|------|---------|
| active / inactive / failed | Runtime state |
| enabled / disabled / static / masked | Boot-time state; `static` = no `[Install]`, only started as a dependency |
| `daemon-reload` | Re-read unit files after editing them |
| `is-active`, `is-enabled`, `is-failed` | Script-friendly checks with exit codes |

**See it on a real system**

```bash
systemctl is-active apache2; systemctl is-enabled apache2
systemctl list-unit-files apache2.service docker.service ssh.service ssh.socket
ls -l /etc/systemd/system/multi-user.target.wants/ | head    # "enabled" = a symlink here
```

```
$ systemctl list-unit-files apache2.service docker.service ssh.service ssh.socket
UNIT FILE       STATE    PRESET
apache2.service enabled  enabled
docker.service  enabled  enabled
ssh.service     disabled enabled
ssh.socket      enabled  enabled

4 unit files listed.
```

→ On Ubuntu 24.04, `ssh.service` is disabled because `ssh.socket` starts it on demand
(socket activation, covered below).

**Hands-on lab (test VM only)**

**Step 1 — Dispatch Apache the reversible way.**

```bash
sudo systemctl disable --now apache2
systemctl is-active apache2; systemctl is-enabled apache2   # inactive / disabled
sudo ss -ltnp 'sport = :80'                                   # port is free now
```

**Step 2 — Break (why mask exists).** Run `sudo apt install --reinstall apache2`.
The package's maintainer script may start it again — check `systemctl is-active
apache2`. Now `sudo systemctl mask --now apache2` and try
`sudo systemctl start apache2`:

```
Failed to start apache2.service: Unit apache2.service is masked.
```

**Step 3 — Roll back** exactly as you would at a client:
`sudo systemctl unmask apache2 && sudo systemctl enable --now apache2`, then verify
with `curl -sI http://127.0.0.1/` and `ss -ltnp`. Write these three commands in the
change request **before** you stop anything in production.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Stopped service is running again after reboot | `systemctl is-enabled UNIT` (still enabled) | This topic |
| Stopped service came back after `apt upgrade` | Maintainer scripts start enabled services — `mask` it | This topic |
| `Unit UNIT is masked.` and nobody remembers why | `systemctl status UNIT`, `ls -l /etc/systemd/system/UNIT` (→ /dev/null) | Change log / ticket |
| Port still busy after `systemctl stop` | `ss -ltnp` — a socket unit or a container holds it | Socket units below, [Ports playbook](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting**

"Dispatching" Apache to free 443 for Traefik is `disable --now` (or `mask --now`)
plus a written rollback. Knowing the difference between stop, disable and mask is
what makes that change safe — see the [case study](21-case-apache-443-dokploy.md).

**Next step**

Dependencies and targets — why things start in the order they do.

### Dependencies, ordering and targets

**Level:** [L1 · Junior]

**Concept**

systemd starts units in parallel unless told otherwise. Two separate kinds of
relationships exist and people mix them up constantly: **requirement** (`Wants=`,
`Requires=`: "also start that") and **ordering** (`After=`, `Before=`: "if both are
starting, start that first"). `After=` alone does **not** pull anything in; `Wants=`
alone does **not** wait for it. You usually need both.

```
 multi-user.target  ─ wants ─▶ apache2.service, docker.service, cron.service, containerd.service ...
        ▲
 graphical.target (requires multi-user)   default.target → symlink to one of these
                                          (graphical on Ubuntu, even on servers; check: systemctl get-default)

 network.target          = network management started (NOT "network is up")
 network-online.target   = a configured address/route exists (needs a wait-online service)

 app.service:
   Wants=network-online.target      ← pull it in
   After=network-online.target      ← and wait for it
```

**Key terms**

| Directive | Meaning |
|-----------|---------|
| `Wants=` | Weak requirement: start it too; if it fails, carry on |
| `Requires=` | Strong: if it fails to start, fail too; if it stops, stop too |
| `BindsTo=` | Like Requires, and stop if it disappears (devices) |
| `PartOf=` | Restart/stop with the other unit |
| `After=` / `Before=` | Ordering only |
| `RequiresMountsFor=/data` | Require and order after the mounts for that path |
| `WantedBy=` (in `[Install]`) | Which target's `.wants/` dir `enable` links into |

**See it on a real system**

```bash
systemctl get-default
systemctl list-dependencies multi-user.target | head -30
systemctl list-dependencies --reverse docker.service     # who depends on Docker?
systemd-analyze critical-chain apache2.service
systemctl show -p Wants,Requires,After docker.service
```

```
$ systemd-analyze critical-chain apache2.service
The time when unit became active or started is printed after the "@" character.
The time the unit took to start is printed after the "+" character.

apache2.service +412ms
└─network.target @4.102s
  └─systemd-networkd.service @3.611s +488ms
    └─systemd-udevd.service @1.902s +301ms
      └─systemd-tmpfiles-setup-dev.service @1.788s +102ms
        └─kmod-static-nodes.service @1.560s +58ms
          └─systemd-journald.socket @1.510s
```

**Hands-on lab (test VM only)**

**Step 1 — Build.** Create a unit that binds a specific IP (use your VM's IP, here
192.0.2.10 as an example):

```ini
# /etc/systemd/system/bind-test.service
[Unit]
Description=Lab: listener on a specific IP

[Service]
ExecStart=/usr/bin/python3 -m http.server 8095 --bind 192.0.2.10

[Install]
WantedBy=multi-user.target
```

**Step 2 — Break.** `sudo systemctl daemon-reload && sudo systemctl enable bind-test`,
reboot the test VM (a reboot stops everything on the machine — fine on a lab VM; on a
server it needs a change window), then `systemctl status bind-test`. Depending on timing it may have
failed at boot with `OSError: [Errno 99] Cannot assign requested address` — the IP
wasn't configured yet — although `systemctl start bind-test` works fine by hand later.

**Step 3 — Fix.** Add to `[Unit]`: `Wants=network-online.target` and
`After=network-online.target`, daemon-reload, reboot, verify. (Alternatives: bind to
`0.0.0.0` and filter with the firewall, or set `net.ipv4.ip_nonlocal_bind=1`.)

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Works when started by hand, fails at boot | `journalctl -b -u UNIT`, check `After=`/`Wants=` | This topic |
| NFS/data mount not ready when the app starts | Add `RequiresMountsFor=/data` | Section 8 |
| Boot waits 2 minutes on "wait-online" | `systemctl status systemd-networkd-wait-online`; an interface in netplan never comes up | Section 9, [Network](02-network.md) |
| Stopping one unit stopped another | `systemctl list-dependencies --reverse UNIT` (Requires/BindsTo/PartOf) | This topic |

**Why it matters for troubleshooting**

"Works by hand, fails at boot" is almost always ordering. Reverse dependencies tell you
what else stops when you stop Docker or Apache — check before you act.

**Next step**

Drop-in overrides — changing a packaged unit without editing it.

### Drop-in overrides

**Level:** [L1 · Junior]

**Concept**

Never edit a unit in `/usr/lib/systemd/system/` — the next package upgrade overwrites
it. Instead, add a drop-in file in `/etc/systemd/system/UNIT.d/*.conf` containing only
the settings you change. `systemctl edit UNIT` creates `override.conf` for you and
reloads systemd. Settings that are **lists** (`ExecStart=`, `Environment=` is additive)
need special care: to replace `ExecStart=` you must first clear it with an empty
`ExecStart=` line.

```
 /usr/lib/systemd/system/nginx.service        (package — don't touch)
 /etc/systemd/system/nginx.service.d/
     10-limits.conf                            (yours; applied on top, in name order:
     override.conf                              digits sort before letters, so override.conf wins)
```

**Key terms**

| Command | Purpose |
|---------|---------|
| `systemctl edit UNIT` | Create/edit a drop-in (opens an editor, reloads on save) |
| `systemctl edit --full UNIT` | Copy the whole unit to `/etc` (stops receiving package fixes — avoid) |
| `systemctl revert UNIT` | Remove all your overrides for that unit |
| `systemd-delta` | List every overridden/extended unit on the system |

**See it on a real system**

```bash
systemd-delta --type=extended,overridden
systemctl cat docker | grep -E '^# /|ExecStart'
systemctl show -p LimitNOFILE,Restart nginx 2>/dev/null
```

```
$ systemd-delta --type=extended
[EXTENDED]   /usr/lib/systemd/system/nginx.service → /etc/systemd/system/nginx.service.d/override.conf
[EXTENDED]   /usr/lib/systemd/system/rc-local.service → /usr/lib/systemd/system/rc-local.service.d/debian.conf

2 overridden configuration files found.
```

→ `systemd-delta` is the first command on an unfamiliar server: it shows every local
customisation someone made to packaged services.

**Hands-on lab (test VM only)**

**Step 1 — Add a restart policy to Apache.**

```bash
sudo systemctl edit apache2
# in the editor, between the comment markers, add:
# [Service]
# Restart=on-failure
# RestartSec=5
systemctl show -p Restart,RestartUSec apache2
```

**Step 2 — Break.** Make a drop-in that adds a second `ExecStart=` without clearing it:

```bash
sudo mkdir -p /etc/systemd/system/cron.service.d
printf '[Service]\nExecStart=/usr/sbin/cron -f -L 15\n' | sudo tee /etc/systemd/system/cron.service.d/broken.conf
sudo systemctl daemon-reload
systemctl status cron --no-pager
```

You'll see: `cron.service: Service has more than one ExecStart= setting, which is only
allowed for Type=oneshot services. Refusing.`

**Step 3 — Fix.** Clear the list first:

```bash
printf '[Service]\nExecStart=\nExecStart=/usr/sbin/cron -f -L 15\n' | sudo tee /etc/systemd/system/cron.service.d/broken.conf
sudo systemctl daemon-reload && sudo systemctl restart cron
sudo systemctl revert cron      # finally, remove the lab override
```

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `Service has more than one ExecStart= setting` | `systemctl cat UNIT` → add empty `ExecStart=` | This topic |
| Override ignored | Wrong section header, wrong directory name (`UNIT.service.d`), or no `daemon-reload` | This topic |
| Docker: `the following directives are specified both as a flag and in the configuration file` | A drop-in passes `-H`/`--dns` while `daemon.json` sets the same — keep one | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

Drop-ins are how you raise limits, add restart policies or environment variables
cleanly — and `systemd-delta` is how you find what the previous admin changed.

**Next step**

Restart policies and start limits — what systemd does when a service dies.

### Restart policies and start limits

**Level:** [L1 · Junior]

**Concept**

`Restart=` tells systemd what to do when the main process exits. `RestartSec=` is the
pause between attempts. To stop a broken service from restarting forever, systemd
counts starts: more than `StartLimitBurst` (default 5) within `StartLimitIntervalSec`
(default 10 s) and it gives up with "start request repeated too quickly". `Type=`
tells systemd how to know the service has *started*.

| `Restart=` | Restarts when the process... |
|------------|------------------------------|
| `no` (default) | never |
| `on-failure` | exits non-zero, is killed by an unclean signal (KILL, SEGV...), times out, or fails the watchdog |
| `on-abnormal` | is killed by a signal or times out (not on non-zero exit) |
| `always` | exits for any reason (except `systemctl stop`) |

"Clean" signals for `on-failure` are HUP, INT, TERM and PIPE: a process that dies
from TERM is **not** restarted, one killed with KILL is.

| `Type=` | systemd considers it started when... |
|---------|--------------------------------------|
| `simple` | the process has been forked (even if exec then fails) |
| `exec` | the binary was executed successfully (better default for new units) |
| `forking` | the parent exits (classic daemons; set `PIDFile=`) |
| `notify` | the app sends `READY=1` via sd_notify (dockerd, containerd and systemd-networkd do; nginx and Apache use `forking`) |
| `oneshot` | the process has exited (scripts, setup tasks) |

**Key terms**

| Term | Meaning |
|------|---------|
| `StartLimitIntervalSec=`, `StartLimitBurst=` | In `[Unit]`: rate limit for starts |
| `systemctl reset-failed UNIT` | Clear the failed state and the start counter |
| `NRestarts` | How many times systemd restarted it (`systemctl show -p NRestarts`) |
| systemd exit status | `203/EXEC` binary missing/not executable, `217/USER` user missing, `200/CHDIR` WorkingDirectory missing, `226/NAMESPACE` sandboxing path missing |

**See it on a real system**

```bash
systemctl show -p Type,Restart,RestartUSec,NRestarts,StartLimitBurst,StartLimitIntervalUSec docker
systemctl --failed
journalctl -u UNIT -b | grep -E 'Scheduled restart|Start request repeated|Failed with result'
```

**Hands-on lab (test VM only)**

The full lab is the next topic (build a unit, kill it, watch the restart). Here, break
the start limit on purpose: in that lab unit, set `ExecStart=/usr/bin/false`, keep
`Restart=on-failure` and `RestartSec=1`, `daemon-reload`, start it, and within a few
seconds `systemctl status` shows:

```
× demo-web.service - Demo Python web server (lab)
     Active: failed (Result: exit-code) since Sat 2026-10-03 10:02:11 UTC; 2s ago
    Process: 51022 ExecStart=/usr/bin/false (code=exited, status=1/FAILURE)
...
systemd[1]: demo-web.service: Start request repeated too quickly.
systemd[1]: demo-web.service: Failed with result 'exit-code'.
```

Fix the `ExecStart=`, `daemon-reload`, then `sudo systemctl reset-failed demo-web` and
start it again.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `Active: activating (auto-restart)` over and over | `journalctl -u UNIT -n 50` — the real error is in the app's output | [systemd reference](07-services-systemd.md) |
| `Start request repeated too quickly` | Fix the cause, then `systemctl reset-failed UNIT` | This topic |
| `status=203/EXEC` | `ls -l` the ExecStart path, shebang, `noexec` mount | Section 2 |
| `status=217/USER` | `getent passwd USER` | Section 3 |
| Service "started" but isn't working (Type=simple) | Use `Type=exec`/`notify`; check `journalctl -u UNIT` | This topic |

**Why it matters for troubleshooting**

The exit-status codes in `systemctl status` (203, 217, 200) diagnose a broken unit
without reading any app logs. Start limits explain why a service "stopped trying".

**Next step**

Write your own unit end to end — the L1 drill.

### Writing a service unit from scratch

**Level:** [L1 · Junior]

**Concept**

A minimal production-worthy unit has: what to run (`ExecStart`), as whom (`User`),
where (`WorkingDirectory`), with which environment (`EnvironmentFile`), what to do on
failure (`Restart`), when to start (`After`/`Wants`, `WantedBy`), and some sandboxing.
This is the **L1 drill** from the Ops Ladder: a small Python HTTP server with
`Restart=on-failure`, killed with `kill -9`, restart found in the journal.

```ini
# /etc/systemd/system/demo-web.service
[Unit]
Description=Demo Python web server (lab)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=exec
User=demo
Group=demo
WorkingDirectory=/srv/demo
ExecStart=/usr/bin/python3 -m http.server 8080 --bind 127.0.0.1
Restart=on-failure
RestartSec=2
# light sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Key terms**

| Directive | Why it's there |
|-----------|----------------|
| `User=`/`Group=` | Never run apps as root |
| `WorkingDirectory=` | Relative paths resolve here; missing → `200/CHDIR` |
| `EnvironmentFile=` | Secrets/config out of the unit (mode 600/640) |
| `ProtectSystem=strict` | Whole filesystem read-only except `ReadWritePaths=` |
| `PrivateTmp=true` | Private `/tmp` — files in "/tmp" won't be where you expect when debugging |

**See it on a real system**

```bash
systemd-analyze verify /etc/systemd/system/demo-web.service   # lint the unit
systemd-analyze security demo-web                              # exposure score per setting
```

**Hands-on lab (test VM only)**

**Step 1 — Build.**

```bash
sudo useradd --system --home-dir /srv/demo --shell /usr/sbin/nologin demo
sudo mkdir -p /srv/demo && echo "demo ok" | sudo tee /srv/demo/index.html
sudo chown -R demo:demo /srv/demo
sudoedit /etc/systemd/system/demo-web.service      # paste the unit above
sudo systemctl daemon-reload
sudo systemctl enable --now demo-web
curl -s http://127.0.0.1:8080/                     # "demo ok"
sudo ss -ltnp 'sport = :8080'
```

**Step 2 — Break it with SIGKILL and watch systemd react.**

> ⚠️ `kill -9` is used here on purpose, on a lab unit, to simulate a crash. On real
> services use `systemctl stop`/`restart`; see the signals topic for the safe order.

```bash
journalctl -fu demo-web &                                 # watch in the background
sudo kill -9 "$(systemctl show -p MainPID --value demo-web)"
```

```
systemd[1]: demo-web.service: Main process exited, code=killed, status=9/KILL
systemd[1]: demo-web.service: Failed with result 'signal'.
systemd[1]: demo-web.service: Scheduled restart job, restart counter is at 1.
systemd[1]: Started demo-web.service - Demo Python web server (lab).
```

Now send TERM instead: `sudo kill "$(systemctl show -p MainPID --value demo-web)"`.
The service stops and stays stopped — TERM is a clean exit for `on-failure`. Change to
`Restart=always` if that's not what you want.

**Step 3 — Break it three more ways, read each error, fix each.**

| Break | Status / journal shows | Fix |
|-------|------------------------|-----|
| `ExecStart=/usr/bin/python4 ...` | `status=203/EXEC` | Correct path (`command -v python3`) |
| `User=demo2` (doesn't exist) | `status=217/USER` | Create user or fix name |
| Add `ExecStartPre=/usr/bin/touch /srv/demo/started` (a write) with `ProtectSystem=strict` | `touch: cannot touch '/srv/demo/started': Read-only file system` | `ReadWritePaths=/srv/demo` |

Finish with `sudo systemctl disable --now demo-web` (keep the file for later labs).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Crash loop after deploy | `journalctl -u UNIT -n 100 --no-pager` | [Site down playbook](25-playbook-site-down.md) |
| Unit runs, app can't write its data dir | `ProtectSystem=`/`ReadWritePaths=`, `namei -l DIR` | This topic |
| App can't find files in /tmp you put there | `PrivateTmp=true` | This topic |

**Why it matters for troubleshooting**

You can only troubleshoot well what you've built yourself. Every Dokploy/Docker
migration still leaves some host services (backup scripts, exporters, agents) that
need a proper unit.

**Next step**

Socket units — why `systemd` itself sometimes "owns" a port.

### Socket units and who really holds a port

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

With **socket activation** systemd opens the listening port itself and starts the
service on the first connection, handing it the socket. Then `ss -p` shows `systemd`
(PID 1) as the owner of the port — confusing during a port inventory. On Ubuntu
22.10 and later (including 24.04), **OpenSSH uses `ssh.socket`**: the port comes from
`sshd_config`, but it is applied by a generator, so changing `Port` needs
`daemon-reload` and a restart of `ssh.socket`, not just `ssh.service`.

```
 client ──▶ :22 ──▶ ssh.socket (held by systemd, PID 1)
                         │ first connection
                         ▼
                    ssh.service (sshd) gets the socket
```

**Key terms**

| Term | Meaning |
|------|---------|
| `ListenStream=` | TCP port/address or Unix socket path in a `.socket` unit |
| `Accept=` | yes = one service instance per connection; no = one service for all |
| `systemctl list-sockets` | All sockets systemd holds and which unit they activate |

**See it on a real system**

```bash
systemctl list-sockets
sudo ss -ltnp 'sport = :22'
systemctl cat ssh.socket
```

```
$ systemctl list-sockets
LISTEN                            UNIT                          ACTIVATES
/run/docker.sock                  docker.socket                 docker.service
/run/systemd/journal/stdout       systemd-journald.socket       systemd-journald.service
[::]:22                           ssh.socket                    ssh.service
...
$ sudo ss -ltnp 'sport = :22'
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096               *:22              *:*     users:(("sshd",pid=901,fd=3),("systemd",pid=1,fd=126))
```

→ Port 22 is held by systemd (fd 126) and shared with sshd. If you "stop ssh" and the
port is still open, this is why.

**Hands-on lab (test VM only)**

> ⚠️ Keep the hypervisor console open. A wrong SSH port change locks you out.

**Step 1.** In `/etc/ssh/sshd_config` set `Port 2222` (and keep `Port 22` on its own
line during the test so you can't lose access). Run `sudo sshd -t`.

**Step 2 — Break.** Run only `sudo systemctl restart ssh`. Check
`sudo ss -ltnp | grep -E ':22|:2222'` — 2222 is **not** listening.

**Step 3 — Fix.** `sudo systemctl daemon-reload && sudo systemctl restart ssh.socket`,
then check again: both ports listen. Allow 2222 in the firewall before removing 22
(section 16). Revert to port 22 only at the end of the lab.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Changed sshd `Port`, still on 22 (Ubuntu 22.10+) | `systemctl list-sockets`; `daemon-reload` + `restart ssh.socket` | Section 10 |
| Port shows owner `systemd` | `systemctl list-sockets | grep PORT` | [Ports playbook](22-playbook-ports-inventory.md) |
| Stopped `docker.service` but Docker starts again | `docker.socket` re-activates it — stop/disable both | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

A port inventory that reports "systemd" as the owner is incomplete until you map it
through `list-sockets` to the real service.

**Next step**

journald — where all of these services' output ends up.

### journald: how the journal works

**Level:** [L1 · Junior]

**Concept**

systemd-journald collects **everything**: stdout/stderr of every unit, syslog
messages, kernel messages, and audit events, and stores them in indexed binary files
with metadata fields (unit, PID, priority, boot ID). On Ubuntu, rsyslog also writes
classic text files (`/var/log/syslog`, `auth.log`) from the same stream. Storage is
**persistent** if `/var/log/journal/` exists (Ubuntu default), otherwise **volatile**
in `/run/log/journal/` and lost at reboot (some RHEL-family installs).

```
 apache2 stderr ─┐
 sshd syslog() ──┼─▶ systemd-journald ──▶ /var/log/journal/MACHINE-ID/*.journal  (binary, indexed)
 kernel (kmsg) ──┤          │
 logger "msg" ───┘          └──▶ rsyslog ──▶ /var/log/syslog, /var/log/auth.log, kern.log (text)
```

**Key terms**

| Term | Meaning |
|------|---------|
| `Storage=` | `persistent`, `volatile`, `auto` (persistent if the directory exists), `none` |
| `SystemMaxUse=` | Cap on journal disk usage (default: 10% of the filesystem, max 4 GB) |
| Rate limiting | `RateLimitIntervalSec=`/`RateLimitBurst=`; drops floods with "Suppressed N messages" |
| Boot ID | Each boot has its own ID; `-b -1` = previous boot |
| Fields | `_SYSTEMD_UNIT`, `_PID`, `PRIORITY`, `_COMM`, `SYSLOG_IDENTIFIER` |

**See it on a real system**

```bash
journalctl --disk-usage
journalctl --list-boots | tail -3
systemd-analyze cat-config systemd/journald.conf | grep -v '^#' | grep .
journalctl -u ssh -n 1 -o verbose          # every field of one entry
```

```
$ journalctl --disk-usage
Archived and active journals take up 1.2G in the file system.
$ journalctl --list-boots | tail -3
 -2 5d0c... Mon 2026-09-14 08:02:11 UTC Mon 2026-09-21 06:12:40 UTC
 -1 7a41... Mon 2026-09-21 06:13:02 UTC Wed 2026-09-30 06:10:55 UTC
  0 c93e... Wed 2026-09-30 06:11:20 UTC Sat 2026-10-03 10:15:02 UTC
```

→ Three boots recorded: you can read logs from **before** the last reboot
(`journalctl -b -1`), which is how you investigate "it rebooted at 06:10 — why?".

**Hands-on lab (test VM only)**

**Step 1 — Cap the journal** with a drop-in:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nSystemMaxUse=300M\n' | sudo tee /etc/systemd/journald.conf.d/size.conf
sudo systemctl restart systemd-journald
journalctl --disk-usage
```

**Step 2 — Break: flood it.** `for i in $(seq 1 20000); do logger -t flood "msg $i"; done`,
then `journalctl -t flood | wc -l` and `journalctl -u systemd-journald -n 5` — you may
see `Suppressed N messages from ...` when a single service floods (rate limiting applies
per unit).

**Step 3 — Clean up.** `sudo journalctl --vacuum-time=1h` on the test VM only, and
remove the lab drop-in if you don't want it. On production prefer
`--vacuum-size=` with a value that keeps several days.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| No logs from before the reboot | `journalctl --list-boots`; create `/var/log/journal` (Storage=persistent) | [Logs reference](06-logs-journal.md) |
| Journal uses many GB of `/var` | `journalctl --disk-usage`, set `SystemMaxUse=` | Section 8 |
| Messages missing during a flood | `journalctl -u systemd-journald | grep Suppressed` | This topic |
| `journalctl` shows nothing for a user | Not in `adm`/`systemd-journal` group — use sudo | Section 3 |

**Why it matters for troubleshooting**

journald is the single place that has the stdout of every service, the kernel's OOM
messages and the sudo trail, correlated by time. Section 14 teaches the filters that
make it fast.

**Next step**

The boot process — what happens before systemd and how to rescue a box that won't boot.

---

## 7. The boot process and recovery

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Linux Core Concepts (kernel, boot) ([course](https://kodekloud.com/courses/the-linux-basics-course)), then LFCS — Operations Deployment: Manage Startup Process and Services ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: this section, then [Kernel & system reference](13-kernel-system.md) · 3) Read (optional): [How Linux Works, 3rd ed.](https://nostarch.com/howlinuxworks3), the boot chapters · 4) Practice: the fstab emergency-mode and `init=/bin/bash` labs below, on a VM with a snapshot

### From power-on to login

**Level:** [L1 · Junior]

**Concept**

Booting is a relay race; each runner hands over to the next, and each hand-over can
fail with a characteristic symptom.

```
 Power on
   │
   ▼
 Firmware: UEFI (modern) or BIOS (legacy) ─ POST, finds a boot disk
   │        UEFI: reads the EFI System Partition (/boot/efi), runs shim → grubx64.efi
   │        BIOS: runs the MBR boot code → GRUB core image
   ▼
 GRUB (bootloader) ─ menu, reads /boot/grub/grub.cfg, loads kernel + initramfs into RAM
   │                 kernel command line: root=..., ro, quiet splash, ...
   ▼
 Linux kernel ─ initialises CPU, memory, drivers built in; mounts the initramfs
   │
   ▼
 initramfs (initrd.img) ─ small temporary root: loads storage drivers, LVM, RAID, LUKS,
   │                      finds the real root filesystem, mounts it, switch_root
   ▼
 systemd (PID 1) ─ reads units, mounts /etc/fstab entries, starts services
   │               towards default.target (graphical.target even on Ubuntu servers, which
   │               pulls in multi-user.target; multi-user.target on RHEL servers)
   ▼
 Login prompt (getty) and sshd
```

| Stage fails | You see |
|-------------|---------|
| Firmware | No boot device, PXE attempts, "Boot device not found" |
| GRUB | `grub>` or `grub rescue>` prompt, "error: file '/boot/vmlinuz...' not found" |
| Kernel | Kernel panic, "VFS: Unable to mount root fs" |
| initramfs | `(initramfs)` BusyBox prompt, "ALERT! UUID=... does not exist. Dropping to a shell!" |
| systemd | "You are in emergency mode", or a long "A start job is running for ..." |

**Key terms**

| Term | Meaning |
|------|---------|
| ESP | EFI System Partition (FAT32, mounted at `/boot/efi`) |
| initramfs / initrd | Compressed early root filesystem built per kernel |
| Kernel command line | Parameters GRUB passes to the kernel (`cat /proc/cmdline`) |
| default.target | What systemd boots towards |

**See it on a real system**

```bash
[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS
cat /proc/cmdline
ls -lh /boot
systemd-analyze                     # time per stage
systemd-analyze blame | head -10    # slowest units
journalctl -b -1 -p err --no-pager  # errors from the PREVIOUS boot
last -x reboot shutdown | head -5   # when did it reboot, was it clean?
```

```
$ systemd-analyze
Startup finished in 6.211s (kernel) + 31.904s (userspace) = 38.116s
graphical.target reached after 31.880s in userspace.
$ systemd-analyze blame | head -3
25.120s systemd-networkd-wait-online.service
 2.004s apt-daily-upgrade.service
 1.212s cloud-init.service
```

→ 25 seconds waiting for the network to be "online": usually an interface in netplan
that never gets a link or address (section 9).

**Hands-on lab (test VM only)**

**Step 1.** Record your VM's boot timeline: `systemd-analyze`, `blame`,
`critical-chain`. Reboot and compare.

**Step 2 — Break.** Add a second virtual NIC in the hypervisor but leave it
disconnected (no link), then give it an entry in netplan (e.g. `ens19: {dhcp4: true}`
under `ethernets:`), `sudo netplan apply`, reboot. Boot now takes ~2 minutes;
`systemd-analyze blame` shows `systemd-networkd-wait-online` on top. (A name that
matches no interface at all may or may not delay boot depending on the netplan and
systemd versions — check with `systemctl cat systemd-networkd-wait-online` which
interfaces it waits for on your release.)

**Step 3 — Fix.** Remove the bogus interface (or mark a non-critical one
`optional: true`), apply, reboot, compare timings.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Box rebooted unexpectedly | `last -x`, `journalctl -b -1 -n 100`, `journalctl -k -b -1 | tail` | [Kernel reference](13-kernel-system.md) |
| Boot is very slow | `systemd-analyze blame`, `critical-chain` | [systemd reference](07-services-systemd.md) |
| Hangs at boot, then emergency mode | fstab — see the rescue topic below | Section 8 |

**Why it matters for troubleshooting**

Knowing which runner dropped the baton tells you which tool to reach for: firmware
console, GRUB editor, initramfs shell, or systemd's emergency shell.

**Next step**

GRUB and the kernel command line — the controls you use to recover.

### GRUB and the kernel command line

**Level:** [L1 · Junior]

**Concept**

GRUB shows a menu (hidden by default on Ubuntu servers), loads a kernel and
initramfs, and passes the kernel command line. You configure it in
`/etc/default/grub` and regenerate `grub.cfg` with `update-grub` — never edit
`grub.cfg` directly. At boot you can edit an entry once (press `e`) to add
parameters for recovery without changing anything on disk.

**Key terms**

| Item | Meaning |
|------|---------|
| `GRUB_TIMEOUT_STYLE=hidden` / `menu` | Ubuntu servers hide the menu; set `menu` + `GRUB_TIMEOUT=5` on servers you manage |
| `GRUB_CMDLINE_LINUX_DEFAULT` | Parameters for normal boots (`quiet splash`) |
| Show the menu | Hold **Shift** (BIOS) or press **Esc** (UEFI) during boot |
| Edit an entry | `e`, edit the `linux` line, boot with **Ctrl-X** or **F10** |
| `update-grub` | Ubuntu; RHEL: `grub2-mkconfig -o /boot/grub2/grub.cfg` or `grubby --update-kernel=ALL --args=...` |
| Older kernel | "Advanced options for Ubuntu" submenu — keep at least one previous kernel |

**See it on a real system**

```bash
grep -E '^GRUB_(DEFAULT|TIMEOUT|TIMEOUT_STYLE|CMDLINE)' /etc/default/grub
dpkg -l 'linux-image-[0-9]*' | awk '/^ii/ {print $2, $3}'
uname -r
```

```
$ dpkg -l 'linux-image-[0-9]*' | awk '/^ii/ {print $2, $3}'
linux-image-6.8.0-44-generic 6.8.0-44.44
linux-image-6.8.0-45-generic 6.8.0-45.45
$ uname -r
6.8.0-45-generic
```

→ Two kernels installed, running the newest: if 6.8.0-45 misbehaves (driver
regression), you can boot 6.8.0-44 from the Advanced menu.

**Hands-on lab (test VM only)**

**Step 1.** Make the menu visible: set `GRUB_TIMEOUT_STYLE=menu` and
`GRUB_TIMEOUT=5` in `/etc/default/grub`, run `sudo update-grub`, reboot via the
hypervisor console and watch the menu.

> ⚠️ `reboot` interrupts everything on the machine. On a lab VM that's fine; on a server,
> check `who`, announce it, and use a change window. Never reboot a remote server whose
> console you can't reach after a GRUB or fstab change.

**Step 2.** At the menu press `e`, append `systemd.unit=rescue.target` to the line
starting with `linux`, press Ctrl-X. You land in rescue mode (next topic). On a stock
Ubuntu VM root has no password, so you only see "the root account is locked" and
pressing Enter continues the normal boot — that is the expected result and the reason
for the `init=/bin/bash` route. If root has a password, log in, look around, then type
`systemctl default` to continue booting normally.

**Step 3.** Boot the older kernel from "Advanced options" and confirm with `uname -r`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `grub rescue>` prompt | GRUB can't find its files — boot a live ISO, mount root, reinstall GRUB | [Kernel reference](13-kernel-system.md) |
| New kernel panics or a NIC/driver vanished | Boot the previous kernel from Advanced options, then `apt-mark hold` or report | This topic |
| Your `/etc/default/grub` change has no effect | Forgot `update-grub` | This topic |

**Why it matters for troubleshooting**

GRUB's edit mode is your universal "boot into a safe state" tool on VMs and bare
metal with a console — it needs no rescue media.

**Next step**

Rescue and emergency mode — what to do once you're in.

### Rescue mode, emergency mode and root password reset

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

systemd has two minimal targets. **rescue.target** mounts all filesystems and gives
a root shell with almost no services. **emergency.target** mounts only the root
filesystem, read-only — used when fstab or a filesystem is broken. Both ask for the
root password; on Ubuntu root has **no** password by default, so you get "the root
account is locked" and need the lower-level fallback `init=/bin/bash`.

| Option (append to the `linux` line in GRUB) | What you get | Use when |
|----------------------------------------------|--------------|----------|
| `systemd.unit=rescue.target` | Root shell, filesystems mounted | Broken service, need to fix config |
| `systemd.unit=emergency.target` | Root shell, only `/` (read-only) | Broken fstab, filesystem errors |
| `init=/bin/bash` | Bash as PID 1, `/` read-only, no systemd at all | Root locked, forgotten passwords, broken sudoers |
| Live ISO / rescue instance | Full tools, your disk mounted at `/mnt` | GRUB broken, disk needs repair |

**Key terms**

| Term | Meaning |
|------|---------|
| sulogin | Asks the root password for rescue/emergency shells |
| `mount -o remount,rw /` | Make the root filesystem writable before editing |
| `systemctl default` | Leave rescue/emergency and continue to the normal target |

**See it on a real system**

The emergency screen you'll eventually meet (after a bad fstab entry):

```
[ TIME ] Timed out waiting for device dev-disk-by\x2duuid-5a7c9d3e....device - /dev/disk/by-uuid/5a7c9d3e-1111-4abc-8def-0123456789ab.
[DEPEND] Dependency failed for data.mount - /data.
[DEPEND] Dependency failed for local-fs.target - Local File Systems.
You are in emergency mode. After logging in, type "journalctl -xb" to view
system logs, "systemctl reboot" to reboot, "systemctl default" or "exit"
to boot into default mode.
Cannot open access to console, the root account is locked.
See sulogin(8) man page for more details.

Press Enter to continue.
```

→ On Ubuntu with a locked root account, emergency mode is a dead end: reboot and use
`init=/bin/bash`.

**Hands-on lab (test VM only)**

> ⚠️ Snapshot first. These steps change how the VM boots.

**Step 1 — Reset a forgotten password with `init=/bin/bash`.** At the GRUB menu press
`e`, go to the end of the `linux` line, append `init=/bin/bash`, press Ctrl-X. Then:

```bash
mount -o remount,rw /           # root is read-only at this point
passwd labuser                   # or fix /etc/sudoers.d/*, /etc/fstab ...
sync                             # flush writes to disk
exec /sbin/init                  # continue a normal boot (or power-cycle from the hypervisor)
```

**Step 2 — Break fstab** (done in section 8's mounts lab): a non-existent UUID without
`nofail` → emergency mode after a 90-second timeout.

**Step 3 — Fix from `init=/bin/bash`:** remount rw, comment out the line (or add
`nofail`), `sync`, reboot. Confirm with `findmnt --verify` before the next reboot.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| "Cannot open access to console, the root account is locked" | GRUB `e` → `init=/bin/bash` | This topic |
| `(initramfs)` prompt, "ALERT! UUID=... does not exist" | `blkid`, `cat /proc/cmdline` — root device changed/missing | Next topic |
| Cloud VM won't boot, no console | Serial console, or attach the disk to a rescue instance | [AWS](16-aws-cloud.md) |

**Why it matters for troubleshooting**

On-prem servers rarely have someone at the console. Knowing the GRUB edit +
`init=/bin/bash` route means a broken fstab or sudoers file costs ten minutes, not a
reinstall.

**Next step**

initramfs and kernel updates — the last piece of the boot chain, and the full `/boot`.

### initramfs, kernels and a full /boot

**Level:** [L1 · Junior]

**Concept**

Each installed kernel has a matching initramfs in `/boot`, built by
`update-initramfs` (Ubuntu) or `dracut` (RHEL). It contains the drivers and scripts
needed to find the root filesystem (LVM, RAID, NVMe, LUKS). Kernel updates install a
new kernel + initramfs; when `/boot` is a small separate partition and old kernels
pile up, updates fail with "No space left on device".

**Key terms**

| Command | Purpose |
|---------|---------|
| `update-initramfs -u` | Rebuild the initramfs of the newest installed kernel (`-k "$(uname -r)"` for the running one, `-k all` for all) |
| `lsinitramfs /boot/initrd.img-$(uname -r)` | List what's inside |
| `dracut -f` / `lsinitrd` | RHEL equivalents |
| `apt autoremove --purge` | Removes old kernels Ubuntu no longer needs |

**See it on a real system**

```bash
df -h /boot
ls -lh /boot/initrd.img-* /boot/vmlinuz-*
lsinitramfs /boot/initrd.img-"$(uname -r)" | grep -E 'lvm|nvme|raid' | head
```

**Hands-on lab (test VM only)**

**Step 1.** List initramfs contents and find the LVM tools inside — that's why an LVM
root can be found at boot.

**Step 2 — Break (read-only exercise).** Look at what would be removed:
`apt-get --dry-run autoremove --purge | grep linux-image`. Never remove the running
kernel (`uname -r`).

**Step 3.** Rebuild the initramfs: `sudo update-initramfs -u` and confirm the
timestamp changed.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `update-initramfs: failed for /boot/initrd.img-... with 1` / `No space left on device` | `df -h /boot`, `sudo apt autoremove --purge` | [Packages reference](11-packages.md) |
| `(initramfs)` shell after moving disks/controllers | Missing driver in initramfs — rebuild from rescue | This topic |
| "Pending kernel upgrade" message, `needrestart` asks to reboot | Plan a reboot window | Section 16 |

**Why it matters for troubleshooting**

A full `/boot` silently blocks security updates until someone notices; the fix is
routine once you've done it on a lab VM.

**Next step**

Storage — partitions, filesystems, fstab and LVM.

---

## 8. Storage and filesystems

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux (partitions, filesystems, NFS, LVM) ([course](https://kodekloud.com/courses/the-linux-basics-course)), then LFCS — Storage: LVM, mount options, swap and Monitor Storage Performance ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page)) · 2) Note: this section, then [Storage & disk reference](01-storage-disk.md) · 3) Video: skip — the loop-device labs teach more · 4) Practice: the Ops Ladder L1 drill "fill /var until a service fails" (disk-full topic), then the disks challenge in *Linux Challenges* (free, [course](https://kodekloud.com/courses/linux-challenges))

### Block devices, partitions and the storage stack

**Level:** [L1 · Junior]

**Concept**

Storage is a stack. A **disk** (block device) gets a **partition table** (GPT today,
MBR on old systems) that divides it into **partitions**. A partition can hold a
**filesystem** directly, or become an LVM **physical volume** that is pooled and carved
into **logical volumes**. A filesystem becomes visible only when **mounted** on a
directory.

```
 /dev/sda (disk)
 ├── sda1  EFI System Partition (vfat)           → /boot/efi
 ├── sda2  ext4                                   → /boot
 └── sda3  LVM physical volume
           └── VG ubuntu-vg
               └── LV ubuntu-lv  (ext4)           → /
 /dev/sdb (second disk, empty)  ← "attached but not partitioned/mounted"

 layers:  disk → partition table → partition → [PV → VG → LV] → filesystem → mount point
```

**Key terms**

| Term | Meaning |
|------|---------|
| Block device | `/dev/sda`, `/dev/vda` (virtio), `/dev/nvme0n1` (NVMe), `/dev/loopN` (file-backed) |
| Partition | `/dev/sda1`, `/dev/nvme0n1p1` (note the `p`) |
| GPT / MBR | Partition table formats; GPT is the modern default |
| UUID | Filesystem ID, stable across reboots — device names are not |
| `/dev/disk/by-uuid/`, `by-id/` | Stable symlinks created by udev |

**See it on a real system**

```bash
lsblk -f                     # tree with filesystem, label, UUID, usage
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS,MODEL,SERIAL
sudo blkid
sudo fdisk -l /dev/sda       # read-only listing of the partition table
ls -l /dev/disk/by-uuid/
```

```
$ lsblk -f
NAME                      FSTYPE      FSVER    LABEL UUID                                   FSAVAIL FSUSE% MOUNTPOINTS
sda
├─sda1                    vfat        FAT32          9C1A-4E2B                                 1G     1% /boot/efi
├─sda2                    ext4        1.0            3f6c2b9e-7a11-4d2c-9e55-0b1c2d3e4f50     1.6G     9% /boot
└─sda3                    LVM2_member LVM2 001       Wc3s7h-2kLm-9QpR-aB1c-dE2f-gH3i-jK4lmN
  └─ubuntu--vg-ubuntu--lv ext4        1.0            8d1e4f0a-2c4b-4c1e-9a77-3f1d2e5b6a10     18.6G    35% /
sdb
```

→ `sdb` has no partitions, filesystem or mount: a new disk that was attached but never
set up — the most common "disk not showing up" answer.

**Hands-on lab (test VM only)**

Use a **loop device** (a file pretending to be a disk) so nothing real is at risk.

> ⚠️ `parted`, `mkfs` and `wipefs` destroy whatever is on the target device. Always run
> `lsblk -f` first and type the device name you just verified — `/dev/loopN` here, never
> a guess like `/dev/sdb` on a real server. Safer habit: `sudo wipefs -n DEVICE` (dry
> run) shows existing signatures before you overwrite anything.

**Step 1 — Build.**

```bash
truncate -s 2G /var/tmp/lab-disk.img
LOOP=$(sudo losetup --find --show --partscan /var/tmp/lab-disk.img); echo "$LOOP"
lsblk -f "$LOOP"                                     # empty
sudo parted -s "$LOOP" mklabel gpt mkpart data ext4 1MiB 100%
sudo mkfs.ext4 -L labdata "${LOOP}p1"
sudo mkdir -p /mnt/lab && sudo mount "${LOOP}p1" /mnt/lab
lsblk -f "$LOOP"; df -h /mnt/lab
```

**Step 2 — Break.** Unmount and detach the loop device (`sudo umount /mnt/lab;
sudo losetup -d "$LOOP"`), then `sudo mount LABEL=labdata /mnt/lab` →
`mount: /mnt/lab: can't find LABEL=labdata.` The "disk" is gone, like a detached
volume or a dead controller.

**Step 3 — Fix.** Re-attach with `losetup --find --show --partscan` and mount again.
Keep the image: the next topics reuse it.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| New disk "not showing up" | `lsblk`, `dmesg -T | tail`, rescan the SCSI bus | [Storage reference](01-storage-disk.md) |
| Device names changed after reboot (sdb ↔ sdc) | Use UUID/LABEL in fstab, `ls -l /dev/disk/by-id/` | Mounts topic below |
| Disk errors | `dmesg -T | grep -iE 'i/o error|nvme|ata'`, `smartctl -H` | [Storage reference](01-storage-disk.md) |

**Why it matters for troubleshooting**

`lsblk -f` is the one picture of the whole storage stack. Every disk question —
"why is this full", "where did that disk go", "can I grow /var" — starts there.

**Next step**

Filesystems — ext4 versus xfs and what each can and can't do.

### Filesystems: ext4 versus xfs

**Level:** [L1 · Junior]

**Concept**

A filesystem organises a block device into files, directories and inodes. Ubuntu
defaults to **ext4**, RHEL/Rocky to **xfs**. Both are mature; they differ in what they
let you do later.

| Feature | ext4 | xfs |
|---------|------|-----|
| Default on | Ubuntu, Debian | RHEL, Rocky, Amazon Linux |
| Grow online | Yes (`resize2fs`) | Yes (`xfs_growfs MOUNTPOINT`) |
| Shrink | Yes, **offline** only | **Never** |
| Inodes | Fixed at `mkfs` time (`-N`, `-i`) | Allocated dynamically |
| Reserved blocks | 5% for root by default (`tune2fs -m`) | None |
| Check/repair | `fsck.ext4` / `e2fsck` (unmounted) | `xfs_repair` (unmounted) |
| Info | `tune2fs -l DEVICE` | `xfs_info MOUNTPOINT` |

**Key terms**

| Term | Meaning |
|------|---------|
| Superblock | Filesystem metadata (size, inode count, state) |
| Journal | Write-ahead log that makes crashes recoverable |
| `errors=remount-ro` | Mount option (set for `/` by Ubuntu cloud images and the older installer) that turns the filesystem read-only on errors instead of corrupting more; check `findmnt -no OPTIONS /` and `tune2fs -l` ("Errors behavior") on yours |
| `ftype=1` | xfs feature required for Docker's overlay2 (`xfs_info` shows it) |

**See it on a real system**

```bash
df -hT
sudo tune2fs -l /dev/mapper/ubuntu--vg-ubuntu--lv | grep -E 'Inode count|Reserved block count|Block count|Filesystem state'
findmnt -no OPTIONS /
```

```
$ sudo tune2fs -l /dev/mapper/ubuntu--vg-ubuntu--lv | grep -E 'Inode count|Block count|Reserved block count|state'
Filesystem state:         clean
Inode count:              3276800
Block count:              13106176
Reserved block count:     655308
$ findmnt -no OPTIONS /
rw,relatime
```

→ 655308 reserved blocks × 4 KiB ≈ 2.5 GiB that only root can use: why `df` shows
"Avail" smaller than "Size − Used", and why root processes keep writing after users
get "No space left".

> ⚠️ Never run `fsck`/`e2fsck`/`xfs_repair` on a **mounted** read-write filesystem — it
> corrupts it. Safer: `sudo fsck -n DEVICE` (read-only check) on an unmounted device, or
> let it run at boot / from rescue mode.

**Hands-on lab (test VM only)**

**Step 1 — Build a filesystem with very few inodes** on the loop device from the
previous topic (unmount it first):

```bash
sudo umount /mnt/lab
sudo mkfs.ext4 -F -N 2000 -L labdata "${LOOP}p1"    # only 2000 inodes (wipes the lab fs)
sudo mount "${LOOP}p1" /mnt/lab && sudo chown "$USER" /mnt/lab
```

**Step 2 — Break: run out of inodes with plenty of space.**

```bash
for i in $(seq 1 3000); do : > /mnt/lab/f$i || break; done
df -h /mnt/lab        # lots of free space...
df -i /mnt/lab        # ...but IUse% 100%
```

You'll see `No space left on device` from the loop.

**Step 3 — Fix.** Delete files (`find /mnt/lab -name 'f*' -delete` — a scoped,
explicit path), or rebuild with more inodes. On real servers the culprits are PHP
session dirs, mail queues, caches and container layers with millions of tiny files.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `No space left on device`, `df -h` shows space | `df -i` | [Storage reference](01-storage-disk.md) |
| `Read-only file system` suddenly | `dmesg -T | grep -iE 'ext4|xfs|i/o'`, `findmnt -no OPTIONS /` | [Storage reference](01-storage-disk.md) |
| Need to shrink an xfs volume | Impossible — create a new smaller one and copy | This topic |
| Docker overlay errors on xfs | `xfs_info /var/lib/docker | grep ftype` | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

The filesystem type decides your options when space runs out (grow? shrink? reserve?)
and which repair tool applies.

**Next step**

Mounting — and the fstab line that can stop a server from booting.

### Mounts and /etc/fstab

**Level:** [L1 · Junior]

**Concept**

`mount` attaches a filesystem to a directory now; `/etc/fstab` lists what to mount at
boot. systemd turns each fstab line into a `.mount` unit. If a line refers to a device
that isn't there and lacks `nofail`, the boot waits 90 seconds and drops into
**emergency mode** — the most common self-inflicted "server won't boot".

```
# /etc/fstab
# DEVICE                                     MOUNTPOINT   TYPE  OPTIONS                                         DUMP PASS
UUID=8d1e4f0a-2c4b-4c1e-9a77-3f1d2e5b6a10    /            ext4  defaults                                        0    1
UUID=5a7c9d3e-1111-4abc-8def-0123456789ab    /data        xfs   defaults,nofail,x-systemd.device-timeout=10s    0    2
nas01.example.com:/export/backups            /mnt/backup  nfs4  defaults,_netdev,nofail,x-systemd.automount     0    0
/swap.img                                    none         swap  sw                                              0    0
```

**Key terms**

| Option | Meaning |
|--------|---------|
| `UUID=` / `LABEL=` | Stable identification; never `/dev/sdX` |
| `nofail` | If the device is missing, boot continues without it |
| `x-systemd.device-timeout=10s` | Wait 10 s instead of 90 s for the device |
| `_netdev` | Network filesystem: wait for the network |
| `x-systemd.automount` | Mount on first access (a dead NAS doesn't block boot) |
| `noatime`, `ro`, `noexec`, `nosuid` | Performance / safety options |
| PASS | fsck order at boot: 1 for `/`, 2 for others, 0 = never |

**See it on a real system**

```bash
findmnt                         # tree of everything mounted
findmnt -T /var/log             # which filesystem holds this path?
sudo findmnt --verify           # check fstab syntax and devices BEFORE rebooting
systemctl list-units --type=mount
```

```
$ sudo findmnt --verify
/data
   [E] unreachable source: UUID=5a7c9d3e-1111-4abc-8def-0123456789ab: No such file or directory

0 parse errors, 1 error, 0 warnings
```

→ `findmnt --verify` caught a UUID that doesn't exist. Run it after **every** fstab edit.

**Hands-on lab (test VM only)**

> ⚠️ Snapshot first and keep the hypervisor console open — step 2 makes the VM fall
> into emergency mode on purpose.

**Step 1 — Persistent mount, the safe way.** Re-attach the loop device and mount it via
fstab:

```bash
UUID=$(sudo blkid -s UUID -o value "${LOOP}p1"); echo "$UUID"
echo "UUID=$UUID /mnt/lab ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2" | sudo tee -a /etc/fstab
sudo systemctl daemon-reload
sudo findmnt --verify
sudo mount -a && findmnt /mnt/lab
```

Reboot: the loop device doesn't exist after reboot (nothing re-creates it), so the
"disk" is missing — and thanks to `nofail` the VM boots normally; the mount just times
out in the background after ~10 s (`systemctl status mnt-lab.mount`).

**Step 2 — Break.** Edit the line and remove `nofail,x-systemd.device-timeout=10s`.
Reboot. After a 90-second "A start job is running for /dev/disk/by-uuid/..." you land
in emergency mode ("root account is locked" on Ubuntu).

**Step 3 — Fix.** Reboot, use GRUB `e` → `init=/bin/bash` (section 7), then
`mount -o remount,rw /`, put `nofail` back (or comment the line), `sync`, reboot.
Finally remove the lab line from `/etc/fstab`.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| Boot hangs "A start job is running for /dev/disk/by-uuid/..." then emergency mode | Fix fstab from rescue; `findmnt --verify` | Section 7 |
| `mount: (hint) your fstab has been modified, but systemd still uses the old version; use 'systemctl daemon-reload' to reload.` | `sudo systemctl daemon-reload` | This topic |
| `umount: /data: target is busy.` | `sudo lsof +f -- /data`, `sudo fuser -vm /data` | [Storage reference](01-storage-disk.md) |
| Processes hang in D state on a dead NFS mount | `findmnt -t nfs,nfs4`; use `soft`/automount options | [Storage reference](01-storage-disk.md) |

**Why it matters for troubleshooting**

Adding a data disk for `/var/lib/docker` before a Dokploy install is routine; doing it
with UUID + `nofail` + `findmnt --verify` is what keeps that routine change from
becoming a 2 a.m. console session.

**Next step**

Inodes and the disk-full investigation — the most common page you'll get.

### The disk-full investigation

**Level:** [L1 · Junior]

**Concept**

"Disk full" has four common causes, and one command sequence separates them:
blocks used up (`df -h`), inodes used up (`df -i`), deleted-but-open files
(`lsof +L1`), or a different filesystem than you think (`findmnt -T PATH`). Root's 5%
reserve explains why some services fail while others keep writing. This is the
Ops Ladder L1 drill: fill `/var` until a service fails, then find which and why with
only `journalctl`, `df` and `du`.

```
 df -h full? ──yes──▶ du -xh --max-depth=1 / | sort -rh | head    → drill down
     │no
     ▼
 df -i full? ──yes──▶ find DIR -xdev -type f | cut -d/ -f2-3 | sort | uniq -c | sort -rn | head
     │no
     ▼
 lsof +L1 shows (deleted)? ──yes──▶ restart/reload the holder, or truncate via /proc/PID/fd/N
     │no
     ▼
 findmnt -T PATH: wrong filesystem? overlay? quota? read-only?
```

**Key terms**

| Term | Meaning |
|------|---------|
| `du -x` | Stay on one filesystem (don't descend into other mounts) |
| Reserved blocks | ext4's root-only 5% |
| Usual suspects | `/var/log` (journal, app logs), `/var/lib/docker` (images, logs, volumes), `/var/cache/apt`, `/tmp`, core dumps |

**See it on a real system**

```bash
df -hT -x tmpfs -x devtmpfs -x squashfs
df -i -x tmpfs -x devtmpfs -x squashfs
sudo du -xh --max-depth=1 /var 2>/dev/null | sort -rh | head
sudo lsof -nP +L1 2>/dev/null | head
journalctl --disk-usage; docker system df 2>/dev/null
```

```
$ sudo du -xh --max-depth=1 /var 2>/dev/null | sort -rh | head -5
21G     /var
17G     /var/lib
3.1G    /var/log
612M    /var/cache
88M     /var/backups
```

→ Keep drilling: `sudo du -xh --max-depth=1 /var/lib | sort -rh | head` — on Docker
hosts it's usually `/var/lib/docker`; see [Docker](30-learn-docker.md) before deleting
anything there.

**Hands-on lab (test VM only)**

**Step 1 — Build a service that writes as a non-root user**, like a database would:

```bash
sudo systemd-run --unit=lab-writer --uid=demo --property=StateDirectory=lab-writer \
  /bin/sh -c 'while true; do head -c 64K /dev/zero >> /var/lib/lab-writer/out.bin || exit 1; sleep 1; done'
systemctl status lab-writer --no-pager
```

**Step 2 — Break: fill /var** (on a test VM, where `/var` is on `/`):

```bash
df -h /var
AVAIL=$(df --output=avail -B1 /var | tail -1 | tr -d ' ')
sudo fallocate -l "$AVAIL" /var/tmp/fill.img      # uses all space normal users can get
df -h /var                                          # 100%, yet root still has the 5% reserve
```

Within seconds `lab-writer` (running as `demo`) fails, while root-owned processes such
as journald keep writing into the reserve.

**Step 3 — Find it with journalctl, df and du only, then fix.**

```bash
systemctl --failed
journalctl -u lab-writer --no-pager | tail -5      # "No space left on device"
journalctl -p err --since "15 min ago" --no-pager | tail -20
df -h; sudo du -xh --max-depth=2 /var 2>/dev/null | sort -rh | head
sudo rm /var/tmp/fill.img                           # a single named lab file
sudo systemctl reset-failed lab-writer; sudo rm -r /var/lib/lab-writer
```

Write your five-line note: which service failed first, which error text it logged,
and why (non-root user, no reserve).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Database or app crashes "No space left on device" | `df -h`, `df -i`, `lsof +L1` | [Storage reference](01-storage-disk.md) |
| Logs filled the disk | `du -sh /var/log/*`, logrotate status | Section 14 |
| Docker filled the disk | `docker system df`, container log sizes | [Containers playbook](26-playbook-containers-k8s.md) |
| Everything slow, disk at 100% | Also check I/O: `iostat -xz 1` | [Slow system playbook](23-playbook-slow-system.md) |

**Why it matters for troubleshooting**

This is the single most frequent page in operations. A fixed command sequence turns
it from panic into a two-minute routine — and alerting on 85% (L4 drill) turns it into
a non-event.

**Next step**

LVM — how to add space without downtime.

### LVM: physical volumes, volume groups and logical volumes

**Level:** [L1 · Junior]

**Concept**

LVM adds a flexible layer between partitions and filesystems. **Physical volumes**
(PVs: disks or partitions) are pooled into a **volume group** (VG); you carve
**logical volumes** (LVs) out of the pool and put filesystems on them. Need more space?
Add a disk to the VG and extend the LV — online. The Ubuntu server installer's guided
LVM layout often leaves part of the VG **unallocated**, so many "full" Ubuntu servers
have free space waiting in the VG.

```
  /dev/sda3 (PV)   /dev/sdb (PV)          ← physical volumes
        └────────┬───────┘
             ubuntu-vg (VG)  60G total, 29G free
             ├── ubuntu-lv (LV) 31G → ext4 → /
             └── [free extents 29G]       ← lvextend takes from here
```

**Key terms**

| Command | Purpose |
|---------|---------|
| `pvs`, `vgs`, `lvs` | Summaries (add `-a`/`-o +devices` for detail) |
| `pvcreate`, `vgextend VG PV` | Add a disk to a pool |
| `lvextend -r -L +10G VG/LV` | Grow LV **and** filesystem (`-r` = resize fs) |
| `lvextend -r -l +100%FREE VG/LV` | Use all free space |
| `lvcreate -s` | Snapshot (point-in-time copy for a risky change) |

**See it on a real system**

```bash
sudo vgs; sudo lvs
sudo pvs -o +pv_used
```

```
$ sudo vgs
  VG        #PV #LV #SN Attr   VSize   VFree
  ubuntu-vg   1   1   0 wz--n- <60.00g <29.00g
$ sudo lvs
  LV        VG        Attr       LSize  Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  ubuntu-lv ubuntu-vg -wi-ao---- 31.00g
```

→ 29 GB free in the VG: `sudo lvextend -r -l +100%FREE ubuntu-vg/ubuntu-lv` grows `/`
online in seconds — often the fastest fix for a full Ubuntu root.

**Hands-on lab (test VM only)**

> ⚠️ `pvcreate`, `vgcreate` and `lvreduce` overwrite or shrink data. Use loop devices
> here; on real servers verify devices with `lsblk -f` and take a backup or snapshot
> before any reduce.

**Step 1 — Build a VG from two loop "disks".**

```bash
truncate -s 1G /var/tmp/pv1.img /var/tmp/pv2.img
P1=$(sudo losetup --find --show /var/tmp/pv1.img); P2=$(sudo losetup --find --show /var/tmp/pv2.img)
sudo pvcreate "$P1" "$P2"
sudo vgcreate labvg "$P1"
sudo lvcreate -n data -L 500M labvg
sudo mkfs.ext4 /dev/labvg/data && sudo mkdir -p /mnt/lvm && sudo mount /dev/labvg/data /mnt/lvm
df -h /mnt/lvm
```

**Step 2 — Break: fill it.** A 500M LV holds less than 500M of data (journal, inode
tables, 5% reserve), so size the file from `df`:
`sudo fallocate -l "$(df --output=avail -B1 /mnt/lvm | tail -1 | tr -d ' ')" /mnt/lvm/big`
→ `df -h /mnt/lvm` at 100%.

**Step 3 — Fix online.** Add the second disk and grow while mounted:

```bash
sudo vgextend labvg "$P2"
sudo lvextend -r -l +100%FREE labvg/data
df -h /mnt/lvm                    # bigger, still mounted, no downtime
```

Clean up: `sudo umount /mnt/lvm; sudo vgremove -y labvg; sudo pvremove "$P1" "$P2";
sudo losetup -d "$P1" "$P2"; rm /var/tmp/pv1.img /var/tmp/pv2.img`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `/` full on Ubuntu but disk is big | `sudo vgs` (free extents?) | This topic |
| Extended the LV but `df` shows the old size | Forgot `-r` → `resize2fs DEVICE` / `xfs_growfs MOUNTPOINT` | [Storage reference](01-storage-disk.md) |
| Cloud/VM disk enlarged, VG not | `growpart DISK N`, then `pvresize PARTITION`, then `lvextend -r` | [Storage reference](01-storage-disk.md) |

**Why it matters for troubleshooting**

Giving Docker or a database more room without downtime is an LVM operation. It's also
the reason to put `/var/lib/docker` on its own LV: a runaway image build can't fill `/`.

**Next step**

Swap — the safety valve for memory, and why Kubernetes wants it off.

### Swap and memory pressure basics

**Level:** [L1 · Junior]

**Concept**

Swap is disk space used as overflow for memory pages that haven't been used recently.
A little swap lets the kernel move idle pages out and keep RAM for active work; heavy
swapping ("thrashing") makes everything slow. Ubuntu installs a swap file `/swap.img`.
`vm.swappiness` (default 60) tunes how eagerly the kernel swaps. kubeadm refuses to
set up a node with swap on unless kubelet is configured for it.

**Key terms**

| Term | Meaning |
|------|---------|
| `swapon --show` | Active swap areas |
| `si`/`so` in `vmstat` | Pages swapped in/out per second — non-zero and sustained = trouble |
| `vm.swappiness` | 0–200; lower = prefer dropping cache over swapping |
| OOM killer | What happens when RAM + swap run out (section 15, [Memory](04-memory.md)) |

**See it on a real system**

```bash
free -h
swapon --show
vmstat 1 5
cat /proc/sys/vm/swappiness
```

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       1.9Gi       212Mi        12Mi       1.9Gi       1.7Gi
Swap:          3.8Gi       420Mi       3.4Gi
```

→ "free" looks tiny but **available** (1.7 GiB) is what matters: buff/cache is
reclaimable. 420 MiB in swap with no ongoing `si`/`so` is harmless.

**Hands-on lab (test VM only)**

**Step 1 — Add a swap file.**

```bash
sudo fallocate -l 1G /swapfile2
sudo chmod 600 /swapfile2
sudo mkswap /swapfile2 && sudo swapon /swapfile2
swapon --show
```

**Step 2 — Break.** `sudo swapoff /swapfile2; sudo chmod 644 /swapfile2;
sudo swapon /swapfile2` → `swapon: /swapfile2: insecure permissions 0644, 0600
suggested.` (swap can contain secrets from memory). It is only a warning — the file is
activated anyway, which is exactly why nobody notices it on real servers.

**Step 3 — Fix and remove.** `sudo chmod 600 /swapfile2`, then disable it again with
`sudo swapoff /swapfile2 && sudo rm /swapfile2`. For a Kubernetes node: `sudo swapoff
-a` and comment the swap line in `/etc/fstab`.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| Box very slow, disk busy, `so` high | `vmstat 1`, `free -h`, top memory users | [Memory](04-memory.md), [Slow system playbook](23-playbook-slow-system.md) |
| kubeadm preflight `[WARNING Swap]` (v1.28+; older releases: `[ERROR Swap]: running with swap on is not supported. Please disable swap`), then kubelet never becomes healthy (`failSwapOn` is true by default) | `swapon --show`, `swapoff -a`, fstab; `journalctl -u kubelet` | [Kubernetes](31-learn-kubernetes.md) |
| Processes killed, no swap | `journalctl -k | grep -i 'out of memory'` | [Memory](04-memory.md) |

**Why it matters for troubleshooting**

Memory problems look like CPU or disk problems from the outside. `free` + `vmstat`
tell you in ten seconds whether swapping is the real cause.

**Next step**

Networking configuration — giving the server its address, routes and DNS.

---

## 9. Networking configuration on Ubuntu (basics)

> 📚 **Study path:** 1) Note: this section, then [Network reference](02-network.md) and [DNS reference](08-dns.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Networking: DNS ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS)), Networking Basics, Troubleshooting ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting)), then LFCS — Networking: Start, Stop and Check Status of Network Services ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) Video: KodeKloud *DNS in Linux for the Absolute Beginners!* ([YouTube](https://www.youtube.com/watch?v=9nCIjLlLVzY), 14 min) · 4) Practice: the "break DNS three ways" drill below; KodeKloud doesn't cover netplan specifics or resolver debugging, so keep [Arch Wiki: systemd-resolved](https://wiki.archlinux.org/title/Systemd-resolved) beside it

This area covers only what an operator needs to configure and read a server's network
settings. The theory (OSI layers, TCP, routing, DNS resolution, HTTP, TLS) and deep
troubleshooting are in [Learn: networking](28-learn-networking.md) and the
[Network reference](02-network.md).

### The ip command: links, addresses and routes

**Level:** [L1 · Junior]

**Concept**

`ip` shows and changes the kernel's live network state: **links** (interfaces, up or
down), **addresses** on them, **routes** (where to send packets), and **neighbours**
(ARP: IP → MAC on the local network). Changes made with `ip` are immediate but **not
persistent** — a reboot or `netplan apply` replaces them. Persistent config lives in
netplan.

**Key terms**

| Term | Meaning |
|------|---------|
| Interface names | `ens18`, `enp0s3` (predictable names based on hardware position); `eth0` on some clouds and inside containers |
| CIDR | `192.0.2.10/24` = address + network size |
| Default route | Where packets go when no more specific route matches (the gateway) |
| `ip route get IP` | Which route, interface and source IP the kernel will use for that destination |

**See it on a real system**

```bash
ip -br link
ip -br addr
ip route
ip route get 1.1.1.1
ip neigh
ip -s link show ens18          # counters: errors, drops
```

```
$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
ens18            UP             192.0.2.10/24 fe80::be24:11ff:fe2a:3b4c/64
docker0          DOWN           172.17.0.1/16
docker_gwbridge  UP             172.18.0.1/16
$ ip route
default via 192.0.2.1 dev ens18 proto static
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
172.18.0.0/16 dev docker_gwbridge proto kernel scope link src 172.18.0.1
192.0.2.0/24 dev ens18 proto kernel scope link src 192.0.2.10
$ ip route get 1.1.1.1
1.1.1.1 via 192.0.2.1 dev ens18 src 192.0.2.10 uid 1000
```

→ `docker_gwbridge` exists: this host runs Docker Swarm (Dokploy). Docker's
172.17/172.18 ranges must not overlap your on-prem networks, or traffic to those
networks silently goes into Docker bridges.

**Hands-on lab (test VM only)**

**Step 1 — Build a dummy interface** (harmless, local only):

```bash
sudo ip link add lab0 type dummy
sudo ip addr add 198.51.100.1/24 dev lab0
sudo ip link set lab0 up
ip route get 198.51.100.7          # → dev lab0
```

**Step 2 — Break.** `sudo ip link set lab0 down`, then `ip route get 198.51.100.7` —
the connected route disappeared; traffic for that network now follows the default
route (or `RTNETLINK answers: Network is unreachable` if there is none).

**Step 3 — Fix/clean.** `sudo ip link set lab0 up`, verify, then
`sudo ip link del lab0`. Note that nothing you did survives a reboot.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Can reach the gateway, nothing beyond | `ip route`, `ip route get IP` | [Network reference](02-network.md), [Site down playbook](25-playbook-site-down.md) |
| Interface `DOWN`/`NO-CARRIER` | `ip -br link`, cable/vNIC, `ethtool IFACE` | [Network reference](02-network.md) |
| Some internal subnet unreachable only from Docker hosts | Overlap with 172.17–172.31 — `ip route` | [Docker](30-learn-docker.md) |
| Packet drops/errors | `ip -s link` | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting**

`ip route get` answers "which way will this packet go?" with certainty — the Ops
Ladder's first move for "the gateway answers, nothing beyond it does".

**Next step**

netplan — making the configuration persistent.

### netplan and systemd-networkd

**Level:** [L1 · Junior]

**Concept**

Ubuntu describes network configuration in YAML files under `/etc/netplan/`. netplan
**renders** them into config for a backend — **systemd-networkd** on servers,
NetworkManager on desktops — which then applies them. On cloud-init installs the file
is often `50-cloud-init.yaml`, and cloud-init may regenerate it unless told not to.

```
 /etc/netplan/*.yaml ──netplan generate──▶ /run/systemd/network/*.network ──▶ systemd-networkd ──▶ kernel
                                                                                      │
                                                                     DNS settings ──▶ systemd-resolved
```

A static configuration:

```yaml
# /etc/netplan/01-static.yaml   (mode 600)
network:
  version: 2
  renderer: networkd
  ethernets:
    ens18:
      dhcp4: false
      addresses:
        - 192.0.2.10/24
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53, 192.0.2.54]
        search: [example.com]
```

(`gateway4:` is deprecated — use `routes: - to: default`.)

**Key terms**

| Command | Purpose |
|---------|---------|
| `netplan get` | Show the merged configuration |
| `netplan generate` | Render backend files (syntax check) |
| `netplan try` | Apply, and **automatically roll back after 120 s** unless you press Enter |
| `netplan apply` | Apply for good |
| `networkctl status IFACE` | networkd's view: state, addresses, gateway, DNS |
| `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` | `network: {config: disabled}` stops cloud-init rewriting netplan |

**See it on a real system**

```bash
ls -l /etc/netplan/
sudo netplan get
networkctl list
networkctl status ens18
```

```
$ networkctl list
IDX LINK            TYPE     OPERATIONAL SETUP
  1 lo              loopback carrier     unmanaged
  2 ens18           ether    routable    configured
  3 docker0         bridge   no-carrier  unmanaged

3 links listed.
```

→ `routable` + `configured` = networkd manages ens18 and it has a route out. Docker's
bridges are `unmanaged` — Docker owns them, not netplan.

**Hands-on lab (test VM only)**

> ⚠️ Do this from the hypervisor console, not over SSH. On real servers always use
> `netplan try` and keep a second session or console.

**Step 1 — Convert DHCP to static** using your VM's current IP/gateway (from
`ip -br a` and `ip route`): write the YAML above with your values, `sudo chmod 600`
it, move the old file aside (`sudo mv /etc/netplan/50-cloud-init.yaml /root/`), then
`sudo netplan try` and confirm with Enter.

**Step 2 — Break it twice.** (a) Indent a line with a **tab** and run
`sudo netplan generate` — netplan rejects the YAML and names the file, line and column.
(b) Set a wrong gateway (`via: 192.0.2.254`) and run `sudo netplan try` — you lose
outside connectivity, do nothing, and after 120 s netplan rolls back by itself.

**Step 3 — Fix** the YAML and apply. Restore the original file at the end if you prefer
DHCP.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `netplan apply` cut off SSH | Console; restore the old YAML; next time `netplan try` | This topic |
| Changes lost after reboot | cloud-init regenerated the file — disable its network config | This topic |
| `Permissions for /etc/netplan/X.yaml are too open` warning | `sudo chmod 600 /etc/netplan/*.yaml` | — |
| Boot waits on `systemd-networkd-wait-online` | `networkctl list` — an interface never configured; `optional: true` | Section 7 |

**Why it matters for troubleshooting**

On-prem Ubuntu servers get their address, gateway **and DNS servers** from netplan. A
bad upstream DNS line here is one of the three DNS breaks in the Ops Ladder L2 drill.

**Next step**

systemd-resolved — how the server resolves names.

### systemd-resolved and /etc/resolv.conf

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Programs resolve names through glibc (`getaddrinfo`), which follows
`/etc/nsswitch.conf`: first `/etc/hosts` ("files"), then DNS. On Ubuntu,
`/etc/resolv.conf` is a symlink pointing glibc at **127.0.0.53**, a local stub run by
**systemd-resolved**, which caches and forwards queries to the upstream servers it
learned from netplan/networkd (per interface). `dig` skips nsswitch and `/etc/hosts`
entirely — so `dig` and `curl` can disagree. `getent ahosts` shows what applications
really get.

```
 curl / apt / your app
    │ getaddrinfo()
    ▼
 /etc/nsswitch.conf  "hosts: files dns"
    ├── files → /etc/hosts                       (checked first!)
    └── dns   → /etc/resolv.conf → nameserver 127.0.0.53
                     │
                     ▼
             systemd-resolved (cache, per-link DNS, search domains)
                     │
                     ▼
             upstream DNS from netplan: 192.0.2.53, 192.0.2.54

 dig HOST → asks the server in /etc/resolv.conf directly (no /etc/hosts, no nsswitch)
```

**Key terms**

| Term | Meaning |
|------|---------|
| Stub resolver | 127.0.0.53 — resolved's local listener |
| `/run/systemd/resolve/resolv.conf` | File listing the **real** upstream servers (kubelet should use this, not the stub) |
| Search domain | Suffix tried for short names (`app` → `app.example.com`) |
| `resolvectl` | resolved's control tool |

**See it on a real system**

```bash
ls -l /etc/resolv.conf
resolvectl status
resolvectl query app.example.com
getent ahosts app.example.com      # what curl will get (includes /etc/hosts)
dig +short app.example.com         # what the DNS server says
grep '^hosts:' /etc/nsswitch.conf
```

```
$ resolvectl status
Global
       Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
resolv.conf mode: stub

Link 2 (ens18)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53 192.0.2.54
        DNS Domain: example.com
```

**Hands-on lab (test VM only)**

The Ops Ladder L2 drill — break DNS three ways, diagnose each with `getent`,
`resolvectl` and `tcpdump`:

**Break 1 — bad upstream in netplan.** Set `nameservers: addresses: [192.0.2.250]`
(nothing answers there), `netplan apply`. `getent ahosts example.com` hangs then fails;
`sudo tcpdump -ni any port 53` shows queries leaving for 192.0.2.250 and no answers.

**Break 2 — resolved stopped.** `sudo systemctl stop systemd-resolved`. Now
`getent ahosts example.com` fails instantly; `resolvectl status` can't connect;
`ss -lunp | grep :53` shows nothing on 127.0.0.53.

**Break 3 — wrong /etc/hosts line.** Add `203.0.113.99 example.com` to `/etc/hosts`.
`getent ahosts example.com` and `curl` use 203.0.113.99, while `dig +short example.com`
shows the real address — the disagreement is the clue.

**Fix each** (restore netplan + apply, `systemctl start systemd-resolved`, remove the
hosts line) and write one line per break: symptom → evidence → fix.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `curl: (6) Could not resolve host: HOST` | `getent ahosts HOST`, `resolvectl query HOST`, `sudo tcpdump -ni any port 53` | [DNS](08-dns.md), [Site down playbook](25-playbook-site-down.md) |
| `dig` works, `curl` doesn't (or the reverse) | `getent ahosts HOST` vs `dig`, check `/etc/hosts` | [Learn: networking](28-learn-networking.md) |
| Containers can't resolve, host can | Docker skips the 127.0.0.53 stub | [Docker](30-learn-docker.md) |
| CoreDNS "Loop ... detected" | kubelet uses the stub resolv.conf → point it at `/run/systemd/resolve/resolv.conf` | [Kubernetes](31-learn-kubernetes.md) |

**Why it matters for troubleshooting**

DNS was half of the original investigation. Knowing that `curl` and `dig` take
different paths, and where resolved gets its upstreams, shortens it to a few commands.
Turn on resolver debug logs when you need them: `sudo resolvectl log-level debug`,
reproduce, `journalctl -u systemd-resolved`, then `sudo resolvectl log-level info`.

**Next step**

Listening sockets — which program owns which port.

### Ports and listening sockets with ss

**Level:** [L1 · Junior]

**Concept**

A server program asks the kernel to **listen** on an address and port. The address
decides who can connect: `0.0.0.0` (all IPv4 addresses), `[::]` or `*` (all addresses,
usually IPv6 + IPv4), `127.0.0.1` (this machine only), or one specific IP. Only one
program can listen on the same address:port (unless both opt in with `SO_REUSEPORT`).
`ss` lists sockets; `-p` (with sudo) adds the owning process.

**Key terms**

| `ss` flag | Meaning |
|-----------|---------|
| `-t` / `-u` | TCP / UDP |
| `-l` | Listening sockets only |
| `-n` | Numeric (no name lookups — faster, unambiguous) |
| `-p` | Process (needs sudo for other users' processes) |
| `'sport = :443'` | Filter by local port |
| Recv-Q on LISTEN | Connections waiting for `accept()` — non-zero and growing = app overloaded |

**See it on a real system**

```bash
sudo ss -ltnp
sudo ss -lunp
sudo ss -ltnp 'sport = :443'
```

```
$ sudo ss -ltnp
State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
LISTEN 0      4096    127.0.0.53%lo:53         0.0.0.0:*     users:(("systemd-resolve",pid=612,fd=14))
LISTEN 0      511                 *:80               *:*     users:(("apache2",pid=1125,fd=3),("apache2",pid=1124,fd=3),("apache2",pid=1123,fd=3))
LISTEN 0      511                 *:443              *:*     users:(("apache2",pid=1125,fd=4),("apache2",pid=1124,fd=4),("apache2",pid=1123,fd=4))
LISTEN 0      5           127.0.0.1:8080       0.0.0.0:*     users:(("python3",pid=2410,fd=3))
LISTEN 0      4096                *:22               *:*     users:(("sshd",pid=901,fd=3),("systemd",pid=1,fd=126))
```

→ Apache holds 80 and 443 on all addresses (`*` = every IPv4 and IPv6 address) — the
exact blocker for Traefik.

→ The python app on 127.0.0.1:8080 is reachable only from this host ("works on
localhost, not from other machines"). On a LISTEN line, Send-Q is the backlog the
program asked for: 511 for Apache, 4096 (systemd's socket default) for sshd, only 5
for Python's `http.server`.

**Hands-on lab (test VM only)**

**Step 1.** Start two throwaway servers:
`python3 -m http.server 8081 --bind 127.0.0.1 &` and
`python3 -m http.server 8082 &`. Compare them in `sudo ss -ltnp`. From another machine,
`curl http://VM_IP:8081/` → "Connection refused"; 8082 works (if no firewall blocks it).

**Step 2 — Break.** Start a third server on 8082: `python3 -m http.server 8082` →
`OSError: [Errno 98] Address already in use`. Same error class as Traefik on 443 while
Apache holds it.

**Step 3 — Fix.** Find the holder (`sudo ss -ltnp 'sport = :8082'`), decide which one
should own the port, stop the other (`kill %2`, then check with `ss` again).

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `bind: Address already in use` / `Errno 98` | `sudo ss -ltnp 'sport = :PORT'`, `systemctl list-sockets` | [Ports playbook](22-playbook-ports-inventory.md) |
| Works on localhost, not remotely | Listening on 127.0.0.1? Firewall? | Section 16, [Network reference](02-network.md) |
| `Connection refused` vs `Connection timed out` | Refused = nothing listening/REJECT; timeout = DROP/route/host down | [Learn: networking](28-learn-networking.md) |

**Why it matters for troubleshooting**

`sudo ss -ltnp` is the first command of every port question and the start of the L1
exit test. Section 17 continues the walk from port to process to unit to config to logs.

**Next step**

SSH — how you reach all of these servers, and how to lock it down safely.

---

## 10. SSH

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (the SSH lesson) ([course](https://kodekloud.com/courses/the-linux-basics-course)), then LFCS — Networking: Configure SSH Servers and Clients ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: this section, then [SSH & remote access reference](09-ssh-remote-access.md) · 3) Later, after CKA: *Certified Kubernetes Security Specialist (CKS)* — System Hardening ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Practice: the L0 exit-test task in "Hardening sshd safely" (a sudo user with key-only SSH)

### Keys, the agent and the client config

**Level:** [L0 · Fresher]

**Concept**

SSH key authentication uses a **key pair**: the private key stays on your laptop
(protected by a passphrase), the public key goes into `~/.ssh/authorized_keys` on the
server. At login the server sends a challenge only the private key can sign. The
**agent** holds decrypted keys in memory so you type the passphrase once. The client
config `~/.ssh/config` turns long commands into short names and handles bastions with
`ProxyJump`.

```
 laptop                                              server
 ~/.ssh/id_ed25519      (private, 600, passphrase)   ~/.ssh/authorized_keys  (600)
 ~/.ssh/id_ed25519.pub  ──── ssh-copy-id ─────────▶  one public key per line
 ssh-agent (holds the unlocked key)                  ~/.ssh (700), home not group/world-writable

 ssh web01  ──▶ ~/.ssh/config: Host web01 → HostName 192.0.2.10, User deploy, ProxyJump bastion
```

**Key terms**

| Term | Meaning |
|------|---------|
| ed25519 | Modern key type — use it unless something old needs RSA |
| `known_hosts` | Fingerprints of servers you've trusted; protects against impersonation |
| `IdentitiesOnly yes` | Offer only the configured key (avoids "Too many authentication failures") |
| `ProxyJump` (`-J`) | Hop through a bastion without copying keys to it |
| Agent forwarding | Lets the remote host use your agent — risky on shared hosts; prefer ProxyJump |

**See it on a real system**

```bash
ls -l ~/.ssh/
ssh-add -l                                   # keys loaded in the agent
ssh -G web01 | grep -E '^(hostname|user|identityfile|proxyjump) '   # effective client config
ssh-keygen -lf ~/.ssh/id_ed25519.pub         # fingerprint of your key
```

A client config:

```
# ~/.ssh/config
Host bastion
    HostName 203.0.113.5
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes

Host web01
    HostName 192.0.2.10
    User deploy
    ProxyJump bastion
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes

Host *
    ServerAliveInterval 30
```

**Hands-on lab (test VM only)**

**Step 1 — Build key login.**

```bash
ssh-keygen -t ed25519 -C "ops@laptop" -f ~/.ssh/id_ed25519     # set a passphrase
ssh-copy-id -i ~/.ssh/id_ed25519.pub labuser@VM_IP
ssh labuser@VM_IP 'id; ls -ld ~ ~/.ssh ~/.ssh/authorized_keys'
```

**Step 2 — Break the server-side permissions.** On the VM run
`chmod 777 /home/labuser` (lab only). Try to log in again: the key is refused and you
fall back to a password prompt or `Permission denied (publickey)`. The server log
explains: `sudo journalctl -u ssh -n 20` shows `Authentication refused: bad ownership
or modes for directory /home/labuser`.

**Step 3 — Fix** with `chmod 755 /home/labuser` (or 750), `chmod 700 ~/.ssh`,
`chmod 600 ~/.ssh/authorized_keys`. Then run `ssh -v labuser@VM_IP` and find the lines
where the client offers your key and the server accepts it.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `Permission denied (publickey)` | `ssh -vvv USER@HOST` (which keys were offered?), server: `journalctl -u ssh` (`sshd` on RHEL) | [SSH reference](09-ssh-remote-access.md) |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | Verify the new fingerprint out of band, then `ssh-keygen -R HOST` | [SSH reference](09-ssh-remote-access.md) |
| `Too many authentication failures` | Agent offers many keys → `IdentitiesOnly yes` + `IdentityFile` | This topic |
| Login hangs for ~10 s before the prompt | `UseDNS`/GSSAPI lookups → `ssh -v` shows where it waits | [SSH reference](09-ssh-remote-access.md) |

**Why it matters for troubleshooting**

You can't fix a server you can't reach. Most SSH failures are permissions or the wrong
key, and `ssh -v` on the client plus the server's journal settle them in a minute.

**Next step**

The server side: sshd and how its configuration is really assembled.

### The sshd server and its configuration

**Level:** [L1 · Junior]

**Concept**

`sshd` reads `/etc/ssh/sshd_config`. On Ubuntu that file begins with
`Include /etc/ssh/sshd_config.d/*.conf`, and for most settings **the first value sshd
reads wins**. So a drop-in such as cloud-init's `50-cloud-init.conf` containing
`PasswordAuthentication yes` beats `PasswordAuthentication no` written further down in
the main file. Don't guess — ask sshd for its effective configuration with `sshd -T`.

```
 /etc/ssh/sshd_config
   Include /etc/ssh/sshd_config.d/*.conf   ← read FIRST, in name order
       00-hardening.conf   PasswordAuthentication no    ← first value: WINS
       50-cloud-init.conf  PasswordAuthentication yes   ← ignored (already set)
   ...
   PasswordAuthentication yes                            ← ignored
```

**Key terms**

| Command | Purpose |
|---------|---------|
| `sudo sshd -t` | Syntax check — run before every reload |
| `sudo sshd -T` | Print the **effective** configuration |
| `sudo sshd -T -C user=deploy,host=203.0.113.9,addr=203.0.113.9` | Effective config for a specific connection (`Match` blocks) |
| Unit name | `ssh.service` + `ssh.socket` on Ubuntu, `sshd.service` on RHEL |

**See it on a real system**

```bash
grep -n '^Include' /etc/ssh/sshd_config
ls /etc/ssh/sshd_config.d/
sudo sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|allowgroups|maxauthtries) '
```

```
$ sudo sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication) '
port 22
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication yes
```

→ Password logins are still allowed even though someone "disabled" them — check which
drop-in sets it (`grep -r PasswordAuthentication /etc/ssh/sshd_config.d/`).
`without-password` is the older spelling of `prohibit-password`.

**Hands-on lab (test VM only)**

**Step 1.** Add `PasswordAuthentication no` at the **end** of `/etc/ssh/sshd_config`,
`sudo sshd -t && sudo systemctl reload ssh`, then `sudo sshd -T | grep passwordauth`.

**Step 2 — Break/learn.** Create `/etc/ssh/sshd_config.d/50-test.conf` with
`PasswordAuthentication yes`, reload, and check again: `yes` wins because the drop-in
is read first.

**Step 3 — Fix the right way.** Remove both lab edits and create
`/etc/ssh/sshd_config.d/00-hardening.conf` (next topic). Verify with `sshd -T`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Setting "has no effect" | `sudo sshd -T | grep -i SETTING`, `ls /etc/ssh/sshd_config.d/` | This topic |
| sshd won't start after an edit | `sudo sshd -t` shows the line | [SSH reference](09-ssh-remote-access.md) |
| `Failed to restart sshd.service: Unit sshd.service not found.` on Ubuntu | The unit is `ssh`; `sshd.service` is only an alias that exists while `ssh.service` is enabled (not on a socket-activated 24.04) | Section 6 |

**Why it matters for troubleshooting**

"I disabled passwords but the audit says they're on" is the drop-in order every
time. `sshd -T` is the truth.

**Next step**

Hardening sshd without locking yourself out.

### Hardening sshd safely

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

A hardened SSH server allows only key logins, no direct root login, only the people
who need it, and few guesses per connection. The **procedure** matters as much as the
settings: keep your current session open, syntax-check, reload (not restart), test a
new login from a second terminal, and only then close the first one.

```
# /etc/ssh/sshd_config.d/00-hardening.conf
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
AllowGroups sshusers
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
AllowAgentForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
```

**Key terms**

| Setting | Why |
|---------|-----|
| `PasswordAuthentication no` + `KbdInteractiveAuthentication no` | Both paths for passwords closed |
| `PermitRootLogin no` | Log in as yourself, then sudo — gives an audit trail |
| `AllowGroups sshusers` | Allow-list; **add yourself to the group first** |
| `MaxAuthTries 3` | Fewer guesses per connection |
| `AllowTcpForwarding` | Leave on if you use tunnels (next topic); `no` blocks them |

**See it on a real system**

```bash
sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|allowgroups|maxauthtries|x11forwarding) '
getent group sshusers
sudo journalctl -u ssh --since today | grep -cE 'Failed password|Invalid user'
```

**Hands-on lab (test VM only) — the L0 exit-test task**

Goal: a sudo user with **key-only** SSH. Keep the hypervisor console open.

**Step 1 — Build.**

```bash
sudo adduser ops                          # set a password (needed for sudo, not for SSH)
sudo usermod -aG sudo ops
sudo groupadd -f sshusers && sudo usermod -aG sshusers ops
sudo usermod -aG sshusers "$USER"         # don't lock yourself out
# from your laptop:  ssh-copy-id -i ~/.ssh/id_ed25519.pub ops@VM_IP
```

**Step 2 — Harden with the safe procedure.**

```bash
sudoedit /etc/ssh/sshd_config.d/00-hardening.conf     # paste the block above
sudo sshd -t && sudo systemctl reload ssh
# NEW terminal on the laptop, old one stays open:
ssh ops@VM_IP 'sudo -v && echo KEY+SUDO OK'
ssh -o PubkeyAuthentication=no ops@VM_IP              # must fail: Permission denied (publickey)
```

**Step 3 — Break and fix.** Remove yourself from `sshusers`
(`sudo gpasswd -d "$USER" sshusers`), open a new SSH session → refused; the journal says
`User USER from 192.0.2.50 not allowed because none of user's groups are listed in
AllowGroups`. Fix it from the session you kept open (or the console).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Locked out after hardening | Console; `sshd -T`; `journalctl -u ssh -n 50` | [SSH reference](09-ssh-remote-access.md) |
| `not allowed because none of user's groups are listed in AllowGroups` | `id USER`, `getent group sshusers` | This topic |
| Thousands of failed logins in the journal | fail2ban, firewall allow-list | Section 16 |

**Why it matters for troubleshooting**

Hardening is a change like any other: plan the rollback (the open session, the console)
before you make it. That habit matters even more for firewalls and netplan.

**Next step**

Tunnels — reaching services you deliberately did not expose.

### SSH tunnels and port forwarding

**Level:** [L1 · Junior]

**Concept**

SSH can carry other TCP connections inside its encrypted session. **Local forwarding**
(`-L`) makes a port on your laptop lead to a host:port reachable **from the server** —
perfect for admin UIs bound to localhost (Dokploy's UI on 3000, a database, Traefik's
dashboard) that you don't want open on the internet. **Remote forwarding** (`-R`) does
the reverse. **Dynamic** (`-D`) gives you a SOCKS proxy.

```
 -L 13000:127.0.0.1:3000
 laptop:13000 ══════ SSH (port 22) ══════▶ server ──▶ 127.0.0.1:3000 (Dokploy UI)
 browser → http://localhost:13000

 -L 15432:db01.internal:5432
 laptop:15432 ══════ SSH ══════▶ bastion ──▶ db01.internal:5432

 -R 18080:127.0.0.1:8080
 server:18080 ══════ SSH ══════▶ laptop ──▶ 127.0.0.1:8080 (your dev app, shown to the server)
```

**Key terms**

| Flag | Meaning |
|------|---------|
| `-L LPORT:HOST:PORT` | Local forward; HOST is resolved **on the server** |
| `-R RPORT:HOST:PORT` | Remote forward |
| `-D 1080` | SOCKS proxy |
| `-N` | No remote command (tunnel only); `-f` go to background |
| `AllowTcpForwarding` | Server-side switch |

**See it on a real system**

```bash
ssh -N -L 13000:127.0.0.1:3000 deploy@app-server.example.com     # then open http://localhost:13000
ss -ltn 'sport = :13000'                                         # on the laptop: the tunnel listens locally
```

**Hands-on lab (test VM only)**

**Step 1 — Build.** On the VM: `python3 -m http.server 8080 --bind 127.0.0.1`. From
the laptop: `ssh -N -L 18080:127.0.0.1:8080 labuser@VM_IP`, then
`curl -s http://localhost:18080/ | head -3`.

**Step 2 — Break twice.** (a) Start the same tunnel twice → the second fails with
`bind [127.0.0.1]:18080: Address already in use`. (b) On the VM add
`AllowTcpForwarding no` to the hardening drop-in, reload, reconnect the tunnel and curl
again → the client prints `channel 2: open failed: administratively prohibited: open
failed`.

**Step 3 — Fix** by removing the setting (or allowing it per group with a `Match
Group` block) and reloading.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `administratively prohibited` | `sudo sshd -T | grep -i allowtcpforwarding` | This topic |
| Tunnel up, `connect failed: Connection refused` in the client output | Nothing listening on the target from the server's view — `ss -ltn` on the server | Section 9 |
| Tunnel drops after idle | `ServerAliveInterval 30` in client config | [SSH reference](09-ssh-remote-access.md) |

**Why it matters for troubleshooting**

Tunnels let you keep admin ports (Dokploy 3000, databases, dashboards) bound to
localhost or firewalled, and still reach them — fewer open ports, fewer incidents.

**Next step**

Scheduling — things that run without you.

---

## 11. Scheduling: cron, systemd timers and at

> 📚 **Study path:** 1) Note: this section, then [Services & systemd reference](07-services-systemd.md) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (the cron lesson) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) Read: [Arch Wiki: systemd](https://wiki.archlinux.org/title/Systemd), then follow its link to the timers page · 4) Practice: port one cron job to a timer, and arm the `at`/`systemd-run` rollback before your next UFW or netplan change

### cron and the crontab format

**Level:** [L1 · Junior]

**Concept**

cron runs commands on a schedule. Each user has a **crontab** (`crontab -e`); the
system has `/etc/crontab` and drop-ins in `/etc/cron.d/` (these have an extra **user**
field); and scripts in `/etc/cron.daily/`, `weekly/`, `monthly/` run via `run-parts`.
cron jobs run with a **minimal environment** — almost no PATH, no TTY, your `.bashrc`
not loaded — which is why "works by hand, fails in cron" is so common.

```
 ┌───────── minute (0-59)
 │ ┌─────── hour (0-23)
 │ │ ┌───── day of month (1-31)
 │ │ │ ┌─── month (1-12)
 │ │ │ │ ┌─ day of week (0-7, 0 and 7 = Sunday)
 │ │ │ │ │
 30 2 * * 1-5  /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1      ← user crontab
 30 2 * * 1-5  root  /usr/local/bin/backup.sh                             ← /etc/cron.d/backup (user field!)

 */5 * * * *   every 5 minutes        0 */6 * * *   every 6 hours at :00
 @reboot       once at boot           @daily        = 0 0 * * *
```

**Key terms**

| Term | Meaning |
|------|---------|
| `crontab -l` / `-e` / `-u USER -l` | List / edit / another user's crontab |
| `%` | Means "newline" in crontab — escape as `\%` (e.g. in `date +\%F`) |
| `MAILTO=` | Where output goes; without a mail system output is **discarded** |
| run-parts naming | Scripts in `cron.daily/` must have **no dot** in the name (`backup.sh` is skipped); files in `/etc/cron.d/` with dots are ignored too |
| `flock -n` | Prevents overlapping runs |

**See it on a real system**

```bash
crontab -l
sudo ls /var/spool/cron/crontabs/            # every user's crontab (Ubuntu)
cat /etc/crontab; ls /etc/cron.d/ /etc/cron.daily/
journalctl -u cron --since today --no-pager | tail     # RHEL: crond, /var/log/cron
run-parts --test /etc/cron.daily              # which scripts WOULD run
```

```
$ journalctl -u cron --since today --no-pager | tail -3
Oct 03 02:30:01 web01 CRON[50122]: (deploy) CMD (/usr/local/bin/backup.sh >> /var/log/backup.log 2>&1)
Oct 03 02:30:01 web01 CRON[50121]: (CRON) info (No MTA installed, discarding output)
Oct 03 02:30:01 web01 CRON[50121]: pam_unix(cron:session): session closed for user deploy
```

→ The job ran, and something it printed was thrown away ("No MTA installed") — that
lost output is often the error you're looking for. Here the job redirects everything,
so the discarded text can only come from the redirection itself failing (for example
`deploy` may not create `/var/log/backup.log` — the shell's "Permission denied" was
the lost message). Redirect output to a log or the
journal (`| logger -t backup`).

**Hands-on lab (test VM only)**

**Step 1 — Build.** `crontab -e` and add
`* * * * * date >> /tmp/cron-test.log 2>&1`. After two minutes, `cat /tmp/cron-test.log`.

**Step 2 — Break it three ways**, one at a time, and observe in `journalctl -u cron`:
(a) `* * * * * date +%F >> /tmp/cron-test.log` — the `%` cuts the command;
(b) `* * * * * mytool --check` where `mytool` is in `/usr/local/sbin` or `~/bin` —
works in your shell, "not found" in cron (PATH);
(c) put a script in `/etc/cron.daily/lab.sh` and check `run-parts --test
/etc/cron.daily` — it's not listed (the dot).

**Step 3 — Fix**: escape `\%`, use absolute paths (or set `PATH=` at the top of the
crontab), rename to `lab` without the dot. Remove the lab entries.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Job "didn't run" | `journalctl -u cron` (did cron start it?), then the job's own output/log | [systemd reference](07-services-systemd.md) |
| Works by hand, fails in cron | Compare environments: add `env > /tmp/cron-env.txt` as a job | This topic |
| Two runs overlap and corrupt data | `flock -n /run/lock/JOB.lock CMD` | This topic |
| Job ran at the wrong time | `timedatectl` (timezone of the server, not yours) | [Time & NTP](12-time-ntp.md) |

**Why it matters for troubleshooting**

Old servers are full of cron jobs nobody remembers — log cleaners, backups, certificate
renewals. During a migration, `crontab -l` for every user and `/etc/cron.d/` are part of
the inventory, or the job silently stops when the app moves.

**Next step**

systemd timers — the modern alternative with logs and dependencies built in.

### systemd timers

**Level:** [L1 · Junior]

**Concept**

A timer unit (`NAME.timer`) triggers a service unit (`NAME.service`, usually
`Type=oneshot`) on a schedule. Compared with cron you get: output in the journal,
exit status in `systemctl status`, `Persistent=true` to catch up on runs missed while
the machine was off, randomised delays to avoid thundering herds, and all the unit
features (User=, sandboxing, dependencies, resource limits).

```
 health-report.timer  ──(OnCalendar=*-*-* 07:00)──▶  health-report.service (Type=oneshot)
                                                        └─ ExecStart=/usr/local/bin/health-report.sh
                                                           output → journal (journalctl -u health-report)
```

**Key terms**

| Directive | Meaning |
|-----------|---------|
| `OnCalendar=` | Wall-clock schedule: `daily`, `Mon..Fri 02:30`, `*-*-* *:00/15:00` |
| `OnBootSec=`, `OnUnitActiveSec=` | Relative: after boot / since last run |
| `Persistent=true` | Run at boot if a scheduled run was missed |
| `RandomizedDelaySec=` | Spread runs out |
| `systemctl list-timers` | Next/last run for every timer |
| `systemd-analyze calendar EXPR` | Test a schedule expression |

**See it on a real system**

```bash
systemctl list-timers --all
systemd-analyze calendar 'Mon..Fri *-*-* 02:30:00'
systemctl cat logrotate.timer
```

```
$ systemctl list-timers --all | head -5
NEXT                        LEFT       LAST                        PASSED  UNIT                  ACTIVATES
Sat 2026-10-03 10:39:00 UTC 21min      Sat 2026-10-03 10:09:01 UTC 9min ago phpsessionclean.timer phpsessionclean.service
Sun 2026-10-04 00:00:00 UTC 13h        Sat 2026-10-03 00:00:00 UTC 10h ago  logrotate.timer       logrotate.service
Sun 2026-10-04 06:34:12 UTC 20h        Sat 2026-10-03 06:21:40 UTC 3h ago   apt-daily-upgrade.timer apt-daily-upgrade.service
$ systemd-analyze calendar 'Mon..Fri *-*-* 02:30:00'
  Original form: Mon..Fri *-*-* 02:30:00
Normalized form: Mon..Fri *-*-* 02:30:00
    Next elapse: Mon 2026-10-05 02:30:00 UTC
       From now: 1 day 16h left
```

→ `apt-daily-upgrade.timer` is what runs unattended-upgrades around 06:00 — the usual
suspect when "Docker restarted by itself this morning" (section 16).

**Hands-on lab (test VM only)**

**Step 1 — Build a timer** for a simple check:

```ini
# /etc/systemd/system/disk-check.service
[Unit]
Description=Lab: log disk usage

[Service]
Type=oneshot
ExecStart=/usr/bin/df -h /

# /etc/systemd/system/disk-check.timer
[Unit]
Description=Lab: run disk-check every 2 minutes

[Timer]
OnCalendar=*:0/2
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now disk-check.timer
systemctl list-timers disk-check.timer
journalctl -u disk-check.service -n 20 --no-pager      # after 2 minutes
```

**Step 2 — Break.** Change `ExecStart=` to `/usr/bin/df -h /nonexistent`,
daemon-reload, wait for a run: `systemctl status disk-check.service` shows
`status=1/FAILURE` and the error is in the journal — something cron would have
discarded.

**Step 3 — Fix**, then `sudo systemctl disable --now disk-check.timer`. Section 12's
health-report script gets scheduled exactly this way.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Timer never fires | `systemctl list-timers --all` (NEXT = n/a?), timer not enabled/started | This topic |
| `Unit X.service not found` from the timer | Service name doesn't match, or no `Unit=` | This topic |
| Job ran at a surprising time | `RandomizedDelaySec=`, `systemd-analyze calendar` | This topic |

**Why it matters for troubleshooting**

Every timer run leaves a status and a log, which turns "did the backup run?" into one
command. New scheduled jobs should be timers.

**Next step**

How to choose between cron and timers.

### Timers versus cron

**Level:** [L1 · Junior]

**Concept**

Both work. Choose deliberately and be consistent per server.

| Need | cron | systemd timer |
|------|------|---------------|
| Quick one-liner, user-level | Easiest | More files |
| Output and exit status recorded | Only if you redirect | Automatic (journal + status) |
| Catch up after downtime | anacron (daily/weekly/monthly jobs only; not installed on Ubuntu servers by default) | `Persistent=true` |
| Prevent overlap | `flock` | Built in (a running service isn't started twice) |
| Resource limits, sandboxing, run as service user | Manual | `User=`, `Nice=`, `MemoryMax=`, `ProtectSystem=` |
| Dependencies ("only if /data is mounted") | No | `RequiresMountsFor=` |
| Visible schedule overview | `crontab -l` per user + files | `systemctl list-timers` |
| Portable to non-systemd systems/containers | Yes | No |

**Key terms**

| Term | Meaning |
|------|---------|
| anacron | Runs daily/weekly/monthly jobs missed while the machine was off (laptops) |
| `systemd-cron` | Not needed — mentioned only so you don't confuse it with timers |

**See it on a real system**

```bash
for u in $(cut -d: -f1 /etc/passwd); do sudo crontab -u "$u" -l 2>/dev/null | grep -v '^#' | sed "s/^/$u: /"; done
systemctl list-timers --all --no-pager
```

→ The first line lists every user's cron jobs — part of any pre-migration inventory.

**Hands-on lab (test VM only)**

Port one of your cron jobs to a timer, run both side by side for a day, then compare
what `journalctl -u cron` and `journalctl -u NAME.service` tell you about a failed run.
Break both (make the command fail) and note which one you'd have noticed.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Job runs twice | Same job in cron **and** a timer (or in two crontabs) | Inventory command above |
| Daily cron job didn't run on a server that was down at night | Use a timer with `Persistent=true` | This topic |

**Why it matters for troubleshooting**

On an inherited server you must find jobs in both places. On servers you build, timers
make every scheduled job observable.

**Next step**

`at` and one-off timers — including the rollback safety net for risky remote changes.

### at and one-off scheduled jobs

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

`at` runs a command once at a given time. `systemd-run --on-active=` does the same as a
transient timer. The senior use: a **dead man's switch** — before a risky remote change
(firewall, netplan, sshd), schedule the **undo** for 5 minutes later. If the change
locks you out, the undo runs by itself; if all is well, you cancel it.

```
 t=0   schedule rollback in 5 min  ──────────────────────────────┐
 t=1   make the risky change (ufw enable / netplan apply / ...)   │
 t=2   test from a NEW session                                    │
       ├─ works  → cancel the rollback                            │
       └─ locked out → wait ─────────────── t=5 rollback runs ◀──┘ → you're back in
```

**Key terms**

| Command | Purpose |
|---------|---------|
| `echo "CMD" | at now + 5 minutes` | Schedule (package `at`, service `atd`) |
| `atq` / `atrm N` | List / cancel |
| `systemd-run --on-active=5min --unit=NAME CMD` | Transient timer + service |
| `systemctl stop NAME.timer` | Cancel the transient timer |

**See it on a real system**

```bash
atq
systemctl list-timers --all | grep -i rollback
```

**Hands-on lab (test VM only)**

> ⚠️ This lab deliberately enables a firewall that can cut SSH. Do it with the hypervisor
> console open.

**Step 1 — Arm the safety net, then make the risky change.**

```bash
sudo systemd-run --on-active=5min --unit=fw-rollback /usr/sbin/ufw disable
systemctl list-timers fw-rollback.timer
sudo ufw default deny incoming
sudo ufw --force enable                    # forgot to allow SSH → existing session may survive, new ones fail
```

**Step 2 — Break confirmed.** From a new terminal, `ssh labuser@VM_IP` times out. Do
nothing. After 5 minutes `fw-rollback.service` runs `ufw disable` and SSH works again:
`journalctl -u fw-rollback` shows it.

**Step 3 — Do it right.** Arm the rollback again, `sudo ufw allow OpenSSH`,
`sudo ufw --force enable`, test a new SSH session, then cancel:
`sudo systemctl stop fw-rollback.timer`. The same pattern with `at`:
`echo 'mv /etc/netplan/01-static.yaml /root/ && cp /root/50-cloud-init.yaml /etc/netplan/ && netplan apply' | sudo at now + 5 minutes`,
then `sudo atrm JOB` once you've confirmed access.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `at` job never ran | `systemctl status atd`, `atq` | This topic |
| Rollback ran although the change was fine | You forgot to cancel — `systemctl list-timers` / `atq` after every change | This topic |

**Why it matters for troubleshooting**

On-prem servers often have no quick console access. A two-line safety net turns a
potential site visit into a five-minute wait — use it for UFW, netplan, sshd and
`AllowGroups` changes.

**Next step**

Bash scripting — turning your checks into reliable tools.

---

## 12. Bash scripting for operations

> 📚 **Study path:** 1) KodeKloud: *Shell Scripts for Beginners* — Shell Script Introduction → Flow Control → Shebang (Exit Codes, Functions, Tips & Tricks – ShellCheck & IDE) ([course](https://kodekloud.com/courses/shell-scripts-for-beginners)) · 2) Note: this section, with the [Bash Guide](https://mywiki.wooledge.org/BashGuide) beside it · 3) Video: KodeKloud *Shell Scripting Tutorial for Beginners | Shell Scripts Crash Course* ([YouTube](https://www.youtube.com/watch?v=XVOsvIp9m2k), 48 min) · 4) Practice: the Ops Ladder L0 drill — the health-report script below with zero [ShellCheck](https://www.shellcheck.net/) warnings

Read the [Bash Guide](https://mywiki.wooledge.org/BashGuide) alongside this area and
lint every script with [ShellCheck](https://www.shellcheck.net/) — the Ops Ladder L0
sites for exactly this.

### Exit codes, tests and conditionals

**Level:** [L0 · Fresher]

**Concept**

Every command returns an exit status: 0 means success, anything else failure. `if`
doesn't test "true/false values" — it **runs a command** and branches on its exit
status. `[[ ... ]]` is just a command that tests strings, files and patterns;
`(( ... ))` tests arithmetic. `&&` runs the next command only on success, `||` only on
failure. `$?` holds the status of the **last** command and is overwritten by the next
one (even `echo`).

```bash
if systemctl is-active --quiet apache2; then      # the command's exit status IS the condition
  echo "apache2 is running"
fi

if [[ -f /etc/apache2/ports.conf && $(id -u) -eq 0 ]]; then echo "root and file exists"; fi
if (( $(nproc) < 2 )); then echo "single CPU"; fi

case $1 in
  start|stop) echo "ok: $1" ;;
  *)          echo "usage: $0 start|stop" >&2; exit 2 ;;
esac
```

**Key terms**

| Test | True when |
|------|-----------|
| `[[ -f F ]]` / `-d` / `-e` / `-x` / `-s` | Regular file / directory / exists / executable / non-empty |
| `[[ -z $S ]]` / `[[ -n $S ]]` | String empty / non-empty |
| `[[ $S == pattern* ]]` / `[[ $S =~ ^[0-9]+$ ]]` | Glob match / regex match |
| `(( N > 5 ))` | Arithmetic comparison |
| `cmd1 && cmd2 || cmd3` | **Not** if/else: `cmd3` also runs when `cmd2` fails |

**See it on a real system**

```bash
systemctl is-active --quiet apache2; echo "is-active exit=$?"
grep -q '^Listen 443' /etc/apache2/ports.conf; echo "grep exit=$?"     # 0 found, 1 not found, 2 error
curl -fsS -o /dev/null http://127.0.0.1/; echo "curl exit=$?"           # -f: HTTP 4xx/5xx → exit 22
```

**Hands-on lab (test VM only)**

**Step 1 — Build** `check-port.sh` that exits 0 if something listens on a port:

```bash
#!/usr/bin/env bash
port=${1:?usage: check-port.sh PORT}
if ss -Htln "sport = :$port" | grep -q .; then
  echo "port $port: LISTEN"; exit 0
else
  echo "port $port: nothing listening" >&2; exit 1
fi
```

**Step 2 — Break.** Add a debug line between the test and the check:
`ss -Htln "sport = :$port"; echo "checked"; if [ $? -eq 0 ]; ...` — the condition now
tests `echo`, which always succeeds, so the script always says LISTEN.

**Step 3 — Fix**: test the command directly in `if` (ShellCheck's SC2181 tells you
exactly this). Use the script from cron or another script:
`./check-port.sh 443 || echo "443 is free"`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Script reports success although a step failed | `bash -x script.sh` (trace every command) | Strict mode below |
| `[: too many arguments` | Unquoted variable with spaces inside `[ ]` → use `[[ ]]` and quotes | Quoting below |
| `a && b || c` ran both b and c | Use a real `if` | This topic |

**Why it matters for troubleshooting**

Health checks, deploy scripts, CI jobs and systemd all speak exit codes. A script that
returns 0 after a failure hides incidents; one that returns the right code can page you.

**Next step**

Quoting — the source of most dangerous script bugs.

### Quoting, expansion and word splitting

**Level:** [L0 · Fresher]

**Concept**

After expanding `$var` or `$(cmd)`, bash **splits the result on whitespace** and
**expands globs** in it — unless it's inside double quotes. So `rm $file` with
`file="my report.txt"` tries to delete `my` and `report.txt`. Rule: **quote every
expansion** — `"$var"`, `"$(cmd)"`, `"${array[@]}"` — unless you specifically want
splitting. Single quotes are fully literal; double quotes allow `$` expansion.

```
 file="access log *.gz"
 ls $file      → ls  access  log  (every *.gz in the current directory)   ← split + glob
 ls "$file"    → ls  "access log *.gz"                                    ← one argument
```

**Key terms**

| Syntax | Meaning |
|--------|---------|
| `'literal $HOME'` | No expansion at all |
| `"value $HOME"` | Variables and `$(...)` expanded, no splitting/globbing |
| `"${arr[@]}"` | Each array element as one argument — the right way to pass lists |
| `${VAR:?message}` | Abort with message if VAR is unset or empty |
| `${VAR:-default}` | Default value |
| `${path##*/}`, `${file%.log}` | Strip prefix/suffix (basename, extension) |
| `<<'EOF'` vs `<<EOF` | Quoted heredoc = literal; unquoted = expands `$` and backticks |

> ⚠️ The most expensive quoting bug: `rm -rf "$DIR/"*` when `DIR` is empty or unset
> becomes `rm -rf /*` and deletes from `/` (GNU rm's `--preserve-root` default only
> blocks a bare `rm -rf /`, not `/*` or `/$SUBDIR` paths). Safer: use `set -u`, guard
> with `${DIR:?}`, preview first, and delete the narrowest thing that works:
> `find "${DIR:?}" -mindepth 1 -maxdepth 1 -print` (look), then the same with `-delete`
> only after checking the list.

**See it on a real system**

```bash
f="two words.txt"; touch "$f"
ls $f        # ls: cannot access 'two': No such file or directory ...
ls "$f"      # works
printf '[%s]\n' $f      # shows how bash split it: [two] [words.txt]
printf '[%s]\n' "$f"    # [two words.txt]
```

**Hands-on lab (test VM only)**

**Step 1.** In `~/lab/q/` create files `a.log`, `b c.log` and `-n.log`
(`touch -- -n.log`).

**Step 2 — Break.** Run `cd ~/lab/q && for f in $(ls); do wc -l $f; done` — it breaks
on the space and treats `-n.log` as an option.

**Step 3 — Fix.** `for f in ~/lab/q/*.log; do wc -l -- "$f"; done` (globs instead of
parsing `ls`, quotes, and `--` to end option parsing). For `find` output use
`find DIR -type f -print0 | xargs -0 CMD`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Script fails only for some file names | `bash -x`; look for unquoted `$var` | This topic |
| Variables in a heredoc expanded too early/late | Check `<<'EOF'` vs `<<EOF` | This topic |
| A variable is mysteriously empty | Assigned in a subshell or pipeline (`cmd | while read`) | Functions topic below |

**Why it matters for troubleshooting**

Real log and file names contain spaces, dashes and brackets. Quoting discipline is
what makes a script safe to run on a server you don't know.

**Next step**

Strict mode — making scripts stop at the first error instead of carrying on.

### Strict mode: set -euo pipefail

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

By default bash keeps going after a failed command, treats unset variables as empty,
and judges a pipeline only by its last command. Strict mode changes that:

| Option | Effect |
|--------|--------|
| `set -e` (errexit) | Exit when a command fails (with exceptions, below) |
| `set -u` (nounset) | Unset variable = error (catches typos like `$DRI`) |
| `set -o pipefail` | A pipeline fails if **any** part fails, not just the last |
| `set -E` (errtrace) | ERR traps also fire inside functions |

`set -e` has well-known blind spots — learn them so they don't surprise you:

| Pitfall | Why | Fix |
|---------|-----|-----|
| Failure inside `if cmd`, `cmd && x`, `cmd || y` | Conditions are allowed to fail | Intended; just know it |
| `local out=$(cmd)` | `local` succeeds and hides cmd's failure (SC2155) | `local out; out=$(cmd)` |
| `(( count++ ))` when count is 0 | Arithmetic result 0 = exit status 1 → script exits | `count=$((count + 1))` |
| `grep pattern file` finds nothing | Exit 1 = "no match" kills the script | `grep ... || true` when no match is fine |
| `cmd | head -1` with pipefail | Writer gets SIGPIPE (exit 141) | Avoid, or tolerate explicitly |
| Errors inside `<(...)` | Process substitution status is ignored | Check results, or use a temp file |

**Key terms**

| Term | Meaning |
|------|---------|
| `bash -x script` / `set -x` | Trace every command with expanded values |
| `PS4='+ ${BASH_SOURCE}:${LINENO}: '` | Trace lines with file and line number |
| `bash -n script` | Syntax check without running |

**See it on a real system**

```bash
bash -c 'set -e; false; echo "not reached"'; echo "exit=$?"
bash -c 'set -o pipefail; false | true'; echo "exit=$?"
bash -c 'set -u; echo "$UNDEFINED_VAR"'; echo "exit=$?"
```

```
exit=1
exit=1
bash: line 1: UNDEFINED_VAR: unbound variable
exit=N
```

→ bash exits with a non-zero status on an unbound variable (`N` above), so a `set -u` script
fails loudly; read stderr for `unbound variable` rather than guessing the cause from the exit code.

**Hands-on lab (test VM only)**

**Step 1.** Write a 5-line script without strict mode where the first line is
`cd /nonexistent` and the second creates a file. Run it: the file lands in the wrong
directory and the script "succeeds".

**Step 2 — Break each pitfall** from the table in a tiny script with `set -Eeuo
pipefail` and confirm the behaviour (the `(( count++ ))` one surprises everybody).

**Step 3 — Fix** with `cd /nonexistent || exit 1` (ShellCheck SC2164) and the fixes
in the table. Add `PS4` and `bash -x` to see the trace.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Script exits silently halfway | `bash -x`; an "expected" non-zero (grep, `(( ))`, diff) under `set -e` | This topic |
| `unbound variable` | Typo, or optional argument → `${1:-}` | This topic |
| Pipeline error ignored | Add `set -o pipefail` | This topic |

**Why it matters for troubleshooting**

A deploy script that keeps going after `cd` fails, or after a failed `docker pull`,
causes the incidents you'll later debug. Strict mode makes scripts fail early and
loudly, close to the cause.

**Next step**

Functions and traps — structure and cleanup.

### Functions, traps and cleanup

**Level:** [L1 · Junior]

**Concept**

Functions group steps and return an exit status (0–255) — data comes back on stdout.
Declare their variables `local`. A **trap** runs code when the script receives a
signal or exits: `trap cleanup EXIT` removes temp files whether the script succeeds,
fails or is interrupted; `trap '...' ERR` reports where it failed. One more classic:
a pipeline into `while read` runs the loop in a **subshell**, so variables set inside
are lost — read from `< <(cmd)` instead.

```bash
tmpdir=$(mktemp -d)
cleanup() { rm -rf -- "${tmpdir:?}"; }       # guarded: never expands to an empty path
trap cleanup EXIT                             # runs on normal exit, error exit, Ctrl-C (INT) and TERM
trap 'echo "failed at line $LINENO" >&2' ERR

count=0
cmd | while read -r line; do count=$((count + 1)); done        # count is still 0 afterwards!
while read -r line; do count=$((count + 1)); done < <(cmd)     # count is correct
```

**Key terms**

| Term | Meaning |
|------|---------|
| `local` | Variable visible only inside the function |
| `return N` | Function exit status (not a value) |
| `trap CMD EXIT` / `INT` / `TERM` / `ERR` | Run CMD on exit / Ctrl-C / stop / error |
| `mktemp -d` | Safe unique temp directory |
| `flock -n /run/lock/NAME.lock` | Single-instance lock |

**See it on a real system**

```bash
trap -p                               # traps set in your current shell (usually none)
grep -n 'trap' /usr/sbin/update-initramfs /usr/bin/ssh-copy-id 2>/dev/null | head   # real-world examples
```

**Hands-on lab (test VM only)**

**Step 1.** Script that creates `mktemp -d`, writes a file there, then `sleep 30`.
Run it, press Ctrl-C, and look in `/tmp` — the directory is left behind.

**Step 2 — Fix** with the `cleanup` + `trap cleanup EXIT` pattern above, run, Ctrl-C,
confirm the directory is gone.

**Step 3 — Break/fix the subshell trap.** Count lines of `/etc/passwd` with
`cat /etc/passwd | while read ...` and print the counter after the loop (0), then fix
with `< <(...)` or `< /etc/passwd`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `/tmp` full of leftover script directories | Add `trap cleanup EXIT` | Section 8 |
| Two cron runs overlap | `flock -n` | Section 11 |
| Variable "loses" its value after a loop | Pipeline subshell | This topic |

**Why it matters for troubleshooting**

Cleanup traps and locks are what make a script safe to run unattended from a timer —
the difference between a helper and a new source of incidents.

**Next step**

ShellCheck — let a linter catch the rest.

### ShellCheck and a script checklist

**Level:** [L0 · Fresher]

**Concept**

ShellCheck is a static analyser that knows every pitfall above and many more. Run it
on every script before it reaches a server. The Ops Ladder L0 drill asks for a report
script with **zero** ShellCheck warnings.

**Key terms**

| Code | Meaning | Typical fix |
|------|---------|-------------|
| SC2086 | Double quote to prevent globbing and word splitting | `"$var"` |
| SC2046 | Quote `$(...)` to prevent word splitting | `"$(cmd)"` or use an array |
| SC2155 | Declare and assign separately to avoid masking return values | `local x; x=$(cmd)` |
| SC2164 | Use `cd ... || exit` in case `cd` fails | `cd DIR || exit 1` |
| SC2181 | Check exit code directly, not via `$?` | `if cmd; then` |
| SC2002 | Useless cat | `cmd < file` |
| SC2034 | Variable appears unused | Typo or dead code |

Checklist for every operations script:

| Item | Why |
|------|-----|
| `#!/usr/bin/env bash` + `set -Eeuo pipefail` | Predictable interpreter, fail early |
| Header: purpose, usage, exit codes | The next person (you, at 3 a.m.) |
| Quote everything, `--` before file arguments | Safe with any input |
| Absolute paths or explicit `PATH=` | Works from cron/systemd |
| Errors to stderr, results to stdout | Composable, greppable |
| Idempotent (safe to run twice) and a `--dry-run` for destructive steps | Safe re-runs |
| `trap cleanup EXIT`, `flock` if scheduled | No leftovers, no overlaps |
| ShellCheck clean | Catches what review misses |

**See it on a real system**

```bash
sudo apt install -y shellcheck
shellcheck --version
shellcheck -S warning ~/lab/*.sh
```

**Hands-on lab (test VM only)**

**Step 1.** Write this deliberately bad script and run ShellCheck on it:

```bash
#!/bin/bash
dir=$1
cd $dir
for f in $(ls *.log); do
  size=$(du -k $f | cut -f1)
  if [ $size -gt 1000 ]; then echo "$f is big"; fi
done
cat $dir/app.log | grep ERROR
```

**Step 2.** Fix every warning (expect SC2086, SC2164, SC2045 "iterating over ls output",
SC2002 and more) without silencing any.

**Step 3 — Break/verify.** Run the fixed script against a directory containing
`b c.log` and against a missing directory; it must behave correctly in both.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| A "small" script edit broke production | `shellcheck` + `bash -n` in CI before deploy | [CI/CD](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting**

Scripts you run during incidents must not create new ones. Adding ShellCheck to your
GitLab CI pipeline makes this automatic.

**Next step**

Put it all together in a real script.

### Worked example: a server health report

**Level:** [L0 · Fresher] → [L1 · Junior]

**Concept**

The Ops Ladder L0 drill: a bash script that reports disk use, memory and failed systemd
units, with zero ShellCheck warnings. This version also checks inodes, uses thresholds,
returns a meaningful exit code (so a systemd timer marks it **failed** when something is
wrong — which monitoring can alert on), and logs in a greppable format.

```bash
#!/usr/bin/env bash
# health-report.sh — disk, inode, memory and failed-unit report for one server.
# Usage:      health-report.sh [-d DISK_WARN] [-m MEM_WARN] [-h]
# Exit codes: 0 = all OK, 1 = at least one warning, 2 = usage or internal error.
set -Eeuo pipefail

DISK_WARN=85      # % used (blocks or inodes) that triggers a warning
MEM_WARN=90       # % of RAM in use (MemTotal - MemAvailable)
status=0          # becomes 1 on the first warning

usage() {
  printf 'Usage: %s [-d DISK_WARN] [-m MEM_WARN] [-h]\n' "${0##*/}" >&2
}

log()  { printf '%s %-5s %s\n' "$(date '+%F %T')" "$1" "$2"; }
warn() { log WARN "$1"; status=1; }

on_error() {
  local rc=$1 line=$2 cmd=$3
  printf 'ERROR: "%s" failed with exit code %s at line %s\n' "$cmd" "$rc" "$line" >&2
  exit 2
}
trap 'on_error "$?" "$LINENO" "$BASH_COMMAND"' ERR

# check_disk LABEL [extra df flags]   e.g. check_disk disk   /   check_disk inodes -i
check_disk() {
  local label=$1; shift
  local use target
  # -P: one line per filesystem; -x: skip pseudo filesystems; NR > 1 skips the header
  while read -r use target; do
    if [[ $use == "-" ]]; then
      continue                              # e.g. vfat has no inode numbers
    fi
    use=${use%\%}                           # "91%" -> "91"
    if (( use >= DISK_WARN )); then
      warn "$label $target at ${use}% (threshold ${DISK_WARN}%)"
    else
      log OK "$label $target at ${use}%"
    fi
  done < <(df -P "$@" -x tmpfs -x devtmpfs -x squashfs -x overlay | awk 'NR > 1 {print $5, $6}')
}

check_memory() {
  local total avail used_pct
  total=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)       # kB
  avail=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)   # kB, includes reclaimable cache
  used_pct=$(( (total - avail) * 100 / total ))
  if (( used_pct >= MEM_WARN )); then
    warn "memory ${used_pct}% used, $(( avail / 1024 )) MiB available"
  else
    log OK "memory ${used_pct}% used, $(( avail / 1024 )) MiB available"
  fi
}

check_failed_units() {
  local -a failed=()
  mapfile -t failed < <(systemctl list-units --state=failed --no-legend --plain | awk '{print $1}')
  if (( ${#failed[@]} > 0 )); then
    warn "failed units: ${failed[*]}"
  else
    log OK "no failed systemd units"
  fi
}

main() {
  local opt
  while getopts ':d:m:h' opt; do
    case $opt in
      d) DISK_WARN=$OPTARG ;;
      m) MEM_WARN=$OPTARG ;;
      h) usage; exit 0 ;;
      *) usage; exit 2 ;;
    esac
  done
  if [[ ! $DISK_WARN =~ ^[0-9]+$ || ! $MEM_WARN =~ ^[0-9]+$ ]]; then
    usage; exit 2
  fi

  log INFO "health report for $(hostname -f 2>/dev/null || hostname)"
  check_disk disk
  check_disk inodes -i
  check_memory
  check_failed_units
  if (( status == 0 )); then log INFO "result: OK"; else log INFO "result: WARN"; fi
  exit "$status"
}

main "$@"
```

Why each design choice:

| Choice | Reason |
|--------|--------|
| `done < <(df ...)` instead of `df ... | while` | The loop runs in the main shell, so `status=1` set by `warn` survives |
| `df -P` | Guarantees one line per filesystem even with long device names |
| `MemAvailable`, not `MemFree` | Free memory excludes reclaimable cache and looks falsely alarming |
| `mapfile` into an array | Unit names stay separate, no word-splitting surprises |
| `(( ... ))` only inside `if` | Avoids the `set -e` arithmetic pitfall |
| Exit 1 on warnings | A systemd timer run shows as **failed** → visible in `systemctl --failed` and to node_exporter's systemd collector (L4 drill) |

**Key terms**

| Term | Meaning |
|------|---------|
| `getopts` | Built-in option parser (`-d 80 -m 95`) |
| `mapfile -t` | Read lines into an array |
| `${0##*/}` | Script name without its directory |

**See it on a real system**

```bash
sudo install -m 755 health-report.sh /usr/local/bin/health-report.sh
shellcheck /usr/local/bin/health-report.sh
health-report.sh; echo "exit=$?"
health-report.sh -d 30; echo "exit=$?"         # low threshold to force warnings
```

```
2026-10-03 07:00:01 INFO  health report for web01.example.com
2026-10-03 07:00:01 OK    disk / at 41%
2026-10-03 07:00:01 WARN  disk /var/lib/docker at 91% (threshold 85%)
2026-10-03 07:00:01 OK    disk /boot at 11%
2026-10-03 07:00:01 OK    disk /boot/efi at 1%
2026-10-03 07:00:01 OK    inodes / at 7%
2026-10-03 07:00:01 OK    inodes /var/lib/docker at 12%
2026-10-03 07:00:01 OK    inodes /boot at 1%
2026-10-03 07:00:01 OK    memory 62% used, 1480 MiB available
2026-10-03 07:00:01 WARN  failed units: certbot.service lab-writer.service
2026-10-03 07:00:01 INFO  result: WARN
exit=1
```

**Hands-on lab (test VM only)**

**Step 1 — Schedule it with a timer** (section 11):

```ini
# /etc/systemd/system/health-report.service
[Unit]
Description=Daily server health report

[Service]
Type=oneshot
ExecStart=/usr/local/bin/health-report.sh

# /etc/systemd/system/health-report.timer
[Unit]
Description=Run health-report every morning

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now health-report.timer
sudo systemctl start health-report.service      # run once now
journalctl -u health-report -n 20 --no-pager
```

**Step 2 — Break it on purpose** and watch the report change: fill `/var` (section 8
lab), make a unit fail (`demo-web` with a wrong `ExecStart`), create many files on the
inode-limited loop filesystem. Each must produce a WARN and exit 1.

**Step 3 — Extend it** (your exercises): add a check for swap activity, for the
certificate expiry of `https://127.0.0.1` (link to [Web, HTTP & TLS](18-web-http-tls.md)),
and for which processes listen on 80/443. Keep ShellCheck at zero warnings.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Timer runs but nothing in the journal | `systemctl status health-report.service`, `ExecStart` path, `chmod 755` | Section 6 |
| `ERROR: "..." failed with exit code ...` | The ERR trap names the command and line | This topic |
| Works by hand, fails from the timer | Environment/PATH, `User=`, sandboxing | Section 6 |

**Why it matters for troubleshooting**

This is your morning check automated, and the bridge to L4: once it exits non-zero
on problems, monitoring can alert on it instead of you remembering to run it.

**Next step**

The text toolkit that powers scripts like this — and one-line log analysis.

---

## 13. Text processing toolkit

> 📚 **Study path:** 1) KodeKloud: *Advanced Bash Scripting* — Streams, then awk and sed (do these modules first) ([course](https://kodekloud.com/courses/advanced-bash-scripting)); for a gentler start, *Learning Linux Basics Course & Labs* — Working with Shell II (IO redirection, searching) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 2) Note: this section, then the [cheat sheet](19-cheatsheet.md) · 3) Video: skip — practise on real logs instead · 4) Practice: run the log-analysis recipes on a copy of a real Apache access log and write the "which apps are still used" summary

All examples use the Apache **combined** log format, the Ubuntu default for vhosts
with their own `CustomLog`:

```
203.0.113.7 - - [03/Oct/2026:09:14:02 +0000] "GET /login HTTP/1.1" 200 5123 "-" "Mozilla/5.0 (X11; Linux x86_64)"
│           │ │ │                            │    │      │        │   │    │   └ $12.. user agent
│           │ │ │                            │    │      │        │   │    └ $11 referer
│           │ │ │                            │    │      │        │   └ $10 bytes
│           │ │ │                            │    │      │        └ $9 status
│           │ │ │                            │    │      └ $8 protocol
│           │ │ │                            │    └ $7 path
│           │ │ │                            └ $6 "METHOD
│           │ │ └ $4 [date:time   ($5 = timezone)
│           │ └ $3 user
│           └ $2 ident
└ $1 client IP
```

Ubuntu also writes `other_vhosts_access.log` in the **vhost_combined** format for
vhosts without their own log: the first field is `vhost:port`, so every other field
shifts by one (status is `$10`).

### grep and regular expressions

**Level:** [L0 · Fresher]

**Concept**

`grep` prints lines matching a pattern. Combined with a few regex building blocks it
answers most "is this in the logs?" questions. Use `-E` (extended regex) by default,
`-F` for fixed strings (fast, no regex surprises), and `zgrep` for rotated `.gz` logs.

**Key terms**

| Flag | Meaning | Regex | Meaning |
|------|---------|-------|---------|
| `-i` | Ignore case | `.` | Any character |
| `-v` | Invert (non-matching lines) | `*` / `+` / `?` | 0+ / 1+ / 0–1 of previous |
| `-c` | Count matching lines | `^` / `$` | Line start / end |
| `-o` | Print only the match | `[0-9]`, `[^ ]` | Character class / negated |
| `-n` | Line numbers | `{3}`, `{2,5}` | Repetition |
| `-r` / `-l` | Recursive / only file names | `(a|b)` | Alternation (with `-E`) |
| `-A N` / `-B N` / `-C N` | Context after / before / around | `\b` | Word boundary |
| `-w` / `-x` | Whole word / whole line | | |
| `-q` | Quiet, exit status only (scripts) | | |

**See it on a real system**

```bash
grep -c '" 5[0-9][0-9] ' /var/log/apache2/access.log           # how many 5xx responses
grep -E '" (500|502|503|504) ' /var/log/apache2/access.log | tail -5
grep -oE 'AH[0-9]{5}' /var/log/apache2/error.log | sort | uniq -c | sort -rn | head
grep -rn --include='*.conf' -E '^\s*(Listen|<VirtualHost)' /etc/apache2/   # every port Apache uses
zgrep -h 'Failed password' /var/log/auth.log* | wc -l                     # includes rotated .gz
grep -B3 -A10 'Traceback' /var/log/app/app.log | less                     # context around an error
```

```
$ grep -rn --include='*.conf' -E '^\s*(Listen|<VirtualHost)' /etc/apache2/
/etc/apache2/ports.conf:5:Listen 80
/etc/apache2/ports.conf:8:      Listen 443
/etc/apache2/ports.conf:12:     Listen 443
/etc/apache2/sites-available/app1.conf:1:<VirtualHost *:80>
/etc/apache2/sites-available/app1-le-ssl.conf:2:<VirtualHost *:443>
/etc/apache2/sites-available/app2.conf:1:<VirtualHost *:80>
```

→ One grep shows every port and vhost Apache is configured for — half of the
inventory for the [case study](21-case-apache-443-dokploy.md). (`sites-available`
includes disabled sites; check `sites-enabled` or `apachectl -S` for what's live. The
stock `ports.conf` has `Listen 443` twice, inside the `ssl_module` and `mod_gnutls.c`
`IfModule` blocks — only the loaded module's block applies.)

**Hands-on lab (test VM only)**

**Step 1 — Build a sample log.** Generate traffic against your lab Apache:
`for i in $(seq 1 50); do curl -s -o /dev/null http://127.0.0.1/; curl -s -o /dev/null http://127.0.0.1/missing-$((i % 5)); done`.

**Step 2.** Answer with grep only: how many 404s? Which paths returned 404? How many
requests from 127.0.0.1?

**Step 3 — Break/learn.** Search for `.` meaning a literal dot: `grep -c '127.0.0.1'`
also matches `127x0y0z1`; use `grep -cF '127.0.0.1'` or escape `127\.0\.0\.1`.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| Pattern with `|` or `+` doesn't match | Use `grep -E` |
| Matches too much | Anchor (`^`, `$`, `\b`) or use `-F`/`-w` |
| grep finds nothing in a `.gz` | `zgrep`, or `zcat -f FILE* | grep` |
| `Binary file matches` | `grep -a` (treat as text) |

**Why it matters for troubleshooting**

During an incident you need answers from millions of log lines in seconds. grep
narrows them; the next tools count and rank.

**Next step**

cut, sort and uniq — turning matches into counts and rankings.

### cut, sort, uniq and wc

**Level:** [L0 · Fresher]

**Concept**

The "top N" pattern answers most log questions:
`extract a field | sort | uniq -c | sort -rn | head`. `uniq` only collapses
**adjacent** duplicates, so always sort first.

**Key terms**

| Command | Purpose |
|---------|---------|
| `cut -d: -f1,7` | Fields 1 and 7, colon-delimited (single-char delimiters only) |
| `sort -n` / `-h` / `-r` / `-k3,3` / `-t:` | Numeric / human sizes (`2G`) / reverse / by field 3 / delimiter |
| `uniq -c` / `-d` | Count duplicates / show only duplicated lines |
| `wc -l` | Count lines |
| `tr -s ' '` | Squeeze repeated spaces (makes `cut` usable on aligned output) |
| `column -t` | Align columns for reading |
| `paste -sd,` | Join lines with commas |

**See it on a real system**

```bash
cut -d: -f1,7 /etc/passwd | grep -v nologin                          # accounts with a real shell
awk '{print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head   # top client IPs
awk '{print $9}' /var/log/apache2/access.log | sort | uniq -c | sort -rn           # status code mix
sudo du -sh /var/log/* 2>/dev/null | sort -rh | head -5                            # biggest log dirs
```

```
$ awk '{print $9}' /var/log/apache2/access.log | sort | uniq -c | sort -rn
  18342 200
   2210 304
    731 404
     96 502
     12 500
```

→ 96 × 502: Apache's proxy to a backend failed — check the backend (`ProxyPass` target)
and `error.log` around those timestamps.

**Hands-on lab (test VM only)**

**Step 1.** On your sample log, list the top 5 paths and the status mix.

**Step 2 — Break.** Run `awk '{print $9}' access.log | uniq -c` without `sort` — counts
are fragmented because duplicates aren't adjacent.

**Step 3 — Fix** with `sort` before `uniq -c`, then `sort -rn` to rank.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| `uniq -c` shows the same value many times | Sort first |
| `sort` puts 100 before 20 | `sort -n` (or `-h` for 1K/2M/3G) |
| `cut` returns empty fields on `ps`/`df` output | Columns are space-aligned → `awk` or `tr -s ' '` first |

**Why it matters for troubleshooting**

"Which IP is hammering us?", "which status codes spiked?", "which directory grew?" —
all one pipeline. You'll use this pattern daily.

**Next step**

awk — when you need conditions, sums and per-key totals.

### awk for columns, filters and sums

**Level:** [L1 · Junior]

**Concept**

awk reads each line, splits it into fields `$1..$NF` (on whitespace by default), and
runs `pattern { action }` for every line that matches. With variables, associative
arrays and an `END` block it becomes a tiny report generator.

```
 awk -F: '$3 >= 1000 { print $1, $3 }' /etc/passwd
      │   └ pattern ┘ └── action ──┘
      └ field separator (default: runs of spaces/tabs)
 NR = line number   NF = number of fields   $NF = last field   $0 = whole line
```

**Key terms**

| Idiom | Meaning |
|-------|---------|
| `'$9 >= 500'` | Lines where field 9 is ≥ 500 (pattern alone = print the line) |
| `'{ s += $10 } END { print s }'` | Sum a column |
| `'{ c[$1]++ } END { for (k in c) print c[k], k }'` | Count per key |
| `'NR > 1'` | Skip a header line |
| `printf "%-20s %8d\n", $1, $2` | Formatted output |
| `substr($4, 2, 14)` | Part of a field (here `03/Oct/2026:09` = the hour) |

**See it on a real system**

```bash
awk '$9 >= 500 {print $4, $7, $9}' /var/log/apache2/access.log | tail -5            # recent 5xx
awk '{print substr($4, 2, 14)}' /var/log/apache2/access.log | uniq -c | tail -24    # requests per hour
awk '$9 ~ /^5/ {print substr($4, 2, 17)}' /var/log/apache2/access.log | uniq -c     # 5xx per minute
awk '{b[$1] += $11} END {for (v in b) printf "%-35s %8.1f MB\n", v, b[v]/1048576}' \
    /var/log/apache2/other_vhosts_access.log | sort -k2 -rn                          # traffic per vhost
ps -eo user,rss --no-headers | awk '{m[$1] += $2} END {for (u in m) printf "%-12s %6.0f MB\n", u, m[u]/1024}' | sort -k2 -rn
```

```
$ awk '$9 ~ /^5/ {print substr($4, 2, 17)}' /var/log/apache2/access.log | uniq -c
      2 03/Oct/2026:09:13
     41 03/Oct/2026:09:14
     53 03/Oct/2026:09:15
      1 03/Oct/2026:09:16
```

→ A two-minute burst of 5xx at 09:14–09:15: correlate with
`journalctl --since "09:13" --until "09:17"` and the backend's logs. That timestamp is
the anchor for the whole investigation.

**Hands-on lab (test VM only)**

**Step 1.** Compute total bytes served and the average response size from your sample
log.

**Step 2.** Count requests per client IP and print only IPs with more than 20 requests
(`... END {for (ip in c) if (c[ip] > 20) print c[ip], ip}`).

**Step 3 — Break/learn.** Make a request with a malformed request line
(`printf 'garbage\r\n\r\n' | nc 127.0.0.1 80`) and see how it shifts fields in the log
(the request becomes `"garbage"` and `$9` is no longer the status). Robust parsers
check `NF` or match the quoted request with a regex.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| Fields off by one | Different log format (`vhost_combined` adds `vhost:port` first) |
| Numbers summed as 0 | Field contains `-` (no bytes sent) — harmless, or filter `$10 != "-"` |
| awk program in double quotes breaks | Use single quotes so the shell doesn't expand `$1` |

**Why it matters for troubleshooting**

awk turns raw logs into the exact numbers you need for a decision — "which vhosts are
still used?" decides which Apache apps must move to Dokploy and which can be retired.

**Next step**

sed — printing ranges and editing config files reproducibly.

### sed for printing ranges and substitutions

**Level:** [L1 · Junior]

**Concept**

sed is a stream editor: it applies commands to each line. The two you need most:
**print a range** (`sed -n '/start/,/end/p'`) and **substitute** (`s/old/new/g`). With
`-i` it edits files in place — powerful for repeatable config changes, dangerous
without a backup.

**Key terms**

| Command | Meaning |
|---------|---------|
| `sed -n '100,120p' FILE` | Print lines 100–120 |
| `sed -n '/09:14:00/,/09:16:00/p' FILE` | Print from the first match to the next match |
| `sed 's/old/new/g'` | Replace all occurrences on each line |
| `sed -E` | Extended regex (`+`, `()`, `|` without backslashes) |
| `sed -i.bak 's/.../.../' FILE` | Edit in place, keep `FILE.bak` |
| `sed '/^\s*#/d; /^\s*$/d'` | Drop comments and blank lines (effective config) |

**See it on a real system**

```bash
sed -n '/03\/Oct\/2026:09:14/,/03\/Oct\/2026:09:16/p' /var/log/apache2/access.log | head   # access log time format
sed -n '/Oct 03 09:14/,/Oct 03 09:16/p' /var/log/apache2/error.log | head                  # error log: [Sat Oct 03 09:14:02.123456 2026]
sed -e 's/#.*//' -e '/^\s*$/d' /etc/ssh/sshd_config            # config without comments
sed -n '1,20p' /etc/apache2/sites-enabled/app1.conf
```

**Hands-on lab (test VM only)**

The "move Apache off 80/443" option from the case study, done reproducibly:

**Step 1 — Change Apache's HTTP port with a backup.**

```bash
sudo sed -i.bak -E 's/^Listen 80$/Listen 127.0.0.1:8080/' /etc/apache2/ports.conf
sudo sed -i.bak -E 's/^<VirtualHost \*:80>/<VirtualHost 127.0.0.1:8080>/' /etc/apache2/sites-available/000-default.conf
diff -u /etc/apache2/ports.conf.bak /etc/apache2/ports.conf
sudo apache2ctl configtest && sudo systemctl restart apache2
sudo ss -ltnp | grep apache2          # now 127.0.0.1:8080 — port 80 is free for Traefik
```

**Step 2 — Break.** Change only `ports.conf` but not the vhost: `apache2ctl -S` shows
the vhost still bound to `*:80` with nothing listening there, and requests on 8080 hit
the wrong (default) vhost.

**Step 3 — Roll back** from the backups: `sudo cp /etc/apache2/ports.conf.bak
/etc/apache2/ports.conf` (same for the vhost), `configtest`, restart, verify with `ss`.

> ⚠️ `sed -i` without a suffix overwrites the file with no backup, and a wrong regex can
> change every line. Safer: run the same expression **without** `-i` first and read the
> output, then use `-i.bak` and `diff`. Configs under Git (or etckeeper) are safer still.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| `sed: -e expression #1, char N: unknown option to 's'` | The pattern contains `/` — use another delimiter: `s#/old#/new#` |
| Range prints to end of file | The end pattern never matched |
| Edited a symlink target unexpectedly | `sed -i` replaces the symlink with a regular file (use `--follow-symlinks`) |

**Why it matters for troubleshooting**

Extracting the exact minutes around an incident from a 2 GB log, and making the same
config change on five servers identically, are both sed jobs.

**Next step**

find and xargs — operating on many files safely.

### find and xargs

**Level:** [L0 · Fresher]

**Concept**

`find` walks a directory tree and selects files by name, type, size, age, owner or
permissions, then prints them or runs an action. `xargs` turns a list on stdin into
arguments for a command. Use `-print0` / `xargs -0` so odd file names can't break
anything.

**Key terms**

| Expression | Meaning |
|------------|---------|
| `-xdev` | Don't cross into other filesystems |
| `-type f` / `d` / `l` | File / directory / symlink |
| `-name '*.log'` / `-iname` | Name glob (quote it!) |
| `-size +100M` | Bigger than 100 MiB |
| `-mtime +30` / `-mmin -10` | Modified more than 30 days ago / in the last 10 minutes |
| `-user www-data`, `-perm -4000` | Owner / setuid |
| `-printf '%s %p\n'` | Custom output (size, path) |
| `-exec CMD {} +` | Run CMD with many files at once |
| `-delete` | Delete matches — **must come last** |

**See it on a real system**

```bash
# The L0 exit-test question: the five largest files under /var
sudo find /var -xdev -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5 | numfmt --field=1 --to=iec
sudo find /etc -xdev -type f -mmin -60                   # config changed in the last hour
sudo find /var/log -type f -name '*.gz' -mtime +30 | head
find /srv -type f -name '*.php' -newer /etc/apache2/apache2.conf | head
```

```
$ sudo find /var -xdev -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5 | numfmt --field=1 --to=iec
4.0G    /var/lib/docker/overlay2/9c1e.../diff/data/db.dump
1.2G    /var/log/journal/3f2a.../system@0006...journal
512M    /var/lib/mysql/ibdata1
220M    /var/cache/apt/archives/linux-firmware_20240318.git3b128b60-0ubuntu2.3_amd64.deb
128M    /var/log/apache2/access.log.1
```

→ `find /etc -mmin -60` is a superb "what changed?" question after an incident.

> ⚠️ `find ... -delete` and `find ... -exec rm` act on everything that matches — and
> `-delete` placed **before** the tests (`find . -delete -name '*.log'`) deletes
> everything. Safer: run the exact command with `-print` first, read the list, then
> replace `-print` with `-delete` at the end of the expression.

```bash
sudo find /var/log/myapp -type f -name '*.log.gz' -mtime +30 -print     # 1. preview
sudo find /var/log/myapp -type f -name '*.log.gz' -mtime +30 -delete    # 2. same expression, -delete last
```

**Hands-on lab (test VM only)**

**Step 1.** Create `~/lab/f/` with files of different ages:
`touch -d '40 days ago' ~/lab/f/old.log; touch ~/lab/f/new.log; touch ~/lab/f/'with space.log'`.

**Step 2 — Break.** `find ~/lab/f -name '*.log' | xargs ls -l` → the file with a
space fails ("No such file or directory").

**Step 3 — Fix** with `find ~/lab/f -name '*.log' -print0 | xargs -0 ls -l` or
`-exec ls -l {} +`. Then preview-and-delete only files older than 30 days.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| `find: paths must precede expression` | Quote the glob: `-name '*.log'` |
| xargs breaks on spaces/newlines | `-print0` + `xargs -0` |
| Command runs once with no input | `xargs -r` (GNU: don't run if empty) |
| `Argument list too long` with `rm *.log` | `find ... -delete` or `xargs` |

**Why it matters for troubleshooting**

"Five largest files", "what changed in the last hour", "which files does this user
own" — find answers them, and they're exactly the questions in the L0 exit test.

**Next step**

jq — because Docker, Kubernetes and systemd all speak JSON.

### jq for JSON output

**Level:** [L1 · Junior]

**Concept**

Modern tools output JSON: `docker inspect`, `kubectl -o json`, `journalctl -o json`,
`ip -j`, `lsblk -J`. `jq` filters and reshapes JSON the way awk handles columns.

**Key terms**

| Filter | Meaning |
|--------|---------|
| `.` | Pretty-print everything |
| `.key`, `.a.b`, `.[0]` | Navigate |
| `.[]` | Iterate over an array |
| `select(.state == "UP")` | Keep matching items |
| `keys`, `length`, `map(.name)` | Inspect structures |
| `-r` | Raw strings (no quotes) |
| `@tsv` / `@csv` | Table output |
| `.x // "default"` | Fallback when null/missing |

**See it on a real system**

```bash
ip -j addr | jq -r '.[] | select(.operstate == "UP") | .ifname as $i | .addr_info[] | "\($i) \(.local)/\(.prefixlen)"'
lsblk -J -o NAME,SIZE,MOUNTPOINTS | jq '.blockdevices[].name'
docker inspect CONTAINER | jq '.[0].NetworkSettings.Networks | keys'          # which networks? (dokploy-network?)
docker inspect CONTAINER | jq '.[0].Config.Labels | with_entries(select(.key | startswith("traefik")))'
journalctl -p err -b -o json | jq -r '._SYSTEMD_UNIT // .SYSLOG_IDENTIFIER // "kernel"' | sort | uniq -c | sort -rn
```

```
$ journalctl -p err -b -o json | jq -r '._SYSTEMD_UNIT // .SYSLOG_IDENTIFIER // "kernel"' | sort | uniq -c | sort -rn
     42 apache2.service
      7 kernel
      3 docker.service
      1 systemd-resolved.service
```

→ Errors this boot, ranked by unit: start with Apache.

**Hands-on lab (test VM only)**

**Step 1.** With Docker installed on the VM (`sudo apt install docker.io` is enough for
the lab), run `docker run -d --name web -l traefik.enable=true -p 127.0.0.1:18080:80 nginx`
and extract: its IP address, its networks, its labels, its published ports.

**Step 2 — Break.** `docker inspect web | jq '.NetworkSettings'` fails with
`jq: error (at <stdin>:N): Cannot index array with "NetworkSettings"` — `docker inspect`
returns an **array**; you need `.[0].NetworkSettings`.

**Step 3 — Fix** and produce a one-line TSV per container:
`docker inspect $(docker ps -q) | jq -r '.[] | [.Name, .State.Status, (.NetworkSettings.Networks | keys | join(","))] | @tsv'`.
Remove the lab container with `docker rm -f web`.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| `null` everywhere | Wrong path; start with `jq 'keys'` and drill down |
| `Cannot index array with "x"` | Add `.[0]` or `.[]` |
| `jq: command not found` | `sudo apt install jq` |

**Why it matters for troubleshooting**

The Traefik 404/502 cases in the Ops Ladder start with "which labels and networks
does this container have?" — a jq one-liner.

**Next step**

Combine everything into recipes for real log questions.

### Log analysis recipes

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

A handful of pipelines answer the questions you ask in nearly every web incident and
every migration. Keep them in your notes; adapt the field numbers to the log format.

**Key terms**

| Question | Tool chain |
|----------|-----------|
| When did it start? | `awk` per minute + `uniq -c` |
| Who/what is affected? | Top IPs, paths, vhosts |
| What does the server say? | error.log codes, journal by unit |
| Is this app still used? | Requests per vhost over retained logs |

**See it on a real system**

```bash
# Run as root or as a member of the adm group (Apache logs are root:adm 750 on Ubuntu)

# 1. Which vhosts are still used? (all retained logs, rotated .gz included — 14 days by default on Ubuntu)
zcat -f /var/log/apache2/other_vhosts_access.log* | awk '{print $1}' | sort | uniq -c | sort -rn

# 2. Vhosts with their own log: request count and last request per file
for f in /var/log/apache2/*access.log; do
  n=$(zcat -f "$f"* | wc -l)
  last=$(tail -n 1 "$f" | awk '{print $4}' | tr -d '[')
  printf '%-50s %8s requests  last: %s\n' "$f" "$n" "${last:-never}"
done

# 3. Top 10 URLs returning 5xx
awk '$9 ~ /^5/ {print $7}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head

# 4. Top Apache error codes
grep -oE 'AH[0-9]{5}' /var/log/apache2/error.log | sort | uniq -c | sort -rn | head

# 5. SSH brute force: top source IPs ("... from IP port N ssh2" → IP is 4th field from the end)
zgrep -h 'Failed password' /var/log/auth.log* | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head

# 6. Errors per unit in the last hour
journalctl -p err --since "1 hour ago" -o json | jq -r '._SYSTEMD_UNIT // "kernel"' | sort | uniq -c | sort -rn
```

```
$ zcat -f /var/log/apache2/other_vhosts_access.log* | awk '{print $1}' | sort | uniq -c | sort -rn
 182340 app1.example.com:443
  20311 app2.example.com:443
    911 app1.example.com:80
     14 legacy.example.com:443
```

→ `legacy.example.com` got 14 requests in two weeks — probably monitoring or bots.
Confirm with the client and it may not need migrating at all: one fewer app to move to
Dokploy.

**Hands-on lab (test VM only)**

**Step 1.** Create two vhosts on your lab Apache (`app1.lab`, `app2.lab` in
`/etc/hosts`), generate uneven traffic with `curl -H 'Host: app1.lab' http://127.0.0.1/`.

**Step 2.** Run recipes 1 and 3; produce a one-paragraph "which apps are used" summary
as you would for the client.

**Step 3 — Break/learn.** Add a vhost with its own `CustomLog` and notice it disappears
from `other_vhosts_access.log` — recipe 2 covers it. Use `apachectl -S` (section 17) to
know which vhost logs where.

**How it breaks**

| Symptom | Fix |
|---------|-----|
| Counts look too low | Logs rotated — include `FILE*` with `zcat -f` |
| Field numbers wrong | Check the `LogFormat` in `apache2.conf` (`combined` vs `vhost_combined`) |
| Recipe 5 prints odd values | The line layout at the end differs on your sshd version or log format (counting fields from the end breaks) — anchor on the word `from` instead: `grep -oE 'from [0-9.]+' | awk '{print $2}'` |

**Why it matters for troubleshooting**

These recipes turn the questions from the original incident — which apps are running,
which are still needed, where are their logs — into evidence you can show a client.

**Next step**

Logs in depth: the `/var/log` map, journal filters and log rotation.

---

## 14. Logs and log rotation

> 📚 **Study path:** 1) Note: this section, then [Logs & journal reference](06-logs-journal.md) · 2) KodeKloud: LFCS — Operations Deployment: Locate and Analyze System Log Files ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page)) · 3) Read: [Arch Wiki: Journal](https://wiki.archlinux.org/title/Systemd/Journal) for every journalctl filter · 4) Practice: the "three mystery apps" lab below, then the log-finding steps of the [ports playbook](22-playbook-ports-inventory.md)

### Where logs live: the /var/log map

**Level:** [L1 · Junior]

**Concept**

Two systems record logs on Ubuntu: **journald** (binary, structured, every unit's
output) and **rsyslog** (classic text files fed from the journal). Applications that
manage their own log files (Apache, Nginx, MySQL) write directly into `/var/log/APP/`.
Containers log through Docker. Knowing which file holds which kind of event saves the
first ten minutes of every investigation.

| File (Ubuntu) | RHEL / Rocky | What's in it |
|---------------|--------------|--------------|
| `/var/log/syslog` | `/var/log/messages` | General system messages (rsyslog) |
| `/var/log/auth.log` | `/var/log/secure` | sudo, ssh logins, PAM, su |
| `/var/log/kern.log` | (in messages) | Kernel: OOM, disks, NICs, firewall drops |
| `/var/log/dpkg.log`, `/var/log/apt/history.log`, `term.log` | `dnf history`, `/var/log/dnf.log` | Package changes |
| `/var/log/unattended-upgrades/` | `/var/log/dnf.rpm.log` | Automatic upgrades |
| `/var/log/apache2/` | `/var/log/httpd/` | access.log, error.log, other_vhosts_access.log |
| `/var/log/nginx/` | `/var/log/nginx/` | access.log, error.log |
| `/var/log/cloud-init.log`, `cloud-init-output.log` | same | First-boot provisioning |
| `/var/log/ufw.log` | (firewalld → journal) | Firewall blocks |
| `/var/log/journal/` | `/var/log/journal/` or `/run/log/journal/` | The journal itself |
| `/var/lib/docker/containers/ID/ID-json.log` | same | Container stdout/stderr (read with `docker logs`) |
| — | `/var/log/audit/audit.log` | SELinux denials, auditd |

**Key terms**

| Term | Meaning |
|------|---------|
| rsyslog | Daemon writing text logs; rules in `/etc/rsyslog.conf` and `/etc/rsyslog.d/` |
| Facility / priority | Syslog categories (auth, kern, daemon...) and levels (emerg..debug) |
| `adm` group | Can read most logs on Ubuntu without sudo |

**See it on a real system**

```bash
ls -lt /var/log | head -15             # most recently written first
sudo tail -n 5 /var/log/auth.log
grep -v '^#' /etc/rsyslog.d/50-default.conf | grep . | head
logger -t labtest "hello from logger"; journalctl -t labtest -n 1; grep labtest /var/log/syslog
```

**Hands-on lab (test VM only)**

**Step 1.** Generate one event of each kind and find it in both the journal and the
text files: a failed SSH login, a `sudo` command, a `logger` message, an `apt install`.

**Step 2 — Break.** `sudo systemctl stop syslog.socket rsyslog.service` (stopping only
`rsyslog` warns that `syslog.socket` can still activate it, and the next message
restarts it), then `logger -t labtest "after stop"`. The journal has it,
`/var/log/syslog` doesn't.

**Step 3 — Fix.** Start rsyslog again (`sudo systemctl start rsyslog`, which also
starts its socket). Lesson: if text files look "quiet", check the
journal before concluding nothing happened.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `/var/log/syslog` stopped updating | `systemctl status rsyslog`, disk full? | [Logs reference](06-logs-journal.md) |
| Log files huge | `sudo du -sh /var/log/* | sort -rh`, logrotate status | logrotate below |
| No `auth.log` (minimal images, some Debian installs) | rsyslog not installed — use `journalctl` | This topic |

**Why it matters for troubleshooting**

During the Apache investigation, half of the questions were "where are its logs?".
This map answers it for the system; the topic after next answers it for any app.

**Next step**

journalctl filters — how to get the right 20 lines out of millions.

### journalctl filters that matter

**Level:** [L1 · Junior]

**Concept**

The journal stores every entry with fields, so you filter by unit, time, priority,
boot, process or text and combine filters freely. Filtering several units together
gives you an **interleaved timeline** — the most useful view during an incident.

**Key terms**

| Filter | Example |
|--------|---------|
| Unit(s) | `-u apache2 -u docker` |
| This boot / previous boot | `-b` / `-b -1` |
| Time window | `--since "2026-10-03 09:10" --until "09:20"`, `--since "1 hour ago"`, `--since yesterday` |
| Priority (and worse) | `-p warning` (emerg 0, alert 1, crit 2, err 3, warning 4, notice 5, info 6, debug 7) |
| Kernel only | `-k` |
| Follow / last N | `-f` / `-n 100` |
| By identifier / PID / command / user | `-t sshd`, `_PID=1123`, `_COMM=sudo`, `_UID=1001` |
| Text search (regex) | `-g 'timeout|refused'` |
| Output | `-o short-iso`, `-o cat` (message only), `-o json`, `-o verbose` |
| Explanations | `-x` (adds help text to some systemd messages) |
| Reverse / UTC | `-r` / `--utc` |

**See it on a real system**

```bash
journalctl -u apache2 -u 'docker*' --since "09:10" --until "09:20" -o short-iso --no-pager   # 'docker*' also matches the docker-ID.scope units of containers
journalctl -p err -b --no-pager | tail -20
journalctl -k -b | grep -iE 'oom|killed process|i/o error'
journalctl -u ssh --since today -g 'Failed|Invalid' --no-pager | tail
journalctl _SYSTEMD_UNIT=cron.service + _COMM=sudo --since today    # "+" = OR between groups
```

```
$ journalctl -u apache2 -u 'docker*' --since "09:10" --until "09:20" -o short-iso --no-pager
2026-10-03T09:12:40+0000 web01 systemd[1]: Stopping apache2.service - The Apache HTTP Server...
2026-10-03T09:12:41+0000 web01 systemd[1]: apache2.service: Deactivated successfully.
2026-10-03T09:12:41+0000 web01 systemd[1]: Stopped apache2.service - The Apache HTTP Server.
2026-10-03T09:13:05+0000 web01 systemd[1]: Started docker-3c1f9a7e2b4d....scope - libcontainer container 3c1f9a7e2b4d....
```

(With the systemd cgroup driver, systemd logs every container start as a
`docker-ID.scope` unit; dockerd itself logs little at the default `info` level.)

→ Apache stopped at 09:12:41, a container started at 09:13:05: the timeline of the
migration step, ready for the change log or postmortem.

**Hands-on lab (test VM only)**

**Step 1.** Reproduce the section 6 lab (kill `demo-web` with KILL, restart Apache)
and build a single timeline of both units for the last 10 minutes.

**Step 2 — Break.** Run `journalctl --since "09:10"` when your terminal and the server
are in different time zones — entries seem "missing". Check `timedatectl` and use
`--utc` or full timestamps with offsets.

**Step 3.** Export the incident window as JSON for later analysis:
`journalctl --since "10 min ago" -o json > /tmp/incident.json` and count entries per
unit with jq (section 13).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `-- No entries --` | Wrong unit name (`ssh` vs `sshd`), time zone, or journal not persistent | Section 6 |
| `Hint: You are currently not seeing messages from other users and the system.` | Use sudo or join `adm`/`systemd-journal` | Section 3 |
| App logs missing from the journal | App writes to its own file, not stdout | Next topic |

**Why it matters for troubleshooting**

Correlating events across services by time is how you find cause and effect. One
`journalctl -u A -u B --since --until` beats opening five log files side by side.

**Next step**

Finding the logs of an application you've never seen before.

### Finding any application's logs

**Level:** [L1 · Junior]

**Concept**

An application's logs can be in five places. Check them in this order and you will
find them every time — this is the "where are its logs?" part of the L1 exit test.

```
 1. journal        journalctl -u UNIT                       (stdout/stderr of systemd services)
 2. its config     apachectl -S, nginx -T, grep -ri 'log' /etc/APP/
 3. open files     sudo lsof -p PID | grep -iE 'log|\.out'   or  sudo ls -l /proc/PID/fd
 4. container      docker logs CONTAINER  /  docker inspect -f '{{.LogPath}}' CONTAINER
 5. conventions    /var/log/APP/, /opt/APP/logs/, APP_HOME/log/, dpkg -L PACKAGE | grep log
```

**Key terms**

| Term | Meaning |
|------|---------|
| `ErrorLog` / `CustomLog` | Apache directives (per vhost or global) |
| `error_log` / `access_log` | Nginx directives |
| `StandardOutput=` | Unit setting: journal (default), `append:/path`, null |
| `PrivateTmp=` | Files "in /tmp" really live under `/tmp/systemd-private-*-UNIT-*/tmp/` |

**See it on a real system**

```bash
sudo apachectl -S 2>/dev/null | grep -E 'ErrorLog|namevhost|default server'
sudo grep -rhE '^\s*(ErrorLog|CustomLog)' /etc/apache2/sites-enabled/
sudo nginx -T 2>/dev/null | grep -E '^\s*(access_log|error_log)'
sudo lsof -nP -p "$(systemctl show -p MainPID --value apache2)" | grep -E '\.log'
systemctl show -p StandardOutput,StandardError UNIT
```

```
$ sudo grep -rhE '^\s*(ErrorLog|CustomLog)' /etc/apache2/sites-enabled/
	ErrorLog ${APACHE_LOG_DIR}/app1-error.log
	CustomLog ${APACHE_LOG_DIR}/app1-access.log combined
	ErrorLog ${APACHE_LOG_DIR}/error.log
$ sudo lsof -nP -p 1123 | grep -E '\.log'
apache2 1123 root    2w   REG  252,0   88213  1311 /var/log/apache2/error.log
apache2 1123 root    7w   REG  252,0  401977  1320 /var/log/apache2/app1-error.log
apache2 1123 root    8w   REG  252,0 9120334  1322 /var/log/apache2/app1-access.log
apache2 1123 root    9w   REG  252,0 2214809  1318 /var/log/apache2/other_vhosts_access.log
```

→ `${APACHE_LOG_DIR}` comes from `/etc/apache2/envvars` (`/var/log/apache2`). `app2`
has no `CustomLog` line, so its requests land in `other_vhosts_access.log`.

**Hands-on lab (test VM only)**

**Step 1 — Three mystery apps.** Start them, then find each one's logs using only the
method above:

```bash
sudo mkdir -p /opt/mystery/logs
sudo systemd-run --unit=mystery1 /bin/sh -c 'exec >> /opt/mystery/logs/run.out; while true; do date; sleep 5; done'
sudo systemd-run --unit=mystery2 --property=PrivateTmp=yes /bin/sh -c 'exec >> /tmp/m2.log; while true; do date; sleep 5; done'
sudo systemd-run --unit=mystery3 /bin/sh -c 'while true; do echo "tick $(date)"; sleep 5; done'
```

**Step 2 — Break/learn.** For `mystery2`, `ls /tmp/m2.log` finds nothing — the file
is in the unit's private tmp. `sudo ls -l /proc/PID/fd` shows `/tmp/m2.log`, and the
real path is under `/tmp/systemd-private-*-mystery2.service-*/tmp/`.

**Step 3 — Clean up** with `sudo systemctl stop mystery1 mystery2 mystery3`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| App writes "to /tmp" but the file isn't there | `systemctl show -p PrivateTmp UNIT` | Section 6 |
| Log file exists but stays empty | Process holds a rotated/deleted file: `lsof -p PID` | logrotate below |
| Container logs missing | App logs to a file inside the container, not stdout | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

This method answers the exact question that cost the most time in the Apache →
Dokploy incident. With the port inventory (section 17), it's the core of
[the ports playbook](22-playbook-ports-inventory.md).

**Next step**

logrotate — keeping all these logs from filling the disk.

### logrotate

**Level:** [L1 · Junior]

**Concept**

logrotate periodically renames a log (`app.log` → `app.log.1`), compresses older
copies, deletes the oldest, and makes sure the app writes to a fresh file. On Ubuntu
22.04+ it runs daily from `logrotate.timer`. The tricky part is the hand-over: a
process keeps writing to its **open file descriptor**, so after a rename it keeps
writing into `app.log.1`. Two fixes: tell the app to reopen its logs (`postrotate`
reload/HUP) or use `copytruncate` (copy then truncate in place; may lose a few lines).

```
 create + postrotate (preferred)          copytruncate (app can't reopen logs)
 1. mv app.log app.log.1                  1. cp app.log app.log.1
 2. create new empty app.log              2. truncate app.log to 0 bytes
 3. postrotate: reload app → reopens      (app keeps its fd, keeps writing — at offset 0 if it opened with O_APPEND)
```

A config for your own app:

```
# /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily
    rotate 14
    missingok
    notifempty
    compress
    delaycompress
    create 0640 myapp adm
    su myapp adm
    sharedscripts
    postrotate
        systemctl reload myapp.service > /dev/null 2>&1 || true
    endscript
}
```

**Key terms**

| Directive | Meaning |
|-----------|---------|
| `daily`/`weekly`, `size 100M`, `maxsize` | When to rotate |
| `rotate N` | How many old copies to keep |
| `compress` + `delaycompress` | gzip old logs, but leave `.1` uncompressed (the app may still be finishing writes) |
| `create MODE USER GROUP` | Mode/owner of the new file |
| `su USER GROUP` | Rotate as this user (needed when the directory isn't root-only) |
| `postrotate ... endscript` | Command after rotation (reload) |
| `copytruncate` | For apps that can't reopen logs |

**See it on a real system**

```bash
cat /etc/logrotate.d/apache2
systemctl list-timers logrotate.timer
sudo logrotate -d /etc/logrotate.d/apache2 2>&1 | tail -20      # dry run: what WOULD happen
sudo grep apache2 /var/lib/logrotate/status                      # last rotation per file
journalctl -u logrotate --since "2 days ago" --no-pager | tail
```

```
$ cat /etc/logrotate.d/apache2
/var/log/apache2/*.log {
	daily
	missingok
	rotate 14
	compress
	delaycompress
	notifempty
	create 640 root adm
	sharedscripts
	prerotate
		if [ -d /etc/logrotate.d/httpd-prerotate ]; then
			run-parts /etc/logrotate.d/httpd-prerotate
		fi
	endscript
	postrotate
		if pgrep -f ^/usr/sbin/apache2 > /dev/null; then
			invoke-rc.d apache2 reload 2>&1 | logger -t apache2.logrotate
		fi
	endscript
}
```

→ Apache: daily, 14 copies, reload after rotation. That's why recipe 1 in section 13
covers about two weeks.

**Hands-on lab (test VM only)**

**Step 1 — Build an app that never reopens its log.**

```bash
sudo mkdir -p /var/log/lab
sudo systemd-run --unit=lab-logger /bin/sh -c 'exec >> /var/log/lab/app.log; while true; do date; sleep 1; done'
printf '/var/log/lab/app.log {\n  rotate 3\n  missingok\n  create 0644 root root\n}\n' | sudo tee /etc/logrotate.d/lab
```

**Step 2 — Break.** Force a rotation and watch where the lines go:

```bash
sudo logrotate -f /etc/logrotate.d/lab
sleep 3; ls -l /var/log/lab/            # app.log stays 0 bytes, app.log.1 keeps growing
sudo lsof -nP -p "$(systemctl show -p MainPID --value lab-logger)" | grep lab
```

**Step 3 — Fix.** Replace `create 0644 root root` with `copytruncate`, restart the
writer so it opens the current `app.log` again (`sudo systemctl restart lab-logger` —
after step 2 it still writes into the renamed file), force again: now `app.log` keeps
receiving lines. (For a real app prefer a `postrotate` reload.) Clean
up: `sudo systemctl stop lab-logger; sudo rm /etc/logrotate.d/lab`, then remove the lab
files with `sudo rm /var/log/lab/app.log*` and `sudo rmdir /var/log/lab`.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `error: skipping "/var/log/X/x.log" because parent directory has insecure permissions ... Set "su" directive` | Add `su USER GROUP` | This topic |
| New log empty, `.1` still growing | Missing reload/copytruncate; `lsof -p PID` | This topic |
| Logs never rotate | `systemctl status logrotate.timer`, `logrotate -d`, syntax error in another file in `/etc/logrotate.d/` | [Logs reference](06-logs-journal.md) |
| Docker container logs fill the disk | logrotate doesn't manage them — set `log-opts` `max-size`/`max-file` in `daemon.json` | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

Unrotated logs are the most common cause of full disks; a wrong rotation setup causes
"the logs stopped" confusion right when you need them.

**Next step**

The kernel — modules, tunables, messages and limits.

---

## 15. Kernel basics

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Operations Deployment: Change Kernel Runtime Parameters, and Verify Integrity and Availability of Resources and Processes ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: this section, then [Kernel & system reference](13-kernel-system.md) and [Memory reference](04-memory.md) · 3) Next course: the CKA lesson *Introduction to Deployment with kubeadm* uses exactly these modules and sysctls ([lesson notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Deployment-With-kubeadm-Introduction/page)) · 4) Practice: the contained-OOM lab (dmesg topic) and the `nsenter` lab (cgroups topic)

### Kernel version and modules

**Level:** [L1 · Junior]

**Concept**

The kernel is the core of the OS: it schedules processes, manages memory, talks to
hardware and implements networking and filesystems. Much of it is loaded on demand as
**modules** (drivers, filesystems, netfilter features). Kubernetes nodes typically load
two modules every CKA candidate must know: `overlay` (container image layers) and
`br_netfilter` (lets iptables/nftables see bridged pod traffic). Current Kubernetes docs
only require `net.ipv4.ip_forward = 1` and leave `br_netfilter` to the network plugin,
but bridge-based CNIs with kube-proxy in iptables mode still need it — so the CKA labs
still set it up.

**Key terms**

| Command | Purpose |
|---------|---------|
| `uname -r` | Running kernel version |
| `lsmod` | Loaded modules (and who uses them) |
| `modinfo NAME` | Description, parameters, file |
| `modprobe NAME` / `modprobe -r NAME` | Load / unload with dependencies |
| `/etc/modules-load.d/*.conf` | Modules to load at boot |
| `/etc/modprobe.d/*.conf` | Options and `blacklist NAME` |

**See it on a real system**

```bash
uname -r
lsmod | grep -E '^(overlay|br_netfilter|nf_conntrack)'
modinfo br_netfilter | head -5
cat /etc/modules-load.d/*.conf 2>/dev/null
```

```
$ lsmod | grep -E '^(overlay|br_netfilter|nf_conntrack)'
br_netfilter           32768  0
overlay               212992  12
nf_conntrack          196608  6 xt_conntrack,nf_nat,xt_nat,nf_conntrack_netlink,xt_MASQUERADE,xt_addrtype
```

→ `overlay` is used 12 times (one per running container layer mount, roughly); this is a
Docker host. `nf_conntrack` is used by NAT — Docker's port publishing depends on it.

**Hands-on lab (test VM only)**

**Step 1 — Kubernetes prerequisites, the classic way** (as in the CKA labs and older
kubeadm install docs).

```bash
printf 'overlay\nbr_netfilter\n' | sudo tee /etc/modules-load.d/k8s.conf
sudo modprobe overlay
sudo modprobe br_netfilter
lsmod | grep -E 'overlay|br_netfilter'
```

**Step 2 — Break** (on a VM **without** Docker or Kubernetes running, otherwise the
module is in use): `sudo modprobe -r br_netfilter`, then
`sysctl net.bridge.bridge-nf-call-iptables` →
`sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-iptables: No such file or directory`.
kubeadm before v1.30 failed its preflight with the same path in the error; v1.30 and
later dropped that check, so a missing module now shows up later as broken Service or
pod-to-pod traffic instead.

**Step 3 — Fix** with `sudo modprobe br_netfilter`; the `modules-load.d` file makes it
survive reboots.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]` (kubeadm before v1.30), or Services unreachable from pods on a bridge-based CNI | `lsmod | grep br_netfilter`, then sysctl | [Kubernetes](31-learn-kubernetes.md) |
| NIC/storage missing after a kernel update | `dmesg -T`, `lspci -k` (driver in use), boot previous kernel | Section 7, [Kernel reference](13-kernel-system.md) |
| `modprobe: FATAL: Module X not found in directory /lib/modules/...` | Module not built for this kernel / `linux-modules-extra-$(uname -r)` missing | [Kernel reference](13-kernel-system.md) |

**Why it matters for troubleshooting**

Container and Kubernetes networking rests on kernel modules and their sysctls. When a
node "can't route pod traffic", these are among the first things to confirm.

**Next step**

sysctl — the kernel's runtime settings.

### sysctl: kernel tunables

**Level:** [L1 · Junior]

**Concept**

The kernel exposes hundreds of settings as files under `/proc/sys/`. `sysctl` reads
and writes them (`net.ipv4.ip_forward` = `/proc/sys/net/ipv4/ip_forward`). Changes with
`sysctl -w` last until reboot; persistent values go into `/etc/sysctl.d/*.conf`, applied
at boot or with `sysctl --system`. Files are applied in name order and **later files
win**, so `99-` overrides `10-`.

| Setting | Why you'll meet it |
|---------|--------------------|
| `net.ipv4.ip_forward = 1` | Routing between interfaces — required by Docker and Kubernetes |
| `net.bridge.bridge-nf-call-iptables = 1` | Kubernetes: bridged pod traffic passes through iptables/nftables |
| `vm.swappiness` | How eagerly to swap (section 8) |
| `vm.max_map_count` | Elasticsearch/OpenSearch require 262144 (Ubuntu 24.04 already ships a much higher default) |
| `fs.inotify.max_user_watches` / `max_user_instances` | Many containers, file watchers, IDEs: "too many open files" from inotify |
| `net.core.somaxconn` | Max listen backlog (busy proxies) |
| `net.netfilter.nf_conntrack_max` | Connection-tracking table size ("table full, dropping packet") |
| `kernel.dmesg_restrict` | 1 = only root can read `dmesg` (Ubuntu default) |

**Key terms**

| Command | Purpose |
|---------|---------|
| `sysctl NAME` / `sysctl -a` | Read one / all |
| `sudo sysctl -w NAME=VALUE` | Set now (not persistent) |
| `/etc/sysctl.d/60-NAME.conf` | Persistent setting |
| `sudo sysctl --system` | Apply all files now, printing each one it reads |

**See it on a real system**

```bash
sysctl net.ipv4.ip_forward vm.swappiness vm.max_map_count net.core.somaxconn
ls /etc/sysctl.d/ /usr/lib/sysctl.d/
sudo sysctl --system 2>&1 | grep -E '^\* Applying'
```

```
$ sudo sysctl --system 2>&1 | grep -E '^\* Applying'
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/99-kubernetes.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
```

**Hands-on lab (test VM only)**

**Step 1 — Runtime only.** `sudo sysctl -w vm.swappiness=10`, check, reboot, check
again → back to the default. Runtime changes don't survive.

**Step 2 — Persistent, and the ordering trap.**

```bash
echo 'vm.swappiness = 10' | sudo tee /etc/sysctl.d/60-lab.conf
echo 'vm.swappiness = 30' | sudo tee /etc/sysctl.d/99-zz-lab.conf
sudo sysctl --system | grep -E 'Applying|swappiness'
sysctl vm.swappiness              # 30 — the later file won
```

**Step 3 — Fix/clean.** Remove `99-zz-lab.conf`, `sysctl --system`, confirm 10; then
remove `60-lab.conf` too. Write down: "check every file in `sysctl --system` output
when a value isn't what I set".

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| Setting lost after reboot | Only set with `-w`; add a file in `/etc/sysctl.d/` | This topic |
| Value differs from your file | Another file sorts later; `sysctl --system` output | This topic |
| `max virtual memory areas vm.max_map_count [65530] is too low` (OpenSearch/Elasticsearch container) | `sysctl vm.max_map_count` on the **host** | [Docker](30-learn-docker.md) |
| `nf_conntrack: table full, dropping packet` in dmesg | `sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max` | [Network reference](02-network.md) |
| Containers have no outbound network | `sysctl net.ipv4.ip_forward` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting**

A container's kernel settings are the **host's** settings — containers share the
kernel. Many "the app in Docker fails" problems are host sysctls.

**Next step**

dmesg — what the kernel is saying.

### dmesg and kernel messages

**Level:** [L1 · Junior]

**Concept**

The kernel writes to a ring buffer: hardware errors, driver events, OOM kills,
segfaults, firewall log lines, filesystem errors. `dmesg` reads the buffer;
`journalctl -k` reads the same messages from the journal (including previous boots).
When an app dies without a word in its own log, the kernel often explains why.

**Key terms**

| Message pattern | Meaning |
|-----------------|---------|
| `Out of memory: Killed process 2345 (java)` / `Memory cgroup out of memory` | OOM killer (system-wide or a container/unit limit) |
| `I/O error, dev sda, sector ...`, `EXT4-fs error` | Disk or filesystem trouble → read-only remount likely |
| `segfault at ... ip ... error 4 in libfoo.so` | Program crashed (bug, bad library, bad memory) |
| `ens18: Link is Down` | NIC lost carrier |
| `INFO: task X blocked for more than 120 seconds` | Process stuck in D state (storage/NFS) |
| `nf_conntrack: table full, dropping packet` | Too many tracked connections |
| `possible SYN flooding on port 443` | Listen backlog overflowing (attack or overloaded app) |

**See it on a real system**

```bash
sudo dmesg -T | tail -20                   # -T: human timestamps (approximate after suspend)
sudo dmesg -T -l err,crit,alert,emerg
journalctl -k -b -1 --no-pager | tail       # kernel messages from the previous boot
sudo dmesg -wT                              # follow
```

```
$ journalctl -k -b | grep -iE 'out of memory|killed process'
Oct 03 03:12:44 web01 kernel: Memory cgroup out of memory: Killed process 2671 (php-fpm8.3) total-vm:812344kB, anon-rss:498112kB, file-rss:9216kB, shmem-rss:0kB, UID:33 pgtables:1240kB oom_score_adj:0
```

→ A **cgroup** OOM: a unit's or container's `MemoryMax`/`--memory` limit was hit, not the
whole machine. Find which with the PID's cgroup in the same journal window.

**Hands-on lab (test VM only)**

**Step 1 — Trigger a contained OOM** (the limit protects the rest of the VM):

```bash
sudo systemd-run --scope -p MemoryMax=50M -p MemorySwapMax=0 \
  python3 -c 'x = bytearray(200 * 1024 * 1024); print("not reached")'
echo "exit=$?"            # 137 = killed by SIGKILL
```

**Step 2.** Find the evidence: `journalctl -k -n 20 | grep -i -A2 'out of memory'`.
Note the process name, UID and memory numbers.

**Step 3.** Repeat with `MemoryMax=500M`: it succeeds. That's exactly what happens with
`docker run --memory` and Kubernetes `limits.memory` (exit 137, `OOMKilled: true`).

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Process vanished, no app log | `journalctl -k | grep -i 'killed process'` | [Memory](04-memory.md) |
| Filesystem went read-only | `dmesg -T | grep -iE 'ext4|xfs|i/o error'` | [Storage reference](01-storage-disk.md) |
| `dmesg: read kernel buffer failed: Operation not permitted` | Use sudo (or `journalctl -k`) | This topic |
| Network flaps | `dmesg -T | grep -i 'link is'` | [Network speed playbook](24-playbook-network-speed.md) |

**Why it matters for troubleshooting**

"It crashed and the logs say nothing" is answered by the kernel log surprisingly often:
OOM, segfault, disk errors. Check it early — it's one command.

**Next step**

Limits — why a process can hit "Too many open files" with plenty of RAM.

### Resource limits: ulimit and LimitNOFILE

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Each process has limits (rlimits): open files, processes, core size, locked memory.
There's a **soft** limit (current) and a **hard** limit (ceiling the soft limit may be
raised to). The trap: `/etc/security/limits.conf` applies only to **PAM login sessions**
(SSH, su). **systemd services ignore it** — they get limits from the unit
(`LimitNOFILE=`) or systemd's defaults. Containers inherit from the Docker daemon unless
set with `--ulimit`.

```
 SSH login ──PAM──▶ /etc/security/limits.conf ──▶ your shell (ulimit -n)
 systemd service ─────────▶ LimitNOFILE= in the unit / drop-in ──▶ /proc/PID/limits
 docker run ──▶ --ulimit nofile=... (or daemon default) ──▶ container processes
```

**Key terms**

| Term | Meaning |
|------|---------|
| `ulimit -n` / `-Hn` | Soft / hard open-file limit of this shell |
| `ulimit -a` | All limits |
| `LimitNOFILE=65536` | Unit setting (soft:hard can be given as `LimitNOFILE=65536:524288`) |
| `/proc/PID/limits` | The truth for a running process |
| EMFILE (errno 24) | "Too many open files" |

**See it on a real system**

```bash
ulimit -n; ulimit -Hn
systemctl show -p LimitNOFILE,LimitNOFILESoft nginx 2>/dev/null
sudo grep -E 'open files|processes' /proc/"$(pgrep -o nginx || pgrep -o apache2)"/limits
sudo ls /proc/"$(pgrep -o apache2)"/fd | wc -l      # how many it has open right now
```

**Hands-on lab (test VM only)**

**Step 1 — Break in a shell.**

```bash
( ulimit -n 64; python3 -c '
fs = [open("/etc/hostname") for _ in range(100)]
print("opened", len(fs))' )
```

→ `OSError: [Errno 24] Too many open files: '/etc/hostname'`

**Step 2 — Break in a service.** Add `LimitNOFILE=64` to `demo-web` with
`systemctl edit`, restart, and check `/proc/PID/limits`. Also put
`* soft nofile 100000` in `/etc/security/limits.d/lab.conf` and notice it changes
**nothing** for the service.

**Step 3 — Fix** with `LimitNOFILE=65536` in the drop-in, restart, verify in
`/proc/PID/limits`. Remove the `limits.d` lab file.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| Nginx `accept4() failed (24: Too many open files)` | `/proc/PID/limits`, `ls /proc/PID/fd | wc -l` | [Processes reference](05-processes.md) |
| Raised limits.conf, service unchanged | Use `LimitNOFILE=` in a drop-in | This topic |
| `fork: retry: Resource temporarily unavailable` | `ulimit -u`, `TasksMax=` of the unit/slice, PID count | [Kernel reference](13-kernel-system.md) |

**Why it matters for troubleshooting**

Proxies like Traefik and Nginx hold two descriptors per proxied connection. Under
load, the open-files limit is a real capacity limit, and the limits.conf trap wastes
hours.

**Next step**

cgroups and namespaces — the kernel features containers are made of.

### cgroups and namespaces: the container building blocks

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Two kernel features make containers possible. **cgroups** (control groups) group
processes and limit/measure their resources: CPU, memory, I/O, number of tasks.
**Namespaces** give a group of processes its own view of the system: its own PIDs,
network stack, mounts, hostname, users. systemd puts **every service** in its own
cgroup (that's how `systemctl status` lists all its processes and how `KillMode`
works). A Docker container or a Kubernetes pod is just processes in their own cgroup
plus their own namespaces. Ubuntu 22.04+ uses **cgroup v2** (one unified tree).

```
 /sys/fs/cgroup/                        (cgroup v2 tree)
 ├── system.slice/
 │   ├── apache2.service/      memory.current, memory.max, cpu.max, pids.current ...
 │   ├── docker.service/
 │   └── docker-3c1f....scope/ ← a container: memory.max = docker run --memory
 ├── user.slice/               ← SSH sessions
 └── kubepods.slice/           ← Kubernetes pods (on a node)

 namespaces per container: pid, net, mnt, uts, ipc, (user), cgroup
 nsenter -t PID -n ss -ltn   → run the HOST's ss inside a container's network namespace
```

**Key terms**

| Term | Meaning |
|------|---------|
| Slice / scope / service | systemd cgroup units (groups / external processes / services) |
| `MemoryMax=`, `CPUQuota=`, `TasksMax=`, `CPUWeight=` | systemd resource controls |
| `systemd-cgls` / `systemd-cgtop` | Tree / live top per cgroup |
| `lsns` | List namespaces |
| `nsenter` | Run a command inside another process's namespaces |

**See it on a real system**

```bash
stat -fc %T /sys/fs/cgroup              # cgroup2fs = cgroup v2
systemd-cgls --no-pager | head -30
systemd-cgtop -n 1 --order=memory | head -12
cat /sys/fs/cgroup/system.slice/apache2.service/memory.current
sudo lsns -t net                        # one net namespace per container
```

```
$ systemd-cgtop -n 1 --order=memory | head -6
CGroup                                          Tasks   %CPU   Memory  Input/s Output/s
/                                                 412      -     2.9G        -        -
system.slice                                      210      -     2.1G        -        -
system.slice/docker-3c1f9a7e2b4d.scope             38      -   912.0M        -        -
system.slice/apache2.service                       55      -   210.4M        -        -
system.slice/docker.service                        24      -   140.2M        -        -
```

→ One view shows the memory of every service **and** every container — the fastest way
to see "who is using the RAM" on a mixed Apache + Docker host. %CPU needs two samples,
so a single iteration (`-n 1`) prints `-`; use `-n 2` or more (or run it interactively)
when CPU matters.

**Hands-on lab (test VM only)**

**Step 1 — Limit CPU.**

```bash
sudo systemd-run --unit=lab-burn -p CPUQuota=20% -p StandardOutput=null /usr/bin/yes   # a shell "> /dev/null" here would only redirect systemd-run itself; yes would flood the journal
systemd-cgtop -n 3 | grep lab-burn       # ~20% of one CPU
```

**Step 2 — Break/observe.** Raise it live: `sudo systemctl set-property --runtime
lab-burn CPUQuota=80%`; watch the change. Then stop it: `sudo systemctl stop lab-burn`.

**Step 3 — Look into a namespace** (needs Docker on the VM): start
`docker run -d --name ns-lab nginx`, find its PID with
`docker inspect -f '{{.State.Pid}}' ns-lab`, then
`sudo nsenter -t PID -n ss -ltn` — the host's `ss` binary inside the container's
network namespace, even though the image has no `ss`. Remove it with
`docker rm -f ns-lab`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Container killed at a memory limit (137, OOMKilled) | `docker inspect -f '{{.State.OOMKilled}}' CONTAINER`, `journalctl -k` | [Docker](30-learn-docker.md) |
| Service slow but host idle | `systemctl show -p CPUQuotaPerSecUSec UNIT`, `cpu.stat` throttling | [CPU reference](03-cpu-performance.md) |
| Kubernetes node: pods evicted / `MemoryPressure` | `systemd-cgtop`, kubelet logs | [Kubernetes](31-learn-kubernetes.md) |

**Why it matters for troubleshooting**

Once you see containers as "processes with cgroups and namespaces", Docker and
Kubernetes stop being magic: memory limits are cgroup files, container networking is a
namespace you can enter with `nsenter` or netshoot.

**Next step**

Security basics — firewall, brute-force protection, updates and MAC.

---

## 16. Security basics

> 📚 **Study path:** 1) KodeKloud: LFCS — Networking: Configure Packet Filtering (Firewall) ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)), with the Linux Basics lesson *IPTABLES Introduction* for the model underneath ([lesson notes](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page)) · 2) Note: this section, then [Users, permissions & security](10-users-permissions-security.md) · 3) Later, after CKA: CKS — System Hardening, including *UFW Firewall Basics* ([lesson notes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)) and AppArmor · 4) Practice: the "Docker bypasses UFW" lab below, then the packet-filtering challenge in *Linux Challenges* (free, [course](https://kodekloud.com/courses/linux-challenges))

### UFW and the nftables underneath

**Level:** [L1 · Junior]

**Concept**

The Linux firewall lives in the kernel (**netfilter**). You configure it through
**nftables** (`nft`) or the older **iptables** commands (on Ubuntu 22.04+ these are
`iptables-nft`, a compatibility layer writing nftables rules). **UFW** is Ubuntu's
friendly front end; on RHEL it's **firewalld**. Docker writes its own rules for
published ports — and those packets are NAT-ed and forwarded **before** UFW's input
rules see them, so `ufw deny 8080` does **not** protect a Docker-published port 8080.

```
 packet for 192.0.2.10:443 arrives
        │
        ▼
 PREROUTING (nat) ── Docker's DNAT for published ports ──▶ FORWARD ──▶ container
        │                                                   ↑ DOCKER-USER chain: YOUR container filters go here
        ▼
 INPUT (filter) ── UFW rules live here ──▶ host processes (sshd, apache2, Traefik with host ports)
```

| Port | Service | Who should reach it |
|------|---------|---------------------|
| 22/tcp | SSH | Admin networks only (or everyone + fail2ban + keys only) |
| 80, 443/tcp | Traefik (Dokploy) or Apache | Everyone |
| 3000/tcp | Dokploy UI | Admin IPs only — or nobody, and use an SSH tunnel |
| 2377/tcp, 7946/tcp+udp, 4789/udp | Docker Swarm | Other Swarm nodes only |

**Key terms**

| Command | Purpose |
|---------|---------|
| `ufw status verbose` / `numbered` | Rules with defaults / with numbers for deletion |
| `ufw allow OpenSSH` / `ufw allow 443/tcp` | Allow by app profile / port |
| `ufw allow from 192.0.2.0/24 to any port 3000 proto tcp` | Allow from a subnet only |
| `ufw delete N` | Remove rule N |
| `ufw app list` | Profiles (`Apache Full`, `OpenSSH`, `Nginx Full`) |
| `nft list ruleset` | Everything actually loaded in the kernel |
| `firewall-cmd --list-all` | RHEL/Rocky equivalent view |

**See it on a real system**

```bash
sudo ufw status verbose
sudo nft list ruleset | less
sudo iptables -t nat -S DOCKER 2>/dev/null | head      # Docker's DNAT rules for published ports
journalctl -k -g 'UFW BLOCK' -n 5 --no-pager
```

```
$ sudo ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere
80,443/tcp (Apache Full)   ALLOW IN    Anywhere
3000/tcp                   ALLOW IN    192.0.2.0/24
22/tcp (OpenSSH (v6))      ALLOW IN    Anywhere (v6)
80,443/tcp (Apache Full (v6)) ALLOW IN    Anywhere (v6)
$ journalctl -k -g 'UFW BLOCK' -n 1 --no-pager
Oct 03 10:41:07 web01 kernel: [UFW BLOCK] IN=ens18 OUT= MAC=... SRC=198.51.100.23 DST=192.0.2.10 LEN=60 TOS=0x00 PREC=0x00 TTL=52 ID=4113 DF PROTO=TCP SPT=51544 DPT=3000 WINDOW=64240 RES=0x00 SYN URGP=0
```

→ A SYN to port 3000 from outside the admin subnet was blocked — as intended.

> ⚠️ `iptables -F` (flush) / `nft flush ruleset` remove **all** rules at once: with a
> default-drop policy you lose SSH instantly, and you also wipe Docker's NAT rules so
> every container loses networking. Safer: save first (`sudo iptables-save >
> /root/fw-backup.rules`, `sudo nft list ruleset > /root/nft-backup.nft`), change one rule
> at a time (`ufw delete N`), arm a rollback timer (section 11), and prefer
> `ufw disable` over flushing if you must turn filtering off.

**Hands-on lab (test VM only)**

**Step 1 — Enable UFW safely** (rollback timer armed, console open):

```bash
sudo systemd-run --on-active=5min --unit=fw-rollback /usr/sbin/ufw disable
sudo ufw default deny incoming && sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80,443/tcp
sudo ufw allow from 192.0.2.0/24 to any port 3000 proto tcp   # your admin subnet
sudo ufw --force enable
# test a NEW SSH session, then:
sudo systemctl stop fw-rollback.timer
```

**Step 2 — Break: the Docker bypass.** With Docker installed:
`docker run -d --name bypass -p 8081:80 nginx`, then `sudo ufw deny 8081/tcp`. From
another machine `curl -I http://VM_IP:8081/` still answers 200.

**Step 3 — Fix.** Publish on loopback only (`-p 127.0.0.1:8081:80`) and let Traefik or
an SSH tunnel reach it — or, for real filtering of container ports, add rules to the
`DOCKER-USER` chain (see [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)).
Remove the lab container with `docker rm -f bypass`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Locked out after `ufw enable` | Console; `ufw disable`; next time allow OpenSSH first + rollback timer | Section 11 |
| Port open although UFW denies it | Docker-published port → `docker ps`, bind to 127.0.0.1 or DOCKER-USER | [Containers playbook](26-playbook-containers-k8s.md) |
| Works locally, times out remotely | `sudo ufw status`, `journalctl -k -g 'UFW BLOCK'` | [Network reference](02-network.md) |
| Swarm nodes can't join / overlay network dead | 2377, 7946, 4789 between nodes | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting**

After the migration, Traefik owns 80/443 and Dokploy's UI listens on 3000. Knowing
that UFW doesn't filter Docker-published ports is the difference between "3000 is
restricted" and "3000 is open to the internet".

**Next step**

fail2ban — automatic bans for brute-force attempts.

### fail2ban

**Level:** [L1 · Junior]

**Concept**

fail2ban watches logs for repeated failures from the same IP (SSH logins, HTTP auth),
and after `maxretry` failures within `findtime` it adds a firewall ban for `bantime`.
Configuration lives in `/etc/fail2ban/jail.local` (never edit `jail.conf`, it's
overwritten on upgrade). On systems without `/var/log/auth.log`, use
`backend = systemd` to read the journal.

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
# your admin network — avoid banning yourself (keep comments on their own line:
# fail2ban does not strip an inline "#" and would read it as part of ignoreip)
ignoreip = 127.0.0.1/8 ::1 192.0.2.0/24

[sshd]
enabled = true
backend = systemd
```

**Key terms**

| Term | Meaning |
|------|---------|
| Jail | Filter (regex for failures) + action (ban) for one service |
| `fail2ban-client status` | List jails |
| `fail2ban-client status sshd` | Failures and banned IPs |
| `fail2ban-client set sshd unbanip IP` | Unban |

**See it on a real system**

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo tail -n 20 /var/log/fail2ban.log
```

```
$ sudo fail2ban-client status sshd
Status for the jail: sshd
|- Filter
|  |- Currently failed: 2
|  |- Total failed:     57
|  `- Journal matches:  _SYSTEMD_UNIT=sshd.service + _COMM=sshd
`- Actions
   |- Currently banned: 3
   |- Total banned:     11
   `- Banned IP list:   203.0.113.50 198.51.100.77 203.0.113.9
```

**Hands-on lab (test VM only)**

**Step 1.** `sudo apt install -y fail2ban`, create the `jail.local` above with
`maxretry = 3` and **without** your client's network in `ignoreip`, then
`sudo systemctl restart fail2ban`.

**Step 2 — Break: ban yourself.** From a second VM (or your laptop), fail three password
logins (`ssh -o PubkeyAuthentication=no wronguser@VM_IP`). The next connection times out.
`sudo fail2ban-client status sshd` (from the console) shows your IP.

**Step 3 — Fix.** `sudo fail2ban-client set sshd unbanip YOUR_IP`, add your admin network
to `ignoreip`, restart fail2ban.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Admin suddenly can't SSH, others can | `fail2ban-client status sshd` — banned? | This topic |
| fail2ban won't start, "Have not found any log file for sshd jail" | Set `backend = systemd` | This topic |
| Jail shows 0 failures despite attacks | Wrong backend/log path; test the filter with `fail2ban-regex` | [Security reference](10-users-permissions-security.md) |

**Why it matters for troubleshooting**

"Some users can't connect, others can" with a pattern by source IP is often a ban.
Checking fail2ban takes seconds and is easy to forget.

**Next step**

Keeping the system patched — automatically, but under control.

### Unattended upgrades and reboots

**Level:** [L1 · Junior]

**Concept**

Ubuntu installs security updates automatically: `apt-daily.timer` refreshes package
lists and `apt-daily-upgrade.timer` (around 06:00 with a random delay) runs
`unattended-upgrade`. By default only the **security** pocket is installed and the
machine is **not** rebooted. When an upgrade touches Docker or containerd, the daemon
restarts — and so do your containers unless restart policies and live-restore handle
it. Ubuntu's own `docker.io`, `containerd` and `runc` packages do get security
updates this way; `docker-ce`/`containerd.io` from Docker's repository are only touched
if someone added that repository to the allowed origins. That's why production
container hosts often hold or blacklist those packages and upgrade them in a planned
window.

**Key terms**

| Item | Meaning |
|------|---------|
| `/etc/apt/apt.conf.d/20auto-upgrades` | Turns the periodic jobs on/off |
| `/etc/apt/apt.conf.d/50unattended-upgrades` | Origins, blacklist, reboot behaviour |
| `Unattended-Upgrade::Package-Blacklist` | Packages never upgraded automatically (regexes) |
| `Unattended-Upgrade::Automatic-Reboot` | `false` by default |
| `/var/run/reboot-required` | Exists when a reboot is needed (`.pkgs` lists why) |
| needrestart | After upgrades, restarts services using outdated libraries (prompts on 22.04; 24.04 restarts automatically by default) |

```
# /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";

# excerpt from /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Package-Blacklist {
    "docker";        // regexes matched from the start of the name: docker.io, docker-ce, docker-ce-cli ...
    "containerd";    // containerd and containerd.io
    "runc";
    "kube.*";
};
```

**See it on a real system**

```bash
systemctl list-timers 'apt-daily*'
cat /etc/apt/apt.conf.d/20auto-upgrades
sudo tail -n 30 /var/log/unattended-upgrades/unattended-upgrades.log
ls /var/run/reboot-required* 2>/dev/null && cat /var/run/reboot-required.pkgs
sudo unattended-upgrade --dry-run --debug 2>&1 | tail -20
```

```
$ sudo tail -n 4 /var/log/unattended-upgrades/unattended-upgrades.log
2026-10-03 06:14:02,118 INFO Starting unattended upgrades script
2026-10-03 06:14:02,119 INFO Allowed origins are: o=Ubuntu,a=noble, o=Ubuntu,a=noble-security, o=UbuntuESMApps,a=noble-apps-security, o=UbuntuESM,a=noble-infra-security
2026-10-03 06:14:31,904 INFO Packages that will be upgraded: libssl3t64 openssl
2026-10-03 06:14:58,210 INFO All upgrades installed
```

→ When something changed "by itself" in the morning, this log and `apt/history.log`
are the first places to look.

**Hands-on lab (test VM only)**

**Step 1.** Run the dry run and list what would be upgraded.

**Step 2 — Break/learn.** Start `sudo unattended-upgrade -d` in one terminal and
`sudo apt install -y tree` in another: the second waits for or fails on the dpkg lock
(`Could not get lock /var/lib/dpkg/lock-frontend ... held by process N
(unattended-upgr)`). Wait — never delete the lock.

**Step 3.** Add a blacklist entry for a lab package, re-run the dry run, and confirm it's
skipped. Check `/var/run/reboot-required` and plan (don't do) a reboot.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Containers restarted at ~06:00 | `grep -E 'docker|containerd' /var/log/apt/history.log` | [Containers playbook](26-playbook-containers-k8s.md) |
| CI/Ansible apt step fails on the lock | `ps -fp PID` from the message; wait or schedule around the timer | [Packages reference](11-packages.md) |
| Security fix "installed" but still vulnerable | Service not restarted: `needrestart -r l`, `/proc/*/exe (deleted)` | Section 4 |

**Why it matters for troubleshooting**

Automatic updates are good security and a classic surprise. Knowing where they log and
how to control them turns "it broke overnight" into a two-minute answer.

**Next step**

The mandatory access control layer — SELinux and AppArmor.

### SELinux and AppArmor overview

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Classic permissions (DAC) ask "does this user own this file?". **MAC** (mandatory
access control) adds "is this *program* allowed to do this at all?", even as root.
**SELinux** (RHEL, Rocky, Fedora) labels every file, process and port with a context
and checks policy rules between them. **AppArmor** (Ubuntu, Debian, SUSE) attaches
path-based profiles to specific programs. Both cause the "Permission denied although
permissions are fine" problem, and both log the denial — you just need to know where.

| | SELinux (RHEL/Rocky) | AppArmor (Ubuntu) |
|--|----------------------|-------------------|
| Model | Labels (contexts) on files, processes, ports | Profiles of allowed paths per program |
| Status | `getenforce`, `sestatus` | `sudo aa-status` |
| Modes | enforcing / permissive / disabled | enforce / complain per profile |
| Denials logged in | `/var/log/audit/audit.log` (`ausearch -m AVC -ts recent`) | Kernel log: `journalctl -k -g 'apparmor="DENIED"'` |
| Typical fix | `restorecon -Rv PATH`, `semanage fcontext`, `setsebool -P`, `semanage port` | Adjust the profile, or `aa-complain` while diagnosing |
| Containers | `:z`/`:Z` on bind mounts | `docker-default` profile |

**Key terms**

| Term | Meaning |
|------|---------|
| Context / label | `system_u:object_r:httpd_sys_content_t:s0` — the type (`_t`) matters most |
| Boolean | Switch for common policy options (`httpd_can_network_connect`) |
| AVC | SELinux "access vector cache" denial record |
| Complain mode | AppArmor logs but doesn't block |

**See it on a real system**

```bash
# Ubuntu
sudo aa-status | head -20
journalctl -k -g 'apparmor="DENIED"' --since today --no-pager | tail -5
# RHEL / Rocky
getenforce
ls -Z /var/www/html/ /srv/site/
sudo ausearch -m AVC -ts recent | tail -5
```

```
type=AVC msg=audit(1727946842.123:512): avc:  denied  { name_connect } for  pid=2210 comm="httpd" dest=8000 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:soundd_port_t:s0 tclass=tcp_socket permissive=0
```

→ Apache (`httpd_t`) was denied a TCP connection to port 8000: a reverse proxy to a
local app on RHEL returns 503 until `sudo setsebool -P httpd_can_network_connect 1`.

**Hands-on lab (test VM only)**

**Step 1 (Rocky VM).** Install httpd, create `/srv/site/index.html`, point a vhost's
`DocumentRoot` at it and allow the directory in the config.

**Step 2 — Break.** Request the page → 403. File permissions are fine (`namei -l`), but
`ls -Z /srv/site` shows `var_t`/`default_t`, and `ausearch -m AVC -ts recent` shows
`httpd` denied `read`.

**Step 3 — Fix properly** (not by disabling SELinux):

```bash
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/site(/.*)?'
sudo restorecon -Rv /srv/site
```

On Ubuntu, run `sudo aa-status`, find which profiles are in enforce mode, and look for
DENIED lines after installing something like `mysql-server` with a non-default datadir.

> ⚠️ `setenforce 0` / `SELINUX=disabled` "fixes" everything by turning the protection
> off. Temporary permissive mode is fine **for diagnosis** (does the error disappear?);
> then fix the label/boolean and return to enforcing.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| 403 / Permission denied with correct permissions (RHEL) | `ausearch -m AVC -ts recent`, `ls -Z` | [Security reference](10-users-permissions-security.md) |
| Reverse proxy 503 on RHEL | `getsebool httpd_can_network_connect` | [Web servers](29-learn-webservers-proxies.md) |
| Container can't read its bind mount on RHEL | Add `:z` to the volume | [Docker](30-learn-docker.md) |
| Ubuntu service denied a path after moving its data dir | `journalctl -k -g apparmor` | This topic |

**Why it matters for troubleshooting**

MAC denials are invisible unless you look in the right log. Add "check AVC/AppArmor
denials" to your permission-denied checklist and these incidents become short.

**Next step**

Put the security basics together as a baseline checklist.

### A baseline hardening checklist

**Level:** [L1 · Junior]

**Concept**

Hardening is a list of small, verifiable settings. Apply it to every new server and
re-check it after migrations; each line has a command that proves it.

| Area | Baseline | Verify with |
|------|----------|-------------|
| SSH | Keys only, no root login, AllowGroups | `sudo sshd -T | grep -E 'passwordauth|permitroot|allowgroups'` |
| Firewall | Default deny incoming, only needed ports | `sudo ufw status verbose`, `sudo ss -ltnp` |
| Container ports | Admin/internal ports bound to 127.0.0.1 | `docker ps --format '{{.Names}} {{.Ports}}'` |
| Brute force | fail2ban on SSH | `sudo fail2ban-client status sshd` |
| Updates | Security updates automatic, risky packages held | `apt-mark showhold`, u-u log |
| Accounts | No shared accounts, narrow sudo, docker group minimal | `getent group sudo docker` |
| Services | Nothing enabled that isn't needed | `systemctl list-unit-files --state=enabled` |
| Time | NTP synchronised (TLS, logs, Kerberos depend on it) | `timedatectl` |
| Logs | Persistent journal, logrotate working | `journalctl --list-boots`, `/var/lib/logrotate/status` |
| MAC | SELinux enforcing / AppArmor profiles loaded | `getenforce` / `sudo aa-status` |
| setuid | No unexpected setuid files | `sudo find / -xdev -perm -4000 -type f` |

**Key terms**

| Term | Meaning |
|------|---------|
| Attack surface | Everything listening or reachable — minimise it |
| Least privilege | Every account and service gets only what it needs |

**See it on a real system**

Run every "Verify with" command on your lab VM and on one real server (read-only
commands only) and note the differences.

**Hands-on lab (test VM only)**

Turn the table into a script (section 12 style) that prints PASS/FAIL per line and
exits non-zero on any FAIL. Break three items on purpose (enable password auth, open
port 3000 to everyone, enable a useless service) and confirm the script catches all
three.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| Audit finding after a migration | Re-run the checklist; compare `ss -ltnp` before/after | [Ports playbook](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting**

A known-good baseline makes "what's different on this broken server?" answerable.

**Next step**

The L2 bridge: tools that show you what's really happening instead of what you infer.

---

## 17. Debugging tools: the bridge to L2

> 📚 **Study path:** 1) Note: this section, then the [ports playbook](22-playbook-ports-inventory.md) and the [slow system playbook](23-playbook-slow-system.md) · 2) KodeKloud: no course teaches `strace` or `tcpdump`; LFCS — Operations Deployment: Diagnose and Manage Processes covers `lsof` ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page)) and Networking: Start, Stop and Check Status of Network Services covers `ss` ([lesson notes](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page)) · 3) Read: [Spying on your programs with strace](https://wizardzines.com/zines/strace/) and [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/) (free zines, one sitting each) · 4) Practice: the Ops Ladder `strace curl` exercise below, then three [SadServers](https://sadservers.com/scenarios) scenarios with no hints

Sections 1–16 taught you to reason from symptoms, configs and logs. Level L2 adds
tools that let you **look at a layer directly** instead of inferring it — the gap the
Ops Ladder found in your incident notes. Four tools cover most of it:

| Tool | Layer it shows | Question it answers | Reference |
|------|----------------|---------------------|-----------|
| `ss` | Sockets in the kernel | Who listens on PORT, on which address? Which connections exist, in which state? | [Network reference](02-network.md) |
| `lsof` | Open files of every process | Which files, logs, sockets and deleted files does PID hold? Who holds this file or mount? | [Processes reference](05-processes.md) |
| `strace` | System calls | What is this program really asking the kernel for, and which call fails? | [Processes reference](05-processes.md) |
| `tcpdump` | Packets on an interface | Did the packet leave? Did an answer come back? Who sent the reset? | [Learn: networking](28-learn-networking.md) |

All four only observe, but `strace` slows down the program it traces and `tcpdump`
captures can contain passwords and cookies. Each topic says how to use them safely on
production.

### The port-to-logs walk

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

This is the Ops Ladder L1 exit test turned into a method: given only a port number,
name the process, the unit that starts it, its config file and the command that shows
its logs. Every hop uses something from an earlier section; the walk strings them
together so you never have to search the web for it again.

```
 PORT ──sudo ss -ltnp──▶ PID + program name
                          │
                          ├─ "docker-proxy" ─▶ docker ps --filter publish=PORT ─▶ CONTAINER (Docker module)
                          ├─ "systemd"      ─▶ systemctl list-sockets ─▶ SOCKET unit ─▶ its SERVICE unit
                          ▼
             ps -o unit= -p PID  /  /proc/PID/cgroup ─▶ UNIT (or docker-ID.scope, or session-N.scope = by hand)
                          │
                          ▼
             readlink /proc/PID/exe ─▶ binary ─dpkg -S─▶ PACKAGE (or "no path found" = hand-installed)
                          │
                          ▼
             systemctl cat UNIT ─▶ ExecStart, EnvironmentFile ─▶ CONFIG (apache2ctl -S, nginx -T)
                          │
                          ▼
             journalctl -u UNIT  +  lsof -p PID | grep log  +  ErrorLog/CustomLog ─▶ LOGS
```

**Key terms**

| Term | Meaning |
|------|---------|
| Listener | A socket in LISTEN state, bound to an address and a port |
| `docker-proxy` | Docker's userland proxy; when it owns a host port, a container publishes that port |
| Main PID | The process systemd supervises for a unit (`systemctl show -p MainPID --value UNIT`) |
| Scope | cgroup for processes systemd didn't start itself: containers (`docker-ID.scope`) and logins (`session-N.scope`) |
| `apache2ctl -S` | Apache's parsed vhost map: every port and name with its file and line, plus the main ErrorLog |

**See it on a real system**

The walk on your Apache host after the move to 81/444. Each step uses the playbook
format, because this is the exact sequence you will run under pressure.

**Step 1 — Who listens on the port?**

**Goal:** turn the port number into a PID and a program name.

```bash
sudo ss -ltnp 'sport = :444'     # sudo: without it the Process column is empty for other users' sockets
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511                *:444             *:*    users:(("apache2",pid=1125,fd=4),("apache2",pid=1124,fd=4),("apache2",pid=1123,fd=4))
```

**What it means:** three `apache2` processes share one listening socket; the lowest PID
(1123) is normally the parent. `*:444` means every address, IPv4 and IPv6. Recv-Q 0
means no connections are waiting for `accept()`, so the server keeps up.

**Why this step (now):** the port is the only fact you were given, and `ss` reads it
straight from the kernel's socket table — no config file can lie to it. Configs tell
you what *should* listen; `ss` tells you what *does*.

**Next step:** If the program is a normal daemon → Step 2. If it is `docker-proxy` →
`docker ps --filter publish=444 --format '{{.Names}}'` names the container (on a
Dokploy host, port 443 gives `dokploy-traefik`); continue in
[Learn: Docker](30-learn-docker.md). If it is `systemd` → `systemctl list-sockets`
names the socket unit; do Step 2 with the service it activates. If the Process column
is empty → rerun with `sudo`. If `ss` shows nothing but clients still connect → a NAT
rule forwards the port (Docker with the userland proxy turned off):
`sudo iptables -t nat -S DOCKER`.

**Step 2 — Which unit or container owns the PID?**

**Goal:** go from a process to the thing that starts and supervises it.

```bash
ps -o pid,ppid,user,etime,cmd -p 1123
ps -o unit= -p 1123              # systemd unit (procps-ng)
cat /proc/1123/cgroup            # the same answer, straight from the kernel
```

```
    PID    PPID USER         ELAPSED CMD
   1123       1 root     12-03:14:55 /usr/sbin/apache2 -k start
apache2.service
0::/system.slice/apache2.service
```

**What it means:** PPID 1 and the cgroup `system.slice/apache2.service` say systemd
started it as `apache2.service`. A `docker-HASH.scope` cgroup would mean a container;
`user.slice/.../session-N.scope` would mean someone started it by hand from a login
session — no unit, no restart policy, no journal entry for its output.

**Why this step (now):** stopping, restarting, disabling and reading logs all go
through the unit, not the PID. Killing a PID that a unit supervises just makes systemd
start it again (`Restart=`), and killing a session process leaves no record of what it
was.

**Next step:** If it is a `.service` → Step 3. If it is a container scope →
`docker ps --no-trunc | grep HASH` and continue in [Learn: Docker](30-learn-docker.md).
If it is a session scope → note the owner (`ps -o user=,lstart= -p PID`), find how it
was started (`sudo tr '\0' '\n' < /proc/PID/environ`, shell history, `last`), and plan
a proper unit (section 6).

**Step 3 — What binary is it, and from which package?**

**Goal:** know what the program is and how it was installed.

```bash
sudo readlink /proc/1123/exe
dpkg -S /usr/sbin/apache2
```

```
/usr/sbin/apache2
apache2-bin: /usr/sbin/apache2
```

**What it means:** it is the packaged Apache binary from `apache2-bin`. "no path found
matching pattern" would mean a hand-installed binary (look in `/opt` and
`/usr/local`); a path ending in `(deleted)` means it was upgraded on disk and the
running copy is the old one.

**Why this step (now):** how something was installed decides how you upgrade,
configure and remove it, and where its default config lives (`dpkg -L PACKAGE`). It
also catches the impostor: a process named `apache2` whose binary is not
`/usr/sbin/apache2`.

**Next step:** If packaged → Step 4. If hand-installed → in Step 4 read the unit's
`ExecStart=` and `WorkingDirectory=`; the config usually sits next to the binary.

**Step 4 — Where is its configuration?**

**Goal:** find the unit file, the config files and, for a web server, the vhost that
serves this port.

```bash
systemctl cat apache2 | grep -E '^# /|ExecStart|EnvironmentFile'
sudo apache2ctl -S
```

```
# /usr/lib/systemd/system/apache2.service
ExecStart=/usr/sbin/apachectl start
VirtualHost configuration:
*:444                  is a NameVirtualHost
         default server app1.example.com (/etc/apache2/sites-enabled/app1-le-ssl.conf:2)
         port 444 namevhost app1.example.com (/etc/apache2/sites-enabled/app1-le-ssl.conf:2)
         port 444 namevhost app2.example.com (/etc/apache2/sites-enabled/app2-le-ssl.conf:2)
*:81                   is a NameVirtualHost
         default server app1.example.com (/etc/apache2/sites-enabled/app1.conf:1)
         port 81 namevhost app1.example.com (/etc/apache2/sites-enabled/app1.conf:1)
         port 81 namevhost app2.example.com (/etc/apache2/sites-enabled/app2.conf:1)
ServerRoot: "/etc/apache2"
Main DocumentRoot: "/var/www/html"
Main ErrorLog: "/var/log/apache2/error.log"
...
User: name="www-data" id=33
Group: name="www-data" id=33
```

**What it means:** the unit runs `apachectl start`, so the config is Apache's own tree
under `/etc/apache2/`. `apache2ctl -S` maps each port to its vhosts with the **file and
line** that defines them: port 444 is served by `app1-le-ssl.conf` (also the default
for names that match nothing) and `app2-le-ssl.conf`.

**Why this step (now):** you now know exactly which files to read, back up or change.
The "default server" line tells you which site answers requests whose Host header
matches nothing — the first surprise after any migration.

**Next step:** For Nginx use `sudo nginx -T | grep -E 'listen|server_name|# configuration file'`;
for other apps read the `ExecStart=` arguments and the `EnvironmentFile=`. Then →
Step 5.

**Step 5 — Where are its logs?**

**Goal:** name the command that shows this service's logs.

```bash
journalctl -u apache2 -n 5 --no-pager
sudo grep -hE '^\s*(ErrorLog|CustomLog)' /etc/apache2/sites-enabled/app1-le-ssl.conf
sudo lsof -nP -p 1123 | grep -E '\.log$'
```

```
Oct 03 00:00:01 web01 systemd[1]: Reloading apache2.service - The Apache HTTP Server...
Oct 03 00:00:01 web01 systemd[1]: Reloaded apache2.service - The Apache HTTP Server.
	ErrorLog ${APACHE_LOG_DIR}/app1-error.log
	CustomLog ${APACHE_LOG_DIR}/app1-access.log combined
apache2 1123 root    2w   REG  252,0   88213  1311 /var/log/apache2/error.log
apache2 1123 root    7w   REG  252,0  401977  1320 /var/log/apache2/app1-error.log
apache2 1123 root    8w   REG  252,0 9120334  1322 /var/log/apache2/app1-access.log
```

**What it means:** the journal only has systemd's own start, stop and reload messages
(here the nightly logrotate reload); Apache writes its real logs to its own files. The
vhost's `ErrorLog`/`CustomLog` lines and the open files agree: `app1` logs to
`app1-error.log` and `app1-access.log` under `/var/log/apache2/`.

**Why this step (now):** the exit-test answer is a command you can paste:
`sudo tail -f /var/log/apache2/app1-error.log`, plus `journalctl -u apache2` for
start-up failures. Cross-checking the config with `lsof` proves these are the files in
use, not stale leftovers.

**Next step:** Done — write the answer: "444 → apache2 (PID 1123) → apache2.service →
/etc/apache2/sites-enabled/app1-le-ssl.conf → `sudo tail -f
/var/log/apache2/app1-error.log`". If the log exists but stays empty → section 14
(logrotate, deleted files). For a container → `docker logs CONTAINER`.

**Hands-on lab (test VM only)**

**Step 1 — Build three kinds of owner.** On the VM, give each port a different owner:

```bash
sudo apt install -y apache2                                        # packaged service on 80
sudo systemd-run --unit=report-api /usr/bin/python3 -m http.server 8731 --bind 127.0.0.1
nohup python3 -m http.server 8732 > /tmp/adhoc.log 2>&1 &          # started by hand: no unit
```

**Step 2 — Walk each port** (80, 8731, 8732) through the five steps and fill in a
table: port, PID, unit or "none", binary and package, config, log command. Time
yourself; the L1 target is five minutes per port.

**Step 3 — Break it.** Stop the transient unit (`sudo systemctl stop report-api`) and
start a different program on the same port (`python3 -m http.server 8731 &`). Walk 8731
again: the answer changes from a unit to a session process — the "same port, different
owner" situation after a half-finished migration. Clean up: check `jobs -l`, then
`kill %1 %2`.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `ss -p` shows no process | Rerun with `sudo` | This topic |
| Port answers, but `ss -ltn` shows no listener | `sudo iptables -t nat -S DOCKER` (a DNAT rule forwards it) | [Learn: Docker](30-learn-docker.md) |
| Owner is `systemd` | `systemctl list-sockets` | Section 6 |
| Owner is `docker-proxy` | `docker ps --filter publish=PORT` | [Containers playbook](26-playbook-containers-k8s.md) |
| Process has no unit (session scope) | `ps -o user=,lstart= -p PID`, `last` | Section 4 |
| Two configs claim the same port | `sudo apache2ctl -S`, `sudo nginx -T` | [Ports playbook](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting**

This walk is what the original Apache → Dokploy investigation needed and didn't have.
It is also the first move of every "site down" and "address already in use" incident;
the full inventory version, for every port on a server, is the
[ports playbook](22-playbook-ports-inventory.md).

**Next step**

lsof — the tool behind steps 1 and 5, and much more.

### lsof: open files, sockets and deleted files

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

On Linux almost everything a process touches is a file descriptor: regular files,
directories, pipes, Unix sockets and TCP/UDP sockets. `lsof` ("list open files") reads
`/proc/PID/fd` and friends for every process and prints one table. It answers questions
from both directions: "what does this process have open?" and "which process has this
file, mount or port open?".

```
 process 1123 (apache2)
 ├── cwd  /                                    ← working directory
 ├── txt  /usr/sbin/apache2                     ← the program itself
 ├── mem  /usr/lib/x86_64-linux-gnu/libssl.so.3 ← mapped libraries
 ├── 2w   /var/log/apache2/error.log            ← fd 2, open for writing
 ├── 4u   IPv6 *:444 (LISTEN)                   ← a socket, read and write
 └── 9w   /var/log/apache2/old.log (deleted)    ← gone from the directory, still using disk
```

**Key terms**

| Item | Meaning |
|------|---------|
| FD column | `cwd`, `txt`, `mem`, or a number plus mode: `r` read, `w` write, `u` both |
| TYPE | `REG` file, `DIR`, `IPv4`/`IPv6` socket, `unix`, `FIFO` pipe |
| `-nP` | No DNS or port-name lookups: faster, and shows numbers |
| `-p PID`, `-u USER`, `-c NAME` | Select by process, user or command name |
| `-iTCP:443 -sTCP:LISTEN` | Select network files by protocol, port and state |
| `-a` | AND the selections (the default is OR) |
| `+L1` | Files with link count 0: deleted but still open |
| `+f -- /mnt/data` | Everything open on that filesystem |

**See it on a real system**

```bash
sudo lsof -nP -iTCP:444 -sTCP:LISTEN               # who listens (the same answer as ss, another view)
sudo lsof -nP -a -p 1123 -iTCP -sTCP:ESTABLISHED   # current client connections of one process
sudo lsof -nP +L1                                  # deleted files that still hold space
sudo lsof -nP +f -- /mnt/backup                    # what keeps a mount busy
```

```
$ sudo lsof -nP -iTCP:444 -sTCP:LISTEN
COMMAND  PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
apache2 1123     root    4u  IPv6  23456      0t0  TCP *:444 (LISTEN)
apache2 1124 www-data    4u  IPv6  23456      0t0  TCP *:444 (LISTEN)
apache2 1125 www-data    4u  IPv6  23456      0t0  TCP *:444 (LISTEN)
$ sudo lsof -nP +L1
COMMAND  PID USER   FD   TYPE DEVICE   SIZE/OFF NLINK   NODE NAME
java    2671  app    5w   REG  252,0 7516192768     0 131202 /var/log/app/app.log.1 (deleted)
```

→ A Java process still writes to a log that someone deleted (by hand, or a logrotate
config without a reload): 7 GB that `du` can't see and `df` still counts. Reloading or
restarting the app releases it.

> ⚠️ You can empty a deleted-but-open file through its descriptor
> (`sudo truncate -s 0 /proc/2671/fd/5`), but its contents are lost for good. Safer
> first: reload or restart the app in a quiet moment; if you must truncate, copy the
> part you need first (`sudo tail -n 10000 /proc/2671/fd/5 > /root/app-tail.log`).

**Hands-on lab (test VM only)**

**Step 1 — Build a writer.**

```bash
sudo systemd-run --unit=lab-holder /bin/sh -c 'exec 3>>/var/tmp/holder.log; while true; do head -c 1M /dev/zero >&3; sleep 1; done'
ls -lh /var/tmp/holder.log            # grows by 1 MB per second
```

**Step 2 — Break.** Delete the file while it is being written:
`sudo rm /var/tmp/holder.log`. `ls` finds nothing, yet `df -h /var/tmp` keeps
falling. Find the space with `sudo lsof -nP +L1 | grep holder` (note PID and FD).

**Step 3 — Fix two ways.** Release the space without stopping the writer:
`sudo truncate -s 0 /proc/PID/fd/3`. Then fix it properly with
`sudo systemctl stop lab-holder`: the space returns once the last descriptor closes.
Bonus: mount the loop device from section 8 on `/mnt/lab`, `cd /mnt/lab` in a second
shell, and try `sudo umount /mnt/lab` → `target is busy`; `sudo lsof +f -- /mnt/lab`
names your shell.

**How it breaks**

| Symptom | First command | Where to go |
|---------|---------------|-------------|
| `df` full, `du` finds much less | `sudo lsof -nP +L1` | Section 8 |
| `umount: target is busy` | `sudo lsof +f -- MOUNTPOINT`, `sudo fuser -vm MOUNTPOINT` | [Storage reference](01-storage-disk.md) |
| `lsof` hangs for minutes | A dead NFS mount: add `-b`, check `findmnt -t nfs,nfs4` | Section 8 |
| `lsof: WARNING: can't stat() fuse.gvfsd-fuse file system` | Harmless; add `-w` to hide warnings | — |
| "Too many open files" | `sudo lsof -nP -p PID | wc -l` versus `/proc/PID/limits` | Section 15 |

**Why it matters for troubleshooting**

`lsof` closes the two most confusing disk incidents (invisible used space, busy mounts)
and finds any app's logs and connections without knowing anything about the app.

**Next step**

strace — when even the open files don't explain what the program is doing.

### strace: watching system calls

**Level:** [L2 · Mid]

**Concept**

A program can't open a file, resolve a name, connect to a server or write a log
without asking the kernel through a **system call**. `strace` uses the kernel's
`ptrace` interface to print every call, its arguments, its result and — on failure —
the error name. It is the "quit thinking and look" tool for programs: instead of
guessing which config file an app reads or why it says "permission denied", you watch
it happen.

```
 program ──openat("/etc/app.conf")───▶ kernel ──▶ = -1 EACCES (Permission denied)
         ──connect(10.0.0.5:5432)────▶ kernel ──▶ = -1 ECONNREFUSED (Connection refused)
           ▲
           └── strace sits here and prints each call with its result
```

**Key terms**

| Item | Meaning |
|------|---------|
| `-f` | Follow child processes and threads (almost always needed) |
| `-e trace=openat,connect` | Only these calls; classes such as `%file`, `%network`, `%process` |
| `-p PID` | Attach to a running process (needs sudo on Ubuntu, which restricts ptrace) |
| `-o FILE`, `-s 200` | Write to a file; show up to 200 characters of each string |
| `-tt`, `-T` | Wall-clock timestamps; time spent inside each call |
| `-c` | Summary table of calls, errors and time instead of every line |
| `ENOENT`, `EACCES`, `ECONNREFUSED`, `ETIMEDOUT` | Not found, permission denied, refused, timed out |
| `EINPROGRESS` | A non-blocking connect has started — normal, not an error |

**See it on a real system**

The Ops Ladder L2 exercise — name every file curl reads and every address it connects
to:

```bash
sudo apt install -y strace
strace -f -e trace=openat,connect curl -so /dev/null https://example.com
```

```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libcurl.so.4", O_RDONLY|O_CLOEXEC) = 3
...
openat(AT_FDCWD, "/usr/lib/ssl/openssl.cnf", O_RDONLY) = 3
[pid  4122] openat(AT_FDCWD, "/etc/nsswitch.conf", O_RDONLY|O_CLOEXEC) = 5
[pid  4122] openat(AT_FDCWD, "/etc/host.conf", O_RDONLY|O_CLOEXEC) = 5
[pid  4122] openat(AT_FDCWD, "/etc/resolv.conf", O_RDONLY|O_CLOEXEC) = 5
[pid  4122] openat(AT_FDCWD, "/etc/hosts", O_RDONLY|O_CLOEXEC) = 5
[pid  4122] connect(5, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("127.0.0.53")}, 16) = 0
[pid  4122] +++ exited with 0 +++
connect(5, {sa_family=AF_INET, sin_port=htons(443), sin_addr=inet_addr("203.0.113.80")}, 16) = -1 EINPROGRESS (Operation now in progress)
openat(AT_FDCWD, "/etc/ssl/certs/ca-certificates.crt", O_RDONLY) = 6
+++ exited with 0 +++
```

→ Read it top to bottom: shared libraries and the OpenSSL config first; then, in
curl's resolver thread (`[pid 4122]`), exactly the files `getent` uses —
`nsswitch.conf`, `host.conf`, `resolv.conf`, `/etc/hosts` — and a DNS query to the
systemd-resolved stub on 127.0.0.53. The main thread then connects to the server on
443 (`EINPROGRESS` is normal for a non-blocking connect) and reads the CA bundle to
verify the certificate. The server address is illustrative.

→ This proves the dig-versus-curl lesson from section 9: curl reads `/etc/hosts`; run
the same trace on `dig example.com` and `/etc/hosts` never appears.

Attaching to a running service shows what it does with each request:

```bash
sudo strace -f -tt -p "$(systemctl show -p MainPID --value demo-web)" -e trace=%network -s 80
```

```
[pid 51200] 10:44:02.118341 accept4(3, {sa_family=AF_INET, sin_port=htons(50512), sin_addr=inet_addr("127.0.0.1")}, [16], SOCK_CLOEXEC) = 4
[pid 51347] 10:44:02.118902 recvfrom(4, "GET / HTTP/1.1\r\nHost: 127.0.0.1:8080\r\nUser-Agent: curl/8.5.0\r\nAccept: */*\r\n\r\n", 8192, 0, NULL, NULL) = 77
[pid 51347] 10:44:02.119611 sendto(4, "HTTP/1.0 200 OK\r\nServer: SimpleHTTP/0.6 Python/3.12.3\r\nDate: Sat, 03 Oct 2026 10"..., 184, 0, NULL, 0) = 184
```

→ One request: accepted on fd 4 by the main thread (51200), then 77 bytes read and the
response headers written back by the handler thread (51347) — `-f` is what makes the
thread visible (`-s 80` cut the string after 80 bytes, hence the `...`). A request
that hangs would stop at a `recvfrom` or `connect` with no result line yet — the call
it is waiting in names the problem.

> ⚠️ strace stops the traced process at **every** traced system call; a busy proxy or
> database can slow down ten times or more while attached. On production: filter with
> `-e trace=`, attach for seconds, prefer `-c` for a summary, detach with Ctrl-C (the
> process keeps running), and avoid tracing PID 1 or a database primary under load.

**Hands-on lab (test VM only)**

**Step 1 — The Ops Ladder exercise.** Run the curl trace above and list, in two
columns, every file it reads and every address it connects to. Then trace
`getent ahosts example.com` and `dig example.com` the same way: only one of them opens
`/etc/hosts`.

**Step 2 — Break: the vague permission error.** Using the site from section 2, run
`sudo chmod 600 /srv/site/index.html`, then
`sudo -u www-data strace -e trace=openat cat /srv/site/index.html`. The trace ends with
`openat(AT_FDCWD, "/srv/site/index.html", O_RDONLY) = -1 EACCES (Permission denied)`:
the exact path and error, even when an app's own message only says "could not load
page".

**Step 3 — Fix and watch a live service.** `sudo chmod 644 /srv/site/index.html` and
trace again (`= 3` now). Then start `demo-web` from section 6, attach with the
command above, `curl http://127.0.0.1:8080/` from another terminal and watch `accept4`,
`recvfrom` and `sendto` go by. Detach with Ctrl-C.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `strace: attach: ptrace(PTRACE_SEIZE, PID): Operation not permitted` | Use `sudo` (Ubuntu restricts ptrace with `kernel.yama.ptrace_scope`) | Section 15 |
| Output floods the terminal | `-e trace=%file` or `%network`, `-o /tmp/trace.txt`, then `grep -E 'ENOENT|EACCES' /tmp/trace.txt` | This topic |
| The interesting part never shows up | Work happens in a child or a thread: add `-f` | This topic |
| The process runs in a container | Get the host PID (`docker inspect -f '{{.State.Pid}}' CONTAINER`) and trace it from the host with sudo | [Learn: Docker](30-learn-docker.md) |
| Dozens of `ENOENT` lines | Usually normal probing of search paths; look at the **last** failing call before the error | This topic |

**Why it matters for troubleshooting**

When the logs say nothing useful, the system calls still tell the truth: which config
file was really opened, which address was dialled, which call failed with which error.
It turns "the app is broken" into "the app can't read `/etc/app/key.pem`: EACCES".

**Next step**

tcpdump — the same "look, don't guess" idea for packets on the wire.

### tcpdump: seeing the packets

**Level:** [L2 · Mid]

**Concept**

strace shows what a program asks the kernel for; `tcpdump` shows what really leaves
and arrives on a network interface. It closes the Ops Ladder's first blind spot: a DNS
write-up *infers* where a query died, a capture *shows* it — did the query leave the
host, which server did it go to, did an answer come back? A filter expression keeps
the capture small and readable.

```
 app ─▶ socket ─▶ kernel (routing, firewall, NAT) ─▶ interface ens18 ─▶ wire ─▶ server
                                                         ▲
                                     tcpdump -i ens18 copies packets here
                                     (incoming packets are seen BEFORE the firewall drops them)

 TCP flags:  [S] SYN   [S.] SYN-ACK   [.] ACK   [P.] data   [F.] FIN   [R] or [R.] reset
```

**Key terms**

| Item | Meaning |
|------|---------|
| `-i any` / `-i ens18` | All interfaces / one interface (with `any`, each line shows the interface and In/Out) |
| `-n` | Don't resolve names — always use it; lookups create their own DNS traffic |
| `-c 20` | Stop after 20 packets |
| `-w FILE.pcap` / `-r FILE.pcap` | Save raw packets for Wireshark / read them back |
| `-A` | Print payloads as ASCII (only useful for plain HTTP) |
| Filters | `port 53`, `host 192.0.2.53`, `tcp port 444 and host 198.51.100.23`, `not port 22` |
| `[S]` → `[S.]` → `[.]` | The three-way handshake: the connection is established |
| `[R]` after `[S]` | Port closed: "Connection refused" |
| `[S]` repeated, no reply | Dropped by a firewall, a wrong route or a dead host: "Connection timed out" |

**See it on a real system**

```bash
sudo tcpdump -ni any port 53                     # the Ops Ladder command; repeat the failing curl in a 2nd terminal
sudo tcpdump -ni ens18 -c 6 'tcp port 444 and host 198.51.100.23'
sudo tcpdump -ni ens18 -c 500 -w /tmp/site.pcap 'tcp port 444'    # save for Wireshark
```

```
$ sudo tcpdump -ni any port 53          (loopback lines to and from 127.0.0.53 left out)
10:21:04.118611 ens18 Out IP 192.0.2.10.36541 > 192.0.2.53.53: 3315+ [1au] A? app.example.com. (44)
10:21:04.118702 ens18 Out IP 192.0.2.10.40122 > 192.0.2.53.53: 6610+ [1au] AAAA? app.example.com. (44)
10:21:04.120982 ens18 In  IP 192.0.2.53.53 > 192.0.2.10.36541: 3315 1/0/1 A 192.0.2.80 (60)
10:21:04.121104 ens18 In  IP 192.0.2.53.53 > 192.0.2.10.40122: 6610 0/1/1 (99)
```

→ The query leaves through `ens18` to 192.0.2.53, the A answer `192.0.2.80` comes back
in 2 ms, and the AAAA query gets no address (`0/1/1`: no answer, one authority record).
DNS works; look elsewhere.

A working connection, a refused one and a dropped one (TCP options trimmed):

```
10:30:01.000101 ens18 In  IP 198.51.100.23.51544 > 192.0.2.10.444: Flags [S], seq 1432598711, win 64240, length 0
10:30:01.000144 ens18 Out IP 192.0.2.10.444 > 198.51.100.23.51544: Flags [S.], seq 2771904410, ack 1432598712, win 65160, length 0
10:30:01.012388 ens18 In  IP 198.51.100.23.51544 > 192.0.2.10.444: Flags [.], ack 1, win 502, length 0

10:31:15.400200 ens18 In  IP 198.51.100.23.51600 > 192.0.2.10.8443: Flags [S], seq 99120333, win 64240, length 0
10:31:15.400231 ens18 Out IP 192.0.2.10.8443 > 198.51.100.23.51600: Flags [R.], seq 0, ack 99120334, win 0, length 0

10:32:40.100800 ens18 In  IP 198.51.100.23.51702 > 192.0.2.10.3000: Flags [S], seq 3011200, win 64240, length 0
10:32:41.112905 ens18 In  IP 198.51.100.23.51702 > 192.0.2.10.3000: Flags [S], seq 3011200, win 64240, length 0
10:32:43.128911 ens18 In  IP 198.51.100.23.51702 > 192.0.2.10.3000: Flags [S], seq 3011200, win 64240, length 0
```

→ First block: a full handshake on 444 — network and listener are fine; if the site
still fails, look at TLS or the app. Second: the SYN on 8443 is answered by a reset —
the host is reachable but nothing listens (curl says "Connection refused"). Third: the
SYN to 3000 is retransmitted after 1 s and 2 s more with no reply — the packet arrives
but UFW drops it (curl says "Connection timed out"). That is the refused-versus-timeout
case from the Ops Ladder, proven with packets.

> ⚠️ Captures contain whatever crosses the wire: cookies, tokens, and passwords on plain
> HTTP or internal protocols. On production always use a filter and a limit (`-c`, or
> `-C 50 -W 4` to rotate four files of about 50 MB), keep `.pcap` files only as long as
> you need them, then delete them. Some organisations require approval before you
> capture.

**Hands-on lab (test VM only)**

**Step 1 — Watch DNS work.** Terminal 1: `sudo tcpdump -ni any port 53`. Terminal 2:
`getent ahosts example.com`. Find the stub query (to 127.0.0.53 on `lo`) and the
upstream query (to the DNS server from your netplan file).

**Step 2 — Break it (Ops Ladder L2 drill).** Point netplan at a dead resolver
(192.0.2.250, as in section 9) and repeat: queries leave, nothing comes back. Restore
netplan, then break `/etc/hosts` instead (`203.0.113.99 example.com`): `getent` answers
instantly and tcpdump shows **no DNS packets at all** — the answer came from a file.

**Step 3 — Refused versus timed out.** On the VM run `python3 -m http.server 8082` in
one terminal and `sudo tcpdump -ni any 'tcp port 8082'` in another. From your laptop:
`curl -m 5 http://VM_IP:8082/` (handshake), stop the server and curl again (`[R.]`),
then, with UFW enabled, `sudo ufw deny 8082/tcp` and curl once more (repeated `[S]`).
Fix with `sudo ufw delete deny 8082/tcp`. Save one capture with `-w /tmp/lab.pcap`,
copy it to your laptop with `scp`, open it in Wireshark, then delete it.

**How it breaks**

| Symptom / error | First command | Where to go |
|-----------------|---------------|-------------|
| `tcpdump: any: You don't have permission to perform this capture on that device` | Use `sudo` | This topic |
| Nothing captured although traffic flows | Wrong interface: container traffic uses `docker0`, `veth*` and bridges → `-i any`, or capture inside the container: `sudo nsenter -t PID -n tcpdump -ni eth0` | [Learn: Docker](30-learn-docker.md) |
| `N packets dropped by kernel` | Narrower filter, `-n`, and `-w FILE` instead of printing | This topic |
| Your own SSH session floods the output | Add `and not port 22` | This topic |
| HTTPS payload unreadable | Expected — TLS is encrypted; use `curl -v` and the app's logs for content | [Learn: networking](28-learn-networking.md) |

**Why it matters for troubleshooting**

Every network argument — "the firewall is fine", "DNS is fine", "the server never got
my request" — ends with a capture. It is the evidence the L2 exit test asks for; the
deep dive (handshakes, retransmissions, TLS) is in
[Learn: networking](28-learn-networking.md).

**Next step**

Put all the tools in this module into one decision tree.

### Which tool for which question

**Level:** [L1 · Junior] → [L2 · Mid]

**Concept**

Under pressure you don't need every tool; you need the right first one. This tree maps
the symptoms you will meet most often on a Linux server to the first command and to the
section of this module that explains it. Take the first branch that matches, and stop
guessing as soon as one command gives you evidence.

```
 Symptom on a Linux server                      First commands                                    Sections
 │
 ├─ "Port busy" / "who is on PORT?" ──────────▶ sudo ss -ltnp 'sport = :PORT' → port-to-logs walk   17, 6
 ├─ Service won't start / keeps restarting ───▶ systemctl status UNIT → journalctl -u UNIT -b       6
 │                                              (203/EXEC, 217/USER, 200/CHDIR, "repeated too quickly")
 ├─ "Permission denied" / 403 ────────────────▶ namei -l PATH → sudo -u USER test → getfacl, lsattr  2, 16
 │                                              → AVC / AppArmor denials
 ├─ "No space left on device" ────────────────▶ df -h → df -i → sudo lsof -nP +L1 → du -xh          8, 17
 ├─ Slow, high load ──────────────────────────▶ uptime → vmstat 1 → ps state R or D → iostat -xz 1   4, 23
 ├─ Process vanished, its log says nothing ───▶ journalctl -k (OOM) → exit code 137/143            15, 4
 ├─ Can't resolve a name ─────────────────────▶ getent ahosts → resolvectl status → tcpdump port 53  9, 17
 ├─ Can't connect (refused or timed out) ─────▶ ss -ltn on the server → ufw status → tcpdump the SYN 9, 16, 17
 ├─ Works by hand, fails in cron or systemd ──▶ compare env, PATH, User=, umask, PrivateTmp          11, 6, 2
 ├─ Won't boot ───────────────────────────────▶ console → which stage failed → GRUB e, init=/bin/bash 7
 └─ App fails with no useful error ───────────▶ strace -f -e trace=%file,%network → lsof -p PID      17
```

**Key terms**

| Term | Meaning |
|------|---------|
| Evidence | Output that confirms or kills a hypothesis: a log line, a syscall error, a packet |
| Layer | Where the fault lives: hardware, kernel, filesystem, process, unit, network, app |
| First command | The cheapest read-only command that splits the problem in two |

**See it on a real system**

A first look you can run in under a minute on any unfamiliar server before you follow
the tree (all read-only):

```bash
uptime; free -h; df -hT -x tmpfs -x devtmpfs -x squashfs
systemctl --failed --no-legend
journalctl -p err -b -n 15 --no-pager
sudo ss -ltnp
```

```
 10:52:11 up 12 days,  3:14,  2 users,  load average: 0.41, 0.38, 0.35
               total        used        free      shared  buff/cache   available
Mem:           3.8Gi       1.9Gi       212Mi        12Mi       1.9Gi       1.7Gi
Swap:          3.8Gi       420Mi       3.4Gi
Filesystem                        Type  Size  Used Avail Use% Mounted on
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   48G   41G  4.6G  90% /
/dev/sda2                         ext4  2.0G  196M  1.6G  11% /boot
● certbot.service loaded failed failed Certbot
Oct 03 10:40:02 web01 certbot[51220]: Some challenges have failed.
...
```

→ Root at 90 % and a failed `certbot.service`: two leads before you have opened a
single log file. The disk branch and the service branch of the tree say what to run
next. (On your Apache host, certbot's HTTP-01 challenge needs port 80, which Traefik
owns since the migration — see [Deployment patterns](35-deployment-patterns.md).)

**Hands-on lab (test VM only)**

**Step 1 — Build a break kit.** Ask a colleague (or write a script you don't read
afterwards) to apply one random break from the labs in this module: a full `/var`, a
wrong `ExecStart=`, `chmod 700` on a web root, a dead DNS server in netplan, a UFW deny
on the web port, a deleted-but-open log.

**Step 2 — Diagnose with the tree.** Start a timer, run the first look, follow the
matching branch, and write down the evidence that settled it before you change
anything.

**Step 3 — Fix and record.** Fix it, verify it, and write the Ops Ladder five-line
note: symptom, first wrong guess, deciding evidence, fix, and what you will check
first next time.

**How it breaks**

| Trap | Why it misleads | Do instead |
|------|-----------------|------------|
| Starting with the tool you know best | Every problem looks like a disk problem to `du` | Run the first look, then follow the tree |
| Changing things while diagnosing | You destroy evidence and add new faults | Read-only commands first; then one change at a time, with a rollback |
| Trusting a config file over the kernel | Configs say what *should* happen | `ss`, `/proc`, `strace` and `tcpdump` show what *does* happen |
| Stopping at the first error line | It is often a consequence, not the cause | Find the **earliest** error in the time window |

**Why it matters for troubleshooting**

Senior engineers aren't faster because they type faster. They pick a first command
that halves the search space, and they stop guessing once they have evidence. The tree
is that habit written down — the same method the [ports](22-playbook-ports-inventory.md)
and [slow system](23-playbook-slow-system.md) playbooks follow in depth.

**Next step**

Prove all of it under time pressure: the exit tests.

---

## 18. Self-check / exit test

> 📚 **Study path:** 1) Note: reread the "How it breaks" tables of the areas you feel least sure about · 2) KodeKloud: *Linux Challenges* (free; five timed challenges on disks, users, permissions, services and packet filtering — use it as your L1 exit check) ([course](https://kodekloud.com/courses/linux-challenges)), then the two mock exams in *Prep Course - Linux Foundation Certified System Administrator (LFCS)* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Practice: five [SadServers](https://sadservers.com/scenarios) easy scenarios inside their time limits · 4) Practice: [Killercoda Linux scenarios](https://killercoda.com/linux) on days you don't want to start a VM

Rules for every test here: a fresh test VM, a timer, **no notes and no web search**.
You pass when you finish inside the time **and** can show the evidence — a command and
its output — for every answer. If you fail, note which section you needed, redo its
lab, and retake the test a week later.

### L0 exit test (30 minutes)

**Level:** [L0 · Fresher] — pass it and your Fresher foundations are done.

From the Ops Ladder: on a fresh VM with no notes, create a sudo user with key-only
SSH, find the five largest files under `/var`, explain every field of `ls -l`, and
revert a bad Git commit.

| # | Task | Prove it with | Taught in |
|---|------|---------------|-----------|
| 1 | Create user `ops` with sudo and **key-only** SSH | `ssh ops@VM_IP 'sudo -v && echo OK'` works; `ssh -o PubkeyAuthentication=no ops@VM_IP` fails with `Permission denied (publickey)`; `sudo sshd -T` shows `passwordauthentication no` | Sections 3, 10 |
| 2 | Find the five largest files under `/var` | `sudo find /var -xdev -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5`, and say why `-xdev` and `2>/dev/null` are there | Sections 8, 13 |
| 3 | Explain every field of `ls -l` | Say each field aloud for `ls -ld /usr/bin/passwd /tmp /etc/resolv.conf`: type, the three triplets, `s` and `t`, link count, owner, group, size, mtime, name, `->` target | Sections 1, 2 |
| 4 | Revert a bad Git commit | `git log --oneline` shows a new commit that undoes the bad one, and the history is not rewritten | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md); KodeKloud *GIT for Beginners* — Resetting and Reverting ([course](https://kodekloud.com/courses/git-for-beginners)) |

Task 4 is the only one taught outside this module, so here is the minimal safe
version:

```bash
cd ~/lab/repo
git log --oneline -3              # find the bad commit
git revert --no-edit HEAD         # a NEW commit that undoes it: safe on shared branches
git log --oneline -3
```

```
$ git log --oneline -3
9f2c1ab (HEAD -> main) Set Listen 8080 in ports.conf
41d7e09 Add app2 vhost
c3a9b12 Initial Apache config
$ git revert --no-edit HEAD
[main 5be0d44] Revert "Set Listen 8080 in ports.conf"
 1 file changed, 1 insertion(+), 1 deletion(-)
$ git log --oneline -3
5be0d44 (HEAD -> main) Revert "Set Listen 8080 in ports.conf"
9f2c1ab Set Listen 8080 in ports.conf
41d7e09 Add app2 vhost
```

→ `revert` adds history instead of deleting it, so nobody who already pulled is
affected. `git reset --hard` rewrites history: use it only on commits nobody else has.

L0 drills to tick before you sit the test (from the Ops Ladder):

- Linux Upskill Challenge days 1–10 on a homelab VM ([linuxupskillchallenge.org](https://linuxupskillchallenge.org/)).
- The health-report script from section 12, with zero ShellCheck warnings.

### L1 exit test (5 minutes per port)

**Level:** [L1 · Junior] — pass it and you can operate servers on your own.

From the Ops Ladder: given only a port number, name the process, the unit that starts
it, its config file and the command that shows its logs. The method is the
port-to-logs walk in section 17.

**Setup, run by a colleague** while you look away. It creates a service with a
misleading description, its config in an unusual place and its logs in a file:

```bash
# Run by a colleague on the TEST VM only.
sudo useradd --system --no-create-home --shell /usr/sbin/nologin invsync
sudo mkdir -p /etc/inventory-sync /var/log/inventory-sync /srv/inventory-sync
echo 'PORT=8731' | sudo tee /etc/inventory-sync/sync.env
echo 'inventory ok' | sudo tee /srv/inventory-sync/index.html
sudo chown invsync: /var/log/inventory-sync
sudo tee /etc/systemd/system/inventory-sync.service > /dev/null <<'EOF'
[Unit]
Description=Nightly sync helper

[Service]
User=invsync
EnvironmentFile=/etc/inventory-sync/sync.env
WorkingDirectory=/srv/inventory-sync
ExecStart=/bin/sh -c 'exec /usr/bin/python3 -m http.server "$PORT" >> /var/log/inventory-sync/sync.log 2>&1'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now inventory-sync
```

**Your task:** you are told only "8731". Fill in four lines inside five minutes:

```
port 8731 → process: ____________ (PID ______)
unit:        ____________
config:      ____________
logs:        ____________
```

**Model answer** (read it only after the timer): the process is `python3` (from
`ss -ltnp`); the unit is `inventory-sync.service` (from `ps -o unit=`); the config is
`/etc/systemd/system/inventory-sync.service` plus `/etc/inventory-sync/sync.env` (from
`systemctl cat`); the logs are `sudo tail -f /var/log/inventory-sync/sync.log` — the
journal only shows start and stop, because the unit sends the output to a file (from
`systemctl cat` and `sudo lsof -p PID`).

Retake it with three variants until each takes under five minutes: a socket-activated
service (owner `systemd`), a container (`docker run -d -p 8733:80 nginx`, owner
`docker-proxy`), and a process started with `nohup` (the right answer is "no unit —
started by hand in session N; propose a unit").

L1 drills to tick before you sit the test (from the Ops Ladder):

- Write a systemd unit for a small Python HTTP server with `Restart=on-failure`, kill it with `kill -9` and find the restart in the journal (section 6).
- Fill `/var` on a test VM until a service fails; find which one and why using only `journalctl`, `df` and `du` (section 8).
- Solve five SadServers easy scenarios inside their time limits.

Cleanup for the colleague: `sudo systemctl disable --now inventory-sync`, remove
`/etc/systemd/system/inventory-sync.service` and run `sudo systemctl daemon-reload`,
then delete `/etc/inventory-sync`, `/srv/inventory-sync` and `/var/log/inventory-sync`
(check each path with `ls -ld` before `sudo rm -r`), and finally `sudo userdel invsync`.

### Timed practical tasks

**Level:** [L0 · Fresher] → [L2 · Mid]

Pick five at random each week (roll a die, or let a colleague choose). Each has a time
limit and the section that teaches it.

| # | Task (test VM) | Limit | Section |
|---|----------------|-------|---------|
| 1 | Show which package owns `/usr/sbin/apachectl` and which of its config files were edited locally | 2 min | 5 |
| 2 | Stop Apache so it stays stopped after a reboot and an `apt upgrade`, and write the one-line rollback | 2 min | 6 |
| 3 | A unit fails with `status=203/EXEC`: find the cause | 3 min | 6 |
| 4 | Show only errors from the previous boot | 1 min | 6, 14 |
| 5 | Give user `auditor` read access to `/var/log/apache2`, including files created tomorrow | 4 min | 2 |
| 6 | Grow `/` online using free space in the volume group | 3 min | 8 |
| 7 | Add a data disk by UUID so that a missing disk can never block boot, and verify it before rebooting | 5 min | 8 |
| 8 | Name the DNS servers this host really uses, and show why `dig` and `curl` disagree for one name | 3 min | 9 |
| 9 | Reach a service bound to 127.0.0.1:3000 on the VM from your laptop without opening a port | 2 min | 10 |
| 10 | Enable UFW over SSH with an automatic rollback armed | 3 min | 11, 16 |
| 11 | From an access log: the top 10 client IPs, and the 5xx count per minute | 4 min | 13 |
| 12 | Find which process holds 2 GB of deleted files and free the space | 3 min | 8, 17 |
| 13 | Explain why nginx still has a 1024 open-files limit after editing `limits.conf`, and fix it | 4 min | 15 |
| 14 | Prove that a Docker-published port bypasses UFW, then close it properly | 5 min | 16 |
| 15 | Name every file curl reads and every address it connects to for one HTTPS request | 5 min | 17 |
| 16 | Prove whether DNS queries leave the host and whether answers come back | 3 min | 17 |

### Knowledge questions

**Level:** [L0 · Fresher] → [L1 · Junior]

Answer aloud or in writing, then check yourself against the answers below.

1. Why does `sudo echo x > /etc/app.conf` fail with "Permission denied"?
2. What does a `+` right after the permission bits in `ls -l` mean?
3. What is the difference between `usermod -G docker USER` and `usermod -aG docker USER`?
4. A process is in state `D` and `kill -9` does nothing. Why, and what do you check next?
5. One container exited with code 137, another with 143. What happened to each?
6. What is the difference between `systemctl stop`, `disable` and `mask`?
7. Why is `After=network-online.target` on its own not enough?
8. Which `/etc/fstab` options stop a missing disk from dropping the server into emergency mode?
9. `df` shows `/` at 100 %, but `du` finds only half of that. Name two causes.
10. Why does `ss -ltnp` show `systemd` on port 22 on Ubuntu 24.04?
11. Why can `dig` and `curl` give different answers for the same name?
12. Why doesn't `/etc/security/limits.conf` change a systemd service's open-files limit?
13. Why doesn't `ufw deny 8080` protect a container published with `-p 8080:80`?
14. What does an unescaped `%` do in a crontab line?
15. What does `set -o pipefail` change, and name two failures `set -e` does *not* stop for.
16. When do you reach for `strace`, and when for `tcpdump`?

**Answers**

1. Your own shell opens `/etc/app.conf` for the redirection before `sudo` runs; use `echo x | sudo tee /etc/app.conf` (section 1).
2. The file has a POSIX ACL; read it with `getfacl` (section 2).
3. Without `-a`, `-G` replaces all supplementary groups, so the user silently loses `sudo` and the rest (section 3).
4. `D` is uninterruptible sleep, usually waiting on disk or NFS; signals are only acted on when the I/O returns. Check `wchan`, `iostat -xz 1` and hung NFS mounts (section 4).
5. 137 = 128 + 9: killed by SIGKILL, often the OOM killer or a memory limit. 143 = 128 + 15: stopped by SIGTERM, for example a normal `docker stop` (section 4).
6. `stop` ends it now; `disable` stops it starting at boot; `mask` makes it impossible to start at all, even as a dependency or from a package script (section 6).
7. `After=` only orders; it doesn't pull the target in. Add `Wants=network-online.target` as well (section 6).
8. `nofail` with a short `x-systemd.device-timeout=`, and `x-systemd.automount` for network filesystems (section 8).
9. Deleted files still held open by a process (`lsof +L1`), and files hidden underneath a mount point that `du` can't reach; ext4's reserved blocks also skew the numbers (section 8).
10. Ubuntu 22.10 and later use socket activation: `ssh.socket`, held by systemd (PID 1), owns the port and hands connections to `sshd` (section 6).
11. curl resolves through glibc `getaddrinfo`, which reads `nsswitch.conf` and `/etc/hosts`; dig asks the DNS server in `/etc/resolv.conf` directly (sections 9 and 17).
12. `limits.conf` is applied by PAM at login; services get their limits from `LimitNOFILE=` in the unit (section 15).
13. Docker DNATs published ports in `PREROUTING` and forwards them to the container, so UFW's `INPUT` rules never see those packets; bind to `127.0.0.1` or filter in `DOCKER-USER` (section 16).
14. It ends the command and sends the rest of the line to it as standard input; escape it as `\%` (section 11).
15. A pipeline fails if any part fails, not only the last. `set -e` doesn't stop for failures inside an `if` condition or an `&&`/`||` list, or hidden by `local x=$(cmd)` (section 12).
16. `strace` when a program misbehaves and you need to see which files and connections it attempts; `tcpdump` when you need to know whether packets leave and whether answers come back (section 17).

### Ready for the next stage

**Level:** [L1 · Junior] → [L2 · Mid]

You have finished this module when every line below is true:

| Check | Evidence |
|-------|----------|
| L0 exit test passed inside 30 minutes | Your notes with the four answers and their outputs |
| L1 exit test passed in under 5 minutes per port, for a unit, a socket and a container | The four-line answers |
| The health-report script runs from a timer with zero ShellCheck warnings | `systemctl list-timers health-report.timer`, ShellCheck output |
| Five SadServers easy scenarios solved inside their limits | Your SadServers history |
| `ss`, `lsof`, `strace` and `tcpdump` each used once on a real problem | Five-line incident notes |

Passing L0 means your Fresher foundations are done; passing L1 means you operate at
Junior level; reaching for the section 17 tools on real incidents is where Mid-level
work starts. The [career ladder](40-career-ladder.md) describes what changes in scope
and trust at each step.

---

## 19. Where to go next

### Next modules by career stage

| You are | Go next | Why |
|---------|---------|-----|
| Junior, L1 test passed | [Ports & inventory playbook](22-playbook-ports-inventory.md), then the [slow system playbook](23-playbook-slow-system.md) | Sections 4, 6, 8, 14 and 17 applied as full incident methods |
| Moving to Mid-level (L2) | [Learn: networking](28-learn-networking.md), [Web servers & proxies](29-learn-webservers-proxies.md), [Site down](25-playbook-site-down.md), [Network speed](24-playbook-network-speed.md) | The Ops Ladder says to put your real hours into L2: DNS, TLS and proxies are where your incidents live |
| Moving to Senior (L3) | [Learn: Docker](30-learn-docker.md), [Learn: Kubernetes](31-learn-kubernetes.md), [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), [Deployment patterns](35-deployment-patterns.md), [the Apache and Dokploy case](21-case-apache-443-dokploy.md) | Containers are sections 15–16 plus namespaces; Dokploy and your CKA track build on them |
| Senior or Lead (L4) | [Performance & observability](32-learn-performance-observability.md), [Security & DevSecOps](37-learn-security-devsecops.md), [Senior architecture](39-learn-senior-architecture.md) | Alerting on the health report, hardening at scale, design decisions |
| Any stage | [Roadmap](34-roadmap.md), [Career ladder](40-career-ladder.md), [Cheat sheet](19-cheatsheet.md) | Where you are, and what to do this week |

### Practice and reading

| Resource | Use it for | Level |
|----------|------------|-------|
| [Linux Upskill Challenge](https://linuxupskillchallenge.org/) | A month of daily lessons on a real server | L0 |
| [Linux Journey](https://labex.io/linuxjourney) | Short lessons with quizzes to fill gaps | L0 |
| KodeKloud [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) | Break and fix without touching your homelab | L0–L1 |
| KodeKloud [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) | One free task a day as a morning rep | L0–L2 |
| [SadServers](https://sadservers.com/scenarios) | Timed broken servers with an automatic check | L1–L2 |
| [Killercoda Linux scenarios](https://killercoda.com/linux) | Guided scenarios in a browser terminal | L1 |
| [How Linux Works, 3rd ed.](https://nostarch.com/howlinuxworks3) | The best single book for L1 and L2 | L1–L2 |
| [Arch Wiki: systemd](https://wiki.archlinux.org/title/Systemd) and [Journal](https://wiki.archlinux.org/title/Systemd/Journal) | Units, drop-ins and journal filters | L1 |
| [Spying on your programs with strace](https://wizardzines.com/zines/strace/), [Let's learn tcpdump!](https://wizardzines.com/zines/tcpdump/), [Linux debugging tools](https://wizardzines.com/zines/debugging/) | The L2 tools, one sitting each | L2 |
| [Some things about getaddrinfo that surprised me](https://jvns.ca/blog/2022/02/23/getaddrinfo-is-kind-of-weird/) | Why dig and curl disagree | L2 |
| [Bash Guide](https://mywiki.wooledge.org/BashGuide) and [ShellCheck](https://www.shellcheck.net/) | Correct, safe scripts | L0–L1 |
| [Brendan Gregg: Linux Performance](https://www.brendangregg.com/linuxperf.html) | Where "slow" goes after this module | L2–L4 |

### Keep the habit

The Ops Ladder's weekly rhythm keeps these skills alive after you finish the module:

| When | Habit |
|------|-------|
| Workday morning, 30 minutes | One SadServers scenario or one KodeKloud task; when time runs out, read the solution and write one line on what you missed |
| After any incident, even a small one | The five-line note: symptom, first wrong guess, deciding evidence, fix, what to check first next time |
| Weekend homelab block | One drill from your current level, then your CKA break-and-fix session |
| Sunday evening | One real postmortem from [k8s.af](https://k8s.af/) or [Dan Luu's list](https://github.com/danluu/post-mortems): name the layer that failed before you read the root cause |

Until your CKA exam, CKA sessions come first and this module runs on the 30-minute
morning rep alone.
