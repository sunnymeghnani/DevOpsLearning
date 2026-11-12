#!/bin/bash
# Reference fix for room 05 (tests only).
set -euo pipefail
# t1: zombies are already dead; only their parent can reap them. Find the parent, restart it.
ppid=$(ps -eo stat=,ppid= | awk '$1 ~ /^Z/ {print $2; exit}')
echo "ANSWER q1=$(ps -eo stat= | grep -m1 '^Z' | cut -c1)"
echo "ANSWER q2=$(ps -o comm= -p "$ppid")"
systemctl restart report-worker.service
# t2: TERM is trapped, so escalate to KILL (signal 9 cannot be caught).
pid=$(pgrep -x backup-sync)
kill "$pid"; sleep 1
kill -0 "$pid" 2>/dev/null && kill -KILL "$pid"
sleep 0.3
