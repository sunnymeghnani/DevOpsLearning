#!/bin/bash
# t2: /reports/monthly (5 s) answers 200, while the 3 s fail-fast limit still holds for the rest of the API
# (/api/stall, 15 s, must still get 504), and no proxy_read_timeout is absurd.
fail() { echo "$1"; exit 1; }
H='Host: api.shop.example.com'
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
c=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' -H "$H" http://127.0.0.1/)
[ "$c" = 200 ] || fail "/ answers $c: fix the 502 first (task 1)"
while read -r v; do
  case $v in
    *ms) n=0 ;;
    *s) n=${v%s} ;;
    *m) n=$(( ${v%m} * 60 )) ;;
    *[0-9]) n=$v ;;
    *) n=99999 ;;
  esac
  [ "$n" -le 300 ] 2>/dev/null || fail "proxy_read_timeout $v is far too long: pick a limit that fits the report (seconds, not hours)"
done < <(nginx -T 2>/dev/null | sed -n 's/^[[:space:]]*proxy_read_timeout[[:space:]]\{1,\}\([^;[:space:]]*\);.*/\1/p')
out=$(curl -s --max-time 20 -o /tmp/.b.$$ -w '%{http_code}' -H "$H" http://127.0.0.1/reports/monthly)
body=$(cat /tmp/.b.$$ 2>/dev/null); rm -f /tmp/.b.$$
[ "$out" = 200 ] || fail "/reports/monthly answers $out (expected 200)"
grep -q '"status": "ready"' <<< "$body" || fail "/reports/monthly does not return the report"
c=$(curl -s --max-time 9 -o /dev/null -w '%{http_code}' -H "$H" http://127.0.0.1/api/stall)
[ "$c" = 504 ] || fail "/api/stall answers ${c/000/no response within 9 s} instead of a fast 504: the 3 s limit must stay for the rest of the API"
echo "/reports/monthly answers 200; the rest of the API still fails fast with 504"
