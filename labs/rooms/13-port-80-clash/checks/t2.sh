#!/bin/bash
# t2: nginx owns port 80, is running and enabled, serves the shop and proxies /legacy/ to Apache.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx does not start at boot"
systemctl is-active -q apache2 || fail "apache2 is not running any more"
owner=$(ss -Htlnp 'sport = :80' 2>/dev/null | grep -o 'users:(("[^"]*"' | sort -u | cut -d'"' -f2 | tr '\n' ' ')
[ "${owner% }" = nginx ] || fail "port 80 must belong to nginx only (now: ${owner:-nobody})"
body=$(curl -s --max-time 5 -H 'Host: shop.example.com' http://127.0.0.1/)
grep -q 'Shop front' <<< "$body" || fail "http://127.0.0.1/ does not serve the shop front"
body=$(curl -s --max-time 5 -H 'Host: shop.example.com' http://127.0.0.1/legacy/)
grep -q 'Legacy admin' <<< "$body" || fail "/legacy/ through nginx does not reach the Apache vhost"
echo "nginx owns port 80, serves the shop and proxies /legacy/ to Apache on 8080"
