#!/bin/bash
# t2: existing assets are readable, and files deploy creates from now on (login shell) are readable by nginx.
fail() { echo "$1"; exit 1; }
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1/assets/app.css)
[ "$code" = 200 ] || fail "/assets/app.css answers $code (expected 200)"
bad=$(find /home/deploy/site -perm -o+w ! -type l | head -1)
[ -z "$bad" ] || fail "$bad is world-writable: never the fix"
probe="probe-$$"
su - deploy -c "mkdir -p ~/site/current/assets/$probe && echo ok > ~/site/current/assets/$probe/new.txt" </dev/null >/dev/null 2>&1 \
  || fail "deploy could not create a test file under ~/site/current/assets"
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1/assets/$probe/new.txt")
mode=$(stat -c %a "/home/deploy/site/current/assets/$probe/new.txt")
rm -rf "/home/deploy/site/current/assets/$probe"
[ "$code" = 200 ] || fail "a file deploy creates in a new login session gets mode $mode and answers $code: fix deploy's umask where it is set"
echo "assets answer 200, and new files from deploy's login shell are readable (mode $mode)"
