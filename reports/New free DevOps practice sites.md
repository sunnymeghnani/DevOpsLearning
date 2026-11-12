# Fresh free labs carry on-prem skills cloudward

A sweep on 7 November 2026 found **about 95 free practice sites, games, labs and drill kits that module 54 does not list yet**. For an on-prem engineer moving to cloud, the useful ones form a clear ladder. The first rung is break-fix practice on your own stack: SadServers' free Traefik, Docker and Kubernetes scenarios (SadServers is already in module 54), Harbor's own public demo server and Linuxzoo's free root VMs. The second rung is the cloud-native bridge, led by Isovalent's Cilium lab and its broken-HTTPRoute exam. The third rung is cloud work in accounts the vendor owns, which cannot bill you: AWS Educate, the AWS Builder Center sandbox, Pwned Labs, Cybr and Microsoft Applied Skills labs. Supply is uneven. Browser games and Linux or Kubernetes labs are plentiful, and DevOps Daily alone offers 62 free simulators ([DevOps Daily](https://devops-daily.com/games)). **No free SadServers-style cloud break-fix platform exists.** AWS Jam is the best one, and it stays behind a subscription ([AWS Jam](https://aws.amazon.com/training/digital/aws-jam/)). The open-source cloud "goats" (deliberately vulnerable labs) deploy into your own account, where IAM Vulnerable's optional Glue module costs about $4 an hour ([IAM Vulnerable](https://github.com/BishopFox/iam-vulnerable)). The biggest status change: **two module-54 entries, EKS Cluster Games and The Big IAM Challenge, were unreachable on 7 Nov 2026.** Their domains, like Wiz's K8s LAN Party, have no DNS address records ([dns.google](https://dns.google/resolve?name=eksclustergames.com&type=A)). Re-check them before retiring. Wiz's newer Cloud Security Championship still loads and covers the same Kubernetes and container skills. The other changes are small, and four niche GitHub lists are the best places to find more. Two gaps remain: nothing free trains Dokploy or Docker Swarm break-fix, and nothing covers macOS.

## Start here: eight steps from your racks to the cloud

The order runs from your own stack towards the cloud, and from no bill risk to very little. Every step runs in a browser or in an account the vendor owns, so nothing is installed on your machine. Levels are the researchers' estimates on the handbook scale (L0 Fresher to L4 Senior/Lead).

1. **SadServers' free scenarios that match your stack** (already in module 54 §1; the new part is which free scenarios match your stack). These are all free: "San Juan: mucho Traefik" (Docker Compose), "Salta" (a Docker container won't start), "Helsingør" (Postgres replication in Compose), "Bilbao", "Buenos Aires" and "Bengaluru" (Kubernetes), and "Kilifi" (Helm) ([scenarios](https://sadservers.com/scenarios)). Free VMs have no internet access and are destroyed afterwards ([FAQ](https://sadservers.com/faq)). L1–L3, modules 43, 44, 46.
2. **Harbor demo server** ([demo.goharbor.io](https://demo.goharbor.io)). Self-register, create a project, then `docker login` and push an image under 100 MB from a codespace. It resets every two days and offers user functions only ([Harbor docs](https://goharbor.io/docs/main/install-config/demo-server/)). L1, modules 44, 47.
3. **Isovalent "Getting Started with Cilium"**. Install Cilium on a cluster that has no CNI, move from L3 to L7 policy, publish a path with Gateway API, and pass an exam that asks you to "diagnose and fix an HTTPRoute that doesn't match the expected request" ([lab](https://isovalent.com/labs/cilium-getting-started/)). L1–L3, modules 31, 43, 46.
4. **AWS Educate, then the AWS Builder Center sandbox**. Educate gives console labs in a sandbox with "No credit card needed" ([AWS Educate](https://aws.amazon.com/education/awseducate/)). The Builder Center sandbox gives a ready-made AWS account for 8 hours, once a week, for selected workshops, with no card ([AWS What's New](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/)). L0, then L1–L3, module 36.
5. **HashiCorp Terraform sandbox**. Terraform, Docker and LocalStack in the browser for up to an hour ([HashiCorp](https://developer.hashicorp.com/terraform/sandbox)). L1–L2, modules 33, 50.
6. **Pwned Labs and Cybr free labs**. Over 30 of Pwned Labs' 90 scenarios and 33 of Cybr's 123 labs are free, and both run in cloud accounts the vendor provides ([Pwned Labs](https://pwnedlabs.io/explore), [Cybr](https://cybr.com/hands-on-labs/)). L1–L3, modules 36, 37.
7. **Microsoft Applied Skills labs**. Timed 30- or 45-minute tasks in a live Azure environment that the lab supplies ([lab FAQ](https://learn.microsoft.com/en-us/credentials/support/assessment-lab-frequently-asked-questions)). For non-students this is the only no-card way the researchers found into a real Azure portal now that Learn sandboxes are retired. Only community write-ups, not Microsoft, say it is free. L1–L3, modules 55, 36.
8. **Wiz Cloud Security Championship**. "Game of Pods" (Kubernetes privilege escalation), "Contain Me If You Can" (container escape) and "State of Affairs" (Terraform) are the L3–L4 stretch ([CSC](https://www.cloudsecuritychampionship.com/)). They also replace EKS Cluster Games while that domain is unreachable. No price is shown; that it is free is an inference.

Between these steps, The Incident Challenge (live rounds every other Monday) and K8s Games' Chaos mode give the best free incident practice. For anything self-hosted, use a GitHub Codespace as the throwaway host. A free personal account gets 120 core-hours of compute and 15 GB-month of storage a month with no payment method, and usage is blocked rather than billed at the quota ([GitHub Docs](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces)). That is about 60 hours on the smallest 2-core machine.

## New finds by category, sorted by where they run

Each table below lists finds that are not in module 54, with the module-54 section each would join. **Runs where** uses four settings:

- **Browser**: the vendor hosts everything.
- **Vendor's cloud account**: a real cloud account the vendor provisions, with no bill to you.
- **Throwaway VM or codespace**: self-hosted, never on your own machine.
- **Own cloud account (bill risk)**: you deploy it and you pay.

**Level (est.)** is the researchers' estimate, not the site's claim. For sign-up and card, "no card (stated)" means the site says so, and "none seen" means no card prompt appeared on the pages opened. Nothing was signed up for, so every "free" label describes the site before login.

**Module** numbers:

- **OS and command modules:** 06 logs, 16 AWS commands, 17 Windows.
- **Playbooks:** 23 slow system, 25 site down, 26 containers/K8s.
- **Learn modules:** 27 Linux, 28 networking, 29 web servers and proxies, 30 Docker, 31 Kubernetes, 32 performance and observability, 33 CI/CD-IaC-SRE, 35 deployment patterns, 36 cloud/AWS, 37 security, 38 databases, 39 senior architecture, 40 career ladder.
- **Problems and toolbox modules:** 41 Linux problems, 42 network/DNS/TLS problems, 43 Traefik, 44 Docker/Swarm/registry, 45 Dokploy, 46 Kubernetes problems, 47 CI/CD toolbox, 48 Wazuh, 49 observability toolbox, 50 cloud/IaC problems, 52 day-to-day.
- **Paths:** 55 on-prem vs cloud.

### Real broken boxes in the browser: Linuxzoo and tmpfs.tech join SadServers (module 54 §1–2)

Linuxzoo is the strongest new real-machine find. It is a free remote Linux VM with root access, run by Edinburgh Napier University since 2004. Its tutorials cover Apache, DNS, firewalls, SELinux and diagnostics, so it is the only new find that offers server-side break-fix topics at no cost without touching your machine. tmpfs.tech and SudoRank are the new competitors to SadServers. Their limits rest on thin evidence: guest play on one, an aggregator's price list on the other. prepare.sh contradicts itself about sign-up.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Linuxzoo** · [linuxzoo.net](https://linuxzoo.net/) | A private VM with root (AlmaLinux 10, Kali, Caine forensics) and tutorials on administration, networking, SELinux, firewalls, DNS, diagnostics, Apache, logs, email and disk forensics | Free, no paid tier mentioned; status "Stable" | Register and join a queue; no card mentioned | Browser SSH client (or your terminal) to their VM | L0–L2 | 27, 41 |
| **tmpfs.tech** · [tmpfs.tech](https://tmpfs.tech/) | Challenges on disposable Linux boxes ("a real box, not a quiz"); a launch post claims 720 challenges ([dev.to, snippet](https://dev.to/binrick/show-dev-tmpfstech-720-hands-on-linux-challenges-on-real-ephemeral-vms-in-your-browser-23kf)) | No prices shown; limits unknown | "Play as guest"; Google or GitHub sign-in optional | Browser, their disposable VMs | L0–L2 | 27, 41 |
| **SudoRank** · [sudorank.com](https://sudorank.com/) | Broken Linux VMs and multi-node Kubernetes clusters | Free tier "8 tracks with 281 challenges"; Pro $8/mo, Pro+ $15/mo; aggregator figures only ([Slashdot](https://slashdot.org/software/comparison/SudoRank-vs-kpt/)) | Unverified (page did not render) | Browser to real VMs, per aggregator | L1–L3 | 41, 46 |
| **prepare.sh** · [prepare.sh](https://prepare.sh/) | Interview-style labs on Linux, Kubernetes, Argo CD, PostgreSQL, Kafka | Conflicting: "Free, and no sign-up required", yet the start button leads to sign-in; DevOpsCube reports most labs free, premium from $30/mo ([DevOpsCube](https://devopscube.com/websites-to-practice-devops/)) | Unclear | Browser ("machines that boot in your browser") | L1–L3 | 52, 40 |
| **systemd by example** · [systemd-by-example.com](https://systemd-by-example.com/) | Edit, add and remove unit files and watch dependencies and targets behave | No price or login mentioned; 10 min per run, no network, capped CPU, memory and processes ([playground post](https://seb.jambor.dev/posts/systemd-by-example-the-playground/)) | None mentioned | Browser; a podman container on their server | L2–L3 | 41, 27 |
| **Webminal** · [webminal.org](https://www.webminal.org/) | Browser terminal with lessons up to shell scripting, "Linux Command Golf" and MySQL | Free "always & forever", running since 2011 | Register; no card mentioned | Browser | L0–L1 | 27 |
| **WebVM** · [webvm.io](https://webvm.io/) and **Linux Dungeon** · [demo](https://jfoxuk.github.io/webvm/) | Full Linux in WebAssembly; Linux Dungeon is an escape-room game of directories, clues and config edits ([showcase](https://labs.leaningtech.com/showcase/linux-dungeon)) | Free, Apache-2.0; pushed 2026-11-02 ([GitHub API](https://api.github.com/repos/leaningtech/webvm)) | None mentioned | Browser tab only | L0–L1 | 27 |

### Containers, registry and Kubernetes: practise on Harbor itself (module 54 §5–6)

The Harbor demo is the most stack-specific find in the sweep. It is the registry you run at work, public and reset every two days, so you can rehearse project and push workflows with no risk to production. Meshery gives live clusters that reset daily. Red Hat's Developer Sandbox gives 30 days of OpenShift with no card but asks for a phone number. The DevOps-Daily challenges are graded by GitHub Actions on your pull request, and those pull requests are public, so sanitise everything you submit.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Harbor demo server** · [demo.goharbor.io](https://demo.goharbor.io) | Projects, `docker login`, push and pull on your own registry product; user functions only, no admin | Free; images under 100 MB; "cleaned and reset every two days"; no sensitive images ([docs](https://goharbor.io/docs/main/install-config/demo-server/)) | Self-register (username, email, password); none seen | Browser UI plus a Docker client in a codespace or throwaway VM | L1 | 44, 47 |
| **Meshery Playground** · [play.meshery.io](https://play.meshery.io) | Live Kubernetes clusters with CNCF projects: traffic splitting, circuit breaking | "Perpetually free, full access"; clusters reset daily ([Meshery docs](https://docs.meshery.io/installation/playground)) | Named account required | Browser, live clusters | L1–L2 | 31 |
| **DevOpsLesson Kubernetes Playground** · [devopslesson.com/playground/kubernetes](https://devopslesson.com/playground/kubernetes) | 18 auto-checked `kubectl` steps (about 30 min); Docker playground and CKA practice lab alongside | Free | No sign-up, no card (stated) | Browser (simulated) | L0–L1 | 31 |
| **Red Hat Developer Sandbox** · [developers.redhat.com/developer-sandbox](https://developers.redhat.com/developer-sandbox) | Hosted OpenShift with Pipelines, Dev Spaces and a guided "Learn Kubernetes" activity | Free for 30 days, restartable; CPU and RAM limits not stated ([FAQ](https://developers.redhat.com/developer-sandbox/FAQ)) | Red Hat account and a phone number; "no credit card required" | Browser (web console, optional `oc`) | L1–L2 | 31 |
| **DevOps-Daily challenges** · [github.com/The-DevOps-Daily/challenges](https://github.com/The-DevOps-Daily/challenges) | Six graded fixes: shrink a Docker image, summarise an access log in Bash, fix a Kubernetes deployment, write Prometheus alerts, speed up PostgreSQL, build a Terraform network module ([README](https://raw.githubusercontent.com/The-DevOps-Daily/challenges/main/README.md)) | Free, MIT; pushed 2026-11-04 | GitHub account; your PRs are public | Fork and PR, graded on GitHub's runners | L1–L2 | 30, 31, 32, 33, 38 |
| **Helm Playground** · [helm-playground.com](https://helm-playground.com/) | Debug Helm templates against values (WASM build with Sprig) | Free; Helm version not stated; last push 2025-08-14 | None | Browser | L1–L2 | 31, 46 |
| **Kyverno Playground** · [playground.kyverno.io](https://playground.kyverno.io/) | Kyverno admission policies | Free; repo pushed 2026-11-06 ([GitHub API](https://api.github.com/repos/kyverno/playground)) | Not verified (JS app) | Browser | L2 | 37, 46 |
| **OPA Rego Playground** · [play.openpolicyagent.org](https://play.openpolicyagent.org) | Rego policies | Free; reachable (HTTP 200), content unread | Not verified | Browser | L2 | 37 |

### Vendor labs bridge Traefik and kubeadm to Gateway API, service mesh and eBPF (module 54 §6, §9)

These labs connect the user's current world (Traefik labels, a kubeadm cluster) to cloud-native networking. **Isovalent's 12-lab list is the standout.** Its labs run in an individual Instruqt environment for 30–60 minutes, and the list includes 15-minute "Discovery" labs on AKS and EKS ([lab list](https://isovalent.com/resource-library/labs/)). Solo and Tetrate cover Istio, Envoy and Gateway API, but the researchers could not open a lab page to confirm whether a cluster is provided in the browser.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Isovalent labs** · [isovalent.com/labs](https://isovalent.com/resource-library/labs/) | Cilium (L3 to L7 policy, Gateway API, WireGuard, fix-the-HTTPRoute exam), Kubernetes networking basics, Tetragon, LB IPAM and L2 announcements, packet capture | Free; badges "Cost: Free" ([Credly, snippet](https://www.credly.com/org/isovalent/badge/cilium-getting-started)); 2 labs are Enterprise | A name/email form is likely (HubSpot forms in the page source); none seen | Browser (Instruqt) | L1–L3 | 31, 43, 46, 49 |
| **Solo Academy** · [solo.io/academy](https://solo.io/academy) | Istio and Ambient Mesh (mTLS, authorization, waypoints, fault injection, sidecar to sidecarless), kgateway with Argo Rollouts canaries | "Free training courses"; Istio course about 2 h, 80% on the final assessment earns a certification ([snippet](https://solo.io/resources/lab/solo-academy-course-get-started-with-istio-service-mesh)) | Not confirmed | Labs; delivery not confirmed | L1–L3 | 31, 43, 47 |
| **Tetrate Academy** · [academy.tetrate.io](https://academy.tetrate.io/) | Istio, Envoy and Envoy Gateway fundamentals; Istio 0–60 workshop with labs on a Kubernetes cluster | Free courses; the Service Bridge course costs $499 | Sign-up | Online course; lab delivery not confirmed | L1–L2 | 43, 31 |
| **LF LFS148 OpenTelemetry** · [training.linuxfoundation.org](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/) | 11 chapters, 8–10 hours, OpenTelemetry labs and a badge | $0; 90 days of access | LF portal login | Dev Container or GitHub Codespaces; use Codespaces | L1 | 32, 49 |

### Observability playgrounds need no install and no account (module 54 §9)

The official Prometheus demo adds two things to the PromLabs demo already in module 54: a live Alertmanager and a live node_exporter, run by the Prometheus project itself ([demo.prometheus.io](https://demo.prometheus.io)). The three pipeline-language playgrounds (LogQL, VRL, OTTL) cover the log and telemetry transforms that are hardest to practise on a production stack. A community PromQL Playground with guided scenarios against demo.promlabs.com also exists ([promql-playground.vercel.app](https://promql-playground.vercel.app/)), but the researchers saw only its loading screen.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Prometheus demo site** · [demo.prometheus.io](https://demo.prometheus.io) | Live Prometheus, Alertmanager, node_exporter and Grafana | Free | None | Browser | L1–L2 | 32, 49 |
| **Grafana LogQL simulator** · [Loki docs](https://grafana.com/docs/loki/latest/query/analyzer/) | LogQL line filters, logfmt, json, pattern and regex parsers, label filters and `line_format` on sample or pasted lines | Free; "very limited": stream selector fixed to `{job="analyze"}`, no metric queries | None | Browser | L1–L2 | 49 |
| **VRL Playground** · [playground.vrl.dev](https://playground.vrl.dev/) | Vector Remap Language programs run against events, shareable | Free; repo pushed 2026-11-06 | None | Browser | L1–L2 | 49 |
| **OTTL Playground** · [ottl.run](https://ottl.run) | OpenTelemetry Collector transformation statements | Free; use the bare domain (the `www.` host returned Cloudflare 522); repo pushed 2026-10-27 ([GitHub API](https://api.github.com/repos/elastic/ottl-playground)) | None | Browser | L2 | 49 |

### Cloud without a bill: vendor-owned sandboxes grew in 2026 (module 54 §7)

What matters here is who owns the account. AWS added the Builder Center sandbox in July 2026; it is covered in the status section, because module 54 already lists AWS Workshops. Microsoft moved the other way and retired its Learn sandboxes. Evidence for two rows is thin. AWS Educate's lab list comes from a 2022 post, and its FAQ returned 404. Oracle LiveLabs timed out, so only search snippets were seen. Students can add Azure for Students: $100 of credit for 12 months with "No credit card required" ([Azure](https://azure.microsoft.com/en-us/free/students)).

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **AWS Educate** · [aws.amazon.com/education/awseducate](https://aws.amazon.com/education/awseducate/) | Console labs on IAM, VPC, EC2, S3, RDS and a static S3 website (list from a [2022 AWS post](https://aws.amazon.com/blogs/training-and-certification/aws-educate-expands-access-to-free-cloud-education)) | "Completely for free"; unlimited attempts within a time window | Email, age 13+, no Amazon account; "No credit card needed" | Vendor's AWS sandbox | L0 | 36, 16 |
| **AWS SimuLearn** (inside Skill Builder) · [aws.amazon.com/training/digital/aws-simulearn](https://aws.amazon.com/training/digital/aws-simulearn/) | Talk to an AI "customer", then do a guided build in "a risk-free AWS environment" | Free accounts get "limited access"; full access needs Skill Builder Individual ($29/mo or $299/yr, snippet) | Skill Builder account; card not stated | Vendor's AWS environment | L0–L2 | 36 |
| **Oracle LiveLabs** · [livelabs.oracle.com](https://livelabs.oracle.com/) | OCI and Oracle workshops, mostly database and AI | Sandbox reservations free and deleted at expiry ([help, snippet](https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/page_help)); reservation length unknown | Account unverified; no card for the sandbox (your own OCI Free Tier usually needs one) | Oracle-owned tenancy | L0–L2 | 36, 55 |
| **Microsoft Applied Skills** · [learn.microsoft.com/credentials/applied-skills](https://learn.microsoft.com/en-us/credentials/applied-skills/) | Timed portal tasks for Azure Administrator, Network Engineer, Windows Server Hybrid, Security and DevOps paths | Free per community write-ups only ([DEV](https://dev.to/gracelee087/i-got-a-microsoft-certification-for-free-heres-how-applied-skills-review-5cf9)); 30 or 45 min, no save and resume; some labs reported unavailable | Microsoft Learn profile; card not stated | Lab VM connected to a live Azure environment | L1–L3 | 55, 36, 17 |
| **HashiCorp sandboxes** · [developer.hashicorp.com/terraform/sandbox](https://developer.hashicorp.com/terraform/sandbox) | Terraform with Docker, LocalStack and `awslocal`; also Vault, Consul, Nomad and Boundary | Up to 1 h, nothing saved; price not stated | Not stated | Browser; never point it at real AWS, which the timer does not clean up | L1–L2 | 33, 50 |

### Cloud and Kubernetes security CTFs run in the vendor's accounts (module 54 §7, §11)

Pwned Labs and Cybr are the safest real-cloud practice in the sweep, because the vendor provisions the account and, at Cybr, cleans it up automatically. The Wiz Championship ran its 12 monthly challenges from June 2025 to May 2026, and 11 of the 12 can still be entered. It goes "straight to the expert level" ([Wiz blog](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges)). Two smaller options are not in the table. HackerDNA has a free plan with no card, but Pro locks all labs and official solutions ([HackerDNA](https://hackerdna.com/)). The SANS Holiday Hack Challenge's 2026 game "The Pyramid on the Ice" had not opened on 7 Nov 2026, and submissions close on 5 Jan 2027 ([SANS](https://www.sans.org/mlp/holiday-hack-challenge/)).

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Pwned Labs** · [pwnedlabs.io/explore](https://pwnedlabs.io/explore) | AWS, Azure, GCP, Kubernetes, CI/CD and hybrid attack-and-defence scenarios | "Over 30" of 90 scenarios free; paid prices unreadable (JS page) | Free account; card not stated | Real cloud accounts "that we provision for you" | L1–L3 | 36, 37 |
| **Cybr** · [cybr.com/hands-on-labs](https://cybr.com/hands-on-labs/) | AWS and Azure red- and blue-team labs | 33 of 123 labs free; auto-cleanup to prevent "surprise bills" | Free account; "No credit card required" ([snippet](https://cybr.com/?p=22193)) | Vendor's AWS and Azure | L1–L3 | 36, 37 |
| **Wiz Cloud Security Championship** · [cloudsecuritychampionship.com](https://www.cloudsecuritychampionship.com/) | Container escape, Kubernetes privilege escalation through `nodes/proxy` ([write-up, snippet](https://kabinet.gitbook.io/ctf-writeup/2026/wiz-cloud-security-challenge/game-of-pods)), Terraform automation, restricted Kubernetes networking, S3, Azure AD | 11 of 12 enterable (Aug 2025 inactive); hints cost points; no price shown | Login/Register | Vendor-provided environment | L3–L4 | 37, 46, 36 |
| **Wiz Cloud Hunting Games** · [cloudhuntinggames.com](https://www.cloudhuntinggames.com/) | Incident-response investigation of a fictional data-extortion case | Price not stated | Not stated | Browser | L2–L3 | 37, 48, 36 |
| **OWASP WrongSecrets** · [wrongsecrets.herokuapp.com](https://wrongsecrets.herokuapp.com/) | 76 challenges on secrets leaking through code, configs, container images and cloud | Free, open source; hosted demo "not always up" ([README](https://github.com/OWASP/wrongsecrets)); Render mirror returned 503 | No sign-up | Hosted for the Docker challenges; K8s/Vault ones self-hosted; cloud ones in your own account | L1–L3 | 37, 44 |
| **PortSwigger Web Security Academy** · [portswigger.net/web-security](https://portswigger.net/web-security) | 31 topics including request smuggling, cache poisoning, Host-header attacks, SSRF, CORS, OAuth, JWT | "100% free"; Burp Community is enough | Account for progress; none seen | Browser labs; run Burp Community in a throwaway VM | L1–L3 | 29, 37, 43 |
| **Root-Me** · [root-me.org](https://www.root-me.org/) | Network pcap and protocol challenges among 600+ challenges | Free for personal, non-professional use ([2026 guide, snippet](https://hackerdna.com/blog/root-me)) | Account; challenge machines accept only logged-in IPs | Browser and their machines; open pcaps in a VM | L1–L3 | 28, 42, 37 |

### Own-account goats can bill you, at up to about $4 an hour (module 54 §7, §11)

These labs fall under module 54's existing "hidden cost" warning. They belong in a dedicated account, never one near production. The safest container is the **AWS Free plan**. It gives up to $200 of credits, closes after six months or when the credits run out, and promises "No charges incurred unless you upgrade to a Paid plan or activate paid-only services" ([AWS Free Tier](https://aws.amazon.com/free/)). The page does not say whether a card is needed at sign-up. AWSGoat's README has no cleanup section, so run `terraform destroy` the same day. AzureGoat and GCPGoat (last pushed October 2024) and Sadcloud (October 2023) are stale and left out.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **CloudFoxable** · [cloudfoxable.bishopfox.com](https://cloudfoxable.bishopfox.com/) | 18 gamified AWS attack-path flags (CTFd), deployed with Terraform | Free OSS; flags split into "Always on (Low or No cost)" and "Enable as needed (These challenges incur cost)" ([README](https://raw.githubusercontent.com/BishopFox/cloudfoxable/main/README.md)); pushed 2026-05-01 | Your AWS account | Own AWS account (bill risk); never production, shared or corporate | L2–L3 | 37, 36 |
| **IAM Vulnerable** · [github.com/BishopFox/iam-vulnerable](https://github.com/BishopFox/iam-vulnerable) | 31 IAM privilege-escalation paths | Default free; optional EC2 about $4.50/month, Glue about $4/hour, CloudFormation about $0.40/month; pushed 2026-03-12 | Your AWS account | Own AWS account (bill risk) | L2–L3 | 36, 37 |
| **AWSGoat** · [github.com/ine-labs/AWSGoat](https://github.com/ine-labs/AWSGoat) | Serverless blog and ECS app with XSS, SQLi, IDOR, SSRF, S3, IAM escalation, ECS breakout | Free inside the free tier, then $0.0125/h and $0.0505/h in us-east-1 ([README](https://raw.githubusercontent.com/ine-labs/AWSGoat/master/README.md)); pushed 2026-11-04 | Admin-level keys | Own AWS account (bill risk) | L2–L3 | 37, 35 |
| **Thunder CTF** · [thunder-ctf.cloud](https://thunder-ctf.cloud/) | Six GCP misconfiguration levels played from Cloud Shell | Free OSS; "most resource use [fits] in GCP's free tier"; pushed 2025-06-25 | GCP account with billing enabled | Own GCP project (bill risk) | L2 | 37, 36 |
| **Stratus Red Team** · [github.com/DataDog/stratus-red-team](https://github.com/DataDog/stratus-red-team) | Emulated cloud attack techniques to test your detections | Free OSS; pushed 2026-11-04 (metadata only) | None | Own cloud account (bill risk) | L2–L4 | 37, 39, 48 |
| **TerraGoat** · [github.com/bridgecrewio/terragoat](https://github.com/bridgecrewio/terragoat) | Vulnerable-by-design Terraform | Free OSS; pushed 2025-07-13 (metadata only) | None | Scan in a codespace; deploying uses your own account | L2–L4 | 37, 50 |
| **GitHub Actions Goat** · [github.com/step-security/github-actions-goat](https://github.com/step-security/github-actions-goat) | CI supply-chain hardening: egress filtering, tamper detection, audit logs, long-lived credentials, untrusted actions, self-hosted ARC runners | Free OSS; pushed 2026-10-30 | GitHub account (fork) | GitHub-hosted runners in your fork; no cloud bill | L2–L3 | 47, 37 |

### Throwaway-VM labs: several security goats have not moved since 2024 (module 54 §2, §4, §5, §8, §11)

Run these only in a throwaway VM or codespace. Google Cloud Shell, with 5 GB of persistent storage and a 60-hour weekly limit, is a second browser-based option, listed in free-for-dev ([free-for-dev](https://github.com/ripienaar/free-for-dev)). The stale ones may need fixes before they start. That is break-fix practice in itself, but only inside the VM. Protohackers, Hackattic's server tasks and the Hurricane Electric certification need a server reachable from the internet, so use a short-lived cloud VM with key-only SSH and delete it the same day. The ControlPlane Kubernetes simulator (last push 2024-09-02) was checked only through repo metadata, so where it deploys is unknown ([GitHub API](https://api.github.com/repos/controlplaneio/simulator)).

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **CI/CD Goat** · [github.com/cider-security-research/cicd-goat](https://github.com/cider-security-research/cicd-goat) | 11 challenges on the OWASP Top 10 CI/CD risks across Gitea, Jenkins, GitLab plus runner, LocalStack and a "prod" box | Free, Apache-2.0; last push 2024-07-14, stale ([GitHub API](https://api.github.com/repos/cider-security-research/cicd-goat)) | None | Throwaway VM via `docker compose`; unverified whether a 2-core codespace has enough RAM for GitLab | L2–L3 | 47, 37 |
| **Kube Security Lab** · [github.com/raesene/kube_security_lab](https://github.com/raesene/kube_security_lab) | 14 vulnerable clusters built with Docker, Ansible and kind, with walkthroughs | Free (no licence listed); pushed 2026-03-19 | None | Throwaway VM | L2–L3 | 46, 37 |
| **Bust-a-Kube** · [bustakube.com](https://www.bustakube.com/) | An intentionally vulnerable three-node Kubernetes cluster with an answer key | Price not stated; "July20" build, year unknown ([download](https://www.bustakube.com/download)) | None seen | Three VM images (OVA or qcow2) on a throwaway hypervisor | L2–L3 | 37, 46 |
| **Dockerlings** · [github.com/furkan/dockerlings](https://github.com/furkan/dockerlings) | Bite-sized Docker exercises in the terminal | Free, MIT; pushed 2026-10-30 | None | Codespace or throwaway VM | L0–L1 | 30 |
| **Docker katas** · [github.com/eficode-academy/docker-katas](https://github.com/eficode-academy/docker-katas) | Docker from hello-world to deploying a web app | Free, MIT; pushed 2026-09-11 | None | Codespace or throwaway VM | L0–L1 | 30 |
| **bashcrawl** · [gitlab.com/slackermedia/bashcrawl](https://gitlab.com/slackermedia/bashcrawl) | Linux commands as a text adventure | Free, GPLv3; last activity 2026-06-09 | None | Codespace or throwaway VM | L0–L1 | 27 |
| **learnbyexample TUI-apps** · [github.com/learnbyexample/TUI-apps](https://github.com/learnbyexample/TUI-apps) | 70+ text-processing, 50+ grep, 50+ sed and 80+ awk exercises | Free, MIT; pushed 2026-02-02 | None | Codespace or throwaway VM | L1–L2 | 27 |
| **PSKoans** · [github.com/vexx32/PSKoans](https://github.com/vexx32/PSKoans) | 635 PowerShell koans: make failing Pester tests pass | Free, GPL-3.0; pushed 2026-10-03; README gives two different Pester versions | None | Throwaway VM with PowerShell 5.1 or 6+ | L1–L2 | 17 |
| **Kathará** · [kathara.org](https://www.kathara.org/) | Container-based network emulation with a lab-scenario collection | Free, open source | None | Throwaway VM (Docker or Kubernetes backend) | L2–L3 | 28 |
| **Cisco Modeling Labs Free 2.10** · [developer.cisco.com](https://developer.cisco.com/docs/modeling-labs/cml-free/) | IOL, IOL-L2 and ASAv routing and switching with Linux hosts | "No-cost, single-user", 5 running nodes, no time limit; telemetry always on | Cisco.com account to download | Bare metal or VMware OVA; heavier than a normal VM | L2–L3 | 28 |
| **SEED Labs** · [seedsecuritylabs.org](https://seedsecuritylabs.org/) | 13 networking labs: spoofing, ARP poisoning, TCP attacks, DNS rebinding and DNSSEC, firewalls, VPN, BGP, Heartbleed ([networking set](https://seedsecuritylabs.org/Labs_20.04/Networking/)) | Free, open source; setup page not read | None | Throwaway VM | L2–L3 | 28, 42, 37 |
| **Practical Packet Analysis captures** · [github.com/chrissanders/packets](https://github.com/chrissanders/packets) | Training-style packet captures | Free (no licence); static since 2018 | None | Wireshark inside a VM | L1–L2 | 42 |
| **Hackattic** · [hackattic.com](https://hackattic.com/) | 17 hard tasks: a TLS certificate to spec, a DNS server to spec, "be the registry", a database restore, Git hosting ([challenges](https://hackattic.com/challenges)) | No price; donations | Optional; API `access_token` to solve | Your code in a throwaway VM; some tasks need a reachable server | L2–L3 | 29, 42, 44 |
| **Protohackers** · [protohackers.com](https://protohackers.com/problems) | 12 TCP/UDP server problems, up to a man-in-the-middle proxy and a reliable protocol over UDP | No price stated; anonymous checks allowed; unconfirmed whether submissions still open | Optional | Short-lived cloud VM with a public port (small bill risk) | L2–L4 | 28 |
| **HE IPv6 Certification** · [ipv6.he.net/certification](https://ipv6.he.net/certification/) | Prove IPv6 connectivity, web server, mail, forward and reverse DNS and IPv6 name servers | "Free IPv6 certification service" | Registration | Your own domain plus an internet-reachable IPv6 host (short-lived cloud VM) | L2–L3 | 28, 42 |

### Networking, TLS and web-server drills fill modules 17, 28, 29 and 42 (module 54 §4)

Module 54 already has Mess With DNS, badssl.com and the wizard zines nginx playground. The new finds add reasoning practice (the debugging mysteries), byte-level TLS, and rule testers for nginx and Apache. Under The Wire plus PSKoans would give the Windows module (17) its first free PowerShell practice. Of the new finds in this area, only the mysteries and Under The Wire are true "something is broken, find out why" exercises. The rest are drills, testers and labs.

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **Wizard Zines debugging mysteries** · [mysteries.wizardzines.com](https://mysteries.wizardzines.com/) | Five branching stories (slow websites, connection timeout, a DNS update that didn't work, a 50 ms request, a failed Docker connection) where you choose curl, tcpdump or iptables checks ([example](https://mysteries.wizardzines.com/connection-timeout.html)) | Free; static (source last pushed 2023) | None | Browser, no real terminal | L1–L2 | 42, 25 |
| **Wizard Zines questions** · [questions.wizardzines.com](https://questions.wizardzines.com/) | ~10-minute quizzes on TLS certificates, HTTP headers and status codes, CORS, CDNs, TCP, UDP, DNS records, Unix permissions, signals | Free | None | Browser | L0–L1 | 27, 28 |
| **The Illustrated TLS 1.3 Connection** · [tls13.xargs.org](https://tls13.xargs.org/) | Every byte of a TLS 1.3 session with commands to reproduce it; sibling pages for TLS 1.2, DTLS and QUIC | Free, MIT; pushed 2026-01-07 | None | Browser; reproduce in a VM | L2–L3 | 42 |
| **RouterJockey trainers** · [routerjockey.com/training-tools](https://routerjockey.com/training-tools/) | IPv4 and nibble-level IPv6 subnet drills, binary and hex trainers | Free; published 23 Jul 2026 | No account | Browser, no backend | L0–L1 | 28 |
| **Subnetting Challenge** · [learnnetworking.itch.io/subnetting-challenge](https://learnnetworking.itch.io/subnetting-challenge) | Timed IPv4, IPv6, binary and VLSM rounds with a leaderboard | Free (donate link) | Not mentioned | Browser | L0–L1 | 28 |
| **Nginx location match tester** · [nginx.viraptor.info](https://nginx.viraptor.info/) | Which `location` block nginx picks for a URL | Free; no sub-locations or listen ports | None | Browser | L1–L2 | 29 |
| **htaccess tester** · [htaccess.madewithlove.com](https://htaccess.madewithlove.com/) | How Apache rewrite rules transform a URL before you deploy | "Free developer tool" | No account | Browser | L1–L2 | 29 |
| **MDN HTTP Observatory** · [developer.mozilla.org/en-US/observatory](https://developer.mozilla.org/en-US/observatory) | Security headers and the HTTP-to-HTTPS redirect of your own public site | Free; one rescan per 60 s; scan history is public; TLS tests removed ([FAQ](https://developer.mozilla.org/en-US/observatory/docs/faq)) | None | Browser | L1–L2 | 29, 37 |
| **Cisco DevNet Sandboxes** · [developer.cisco.com/site/sandbox](https://developer.cisco.com/site/sandbox/) | Real Cisco gear: always-on, or reserved for up to 7 days | "Free, in your browser, on real Cisco gear" | Not stated | Vendor lab | L2–L3 | 28 |
| **Juniper vLabs** · [jlabs.juniper.net/vlabs](https://jlabs.juniper.net/vlabs/) | Pre-built vMX, vSRX, Apstra, SRv6 and BGP topologies | "All for free!" | Sign-up to reserve | Vendor lab | L2–L3 | 28 |
| **Under The Wire** · [underthewire.tech](https://underthewire.tech/) | PowerShell wargames over SSH (Century, Cyborg, Groot, Oracle, Trebek); Oracle covers the registry and DNS zone records ([write-up](https://narrowtomato.github.io/writeups/underthewire/oracle.html)) | Free per player blogs; current levels unreadable (JS app) | First credentials via the project's Slack, per a 2021 blog ([SQLServerCentral](https://www.sqlservercentral.com/blogs/powershell-practice-with-a-war-game)) | SSH to their hosts, no install | L1–L2 | 17 |

### Games: 62 DevOps Daily simulators and a wave of autumn on-call games (module 54 §10)

DevOps Daily's games page is the biggest single DevOps-specific gap. It has 62 simulators covering nearly every handbook topic with no sign-up seen, but they are simulations. They belong at L0–L2 next to SysAdmin Simulator, not next to SadServers. Server Survival and K8s Games are the closest thing to a free chaos-engineering game. The researchers found no maintained standalone browser chaos game, because real chaos tools need a platform or an account. The on-call games are weeks old: ON-CALL's repository was created on 18 Oct 2026 and Pit Wall's on 27 Sep 2026, so label them "new in 2026, may change". **The Incident Challenge is the only one built as a real investigation.** System Design Sim updates the monthly bill on real AWS, Azure and GCP prices as you build, which makes it a cheap way to build cost intuition before a migration. Mechanical Rock's devops.games still offers only DevOps Dream, and its linked WayFinder is a sign-up benchmarking product, not a game ([devops.games](https://devops.games/)).

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **DevOps Daily games** · [devops-daily.com/games](https://devops-daily.com/games) | Kubernetes RBAC, CNI, scheduler and terminal; Docker terminal; GitOps and deployment strategies; Terraform basics and state puzzles; Incident Commander; a daily on-call incident; PromQL; DNS, TCP/UDP, TLS and AWS VPC | Free to open; an unexplained "Pro" area; repo pushed 2026-11-07 ([GitHub API](https://api.github.com/repos/The-DevOps-Daily/devops-daily)) | No sign-up seen | Browser (simulated) | L0–L2 | 31, 33, 32, 28 |
| **K8s Games** · [k8sgames.com](https://k8sgames.com/) | 3D cluster simulator: 20-level campaign, Chaos Mode, 10 timed outage challenges, scored sandbox, `kubectl` bar, YAML export | Free, Apache-2.0; 1,458 stars; pushed 2026-04-28 | "No install, no signup" ([README](https://github.com/rohitg00/k8sgames)) | Browser | L0–L2 | 31, 26, 46 |
| **Server Survival** · [pshenok.github.io/server-survival](https://pshenok.github.io/server-survival/) | Cloud-architecture tower defence: WAF, load balancers, queues, caches, replicas and GeoDNS against traffic and DDoS waves on a budget | Free, MIT; 6,479 stars; pushed 2026-11-04 ([GitHub](https://github.com/pshenok/server-survival)); use this original, not the copies | No account | Browser | L1–L3 | 39, 23 |
| **SDPD** · [sdpd.live](https://sdpd.live/) | Diagnose 33 distributed-system failures (split brain, stale reads, thundering herd, hot partitions); chaos simulator | Free, MIT | None | Browser | L2–L3 | 39, 40 |
| **SystemLore** · [systemlore.com](https://systemlore.com/) | Five-minute runs keeping services alive through spikes, outages and failover, each ending in a post-mortem | Free; owner, licence and pricing unknown | "No signup needed" | Browser | L1–L3 | 39, 23 |
| **System Design Sim** · [systemdesignsim.com/playground](https://systemdesignsim.com/playground) | Build on real AWS, Azure or GCP sizes while p99, errors and the monthly bill update; flash-sale challenges up to 20,000 req/s | Free; "Practice stays free either way" ([about](https://systemdesignsim.com/about)) | No account | Browser | L2–L4 | 39, 23 |
| **StackMonkey** · [stackmonkey.dev](https://stackmonkey.dev/) | Live traffic, queues and retry storms; names the component that fails first | "Free to use · No credit card"; licence unconfirmed | None stated | Browser | L2–L4 | 39 |
| **The CTO Game** · [thectogame.com](https://thectogame.com/) | Architecture decisions trading scalability, velocity and tech debt | Free to load; depth and account unverified | Unverified | Browser | L3–L4 | 40, 39 |
| **ON-CALL** · [oncall-simulator.vercel.app](https://oncall-simulator.vercel.app/) | Six incidents in one night with error budget and blast radius; symptom-only fixes return one severity higher; graded postmortem | "Free, no signup"; 0 stars, created 18 Oct 2026 ([GitHub](https://github.com/kanishk-sachdeva/oncall-simulator)) | None | Browser | L1–L2 | 25, 52 |
| **Pit Wall On-Call** · [pitwall.rafifdzaky.com](https://pitwall.rafifdzaky.com/) | A daily real-time incident: acknowledge, read alerts, metrics and logs, find the real cause | Free, AGPL-3.0; needs a 1024 px screen ([GitHub](https://github.com/rafifdzaky27/pit-wall-on-call)) | None seen | Browser | L1–L3 | 25 |
| **non-call** · [serum.sh/non-call](https://serum.sh/non-call/) | A terminal-style on-call night of competing alerts and interruptions until the 07:00 hand-off | Free; Show HN on 21 Oct 2026 ([HN](https://hn.algolia.com/api/v1/search?query=on-call%20game&tags=show_hn)) | None seen | Browser | L1–L3 | 25, 52 |
| **The Incident Challenge** · [theincidentchallenge.com](https://theincidentchallenge.com/) | Live rounds every other Monday (24-hour window): compare staging with production logs, requests, services and config; ranked by solve time | No price shown; reports "400+ engineers, 36 countries, 20% success rate"; next round 9 Nov 2026 13:00 UTC | Google or LinkedIn sign-in, even for the demo ([demo](https://challenge.theincidentchallenge.com/#/demo)) | Browser | L2–L4 | 25, 23 |
| **TWiG Online** · [analytics.actionableagile.com/twig](https://analytics.actionableagile.com/twig/index.html) | A flow simulation of a pull system with WIP limits, plus flow-metric charts | "It's free to play!" ([ActionableAgile](https://actionableagile.com/play-twig/)) | No login | Browser plus facilitator PDFs | L2–L4 | 39, 40, 33 |
| **Featureban** · [agendashift.com/resources/featureban](https://www.agendashift.com/resources/featureban) | Classic kanban simulation; free online version at [FlowFast](https://tools.flowfast.io/featureban/) | Free, CC BY-SA 4.0 | Online sign-up flow unchecked | Browser, or paper and cards | L1–L4 | 39 |

### Drill kits and incident libraries give L3–L4 leads ready-made game days (module 54 §10)

These pair with Wheel of Misfortune and the game day in module 33 §8. PagerDuty's open material is the one to adopt first. It is maintained (repositories pushed 30 Oct 2026) and it defines the incident roles the handbook's L3 and L4 exit tests assume ([PagerDuty IR docs](https://github.com/PagerDuty/incident-response-docs)). For L4 reading, Lorin Hochstein's resilience-engineering list was pushed on 31 Oct 2026 ([GitHub](https://github.com/lorin/resilience-engineering)).

| Site and URL | What you practise | Free vs limits | Sign-up / card | Runs where | Level (est.) | Module |
|---|---|---|---|---|---|---|
| **PagerDuty Incident Response** · [response.pagerduty.com](https://response.pagerduty.com/) | Role guides for incident commander, deputy, scribe, SME and liaisons; severity levels; postmortem template; an open-source 2018 course with slides ([course](https://response.pagerduty.com/training/courses/incident_response/)) | Free | None | Docs | L1–L4 | 52, 33, 25, 40 |
| **Deployments and Disasters** · [antolius.github.io/deployments-and-disasters](https://antolius.github.io/deployments-and-disasters/) | A tabletop role-playing game for incident management, with hosting rules | Free (CC0); "still in development", last push 2022 | None | Read online | L2–L4 | 33 |
| **Twilio GameDay template** · [github.com/twilio/gameday](https://github.com/twilio/gameday) | Game-day plan: service context, customer impact, SLOs and SLIs, checklists, roles | Free, MIT; last push 2020 | None | Markdown | L2–L4 | 33 |
| **Equal Experts Chaos Day Playbook** · [playbooks.equalexperts.com/chaos-day-playbook](https://playbooks.equalexperts.com/chaos-day-playbook) | Designing and running a Chaos Day | Free, PDF; "Last updated 2 years ago" | None | Web and PDF | L3–L4 | 33 |
| **Rolls & Responders** · [ncsc.govt.nz](https://www.ncsc.govt.nz/protect-your-organisation/rolls-and-responders/) | NCSC New Zealand's open-source security incident tabletop kit | Free downloads | None | Documents | L2–L4 | 37, 48 |
| **Oh Noes!** · [expel.com/oh-noes-cybersecurity-tabletop](https://expel.com/oh-noes-cybersecurity-tabletop/) | A tabletop game in the style of Dungeons & Dragons for a team run-through of a cyberattack, "under 2 hours. No facilitator required" | Free ZIP kit | None | Documents | L2–L4 | 37, 48 |
| **Defensomania** · [karneades.github.io/Defensomania/play](https://karneades.github.io/Defensomania/play/) | Incident-response card game with a free online dealer | Free, MIT; pushed 6 Nov 2026 ([GitHub](https://github.com/Karneades/Defensomania)) | None | Browser | L2–L4 | 37, 48 |
| **The VOID** · [thevoid.community](https://www.thevoid.community/) | Search "over 10,000" incident reports by impact type ([database](https://www.thevoid.community/database)) | Free to browse | None | Browser | L2–L4 | 39 |
| **Failure Modes** · [failuremodes.dev](https://failuremodes.dev/) | Practitioner failure stories; invite-only meetups in Bangalore and Pune | Free | None | Browser | L1–L4 | 39 |
| **Postmortem Index** · [postmortems.app](https://postmortems.app/) | 242 postmortems in 8 categories, a filterable view of Dan Luu's list (already in module 54) | Free; pushed 5 Nov 2026 | None | Browser | L1–L4 | 39 |
| **How They SRE** · [github.com/upgundecha/howtheysre](https://github.com/upgundecha/howtheysre) | How real organisations run SRE | Free; 9,833 stars; pushed 30 Sep 2026 | None | GitHub list | L3–L4 | 39 |

## Two module-54 links went dark; the rest mostly held

About 40 of the 80 module-54 entries were re-tested on 7 Nov 2026. The one serious finding is the **Wiz outage**. The domains eksclustergames.com and bigiamchallenge.com, both in module 54, and k8slanparty.com, not in it, return NOERROR with no A, AAAA or CNAME records. Their Route 53 zones still exist ([dns.google, Big IAM](https://dns.google/resolve?name=bigiamchallenge.com&type=A); [dns.google, LAN Party](https://dns.google/resolve?name=k8slanparty.com&type=A)). Two pieces of evidence contradict a retirement. Wiz's own CTF hub still shows "Start challenge" buttons for all three ([wiz.io/ctf](https://www.wiz.io/ctf)), and Wiz wrote in 2025 that its earlier CTFs are "always available for people to play" ([Wiz blog](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges)). No shutdown notice was found, and one day's DNS check cannot rule out a temporary change. The right label is therefore **"unreachable on 7 Nov 2026, re-check before retiring"**. Meanwhile cloudsecuritychampionship.com and cloudhuntinggames.com resolve and load.

| Module-54 entry (where it appears) | What the 7 Nov 2026 check found | Suggested edit |
|---|---|---|
| **EKS Cluster Games** (§6 table) | Apex and `www` have no address records; the fetch fails with ENOTFOUND ([dns.google](https://dns.google/resolve?name=www.eksclustergames.com&type=A)) | Mark "unreachable on 7 Nov 2026, re-check before retiring"; point to Wiz CSC "Game of Pods" meanwhile |
| **The Big IAM Challenge** (§7 table, free-only path and best picks; §14 Senior plan; §15 row 36) | No apex A record; `www` returns NXDOMAIN ([dns.google](https://dns.google/resolve?name=www.bigiamchallenge.com&type=A)) | Same label in all five places; meanwhile practise IAM policy reading on Pwned Labs' free labs or IAM Vulnerable in a credit-capped account |
| **AWS Cloud Quest** (§7, §15 row 36) | The linked docs page now only says it "has moved to AWS Skill Builder" and links skillbuilder.aws/cloudquest ([docs](https://docs.cloudquest.skillbuilder.aws/coming-soon/index.html)). The product page says free accounts get "limited access" and all roles need a subscription ([AWS](https://aws.amazon.com/training/digital/aws-cloud-quest/)). That contradicts the handbook's two free roles, although a search snippet still says two roles are free | Relink to https://skillbuilder.aws/cloudquest; re-check the free roles while signed in |
| **AWS Workshops** (§7 table; §0 "hidden cost") | Since 8 Jul 2026 a free, ready-made account for selected workshops: no AWS account or card, 8 hours, one per week, resets Sunday, ready in about 15 min ([AWS What's New](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/)). The launch set included Bedrock and AI workshops ([InfoQ](https://infoq.com/news/2026/08/aws-builder-sandbox)); the current list was not opened | Change "AWS usage is billed" to "free 8-hour sandbox for selected workshops, otherwise billed" |
| **SadServers** (§1) | More detail, no change in status. The pricing page, dated 4 Nov 2026, shows the same Pro price of $9/month or $72/year and a free tier of "a selection of scenarios with daily limits" ([pricing](https://sadservers.com/pricing)). At least 57 of the 96 scenarios listed are free. Prometheus scrape, Ingress-NGINX to Traefik ("Lyon"), BuildKit, Podman and Jenkins scenarios are Pro-only ([scenarios](https://sadservers.com/scenarios)). The daily limit is not published | Name the free Traefik, Docker and Kubernetes scenarios in §1, and add "San Juan" to §15 rows 43 and 45 as the nearest Dokploy-style drill |
| **Backdoors & Breaches** (§10, §15 row 48) | The old URL redirects to /tools/backdoorsandbreaches/ ([BHIS](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/)) | Update the link |
| **Wheel of Misfortune** (§10) | The github.io tool works; the repo's homepage field now points to dastergon.gr, which returns 404 ([GitHub](https://github.com/dastergon/wheel-of-misfortune)) | Keep the github.io link |
| **Microsoft Learn sandboxes** (§16) | Already marked retired; the FAQ (updated 29 Jul 2026) confirms and points to a trial or pay-as-you-go ([FAQ](https://learn.microsoft.com/en-us/training/support/faq?pivots=sandbox)) | Add Applied Skills labs (and Azure for Students, for students) to "Use instead" |
| **YouBrokeProd** (§16) | Still "Back Online Soon" ([site](https://youbrokeprod.com/)) | No change |
| **LocalStack, Google Skills, Red Hat interactive labs** (§7, §8, §16) | Unchanged. LocalStack's Hobby plan needs an account and token, and the Community emulator gets no updates ([pricing](https://www.localstack.cloud/pricing)). Google's April 2026 Arcade changes match the handbook ([forum](https://discuss.google.dev/t/what-s-changing-in-the-google-skills-arcade-from-april-2026/345557)). Red Hat lists 14 no-cost Ansible labs, including Event-Driven Ansible ([labs](https://www.redhat.com/en/interactive-labs/ansible)) | None |
| **Play with Docker, Play with Kubernetes** (§16) | Both hosts return HTTP 200; content not checked | Keep them retired; an HTTP 200 is not a revival |

These sites returned HTTP 200 on 7 Nov 2026 in the researchers' checks:

- [Killercoda](https://killercoda.com/), [iximiuz Labs](https://labs.iximiuz.com/) and [KodeKloud Engineer](https://engineer.kodekloud.com/)
- [DockerLabs](https://dockerlabs.collabnix.com/), the [Network Policy Editor](https://editor.networkpolicy.io/) and [Kubernetes Goat](https://madhuakula.com/kubernetes-goat/)
- PromLens and the PromLabs demo, [Grafana Play](https://play.grafana.org/) and [k8s.af](https://k8s.af/)
- [Oh My Git!](https://ohmygit.org/) and Git Exercises
- [devops.games](https://devops.games/), dream.devops.games and the DORA Quick Check
- SysAdmin Simulator, Uptime Labs, LetsDefend and Blue Team Labs Online

flaws.cloud, flaws2.cloud and cloudresumechallenge.dev still resolve in DNS, and CloudGoat was pushed on 2026-10-14 ([GitHub](https://github.com/RhinoSecurityLabs/cloudgoat)).

These were not re-tested and should be checked in the next quarterly pass:

- killer.sh, CodeCrafters, LabEx, roadmap.sh and KodeKloud's free-course pages
- the GitHub repositories (Kubernetes the Hard Way, devops-exercises, 90DaysOfDevOps, CKAD exercises)
- the HashiCorp, GitLab and GitHub docs, the OpenTelemetry demo, the Wazuh guide and Juice Shop
- most of the Linux, networking and SQL entries in §2, §4 and §12
- the HTB Academy pricing change and the LetsDefend acquisition (only their HTTP status was checked)

## Four niche lists beat the giant awesome-lists

The well-known general lists are maintained but useless for this job. free-for-dev (142k stars) catalogues free-tier infrastructure, and awesome-sysadmin catalogues software; neither catalogues practice platforms. **The productive sources are short, focused lists**, which also added the newest DevOps browser tools (DevOps Daily, SudoRank, DevOpsLesson, Dockerlings). Even good lists keep dead entries. awesome-docker still lists Play With Docker, which shut down on 1 March 2026. awesome-kubernetes still lists Play with Kubernetes and YouBrokeProd. Awesome-CloudSec-Labs carries malformed Wiz links. So treat every list entry as a lead to verify, not as evidence. Show HN launches, searched through the HN Algolia API, surfaced Server Survival, non-call and The CTO Game before any list did ([HN Algolia](https://hn.algolia.com/api/v1/search?query=tower%20defense%20cloud)).

| Catalog | Stars · last push (7 Nov 2026) | What to mine | Verdict |
|---|---|---|---|
| [zardus/wargame-nexus](https://github.com/zardus/wargame-nexus) | 1,360 · 2026-10-25 | Cloud, Blue Team/DFIR and "Not Security" sections (CMD Challenge, SadServers, UnderTheWire, Protohackers); badges for offline, "heartbeat failed" and dead sites | Best liveness tracker; leans towards security |
| [iknowjason/Awesome-CloudSec-Labs](https://github.com/iknowjason/Awesome-CloudSec-Labs) | 2,210 · 2025-10-01 | AWS, Azure, GCP, Kubernetes, container, Terraform, CI/CD and PaaS labs, each tagged hosted or self-hosted | Best cloud-security catalog, but no push in 13 months |
| [veggiemonk/awesome-docker](https://github.com/veggiemonk/awesome-docker) "Where to Start" | 37,190 · 2026-11-04 | Docker katas, DevOps Daily's Docker simulator, Dockerlings | Good; still lists Play With Docker |
| [ramitsurana/awesome-kubernetes](https://github.com/ramitsurana/awesome-kubernetes/blob/master/docs/learning-resources/interactive-environments.md) interactive environments | 16,139 · 2026-10-31 | Meshery Playground, SudoRank, DevOpsLesson | Good; still lists dead and offline sites |
| [joe-shenouda/awesome-cyber-skills](https://github.com/joe-shenouda/awesome-cyber-skills) | 4,781 · 2026-09-17 | 120 entries with a category column (Cloud, System/Network, Blue Team) | Useful; many old VMs |
| [magnologan/awesome-k8s-security](https://github.com/magnologan/awesome-k8s-security) | 2,008 · 2026-11-06 | "Trainings" and "Learning" sections | Active; links dead brands (Katacoda, Linux Academy) |
| [networktocode/awesome-network-automation](https://github.com/networktocode/awesome-network-automation) | 2,882 · 2026-11-04 | Emulators and simulators (netlab, Batfish, Containerlab) | Tools, no hosted sandboxes |
| [michelpereira/awesome-games-of-coding](https://github.com/michelpereira/awesome-games-of-coding) | 2,169 · 2026-09-23 | DevOps game entries | All already in module 54 |
| [ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev) | 142,131 · 2026-11-06 | Free browser shells such as Google Cloud Shell | Infrastructure, not practice |
| [wmariuss/awesome-devops](https://github.com/wmariuss/awesome-devops), [awesome-sysadmin](https://github.com/awesome-foss/awesome-sysadmin) | 4,448 · 2026-11-07; 35,622 · 2026-10-22 | One hands-on entry (Meshery); software only | Not worth mining |
| [dastergon/awesome-sre](https://github.com/dastergon/awesome-sre) | 13,757 · 2025-08-28 | Education section | Stale |
| [apsdehal/awesome-ctf](https://github.com/apsdehal/awesome-ctf), devsecops/awesome-devsecops | 11,974 · 2024-07-22; 5,512 · 2024-05-11 | — | Stale; use wargame-nexus |
| [DevOpsCube: 8 Best Websites To Practice DevOps Scenarios](https://devopscube.com/websites-to-practice-devops/) | dated 15 Feb 2026 | Free-tier limits for Killercoda (about 1 h a session), iximiuz (about 1 h a day), SadServers, prepare.sh | Best non-GitHub roundup |
| [iximiuz: Learn-by-Doing Platforms](https://iximiuz.com/en/posts/learn-by-doing-platforms/) | updated Jan 2022 | — | Stale; still lists Katacoda |

Among cloud-security lists, 4ndersonLin/awesome-cloud-security (2,517 stars, last push March 2026) is slowing, and teamssix and Metarget stopped in 2024 and 2023 ([GitHub search](https://api.github.com/search/repositories?q=awesome+cloud+security+in:name&sort=stars&per_page=6)). For flow and kanban games, Kirill Klimov's index dates from October 2022 ([list](https://kirillklimov.com/kanban-games/)).

## Dead, hijacked or paid: leave these out

| Site | Finding on 7 Nov 2026 |
|---|---|
| The Unix Game (`unixgame.io`) | **Dead, do not link**: it redirects (301) to an unrelated gambling domain |
| K8s LAN Party (Wiz; not in module 54) | Same DNS outage as EKS Cluster Games: unreachable on 7 Nov 2026, re-check before adding |
| contained.af (old container-escape game) | NXDOMAIN ([dns.google](https://dns.google/resolve?name=contained.af&type=A)) |
| Netsim, Deadlock OS, WebTerm Learn, Cisco Binary Game | Connection refused, 404, 403, and a broken CSS loader respectively ([Netsim repo](https://api.github.com/repos/errorinn/netsim)) |
| LF "Introduction to GitOps (LFS169)" | "No longer available" ([LF](https://training.linuxfoundation.org/training/introduction-to-gitops-lfs169/)) |
| Codefresh "GitOps with Argo" certification | Now at Octopus behind a login and a paid bundle ([Octopus](https://learning.octopus.com/)) |
| WrongSecrets Render mirror | HTTP 503 ([mirror](https://wrongsecrets.onrender.com/)); use the Heroku instance |
| Sadcloud, AzureGoat, GCPGoat | Stale (last pushes 2023 and October 2024) |
| CyberDefenders | No free plan; CyberRange costs $25/month ([pricing](https://cyberdefenders.org/pricing/)) |
| AWS Jam | Free accounts get "limited access"; Jam Events need a Team subscription ([AWS Jam](https://aws.amazon.com/training/digital/aws-jam/)) |

These were paid or could not be checked:

- **Paid, skipped:** Pluralsight and A Cloud Guru break-fix labs, QA's FinOps SimuLab, Tetrate Service Bridge ($499), Root-Me PRO and HackerDNA Pro.
- **No public pricing:** PacketSafari.
- **Unverifiable:** the Datadog Learning Center (HTTP 403), LabEx's free labs (pricing page 403), and three flow games that may be paid (G2G3's Phoenix Project simulation, Okaloa Flowlab, getKanban).

Seven sites the 3 Oct 2026 pass excluded in the local catalog `research/practice.json` stay excluded: HackerRank Linux Shell, Linux Survival, RegexOne, SubnetIPv4, internet.nl, CyberDefenders and Malware-Traffic-Analysis.

## The holes no free site fills yet

**Dokploy and Docker Swarm have no free break-fix lab anywhere.** The nearest stand-ins are SadServers' "San Juan" (Traefik with Docker Compose), the iximiuz Swarm playground already in module 54, and the Harbor demo. **Cloud break-fix is the other hole.** AWS Jam is paywalled. The do-it-yourself routes need your own account: an AWS Builder Center article gives 10 beginner scenarios you break yourself ([builder.aws.com, snippet](https://builder.aws.com/content/3KHK3QXbPa3vM0TZQeC1XJo0QJy/i-broke-aws-on-purpose-troubleshooting-scenarios-every-beginner-should-try)), and re:Invent's NET302 "We break it, you fix it" workshop has a template that a write-up says deletes the default VPCs in every region ([Classmethod, snippet](https://dev.classmethod.jp/articles/reinvent2023-network-troubleshooting-net302-eng/)). Use NET302 only in a dedicated account.

The sweep found nothing usable in five more areas:

- **FinOps:** no free FinOps game with verified availability. The FinOps Foundation board game is CC BY 4.0 but its page has a purchase link ([finops.org, snippet](https://www.finops.org/game/)), and KodeKloud's "CloudBill" repo has 3 stars ([GitHub](https://github.com/kodekloudhub/finops-practitioner-)).
- **Flux, OpenTofu and Jenkins:** no free browser playground. Jenkins appears only inside CI/CD Goat and a paid SadServers scenario.
- **iptables and nftables:** no verified browser sandbox.
- **macOS:** nothing for module 20.
- **Chaos engineering:** no standalone free game.

Several details stayed unverified because nothing was signed in to:

- SadServers' exact daily limit
- Pwned Labs' and Cybr's free/paid split by cloud
- whether Microsoft officially calls Applied Skills free
- LiveLabs reservation terms
- whether the AWS Free plan needs a card
- the Isovalent form, and how Solo and Tetrate deliver their labs
- the Wiz price and sign-up terms
- Under The Wire's Slack requirement
- SudoRank's tiers (aggregator only) and prepare.sh's contradictory free tier
- session limits on tmpfs.tech and Meshery
- whether Protohackers still accepts submissions

Levels and module fits throughout are the researchers' judgement, and no game was played end to end, so scenario accuracy is unassessed.

## Conclusion

For this user's move to cloud, the deciding question is not price, since nearly everything here is free. It is **who owns the account**. In 2026 free cloud practice shifted towards accounts the vendor owns, which cannot bill you: AWS's Builder Center sandbox arrived in July, and Pwned Labs and Cybr give away real-account labs. Microsoft went the other way and removed Learn sandboxes. Module 54 §7 could be reordered by bill risk instead of by brand: browser, then vendor account, then a credit-capped own account such as the AWS Free plan, then an ordinary own account. Under that order the own-account goats can be used safely only inside the capped account, which turns the existing "hidden cost" warning into a rule the tables enforce. The gaps point at an opportunity the handbook already describes in §17. No free site breaks Dokploy, Swarm or a cloud VPC for you, so the L4 skill of writing break scripts for others is also the cheapest way to cover the user's own stack.

The Wiz outage also changes how the quarterly re-check should work. Single-purpose CTF domains can go dark while the vendor's hub still advertises them, curated lists keep dead entries for months, and Play with Docker still answers HTTP 200 eight months after it shut down. A link check that stops at HTTP status will miss all three. The next pass should test DNS, read the page content, and record a dated "unreachable, re-check" state before anything moves to §16. The newest finds need the same care: some on-call games were weeks old with zero stars when checked. Give them a "new in 2026, may change" label and keep the main tables for long-lived options such as Server Survival, K8s Games, Linuxzoo and the vendor labs.
