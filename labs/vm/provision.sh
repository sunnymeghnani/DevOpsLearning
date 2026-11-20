#!/bin/bash
# Verify VM provisioning: the single source of truth for what the PREPARED image holds (labs/vm/README.md).
# vmctl.py `prepare` runs it ONCE, as root, inside a throwaway Ubuntu 24.04 cloud-image VM (never on the
# host), then powers the VM off and keeps its disk as the backing image for every later run. Changing this
# file (or the lab image's package list) changes the prepared-image hash, so the next run rebuilds it.
#
# vmctl.py prepends one line:  BASE_PACKAGES="..."  (parsed from the apt-get install in labs/base/Dockerfile,
# so the VM always has the same tools as the lab machine).
set -euo pipefail
: "${BASE_PACKAGES:?vmctl.py sets BASE_PACKAGES from labs/base/Dockerfile}"
export DEBIAN_FRONTEND=noninteractive

# Tools the handbook modules use that Ubuntu's archive has (on top of the lab image's list). Tools that are
# not in the archive (kubectl, aws, terraform, helm, ...) are reported as EXTERNAL instead.
EXTRA_PACKAGES=(
  command-not-found                      # package hints for MISSING commands
  docker.io docker-compose-v2 docker-buildx
  iotop nmap ethtool bridge-utils nftables ufw iptables conntrack ipset net-tools iputils-arping iputils-tracepath
  iperf3 socat telnet whois iftop nethogs vnstat iptraf-ng wireguard-tools tcptraceroute
  sysstat atop numactl ltrace gdb fio stress-ng sysbench wrk apache2-utils
  smartmontools lvm2 nfs-common mdadm xfsprogs nvme-cli hdparm pciutils usbutils dmidecode cryptsetup parted
  auditd apparmor-utils fail2ban debsums needrestart unattended-upgrades
  redis-tools mysql-client sqlite3 postgresql-contrib
  certbot haproxy rsync restic rclone borgbackup etcd-client ipmitool
  unzip zip zstd pv at tmux bc
)

APT=(apt-get -y -q -o DPkg::Lock::Timeout=600 -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)

echo "== waiting for cloud-init"
cloud-init status --wait >/dev/null 2>&1 || true

# No service may start while packages install: dnsmasq would fight systemd-resolved for port 53, and
# nginx/apache2 for port 80. Boot-time choices are made explicitly below.
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
trap 'rm -f /usr/sbin/policy-rc.d' EXIT

echo "== apt-get update"
"${APT[@]}" update

# keep only names this archive knows (a renamed package must not stop the whole build)
want=()
for p in $BASE_PACKAGES "${EXTRA_PACKAGES[@]}"; do
  if apt-cache show "$p" >/dev/null 2>&1; then want+=("$p"); else echo "VFY-NOTE package not in the archive: $p"; fi
done
echo "== installing ${#want[@]} packages"
"${APT[@]}" install --no-install-recommends "${want[@]}"
# perf for the running kernel (the meta package would pull a newer kernel's tools)
"${APT[@]}" install --no-install-recommends "linux-tools-$(uname -r)" linux-tools-common \
  || echo "VFY-NOTE linux-tools-$(uname -r) is not in the archive: perf will be MISSING"

# command-not-found's database is built from the archive's Commands files: fetch them now, offline later
"${APT[@]}" update
/usr/lib/cnf-update-db >/dev/null 2>&1 || true
rm -f /usr/sbin/policy-rc.d

# --- boot-time services: the same choices as labs/base/Dockerfile, except what a VM needs ------------------
# Off at boot but startable (rooms decide), exactly as in the lab image:
systemctl disable nginx.service apache2.service dnsmasq.service postgresql.service cron.service >/dev/null 2>&1 || true
# The packaged ttyd.service would hold port 7681 at boot (the lab image masks it too):
systemctl mask ttyd.service >/dev/null 2>&1 || true
# Not in the lab image at all; off at boot so rooms see the same machine (docker0 would be a second NIC).
# The commands pass starts docker itself.
systemctl disable docker.service docker.socket containerd.service haproxy.service >/dev/null 2>&1 || true
# This VM is offline after prepare: apt timers would only hold the dpkg lock during a run.
systemctl disable apt-daily.timer apt-daily-upgrade.timer motd-news.timer >/dev/null 2>&1 || true
# Kept ON, unlike the lab image (which is a container): ssh (how vmctl reaches the VM) and systemd-resolved
# (the VM's DNS). Container-only masks (udevd, logind, getty, modules-load, debug mounts) are NOT applied.

# --- the terminal user: `lab`, passwordless sudo, exactly like labs/base/Dockerfile --------------------------
# cloud-init created lab (uid 1000, groups sudo,adm,systemd-journal, SSH key only, no password).
id lab
printf 'lab ALL=(ALL:ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/lab
chmod 0440 /etc/sudoers.d/lab
rm -f /etc/sudoers.d/90-cloud-init-users
visudo -cq
touch /home/lab/.sudo_as_admin_successful && chown lab:lab /home/lab/.sudo_as_admin_successful
sed -i '/pam_lastlog\.so/d' /etc/pam.d/login
rm -f /etc/update-motd.d/10-help-text /etc/update-motd.d/50-motd-news /etc/update-motd.d/60-unminimize
printf '%s\n' '' '  Verify VM (Ubuntu 24.04, offline). Thrown away after every run.' '' > /etc/motd

# --- later boots: no cloud-init (no seed disk any more; the network config it wrote stays) -------------------
touch /etc/cloud/cloud-init.disabled

# --- small image ------------------------------------------------------------------------------------------
apt-get clean
journalctl --vacuum-size=8M >/dev/null 2>&1 || true
rm -rf /var/lib/cloud/instances/*/sem/config_scripts_user /tmp/* /var/tmp/* 2>/dev/null || true
fstrim -av >/dev/null 2>&1 || true
echo "VFY-PROVISION-OK"
