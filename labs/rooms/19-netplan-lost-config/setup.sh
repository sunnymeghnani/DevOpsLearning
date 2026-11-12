#!/bin/bash
# Room 19 (ubuntu-netconfig): a server that lost its network config after a mainboard swap. Config level only:
# the lab has no CAP_NET_ADMIN, so nothing is applied; the learner reads what `netplan generate` would hand to
# systemd-networkd (/run/systemd/network) and fixes the YAML until the generated files are right.
# Broken state:
#  - 01-static.yaml sets the static address for "eno1", but 50-cloud-init.yaml (left by the installer) sorts
#    later and turns dhcp4 back on for the same interface;
#  - cloud-init's file matches the OLD NIC's MAC and renames it eno1: after the swap the live NIC (eth0 here)
#    matches nothing, so no config at all would apply to it;
#  - the static file has no default route: someone deleted the deprecated gateway4 line and never added routes:.
set -euo pipefail

OLD_MAC=3c:ec:ef:12:34:56          # the NIC on the old mainboard (gone)

# clean slate (idempotent)
mkdir -p /etc/netplan /etc/cloud/cloud.cfg.d
rm -f /etc/netplan/*.yaml /etc/netplan/*.yaml.* /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
rm -rf /run/netplan /run/systemd/network /run/udev/rules.d/*netplan* \
       /run/systemd/system/systemd-networkd-wait-online.service.d/10-netplan.conf

# what the installer's cloud-init wrote on first boot (the old NIC, DHCP)
cat > /etc/netplan/50-cloud-init.yaml <<YAML
# This file is generated from information provided by the datasource.  Changes
# to it will not persist across an instance reboot.  To disable cloud-init's
# network configuration capabilities, write a file
# /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg with the following:
# network: {config: disabled}
network:
    ethernets:
        eno1:
            dhcp4: true
            match:
                macaddress: ${OLD_MAC}
            set-name: eno1
    version: 2
YAML

# the admin's static config (written after install, never worked as intended)
cat > /etc/netplan/01-static.yaml <<'YAML'
# web-04 static address (ticket NET-212)
# 2026-11-03: removed "gateway4: 192.0.2.1", netplan warns it is deprecated. TODO: routes
network:
  version: 2
  renderer: networkd
  ethernets:
    eno1:
      dhcp4: false
      addresses: [192.0.2.10/24]
      nameservers:
        addresses: [192.0.2.53]
        search: [example.com]
YAML
chmod 600 /etc/netplan/*.yaml

cat > /etc/cloud/cloud.cfg.d/90_dpkg.cfg <<'CFG'
# to update this file, run dpkg-reconfigure cloud-init
datasource_list: [ NoCloud, None ]
CFG

# the hardware ticket, for the learner
cat > /home/lab/HW-CHANGE.txt <<TXT
HW-0931  web-04  2026-11-09
Mainboard replaced (onboard NIC failed). Old onboard NIC: eno1, MAC ${OLD_MAC}.
The new board's NIC is the only Ethernet port. Same switch port, same cable.
After the swap: no address on the console. Static IP must be 192.0.2.10/24, gateway 192.0.2.1, DNS 192.0.2.53.
TXT
chown lab:lab /home/lab/HW-CHANGE.txt
