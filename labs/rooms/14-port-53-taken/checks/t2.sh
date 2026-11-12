#!/bin/bash
# t2: dnsmasq serves the records from /etc/dnsmasq.hosts, its config is valid, and it starts at boot.
fail() { echo "$1"; exit 1; }
# the directory list Ubuntu's unit passes (CONFIG_DIR in /etc/default/dnsmasq): a bare --test skips /etc/dnsmasq.d
out=$(dnsmasq --test --conf-dir=/etc/dnsmasq.d,.dpkg-dist,.dpkg-old,.dpkg-new 2>&1) || fail "dnsmasq --test (with /etc/dnsmasq.d): $(tr '\n' ' ' <<< "$out")"
systemctl is-enabled -q dnsmasq || fail "dnsmasq does not start at boot"
systemctl is-enabled -q stub-resolver || fail "stub-resolver must still start at boot"
systemctl is-active -q dnsmasq || fail "dnsmasq is not running"
for pair in cache.example.com=192.0.2.11 queue.example.com=192.0.2.12 db.example.com=192.0.2.10; do
  n=${pair%=*}; want=${pair#*=}
  r=$(dig +short +time=2 +tries=1 @127.0.0.1 "$n" 2>/dev/null)
  [ "$r" = "$want" ] || fail "dig @127.0.0.1 $n answers '${r:-nothing}' (expected $want)"
done
r=$(dig +short +tcp +time=2 +tries=1 @127.0.0.1 cache.example.com 2>/dev/null)
[ "$r" = 192.0.2.11 ] || fail "dnsmasq does not answer over TCP"
echo "dnsmasq serves db, cache and queue.example.com and starts at boot"
