# Shell building blocks: files, variables, loops & scripts

These are the words around the real tools in almost every example of this handbook: printing (`echo`, `printf`), copying and replacing files safely (`cp -a`, `install`, `mv`, `ln`), repeating a check (`for`, `while read`, `seq`, `sleep`), and making scripts and environments behave (`set`, `trap`, `export`, `bash -c`). When a line confuses you, ask three questions: which shell runs each part (yours, a `sudo sh -c` root shell, or one inside a container), what each quote protects, and which file it changes.

| If you would reach for | Prefer | Because |
|---|---|---|
| `sudo echo x > /etc/file` | `echo x | sudo tee /etc/file`, or `sudo sh -c '… > /etc/file'` | your own shell opens the `>` file, without root |
| `echo -e` for a report | `printf '%-22s %s\n' "$a" "$b"` | the same bytes in every shell, in aligned columns |
| editing a live config in place | `cp -a` a backup, `install` a `.tmp` copy with the right mode, then `mv` it over | owner and mode stay right, and no program reads a half-written file |
| `which docker` | `type -a docker` | it shows aliases, functions and every copy on `PATH`, first one wins |
| `cat FILE | while read line` | `while IFS= read -r line; do …; done < FILE` | no subshell, so variables survive, and backslashes stay |
| a script with no error handling | `set -Eeuo pipefail` plus `trap … EXIT` | it stops at the first failure and still cleans up |
| `export PASSWORD=…` typed in the shell | `read -rsp 'Password: ' PW`, use `"$PW"`, then `unset PW` | nothing lands in `~/.bash_history` |
| `rm -rf "$DIR"/*` | `rm -rf -- "${DIR:?}"/*` after listing what it matches | an empty `DIR` aborts instead of becoming `/*` |

### echo / printf — print a line, or a formatted report with aligned columns
Match: echo, printf
Instead of: echo -e
Safety: read-only · a `>` after them writes a file, opened by your own shell even under sudo

**In one line:** `echo` prints its arguments plus a newline; `printf` fills a format (`%s` text, `%d` number), so columns line up and every shell prints the same bytes.

**Read the command:** `printf '%-22s https=%s  http=%s  %s\n' "$name" "$https" "$http" "$cert"`

| Part | Meaning |
|---|---|
| `'%-22s …\n'` | the format: `%-22s` is the next argument, left-aligned, 22 wide; `\n` is the only newline |
| `"$name" …` | one argument per `%s`, quoted so spaces do not split it |
| `printf '%s\n' a b c` · `printf '%d' 0x0CEA` | one line per argument · `%d` reads hex: `3306` (a port in `/proc/net/tcp`) |
| `echo -n` · `echo -e` | no final newline · expand `\t`, `\n` (bash; Ubuntu's `sh` always expands them) |

**What the output tells you:**

```
shop.example.com       https=200  http=301->https://shop.example.com/  issuer=… CN = R11 …
wiki.example.com       https=000  http=301->https://wiki.example.com/  issuer=CN = TRAEFIK DEFAULT CERT …
```

The odd line stands out: wiki gets Traefik's default certificate, so none was issued.

**Why it is effective:** a loop becomes a report to scan, sort or paste into a ticket; `printf '%s\n' "$x"` prints any value exactly, even `-n` or a backslash, which `echo` may misread.

**Compared with `echo -e`:** fine for a quick line, but options and escapes differ between bash, dash (`sh`) and `/bin/echo`.

**Trap:** `printf "$var"` turns data into the format: a `%` in it garbles the line. `echo "$secret" | base64` encodes a trailing newline. `sudo echo x > /etc/file` fails: your shell opens the file before sudo runs (see `tee`).

**Next step:** align existing output → `column -t`. Build JSON → `jq -n`, never echo.

### cp / mv / install — back up before an edit, create a file with its mode, swap it in atomically
Match: cp, mv, install
Instead of: editing the live file in place, cp then chmod
Safety: changes state: all three overwrite an existing target without asking · under /etc they need sudo

**In one line:** `cp -a` copies with owner, mode and times, the backup before any change; `install` copies and sets the mode in one step; `mv` within a filesystem renames: readers see the old file or the new, never half.

**Read the command:** `sudo install -m 600 ~/case-web01/legacy-apache.yml /etc/dokploy/traefik/legacy-apache.yml.tmp && sudo mv /etc/dokploy/traefik/legacy-apache.yml.tmp /etc/dokploy/traefik/dynamic/legacy-apache.yml`

| Part | Meaning |
|---|---|
| `install -m 600 SRC DEST` | copy with mode 600 (owner read and write) from the start |
| `….tmp`, then `&& sudo mv` | written beside the watched directory, same filesystem; if that worked, renamed into it |
| `cp -a FILE FILE.pre-window` | backup with owner, mode, times and links; reversed, it is the rollback |
| `cp -L` · `install -d -m 700 DIR` | copy what a symlink points to (Let's Encrypt's `live/`) · a directory with that mode |

**What the output tells you:** nothing on success; `sudo stat -c '%a %U:%G %n' FILE` should print `600 root:root …`.

**Why it is effective:** a program watching a directory (Traefik, node_exporter) can read a half-written file; a rename swaps it whole, and `cp -a` makes the rollback one command.

**Compared with `cp` then `chmod`:** same end state, but for a moment a key has default permissions.

**Trap:** `mv` across filesystems (from a tmpfs `/tmp`) is copy-and-delete, not atomic. A moved file keeps its own owner, mode and SELinux label, not the replaced file's (`restorecon` on RHEL). `cp` without `-a` gives a new copy your ownership and a fresh time. None of them asks before overwriting.

**Next step:** after the swap → the service's log. Prove an edit → `diff -u FILE.pre-window FILE`.

### mkdir / touch / ln / rm / rmdir — create paths, flip a release symlink, delete exactly what you meant
Match: mkdir, touch, ln, rm, rmdir
Instead of: rm -rf on a path built from a variable
Safety: changes state: `rm` deletes at once (no trash), `ln -f` replaces the existing link

**In one line:** `mkdir -p` creates a directory and its parents, `touch` an empty file, `ln -s` a symlink, the switch between releases; `rm` and `rmdir` delete for good.

**Read the command:** `ln -sfn /srv/docs/releases/2026-09-28 /srv/docs/current`

| Part | Meaning |
|---|---|
| `-s` · `-f` | symbolic: stores the target path as text · replace an existing link (else `File exists`) |
| `-n` | replace a link to a directory; without it, ln puts the new link *inside* the old release |
| `mkdir -p DIR` · `touch FILE` | parents too, no error if it exists · an empty file: proof you may write there |
| `rm -f FILE` · `rmdir DIR` | delete, silent if missing · remove an empty directory |

**What the output tells you:**

```
lrwxrwxrwx 1 deploy deploy   29 Sep 28 12:01 current -> /srv/docs/releases/2026-09-28
drwxr-xr-x 3 deploy deploy 4096 Sep 28 12:01 releases
```

In `ls -l /srv/docs/`, `->` shows what is live; the rollback is the same `ln -sfn` with the previous date.

**Why it is effective:** going live and rolling back are one reviewable command each, and old releases stay untouched.

**Compared with `rm -rf` on a variable path:** `rm -rf "$DIR"/` with an empty `DIR` is `rm -rf /`, which GNU rm refuses (`--preserve-root`); `rm -rf "$DIR"/*` becomes `rm -rf /*`, which it runs. `"${DIR:?}"` aborts when empty.

**Trap:** a relative target counts from the link's directory: `ln -sf ../run/systemd/resolve/stub-resolv.conf /etc/resolv.conf` means `/run/…`. Deleting a file a process holds open frees no space (`lsof +L1`).

**Next step:** wrong target → `readlink -f`. Before deleting a tree → `find "${DIR:?}" -mindepth 1 -maxdepth 1 -print`.

### cd / pwd / type / which / history — where am I, what runs when I type a name, what did I run?
Match: cd, pwd, type, which, history
Instead of: which
Safety: read-only · `cd` changes only this shell's directory

**In one line:** `cd` and `pwd` set and show the directory relative paths start from; `type -a` shows what a name really is: alias, function, builtin or file on `PATH`; `history` lists past commands.

**Read the command:** `type -a docker`

| Part | Meaning |
|---|---|
| `-a` | every match, in the order bash tries them: the first one runs |
| `which -a python3` · `command -v terraform` | every file on `PATH` · what bash would run (exit 1 if nothing), for scripts |
| `cd DIR || exit 1` · `cd -` · `pwd -P` | enter or stop the script · back to the last directory · the real path, symlinks resolved |
| `history | tail -3` | the last commands, timestamped once `HISTTIMEFORMAT='%F %T '` is set |

**What the output tells you:**

```
$ type -a docker
docker is /usr/bin/docker
docker is /bin/docker
docker is /snap/bin/docker
```

The first runs. `/bin` links to `/usr/bin` on current Ubuntu (one file); `/snap/bin/docker` is a second install with its own daemon.

**Why it is effective:** "command not found", a wrong version or odd behaviour is often a lookup problem, solved here before you debug the tool.

**Compared with `which`:** paths only, blind to aliases, functions and builtins: on Ubuntu `which cd` finds nothing, yet `cd` works.

**Trap:** sudo has its own `secure_path` (`sudo sh -c 'command -v docker'`), and `sudo cd` fails: `cd` is a builtin. bash caches paths (`hash -r`). History is per terminal, saved at exit, editable: no audit log.

**Next step:** wrong copy first → remove it (`dpkg -S`, `snap list`) or fix `PATH`. Not found → `apt-file search bin/NAME`.

### for / while read / case — repeat a check for every host, line or value, and branch on the result
Match: for, done, read, case, esac, fi, test, true, false, continue, break, shift, local, return
Instead of: cat FILE | while read line, for x in $(cat FILE)
Safety: read-only themselves · the body runs once per item, changes included

**In one line:** `for` runs a body once per word, `while read` once per input line, `case` takes the first matching pattern, `if` branches on an exit status; `done`, `esac`, `fi` close them.

**Read the command:** `for h in app.example.com shop.example.com legacy.example.com; do printf '%-22s ' "$h"; curl -sS -o /dev/null -m 10 -w '%{http_code}\n' "https://$h/" 2>&1; done`

| Part | Meaning |
|---|---|
| `for h in …; do … done` | `h` takes each word in turn; quote it: `"$h"` |
| `curl … 2>&1` | status code per host, errors included (see `curl`) |
| `while read -r h p; do … done < FILE` | one round per line, split into fields, the last taking the rest; `-r` keeps backslashes |
| `case $1 in start|stop) … ;; *) … ;; esac` | the first matching pattern wins; `*)` catches the rest |

**What the output tells you:**

```
app.example.com        502
shop.example.com       200
legacy.example.com     200
```

Only `app` fails behind the same proxy: the shared layers work, so look at what is unique to it.

**Why it is effective:** one paste checks every host the same way: a comparison instead of an anecdote, rerun after the fix.

**Compared with `cat FILE | while read line`:** works, but the loop runs in a subshell, so variables set inside are lost; `done < <(cmd)` avoids that.

**Trap:** `for x in $(cat FILE)` splits on spaces and expands `*`. Inside `while read`, `ssh` swallows the remaining lines: use `ssh -n`. A glob matching nothing stays literal.

**Next step:** many hosts → `xargs -P` or Ansible. Long runs → `tmux`, output `>> FILE`. Related builtins: `test EXPR` (same as `[ EXPR ]`) and `true`/`false` give the exit status that `if`/`while` test; `continue`/`break` skip or leave a loop; `shift` drops `$1` in argument loops; `local` and `return` work inside shell functions.

### sleep / seq — pace a sampling loop, count its rounds, wait between retries
Match: sleep, seq
Instead of: while true without an end
Safety: read-only themselves

**In one line:** `seq` prints a range of numbers, so `for i in $(seq 1 288)` runs 288 rounds; `sleep` pauses between them: a sampler with a known interval and end.

**Read the command:** `for i in $(seq 1 288); do …; sleep 300; done >> ~/conn-sample-$(hostname)-$(date +%F).csv`

| Part | Meaning |
|---|---|
| `seq 1 288` | 1 to 288, one per line |
| `sleep 300` | wait 5 minutes: 288 rounds ≈ 24 hours (`0.5` and `2m` work too) |
| `done >> FILE` | append the loop's whole output to one file, named once at the start |
| `until CMD; do sleep 2; done` · `timeout 60 CMD` | retry until CMD succeeds · stop CMD after 60 s (exit status 124) |

**What the output tells you:**

```
2026-10-03T10:25:00+00:00,3,18,4,0,1
2026-10-03T10:30:00+00:00,2,22,5,0,0
```

One row per round: a timestamp, then connections per port. Fewer than 288 rows after a day means the loop died.

**Why it is effective:** a fixed interval and count make samples comparable, and the run ends by itself: leave it in `tmux` overnight.

**Compared with `while true; do …; sleep 60; done`:** fine while watching, but endless: a forgotten one keeps growing a file or hitting an endpoint.

**Trap:** each round lasts the sleep plus the body, so samples drift and 288 rounds exceed 24 hours: stamp each row with `date`. `until` waits forever if the service never comes up: `timeout 120 bash -c 'until …; do sleep 2; done'`. A loop in a plain SSH session dies with it.

**Next step:** longer → a systemd timer or real metrics (node_exporter). Reading rows → `column -s, -t`.

### set -euo pipefail / trap / exit — make a script stop at the first failure, say where, and clean up
Match: set, trap, exit
Instead of: a script without error handling
Safety: changes state: options and traps of the running shell · `exit` in your login shell or a sourced file closes that shell

**In one line:** `set` switches shell options; `trap` runs code when the script exits or fails; `exit N` ends it with a status the caller can test.

**Read the command:** `set -Eeuo pipefail`

| Part | Meaning |
|---|---|
| `-e` | exit when a command fails (not in `if`/`while` tests, before `&&`/`||`, after `!`) |
| `-u` | unset variables are errors: a typo like `$DRI` stops the script |
| `-o pipefail` | any failing part fails the pipeline: `mysqldump … | gzip > FILE` cannot hide a failed dump |
| `-E` | `ERR` traps also fire inside functions and subshells |
| `trap 'rm -rf "$TMP"' EXIT` · `trap '… $LINENO …' ERR` | clean up however bash exits (not after `kill -9`) · name the failing line |

**What the output tells you:**

```
$ ./deploy.sh; echo "exit=$?"
./deploy.sh: line 6: cd: /srv/app: No such file or directory
failed at line 6
exit=1
```

The error, the line from the ERR trap, and a non-zero status for cron or CI.

**Why it is effective:** without `-e`, a failed `cd` lets the next line run in the wrong directory and the script still "succeeds"; strict mode stops at the cause.

**Compared with no options:** the default suits typing: errors print and the next command runs anyway.

**Trap:** `-e` ignores failures inside `if`, `&&` and `local x=$(cmd)`, yet stops on expected ones: `grep` finding nothing, `(( n++ ))` while n is 0 (add `|| true`). `set -x` prints secrets into CI logs.

**Next step:** stops silently → `bash -x script.sh`. Lint → `shellcheck`. Unattended → `flock`, a systemd timer with `OnFailure=`.

### export / unset / printenv / source — which variables a program really gets, and how to load or clear them
Match: export, unset, printenv, source, eval
Instead of: typing secrets into export, expecting sudo to keep your variables
Safety: changes state: this shell and the programs it starts later · nothing persists unless written to a file such as `~/.bashrc`

**In one line:** `export` puts a variable into the environment that every child program inherits (`KUBECONFIG`, `AWS_PROFILE`); `unset` removes it, `printenv` lists exported ones, `source FILE` runs FILE in this shell.

**Read the command:** `export KUBECONFIG=~/.kube/config:~/.kube/lab.config`

| Part | Meaning |
|---|---|
| `export NAME=value` | set and export: kubectl, started later from here, sees it |
| `~/…:~/…` | a list; bash expands each `~` here, but not inside quotes |
| `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY` | drop leftover keys, which beat `AWS_PROFILE` |
| `printenv DATABASE_URL` | one exported value (exit 1 if unset); alone, all of them |
| `source ~/.bashrc` · `set -a; . FILE; set +a` | apply a file to this shell · and export everything it assigns |

**What the output tells you:**

```
$ printenv | grep -E '^(KUBECONFIG|AWS_)'
KUBECONFIG=/home/ops/.kube/config:/home/ops/.kube/lab.config
AWS_PROFILE=lab-admin
```

Tildes expanded, no stray `AWS_ACCESS_KEY_ID` overriding the profile. A variable you set but cannot see here is not exported.

**Why it is effective:** "works in my shell, fails in cron, sudo or CI" is usually a missing or extra variable; `printenv` in each place shows which.

**Compared with typing `export PGPASSWORD=…`:** works, but the value lands in `~/.bash_history`; `read -rsp 'Password: ' PW` or `"$(pass show lab/pve-token)"` keeps it out, then `unset PW`.

**Trap:** sudo resets the environment (`env_reset`) and `PATH` (`secure_path`), so `sudo aws …` ignores your `AWS_PROFILE`; `sudo VAR=value cmd` passes one. An exported secret reaches every child process and `/proc/PID/environ`. `source` runs code: read an env file first. dash (`sh`) knows only `.`.

**Next step:** fails only in cron or systemd → compare `printenv` there (`Environment=`). Service secrets → `EnvironmentFile=` with mode 600. Related: `eval "$(ssh-agent)"` runs a command's output as shell code in this shell, so a tool can set variables here; like `source`, only for output you trust.

### bash / sh — run a script or a quoted command line in a new shell: as root, traced, or syntax-checked
Match: bash, sh
Instead of: sudo cmd with a glob or redirect into a root-only path
Safety: changes state: whatever the script or string does · under sudo, all of it runs as root

**In one line:** `bash FILE` runs a script in a new bash, no execute bit needed; `sh -c 'STRING'` runs a command line in a new shell, so after `sudo` its globs and redirects run as root.

**Read the command:** `sudo sh -c 'du -h /var/lib/docker/containers/*/*-json.log' | sort -h | tail -5`

| Part | Meaning |
|---|---|
| `sudo sh -c '…'` | a root shell expands the `*`, in a directory only root can read |
| single quotes | your shell passes the string as is; in double quotes it would expand `$VAR` first |
| `| sort -h | tail -5` | outside the quotes: runs as you; biggest last |
| `bash -n FILE` · `bash -x FILE` | syntax only, nothing runs · run, printing each expanded command after `+` |

**What the output tells you:**

```
12M     /var/lib/docker/containers/3f9c…/3f9c…-json.log
7.9G    /var/lib/docker/containers/9c2d…/9c2d…-json.log
```

The directory is the container ID; gigabytes mean no `max-size` log option.

**Why it is effective:** after `sudo cmd`, pipes, redirects and globs still belong to your shell; `sudo sh -c` moves them into the root shell.

**Compared with `sudo du -h /var/lib/docker/containers/*/*-json.log`:** your shell cannot read the directory, so the pattern stays literal and du says `No such file or directory`.

**Trap:** Ubuntu's `sh` is dash: `[[ ]]`, arrays, `source` and `echo -e` fail or differ, so run bash scripts with `bash`. `bash -n` misses misspelt commands; `-x` prints secrets. In `sh -c "…"` your shell expands first.

**Next step:** failing script → `bash -x`, then `shellcheck`. Root only for a file → `sudo tee`. Containers → `docker exec CTR sh -c '…'` (many images lack bash).

### python3 — validate JSON or YAML, serve a test page, do subnet maths
Match: python3
Instead of: eyeballing a JSON or YAML file before a restart
Safety: read-only for `-m json.tool` and the `-c` checks · `-m http.server` publishes the current directory until Ctrl-C

**In one line:** Ubuntu servers ship `python3`: `-m json.tool` proves JSON parses, `-c '…'` runs a short program (YAML check, subnet maths), `-m http.server` serves a directory as a test backend.

**Read the command:** `sudo python3 -m json.tool /etc/docker/daemon.json >/dev/null && echo "JSON syntax OK"`

| Part | Meaning |
|---|---|
| `-m json.tool FILE` | parse and pretty-print; on a syntax error print line and column, exit 1 |
| `>/dev/null` · `&& echo …` | hide the pretty copy · OK only if parsing worked |
| `-c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' FILE` | the same check for YAML; `sys.argv[1]` is FILE |
| `-m http.server 80 --bind 10.10.2.20` | serve the current directory on port 80 (root below 1024), on that address only |

**What the output tells you:**

```
Expecting property name enclosed in double quotes: line 6 column 1 (char 112)
```

Usually a comma after an object's last entry (end of line 5): JSON forbids it, and dockerd would not start.

**Why it is effective:** one stray comma in `daemon.json` or a Traefik YAML file takes down Docker or routes; the check costs a second.

**Compared with eyeballing the file:** a trailing comma or a tab in YAML indentation is easy to miss, and the service complains only after the restart.

**Trap:** valid syntax is not valid configuration: a misspelt key parses fine. `import yaml` needs `python3-yaml`, absent from slim images. `http.server` serves every file in the directory, `.env` and keys included, to anyone reaching the port.

**Next step:** JSON valid → `sudo dockerd --validate --config-file /etc/docker/daemon.json`, then restart. Test server answers, the app does not → look at the app.

### script / nano — record the whole terminal session for the incident log; edit a small file
Match: script, nano
Instead of: copying terminal output by hand
Safety: changes state: `script` writes its log file (`-a` appends) · `nano` rewrites the file when you save

**In one line:** `script` starts a new shell and records everything shown in the terminal, commands and output, into a file until you type `exit`; `nano` is the simple editor the handbook uses for small edits.

**Read the command:** `script -q -a inventory-$(date +%F).log`

| Part | Meaning |
|---|---|
| `-q` · `-a` | no start and done messages · append, so a second session does not overwrite the first |
| `$(date +%F)` | today's date in the name: `inventory-2026-10-03.log` |
| `exit` or Ctrl+D | end the recording |
| `sudo nano FILE` · `nano -B FILE` | Ctrl+O saves, Ctrl+X quits, Ctrl+W searches · keep the old version as `FILE~` |

**What the output tells you:**

```
ops@web01:~/case-web01$ date +%T; sudo cp -a /etc/apache2/ports.conf /etc/apache2/ports.conf.pre-window
22:00:03
```

Prompt, command and output as they appeared: the change window's timeline. Colours and full-screen programs leave escape codes: read the log with `less -R`.

**Why it is effective:** the postmortem timeline comes from what really happened, including errors nobody noticed, not from memory.

**Compared with copying output by hand:** you keep only what looked important then; `history` keeps commands without output or, by default, times.

**Trap:** everything on screen is recorded: a printed secret (`printenv`, `cat .env`) is now in a file, so keep logs private and redact before sharing. A forgotten `exit` leaves you recording in a nested shell. `sudo nano` runs the editor as root; `sudoedit` edits a copy as you.

**Next step:** session over → link the log in the ticket. File edited → validate (`python3 -m json.tool`, `netplan try`, `nginx -t`), then reload.
