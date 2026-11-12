#!/bin/bash
# Room 04 (ssh-basics): key login for deploy fails on both ends.
# Broken state:
#  - client: ops's private key (deploy.pem) arrived with mode 0644 -> "WARNING: UNPROTECTED PRIVATE KEY FILE!", key ignored;
#  - server: someone ran "chmod -R a+rwX" on /home/deploy -> sshd StrictModes refuses authorized_keys.
set -euo pipefail

# sshd: Ubuntu 24.04 starts it through ssh.socket. If the image masks the socket, run ssh.service directly.
if [ "$(systemctl is-enabled ssh.socket 2>/dev/null || true)" = masked ]; then
  rm -f /etc/systemd/system/ssh.service.requires/ssh.socket
  systemctl daemon-reload
  systemctl enable ssh >/dev/null 2>&1
  systemctl restart ssh
else
  systemctl enable ssh.socket >/dev/null 2>&1
  systemctl restart ssh.socket
fi
install -d -m 0755 /run/sshd   # privilege separation dir (sshd -t / -T / -d need it)

for u in ops deploy; do id "$u" >/dev/null 2>&1 || useradd -m -s /bin/bash "$u"; done

# --- client side (ops) ---
# A PEM RSA key, like the .pem files cloud consoles hand out; only the private key was copied (no .pub).
install -d -o ops -g ops -m 0700 /home/ops/.ssh
K=/home/ops/.ssh/deploy.pem
if [ ! -f "$K" ]; then
  runuser -u ops -- ssh-keygen -q -t rsa -b 2048 -m PEM -N '' -C '' -f "$K"
  rm -f "$K.pub"
fi
cat > /home/ops/.ssh/config <<'CFG'
# app server (key copied from the old jump host)
Host app
    HostName 127.0.0.1
    User deploy
    IdentityFile ~/.ssh/deploy.pem
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
CFG
chown ops:ops /home/ops/.ssh/config "$K"
chmod 0600 /home/ops/.ssh/config
rm -f /home/ops/.ssh/known_hosts /home/ops/.ssh/known_hosts.old

# --- server side (deploy) ---
install -d -o deploy -g deploy /home/deploy/.ssh /home/deploy/uploads
ssh-keygen -y -f "$K" | sed 's/$/ ops@jump-01/' > /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
echo "uploads land here" > /home/deploy/uploads/README
chown deploy:deploy /home/deploy/uploads/README

# the broken modes
chmod 0644 "$K"                   # "unzipped from the old jump host"
chmod -R a+rwX /home/deploy       # the "quick fix" for an upload error last Friday
