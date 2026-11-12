#!/bin/bash
# t2: every shopctl on the standard PATH (users and sudo) resolves to the vendor binary under /opt.
fail() { echo "$1"; exit 1; }
STD=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
[ -x /opt/shop/bin/shopctl ] || fail "/opt/shop/bin/shopctl is missing or not executable"
out=$(env -i PATH="$STD" HOME=/root bash -c 'shopctl version' 2>/dev/null) || fail "shopctl is not found on the standard PATH"
[ "$out" = "shopctl 2.3.1" ] || fail "shopctl on PATH reports '$out' (expected shopctl 2.3.1)"
secure=$(sudo -V 2>/dev/null | sed -n 's/^Value to override user.s \$PATH with: //p')
out=$(env -i PATH="${secure:-$STD}" bash -c 'shopctl version' 2>/dev/null)
[ "$out" = "shopctl 2.3.1" ] || fail "sudo shopctl (secure_path) still runs '$out'"
IFS=: read -ra dirs <<< "$STD"
for d in "${dirs[@]}"; do
  [ -e "$d/shopctl" ] || continue
  [ "$(readlink -f "$d/shopctl")" = /opt/shop/bin/shopctl ] || fail "$d/shopctl is a separate copy, not a link to /opt/shop/bin/shopctl"
done
echo "shopctl resolves to /opt/shop/bin/shopctl (2.3.1) for users and sudo"
