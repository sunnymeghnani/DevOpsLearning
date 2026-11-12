#!/bin/bash
# Reference fix for room 15 (tests only).
set -euo pipefail
U=export-worker.service
grep -q 'Start request repeated too quickly' <<< "$(journalctl -u $U -o cat --no-pager)"
grep -q 'Failed to load environment files' <<< "$(journalctl -u $U -o cat --no-pager)"
echo "ANSWER q2=$(systemctl show -P StartLimitBurst $U)"
grep -q 'is not executable' <<< "$(systemd-analyze verify /etc/systemd/system/$U 2>&1)"
# t1: the environment file from the example, and the 2.0 program path.
cp /etc/export-worker/worker.env.example /etc/export-worker/worker.env
sed -i 's|^ExecStart=/usr/local/bin/export-worker|ExecStart=/opt/export-worker/bin/export-worker|' /etc/systemd/system/$U
systemd-analyze verify /etc/systemd/system/$U
systemctl daemon-reload
# t2: clear the start limit, start, keep it enabled.
systemctl reset-failed $U
systemctl start $U
systemctl enable $U
sleep 1
systemctl is-active $U
