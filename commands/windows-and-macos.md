# Windows & macOS

The Linux method does not change on these systems (port → PID → service → config → logs; resource → process → evidence); only the tools do. On Windows, prefer the PowerShell cmdlets: they return objects that you filter by property instead of text you grep, and they work the same on Server Core and over remoting. On macOS most BSD habits work, but services (launchd), logs (the unified log), DNS (scutil) and storage (APFS) have tools of their own. Use an elevated prompt on Windows and sudo on macOS when a command reads system-wide state.

| If you would reach for | Prefer | Because |
|---|---|---|
| `netstat -ano`, then `tasklist` by hand | `Get-NetTCPConnection -State Listen` with the process name added | port, PID and name in one sortable table; PID 4 sends you to `netsh http show servicestate` |
| `ping host` to ask "is the service up?" | `Test-NetConnection host -Port 443` | the service lives on a TCP port, and a failure also says whether the host answers |
| `tracert host` | `pathping -n -q 50 host` | loss per hop and per link, read like mtr, instead of one 3-probe snapshot |
| scrolling Event Viewer | `Get-WinEvent -FilterHashtable @{LogName='System'; Id=6008}` | filtered by log, ID, level and time at the source, and pasteable |
| Task Manager screenshots | `Get-Counter` with the key counters, `logman` for history | numbers per resource, also on Server Core, and a record of the next incident |
| `cat /etc/resolv.conf` on a Mac | `scutil --dns` | per-domain and VPN resolvers exist only in scutil's view |
| `tail -f /var/log/system.log` | `log stream --predicate 'process == "myapp"'` | most macOS logging goes only to the unified log |
| killing a process that comes back | `sc.exe qfailure NAME`, `launchctl print DOMAIN/LABEL` | service recovery and launchd's KeepAlive restart what you kill |

### Get-NetTCPConnection — which process owns this port, as objects you can sort and filter
Match: get-nettcpconnection, get-netudpendpoint
Instead of: netstat -ano
Safety: read-only · run PowerShell as Administrator so every owning process can be looked up

**In one line:** lists TCP sockets with addresses, state and owning PID as objects, so one pipeline goes from port to PID to process name, sorted and filtered by property.

**Read the command:** `Get-NetTCPConnection -State Listen | Sort-Object LocalPort | Select-Object LocalAddress, LocalPort, OwningProcess, @{n='Process'; e={ (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName }} | Format-Table -AutoSize`

| Part | Meaning |
|---|---|
| `-State Listen` | listening sockets only; `Established`, `TimeWait`, `CloseWait` select connections |
| `-LocalPort 443` | one local port (with `-State Established`: who is connected to it) |
| `@{n='Process'; e={ … }}` | a calculated column: the name of the process behind each row's `OwningProcess` |
| `-ErrorAction SilentlyContinue` | a process that has exited leaves the name empty instead of printing an error |
| `Sort-Object`, `Format-Table -AutoSize` | sort by port, as a number; columns sized to their content |
| `Get-NetUDPEndpoint` | the UDP twin: address, port and PID (UDP has no state) |

**What the output tells you:**

```
LocalAddress LocalPort OwningProcess Process
------------ --------- ------------- -------
0.0.0.0             80             4 System
0.0.0.0           3389          1188 svchost
127.0.0.1         3000          9412 node
```

`0.0.0.0` (or `::`) means every address; `127.0.0.1` this host only, the classic "works on the server, refused from outside". PID 4 `System` is not the real owner: http.sys, the kernel HTTP driver, holds the port for IIS, WinRM or another registered service. `svchost` hosts one or more services.

**Why it is effective:** filters compare properties, so port 443 never matches 4430, and the objects can be grouped: `Get-NetTCPConnection -State Established | Group-Object RemoteAddress` shows which clients hold the most connections.

**Compared with `netstat -ano`:** the same table with PIDs in any cmd window, enough for a quick look, but as text (`findstr :443` also hits `:4430`) and with every PID to look up by hand.

**Trap:** a port with no socket can still refuse to bind: Hyper-V and WinNAT reserve whole ranges (the `netsh int` card). Without `-State` you also get every `TimeWait` and `Bound` entry.

**Next step:** PID 4 → `netsh http show servicestate`. `svchost` → `tasklist /svc /fi "PID eq 1188"`. Other PIDs → `Get-CimInstance Win32_Process -Filter "ProcessId = 9412"`. Listening but unreachable → the Windows Firewall card.

### Get-Process — which process holds the memory or burns the CPU, and what is it?
Match: get-process, stop-process
Instead of: Task Manager, tasklist
Safety: read-only · `Stop-Process` changes state: it ends the process at once, with no chance to clean up (like `kill -9`)

**In one line:** returns every process as an object (working set, private memory, CPU seconds, handles, path, start time), to rank the top consumers or inspect one PID.

**Read the command:** `Get-Process | Sort CPU -Descending | Select -First 10`

| Part | Meaning |
|---|---|
| `Sort CPU -Descending` | `Sort` = `Sort-Object`; `CPU` = processor seconds used **since the process started** |
| `Select -First 10` | `Select-Object`: keep the first 10 |
| `Sort WS -Descending` | by working set, the RAM in use now |
| `-Id 4321 | Select Path,StartTime,Threads,Handles` | one PID: its program file and start time |
| `-Name java | Stop-Process -Force` | **changes state**: end every process named java, without asking |

**What the output tells you:**

```
Handles  NPM(K)  PM(K)    WS(K)   CPU(s)    Id  ProcessName
   1234      98  812000  1843200  9214.44  4321 java
```

`WS` is RAM in use now, close to Linux RSS. `PM` is committed private memory, which counts against the commit limit even when paged out; a `PM` that only grows for hours is the Windows leak signature, and so are `Handles` that climb from sample to sample.

**Why it is effective:** sorting by any property, in scripts and over remoting, turns "the server is slow" into a named process in one line.

**Compared with Task Manager and `tasklist`:** Task Manager shows CPU % right now, fine at a desktop; tasklist shows memory and services but cannot sort.

**Trap:** `CPU` is a total since start: a database up for a month always tops the list. For CPU now, use `Get-Counter '\Process(*)\% Processor Time'`. A service's recovery actions or a wrapper often restart what `Stop-Process` ended.

**Next step:** command line and parent → `Get-CimInstance Win32_Process`. `svchost` → `tasklist /svc`. Growing `PM` → sample it over hours. To stop it for good → `Stop-Service`, not the process.

### tasklist / taskkill — which program and which services sit behind this PID, and end it from cmd
Match: tasklist, taskkill
Instead of: Task Manager
Safety: read-only for `tasklist` · `taskkill` changes state: `/F` ends processes at once, `/T` their child processes too

**In one line:** the cmd process list (image name, PID, memory) with filters; `/svc` names the services inside each process, which is how you see through `svchost.exe`.

**Read the command:** `tasklist /svc /fi "PID eq 1188"`

| Part | Meaning |
|---|---|
| `/svc` | list the services hosted in each process instead of memory |
| `/fi "PID eq 1188"` | a filter in double quotes: field, operator (`eq`, `ne`, `gt`, `lt`), value |
| `/fi "IMAGENAME eq java.exe"`, `/fi "MEMUSAGE gt 500000"` | by program name; by memory in KB (here 500 MB) |
| `taskkill /PID 4321 /F` | **changes state**: force-end PID 4321 (≈ `kill -9`) |
| `taskkill /IM notepad.exe /F /T` | **changes state**: by name, with its child processes |

**What the output tells you:**

```
Image Name                     PID Services
========================= ======== ============================================
svchost.exe                   1188 TermService
svchost.exe                   3120 wuauserv
```

PID 1188 is Remote Desktop Services and 3120 Windows Update: names that `sc qc` and the event log understand. `N/A` means no service inside.

**Why it is effective:** several services share one `svchost.exe`, so a port or CPU "used by svchost" means nothing until `/svc` names the service; it works in plain cmd and in recovery consoles.

**Compared with Task Manager:** its Services tab maps PIDs to services too, in the GUI only.

**Trap:** killing a shared `svchost` ends every service inside it, and the Service Control Manager may restart a killed service. PID 4 (`System`) is the kernel and cannot be ended.

**Next step:** service named → `sc qc NAME`, `Get-WinEvent`. Command line → `Get-CimInstance Win32_Process`. Back after `taskkill` → `sc.exe qfailure NAME`, scheduled tasks, wrappers such as NSSM.

### Get-CimInstance — the full command line, parent, services and boot time behind a PID
Match: get-ciminstance, wmic, systeminfo, get-computerinfo
Instead of: wmic, systeminfo
Safety: read-only · run elevated, or other users' command lines come back empty

**In one line:** queries WMI, Windows' live inventory: `Win32_Process` gives a process's command line and parent, `Win32_Service` the services in a process, `Win32_OperatingSystem` the last boot and free memory.

**Read the command:** `Get-CimInstance Win32_Process -Filter "ProcessId = 9412" | Select-Object ProcessId, ParentProcessId, CreationDate, ExecutablePath, CommandLine | Format-List`

| Part | Meaning |
|---|---|
| `Win32_Process` | the class: one object per process |
| `-Filter "ProcessId = 9412"` | a WQL condition (`=`, `<>`, strings in single quotes), not PowerShell's `-eq` |
| `Select-Object …`, `Format-List` | parent, start time, binary and command line, one per line so nothing is cut |
| `Win32_Service -Filter "ProcessId = 1188"` | the services in that process: Name, State, StartMode, PathName |
| `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime` | the last boot; `(Get-Date) - …` = uptime |
| `Win32_StartupCommand`, `Win32_ComputerSystem` | programs started at logon; `.NumberOfLogicalProcessors` |

**What the output tells you:**

```
ProcessId       : 9412
ParentProcessId : 7720
CreationDate    : 03/10/2026 08:15:22
ExecutablePath  : C:\Program Files\nodejs\node.exe
CommandLine     : "C:\Program Files\nodejs\node.exe" D:\apps\reporting\server.js
```

The arguments reveal the app directory, where config and logs usually live. Then look up the parent: `nssm.exe` or `winsw.exe` is a service wrapper that restarts the app.

**Why it is effective:** tasklist stops at `node.exe` or `java.exe`; with five Java services on one host, only the command line says which is which.

**Compared with `wmic` and `systeminfo`:** wmic reads the same classes but is deprecated in favour of the CIM cmdlets. `systeminfo` prints version, boot time and memory as text, fine for a glance (`Get-ComputerInfo` returns them as an object).

**Trap:** Windows reuses PIDs, so a parent may be gone and its number reused: a real parent's `CreationDate` is older than the child's.

**Next step:** wrapper as parent → `sc.exe qfailure` on its service. Unexpected boot time → `Get-WinEvent` IDs 41, 6008, 1074.

### Test-NetConnection — does this TCP port answer from here, and through which interface?
Match: test-netconnection, test-connection
Instead of: ping, telnet
Safety: read-only · one TCP connection attempt, plus a ping when it fails; `-TraceRoute` probes every hop

**In one line:** Windows' `nc -zv`: it resolves the name, tries a TCP handshake and reports the result with the interface and source address used; on failure it also pings, separating "host up, port closed" from "nothing answers".

**Read the command:** `Test-NetConnection app.example.com -Port 443 -InformationLevel Detailed`

| Part | Meaning |
|---|---|
| `-Port 443` | try a TCP handshake (`-CommonTCPPort RDP`, `SMB`, `HTTP`, `WINRM` are shortcuts) |
| `-InformationLevel Detailed` | add the name resolution results and the next hop (`NetRoute`) |
| `-TraceRoute` | ping plus the hop list (a silent hop shows as `0.0.0.0`) |
| `Test-Connection host -Count 4` | PowerShell's ping, as objects |

**What the output tells you:**

```
WARNING: TCP connect to (10.0.1.20 : 443) failed
RemoteAddress          : 10.0.1.20
RemotePort             : 443
InterfaceAlias         : Ethernet0
SourceAddress          : 10.0.1.10
PingSucceeded          : True
TcpTestSucceeded       : False
```

`TcpTestSucceeded : True`: the handshake completed. `False` with a successful ping: the host is up but the port is closed or filtered (service down, bound to 127.0.0.1, firewall). Both false: the path or the host, or ICMP is blocked too. `InterfaceAlias` and `SourceAddress` show whether traffic left through the VPN or the LAN.

**Why it is effective:** it tests the port users need, works where ICMP is blocked, and ships with Windows PowerShell, where `nc` does not.

**Compared with `ping` and `telnet`:** ping (and `Test-Connection`) prove ICMP reachability and show loss, enough for "is the host there?", not for the port. The telnet client is not installed by default on current Windows.

**Trap:** `False` does not tell a refusal from a silent drop (`nc -zv` does): a fast failure suggests a refusal, a long wait a drop. A test run on the server itself skips outside firewalls. Success proves only the handshake: a proxy answers even when the app behind it is down.

**Next step:** true but the app fails → `curl.exe -v https://app.example.com/`. False with a working ping → on the target, `Get-NetTCPConnection -LocalPort 443`, then the firewall card. Both false → `pathping -n`.

### pathping / tracert — which routers does the path cross, and where does loss start?
Match: pathping, tracert
Instead of: ping
Safety: read-only · ICMP probes to every hop; pathping collects for minutes before printing statistics

**In one line:** `tracert` lists the routers on the path with three round-trip times each; `pathping` traces, then probes every hop many times and reports loss per hop and per link: the Windows mtr.

**Read the command:** `pathping -n -q 50 app.example.com`

| Part | Meaning |
|---|---|
| `-n` | no reverse-DNS lookups (pathping's flag; tracert's is `-d`) |
| `-q 50` | 50 probes per hop instead of 100: twice as fast |
| `tracert -d host` | the plain trace: 3 probes per hop, no DNS |

**What the output tells you:**

```
            Source to Here   This Node/Link
Hop  RTT    Lost/Sent = Pct  Lost/Sent = Pct  Address
  1    1ms     0/  50 =  0%     0/  50 =  0%  10.0.1.1
                               10/  50 = 20%   |
  2   35ms    10/  50 = 20%     0/  50 =  0%  198.51.100.1
                                0/  50 =  0%   |
  3   36ms    10/  50 = 20%     0/  50 =  0%  203.0.113.10
```

`Source to Here` is the loss from you to that hop. `This Node/Link` splits it: on a hop line, loss caused by the router itself; on a `|` line, loss on the link between two hops. Here 20% disappears on the link into hop 2 and stays to the destination: real loss, starting there.

**Why it is effective:** a 3-probe snapshot misses intermittent loss; pathping's statistics show where it begins, evidence for an ISP ticket.

**Compared with `ping`:** ping prints end-to-end loss but not where. tracert shows the route and where latency jumps, enough for "which way does traffic go?".

**Trap:** loss at one middle router that is gone at later hops is that router rate-limiting its own replies; tracert's `Request timed out.` lines mean the same when later hops answer. Both use ICMP only: a path that filters ICMP looks dead while TCP works.

**Next step:** loss from hop 1 → the local link (`Get-NetAdapter`, `netsh wlan show interfaces`). Loss from an ISP hop onward → the report to the ISP. Clean path, failing port → `Test-NetConnection -Port`.

### ipconfig — which address, gateway, DHCP lease and DNS servers does each adapter have?
Match: ipconfig, get-netipconfiguration, get-netipaddress
Instead of: plain ipconfig
Safety: read-only for `/all` and `/displaydns` · changes state: `/release` and `/renew` drop and request the DHCP lease (a remote session on that adapter drops); `/flushdns` empties the DNS cache (harmless)

**In one line:** Windows' `ip addr` plus the DHCP view: each adapter's addresses, gateway, DHCP server, lease and DNS servers; it also shows and clears the DNS cache.

**Read the command:** `ipconfig /all`

| Part | Meaning |
|---|---|
| `/all` | adds the MAC, DHCP server, lease times and DNS servers |
| `/release`, `/renew` | **changes state**: give back, then request a DHCP lease |
| `/displaydns`, `/flushdns` | show / **empty** the DNS client cache (= `Clear-DnsClientCache`) |
| `Get-NetIPConfiguration` | the per-adapter summary as objects |
| `Get-NetIPAddress -AddressFamily IPv4` | every IPv4 address with prefix length and origin (`Dhcp`, `Manual`) |

**What the output tells you:**

```
Ethernet adapter Ethernet0:
   IPv4 Address. . . . . . . . . . . : 10.0.1.10(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 10.0.1.1
   DHCP Server . . . . . . . . . . . : 10.0.1.5
   DNS Servers . . . . . . . . . . . : 10.0.1.5
```

169.254.x.x (APIPA): DHCP failed (link, VLAN, DHCP server). No gateway: only the local subnet is reachable. `Media disconnected`: no link. `(Duplicate)` instead of `(Preferred)`: another machine has this IP.

**Why it is effective:** most "the internet is broken" tickets are on this screen: no lease, no gateway, or a wrong DNS server pushed by a VPN.

**Compared with plain `ipconfig`:** address, mask and gateway only; the DHCP and DNS servers, where client problems usually sit, need `/all`.

**Trap:** macOS has an unrelated `ipconfig` (the networksetup card). Virtual adapters (Hyper-V, VPN, WSL) are listed too: read the one carrying the traffic. `/flushdns` clears neither the browser's cache nor the DNS server's.

**Next step:** APIPA → cable, VLAN, DHCP server. Wrong DNS → `Get-DnsClientServerAddress`, the VPN client, `Resolve-DnsName`. All fine → `Test-NetConnection`, `pathping`.

### Resolve-DnsName / Clear-DnsClientCache — what does DNS answer, which servers are asked, and how fast?
Match: resolve-dnsname, clear-dnsclientcache, get-dnsclientcache, get-dnsclientserveraddress, measure-command
Instead of: nslookup
Safety: read-only · `Clear-DnsClientCache` changes state: it empties the local DNS cache, which refills by itself

**In one line:** `Resolve-DnsName` is Windows' dig: one record type, optionally from a chosen server, returned as objects with a TTL; the client cmdlets show which servers each interface asks and what the cache holds.

**Read the command:** `Resolve-DnsName host -Server 8.8.8.8`

| Part | Meaning |
|---|---|
| `-Server 8.8.8.8` | ask this server directly instead of the configured ones |
| `-Type A` | the record type: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `SRV`, `PTR`… |
| `-DnsOnly` | DNS only, no fallback to LLMNR or NetBIOS |
| `Measure-Command { … } | Select-Object TotalMilliseconds` | lookup time (after `Clear-DnsClientCache`: with a cold cache) |
| `Get-DnsClientServerAddress -AddressFamily IPv4` | the DNS servers of each interface |
| `Get-DnsClientCache | Where Entry -like "*example*"` | what the cache holds for matching names |

**What the output tells you:**

```
Name                 Type   TTL   Section    IPAddress
----                 ----   ---   -------    ---------
app.example.com      A      300   Answer     203.0.113.20
```

`TTL`: seconds the answer may be cached, so a wrong record lives that long. `DNS name does not exist` is NXDOMAIN (missing record or a typo); `This operation returned because the timeout period expired`: the server did not answer.

**Why it is effective:** the configured server and a public one, asked two lines apart, separate "the record is wrong" from "my resolver is stale or split by a VPN".

**Compared with `nslookup`:** it shows the answering server too, fine for a quick check, but it sends its own queries and skips the hosts file, the cache and VPN name rules (NRPT), so it can disagree with what applications get.

**Trap:** without `-Server`, the answer may come from the cache or the hosts file. `Clear-DnsClientCache` does not clear the browser's cache.

**Next step:** wrong only from the configured server → that server or the VPN's DNS. Right answer, app still on the old IP → the app's own cache. NXDOMAIN everywhere → the zone itself.

### Get-NetAdapter / netsh wlan — link speed, duplex, error counters and Wi-Fi signal
Match: get-netadapter, get-netadapterstatistics, get-netadapteradvancedproperty, netsh wlan
Instead of: ipconfig
Safety: read-only · `netsh wlan show wlanreport` needs an elevated prompt and writes an HTML report

**In one line:** `Get-NetAdapter` shows each adapter's status, negotiated speed and duplex; `Get-NetAdapterStatistics` its error and discard counters; `netsh wlan show interfaces` the Wi-Fi radio.

**Read the command:** `Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, LinkSpeed, FullDuplex`

| Part | Meaning |
|---|---|
| `Format-Table …, LinkSpeed, FullDuplex` | the columns to show; `LinkSpeed` is the negotiated speed |
| `Get-NetAdapterStatistics -Name "Ethernet"` | counters since the adapter started: `ReceivedPacketErrors`, `ReceivedDiscardedPackets`… |
| `Get-NetAdapterAdvancedProperty -Name "Ethernet" -DisplayName "Speed & Duplex"` | whether the driver forces a speed |
| `netsh wlan show interfaces` | SSID, band, channel, receive and transmit rate, `Signal` in % |
| `netsh wlan show wlanreport` | an HTML history of Wi-Fi sessions and disconnect reasons |

**What the output tells you:**

```
Name     InterfaceDescription                Status LinkSpeed  FullDuplex
----     --------------------                ------ ---------  ----------
Ethernet Intel(R) Ethernet Connection I219-V Up     100 Mbps         True
Wi-Fi    Intel(R) Wi-Fi 6 AX201 160MHz       Up     866.7 Mbps       True
```

100 Mbps on a gigabit port: a damaged cable or a forced switch port. For Wi-Fi, `LinkSpeed` is the radio rate, not throughput. netsh's `Signal` maps roughly to dBm as percent / 2 − 100: 48% ≈ −76 dBm, weak.

**Why it is effective:** ping and ipconfig look perfect on a 100 Mbit/s or half-duplex link; the adapter knows what was negotiated, and its errors (physical fault) differ from discards (host not keeping up).

**Compared with `ipconfig`:** it shows `Media disconnected`, but no speed, duplex, errors or signal.

**Trap:** counters are cumulative: sample twice. A VM's NIC reports a nominal speed. Property names vary by driver. A Wi-Fi reading is a snapshot.

**Next step:** wrong speed → cable, switch port, auto-negotiation. Errors rising → cable and port; discards → driver, CPU. Weak signal → closer, 5 GHz, or a cable; then `pathping` to the gateway.

### netsh http — which service is really behind PID 4 (System) on port 80, 443 or 5985?
Match: netsh http
Instead of: netstat -ano, tasklist
Safety: read-only for `show` · `netsh http add` and `delete` change http.sys; a new `iplisten` applies only when the HTTP service restarts, which restarts IIS, WinRM and its other dependents

**In one line:** IIS, WinRM, SSRS, WSUS and many vendor tools register URLs with http.sys, the kernel HTTP driver, which owns the port and appears as PID 4; `netsh http` asks it which request queue, process and URL hold each port.

**Read the command:** `netsh http show servicestate view=requestq verbose=no`

| Part | Meaning |
|---|---|
| `show servicestate` | a snapshot of http.sys: request queues, registered URLs, process IDs |
| `view=requestq` | one block per request queue (an IIS application pool or a service) |
| `verbose=no` | the short form |
| `show urlacl` | URL reservations: which account may register which URL |
| `show sslcert` | certificate bindings per `ip:port` |
| `show iplisten` | if anything is listed, http.sys binds only these addresses |

**What the output tells you:**

```
Request queue name: DefaultAppPool
    Process IDs:
        5132
    URL groups:
        Registered URLs:
            HTTP://*:80/
            HTTPS://*:443/
Request queue name: Request queue is unnamed.
    Process IDs:
        2280
```

`DefaultAppPool` is an IIS application pool whose `w3wp.exe` worker, PID 5132, serves 80 and 443. The unnamed queue of PID 2280 holds `HTTP://+:5985/WSMAN/`, and `tasklist /svc /fi "PID eq 2280"` names it: WinRM. `+` is a strong wildcard (every host name), `*` a weak one (only what no other registration claims).

**Why it is effective:** socket tools stop at PID 4; only http.sys knows the URLs and the processes behind it.

**Compared with `netstat -ano` and `tasklist`:** they prove that PID 4 holds the port, which already says "http.sys", and no more.

**Trap:** `net stop http` frees the port by stopping http.sys and every dependent service (IIS, WinRM…); stop the one service that registered the URL instead. Another web server cannot bind 443 while http.sys holds it on all addresses; `iplisten` can give each its own IP.

**Next step:** the PID → `tasklist /svc`, then that service or IIS site. Two servers on 443 → `netsh http add iplisten ipaddress=192.0.2.10` in a planned restart. TLS errors → `show sslcert`.

### netsh int — reserved port ranges, interface MTU, TCP auto-tuning, and stack resets
Match: netsh int, netsh interface, netsh winsock, netsh, get-nettcpsetting
Instead of: netstat -ano
Safety: read-only for `show` · changes state: `set` changes the TCP stack at once; `int ip reset` and `winsock reset` rewrite network settings and need a reboot

**In one line:** netsh, the cmd-era network shell, works in contexts (`interface` or `int`, `http`, `wlan`, `advfirewall`, `winsock`); `int` shows reserved ports, the ephemeral range, each interface's MTU and the global TCP settings.

**Read the command:** `netsh int ipv4 show excludedportrange protocol=tcp`

| Part | Meaning |
|---|---|
| `show excludedportrange protocol=tcp` | TCP ranges reserved by Hyper-V, WSL2, WinNAT, or an admin (`*`) |
| `show dynamicport tcp` | the ephemeral range (default: start 49152, 16384 ports) |
| `interface ipv4 show subinterfaces` | the MTU of each interface (VPN adapters often 1400 or less) |
| `interface tcp show global` | auto-tuning, RSS, ECN (`Get-NetTCPSetting`: the same as objects) |
| `int ip reset`, `winsock reset` | **changes state**: reset TCP/IP or Winsock to defaults, then reboot |

**What the output tells you:**

```
Start Port    End Port
----------    --------
     49709       49808
     50000       50059     *

* - Administered port exclusions.
```

A port inside a range cannot be bound (error 10013, "forbidden by its access permissions") although netstat shows nothing there; the ranges can move at a reboot, hence "it worked yesterday". In `tcp show global`, `Receive Window Auto-Tuning Level : disabled` caps the window at 64 KB and cripples WAN and VPN downloads.

**Why it is effective:** it explains what no socket list can: a bind failing on a free port, and transfers that are fast on the LAN but slow far away.

**Compared with `netstat -ano`:** it lists sockets, not reservations: its empty output is the symptom.

**Trap:** the resets are last resorts: `winsock reset` also removes Winsock providers installed by VPN and security software, `int ip reset` returns TCP/IP to its defaults (note the IP settings first), and neither acts before the reboot.

**Next step:** port excluded → use another port, or restore the range (`netsh int ipv4 set dynamic tcp start=49152 num=16384`, reboot). Auto-tuning off → `netsh interface tcp set global autotuninglevel=normal`. Small VPN MTU → `ping -f -l 1472`.

### New-NetFirewallRule / Get-NetFirewallRule — is Windows Firewall dropping it, and how to open one port for one client
Match: new-netfirewallrule, get-netfirewallrule, get-netfirewallprofile, remove-netfirewallrule, netsh advfirewall
Instead of: turning the firewall off
Safety: read-only for `Get-…` and `netsh advfirewall show` · changes state: `New-`/`Remove-NetFirewallRule` and `netsh advfirewall set` act at once and survive reboots

**In one line:** Windows Defender Firewall filters per profile (Domain, Private, Public); these commands show the profiles and rules, add and remove a narrow rule, and switch on the log that proves a drop.

**Read the command:** `New-NetFirewallRule -DisplayName "iperf3-test" -Direction Inbound -Protocol TCP -LocalPort 5201 -RemoteAddress 10.0.20.11 -Action Allow`

| Part | Meaning |
|---|---|
| `-DisplayName "iperf3-test"` | the name to find and delete it by |
| `-Direction Inbound -Protocol TCP -LocalPort 5201` | connections arriving at TCP port 5201 on this host |
| `-RemoteAddress 10.0.20.11` | only from this client (default: any) |
| `-Action Allow` | allow; a matching Block rule still wins |
| `Get-NetFirewallProfile`, `netsh advfirewall show allprofiles` | which profiles are on, default actions, logging |
| `Get-NetFirewallRule -Enabled True -Direction Inbound` | the enabled inbound rules |
| `netsh advfirewall set allprofiles logging droppedconnections enable` | **changes state**: log drops to `pfirewall.log` |
| `Remove-NetFirewallRule -DisplayName "iperf3-test"` | **changes state**: delete the rule after the test |

**What the output tells you:** the drop log, read with `Get-Content $env:systemroot\system32\LogFiles\Firewall\pfirewall.log -Tail 20`:

```
2026-10-03 10:12:44 DROP TCP 10.0.20.11 10.0.20.15 51544 5201 52 S 2733914 0 64240 - - - RECEIVE
```

Date, time, action, protocol, source and destination IP, then ports: 10.0.20.11 tried port 5201 and was dropped, so the firewall, not the network, is the cause.

**Why it is effective:** one port for one client instead of no protection, and a log line that turns a silent timeout into evidence.

**Compared with turning the firewall off:** it answers "is it the firewall?" in seconds, by leaving the host open to everyone until someone remembers.

**Trap:** the network's profile decides which rules apply: a Domain-only rule does nothing on a NIC classified as Public. Group Policy can override local rules. Nothing is logged until logging is on.

**Next step:** DROP lines → the profile and Block rules (`Get-NetFirewallRule -Action Block -Enabled True`). No drops, still a timeout → the listener (`Get-NetTCPConnection -LocalPort`), then the path.

### Get-WinEvent — what Windows logged, filtered by log, event ID, level and time
Match: get-winevent, eventvwr, get-date
Instead of: Event Viewer (eventvwr)
Safety: read-only · the Security log needs an elevated prompt

**In one line:** reads any event log (System, Application, Security, the `Microsoft-Windows-…` logs) and filters at the source by log, provider, ID, level and time: the Windows `journalctl`.

**Read the command:** `Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2,3; StartTime=(Get-Date).AddHours(-24)} -MaxEvents 40`

| Part | Meaning |
|---|---|
| `-FilterHashtable @{…}` | conditions applied by the event log service itself: fast on big logs |
| `LogName='System'` | the log: `Application`, `Security`, or a full name such as `Microsoft-Windows-…/Operational` |
| `Level=1,2,3` | Critical, Error, Warning (4 = Information) |
| `StartTime=(Get-Date).AddHours(-24)` | the last 24 hours only |
| `Id=6008`, `ProviderName='Service Control Manager'` | one event ID, or one source |
| `-MaxEvents 40` | the newest 40 |
| `-LogName System -MaxEvents 30` | the simple form: the newest events, unfiltered |
| `-ListLog * | Where RecordCount -gt 0` | every log that holds events |

**What the output tells you:**

```
TimeCreated          Id LevelDisplayName Message
8/9/2026 3:11:58   6008 Error            The previous system shutdown at 3:02:11 AM
                                         on 8/9/2026 was unexpected.
8/9/2026 3:14:22   7034 Error            The MyApp service terminated unexpectedly.
```

IDs worth knowing: 41 and 6008, an unexpected shutdown; 1074, who started a restart; 7000/7001, a service failed to start; 7031/7034, a service crashed; 4625, a failed logon; 4740, a lockout (naming the calling computer); 2004, low virtual memory; 153 and 129, storage retries and resets.

**Why it is effective:** the event behind an outage is one line among thousands; filtering by ID and time finds it in seconds, newest first, ready to paste.

**Compared with Event Viewer:** the same events and filters, fine at a desk, but not on Server Core, over remoting or in scripts.

**Trap:** no match raises an error ("No events were found that match the specified selection criteria"): add `-ErrorAction SilentlyContinue` in scripts. `Format-Table` cuts messages: use `Format-List`. Logs are size-limited and overwrite their oldest events.

**Next step:** 7000 or 7034 → `sc qc NAME`. 41 or 6008 without a 1074 → power loss or a crash: minidumps, `ProviderName='BugCheck'`. 4740 → the calling computer. 2004 → `Get-Process` by memory.

### Get-Counter — CPU queue, memory, paging, disk latency and network, in numbers
Match: get-counter, resmon, resmon.exe, perfmon, taskmgr
Instead of: Task Manager (taskmgr)
Safety: read-only

**In one line:** samples performance counters, the data Performance Monitor graphs: CPU, processor queue, free memory, paging, disk latency and throughput in one command, on Server Core and over remoting too.

**Read the command:** `Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5`

| Part | Meaning |
|---|---|
| `'\Processor(_Total)\% Processor Time'` | a path, `\object(instance)\counter`: `_Total` = all CPUs, `(*)` = each instance |
| `-SampleInterval 2 -MaxSamples 5` | 5 samples 2 s apart (default: one sample; `-Continuous` runs until Ctrl-C) |
| `-Counter $counters` | a list of paths in one pass |
| `'\Memory\Available MBytes'`, `'\Memory\Pages/sec'` | free RAM; pages read or written to resolve page faults |
| `'\PhysicalDisk(_Total)\Avg. Disk sec/Read'` | latency in **seconds**: 0.010 = 10 ms |
| `'\Process(*)\% Processor Time'` | per process, per core: divide by the logical CPU count |
| `resmon`, `perfmon`, `taskmgr` | the GUIs: Resource Monitor (per-process disk, network, files), Performance Monitor, Task Manager |

**What the output tells you:** the slow-system playbook's first pass, paths shortened:

```
\\win-app01\processor(_total)\% processor time        34.812
\\win-app01\system\processor queue length                  1
\\win-app01\memory\available mbytes                      388
\\win-app01\memory\pages/sec                        2411.902
\\win-app01\physicaldisk(_total)\avg. disk sec/write   0.091
```

CPU 35% with a queue of 1 on 4 CPUs: not CPU-bound. 388 MB free of 8 GB at 2,400 pages/s: paging, and 91 ms writes because of it. Sustained limits: a queue above 2 per logical CPU, free memory under 10% of RAM, latency above 0.010 s (SSD) or 0.020 s (HDD).

**Why it is effective:** every resource in one pass, as numbers to compare and paste, separates "busy CPU" from "waiting for disk or memory" before you blame a process.

**Compared with Task Manager:** live graphs and per-process CPU, fine at a desktop, but no history and no GUI on Server Core. Resource Monitor names the process and the file behind disk I/O, which counters cannot.

**Trap:** counter names are translated on non-English Windows, where English paths fail. `Pages/sec` alone can come from memory-mapped files; it matters with low `Available MBytes`. Latency is in seconds.

**Next step:** paging → `Get-Process` by working set. Queue high → `Get-Process` by CPU. Disk latency → Resource Monitor's Disk tab. Comes and goes → a `logman` collector.

### logman — record performance counters around the clock, so "slow at 2 a.m." leaves evidence
Match: logman, relog
Instead of: Get-Counter
Safety: changes state: `create` and `start` add a collector that writes to disk until it is stopped or deleted · read-only: `query`

**In one line:** creates and controls Performance Monitor data collectors from the command line; a capped circular log keeps days of history without filling the disk, and `relog` exports the slow window.

**Read the command:** `logman create counter SlowCatch -si 00:00:15 -f bincirc -max 512 -o "C:\PerfLogs\SlowCatch" -c "\Memory\Available MBytes"`

| Part | Meaning |
|---|---|
| `create counter SlowCatch` | a counter collector named SlowCatch |
| `-si 00:00:15` | one sample every 15 seconds |
| `-f bincirc -max 512` | a circular binary `.blg` file of at most 512 MB: the oldest data is overwritten |
| `-o "C:\PerfLogs\SlowCatch"` | where the log goes |
| `-c "…" "…"` | the counter paths (the handbook records CPU, memory, disk, network, `\Process(*)`) |
| `start`, `query`, `stop`, `delete SlowCatch` | run it, show its status, stop it, remove it |
| `relog FILE.blg -f csv -o slow.csv -b … -e …` | export one time window to CSV |

**What the output tells you:** `logman query SlowCatch`, shortened:

```
Name:                 SlowCatch
Status:               Running
Circular:             On
Sample Interval:      15
Output Location:      C:\PerfLogs\SlowCatch.blg
```

`Running` with `Circular: On`: recording, never past the cap. `Output Location` is the file for Performance Monitor or relog.

**Why it is effective:** Windows keeps no counter history by default; this is its `sar`, and the `\Process(*)` counters answer "which process at 02:10?".

**Compared with `Get-Counter`:** perfect during the problem; for slowness that comes and goes, a live tool always arrives too late.

**Trap:** a collector does not restart after a reboot by itself (the handbook adds a `schtasks` start-up task). `\Process(*)` counters grow the file fastest. A circular file overwrites itself: export the incident soon.

**Next step:** after the next complaint, `relog` the window or open the `.blg` in Performance Monitor, read it like the Get-Counter card, then check events and scheduled tasks at that time.

### Get-Service / sc.exe — is the service running, how does it start, as which account, and what restarts it?
Match: get-service, set-service, restart-service, stop-service, sc, sc.exe
Instead of: services.msc, net start
Safety: read-only for `Get-Service` and `sc query/qc/queryex/qfailure` · changes state: `Restart-Service`, `Stop-Service`, `Set-Service` and `sc.exe config` act at once; `Stop-Service` stops a service with dependents only with `-Force`, which stops them too

**In one line:** `Get-Service` lists services with status and start type; `sc.exe` shows the rest: binary path, account, dependencies, PID, and the recovery actions that restart a failed service.

**Read the command:** `sc qc MSSQLSERVER`

| Part | Meaning |
|---|---|
| `qc NAME` | configuration: start type, binary path, dependencies, account (`SERVICE_START_NAME`) |
| `query`, `queryex NAME` | the state (`RUNNING`, `STOPPED`, `START_PENDING`) and exit codes; `queryex` adds the PID |
| `qfailure W3SVC` | recovery actions: `RESTART` explains "it keeps coming back" |
| `config W3SVC start= disabled` | **changes state**: the start type; the space after `start=` is required |
| `Get-Service | Where Status -eq "Stopped" | Where StartType -eq "Automatic"` | services that should run but do not |
| `Set-Service spooler -StartupType Automatic` | **changes state**: the start type |
| `Restart-Service spooler -Verbose`, `Stop-Service -Name W3SVC` | **changes state**: restart (reporting it), stop |

**What the output tells you:**

```
SERVICE_NAME: MSSQLSERVER
        START_TYPE         : 2   AUTO_START
        BINARY_PATH_NAME   : "C:\Program Files\...\sqlservr.exe" -sMSSQLSERVER
        DEPENDENCIES       : KEYISO
        SERVICE_START_NAME : CORP\svc-sql
```

The account is the usual suspect: an expired or changed password, or a locked account, stops the start (events 7000 and 7038); `LocalSystem` has no password. Start type 2 is automatic, 3 manual, 4 disabled.

**Why it is effective:** "Stopped" is the symptom; the cause (account, dependency, missing binary, port taken) sits here and in the System log, and `qfailure` exposes the restarts that undo a kill.

**Compared with services.msc and `net start`:** the console spreads the same settings over several tabs; `net start NAME` is enough when nothing is wrong.

**Trap:** in Windows PowerShell, `sc` is the alias of `Set-Content`: `sc query spooler` writes "spooler" into a file named query. Type `sc.exe`. Killing a service's process triggers its recovery actions.

**Next step:** will not start → `Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Service Control Manager'} -MaxEvents 10`. Comes back → `qfailure`, scheduled tasks, NSSM or WinSW. Port conflict → `Get-NetTCPConnection`.

### net — start or stop a service, list mapped drives, read a domain account's state
Match: net, get-smbconnection, get-smbsession, get-smbopenfile
Instead of: —
Safety: read-only for `net use` and `net user` as shown · changes state: `net start`, `net stop`, and options that map, delete or change drives and accounts

**In one line:** the old all-purpose cmd tool: services by name, mapped drives, and a domain account's state (locked, password expiry, last logon); the SMB cmdlets give the PowerShell view of file-share connections.

**Read the command:** `net user deploy /domain`

| Part | Meaning |
|---|---|
| `user deploy /domain` | the account `deploy`, asked of a domain controller instead of the local database |
| `start spooler`, `stop spooler` | **changes state**: start or stop a service (`net start` alone lists the running ones) |
| `use` | mapped drives: letter, share, status (`OK`, `Disconnected`, `Unavailable`) |
| `Get-SmbConnection` | this machine's SMB connections and their `Dialect` (3.x expected) |
| `Get-SmbSession`, `Get-SmbOpenFile` | on a file server: who is connected, which files are open |

**What the output tells you:**

```
Account active               Yes
Password last set            7/2/2026 9:00 AM
Password expires             9/30/2026 10:00 AM
Last logon                   8/9/2026 8:55 AM
```

`Account active  Locked` means locked out, `No` disabled. A `Password expires` date in the past explains "my password stopped working", for service accounts too.

**Why it is effective:** it works on any domain-joined Windows without the Active Directory module, so you and the help desk see the same answer.

**Trap:** `Last logon` comes from one domain controller and is not replicated, so another DC may know a newer one. Drives mapped in your normal session are invisible in an elevated prompt, and the other way round. `net stop http` stops every web service that depends on http.sys.

**Next step:** locked → event 4740 on a DC names the calling computer. Drive `Unavailable` → `Test-NetConnection fileserver -Port 445`. Slow copies → `Get-SmbConnection`.

### nltest / w32tm — which domain controller, is the machine trust intact, and is the clock close enough for Kerberos?
Match: nltest, w32tm, klist, gpresult, gpupdate, test-computersecurechannel
Instead of: rejoining the domain
Safety: read-only for `nltest`, `w32tm /query` and `/stripchart`, `klist`, `gpresult` · changes state: `w32tm /resync`, `klist purge`, `gpupdate /force`, `Test-ComputerSecureChannel -Repair` (resets the machine account password)

**In one line:** a domain logon needs a reachable DC, a valid machine account (the secure channel) and clocks within Kerberos' tolerance, 5 minutes by default; `nltest` checks the first two, `w32tm` the third, `klist` and `gpresult` the tickets and policies that follow.

**Read the command:** `nltest /sc_verify:corp.local`

| Part | Meaning |
|---|---|
| `/sc_verify:corp.local` | test this computer's secure channel with a DC of the domain |
| `/dsgetdc:corp.local` | which DC this machine finds, with its site and roles |
| `w32tm /query /status` | time source, last sync, phase offset |
| `w32tm /stripchart /computer:dc01 /samples:5` | the offset against one DC, 5 samples; `/resync` **syncs now** |
| `klist`, `klist purge` | the Kerberos tickets of this session / **delete** them to get new ones |
| `gpresult /r`, `gpupdate /force` | applied GPOs and their DC / **re-apply** policy now |
| `Test-ComputerSecureChannel -Repair -Credential CORP\admin` | **changes state**: repair the machine trust in place |

**What the output tells you:**

```
Flags: b0 HAS_IP  HAS_TIMESERV
Trusted DC Name \\dc01.corp.local
Trusted DC Connection Status Status = 0 0x0 NERR_Success
Trust Verification Status = 0 0x0 NERR_Success
The command completed successfully
```

Both `NERR_Success`: a DC answered and the trust holds. Anything else: no DC was reached (DNS, firewall, site) or the machine password no longer matches, which users see as "The trust relationship between this workstation and the primary domain failed". In `w32tm`, `Source: Local CMOS Clock` means no time source.

**Why it is effective:** "random" logon failures become three checkable facts, each with its own fix.

**Compared with rejoining the domain:** that fixes the trust too, but needs a local administrator and a restart.

**Trap:** `/dsgetdc` may return a cached DC (`/force` rediscovers). A small offset means nothing if the source is the local clock. On a VM, the hypervisor's time sync can fight w32tm.

**Next step:** no DC → `Resolve-DnsName _ldap._tcp.dc._msdcs.corp.local -Type SRV`, then ports 88 and 389. Broken trust → `-Repair`. Skew → the time chain up to the PDC emulator.

### Get-Volume / Get-ChildItem — how full is each volume, how healthy is the disk, and which folders use the space?
Match: get-volume, get-childitem, get-physicaldisk, get-disk, get-partition, get-psdrive, dir, cleanmgr
Instead of: dir /s, Explorer
Safety: read-only · a recursive scan of C:\ reads every folder and takes minutes

**In one line:** `Get-Volume` is Windows' `df -h`, `Get-PhysicalDisk` adds disk type and health, and this `Get-ChildItem` pipeline is the `du` that names the folders eating the space.

**Read the command:** `Get-ChildItem C:\ -Directory | ForEach-Object { [pscustomobject]@{ Dir=$_.FullName; GB=[math]::Round((Get-ChildItem $_ -Recurse -File -EA SilentlyContinue | Measure-Object Length -Sum).Sum/1GB,2) } } | Sort GB -Descending | Select -First 10`

| Part | Meaning |
|---|---|
| `Get-ChildItem C:\ -Directory` | the top-level folders of C: |
| `ForEach-Object { [pscustomobject]@{ … } }` | per folder (`$_`), one result object with `Dir` and `GB` |
| `-Recurse -File -EA SilentlyContinue` | every file below it; `-EA` = `-ErrorAction`: skip unreadable folders |
| `Measure-Object Length -Sum`, `/1GB` | the total in bytes, divided by the constant `1GB` |
| `Sort GB -Descending | Select -First 10` | the ten biggest |
| `Get-Volume` | per volume: letter, file system, `HealthStatus`, `SizeRemaining`, `Size` |
| `Get-PhysicalDisk | Select FriendlyName,MediaType,HealthStatus` | SSD or HDD and disk health (`Get-Disk`, `Get-Partition`: the `lsblk` view) |

**What the output tells you:**

```
DriveLetter FileSystem HealthStatus SizeRemaining   Size
C           NTFS       Healthy            12.1 GB 250 GB
```

About 5% free on C: is too little: updates, shadow copies and the page file need room; aim for 10–15%. A `HealthStatus` other than `Healthy` → chkdsk and the disk.

**Why it is effective:** free space says that a volume is full; the ranking says what to clean, Windows' own space users included (`C:\Windows\Installer`, WinSxS).

**Compared with `dir /s` and Explorer:** one folder's total at a time; the ranking needs the loop.

**Trap:** `-Directory` skips the files in `C:\` itself, where `pagefile.sys` and `hiberfil.sys` can hold tens of GB. Unreadable folders count as 0: run elevated. WinSxS hard links make it look bigger than it is. In Windows PowerShell 5.1, `$_` passed as a path can become the bare folder name, resolved against the current directory: `$_.FullName` is safer.

**Next step:** WinSxS → `DISM /Online /Cleanup-Image /StartComponentCleanup`. Shadow copies → `vssadmin list shadowstorage`. Unhealthy disk → `chkdsk`. Related: `cleanmgr` is the Disk Cleanup GUI (its "Clean up system files" button also removes old update files; Settings › System › Storage offers the same). `dir` is cmd's listing and PowerShell's alias of `Get-ChildItem`: `dir C:\Windows\Minidump` shows the small dump files that blue screens usually leave, one per crash, read with WinDbg (`!analyze -v`).

### chkdsk — is the NTFS file system damaged, and can Windows repair it?
Match: chkdsk, fsutil, sfc, defrag
Instead of: —
Safety: read-only without switches · changes state: `/f` repairs and locks the volume (C: is checked at the next restart); `/r` reads every sector, for hours; `sfc /scannow` replaces system files

**In one line:** `chkdsk` checks a volume's file system and, with `/r`, its surface; `fsutil dirty query` shows whether a boot-time check is pending; `sfc` checks Windows' own system files, a different kind of damage.

**Read the command:** `chkdsk D: /f /r`

| Part | Meaning |
|---|---|
| `D:` | the volume (`chkdsk C:` alone: a read-only scan) |
| `/f` | **changes state**: fix errors; a volume in use is dismounted first, C: waits for the restart |
| `/r` | also find bad sectors and recover readable data; includes `/f`; slow |
| `fsutil dirty query C:` | `is Dirty` = a check runs at the next boot |
| `sfc /scannow` | **changes state**: verify and repair protected system files |

**What the output tells you:**

```
Windows has scanned the file system and found no problems.
No further action is required.
```

Otherwise it asks you to run CHKDSK with `/f`. sfc ends in one of three ways: no integrity violations; corrupt files repaired (details in `C:\Windows\Logs\CBS\CBS.log`); or some it could not fix, which calls for `DISM /Online /Cleanup-Image /RestoreHealth`, a restart and sfc again.

**Why it is effective:** "Windows is broken" has three repairs, the file system (`/f`), bad sectors (`/r`, then a new disk) and system files (sfc, DISM), and these commands say which one you need.

**Trap:** a read-only scan of a busy volume can report errors that are not real. `/r` stresses a failing disk: back up first. A dismount closes every open file on the volume. chkdsk does not judge the hardware; SMART and `Get-PhysicalDisk` do.

**Next step:** errors → back up, then `/f` in a maintenance window. Bad sectors, or events 7 and 153 → replace the disk. sfc stuck → DISM, restart, sfc. Related: `defrag C: /A` (elevated) only analyses fragmentation; `/O` optimises the right way for the media (defragments an HDD, retrims an SSD). Windows runs this weekly as the `ScheduledDefrag` task, so a badly fragmented HDD usually means that task is disabled or failing.

### schtasks / Get-ScheduledTask — what runs on a schedule or at boot, as whom, and did it succeed?
Match: schtasks, get-scheduledtask, get-scheduledtaskinfo
Instead of: Task Scheduler (taskschd.msc)
Safety: read-only for `/query` and the `Get-` cmdlets · changes state: `schtasks /create`, `/change` and `/delete`, often for tasks that run as SYSTEM

**In one line:** Task Scheduler is Windows' cron with more triggers (boot, logon, events); these commands list each task's state, account, command, last run and result: the answer to "something runs every night" or "it came back".

**Read the command:** `schtasks /query /fo LIST /v`

| Part | Meaning |
|---|---|
| `/query /fo LIST` | list the tasks, one field per line (`TABLE` and `CSV` also exist) |
| `/v` | verbose: run-as user, command, schedule, last run time and result |
| `/create /tn "Start SlowCatch" /sc onstart /ru SYSTEM /tr "logman start SlowCatch"` | **changes state**: a task that runs that command at startup, as SYSTEM |
| `Get-ScheduledTask | Where-Object State -ne 'Disabled' | Where-Object TaskName -like '*report*'` | enabled tasks with a matching name |
| `Get-ScheduledTaskInfo "\Microsoft\Windows\Defrag\ScheduledDefrag"` | `LastRunTime`, `LastTaskResult`, `NextRunTime` |

**What the output tells you:**

```
TaskName:                             \Start SlowCatch
Status:                               Ready
Last Run Time:                        10/3/2026 6:02:11 AM
Last Result:                          0
Task To Run:                          logman start SlowCatch
Run As User:                          SYSTEM
```

`Last Result` 0 = success, 267009 (0x41301) = running now, 267011 (0x41303) = never run; other values are the program's error codes. `Ready` with a non-zero result is a task failing quietly every night.

**Why it is effective:** tasks hide in folders such as `\Microsoft\Windows\…`, run as SYSTEM and fire on events; one listing with account, command and result finds the 2 a.m. job, or the task that restarts what you stopped.

**Compared with Task Scheduler:** the same tasks plus a History tab, fine at a desktop.

**Trap:** there are hundreds of built-in tasks: filter by name or folder. A `/ru SYSTEM` task runs with full rights, so check its `/tr` command.

**Next step:** a task at the slow time → its action and owner. Programs started at logon → `Get-CimInstance Win32_StartupCommand`. A returning service → `sc.exe qfailure`.

### findstr / Get-Content — the Windows grep and tail, for command output and log files
Match: findstr, get-content, more
Instead of: find
Safety: read-only · logs under C:\Windows usually need an elevated prompt

**In one line:** `findstr` keeps the lines that contain a string or match a simple regex, in cmd and PowerShell; `Get-Content -Tail` prints the end of a file, and `-Wait` follows it like `tail -f`.

**Read the command:** `netstat -ano -p tcp | findstr /C:":443 "`

| Part | Meaning |
|---|---|
| `/C:":443 "` | one literal string, space included, so `:4430` does not match |
| `findstr :443` | a plain search: also matches `:4430` |
| `/b /i /c:"OS Name" /c:"OS Version"` | several phrases, any one matches; `/i` any case; `/b` only at the start of a line (or `BIOS Version` matches too) |
| `/R` | regular expressions (`.`, `*`, `^`, `$`, `[ ]`; no `+`, no alternation) |
| `Get-Content …\pfirewall.log -Tail 20` | the last 20 lines; add `-Wait` to follow |

**What the output tells you:**

```
  TCP    0.0.0.0:443            0.0.0.0:0              LISTENING       4
  TCP    10.0.1.10:52011        203.0.113.20:443       ESTABLISHED     7788
```

The string matches anywhere on the line: a listener on 443, then an outgoing connection to a remote port 443. Check the column before acting on a PID.

**Why it is effective:** it is on every Windows, it filters cmd tools that have no filters of their own, and `/C:` matches exactly.

**Compared with `find`:** `find "LISTENING"` searches one literal string, fine for one word, with no regex and no alternatives.

**Trap:** `findstr /i "OS Name"` matches every line containing OS or Name (`Host Name` too): `/C:"OS Name"` searches the phrase. `Get-Content` without `-Tail` reads the whole file. On PowerShell objects, `Where-Object` beats filtering text.

**Next step:** a PID → `tasklist /fi "PID eq N"` or `Get-Process -Id N`. A DROP line in the firewall log → the Windows Firewall card. Related: `| more` pages long output in cmd and PowerShell (Space: next page, Enter: next line, Q: quit), as in `schtasks /query /fo LIST /v | more`.

### Select-Object / Where-Object / Sort-Object — PowerShell's pipeline: filter, sort, group and pick columns
Match: select-object, where-object, sort-object, format-table, format-list, foreach-object, measure-object, group-object, out-null
Instead of: findstr on PowerShell output
Safety: read-only · these cmdlets only reshape what the previous command returns

**In one line:** PowerShell passes objects, not text; these cmdlets are its `grep`, `sort`, `uniq -c`, `awk` and `column`: filter on a property, sort numbers as numbers, group and count, add up, choose the display.

**Read the command:** `Get-NetTCPConnection -State Established | Group-Object RemoteAddress | Sort-Object Count -Descending | Select-Object -First 10 Count, Name`

| Part | Meaning |
|---|---|
| `Group-Object RemoteAddress` | one group per value, with `Count` and `Name` (like `uniq -c`) |
| `Sort-Object Count -Descending` | sort on a property, numerically |
| `Select-Object -First 10 Count, Name` | the first 10 objects, these properties; also `-Last 1`, and `-ExpandProperty X` to unwrap a nested list |
| `Where-Object State -ne 'Disabled'` | keep matching objects: `-eq`, `-ne`, `-gt`, `-like '*sql*'`, `-notin` |
| `@{n='MB/s'; e={ … }}` | a calculated property; `$_` is the current object |
| `ForEach-Object { … }`, `Measure-Object Length -Sum` | run a block per object; count, sum, average or maximum |
| `Format-Table -AutoSize`, `Format-List` | display only, always last: sized columns / one property per line |

**What the output tells you:**

```
Count Name
----- ----
  412 203.0.113.50
   37 10.0.1.20
```

One client holds 412 connections: a proxy, a load balancer or a connection leak. `Where`, `Select`, `Sort` and `%` are the short aliases seen in one-liners.

**Why it is effective:** filters compare properties, so 443 never matches 4430 and numbers sort as numbers, for processes, services, events, sockets and counters alike.

**Compared with `findstr` on PowerShell output:** it filters the rendered text, cut to the window width and missing every property not displayed; fine for a cmd tool's output.

**Trap:** `Format-*` output is display data: anything after it (`Sort-Object`, `Export-Csv`) gets nonsense, so put it last. Tables cut long values with `…`: use `Format-List` or `-Wrap`. `-like` takes wildcards, `-match` a regex.

**Next step:** build a one-liner one stage at a time; `Get-Member` lists the properties you can filter, sort and select. Related: `| Out-Null` throws the output away (PowerShell's `> /dev/null`); errors still show.

### networksetup / ipconfig getifaddr — which service is which device, with its DNS, proxy, MTU and DHCP lease
Match: networksetup, ipconfig getifaddr, ipconfig getpacket
Instead of: ifconfig, System Settings
Safety: read-only for `-list…`, `-get…` and `ipconfig get…` · changes state: `-setdnsservers` and the other `-set…` options apply at once and persist

**In one line:** macOS configures networks per network service (Wi-Fi, Ethernet, VPN), not per device; `networksetup` reads and sets each service's DNS, proxy and MTU, and macOS's own `ipconfig` prints one interface's address and DHCP lease.

**Read the command:** `networksetup -getdnsservers Wi-Fi`

| Part | Meaning |
|---|---|
| `-getdnsservers Wi-Fi` | DNS servers set by hand on the service `Wi-Fi` |
| `-listallhardwareports` | each port (Wi-Fi, Ethernet…) with its device (`en0`) and MAC |
| `-setdnsservers Wi-Fi 1.1.1.1 8.8.8.8` | **changes state**: set them (`Empty` returns to DHCP) |
| `-getwebproxy Wi-Fi`, `-getMTU en0` | the service's HTTP proxy; a device's MTU |
| `ipconfig getifaddr en0`, `ipconfig getpacket en0` | the IPv4 address; the DHCP answer (server, router, DNS, lease) |

**What the output tells you:**

```
$ networksetup -listallhardwareports
Hardware Port: Wi-Fi
Device: en0
Ethernet Address: 02:00:00:12:34:56
$ networksetup -getdnsservers Wi-Fi
There aren't any DNS Servers set on Wi-Fi.
$ ipconfig getifaddr en0
192.0.2.25
```

"There aren't any DNS Servers set" means DHCP or a VPN supplies them, not that DNS is missing. The port map says which `enN` to give `tcpdump` or `networkQuality -I`.

**Why it is effective:** DNS servers and proxies set by hand on a service override DHCP and survive network changes; this is where those leftovers hide.

**Compared with `ifconfig`:** addresses, flags and MTU per interface, enough for "do I have an address?", but no services, DNS or proxies.

**Trap:** `-getdnsservers` lists only manual servers; `scutil --dns` shows what is really in force. Quote service names that contain spaces. Note the old values before any `-set…`.

**Next step:** DNS doubts → `scutil --dns`. Unexpected proxy → `scutil --proxy`, configuration profiles. No address → `ipconfig getpacket en0`, then the cable or Wi-Fi (`wdutil info`).

### scutil --dns / dscacheutil — which resolvers macOS really uses, and what an app gets for a name
Match: scutil, dscacheutil, dns-sd
Instead of: cat /etc/resolv.conf, nslookup, dig
Safety: read-only for `scutil --dns`, `--proxy` and `dscacheutil -q` · flushing the cache (`dscacheutil -flushcache` and `killall -HUP mDNSResponder`, with sudo) is harmless

**In one line:** `scutil --dns` prints the resolver configuration in force, including the per-domain resolvers VPN clients add; `dscacheutil -q host` resolves a name the way applications do.

**Read the command:** `scutil --dns`

| Part | Meaning |
|---|---|
| `--dns` | each resolver: search domains, nameservers, interface (`if_index`), and the domain it serves |
| `--proxy` | the proxy settings in force |
| `dscacheutil -q host -a name app.example.com` | resolve like an app: system resolver, `/etc/hosts`, cache |
| `dscacheutil -flushcache` + `killall -HUP mDNSResponder` | **flush** the DNS cache (the usual pair) |
| `dns-sd -B _ssh._tcp` | browse Bonjour (mDNS) services of that type |

**What the output tells you:**

```
resolver #1
  search domain[0] : corp.internal
  nameserver[0] : 10.0.1.5
  if_index : 17 (utun3)
resolver #2
  domain   : local
  options  : mdns
```

Resolver #1 answers by default, and `utun3` shows that a VPN pushed it. A resolver with a `domain :` line serves only that domain (split DNS); `local` goes to multicast DNS. `dscacheutil -q host` answers with `name:` and `ip_address:` lines: what Safari, curl and ssh will use.

**Why it is effective:** macOS's `/etc/resolv.conf` is a compatibility file without the per-domain resolvers, so split-DNS and stale-VPN problems show only here.

**Compared with `resolv.conf`, `nslookup` and `dig`:** dig and nslookup query one server directly, right for testing that server, but they bypass the system resolver, `/etc/hosts` and the per-domain rules: hence "dig works, the browser does not".

**Trap:** `scutil` without options opens an interactive prompt (`quit` leaves). A VPN that disconnects badly can leave its resolver behind. `-flushcache` alone may leave mDNSResponder's cache in place.

**Next step:** stale VPN resolver → reconnect or restart the VPN client. `dig` and `dscacheutil` disagree → `/etc/hosts`, per-domain resolvers, profiles. Proxy in force → `networksetup -getwebproxy`.

### log show / log stream — search and follow macOS's unified log
Match: log show, log stream, log collect, sysdiagnose
Instead of: tail -f /var/log/system.log, Console
Safety: read-only · `log collect` and `sudo sysdiagnose` write large archives that can contain personal data

**In one line:** most macOS daemons and apps log only to the unified log, a structured binary store; `log show` searches it by time and predicate, `log stream` follows it live like `journalctl -f`, `log collect` archives it.

**Read the command:** `log show --last 1h --predicate 'process == "sshd"'`

| Part | Meaning |
|---|---|
| `--last 1h` | the time window (`10m`, `2h`, `1d`) |
| `--predicate 'process == "sshd"'` | filter on `process`, `subsystem`, `category` or `eventMessage`; `CONTAINS[c]` = contains, any case |
| `--style compact` | one short line per entry (`json` and `syslog` too) |
| `--info`, `--debug` | include Info and Debug entries, left out by default |
| `stream --predicate 'process == "myapp"'` | new entries live, until Ctrl-C |
| `collect --output app.logarchive` | an archive that Console or `log show` can open |
| `sysdiagnose` | Apple's full diagnostic bundle; takes minutes |

**What the output tells you:** with `--style compact`:

```
Timestamp               Ty Process[PID:TID]
2026-10-03 10:42:11.512 Df sshd[812:2f41c] Accepted publickey for deploy from 192.0.2.50 port 51712 ssh2
2026-10-03 10:42:19.004 E  myapp[3311:9a12] connection to 10.0.1.20:5432 refused
```

`Ty` is the level: `Df` default, `I` info, `Db` debug, `E` error, `F` fault; then the process with PID and thread, then the message. `<private>` marks redacted personal data.

**Why it is effective:** entries carry process, subsystem and level, so one predicate selects exactly one daemon over any window, with no rotated files to piece together.

**Compared with `system.log` and Console:** `/var/log/system.log` receives only a few legacy daemons; Console shows the same unified log with a search field, fine interactively.

**Trap:** `--last 1h` without a predicate prints hundreds of thousands of lines. Debug entries are not kept on disk by default: catch them live with `log stream --level debug`. Single quotes go around the predicate, double quotes inside it.

**Next step:** a daemon's errors → `launchctl print` for its plist and log files. App crashes → the `.ips` reports under `Library/Logs/DiagnosticReports`. A case for Apple or a vendor → `sysdiagnose`.

### launchctl — is this launchd job loaded and running, what does it run, and how do I restart or stop it?
Match: launchctl, plutil, periodic
Instead of: kill, ps
Safety: read-only for `list` and `print` · changes state: `bootstrap`/`bootout` load and unload, `kickstart -k` kills and restarts, `disable` blocks loading until `enable`; the system domain needs sudo

**In one line:** launchd is macOS's systemd: it starts daemons (system) and agents (per user) from plist files and restarts `KeepAlive` jobs; `launchctl` lists jobs with PID and last exit status, prints one job's state, and loads, unloads, restarts or disables it.

**Read the command:** `launchctl print system/com.openssh.sshd`

| Part | Meaning |
|---|---|
| `print` | one job: program, arguments, plist path, state, stdout and stderr paths, last exit code |
| `system/com.openssh.sshd` | domain and label: `system/` for daemons, `gui/$(id -u)/` for your own agents |
| `list` | `PID` (`-` = not running), `Status` (last exit code), `Label`; with `sudo` for daemons |
| `bootstrap system /Library/LaunchDaemons/com.example.plist` | **load** a daemon from its plist |
| `bootout system/com.example.daemon` | **unload** and stop it (it returns at boot unless disabled or removed) |
| `kickstart -k system/com.example.daemon` | **restart**: `-k` kills the running instance first |
| `disable gui/$(id -u)/LABEL` | **keep it from loading**, until `enable` |
| `plutil -lint FILE.plist` | syntax-check a plist before loading it |

**What the output tells you:**

```
$ launchctl list | head -4
PID     Status  Label
812     0       com.docker.helper
-       0       com.apple.SafariHistoryServiceAgent
-       78      com.example.badjob
```

`-` with 0: loaded, not running, last run fine. `-` with a non-zero status: it exited with that code and is failing (a negative number is the signal that killed it). `print`'s `stdout path` and `stderr path` show where the job's own output goes.

**Why it is effective:** `ps` shows that a process runs; launchctl shows who starts it, from which plist, where it logs, and whether it will come back after a kill.

**Compared with `kill` and `ps`:** kill stops a hung app now, but launchd restarts a `KeepAlive` job at once.

**Trap:** without sudo, `list` shows only your own jobs. `load` and `unload` still work but are legacy. `bootout system/com.openssh.sshd` over SSH cuts you off. `gui/UID` exists only while that user is logged in at the screen.

**Next step:** failing job → its stdout and stderr files, then `log show --predicate 'process == "NAME"'`. Back after a kill → `bootout`, then `disable`. `homebrew.mxcl.*` jobs → `brew services`. Edited plist → `plutil -lint`, `bootout`, `bootstrap`. Related: `sudo periodic daily weekly monthly` runs the BSD maintenance scripts in `/etc/periodic/` now instead of when launchd schedules them; their output goes to `/var/log/daily.out`, `weekly.out` and `monthly.out`.

### diskutil — which disks, APFS containers and volumes exist; verify, repair, mount or eject them
Match: diskutil
Instead of: df
Safety: read-only for `list`, `info`, `apfs list` and `verifyVolume` · changes state: `repairVolume`, `mount`, `unmountDisk` and `eject` act at once; close files on that disk first

**In one line:** Disk Utility on the command line: the disks, the APFS containers on them and their volumes, one volume's details, checks and repairs, mounting and ejecting.

**Read the command:** `diskutil list`

| Part | Meaning |
|---|---|
| `list` | every disk with its partitions, containers and volume identifiers (`disk3s1`…) |
| `info disk3s1` | mount point, file system, size, free space, read-only or not |
| `apfs list` | each container's capacity and what each of its volumes consumes |
| `verifyVolume /` | check the file system without repairing |
| `repairVolume /Volumes/Data` | **changes state**: check and repair |
| `mount disk3s2` | **changes state**: mount a volume that did not mount |
| `unmountDisk /dev/disk4`, `eject /dev/disk4` | **changes state**: unmount all its volumes / and eject it |

**What the output tells you:**

```
/dev/disk3 (synthesized):
   #:                       TYPE NAME                    SIZE       IDENTIFIER
   0:      APFS Container Scheme -                      +994.7 GB   disk3
   1:                APFS Volume Macintosh HD            11.2 GB    disk3s1
   2:                APFS Volume Macintosh HD - Data     680.9 GB   disk3s5
```

`synthesized`: an APFS container shown as a disk. Its volumes share the free space, so `df` shows the same available space for each. `Macintosh HD` is the sealed system volume; your files live on `Macintosh HD - Data`. `(external, physical)` marks a USB or Thunderbolt disk.

**Why it is effective:** APFS makes `df` look wrong (shared space, snapshots, a read-only system volume); the container view explains it, and its identifiers drive every other diskutil command.

**Compared with `df`:** correct sizes for mounted volumes, but no containers, no unmounted volumes, and no disk behind each volume.

**Trap:** identifiers like `disk4` change between boots and plug-ins: run `list` again right before unmounting, ejecting or anything destructive. `Resource busy` means open files. Repair the startup volume from Recovery.

**Next step:** space puzzles → `tmutil listlocalsnapshots /`, then `du`. Errors on a data disk → `repairVolume`, then a backup. Busy → `lsof` to find the process.

### tmutil — are Time Machine snapshots eating the disk, and is a backup running now?
Match: tmutil
Instead of: du, deleting files
Safety: read-only for `listlocalsnapshots`, `status`, `latestbackup`, `listbackups` and `compare` · changes state: `deletelocalsnapshots` and `thinlocalsnapshots` delete for good; `stopbackup` stops the running backup

**In one line:** Time Machine also keeps APFS local snapshots on the internal disk; tmutil lists and deletes them, the usual answer to "the disk is full but my files do not add up", and reports the backup state.

**Read the command:** `tmutil thinlocalsnapshots / 20000000000 4`

| Part | Meaning |
|---|---|
| `thinlocalsnapshots /` | **delete** local snapshots of `/` until enough space is free |
| `20000000000` | the bytes to free (about 20 GB) |
| `4` | urgency 1–4; 4 is the most aggressive |
| `listlocalsnapshots /`, `deletelocalsnapshots 2026-08-08-120000` | list the snapshots / **delete** the one with that date |
| `status` | whether a backup runs, its phase and progress |
| `latestbackup`, `listbackups`, `compare -s` | the newest backup, all backups, what differs from the newest |
| `stopbackup` | **changes state**: stop the running backup (it resumes at the next scheduled run) |

**What the output tells you:**

```
$ tmutil listlocalsnapshots /
com.apple.TimeMachine.2026-08-08-120000.local
$ tmutil status
Backup session status:
{
    BackupPhase = Copying;
    Percent = "0.41";
    Running = 1;
}
```

Snapshot names carry the date that `deletelocalsnapshots` needs. `Running = 1` at `Percent = "0.41"`: a backup is 41% done and competing for the disk; `Running = 0`: idle.

**Why it is effective:** snapshot space appears in no folder, so `du` and Finder miss it; thinning or deleting snapshots gets it back now (macOS also thins them as space runs low, hence "purgeable").

**Compared with `du` and deleting files:** du finds big folders, right when files are the problem, but deleting files frees nothing while a snapshot still holds them.

**Trap:** deleted snapshots are gone, and with them the local restore points. A backup in working hours slows the Mac (`backupd` in `fs_usage`).

**Next step:** small snapshots → `du -sh`, `diskutil apfs list`. A backup slowing work → let it finish or `stopbackup`. Space keeps vanishing → swap and caches (the vm_stat card).

### pmset — why did the Mac sleep or wake, what keeps it awake, and is it throttled by heat?
Match: pmset, caffeinate, powermetrics
Instead of: Energy settings in System Settings
Safety: read-only for `pmset -g …` and `powermetrics` (sudo) · `caffeinate` holds a no-sleep assertion only while it runs; `pmset` without `-g` changes settings (not covered)

**In one line:** `pmset -g` reads power management: settings, battery, the assertions keeping the Mac awake, a log of sleeps and wakes with reasons, thermal limits; `caffeinate` keeps the Mac awake while a job runs.

**Read the command:** `pmset -g log | grep -E "Sleep|Wake" | tail`

| Part | Meaning |
|---|---|
| `-g`, `-g batt` | the current settings (sleep timers…); battery %, charging, power source |
| `-g log` | the power history: Sleep, Wake, DarkWake, each with a reason |
| `-g assertions` | what prevents sleep now, and which process holds it |
| `-g therm` | thermal warnings and `CPU_Speed_Limit` (Intel Macs) |
| `caffeinate -i long_job.sh` | run the job while preventing idle sleep |
| `sudo powermetrics --samplers thermal -n 1` | one sample of the thermal pressure level (`Nominal` … `Critical`) |

**What the output tells you:** `pmset -g assertions`, shortened:

```
Listed by owning process:
   pid 412(caffeinate): [0x0001] 00:42:10 PreventUserIdleSystemSleep named: "caffeinate command-line tool"
   pid 901(myapp): [0x0002] 00:05:12 PreventUserIdleDisplaySleep named: "Playing video"
```

`PreventUserIdleSystemSleep` keeps the Mac awake; a `DisplaySleep` assertion only the screen. In `-g log`, the text after "due to" is the reason for each sleep or wake, which dates when an overnight job stopped. `CPU_Speed_Limit = 56`: the CPU runs at 56% speed because of heat.

**Why it is effective:** "my overnight job died" and "the Mac never sleeps" get a timestamp and a culprit instead of guesses.

**Compared with System Settings:** the configured timers, not what happened or who overrides them.

**Trap:** `caffeinate -i` stops idle sleep only: closing the lid still sleeps a laptop without an external display and power. `-g log` is long: filter it. On Apple Silicon, read thermal pressure from `powermetrics`.

**Next step:** slept mid-job → `caffeinate`, or a launchd job. Heavy thermal pressure → airflow, vents, sustained load. Battery doubts → `system_profiler SPPowerDataType`.

### networkQuality / wdutil — how fast is this link under load, and how good is the Wi-Fi radio?
Match: networkquality, wdutil
Instead of: a speed-test website, ping
Safety: read-only · networkQuality loads the link to Apple's servers during the test; `wdutil` needs sudo

**In one line:** `networkQuality` measures capacity in both directions and, at the same time, latency under that load ("responsiveness"), which exposes bufferbloat; `wdutil info` shows the Wi-Fi radio: RSSI, noise, channel, rate.

**Read the command:** `networkQuality -I en0`

| Part | Meaning |
|---|---|
| `networkQuality` | download and upload at the same time, then a summary |
| `-s` | sequential: one direction after the other |
| `-I en0` | test through this interface (Wi-Fi versus Ethernet) |
| `sudo wdutil info` | Wi-Fi: `RSSI`, `Noise`, `Tx Rate`, `Channel`, `PHY Mode` |

**What the output tells you:**

```
Uplink capacity: 21.344 Mbps
Downlink capacity: 286.120 Mbps
Responsiveness: Medium (146.341 milliseconds | 410 RPM)
Idle Latency: 24.500 milliseconds
    RSSI                 : -73 dBm
    Noise                : -91 dBm
```

RPM is round trips per minute under load (60000 ÷ RPM = ms): higher is better. 24.5 ms idle rising to 146 ms under load is bufferbloat: calls and SSH lag whenever someone uploads. The last two lines come from `wdutil`: RSSI minus noise is the SNR, 18 dB here, which is weak; about 25 dB or more is comfortable.

**Why it is effective:** a speed test gives Mbps only; responsiveness shows how interactive traffic feels on a busy link, and `wdutil` shows whether the radio is the bottleneck.

**Compared with a speed-test website and `ping`:** both measure something useful (capacity; idle latency and loss), but neither shows latency under load.

**Trap:** it measures the path to Apple, not to your server (use `iperf3` for that). A VPN changes the route and the result. The layout varies by macOS version, and `wdutil` may redact fields.

**Next step:** low responsiveness → queue management (SQM) on the bottleneck router. Weak SNR → closer, 5 GHz, or a cable. Fine here but slow to your server → `mtr`, `iperf3`.

### vm_stat / memory_pressure — is this Mac short of memory right now?
Match: vm_stat, memory_pressure
Instead of: top's PhysMem line, Activity Monitor's free memory
Safety: read-only

**In one line:** macOS compresses memory before it swaps, so "free" is always small; `memory_pressure` prints the free percentage behind Activity Monitor's graph, and `vm_stat 1` per-second page counters, where swap-outs are the real pain.

**Read the command:** `vm_stat 1`

| Part | Meaning |
|---|---|
| `vm_stat` | page counters, in pages (size in the header: 16384 bytes on Apple Silicon, 4096 on Intel) |
| `1` | a line per second: the first holds totals since boot, the next ones the change |
| `swapins`, `swapouts` | the last two columns: pages read from and written to swap; 0 when healthy |
| `cmprssor`, `comprs` | pages held by the compressor; pages compressed in the interval |
| `memory_pressure | tail -n 1` | only the line "System-wide memory free percentage" |

**What the output tells you:**

```
$ memory_pressure | tail -n 1
System-wide memory free percentage: 8%
$ sysctl vm.swapusage
vm.swapusage: total = 4096.00M  used = 3411.25M  free = 684.75M  (encrypted)
```

8% free plus swap-outs per second in `vm_stat 1`: short of memory now (below about 10–15%, Activity Monitor's graph turns yellow or red). Swap used is history; swap-outs per second are the live signal, like `si`/`so` in Linux vmstat.

**Why it is effective:** the compressor hides pressure until it suddenly cannot; these numbers show it while closing something still helps.

**Compared with top's PhysMem line:** good for the compressor's size, but "unused" is small on a healthy Mac too.

**Trap:** multiply pages by the page size: reading 16 KB pages as 4 KB understates memory fourfold. Docker Desktop's VM reserves all its configured memory, so the biggest user may be the VM.

**Next step:** short of memory → `top -o mem`, shrink the container VM, close the biggest apps. Swap plus a busy disk → `fs_usage`.

### fs_usage / mdutil — which process is hammering the disk, and is it Spotlight?
Match: fs_usage, mdutil
Instead of: Activity Monitor's Disk tab, iostat
Safety: read-only for `fs_usage` (sudo, very verbose) and `mdutil -s` · changes state: `mdutil -E` rebuilds the index; `-i off`/`on` switches indexing for a volume

**In one line:** `fs_usage` traces file system and disk calls live with process and path, the macOS `strace` for files; `mdutil` shows and controls Spotlight indexing, the usual background disk user.

**Read the command:** `fs_usage -w -f diskio -t 10`

| Part | Meaning |
|---|---|
| `-w` | wide: full paths and process names |
| `-f diskio` | only physical disk I/O (`filesys`: file system calls; `network`: socket calls) |
| `-t 10` | stop after 10 seconds |
| `pid 1234`, `mds_stores` | trace one process, by PID or by name |
| `mdutil -s /` | the indexing state of a volume |
| `mdutil -i off /Volumes/Dev`, `mdutil -E /` | **changes state**: stop indexing a volume / erase and rebuild the index |

**What the output tells you:**

```
10:43:01.123412  RdData[A]  D=0x01a2b3c0  B=0x10000  /dev/disk4s1  /Volumes/Dev/shop/node_modules/.cache/4f1c.json  0.004211 W mds_stores.612
10:43:01.130021  WrData[A]  D=0x02b1c4d8  B=0x8000   /dev/disk3s5  /System/Volumes/VM/swapfile3                      0.012001 W kernel_task.0
```

`RdData`/`WrData`: a disk read or write; `B=` the size in hex; then device, file, duration and `process.PID`. Spotlight (`mds_stores`) reads a build cache nobody will search, and `kernel_task` writes to swap: memory pressure as well.

**Why it is effective:** it names the file and process behind each I/O: Spotlight on `node_modules`, a backup, or swap.

**Compared with Activity Monitor and `iostat`:** bytes per process, or throughput per disk; neither names the file.

**Trap:** unfiltered output floods: narrow it with `-f`, a process or `-t`, and pipe it into `head`. `mdutil -E` makes indexing heavier before it gets lighter. Folders on the system volume are excluded in System Settings → Spotlight.

**Next step:** `mds_stores` on development folders → stop indexing that volume or exclude the folders. `backupd` → `tmutil status`. `kernel_task` on the swap file → the vm_stat card.

### sw_vers / system_profiler — which macOS and hardware, plus SSD SMART, battery and Wi-Fi details
Match: sw_vers, system_profiler
Instead of: About This Mac
Safety: read-only · some data types take seconds; the hardware report includes serial numbers (remove them before sharing)

**In one line:** `sw_vers` prints the macOS version and build; `system_profiler` prints the System Information report, one data type at a time.

**Read the command:** `system_profiler SPHardwareDataType`

| Part | Meaning |
|---|---|
| `SPHardwareDataType` | model, chip or processor, cores, memory, serial number |
| `SPNVMeDataType` | the internal SSD: model, capacity, `S.M.A.R.T. Status` |
| `SPPowerDataType` | battery: `Cycle Count`, `Condition` |
| `SPAirPortDataType` | Wi-Fi: PHY mode, channel, signal / noise, rate |
| `sw_vers` | `ProductName`, `ProductVersion`, `BuildVersion` |

**What the output tells you:**

```
$ sw_vers
ProductName:    macOS
ProductVersion: 15.5
BuildVersion:   24F74
$ system_profiler SPHardwareDataType | grep -E 'Chip|Memory'
      Chip: Apple M3 Pro
      Memory: 18 GB
```

The build pins the exact patch level for bug reports. `Chip: Apple …` means Apple Silicon (arm64, Homebrew in `/opt/homebrew`); an Intel `Processor Name` means x86_64 (`/usr/local`). SMART `Verified` passes; `Failing` means back up now. A battery `Condition` other than `Normal` explains sudden shutdowns.

**Why it is effective:** version, build and hardware facts for every ticket, and disk and battery health without extra tools.

**Compared with About This Mac:** the same facts, but nothing to paste or script.

**Trap:** SMART here is one pass/fail word (`smartctl` from Homebrew shows the attributes). Without a data type, `system_profiler` runs the full, slow report.

**Next step:** SMART failing → back up, then replace. Worn battery → `pmset -g batt`. Wi-Fi → `wdutil info`. x86 binaries on Apple Silicon → `softwareupdate --install-rosetta`.

### brew / softwareupdate / pkgutil / xcode-select — Homebrew services and health, Apple updates, receipts, developer tools
Match: brew, softwareupdate, pkgutil, xcode-select
Instead of: launchctl for Homebrew jobs, System Settings → Software Update
Safety: read-only for `brew services list`, `brew doctor`, `brew list`, `softwareupdate -l`, `pkgutil`, `xcode-select -p` · changes state: `brew services restart/stop`, `brew install`, `softwareupdate -i -a` (a restart may follow), `xcode-select --install`

**In one line:** Homebrew installs Unix tools and runs some as launchd services (`brew services`, `brew doctor`); `softwareupdate` handles Apple's updates, `pkgutil` reads installer receipts, `xcode-select` points at the developer tools.

**Read the command:** `brew services list`

| Part | Meaning |
|---|---|
| `services list` | Homebrew jobs: `Name`, `Status` (`started`, `stopped`, `error`, `none`), `User`, plist |
| `services restart NAME`, `services stop NAME` | **restart** and start at login / **stop** and no longer start at login |
| `doctor` | check the install: permissions, unlinked or outdated pieces, missing tools |
| `list --versions`, `install mtr iperf3` | installed formulae with versions / **install** with dependencies |
| `softwareupdate -l`, `softwareupdate -i -a` | list Apple's updates / **install** them all |
| `pkgutil --pkgs`, `pkgutil --pkg-info com.example.pkg` | `.pkg` receipts / one package's version, location and install time |
| `xcode-select -p`, `xcode-select --install` | the active developer directory / **install** the Command Line Tools |

**What the output tells you:**

```
$ brew services list
Name          Status  User
postgresql@16 started ops
redis         error   ops
$ git --version
xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools), missing xcrun at: /Library/Developer/CommandLineTools/usr/bin/xcrun
```

`error`: the job exits with an error; `none`: not loaded. The xcrun error typically follows a macOS upgrade that removed the Command Line Tools.

**Why it is effective:** each software question on a Mac or a Mac build agent gets a one-line answer that a script can check.

**Compared with `launchctl` and System Settings:** `launchctl list` shows the same jobs (`homebrew.mxcl.NAME`) with PID and exit code, and `print` their log paths; brew services is simpler for start and stop. System Settings installs the same updates by hand.

**Trap:** `sudo brew services …` registers a root daemon and can leave root-owned files in the Homebrew prefix. Apple Silicon uses `/opt/homebrew`, Intel `/usr/local`: two installs, two PATHs. A receipt survives a deleted app. `softwareupdate -i -a` can restart a build agent mid-job.

**Next step:** `error` → `launchctl print gui/$(id -u)/homebrew.mxcl.NAME` for its log path. Tools broken after an upgrade → `xcode-select --install`, then `brew doctor`. Which package owns a file → `pkgutil --file-info PATH`.

### spctl / xattr — why does macOS refuse to run this app or binary?
Match: spctl, xattr, codesign, csrutil
Instead of: turning Gatekeeper off
Safety: read-only for `spctl --status`, `spctl -a`, `xattr -l`, `codesign -dv`, `csrutil status` · changes state: `xattr -d com.apple.quarantine` removes the download check from that file; only for files you trust and obtained on purpose

**In one line:** Gatekeeper checks downloaded code (signed? notarized?) before its first run, triggered by the quarantine attribute that browsers add; `spctl` shows the verdict, `xattr` the flag, `codesign` the signature, `csrutil` whether SIP is on.

**Read the command:** `spctl -a -vv /Applications/MyTool.app`

| Part | Meaning |
|---|---|
| `-a` | assess the app as Gatekeeper would at launch |
| `-vv` | add the source (such as `Notarized Developer ID`) and the signer |
| `spctl --status` | `assessments enabled` = Gatekeeper is on |
| `xattr -l tool-binary`, `xattr -d com.apple.quarantine tool-binary` | list the attributes / **remove** the quarantine flag |
| `codesign -dv --verbose=2 /Applications/MyTool.app` | identifier, team, signing authorities |
| `csrutil status` | System Integrity Protection on or off (why even root cannot change `/System`) |

**What the output tells you:**

```
$ spctl -a -vv /Applications/MyTool.app
/Applications/MyTool.app: rejected
source=no usable signature
$ xattr -l tool-binary
com.apple.quarantine: 0083;6703a1b2;Safari;
```

`rejected` with `no usable signature`: unsigned, hence "damaged" or "unidentified developer". `accepted` with `source=Notarized Developer ID` is signed and notarized. The quarantine value records flags, time and the downloading app.

**Why it is effective:** a vague "cannot be opened" becomes a precise reason (unsigned, not notarized, quarantined, broken signature), each with its own fix.

**Compared with turning Gatekeeper off:** the app runs, and so does every other unsigned download, on a machine that may hold production credentials.

**Trap:** for a plain command-line binary, `spctl -a` can answer "the code is valid but does not seem to be an app" even when it is fine. Removing quarantine skips the malware check. `sudo` does not bypass SIP or the privacy (TCC) permissions.

**Next step:** unsigned internal tool → sign and notarize it in CI, or unquarantine that one file. "Operation not permitted" despite sudo → Full Disk Access for the terminal, or SIP. Broken signature → reinstall.

### Get-HotFix / wusa / Get-WindowsUpdateLog — which update landed just before it broke, and how to take it back
Match: get-hotfix, wusa, get-windowsupdatelog
Instead of: Settings › Windows Update › Update history
Safety: read-only for `Get-HotFix` · `Get-WindowsUpdateLog` writes one text file · `wusa /uninstall` changes state: it removes an update, usually with a restart

**In one line:** `Get-HotFix` lists installed Windows updates with KB number, type and install date; `wusa /uninstall` removes one; `Get-WindowsUpdateLog` merges Windows Update's binary trace files into a readable `WindowsUpdate.log` on your desktop.

**Read the command:** `Get-HotFix | Sort InstalledOn -Descending | Select -First 10`

| Part | Meaning |
|---|---|
| `Sort InstalledOn -Descending`, `Select -First 10` | the ten newest; compare with when the trouble began |
| `-ComputerName web01` | ask another server |
| `wusa /uninstall /kb:5031234` | **changes state**: remove that update; `/quiet /norestart` = no prompts, no automatic restart |
| `Get-WindowsUpdateLog -LogPath C:\Temp\wu.log` | write the merged log there instead |

**What the output tells you:**

```
Source  Description      HotFixID   InstalledBy          InstalledOn
------  -----------      --------   -----------          -----------
WEB01   Security Update  KB5031234  NT AUTHORITY\SYSTEM  10/9/2026 12:00:00 AM
```

`InstalledOn` is a date only (midnight): match the day here, the hour in the event log.

**Why it is effective:** after a sudden break, a KB from the night before is a suspect you can name, look up and remove.

**Trap:** drivers, Defender definitions and apps do not appear, and some rows have no date. A cumulative update shipped together with a servicing stack update cannot be removed with `wusa`: use `DISM /Online /Remove-Package`. A removed update returns at the next scan unless you pause or decline it.

**Next step:** the hour → `Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WindowsUpdateClient'}` (19 installed, 20 failed). Failed installs → `WindowsUpdate.log`, then `sfc` and DISM (the chkdsk card).

### bcdedit / msconfig — what does Windows boot, and why does it keep starting in Safe Mode?
Match: bcdedit, msconfig
Instead of: —
Safety: read-only for `bcdedit /enum` (elevated prompt) · changes state: `/set` and `/deletevalue` edit the boot configuration, and so does msconfig's Boot tab · keep the BitLocker recovery key at hand before boot changes

**In one line:** the Boot Configuration Data (BCD) is Windows' GRUB configuration; `bcdedit /enum` lists the boot manager and every loader entry with its options, and `msconfig` shows the common ones in a window.

**Read the command:** `bcdedit /enum`

| Part | Meaning |
|---|---|
| `/enum` | the active entries; `/enum all` adds hidden and recovery entries, `/v` shows GUIDs instead of names |
| `{current}`, `{default}` | the running entry; the one booted by default |
| `/deletevalue {current} safeboot` | **changes state**: stop starting in Safe Mode |
| `msconfig` | Boot tab (Safe boot, timeout); Services tab for a clean boot |

**What the output tells you:**

```
Windows Boot Loader
-------------------
identifier              {current}
path                    \Windows\system32\winload.efi
description             Windows Server
safeboot                Minimal
```

`winload.efi` means UEFI (`winload.exe`: legacy BIOS). A `safeboot` line means every restart enters Safe Mode: `Minimal` without network, `Network` with it.

**Why it is effective:** a server that comes back after "just a restart" without network or services usually carries a forgotten `safeboot` value, and this one listing shows it.

**Trap:** in PowerShell, quote the braces (`"{current}"`): bare `{…}` is a script block. Ticking Safe boot in msconfig stays in force until you untick it.

**Next step:** remove `safeboot`, restart. No boot at all → Windows Recovery Environment (from a running system: `shutdown /r /o /t 0`), Startup Repair.

### Enter-PSSession / Invoke-Command — PowerShell remoting: a shell on one server, or one command on many
Match: enter-pssession, invoke-command, test-wsman, enable-psremoting
Instead of: an RDP session for a one-line check
Safety: the remote commands run with your rights and can change anything they could change locally · `Enable-PSRemoting` changes state: it starts WinRM, adds a listener and firewall rules

**In one line:** Windows' ssh: WinRM carries PowerShell over TCP 5985 (HTTP, with the content encrypted by Kerberos or NTLM) or 5986 (HTTPS); `Enter-PSSession` opens a remote prompt, `Invoke-Command` runs a script block on many servers at once.

**Read the command:** `Invoke-Command -ComputerName srv01,srv02 -ScriptBlock { Get-Service spooler }`

| Part | Meaning |
|---|---|
| `-ComputerName srv01,srv02` | the targets, in parallel; each result carries `PSComputerName` |
| `-ScriptBlock { … }` | the code run on each target |
| `Enter-PSSession -ComputerName srv01` | an interactive prompt, `[srv01]: PS C:\…>`; `exit` leaves |
| `Test-WSMan srv01` | does a WinRM listener answer? |
| `Enable-PSRemoting -Force` | on the target, elevated: turn remoting on without prompts |

**What the output tells you:** `Test-WSMan` returning `ProductVendor : Microsoft Corporation` means the listener answers; an error that mentions WinRM and the firewall means remoting is off or port 5985 is blocked (`Test-NetConnection srv01 -CommonTCPPort WINRM`).

**Why it is effective:** one line checks twenty servers, with no desktop session, as objects you can sort.

**Trap:** inside a session your credentials go no further (the "second hop"): a file share or a third server answers access denied. Kerberos needs the server's name; by IP you need HTTPS or a `TrustedHosts` entry. Servers have it on by default since 2012; desktop Windows does not.

**Next step:** access denied → membership in Administrators or Remote Management Users on the target. Port 5985 owned by PID 4 → the `netsh http` card.

### mstsc / qwinsta / rwinsta — connect over RDP, list a server's sessions, reset a hung one
Match: mstsc, qwinsta, rwinsta
Instead of: rebooting the server to free a Remote Desktop session
Safety: read-only for `qwinsta` · `rwinsta` changes state: it ends the session at once, and unsaved work in it is lost

**In one line:** `mstsc` is the Remote Desktop client (TCP 3389); `qwinsta` (= `query session`) lists a server's sessions with ID, user and state; `rwinsta` (= `reset session`) ends one by ID.

**Read the command:** `qwinsta /server:srv01`

| Part | Meaning |
|---|---|
| `/server:srv01` | ask that server instead of this one |
| `rwinsta 2 /server:srv01` | **changes state**: end session 2 |
| `quser /server:srv01` | the same users with idle and logon time |
| `mstsc /v:srv01` | open Remote Desktop to srv01; `/admin` for the administrative session |

**What the output tells you:**

```
 SESSIONNAME       USERNAME                 ID  STATE   TYPE        DEVICE
 services                                    0  Disc
 console                                     1  Conn
 rdp-tcp#4         ops                       2  Active
                   deploy                    3  Disc
 rdp-tcp                                 65536  Listen
```

`Disc` sessions keep their programs running and their memory in use; `Listen` is the listener, not a user.

**Why it is effective:** "the number of connections to this computer is limited" on a server without Remote Desktop Services licensing usually means forgotten disconnected sessions; this names them and frees one without a reboot.

**Trap:** `/server:` talks RPC to the server, not RDP, so a firewall can block it where RDP works. Resetting someone's `Active` session ends their programs mid-work: ask first.

**Next step:** RDP itself fails → `Test-NetConnection srv01 -CommonTCPPort RDP`, then `Get-Service TermService` on the target.

### Get-IISSite / Get-WebBinding — which IIS site answers on which IP, port and host name?
Match: get-iissite, get-webbinding, import-module, appcmd
Instead of: IIS Manager
Safety: read-only · run elevated: the IIS configuration is not readable for ordinary users

**In one line:** IIS keeps its sites in `applicationHost.config`; these list every site with its ID, state and bindings, the IIS view of Apache's virtual hosts.

**Read the command:** `Import-Module WebAdministration; Get-WebBinding | Select-Object protocol, bindingInformation`

| Part | Meaning |
|---|---|
| `Import-Module WebAdministration` | load a module, here the older IIS one (its cmdlets and the `IIS:\` drive) |
| `Get-WebBinding` | one object per binding, across all sites |
| `protocol`, `bindingInformation` | `http` or `https`, and `IP:PORT:HOSTNAME` |
| `Get-IISSite` | the newer IISAdministration module: name, ID, state, path and bindings |
| `appcmd list sites` | the same from cmd, in `%windir%\system32\inetsrv\` |

**What the output tells you:**

```
protocol bindingInformation
-------- ------------------
http     *:80:
https    *:443:crm.example.com
```

`*` = every IP. An empty host name catches every name on that port; a host name works like a name-based virtual host. Site ID N logs to `inetpub\logs\LogFiles\W3SVCN`.

**Why it is effective:** "the wrong site answers" and "404 for one name only" are binding questions, and this is the whole map in one table.

**Trap:** the HTTPS certificate is not in this table: http.sys holds it (`netsh http show sslcert`). Two sites with the same binding cannot both run: the second does not start.

**Next step:** certificate → the `netsh http` card. Requests rejected before IIS → `%SystemRoot%\System32\LogFiles\HTTPERR`.

### Start-Job / Get-Job — PowerShell background jobs: list, stop and clean them up
Match: start-job, get-job, stop-job, remove-job, receive-job
Instead of: a second PowerShell window
Safety: read-only for `Get-Job` and `Receive-Job` · changes state: `Start-Job` runs code in a new process, `Stop-Job` ends it, `Remove-Job` deletes the job and its unread output

**In one line:** `Start-Job { … }` runs a script block in a separate background PowerShell process (≈ `&` in bash); `Get-Job` lists this session's jobs, `Receive-Job` collects their output, `Stop-Job` and `Remove-Job` clean up.

**Read the command:** `Get-Job | Stop-Job; Get-Job | Remove-Job`

| Part | Meaning |
|---|---|
| `Get-Job` | Id, Name, State (`Running`, `Completed`, `Failed`, `Stopped`), HasMoreData |
| `| Stop-Job` | stop every job in the list |
| `| Remove-Job` | delete them; `Remove-Job -Force` also takes running ones |
| `Receive-Job -Id 1 -Keep` | the output so far; `-Keep` leaves it for the next read |

**What the output tells you:**

```
Id  Name  PSJobTypeName  State    HasMoreData  Location   Command
--  ----  -------------  -----    -----------  --------   -------
1   Job1  BackgroundJob  Running  True         localhost  while ($true) {}
```

A `Failed` job keeps its error until you `Receive-Job` it.

**Why it is effective:** jobs belong to the session that started them, so `Get-Job` in that window finds and stops exactly them, with no PID hunting.

**Trap:** in `Get-Process` each job is just another `powershell` (or `pwsh`) process, so a busy job hides behind a generic name. Closing the window ends its jobs, and another window's `Get-Job` sees none of them.

**Next step:** an unknown busy `powershell` process → `Get-CimInstance Win32_Process` for its parent, the window that started it.

### curl.exe — the real curl on Windows: status, TLS and the time of each phase
Match: curl.exe
Instead of: Invoke-WebRequest
Safety: read-only for GET · `-k` turns off certificate checks; `--ssl-no-revoke` turns off only the revocation check

**In one line:** Windows 10 1803 and later ship curl as `C:\Windows\System32\curl.exe`, with the Linux options; type the `.exe`, because in Windows PowerShell 5.1 plain `curl` is an alias for `Invoke-WebRequest`.

**Read the command:** `curl.exe -o NUL -s -w "dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} speed=%{speed_download}\n" https://app.example.com/`

| Part | Meaning |
|---|---|
| `-o NUL`, `-s` | throw the body away (`NUL` is Windows' `/dev/null`); no progress meter |
| `-w "…"` | after the transfer, print these variables |
| `time_namelookup`, `time_connect`, `time_appconnect` | seconds from the start until DNS, TCP and TLS were done |
| `time_starttransfer`, `time_total` | until the first response byte; until the end |
| `speed_download` | average download speed in bytes per second |

**What the output tells you:**

```
dns=0.015243 tcp=0.031907 tls=0.080512 ttfb=0.412348 total=0.415107 speed=45231
```

The times add up from the start: TLS took 0.08 − 0.03 s, and the server needed 0.41 − 0.08 s before its first byte, the slow part here.

**Why it is effective:** one line splits "the site is slow" into DNS, network, TLS and server time, from the user's own machine.

**Compared with `Invoke-WebRequest`:** status and content, no per-phase timing.

**Trap:** this build uses Windows' TLS (Schannel) and certificate store: it trusts what Windows trusts, and behind proxies that block revocation lookups fails with `0x80092012` or `0x80092013`. In a `.bat` file, double every `%`.

**Next step:** slow DNS → `Resolve-DnsName`. Slow TCP → `pathping -n`. Headers, `--resolve` and more → the `curl` card.

### sample / spindump — where is a hung or CPU-busy Mac app stuck?
Match: sample, spindump
Instead of: Force Quit, the spinning wheel
Safety: read-only · `spindump` needs sudo · the reports contain file paths and function names

**In one line:** both record call stacks many times a second for a few seconds and print a tree with sample counts: `sample` for one process (Activity Monitor's "Sample Process"), `spindump` for a hang, the kind of report macOS saves for frozen apps.

**Read the command:** `sample 1234 5`

| Part | Meaning |
|---|---|
| `1234` | the PID (a process name also works) |
| `5` | sample for 5 seconds (default 10) |
| `-file /tmp/app.txt` | write the report there (by default it goes to a file under `/tmp`, whose path it prints) |
| `sudo spindump 1234` | a hang report for that process, saved to a file it names |

**What the output tells you:**

```
Sort by top of stack, same collapsed (when >= 5):
        __psynch_cvwait  (in libsystem_kernel.dylib)        4210
        read  (in libsystem_kernel.dylib)                    388
        parseConfig  (in MyApp)                              210
```

The functions most often on top of the stack: a wait such as `__psynch_cvwait` is a thread blocked on a lock; the app's own functions on top are where it burns CPU.

**Why it is effective:** a frozen window says nothing; the stacks say whether the app spins in its own code or waits on a lock, the disk or the network.

**Trap:** most threads always sit in a wait: read the main thread first. Without symbols you get bare addresses.

**Next step:** waiting on files or sockets → `sudo fs_usage pid 1234`, `lsof -p 1234`. Crashed instead → its `.ips` report (the `open` card).

### nettop — which process on a Mac is using the network, with retransmits and round-trip time
Match: nettop
Instead of: iftop, Activity Monitor's Network tab
Safety: read-only

**In one line:** macOS's `nethogs`: a live table of network traffic per process and, unless collapsed, per connection, with bytes in and out, retransmitted bytes and average round-trip time.

**Read the command:** `nettop -P -m tcp`

| Part | Meaning |
|---|---|
| `-P` | one summary row per process, without its connections |
| `-m tcp` | TCP only (`-m udp` for UDP) |
| `-p 1234` | one process |
| `-L 1` | one sample as CSV, then exit: for a ticket or a script |

**What the output tells you:** rows are named `process.PID`. `bytes_in` and `bytes_out` are totals (press `d` in the live view for the change per interval); `re-tx` is retransmitted data and `rtt_avg` the round-trip time. High `re-tx` and `rtt_avg` point at a lossy path or poor Wi-Fi; a backup or sync client at the top of `bytes_out` explains a full uplink.

**Why it is effective:** "the network is slow" is often one process filling the link; nettop names it, which interface counters cannot.

**Compared with `iftop`:** iftop (from Homebrew) shows traffic per remote host, not per process.

**Trap:** helper processes carry traffic for their app: Safari's shows up under `com.apple.WebKit.Networking`. Totals since start make a long-lived process look busy now: watch the deltas.

**Next step:** one remote host to blame → `route -n get HOST`, `ping`. Wi-Fi quality → `wdutil info`, `networkQuality`. On Linux → `nethogs`.

### open — open a crash report, file, folder or URL from the Mac Terminal
Match: open
Instead of: double-clicking in Finder
Safety: read-only when viewing · it starts the app that handles the file, so opening an app or script runs it

**In one line:** `open` hands a file, folder or URL to the app macOS uses for it, as a double-click would: an `.ips` crash report opens in Console, a folder in Finder, a URL in the browser.

**Read the command:** `open ~/Library/Logs/DiagnosticReports/MyApp-2026-08-09.ips`

| Part | Meaning |
|---|---|
| `~/Library/Logs/DiagnosticReports/` | crash and hang reports of your apps; `/Library/Logs/DiagnosticReports/` has the system daemons' |
| `open -a Console FILE` | with a named app |
| `open -R FILE` | reveal it in Finder |
| `open -t FILE`, `open .` | in the default text editor; this folder in Finder |

**What the output tells you:** a crash report names the exception type (for example `EXC_BAD_ACCESS (SIGSEGV)`), the termination reason, the crashed thread and its stack. Since macOS 12 the `.ips` file is JSON: a one-line header, then the report; Console shows it readable.

**Why it is effective:** `ls -lt` on the folder plus `open` on the newest report answers "did it crash, and where" faster than searching the unified log.

**Trap:** `open` prints nothing in your terminal: over SSH, read the file with `less` instead. Depending on the macOS version, hangs appear as `.ips`, `.hang` or `.spin` files in the same folders.

**Next step:** crash at launch → `log show --last 10m --predicate 'process == "MyApp"'`. Frozen, not crashed → `sample` or `spindump`. Blocked from running → `spctl`.

### vmware-toolbox-cmd — is the VMware host ballooning, swapping or capping this VM?
Match: vmware-toolbox-cmd
Instead of: free inside the guest
Safety: read-only for `stat` and `timesync status` · `timesync enable` and `disable` change state

**In one line:** the VMware Tools command line in a guest (`open-vm-tools` on Linux, `VMwareToolboxCmd.exe` on Windows); `stat` asks the hypervisor what it took back and which limits apply.

**Read the command:** `vmware-toolbox-cmd stat balloon`

| Part | Meaning |
|---|---|
| `stat balloon` | memory the balloon driver holds for the host, in MB |
| `stat swap` | VM memory the host has swapped to its own disk |
| `stat memlimit`, `stat cpulimit` | limits set on the VM in vSphere |
| `timesync status` | whether Tools sets the guest clock from the host |

**What the output tells you:**

```
$ vmware-toolbox-cmd stat balloon
2048 MB
```

The host took 2 GB back: the guest counts it as used, so applications have that much less. `stat swap` above 0 MB is worse: the host pages VM memory to its own disk, invisible to the guest.

**Why it is effective:** ballooning and host swapping slow a VM with no visible cause inside; these numbers are evidence for the virtualisation team.

**Compared with `free`:** it shows the balloon only as used memory.

**Trap:** a limit shown as a huge number means no limit. The values are for now; vCenter's performance charts hold the history.

**Next step:** balloon or swap above 0 → a reservation, or less overcommitment on the host. A CPU limit → ask for its removal (vCenter's CPU Ready shows the waiting). Clock drift → one time source: chrony or Tools time sync, not both.
