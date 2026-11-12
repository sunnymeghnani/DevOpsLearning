# New free DevOps practice sites: containers, Kubernetes, GitOps, CI/CD, IaC, observability (checked 2026-11-07)

How things were checked (applies to every row below):
- **Opened** = page fetched and its content read on 2026-11-07.
- **HTTP-only** = the URL returned HTTP 200 to `curl -L` on 2026-11-07, but the content is a JavaScript app, so the fetch tool could not read it.
- **Snippet** = only a search-engine snippet was seen. The page itself was not opened.
- Repo freshness ("pushed", stars) comes from the public GitHub REST API (`api.github.com/repos/<owner>/<repo>`), queried 2026-11-07.
- Nothing was signed up for, logged into, submitted, downloaded or run. Self-hosted items are described from their READMEs only.
- Levels (L0 fresher .. L4 senior) and handbook-module fits are my own judgement (see Inferences), not claims made by the sites.

## Q1. Which new free sites exist in 2026 (not already in the handbook), and what do you practise on each?

### Takeaway
About 20 new, verified, free options fill real gaps in the handbook. The strongest break-fix finds are SadServers (free scenarios for Docker, K8s, Traefik, Helm, Envoy and Nginx in a browser terminal), the Wiz Cloud Security Championship (container-escape, K8s and Terraform CTFs, still playable), the Isovalent Cilium labs (the "Getting Started" lab ends with a fix-the-broken-HTTPRoute exam), OWASP WrongSecrets (hosted, no sign-up), and the CI/CD goats (Jenkins/GitLab/Gitea and GitHub Actions). The observability gap is filled by small browser playgrounds: the official Prometheus demo, the Grafana LogQL simulator, the Vector VRL playground and the OTTL playground.

### Cited Findings

**Break-fix / troubleshooting scenarios (browser)**
- **SadServers**: https://sadservers.com. "Hobbyist" plan costs $0 and needs an account. It gives "a selection of scenarios with daily limits". Pro costs $9/month or $72/year and gives 125+ scenarios and double the time limit. The pricing page shows a last update of 2026-11-04. — [SadServers pricing](https://sadservers.com/pricing)
- SadServers scenarios run on an ephemeral AWS EC2 VM reached through an in-browser terminal. Nothing is installed locally, free-tier VMs have no internet access (only a proxy serves the terminal), the VM is destroyed at the end, and sign-up is email/password or Google. No credit card is mentioned for the free tier. — [SadServers FAQ](https://sadservers.com/faq)
- Free (marked "Public" or "Email") SadServers scenarios relevant to the handbook: "Bilbao" Basic Kubernetes Problems (Easy), "Buenos Aires" Kubernetes Pod Crashing, "Bengaluru" Kubernetes StatefulSet, "Salta" Docker container won't start, "Quito" Control One Container from Another, "Helsingør" Postgres replication (Docker Compose), "San Juan" mucho Traefik (Docker Compose), "Kilifi" Helm, "Bangalore" Envoy Panics, "Cape Town" Borked Nginx, "Geneva" renew Nginx SSL cert, "Genova" cgroups problem, "Venice" Am I in a container? Among the paid-only ones: Prometheus can't scrape, Helm chart issue, Migrate Ingress-NGINX to Traefik, BuildKit mismatch, Docker→Podman, Jenkins. Of the 96 scenarios visible on the (truncated) list, about 57 are free. — [SadServers scenarios](https://sadservers.com/scenarios) (opened; page truncated at about 100k characters, so the counts are minimums)

**Security CTFs that are also K8s/container break-fix (browser)**
- **Wiz Cloud Security Championship**: https://cloudsecuritychampionship.com. A monthly CTF by Wiz Research with 12 challenges (Jun 2025 to May 2026). 11 of them are still listed as "Enter Challenge". One (Aug 2025, Azure AD) is "no longer running". Relevant ones: "Contain Me If You Can" (Jul 2025, container escape to the host filesystem), "Game of Pods" (Oct 2025, Kubernetes privilege escalation), "State of Affairs" (Dec 2025, Terraform automation), "Split Horizon" (Apr 2026, restricted Kubernetes lab). The page has Login/Register links. No price is shown. — [Cloud Security Championship](https://cloudsecuritychampionship.com/) (opened)
- Wiz's launch post (26 Jun 2025) says hints cost points and that Wiz's earlier CTFs are "always available for people to play". — [Wiz blog](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges). That claim is contradicted for K8s LAN Party and EKS Cluster Games by the DNS checks in Q4.
- Community write-ups confirm Game of Pods is about kubelet API access via the API-server `nodes/proxy` permission. — [kabinet write-up](https://kabinet.gitbook.io/ctf-writeup/2026/wiz-cloud-security-challenge/game-of-pods) (snippet)
- **OWASP WrongSecrets**: a hosted instance at https://wrongsecrets.herokuapp.com loads with no sign-up. It shows "Version: 1.14.2-no-vault" and 76 challenges (61 Docker, 6 K8s-only, 5 K8s+Vault, 4 cloud). — [WrongSecrets Heroku](https://wrongsecrets.herokuapp.com/) (opened)
- WrongSecrets teaches how secrets leak via code, configs, containers and cloud. It can also be run locally with `docker run ... jeroenwillemsen/wrongsecrets:latest-no-vault`, on minikube or Vault for the K8s challenges, or on AWS/GCP/Azure. The README warns that the cloud variants include IAM privilege-escalation and must never run in a production account. The Render.io instance is "experimental". — [GitHub OWASP/wrongsecrets](https://github.com/OWASP/wrongsecrets)
- WrongSecrets repo: 1,474 stars, last push 2026-11-02, not archived. — [GitHub API](https://api.github.com/repos/OWASP/wrongsecrets)
- The WrongSecrets Render mirror returned HTTP 503 on 2026-11-07 (curl check). Use the Heroku instance. — [wrongsecrets.onrender.com](https://wrongsecrets.onrender.com/)

**CI/CD security and break-fix**
- **CI/CD Goat** (Cider Security, now Palo Alto Networks): a deliberately vulnerable CI/CD environment with 11 challenges mapped to the OWASP Top 10 CI/CD risks, such as poisoned pipeline execution. It runs locally via `docker compose up -d` and contains Gitea, Jenkins plus agent, GitLab plus runner, CTFd, LocalStack, and a Docker-in-Docker "prod" box. Setup can take up to 5 minutes. — [GitHub cicd-goat](https://github.com/cider-security-research/cicd-goat)
- CI/CD Goat repo: 2,334 stars, last push 2024-07-14, not archived. It is unmaintained for more than 2 years but still published. — [GitHub API](https://api.github.com/repos/cider-security-research/cicd-goat)
- **GitHub Actions Goat** (StepSecurity): fork the repo, enable Actions on the fork, then follow tutorials on egress filtering, file-tampering detection, audit logs, long-lived credentials and untrusted third-party actions. It covers GitHub-hosted runners and self-hosted ARC. No local install is described. — [GitHub github-actions-goat](https://github.com/step-security/github-actions-goat)
- GitHub Actions Goat repo: 523 stars, last push 2026-10-30. — [GitHub API](https://api.github.com/repos/step-security/github-actions-goat)

**Vendor labs (browser, free registration)**
- **Isovalent (Cilium/Tetragon/eBPF) labs**: https://isovalent.com/labs/. 12 labs are listed. They include "Getting Started with Cilium (Hubble, Gateway API, WireGuard)", "Foundations: Getting Started with Kubernetes Networking and Cilium", "Getting Started with Tetragon", "Cilium LoadBalancer IPAM and L2 Service Announcement", "Kubernetes Packet Capture with Isopcap", 15-minute "Discovery" labs on AKS/EKS, and two "Isovalent Enterprise" labs. — [Isovalent labs list](https://isovalent.com/resource-library/labs/) (opened)
- The Isovalent "Getting Started with Cilium" lab installs Cilium on a cluster without a CNI, moves from L3 to L7 policy, publishes a path via Gateway API, enables WireGuard, and ends with an exam: "diagnose and fix an HTTPRoute that doesn't match the expected request". — [Isovalent lab page](https://isovalent.com/labs/cilium-getting-started/) (opened)
- Isovalent labs run in the browser on Instruqt with "an individual environment per user" and take 30-60 minutes. The Credly badges for them are listed as "Cost: Free". — [Isovalent badges blog](https://isovalent.com/blog/post/badges-for-cilium-labs-catch-em-over-the-holidays) (snippet); [Credly Cilium Getting Started](https://www.credly.com/org/isovalent/badge/cilium-getting-started) (snippet)
- **Solo Academy (Solo.io)**: https://solo.io/academy. It offers labs on Istio and Ambient Mesh (mTLS, authorization policies, waypoints, circuit breaking, fault injection, sidecar-to-sidecarless migration), kgateway (Gateway API, canary with Argo Rollouts), kagent and agentgateway. — [Solo Academy](https://solo.io/academy) (opened; the page did not state price or registration)
- Solo Academy is described as "free training courses". "Get Started with Istio Service Mesh" takes about 2 hours, and a score of at least 80% on the final assessment earns a Solo.io certification. — [Solo lab page](https://solo.io/resources/lab/solo-academy-course-get-started-with-istio-service-mesh) (snippet; the opened page showed only a listing)
- **Tetrate Academy**: https://academy.tetrate.io. Free courses: Istio Fundamentals, Envoy Fundamentals, Envoy Gateway Fundamentals, the Istio 0-60 Workshop ("labs on a Kubernetes cluster") and the Istio Wasm Workshop. Tetrate Service Bridge Fundamentals is paid ($499). Sign Up/Sign In links are present. — [Tetrate Academy](https://academy.tetrate.io/) (opened)
- **Red Hat interactive labs (Ansible)**: https://www.redhat.com/en/interactive-labs/ansible. 14 labs of 15-60 minutes each in a "preconfigured Red Hat Ansible Automation Platform environment". Examples: Get started with ansible-navigator (introductory), ansible-builder, Automation Controller, network-automation "First playbook", and Event-Driven Ansible rulebooks. — [Red Hat Ansible labs](https://www.redhat.com/en/interactive-labs/ansible) (opened)
- Red Hat says the interactive labs are no-cost, need only a Red Hat account, and open in the browser with a terminal and instructions side by side. Some lab pages ask for a form submission. — [Red Hat blog](https://www.redhat.com/en/blog/interactive-labs-enterprise-lab-environments-ready-minutes-no-cost) (snippet)
- **Red Hat Developer Sandbox**: a free hosted OpenShift environment ("30-day trial experience"). It includes OpenShift Pipelines, Dev Spaces, OpenShift AI and Ansible Automation Platform trials, plus guided activities such as "Learn Kubernetes using the Developer Sandbox". — [Developer Sandbox](https://developers.redhat.com/developer-sandbox) (opened)
- Developer Sandbox FAQ: "There is no credit card required". It is free, lasts 30 days, and you can export your work and start a new 30-day trial. It needs a Red Hat account plus a valid phone number. CPU/RAM limits are not stated. — [Developer Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ) (opened)

**Registry practice (your own stack: Harbor)**
- **Harbor public demo server**: https://demo.goharbor.io. Anyone can self-register. You can create a project and `docker login`/push images (keep them under 100 MB). Only user functions are available, with no admin. The server is "cleaned and reset every two days". Do not upload sensitive images. — [Harbor docs: demo server](https://goharbor.io/docs/main/install-config/demo-server/) (opened); demo.goharbor.io returned HTTP 200 on 2026-11-07 (curl).

**Free course with labs (Linux Foundation)**
- **LFS148 Getting Started with OpenTelemetry**: $0, self-paced, about 8-10 hours, 11 chapters with several hands-on labs, 90 days of access, a digital badge, beginner level. Labs run in a Dev Container (Docker, VS Code, Dev Containers extension, up to 4 GB RAM and 5 GB disk) or in GitHub Codespaces. The LF portal login is needed to enrol. The page was modified 2026-05-28. — [LF LFS148](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/) (opened)

**Browser simulators and games (L0-L2 warm-ups)**
- **DevOps Daily games**: https://devops-daily.com/games. 62 browser simulators and games (2 more coming soon). Among them: Kubernetes RBAC Simulator, Kubernetes Networking/CNI Simulator, Kubernetes Scheduler Challenge, Kubernetes Terminal Simulator, Docker Terminal Simulator, Container Security Challenge, GitOps Workflow Simulator, Deployment Strategies Simulator, Terraform Basics Simulator ("no AWS account needed"), Terraform State Puzzle, Incident Commander Simulator, On-Call: The Daily Incident, Log Aggregation Pipeline Simulator, and a PromQL Playground. — [DevOps Daily games](https://devops-daily.com/games) (opened; the page does not state price or account, and has a separate "Pro" area)
- DevOps Daily repo: 1,149 stars, pushed 2026-11-07 (very active). — [GitHub API](https://api.github.com/repos/The-DevOps-Daily/devops-daily)

**Policy-as-code and templating playgrounds (browser)**
- **Kyverno Playground**: https://playground.kyverno.io. The page title is "Kyverno Playground" (it is a JS app, so content could not be read). The kyverno/playground repo was pushed 2026-11-06 (35 stars). — [Kyverno Playground](https://playground.kyverno.io/) (HTTP-only); [GitHub API](https://api.github.com/repos/kyverno/playground)
- **OPA Rego Playground**: https://play.openpolicyagent.org returned HTTP 200 (curl). The OPA project is active (pushed 2026-11-07, 12,443 stars). — [OPA playground](https://play.openpolicyagent.org) (HTTP-only); [GitHub API](https://api.github.com/repos/open-policy-agent/opa)
- **Helm Playground**: https://helm-playground.com, "Debug Helm templates in your browser". It has template.yaml, values.yaml and output panes. The WASM build "includes Sprig, which Helm uses for templating". The Helm version is not stated. — [Helm Playground](https://helm-playground.com/) (opened); repo shipmight/helm-playground, 136 stars, last push 2025-08-14 — [GitHub API](https://api.github.com/repos/shipmight/helm-playground)

**Observability playgrounds (browser)**
- **Official Prometheus demo site**: https://demo.prometheus.io links to live instances at prometheus.demo.prometheus.io, alertmanager.demo.prometheus.io, node.demo.prometheus.io (node_exporter) and grafana.demo.prometheus.io. The source is github.com/prometheus/demo-site. — [demo.prometheus.io](https://demo.prometheus.io) (HTML inspected via curl)
- **Grafana LogQL simulator** (in the Loki docs): an online tool for trying LogQL line filters, logfmt/json/pattern/regex parsers, label filters and `line_format` on sample or pasted log lines, without running Loki. It is "very limited": the stream selector is fixed to `{job="analyze"}` and metric queries are not supported. — [Loki docs: LogQL analyzer](https://grafana.com/docs/loki/latest/query/analyzer/) (opened)
- **VRL Playground** (Vector Remap Language, Datadog's Vector log pipeline): write a VRL program, run it against events and share it. The vectordotdev/vrl repo was pushed 2026-11-06. — [VRL Playground](https://playground.vrl.dev/) (opened; shows "Loading playground…"); [GitHub API](https://api.github.com/repos/vectordotdev/vrl)
- **OTTL Playground** (OpenTelemetry Transformation Language for Collector processors): https://ottl.run. Page title "OTTL Playground", source elastic/ottl-playground (pushed 2026-10-27, 23 stars). The `www.` host returned Cloudflare 522; the bare domain returned 200. — [ottl.run](https://ottl.run) (HTML inspected via curl); [GitHub API](https://api.github.com/repos/elastic/ottl-playground)
- **PromQL Playground** (community): a browser editor with guided scenarios (error rates, latency percentiles, topk) that queries demo.promlabs.com. — [dev.to post](https://dev.to/rohitpotato/i-built-a-tool-to-master-promql-2p3l) (snippet). The fetched page only showed "Loading PromQL Playground...". Repo: 19 stars, last push 2026-01-10. — [promql-playground.vercel.app](https://promql-playground.vercel.app/); [GitHub API](https://api.github.com/repos/rohitpotato/promql-playground)

**Reverse-proxy playground (browser)**
- **nginx playground** (wizard zines, Julia Evans): edit an nginx config, run a `curl`/`http` command against it, and see the output and errors. — [nginx playground](https://nginx-playground.wizardzines.com/) (opened; usage limits not stated)

**Self-hosted, for a throwaway VM only**
- **Bust-a-Kube** (Jay Beale, InGuardians): "an intentionally-vulnerable Kubernetes cluster" shipped as 3 prebuilt VM images (1 control plane, 2 workers) for VMware (OVA) or KVM (qcow2.gz), with an answer key. The readme path says "BustaKube-OVA-July20" and gives no year or version. — [Bust-a-Kube](https://www.bustakube.com/), [download page](https://www.bustakube.com/download) (opened)
- **kube_security_lab** (raesene): 288 stars, last push 2026-03-19. Metadata only; the README was not opened. — [GitHub API](https://api.github.com/repos/raesene/kube_security_lab)
- **ControlPlane simulator** (the "kubernetes-simulator" CTF named in the brief): 1,009 stars, last push 2024-09-02. Metadata only; the README was not opened. — [GitHub API](https://api.github.com/repos/controlplaneio/simulator)
- **TerraGoat** (vulnerable Terraform, Bridgecrew): 1,318 stars, last push 2025-07-13. Metadata only. — [GitHub API](https://api.github.com/repos/bridgecrewio/terragoat)
- **ahmetb/kubernetes-network-policy-recipes**: 6,193 stars, last push 2025-02-07. Metadata only. — [GitHub API](https://api.github.com/repos/ahmetb/kubernetes-network-policy-recipes)
- **ansible/workshops** (self-paced Red Hat workshop content): 1,872 stars, pushed 2026-11-06. Metadata only. — [GitHub API](https://api.github.com/repos/ansible/workshops)

**Enabler: a free throwaway Linux box in the browser**
- **GitHub Codespaces free quota**: GitHub Free personal accounts get 120 hours of compute (scaled by core count) and 15 GB-month of storage per month. No payment method is needed. Without one, "usage is blocked once you use up your quota". — [GitHub Docs: Codespaces billing](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces) (opened). LF LFS148 names Codespaces as its alternative lab environment. — [LF LFS148](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/)

### Inferences
- SadServers is the closest match to the handbook's break-fix style and to the user's real stack: free scenarios include a Traefik + Docker Compose fix ("San Juan"), Kubernetes pod and StatefulSet fixes, and Docker "won't start". It runs on a disposable VM with no internet, so it needs no throwaway VM of the user's own.
- The Isovalent "Getting Started with Cilium" exam and the Solo/Tetrate Gateway API and Envoy labs are good "on-prem to cloud-native" bridges. They move from Traefik/Ingress thinking to Gateway API, eBPF CNI and service mesh.
- The self-hosted goats (CI/CD Goat, Bust-a-Kube, kube_security_lab, the ControlPlane simulator) fit the user's rule only inside a throwaway VM. GitHub Codespaces may be a cheaper throwaway host than a local VM for the Docker-based ones. I did not verify whether a 2-core Codespace has enough RAM for CI/CD Goat's GitLab container.
- The GitHub Actions Goat runs entirely on GitHub's own runners in your fork, so nothing touches the user's machine. It is about supply-chain hardening rather than break-fix.
- Wiz CSC challenges are hard (L3-L4) and security-flavoured, but "Game of Pods" and "Split Horizon" exercise exactly the RBAC, kubelet and network-isolation knowledge a CKA holder needs for K8s problem-solving.

### Gaps
- **Solo Academy and Tetrate**: I could not open an individual lab page to confirm whether the cluster is provided in the browser or what the registration form asks for.
- **Isovalent**: the lab page's HTML embeds HubSpot forms ("hsforms"), so a name/email form before launch is likely. I did not see the form itself.
- **Wiz CSC**: price and sign-up terms are not stated on the page. That it is free is my inference from the Register link and community write-ups, not a stated fact.
- **Datadog Learning Center** (learn.datadoghq.com): returned HTTP 403 to both curl and WebFetch, so I could not verify its free hands-on labs.
- **Oracle LiveLabs** (livelabs.oracle.com, free OKE sandboxes): the connection failed from this environment, so it was not verified.
- **No free browser playground found for OpenTofu, Flux or Jenkins specifically.** Jenkins practice exists only inside CI/CD Goat (self-hosted) and a paid SadServers scenario. GitOps/Argo CD hands-on beyond Killercoda (already in the handbook) was not found free (see Q4, Octopus).
- **No free lab found for Dokploy or Docker Swarm** (module 45, and the Swarm part of 44).
- TryHackMe and Pwned Labs container rooms were not checked. pwnedlabs.io only returned HTTP 200.

## Q2. Access terms per site: free vs free tier, sign-up, credit card, browser vs self-hosted, level, maintenance

### Takeaway
Most finds are free with at most a free account and no credit card. The exceptions are SadServers (a free tier with daily limits; the rest is $9/month Pro), the Red Hat Sandbox (needs a phone number, 30-day renewable), and Codespaces (a quota). Five finds are self-hosted and belong in a throwaway VM. The CI/CD Goat and Bust-a-Kube are clearly stale.

### Cited Findings

| Site (URL) | Free model | Sign-up / card | Where it runs | Level (my estimate) | Maintenance signal | Source |
|---|---|---|---|---|---|---|
| SadServers (sadservers.com) | Free tier: "selection of scenarios with daily limits"; Pro $9/mo | Account (email or Google); no card mentioned for free | Browser terminal to ephemeral EC2 VM | L1-L3 | Pricing page updated 2026-11-04; advent2025 tag | [pricing](https://sadservers.com/pricing), [FAQ](https://sadservers.com/faq), [scenarios](https://sadservers.com/scenarios) |
| Wiz Cloud Security Championship (cloudsecuritychampionship.com) | No price shown | Register/Login links present | Browser (challenge environments provided) | L3-L4 | 12 challenges Jun 2025 to May 2026; 11 enterable | [site](https://cloudsecuritychampionship.com/), [blog](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges) |
| OWASP WrongSecrets (wrongsecrets.herokuapp.com) | Fully free, open source | No sign-up on hosted instance | Hosted browser app; or Docker/minikube/cloud self-host | L1-L3 | v1.14.2; repo pushed 2026-11-02 | [hosted](https://wrongsecrets.herokuapp.com/), [repo](https://github.com/OWASP/wrongsecrets) |
| CI/CD Goat (github.com/cider-security-research/cicd-goat) | Fully free, open source | None | Self-hosted Docker Compose (throwaway VM) | L2-L3 | Last push 2024-07-14 (stale) | [repo](https://github.com/cider-security-research/cicd-goat), [API](https://api.github.com/repos/cider-security-research/cicd-goat) |
| GitHub Actions Goat (github.com/step-security/github-actions-goat) | Free, open source | GitHub account (fork) | GitHub-hosted runners in your fork | L2-L3 | Pushed 2026-10-30 | [repo](https://github.com/step-security/github-actions-goat) |
| Isovalent labs (isovalent.com/labs) | Free; badges "Cost: Free" | Likely HubSpot form (inferred from page source); 2 labs are "Enterprise" | Browser (Instruqt) | L1-L3 | 2026 lab list incl. Cilium 1.19.5 | [list](https://isovalent.com/resource-library/labs/), [Credly](https://www.credly.com/org/isovalent/badge/cilium-getting-started) |
| Solo Academy (solo.io/academy) | "Free training courses" (snippet) | Not confirmed | Labs (delivery not confirmed) | L1-L3 | Covers 2026 topics (kagent, agentgateway) | [academy](https://solo.io/academy) |
| Tetrate Academy (academy.tetrate.io) | Istio/Envoy/Envoy Gateway courses free; TSB course $499 | Sign-up links present | Online course; Istio 0-60 has K8s labs | L1-L2 | Not stated | [academy](https://academy.tetrate.io/) |
| Red Hat interactive labs, Ansible (redhat.com/en/interactive-labs/ansible) | No-cost | Red Hat account; some pages ask for a form | Browser | L0-L2 | 14 labs listed incl. Event-Driven Ansible | [labs](https://www.redhat.com/en/interactive-labs/ansible), [blog](https://www.redhat.com/en/blog/interactive-labs-enterprise-lab-environments-ready-minutes-no-cost) |
| Red Hat Developer Sandbox (developers.redhat.com/developer-sandbox) | Free 30-day, restartable | Red Hat account + phone; "no credit card required" | Hosted OpenShift (web console, optional `oc`) | L1-L2 | © 2026 page | [page](https://developers.redhat.com/developer-sandbox), [FAQ](https://developers.redhat.com/developer-sandbox/FAQ) |
| Harbor demo (demo.goharbor.io) | Free | Self-register (username, email, password) | Browser UI + your Docker client | L1 | Resets every 2 days; HTTP 200 on 2026-11-07 | [docs](https://goharbor.io/docs/main/install-config/demo-server/) |
| LF LFS148 OpenTelemetry (training.linuxfoundation.org) | $0 | LF portal login | Dev Container on own Docker, or Codespaces | L1 | Page modified 2026-05-28 | [course](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/) |
| DevOps Daily games (devops-daily.com/games) | Free to open; price not stated; separate "Pro" area | None seen | Browser simulators | L0-L2 | Repo pushed 2026-11-07 | [games](https://devops-daily.com/games), [API](https://api.github.com/repos/The-DevOps-Daily/devops-daily) |
| Kyverno Playground (playground.kyverno.io) | Free | None (not verified) | Browser | L2 | Repo pushed 2026-11-06 | [API](https://api.github.com/repos/kyverno/playground) |
| OPA Rego Playground (play.openpolicyagent.org) | Free | None (not verified) | Browser | L2 | HTTP 200 only | [site](https://play.openpolicyagent.org) |
| Helm Playground (helm-playground.com) | Free | None | Browser (WASM, Sprig) | L1-L2 | Last push 2025-08-14 | [site](https://helm-playground.com/) |
| Prometheus demo (demo.prometheus.io) | Free | None | Browser (live Prometheus/Alertmanager/node_exporter/Grafana) | L1-L2 | Official project site | [site](https://demo.prometheus.io) |
| LogQL simulator (grafana.com/docs/loki/latest/query/analyzer/) | Free | None | Browser | L1-L2 | In "latest" docs | [docs](https://grafana.com/docs/loki/latest/query/analyzer/) |
| VRL Playground (playground.vrl.dev) | Free | None | Browser | L1-L2 | vrl repo pushed 2026-11-06 | [site](https://playground.vrl.dev/) |
| OTTL Playground (ottl.run) | Free | None | Browser | L2 | Repo pushed 2026-10-27 | [API](https://api.github.com/repos/elastic/ottl-playground) |
| nginx playground (nginx-playground.wizardzines.com) | Free | None | Browser | L1-L2 | Not stated | [site](https://nginx-playground.wizardzines.com/) |
| Bust-a-Kube (bustakube.com) | Price not stated (download page) | None seen | Self-hosted 3 VM images, VMware/KVM | L2-L3 | "July20" build, year unknown (stale) | [download](https://www.bustakube.com/download) |
| GitHub Codespaces (enabler) | 120 compute-hours + 15 GB-month per month | GitHub account; no card needed (blocked at quota) | Browser VS Code + Linux container | n/a | Current docs | [docs](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces) |

### Inferences
- A credit card is not required for any item in the table. Where a site gave no explicit statement, I found no card prompt on the pages I opened.
- The Red Hat Sandbox's phone-number requirement and SadServers' account are the only sign-ups that collect personal data beyond an email address. The user must do those sign-ups themselves.
- Treat CI/CD Goat (no push since Jul 2024) and Bust-a-Kube (undated 2020-era build) as "may need fixes to start". That is itself break-fix practice, but only in a throwaway VM.

### Gaps
- The exact daily limit and per-scenario time on SadServers' free tier are not published.
- I did not confirm whether Kyverno, OPA, VRL or OTTL playgrounds need sign-in, because they are JS apps and the content was unreadable. Public evidence suggests they are open, but this is unverified.
- No repo or date was found for nginx-playground.wizardzines.com.

## Q3. Which handbook module does each new find fit?

### Takeaway
New coverage is strongest for 46 (K8s problems), 44 (Docker/registry), 37 (security), 47 (CI/CD) and 49 (observability). Module 43 (Traefik) gets one free SadServers Traefik scenario plus the nginx, Gateway API and Envoy labs. Module 45 (Dokploy/PaaS) got nothing.

### Cited Findings
- **26 containers/k8s playbook and 46 Kubernetes problems**: SadServers "Bilbao", "Buenos Aires", "Bengaluru" (free) ([scenarios](https://sadservers.com/scenarios)); Wiz CSC "Game of Pods" and "Split Horizon" ([CSC](https://cloudsecuritychampionship.com/)); Isovalent Cilium lab with the HTTPRoute fix exam ([lab](https://isovalent.com/labs/cilium-getting-started/)); Helm Playground ([site](https://helm-playground.com/)); SadServers "Kilifi" (Helm, free).
- **30 Learn Docker and 44 Docker/Swarm/registry problems**: SadServers "Salta" Docker container won't start, "Quito", "Helsingør" (Compose) (free) ([scenarios](https://sadservers.com/scenarios)); Harbor demo ([docs](https://goharbor.io/docs/main/install-config/demo-server/)); WrongSecrets Docker challenges (secrets leaked in images) ([hosted](https://wrongsecrets.herokuapp.com/)); Wiz "Contain Me If You Can" container escape ([CSC](https://cloudsecuritychampionship.com/)); DevOps Daily Docker Terminal Simulator ([games](https://devops-daily.com/games)).
- **31 Learn Kubernetes**: Isovalent "Foundations: Getting Started with Kubernetes Networking and Cilium" ([list](https://isovalent.com/resource-library/labs/)); Red Hat Developer Sandbox "Learn Kubernetes using the Developer Sandbox" ([page](https://developers.redhat.com/developer-sandbox)); DevOps Daily K8s RBAC/Scheduler/CNI simulators ([games](https://devops-daily.com/games)); Solo and Tetrate Istio fundamentals ([Solo](https://solo.io/academy), [Tetrate](https://academy.tetrate.io/)).
- **43 Traefik & reverse proxies**: SadServers "San Juan: mucho Traefik" (free), "Cape Town: Borked Nginx" (free), "Bangalore: Envoy Panics" (free), "Lyon: Migrate Ingress-NGINX to Traefik" (paid) ([scenarios](https://sadservers.com/scenarios)); nginx playground ([site](https://nginx-playground.wizardzines.com/)); Tetrate Envoy Gateway Fundamentals ([Tetrate](https://academy.tetrate.io/)); kgateway labs ([Solo](https://solo.io/academy)).
- **33 CI/CD-IaC-SRE**: Red Hat Ansible interactive labs ([labs](https://www.redhat.com/en/interactive-labs/ansible)); Wiz "State of Affairs" Terraform challenge ([CSC](https://cloudsecuritychampionship.com/)); DevOps Daily Terraform Basics and Terraform State Puzzle, Incident Commander ([games](https://devops-daily.com/games)).
- **47 CI/CD GitLab/Jenkins/Actions/ArgoCD**: CI/CD Goat (Jenkins, GitLab, Gitea) ([repo](https://github.com/cider-security-research/cicd-goat)); GitHub Actions Goat ([repo](https://github.com/step-security/github-actions-goat)); kgateway canary with Argo Rollouts lab ([Solo](https://solo.io/academy)); DevOps Daily GitOps Workflow / Deployment Strategies simulators ([games](https://devops-daily.com/games)).
- **32 performance & observability and 49 observability stack problems**: Prometheus demo site ([site](https://demo.prometheus.io)); LogQL simulator ([docs](https://grafana.com/docs/loki/latest/query/analyzer/)); VRL Playground ([site](https://playground.vrl.dev/)); OTTL Playground ([ottl.run](https://ottl.run)); LF LFS148 OpenTelemetry ([course](https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/)); Isovalent Hubble and Tetragon labs ([list](https://isovalent.com/resource-library/labs/)).
- **37 Security/DevSecOps**: WrongSecrets, CI/CD Goat, GitHub Actions Goat, Wiz CSC, Kyverno and OPA playgrounds, Bust-a-Kube (sources as above).

### Inferences
- Module 45 (Dokploy & self-hosted PaaS) has no matching free lab. The nearest proxies are SadServers' Traefik + Compose scenario and the Harbor demo, since Dokploy uses Traefik and Docker Swarm.
- A sensible ladder for the user: DevOps Daily (L0-L1 warm-up), then SadServers free (L1-L3), then vendor labs (Isovalent/Solo/Red Hat), then the goats in a throwaway VM, then the Wiz CSC (L3-L4).

### Gaps
- No free Docker Swarm-specific break-fix lab was found.

## Q4. Status changes to handbook-covered sites since 3 Oct 2026, and paid/trial-only sites skipped

### Takeaway
One handbook entry looks broken. **eksclustergames.com no longer resolves (no DNS A record on 2026-11-07)**, and neither does Wiz's K8s LAN Party (k8slanparty.com). Every other handbook site I spot-checked returned HTTP 200. Also, LF's free "Introduction to GitOps (LFS169)" has been withdrawn, and the former Codefresh Argo CD certification (now at Octopus) is paid.

### Cited Findings
- `eksclustergames.com` and `www.eksclustergames.com`: Google DNS-over-HTTPS returns NOERROR (Status 0) with **no A, AAAA or CNAME answers**. The domain is still registered on Route 53 nameservers but points nowhere, and `curl` fails. — [dns.google eksclustergames.com](https://dns.google/resolve?name=eksclustergames.com&type=A) (queried 2026-11-07)
- `k8slanparty.com` and `www.k8slanparty.com`: same result, no A, AAAA or CNAME records, unreachable. — [dns.google k8slanparty.com](https://dns.google/resolve?name=k8slanparty.com&type=A). Wiz's March 2024 announcement still links to https://www.k8slanparty.com/ (5 K8s-networking scenarios). — [Wiz blog](https://www.wiz.io/blog/k8s-lan-party-challenge)
- `bigiamchallenge.com` (Wiz, AWS IAM): also no A record; `www.` returns NXDOMAIN. — [dns.google bigiamchallenge.com](https://dns.google/resolve?name=bigiamchallenge.com&type=A)
- `contained.af` (Jess Frazelle's old container-escape game, not in the handbook): NXDOMAIN, gone. — [dns.google contained.af](https://dns.google/resolve?name=contained.af&type=A)
- Handbook sites that returned HTTP 200 on 2026-11-07 (curl -L): killercoda.com, labs.iximiuz.com, engineer.kodekloud.com, labs.play-with-k8s.com, labs.play-with-docker.com, dockerlabs.collabnix.com, editor.networkpolicy.io, demo.promlens.com, demo.promlabs.com (redirects to /query), play.grafana.org, k8s.af, ohmygit.org, gitexercises.fracz.com, madhuakula.com/kubernetes-goat/. — (curl checks; no single source URL)
- **LF "Introduction to GitOps (LFS169)"**: the course page now says "THE TRAINING OR CERTIFICATION PRODUCT YOU ARE SEARCHING FOR IS NO LONGER AVAILABLE". — [LF LFS169](https://training.linuxfoundation.org/training/introduction-to-gitops-lfs169/) (opened). (An older TFIR article called it free — [TFIR](https://tfir.io/linux-foundation-launches-gitops-training-courses/), snippet.)
- **Paid, skipped: Codefresh "GitOps with Argo" certification.** learning.codefresh.io now 301-redirects to learning.octopus.com, which requires login and offers a discounted "GitOps Certification Bundle" ([Octopus learning](https://learning.octopus.com/), opened). The Credly GitOps Fundamentals badge lists "Cost: Paid" ([Credly](https://www.credly.com/org/codefresh/badge/gitops-fundamentals), snippet).
- **Paid, skipped (other)**: SadServers Pro/Pro+ ($9-11/month; [pricing](https://sadservers.com/pricing)); Tetrate Service Bridge Fundamentals ($499; [Tetrate](https://academy.tetrate.io/)); Pluralsight PromQL lab (subscription; [Pluralsight](https://www.pluralsight.com/labs/aws/working-with-prometheus-queries), snippet).

### Inferences
- The Wiz domains may have been retired or moved quietly. The Cloud Security Championship site is where Wiz's playable K8s and container challenges now live, so the handbook could point there instead of eksclustergames.com. A temporary DNS outage cannot be ruled out from one day's check, so re-check before deleting the entry.

### Gaps
- Not every handbook entry was re-checked. killer.sh, localstack.cloud, codecrafters.io, labex.io, roadmap.sh, kodekloud.com free-course pages, the GitHub repos (kelseyhightower, bregman-arie, MichaelCade, dgkanatsios, lucky-sideburn), the HashiCorp/GitLab/GitHub docs, the OpenTelemetry demo, the Wazuh docs and OWASP Juice Shop were not tested for price or status changes.
- I found no Wiz statement explaining why eksclustergames.com and k8slanparty.com stopped resolving.
