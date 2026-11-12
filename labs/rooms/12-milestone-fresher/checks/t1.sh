#!/bin/bash
# t1: nginx has a valid config with the shop site, runs, and starts at boot.
fail() { echo "$1"; exit 1; }
err=$(nginx -t 2>&1) || fail "nginx -t fails: $(grep -m1 emerg <<< "$err")"
nginx -T 2>/dev/null | grep -q 'server_name shop.example.com;' || fail "the shop site is no longer in the loaded configuration"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx does not start at boot"
c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H 'Host: shop.example.com' http://127.0.0.1/)
[ "$c" != 000 ] || fail "nothing answers on port 80"
echo "nginx runs with a valid config and starts at boot (shop answers $c)"
