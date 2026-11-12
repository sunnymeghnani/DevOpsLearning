#!/bin/bash
# Reference fix for room 03 (tests only).
set -euo pipefail
# t1: map the new name to the loopback alias Ubuntu uses for the machine's own name.
grep -q 'app-prod-01' /etc/hosts || echo '127.0.1.1 app-prod-01' >> /etc/hosts
getent hosts app-prod-01
# t2: sudo ignores drop-ins whose name contains "." or ends in "~": rename, then validate.
mv /etc/sudoers.d/deploy.conf /etc/sudoers.d/deploy
visudo -c -f /etc/sudoers.d/deploy
sudo -l -U deploy
su -s /bin/bash deploy -c /opt/ci/post-deploy.sh </dev/null
