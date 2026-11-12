#!/bin/bash
# Reference fix for room 09 (tests only). Runs git as deploy.
set -euo pipefail
runuser -u deploy -- bash -euo pipefail <<'AS_DEPLOY'
cd /home/deploy/shop
git push origin main 2>&1 | grep -q 'push declined' || true
# t1: take .env out of the last (unpushed) commit, keep the file, ignore it, push.
git rm -q --cached .env
echo '.env' >> .gitignore
git add .gitignore
git commit -q --amend --no-edit
git push -q origin main
# t2: the reflog remembers the commit made on the detached HEAD; bring it onto main.
sha=$(git reflog --format='%h %gs %s' | awk '/hotfix: raise proxy_read_timeout/ {print $1; exit}')
git cherry-pick "$sha" >/dev/null
git push -q origin main
git log --oneline -4
AS_DEPLOY
