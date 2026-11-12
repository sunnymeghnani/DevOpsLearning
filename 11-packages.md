# 11 — Package Management Troubleshooting

Typical symptoms: install fails, broken dependencies, "could not get lock",
repo errors, "which package owns this file", service broke after update.

---

## 1. Debian / Ubuntu (apt, dpkg)

### Daily use (apt)
```bash
apt update                              # refresh package lists (do this before install)
apt install pkg ; apt remove pkg
apt upgrade                             # upgrade all (no removals)
apt full-upgrade                        # upgrade allowing removals
apt search keyword ; apt show pkg
apt list --installed | grep nginx
apt list --upgradable
apt policy nginx                        # available versions + which repo wins ★
apt install nginx=1.24.0-1ubuntu1       # specific version
```

### Troubleshooting (apt)
```bash
apt --fix-broken install                # fix broken/interrupted dependency state ★
dpkg --configure -a                     # finish interrupted configuration
dpkg -l | grep -v '^ii'                 # packages NOT in normal state (iU, rc, iF...)
apt-mark showhold                       # held packages block upgrades
apt-mark hold pkg / unhold pkg
apt-get clean                           # clear /var/cache/apt (disk space)
```

**"Could not get lock /var/lib/dpkg/lock-frontend"** — another apt is running
(often `unattended-upgrades` right after boot):
```bash
ps aux | grep -E "apt|dpkg|unattended" # who holds it — normally just WAIT for it
lsof /var/lib/dpkg/lock-frontend
# Only if the holder is truly dead: rm the lock files, then: dpkg --configure -a
```

### dpkg — file/package mapping
```bash
dpkg -L nginx                           # files a package installed
dpkg -S /usr/sbin/nginx                 # which package owns a file
dpkg -s nginx                           # installed status/version
dpkg -i pkg.deb ; apt install ./pkg.deb # local .deb (apt resolves deps)
ls /var/log/apt/history.log*            # what was installed/removed WHEN ★
                                        #   ("what changed before it broke?")
```

### Repo problems
```bash
cat /etc/apt/sources.list /etc/apt/sources.list.d/*.list
apt-key list                            # legacy keys (deprecated)
ls /etc/apt/trusted.gpg.d/ /usr/share/keyrings/
# "NO_PUBKEY XXXX" → missing repo key → fetch key into /usr/share/keyrings + signed-by
# "Release file ... is not valid yet" → CLOCK WRONG → see 12-time-ntp.md
# 404s on update → dead/old repo or wrong distro codename in sources.list
```

## 2. RHEL / CentOS / Rocky / Amazon Linux (dnf/yum, rpm)

### Daily use (dnf)
```bash
dnf install pkg ; dnf remove pkg ; dnf update
dnf search keyword ; dnf info pkg
dnf list installed | grep nginx
dnf --showduplicates list nginx         # all available versions
dnf install nginx-1.24.0                # specific version
dnf history                             # transaction history ★
dnf history info 42                     # what exactly changed in transaction 42
dnf history undo 42                     # roll back a transaction (best effort)
dnf downgrade pkg
```

### Troubleshooting (dnf)
```bash
dnf clean all && dnf makecache          # fix corrupt/stale metadata
dnf repolist ; dnf repolist -v          # enabled repos
dnf config-manager --set-disabled repo  # disable a broken repo to unblock updates
dnf versionlock list                    # locked versions (dnf-plugin-versionlock)
package-cleanup --problems              # older yum: dependency problems
rpm --rebuilddb                         # corrupt rpm database
```

### rpm — file/package mapping & verification
```bash
rpm -qa | grep nginx                    # installed packages
rpm -ql nginx                           # files of a package
rpm -qf /usr/sbin/nginx                 # which package owns a file
rpm -qi nginx                           # package info
rpm -V nginx                            # VERIFY: which packaged files were modified ★
                                        #   (S=size M=mode 5=checksum U/G=owner)
rpm -Va | head                          # verify everything (config drift/tampering)
```

## 3. Cross-distro helpers

```bash
which -a python3 ; type -a python3      # which binary actually runs (PATH order!)
command -v terraform                    # portable existence check
ldd /usr/bin/app                        # shared-library deps; "not found" = missing lib
ldconfig -p | grep libssl               # is the lib registered?
snap list ; snap refresh                # Ubuntu snaps (note: snapd auto-updates!)
pip list ; pip check                    # Python deps consistency
needs-restarting -r                     # RHEL: reboot needed after updates?
checkrestart / needrestart              # Debian: services running old libs after upgrade
```

## Common scenarios

| Symptom | Approach |
|---|---|
| "It worked yesterday" | `/var/log/apt/history.log` or `dnf history` — what updated? downgrade/pin |
| Binary exists but "command not found" | PATH: `echo $PATH`, `hash -r`; or noexec mount |
| "error while loading shared libraries: libfoo.so.1" | `ldd binary`, install lib, or `ldconfig` after manual lib install |
| Config file overwritten by update | Debian keeps `.dpkg-old/.dpkg-dist`; RHEL keeps `.rpmsave/.rpmnew` — diff them |
| Update fails: GPG/signature | wrong repo key, or **system clock wrong** (12-time-ntp.md) |
| Repo unreachable (air-gapped/on-prem) | mirror/local repo, `dnf config-manager`, or offline: `apt-get download` + `dpkg -i` / `dnf download` + `rpm -i` |
