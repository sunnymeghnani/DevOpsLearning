#!/bin/bash
# Room 10 (net-basics): an IP allowlist behind a load balancer: wrong trusted proxy address and wrong prefix length.
# Broken state (nginx site "admin"):
#  - set_real_ip_from still names the old LB 10.0.0.10, but the LB now connects from 127.0.0.1
#    -> nginx sees every client as 127.0.0.1 and denies everyone;
#  - allow 10.20.0.0/24, but the VPN pool was enlarged to 10.20.0.0-10.20.3.255.
set -euo pipefail

install -d /var/www/admin
echo '<!doctype html><title>Admin</title><h1>Shop admin</h1>' > /var/www/admin/index.html
cat > /etc/nginx/sites-available/admin <<'EOF'
# admin.example.com - internal admin panel, reachable only through the load balancer
server {
    listen 80 default_server;
    server_name admin.example.com;
    root /var/www/admin;
    index index.html;
    access_log /var/log/nginx/admin-access.log;

    # the load balancer in front of us puts the client address in X-Forwarded-For
    set_real_ip_from 10.0.0.10;          # lb-01
    real_ip_header X-Forwarded-For;

    # office and VPN users only
    allow 10.20.0.0/24;
    deny all;
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/admin /etc/nginx/sites-enabled/admin
systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
: > /var/log/nginx/admin-access.log
: > /var/log/nginx/error.log
# this morning's traffic through the LB (which now runs on this VM and connects from 127.0.0.1)
for ip in 10.20.0.14 10.20.2.31 10.20.1.7 10.20.3.120 10.20.2.31 10.20.0.14; do
  curl -s -o /dev/null -H "X-Forwarded-For: $ip" http://127.0.0.1/ || true
done
