#!/bin/bash
# Room 15 (systemd-units): a unit in a restart loop until systemd gives up (start-limit-hit).
# Broken state, after the export-worker 2.0 package moved its files:
#  - EnvironmentFile=/etc/export-worker/worker.env does not exist (only worker.env.example ships) -> 'resources';
#  - ExecStart= still points at the 1.x path /usr/local/bin/export-worker (now /opt/export-worker/bin/export-worker);
#  - Restart=on-failure + RestartSec=300ms -> five failures in a few seconds -> "Start request repeated too quickly".
set -euo pipefail

systemctl stop export-worker >/dev/null 2>&1 || true
systemctl reset-failed export-worker >/dev/null 2>&1 || true

id exporter >/dev/null 2>&1 || useradd --system --home-dir /var/lib/export-worker --shell /usr/sbin/nologin exporter
install -d -o exporter -g exporter -m 0750 /var/lib/export-worker
install -d /opt/export-worker/bin /etc/export-worker
cat > /opt/export-worker/bin/export-worker <<'SH'
#!/bin/bash
# export-worker 2.0: picks up export jobs and writes a heartbeat every 5 s.
: "${EXPORT_DIR:?EXPORT_DIR is not set (copy /etc/export-worker/worker.env.example to worker.env)}"
[ -d "$EXPORT_DIR" ] && [ -w "$EXPORT_DIR" ] || { echo "export-worker: cannot write to $EXPORT_DIR" >&2; exit 1; }
echo "export-worker 2.0 started: queue=${2:-default} dir=$EXPORT_DIR"
while :; do date -Is > "$EXPORT_DIR/heartbeat"; sleep 5; done
SH
chmod 755 /opt/export-worker/bin/export-worker
rm -f /usr/local/bin/export-worker /etc/export-worker/worker.env
cat > /etc/export-worker/worker.env.example <<'ENV'
# export-worker 2.0 settings: copy to /etc/export-worker/worker.env
EXPORT_DIR=/var/lib/export-worker
ENV
cat > /etc/export-worker/CHANGES <<'TXT'
export-worker 2.0
- the program moved from /usr/local/bin to /opt/export-worker/bin
- settings moved to an environment file: see worker.env.example
TXT
cat > /etc/systemd/system/export-worker.service <<'UNIT'
[Unit]
Description=Export worker (nightly CSV exports)
After=network.target

[Service]
User=exporter
EnvironmentFile=/etc/export-worker/worker.env
ExecStart=/usr/local/bin/export-worker --queue nightly
Restart=on-failure
RestartSec=300ms

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable export-worker >/dev/null 2>&1
systemctl start --no-block export-worker
# wait until systemd gives up, then do what the night shift did: start it again (-> start-limit-hit)
for _ in $(seq 60); do
  [ "$(systemctl show -P NRestarts export-worker)" -ge 5 ] && systemctl is-failed -q export-worker && break
  sleep 0.1
done
systemctl start export-worker >/dev/null 2>&1 || true
