#!/bin/bash
# Reference fix for room 18 (tests only).
set -euo pipefail
cd /etc/nginx/ssl
served=$(echo | openssl s_client -connect 127.0.0.1:443 -servername shop.example.com 2>/dev/null | openssl x509 -noout -enddate)
echo "ANSWER q1=$(date -u -d "${served#notAfter=}" +%F)"
openssl x509 -in shop.example.com.crt -noout -dates -ext subjectAltName
# t1: a new self-signed certificate with both names in the SAN (the old one-liner had none).
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 90 \
  -subj "/O=Example Shop/CN=shop.example.com" \
  -addext "subjectAltName=DNS:shop.example.com,DNS:www.shop.example.com" \
  -keyout shop.example.com.key -out shop.example.com.crt 2>/dev/null
chmod 600 shop.example.com.key
openssl x509 -in shop.example.com.crt -noout -checkend 2592000
# t2: nginx reads certificates at start and reload only.
nginx -t
systemctl reload nginx
sleep 0.5
curl -sS --cacert shop.example.com.crt https://www.shop.example.com/ -o /dev/null -w '%{http_code}\n'
