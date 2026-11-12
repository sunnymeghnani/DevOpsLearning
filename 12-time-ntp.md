# 12 — Time & NTP Troubleshooting

Wrong clocks break: **TLS certificates** ("certificate not yet valid"),
**Kerberos/AD auth**, **AWS API calls** (`SignatureDoesNotMatch` / RequestTimeTooSkewed),
2FA/TOTP codes, distributed databases, log correlation, apt/dnf metadata checks.
If auth or signatures fail mysteriously — **check the clock first.**

---

## 1. Status

```bash
timedatectl                             # the one-stop view
```
```
$ timedatectl
               Local time: Sat 2026-08-09 14:22:03 UTC
           Universal time: Sat 2026-08-09 14:22:03 UTC
                 RTC time: Sat 2026-08-09 14:22:04
                Time zone: Etc/UTC (UTC, +0000)
System clock synchronized: yes          ← the key line
              NTP service: active
```
`synchronized: no` + `NTP service: active` = daemon running but can't reach servers.

```bash
date                                    # current time+zone
date -u                                 # UTC (compare with a known-good source)
hwclock --show                          # hardware clock (on-prem; VMs get time from host)
cat /etc/timezone ; ls -l /etc/localtime
timedatectl list-timezones | grep -i kolkata
timedatectl set-timezone Asia/Kolkata
timedatectl set-ntp true                # enable NTP sync
```

## 2. chrony (default on RHEL, Amazon Linux, newer Ubuntu)

```bash
chronyc tracking                        # offset from true time, drift, stratum ★
chronyc sources -v                      # each server: reachable? selected (^*)?
chronyc sourcestats
chronyc makestep                        # force immediate step correction (big skew)
systemctl status chronyd
cat /etc/chrony.conf                    # which servers are configured
```
Reading `chronyc sources`:
```
MS Name/IP address       Stratum Poll Reach LastRx Last sample
^* 169.254.169.123           3    4   377    12   +12us[+15us]
```
- `^*` = currently selected server; `^?` = unreachable
- `Reach 377` (octal) = last 8 polls all succeeded; `0` = nothing getting through
  → firewall blocking **UDP 123** outbound, or wrong server names
- `System time offset` in `chronyc tracking` should be milliseconds or better

## 3. ntpd / systemd-timesyncd (older / minimal systems)

```bash
ntpq -p                                 # peer status ('*' = selected)
ntpstat                                 # sync summary
systemctl status ntpd

timedatectl timesync-status             # systemd-timesyncd detail
systemctl status systemd-timesyncd
cat /etc/systemd/timesyncd.conf
```
⚠️ Only ONE time daemon should run — chronyd, ntpd, and timesyncd conflict.
`ps -e | grep -E "chronyd|ntpd|timesyncd"` — if two show up, disable one.

## 4. Manual checks & one-shot sync

```bash
chronyd -Q 'server pool.ntp.org iburst'  # query offset without changing clock
ntpdate -q pool.ntp.org                  # legacy query-only check
date -s "2026-08-09 14:25:00"            # manual set (last resort, breaks monotonicity)
```

## 5. AWS specifics

- Use the **Amazon Time Sync Service**: server `169.254.169.123` (link-local —
  works without internet access, already default in Amazon Linux chrony.conf).
- `SignatureDoesNotMatch` / `RequestTimeTooSkewed` from AWS CLI/SDK → clock skew
  > 5 min → `chronyc makestep`.
- Containers inherit the **host** clock — fix time on the node, not in the container.

## 6. On-prem specifics

- Dead CMOS battery → clock resets on every power cycle → `hwclock`, replace battery.
- Sync hardware clock after fixing system time: `hwclock --systohc`.
- Firewalled networks: internal NTP servers; verify with `chronyc sources` reach
  and `tcpdump -i any -nn port 123`.
- Windows AD environments: domain machines should sync to DCs (w32tm — see 17-windows.md);
  Kerberos tolerates only 5 min skew by default.
