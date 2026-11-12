#!/bin/bash
# t2: deploy may run exactly "systemctl restart nginx" without a password, and nothing else.
fail() { echo "$1"; exit 1; }
visudo -c -q >/dev/null 2>&1 || fail "visudo -c reports a sudoers syntax error"
for f in /etc/sudoers.d/*; do
  [ -f "$f" ] || continue
  [ "$(stat -c '%U %a' "$f")" = "root 440" ] || fail "$f should be owned by root with mode 0440"
done
id -nG deploy | tr ' ' '\n' | grep -qxE 'sudo|admin|wheel' && fail "deploy is in an admin group: that is full root, not least privilege"
out=$(su -s /bin/bash deploy -c 'sudo -n /usr/bin/systemctl restart nginx' </dev/null 2>&1) \
  || fail "deploy cannot run 'sudo -n systemctl restart nginx': ${out##*$'\n'}"
for cmd in "/usr/bin/id" "/usr/bin/systemctl stop nginx" "/usr/bin/bash" "/usr/bin/systemctl restart ssh"; do
  sudo -n -l -U deploy $cmd >/dev/null 2>&1 && fail "deploy may also run '$cmd': grant only the restart"
done
systemctl is-active -q nginx || fail "nginx is not running"
echo "deploy may restart nginx without a password, and nothing else"
