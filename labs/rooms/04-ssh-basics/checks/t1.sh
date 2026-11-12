#!/bin/bash
# t1: ssh (as ops) accepts the private key again; it is still the key deploy trusts and the "app" alias uses.
fail() { echo "$1"; exit 1; }
K=/home/ops/.ssh/deploy.pem
[ -f "$K" ] || fail "$K is missing"
[ "$(stat -c %U "$K")" = ops ] || fail "$K must be owned by ops"
m=$(stat -c %a "$K")
(( 8#$m & 8#077 )) && fail "$K has mode $m: group/others can still read it"
(( 8#$(stat -c %a /home/ops/.ssh) & 8#022 )) && fail "/home/ops/.ssh is writable by group/others"
pub=$(runuser -u ops -- ssh-keygen -y -f "$K" </dev/null 2>/dev/null) || fail "ssh still refuses to load $K"
grep -qF "$(cut -d' ' -f2 <<< "$pub")" /home/deploy/.ssh/authorized_keys || fail "$K is not the key that deploy's authorized_keys trusts"
runuser -u ops -- ssh -G app </dev/null 2>/dev/null | grep -qi '^identityfile .*deploy\.pem' \
  || fail "the 'app' alias in ~ops/.ssh/config no longer uses deploy.pem"
echo "ops's key has mode $m and loads again"
