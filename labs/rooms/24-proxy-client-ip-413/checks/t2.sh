#!/bin/bash
# t2: a 2 MB upload to /upload passes (the app stores all bytes); the limit is raised for /upload only,
# so a 2 MB body to another path still gets nginx's 413.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
F=$(mktemp); trap 'rm -f "$F"' EXIT
head -c 2097152 /dev/zero > "$F"
out=$(curl -q -s --max-time 20 --interface 127.0.0.66 -w '\n%{http_code}' --data-binary @"$F" http://uploads.example.com/upload)
code=${out##*$'\n'}
[ "$code" = 200 ] || fail "a 2 MB upload to /upload answers $code"
grep -q 'stored 2097152 bytes' <<< "$out" || fail "the app did not receive all 2 MB: ${out%%$'\n'*}"
code=$(curl -q -s -o /dev/null --max-time 20 -w '%{http_code}' --data-binary @"$F" http://uploads.example.com/orders)
[ "$code" = 413 ] || fail "a 2 MB POST to /orders answers $code: raise the limit only for location /upload, not the whole server"
nginx -T 2>/dev/null | grep -qE '^[[:space:]]*client_max_body_size[[:space:]]+0[[:space:]]*;' && fail "client_max_body_size 0 turns the limit off: give /upload a real ceiling"
echo "2 MB uploads pass on /upload; other paths keep the 1 MB default"
