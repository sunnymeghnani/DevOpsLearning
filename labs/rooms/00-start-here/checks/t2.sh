#!/usr/bin/env bash
# t2: the handover is acknowledged next to the note, with the ticket ID from the note.
note=$(grep -rl --include='*.txt' 'Handover, night shift' /srv/ops 2>/dev/null | head -n1)
ack="$(dirname "${note:-/nonexistent/x}")/handover.ack"
if [ -z "$note" ]; then echo "The handover note is missing: reset the lab."; exit 1; fi
if [ ! -f "$ack" ]; then echo "No handover.ack next to the handover note yet."; exit 1; fi
ticket=$(grep -o 'OPS-[0-9]\+' "$note" | head -n1)
if ! grep -qi -- "$ticket" "$ack"; then echo "handover.ack exists but does not contain the ticket ID from the note."; exit 1; fi
echo "Handover acknowledged with the right ticket ID."
