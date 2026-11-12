#!/bin/bash
# t2: cloud-init's network config is disabled, and the generated networkd config matches the LIVE NIC by MAC,
# renames it (set-name), and is static (no DHCP) with 192.0.2.10/24. Generated into a scratch root: nothing applied.
fail() { echo "$1"; exit 1; }
shopt -s nullglob
NIC=$(ls /sys/class/net | grep -v '^lo$' | head -1)
MAC=$(cat "/sys/class/net/$NIC/address")
OLD_MAC=3c:ec:ef:12:34:56
python3 - <<'PY' || fail "cloud-init would rewrite 50-cloud-init.yaml: no /etc/cloud/cloud.cfg.d/*.cfg sets network: {config: disabled}"
import glob, sys, yaml
for f in glob.glob("/etc/cloud/cloud.cfg.d/*.cfg"):
    try:
        d = yaml.safe_load(open(f)) or {}
    except Exception:
        continue
    if isinstance(d, dict) and isinstance(d.get("network"), dict) and d["network"].get("config") == "disabled":
        sys.exit(0)
sys.exit(1)
PY
for f in /etc/netplan/*.yaml; do
  m=$(stat -c %a "$f"); [ $((8#$m & 8#077)) -eq 0 ] || fail "$f is mode $m: netplan files must be 600 (they can hold secrets)"
done
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/etc" "$T/run" "$T/lib"
cp -a /etc/netplan "$T/etc/"; [ -d /run/netplan ] && cp -a /run/netplan "$T/run/"; [ -d /lib/netplan ] && cp -a /lib/netplan "$T/lib/"
err=$(/usr/libexec/netplan/generate --root-dir "$T" 2>&1 </dev/null) || fail "netplan generate fails: $(grep -m1 -iE 'error|invalid' <<< "$err")"
nets=("$T"/run/systemd/network/*.network)
[ ${#nets[@]} -gt 0 ] || fail "the YAML generates no .network file at all"
mine=$(grep -il "MACAddress=$MAC" "${nets[@]}" </dev/null)
[ -n "$mine" ] || fail "no generated .network matches the live NIC $NIC by its MAC ($MAC): match: macaddress:"
[ "$(wc -l <<< "$mine")" -eq 1 ] || fail "more than one generated .network matches the live NIC's MAC"
for f in "${nets[@]}"; do
  if grep -qi "MACAddress=$OLD_MAC" "$f" || { grep -qx 'Name=eno1' "$f" && ! grep -qi 'MACAddress=' "$f"; }; then
    fail "a config for the old NIC (eno1 / $OLD_MAC) is still generated ($(basename "$f")): which YAML still defines it?"
  fi
done
links=("$T"/run/systemd/network/*.link)
link=""; [ ${#links[@]} -gt 0 ] && link=$(grep -il "MACAddress=$MAC" "${links[@]}" </dev/null)
[ -n "$link" ] && grep -q '^Name=' "$link" || fail "the live NIC is matched but not renamed: add set-name: so its name stops depending on the slot"
grep -qiE '^DHCP=(ipv4|yes|true|both)' "$mine" && fail "DHCP is still on for the live NIC: a later file (by name) wins the merge"
grep -qx 'Address=192.0.2.10/24' "$mine" || fail "the live NIC's generated config has no Address=192.0.2.10/24"
echo "the live NIC ($MAC) gets a static 192.0.2.10/24 as $(sed -n 's/^Name=//p' "$link"); cloud-init network config is disabled"
