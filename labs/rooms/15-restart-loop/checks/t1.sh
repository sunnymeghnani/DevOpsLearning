#!/bin/bash
# t1: the unit file is fixed (program path, environment file) and systemd has loaded the fixed version.
fail() { echo "$1"; exit 1; }
U=export-worker.service
F=/etc/systemd/system/$U
[ -f "$F" ] || fail "$F is missing"
out=$(systemd-analyze verify "$F" 2>&1 | grep -i 'export-worker' | head -1)
[ -z "$out" ] || fail "systemd-analyze verify: $out"
grep -qE '^[[:space:]]*User=exporter[[:space:]]*$' "$F" || fail "the worker must keep running as User=exporter"
while read -r ef; do
  [ -n "$ef" ] || continue
  case $ef in -*) continue ;; esac
  [ -r "$ef" ] || fail "EnvironmentFile $ef does not exist"
done < <(sed -n 's/^[[:space:]]*EnvironmentFile=//p' "$F")
env=$(systemctl show -P Environment $U 2>/dev/null)
files=$(sed -n 's/^[[:space:]]*EnvironmentFile=-\{0,1\}//p' "$F")
dir=$( { for f in $files; do [ -r "$f" ] && cat "$f"; done; tr ' ' '\n' <<< "$env"; } | sed -n 's/^[[:space:]]*EXPORT_DIR=//p' | tail -1 | tr -d '"'"'")
[ -n "$dir" ] || fail "the unit's environment does not set EXPORT_DIR (see /etc/export-worker/worker.env.example)"
[ "$(systemctl show -P NeedDaemonReload $U)" = no ] || fail "systemd still runs the old copy of the unit: daemon-reload"
exe=$(systemctl show -P ExecStart $U | sed -n 's/.*path=\([^ ;]*\).*/\1/p')
[ -x "$exe" ] || fail "ExecStart program $exe is not executable"
echo "the unit verifies cleanly, its environment file exists and systemd loaded it"
