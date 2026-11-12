#!/bin/bash
# Reference fix for room 08 (tests only).
set -euo pipefail
# Reproduce cron: minimal environment.
env -i HOME=/root LOGNAME=root SHELL=/bin/sh PATH=/usr/bin:/bin /bin/sh -c /usr/local/bin/shop-backup >/tmp/cron-like.txt 2>&1 || true
grep -q 'command not found' /tmp/cron-like.txt
echo "ANSWER q4=$(bash -c 'false | true; echo $?')"
# t1: run cron, and give the job a full PATH in the cron file.
systemctl enable --now cron
sed -i 's|^# m  h  dom mon dow user command$|PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n&|' /etc/cron.d/shop-backup
# t2: stop on the first error, including inside pipelines; quote variables.
cat > /usr/local/bin/shop-backup <<'EOF'
#!/bin/bash
# Nightly backup of the shop: check the web config, dump the database, archive the web root.
set -euo pipefail
STAMP=$(date +%F)
DEST=/var/backups/shop

mkdir -p "$DEST"
nginx -t -q
shop-snapshot --stdout | gzip > "$DEST/db-$STAMP.sql.gz"
tar -czf "$DEST/www-$STAMP.tar.gz" -C /var/www shop
echo "$(date -Is) backup OK" >> /var/log/shop-backup.log
EOF
cat /etc/cron.d/shop-backup
