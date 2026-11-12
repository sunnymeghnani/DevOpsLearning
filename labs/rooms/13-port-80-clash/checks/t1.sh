#!/bin/bash
# t1: Apache moved off port 80 to 8080 (Listen and vhost), config valid, running and enabled.
fail() { echo "$1"; exit 1; }
out=$(apachectl configtest 2>&1) || fail "apachectl configtest fails: $(grep -v AH00558 <<< "$out" | head -1)"
systemctl is-active -q apache2 || fail "apache2 is not running"
systemctl is-enabled -q apache2 || fail "apache2 does not start at boot"
socks=$(ss -Htlnp 2>/dev/null)
grep -E '[:.]80[[:space:]]' <<< "$socks" | grep -q '"apache2"' && fail "Apache still listens on port 80"
grep -E '[:.]8080[[:space:]]' <<< "$socks" | grep -q '"apache2"' || fail "Apache does not listen on port 8080"
body=$(curl -s --max-time 5 -H 'Host: legacy.example.com' http://127.0.0.1:8080/)
grep -q 'Legacy admin' <<< "$body" || fail "port 8080 answers, but not with the legacy vhost: does its <VirtualHost> still say *:80?"
echo "Apache runs on 8080 only and serves the legacy vhost"
