# New free practice sites for Linux, shell, networking, DNS, TLS and web servers (checked 7 Nov 2026)

Scope: free (or genuine free tier) sites, games and labs not already in the handbook. All pages were opened with a fetch tool on 7 Nov 2026 unless marked "(snippet only)". "Self-hosted" means the user would run it only in a throwaway VM. Some candidates were already looked at in `research/practice.json` on 3 Oct 2026 and left out. Where that is the case, the earlier reason is quoted so the writer can decide whether to bring them back.

## Q1. Which other free Linux, shell, Windows and networking practice sites exist in 2026?

### Takeaway
There are about 20 strong new candidates. Linuxzoo is the closest to a new break-fix lab: a free remote root VM you work on in the browser, with DNS, Apache, firewall, SELinux and diagnostics tutorials. Julia Evans' Wizard Zines debugging mysteries and quiz sets fill the "networking puzzle" gap. Under The Wire and PSKoans fill the Windows/PowerShell gap. RouterJockey (new in July 2026), the itch.io Subnetting Challenge and the Hurricane Electric IPv6 certification cover subnetting and IPv6. Hackattic and Protohackers give real TLS, DNS and TCP/UDP server tasks for mid-level and senior engineers. Three candidates are dead or broken, including unixgame.io, which now redirects to a gambling domain.

### Cited Findings

#### Linux and shell: browser labs and games
- **Linuxzoo**, https://linuxzoo.net/
  - What it is: a free site that gives you a remote, private Linux machine with root access, controlled from your browser.
  - Getting in: you register, join a queue, switch the machine on, and connect with a browser SSH client or your own terminal.
  - Images: AlmaLinux 10, Caine Forensics 10.0/13.0, Kali 2020-4/2024-4.
  - Tutorials: paths, shell, search, permissions, pipes, vi, administration, networking, SELinux, firewalls, DNS, diagnostics, Apache, logs, email, grep, and forensics (MBR, GPT, FAT, NTFS, file recovery).
  - Status: the page shows "Stable" with the note "Patching and rebooting underway", and a © 2004-2026 Edinburgh Napier University footer (created by Gordon Russell). No paid tier is mentioned. — [Linuxzoo](https://linuxzoo.net/)
- **Webminal**, https://www.webminal.org/
  - What it is: "The free GNU/Linux terminal for everyone", running in the browser, "free since 2011".
  - Content: guided lessons from navigation to shell scripting, screencasts, "Linux Command Golf" challenges, MySQL access, and a forum.
  - Access: the page has Log in / Register links. It says the service will be "always & forever" free and has a sponsor link.
  - Status: no dated news on the page. It claims 35,211,335 commands executed and 500k+ users. — [Webminal](https://www.webminal.org/)
- **WebVM**, https://webvm.io/
  - What it is: "Linux virtualization in WebAssembly", powered by CheerpX, © Leaning Technologies 2022-2025. — [WebVM](https://webvm.io/)
  - Repo: leaningtech/webvm, Apache-2.0, 17,468 stars, last push 2026-11-02, not archived. — [GitHub API](https://api.github.com/repos/leaningtech/webvm)
  - A related game, **Linux Dungeon** (a WebVM Hackathon II entry by Jonathan Fox and Ruby Tipper), runs a full Linux client-side in the browser. You explore directories, decode clues and edit config files to escape rooms. Demo: https://jfoxuk.github.io/webvm/. No release date or price is stated. — [Leaning Technologies showcase](https://labs.leaningtech.com/showcase/linux-dungeon)
- **systemd by example playground**, https://systemd-by-example.com/
  - How it works: click "Start system" and you get a bash shell in a container, where you can edit and add or remove unit files. The backend builds an image from your units and runs it as a podman container.
  - Limits: no network, limited CPU and memory, a cap on parallel processes, and at most 10 minutes per run. A share button saves a setup as a link.
  - The playground post is dated 25 Jan 2022. It mentions no login and no price. — [Seb Jambor, "systemd by example: the playground"](https://seb.jambor.dev/posts/systemd-by-example-the-playground/)
  - The companion article series has 5 parts (Minimization, Dependencies, Defining services, Installing units, Timers). Part 1 is dated 23 Nov 2021. — [Part 1](https://seb.jambor.dev/posts/systemd-by-example-part-1-minimization/)
  - The site title "systemd by example - the systemd playground" loaded on 7 Nov 2026. A system was not started. — [systemd-by-example.com](https://systemd-by-example.com/)
- **bashcrawl** (self-hosted), https://gitlab.com/slackermedia/bashcrawl
  - What it is: "Learn Linux commands by playing a simple text adventure."
  - Repo: GPLv3, 217 commits, 1 release, created 24 Jul 2019. — [GitLab](https://gitlab.com/slackermedia/bashcrawl)
  - Activity: 296 stars, 157 forks, last activity 2026-06-09. — [GitLab API](https://gitlab.com/api/v4/projects/slackermedia%2Fbashcrawl)
  - The README with play instructions was not fetched, so install steps are a gap.
- **learnbyexample TUI-apps** (self-hosted), https://github.com/learnbyexample/TUI-apps
  - Terminal exercise apps: Linux CLI Text Processing Exercises (70+), Grep (50+), Sed (50+), Awk (80+, plus an Awk tutorial), and Python regex playground and exercises. Built with Textual. MIT, 1.0k stars, 105 commits. — [GitHub](https://github.com/learnbyexample/TUI-apps)
  - Last push 2026-02-02, not archived. — [GitHub API](https://api.github.com/repos/learnbyexample/TUI-apps)

#### Windows and PowerShell (module 17)
- **Under The Wire**, https://underthewire.tech/
  - What it is: PowerShell war games. You SSH into a box, and each level's answer is the password for the next user (century1 → century2 ...).
  - Access: a 2021 player blog says the first credentials and help come from the project's Slack server. — [SQLServerCentral blog](https://www.sqlservercentral.com/blogs/powershell-practice-with-a-war-game)
  - Games named in community write-ups: Century, Cyborg (levels 0-15), Groot, Oracle (registry and DNS zone records) and Trebek. One write-up calls Trebek "all the wargames currently available"; that write-up is undated. — [narrowtomato write-ups](https://narrowtomato.github.io/writeups/underthewire/trebek.html); [0xBEN, Cyborg](https://benheater.com/underthewire-cyborg/); [narrowtomato, Oracle](https://narrowtomato.github.io/writeups/underthewire/oracle.html)
  - On 7 Nov 2026 the site answered, but it is a JavaScript app: the fetch tool saw only the title "underthewire-react", so levels and status could not be read from the site. — [underthewire.tech/century](https://underthewire.tech/century)
- **PSKoans** (self-hosted), https://github.com/vexx32/PSKoans
  - What it is: "learn the PowerShell language through Pester unit testing". Each koan is a failing Pester test you make pass; the progress example shows 635 koans.
  - Install: `Install-Module PSKoans -Scope CurrentUser`. Prerequisites are PowerShell 5.1 or 6+; the README contradicts itself on Pester (v4.x in one place, 5.0.2+ in another). GPL-3.0, 973 commits. — [GitHub](https://github.com/vexx32/PSKoans)
  - Activity: 1,883 stars, last push 2026-10-03, 9 open issues, not archived. — [GitHub API](https://api.github.com/repos/vexx32/PSKoans)

#### Networking, subnetting and IPv6 (module 28)
- **RouterJockey training tools**, https://routerjockey.com/training-tools/
  - Four tools: IPv4 Subnet Trainer (prefix slider, colour-coded 32-bit view, and a drill tab with random CIDR problems covering network, mask, broadcast, first and last host, and usable hosts); IPv6 Subnet Trainer (nibble-level, /0 to /128, learn and drill tabs); a Binary Trainer (including AND/OR/XOR/NOT); and a Hex Trainer.
  - All four are free, run entirely in the browser with no backend, and need no account. Article published 2026-07-23, updated 2026-07-26. — [RouterJockey](https://routerjockey.com/training-tools/)
- **Subnetting Challenge (LearnNetworking)**, https://learnnetworking.itch.io/subnetting-challenge
  - An HTML5 browser game in itch.io's "Free" category, with a donate link.
  - Covers IPv4, IPv6, binary, VLSM or a mix, at Easy, Medium or Hard, with timer, history and leaderboard; aimed at CCNA beginners.
  - No publish date is shown. — [itch.io](https://learnnetworking.itch.io/subnetting-challenge)
- **Hurricane Electric IPv6 Certification**, https://ipv6.he.net/certification/
  - Described as a "Free IPv6 certification service"; registration is needed.
  - Tasks: prove IPv6 connectivity, an IPv6 web server, an IPv6 email address, forward and reverse IPv6 DNS, and name servers that answer over IPv6, plus quick concept tests. © 1994-2026. — [HE](https://ipv6.he.net/certification/)
  - It was already logged on 3 Oct 2026 as "Free and live; candidate for a later IPv6 drill". — `research/practice.json` (local catalog)
- **Cisco Modeling Labs Free (CML-Free v2.10)** (self-hosted)
  - Cost: "no-cost, single-user", up to 5 running nodes (unmanaged switches and external connectors don't count), no time limit.
  - Download needs a free Cisco.com account. Install on bare metal or as a VMware OVA.
  - Images: IOL, IOL-L2 and ASAv, plus Ubuntu, Alpine and desktop hosts.
  - Anonymised telemetry is always on and cannot be turned off. — [Cisco DevNet docs](https://developer.cisco.com/docs/modeling-labs/cml-free/)
- **Kathará** (self-hosted), https://www.kathara.org/
  - Open-source, container-based network emulation: devices are containers joined by virtual L2 LANs, with Docker or Kubernetes as the backend.
  - "Get it for Free". It links a "Network Scenarios" lab collection (Kathara-Labs). No version is shown on the page. — [kathara.org](https://www.kathara.org/)
- **Cisco DevNet Sandboxes**, https://developer.cisco.com/site/sandbox/
  - "Free, in your browser, on real Cisco gear."
  - Always-on sandboxes open at once; on-demand ones can be reserved for up to 7 days and extended. — [DevNet](https://developer.cisco.com/site/sandbox/)
- **Juniper vLabs**, https://jlabs.juniper.net/vlabs/
  - "Use pre-built topologies ... all for free!"; sign-up or login is needed to reserve.
  - Topologies include vMX, vSRX, Apstra, JCNR, SRv6 and BGP CT. © 1999-2025. — [Juniper vLabs](https://jlabs.juniper.net/vlabs/)

#### Networking and debugging puzzles, DNS, TLS, HTTP, web servers (modules 28, 29, 42)
- **Wizard Zines debugging mysteries (Julia Evans)**, https://mysteries.wizardzines.com/
  - Five mysteries: The Case of the Slow Websites, ... the Connection Timeout, ... the DNS Update that Didn't Work, ... the 50ms Request, ... the Failed Docker Connection. — [mysteries.wizardzines.com](https://mysteries.wizardzines.com/)
  - How they play: a branching text detective story. You pick actions such as "Try using curl", "Look at the iptables rules" or "Try tcpdump", type free-text answers, and collect clues in a "What you know" sidebar. There is no real terminal.
  - The connection-timeout case runs from a service on port 1234 in AWS, through SYN retries in tcpdump, to security groups and iptables. It runs in the browser with no sign-up or payment seen. — [Connection Timeout](https://mysteries.wizardzines.com/connection-timeout.html)
  - Source: jvns/twine-stories, 135 stars, no licence, last push 2023-02-18 (static and complete, not actively updated). — [GitHub API](https://api.github.com/repos/jvns/twine-stories)
- **Wizard Zines question sets**, https://questions.wizardzines.com/
  - Tricky ~10-minute quizzes on TLS certificates, HTTP request headers, HTTP status codes, CORS, CDNs, UDP, TCP, sockets, IPv4, DNS, DNS records and network layers. Systems sets cover virtual memory, signals, assembly and Unix permissions; Bash sets cover variables and redirects.
  - No account or price is mentioned. — [questions.wizardzines.com](https://questions.wizardzines.com/)
- **The Illustrated TLS 1.3 Connection**, https://tls13.xargs.org/
  - A byte-by-byte walk through a TLS 1.3 session: X25519 key exchange, ClientHello/ServerHello, HKDF key derivation, the encrypted handshake and session tickets.
  - Each step has command-line commands to reproduce it, plus downloadable keys, certificates, C tools and packet captures. Sibling pages cover TLS 1.2, DTLS and QUIC. — [tls13.xargs.org](https://tls13.xargs.org/)
  - Repo syncsynchalt/illustrated-tls13: MIT, 921 stars, last push 2026-01-07. — [GitHub API](https://api.github.com/repos/syncsynchalt/illustrated-tls13)
- **Nginx location match tester**, https://nginx.viraptor.info/
  - Paste an nginx config and a URL to see which `location` block matches.
  - Not supported: sub-locations, listen ports and readable parse errors. Price, maintainer and dates are not stated. — [nginx.viraptor.info](https://nginx.viraptor.info/)
- **htaccess tester (madewithlove)**, https://htaccess.madewithlove.com/
  - Paste Apache `.htaccess` rewrite rules and a URL; it shows "exactly how Apache would rewrite it before you deploy". It has server-variable and advanced test sections.
  - A "Free developer tool" with no account needed (the newsletter box is separate). — [htaccess tester](https://htaccess.madewithlove.com/)
- **MDN HTTP Observatory**, https://developer.mozilla.org/en-US/observatory
  - Checks a site's HTTP headers and security configuration; launched in 2016. — [MDN Observatory](https://developer.mozilla.org/en-US/observatory)
  - Anyone can scan any domain, and scan history is public. Rescans are limited to one every 60 s.
  - The new version (on MDN since 2 Jul 2024) checks headers and the HTTP→HTTPS redirect only. The TLS and certificate tabs were removed; the old Mozilla Observatory, which had TLS and SSH tests, was shut down in Oct 2024. — [Observatory FAQ](https://developer.mozilla.org/en-US/observatory/docs/faq)
- **Hackattic**, https://hackattic.com/
  - "Hard, no-nonsense programming challenges" about real-world work, run by "Jack". Optional sign-up and GitHub login; 17 challenges. — [hackattic.com](https://hackattic.com/)
  - Ops-relevant challenges: Tales of SSL (generate a certificate to a given spec), Serving DNS (set up a DNS server to a specification), Dockerized solutions ("you get to be the registry"), Backup restore (restore a database dump), A global presence (send requests from several locations), WebSocket chit chat, and Hosting git. No price; only a "buy me a coffee" link. — [Hackattic challenges](https://hackattic.com/challenges)
  - How you solve them: GET a problem and POST a solution to API endpoints that take an `access_token`. Tales of SSL asks for a self-signed cert with a given domain, serial and country, sent as base64 DER. — [Tales of SSL](https://hackattic.com/challenges/tales_of_ssl)
- **Protohackers**, https://protohackers.com/
  - Server-programming challenges: "Build real network servers, solve protocol challenges" (TCP, UDP, JSON). — [protohackers.com](https://protohackers.com/)
  - Made by James Stanley. — [About](https://protohackers.com/about)
  - 12 problems: 0 Smoke Test, 1 Prime Time, 2 Means to an End, 3 Budget Chat, 4 Unusual Database Program, 5 Mob in the Middle, 6 Speed Daemon, 7 Line Reversal, 8 Insecure Sockets Layer, 9 Job Centre, 10 Voracious Code Storage, 11 Pest Control.
  - It has a leaderboard and says you can "check your programs anonymously". Price and whether submissions are still open are not stated. — [Problems](https://protohackers.com/problems)
  - The homepage statistics show placeholder values, so current activity could not be confirmed. — [protohackers.com](https://protohackers.com/)

#### Packet analysis and security-adjacent (modules 37 and 42)
- **Root Me (Network category)**, https://www.root-me.org/en/Challenges/Network/ (snippet only)
  - The site is behind Anubis bot protection and returned "Access Denied" to the fetch tool. — [root-me.org](https://www.root-me.org/en/Challenges/Network/)
  - Search snippets say the network challenges are pcap analysis (for example, recovering an FTP password with tshark). The platform is free for personal, non-professional use; "Root-Me PRO" is the paid business product. — [crmulent write-up](https://crmulent.github.io/posts/root-me-network); [Root-Me PRO](https://pro.root-me.org/?lang=en)
- **Chris Sanders, Practical Packet Analysis captures** (self-hosted files), https://github.com/chrissanders/packets
  - Repo "Packet Captures": 420 stars, no licence, last push 2018-01-03 (static). — [GitHub API](https://api.github.com/repos/chrissanders/packets)
  - A 2026 pcap-repository guide describes them as training-style captures. — [Cellstream PCAP repositories (snippet only)](https://www.cellstream.com/2026/09/04/pcap-repositories/)
- **HackerDNA**, https://hackerdna.com/
  - Browser-based ethical-hacking labs ("Kali in your browser"). Topics include Linux enumeration and privilege escalation, and forensics including network traffic.
  - The free plan needs no credit card. Pro paywalls all labs, courses and official solutions, more AI coach use and longer machines. © 2026. — [hackerdna.com](https://hackerdna.com/)
- **SANS Holiday Hack Challenge**
  - Described as "FREE, hands-on cybersecurity challenges". The 2026 game "The Pyramid on the Ice" is not open yet; submissions close 5 Jan 2027. — [SANS](https://www.sans.org/mlp/holiday-hack-challenge/)
  - The 2025 game "Revenge of the Gnome(s)" shows "Play Now". 2021-2024 are marked "Not Available"; the site keeps only the last year playable. — [Past challenges](https://www.holidayhackchallenge.com/past-challenges/)

#### Dead, broken or unverifiable (do not add)
- **The Unix Game (unixgame.io)**: on 7 Nov 2026 it answered with a 301 redirect to `fun88tl.net`, an unrelated gambling domain. Treat it as dead or hijacked and do not link it. — [fetch of unixgame.io](https://unixgame.io/)
- **Netsim (netsim.erinn.io)**: a web network simulator for "teaching hacking to high schoolers". The hosted site refused the connection on 7 Nov 2026. — [netsim.erinn.io](https://netsim.erinn.io/)
  - Repo errorinn/netsim: MIT, 181 stars, last push 2020-08-18. Self-hosting needs PHP and a database. — [GitHub API](https://api.github.com/repos/errorinn/netsim); [search result describing repo](https://github.com/errorinn/netsim)
- **Deadlock OS (CrazyGames)**: a Linux command-line puzzle game (logs, permissions, processes, network restrictions) described as a Sept 2026 alpha (snippet only). The game page returned 404 on 7 Nov 2026. — [CrazyGames URL](https://www.crazygames.com/game/deadlock-os-cvg)
- **WebTerm Learn**: a free browser terminal, Git and Vim lessons site, said to have launched on Product Hunt on 31 Aug 2026 (snippet only). The listing returned 403. — [Peerlist](https://peerlist.io/daiaoki/project/webterm-learn)
- **Cisco Learning Network Binary Game**: the page showed only a "Sorry to interrupt / CSS Error" loader. — [Cisco Learning Network](https://learningnetwork.cisco.com/s/binary-game)
- **LabEx free labs** (such as labex.io/free-labs/wireshark, seen in search): the pricing page returned 403, so free-tier limits could not be checked. — [LabEx pricing](https://labex.io/pricing)

#### Paid, skipped
- Paid only: Pluralsight / A Cloud Guru firewall and pcap labs (subscription), Boson NetSim, Root-Me PRO, HackerDNA Pro. — [search results](https://pluralsight.com/cloud-guru/labs/aws/working-with-ip-sets-and-iptables); [Root-Me PRO](https://pro.root-me.org/?lang=en)
- No public pricing: PacketSafari is a commercial pcap-analysis platform with no visible free tier or exercises, and evaluation goes through registration. — [packetsafari.com](https://packetsafari.com/)

#### Checked on 3 Oct 2026 and left out (still not in the handbook)
- From `research/practice.json` "excluded_after_research":
  - HackerRank Linux Shell: "Live, but CMD Challenge and Exercism cover the same skills better"
  - Linux Survival: "overlaps with Linux Journey and Terminus"
  - RegexOne
  - SubnetIPv4: "Duplicate of Subnetting Practice"
  - internet.nl: free test of your own domain for IPv6, DNSSEC, HTTPS and mail
  - CyberDefenders: freemium
  - Malware-Traffic-Analysis: "Contains real malicious traffic; left out for safety"
- From the same file, "Microsoft Learn sandboxes" is in "dead_or_renamed".

These entries are local catalog facts, not re-fetched today.

### Inferences
- The best new break-fix lab is Linuxzoo. It is the only new find that gives a real root VM with server-side topics (Apache, DNS, firewall, SELinux, diagnostics), at no cost and without touching the user's machine. Registration is the only barrier.
- The Wizard Zines mysteries are the nearest thing to a "networking break-fix game". They practise reasoning (which command next, what the symptom means) rather than typing, so they pair well with SadServers.
- The Windows module (17) currently has no free PowerShell practice. Under The Wire (browser SSH, nothing to install) plus PSKoans (VM) would fill it.
- RouterJockey's IPv6 trainer and the Subnetting Challenge's IPv6 mode cover IPv6 subnetting. Whether the handbook's existing Subnetting Practice entry covers IPv6 was not checked.
- Hackattic (Tales of SSL, Serving DNS, be-the-registry) and Protohackers (Mob in the Middle proxy, Insecure Sockets Layer) are rare free sources of mid-level and senior tasks where you build the service rather than read about it.
- Of the new finds, only Linuxzoo, Wizard Zines mysteries, Under The Wire and systemd-by-example are genuinely "something is broken, find out why". The rest are drills, sandboxes, testers or labs to build in.

### Gaps
- Under The Wire's current level list, Slack requirement and server status could not be read, because the site is a JavaScript app that the fetch tool cannot render. The level details come from undated community write-ups.
- Whether Linuxzoo exercises are auto-checked, and how VM resets or quotas work, is not stated on the homepage.
- I found no free macOS (module 20) troubleshooting practice site; searches returned nothing usable.
- I found no free browser sandbox built for iptables or nftables. The only browser option seen, Shipwreck Ex on hackclub.app, came from a snippet and was not verified.
- Regex Crossword, internet.nl and Linux Survival were not re-fetched today: Regex Crossword's page rendered only its title, and the other two were checked on 3 Oct.

## Q2. For each site: cost, sign-up, card, browser or self-hosted, level, and upkeep

### Takeaway
Most finds are fully free and run in the browser, and about half need no account. The free tiers with limits are HackerDNA (Pro paywalls most labs and solutions) and CML-Free (5 nodes). Linuxzoo, HE IPv6, Juniper vLabs and CML-Free need an account, and no new free find asked for a credit card. Upkeep varies: PSKoans, WebVM, bashcrawl and RouterJockey were updated in 2026. The Wizard Zines mysteries (2023), systemd-by-example (2022) and the Sanders pcaps (2018) are static but still load. "Level" below is my estimate (L0 fresher to L4 senior).

### Cited Findings
| Site | Cost / free tier | Sign-up | Card | Runs where | Upkeep | Source |
|---|---|---|---|---|---|---|
| Linuxzoo | Free, no paid tier mentioned | Yes (register, queue) | None mentioned | Browser SSH to remote root VM | © 2004-2026, status "Stable" | [linuxzoo.net](https://linuxzoo.net/) |
| Webminal | Free "always & forever" | Register/Login links | None mentioned | Browser terminal | Running since 2011, no dated news | [webminal.org](https://www.webminal.org/) |
| WebVM / Linux Dungeon | Open source (Apache-2.0); no price shown | None mentioned | None mentioned | Fully in browser (WebAssembly) | Push 2026-11-02 | [GitHub API](https://api.github.com/repos/leaningtech/webvm); [showcase](https://labs.leaningtech.com/showcase/linux-dungeon) |
| systemd by example | No price or login mentioned | None mentioned | None mentioned | Browser UI; podman container on their server, 10 min, no network | Posts 2021-2022; site loads | [playground post](https://seb.jambor.dev/posts/systemd-by-example-the-playground/) |
| bashcrawl | GPLv3 | No | No | Self-hosted (VM) | Last activity 2026-06-09 | [GitLab API](https://gitlab.com/api/v4/projects/slackermedia%2Fbashcrawl) |
| learnbyexample TUI-apps | MIT | No | No | Self-hosted Python/Textual (VM) | Push 2026-02-02 | [GitHub API](https://api.github.com/repos/learnbyexample/TUI-apps) |
| Under The Wire | Free (blog) | Credentials via Slack (2021 blog) | None seen | SSH to their Windows hosts | Site answers; content unreadable | [blog](https://www.sqlservercentral.com/blogs/powershell-practice-with-a-war-game) |
| PSKoans | GPL-3.0 | No | No | Self-hosted PowerShell module (VM) | Push 2026-10-03 | [GitHub API](https://api.github.com/repos/vexx32/PSKoans) |
| RouterJockey trainers | Free | No accounts | No | Browser, no backend | Published 2026-07-23 | [routerjockey.com](https://routerjockey.com/training-tools/) |
| Subnetting Challenge | Free category, donate link | Not mentioned | No | Browser (HTML5) | Date not shown | [itch.io](https://learnnetworking.itch.io/subnetting-challenge) |
| HE IPv6 Certification | Free | Yes | None mentioned | Browser tests against your own IPv6 host and domain | © 1994-2026 | [HE](https://ipv6.he.net/certification/) |
| CML-Free 2.10 | Free, 5 running nodes | Cisco.com account to download | None mentioned | Self-hosted (bare metal or VMware OVA); telemetry always on | v2.10 docs | [Cisco](https://developer.cisco.com/docs/modeling-labs/cml-free/) |
| Kathará | Open source, free | No | No | Self-hosted on Docker or Kubernetes (VM) | Page shows no version | [kathara.org](https://www.kathara.org/) |
| Cisco DevNet Sandboxes | Free | Not stated on page | None mentioned | Browser / reserved labs up to 7 days | Live | [DevNet](https://developer.cisco.com/site/sandbox/) |
| Juniper vLabs | Free | Yes | None mentioned | Reserved remote topologies | © 1999-2025 | [vLabs](https://jlabs.juniper.net/vlabs/) |
| Wizard Zines mysteries | No price seen | No | No | Browser | Repo push 2023-02-18 (static) | [GitHub API](https://api.github.com/repos/jvns/twine-stories) |
| Wizard Zines questions | No price seen | No | No | Browser | No dates | [questions.wizardzines.com](https://questions.wizardzines.com/) |
| Illustrated TLS 1.3 (+1.2, DTLS, QUIC) | MIT | No | No | Browser (plus optional local reproduction) | Push 2026-01-07 | [GitHub API](https://api.github.com/repos/syncsynchalt/illustrated-tls13) |
| Nginx location tester | Not stated | No | No | Browser | No dates | [nginx.viraptor.info](https://nginx.viraptor.info/) |
| htaccess tester | "Free developer tool" | No | No | Browser | No dates | [madewithlove](https://htaccess.madewithlove.com/) |
| MDN HTTP Observatory | No price; anyone can scan | No | No | Browser; one rescan per 60 s | On MDN since 2 Jul 2024 | [FAQ](https://developer.mozilla.org/en-US/observatory/docs/faq) |
| Hackattic | No price; donations | Optional on site; API `access_token` needed to solve | No | You run code and servers yourself (VM) | 17 challenges, no dates | [hackattic.com](https://hackattic.com/); [Tales of SSL](https://hackattic.com/challenges/tales_of_ssl) |
| Protohackers | No price stated | Optional; "check your programs anonymously" | No | You run a TCP/UDP server, their checker tests it | Status unclear (placeholder stats) | [problems](https://protohackers.com/problems) |
| Root Me (Network) | Free for personal use; PRO paid | Account (not confirmed for pcaps) | None seen | Browser downloads of pcaps | Bot wall; snippet only | [write-up](https://crmulent.github.io/posts/root-me-network) |
| Sanders pcaps | Free repo, no licence | No | No | Files (open in a VM's Wireshark) | Push 2018-01-03 | [GitHub API](https://api.github.com/repos/chrissanders/packets) |
| HackerDNA | Free tier; Pro paywalls all labs, solutions, longer machines | Yes | "No credit card" for free | Browser | © 2026 | [hackerdna.com](https://hackerdna.com/) |
| SANS Holiday Hack | Free | Not stated | No | Browser game (2025 edition "Play Now") | 2026 edition pending, closes 5 Jan 2027 | [SANS](https://www.sans.org/mlp/holiday-hack-challenge/); [past](https://www.holidayhackchallenge.com/past-challenges/) |

### Inferences
Estimated levels (my judgment from the content described above):
- L0-L1: Webminal, WebVM / Linux Dungeon, bashcrawl, Wizard Zines questions, RouterJockey, Subnetting Challenge.
- L1-L2: Linuxzoo (L0 to L2 by tutorial), TUI-apps (grep, sed, awk), Under The Wire, PSKoans, Wizard Zines mysteries, the nginx and htaccess testers, HTTP Observatory, Sanders pcaps, Root Me Network.
- L2-L3: systemd by example, Illustrated TLS 1.3, HE IPv6 (needs your own domain and an IPv6 host), CML-Free, Kathará, DevNet, Juniper vLabs, Hackattic.
- L3-L4: Protohackers (protocol design, a proxy in "Mob in the Middle", a reliable protocol over UDP in "Line Reversal").

Safety notes for the "throwaway VM only" rule:
- Hackattic, Protohackers and HE IPv6 all need the user to run a server they control.
- For Protohackers and HE IPv6 it probably has to be reachable from the internet. This is inferred from the task descriptions (an outside checker or test must reach your server), not stated on the pages fetched. A short-lived cloud VM fits better than a home machine.
- CML-Free needs a hypervisor host (bare metal or VMware), so it is heavier than a normal throwaway VM.

### Gaps
- Release and last-update dates are missing for the Subnetting Challenge, the nginx location tester, the htaccess tester, the Wizard Zines questions and Hackattic. Hackattic links changelog RSS feeds that were not fetched.
- Whether Protohackers still accepts submissions in Nov 2026 is not confirmed.
- CML-Free hardware requirements are on a separate page that was not fetched.
- Root Me registration rules for the pcap challenges are not confirmed, because the bot wall blocked the fetch.

## Q3. Which handbook module does each fit?

### Takeaway
New material concentrates in modules 27 (shell and Linux sandboxes, text-processing drills), 28 (subnetting/IPv6 trainers and network labs) and 42 (debugging mysteries, TLS byte-walk, pcaps). Module 29 gains nginx and Apache rule testers and the HTTP Observatory, and module 17 gets its first free PowerShell practice. Module 41 gains Linuxzoo and systemd by example. Module 20 (macOS) gains nothing.

### Cited Findings
- Linuxzoo tutorials span shell basics, administration, SELinux, firewalls, DNS, diagnostics, Apache, logs and email. — [Linuxzoo](https://linuxzoo.net/)
- The Wizard Zines mysteries cover slow websites, connection timeouts, a DNS update that didn't work, a 50 ms request and a failed Docker connection. — [mysteries.wizardzines.com](https://mysteries.wizardzines.com/)
- The Wizard Zines quizzes span networking (TLS certificates, HTTP headers and status codes, CORS, CDNs, TCP, UDP, DNS) and systems (Unix permissions, signals, virtual memory, bash redirects). — [questions.wizardzines.com](https://questions.wizardzines.com/)
- The Under The Wire Oracle game covers the registry and DNS zone records. — [Oracle write-up](https://narrowtomato.github.io/writeups/underthewire/oracle.html)
- Hackattic covers TLS cert generation, DNS serving, container registry and database restore. — [Hackattic challenges](https://hackattic.com/challenges)

### Inferences
| Module | New candidates (best first) |
|---|---|
| 27 Learn Linux | Linuxzoo, Webminal, WebVM (+ Linux Dungeon), bashcrawl, learnbyexample TUI-apps (grep/sed/awk), Wizard Zines questions (permissions, signals, bash), systemd by example |
| 28 Learn networking | RouterJockey IPv4/IPv6/binary trainers, Subnetting Challenge, HE IPv6 Certification, Wizard Zines questions (TCP, UDP, IPv4, layers), CML-Free, Kathará, Cisco DevNet Sandboxes, Juniper vLabs, Protohackers |
| 29 Web servers & proxies | Nginx location match tester, htaccess tester (fits the user's Apache background), MDN HTTP Observatory, Hackattic (Tales of SSL, WebSocket), Linuxzoo Apache tutorial |
| 41 Linux system problems | Linuxzoo (diagnostics, logs, SELinux, forensics of MBR/GPT/file recovery), systemd by example (dependency and target experiments) |
| 42 Network/DNS/TLS/VPN problems | Wizard Zines mysteries (timeouts, DNS propagation, latency, Docker networking), Illustrated TLS 1.3/1.2/QUIC, HE IPv6 (AAAA, PTR, IPv6 NS), Hackattic Serving DNS / Tales of SSL, Sanders pcaps, Root Me Network pcaps |
| 17 Windows | Under The Wire (PowerShell over SSH), PSKoans |
| 20 macOS | none found |
| 37 Security/DevSecOps | MDN HTTP Observatory, HackerDNA (free tier), Root Me, SANS Holiday Hack Challenge |

- Suggested shortlist for a first handbook update, picked for break-fix value, being free and needing no install: Linuxzoo (27/41), Wizard Zines mysteries (42), Under The Wire (17), RouterJockey (28), htaccess tester and nginx location tester (29), Illustrated TLS 1.3 (42), systemd by example (41), Hackattic (29/42, L2-L3).

### Gaps
- None of the module fits were checked against each module's current text beyond the covered-sites list in the brief. There may be overlaps the writer should check, for example whether module 28 already links Cisco DevNet or CML.
- No free practice site for macOS (module 20) troubleshooting was found.
