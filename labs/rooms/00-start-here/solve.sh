#!/usr/bin/env bash
# TEST ONLY (never served to the browser): the documented fix for 00-start-here.
set -euo pipefail
note=$(grep -rl --include='*.txt' 'Handover, night shift' /srv/ops | head -n1)
ticket=$(grep -o 'OPS-[0-9]\+' "$note" | head -n1)
# t1: record where you are, as the on-call user
runuser -u lab -- sh -c 'hostname > /home/lab/whereami.txt'
# t2: acknowledge the handover
runuser -u lab -- sh -c "echo '$ticket' > '$(dirname "$note")/handover.ack'"
# t3: start nginx now and at every boot
systemctl enable --now nginx >/dev/null 2>&1
port=$(ss -Htlnp 'sport = :80' | grep -q nginx && echo 80)
. /etc/os-release
echo "ANSWER q-hostname=$(hostname)"
echo "ANSWER q-codename=$VERSION_CODENAME"
echo "ANSWER q-note-path=$note"
echo "ANSWER q-ticket=$ticket"
echo "ANSWER q-port=$port"
echo "ANSWER q-enable=enable"
