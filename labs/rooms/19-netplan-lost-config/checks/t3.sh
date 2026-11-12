#!/bin/bash
# t3: the live NIC's generated config has a default route via 192.0.2.1, written with routes: (no gateway4), and keeps DNS.
fail() { echo "$1"; exit 1; }
shopt -s nullglob
NIC=$(ls /sys/class/net | grep -v '^lo$' | head -1)
MAC=$(cat "/sys/class/net/$NIC/address")
grep -qE '^[[:space:]]*gateway4:' /etc/netplan/*.yaml 2>/dev/null && fail "gateway4 is deprecated: use routes: with to: default"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/etc" "$T/run" "$T/lib"
cp -a /etc/netplan "$T/etc/"; [ -d /run/netplan ] && cp -a /run/netplan "$T/run/"; [ -d /lib/netplan ] && cp -a /lib/netplan "$T/lib/"
err=$(/usr/libexec/netplan/generate --root-dir "$T" 2>&1 </dev/null) || fail "netplan generate fails: $(grep -m1 -iE 'error|invalid' <<< "$err")"
nets=("$T"/run/systemd/network/*.network)
[ ${#nets[@]} -gt 0 ] || fail "the YAML generates no .network file at all"
mine=$(grep -il "MACAddress=$MAC" "${nets[@]}" </dev/null | head -1)
[ -n "$mine" ] || fail "no generated .network matches the live NIC's MAC yet (task 2)"
awk '/^\[Route\]/{r=1;next} /^\[/{r=0} r&&/^Gateway=192\.0\.2\.1$/{g=1} r&&/^Destination=(0\.0\.0\.0\/0|default)$/{d=1} END{exit !(g&&d)}' "$mine" \
  || fail "no default route via 192.0.2.1 in the live NIC's generated config ([Route] Gateway=, Destination=0.0.0.0/0)"
grep -qx 'DNS=192.0.2.53' "$mine" || fail "the DNS server 192.0.2.53 went missing from the live NIC's config"
echo "the live NIC's config has default via 192.0.2.1 and DNS 192.0.2.53 (routes:, no gateway4)"
