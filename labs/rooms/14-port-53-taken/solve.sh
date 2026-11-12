#!/bin/bash
# Reference fix for room 14 (tests only).
set -euo pipefail
grep -q 'failed to create listening socket for port 53: Address already in use' <<< "$(journalctl -u dnsmasq -o cat --no-pager)"
echo "ANSWER q1=$(ss -Hlun 'sport = :53' | awk '{print $4}' | grep -m1 '^127\.0\.0\.53:53$')"
# t1: bind dnsmasq to 127.0.0.1 only, so it stops asking for the wildcard 0.0.0.0:53.
cat > /etc/dnsmasq.d/listen.conf <<'CONF'
listen-address=127.0.0.1
bind-interfaces
CONF
# t2: load the hosts file from the network team.
echo 'addn-hosts=/etc/dnsmasq.hosts' >> /etc/dnsmasq.d/internal.conf
dnsmasq --test
systemctl reset-failed dnsmasq || true
systemctl enable dnsmasq
systemctl restart dnsmasq
dig +short @127.0.0.1 cache.example.com
