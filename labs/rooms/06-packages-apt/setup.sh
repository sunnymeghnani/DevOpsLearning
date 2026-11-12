#!/bin/bash
# Room 06 (packages-apt): "E: dpkg was interrupted" after an install was killed mid-way, offline.
# Broken state:
#  - air-gapped box: Ubuntu archives disabled, internal mirror file:/srv/mirror with app-agent 1.0 and 1.1;
#  - the install of app-agent 1.0 was killed during its postinst -> dpkg journal left behind, package half-configured;
#  - /etc/app-agent/agent.conf has a typo ("sever"), so the postinst fails when it is re-run;
#  - 1.1 (recalled by the vendor) is in the mirror and would be pulled by the next "apt upgrade".
set -euo pipefail

# --- reset (idempotent) ---
pkill -KILL -x dpkg >/dev/null 2>&1 || true
rm -f /run/app-agent/draining
if dpkg-query -W app-agent >/dev/null 2>&1; then
  apt-mark unhold app-agent >/dev/null 2>&1 || true
  printf 'server = 10.0.20.5\n' > /etc/app-agent/agent.conf
  dpkg --configure -a >/dev/null 2>&1 || true
  dpkg --purge app-agent >/dev/null 2>&1 || true
fi

# --- build the two package versions (dpkg-deb only, no internet) ---
build() {   # build VERSION
  local v=$1 w; w=$(mktemp -d)
  mkdir -p "$w/DEBIAN" "$w/usr/bin"
  cat > "$w/DEBIAN/control" <<EOF
Package: app-agent
Version: $v
Architecture: all
Maintainer: Example Ops <ops@example.com>
Section: admin
Priority: optional
Description: metrics agent for the internal monitoring
 Ships /usr/bin/app-agent. Reads /etc/app-agent/agent.conf.
EOF
  cat > "$w/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
case "$1" in
  configure)
    # wait for a running agent to drain its queue before switching versions
    while [ -e /run/app-agent/draining ]; do sleep 1; done
    /usr/bin/app-agent --check-config /etc/app-agent/agent.conf
    ;;
esac
exit 0
EOF
  cat > "$w/usr/bin/app-agent" <<EOF
#!/bin/bash
# app-agent $v
VERSION=$v
EOF
  cat >> "$w/usr/bin/app-agent" <<'EOF'
case "${1:-}" in
  --version) echo "app-agent $VERSION" ;;
  --check-config)
    f=${2:-/etc/app-agent/agent.conf}; n=0; have_server=no
    [ -r "$f" ] || { echo "app-agent: cannot read $f" >&2; exit 1; }
    while IFS= read -r line || [ -n "$line" ]; do
      n=$((n+1)); line=${line%%#*}; [ -z "${line// }" ] && continue
      key=$(echo "${line%%=*}" | tr -d ' ')
      case "$key" in
        server) have_server=yes ;;
        port|token|interval) ;;
        *) echo "app-agent: $f:$n: unknown key '$key' (allowed: server, port, token, interval)" >&2; exit 1 ;;
      esac
    done < "$f"
    [ "$have_server" = yes ] || { echo "app-agent: $f: 'server' is not set" >&2; exit 1; }
    echo "app-agent: $f OK" ;;
  *) echo "usage: app-agent --version | --check-config [FILE]" >&2; exit 2 ;;
esac
EOF
  chmod 755 "$w/DEBIAN/postinst" "$w/usr/bin/app-agent"
  dpkg-deb --build --root-owner-group "$w" "/srv/mirror/app-agent_${v}_all.deb" >/dev/null
  rm -rf "$w"
}
rm -rf /srv/mirror && mkdir -p /srv/mirror
build 1.0
build 1.1
python3 - <<'PY'
import hashlib, os, subprocess, time
os.chdir("/srv/mirror")
stanzas = []
for deb in sorted(f for f in os.listdir(".") if f.endswith(".deb")):
    ctl = subprocess.run(["dpkg-deb", "-f", deb], capture_output=True, text=True, check=True).stdout.rstrip("\n")
    data = open(deb, "rb").read()
    stanzas.append(ctl + f"\nFilename: ./{deb}\nSize: {len(data)}\nMD5sum: {hashlib.md5(data).hexdigest()}"
                   f"\nSHA256: {hashlib.sha256(data).hexdigest()}\n")
open("Packages", "w").write("\n".join(stanzas))
p = open("Packages", "rb").read()
open("Release", "w").write(
    "Origin: Example Internal Mirror\nLabel: internal\nSuite: internal\nCodename: internal\n"
    "Date: " + time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime()) + "\nArchitectures: all amd64\n"
    f"SHA256:\n {hashlib.sha256(p).hexdigest()} {len(p)} Packages\n")
PY

# --- apt: archives off (no internet here), internal mirror on ---
src=/etc/apt/sources.list.d/ubuntu.sources
if [ -f "$src" ] && ! grep -q '^Enabled: no' "$src"; then
  sed -i 's/^Types: deb$/Types: deb\nEnabled: no/' "$src"
fi
cat > /etc/apt/sources.list.d/internal-mirror.sources <<'EOF'
# internal package mirror (this network has no internet access)
Types: deb
URIs: file:/srv/mirror
Suites: ./
Trusted: yes
EOF
apt-get update -qq >/dev/null 2>&1

# --- the interrupted install ---
mkdir -p /etc/app-agent /run/app-agent
cat > /etc/app-agent/agent.conf <<'EOF'
# app-agent configuration (written by hand before the install, ticket MON-77)
sever = 10.0.20.5
port = 9100
interval = 30
EOF
touch /run/app-agent/draining
setsid dpkg -i /srv/mirror/app-agent_1.0_all.deb </dev/null >/dev/null 2>&1 &
disown
for _ in $(seq 100); do pgrep -f 'app-agent.postinst configure' >/dev/null && break; sleep 0.1; done
pg=$(ps -o pgid= -p "$(pgrep -x dpkg | head -1)" | tr -d ' ')
kill -KILL -- "-$pg" 2>/dev/null || true      # the SSH session died: dpkg and its postinst are gone
sleep 0.3
rm -f /run/app-agent/draining
