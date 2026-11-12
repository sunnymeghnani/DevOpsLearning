# KodeKloud study map for the troubleshooting handbook

Checked on 3 October 2026. Every KodeKloud course URL below returned HTTP 200 with the expected page title. Most course pages were also fetched and their curriculum read. Every YouTube link was checked for title, channel and length.

This map tells you, for each handbook topic, which KodeKloud course to take first and which sections in which order, which free video to watch, which handbook note to read, and which drill to run. It follows the levels in `ops-ladder.txt` (L0 Foundations, L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE) and fills the gaps KodeKloud leaves.

## Verification legend

| Tag | Meaning |
|---|---|
| **[V1]** | Course page fetched on 3 Oct 2026. Title, level, length, labs and curriculum come from that page. |
| **[V2]** | URL fetched and its real page title confirmed (HTTP 200, not a soft 404). Content not read in full. |
| **[V3]** | YouTube video or playlist. Title, channel and length confirmed from YouTube on 3 Oct 2026. |
| **[NV]** | Not verified. The reason is given next to it. |

Lesson notes on `notes.kodekloud.com` are tagged [V2]. They are KodeKloud's free text versions of individual lessons, and every one listed here returned its real lesson title. Some courses appear under two URL slugs on that site, for example `CKA-Certification-Course-Certified-Kubernetes-Administrator` and `Certified-Kubernetes-Administrator-CKA`. Both work, so links use whichever slug resolved.

---

## How to use KodeKloud with this handbook

Every topic follows the same loop. Each step has a reason, and each one tells you what comes next.

1. **Read the handbook note first (10 min).** Open the matching module, for example `22-playbook-ports-inventory.md`. *Why:* you see the real problem and its commands before the theory, so the lesson has something to attach to. *Next:* write down the 2–3 commands or ideas you don't understand yet.
2. **Do the KodeKloud lesson, video plus its lab (30–60 min).** Only do the sections this map names, in the order given. *Why:* KodeKloud labs grade you in a real terminal, so you learn by typing, not by watching. *Next:* if a lab beats you, read the free lesson note on `notes.kodekloud.com` and retry the lab once before you look at the solution.
3. **Review with KodeKloud Notes (5 min).** Search `notes.kodekloud.com` for the lesson title. *Why:* the notes are the lesson in text form, so you can grep them later and paste commands from them. *Next:* copy any new command into your own runbook with one line saying when to use it.
4. **Break it on purpose (20–30 min).** Use a KodeKloud playground (Ubuntu 24.04, Docker, Kubernetes) or your homelab, and recreate a failure from the handbook's case library or `21-case-apache-443-dokploy.md`. *Why:* course labs teach you how to build things, but your job is fixing them. *Next:* fix it using only the handbook playbook, `23`–`26`.
5. **Run the handbook drill under a timer.** Use the exit test for your ops-ladder level. *Why:* it proves the skill transferred out of the course. *Next:* tick the drill, write the five-line incident note (symptom, first wrong guess, deciding evidence, fix, what to check first next time), and move on to the next topic.

**Weekly rhythm (fits the ops-ladder plan):**
- *Workday morning (30 min):* one KodeKloud Engineer / 100 Days of DevOps task (the free plan allows one task a day) **or** one SadServers scenario. Alternate between them.
- *Two evenings (60 min each):* steps 1–3 for the current topic.
- *Weekend homelab block:* steps 4–5, then a CKA break-and-fix session using KodeKloud CKA labs, Lightning Labs or the mock exams.
- **Until you pass CKA, the CKA course comes first.** Everything else runs on the morning rep.

**Subscription note.** KodeKloud's Free Courses page ([V2] https://kodekloud.com/free-courses) currently lists these as free: *Docker Training Course for the Absolute Beginner*, *Crash Course: Linux / Docker / Kubernetes / AWS Basics*, *Linux Challenges*, *Kubernetes Challenges*, *Terraform Challenges*, *CKS – Challenges*, *Lab – Terraform for Beginners*, *Udemy Labs: DevOps Pre-Requisite Course* and *DevOps Interview Questions and Answers: Scenario-Based Prep*. The other courses need a subscription. Free enrollment shows the course outline.

---

## The shortest KodeKloud route for your real incident (Apache on 443, Dokploy needs 80/443/3000)

Do these **lessons** first, before any full course. Each one matches a step you had to search for during the incident.

| Incident step | KodeKloud lesson (free notes link) | Course | Handbook |
|---|---|---|---|
| Which app is on which port? | *Start, Stop, and Check Status of Network Services*: `ss -ltunp` [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Start-Stop-and-Check-Status-of-Network-Services/page | LFCS | `22-playbook-ports-inventory.md`, `02-network.md` |
| Which process, which files? | *Diagnose and Manage Processes*: ps, top, lsof, signals [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Diagnose-and-Manage-Processes/page | LFCS | `05-processes.md` |
| Where are its logs? | *Locate and Analyze System Log Files* [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page | LFCS | `06-logs-journal.md` |
| What is a service, and how do I stop or disable it? | *SYSTEMD Tools* [V2] https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/SYSTEMD-Tools/page | Linux Basics | `07-services-systemd.md` |
| How Apache vhosts and logs are laid out | *Apache Web Server* (vhosts, logs) [V2] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page and *IPs and Ports* [V2] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/IPs-and-Ports/page | DevOps Pre-Requisite | `29-learn-webservers-proxies.md` |
| One proxy in front of many apps | *Implement Reverse Proxies and Load Balancers* [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Implement-Reverse-Proxies-and-Load-Balancers/page | LFCS | `29-learn-webservers-proxies.md` |
| The firewall around it | *Configure Packet Filtering (Firewall)* (UFW) [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall | LFCS | `10-users-permissions-security.md` |
| Docker ports and networks | *Publishing Ports* [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page and *Docker Networking* [V2] https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page | DCA / Docker Beginner | `30-learn-docker.md`, `14-docker-containers.md` |
| What Traefik is (the proxy Dokploy runs) | *Traefik Overview* [V2] https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page | Kubernetes Networking Deep Dive | `21-case-apache-443-dokploy.md` |

Then replay the whole case on a KodeKloud Ubuntu playground ([V2] https://kodekloud.com/playgrounds/playground-ubuntu; free, Ubuntu 24.04, one hour, extendable). Install Apache with two vhosts on 443, then follow `21-case-apache-443-dokploy.md` to free 443 for a Traefik container.

---

## 1. DevOps prerequisites (start here, L0)

**Handbook:** `README.md`, `19-cheatsheet.md`, `27-learn-linux.md`, `28-learn-networking.md`

**KodeKloud:** *DevOps Pre-Requisite Course* [V1] https://kodekloud.com/courses/devops-pre-requisite-course. Beginner, 6.5 h of video, labs after almost every lesson.
- Order for you: **Networking Basics** (Networking Basics, Labs – Switching and Routing, DNS, Labs – DNS) → **Web Server** (Web Servers Introduction, **Apache Web Server**, Labs – Apache Web Server, **IPs and Ports**, Labs – IPs and Ports) → **Security** (**SSL & TLS Basics**, Labs) → **General Pre-Requisites** (YAML, JSON & JSON Path) → **2 Tier Applications** (set up the e-commerce app all-in-one, then distributed).
- Skim Linux Basics, Lab Setup (VirtualBox/Vagrant) and Applications Basics if you already know them.
- The free lab-only version is listed as *Udemy Labs: DevOps Pre-Requisite Course* on the Free Courses page [V2].

**Why:** the Web Server and SSL/TLS sections are the shortest KodeKloud explanation of the Apache vhost, port and certificate layout from your incident. The 2-tier labs make you debug app-to-DB connectivity, which is the same "which layer is broken" habit.
**Next:** Linux (section 2) or the LFCS lessons in the table above.

---

## 2. Linux basics and administration (L0 → L1, LFCS)

**Handbook:** `27-learn-linux.md`, `01-storage-disk.md`, `04-memory.md`, `05-processes.md`, `06-logs-journal.md`, `07-services-systemd.md`, `10-users-permissions-security.md`, `11-packages.md`, `12-time-ntp.md`, `13-kernel-system.md`, `22-playbook-ports-inventory.md`

**KodeKloud order:**
1. *Learning Linux Basics Course & Labs* [V1] https://kodekloud.com/courses/the-linux-basics-course. Beginner, 5.25 h, labs after every lecture.
   - Sections: Working with Shell I → Linux Core Concepts (kernel, boot, file types, FHS) → Package Management (DPKG and APT) → Working with Shell II (IO redirection, searching) → **Networking (DNS, Networking Basics, Troubleshooting)** → **Security and File Permissions (accounts, permissions, SSH, IPTABLES, cron)** → **Service Management with SYSTEMD (Creating a SYSTEMD Service, SYSTEMD Tools)** → Storage in Linux (partitions, filesystems, NFS, LVM) → The Client Demonstration (troubleshoot the dev environment).
   - Free notes for the key lessons: Networking/DNS [V2] https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/DNS · Networking/Troubleshooting [V2] https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting · Creating a SYSTEMD Service [V2] https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Service-management-with-SYSTEMD/Creating-a-SYSTEMD-Service/page · IPTABLES Introduction [V2] https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Security-and-File-Permissions/IPTABLES-Introduction/page
   - The free 21-minute taster is *Crash Course: Linux For Absolute Beginners* [V1] https://kodekloud.com/courses/crash-course-linux-for-absolute-beginners. Skip it if you already use Linux daily.
2. *Prep Course - Linux Foundation Certified System Administrator (LFCS)* [V1] https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs. Associate, about 11.3 h, labs for every topic, 2 mock exams.
   - Sections in the order that matters for your job:
     - **Operations Deployment**: Manage Startup Process and Services, Create systemd Services, Diagnose and Manage Processes, Locate and Analyze System Log Files, Verify Integrity and Availability of Resources and Processes, Change Kernel Runtime Parameters.
     - **Networking**: Configure IPv4/IPv6 Networking and Hostname Resolution, Start/Stop/Check Status of Network Services, Configure Packet Filtering (Firewall), Port Redirection and NAT, Implement Reverse Proxies and Load Balancers, Set and Synchronize System Time, Configure SSH Servers and Clients.
     - **Storage**: Monitor Storage Performance, LVM, mount options, swap.
     - **Essential Commands**: Work With SSL Certificates, Git basics, grep/regex.
     - **Users and Groups**, then the Mock Exams.
   - `https://kodekloud.com/courses/linux-system-administration` [V1] serves the same LFCS prep curriculum. Treat it as the same course, not an extra one.
3. *Linux Challenges* (free) [V1 page, free per Free Courses page] https://kodekloud.com/courses/linux-challenges. Five timed scenario challenges covering disks, users, permissions, services (HTTP, DB, proxy), packet filtering. Use it as your L1 exit check.
4. Optional: KodeKloud's own Linux learning path ([V2] https://kodekloud.com/learning-path/linux) also lists LPIC-1 and RHCSA. Skip both. You run Ubuntu, and LFCS covers Ubuntu tooling (UFW, netplan-era networking).

**Free practice:** Ubuntu playground [V2] https://kodekloud.com/playgrounds/playground-ubuntu. Free Linux labs category [V2] https://kodekloud.com/studio/labs/linux: search results describe about 20 free labs, including "Linux Troubleshooting", "Linux systemd Services", "Linux Networking" and "Linux IPTables" (each about 1.5 h). **[NV]** individual lab titles: the page renders in JavaScript and the fetch returned only the shell, so the lab names come from search snippets.

**Videos:**
- KodeKloud: *Linux Crash Course for Beginners | Free Linux Lab Access | KodeKloud* [V3] https://www.youtube.com/watch?v=a3ujwK65dgs (141 min, 2023).
- Sanjeev Thiyagarajan, a KodeKloud instructor, on his own channel: *Linux for Beginners: systemd start/stop services & journalctl* [V3] https://www.youtube.com/watch?v=jZfNVROoF74 (18 min).

**Why:** LFCS Networking and Operations Deployment are the exact skills behind "given a port, name the process, unit, config and log command" (ops-ladder L1 exit test).
**Next:** run the L1 exit test from ops-ladder, then `22-playbook-ports-inventory.md` drills.

---

## 3. Shell and bash scripting (L0)

**Handbook:** `27-learn-linux.md` (scripting part), `19-cheatsheet.md`

**KodeKloud order:**
1. *Shell Scripts for Beginners* [V1] https://kodekloud.com/courses/shell-scripts-for-beginners. Beginner, 2 h, a lab after every lesson. Sections: Shell Script Introduction (variables, arguments, arithmetic) → Flow Control (if, for, while, case) → Shebang (**Exit Codes**, Functions, **Tips & Tricks – ShellCheck & IDE**) → Project – E-Commerce Application.
2. *Advanced Bash Scripting* [V1] https://kodekloud.com/courses/advanced-bash-scripting. Intermediate, about 8.4 h, 15 labs. Modules: Conventions → Refresher → **Streams** → Expansions I → Globs → Expansions II → **Special Shell Variables** → Arrays → **Good Practices Applied** → **awk** → **sed**. For log triage, do Streams, Good Practices, awk and sed first.

**Video:** KodeKloud *Shell Scripting Tutorial for Beginners | Shell Scripts Crash Course* [V3] https://www.youtube.com/watch?v=XVOsvIp9m2k (48 min, 2025).

**Why:** the ops-ladder L0 drill (a health-report script with zero ShellCheck warnings) needs exit codes, functions and quoting. Advanced Bash's awk and sed are what you use to slice Apache and Traefik access logs.
**Next:** write the `22-playbook-ports-inventory.md` inventory as a script (ports → PID → unit → config → log path).

---

## 4. Git (L0)

**Handbook:** `33-learn-cicd-iac-sre.md`

**KodeKloud:** *GIT for Beginners* [V1] https://kodekloud.com/courses/git-for-beginners. Beginner, 1.25 h, lab after each lesson. Order: GIT Introduction → Git Branches → Initialize Remote Repositories (push, clone, PRs, fetch/pull, merge conflicts) → Rebasing (interactive rebase, cherry-pick) → **Resetting and Reverting** (reset, revert, stash, **reflog**).
- Free practice: Git Playground and Visualization [V2] https://kodekloud.com/playgrounds/playground-git.

**Video:** KodeKloud *What is Git? | GIT Basics for DevOps Beginners* [V3] https://www.youtube.com/watch?v=Lr7sYCrhxE0 (17 min).

**Why:** the L0 exit test includes "revert a bad Git commit", and the Resetting and Reverting section plus reflog is exactly that. **Next:** GitLab CI (section 18).

---

## 5. Networking fundamentals, DNS, TLS, HTTP (L2)

**Handbook:** `28-learn-networking.md`, `02-network.md`, `08-dns.md`, `18-web-http-tls.md`, `24-playbook-network-speed.md`, `25-playbook-site-down.md`

**KodeKloud order:**
1. *Networks and Communications* [V1] https://kodekloud.com/courses/networks-and-communications. Beginner, about 1 h. Network types, the Internet, hardware, protocols (TCP/IP/HTTP), **Network Troubleshooting**. Take it only if routing or switching feels shaky.
2. DevOps Pre-Requisite: **Networking Basics** and **DNS** lessons (section 1). Notes: [V2] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/Networking-Basics/page and [V2] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Networking-Basics/DNS/page
3. *Demystifying DNS* [V1] https://kodekloud.com/courses/demystifying-dns. About 3.65 h, 5 labs. Order: Welcome to the World of DNS → **DNS as a System (Resolvers, Walking the DNS Tree, TTL)** → DNS as a Protocol (requests and responses, EDNS, DoH/DoT/DNSSEC) → Record Types → **Miscellaneous: DNS Monitoring Tools, Troubleshooting DNS** → Final Project (set up a DNS server).
   - Notes: Troubleshooting DNS [V2] https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page · TTL [V2] https://notes.kodekloud.com/docs/Demystifying-DNS/DNS-as-a-System/Time-to-Live-TTL/page
4. TLS: DevOps Pre-Requisite *SSL & TLS Basics* [V2 notes] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page → LFCS *Work With SSL Certificates* (openssl CSR, self-signed, x509 inspection) [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates → CKA *TLS Basics* (Security section) [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics
5. Firewalls: LFCS *Configure Packet Filtering (Firewall)* (UFW) and *Port Redirection and NAT* [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page → CKS *UFW Firewall Basics* [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page

**Gaps (KodeKloud has nothing on these):** tcpdump, `getent` vs `dig`, systemd-resolved debug logging, netplan specifics, `curl --resolve`, nftables in depth. Use the ops-ladder "Blind spots" resources for these: wizardzines tcpdump, Julia Evans on getaddrinfo, Arch Wiki systemd-resolved, everything curl, Practical Networking, Mess With DNS, badssl.com.

**Videos:**
- KodeKloud *DNS in Linux for the Absolute Beginners!* [V3] https://www.youtube.com/watch?v=9nCIjLlLVzY (14 min).
- ByteByteGo *SSL, TLS, HTTPS Explained* [V3] https://www.youtube.com/watch?v=j9QmMEWmcfo (5 min).

**Why:** this is ops-ladder L2, your "start here" level. KodeKloud gives the model (resolvers, TTL, cert chain). The handbook and the ops-ladder tools give the evidence (captures, resolver logs).
**Next:** the L2 drill "break DNS three ways", then `25-playbook-site-down.md`.

---

## 6. Web servers: Apache and Nginx (L1 → L2)

**Handbook:** `29-learn-webservers-proxies.md`, `18-web-http-tls.md`, `21-case-apache-443-dokploy.md`

**Apache:** KodeKloud has **no dedicated Apache course**. The best KodeKloud material is DevOps Pre-Requisite → Web Server → *Apache Web Server* (install, config, logs, **virtual hosts**) + lab [V2 notes] https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Web-Server/Apache-Web-Server/page. Fill the rest from the official docs: Apache Virtual Host documentation [V2] https://httpd.apache.org/docs/2.4/vhosts/ and Log Files [V2] https://httpd.apache.org/docs/2.4/logs.html. Use them with `apachectl -S` from the handbook to list every vhost, its port and its config file.

**Nginx:** *Nginx For Beginners* [V1] https://kodekloud.com/courses/nginx-for-beginners. Beginner, 6.85 h, a lab per topic. Order:
1. Install & Config, including **Firewall & Ports** [V2] https://notes.kodekloud.com/docs/Nginx-For-Beginners/Install-Config/Firewall-Ports/page.
2. **Intermediate Config**: Virtual Servers & Multiple Sites [V2] https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Virtual-Servers-Multiple-Sites/page, URL redirect/rewrite, Load Balancer, **Reverse Proxy** [V2] https://notes.kodekloud.com/docs/Nginx-For-Beginners/Intermediate-Config/Reverse-Proxy/page.
3. **Security**: HTTPS [V2] https://notes.kodekloud.com/docs/Nginx-For-Beginners/Security/HTTPS/page, headers, auth, blocking.
4. **Performance**, including **Monitoring & Troubleshooting** [V2] https://notes.kodekloud.com/docs/Nginx-For-Beginners/Performance/Monitoring-Troubleshooting/page.

**Video:** KodeKloud *NGINX For Beginners | NGINX Tutorial* [V3] https://www.youtube.com/watch?v=Hfg7_y0fGTg (86 min, 2025).

**Why:** Apache vhosts, Nginx server blocks and Traefik routers are the same idea: route by Host header or SNI to a backend. Learn it once in Nginx, where KodeKloud has labs, then map it onto Apache and Traefik.
**Next:** section 7, reverse proxies and Traefik.

---

## 7. Reverse proxies, Traefik and Dokploy (L2 → L3)

**Handbook:** `29-learn-webservers-proxies.md`, `21-case-apache-443-dokploy.md`, `26-playbook-containers-k8s.md`

**KodeKloud has no Traefik-on-Docker course and no Dokploy content.** The closest material:
- LFCS *Implement Reverse Proxies and Load Balancers* (Nginx) [V2] (link in the incident table).
- *Kubernetes Networking Deep Dive* [V1] https://kodekloud.com/courses/kubernetes-networking. Advanced, about 2 h, labs. Module **Kubernetes Ingress**: Ingress Overview → Ingress Controllers Overview → **Traefik Overview** → **Demo/Lab: Traefik Installation** (includes Traefik access logs) → **Demo: Traefik Observability** (dashboard) → External DNS. Module **Network Security**: Cert Manager and Let's Encrypt, **Lab: Securing Ingress**. This is Traefik on Kubernetes, not Docker labels, but the concepts carry over: entrypoints, routers, services, access logs, dashboard.
  - Notes: Traefik Overview [V2] https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page · Demo Traefik Installation [V2] https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Demo-Traefik-Installation/page

**Use these instead (official):**
- Traefik *Docker and Traefik Quick Start* [V2] https://doc.traefik.io/traefik/getting-started/docker/
- Traefik Docker routing reference (from ops-ladder) [V2] https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/
- Dokploy docs [V2] https://docs.dokploy.com/docs/core and Dokploy troubleshooting [V2] https://docs.dokploy.com/docs/core/troubleshooting

**Videos (non-KodeKloud):**
- Christian Lempa *Is this the BEST Reverse Proxy for Docker? // Traefik Tutorial* [V3] https://www.youtube.com/watch?v=wLrmmh1eI94 (21 min, 2021, Traefik v2-era syntax, though the router, service and label concepts are unchanged).
- Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* [V3] https://www.youtube.com/watch?v=CmUzMi5QLzI (32 min, 2025, current v3).
- No Dokploy video is recommended. The ones found (WEBdoze, Monovm) are small channels with thin content, so use the docs.

**Why:** Dokploy *is* Traefik plus Docker Swarm plus a UI. If you can read Traefik's routers and services and its access log, Dokploy 404s and 502s become ordinary proxy debugging.
**Next:** the ops-ladder L3 drill "make Traefik return 502 with a wrong port, fix it from Traefik logs alone".

---

## 8. Docker, beginner to advanced (DCA) (L3)

**Handbook:** `30-learn-docker.md`, `14-docker-containers.md`, `26-playbook-containers-k8s.md`

**KodeKloud order:**
1. *Docker Training Course for the Absolute Beginner* (listed as **free**) [V1] https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner. Beginner, about 3.7 h, labs.
   - Order: Docker Commands → **Docker Run Commands (Port Mapping, Volumes and Bind Mounts, Inspect and Logs)** → Docker Images (BuildKit, docker init, CMD vs ENTRYPOINT, env vars) → **Docker Compose** → **Docker Engine & Storage (namespaces, cgroups)** → **Docker Networking** → **Docker Registry** → Container Orchestration (Swarm, Kubernetes intro).
   - Notes: Docker Networking [V2] https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Networking/Docker-Networking/page · Docker Compose [V2] https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Compose/Docker-Compose/page · Docker Registry [V2] https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page
2. *Docker Certified Associate* [V1] https://kodekloud.com/courses/docker-certified-associate-exam-course. Associate, 13.5 h, labs and research questions, 3 mock exams. Skip the Docker Enterprise, UCP and DTR sections (Mirantis-era products you won't use). Order:
   1. **Docker Engine**: Docker Service Configuration, **Publishing Ports**, **Restart Policies**, **Troubleshooting Docker Daemon**, Demo – Docker Debug Mode, **Logging Driver**.
   2. **Docker Engine – Networking**: Networking Deep Dive – Namespaces, Networking Deep Dive – Docker.
   3. **Docker Image Management**: Image Addressing Convention, **Authenticating to Registries**, Build Cache, **Multi-Stage Builds**, Dockerfile Best Practices.
   4. **Docker Engine – Security**: namespaces, capabilities, cgroups, resource limits.
   5. Docker Engine – Storage → Docker Compose → Docker Swarm (section 9).
   - Notes: Troubleshooting Docker Daemon [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page · Logging Driver [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page · Publishing Ports [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Publishing-Ports/page · Restart Policies [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Restart-Policies/page · Networking Deep Dive – Namespaces [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Namespaces/page · Networking Deep Dive – Docker [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine-Networking/Networking-Deep-Dive-Docker/page · Multi-Stage Builds [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page
3. A free 30-minute refresher is *Crash Course: Docker For Absolute Beginners* [V1/V2] https://kodekloud.com/courses/crash-course-docker-for-absolute-beginner.

**Free practice:** Docker Playground (includes Compose) [V2] https://kodekloud.com/playgrounds/playground-docker. Docker free labs category [V2] https://kodekloud.com/studio/labs/docker ([NV] individual lab list, because the page is rendered by JavaScript).

**Gaps:** KodeKloud does not cover "published ports bypass UFW", DOCKER-USER, Docker's embedded DNS at 127.0.0.11 or the 8.8.8.8 fallback, or netshoot. Use the ops-ladder blind spots (Docker docs: Packet filtering and firewalls [V2] https://docs.docker.com/engine/network/packet-filtering-firewalls/, netshoot) plus iximiuz Labs.

**Videos:**
- KodeKloud *Learn Docker in 2 Hours - A Full Tutorial (2025)* [V3] https://www.youtube.com/watch?v=zJ6WbK9zFpI (129 min; first uploaded 2019, retitled 2025).
- KodeKloud *How Docker Networking Actually Works* [V3] https://www.youtube.com/watch?v=W7X6u2BGVRY (9 min, June 2026).
- Optional: KodeKloud *Docker Compose Tutorial | Docker for Beginners* [V3] https://www.youtube.com/watch?v=iOGEBj7Ozak (44 min, 2025).
- Alternative full course: TechWorld with Nana *Docker Tutorial for Beginners [FULL COURSE in 3 Hours]* [V3] https://www.youtube.com/watch?v=3c-iBn73dDE (166 min, 2020).

**Why:** the DCA Engine sections (daemon troubleshooting, logging driver, publishing ports, restart policies) are what you need when a Dokploy-managed container misbehaves. The beginner course alone stops before them.
**Next:** Swarm (section 9), because Dokploy runs Swarm mode.

---

## 9. Docker Swarm (L3, needed for Dokploy)

**Handbook:** `30-learn-docker.md`, `26-playbook-containers-k8s.md`

**KodeKloud:** DCA → **Docker Swarm** section [V1] (same course URL as section 8). This is the only substantial KodeKloud Swarm material. Order: Swarm Architecture → Swarm Setup 2 node Cluster → Swarm Operations → High Availability/Quorum → **Swarm Services** → **Scaling, Rolling Updates and Rollbacks** → Service Types → Placement → **Docker Config Objects** → **Docker Overlay Network** → **Swarm Service Discovery** → **Docker Stack** → (later) Disaster Recovery – Docker Swarm.
- Notes: Section Introduction [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Section-Introduction · Docker Overlay Network [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Overlay-Network/page · Swarm Service Discovery [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Swarm-Service-Discovery/page · Docker Stack [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Swarm/Docker-Stack/page
- The Docker beginner course's Container Orchestration → Docker Swarm lesson is only an overview.

**Official alternative:** Docker docs *Getting started with Swarm mode* [V2] https://docs.docker.com/engine/swarm/swarm-tutorial/

**Video:** none verified. No KodeKloud or well-known Swarm video was found that could be confirmed, so use the DCA section plus the Docker docs tutorial.

**Why:** `dokploy-network` is a Swarm overlay network, and Dokploy apps are Swarm services. "Service won't start", "task pending" and "can't reach the other container" are Swarm placement, overlay and service-discovery problems.
**Next:** registries and Harbor (section 10), then Kubernetes.

---

## 10. Container registries and Harbor with a private CA (L3)

**Handbook:** `30-learn-docker.md`, `18-web-http-tls.md`, `33-learn-cicd-iac-sre.md`

**KodeKloud has no Harbor course.** Use these KodeKloud pieces:
- Docker Beginner *Docker Registry* (deploy a private registry) [V2 notes] (link in section 8).
- DCA *Docker Image Registry* [V2] https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Docker-Image-Registry/page and *Authenticating to Registries* [V2] (link in section 8).
- GitLab CI course *Publish Image to Gitlab Container Registry* [V2] https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Publish-Image-to-Gitlab-Container-Registry/page
- Community post (not a course) *Setting up your own Container Registry with Harbor* [V2] https://kodekloud.com/community/t/setting-up-your-own-container-registry-with-harbor/275367

**Official alternative:** Harbor docs (v2.15.0) [V2] https://goharbor.io/docs/ and *Configure HTTPS Access to Harbor* [V2] https://goharbor.io/docs/2.15.0/install-config/configure-https/. Pair this with LFCS *Work With SSL Certificates* so you know which file the private CA goes into on the Docker host (`/etc/docker/certs.d/HOST/ca.crt`), on containerd nodes, and in the OS trust store (`update-ca-certificates`).

**Why:** "x509: certificate signed by unknown authority" on `docker login`, in GitLab runners or in kubelet pulls is a trust-store problem, and each client keeps its own store.
**Next:** CI (section 18) pushing to Harbor.

---

## 11. Kubernetes, beginner to CKA (L3, your top priority)

**Handbook:** `31-learn-kubernetes.md`, `15-kubernetes.md`, `26-playbook-containers-k8s.md`

KodeKloud's own CKA path ([V2] https://kodekloud.com/learning-path/cka) is: Linux for Beginners → Docker for Beginners → Kubernetes for Beginners → CKA → Ultimate CKA Mock Exam. You already have Linux and Docker, so start at step 1 below.

**KodeKloud order:**
1. *Kubernetes for the Absolute Beginners – Hands-on Tutorial* [V1] https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial. Beginner, 6 h, labs. Do it fast: Kubernetes Overview → YAML → PODs, ReplicaSets, Deployments (+ rolling update labs) → Networking → Services → Microservices (voting app) → Appendix: **kubeadm setup**. Free taster: *Crash Course: Kubernetes For Absolute Beginners* (free) [V2] https://kodekloud.com/courses/crash-course-kubernetes-for-absolute-beginners.
   - Notes: Docker vs ContainerD (ctr, nerdctl, crictl) [V2] https://notes.kodekloud.com/docs/kubernetes-for-the-absolute-beginners-hands-on-tutorial/Kubernetes-Overview/Docker-vs-ContainerD
2. *Certified Kubernetes Administrator (CKA)* [V1] https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator. Associate, about 26 h, labs, 2 Lightning Labs, 3 mock exams. The page says it was last updated in April 2026 for Kubernetes 1.35.
   - **Order for your goals** (CKA domains: Troubleshooting 30%, Cluster Architecture/Install 25%, Services and Networking 20%, Workloads 15%, Storage 10%):
     1. **Core Concepts**: Cluster Architecture, **Docker vs ContainerD**, etcd, kube-apiserver, kubelet, kube-proxy, Services.
     2. **Install Kubernetes the kubeadm way**: matches your containerd homelab, including `SystemdCgroup = true`.
     3. **Networking**: Prerequisite Switching/Routing/Gateways, **Prerequisite DNS**, **Prerequisite Network Namespaces**, **Prerequisite Docker Networking**, CNI, Pod/Service Networking, **CoreDNS in Kubernetes**, Ingress, Gateway API (2025 updates).
     4. **Troubleshooting**: Application Failure, Control Plane Failure, Worker Node Failure, Network Troubleshooting.
     5. **Cluster Maintenance**: OS upgrades, cluster upgrade, **Backup and Restore Methods** (etcd).
     6. **Security**: TLS/certificates, kubeconfig, RBAC, NetworkPolicies.
     7. Scheduling, Logging & Monitoring, Application Lifecycle Management, Storage.
     8. Helm Basics and Kustomize Basics (2025 updates).
     9. Lightning Labs → Mock Exams.
   - Notes: Cluster Architecture [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Core-Concepts/Cluster-Architecture · Docker vs ContainerD [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page · Introduction to Deployment with kubeadm [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Introduction-to-Deployment-with-kubeadm/page · Solution Install a Kubernetes Cluster using kubeadm [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Install-Kubernetes-the-kubeadm-way/Solution-Install-a-Kubernetes-Cluster-using-kubeadm/page · Prerequisite DNS [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Prerequisite-DNS · Prerequisite Network Namespaces [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Network-Namespaces/page · Prerequisite Docker Networking [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Docker-Networking/page · CoreDNS in Kubernetes [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page · Ingress [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page · Troubleshooting Section Introduction [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Troubleshooting-Section-Introduction · Application Failure [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure · Control Plane Failure [V2] https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Troubleshooting/Control-Plane-Failure/page · Worker Node Failure [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure · Backup and Restore Methods [V2] https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods
3. *Kubernetes Challenges* (**free**) [V1] https://kodekloud.com/courses/kubernetes-challenges. Four timed challenges: deploy from an architecture diagram, troubleshoot, secure.
4. *Kubernetes Troubleshooting for Application Developers* [V1] https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers. Intermediate, about 3.1 h, 43 labs and challenges. Prerequisites: kubectl refresher (get/describe/events/logs/exec/port-forward/auth can-i/top), **Ephemeral/Debug Containers**, k9s. Troubleshooting Scenarios: Image Pull Errors, Crashing Pods, Pending Pods, Create Container Errors, Config Out of Date, Endlessly Terminating Pods, RBAC, **Unreachable Pods + Leaky Network Policies**, **What the Ingress?**, Multi-Attach Volume Errors. This is the best KodeKloud break-and-fix set besides the CKA labs.
5. *Kubernetes Networking Deep Dive* [V1] (section 7): Services → **Troubleshooting Internal Networking** [V2] https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page, Cilium CNI, NetworkPolicies.
6. *Ultimate Certified Kubernetes Administrator (CKA) Mock Exam Series* [V2] https://kodekloud.com/courses/ultimate-certified-kubernetes-administrator-cka-mock-exam. Take it in the last two weeks, then killer.sh [V2] https://killer.sh/.

**Free practice:** Kubernetes multi-cluster playground [V2] https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster. Killercoda [V2] https://killercoda.com/ (ops-ladder).

**Videos:**
- KodeKloud *Kubernetes Crash Course: Learn the Basics and Build a Microservice Application* [V3] https://www.youtube.com/watch?v=XuSQU5Grv1g (130 min, 2023).
- Alternative: TechWorld with Nana *Kubernetes Tutorial for Beginners [FULL COURSE in 4 Hours]* [V3] https://www.youtube.com/watch?v=X48VuDVv0do (216 min, 2020).
- KodeKloud playlist *Learn Kubernetes with KodeKloud* [V3 playlist] https://www.youtube.com/playlist?list=PL2We04F3Y_43dAehLMT5GxJhtk3mJtkl5
- Not recommended: the KodeKloud YouTube uploads titled "Certified Kubernetes Administrator Course with Practice Tests" (9 min) and "Kubernetes For The Absolute Beginners Course" (2 min). Both turned out to be short promos, not courses [V3].

**Why:** Troubleshooting is the biggest exam domain and your homelab break-and-fix goal. The networking prerequisites (namespaces, Docker networking, DNS) explain the CoreDNS-loop and pod-DNS cases in the ops-ladder case library.
**Next:** Helm (section 13), then monitoring (section 14).

---

## 12. CKAD and CKS (after CKA)

**KodeKloud:**
- *Certified Kubernetes Application Developer (CKAD)* [V1] https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad. Associate, 14.75 h, labs, Lightning Labs, 2 mock exams. Modules: Core Concepts, Configuration, Multi-Container PODs, **Observability** (probes, logging), POD Design, Services & Networking, State Persistence, Kubernetes Challenges, Lightning Labs, Mock Exams.
- *Certified Kubernetes Security Specialist (CKS)* [V1] https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks. Professional, 8.75 h, labs, 3 mock exams. You need CKA first. Most relevant to your on-prem work: **System Hardening**, which covers SSH hardening, open ports, **UFW** ([V2] note linked in section 5), seccomp, AppArmor, then **Supply Chain Security** (Trivy scanning, registry allow-listing) and **Runtime Security** (Falco, audit logs).
- Free practice: *CKS – Challenges* (free) [V2] https://kodekloud.com/courses/cks-challenges

**Why:** CKAD's Observability module is the app-side half of `26-playbook-containers-k8s.md`. CKS System Hardening is Linux hardening with a Kubernetes label on it, and it applies straight to your Ubuntu servers.
**Next:** only after CKA. Per the ops-ladder, collect no more certificates before then.

---

## 13. Helm (and Kustomize) (L3)

**Handbook:** `31-learn-kubernetes.md`

**KodeKloud:** first the CKA course's **Helm Basics** and **Kustomize Basics** (2025 updates) sections. Then *Helm for Beginners* [V1] https://kodekloud.com/courses/helm-for-beginners (beginner, 2.25 h, labs): Introduction to Helm (install, Helm 3, architecture, charts, lifecycle management) → Helm Charts Anatomy (functions, pipelines, conditionals, named templates, hooks, packaging).
- Free practice: Helm Playground [V2] https://kodekloud.com/playgrounds/playground-helm

**Video:** KodeKloud *What is Helm? | Helm Concepts Explained* [V3] https://www.youtube.com/watch?v=kJscDZfHXrQ (13 min).

**Why:** you install Prometheus, Loki and Traefik on Kubernetes with Helm, and `helm history` and `helm rollback` are part of every Kubernetes rollback plan.
**Next:** monitoring (section 14), where the PCA course installs kube-prometheus via Helm.

---

## 14. Monitoring with Prometheus and Grafana (PCA) (L4)

**Handbook:** `32-learn-performance-observability.md`, `03-cpu-performance.md`

**KodeKloud:** *Prep Course - Prometheus Certified Associate (PCA)* [V1] https://kodekloud.com/courses/prometheus-certified-associate-pca. Associate, about 6.75–7.3 h (the page and the listing differ), labs, mock exams.
- Order:
  1. Observability Fundamentals (SLO/SLA/SLI).
  2. **Prometheus Fundamentals**: installation, including as a systemd service; **Node Exporter**; configuration; Docker; Monitoring Containers.
  3. **PromQL**: selectors, rate, aggregation, recording rules.
  4. **Alerting**: Alertmanager, receivers, silences.
  5. **Monitoring Kubernetes**: Helm, ServiceMonitors.
  6. Service Discovery and relabeling.
  7. Dashboarding, Instrumentation and Push Gateway last.
- Notes: Prometheus Basics [V2] https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Prometheus-Basics · Node Exporter [V2] https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Node-Exporter/page · Monitoring Containers [V2] https://notes.kodekloud.com/docs/Prometheus-Certified-Associate-PCA/Prometheus-Fundamentals/Monitoring-Containers/page
- The PCA course's dashboarding module uses the expression browser and console templates. For Grafana, use the free *Grafana fundamentals* tutorial [V2] https://grafana.com/tutorials/grafana-fundamentals/ (ops-ladder).

**Video:** KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* [V3] https://www.youtube.com/watch?v=6xmWr7p5TE0 (68 min, 2023).

**Why:** the ops-ladder L4 drill is node_exporter + Prometheus + Grafana with alerts for disk above 85% and failed systemd units. The PCA Fundamentals and Alerting sections cover it exactly.
**Next:** logging (section 15).

---

## 15. Logging and observability (L4)

**Handbook:** `06-logs-journal.md`, `32-learn-performance-observability.md`

**KodeKloud order:**
1. Linux-side logs first: LFCS *Locate and Analyze System Log Files* [V2] (incident table) and DCA *Logging Driver* [V2] (section 8). These match how you actually find logs on your servers: journald, `/var/log`, `docker logs`, json-file rotation.
2. *Grafana Loki* [V1] https://kodekloud.com/courses/grafana-loki. About 1.1 h plus labs. Grafana Loki Essentials (architecture, install, **Grafana Alloy agent**, collecting app logs) → Grafana Loki on Kubernetes (Helm install, **LogQL** labs, Alloy pipelines). Best fit for a homelab stack next to Prometheus and Grafana.
3. Optional, heavier: *EFK Stack: Enterprise-Grade Logging and Monitoring* [V2] https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring. Elasticsearch, Kibana, Fluent Bit.
4. *Fundamentals of SRE* → Observability and Monitoring (section 21).

**Video:** none verified from KodeKloud for Loki. Use the course labs.

**Why:** "where are this app's logs?" was one of your incident questions. The answer depends on the layer: journald for systemd units, `/var/log/apache2` for Apache, the Docker logging driver for containers, Traefik's access log for routing, and Loki to search them all in one place.
**Next:** performance (section 16).

---

## 16. Linux performance troubleshooting (L4)

**Handbook:** `23-playbook-slow-system.md`, `24-playbook-network-speed.md`, `03-cpu-performance.md`, `04-memory.md`, `32-learn-performance-observability.md`

**KodeKloud has no dedicated Linux performance course.** The relevant lessons are scattered:
- LFCS *Diagnose and Manage Processes* (ps, top, nice, signals, lsof) [V2], *Verify Integrity and Availability of Resources and Processes* [V1 curriculum], and *Monitor Storage Performance* (iostat, pidstat from sysstat) [V2] https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Storage/Monitor-Storage-Performance/page
- Nginx For Beginners → Performance → **Monitoring & Troubleshooting** [V2] (section 6).
- Fundamentals of SRE → **Performance Monitoring Deep Dive** [V2] https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page
- Docker DCA → Docker Engine – Security → Resource Limits CPU/Memory, plus cgroups [V1 curriculum].

**Use instead (ops-ladder):** Netflix *Linux Performance Analysis in 60,000 ms*, Brendan Gregg's Linux performance page, wizardzines strace and debugging zines, and the stress-ng drill.

**Videos:**
- Brendan Gregg *Linux Performance Tools, Brendan Gregg, part 1 of 2* (Velocity 2015, his own channel) [V3] https://www.youtube.com/watch?v=FJW8nGV4jxY (54 min).
- Shorter version: *Linux Performance Tools, Brendan Gregg, LinuxCon Europe 2014* [V3] https://www.youtube.com/watch?v=SN7Z0eCn0VY (49 min).

**Why:** the USE method (utilisation, saturation, errors for each resource) is the "why" behind every command in `23-playbook-slow-system.md`. KodeKloud teaches the tools but not the method.
**Next:** the ops-ladder L4 drill: stress-ng plus the 60-second checklist.

---

## 17. Ansible (L3)

**Handbook:** `33-learn-cicd-iac-sre.md`

**KodeKloud:** *Ansible Basics Course* (URL slug: ansible-for-the-absolute-beginners-course) [V1] https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course. Beginner, about 2.75 h, labs. Order: Configuration and Basic Concepts → Inventory → Variables and Facts → **Playbooks (+ verifying, ansible-lint)** → Conditionals/Loops → Modules & Plugins → **Handlers, Roles and Collections** → **Templates (Jinja2)**.
- Free practice: Ansible Playground [V2] https://kodekloud.com/playgrounds/playground-ansible. Free Ansible labs, listed as 7 on the Free Courses page [V2].

**Videos:**
- KodeKloud playlist *Ansible for the Absolute Beginners* [V3 playlist] https://www.youtube.com/playlist?list=PL2We04F3Y_42_PN52bT_U5o_lt6uPQqqq
- Jeff Geerling *Ansible 101* playlist (already in ops-ladder) [V3 playlist] https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN

**Why:** the ops-ladder L3 drill installs Docker with your `daemon.json` (DNS servers, log rotation) on a fresh VM. Handlers and templates are exactly that pattern.
**Next:** Terraform (if you do IaC on AWS) or GitLab CI.

---

## 18. CI/CD: GitLab CI (plus Jenkins and GitHub Actions) (L3)

**Handbook:** `33-learn-cicd-iac-sre.md`

**KodeKloud:** *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* [V1] https://kodekloud.com/courses/gitlab-ci-cd. Associate, 12.5 h, a lab per module.
- Order:
  1. **Architecture & Core Concepts**: pipelines, runner types, **executors**, artifacts, variables.
  2. **Continuous Integration with GitLab**: tests, caching, services, **Docker build/test/push**, **Publish Image to GitLab Container Registry**.
  3. **Self-Managed Runners**: Linux runner with shell and **Docker executor**, which is what you run on-prem.
  4. Continuous Deployment (Kubernetes, environments, GitLab Agent).
  5. Optimization, Security and Monitoring (extends/anchors, SAST, container scanning).
  6. Auto DevOps last.
- Notes: Types of Executors [V2] https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Architecture-Core-Concepts/Types-of-Executors/page · Docker Push [V2] https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page · Install Group Runner on Linux Machine with Docker Executor [V2] https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Self-Managed-Runners/Install-Group-Runner-on-Linux-Machine-with-Docker-Executor/page
- Official companion: GitLab docs *Use Docker to build Docker images* [V2] https://docs.gitlab.com/ci/docker/using_docker_build/. It covers docker-in-docker vs socket binding, the root of the "DinD runner falls back to 8.8.8.8" DNS case in the ops-ladder.
- CI/CD Playground [V2] https://kodekloud.com/playgrounds/playground-ci-cd

**Only if your job needs them:**
- *Certified Jenkins Engineer* [V1] https://kodekloud.com/courses/certified-jenkins-engineer. Associate, about 20 h, labs, mock exams.
- *GitHub Actions Certification* [V1] https://kodekloud.com/courses/github-actions-certification. 9 modules including Self Hosted Runner and Security Guide.

**Video:** TechWorld with Nana *GitLab CI CD Tutorial for Beginners [Crash Course]* [V3] https://www.youtube.com/watch?v=qP8kir2GUgo (68 min, 2022). No verified KodeKloud GitLab video was found.

**Why:** the L3 exit test is "GitLab CI builds, tags with the commit SHA, pushes to Harbor, Dokploy deploys, rollback tested". The CI and Self-Managed Runners modules cover the first half. For the Harbor half, swap the GitLab registry for Harbor plus your private CA (section 10).
**Next:** SRE practice (section 21).

---

## 19. Terraform (L3, mainly for AWS)

**KodeKloud order:**
1. *Terraform Basics Training Course* [V1] https://kodekloud.com/courses/terraform-basics-training-course. Beginner, 4.75 h, labs. Order: Getting Started → Terraform Basics → **Terraform State** → Working with Terraform (lifecycle, data sources, count/for_each) → Terraform with AWS → **Remote State (S3 backend, locking)** → Import/Taint/**Debugging** → Modules.
2. *Terraform Challenges* (**free**) [V2] https://kodekloud.com/courses/terraform-challenges
3. Later, if you want the certificate: *HashiCorp Certified: Terraform Associate 004* [V2] https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004

**Video:** KodeKloud *What is Terraform? | Introduction To Terraform Basics* [V3] https://www.youtube.com/watch?v=mzgfHmDRamk (23 min).

**Why:** state and remote state are where most real Terraform incidents start, such as drift, locks and imports. **Next:** AWS (section 20).

---

## 20. AWS (Cloud Practitioner, CloudOps/SysOps, networking)

**Handbook:** `16-aws-cloud.md`

**KodeKloud order:**
1. *Crash Course: AWS Basics* (**free**) [V1] https://kodekloud.com/courses/crash-course-aws-basics. About 30 min plus labs: S3, EC2, VPC.
2. *AWS Networking Fundamentals* [V1] https://kodekloud.com/courses/aws-networking-fundamentals. Beginner, 3 h, labs: VPC, subnets, gateways, routing, security groups, load balancers, Route 53/DNS in VPC, Transit Gateway, CloudFront. Take this before any certificate. It maps straight onto `25-playbook-site-down.md` in the cloud.
3. *AWS Certified Cloud Practitioner (CLF-C02)* [V1] https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02. 15 h, 8 modules. Only if you want the badge.
4. *AWS Certified CloudOps Engineer - Associate* [V1] https://kodekloud.com/courses/aws-certified-sysops-administrator-associate. About 22 h, labs. **Note:** the old SysOps Administrator URL now serves this retitled course. Domains: Monitoring/Logging/Remediation (CloudWatch, CloudTrail, EventBridge, SSM), Reliability, Deployment/Automation, Security, **Networking and Content Delivery (VPC, Route 53, troubleshooting connectivity)**, Cost/Performance. **[NV]** exam code: the fetched page did not state it clearly.
- AWS Playground [V2] https://kodekloud.com/cloud-playgrounds/aws. Free 100 Days of Cloud [V2] https://kodekloud.com/100-days-of-cloud

**Video:** KodeKloud *AWS Networking Basics | AWS VPC & Subnets for Beginners* [V3] https://www.youtube.com/watch?v=QM63dyA_4Pc (18 min, 2025).

**Why:** your on-prem layered walk (DNS → route → firewall → TLS → proxy → app) becomes Route 53 → route tables → security groups and NACLs → ALB/ACM → target health on AWS. **Next:** CloudOps only after CKA.

---

## 21. SRE practice and incident management (L4)

**Handbook:** `33-learn-cicd-iac-sre.md`, `34-roadmap.md`

**KodeKloud:** *Fundamentals of SRE* [V1] https://kodekloud.com/courses/fundamentals-of-sre. About 7.1 h, labs, quizzes and games, with a capstone on the "KodeKloud Record Store" app.
- Order: Service Level Objectives and Measurements (SLIs, SLOs, error budgets; **Lab: Building a Monitoring Dashboard**) → **Incident Management** (Preparing for Incidents, Designing Effective Alerts, IMAG roles, **Blameless Postmortem Culture**, **Root Cause Analysis**) → Managing Complexity, Risk and Toil (**Change Management for Reliability**, capacity planning, toil) → Release Engineering (production readiness, IaC lab, secure release pipeline lab) → Observability and Monitoring → Chaos Engineering.
- Notes: Root Cause Analysis [V2] https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page · Blameless Postmortem Culture [V2] https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page · Change Management for Reliability [V2] https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page
- KodeKloud's SRE learning path [V2] https://kodekloud.com/learning-path/site-reliability-engineer also adds Golang, Python, OTCA, Azure and GCP. That is far broader than you need now, so skip it.

**Use with it (ops-ladder):** the Google SRE book chapters 12, 14 and 15, GitLab change management and its 2017 postmortem, and *Debugging: The 9 Indispensable Rules*.

**Video:** none recommended. The only KodeKloud SRE item found is a YouTube Short. Read the SRE book instead.

**Why:** the Apache → Dokploy cut-over is a change with a rollback, and a postmortem is how you turn it into proof of your skill. **Next:** the ops-ladder L4 game day.

---

## 22. KodeKloud free offerings, all in one place

| What | URL | Tag | Use it for |
|---|---|---|---|
| KodeKloud Notes (free text of every lesson) | https://notes.kodekloud.com/ | [V2] | Step 3 of the loop: review and grep lessons without a subscription |
| Free Courses list | https://kodekloud.com/free-courses | [V1] | Docker Absolute Beginner, crash courses, Linux/Kubernetes/Terraform/CKS Challenges |
| Free labs (Studio) | https://kodekloud.com/studio/labs (categories such as /linux, /docker, /devops) | [V2] ([NV] individual lab list, rendered by JavaScript) | Topic labs. The Free Courses page counts DevOps 12, Kubernetes 7, Docker 9, Git 15, Terraform 26, Linux 20, Ansible 7, Jenkins 5 |
| Playgrounds | https://kodekloud.com/studio/playgrounds · Ubuntu https://kodekloud.com/playgrounds/playground-ubuntu · Docker https://kodekloud.com/playgrounds/playground-docker · Kubernetes multi-cluster https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster · Git, Helm, Ansible, CI/CD, AWS | [V2] (Ubuntu page fetched: free, 24.04, 1 h + 15 min extensions [V1]) | Step 4: break and fix without your homelab |
| KodeKloud Engineer | https://engineer.kodekloud.com/ (curriculum: https://engineer.kodekloud.com/curriculum) | [V2] | Morning rep: real tasks on real systems |
| 100 Days of DevOps | https://kodekloud.com/100-days-of-devops | [V1] | "100% free", 100 tasks across Git, Docker, Kubernetes, Linux, CI/CD, Terraform, Python, monitoring. Free plan: one task a day |
| 100 Days of Cloud | https://kodekloud.com/100-days-of-cloud | [V2] | AWS morning reps |
| KodeKloud YouTube | https://www.youtube.com/@KodeKloud | [V2] | Free full-length crash courses (Linux, Docker, Kubernetes, Nginx, shell) |
| devops-101 visual guides | https://github.com/kodekloudhub/devops-101 | [V2] | Cheat-sheet style infographics |
| Community forum | https://kodekloud.com/community/ | [V2] | Ask about lab errors |

**KodeKloud Engineer, free or not:** the 100 Days of DevOps page says the program is "100% free" with one task a day on Free and Standard plans [V1]. A KodeKloud blog page describes the KodeKloud Engineer practice area as needing enrollment. Expect a free tier with daily limits.

---

## 23. Where KodeKloud has nothing, and what to use instead

| Topic | KodeKloud coverage | Use instead |
|---|---|---|
| Traefik on Docker (labels, entrypoints, 502s) | Traefik on Kubernetes only (K8s Networking Deep Dive) | Traefik Docker quick start [V2] https://doc.traefik.io/traefik/getting-started/docker/ + Docker routing reference (ops-ladder) |
| Dokploy | None | Dokploy docs [V2] https://docs.dokploy.com/docs/core + troubleshooting [V2] |
| Harbor + private CA | Registry basics only | Harbor docs [V2] https://goharbor.io/docs/ + Configure HTTPS [V2] |
| Apache httpd in depth | One lesson (DevOps Pre-Requisite) | Apache vhosts [V2] https://httpd.apache.org/docs/2.4/vhosts/, logs [V2] https://httpd.apache.org/docs/2.4/logs.html |
| tcpdump, strace, getaddrinfo, systemd-resolved debugging, curl --resolve | None found | ops-ladder blind spots (wizardzines, Julia Evans, Arch Wiki, everything curl) |
| Linux performance method (USE, 60-second checklist) | Tools only (LFCS lessons) | Netflix 60,000 ms article, Brendan Gregg (ops-ladder) |
| Real broken servers, timed | Linux/Kubernetes Challenges, KodeKloud Engineer | SadServers, iximiuz Labs, Killercoda (ops-ladder) |
| Docker firewalling (published ports skip UFW, DOCKER-USER) | None | Docker docs: Packet filtering and firewalls [V2] |
| Docker Swarm video | DCA Swarm section only | Docker docs Swarm tutorial [V2] https://docs.docker.com/engine/swarm/swarm-tutorial/ |

---

## 24. Suggested order (CKA first, morning reps for the rest)

| Weeks | Main block (evenings and weekend) | Morning rep (30 min) | Handbook drill |
|---|---|---|---|
| 1 | The incident lessons table above + DevOps Pre-Requisite (Web Server, SSL/TLS) | 100 Days of DevOps, Linux tasks | Replay `21-case-apache-443-dokploy.md` on the Ubuntu playground |
| 2–3 | LFCS: Operations Deployment + Networking sections | KodeKloud Engineer / SadServers | ops-ladder L1 exit test; `22-playbook-ports-inventory.md` |
| 4 | Docker Absolute Beginner (free) → DCA Engine + Networking | Docker tasks | `30-learn-docker.md`; netshoot drill |
| 5 | DCA Swarm + Traefik (K8s Networking Deep Dive: Ingress module) + Traefik/Dokploy docs | Linux Challenges (free) | Traefik 502 drill; `26-playbook-containers-k8s.md` |
| 6–11 | **CKA** in the order given in section 11 + Kubernetes Troubleshooting for App Developers | Kubernetes Challenges (free), Killercoda | Homelab break-and-fix; ops-ladder Kubernetes cases |
| 12 | CKA Lightning Labs, mock exams, Ultimate CKA Mock Exam, killer.sh | | Take CKA |
| 13–14 | Demystifying DNS + GitLab CI (CI and Self-Managed Runners) + Harbor docs | Git, CI/CD tasks | ops-ladder L3 exit test |
| 15–16 | PCA (Fundamentals, Alerting, Kubernetes) + Grafana Loki + Fundamentals of SRE (Incident Management) | Monitoring tasks | ops-ladder L4 game day + postmortem |
| Later | Ansible Basics, Terraform Basics, AWS Networking Fundamentals, CKAD/CKS, CloudOps | 100 Days of Cloud | `33-learn-cicd-iac-sre.md`, `16-aws-cloud.md` |

Course facts (lengths, modules, free status) were read from KodeKloud pages on 3 Oct 2026 and can change. Re-check a course page before you buy or schedule anything.

