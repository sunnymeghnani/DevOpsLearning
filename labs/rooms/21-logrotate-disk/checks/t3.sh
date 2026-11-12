#!/bin/bash
# t3: the effective journald config caps the persistent journal at 500M or less, and the running journald uses it.
fail() { echo "$1"; exit 1; }
cfg=$(systemd-analyze cat-config systemd/journald.conf 2>/dev/null </dev/null)
val=$(grep -E '^[[:space:]]*SystemMaxUse=' <<< "$cfg" | tail -1 | cut -d= -f2 | tr -d ' ')
[ -n "$val" ] || fail "no SystemMaxUse= in the effective journald config"
bytes=$(numfmt --from=iec "${val%B}" 2>/dev/null) || fail "SystemMaxUse=$val is not a size journald understands"
[ "$bytes" -le $((500 * 1024 * 1024)) ] || fail "the last SystemMaxUse= wins, and it is $val: cap it at 500M or less"
grep -E '^[[:space:]]*Storage=' <<< "$cfg" | tail -1 | grep -qE '=(persistent|auto)' || fail "keep the journal persistent (the team wants logs across reboots)"
pid=$(systemctl show -p MainPID --value systemd-journald)
line=$(journalctl -u systemd-journald --no-pager -o cat _PID="$pid" 2>/dev/null </dev/null | grep 'System Journal' | tail -1)
[ -n "$line" ] || fail "the running journald has not reported its system journal: restart it after the change"
max=$(sed -nE 's/.*, max ([0-9.]+)([KMGT]?)B?, .*/\1 \2/p' <<< "$line")
mb=$(awk -v n="${max% *}" -v u="${max#* }" 'BEGIN{m=(u=="K")?1/1024:(u=="M")?1:(u=="G")?1024:(u=="T")?1048576:1/1048576; printf "%d", n*m}')
[ "$mb" -gt 0 ] && [ "$mb" -le 500 ] || fail "the running journald still uses: $line (restart systemd-journald)"
echo "journald runs with SystemMaxUse=$val: $line"
