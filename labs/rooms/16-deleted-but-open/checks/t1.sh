#!/bin/bash
# t1: the space held by the deleted log is free again, the volume is still mounted, and the agent still runs.
fail() { echo "$1"; exit 1; }
V=/var/log/metrics
[ "$(findmnt -n -o SOURCE --target $V 2>/dev/null)" = metrics-vol ] || fail "$V is no longer the metrics volume: leave it mounted"
systemctl is-active -q metrics-agent || fail "metrics-agent is not running: free the space without stopping the agent for good"
held=$(for fd in /proc/[0-9]*/fd/*; do
  t=$(readlink "$fd" 2>/dev/null) || continue
  case $t in "$V"/*" (deleted)") stat -L -c '%d:%i %s' "$fd" 2>/dev/null ;; esac
done | sort -u | awk '{s += $2} END {print s + 0}')
[ "$held" -lt 1048576 ] || fail "open but deleted files under $V still hold $((held / 1048576)) MB"
use=$(df --output=pcent $V | tail -1 | tr -dc 0-9)
[ "$use" -lt 50 ] || fail "$V is still ${use}% full"
echo "$V is ${use}% full and the agent still runs"
