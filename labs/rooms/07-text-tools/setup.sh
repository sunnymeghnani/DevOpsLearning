#!/bin/bash
# Room 07 (text-tools): an error spike caused by a crawler that rotates IPs but keeps one user agent.
# Broken state:
#  - incident logs exported to /var/log/incident/ (nginx access log + app JSON log, 10:30-11:00 UTC);
#  - the crawler (DocHarvester/1.7, 37 addresses in 203.0.113.0/24) is still not blocked in nginx.
set -euo pipefail

install -d -m 0755 /var/log/incident /srv/incident /var/www/docs/downloads
rm -f /srv/incident/*
python3 - <<'PY'
# Deterministic log generator (own LCG, so the numbers never change between Python versions).
import json
seed = 20261020
def rnd(n):
    global seed
    seed = (seed * 1103515245 + 12345) % 2**31
    return seed % n

browsers = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "curl/8.5.0",
]
bot = "Mozilla/5.0 (compatible; DocHarvester/1.7; +https://crawler.example.net/bot)"
users = [f"192.0.2.{i}" for i in range(10, 34)] + [f"198.51.100.{i}" for i in range(40, 56)]
bots = [f"203.0.113.{i}" for i in range(11, 48)]            # 37 addresses
pages = ["/", "/docs/install", "/docs/config", "/docs/upgrade", "/api/search?q=proxy", "/api/search?q=tls",
         "/static/app.css", "/static/app.js", "/favicon.ico", "/docs/missing-page"]
zips = [f"/downloads/docs-{v}-html.zip" for v in ("1.0", "1.1", "1.2", "2.0", "2.1", "2.2", "3.0")]
rows = []                                                     # (second, ip, method, path, status, bytes, ua)
for sec in range(0, 1800, 10):                                # normal users: one request every 10 s
    t = sec + rnd(10)
    path = pages[rnd(len(pages))]
    st = 404 if path == "/docs/missing-page" else (304 if rnd(6) == 0 else 200)
    if t >= 720 and rnd(3) == 0:                              # during the spike users suffer too
        st = 502
    if t == 300 + (t % 10) and sec == 300:                    # one stray 500 at 10:35
        st = 500
    rows.append((t, users[rnd(len(users))], "GET", path, st, 0 if st == 304 else 2000 + rnd(30000), browsers[rnd(len(browsers))]))
for t in range(720, 1800):                                    # the crawler from 10:42:00
    if rnd(3) != 0:
        continue
    path = zips[rnd(len(zips))] if rnd(4) else f"/docs/archive/{rnd(400)}"
    load = t - 720
    st = 200 if load < 20 else ([502, 504, 200][rnd(3)] if load < 120 else [502, 504, 504, 503, 200][rnd(5)])
    rows.append((t, bots[rnd(len(bots))], "GET", path, st, 48_000_000 + rnd(9_000_000) if st == 200 else 166, bot))
rows.sort()
with open("/var/log/incident/access-2026-10-20.log", "w") as f:
    for t, ip, m, path, st, size, ua in rows:
        ts = f"20/Oct/2026:10:{30 + t // 60:02d}:{t % 60:02d} +0000"
        f.write(f'{ip} - - [{ts}] "{m} {path} HTTP/1.1" {st} {size} "-" "{ua}"\n')
msgs = ["upstream timed out"] * 6 + ["connection pool exhausted"] * 3 + ["slow disk read on /srv/docs"]
with open("/var/log/incident/app-2026-10-20.json", "w") as f:
    for t, ip, m, path, st, size, ua in rows:
        if st >= 500:
            ev = {"ts": f"2026-10-20T10:{30 + t // 60:02d}:{t % 60:02d}Z", "level": "error",
                  "msg": msgs[rnd(len(msgs))], "path": path.split("?")[0], "client": ip, "status": st}
        elif rnd(5) == 0:
            ev = {"ts": f"2026-10-20T10:{30 + t // 60:02d}:{t % 60:02d}Z", "level": "info",
                  "msg": "request served", "path": path.split("?")[0], "client": ip, "status": st}
        else:
            continue
        f.write(json.dumps(ev) + "\n")
PY
chmod 0644 /var/log/incident/*

# the docs site, as it is now (no block yet)
echo '<!doctype html><title>Docs</title><h1>Docs</h1>' > /var/www/docs/index.html
cat > /etc/nginx/sites-available/docs <<'EOF'
server {
    listen 80 default_server;
    server_name docs.example.com;
    root /var/www/docs;
    index index.html;
}
EOF
rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/*block* /etc/nginx/conf.d/*bot*
ln -sfn /etc/nginx/sites-available/docs /etc/nginx/sites-enabled/docs
systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
