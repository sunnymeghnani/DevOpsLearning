#!/bin/bash
# t2: the runaway backup-sync is gone.
fail() { echo "$1"; exit 1; }
p=$(pgrep -x backup-sync | tr '\n' ' ')
[ -z "$p" ] || fail "backup-sync is still running (PID ${p% })"
echo "backup-sync is gone"
