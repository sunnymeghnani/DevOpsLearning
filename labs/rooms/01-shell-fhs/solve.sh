#!/bin/bash
# Reference fix for room 01 (tests only).
set -euo pipefail
# t1: see what nginx really loads, replace the stale copy with a link, test, reload.
nginx -T 2>/dev/null | grep '^# configuration file' >/dev/null
echo "ANSWER q1=$(stat -c %F /etc/nginx/sites-enabled/shop)"
rm /etc/nginx/sites-enabled/shop
ln -s /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/shop
nginx -t
systemctl reload nginx
# t2: find every shopctl on PATH, drop the stale copy, link the vendor binary into /usr/local/bin.
echo "ANSWER q4=$(dirname "$(bash -c 'type -P shopctl')")"
rm /usr/local/sbin/shopctl
ln -s /opt/shop/bin/shopctl /usr/local/bin/shopctl
hash -r
shopctl version
