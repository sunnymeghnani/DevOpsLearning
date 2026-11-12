#!/bin/bash
# Room 05 (processes-signals): a worker that never reaps its children, and a runaway that ignores SIGTERM.
# Broken state:
#  - report-worker.service forks one child per job and never wait()s -> 60 zombies (<defunct>) pile up;
#  - /usr/local/bin/backup-sync (left over from last night's cron) burns CPU and traps TERM/INT/HUP.
set -euo pipefail

# --- reset (idempotent) ---
systemctl stop report-worker.service >/dev/null 2>&1 || true
pkill -KILL -x backup-sync >/dev/null 2>&1 || true

# --- the leaky worker ---
install -d /opt/report-worker /var/spool/report-worker
cat > /opt/report-worker/worker.py <<'PY'
#!/usr/bin/python3
"""report-worker 0.9: renders one report per job file in /var/spool/report-worker."""
import ctypes, glob, os, time

ctypes.CDLL(None).prctl(15, b"report-worker", 0, 0, 0)   # PR_SET_NAME: show as "report-worker" in ps
SPOOL = "/var/spool/report-worker"

while True:
    for job in sorted(glob.glob(SPOOL + "/*.job")):
        pid = os.fork()
        if pid == 0:                      # child: "render" the report, then exit
            os.execv("/bin/sh", ["sh", "-c", "exit 0"])
        os.unlink(job)                    # parent: next job. BUG: never calls os.waitpid(pid, 0)
    time.sleep(2)
PY
chmod 755 /opt/report-worker/worker.py
cat > /etc/systemd/system/report-worker.service <<'UNIT'
[Unit]
Description=Report worker (renders queued reports)
After=network.target

[Service]
ExecStart=/opt/report-worker/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
rm -f /var/spool/report-worker/*.job
for i in $(seq -w 1 60); do   # stays below the unit's TasksMax (15% of 512 here)
   : > "/var/spool/report-worker/report-$i.job"; done
systemctl daemon-reload
systemctl enable report-worker.service >/dev/null 2>&1
systemctl start report-worker.service
for _ in $(seq 50); do                      # wait until the queue is drained
  [ -z "$(ls -A /var/spool/report-worker)" ] && break
  sleep 0.1
done

# --- the runaway ---
cat > /usr/local/bin/backup-sync <<'SH'
#!/bin/bash
# backup-sync: nightly sync wrapper. "Do not let anything interrupt a sync."
trap '' TERM INT HUP
while :; do :; done
SH
chmod 755 /usr/local/bin/backup-sync
setsid nice -n 5 /usr/local/bin/backup-sync </dev/null >/dev/null 2>&1 &
sleep 0.3
