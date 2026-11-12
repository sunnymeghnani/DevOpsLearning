#!/bin/bash
# Reference fix for room 12 (tests only).
set -euo pipefail
# t1: read the error, fix the missing semicolon, start and enable.
nginx -t 2>&1 | grep -q 'invalid number of arguments in "root"' || true
sed -i 's|^    root /srv/shop/public$|    root /srv/shop/public;|' /etc/nginx/sites-available/shop
nginx -t
systemctl enable --now nginx
# t2: let www-data (others) traverse the directories and read the page.
echo "ANSWER q2=$(ps -o user= --ppid "$(cat /run/nginx.pid)" | sort -u | head -1)"
chmod 755 /srv/shop /srv/shop/public
chmod 644 /srv/shop/public/index.html
# t3: CRLF -> LF.
file /usr/local/bin/shop-health | grep -q 'CRLF'
echo "ANSWER q4=file"
sed -i 's/\r$//' /usr/local/bin/shop-health
/usr/local/bin/shop-health && cat /var/lib/shop/health.txt
