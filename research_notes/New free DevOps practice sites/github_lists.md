# GitHub awesome-lists and community catalogs of free DevOps / sysadmin / cloud practice sites (status as of 7 Nov 2026)

Method: repo metadata (stars, last push) read from the GitHub REST API on 7 Nov 2026; README files read raw from GitHub; candidate sites opened directly with a web fetch. Nothing was signed up for, logged in to, downloaded, cloned or run. "Last push" = the API's `pushed_at` field, which is close to (but not always the same as) the last commit on the default branch. Where only a search snippet or a page title could be seen, this is said explicitly. Reddit / Stack Overflow / Server Fault were not used.

## Which GitHub lists are the best, still-maintained catalogs for this (and which are stale)?

### Takeaway
No single GitHub list covers "free hands-on DevOps practice" well. The most useful sources are niche lists: **zardus/wargame-nexus** (wargames, with liveness badges), **iknowjason/Awesome-CloudSec-Labs** (cloud/K8s/CI-CD security labs, each tagged hosted or self-hosted), **veggiemonk/awesome-docker** "Where to Start", the **ramitsurana/awesome-kubernetes** "interactive environments" page, and **joe-shenouda/awesome-cyber-skills**. The giant general lists (free-for-dev, awesome-sysadmin, awesome-devops, awesome-sre) are maintained but list almost no practice sites. awesome-ctf and devsecops/awesome-devsecops are stale.

### Cited Findings

**Best lists for mining practice sites (ranked by usefulness to the handbook)**

1. **zardus/wargame-nexus**: "A sorted and updated list of security wargame sites"; 1,360 stars; last push 2026-10-25; not archived — [GitHub API](https://api.github.com/repos/zardus/wargame-nexus)
   - Sorted by category (Beginner, General, Box-style, Binary, Web, Crypto, Forensics, **Cloud**, **Blue Team / DFIR**, **"Not Security"**, "Gone, but not forgotten", Other Indexes). It marks entries with badges such as recommended, beginner, offline, "heartbeat failed", dead and "no scoreboard" — [README](https://github.com/zardus/wargame-nexus)
   - Its "Not Security" section lists sysadmin-relevant sites: CMD Challenge, SadServers, **UnderTheWire** (PowerShell, beginner), **Protohackers** (network servers), Advent of Code, Exercism, Codewars and others — [README](https://github.com/zardus/wargame-nexus)
   - Usefulness: the best-maintained liveness tracker of the lists checked. It covers security more than DevOps.
2. **iknowjason/Awesome-CloudSec-Labs**: "Awesome free cloud native security learning labs. Includes CTF, self-hosted workshops, guided vulnerability labs, and research labs."; 2,210 stars; last push 2025-10-01 (about 13 months ago) — [GitHub API](https://api.github.com/repos/iknowjason/Awesome-CloudSec-Labs)
   - Sections: AWS, Azure, GCP, Kubernetes, Container, Terraform, Research Labs, CI/CD, PaaS. Each entry says whether it is author-hosted or self-hosted. It includes Wiz's Cloud Security Championship, Cloud Hunting Games, Pwned Labs, K8s LAN Party, Broken Azure, Bustakube, Kube Security Lab, CI/CD Goat, GitHub Actions Goat, TerraGoat, IAM Vulnerable, Thunder CTF, EntraGoat and OWASP EKS Goat — [README](https://github.com/iknowjason/Awesome-CloudSec-Labs)
   - Note: the README's Wiz links for K8s LAN Party and EKS Cluster Games are malformed ("https:www.wiz.io") — [README](https://github.com/iknowjason/Awesome-CloudSec-Labs)
   - Usefulness: the best catalog for cloud/IaC/CI-CD security labs. It is slowing down (no push in over a year).
3. **veggiemonk/awesome-docker**: 37,190 stars; last push 2026-11-04 — [GitHub API](https://api.github.com/repos/veggiemonk/awesome-docker)
   - Its "Learning Resources > Where to Start" section lists Docker katas (eficode-academy), **Docker Terminal Simulator (devops-daily.com)**, **Dockerlings**, Play With Docker and prepare.sh's Docker course (marked paid). A "Privileged Containers" exercise on ransomleak.com sits under Security Articles — [README](https://github.com/veggiemonk/awesome-docker)
4. **ramitsurana/awesome-kubernetes**: 16,139 stars; last push 2026-10-31 — [GitHub API](https://api.github.com/repos/ramitsurana/awesome-kubernetes)
   - The page `docs/learning-resources/interactive-environments.md` lists LabEx K8s labs, Kubernetes Bootcamp, Play with Kubernetes, sharelearn.net K8s labs, **Meshery Playground**, YouBrokeProd, **SudoRank** and **DevOpsLesson Kubernetes Playground** — [interactive-environments.md](https://github.com/ramitsurana/awesome-kubernetes/blob/master/docs/learning-resources/interactive-environments.md)
5. **joe-shenouda/awesome-cyber-skills**: "A curated list of hacking environments where you can train your cyber skills legally and safely"; 4,781 stars; last push 2026-09-17 — [GitHub API](https://api.github.com/repos/joe-shenouda/awesome-cyber-skills)
   - It has 120 entries in a single table with a category column (Web, Crypto, RE, CTF/Wargame, Blue Team, Cloud, Mobile, System/Network, Tutorials, Games). Many entries are old SourceForge or VulnHub VMs. Useful entries include PortSwigger Web Security Academy, Root Me, **SEED Labs**, techlogia Lab ("Browser-based Linux and OWASP lab"), CyberTalents, GOAD and Metasploitable 3 — [README](https://github.com/joe-shenouda/awesome-cyber-skills)
6. **magnologan/awesome-k8s-security**: 2,008 stars; last push 2026-11-06 — [GitHub API](https://api.github.com/repos/magnologan/awesome-k8s-security)
   - Its "Trainings" and "Repositories/Tools > Learning" sections list securekubernetes.com, Kubernetes Goat, Bust-a-Kube, kube-goat, **Kube Security Lab (raesene)**, k8s-net-labs (KubeCon EU 2020), killer.sh CKS and KodeKloud Game of Pods. Several training links are dead brands, such as Katacoda, Linux Academy and A Cloud Guru course URLs — [README](https://github.com/magnologan/awesome-k8s-security)
7. **michelpereira/awesome-games-of-coding**: 2,169 stars; last push 2026-09-23 — [GitHub API](https://api.github.com/repos/michelpereira/awesome-games-of-coding)
   - Its DevOps-relevant entries are all already in the handbook: clmystery, SQL Murder Mystery, Learn Git Branching, Oh My Git, YouBrokeProd and Microcorruption (security) — [README](https://github.com/michelpereira/awesome-games-of-coding)
8. **networktocode/awesome-network-automation**: 2,882 stars; last push 2026-11-04 — [GitHub API](https://api.github.com/repos/networktocode/awesome-network-automation)
   - It has "Training", "Network Emulators" and "Network Simulators" sections: Model-Driven Network Configuration Tutorial (containerlab + NETCONF/gNMI on SR Linux/cEOS), CML, Containerlab, EVE-NG, FakeNOS, GNS3, Mininet, **netlab (ipspace)**, VRNetLab and **Batfish**. It lists no hosted sandboxes such as DevNet Sandbox or Juniper vLabs — [README](https://github.com/networktocode/awesome-network-automation)

**Large general lists: maintained, but few practice sites**

- **ripienaar/free-for-dev**: "SaaS, PaaS and IaaS offerings that have free tiers of interest to devops and infradev"; 142,131 stars; last push 2026-11-06 — [GitHub API](https://api.github.com/repos/ripienaar/free-for-dev)
  - Practice-relevant entries: Killercoda; Google Cloud Shell ("Web-based Linux shell... 5GB of persistent storage. 60-hour limit per week"); cocalc.com ("Browser access to full Ubuntu"); GetVM ("Instant free Linux and IDEs chrome sidebar. The free tier includes 5 VMs per day") — [README](https://github.com/ripienaar/free-for-dev)
  - An "Education and Career Development" section exists (FreeCodeCamp, The Odin Project, Full Stack Open, Ladderly). I saw it only through mirror commit snippets, not in the live README — [mirror commit snippet](https://git.hackliberty.org/Git-Mirrors/free-for-dev/commit/24ee99f30627b932952de215d245c0ee616758cf)
  - Usefulness: good for free cloud shells and free-tier infrastructure, poor for practice platforms.
- **awesome-foss/awesome-sysadmin**: 35,622 stars; last push 2026-10-22 — [GitHub API](https://api.github.com/repos/awesome-foss/awesome-sysadmin). It lists open-source software, not learning sites (not mined further).
- **wmariuss/awesome-devops**: 4,448 stars; last push 2026-11-07 — [GitHub API](https://api.github.com/repos/wmariuss/awesome-devops). Its only hands-on entry is "Cloud Native Playground" (play.meshery.io) under Resources > Online Platforms, plus roadmap links (roadmap.sh, devopsroadmap.io) — [README](https://github.com/wmariuss/awesome-devops)
- **dastergon/awesome-sre**: 13,757 stars; last push 2025-08-28 (stale for over a year) — [GitHub API](https://api.github.com/repos/dastergon/awesome-sre). Its Education section has Wheel of Misfortune (already in the handbook), the Google SRE Classroom distributed PubSub workshop and NALSD flashcards. An On-Call entry links an incident-command training handbook — [README](https://github.com/dastergon/awesome-sre)

**Stale lists**

- **apsdehal/awesome-ctf**: 11,974 stars; last push 2024-07-22 (stale for over 2 years) — [GitHub API](https://api.github.com/repos/apsdehal/awesome-ctf). wargame-nexus is the maintained replacement for its wargames section.
- **devsecops/awesome-devsecops**: 5,512 stars; last push 2024-05-11. **jakob-pennington/awesome-devsecops**: 1,756 stars; last push 2024-08-02 — [GitHub search API](https://api.github.com/search/repositories?q=devsecops+awesome+in:name&sort=stars&per_page=5)
- Cloud-security lists: **4ndersonLin/awesome-cloud-security** has 2,517 stars and a last push of 2026-03-17 (slowing). **teamssix/awesome-cloud-security** (Chinese) last pushed 2024-10-28. **Metarget/awesome-cloud-native-security** last pushed 2023-11-04 — [GitHub search API](https://api.github.com/search/repositories?q=awesome+cloud+security+in:name&sort=stars&per_page=6)

**Non-GitHub community catalogs checked**

- iximiuz, "Learn-by-Doing Platforms for Dev, DevOps, and SRE Folks": published 3 Oct 2021, updated 22 Jan 2022, so it is stale (it still lists Katacoda and KubeAcademy as live) — [iximiuz.com](https://iximiuz.com/en/posts/learn-by-doing-platforms/)
- DevOpsCube, "8 Best Websites To Practice DevOps Scenarios": dated 15 Feb 2026. It lists KodeKloud, iximiuz Labs, Killercoda, Pluralsight, Educative, **Prepare.sh**, AWS Skill Builder and SadServers, with free-tier limits. Examples: Killercoda free is about 1 h per session, one at a time; iximiuz free is about 1 h per day; SadServers free is "30+ of 80 scenarios" — [devopscube.com](https://devopscube.com/websites-to-practice-devops/)

### Inferences
- For a recurring "what's new" sweep, the highest-value lists to re-check are wargame-nexus (it tracks dead sites with heartbeat badges), the awesome-docker "Where to Start" section, the awesome-kubernetes interactive-environments page, and Awesome-CloudSec-Labs. They are short, focused, and recently added DevOps-specific browser tools (devops-daily, SudoRank, DevOpsLesson, Dockerlings).
- free-for-dev, awesome-sysadmin, awesome-devops and awesome-sre are not worth mining for practice platforms. They are tool or free-tier catalogs.
- No well-maintained "awesome terminal games", "awesome-linux-learning" or "awesome-hacking-games" list surfaced (see Gaps). wargame-nexus plus awesome-games-of-coding cover that space.

### Gaps
- I did not find a maintained GitHub list named awesome-cli-games, awesome-ttygames or awesome-linux-learning. Search turned up only small personal repos (Seniru/cli-games, kaamkiya/gg) and spam results — [web search snippet](https://awesome.ecosyste.ms/projects/github.com%2FSeniru%2Fcli-games); [GitHub search API](https://api.github.com/search/repositories?q=awesome+linux+learning+in:name,description&sort=stars&per_page=6)
- I did not check EbookFoundation/free-programming-books, the techiescamp repos, milanm/DevOps-Roadmap or LabEx's "devops-practice-projects" lists. The LabEx lists are vendor marketing for labex.io, which the handbook already covers — [ecosyste.ms snippet](https://awesome.ecosyste.ms/lists/labex-labs%2Fdevops-practice-projects)
- I could not read free-for-dev's "Education and Career Development" section in the live README. The fetch read characters 0–100k and 175k–275k, and the section was in neither part.

## What practice sites appear in them that the handbook lacks, and which of those are genuinely free and still alive in 2026?

### Takeaway
About 15 list-sourced sites are new to the handbook and alive in Nov 2026. The best DevOps fits are devops-daily.com/games (62 free browser simulators, including a daily "On-Call" incident puzzle), tmpfs.tech, SudoRank, Meshery Playground, DevOpsLesson, prepare.sh, Protohackers, UnderTheWire and the DevOps-Daily CI-graded challenges. Security and cloud additions include PortSwigger Web Security Academy, Root-Me, Pwned Labs, Wiz's Cloud Security Championship and Cloud Hunting Games, and self-hosted SEED Labs, Kube Security Lab, CI/CD Goat, Dockerlings and Docker katas. **Status alert for the handbook:** three Wiz challenge domains, including two the handbook lists (eksclustergames.com and bigiamchallenge.com), did not resolve in DNS on 7 Nov 2026.

### Cited Findings

**Handbook-covered sites whose status changed (check before editing the handbook)**
- **eksclustergames.com** (in the handbook): my fetch failed with `getaddrinfo ENOTFOUND` — [eksclustergames.com](https://eksclustergames.com/). Google DNS returns NOERROR with no A record for either the apex or `www`, only a Route 53 SOA — [dns.google apex](https://dns.google/resolve?name=eksclustergames.com&type=A); [dns.google www](https://dns.google/resolve?name=www.eksclustergames.com&type=A)
- **bigiamchallenge.com** (in the handbook): the fetch failed with ENOTFOUND — [bigiamchallenge.com](https://bigiamchallenge.com/). `www.bigiamchallenge.com` returns NXDOMAIN (status 3), with a Route 53 SOA only — [dns.google](https://dns.google/resolve?name=www.bigiamchallenge.com&type=A)
- **k8slanparty.com** (not in the handbook; listed by Awesome-CloudSec-Labs): the fetch failed with ENOTFOUND for both www and apex, and there is no A record — [dns.google](https://dns.google/resolve?name=k8slanparty.com&type=A)
- Conflict: Wiz's own CTF hub (© 2026) still shows "Start challenge" buttons for K8s LAN Party, EKS Cluster Games and the Big IAM Challenge, pointing at those same domains — [wiz.io/ctf](https://www.wiz.io/ctf); [Wiz K8s course "Test Yourself"](https://www.wiz.io/courses/kubernetes-security/test-yourself). A web search found no announcement of retirement or a move — [search result: wiz.io/ctf](https://wiz.io/ctf)
- Wiz's newer challenges on their own domains **do** load: cloudsecuritychampionship.com and cloudhuntinggames.com (details below).

**New, alive, free (or genuine free tier): opened directly**
- **DevOps Daily games**, https://devops-daily.com/games: 62 tools plus 2 "coming soon". Examples: On-Call: The Daily Incident, Incident Commander Simulator, Terraform State Puzzle (8 puzzles), Terraform Basics Simulator, Kubernetes Terminal Simulator, K8s RBAC Simulator, Kubernetes Networking/CNI Simulator, PromQL Playground, Log Aggregation Pipeline Simulator, DNS / TCP-vs-UDP / TLS handshake / AWS VPC simulators, Docker Terminal Simulator, PostgreSQL and SQL terminal simulators, Git Merge Conflict Simulator and Learn Linux (6 lessons). No login wall was visible. The site has a separate "Pro" section that the page does not explain — [devops-daily.com/games](https://devops-daily.com/games)
- **The-DevOps-Daily/challenges**, https://github.com/The-DevOps-Daily/challenges: 6 challenges, each graded by GitHub Actions on a PR to the upstream repo (PRs are closed, never merged). Topics: Docker image shrink, a Bash access-log summary, a Kubernetes deployment fix, Prometheus alerts, slow PostgreSQL queries, and a Terraform network module. Needs a GitHub account; PRs are public. Repo has 5 stars, last push 2026-11-04, MIT — [README](https://raw.githubusercontent.com/The-DevOps-Daily/challenges/main/README.md); [GitHub API](https://api.github.com/orgs/The-DevOps-Daily/repos?per_page=100&sort=updated)
- **DevOpsLesson Kubernetes Playground**, https://devopslesson.com/playground/kubernetes: free and simulated, with 18 auto-checked kubectl steps (about 30 min). No sign-up, no card. Also links a Docker Playground and a CKA Practice Lab — [devopslesson.com](https://devopslesson.com/playground/kubernetes)
- **Meshery Playground**, https://play.meshery.io: live Kubernetes clusters plus CNCF projects. Free ("perpetually free, full access"), but a named account is required. Clusters reset daily — [docs.meshery.io](https://docs.meshery.io/installation/playground)
- **tmpfs.tech**, https://tmpfs.tech/: "a real box, not a quiz", with "disposable Linux labs". You can "Play as guest"; Google or GitHub sign-in is optional. No prices shown — [tmpfs.tech](https://tmpfs.tech/). A Show-DEV post claims "720 hands-on Linux challenges on real ephemeral VMs in your browser" (search snippet only) — [dev.to](https://dev.to/binrick/show-dev-tmpfstech-720-hands-on-linux-challenges-on-real-ephemeral-vms-in-your-browser-23kf)
- **prepare.sh**, https://prepare.sh/: "real Linux, Kubernetes and database machines that boot in your browser". Topics include Docker, Kubernetes, Argo CD, PostgreSQL, Kafka, Airflow and Spark — [prepare.sh](https://prepare.sh/)
  - Free-tier conflict: the page says "Free, and no sign-up required", yet its "Get started free" button links to sign-in — [prepare.sh](https://prepare.sh/). DevOpsCube says "most labs are free", premium starts at $30/mo, 576+ labs — [devopscube.com](https://devopscube.com/websites-to-practice-devops/). awesome-docker marks its Docker course as paid — [awesome-docker](https://github.com/veggiemonk/awesome-docker)
- **Protohackers**, https://protohackers.com/: you implement network servers to a protocol spec and their checker connects to your public endpoint. 12 problems (0 Smoke Test through 11 Pest Control); no new-problem or end notice. You "are free to check your programs anonymously" but then get no leaderboard or saved progress — [protohackers.com/problems](https://protohackers.com/problems); [protohackers.com](https://protohackers.com/)
- **PortSwigger Web Security Academy**, https://portswigger.net/web-security: "100% free". 31 topics, including Request smuggling, Web cache poisoning, HTTP Host header attacks, SSRF, CORS, OAuth, JWT, WebSockets, Race conditions, Web cache deception and Web LLM attacks. An account tracks progress. Burp Suite Community (free) is enough; Pro is not required — [portswigger.net](https://portswigger.net/web-security)
- **Pwned Labs**, https://pwnedlabs.io/: cloud and AI offensive-security labs covering AWS, Azure, GCP, Kubernetes, CI/CD and hybrid. The Academy has a free tier; free labs are at /explore. Registration is required. "Labs run in live environments that Pwned Labs provides" (browser; no own cloud account needed). Prices are not shown on the landing page — [pwnedlabs.io](https://pwnedlabs.io/)
- **Wiz Cloud Security Championship ("Cloud Champions")**, https://www.cloudsecuritychampionship.com/: 12 monthly CTFs, from June 2025 (Perimeter Leak) to May 2026 (Glass House). They include Oct 2025 "Game of Pods" (Hard) and July 2025 "Contain Me If You Can". Only Aug 2025 is marked inactive. It has Login/Register and a leaderboard; the price is not stated (no fee shown) — [cloudsecuritychampionship.com](https://www.cloudsecuritychampionship.com/)
- **Wiz Cloud Hunting Games**, https://www.cloudhuntinggames.com/: an incident-response CTF (the fictional "ExfilCola" ransomware/extortion story), "Made by Wiz Research". The page loads with a "Start Investigation" button; stages, cost and sign-up are not stated on the landing page — [cloudhuntinggames.com](https://www.cloudhuntinggames.com/). Wiz's hub describes it as incident-response practice — [wiz.io/ctf](https://www.wiz.io/ctf)
- **SEED Labs**, https://seedsecuritylabs.org/: Prof. Wenliang Du's labs, started in 2002 and used by "1180 institutes"; 40+ labs, open source on GitHub — [seedsecuritylabs.org](https://seedsecuritylabs.org/). The networking set (Labs_20.04) has 13 entries: Packet Sniffing/Spoofing, ARP Cache Poisoning, ICMP Redirect, TCP Attacks, Mitnick, DNS (Local, Remote, Rebinding, Infrastructure, DNSSEC), Firewall Exploration, Firewall Evasion, VPN Tunneling, VPN, BGP Exploration and Attack, Morris Worm and Heartbleed — [Networking labs](https://seedsecuritylabs.org/Labs_20.04/Networking/)

**New and alive, but seen only partly (title, snippet or bot wall)**
- **SudoRank**, https://sudorank.com: the page title is "Hands-on Linux, Kubernetes & DevOps Challenges"; the content did not render (JS app) — [sudorank.com](https://sudorank.com/). An aggregator says it runs broken systems on real Linux VMs and multi-node K8s clusters. Its free tier is "8 tracks with 281 challenges"; Pro is $8/mo (652 challenges) and Pro+ $15/mo (all 750) (snippet only, aggregator source) — [Slashdot comparison](https://slashdot.org/software/comparison/SudoRank-vs-kpt/). Listed by awesome-kubernetes — [interactive-environments.md](https://github.com/ramitsurana/awesome-kubernetes/blob/master/docs/learning-resources/interactive-environments.md)
- **UnderTheWire**, https://underthewire.tech/: the site serves (page title "underthewire-react"), but the JS content did not render — [underthewire.tech](https://underthewire.tech/). wargame-nexus lists it as beginner, no scoreboard — [wargame-nexus](https://github.com/zardus/wargame-nexus). Community write-ups (snippets) describe PowerShell wargames (Century, Cyborg, and more) played over SSH, with starting credentials from the project's Slack #StartHere channel. Later Cyborg levels involve Active Directory queries — [benheater.com](https://benheater.com/underthewire-cyborg/); [sqlservercentral.com](https://www.sqlservercentral.com/blogs/powershell-practice-with-a-war-game)
- **Root-Me**, https://www.root-me.org/: my fetch hit an Anubis bot-protection "Access Denied" page, so the site is up but its content was unread — [root-me.org](https://www.root-me.org/en/Challenges/). Per search snippets, it is free for personal non-professional use. It has a Network category (captured traffic, network services, packet analysis); a 2026 guide counts 608 challenges and 178 virtual environments, and challenge machines only accept IPs logged in to root-me.org (third-party, snippet only) — [hackerdna.com 2026 guide](https://hackerdna.com/blog/root-me)
- **Hacker101**, https://www.hacker101.com/: a free web-security class and videos, plus a CTF at ctf.hacker101.com. CTF status and cost were not checked — [hacker101.com](https://www.hacker101.com/)

**New self-hosted labs (throwaway-VM candidates), with repo activity**
- **Dockerlings** (furkan/dockerlings): "learn docker in your terminal, with bite sized exercises"; 1,038 stars; last push 2026-10-30; MIT — [GitHub API](https://api.github.com/repos/furkan/dockerlings)
- **Docker katas** (eficode-academy/docker-katas): "Exercises for Docker training"; 292 stars; last push 2026-09-11; MIT — [GitHub API](https://api.github.com/repos/eficode-academy/docker-katas)
- **Kube Security Lab** (raesene/kube_security_lab): builds 14 vulnerable clusters with Docker, Ansible and kind, with walkthroughs — [Awesome-CloudSec-Labs](https://github.com/iknowjason/Awesome-CloudSec-Labs). 288 stars, last push 2026-03-19, no license listed — [GitHub API](https://api.github.com/repos/raesene/kube_security_lab)
- **CI/CD Goat** (cider-security-research/cicd-goat): "A deliberately vulnerable CI/CD environment"; locally hosted Docker CTF — [Awesome-CloudSec-Labs](https://github.com/iknowjason/Awesome-CloudSec-Labs). 2,334 stars, **last push 2024-07-14 (stale)**, Apache-2.0 — [GitHub API](https://api.github.com/repos/cider-security-research/cicd-goat)

**Checked and rejected**
- **CyberDefenders**: the pricing page shows no free plan. Certs from $600; CyberRange practice is $25/month — [cyberdefenders.org/pricing](https://cyberdefenders.org/pricing/)
- **RansomLeak "Privileged Containers"**: an "Interactive 3D Simulation" (~45 min). Cost and sign-up are not stated; it appears scripted, not a real shell — [ransomleak.com](https://ransomleak.com/exercises/privileged-containers/)
- wargame-nexus marks VulnHub, Exploit Education (Nebula/Fusion/Phoenix/Main Sequence) and Hackropole as offline, and lists Defend the Web, Lords of SQLi and XSS PwnFunction under "Gone, but not forgotten" — [wargame-nexus](https://github.com/zardus/wargame-nexus)

### Inferences
- The Wiz DNS result most likely means the three older Wiz CTFs (EKS Cluster Games, Big IAM Challenge, K8s LAN Party) were taken offline, or are mid-migration, after the handbook's 3 Oct 2026 check. The zones still exist in Route 53 and the Wiz hub still links them, so it could be temporary. Re-check from a second network before marking them retired in 54-practice-arena.md's "retired" table (the table that already lists Katacoda).
- devops-daily.com/games is the single biggest DevOps-specific gap. It hits nearly every handbook topic (incident response, K8s, Terraform state, PromQL, DNS/TLS, Postgres) with no sign-up. The tools are simulations, though, so they belong at L0–L2 next to YouBrokeProd and sys-admin-simulator, not next to SadServers or Killercoda.
- For "real broken box" practice, the new competitors to SadServers and iximiuz are tmpfs.tech (guest play) and SudoRank (free tier per aggregator). Both need direct confirmation of their limits before the handbook cites numbers.

### Gaps
- I could not render SudoRank, UnderTheWire or Root-Me content (JS apps or a bot wall). Their free-tier details rest on aggregator or third-party snippets.
- The free-lab count and paid prices for Pwned Labs are not on its landing page; I did not open /explore or /pricing.
- I did not open Cloud Hunting Games' /challenge, so whether it needs registration is unknown.
- I did not verify ctf.hacker101.com, techlogia.de/en/lab, sharelearn.net K8s labs, GetVM, Broken Azure (brokenazure.cloud) or OWASP EKS Goat. The last needs your own EKS, which costs money.
- Whether the Wiz domains' DNS outage is permanent cannot be confirmed from one day's check; there is no official notice.

## For each verified site: exact URL, what you practise, free-tier limits, sign-up, credit card, browser vs self-hosted, level, handbook topic

### Takeaway
Of the ~19 sites checked, 9 are browser-based and free with no card (devops-daily, DevOpsLesson, tmpfs.tech, Protohackers checking, PortSwigger, Meshery, Pwned Labs free tier, Wiz Championship, Root-Me). 2 have a paid-leaning or unclear free tier (prepare.sh, SudoRank). 5 are self-hosted and suit the user's throwaway VM (SEED Labs, Dockerlings, Docker katas, Kube Security Lab, CI/CD Goat). Protohackers needs a publicly reachable server, so it is a throwaway cloud-VM job.

### Cited Findings
(Facts per site are cited in the section above; repeated here in compact form with the key source.)

| Site (exact URL) | What you practise | Free / limits | Sign-up? / card? | Browser vs self-hosted | Source |
|---|---|---|---|---|---|
| https://devops-daily.com/games | 62 simulators: daily incident, IC sim, Terraform state puzzle, kubectl / RBAC / CNI, PromQL, DNS / TCP / TLS / VPC, Docker, Postgres, Git | Free; a separate "Pro" section exists, unexplained | No sign-up seen (On-Call stores its streak in the browser); no card mentioned | Browser (simulated) | [games](https://devops-daily.com/games); [on-call](https://devops-daily.com/games/on-call) |
| https://github.com/The-DevOps-Daily/challenges | 6 CI-graded fixes: Docker, Bash, K8s, Prometheus alerts, Postgres, Terraform | Free | GitHub account; PRs public | Fork + PR; graded on GitHub Actions; local testing optional | [README](https://raw.githubusercontent.com/The-DevOps-Daily/challenges/main/README.md) |
| https://devopslesson.com/playground/kubernetes | 18 guided kubectl steps; also Docker playground, CKA practice | Free | No sign-up, no card | Browser (simulated) | [devopslesson](https://devopslesson.com/playground/kubernetes) |
| https://play.meshery.io | Live K8s clusters + CNCF projects (traffic splitting, circuit breaking) | Free; clusters reset daily | Account required | Browser (live clusters) | [Meshery docs](https://docs.meshery.io/installation/playground) |
| https://tmpfs.tech/ | Linux / open-source challenges on disposable boxes | No prices shown | Guest play; optional Google / GitHub | Browser (real disposable labs per site) | [tmpfs.tech](https://tmpfs.tech/) |
| https://sudorank.com | Broken Linux VMs + multi-node K8s troubleshooting | Free: 8 tracks / 281 challenges; Pro $8/mo; Pro+ $15/mo (aggregator only) | Unverified | Browser to real VMs (per aggregator) | [Slashdot](https://slashdot.org/software/comparison/SudoRank-vs-kpt/) (snippet) |
| https://prepare.sh/ | DevOps / SRE interview-style labs (Docker, K8s, Argo CD, Postgres, Kafka) | "Most labs free", premium from $30/mo per DevOpsCube; its own page conflicts | Unclear (sign-in link vs "no sign-up required") | Browser (machines "boot in your browser") | [prepare.sh](https://prepare.sh/); [devopscube](https://devopscube.com/websites-to-practice-devops/) |
| https://protohackers.com/ | Write TCP/UDP servers to protocol specs (12 problems) | Free; anonymous checks allowed | Optional (for leaderboard and progress) | You host a public server; their checker connects | [problems](https://protohackers.com/problems) |
| https://underthewire.tech/ | PowerShell / Windows / AD wargames (Century, Cyborg, ...) | Free (no scoreboard per nexus) | Credentials via the project's Slack | SSH to their hosts | [wargame-nexus](https://github.com/zardus/wargame-nexus); [benheater](https://benheater.com/underthewire-cyborg/) (snippet) |
| https://www.root-me.org/ | Network pcap / protocol challenges, App-Script, realist; 600+ challenges | Free for personal use | Account; VMs accept only logged-in IPs | Browser + their hosted challenge machines (connection method not verified) | [hackerdna 2026](https://hackerdna.com/blog/root-me) (snippet) |
| https://portswigger.net/web-security | HTTP request smuggling, cache poisoning, Host header, SSRF, CORS, OAuth, JWT, ... (31 topics) | "100% free" | Account for progress; no card | Browser labs + free Burp Community | [portswigger](https://portswigger.net/web-security) |
| https://pwnedlabs.io/ (free labs at /explore) | AWS / Azure / GCP / K8s / CI-CD offensive cloud labs | Free tier; paid tiers (prices not shown) | Registration | Browser; labs in Pwned Labs' own cloud | [pwnedlabs](https://pwnedlabs.io/) |
| https://www.cloudsecuritychampionship.com/ | 12 monthly cloud / K8s CTFs (Jun 2025 – May 2026) | No fee shown | Login / Register | Browser | [championship](https://www.cloudsecuritychampionship.com/) |
| https://www.cloudhuntinggames.com/ | Cloud incident-response CTF | No fee shown | Not stated on landing page | Browser | [cloudhuntinggames](https://www.cloudhuntinggames.com/) |
| https://seedsecuritylabs.org/ | ARP / ICMP / TCP attacks, DNS + DNSSEC, firewall, VPN, BGP, Heartbleed | Open source | None | Self-hosted (VM; setup page not read) | [Networking labs](https://seedsecuritylabs.org/Labs_20.04/Networking/) |
| https://github.com/furkan/dockerlings | Docker basics as TUI exercises | Free, MIT | None | Self-hosted | [API](https://api.github.com/repos/furkan/dockerlings) |
| https://github.com/eficode-academy/docker-katas | Docker from hello-world to deploying a web app | Free, MIT | None | Self-hosted | [API](https://api.github.com/repos/eficode-academy/docker-katas); [awesome-docker](https://github.com/veggiemonk/awesome-docker) |
| https://github.com/raesene/kube_security_lab | 14 vulnerable K8s clusters (kind + Ansible) with walkthroughs | Free (no license listed) | None | Self-hosted | [API](https://api.github.com/repos/raesene/kube_security_lab) |
| https://github.com/cider-security-research/cicd-goat | CI/CD pipeline security CTF (Docker-hosted) | Free, Apache-2.0; last push 2024-07 | None | Self-hosted | [API](https://api.github.com/repos/cider-security-research/cicd-goat) |

### Inferences
Level (L0 fresher .. L4 senior) and handbook topic are my own ratings, based on the content described above:

| Site | Level | Likely handbook chapter(s) |
|---|---|---|
| devops-daily.com/games | L0–L2 (On-Call / Incident Commander L1–L2) | 54 practice arena; 33 CI/CD-IaC-SRE (incident, Terraform state); 31 Kubernetes; 32 observability (PromQL); 28 networking (DNS / TCP / TLS) |
| DevOps-Daily/challenges | L1–L2 | 30 Docker, 31 K8s, 32 observability, 33 IaC, 38 databases |
| DevOpsLesson K8s playground | L0–L1 | 31 Kubernetes |
| Meshery Playground | L1–L2 | 31 Kubernetes (service mesh) |
| tmpfs.tech | L0–L2 | 27 Linux, 41 Linux problems |
| SudoRank | L1–L3 | 27 Linux, 46 K8s problems (SadServers-style) |
| prepare.sh | L1–L3 | 52 day-to-day / interview (40 career ladder) |
| Protohackers | L2–L3 | 28 networking (sockets, protocols); needs a throwaway cloud VM with a public port |
| UnderTheWire | L1–L2 | 17 Windows (PowerShell, AD) |
| Root-Me (Network, App-Script) | L1–L3 | 28 networking (pcap), 37 security |
| PortSwigger Academy | L1–L3 | 29 web servers / proxies (request smuggling, cache poisoning, Host header), 37 security |
| Pwned Labs | L1–L3 | 36 cloud / AWS, 37 security |
| Wiz Cloud Security Championship | L2–L4 | 36 cloud, 37 security, 31 K8s ("Game of Pods") |
| Wiz Cloud Hunting Games | L2–L3 | 36 cloud, 48 security tools (IR) |
| SEED Labs (networking) | L2–L3 | 28 networking, 37 security; throwaway VM |
| Dockerlings / Docker katas | L0–L1 | 30 Docker; throwaway VM |
| Kube Security Lab | L2–L3 | 46 K8s problems, 37 security; throwaway VM |
| CI/CD Goat | L2–L3 | 47 CI/CD, 37 security; throwaway VM; stale repo |

- Self-hosted items (SEED, Dockerlings, katas, Kube Security Lab, CI/CD Goat) fit the user's "throwaway VM only, never own machine" rule. Protohackers additionally needs inbound internet access to the VM.
- Wiz Championship and Pwned Labs give the handbook replacements if EKS Cluster Games and Big IAM Challenge prove permanently gone.

### Gaps
- None of the "Free" labels was checked behind a login, so per-session time limits are unknown for Meshery, tmpfs.tech, Pwned Labs and Root-Me.
- SudoRank's prices and free-tier counts come from one aggregator page; prepare.sh's own page contradicts itself about sign-up.
- I did not open SEED Labs' "Lab Setup" page, so the exact VM or Docker setup (and the Ubuntu version) is unconfirmed.
