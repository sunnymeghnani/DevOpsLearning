#!/bin/bash
# Reference fix for room 20 (tests only).
set -euo pipefail
D=/home/lab/boot-2026-11-09
# t1: the journal shows the 1min 30s device job; keep the line, stop it holding the boot.
grep -q 'start timed out' "$D/journal.txt"
echo "ANSWER q1=$(grep -oE '\(30s / [0-9]+min [0-9]+s\)' "$D/journal.txt" | head -1 | sed -E 's/.*\/ ([0-9]+)min ([0-9]+)s\)/\1 \2/' | awk '{print $1*60+$2}')"
sed -i -E 's/^(UUID=3f1c9a2e-5b7d-4e0a-9c61-2d8f4b7a1e90 none swap )sw /\1sw,nofail,x-systemd.device-timeout=10s /' /etc/fstab
systemctl daemon-reload
findmnt --verify || true          # only the known missing source remains
# t2: the unit at the top of blame; mark the cable-less NIC optional.
echo "ANSWER q2=$(head -1 "$D/blame.txt" | awk '{print $NF}')"
sed -i 's|^      addresses: \[198.51.100.20/24\]|      optional: true\n      addresses: [198.51.100.20/24]|' /etc/netplan/01-netcfg.yaml
netplan get ethernets.ens19
echo "ANSWER q3=--any"
