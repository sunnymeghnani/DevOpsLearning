#!/bin/bash
# t2: the logrotate config is valid, and after a forced rotation the agent writes to the live agent.log
# (copytruncate, or a postrotate that makes it reopen), with no deleted file left open.
fail() { echo "$1"; exit 1; }
V=/var/log/metrics
C=/etc/logrotate.d/metrics-agent
[ -f $C ] || fail "$C is missing"
out=$(logrotate -d $C 2>&1) || fail "logrotate -d $C fails: $(grep -m1 -i error <<< "$out")"
grep -qi '^error' <<< "$out" && fail "logrotate -d: $(grep -m1 -i '^error' <<< "$out")"
grep -q "^$V/agent.log" $C || fail "$C no longer rotates $V/agent.log"
systemctl is-active -q metrics-agent || fail "metrics-agent is not running"
for _ in $(seq 30); do [ -s $V/agent.log ] && break; sleep 0.1; done
[ -s $V/agent.log ] || fail "$V/agent.log stays empty: the agent is not writing to it (restart it once)"
st=$(mktemp)
logrotate -f -s "$st" $C >/dev/null 2>&1; rc=$?
rm -f "$st"
[ "$rc" -eq 0 ] || fail "a forced rotation (logrotate -f) fails"
sleep 2
systemctl is-active -q metrics-agent || fail "metrics-agent stopped during rotation"
pid=$(systemctl show -P MainPID metrics-agent)
t=$(readlink /proc/"$pid"/fd/1 2>/dev/null)
[ "$t" = "$V/agent.log" ] || fail "after a forced rotation the agent writes to '${t:-?}', not $V/agent.log"
for fd in /proc/[0-9]*/fd/*; do
  case $(readlink "$fd" 2>/dev/null) in "$V"/*" (deleted)") fail "after a forced rotation a deleted file is still open: $fd" ;; esac
done
s1=$(stat -c %s $V/agent.log); sleep 1.5; s2=$(stat -c %s $V/agent.log)
[ "$s2" -gt "$s1" ] || fail "$V/agent.log does not grow after rotation"
echo "after a forced rotation the agent keeps writing to $V/agent.log, and no deleted file stays open"
