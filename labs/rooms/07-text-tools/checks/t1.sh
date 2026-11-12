#!/bin/bash
# t1: the evidence file lists exactly the crawler's client addresses, one per line, without duplicates.
fail() { echo "$1"; exit 1; }
F=/srv/incident/docharvester-ips.txt
LOG=/var/log/incident/access-2026-10-20.log
[ -s "$F" ] || fail "$F is missing or empty"
want=$(grep -F 'DocHarvester/' "$LOG" | awk '{print $1}' | sort -u)
have=$(tr -d ' \t\r' < "$F" | grep -v '^$' | sort)
dups=$(uniq -d <<< "$have" | head -1)
[ -z "$dups" ] || fail "$F lists $dups more than once"
missing=$(comm -23 <(echo "$want") <(echo "$have") | wc -l)
extra=$(comm -13 <(echo "$want") <(echo "$have") | head -1)
[ -z "$extra" ] || fail "$F contains $extra, which never sent the crawler's user agent"
[ "$missing" -eq 0 ] || fail "$F is missing $missing of the crawler's addresses"
echo "$F lists all $(wc -l <<< "$want") crawler addresses"
