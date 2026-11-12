#!/bin/bash
# Room 13 (port-ownership): Apache and nginx both want port 80. Apache won the boot race, nginx failed.
# Broken state:
#  - apache2 (legacy admin vhost) listens on *:80 and is running;
#  - nginx (the shop front, which should own :80 and proxy /legacy/ to Apache on 8080) failed:
#    "bind() to 0.0.0.0:80 failed (98: Address already in use)".
set -euo pipefail

systemctl stop nginx apache2 >/dev/null 2>&1 || true
systemctl reset-failed nginx apache2 >/dev/null 2>&1 || true

# --- content ---
install -d /var/www/shop /var/www/legacy
echo '<!doctype html><title>Shop</title><h1>Shop front (nginx)</h1>' > /var/www/shop/index.html
echo '<!doctype html><title>Legacy admin</title><h1>Legacy admin (Apache)</h1>' > /var/www/legacy/index.html

# --- Apache: stock ports.conf (Listen 80) and the legacy vhost on *:80 ---
cat > /etc/apache2/ports.conf <<'CONF'
# If you just change the port or add more ports here, you will likely also
# have to change the VirtualHost statement in
# /etc/apache2/sites-enabled/000-default.conf

Listen 80

<IfModule ssl_module>
	Listen 443
</IfModule>

<IfModule mod_gnutls.c>
	Listen 443
</IfModule>
CONF
cat > /etc/apache2/sites-available/legacy.conf <<'CONF'
# legacy.example.com: the old admin app (PHP was removed; static export only)
<VirtualHost *:80>
    ServerName legacy.example.com
    DocumentRoot /var/www/legacy
    ErrorLog ${APACHE_LOG_DIR}/legacy-error.log
    CustomLog ${APACHE_LOG_DIR}/legacy-access.log combined
</VirtualHost>
CONF
a2dissite -q 000-default >/dev/null 2>&1 || true
a2ensite -q legacy >/dev/null

# --- nginx: the shop owns :80 and sends /legacy/ to Apache on 8080 ---
cat > /etc/nginx/sites-available/shop <<'CONF'
# shop.example.com: public front. Plan (OPS-112): nginx owns :80, Apache moves behind it on 127.0.0.1:8080.
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name shop.example.com;
    root /var/www/shop;
    index index.html;

    location /legacy/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host legacy.example.com;
    }
}
CONF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/shop

# --- the boot race: both enabled, Apache started first ---
systemctl enable apache2 nginx >/dev/null 2>&1
systemctl start apache2
systemctl start nginx >/dev/null 2>&1 || true
