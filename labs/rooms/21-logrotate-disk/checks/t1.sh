#!/bin/bash
# t1: logrotate parses its whole configuration without errors, and the orders-api config is loaded with a size cap.
fail() { echo "$1"; exit 1; }
F=/etc/logrotate.d/orders-api
[ -f "$F" ] || fail "$F is gone: the app's logs need a rotation config"
out=$(logrotate -d /etc/logrotate.conf 2>&1 </dev/null)
err=$(grep -m1 '^error:' <<< "$out")
[ -z "$err" ] || fail "logrotate -d: $err"
grep -q '^rotating pattern: /var/log/orders-api/' <<< "$out" || fail "logrotate does not load a config for /var/log/orders-api/ any more"
grep -qE '^[[:space:]]*(maxsize|size)[[:space:]]+[0-9]+[kKmMgG]?[[:space:]]*$' "$F" || fail "$F has no size or maxsize limit: a busy log can still fill the disk within a day"
grep -qE '^[[:space:]]*rotate[[:space:]]+[1-9][0-9]*[[:space:]]*$' "$F" || fail "$F must keep some old logs (rotate N, N >= 1)"
echo "logrotate -d reads every config without errors, orders-api included"
