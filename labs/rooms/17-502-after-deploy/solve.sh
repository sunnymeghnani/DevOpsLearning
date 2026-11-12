#!/bin/bash
# Reference fix for room 17 (tests only).
set -euo pipefail
H='Host: api.shop.example.com'
[ "$(curl -s -o /dev/null -w '%{http_code}' -H "$H" http://127.0.0.1/)" = 502 ]
grep -q '(111: Connection refused) while connecting to upstream' /var/log/nginx/error.log
echo "ANSWER q1=$(ss -Hltn | awk '{print $4}' | grep -m1 '^127\.0\.0\.1:23' | cut -d: -f2)"
# t1: point the upstream at the port the app really uses.
sed -i 's/server 127.0.0.1:2368;/server 127.0.0.1:2369;/' /etc/nginx/sites-available/shop-api
nginx -t
systemctl reload nginx
sleep 0.5
curl -s -H "$H" http://127.0.0.1/
echo "ANSWER q3=$(curl -s -o /dev/null -w '%{http_code}' -H "$H" http://127.0.0.1/reports/monthly)"
# t2: a longer read timeout for the report location only.
python3 - <<'PY'
p = "/etc/nginx/sites-available/shop-api"
s = open(p).read()
s = s.replace("    location / {", """    location /reports/ {
        proxy_pass http://shop_api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;     # monthly report takes ~5 s; well above that, still bounded
    }

    location / {""", 1)
open(p, "w").write(s)
PY
nginx -t
systemctl reload nginx
sleep 0.5
curl -s -H "$H" http://127.0.0.1/reports/monthly
