#!/bin/bash
# Room 22 (dns-deep): "dig works, the app doesn't". getaddrinfo (NSS: files, then dns) versus dig (DNS only).
# The company DNS is a local dnsmasq on 127.0.0.2:53 (needs only NET_BIND_SERVICE); the "new API host" is a
# loopback address, so it is reachable without any network change.
# Broken state:
#  - /etc/hosts still pins api.internal.example.com to the decommissioned 192.0.2.44 (as an alias on a second
#    line, too): getent/curl/python get the old address, dig asks DNS and gets the new one;
#  - report-export calls http://api:8080 and relies on the search list: with "search example.com" the short name
#    becomes api.example.com, a different (public) host, so it fails in a way that looks like an outage.
set -euo pipefail

# --- the company DNS (stand-in): dnsmasq on 127.0.0.2, authoritative for example.com, rest to Docker's resolver
cat > /etc/dnsmasq.d/lab-dns.conf <<'CONF'
# company resolver stand-in (lab): answers example.com, forwards the rest to Docker's resolver
listen-address=127.0.0.2
bind-interfaces
no-resolv
no-hosts
local=/example.com/
server=127.0.0.11
host-record=api.internal.example.com,127.0.10.20
host-record=api.example.com,203.0.113.80
host-record=www.example.com,203.0.113.10
CONF
systemctl enable dnsmasq >/dev/null 2>&1
systemctl restart dnsmasq

# resolv.conf is a Docker bind mount: rewrite it in place (never replace the file). Docker's resolver stays second.
cat > /etc/resolv.conf <<'CONF'
# company resolver first (dnsmasq on 127.0.0.2), Docker's embedded resolver as a fallback
nameserver 127.0.0.2
nameserver 127.0.0.11
search example.com
options ndots:1 timeout:1 attempts:2
CONF

# /etc/hosts is a bind mount too: rewrite in place, keep Docker's lines, add the stale pins
grep -vE 'example\.com|^# (old|migration)' /etc/hosts > /tmp/.hosts.$$ || true
cat >> /tmp/.hosts.$$ <<'HOSTS'
# old API server, pinned during the 2025 migration (DNS was slow then)
192.0.2.44	api-old.internal.example.com api.internal.example.com
192.0.2.45	api-old-2.internal.example.com
# migration test box
192.0.2.46	staging-api.internal.example.com api.internal.example.com
HOSTS
cat /tmp/.hosts.$$ > /etc/hosts && rm -f /tmp/.hosts.$$
sed -i 's/^hosts:.*/hosts:          files dns/' /etc/nsswitch.conf

# --- the new API (127.0.10.20:8080)
id orders >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin orders
cat > /usr/local/bin/api-v2 <<'PY'
#!/usr/bin/env python3
"""api.internal.example.com (lab stand-in on a loopback address)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"ok api-v2\n" if self.path.startswith("/health") else b"{\"orders\": []}\n"
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass
ThreadingHTTPServer(("127.0.10.20", 8080), H).serve_forever()
PY
chmod 755 /usr/local/bin/api-v2
cat > /etc/systemd/system/api-v2.service <<'UNIT'
[Unit]
Description=api.internal.example.com v2 (lab stand-in)
[Service]
User=orders
ExecStart=/usr/local/bin/api-v2
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

# --- consumer 1: orders-sync, a Python worker (getaddrinfo, like most apps)
cat > /usr/local/bin/orders-sync <<'PY'
#!/usr/bin/env python3
"""Polls the orders API every 3 s and logs the result (lab stand-in)."""
import socket, time, urllib.request
URL = "http://api.internal.example.com:8080/health"
while True:
    host = URL.split("/")[2].split(":")[0]
    try:
        addr = socket.getaddrinfo(host, 8080, type=socket.SOCK_STREAM)[0][4][0]
    except OSError as e:
        addr = f"unresolved ({e})"
    try:
        body = urllib.request.urlopen(URL, timeout=2).read().decode().strip()
        print(f"sync ok: {host} -> {addr}: {body}", flush=True)
    except Exception as e:
        print(f"sync FAILED: {host} -> {addr}: {e}", flush=True)
    time.sleep(3)
PY
chmod 755 /usr/local/bin/orders-sync
cat > /etc/systemd/system/orders-sync.service <<'UNIT'
[Unit]
Description=orders-sync worker (lab stand-in)
After=api-v2.service dnsmasq.service
[Service]
User=orders
ExecStart=/usr/local/bin/orders-sync
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

# --- consumer 2: report-export, a nightly job that uses the short name
cat > /etc/report-export.conf <<'CONF'
# report-export: where the orders API lives (short name, "the search domain adds the rest")
API_URL=http://api:8080/health
CONF
cat > /usr/local/bin/report-export <<'SH'
#!/bin/bash
# nightly report export (lab stand-in): fetch from the API, fail loudly
. /etc/report-export.conf
host=${API_URL#*://}; host=${host%%[:/]*}
echo "report-export: $API_URL ($host -> $(getent ahostsv4 "$host" | awk 'NR==1{print $1}'))"
curl -fsS --max-time 3 "$API_URL"
SH
chmod 755 /usr/local/bin/report-export
cat > /etc/systemd/system/report-export.service <<'UNIT'
[Unit]
Description=nightly report export (lab stand-in)
[Service]
Type=oneshot
User=orders
ExecStart=/usr/local/bin/report-export
UNIT

systemctl daemon-reload
systemctl enable api-v2.service orders-sync.service >/dev/null 2>&1
systemctl restart api-v2.service orders-sync.service
systemctl reset-failed report-export.service >/dev/null 2>&1 || true
systemctl start report-export.service >/dev/null 2>&1 || true
