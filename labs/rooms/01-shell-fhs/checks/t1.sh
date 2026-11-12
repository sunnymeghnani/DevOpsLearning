#!/bin/bash
# t1: nginx loads the edited file from sites-available through a symlink, and serves the new config.
fail() { echo "$1"; exit 1; }
f=/etc/nginx/sites-enabled/shop
[ -L "$f" ] || fail "$f is not a symlink: nginx still reads a separate copy"
[ "$(readlink -f "$f")" = /etc/nginx/sites-available/shop ] || fail "$f does not point to /etc/nginx/sites-available/shop"
n=$(grep -l 'server_name shop.example.com' /etc/nginx/sites-enabled/* 2>/dev/null | wc -l)
[ "$n" -eq 1 ] || fail "shop.example.com is defined $n times in sites-enabled (expected 1)"
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
for _ in 1 2 3 4 5 6; do   # a reload finishes asynchronously
  curl -s --max-time 5 http://127.0.0.1/ | grep -q MAINTENANCE && break; sleep 0.5
done
curl -s --max-time 5 http://127.0.0.1/ | grep -q MAINTENANCE || fail "http://127.0.0.1/ does not show the maintenance banner yet (reloaded?)"
[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1/healthz)" = 200 ] || fail "/healthz does not answer 200"
echo "nginx serves sites-available/shop through the symlink: banner and /healthz are live"
