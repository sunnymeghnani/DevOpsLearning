# 06 — Logs & Journal

Rule zero of troubleshooting: **read the logs before restarting anything.**

---

## 1. journalctl (systemd journal)

```bash
journalctl -xe                        # end of journal + explanations — first stop after a failure
journalctl -u nginx                   # one service's logs
journalctl -u nginx -f                # follow live (like tail -f)
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx --since "2026-08-08 22:00" --until "2026-08-08 23:00"
journalctl -p err -b                  # only err+ severity, current boot
journalctl -b -1                      # PREVIOUS boot (what happened before the crash/reboot?)
journalctl -k                         # kernel messages only (≈ dmesg with timestamps)
journalctl _PID=1234                  # by PID
journalctl -u app -o json-pretty      # structured output
journalctl -g "timeout|refused"       # grep within the journal
journalctl --disk-usage               # journal size on disk
journalctl --vacuum-size=500M         # shrink journal
journalctl --list-boots               # boot history
```
Priorities for `-p`: emerg alert crit err warning notice info debug.

`journalctl -b -1` requires persistent journal:
```bash
mkdir -p /var/log/journal && systemctl restart systemd-journald
```

## 2. dmesg (kernel ring buffer)

```bash
dmesg -T                              # human timestamps
dmesg -T | tail -50                   # recent kernel events
dmesg -T --level=err,warn             # problems only
dmesg -Tw                             # follow live
dmesg -T | grep -iE "oom|kill"        # OOM killer evidence
dmesg -T | grep -iE "i/o error|sd[a-z]|nvme|xvd"   # disk errors
dmesg -T | grep -iE "link (up|down)|eth|ens"       # NIC flaps
dmesg -T | grep -i segfault           # app crashes
```

## 3. Classic log files (/var/log)

| File (Debian/Ubuntu) | File (RHEL/CentOS) | Contents |
|---|---|---|
| /var/log/syslog | /var/log/messages | general system log |
| /var/log/auth.log | /var/log/secure | logins, sudo, sshd |
| /var/log/kern.log | (in messages) | kernel |
| /var/log/dpkg.log | /var/log/dnf.log, yum.log | package changes |
| /var/log/cloud-init.log, cloud-init-output.log | same | first-boot/user-data on cloud VMs |
| /var/log/nginx/{access,error}.log | same | web server |
| /var/log/audit/audit.log | same | auditd/SELinux denials |
| /var/log/btmp (`lastb`) | same | FAILED logins |
| /var/log/wtmp (`last`) | same | login/reboot history |

## 4. Reading & watching logs

```bash
tail -f /var/log/syslog                       # follow
tail -F /var/log/app.log                      # -F survives rotation — use for long watches
tail -n 200 file.log                          # last 200 lines
less +F file.log                              # follow inside less; Ctrl-C to scroll, F to resume
less +G file.log                              # open at the END of a huge file
zless file.log.2.gz ; zgrep ERROR *.gz        # rotated compressed logs
multitail /var/log/nginx/*.log                # several at once (if installed)
```

### grep patterns that pull their weight
```bash
grep -i error app.log                         # case-insensitive
grep -riE "error|fail|fatal|panic" /var/log/  # recursive multi-pattern
grep -v -e DEBUG -e healthcheck app.log       # filter noise OUT
grep -C 5 "OutOfMemory" app.log               # 5 lines of context around match
grep -c "500 " access.log                     # count occurrences
awk '$9>=500' access.log | tail               # nginx/apache: only 5xx lines
awk '{print $9}' access.log | sort | uniq -c | sort -rn    # status code histogram
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head   # top client IPs
```

## 5. Log rotation issues

```bash
cat /etc/logrotate.conf ; ls /etc/logrotate.d/
logrotate -d /etc/logrotate.d/app             # DRY RUN — debug config
logrotate -f /etc/logrotate.d/app             # force a rotation now
```
Classic failure: log rotated (moved) but app keeps writing to the old fd →
disk fills "invisibly" → see `lsof +L1` in [01-storage-disk.md](01-storage-disk.md).
Fix with `copytruncate` in logrotate config, or a postrotate reload signal.

## 6. Sending test messages & remote syslog

```bash
logger "test message from troubleshooting"    # writes into syslog — verify pipeline
logger -p local0.err -t myapp "test error"
grep -E "@|target" /etc/rsyslog.conf /etc/rsyslog.d/*   # where logs are forwarded
systemctl status rsyslog
```

## Where do I even look? (by symptom)

| Symptom | Look at |
|---|---|
| Service won't start | `journalctl -xeu <svc>`, then the app's own log file |
| Box rebooted unexpectedly | `last -x reboot`, `journalctl -b -1 -e`, `dmesg` after boot |
| Process disappeared | `dmesg -T | grep -i oom`, `journalctl -u <svc>` |
| Login/ssh problems | `/var/log/auth.log` or `/var/log/secure`, `lastb` |
| Disk/filesystem weirdness | `dmesg -T | grep -iE "error|ext4|xfs"` |
| Cloud VM misconfigured at boot | `/var/log/cloud-init-output.log` |
| Cron job didn't run | `grep CRON /var/log/syslog`, `journalctl -u cron` |
