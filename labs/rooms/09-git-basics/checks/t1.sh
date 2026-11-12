#!/bin/bash
# t1: the rate-limit change is on origin/main, no branch or tag (local or origin) has .env, .env is kept and ignored.
fail() { echo "$1"; exit 1; }
R=/home/deploy/shop
B=/srv/git/shop.git
g() { runuser -u deploy -- git -C "$1" "${@:2}" 2>/dev/null; }
has_env() {   # has_env REPO REVLIST-ARGS...: prints the first commit whose tree contains .env
  local repo=$1; shift
  for c in $(g "$repo" rev-list "$@"); do
    g "$repo" ls-tree -r --name-only "$c" | grep -qE '(^|/)\.env$' && { echo "${c:0:7}"; return 0; }
  done; return 1
}
[ -d "$R/.git" ] || fail "$R is not a git repository any more"
c=$(has_env "$B" --all) && fail "origin has commit $c that contains .env"
c=$(has_env "$R" --branches --tags) && fail "local commit $c (on a branch or tag) still contains .env"
g "$B" show main:app.conf | grep -q '^rate_limit=100$' || fail "origin/main does not have the rate limiting change yet (push it)"
grep -q '^DB_PASSWORD=' "$R/.env" 2>/dev/null || fail "$R/.env is gone: the app still needs it locally, only git must not track it"
src=$(cd "$R" && g "$R" check-ignore -v .env | cut -d: -f1)
[ "$src" = .gitignore ] || fail ".env is not ignored by the repository's .gitignore"
[ -n "$(g "$R" ls-files .gitignore)" ] || fail ".gitignore is not committed, so other clones would still pick up .env"
[ -z "$(g "$R" ls-files .env)" ] || fail ".env is still tracked in the index"
echo "origin/main has the rate limit, no commit carries .env, and .env stays local and ignored"
