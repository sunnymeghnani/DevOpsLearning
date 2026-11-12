#!/bin/bash
# t1: no /etc/hosts pin for api.internal.example.com any more, so getaddrinfo follows DNS (127.0.10.20) like dig;
# the hosts file and NSS order are otherwise intact; the worker's own lookup and request succeed.
fail() { echo "$1"; exit 1; }
N=api.internal.example.com
pin=$(grep -nE "^[^#]*[[:space:]]$N([[:space:]]|$)" /etc/hosts | head -1)
[ -z "$pin" ] || fail "/etc/hosts still pins $N (line ${pin%%:*}): getaddrinfo reads it before DNS"
grep -qE '^127\.0\.0\.1[[:space:]]+localhost' /etc/hosts || fail "/etc/hosts lost its localhost line: delete only the stale pins"
grep -qE '^hosts:.*\bfiles\b.*\bdns\b' /etc/nsswitch.conf || fail "keep 'hosts: files dns' in /etc/nsswitch.conf: the fix is the stale entry, not the order"
systemctl is-active -q dnsmasq || fail "the DNS server (dnsmasq on 127.0.0.2) is not running"
[ "$(dig +short +time=2 @127.0.0.2 $N A)" = 127.0.10.20 ] || fail "DNS no longer answers $N with 127.0.10.20"
got=$(getent ahostsv4 $N | awk 'NR==1{print $1}')
[ "$got" = 127.0.10.20 ] || fail "getent ahosts $N gives ${got:-nothing}, DNS says 127.0.10.20"
body=$(runuser -u orders -- python3 -c "import urllib.request; print(urllib.request.urlopen('http://$N:8080/health', timeout=3).read().decode().strip())" 2>&1 </dev/null | tail -1)
[ "$body" = "ok api-v2" ] || fail "the app's request to $N:8080 fails: $body"
systemctl is-active -q orders-sync || fail "orders-sync is not running"
echo "getaddrinfo and dig agree: $N -> 127.0.10.20, and the worker's request succeeds"
