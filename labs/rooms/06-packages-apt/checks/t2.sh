#!/bin/bash
# t2: app-agent is held at 1.0 although the mirror offers 1.1, so "apt upgrade" leaves it alone.
fail() { echo "$1"; exit 1; }
v=$(dpkg-query -W -f='${Version}' app-agent 2>/dev/null) || fail "app-agent is not installed"
[ "$v" = 1.0 ] || fail "app-agent $v is installed: the vendor recalled 1.1, stay on 1.0"
apt-cache madison app-agent 2>/dev/null | grep -q '| *1\.1 *|' || fail "the mirror no longer offers 1.1: keep the mirror, hold the package instead"
apt-mark showhold 2>/dev/null | grep -qx app-agent || fail "app-agent is not on hold"
apt-get -s upgrade </dev/null 2>/dev/null | grep -q '^Inst app-agent' && fail "apt-get upgrade would still install app-agent 1.1"
echo "app-agent is held at 1.0; apt upgrade keeps it back"
