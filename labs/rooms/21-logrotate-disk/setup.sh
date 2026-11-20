#!/bin/bash
# Room 21 (journald-logs): logs keep eating the disk.
# Broken state:
#  - orders-api writes /var/log/orders-api/app.log (already ~30 MB) and logrotate never rotates it: its config has
#    "maxsize 20 M" (a space inside the size) -> "bad size", logrotate skips the whole file and exits 1;
#  - that made logrotate.service fail every day, so someone disabled logrotate.timer to stop the alerts;
#  - a debugging drop-in made the journal persistent with SystemMaxUse=8G.
set -euo pipefail

id orders >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin orders

# the app: one line every 0.2 s, reopening the file for each line (">>"), so a renamed file is let go at once
cat > /usr/local/bin/orders-api <<'SH'
#!/bin/bash
# orders-api (stand-in): access log lines
i=0
while :; do
  i=$((i + 1))
  echo "$(date -Is) INFO GET /api/orders/$((RANDOM % 9000 + 1000)) 200 $((RANDOM % 90 + 5))ms req=$i" >> /var/log/orders-api/app.log
  sleep 0.2
done
SH
chmod 755 /usr/local/bin/orders-api
cat > /etc/systemd/system/orders-api.service <<'UNIT'
[Unit]
Description=orders-api (lab stand-in)
After=network.target

[Service]
User=orders
Group=orders
ExecStart=/usr/local/bin/orders-api
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl stop orders-api.service >/dev/null 2>&1 || true
install -d -o orders -g orders -m 0755 /var/log/orders-api
find /var/log/orders-api -mindepth 1 -maxdepth 1 -name 'app.log*' -delete
# about 30 MB of history that never got rotated
yes '2026-11-09T22:14:03+00:00 INFO GET /api/orders/4711 200 18ms req=1 user=web-07 ua="okhttp/4.12"' \
  | head -c 30M > /var/log/orders-api/app.log || true
chown orders:orders /var/log/orders-api/app.log
chmod 0644 /var/log/orders-api/app.log
touch -d '9 days ago' /var/log/orders-api/app.log

cat > /etc/logrotate.d/orders-api <<'CONF'
# orders-api logs (OPS-1187)
/var/log/orders-api/*.log {
    daily
    rotate 7
    maxsize 20 M
    compress
    delaycompress
    missingok
    notifempty
}
CONF
chmod 644 /etc/logrotate.d/orders-api

# the state the box was found in: today's run failed, and the timer was switched off "to stop the alerts"
rm -f /var/lib/logrotate/status
systemctl reset-failed logrotate.service >/dev/null 2>&1 || true
systemctl start logrotate.service >/dev/null 2>&1 || true
systemctl disable --now logrotate.timer >/dev/null 2>&1

# journal: persistent, with a far too generous limit from a debugging session
mkdir -p /etc/systemd/journald.conf.d   # not on every Ubuntu (the lab image has it)
find /etc/systemd/journald.conf.d -maxdepth 1 -name '[6-9]*.conf' -delete
cat > /etc/systemd/journald.conf.d/50-orders-debug.conf <<'CONF'
# OPS-1187 debugging (2026-10-12): keep everything across reboots
[Journal]
Storage=persistent
SystemMaxUse=8G
CONF
mkdir -p /var/log/journal
systemctl restart systemd-journald
journalctl --flush >/dev/null 2>&1 || true

systemctl daemon-reload
systemctl enable orders-api.service >/dev/null 2>&1
systemctl restart orders-api.service
