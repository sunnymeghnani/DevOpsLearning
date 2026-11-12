# Practice sites: tracks `linux` and `sre` (deep links)

Checked: 2026-11-09, 00:58–01:25 IST. Method: every URL below was opened with an HTTP GET (curl) and its page title, og:description or scenario info box was read. No logins, no sign-ups, no scenario started, nothing run.

"Verified" = page opened (HTTP 200) and the title and description match what the row says. "Snippet" = seen only in a list or sitemap, page not opened.

## Platform access rules (apply to every row of that platform)

| Platform (practice.json id) | Free tier / limits | Sign-up / card | Runs |
|---|---|---|---|
| SadServers (`sadservers`) | The scenario list has an Access field per scenario. **Public** = no registration. **Email** = free account. **Paid/Business** = Pro only (those were left out). Each VM is time-boxed (10–30+ min). | Public: none. Email: free e-mail account, no card | Browser terminal on a throwaway VM |
| iximiuz Labs (`iximiuz-labs`) | Only challenges *without* the "Premium Challenge" banner are listed. Most Linux challenges (create-systemd-service, find-process-using-port, install-packages, OOM/cgroup, ssh-tunnels) are **Premium** and left out. | Free account (no card) to start a playground | Browser terminal on a throwaway VM |
| Killercoda (`killercoda`) | Free plan, time-limited sessions. The scenarios below are **community-authored**, so quality varies. Some are in Portuguese (diario) or French (emelin). | Free account, no card | Browser terminal on a throwaway Ubuntu VM |

Level key: L0 Fresher, L1 Junior, L2 Mid, L3 Senior, L4 Lead/SRE, following the handbook's levels.

---

## linux track

### start-here (L0): has kodekloud-playgrounds and killercoda (generic)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| SadServers "Resumable Server" (Linux Upskill Challenge box) | https://sadservers.com/scenario/luc | Free Debian 11 VM with no task, to use as a lab with the Linux Upskill Challenge. No outbound internet. | SadServers, Email | L0 | verified (list info box) |
| SadServers "Linux Server Review": guided | https://sadservers.com/scenario/linux-server-review | Guided review of an unknown server: what it does, what runs, what listens | SadServers, Email | L0–L1 | verified |
| KubeDojo "Systematic Troubleshooting" | https://killercoda.com/kubedojo/scenario/linux-6.1-systematic-troubleshooting | Gather info, check services, read logs, write findings: the study loop | Killercoda | L0–L1 | verified |

### shell-fhs (L0): has bandit, pwn-college
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "Fix a Broken $PATH So Commands Work Again" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-2-2f97f6e6 | Repair a corrupted PATH ("command not found") | iximiuz, free challenge | L0 | verified |
| iximiuz "Persist a Custom Binary Directory in $PATH" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-3-45df473d | Make a PATH change permanent in the user's profile | iximiuz, free | L0 | verified |
| iximiuz "Audit the Shell Environment: Detect a Shadowed Command" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-5-78ed0ed6 | Find aliases and functions that shadow real commands (`type`, `command`) | iximiuz, free | L0–L1 | verified |
| iximiuz "Get Help: man, whatis, type, apropos" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-1-4e520bb5 | Answer questions using only the built-in help | iximiuz, free | L0 | verified |
| iximiuz "Broken Man Pages: whatis Returns Nothing" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-1-7a6c4e17 | Break-fix: rebuild the man database | iximiuz, free | L1 | verified |
| SadServers "Bata": Find in /proc | https://sadservers.com/scenario/bata | Search /proc/sys for a planted secret: learn the pseudo-filesystems | SadServers, Email | L0 | verified |
| SadServers "Nara": No ls on this system | https://sadservers.com/scenario/nara | Find a file when ls and find are missing (shell globbing, builtins) | SadServers, Email | L0–L1 | verified |
| Killercoda "Bash EscapeRoom" (56 rooms) | https://killercoda.com/codewizard/scenario/BashEscapeRoom | 56 progressive bash puzzles | Killercoda | L0 | verified |
| KubeDojo "Filesystem Hierarchy" | https://killercoda.com/kubedojo/scenario/linux-1.3-filesystem-hierarchy | FHS, finding files, disk and mount info | Killercoda | L0 | verified |
| The Dev Bench "A command points at nothing" | https://killercoda.com/barrymister/scenario/linux-broken-symlink | Break-fix: repoint a dangling symlink | Killercoda | L0 | verified |

### files-permissions (L0): has wizard-zines-questions, bandit, pwn-college
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| The Dev Bench "Permission denied running a script" | https://killercoda.com/barrymister/scenario/linux-permission-denied | Break-fix: make a deploy script executable | Killercoda | L0 | verified |
| Devopsify "Fix the Service That Permissions Broke" | https://killercoda.com/devopsify/course/en/fix-service-broken-by-permissions | Reproduce a permission-denied service failure as the service user, then fix it | Killercoda | L1 | verified |
| Alexis Carbillet "User, Group, and Permissions Troubleshooting" | https://killercoda.com/alexis-carbillet/course/Linux/User-Group-Permissions-Troubleshooting | Users, groups, ACLs, debugging access errors | Killercoda | L0–L1 | verified |
| French course "Les Inodes" | https://killercoda.com/emelin/course/cours05/inodes | Inodes, links, permissions (in French) | Killercoda | L0 | verified |

### users-sudo (L0): has kodekloud-engineer, linuxzoo
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| The Dev Bench "Sudo is broken" | https://killercoda.com/barrymister/scenario/linux-sudo-broken | Break-fix: a bad /etc/sudoers.d drop-in broke sudo for everyone (visudo -c) | Killercoda | L1 | verified |
| SadServers "Budapest": User Creation | https://sadservers.com/scenario/budapest | Bulk-create users with passwords from a file | SadServers, Email | L0–L1 | verified |
| iximiuz "RHCSA Prep: The sudo Command Isn't What It Seems" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-5-6fe249f9 | Break-fix: sudo runs something unexpected (PATH, alias or secure_path) | iximiuz, free | L1 | verified |
| SadServers "La Rinconada": Elevating privileges | https://sadservers.com/scenario/rinconada | Abuse a too-wide sudo rule, so you learn to write tight ones | SadServers, Email | L1–L2 | verified |
| SadServers "Annapurna": High privileges | https://sadservers.com/scenario/annapurna | Audit "admin should not have root" and find the escalation path | SadServers, Email | L2 | verified |
| ProLUG "Unusual user behavior: Attempted Sudo" | https://killercoda.com/het-tanis/course/Linux-Labs/202-attempted-sudo-access | Find failed sudo attempts in the logs | Killercoda | L1 | verified |
| The Dev Bench "Users & groups" | https://killercoda.com/barrymister/scenario/linux-learn-users | Create a user with home and shell, add to groups | Killercoda | L0 | verified |

### ssh-basics (L0): has bandit, kodekloud-engineer
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| EgyKode "SSH Hardening Without Locking Yourself Out" | https://killercoda.com/egykode/scenario/linux-ssh-hardening | Install a key sshd accepts, disable password and root login, and prove access before closing the last session | Killercoda | L1 | verified |
| iximiuz "Restore SSH Access to a Dual-Homed Server" | https://labs.iximiuz.com/challenges/networking-restore-emergency-ssh-access | VPN down: reach the box over another network with a routing trick | iximiuz, free | L2 | verified |
| The Dev Bench "SSH keys & client config" | https://killercoda.com/barrymister/scenario/linux-learn-ssh | Generate a key pair, install the public key, write a ~/.ssh/config alias | Killercoda | L0 | verified |
| ProLUG "Public and Private Keys with SSH" | https://killercoda.com/het-tanis/course/Linux-Labs/212-public-private-keys-with-ssh | Key pairs, authorized_keys | Killercoda | L0 | verified |
| Alexis Carbillet "SSH Hardening & Security Audit" | https://killercoda.com/alexis-carbillet/course/Linux/ssh-hardening | Harden sshd_config, key-only auth | Killercoda | L1 | verified |
| (Pro only, not counted) SadServers Nuuk and Pokhara (SSH troubles) | https://sadservers.com/scenario/nuuk | marked Paid in the list | n/a | n/a | verified as Paid |

### processes-signals (L0): has wizard-zines-questions, pwn-college
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "Kill a Stubborn Process with SIGKILL" | https://labs.iximiuz.com/challenges/kill-stubborn-process-with-sigkill-33e04027 | A process ignores SIGTERM, so you escalate the signal | iximiuz, free | L0 | verified |
| The Dev Bench "A process is pegging the CPU" | https://killercoda.com/barrymister/scenario/linux-runaway-process | Find and stop a 100%-CPU process | Killercoda | L0 | verified |
| The Dev Bench "Processes: priority & signals" | https://killercoda.com/barrymister/scenario/linux-learn-signals | renice, then stop cleanly with a signal | Killercoda | L0 | verified |
| SadServers "Oaxaca": Close an Open File | https://sadservers.com/scenario/oaxaca | Close a file a process holds open *without* killing it (fd tricks, gdb or /proc) | SadServers, Email | L1–L2 | verified |
| SadServers "Tokamachi": Named pipe | https://sadservers.com/scenario/tokamachi | Debug a process blocked on a FIFO | SadServers, Email | L1 | verified |
| SadServers "Vienna": The Vanishing Process | https://sadservers.com/scenario/vienna | systemctl says the agent is active but the process keeps "disappearing" | SadServers, Email | L1–L2 | verified |
| Alexis Carbillet "Process Management & Resource Limits" | https://killercoda.com/alexis-carbillet/course/Linux/Process-Management-Resource-Limits | Runaway processes, CPU and memory limits, safe termination | Killercoda | L1 | verified |

### packages-apt (L0): has only kodekloud-playgrounds (generic)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| SadServers "Dakar": The half-installed package | https://sadservers.com/scenario/dakar | Break-fix: an interrupted upgrade leaves a package half-configured and the service unhealthy (dpkg --configure -a, apt -f) | SadServers, Email | L1 | verified |
| The Dev Bench "Apt & dpkg" | https://killercoda.com/barrymister/scenario/linux-learn-packages | apt install, then query the dpkg database | Killercoda | L0 | verified |
| KubeDojo "Package and User Management" | https://killercoda.com/kubedojo/scenario/linux-8.3-package-user-management | apt, holding versions (apt-mark hold), maintenance | Killercoda | L0–L1 | verified |
| Shadil Rayyan "dpkg: Debian Package Tool" | https://killercoda.com/shadil-rayyan/course/linux_troubleshooting/dpkg | Low-level dpkg queries | Killercoda | L0 | verified |
| ProLUG "Update a Golden Image" | https://killercoda.com/het-tanis/course/Linux-Labs/203-updating-golden-image | Patch a base image | Killercoda | L1 | verified |

### text-tools (L0): has cmdchallenge, learnbyexample, command-line-murders
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "The SED command: Survival Guide" (10 tasks) | https://labs.iximiuz.com/challenges/sed-command-basics-1-b2c4c9e9 | Substitution, regex, line ranges, delete and insert, auto-checked | iximiuz, free | L0 | verified |
| SadServers "Saskatoon": counting IPs | https://sadservers.com/scenario/saskatoon | Most frequent IP in an access log | SadServers, Email | L0 | verified |
| SadServers "Lhasa": Easy Math | https://sadservers.com/scenario/lhasa | Average a column with awk | SadServers, Email | L0 | verified |
| KubeDojo "Log Analysis Techniques" | https://killercoda.com/kubedojo/scenario/linux-6.2-log-analysis | grep, awk and sed on Apache logs | Killercoda | L1 | verified |
| KubeDojo "Text Processing with awk, sed, pipelines" | https://killercoda.com/kubedojo/scenario/linux-7.2-text-processing | Field extraction, stream editing | Killercoda | L0 | verified |
| The Dev Bench "A counter script always prints 0" | https://killercoda.com/barrymister/scenario/bash-pipe-subshell | Pipe-subshell variable bug | Killercoda | L1 | verified |
| The Dev Bench "bad interpreter: No such file" (CRLF) | https://killercoda.com/barrymister/scenario/bash-crlf-endings | Windows line endings in a script | Killercoda | L0 | verified |
| iximiuz "Fix the Broken Script That Processes Special-Character Filenames" | https://labs.iximiuz.com/challenges/rhcsa-x200101-challenge-broken-6-0f81e7c4 | Quoting, IFS, filenames with spaces | iximiuz, free | L1 | verified |

### milestone-fresher (L0)
Use the shell-fhs, files-permissions and processes-signals finds above as a timed set. Extra: SadServers "Saint John" (no registration, see disk-full) as the exit test.

### systemd-units (L1): has systemd-by-example, sadservers (generic)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "Troubleshoot a Worker Service That Keeps Disappearing" | https://labs.iximiuz.com/challenges/linux-debug-vanishing-worker-service | A systemd worker starts, logs heartbeats, then dies over and over: find the cause and stabilise it | iximiuz, free | L1–L2 | verified |
| The Dev Bench "A systemd service won't start" | https://killercoda.com/barrymister/scenario/linux-service-wont-start | An enabled unit fails to start: read the journal and fix the unit | Killercoda | L1 | verified |
| Devopsify "Diagnose a Boot Failure from Environment and Unit" | https://killercoda.com/devopsify/course/en/boot-failure-from-environment-and-unit | Predict startup behaviour from the unit plus EnvironmentFile, then fix it | Killercoda | L1 | verified |
| SadServers "Valladolid": Cleaner not cleaning | https://sadservers.com/scenario/valladolid | A oneshot unit exits 0 but deletes nothing | SadServers, Email | L1 | verified |
| SadServers "Kampot": A New Port | https://sadservers.com/scenario/kampot | A supervisor-managed app can't change port, so you redirect it | SadServers, Email | L1–L2 | verified |
| Alexis Carbillet "Linux Systemd Service Debugging" | https://killercoda.com/alexis-carbillet/course/Linux/Systemd-Service-Debugging | Write, start and debug custom units | Killercoda | L1 | verified |
| KubeDojo "Processes and systemd Deep Dive" | https://killercoda.com/kubedojo/scenario/linux-1.2-processes-systemd | Unit types, dependencies, cgroups v2 | Killercoda | L1–L2 | verified |

### journald-logs (L1): has sadservers, sysadmin-simulator (generic)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| The Dev Bench "Journald & logrotate" | https://killercoda.com/barrymister/scenario/linux-learn-logs | Query the journal, write a logrotate config so a log can't fill the disk | Killercoda | L1 | verified |
| EgyKode "Processes, Services and Logs: Find It, Read It, Fix It" | https://killercoda.com/egykode/scenario/linux-processes-services-logs | Port to process, the service's own logs, break a service and diagnose it from the journal | Killercoda | L1 | verified |
| SadServers "Saint John": what is writing to this log file? | https://sadservers.com/scenario/saint-john | Find the process writing to /var/log/bad.log and stop it | SadServers, **Public, no registration** | L1 | verified |
| Diario "Syslog clássico e logrotate" (PT) | https://killercoda.com/diario/scenario/s03d03-syslog-logrotate | Does deleting app.log free the space? rsyslog and logrotate | Killercoda | L1 | verified |
| Diario "Dmesg: quando o kernel fala" (PT) | https://killercoda.com/diario/scenario/s03d04-dmesg-kernel | Kernel ring buffer when the app logged nothing | Killercoda | L1 | verified |

### disk-full (L1): has sadservers, sysadmin-simulator (generic)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| SadServers "Cordoba": df is lying (or is it du?) | https://sadservers.com/scenario/cordoba | Root filesystem under pressure but du shows nothing: deleted-but-open files | SadServers, Email | L1–L2 | verified |
| SadServers "Kihei": Surely Not Another Disk Space Scenario | https://sadservers.com/scenario/kihei | Make a program run without deleting its data file (space or inode tricks) | SadServers, Email | L2 | verified |
| SadServers "Manhattan": can't write data into database | https://sadservers.com/scenario/manhattan | Postgres can't insert, and the cause is disk | SadServers, **Public, no registration** | L1–L2 | verified |
| Devopsify "Fill, Find and Safely Clean Inode Pressure" | https://killercoda.com/devopsify/course/en/inode-pressure-safe-cleanup | Cause inode exhaustion in a bounded dir, find it, clean safely | Killercoda | L1 | verified |
| The Dev Bench "A folder is eating the disk" | https://killercoda.com/barrymister/scenario/linux-disk-space-hog | Find and reclaim a giant log | Killercoda | L0–L1 | verified |
| The Dev Bench "Volume out of space" (LVM) | https://killercoda.com/barrymister/scenario/linux-lvm-full | Extend a full LV live from free VG extents | Killercoda | L1–L2 | verified |

### time-scheduling (L1): has kodekloud-engineer, SadServers Cairo
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| The Dev Bench "A cron job never runs" | https://killercoda.com/barrymister/scenario/linux-cron-job-not-running | Break-fix: a wrong schedule | Killercoda | L1 | verified |
| SadServers "Alexandria": The Vanishing Backups | https://sadservers.com/scenario/alexandria | A backup cron job silently stopped 3 days ago | SadServers, Email | L1 | verified |
| SadServers "Amsterdam": Cron Hijack | https://sadservers.com/scenario/amsterdam | Root cron with a writable PATH entry (security side of cron) | SadServers, Email | L2 | verified |
| Alexis Carbillet "Cron Job Troubleshooting" | https://killercoda.com/alexis-carbillet/course/Linux/Cron-Job-Troubleshooting | Diagnose and fix broken cron jobs | Killercoda | L1 | verified |
| Diario "Cron e PATH" (PT) | https://killercoda.com/diario/scenario/s10d03-cron-path | Cron's minimal PATH, logging cron output | Killercoda | L1 | verified |
| The Dev Bench "Cron, at & systemd timers" | https://killercoda.com/barrymister/scenario/linux-learn-scheduling | Schedule with cron, at and timers | Killercoda | L0–L1 | verified |
| Shadil Rayyan "timedatectl" | https://killercoda.com/shadil-rayyan/course/linux_troubleshooting/timedatectl | Time, timezone, NTP status | Killercoda | L0 | verified |

### kernel-boot (L1): has only SadServers Cork
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "Make a Filesystem Mount Survive a Reboot" | https://labs.iximiuz.com/challenges/storage-persistent-mount | fstab vs systemd mount units, tested with a real reboot | iximiuz, free | L1 | verified |
| The Dev Bench "Filesystem won't mount" (bad fstab) | https://killercoda.com/barrymister/scenario/linux-fstab-broken | `mount -a` fails on a bad /etc/fstab line | Killercoda | L1 | verified |
| The Dev Bench "Boot & targets" | https://killercoda.com/barrymister/scenario/linux-learn-boot | Default target, this boot's journal, set multi-user | Killercoda | L1 | verified |
| ProLUG "Server Startup Process" | https://killercoda.com/het-tanis/course/Linux-Labs/107-server-startup-process | Boot sequence walk-through | Killercoda | L1 | verified |
| Shadil Rayyan "systemd-analyze: Boot Analysis" | https://killercoda.com/shadil-rayyan/course/linux_troubleshooting/systemd-analyze | Slow-boot blame and critical-chain | Killercoda | L1 | verified |
| SadServers "Genova": cgroups problem | https://sadservers.com/scenario/genova | A memory-hungry batch job starves the API: cgroup limits | SadServers, Email | L2 | verified |
| SadServers "Kampala": Strange Script Error | https://sadservers.com/scenario/kampala | `cannot execute: required file not found` (interpreter, CRLF) | SadServers, Email | L1 | verified |
| iximiuz storage set (free): Simple mount, Format ext4, GPT table, Partition ext4+btrfs, Bind mount, Provision-drive script | https://labs.iximiuz.com/challenges/storage-simple-mount · /storage-simple-format · /storage-simple-partition-table · /storage-partition-drive · /storage-bind-mount · /storage-provision-drive-script | Block devices to filesystem to mount to persist | iximiuz, free | L0–L2 | verified (all 6) |

### port-ownership (L1): has SadServers Bergen, kodekloud-playgrounds
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| iximiuz "Find the Listening Port" | https://labs.iximiuz.com/challenges/networking-find-listening-port-24f244e3 | A mystery service: which TCP port? | iximiuz, free | L1 | verified |
| SadServers "Porto": Port audit without net tools | https://sadservers.com/scenario/porto | ss, netstat and nmap removed, so probe ports via /proc and bash /dev/tcp | SadServers, Email | L1–L2 | verified |
| SadServers "Tokyo": can't serve web file | https://sadservers.com/scenario/tokyo | curl 127.0.0.1:80 returns nothing | SadServers, Email | L1 | verified |
| ProLUG "Let's do Linux Troubleshooting: lsof" | https://killercoda.com/het-tanis/course/Linux-Labs/400-troubleshoot-with-lsof | lsof for ports and open files | Killercoda | L1 | verified |
| Diario "Portas e Sockets" (PT) | https://killercoda.com/diario/scenario/s13d04-portas-sockets-ss | ss, "refused" vs "timeout" | Killercoda | L1 | verified |
| iximiuz "Protect an Unintentionally Exposed Server Port" | https://labs.iximiuz.com/challenges/linux-protect-ports | Firewall a port while keeping it reachable locally | iximiuz, free | L1–L2 | verified |
| iximiuz "Preserve Firewall Rules Across Reboots" (nftables / iptables) | https://labs.iximiuz.com/challenges/linux-preserve-nftables-rules · https://labs.iximiuz.com/challenges/linux-preserve-iptables-rules | Rules vanish after reboot | iximiuz, free | L1–L2 | verified |
| Alexis Carbillet "Network Service Troubleshooting" | https://killercoda.com/alexis-carbillet/course/Linux/Network-Service-Troubleshooting | Open ports, listening processes, reachability | Killercoda | L1 | verified |

### incident-note (L1): has danluu-post-mortems, the-void
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Devopsify "Rewrite a Broken Runbook So Someone Else Can Run It" | https://killercoda.com/devopsify/course/en/rewrite-runbook-handover-run | Rewrite a runbook to the "stranger standard" with stop conditions, then hand it over | Killercoda | L1–L2 | verified |
| KubeDojo "Systematic Troubleshooting" (ends with documenting findings) | https://killercoda.com/kubedojo/scenario/linux-6.1-systematic-troubleshooting | Write up what you found | Killercoda | L1 | verified |

### windows-macos (L1): has under-the-wire
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Mentorchita "Workshop PowerShell on Linux" | https://killercoda.com/mentorchita/scenario/ws_powershell | First PowerShell steps (pwsh on Linux) | Killercoda | L0–L1 | verified (thin, beginner only) |
| (macOS is out of scope here; the parallel researcher covers it) | | | | | |

### milestone-junior (L1)
Suggested free exit set: SadServers Saint John (public), Cordoba, Dakar, Valladolid, Tokyo + iximiuz vanishing-worker-service + Dev Bench fstab-broken.

### memory-oom (L2): has iximiuz USE playground, sadservers
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| SadServers "Genova": cgroups problem | https://sadservers.com/scenario/genova | A batch job's RAM spike kills the API, so you contain it with cgroups or systemd limits | SadServers, Email | L2 | verified |
| SadServers "Philadelphia": htop metrics disagree | https://sadservers.com/scenario/philadelphia | Load and uptime in the dashboard are wrong while htop is right | SadServers, Email | L2 | verified |
| KubeDojo "Memory Management Deep Dive" | https://killercoda.com/kubedojo/scenario/linux-5.3-memory-management | Memory stats, page cache, OOM killer | Killercoda | L2 | verified |
| Shadil Rayyan "oom_score_adj: OOM Killer Tuning" | https://killercoda.com/shadil-rayyan/course/linux_performance_advanced/oom_score_adj | Choose which process the OOM killer picks | Killercoda | L2 | verified |
| The Dev Bench "Swap space" | https://killercoda.com/barrymister/scenario/linux-learn-swap | Create and enable a swap file | Killercoda | L1 | verified |
| SadServers "Bizerte": The Slow Application | https://sadservers.com/scenario/bizerte | Every request takes over 5 s and the redis cache isn't used | SadServers, Email | L2 | verified |

### disk-io (L2): has only iximiuz USE playground
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| KubeDojo "I/O Performance Analysis" | https://killercoda.com/kubedojo/scenario/linux-5.4-io-performance | iostat, I/O schedulers, dd throughput | Killercoda | L2 | verified |
| KubeDojo "USE Method for Performance Analysis" | https://killercoda.com/kubedojo/scenario/linux-5.1-use-method | Utilisation, saturation and errors across CPU, memory, disk and network | Killercoda | L2 | verified |
| Shadil Rayyan "iostat: Device I/O Statistics" | https://killercoda.com/shadil-rayyan/course/linux_performance_essential/iostat | IOPS, queue depth, latency: is storage the bottleneck? | Killercoda | L2 | verified |
| KubeDojo "Process Debugging with strace, lsof, ltrace" | https://killercoda.com/kubedojo/scenario/linux-6.3-process-debugging | See what a stuck process is waiting on | Killercoda | L2 | verified |
| Note | | No free *break-fix* D-state scenario found; these are guided labs. | | | |

### linux-problems (L2): has systemd-by-example, sadservers, linuxzoo
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| The Dev Bench break-fix series (cron, disk hog, runaway, fstab, permission, sudo, LVM, service won't start, DNS) | https://killercoda.com/barrymister | 9+ short Linux break-fix labs with a checker | Killercoda | L1–L2 | verified (each URL above) |
| SadServers "Dakar", "Cordoba", "Kampala", "Vienna" | see rows above | apt, disk, exec and systemd problems | SadServers, Email | L1–L2 | verified |
| iximiuz vanishing-worker-service and storage-persistent-mount | see rows above | systemd and limits, mounts | iximiuz, free | L1–L2 | verified |

### milestone-mid (L2)
Exit set: SadServers Kihei, Oaxaca, Genova, Philadelphia, Porto + iximiuz networking-restore-emergency-ssh-access.

### milestone-senior (L3), oss-toolbox (L3)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| SadServers "Nairn": Phantom Gitea Deploy | https://sadservers.com/scenario/nairn | A Gitea Actions pipeline reports success but the deploy didn't happen | SadServers, Email | L3 | verified (list) |
| SadServers "Kyoto": The Gion ticket API will not start | https://sadservers.com/scenario/kyoto | Recover after "last night's change" using a handover note and manifests | SadServers, Email | L3 | verified (list) |
| SadServers "Verona": Apache Portal Won't Open | https://sadservers.com/scenario/verona | An Apache site migrated to a new host: DocumentRoot and a legacy /reports redirect broken (fits the Apache to Dokploy story) | SadServers, Email | L2–L3 | verified (list) |
| Uptime Kuma public demo (oss-toolbox) | https://demo.kuma.pet/start-demo | A temporary Uptime Kuma instance per visitor: add monitors, status pages, notifications | No sign-up; timed demo that ends | L1–L3 | verified (page opened, "Start Demo" timer) |
| Portainer demo lab (oss-toolbox) | https://killercoda.com/codewizard/scenario/Portainer | Portainer with live containers | Killercoda | L1–L2 | verified |
| ProLUG "Grafana monitoring of logs with Loki and Promtail" | https://killercoda.com/het-tanis/course/Linux-Labs/102-monitoring-linux-logs | Stand up a Loki and Grafana log stack | Killercoda | L2–L3 | verified |
| ProLUG "Telegraf + InfluxDB + Grafana" | https://killercoda.com/het-tanis/course/Linux-Labs/104-monitoring-linux-Influx-Grafana | Metrics stack | Killercoda | L2 | verified |
| ProLUG "Fail2ban with Monitoring" | https://killercoda.com/het-tanis/course/Linux-Labs/109-fail2ban-with-log-monitoring | fail2ban plus log monitoring | Killercoda | L2 | verified |
| NetBox public demo (oss-toolbox, read-mostly) | https://demo.netbox.dev/ | Browse a populated IPAM/DCIM. Login page shown; credentials not tested | Vendor demo (login) | L2 | verified (login page only) |
| Gitea demo | https://demo.gitea.com/ | Look at Gitea's UI. Creating repos needs an account on the demo | Vendor demo | L1 | verified (home page) |

---

## sre track

### outage-basics (L2): has wheel-of-misfortune, sysadmin-simulator, incident-challenge
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Josue Cross "SRE On-Call Triage: API Error Rate Alert" | https://killercoda.com/josuecross/scenario/sre-api-error-rate-triage | First response: synthetic alert, metrics, logs, **stakeholder-update prompts** | Killercoda | L2 | verified |
| Josue Cross "Queue Backlog / Worker Saturation Triage" | https://killercoda.com/josuecross/scenario/queue-backlog-worker-saturation | Growing queue: curl, docker logs, grep/awk, mitigation, update notes | Killercoda | L2 | verified |
| Josue Cross "Deployment Mismatch / Rollback Decision Triage" | https://killercoda.com/josuecross/scenario/deployment-mismatch-rollback | Roll back or fix forward, using health, version, config and recovery evidence | Killercoda | L2–L3 | verified |
| Devopsify "Find the Error Source from Logs and Simple Metrics" | https://killercoda.com/devopsify/course/en/find-error-source-logs-metrics | From a metric spike to its scope to the log source | Killercoda | L2 | verified |

### incident-command (L4): has pagerduty training, wheel-of-misfortune, devops-daily-games
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Crunchyblue "SRE Incident Triage & SLO Burn-Rate Alerting" | https://killercoda.com/crunchyblue/scenario/sre-incident-triage-slo | Investigate a production incident, fix observability gaps, write SLO burn-rate alerts, automate the fix (Kubernetes) | Killercoda | L3–L4 | verified |
| Josue Cross SRE Incident Practice Labs (3 labs above) | https://killercoda.com/josuecross/scenario/sre-api-error-rate-triage | Run a game day with an IC and a scribe on them | Killercoda | L3–L4 | verified |

### postmortems (L4): has danluu-post-mortems, the-void
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Sandeep "Post Incident Practices" (DevOps Dojo Yellow Belt) | https://killercoda.com/sandeep3004/course/yellow-belt-devops-dojo/post-incident-practices | Safety culture, blameless postmortem, incident code of conduct | Killercoda | L3–L4 | verified (guided, light on hands-on) |
| Practice tip | | Write a blameless postmortem after each Josue Cross / SadServers run (Kyoto ships a HANDOVER.txt) | | | |

### change-management (L4): had 0 sites
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Devopsify "Run Go/No-go and Roll Back a Bad New Version" | https://killercoda.com/devopsify/course/en/go-nogo-rollback-bad-release | Go/no-go checklist with owners, then roll back a bad version | Killercoda | L3–L4 | verified |
| Devopsify "Rewrite a Broken Runbook So Someone Else Can Run It" | https://killercoda.com/devopsify/course/en/rewrite-runbook-handover-run | Runbook with stop conditions, handover | Killercoda | L3 | verified |
| Devopsify "Revert a Published Mistake Without Breaking History" | https://killercoda.com/devopsify/course/en/revert-published-mistake | Safe revert of a change that is already public (git revert, not a force-push) | Killercoda | L2 | verified |
| Josue Cross "Deployment Mismatch / Rollback Decision Triage" | https://killercoda.com/josuecross/scenario/deployment-mismatch-rollback | Rollback vs fix-forward decision | Killercoda | L3 | verified |
| EgyKode "Helm Upgrades, Rollbacks and Release Strategy" | https://killercoda.com/egykode/scenario/helm-upgrade-rollback | Ship, break, auto-rollback, roll back to a named revision | Killercoda | L3 | verified |
| The Dev Bench "Someone changed it outside Terraform" | https://killercoda.com/barrymister/scenario/terraform-drift | Detect and reconcile an unmanaged change (drift) | Killercoda | L2–L3 | verified |
| The Dev Bench "The playbook reports changed every single run" | https://killercoda.com/barrymister/scenario/ansible-not-idempotent | Make a change idempotent | Killercoda | L2 | verified |
| iximiuz "Safe node drain with a disruption budget" | https://labs.iximiuz.com/challenges/safe-node-drain-with-a-disruption-budget-8fc8f25e | Plan maintenance without dropping capacity (PDB) | iximiuz, free | L3 | verified (listed free; description read) |
| Diario "Nftables: listar, backup, rollback" (PT) | https://killercoda.com/diario/scenario/s15d02-nftables-basico-rollback | Back up the ruleset before a firewall change, and roll back | Killercoda | L2 | verified |

### availability-dr (L4): has sdpd, server-survival, system-design-sim (all simulators)
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| EgyKode "Chaos Experiments: Measure the Recovery You Assume" | https://killercoda.com/egykode/scenario/k8s-chaos-experiments | Steady traffic, kill pods, time recovery, find the failure replicas don't survive, write the hypothesis | Killercoda | L3–L4 | verified |
| CirrusNorth "Chaos Engineering Quick Demo" (Chaos Mesh) | https://killercoda.com/parker-smits/course/Resilient_Architecture/d3-lab7-chaos-engineering | Run a safe Chaos Mesh experiment and check automated recovery | Killercoda | L3 | verified |
| Devopsify "Verify Health Checks, SIGTERM Handling and Resource Limits" | https://killercoda.com/devopsify/course/en/healthcheck-sigterm-limits | Readiness on a real dependency, graceful shutdown, limits | Killercoda | L2–L3 | verified |
| (Backups and DR restore drills are left to the parallel researcher) | | | | | |

### milestone-lead (L4)
Game-day pack: Crunchyblue SLO lab + Josue Cross trio + EgyKode chaos lab, each run with a rotating IC and a postmortem.

### devops-day-to-day (L1): has kodekloud-engineer, sysadmin-simulator
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| EgyKode "Linux Server Administration: Users, Permissions, Services" | https://killercoda.com/egykode/scenario/linux-users-permissions-services | A ticket-like task: deploy account, permissions that survive, enable a service on boot | Killercoda | L1 | verified |
| SadServers "Budapest" (bulk user creation request) | https://sadservers.com/scenario/budapest | A typical request ticket | SadServers, Email | L1 | verified |
| SadServers "Yokohama" | https://sadservers.com/scenario/yokohama | Shared project permissions | **Paid**, not counted | | verified as Paid |

### learn-from-tickets (L2): has danluu-post-mortems
| Find | URL | What you practise | Platform | Level | Verified |
|---|---|---|---|---|---|
| Devopsify EN course (40 short ticket-sized labs: inode pressure, 502/503 proxy, permissions, TLS with a test CA, setup script that is safe to run twice…) | https://killercoda.com/devopsify/course/en | Turn each lab into a "ticket", then a note, then a runbook | Killercoda | L1–L2 | verified (7 labs opened; course list from sitemap) |

---

## Rejected or not counted
- Paid (SadServers Pro): Nuuk, Pokhara, Yokohama, Kortenberg, Apia, Zaragoza, Montevideo, Modena, Stockholm, Hangzhou, Spa, Karakorum, Madrid, Sapporo, Cadiz, Dublin, Marseille, Bekasi, Hanoi, Toulon, Bermuda, Warsaw, Ravenna.
- Premium iximiuz: linux-create-systemd-service, linux-find-process-using-port, linux-find-port-used-by-service, linux-install-packages-debian-ubuntu, linux-missing-shared-library, linux-strace-failing-daemon, linux-resolve-port-conflict, kill-process-group-on-oom-event, limit-cpu-and-memory-of-linux-process, ssh-local/remote-port-forwarding, ssh-socks-proxy, ssh-jump-host-*, systemd-socket-activate-*.
- try.gitea.io: did not respond (connection failed).
- Caveat: curl sometimes returned a stale `<title>` for iximiuz pages. Each row was checked against the page's H1 and og:description instead.
