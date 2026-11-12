# 13 — Kernel, Boot & Hardware

Typical tasks: identify the system, tune kernel parameters, check limits,
diagnose hardware (on-prem), inspect modules, boot issues.

---

## 1. System identification

```bash
uname -a                          # kernel version + arch
uname -r                          # kernel release only
cat /etc/os-release               # distro + version (portable way)
hostnamectl                       # hostname, OS, kernel, virtualization type ★
                                  #   "Virtualization: kvm/xen/vmware" vs bare metal
lscpu                             # CPU model, cores, sockets, NUMA, flags
arch                              # x86_64 / aarch64 (Graviton!)
uptime -s                         # up since when
systemd-detect-virt               # what hypervisor (kvm, xen, amazon, none)
dmidecode -s system-product-name  # hardware model / cloud instance hints
dmidecode -t memory | grep -E "Size|Speed" | sort | uniq -c   # DIMM inventory (on-prem)
```

## 2. Kernel parameters (sysctl)

```bash
sysctl -a 2>/dev/null | less              # everything
sysctl vm.swappiness                      # read one
sysctl -w vm.swappiness=10                # set until reboot
echo "vm.swappiness=10" >> /etc/sysctl.d/99-tuning.conf && sysctl --system  # persist
sysctl --system                           # reload all config files
```

Frequently-tuned parameters in incidents:
```bash
fs.file-max                               # system-wide fd limit
net.core.somaxconn                        # accept queue (listen backlog)
net.ipv4.ip_local_port_range              # ephemeral ports
net.ipv4.tcp_tw_reuse                     # TIME_WAIT reuse for outbound
net.netfilter.nf_conntrack_max            # conntrack table size
vm.max_map_count                          # needed by Elasticsearch etc.
vm.overcommit_memory                      # Redis wants 1
net.ipv4.ip_forward                       # must be 1 on routers/NAT/K8s nodes
kernel.pid_max ; kernel.threads-max
```

## 3. Resource limits (ulimit)

```bash
ulimit -a                                 # limits of current shell
ulimit -n 65535                           # raise fd limit for this shell
cat /proc/1234/limits                     # limits of a RUNNING process ★ (the truth)
cat /etc/security/limits.conf ; ls /etc/security/limits.d/   # PAM limits (login sessions)
systemctl show app -p LimitNOFILE         # systemd services use unit-file limits,
                                          #   NOT limits.conf!
```

## 4. Kernel modules & drivers

```bash
lsmod                                     # loaded modules
modinfo ena                               # module details (e.g. AWS ENA NIC driver)
modprobe module ; modprobe -r module      # load / unload
dmesg -T | grep -i firmware               # missing firmware complaints
ls /etc/modprobe.d/                       # blacklists/options
lspci -k                                  # PCI devices + which driver claimed each ★
lsusb                                     # USB devices
lshw -short 2>/dev/null                   # overall hardware summary
```

## 5. Boot & GRUB

```bash
cat /proc/cmdline                         # parameters the kernel booted with
ls /boot                                  # installed kernels (also: /boot full = failed
                                          #   kernel updates → clean old kernels)
grubby --default-kernel                   # RHEL: default boot kernel
grep -E "^GRUB_CMDLINE" /etc/default/grub # then: update-grub / grub2-mkconfig -o ...
journalctl -b -1 -e                       # end of previous boot — why did it die? ★
last -x shutdown reboot | head            # clean shutdowns vs crashes
```
Crash without shutdown entry = power loss, panic, or hard hang.
Kernel crash dumps (if kdump configured): `ls /var/crash/`.

Emergency/rescue: boot with `systemd.unit=rescue.target` (or `emergency.target`)
appended to the kernel line in GRUB; single-user password reset with `init=/bin/bash`.

## 6. Hardware health (on-premise)

```bash
sensors                                   # temperatures/fans (lm-sensors)
ipmitool sensor ; ipmitool sel list       # BMC sensors + hardware event log ★
                                          #   (ECC errors, PSU failures, fan failures)
ipmitool chassis status
mcelog ; grep -i "machine check" /var/log/messages   # CPU/memory machine-check errors
dmesg -T | grep -iE "ecc|mce|thermal"
smartctl -a /dev/sda                      # disk health (01-storage-disk.md)
# RAID controllers (vendor tools): storcli /c0 show all   (Broadcom/LSI)
#                                  perccli /c0 show       (Dell PERC)
#                                  ssacli ctrl all show config   (HPE)
free -h vs dmidecode -t memory            # OS sees less RAM than installed? failed DIMM
```

## 7. Virtualization/cloud detection oddities

```bash
systemd-detect-virt                       # "amazon"/"kvm"/"xen"/"vmware"/"none"
dmesg | grep -i hypervisor
cat /sys/hypervisor/uuid 2>/dev/null      # xen-based EC2
# EC2 Nitro instances: EBS volumes appear as /dev/nvme*; map to attachment names:
nvme list
nvme id-ctrl -v /dev/nvme1n1 | grep -a xvd   # shows the console device name (e.g. xvdf)
lsblk -o NAME,SERIAL                      # NVMe serial = EBS volume-id (vol...)
```

## 8. Core dumps & panics

```bash
coredumpctl list                          # recent crashes (systemd-coredump)
coredumpctl info 1234                     # details incl. signal & stack
coredumpctl gdb 1234                      # open the dump in gdb
ulimit -c                                 # 0 = core dumps disabled for this shell
cat /proc/sys/kernel/core_pattern         # where cores go (may pipe to systemd/apport)
sysctl kernel.panic kernel.panic_on_oops  # auto-reboot behavior after panic
```
