# 10 — Users, Permissions & Security

Typical symptoms: "Permission denied", sudo not working, account locked,
SELinux silently blocking, auditing "who did what".

---

## 1. Identity — who am I / who exists

```bash
id                                  # my uid, gid, groups
id appuser                          # someone else's
whoami ; groups
getent passwd appuser               # account entry (works with LDAP/SSSD too, unlike
                                    #   reading /etc/passwd directly)
getent group docker                 # who's in a group
sudo -l                             # what I'm allowed to sudo (first sudo-debug command)
w ; who                             # who is logged in now, from where
last | head                         # recent logins & reboots
lastb | head                        # recent FAILED logins (root only)
lastlog | grep -v Never             # last login per account
```

**Gotcha:** after being added to a group (e.g. docker) you must **log out/in**
(or `newgrp docker`) — existing sessions don't pick up new groups.

## 2. Account state

```bash
passwd -S appuser                   # P=usable, L=locked, NP=no password
chage -l appuser                    # password/account expiry — expired = weird auth failures
usermod -L appuser ; usermod -U appuser     # lock / unlock
faillock --user appuser             # RHEL: failed-attempt lockout status
faillock --user appuser --reset     # clear the lockout
pam_tally2 --user appuser           # older equivalent
grep appuser /etc/shadow            # '!' or '*' prefix in hash field = locked/no login
getent passwd appuser | cut -d: -f7 # shell = /sbin/nologin? that's why they can't log in
```

## 3. File permissions

```bash
ls -l file ; ls -ld dir             # mode, owner, group (d needs x to enter!)
stat file                           # full metadata incl. octal mode
namei -l /var/www/app/config.yml    # permissions of EVERY path component —
                                    #   finds the blocking parent dir instantly
chmod 644 file ; chmod 755 dir ; chmod -R g+w dir
chown appuser:appgroup file ; chown -R appuser: dir
umask                               # default-permission mask of this shell
find /app ! -user appuser -ls       # files NOT owned by expected user
find / -xdev -perm -4000 -type f 2>/dev/null   # setuid binaries (security review)
```
`namei -l` example — the underrated gem:
```
$ namei -l /data/app/secret.key
f: /data/app/secret.key
drwxr-xr-x root root /
drwx------ root root data          ← appuser can't traverse THIS dir
-rw-r--r-- app  app  secret.key
```

### ACLs (when ls -l looks right but access still fails — check for `+`)
```bash
getfacl file                        # full ACL list
setfacl -m u:appuser:rw file        # grant one user rw
setfacl -m d:u:appuser:rwX dir      # default ACL: inherited by new files
setfacl -b file                     # remove all ACLs
```

### Immutable flag (chmod/chown/rm all fail even as root)
```bash
lsattr file                         # 'i' flag = immutable
chattr -i file                      # remove it
```

## 4. sudo problems

```bash
sudo -l                             # effective rules for me
visudo -c                           # syntax-check sudoers (a broken sudoers can lock
                                    #   everyone out — ALWAYS edit via visudo)
ls /etc/sudoers.d/
grep sudo /var/log/auth.log         # who ran what / why denied  (RHEL: /var/log/secure)
```
"user is not in the sudoers file" → add to wheel (RHEL) / sudo (Debian) group:
`usermod -aG sudo appuser` — then re-login.

## 5. SELinux (RHEL/CentOS/Amazon Linux) — the invisible "permission denied"

When ownership and mode are all correct but access is still denied, suspect SELinux.

```bash
getenforce                          # Enforcing / Permissive / Disabled
sestatus                            # fuller status
ls -Z /var/www/html/                # file contexts
ps -eZ | grep nginx                 # process contexts
ausearch -m avc -ts recent          # recent denials from the audit log ★
journalctl -t setroubleshoot        # human-readable explanations (if installed)
audit2why < /var/log/audit/audit.log | tail       # explain denials
setenforce 0                        # TEMPORARILY permissive — retest; if it now works,
                                    #   it was SELinux. setenforce 1 to re-enable. Don't
                                    #   leave it off; fix the label/boolean instead:
restorecon -Rv /var/www/html        # fix file contexts to policy defaults
chcon -t httpd_sys_content_t file   # set a context manually (non-persistent)
semanage fcontext -a -t httpd_sys_content_t "/srv/www(/.*)?" && restorecon -R /srv/www
getsebool -a | grep httpd           # policy booleans
setsebool -P httpd_can_network_connect on   # e.g. let nginx proxy to upstream
semanage port -l | grep http        # allowed ports per service; add: semanage port -a -t http_port_t -p tcp 8081
```
Classic cases: files moved (not copied) into /var/www keep old context; web server
on a non-standard port; daemon needing outbound network → boolean.

### AppArmor (Ubuntu/Debian)
```bash
aa-status                           # loaded profiles, enforce vs complain
dmesg | grep -i apparmor            # denials
aa-complain /etc/apparmor.d/usr.sbin.nginx   # switch one profile to complain mode
```

## 6. Auditing — "who did what, when?"

```bash
ausearch -f /etc/passwd             # who touched a file (needs an audit rule)
auditctl -w /etc/passwd -p wa -k passwd_watch    # add watch rule
aureport --summary ; aureport -au   # audit summaries, auth attempts
history ; HISTTIMEFORMAT="%F %T " history        # shell history (per user)
cat /home/*/.bash_history           # (root) other users' history — forensics
find /etc -newermt "2026-08-08" -type f          # files changed since a date
rpm -Va | head                      # RHEL: packaged files that were MODIFIED
debsums -c 2>/dev/null | head       # Debian equivalent
```

## 7. Quick security triage of a suspicious box

```bash
w ; last -20                        # who's on / was on
ss -tulpn                           # unexpected listeners?
ps auxf                             # odd processes / odd parents?
crontab -l ; ls /etc/cron*          # persistence via cron?
cat /etc/passwd | awk -F: '$3==0'   # extra uid-0 accounts?!
find / -xdev -mmin -60 -type f 2>/dev/null | grep -vE "^/(proc|sys|run|var/log)"  # recent file changes
lsof -i -nP | grep -v LISTEN        # active outbound connections
```

## Decision tree: "Permission denied"

```
1. As WHICH user does the app run?  ps -o user= -p PID
2. namei -l /full/path              → parent dir missing x? owner/group wrong?
3. getfacl file                     → ACL overriding? ('+' in ls -l)
4. lsattr file                      → immutable flag?
5. getenforce → Enforcing?          → ausearch -m avc -ts recent → SELinux label/boolean
6. AppArmor (Ubuntu)?               → aa-status, dmesg | grep -i apparmor
7. Filesystem mounted ro or noexec? → findmnt /path → 'ro' / 'noexec' flags
```
