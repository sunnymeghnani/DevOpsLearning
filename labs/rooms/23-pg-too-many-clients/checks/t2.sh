#!/bin/bash
# t2: no session idles in an open transaction for more than a minute; the reports role gets an idle-in-transaction
# and an idle-session timeout (system-wide or per role, 1 s to 1 h); applied with a reload, not a restart.
fail() { echo "$1"; exit 1; }
q() { runuser -u postgres -- psql -X -Atc "$1" 2>/dev/null </dev/null; }
systemctl is-active -q postgresql || fail "PostgreSQL is not running"
start=$(cat /var/lib/lab-room23/pg-start 2>/dev/null)
[ "$(q 'select pg_postmaster_start_time()')" = "$start" ] \
  || fail "PostgreSQL was restarted: that dropped every session, the shop's too. These settings need only a reload (Reset the room to retry)"
stale=$(q "select count(*) from pg_stat_activity where state like 'idle in transaction%' and now() - state_change > interval '60 seconds'")
[ "${stale:-1}" -eq 0 ] || fail "$stale session(s) still sit idle in transaction for over a minute (they hold locks and slots)"
pids=$(paste -sd, /var/lib/lab-room23/stale-pids 2>/dev/null)
if [ -n "$pids" ]; then
  left=$(q "select count(*) from pg_stat_activity where pid in ($pids)")
  [ "${left:-1}" -eq 0 ] || fail "the $left forgotten analyst session(s) are still open, idle in transaction: end them from the server side"
fi
ms() { runuser -u reports -- psql -X -d shop -Atc "select setting::bigint * case unit when 's' then 1000 when 'min' then 60000 else 1 end from pg_settings where name = '$1'" 2>/dev/null </dev/null; }
for s in idle_in_transaction_session_timeout idle_session_timeout; do
  v=$(ms $s)
  [ -n "$v" ] || fail "can't read $s as the reports role (can reports connect?)"
  [ "$v" -gt 0 ] || fail "$s is 0 (off) for the reports role: set it and reload"
  [ "$v" -ge 1000 ] && [ "$v" -le 3600000 ] || fail "$s is ${v} ms for the reports role: use 1 s to 1 h"
done
echo "no stale transactions; reports sessions time out (idle in transaction: $(ms idle_in_transaction_session_timeout) ms, idle: $(ms idle_session_timeout) ms); no restart"
