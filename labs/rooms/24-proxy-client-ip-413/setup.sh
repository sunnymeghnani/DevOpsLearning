#!/bin/bash
# Room 24 (proxy-problems): behind nginx every client has the same IP, and uploads over 1 MB fail with 413.
# The app (python3, 127.0.0.1:8000) logs the client address it believes in: X-Real-IP when the request comes from
# the local proxy, else the peer. Test clients use other loopback source addresses (curl --interface 127.0.0.77).
# Broken state:
#  - the proxy sends no X-Real-IP / X-Forwarded-For, so the app logs 127.0.0.1 for everybody;
#  - location /upload has its own proxy_set_header line, so headers set at server level would NOT reach it
#    (proxy_set_header is inherited only when a level defines none);
#  - client_max_body_size is the default 1m: a 2 MB upload gets "413 Request Entity Too Large" from nginx.
set -euo pipefail

id uploads >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin uploads
install -d -o uploads -g uploads -m 0755 /var/log/upload-app /srv/uploads
: > /var/log/upload-app/access.log
chown uploads:uploads /var/log/upload-app/access.log
find /srv/uploads -mindepth 1 -maxdepth 1 -type f -delete

cat > /usr/local/bin/upload-app <<'PY'
#!/usr/bin/env python3
"""uploads.example.com backend (lab stand-in). Trusts X-Real-IP only from the local proxy."""
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = "/var/log/upload-app/access.log"
TRUSTED_PROXIES = {"127.0.0.1"}
MAX = 10 * 1024 * 1024

class H(BaseHTTPRequestHandler):
    def client(self):
        peer = self.client_address[0]
        real = self.headers.get("X-Real-IP")
        return real.strip() if real and peer in TRUSTED_PROXIES else peer

    def log_request_line(self, status, nbytes):
        with open(LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} client={self.client()} peer={self.client_address[0]} "
                    f"xff=\"{self.headers.get('X-Forwarded-For', '-')}\" rid={self.headers.get('X-Request-Id', '-')} "
                    f"{self.command} {self.path} {status} bytes={nbytes}\n")

    def reply(self, status, text):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.log_request_line(200, 0)
        self.reply(200, f"hello {self.client()}\n")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX:
            self.log_request_line(413, n)
            return self.reply(413, "too large for the app\n")
        left, got = n, 0
        while left > 0:
            chunk = self.rfile.read(min(65536, left))
            if not chunk:
                break
            got += len(chunk)
            left -= len(chunk)
        self.log_request_line(200, got)
        self.reply(200, f"stored {got} bytes from {self.client()}\n")

    def log_message(self, *a):
        pass

ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
PY
chmod 755 /usr/local/bin/upload-app
cat > /etc/systemd/system/upload-app.service <<'UNIT'
[Unit]
Description=uploads.example.com backend (lab stand-in)
After=network.target

[Service]
User=uploads
ExecStart=/usr/local/bin/upload-app
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/nginx/sites-available/uploads <<'CONF'
# uploads.example.com: nginx in front of the upload app (127.0.0.1:8000)
server {
    listen 80;
    server_name uploads.example.com;

    access_log /var/log/nginx/uploads.access.log;
    error_log  /var/log/nginx/uploads.error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }

    location /upload {
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
        proxy_pass http://127.0.0.1:8000;
    }
}
CONF
ln -sfn /etc/nginx/sites-available/uploads /etc/nginx/sites-enabled/uploads
rm -f /var/log/nginx/uploads.access.log /var/log/nginx/uploads.error.log

# the name -> this box (/etc/hosts is a bind mount: rewrite in place)
grep -v 'uploads\.example\.com' /etc/hosts > /tmp/.hosts.$$ || true
echo '127.0.0.1 uploads.example.com' >> /tmp/.hosts.$$
cat /tmp/.hosts.$$ > /etc/hosts && rm -f /tmp/.hosts.$$

# a test file for the learner: 2 MB
head -c 2097152 /dev/urandom > /home/lab/scan-2mb.pdf
chown lab:lab /home/lab/scan-2mb.pdf

systemctl daemon-reload
systemctl enable upload-app.service nginx.service >/dev/null 2>&1
systemctl restart upload-app.service nginx.service
