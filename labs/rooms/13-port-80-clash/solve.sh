#!/bin/bash
# Reference fix for room 13 (tests only).
set -euo pipefail
echo "ANSWER q1=$(ss -Htlnp 'sport = :80' | grep -o 'users:(("[^"]*"' | head -1 | cut -d'"' -f2)"
grep -q 'Address already in use' <<< "$(journalctl -u nginx --no-pager)"
echo "ANSWER q3=$(journalctl -u nginx --no-pager | grep -o 'failed ([0-9]*: Address already in use)' | head -1 | grep -o '[0-9]\+')"
# t1: Apache to 8080, both the Listen line and the vhost.
sed -i 's/^Listen 80$/Listen 8080/' /etc/apache2/ports.conf
sed -i 's/<VirtualHost \*:80>/<VirtualHost *:8080>/' /etc/apache2/sites-available/legacy.conf
apachectl configtest
systemctl restart apache2
systemctl enable apache2
# t2: port 80 is free now.
nginx -t
systemctl enable --now nginx
curl -s -H 'Host: shop.example.com' http://127.0.0.1/legacy/
