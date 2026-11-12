#!/bin/bash
# t2: the allowlist covers exactly the VPN pool 10.20.0.0-10.20.3.255.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H "X-Forwarded-For: $1" http://127.0.0.1/; }
for _ in 1 2 3 4 5 6; do [ "$(code 10.20.3.254)" = 200 ] && break; sleep 0.5; done
for ip in 10.20.0.5 10.20.1.200 10.20.2.15 10.20.3.254; do
  c=$(code "$ip"); [ "$c" = 200 ] || fail "VPN client $ip gets $c (expected 200)"
done
for ip in 10.20.4.9 10.20.255.1 10.21.0.5 10.0.0.10 203.0.113.50 192.0.2.44; do
  c=$(code "$ip"); [ "$c" = 403 ] || fail "$ip is outside the VPN pool but gets $c (expected 403)"
done
[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --interface 127.0.0.2 -H 'X-Forwarded-For: 10.20.2.15' http://127.0.0.1/)" = 403 ] \
  || fail "forged X-Forwarded-For from a host other than the LB is trusted again"
echo "10.20.0.0-10.20.3.255 is allowed, everything else is denied"
