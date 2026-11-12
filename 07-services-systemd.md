# 07 — Services & systemd

Typical symptoms: service won't start, keeps restarting, slow boot, wrong
service enabled, timer/cron didn't run.

---

## 1. Service status & control

```bash
systemctl status nginx                # state, PID, last log lines — start here
systemctl start|stop|restart nginx
systemctl reload nginx                # re-read config without dropping connections
systemctl enable --now nginx          # enable at boot AND start now
systemctl disable --now nginx
systemctl is-active nginx ; systemctl is-enabled nginx
systemctl list-units --type=service --state=running
systemctl --failed                    # ALL failed units — great morning check
systemctl reset-failed nginx          # clear failed state / restart-limit counter
```

Reading `systemctl status`:
```
● app.service - My App
   Active: activating (auto-restart) (Result: exit-code) since ...
  Process: 4321 ExecStart=/usr/bin/app (code=exited, status=1/FAILURE)
```
- `active (running)` good; `failed` dead; `activating (auto-restart)` = **crash looping**
- `status=1/FAILURE` app exited with code 1 → read its logs
- `status=203/EXEC` binary missing/not executable / bad ExecStart path
- `status=217/USER` bad User= in unit
- `oom-kill` → killed by kernel, see 04-memory.md
- "Start request repeated too quickly" → hit StartLimit; fix cause then `reset-failed`

Always pair with:
```bash
journalctl -xeu app.service           # the WHY behind the failure
journalctl -u app.service -f          # watch while you retry
```

## 2. Unit files — what is this service actually configured to do?

```bash
systemctl cat app.service             # effective unit file + drop-ins
systemctl show app.service            # every effective property
systemctl show app -p Environment,ExecStart,User,LimitNOFILE
systemctl list-dependencies app.service
systemd-analyze verify app.service    # syntax check a unit
```
Locations: `/etc/systemd/system/` (yours, wins) → `/run/systemd/system` →
`/usr/lib/systemd/system/` (package default). Override safely:
```bash
systemctl edit app.service            # creates a drop-in override
systemctl daemon-reload               # REQUIRED after any manual unit edit
```
Forgot `daemon-reload`? systemd warns: "unit file changed on disk".

## 3. Boot problems & slowness

```bash
systemd-analyze                       # total boot time
systemd-analyze blame                 # slowest units
systemd-analyze critical-chain        # dependency chain that gated boot
systemctl list-jobs                   # jobs stuck right now (e.g. waiting on a mount)
systemctl get-default                 # boot target (multi-user vs graphical)
systemctl set-default multi-user.target
last -x reboot | head                 # reboot history
```
Classic hang: a broken `/etc/fstab` entry blocks boot for 90s+ ("A start job is
running for dev-disk-by...") → fix fstab, add `nofail` to non-critical mounts,
verify with `findmnt --verify`.

## 4. Timers (systemd cron)

```bash
systemctl list-timers --all           # every timer, last run, next run
journalctl -u backup.timer -u backup.service
systemd-run --on-active=30s /bin/touch /tmp/proof   # ad-hoc scheduled run
```

## 5. Classic cron (still everywhere)

```bash
crontab -l ; crontab -l -u appuser    # user crontabs
ls /etc/cron.d/ /etc/cron.{daily,hourly,weekly,monthly}/
cat /etc/crontab
grep CRON /var/log/syslog | tail      # did it fire? (RHEL: /var/log/cron)
```
Cron didn't do what you expected — usual causes:

- **PATH is minimal** in cron: use absolute paths in the job
- `%` must be escaped in crontab lines
- no trailing newline at end of crontab file
- script relies on env vars that only exist in your login shell
- output went to mail: add `>> /var/log/job.log 2>&1` to see errors

## 6. Legacy init (old boxes)

```bash
service nginx status                  # SysV wrapper
chkconfig --list                      # RHEL6-era enablement
/etc/init.d/nginx status
```

## Decision tree: "service won't start"

```
systemctl status svc
├── status=203/EXEC        → bad path/permissions on ExecStart binary
├── status=1..n/FAILURE    → journalctl -xeu svc + app's own log → config error? port taken?
│                            (port taken: ss -tlnp sport = :PORT)
├── auto-restart loop      → journalctl -u svc | tail -100 → fix root cause → reset-failed
├── timeout                → app not signalling readiness: wrong Type= (simple vs forking vs notify)
└── "changed on disk"      → systemctl daemon-reload, retry
```
