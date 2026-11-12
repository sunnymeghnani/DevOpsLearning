#!/bin/bash
# t2: the shop page answers 200, served by www-data workers, with nothing world-writable.
fail() { echo "$1"; exit 1; }
systemctl is-active -q nginx || fail "nginx is not running"
users=$(ps -o user= --ppid "$(cat /run/nginx.pid 2>/dev/null || echo 1)" | sort -u | tr '\n' ' ')
[ "${users% }" = www-data ] || fail "nginx workers must run as www-data (now: ${users:-none})"
bad=$(find /srv/shop -perm -o+w ! -type l | head -1)
[ -z "$bad" ] || fail "$bad is world-writable: never the fix"
body=$(curl -s --max-time 5 -w '\n%{http_code}' -H 'Host: shop.example.com' http://127.0.0.1/)
[ "${body##*$'\n'}" = 200 ] || fail "the shop answers ${body##*$'\n'} (expected 200)"
grep -q 'Shop is up' <<< "$body" || fail "the shop page is not the one from /srv/shop/public"
echo "the shop answers 200"
