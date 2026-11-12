#!/bin/bash
# t2: the worker runs and stays up (same PID, no restarts), starts at boot, and writes its heartbeat as exporter.
fail() { echo "$1"; exit 1; }
U=export-worker.service
systemctl is-enabled -q $U || fail "export-worker does not start at boot"
[ "$(systemctl show -P SubState $U)" = running ] || fail "export-worker is $(systemctl show -P ActiveState $U) ($(systemctl show -P Result $U))"
pid=$(systemctl show -P MainPID $U)
[ "$pid" != 0 ] || fail "export-worker has no main process"
[ "$(ps -o user= -p "$pid" | tr -d ' ')" = exporter ] || fail "the worker must run as exporter"
sleep 2
[ "$(systemctl show -P MainPID $U)" = "$pid" ] && [ "$(systemctl show -P SubState $U)" = running ] \
  || fail "export-worker restarted or stopped within 2 seconds: it is still looping"
hb=/var/lib/export-worker/heartbeat
[ -f "$hb" ] || fail "no heartbeat in $hb yet"
age=$(( $(date +%s) - $(stat -c %Y "$hb") ))
[ "$age" -le 15 ] || fail "the heartbeat is ${age}s old"
echo "export-worker runs as exporter (PID $pid), stays up and starts at boot"
