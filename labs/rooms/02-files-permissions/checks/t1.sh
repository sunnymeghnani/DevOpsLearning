#!/bin/bash
# t1: the docs page is served (200) by nginx running as www-data, without loosening write permissions.
fail() { echo "$1"; exit 1; }
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
users=$(ps -o user= --ppid "$(cat /run/nginx.pid 2>/dev/null || echo 1)" | sort -u | tr '\n' ' ')
[ "${users% }" = www-data ] || fail "nginx workers must keep running as www-data (now: ${users:-none})"
for p in /home/deploy /home/deploy/site /home/deploy/site/current/index.html; do
  m=$(stat -Lc %a "$p")
  (( 8#$m & 8#002 )) && fail "$p is world-writable ($m): never the fix"
done
(( 8#$(stat -c %a /home/deploy) & 8#020 )) && fail "/home/deploy is group-writable: not needed for reading"
code=$(curl -s -o /tmp/.t1body -w '%{http_code}' --max-time 5 http://127.0.0.1/)
[ "$code" = 200 ] || fail "http://127.0.0.1/ answers $code (expected 200)"
grep -q 'Docs portal' /tmp/.t1body || fail "the page is not the docs release"
rm -f /tmp/.t1body
echo "www-data can traverse /home/deploy: the docs page answers 200"
