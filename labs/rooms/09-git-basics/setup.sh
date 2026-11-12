#!/bin/bash
# Room 09 (git-basics): a push blocked by secret scanning, and a hotfix lost on a detached HEAD.
# Broken state (repo /home/deploy/shop, origin /srv/git/shop.git, all owned by deploy):
#  - the newest local commit "Add rate limiting" also added .env with a database password; origin's pre-receive
#    hook refuses any push containing .env;
#  - a hotfix (proxy_read_timeout 30s) was committed on a detached HEAD (tag v1.4) and left behind: only the reflog
#    still knows it.
set -euo pipefail

id deploy >/dev/null 2>&1 || useradd -m -s /bin/bash deploy
rm -rf /srv/git/shop.git /home/deploy/shop
install -d -o deploy -g deploy /srv/git
cat > /home/deploy/.gitconfig <<'EOF'
[user]
	name = Deploy Bot
	email = deploy@example.com
[init]
	defaultBranch = main
[advice]
	detachedHead = true
EOF
chown deploy:deploy /home/deploy/.gitconfig

runuser -u deploy -- bash -euo pipefail <<'AS_DEPLOY'
export GIT_AUTHOR_DATE GIT_COMMITTER_DATE
at() { GIT_AUTHOR_DATE="$1"; GIT_COMMITTER_DATE="$1"; }
git init -q --bare /srv/git/shop.git
cat > /srv/git/shop.git/hooks/pre-receive <<'HOOK'
#!/bin/bash
# pre-receive: refuse pushes that contain secret files (.env), like a hosted "push protection".
zero=0000000000000000000000000000000000000000
status=0
while read -r old new ref; do
  [ "$new" = "$zero" ] && continue
  if [ "$old" = "$zero" ]; then commits=$(git rev-list "$new" --not --all); else commits=$(git rev-list "$old..$new"); fi
  for c in $commits; do
    if git ls-tree -r --name-only "$c" | grep -qE '(^|/)\.env$'; then
      echo "error: push declined: commit ${c:0:7} on $ref contains .env (secrets must not be committed)" >&2
      echo "hint: remove the file from that commit, ignore it, push again" >&2
      status=1; break
    fi
  done
done
exit $status
HOOK
chmod 755 /srv/git/shop.git/hooks/pre-receive

git clone -q /srv/git/shop.git /home/deploy/shop 2>/dev/null
cd /home/deploy/shop
printf 'listen=8080\nworkers=4\n' > app.conf
printf 'proxy_read_timeout 10s;\n' > timeout.conf
printf '# shop config\nDeployed by CI from this repository.\n' > README.md
at "2026-10-12T09:00:00+00:00"; git add -A; git commit -q -m "Initial shop config"
printf 'health_path=/healthz\n' >> app.conf
at "2026-10-14T11:20:00+00:00"; git commit -q -am "Add healthcheck endpoint"
git tag v1.4
git push -q origin main --tags 2>/dev/null

# 2026-10-18, night: hotfix made on the checked-out tag (detached HEAD), then left behind
git checkout -q v1.4 2>/dev/null
printf 'proxy_read_timeout 30s;\n' > timeout.conf
at "2026-10-18T23:41:00+00:00"; git commit -q -am "hotfix: raise proxy_read_timeout to 30s (INC-977)"
git checkout -q main 2>/dev/null

# 2026-10-20: rate limiting, plus the local secrets file by accident
printf 'rate_limit=100\n' >> app.conf
printf 'DB_HOST=10.0.30.5\nDB_USER=shop\nDB_PASSWORD=S3cr3t-shop-2026\n' > .env
at "2026-10-20T08:55:00+00:00"; git add -A; git commit -q -m "Add rate limiting"
git push -q origin main 2>/dev/null || true      # rejected by the hook
AS_DEPLOY
