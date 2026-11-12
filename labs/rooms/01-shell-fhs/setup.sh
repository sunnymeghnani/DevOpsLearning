#!/bin/bash
# Room 01 (shell-fhs): an edit that changes nothing, and a command that runs the wrong copy.
# Broken state:
#  - /etc/nginx/sites-enabled/shop is a stale regular COPY, so edits to sites-available/shop never load;
#  - an old shopctl 1.0 copy in /usr/local/sbin shadows the vendor's 2.3.1 in /opt/shop/bin (not on PATH).
set -euo pipefail

mkdir -p /var/www/shop
cat > /var/www/shop/index.html <<'EOF'
<!doctype html><title>Shop</title><h1>Shop</h1><p>Welcome to the shop.</p>
EOF
cat > /var/www/shop/maintenance.html <<'EOF'
<!doctype html><title>Shop</title><h1>Shop</h1><p>MAINTENANCE 09:00-09:30 UTC: checkout is paused.</p>
EOF

# The file the team edited this morning (correct, new).
cat > /etc/nginx/sites-available/shop <<'EOF'
# shop.example.com - edited 2026-10-20 for the 09:00 maintenance window (CHG-2210)
server {
    listen 80 default_server;
    server_name shop.example.com;
    root /var/www/shop;
    index maintenance.html;

    location = /healthz {
        default_type text/plain;
        return 200 "ok\n";
    }
}
EOF

# The stale copy someone made months ago with cp instead of ln -s.
rm -f /etc/nginx/sites-enabled/shop /etc/nginx/sites-enabled/default
cat > /etc/nginx/sites-enabled/shop <<'EOF'
# shop.example.com
server {
    listen 80 default_server;
    server_name shop.example.com;
    root /var/www/shop;
    index index.html;
}
EOF
touch -d '2026-06-02 14:10' /etc/nginx/sites-enabled/shop

# shopctl: the vendor package puts 2.3.1 under /opt; an old hand-copied 1.0 shadows it.
mkdir -p /opt/shop/bin /opt/shop/share
cat > /opt/shop/bin/shopctl <<'EOF'
#!/bin/bash
# shopctl 2.3.1 - shop operations helper (vendor package, installed under /opt/shop)
case "${1:-}" in
  version) echo "shopctl 2.3.1" ;;
  status)  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/healthz)
           echo "shop health: HTTP $code" ; [ "$code" = 200 ] ;;
  *) echo "usage: shopctl {version|status}" >&2; exit 2 ;;
esac
EOF
chmod 755 /opt/shop/bin/shopctl
echo "Docs: run 'shopctl status' after every change. Binary: /opt/shop/bin/shopctl" > /opt/shop/share/README
rm -f /usr/local/bin/shopctl
cat > /usr/local/sbin/shopctl <<'EOF'
#!/bin/bash
# shopctl 1.0 (copied by hand in 2025, before the vendor package existed)
case "${1:-}" in
  version) echo "shopctl 1.0" ;;
  status)  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status)
           echo "shop health: HTTP $code" ; [ "$code" = 200 ] ;;
  *) echo "usage: shopctl {version|status}" >&2; exit 2 ;;
esac
EOF
chmod 755 /usr/local/sbin/shopctl
touch -d '2025-03-11 09:00' /usr/local/sbin/shopctl

systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
