#!/bin/bash
# t2: the hotfix from the detached HEAD is on main, locally and on origin, without losing the rate-limit change.
fail() { echo "$1"; exit 1; }
R=/home/deploy/shop
B=/srv/git/shop.git
g() { runuser -u deploy -- git -C "$1" "${@:2}" 2>/dev/null; }
g "$R" log main --format=%s | grep -q '^hotfix: raise proxy_read_timeout' || fail "main's history has no hotfix commit yet"
g "$R" show main:timeout.conf | grep -q 'proxy_read_timeout 30s' || fail "timeout.conf on main does not have 30s"
g "$B" show main:timeout.conf | grep -q 'proxy_read_timeout 30s' || fail "origin/main does not have the hotfix yet (push it)"
g "$B" show main:app.conf | grep -q '^rate_limit=100$' || fail "origin/main lost the rate limiting change"
for c in $(g "$B" rev-list --all); do
  g "$B" ls-tree -r --name-only "$c" | grep -qE '(^|/)\.env$' && fail "origin has commit ${c:0:7} that contains .env"
done
echo "the hotfix is on main and origin/main, next to the rate limit"
