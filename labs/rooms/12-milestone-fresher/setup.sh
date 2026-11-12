#!/bin/bash
# Room 12 (milestone-fresher): capstone "broken server handover". Several L0 skills, no hints in the brief.
# Broken state:
#  - nginx is stopped and disabled; the shop site has a syntax error (missing ';'), so nginx cannot start;
#  - /srv/shop is deploy-only (0750/0640): once nginx runs, the shop answers 403;
#  - the health probe run by cron every minute was written on Windows (CRLF): "/bin/bash^M: bad interpreter".
set -euo pipefail

id deploy >/dev/null 2>&1 || useradd -m -s /bin/bash deploy

# --- web content, private to deploy ---
rm -rf /srv/shop
install -d -o deploy -g deploy -m 0750 /srv/shop /srv/shop/public
echo '<!doctype html><title>Shop</title><h1>Shop is up</h1>' > /srv/shop/public/index.html
chown deploy:deploy /srv/shop/public/index.html
chmod 0640 /srv/shop/public/index.html

# --- nginx: broken site, service down ---
cat > /etc/nginx/sites-available/shop <<'EOF'
# shop.example.com (handed over by the contractor)
server {
    listen 80;
    server_name shop.example.com;
    root /srv/shop/public
    index index.html;
}
EOF
ln -sfn /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/shop
systemctl disable --now nginx >/dev/null 2>&1 || true

# --- health probe from a Windows laptop (CRLF line endings) ---
install -d /var/lib/shop
rm -f /var/lib/shop/health.txt
printf '%s\r\n' \
  '#!/bin/bash' \
  '# shop health probe: records the HTTP status of the shop every minute' \
  "code=\$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 -H 'Host: shop.example.com' http://127.0.0.1/)" \
  'echo "$(date -Is) $code" > /var/lib/shop/health.txt' \
  '[ "$code" = 200 ]' > /usr/local/bin/shop-health
chmod 755 /usr/local/bin/shop-health
cat > /etc/cron.d/shop-health <<'EOF'
# shop health probe, every minute
* * * * * root /usr/local/bin/shop-health
EOF
chmod 644 /etc/cron.d/shop-health
systemctl enable cron >/dev/null 2>&1
systemctl restart cron
