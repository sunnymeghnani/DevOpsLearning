#!/bin/bash
# t1: for both locations the app logs the real client (127.0.0.77 here) and an X-Forwarded-For chain ending in it;
# a client-supplied X-Real-IP is overwritten by the proxy, not trusted.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
systemctl is-active -q upload-app || fail "upload-app is not running"
LOG=/var/log/upload-app/access.log
for path in /orders /upload; do
  rid="chk-$RANDOM$RANDOM"
  if [ $path = /upload ]; then data=(--data-binary 'x=1'); else data=(); fi
  code=$(curl -q -s -o /dev/null -w '%{http_code}' --max-time 5 --interface 127.0.0.77 \
         -H "X-Request-Id: $rid" -H 'X-Real-IP: 198.51.100.66' "${data[@]}" "http://uploads.example.com$path")
  [ "$code" = 200 ] || fail "$path answers $code through the proxy"
  line=$(grep -m1 "rid=$rid " "$LOG")
  [ -n "$line" ] || fail "the app logged nothing for a request to $path"
  client=$(sed -nE 's/.* client=([^ ]+) .*/\1/p' <<< "$line")
  [ "$client" != 198.51.100.66 ] || fail "on $path the app believed a client-supplied X-Real-IP (198.51.100.66): the proxy must overwrite it"
  [ "$client" = 127.0.0.77 ] || fail "on $path the app logs client=$client for a client at 127.0.0.77"
  xff=$(sed -nE 's/.* xff="([^"]*)" .*/\1/p' <<< "$line")
  [[ "$xff" =~ (^|,\ ?)127\.0\.0\.77$ ]] || fail "on $path X-Forwarded-For is '$xff': it should end with the client address"
done
echo "for / and /upload the app logs client=127.0.0.77 with X-Forwarded-For ending in it"
