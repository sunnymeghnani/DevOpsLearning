#!/bin/bash
# Reference fix for room 11 (tests only).
set -euo pipefail
curl -s http://127.0.0.1/ | grep -q 'Welcome to nginx'                 # no Host header -> default server
echo "ANSWER q2=$(curl -sk -o /dev/null -w '%{http_code}' https://shop.example.com/docs/)"
curl -skIL --max-redirs 3 https://shop.example.com/ >/dev/null 2>&1 || true   # Maximum (3) redirects followed
# t1: the 443 block must serve files, not redirect: try_files needs $uri.
sed -i 's|try_files / =404;|try_files $uri $uri/ =404;|' /etc/nginx/sites-available/shop
nginx -t
systemctl reload nginx
# t2: trust the internal CA system-wide.
curl -sS https://shop.example.com/health >/dev/null 2>&1 || true          # (60) unable to get local issuer certificate
cp /etc/ssl/example-ca/ca.crt /usr/local/share/ca-certificates/example-internal-ca.crt
update-ca-certificates >/dev/null
curl -sS https://shop.example.com/health
