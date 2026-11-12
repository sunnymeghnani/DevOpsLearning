# Command Decoder intro

A troubleshooting command is only useful if you know **what question it answers** and **what it cannot see**. `ping 8.8.8.8` answers "do packets get there and back?" and even prints an end-to-end loss figure, but it cannot tell you *where* packets are lost. `mtr` probes every hop, so the same three per cent loss becomes "loss starts at hop 2, my ISP's edge router". Each card below explains its command in that way:

| Part of a card | What it gives you |
|---|---|
| **In one line** | the question the command answers |
| **Read the command** | a real invocation from this handbook, flag by flag |
| **What the output tells you** | the fields that matter and how to read them |
| **Why it is effective** | what it shows that the obvious alternative hides |
| **Compared with …** | the command people reach for first, what that one does show, and when it is enough |
| **Trap** | how the output can mislead you |
| **Next step** | where the answer sends you next |

**How to read any command line:** `sudo ss -tlnp 'sport = :443' | grep -v 127.0.0.1`

| Piece | Role |
|---|---|
| `sudo` | run as root: needed here to see *which process* owns each socket |
| `ss` | the program (here: socket statistics) |
| `-tlnp` | short flags bundled: `-t` TCP, `-l` listening, `-n` numeric (no DNS lookups), `-p` show the process |
| `'sport = :443'` | an argument: the filter "source port 443", quoted so the shell passes it as one word |
| `| grep -v 127.0.0.1` | a pipe: the next program filters the output (drop lines bound to loopback only) |

**Safety labels:** *read-only* commands only look. *Changes state* commands restart, delete, block or rewrite something: read the trap before running them on a real server, and prefer the lab from the Practice Arena. Nothing on this page was run on your machine; outputs are illustrative and use documentation addresses (192.0.2.x, 198.51.100.x, 203.0.113.x, example.com).

**Commands people reach for first, and what to use instead:**

| If you would reach for | Prefer | Because |
|---|---|---|
| `ping 8.8.8.8` | `mtr -rwbzc 100 8.8.8.8` | ping gives one end-to-end loss figure; mtr shows the hop where loss starts |
| `ping host` for "is the service up?" | `nc -zv host 443`, `curl -v https://host` | ICMP is often blocked; the service lives on a TCP port and needs an HTTP answer |
| `netstat -tulpn` | `ss -tulpn` | same answer, faster, with filters (`'sport = :443'`), and installed by default |
| `ifconfig` | `ip -br addr`, `ip route get IP` | shows every address and *which route and source IP* a packet will use |
| `nslookup name` | `dig +short name`, `dig @server name`, `resolvectl query name` | dig shows TTLs and status codes and can ask one server at a time |
| `curl https://site` | `curl -sv -o /dev/null https://site` | `-v` shows DNS, TCP connect, the TLS handshake and the response headers |
| `top` | `pidstat 1`, `vmstat 1`, `iostat -xz 1` | separates CPU, I/O wait and memory pressure instead of one busy screen |
| `df -h` | `df -h` **and** `df -i`, `du -xh --max-depth=1` | a disk can be full of inodes, and df alone does not say *what* is using space |
| `free -h` "free" column | `free -h` "available" column, `vmstat 1` si/so | Linux uses idle RAM as cache; "available" and swap activity show real pressure |
| `cat /var/log/syslog` | `journalctl -u app -b -p warning --since "10 min ago"` | filter by unit, boot, priority and time instead of scrolling |
| `docker ps` | `docker ps -a`, `docker inspect`, `docker logs --since 10m` | stopped containers, exit codes and recent logs are where crashes hide |
| `kubectl get pods` | `kubectl describe pod`, `kubectl get events --sort-by=.lastTimestamp` | events show *why* (failed probes, pull errors, OOMKilled) |
| `systemctl status app` | `systemctl status app` **then** `journalctl -u app -b` | status shows only the last few log lines |
