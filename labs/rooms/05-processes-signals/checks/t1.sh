#!/bin/bash
# t1: no zombies left, and the report worker is still running (restarted, not just killed or disabled).
fail() { echo "$1"; exit 1; }
systemctl is-active -q report-worker.service || fail "report-worker.service is not running: reports must keep flowing"
systemctl is-enabled -q report-worker.service || fail "report-worker.service is not enabled at boot"
for _ in 1 2 3 4 5; do                       # ignore a zombie that exists only for a moment
  z=$(ps -eo stat= | grep -c '^Z' || true)
  [ "$z" -eq 0 ] && break
  sleep 0.4
done
[ "$z" -eq 0 ] || fail "$z zombie (Z/<defunct>) processes are still in the process table"
echo "no zombies; report-worker is running (PID $(systemctl show -p MainPID --value report-worker))"
