#!/bin/bash
# t1: dpkg is consistent again: app-agent 1.0 fully configured, no interrupted journal, apt usable.
fail() { echo "$1"; exit 1; }
st=$(dpkg-query -W -f='${Status} ${Version}' app-agent 2>/dev/null) || fail "app-agent is not installed"
case "$st" in
  "install ok installed 1.0"|"hold ok installed 1.0") ;;
  *) fail "app-agent state is '$st' (expected: installed 1.0)" ;;
esac
ls /var/lib/dpkg/updates/ 2>/dev/null | grep -q '^[0-9]' && fail "/var/lib/dpkg/updates still holds an interrupted journal (dpkg was interrupted)"
a=$(dpkg --audit 2>&1); [ -z "$a" ] || fail "dpkg --audit still reports: $(head -1 <<< "$a")"
apt-get check -qq </dev/null >/dev/null 2>&1 || fail "apt-get check fails: apt is still blocked"
/usr/bin/app-agent --check-config /etc/app-agent/agent.conf >/dev/null 2>&1 || fail "app-agent --check-config rejects /etc/app-agent/agent.conf"
grep -q '^[[:space:]]*server[[:space:]]*=[[:space:]]*10\.0\.20\.5' /etc/app-agent/agent.conf || fail "agent.conf must still point at the monitoring server 10.0.20.5"
echo "app-agent 1.0 is installed and configured; dpkg and apt are healthy"
