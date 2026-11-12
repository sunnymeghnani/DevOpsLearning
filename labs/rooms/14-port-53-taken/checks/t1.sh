#!/bin/bash
# t1: dnsmasq runs on 127.0.0.1:53 only (no wildcard), next to the stub, which still answers on 127.0.0.53.
fail() { echo "$1"; exit 1; }
systemctl is-active -q stub-resolver || fail "the stub on 127.0.0.53 is not running: other software on this box uses it, keep it"
r=$(dig +short +time=2 +tries=1 @127.0.0.53 gw.example.com 2>/dev/null)
[ "$r" = 192.0.2.1 ] || fail "the stub on 127.0.0.53 no longer answers gw.example.com"
if ! systemctl is-active -q dnsmasq; then
  why=$(journalctl -u dnsmasq -t dnsmasq -o cat -n 30 --no-pager 2>/dev/null | grep -v 'FAILED to start up' | tail -1)
  fail "dnsmasq is not running${why:+: $why}"
fi
socks=$(ss -Hlun 'sport = :53'; ss -Hltn 'sport = :53')
grep -qE '(0\.0\.0\.0|\*|\[::\]):53[[:space:]]' <<< "$socks" && fail "something listens on the wildcard address for port 53"
[ "$(grep -c '127\.0\.0\.1:53[[:space:]]' <<< "$socks")" -ge 2 ] || fail "dnsmasq must listen on 127.0.0.1:53 (UDP and TCP)"
r=$(dig +short +time=2 +tries=1 @127.0.0.1 db.example.com 2>/dev/null)
[ "$r" = 192.0.2.10 ] || fail "dig @127.0.0.1 db.example.com answers '${r:-nothing}' (expected 192.0.2.10)"
echo "dnsmasq answers on 127.0.0.1:53 and the stub keeps 127.0.0.53:53"
