#!/bin/bash
# Room 14 (sockets-ports): dnsmasq can't start because a local DNS stub already holds 127.0.0.53:53.
# This lab machine cannot run systemd-resolved itself (it needs CAP_SETPCAP to drop its privileges), so
# stub-resolver.service plays the part of resolved's stub listener: a tiny DNS server on 127.0.0.53:53,
# answering from /etc/hosts. The rest is real: Ubuntu's dnsmasq binds the wildcard 0.0.0.0:53 by default and fails.
# Broken state:
#  - stub-resolver on 127.0.0.53:53 (udp+tcp), enabled, must stay;
#  - dnsmasq (stock config + /etc/dnsmasq.d/internal.conf) fails: "failed to create listening socket for port 53";
#  - the hosts-format file /etc/dnsmasq.hosts (cache/queue records) is not loaded by any dnsmasq option.
set -euo pipefail

systemctl stop dnsmasq >/dev/null 2>&1 || true
systemctl reset-failed dnsmasq >/dev/null 2>&1 || true

# --- the stub (stand-in for systemd-resolved's stub listener) ---
install -d /usr/local/lib/stub-resolver
cat > /usr/local/lib/stub-resolver/stub.py <<'PY'
#!/usr/bin/python3
"""Minimal local DNS stub on 127.0.0.53:53 (lab stand-in for systemd-resolved's stub listener).
Answers A queries from /etc/hosts; everything else gets NXDOMAIN."""
import socket, socketserver, struct, threading

ADDR = ("127.0.0.53", 53)


def hosts():
    m = {}
    try:
        for line in open("/etc/hosts"):
            f = line.split("#")[0].split()
            if len(f) >= 2 and "." in f[0] and ":" not in f[0]:
                for n in f[1:]:
                    m.setdefault(n.lower().rstrip("."), f[0])
    except OSError:
        pass
    return m


def answer(q):
    if len(q) < 12:
        return None
    tid, _flags, qd = struct.unpack(">HHH", q[:6])
    i, labels = 12, []
    while i < len(q) and q[i]:
        labels.append(q[i + 1:i + 1 + q[i]].decode(errors="replace"))
        i += 1 + q[i]
    qend = i + 5
    if qd != 1 or qend > len(q):
        return None
    qtype = struct.unpack(">H", q[i + 1:i + 3])[0]
    ip = hosts().get(".".join(labels).lower())
    head = struct.pack(">HHHHHH", tid, 0x8180 if ip else 0x8183, 1, 1 if ip and qtype == 1 else 0, 0, 0)
    body = q[12:qend]
    if ip and qtype == 1:
        body += b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 30, 4) + socket.inet_aton(ip)
    return head + body


class TCP(socketserver.BaseRequestHandler):
    def handle(self):
        n = self.request.recv(2)
        if len(n) == 2:
            a = answer(self.request.recv(struct.unpack(">H", n)[0]))
            if a:
                self.request.sendall(struct.pack(">H", len(a)) + a)


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(ADDR)
threading.Thread(target=TCPServer(ADDR, TCP).serve_forever, daemon=True).start()
while True:
    q, peer = udp.recvfrom(512)
    a = answer(q)
    if a:
        udp.sendto(a, peer)
PY
chmod 755 /usr/local/lib/stub-resolver/stub.py
cat > /etc/systemd/system/stub-resolver.service <<'UNIT'
[Unit]
Description=Local DNS stub on 127.0.0.53 (lab stand-in for systemd-resolved's stub listener)
Before=nss-lookup.target dnsmasq.service

[Service]
ExecStart=/usr/local/lib/stub-resolver/stub.py
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

# a name the stub knows (from /etc/hosts; it is a bind mount here: rewrite in place)
grep -v 'example\.com' /etc/hosts > /tmp/.hosts.$$ || true
echo '192.0.2.1 gw.example.com' >> /tmp/.hosts.$$
cat /tmp/.hosts.$$ > /etc/hosts && rm -f /tmp/.hosts.$$

# --- dnsmasq: stock config plus the internal records ---
sed -i -E '/^(listen-address|bind-interfaces|bind-dynamic|interface|except-interface|addn-hosts|port)\b/d' /etc/dnsmasq.conf
find /etc/dnsmasq.d -maxdepth 1 -type f -name '*.conf' -delete
cat > /etc/dnsmasq.d/internal.conf <<'CONF'
# internal names for the app servers (ticket NET-207)
domain-needed
bogus-priv
address=/db.example.com/192.0.2.10
CONF
cat > /etc/dnsmasq.hosts <<'CONF'
# from the network team: hosts format, one "IP name" per line
192.0.2.11  cache.example.com
192.0.2.12  queue.example.com
CONF

systemctl daemon-reload
systemctl enable stub-resolver >/dev/null 2>&1
systemctl restart stub-resolver
for _ in $(seq 30); do ss -Hlun 'sport = :53' | grep -q 127.0.0.53 && break; sleep 0.1; done
systemctl enable dnsmasq >/dev/null 2>&1
systemctl start dnsmasq >/dev/null 2>&1 || true
