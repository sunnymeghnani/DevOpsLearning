#!/bin/bash
# Reference fix for room 04 (tests only).
set -euo pipefail
K=/home/ops/.ssh/deploy.pem
# t1: read the client warning, then make the key private to its owner.
mode=$(runuser -u ops -- ssh -o BatchMode=yes app true </dev/null 2>&1 | sed -n 's/^Permissions \([0-7]*\) for.*/\1/p' | head -1 || true)
echo "ANSWER q1=$mode"
chmod 600 "$K"
# t2: the server side. Logs are in the journal; a one-shot debug sshd shows the reason right away.
timeout 8 /usr/sbin/sshd -d -p 2222 >/tmp/sshd-debug.log 2>&1 &
sleep 1
runuser -u ops -- ssh -p 2222 -o BatchMode=yes app true </dev/null >/dev/null 2>&1 || true
wait || true
first=$(sed -n 's/.*bad ownership or modes for \(file\|directory\) \(.*\)$/\2/p' /tmp/sshd-debug.log | head -1)
echo "ANSWER q4=$first"
chmod 755 /home/deploy
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chmod 755 /home/deploy/uploads
runuser -u ops -- ssh -o BatchMode=yes app whoami </dev/null
