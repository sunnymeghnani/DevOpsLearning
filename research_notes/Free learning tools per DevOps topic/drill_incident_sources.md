# Drill incident sources: 30 candidates (research, 10 November 2026)

Purpose: public incidents for new decision drills (see `drills/SPEC.md`). Every source below was
**opened and read on 2026-11-10** with WebFetch unless marked otherwise. No Reddit, Stack Overflow or
Server Fault; no logins. Facts in "Incident" come from the source; "Decision points" are teaching
devices: moves marked *(real)* are what people in the source actually did, the rest are invented
tempting moves for the drill.

Not reused: the 12 existing drills (GitLab 2017, GitLab dind 2019, Docker json-logs, NADA inodes,
Let's Encrypt DST root, GitHub RSA key, Datadog 2023 networkd, Zalando CoreDNS, Cloudflare 2019 WAF,
Roblox 2021, AWS S3 2017, Atlassian 2022). From `research/community-incidents.json` this list uses
Traefik #12253, Dokploy #5453, HashiCorp Discuss #62078 and Grafana Community #127458 (all unused
until now). Other unused items there were opened and are listed under "Reserves".

Source-strength key: **strong** = vendor/engineering post-mortem or maintainer-explained fix;
**medium** = fix confirmed by the reporter, cause partly explained; flagged where it matters.

Uncovered topics hit by the 30: **58 of 74** (list at the end).

---

## L0 Fresher

### 1. AWS us-east-1, 19–20 October 2025: "is it us or the cloud?"
- **Source:** "Summary of the Amazon DynamoDB Service Disruption in the Northern Virginia (US-EAST-1) Region", AWS, 2025-10-19/20, https://aws.amazon.com/message/101925/ (opened). Strong.
- **Incident:** From 23:48 PDT on 19 Oct, DynamoDB API errors rose and clients could not make new connections. A latent race between two DNS Enactors left `dynamodb.us-east-1.amazonaws.com` with an empty DNS record (a delayed Enactor applied an old plan; the other's cleanup then deleted it). DNS was restored by 02:25; client caches expired by 02:40. The cascade lasted much longer: EC2's DropletWorkflow Manager went into congestive collapse re-establishing leases (hosts restarted 04:14, leases back 05:28), network propagation lagged until 10:36, and NLB health checks flapped and triggered AZ DNS failover, which engineers disabled at 09:36. Lambda, ECS/EKS, STS, console sign-in and others were hit; full recovery 14:20 PDT (Redshift next day). AWS disabled the DNS Planner/Enactor automation worldwide, and added an NLB failover velocity control and DWFM recovery tests.
- **Placement:** L0, cloud; topics `cloud-concepts`, `aws-platform`, `incident-note`.
- **Decision points:**
  1. Your app on EC2 times out talking to DynamoDB: redeploy your app / check the AWS Health Dashboard and your own error graph first / open a ticket blaming the network team.
  2. DNS is back but your instances still fail: flush and restart everything / read the provider timeline and wait for cached records to expire / move the database to another region in a panic.
  3. New EC2 launches fail with "insufficient capacity": keep retrying in a loop (adds load) / keep existing instances and pause autoscaling changes / terminate "unhealthy" instances.
  4. After: write an incident note naming the single-region dependency, not "AWS broke".
- **Practice:** `aws-skill-builder` (Cloud Quest) for regions/AZs; `the-void` to read more provider reports.

### 2. CrowdStrike Channel File 291, 19 July 2024: Windows machines crash at boot
- **Source:** "Falcon Content Update Preliminary Post Incident Report", CrowdStrike, 2024-07-19 (PIR 24 July), https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/ (opened). Strong.
- **Incident:** A Rapid Response Content update released 04:09 UTC reached Windows hosts running sensor 7.11+ until it was reverted at 05:27 UTC. A bug in the Content Validator let a problematic IPC Template Instance pass; Channel File 291 caused an out-of-bounds read in the sensor's Content Interpreter, unhandled, so Windows crashed (BSOD). Mac and Linux were not affected. Follow-ups: staggered/canary rollout of content, customer control over timing, more validation, fuzzing and fault injection, third-party review. (The PIR does not include the per-host recovery steps; use the drill only for what the PIR says.)
- **Placement:** L0, linux (track of `windows-macos`); topics `windows-macos`, `kernel-boot`.
- **Decision points:**
  1. Help desk floods with blue screens: reinstall Windows on each machine / find the common factor (all crashed after an agent update, all Windows, none Linux) / disable the antivirus on servers that still work.
  2. Is it the OS update or the security agent? Compare timestamps with the vendor's content release; check Linux/Mac hosts.
  3. Communicate: one status message with scope and next update time, instead of silence.
  4. After: ask for staged rollouts and a canary group for third-party kernel-level agents.
- **Practice:** Killercoda "Dev Bench: boot and targets"; handbook Windows module.

### 3. Pi-hole on Ubuntu: "Address already in use" on port 53
- **Source:** "Installation breaks Ubuntu's systemd-resolved", pi-hole/pi-hole #4816, GitHub, opened 2022-07-11, https://github.com/pi-hole/pi-hole/issues/4816 (opened). Strong (maintainer-confirmed bug).
- **Incident:** On Ubuntu 20.04, Pi-hole fails to start while systemd-resolved holds port 53 ("Address already in use"). The installer set `DNSStubListener=no` and restarted resolved, after which the host itself could not resolve names: resolved warned that the stub listener is disabled but `/etc/resolv.conf` is still a symlink to the stub file. Maintainer dschaper: the installer does only half the job; `/etc/resolv.conf` must point to the non-stub resolver file. Users found alternatives: keep the stub on 127.0.0.53 and bind Pi-hole to specific interfaces (`bind-interfaces`); disabling resolved entirely broke Docker image pulls for one user. Labelled "Bug: Confirmed", still open.
- **Placement:** L0, network; topics `port-ownership`, `sockets-ports`, `network-problems`.
- **Decision points:**
  1. The DNS container will not start, "address already in use": reboot / find the owner with `ss -lntup 'sport = :53'` then `systemctl status` of that unit / pick port 5353 and tell clients nothing.
  2. Owner is systemd-resolved: stop and mask it *(real, broke Docker pulls)* / disable only the stub and repoint `/etc/resolv.conf` / bind the new service to one interface address and leave 127.0.0.53 alone.
  3. Host now cannot resolve anything: blame Pi-hole / read `resolvectl status` and the resolv.conf symlink target.
- **Practice:** SadServers "Bergen: port already in use"; iximiuz "Find the listening port"; lab room `10-net-basics`.

### 4. Docker-published MongoDB ransomed behind UFW
- **Source:** "Lessons from a Hack: Securing systems properly when using UFW with Docker", realogs blog, 2024-06-07, https://blog.realogs.in/docker-ufw-config/ (opened). Medium-strong (first-hand account; mechanism documented by Docker).
- **Incident:** A MongoDB container on a VPS was published with `-p 27017:27017`. The author relied on UFW because the provider had no external firewall. One day the databases were gone, replaced by a single database holding a ransom note (0.005 BTC in 48 hours); logs also showed SSH password brute-forcing. Cause: Docker's `-p` adds iptables rules that bypass UFW, so the port was public. Fixes: publish to `127.0.0.1:27017:27017`, set the daemon's default bind IP to 127.0.0.1 in `daemon.json`, open only 80/443 and SSH, key-only SSH, Tailscale SSH.
- **Placement:** L0, security; topics `host-firewall`, `docker-firewall`, `sockets-ports`.
- **Decision points:**
  1. Data replaced by a ransom note: pay / stop the container but keep the volume and logs as evidence / delete everything and redeploy.
  2. "But UFW denies 27017": trust `ufw status` / test from outside the host (`nc -vz` from another machine) and read `iptables -L DOCKER -n`.
  3. Fix: add a UFW deny rule (does nothing) / bind the published port to 127.0.0.1 or drop `ports:` entirely and use the Compose network / add a DOCKER-USER rule.
  4. Restore from backup and rotate credentials; SSH keys only.
- **Practice:** iximiuz "Restrict access to a Docker-published port"; Killercoda "Network exposure lab: 127.0.0.1 vs 0.0.0.0".

### 5. Healthchecks.io, 20 August 2016: unattended upgrade restarts Postgres
- **Source:** "Outage Postmortem — 20 August 2016", Healthchecks.io blog, https://blog.healthchecks.io/2016/08/outage-postmortem-20-august-2016/ (read on the blog index page https://blog.healthchecks.io/page/6/ where the full post text appears; opened). Strong.
- **Incident:** For about 24 hours the service stopped processing pings, so many checks went "down" and users got a flood of false alerts. Ubuntu's unattended security upgrades installed a PostgreSQL update and restarted the database. The Django site and alerting reconnected; the Go ping handler did not, because its error handling logged failures and carried on, answering every ping with HTTP 400. Alerts reached the sole maintainer within about 5 minutes, but he was travelling and unreachable. A restart of the ping handler fixed it; the code was changed to handle dropped connections, unattended upgrades were disabled on the DB server, and the travel kit/mobile-data habits changed.
- **Placement:** L0, sre; topics `uptime-checks`, `incident-note`, `devops-day-to-day`.
- **Decision points:**
  1. Alert: all checks down at once: assume every customer broke / check your own ingest endpoint from outside first.
  2. Ping endpoint returns 400 but the website works: restart Postgres again / read `/var/log/unattended-upgrades/` and `journalctl -u postgresql` and see what restarted / roll back the whole server.
  3. Fix now vs later: restart the handler (*real*), then plan a reconnect fix.
  4. Who else can answer the page when you are away? Write the incident note and an on-call backup.
- **Practice:** SadServers "Cork: the catalog won't open (Postgres after a reboot)"; lab room `06-packages-apt`; `uptime-kuma-demo`.

---

## L1 Junior

### 6. Jenkins project, 10 November 2013: 186 repositories force-pushed
- **Source:** "Summary report: git repository disruption incident of Nov 10th", Jenkins project, published 2013-11-25, https://www.jenkins.io/blog/2013/11/25/summary-report-git-repository-disruption-incident-of-nov-10th/ (opened). Strong.
- **Incident:** One of 680 developers started Gerrit with a partly misconfigured replication plugin pointing at a local folder of 186 two-month-old clones of Jenkins GitHub repositories. The plugin treated them as mirrors and pushed them back with force (its default), moving branch heads to old commits. Developers noticed by 12:54 GMT; Gerrit logs plus GitHub support identified the cause within hours. Commits were not lost (Git objects stay); only refs moved. Recovery: up-to-date developers pushed again, GitHub support reset most heads, and a script using the GitHub events API found about a dozen branches support had missed. Follow-ups: ask for a "no force push" option, log every ref update across the org, per-repo access control; recommend `core.logAllRefUpdates`.
- **Placement:** L1, automation; topics `git-team`, `jenkins`.
- **Decision points:**
  1. "My last month of commits vanished from main": re-commit from memory / check `git reflog` and the hosting provider's push events for the old SHA.
  2. Many repos at once: fix each by hand / find the common pusher and stop it first (*real: Gerrit logs*).
  3. Restore: force-push your local copy without checking it is newer / compare SHAs with the events API, then push.
  4. Prevent: protected branches, no force push to main.
- **Practice:** `learn-git-branching`; GitHub Skills "Change commit history course"; lab room `09-git-basics`.

### 7. Wikimedia Phabricator, July 2024: Apache security update → 403 on URLs with %3F
- **Source:** "T370110 Apache 2.4.61 throws a 403 Forbidden for links containing %3F", Wikimedia Phabricator, reported 2024-07-15, https://phabricator.wikimedia.org/T370110 (opened). Strong. Supporting: Debian bug #1079172 (regression fixed in 2.4.62-1~deb12u2), https://www.mail-archive.com/debian-bugs-closed@lists.debian.org/msg780285.html (opened).
- **Incident:** A fleet-wide Apache update from 2.4.59 to 2.4.61 (12 July 2024) restarted Apache on the Phabricator hosts. Afterwards URLs containing an encoded question mark returned 403. The error log said `AH10508: Unsafe URL with %3f URL rewritten without UnsafeAllow3F`. Trace logging showed the catch-all rule `RewriteRule ^(.*)$ /index.php?__path__=$1 [B,L,QSA]` tripped the new CVE-2024-38474 check. Fix: add `UnsafeAllow3F` to that one rule in the Puppet template, plus an httpbb regression test; resolved 20 Aug 2024. Debian later shipped a regression fix with better question-mark tracking.
- **Placement:** L1, web; topics `apache-vhosts`, `site-down-walk`.
- **Decision points:**
  1. Only some URLs give 403 after patch night: roll back the security update / read the Apache error log for the exact request / clear the browser cache.
  2. Log says AH10508: add `UnsafeAllow3F` to every rule globally / find the one rule (`LogLevel rewrite:trace3` on a test host *(real)*) and flag only it.
  3. Prove it: add a regression check that requests a %3F URL after each deploy.
- **Practice:** SadServers "Verona: Apache portal won't open"; `htaccess-tester`.

### 8. Wikimedia, 24 May 2022: Puppet makes Apache `Listen 443` without mod_ssl
- **Source:** "Incidents/2022-05-24 Failed Apache restart", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2022-05-24_Failed_Apache_restart (opened). Strong.
- **Incident:** A Puppet change merged at 11:40 UTC made Apache listen on 443 even where mod_ssl was not enabled, and Apache restarted with the bad config on a subset of hosts: `apache2.service` failed, Icinga showed connection refused on port 80, a few 502s for logged-in users. Puppet was disabled on MediaWiki hosts at 11:45; a revert at 11:46 did not repair hosts already broken. At 11:56 a fleet command removed the line and started Apache: `cumin ... 'sed -i "s/Listen 443//" /etc/apache2/ports.conf' 'systemctl start apache2'`. A proper fix for servers using Debian's default config followed at 12:05; all healthy 12:16. Gaps: compilation checks passed, no canary for Puppet changes.
- **Placement:** L1, web; topics `apache-81-444`, `apache-vhosts`, `ansible-practice`.
- **Decision points:**
  1. Alerts: apache2 failed on many hosts right after a config-management merge: restart Apache everywhere / stop config management from spreading it (*real*) / wait for the next run.
  2. Revert merged but hosts still down: assume the revert failed / understand that a dead service is not restarted by a revert; check `apachectl configtest` and `ss -ltnp`.
  3. Fix on the fleet: hand-edit 40 hosts / one scripted edit + start, then the proper patch.
  4. After: canary hosts for config changes.
- **Practice:** SadServers "Verona: Apache portal won't open"; Killercoda "Dev Bench: a systemd service won't start".

### 9. journald ignores `SystemMaxUse`: the machine-id keeps changing
- **Source:** "Journal doesn't respect SystemMaxUse option", systemd/systemd #14583, GitHub, 2020-01-16, https://github.com/systemd/systemd/issues/14583 (opened). Strong (maintainer explanation, "not-a-bug").
- **Incident:** With `SystemMaxUse=128M`, `/var/log/journal/` grew to 169M across about a dozen subdirectories of 8–25M each (systemd 243, Yocto). Lennart Poettering: journald names each directory after the machine ID; if `/etc/machine-id` changes, journald starts a new directory and never manages the old ones. Randomising the machine ID at boot is supported only when `/var` is also wiped each boot. Fix is operational: keep `/etc/machine-id` stable (or clear `/var` on stateless systems), then remove the orphaned directories.
- **Placement:** L1, linux; topics `journald-logs`.
- **Decision points:**
  1. `/var/log` full although the journal cap is set: raise the cap / run `journalctl --disk-usage` and `du -sh /var/log/journal/*` and count the directories.
  2. Many directories: delete `/var/log/journal` wholesale while journald runs / compare directory names with `cat /etc/machine-id`.
  3. Root cause: why does the ID change (image build, cloned template)? Fix the image, then `journalctl --vacuum-size` and remove old dirs.
- **Practice:** Killercoda "Dev Bench: journald and logrotate"; SadServers "Saint John: what is writing to this log file?".

### 10. `docker compose up` takes 192.168.16.0/20 and the server vanishes from the office LAN
- **Source:** "Docker (compose?) suddenly creates bridge using 192.168.16.0/20 range", moby/moby #37823, GitHub, 2018-09-11, https://github.com/moby/moby/issues/37823 (opened). Strong (maintainer explanation + documented fix).
- **Incident:** After `docker-compose up` for one project on a physical Ubuntu 18.04 server (192.168.64.2 behind 192.168.64.1), the server stopped answering on the office network. Docker had created a bridge 192.168.16.1 in 192.168.16.0/20, overlapping the LAN behind the gateway. Maintainers: the default pools include 172.17–172.31/16 and 192.168.0.0/16, and the overlap check only covers Docker's own networks and local routes, not the remote LAN. Fix: set `default-address-pools` in `/etc/docker/daemon.json` (e.g. base 172.17.0.0/16, size 24); existing networks keep their subnets, so containers must be stopped, networks recreated and the daemon restarted. A static route was an interim workaround.
- **Placement:** L1, containers; topics `docker-networking`, `network-problems`.
- **Decision points:**
  1. Users on another subnet cannot reach the server after a deploy, but it still pings from its own subnet: blame the firewall / compare `ip route` before and after; look for a new `br-` interface.
  2. Found `br-xxxx 192.168.16.1/20`: delete the interface by hand (Docker recreates it) / set address pools and recreate the project network.
  3. Change window: pool changes need containers down; schedule it and tell people.
- **Practice:** SadServers "Bern: web container can't reach the db container"; iximiuz "Container networking from scratch (free tutorial)".

---

## L2 Mid-level

### 11. Ravelin, July 2019: 502s on every deploy
- **Source:** "Kubernetes' dirty endpoint secret and Ingress", Phil Pearl (Ravelin), 2019-07-26, https://philpearl.github.io/post/k8s_ingress/ (opened; listed on k8s.af). Strong.
- **Incident:** After moving the API layer from VMs to GKE behind a GKE Ingress, integration tests saw occasional 502s during deploys and pod removals. Kubernetes removes a pod from the endpoints and sends it SIGTERM at roughly the same time, and ingress controllers are slow to update, so a pod that stops accepting connections on SIGTERM still gets traffic. Fix: keep serving after SIGTERM (optionally send `Connection: close`), make the termination grace period longer than load-balancer reprogramming, and for code you cannot change add a `preStop` hook that sleeps.
- **Placement:** L2, kubernetes; topics `k8s-workloads`, `deployment-patterns`, `proxy-problems`.
- **Decision points:**
  1. 502s only during rollouts: add retries in the client / correlate 502 timestamps with pod termination events.
  2. Fix: shorten the grace period (worse) / add `preStop` sleep + longer `terminationGracePeriodSeconds` / disable rolling updates.
  3. Verify with a load test during a rollout.
- **Practice:** iximiuz "Deployments: scale, roll out, roll back"; iximiuz "Safe node drain with a disruption budget".

### 12. Moonlight: all web pods on one node, CPU 100%, kernel panics spread
- **Source:** "Outage post-mortem", Moonlight, https://updates.moonlightwork.com/outage-post-mortem-87370 (opened; listed on k8s.af; the page gives "January 18 to January 22" without a year). Strong.
- **Incident:** Intermittent API errors from Friday became full downtime by Tuesday. They first looked like Redis connectivity problems and a Google Cloud networking issue (Google had reported disruptions, and a Twitter user had similar symptoms). Google Cloud support found the pattern: the scheduler sometimes put several CPU-heavy pods on the same node; sustained 100% CPU made the VM kernel panic; rescheduled pods then overloaded the next node, and back-off lengthened the outage. All three website replicas could land on one node. Fix: anti-affinity rules on the major deployments; continue the kernel-panic investigation with Google.
- **Placement:** L2, kubernetes; topics `k8s-scheduling-storage`, `k8s-architecture`.
- **Decision points:**
  1. Redis timeouts + a provider network notice: wait for the provider *(real: the first theory)* / check node health and where pods run (`kubectl get pods -o wide`).
  2. Nodes go NotReady one after another: add nodes only / spread replicas with anti-affinity or topology spread and set CPU requests.
  3. Escalate to the provider with evidence (node crash times, CPU graphs) early.
- **Practice:** iximiuz "Recover pods stuck in Pending"; Killercoda "Chad Crowell CKA scenarios".

### 13. TrueNAS and WD Red DM-SMR drives: resilver turns into drive failures
- **Source:** "WD Red SMR Drive Compatibility with ZFS", TrueNAS (iXsystems) hardware notice, c. 2020 (page modified 2024-08-27), https://www.truenas.com/docs/hardware/notices/wdsmr (opened). Strong (vendor lab finding).
- **Incident:** iXsystems and Western Digital investigated WD Red DM-SMR drives in ZFS. In the lab, the 4 TB WD40EFAX (firmware 82.00A82) under heavy writes such as resilvering could enter a faulty state, return IDNF errors and become unusable; ZFS treats it as a failed drive, and pool data can be lost if several fail. Affected: 2–6 TB WD Red with "EFAX" in the model; 8 TB+ EFAX and older EFRX are CMR. Advice: use CMR drives, avoid these DM-SMR models, erase DM-SMR drives before adding them, keep backups; iXsystems stopped shipping Minis with them.
- **Placement:** L2, data; topics `disk-io`, `backup-tools`.
- **Decision points:**
  1. Replacement disk makes the resilver crawl and then the new disk faults: replace it again with the same model / read `smartctl -i` model, check SMR vs CMR, look at `zpool status` errors.
  2. Pool degraded with a second disk wobbling: start another resilver now / take a fresh backup or replication first.
  3. Purchasing rule: CMR only for ZFS; record the model in the runbook.
- **Practice:** Killercoda "KubeDojo: I/O performance analysis"; iximiuz "USE Practice playground".

### 14. Wikimedia GitLab, 28 February 2023: the nightly restore job ran on production
- **Source:** "Incidents/2023-02-28 GitLab data loss", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2023-02-28_GitLab_data_loss (opened). Strong.
- **Incident:** Self-hosted GitLab had been switched from gitlab1004 to gitlab2002 on 27 Feb for maintenance. The daily restore timer (meant for the replica) was still enabled on what was now production, so at 02:00 UTC it restored the 00:04 backup onto production. ProbeDown fired at 02:03 (nobody paged); the restore finished at 02:20; rsync on production was disabled so replica backups could not be restored again. Work done between 00:04 and 02:00 was lost. Root cause: the manual setting `profile::gitlab::enable_restore` was not updated after the switchover and nobody checked the timers. Actions: enable/disable restore automatically from instance role (done), a switchover cookbook, a post-switchover timer check, a guard in the restore script against the active host.
- **Placement:** L2, data; topics `backup-tools`, `devops-day-to-day`.
- **Decision points:**
  1. GitLab briefly down at 02:00 and recent MRs are missing: restart GitLab / check `systemctl list-timers` and the restore job log.
  2. Restore is still running: let it finish and hope / stop further restores (*real: disabled rsync*) and record exactly which window is lost.
  3. Communicate the lost window to users so they can re-push.
  4. After: role-aware jobs, switchover checklist.
- **Practice:** SadServers "Alexandria: the vanishing backups (cron)"; Killercoda "Dev Bench: a cron job never runs".

### 15. Wikimedia Cloud VPS proxy, 25 November 2024: empty resolver line kills nginx
- **Source:** "Incidents/2024-11-25 WMCS proxy nginx failure", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2024-11-25_WMCS_proxy_nginx_failure (opened). Strong.
- **Incident:** At 03:09 UTC Puppet removed the nameserver line from `/etc/resolv.conf` (known bug T379927) and also the nameserver IP from nginx site files, so nginx logged a fatal error. ProjectProxyMainProxyDown paged at 03:12. The VM answered SSH, nginx would not restart, and a forced Puppet run failed with a name-resolution error. At 03:54 the responder compared configs and found the `resolver` line empty on proxy-04 but set on proxy-03; restoring the nameserver and rerunning Puppet fixed both. No user impact (standby proxy). Actions: fix the Puppet bug, add a runbook, review the alert severity.
- **Placement:** L2, web; topics `network-problems`, `proxy-problems`, `site-down-walk`.
- **Decision points:**
  1. Proxy down, host up: reboot / `nginx -t` and `journalctl -u nginx` first.
  2. Error mentions the resolver: re-run config management (fails: no DNS) / diff the config against the healthy twin (*real*) and check `/etc/resolv.conf`.
  3. Standby only: fix calmly; adjust paging severity afterwards.
- **Practice:** Killercoda "Dev Bench: a hostname won't resolve"; SadServers "Cape Town: borked Nginx".

### 16. Wikimedia toolsdb, 4–5 November 2025: MariaDB primary out of disk, no alert
- **Source:** "Incidents/2025-11-05 WMCS toolsdb primary out of space", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2025-11-05_WMCS_toolsdb_primary_out_of_space (opened). Strong.
- **Incident:** tools-db-4 ran out of disk at 22:40 UTC; tools could not use the shared MariaDB. Users reported it (task at 00:58) but response began at 07:19. The volume was resized; a clean MariaDB stop took too long, so it was force-stopped, unmounted, extended and restarted (4.9 TB, 80% used) at 08:42; normal at 09:04. Cause per actionables: `ibdata1` had grown and never shrinks. No alert fired because a read/write check had been removed in favour of Alertmanager checks that never attempt a write. Actions: fail over to a replica with a small ibdata1 and rebuild, predictive disk alerts, page on low disk.
- **Placement:** L2, data; topics `db-incidents`, `uptime-checks`.
- **Decision points:**
  1. "Can't connect" from users, dashboards green: trust the dashboards / try a real write and check `df -h` on the DB host.
  2. Disk full: delete files in the datadir (ibdata1, binlogs by hand) / extend the volume, or purge binlogs with SQL only.
  3. Stop is slow: kill -9 immediately / give a clean shutdown a bounded time, then force (*real*) and expect crash recovery.
  4. After: synthetic write check + predictive disk alert.
- **Practice:** SadServers "Manhattan: can't write data into Postgres (public, no sign-up)"; SadServers "Rosario: restore a MySQL dump".

---

## L3 Senior

### 17. Docker Engine 29 removes API 1.24: Traefik loses every route
- **Source:** "Docker provider fails with Docker 29: client version 1.24 is too old", traefik/traefik #12253, GitHub, 2025-11-10, https://github.com/traefik/traefik/issues/12253 (opened). Strong (confirmed P0 bug, fixed in 3.6.x).
- **Incident:** After upgrading Docker Engine to 29.0.0 (API 1.52, minimum 1.44) on Debian 12/13 and Ubuntu 24.04, Traefik's Docker provider logged "client version 1.24 is too old. Minimum supported API version is 1.44" and "Provider error, retrying"; all Docker-label routes disappeared. Workarounds were downgrading Docker to 28.x with a package hold, or upgrading Traefik; a user confirmed v3.6.6 works and v3.1.7 fails on Docker 29. Watchtower was hit too. One user noted `/ping` still returned 200 while the provider was failing.
- **Placement:** L3, web; topics `traefik-deep-dive`, `docker-engine`, `dokploy-operations`, `traefik`.
- **Decision points:**
  1. Every site 404 after patch night: restart Traefik / read Traefik logs for the provider error.
  2. "API too old": downgrade Docker and hold it / upgrade Traefik to a fixed 3.6.x / set a daemon-wide minimum API override (not in source; check docs before suggesting).
  3. Monitoring said healthy: why? `/ping` does not check providers; add a probe for a real route.
  4. After: pin Docker versions with `apt-mark hold` and test Engine upgrades on staging.
- **Practice:** SadServers "San Juan: Traefik in Docker Compose"; `docker-workshop` "Docker's Traefik guide".

### 18. Dokploy: each deploy strips Traefik labels from the Swarm service
- **Source:** "Docker-image apps lose Traefik labels on deploy", Dokploy/dokploy #5453, GitHub, 2026-09-13 (closed 2026-10-23 by PR #5631), https://github.com/Dokploy/dokploy/issues/5453 (opened). Medium (fix merged; no maintainer root-cause text).
- **Incident:** On Dokploy v0.29.12 and v0.30.6 (single-node Swarm, Ubuntu arm64), every deploy of a `sourceType=docker` app via webhook or API removed the app's nine `traefik.*` labels from the Swarm service spec. Containers stayed healthy but each hostname returned "404 page not found". `docker service inspect` showed `Spec.Labels` empty while `PreviousSpec.Labels` still had them; the deploy log did not show the update that dropped them. The apps had been created by duplicating a project on an older Dokploy. Workarounds: a systemd timer re-adding labels every 15 s; `docker service update --rollback` restored labels but also the old image. Fixed upstream by PR #5631 ("keep service labels on application deploy").
- **Placement:** L3, containers; topics `dokploy`, `swarm-in-practice`, `swarm`.
- **Decision points:**
  1. 404 from Traefik, containers healthy: redeploy again / compare `docker service inspect --format '{{json .Spec.Labels}}'` with `PreviousSpec`.
  2. Labels gone: roll back the service (*real; also rolls back image*) / re-add labels with `docker service update --label-add` and open an upstream issue with evidence.
  3. Long-term: upgrade to the fixed release; avoid duplicated projects from old versions.
- **Practice:** iximiuz "three-node Docker Swarm playground"; SadServers "San Juan: Traefik in Docker Compose".

### 19. Codecov, January–April 2021: a credential in a Docker image build → CI secrets stolen
- **Source:** "Bash Uploader Security Update", Codecov, 2021-04-15 (updated 2021-04-29), https://about.codecov.io/security-update/ (opened). Strong.
- **Incident:** From 31 January 2021 an attacker altered Codecov's Bash Uploader to send git remote info and all CI environment variables to an outside server, while uploads kept working. The attacker got the needed credential (a GCS key) because of an error in Codecov's Docker image creation process. A customer found it on 1 April by comparing the uploader's SHA checksum with the published value. Affected: the Bash Uploader and tools built on it (GitHub Action, CircleCI orb, Bitrise step). Customers were told to run `env` in CI to list exposed secrets, rotate them, audit their use, and replace stored copies; Codecov rotated credentials and added change monitoring.
- **Placement:** L3, security; topics `container-hardening`, `dockerfile`, `gitops-argocd`, `gitlab-ci-harbor`.
- **Decision points:**
  1. Vendor says its CI script was tampered with: wait for more details / list which pipelines ran it in the window and which secrets they had.
  2. Rotate: only the token named in the email / every secret those jobs could read (registry robots, deploy keys, cloud keys).
  3. Your own images: check layers for secrets (`docker history --no-trunc`), use build secrets/multi-stage.
  4. Prevent: verify checksums or pin by digest/SHA for anything `curl | bash` in CI.
- **Practice:** Kubernetes Goat "Scenario 15: secrets hidden in image layers"; iximiuz "Production image build: multi-stage and non-root"; `cicd-goat`.

### 20. Terraform multi-region: fixing the provider reveals a plan full of destroys
- **Source:** "Terraform catch-22: lack of default provider causes error, default provider breaks per-region providers", HashiCorp Discuss, 2024-01-25, https://discuss.hashicorp.com/t/terraform-catch-22-lack-of-default-provider-causes-error-default-provider-breaks-per-region-providers/62078 (opened). Medium-strong (author-confirmed; explanation by apparentlymart).
- **Incident:** With no default AWS provider, `terraform plan` failed with "Invalid provider configuration"/"Invalid AWS Region". Adding a default made errors vanish but every regional module silently used the default region. Hand-editing `terraform.tfstate` gave "removed provider configuration still needed"; combining state edits and explicit providers gave "Provider configuration not present". Once providers worked, the plan showed many destroys. apparentlymart: configuration, not state, decides which provider manages a resource; state's provider record only matters for removed blocks; check `providers` arguments on module calls and run `terraform providers`. The fix that worked: an explicit per-region `provider = aws.<region>` on every resource in the regional modules.
- **Placement:** L3, automation; topics `terraform`, `terraform-opentofu`.
- **Decision points:**
  1. Errors disappear after adding a default provider: apply / read the plan carefully for region changes and destroys.
  2. Edit state by hand (*real, made it worse*) / use `terraform providers` and fix configuration.
  3. Plan shows destroys: apply anyway / stop, back up state, and fix until the plan is no-op.
- **Practice:** Killercoda "Dev Bench: someone changed it outside Terraform"; SadServers "Parma: debugging Terraform issues"; Wiz "State of Affairs: Terraform state".

### 21. NRE Labs, 4 December 2018: kubeadm etcd killed by its own liveness probe
- **Source:** "December 4 NRE Labs Outage Post-Mortem", Matt Oswalt, https://oswalt.dev/2018/12/december-4-nre-labs-outage-post-mortem/ (opened; k8s.af link redirects here). Strong (honest; probe failure cause left open).
- **Incident:** `kubectl` got "connection ... :6443 was refused" on a single-master kubeadm cluster (K8s 1.12, one GCE VM, etcd as a static pod); API server and etcd had restarted 183 times. A kubelet restart helped briefly and a fix was announced on Twitter, then it broke again. A full `terraform destroy` and rebuild (about 30 min) brought the same problem back. `docker ps -a` showed etcd living 1.5–2 min before SIGTERM: its liveness probe (`etcdctl get foo`, `failureThreshold: 8`, `timeoutSeconds: 15`) failed and kubelet restarted a healthy etcd. Removing the probe from the kubeadm manifest fixed it; one worker on 1.11.3 vs 1.12.1 was a side finding. Lessons: monitor single masters, a maintenance page, verify before drastic action.
- **Placement:** L3, kubernetes; topics `kubeadm-cluster`, `k8s-troubleshooting`, `cka-exam`.
- **Decision points:**
  1. API refused: restart kubelet and announce "fixed" (*real*) / look at restart counts and container lifetimes first.
  2. Rebuild the cluster from Terraform (*real, 30 min, same result*) / read `crictl ps -a`/`docker ps -a`, kubelet logs, the static pod manifest in `/etc/kubernetes/manifests/`.
  3. etcd killed every 2 min: hunt for disk/network issues / check the liveness probe and its thresholds.
  4. Communicate: one honest status update, not a premature "resolved".
- **Practice:** iximiuz "Recover a broken static control-plane pod"; iximiuz "Take and restore an etcd snapshot"; SadServers "Lisbon: etcd SSL certificate troubles".

### 22. Proxmox VE two-node cluster breaks after changing one node's IP
- **Source:** "[SOLVED] Cluster broken after changing 1 of 2 nodes IP - VMs not starting for no quorum", Proxmox Support Forum, 2023-06-04, https://forum.proxmox.com/threads/cluster-broken-after-changing-1-of-2-nodes-ip-vms-not-starting-for-no-quorum-please-help.128377/ (opened). **Medium** (author-confirmed fix; no staff explanation).
- **Incident:** The author changed node faxmox's IP and edited `corosync.conf` on both nodes. Quorum was lost, VMs would not start, the web shell failed with code 1006 (SSH still worked). faxmox: corosync up but alone, "link: host: 2 link: 0 is down", 1 of 2 votes. FaxmoxOUT: corosync failed, `pvecm status` "Cannot initialize CMAP service", config version 2 vs 6 on the other node. Copying corosync files across did not help; deleting corosync config on one node restored local VMs but the nodes stayed apart ("401: No ticket"). Final fix: copy `/etc/pve/corosync.conf` and `/etc/corosync/*` back from the other node, `pvecm updatecerts --force` on both, reboot.
- **Placement:** L3, cloud; topics `proxmox-ve`.
- **Decision points:**
  1. Before: change a node IP by editing files on one node at a time / follow the documented procedure, bump `config_version`, keep a backup of `/etc/pve/corosync.conf`.
  2. No quorum, VMs down: `pvecm expected 1` to start VMs now (state the risk) / compare `pvecm status` and `corosync-cfgtool -s` on both nodes.
  3. Config versions differ (2 vs 6): copy blindly / pick the newer correct file, distribute, `pvecm updatecerts --force`.
  4. Long-term: a QDevice for two-node clusters.
- **Practice:** no Proxmox site in `practice.json` yet (gap); closest: iximiuz "Configure basic routing between two networks".

### 23. Healthchecks.io, 1–2 November 2025: HAProxy tarpit exhausts connection slots
- **Source:** "Post-mortem: Outage on November 1", Healthchecks.io blog, https://blog.healthchecks.io/2025/11/post-mortem-outage-on-november-1/ (opened). Strong.
- **Incident:** From 23:24 UTC one misconfigured client's pings for a single check rose from 10 to a sustained 300 req/s. HAProxy rate limiting used `tarpit` (hold the request 1 s, then 429); the client did not slow down, held sockets piled up, connection slots ran out and legitimate requests were rejected. At 23:39 one load balancer was dropped from DNS, moving load onto the others. Alerts woke the author at 00:11; Netdata socket graphs showed the problem. 01:06: blocked the client's IPv4 address and IPv6 /64, recovery. Later: immediate 429 instead of tarpit, then `deny`; `timeout http-request 5s`; higher `maxconn`; rate limits on all ping domains; an alert on frontend sessions well below `maxconn`; better logs.
- **Placement:** L3, security; topics `crowdsec-fail2ban`, `proxy-problems`.
- **Decision points:**
  1. Intermittent timeouts, CPU fine: add servers / look at open sockets and HAProxy session counts vs `maxconn`.
  2. One client is the source: tarpit it harder (*real, made it worse*) / block the IP and /64 at the edge (*real fix*).
  3. Rate-limit design: answer 429 immediately; set request timeouts against slowloris.
- **Practice:** ProLUG "fail2ban with log monitoring lab"; `crowdsec-playground`; Killercoda "Devopsify: find the 502/503 cause on a proxy".

### 24. Wikimedia Toolforge, 12 June 2024: Kyverno overloads the Kubernetes API
- **Source:** "Incidents/2024-06-12 WMCS toolforge k8s control plane", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2024-06-12_WMCS_toolforge_k8s_control_plane (opened). Strong.
- **Incident:** At 16:35 UTC a `maintain-kubeusers` change started a large, slow rename of many resources. Kyverno's resource limits had been lifted around 14:00 after frequent Kyverno pod deaths; together this let Kyverno overload the API server. Running tools mostly kept serving, but nothing could be created or changed for about 38 minutes. Responders removed Kyverno policies (16:44), resized control nodes 4→8 CPUs (16:50), saw kubelets report "node not found" and a failing registry admission webhook (17:00), fixed the webhook config, and forced workloads onto the healthy control-7 node (17:09). Actions: fix the HAProxy health check that kept sending to unresponsive API nodes, load-test Kyverno before deploying, verify policy namespaces, scale CoreDNS.
- **Placement:** L3, kubernetes; topics `k8s-security`, `k8s-architecture`.
- **Decision points:**
  1. API slow right after a mass change: scale API servers only / look at which client floods the API (audit log, apiserver metrics) and pause it.
  2. Admission webhooks/policies failing closed: delete the policy engine / remove the policies temporarily (*real*) with a note to restore them.
  3. Load balancer keeps sending to a dead API node: fix the health check to probe `/readyz`.
- **Practice:** iximiuz "Roll out Pod Security Standards across namespaces"; iximiuz "Troubleshoot RBAC for a failing Deployment".

---

## L4 Senior/Lead

### 25. Cloudflare, 2015: "the story of one latency spike" (tcpdump, SystemTap, tcp_rmem)
- **Source:** "The story of one latency spike", Cloudflare blog, 2015-11-19, https://blog.cloudflare.com/the-story-of-one-latency-spike/ (opened). Strong.
- **Incident:** A customer saw rare HTTP requests taking about 30 s; in tests about 5 of thousands took up to 1000 ms, NGINX showed nothing slow. Ping to the router was flat at ~20 ms, but ping to a server behind it peaked at 1.868 s, so the delay was inside the server. tcpdump showed an ICMP reply leaving about 1.3 s after the request arrived. SystemTap traced the stall to `net_rx_action` and then `tcp_collapse`: large receive buffers (`tcp_rmem` max 32 MiB) full of small packets were being collapsed under memory pressure, stalling packet processing. 2 MiB removed the stalls; Cloudflare settled on 4 MiB as a throughput compromise (net_rx_action max 23 ms → 3 ms).
- **Placement:** L4, network; topics `packet-capture`, `network-speed`, `kernel-boot`.
- **Decision points:**
  1. "Rare 30 s requests" with clean app logs: tune NGINX / bisect the path with ping/mtr to find which hop adds delay.
  2. Delay is on the host: capture both sides with `tcpdump -ttt` and compare arrival vs reply.
  3. Kernel stall: copy sysctls from a blog / measure with tracing, change one sysctl on a canary, roll out.
- **Practice:** Killercoda "KubeDojo: network debugging with tcpdump"; Killercoda "Network latency triage"; `wireshark-samples`.

### 26. Sentry, 20 July 2015: Postgres transaction-ID wraparound stops all writes
- **Source:** "Transaction ID Wraparound in Postgres", Sentry blog, 2015-07-23, https://blog.sentry.io/transaction-id-wraparound-in-postgres/ (opened). Strong.
- **Incident:** Sentry's primary Postgres stopped accepting writes for most of a US working day; the app was pointed at read replicas so reads continued. Cause: XID wraparound protection (Postgres halts writes with under one million XIDs left); autovacuum had been tuned too conservatively (high `autovacuum_freeze_max_age`, 3 workers, high cost delay) for their write load. They let running autovacuums finish, failed over to bigger hardware, flushed the event backlog, and considered single-user mode but feared losing ~3 hours of progress. Statistics showed every table vacuumed except one large mapping table; they truncated it (non-critical, recoverable data) and were back about five minutes later. Follow-ups: more aggressive autovacuum settings, splitting databases, new hardware.
- **Placement:** L4, data; topics `db-incidents`.
- **Decision points:**
  1. Writes fail, reads fine: restart Postgres (does not help) / read the log for wraparound warnings; check `age(datfrozenxid)`.
  2. Cancel autovacuum to "free resources" / let it run, watch progress in `pg_stat_progress_vacuum`/stats.
  3. One huge table left: wait hours more / truncate non-critical data after confirming it can be rebuilt (*real*); get sign-off.
  4. After: alert on XID age long before the limit.
- **Practice:** `postgres-playground` "Transactions and locking"; SadServers "Luxor: PostgreSQL analytics queries crawl".

### 27. Wazuh: no new alerts since 4 October (1000/1000 shards)
- **Source:** "No new alerts since october 4th, total shards 1000/1000", wazuh/wazuh-dashboard-plugins #3669, GitHub, 2021-11-01, https://github.com/wazuh/wazuh-dashboard-plugins/issues/3669 (opened). Strong (maintainer explanation).
- **Incident:** A single-server Wazuh 4.2.4 (Elasticsearch/Kibana 7.10.2) stopped showing alerts after 4 October; indexing was rejected with "this action would add [2] total shards, but this cluster currently has [1000]/[1000] maximum shards open" and Kibana could not create the daily monitoring index. The reporter's curl checks first returned "Empty reply from server" because they used HTTP and wrong credentials. Maintainer: the default limit is 1000 shards per node. Options: delete old indices with a retention (ILM/ISM) policy, add nodes, set `index.number_of_shards: 1` in the Filebeat template and reload it, or (not recommended) raise the limit. The reporter deleted `wazuh-statistics-2021*` indices and alerts resumed.
- **Placement:** L4, security; topics `wazuh-siem`, `wazuh`.
- **Decision points:**
  1. SIEM quiet for a month: "nothing happened" / check the newest index date and Filebeat/indexer logs.
  2. Shard limit: raise to 5000 and move on / delete or roll up old indices and add a retention policy.
  3. Template: one primary shard per daily index on a single node.
  4. After: alert on "no alerts received in N hours".
- **Practice:** `wazuh-poc-guide` "Detect an SSH brute-force attack"; `opensearch-playground`.

### 28. Loki on EKS: slow queries and lost logs fixed by changing what is ingested
- **Source:** "Loki performance and missing logs issues", Grafana Community Forums, 2024-07-30 (author update 2024-11-04), https://community.grafana.com/t/loki-performance-and-missing-logs-issues/127458 (opened). Medium (author-confirmed for performance; missing-log part not closed).
- **Incident:** Loki 3.1 in simple-scalable mode on EKS 1.28 (5 read/write/backend replicas, S3, TSDB v13, promtail, ~50 GB/day). A trace_id "needle" query pegged CPU and 30-day queries timed out; promtail got HTTP 429 and some lines never arrived; ingesters logged ingestion-rate-limit errors for tenant "fake". Tuning `limits_config`, caches, retention, stream sharding and structured metadata, and scaling nodes up, cleared the rate-limit errors but not all loss. In November the author reported that leaner log lines and fewer labels solved most performance problems, and that no setting helps much while read and write share nodes.
- **Placement:** L4, observability; topics `logs-loki`, `grafana-loki-ops`.
- **Decision points:**
  1. 429 at promtail: raise every limit / read which limit (per-stream, ingestion rate) and look at label cardinality first.
  2. Slow needle query: more replicas / use structured metadata or line filters, shorter time range.
  3. Fix the source: fewer labels, smaller lines (*real*); separate read and write nodes.
- **Practice:** Grafana `logql-simulator`; Killercoda "Grafana Labs: Loki getting started"; iximiuz "Observability on-call: six tickets (Prometheus, Loki, Jaeger)".

### 29. Wikimedia, 9 October 2024: a maintenance script creates 2k NetworkPolicies, Calico falls over
- **Source:** "Incidents/2024-10-09 calico-codfw", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2024-10-09_calico-codfw (opened). Strong.
- **Incident:** 05:01–06:10 UTC: uncached traffic (logged-in users, edits, API) saw latency and errors in the primary datacenter. An operator ran a transcode maintenance script through the new `mwscript-k8s` tool; each invocation deploys a full Helm release, producing close to 2k Calico NetworkPolicies and 1791 jobs in the namespace; ConfigMaps in etcd roughly doubled (6k → 12k). Calico controllers and typha hit resource limits and failed, calico-node pods left rotation, API calls timed out. Responders raised Calico limits via helmfile; 212 calico-node pods were ready by 06:07 (unclear whether the limit change or the redeploy fixed it). Durable fix tracked: one shared NetworkPolicy for scripts, concurrency limits for mwscript-k8s.
- **Placement:** L4, kubernetes; topics `k8s-networking`, `helm-kustomize`, `platform-engineering`.
- **Decision points:**
  1. Errors + KubernetesCalicoDown: restart all calico-node pods / find what changed object counts (`kubectl get networkpolicy -A | wc -l`, jobs per namespace).
  2. Stop the source (pause the script) vs only raise limits *(real: limits raised)*.
  3. Fail over to the other datacenter? *(discussed, not needed)*.
  4. Platform design: self-service tools need quotas and shared resources.
- **Practice:** iximiuz "Restrict pod traffic with NetworkPolicy"; `helm-playground`; `network-policy-editor`.

### 30. Wikimedia Cloud VPS, 28–29 September 2023: a package cleanup removes the DHCP client
- **Source:** "Incidents/2023-09-29 CloudVPS vms losing network connectivity", Wikimedia Wikitech, https://wikitech.wikimedia.org/wiki/Incidents/2023-09-29_CloudVPS_vms_losing_network_connectivity (opened). Strong.
- **Incident:** A Puppet package-cleanup change merged 11:07 UTC on 28 Sep removed `isc-dhcp-client` from bullseye VMs; as leases expired VMs lost networking. Toolforge, PAWS, Quarry and the external proxies went down; the monitoring VMs failed too, so no alerts fired; NFS clients hung. Users reported on IRC from 04:14; Alertmanager was noticed down at 07:06; `dhclient` missing and apt logs pointing at Puppet were found by 07:18; revert at 07:23. Puppet could not run, so admins fixed VMs by hand and by script, then rebooted NFS servers, Kubernetes workers and grid nodes; all services back 11:46 on 29 Sep. Actions: fix paging, meta-monitoring for the monitoring stack, a virsh-console cookbook, NFS that recovers without reboots.
- **Placement:** L4, sre; topics `ansible-practice`, `ansible`, `prometheus-alertmanager`, `network-problems`.
- **Decision points:**
  1. Users report outages, no alerts: trust silence / check whether monitoring itself is up (*real gap*).
  2. VM unreachable: rebuild it / console in and check `ip a`, lease, `journalctl`, `/var/log/apt/history.log` (*real*).
  3. Revert merged but hosts cannot reach the config server: wait for the agent / fix out-of-band (console script) then let config management run.
  4. After: stage package removals on a canary group; meta-monitoring ("deadman" alert).
- **Practice:** Killercoda "Dev Bench: apt and dpkg"; Killercoda "Ansible 101 to 103 scenarios"; `alertmanager-routing-tree`.

---

## Reserves (opened, not in the 30)

- Resend, 21 Feb 2024: local migration pointed at production dropped all tables; first restore used the wrong backup timestamp; ~12 h outage. https://resend.com/blog/incident-report-for-february-21-2024 (strong; topics `db-incidents`, `devops-day-to-day`; good L1/L2 swap-in).
- Slack, 12 May 2020: HAProxy slot-sync program exited when the fleet exceeded N×M slots; scale-down left too few valid backends; rolling HAProxy restart. https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/ (strong; `proxy-problems`, `deployment-patterns`).
- Grafana Labs, 19 Jul 2019: pod priority preemption cascade evicted all Cortex ingesters. https://grafana.com/blog/2019/07/24/how-a-production-outage-was-caused-using-kubernetes-pod-priorities/ (strong; `k8s-scheduling-storage`).
- loveholidays, Feb 2020: conntrack table full after halving node RAM and doubling connections. https://deploy.live/blog/kubernetes-networking-problems-due-to-the-conntrack/ (strong; `k8s-networking`, `kernel-boot`).
- Wikimedia Prometheus, 5 May 2023: corrupted WAL copied during OS migration; Prometheus down 8 h, nobody paged. https://wikitech.wikimedia.org/wiki/Incidents/2023-05-05_prometheus_down_in_ulsfo_and_eqsin (strong; `prometheus-alertmanager`).
- Wikimedia MariaDB password leak, 16 Jun 2022: debug `print` exposed DB credentials ~2 h; partly manual rotation took 60–90 min. https://wikitech.wikimedia.org/wiki/Incidents/2022-06-16_MariaDB_password_leak (strong; `vault-sso`, `incident-note`).
- Wikimedia mw-on-k8s, 9 Aug 2023: chart default switched to cert-manager certificates, wrong TLS cert served, ~1% errors. https://wikitech.wikimedia.org/wiki/Incidents/2023-08-09_mw-on-k8s_outage_due_to_wrong_tls_cert (strong but thin on which CA; `k8s-onprem-edge`, `private-ca`).
- tj-actions/changed-files, 14–15 Mar 2025: tags repointed to code that dumped runner secrets to logs. https://github.com/advisories/GHSA-mrrh-fwg8-r2c3 (strong; `gitops-argocd`).
- Headscale #2182 (Oct 2024): after 0.23 upgrade nodes offline; reporter fixed with `listen_addr :443` for TLS-ALPN-01. https://github.com/juanfont/headscale/issues/2182 (medium; `vpn-mesh`).
- Harbor #22222 (Jul 2025, open): Harbor's own CI hit Docker Hub unauthenticated 429s; PR routes pulls via its proxy cache. https://github.com/goharbor/harbor/issues/22222 (medium, not an incident write-up; `harbor-ops`).
- Wazuh mailing list (May 2021): agent "never connected" because agent < 4.0 vs manager; reinstalling latest fixed it. https://groups.google.com/g/wazuh/c/DmlrOS3VXt8 (medium; `wazuh`).
- Healthchecks.io, 27 Oct 2019: Hetzner vSwitch loss on one LB; script pulled it from DNS. https://blog.healthchecks.io/2019/10/incident-report-27-october-2019/ (root cause not found).

Rejected after reading: Traefik Community "502 Bad Gateway solved" (#2947, cause only a guess), Proxmox threads 143517/137750/134232 (no root cause), fail2ban discussion #3631 (never confirmed), Tailscale #16820 (unsupported setup, closed), Docker forum 150233 (no confirmation), Docker forum Swarm 98579 (no confirmation), GitLab infra issues #17502/#18490 (stub pages). Medium posts on k8s.af (MindTickle, Skyscanner, JW Player) returned 403 and were not used.

## Uncovered topics hit (58 of 74)

cloud-concepts, aws-platform, incident-note, windows-macos, kernel-boot, port-ownership, sockets-ports,
network-problems, host-firewall, docker-firewall, uptime-checks, devops-day-to-day, git-team, jenkins,
apache-vhosts, site-down-walk, apache-81-444, ansible-practice, journald-logs, docker-networking,
k8s-workloads, deployment-patterns, proxy-problems, k8s-scheduling-storage, k8s-architecture, disk-io,
backup-tools, db-incidents, traefik-deep-dive, docker-engine, dokploy-operations, traefik, dokploy,
swarm-in-practice, swarm, container-hardening, dockerfile, gitops-argocd, gitlab-ci-harbor, terraform,
terraform-opentofu, kubeadm-cluster, k8s-troubleshooting, cka-exam, proxmox-ve, crowdsec-fail2ban,
k8s-security, packet-capture, network-speed, wazuh-siem, wazuh, logs-loki, grafana-loki-ops,
k8s-networking, helm-kustomize, platform-engineering, ansible, prometheus-alertmanager.

Still uncovered after the 30 (16): aws-iam-ec2, private-ca, aws-vpc-alb, harbor-ops, vault-sso,
object-storage-minio, vpn-mesh, k8s-onprem-edge, slo, traefik-legacy-routes, learn-from-tickets,
oss-toolbox, and the four milestone nodes (milestone-junior/mid/senior/lead), which are exit tests rather
than incident topics. Reserves cover harbor-ops, vault-sso, vpn-mesh, k8s-onprem-edge and private-ca
with weaker sources. Searches for a first-hand ALB keep-alive 502 post-mortem, a leaked-AWS-key
post-mortem and a MinIO incident found only tutorials or unverified anecdotes.
