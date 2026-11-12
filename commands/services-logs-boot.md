# systemd, logs, time, kernel & boot

systemd starts and supervises every service, journald keeps what they print, and the kernel, the clock and the boot chain sit underneath. Work in that order: what state is the unit in (`systemctl status`, `systemctl --failed`), why (`journalctl`), how is it configured (`systemctl cat`, `show`), then change it safely (`edit`, `daemon-reload`, `restart`). When the service itself is fine, go down a layer: kernel messages, tunables, time and boot.

| If you would reach for | Prefer | Because |
|---|---|---|
| `systemctl status app`, and stop there | `systemctl status app`, then `journalctl -u app -b` | status shows only the last 10 log lines |
| `grep app /var/log/syslog` | `journalctl -u app --since "30 min ago" -p warning` | exact filters by unit, boot, time and priority, across rotations |
| `systemctl restart app` after editing its unit | `systemctl daemon-reload`, then `restart` | without the reload systemd restarts the old definition |
| `vi /lib/systemd/system/app.service` | `systemctl edit app` | a drop-in survives package upgrades and shows in `systemctl cat` |
| `systemctl disable` to keep a service off | `systemctl mask --now` | a disabled unit can still be started by hand, a dependency or a socket |
| `systemd-analyze blame` | `systemd-analyze critical-chain` | blame sorts durations; critical-chain shows what boot actually waited for |
| `date` | `timedatectl`, `chronyc tracking` | they show whether the clock is synchronised and how far off it is |
| `dmesg` | `dmesg -T --level=err,warn`, `journalctl -k -b -1` | readable times, problems only, and the boot before the crash |

### systemctl status — what state is this unit in, and how did it last exit?
Match: systemctl status, service
Instead of: ps aux | grep nginx, service nginx status
Safety: read-only

**In one line:** `systemctl status` puts a unit's whole state on one screen: the file that defines it, whether it starts at boot, whether it runs, crash-loops or failed, how its last process exited, every process it owns and its last 10 journal lines.

**Read the command:** `systemctl status apache2 --no-pager -l`

| Part | Meaning |
|---|---|
| `apache2` | the unit; `.service` is assumed when you give no suffix |
| `--no-pager` | print and exit instead of opening `less` (scripts, tickets) |
| `-l` | `--full`: do not shorten long lines with `…` |
| `-n 50` | 50 journal lines instead of 10; `-n 0` for none |
| `status 1234` | given a PID, show the unit that owns that process |
| `service nginx status` | the SysV-era syntax; on a systemd host it calls `systemctl status` |

**What the output tells you:**

```
● app.service - My App
     Loaded: loaded (/etc/systemd/system/app.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/app.service.d
             └─override.conf
     Active: activating (auto-restart) (Result: exit-code) since Sat 2026-10-03 10:02:11 UTC; 2s ago
    Process: 51022 ExecStart=/usr/bin/app (code=exited, status=1/FAILURE)
```

`Loaded` names the file in use and the boot state; `Drop-In` lists overrides. `Active` is `active (running)`, `inactive (dead)`, `failed`, or `activating (auto-restart)`: a crash loop. `status=` decodes the exit: `1/FAILURE` is the app's own error, `203/EXEC` a missing or non-executable binary, `217/USER` a missing `User=`, `200/CHDIR` a missing `WorkingDirectory=`.

**Why it is effective:** one command answers "is it running, since when, defined where, overridden how, and how did it last die", without knowing the process name or where the app logs.

**Compared with `ps aux | grep nginx`:** ps proves a process exists and shows its arguments. It cannot show a crash loop between two restarts, an exit code, the unit file, or whether the service returns after a reboot.

**Trap:** the 10 log lines can be older than the latest restart, and are cut short without `-l`. `active (running)` only means the main process is alive (with `Type=simple`, from the moment it was forked): it is not a health check. A `Warning: ... changed on disk` line means systemd still runs the old unit definition.

**Next step:** exit code or crash loop → `journalctl -u UNIT -b -n 50`. `203`, `217` or `200` → `systemctl cat UNIT` and fix the path or user. Running but not answering → `ss -ltnp`, `curl -v`. "changed on disk" → `systemctl daemon-reload`.

### journalctl — filter the journal by unit, boot, time and priority
Match: journalctl
Instead of: cat /var/log/syslog, grep app /var/log/syslog, tail -f /var/log/syslog
Safety: read-only · --vacuum-* deletes archived journal files · other users' and system logs need sudo or the adm / systemd-journal group

**In one line:** journald stores every line with fields (unit, PID, boot, priority, time), so `journalctl` filters on facts instead of text, merges services into one timeline, and holds the output of services that write no log file.

**Read the command:** `journalctl -u docker --since '30 min ago' -p warning --no-pager`

| Part | Meaning |
|---|---|
| `-u docker` | this unit, plus systemd's lines about it; repeat `-u` for one merged timeline |
| `--since '30 min ago'` | window start: also `today`, `-1h`, `"2026-10-03 02:00"`; end with `--until` |
| `-p warning` | warning **and worse** (emerg 0 … debug 7) |
| `--no-pager` | print instead of opening `less` |
| `-b` · `-b -1` | this boot · the previous boot (needs a persistent journal) |
| `-f` · `-n 50` · `-e` | follow live · last 50 lines · jump to the end |
| `-k` · `-x` · `-g 'regex'` | kernel messages · explanation texts · grep the messages |
| `-o short-iso` | format; also `short-precise`, `json`, `verbose` (all fields), `cat` |

**What the output tells you:**

```
Oct 03 09:12:41 web01 systemd[1]: docker.service: Failed with result 'exit-code'.
Oct 03 09:12:41 web01 systemd[1]: Failed to start docker.service - Docker Application Container Engine.
```

Each line: time, host, identifier[PID], message. With `-p warning` you see systemd's verdict but not the daemon's own explanation: a service's plain stdout/stderr is stored as `info` unless the program marks it, so read the window again without `-p`.

**Why it is effective:** exact filters instead of text matches, one timeline across services (`-u apache2 -u 'docker*'`), and the logs of the boot before a crash, without knowing where each program writes.

**Compared with `grep app /var/log/syslog`:** on Ubuntu rsyslog copies the same stream into `/var/log/syslog`, and grep is fine for a quick text search. It cannot filter by boot, unit or priority, rotation spreads history over `.1` and `.gz` files, and hosts without rsyslog have no such file.

**Trap:** `-- No entries --` usually means a wrong unit name (`ssh` vs `sshd`), a time-zone mismatch in `--since`, a volatile journal (no earlier boots) or no permission ("not seeing messages from other users"). `-k` implies the current boot: add `-b -1` for the boot that crashed. `--vacuum-size=` removes only archived files, never the active one.

**Next step:** error found → `systemctl status UNIT` (exit code), then the app's own log. No earlier boots → create `/var/log/journal`. Journal too big → `--disk-usage`, then `SystemMaxUse=`.

### systemctl list-units / list-unit-files — what is loaded, running or failed on this host?
Match: systemctl list-units, systemctl list-unit-files
Instead of: ps aux, service --status-all
Safety: read-only

**In one line:** `list-units` lists the units systemd has loaded now, with their load, active and sub state; `list-unit-files` lists the installed unit files with their boot state (`enabled`, `disabled`, `static`, `masked`).

**Read the command:** `systemctl list-units --type=service --state=running --no-pager`

| Part | Meaning |
|---|---|
| `--type=service` | only services (`mount`, `socket`, `timer` work too) |
| `--state=running` | filter on a state: `running`, `exited`, `failed`, `active`… |
| `--failed` | short for `--state=failed` |
| `--all` | also loaded units that are inactive |
| `--no-pager` | print without `less` |
| `list-unit-files --state=enabled` | everything set to start at boot, running or not |

**What the output tells you:** without `--state` you see all kinds:

```
  UNIT               LOAD   ACTIVE SUB     DESCRIPTION
  apache2.service    loaded active running The Apache HTTP Server
  ufw.service        loaded active exited  Uncomplicated firewall
● lab-fail.service   loaded failed failed  Lab: failing unit
```

`LOAD` says whether the unit file was read (`not-found` and `bad-setting` are problems, `masked` is deliberate). `ACTIVE` is the general state, `SUB` the detail: `running` has a process, `exited` is a oneshot that ran fine and stays active (`RemainAfterExit=yes`), `failed` needs you.

**Why it is effective:** it is the inventory of what this server really runs, including units without any process (finished oneshots, failed units, mounts) that a process list cannot show.

**Compared with `ps aux`:** ps shows processes, but not which unit owns them, nothing for units that failed (no process left), and nothing about the next boot. `service --status-all` covers only init.d scripts.

**Trap:** `list-units` shows only **loaded** units: an installed unit nothing has started or referenced is missing (use `list-unit-files`). `--state=running` hides successful oneshots and failed units. `enabled` does not mean running, `disabled` does not mean stopped. User services need `systemctl --user list-units`.

**Next step:** failed unit → `systemctl status UNIT`, `journalctl -u UNIT -b`. Unknown service running → `systemctl cat UNIT` and the CGroup in `status`. Enabled but not running → `systemctl status UNIT` for why it did not start.

### systemctl — failed units, jobs, targets and user units
Match: systemctl
Instead of: —
Safety: read-only for --failed, list-jobs, get-default · changes state: set-default, default, kill, and --user start/stop · system units need root to change

**In one line:** the bare command and its rarer verbs: `systemctl --failed` is the one-line health check of a host, `list-jobs` shows what boot or a start is waiting for, and `--user` talks to your per-user systemd instead of the system one.

**Read the command:** `systemctl --failed --no-legend`

| Part | Meaning |
|---|---|
| `--failed` | short for `list-units --failed`: every unit in failed state |
| `--no-legend` | no header or footer: one line per unit, easy to count |
| `--user` | your user's systemd (`~/.config/systemd/user`, rootless Docker/Podman), e.g. `systemctl --user daemon-reload` |
| `list-jobs` | start/stop jobs queued or running now ("A start job is running for…") |
| `get-default` · `set-default multi-user.target` | which target the host boots into · change it |
| `default` | from rescue or emergency mode, continue to the normal target |
| `kill -s KILL reports` | send a signal to all processes of the unit, e.g. to test `Restart=` |

**What the output tells you:**

```
● data.mount        loaded failed failed /data
● lab-fail.service  loaded failed failed Lab: failing unit
```

Each line is a unit that failed and was not reset. No output means nothing is in failed state right now.

**Why it is effective:** one short command finds failed mounts, timer jobs and oneshot scripts that no process list shows: a good first command on any server and a good morning check.

**Trap:** a unit in a restart loop is `activating`, not `failed`, so it is missing here until it hits its start limit. Units cleared with `reset-failed` vanish too. User units appear only with `--user`, and `systemctl --user` run through `sudo -u` or `su` usually fails with "Failed to connect to bus": log in as that user over SSH instead.

**Next step:** a failed unit → `systemctl status UNIT`, `journalctl -u UNIT -b`. A failed `.mount` → `/etc/fstab` and `findmnt --verify`. Boot hangs → `systemctl list-jobs`, then `systemd-analyze critical-chain`.

### systemctl is-active / is-enabled / is-failed — one-word answers for scripts
Match: systemctl is-active, systemctl is-enabled, systemctl is-failed
Instead of: systemctl status | grep running, pgrep nginx
Safety: read-only

**In one line:** each prints one word per unit (`active`, `enabled`, `failed`…) and sets the exit code, so scripts, health checks and Ansible tasks can test a unit without parsing `status`.

**Read the command:** `systemctl is-active kubelet containerd`

| Part | Meaning |
|---|---|
| `is-active` | prints `active`, `activating`, `inactive`, `failed`… for each unit |
| `kubelet containerd` | several units: one line each, in order |
| `is-enabled` | prints `enabled`, `disabled`, `static`, `masked`, `alias`… |
| `is-failed` | exit code 0 when the unit is in `failed` state |
| `-q` | quiet: print nothing, only set the exit code (`if systemctl -q is-active nginx; then`) |
| `2>/dev/null` | hide the error for a unit that does not exist |

**What the output tells you:**

```
activating
active
```

`kubelet` is `activating`: it is in a restart loop, not up. `containerd` is `active`. `inactive` means cleanly stopped. In `is-enabled`, `static` means the unit has no `[Install]` section, so something else (a timer, a socket, another unit) starts it.

**Why it is effective:** a fixed word and exit code are safer in automation than grepping the human-readable `status` output, whose layout changes between versions.

**Compared with `pgrep nginx`:** pgrep finds a process by name, including a stray copy started by hand outside systemd; it says nothing about the unit's state or its boot setting.

**Trap:** with several units the exit code is 0 if **any** of them matches, so `systemctl is-active kubelet containerd && echo OK` prints OK here although kubelet is down: test one unit per call. `active` means the main process lives, not that its port answers.

**Next step:** `activating` or `failed` → `systemctl status UNIT`, `journalctl -u UNIT -b -n 50`. `disabled` but must survive a reboot → `systemctl enable UNIT`. Real health check → follow the state test with `curl -fsS` or `ss -ltn`.

### systemctl cat / systemd-delta — what is this unit really configured to do?
Match: systemctl cat, systemd-delta
Instead of: cat /lib/systemd/system/nginx.service
Safety: read-only

**In one line:** `systemctl cat` prints the unit file systemd uses plus every drop-in, each headed by its path, in the order they apply; `systemd-delta` lists every unit (and other systemd config) on the host that a local file overrides or extends.

**Read the command:** `systemctl cat gunicorn-app.service`

| Part | Meaning |
|---|---|
| `cat` | the winning unit file and all its drop-ins, as one text |
| `gunicorn-app.service` | the unit |
| `# /path` lines | where each block comes from; later blocks override earlier ones |
| `systemd-delta --type=extended,overridden` | host-wide: units with drop-ins (`extended`) or replaced by a full copy in `/etc` (`overridden`) |
| `--no-pager` | print without `less` |

**What the output tells you:**

```
# /etc/systemd/system/gunicorn-app.service
[Service]
ExecStart=/srv/app/venv/bin/gunicorn -b 127.0.0.1:8000 app:app

# /etc/systemd/system/gunicorn-app.service.d/override.conf
[Service]
Environment=WORKERS=4
```

The main file comes first, the drop-in after it. `systemd-delta` prints one line per finding, such as `[EXTENDED] /usr/lib/systemd/system/nginx.service → /etc/systemd/system/nginx.service.d/override.conf`.

**Why it is effective:** "my change has no effect" and "who changed this service?" are answered on one screen: every file that contributes, including an old full copy in `/etc` that silently beats the package version.

**Compared with `cat /lib/systemd/system/nginx.service`:** that shows only the package file, which may not be the one in use, and none of the drop-ins.

**Trap:** cat shows the files **on disk**; if someone edited them without `daemon-reload`, systemd still runs the old version (`status` warns "changed on disk"). It shows no defaults: `systemctl show` gives the resulting values. A second `ExecStart=` in a drop-in is valid only after an empty `ExecStart=` line that clears the first.

**Next step:** an unintended full copy in `/etc` → `systemctl revert UNIT`. Effective value in doubt → `systemctl show -p SETTING UNIT`. Unfamiliar server → `systemd-delta --type=extended,overridden` lists every local customisation.

### systemctl show — the exact effective value of any unit setting
Match: systemctl show
Instead of: grep on the unit file, systemctl status
Safety: read-only

**In one line:** `show` prints systemd's own view of a unit as `Key=value` properties, after all drop-ins and defaults, including runtime values such as the main PID, the restart counter and timestamps.

**Read the command:** `systemctl show apache2 -p ActiveEnterTimestamp -p NRestarts -p UnitFileState -p FragmentPath`

| Part | Meaning |
|---|---|
| `-p NAME` | only this property; repeat `-p` or join with commas (`-p Environment,ExecStart`) |
| `ActiveEnterTimestamp` | when the unit last became active: did it really restart at 03:12? |
| `NRestarts` | how often systemd restarted it automatically (`Restart=`); rising = crash loop |
| `UnitFileState` | the boot state: `enabled`, `disabled`, `static`, `masked` |
| `FragmentPath` | the main unit file in use; `DropInPaths` lists the overrides |
| `--value` | the value only: `cat /proc/"$(systemctl show -p MainPID --value app)"/limits` |
| `-p LimitNOFILE` | the open-files limit the service really gets (limits.conf does not apply) |

**What the output tells you:**

```
NRestarts=14
FragmentPath=/usr/lib/systemd/system/apache2.service
UnitFileState=enabled
ActiveEnterTimestamp=Sat 2026-10-03 03:12:41 UTC
```

Properties come in systemd's order, not yours. Fourteen automatic restarts and a last start at 03:12: the service crashed and came back, which the `active (running)` in `status` hides.

**Why it is effective:** single, script-friendly values that include settings nobody wrote down (defaults such as `TimeoutStopUSec` or `LimitNOFILE`), so you see what systemd will actually do, not what a file seems to say.

**Compared with `systemctl cat`:** cat shows the files and their order, so you know **where** a setting comes from; show gives the **result** but not its source. `grep` on one unit file misses drop-ins and defaults.

**Trap:** show does not fail on a mistyped unit or property: it prints defaults with `LoadState=not-found`, or nothing. `Environment` lists only `Environment=` lines; variables from `EnvironmentFile=` appear only as the file path in `EnvironmentFiles`. Time properties end in `USec` (`RestartUSec=5s`).

**Next step:** restarts above 0 → `journalctl -u UNIT -b | grep -E 'Scheduled restart|Main process exited'`. Unexpected `FragmentPath` → `systemctl cat UNIT`. Limit too low → `systemctl edit UNIT` with `LimitNOFILE=`, restart, check `/proc/PID/limits`.

### systemctl list-dependencies — what does this unit pull in, and what needs it?
Match: systemctl list-dependencies
Instead of: reading Wants= and Requires= by hand
Safety: read-only

**In one line:** `list-dependencies` draws the tree of units a unit wants or requires; with `--reverse` it shows which units depend on it, i.e. what may stop or fail along with it.

**Read the command:** `systemctl list-dependencies --reverse crm-worker.service --no-pager`

| Part | Meaning |
|---|---|
| `list-dependencies` | units pulled in through `Wants=`, `Requires=`, `BindsTo=`… (targets expanded recursively) |
| `--reverse` | the other direction: units that want or require this one |
| `crm-worker.service` | the unit to start from |
| `--no-pager` | print without `less` |
| `--all` | expand every unit, not only targets |
| `multi-user.target` | as the unit: what a normal boot starts |

**What the output tells you:** `--reverse docker.service` on a Docker host:

```
docker.service
● ├─app-api.service
● └─multi-user.target
●   └─graphical.target
```

`app-api.service` wants or requires Docker, so stopping Docker hits it; `multi-user.target` wants Docker because it is enabled. The dots are coloured by state.

**Why it is effective:** before you stop, mask or restart something it shows the blast radius, and after "stopping one unit stopped another" it shows the link.

**Compared with reading unit files:** dependencies come from many places (`WantedBy=` symlinks, drop-ins, generators, defaults), so the tree is the only complete picture.

**Trap:** it shows requirement links, not ordering: `After=` alone appears nowhere here (use `--after`, or `systemd-analyze critical-chain`). A failed `Wants=` dependency does not stop the unit that wants it, while `Requires=` and `BindsTo=` do, yet the tree draws them the same way.

**Next step:** dependents of a unit you will stop → stop them first or plan the order. Works by hand but fails at boot → check `After=` and `Wants=network-online.target` in `systemctl cat`. Boot ordering → `systemd-analyze critical-chain UNIT`.

### systemctl list-sockets — which unit owns a port that systemd holds?
Match: systemctl list-sockets
Instead of: ss -ltnp (when the owner shows as systemd)
Safety: read-only

**In one line:** with socket activation systemd itself listens on a port or socket and starts the service on the first connection; `list-sockets` maps each such listener to its `.socket` unit and the service it activates.

**Read the command:** `systemctl list-sockets --all --no-pager`

| Part | Meaning |
|---|---|
| `list-sockets` | every socket unit: LISTEN address, UNIT, ACTIVATES |
| `--all` | include inactive socket units |
| `--no-legend` | drop header and footer (used in scripts) |
| `--no-pager` | print without `less` |

**What the output tells you:**

```
LISTEN               UNIT              ACTIVATES
/run/docker.sock     docker.socket     docker.service
[::]:22              ssh.socket        ssh.service
[::]:9090            cockpit.socket    cockpit.service
```

`LISTEN` is the address or path systemd holds, `ACTIVATES` the service that gets the connections. Port 22 belongs to `ssh.socket` (Ubuntu 22.10 and later), 9090 to Cockpit.

**Why it is effective:** when `ss -ltnp` names `systemd` (PID 1) as a port's owner, this is the command that names the real service, which a port inventory or migration plan needs.

**Compared with `ss -ltnp`:** ss shows the port and the processes holding it (`systemd`, perhaps `sshd`), but not the unit or its config. It is enough when a normal daemon owns the port.

**Trap:** stopping the service is not enough: the socket stays and starts it again on the next connection, so stop and disable both (`systemctl disable --now cockpit.socket cockpit.service`). A changed `ListenStream=`, or sshd's `Port` on Ubuntu 22.10+, needs `daemon-reload` and a restart of the `.socket`.

**Next step:** port to free → `systemctl disable --now NAME.socket NAME.service`, then `ss -ltnp 'sport = :PORT'`. Socket settings → `systemctl cat NAME.socket`. Service failing → `systemctl status NAME.service`.

### systemctl list-timers — when do scheduled units run, and when did they last run?
Match: systemctl list-timers
Instead of: crontab -l, ls /etc/cron.*
Safety: read-only

**In one line:** `list-timers` shows every timer unit with its next run, time left, last run, time since, and the service it activates, sorted by what fires next.

**Read the command:** `systemctl list-timers 'sysstat*' --no-pager`

| Part | Meaning |
|---|---|
| `list-timers` | timers loaded in systemd, next to fire first |
| `'sysstat*'` | only units matching the pattern; quoted so the shell does not expand it |
| `--all` | include inactive timers (stopped or not enabled), shown with `n/a` |
| `--no-pager` | print without `less` |

**What the output tells you:**

```
NEXT                        LEFT  LAST                        PASSED   UNIT                  ACTIVATES
Sat 2026-10-03 10:40:00 UTC 2min  Sat 2026-10-03 10:30:00 UTC 7min ago sysstat-collect.timer sysstat-collect.service
Sun 2026-10-04 00:07:00 UTC 13h   Sat 2026-10-03 00:07:00 UTC 10h ago  sysstat-summary.timer sysstat-summary.service
```

`NEXT`/`LEFT`: the next run. `LAST`/`PASSED`: the last time it fired. `ACTIVATES`: the service that does the work. `n/a` in `NEXT` means inactive or no future run.

**Why it is effective:** one table answers "is it scheduled, did it fire, when next" for every timer, including the apt and logrotate timers behind many "it changed by itself at 06:00" mysteries.

**Compared with `crontab -l`:** crontab lists one user's cron lines and has no "last run" column; list-timers shows no cron jobs at all, so an inherited server needs both.

**Trap:** `LAST` says the timer fired, not that the job succeeded: check `systemctl status NAME.service`. Times are in the server's time zone, and `RandomizedDelaySec=` shifts runs. Transient timers from `systemd-run --on-active` appear here too, and a forgotten `fw-rollback.timer` still fires.

**Next step:** timer missing → `systemctl enable --now NAME.timer`. Job failed → `journalctl -u NAME.service -n 20`. Unclear schedule → `systemd-analyze calendar 'EXPR'`. Cancel a transient rollback → `systemctl stop NAME.timer`.

### systemctl restart / start / stop — run, stop or bounce a unit
Match: systemctl restart, systemctl start, systemctl stop
Instead of: kill PID, service nginx restart, /etc/init.d/nginx restart
Safety: changes state: starts or stops the service; restart drops its connections · needs root

**In one line:** these tell systemd to start, stop, or stop-then-start a unit; systemd runs the unit's own commands and stops **every process in its cgroup**, so nothing is left behind.

**Read the command:** `sudo systemctl stop docker.socket docker`

| Part | Meaning |
|---|---|
| `stop` | run `ExecStop=` if set, SIGTERM to the remaining processes, SIGKILL after `TimeoutStopSec=` (90 s by default) |
| `docker.socket` | stop the socket too, or the next client of `/run/docker.sock` starts Docker again |
| `docker` | short for `docker.service` |
| `start` | start now; does **not** enable it at boot |
| `restart` | stop then start: new PID, open connections dropped; starts the unit if it was stopped |
| `wg-quick@wg0` | an instance of a template unit (`wg-quick@.service` with `wg0` as `%i`) |

**What the output tells you:** nothing on success. On failure:

```
Job for app.service failed because the control process exited with error code.
See "systemctl status app.service" and "journalctl -xeu app.service" for details.
```

The message is only a pointer: the reason is in the journal. "attempted too often" instead means the start limit was hit.

**Why it is effective:** systemd knows the unit's main PID, its stop command and every child in its cgroup, so a stop is clean and complete, and each action is logged with a timestamp.

**Compared with `kill PID`:** kill reaches one process and leaves the rest of the cgroup. With `Restart=on-failure`, SIGKILL counts as a failure and systemd starts the service again, while SIGTERM counts as a clean exit. `service x restart` (and on Debian/Ubuntu `/etc/init.d/x restart`) hand over to systemctl.

**Trap:** `stop` lasts until something starts the unit again: a socket, a timer, a dependency or the next boot; use `disable --now` or `mask` for that. Restarting `docker` or `containerd` restarts the containers unless live-restore is on, and `restart` drops connections where `reload` would not.

**Next step:** after any of them → `systemctl status UNIT`, `journalctl -u UNIT -n 30`, `ss -ltnp`. "attempted too often" → fix the cause, then `systemctl reset-failed UNIT`. Config change only → `systemctl reload UNIT`.

### systemctl reload — apply new config without dropping connections
Match: systemctl reload
Instead of: systemctl restart
Safety: changes state: the daemon re-reads its config (a broken config can fail or be ignored) · needs root

**In one line:** `reload` runs the unit's `ExecReload=` command, usually a SIGHUP or the daemon's own graceful reload, so the daemon re-reads its configuration while the main process and open connections stay.

**Read the command:** `sudo systemctl reload nginx`

| Part | Meaning |
|---|---|
| `reload` | ask the running daemon to re-read its own config files |
| `nginx` | the unit; it must define `ExecReload=` |
| `ExecReload=` | what reload runs, e.g. `kill -HUP $MAINPID` or `apachectl graceful` |
| `systemctl reload ssh` | sshd re-reads `sshd_config`; open sessions stay |
| `nginx -t` · `apache2ctl configtest` | test the config **before** reloading |

**What the output tells you:** nothing on success; `systemctl status` keeps the same `Main PID` and the journal shows `Reloading…` then `Reloaded…`. A unit without a reload command answers:

```
Failed to reload app.service: Job type reload is not applicable for unit app.service.
```

**Why it is effective:** Nginx, Apache, HAProxy, PHP-FPM, sshd and Caddy take a new config without closing client connections or SSH sessions, so the change is invisible to users.

**Compared with `systemctl restart`:** restart also applies the config but kills the process: in-flight requests fail, keep-alive and WebSocket connections drop, caches empty. Restart is still needed after a unit-file change (after `daemon-reload`) or when the daemon has no reload.

**Trap:** `reload` is not `daemon-reload`, which is for unit files. A reload with a broken config may fail or be ignored while the old config keeps serving, so "no error" does not prove the new config is live: test first (`nginx -t`, `apache2ctl configtest`, `haproxy -c -f FILE`) and read the error log after.

**Next step:** config test fails → fix and test again before touching the service. Reloaded but nothing changed → `journalctl -u UNIT -n 20` and the daemon's error log. "not applicable" → `restart` in a quiet moment.

### systemctl enable / disable — will it start at boot?
Match: systemctl enable, systemctl disable, chkconfig
Instead of: systemctl start, update-rc.d, chkconfig
Safety: changes state: creates or removes boot symlinks; with --now also starts or stops the unit · needs root

**In one line:** `enable` creates the symlinks named in the unit's `[Install]` section (for example in `multi-user.target.wants/`) so it starts at boot; `disable` removes them. Neither changes the running state unless you add `--now`.

**Read the command:** `sudo systemctl enable --now backup-volumes.timer`

| Part | Meaning |
|---|---|
| `enable` | link the unit into the target named by `WantedBy=` (for timers `timers.target`) |
| `--now` | also start it now; with `disable`, also stop it |
| `backup-volumes.timer` | enable the **timer**; the service it triggers needs no enabling |
| `disable` | remove the links; a running unit keeps running without `--now` |
| `static` | (shown by `is-enabled`) no `[Install]` section: only another unit, a timer or a socket starts it |

**What the output tells you:**

```
Created symlink /etc/systemd/system/timers.target.wants/backup-volumes.timer → /etc/systemd/system/backup-volumes.timer.
```

`Created symlink` means enabled, `Removed` means disabled. Enabling a unit with no `[Install]` section only prints a warning that it has no installation config.

**Why it is effective:** it separates the two questions behind most "it came back" and "it vanished" surprises: does it run **now**, and does it run **after the next reboot**. `--now` answers both in one step.

**Compared with `systemctl start`:** start runs it until the next reboot only. `update-rc.d` and `chkconfig` are the SysV-era tools for the same job.

**Trap:** for socket- or timer-activated services enable the `.socket` or `.timer`; enabling the service too makes it start at boot unconditionally. A disabled unit can still be started by hand, by a dependency or by a socket: use `mask` to prevent that.

**Next step:** verify → `systemctl is-enabled UNIT`, and for timers `systemctl list-timers UNIT`. Stopped service back after reboot → still enabled, or pulled in by another unit (`systemctl list-dependencies --reverse UNIT`). Must never run → `systemctl mask --now UNIT`. Related: `chkconfig --list` is the RHEL 6-era view, on or off per runlevel for each SysV script; on systemd hosts it lists only leftover SysV scripts.

### systemctl mask / unmask — make a unit impossible to start
Match: systemctl mask, systemctl unmask
Instead of: systemctl disable, systemctl stop
Safety: changes state: links the unit to /dev/null so nothing can start it (--now also stops it) · needs root

**In one line:** `mask` puts a link to `/dev/null` in `/etc/systemd/system` in place of the unit, so it cannot be started by anyone or anything: not you, not a dependency, not a socket, not a package script. `unmask` removes the link.

**Read the command:** `sudo systemctl mask --now apache2`

| Part | Meaning |
|---|---|
| `mask` | create `/etc/systemd/system/apache2.service → /dev/null` |
| `--now` | also stop it now |
| `apache2` | the unit (`.service` assumed) |
| `unmask apache2` | remove the link; then `enable --now` to bring it back |

**What the output tells you:**

```
Created symlink /etc/systemd/system/apache2.service → /dev/null.
```

Any later start fails with `Unit apache2.service is masked.`, and `systemctl status` shows `Loaded: masked`.

**Why it is effective:** when you hand a port to another service (Apache's 443 to Traefik), "disabled" leaves gaps: a dependency, a package reinstall or a colleague may start Apache again and take the port back. Masked, it stays down until someone deliberately unmasks it.

**Compared with `systemctl disable --now`:** disable removes the boot links and keeps a service off after a reboot, but manual starts, sockets and dependencies still work. Use disable for "not needed", mask for "must not run".

**Trap:** units that `Requires=` a masked unit fail to start too. `mask` refuses a custom unit whose own file lives in `/etc/systemd/system`, because the link would replace it. A `.socket` for the service keeps listening: mask or disable it as well. Write the rollback (`unmask`, then `enable --now`) into the change before you mask.

**Next step:** verify → `systemctl is-enabled apache2` prints `masked`; `ss -ltnp 'sport = :443'` shows the new owner. Rollback → `sudo systemctl unmask apache2 && sudo systemctl enable --now apache2`.

### systemctl edit / revert — change a packaged unit without touching its file
Match: systemctl edit, systemctl revert
Instead of: vi /lib/systemd/system/app.service, copying the unit to /etc/systemd/system
Safety: changes state: writes a drop-in under /etc/systemd/system and reloads systemd; revert deletes your overrides · needs root

**In one line:** `systemctl edit` opens an editor on a drop-in (`/etc/systemd/system/UNIT.d/override.conf`) that holds only the settings you change, and reloads systemd when you save; package upgrades never overwrite it.

**Read the command:** `sudo systemctl edit gunicorn-app.service`

| Part | Meaning |
|---|---|
| `edit` | create or edit `gunicorn-app.service.d/override.conf` |
| `[Service]` | a drop-in needs the section header of every setting it contains |
| `ExecStart=` (empty) | clears the list; the next `ExecStart=` line then replaces the command |
| `--full` | edit a full copy in `/etc` instead (it stops receiving package fixes) |
| `revert UNIT` | delete your drop-ins and `/etc` copies; also undoes `mask` and `set-property` |

**What the output tells you:** current systemd versions show the existing unit as comments below a marker, and only what you write between the markers is saved. A typical drop-in:

```
[Service]
Restart=on-failure
RestartSec=5
LimitNOFILE=65536
```

`systemctl cat` then shows it as the last block, under `# /etc/systemd/system/gunicorn-app.service.d/override.conf`.

**Why it is effective:** the change is small, visible (`systemctl cat`, `systemd-delta`), survives upgrades, and is undone with one command.

**Compared with editing `/lib/systemd/system/app.service`:** the next package upgrade silently overwrites it. A full copy in `/etc/systemd/system` wins forever and never gets the vendor's fixes; a drop-in changes only what you meant to change.

**Trap:** edit reloads unit files but does **not** restart the service: run `systemctl restart UNIT`. A setting under the wrong section header is ignored. Saving an empty file cancels the edit. `revert` removes every drop-in of the unit, including ones a colleague added.

**Next step:** after saving → `sudo systemctl restart UNIT`, then `systemctl show -p Restart,LimitNOFILE UNIT`. "more than one ExecStart= setting" → add the empty `ExecStart=` line. Whole-host audit → `systemd-delta`.

### systemctl daemon-reload — make systemd see edited unit files
Match: systemctl daemon-reload
Instead of: systemctl restart (alone, after editing a unit)
Safety: changes state: systemd re-reads all unit files and reruns its generators; running services are not restarted · needs root

**In one line:** systemd works from its in-memory copy of every unit; `daemon-reload` re-reads all unit files and drop-ins and reruns the generators (`/etc/fstab` becomes mount units), so edits take effect at the **next** start or restart.

**Read the command:** `sudo systemctl daemon-reload`

| Part | Meaning |
|---|---|
| `daemon-reload` | reload systemd's own configuration (units), not the service's config |
| `--user` | the same for your per-user instance (`systemctl --user daemon-reload`) |
| needed after | creating or editing a unit or drop-in by hand, editing `/etc/fstab`, changing sshd's `Port` with socket activation |
| not needed after | `systemctl edit`, `enable`, `disable`: they reload for you |

**What the output tells you:** nothing. Forgetting it shows up later in `systemctl status`:

```
Warning: The unit file, source configuration file or drop-ins of app.service changed on disk. Run 'systemctl daemon-reload' to reload units.
```

**Why it is effective:** it makes systemd pick up a changed `ExecStart=`, `Environment=`, limit or dependency without a reboot, and it does not stop or restart any service, so it is safe on a busy server.

**Compared with `systemctl restart` alone:** restarting without the reload starts the service with the **old** definition, so the change seems to do nothing. `systemctl reload` is different again: it asks the daemon (nginx, sshd) to re-read **its own** config files.

**Trap:** daemon-reload does not touch running processes: the service keeps its old environment, limits and command line until you restart it. A typo is only logged: the setting is ignored, or the unit refuses to load (`Loaded: bad-setting`). Check with `systemd-analyze verify` first.

**Next step:** after the reload → `systemctl restart UNIT`, then `systemctl show -p ExecStart UNIT`. Warning persists → another drop-in or a full copy in `/etc` wins: `systemctl cat UNIT`.

### systemctl reset-failed — clear a failed state and the start-limit counter
Match: systemctl reset-failed
Instead of: rebooting, systemctl restart (on a start-limited unit)
Safety: changes state: clears the failed state and the start and restart counters (the evidence in systemctl --failed) · needs root

**In one line:** after too many quick starts systemd refuses to start a unit again ("start request repeated too quickly"); `reset-failed` clears that counter and the `failed` state so the unit can be started.

**Read the command:** `sudo systemctl reset-failed lab-fail.service`

| Part | Meaning |
|---|---|
| `reset-failed` | forget the failure: state, start-limit counter, restart counter |
| `lab-fail.service` | the unit; with no name, every failed unit on the host |
| the limit | more than `StartLimitBurst=` (default 5) starts within `StartLimitIntervalSec=` (default 10 s) |

**What the output tells you:** nothing. Before it, a start fails like this:

```
Job for lab-fail.service failed because start of the service was attempted too often.
systemd[1]: lab-fail.service: Start request repeated too quickly.
systemd[1]: lab-fail.service: Failed with result 'start-limit-hit'.
```

(the first line from `systemctl start`, the others from the journal). Afterwards the unit is `inactive (dead)` and gone from `systemctl --failed`.

**Why it is effective:** the start limit protects the host from an endless crash loop; once the cause is fixed, reset-failed lets you try again at once instead of waiting or rebooting. It also clears a failed transient unit from `systemd-run`, so its name can be used again.

**Compared with `systemctl restart`:** a restart of a start-limited unit is refused with the message above until you reset it or the interval has passed.

**Trap:** it fixes nothing: the next start fails the same way if the cause remains, and you have wiped the evidence that `systemctl --failed` and monitoring were showing. Read `journalctl -u UNIT -b` first.

**Next step:** find why it failed → `journalctl -u UNIT -b -n 50`, fix it (often `systemctl edit`), then reset-failed and `systemctl start UNIT`. Still failing → `systemctl status UNIT` for the exit code.

### systemctl set-property — cap a unit's CPU, memory or I/O while it runs
Match: systemctl set-property
Instead of: renice, ionice, kill
Safety: changes state: changes the unit's cgroup limits at once; permanent unless --runtime · needs root

**In one line:** `set-property` changes resource controls of a running unit (CPU quota, memory limits, I/O bandwidth) by writing its cgroup, with no restart.

**Read the command:** `sudo systemctl set-property --runtime UNIT CPUQuota=50%`

| Part | Meaning |
|---|---|
| `--runtime` | only until reboot; without it the setting is saved as a drop-in under `/etc/systemd/system.control/` |
| `UNIT` | a service, scope or slice |
| `CPUQuota=50%` | at most half of one CPU in total (`200%` = two CPUs) |
| `CPUQuota=` | an empty value removes the quota |
| `MemoryHigh=1G MemoryMax=1200M` | above 1G the kernel throttles and reclaims; above 1200M it OOM-kills inside the unit |
| `IOWriteBandwidthMax="/dev/sda 40M"` | cap writes to that disk at 40 MB/s |

**What the output tells you:** nothing. Check with `systemctl show -p CPUQuotaPerSecUSec UNIT`, which prints `CPUQuotaPerSecUSec=500ms` for 50%, and watch the effect in `systemd-cgtop`.

**Why it is effective:** during an incident you can tame a runaway backup, reindex or worker so the rest of the host recovers, without killing the job or restarting it; the cap covers every process in the unit, including children it starts later.

**Compared with `renice`/`ionice`:** priorities only matter when processes compete, apply per process and set no ceiling; a quota is a hard limit for the whole cgroup. Killing the job loses its work.

**Trap:** without `--runtime` the limit is permanent, and the service is still throttled next month: undo with an empty value or `systemctl revert UNIT`. `MemoryMax=` set too low makes the kernel OOM-kill the service, which looks like a crash. The I/O limits need cgroup v2 (Ubuntu 22.04 and later use it).

**Next step:** confirm the throttle → `systemd-cgtop`, `systemctl show -p CPUQuotaPerSecUSec,MemoryMax UNIT`. Service OOM-killed → `journalctl -k | grep -i 'memory cgroup'`. One-off job → set limits at launch: `systemd-run --scope -p MemoryMax=… CMD`.

### systemd-run — run a command as a managed, limited or delayed unit
Match: systemd-run
Instead of: nohup cmd &, sleep 300 && cmd &, at
Safety: changes state: runs a command (as root under sudo), now or later; read the Trap before arming a rollback timer

**In one line:** `systemd-run` starts a command as a **transient** unit: supervised, logged to the journal under a name, inside its own cgroup with any limits you set, and if you like delayed by a one-shot timer, all without writing a unit file.

**Read the command:** `sudo systemd-run --on-active=5min --unit=fw-rollback /usr/sbin/ufw disable`

| Part | Meaning |
|---|---|
| `--on-active=5min` | do not run now: a transient timer fires once, 5 minutes from now |
| `--unit=fw-rollback` | name it (`fw-rollback.timer` + `fw-rollback.service`) to find, read and cancel it |
| `/usr/sbin/ufw disable` | the command; use absolute paths, the unit gets a clean environment |
| `--scope` | run in your terminal, in the foreground, but in a new cgroup so limits apply |
| `-p MemoryMax=300M` | any unit setting (`--property=`): `CPUQuota=`, `IOWriteBandwidthMax=`, `Nice=`, `PrivateTmp=` |
| `--uid=demo` | run as that user |
| `--wait` · `--collect` | wait until it finishes · unload it even if it failed |

**What the output tells you:**

```
Running timer as unit: fw-rollback.timer
Will run service as unit: fw-rollback.service
```

These names are what you use next: `systemctl list-timers fw-rollback.timer` shows when it fires, `journalctl -u fw-rollback` what it did.

**Why it is effective:** it turns a risky remote change into a reversible one (a dead man's switch: arm the rollback, make the change, cancel it if you can still log in), and gives ad-hoc jobs the logging and limits of real services.

**Compared with `nohup cmd &` or `sleep 300 && cmd &`:** a background job inherits your shell, can die with your SSH session, logs nowhere and has no limits. `at now + 5 minutes` also works as a dead man's switch, but needs `atd` and mails its output instead of journaling it.

**Trap:** a forgotten switch fires anyway: cancel with `sudo systemctl stop fw-rollback.timer` once the change is confirmed. A failed transient unit keeps its name until `systemctl reset-failed NAME`. Without `--scope` the command runs in systemd's clean environment: none of your shell's variables, PATH additions or current directory.

**Next step:** after arming → `systemctl list-timers --all | grep rollback`. Change confirmed → stop the timer. Locked out → wait; later `journalctl -u fw-rollback` shows the rollback ran. Heavy one-off job → `systemd-run --scope -p IOWriteBandwidthMax='/dev/sdb 20M' CMD`.

### systemd-analyze — where did the boot time go?
Match: systemd-analyze, systemd-analyze blame, systemd-analyze critical-chain, systemd-analyze plot
Instead of: systemd-analyze blame (alone)
Safety: read-only

**In one line:** `systemd-analyze` reads systemd's boot timestamps: the total time per stage, the slowest units (`blame`), and the chain of units the boot really waited for (`critical-chain`).

**Read the command:** `systemd-analyze critical-chain docker.service`

| Part | Meaning |
|---|---|
| `systemd-analyze` | alone: boot time split into kernel, initrd and userspace (plus firmware and loader on UEFI) |
| `blame` | every unit sorted by how long its own start took |
| `critical-chain` | the chain of units the boot waited on, with times |
| `docker.service` | the chain that led to this unit (default: the boot target) |
| `@6.498s` | when the unit became active, counted from boot |
| `+5.085s` | how long the unit itself took to start |
| `plot > /var/tmp/boot.svg` | the whole boot as an SVG timeline for a browser |

**What the output tells you:**

```
docker.service +1.204s
└─network-online.target @6.498s
  └─systemd-networkd-wait-online.service @1.410s +5.085s
    └─systemd-networkd.service @1.220s +180ms
      └─systemd-udevd.service @0.910s +290ms
```

Read it from the bottom up: Docker waited for `network-online.target`, and `systemd-networkd-wait-online` spent 5 s waiting for the network. That wait, not Docker, is the delay.

**Why it is effective:** units start in parallel, so the slowest unit in `blame` may delay nothing; critical-chain shows the path that really held the boot, or your service, back.

**Compared with `systemd-analyze blame`:** blame is a useful list of suspects, but it cannot tell whether a slow unit was on the critical path, and it shows nothing for `Type=simple` services, which systemd counts as started at once.

**Trap:** "Bootup is not yet finished" means a start job is still running, and that is the finding: run `systemctl list-jobs`. The numbers describe the last boot only, so reboot after a fix and compare. `systemd-networkd-wait-online` on top usually means a netplan interface that never gets a link or address, not slow DHCP.

**Next step:** wait-online slow → fix the interface, or mark it `optional: true` in netplan. Mount slow → `/etc/fstab` (`nofail`, wrong UUID). One service slow → `journalctl -b -u UNIT`.

### systemd-analyze verify / calendar / security — check units, schedules and sandboxing
Match: systemd-analyze verify, systemd-analyze calendar, systemd-analyze security, systemd-analyze cat-config
Instead of: daemon-reload and restart to see if it works
Safety: read-only

**In one line:** these check configuration before it hurts: `verify` lints unit files, `calendar` explains an `OnCalendar=` schedule, `security` scores a service's sandboxing, and `cat-config` prints a config file with its drop-ins.

**Read the command:** `systemd-analyze verify /etc/systemd/system/app.service`

| Part | Meaning |
|---|---|
| `verify` | load the unit; report unknown sections and keys, missing `Exec…=` binaries, missing dependencies |
| `/etc/systemd/system/app.service` | the file to check (an installed unit name works too) |
| `calendar 'Mon..Fri *-*-* 02:30:00'` | normalise a schedule and print when it fires next |
| `security demo-web` | exposure score 0–10 (lower is better) and each sandboxing setting it lacks |
| `cat-config systemd/journald.conf` | the main file plus every drop-in for it, in the order applied |

**What the output tells you:** `verify` prints nothing for a clean unit. Each problem names the unit (and, for syntax errors, the file and line), for example an unknown key (a typo such as `ExecStar=`) or a binary that is not there:

```
app.service: Command /usr/bin/pyhton3 is not executable: No such file or directory
```

`calendar` prints the normalised form and the next elapse; `security` ends with an overall exposure level and a rating such as `UNSAFE` or `OK`.

**Why it is effective:** systemd ignores an unknown or misspelled setting with only a warning, so a unit can start **without** the line you wrote (a typo in `Restart=` means no restarts); verify shows that before production does.

**Compared with daemon-reload and a restart:** that reveals errors too, but only in the journal, often as warnings, and only after you stopped the working version.

**Trap:** verify also loads units yours refers to, and warns about them or about man pages in `Documentation=`; that noise is not your bug. A clean verify proves only that systemd can parse the file and find the binary, not that the app works. The security score is a heuristic: some services need network or write access.

**Next step:** errors → fix, `daemon-reload`, verify again, then restart. Timer fires at the wrong time → compare `calendar` with the server's zone (`timedatectl`). High exposure → add settings such as `ProtectSystem=strict` and `PrivateTmp=true` one at a time, testing each.

### loginctl — user sessions and lingering
Match: loginctl, machinectl
Instead of: who, w
Safety: read-only for list-sessions, session-status · changes state: enable-linger (user services start at boot), terminate-user (kills that user's processes) · needs root

**In one line:** `loginctl` asks systemd-logind who has which session, which processes belong to a session, and whether a user's own systemd (and its services) keeps running without a login, which is called **lingering**.

**Read the command:** `sudo loginctl enable-linger ci`

| Part | Meaning |
|---|---|
| `enable-linger ci` | start user ci's systemd at boot and keep it after logout, so its user services (rootless Docker, Podman) run |
| `list-sessions` | current sessions: ID, UID, user, seat, TTY |
| `session-status 12` | the processes of session 12 and its recent log lines |
| `terminate-user deploy` | end every session and process of that user |
| `/var/lib/systemd/linger/` | one file per user with lingering enabled |

**What the output tells you:**

```
SESSION  UID USER   SEAT TTY
      3 1001 deploy      pts/0
     12 1000 ops         pts/1
```

Columns vary a little between versions; the session ID is what `session-status` takes.

**Why it is effective:** "the rootless container dies when I log out" and "the user service starts only after someone logs in" are both lingering. A process in a `session-N.scope` was started by a person, not a unit, and loginctl names that person.

**Compared with `who`/`w`:** they list logins from utmp but know nothing about lingering, user managers, or which processes a session owns.

**Trap:** `terminate-user` kills everything that user runs, including tmux sessions and long jobs. `enable-linger` is also persistence: that user's services now start at every boot, so audit `/var/lib/systemd/linger/`.

**Next step:** user service gone after reboot → enable linger, then as that user `systemctl --user enable --now NAME`. Stray process → `loginctl session-status N`, then stop it through whatever started it. Related: `sudo machinectl shell USER@` (package systemd-container) opens a real login session for that user, with `XDG_RUNTIME_DIR` and a user manager, which `sudo -u` and `su` usually lack; rootless Docker needs one.

### crontab / run-parts / at — scheduled jobs outside systemd
Match: crontab, run-parts, at, atq, atrm
Instead of: cat /etc/crontab
Safety: read-only for crontab -l, atq, run-parts --test · changes state: crontab -e and -r, at, atrm, run-parts without --test (runs the scripts)

**In one line:** `crontab` lists or edits one user's recurring jobs, `run-parts` runs (or with `--test` lists) the scripts in a directory such as `/etc/cron.daily`, and `at` queues a command to run once later; `atq` lists and `atrm` cancels those.

**Read the command:** `crontab -l -u www-data 2>/dev/null`

| Part | Meaning |
|---|---|
| `-l` | list the crontab (`-e` edits it, with a syntax check on save) |
| `-u www-data` | of this user; other users' crontabs need root |
| `2>/dev/null` | hide "no crontab for www-data" when looping over all users |
| `run-parts --test /etc/cron.daily` | which scripts would run; names with a dot (`backup.sh`) are skipped |
| `echo 'ufw --force disable' | sudo at now + 5 minutes` | run once in 5 minutes: a dead man's switch for risky remote changes |
| `atq` · `atrm 3` | list pending at jobs · cancel job 3 |

**What the output tells you:**

```
*/5 * * * * /usr/local/bin/watchdog.sh >> /var/log/watchdog.log 2>&1
@reboot cd /srv/crm && /usr/bin/pm2 resurrect
```

Fields: minute, hour, day of month, month, day of week, command. A watchdog every 5 minutes and a pm2 resurrect at every boot: two hidden ways a stopped app comes back.

**Why it is effective:** user crontabs live in `/var/spool/cron/crontabs/` (Ubuntu, root-only) and appear nowhere else, not in `/etc/cron.d` and not in `systemctl list-timers`; an inventory or migration has to read them user by user.

**Compared with `cat /etc/crontab`:** it shows the system crontab only; `/etc/cron.d/*`, the `cron.daily` scripts and each user's crontab are separate places.

**Trap:** cron runs jobs with a minimal environment (short PATH, no profile), `%` means newline unless escaped, and output is discarded without a mail system ("No MTA installed"). `crontab -r` deletes the whole crontab without asking, and `r` sits next to `e`. An `at` job needs `atd` running, and a dead man's switch you forget to cancel fires anyway.

**Next step:** did it run? → `journalctl -u cron --since today` (RHEL: `crond`). Works by hand, fails in cron → absolute paths, output redirected to a log. New jobs → a systemd timer, which records status and output.

### pm2 — the Node.js process manager behind a systemd unit
Match: pm2
Instead of: kill PID, systemctl restart pm2-deploy
Safety: changes state: restart, stop and start change running apps; save rewrites the list restored at boot · run it as the app's user

**In one line:** pm2 keeps Node.js apps running, restarts them when they die and keeps their logs in `~/.pm2/logs`; each user has their own pm2 daemon and app list, usually started at boot by a `pm2-USER.service` unit.

**Read the command:** `pm2 restart ecosystem.config.js --only crm --update-env && pm2 save`

| Part | Meaning |
|---|---|
| `restart ecosystem.config.js` | restart the apps defined in this file, re-reading it |
| `--only crm` | only the app named `crm` in the file |
| `--update-env` | refresh the app's environment from the file (with a bare app name it takes your shell's) |
| `pm2 save` | store the current app list; `pm2 resurrect` at boot restores exactly that |
| `sudo -u deploy pm2 stop crm` | act as the app's user: root's pm2 is another daemon with another list |
| `pm2 list` · `pm2 describe crm` | status, restart count, memory · one app's script, cwd, env and log paths |

**What the output tells you:** `pm2 list` gives each app's status (`online`, `stopped`, `errored`), its restart count and memory. A restart count that keeps climbing is a crash loop that pm2 hides by restarting the app every time.

**Why it is effective:** on inherited servers pm2 is often the real supervisor: `systemctl` sees only the pm2 daemon, and a killed Node process comes straight back. Working through pm2, as the right user, is the clean way to stop, restart or reconfigure the app.

**Compared with `kill PID`:** pm2 restarts the process at once. Restarting `pm2-deploy.service` bounces every app of that user.

**Trap:** `sudo pm2 list` shows root's (usually empty) list, not the app user's. `pm2 stop` keeps the app in the saved list, so a later `pm2 resurrect` may start it again, depending on the pm2 version. Without `pm2 save` the next boot brings back the old list. Look for a second supervisor too (cron `@reboot`, a watchdog).

**Next step:** where are its logs → `pm2 describe APP` as that user. App must stay off → `pm2 delete APP && pm2 save`, and disable `pm2-USER.service` if pm2 itself should go. Other starters → `crontab -l -u USER`.

### logger — write a test line into the system log
Match: logger
Instead of: echo "test" >> /var/log/syslog
Safety: changes state: adds one log entry (harmless)

**In one line:** `logger` sends a message down the normal syslog path, so it lands in the journal, in rsyslog's files and in any remote forwarding: a known string that proves the log pipeline end to end.

**Read the command:** `logger -p local0.err -t myapp "test error"`

| Part | Meaning |
|---|---|
| `-p local0.err` | facility.priority: `local0` (free for local apps), priority `err` |
| `-t myapp` | the tag (`SYSLOG_IDENTIFIER`); find it with `journalctl -t myapp` |
| `"test error"` | the message |
| `-p auth.notice` | the auth facility: goes to `auth.log` and to SIEM rules that watch it |

**What the output tells you:** nothing; read it back with `journalctl -t myapp -n 1`:

```
Oct 03 10:15:02 web01 myapp[50433]: test error
```

In the journal but not in `/var/log/syslog`, or not on the central server: the break is in rsyslog or the forwarding.

**Why it is effective:** it tests the path real logs take, with a unique string you choose, so "logs are not arriving" becomes a yes/no per hop.

**Compared with `echo "test" >> /var/log/syslog`:** that writes one file directly, bypassing journald, rsyslog rules and forwarding, so it proves nothing.

**Trap:** arriving locally does not prove arriving at the collector: search there for the same string. Floods are rate-limited ("Suppressed N messages"). In scripts, `| logger -t NAME` beats writing a private log file.

**Next step:** missing remotely → `grep -E "@|target" /etc/rsyslog.conf /etc/rsyslog.d/*`, `systemctl status rsyslog`. Missing locally → `systemctl status systemd-journald`.

### logrotate — why did (or didn't) this log rotate?
Match: logrotate
Instead of: ls -l /var/log/app/, deleting big log files by hand
Safety: read-only with -d · -f changes state: renames, compresses and deletes logs and runs postrotate scripts · needs root

**In one line:** `logrotate -d` replays the rotation logic for a config and prints every decision without changing anything; `-f` performs the rotation now.

**Read the command:** `sudo logrotate -d /etc/logrotate.d/apache2 2>&1`

| Part | Meaning |
|---|---|
| `-d` | debug: a dry run; nothing rotates and the state file is not updated |
| `/etc/logrotate.d/apache2` | only this file; defaults from `/etc/logrotate.conf` are not read |
| `2>&1` | the report goes to stderr; merge it so `| tail` or `| grep` see it |
| `-f` | force a rotation now, even if not due (really changes files) |

**What the output tells you:**

```
rotating pattern: /var/log/apache2/*.log  after 1 days (14 rotations)
considering log /var/log/apache2/access.log
  Now: 2026-10-03 10:20
  Last rotated at 2026-10-03 00:00
  log does not need rotating (log has been already rotated)
```

The pattern line gives the schedule and how many old copies are kept; each `considering log` block says why a file is or is not rotated. Errors (a bad directive, insecure parent directory permissions) appear here too.

**Why it is effective:** you see the decision per file (matched? due? too small?) and the config errors that make the nightly run skip files.

**Compared with `ls -l /var/log/app/`:** ls shows whether `.1` and `.gz` files exist and how big the log is, not why rotation did not happen.

**Trap:** `-f` really rotates and runs `postrotate`, often a service reload. Testing one file skips the global defaults, so the nightly run may differ. An app that never reopens its log keeps writing into `app.log.1` after a rotation (fix: a `postrotate` reload or `copytruncate`). Docker's container logs are not handled by logrotate.

**Next step:** never rotates → `systemctl status logrotate.timer`, `journalctl -u logrotate --since "2 days ago"`. "insecure permissions" → add `su USER GROUP`. Disk still full → `lsof +L1` for deleted files held open.

### dmesg — what is the kernel saying?
Match: dmesg
Instead of: dmesg (no flags), application logs only
Safety: read-only · Ubuntu allows it only for root · never -c, which clears the buffer

**In one line:** `dmesg` prints the kernel's ring buffer: OOM kills, segfaults, disk and filesystem errors, NIC link changes and conntrack overflows, the evidence for problems an application cannot log about itself.

**Read the command:** `sudo dmesg -T --level=err,warn`

| Part | Meaning |
|---|---|
| `-T` | human-readable timestamps instead of seconds since boot (approximate) |
| `--level=err,warn` | only these priorities; `-l err,crit,alert,emerg` is the short form |
| `-w` | follow new messages as they arrive (`-Tw`) |
| `sudo` | on Ubuntu only root may read the buffer (`kernel.dmesg_restrict=1`) |
| `> /dev/shm/dmesg-$(date +%F).txt` | save a copy in RAM: works on a full or read-only disk, and the buffer is lost at reboot |

**What the output tells you:**

```
[Sat Oct  4 02:11:07 2026] I/O error, dev sda, sector 41208832 op 0x1:(WRITE) flags 0x800 phys_seg 4 prio class 2
[Sat Oct  4 02:11:08 2026] EXT4-fs error (device dm-0): ext4_journal_check_start:84: comm kworker/u8:2: Detected aborted journal
[Sat Oct  4 02:11:08 2026] EXT4-fs (dm-0): Remounting filesystem read-only
```

Read the order: the disk failed a write first, then ext4 aborted its journal and went read-only, so the cause is storage, not ext4. Other patterns: `Out of memory: Killed process`, `segfault at`, `Link is Down`, `nf_conntrack: table full, dropping packet`.

**Why it is effective:** when a process vanished or a filesystem went read-only, the kernel is often the only witness, and one command finds it.

**Compared with `journalctl -k`:** the journal holds the same kernel messages with exact timestamps and, if persistent, from earlier boots (`journalctl -k -b -1`). dmesg needs no journal, but covers only the current boot, and old lines are overwritten when the buffer fills.

**Trap:** `-T` times drift after suspend/resume or a paused VM; trust `journalctl -k` for timing. The buffer empties at reboot, so save it before rebooting a broken host. `dmesg -c` clears it for everyone.

**Next step:** OOM → `journalctl -k | grep -i 'killed process'`, then memory limits. I/O errors → `smartctl -a`, the storage layer. Link flaps → `ethtool`, cable and switch. Segfaults → `coredumpctl list`.

### coredumpctl — which program crashed, and where in its code?
Match: coredumpctl
Instead of: dmesg | grep segfault
Safety: read-only · core dumps contain process memory, possibly secrets: treat them as sensitive

**In one line:** when systemd-coredump is the crash handler, every crash is stored with metadata; `coredumpctl` lists them, shows the details with a short stack trace, and opens a dump in gdb.

**Read the command:** `coredumpctl info 1234`

| Part | Meaning |
|---|---|
| `list` | crashes: time, PID, UID, signal, whether the core file is still there, executable |
| `info 1234` | details of the crash of PID 1234: signal, command line, unit, stack trace |
| `gdb 1234` | open the dump in gdb (`bt` for the full backtrace); newer name `debug` |
| `1234` | a match: PID, program name or path |

**What the output tells you:**

```
TIME                         PID UID GID SIG     COREFILE EXE
Sat 2026-10-03 09:41:12 UTC 1234  33  33 SIGSEGV present  /usr/sbin/php-fpm8.3
```

(`coredumpctl list`): php-fpm running as UID 33 (www-data) died of a segfault, and its core is still stored.

**Why it is effective:** a segfault leaves one kernel line; the dump and `info` show which function crashed, which a bug report or a "roll back that library" decision needs.

**Compared with `dmesg | grep segfault`:** dmesg proves the crash and names the library and address, but not the call stack.

**Trap:** Ubuntu's default crash handler is apport (`/var/crash`), not systemd-coredump, so `coredumpctl list` can be empty although programs crash: check `cat /proc/sys/kernel/core_pattern`. `COREFILE` `missing` means the dump was removed (size limits, cleanup). Without debug symbols a stack shows only addresses.

**Next step:** one binary keeps crashing → recent updates in `/var/log/apt/history.log`, roll back or report. No dumps at all → `core_pattern`, `ulimit -c`, the unit's `LimitCORE=`.

### sysctl — read and set kernel tunables
Match: sysctl, tuned-adm
Instead of: cat /etc/sysctl.conf
Safety: read-only without -w · changes state: -w, -p and --system change the running kernel · needs root to write

**In one line:** `sysctl` reads and writes the kernel settings under `/proc/sys` (`net.ipv4.ip_forward` is `/proc/sys/net/ipv4/ip_forward`) and shows the value the kernel uses **now**, whatever the files say.

**Read the command:** `sudo sysctl -w net.netfilter.nf_conntrack_max=524288`

| Part | Meaning |
|---|---|
| `sysctl NAME …` | read one or several values |
| `-w NAME=VALUE` | write now; lost at reboot |
| `--system` | apply every file in the `sysctl.d` directories and `/etc/sysctl.conf`, printing each file |
| `-p FILE` | apply one file (default `/etc/sysctl.conf`) |
| `-a 2>/dev/null` | dump all keys, hiding the ones you may not read |
| `-n` | the value only, for scripts (also on macOS: `sysctl -n hw.memsize`) |

**What the output tells you:**

```
net.netfilter.nf_conntrack_count = 261880
net.netfilter.nf_conntrack_max = 262144
```

(`sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max`): the connection-tracking table is almost full; once it is, the kernel drops new connections and logs `nf_conntrack: table full, dropping packet`.

**Why it is effective:** it shows the live value, which is what counts during an incident, and `-w` lets you test a change without a reboot.

**Compared with `cat /etc/sysctl.conf`:** that shows what someone wrote in one file; files in `/etc/sysctl.d/` may override it, and nothing proves it was applied.

**Trap:** `-w` does not persist: put the value in `/etc/sysctl.d/NN-name.conf`. Files apply in name order and the later file wins (`99-` beats `60-`), so read the `--system` output when a value is not what you set. `net.bridge.*` and `net.netfilter.*` keys exist only once their module is loaded. Containers share the host's `vm.*` and `kernel.*` values, while many `net.*` keys are per network namespace.

**Next step:** lost after reboot → a file in `/etc/sysctl.d/`, then `sysctl --system`. `cannot stat /proc/sys/...` → load the module (`modprobe`). Conntrack full → raise the limit and find who opens so many connections (`ss -s`, `conntrack -S`). Related: on RHEL, `tuned-adm active` names the tuned profile in force; profiles can set sysctl keys too, so check it when a value differs from your files.

### lsmod / modprobe / modinfo — is the kernel module this needs loaded?
Match: lsmod, modprobe, modinfo
Instead of: ls /lib/modules
Safety: read-only for lsmod and modinfo · modprobe changes state: loads, or with -r unloads, a module (unloading one in use breaks networking or storage) · needs root

**In one line:** much of the kernel (drivers, filesystems, netfilter features) comes as modules; `lsmod` lists what is loaded, `modinfo` describes a module, and `modprobe` loads or unloads one together with its dependencies.

**Read the command:** `sudo modprobe br_netfilter`

| Part | Meaning |
|---|---|
| `modprobe br_netfilter` | load the module and the modules it needs, for the running kernel |
| `modprobe -r module` | unload it (refused while it is in use) |
| `lsmod` | loaded modules: name, size, use count, which modules use it |
| `modinfo br_netfilter` | file path, description, version, parameters, dependencies |
| `/etc/modules-load.d/k8s.conf` | module names listed here load at every boot |
| `/etc/modprobe.d/*.conf` | `options` and `blacklist` lines |

**What the output tells you:**

```
br_netfilter           32768  0
overlay               212992  12
nf_conntrack          196608  6 xt_conntrack,nf_nat,xt_nat,nf_conntrack_netlink,xt_MASQUERADE,xt_addrtype
```

(`lsmod | grep -E '^(overlay|br_netfilter|nf_conntrack)'`): the third column counts users. `overlay` in use 12 times points to a Docker host with running containers; `nf_conntrack` is used by NAT.

**Why it is effective:** container and Kubernetes networking depend on modules (`overlay`, `br_netfilter`, `nf_conntrack`); confirming them takes seconds and rules out a whole class of "pods can't reach Services" problems.

**Compared with `ls /lib/modules/$(uname -r)`:** that shows what is installed for the kernel, not what is loaded.

**Trap:** a feature built into the kernel never appears in `lsmod`, yet works (see `/lib/modules/$(uname -r)/modules.builtin`). `modprobe` lasts until reboot unless the name is in `modules-load.d`. `Module X not found in directory /lib/modules/...` means it is not built for this kernel (on Ubuntu often the `linux-modules-extra` package).

**Next step:** module missing → `modprobe`, then add it to `/etc/modules-load.d/`. Which driver a device uses → `lspci -k`. Loaded but the feature is off → its sysctl (`sysctl net.bridge.bridge-nf-call-iptables`).

### uname / lsb_release / hostnamectl / hostname — which kernel, OS and name is this?
Match: uname, lsb_release, hostnamectl, hostname
Instead of: cat /etc/issue
Safety: read-only · hostnamectl set-hostname and hostname NAME change the hostname (needs root)

**In one line:** these identify the box before you trust any instructions: kernel release and CPU architecture (`uname`), distribution (`lsb_release`), and hostname, OS, kernel and virtualization in one view (`hostnamectl`).

**Read the command:** `lsb_release -ds; uname -r`

| Part | Meaning |
|---|---|
| `lsb_release -ds` | `-d` the distribution description, `-s` short (value only): `Ubuntu 24.04.1 LTS` |
| `uname -r` | the running kernel, `6.8.0-45-generic`: modules, headers and initramfs must match it |
| `uname -m` · `uname -a` | CPU architecture (`x86_64`, `aarch64`) · all fields in one line |
| `hostnamectl` | static hostname, OS, kernel, architecture, virtualization, hardware model |
| `hostnamectl --static` | only the static hostname |
| `hostnamectl set-hostname cp1` | set it persistently (`/etc/hostname`); Kubernetes nodes need unique names |
| `hostname -I` · `hostname -f` | every IP address on the host · the fully qualified name (from `/etc/hosts` or DNS) |

**What the output tells you:** an excerpt of `hostnamectl`:

```
 Static hostname: web01
  Virtualization: kvm
Operating System: Ubuntu 24.04.1 LTS
          Kernel: Linux 6.8.0-45-generic
    Architecture: x86-64
```

A KVM guest on Ubuntu 24.04 with kernel 6.8: Ubuntu 24.04 docs, amd64 images and VM limits apply.

**Why it is effective:** many wrong fixes start from a wrong assumption (a RHEL command on Ubuntu, an arm64 image on x86, a bare-metal tuning guide on a VM); one line removes the guesswork.

**Compared with `cat /etc/os-release`:** os-release is the portable way to get the distribution, also inside containers, but shows no kernel, architecture or virtualization.

**Trap:** inside a container `uname -r` shows the **host's** kernel (containers share it) while `/etc/os-release` shows the image's distribution. `hostname -I` includes Docker bridge addresses such as 172.17.0.1, and `hostname -i` often returns 127.0.1.1 on Ubuntu. `hostname NAME` lasts only until reboot (or applies only inside a UTS namespace); after `set-hostname`, add the name to `/etc/hosts` or sudo complains "unable to resolve host".

**Next step:** wrong kernel after an update → `ls /boot`, the GRUB menu. VM → `systemd-detect-virt`, the hypervisor's limits. Name problems → `getent hosts "$(hostname)"`.

### systemd-detect-virt / dmidecode / lspci / sensors / ipmitool — what hardware is this, and is it healthy?
Match: systemd-detect-virt, dmidecode, lspci, sensors, ipmitool, lsusb, lshw, mcelog
Instead of: dmesg | grep -i mce, lscpu
Safety: read-only · dmidecode and ipmitool need root

**In one line:** first find out whether you are on a VM or bare metal and which hardware and drivers are involved; on bare metal, then read temperatures and the BMC's event log, which records faults the OS never sees.

**Read the command:** `sudo ipmitool sel list`

| Part | Meaning |
|---|---|
| `systemd-detect-virt` | hypervisor or container type (`kvm`, `vmware`, `microsoft`, `amazon`, `docker`…) or `none` |
| `dmidecode -s system-product-name` | the server model from the firmware tables (a VM shows its hypervisor's) |
| `dmidecode -t memory` | every DIMM slot: size, speed, type, empty slots |
| `lspci -k` | PCI devices (NICs, RAID controllers) and the kernel driver in use for each |
| `sensors` | CPU and board temperatures, fans, voltages, with high and critical limits |
| `ipmitool sensor` · `sdr type Temperature` | the BMC's sensors with thresholds · only temperatures |
| `ipmitool sel list` | the BMC's System Event Log: ECC errors, PSU and fan failures, with time |
| `ipmitool chassis status` | power state, last power event, fault flags |

**What the output tells you:**

```
   1 | 10/03/2026 | 03:12:40 | Memory #0x53 | Correctable ECC | Asserted
   2 | 10/03/2026 | 03:40:02 | Power Supply #0x62 | Power Supply AC lost | Asserted
```

Correctable ECC errors that keep coming point to a failing DIMM; "AC lost" on one PSU means that supply or its feed died. The BMC's clock may differ from the OS clock.

**Why it is effective:** random reboots, thermal throttling and memory errors have hardware causes no service log shows, and the BMC keeps its log even when the OS crashed or was off.

**Compared with `dmesg | grep -i mce`:** the kernel reports machine-check events it saw while running; it knows nothing about PSU, fan or chassis events, or anything during a hang.

**Trap:** VMs have no real sensors or BMC (`No sensors found!`, `Could not open device at /dev/ipmi0…`): virtual, not broken. `sensors` may need `sensors-detect` once. dmidecode data comes from firmware and can be blank or generic.

**Next step:** VM → look at the hypervisor (host load, steal time in `top`). ECC or PSU events → vendor support with the SEL. Hot CPU → fans, airflow, throttling with `turbostat`. Wrong NIC driver → `modinfo DRIVER`, firmware. Related: `lsusb` lists USB devices, `lshw -short` (as root) one line per device, and `mcelog` decodes CPU and memory machine-check errors where still used (newer hosts: rasdaemon).

### timedatectl / hwclock — is the clock synchronised, and in which time zone?
Match: timedatectl, hwclock
Instead of: date
Safety: read-only for the status views · changes state: set-ntp, set-timezone, hwclock --systohc · needs root to change

**In one line:** `timedatectl` shows the system time, UTC, the hardware clock (RTC), the time zone and, most important, whether NTP is keeping the clock synchronised right now.

**Read the command:** `timedatectl`

| Part | Meaning |
|---|---|
| `System clock synchronized` | `yes`: an NTP client is disciplining the clock now |
| `NTP service` | `active`: the NTP client timedatectl manages (usually systemd-timesyncd) is enabled |
| `timesync-status` | systemd-timesyncd details: server, offset, poll interval |
| `set-ntp true` | enable and start that NTP client |
| `set-timezone Asia/Kolkata` | change the zone; find names with `list-timezones` |
| `hwclock --show` | read the hardware clock (RTC) directly |
| `hwclock --systohc` | copy the (correct) system time into the RTC |

**What the output tells you:**

```
               Local time: Mon 2025-06-02 03:11:09 UTC
           Universal time: Mon 2025-06-02 03:11:09 UTC
                 RTC time: Mon 2025-06-02 03:11:10
                Time zone: Etc/UTC (UTC, +0000)
System clock synchronized: no
              NTP service: active
```

`synchronized: no` with `NTP service: active` is the classic pattern: the client runs but gets no answer, usually because outbound UDP 123 is blocked.

**Why it is effective:** TLS ("certificate not yet valid"), AWS signatures, Kerberos and TOTP all fail on a wrong clock with errors that never mention time; one screen says whether the clock can be trusted.

**Compared with `date`:** date prints the time, and a clock five minutes off looks normal; it cannot say whether the clock is synchronised.

**Trap:** `synchronized: yes` says nothing about which server is used or how big the offset was; with chrony ask `chronyc tracking`. Only one time daemon should run (timesyncd, chrony or ntpd). Containers use the host's clock, so fix it on the host. Cron and `journalctl --since` use the server's zone, not yours.

**Next step:** not synchronised → `timedatectl timesync-status` or `chronyc sources`, then the firewall for UDP 123. Big offset with chrony → `chronyc makestep`. RTC wrong after the fix → `hwclock --systohc`.

### chronyc / ntpq — which time server is used, and how far off is the clock?
Match: chronyc, ntpq, chronyd, ntpdate, ntpstat
Instead of: date, timedatectl (alone)
Safety: read-only · makestep jumps the clock (needs root)

**In one line:** `chronyc` asks the running chrony daemon for its sources and its estimate of the clock error; `ntpq -p` gives the same peer view for the older ntpd.

**Read the command:** `chronyc -n sources -v`

| Part | Meaning |
|---|---|
| `-n` | show IP addresses, do not resolve names (fast, no DNS dependency) |
| `sources` | every configured server and its state |
| `-v` | print a legend that explains each column |
| `tracking` | the clock's offset from true time, stratum, drift, leap status |
| `sourcestats` | per server: estimated offset and its spread |
| `makestep` | step the clock to the right time now instead of slewing slowly |
| `ntpq -p` | ntpd's peer list: `*` marks the selected peer; `reach`, `offset` in ms |

**What the output tells you:**

```
MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^* 169.254.169.123               3   4   377    12   +12us[  +15us] +/-  320us
^? 10.0.1.3                      0   6     0     -     +0ns[   +0ns] +/-    0ns
```

`^*` is the selected server, `^+` a usable one, `^?` unreachable, `^x` a falseticker. `Reach` is octal for the last eight polls: `377` all answered, `0` none ever did. `Last sample` is the measured offset with its error margin.

**Why it is effective:** it separates "no server answers" (firewall, wrong address) from "servers answer but disagree" from "synced, small offset", which `timedatectl`'s single yes/no cannot.

**Compared with `timedatectl`:** timedatectl says whether the kernel clock is synchronised; it does not show which server, whether the others are reachable, or the offset.

**Trap:** with the usual `makestep 1 3` in chrony.conf, chrony steps the clock only in its first updates after start and then slews slowly, so a 5-minute error after a VM resume can last an hour. `makestep` jumps the time, which can confuse running software and log order. `506 Cannot talk to daemon` means chronyd is not running (timesyncd may be the client).

**Next step:** all `^?` or Reach 0 → allow UDP 123 to the servers, or use an internal NTP server. Source selected but big offset → `sudo chronyc makestep`, then `hwclock --systohc`. ntpd hosts → `ntpq -p`. Related: `chronyd -Q 'server pool.ntp.org iburst'` and the legacy `ntpdate -q pool.ntp.org` only measure the offset, never set the clock; `ntpstat` prints one sync line (exit 0 = synchronised).

### cloud-init — has first-boot provisioning finished, and did it fail?
Match: cloud-init
Instead of: checking whether the user, package or file from user-data exists
Safety: read-only for status · clean changes state: removes cloud-init's record and logs so the next boot runs as a first boot (templates only) · needs root for clean

**In one line:** cloud VMs and Proxmox templates are configured at first boot by cloud-init from user-data; `cloud-init status` says whether that is still running, finished, or failed.

**Read the command:** `cloud-init status --long`

| Part | Meaning |
|---|---|
| `status` | `running`, `done`, `error` or `disabled` |
| `--long` | more detail: boot stage, datasource (EC2, NoCloud…), errors |
| `--wait` | block until cloud-init has finished (use it at the start of provisioning scripts) |
| `clean --logs --machine-id` | remove cloud-init's state and logs and reset `/etc/machine-id` to `uninitialized` before making a template |

**What the output tells you:** the first line is the verdict. `status: running` explains apt locks and missing users in the first minutes of a new VM; `status: error` comes with an `errors` list naming the failed module. The output of your own user-data script is in `/var/log/cloud-init-output.log`.

**Why it is effective:** "the user doesn't exist", "nothing listens" and "apt is locked" on a fresh VM are often provisioning that failed or has not finished; one command tells you which.

**Compared with checking the result:** looking for the user, package or file tells you something is missing, not that provisioning failed, or why.

**Trap:** `done` means no cloud-init module failed; it does not prove your application works. `clean` on a running server makes the next boot redo first-boot steps (new SSH host keys and machine-id, user and network setup), so use it only on templates. User-data changed after the first boot is not applied again by default.

**Next step:** error → `/var/log/cloud-init-output.log`, then `/var/log/cloud-init.log`. Scripts racing provisioning → start them with `cloud-init status --wait`. Clones sharing an IP or machine-id → `cloud-init clean --logs --machine-id` in the template.

### update-initramfs / lsinitramfs — rebuild and inspect the early-boot image
Match: update-initramfs, lsinitramfs
Instead of: rebooting and hoping
Safety: update-initramfs changes state: rewrites files in /boot (a broken image can stop the next boot) · lsinitramfs is read-only · needs root

**In one line:** the initramfs is the small root filesystem the kernel starts first to find the real root (storage drivers, LVM, RAID, LUKS); `update-initramfs` rebuilds it, `lsinitramfs` lists what is inside.

**Read the command:** `sudo update-initramfs -u -k all`

| Part | Meaning |
|---|---|
| `-u` | update (rebuild) an existing initramfs |
| `-k all` | for every installed kernel; without `-k`, only the newest |
| `-c -k 6.8.0-85-generic` | create one for a kernel that has none (e.g. after a failed install) |
| `lsinitramfs /boot/initrd.img-6.8.0-85-generic` | list the files in that image |

**What the output tells you:**

```
update-initramfs: Generating /boot/initrd.img-6.8.0-85-generic
update-initramfs: Generating /boot/initrd.img-6.8.0-79-generic
```

One line per kernel. `update-initramfs: failed for /boot/initrd.img-… with 1` usually means a full `/boot`.

**Why it is effective:** anything needed at early boot (a storage driver, `mdadm.conf`, `crypttab`, module options for the root disk) takes effect only once it is in the image, and `lsinitramfs | grep` proves it is there.

**Compared with rebooting to see:** an image without the right driver drops you at an `(initramfs)` BusyBox prompt, far from your SSH session.

**Trap:** `/boot` is often a small partition: check `df -h /boot` first. Keep a known-good older kernel and image to boot from the GRUB menu. RHEL uses `dracut -f` and `lsinitrd` instead.

**Next step:** `/boot` full → `sudo apt autoremove --purge` (never remove the running kernel, `uname -r`). Driver missing from the image → add it to `/etc/initramfs-tools/modules`, rebuild, check with `lsinitramfs`.

### needrestart — what still runs old code after updates?
Match: needrestart, needs-restarting, checkrestart
Instead of: ls /var/run/reboot-required
Safety: read-only with -r l · in interactive or automatic mode it can restart services, including containerd and so every container · needs root

**In one line:** after `apt upgrade`, running daemons keep the old libraries in memory until they restart; `needrestart` finds them, and compares the running kernel with the newest installed one.

**Read the command:** `sudo needrestart -r l -b`

| Part | Meaning |
|---|---|
| `-r l` | restart mode **list**: report only, restart nothing (`i` = ask, `a` = automatic) |
| `-b` | batch mode: machine-readable `NEEDRESTART-*` lines |
| `NEEDRESTART-KCUR` · `KEXP` | the running kernel · the newest installed kernel |
| `NEEDRESTART-KSTA` | 1 = current, 2 = ABI-compatible update pending, 3 = new kernel version pending (reboot), 0 = unknown |
| `NEEDRESTART-SVC` | a service still using outdated libraries |

**What the output tells you:**

```
NEEDRESTART-VER: 3.6
NEEDRESTART-KCUR: 6.8.0-79-generic
NEEDRESTART-KEXP: 6.8.0-85-generic
NEEDRESTART-KSTA: 3
NEEDRESTART-SVC: containerd.service
NEEDRESTART-SVC: ssh.service
```

A reboot is pending for the new kernel, and containerd and ssh still run old library code: the security fix is installed but not active yet.

**Why it is effective:** "patched" and "running patched code" are different things; this is the list of what must restart (or the reboot) for the update to take effect, and it restarts nothing yet.

**Compared with `/var/run/reboot-required`:** that file appears when a package asks for a reboot, and `.pkgs` names the package; it says nothing about services still running old libraries.

**Trap:** without `-r l`, interactive runs ask (and hang unattended scripts), and automatic mode restarts services itself, which on a Docker or Kubernetes host restarts every container. Defaults differ between Ubuntu releases: check `$nrconf{restart}` under `/etc/needrestart/`.

**Next step:** services listed → restart them in a window (drain the node first for containerd). `KSTA: 3` → plan the reboot. apt in scripts → `NEEDRESTART_MODE=l` with `DEBIAN_FRONTEND=noninteractive`. Related: on RHEL, `needs-restarting -r` exits 1 when a reboot is needed (`-s` lists services to restart); `checkrestart` (debian-goodies) is the older Debian tool needrestart replaced.

### reboot / shutdown — restart the machine cleanly (Linux and Windows)
Match: reboot, shutdown, systemctl reboot, poweroff
Instead of: a hard power cycle from the hypervisor or BMC
Safety: changes state: stops every service and restarts the host · needs root (Administrator on Windows)

**In one line:** on Linux `reboot` asks systemd to stop all services in order, unmount filesystems and restart; on Windows `shutdown /r` does the same, with options for a delay or the recovery menu.

**Read the command:** `shutdown /r /o /t 0`

| Part | Meaning |
|---|---|
| `shutdown /r` | Windows: restart |
| `/o` | Windows: restart into the advanced boot options (recovery) menu; only with `/r` |
| `/t 0` | Windows: after 0 seconds (default 30) |
| `sudo reboot` | Linux: reboot now; the same as `systemctl reboot` |
| `shutdown -r +5 "kernel update"` | Linux: reboot in 5 minutes and warn logged-in users; `shutdown -c` cancels |

**What the output tells you:** nothing useful: the session ends. Check afterwards with `uptime -s`, `last -x reboot | head`, and `journalctl -b -1 -e` for how the previous boot ended.

**Why it is effective:** a clean reboot lets databases flush, services stop with their own stop commands and filesystems unmount, so the host comes back without fsck or crash recovery.

**Compared with a hard power cycle:** a reset from the hypervisor or BMC works when the host hangs, but nothing stops cleanly; use it only when a clean reboot is impossible.

**Trap:** after kernel, GRUB, fstab or network changes the host may not come back: secure console or BMC access first. Check `who`, announce it, and make sure you are in the right terminal (the `molly-guard` package asks for the hostname before a reboot over SSH). `/t 0` gives Windows users no warning.

**Next step:** after the reboot → `systemctl --failed`, `uname -r` (new kernel?), your service checks. Unexpected reboots → `last -x`, `journalctl -b -1 -p err`, the BMC event log. Related: `poweroff` switches the machine off at once (`systemctl poweroff`): the last step when sealing a VM template, never on a host nobody can power on again.
