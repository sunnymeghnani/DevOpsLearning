#!/bin/bash
# Room 08 (bash-scripting): the nightly backup "works by hand" and its log says OK, but cron never made a real dump.
# Broken state:
#  - cron.service is stopped and disabled (golden image default);
#  - /etc/cron.d/shop-backup runs with cron's PATH=/usr/bin:/bin, where nginx (/usr/sbin) and shop-snapshot
#    (/usr/local/sbin) are not found;
#  - /usr/local/bin/shop-backup has no error handling: "shop-snapshot | gzip" succeeds even when shop-snapshot fails,
#    so it logs "backup OK" over empty dumps.
set -euo pipefail

systemctl disable --now cron >/dev/null 2>&1 || true
rm -f /run/shop-db.down

install -d /var/www/shop /var/backups/shop
echo '<!doctype html><title>Shop</title><h1>Shop</h1>' > /var/www/shop/index.html

cat > /usr/local/sbin/shop-snapshot <<'EOF'
#!/bin/bash
# shop-snapshot: dump the shop database as SQL (vendor tool). --stdout writes the dump to standard output.
if [ -e /run/shop-db.down ]; then
  echo "shop-snapshot: cannot connect to database shop on 127.0.0.1:5432: Connection refused" >&2
  exit 3
fi
[ "${1:-}" = --stdout ] || { echo "usage: shop-snapshot --stdout" >&2; exit 2; }
echo "-- shop database dump $(date -Is)"
echo "CREATE TABLE orders (id integer PRIMARY KEY, total_cents integer, created_at timestamp);"
for i in $(seq 1 200); do echo "INSERT INTO orders VALUES ($i, $((i * 137 % 9000 + 500)), '2026-10-19 10:00:00');"; done
EOF
chmod 755 /usr/local/sbin/shop-snapshot

cat > /usr/local/bin/shop-backup <<'EOF'
#!/bin/bash
# Nightly backup of the shop: check the web config, dump the database, archive the web root.
STAMP=$(date +%F)
DEST=/var/backups/shop

mkdir -p $DEST
nginx -t -q
shop-snapshot --stdout | gzip > $DEST/db-$STAMP.sql.gz
tar -czf $DEST/www-$STAMP.tar.gz -C /var/www shop
echo "$(date -Is) backup OK" >> /var/log/shop-backup.log
EOF
chmod 755 /usr/local/bin/shop-backup

cat > /etc/cron.d/shop-backup <<'EOF'
# nightly shop backup (ticket OPS-1880)
# m  h  dom mon dow user command
30 2 * * * root /usr/local/bin/shop-backup
EOF
chmod 644 /etc/cron.d/shop-backup

# a week of "successful" nights: 20-byte gzip files (gzip of nothing) and OK lines
rm -f /var/backups/shop/* /var/log/shop-backup.log
for d in 13 14 15 16 17 18 19; do
  : | gzip > "/var/backups/shop/db-2026-10-$d.sql.gz"
  tar -czf "/var/backups/shop/www-2026-10-$d.tar.gz" -C /var/www shop
  touch -d "2026-10-$d 02:30:01" "/var/backups/shop/db-2026-10-$d.sql.gz" "/var/backups/shop/www-2026-10-$d.tar.gz"
  echo "2026-10-${d}T02:30:01+00:00 backup OK" >> /var/log/shop-backup.log
done
