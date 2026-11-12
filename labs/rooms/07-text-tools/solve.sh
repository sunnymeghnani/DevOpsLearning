#!/bin/bash
# Reference fix for room 07 (tests only). The answers are derived from the logs with the tools taught here.
set -euo pipefail
LOG=/var/log/incident/access-2026-10-20.log
JSON=/var/log/incident/app-2026-10-20.json
# t1: 5xx per minute -> first minute with a jump; user agent with most 5xx; its addresses.
awk '$9 ~ /^5/ {print substr($4, 14, 5)}' "$LOG" | sort | uniq -c > /tmp/per-minute.txt
echo "ANSWER q1=$(awk '$1 >= 10 {print $2; exit}' /tmp/per-minute.txt)"
ua=$(awk -F'"' '$3 ~ /^ 5/ {print $6}' "$LOG" | sort | uniq -c | sort -rn | head -1 | sed 's/^ *[0-9]* //')
echo "ANSWER q2=$(grep -o 'DocHarvester/[0-9.]*' <<< "$ua")"
grep -F 'DocHarvester/' "$LOG" | awk '{print $1}' | sort -u > /srv/incident/docharvester-ips.txt
# t2: request count, top error message (jq), then block the user agent in nginx.
echo "ANSWER q3=$(grep -c 'DocHarvester/' "$LOG")"
echo "ANSWER q4=$(jq -r 'select(.level == "error") | .msg' "$JSON" | sort | uniq -c | sort -rn | head -1 | sed 's/^ *[0-9]* //')"
cat > /etc/nginx/conf.d/block-crawlers.conf <<'EOF'
# INC-2026-10-20: DocHarvester rotates IPs, so block it by user agent
map $http_user_agent $blocked_ua {
    default          0;
    ~*DocHarvester   1;
}
EOF
sed -i 's|^    index index.html;$|    index index.html;\n    if ($blocked_ua) { return 403; }|' /etc/nginx/sites-available/docs
nginx -t
systemctl reload nginx
