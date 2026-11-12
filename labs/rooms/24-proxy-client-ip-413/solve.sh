#!/bin/bash
# Reference fix for room 24 (tests only).
set -euo pipefail
curl -s --interface 127.0.0.77 http://uploads.example.com/ >/dev/null
tail -1 /var/log/upload-app/access.log                     # client=127.0.0.1 for everybody
curl -s -o /dev/null -w '%{http_code}\n' --data-binary @/home/lab/scan-2mb.pdf http://uploads.example.com/upload   # 413
grep 'client intended to send too large body' /var/log/nginx/uploads.error.log | tail -1
cat > /etc/nginx/snippets/proxy-client-ip.conf <<'CONF'
# pass the client address to the app (included in every location that proxies)
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
CONF
cat > /etc/nginx/sites-available/uploads <<'CONF'
# uploads.example.com: nginx in front of the upload app (127.0.0.1:8000)
server {
    listen 80;
    server_name uploads.example.com;

    access_log /var/log/nginx/uploads.access.log;
    error_log  /var/log/nginx/uploads.error.log;

    location / {
        include snippets/proxy-client-ip.conf;
        proxy_pass http://127.0.0.1:8000;
    }

    location /upload {
        include snippets/proxy-client-ip.conf;
        client_max_body_size 25m;
        proxy_read_timeout 120s;
        proxy_pass http://127.0.0.1:8000;
    }
}
CONF
nginx -t
systemctl reload nginx
sleep 0.5
curl -s --interface 127.0.0.77 http://uploads.example.com/ >/dev/null
tail -1 /var/log/upload-app/access.log
curl -s --data-binary @/home/lab/scan-2mb.pdf http://uploads.example.com/upload
