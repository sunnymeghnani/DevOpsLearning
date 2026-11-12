#!/usr/bin/env bash
# 00-start-here: orientation shift. Runs as root inside a fresh lab; idempotent, offline, < 1 s.
# Broken state: the status page (nginx) is stopped AND disabled, as if the decommission steps
# for an old host had been run on this one; the handover note sits somewhere under /srv.
set -euo pipefail

rm -rf /srv/ops
mkdir -p /srv/ops/shift-notes/2026-10-18 /srv/ops/shift-notes/2026-10-19 /srv/ops/runbooks /srv/backups

cat > /srv/ops/shift-notes/2026-10-18/notes.txt <<'NOTE'
Quiet night. Disk on the backup host at 61 %. Nothing to hand over.
NOTE

cat > /srv/ops/shift-notes/2026-10-19/handover.txt <<'NOTE'
Handover, night shift -> morning shift
Ticket: OPS-4127  "status page down after maintenance"

During maintenance I ran the decommission steps for the OLD status host
(status-old) in the wrong terminal tab. They ran on THIS host instead:
the web server was stopped and disabled. Sorry.

Morning shift, please:
  1. acknowledge this handover: write the ticket ID into handover.ack
     in this folder;
  2. bring the status page back so it also survives the next reboot.
NOTE

cat > /srv/ops/runbooks/status-page.md <<'NOTE'
# Status page runbook
The status page is a static file served by nginx from /var/www/html.
Healthy answer from http://localhost/ contains: status: ok
NOTE

: > /srv/backups/README
chown -R root:root /srv/ops /srv/backups
chmod -R a+rX /srv/ops /srv/backups
# the on-call user may write in today's shift folder (for the acknowledgement)
chown lab:lab /srv/ops/shift-notes/2026-10-19

# the status page itself
mkdir -p /var/www/html
rm -f /var/www/html/index.nginx-debian.html
printf '<!doctype html>\n<title>status</title>\n<p>status: ok</p>\n' > /var/www/html/index.html

# the incident: web server stopped and disabled; no earlier attempts left behind
rm -f /home/lab/whereami.txt
systemctl disable --now nginx.service >/dev/null 2>&1 || true
