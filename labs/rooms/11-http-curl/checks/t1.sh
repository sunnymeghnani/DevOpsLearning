#!/bin/bash
# t1: no redirect loop on HTTPS; pages and 404s answer correctly; HTTP still redirects once to HTTPS.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx is not enabled at boot"
R=(--resolve shop.example.com:443:127.0.0.1 --resolve shop.example.com:80:127.0.0.1)
get() { curl -q -sk "${R[@]}" --max-time 5 -o /tmp/.body.$$ -w '%{http_code} %{redirect_url}' "$1"; }
for _ in 1 2 3 4 5 6; do [ "$(get https://shop.example.com/)" = "200 " ] && break; sleep 0.5; done
r=$(get https://shop.example.com/); [ "$r" = "200 " ] || fail "https://shop.example.com/ answers '$r' (expected 200, no redirect)"
grep -q 'Autumn sale' /tmp/.body.$$ || fail "https://shop.example.com/ does not serve the shop page"
r=$(get https://shop.example.com/docs/); [ "$r" = "200 " ] || fail "https://shop.example.com/docs/ answers '$r' (expected 200)"
r=$(get https://shop.example.com/no-such-page); [ "${r%% *}" = 404 ] || fail "a missing page answers '$r' (expected 404)"
r=$(get 'http://shop.example.com/docs/?a=1')
[ "$r" = "301 https://shop.example.com/docs/?a=1" ] || fail "http:// must still redirect once to the same https:// URL, got '$r'"
rm -f /tmp/.body.$$
echo "https serves pages (200/404) without redirects; http redirects once to https"
