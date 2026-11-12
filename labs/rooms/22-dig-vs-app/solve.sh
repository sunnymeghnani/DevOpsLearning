#!/bin/bash
# Reference fix for room 22 (tests only).
set -euo pipefail
N=api.internal.example.com
# t1: two resolution paths. dig asks DNS; getaddrinfo follows nsswitch.conf (files first).
dig +short $N
echo "ANSWER q1=$(getent ahostsv4 $N | awk 'NR==1{print $1}')"
grep '^hosts:' /etc/nsswitch.conf
# /etc/hosts is a bind mount: rewrite it in place (sed -i would fail with "Device or resource busy")
grep -vE "[[:space:]]$N([[:space:]]|$)" /etc/hosts > /tmp/.h || true
cat /tmp/.h > /etc/hosts; rm -f /tmp/.h
getent ahostsv4 $N | head -1
# t2: the short name went through the search list to another host.
echo "ANSWER q3=$(getent ahostsv4 api | awk 'NR==1{print $3}')"
sed -i 's|^API_URL=.*|API_URL=http://api.internal.example.com.:8080/health|' /etc/report-export.conf
systemctl start report-export.service
