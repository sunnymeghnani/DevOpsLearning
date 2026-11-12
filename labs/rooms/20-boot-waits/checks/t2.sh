#!/bin/bash
# t2: netplan marks ens19 (no cable) optional, keeps its config, and still requires the uplink ens18.
fail() { echo "$1"; exit 1; }
shopt -s nullglob
for f in /etc/netplan/*.yaml; do
  m=$(stat -c %a "$f"); [ $((8#$m & 8#077)) -eq 0 ] || fail "$f is mode $m: netplan files must be 600"
done
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
mkdir -p "$T/etc"; cp -a /etc/netplan "$T/etc/"
err=$(/usr/libexec/netplan/generate --root-dir "$T" 2>&1 </dev/null) || fail "netplan generate fails: $(grep -m1 -iE 'error|invalid' <<< "$err")"
get() { netplan get "$1" 2>/dev/null </dev/null; }
[ "$(get ethernets.ens19.optional)" = true ] || fail "ens19 is not optional: wait-online keeps waiting for a link with no cable"
get ethernets.ens19.addresses | grep -q '198.51.100.20/24' || fail "ens19 lost its address config: keep it for when the new NAS is cabled"
[ "$(get ethernets.ens18.dhcp4)" = true ] || fail "the uplink ens18 must keep dhcp4: true"
[ "$(get ethernets.ens18.optional)" = true ] && fail "the uplink ens18 is optional too: then nothing waits for the network that services need"
echo "ens19 is optional (keeps 198.51.100.20/24); boot still waits for the uplink ens18"
