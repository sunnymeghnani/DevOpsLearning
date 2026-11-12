#!/bin/bash
# t1: nginx reaches shop-api again: / answers 200 with the API's JSON; both services run and start at boot.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
for u in nginx shop-api; do
  systemctl is-active -q $u || fail "$u is not running"
  systemctl is-enabled -q $u || fail "$u does not start at boot"
done
[ "$(ps -o user= -p "$(systemctl show -P MainPID shop-api)" | tr -d ' ')" = shopapi ] || fail "shop-api must keep running as shopapi"
out=$(curl -s --max-time 5 -o /tmp/.b.$$ -w '%{http_code}' -H 'Host: api.shop.example.com' http://127.0.0.1/)
body=$(cat /tmp/.b.$$ 2>/dev/null); rm -f /tmp/.b.$$
[ "$out" = 200 ] || fail "http://api.shop.example.com/ answers $out (expected 200)"
grep -q '"service": "shop-api"' <<< "$body" || fail "the 200 does not come from shop-api"
echo "nginx reaches shop-api: / answers 200"
