#!/bin/bash
# t2: "ssh app" as ops logs in as deploy with the key; sshd still enforces StrictModes.
fail() { echo "$1"; exit 1; }
cfg=$(sshd -T 2>&1) || fail "sshd -T reports an error: ${cfg##*$'\n'}"
grep -qi '^strictmodes yes' <<< "$cfg" || fail "StrictModes is off in sshd: fix the modes instead of disabling the check"
for p in /home/deploy /home/deploy/.ssh /home/deploy/.ssh/authorized_keys; do
  [ -e "$p" ] || fail "$p is missing"
  [ "$(stat -c %U "$p")" = deploy ] || fail "$p must be owned by deploy"
  m=$(stat -c %a "$p")
  (( 8#$m & 8#022 )) && fail "$p is writable by group/others (mode $m)"
done
who=$(runuser -u ops -- ssh -o BatchMode=yes -o ConnectTimeout=5 app whoami </dev/null 2>/tmp/.ssherr.$$)
err=$(tail -n1 /tmp/.ssherr.$$); rm -f /tmp/.ssherr.$$
[ "$who" = deploy ] || fail "ssh app (as ops) does not log in: ${err:-no output}"
echo "ssh app logs in as deploy with the key; StrictModes stays on"
