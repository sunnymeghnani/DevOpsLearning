#!/bin/bash
# t2: shop-backup fails loudly: if the database dump fails it exits non-zero and does not log "backup OK".
fail() { echo "$1"; exit 1; }
S=/usr/local/bin/shop-backup
L=/var/log/shop-backup.log
bash -n "$S" 2>/dev/null || fail "$S has a syntax error (bash -n)"
run() { env -i HOME=/root LOGNAME=root SHELL=/bin/sh PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "$S" </dev/null >/dev/null 2>&1; }
touch "$L"
before=$(grep -c 'backup OK' "$L")
touch /run/shop-db.down                      # simulate: the database is down
run; rc=$?
rm -f /run/shop-db.down
after=$(grep -c 'backup OK' "$L")
[ "$rc" -ne 0 ] || fail "with the database down, shop-backup still exits 0"
[ "$after" -eq "$before" ] || fail "with the database down, shop-backup still writes 'backup OK' to $L"
run || fail "with the database up, shop-backup now fails (exit $?)"
[ "$(grep -c 'backup OK' "$L")" -eq $((before + 1)) ] || fail "with the database up, shop-backup no longer logs 'backup OK'"
echo "shop-backup exits $rc and logs nothing when the dump fails, and still succeeds normally"
