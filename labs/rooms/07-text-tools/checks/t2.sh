#!/bin/bash
# t2: nginx refuses the crawler by user agent (any version), while browsers and curl still get the docs.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 5 -A "$1" http://127.0.0.1/; }
for _ in 1 2 3 4 5 6; do   # a reload finishes asynchronously
  c=$(code 'Mozilla/5.0 (compatible; DocHarvester/1.7; +https://crawler.example.net/bot)')
  case "$c" in 403|429|444|000) break ;; esac; sleep 0.5
done
botcode=$c
for ua in 'Mozilla/5.0 (compatible; DocHarvester/1.7; +https://crawler.example.net/bot)' 'DocHarvester/1.8'; do
  c=$(code "$ua")
  case "$c" in 403|429|444|000) ;; *) fail "user agent '$ua' still gets HTTP $c" ;; esac
done
for ua in 'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0' 'curl/8.5.0'; do
  c=$(code "$ua")
  [ "$c" = 200 ] || fail "a normal client ('$ua') gets HTTP $c: block only the crawler"
done
echo "DocHarvester is refused (HTTP $botcode), browsers and curl still get 200"
