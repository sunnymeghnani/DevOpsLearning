#!/bin/bash
# Room 02 (files-permissions): nginx 403 for a site under /home/deploy.
# Broken state:
#  - /home/deploy is 0750 (Ubuntu 21.04+ default HOME_MODE), so www-data cannot traverse it -> 403 on everything;
#  - deploy's ~/.profile sets umask 077, so the new release's assets were created 0600/0700 -> 403 on assets.
set -euo pipefail

id deploy >/dev/null 2>&1 || useradd -m -s /bin/bash deploy
H=/home/deploy
chmod 0750 "$H"
gpasswd -d www-data deploy >/dev/null 2>&1 || true

# "hardening" line added by a well-meant ticket
sed -i '/SEC-142/,+1d' "$H/.profile" 2>/dev/null || true
printf '\n# hardening (ticket SEC-142): keep new files private\numask 077\n' >> "$H/.profile"
chown deploy:deploy "$H/.profile"

rm -rf "$H/site"
R="$H/site/releases/2026-10-20"
install -d -o deploy -g deploy -m 0755 "$H/site" "$H/site/releases" "$R"
cat > "$R/index.html" <<'EOF'
<!doctype html><title>Docs</title><link rel="stylesheet" href="/assets/app.css"><h1>Docs portal</h1><p>Release 2026-10-20</p>
EOF
chmod 0644 "$R/index.html"
# assets written by the deploy job under umask 077
install -d -o deploy -g deploy -m 0700 "$R/assets"
printf 'body { font-family: sans-serif; }\n' > "$R/assets/app.css"
chmod 0600 "$R/assets/app.css"
chown -R deploy:deploy "$H/site"
ln -sfn "$R" "$H/site/current"
chown -h deploy:deploy "$H/site/current"

cat > /etc/nginx/sites-available/docs <<'EOF'
server {
    listen 80 default_server;
    server_name docs.example.com;
    root /home/deploy/site/current;
    index index.html;
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/docs /etc/nginx/sites-enabled/docs
: > /var/log/nginx/error.log
systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
curl -s -o /dev/null http://127.0.0.1/ || true
curl -s -o /dev/null http://127.0.0.1/assets/app.css || true
