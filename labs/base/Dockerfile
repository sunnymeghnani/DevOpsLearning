# Lab machine: a disposable Ubuntu 24.04 "server" with real systemd, for the handbook's lab rooms.
#
#   docker compose --profile labs build lab-base        (or: docker build -t devops-handbook-lab:base labs/base)
#
# It runs unprivileged: the labs controller starts it ONLY with the docker run options in
# labs/SPEC.md (no --privileged, all capabilities dropped except a short list, an internal
# network, memory/CPU/pid limits). It is destroyed on Finish, Reset, 30 min idle, controller
# start and `docker compose --profile labs down`. Nothing in here runs on the host.
FROM ubuntu:24.04 AS devlab-base
LABEL devops-handbook.labs="base" org.opencontainers.image.title="devops-handbook-lab"
ENV DEBIAN_FRONTEND=noninteractive container=docker LANG=C.UTF-8
RUN : devlab-base
RUN apt-get update && apt-get install -y --no-install-recommends \
      systemd systemd-sysv dbus ca-certificates sudo locales tzdata \
      bash-completion less vim-tiny nano man-db file tree \
      iproute2 iputils-ping dnsutils netcat-openbsd curl wget traceroute mtr-tiny tcpdump \
      procps psmisc lsof strace htop sysstat util-linux e2fsprogs \
      openssh-server openssh-client git jq python3 cron rsyslog logrotate nginx-light ttyd \
      acl shellcheck dos2unix ipcalc \
      apache2 openssl dnsmasq systemd-resolved netplan.io postgresql \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 # quiet, fast boot: drop units that make no sense in a container
 && systemctl mask systemd-udevd.service systemd-udev-trigger.service systemd-modules-load.service \
      sys-kernel-debug.mount sys-kernel-tracing.mount getty.target console-getty.service \
      systemd-logind.service \
 # the packaged ttyd.service would hold port 7681 at boot; the controller starts the lab's own ttyd
 && systemctl mask ttyd.service \
 # off at boot, but startable (`systemctl start ssh` needs ssh.socket unmasked): rooms decide
 && systemctl disable ssh.socket ssh.service nginx.service cron.service apache2.service dnsmasq.service \
      systemd-resolved.service postgresql.service >/dev/null 2>&1 || true

# "degraded" fix. The failed units were systemd-journald (+ its sockets, journal-flush) and
# rsyslog (+ syslog.socket), all with status=218/CAPABILITIES: their unit files set
# CapabilityBoundingSet=, and dropping a capability from the bounding set needs CAP_SETPCAP,
# which the lab does not get (--cap-drop ALL + a short --cap-add list). Masking them would
# remove journalctl, which the log rooms need, so instead every service's bounding set is
# widened to exactly the lab's own capability list: nothing has to be dropped, nothing fails,
# and no service can hold more than the container already allows.
RUN mkdir -p /etc/systemd/system/service.d \
 && printf '%s\n' '[Service]' \
      '# lab containers lack CAP_SETPCAP; keep the bounding set equal to the container'"'"'s (see labs/base/Dockerfile)' \
      'CapabilityBoundingSet=CAP_CHOWN CAP_DAC_OVERRIDE CAP_FOWNER CAP_SETUID CAP_SETGID CAP_KILL CAP_NET_BIND_SERVICE CAP_SYS_CHROOT CAP_AUDIT_WRITE CAP_NET_RAW CAP_SYS_ADMIN' \
      > /etc/systemd/system/service.d/10-lab-capabilities.conf \
 # journald: keep the journal small and in memory (the lab is thrown away anyway)
 && mkdir -p /etc/systemd/journald.conf.d \
 && printf '%s\n' '[Journal]' 'Storage=volatile' 'RuntimeMaxUse=32M' > /etc/systemd/journald.conf.d/10-lab.conf \
 # rsyslog: a container cannot read the host's kernel log (/proc/kmsg); without this every boot
 # logs two errors that would show up in `journalctl -p err` during the log rooms
 && sed -i 's/^module(load="imklog"/#&/' /etc/rsyslog.conf

# The terminal user: `lab`, passwordless sudo (the learner fixes the machine as root with sudo).
# No password is set, so nobody can log in over the network; ttyd starts `login -f lab`.
RUN userdel -r ubuntu 2>/dev/null || true \
 && useradd -m -u 1000 -s /bin/bash -G sudo,adm,systemd-journal lab \
 && passwd -l lab >/dev/null \
 && printf 'lab ALL=(ALL:ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/lab && chmod 0440 /etc/sudoers.d/lab \
 && visudo -cq \
 && touch /home/lab/.sudo_as_admin_successful && chown lab:lab /home/lab/.sudo_as_admin_successful \
 && printf 'LANG=C.UTF-8\n' > /etc/default/locale \
 # pam_lastlog.so is not shipped in 24.04; drop the line so every login stops logging a PAM error
 && sed -i '/pam_lastlog\.so/d' /etc/pam.d/login \
 # login banner: short and offline (the stock scripts fetch news or talk about unminimize)
 && rm -f /etc/update-motd.d/10-help-text /etc/update-motd.d/50-motd-news /etc/update-motd.d/60-unminimize \
 && printf '%s\n' '' \
      '  Disposable lab machine (Ubuntu 24.04, real systemd, no internet).' \
      '  You are "lab" with passwordless sudo. Break anything: Finish or Reset throws it away.' \
      '' > /etc/motd

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
