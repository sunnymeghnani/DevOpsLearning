#!/bin/bash
# t1: nginx trusts X-Forwarded-For from the load balancer (127.0.0.1) and only from it.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 ${3:+--interface "$3"} -H "X-Forwarded-For: $1" "http://127.0.0.1/$2"; }
for _ in 1 2 3 4 5 6; do [ "$(code 10.20.0.25)" = 200 ] && break; sleep 0.5; done   # reloads are asynchronous
c=$(code 10.20.0.25)
[ "$c" = 200 ] || fail "an office client (10.20.0.25) through the LB still gets $c"
tag="probe$$$RANDOM"
code 10.20.0.77 "?$tag" >/dev/null
sleep 0.2
seen=$(grep -F "$tag" /var/log/nginx/admin-access.log | tail -1 | awk '{print $1}')
[ "$seen" = 10.20.0.77 ] || fail "nginx logs the client as '${seen:-nothing}', not 10.20.0.77"
c=$(code 10.20.0.25 "" 127.0.0.2)
[ "$c" = 403 ] || fail "a request from 127.0.0.2 (not the LB) with a forged X-Forwarded-For gets $c: trust only 127.0.0.1"
echo "nginx sees the real client behind the LB (127.0.0.1) and ignores forged headers from elsewhere"
