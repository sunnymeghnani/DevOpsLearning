#!/bin/bash
# t1: cron runs, and the job from /etc/cron.d/shop-backup, executed in cron's own environment, makes a real dump.
fail() { echo "$1"; exit 1; }
systemctl is-active -q cron || fail "the cron daemon is not running"
systemctl is-enabled -q cron || fail "cron is not enabled at boot"
CF=/etc/cron.d/shop-backup
[ -f "$CF" ] || fail "$CF is missing (keep the job there)"
[ "$(stat -c %U "$CF")" = root ] || fail "$CF must be owned by root, or cron ignores it"
(( 8#$(stat -c %a "$CF") & 8#022 )) && fail "$CF is group/world-writable, so cron ignores it"
# cron's environment: a minimal one plus VAR=value lines from the file
envs=(HOME=/root LOGNAME=root SHELL=/bin/sh PATH=/usr/bin:/bin)
job=""
while IFS= read -r line; do
  [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
  if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
    v=${BASH_REMATCH[2]}; v=${v%\"}; v=${v#\"}; v=${v%\'}; v=${v#\'}
    envs+=("${BASH_REMATCH[1]}=$v"); continue
  fi
  job=$line; break
done < "$CF"
[ -n "$job" ] || fail "no job line in $CF"
read -r m h dom mon dow user cmd <<< "$job"
[ "$user" = root ] || fail "the job in $CF must run as root (6th field), found '$user'"
[[ "$cmd" == *shop-backup* ]] || fail "the job in $CF no longer runs shop-backup"
today=$(date +%F)
rm -f "/var/backups/shop/db-$today.sql.gz" "/var/backups/shop/www-$today.tar.gz"
out=$(env -i "${envs[@]}" /bin/sh -c "$cmd" </dev/null 2>&1); rc=$?
[ "$rc" -eq 0 ] || fail "in cron's environment the job exits $rc: $(tail -n1 <<< "$out")"
db=/var/backups/shop/db-$today.sql.gz
[ -f "$db" ] || fail "in cron's environment no $db is created"
zcat "$db" 2>/dev/null | grep -q 'CREATE TABLE' || fail "in cron's environment $db is empty ($(stat -c %s "$db") bytes): shop-snapshot did not run"
[ -s "/var/backups/shop/www-$today.tar.gz" ] || fail "in cron's environment the web root archive is missing"
echo "cron is running; in cron's environment the job writes a real dump ($(stat -c %s "$db") bytes)"
