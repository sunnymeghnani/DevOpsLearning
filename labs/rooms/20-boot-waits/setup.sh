#!/bin/bash
# Room 20 (kernel-boot): boot takes 3.5 minutes. Config level only (a container never boots through fstab or
# wait-online), with the recorded output of the slow boot in ~/boot-2026-11-09/.
# Broken state:
#  - /etc/fstab still has a swap partition on a disk that was detached (UUID not present): systemd waits the
#    default 90 s for the device on every boot;
#  - netplan requires ens19 (storage NIC, cable pulled when the old NAS was retired): systemd-networkd-wait-online
#    waits for it until its 120 s timeout.
set -euo pipefail
U=3f1c9a2e-5b7d-4e0a-9c61-2d8f4b7a1e90
E='dev-disk-by\x2duuid-3f1c9a2e\x2d5b7d\x2d4e0a\x2d9c61\x2d2d8f4b7a1e90'

cat > /etc/fstab <<FSTAB
# /etc/fstab: static file system information.
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
# / is on the root volume (managed by the image)
# swap on the second virtual disk (sdb1), added 2025-04 by INFRA-311
UUID=$U none swap sw 0 0
FSTAB
systemctl daemon-reload            # systemd has read this version: an edit without a reload shows in findmnt --verify

mkdir -p /etc/netplan
rm -f /etc/netplan/*.yaml
cat > /etc/netplan/01-netcfg.yaml <<'YAML'
# app-02 (provisioned 2025-03)
network:
  version: 2
  renderer: networkd
  ethernets:
    ens18:                       # uplink
      dhcp4: true
    ens19:                       # storage network to nas-01 (198.51.100.0/24)
      addresses: [198.51.100.20/24]
YAML
chmod 600 /etc/netplan/01-netcfg.yaml

# what was recorded on the real app-02 during the slow boot (this container never boots that way)
D=/home/lab/boot-2026-11-09
rm -rf "$D"; mkdir -p "$D"
cat > "$D/README.txt" <<'TXT'
Recorded on app-02 after the reboot on 2026-11-09 (kernel patching), by the on-call engineer.
  systemd-analyze.txt      systemd-analyze
  blame.txt                systemd-analyze blame | head
  critical-chain.txt       systemd-analyze critical-chain
  journal.txt              journalctl -b -1 -p notice (excerpt)
  networkctl.txt           networkctl list
Since then: the second virtual disk (sdb) was detached during the storage migration INFRA-402
and will be re-attached next week. nas-01 was retired on 2026-10-30; its cable on ens19 was pulled.
TXT
cat > "$D/systemd-analyze.txt" <<'TXT'
Startup finished in 2.104s (kernel) + 3min 34.871s (userspace) = 3min 36.975s
graphical.target reached after 3min 34.802s in userspace.
TXT
cat > "$D/blame.txt" <<'TXT'
2min 418ms systemd-networkd-wait-online.service
    2.731s apt-daily-upgrade.service
    2.688s docker.service
    1.912s snapd.seeded.service
    1.204s cloud-init-local.service
     812ms systemd-journal-flush.service
     433ms systemd-udev-trigger.service
     251ms systemd-networkd.service
     187ms systemd-resolved.service
     102ms systemd-tmpfiles-setup.service
TXT
cat > "$D/critical-chain.txt" <<'TXT'
The time when unit became active or started is printed after the "@" character.
The time the unit took to start is printed after the "+" character.

graphical.target @3min 34.802s
└─multi-user.target @3min 34.801s
  └─docker.service @3min 32.112s +2.688s
    └─network-online.target @3min 32.090s
      └─systemd-networkd-wait-online.service @1min 31.668s +2min 418ms
        └─systemd-networkd.service @1min 31.402s +251ms
          └─network-pre.target @1min 31.390s
            └─cloud-init-local.service @1min 30.181s +1.204s
              └─basic.target @1min 30.170s
                └─sockets.target @1min 30.170s
                  └─snapd.socket @1min 30.161s +8ms
                    └─sysinit.target @1min 30.152s
                      └─systemd-update-utmp.service @1.012s +9ms
                        └─systemd-tmpfiles-setup.service @905ms +102ms
                          └─local-fs.target @901ms
                            └─system.slice @612ms
                              └─-.slice @612ms
TXT
cat > "$D/journal.txt" <<TXT
Nov 09 06:12:04 app-02 systemd[1]: Expecting device $E.device - /dev/disk/by-uuid/$U...
Nov 09 06:12:34 app-02 systemd[1]: A start job is running for /dev/disk/by-uuid/$U (30s / 1min 30s)
Nov 09 06:13:34 app-02 systemd[1]: $E.device: Job $E.device/start timed out.
Nov 09 06:13:34 app-02 systemd[1]: Timed out waiting for device $E.device - /dev/disk/by-uuid/$U.
Nov 09 06:13:34 app-02 systemd[1]: Dependency failed for $E.swap - /dev/disk/by-uuid/$U.
Nov 09 06:13:34 app-02 systemd[1]: $E.swap: Job $E.swap/start failed with result 'dependency'.
Nov 09 06:13:34 app-02 systemd[1]: Dependency failed for swap.target - Swaps.
Nov 09 06:13:34 app-02 systemd[1]: swap.target: Job swap.target/start failed with result 'dependency'.
Nov 09 06:13:35 app-02 systemd-networkd[598]: ens18: Gained carrier
Nov 09 06:13:35 app-02 systemd-networkd[598]: ens19: Link UP
Nov 09 06:13:35 app-02 systemd[1]: Starting systemd-networkd-wait-online.service - Wait for Network to be Configured...
Nov 09 06:13:36 app-02 systemd-networkd[598]: ens18: DHCPv4 address 192.0.2.31/24, gateway 192.0.2.1 acquired from 192.0.2.1
Nov 09 06:15:36 app-02 systemd-networkd-wait-online[612]: Timeout occurred while waiting for network connectivity.
Nov 09 06:15:36 app-02 systemd[1]: systemd-networkd-wait-online.service: Main process exited, code=exited, status=1/FAILURE
Nov 09 06:15:36 app-02 systemd[1]: systemd-networkd-wait-online.service: Failed with result 'exit-code'.
Nov 09 06:15:36 app-02 systemd[1]: Failed to start systemd-networkd-wait-online.service - Wait for Network to be Configured.
Nov 09 06:15:36 app-02 systemd[1]: Reached target network-online.target - Network is Online.
TXT
cat > "$D/networkctl.txt" <<'TXT'
IDX LINK  TYPE     OPERATIONAL SETUP
  1 lo    loopback carrier     unmanaged
  2 ens18 ether    routable    configured
  3 ens19 ether    no-carrier  configuring

3 links listed.
TXT
chown -R lab:lab "$D"
