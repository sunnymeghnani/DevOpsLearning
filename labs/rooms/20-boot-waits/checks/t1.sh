#!/bin/bash
# t1: the swap line for the detached disk stays (the disk comes back) but no longer holds the boot:
# nofail + a short x-systemd.device-timeout; findmnt --verify shows nothing else wrong and systemd has re-read fstab.
fail() { echo "$1"; exit 1; }
U=3f1c9a2e-5b7d-4e0a-9c61-2d8f4b7a1e90
line=$(grep -E "^[[:space:]]*UUID=$U[[:space:]]" /etc/fstab)
[ -n "$line" ] || fail "the swap line for UUID=$U is gone: the disk is re-attached next week, keep it (with options)"
[ "$(wc -l <<< "$line")" -eq 1 ] || fail "UUID=$U appears on more than one active fstab line"
read -r _ _ _ opts _ <<< "$line"
[[ ",$opts," == *,nofail,* ]] || fail "the swap line has no nofail: boot still waits for the device (options: $opts)"
t=$(grep -oE 'x-systemd\.device-timeout=[^,]+' <<< "$opts" | cut -d= -f2)
[ -n "$t" ] || fail "nofail alone still waits the default 90 s for the device: add x-systemd.device-timeout="
secs=$(systemd-analyze timespan "$t" 2>/dev/null | sed -n 's/^ *μs: *//p')
[ -n "$secs" ] || fail "x-systemd.device-timeout=$t is not a time span systemd understands"
[ "$secs" -gt 0 ] && [ "$secs" -le 30000000 ] || fail "x-systemd.device-timeout=$t: use 1-30 seconds, not longer"
out=$(findmnt --verify 2>&1)
grep -qE '^0 parse errors' <<< "$out" || fail "findmnt --verify: $(grep -m1 'parse error' <<< "$out")"
grep -q 'daemon-reload' <<< "$out" && fail "fstab changed but systemd still uses the old version: sudo systemctl daemon-reload"
other=$(grep '\[E\]' <<< "$out" | grep -v "unreachable on boot required source: UUID=$U")
[ -z "$other" ] || fail "findmnt --verify reports another error: $(head -1 <<< "$other" | sed 's/^ *//')"
echo "the swap line keeps the disk but waits at most $t (nofail); findmnt --verify shows no other error"
