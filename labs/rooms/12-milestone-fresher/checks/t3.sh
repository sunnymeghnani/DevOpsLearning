#!/bin/bash
# t3: the health probe runs from cron's environment and records 200; cron runs and starts at boot.
fail() { echo "$1"; exit 1; }
S=/usr/local/bin/shop-health
[ -x "$S" ] || fail "$S is missing or not executable"
grep -q $'\r' "$S" && fail "$S still has Windows (CRLF) line endings"
systemctl is-active -q cron || fail "cron is not running"
systemctl is-enabled -q cron || fail "cron does not start at boot"
grep -qE '^[^#]*[[:space:]]root[[:space:]]+/usr/local/bin/shop-health' /etc/cron.d/shop-health 2>/dev/null \
  || fail "/etc/cron.d/shop-health no longer runs the probe as root"
rm -f /var/lib/shop/health.txt
out=$(env -i HOME=/root LOGNAME=root SHELL=/bin/sh PATH=/usr/bin:/bin /bin/sh -c "$S" </dev/null 2>&1); rc=$?
[ "$rc" -eq 0 ] || fail "in cron's environment the probe exits $rc: $(tail -n1 <<< "$out")"
grep -q ' 200$' /var/lib/shop/health.txt 2>/dev/null || fail "/var/lib/shop/health.txt does not record 200"
echo "the probe runs from cron and records: $(cat /var/lib/shop/health.txt)"
