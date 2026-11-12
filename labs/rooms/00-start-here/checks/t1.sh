#!/usr/bin/env bash
# t1: ~/whereami.txt exists, belongs to the on-call user and names this machine.
f=/home/lab/whereami.txt
if [ ! -f "$f" ]; then echo "No ~/whereami.txt yet: write this machine's hostname into it."; exit 1; fi
if [ "$(stat -c %U "$f")" != "lab" ]; then echo "~/whereami.txt belongs to $(stat -c %U "$f"): create it as yourself, without sudo."; exit 1; fi
if [ "$(tr -d '[:space:]' < "$f")" != "$(hostname)" ]; then echo "~/whereami.txt does not contain just this machine's hostname."; exit 1; fi
echo "~/whereami.txt names this machine."
