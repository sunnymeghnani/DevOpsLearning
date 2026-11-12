#!/bin/bash
# t1: `netplan generate` has run on the current YAML: its networkd files in /run/systemd/network are up to date.
fail() { echo "$1"; exit 1; }
shopt -s nullglob
yaml=(/etc/netplan/*.yaml)
gen=(/run/systemd/network/10-netplan-*)
[ ${#yaml[@]} -gt 0 ] || fail "/etc/netplan has no .yaml files any more"
[ ${#gen[@]} -gt 0 ] || fail "nothing generated in /run/systemd/network yet: run sudo netplan generate (it applies nothing)"
newest_yaml=$(stat -c %Y "${yaml[@]}" | sort -n | tail -1)
oldest_gen=$(stat -c %Y "${gen[@]}" | sort -n | head -1)
[ "$oldest_gen" -ge "$newest_yaml" ] || fail "the YAML changed after the last netplan generate: run it again"
echo "netplan generate wrote ${#gen[@]} file(s) to /run/systemd/network from the current YAML"
