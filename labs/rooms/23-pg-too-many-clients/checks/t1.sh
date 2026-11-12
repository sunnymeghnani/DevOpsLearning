#!/bin/bash
# t1: the leaking worker is stopped and stays off after a reboot; it holds no connections; the shop can connect again.
fail() { echo "$1"; exit 1; }
q() { runuser -u postgres -- psql -X -Atc "$1" 2>/dev/null </dev/null; }
systemctl is-active -q postgresql || fail "PostgreSQL is not running"
systemctl is-active -q report-worker && fail "report-worker.service is still running and leaking connections"
st=$(systemctl is-enabled report-worker 2>/dev/null)
case "$st" in disabled|masked) ;; *) fail "report-worker.service is $st: it starts again at the next boot (disable or mask it)";; esac
n=$(q "select count(*) from pg_stat_activity where application_name = 'report-worker'")
[ "${n:-1}" -eq 0 ] || fail "report-worker still holds $n connections"
runuser -u shop -- psql -X -d shop -Atc 'select 1' >/dev/null 2>&1 </dev/null || fail "the shop role still can't connect: $(runuser -u shop -- psql -X -d shop -Atc 'select 1' 2>&1 </dev/null | tail -1)"
echo "report-worker is stopped and $st; the shop can connect again"
