# 20 — macOS Troubleshooting

macOS is BSD-based: most Linux habits (`ps`, `top`, `lsof`, `df`, `ping`,
`traceroute`, `dig`, `ssh`) work, but storage (APFS/`diskutil`), services
(`launchd`), logs (unified `log`) and networking config differ. Sample outputs
included with how to read them.

---

## 1. System identification

```bash
sw_vers                            # macOS version
system_profiler SPHardwareDataType # hardware overview (chip, RAM, serial)
sysctl -n machdep.cpu.brand_string # CPU name ("Apple M3 Pro")
sysctl -n hw.memsize               # RAM in bytes
sysctl hw.ncpu hw.perflevel0.physicalcpu   # core counts (P/E cores on Apple Silicon)
uname -a                           # Darwin kernel version
uptime                             # load average — same reading as Linux
arch                               # arm64 (Apple Silicon) vs x86_64 (Intel) ★
```
```
$ sw_vers
ProductName:    macOS
ProductVersion: 15.5
BuildVersion:   24F74
```
`arch` matters constantly: x86-only binaries need Rosetta 2
(`softwareupdate --install-rosetta`), Homebrew lives in `/opt/homebrew` on
arm64 vs `/usr/local` on Intel — the source of most "works on my old Mac" issues.

---

## 2. Storage & disk

### `diskutil` — the lsblk/fdisk of macOS
```bash
diskutil list                      # ★ all disks, containers, volumes
diskutil info disk3s1              # details of one volume (free space, mount point)
diskutil apfs list                 # APFS containers: who shares which space
diskutil verifyVolume /            # filesystem check (read-only)
diskutil repairVolume /Volumes/Data
diskutil unmountDisk /dev/disk4 ; diskutil eject /dev/disk4
diskutil mount disk3s2             # mount a volume that didn't auto-mount
```
```
$ diskutil list
/dev/disk3 (synthesized):
   #:                type name           size       identifier
   0:  APFS Container Scheme -           +994.7 GB  disk3
   1:  APFS Volume Macintosh HD          11.2 GB    disk3s1
   2:  APFS Volume Macintosh HD - Data   680.9 GB   disk3s5
   3:  APFS Volume Preboot               6.4 GB     disk3s2
```
Key concept: APFS volumes in one container **share free space** — `df` for any
of them shows the same "Available". The read-only system volume (`Macintosh HD`)
is sealed; your files live on `...- Data`.

### Space usage
```bash
df -h                              # as Linux; APFS shows shared container free space
du -sh ~/* 2>/dev/null | sort -rh | head    # biggest home dirs
du -sh /private/var/log /Library/Caches ~/Library/Caches
ncdu ~                             # if installed (brew install ncdu)
```
macOS-specific space eaters: local Time Machine snapshots, `~/Library/Caches`,
old iOS device backups (`~/Library/Application Support/MobileSync/Backup`),
Xcode DerivedData (`~/Library/Developer/Xcode/DerivedData`), Docker Desktop's
`Docker.raw`.

**"Disk full but my files don't add up"** — usually local snapshots:
```bash
tmutil listlocalsnapshots /                      # snapshot list
tmutil deletelocalsnapshots 2026-08-08-120000    # delete one
tmutil thinlocalsnapshots / 20000000000 4        # free ~20 GB of snapshots
```

### Disk performance / health
```bash
iostat -w 1                        # basic disk throughput per second
sudo fs_usage -w -f filesys pid 1234    # ★ live file operations of a process
                                        #   (macOS answer to strace-for-files)
system_profiler SPNVMeDataType | grep -A2 "S.M.A.R.T"   # SMART verified?
smartctl -a /dev/disk0             # if smartmontools installed (brew)
```

---

## 3. Processes & performance

```bash
ps aux | head ; ps aux | grep -i [s]afari      # as Linux
top -o cpu                         # sort by CPU (macOS top sorts by pid by default!)
top -o mem
top -l 1 | head -12                # one snapshot (for scripts)
htop                               # if installed — shows P/E cores nicely
```
```
$ top -l 1 | head -8
Processes: 612 total, 3 running, 609 sleeping
Load Avg: 2.31, 2.05, 1.98
CPU usage: 8.42% user, 4.11% sys, 87.45% idle
PhysMem: 30G used (2431M wired, 9G compressor), 1522M unused
```
Reading PhysMem: `compressor` = RAM holding compressed pages — a large,
**growing** compressor plus frequent swap = memory pressure. The honest signal:
```bash
memory_pressure                    # "System-wide memory free percentage: 71%"
vm_stat 1                          # pageouts column increasing = real pressure ★
sysctl vm.swapusage                # swap used
```
`vm_stat` counts are in **16384-byte pages** on Apple Silicon (4096 on Intel) —
multiply accordingly.

Hung / misbehaving apps:
```bash
sample 1234 5                      # 5-second CPU sample of a process → call stacks
sudo spindump 1234                 # deeper hang report (needs root)
sudo fs_usage pid 1234             # what files/sockets it touches live
lsof -p 1234                       # open files (as Linux)
kill -9 1234 ; killall "Safari"    # killall matches app names on macOS
launchctl kickstart -k system/com.example.daemon   # restart a managed daemon
caffeinate -i long_job.sh          # prevent sleep while a job runs ★ (laptops sleep
                                   #   mid-job — a classic "it stopped overnight")
pmset -g assertions                # what is currently preventing sleep
```

---

## 4. Services — launchd (the systemd of macOS)

```bash
launchctl list                            # loaded jobs for current user
sudo launchctl list                       # system daemons
launchctl list | grep -v "^-"             # only jobs that have a PID (running)
launchctl print system/com.openssh.sshd   # ★ detailed status of one service
sudo launchctl bootstrap system /Library/LaunchDaemons/com.example.plist   # load
sudo launchctl bootout system/com.example.daemon                           # unload
launchctl kickstart -k system/com.example.daemon                           # restart
plutil -lint /Library/LaunchDaemons/com.example.plist   # ★ syntax-check a plist
                                                        #   before loading it
```
```
$ launchctl list | head -4
PID     Status  Label
812     0       com.docker.helper
-       0       com.apple.SafariHistoryServiceAgent
-       78      com.example.badjob        ← nonzero Status = last exit code: it's failing
```
Where jobs live: `~/Library/LaunchAgents` (user), `/Library/LaunchAgents`,
`/Library/LaunchDaemons` (system, run as root), `/System/Library/...` (Apple's).
Homebrew services are launchd jobs too:
```bash
brew services list                 # started/stopped/error per service
brew services restart postgresql@16
```

---

## 5. Network

```bash
ifconfig en0                       # addresses (en0 = WiFi on laptops, first NIC otherwise)
ipconfig getifaddr en0             # ★ just my IPv4 (macOS ipconfig ≠ Windows ipconfig!)
ipconfig getpacket en0             # DHCP lease details (server, router, DNS)
networksetup -listallhardwareports # map devices (en0/en1...) to WiFi/Ethernet
networksetup -getdnsservers Wi-Fi  # DNS config of a network service
networksetup -setdnsservers Wi-Fi 1.1.1.1 8.8.8.8   # change it ("Empty" resets to DHCP)
networksetup -getwebproxy Wi-Fi    # proxy settings (corp machines!)
route -n get default               # ≈ ip route get: default gateway + interface
netstat -rn                        # routing table
netstat -an | grep LISTEN          # listeners (or: sudo lsof -iTCP -sTCP:LISTEN -nP ★)
sudo lsof -i :8080                 # who owns a port (no ss on macOS)
ping -c 4 host ; traceroute host   # as Linux
mtr host                           # via brew install mtr (run with sudo)
nc -zv host 443                    # port test, as Linux
scutil --dns | head -20            # ★ the REAL resolver config (per-domain resolvers,
                                   #   VPN split-DNS shows up here)
scutil --proxy                     # effective proxy config
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder   # ★ flush DNS cache
dscacheutil -q host -a name example.com    # resolve the way apps do (like getent)
dns-sd -B _ssh._tcp                # browse Bonjour/mDNS services
wdutil info                        # WiFi diagnostics (rssi, channel, noise) — sudo
```
```
$ scutil --dns | head -8
DNS configuration
resolver #1
  search domain[0] : corp.internal
  nameserver[0] : 10.0.1.5          ← VPN pushed this resolver
  if_index : 17 (utun3)
  flags    : Request A records
```
Typical Mac issues: VPN leaves stale resolvers/routes (`scutil --dns`,
`netstat -rn | grep utun`), captive-network WiFi (portal not completed),
corporate proxy set per-network-service (`networksetup -getwebproxy`),
firewall: `/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate`,
packet filter rules: `sudo pfctl -sr`.

---

## 6. Logs — the unified log

There's no /var/log/syslog for most things anymore; use `log`:

```bash
log show --last 10m --predicate 'eventMessage CONTAINS[c] "error"' | tail -50
log show --last 1h --predicate 'process == "sshd"'
log show --predicate 'subsystem == "com.apple.TimeMachine"' --last 2h
log stream --predicate 'process == "myapp"'        # ★ live follow (≈ journalctl -f)
log show --last 5m --style compact
log collect --output ~/Desktop/logs.logarchive     # bundle for offline analysis
```
Still-real files: `/var/log/install.log` (installs/updates),
`/var/log/system.log` (some legacy daemons), `~/Library/Logs` +
`/Library/Logs` (app crash reports — `DiagnosticReports/*.ips`).
GUI: Console.app shows the same unified log + crash reports.

Crash reports:
```bash
ls ~/Library/Logs/DiagnosticReports/ | tail        # per-user app crashes
ls /Library/Logs/DiagnosticReports/ | tail         # system daemons
open ~/Library/Logs/DiagnosticReports/MyApp-2026-08-09.ips   # JSON-ish crash dump:
                                                   # "termination reason" + thread stacks
```

---

## 7. Software, security & "app won't run"

```bash
softwareupdate -l                          # available OS updates
softwareupdate -i -a                       # install all (careful: may reboot)
pkgutil --pkgs | tail                      # installed pkg receipts
pkgutil --pkg-info com.example.pkg
brew doctor                                # ★ Homebrew self-diagnosis
brew list --versions | grep openssl
brew services list
xcode-select -p                            # dev tools path ("xcrun: error: invalid
xcode-select --install                     #   active developer path" → reinstall)
```

**"App is damaged / can't be opened / unidentified developer"** — Gatekeeper &
quarantine:
```bash
spctl --status                             # Gatekeeper on?
spctl -a -vv /Applications/MyTool.app      # why it's rejected (unsigned? unnotarized?)
codesign -dv --verbose=2 /Applications/MyTool.app   # signature details
xattr -l ~/Downloads/tool-binary           # look for com.apple.quarantine ★
xattr -d com.apple.quarantine ~/Downloads/tool-binary   # remove it (ONLY for files
                                           # you trust and obtained deliberately)
```

**Permission denied on files that look fine** → TCC privacy layer: System
Settings → Privacy & Security → Full Disk Access (terminals need it to read
Mail/Messages/other apps' data). `sudo` does **not** bypass TCC.

System Integrity Protection state:
```bash
csrutil status                             # "enabled" is normal; explains why even
                                           # root can't touch /System
```

---

## 8. Power, Time Machine & maintenance

```bash
pmset -g batt                              # battery %, source, condition
pmset -g                                   # sleep/hibernate settings
pmset -g log | grep -E "Sleep|Wake" | tail # ★ why did it sleep/wake? (great for
                                           #   "my overnight job died" mysteries)
system_profiler SPPowerDataType | grep -E "Cycle|Condition"
tmutil status                              # Time Machine backup running?
tmutil latestbackup ; tmutil listbackups | tail
tmutil compare -s                          # what changed since last backup
mdutil -s /                                # Spotlight indexing status ("mds" eating
mdutil -E /                                #   CPU? rebuild the index)
sudo periodic daily weekly monthly         # run maintenance scripts manually
networkQuality                             # built-in speed test (macOS 12+) ★
sysdiagnose                                # full diagnostic bundle (what Apple
                                           #   support asks for)
```
```
$ pmset -g batt
Now drawing from 'Battery Power'
 -InternalBattery-0 (id=123456)  84%; discharging; 5:12 remaining
```

---

## Linux ↔ macOS cheat table

| Purpose | Linux | macOS |
|---|---|---|
| List disks | `lsblk` | `diskutil list` |
| FS check/repair | `fsck` | `diskutil verifyVolume` / `repairVolume` |
| Services | `systemctl` | `launchctl` (+ `brew services`) |
| Logs | `journalctl -f` | `log stream`, `log show --last 1h` |
| Trace file access | `strace -e openat` | `sudo fs_usage pid N` |
| Sample a hung app | `gdb`/`perf` | `sample PID`, `spindump` |
| Memory pressure | `free -h`, vmstat | `memory_pressure`, `vm_stat` |
| Who owns a port | `ss -tlnp` | `sudo lsof -iTCP -sTCP:LISTEN -nP` |
| My IP | `ip -br addr` | `ipconfig getifaddr en0` |
| Real DNS config | `resolvectl status` | `scutil --dns` |
| Flush DNS | `resolvectl flush-caches` | `dscacheutil -flushcache` + `killall -HUP mDNSResponder` |
| Route lookup | `ip route get X` | `route -n get X` |
| Speed test | iperf3 | `networkQuality` (built-in) |
| Package verify | `rpm -V` | `pkgutil`, `codesign -dv`, `brew doctor` |
| Snapshots eating disk | LVM snapshots | `tmutil listlocalsnapshots /` |
| Keep-awake for jobs | — | `caffeinate -i cmd` |
