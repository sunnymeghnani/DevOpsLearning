#!/bin/bash
# Room 03 (users-sudo): "sudo: unable to resolve host" after a rename, and a sudoers drop-in that is silently ignored.
# Broken state:
#  - hostname changed to app-prod-01 (and /etc/hostname), but /etc/hosts still only knows the old name;
#  - /etc/sudoers.d/deploy.conf grants deploy one command, but sudo skips file names that contain a dot.
set -euo pipefail

hostname app-prod-01
echo app-prod-01 > /etc/hostname
# /etc/hosts keeps the old name only (remove anything a previous run or the learner added)
# (/etc/hosts is a bind mount in this lab: rewrite it in place, sed -i cannot rename over it)
grep -v 'app-prod-01' /etc/hosts > /tmp/.hosts.$$ || true
cat /tmp/.hosts.$$ > /etc/hosts
rm -f /tmp/.hosts.$$

id deploy >/dev/null 2>&1 || useradd -m -s /bin/bash deploy
for g in sudo admin; do gpasswd -d deploy "$g" >/dev/null 2>&1 || true; done
rm -f /etc/sudoers.d/deploy /etc/sudoers.d/deploy-nginx /etc/sudoers.d/deploy_nginx
cat > /etc/sudoers.d/deploy.conf <<'EOF'
# CI deploy user may restart nginx after a release (ticket OPS-2981)
deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx
EOF
chmod 0440 /etc/sudoers.d/deploy.conf

mkdir -p /opt/ci
cat > /opt/ci/post-deploy.sh <<'EOF'
#!/bin/bash
# runs as deploy at the end of every pipeline
set -euo pipefail
sudo -n /usr/bin/systemctl restart nginx
echo "nginx restarted"
EOF
chmod 755 /opt/ci/post-deploy.sh

systemctl enable nginx >/dev/null 2>&1
systemctl restart nginx
