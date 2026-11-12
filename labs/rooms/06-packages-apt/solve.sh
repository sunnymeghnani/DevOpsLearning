#!/bin/bash
# Reference fix for room 06 (tests only).
set -euo pipefail
apt-get install -s app-agent >/dev/null 2>&1 || true        # E: dpkg was interrupted ...
# t1: finish the interrupted configuration; it fails and names the failing script and the cause.
out=$(dpkg --configure -a 2>&1 || true)
echo "ANSWER q2=$(sed -n 's/.*installed app-agent package \([a-z-]*\) script subprocess.*/\1/p' <<< "$out" | head -1 | sed 's/post-installation/postinst/')"
sed -i 's/^sever = /server = /' /etc/app-agent/agent.conf
dpkg --configure -a
apt-get check
# t2: keep the recalled 1.1 out of the next upgrade.
echo "ANSWER q4=$(apt-cache policy app-agent | sed -n 's/^ *Candidate: //p')"
apt-mark hold app-agent
apt-mark showhold
