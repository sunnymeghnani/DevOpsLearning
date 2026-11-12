#!/bin/bash
# Reference fix for room 16 (tests only).
set -euo pipefail
V=/var/log/metrics
df -h $V; du -sh $V
grep -q '(deleted)' <<< "$(lsof +L1 2>/dev/null)"
pid=$(systemctl show -P MainPID metrics-agent)
echo "ANSWER q2=$(ps -o unit= -p "$pid" | tr -d ' ')"
# t1: free the space. The agent reopens its log on SIGHUP (ExecReload); a restart works too.
systemctl reload metrics-agent
sleep 2
df -h $V
# t2: tell the agent after each rotation (and compress one day later, so gzip never races a writer).
cat > /etc/logrotate.d/metrics-agent <<'CONF'
/var/log/metrics/agent.log {
    daily
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    postrotate
        systemctl reload metrics-agent >/dev/null 2>&1 || true
    endscript
}
CONF
logrotate -d /etc/logrotate.d/metrics-agent >/dev/null 2>&1
