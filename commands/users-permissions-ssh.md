# Users, permissions, SSH & hardening

Most "Permission denied" and "cannot log in" problems come down to four questions, in this order: which identity is really asking (`id`, `getent`), what the file and every directory above it allow (`namei -l`, `chmod`, `chown`, ACLs), whether a second layer (account locks, SELinux, AppArmor, capabilities) refuses anyway, and, for SSH, what the server decided and why (`ssh -v` on the client, `sshd -T` and the server log). Make the narrowest change that fixes it, and turn to the login records and the audit log when the question becomes "who did this?".

| If you would reach for | Prefer | Because |
|---|---|---|
| `chmod 777` for "Permission denied" | `namei -l /full/path`, then `chown` or `setfacl -m u:USER:rX` | the block is usually one directory or a wrong owner; 777 opens the file to everyone and hides the cause |
| `sudo vim /etc/apache2/ports.conf` | `sudoedit /etc/apache2/ports.conf` | your editor runs as you, not as root, and a sudoers rule can allow exactly that file |
| `grep deploy /etc/passwd`, `grep docker /etc/group` | `getent passwd deploy`, `getent group docker` | getent goes through NSS like login and sudo do, so LDAP and SSSD accounts appear too |
| `dig app.example.com` to see what the app gets | `getent ahosts app.example.com` | it follows `/etc/hosts` and nsswitch.conf like programs do; dig asks DNS only |
| `id` right after `usermod -aG docker ops` | `id ops`, then log in again | plain `id` shows the groups your session received at login |
| `ssh user@host` again and again | `ssh -v user@host`, plus `journalctl -u ssh` on the server | the client shows which key it offered; only the server log says why it was refused |
| `cat /etc/ssh/sshd_config` | `sudo sshd -T`, and `sudo sshd -t` before every reload | drop-ins are read first and the first value wins; `-t` stops a broken config from going live |
| `setenforce 0` to "fix" SELinux | `ausearch -m AVC -ts recent`, then a label, port or boolean | one targeted change instead of switching protection off for the whole host |

### id / whoami — which user and groups does this session, or that account, really have?
Match: id, whoami, groups
Instead of: groups, grep USER /etc/group
Safety: read-only

**In one line:** `id` prints the numeric identity the kernel checks (UID, primary GID and every supplementary group, each with its name); `whoami` prints only the effective user name.

**Read the command:** `id deploy`

| Part | Meaning |
|---|---|
| `id` | no argument: the identity of **this process**, i.e. the groups your session received at login |
| `deploy` | an account: its groups as the user and group databases list them **now** |
| `-u` / `-g` | only the numeric UID / primary GID, for scripts: `[ "$(id -u)" -eq 0 ]` means "running as root" |
| `-nG` | only the group names, on one line |
| `whoami` | the effective user name (`id -un`); under `sudo` it prints `root` |
| `whoami /user /groups` | Windows: your SID and group memberships, including whether the prompt is elevated |

**What the output tells you:**

```
$ id
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),27(sudo)
$ id deploy
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),27(sudo),988(docker)
$ docker ps
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: …
```

`uid=` is who you are, `gid=` the primary group (new files get it), `groups=` every group the kernel accepts in permission checks. The account is in `docker`, but this session is not: it started before `usermod -aG docker deploy`, so the socket (`660 root:docker`) still refuses it.

**Why it is effective:** permissions are decided by numbers, not names, and `id` shows exactly the UID and GIDs a process carries. Comparing `id` with `id USER` explains the most common "I added the group and it still fails".

**Compared with `groups`:** groups prints the same group names (for the session, or for a user with `groups USER`), enough for a glance, but no UIDs, GIDs or primary group. `grep USER /etc/group` misses directory (LDAP, SSSD) groups and the primary group.

**Trap:** a session's groups are fixed at login; `usermod` changes only the database. Daemons keep the groups they started with until they restart. Inside a container, `id` shows the container's users: UID 999 there may have another name, or none, on the host. `sudo id` reports root, not you.

**Next step:** group in `id USER` but not in `id` → log out and in again, restart the service. Missing in both → `usermod -aG GROUP USER`. Files owned by a bare number → `ls -ln`, then `chown` to the UID the process uses (`docker exec CTR id`, `ps -o user,uid -p PID`). Related: `groups` (or `groups USER`) prints only the group names.

### getent passwd / group — does this account or group exist, and what does the system know about it?
Match: getent passwd, getent group, getent
Instead of: cat /etc/passwd, grep docker /etc/group
Safety: read-only · `getent shadow` needs root

**In one line:** `getent` asks the system's name service switch (NSS) for an entry: the same lookup login, sudo, sshd and `ls -l` use, so it sees local accounts and directory accounts (LDAP, SSSD, Active Directory) alike.

**Read the command:** `getent group sudo docker`

| Part | Meaning |
|---|---|
| `group` | the group database: `/etc/group` plus any directory source listed in `/etc/nsswitch.conf` |
| `sudo docker` | one or more keys (names or numbers); no key lists the whole database |
| `passwd appuser` | the account: UID, primary GID, home directory and login shell |
| `shadow deploy` | password hash and ageing fields of a local account (root only) |
| `services 443 53/udp` | the service name for a port, from `/etc/services` |
| `hosts`, `ahosts` | names to addresses: see the next card |
| exit status `2` | a key was not found; scripts use it: `getent passwd app >/dev/null || useradd …` |

**What the output tells you:**

```
$ getent group sudo docker
sudo:x:27:ops,deploy
docker:x:988:deploy
$ getent passwd appuser
appuser:x:1002:1002:App service:/srv/app:/usr/sbin/nologin
```

Group lines are `name:x:GID:members`. Passwd lines are `name:x:UID:GID:comment:home:shell`; `x` means the hash lives in shadow, and a `nologin` shell is why `su - appuser` answers "This account is currently not available."

**Why it is effective:** it answers with the system's own view, whichever source an account comes from, one line per key, easy to script. On a host joined to a directory, most users are simply not in `/etc/passwd`.

**Compared with `cat /etc/passwd`:** reading the files is fine on a standalone server, where getent returns the same lines, but it misses every directory account and never shows what NSS actually resolved.

**Trap:** the member list holds only **supplementary** members: a user whose primary group is `docker` does not appear after the last colon. With SSSD, listing a whole database (`getent passwd` without a key) usually omits directory users (enumeration is off by default), and answers are cached, so a directory change shows up only after the cache expires (`sss_cache -E`). getent reads databases; whether a running session has the group is `id`'s question.

**Next step:** account missing → `useradd` or `adduser`, or the SSSD or LDAP configuration. Wrong shell → `usermod -s`. User missing from a group → `usermod -aG GROUP USER`, then a new login. Account present but logins refused → `passwd -S`, `chage -l`.

### getent hosts / ahosts — what does a normal program on this host get for this name?
Match: getent hosts, getent ahosts
Instead of: dig name, nslookup name
Safety: read-only · may send DNS queries

**In one line:** `getent ahosts NAME` resolves a name the way most programs on this host do, through NSS (`/etc/nsswitch.conf`): `/etc/hosts`, then DNS (systemd-resolved, or a container's DNS), plus mDNS if configured. DNS-like resolution, not a DNS query.

**Read the command:** `getent ahosts app.example.com`

| Part | Meaning |
|---|---|
| `ahosts app.example.com` | resolve with `getaddrinfo()`, as curl, Apache and most clients do: every IPv4 and IPv6 address, preferred first |
| `hosts NAME` | the older lookup: shorter, but one address family only (IPv6 if the name has any) |
| `hosts 198.51.100.23` | reverse: the name this address maps to |
| `-s files hosts NAME` | ask only `/etc/hosts` |
| `-s dns hosts NAME` | ask only DNS, the way glibc does it (resolv.conf, search domains) |
| exit status `2` | no source knew the name: it does not resolve **here** |

**What the output tells you:**

```
$ getent ahosts app.example.com
192.0.2.99      STREAM app.example.com
192.0.2.99      DGRAM
192.0.2.99      RAW
$ getent -s files hosts app.example.com
192.0.2.99      app.example.com
$ getent -s dns hosts app.example.com
192.0.2.10      app.example.com
```

`ahosts` prints each address once per socket type, preferred first. Asking each source separately shows the cause: DNS says .10, a forgotten `/etc/hosts` line says .99, and `files` comes first in nsswitch.conf's `hosts:` line, so every program here goes to .99.

**Why it is effective:** "dig is right but the app goes elsewhere" is nearly always outside DNS: an `/etc/hosts` override, a missing search domain, `.local` names swallowed by `mdns4_minimal [NOTFOUND=return]`, a container's own resolv.conf. getent follows the application's path, so it reproduces its answer.

**Compared with `dig`:** dig (and nslookup) show what one DNS server answers; dig adds the TTL, the status (`NXDOMAIN`, `SERVFAIL`) and the server used: the right tool for DNS itself. Both ignore `/etc/hosts` and nsswitch, so they can disagree with every program on the host. getent shows no TTL, status or server.

**Trap:** getent answers for **this** host or container: for a container, run it inside (`docker exec CTR getent hosts db`). `hosts` shows one family, so an IPv6 answer can hide the IPv4 address clients reach: prefer `ahosts`. Programs that cache names (the JVM, nginx resolving `proxy_pass` at start) can keep using an old address.

**Next step:** wrong address from `files` → fix `/etc/hosts`. Exit 2 but dig works → the `hosts:` line (`.local`, mDNS), search domains (`dig +search`). Right address but the app fails → `curl -v`, the app's cache or proxy.

### useradd / adduser — create a service account or a person's login
Match: useradd, adduser
Instead of: editing /etc/passwd by hand
Safety: changes state: creates the account and its group, and with `-m` (or adduser) a home directory · needs root

**In one line:** `useradd` is the low-level, scriptable account creator found on every distribution; Debian and Ubuntu add `adduser`, a friendlier wrapper that creates the home directory, copies the skeleton files and asks for a password.

**Read the command:** `useradd --system --home-dir /srv/demo --shell /usr/sbin/nologin demo`

| Part | Meaning |
|---|---|
| `--system` | a system account: UID below 1000, no password ageing, no home directory created |
| `--home-dir /srv/demo` | the home field (the service's working directory); this command does not create it |
| `--shell /usr/sbin/nologin` | no interactive login: `su` and SSH shells are refused |
| `demo` | the account name; a group `demo` is created with it |
| `-m -s /bin/bash ci` | a login account (people, CI runners): home created from `/etc/skel`, a real shell |
| `-M` / `-G sudo` | no home directory / supplementary groups at creation |
| `adduser --disabled-password --gecos '' deploy` | Ubuntu's wrapper: home and group, no password (SSH keys only), no questions; 24.04 prefers `--comment` to the deprecated `--gecos` |

**What the output tells you:** useradd prints nothing on success, so check the result:

```
$ getent passwd demo
demo:x:998:998::/srv/demo:/usr/sbin/nologin
$ sudo -u demo ls /srv/demo
ls: cannot access '/srv/demo': No such file or directory
```

A system UID (998) and the nologin shell are right, but the home directory does not exist yet: a unit with `WorkingDirectory=/srv/demo` fails with status `200/CHDIR` until you create it.

**Why it is effective:** the flags make the account exactly as powerful as the service needs: a system UID, no password, no shell, its data where the service expects it, and the same line gives the same account on every host.

**Compared with `adduser`:** on Debian and Ubuntu, adduser is the better tool for a person (home, group, password and sensible defaults in one go). On RHEL, `adduser` is just a link to `useradd`, so scripts should call useradd with explicit flags.

**Trap:** a bare `useradd NAME` on Ubuntu creates **no** home directory and takes the shell from `/etc/default/useradd`: always pass `-m` or `-M` and `-s`. System UIDs are handed out from 999 downwards, the numbers many container images use (postgres, mysql, redis), so files a container wrote may suddenly show the new account's name in `ls -l`.

**Next step:** create the directory: `install -d -o demo -g demo -m 750 /srv/demo`. Extra groups → `usermod -aG`. A person's SSH key → `ssh-copy-id`, or `authorized_keys` with mode 600. Verify with `id demo` and `sudo -u demo …`.

### usermod / groupadd / gpasswd — add or remove group members, lock or expire an account
Match: usermod, groupadd, gpasswd
Instead of: editing /etc/group by hand
Safety: changes state: group membership, password lock, expiry or shell · needs root · group changes reach the user only at the next login

**In one line:** `usermod` changes an existing account (supplementary groups, password lock, expiry date, shell), `groupadd` creates a group, and `gpasswd -d` removes one member from a group without touching the others.

**Read the command:** `usermod -aG docker "$USER"`

| Part | Meaning |
|---|---|
| `-a` | **append**: keep the existing supplementary groups (only valid with `-G`) |
| `-G docker` | the group(s) to add, comma-separated |
| `"$USER"` | the account, here your own |
| `-L` / `-U` | lock / unlock the **password** (a `!` in front of the hash) |
| `-L -e 1` | lock and expire (day 1 = 2 January 1970): no login at all, SSH keys included |
| `-s /usr/sbin/nologin` | change the login shell |
| `groupadd -f sshusers` | create a group; `-f` = succeed quietly if it already exists |
| `gpasswd -d ubuntu lxd` | remove ubuntu from lxd, leave its other groups alone |

**What the output tells you:** usermod prints nothing, so check with `id`:

```
$ sudo usermod -aG docker deploy
$ id deploy
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),27(sudo),988(docker)
$ sudo usermod -G docker deploy
$ id deploy
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),988(docker)
```

The second command forgot `-a`: `-G` alone **replaces** the list, so deploy silently lost `sudo`.

**Why it is effective:** each command changes one thing in the account database, with locking, and `gpasswd -d` removes a single membership without rewriting the whole list.

**Compared with editing `/etc/group`:** a text edit works, but it risks a malformed line, leaves `/etc/gshadow` out of step, and races with other tools changing the same file.

**Trap:** membership changes apply at the **next login**: running sessions and started daemons keep their old groups, so removing someone from `docker` does not end the access they already have. `-L` alone does not stop SSH key logins on a default Ubuntu server: use `-L -e 1` and remove `authorized_keys`. Membership of `docker`, `lxd` or `sudo` is each equivalent to root.

**Next step:** verify with `id USER`, then a fresh login. End access now → `loginctl terminate-user USER`. `newgrp docker` gives one shell the group at once, but as its primary group (new files get it); a fresh login is cleaner. Offboarding → `usermod -L -e 1` first, archive the home, delete later.

### passwd -S / chage -l / faillock — is this account locked, expired or locked out?
Match: passwd, chage, faillock, pam_tally2
Instead of: grep USER /etc/shadow, resetting the password to see if it helps
Safety: read-only for `passwd -S`, `chage -l` and `faillock --user` · changes state: `passwd USER` sets a password, `faillock --reset` clears the lockout · needs root for other users

**In one line:** three views of "why can't this account log in when the key or password is right": `passwd -S` gives the password status in one line, `chage -l` the expiry dates, `faillock` the failure counter PAM uses for temporary lockouts.

**Read the command:** `chage -l deploy`

| Part | Meaning |
|---|---|
| `chage -l deploy` | list deploy's ageing and expiry data, readable (other chage flags change it) |
| `passwd -S appuser` | one line: name, `P` usable password, `L` locked, `NP` no password, then the ageing fields (RHEL prints `PS`, `LK`, `NP`) |
| `passwd labuser` | **changes state**: as root, set a new password without knowing the old one |
| `faillock --user appuser` | the failed attempts pam_faillock has recorded for appuser |
| `--reset` | **changes state**: clear them, which lifts the temporary lock |

**What the output tells you:**

```
$ sudo chage -l deploy | head -4
Last password change                                    : Sep 01, 2026
Password expires                                        : never
Password inactive                                       : never
Account expires                                         : Jan 02, 1970
$ sudo faillock --user appuser
appuser:
When                Type  Source                                           Valid
2026-10-04 09:14:02 RHOST 198.51.100.7                                         V
```

`Account expires` in the past blocks **every** login method, SSH keys included (what `usermod -e 1` does). `Password expires` in the past forces a password change at the next login, which also breaks non-interactive key logins such as CI jobs. Each `V` line is a counted failure; at the limit (`deny`, 3 by default) pam_faillock refuses even the right password until `unlock_time` passes (600 s by default) or someone runs `--reset`.

**Why it is effective:** the client only says "Permission denied"; these name the account rule responsible, changing nothing.

**Compared with `grep USER /etc/shadow`:** the raw line holds the same ageing data (a `!` prefix = locked, field 8 = account expiry), but as day counts since 1970, and no lockout counter.

**Trap:** `L` is not "cannot log in": an `adduser --disabled-password` account shows `L` and logs in with its SSH key all day. faillock counts PAM password failures only, never key logins, and exists only where pam_faillock is configured (common on RHEL, not on a default Ubuntu), where an empty list proves nothing.

**Next step:** `L` but should use a password → `usermod -U` or `passwd USER`. Account expired → `chage -E -1 USER` (no expiry) or a new date. Service account's password expired → `chage -M -1 USER`. Locked out → `faillock --user USER --reset`, then find the source in the journal. Related: `pam_tally2 --user USER`, the older counter, is gone from current PAM.

### sudoedit — edit a root-owned file without running your editor as root
Match: sudoedit
Instead of: sudo vim FILE, sudo nano FILE
Safety: changes state: writes the file back as root when the editor exits; the next reload or restart uses it · needs a sudo rule that allows it

**In one line:** `sudoedit FILE` (the same as `sudo -e`) copies the file to a temporary file owned by you, opens it in **your** editor as **you**, and copies it back over the original as root only when the editor exits.

**Read the command:** `sudoedit /etc/apache2/ports.conf`

| Part | Meaning |
|---|---|
| `sudoedit` | sudo in edit mode: sudo reads and writes the file as root; the editor never runs as root |
| `/etc/apache2/ports.conf` | the file; give several to open them together; a path that does not exist is created when you save |
| `SUDO_EDITOR=nano sudoedit FILE` | choose the editor: `SUDO_EDITOR`, then `VISUAL`, then `EDITOR`, then the system default |
| `deploy ALL=(root) sudoedit /etc/apache2/ports.conf` | a sudoers rule that allows editing exactly this file and nothing else |

**What the output tells you:**

```
$ sudoedit /etc/apache2/ports.conf
sudoedit: /etc/apache2/ports.conf unchanged
$ sudoedit /srv/shop/.env
sudoedit: /srv/shop/.env: editing files in a writable directory is not permitted
```

No message after you quit means the file was written back. `unchanged` means nothing was saved. The refusal is a safety check: a user who can write the directory could swap the file for a symlink to another root-owned file during the edit (symlinks themselves are refused too).

**Why it is effective:** the editor, its plugins and its shell escapes (`:!sh`) run with your rights, with your own editor settings, and a sudoers rule can grant "edit this one file" safely.

**Compared with `sudo vim FILE`:** it edits the same file and is fine for an admin who has full sudo anyway, but the whole editor runs as root (root's config, root-owned swap files), and a rule allowing `sudo vim` is in effect a root shell.

**Trap:** the file is written back when the editor **exits**, not at each `:w`, so a reload from another terminal still reads the old content. A mistyped path silently creates a new file on save. sudoedit does not check the content: a typo goes live at the next reload. Never edit sudoers this way: `visudo` refuses a broken file.

**Next step:** validate before the reload: `apache2ctl configtest`, `nginx -t`, `sshd -t`, `systemctl daemon-reload` for unit files, `netplan try` for netplan. Not allowed to edit → `sudo -l` shows your rules. Directory refused → edit as root from a root shell, or fix the directory's owner.

### visudo — will sudo still work after this change?
Match: visudo
Instead of: vi /etc/sudoers, echo … >> /etc/sudoers.d/FILE
Safety: `-c` is read-only · without `-c` it edits under a lock and will not save a broken file unless you force it · needs root

**In one line:** `visudo` edits `/etc/sudoers` or a drop-in under a lock and parses the result before saving; `visudo -c` only checks, so files written by Ansible, a template or `echo` can be tested before sudo reads them.

**Read the command:** `visudo -cf /etc/sudoers.d/deploy`

| Part | Meaning |
|---|---|
| `-c` | check only: parse and report, change nothing; exit status 0 = valid |
| `-f /etc/sudoers.d/deploy` | the file to check or edit instead of `/etc/sudoers` |
| `visudo -c` | without `-f`: `/etc/sudoers` and every file it includes, owners and modes too |
| `visudo -f /etc/sudoers.d/ops1-restart` | **changes state**: edit this drop-in; on an error it asks `What now?` (`e` edit again, `x` discard, `Q` save anyway: never) |
| `pkexec visudo -c` | the same check when sudo itself is already broken (see the pkexec card) |

**What the output tells you:**

```
$ sudo visudo -c
/etc/sudoers: parsed OK
/etc/sudoers.d/README: parsed OK
>>> /etc/sudoers.d/deploy: syntax error near line 1 <<<
$ sudo visudo -cf /etc/sudoers.d/ops1-restart
/etc/sudoers.d/ops1-restart: parsed OK
```

`parsed OK` per file means sudo can read it. A syntax error can stop sudo for **everyone** (`sudo: no valid sudoers sources found, quitting`), and on Ubuntu there is no root password to fall back on, so this check stands between one typo and losing root.

**Why it is effective:** it is the same parser sudo uses, run before the change takes effect, with the file name and line of the problem.

**Compared with editing directly:** `vi /etc/sudoers` or `echo >>` writes whatever you typed, valid or not, and the first sign of a mistake is a broken sudo. Fine only if you check the file with `visudo -cf` before it lands in `/etc/sudoers.d`.

**Trap:** files in `/etc/sudoers.d` whose names contain a dot or end in `~` are silently skipped (`deploy.conf` never applies), and `visudo -c` does not check them either. When several rules match, the **last** one wins, so a later file can undo an earlier `NOPASSWD`. Keep drop-ins `root:root` and mode 0440.

**Next step:** `parsed OK` but the rule does not apply → `sudo -l -U deploy` (as root) shows the effective rules; check the file name and order. sudo already broken → `pkexec visudo -f FILE`, or the console or recovery mode. For templates → Ansible's `validate: visudo -cf %s`.

### runuser / pkexec — run one command as another user when sudo is not the tool
Match: runuser, pkexec
Instead of: su - postgres -c '…', sudo (when sudo itself is broken)
Safety: changes state: whatever the command does, with that user's rights · runuser is for root only · pkexec asks polkit and needs your password

**In one line:** `runuser` lets root drop to a service account for one command, with no password or sudo rule; `pkexec` goes the other way, raising you to root through polkit, which still works when a broken sudoers file has disabled sudo.

**Read the command:** `runuser -u postgres -- pg_dump -Fc -f "$DIR/appdb-$STAMP.dump" appdb`

| Part | Meaning |
|---|---|
| `runuser -u postgres` | as root, run the command as postgres (its UID and groups); no password, root only |
| `--` | end of runuser's options: the rest is the command with its own flags |
| `pg_dump -Fc -f FILE appdb` | the command: dump appdb in custom format (`-Fc`) to `FILE`, which postgres opens, so it needs write access to `$DIR` |
| `pkexec visudo -c` | run it as root through polkit: you type **your** password, and polkit must count you as an admin |
| `pkexec chmod 0440 /etc/sudoers.d/deploy` | **changes state**: the usual repair once you know the bad file |

**What the output tells you:** both print only what the command prints; the difference shows in the files:

```
$ sudo ls -l /var/backups/db
-rw------- 1 postgres postgres 48211907 Oct  4 02:00 appdb-2026-10-04_0200.dump
-rw------- 1 root     root         5114 Oct  4 02:00 globals-2026-10-04_0200.sql
```

postgres wrote the dump (`-f`). The globals file came from `runuser … > FILE`: the calling **root** shell opens that redirection before runuser starts, so root owns it.

**Why it is effective:** runuser needs no sudo rule, password or terminal, so a root timer runs database tools as their owner. pkexec authenticates through polkit, not sudoers, so a typo in `/etc/sudoers.d` does not cost you root.

**Compared with `su - postgres -c '…'`:** su works too, but passes the command as one string to the target's shell, with its quoting traps. **Compared with `sudo`:** sudo needs a valid sudoers file, exactly what is broken when you reach for pkexec.

**Trap:** runuser fails for normal users (`may not be used by non-root users`). Over SSH, pkexec can fail with `No session for cookie` or `Not authorized` when no polkit agent is attached: run `pkttyagent --process PID` (your first shell's PID) in a second session, or use the console. pkexec works only for polkit admins (on Ubuntu, the sudo group), and some hardened hosts remove it (PwnKit, CVE-2021-4034).

**Next step:** dump permission errors → `namei -l "$DIR"`, `install -d -o postgres -g postgres -m 0750 DIR`. sudo broken → `pkexec visudo -c`, then `pkexec visudo -f FILE`, else the console.

### namei -l — which directory on this path blocks access?
Match: namei
Instead of: ls -l FILE
Safety: read-only

**In one line:** `namei -l` walks a path from `/` to the file and prints the mode, owner and group of **every** component, so you see the one directory a user cannot pass.

**Read the command:** `namei -l /srv/site/index.html`

| Part | Meaning |
|---|---|
| `namei` | split the path and look up each component, following symlinks |
| `-l` | long format: modes, owners and groups, aligned (the same as `-m -o -v`) |
| `/srv/site/index.html` | the full path the service opens |
| `-n` | do not follow symlinks |
| `-x` | mark mount points with `D` instead of `d` |

**What the output tells you:**

```
$ namei -l /srv/site/index.html
f: /srv/site/index.html
drwxr-xr-x root   root   /
drwxr-xr-x root   root   srv
drwx------ deploy deploy site
-rw-r--r-- deploy deploy index.html
```

Every directory needs `x` (search) for the user, and the file needs `r`. Apache runs as www-data, which is neither deploy nor in group deploy, and `site` gives others nothing, so the browser gets 403 although `index.html` itself is world-readable.

**Why it is effective:** "Permission denied" names the file, but the kernel checks the whole path. One command lines up all components, and a symlink (`l` line) is shown with its target, whose components follow.

**Compared with `ls -l FILE`:** ls shows the file's own mode, which here looks perfect; you would need `ls -ld` on every parent to find the culprit.

**Trap:** namei shows mode bits only: not ACLs, SELinux labels or AppArmor rules, and it looks with **your** rights (use sudo to see components you cannot read). Current Ubuntu LTS releases create home directories with mode 750, so a web server cannot reach content inside a user's home unless that directory grants it `x`.

**Next step:** prove it as the service user: `sudo -u www-data cat /srv/site/index.html`. Fix the one component: `chmod o+x DIR`, or `setfacl -m u:www-data:x DIR` for just that user. Modes fine but still denied → `getfacl`, `ls -Z` and `ausearch -m AVC` (SELinux), `aa-status` (AppArmor).

### chmod — set exactly who may read, write or enter
Match: chmod
Instead of: chmod 777, chmod -R 755
Safety: changes state: modes change at once; a wrong recursive change can break a service or SSH logins, or expose secrets · owner or root only

**In one line:** `chmod` sets the read, write and execute bits for owner, group and others, plus setuid, setgid and sticky, as an exact octal mode or as a change to selected bits.

**Read the command:** `chmod -R g+rwX /srv/shop/uploads`

| Part | Meaning |
|---|---|
| `-R` | recursive: `/srv/shop/uploads` and everything below it |
| `g+rwX` | group (`u` owner, `o` others, `a` all) gains (`-` removes, `=` sets) read, write and `X`: execute only on directories and already-executable files |
| `600` / `644` | octal digits for owner, group, others (r=4, w=2, x=1): owner-only (keys, `.env`) / everyone reads |
| `700` / `750` / `755` | for directories and scripts; on a directory `x` means "may pass through" |
| `2775` | leading `2` = setgid on a directory: new files inherit its group |
| `4755` | leading `4` = setuid: the program runs as its owner, here root; on an unknown file, a classic backdoor |
| `go-w` | remove write for group and others, nothing else (what sshd demands of a home directory) |

**What the output tells you:** chmod prints nothing; check with `ls -l`:

```
$ ls -ld /srv/shared /srv/shared/report.pdf /usr/local/bin/.cache-helper
drwxrwsr-x 2 root webdev    4096 Oct  4 10:12 /srv/shared
-rw-rw-r-- 1 ops  webdev    1834 Oct  4 10:15 /srv/shared/report.pdf
-rwsr-xr-x 1 root root   1446024 Oct  4 03:12 /usr/local/bin/.cache-helper
```

`s` in the group's execute slot is setgid (2775): the PDF got group webdev by itself. `s` in the owner's slot is setuid root (4755): whoever runs that hidden file gets root.

**Why it is effective:** octal sets the whole mode as one reviewable number; symbolic changes only the bits you name; `X` keeps `-R` from making every file executable.

**Compared with `chmod 777`:** 777 silences the error by letting every local user and compromised service write the file, and hides the cause. Some programs then refuse: sshd ignores keys under group- or world-writable directories, Traefik rejects an `acme.json` that is not 600.

**Trap:** "Permission denied" is often not about this file: a parent directory without `x`, an ACL mask, SELinux or AppArmor. `chmod -R 644` strips `x` from directories, so nobody can enter them. On a file with an ACL, `chmod g-w` lowers the ACL mask, cutting named users' rights too.

**Next step:** blocking component → `namei -l /full/path`. Wrong owner → `chown`. One more user needs access → `setfacl`. New files get wrong modes → the creator's `umask`. Setuid audit → `find / -xdev -perm -4000`.

### chown / chgrp — give files to the user or group the process really runs as
Match: chown, chgrp
Instead of: chmod 777, running the container or service as root
Safety: changes state: ownership changes at once; a recursive change on a wrong path is hard to undo · needs root

**In one line:** `chown` sets a file's owner and group, by name or by number, and `chgrp` only the group; the kernel compares these numbers with the UID and GIDs of the process that opens the file.

**Read the command:** `chown -R 999:999 /srv/shop/data`

| Part | Meaning |
|---|---|
| `-R` | recursive: the directory and everything below it |
| `999:999` | owner UID 999, group GID 999: the numbers the container's process runs as (postgres in the official image) |
| `/srv/shop/data` | the bind-mounted data directory |
| `demo:demo` | by name: owner and group |
| `appuser:` | trailing colon: owner appuser, group = appuser's login group |
| `root:www-data` | root owns it, the web server's group may read it (with mode 640 or 750) |
| `101000:101000` | UID 1000 inside an unprivileged Proxmox or LXC container, as the host sees it (offset 100000) |
| `chgrp -R deployers /srv/app` | change only the group, e.g. for a shared deploy tree |

**What the output tells you:** chown prints nothing; compare numbers before and after:

```
$ docker exec shop-db id
uid=999(postgres) gid=999(postgres) groups=999(postgres)
$ ls -ln /srv/shop
drwx------ 19 1000 1000 4096 Oct  4 09:12 data
```

The process is UID 999, the directory belongs to UID 1000 with mode 700: postgres cannot enter its own data directory. `-n` shows numbers because names differ per system; on the host, 999 may belong to another account or to none.

**Why it is effective:** it matches the file to the identity that uses it, so the mode can stay tight (700, 600) and nobody else gains access.

**Compared with `chmod 777`:** it makes the error go away for everyone at once, and some programs refuse such files anyway: PostgreSQL insists its data directory is owned by its own user with mode 0700 or 0750; sshd and Traefik check too.

**Trap:** GNU chown does not protect `/`: a stray space (`chown -R deploy: / srv/app`) walks the whole system. An image update or a `user:` setting can change the container's UID, and rootless or userns-remapped Docker shifts every UID on the host. New files get the process's UID anyway; only existing ones need fixing.

**Next step:** find the UID first: `docker exec CTR id`, `ps -o user,uid,gid -p PID`, or the image's documentation. Several writers → a shared group with `chgrp -R`, `chmod 2775` and an ACL. Still denied → `namei -l` for the whole path.

### umask — which permissions will new files get?
Match: umask
Instead of: chmod after the fact
Safety: read-only without an argument · with one, changes the mask of this shell and everything it starts, until it exits

**In one line:** `umask` shows or sets the permission bits that are **removed** from every file and directory this shell and its children create: files start from 666, directories from 777.

**Read the command:** `umask 077`

| Part | Meaning |
|---|---|
| `umask` | print the current mask in octal, e.g. `0022` |
| `-S` | print what remains instead: `u=rwx,g=rx,o=rx` |
| `077` | remove everything for group and others: new files 600, directories 700 (secrets, backups) |
| `022` | the usual default: files 644, directories 755 |
| `002` | group-writable: files 664, directories 775 (shared group directories) |
| `UMask=0002` | the same for a systemd service, set in its unit (`systemctl edit`) |

**What the output tells you:**

```
$ umask; umask -S
0002
u=rwx,g=rwx,o=rx
$ grep Umask /proc/1344/status
Umask:	0022
```

The first is your shell (0002 is typical for Ubuntu login users, who each have a private group); the second is a running service, read from `/proc`, and that is what its files really get.

**Why it is effective:** it decides permissions at creation time, so a secret is never readable even for a moment, and it explains files that come out 600 or 664 when you expected 644.

**Compared with `chmod` after the fact:** chmod fixes one existing file; a file created readable and fixed a second later was readable in between, and the next file comes out wrong again.

**Trap:** umask only removes bits, and only when a file is **created**: overwriting with `>` keeps the old mode, and a program that sets the mode itself afterwards (`install -m 644`, a `chmod` in the script) overrides it. It is per process: setting it in your shell changes nothing for a cron job, CI runner or service. A deploy script with `umask 077` produces files the web server cannot read (403).

**Next step:** wrong modes on new files → check the creating process (`/proc/PID/status`, the unit's `UMask=`, the script's own `umask`). Shared directories → `UMask=0002` plus setgid (`chmod 2775`). Existing files → `chmod`; in scripts set modes explicitly with `install -m`.

### getfacl / setfacl — give one more user or group access without changing owner or mode
Match: getfacl, setfacl
Instead of: chmod 777, adding the user to the file's group
Safety: getfacl is read-only · setfacl changes state: `-m` adds or changes entries, `-x` and `-b` remove them, `-R` applies to a whole tree

**In one line:** an ACL adds entries such as "user auditor may read" or "group deployers may write" on top of owner, group and others; `getfacl` shows them with the rights that really apply, `setfacl` changes them, and a default ACL on a directory is inherited by new files.

**Read the command:** `setfacl -R -m g:deployers:rwX,m::rwX /srv/app`

| Part | Meaning |
|---|---|
| `-R` | apply to the directory and everything below it |
| `-m` | modify: add or change these entries, keep the others |
| `g:deployers:rwX` | group deployers: read, write, and execute on directories (and on already-executable files) |
| `m::rwX` | the **mask**: the most any named user or group entry can get |
| `-d -m u:auditor:r DIR` | a default ACL: the template for files created in DIR later |
| `-x u:auditor` / `-b` | remove one entry / all ACL entries |
| `getfacl -p FILE` | show the ACL; `-p` keeps the leading `/` in names |

**What the output tells you:**

```
$ getfacl -p /srv/app/releases/42/config.yml
# file: /srv/app/releases/42/config.yml
# owner: ci
# group: ci
user::rw-
group::rwx                      #effective:r--
group:deployers:rwx             #effective:r--
mask::r--
other::r--
```

The deployers entry says `rwx`, but the mask is `r--`, so deployers may only read: the CI job created the file with mode 644, and that mode lowered the mask. In `ls -l`, a `+` after the mode (`-rw-r--r--+`) shows that an ACL exists, and the group bits shown there are the mask.

**Why it is effective:** it grants exactly one extra user or group exactly the access needed, without loosening the mode for everyone or adding people to groups that carry other rights (`adm` reads every log).

**Compared with `chmod 777`:** 777 opens the file to every user to help one. Adding the user to the file's group works when one group fits, but gives them everything that group can reach.

**Trap:** the mask caps every named entry and the owning group, and a later `chmod g-w` or a program that creates files 600 or 644 lowers it silently (`#effective:` reveals it). Default ACLs affect only files created afterwards: use `-R` for existing ones. Copies made with tools that ignore ACLs (plain `cp`, `rsync` without `-A`) lose them.

**Next step:** effective right lower than the entry → raise the mask (`m::rwX`) and fix the creating program's mode (`UMask=0002`, `rsync --chmod`). Still denied → `namei -l` for the path, then SELinux or AppArmor. Remove a grant → `setfacl -x u:USER FILE`.

### getcap / setcap / capsh — which single root powers does this binary or process have?
Match: getcap, setcap, capsh
Instead of: running the service as root, chmod u+s
Safety: getcap and `capsh --decode` are read-only · setcap changes state: everyone who can run the file gets the capability · needs root to set

**In one line:** Linux splits root's power into about 40 capabilities (bind ports below 1024, open raw sockets, bypass file permissions…); `setcap` attaches chosen ones to a program file, `getcap` shows them, and `capsh --decode` turns a process's capability bitmask into names.

**Read the command:** `setcap cap_net_raw+ep /usr/local/bin/blackbox_exporter`

| Part | Meaning |
|---|---|
| `cap_net_raw` | open raw sockets, which ICMP probes need (`cap_net_bind_service` = bind ports below 1024) |
| `+ep` | add to the **e**ffective and **p**ermitted sets: active as soon as the program starts |
| `/usr/local/bin/blackbox_exporter` | the binary itself, not a script that starts it |
| `setcap -r FILE` | remove the file's capabilities |
| `getcap /usr/bin/node` | show one file's capabilities; no output = none |
| `getcap -r / 2>/dev/null` | every file with capabilities on the system: a hardening baseline |
| `capsh --decode=00000000a80425fb` | names for a hex mask from `/proc/PID/status` (`CapEff`, `CapBnd`…) |

**What the output tells you:**

```
$ getcap -r / 2>/dev/null
/usr/bin/ping cap_net_raw=ep
/usr/bin/mtr-packet cap_net_raw=ep
/usr/local/bin/blackbox_exporter cap_net_raw=ep
$ capsh --decode=00000000a80425fb
0x00000000a80425fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_raw,cap_sys_chroot,cap_mknod,cap_audit_write,cap_setfcap
```

Each getcap line is a file and its capabilities. The decoded mask is Docker's default set for a container's root: 14 capabilities, without `cap_net_admin` or `cap_sys_admin`.

**Why it is effective:** the program runs as an ordinary user with one extra power instead of all of root, so a bug in it is not a root compromise. capsh answers "what can this process or container actually do?" from the kernel's own numbers.

**Compared with running as root or setuid:** both work, but then any flaw in the program hands out every root power at once.

**Trap:** the capability belongs to that exact file: an upgrade or a fresh download replaces it, silently drops it, and the old error returns. It applies to everyone who can run the file: `cap_net_bind_service` on `/usr/bin/node` lets every Node script on the host bind port 80. File capabilities are ignored on `nosuid` mounts and on scripts (the kernel runs the interpreter, not the script).

**Next step:** a service needs a low port → `AmbientCapabilities=CAP_NET_BIND_SERVICE` in its systemd unit (only that service gets it), or a reverse proxy in front. Unknown entry in `getcap -r /` → compare with your baseline, `dpkg -S FILE`. Containers → `--cap-drop ALL`, then `--cap-add` only what is needed.

### getenforce / setenforce / setsebool — is SELinux blocking this, and is a policy switch off?
Match: getenforce, setenforce, setsebool, getsebool, sestatus
Instead of: SELINUX=disabled, setenforce 0 as the fix
Safety: getenforce is read-only · setenforce changes state for the whole host until reboot (0 = nothing is blocked) · setsebool changes a policy switch, permanently with `-P` · needs root

**In one line:** on RHEL-family hosts SELinux checks every access a second time, by labels; `getenforce` says whether it enforces, `setenforce 0` is a one-minute test of whether SELinux is the cause, and `setsebool` flips one of the policy's built-in switches (booleans).

**Read the command:** `setsebool -P httpd_can_network_connect on`

| Part | Meaning |
|---|---|
| `setsebool` | set a boolean: an on/off switch the policy authors built in for a common need |
| `-P` | persistent: written into the policy so it survives reboot (slower to apply) |
| `httpd_can_network_connect` | let web servers (Apache and nginx run as type `httpd_t`) open TCP connections to any port, e.g. an upstream on 8080 |
| `on` | the new value (`1` works too; `off` or `0` reverts) |
| `getenforce` | `Enforcing` (blocks and logs), `Permissive` (logs only) or `Disabled` |
| `setenforce 0` / `1` | permissive / enforcing for the whole host, until reboot |
| `getsebool -a | grep httpd` | the booleans that exist, and their state |

**What the output tells you:**

```
$ getenforce
Enforcing
$ sudo ausearch -m AVC -ts recent | tail -1
type=AVC msg=audit(…): avc:  denied  { name_connect } for  pid=1402 comm="nginx" dest=8080 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:http_cache_port_t:s0 tclass=tcp_socket permissive=0
$ getsebool httpd_can_network_connect
httpd_can_network_connect --> off
```

nginx (`httpd_t`) was denied `name_connect` to port 8080, and the boolean made for exactly that is off: one `setsebool -P` fixes it and leaves the rest of SELinux enforcing.

**Why it is effective:** the permissive test (`setenforce 0`, retry, `setenforce 1`) proves or rules out SELinux in a minute, and a boolean is the supported, minimal fix for a whole class of denials.

**Compared with `SELINUX=disabled`:** it makes the app work by removing the protection from every service, and switching SELinux back on later needs a full relabel at boot.

**Trap:** `setenforce 0` is host-wide and lasts until reboot, so it is easy to forget. `setsebool` without `-P` is lost at the next reboot: the app breaks again after patching. `setenforce` cannot leave `Disabled`; that takes the config file and a reboot.

**Next step:** denial on a file (`tcontext` such as `user_home_t`) → `semanage fcontext` and `restorecon`. `name_bind` on a port → `semanage port -a`. `name_connect` → a boolean, as here. No AVC at all → not SELinux: `namei -l`, `getfacl`. Related: `sestatus` adds the loaded policy and the mode set in the config file; `getsebool -a` lists every boolean.

### semanage / restorecon — give files and ports the SELinux label a service needs
Match: semanage, restorecon, chcon
Instead of: chcon, audit2allow -M on every denial, setenforce 0
Safety: `semanage … -l` only reads · changes state: `fcontext -a` and `port -a` add permanent rules to the local policy; `restorecon` relabels files on disk · needs root

**In one line:** SELinux decides by labels: `semanage fcontext` records which label files under a path should carry, `restorecon` applies the recorded labels to the files that exist, and `semanage port` lists or adds the port labels that say which service may use which port.

**Read the command:** `semanage fcontext -a -t httpd_sys_content_t "/srv/www(/.*)?" && restorecon -R /srv/www`

| Part | Meaning |
|---|---|
| `fcontext -a` | add a file-context rule to the local policy |
| `-t httpd_sys_content_t` | the type to assign: web content that web servers may read |
| `"/srv/www(/.*)?"` | a regular expression: the directory and everything below it (quote it) |
| `restorecon -R /srv/www` | apply the rules now to the existing files, recursively; `-v` prints each change |
| `port -l` | list port types with their ports |
| `port -a -t http_port_t -p tcp 8444` | label TCP 8444 so web servers may bind it |
| `port -m …` | change a port that already has another type (`-a` then fails with `already defined`) |

**What the output tells you:**

```
$ ls -Z /srv/www/index.html
unconfined_u:object_r:user_home_t:s0 /srv/www/index.html
$ sudo restorecon -Rv /srv/www
Relabeled /srv/www/index.html from unconfined_u:object_r:user_home_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0
$ sudo semanage port -l | grep -w http_port_t
http_port_t                    tcp      80, 81, 443, 488, 8008, 8009, 8443, 9000
```

The file was moved with `mv` from a home directory and kept its `user_home_t` label, so nginx returned 403 despite correct modes. The port list shows why nginx can bind 8443 but not 8444.

**Why it is effective:** the rule plus the relabel make the label right now and after every future relabel, and a port label allows one service one more port while SELinux keeps enforcing.

**Compared with `chcon`:** chcon changes the label at once, but the next `restorecon` or full relabel quietly reverts it, because no rule records it. **Compared with `audit2allow -M`:** it writes policy that allows whatever was denied, often far more than needed.

**Trap:** `semanage fcontext -a` alone changes no file: run `restorecon`. `mv` keeps a file's label, `cp` gives it the destination's. Container bind mounts on SELinux hosts are relabelled with `:Z` or `:z` on the volume instead.

**Next step:** relabelled but still denied → `ausearch -m AVC -ts recent` again: maybe a boolean (`setsebool`). Labels keep reverting → the rule is missing (`semanage fcontext -l | grep /srv/www`). Unsure which type → copy it from a working path: `ls -Z /var/www/html`. Related: `chcon -t TYPE FILE` (compared above) is for tests only.

### aa-status — is AppArmor confining this program, and in which mode?
Match: aa-status, aa-complain
Instead of: —
Safety: read-only · run it with sudo for the full list

**In one line:** AppArmor is Ubuntu's mandatory access control: per-program profiles list the paths and capabilities a program may use, whatever the file modes say; `aa-status` shows which profiles are loaded, in which mode, and which running processes they confine.

**Read the command:** `aa-status`

| Part | Meaning |
|---|---|
| `aa-status` | loaded profiles by mode, then the confined processes with their PIDs |
| enforce mode | violations are blocked and logged |
| complain mode | violations are only logged: for testing a profile |
| `aa-complain /etc/apparmor.d/usr.sbin.nginx` | **changes state**: switch one profile to complain mode to test whether it is the cause |
| `journalctl -k | grep 'apparmor="DENIED"'` | the denials, with profile, operation and path |

**What the output tells you:**

```
apparmor module is loaded.
48 profiles are loaded.
46 profiles are in enforce mode.
   /usr/sbin/mysqld
   …
2 profiles are in complain mode.
3 processes have profiles defined.
3 processes are in enforce mode.
   /usr/sbin/mysqld (1120)
```

mysqld runs confined in enforce mode. If its data directory moves to `/data/mysql`, the profile still allows only the old paths, and MySQL fails with "Permission denied" although owner and mode are right; the kernel log shows `apparmor="DENIED" operation="open" profile="/usr/sbin/mysqld" name="/data/mysql/…"`.

**Why it is effective:** it explains Ubuntu's invisible "Permission denied": correct owner, mode and ACL, still refused. One look tells you whether the program is confined at all.

**Trap:** profiles work on paths: a moved data directory is checked against its new path, even behind a symlink from the old one (AppArmor resolves symlinks). Add rules in the local override (`/etc/apparmor.d/local/usr.sbin.mysqld`) rather than the packaged profile, then reload it. Containers run under `docker-default`, snaps under their own profiles. Disabling AppArmor host-wide is never the fix.

**Next step:** denial found → allow the path in the local file, then `sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.mysqld`. No denial → not AppArmor: `namei -l`, `getfacl`. RHEL host → `getenforce`. Related: `aa-complain PROFILE` (apparmor-utils) makes a profile log instead of block; `aa-enforce PROFILE` switches it back.

### ssh — log in, run a command or tunnel, and see exactly where a login fails
Match: ssh
Instead of: ping host, telnet host 22
Safety: read-only for `-v`, `-G` and `true` tests · remote commands run with that user's rights · `-L`, `-R` and `-D` open listening ports for as long as the session lives

**In one line:** `ssh` opens an encrypted session to log in, run a command or carry traffic (jump hosts, tunnels); `-v` narrates each phase, from TCP connect to the key the server accepted or refused.

**Read the command:** `ssh -vvv -o BatchMode=yes deploy@192.0.2.20 true`

| Part | Meaning |
|---|---|
| `-vvv` | debug level 3 (`-v` often suffices): every phase, each key offered, the reply |
| `-o BatchMode=yes` | never prompt (password, passphrase, new host key): fail at once, like cron or CI; `-o ConnectTimeout=5` also caps the connect |
| `deploy@192.0.2.20 true` | user, host, and a remote command that does nothing: exit 0 = login works |
| `-i KEY -o IdentitiesOnly=yes` | offer only this key, not every agent key (`Too many authentication failures`) |
| `-J bastion` | jump through bastion to the target (ProxyJump) |
| `-N -L 15432:127.0.0.1:5432` / `-R 8080:localhost:80` | tunnel only: local 15432 to 5432 as seen *from the server* / server port 8080 to port 80 here |
| `-G web01` | print the effective client settings for web01 (host name, user, port, keys) and exit |

**What the output tells you:**

```
debug1: Connecting to 192.0.2.20 [192.0.2.20] port 22.
debug1: Host '192.0.2.20' is known and matches the ED25519 host key.
debug1: Offering public key: /builds/shop/web.tmp/SSH_PRIVATE_KEY ED25519 SHA256:4mF0c2Qk... explicit
debug1: Authentications that can continue: publickey
deploy@192.0.2.20: Permission denied (publickey).
```

TCP works, the host key is trusted, the key goes out, and no `Server accepts key` follows: the **server** refused it. Earlier stops point elsewhere: `Connection timed out` (firewall, route), `Connection refused` (nothing listening), `Host key verification failed` (known_hosts).

**Why it is effective:** `Permission denied (publickey)` covers many causes; the trace shows how far the login got, which key went out and what the server allows.

**Compared with `ping host` / `telnet host 22`:** they only prove the host or port answers (`nc -zv -w 3 HOST 22` does that better), not users or keys.

**Trap:** the client never learns **why** a key was refused (not in authorized_keys, bad modes on the server's `~/.ssh`, `AllowGroups`, an expired account); only the server log says (`journalctl -u ssh`; `sshd` on RHEL). A host key changed without a rebuild: stop. `StrictHostKeyChecking=accept-new` trusts new hosts but refuses changed keys; `=no` accepts anything.

**Next step:** timeout or refused → firewall, `ss -ltnp` on the server. Key refused → server log, `namei -l` on authorized_keys, `sshd -T`. Wrong key → `ssh-add -l`. Expected host-key change → `ssh-keygen -R HOST`. Slow → where `-vvv` pauses.

### sshd -t / -T — is the server config valid, and which values are really in force?
Match: sshd
Instead of: cat /etc/ssh/sshd_config, systemctl restart ssh to find out
Safety: read-only · starts no server and leaves the running one alone · needs root (it reads the host keys)

**In one line:** `sshd -t` parses the whole server configuration, main file and every `Include`, and prints nothing if it is valid; `sshd -T` prints the **effective** value of every setting after includes, defaults and the first-value-wins rule, i.e. what sshd will enforce.

**Read the command:** `sshd -T | grep -iE "permitroot|passwordauth|pubkey|allowusers|port"`

| Part | Meaning |
|---|---|
| `sshd` | the server binary, run here as a one-shot checker |
| `-T` | extended test: validate, then print every setting as `keyword value`, keywords in lower case |
| `| grep -iE "permitroot|passwordauth|…"` | keep the settings you care about |
| `-t` | test only: silent with exit status 0 if valid, otherwise the file, line and problem |
| `-C user=deploy,addr=198.51.100.7` | with `-T`: apply the `Match` blocks for this connection (also `host=`, `laddr=`, `lport=`) |
| `-f FILE` | check a candidate config file instead of `/etc/ssh/sshd_config` |

**What the output tells you:**

```
$ sudo sshd -t
/etc/ssh/sshd_config.d/10-hardening.conf: line 3: Bad configuration option: PasswordAuthentification
/etc/ssh/sshd_config.d/10-hardening.conf: terminating, 1 bad configuration options
$ sudo sshd -T | grep -iE "permitroot|passwordauth|pubkey|allowusers|port"
port 22
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication yes
```

`-t` names the file and line to fix. In `-T`, `passwordauthentication yes` although your file says `no` means another file was read first: Ubuntu's sshd_config begins with `Include /etc/ssh/sshd_config.d/*.conf`, files are read in name order, and for most keywords the **first** value wins, so `50-cloud-init.conf` beats `99-hardening.conf`. No `allowusers` line means anyone may log in; `without-password` is the old name of `prohibit-password`.

**Why it is effective:** includes, first-value-wins, built-in defaults and `Match` blocks combine, so the effective config cannot be read from the files. `-T` computes it, and `-t` keeps a typo from reaching a reload.

**Compared with `cat /etc/ssh/sshd_config`:** it shows what one file says, enough to spot a typo, not which value wins. Restarting to find out risks an sshd that does not come back.

**Trap:** without `-C`, `-T` ignores `Match` blocks. `-t` checks syntax, not safety: an `AllowGroups` line that excludes you passes. On Ubuntu 22.10 and later, systemd's ssh.socket holds port 22; on 24.04 a new `Port` takes `systemctl daemon-reload` and a restart of `ssh.socket`, so `-T` can say `port 2222` while systemd still listens on 22.

**Next step:** valid → `systemctl reload ssh`, then test a **new** login from a second terminal before closing the first. Value not what you wrote → `grep -rn KEYWORD /etc/ssh/sshd_config.d/ /etc/ssh/sshd_config`, and name your drop-in so it sorts first (`10-…`).

### ssh-keygen — make a key, check a fingerprint, fix known_hosts, sign certificates
Match: ssh-keygen
Instead of: comparing keys by eye, editing known_hosts by hand
Safety: read-only for `-l`, `-L` and `-F` · changes state: generating writes key files, `-R` rewrites known_hosts (keeping a `.old` copy), `-s` issues a certificate

**In one line:** one tool for the key life cycle: create key pairs, print the fingerprints that logs show, find or remove hosts in `known_hosts`, and sign short-lived certificates with an SSH CA.

**Read the command:** `ssh-keygen -t ed25519 -C "ops@laptop" -f ~/.ssh/id_ed25519`

| Part | Meaning |
|---|---|
| `-t ed25519` | key type Ed25519: short, fast, accepted by every current server |
| `-C "ops@laptop"` | a comment in the public key: whose key, which machine |
| `-f ~/.ssh/id_ed25519` | the private key file; the public half goes to `id_ed25519.pub` |
| `-a 100` / `-N ''` | 100 KDF rounds protect the passphrase (slower brute force of a stolen file) / empty passphrase, for an unattended job's key |
| `-lf FILE` | fingerprint of a key file (a private key too, or every key in authorized_keys) |
| `-F HOST` / `-R HOST` | find / remove HOST's lines in known_hosts, hashed names included |
| `-s CA -I ID -n ops -V +10m KEY.pub` | sign a user certificate for login name ops, valid 10 minutes; `-L -f KEY-cert.pub` shows it |

**What the output tells you:**

```
$ ssh-keygen -lf ~/.ssh/id_ed25519.pub
256 SHA256:3qL0kTq9mV0g8Yb7Xc2Rz5Wd1Ne4Pa6Su8Hj0Lf2Gk ops@laptop (ED25519)
$ ssh-keygen -F 10.10.0.21
# Host 10.10.0.21 found: line 12
10.10.0.21 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK3…
```

Bits, `SHA256:` fingerprint, comment, type. The same `SHA256:` string appears in `ssh -v` (`Offering public key`) and in the server log (`Accepted publickey for deploy … SHA256:…`), which proves which key was used.

**Why it is effective:** a fingerprint turns "is this the right key?" into a string comparison across client, agent, server file and log, and `-F`/`-R` handle hashed known_hosts names that grep cannot find.

**Compared with comparing keys by eye:** long base64 lines differ only near the end; the fingerprint is short and is what logs print.

**Trap:** only the `.pub` file goes to servers. `Load key "…": error in libcrypto` means a damaged private key file, typically a CI variable that lost its final newline or gained CRLF (`ssh-keygen -lf FILE` fails the same way). Old RSA keys can fail against current OpenSSH, which disabled `ssh-rsa` (SHA-1) signatures in 8.8: make an Ed25519 key. `-R` needs the name exactly as you connected (`[host]:2222` for another port).

**Next step:** key refused → compare with `ssh-keygen -lf` of the server's authorized_keys, then `namei -l` on it. Host rebuilt → `-R HOST`, then `ssh-keyscan` and a fingerprint check on the console. Certificate refused → `-L -f CERT` (validity, principals), the server log.

### ssh-copy-id / ssh-keyscan — install my key on a server, record a server's key on my side
Match: ssh-copy-id, ssh-keyscan
Instead of: pasting keys into authorized_keys by hand, StrictHostKeyChecking=no
Safety: ssh-copy-id changes state: appends to the remote authorized_keys and creates `~/.ssh` there if missing · ssh-keyscan only reads; appending its output to known_hosts makes your side trust that key

**In one line:** SSH trust runs both ways: the server must know your public key (`authorized_keys`, installed by `ssh-copy-id`), and you must know the server's host key (`known_hosts`, which `ssh-keyscan` fetches in advance for automation).

**Read the command:** `ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@10.0.1.10`

| Part | Meaning |
|---|---|
| `-i ~/.ssh/id_ed25519.pub` | the public key to install; without `-i`, every key your agent holds (or a default key file) |
| `deploy@10.0.1.10` | the account whose `~/.ssh/authorized_keys` receives it; you log in once with its password |
| `-p 2222` / `-n` | sshd on another port / dry run: show which keys would be installed |
| `ssh-keyscan -t ed25519 10.10.0.21` | ask the server for its Ed25519 host key, printed as a known_hosts line |
| `>> ~/.ssh/known_hosts` | append it, so the first connection does not stop at "authenticity can't be established" |
| `-H` (ssh-keyscan) | hash the host names in the output, like `HashKnownHosts yes` |

**What the output tells you:**

```
$ ssh-copy-id -i ~/.ssh/id_ed25519.pub deploy@10.0.1.10
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
deploy@10.0.1.10's password:
Number of key(s) added: 1
$ ssh-keyscan -t ed25519 10.10.0.21
# 10.10.0.21:22 SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.5
10.10.0.21 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK3…
```

`Number of key(s) added: 1` means the key was appended; "All keys were skipped because they already exist" means it is there and the problem is elsewhere. ssh-keyscan's `#` line names the server's SSH version; the next line is what goes into known_hosts.

**Why it is effective:** ssh-copy-id appends instead of overwriting, creates a missing `~/.ssh` with safe modes and skips keys that already work. ssh-keyscan lets CI and Ansible pin a host key once, instead of `StrictHostKeyChecking=no`, which accepts any man in the middle.

**Compared with pasting by hand:** `echo … >> authorized_keys` works, but a key split over two lines, or a file owned by root or too open, is the classic "key still refused".

**Trap:** ssh-keyscan believes whoever answers on that address right now: compare `ssh-keyscan -t ed25519 HOST | ssh-keygen -lf -` with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` read on the console. ssh-copy-id needs password logins to be allowed; on a key-only server, add the key from an existing session or through cloud-init.

**Next step:** key added → `ssh -v deploy@HOST` should show `Server accepts key`. Still refused → the server log, `namei -l` on authorized_keys (StrictModes). Host key changed after a rebuild → `ssh-keygen -R HOST`, then scan and verify again.

### ssh-add — which keys does my agent hold, and offer to every server?
Match: ssh-add, ssh-agent
Instead of: —
Safety: read-only for `-l` and `-L` · changes state in the running agent only: adding keys, or removing them with `-d` and `-D`; key files are not touched

**In one line:** `ssh-add` loads private keys into `ssh-agent` (you type each passphrase once) and lists what is loaded; ssh offers every agent key, often before your key files, so this list explains which key a login really uses.

**Read the command:** `ssh-add -l`

| Part | Meaning |
|---|---|
| `-l` | list the fingerprints of the loaded keys |
| `-L` | print the full public keys, ready for authorized_keys |
| `ssh-add` | no argument: load your default key files (`~/.ssh/id_ed25519`, `id_rsa`, …) |
| `ssh-add FILE` | load one specific key |
| `-t 1h` | forget the key after one hour |
| `-d FILE` / `-D` | remove one key / all keys from the agent |
| `eval "$(ssh-agent)"` | first start an agent for this shell (it sets `SSH_AUTH_SOCK`) |

**What the output tells you:**

```
$ ssh-add -l
256 SHA256:3qL0kTq9mV0g8Yb7Xc2Rz5Wd1Ne4Pa6Su8Hj0Lf2Gk ops@laptop (ED25519)
3072 SHA256:Hc2Lk9Pq4Wd7Zs1Xv8Tn3Ry6Ub0Mf5Je2Ga9Ko4Ni7B old-laptop (RSA)
$ ssh-add -l
The agent has no identities.
$ ssh-add -l
Could not open a connection to your authentication agent.
```

The same format as `ssh-keygen -l`. "No identities": an agent runs but holds nothing (ssh still tries the key files directly). "Could not open a connection": no agent reachable from this shell, typical in a sudo shell, a fresh tmux pane or a CI job.

**Why it is effective:** ssh offers agent keys one after another, and the server disconnects after `MaxAuthTries` attempts (6 by default), so with many keys loaded the right one may never be tried: `Too many authentication failures`. The list shows what will go out, with fingerprints you can match against `ssh -v` and the server log.

**Trap:** agent forwarding (`ssh -A`) lets root on the remote host use your keys while you are connected: prefer `ssh -J bastion`. `sudo` normally drops `SSH_AUTH_SOCK`, so `sudo git pull` does not see your agent. A key added without `-t` stays loaded until the agent exits.

**Next step:** wrong or too many keys → `ssh -o IdentitiesOnly=yes -i KEY`, or `IdentityFile` plus `IdentitiesOnly yes` for that host in `~/.ssh/config`. No agent → `eval "$(ssh-agent)"`, then `ssh-add`. Fingerprint unknown to the server → `ssh-copy-id`. Related: `ssh-agent` starts the agent and prints the variables your shell needs, which is why it runs inside `eval`.

### scp / sftp — copy files over SSH, and what a slow or stuck copy means
Match: scp, sftp
Instead of: —
Safety: changes state: writes files on the target and overwrites existing ones without asking · uses the same login and rights as ssh

**In one line:** `scp` copies files and directories between hosts over an SSH connection, with the same keys, ports and `~/.ssh/config` aliases; `sftp` opens an interactive file session over the same transport.

**Read the command:** `scp -P 2222 file user@host:/path/`

| Part | Meaning |
|---|---|
| `-P 2222` | the server's SSH port: **capital** P (ssh uses `-p`; in scp, lower-case `-p` preserves times and modes) |
| `file` | the local source; several files and globs are allowed |
| `user@host:/path/` | the remote target: the colon makes it remote; a path without a leading `/` starts in the user's home |
| `-r` | copy directories recursively |
| `-v` | the same debug output as `ssh -v` (authentication, cipher) |
| `HOST:/tmp/incident.pcap .` | the other direction: a remote file into the current directory |
| `-l 50000` | limit the rate to 50,000 Kbit/s |
| `sftp user@host` | interactive: `ls`, `cd`, `get`, `put`, `bye` |

**What the output tells you:**

```
$ scp ./bigfile.tar deploy@203.0.113.40:/tmp/
bigfile.tar                                    37%  377MB  11.2MB/s   00:54 ETA
```

Percentage, bytes so far, current rate, time left. A steady 11 MB/s is roughly a 100 Mbit/s link, or one CPU core busy with encryption. If a large file stops moving (the ETA turns into `- stalled -`) while `ssh HOST 'echo ok'` works, that is the MTU black-hole pattern: small packets pass, full-size ones vanish.

**Why it is effective:** nothing to install or open: it reuses your SSH access, firewall rules and keys, and `-v` shows the cipher and where a transfer hangs.

**Compared with `rsync`:** rsync also runs over SSH, but copies only what changed, resumes with `--partial` and can dry-run: prefer it for large trees and repeated syncs. scp is fine for a single file.

**Trap:** a copy rate is not the network's speed: encryption runs on one core (ssh near 100% CPU in `top`) and both disks take part; measure the link with `iperf3`. scp overwrites the target without asking. Since OpenSSH 9.0, scp uses the SFTP protocol underneath (`-O` forces the old protocol for servers without SFTP). Text printed by the remote shell's startup files (`echo` in `.bashrc`) breaks both scp and sftp.

**Next step:** slow → `top` during the copy, then a faster cipher (`-c aes128-gcm@openssh.com`) or rsync, and `iperf3` for the link. Stalls → `ping -M do -s 1472 HOST`, `tracepath HOST`. Permission denied → `scp -v` and the ssh card. Many small files → `tar … | ssh HOST 'tar -x …'` or rsync.

### last / lastb / lastlog — who logged in, from where, and when did the machine reboot?
Match: last, lastb, lastlog
Instead of: uptime, grep sshd /var/log/auth.log
Safety: read-only · lastb needs root

**In one line:** `last` reads the login history in `/var/log/wtmp` (sessions with times and source address, every boot and clean shutdown), `lastb` the failed logins in `/var/log/btmp`, and `lastlog` the latest login per account.

**Read the command:** `last -x reboot shutdown`

| Part | Meaning |
|---|---|
| `last` | sessions, newest first: user, terminal, source, login and logout time, duration |
| `-x` | include system entries: shutdowns and run-level changes |
| `reboot shutdown` | show only these pseudo-users: every boot and every clean shutdown |
| `-n 20` (or `-20`) / `-i` | only the newest 20 lines / source IP addresses instead of host names |
| `lastb` | failed login attempts, unknown user names included (root only) |
| `lastlog` | each account's latest login, or `**Never logged in**` |

**What the output tells you:**

```
$ last -x reboot shutdown | head -3
reboot   system boot  6.8.0-85-generic Sat Oct  4 04:00   still running
shutdown system down  6.8.0-79-generic Sat Oct  4 04:00 - 04:00  (00:00)
reboot   system boot  6.8.0-79-generic Mon Sep 22 13:12 - 04:00 (11+14:48)
$ last -i -n 2
deploy   pts/0        198.51.100.7     Sat Oct  4 09:12   still logged in
ops      pts/1        10.0.1.5         Mon Sep 22 08:15 - crash  (04:57)
```

The newest boot follows a clean shutdown and runs a new kernel: an unattended-upgrades reboot. A `reboot` line with no `shutdown` line directly below it (newest first), or a session ending in `crash`, means the host went down uncleanly (power, panic, hard reset), as on Sep 22.

**Why it is effective:** one command answers "did it reboot, when, cleanly, into which kernel?" and "who was on the box around the incident, from where".

**Compared with `uptime`:** uptime gives only the age of the current boot. **Compared with grepping auth.log:** it has every attempt and key fingerprint, but is long and rotates; last is the summary.

**Trap:** only sessions that got a terminal are recorded: `ssh host command`, scp, sftp, git over SSH and Ansible leave no `last` line, so check `journalctl -u ssh` (`Accepted publickey for …`). wtmp rotates: the closing `wtmp begins …` line shows how far back it goes (`last -f /var/log/wtmp.1` for older). Root can edit these files, so an empty history on a suspicious box is itself a finding.

**Next step:** unclean reboot → `journalctl -b -1 -e` (the end of the previous boot). Unknown address or user → `journalctl -u ssh --since …`, then `ausearch`. Many `lastb` entries from one address → fail2ban or the firewall.

### w / who — who is logged in right now, from where, doing what?
Match: w, who
Instead of: ps aux | grep sshd
Safety: read-only

**In one line:** `w` lists every terminal session open now, with source address, idle time and current command, under a header with uptime and load; `who` gives the same sessions in a shorter form.

**Read the command:** `w`

| Part | Meaning |
|---|---|
| `w` | header (time, uptime, number of users, load average), then one line per session |
| `w ops` | only ops's sessions |
| `-h` | no header, for scripts |
| `who` | user, terminal, login time and source, one line per session |
| `who -b` | the time of the last boot |

**What the output tells you:**

```
$ w
 10:12:41 up 3 days,  2:04,  2 users,  load average: 0.08, 0.12, 0.10
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
ops      pts/0    198.51.100.7     09:12    0.00s  0.05s  0.00s w
deploy   pts/1    10.0.1.5         10:02   10:00   0.02s  0.02s -bash
```

`FROM` is the source address, `IDLE` the time since the last keystroke, `JCPU` the CPU used by everything on that terminal and `PCPU` by the current command in `WHAT`. Here deploy has an idle shell open from 10.0.1.5.

**Why it is effective:** before a reboot or a risky change you see who else is working on the box; in a security check, an active shell from an unknown address stands out at once.

**Compared with `ps aux | grep sshd`:** ps shows the sshd processes behind every connection, including non-terminal ones (scp, tunnels) that w misses, but no source address, idle time or current command.

**Trap:** like `last`, w and who list only sessions with a terminal: `ssh host command`, scp, sftp, `ssh -N` tunnels and `docker exec` shells are invisible, so "nobody is logged in" is not proof. A large `IDLE` can still be a tmux session someone is about to use.

**Next step:** every SSH connection, terminal or not → `ss -tnp state established '( sport = :22 )'`. Details or ending a session → `loginctl list-sessions`, `loginctl terminate-session ID`. History → `last -i`.

### auditctl / augenrules — record every change to a file, with the human behind it
Match: auditctl, augenrules
Instead of: inotifywait, comparing file timestamps
Safety: changes state: `-w` adds and `-W` removes a rule in the running kernel; `augenrules --load` replaces all loaded rules with those in /etc/audit/rules.d · `-l` and `-s` only read · needs root

**In one line:** `auditctl` controls the kernel's audit system: a watch rule makes it record every access of a chosen kind to a file or directory, with the login user behind it; `augenrules --load` loads the permanent rule files.

**Read the command:** `auditctl -w /etc/passwd -p wa -k passwd_watch`

| Part | Meaning |
|---|---|
| `-w /etc/passwd` | watch this path (a directory watch covers everything below it) |
| `-p wa` | record writes (`w`) and attribute changes (`a`: mode, owner); also `r` read and `x` execute |
| `-k passwd_watch` | a key (label) to find the events later: `ausearch -k passwd_watch` |
| `-W …` | the same rule with capital W: remove that watch |
| `-l` | list the rules loaded now |
| `-s` | status: `enabled`, `lost` events, `backlog` |
| `augenrules --load` | merge `/etc/audit/rules.d/*.rules` into audit.rules and load them: rules that survive reboot |

**What the output tells you:**

```
$ sudo auditctl -l
-w /etc/passwd -p wa -k passwd_watch
-w /usr/bin/node -p x -k who-starts-node
$ sudo auditctl -s
enabled 1
failure 1
…
backlog_limit 8192
lost 0
backlog 0
```

`enabled 1` = recording (`2` = immutable: rules locked until reboot). `lost` counts events dropped because the backlog was full: if it grows, the rules are too noisy. The `x` watch on `/usr/bin/node` records every start of node with its parent process, which answers "what keeps launching this?".

**Why it is effective:** each event carries the `auid`, the user who originally logged in, which survives `sudo` and `su`, plus the program and the result, so "who changed /etc/passwd?" gets evidence instead of guesses.

**Compared with `inotifywait`:** inotify reports live that a file changed while you watch; it records neither who nor which program, and keeps no history.

**Trap:** auditctl rules live only in the running kernel: a reboot or the next `augenrules --load` drops them, so permanent rules belong in `/etc/audit/rules.d/`. A watch whose directory does not exist fails to load. In immutable mode (`-e 2`) nothing can change until reboot. Watches on busy paths fill `/var/log/audit` fast.

**Next step:** read the events → `ausearch -k KEY -i`; counts per key → `aureport -k --summary`. Rules missing after reboot → `augenrules --check`, `systemctl status auditd`. `lost` rising → fewer or narrower rules.

### ausearch / aureport — read the audit log: who did it, and what did SELinux deny?
Match: ausearch, aureport, audit2why, sealert
Instead of: grep on /var/log/audit/audit.log
Safety: read-only · needs root (the audit log is root-only)

**In one line:** `ausearch` finds audit events by key, type, file, user or time and keeps each event's records together; `aureport` turns the same log into summaries (logins, authentications, events per key).

**Read the command:** `ausearch -k sudoers -i --start today`

| Part | Meaning |
|---|---|
| `-k sudoers` | events recorded by rules with this key |
| `-i` | interpret: UIDs to names, syscall numbers to names, readable times |
| `--start today` | from midnight (`-ts` is the short form); also `recent` = the last 10 minutes, `this-week`, or a date |
| `-m AVC,USER_AVC -ts recent` | by record type: SELinux denials of the last 10 minutes |
| `-f /etc/passwd` | events about this file (only if a rule recorded them) |
| `aureport --summary` | an overview: logins, failed authentications, events by type |
| `aureport -au` | authentication attempts: who, from where, success or failure |
| `aureport -k --summary` | events per key: which rule fires, and which never does |

**What the output tells you:**

```
type=PROCTITLE msg=audit(10/04/2026 14:03:11.204:812) : proctitle=vi /etc/sudoers
type=PATH msg=audit(10/04/2026 14:03:11.204:812) : item=1 name=/etc/sudoers … nametype=NORMAL
type=SYSCALL msg=audit(10/04/2026 14:03:11.204:812) : syscall=openat success=yes … auid=ops uid=root … comm=vi exe=/usr/bin/vim.basic key=sudoers
```

The three records share the serial `:812`, so they are one event. `auid=ops` is the person who logged in; `uid=root` is the identity after sudo. Someone edited sudoers with plain vi instead of visudo, and the log names them.

**Why it is effective:** one event spans several records tied by a serial number, and the raw log keeps numbers (`uid=1001`, hex proctitles, syscall numbers); ausearch groups the records and translates them.

**Compared with `grep` on audit.log:** fine for a quick "is there anything for this key?", but it splits events apart and leaves the numbers raw.

**Trap:** ausearch finds only what a rule recorded: `<no matches>` can mean "no rule", not "nothing happened". `auid=unset` (4294967295) is a daemon started at boot, not a person. `-ts recent` covers only 10 minutes: older denials need `-ts today`. The log rotates by size (`/etc/audit/auditd.conf`).

**Next step:** an AVC denial → the SELinux cards (label, port or boolean). A person changed a file → `last` and `journalctl -u ssh` for their session. A key never fires → `auditctl -l` (is the rule loaded?), `aureport -k --summary`. Related: `audit2why < /var/log/audit/audit.log` says why each denial happened (wrong label, boolean off), and `sealert -a /var/log/audit/audit.log` (setroubleshoot-server) prints advice per denial; check a suggested fix before applying it.

### lynis — how hardened is this host, and what should I fix first?
Match: lynis
Instead of: —
Safety: read-only audit: runs a few hundred local checks and writes /var/log/lynis.log and /var/log/lynis-report.dat · run it with sudo for complete results

**In one line:** `lynis audit system` checks the host (SSH, PAM, kernel settings, packages, file permissions, logging, firewall…) and prints warnings, suggestions with test IDs, and a hardening index from 0 to 100 you can track over time.

**Read the command:** `lynis audit system --quick 2>/dev/null`

| Part | Meaning |
|---|---|
| `audit system` | audit this host (`audit dockerfile FILE` checks a Dockerfile instead) |
| `--quick` | do not pause between sections: non-interactive |
| `2>/dev/null` | hide error noise from the terminal |
| `/var/log/lynis-report.dat` | machine-readable results: `hardening_index=`, `warning[]=`, `suggestion[]=` |
| `lynis show details SSH-7408` | explain one test and what it found |
| `skip-test=` in `/etc/lynis/custom.prf` | a documented exception: accept a finding on purpose |

**What the output tells you:**

```
  Warnings (1):
  ----------------------------
  ! Found one or more vulnerable packages. [PKGS-7392]
  Suggestions (41):
  ----------------------------
  * Consider hardening SSH configuration [SSH-7408]
      - Details  : AllowTcpForwarding (set YES to NO)
  …
  Hardening index : 61 [############        ]
```

Warnings come first (here: unpatched packages). Each suggestion names the setting and a test ID. The index is a trend for your own hosts, not a grade to compare between companies.

**Why it is effective:** hundreds of checks in a minute, each with an ID you can look up, fix, skip with a reason and re-test, so hardening becomes a measurable list instead of an opinion.

**Trap:** suggestions are not orders: `AllowTcpForwarding no` breaks SSH tunnels and editor remote sessions, and switching off IP forwarding (a common benchmark item) cuts every Docker container off the network. Lynis is not a CIS benchmark: use Ubuntu's `usg` or OpenSCAP for formal compliance. Without root many tests are skipped.

**Next step:** warnings → patch (`apt list --upgradable`), then rerun. Each suggestion → the matching card (`sshd -T`, `sysctl`, `auditctl`), changed on a test VM first. Track `hardening_index` per host after every change.
