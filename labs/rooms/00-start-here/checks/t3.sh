#!/usr/bin/env bash
# t3: nginx runs now, starts at boot, and serves the status page.
if ! systemctl is-active --quiet nginx; then echo "nginx is not running (look at systemctl status nginx)."; exit 1; fi
if ! systemctl is-enabled --quiet nginx; then echo "nginx runs now but is not enabled, so the next reboot takes the status page down again."; exit 1; fi
if ! curl -fsS --max-time 5 http://127.0.0.1/ 2>/dev/null | grep -q 'status: ok'; then echo "nginx runs, but http://localhost/ does not return the status page."; exit 1; fi
echo "nginx is active, enabled and serving the status page."
