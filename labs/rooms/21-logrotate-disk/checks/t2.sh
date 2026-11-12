#!/bin/bash
# t2: app.log has been rotated (old data in app.log.1[.gz]), the app writes on into a fresh app.log,
# the daily timer is enabled and waiting, and the scheduled job no longer fails.
fail() { echo "$1"; exit 1; }
L=/var/log/orders-api/app.log
old=""; for f in "$L".1 "$L".1.gz; do [ -f "$f" ] && old=$f; done
[ -n "$old" ] || fail "no $L.1 or $L.1.gz: force one rotation of the orders-api config"
size=$(stat -c %s "$L" 2>/dev/null || echo missing)
[ "$size" != missing ] || fail "$L is missing: the app has nowhere to write"
[ "$size" -lt 10485760 ] || fail "$L is still $((size / 1048576)) MB: it was not rotated"
systemctl is-active -q orders-api || fail "orders-api is not running"
s1=$size; sleep 1.2; s2=$(stat -c %s "$L")
[ "$s2" -gt "$s1" ] || fail "orders-api no longer writes to $L after the rotation"
grep -q '/var/log/orders-api/app.log' /var/lib/logrotate/status 2>/dev/null || fail "logrotate's state file has no entry for app.log"
systemctl is-enabled -q logrotate.timer || fail "logrotate.timer is not enabled: nothing rotates after a reboot"
systemctl is-active -q logrotate.timer || fail "logrotate.timer is not active: the next daily run never comes"
systemctl is-failed -q logrotate.service && fail "logrotate.service is still in the failed state: run the scheduled job once and see it succeed"
echo "app.log rotated (${old##*/}), the app writes on, logrotate.timer is enabled and the job succeeds"
