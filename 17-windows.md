# 17 — Windows Troubleshooting

CMD and PowerShell equivalents of the Linux toolkit — with sample outputs and
how to read them. PowerShell commands (`Get-*`) return objects you can filter
and sort; prefer them in scripts. Run an **elevated** (Administrator) prompt for
anything system-level.

---

## 1. Network

### `ipconfig` — interface addresses (≈ `ip addr`)
```powershell
ipconfig                       # basic IP info per adapter
ipconfig /all                  # + MAC, DHCP server, DNS servers, lease times ★
ipconfig /release && ipconfig /renew    # recycle the DHCP lease
ipconfig /displaydns           # DNS client cache contents
ipconfig /flushdns             # ★ clear DNS cache — first move on stale-DNS issues
Get-NetIPConfiguration         # PowerShell: tidy per-adapter summary
Get-NetIPAddress -AddressFamily IPv4
```
Sample `ipconfig /all` (trimmed) and what to read:
```
Ethernet adapter Ethernet0:
   Description . . . . . . . : Intel(R) 82574L Gigabit
   Physical Address. . . . . : 00-0C-29-3A-BC-01
   DHCP Enabled. . . . . . . : Yes
   IPv4 Address. . . . . . . : 10.0.1.10(Preferred)          ← got a real address?
   Subnet Mask . . . . . . . : 255.255.255.0
   Default Gateway . . . . . : 10.0.1.1                      ← empty = no route out!
   DHCP Server . . . . . . . : 10.0.1.5
   Lease Expires . . . . . . : Sunday, August 10, 2026 9:14  ← expired/renewing loops?
   DNS Servers . . . . . . . : 10.0.1.5, 10.0.1.6            ← wrong DNS = "internet
                                                                broken" for users
```
- Address starting **169.254.x.x** (APIPA) = DHCP failed → link, VLAN, or DHCP
  server problem.
- No Default Gateway → can reach the LAN only.
- `Media State . . . : Media disconnected` → cable/NIC/switch port.

### `ping` — reachability (≈ Linux ping)
```powershell
ping host                      # 4 echoes then stops (Linux pings forever)
ping -t host                   # continuous (Ctrl-C stops; Ctrl-Break shows stats)
ping -n 50 host                # specific count
ping -l 1472 -f host           # payload size + Don't-Fragment → MTU testing
ping -a 10.0.1.20              # also reverse-resolve the name
ping -4 host / ping -6 host    # force IPv4 / IPv6
Test-Connection host -Count 4  # PowerShell version (objects, not text)
```
```
C:\> ping 10.0.1.20
Reply from 10.0.1.20: bytes=32 time=1ms TTL=128
Request timed out.
Reply from 10.0.1.20: bytes=32 time=1ms TTL=128
Reply from 10.0.1.20: bytes=32 time=214ms TTL=128
Ping statistics: Sent = 4, Received = 3, Lost = 1 (25% loss)
```
- Mixed replies + timeouts + wild `time=` swings → loss/congestion → `pathping`.
- `TTL=128` hints the peer is Windows; `TTL=64` Linux; much lower = many hops away.
- `Destination host unreachable` (from **your own** IP) → no route locally;
  (from the gateway's IP) → the router can't route it.
- `Request timed out` → dropped somewhere (or ICMP just blocked — verify with a
  TCP probe below before concluding it's down).

### `Test-NetConnection` — port test (≈ `nc -zv`) ★
```powershell
Test-NetConnection 10.0.1.20 -Port 443
Test-NetConnection host -Port 3389 -InformationLevel Detailed
Test-NetConnection host -TraceRoute
```
```
ComputerName     : 10.0.1.20
RemoteAddress    : 10.0.1.20
RemotePort       : 443
InterfaceAlias   : Ethernet0
SourceAddress    : 10.0.1.10
TcpTestSucceeded : True          ← the line that matters
```
Only when the TCP test fails does the output add a ping (`PingSucceeded`):
`PingSucceeded True` + `TcpTestSucceeded False` → host is up but the **port** is
blocked/closed → service down or firewall. Both False → likely network path.

### `tracert` — path (≈ `traceroute -I`)
```powershell
tracert host
tracert -d host                # skip DNS resolution (much faster)
```
```
  1     1 ms    1 ms    1 ms  10.0.1.1
  2     9 ms    8 ms    9 ms  100.64.0.1
  3     *        *       *    Request timed out.      ← hop hides from ICMP (often fine)
  4    22 ms   21 ms   23 ms  203.0.113.9             ← ...because later hops answer
```
The first hop where latency jumps and **stays** high for all later hops is where
the delay is added.

### `pathping` — tracert + per-hop loss statistics (≈ `mtr`)
```powershell
pathping host                  # traces, then samples each hop (takes minutes)
pathping -q 50 -n host         # 50 queries/hop, no DNS (-n; -d is tracert's flag)
```
```
Computing statistics for 125 seconds...
            Source to Here   This Node/Link
Hop  RTT    Lost/Sent = Pct  Lost/Sent = Pct  Address
  0                                           WS01 [10.0.1.10]
  1    1ms     0/ 100 =  0%     0/ 100 =  0%  10.0.1.1
  2   35ms    20/ 100 = 20%    20/ 100 = 20%  isp-router      ← loss starts here...
  3   36ms    20/ 100 = 20%     0/ 100 =  0%  destination     ← ...and persists to the end
```
Same rule as mtr: loss that appears at a hop **and continues to the destination**
is real; loss only at one middle hop that vanishes afterwards is that router
deprioritizing ICMP.

### Ports, connections, routes, ARP
```powershell
netstat -ano                   # all connections + owning PID (-o) ★
netstat -ano | findstr :443    # filter to one port
netstat -anob                  # + program names (needs admin, slower)
Get-NetTCPConnection -State Listen
Get-NetTCPConnection -LocalPort 443 | Select LocalAddress,State,OwningProcess
route print                    # routing table (≈ ip route)
arp -a                         # ARP cache (≈ ip neigh)
Get-NetAdapter                 # link state/speed of all NICs (≈ ip link)
Get-NetAdapterStatistics       # counters
netsh wlan show wlanreport     # WiFi diagnostics HTML report
netsh winsock reset            # repair corrupted socket stack (reboot after)
netsh int ip reset             # reset TCP/IP stack (reboot after)
```
Reading `netstat -ano` and finding the owner:
```
  Proto  Local Address    Foreign Address   State       PID
  TCP    0.0.0.0:443      0.0.0.0:0         LISTENING   4312
  TCP    10.0.1.10:52011  10.0.2.9:1433     ESTABLISHED 7788
```
```powershell
tasklist /fi "PID eq 4312"     # → which program is PID 4312
```
- `0.0.0.0:443` = listening on all interfaces; `127.0.0.1:443` = local only —
  the classic "works on the server, refused from outside".
- Thousands of `TIME_WAIT` → connection churn; `SYN_SENT` stuck → remote not answering.

### DNS
```powershell
nslookup host                  # basic query
nslookup host 8.8.8.8          # ask a specific server
nslookup -type=mx example.com
Resolve-DnsName host -Type A   # PowerShell, richer output
Resolve-DnsName host -Server 8.8.8.8
Get-DnsClientCache | Where Entry -like "*example*"
Clear-DnsClientCache           # = ipconfig /flushdns
```
```
C:\> nslookup app.example.com
Server:  dc01.corp.local          ← WHO answered (your configured resolver)
Address:  10.0.1.5

Non-authoritative answer:
Name:    app.example.com
Address: 203.0.113.20
```
`Non-authoritative` just means "from cache", not an error. Errors that matter:
`Non-existent domain` (NXDOMAIN — record missing/typo), `DNS request timed out`
(resolver unreachable → firewall/UDP 53), or the wrong `Server:` line entirely
(machine pointed at the wrong DNS — very common after VPN connects).

### Windows Firewall
```powershell
Get-NetFirewallProfile | Select Name,Enabled
netsh advfirewall show allprofiles
Get-NetFirewallRule -Enabled True -Direction Inbound | Where DisplayName -like "*SQL*"
New-NetFirewallRule -DisplayName "App 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
# which rule blocked something? enable + read the drop log:
netsh advfirewall set allprofiles logging droppedconnections enable
Get-Content $env:systemroot\system32\LogFiles\Firewall\pfirewall.log -Tail 20
```

---

## 2. Processes, CPU & memory

### `tasklist` / `taskkill` (≈ ps / kill)
```powershell
tasklist                                  # all processes
tasklist /svc                             # ★ which services run inside which process
tasklist /fi "IMAGENAME eq java.exe"
tasklist /fi "MEMUSAGE gt 500000"         # >500 MB
taskkill /PID 4321 /F                     # ≈ kill -9
taskkill /IM notepad.exe /F /T            # by name, /T = child processes too
```
```
Image Name        PID  Session Name  Session#  Mem Usage
java.exe         4321  Services         0      1,842,120 K   ← ~1.8 GB
sqlservr.exe     1988  Services         0      6,204,844 K
```

### `Get-Process` — the better view
```powershell
Get-Process | Sort CPU -Descending | Select -First 10       # top CPU ★
Get-Process | Sort WS  -Descending | Select -First 10       # top memory
Get-Process -Id 4321 | Select Path,StartTime,Threads,Handles
Get-Process -Name java | Stop-Process -Force
Get-CimInstance Win32_Process -Filter "ProcessId=4321" |
  Select CommandLine                       # ★ full command line of a process
```
```
Handles  NPM(K)  PM(K)    WS(K)   CPU(s)    Id  ProcessName
   1234      98  812000  1843200  9214.44  4321 java
```
Column meanings: `WS(K)` working set = real RAM in KB (≈ RSS); `PM(K)` private
committed memory; `CPU(s)` **cumulative** CPU seconds since start (large number
alone ≠ busy *now* — sample twice and compare); `Handles` steadily climbing
across samples = handle leak.

### CPU / memory right now
```powershell
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5
Get-Counter '\Memory\Available MBytes'
Get-Counter '\PhysicalDisk(_Total)\Avg. Disk Queue Length'   # ≈ iostat queue
Get-Counter '\Processor(_Total)\% Interrupt Time'            # high = driver issue
wmic cpu get loadpercentage
Get-CimInstance Win32_OperatingSystem |
  Select FreePhysicalMemory,TotalVisibleMemorySize            # KB
taskmgr                                    # GUI; Performance tab
resmon                                     # ★ Resource Monitor: per-process disk
                                           #   and network I/O — Linux has no
                                           #   single tool this convenient
perfmon                                    # long-term counter graphs/logs
```
```
Timestamp                 CounterSamples
2026-08-09 14:10:02       \\ws01\processor(_total)\% processor time : 87.42
```
Sustained > 85% → find the process (`Get-Process | Sort CPU`); also check
`% Interrupt Time` > 15% (bad driver/hardware) and single-core saturation in
Task Manager's per-core view (one core pinned = single-threaded bottleneck).

Memory: `Available MBytes` < ~10% of RAM → pressure; watch hard page faults:
`Get-Counter '\Memory\Pages/sec'` sustained high while disk is busy = thrashing.

---

## 3. Services (≈ systemctl)

```powershell
Get-Service spooler
Get-Service | Where Status -eq "Stopped" | Where StartType -eq "Automatic"
                                           # ★ should-be-running-but-isn't list
Restart-Service spooler -Verbose
Set-Service spooler -StartupType Automatic
sc.exe query spooler                       # low-level state (in PowerShell plain "sc" is Set-Content)
sc.exe qc spooler                          # ★ config: binary path, account, deps
sc.exe queryex spooler                     # + PID (to correlate with tasklist)
net start / net stop spooler               # legacy control
```
```
PS> Get-Service | Where {$_.Status -eq "Stopped" -and $_.StartType -eq "Automatic"}
Status   Name        DisplayName
------   ----        -----------
Stopped  MSSQLSERVER SQL Server (MSSQLSERVER)     ← this should worry you
```
```
C:\> sc qc MSSQLSERVER
  BINARY_PATH_NAME : "C:\Program Files\...\sqlservr.exe"
  SERVICE_START_NAME : CORP\svc-sql        ← service account: expired password /
                                              locked account = service won't start
  DEPENDENCIES     : KEYISO
```
Service fails to start → System event log has the exact error
(`Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Service Control Manager'} -MaxEvents 10`).
Frequent causes: service-account password expired, dependency service stopped,
port already taken, missing file on the BINARY_PATH.

---

## 4. Disk & filesystem

```powershell
Get-Volume                                 # ≈ df -h (health + free space)
Get-PSDrive -PSProvider FileSystem
Get-Disk ; Get-Partition                   # ≈ lsblk
Get-PhysicalDisk | Select FriendlyName,MediaType,HealthStatus   # SSD/HDD + health ★
chkdsk C:                                  # read-only check
chkdsk C: /f                               # fix (C: schedules at next reboot)
chkdsk D: /f /r                            # + locate bad sectors (slow)
fsutil dirty query C:                      # is the volume flagged dirty?
defrag C: /A                               # fragmentation analysis (HDD)
cleanmgr                                   # GUI cleanup; storage settings in Win11
```
```
PS> Get-Volume
DriveLetter FileSystem HealthStatus SizeRemaining     Size
C           NTFS       Healthy            12.1 GB   250 GB    ← ~5% free: NTFS+VSS
D           NTFS       Healthy           801.2 GB     1 TB       want 10-15% free
```
What's eating space (≈ `du -sh`):
```powershell
Get-ChildItem C:\ -Directory | ForEach-Object {
  [pscustomobject]@{ Dir=$_.FullName
    GB=[math]::Round((Get-ChildItem $_.FullName -Recurse -File -EA SilentlyContinue |
        Measure-Object Length -Sum).Sum/1GB,2) } } | Sort GB -Descending | Select -First 10
```
Windows-specific space hogs: `C:\Windows\Installer`, WinSxS (clean with
`DISM /Online /Cleanup-Image /StartComponentCleanup`), shadow copies
(`vssadmin list shadowstorage`), hiberfil.sys (`powercfg /h off`), pagefile,
and forgotten user Downloads/Recycle Bins.

Shares and open files:
```powershell
net use                                    # mapped drives (≈ mount for SMB)
Get-SmbSession ; Get-SmbOpenFile           # who has files open on MY shares
Get-SmbConnection                          # my outbound SMB connections + dialect
Test-NetConnection fileserver -Port 445    # SMB reachability
```

---

## 5. System info, events & logs

### `systeminfo` — uname + dmidecode + uptime in one
```powershell
systeminfo | findstr /b /i /c:"OS Name" /c:"OS Version" /c:"System Boot Time" /c:"Total Physical" /c:"Available Physical"
```
```
OS Name:                   Microsoft Windows Server 2022 Standard
OS Version:                10.0.20348 N/A Build 20348
System Boot Time:          8/9/2026, 3:12:44 AM       ← unexpected reboot overnight?
Total Physical Memory:     32,768 MB
Available Physical Memory: 2,014 MB                   ← 6% free = memory pressure
```
Each `/c:"…"` is one whole phrase and `/b` matches only at the start of a line
(so `BIOS Version` is not hit). A plain `findstr /i "OS Name …"` treats every
word separately and also prints Host Name, BIOS Version, Time Zone, Virtual Memory
and more.
```powershell
Get-ComputerInfo | Select OsName,OsVersion,OsLastBootUpTime,CsModel
(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime   # uptime ★
```

### Event logs (≈ journalctl) ★
```powershell
Get-WinEvent -LogName System -MaxEvents 30
Get-WinEvent -FilterHashtable @{LogName='System';Level=1,2} -MaxEvents 30    # crit+err
Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddHours(-2)}
Get-WinEvent -FilterHashtable @{LogName='System';Id=6008}          # unexpected shutdowns
Get-WinEvent -FilterHashtable @{LogName='System';Id=41}            # kernel-power (crash/power loss)
Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625} -MaxEvents 20    # failed logons
Get-WinEvent -FilterHashtable @{LogName='Security';Id=4740}        # account lockouts ★
Get-WinEvent -ListLog * | Where RecordCount -gt 0 | Sort RecordCount -Descending
eventvwr                                   # GUI
```
```
TimeCreated          Id LevelDisplayName Message
8/9/2026 3:11:58   6008 Error            The previous system shutdown at 3:02:11 AM
                                         on 8/9/2026 was unexpected.
8/9/2026 3:14:22   7034 Error            The MyApp service terminated unexpectedly.
                                         It has done this 3 time(s).
```
Event IDs worth memorizing: **6008** unexpected shutdown, **41** kernel-power,
**7034/7031** service crashed, **7000/7001** service failed to start,
**4625** logon failed (its `Status` code tells why: `0xC000006A` bad password,
`0xC0000234` locked out, `0xC0000071` expired password), **4740** lockout
(names the **calling computer** — the device with stale creds causing lockouts!),
**1074** who/what initiated a reboot.

### Crash dumps
```powershell
dir C:\Windows\Minidump                    # BSOD minidumps
# analyze with WinDbg: !analyze -v  (or NirSoft BlueScreenView for quick reads)
Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='BugCheck'}
```

---

## 6. Boot, updates & file integrity

```powershell
sfc /scannow                               # ★ system file check & repair
DISM /Online /Cleanup-Image /RestoreHealth # repair the component store — run this
                                           #   first if sfc says it can't fix
Get-HotFix | Sort InstalledOn -Descending | Select -First 10
                                           # ★ "what patched right before it broke?"
wusa /uninstall /kb:5031234                # remove a specific update
Get-WindowsUpdateLog                       # compile WU ETL logs into a text file
shutdown /r /t 0                           # reboot now
shutdown /r /o /t 0                        # reboot into recovery options menu
bcdedit /enum                              # boot configuration
msconfig                                   # boot options GUI (safe mode toggle)
```
`sfc` verdicts decoded: "did not find any integrity violations" (clean) •
"found corrupt files and successfully repaired" (done, details in
`C:\Windows\Logs\CBS\CBS.log`) • "found corrupt files but was unable to fix"
→ run the DISM RestoreHealth line, reboot, sfc again.

Startup programs & scheduled tasks (the "why is boot slow / what keeps running"):
```powershell
Get-CimInstance Win32_StartupCommand | Select Name,Command,Location
Get-ScheduledTask | Where State -eq "Running"
Get-ScheduledTaskInfo "\Microsoft\Windows\Defrag\ScheduledDefrag"
schtasks /query /fo LIST /v | more         # legacy full detail
```

---

## 7. Remote management & Active Directory

```powershell
Enter-PSSession -ComputerName srv01        # interactive remote shell (≈ ssh)
Invoke-Command -ComputerName srv01,srv02 -ScriptBlock { Get-Service spooler }
Test-WSMan srv01                           # is PS remoting enabled/reachable? (5985/5986)
Enable-PSRemoting -Force                   # turn it on (elevated, on the target)
mstsc /v:srv01                             # RDP client
qwinsta /server:srv01                      # RDP sessions on a server:
rwinsta 2 /server:srv01                    #   kick session ID 2 (hung session)
```

Domain / auth debugging:
```powershell
whoami /user /groups                       # my SID and group memberships (≈ id)
gpresult /r                                # ★ which GPOs applied, and from which DC
gpupdate /force                            # re-pull group policy
klist                                      # Kerberos tickets; klist purge to refresh
nltest /dsgetdc:corp.local                 # which DC am I using
nltest /sc_verify:corp.local               # secure channel to the domain OK?
Test-ComputerSecureChannel -Repair -Credential CORP\admin   # fix broken machine trust ★
                                           # ("trust relationship ... failed" at logon)
net user jsmith /domain                    # account state:
w32tm /query /status                       # time sync (≈ chronyc tracking)
w32tm /resync
w32tm /stripchart /computer:dc01 /samples:5   # live offset vs the DC
```
```
C:\> net user jsmith /domain
Account active               Yes            ← "Locked" shows here when locked out
Account expires              Never
Password expires             9/30/2026 10:00 AM
Last logon                   8/9/2026 8:55 AM
```
```
C:\> w32tm /query /status
Source: dc01.corp.local
Last Successful Sync Time: 8/9/2026 2:10:11 PM
Phase Offset: 0.0021088s                   ← >300s off = Kerberos logons fail
```

---

## Linux ↔ Windows cheat table

| Purpose | Linux | Windows |
|---|---|---|
| IP config | `ip addr` | `ipconfig /all`, `Get-NetIPConfiguration` |
| Reachability | `ping -c 4` | `ping` (`-t` continuous) |
| Route path | `traceroute` / `mtr` | `tracert` / `pathping` |
| Port test | `nc -zv h p` | `Test-NetConnection h -Port p` |
| Sockets+PID | `ss -tulpn` | `netstat -ano`, `Get-NetTCPConnection` |
| DNS query | `dig` | `nslookup`, `Resolve-DnsName` |
| Flush DNS | `resolvectl flush-caches` | `ipconfig /flushdns` |
| Processes | `ps aux`, `top` | `tasklist`, `Get-Process`, taskmgr |
| Cmdline of PID | `cat /proc/PID/cmdline` | `Get-CimInstance Win32_Process` |
| Kill | `kill -9 PID` | `taskkill /PID n /F` |
| Services | `systemctl status` | `Get-Service`, `sc query/qc` |
| Logs | `journalctl` | `Get-WinEvent`, eventvwr |
| Disk free | `df -h` | `Get-Volume` |
| Disk usage | `du -sh` | Get-ChildItem + Measure-Object |
| Disk health | `smartctl` | `Get-PhysicalDisk` (HealthStatus) |
| FS check | `fsck` | `chkdsk /f` |
| I/O by process | `iotop` | resmon (Disk tab) |
| Uptime | `uptime` | `systeminfo` (Boot Time) |
| Time sync | `chronyc tracking` | `w32tm /query /status` |
| Remote shell | `ssh` | `Enter-PSSession`, RDP |
| Pkg integrity | `rpm -V` / `debsums` | `sfc /scannow` + DISM |
| Recent updates | `dnf history` | `Get-HotFix` |
| Startup items | `systemctl list-unit-files` | `Get-CimInstance Win32_StartupCommand`, `Get-ScheduledTask` |
