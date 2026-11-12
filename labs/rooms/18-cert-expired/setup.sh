#!/bin/bash
# Room 18 (tls-certs): nginx serves an expired self-signed certificate on 443.
# Broken state:
#  - /etc/nginx/ssl/shop.example.com.crt: notBefore 2026-08-11, notAfter 2026-11-09 00:00:00 UTC (expired);
#  - RENEW.txt holds last time's one-liner, which has no subjectAltName (a trap: clients need the SAN, and www is missing).
# Internal clients trust exactly this self-signed certificate file (it is copied to them), so the fix is a new
# self-signed certificate with the right names, then nginx -t and a reload.
set -euo pipefail

# names -> this box (/etc/hosts is a bind mount here: rewrite in place)
grep -v 'shop\.example\.com' /etc/hosts > /tmp/.hosts.$$ || true
echo '127.0.0.1 shop.example.com www.shop.example.com' >> /tmp/.hosts.$$
cat /tmp/.hosts.$$ > /etc/hosts && rm -f /tmp/.hosts.$$

install -d -m 0755 /etc/nginx/ssl /var/www/shop-tls
echo '<!doctype html><title>Shop</title><h1>Shop (TLS)</h1>' > /var/www/shop-tls/index.html

# --- the expired certificate: openssl 3.0 sets past dates only through "openssl ca" ---
w=$(mktemp -d)
install -d "$w/new"; : > "$w/index.txt"; echo 1000 > "$w/serial"
cat > "$w/ca.cnf" <<CNF
[ca]
default_ca = lab
[lab]
database = $w/index.txt
new_certs_dir = $w/new
serial = $w/serial
default_md = sha256
policy = any
copy_extensions = copy
unique_subject = no
[any]
commonName = supplied
CNF
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -subj "/O=Example Shop/CN=shop.example.com" \
  -addext "subjectAltName=DNS:shop.example.com,DNS:www.shop.example.com" \
  -keyout /etc/nginx/ssl/shop.example.com.key -out "$w/req.csr" 2>/dev/null
openssl ca -batch -notext -config "$w/ca.cnf" -selfsign -keyfile /etc/nginx/ssl/shop.example.com.key -in "$w/req.csr" \
  -startdate 20260811000000Z -enddate 20261109000000Z -out /etc/nginx/ssl/shop.example.com.crt >/dev/null 2>&1
rm -rf "$w"
chmod 0644 /etc/nginx/ssl/shop.example.com.crt
chmod 0600 /etc/nginx/ssl/shop.example.com.key
cat > /etc/nginx/ssl/RENEW.txt <<'TXT'
Renewing the shop certificate (self-signed; the app servers trust this exact .crt file)
Last done 2026-08-11 by the previous admin:

  cd /etc/nginx/ssl
  openssl req -x509 -newkey rsa:2048 -nodes -days 90 -subj "/CN=shop.example.com" \
    -keyout shop.example.com.key -out shop.example.com.crt

Then copy shop.example.com.crt to the app servers (ansible role "shop-trust").
TXT

cat > /etc/nginx/sites-available/shop-tls <<'CONF'
# shop.example.com over HTTPS
server {
    listen 80;
    server_name shop.example.com www.shop.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name shop.example.com www.shop.example.com;
    ssl_certificate     /etc/nginx/ssl/shop.example.com.crt;
    ssl_certificate_key /etc/nginx/ssl/shop.example.com.key;

    root /var/www/shop-tls;
    index index.html;
}
CONF
ln -sfn /etc/nginx/sites-available/shop-tls /etc/nginx/sites-enabled/shop-tls
[ -e /etc/nginx/sites-enabled/default ] || ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
