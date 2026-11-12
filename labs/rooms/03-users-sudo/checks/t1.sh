#!/bin/bash
# t1: the new hostname stays, and it resolves locally (no more "sudo: unable to resolve host").
fail() { echo "$1"; exit 1; }
[ "$(hostname)" = app-prod-01 ] || fail "the hostname must stay app-prod-01 (naming standard), now: $(hostname)"
[ "$(tr -d '[:space:]' < /etc/hostname)" = app-prod-01 ] || fail "/etc/hostname does not say app-prod-01, so a reboot would change the name"
getent hosts localhost >/dev/null || fail "localhost no longer resolves: keep the existing /etc/hosts lines"
addr=$(getent hosts app-prod-01 | awk '{print $1; exit}')
[ -n "$addr" ] || fail "app-prod-01 does not resolve (getent hosts app-prod-01 is empty)"
case "$addr" in
  127.*|::1) ;;
  *) ip -o addr show | grep -qw "$addr" || fail "app-prod-01 resolves to $addr, which is not an address of this machine" ;;
esac
out=$(sudo -n true 2>&1)
case "$out" in *"unable to resolve host"*) fail "sudo still prints: $out" ;; esac
echo "app-prod-01 resolves to $addr; sudo is quiet"
