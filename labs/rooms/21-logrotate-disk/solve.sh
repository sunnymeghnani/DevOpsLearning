#!/bin/bash
# Reference fix for room 21 (tests only).
set -euo pipefail
# t1: logrotate -d names the line: "bad size '20 '" -> the size must not contain a space.
out=$(logrotate -d /etc/logrotate.d/orders-api 2>&1 || true); grep -q "bad size" <<< "$out"
sed -i -E 's/^([[:space:]]*maxsize[[:space:]]+)20 M$/\120M/' /etc/logrotate.d/orders-api
! logrotate -d /etc/logrotate.conf 2>&1 | grep '^error:'
# t2: force one rotation of this config, then let the timer do it daily and prove the scheduled job works.
logrotate -f /etc/logrotate.d/orders-api
ls -l /var/log/orders-api/
systemctl enable --now logrotate.timer
systemctl list-timers logrotate.timer --no-pager | grep -q logrotate.timer
systemctl start logrotate.service
# t3: a later drop-in wins; restart journald so it uses the new cap.
printf '%s\n' '# cap the persistent journal (OPS-1187 follow-up)' '[Journal]' 'SystemMaxUse=200M' 'SystemKeepFree=1G' \
  > /etc/systemd/journald.conf.d/60-limits.conf
systemctl restart systemd-journald
journalctl --disk-usage
