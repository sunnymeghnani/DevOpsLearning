#!/bin/bash
# Reference fix for room 23 (tests only).
set -euo pipefail
q() { runuser -u postgres -- psql -X -Atc "$1"; }
# t1: who holds the slots? The superuser still gets in through the reserved slots.
q "select usename, application_name, state, count(*) from pg_stat_activity where backend_type = 'client backend' group by 1,2,3 order by 4 desc"
echo "ANSWER q1=$(q "select application_name from pg_stat_activity where backend_type = 'client backend' group by 1 order by count(*) desc limit 1")"
echo "ANSWER q2=$(q "select name from pg_settings where name like 'superuser_reserved%'")"
systemctl disable --now report-worker.service
# t2: end the sessions that sit in an open transaction, then add timeouts (reload, no restart).
q "select pid, usename, state, now() - state_change as idle_for from pg_stat_activity where state like 'idle in transaction%'"
q "select pg_terminate_backend(pid) from pg_stat_activity where state like 'idle in transaction%' and pid <> pg_backend_pid()"
q "alter system set idle_in_transaction_session_timeout = '5min'"
q "alter role reports set idle_session_timeout = '15min'"
q "select pg_reload_conf()"
echo "ANSWER q3=$(q "select context from pg_settings where name = 'max_connections'")"
