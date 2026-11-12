#!/bin/bash
# t2: report-export uses a fully qualified name that resolves to the API (no search-list guess), and its run succeeds.
fail() { echo "$1"; exit 1; }
url=$(sed -nE 's/^[[:space:]]*API_URL=//p' /etc/report-export.conf | tail -1 | tr -d "\"'")
[ -n "$url" ] || fail "/etc/report-export.conf has no API_URL="
host=${url#*://}; host=${host%%[:/]*}
[[ "$host" == *.* ]] || fail "report-export still uses the short name '$host': it depends on the search list"
[ "${host%.}" = api.internal.example.com ] || fail "report-export points at $host, not the orders API (api.internal.example.com)"
grep -qE '^search[[:space:]]+example\.com[[:space:]]*$' /etc/resolv.conf || fail "leave the search list in /etc/resolv.conf as it was: other jobs on this box rely on it"
got=$(getent ahostsv4 "$host" | awk 'NR==1{print $1}')
[ "$got" = 127.0.10.20 ] || fail "$host resolves to ${got:-nothing}, not the API at 127.0.10.20"
systemctl reset-failed report-export.service >/dev/null 2>&1
systemctl start report-export.service >/dev/null 2>&1 </dev/null || fail "report-export fails: $(journalctl -u report-export -n 5 --no-pager -o cat | grep -m1 -E 'curl|report-export:')"
echo "report-export uses $host -> 127.0.10.20 and its run succeeds"
