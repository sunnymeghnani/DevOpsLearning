#!/bin/bash
# Reference fix for room 19 (tests only). Nothing is applied: the lab has no CAP_NET_ADMIN.
set -euo pipefail
NIC=$(ls /sys/class/net | grep -v '^lo$' | head -1)
MAC=$(cat "/sys/class/net/$NIC/address")
echo "ANSWER q2=$NIC"
# t1: read what netplan would generate; the later file (50-…) wins dhcp4.
netplan get ethernets.eno1.dhcp4 2>/dev/null | grep -qx true
netplan generate </dev/null 2>/dev/null
grep -q '^DHCP=ipv4' /run/systemd/network/10-netplan-eno1.network
echo "ANSWER q1=$(grep -l 'dhcp4: true' /etc/netplan/*.yaml | xargs -n1 basename)"
# t2: stop cloud-init from rewriting its file, move it aside, match the new NIC by MAC.
echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
mv /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.disabled
echo "ANSWER q3=$(sed -n 's|^# /etc/cloud/cloud.cfg.d/\([^ ]*\) with.*|\1|p' /etc/netplan/50-cloud-init.yaml.disabled)"
# t3: default route with routes: instead of gateway4.
echo "ANSWER q4=$(sed -n 's/^DEFAULT_INPUT_TIMEOUT = //p' /usr/share/netplan/netplan_cli/cli/commands/try_command.py)"
cat > /etc/netplan/01-static.yaml <<YAML
# web-04 static address (ticket NET-212, HW-0931)
network:
  version: 2
  renderer: networkd
  ethernets:
    lan0:
      match:
        macaddress: "$MAC"
      set-name: lan0
      dhcp4: false
      addresses: [192.0.2.10/24]
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53]
        search: [example.com]
YAML
chmod 600 /etc/netplan/01-static.yaml
rm -rf /run/systemd/network
netplan generate </dev/null 2>/dev/null
ls /run/systemd/network
