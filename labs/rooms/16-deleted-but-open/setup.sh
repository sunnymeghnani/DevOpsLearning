#!/bin/bash
# Room 16 (disk-full): the log volume is ~90% full, but du finds almost nothing: a deleted log is still open.
# The "volume" is a 48 MB tmpfs on /var/log/metrics (memory-backed, inside the lab only; never the host disk).
# Broken state:
#  - metrics-agent.service (root, bash) appends to /var/log/metrics/agent.log through fd 1 and only reopens on SIGHUP;
#  - /etc/logrotate.d/metrics-agent has "compress" but neither copytruncate nor a postrotate that tells the agent;
#  - a forced rotation renamed the 44 MB agent.log to agent.log.1, gzip deleted agent.log.1, and the agent
#    still writes to that deleted inode: df ~90%, du a few hundred KB.
set -euo pipefail
V=/var/log/metrics

systemctl stop metrics-agent >/dev/null 2>&1 || true
systemctl reset-failed metrics-agent >/dev/null 2>&1 || true
install -d -m 0755 $V
mountpoint -q $V && umount $V
mount -t tmpfs -o size=48m,mode=0755 metrics-vol $V

cat > /usr/local/bin/metrics-agent <<'SH'
#!/bin/bash
# metrics-agent 1.4: flushes samples to its log every second. Reopens the log on SIGHUP.
LOG=/var/log/metrics/agent.log
exec >>"$LOG" 2>&1
trap 'exec >>"$LOG" 2>&1; echo "$(date -Is) INFO reopened $LOG"' HUP
n=0
while :; do
  n=$((n + 1))
  echo "$(date -Is) INFO flush batch=$n samples=120 queue=0"
  sleep 1
done
SH
chmod 755 /usr/local/bin/metrics-agent
cat > /etc/systemd/system/metrics-agent.service <<'UNIT'
[Unit]
Description=Metrics agent (ships host metrics)

[Service]
ExecStart=/usr/local/bin/metrics-agent
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/logrotate.d/metrics-agent <<'CONF'
/var/log/metrics/agent.log {
    daily
    rotate 3
    compress
    missingok
    notifempty
    create 0640 root adm
}
CONF
systemctl daemon-reload
systemctl enable metrics-agent >/dev/null 2>&1
systemctl start metrics-agent
for _ in $(seq 30); do [ -s $V/agent.log ] && break; sleep 0.1; done

# weeks of debug logging, compressed into one burst (44 MB of text)
{ yes "$(date -Is) DEBUG sample host=web-01 cpu=0.42 mem=0.61 disk=0.77 net_rx=1834 net_tx=922" || true; } | head -c 44M >> $V/agent.log
# the nightly rotation: rename to agent.log.1, create a new agent.log, gzip agent.log.1 (gzip deletes it)
logrotate -f -s /var/lib/logrotate/status /etc/logrotate.d/metrics-agent
