#!/bin/bash
# Reference fix for room 10 (tests only).
set -euo pipefail
echo "ANSWER q1=$(awk '{print $1}' /var/log/nginx/admin-access.log | sort -u | head -1)"
# t1: trust the X-Forwarded-For header from the LB's real address only.
sed -i 's|^    set_real_ip_from 10.0.0.10;.*|    set_real_ip_from 127.0.0.1;          # lb-01 runs on this VM since 2026-10-19|' /etc/nginx/sites-available/admin
# t2: 10.20.0.0 - 10.20.3.255 is 4 x 256 addresses = 2^10 -> 32 - 10 = /22
python3 -c "import ipaddress as i; n=i.ip_network('10.20.0.0/22'); print('ANSWER q4=' + str(n.broadcast_address)); print('ANSWER q3=/' + str(n.prefixlen))"
sed -i 's|^    allow 10.20.0.0/24;|    allow 10.20.0.0/22;|' /etc/nginx/sites-available/admin
nginx -t
systemctl reload nginx
