#!/bin/bash
# Room 17 (reverse-proxy): 502 after a "successful" deploy, then a 504 on the slow report endpoint.
# Broken state:
#  - shop-api 2.4 (python3, systemd unit, user shopapi) listens on 127.0.0.1:2369 (PORT in /etc/shop-api/env);
#  - nginx's upstream still says 127.0.0.1:2368 -> connect() failed (111: Connection refused) -> 502;
#  - the server block sets proxy_read_timeout 3s (fail fast), but /reports/monthly needs ~5 s -> 504 once t1 is fixed.
set -euo pipefail

systemctl stop shop-api >/dev/null 2>&1 || true
systemctl reset-failed shop-api >/dev/null 2>&1 || true
id shopapi >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin shopapi

install -d /opt/shop-api /etc/shop-api
cat > /opt/shop-api/app.py <<'PY'
#!/usr/bin/python3
"""shop-api 2.4: tiny JSON API behind nginx."""
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SLOW = {"/reports/monthly": 5, "/api/stall": 15}   # seconds; /api/stall is the monitoring probe for the fail-fast limit


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in SLOW:
            time.sleep(SLOW[path])
        if path == "/reports/monthly":
            body = {"report": "monthly", "status": "ready", "rows": 1240}
        elif path in ("/", "/health", "/api/stall"):
            body = {"service": "shop-api", "version": "2.4", "status": "ok"}
        else:
            self.send_error(404)
            return
        data = (json.dumps(body) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args), flush=True)


ThreadingHTTPServer.daemon_threads = True
addr = (os.environ.get("BIND", "127.0.0.1"), int(os.environ.get("PORT", "8000")))
print("shop-api 2.4 listening on %s:%d" % addr, flush=True)
ThreadingHTTPServer(addr, H).serve_forever()
PY
chmod 755 /opt/shop-api/app.py
cat > /etc/shop-api/env <<'ENV'
# shop-api 2.4: the default port changed from 2368 to 2369 (release notes, "breaking changes")
BIND=127.0.0.1
PORT=2369
ENV
cat > /etc/systemd/system/shop-api.service <<'UNIT'
[Unit]
Description=shop-api (JSON API behind nginx)
After=network.target

[Service]
User=shopapi
EnvironmentFile=/etc/shop-api/env
ExecStart=/opt/shop-api/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/nginx/sites-available/shop-api <<'CONF'
# api.shop.example.com -> shop-api
upstream shop_api {
    server 127.0.0.1:2368;
}

server {
    listen 80;
    server_name api.shop.example.com;

    # fail fast: a hung backend must not pile up requests (SRE-88)
    proxy_connect_timeout 2s;
    proxy_read_timeout 3s;

    location / {
        proxy_pass http://shop_api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
CONF
ln -sfn /etc/nginx/sites-available/shop-api /etc/nginx/sites-enabled/shop-api
[ -e /etc/nginx/sites-enabled/default ] || ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable shop-api nginx >/dev/null 2>&1
systemctl start shop-api
systemctl restart nginx
for _ in $(seq 30); do ss -Hltn 'sport = :2369' | grep -q . && break; sleep 0.1; done
# the deploy pipeline's smoke test (it only checked that the unit is active), and a few real requests
for _ in 1 2 3; do curl -s -o /dev/null -H 'Host: api.shop.example.com' http://127.0.0.1/ || true; done
