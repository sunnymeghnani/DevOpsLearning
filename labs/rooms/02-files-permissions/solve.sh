#!/bin/bash
# Reference fix for room 02 (tests only).
set -euo pipefail
tail -n 2 /var/log/nginx/error.log | grep -q '13: Permission denied'
namei -l /home/deploy/site/current/index.html >/dev/null
# t1: give "others" (www-data) traverse permission on the home directory only.
chmod o+x /home/deploy
# t2: fix what was already created, then the source of the problem: the umask in ~/.profile.
chmod -R u=rwX,go=rX /home/deploy/site/releases/2026-10-20
sed -i 's/^umask 077$/umask 022/' /home/deploy/.profile
echo "ANSWER q3=$(su - deploy -c 'umask 077; f=/tmp/umask-probe-$$; touch "$f"; stat -c %a "$f"; rm -f "$f"' </dev/null)"
echo "ANSWER q4=$(grep -l '^umask 0' /home/deploy/.profile)"
